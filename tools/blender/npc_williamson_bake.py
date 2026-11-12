"""
R2-W, Furman R. Williamson (npc) - colour atlas + baked crease shading (AO) + GLB export.
Same method as npc_rittenhouse_bake.py / npc_grocer_boy_bake.py (loaded here as libraries for the
node helper, the atlas packing and overlap check, the scalp clean-up, the compose step, sole
levelling and the bake plumbing).

Run in Blender after tools/blender/npc_williamson.py (same session, or open
assets/models/source/npc-williamson.blend before this script has been run on it):
    exec(open(r"<project>/tools/blender/npc_williamson_bake.py").read())

1. Source materials per slot (SRC_*), box-projected in metres, no new downloads: Pickell's Poly
   Haven CC0 maps - the mid-grey wool herringbone (poly_wool_herringbone, fine weave) lifted to
   a light warm grey for the summer suit (~#8A877F; the weave and crease shading stay visible),
   white poplin for the shirt, wing collar and handkerchief, brown leather darkened for the
   oxfords; MakeHuman CC0 old light male skin, light blue eyes, eyebrow006 painted white-grey;
   procedural white hair and moustache (fine strands, a little cream), boater straw (sennit
   braid rings), black grosgrain ribbon, dark navy bow tie with small white spots.
2. One "Atlas" UV for all parts (face ~30 %), packed; Cycles bakes of albedo (head and hands
   from the full-resolution MakeHuman meshes) and AO; atlas = colour x AO, JPEG q85
   (assets/textures/npc-williamson-atlas.jpg).
3. Joins everything into ONE skinned mesh with ONE material, scales rig + mesh uniformly so the
   crown of the head is at FINAL_H (1.74 m; the boater rises above it), levels the soles to
   y 0 and exports assets/models/npc-williamson.glb (clips Idle / Talk / Walk).
"""
import bpy, bmesh, os, math
import numpy as np
from mathutils import Vector

_ROOT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
GROCER_BAKE_LIB_ONLY = True
exec(open(os.path.join(_ROOT, r"tools\blender\npc_grocer_boy_bake.py"), encoding="utf-8").read())
GROCER_BAKE_LIB_ONLY = False

ATLAS_PATH = os.path.join(ROOT, r"assets\textures\npc-williamson-atlas.jpg")
GLB_PATH = os.path.join(ROOT, r"assets\models\npc-williamson.glb")
BLEND = os.path.join(ROOT, r"assets\models\source\npc-williamson.blend")
COLL = "NPC_Williamson"
WORK = "NPC_Williamson_Work"
RIG = "Williamson_Rig"
FINAL_H = 1.74                      # crown of the head (hair), not the hat
HAIR_ON_CROWN = 0.006               # hair thickness over the scalp's top (the top is under the hat)
SLOTS = ["SKIN", "HAIR", "EYE", "SUIT", "SHIRT", "TIE", "SHOE", "GOLD", "TAPE", "PENCIL", "BUTTON", "HANKY",
         "STRAW", "RIBBON", "MOUST", "BOWTIE"]

PART_WEIGHT = {
    "PART_head": 0.29, "PART_eyes": 0.012, "PART_hair": 0.040, "PART_hands": 0.10,
    "PART_jacket": 0.16, "PART_collar": 0.025, "PART_sleeves": 0.085, "PART_cuffs": 0.010,
    "PART_front": 0.075, "PART_shirt": 0.012, "PART_trousers": 0.085, "PART_shoes": 0.045,
    "PART_gusset": 0.004, "PART_seat": 0.025, "PART_hat": 0.045, "PART_moustache": 0.014,
}

HAIR_WHITE = hexlin("E4E0D8")
HAIR_SHADE = hexlin("A9A49B")
SUIT_TINT = (1.42, 1.38, 1.22, 1.0)   # mid-grey wool herringbone x this = light warm grey (~#8A877F)


