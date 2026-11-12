"""
A1, the grocer's boy (npc) - colour atlas + baked crease shading (AO) + GLB export.
Same method as npc_rittenhouse_bake.py (loaded here as a library for the node helper, the atlas
packing, the hairline clean-up, the compose step and the bake plumbing).

Run in Blender after tools/blender/npc_grocer_boy.py (same session, or open
assets/models/source/npc-grocer-boy.blend before this script has been run on it):
    exec(open(r"<project>/tools/blender/npc_grocer_boy_bake.py").read())

1. Source materials per slot (SRC_*), box-projected in metres, no new downloads: Pickell's Poly
   Haven CC0 maps - white poplin tinted light tan for the duck work jacket, white poplin for the
   shirt and (cream) for the apron, the charcoal herringbone tinted dark brown-grey for the
   trousers, brown leather for the work shoes; MakeHuman CC0 young light male skin (a touch of
   sun, faint freckles), blue eyes, eyebrow010 painted in; procedural light-brown hair.
2. One "Atlas" UV for all parts (face ~30 %), packed; Cycles bakes of albedo (head and hands
   from the full-resolution MakeHuman meshes) and AO; atlas = colour x AO, JPEG q85
   (assets/textures/npc-grocer-boy-atlas.jpg).
3. Joins everything into ONE skinned mesh with ONE material, scales rig + mesh uniformly to
   FINAL_H (top of the hair), levels the soles to y 0 and exports assets/models/npc-grocer-boy.glb
   (clips Idle / Talk).
"""
import bpy, bmesh, os, math
import numpy as np
from mathutils import Vector

_ROOT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
RITTENHOUSE_LIB_ONLY = True
exec(open(os.path.join(_ROOT, r"tools\blender\npc_rittenhouse_bake.py"), encoding="utf-8").read())
RITTENHOUSE_LIB_ONLY = False

ATLAS_PATH = os.path.join(ROOT, r"assets\textures\npc-grocer-boy-atlas.jpg")
GLB_PATH = os.path.join(ROOT, r"assets\models\npc-grocer-boy.glb")
BLEND = os.path.join(ROOT, r"assets\models\source\npc-grocer-boy.blend")
COLL = "NPC_GrocerBoy"
WORK = "NPC_GrocerBoy_Work"
RIG = "GrocerBoy_Rig"
FINAL_H = 1.72
SLOTS = ["SKIN", "HAIR", "EYE", "SUIT", "SHIRT", "TIE", "SHOE", "GOLD", "TAPE", "PENCIL", "BUTTON", "HANKY",
         "TROUSERS", "APRON"]

PART_WEIGHT = {
    "PART_head": 0.30, "PART_eyes": 0.012, "PART_hair": 0.045, "PART_hands": 0.10,
    "PART_jacket": 0.15, "PART_collar": 0.025, "PART_sleeves": 0.085, "PART_cuffs": 0.010,
    "PART_front": 0.035, "PART_trousers": 0.065, "PART_shoes": 0.045, "PART_apron": 0.11, "PART_gusset": 0.006,
}

HAIR_DARK = hexlin("4A3220")
HAIR_MID = hexlin("7E5A38")
TAN = (0.62, 0.50, 0.33, 1.0)              # white poplin x this = light tan duck (~#C4AE86 on screen)


