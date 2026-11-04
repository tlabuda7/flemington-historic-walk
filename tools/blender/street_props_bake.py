"""
Street props kit - colour atlas + baked ambient occlusion + GLB export.

Run in Blender right after tools/blender/street_props.py (it needs the SRC_* material slots, so
re-run the geometry script first when rebuilding):
    exec(open(r"<project>/tools/blender/street_props_bake.py").read())

The props are stamped all along both sides of the street (front facing east and west), so there is
NO sun bake here: colour x ambient occlusion only, and the scene lights do the rest.

1. Lettering mask ("GROCERIES", "ICE CREAM / SODA", "GASOLINE", plain serif capitals) rendered
   with Workbench into a temporary PNG, read through the "Aux" UV.
2. Source materials (SRC_*): Poly Haven CC0 colour maps box-projected in metres
   (old_planks_02, granite_rough_grey, granite_dressed_light, rust_coarse_01,
   iron_paint_redbrown, metal_plate_02, wood_table_worn) plus flat paints, with weathering:
   creosote pole base and bleached top, grime low on the granite, a water stain under the spout,
   rust and chips on the iron, scuffed board feet.
3. One "Atlas" UV for all 12 props (smart project, equal texel density with per-prop weights,
   packed), Cycles bakes: DIFFUSE colour of every prop + AO (props laid out in a row on a
   ground plane, 0.5 m reach) -> atlas = colour x (0.32 + 0.68 AO), saved as JPEG q85
   (assets/textures/street-props-atlas.jpg, sRGB, 2048^2).
4. One material M_StreetProps (lit, roughness 0.9, metallic 0, no alpha) on all 12 objects, each
   object back at the origin, export assets/models/street-props.glb (12 nodes, one texture).
"""
import bpy, os, math, tempfile
import numpy as np
from mathutils import Vector

ROOT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
TEX = os.path.join(ROOT, r"assets\textures\street-props")
PH = os.path.join(ROOT, r"assets\textures\polyhaven")
ATLAS_PATH = os.path.join(ROOT, r"assets\textures\street-props-atlas.jpg")
GLB_PATH = os.path.join(ROOT, r"assets\models\street-props.glb")
BLEND = os.path.join(ROOT, r"assets\models\source\street-props.blend")
COLL = "street_props"
SIZE = 2048

_ns = {"STREET_PROPS_LIB_ONLY": True, "__name__": "street_props_lib"}
exec(open(os.path.join(ROOT, r"tools\blender\street_props.py")).read(), _ns)
MNAMES, LETTER_REGIONS, GAS_BAND_V = _ns["MNAMES"], _ns["LETTER_REGIONS"], _ns["GAS_BAND_V"]
PROPS = [n for n, _ in _ns["BUILDERS"]]

# row layout used while baking AO (and by the preview script); arc lamp at its street height
LINEUP = {"pole": (0, 0, 0), "pole_lamp": (0, 0, 0), "arc_lamp": (2.2, 0, 8.35), "fountain": (4.6, 0, 0),
          "hitching_post": (6.6, 0, 0), "carriage_step": (8.0, 0, 0), "hydrant": (9.6, 0, 0),
          "shop_goods": (11.4, 0, 0), "sandwich_board_groceries": (13.4, 0, 0),
          "sandwich_board_icecream": (14.8, 0, 0), "bicycle": (16.4, 0, 0), "gas_pump": (18.2, 0, 0)}
# relative texel density (linear) per prop; 1.0 = the kit average
DENSITY = {"pole": 0.55, "pole_lamp": 1.0, "arc_lamp": 0.8, "fountain": 1.35, "hitching_post": 1.1,
           "carriage_step": 0.9, "hydrant": 1.35, "shop_goods": 1.0, "sandwich_board_groceries": 1.9,
           "sandwich_board_icecream": 1.9, "bicycle": 1.0, "gas_pump": 1.5}


