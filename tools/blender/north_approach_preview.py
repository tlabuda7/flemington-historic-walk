"""
north_approach_preview.py - review previews of the baked north approach (run after
north_approach_bake.py, in assets/models/source/north_approach.blend). Same method as
street_ends_preview.py.

    exec(open(r"<project>/tools/blender/north_approach_preview.py", encoding="utf8").read())

EEVEE, view transform "Standard", the model's materials swapped for an unlit emission of
colour x lightmap x LIGHTMAP_SCALE (the web page's `baked-lighting` maths). Context drawn the same
way: street-ends.glb (road, east walk, monument, church, E1-E4), 27 Main, 24-30 Main, the Palace,
32-38 Main at their index.html places with their own lightmaps; the landscape's Town silhouettes
(unlit vertex colours); flat planes for the Main St road and walks js/ground.js draws (z > -180).
Trees: old-maple.glb / backdrop-tree.glb at the positions in north_approach_bake.py TREES and the
scene's north-end backdrop trees, lit by a preview sun as in the scene.
Writes assets/models/previews/north-approach-*.png (1280 px wide). Camera, engine, view transform,
resolution and the model's materials are restored.

Scene -> Blender: (x, y, z) -> (x, -z, y).
"""

import math
import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\north-approach-lightmap.jpg"
M = PROJECT + r"\assets\models" + "\\"
T = PROJECT + r"\assets\textures" + "\\"
EN_SCALE = globals().get("EN_SCALE", 1.0491)       # street-ends LIGHTMAP_SCALE
CONTEXT = [  # glb, lightmap, intensity, scene position (index.html), rotation y
    ("street-ends.glb", "street-ends-lightmap.jpg", EN_SCALE, (0.0, 0.0, 0.0), 0),
    ("store-27.glb", "store-27-lightmap.jpg", 0.8992, (-10.30, 0.15, -158.49), 90),
    ("block-24-30.glb", "block-24-30-lightmap.jpg", 1.1509, (7.29, 0.15, -152.365), -90),
    ("palace-theatre.glb", "palace-theatre-lightmap.jpg", 0.9901, (-10.3, 0.15, -145.52), 90),
    ("block-32-38.glb", "block-32-38-lightmap.jpg", 1.1463, (8.54, 0.15, -130.755), -90),
]
# (x, z, scale, y, kind) = north_approach_bake.py TREES + the scene's btree-end-1
TREES = [(-11.3, -206.0, 0.95, 0.15, "maple"), (-11.3, -224.0, 1.0, 0.15, "maple"),
         (-11.3, -241.0, 0.9, 0.15, "maple"), (-11.3, -258.0, 1.0, 0.15, "maple"),
         (-11.3, -276.0, 0.95, 0.15, "maple"), (-11.3, -291.0, 1.0, 0.15, "maple"),
         (7.0, -198.0, 1.0, 0.15, "maple"), (7.0, -214.0, 0.95, 0.15, "maple"),
         (7.0, -230.0, 1.0, 0.15, "maple"), (7.0, -246.0, 0.9, 0.15, "maple"),
         (12.4, -275.0, 1.0, 0.15, "maple"), (20.0, -291.5, 0.95, 0.15, "maple"),
         (-20.0, -300.0, 1.05, 0.15, "maple"), (-22.0, -286.0, 1.05, 0.15, "maple"),
         (9.6, -261.0, 0.95, 0.15, "maple"),                                      # R-a 2026-11-12
         (40.0, -236.0, 1.0, 0.15, "maple"), (36.0, -259.0, 0.9, 0.15, "maple"),
         (55.0, -283.0, 1.05, 0.15, "maple"), (66.0, -205.0, 0.95, 0.15, "maple"),
         (-45.0, -218.0, 1.0, 0.15, "maple"), (-48.0, -246.0, 0.9, 0.15, "maple"),
         (-52.0, -277.0, 1.05, 0.15, "maple"), (-82.0, -240.0, 0.85, 0.15, "maple"),
         (-14.0, -322.0, 2.2, 0.15, "young"),
         (-7.6, -187.0, 2.1, 0.15, "young"), (-7.6, -173.5, 2.0, 0.15, "young"), (40.0, -326.0, 2.2, 0.15, "young"),
         (14.0, -337.5, 2.3, 0.15, "young")]

