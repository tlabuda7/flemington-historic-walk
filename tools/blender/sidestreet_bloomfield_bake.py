"""
sidestreet_bloomfield_bake.py - materials, baked lighting and export for the Bloomfield Ave
backdrop (assets/models/sidestreet-bloomfield.glb). Same pipeline as sidestreet_court_bake.py.

Run inside Blender:
    exec(open(r"<project>/tools/blender/sidestreet_bloomfield_bake.py").read())
Set SB_MATERIALS_ONLY = True before exec() to stop after step 2 (look at the materials).

 1. Rebuild the geometry (sidestreet_bloomfield.py).
 2. Nine materials, nine 1024 px colour maps (`baked-lighting` merges them into one call):
      clap      house-65-main/clapboard_cream.jpg, tile 1.0 m (paint colours go into the
                lightmap via the Tint attribute, so one material serves every frame house)
      brick     polyhaven/red_brick.jpg, tile 1.4 m, x factor -> #7A4436
      slate     polyhaven/roof_slates_03.jpg, tile 1.5 m (B7's shingles: a brown Tint)
      atlas     shared/backdrop_windows.jpg: windows, doors, plain paint / tin / stone swatches
                (the bakery's and no. 16's plaster, trim, porch roofs, G1's sills, lintels, panel)
      road      ground/road_oiled_earth.jpg: the road with js/ground.js's arm UVs (only the road;
                R-c 2026-11-12 moved the back lots to the two maps below)
      grass     shared/backdrop_grass.jpg, tile 4 m: house yards (as north_approach_bake.py)
      yard      shared/backdrop_earth.jpg, tile 3 m, x factor -> #8C7B62: work yards (as
                back_lots_bake.py)
      concrete  polyhaven/sidewalk_concrete.jpg, tile 3 m (walks, curbs, steps)
      block     shared/backdrop_block_rockfaced.jpg = bank-building/stone_rockfaced.jpg (Poly Haven
                sandstone_blocks_05, grey) re-saved at JPEG q60 to keep the GLB under 1.5 MB; tile
                1.4 m (~0.21 m courses), x factor -> light buff-grey: G1's rock-faced concrete
                block, the house foundations
 3. Join, delete faces nobody can see, unwrap "Lightmap" (fronts and the west walls facing Main
    St weighted up, lots and roofs down), pack.
 4. Bake warm late-afternoon sun + sky into one 2K lightmap with Cycles. Scene axes, so the
    world sun is used directly: Blender to-sun (-0.90, -0.40, 0.36). Bake-only extras (not
    exported): a ground plane, the built Main St neighbours (Rea Building, Bank Building,
    Lovell's, 40-46 Main: their GLBs in "SB_Context" at their index.html places), a box for
    the pass-2 wagon shed A7, and leafy crowns at the proposed backdrop-tree positions (TREES).
 5. Grime mask (dirt band on the bottom 0.8 m, blotches, streaks; lots blotchy) x Tint.
 6. Fill empty pixels, warm the shade, save the sRGB JPEG, print LIGHTMAP_SCALE, export GLB.
"""

import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
TX = PROJECT + r"\assets\textures" + "\\"
GLB = PROJECT + r"\assets\models\sidestreet-bloomfield.glb"
LIGHTMAP = PROJECT + r"\assets\textures\sidestreet-bloomfield-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 256
TO_SUN = (-0.90, -0.40, 0.36)
COLL, RIG, OBJ_NAME = "SidestreetBloomfield", "SB_BakeRig", "SidestreetBloomfield"
CONTEXT = "SB_Context"
TREE_SHADOWS = True
# scene (x, z, scale) of the proposed backdrop-tree instances (TYPICAL-GUESS); crown ~6.6 m x scale
TREES = [(71.0, -96.0, 2.0), (78.5, -93.0, 2.2), (93.8, -92.6, 2.1), (104.9, -92.4, 2.0), (114.9, -93.6, 2.15),
         (133.5, -95.0, 2.25), (45.0, -70.0, 2.2), (65.15, -71.0, 1.9), (95.9, -76.0, 2.1), (107.0, -70.0, 2.0)]

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\sidestreet_bloomfield.py").read())


# 2. Materials ----------------------------------------------------------------
def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


