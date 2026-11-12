"""
A2, the woman shopping (npc) - colour atlas + baked crease shading (AO) + GLB export.
Same method as npc_rittenhouse_bake.py (loaded here as a library for the node helper, the atlas
packing, the bakes' plumbing and the export).

Run in Blender after tools/blender/npc_shopper.py (same session, or open
assets/models/source/npc-shopper.blend before this script has been run on it):
    exec(open(r"<project>/tools/blender/npc_shopper_bake.py").read())

1. Source materials per slot (SRC_*): Pickell's Poly Haven CC0 cloth maps (no new downloads),
   box-projected in metres: white poplin blouse, poly-wool herringbone skirt tinted navy, brown
   leather shoes; MakeHuman CC0 young light female skin, brown eyes, eyebrow004 painted in, a
   painted lash line; procedural: brown pinned-up hair, wine silk sash, dark stockings, plaited
   straw hat with a navy grosgrain ribbon, willow basket, red-and-white checked cloth.
2. One "Atlas" UV for all parts (face ~28 %), packed; Cycles bakes of albedo (head and hands from
   the full-resolution MakeHuman meshes) and AO; atlas = colour x AO, JPEG q85
   (assets/textures/npc-shopper-atlas.jpg).
3. Joins everything into ONE skinned mesh with ONE material, scales rig + mesh uniformly so the
   top of her head is FINAL_H, exports assets/models/npc-shopper.glb (Idle / Talk).
"""
import bpy, bmesh, os, math
import numpy as np
from mathutils import Vector

_ROOT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
RITTENHOUSE_LIB_ONLY = True
exec(open(os.path.join(_ROOT, r"tools\blender\npc_rittenhouse_bake.py"), encoding="utf-8").read())
RITTENHOUSE_LIB_ONLY = False

ATLAS_PATH = os.path.join(ROOT, r"assets\textures\npc-shopper-atlas.jpg")
GLB_PATH = os.path.join(ROOT, r"assets\models\npc-shopper.glb")
BLEND = os.path.join(ROOT, r"assets\models\source\npc-shopper.blend")
COLL = "NPC_Shopper"
WORK = "NPC_Shopper_Work"
RIG = "Shopper_Rig"
FINAL_H = 1.62                 # top of her head (the hat crown rises ~4 cm above it)
SLOTS = ["SKIN", "HAIR", "EYE", "BLOUSE", "SKIRT", "SASH", "STOCKING", "SHOE", "STRAW", "RIBBON",
         "WICKER", "CLOTH", "BUTTON"]

PART_WEIGHT = {
    "PART_head": 0.28, "PART_eyes": 0.012, "PART_hair": 0.04, "PART_bun": 0.012, "PART_hands": 0.10,
    "PART_blouse": 0.12, "PART_collar": 0.02, "PART_sleeves": 0.08, "PART_skirt": 0.12,
    "PART_sash": 0.03, "PART_legs": 0.03, "PART_shoes": 0.03, "PART_hat": 0.06, "PART_basket": 0.045,
    "PART_hairvol": 0.035, "PART_capfill": 0.004,
}

HAIR_DARK = hexlin("2E2018")
HAIR_MID = hexlin("5A3F2C")


def hair_colour_s(g):
    """Brown hair combed back and up into the bun: strands along y on the sides, round the bun."""
    x, y, z = g.xyz()
    s1 = g.noise((70.0, 700.0, 140.0), detail=3)
    s2 = g.noise((700.0, 140.0, 70.0), detail=3)
    sep = g.nt.nodes.new("ShaderNodeSeparateXYZ"); g.link(g.geo().outputs["Normal"], sep.inputs[0])
    ny = g.m("ABSOLUTE", sep.outputs[1])
    st = g.mix(g.maprange(ny, 0.4, 0.8, 0, 1), s1, s2)
    v = g.maprange(st, 0.30, 0.75, 0.0, 1.0)
    col = g.mix(v, g.rgb(HAIR_DARK), g.rgb(HAIR_MID))
    sheen = g.m("MULTIPLY", g.maprange(g.noise((300.0, 300.0, 300.0), detail=1), 0.55, 0.75, 0, 1), 0.25)
    return g.mix(sheen, col, g.rgb(hexlin("7A5A40")))


