"""
north_approach_bake.py - materials, baked lighting and export for the north approach
(assets/models/north-approach.glb: the ten houses 1-11 / 2-10 Main between the last shops and the
Soldiers' Monument, with their lawns, paths and the 1913 west walk; PLAN.md 7.9). Same pipeline
as street_ends_bake.py.

Run inside Blender (assets/models/source/north_approach.blend):
    exec(open(r"<project>/tools/blender/north_approach_bake.py", encoding="utf8").read())
Set NA_MATERIALS_ONLY = True before exec() to stop after step 2.

 1. Rebuild the geometry (north_approach.py).
 2. Eight 1024 px materials (`baked-lighting` merges them into one draw call):
      clap      house-65-main/clapboard_cream.jpg, tile 1.0 m (paint colours via Tint)
      brick     polyhaven/red_brick.jpg, tile 1.4 m, x factor -> #7A4436 (NW5, NE1, NE2, NE4)
      slate     polyhaven/roof_slates_03.jpg, tile 1.5 m (NE2's shingle by Tint)
      block     shared/backdrop_block_rockfaced.jpg, tile 2.0 m: NW1's rubble stone (grey-brown Tint)
      stucco    courthouse/stucco_cream.jpg, tile 2.5 m: NE5's pale scored stucco
      atlas     shared/backdrop_windows.jpg: windows, doors, pickets, paint / tin / stone swatches
      concrete  polyhaven/sidewalk_concrete.jpg, tile 3 m (walk, paths, curb, foundations, steps)
      grass     shared/backdrop_grass.jpg, tile 4 m (lawns, grass strip)
 3. Join, delete faces nobody can see, unwrap "Lightmap" (street fronts and south faces up,
    lawns and roofs down), pack.
 4. Bake warm late-afternoon sun + sky into one 2K lightmap with Cycles: scene axes, Blender
    to-sun (-0.90, -0.40, 0.36). Bake-only extras (not exported): a ground plane, the built
    neighbours (27 Main, 24-30 Main, street-ends.glb) and leafy crowns at the tree positions.
 5. Grime mask x Tint. 6. Fill, warm the shade, save sRGB JPEG, print LIGHTMAP_SCALE, export GLB.
"""

import math
import os
import tempfile
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
TX = PROJECT + r"\assets\textures" + "\\"
GLB = PROJECT + r"\assets\models\north-approach.glb"
LIGHTMAP = PROJECT + r"\assets\textures\north-approach-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 256
TO_SUN = (-0.90, -0.40, 0.36)
COLL, RIG, OBJ_NAME = "NorthApproach", "NA_BakeRig", "NorthApproach"
CONTEXT = "NA_Context"
# scene (x, z, scale, y, kind) of the tree instances the scene should place (old-maple.glb at real
# size = "maple"; backdrop-tree.glb = "young"). Rows: PHOTO (1908, 1913 cards); spacing GUESS.
TREES = [(-11.3, -206.0, 0.95, 0.15, "maple"), (-11.3, -224.0, 1.0, 0.15, "maple"),     # west, lawn edge
         (-11.3, -241.0, 0.9, 0.15, "maple"), (-11.3, -258.0, 1.0, 0.15, "maple"),
         (-11.3, -276.0, 0.95, 0.15, "maple"), (-11.3, -291.0, 1.0, 0.15, "maple"),
         (7.0, -198.0, 1.0, 0.15, "maple"), (7.0, -214.0, 0.95, 0.15, "maple"),          # east, behind the walk
         (7.0, -230.0, 1.0, 0.15, "maple"), (7.0, -246.0, 0.9, 0.15, "maple"),
         (12.4, -275.0, 1.0, 0.15, "maple"), (20.0, -291.5, 0.95, 0.15, "maple"),        # along the bend
         (-20.0, -300.0, 1.05, 0.15, "maple"), (-22.0, -286.0, 1.05, 0.15, "maple"),     # NW5's lawn (c.1910)
         # already in the scene (street-ends' backdrop-tree instances btree-end-3, -4, -5)
         (10.0, -262.0, 2.1, 0.15, "young"), (-14.0, -300.0, 2.3, 0.15, "young"), (-14.0, -322.0, 2.2, 0.15, "young"),
         (-7.6, -187.0, 2.1, 0.15, "young")]
