"""
back_lots_preview.py - review previews of the baked back-lot buildings (run after
back_lots_bake.py). Same method as sidestreet_southeast_preview.py.

    exec(open(r"<project>/tools/blender/back_lots_preview.py").read())

EEVEE, view transform "Standard", every material of the model swapped for an unlit emission of
colour x lightmap x LIGHTMAP_SCALE (the web page's `baked-lighting` maths). Context drawn the same
way with their own lightmaps and intensities (both read from index.html): the Main St buildings
and the backdrops around the back lots; flat unlit planes for what js/ground.js draws (road,
walks, earth lanes) and the scene's ground disc. Writes assets/models/previews/back-lots-*.png
(1280 px wide). Camera, engine, view transform, resolution and the model's materials are restored.

Scene -> Blender: (x, y, z) -> (x, -z, y).
"""

import math
import re
import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\back-lots-lightmap.jpg"
M = PROJECT + r"\assets\models" + "\\"
CONTEXT_GLBS = ["county-hotel.glb", "store-57.glb", "palace-theatre.glb", "block-35-41.glb",
                "block-24-30.glb", "block-32-38.glb", "block-40-46.glb", "rea-building.glb",
                "bank-building.glb", "lovells-restaurant.glb", "union-hotel.glb", "wurts-law-office.glb",
                "house-65-main.glb", "store-27.glb", "sidestreet-bloomfield.glb", "sidestreet-southeast.glb",
                "sidestreet-court.glb", "nevius-store.glb"]

scene = bpy.context.scene
r_obj = bpy.data.objects["BackLots"]
mesh = r_obj.data
scale = float(r_obj.get("lightmap_scale", 1.0))


def scene_entities():
    """{glb: (position, rotation y, lightmap file, intensity)} from index.html"""
    html = open(PROJECT + r"\index.html", encoding="utf8").read()
    out = {}
    for ent in re.findall(r"<a-entity\b[^>]*?>", html, re.S):
        m = re.search(r'gltf-model="url\(([^)?]*)', ent)
        bl = re.search(r'baked-lighting="lightmap:\s*([^;"?]+)[^;"]*;\s*intensity:\s*([\d.]+)', ent)
        if not m or not bl:
            continue
        pos = re.search(r'\sposition="([^"]*)"', ent)
        rot = re.search(r'\srotation="([^"]*)"', ent)
        p = [float(v) for v in (pos.group(1) if pos else "0 0 0").split()]
        r = [float(v) for v in (rot.group(1) if rot else "0 0 0").split()]
        out[m.group(1).split("/")[-1]] = (p, r[1], PROJECT + "\\" + bl.group(1).strip().replace("/", "\\"),
                                          float(bl.group(2)))
    return out


pcol = bpy.data.collections.get("BL_Preview")
if not pcol:
    pcol = bpy.data.collections.new("BL_Preview")
    scene.collection.children.link(pcol)
pcol.hide_viewport = pcol.hide_render = False
cam_data = bpy.data.cameras.get("BL_Cam") or bpy.data.cameras.new("BL_Cam")
cam = bpy.data.objects.get("BL_Cam") or bpy.data.objects.new("BL_Cam", cam_data)
if cam.name not in pcol.objects:
    pcol.objects.link(cam)
cam_data.clip_end = 900
cam_data.sensor_fit = "HORIZONTAL"
cam_data.sensor_width = 36

lm_img = bpy.data.images.load(LIGHTMAP, check_existing=True)
lm_img.reload()
lm_img.colorspace_settings.name = "sRGB"


def sock(socks, name):
    return next(x for x in socks if x.name == name and x.type == "RGBA")


