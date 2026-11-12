"""
county_offices_preview.py - review previews of the baked County Offices (run after
county_offices_bake.py).

    exec(open(r"<project>/tools/blender/county_offices_preview.py").read())

Renders with EEVEE, view transform "Standard", and every material swapped for an unlit
emission of colour x lightmap x LIGHTMAP_SCALE - the same maths as the web page's
`baked-lighting` component (MeshBasicMaterial: map x color x lightMap x intensity), so
the pictures match what the headset shows. The brick's tint (glTF baseColorFactor) is
included. Writes assets/models/previews/county-offices-*.png (1280 px wide). The camera,
engine, view transform, resolution and the building's own materials are restored.
"""

import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\county-offices-lightmap.jpg"

scene = bpy.context.scene
co_obj = bpy.data.objects["CountyOffices"]
mesh = co_obj.data
scale = float(co_obj.get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("CO_Preview")
if not pcol:
    pcol = bpy.data.collections.new("CO_Preview")
    scene.collection.children.link(pcol)
cam_data = bpy.data.cameras.get("CO_Cam") or bpy.data.cameras.new("CO_Cam")
cam = bpy.data.objects.get("CO_Cam") or bpy.data.objects.new("CO_Cam", cam_data)
if cam.name not in pcol.objects:
    pcol.objects.link(cam)
cam_data.clip_end = 600

lm_img = bpy.data.images.load(LIGHTMAP, check_existing=True)
lm_img.reload()
lm_img.colorspace_settings.name = "sRGB"          # three.js decodes it as sRGB too


def sock(socks, name):
    return next(x for x in socks if x.name == name and x.type == "RGBA")


SKY = PROJECT + r"\assets\textures\sky\sky-late-afternoon.jpg"
REFLECT = 1.2                                     # glass-reflect intensity (js/components.js)


def glass_preview(src):
    """Glass (section E): not lightmapped in the scene; dark tint over the window backs at its
    own alpha, plus the glass-reflect sky reflection (Fresnel, IOR 1.5, x REFLECT) on top."""
    bsdf = next(n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    mat = bpy.data.materials.new("COP_" + src.name)
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
    tc = N("ShaderNodeTexCoord")
    env = N("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(SKY, check_existing=True)
    L(tc.outputs["Reflection"], env.inputs["Vector"])
    fres = N("ShaderNodeFresnel")
    fres.inputs["IOR"].default_value = 1.5
    refl = N("ShaderNodeEmission")
    L(env.outputs["Color"], refl.inputs["Color"])
    k = N("ShaderNodeMath")
    k.operation = "MULTIPLY"
    L(fres.outputs[0], k.inputs[0])
    k.inputs[1].default_value = REFLECT
    L(k.outputs[0], refl.inputs["Strength"])
    add = N("ShaderNodeAddShader")
    L(mix.outputs[0], add.inputs[0])
    L(refl.outputs[0], add.inputs[1])
    L(add.outputs[0], out.inputs["Surface"])
    mat.use_backface_culling = True
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    elif hasattr(mat, "blend_method"):
        mat.blend_method = "BLEND"
    return mat


def preview_material(src):
    """Unlit copy: emission = base colour (texture x tint, or plain) x lightmap x scale."""
    if src.name == "glass":
        return glass_preview(src)
    mat = bpy.data.materials.new("COP_" + src.name)
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


# context: lawn in front of the building, the street beyond (unlit, flat colours)
flat("COP_Lawn", -150, 150, -7.4, 150, -0.005, unlit("COP_LawnMat", (0.13, 0.17, 0.07)))
flat("COP_Street", -150, 150, -150, -7.4, 0.13, unlit("COP_StreetMat", (0.30, 0.28, 0.25)))

# --- remember and change settings ----------------------------------------------------
originals = list(mesh.materials)
previews = [preview_material(m) for m in originals]
saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
render_state = {c.name: c.hide_render for c in bpy.data.collections}
for c in bpy.data.collections:
    c.hide_render = c.name not in ("CountyOffices", "CO_Preview")
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

# name -> (eye, target, lens). Local frame: -Y = Main St (east), +X = north, -X = south
# (the courthouse). The far (east) sidewalk is ~26 m in front of the wall and ~0.13 m above
# the lawn; eye height 1.7 m above it.
VIEWS = {
    "front":              ((0.0, -26.0, 1.83), (0.0, 0.0, 4.6), 30),
    "three-quarter-ne":   ((19.0, -19.0, 1.83), (0.0, 6.0, 4.8), 26),
    "three-quarter-se":   ((-19.0, -19.0, 1.83), (0.0, 6.0, 4.8), 26),
    "detail":             ((1.6, -6.8, 1.75), (0.0, 0.0, 2.6), 30),     # centre entrance and stoop
    "match-1908":         ((22.0, -27.0, 1.9), (-2.5, 5.0, 5.5), 38),   # flmngtncntybldngsvuof08, from the NE
    "match-1912":         ((-11.0, -15.5, 1.7), (2.0, 2.0, 4.6), 24),   # county building 1912, from the SE
}
# Section E (windows) pictures, 2026-11-11: run with
#   PREVIEW_VIEWS = "windows"; PREVIEW_PREFIX = "county-offices-windows-after"
WINDOW_VIEWS = {
    # straight on from the east sidewalk in front of the lawn, eye 1.6 m above the walk
    "":        ((0.0, -12.5, 1.73), (0.0, 0.0, 4.9), 20),
    # one ground-floor window (south inner) close up, glass with the sky reflection
    "-detail": ((-1.2, -3.2, 2.0), (-2.1, 0.0, 2.9), 32),
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS     # set PREVIEW_VIEWS before exec() for other views
if VIEWS == "windows":
    VIEWS = WINDOW_VIEWS
PREFIX = globals().get("PREVIEW_PREFIX") or "county-offices-"
written = []
try:
    for name, (eye, target, lens) in VIEWS.items():
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = lens
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