def srgb_to_lin(x):
    return ((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92


def hexlin(h):
    h = h.lstrip("#")
    return tuple(srgb_to_lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1.0,)


# ----------------------------------------------------------------------------------------------
# node helper
# ----------------------------------------------------------------------------------------------
class G:
    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.out = self.nt.nodes.new("ShaderNodeOutputMaterial")
        self.bsdf = self.nt.nodes.new("ShaderNodeBsdfPrincipled")
        self.nt.links.new(self.bsdf.outputs[0], self.out.inputs[0])
        self.bsdf.inputs["Roughness"].default_value = 0.9
        self._tc = None
        self._xyz = None
        self._aux = None

    def link(self, a, b):
        self.nt.links.new(a, b)

    def tc(self):
        if self._tc is None:
            self._tc = self.nt.nodes.new("ShaderNodeTexCoord")
        return self._tc

    def xyz(self):
        if self._xyz is None:
            s = self.nt.nodes.new("ShaderNodeSeparateXYZ")
            self.link(self.tc().outputs["Object"], s.inputs[0])
            self._xyz = s.outputs
        return self._xyz

    def aux(self):
        if self._aux is None:
            u = self.nt.nodes.new("ShaderNodeUVMap"); u.uv_map = "Aux"
            s = self.nt.nodes.new("ShaderNodeSeparateXYZ")
            self.link(u.outputs[0], s.inputs[0])
            self._aux = (u.outputs[0], s.outputs[0], s.outputs[1])
        return self._aux

    def _set(self, sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, tuple):
            sock.default_value = v
        else:
            self.link(v, sock)

    def m(self, op, a, b=None, c=None, clamp=False):
        n = self.nt.nodes.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is not None:
                self._set(n.inputs[i], v)
        return n.outputs[0]

    def maprange(self, v, a, b, c=0.0, d=1.0):
        n = self.nt.nodes.new("ShaderNodeMapRange"); n.interpolation_type = "SMOOTHSTEP"; n.clamp = True
        self._set(n.inputs["Value"], v)
        n.inputs["From Min"].default_value = a; n.inputs["From Max"].default_value = b
        n.inputs["To Min"].default_value = c; n.inputs["To Max"].default_value = d
        return n.outputs["Result"]

    def mix(self, fac, a, b, blend="MIX"):
        n = self.nt.nodes.new("ShaderNodeMix"); n.data_type = "RGBA"; n.blend_type = blend; n.clamp_result = True
        for sock, v in ((n.inputs[0], fac), (n.inputs[6], a), (n.inputs[7], b)):
            self._set(sock, v)
        return n.outputs[2]

    def vec(self, x, y, z=0.0):
        n = self.nt.nodes.new("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)):
            self._set(n.inputs[i], v)
        return n.outputs[0]

    def img(self, path, vec=None, box=None, loc=(0, 0, 0), rot=(0, 0, 0), noncolor=False):
        """Image texture; box = (sx, sy, sz) real tile size in metres for object-space box projection."""
        n = self.nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(path, check_existing=True)
        if noncolor:
            n.image.colorspace_settings.name = "Non-Color"
        if box is not None:
            n.projection = "BOX"; n.projection_blend = 0.25
            mp = self.nt.nodes.new("ShaderNodeMapping")
            b = box if isinstance(box, tuple) else (box, box, box)
            mp.inputs["Scale"].default_value = tuple(1.0 / s for s in b)
            mp.inputs["Location"].default_value = loc
            mp.inputs["Rotation"].default_value = rot
            self.link(self.tc().outputs["Object"], mp.inputs["Vector"])
            self.link(mp.outputs["Vector"], n.inputs["Vector"])
        elif vec is not None:
            self.link(vec, n.inputs["Vector"])
        return n.outputs["Color"]

    def img_data(self, image, vec):
        n = self.nt.nodes.new("ShaderNodeTexImage")
        n.image = image
        n.interpolation = "Cubic"
        self.link(vec, n.inputs["Vector"])
        return n.outputs["Color"]

    def noise(self, scale, detail=3.0, offset=(0, 0, 0)):
        mp = self.nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Location"].default_value = offset
        self.link(self.tc().outputs["Object"], mp.inputs["Vector"])
        n = self.nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        self.link(mp.outputs["Vector"], n.inputs["Vector"])
        return n.outputs["Fac"]

    def base(self, v):
        self._set(self.bsdf.inputs["Base Color"], v)


def flat(name, hx, var=0.08, scale=6.0):
    g = G(bpy.data.materials[name])
    c = hexlin(hx)
    n = g.noise(scale)
    f = g.maprange(n, 0.3, 0.7, 1.0 - var, 1.0 + var)
    g.base(g.mix(1.0, c, g.vec(f, f, f), "MULTIPLY"))
    return g


# ----------------------------------------------------------------------------------------------
# 1. lettering mask
# ----------------------------------------------------------------------------------------------
def lettering_mask():
    path = os.path.join(tempfile.gettempdir(), "street_props_letters.png")
    sc = bpy.data.scenes.get("SP_Letters") or bpy.data.scenes.new("SP_Letters")
    for o in list(sc.collection.objects):
        d = o.data
        bpy.data.objects.remove(o)
    font = None
    for f in ("BOOKOSB.TTF", "timesbd.ttf", "georgiab.ttf"):
        p = os.path.join(r"C:\Windows\Fonts", f)
        if os.path.exists(p):
            font = bpy.data.fonts.load(p, check_existing=True)
            break

    def text(body, x, y, maxw, maxh):
        cu = bpy.data.curves.new("SPL_" + body, "FONT")
        cu.body = body
        if font:
            cu.font = font
        cu.align_x = "CENTER"; cu.align_y = "CENTER"
        cu.size = 0.1
        ob = bpy.data.objects.new(cu.name, cu)
        sc.collection.objects.link(ob)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        me = ob.evaluated_get(dg).to_mesh()
        xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        ob.evaluated_get(dg).to_mesh_clear()
        k = min(maxw / w, maxh / h)
        cu.size = 0.1 * k
        ob.location = (x - cx * k, y - cy * k, 0)

    def rect(x0, y0, x1, y1):
        me = bpy.data.meshes.new("SPL_rect")
        me.from_pydata([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], [], [(0, 1, 2, 3)])
        ob = bpy.data.objects.new("SPL_rect", me)
        sc.collection.objects.link(ob)

    def frame(x0, y0, x1, y1, t):
        rect(x0, y0, x1, y0 + t); rect(x0, y1 - t, x1, y1)
        rect(x0, y0, x0 + t, y1); rect(x1 - t, y0, x1, y1)

    # sandwich boards (u range -> x = 2u, v -> y); panel 0.60 m wide, v = height 0..1 m
    for key, lines in (("groceries", [("GROCERIES", 0.62, 0.46, 0.11)]),
                       ("icecream", [("ICE CREAM", 0.72, 0.44, 0.10), ("\u00b7 SODA \u00b7", 0.52, 0.34, 0.10)])):
        u0, u1 = LETTER_REGIONS[key]
        x0, x1 = 2 * u0, 2 * u1
        frame(x0 + 0.035, 0.12, x1 - 0.035, 0.95, 0.012)
        frame(x0 + 0.06, 0.145, x1 - 0.06, 0.925, 0.005)
        for body, y, mw, mh in lines:
            text(body, (x0 + x1) / 2, y, mw, mh)
    u0, u1 = LETTER_REGIONS["gas"]
    v0, v1 = GAS_BAND_V
    # the band is mapped twice (front half and back half each run u0..u1), so the word appears
    # front and back; kept to the middle half of each half-band so the joins at the sides
    # (east/west) fall in blank band, and it is never seen wrapped round the edge
    text("GASOLINE", (u0 + u1), (v0 + v1) / 2, 0.25, 0.058)
    rect(2 * u0, v0, 2 * u1, v0 + 0.006); rect(2 * u0, v1 - 0.006, 2 * u1, v1)
    cam_d = bpy.data.cameras.get("SPL_cam") or bpy.data.cameras.new("SPL_cam")
    cam_d.type = "ORTHO"; cam_d.ortho_scale = 2.0
    cam = bpy.data.objects.new("SPL_cam", cam_d)
    sc.collection.objects.link(cam)
    cam.location = (1.0, 0.5, 5.0)
    sc.camera = cam
    w = bpy.data.worlds.get("SPL_black") or bpy.data.worlds.new("SPL_black")
    w.color = (0, 0, 0)
    sc.world = w
    for eng in ("BLENDER_WORKBENCH",):
        sc.render.engine = eng
    sh = sc.display.shading
    sh.light = "FLAT"; sh.color_type = "SINGLE"; sh.single_color = (1, 1, 1)
    sh.show_shadows = False; sh.show_cavity = False; sh.show_object_outline = False
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 2048, 1024, 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True, scene=sc.name)
    for o in list(sc.collection.objects):
        bpy.data.objects.remove(o)
    bpy.data.scenes.remove(sc)
    im = bpy.data.images.get("SP_letters")
    if im:
        bpy.data.images.remove(im)
    im = bpy.data.images.load(path)
    im.name = "SP_letters"
    im.colorspace_settings.name = "Non-Color"
    im.pack()
    print("LETTERS", path)
    return im


# ----------------------------------------------------------------------------------------------
# 2. source materials
# ----------------------------------------------------------------------------------------------
def build_source_materials(letters):
    t = lambda f: os.path.join(TEX, f)
    x, y, z = None, None, None

    # poles: one plank of old_planks_02 per face (no plank gaps), vertical grain
    g = G(bpy.data.materials["SRC_wood_pole"])
    c = g.img(t("old_planks_02.jpg"), box=(3.0, 3.0, 2.0), loc=(0.385, 0.385, 0.0))
    X, Y, Z = g.xyz()
    creo = g.m("MULTIPLY", g.maprange(Z, 1.9, 0.2), g.maprange(g.noise(2.0), 0.3, 0.7, 0.6, 1.0))
    c = g.mix(creo, c, g.mix(1.0, c, hexlin("3A2E24"), "MULTIPLY"))
    c = g.mix(g.maprange(Z, 4.0, 10.0, 0.0, 0.40), c, hexlin("9C968A"))
    c = g.mix(g.maprange(g.noise(1.5, offset=(5, 2, 0)), 0.45, 0.65, 0.0, 0.25), c, hexlin("4A4036"))
    c = g.mix(1.0, c, hexlin("B8B2A8"), "MULTIPLY")      # darker, greyer weathered wood
    g.base(c)

    g = G(bpy.data.materials["SRC_wood_arm"])
    c = g.img(t("old_planks_02.jpg"), box=(3.0, 2.0, 3.0), loc=(0.53, 0.0, 0.53), rot=(math.radians(90), 0, 0))
    g.base(g.mix(0.35, c, hexlin("8E897F")))

    # crates: slats from the Aux UV (u along, v across), a different plank per slat, dark gaps
    g = G(bpy.data.materials["SRC_wood_crate"])
    uvv, U, V = g.aux()
    q = g.m("DIVIDE", V, 0.1167)
    fr = g.m("FRACT", q)
    fl = g.m("FLOOR", q)
    vx = g.m("ADD", g.m("ADD", 0.315, g.m("MULTIPLY", fr, 0.09)), g.m("MULTIPLY", fl, 0.1426))
    c = g.img(t("old_planks_02.jpg"), vec=g.vec(vx, g.m("DIVIDE", U, 1.5)))
    c = g.mix(0.30, c, hexlin("A09480"))
    gap = g.m("MAXIMUM", g.maprange(fr, 0.07, 0.03), g.maprange(fr, 0.965, 0.995))
    g.base(g.mix(g.m("MULTIPLY", gap, 0.75), c, hexlin("1E1812")))

    # barrel: wood_table_worn per stave, dark joints; lid boards
    g = G(bpy.data.materials["SRC_barrel"])
    uvv, U, V = g.aux()
    fr = g.m("FRACT", U)
    fl = g.m("FLOOR", U)
    vx = g.m("ADD", g.m("MULTIPLY", fr, 0.10), g.m("MULTIPLY", fl, 0.137))
    c = g.img(os.path.join(PH, "wood_table_worn.jpg"), vec=g.vec(vx, g.m("DIVIDE", V, 0.6)))
    c = g.mix(0.25, c, hexlin("5C4630"))
    gap = g.m("MAXIMUM", g.maprange(fr, 0.05, 0.02), g.maprange(fr, 0.975, 0.995))
    g.base(g.mix(g.m("MULTIPLY", gap, 0.7), c, hexlin("1A120C")))

    # sandwich boards: dark green paint, scuffed to grey wood at the feet, cream lettering
    for name in ("SRC_board_green", "SRC_board_letters"):
        g = G(bpy.data.materials[name])
        X, Y, Z = g.xyz()
        n = g.noise(9.0, detail=4)
        paint = g.mix(1.0, hexlin("2E4A36"), g.vec(*(g.maprange(n, 0.3, 0.7, 0.85, 1.12),) * 3), "MULTIPLY")
        scuff = g.m("MULTIPLY", g.maprange(Z, 0.10, 0.01), g.maprange(g.noise(14.0, offset=(3, 1, 0)), 0.50, 0.60))
        paint = g.mix(scuff, paint, hexlin("6E665A"))
        if name == "SRC_board_letters":
            uvv, U, V = g.aux()
            mk = g.img_data(letters, uvv)
            fac = g.maprange(g.m("ADD", mk, 0.0), 0.25, 0.75)
            cream = g.mix(g.m("MULTIPLY", scuff, 0.6), hexlin("E2D6B4"), hexlin("9A9282"))
            paint = g.mix(fac, paint, cream)
        g.base(paint)

    # granite: rough-pitched monolith (grime low, water stain under the spout, blotches)
    g = G(bpy.data.materials["SRC_granite_rough"])
    X, Y, Z = g.xyz()
    c = g.img(t("granite_rough_grey.jpg"), box=1.8)
    grime = g.m("MULTIPLY", g.maprange(Z, 0.45, 0.02), g.maprange(g.noise(4.0), 0.3, 0.7, 0.5, 1.0))
    c = g.mix(g.m("MULTIPLY", grime, 0.55), c, g.mix(1.0, c, hexlin("6A6458"), "MULTIPLY"))
    stain = g.m("MULTIPLY", g.maprange(g.m("ABSOLUTE", X), 0.30, 0.18),
                g.m("MULTIPLY", g.maprange(Z, 0.55, 0.70), g.maprange(Z, 1.10, 0.95)))
    stain = g.m("MULTIPLY", stain, g.maprange(Y, -0.25, -0.30))
    c = g.mix(g.m("MULTIPLY", stain, 0.55), c, g.mix(1.0, c, hexlin("8A8A80"), "MULTIPLY"))
    blot = g.maprange(g.noise(2.2, offset=(1, 4, 2)), 0.55, 0.72, 0.0, 0.35)
    c = g.mix(blot, c, g.mix(1.0, c, hexlin("B4AE9C"), "MULTIPLY"))
    g.base(c)

    # dressed granite: bowl, medallion, posts, steps (grime low; dark ring inside the bowl rim)
    g = G(bpy.data.materials["SRC_granite_dressed"])
    X, Y, Z = g.xyz()
    c = g.img(t("granite_dressed_light.jpg"), box=1.125)
    grime = g.m("MULTIPLY", g.maprange(Z, 0.30, 0.0), g.maprange(g.noise(5.0), 0.3, 0.7, 0.4, 1.0))
    c = g.mix(g.m("MULTIPLY", grime, 0.5), c, g.mix(1.0, c, hexlin("6A6458"), "MULTIPLY"))
    blot = g.maprange(g.noise(3.0, offset=(2, 1, 5)), 0.55, 0.72, 0.0, 0.3)
    c = g.mix(blot, c, g.mix(1.0, c, hexlin("A8A290"), "MULTIPLY"))
    g.base(c)

    g = G(bpy.data.materials["SRC_water"])
    n = g.noise(12.0)
    g.base(g.mix(g.maprange(n, 0.3, 0.7), hexlin("161C1E"), hexlin("2A3432")))

    # cast iron: dark paint over metal_plate_02, rust breaking through
    g = G(bpy.data.materials["SRC_iron"])
    c = g.img(os.path.join(PH, "metal_plate_02.jpg"), box=0.8)
    c = g.mix(1.0, c, hexlin("5A544C"), "MULTIPLY")
    r = g.img(t("rust_coarse_01.jpg"), box=0.8)
    g.base(g.mix(g.maprange(g.noise(7.0, detail=5), 0.56, 0.70, 0.0, 0.75), c, r))

    g = G(bpy.data.materials["SRC_rust"])
    g.base(g.img(t("rust_coarse_01.jpg"), box=0.8))

    g = G(bpy.data.materials["SRC_hydrant"])
    c = g.img(t("iron_paint_redbrown.jpg"), box=0.8)
    r = g.img(t("rust_coarse_01.jpg"), box=0.5)
    chip = g.maprange(g.noise(11.0, detail=6, offset=(7, 3, 1)), 0.60, 0.68, 0.0, 0.85)
    g.base(g.mix(chip, c, g.mix(0.5, r, hexlin("2A2622"))))

    flat("SRC_glass_green", "9CC4AE", 0.06)
    flat("SRC_opal", "EEEDE6", 0.03, 3.0)
    flat("SRC_enamel_green", "1F4A30", 0.10)
    flat("SRC_enamel_white", "E6E6DE", 0.04)
    flat("SRC_bulb", "E8E4CC", 0.02)
    flat("SRC_black_enamel", "1E1E1E", 0.10, 20.0)
    flat("SRC_nickel", "9C9C96", 0.10, 20.0)
    flat("SRC_leather", "5A3A22", 0.12, 25.0)
    flat("SRC_rubber", "2E2C2A", 0.10, 20.0)
    flat("SRC_brass", "A08040", 0.12, 20.0)

    g = G(bpy.data.materials["SRC_pump_red"])
    c = g.img(os.path.join(PH, "metal_plate_02.jpg"), box=0.8)
    red = g.mix(0.45, hexlin("8A1E16"), c, "OVERLAY")
    X, Y, Z = g.xyz()
    dirt = g.m("MULTIPLY", g.maprange(Z, 0.35, 0.05), 0.5)
    g.base(g.mix(dirt, red, hexlin("3A2A22")))

    g = G(bpy.data.materials["SRC_gas_globe"])
    uvv, U, V = g.aux()
    mk = g.img_data(letters, uvv)
    g.base(g.mix(g.maprange(mk, 0.25, 0.75), hexlin("B02418"), hexlin("F2F0E8")))


# ----------------------------------------------------------------------------------------------
# 3. atlas UVs and bakes
# ----------------------------------------------------------------------------------------------
def win_ctx():
    win = bpy.context.window_manager.windows[0]
    area = next(a for a in win.screen.areas if a.type == "VIEW_3D")
    region = next(r for r in area.regions if r.type == "WINDOW")
    return bpy.context.temp_override(window=win, screen=win.screen, area=area, region=region)


def objs():
    return [bpy.data.objects[n] for n in PROPS]


def select_only(obs, active):
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in obs:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = active


def uv_area(ob, layer="Atlas"):
    uv = ob.data.uv_layers[layer].data
    a = 0.0
    for p in ob.data.polygons:
        pts = [uv[i].uv for i in p.loop_indices]
        for k in range(1, len(pts) - 1):
            a += abs((pts[k] - pts[0]).cross(pts[k + 1] - pts[0])) * 0.5
    return a


def make_atlas_uvs():
    P = objs()
    for ob in P:
        me = ob.data
        if "Atlas" in me.uv_layers:
            me.uv_layers.remove(me.uv_layers["Atlas"])
        lay = me.uv_layers.new(name="Atlas", do_init=False)
        me.uv_layers.active = lay
        select_only([ob], ob)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
    select_only(P, P[0])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode="OBJECT")
    for ob in P:
        uv = ob.data.uv_layers["Atlas"].data
        co = np.empty(len(uv) * 2, np.float32); uv.foreach_get("uv", co)
        uv.foreach_set("uv", co * DENSITY.get(ob.name, 1.0))
    select_only(P, P[0])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    try:
        bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, shape_method="CONCAVE",
                                margin_method="FRACTION", margin=0.004)
    except TypeError:
        bpy.ops.uv.pack_islands(rotate=True, scale=True, margin_method="FRACTION", margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")
    dens = {}
    for ob in P:
        area3 = sum(p.area for p in ob.data.polygons)
        dens[ob.name] = round(SIZE * math.sqrt(uv_area(ob) / max(area3, 1e-9)))
    print("ATLAS px/m", dens, "fill", round(sum(uv_area(o) for o in P), 3))


def new_image(name, colour, noncolor=False):
    im = bpy.data.images.get(name)
    if im:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(name, SIZE, SIZE, alpha=False, float_buffer=False)
    im.generated_color = colour
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    return im


def src_mats():
    return [bpy.data.materials[n] for n in MNAMES]


def set_target(image):
    for m in src_mats():
        nt = m.node_tree
        n = next((x for x in nt.nodes if x.type == "TEX_IMAGE" and x.label == "BAKE_TARGET"), None)
        if n is None:
            n = nt.nodes.new("ShaderNodeTexImage"); n.label = "BAKE_TARGET"
            u = nt.nodes.new("ShaderNodeUVMap"); u.uv_map = "Atlas"; u.label = "BAKE_UV"
            nt.links.new(u.outputs[0], n.inputs["Vector"])
        n.image = image
        for x in nt.nodes:
            x.select = False
        nt.nodes.active = n
        n.select = True


def clear_targets():
    for m in bpy.data.materials:
        if m.node_tree:
            for n in list(m.node_tree.nodes):
                if n.label in ("BAKE_TARGET", "BAKE_UV"):
                    m.node_tree.nodes.remove(n)


def lay_out(on=True):
    for n in PROPS:
        bpy.data.objects[n].location = LINEUP[n] if on else (0, 0, 0)


def bake_all():
    sc = bpy.context.scene
    try:
        sc.render.engine = "CYCLES"
    except TypeError as e:
        print("engine", e)
    sc.cycles.device = "GPU"
    sc.render.bake.margin = 6
    sc.render.bake.target = "IMAGE_TEXTURES"
    sc.render.bake.use_selected_to_active = False
    # only this kit renders
    for c in bpy.data.collections:
        if c.name != COLL:
            c.hide_render = True
    bpy.data.collections[COLL].hide_render = False
    P = objs()
    for ob in P:
        ob.data.uv_layers.active = ob.data.uv_layers["Atlas"]
        ob.hide_render = False
    lay_out(True)
    # ground plane for contact occlusion
    gme = bpy.data.meshes.new("SP_BakeGround")
    gme.from_pydata([(-6, -6, 0), (25, -6, 0), (25, 6, 0), (-6, 6, 0)], [], [(0, 1, 2, 3)])
    ground = bpy.data.objects.new("SP_BakeGround", gme)
    bpy.data.collections[COLL].objects.link(ground)
    col = new_image("SP_atlas_colour", (0.5, 0.5, 0.5, 1))
    set_target(col)
    select_only(P, P[0])
    sc.cycles.samples = 16
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, use_clear=True, margin=6)
    ao = new_image("SP_atlas_ao", (1, 1, 1, 1), noncolor=True)
    set_target(ao)
    if sc.world is None:
        sc.world = bpy.data.worlds.new("World")
    sc.world.light_settings.distance = 0.5
    sc.cycles.samples = 256
    select_only(P, P[0])
    bpy.ops.object.bake(type="AO", use_clear=True, margin=6)
    bpy.data.objects.remove(ground)
    bpy.data.meshes.remove(gme)
    lay_out(False)
    return col, ao


