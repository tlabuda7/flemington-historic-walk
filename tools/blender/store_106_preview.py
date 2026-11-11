"""
store_106_preview.py - review previews of the baked corner drugstore, 106 Main St (run after
store_106_bake.py).

    exec(open(r"<project>/tools/blender/store_106_preview.py").read())

Renders with EEVEE, view transform "Standard", and every material swapped for an unlit
emission of colour x lightmap x LIGHTMAP_SCALE - the same maths as the web page's
`baked-lighting` component (MeshBasicMaterial: map x color x lightMap x intensity), so
the pictures match what the headset shows. The colour tints (glTF baseColorFactor) are
included. Writes assets/models/previews/store-106-*.png (1280 px wide). The camera, engine,
view transform, resolution and the building's own materials are restored.
Most views add the built 100-102 Main (its GLB with its own lightmap, the same unlit maths) to
the north. "match-100-110-Main" is taken from roughly the viewpoint of the 1890s photo
(Goodspeed `100-110-Main-copy.jpeg`, from the SW across Main St). Pattern:
store_100_102_preview.py.
"""

import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\store-106-lightmap.jpg"
GLB_N = PROJECT + r"\assets\models\store-100-102.glb"
LM_N = PROJECT + r"\assets\textures\store-100-102-lightmap.jpg"
SCALE_N = 1.1366                                     # 100-102's LIGHTMAP_SCALE
OFF_N = (52.01 - 58.80, 10.30 - 8.06, 0.0)           # its local frame -> this one

