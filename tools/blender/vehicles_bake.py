"""
vehicles_bake.py - materials, shared lightmap bake and export for the three parked vehicles,
version 2 (PLAN.md, Street details pass 2, F12-F14; geometry: vehicles.py).

Run inside Blender:
    exec(open(r"<project>/tools/blender/vehicles_bake.py").read())

 1. Rebuild the geometry (vehicles.py): objects "model-t", "buggy", "delivery-wagon" with smooth /
    weighted normals and "UVMap" (metres; wagon boards one plank of the texture each).
 2. Materials (plain colours, no lettering, no pinstriping):
      enamel          #141414, roughness 0.30 (Model T body, fenders, hood, wheels, top bows) - the
                      scene may give it a sky environment map, hence the fixed name
      satin_black     #1A1A1A, roughness 0.50 (buggy body, seat box, bows; wagon trim)
      leather         #1E1C1A, roughness 0.55 (seats, buggy dash, straps)
      top_fabric      generated twill weave (assets/textures/vehicles-top-fabric.jpg, 512 px,
                      made here with numpy, no download), tile 0.15 m, tinted to #2A2826, rough 0.85
      rubber          #2C2A28, roughness 0.90 (tyres, floor mat, running-board mats)
      iron            #2E2D2B, roughness 0.60 (springs, axles, steel tyres, straps, chains)
      gear_paint      #3A2B26, roughness 0.50 (dull carriage red-brown: buggy and wagon wheels and
                      running gear, shafts; colour is a guess)
      wagon_wood      polyhaven/weathered_planks.jpg, tile 1.0 m, tinted to #7E705E (wagon boards)
      glass           #1A1916, alpha 0.30 (windshield, lamp lenses) - left alone by the scene
      reflector       #A8A69E (headlamp reflectors), radiator_core #1C1C1A
 3. "Lightmap" UVs: smart project per vehicle, equal texel density across all three, glass and
    downward faces shrunk, packed together into ONE 2K map.
 4. Bake: east-curb street (front faces scene south): to-sun (-0.90, -0.40, 0.36) in this frame
    (scene WSW, 21 deg up), sky (0.42, 0.55, 0.78) x 0.9, road, raised sidewalk and the east
    building fronts as a wall 5 m to +X. Vehicles spread 15 m apart along Y while baking.
 5. Grime / dust: object-space position, normal and material id are baked into the same UVs and
    the mask is computed with numpy: restrained road dust (brightening, warm) on tyres, wheels,
    running gear and lower panels, dust on up-facing low surfaces, blotchy fading, darker door
    lines and hood seams on the Model T, button tufts on the seats. Multiplied into the lighting.
 6. Fill, save assets/textures/vehicles-lightmap.jpg (sRGB), print LIGHTMAP_SCALE, export
    assets/models/vehicles.glb (three root nodes at the origin, TEXCOORD_0 + TEXCOORD_1).
"""
import math
import os
import bpy
import numpy as np
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PH = PROJECT + r"\assets\textures\polyhaven" + "\\"
FABRIC = PROJECT + r"\assets\textures\vehicles-top-fabric.jpg"
GLB = PROJECT + r"\assets\models\vehicles.glb"
LIGHTMAP = PROJECT + r"\assets\textures\vehicles-lightmap.jpg"
BLEND = PROJECT + r"\assets\models\source\vehicles.blend"
SIZE = 2048
SAMPLES = 384
GLASS_ALPHA = 0.30
TO_SUN = (-0.90, -0.40, 0.36)
COLL, RIG = "vehicles", "VEH_BakeRig"
NAMES = ["model-t", "buggy", "delivery-wagon"]
BAKE_POS = {"model-t": (0, 0, 0), "buggy": (0, -15, 0), "delivery-wagon": (0, -30, 0)}
POS_OFFSET = 5.0                     # positions are baked as emission + 5 (kept positive)