NEIGHBOURS = [("store-27.glb", (-10.30, 0.15, -158.49), 90), ("block-24-30.glb", (7.29, 0.15, -152.365), -90),
              ("street-ends.glb", (0.0, 0.0, 0.0), 0)]

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\north_approach.py", encoding="utf8").read())


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
    "stucco": (TX + r"courthouse\stucco_cream.jpg", 0.9, None),
    "atlas": (TX + r"shared\backdrop_windows.jpg", 0.85, None),
    "concrete": (TX + r"polyhaven\sidewalk_concrete.jpg", 0.95, None),
    "grass": (TX + r"shared\backdrop_grass.jpg", 1.0, (0.80, 0.74, 0.80)),
}
FINAL_NAMES = {k: "na_" + k for k in LOOK}


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

# Paint colours, stone / brick / roof shades, multiplied into the lightmap: (part, material) or part.
STONE = (168, 162, 147)
TINTS = {("NW1", "block"): tint(STONE, (138, 124, 104)),            # grey-brown rubble (GUESS)
         ("NW1", "clap"): (0.9, 0.88, 0.8),
         ("NW1A", "clap"): (0.86, 0.84, 0.78), ("NW1B", "clap"): (0.78, 0.74, 0.66),
         ("NW2", "clap"): (0.99, 0.98, 0.95),
         ("NW3", "clap"): (1.0, 0.9, 0.66),                                 # cream (1913 tint)
         ("NW4", "clap"): (0.98, 0.92, 0.75), ("NW4T", "clap"): (0.98, 0.92, 0.75),
         ("NW4TR", "slate"): (0.62, 0.62, 0.66),                            # dark steep turret roof
         ("NW5", "brick"): (1.0, 0.95, 0.92), ("NW5R", "brick"): (1.0, 0.95, 0.92),
         ("NW5R", "clap"): (0.96, 0.94, 0.88),
         ("NE1", "brick"): (0.9, 0.84, 0.8), ("NE1I", "clap"): (0.6, 0.6, 0.58),   # iron-clad, grey
         ("NE2", "brick"): (0.86, 0.8, 0.76), ("NE2", "slate"): (0.82, 0.7, 0.58),  # shingle
         ("NE2R", "clap"): (0.9, 0.88, 0.8),
         ("NE3", "clap"): (0.93, 0.93, 0.86),
         ("NE4", "brick"): (0.82, 0.74, 0.7),
         ("NE5", "stucco"): (0.98, 0.96, 0.9), ("NE5E", "clap"): (0.95, 0.94, 0.9),
         ("Curb", "concrete"): (1.0, 0.98, 0.95), ("WalkW", "concrete"): (0.96, 0.95, 0.92),
         ("Paths", "concrete"): (1.0, 0.97, 0.90), ("LotW", "grass"): (0.98, 0.94, 0.84),
         ("Strip", "grass"): (0.98, 0.94, 0.84), ("LotE", "grass"): (0.98, 0.95, 0.86)}
PART_TINT = {"NW3S": (0.55, 0.6, 0.55), "NW4S": (0.55, 0.6, 0.55), "NE5S": (0.55, 0.6, 0.55)}


def part_tint(part, mat):
    if (part, mat) in TINTS:
        return TINTS[(part, mat)]
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

