"""
John B. Pickell (npc) - colour atlas + baked crease shading (AO) + GLB export.

Run in Blender after tools/blender/npc_pickell.py (same session, or open
assets/models/source/npc_pickell.blend):
    exec(open(r"<project>/tools/blender/npc_pickell_bake.py").read())

1. Source materials per slot (SRC_*): Poly Haven CC0 cloth maps box-projected in metres
   (suit 0.27 m, shirting 0.29 m, calf 0.40 m), MakeHuman CC0 skin / eye maps, painted brows,
   eyelashes and moustache (no alpha in the result), procedural hair with grey temples,
   maroon tie with a small figure, tape-measure marks, light weathering.
2. One "Atlas" UV for all parts (face ~30 %, hands ~10 %, suit ~35 %, rest ~25 %), packed.
3. Cycles bakes: albedo (DIFFUSE colour only) of every part into the 2048 atlas; head and hands
   selected-to-active from the full-resolution MakeHuman meshes; ambient occlusion (crease
   shading) of the whole figure; atlas = colour x AO, saved as JPEG q85
   (assets/textures/npc-pickell-atlas.jpg).
4. Joins everything into ONE skinned mesh with ONE material (lit, roughness 0.8, metallic 0),
   exports assets/models/npc-pickell.glb with the clips Idle / Talk / Walk.
"""
import bpy, bmesh, os, math
import numpy as np
from mathutils import Vector

ROOT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
TEX = os.path.join(ROOT, r"assets\textures\npc-pickell")
MH = os.path.join(os.environ["APPDATA"], r"Blender Foundation\Blender\5.2\extensions\.user\user_default\mpfb\data")
ATLAS_PATH = os.path.join(ROOT, r"assets\textures\npc-pickell-atlas.jpg")
GLB_PATH = os.path.join(ROOT, r"assets\models\npc-pickell.glb")
BLEND = os.path.join(ROOT, r"assets\models\source\npc_pickell.blend")
SIZE = 2048
COLL = "NPC_Pickell"

PART_WEIGHT = {   # share of the atlas (renormalised)
    "PART_head": 0.30, "PART_eyes": 0.012, "PART_hair": 0.05, "PART_hands": 0.10,
    "PART_jacket": 0.17, "PART_sleeves": 0.09, "PART_trousers": 0.09,
    "PART_front": 0.085, "PART_collar": 0.025, "PART_cuffs": 0.012, "PART_shoes": 0.05, "PART_accessories": 0.025, "PART_pencil": 0.006,
}


def srgb_to_lin(c):
    return tuple(((x / 255.0 + 0.055) / 1.055) ** 2.4 if x / 255.0 > 0.04045 else x / 255.0 / 12.92 for x in c)


def hexlin(h):
    h = h.lstrip("#")
    return srgb_to_lin([int(h[i:i + 2], 16) for i in (0, 2, 4)]) + (1.0,)