def hair_colour_b(g):
    """Light-to-mid brown, combed back from a centre parting: strands along y on top, down the
    short sides; a little sun-lightening on the top."""
    x, y, z = g.xyz()
    s1 = g.noise((90.0, 700.0, 90.0), detail=3)
    s2 = g.noise((700.0, 120.0, 90.0), detail=3)
    sep = g.nt.nodes.new("ShaderNodeSeparateXYZ"); g.link(g.geo().outputs["Normal"], sep.inputs[0])
    nz = g.m("ABSOLUTE", sep.outputs[2])
    st = g.mix(g.maprange(nz, 0.5, 0.85, 0, 1), s2, s1)
    v = g.maprange(st, 0.30, 0.75, 0.0, 1.0)
    col = g.mix(v, g.rgb(HAIR_DARK), g.rgb(HAIR_MID))
    sun = g.m("MULTIPLY", g.maprange(z, 1.69, 1.73, 0, 1), 0.35)
    col = g.mix(sun, col, g.rgb(hexlin("9C7A52")))
    # the parting line itself shows a little scalp-dark
    part = g.m("MULTIPLY", g.maprange(g.m("ABSOLUTE", x), 0.0035, 0.0010, 0, 1), g.maprange(y, 0.04, 0.02, 0, 1))
    part = g.m("MULTIPLY", part, g.maprange(z, 1.66, 1.68, 0, 1))
    return g.mix(g.m("MULTIPLY", part, 0.5), col, g.rgb(hexlin("3A271A")))


def skin_material_b(name, with_face):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    skin, _ = g.img(os.path.join(MH, r"skins\young_caucasian_male\young_lightskinned_male_diffuse.png"), uv="UVMap")
    col = g.mix(1.0, skin, (0.99, 0.95, 0.92, 1.0), "MULTIPLY")      # outdoors, a little less pink
    if with_face:
        x, y, z = g.xyz()
        hz = g.nt.nodes.new("ShaderNodeAttribute"); hz.attribute_name = "hairzone"
        # round 1: a soft, broken 1.5 cm fade of short hair growing in below the hairline
        # (fine streaks along the growth direction), full hair colour only right at the shell edge
        h = hz.outputs["Fac"]
        streak = g.maprange(g.noise((520.0, 520.0, 110.0), detail=2), 0.30, 0.70, 0.0, 1.0)
        soft = g.m("MULTIPLY", g.m("POWER", h, 0.6), g.m("ADD", 0.40, g.m("MULTIPLY", streak, 0.60)))
        edge = g.maprange(h, 0.82, 1.0, 0.0, 1.0)
        fac = g.m("MINIMUM", g.m("MAXIMUM", g.m("MULTIPLY", soft, 0.95), g.m("MULTIPLY", edge, 0.92)), 0.92)
        col = g.mix(fac, col, g.rgb(HAIR_MID))
        fits = brow_fits()
        brow = None
        for side in (1, -1):
            (a1, a2, a3, a4), (b1, b2, b3, b4), (u0, u1, v0, v1) = fits[side]
            u = g.m("ADD", g.m("MULTIPLY_ADD", x, a1, g.m("MULTIPLY_ADD", y, a2, g.m("MULTIPLY", z, a3))), a4)
            v = g.m("ADD", g.m("MULTIPLY_ADD", x, b1, g.m("MULTIPLY_ADD", y, b2, g.m("MULTIPLY", z, b3))), b4)
            cv = g.nt.nodes.new("ShaderNodeCombineXYZ"); g.link(u, cv.inputs[0]); g.link(v, cv.inputs[1])
            _, ba = g.img(os.path.join(MH, r"eyebrows\eyebrow010\eyebrow010.png"), vec=cv.outputs[0], extension="CLIP")
            sidemask = g.maprange(x, -0.004 * side, 0.004 * side, 0, 1)
            sidemask = g.m("MULTIPLY", sidemask, g.band(v, v0 - 0.02, v0 + 0.01, v1 - 0.01, v1 + 0.02))
            sidemask = g.m("MULTIPLY", sidemask, g.band(u, u0 - 0.02, u0 + 0.01, u1 - 0.01, u1 + 0.02))
            ba = g.m("MULTIPLY", ba, sidemask)
            brow = ba if brow is None else g.m("MAXIMUM", brow, ba)
        brow = g.m("MULTIPLY", brow, g.maprange(y, -0.06, -0.085, 0, 1))
        brow = g.m("POWER", brow, 0.7)
        col = g.mix(g.m("MINIMUM", g.m("MULTIPLY", brow, 1.25), 0.88), col, g.rgb(hexlin("4A3222")))
        # faint freckles over the nose and the cheeks
        ax = g.m("ABSOLUTE", x)
        zone = g.m("MULTIPLY", g.maprange(ax, 0.050, 0.035, 0, 1), g.band(z, 1.555, 1.57, 1.60, 1.61))
        zone = g.m("MULTIPLY", zone, g.maprange(y, -0.08, -0.105, 0, 1))
        fr = g.maprange(g.noise((1400.0, 1400.0, 1400.0), detail=1), 0.62, 0.70, 0, 1)
        col = g.mix(g.m("MULTIPLY", g.m("MULTIPLY", zone, fr), 0.22), col, g.rgb(hexlin("9A5E3E")))
        # a little colour in the cheeks and lips (young, outdoors)
        cheek = g.m("MULTIPLY", g.band(ax, 0.022, 0.034, 0.050, 0.060), g.band(z, 1.545, 1.56, 1.585, 1.595))
        cheek = g.m("MULTIPLY", cheek, g.maprange(y, -0.08, -0.11, 0, 1))
        col = g.mix(g.m("MULTIPLY", cheek, 0.06), col, g.rgb(hexlin("C4706A")))
    g.base(col)
    return mat


