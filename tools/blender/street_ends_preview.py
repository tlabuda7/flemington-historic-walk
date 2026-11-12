"""
street_ends_preview.py - review previews of the baked street ends (run after street_ends_bake.py).
Same method as sidestreet_southeast_preview.py.

    exec(open(r"<project>/tools/blender/street_ends_preview.py", encoding="utf8").read())

EEVEE, view transform "Standard", every material of the model swapped for an unlit emission of
colour x lightmap x LIGHTMAP_SCALE (the web page's `baked-lighting` maths). Context, drawn the
same way where it is baked: the built neighbours at both ends (27 Main, 24-30 Main, Palace,
100-102, 106, Democrat, the Court St and south-east backdrops) at their index.html places with
their own lightmaps; the landscape's `Town` silhouettes (landscape.glb, unlit vertex colours, as
in the scene); flat planes for the Main St road and walks that js/ground.js draws (z -180 .. 80);
plain boxes for the placeholders 91-93 and 95-97 Main. Views ending in "-trees" (and the match
views) also show backdrop-tree.glb at the positions proposed in street_ends_bake.py (lit by a
preview sun, as the scene's trees are). Writes assets/models/previews/street-ends-*.png (1280 px
wide). Camera, engine, view transform, resolution and the model's materials are restored.

Scene -> Blender: (x, y, z) -> (x, -z, y).
"""

import math
import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\street-ends-lightmap.jpg"
M = PROJECT + r"\assets\models" + "\\"
T = PROJECT + r"\assets\textures" + "\\"
CONTEXT = [  # glb, lightmap, intensity, scene position (index.html), rotation y
    ("store-27.glb", "store-27-lightmap.jpg", 0.8992, (-10.30, 0.15, -158.49), 90),
    ("block-24-30.glb", "block-24-30-lightmap.jpg", 1.1509, (7.29, 0.15, -152.365), -90),
    ("palace-theatre.glb", "palace-theatre-lightmap.jpg", 0.9901, (-10.3, 0.15, -145.52), 90),
    ("block-32-38.glb", "block-32-38-lightmap.jpg", 1.1463, (8.54, 0.15, -130.755), -90),
    ("democrat-building.glb", "democrat-building-lightmap.jpg", 1.1571, (10.08, 0.15, 43.85), -90),
    ("store-100-102.glb", "store-100-102-lightmap.jpg", 1.1366, (10.30, 0.15, 52.01), -90),
    ("store-106.glb", "store-106-lightmap.jpg", 1.1209, (8.06, 0.15, 58.80), -90),
    ("sidestreet-southeast.glb", "sidestreet-southeast-lightmap.jpg", 1.0015, (0.0, 0.0, 0.0), 0),
    ("sidestreet-court.glb", "sidestreet-court-lightmap.jpg", 1.0366, (0.0, 0.0, 0.0), 0),
]
TREE_GLB = M + "backdrop-tree.glb"
# (x, z, scale, y) as street_ends_bake.py
# (R-a 2026-11-12: (10, -262) and (-14, -300) removed; omaple-n-15 at (9.6, -261) is an old maple)
TREES = [(-7.6, -173.5, 2.0, 0.15), (-7.6, -187.0, 2.1, 0.15),
         (-14.0, -322.0, 2.2, 0.15), (40.0, -326.0, 2.2, 0.15), (14.0, -337.5, 2.3, 0.15), (0.0, -378.0, 2.2, 0.15),
         (-10.8, 70.0, 2.2, 0.15), (-10.8, 89.0, 2.3, 0.15), (-10.8, 108.0, 2.2, 0.15), (-10.8, 127.0, 2.3, 0.15),
         (-10.8, 146.0, 2.2, 0.15), (12.6, 112.0, 1.4, 0.15), (40.0, 98.0, 2.2, 0.15), (40.0, 145.0, 2.1, 0.15),
         (16.0, 182.0, 2.3, 0.15), (24.0, 196.0, 2.2, 0.15)]

