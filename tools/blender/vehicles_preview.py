"""
vehicles_preview.py - review previews of the baked vehicles, version 2 (run after vehicles_bake.py).

    exec(open(r"<project>/tools/blender/vehicles_preview.py").read())

EEVEE, view transform "Standard". Every vehicle material is swapped for an unlit emission of
colour x lightmap x LIGHTMAP_SCALE (the web page's baked-lighting maths); glass as a dark
see-through tint. The vehicles stand on a lit road-coloured ground plane with the bake's sun
(same direction and colour, soft 3 degree disc) so they cast soft shadows; sky as in the bake.
A 1.75 m reference box for the scale view. Everything is put back afterwards.
Writes assets/models/previews/vehicles-*.png (1600 px wide); old vehicles-*.png are removed first.
"""
import glob
import math
import os
import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\vehicles-lightmap.jpg"
NAMES = ["model-t", "buggy", "delivery-wagon"]
POS = {"model-t": (0, 0, 0), "buggy": (0, -9, 0), "delivery-wagon": (0, -19, 0)}
TO_SUN = (-0.90, -0.40, 0.36)

scene = bpy.context.scene
objs = [bpy.data.objects[n] for n in NAMES]
scale = float(objs[0].get("lightmap_scale", 1.0))
pcol = bpy.data.collections.get("VEH_Preview") or bpy.data.collections.new("VEH_Preview")
if pcol.name not in scene.collection.children:
    scene.collection.children.link(pcol)
pcol.hide_render = False
pcol.hide_viewport = False
for o in list(pcol.objects):
    bpy.data.objects.remove(o, do_unlink=True)
cam_data = bpy.data.cameras.get("VEH_Cam") or bpy.data.cameras.new("VEH_Cam")
cam = bpy.data.objects.new("VEH_Cam", cam_data)
pcol.objects.link(cam)
cam_data.clip_start = 0.03
cam_data.clip_end = 300
sun_data = bpy.data.lights.get("VEHP_Sun") or bpy.data.lights.new("VEHP_Sun", "SUN")
sun = bpy.data.objects.new("VEHP_Sun", sun_data)
pcol.objects.link(sun)
sun_data.energy = 3.2
sun_data.color = (1.0, 0.80, 0.58)
sun_data.angle = math.radians(3.0)
sun.rotation_euler = (-Vector(TO_SUN).normalized()).to_track_quat("-Z", "Y").to_euler()
lm = bpy.data.images.load(LIGHTMAP, check_existing=True)
lm.reload()
lm.colorspace_settings.name = "sRGB"


def sock(socks, name):
    return next(x for x in socks if x.name == name and x.type == "RGBA")


