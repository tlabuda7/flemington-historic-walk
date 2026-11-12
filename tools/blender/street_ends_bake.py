"""
street_ends_bake.py - materials, baked lighting and export for the street ends
(assets/models/street-ends.glb: E1-E11 north and south of the walkable stretch, with their
ground). Same pipeline as sidestreet_court_bake.py / sidestreet_bloomfield_bake.py /
sidestreet_southeast_bake.py.

Run inside Blender:
    exec(open(r"<project>/tools/blender/street_ends_bake.py", encoding="utf8").read())
Set EN_MATERIALS_ONLY = True before exec() to stop after step 2 (look at the materials).

 1. Rebuild the geometry (street_ends.py).
 2. Nine materials (`baked-lighting` merges them into one draw call):
      clap      house-65-main/clapboard_cream.jpg, tile 1.0 m (paint colours via the Tint attribute
                into the lightmap)
      brick     polyhaven/red_brick.jpg, tile 1.4 m, x factor -> #7A4436 (hotel, Vosseller, library,
                Deats Building; per-building shade via Tint)
      slate     polyhaven/roof_slates_03.jpg, tile 1.5 m (church and dwelling roofs)
      block     shared/backdrop_block_rockfaced.jpg, tile 2.0 m: the two stone churches (Methodist warm
                buff-grey, Presbyterian dark grey, by Tint)
      atlas     shared/backdrop_windows.jpg: windows, doors, railings, paint / tin / stone / iron
                swatches (porches, cornices, the Doric House portico, the monument)
      road      ground/road_oiled_earth.jpg with js/ground.js's Main St UVs (u = (x - crown) / 6.4,
                v = z / 6.4) so the road continues the scene's road; side-street arms as js/ground.js
      concrete  polyhaven/sidewalk_concrete.jpg, tile 3 m (walks, curbs, steps)
      grass     shared/backdrop_grass.jpg, tile 4 m (lots, lawns, the monument plot)
      earth     ground/ground_detail.jpg x js/ground.js's EARTH #8c7b62, tile 2 m (trodden lots)
 3. Join, delete faces nobody can see, unwrap "Lightmap" (street fronts weighted up, roofs and
    far ground down), pack.
 4. Bake warm late-afternoon sun + sky into one 2K lightmap with Cycles. Scene axes, so the world
    sun is used directly: Blender to-sun (-0.90, -0.40, 0.36). Bake-only extras (not exported): a
    ground plane, the built neighbours at the two ends (27 Main, 24-30 Main, 100-102 and 106 Main,
    the south-east backdrop) at their index.html places, and leafy crowns at the proposed
    backdrop-tree positions (TREES).
 5. Grime mask (dirt band on the bottom 0.8 m, blotches, streaks; lots blotchy) x Tint.
 6. Fill empty pixels, warm the shade, save the sRGB JPEG, print LIGHTMAP_SCALE, export GLB
    (road, slate, brick and grass maps embedded as re-encoded copies and ground_detail at 1024 px,
    made in a temp folder at export time, to stay under 1.5 MB and in one merged draw call).
"""

import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
TX = PROJECT + r"\assets\textures" + "\\"
GLB = PROJECT + r"\assets\models\street-ends.glb"
LIGHTMAP = PROJECT + r"\assets\textures\street-ends-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 256
TO_SUN = (-0.90, -0.40, 0.36)
COLL, RIG, OBJ_NAME = "StreetEnds", "EN_BakeRig", "StreetEnds"
CONTEXT = "EN_Context"
TREE_SHADOWS = True
# scene (x, z, scale, y) of the proposed backdrop-tree instances (PHOTO where noted, else
# TYPICAL-GUESS); crown ~6.6 m x scale
TREES = [(-7.6, -173.5, 2.0, 0.15),   # big trees on the walk in front of the hotel (1908 cards)
         (-7.6, -187.0, 2.1, 0.15),
         (10.0, -262.0, 2.1, 0.15),   # east side, south of the fork
         (-14.0, -300.0, 2.3, 0.15),  # big trees round the monument (1910 colour card, rear views)
         (-14.0, -322.0, 2.2, 0.15),
         (40.0, -326.0, 2.2, 0.15),   # corner of Branch St and Pennsylvania Ave
         (14.0, -337.5, 2.3, 0.15),   # church lawn (1923 card: tall trees)
         (0.0, -378.0, 2.2, 0.15),    # west of the church
         (-10.8, 70.0, 2.2, 0.15),    # west side lawns: double row of big trees (1907 card)
         (-10.8, 89.0, 2.3, 0.15),
         (-10.8, 108.0, 2.2, 0.15),
         (-10.8, 127.0, 2.3, 0.15),
         (-10.8, 146.0, 2.2, 0.15),
         (12.6, 112.0, 1.4, 0.15),    # young tree on the church lawn (1909 card)
         (40.0, 98.0, 2.2, 0.15),     # behind the Doric House
         (40.0, 145.0, 2.1, 0.15),    # behind the library
         (16.0, 182.0, 2.3, 0.15),    # beyond the Deats Building, closing the view south
         (24.0, 196.0, 2.2, 0.15)]