# ----------------------------------------------------------------------------------------------
# tiny node-graph helper
# ----------------------------------------------------------------------------------------------
class G:
    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.out = self.nt.nodes.new("ShaderNodeOutputMaterial")
        self.bsdf = self.nt.nodes.new("ShaderNodeBsdfPrincipled")
        self.nt.links.new(self.bsdf.outputs[0], self.out.inputs[0])
        self.bsdf.inputs["Roughness"].default_value = 0.8
        self._tc = None; self._geo = None

    def link(self, a, b):
        self.nt.links.new(a, b)

    def tc(self):
        if self._tc is None:
            self._tc = self.nt.nodes.new("ShaderNodeTexCoord")
        return self._tc

    def geo(self):
        if self._geo is None:
            self._geo = self.nt.nodes.new("ShaderNodeNewGeometry")
        return self._geo

    def xyz(self):
        s = self.nt.nodes.new("ShaderNodeSeparateXYZ")
        self.link(self.tc().outputs["Object"], s.inputs[0])
        return s.outputs[0], s.outputs[1], s.outputs[2]

    def m(self, op, a, b=None, c=None, clamp=False):
        n = self.nt.nodes.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                self.link(v, n.inputs[i])
        return n.outputs[0]

    def band(self, v, lo0, lo1, hi0=None, hi1=None):
        """Smooth 0..1 mask rising lo0->lo1 (and falling hi0->hi1)."""
        a = self.maprange(v, lo0, lo1, 0, 1)
        if hi0 is not None:
            b = self.maprange(v, hi0, hi1, 1, 0)
            a = self.m("MULTIPLY", a, b)
        return a

    def maprange(self, v, a, b, c, d):
        n = self.nt.nodes.new("ShaderNodeMapRange"); n.interpolation_type = "SMOOTHSTEP"; n.clamp = True
        self.link(v, n.inputs["Value"])
        n.inputs["From Min"].default_value = a; n.inputs["From Max"].default_value = b
        n.inputs["To Min"].default_value = c; n.inputs["To Max"].default_value = d
        return n.outputs["Result"]

    def rgb(self, col):
        n = self.nt.nodes.new("ShaderNodeRGB"); n.outputs[0].default_value = col
        return n.outputs[0]

    def mix(self, fac, a, b, blend="MIX"):
        n = self.nt.nodes.new("ShaderNodeMix"); n.data_type = "RGBA"; n.blend_type = blend; n.clamp_result = True
        for sock, v in ((n.inputs[0], fac), (n.inputs[6], a), (n.inputs[7], b)):
            if isinstance(v, (int, float)):
                sock.default_value = v
            elif isinstance(v, tuple):
                sock.default_value = v
            else:
                self.link(v, sock)
        return n.outputs[2]

    def img(self, path, vec=None, uv=None, box=None, alpha=False, extension="REPEAT", noncolor=False):
        n = self.nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(path, check_existing=True)
        if noncolor:
            n.image.colorspace_settings.name = "Non-Color"
        n.extension = extension
        if box is not None:
            n.projection = "BOX"; n.projection_blend = 0.3
            mp = self.nt.nodes.new("ShaderNodeMapping")
            mp.inputs["Scale"].default_value = (1 / box,) * 3
            self.link(self.tc().outputs["Object"], mp.inputs["Vector"])
            self.link(mp.outputs["Vector"], n.inputs["Vector"])
        elif uv is not None:
            u = self.nt.nodes.new("ShaderNodeUVMap"); u.uv_map = uv
            self.link(u.outputs[0], n.inputs["Vector"])
        elif vec is not None:
            self.link(vec, n.inputs["Vector"])
        return n.outputs["Color"], n.outputs["Alpha"]

    def noise(self, scale_xyz, detail=2.0, base_scale=1.0):
        mp = self.nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = scale_xyz
        self.link(self.tc().outputs["Object"], mp.inputs["Vector"])
        n = self.nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = base_scale
        n.inputs["Detail"].default_value = detail
        self.link(mp.outputs["Vector"], n.inputs["Vector"])
        return n.outputs["Fac"]

    def base(self, sock):
        if isinstance(sock, tuple):
            self.bsdf.inputs["Base Color"].default_value = sock
        else:
            self.link(sock, self.bsdf.inputs["Base Color"])


# ----------------------------------------------------------------------------------------------
# 1. source materials
# ----------------------------------------------------------------------------------------------
HAIR_DARK = hexlin("3A2A1E")
HAIR_GREY = hexlin("8E8782")


def hair_colour(g):
    """Dark brown, combed streaks, pomade sheen, grey at the temples (object space)."""
    x, y, z = g.xyz()
    s1 = g.noise((60.0, 700.0, 60.0), detail=3)          # strands along x/z (top, sides)
    s2 = g.noise((700.0, 60.0, 60.0), detail=3)          # strands along y/z (back)
    sep = g.nt.nodes.new("ShaderNodeSeparateXYZ"); g.link(g.geo().outputs["Normal"], sep.inputs[0])
    ny = g.m("ABSOLUTE", sep.outputs[1])
    st = g.mix(g.maprange(ny, 0.4, 0.8, 0, 1), s1, s2)
    v = g.maprange(g.m("ADD", st, 0.0), 0.35, 0.75, 0.75, 1.35)
    col = g.mix(1.0, g.rgb(HAIR_DARK), v, "MULTIPLY")
    # grey at the temples / above the ears (salt and pepper)
    ax = g.m("ABSOLUTE", x)
    t = g.m("MULTIPLY", g.maprange(ax, 0.052, 0.07, 0, 1), g.maprange(z, 1.648, 1.615, 0, 1))
    t = g.m("MULTIPLY", t, g.maprange(y, 0.012, -0.012, 0, 1))          # temples, in front of the ears
    pep = g.maprange(g.noise((900.0, 900.0, 300.0), detail=1), 0.40, 0.62, 0.15, 1.0)
    t = g.m("MULTIPLY", t, pep)
    return g.mix(g.m("MULTIPLY", t, 0.7), col, g.rgb(HAIR_GREY))


