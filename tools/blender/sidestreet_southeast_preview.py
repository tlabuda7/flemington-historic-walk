"""
sidestreet_southeast_preview.py - review previews of the baked south-east backdrop (run after
sidestreet_southeast_bake.py). Same method as sidestreet_bloomfield_preview.py.

    exec(open(r"<project>/tools/blender/sidestreet_southeast_preview.py").read())

EEVEE, view transform "Standard", every material of the model swapped for an unlit emission of
colour x lightmap x LIGHTMAP_SCALE (the web page's `baked-lighting` maths). Context, drawn the
same way where it is baked: the Nevius, Odd Fellows, Masonic, Democrat, 100-102, 106 and Union
Hotel GLBs at their index.html places (own lightmaps and intensities); the landscape's `Town`
silhouettes (landscape.glb, unlit vertex colours, as in the scene); flat planes for Main St, the
alley and Higgins Ave mouths that js/ground.js draws; a plain box for the west side of Main St.
Views ending in "-trees" also show backdrop-tree.glb at the positions proposed for the scene
(lit by a preview sun, as the scene's trees are). Writes
assets/models/previews/sidestreet-southeast-*.png (1280 px wide). Camera, engine, view
transform, resolution and the model's materials are restored.

Scene -> Blender: (x, y, z) -> (x, -z, y).
"""

import math
import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\sidestreet-southeast-lightmap.jpg"
M = PROJECT + r"\assets\models" + "\\"
T = PROJECT + r"\assets\textures" + "\\"
CONTEXT = [  # glb, lightmap, intensity, scene position (index.html), rotation y
    ("nevius-store.glb", "nevius-store-lightmap.jpg", 1.1239, (10.3, 0.15, -7.33), -90),
    ("odd-fellows-hall.glb", "odd-fellows-hall-lightmap.jpg", 1.2485, (10.3, 0.15, 9.09), -90),
    ("masonic-hall.glb", "masonic-hall-lightmap.jpg", 1.1751, (10.00, 0.15, 30.92), -90),
    ("democrat-building.glb", "democrat-building-lightmap.jpg", 1.1571, (10.08, 0.15, 43.85), -90),
    ("store-100-102.glb", "store-100-102-lightmap.jpg", 1.1366, (10.30, 0.15, 52.01), -90),
    ("store-106.glb", "store-106-lightmap.jpg", 1.1209, (8.06, 0.15, 58.80), -90),
    ("union-hotel.glb", "union-hotel-lightmap.jpg", 1.214, (11.6, 0.15, -30.75), -90),
]
TREE_GLB = M + "backdrop-tree.glb"
# (x, z, scale, y) as sidestreet_southeast_bake.py
TREES = [(44.0, 12.5, 1.9, 0.15), (100.0, -20.0, 2.2, 0.15), (88.0, 30.0, 2.3, 0.15), (127.5, -1.0, 2.2, 0.0),
         (56.0, 59.0, 2.1, 0.15), (57.5, 70.5, 2.0, 0.15), (78.0, 73.0, 2.2, 0.15), (127.5, 66.0, 2.1, 0.0)]

