"""
sidestreet_bloomfield_preview.py - review previews of the baked Bloomfield Ave backdrop (run
after sidestreet_bloomfield_bake.py). Same method as sidestreet_court_preview.py.

    exec(open(r"<project>/tools/blender/sidestreet_bloomfield_preview.py").read())

EEVEE, view transform "Standard", every material of the model swapped for an unlit emission of
colour x lightmap x LIGHTMAP_SCALE (the web page's `baked-lighting` maths). Context, drawn the
same way where it is baked: the Rea Building, Bank Building, Lovell's and 40-46 Main GLBs at
their index.html places (own lightmaps and intensities); flat planes for Main St and the
Bloomfield Ave mouth that js/ground.js draws; a plain box for the west side of Main St.
Views ending in "-trees" also show backdrop-tree.glb at the positions proposed for the scene
(lit by a preview sun, as the scene's trees are). Writes
assets/models/previews/sidestreet-bloomfield-*.png (1280 px wide). Camera, engine, view
transform, resolution and the model's materials are restored.

Scene -> Blender: (x, y, z) -> (x, -z, y).
"""

import math
import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\sidestreet-bloomfield-lightmap.jpg"
M = PROJECT + r"\assets\models" + "\\"
T = PROJECT + r"\assets\textures" + "\\"
CONTEXT = [  # glb, lightmap, intensity, scene position (index.html), rotation y
    ("rea-building.glb", "rea-building-lightmap.jpg", 1.1726, (10.85, 0.15, -97.79), -90),
    ("bank-building.glb", "bank-building-lightmap.jpg", 1.1309, (12.24, 0.15, -66.24), -90),
    ("lovells-restaurant.glb", "lovells-restaurant-lightmap.jpg", 1.2468, (12.66, 0.15, -52.13), -90),
    ("block-40-46.glb", "block-40-46-lightmap.jpg", 1.2093, (8.60, 0.15, -116.55), -90),
]
TREE_GLB = M + "backdrop-tree.glb"
TREES = [(71.0, -96.0, 2.0), (78.5, -93.0, 2.2), (93.8, -92.6, 2.1), (104.9, -92.4, 2.0), (114.9, -93.6, 2.15),
         (133.5, -95.0, 2.25), (45.0, -70.0, 2.2), (65.15, -71.0, 1.9), (95.9, -76.0, 2.1), (107.0, -70.0, 2.0)]

scene = bpy.context.scene
r_obj = bpy.data.objects["SidestreetBloomfield"]
mesh = r_obj.data
scale = float(r_obj.get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("SB_Preview")
if not pcol:
    pcol = bpy.data.collections.new("SB_Preview")
    scene.collection.children.link(pcol)
tcol = bpy.data.collections.get("SB_PreviewTrees")
if not tcol:
    tcol = bpy.data.collections.new("SB_PreviewTrees")
    scene.collection.children.link(tcol)
pcol.hide_viewport = pcol.hide_render = False
cam_data = bpy.data.cameras.get("SB_Cam") or bpy.data.cameras.new("SB_Cam")
cam = bpy.data.objects.get("SB_Cam") or bpy.data.objects.new("SB_Cam", cam_data)
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
    mat = bpy.data.materials.new("SBP_" + src.name)
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
sbox("SBP_Disc", -400, 400, -400, 400, -0.05, 0.0, unlit("SBP_DiscMat", (0.15, 0.14, 0.08)))
road = unlit("SBP_RoadMat", (0.20, 0.18, 0.15))
sbox("SBP_MainRoad", -6.4, 6.4, -200, 80, 0.0, 0.01, road)
sbox("SBP_BloomRoad", 6.4, 60, -86.5, -79.9, 0.0, 0.01, road)
walk = unlit("SBP_WalkMat", (0.36, 0.35, 0.32))
sbox("SBP_WalkW", -10.3, -6.4, -200, 80, 0.0, 0.15, walk)
sbox("SBP_WalkEN", 6.4, 10.3, -200, -86.5, 0.0, 0.15, walk)
sbox("SBP_WalkES", 6.4, 10.3, -79.9, 80, 0.0, 0.15, walk)
sbox("SBP_WalkBN", 8.5, 60, -89.9, -86.5, 0.0, 0.15, walk)
sbox("SBP_WalkBS", 10.3, 60, -79.9, -77.3, 0.0, 0.15, walk)
sbox("SBP_West", -30.0, -10.3, -170, -60, 0.0, 10.0, unlit("SBP_WestMat", (0.45, 0.40, 0.33)))

# the built neighbours with their own lightmaps
for o in [o for o in pcol.objects if o.name.startswith("SBP_CTX")]:
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
        o.name = "SBP_CTX_" + glb[:-4]
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
for i, (x, z, s) in enumerate(TREES):
    for r in roots:
        for src in [r] + list(r.children_recursive):
            if src.type != "MESH":
                continue
            d = bpy.data.objects.new("SBP_Tree%d_%s" % (i, src.name), src.data)
            d.matrix_world = src.matrix_world.copy()
            d.location = Vector((x, -z, 0.15)) + d.location * s
            d.scale = d.scale * s
            d.rotation_euler.z += math.radians(90 * (i % 4))
            tcol.objects.link(d)
sun = bpy.data.objects.get("SBP_Sun") or bpy.data.objects.new("SBP_Sun", bpy.data.lights.new("SBP_Sun", "SUN"))
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
    # the orchestrator's check view: Main St centre at Bloomfield Ave, looking east
    "from-main":        dict(eye=S(0, 1.75, -83.6), target=S(100, 2.5, -83.4), lens=24, h=720),
    "from-main-trees":  dict(eye=S(0, 1.75, -83.6), target=S(100, 2.5, -83.4), lens=24, h=720, trees=True),
    # section 5 check 6: from the east sidewalk line
    "from-east-walk":   dict(eye=S(10, 1.75, -84), target=S(100, 2.8, -83.4), lens=30, h=720),
    "overview":         dict(eye=S(35, 62, -18), target=S(92, 0, -84), lens=28, h=760),
    "north-side":       dict(eye=S(72, 2.2, -79.2), target=S(98, 4.5, -101), lens=24, h=760),
    "south-side":       dict(eye=S(66, 3.0, -88.5), target=S(92, 4.0, -64), lens=24, h=760),
    # flmingtngarage09.jpg (1909): from the Bloomfield / Spring crossing, NW of G1, looking SE
    "match-garage09":   dict(eye=S(115.5, 1.7, -86.0), target=S(137.0, 2.4, -63.0), lens=30, h=800),
    # flmngtnparadefloatbldg.jpg (c. 1910): close, face-on to G1's Spring St side
    "match-float":      dict(eye=S(110.0, 1.5, -62.5), target=S(124.2, 3.4, -61.5), lens=28, h=812),
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS
written = []
try:
    for name, v in VIEWS.items():
        for c in bpy.data.collections:
            c.hide_render = c.name not in ("SidestreetBloomfield", "SB_Preview") + (
                ("SB_PreviewTrees",) if v.get("trees") else ())
        eye, target = Vector(v["eye"]), Vector(v["target"])
        cam.location = eye
        cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = v["lens"]
        scene.render.resolution_x, scene.render.resolution_y = 1280, v.get("h", 960)
        scene.render.filepath = PREV + "sidestreet-bloomfield-" + name + ".png"
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