def moustache_mask_image():
    """A 256x128 mask in the front projection x [-0.04,0.04], z [1.530,1.570] (clipped moustache)."""
    name = "PK_moustache_mask"
    im = bpy.data.images.get(name)
    if im:
        bpy.data.images.remove(im)
    W, H = 256, 128
    xs = (np.arange(W) + 0.5) / W * 0.08 - 0.04
    zs = (np.arange(H) + 0.5) / H * 0.04 + 1.530
    X, Zz = np.meshgrid(xs, zs)
    ax = np.abs(X)
    top = 1.5538 - 0.0068 * (ax / 0.0268) ** 2.2            # under the nose, tapering to the ends
    bot = 1.5412 + 0.0026 * (ax / 0.0268) ** 3.0            # just over the upper-lip line
    inside = (Zz < top) & (Zz > bot) & (ax < 0.0268)
    edge = np.clip((0.0268 - ax) / 0.005, 0, 1) * np.clip((top - Zz) / 0.0015, 0, 1) * np.clip((Zz - bot) / 0.001, 0, 1)
    rng = np.random.default_rng(7)
    strands = 0.85 + 0.15 * np.sin((X * 2600 + (Zz - 1.54) * 900 * np.sign(X)) + rng.normal(0, 0.6, X.shape))
    m = (inside * edge * strands).clip(0, 1)
    m[:, W // 2 - 1:W // 2 + 1] *= 0.75                      # faint philtrum parting
    px = np.zeros((H, W, 4), np.float32); px[..., 0] = m; px[..., 1] = m; px[..., 2] = m; px[..., 3] = 1
    im = bpy.data.images.new(name, W, H, alpha=False, float_buffer=False)
    im.colorspace_settings.name = "Non-Color"
    im.pixels.foreach_set(px.ravel())
    im.pack()
    return im


def brow_fits():
    """Least-squares affine (x, y, z) -> (u, v) of the eyebrow proxy, per side."""
    ob = bpy.data.objects["SRC_Eyebrows"]
    me = ob.data
    uv = me.uv_layers.active.data
    rows = {1: ([], []), -1: ([], [])}
    for p in me.polygons:
        for li, vi in zip(p.loop_indices, p.vertices):
            co = me.vertices[vi].co
            side = 1 if co.x > 0 else -1
            rows[side][0].append((co.x, co.y, co.z, 1.0)); rows[side][1].append(tuple(uv[li].uv))
    out = {}
    for side, (A, U) in rows.items():
        P = np.array(A)[:, :3]; U = np.array(U)
        c = P.mean(0)
        _, _, vt = np.linalg.svd(P - c)
        e1, e2 = vt[0], vt[1]                        # the strip's own plane (no normal component)
        S = np.stack([(P - c) @ e1, (P - c) @ e2, np.ones(len(P))], 1)
        res = []
        for k in range(2):
            a, *_ = np.linalg.lstsq(S, U[:, k], rcond=None)
            g3 = a[0] * e1 + a[1] * e2
            res.append((g3[0], g3[1], g3[2], a[2] - g3 @ c))
        res.append((U[:, 0].min(), U[:, 0].max(), U[:, 1].min(), U[:, 1].max()))   # own UV box
        out[side] = tuple(res)
    return out


def skin_material(name, with_face):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    skin, _ = g.img(os.path.join(MH, r"skins\middleage_caucasian_male\middleage_lightskinned_male_diffuse.png"), uv="UVMap")
    # a touch ruddier, sun-weathered
    col = g.mix(1.0, skin, (1.04, 0.93, 0.86, 1.0), "MULTIPLY")
    if with_face:
        x, y, z = g.xyz()
        # scalp under the hair edge darkened to the hair colour (no skin gaps at the hairline)
        hz = g.nt.nodes.new("ShaderNodeAttribute"); hz.attribute_name = "hairzone"
        col = g.mix(g.m("MULTIPLY", hz.outputs["Fac"], 0.95), col, g.rgb(HAIR_DARK))
        # eyebrows: the MakeHuman eyebrow001 texture, front-projected with an affine map fitted
        # to where the eyebrow proxy sat on this head (one fit per side)
        fits = brow_fits()
        brow = None
        for side in (1, -1):
            (a1, a2, a3, a4), (b1, b2, b3, b4), (u0, u1, v0, v1) = fits[side]
            u = g.m("ADD", g.m("MULTIPLY_ADD", x, a1, g.m("MULTIPLY_ADD", y, a2, g.m("MULTIPLY", z, a3))), a4)
            v = g.m("ADD", g.m("MULTIPLY_ADD", x, b1, g.m("MULTIPLY_ADD", y, b2, g.m("MULTIPLY", z, b3))), b4)
            cv = g.nt.nodes.new("ShaderNodeCombineXYZ"); g.link(u, cv.inputs[0]); g.link(v, cv.inputs[1])
            _, ba = g.img(os.path.join(MH, r"eyebrows\eyebrow001\eyebrow001.png"), vec=cv.outputs[0], extension="CLIP")
            sidemask = g.maprange(x, -0.004 * side, 0.004 * side, 0, 1)
            # only this brow's part of the texture (the other brow lies below/above in v)
            sidemask = g.m("MULTIPLY", sidemask, g.band(v, v0 - 0.02, v0 + 0.01, v1 - 0.01, v1 + 0.02))
            sidemask = g.m("MULTIPLY", sidemask, g.band(u, u0 - 0.02, u0 + 0.01, u1 - 0.01, u1 + 0.02))
            ba = g.m("MULTIPLY", ba, sidemask)
            brow = ba if brow is None else g.m("MAXIMUM", brow, ba)
        brow = g.m("MULTIPLY", brow, g.maprange(y, -0.06, -0.085, 0, 1))      # front of the face only
        bcol = g.mix(g.maprange(g.noise((900.0, 900.0, 900.0)), 0.55, 0.7, 0, 0.3),
                     g.rgb(hexlin("2A1E16")), g.rgb(hexlin("6A625C")))
        brow = g.m("POWER", brow, 0.6)                                       # fuller, a man's brow
        col = g.mix(g.m("MINIMUM", g.m("MULTIPLY", brow, 1.5), 0.95), col, bcol)
        # clipped moustache (front projection), dark brown flecked grey
        cx = g.nt.nodes.new("ShaderNodeCombineXYZ")
        g.link(x, cx.inputs[0]); g.link(z, cx.inputs[1])
        mp2 = g.nt.nodes.new("ShaderNodeMapping")
        mp2.inputs["Location"].default_value = (0.5, -1.530 / 0.04, 0.0)
        mp2.inputs["Scale"].default_value = (1 / 0.08, 1 / 0.04, 1.0)
        g.link(cx.outputs[0], mp2.inputs["Vector"])
        tn = g.nt.nodes.new("ShaderNodeTexImage"); tn.image = moustache_mask_image(); tn.extension = "CLIP"
        g.link(mp2.outputs["Vector"], tn.inputs["Vector"])
        front = g.maprange(y, -0.062, -0.078, 0, 1)        # whole upper lip, not only its front
        mm = g.m("MULTIPLY", tn.outputs["Color"], front)
        mcol = g.mix(g.maprange(g.noise((800.0, 800.0, 800.0)), 0.55, 0.7, 0, 0.35),
                     g.rgb(hexlin("2C2018")), g.rgb(hexlin("6E655E")))
        col = g.mix(mm, col, mcol)
    g.base(col)
    return mat


def cloth(name, path, tile, tweak=None):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = G(mat)
    c, _ = g.img(path, box=tile)
    if tweak:
        c = tweak(g, c)
    g.base(c)
    return mat


def build_source_materials():
    M = {}
    M["SKIN"] = skin_material("SRC_SKIN", False)            # target material of the low head/hands
    skin_material("SRC_SKIN_HI_HEAD", True)
    skin_material("SRC_SKIN_HI_HANDS", False)

    def suit_tweak(g, c):
        x, y, z = g.xyz()
        ax = g.m("ABSOLUTE", x)
        elbow = g.band(ax, 0.40, 0.425, 0.45, 0.475)                      # sheen at the elbows
        c = g.mix(g.m("MULTIPLY", elbow, 0.22), c, g.rgb((0.075, 0.072, 0.075, 1)))
        cuff = g.maprange(ax, 0.64, 0.68, 0, 1)                           # worn cuff edges
        c = g.mix(g.m("MULTIPLY", cuff, 0.18), c, g.rgb((0.08, 0.078, 0.08, 1)))
        dust = g.m("MULTIPLY", g.maprange(z, 0.12, 0.04, 0, 1), g.maprange(g.noise((60.0, 60.0, 60.0)), 0.3, 0.7, 0.4, 1.0))
        c = g.mix(g.m("MULTIPLY", dust, 0.30), c, g.rgb(hexlin("5E574C")))   # dust on the turn-ups
        return c
    M["SUIT"] = cloth("SRC_SUIT", os.path.join(TEX, "suit_charcoal_herringbone.jpg"), 0.27, suit_tweak)

    M["SHIRT"] = cloth("SRC_SHIRT", os.path.join(TEX, "shirt_white_poplin.jpg"), 0.29)
    M["HANKY"] = cloth("SRC_HANKY", os.path.join(TEX, "shirt_white_poplin.jpg"), 0.29,
                       lambda g, c: g.mix(1.0, c, (1.08, 1.08, 1.1, 1.0), "MULTIPLY"))

    def shoe_tweak(g, c):
        x, y, z = g.xyz()
        lx = g.m("ABSOLUTE", g.m("SUBTRACT", g.m("ABSOLUTE", x), 0.088))
        lacing = g.m("MULTIPLY", g.maprange(lx, 0.014, 0.009, 0, 1), g.band(y, -0.115, -0.105, -0.045, -0.035))
        lacing = g.m("MULTIPLY", lacing, g.maprange(z, 0.050, 0.060, 0, 1))
        lines = g.maprange(g.m("SINE", g.m("MULTIPLY", y, 2 * math.pi / 0.0085)), 0.2, 0.7, 0, 1)
        c = g.mix(g.m("MULTIPLY", lacing, 0.85), c, g.mix(lines, g.rgb((0.004, 0.004, 0.004, 1)), g.rgb((0.05, 0.045, 0.04, 1))))
        cap = g.band(y, -0.215, -0.212, -0.208, -0.205)                           # toe-cap seam
        c = g.mix(g.m("MULTIPLY", cap, 0.8), c, g.rgb((0.0, 0.0, 0.0, 1)))
        dust = g.m("MULTIPLY", g.maprange(z, 0.035, 0.06, 0, 1), g.maprange(y, -0.16, -0.24, 0, 1))
        c = g.mix(g.m("MULTIPLY", dust, 0.20), c, g.rgb(hexlin("4A443C")))
        return c
    M["SHOE"] = cloth("SRC_SHOE", os.path.join(TEX, "shoe_black_calf.jpg"), 0.40, shoe_tweak)

    mat = bpy.data.materials.get("SRC_TIE"); g = G(mat)
    vor = g.nt.nodes.new("ShaderNodeTexVoronoi"); vor.feature = "F1"; vor.inputs["Scale"].default_value = 260.0
    g.link(g.tc().outputs["Object"], vor.inputs["Vector"])
    dots = g.maprange(vor.outputs["Distance"], 0.16, 0.10, 0, 1)
    g.base(g.mix(g.m("MULTIPLY", dots, 0.55), g.rgb(hexlin("5A1F24")), g.rgb(hexlin("8A5A50"))))

    mat = bpy.data.materials.get("SRC_HAIR"); g = G(mat); g.base(hair_colour(g))

    mat = bpy.data.materials.get("SRC_EYE"); g = G(mat)
    c, _ = g.img(os.path.join(MH, r"eyes\materials\brownlight_eye.png"), uv="UVMap")
    g.base(g.mix(1.0, c, (0.80, 0.74, 0.70, 1.0), "MULTIPLY"))

    mat = bpy.data.materials.get("SRC_GOLD"); g = G(mat)
    g.base(g.mix(g.maprange(g.noise((400.0, 400.0, 400.0)), 0.4, 0.6, 0, 0.5), g.rgb(hexlin("B8964A")), g.rgb(hexlin("E3C77A"))))
    mat = bpy.data.materials.get("SRC_TAPE"); g = G(mat)
    x, y, z = g.xyz()
    marks = g.maprange(g.m("FRACT", g.m("DIVIDE", z, 0.0254)), 0.0, 0.07, 1, 0)
    half = g.maprange(g.m("FRACT", g.m("DIVIDE", g.m("ADD", z, 0.0127), 0.0254)), 0.0, 0.04, 0.6, 0)
    k = g.m("MAXIMUM", marks, half)
    g.base(g.mix(g.m("MULTIPLY", k, 0.9), g.rgb(hexlin("E6D79A")), g.rgb((0.02, 0.02, 0.02, 1))))
    mat = bpy.data.materials.get("SRC_PENCIL"); g = G(mat); g.base(hexlin("E8B820"))
    mat = bpy.data.materials.get("SRC_BUTTON"); g = G(mat); g.base(hexlin("241C17"))
    return M


# ----------------------------------------------------------------------------------------------
# 2. atlas UVs
# ----------------------------------------------------------------------------------------------
def win_ctx():
    win = bpy.context.window_manager.windows[0]
    area = next(a for a in win.screen.areas if a.type == "VIEW_3D")
    region = next(r for r in area.regions if r.type == "WINDOW")
    return bpy.context.temp_override(window=win, screen=win.screen, area=area, region=region)


def parts():
    return [o for o in bpy.data.collections[COLL].objects if o.type == "MESH" and o.name.startswith("PART_")]


def select_only(objs, active):
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = active


def uv_area(ob, layer):
    a = 0.0
    uv = ob.data.uv_layers[layer].data
    for p in ob.data.polygons:
        pts = [uv[i].uv for i in p.loop_indices]
        for k in range(1, len(pts) - 1):
            a += abs((pts[k] - pts[0]).cross(pts[k + 1] - pts[0])) * 0.5
    return a


def make_atlas_uvs():
    P = parts()
    for ob in P:
        me = ob.data
        if "Atlas" in me.uv_layers:
            me.uv_layers.remove(me.uv_layers["Atlas"])
        keep_mh = ob.name in ("PART_head", "PART_hands", "PART_eyes") and "UVMap" in me.uv_layers
        if keep_mh:
            me.uv_layers.active = me.uv_layers["UVMap"]
        lay = me.uv_layers.new(name="Atlas", do_init=keep_mh)
        me.uv_layers.active = lay
        if not keep_mh:
            select_only([ob], ob)
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.002, scale_to_bounds=False)
            bpy.ops.object.mode_set(mode="OBJECT")
    # uniform texel density, then weight per part
    select_only(P, P[0])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode="OBJECT")
    tot_w = sum(PART_WEIGHT.get(o.name, 0.01) for o in P)
    for ob in P:
        a = uv_area(ob, "Atlas")
        f = math.sqrt((PART_WEIGHT.get(ob.name, 0.01) / tot_w) / max(a, 1e-9))
        uv = ob.data.uv_layers["Atlas"].data
        co = np.empty(len(uv) * 2, np.float32); uv.foreach_get("uv", co)
        uv.foreach_set("uv", co * f)
    select_only(P, P[0])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    try:
        bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, shape_method="CONCAVE",
                                margin_method="FRACTION", margin=0.003)
    except TypeError:
        bpy.ops.uv.pack_islands(rotate=True, scale=True, margin_method="FRACTION", margin=0.003)
    bpy.ops.object.mode_set(mode="OBJECT")
    share = {o.name: round(uv_area(o, "Atlas"), 4) for o in P}
    print("ATLAS UV share", share, "fill", round(sum(share.values()), 3))