def hair_colour_w(g):
    """White hair, short back and sides: fine strands combed back / down, a little grey in the
    shadowed under-layer, the faintest cream - object space."""
    x, y, z = g.xyz()
    s1 = g.noise((70.0, 700.0, 70.0), detail=3)          # strands along y (combed back at the sides)
    s2 = g.noise((700.0, 90.0, 60.0), detail=3)          # strands falling down at the back
    sep = g.nt.nodes.new("ShaderNodeSeparateXYZ"); g.link(g.geo().outputs["Normal"], sep.inputs[0])
    ny = g.m("ABSOLUTE", sep.outputs[1])
    st = g.mix(g.maprange(ny, 0.4, 0.8, 0, 1), s1, s2)
    v = g.maprange(st, 0.30, 0.72, 0.0, 1.0)
    col = g.mix(v, g.rgb(HAIR_SHADE), g.rgb(HAIR_WHITE))
    cream = g.m("MULTIPLY", g.maprange(g.noise((40.0, 40.0, 40.0)), 0.4, 0.7, 0, 1), 0.25)
    return g.mix(cream, col, g.rgb(hexlin("DCD3C0")))


def skin_material_w(name, with_face):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    skin, _ = g.img(os.path.join(MH, r"skins\old_caucasian_male\old_lightskinned_male_diffuse.png"), uv="UVMap")
    col = g.mix(1.0, skin, (1.04, 0.95, 0.90, 1.0), "MULTIPLY")      # an older man, a little ruddy
    if with_face:
        x, y, z = g.xyz()
        hz = g.nt.nodes.new("ShaderNodeAttribute"); hz.attribute_name = "hairzone"
        # (npc_grocer_boy round 1) a soft, broken 1.5 cm fade of short white hair below the
        # hairline, full colour only right at the shell edge: no hard skullcap line
        h = hz.outputs["Fac"]
        streak = g.maprange(g.noise((520.0, 520.0, 110.0), detail=2), 0.30, 0.70, 0.0, 1.0)
        soft = g.m("MULTIPLY", g.m("POWER", h, 0.7), g.m("ADD", 0.35, g.m("MULTIPLY", streak, 0.65)))
        edge = g.maprange(h, 0.82, 1.0, 0.0, 1.0)
        fac = g.m("MINIMUM", g.m("MAXIMUM", g.m("MULTIPLY", soft, 0.85), g.m("MULTIPLY", edge, 0.92)), 0.92)
        col = g.mix(fac, col, g.rgb(hexlin("CFCAC1")))
        fits = brow_fits()
        brow = None
        for side in (1, -1):
            (a1, a2, a3, a4), (b1, b2, b3, b4), (u0, u1, v0, v1) = fits[side]
            u = g.m("ADD", g.m("MULTIPLY_ADD", x, a1, g.m("MULTIPLY_ADD", y, a2, g.m("MULTIPLY", z, a3))), a4)
            v = g.m("ADD", g.m("MULTIPLY_ADD", x, b1, g.m("MULTIPLY_ADD", y, b2, g.m("MULTIPLY", z, b3))), b4)
            cv = g.nt.nodes.new("ShaderNodeCombineXYZ"); g.link(u, cv.inputs[0]); g.link(v, cv.inputs[1])
            _, ba = g.img(os.path.join(MH, r"eyebrows\eyebrow006\eyebrow006.png"), vec=cv.outputs[0], extension="CLIP")
            sidemask = g.maprange(x, -0.004 * side, 0.004 * side, 0, 1)
            sidemask = g.m("MULTIPLY", sidemask, g.band(v, v0 - 0.02, v0 + 0.01, v1 - 0.01, v1 + 0.02))
            sidemask = g.m("MULTIPLY", sidemask, g.band(u, u0 - 0.02, u0 + 0.01, u1 - 0.01, u1 + 0.02))
            ba = g.m("MULTIPLY", ba, sidemask)
            brow = ba if brow is None else g.m("MAXIMUM", brow, ba)
        brow = g.m("MULTIPLY", brow, g.maprange(y, -0.06, -0.085, 0, 1))
        brow = g.m("POWER", brow, 0.55)                                    # full, an older man's brows
        bcol = g.mix(g.maprange(g.noise((900.0, 900.0, 900.0)), 0.45, 0.7, 0, 0.7),
                     g.rgb(hexlin("8E8880")), g.rgb(hexlin("DAD5CC")))      # white, a few grey hairs
        col = g.mix(g.m("MINIMUM", g.m("MULTIPLY", brow, 1.35), 0.92), col, bcol)
        # a faint shadow of a shaved white beard on the chin and jaw (not under the moustache)
        beard = g.m("MULTIPLY", g.maprange(z, 1.525, 1.512, 0, 1), g.maprange(z, 1.45, 1.475, 0, 1))
        beard = g.m("MULTIPLY", beard, g.maprange(y, -0.03, -0.07, 0, 1))
        col = g.mix(g.m("MULTIPLY", beard, 0.07), col, g.rgb(hexlin("8A8580")))
        # a little colour in the cheeks and the nose (an older man outdoors in September)
        ax = g.m("ABSOLUTE", x)
        cheek = g.m("MULTIPLY", g.band(ax, 0.022, 0.034, 0.050, 0.060), g.band(z, 1.540, 1.555, 1.580, 1.590))
        cheek = g.m("MULTIPLY", cheek, g.maprange(y, -0.08, -0.11, 0, 1))
        col = g.mix(g.m("MULTIPLY", cheek, 0.07), col, g.rgb(hexlin("C2706A")))
    g.base(col)
    return mat