def build_source_materials_b():
    skin_material_b("SRC_SKIN", False)
    skin_material_b("SRC_SKIN_HI_HEAD", True)
    skin_material_b("SRC_SKIN_HI_HANDS", False)

    # light tan cotton duck work jacket: mottled, darker and worn at the cuffs and elbows, a little
    # grime round the pockets and the hem, seams along the buttoning edge
    def duck_tweak(g, c):
        x, y, z = g.xyz()
        c = g.mix(1.0, c, TAN, "MULTIPLY")
        mott = g.maprange(g.noise((25.0, 25.0, 25.0), detail=3), 0.3, 0.7, 0, 1)
        c = g.mix(g.m("MULTIPLY", mott, 0.25), c, g.rgb(hexlin("A08A62")))
        ax = g.m("ABSOLUTE", x)
        elbow = g.band(ax, 0.39, 0.42, 0.46, 0.49)
        c = g.mix(g.m("MULTIPLY", elbow, 0.22), c, g.rgb(hexlin("8C7752")))
        cuff = g.maprange(ax, 0.63, 0.68, 0, 1)
        c = g.mix(g.m("MULTIPLY", cuff, 0.30), c, g.rgb(hexlin("7E6A48")))
        hem = g.maprange(z, 0.76, 0.69, 0, 1)
        c = g.mix(g.m("MULTIPLY", hem, 0.25), c, g.rgb(hexlin("7E6A48")))
        seam = g.m("MULTIPLY", g.band(x, -0.004, 0.0, 0.004, 0.008), g.maprange(y, -0.05, -0.08, 0, 1))
        c = g.mix(g.m("MULTIPLY", seam, 0.35), c, g.rgb(hexlin("6E5C3E")))
        return c
    cloth("SRC_SUIT", os.path.join(TEX, "shirt_white_poplin.jpg"), 0.22, duck_tweak)

    cloth("SRC_SHIRT", os.path.join(TEX, "shirt_white_poplin.jpg"), 0.29,
          lambda g, c: g.mix(1.0, c, (1.02, 1.01, 0.99, 1.0), "MULTIPLY"))

    # long white grocer's apron: cream cotton, a little soiled low at the front and where the
    # hands wipe at the sides, faint vertical press creases
    def apron_tweak(g, c):
        x, y, z = g.xyz()
        c = g.mix(1.0, c, (1.03, 1.02, 0.98, 1.0), "MULTIPLY")
        crease = g.maprange(g.m("SINE", g.m("MULTIPLY", x, 2 * math.pi / 0.11)), 0.85, 1.0, 0, 1)
        c = g.mix(g.m("MULTIPLY", crease, 0.10), c, g.rgb(hexlin("CFC8B8")))
        dirt = g.maprange(g.noise((18.0, 18.0, 18.0), detail=3), 0.45, 0.75, 0, 1)
        low = g.maprange(z, 0.62, 0.40, 0, 1)
        wipe = g.m("MULTIPLY", g.maprange(g.m("ABSOLUTE", x), 0.10, 0.17, 0, 1), g.band(z, 0.70, 0.76, 0.88, 0.93))
        soil = g.m("MULTIPLY", g.m("MAXIMUM", low, wipe), dirt)
        return g.mix(g.m("MULTIPLY", soil, 0.30), c, g.rgb(hexlin("A89E88")))
    cloth("SRC_APRON", os.path.join(TEX, "shirt_white_poplin.jpg"), 0.29, apron_tweak)

    def trouser_tweak(g, c):
        x, y, z = g.xyz()
        c = g.mix(1.0, c, (0.92, 0.84, 0.74, 1.0), "MULTIPLY")              # dark brown-grey
        knee = g.m("MULTIPLY", g.band(z, 0.44, 0.48, 0.55, 0.60), g.maprange(y, -0.02, -0.06, 0, 1))
        c = g.mix(g.m("MULTIPLY", knee, 0.15), c, g.rgb(hexlin("4A453E")))  # worn shiny knees
        dust = g.m("MULTIPLY", g.maprange(z, 0.16, 0.05, 0, 1), g.maprange(g.noise((60.0, 60.0, 60.0)), 0.3, 0.7, 0.4, 1.0))
        return g.mix(g.m("MULTIPLY", dust, 0.35), c, g.rgb(hexlin("6A6052")))
    cloth("SRC_TROUSERS", os.path.join(TEX, "suit_charcoal_herringbone.jpg"), 0.27, trouser_tweak)

    def shoe_tweak(g, c):
        x, y, z = g.xyz()
        c = g.mix(1.0, c, (0.62, 0.52, 0.44, 1.0), "MULTIPLY")              # mid-brown work leather
        lx = g.m("ABSOLUTE", g.m("SUBTRACT", g.m("ABSOLUTE", x), 0.088))
        lacing = g.m("MULTIPLY", g.maprange(lx, 0.014, 0.009, 0, 1), g.band(y, -0.115, -0.105, -0.045, -0.035))
        lacing = g.m("MULTIPLY", lacing, g.maprange(z, 0.050, 0.060, 0, 1))
        lines = g.maprange(g.m("SINE", g.m("MULTIPLY", y, 2 * math.pi / 0.0085)), 0.2, 0.7, 0, 1)
        c = g.mix(g.m("MULTIPLY", lacing, 0.85), c, g.mix(lines, g.rgb((0.012, 0.008, 0.006, 1)), g.rgb((0.07, 0.05, 0.035, 1))))
        sole = g.maprange(z, 0.012, 0.008, 0, 1)
        c = g.mix(g.m("MULTIPLY", sole, 0.8), c, g.rgb((0.02, 0.015, 0.01, 1)))
        dust = g.m("MULTIPLY", g.maprange(z, 0.02, 0.06, 0, 1), g.maprange(g.noise((60.0, 60.0, 60.0)), 0.35, 0.7, 0, 1))
        return g.mix(g.m("MULTIPLY", dust, 0.25), c, g.rgb(hexlin("7A6E5E")))
    cloth("SRC_SHOE", os.path.join(TEX, "brown_leather.jpg"), 0.40, shoe_tweak)

    mat = bpy.data.materials.get("SRC_HAIR"); g = G(mat); g.base(hair_colour_b(g))
    mat = bpy.data.materials.get("SRC_EYE"); g = G(mat)
    c, _ = g.img(os.path.join(MH, r"eyes\materials\blue_eye.png"), uv="UVMap")
    g.base(g.mix(1.0, c, (0.82, 0.80, 0.78, 1.0), "MULTIPLY"))
    mat = bpy.data.materials.get("SRC_BUTTON"); g = G(mat)
    g.base(g.mix(g.maprange(g.noise((900.0, 900.0, 900.0)), 0.4, 0.6, 0, 0.5), g.rgb(hexlin("3A2A1E")), g.rgb(hexlin("5A4430"))))
    for k in ("TIE", "GOLD", "TAPE", "PENCIL", "HANKY"):         # unused slots (Pickell's slot list)
        mat = bpy.data.materials.get("SRC_" + k)
        if mat:
            g = G(mat); g.base(hexlin("808080"))


