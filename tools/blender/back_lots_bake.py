"""
back_lots_bake.py - materials, baked lighting and export for the back-lot buildings
(assets/models/back-lots.glb; PLAN.md "Street details pass 2", section 5 list A, build split D).
Same pipeline as sidestreet_southeast_bake.py.

Run inside Blender:
    exec(open(r"<project>/tools/blender/back_lots_bake.py").read())
Set BL_MATERIALS_ONLY = True before exec() to stop after step 2 (look at the materials).

 1. Rebuild the geometry (back_lots.py).
 2. Six materials, six 1024 px colour maps (`baked-lighting` merges them into one draw call):
      boards    wurts-law-office/planks_grey.jpg (Poly Haven weathered_planks, greyed), tile 1.6 m:
                weathered vertical boards of the barn, sheds, blacksmith and wagon-shed ends
      clap      house-65-main/clapboard_cream.jpg, tile 1.0 m (the harness shop; paint by Tint)
      brick     polyhaven/red_brick.jpg, tile 1.4 m, x factor -> #7A4436
      tin       county-offices/roof_tin_redbrown.jpg, tile 2.0 m, dulled: all roofs and hoods
      atlas     shared/backdrop_windows.jpg: windows, doors, trim / stone swatches
      earth     shared/backdrop_earth.jpg (= polyhaven/gravel_ground_01.jpg at JPEG q70), tile 3 m, x factor -> js/ground.js's EARTH
                #8c7b62: the pads under A1-A3 that continue the earth lanes
 3. Join, delete faces nobody can see, unwrap "Lightmap" (walls seen from Main St weighted up,
    roofs and pads down), pack.
 4. Bake warm late-afternoon sun + sky into one 2K lightmap with Cycles. Scene axes, so the
    world sun is used directly: Blender to-sun (-0.90, -0.40, 0.36). Bake-only shadow casters
    (never exported): a ground plane and the placed neighbours (Main St GLBs and the Bloomfield,
    south-east and street-end backdrops) in "BL_Context" at their index.html transforms
    (back_lots_context.py). Every other collection is hidden from render during the bake.
 5. Grime mask (dirt band on the bottom 0.8 m, blotches, streaks; pads blotchy) x Tint.
 6. Fill empty pixels, warm the shade, save the sRGB JPEG, print LIGHTMAP_SCALE, export GLB.
"""

import math
import random
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
TX = PROJECT + r"\assets\textures" + "\\"
GLB = PROJECT + r"\assets\models\back-lots.glb"
LIGHTMAP = PROJECT + r"\assets\textures\back-lots-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 256
TO_SUN = (-0.90, -0.40, 0.36)
COLL, RIG, OBJ_NAME = "BackLots", "BL_BakeRig", "BackLots"
CONTEXT = "BL_Context"

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\back_lots.py").read())


# 2. Materials ----------------------------------------------------------------
def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


LOOK = {   # name: (file, roughness, factor)
    "boards": (TX + r"wurts-law-office\planks_grey.jpg", 0.9, (0.93, 0.90, 0.85)),
    "clap": (TX + r"house-65-main\clapboard_cream.jpg", 0.85, tint((229, 223, 204), (0xE4, 0xDF, 0xD2))),
    "brick": (TX + r"polyhaven\red_brick.jpg", 0.9, tint((142, 103, 80), (0x7A, 0x44, 0x36))),
    "tin": (TX + r"county-offices\roof_tin_redbrown.jpg", 0.7, (0.80, 0.78, 0.78)),
    "atlas": (TX + r"shared\backdrop_windows.jpg", 0.85, None),
    "earth": (TX + r"shared\backdrop_earth.jpg", 1.0, tint((146, 131, 104), (0x8C, 0x7B, 0x62))),
}
FINAL_NAMES = {k: "bl_" + k for k in LOOK}