# 2026-11-12: the north approach's mature maples (old-maple.glb, real size; the same list as
# north_approach_bake.py TREES), so their shade falls on the road here too
TREES += [(-11.3, -206.0, 0.95, 0.15, "maple"), (-11.3, -224.0, 1.0, 0.15, "maple"),
          (-11.3, -241.0, 0.9, 0.15, "maple"), (-11.3, -258.0, 1.0, 0.15, "maple"),
          (-11.3, -276.0, 0.95, 0.15, "maple"), (-11.3, -291.0, 1.0, 0.15, "maple"),
          (7.0, -198.0, 1.0, 0.15, "maple"), (7.0, -214.0, 0.95, 0.15, "maple"),
          (7.0, -230.0, 1.0, 0.15, "maple"), (7.0, -246.0, 0.9, 0.15, "maple"),
          (12.4, -275.0, 1.0, 0.15, "maple"), (20.0, -291.5, 0.95, 0.15, "maple"),
          (-20.0, -300.0, 1.05, 0.15, "maple"), (-22.0, -286.0, 1.05, 0.15, "maple")]
# neighbours for the bake (GLB, index.html position, rotation y); the south-east backdrop and the
# north approach are in scene axes already
NEIGHBOURS = [("store-27.glb", (-10.30, 0.15, -158.49), 90), ("block-24-30.glb", (7.29, 0.15, -152.365), -90),
              ("store-100-102.glb", (10.30, 0.15, 52.01), -90), ("store-106.glb", (8.06, 0.15, 58.80), -90),
              ("sidestreet-southeast.glb", (0.0, 0.0, 0.0), 0), ("north-approach.glb", (0.0, 0.0, 0.0), 0)]

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\street_ends.py", encoding="utf8").read())


# 2. Materials ----------------------------------------------------------------
def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


LOOK = {   # name: (file, roughness, factor)
    "clap": (TX + r"house-65-main\clapboard_cream.jpg", 0.85, tint((229, 223, 204), (0xE4, 0xDF, 0xD2))),
    "brick": (TX + r"polyhaven\red_brick.jpg", 0.9, tint((142, 103, 80), (0x7A, 0x44, 0x36))),
    "slate": (TX + r"polyhaven\roof_slates_03.jpg", 0.75, None),
    "block": (TX + r"shared\backdrop_block_rockfaced.jpg", 0.95, None),
    "atlas": (TX + r"shared\backdrop_windows.jpg", 0.85, None),
    "road": (TX + r"ground\road_oiled_earth.jpg", 1.0, None),
    "concrete": (TX + r"polyhaven\sidewalk_concrete.jpg", 0.95, None),
    "grass": (TX + r"shared\backdrop_grass.jpg", 1.0, (0.80, 0.74, 0.80)),
    "earth": (TX + r"ground\ground_detail.jpg", 1.0, tint((201, 201, 201), (0x8C, 0x7B, 0x62))),
}
FINAL_NAMES = {k: "en_" + k for k in LOOK}


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

