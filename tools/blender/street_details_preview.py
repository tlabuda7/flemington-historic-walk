"""
street_details_preview.py - review previews of the baked street-details kit (run after
street_details_bake.py). Same method as sidestreet_bloomfield_preview.py.

    exec(open(r"<project>/tools/blender/street_details_preview.py").read())

EEVEE, view transform "Standard", every material of the kit swapped for an unlit emission of
colour x lightmap x LIGHTMAP_SCALE (the web page's `baked-lighting` maths; the hedge cards keep
their alpha cut-out). Context drawn the same way: the neighbouring buildings' GLBs at their
index.html places with their own lightmaps and intensities, street trees lit by a preview sun,
flat unlit boxes for the ground, lawn and walks. Writes assets/models/previews/street-details-*.png
(1280 px wide). Camera, engine, view transform, resolution and the kit's materials are restored.

Scene -> Blender: (x, y, z) -> (x, -z, y).
"""

import math
import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\street-details-lightmap.jpg"
M = PROJECT + r"\assets\models" + "\\"
T = PROJECT + r"\assets\textures" + "\\"
CONTEXT = [  # glb, lightmap, intensity, scene position (index.html), rotation y
    ("wurts-law-office.glb", "wurts-law-office-lightmap.jpg", 1.1697, (-14.95, 0.02, -68.69), 90),
    ("house-65-main.glb", "house-65-main-lightmap.jpg", 1.274, (-14.07, 0.02, -51.19), 90),
    ("county-offices.glb", "county-offices-lightmap.jpg", 1.1299, (-17.71, 0.02, -27.87), 90),
    ("courthouse.glb", "courthouse-lightmap.jpg", 1.1979, (-18.34, 0.15, -6.85), 90),
    ("store-57.glb", "store-57-lightmap.jpg", 1.1581, (-12.40, 0.15, -84.94), 90),
    ("rea-building.glb", "rea-building-lightmap.jpg", 1.1726, (10.85, 0.15, -97.79), -90),
    ("union-hotel.glb", "union-hotel-lightmap.jpg", 1.214, (11.6, 0.15, -30.75), -90),
    ("lovells-restaurant.glb", "lovells-restaurant-lightmap.jpg", 1.2468, (12.66, 0.15, -52.13), -90),
    ("bank-building.glb", "bank-building-lightmap.jpg", 1.1309, (12.24, 0.15, -66.24), -90),
]
TREES = [(-7.5, 0.175, -24, 90, 1.15, 1.12), (-7.5, 0.175, -33, 180, 1.05, 1.1), (-7.5, 0.175, -60, 270, 1, 1),
         (7.5, 0.175, -44, 0, 1.05, 1.05), (7.5, 0.175, -39.8, 90, 0.92, 0.95), (7.5, 0.175, -35.6, 180, 1.1, 1.08),
         (7.5, 0.175, -31.4, 270, 0.97, 1.0), (-7.5, 0.175, -2.6, 270, 0.85, 0.88), (-7.5, 0.175, -11.5, 0, 0.9, 0.92)]
KIT = "street_details"