scene = bpy.context.scene
bk_obj = bpy.data.objects["Store106"]
mesh = bk_obj.data
scale = float(bk_obj.get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("DS_Preview")
if not pcol:
    pcol = bpy.data.collections.new("DS_Preview")
    scene.collection.children.link(pcol)
pcol.hide_render = False
cam_data = bpy.data.cameras.get("DS_Cam") or bpy.data.cameras.new("DS_Cam")
cam = bpy.data.objects.get("DS_Cam") or bpy.data.objects.new("DS_Cam", cam_data)
if cam.name not in pcol.objects:
    pcol.objects.link(cam)
cam_data.clip_start = 0.1
cam_data.clip_end = 600


def load_lm(path):
    img = bpy.data.images.load(path, check_existing=True)
    img.reload()
    img.colorspace_settings.name = "sRGB"          # three.js decodes it as sRGB too
    return img


lm_img = load_lm(LIGHTMAP)


def sock(socks, name):
    return next(x for x in socks if x.name == name and x.type == "RGBA")


def glass_preview(src):
    """The `glass` material: not lightmapped in the scene; plain dark tint over the
    window backs at its own alpha (the scene adds the sky reflection later)."""
    bsdf = next(n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    mat = bpy.data.materials.new("DSP_" + src.name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    emit = N("ShaderNodeEmission")
    emit.inputs["Color"].default_value = bsdf.inputs["Base Color"].default_value
    tr = N("ShaderNodeBsdfTransparent")
    mix = N("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.40
    L(tr.outputs[0], mix.inputs[1])
    L(emit.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs["Surface"])
    mat.use_backface_culling = True
    return mat


def preview_material(src, lm, lm_scale, uv_col="UVMap", uv_lm="Lightmap"):
    """Unlit copy: emission = base colour (texture x tint, or plain) x lightmap x scale."""
    if src.name.startswith("glass"):
        return glass_preview(src)
    mat = bpy.data.materials.new("DSP_" + src.name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    emit = N("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = lm_scale
    uv1 = N("ShaderNodeUVMap")
    uv1.uv_map = uv_lm
    lmn = N("ShaderNodeTexImage")
    lmn.image = lm
    L(uv1.outputs["UV"], lmn.inputs["Vector"])
    mix = N("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    bsdf = next(n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    src_tex = next((n for n in src.node_tree.nodes if n.type == "TEX_IMAGE" and n.name != "BakeTarget"), None)
    src_tint = next((n for n in src.node_tree.nodes if n.type == "MIX" and n.blend_type == "MULTIPLY"), None)
    if src_tex:
        uv0 = N("ShaderNodeUVMap")
        uv0.uv_map = uv_col
        tex = N("ShaderNodeTexImage")
        tex.image = src_tex.image
        L(uv0.outputs["UV"], tex.inputs["Vector"])
        colour = tex.outputs["Color"]
        tint = None
        if src_tint:
            tint = sock(src_tint.inputs, "B").default_value
        elif not bsdf.inputs["Base Color"].is_linked:
            tint = bsdf.inputs["Base Color"].default_value
        if tint is not None:
            t = N("ShaderNodeMix")
            t.data_type = "RGBA"
            t.blend_type = "MULTIPLY"
            t.inputs["Factor"].default_value = 1.0
            L(colour, sock(t.inputs, "A"))
            sock(t.inputs, "B").default_value = tint
            colour = sock(t.outputs, "Result")
        L(colour, sock(mix.inputs, "A"))
    else:
        sock(mix.inputs, "A").default_value = bsdf.inputs["Base Color"].default_value
    L(lmn.outputs["Color"], sock(mix.inputs, "B"))
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


# context (unlit, flat colours): east sidewalk from the curb (local y = -1.54) back under the
# porch, the Higgins Ave lane (X 3.3 ... 9.9) a little darker, the road 0.15 lower
flat("DSP_Walk", -150, 150, -1.54, 150, -0.005, unlit("DSP_WalkMat", (0.36, 0.34, 0.31)))
flat("DSP_Lane", 3.3, 9.9, -1.54, 60, -0.002, unlit("DSP_LaneMat", (0.31, 0.28, 0.24)))
flat("DSP_Road", -150, 150, -150, 150, -0.15, unlit("DSP_RoadMat", (0.30, 0.27, 0.23)))

# the built 100-102 Main, with its own lightmap
nb = bpy.data.objects.get("DSP_100102")
if not nb:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=GLB_N)
    nb = [o for o in bpy.data.objects if o not in before][0]
    for c in list(nb.users_collection):
        c.objects.unlink(nb)
    pcol.objects.link(nb)
    nb.name = "DSP_100102"
    nb.location = Vector(OFF_N)
    uvs = [u.name for u in nb.data.uv_layers]
    lm_n = load_lm(LM_N)
    for i, m in enumerate(list(nb.data.materials)):
        nb.data.materials[i] = preview_material(m, lm_n, SCALE_N, uvs[0], uvs[1])
NEIGHBOURS = [nb]

# --- remember and change settings ----------------------------------------------------
originals = list(mesh.materials)
previews = [preview_material(m, lm_img, scale) for m in originals]
saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
render_state = {c.name: c.hide_render for c in bpy.data.collections}
for c in bpy.data.collections:
    c.hide_render = c.name not in ("Store106", "DS_Preview")
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
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1280, 960, 100

# name -> (eye, target, lens). Local frame: -Y = Main St (west), +X = south (Higgins Ave),
# -X = north (100-102). Scene -> local: X = z - 58.80, Y = x - 8.06, Z = y - 0.15. The far
# (west) sidewalk is ~14 m in front of the porch; eye height 1.6-1.7 m.
VIEWS = {
    "front":              ((0.0, -15.0, 1.7), (0.0, 1.5, 4.7), 26),       # straight on
    "three-quarter":      ((-10.0, -12.5, 1.7), (0.0, 2.0, 4.4), 26),     # from the NW
    "detail":             ((-0.9, -4.2, 1.6), (0.0, 2.3, 1.8), 24),       # entrance under the porch
    "sw":                 ((13.0, -10.0, 1.7), (2.0, 7.0, 4.4), 26),      # from the SW: Higgins Ave side
    "match-100-110-Main": ((16.0, -11.5, 1.7), (0.0, 3.5, 5.0), 30),      # the 1890s photo's viewpoint
    "context":            ((-16.0, -13.0, 1.7), (-3.5, 2.0, 4.4), 24),    # from the NW, 100-102 beside it
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS     # set PREVIEW_VIEWS before exec() for other views
PREFIX = globals().get("PREVIEW_PREFIX") or "store-106-"
SOLO = ("front", "detail")                         # views without the neighbour
written = []
try:
    for name, (eye, target, lens) in VIEWS.items():
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = lens
        for o in NEIGHBOURS:
            o.hide_render = name in SOLO
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
    pcol.hide_render = True
    bg.inputs[0].default_value, bg.inputs[1].default_value = saved_bg
    scene.camera = saved["camera"] or cam
    scene.render.engine = saved["engine"]
    scene.view_settings.view_transform = saved["vt"]
    scene.view_settings.look = saved["look"]
    scene.render.resolution_x, scene.render.resolution_y = saved["rx"], saved["ry"]
    scene.render.resolution_percentage = saved["pct"]
print("previews written:", *written, sep="\n  ")
