"""
block_32_38_preview.py - review previews of the baked frame row at 32-38 Main St (Mill'y,
Bakery, Meats) (run after block_32_38_bake.py). The built block-40-46.glb is shown beside it
(its own lightmap and intensity), so the step down to 40-42 and the patch read in context.

    exec(open(r"<project>/tools/blender/block_32_38_preview.py").read())

Renders with EEVEE, view transform "Standard", and every material swapped for an unlit
emission of colour x lightmap x LIGHTMAP_SCALE - the same maths as the web page's
`baked-lighting` component (MeshBasicMaterial: map x color x lightMap x intensity), so
the pictures match what the headset shows. Colour factors (glTF baseColorFactor) are
included. Writes assets/models/previews/block-32-38-*.png (1280 px wide). The camera,
engine, view transform, resolution and the building's own materials are restored.
"""

import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\block-32-38-lightmap.jpg"
GLB_4046 = PROJECT + r"\assets\models\block-40-46.glb"
LM_4046 = PROJECT + r"\assets\textures\block-40-46-lightmap.jpg"
SCALE_4046 = 1.2093                    # index.html intensity of #bldg-40-46-main
OFF_4046 = (14.205, 0.06, 0.0)         # block-40-46 local -> this frame

scene = bpy.context.scene
r_obj = bpy.data.objects["Block3238"]
mesh = r_obj.data
scale = float(r_obj.get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("RW_Preview")
if not pcol:
    pcol = bpy.data.collections.new("RW_Preview")
    scene.collection.children.link(pcol)
pcol.hide_viewport = False
pcol.hide_render = False
cam_data = bpy.data.cameras.get("RW_Cam") or bpy.data.cameras.new("RW_Cam")
cam = bpy.data.objects.get("RW_Cam") or bpy.data.objects.new("RW_Cam", cam_data)
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


def glass_preview(src):
    """The `glass` material: not lightmapped in the scene; plain dark tint over the
    window backs at its own alpha (the scene adds the sky reflection later)."""
    bsdf = next(n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    mat = bpy.data.materials.new("RWP_" + src.name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    emit = N("ShaderNodeEmission")
    emit.inputs["Color"].default_value = bsdf.inputs["Base Color"].default_value
    tr = N("ShaderNodeBsdfTransparent")
    mix = N("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = bsdf.inputs["Alpha"].default_value
    L(tr.outputs[0], mix.inputs[1])
    L(emit.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs["Surface"])
    mat.use_backface_culling = True
    return mat


def preview_material(src, lm_image=None, lm_scale=None, lm_uv="Lightmap", uv0_name="UVMap"):
    """Unlit copy: emission = base colour (texture x factor, or plain) x lightmap x scale."""
    lm_image = lm_image or lm_img
    lm_scale = scale if lm_scale is None else lm_scale
    if src.name.split('.')[0] == "glass":
        return glass_preview(src)
    mat = bpy.data.materials.new("RWP_" + src.name)
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


# context (unlit, flat colours), local frame (-Y = west, Main St; +X = south): east sidewalk
# y -2.14 ... 1.76 (z 0 = sidewalk top); road and yards 0.15 lower; west sidewalk
walk = unlit("RWP_WalkMat", (0.42, 0.41, 0.38))
road = unlit("RWP_RoadMat", (0.30, 0.28, 0.25))
flat("RWP_Road", -200, 200, -200, 200, -0.15, road)
flat("RWP_Walk", -200, 200, -2.14, 1.76, -0.002, walk)
flat("RWP_WalkW", -200, 200, -18.84, -14.94, -0.002, walk)

# the built 40-46 next door, drawn the same way with its own lightmap (re-imported every run)
for o in [o for o in pcol.objects if o.name.startswith("RWP_4046")]:
    bpy.data.objects.remove(o, do_unlink=True)
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_4046)
lm_4046 = bpy.data.images.load(LM_4046, check_existing=True)
lm_4046.colorspace_settings.name = "sRGB"
for o in [o for o in bpy.data.objects if o not in _before]:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    pcol.objects.link(o)
    o.name = "RWP_4046"
    o.location = OFF_4046
    uvs = [u.name for u in o.data.uv_layers]
    for i, m in enumerate(list(o.data.materials)):
        o.data.materials[i] = preview_material(m, lm_4046, SCALE_4046, uvs[1], uvs[0])

# --- remember and change settings ----------------------------------------------------
originals = list(mesh.materials)
previews = [preview_material(m) for m in originals]
saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
render_state = {c.name: c.hide_render for c in bpy.data.collections}
for c in bpy.data.collections:
    c.hide_render = c.name not in ("Block3238", "RW_Preview")
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
# Local frame: -Y = Main St (west), +X = south (40-42), -X = north (gap to 24-30).
# Scene -> local: x = scene_z + 130.755, y = scene_x - 8.54, z = scene_y - 0.15.
VIEWS = {
    # straight on, from the west sidewalk across Main St
    "front":         dict(eye=(0.0, -17.0, 1.7), target=(0.0, 2.0, 3.2), lens=24, h=760),
    # from the NW across the 3.4 m gap: the long north wall, and the patch over 40-42 above D
    "three-quarter": dict(eye=(-19.0, -11.0, 4.5), target=(1.5, 6.0, 3.6), lens=26, h=860),
    # from the SW along the porch: the Meats strip stepping down beside 40-42, shop fronts
    "detail":        dict(eye=(8.6, -3.6, 1.65), target=(0.0, 1.4, 1.9), lens=22, h=860),
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
        scene.render.filepath = PREV + "block-32-38-" + name + ".png"
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
    pcol.hide_viewport = True
    bg.inputs[0].default_value, bg.inputs[1].default_value = saved_bg
    scene.camera = saved["camera"] or cam
    scene.render.engine = saved["engine"]
    scene.view_settings.view_transform = saved["vt"]
    scene.view_settings.look = saved["look"]
    scene.render.resolution_x, scene.render.resolution_y = saved["rx"], saved["ry"]
    scene.render.resolution_percentage = saved["pct"]
print("previews written:", *written, sep="\n  ")