def lash_attribute():
    """'lash' on HI_head: a soft band just round the eyeballs, strongest on the upper lid."""
    from mathutils.bvhtree import BVHTree
    hi = bpy.data.objects["HI_head"]; eyes = bpy.data.objects["PART_eyes"]
    bt = BVHTree.FromObject(eyes, bpy.context.evaluated_depsgraph_get())
    ec = np.array([v.co[:] for v in eyes.data.vertices])
    ez = float(ec[:, 2].mean())
    vals = []
    for v in hi.data.vertices:
        loc, n, i, d = bt.find_nearest(v.co)
        if loc is None or v.co.y > -0.09:
            vals.append(0.0); continue
        band = max(0.0, 1.0 - max(0.0, d - 0.0012) / 0.0032)
        upper = 1.0 if v.co.z > ez - 0.001 else 0.35
        vals.append(band * upper)
    at = hi.data.attributes.get("lash") or hi.data.attributes.new("lash", "FLOAT", "POINT")
    at.data.foreach_set("value", vals)


def skin_material_s(name, with_face):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    skin, _ = g.img(os.path.join(MH, r"skins\young_caucasian_female\young_lightskinned_female_diffuse.png"), uv="UVMap")
    col = g.mix(1.0, skin, (1.03, 0.97, 0.94, 1.0), "MULTIPLY")      # a little warmth, outdoors
    if with_face:
        x, y, z = g.xyz()
        hz = g.nt.nodes.new("ShaderNodeAttribute"); hz.attribute_name = "hairzone"
        col = g.mix(g.m("MULTIPLY", hz.outputs["Fac"], 0.92), col, g.rgb(HAIR_DARK))
        fits = brow_fits()
        brow = None
        for side in (1, -1):
            (a1, a2, a3, a4), (b1, b2, b3, b4), (u0, u1, v0, v1) = fits[side]
            u = g.m("ADD", g.m("MULTIPLY_ADD", x, a1, g.m("MULTIPLY_ADD", y, a2, g.m("MULTIPLY", z, a3))), a4)
            v = g.m("ADD", g.m("MULTIPLY_ADD", x, b1, g.m("MULTIPLY_ADD", y, b2, g.m("MULTIPLY", z, b3))), b4)
            cv = g.nt.nodes.new("ShaderNodeCombineXYZ"); g.link(u, cv.inputs[0]); g.link(v, cv.inputs[1])
            _, ba = g.img(os.path.join(MH, r"eyebrows\eyebrow004\eyebrow004.png"), vec=cv.outputs[0], extension="CLIP")
            sidemask = g.maprange(x, -0.004 * side, 0.004 * side, 0, 1)
            sidemask = g.m("MULTIPLY", sidemask, g.band(v, v0 - 0.02, v0 + 0.01, v1 - 0.01, v1 + 0.02))
            sidemask = g.m("MULTIPLY", sidemask, g.band(u, u0 - 0.02, u0 + 0.01, u1 - 0.01, u1 + 0.02))
            ba = g.m("MULTIPLY", ba, sidemask)
            brow = ba if brow is None else g.m("MAXIMUM", brow, ba)
        brow = g.m("MULTIPLY", brow, g.maprange(y, -0.06, -0.085, 0, 1))
        col = g.mix(g.m("MINIMUM", g.m("MULTIPLY", brow, 1.15), 0.85), col, g.rgb(hexlin("3A2A20")))
        la = g.nt.nodes.new("ShaderNodeAttribute"); la.attribute_name = "lash"
        col = g.mix(g.m("MULTIPLY", la.outputs["Fac"], 0.75), col, g.rgb(hexlin("2A1E18")))
        # a faint warmth on the cheeks
        ax = g.m("ABSOLUTE", x)
        cheek = g.m("MULTIPLY", g.band(ax, 0.022, 0.034, 0.050, 0.060), g.band(z, 1.455, 1.47, 1.49, 1.50))
        cheek = g.m("MULTIPLY", cheek, g.maprange(y, -0.08, -0.11, 0, 1))
        col = g.mix(g.m("MULTIPLY", cheek, 0.10), col, g.rgb(hexlin("C4706A")))
    g.base(col)
    return mat