scene = bpy.context.scene
r_obj = bpy.data.objects["StreetEnds"]
mesh = r_obj.data
scale = float(r_obj.get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("EN_Preview")
if not pcol:
    pcol = bpy.data.collections.new("EN_Preview")
    scene.collection.children.link(pcol)
tcol = bpy.data.collections.get("EN_PreviewTrees")
if not tcol:
    tcol = bpy.data.collections.new("EN_PreviewTrees")
    scene.collection.children.link(tcol)
pcol.hide_viewport = pcol.hide_render = False
cam_data = bpy.data.cameras.get("EN_Cam") or bpy.data.cameras.new("EN_Cam")
cam = bpy.data.objects.get("EN_Cam") or bpy.data.objects.new("EN_Cam", cam_data)
if cam.name not in pcol.objects:
    pcol.objects.link(cam)
cam_data.clip_end = 1500
cam_data.sensor_fit = "HORIZONTAL"
cam_data.sensor_width = 36

lm_img = bpy.data.images.load(LIGHTMAP, check_existing=True)
lm_img.reload()
lm_img.colorspace_settings.name = "sRGB"


def sock(socks, name):
    return next(x for x in socks if x.name == name and x.type == "RGBA")


def preview_material(src, lm_image, lm_scale, lm_uv, uv0_name):
    mat = bpy.data.materials.new("ENP_" + src.name)
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


# context ground (js/ground.js area: Main St z -180 .. 80) and the two placeholders south of Court St
sbox("ENP_Disc", -600, 600, -600, 600, -0.05, 0.0, unlit("ENP_DiscMat", (0.15, 0.14, 0.08)))
road = unlit("ENP_RoadMat", (0.20, 0.18, 0.15))
sbox("ENP_MainRoad", -6.4, 6.4, -180, 80, 0.0, 0.01, road)
walk = unlit("ENP_WalkMat", (0.36, 0.35, 0.32))
sbox("ENP_WalkW", -10.3, -6.4, -180, 10.4, 0.0, 0.15, walk)
sbox("ENP_WalkWS", -7.76, -4.4, 10.4, 80, 0.0, 0.15, walk)
sbox("ENP_WalkE", 6.4, 10.3, -164, 62.1, 0.0, 0.15, walk)
sbox("ENP_WalkEN", 3.5, 6.36, -180, -164, 0.0, 0.15, walk)
sbox("ENP_WalkES", 6.4, 9.3, 68.7, 80, 0.0, 0.15, walk)
earth = unlit("ENP_EarthMat", (0.23, 0.19, 0.13))
sbox("ENP_LaneN", 6.3, 10.35, -180, -140.9, 0.0, 0.012, earth)
sbox("ENP_HigginsRoad", 6.4, 40.0, 62.9, 67.9, 0.0, 0.01, road)
sbox("ENP_HigginsN", 6.9, 40.0, 62.1, 62.9, 0.0, 0.15, earth)
sbox("ENP_HigginsS", 6.9, 40.0, 67.9, 68.7, 0.0, 0.15, earth)
sbox("ENP_Yards9197", -13.0, -7.9, 26.4, 58.4, 0.0, 0.015, unlit("ENP_LawnMat", (0.20, 0.25, 0.10)))
sbox("ENP_P9193", -21.4, -13.2, 34.3, 42.5, 0.0, 6.5, unlit("ENP_P1Mat", (0.62, 0.58, 0.48)))
sbox("ENP_P9597", -23.0, -13.0, 48.9, 56.7, 0.0, 6.5, unlit("ENP_P2Mat", (0.45, 0.28, 0.22)))
sbox("ENP_P8387", -25.67, -8.67, 19.8, 26.4, 0.0, 9.75, unlit("ENP_P3Mat", (0.40, 0.22, 0.17)))

# the landscape's Town silhouettes (unlit vertex colours), as in the scene
for o in [o for o in pcol.objects if o.name.startswith("ENP_Town")]:
    bpy.data.objects.remove(o, do_unlink=True)
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=M + "landscape.glb")
for o in [o for o in bpy.data.objects if o not in _before]:
    if o.name.startswith("landscape_town"):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        pcol.objects.link(o)
        o.name = "ENP_Town"
        tm = bpy.data.materials.new("ENP_TownMat")
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
for o in [o for o in pcol.objects if o.name.startswith("ENP_CTX")]:
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
        o.name = "ENP_CTX_" + glb[:-4]
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
            d = bpy.data.objects.new("ENP_Tree%d_%s" % (i, src.name), src.data)
            d.matrix_world = src.matrix_world.copy()
            d.location = Vector((x, -z, ty)) + d.location * s
            d.scale = d.scale * s
            d.rotation_euler.z += math.radians(90 * (i % 4))
            tcol.objects.link(d)