scene = bpy.context.scene
r_obj = bpy.data.objects["SidestreetSoutheast"]
mesh = r_obj.data
scale = float(r_obj.get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("SE_Preview")
if not pcol:
    pcol = bpy.data.collections.new("SE_Preview")
    scene.collection.children.link(pcol)
tcol = bpy.data.collections.get("SE_PreviewTrees")
if not tcol:
    tcol = bpy.data.collections.new("SE_PreviewTrees")
    scene.collection.children.link(tcol)
pcol.hide_viewport = pcol.hide_render = False
cam_data = bpy.data.cameras.get("SE_Cam") or bpy.data.cameras.new("SE_Cam")
cam = bpy.data.objects.get("SE_Cam") or bpy.data.objects.new("SE_Cam", cam_data)
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
    mat = bpy.data.materials.new("SEP_" + src.name)
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


# context ground (js/ground.js area) and the west side of Main St
sbox("SEP_Disc", -400, 400, -400, 400, -0.05, 0.0, unlit("SEP_DiscMat", (0.15, 0.14, 0.08)))
road = unlit("SEP_RoadMat", (0.20, 0.18, 0.15))
sbox("SEP_MainRoad", -6.4, 6.4, -200, 80, 0.0, 0.01, road)
walk = unlit("SEP_WalkMat", (0.36, 0.35, 0.32))
sbox("SEP_WalkW", -10.3, -6.4, -200, 10.4, 0.0, 0.15, walk)
sbox("SEP_WalkWS", -8.0, -4.4, 10.4, 80, 0.0, 0.15, walk)
sbox("SEP_WalkE", 6.4, 10.3, -200, 62.1, 0.0, 0.15, walk)
sbox("SEP_WalkES", 6.4, 9.3, 68.7, 80, 0.0, 0.15, walk)
earth = unlit("SEP_EarthMat", (0.23, 0.19, 0.13))
sbox("SEP_Alley80", 10.3, 57.0, -3.3, 1.3, 0.0, 0.012, earth)
sbox("SEP_Alley86", 10.3, 29.0, 16.9, 21.7, 0.0, 0.012, earth)
sbox("SEP_GapHotel", 10.3, 45.0, -15.9, -11.3, 0.0, 0.012, earth)
sbox("SEP_HigginsRoad", 6.4, 40.0, 62.9, 67.9, 0.0, 0.01, road)
sbox("SEP_HigginsN", 6.9, 40.0, 62.1, 62.9, 0.0, 0.15, earth)
sbox("SEP_HigginsS", 6.9, 40.0, 67.9, 68.7, 0.0, 0.15, earth)
sbox("SEP_West", -40.0, -10.3, -60, 0, 0.0, 10.0, unlit("SEP_WestMat", (0.45, 0.40, 0.33)))

# the landscape's Town silhouettes (unlit vertex colours), as in the scene
for o in [o for o in pcol.objects if o.name.startswith("SEP_Town")]:
    bpy.data.objects.remove(o, do_unlink=True)
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=M + "landscape.glb")
for o in [o for o in bpy.data.objects if o not in _before]:
    if o.name.startswith("landscape_town"):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        pcol.objects.link(o)
        o.name = "SEP_Town"
        tm = bpy.data.materials.new("SEP_TownMat")
        tm.use_nodes = True
        tn = tm.node_tree
        tn.nodes.clear()
        va = tn.nodes.new("ShaderNodeVertexColor")
        te = tn.nodes.new("ShaderNodeEmission")
        to = tn.nodes.new("ShaderNodeOutputMaterial")
        tn.links.new(va.outputs["Color"], te.inputs["Color"])
        tn.links.new(te.outputs["Emission"], to.inputs["Surface"])
        o.data.materials.clear()
        o.data.materials.append(tm)
    else:
        bpy.data.objects.remove(o, do_unlink=True)

# the built neighbours with their own lightmaps
for o in [o for o in pcol.objects if o.name.startswith("SEP_CTX")]:
    bpy.data.objects.remove(o, do_unlink=True)
for glb, lmf, inten, (px, py, pz), rot in CONTEXT:
    _before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=M + glb)
    img = bpy.data.images.load(T + lmf, check_existing=True)
    img.colorspace_settings.name = "sRGB"
    for o in [o for o in bpy.data.objects if o not in _before]:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        pcol.objects.link(o)
        o.name = "SEP_CTX_" + glb[:-4]
        if o.parent is None:
            o.rotation_mode = "XYZ"
            o.location = (px, -pz, py)
            o.rotation_euler = (0, 0, math.radians(rot))
        if o.type == "MESH":
            uvs = [u.name for u in o.data.uv_layers]
            for i, m in enumerate(list(o.data.materials)):
                if len(uvs) > 1:
                    o.data.materials[i] = preview_material(m, img, inten, uvs[1], uvs[0])

# trees (only for the "-trees" views)
for o in list(tcol.objects):
    bpy.data.objects.remove(o, do_unlink=True)
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=TREE_GLB)
tree_src = [o for o in bpy.data.objects if o not in _before]
for o in tree_src:
    for c in list(o.users_collection):
        c.objects.unlink(o)