def textured_material(name, image_file, roughness, factor):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = roughness
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(image_file, check_existing=True)
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    if factor:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        sock = lambda socks, n: next(x for x in socks if x.name == n and x.type == "RGBA")
        nt.links.new(tex.outputs["Color"], sock(mix.inputs, "A"))
        sock(mix.inputs, "B").default_value = (*factor, 1.0)
        nt.links.new(sock(mix.outputs, "Result"), bsdf.inputs["Base Color"])
    else:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


FINAL = {k: textured_material(FINAL_NAMES[k], *LOOK[k]) for k in LOOK}

# Weathering / paint per building, multiplied into the lightmap: (part, material) or part.
PAINT = {"A1": (0.86, 0.84, 0.80), "A3": (0.98, 0.96, 0.92), "A5": (0.95, 0.92, 0.88),
         "A7": (0.92, 0.90, 0.86), "A6": (0.94, 0.92, 0.84)}
TINTS = {("A2", "tin"): (0.85, 0.85, 0.85), ("A2W", "tin"): (0.85, 0.85, 0.85),
         ("A4", "tin"): (0.85, 0.85, 0.85), ("A1", "tin"): (0.88, 0.86, 0.84),
         ("PadA1", "earth"): (1.0, 0.98, 0.95)}


def part_tint(part, mat):
    if (part, mat) in TINTS:
        return TINTS[(part, mat)]
    if mat in ("boards", "clap") and part in PAINT:
        return PAINT[part]
    return (1.0, 1.0, 1.0)


def add_tint(obj, rgb):
    attr = obj.data.color_attributes.new("Tint", "FLOAT_COLOR", "CORNER")
    attr.data.foreach_set("color", np.tile(np.array([*rgb, 1.0], dtype=np.float32), len(obj.data.loops)))


parts = [o for o in bpy.data.collections[COLL].objects if o.type == "MESH"]
for obj in parts:
    obj.data.materials.clear()
    obj.data.materials.append(FINAL[obj["mat"]])
    add_tint(obj, part_tint(obj["part"], obj["mat"]))

if globals().get("BL_MATERIALS_ONLY"):
    raise RuntimeError("materials only: stopped before the join")