sun = bpy.data.objects.get("ENP_Sun") or bpy.data.objects.new("ENP_Sun", bpy.data.lights.new("ENP_Sun", "SUN"))
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
    # the two required street views, eye 1.75 m on the crown line, from the walk limits
    "view-north":          dict(eye=S(0.0, 1.75, -150), target=S(0.0, 4.0, -260), lens=26, h=720, trees=True),
    "view-north-zoom":     dict(eye=S(0.0, 1.75, -150), target=S(4.0, 9.0, -330), lens=70, h=720, trees=True),
    "view-south":          dict(eye=S(0.0, 1.75, 50), target=S(0.0, 4.0, 160), lens=26, h=720, trees=True),
    "view-south-zoom":     dict(eye=S(0.0, 1.75, 50), target=S(10.0, 6.0, 130), lens=60, h=720, trees=True),
    # overviews of each end
    "overview-north":      dict(eye=S(-62, 80, -128), target=S(6, 0, -262), lens=22, h=800),
    "overview-south":      dict(eye=S(-50, 55, 50), target=S(18, 0, 130), lens=26, h=800),
    # match views of the primary reference photos
    "match-methodist":     dict(eye=S(-5.0, 1.75, 136.0), target=S(25.0, 8.5, 113.0), lens=30, h=840, trees=True),
    "match-presbyterian":  dict(eye=S(2.0, 1.75, -322.0), target=S(19.0, 11.0, -362.0), lens=26, h=840, trees=True),
    "match-monument":      dict(eye=S(1.0, 1.75, -282.0), target=S(7.0, 5.5, -322.0), lens=30, h=840, trees=True),
    "match-deats":         dict(eye=S(-6.0, 1.75, 180.0), target=S(21.0, 7.0, 158.0), lens=30, h=840, trees=True),
    "match-hotel":         dict(eye=S(1.0, 1.75, -180.0), target=S(-14.0, 6.0, -180.0), lens=24, h=840, trees=True),
    "match-doric":         dict(eye=S(3.0, 1.6, 96.4), target=S(15.0, 4.6, 96.4), lens=26, h=840),
    "match-vosseller":     dict(eye=S(-1.5, 1.75, 108.0), target=S(5.0, 4.0, 60.0), lens=32, h=720, trees=True),
    "match-library":       dict(eye=S(1.5, 1.75, 126.0), target=S(22.0, 4.5, 142.0), lens=30, h=840, trees=True),
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS
PREFIX = globals().get("PREVIEW_PREFIX") or "street-ends-"
written = []
try:
    for name, v in VIEWS.items():
        for c in bpy.data.collections:
            c.hide_render = c.name not in ("StreetEnds", "EN_Preview") + (
                ("EN_PreviewTrees",) if v.get("trees") else ())
        eye, target = Vector(v["eye"]), Vector(v["target"])
        cam.location = eye
        cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = v["lens"]
        scene.render.resolution_x, scene.render.resolution_y = 1280, v.get("h", 960)
        scene.render.filepath = PREV + PREFIX + name + ".png"
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
