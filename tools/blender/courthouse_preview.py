"""
courthouse_preview.py - review previews of the baked courthouse (run after courthouse_bake.py).

    exec(open(r"<project>/tools/blender/courthouse_preview.py").read())

Renders with EEVEE, view transform "Standard", and every material swapped for an unlit
emission of colour x lightmap x LIGHTMAP_SCALE - the same maths as the web page's
`baked-lighting` component, so the pictures match what the headset shows.
Writes assets/models/previews/courthouse-*.png (1280 px wide). The camera, engine,
view transform, resolution and the courthouse's own materials are restored afterwards.
"""

import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\courthouse-lightmap.jpg"

scene = bpy.context.scene
ch = bpy.data.objects["Courthouse"]
mesh = ch.data
scale = float(ch.get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("CH_Preview")
if not pcol:
    pcol = bpy.data.collections.new("CH_Preview")
    scene.collection.children.link(pcol)
cam_data = bpy.data.cameras.get("CH_Cam") or bpy.data.cameras.new("CH_Cam")
cam = bpy.data.objects.get("CH_Cam") or bpy.data.objects.new("CH_Cam", cam_data)
if cam.name not in pcol.objects:
    pcol.objects.link(cam)
cam_data.clip_end = 600

lm_img = bpy.data.images.load(LIGHTMAP, check_existing=True)
lm_img.reload()
lm_img.colorspace_settings.name = "sRGB"          # three.js decodes it as sRGB too


def preview_material(src):
    """Unlit copy: emission = base colour (texture or plain) x lightmap x scale."""
    mat = bpy.data.materials.new("CHP_" + src.name)
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
    sock = lambda socks, name: next(x for x in socks if x.name == name and x.type == "RGBA")
    src_tex = next((n for n in src.node_tree.nodes if n.type == "TEX_IMAGE"), None)
    if src_tex:
        uv0 = N("ShaderNodeUVMap")
        uv0.uv_map = "UVMap"
        tex = N("ShaderNodeTexImage")
        tex.image = src_tex.image
        L(uv0.outputs["UV"], tex.inputs["Vector"])
        L(tex.outputs["Color"], sock(mix.inputs, "A"))
    else:
        bsdf = next(n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        sock(mix.inputs, "A").default_value = bsdf.inputs["Base Color"].default_value
    L(lm.outputs["Color"], sock(mix.inputs, "B"))
    L(sock(mix.outputs, "Result"), emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


# a plain unlit ground (warm grey paving) for context
ground = bpy.data.objects.get("CHP_Ground")
if not ground:
    gm = bpy.data.meshes.new("CHP_Ground")
    S = 150.0
    gm.from_pydata([(-S, -S, -0.005), (S, -S, -0.005), (S, S, -0.005), (-S, S, -0.005)], [], [(0, 1, 2, 3)])
    gmat = bpy.data.materials.new("CHP_GroundMat")
    gmat.use_nodes = True
    gnt = gmat.node_tree
    gnt.nodes.clear()
    ge = gnt.nodes.new("ShaderNodeEmission")
    ge.inputs["Color"].default_value = (0.30, 0.28, 0.25, 1)
    go = gnt.nodes.new("ShaderNodeOutputMaterial")
    gnt.links.new(ge.outputs["Emission"], go.inputs["Surface"])
    gm.materials.append(gmat)
    ground = bpy.data.objects.new("CHP_Ground", gm)
    pcol.objects.link(ground)

# --- remember and change settings ----------------------------------------------------
originals = list(mesh.materials)
previews = [preview_material(m) for m in originals]
saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
render_state = {c.name: c.hide_render for c in bpy.data.collections}
for c in bpy.data.collections:
    c.hide_render = c.name not in ("Courthouse", "CH_Preview")
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

# name -> (eye, target, lens).  Local frame: -Y = Main St (east), +X = north, -X = Court St.
# The far side of Main St is ~27 m in front of the portico; eye height 1.7 m.
VIEWS = {
    "front":            ((0.0, -27.5, 1.7), (1.0, 0.0, 8.8), 28),
    "three-quarter":    ((19.0, -21.0, 1.7), (1.5, 8.0, 8.0), 24),       # from the north-east
    "three-quarter-se": ((-17.0, -21.0, 1.7), (-2.5, 8.0, 8.0), 24),     # from the south-east (Court St corner)
    "detail":           ((2.4, -6.8, 1.9), (0.0, 4.4, 3.2), 26),         # the entrance
    "match-1910":       ((0.0, -40.0, 2.0), (0.0, 0.0, 9.0), 40),        # dead-on c.1910 postcard
    "match-1909":       ((26.0, -24.0, 2.0), (1.0, 8.0, 9.0), 30),       # 1909 colour card, from the NE
    "match-habs":       ((-19.0, -19.0, 1.6), (-3.0, 7.0, 8.5), 24),     # HABS east front and south side
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS     # set PREVIEW_VIEWS before exec() for extra views
written = []
try:
    for name, (eye, target, lens) in VIEWS.items():
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = lens
        scene.render.filepath = PREV + "courthouse-" + name + ".png"
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