def build_source_materials_s():
    skin_material_s("SRC_SKIN", False)
    skin_material_s("SRC_SKIN_HI_HEAD", True)
    skin_material_s("SRC_SKIN_HI_HANDS", False)

    cloth("SRC_BLOUSE", os.path.join(TEX, "shirt_white_poplin.jpg"), 0.29,
          lambda g, c: g.mix(1.0, c, (1.03, 1.03, 1.03, 1.0), "MULTIPLY"))

    def skirt_tweak(g, c):
        x, y, z = g.xyz()
        c = g.mix(1.0, c, (0.12, 0.165, 0.38, 1.0), "MULTIPLY")              # navy serge
        dust = g.m("MULTIPLY", g.maprange(z, 0.34, 0.27, 0, 1), g.maprange(g.noise((50.0, 50.0, 50.0)), 0.3, 0.7, 0.4, 1.0))
        return g.mix(g.m("MULTIPLY", dust, 0.22), c, g.rgb(hexlin("5E574C")))   # dusty hem
    cloth("SRC_SKIRT", os.path.join(TEX, "poly_wool_herringbone.jpg"), 0.27, skirt_tweak)

    def shoe_tweak(g, c):
        x, y, z = g.xyz()
        c = g.mix(1.0, c, (0.55, 0.50, 0.46, 1.0), "MULTIPLY")              # darker brown calf
        lx = g.m("ABSOLUTE", g.m("SUBTRACT", g.m("ABSOLUTE", x), 0.101))
        lacing = g.m("MULTIPLY", g.maprange(lx, 0.010, 0.006, 0, 1), g.band(y, -0.100, -0.090, -0.030, -0.020))
        lacing = g.m("MULTIPLY", lacing, g.maprange(z, 0.050, 0.058, 0, 1))
        lines = g.maprange(g.m("SINE", g.m("MULTIPLY", y, 2 * math.pi / 0.008)), 0.2, 0.7, 0, 1)
        c = g.mix(g.m("MULTIPLY", lacing, 0.85), c, g.mix(lines, g.rgb((0.01, 0.006, 0.004, 1)), g.rgb((0.06, 0.04, 0.03, 1))))
        heel = g.maprange(z, 0.024, 0.020, 0, 1)                            # dark heel and sole edge
        c = g.mix(g.m("MULTIPLY", heel, 0.7), c, g.rgb((0.02, 0.014, 0.01, 1)))
        dust = g.m("MULTIPLY", g.maprange(z, 0.03, 0.05, 0, 1), g.maprange(g.noise((60.0, 60.0, 60.0)), 0.35, 0.7, 0, 1))
        return g.mix(g.m("MULTIPLY", dust, 0.15), c, g.rgb(hexlin("6A5E50")))
    cloth("SRC_SHOE", os.path.join(TEX, "brown_leather.jpg"), 0.40, shoe_tweak)

    # sash: wine silk with soft sheen streaks
    mat = bpy.data.materials.get("SRC_SASH"); g = G(mat)
    sh = g.maprange(g.noise((30.0, 30.0, 220.0), detail=2), 0.35, 0.75, 0, 1)
    g.base(g.mix(g.m("MULTIPLY", sh, 0.55), g.rgb(hexlin("5E2232")), g.rgb(hexlin("8E4255"))))

    # dark lisle stockings, faintly lighter where stretched over the shin
    mat = bpy.data.materials.get("SRC_STOCKING"); g = G(mat)
    x, y, z = g.xyz()
    sep = g.nt.nodes.new("ShaderNodeSeparateXYZ"); g.link(g.geo().outputs["Normal"], sep.inputs[0])
    front = g.maprange(g.m("MULTIPLY", sep.outputs[1], -1.0), 0.3, 0.9, 0, 1)
    knit = g.maprange(g.noise((900.0, 900.0, 300.0), detail=1), 0.4, 0.6, 0, 1)
    c = g.mix(g.m("MULTIPLY", front, 0.45), g.rgb(hexlin("231D1A")), g.rgb(hexlin("4A3E37")))
    g.base(g.mix(g.m("MULTIPLY", knit, 0.15), c, g.rgb(hexlin("15110F"))))

    # plaited straw: rings round the crown / brim (radial + height), fibre noise
    mat = bpy.data.materials.get("SRC_STRAW"); g = G(mat)
    x, y, z = g.xyz()
    r = g.m("SQRT", g.m("ADD", g.m("MULTIPLY", x, x), g.m("MULTIPLY", g.m("ADD", y, 0.048), g.m("ADD", y, 0.048))))
    ringc = g.m("ADD", r, z)
    rings = g.maprange(g.m("SINE", g.m("MULTIPLY", ringc, 2 * math.pi / 0.0065)), -0.6, 0.9, 0, 1)
    ang = g.m("ARCTAN2", x, g.m("ADD", y, 0.048))
    plait = g.maprange(g.m("SINE", g.m("ADD", g.m("MULTIPLY", ang, 95.0), g.m("MULTIPLY", ringc, 2 * math.pi / 0.013))), -1, 1, 0, 1)
    fib = g.maprange(g.noise((600.0, 600.0, 600.0), detail=2), 0.35, 0.7, 0, 1)
    c = g.mix(g.m("MULTIPLY", rings, 0.55), g.rgb(hexlin("B39250")), g.rgb(hexlin("DCC48A")))
    c = g.mix(g.m("MULTIPLY", plait, 0.25), c, g.rgb(hexlin("E6D39C")))
    g.base(g.mix(g.m("MULTIPLY", fib, 0.25), c, g.rgb(hexlin("9C7C42"))))

    # navy grosgrain ribbon, fine ribs
    mat = bpy.data.materials.get("SRC_RIBBON"); g = G(mat)
    x, y, z = g.xyz()
    rib = g.maprange(g.m("SINE", g.m("MULTIPLY", z, 2 * math.pi / 0.0016)), -1, 1, 0, 1)
    g.base(g.mix(g.m("MULTIPLY", rib, 0.4), g.rgb(hexlin("1C2133")), g.rgb(hexlin("323A55"))))

    # willow basket weave: horizontal weavers over upright stakes, colour drift
    mat = bpy.data.materials.get("SRC_WICKER"); g = G(mat)
    x, y, z = g.xyz()
    weav = g.m("SINE", g.m("MULTIPLY", z, 2 * math.pi / 0.011))
    stake = g.m("SINE", g.m("MULTIPLY", g.m("ADD", x, y), 2 * math.pi / 0.022))
    wv = g.maprange(g.m("MULTIPLY", weav, stake), -0.6, 0.6, 0, 1)
    rows = g.maprange(g.m("ABSOLUTE", g.m("SINE", g.m("MULTIPLY", z, 2 * math.pi / 0.022))), 0.0, 0.25, 0, 1)
    c = g.mix(wv, g.rgb(hexlin("6E4A26")), g.rgb(hexlin("B08A55")))
    c = g.mix(g.m("MULTIPLY", g.m("SUBTRACT", 1.0, rows), 0.5), c, g.rgb(hexlin("4A3018")))
    drift = g.maprange(g.noise((40.0, 40.0, 40.0), detail=2), 0.3, 0.7, 0, 1)
    g.base(g.mix(g.m("MULTIPLY", drift, 0.25), c, g.rgb(hexlin("8C6A3E"))))

    # red-and-white checked cloth (gingham, 12 mm checks)
    mat = bpy.data.materials.get("SRC_CLOTH"); g = G(mat)
    x, y, z = g.xyz()
    a = g.maprange(g.m("SINE", g.m("MULTIPLY", g.m("ADD", x, z), 2 * math.pi / 0.024)), -0.05, 0.05, 0, 1)
    b = g.maprange(g.m("SINE", g.m("MULTIPLY", g.m("SUBTRACT", y, z), 2 * math.pi / 0.024)), -0.05, 0.05, 0, 1)
    both = g.m("MULTIPLY", a, b)
    one = g.m("SUBTRACT", g.m("ADD", a, b), g.m("MULTIPLY", both, 2.0))
    c = g.mix(g.m("MULTIPLY", one, 0.55), g.rgb(hexlin("EFE8DC")), g.rgb(hexlin("B23A34")))
    g.base(g.mix(both, c, g.rgb(hexlin("9A2A26"))))

    mat = bpy.data.materials.get("SRC_HAIR"); g = G(mat); g.base(hair_colour_s(g))
    mat = bpy.data.materials.get("SRC_EYE"); g = G(mat)
    c, _ = g.img(os.path.join(MH, r"eyes\materials\brownlight_eye.png"), uv="UVMap")
    c = g.mix(1.0, c, (0.82, 0.80, 0.78, 1.0), "MULTIPLY")
    hsv = g.nt.nodes.new("ShaderNodeSeparateColor"); hsv.mode = "HSV"; g.link(c, hsv.inputs[0])
    iris = g.maprange(hsv.outputs[1], 0.25, 0.5, 0, 1)                  # only the coloured iris
    g.base(g.mix(iris, c, g.mix(1.0, c, (0.55, 0.47, 0.40, 1.0), "MULTIPLY")))   # a deeper hazel brown
    mat = bpy.data.materials.get("SRC_BUTTON"); g = G(mat)
    g.base(g.mix(g.maprange(g.noise((900.0, 900.0, 900.0)), 0.4, 0.6, 0, 0.5), g.rgb(hexlin("D9D2C4")), g.rgb(hexlin("F2EEE6"))))