# ----------------------------------------------------------------------------------------------
# 3. bakes
# ----------------------------------------------------------------------------------------------
def new_image(name, colour=(0, 0, 0, 1), noncolor=False):
    im = bpy.data.images.get(name)
    if im:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(name, SIZE, SIZE, alpha=False, float_buffer=False)
    im.generated_color = colour
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    return im


def set_target(mats, image):
    """Add/point a target image node in each material and make it active (bake target)."""
    for m in mats:
        nt = m.node_tree
        n = next((x for x in nt.nodes if x.type == "TEX_IMAGE" and x.label == "BAKE_TARGET"), None)
        if n is None:
            n = nt.nodes.new("ShaderNodeTexImage"); n.label = "BAKE_TARGET"
            u = nt.nodes.new("ShaderNodeUVMap"); u.uv_map = "Atlas"; u.label = "BAKE_UV"
            nt.links.new(u.outputs[0], n.inputs["Vector"])
        n.image = image
        nt.nodes.active = n
        n.select = True


def clear_targets():
    for m in bpy.data.materials:
        if m.node_tree:
            for n in list(m.node_tree.nodes):
                if n.label in ("BAKE_TARGET", "BAKE_UV"):
                    m.node_tree.nodes.remove(n)


def bake_all():
    sc = bpy.context.scene
    try:
        sc.render.engine = "CYCLES"
    except TypeError as e:
        print("engine", e)
    sc.cycles.device = "GPU"
    sc.cycles.samples = 64
    sc.render.bake.margin = 6
    arm = bpy.data.objects["Pickell_Rig"]
    arm.data.pose_position = "REST"
    # only the figure renders: hide helpers / sources / donor from render
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
    col = new_image("PK_atlas_colour", (0.5, 0.5, 0.5, 1))
    src_mats = [bpy.data.materials["SRC_" + k] for k in
                ("SKIN", "HAIR", "EYE", "SUIT", "SHIRT", "TIE", "SHOE", "GOLD", "TAPE", "PENCIL", "BUTTON", "HANKY")]
    set_target(src_mats, col)
    bk = sc.render.bake
    # (a) clothes, hair, eyes, accessories: their own materials
    others = [o for o in P if o not in (head, hands)]
    select_only(others, others[0])
    bk.use_selected_to_active = False
    bk.use_clear = True
    bk.target = "IMAGE_TEXTURES"
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, use_clear=True, margin=6)
    # (b) head and hands from the full-resolution MakeHuman meshes
    work = bpy.data.collections.get("NPC_Pickell_Work")
    if work:
        work.hide_render = False                         # objects inside stay hidden individually
    for lo, hi in ((head, hi_head), (hands, hi_hands)):
        hi.hide_render = False
        select_only([hi, lo], lo)
        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, use_selected_to_active=True,
                            cage_extrusion=0.006, max_ray_distance=0.02, use_clear=False, margin=6)
        hi.hide_render = True
    if work:
        work.hide_render = True
    # (c) crease shading (AO) of the whole figure in its rest pose
    ao = new_image("PK_atlas_ao", (1, 1, 1, 1), noncolor=True)
    set_target(src_mats, ao)
    if sc.world is None:
        sc.world = bpy.data.worlds.new("World")
    sc.world.light_settings.distance = 0.12           # crease-scale occlusion
    PA = [o for o in P if o.name != "PART_eyes"]          # eyeballs sit deep: no AO on them
    select_only(PA, PA[0])
    sc.cycles.samples = 128
    bpy.ops.object.bake(type="AO", use_selected_to_active=False, use_clear=True, margin=6)
    # second passes: a part is re-baked with the parts that lie over it hidden, so wherever it
    # peeks out in motion it shows as cloth, not as a black (fully occluded) patch
    def rebake(target, hide):
        obs = [bpy.data.objects[h] for h in hide]
        for o in obs:
            o.hide_render = True
        t = bpy.data.objects[target]
        select_only([t], t)
        bpy.ops.object.bake(type="AO", use_selected_to_active=False, use_clear=False, margin=3)
        for o in obs:
            o.hide_render = False
    rebake("PART_trousers", ["PART_jacket"])
    rebake("PART_jacket", ["PART_collar", "PART_accessories"])
    rebake("PART_cuffs", ["PART_sleeves", "PART_hands"])
    # the eyeballs get no crease shading: write white into their islands
    eyes = bpy.data.objects["PART_eyes"]
    wm = bpy.data.materials.get("PK_BAKE_WHITE") or bpy.data.materials.new("PK_BAKE_WHITE")
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