roots = [o for o in tree_src if o.parent is None]
for i, (x, z, s, ty) in enumerate(TREES):
    for r in roots:
        for src in [r] + list(r.children_recursive):
            if src.type != "MESH":
                continue
            d = bpy.data.objects.new("SEP_Tree%d_%s" % (i, src.name), src.data)
            d.matrix_world = src.matrix_world.copy()
            d.location = Vector((x, -z, ty)) + d.location * s
            d.scale = d.scale * s
            d.rotation_euler.z += math.radians(90 * (i % 4))
            tcol.objects.link(d)
sun = bpy.data.objects.get("SEP_Sun") or bpy.data.objects.new("SEP_Sun", bpy.data.lights.new("SEP_Sun", "SUN"))
if sun.name not in tcol.objects:
    tcol.objects.link(sun)
sun.data.energy = 3.0
sun.data.color = (1.0, 0.85, 0.66)
sun.rotation_euler = (-Vector((-0.90, -0.40, 0.36)).normalized()).to_track_quat("-Z", "Y").to_euler()

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
    # from the west sidewalk opposite the alley at No. 80 (between Nevius and Odd Fellows), eye 1.75 m
    "from-main-alley80":       dict(eye=S(-8.0, 1.75, -1.0), target=S(100, 3.0, -0.6), lens=28, h=720),
    "from-main-alley80-trees": dict(eye=S(-8.0, 1.75, -1.0), target=S(100, 3.0, -0.6), lens=28, h=720, trees=True),
    "alley80-zoom":            dict(eye=S(-8.0, 1.75, -1.0), target=S(100, 3.0, -0.6), lens=75, h=720, trees=True),
    # from the east sidewalk at the alley mouth (walk limit x 10.2)
    "alley80-from-east-walk":  dict(eye=S(10.0, 1.75, -1.0), target=S(100, 3.0, -0.4), lens=28, h=720, trees=True),
    # alley 86: the two brick houses A14
    "from-main-alley86":       dict(eye=S(-6.0, 1.75, 19.3), target=S(45, 3.5, 21.5), lens=35, h=720, trees=True),
    # Higgins Ave from Main St: the south walk limit is z 60
    "from-main-higgins":       dict(eye=S(-7.8, 1.75, 59.5), target=S(60, 3.0, 68.5), lens=30, h=720),
    "from-main-higgins-trees": dict(eye=S(-7.8, 1.75, 59.5), target=S(60, 3.0, 68.5), lens=30, h=720, trees=True),
    "higgins-from-road":       dict(eye=S(1.0, 1.75, 60.0), target=S(70, 3.0, 66.5), lens=30, h=720, trees=True),
    "overview":                dict(eye=S(15, 70, -45), target=S(72, 0, 28), lens=26, h=800),
    # one from each side of the model
    "alley-north-side":        dict(eye=S(48, 2.2, 0.8), target=S(100, 4.0, -8.5), lens=24, h=760),
    "alley-south-side":        dict(eye=S(48, 2.2, -3.8), target=S(100, 4.0, 6.5), lens=24, h=760),
    "higgins-south-side":      dict(eye=S(30, 3.0, 63.5), target=S(70, 4.0, 78), lens=24, h=760),
    "from-spring-st":          dict(eye=S(116.5, 1.75, 30), target=S(60, 4.0, 20), lens=24, h=760, trees=True),
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS
written = []
try:
    for name, v in VIEWS.items():
        for c in bpy.data.collections:
            c.hide_render = c.name not in ("SidestreetSoutheast", "SE_Preview") + (
                ("SE_PreviewTrees",) if v.get("trees") else ())
        eye, target = Vector(v["eye"]), Vector(v["target"])
        cam.location = eye
        cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = v["lens"]
        scene.render.resolution_x, scene.render.resolution_y = 1280, v.get("h", 960)
        scene.render.filepath = PREV + "sidestreet-southeast-" + name + ".png"
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
    tcol.hide_render = tcol.hide_viewport = True
    bg.inputs[0].default_value, bg.inputs[1].default_value = saved_bg
    scene.camera = saved["camera"] or cam
    scene.render.engine = saved["engine"]
    scene.view_settings.view_transform = saved["vt"]
    scene.view_settings.look = saved["look"]
    scene.render.resolution_x, scene.render.resolution_y = saved["rx"], saved["ry"]
    scene.render.resolution_percentage = saved["pct"]
print("previews written:", *written, sep="\n  ")