def bake_all_s():
    """As npc_rittenhouse_bake.bake_all with this figure's slots and AO second passes."""
    sc = bpy.context.scene
    try:
        sc.render.engine = "CYCLES"
    except TypeError as e:
        print("engine", e)
    sc.cycles.device = "GPU"
    sc.cycles.samples = 64
    sc.render.bake.margin = 6
    arm = bpy.data.objects[RIG]
    arm.data.pose_position = "REST"
    for o in bpy.data.objects:
        if not o.name.startswith("PART_") and o.type == "MESH":
            o.hide_render = True
    P = parts()
    head, hands = bpy.data.objects["PART_head"], bpy.data.objects["PART_hands"]
    hi_head, hi_hands = bpy.data.objects["HI_head"], bpy.data.objects["HI_hands"]
    for hi, mname in ((hi_head, "SRC_SKIN_HI_HEAD"), (hi_hands, "SRC_SKIN_HI_HANDS")):
        hi.data.materials.clear(); hi.data.materials.append(bpy.data.materials[mname])
        hi.data.uv_layers.active = hi.data.uv_layers["UVMap"]
    for ob in P:
        ob.data.uv_layers.active = ob.data.uv_layers["Atlas"]
    col = new_image("SH_atlas_colour", (0.5, 0.5, 0.5, 1))
    src_mats = [bpy.data.materials["SRC_" + k] for k in SLOTS]
    set_target(src_mats, col)
    bk = sc.render.bake
    others = [o for o in P if o not in (head, hands)]
    select_only(others, others[0])
    bk.use_selected_to_active = False
    bk.target = "IMAGE_TEXTURES"
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, use_clear=True, margin=6)
    work = bpy.data.collections.get(WORK)
    if work:
        work.hide_render = False
    for lo, hi in ((head, hi_head), (hands, hi_hands)):
        hi.hide_render = False
        select_only([hi, lo], lo)
        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, use_selected_to_active=True,
                            cage_extrusion=0.006, max_ray_distance=0.02, use_clear=False, margin=6)
        hi.hide_render = True
    if work:
        work.hide_render = True
    ao = new_image("SH_atlas_ao", (1, 1, 1, 1), noncolor=True)
    set_target(src_mats, ao)
    if sc.world is None:
        sc.world = bpy.data.worlds.new("World")
    sc.world.light_settings.distance = 0.12
    PA = [o for o in P if o.name != "PART_eyes"]
    select_only(PA, PA[0])
    sc.cycles.samples = 128
    bpy.ops.object.bake(type="AO", use_selected_to_active=False, use_clear=True, margin=6)

    def rebake(target, hide):
        obs = [bpy.data.objects[h] for h in hide]
        for o in obs:
            o.hide_render = True
        t = bpy.data.objects[target]
        select_only([t], t)
        bpy.ops.object.bake(type="AO", use_selected_to_active=False, use_clear=False, margin=3)
        for o in obs:
            o.hide_render = False
    # parts that peek out from under others in motion get cloth-coloured, not black, AO
    rebake("PART_blouse", ["PART_collar", "PART_sash", "PART_sleeves"])   # no dark wedge at the armholes
    rebake("PART_skirt", ["PART_sash"])
    rebake("PART_legs", ["PART_skirt", "PART_shoes"])
    rebake("PART_hair", ["PART_hat", "PART_bun"])
    rebake("PART_sleeves", ["PART_hands", "PART_basket", "PART_blouse", "PART_capfill", "PART_collar"])   # no dark cuff ring / sleeve cap
    rebake("PART_hairvol", ["PART_hat", "PART_bun", "PART_hair", "PART_head"])   # no grey edge at the temples
    eyes = bpy.data.objects["PART_eyes"]
    wm = bpy.data.materials.get("SH_BAKE_WHITE") or bpy.data.materials.new("SH_BAKE_WHITE")
    gw = G(wm)
    em = gw.nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (1, 1, 1, 1)
    gw.link(em.outputs[0], gw.out.inputs[0])
    set_target([wm], ao)
    for ob_w in (eyes, bpy.data.objects.get("PART_capfill")):     # no crease shading on these
        if ob_w is None:
            continue
        saved = [s.material for s in ob_w.material_slots]
        for s in ob_w.material_slots:
            s.material = wm
        select_only([ob_w], ob_w)
        bpy.ops.object.bake(type="EMIT", use_selected_to_active=False, use_clear=False, margin=4)
        for s, m in zip(ob_w.material_slots, saved):
            s.material = m
    bpy.data.materials.remove(wm)
    arm.data.pose_position = "POSE"
    return col, ao