def bake_all_b():
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
    col = new_image("GB_atlas_colour", (0.5, 0.5, 0.5, 1))
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
    ao = new_image("GB_atlas_ao", (1, 1, 1, 1), noncolor=True)
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
    rebake("PART_trousers", ["PART_jacket", "PART_apron"])
    rebake("PART_jacket", ["PART_collar", "PART_apron", "PART_sleeves"])   # (the sleeve cone inside the shoulder)
    rebake("PART_cuffs", ["PART_sleeves", "PART_hands"])
    # round 1: the shirt front in the V is plain white (its AO under the jacket edges read as a
    # thin grey tie); the gusset between the thighs is cloth, not a black hole
    rebake("PART_front", ["PART_collar", "PART_jacket"])
    rebake("PART_gusset", ["PART_trousers", "PART_jacket", "PART_apron"])
    eyes = bpy.data.objects["PART_eyes"]
    wm = bpy.data.materials.get("GB_BAKE_WHITE") or bpy.data.materials.new("GB_BAKE_WHITE")
    gw = G(wm)
    em = gw.nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (1, 1, 1, 1)
    gw.link(em.outputs[0], gw.out.inputs[0])
    set_target([wm], ao)
    saved = [s.material for s in eyes.material_slots]
    for s in eyes.material_slots:
        s.material = wm
    select_only([eyes], eyes)
    bpy.ops.object.bake(type="EMIT", use_selected_to_active=False, use_clear=False, margin=4)
    for s, m in zip(eyes.material_slots, saved):
        s.material = m
    bpy.data.materials.remove(wm)
    arm.data.pose_position = "POSE"
    return col, ao


