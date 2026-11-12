"""
block_83_87_preview.py - review previews of the baked 83-87 Main St grocery (run after
block_83_87_bake.py).

    exec(open(r"<project>/tools/blender/block_83_87_preview.py").read())

Renders with EEVEE, view transform "Standard", and every material swapped for an unlit
emission of colour x lightmap x LIGHTMAP_SCALE - the same maths as the web page's
`baked-lighting` component (MeshBasicMaterial: map x color x lightMap x intensity), so the
pictures match what the headset shows. Writes assets/models/previews/block-83-87-*.png
(1280 px wide). The camera, engine, view transform, resolution and the building's own
materials are restored. Pattern: store_106_preview.py.

"match-card" is taken from the viewpoint of the Goodspeed card "Main Street looking S."
(c. 1905-12; PLAN.md [C1]): camera on the road at scene (0, 1.6, -3.3) looking south, focal
length ~2430 px on a 2076 px wide card (lens 42 mm on a 36 mm sensor), the vanishing point at
u 1100 / v ~1100 (lens shift, verticals stay vertical), 2076 x 1350 aspect. The card itself
is view-only and not used here.
"""

import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\block-83-87-lightmap.jpg"

scene = bpy.context.scene
bk_obj = bpy.data.objects["Block8387"]
mesh = bk_obj.data
scale = float(bk_obj.get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("GB_Preview")
if not pcol:
    pcol = bpy.data.collections.new("GB_Preview")
    scene.collection.children.link(pcol)
pcol.hide_render = False
cam_data = bpy.data.cameras.get("GB_Cam") or bpy.data.cameras.new("GB_Cam")
cam = bpy.data.objects.get("GB_Cam") or bpy.data.objects.new("GB_Cam", cam_data)
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
    mat = bpy.data.materials.new("GBP_" + src.name)
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
    mat = bpy.data.materials.new("GBP_" + src.name)
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


def block(name, x0, x1, y0, y1, z0, z1, mat):
    obj = bpy.data.objects.get(name)
    if not obj:
        v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
        gm = bpy.data.meshes.new(name)
        gm.from_pydata(v, [], [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)])
        gm.materials.append(mat)
        obj = bpy.data.objects.new(name, gm)
        pcol.objects.link(obj)
    return obj


# context (unlit, flat colours): west walk from the curb (local y = -0.10) back under the
# porch and to the street line, the road 0.15 lower, grass in 91's yard to the south; plain
# grey boxes for the 79 Main and 91-93 placeholders (not built yet)
flat("GBP_Walk", -40, 40, -0.10, 60, -0.005, unlit("GBP_WalkMat", (0.36, 0.34, 0.31)))
flat("GBP_Yard", -20.0, -3.31, 4.70, 60, -0.002, unlit("GBP_YardMat", (0.16, 0.20, 0.10)))
flat("GBP_Road", -150, 150, -150, 150, -0.15, unlit("GBP_RoadMat", (0.30, 0.27, 0.23)))
occ = unlit("GBP_OccMat", (0.42, 0.40, 0.37))
NEIGHBOURS = [block("GBP_79", 5.06, 12.72, 5.16, 27.02, 0.0, 9.75, occ),
              block("GBP_9193", -19.30, -11.74, 10.79, 19.07, 0.0, 6.5, occ)]

# --- remember and change settings ----------------------------------------------------
originals = list(mesh.materials)
previews = [preview_material(m, lm_img, scale) for m in originals]
saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
render_state = {c.name: c.hide_render for c in bpy.data.collections}
for c in bpy.data.collections:
    c.hide_render = c.name not in ("Block8387", "GB_Preview")
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

# name -> (eye, target, lens, shift, (res x, res y)). Local frame: -Y = Main St (east), +X =
# north (79 Main), -X = south (91-93's yard). Scene -> local: X = 23.11 - z, Y = -4.58 - x,
# Z = y - 0.15. The far (east) walk is ~15 m in front of the porch; eye height 1.6-1.7 m.
CARD_EYE = (23.11 + 3.3, -4.58 - 0.0, 1.6 - 0.15)
VIEWS = {
    "front":              ((0.0, -14.5, 1.7), (0.0, 4.0, 4.9), 24, (0, 0), (1280, 960)),
    "three-quarter-ne":   ((11.0, -12.5, 1.7), (0.0, 4.0, 4.6), 24, (0, 0), (1280, 960)),
    "three-quarter-se":   ((-13.0, -11.0, 1.7), (-2.0, 6.0, 4.6), 24, (0, 0), (1280, 960)),
    "detail":             ((-1.2, -3.6, 1.6), (0.2, 4.5, 2.0), 20, (0, 0), (1280, 960)),
    "match-card":         (CARD_EYE, (CARD_EYE[0] - 50.0, CARD_EYE[1], CARD_EYE[2]), 42.1,
                           (-0.03, 0.205), (1280, 832)),
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS
PREFIX = globals().get("PREVIEW_PREFIX") or "block-83-87-"
SOLO = ("front", "detail")                         # views without the neighbour boxes
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
        for o in NEIGHBOURS:
            o.hide_render = name in SOLO
        scene.render.filepath = PREV + PREFIX + name + ".png"
        bpy.ops.render.render(write_still=True)
        written.append(scene.render.filepath)
finally:
    cam_data.shift_x = cam_data.shift_y = 0.0
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
