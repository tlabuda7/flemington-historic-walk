"""
house_91_93_bake.py - textures and baked lighting for 91-93 Main St (frame house used as offices
with a dwelling ell), then export to assets/models/house-91-93.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/house_91_93_bake.py").read())

Steps (pattern: store_79_bake.py):
 1. Rebuild the geometry (house_91_93.py).
 2. Seven materials, all maps reused (nothing downloaded):
      clapboard    house-65-main/clapboard_cream.jpg, tile 1.08 m (9 boards -> 0.12 m exposure),
                   x factor -> white-cream #E3DED0
      trim         polyhaven/trim_paint_cream.jpg, tile 1.0 m, x factor -> #DDD5C2 (cornices,
                   modillions, rakes, casings, corner boards, porch posts, skirts, ceilings); the
                   porch floors and steps use it too with a grey tint baked into the lightmap
                   (painted grey porch floors; keeps the material count at 7)
      door         county-offices/door_varnish_dark.jpg, tile 0.8 m (doors, sashes)
      roof         county-offices/roof_tin_redbrown.jpg, tile 2.0 m (N80 "metal roof"; dulled)
      brick        polyhaven/red_brick.jpg, tile 1.4 m (0.07 m courses, as 83-87), foundations
                   and chimneys
      WindowBack   shared/window_backs.jpg cells (atlas UVs from house_91_93.py)
      glass        plain #1A1916, alpha 0.40, BLEND, single-sided; not lightmapped in the scene
                   (`glass-reflect`); fully transparent during the bake
 3. Join, delete the faces nobody can see, unwrap "Lightmap" (front and north side weighted up).
 4. Bake warm late-afternoon sun + sky into one 2K lightmap with Cycles. West side of Main St
    (front faces east): to-sun (-0.40, 0.90, 0.36). Bake-only shadow casters (not exported):
    the real GLBs of 83-87 Main, 79 Main, the street ends, the Court St side street, the street
    details and the back lots at their index.html transforms, a stand-in for 95-97 Main (PLAN.md
    occluder numbers), and ground boxes (lawn at 0, walk +0.13, road -0.02). Other collections
    are hidden from render during the bake.
 5. Bake an RGB grime mask (dirt and green-grey mildew on the lowest boards and the porch skirts,
    chalky paint under the cornices, streaks under the sills, rust at the tin eaves, soot on the
    chimney tops, grey porch floors) and multiply it in.
 6. Fill empty lightmap pixels, warm the shade, save the sRGB JPEG, print LIGHTMAP_SCALE,
    export the GLB (TEXCOORD_0 + TEXCOORD_1).
"""

import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
TX = PROJECT + r"\assets\textures" + "\\"
MODELS = PROJECT + r"\assets\models" + "\\"
GLB = PROJECT + r"\assets\models\house-91-93.glb"
LIGHTMAP = PROJECT + r"\assets\textures\house-91-93-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 384
TO_SUN = (-0.40, 0.90, 0.36)          # west-side building (front faces east)
COLL, RIG, NEIGH = "House9193", "H91_BakeRig", "H91_Neighbours"
ENTITY = (-13.18, 0.02, 38.63)        # scene position of this building (rotation 0 90 0)

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\house_91_93.py", encoding="utf-8").read())


# 2. Materials ----------------------------------------------------------------
def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    """Constant colour that turns a texture averaging `avg` (sRGB 0-255) into `target`."""
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


GLASS_ALPHA = 0.40
GLASS_RGB = (0x1A, 0x19, 0x16)
SHARED = TX + "shared" + "\\"
LOOK = {
    "Clap":  (TX + r"house-65-main\clapboard_cream.jpg", 1.08, 0.85, None, tint((229, 223, 204), (0xE3, 0xDE, 0xD0))),
    "Trim":  (TX + r"polyhaven\trim_paint_cream.jpg", 1.0, 0.7, None, tint((230, 218, 191), (0xDD, 0xD5, 0xC2))),
    "Door":  (TX + r"county-offices\door_varnish_dark.jpg", 0.8, 0.6, None, None),
    "Roof":  (TX + r"county-offices\roof_tin_redbrown.jpg", 2.0, 0.6, None, None),
    "Brick": (TX + r"polyhaven\red_brick.jpg", 1.4, 0.9, None, tint((142, 103, 80), (0x8A, 0x4A, 0x36))),
    "WBack": (SHARED + "window_backs.jpg", 1.0, 0.9, None, None),
    "Glass": (None, 1.0, 0.05, tuple(srgb_to_lin(c) for c in GLASS_RGB), None),
}
FINAL_NAMES = {"Clap": "clapboard", "Trim": "trim", "Door": "door", "Roof": "roof", "Brick": "brick",
               "WBack": "WindowBack", "Glass": "glass"}