if globals().get("NA_MATERIALS_ONLY"):
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
    if m == "na_grass" and n.z > 0.9:
        f *= 0.32                                 # lawns, grass strip
    elif m == "na_grass":
        f *= 0.25                                 # skirts
    elif m == "na_concrete" and n.z > 0.9 and c.z < 0.3:
        f *= 0.5                                  # walk, paths
    elif m == "na_slate" or (n.z > 0.5 and c.z > 3.0):
        f *= 0.6                                  # roofs
    if n.z < -0.5:
        f *= 0.6                                  # soffits, porch ceilings
    if abs(n.z) < 0.5 and ((n.x < -0.7 and c.x > 0) or (n.x > 0.7 and c.x < 0)):
        f *= 1.35                                 # fronts on Main St
    elif abs(n.z) < 0.5 and n.y < -0.7:
        f *= 1.15                                 # south faces (seen from the walkable stretch)
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
sun = bpy.data.objects.new("NA_Sun", bpy.data.lights.new("NA_Sun", "SUN"))
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


gm = bpy.data.meshes.new("NA_Ground")
gm.from_pydata([(-600, -600, -0.02), (600, -600, -0.02), (600, 600, -0.02), (-600, 600, -0.02)], [], [(0, 1, 2, 3)])
gm.materials.append(rig_mat("NA_GroundMat", (0.20, 0.19, 0.12)))
rig.objects.link(bpy.data.objects.new("NA_Ground", gm))
occ = rig_mat("NA_OccMat", (0.45, 0.42, 0.36))

ctx = bpy.data.collections.get(CONTEXT)
if not ctx:
    ctx = bpy.data.collections.new(CONTEXT)
    scene.collection.children.link(ctx)
for o in list(ctx.objects):
    me = o.data if o.type == "MESH" else None
    bpy.data.objects.remove(o, do_unlink=True)
    if me and me.users == 0:
        bpy.data.meshes.remove(me)
for glb, (px, py, pz), rot in NEIGHBOURS:
    _before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=PROJECT + r"\assets\models" + "\\" + glb)
    for o in [o for o in bpy.data.objects if o not in _before]:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        ctx.objects.link(o)
        o.name = "NACTX_" + glb[:-4]
        if o.parent is None:
            o.rotation_mode = "XYZ"
            o.location = (px, -pz, py)
            o.rotation_euler = (0, 0, math.radians(rot))
ctx.hide_viewport = False

leaf = bpy.data.materials.get("NA_Leaf") or bpy.data.materials.new("NA_Leaf")
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
nt.links.new(ramp.outputs["Result"], mix.inputs["Fac"])
nt.links.new(tr.outputs[0], mix.inputs[1])
nt.links.new(dif.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], out.inputs["Surface"])
for i, (x, z, s, base, kind) in enumerate(TREES):
    maple = kind == "maple"
    cz, rh, rv, th = (11.2, 6.8, 5.6, 6.0) if maple else (7.4, 3.3, 2.9, 4.5)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(x, -z, base + cz * s))
    cr = bpy.context.active_object
    cr.scale = (rh * s, rh * s, rv * s)
    cr.name = "NA_Crown%d" % i
    cr.data.materials.append(leaf)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=(0.35 if maple else 0.2) * s, depth=th * s,
                                        location=(x, -z, base + th / 2 * s))
    tk = bpy.context.active_object
    tk.name = "NA_Trunk%d" % i
    tk.data.materials.append(occ)
    for o in (cr, tk):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        rig.objects.link(o)

if scene.world is None:
    scene.world = bpy.data.worlds.new("NA_Sky")
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
    light_img = bake_target("NA_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask -------------------------------------------------------------
    grime_mat = bpy.data.materials.get("NA_GrimeBake") or bpy.data.materials.new("NA_GrimeBake")
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

    wall = map_range(math_op("ABSOLUTE", NZ), 0.5, 0.3, 0.0, 1.0)
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
    grime_img = bake_target("NA_Grime", True)
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
    ctx.hide_render = True
    ctx.hide_viewport = True

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
out_img = bpy.data.images.get("NA_Lightmap") or bpy.data.images.new("NA_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
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
# heavy maps embedded as re-encoded copies (temp folder; nothing new in the project)
REENCODE = {"roof_slates_03": (62, None), "red_brick": (62, None), "backdrop_grass": (72, None),
            "stucco_cream": (70, None), "backdrop_block_rockfaced": (70, None)}
tmpdir = tempfile.mkdtemp(prefix="north_approach_glb_")
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