scene = bpy.context.scene
objs = list(bpy.data.collections[KIT].objects)
scale = float(objs[0].get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("SD_Preview")
if not pcol:
    pcol = bpy.data.collections.new("SD_Preview")
    scene.collection.children.link(pcol)
pcol.hide_viewport = pcol.hide_render = False
for o in list(pcol.all_objects):
    bpy.data.objects.remove(o, do_unlink=True)
cam_data = bpy.data.cameras.get("SD_Cam") or bpy.data.cameras.new("SD_Cam")
cam = bpy.data.objects.get("SD_Cam") or bpy.data.objects.new("SD_Cam", cam_data)
if cam.name not in pcol.objects:
    pcol.objects.link(cam)
cam_data.clip_start = 0.05
cam_data.clip_end = 900
cam_data.sensor_fit = "HORIZONTAL"
cam_data.sensor_width = 36

lm_img = bpy.data.images.load(LIGHTMAP, check_existing=True)
lm_img.reload()
lm_img.colorspace_settings.name = "sRGB"


def sock(socks, name):
    return next(x for x in socks if x.name == name and x.type == "RGBA")


def preview_material(src, lm_image, lm_scale, lm_uv, uv0_name):
    mat = bpy.data.materials.new("SDP_" + src.name)
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
    nodes = src.node_tree.nodes if src.node_tree else []
    src_tex = next((n for n in nodes if n.type == "TEX_IMAGE" and n.name != "BakeTarget"), None)
    src_tint = next((n for n in nodes if n.type == "MIX" and n.blend_type == "MULTIPLY"), None)
    bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    alpha = None
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
        if bsdf and bsdf.inputs["Alpha"].is_linked:
            alpha = tex.outputs["Alpha"]
    elif bsdf:
        sock(mix.inputs, "A").default_value = bsdf.inputs["Base Color"].default_value
    L(lm.outputs["Color"], sock(mix.inputs, "B"))
    L(sock(mix.outputs, "Result"), emit.inputs["Color"])
    if alpha is not None:
        rnd = N("ShaderNodeMath")
        rnd.operation = "ROUND"
        L(alpha, rnd.inputs[0])
        tr = N("ShaderNodeBsdfTransparent")
        ms = N("ShaderNodeMixShader")
        L(rnd.outputs[0], ms.inputs["Fac"])
        L(tr.outputs[0], ms.inputs[1])
        L(emit.outputs["Emission"], ms.inputs[2])
        L(ms.outputs[0], out.inputs["Surface"])
        try:
            mat.surface_render_method = "DITHERED"
        except (AttributeError, TypeError):
            pass
    else:
        L(emit.outputs["Emission"], out.inputs["Surface"])
    mat.use_backface_culling = src.use_backface_culling
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
    me = bpy.data.meshes.new(name)
    v = [(x, -z, y) for y in (y0, y1) for z in (z0, z1) for x in (x0, x1)]
    me.from_pydata(v, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    pcol.objects.link(o)


# ground as js/ground.js and index.html draw it (flat colours)
sbox("SDP_Disc", -400, 400, -400, 400, -0.05, 0.0, unlit("SDP_DiscMat", (0.15, 0.14, 0.08)))
sbox("SDP_Road", -6.4, 6.4, -200, 80, 0.0, 0.05, unlit("SDP_RoadMat", (0.20, 0.18, 0.15)))
sbox("SDP_BloomRoad", 6.4, 60, -86.5, -79.9, 0.0, 0.01, unlit("SDP_RoadMat", (0.20, 0.18, 0.15)))
walk = unlit("SDP_WalkMat", (0.36, 0.35, 0.32))
grass = unlit("SDP_GrassMat", (0.16, 0.20, 0.09))
sbox("SDP_Lawn", -45, -10.3, -77.4, 0.0, 0.0, 0.015, grass)
sbox("SDP_WalkW", -10.3, -6.4, -200, 0.0, 0.0, 0.15, walk)
sbox("SDP_GrassStrip", -8.0, -6.64, -78.5, -56, 0.0, 0.151, grass)
sbox("SDP_WalkE", 6.4, 10.3, -200, 80, 0.0, 0.15, walk)
sbox("SDP_WalkBN", 6.4, 60, -89.9, -87.7, 0.0, 0.15, walk)
sbox("SDP_VergeBN", 8.5, 30, -87.7, -86.5, 0.0, 0.151, grass)
sbox("SDP_Forecourt", -18.5, -10.3, -13.55, 0.0, 0.0, 0.15, walk)
path = unlit("SDP_PathMat", (0.42, 0.40, 0.36))
for x, z, w, d in ((-12.85, -24.07, 5.1, 1.6), (-12.85, -27.87, 5.1, 1.6), (-12.85, -31.67, 5.1, 1.6),
                   (-12.63, -51.19, 4.75, 1.3), (-12.5, -68.69, 4.5, 1.2)):
    sbox("SDP_Path", x - w / 2, x + w / 2, z - d / 2, z + d / 2, 0.0, 0.03, path)

for glb, lmf, inten, (px, py, pz), rot in CONTEXT:
    _before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=M + glb)
    img = bpy.data.images.load(T + lmf, check_existing=True)
    img.colorspace_settings.name = "sRGB"
    for o in [o for o in bpy.data.objects if o not in _before]:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        pcol.objects.link(o)
        o.name = "SDP_CTX_" + glb[:-4]
        if o.parent is None:
            o.rotation_mode = "XYZ"
            o.location = (px, -pz, py)
            o.rotation_euler = (0, 0, math.radians(rot))
        if o.type == "MESH":
            uvs = [u.name for u in o.data.uv_layers]
            for i, m in enumerate(list(o.data.materials)):
                if len(uvs) > 1 and m.name not in ("glass",):
                    o.data.materials[i] = preview_material(m, img, inten, uvs[1], uvs[0])

# street trees, lit by a preview sun (the scene lights them the same way)
for i, (x, y, z, rot, s, sy) in enumerate(TREES):
    _before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=M + "street-tree.glb")
    for o in [o for o in bpy.data.objects if o not in _before]:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        pcol.objects.link(o)
        if o.parent is None:
            o.location = (x, -z, y)
            o.rotation_euler = (0, 0, math.radians(rot))
            o.scale = (s, s, sy)