# 3. Join, drop hidden faces, unwrap the lightmap UVs --------------------------
r_obj = parts[0]
with bpy.context.temp_override(active_object=r_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
old = bpy.data.objects.get(OBJ_NAME)
if old and old != r_obj:
    bpy.data.objects.remove(old, do_unlink=True)
r_obj.name = r_obj.data.name = OBJ_NAME
mesh = r_obj.data
slots, remap = {}, []
for m in mesh.materials:
    if m.name not in slots:
        slots[m.name] = len(slots)
    remap.append(slots[m.name])
mi = np.empty(len(mesh.polygons), dtype=np.int32)
mesh.polygons.foreach_get("material_index", mi)
mi = np.array(remap, dtype=np.int32)[mi]
order = sorted(slots, key=slots.get)
mesh.materials.clear()
for name in order:
    mesh.materials.append(bpy.data.materials[name])
mesh.polygons.foreach_set("material_index", mi)


def fibonacci(n):
    pts = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        a = i * math.pi * (3 - math.sqrt(5))
        pts.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    return pts


def face_samples(f, tris, rng):
    area = f.calc_area()
    n = int(min(600, max(6, area / 0.01)))
    pts = [f.calc_center_median()]
    areas = [((t[1].vert.co - t[0].vert.co).cross(t[2].vert.co - t[0].vert.co)).length / 2 for t in tris]
    total = sum(areas) or 1.0
    for t, a in zip(tris, areas):
        for _ in range(max(1, round(n * a / total))):
            r1, r2 = rng.random(), rng.random()
            if r1 + r2 > 1:
                r1, r2 = 1 - r1, 1 - r2
            p0, p1, p2 = (l.vert.co for l in t)
            pts.append(p0 + (p1 - p0) * r1 + (p2 - p0) * r2)
    c = pts[0]
    out = []
    for p in pts:
        v = c - p
        d = v.length
        out.append(p + v * (min(0.008, 0.25 * d) / d) if d > 1e-6 else p)
    return out


def remove_hidden_faces(obj, rays=120):
    rng = random.Random(7)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    bm.verts.index_update()
    bvh = BVHTree.FromPolygons([v.co for v in bm.verts], [[v.index for v in f.verts] for f in bm.faces])
    dirs = fibonacci(rays)
    face_tris = {}
    for t in bm.calc_loop_triangles():
        face_tris.setdefault(t[0].face, []).append(t)
    dead = []
    for f in bm.faces:
        n = f.normal
        c = f.calc_center_median()
        if n.z < -0.9 and c.z < 0.02:
            dead.append(f)
            continue
        hemi = [d for d in dirs if d.dot(n) > 0.04]
        seen = False
        for p in face_samples(f, face_tris.get(f, []), rng):
            o = p + n * 0.003
            for d in hemi:
                if bvh.ray_cast(o, d, 1.0e4)[0] is None:
                    seen = True
                    break
            if seen:
                break
        if not seen:
            dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    return len(dead)


before = sum(len(p.vertices) - 2 for p in mesh.polygons)
removed = remove_hidden_faces(r_obj)
after = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("hidden faces removed:", removed, "| triangles", before, "->", after)

lm = mesh.uv_layers.new(name="Lightmap")
mesh.uv_layers.active = lm
mesh.uv_layers["UVMap"].active_render = True
for o in bpy.context.view_layer.objects:
    o.select_set(o == r_obj)
bpy.context.view_layer.objects.active = r_obj
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.002,
                         area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.object.mode_set(mode="OBJECT")
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    f = 1.0
    c, n = p.center, p.normal
    m = mat_names[p.material_index]
    if m == "bl_earth":
        f *= 0.35                                 # pads
    elif m == "bl_tin" and n.z > 0.5:
        f *= 0.6                                  # roofs
    if n.z < -0.5:
        f *= 0.6                                  # soffits, eave undersides
    if abs(n.z) < 0.5 and (n.x < -0.7 or n.y < -0.7):
        f *= 1.35                                 # west and south walls: the ones seen from Main St
    if f != 1.0:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.002, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig ------------------------------------------------------------------
scene = bpy.context.scene
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
for o in list(rig.objects):
    bpy.data.objects.remove(o, do_unlink=True)
rig.hide_viewport = False
rig.hide_render = False
sun = bpy.data.objects.new("BL_Sun", bpy.data.lights.new("BL_Sun", "SUN"))
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


gm = bpy.data.meshes.new("BL_Ground")
gm.from_pydata([(-400, -400, -0.02), (400, -400, -0.02), (400, 400, -0.02), (-400, 400, -0.02)], [], [(0, 1, 2, 3)])
gm.materials.append(rig_mat("BL_GroundMat", (0.20, 0.19, 0.12)))
rig.objects.link(bpy.data.objects.new("BL_Ground", gm))

# neighbours (shadow casters), re-imported at their index.html places on every run
exec(open(PROJECT + r"\tools\blender\back_lots_context.py").read())
bpy.data.collections[CONTEXT].hide_viewport = False

if scene.world is None:
    scene.world = bpy.data.worlds.new("BL_Sky")
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
    c.hide_render = c.name not in (COLL, RIG, CONTEXT)
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
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = False
scene.cycles.transparent_max_bounces = 16
print("Cycles device:", prefs.compute_device_type, [d.name for d in prefs.devices if d.use])


def bake_target(name, float_buffer):
    img = bpy.data.images.get(name)
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(name, LIGHTMAP_SIZE, LIGHTMAP_SIZE, alpha=True, float_buffer=float_buffer)
    img.generated_color = (0, 0, 0, 0)
    return img


def point_materials_at(img):
    for mat in mesh.materials:
        nt = mat.node_tree
        node = nt.nodes.get("BakeTarget") or nt.nodes.new("ShaderNodeTexImage")
        node.name = "BakeTarget"
        node.image = img
        uvn = nt.nodes.get("BakeUV") or nt.nodes.new("ShaderNodeUVMap")
        uvn.name = "BakeUV"
        uvn.uv_map = "Lightmap"
        nt.links.new(uvn.outputs["UV"], node.inputs["Vector"])
        nt.nodes.active = node


for o in bpy.context.view_layer.objects:
    o.select_set(o == r_obj)
bpy.context.view_layer.objects.active = r_obj
try:
    light_img = bake_target("BL_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask -------------------------------------------------------------
    grime_mat = bpy.data.materials.get("BL_GrimeBake") or bpy.data.materials.new("BL_GrimeBake")
    grime_mat.use_nodes = True
    nt = grime_mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    emit = N("ShaderNodeEmission")
    geo = N("ShaderNodeNewGeometry")
    sep = N("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs["Vector"])
    nsep = N("ShaderNodeSeparateXYZ")
    L(geo.outputs["Normal"], nsep.inputs["Vector"])
    Z = sep.outputs["Z"]
    NZ = nsep.outputs["Z"]

    def map_range(value_socket, a, b, c, d):
        m = N("ShaderNodeMapRange")
        m.inputs["From Min"].default_value, m.inputs["From Max"].default_value = a, b
        m.inputs["To Min"].default_value, m.inputs["To Max"].default_value = c, d
        L(value_socket, m.inputs["Value"])
        return m.outputs["Result"]

    def math_op(op, a, b=None):
        m = N("ShaderNodeMath")
        m.operation = op
        for i, s in enumerate((a, b)):
            if s is None:
                continue
            if isinstance(s, (int, float)):
                m.inputs[i].default_value = s
            else:
                L(s, m.inputs[i])
        return m.outputs["Value"]

    def mult(*socks):
        r = socks[0]
        for s in socks[1:]:
            r = math_op("MULTIPLY", r, s)
        return r

    def noise_tex(vec, scale, detail):
        t = N("ShaderNodeTexNoise")
        t.inputs["Scale"].default_value = scale
        t.inputs["Detail"].default_value = detail
        L(vec, t.inputs["Vector"])
        return t.outputs["Fac"]

    wall = map_range(math_op("ABSOLUTE", NZ), 0.5, 0.3, 0.0, 1.0)            # 1 on walls
    # dirt band and splash on the bottom of the walls, fading by 1 m
    band = map_range(Z, 0.05, 1.0, 0.78, 1.0)
    height = math_op("ADD", mult(wall, math_op("SUBTRACT", band, 1.0)), 1.0)
    blotch_n = noise_tex(geo.outputs["Position"], 0.35, 6.0)
    blotch = map_range(blotch_n, 0.0, 1.0, 0.85, 1.05)
    stretch = N("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (4.0, 4.0, 0.18)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_n = noise_tex(stretch.outputs["Vector"], 1.7, 2.0)
    streaks = math_op("ADD", mult(wall, math_op("SUBTRACT", map_range(streak_n, 0.35, 0.75, 0.90, 1.0), 1.0)), 1.0)
    # ground: big soft patches (damp earth, worn tracks)
    ground = map_range(NZ, 0.8, 0.95, 0.0, 1.0)
    low = map_range(Z, 0.7, 0.6, 0.0, 1.0)
    patch_n = noise_tex(geo.outputs["Position"], 0.12, 3.0)
    patches = math_op("ADD", mult(ground, low, math_op("SUBTRACT", map_range(patch_n, 0.3, 0.7, 0.84, 1.06), 1.0)), 1.0)
    grey = mult(height, blotch, streaks, patches)
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    attr = N("ShaderNodeAttribute")
    attr.attribute_name = "Tint"
    vm = N("ShaderNodeVectorMath")
    vm.operation = "MULTIPLY"
    L(gc.outputs["Vector"], vm.inputs[0])
    L(attr.outputs["Color"], vm.inputs[1])
    L(vm.outputs["Vector"], emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    grime_img = bake_target("BL_Grime", True)
    target = N("ShaderNodeTexImage")
    target.image = grime_img
    target_uv = N("ShaderNodeUVMap")
    target_uv.uv_map = "Lightmap"
    L(target_uv.outputs["UV"], target.inputs["Vector"])
    nt.nodes.active = target
    saved = list(mesh.materials)
    for i in range(len(mesh.materials)):
        mesh.materials[i] = grime_mat
    bpy.ops.object.bake(type="EMIT", margin=0, use_clear=True)
    for i, mat in enumerate(saved):
        mesh.materials[i] = mat
    print("grime baked")
finally:
    for name, state in render_state.items():
        if bpy.data.collections.get(name):
            bpy.data.collections[name].hide_render = state
    for name, state in loose_state.items():
        if bpy.data.objects.get(name):
            bpy.data.objects[name].hide_render = state
    rig.hide_render = True
    rig.hide_viewport = True
    bpy.data.collections[CONTEXT].hide_render = True
    bpy.data.collections[CONTEXT].hide_viewport = True

# 6. Combine, normalise, save ---------------------------------------------------
px = LIGHTMAP_SIZE * LIGHTMAP_SIZE
light = np.empty(px * 4, dtype=np.float32)
grime = np.empty(px * 4, dtype=np.float32)
light_img.pixels.foreach_get(light)
grime_img.pixels.foreach_get(grime)
light = light.reshape(-1, 4)
grime = grime.reshape(-1, 4)
baked = light[:, 3] > 0.5
combined = light[:, :3] * np.where(baked[:, None], grime[:, :3], 1.0)
lum = combined.mean(axis=1, keepdims=True)
ref = np.percentile(lum[baked], 99.0)
shade = np.clip(1.0 - lum / (0.9 * ref), 0.0, 1.0)
w = 0.12 + 0.63 * shade
combined = combined * (1 - w) + lum * np.array([[1.0, 0.94, 0.80]]) * w
scale = float(np.percentile(combined[baked].max(axis=1), 99.5))
img2 = combined.reshape(LIGHTMAP_SIZE, LIGHTMAP_SIZE, 3).copy()
filled = baked.reshape(LIGHTMAP_SIZE, LIGHTMAP_SIZE).copy()
for _ in range(160):
    if filled.all():
        break
    acc = np.zeros_like(img2)
    cnt = np.zeros(filled.shape, dtype=np.float32)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        f = np.roll(filled, (dy, dx), axis=(0, 1))
        acc += np.roll(img2, (dy, dx), axis=(0, 1)) * f[..., None]
        cnt += f
    grow = (~filled) & (cnt > 0)
    img2[grow] = acc[grow] / cnt[grow][:, None]
    filled |= grow
combined = img2.reshape(-1, 3)
encoded = np.clip(combined / scale, 0, 1) ** (1 / 2.2)
rgba = np.ones((px, 4), dtype=np.float32)
rgba[:, :3] = encoded
out_img = bpy.data.images.get("BL_Lightmap") or bpy.data.images.new("BL_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
out_img.scale(LIGHTMAP_SIZE, LIGHTMAP_SIZE)
out_img.colorspace_settings.name = "Non-Color"
out_img.pixels.foreach_set(rgba.ravel())
out_img.filepath_raw = LIGHTMAP
out_img.file_format = "JPEG"
scene.render.image_settings.quality = 88
out_img.save()
LIGHTMAP_SCALE = round(scale, 4)
print("lightmap coverage: %.1f%% of pixels baked" % (100 * baked.mean()))
print("LIGHTMAP_SCALE =", LIGHTMAP_SCALE)

for mat in mesh.materials:
    for name in ("BakeTarget", "BakeUV"):
        node = mat.node_tree.nodes.get(name)
        if node:
            mat.node_tree.nodes.remove(node)
if mesh.color_attributes.get("Tint"):
    mesh.color_attributes.remove(mesh.color_attributes["Tint"])

# 7. Export ---------------------------------------------------------------------
for o in bpy.context.scene.objects:
    o.select_set(o == r_obj)
bpy.context.view_layer.objects.active = r_obj
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_texcoords=True,
                          export_normals=True)
tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("exported", GLB, "|", tris, "triangles |", len(mesh.materials), "materials:",
      [m.name for m in mesh.materials])
r_obj["lightmap_scale"] = LIGHTMAP_SCALE
