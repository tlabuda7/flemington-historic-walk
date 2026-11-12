"""
sidestreet_court_preview.py - review previews of the baked Court St backdrop (run after
sidestreet_court_bake.py).

    exec(open(r"<project>/tools/blender/sidestreet_court_preview.py").read())

EEVEE, view transform "Standard", every material of the model swapped for an unlit emission of
colour x lightmap x LIGHTMAP_SCALE (the web page's `baked-lighting` maths). Context, drawn the
same way where it is baked: the courthouse GLB at its index.html place (its own lightmap and
intensity); flat unlit boxes for the 79 and 83-87 Main placeholders; flat planes for Main St
and the Court St mouth that js/ground.js draws. Views ending in "-trees" also show
street-tree.glb at the positions proposed for the scene (lit by a preview sun; the scene's
trees are lit the same way). Writes assets/models/previews/sidestreet-court-*.png (1280 px
wide). Camera, engine, view transform, resolution and the model's materials are restored.

Scene -> Blender: (x, y, z) -> (x, -z, y).
"""

import math
import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\sidestreet-court-lightmap.jpg"
CH_GLB = PROJECT + r"\assets\models\courthouse.glb"
CH_LM = PROJECT + r"\assets\textures\courthouse-lightmap.jpg"
CH_SCALE = 1.1979
TREE_GLB = PROJECT + r"\assets\models\street-tree.glb"
TREES = [(x, -1.3, s) for x, s in ((-90, 2.1), (-101, 2.3), (-112, 2.2), (-123, 2.35), (-134, 2.15),
                                   (-145, 2.3), (-156, 2.2), (-167, 2.25))] + \
        [(x, 11.2, s) for x, s in ((-94.4, 2.2), (-111.5, 2.3), (-123.5, 2.15), (-140.0, 2.3),
                                   (-155.0, 2.2), (-168.5, 2.25))]