def uv_overlap_check(res=1024, report=6):
    """Texels (at res x res) covered by faces of two different parts - must be ~0. Prints a few
    clashing (part, face centre) pairs."""
    owner = np.full((res, res), -1, np.int32)
    oface = np.full((res, res), -1, np.int32)
    P_ = parts()
    clash = 0
    pairs = {}
    for pi, ob in enumerate(P_):
        uv = ob.data.uv_layers["Atlas"].data
        for p in ob.data.polygons:
            P = np.array([uv[l].uv[:] for l in p.loop_indices]) * res
            for k in range(1, len(P) - 1):
                tri = np.array([P[0], P[k], P[k + 1]])
                x0, y0 = np.floor(tri.min(0)).astype(int); x1, y1 = np.ceil(tri.max(0)).astype(int)
                xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, res)), np.arange(max(y0, 0), min(y1 + 1, res)))
                q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
                a, b, c = tri
                M = np.array([b - a, c - a]).T
                if abs(np.linalg.det(M)) < 1e-12:
                    continue
                l_ = np.linalg.solve(M, (q - a).T).T
                ins = (l_[:, 0] >= 0) & (l_[:, 1] >= 0) & (l_.sum(1) <= 1)
                yy, xx = ys.ravel()[ins], xs.ravel()[ins]
                other = owner[yy, xx]
                hit = (other >= 0) & (other != pi)
                clash += int(hit.sum())
                for j in np.where(hit)[0][:1]:
                    key = (P_[other[j]].name, int(oface[yy[j], xx[j]]), ob.name, p.index)
                    pairs[key] = 1
                owner[yy, xx] = pi
                oface[yy, xx] = p.index
    print("UV OVERLAP texels between parts (at", res, "):", clash)
    for (na, fa, nb, fb) in list(pairs)[:report]:
        ca = bpy.data.objects[na].data.polygons[fa].center
        cb = bpy.data.objects[nb].data.polygons[fb].center
        print("   ", na, fa, ca.to_tuple(3), "<->", nb, fb, cb.to_tuple(3))
    return clash