def textured_material(name, image_file, roughness, colour, factor):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = roughness
    if image_file:
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
    else:
        bsdf.inputs["Base Color"].default_value = (*colour, 1)
    if name == "glass":
        bsdf.inputs["Alpha"].default_value = GLASS_ALPHA
        mat.use_backface_culling = True
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        elif hasattr(mat, "blend_method"):
            mat.blend_method = "BLEND"
    return mat


FINAL = {k: textured_material(FINAL_NAMES[k], LOOK[k][0], *LOOK[k][2:]) for k in LOOK}
TINTS = {"Roof": (0.84, 0.86, 0.90), "Deck": (0.60, 0.64, 0.70)}
OBJ_MAT = {k: "Clap" for k in ("ShellA", "ShellX", "ShellB", "ShellC", "ShellD")}


def set_uvs(obj, kind):
    """Box UVs in real-world metres; window backs from their records."""
    mesh = obj.data
    while mesh.uv_layers:
        mesh.uv_layers.remove(mesh.uv_layers[0])
    uv = mesh.uv_layers.new(name="UVMap")
    mat_key = OBJ_MAT.get(kind) or BUILDER_MAT[kind]
    tile = LOOK[mat_key][1]
    rid_attr = mesh.attributes.get("rid")
    for poly in mesh.polygons:
        n = poly.normal
        if kind == "WBack":
            rec = BACKREC.get(rid_attr.data[poly.index].value)
            for li in poly.loop_indices:
                co = mesh.vertices[mesh.loops[li].vertex_index].co
                (px, py), (nx, ny) = rec["wall"]
                u = (co.x - px) * -ny + (co.y - py) * nx
                fu = (u - rec["u0"]) / (rec["u1"] - rec["u0"])
                fz = (co.z - rec["z0"]) / (rec["z1"] - rec["z0"])
                U0, V0, U1, V1 = rec["uv"]
                uv.data[li].uv = (U0 + (U1 - U0) * fu, V0 + (V1 - V0) * fz)
            continue
        h = math.hypot(n.x, n.y)
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            if 0.25 < abs(n.z) < 0.97:
                tx, ty = -n.y / h, n.x / h
                u, v = co.x * tx + co.y * ty, co.z / h
            elif abs(n.z) >= 0.97:
                u, v = co.x, co.y
            else:
                tx, ty = -n.y / h, n.x / h
                u, v = co.x * tx + co.y * ty, co.z
            uv.data[li].uv = (u / tile, v / tile)


def add_tint(obj, rgb):
    attr = obj.data.color_attributes.new("Tint", "FLOAT_COLOR", "CORNER")
    data = np.tile(np.array([*rgb, 1.0], dtype=np.float32), len(obj.data.loops))
    attr.data.foreach_set("color", data)


