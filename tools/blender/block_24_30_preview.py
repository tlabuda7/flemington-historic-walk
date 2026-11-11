"""
block_24_30_preview.py - review previews of the baked frame buildings at 24-30 Main St (24
dwelling, 26 Mill'y, 28-30 Conf'y / Barber) (run after block_24_30_bake.py). The built
block-32-38.glb is shown beside it (its own lightmap and intensity) for the context view.

    exec(open(r"<project>/tools/blender/block_24_30_preview.py").read())

Renders with EEVEE, view transform "Standard", and every material swapped for an unlit
emission of colour x lightmap x LIGHTMAP_SCALE - the same maths as the web page's
`baked-lighting` component (MeshBasicMaterial: map x color x lightMap x intensity), so
the pictures match what the headset shows. Colour factors (glTF baseColorFactor) are
included. Writes assets/models/previews/block-24-30-*.png (1280 px wide). The camera,
engine, view transform, resolution and the building's own materials are restored.
"""

import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\block-24-30-lightmap.jpg"
GLB_3238 = PROJECT + r"\assets\models\block-32-38.glb"
LM_3238 = PROJECT + r"\assets\textures\block-32-38-lightmap.jpg"
SCALE_3238 = 1.1463                    # index.html intensity of #bldg-32-38-main
OFF_3238 = (21.61, 1.25, 0.0)          # block-32-38 local -> this frame

scene = bpy.context.scene
r_obj = bpy.data.objects["Block2430"]
mesh = r_obj.data
scale = float(r_obj.get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("HS_Preview")
if not pcol:
    pcol = bpy.data.collections.new("HS_Preview")
    scene.collection.children.link(pcol)
pcol.hide_viewport = False
pcol.hide_render = False
cam_data = bpy.data.cameras.get("HS_Cam") or bpy.data.cameras.new("HS_Cam")
cam = bpy.data.objects.get("HS_Cam") or bpy.data.objects.new("HS_Cam", cam_data)
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
    mat = bpy.data.materials.new("HSP_" + src.name)
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
    mat = bpy.data.materials.new("HSP_" + src.name)
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


def poly(name, pts, z, mat):
    obj = bpy.data.objects.get(name)
    if not obj:
        gm = bpy.data.meshes.new(name)
        gm.from_pydata([(x, y, z) for x, y in pts], [], [tuple(range(len(pts)))])
        gm.materials.append(mat)
        obj = bpy.data.objects.new(name, gm)
        pcol.objects.link(obj)
    return obj


# context (unlit, flat colours), local frame (-Y = west, Main St; +X = south): east walk from
# the slanted road edge (y = -2.895 + 0.0321 X) to the fronts (z 0 = walk top); road and yards
# 0.15 lower; west walk scene x -10.3 ... -6.4 = local y -17.59 ... -13.69
walk = unlit("HSP_WalkMat", (0.42, 0.41, 0.38))
road = unlit("HSP_RoadMat", (0.30, 0.28, 0.25))
flat("HSP_Road", -200, 200, -200, 200, -0.15, road)
edge = lambda x: -2.895 + 0.0321 * x
poly("HSP_Walk", [(-60, edge(-60)), (60, edge(60)), (60, 1.94), (-60, 1.94)], -0.002, walk)
flat("HSP_WalkW", -200, 200, -17.59, -13.69, -0.002, walk)

# the built 32-38 to the south, drawn the same way with its own lightmap (re-imported every run)
for o in [o for o in pcol.objects if o.name.startswith("HSP_3238")]:
    bpy.data.objects.remove(o, do_unlink=True)
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_3238)
lm_3238 = bpy.data.images.load(LM_3238, check_existing=True)
lm_3238.colorspace_settings.name = "sRGB"
for o in [o for o in bpy.data.objects if o not in _before]:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    pcol.objects.link(o)
    o.name = "HSP_3238"
    o.location = OFF_3238
    uvs = [u.name for u in o.data.uv_layers]
    for i, m in enumerate(list(o.data.materials)):
        o.data.materials[i] = preview_material(m, lm_3238, SCALE_3238, uvs[1], uvs[0])

# --- remember and change settings ----------------------------------------------------
originals = list(mesh.materials)
previews = [preview_material(m) for m in originals]
saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
render_state = {c.name: c.hide_render for c in bpy.data.collections}
for c in bpy.data.collections:
    c.hide_render = c.name not in ("Block2430", "HS_Preview")
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
# Local frame: -Y = Main St (west), +X = south (32-38), -X = north (no. 22).
# Scene -> local: x = scene_z + 152.365, y = scene_x - 7.29, z = scene_y - 0.15.
VIEWS = {
    # straight on, from the west sidewalk across Main St
    "front":         dict(eye=(0.0, -26.0, 1.7), target=(0.0, 2.0, 3.4), lens=24, h=640),
    # from the SW along the porches (28-30's two tiers, 26's deep porch beyond)
    "three-quarter": dict(eye=(17.0, -12.0, 1.7), target=(-1.0, 1.0, 3.0), lens=26, h=820),
    # 26's entrance: the bay shop window and door under the deep porch
    "detail":        dict(eye=(1.2, -6.4, 1.6), target=(-2.6, 1.0, 1.7), lens=22, h=860),
    # from the NW: 24's gable end and north wall, the porch row
    "nw":            dict(eye=(-22.0, -12.0, 2.0), target=(-3.0, 3.0, 3.2), lens=26, h=820),
    # the 26 | 28 gap from the street
    "gap":           dict(eye=(1.2, -9.0, 1.6), target=(1.2, 10.0, 2.6), lens=24, h=860),
    # context with 32-38 to the south, from the west walk looking SE
    "context":       dict(eye=(-8.0, -15.5, 1.7), target=(12.0, 2.0, 3.0), lens=22, h=720),
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
        scene.render.filepath = PREV + "block-24-30-" + name + ".png"
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