TREES = globals().get("PREVIEW_TREES") or TREES

scene = bpy.context.scene
r_obj = bpy.data.objects["NorthApproach"]
mesh = r_obj.data
scale = float(r_obj.get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("NA_Preview")
if not pcol:
    pcol = bpy.data.collections.new("NA_Preview")
    scene.collection.children.link(pcol)
tcol = bpy.data.collections.get("NA_PreviewTrees")
if not tcol:
    tcol = bpy.data.collections.new("NA_PreviewTrees")
    scene.collection.children.link(tcol)
pcol.hide_viewport = pcol.hide_render = False
tcol.hide_viewport = tcol.hide_render = False
cam_data = bpy.data.cameras.get("NA_Cam") or bpy.data.cameras.new("NA_Cam")
cam = bpy.data.objects.get("NA_Cam") or bpy.data.objects.new("NA_Cam", cam_data)
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
    mat = bpy.data.materials.new("NAP_" + src.name)
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
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
    me = bpy.data.meshes.new(name)
    v = [(x, -z, y) for y in (y0, y1) for z in (z0, z1) for x in (x0, x1)]
    me.from_pydata(v, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    pcol.objects.link(o)


sbox("NAP_Disc", -600, 600, -600, 600, -0.05, 0.0, unlit("NAP_DiscMat", (0.15, 0.14, 0.08)))
sbox("NAP_MainRoad", -6.4, 6.4, -180, 80, 0.0, 0.01, unlit("NAP_RoadMat", (0.20, 0.18, 0.15)))
walk = unlit("NAP_WalkMat", (0.36, 0.35, 0.32))
sbox("NAP_WalkW", -10.3, -6.4, -180, 10.4, 0.0, 0.15, walk)
sbox("NAP_WalkE", 6.4, 10.3, -164, 62.1, 0.0, 0.15, walk)
sbox("NAP_WalkEN", 3.5, 6.36, -180, -164, 0.0, 0.15, walk)
sbox("NAP_LaneN", 6.3, 10.35, -180, -140.9, 0.0, 0.012, unlit("NAP_EarthMat", (0.23, 0.19, 0.13)))

for o in [o for o in pcol.objects if o.name.startswith("NAP_Town")]:
    bpy.data.objects.remove(o, do_unlink=True)
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=M + "landscape.glb")
for o in [o for o in bpy.data.objects if o not in _before]:
    if o.name.startswith("landscape_town"):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        pcol.objects.link(o)
        o.name = "NAP_Town"
        tm = bpy.data.materials.new("NAP_TownMat")
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

for o in [o for o in pcol.objects if o.name.startswith("NAP_CTX")]:
    bpy.data.objects.remove(o, do_unlink=True)
for glb, lmf, inten, (px, py, pz), rot in CONTEXT:
    _before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=M + glb)
    img = bpy.data.images.load(T + lmf, check_existing=True)
    img.reload()
    img.colorspace_settings.name = "sRGB"
    for o in [o for o in bpy.data.objects if o not in _before]:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        pcol.objects.link(o)
        o.name = "NAP_CTX_" + glb[:-4]
        if o.parent is None:
            o.rotation_mode = "XYZ"
            o.location = (px, -pz, py)
            o.rotation_euler = (0, 0, math.radians(rot))
        if o.type == "MESH":
            uvs = [u.name for u in o.data.uv_layers]
            for i, m in enumerate(list(o.data.materials)):
                if len(uvs) > 1:
                    o.data.materials[i] = preview_material(m, img, inten, uvs[1], uvs[0])