def bisect_faces(obj, select, cuts):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for co, no in cuts:
        bm.normal_update()
        faces = [f for f in bm.faces if select(f)]
        edges = list({e for f in faces for e in f.edges})
        verts = list({v for f in faces for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=verts + edges + faces, dist=1e-4, plane_co=co, plane_no=no)
    bm.to_mesh(obj.data)
    bm.free()


def on_plane(axis, value, sign):
    k = "xyz".index(axis)
    return lambda f: f.normal[k] * sign > 0.99 and abs(f.calc_center_median()[k] - value) < 0.01


# split big wall faces where other masses cover them, so the hidden parts can go
SPLITS = {
    "ShellA": [
        (on_plane("x", -HW, -1), [((0, BY0, 0), (0, 1, 0)), ((0, 0, zB(BX1) + 0.02), (0, 0, 1))]),
        (on_plane("y", YA, 1), [((CX1, 0, 0), (1, 0, 0)), ((CX0, 0, 0), (1, 0, 0)), ((0, 0, C_EAVE), (0, 0, 1))]),
    ],
}

parts = [o for o in col.objects if o.type == "MESH"]
for obj in parts:
    kind = obj.name[4:]
    for select, cuts in SPLITS.get(kind, []):
        bisect_faces(obj, select, cuts)
    set_uvs(obj, kind)
    add_tint(obj, TINTS.get(kind, (1.0, 1.0, 1.0)))
    obj.data.materials[0] = FINAL[OBJ_MAT.get(kind) or BUILDER_MAT[kind]]
    if obj.data.attributes.get("rid"):
        obj.data.attributes.remove(obj.data.attributes["rid"])

# 3. Join, drop hidden faces, unwrap the lightmap UVs --------------------------
r_obj = bpy.data.objects["H91_ShellA"]
with bpy.context.temp_override(active_object=r_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
r_obj.name = r_obj.data.name = COLL
mesh = r_obj.data
slots = {}
remap = []
for m in mesh.materials:
    if m.name not in slots:
        slots[m.name] = len(slots)
    remap.append(slots[m.name])
order = sorted(slots, key=slots.get)
mi = np.empty(len(mesh.polygons), dtype=np.int32)
mesh.polygons.foreach_get("material_index", mi)
mi = np.array(remap, dtype=np.int32)[mi]
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
    n = int(min(3000, max(6, area / 0.01)))
    areas = [((t[1].vert.co - t[0].vert.co).cross(t[2].vert.co - t[0].vert.co)).length / 2 for t in tris]
    total = sum(areas) or 1.0
    out = []
    for t, a in zip(tris, areas):
        p0, p1, p2 = (l.vert.co for l in t)
        c = (p0 + p1 + p2) / 3
        out.append(c)
        for _ in range(max(1, round(n * a / total))):
            r1, r2 = rng.random(), rng.random()
            if r1 + r2 > 1:
                r1, r2 = 1 - r1, 1 - r2
            p = p0 + (p1 - p0) * r1 + (p2 - p0) * r2
            v = c - p
            d = v.length
            out.append(p + v * (min(0.008, 0.25 * d) / d) if d > 1e-6 else p)
    return out or [f.calc_center_median()]


def remove_hidden_faces(obj, rays=120):
    """Delete faces that no ray from any of their sample points can leave the model
    through (inside walls, under trim, behind glass). Downward faces at grade go too."""
    import random
    rng = random.Random(7)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    glass_i = [i for i, m in enumerate(obj.data.materials) if m.name == "glass"]
    bm.verts.index_update()
    bvh = BVHTree.FromPolygons([v.co for v in bm.verts],
                               [[v.index for v in f.verts] for f in bm.faces if f.material_index not in glass_i])
    dirs = fibonacci(rays)
    face_tris = {}
    for t in bm.calc_loop_triangles():
        face_tris.setdefault(t[0].face, []).append(t)
    dead = []
    for f in bm.faces:
        n = f.normal
        c = f.calc_center_median()
        if n.z < -0.9 and c.z < 0.01:
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
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    return len(dead)


before = sum(len(p.vertices) - 2 for p in mesh.polygons)
removed = remove_hidden_faces(r_obj)
after = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("hidden faces removed:", removed, "| triangles", before, "->", after)

# every visible face must point out of the model (nothing touching right in front of it)
bvh_all = BVHTree.FromPolygons([v.co for v in mesh.vertices], [list(p.vertices) for p in mesh.polygons])
inward = sum(1 for p in mesh.polygons if bvh_all.ray_cast(p.center + p.normal * 0.002, p.normal, 0.004)[0] is not None)
print("faces with something touching right in front of them:", inward)

lm = mesh.uv_layers.new(name="Lightmap")
mesh.uv_layers.active = lm
mesh.uv_layers["UVMap"].active_render = True
for o in bpy.context.view_layer.objects:
    o.select_set(o == r_obj)
bpy.context.view_layer.objects.active = r_obj
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003,
                         area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.object.mode_set(mode="OBJECT")
# Lightmap pixels to what matters: the front, the porch and the north side across the yard.
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    f = 1.0
    c, n = p.center, p.normal
    m = mat_names[p.material_index]
    if m == "glass":
        f *= 0.03
    elif m == "WindowBack":
        f *= 0.6
    if n.z < -0.5:
        f *= 0.7
    if n.y < -0.7 and c.y < BY0 + 0.3:
        f *= 1.3                                   # the fronts and porches
    if n.x > 0.7 and c.x > HW - 0.05 and c.y < YA:
        f *= 1.15                                  # north side (seen across the yard)
    if n.y > 0.7 and c.y > BY1 - 0.1:
        f *= 0.5                                   # rear walls
    if c.y > YA + 0.05:
        f *= 0.6                                   # wing and rear parts
    if m == "roof" and n.z > 0.5:
        f *= 0.5
    if f != 1.0:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.0015, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig and neighbours (not exported) ----------------------------------------
scene = bpy.context.scene


def get_coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        scene.collection.children.link(c)
    return c


rig = get_coll(RIG)
rig.hide_viewport = False
rig.hide_render = False
sun = bpy.data.objects.get("H91_Sun")
if not sun:
    sun = bpy.data.objects.new("H91_Sun", bpy.data.lights.new("H91_Sun", "SUN"))
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
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    m = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0),
                       (z0 + z1) / 2 + v.co.z * (z1 - z0)))
    bm.to_mesh(m)
    bm.free()
    m.materials.append(mat)
    o = bpy.data.objects.new(name, m)
    rig.objects.link(o)
    return o