CONC = (112, 112, 107)
LOOK = {   # name: (file, roughness, factor)
    "clap": (TX + r"house-65-main\clapboard_cream.jpg", 0.85, tint((229, 223, 204), (0xE4, 0xDF, 0xD2))),
    "brick": (TX + r"polyhaven\red_brick.jpg", 0.9, tint((142, 103, 80), (0x7A, 0x44, 0x36))),
    "slate": (TX + r"polyhaven\roof_slates_03.jpg", 0.75, None),
    "atlas": (TX + r"shared\backdrop_windows.jpg", 0.85, None),
    "road": (TX + r"ground\road_oiled_earth.jpg", 1.0, None),
    "concrete": (TX + r"polyhaven\sidewalk_concrete.jpg", 0.95, None),
    "block": (TX + r"shared\backdrop_block_rockfaced.jpg", 0.95, tint((168, 162, 148), (0xB6, 0xAE, 0x9A))),
    # R-c 2026-11-12: house yards and work yards (as north_approach_bake.py / back_lots_bake.py)
    "grass": (TX + r"shared\backdrop_grass.jpg", 1.0, (0.80, 0.74, 0.80)),
    "yard": (TX + r"shared\backdrop_earth.jpg", 1.0, tint((146, 131, 104), (0x8C, 0x7B, 0x62))),
}
FINAL_NAMES = {k: "bloom_" + k for k in LOOK}


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

# Paint colours and ground variations, multiplied into the lightmap: (part, material) or part.
PAINT = {"A8R": (0.78, 0.75, 0.68), "A11": (0.93, 0.89, 0.78), "A12": (0.86, 0.87, 0.81),
         "A13": (1.0, 0.95, 0.84), "A13R": (1.0, 0.95, 0.84), "B2": (0.98, 0.98, 0.96),
         "B3": (0.88, 0.92, 0.85), "B4": (1.0, 0.93, 0.76), "B5": (0.90, 0.89, 0.85),
         "B5R": (0.90, 0.89, 0.85), "B7": (0.95, 0.88, 0.74), "B8": (0.64, 0.60, 0.53)}
TINTS = {("Curb", "concrete"): (1.0, 0.98, 0.95), ("Walk", "concrete"): (0.96, 0.95, 0.92),
         ("LotsN", "grass"): (0.98, 0.95, 0.86), ("LotsS", "grass"): (0.98, 0.95, 0.86),
         ("B7", "slate"): (0.88, 0.74, 0.62),
         ("A10", "atlas"): (0.95, 0.92, 0.86)}


def part_tint(part, mat):
    if (part, mat) in TINTS:
        return TINTS[(part, mat)]
    if mat == "clap" and part in PAINT:
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

if globals().get("SB_MATERIALS_ONLY"):
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
    import random
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
    if m == "bloom_road" and n.z > 0.9:
        f *= 0.45                                 # road
    elif m in ("bloom_grass", "bloom_yard") and n.z > 0.9:
        f *= 0.24                                 # huge flat lots (R-c: grass / earth)
    elif m in ("bloom_road", "bloom_grass", "bloom_yard"):
        f *= 0.3                                  # lot skirts
    elif m == "bloom_concrete" and n.z > 0.9 and c.z < 0.2:
        f *= 0.5                                  # walks
    elif m == "bloom_slate" or (n.z > 0.5 and c.z > 3.0):
        f *= 0.55                                 # roofs
    if n.z < -0.5:
        f *= 0.6                                  # soffits, porch ceilings
    if abs(n.z) < 0.5 and (n.x < -0.7 or (n.y < -0.7 and c.y > 89) or (n.y > 0.7 and c.y < 78)):
        f *= 1.3                                  # walls seen from Main St: west sides and street fronts
    if abs(n.z) < 0.5 and c.x > 115:
        f *= 0.8                                  # far end (Opera House, G1)
    if f != 1.0:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.0015, shape_method="CONCAVE")
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
sun = bpy.data.objects.new("SB_Sun", bpy.data.lights.new("SB_Sun", "SUN"))
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


gm = bpy.data.meshes.new("SB_Ground")
gm.from_pydata([(-400, -400, -0.02), (400, -400, -0.02), (400, 400, -0.02), (-400, 400, -0.02)], [], [(0, 1, 2, 3)])
gm.materials.append(rig_mat("SB_GroundMat", (0.20, 0.19, 0.12)))
rig.objects.link(bpy.data.objects.new("SB_Ground", gm))
occ = rig_mat("SB_OccMat", (0.45, 0.42, 0.36))


def rig_box(name, x0, x1, y0, y1, z0, z1):
    m = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0),
                       (z0 + z1) / 2 + v.co.z * (z1 - z0)))
    bm.to_mesh(m)
    bm.free()
    m.materials.append(occ)
    rig.objects.link(bpy.data.objects.new(name, m))