sun = bpy.data.objects.new("SDP_Sun", bpy.data.lights.new("SDP_Sun", "SUN"))
pcol.objects.link(sun)
sun.data.energy = 3.0
sun.data.color = (1.0, 0.85, 0.66)
sun.rotation_euler = (-Vector((-0.90, -0.40, 0.36)).normalized()).to_track_quat("-Z", "Y").to_euler()

# --- remember and change settings ----------------------------------------------
FINALS = {}
for o in objs:
    for m in o.data.materials:
        FINALS[m.name] = m
PREVIEW_MATS = {n: preview_material(m, lm_img, scale, "Lightmap", "UVMap") for n, m in FINALS.items()}
originals = {o.name: list(o.data.materials) for o in objs}
saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
render_state = {c.name: c.hide_render for c in bpy.data.collections}
loose_state = {o.name: o.hide_render for o in scene.collection.objects}
for o in scene.collection.objects:
    o.hide_render = True
for o in objs:
    for i, m in enumerate(list(o.data.materials)):
        o.data.materials[i] = PREVIEW_MATS[m.name]
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


# eye 1.6 m above the ground the viewer stands on (walk 0.15, lawn 0.015)
VIEWS = {
    "wurts-fence":      dict(eye=S(-8.1, 1.75, -71.2), target=S(-10.42, 0.75, -68.9), lens=24, h=800),
    "wurts-urn":        dict(eye=S(-8.6, 1.75, -70.4), target=S(-10.42, 1.1, -69.3), lens=35, h=800),
    # flmngtnmainstdrtompkinsoffice.jpg: on the walk, on the axis of the office's path, looking west
    "match-tompkins":   dict(eye=S(-3.3, 1.8, -68.95), target=S(-14.65, 2.65, -68.85), lens=88, h=2002),
    "picket-gate":      dict(eye=S(-8.0, 1.75, -53.6), target=S(-10.44, 0.6, -51.3), lens=24, h=800),
    "stone-post":       dict(eye=S(-8.2, 1.75, -41.4), target=S(-10.45, 0.7, -39.3), lens=26, h=800),
    "pipe-rail":        dict(eye=S(-8.1, 1.75, -30.2), target=S(-11.6, 0.45, -27.9), lens=24, h=800),
    "board-fence":      dict(eye=S(-15.2, 1.615, -15.6), target=S(-17.7, 1.0, -17.0), lens=24, h=800),
    "board-fence-walk": dict(eye=S(-8.5, 1.75, -22.5), target=S(-17.0, 1.0, -17.0), lens=26, h=800),
    "hedge":            dict(eye=S(12.8, 1.75, -87.1), target=S(17.0, 0.55, -89.3), lens=24, h=800),
    "waste-paper-box":  dict(eye=S(7.9, 1.75, -107.6), target=S(9.4, 0.5, -105.5), lens=26, h=800),
    "barber-pole":      dict(eye=S(7.9, 1.75, -40.2), target=S(10.0, 1.05, -38.3), lens=26, h=800),
    "overview-west":    dict(eye=S(-1.0, 2.6, -84.0), target=S(-10.4, 0.6, -60.0), lens=24, h=760),
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS
written = []
try:
    for c in bpy.data.collections:
        c.hide_render = c.name not in (KIT, "SD_Preview")
    for name, v in VIEWS.items():
        eye, target = Vector(v["eye"]), Vector(v["target"])
        cam.location = eye
        cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = v["lens"]
        scene.render.resolution_x, scene.render.resolution_y = 1280, v.get("h", 960)
        scene.render.filepath = PREV + "street-details-" + name + ".png"
        bpy.ops.render.render(write_still=True)
        written.append(scene.render.filepath)
finally:
    for o in objs:
        for i, m in enumerate(originals[o.name]):
            o.data.materials[i] = m
    for m in PREVIEW_MATS.values():
        bpy.data.materials.remove(m)
    for name, state in render_state.items():
        if bpy.data.collections.get(name):
            bpy.data.collections[name].hide_render = state
    for name, state in loose_state.items():
        if bpy.data.objects.get(name):
            bpy.data.objects[name].hide_render = state
    pcol.hide_render = pcol.hide_viewport = True
    bg.inputs[0].default_value, bg.inputs[1].default_value = saved_bg
    scene.camera = saved["camera"] or cam
    scene.render.engine = saved["engine"]
    scene.view_settings.view_transform = saved["vt"]
    scene.view_settings.look = saved["look"]
    scene.render.resolution_x, scene.render.resolution_y = saved["rx"], saved["ry"]
    scene.render.resolution_percentage = saved["pct"]
print("previews written:", *written, sep="\n  ")