def preview_material(src):
    bsdf = next(n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    mat = bpy.data.materials.new("VEHP_" + src.name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    emit = N("ShaderNodeEmission")
    if src.name == "glass":
        emit.inputs["Color"].default_value = bsdf.inputs["Base Color"].default_value
        tr = N("ShaderNodeBsdfTransparent")
        mix = N("ShaderNodeMixShader")
        mix.inputs["Fac"].default_value = bsdf.inputs["Alpha"].default_value
        L(tr.outputs[0], mix.inputs[1])
        L(emit.outputs[0], mix.inputs[2])
        L(mix.outputs[0], out.inputs["Surface"])
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        return mat
    emit.inputs["Strength"].default_value = scale
    uv1 = N("ShaderNodeUVMap")
    uv1.uv_map = "Lightmap"
    lmn = N("ShaderNodeTexImage")
    lmn.image = lm
    L(uv1.outputs["UV"], lmn.inputs["Vector"])
    mix = N("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    tex0 = next((n for n in src.node_tree.nodes if n.type == "TEX_IMAGE"), None)
    tint0 = next((n for n in src.node_tree.nodes if n.type == "MIX"), None)
    if tex0:
        uv0 = N("ShaderNodeUVMap")
        uv0.uv_map = "UVMap"
        tex = N("ShaderNodeTexImage")
        tex.image = tex0.image
        L(uv0.outputs["UV"], tex.inputs["Vector"])
        t = N("ShaderNodeMix")
        t.data_type = "RGBA"
        t.blend_type = "MULTIPLY"
        t.inputs["Factor"].default_value = 1.0
        L(tex.outputs["Color"], sock(t.inputs, "A"))
        sock(t.inputs, "B").default_value = sock(tint0.inputs, "B").default_value
        L(sock(t.outputs, "Result"), sock(mix.inputs, "A"))
    else:
        sock(mix.inputs, "A").default_value = bsdf.inputs["Base Color"].default_value
    L(lmn.outputs["Color"], sock(mix.inputs, "B"))
    L(sock(mix.outputs, "Result"), emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def lit(name, rgb, rough=0.9):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(b.outputs["BSDF"], o.inputs["Surface"])
    return m


def helper_box(name, c, s, mat):
    x0, y0, z0 = (c[i] - s[i] / 2 for i in range(3))
    x1, y1, z1 = (c[i] + s[i] / 2 for i in range(3))
    v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)])
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    pcol.objects.link(o)
    return o


helper_box("VEHP_Ground", (0, -9, -0.05), (120, 120, 0.1), lit("VEHP_GroundMat", (0.28, 0.23, 0.17)))
figure = helper_box("VEHP_Figure", (0, 0, 0.875), (0.45, 0.30, 1.75), lit("VEHP_FigureMat", (0.55, 0.12, 0.10), 0.7))

for f in glob.glob(PREV + "vehicles-*.png"):
    os.remove(f)

originals = {o.name: list(o.data.materials) for o in objs}
pmats = {}
saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
eevee = scene.eevee
saved_rt = getattr(eevee, "use_raytracing", None)
render_state = {c.name: c.hide_render for c in bpy.data.collections}
loose_state = {o.name: o.hide_render for o in scene.collection.objects}
for c in bpy.data.collections:
    c.hide_render = c.name not in ("vehicles", "VEH_Preview")
for o in scene.collection.objects:
    o.hide_render = True
for o in objs:
    o.location = POS[o.name]
    o.hide_render = False
    for i, m in enumerate(originals[o.name]):
        if m.name not in pmats:
            pmats[m.name] = preview_material(m)
        o.data.materials[i] = pmats[m.name]
world = scene.world
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
saved_bg = (tuple(bg.inputs[0].default_value), bg.inputs[1].default_value)
bg.inputs[0].default_value = (0.42, 0.55, 0.78, 1)
bg.inputs[1].default_value = 0.9
scene.camera = cam
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = eng
        break
    except TypeError:
        pass
if saved_rt is not None:
    eevee.use_raytracing = True
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1600, 1000, 100


def V(p, d):
    return tuple(a + b for a, b in zip(p, d))


# (eye, target, lens, figure location or None); front of every vehicle is -Y, street side -X
VIEWS = {}
for n, short in (("model-t", "model-t"), ("buggy", "buggy"), ("delivery-wagon", "wagon")):
    p = POS[n]
    dy = -0.5 if n != "model-t" else 0.0           # shafts reach forward
    tgt = V(p, (0, dy, 0.85))
    VIEWS[short + "-three-quarter-front"] = (V(p, (-4.6, -5.4 + dy, 1.65)), tgt, 40, None)
    VIEWS[short + "-three-quarter-rear"] = (V(p, (-4.4, 4.6, 1.75)), V(p, (0, -0.2, 0.85)), 40, None)
    VIEWS[short + "-side"] = (V(p, (-9.0, dy, 1.05)), V(tgt, (0, 0, 0.05)), 42 if n == "model-t" else 36, None)
VIEWS["model-t-front"] = ((0.0, -6.8, 1.6), (0.0, 0.0, 0.85), 42, None)      # eye 1.6 m, crank visible
VIEWS["model-t-top-rear"] = ((-2.3, 4.9, 3.1), (0.0, 0.85, 1.35), 38, None)    # top, rear curtain, back light
VIEWS["wheel-closeup"] = ((-1.95, -1.80, 0.62), (-0.70, -1.27, 0.40), 50, None)
VIEWS["wheel-closeup-buggy"] = ((-1.85, -9.0 - 1.45, 0.75), (-0.70, -9.0 - 0.80, 0.50), 50, None)
VIEWS["scale"] = ((-20.0, -10.0, 3.4), (0, -10.0, 0.9), 28, (-2.0, -4.5, 0))
written = []
try:
    for name, (eye, target, lens, fig) in VIEWS.items():
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = lens
        figure.hide_render = fig is None
        if fig:
            figure.location = fig
        scene.render.filepath = PREV + "vehicles-" + name + ".png"
        bpy.ops.render.render(write_still=True)
        written.append(scene.render.filepath)
finally:
    for o in objs:
        for i, m in enumerate(originals[o.name]):
            o.data.materials[i] = m
        o.location = (0, 0, 0)
    for m in pmats.values():
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
    scene.camera = saved["camera"] if saved["camera"] and saved["camera"].name in bpy.data.objects else cam
    scene.render.engine = saved["engine"]
    if saved_rt is not None:
        eevee.use_raytracing = saved_rt
    scene.view_settings.view_transform = saved["vt"]
    scene.view_settings.look = saved["look"]
    scene.render.resolution_x, scene.render.resolution_y = saved["rx"], saved["ry"]
    scene.render.resolution_percentage = saved["pct"]
print("previews written:", *written, sep="\n  ")