def build_source_materials_w():
    skin_material_w("SRC_SKIN", False)
    skin_material_w("SRC_SKIN_HI_HEAD", True)
    skin_material_w("SRC_SKIN_HI_HANDS", False)

    # light warm-grey summer suit: the wool herringbone's weave kept (contrast lifted a little so
    # the light cloth never reads as flat white), faint wear at elbows and cuffs, a little dust low
    def suit_tweak(g, c):
        x, y, z = g.xyz()
        bw = g.nt.nodes.new("ShaderNodeRGBToBW"); g.link(c, bw.inputs[0])
        weave = g.maprange(bw.outputs[0], 0.12, 0.26, 0.0, 1.0)
        c = g.mix(1.0, c, SUIT_TINT, "MULTIPLY")
        c = g.mix(g.m("MULTIPLY", g.m("SUBTRACT", 1.0, weave), 0.30), c, g.rgb(hexlin("6E6B64")))
        mott = g.maprange(g.noise((30.0, 30.0, 30.0), detail=3), 0.35, 0.65, 0, 1)
        c = g.mix(g.m("MULTIPLY", mott, 0.12), c, g.rgb(hexlin("7C786F")))
        ax = g.m("ABSOLUTE", x)
        elbow = g.band(ax, 0.40, 0.425, 0.45, 0.475)
        c = g.mix(g.m("MULTIPLY", elbow, 0.15), c, g.rgb(hexlin("767269")))
        cuff = g.maprange(ax, 0.64, 0.68, 0, 1)
        c = g.mix(g.m("MULTIPLY", cuff, 0.15), c, g.rgb(hexlin("706C63")))
        # round 1: a plain fly seam on the trouser front, just off the centre line, below the
        # waistcoat points (only trouser cloth is there: the coat is cut away)
        fly = g.m("MULTIPLY", g.band(x, 0.0035, 0.0050, 0.0062, 0.0078), g.band(z, 0.815, 0.83, 0.90, 0.915))
        fly = g.m("MULTIPLY", fly, g.maprange(y, -0.04, -0.07, 0, 1))
        c = g.mix(g.m("MULTIPLY", fly, 0.35), c, g.rgb(hexlin("5E5A52")))
        dust = g.m("MULTIPLY", g.maprange(z, 0.13, 0.04, 0, 1), g.maprange(g.noise((60.0, 60.0, 60.0)), 0.3, 0.7, 0.4, 1.0))
        return g.mix(g.m("MULTIPLY", dust, 0.22), c, g.rgb(hexlin("8C8270")))
    cloth("SRC_SUIT", os.path.join(TEX, "poly_wool_herringbone.jpg"), 0.25, suit_tweak)

    cloth("SRC_SHIRT", os.path.join(TEX, "shirt_white_poplin.jpg"), 0.29,
          lambda g, c: g.mix(1.0, c, (1.03, 1.03, 1.03, 1.0), "MULTIPLY"))
    cloth("SRC_HANKY", os.path.join(TEX, "shirt_white_poplin.jpg"), 0.29,
          lambda g, c: g.mix(1.0, c, (1.06, 1.06, 1.07, 1.0), "MULTIPLY"))

    def shoe_tweak(g, c):
        x, y, z = g.xyz()
        c = g.mix(1.0, c, (0.40, 0.28, 0.20, 1.0), "MULTIPLY")              # dark brown calf
        lx = g.m("ABSOLUTE", g.m("SUBTRACT", g.m("ABSOLUTE", x), 0.088))
        lacing = g.m("MULTIPLY", g.maprange(lx, 0.014, 0.009, 0, 1), g.band(y, -0.115, -0.105, -0.045, -0.035))
        lacing = g.m("MULTIPLY", lacing, g.maprange(z, 0.050, 0.060, 0, 1))
        lines = g.maprange(g.m("SINE", g.m("MULTIPLY", y, 2 * math.pi / 0.0085)), 0.2, 0.7, 0, 1)
        c = g.mix(g.m("MULTIPLY", lacing, 0.85), c, g.mix(lines, g.rgb((0.008, 0.005, 0.004, 1)), g.rgb((0.05, 0.035, 0.025, 1))))
        cap = g.band(y, -0.215, -0.212, -0.208, -0.205)                       # toe-cap seam
        c = g.mix(g.m("MULTIPLY", cap, 0.6), c, g.rgb((0.01, 0.006, 0.004, 1)))
        sole = g.maprange(z, 0.012, 0.008, 0, 1)
        c = g.mix(g.m("MULTIPLY", sole, 0.8), c, g.rgb((0.015, 0.01, 0.008, 1)))
        dust = g.m("MULTIPLY", g.maprange(z, 0.035, 0.06, 0, 1), g.maprange(y, -0.16, -0.24, 0, 1))
        return g.mix(g.m("MULTIPLY", dust, 0.10), c, g.rgb(hexlin("5A4E40")))
    cloth("SRC_SHOE", os.path.join(TEX, "brown_leather.jpg"), 0.40, shoe_tweak)

    mat = bpy.data.materials.get("SRC_HAIR"); g = G(mat); g.base(hair_colour_w(g))

    # moustache: white with fine strands combed down and out from the centre, a touch of cream
    mat = bpy.data.materials.get("SRC_MOUST"); g = G(mat)
    x, y, z = g.xyz()
    ax = g.m("ABSOLUTE", x)
    sweep = g.nt.nodes.new("ShaderNodeCombineXYZ")
    g.link(g.m("MULTIPLY", ax, 1.0), sweep.inputs[0])
    g.link(g.m("ADD", z, g.m("MULTIPLY", ax, 0.6)), sweep.inputs[1])
    mp = g.nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (2600.0, 300.0, 1.0)
    g.link(sweep.outputs[0], mp.inputs["Vector"])
    nz = g.nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Detail"].default_value = 3.0
    g.link(mp.outputs["Vector"], nz.inputs["Vector"])
    v = g.maprange(nz.outputs["Fac"], 0.32, 0.70, 0, 1)
    col = g.mix(v, g.rgb(hexlin("8E877C")), g.rgb(hexlin("E8E2D6")))
    low = g.m("MULTIPLY", g.maprange(z, 1.530, 1.523, 0, 1), g.maprange(ax, 0.012, 0.0, 0, 1))
    g.base(g.mix(g.m("MULTIPLY", low, 0.25), col, g.rgb(hexlin("D6C8A4"))))

    # straw boater: natural sennit braid in rings (crown sides by height, brim and top by radius)
    mat = bpy.data.materials.get("SRC_STRAW"); g = G(mat)
    x, y, z = g.xyz()
    r = g.m("SQRT", g.m("ADD", g.m("MULTIPLY", x, x), g.m("MULTIPLY", g.m("ADD", y, 0.022), g.m("ADD", y, 0.022))))
    ang = g.nt.nodes.new("ShaderNodeMath"); ang.operation = "ARCTAN2"
    g.link(x, ang.inputs[0]); g.link(g.m("ADD", y, 0.022), ang.inputs[1])
    s = g.m("ADD", r, z)
    ring = g.m("SINE", g.m("MULTIPLY", s, 2 * math.pi / 0.0042))
    plait = g.m("SINE", g.m("ADD", g.m("MULTIPLY", ang.outputs[0], 90.0), g.m("MULTIPLY", s, 2 * math.pi / 0.0084)))
    pat = g.m("ADD", g.m("MULTIPLY", ring, 0.6), g.m("MULTIPLY", plait, 0.4))
    v = g.maprange(pat, -0.9, 0.9, 0, 1)
    col = g.mix(v, g.rgb(hexlin("B39A62")), g.rgb(hexlin("E4D3A0")))
    fleck = g.maprange(g.noise((300.0, 300.0, 300.0), detail=2), 0.55, 0.75, 0, 1)
    g.base(g.mix(g.m("MULTIPLY", fleck, 0.2), col, g.rgb(hexlin("9C8452"))))

    mat = bpy.data.materials.get("SRC_RIBBON"); g = G(mat)
    x, y, z = g.xyz()
    rib = g.maprange(g.m("SINE", g.m("MULTIPLY", z, 2 * math.pi / 0.0011)), -1, 1, 0, 1)
    g.base(g.mix(rib, g.rgb(hexlin("111112")), g.rgb(hexlin("26262A"))))

    # bow tie: dark navy silk with small white spots (~7 mm apart)
    mat = bpy.data.materials.get("SRC_BOWTIE"); g = G(mat)
    x, y, z = g.xyz()
    vor = g.nt.nodes.new("ShaderNodeTexVoronoi"); vor.feature = "F1"
    vor.inputs["Scale"].default_value = 1.0 / 0.007
    vor.inputs["Randomness"].default_value = 0.15
    g.link(g.tc().outputs["Object"], vor.inputs["Vector"])
    dots = g.maprange(vor.outputs["Distance"], 0.20, 0.13, 0, 1)
    sheen = g.maprange(g.noise((400.0, 400.0, 400.0)), 0.4, 0.7, 0, 1)
    base = g.mix(sheen, g.rgb(hexlin("161C2C")), g.rgb(hexlin("222A40")))
    g.base(g.mix(g.m("MULTIPLY", dots, 0.9), base, g.rgb(hexlin("E6E4DE"))))

    mat = bpy.data.materials.get("SRC_EYE"); g = G(mat)
    c, _ = g.img(os.path.join(MH, r"eyes\materials\lightblue_eye.png"), uv="UVMap")
    g.base(g.mix(1.0, c, (0.80, 0.79, 0.77, 1.0), "MULTIPLY"))
    mat = bpy.data.materials.get("SRC_BUTTON"); g = G(mat)                  # grey horn buttons
    g.base(g.mix(g.maprange(g.noise((900.0, 900.0, 900.0)), 0.4, 0.6, 0, 0.5), g.rgb(hexlin("3E3832")), g.rgb(hexlin("5E564C"))))
    for k in ("TIE", "GOLD", "TAPE", "PENCIL"):             # unused slots (Pickell's slot list)
        mat = bpy.data.materials.get("SRC_" + k)
        if mat:
            g = G(mat); g.base(hexlin("808080"))