def compose_s(col, ao):
    im = compose(col, ao)
    im.name = "npc-shopper-atlas"
    return im


def final_material_s(atlas):
    m = final_material(atlas)
    m.name = "M_Shopper"
    return m


def head_top(arm):
    """Top of her skull (the MakeHuman body; the scalp under the hat crown is not kept)."""
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    z = max(v.co.z for v in bpy.data.objects["SRC_Body"].data.vertices)
    zs = min(v.co.z for v in bpy.data.objects["PART_shoes"].data.vertices)
    arm.data.pose_position = "POSE"
    return z, zs


def join_and_export_s(atlas):
    clear_targets()
    P = parts()
    arm = bpy.data.objects[RIG]
    top, sole = head_top(arm)
    mat = final_material_s(atlas)
    bones = {b.name for b in arm.data.bones}
    for ob in P:
        me = ob.data
        for lay in [l for l in me.uv_layers if l.name != "Atlas"]:
            me.uv_layers.remove(lay)
        for vg in [g for g in ob.vertex_groups if g.name not in bones]:
            ob.vertex_groups.remove(vg)
    select_only(P, bpy.data.objects["PART_blouse"])
    bpy.ops.object.join()
    body = bpy.context.view_layer.objects.active
    body.name = body.data.name = "Shopper"
    body.data.materials.clear()
    body.data.materials.append(mat)
    for p in body.data.polygons:
        p.material_index = 0
    body.data.uv_layers["Atlas"].name = "UVMap"
    mat.node_tree.nodes[[n.type for n in mat.node_tree.nodes].index("UVMAP")].uv_map = "UVMap"
    for m in [m for m in body.modifiers if m.type != "ARMATURE"]:
        body.modifiers.remove(m)
    for m in [m for m in body.modifiers if m.type == "ARMATURE"][1:]:
        body.modifiers.remove(m)
    for a in [a for a in body.data.attributes if a.name in ("hairzone", "hairdist", "lash")]:
        body.data.attributes.remove(a)
    for ca in list(body.data.color_attributes):
        body.data.color_attributes.remove(ca)
    tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
    # uniform scale so the top of her head is FINAL_H
    k = FINAL_H / top
    if abs(k - 1.0) > 1e-4:
        arm.scale = (k, k, k)
        bpy.context.view_layer.update()
        select_only([arm, body], arm)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        for name in ("Idle", "Talk", "Walk"):
            act = bpy.data.actions.get(name)
            if act is None:
                continue
            for fc in iter_fcurves(act):
                if fc.data_path.endswith(".location"):
                    for kp in fc.keyframe_points:
                        kp.co.y *= k; kp.handle_left.y *= k; kp.handle_right.y *= k
    z0, z1 = rest_height(arm, body)
    print("RESCALE", round(k, 5), "head top", round(top, 4), "->", round(top * k, 4), "hat top", round(z1, 4),
          "soles", round(z0, 4))
    level_soles(body)
    ad = arm.animation_data
    ad.action = None
    for tr in ad.nla_tracks:
        tr.mute = False
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    select_only([arm, body], arm)
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
        export_texcoords=True, export_normals=True, export_tangents=False, export_attributes=False,
        export_vertex_color="NONE", export_materials="EXPORT", export_image_format="JPEG",
        export_jpeg_quality=85, export_image_quality=85,
        export_skins=True, export_influence_nb=4, export_def_bones=False, export_leaf_bone=False,
        export_animations=True, export_animation_mode="NLA_TRACKS", export_force_sampling=True,
        export_frame_step=1, export_optimize_animation_size=True, export_anim_slide_to_zero=True,
        export_morph=False, export_rest_position_armature=True)
    for tr in ad.nla_tracks:
        tr.mute = True
    print("GLB", GLB_PATH, os.path.getsize(GLB_PATH), "bytes; tris", tris, "bones", len(arm.data.bones))
    return body