# Paint colours, stone and brick shades and ground variations, multiplied into the lightmap:
# (part, material) or part (any material).
STONE = (168, 162, 148)                                       # average of the rock-faced block map
METH = tint(STONE, (156, 145, 122))                           # Methodist: warm buff-grey
PRES = tint(STONE, (112, 110, 105))                           # Presbyterian: dark grey (#6E6C68 area)
PART_TINT = {"E1W": (0.62, 0.62, 0.60), "E1L": (0.90, 0.88, 0.83), "E1R": (0.95, 0.94, 0.90),
             "E2": (0.88, 0.87, 0.80), "E3": (0.96, 0.94, 0.86), "E4": (0.84, 0.78, 0.64),
             "E6N": (0.80, 0.80, 0.78), "E6F": (0.10, 0.10, 0.10), "E6W": (0.98, 0.97, 0.93),
             "E7I": (0.85, 1.0, 0.75), "E9R": (0.10, 0.10, 0.10), "E9M": (0.97, 0.97, 0.95),
             "RoadND": (0.77, 0.75, 0.73), "RoadSD": (0.77, 0.75, 0.73), "Beds": (0.78, 0.68, 0.58)}
TINTS = {("E1", "brick"): (0.98, 0.92, 0.90), ("E5", "brick"): (0.80, 0.72, 0.70),
         ("E10", "brick"): (0.82, 0.74, 0.72), ("E11", "brick"): (0.95, 0.88, 0.85),
         ("Curb", "concrete"): (1.0, 0.98, 0.95), ("WalkN", "concrete"): (0.96, 0.95, 0.92),
         ("WalkS", "concrete"): (0.96, 0.95, 0.92), ("WalkC", "concrete"): (0.96, 0.95, 0.92),
         ("Paths", "concrete"): (1.0, 0.97, 0.90), ("LotW", "grass"): (0.98, 0.94, 0.84),
         ("LotE", "grass"): (0.98, 0.95, 0.86), ("LotB", "grass"): (0.98, 0.95, 0.86),
         ("LotC", "grass"): (1.0, 1.0, 0.95), ("LotS", "grass"): (1.0, 0.99, 0.93),
         ("LawnW", "grass"): (1.0, 1.0, 0.95), ("E9P", "grass"): (1.0, 1.0, 0.95)}


def part_tint(part, mat):
    if (part, mat) in TINTS:
        return TINTS[(part, mat)]
    if mat == "block":
        if part.startswith("E7"):
            return tuple(min(1.0, c * (1.12 if part == "E7B" else 1.0)) for c in METH)
        if part.startswith("E8"):
            return PRES
    if part in PART_TINT:
        return PART_TINT[part]
    return (1.0, 1.0, 1.0)


def add_tint(obj, rgb):
    attr = obj.data.color_attributes.new("Tint", "FLOAT_COLOR", "CORNER")
    attr.data.foreach_set("color", np.tile(np.array([*rgb, 1.0], dtype=np.float32), len(obj.data.loops)))


parts = [o for o in bpy.data.collections[COLL].objects if o.type == "MESH"]
for obj in parts:
    obj.data.materials.clear()
    obj.data.materials.append(FINAL[obj["mat"]])
    add_tint(obj, part_tint(obj["part"], obj["mat"]))

if globals().get("EN_MATERIALS_ONLY"):
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
    zs = -c.y                                     # scene z
    near = (-200.0 < zs < -160.0) or (60.0 < zs < 170.0)
    if m == "en_road" and n.z > 0.9:
        f *= 0.35 if near else 0.22               # Main St, junction, side-street stubs
    elif m in ("en_grass", "en_earth") and n.z > 0.9:
        f *= 0.3 if near else 0.18                # lots and lawns
    elif m in ("en_grass", "en_earth", "en_road"):
        f *= 0.25                                 # skirts
    elif m == "en_concrete" and n.z > 0.9 and c.z < 0.3:
        f *= 0.45 if near else 0.3                # walks
    elif m == "en_slate" or (n.z > 0.5 and c.z > 3.0):
        f *= 0.55                                 # roofs
    if n.z < -0.5:
        f *= 0.6                                  # soffits, porch ceilings
    street = abs(n.z) < 0.5 and ((n.x < -0.7 and c.x < 20.0) or (n.x > 0.7 and c.x < -10.0))
    if street:
        f *= 1.35                                 # fronts on Main St
    elif abs(n.z) < 0.5 and ((zs > 60 and n.y > 0.7) or (zs < -160 and n.y < -0.7)):
        f *= 1.15                                 # walls facing the walkable stretch
    if abs(n.z) < 0.5 and (zs < -290 or zs > 175):
        f *= 0.8                                  # the far church, the far ends
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
sun = bpy.data.objects.new("EN_Sun", bpy.data.lights.new("EN_Sun", "SUN"))
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