for o in list(tcol.objects):
    bpy.data.objects.remove(o, do_unlink=True)
srcs = {}
for kind, glb in (("maple", "old-maple.glb"), ("young", "backdrop-tree.glb")):
    _before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=M + glb)
    new = [o for o in bpy.data.objects if o not in _before]
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
    srcs[kind] = [o for o in new if o.parent is None]
for i, (x, z, s, ty, kind) in enumerate(TREES):
    for r in srcs[kind]:
        for src in [r] + list(r.children_recursive):
            if src.type != "MESH":
                continue
            d = bpy.data.objects.new("NAP_Tree%d_%s" % (i, src.name), src.data)
            d.matrix_world = src.matrix_world.copy()
            d.location = Vector((x, -z, ty)) + d.location * s
            d.scale = d.scale * s
            d.rotation_euler.z += math.radians(61 * i)
            tcol.objects.link(d)
sun = bpy.data.objects.get("NAP_Sun") or bpy.data.objects.new("NAP_Sun", bpy.data.lights.new("NAP_Sun", "SUN"))
if sun.name not in tcol.objects:
    tcol.objects.link(sun)
sun.data.energy = 3.0
sun.data.color = (1.0, 0.85, 0.66)
sun.rotation_euler = (-Vector((-0.90, -0.40, 0.36)).normalized()).to_track_quat("-Z", "Y").to_euler()

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
if scene.world is None:
    scene.world = bpy.data.worlds.new("NA_Sky")
world = scene.world
world.use_nodes = True
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
    # the view north from the walk limit (orchestrator: scene (0, 1.75, -150))
    "view-north":       dict(eye=S(0.0, 1.75, -150), target=S(0.0, 4.0, -260), lens=26, h=720, trees=True),
    "view-north-zoom":  dict(eye=S(0.0, 1.75, -150), target=S(0.0, 6.0, -260), lens=60, h=720, trees=True),
    # acceptance checks 2 and 3 (west and east walks at z -160; the spec's (-9 / 8, -160) stand
    # under 27 Main's awning / inside 24-30 Main, so the eyes are at the walks' outer edges)
    "west-walk":        dict(eye=S(-7.0, 1.75, -160), target=S(-13.0, 4.0, -260), lens=35, h=720, trees=True),
    "east-walk":        dict(eye=S(5.0, 1.75, -160), target=S(13.0, 4.0, -260), lens=35, h=720, trees=True),
    "overview":         dict(eye=S(60, 70, -170), target=S(-5, 0, -262), lens=24, h=800),
    "west-side":        dict(eye=S(4.0, 6.0, -200), target=S(-22.0, 4.0, -262), lens=28, h=800),
    "east-side":        dict(eye=S(-5.0, 6.0, -195), target=S(22.0, 4.0, -262), lens=28, h=800),
    "detail":           dict(eye=S(-4.0, 2.2, -222), target=S(-19.0, 3.5, -246), lens=35, h=840, trees=True),
    # match views of the reference cards
    "match-1913":       dict(eye=S(-9.0, 1.6, -215), target=S(-9.0, 1.6 + 13.2, -315), lens=40, h=792, trees=True),
    "match-brodhead":   dict(eye=S(6.0, 1.7, -296), target=S(-33.0, 6.0, -300), lens=36, h=810, trees=True),
    "match-bloom":      dict(eye=S(-3.0, 1.7, -345), target=S(15.0, 5.0, -300), lens=40, h=830, trees=True),
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS
PREFIX = globals().get("PREVIEW_PREFIX") or "north-approach-"
written = []
try:
    for name, v in VIEWS.items():
        for c in bpy.data.collections:
            c.hide_render = c.name not in ("NorthApproach", "NA_Preview") + (
                ("NA_PreviewTrees",) if v.get("trees") else ())
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