def preview_material(src, lm_image, lm_scale, lm_uv, uv0_name):
    mat = bpy.data.materials.new("BLP_" + src.name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    emit = N("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = lm_scale
    uv1 = N("ShaderNodeUVMap")
    uv1.uv_map = lm_uv
    lm = N("ShaderNodeTexImage")
    lm.image = lm_image
    L(uv1.outputs["UV"], lm.inputs["Vector"])
    mix = N("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    src_tex = next((n for n in src.node_tree.nodes if n.type == "TEX_IMAGE"), None) if src.node_tree else None
    src_tint = next((n for n in src.node_tree.nodes if n.type == "MIX" and n.blend_type == "MULTIPLY"),
                    None) if src.node_tree else None
    bsdf = next((n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if src.node_tree else None
    if src_tex:
        uv0 = N("ShaderNodeUVMap")
        uv0.uv_map = uv0_name
        tex = N("ShaderNodeTexImage")
        tex.image = src_tex.image
        L(uv0.outputs["UV"], tex.inputs["Vector"])
        colour = tex.outputs["Color"]
        if src_tint:
            t = N("ShaderNodeMix")
            t.data_type = "RGBA"
            t.blend_type = "MULTIPLY"
            t.inputs["Factor"].default_value = 1.0
            L(colour, sock(t.inputs, "A"))
            sock(t.inputs, "B").default_value = sock(src_tint.inputs, "B").default_value
            colour = sock(t.outputs, "Result")
        L(colour, sock(mix.inputs, "A"))
    elif bsdf:
        sock(mix.inputs, "A").default_value = bsdf.inputs["Base Color"].default_value
    L(lm.outputs["Color"], sock(mix.inputs, "B"))
    L(sock(mix.outputs, "Result"), emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def unlit(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*rgb, 1)
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs["Emission"], o.inputs["Surface"])
    return m


def sbox(name, x0, x1, z0, z1, y0, y1, mat):
    """scene-coordinate box (context, unlit)"""
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
    me = bpy.data.meshes.new(name)
    v = [(x, -z, y) for y in (y0, y1) for z in (z0, z1) for x in (x0, x1)]
    me.from_pydata(v, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    pcol.objects.link(o)


# context ground (js/ground.js and the scene disc)
sbox("BLP_Disc", -400, 400, -400, 400, -0.05, 0.0, unlit("BLP_DiscMat", (0.15, 0.14, 0.08)))
road = unlit("BLP_RoadMat", (0.20, 0.18, 0.15))
sbox("BLP_MainRoad", -6.4, 6.4, -200, 80, 0.0, 0.01, road)
sbox("BLP_Bloomfield", 6.4, 60, -86.5, -79.9, 0.0, 0.01, road)
walk = unlit("BLP_WalkMat", (0.36, 0.35, 0.32))
sbox("BLP_WalkW", -10.3, -6.4, -200, 0, 0.0, 0.15, walk)
sbox("BLP_WalkE", 6.4, 10.3, -200, -89.9, 0.0, 0.15, walk)
sbox("BLP_WalkEM", 6.4, 10.3, -77.3, 0, 0.0, 0.15, walk)
earth = unlit("BLP_EarthMat", (0.23, 0.19, 0.13))
for name, (x0, x1, z0, z1) in {"PalaceAlley": (-35, -10.3, -139.2, -135.9), "Smith": (-57.5, -10.3, -100.1, -94.5),
                               "Lane32": (7.6, 58, -140.9, -137.8), "Gap68": (10.3, 36, -49.1, -45.6),
                               "GapHotel": (10.3, 45, -15.9, -11.3)}.items():
    sbox("BLP_" + name, x0, x1, z0, z1, 0.0, 0.012, earth)

# neighbours with their own lightmaps
for o in [o for o in pcol.objects if o.name.startswith("BLP_CTX")]:
    bpy.data.objects.remove(o, do_unlink=True)
ents = scene_entities()
for glb in CONTEXT_GLBS:
    (px, py, pz), rot, lmf, inten = ents[glb]
    _before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=M + glb)
    img = bpy.data.images.load(lmf, check_existing=True)
    img.colorspace_settings.name = "sRGB"
    for o in [o for o in bpy.data.objects if o not in _before]:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        pcol.objects.link(o)
        o.name = "BLP_CTX_" + glb[:-4]
        if o.parent is None:
            o.rotation_mode = "XYZ"
            o.location = (px, -pz, py)
            o.rotation_euler = (0, 0, math.radians(rot))
        if o.type == "MESH":
            uvs = [u.name for u in o.data.uv_layers]
            for i, m in enumerate(list(o.data.materials)):
                if len(uvs) > 1:
                    o.data.materials[i] = preview_material(m, img, inten, uvs[1], uvs[0])

# --- remember and change settings ----------------------------------------------
originals = list(mesh.materials)
previews = [preview_material(m, lm_img, scale, "Lightmap", "UVMap") for m in originals]
saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
render_state = {c.name: c.hide_render for c in bpy.data.collections}
loose_state = {o.name: o.hide_render for o in scene.collection.objects}
for o in scene.collection.objects:
    o.hide_render = True
for i, m in enumerate(previews):
    mesh.materials[i] = m
world = scene.world
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
saved_bg = (tuple(bg.inputs[0].default_value), bg.inputs[1].default_value)
bg.inputs[0].default_value = (0.42, 0.55, 0.78, 1)
bg.inputs[1].default_value = 1.0
scene.camera = cam
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = eng
        break
    except TypeError:
        pass
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.resolution_percentage = 100


def S(x, y, z):
    return (x, -z, y)


VIEWS = {
    # A1 blacksmith: down the blacksmith's lane (z -100.1 .. -94.5), eye 1.75 m
    "from-main-blacksmith-lane":  dict(eye=S(8.0, 1.75, -97.3), target=S(-73, 2.2, -98.6), lens=30),
    "blacksmith-lane-mouth":      dict(eye=S(-10.0, 1.75, -97.3), target=S(-73, 2.2, -98.6), lens=35),
    # A2 + A3: down the lane at 32 (z -140.9 .. -137.8)
    "from-main-lane32":           dict(eye=S(-8.0, 1.75, -139.3), target=S(64, 2.0, -141.0), lens=30),
    "lane32-mouth":               dict(eye=S(7.4, 1.75, -139.3), target=S(64, 2.0, -142.5), lens=32),
    # A4 + A5: through carriageway 40 (z -124.2 .. -121.5) and over the low rear of 32-38
    "from-main-carriageway40":    dict(eye=S(-8.0, 1.75, -122.8), target=S(45, 2.5, -121.5), lens=30),
    "from-main-west-walk-118":    dict(eye=S(-9.0, 1.75, -128.0), target=S(70, 5.0, -121.0), lens=40),
    # A6 + A7: down the gap between 68 Main and the Union Hotel (z -49.1 .. -45.6)
    "from-main-gap68":            dict(eye=S(-8.0, 1.75, -47.3), target=S(60, 2.2, -49.0), lens=30),
    "gap68-mouth":                dict(eye=S(10.0, 1.75, -47.3), target=S(60, 2.2, -49.5), lens=30),
    # overviews of each group
    "overview-a1":                dict(eye=S(-40, 22, -82), target=S(-65, 1.5, -99), lens=30, h=800),
    "overview-a2-a3":             dict(eye=S(35, 24, -122), target=S(61, 1.5, -145), lens=30, h=800),
    "overview-a4-a5":             dict(eye=S(30, 28, -95), target=S(58, 2.0, -120), lens=30, h=800),
    "overview-a6-a7":             dict(eye=S(20, 26, -28), target=S(54, 2.0, -51), lens=28, h=800),
    "overview-a6-a7-north":       dict(eye=S(30, 22, -80), target=S(52, 2.0, -51), lens=30, h=800),
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS
written = []
try:
    for name, v in VIEWS.items():
        for c in bpy.data.collections:
            c.hide_render = c.name not in ("BackLots", "BL_Preview")
        eye, target = Vector(v["eye"]), Vector(v["target"])
        cam.location = eye
        cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = v["lens"]
        scene.render.resolution_x, scene.render.resolution_y = 1280, v.get("h", 720)
        scene.render.filepath = PREV + "back-lots-" + name + ".png"
        bpy.ops.render.render(write_still=True)
        written.append(scene.render.filepath)
finally:
    for i, m in enumerate(originals):
        mesh.materials[i] = m
    for m in previews:
        bpy.data.materials.remove(m)
    for name, state in render_state.items():
        if bpy.data.collections.get(name):
            bpy.data.collections[name].hide_render = state
    for name, state in loose_state.items():
        if bpy.data.objects.get(name):
            bpy.data.objects[name].hide_render = state
    pcol.hide_render = pcol.hide_viewport = True
    bg.inputs[0].default_value, bg.inputs[1].default_value = saved_bg
    scene.camera = saved["camera"] or cam
    scene.render.engine = saved["engine"]
    scene.view_settings.view_transform = saved["vt"]
    scene.view_settings.look = saved["look"]
    scene.render.resolution_x, scene.render.resolution_y = saved["rx"], saved["ry"]
    scene.render.resolution_percentage = saved["pct"]
print("previews written:", *written, sep="\n  ")
