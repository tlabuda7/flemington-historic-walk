"""
house_65_main_preview.py - review previews of the baked house at 65 Main St (run after
house_65_main_bake.py).

    exec(open(r"<project>/tools/blender/house_65_main_preview.py").read())

Renders with EEVEE, view transform "Standard", and every material swapped for an unlit
emission of colour x lightmap x LIGHTMAP_SCALE - the same maths as the web page's
`baked-lighting` component (MeshBasicMaterial: map x color x lightMap x intensity), so
the pictures match what the headset shows. Colour factors (glTF baseColorFactor) are
included. Writes assets/models/previews/house-65-main-*.png (1280 px wide). The camera,
engine, view transform, resolution and the building's own materials are restored.
"""

import math
import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\house-65-main-lightmap.jpg"

scene = bpy.context.scene
h_obj = bpy.data.objects["House65Main"]
mesh = h_obj.data
scale = float(h_obj.get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("H65_Preview")
if not pcol:
    pcol = bpy.data.collections.new("H65_Preview")
    scene.collection.children.link(pcol)
cam_data = bpy.data.cameras.get("H65_Cam") or bpy.data.cameras.new("H65_Cam")
cam = bpy.data.objects.get("H65_Cam") or bpy.data.objects.new("H65_Cam", cam_data)
if cam.name not in pcol.objects:
    pcol.objects.link(cam)
cam_data.clip_end = 600
cam_data.sensor_fit = "HORIZONTAL"
cam_data.sensor_width = 36

lm_img = bpy.data.images.load(LIGHTMAP, check_existing=True)
lm_img.reload()
lm_img.colorspace_settings.name = "sRGB"          # three.js decodes it as sRGB too


def sock(socks, name):
    return next(x for x in socks if x.name == name and x.type == "RGBA")


def preview_material(src):
    """Unlit copy: emission = base colour (texture x factor, or plain) x lightmap x scale."""
    mat = bpy.data.materials.new("H65P_" + src.name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    emit = N("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = scale
    uv1 = N("ShaderNodeUVMap")
    uv1.uv_map = "Lightmap"
    lm = N("ShaderNodeTexImage")
    lm.image = lm_img
    L(uv1.outputs["UV"], lm.inputs["Vector"])
    mix = N("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    src_tex = next((n for n in src.node_tree.nodes if n.type == "TEX_IMAGE"), None)
    src_tint = next((n for n in src.node_tree.nodes if n.type == "MIX" and n.blend_type == "MULTIPLY"), None)
    if src_tex:
        uv0 = N("ShaderNodeUVMap")
        uv0.uv_map = "UVMap"
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
    else:
        bsdf = next(n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
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


def flat(name, x0, x1, y0, y1, z, mat):
    obj = bpy.data.objects.get(name)
    if not obj:
        gm = bpy.data.meshes.new(name)
        gm.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
        gm.materials.append(mat)
        obj = bpy.data.objects.new(name, gm)
        pcol.objects.link(obj)
    return obj


# context (unlit, flat colours), local frame: lawn behind the property line (y > -3.77),
# west sidewalk y -3.77 ... -7.67 (0.13 above the lawn), road, east sidewalk y -20.47 ... -24.37
flat("H65P_Under", -150, 150, -150, 150, -0.05, unlit("H65P_WalkMat", (0.42, 0.41, 0.38)))   # curb faces
flat("H65P_Lawn", -150, 150, -3.77, 150, -0.005, unlit("H65P_LawnMat", (0.13, 0.17, 0.07)))
flat("H65P_Walk", -150, 150, -7.67, -3.77, 0.13, unlit("H65P_WalkMat", (0.42, 0.41, 0.38)))
flat("H65P_Road", -150, 150, -20.47, -7.67, -0.03, unlit("H65P_RoadMat", (0.30, 0.28, 0.25)))
flat("H65P_WalkE", -150, 150, -60, -20.47, 0.13, unlit("H65P_WalkMat", (0.42, 0.41, 0.38)))

# --- remember and change settings ----------------------------------------------------
originals = list(mesh.materials)
previews = [preview_material(m) for m in originals]
saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
render_state = {c.name: c.hide_render for c in bpy.data.collections}
for c in bpy.data.collections:
    c.hide_render = c.name not in ("House65Main", "H65_Preview")
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

# name -> dict(eye, target, lens, [h = image height for 1280 wide], [shift = (x, y)], [level]).
# Local frame: -Y = Main St (east), +X = north, -X = south. The east sidewalk is ~22 m in
# front of the porch and ~0.13 m above the lawn: eye 1.7 m above it.
# 1909 card: from the east sidewalk opposite the Hall of Records (scene ~(10, -26)) =
# local (-25.2, -24.1); the card looks ~7 deg north of west, with the house at its right
# edge; this view turns 19 deg further right so the whole south side is in frame.
yaw = math.radians(26.0)
EYE09 = Vector((-25.19, -24.07, 1.73))
VIEWS = {
    "front":              dict(eye=(0.0, -22.4, 1.83), target=(0.0, 0.0, 1.83), lens=44, shift=(0, 0.22), level=True),
    "three-quarter-ne":   dict(eye=(17.0, -15.0, 1.83), target=(0.0, 6.0, 4.0), lens=30),
    "three-quarter-se":   dict(eye=(-17.0, -15.0, 1.83), target=(-1.0, 6.0, 4.0), lens=30),
    "detail":             dict(eye=(1.6, -6.2, 1.7), target=(0.0, 1.6, 2.1), lens=30),      # entrance
    "match-1909":         dict(eye=tuple(EYE09), target=tuple(EYE09 + Vector((math.sin(yaw), math.cos(yaw), 0)) * 30),
                               lens=37.7, h=858, shift=(0, 0.12), level=True),
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS     # set PREVIEW_VIEWS before exec() for other views
written = []
try:
    for name, v in VIEWS.items():
        eye, target = Vector(v["eye"]), Vector(v["target"])
        if v.get("level"):
            target.z = eye.z
        cam.location = eye
        cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = v["lens"]
        cam_data.shift_x, cam_data.shift_y = v.get("shift", (0, 0))
        scene.render.resolution_x, scene.render.resolution_y = 1280, v.get("h", 960)
        scene.render.filepath = PREV + "house-65-main-" + name + ".png"
        bpy.ops.render.render(write_still=True)
        written.append(scene.render.filepath)
finally:
    cam_data.shift_x = cam_data.shift_y = 0
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
    pcol.hide_render = True
    bg.inputs[0].default_value, bg.inputs[1].default_value = saved_bg
    scene.camera = saved["camera"] or cam
    scene.render.engine = saved["engine"]
    scene.view_settings.view_transform = saved["vt"]
    scene.view_settings.look = saved["look"]
    scene.render.resolution_x, scene.render.resolution_y = saved["rx"], saved["ry"]
    scene.render.resolution_percentage = saved["pct"]
print("previews written:", *written, sep="\n  ")