# 1. geometry -----------------------------------------------------------------------------
VEHICLES_LIB_ONLY = False
exec(open(PROJECT + r"\tools\blender\vehicles.py", encoding="utf-8").read())
objs = [bpy.data.objects[n] for n in NAMES]


# 2. materials ----------------------------------------------------------------------------
def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexlin(h):
    return tuple(srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def tint(avg, target):
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


def make_fabric_texture(path, n=512):
    """Tileable twill weave with fibre noise and soft blotches (plain dark grey-brown)."""
    if os.path.exists(path):
        return
    rng = np.random.default_rng(1917)
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    p = 8.0                                            # thread period in px
    warp = 0.5 + 0.5 * np.sin(2 * np.pi * x / p)
    weft = 0.5 + 0.5 * np.sin(2 * np.pi * y / p)
    twill = 0.5 + 0.5 * np.sin(2 * np.pi * (x + y) / (2 * p))
    v = 0.52 + 0.10 * (warp * weft - 0.25) + 0.08 * (twill - 0.5)
    v += rng.normal(0, 0.035, (n, n)).astype(np.float32)
    v = np.clip(v, 0, 1)
    img = bpy.data.images.new("VEH_FabricGen", n, n, alpha=False)
    rgba = np.ones((n, n, 4), np.float32)
    rgba[..., 0] = v * 1.02
    rgba[..., 1] = v
    rgba[..., 2] = v * 0.96
    img.pixels.foreach_set(np.clip(rgba, 0, 1).ravel())
    img.filepath_raw = path
    img.file_format = "JPEG"
    img.save()
    bpy.data.images.remove(img)


make_fabric_texture(FABRIC)

# name -> (texture, roughness, plain colour or target sRGB for the texture)
LOOK = {
    "enamel":        (None, 0.30, "141414"),
    "satin_black":   (None, 0.50, "1A1A1A"),
    "leather":       (None, 0.55, "1E1C1A"),
    "top_fabric":    (FABRIC, 0.85, "2A2826"),
    "rubber":        (None, 0.90, "2C2A28"),
    "iron":          (None, 0.60, "2E2D2B"),
    "gear_paint":    (None, 0.50, "3A2B26"),
    "wagon_wood":    (PH + "weathered_planks.jpg", 0.85, "7E705E"),
    "glass":         (None, 0.05, "1A1916"),
    "reflector":     (None, 0.25, "A8A69E"),
    "radiator_core": (None, 0.80, "1C1C1A"),
}


def image_average(path):
    img = bpy.data.images.load(path, check_existing=True)
    px = np.empty(len(img.pixels), np.float32)
    img.pixels.foreach_get(px)
    lin = px.reshape(-1, 4)[:, :3].mean(axis=0)
    return tuple(int(round(255 * ((c * 12.92) if c <= 0.0031308 else (1.055 * c ** (1 / 2.4) - 0.055)))) for c in lin)


def sock(socks, n):
    return next(x for x in socks if x.name == n and x.type == "RGBA")


def make_material(name, image_file, roughness, hexcol):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0
    if image_file:
        avg = image_average(image_file)
        target = tuple(int(hexcol[i:i + 2], 16) for i in (0, 2, 4))
        factor = tint(avg, target)
        print("texture average", name, avg, "-> tint", tuple(round(c, 3) for c in factor))
        uv = nt.nodes.new("ShaderNodeUVMap")
        uv.uv_map = "UVMap"
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(image_file, check_existing=True)
        tex.image.reload()
        nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(tex.outputs["Color"], sock(mix.inputs, "A"))
        sock(mix.inputs, "B").default_value = (*factor, 1.0)
        nt.links.new(sock(mix.outputs, "Result"), bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (*hexlin(hexcol), 1)
    mat.use_backface_culling = True
    if name == "glass":
        bsdf.inputs["Alpha"].default_value = GLASS_ALPHA
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        elif hasattr(mat, "blend_method"):
            mat.blend_method = "BLEND"
    return mat


FINAL = {k: make_material(k, *v) for k, v in LOOK.items()}
MAT_ID = {k: i for i, k in enumerate(LOOK)}


# 3. lightmap UVs ---------------------------------------------------------------------------
def select_only(obs, active):
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for o in bpy.context.view_layer.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = active


for o in objs:
    o.hide_set(False)
    o.hide_viewport = False
    me = o.data
    if "Lightmap" in me.uv_layers:
        me.uv_layers.remove(me.uv_layers["Lightmap"])
    lm = me.uv_layers.new(name="Lightmap")
    me.uv_layers.active = lm
    me.uv_layers["UVMap"].active_render = True
    select_only([o], o)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
select_only(objs, objs[0])
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.average_islands_scale()
bpy.ops.object.mode_set(mode="OBJECT")
for o in objs:
    me = o.data
    lmd = me.uv_layers["Lightmap"].data
    names = [m.name for m in me.materials]
    for p in me.polygons:
        f = None
        if names[p.material_index] in ("glass", "reflector"):
            f = 0.1
        elif p.normal.z < -0.7:
            f = 0.4                          # undersides
        if f:
            for li in p.loop_indices:
                lmd[li].uv = lmd[li].uv * f
select_only(objs, objs[0])
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.0015, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. light rig --------------------------------------------------------------------------------
scene = bpy.context.scene
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
for o in list(rig.objects):
    bpy.data.objects.remove(o, do_unlink=True)
rig.hide_viewport = False
rig.hide_render = False
sun = bpy.data.objects.new("VEH_Sun", bpy.data.lights.get("VEH_Sun") or bpy.data.lights.new("VEH_Sun", "SUN"))
rig.objects.link(sun)
sun.data.energy = 3.2
sun.data.color = (1.0, 0.80, 0.58)
sun.data.angle = math.radians(1.5)
to_sun = Vector(TO_SUN).normalized()
sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()


def rig_mat(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (*rgb, 1)
    return m


def rig_box(name, x0, x1, y0, y1, z0, z1, mat):
    v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    m = bpy.data.meshes.new(name)
    m.from_pydata(v, [], [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)])
    m.materials.append(mat)
    o = bpy.data.objects.new(name, m)
    rig.objects.link(o)
    return o


rig_box("VEH_Road", -60, 60, -80, 60, -0.3, 0.0, rig_mat("VEH_RoadMat", (0.34, 0.28, 0.19)))
rig_box("VEH_Walk", 1.2, 5.0, -80, 60, -0.3, 0.15, rig_mat("VEH_WalkMat", (0.40, 0.38, 0.34)))
rig_box("VEH_Fronts", 5.0, 15.0, -80, 60, 0.0, 10.0, rig_mat("VEH_BrickMat", (0.42, 0.30, 0.24)))

if scene.world is None:
    scene.world = bpy.data.worlds.new("VEH_Sky")
world = scene.world
world.use_nodes = True
bg = next((n for n in world.node_tree.nodes if n.type == "BACKGROUND"), None)
if bg is None:
    bg = world.node_tree.nodes.new("ShaderNodeBackground")
    wout = next((n for n in world.node_tree.nodes if n.type == "OUTPUT_WORLD"), None) \
        or world.node_tree.nodes.new("ShaderNodeOutputWorld")
    world.node_tree.links.new(bg.outputs[0], wout.inputs["Surface"])
bg.inputs[0].default_value = (0.42, 0.55, 0.78, 1)
bg.inputs[1].default_value = 0.9

render_state = {}
for c in bpy.data.collections:
    render_state[c.name] = c.hide_render
    c.hide_render = c.name not in (COLL, RIG)
loose_state = {o.name: o.hide_render for o in scene.collection.objects}
for o in scene.collection.objects:
    o.hide_render = True

try:
    scene.render.engine = "CYCLES"
except TypeError as e:
    print("engine choices:", e)
prefs = bpy.context.preferences.addons["cycles"].preferences
for kind in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = kind
        prefs.get_devices()
        if any(d.type == kind for d in prefs.devices):
            for d in prefs.devices:
                d.use = d.type == kind
            break
    except TypeError:
        pass
scene.cycles.device = "GPU"
scene.cycles.use_denoising = False


def bake_target(name):
    img = bpy.data.images.get(name)
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(name, SIZE, SIZE, alpha=True, float_buffer=True)
    img.generated_color = (0, 0, 0, 0)
    return img


def add_target(mat, img):
    nt = mat.node_tree
    node = nt.nodes.get("BakeTarget") or nt.nodes.new("ShaderNodeTexImage")
    node.name = "BakeTarget"
    node.image = img
    uvn = nt.nodes.get("BakeUV") or nt.nodes.new("ShaderNodeUVMap")
    uvn.name = "BakeUV"
    uvn.uv_map = "Lightmap"
    nt.links.new(uvn.outputs["UV"], node.inputs["Vector"])
    for x in nt.nodes:
        x.select = False
    node.select = True
    nt.nodes.active = node


def info_material(kind, vid, mid, img):
    """Emission-only helper: kind 'pos' (object position + 5), 'nrm' ((n + 1) / 2), 'id'."""
    m = bpy.data.materials.new("VEH_Info_%s_%d_%d" % (kind, vid, mid))
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    em = N("ShaderNodeEmission")
    L(em.outputs["Emission"], out.inputs["Surface"])
    if kind == "id":
        em.inputs["Color"].default_value = ((mid + 0.5) / 16, (vid + 0.5) / 4, 1.0, 1)
    else:
        if kind == "pos":
            tc = N("ShaderNodeTexCoord")
            src = tc.outputs["Object"]
            add = N("ShaderNodeVectorMath")
            add.operation = "ADD"
            add.inputs[1].default_value = (POS_OFFSET,) * 3
        else:
            geo = N("ShaderNodeNewGeometry")
            src = geo.outputs["Normal"]          # world = object (objects are only translated)
            add = N("ShaderNodeVectorMath")
            add.operation = "MULTIPLY_ADD"
            add.inputs[1].default_value = (0.5, 0.5, 0.5)
            add.inputs[2].default_value = (0.5, 0.5, 0.5)
        L(src, add.inputs[0])
        L(add.outputs["Vector"], em.inputs["Color"])
    add_target(m, img)
    return m


for o in objs:
    o.location = BAKE_POS[o.name]
    o.hide_render = False
bpy.context.view_layer.update()
select_only(objs, objs[0])
all_mats = list(FINAL.values())
saved = {o.name: list(o.data.materials) for o in objs}
glass_alpha = next(n for n in FINAL["glass"].node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"]
glass_alpha.default_value = 0.0              # light passes the windshield while baking
info = {}
try:
    light_img = bake_target("VEH_Light")
    for m in all_mats:
        add_target(m, light_img)
    scene.cycles.samples = SAMPLES
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")
    scene.cycles.samples = 4
    for kind in ("pos", "nrm", "id"):
        img = bake_target("VEH_Info_" + kind)
        for vid, o in enumerate(objs):
            for i, m in enumerate(saved[o.name]):
                o.data.materials[i] = info_material(kind, vid, MAT_ID[m.name], img)
        bpy.ops.object.bake(type="EMIT", margin=0, use_clear=True)
        info[kind] = img
        for o in objs:
            for i, m in enumerate(saved[o.name]):
                o.data.materials[i] = m
        print(kind, "baked")
finally:
    for o in objs:
        for i, m in enumerate(saved[o.name]):
            o.data.materials[i] = m
        o.location = (0, 0, 0)
    glass_alpha.default_value = GLASS_ALPHA
    for name, state in render_state.items():
        if bpy.data.collections.get(name):
            bpy.data.collections[name].hide_render = state
    for name, state in loose_state.items():
        if bpy.data.objects.get(name):
            bpy.data.objects[name].hide_render = state
    rig.hide_render = True
    rig.hide_viewport = True
    for m in [m for m in bpy.data.materials if m.name.startswith("VEH_Info_")]:
        bpy.data.materials.remove(m)
    for mat in all_mats:
        for nm in ("BakeTarget", "BakeUV"):
            node = mat.node_tree.nodes.get(nm)
            if node:
                mat.node_tree.nodes.remove(node)


# 5. grime / dust mask (numpy) -----------------------------------------------------------------
def pixels(img):
    a = np.empty(SIZE * SIZE * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(-1, 4)


def value_noise(P, seed=0):
    """Smooth 3D value noise in [0, 1] (trilinear over a hashed integer lattice)."""
    i = np.floor(P).astype(np.int64)
    f = P - i
    f = f * f * (3 - 2 * f)

    def h(ix, iy, iz):
        n = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177
        return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out = out + w * h(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz)
    return out


def fbm(P, oct=3, seed=0):
    s, a, tot = 0, 1.0, 0
    for k in range(oct):
        s = s + a * value_noise(P * (2 ** k), seed + k)
        tot += a
        a *= 0.5
    return s / tot


def pulse(d, w):
    return np.clip(1 - np.abs(d) / w, 0, 1)


light = pixels(light_img)
posi = pixels(info["pos"])
nrmi = pixels(info["nrm"])
idi = pixels(info["id"])
baked = light[:, 3] > 0.5
sel = np.nonzero(baked)[0]
P = posi[sel, :3] - POS_OFFSET
Nn = nrmi[sel, :3] * 2 - 1
mid = np.clip(np.floor(idi[sel, 0] * 16), 0, 15).astype(int)
vid = np.clip(np.floor(idi[sel, 1] * 4), 0, 3).astype(int)
MN = {v: k for k, v in MAT_ID.items()}
mat_name = np.array([MN.get(i, "enamel") for i in range(16)])[mid]
x, y, z = P[:, 0], P[:, 1], P[:, 2]

# dust: rises from the road; blotchy; settles on up-facing surfaces
blot = fbm(P * 3.0, 3, 1)
speck = value_noise(P * 40.0, 7)
low = np.clip(1 - z / 0.95, 0, 1) ** 1.4
DUST = {"rubber": 0.55, "iron": 0.55, "gear_paint": 0.45, "enamel": 0.32, "satin_black": 0.30, "wagon_wood": 0.25,
        "leather": 0.10, "top_fabric": 0.06, "radiator_core": 0.2, "reflector": 0.0, "glass": 0.0}
DUSTCOL = {"rubber": (2.3, 2.05, 1.7), "iron": (2.0, 1.8, 1.5), "gear_paint": (1.45, 1.38, 1.22),
           "enamel": (2.4, 2.15, 1.8), "satin_black": (2.2, 2.0, 1.7), "wagon_wood": (1.18, 1.14, 1.06),
           "leather": (1.6, 1.5, 1.35), "top_fabric": (1.5, 1.42, 1.3), "radiator_core": (1.5, 1.4, 1.25),
           "reflector": (1, 1, 1), "glass": (1, 1, 1)}
amt = np.zeros(len(sel), np.float32)
col = np.ones((len(sel), 3), np.float32)
for name in DUST:
    m = mat_name == name
    if not m.any():
        continue
    a = DUST[name] * low[m] * (0.45 + 0.9 * blot[m])
    if name == "rubber":
        a = 0.30 + 0.25 * low[m] + 0.15 * blot[m]          # tyres pick dust up all round
    a = a + DUST[name] * 0.5 * np.clip(Nn[m, 2], 0, 1) * np.clip(1 - z[m] / 1.3, 0, 1)
    amt[m] = np.clip(a, 0, 1)
    col[m] = np.array(DUSTCOL[name], np.float32)
grime = 1 + (col - 1) * amt[:, None]
dark = 0.90 + 0.10 * blot                                  # blotchy fading / old grime
dark *= 0.97 + 0.03 * speck

# Model T: door lines and hood seams (enamel)
t_en = (vid == 0) & (mat_name == "enamel")
side = np.abs(x) > 0.50
door = np.zeros(len(sel), np.float32)
for yy in (0.60, 1.08):
    door = np.maximum(door, pulse(y - yy, 0.006) * side * (z > 0.58) * (z < 1.05))
for yy in (-0.38, 0.14):
    door = np.maximum(door, pulse(y - yy, 0.006) * (x < -0.50) * (z > 0.58) * (z < 1.05))
hood = (y > -1.54) & (y < -0.86)
seams = pulse(y + 0.88, 0.006) * (np.abs(x) < 0.27) * (z > 0.64)
seams = np.maximum(seams, pulse(x, 0.005) * hood * (z > 1.10))
zs = 1.05 + 0.02 * (y + 1.535) / 0.655
seams = np.maximum(seams, pulse(z - zs, 0.005) * hood * (np.abs(x) > 0.18))
lines = np.maximum(door, seams) * t_en
dark *= 1 - 0.55 * lines

# button tufts (diamond pattern) on the seats
seat = (mat_name == "leather") & ~((vid == 1) & (y < -0.65))
flat = np.abs(Nn[:, 2]) > 0.6
a2 = np.where(flat, y, z)
u = (x + a2) / 0.11
v = (x - a2) / 0.11
du = u - np.round(u)
dv = v - np.round(v)
tuft = np.exp(-((du ** 2 + dv ** 2) / 0.012))
dark *= 1 - 0.40 * tuft * seat

grime = grime * dark[:, None]

combined = light[:, :3].copy()
combined[sel] *= grime
lum = combined.mean(axis=1, keepdims=True)
combined = combined * 0.8 + lum * np.array([[1.0, 0.96, 0.88]]) * 0.2
scale = float(np.percentile(combined[baked].max(axis=1), 99.5))
img2 = combined.reshape(SIZE, SIZE, 3).copy()
filled = baked.reshape(SIZE, SIZE).copy()
for _ in range(96):
    if filled.all():
        break
    acc = np.zeros_like(img2)
    cnt = np.zeros(filled.shape, np.float32)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        f = np.roll(filled, (dy, dx), axis=(0, 1))
        acc += np.roll(img2, (dy, dx), axis=(0, 1)) * f[..., None]
        cnt += f
    grow = (~filled) & (cnt > 0)
    img2[grow] = acc[grow] / cnt[grow][:, None]
    filled |= grow
encoded = np.clip(img2.reshape(-1, 3) / scale, 0, 1) ** (1 / 2.2)
rgba = np.ones((SIZE * SIZE, 4), np.float32)
rgba[:, :3] = encoded
out_img = bpy.data.images.get("VEH_Lightmap") or bpy.data.images.new("VEH_Lightmap", SIZE, SIZE)
out_img.scale(SIZE, SIZE)
out_img.colorspace_settings.name = "Non-Color"
out_img.pixels.foreach_set(rgba.ravel())
out_img.filepath_raw = LIGHTMAP
out_img.file_format = "JPEG"
scene.render.image_settings.quality = 88
out_img.save()
LIGHTMAP_SCALE = round(scale, 4)
print("lightmap coverage: %.1f%% of pixels baked" % (100 * baked.mean()))
print("LIGHTMAP_SCALE =", LIGHTMAP_SCALE)

for img in [light_img] + list(info.values()):
    bpy.data.images.remove(img)

select_only(objs, objs[0])
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True, export_apply=False,
                          export_yup=True, export_texcoords=True, export_normals=True,
                          export_tangents=False, export_attributes=False, export_animations=False,
                          export_skins=False, export_morph=False)
for o in objs:
    o["lightmap_scale"] = LIGHTMAP_SCALE
    print(o.name, "tris", sum(len(p.vertices) - 2 for p in o.data.polygons))
print("GLB", GLB, os.path.getsize(GLB), "bytes; lightmap", os.path.getsize(LIGHTMAP), "bytes")
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