gm = bpy.data.meshes.new("EN_Ground")
gm.from_pydata([(-600, -600, -0.02), (600, -600, -0.02), (600, 600, -0.02), (-600, 600, -0.02)], [], [(0, 1, 2, 3)])
gm.materials.append(rig_mat("EN_GroundMat", (0.20, 0.19, 0.12)))
rig.objects.link(bpy.data.objects.new("EN_Ground", gm))
occ = rig_mat("EN_OccMat", (0.45, 0.42, 0.36))


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


# bake context only: the built neighbours' GLBs at their index.html places in the EN_Context
# collection (re-imported on every run)
ctx = bpy.data.collections.get(CONTEXT)
if not ctx:
    ctx = bpy.data.collections.new(CONTEXT)
    scene.collection.children.link(ctx)
for o in list(ctx.objects):
    me = o.data if o.type == "MESH" else None
    bpy.data.objects.remove(o, do_unlink=True)
    if me and me.users == 0:
        bpy.data.meshes.remove(me)
import os as _os
for glb, (px, py, pz), rot in NEIGHBOURS:
    if not _os.path.exists(PROJECT + r"\assets\models" + "\\" + glb):
        print("bake context: missing", glb)
        continue
    _before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=PROJECT + r"\assets\models" + "\\" + glb)
    for o in [o for o in bpy.data.objects if o not in _before]:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        ctx.objects.link(o)
        o.name = "ENCTX_" + glb[:-4]
        if o.parent is None:
            o.rotation_mode = "XYZ"
            o.location = (px, -pz, py)
            o.rotation_euler = (0, 0, math.radians(rot))
ctx.hide_viewport = False

if TREE_SHADOWS:
    leaf = bpy.data.materials.get("EN_Leaf") or bpy.data.materials.new("EN_Leaf")
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
    for i, tr in enumerate(TREES):
        x, z, s, base = tr[:4]
        maple = len(tr) > 4 and tr[4] == "maple"      # old-maple.glb: crown ~14 m wide, top 17 m
        cz, rh, rv, th = (11.2, 6.8, 5.6, 6.0) if maple else (7.4, 3.3, 2.9, 4.5)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(x, -z, base + cz * s))
        cr = bpy.context.active_object
        cr.scale = (rh * s, rh * s, rv * s)
        cr.name = "EN_Crown%d" % i
        cr.data.materials.append(leaf)
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=(0.35 if maple else 0.2) * s, depth=th * s,
                                            location=(x, -z, base + th / 2 * s))
        tk = bpy.context.active_object
        tk.name = "EN_Trunk%d" % i
        tk.data.materials.append(occ)
        for o in (cr, tk):
            for c in list(o.users_collection):
                c.objects.unlink(o)
            rig.objects.link(o)

if scene.world is None:
    scene.world = bpy.data.worlds.new("EN_Sky")
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
    light_img = bake_target("EN_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask -------------------------------------------------------------
    grime_mat = bpy.data.materials.get("EN_GrimeBake") or bpy.data.materials.new("EN_GrimeBake")
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
    grime_img = bake_target("EN_Grime", True)
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
out_img = bpy.data.images.get("EN_Lightmap") or bpy.data.images.new("EN_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
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
# Nine maps would make a 1.8 MB GLB (PLAN.md asks <= 1.5 MB per backdrop): the four heaviest /
# odd ones are embedded as re-encoded copies made here in a temp folder from the project files
# (nothing new is written into the project): road q70, slate and brick q62, grass q72, and
# ground_detail scaled 256 -> 1024 px so `baked-lighting` can merge it with the other 1K maps
# into the one draw call. The materials point back at the originals afterwards.
import os
import tempfile
REENCODE = {"road_oiled_earth": (70, None), "roof_slates_03": (62, None), "red_brick": (62, None),
            "backdrop_grass": (72, None), "ground_detail": (85, 1024)}
tmpdir = tempfile.mkdtemp(prefix="street_ends_glb_")
swapped = []
for mat in mesh.materials:
    for node in mat.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image:
            stem = os.path.splitext(os.path.basename(node.image.filepath))[0]
            if stem in REENCODE:
                q, size = REENCODE[stem]
                cp = node.image.copy()
                if size:
                    cp.scale(size, size)
                cp.file_format = "JPEG"
                path = os.path.join(tmpdir, stem + ".jpg")
                cp.save(filepath=path, quality=q)
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