def compose(col, ao):
    c = np.empty(SIZE * SIZE * 4, np.float32); col.pixels.foreach_get(c); c = c.reshape(SIZE, SIZE, 4)
    a = np.empty(SIZE * SIZE * 4, np.float32); ao.pixels.foreach_get(a); a = a.reshape(SIZE, SIZE, 4)[..., 0]
    shade = 0.30 + 0.70 * np.clip(a, 0, 1) ** 0.8      # crease shading, never fully black
    out = c.copy()
    out[..., :3] = c[..., :3] * shade[..., None]       # pixels are display-space (sRGB) values
    out[..., 3] = 1.0
    name = "PK_atlas"
    im = bpy.data.images.get(name)
    if im:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(name, SIZE, SIZE, alpha=False)
    im.pixels.foreach_set(out.ravel())
    im.filepath_raw = ATLAS_PATH
    im.file_format = "JPEG"
    try:
        im.save(filepath=ATLAS_PATH, quality=85)
    except TypeError:
        im.save()
    im2 = bpy.data.images.load(ATLAS_PATH, check_existing=False)
    im2.name = "npc-pickell-atlas"
    bpy.data.images.remove(im)
    print("ATLAS", ATLAS_PATH, os.path.getsize(ATLAS_PATH))
    return im2