def compose(col, ao):
    c = np.empty(SIZE * SIZE * 4, np.float32); col.pixels.foreach_get(c); c = c.reshape(SIZE, SIZE, 4)
    a = np.empty(SIZE * SIZE * 4, np.float32); ao.pixels.foreach_get(a); a = a.reshape(SIZE, SIZE, 4)[..., 0]
    shade = 0.32 + 0.68 * np.clip(a, 0, 1) ** 0.9
    out = c.copy()
    out[..., :3] = np.clip(c[..., :3] * shade[..., None], 0, 1)
    out[..., 3] = 1.0
    im = bpy.data.images.get("SP_atlas_out")
    if im:
        bpy.data.images.remove(im)
    im = bpy.data.images.new("SP_atlas_out", SIZE, SIZE, alpha=False)
    im.pixels.foreach_set(out.ravel())
    im.filepath_raw = ATLAS_PATH
    im.file_format = "JPEG"
    try:
        im.save(filepath=ATLAS_PATH, quality=85)
    except TypeError:
        im.save()
    bpy.data.images.remove(im)
    old = bpy.data.images.get("street-props-atlas")
    if old:
        bpy.data.images.remove(old)
    im2 = bpy.data.images.load(ATLAS_PATH, check_existing=False)
    im2.name = "street-props-atlas"
    print("ATLAS", ATLAS_PATH, os.path.getsize(ATLAS_PATH), "bytes")
    return im2