def rig_gable(name, x0, x1, y0, y1, eave, ridge, mat):
    """Stand-in house with a gable roof, ridge along X at the middle of y0..y1."""
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    yc = (y0 + y1) / 2
    prof = [(y0, 0.0), (y1, 0.0), (y1, eave), (yc, ridge), (y0, eave)]
    vs = [(x0, y, z) for y, z in prof] + [(x1, y, z) for y, z in prof]
    fs = [(0, 1, 2, 3, 4), (9, 8, 7, 6, 5)] + [(i, (i + 1) % 5, 5 + (i + 1) % 5, 5 + i) for i in range(5)]
    m = bpy.data.meshes.new(name)
    m.from_pydata(vs, [], fs)
    m.materials.append(mat)
    o = bpy.data.objects.new(name, m)
    rig.objects.link(o)
    return o


# ground (local frame): lawn at 0 from the street line (scene x -7.95 -> Y -5.23); walk top
# +0.13 out to the curb (scene x -6.52 -> Y -6.66); road -0.02
warm = rig_mat("H91_GroundWarm", (0.34, 0.28, 0.19))
grass = rig_mat("H91_GroundLawn", (0.20, 0.24, 0.12))
wall_m = rig_mat("H91_Standin", (0.45, 0.30, 0.24))
rig_box("H91_Road", -150, 150, -150, 150, -0.25, -0.02, warm)
rig_box("H91_Walk", -150, 150, -6.66, -5.23, -0.25, 0.13, warm)
rig_box("H91_Lawn", -150, 150, -5.23, 150, -0.25, 0.0, grass)
# 95-97 Main (not built yet): PLAN.md occluder numbers, gable roof along Main St
rig_gable("H91_Stand9597", -19.70, -11.07, 2.03, 10.90, 6.90, 10.18, wall_m)
rig_box("H91_Stand95Off", -10.97, -7.95, 3.86, 15.20, 0.0, 3.6, wall_m)


def entity_matrix(px, py, pz, rot_y):
    """Scene entity transform -> this building's local frame. rot_y 90 = west-side building
    (its GLB is already in a local frame like ours); 0 = scene-origin model (GLB in scene axes)."""
    ex, ey, ez = ENTITY
    if rot_y == 90:
        return Matrix.Translation((ez - pz, ex - px, py - ey))
    # scene-axis GLB imported to Blender as (x, -z, y): X = 38.63 + by, Y = -13.18 - bx
    return Matrix.Translation((ez - pz, ex - px, py - ey)) @ Matrix.Rotation(math.radians(-90), 4, "Z")


NEIGHBOURS = {
    "block-83-87": (-4.58, 0.15, 23.11, 90),
    "store-79": (-9.74, 0.15, 14.22, 90),
    "street-ends": (0.0, 0.0, 0.0, 0),
    "sidestreet-court": (0.0, 0.0, 0.0, 0),
    "street-details": (0.0, 0.0, 0.0, 0),
    "back-lots": (0.0, 0.0, 0.0, 0),
}


def import_neighbours():
    """The real neighbour GLBs, placed by their index.html entities (scene -> local frame)."""
    nb = get_coll(NEIGH)
    for o in list(nb.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    for name, (px, py, pz, ry) in NEIGHBOURS.items():
        M = entity_matrix(px, py, pz, ry)
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=MODELS + name + ".glb")
        for o in [o for o in bpy.data.objects if o not in before]:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            nb.objects.link(o)
            o["neighbour"] = name
            if o.parent is None:
                o.matrix_world = M @ o.matrix_world
    return nb


nb = import_neighbours()
nb.hide_render = False

