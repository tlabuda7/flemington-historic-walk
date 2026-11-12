"""
house_91_93_preview.py - review previews of the baked 91-93 Main St house (run after
house_91_93_bake.py).

    exec(open(r"<project>/tools/blender/house_91_93_preview.py").read())

Renders with EEVEE, view transform "Standard", and every material swapped for an unlit emission
of colour x lightmap x LIGHTMAP_SCALE - the same maths as the web page's `baked-lighting`
component, so the pictures match what the headset shows. The neighbours imported by the bake
("H91_Neighbours": 83-87 and 79 Main, street ends, Court St side street, street details, back
lots) are drawn the same way with their own lightmaps and intensities from index.html. Context
(flat, unlit): lawn, the Main St walk, the road and the front path the integrator will lay
(GUESS, as PLAN.md). Writes assets/models/previews/house-91-93-*.png (1280 px wide). Camera,
engine, view transform, resolution and all materials are restored. Pattern: store_79_preview.py.
"""

import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
TXD = PROJECT + r"\assets\textures" + "\\"
LIGHTMAP = TXD + "house-91-93-lightmap.jpg"
NB_LM = {"block-83-87": ("block-83-87-lightmap.jpg", 1.0332),
         "store-79": ("store-79-lightmap.jpg", 1.0137),
         "street-ends": ("street-ends-lightmap.jpg", 1.0477),
         "sidestreet-court": ("sidestreet-court-lightmap.jpg", 1.0366),
         "street-details": ("street-details-lightmap.jpg", 1.0005),
         "back-lots": ("back-lots-lightmap.jpg", 1.0203)}
COLL, NEIGH, PCOL, CAM = "House9193", "H91_Neighbours", "H91_Preview", "H91_Cam"
ENTITY = (-13.18, 0.02, 38.63)

scene = bpy.context.scene
h_obj = bpy.data.objects[COLL]
mesh = h_obj.data
scale = float(h_obj.get("lightmap_scale", 1.0))
nb = bpy.data.collections.get(NEIGH)

pcol = bpy.data.collections.get(PCOL)
if not pcol:
    pcol = bpy.data.collections.new(PCOL)
    scene.collection.children.link(pcol)
pcol.hide_render = False
cam_data = bpy.data.cameras.get(CAM) or bpy.data.cameras.new(CAM)
cam = bpy.data.objects.get(CAM) or bpy.data.objects.new(CAM, cam_data)
if cam.name not in pcol.objects:
    pcol.objects.link(cam)
cam_data.clip_start = 0.1
cam_data.clip_end = 600


def load_lm(path):
    img = bpy.data.images.load(path, check_existing=True)
    img.reload()
    img.colorspace_settings.name = "sRGB"
    return img


def sock(socks, name):
    return next(x for x in socks if x.name == name and x.type == "RGBA")