scene = bpy.context.scene
r_obj = bpy.data.objects["SidestreetCourt"]
mesh = r_obj.data
scale = float(r_obj.get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("SC_Preview")
if not pcol:
    pcol = bpy.data.collections.new("SC_Preview")
    scene.collection.children.link(pcol)
tcol = bpy.data.collections.get("SC_PreviewTrees")
if not tcol:
    tcol = bpy.data.collections.new("SC_PreviewTrees")
    scene.collection.children.link(tcol)
pcol.hide_viewport = pcol.hide_render = False
cam_data = bpy.data.cameras.get("SC_Cam") or bpy.data.cameras.new("SC_Cam")
cam = bpy.data.objects.get("SC_Cam") or bpy.data.objects.new("SC_Cam", cam_data)
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
    mat = bpy.data.materials.new("SCP_" + src.name)
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
    src_tex = next((n for n in src.node_tree.nodes if n.type == "TEX_IMAGE"), None)
    src_tint = next((n for n in src.node_tree.nodes if n.type == "MIX" and n.blend_type == "MULTIPLY"), None)
    bsdf = next((n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
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


# context ground (js/ground.js area), placeholders
sbox("SCP_Disc", -400, 400, -400, 400, -0.05, 0.0, unlit("SCP_DiscMat", (0.15, 0.14, 0.08)))
sbox("SCP_MainRoad", -6.4, 6.4, -200, 80, 0.0, 0.01, unlit("SCP_RoadMat", (0.20, 0.18, 0.15)))
sbox("SCP_CourtRoad", -60, -6.4, 2.0, 8.4, 0.0, 0.01, bpy.data.materials["SCP_RoadMat"])
walk = unlit("SCP_WalkMat", (0.36, 0.35, 0.32))
sbox("SCP_WalkWN", -10.3, -6.4, -200, 0.0, 0.0, 0.15, walk)
sbox("SCP_WalkCN", -60, -6.4, 0.0, 2.0, 0.0, 0.15, walk)
sbox("SCP_WalkCS", -60, -4.55, 8.4, 10.4, 0.0, 0.15, walk)
sbox("SCP_WalkWS", -8.15, -4.4, 10.4, 80, 0.0, 0.15, walk)
sbox("SCP_WalkE", 6.4, 10.3, -200, 80, 0.0, 0.15, walk)
sbox("SCP_LawnW", -45, -10.3, -77.4, 0.0, 0.0, 0.015, unlit("SCP_LawnMat", (0.12, 0.15, 0.07)))
sbox("SCP_79", -33.13, -8.13, 10.4, 18.0, 0.0, 9.75, unlit("SCP_79Mat", (0.62, 0.59, 0.52)))
sbox("SCP_8387", -25.67, -8.67, 19.8, 26.4, 0.0, 9.75, unlit("SCP_8387Mat", (0.33, 0.17, 0.12)))
sbox("SCP_East", 10.3, 30.0, -60, 40, 0.0, 10.0, unlit("SCP_EastMat", (0.45, 0.40, 0.33)))

# the courthouse GLB with its own lightmap
for o in [o for o in pcol.objects if o.name.startswith("SCP_CH")]:
    bpy.data.objects.remove(o, do_unlink=True)
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=CH_GLB)
ch_lm = bpy.data.images.load(CH_LM, check_existing=True)
ch_lm.colorspace_settings.name = "sRGB"
for o in [o for o in bpy.data.objects if o not in _before]:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    pcol.objects.link(o)
    o.name = "SCP_CH"
    if o.parent is None:
        o.location = (-18.34, 6.85, 0.15)
        o.rotation_euler = (0, 0, math.radians(90))
    if o.type == "MESH":
        uvs = [u.name for u in o.data.uv_layers]
        for i, m in enumerate(list(o.data.materials)):
            o.data.materials[i] = preview_material(m, ch_lm, CH_SCALE, uvs[1], uvs[0])

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
            d = bpy.data.objects.new("SCP_Tree%d_%s" % (i, src.name), src.data)
            d.matrix_world = src.matrix_world.copy()
            base = 0.575 if z < 0 else 0.175
            d.location = Vector((x, -z, base)) + d.location * s
            d.scale = d.scale * s
            d.rotation_euler.z += math.radians(90 * (i % 4))
            tcol.objects.link(d)
sun = bpy.data.objects.get("SCP_Sun") or bpy.data.objects.new("SCP_Sun", bpy.data.lights.new("SCP_Sun", "SUN"))
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
    # the visitor's start view: Main St centre, looking west down Court St
    "from-main":        dict(eye=S(0, 1.75, 5), target=S(-100, 1.75, 5.2), lens=24, h=720),
    "from-main-trees":  dict(eye=S(0, 1.75, 5), target=S(-100, 1.75, 5.2), lens=24, h=720, trees=True),
    # section 5 check 5: from the west sidewalk line
    "from-west-walk":   dict(eye=S(-10, 1.75, 5), target=S(-100, 2.5, 5.2), lens=30, h=720),
    "overview":         dict(eye=S(-20, 70, 75), target=S(-105, 0, 5), lens=28, h=760),
    "north-side":       dict(eye=S(-48, 2.2, 9.6), target=S(-72, 3.5, -6), lens=24, h=760),
    "south-side":       dict(eye=S(-85, 3.0, -14), target=S(-110, 4.0, 18), lens=24, h=760),
    # parade card (c. 1910): from the road near Park Ave looking east towards Main St
    "match-parade":     dict(eye=S(-165, 1.6, 4.0), target=S(-60, 2.6, 5.5), lens=26, h=808, trees=True),
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS
written = []
try:
    for name, v in VIEWS.items():
        for c in bpy.data.collections:
            c.hide_render = c.name not in ("SidestreetCourt", "SC_Preview") + (("SC_PreviewTrees",) if v.get("trees") else ())
        eye, target = Vector(v["eye"]), Vector(v["target"])
        cam.location = eye
        cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = v["lens"]
        scene.render.resolution_x, scene.render.resolution_y = 1280, v.get("h", 960)
        scene.render.filepath = PREV + "sidestreet-court-" + name + ".png"
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