if scene.world is None:
    scene.world = bpy.data.worlds.new("H91_Sky")
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
    c.hide_render = c.name not in (COLL, RIG, NEIGH)
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
glass_alpha = next(n for n in FINAL["Glass"].node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"]
glass_alpha.default_value = 0.0
try:
    light_img = bake_target("H91_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask (RGB) ----------------------------------------------------------
    grime_mat = bpy.data.materials.get("H91_GrimeBake") or bpy.data.materials.new("H91_GrimeBake")
    grime_mat.use_nodes = True
    nt = grime_mat.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    L = nt.links.new
    out = N("ShaderNodeOutputMaterial")
    emit = N("ShaderNodeEmission")
    geo = N("ShaderNodeNewGeometry")
    sep = N("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs["Vector"])
    nsep = N("ShaderNodeSeparateXYZ")
    L(geo.outputs["Normal"], nsep.inputs["Vector"])
    X, Y, Z = sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]
    NX, NY, NZ = nsep.outputs["X"], nsep.outputs["Y"], nsep.outputs["Z"]

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

    def vmul(a, b):
        m = N("ShaderNodeVectorMath")
        m.operation = "MULTIPLY"
        for i, s in enumerate((a, b)):
            if isinstance(s, tuple):
                m.inputs[i].default_value = s
            else:
                L(s, m.inputs[i])
        return m.outputs["Vector"]

    def vmix(fac, a, b):
        m = N("ShaderNodeMix")
        m.data_type = "RGBA"
        L(fac, m.inputs["Factor"])
        sock = lambda socks, n: next(x for x in socks if x.name == n and x.type == "RGBA")
        sock(m.inputs, "A").default_value = (*a, 1)
        sock(m.inputs, "B").default_value = (*b, 1)
        return sock(m.outputs, "Result")

    def noise_tex(vec, scale, detail):
        t = N("ShaderNodeTexNoise")
        t.inputs["Scale"].default_value = scale
        t.inputs["Detail"].default_value = detail
        L(vec, t.inputs["Vector"])
        return t.outputs["Fac"]

    vert = map_range(math_op("ABSOLUTE", NZ), 0.3, 0.1, 0.0, 1.0)
    up = map_range(NZ, 0.8, 0.95, 0.0, 1.0)
    slope_up = map_range(NZ, 0.25, 0.45, 0.0, 1.0)
    # dirt splash on the bottom ~0.5 m, fading by 1.0 m; blotchy
    height = map_range(Z, -0.15, 1.0, 0.80, 1.0)
    blotch = map_range(noise_tex(geo.outputs["Position"], 0.6, 6.0), 0.0, 1.0, 0.90, 1.03)
    stretch = N("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (4.0, 4.0, 0.18)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_n = noise_tex(stretch.outputs["Vector"], 1.7, 2.0)
    streaks = map_range(streak_n, 0.35, 0.75, 0.94, 1.0)
    # chalky paint streaked under the cornices of A (soffit 6.18) and B (5.79)
    under_a = mult(vert, map_range(Z, 4.6, FRZ0 - 0.01, 0.0, 0.12), map_range(Z, FRZ0 - 0.01, FRZ0 + 0.01, 1.0, 0.0),
                   map_range(streak_n, 0.3, 0.8, 0.6, 1.4))
    under_b = mult(vert, map_range(X, BX1 - 0.05, BX1 + 0.05, 1.0, 0.0), map_range(Z, 4.4, FRZ0_B - 0.01, 0.0, 0.10),
                   map_range(Z, FRZ0_B - 0.01, FRZ0_B + 0.01, 1.0, 0.0), map_range(streak_n, 0.3, 0.8, 0.6, 1.4))
    # streaks below the window sills
    drip = None
    for zz in (GF[0] - 0.15, UF[0] - 0.15, 1.05, 3.85):
        band = mult(map_range(Z, zz - 1.0, zz - 0.02, 0.0, 1.0), map_range(Z, zz - 0.02, zz, 1.0, 0.0))
        drip = band if drip is None else math_op("MAXIMUM", drip, band)
    drips = mult(vert, drip, map_range(streak_n, 0.3, 0.75, 0.09, 0.02))
    soot = math_op("SUBTRACT", 1.0, math_op("ADD", math_op("MAXIMUM", under_a, under_b), drips))
    # soot on the chimney tops
    chim = mult(map_range(Z, 9.8, 10.3, 1.0, 0.6),
                math_op("SUBTRACT", 1.0, mult(map_range(Y, 16.15, 16.25, 0.0, 1.0), map_range(Y, 16.85, 16.95, 1.0, 0.0),
                                              map_range(Z, 8.0, 8.5, 0.0, 0.4))))
    # grey porch floors worn in front of the doors and at the steps
    treads = map_range(mult(up, map_range(Z, 0.50, 0.44, 0.0, 1.0), map_range(Z, 0.10, 0.14, 0.0, 1.0),
                            map_range(math_op("ABSOLUTE", X), 1.2, 0.5, 0.0, 1.0)), 0.0, 1.0, 1.0, 0.90)
    # rust streaks on the tin roofs near the eaves (low edge of each slope)
    rust_amt = mult(slope_up, map_range(streak_n, 0.35, 0.8, 0.0, 1.0),
                    math_op("MAXIMUM", map_range(Z, 6.6, 6.2, 0.0, 1.0),
                            mult(map_range(Z, 3.5, 3.3, 0.0, 1.0), map_range(Z, 2.8, 2.9, 0.0, 1.0))))
    rust_col = vmix(mult(rust_amt, 0.8), (1.0, 1.0, 1.0), (0.92, 0.78, 0.66))
    # wing and the rear walls duller and streakier
    rear = map_range(Y, YA - 0.1, YA + 0.05, 0.0, 1.0)
    cd = math_op("SUBTRACT", 1.0, mult(rear, math_op("ADD", 0.04, map_range(streak_n, 0.3, 0.75, 0.08, 0.0))))
    grey = mult(height, blotch, streaks, soot, chim, treads, cd)
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    # green-grey mildew on the lowest boards and the porch skirts (vertical faces below 0.7 m)
    mildew = mult(vert, map_range(Z, 0.15, 0.75, 1.0, 0.0), map_range(noise_tex(geo.outputs["Position"], 1.3, 4.0),
                                                                   0.35, 0.7, 0.4, 1.0))
    mildew_col = vmix(mildew, (1.0, 1.0, 1.0), (0.88, 0.94, 0.86))
    attr = N("ShaderNodeAttribute")
    attr.attribute_name = "Tint"
    rgb = vmul(vmul(vmul(gc.outputs["Vector"], mildew_col), rust_col), attr.outputs["Color"])
    L(rgb, emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    grime_img = bake_target("H91_Grime", True)
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
    glass_alpha.default_value = GLASS_ALPHA
    for name, state in render_state.items():
        if bpy.data.collections.get(name):
            bpy.data.collections[name].hide_render = state
    for name, state in loose_state.items():
        if bpy.data.objects.get(name):
            bpy.data.objects[name].hide_render = state
    rig.hide_render = True
    rig.hide_viewport = True
    nb.hide_render = True
bpy.data.materials.remove(bpy.data.materials["H91_GrimeBake"])

# Combine, normalise and save as an sRGB-encoded JPEG.
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
out_img = bpy.data.images.get("H91_Lightmap") or bpy.data.images.new("H91_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
out_img.scale(LIGHTMAP_SIZE, LIGHTMAP_SIZE)
out_img.colorspace_settings.name = "Non-Color"
out_img.pixels.foreach_set(rgba.ravel())
out_img.filepath_raw = LIGHTMAP
out_img.file_format = "JPEG"
scene.render.image_settings.quality = 88
out_img.save()
LIGHTMAP_SCALE = round(scale, 4)
print("lightmap coverage: %.1f%% of pixels baked" % (100 * baked.mean()))
print("LIGHTMAP_SCALE =", LIGHTMAP_SCALE, "(use baked-lighting intensity:", LIGHTMAP_SCALE, ")")

for mat in mesh.materials:
    for name in ("BakeTarget", "BakeUV"):
        node = mat.node_tree.nodes.get(name)
        if node:
            mat.node_tree.nodes.remove(node)
if mesh.color_attributes.get("Tint"):
    mesh.color_attributes.remove(mesh.color_attributes["Tint"])

# 6. Export ---------------------------------------------------------------------
for o in bpy.context.scene.objects:
    o.select_set(o == r_obj)
bpy.context.view_layer.objects.active = r_obj
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_texcoords=True,
                          export_normals=True)
tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("exported", GLB, "|", tris, "triangles |", len(mesh.materials), "materials")
r_obj["lightmap_scale"] = LIGHTMAP_SCALE            # read by house_91_93_preview.py