# Main St side (bake context only): the built neighbours are in the SB_Context collection
# (their GLBs at the index.html places); the pass-2 wagon shed A7 (not built yet) as a box
rig_box("SB_OccA7", 36.3, 74.5, 47.5, 55.0, 0.0, 4.2)

if TREE_SHADOWS:
    leaf = bpy.data.materials.get("SB_Leaf") or bpy.data.materials.new("SB_Leaf")
    leaf.use_nodes = True
    nt = leaf.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dif.inputs["Color"].default_value = (0.05, 0.08, 0.03, 1)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.9
    noise.inputs["Detail"].default_value = 4.0
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value, ramp.inputs["From Max"].default_value = 0.42, 0.56
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], mix.inputs["Fac"])      # 0 = transparent hole, 1 = leaves
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(dif.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    for i, (x, z, s) in enumerate(TREES):
        base = G
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(x, -z, base + 7.4 * s))
        cr = bpy.context.active_object
        cr.scale = (3.3 * s, 3.3 * s, 2.9 * s)
        cr.name = "SB_Crown%d" % i
        cr.data.materials.append(leaf)
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.2 * s, depth=4.5 * s,
                                            location=(x, -z, base + 2.25 * s))
        tk = bpy.context.active_object
        tk.name = "SB_Trunk%d" % i
        tk.data.materials.append(occ)
        for o in (cr, tk):
            for c in list(o.users_collection):
                c.objects.unlink(o)
            rig.objects.link(o)

if scene.world is None:
    scene.world = bpy.data.worlds.new("SB_Sky")
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
    light_img = bake_target("SB_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask -------------------------------------------------------------
    grime_mat = bpy.data.materials.get("SB_GrimeBake") or bpy.data.materials.new("SB_GrimeBake")
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
    band = map_range(Z, 0.05, 1.0, 0.80, 1.0)
    height = math_op("ADD", mult(wall, math_op("SUBTRACT", band, 1.0)), 1.0)
    blotch_n = noise_tex(geo.outputs["Position"], 0.35, 6.0)
    blotch = map_range(blotch_n, 0.0, 1.0, 0.86, 1.05)
    stretch = N("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (4.0, 4.0, 0.18)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_n = noise_tex(stretch.outputs["Vector"], 1.7, 2.0)
    streaks = math_op("ADD", mult(wall, math_op("SUBTRACT", map_range(streak_n, 0.35, 0.75, 0.92, 1.0), 1.0)), 1.0)
    # ground: big soft patches (worn grass, damp earth)
    ground = map_range(NZ, 0.8, 0.95, 0.0, 1.0)
    low = map_range(Z, 0.7, 0.6, 0.0, 1.0)
    patch_n = noise_tex(geo.outputs["Position"], 0.08, 3.0)
    patches = math_op("ADD", mult(ground, low, math_op("SUBTRACT", map_range(patch_n, 0.3, 0.7, 0.86, 1.06), 1.0)), 1.0)
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
    grime_img = bake_target("SB_Grime", True)
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
out_img = bpy.data.images.get("SB_Lightmap") or bpy.data.images.new("SB_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
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
# R-c: nine maps; the two lot maps are embedded as re-encoded copies (temp folder, nothing new in
# the project) to stay under 1.8 MB
import os
import tempfile
REENCODE = {"backdrop_grass": 66, "backdrop_earth": 56}
tmpdir = tempfile.mkdtemp(prefix="sidestreet_bloomfield_glb_")
swapped = []
for mat in mesh.materials:
    for node in mat.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image:
            stem = os.path.splitext(os.path.basename(node.image.filepath))[0]
            if stem in REENCODE:
                cp = node.image.copy()
                cp.file_format = "JPEG"
                path = os.path.join(tmpdir, stem + ".jpg")
                cp.save(filepath=path, quality=REENCODE[stem])
                new = bpy.data.images.load(path)
                swapped.append((node, node.image, new, cp))
                node.image = new
try:
    bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True, export_texcoords=True,
                              export_normals=True)
finally:
    for node, orig, new, cp in swapped:
        node.image = orig
        bpy.data.images.remove(new)
        bpy.data.images.remove(cp)
print("GLB size: %.2f MB" % (os.path.getsize(GLB) / 1e6))
tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("exported", GLB, "|", tris, "triangles |", len(mesh.materials), "materials:",
      [m.name for m in mesh.materials])
r_obj["lightmap_scale"] = LIGHTMAP_SCALE