# ----------------------------------------------------------------------------------------------
# 4. one material, export
# ----------------------------------------------------------------------------------------------
def final_material(atlas):
    m = bpy.data.materials.get("M_StreetProps") or bpy.data.materials.new("M_StreetProps")
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = atlas
    u = nt.nodes.new("ShaderNodeUVMap"); u.uv_map = "UVMap"
    nt.links.new(u.outputs[0], t.inputs["Vector"])
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(b.outputs[0], out.inputs[0])
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Metallic"].default_value = 0.0
    m.use_backface_culling = True
    return m


def finalize_and_export(atlas):
    clear_targets()
    mat = final_material(atlas)
    P = objs()
    tris = {}
    for ob in P:
        me = ob.data
        for lay in [l for l in me.uv_layers if l.name != "Atlas"]:
            me.uv_layers.remove(lay)
        me.uv_layers["Atlas"].name = "UVMap"
        me.materials.clear()
        me.materials.append(mat)
        for p in me.polygons:
            p.material_index = 0
        for ca in list(me.color_attributes):
            me.color_attributes.remove(ca)
        ob.location = (0, 0, 0)
        tris[ob.name] = sum(len(p.vertices) - 2 for p in me.polygons)
    select_only(P, P[0])
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
        export_texcoords=True, export_normals=True, export_tangents=False, export_attributes=False,
        export_vertex_color="NONE", export_materials="EXPORT", export_image_format="AUTO",
        export_animations=False, export_skins=False, export_morph=False)
    print("GLB", GLB_PATH, os.path.getsize(GLB_PATH), "bytes")
    print("TRIS", tris, "total", sum(tris.values()))
    return tris


def run():
    with win_ctx():
        letters = lettering_mask()
        build_source_materials(letters)
        make_atlas_uvs()
        col, ao = bake_all()
        atlas = compose(col, ao)
        finalize_and_export(atlas)
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)


if not globals().get("STREET_PROPS_BAKE_LIB_ONLY"):
    run()