def glass_preview(src):
    bsdf = next(n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    mat = bpy.data.materials.new("H91P_" + src.name)
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
    mat = bpy.data.materials.new("H91P_" + src.name)
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
    bsdf = next((n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    src_tex = next((n for n in src.node_tree.nodes if n.type == "TEX_IMAGE" and n.name != "BakeTarget"), None)
    src_tint = next((n for n in src.node_tree.nodes if n.type == "MIX" and n.blend_type == "MULTIPLY"), None)
    if src_tex:
        uv0 = N("ShaderNodeUVMap")
        uv0.uv_map = uv_col
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
            other = sock(src_tint.inputs, "B")
            if other.is_linked:
                other = sock(src_tint.inputs, "A")
            sock(t.inputs, "B").default_value = other.default_value
            colour = sock(t.outputs, "Result")
        L(colour, sock(mix.inputs, "A"))
    else:
        sock(mix.inputs, "A").default_value = bsdf.inputs["Base Color"].default_value if bsdf else (0.5, 0.5, 0.5, 1)
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
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)
    gm = bpy.data.meshes.new(name)
    gm.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
    gm.materials.append(mat)
    obj = bpy.data.objects.new(name, gm)
    pcol.objects.link(obj)
    return obj


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# context (local frame): scene lawn #6f8048 from the street line (Y -5.23) back; the walk
# (top 0.13) to the curb at Y -6.66; road 0.02 below the lawn; the front path (GUESS) from the
# walk to the steps, 1.2 m wide
flat("H91P_Lawn", -60, 60, -5.23, 60, -0.005, unlit("H91P_LawnMat", tuple(c * 0.9 for c in srgb("#6f8048"))))
flat("H91P_Walk", -60, 60, -6.66, -5.23, 0.13, unlit("H91P_WalkMat", (0.36, 0.34, 0.31)))
flat("H91P_Road", -300, 300, -300, 300, -0.02, unlit("H91P_RoadMat", (0.30, 0.27, 0.23)))
flat("H91P_Path", -0.6, 0.6, -5.23, -0.55, 0.01, unlit("H91P_PathMat", srgb("#b9b0a0")))

# --- remember and change settings ----------------------------------------------------
swaps = [(mesh, list(mesh.materials), [preview_material(m, load_lm(LIGHTMAP), scale) for m in mesh.materials])]
if nb:
    for o in nb.objects:
        if o.type != "MESH" or o.get("neighbour") not in NB_LM:
            continue
        f, s = NB_LM[o["neighbour"]]
        lmimg = load_lm(TXD + f)
        uvs = [u.name for u in o.data.uv_layers]
        if len(uvs) < 2:
            continue
        swaps.append((o.data, list(o.data.materials),
                      [preview_material(m, lmimg, s, uvs[0], uvs[1]) for m in o.data.materials]))
saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
render_state = {c.name: c.hide_render for c in bpy.data.collections}
for c in bpy.data.collections:
    c.hide_render = c.name not in (COLL, PCOL, NEIGH)
loose_state = {o.name: o.hide_render for o in scene.collection.objects}
for o in scene.collection.objects:
    o.hide_render = True
for me, orig, prev in swaps:
    for i, m in enumerate(prev):
        me.materials[i] = m
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

EYE = 1.75 + 0.13                     # eye height above the walk (local z of the walk 0.13)
VIEWS = {
    "front":            ((0.0, -19.5, 1.75), (0.0, 4.0, 4.6), 24, (0, 0), (1280, 960)),
    "three-quarter-ne": ((15.0, -16.0, 1.75), (0.0, 5.0, 4.4), 24, (0, 0), (1280, 960)),
    "three-quarter-se": ((-15.0, -16.0, 1.75), (-1.5, 5.0, 4.4), 24, (0, 0), (1280, 960)),
    "detail":           ((2.0, -6.0, EYE), (-0.3, 2.2, 2.0), 26, (0, 0), (1280, 960)),
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS
PREFIX = globals().get("PREVIEW_PREFIX") or "house-91-93-"
SOLO = ("detail",)
written = []
try:
    for name, (eye, target, lens, shift, res) in VIEWS.items():
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = lens
        cam_data.sensor_fit = "HORIZONTAL"
        cam_data.sensor_width = 36
        cam_data.shift_x, cam_data.shift_y = shift
        scene.render.resolution_x, scene.render.resolution_y = res
        if nb:
            for o in nb.objects:
                o.hide_render = name in SOLO
        scene.render.filepath = PREV + PREFIX + name + ".png"
        bpy.ops.render.render(write_still=True)
        written.append(scene.render.filepath)
finally:
    cam_data.shift_x = cam_data.shift_y = 0.0
    for me, orig, prev in swaps:
        for i, m in enumerate(orig):
            me.materials[i] = m
        for m in prev:
            bpy.data.materials.remove(m)
    for name, state in render_state.items():
        if bpy.data.collections.get(name):
            bpy.data.collections[name].hide_render = state
    for name, state in loose_state.items():
        if bpy.data.objects.get(name):
            bpy.data.objects[name].hide_render = state
    pcol.hide_render = True
    if nb:
        nb.hide_render = True
    bg.inputs[0].default_value, bg.inputs[1].default_value = saved_bg
    scene.camera = saved["camera"] or cam
    scene.render.engine = saved["engine"]
    scene.view_settings.view_transform = saved["vt"]
    scene.view_settings.look = saved["look"]
    scene.render.resolution_x, scene.render.resolution_y = saved["rx"], saved["ry"]
    scene.render.resolution_percentage = saved["pct"]
print("previews written:", *written, sep="\n  ")