def collapse_folded_uvs():
    """Faces folded over within their own island (e.g. at a lapel notch) project with reversed
    winding in smart-project and overlap other islands after packing: give them zero UV area
    (all corners at their centroid) - they are tiny and take the colour of that one texel."""
    n = 0
    for ob in parts():
        uv = ob.data.uv_layers["Atlas"].data
        areas = []
        for p in ob.data.polygons:
            pts = [uv[i].uv.copy() for i in p.loop_indices]
            a = 0.0
            for k in range(len(pts)):
                a += pts[k].x * pts[(k + 1) % len(pts)].y - pts[(k + 1) % len(pts)].x * pts[k].y
            areas.append(a)
        sgn = 1.0 if sum(1 for a in areas if a > 0) >= sum(1 for a in areas if a < 0) else -1.0
        # texel scale of the part (uv units per metre) and, per face, its UV extent against the
        # extent its 3D size would give: slivers (pinched rows) get stretched into long crossed
        # strips by smart-project
        dens = sorted(math.sqrt(abs(a) * 0.5 / max(p.area, 1e-12)) for p, a in zip(ob.data.polygons, areas) if p.area > 1e-6)
        sc = dens[len(dens) // 2] if dens else 0.0
        for p, a in zip(ob.data.polygons, areas):
            if ob.name in ("PART_head", "PART_hands", "PART_eyes"):
                continue
            pts = [uv[i].uv for i in p.loop_indices]
            diag = (Vector((max(q.x for q in pts), max(q.y for q in pts)))
                    - Vector((min(q.x for q in pts), min(q.y for q in pts)))).length
            exp_ = sc * math.sqrt(max(p.area, 1e-12)) * 1.5 + 0.0015
            crossed = False
            if len(pts) == 4 and ob.name in ("PART_jacket", "PART_front", "PART_collar", "PART_sleeves",
                                             "PART_trousers"):     # a bow-tie (self-crossing) quad in UV
                t1 = (pts[1] - pts[0]).cross(pts[2] - pts[0]); t2 = (pts[2] - pts[0]).cross(pts[3] - pts[0])
                crossed = t1 * t2 < 0
            if a * sgn < 0 or crossed or diag > 3.0 * exp_:
                li = list(p.loop_indices)
                c = sum((uv[i].uv for i in li), Vector((0.0, 0.0))) / len(li)
                for i in li:
                    uv[i].uv = c
                n += 1
    print("UV folded faces collapsed", n)
    return n


def overlap_pairs(res=1024):
    """(part, face) pairs whose UV triangles cover the same texel (as uv_overlap_check)."""
    owner = np.full((res, res), -1, np.int32)
    oface = np.full((res, res), -1, np.int32)
    P_ = parts()
    pairs = set()
    for pi, ob in enumerate(P_):
        uv = ob.data.uv_layers["Atlas"].data
        for p in ob.data.polygons:
            Q = np.array([uv[l].uv[:] for l in p.loop_indices]) * res
            for k in range(1, len(Q) - 1):
                tri = np.array([Q[0], Q[k], Q[k + 1]])
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
                for j in np.where((other >= 0) & (other != pi))[0]:
                    pairs.add(((P_[other[j]].name, int(oface[yy[j], xx[j]])), (ob.name, p.index)))
                owner[yy, xx] = pi
                oface[yy, xx] = p.index
    return pairs


def resolve_overlaps(max_rounds=3):
    """Any faces still sharing texels after packing: the smaller (in 3D) face of each pair gets
    zero UV area (it takes the colour of one texel of its own island)."""
    for r in range(max_rounds):
        pairs = overlap_pairs()
        if not pairs:
            print("UV overlaps resolved after", r, "rounds")
            return
        done = set()
        for (na, fa), (nb, fb) in pairs:
            A = bpy.data.objects[na].data.polygons[fa]; B = bpy.data.objects[nb].data.polygons[fb]
            n, f = (na, fa) if A.area <= B.area else (nb, fb)
            if (n, f) in done or n in ("PART_head", "PART_hands", "PART_eyes"):
                continue
            uv = bpy.data.objects[n].data.uv_layers["Atlas"].data
            li = list(bpy.data.objects[n].data.polygons[f].loop_indices)
            c = sum((uv[i].uv for i in li), Vector((0.0, 0.0))) / len(li)
            for i in li:
                uv[i].uv = c
            done.add((n, f))
        print("UV overlap round", r, "faces collapsed", sorted(done))
    print("UV overlap pairs left", len(overlap_pairs()))


def bake_all_w():
    """As npc_grocer_boy_bake.bake_all_b with this figure's slots and AO second passes."""
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
    # only this figure renders (other collections / helpers hidden from render)
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
    col = new_image("FW_atlas_colour", (0.5, 0.5, 0.5, 1))
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
    ao = new_image("FW_atlas_ao", (1, 1, 1, 1), noncolor=True)
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
    rebake("PART_trousers", ["PART_jacket", "PART_seat"])
    rebake("PART_seat", ["PART_jacket"])
    # round 1: the waistcoat, wing collar and bow tie without the coat over them (the waistcoat's
    # shaded edge under the right lapel read as a dark necktie under the bow tie)
    rebake("PART_front", ["PART_jacket"])
    rebake("PART_jacket", ["PART_collar", "PART_sleeves"])
    rebake("PART_cuffs", ["PART_sleeves", "PART_hands"])
    # the shirt front is plain white (no grey stripe that could read as a tie)
    rebake("PART_shirt", ["PART_front", "PART_jacket", "PART_collar"])
    rebake("PART_gusset", ["PART_trousers", "PART_jacket", "PART_seat"])
    # the inside of the coat collar's stand faces the wing collar: baked without it (no dark band
    # between the two collars at the back of the neck)
    rebake("PART_collar", ["PART_front", "PART_head", "PART_hair"])
    # the hat's inside is not seen; its outside gets AO without the head inside it
    rebake("PART_hat", ["PART_hair", "PART_head"])
    eyes = bpy.data.objects["PART_eyes"]
    wm = bpy.data.materials.get("FW_BAKE_WHITE") or bpy.data.materials.new("FW_BAKE_WHITE")
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


def crown_height():
    """Crown of the head (rest pose): top of the MakeHuman scalp + the hair over it (the hair
    shell's top was removed under the hat, so the PARTs alone would under-measure)."""
    b = bpy.data.objects["SRC_Body"]
    return max(v.co.z for v in b.data.vertices) + HAIR_ON_CROWN


def rescale_crown(arm, body, crown):
    k = FINAL_H / crown
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
    print("RESCALE", round(k, 5), "crown", round(crown, 4), "->", round(crown * k, 4), "top (hat)", round(z1, 4),
          "soles", round(z0, 4))
    return k


def join_and_export_w(atlas):
    clear_targets()
    P = parts()
    arm = bpy.data.objects[RIG]
    crown = crown_height()
    mat = final_material(atlas)
    mat.name = "M_Williamson"
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
    body.name = body.data.name = "Williamson"
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
    for a in [a for a in body.data.attributes if a.name in ("hairzone", "hairdist", "legside")]:
        body.data.attributes.remove(a)
    for ca in list(body.data.color_attributes):
        body.data.color_attributes.remove(ca)
    tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
    rescale_crown(arm, body, crown)
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


def run_w():
    with win_ctx():
        # only this figure's collection renders during the bakes
        for c in bpy.data.collections:
            if c.name not in (COLL, WORK) and c.name in bpy.context.scene.collection.children:
                c.hide_render = True
        for o in bpy.data.collections[COLL].objects:
            o.hide_set(False)
        build_source_materials_w()
        make_atlas_uvs()
        collapse_folded_uvs()
        if uv_overlap_check() > 0:
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
        resolve_overlaps()
        col, ao = bake_all_w()
        paint_scalp(col, ao)
        atlas = compose(col, ao)
        atlas.name = "npc-williamson-atlas"
        body = join_and_export_w(atlas)
        sole_check(body)
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    return body


if not globals().get("WILLIAMSON_BAKE_LIB_ONLY"):
    run_w()