def paint_scalp(col, ao):
    """npc_rittenhouse_bake.paint_hairline, part (a) only: scalp faces lying wholly above the
    hairline (under the hair shell) get the hair colour. (Part (b), which repaints darker skin
    below the hairline as forehead, would erase the round-1 hairline fade.)"""
    head = bpy.data.objects["PART_head"]; hair = bpy.data.objects["PART_hair"]
    C = np.empty(SIZE * SIZE * 4, np.float32); col.pixels.foreach_get(C); C = C.reshape(SIZE, SIZE, 4)
    A = np.empty(SIZE * SIZE * 4, np.float32); ao.pixels.foreach_get(A); A = A.reshape(SIZE, SIZE, 4)

    def centre_px(ob, p):
        uv = ob.data.uv_layers["Atlas"].data
        u = np.mean([uv[l].uv[0] for l in p.loop_indices]); v = np.mean([uv[l].uv[1] for l in p.loop_indices])
        return min(SIZE - 1, int(v * SIZE)), min(SIZE - 1, int(u * SIZE))
    hs = [centre_px(hair, p) for p in hair.data.polygons]
    h_col = np.median(np.array([C[y, x, :3] for y, x in hs]), 0)
    h_ao = float(np.median([A[y, x, 0] for y, x in hs]))
    me = head.data
    hd = np.empty(len(me.vertices), np.float32); me.attributes["hairdist"].data.foreach_get("value", hd)
    uv = me.uv_layers["Atlas"].data
    n = 0
    for p in me.polygons:
        if min(hd[i] for i in p.vertices) > 0.0005:
            ys, xs = _face_texels(np.array([uv[l].uv[:] for l in p.loop_indices]) * SIZE)
            C[ys, xs, :3] = h_col; A[ys, xs, :3] = h_ao; n += 1
    col.pixels.foreach_set(C.ravel()); ao.pixels.foreach_set(A.ravel())
    print("PAINT scalp faces", n)


def level_soles(body):
    """(npc_shopper_bake) raise/lower the pelvis keys of Idle and Talk so the lowest sole point
    averages 0."""
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


def join_and_export_b(atlas):
    clear_targets()
    P = parts()
    arm = bpy.data.objects[RIG]
    mat = final_material(atlas)
    mat.name = "M_GrocerBoy"
    bones = {b.name for b in arm.data.bones}
    for ob in P:
        me = ob.data
        for lay in [l for l in me.uv_layers if l.name != "Atlas"]:
            me.uv_layers.remove(lay)
        for vg in [g for g in ob.vertex_groups if g.name not in bones]:
            ob.vertex_groups.remove(vg)
    select_only(P, bpy.data.objects["PART_jacket"])
    bpy.ops.object.join()
    body = bpy.context.view_layer.objects.active
    body.name = body.data.name = "GrocerBoy"
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
    for a in [a for a in body.data.attributes if a.name in ("hairzone", "hairdist")]:
        body.data.attributes.remove(a)
    for ca in list(body.data.color_attributes):
        body.data.color_attributes.remove(ca)
    tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
    rescale(arm, body)                     # top of the hair -> FINAL_H (uniform, applied)
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


def run_b():
    with win_ctx():
        for o in bpy.data.collections[COLL].objects:
            o.hide_set(False)
        build_source_materials_b()
        make_atlas_uvs()
        if uv_overlap_check() > 0:
            # concave packing slid islands into each other (folded hem bands / collar stand make
            # odd island outlines): re-pack by bounding boxes, relative scales kept (fill drops
            # from ~0.54 to ~0.46)
            P = parts()
            select_only(P, P[0])
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.select_all(action="SELECT")
            bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, shape_method="AABB",
                                    margin_method="FRACTION", margin=0.003)
            bpy.ops.object.mode_set(mode="OBJECT")
            uv_overlap_check()
            print("ATLAS fill after AABB re-pack", round(sum(uv_area(o, "Atlas") for o in P), 3))
        col, ao = bake_all_b()
        paint_scalp(col, ao)
        atlas = compose(col, ao)
        atlas.name = "npc-grocer-boy-atlas"
        body = join_and_export_b(atlas)
        sole_check(body)
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    return body


if not globals().get("GROCER_BAKE_LIB_ONLY"):
    run_b()