# ----------------------------------------------------------------------------------------------
# 4. one mesh, one material, export
# ----------------------------------------------------------------------------------------------
def final_material(atlas):
    m = bpy.data.materials.get("M_Pickell") or bpy.data.materials.new("M_Pickell")
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = atlas
    u = nt.nodes.new("ShaderNodeUVMap"); u.uv_map = "Atlas"
    nt.links.new(u.outputs[0], t.inputs["Vector"])
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(b.outputs[0], out.inputs[0])
    b.inputs["Roughness"].default_value = 0.8
    b.inputs["Metallic"].default_value = 0.0
    m.use_backface_culling = False       # cloth shells are seen from inside at hems -> doubleSided
    return m


def join_and_export(atlas):
    clear_targets()
    P = parts()
    arm = bpy.data.objects["Pickell_Rig"]
    mat = final_material(atlas)
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
    body.name = body.data.name = "Pickell"
    body.data.materials.clear()
    body.data.materials.append(mat)
    for p in body.data.polygons:
        p.material_index = 0
    body.data.uv_layers["Atlas"].name = "UVMap"
    mat.node_tree.nodes[[n.type for n in mat.node_tree.nodes].index("UVMAP")].uv_map = "UVMap"
    for m in [m for m in body.modifiers if m.type != "ARMATURE"]:
        body.modifiers.remove(m)
    arm_mods = [m for m in body.modifiers if m.type == "ARMATURE"]
    for m in arm_mods[1:]:
        body.modifiers.remove(m)
    # attributes the web doesn't need
    for a in [a for a in body.data.attributes if a.name in ("hairzone",)]:
        body.data.attributes.remove(a)
    for ca in list(body.data.color_attributes):
        body.data.color_attributes.remove(ca)
    tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
    # clips: one NLA track each, un-muted for the exporter
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


def run():
    with win_ctx():
        build_source_materials()
        make_atlas_uvs()
        col, ao = bake_all()
        atlas = compose(col, ao)
        body = join_and_export(atlas)
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    return body


if not globals().get("PICKELL_LIB_ONLY"):
    run()