def level_soles(body):
    """Raise/lower the pelvis keys of Idle and Talk so the lowest sole point averages 0."""
    arm = bpy.data.objects[RIG]
    for act in ("Idle", "Talk"):
        a = bpy.data.actions[act]
        arm.animation_data.action = a
        lows = []
        for f in range(int(a.frame_range[0]), int(a.frame_range[1]) + 1, 6):
            bpy.context.scene.frame_set(f)
            dg = bpy.context.evaluated_depsgraph_get()
            ev = body.evaluated_get(dg); me = ev.to_mesh()
            lows.append(min(v.co.z for v in me.vertices))
            ev.to_mesh_clear()
        dz = -float(np.mean(lows))
        d_local = arm.data.bones["pelvis"].matrix_local.to_3x3().inverted() @ Vector((0, 0, dz))
        for fc in iter_fcurves(a):
            if fc.data_path == 'pose.bones["pelvis"].location':
                for kp in fc.keyframe_points:
                    for attr in ("co", "handle_left", "handle_right"):
                        vv = getattr(kp, attr); vv.y += d_local[fc.array_index]
        print("LEVEL", act, "pelvis", round(dz * 1000, 1), "mm")
    arm.animation_data.action = None


def sole_check(body):
    """Lowest sole point over Idle / Talk (should stay at 0 +- a few mm)."""
    arm = bpy.data.objects[RIG]
    out = {}
    for act in ("Idle", "Talk"):
        a = bpy.data.actions[act]
        arm.animation_data.action = a
        lows = []
        for f in range(int(a.frame_range[0]), int(a.frame_range[1]) + 1, 6):
            bpy.context.scene.frame_set(f)
            dg = bpy.context.evaluated_depsgraph_get()
            ev = body.evaluated_get(dg); me = ev.to_mesh()
            lows.append(min(v.co.z for v in me.vertices))
            ev.to_mesh_clear()
        out[act] = (round(min(lows), 4), round(max(lows), 4))
    arm.animation_data.action = None
    print("SOLES min z over frames", out)
    return out


def run_s():
    with win_ctx():
        for o in bpy.data.collections[COLL].objects:
            o.hide_set(False)
        lash_attribute()
        build_source_materials_s()
        make_atlas_uvs()
        col, ao = bake_all_s()
        atlas = compose_s(col, ao)
        body = join_and_export_s(atlas)
        sole_check(body)
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    return body


if not globals().get("SHOPPER_BAKE_LIB_ONLY"):
    run_s()
