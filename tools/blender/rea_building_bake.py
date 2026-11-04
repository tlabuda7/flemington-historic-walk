"""
rea_building_bake.py - textures and baked lighting for the Rea Building / "Clock Tower
Building" (48-52 Main St), then export to assets/models/rea-building.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/rea_building_bake.py").read())

Steps (pattern: lovells_restaurant_bake.py / bank_building_bake.py):
 1. Rebuild the geometry (rea_building.py).
 2. Five materials only (= five draw calls, merged into one by `baked-lighting`):
      brick  polyhaven/red_brick.jpg, tile 1.4 m, x factor -> #8A4030 (walls, hoods, tympana, chimney)
      trim   county-offices/trim_paint_drab.jpg, tile 2.0 m, x factor -> #B5AC98 (cornices,
             brackets, mouldings, shop fronts, sash, sills, keystones, stucco, cupola)
      stone  lovells-restaurant/stone_bluestone.jpg, tile 2.0 m (steps, cheeks, water table)
      dark   plain tin grey #4A4C50 (roofs); glass, door varnish and iron by bake tints
      signs  rea-building/signs_atlas.jpg (tools/prepare_rea_textures.py): awning canvas and
             stripes, valances, clock dials, shutter louvres, dentil strips, sign boards
    Bake tints (multiplied into the lightmap): cupola cream (1.00, 0.96, 0.80), glass, door
    varnish, iron.
 3. Cut the wall shell where the steps, water table, stucco face, pilasters and shop
    entablature cover it, join everything into one object, delete the faces nobody can see,
    unwrap "Lightmap" (front, Bloomfield side and cupola weighted up; north, rear, roofs down).
 4. Bake warm late-afternoon sun + sky (direct and bounced light) into one 2K lightmap with
    Cycles. East side of Main St (front faces west): to-sun (0.40, -0.90, 0.36); the front is
    sunlit, the Bloomfield side grazed, the north wall in shade. Bake-only occluders (the 44-46
    frame building north of the passage, the Bank Building across Bloomfield Ave) are hidden
    from the export. Other collections are hidden from render during the bake.
 5. Bake an RGB grime mask and multiply it in.
 6. Fill empty lightmap pixels from their neighbours, warm the shade, save the sRGB JPEG,
    print LIGHTMAP_SCALE, export the GLB (TEXCOORD_0 + TEXCOORD_1).
"""

import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
TX = PROJECT + r"\assets\textures" + "\\"
GLB = PROJECT + r"\assets\models\rea-building.glb"
LIGHTMAP = PROJECT + r"\assets\textures\rea-building-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 384
TO_SUN = (0.40, -0.90, 0.36)          # east-side building (front faces west)
COLL, RIG = "ReaBuilding", "RB_BakeRig"

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\rea_building.py").read())

# 2. Materials ----------------------------------------------------------------


def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    """Constant colour that turns a texture averaging `avg` (sRGB 0-255) into `target`."""
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


def ratio(target, base):
    return tuple(srgb_to_lin(t) / srgb_to_lin(b) for t, b in zip(target, base))


DARK_BASE = (0x4A, 0x4C, 0x50)        # tin grey
# material -> (texture file, metres per repeat, roughness, plain colour (linear) or None, factor or None)
LOOK = {
    "Brick": (TX + r"polyhaven\red_brick.jpg", 1.4, 0.9, None, tint((142, 103, 80), (0x8A, 0x40, 0x30))),
    "Trim":  (TX + r"county-offices\trim_paint_drab.jpg", 2.0, 0.7, None, tint((0xBC, 0xB4, 0xA0), (0xB5, 0xAC, 0x98))),
    "Stone": (TX + r"lovells-restaurant\stone_bluestone.jpg", 2.0, 0.9, None, None),
    "Dark":  (None, 1.0, 0.4, tuple(srgb_to_lin(c) for c in DARK_BASE), None),
    "Signs": (TX + r"rea-building\signs_atlas.jpg", 1.0, 0.85, None, None),
}
FINAL_NAMES = {"Brick": "brick", "Trim": "trim", "Stone": "stone", "Dark": "dark", "Signs": "signs"}


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
            # texture x constant colour: the glTF exporter writes this as baseColorFactor
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
    return mat


FINAL = {k: textured_material(FINAL_NAMES[k], LOOK[k][0], *LOOK[k][2:]) for k in LOOK}

# Bake tints per builder (multiplied into the lightmap through the grime mask)
CUPOLA_TINT = (1.00, 0.96, 0.80)
TINTS = {"Cupola": CUPOLA_TINT, "CupBody": CUPOLA_TINT,
         "Glass": ratio((0x1E, 0x22, 0x26), DARK_BASE),
         "Door": ratio((0x3A, 0x2A, 0x1F), DARK_BASE),
         "Iron": ratio((0x2A, 0x2A, 0x2B), DARK_BASE)}
OBJ_MAT = {"Shell": "Brick", "Tymp": "Brick", "Stucco": "Trim", "CupBody": "Trim"}

# Atlas boxes (pixels from the top-left; must match tools/prepare_rea_textures.py)
REGIONS = {"canvas48": (0, 0, 512, 320), "stripes": (512, 0, 1024, 320), "val48": (0, 320, 1024, 416),
           "val52": (0, 416, 1024, 480), "dial": (0, 480, 384, 864), "louvre": (384, 480, 576, 864),
           "dentil": (576, 480, 1024, 544), "jeweler": (576, 544, 1024, 640), "shoes": (576, 640, 1024, 736),
           "spare": (576, 736, 1024, 864), "spare2": (0, 864, 1024, 1024)}
EDGE = {"dentil": (0.5, 0.06), "dial": (0.5, 0.004), "louvre": (0.03, 0.5)}


def atlas_uv(region, fu, fv, inset=2):
    """UV of the point (fu across, fv down from the top, both 0..1) inside an atlas box."""
    c0, r0, c1, r1 = REGIONS[region]
    col_ = c0 + inset + (c1 - c0 - 2 * inset) * min(max(fu, 0.0), 1.0)
    row = r0 + inset + (r1 - r0 - 2 * inset) * min(max(fv, 0.0), 1.0)
    return (col_ / 1024, 1 - row / 1024)


def atlas_face_uvs(rec, n, cos):
    """UVs for the corners `cos` of a face with normal n, from its atlas record."""
    (px, py), (nx, ny) = rec["wall"]
    tx, ty = -ny, nx
    region = rec["region"]
    front = n.x * nx + n.y * ny > 0.9
    out = []
    for co in cos:
        u = (co.x - px) * tx + (co.y - py) * ty
        d = (co.x - px) * nx + (co.y - py) * ny
        z = co.z
        mode = rec["mode"]
        if mode == "slope":
            out.append(atlas_uv(region, (u - rec["u0"]) / (rec["u1"] - rec["u0"]),
                                (d - rec["d0"]) / (rec["d1"] - rec["d0"])))
        elif mode == "side":
            out.append(atlas_uv(region, (d - rec["d0"]) / (rec["d1"] - rec["d0"]),
                                (rec["z1"] - z) / (rec["z1"] - rec["z0"]), 4))
        elif mode == "rect":
            fu = (u - rec["u0"]) / (rec["u1"] - rec["u0"])
            fv = (rec["z1"] - z) / (rec["z1"] - rec["z0"])
            if front:
                out.append(atlas_uv(region, fu, fv))
            elif rec.get("back"):
                out.append(atlas_uv(rec["back"], fu, fv, 4))
            else:
                out.append(atlas_uv(region, *EDGE.get(region, (0.01, 0.5))))
        elif mode == "arc":
            du, dz = u - rec["cu"], z - rec["zc"]
            if front:
                a = math.atan2(dz, du)
                r = math.hypot(du, dz)
                fu = rec["f0"] + (rec["f1"] - rec["f0"]) * (a - rec["a0"]) / (rec["a1"] - rec["a0"])
                fv = (rec["r1"] - r) / (rec["r1"] - rec["r0"])
                out.append(atlas_uv(region, fu, fv))
            else:
                out.append(atlas_uv(region, *EDGE[region]))
        elif mode == "disc":
            if front:
                out.append(atlas_uv(region, 0.5 + (u - rec["cu"]) / (2 * rec["r"]),
                                    0.5 - (z - rec["cz"]) / (2 * rec["r"])))
            else:
                out.append(atlas_uv(region, *EDGE[region]))
    return out


def set_uvs(obj, kind):
    """Box UVs in real-world metres (tile from the builder's material); atlas faces from
    their records."""
    mesh = obj.data
    while mesh.uv_layers:
        mesh.uv_layers.remove(mesh.uv_layers[0])
    uv = mesh.uv_layers.new(name="UVMap")
    mat_key = OBJ_MAT.get(kind) or BUILDER_MAT[kind]
    tile = LOOK[mat_key][1]
    rid_attr = mesh.attributes.get("rid")
    for poly in mesh.polygons:
        n = poly.normal
        if kind == "Atlas":
            rid = rid_attr.data[poly.index].value if rid_attr else 0
            rec = ATLAS.get(rid)
            cos = [mesh.vertices[mesh.loops[li].vertex_index].co for li in poly.loop_indices]
            uvs = atlas_face_uvs(rec, n, cos) if rec else [atlas_uv("spare2", 0.5, 0.5)] * len(cos)
            for li, t in zip(poly.loop_indices, uvs):
                uv.data[li].uv = t
            continue
        h = math.hypot(n.x, n.y)
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            if 0.25 < abs(n.z) < 0.97:                   # slopes: along the slope
                tx, ty = -n.y / h, n.x / h
                u, v = co.x * tx + co.y * ty, co.z / h
            elif abs(n.z) >= 0.97:
                u, v = co.x, co.y
            else:                                        # vertical: along the face
                tx, ty = -n.y / h, n.x / h
                u, v = co.x * tx + co.y * ty, co.z
            uv.data[li].uv = (u / tile, v / tile)


def add_tint(obj, rgb):
    attr = obj.data.color_attributes.new("Tint", "FLOAT_COLOR", "CORNER")
    data = np.tile(np.array([*rgb, 1.0], dtype=np.float32), len(obj.data.loops))
    attr.data.foreach_set("color", data)


# The shell's front and Bloomfield faces are split where other parts cover them, so the
# covered pieces become separate faces and are deleted below.
FRONT_CUTS = [((0, 0, FL), (0, 0, 1)), ((0, 0, 3.95), (0, 0, 1)), ((0, 0, 4.70), (0, 0, 1)),
              ((2.25, 0, 0), (1, 0, 0)), ((-2.25, 0, 0), (1, 0, 0)), ((2.60, 0, 0), (1, 0, 0)),
              ((-2.60, 0, 0), (1, 0, 0)), ((7.62, 0, 0), (1, 0, 0)), ((-7.62, 0, 0), (1, 0, 0))]
SIDE_CUTS = [((0, 0, FL), (0, 0, 1)), ((0, 0, 0.30), (0, 0, 1))]


def bisect_faces(obj, select, cuts):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for co, no in cuts:
        faces = [f for f in bm.faces if select(f)]
        edges = list({e for f in faces for e in f.edges})
        verts = list({v for f in faces for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=verts + edges + faces, dist=1e-4, plane_co=co, plane_no=no)
    bm.to_mesh(obj.data)
    bm.free()


parts = [o for o in col.objects if o.type == "MESH"]
for obj in parts:
    kind = obj.name[3:]
    if kind == "Shell":
        bisect_faces(obj, lambda f: f.normal.y < -0.99 and abs(f.calc_center_median().y) < 0.01, FRONT_CUTS)
        bisect_faces(obj, lambda f: f.normal.x > 0.99 and abs(f.calc_center_median().x - HW) < 0.01, SIDE_CUTS)
        bisect_faces(obj, lambda f: f.normal.y > 0.99 and abs(f.calc_center_median().y - FY1) < 0.01, SIDE_CUTS[1:])
    set_uvs(obj, kind)
    add_tint(obj, TINTS.get(kind, (1.0, 1.0, 1.0)))
    obj.data.materials[0] = FINAL[OBJ_MAT.get(kind) or BUILDER_MAT[kind]]
    if obj.data.attributes.get("rid"):
        obj.data.attributes.remove(obj.data.attributes["rid"])

# 3. Join, drop hidden faces, unwrap the lightmap UVs --------------------------
r_obj = bpy.data.objects["RB_Shell"]
with bpy.context.temp_override(active_object=r_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
r_obj.name = r_obj.data.name = "ReaBuilding"
mesh = r_obj.data
for name in [a.name for a in mesh.attributes if a.name == "rid"]:
    mesh.attributes.remove(mesh.attributes[name])
# merge the duplicate material slots left by the join (one slot per material)
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
    """Points spread over the face (about one per 0.01 m2, 6 to 3000), pulled a little in
    from the edges so a face only covered by a touching solid does not see past it."""
    area = f.calc_area()
    n = int(min(3000, max(6, area / 0.01)))
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
    """Delete faces that no ray from any of their sample points can leave the model
    through (inside walls, under trim, behind glass). Downward faces at grade go too."""
    import random
    rng = random.Random(7)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    bvh = BVHTree.FromBMesh(bm)
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
# Give the lightmap's pixels to what matters: the front, the Bloomfield side and the cupola.
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    f = 1.0
    c, n = p.center, p.normal
    if mat_names[p.material_index] == "dark":
        f *= 0.6
    if n.z < -0.5:
        f *= 0.7                                   # soffits, awning undersides
    if n.x < -0.7 and c.z < 11.9:
        f *= 0.55                                  # north (passage) and Flats yard faces
    if n.y > 0.7 and c.z < 11.9:
        f *= 0.5                                   # rear walls
    if n.z > 0.5 and 10.5 < c.z < 12.0:
        f *= 0.45                                  # roofs, cornice tops
    if c.z > 12.0 and abs(c.x) < 2.5:
        f *= 1.3                                   # cupola
    if f != 1.0:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.0015, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig: sun, sky, ground, occluders (in RB_BakeRig, not exported) ---------------
scene = bpy.context.scene
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
rig.hide_viewport = False
rig.hide_render = False
sun = bpy.data.objects.get("RB_Sun")
if not sun:
    sun = bpy.data.objects.new("RB_Sun", bpy.data.lights.new("RB_Sun", "SUN"))
    rig.objects.link(sun)
sun.data.energy = 3.2
sun.data.color = (1.0, 0.80, 0.58)
sun.data.angle = math.radians(1.5)
to_sun = Vector(TO_SUN).normalized()            # about 21 degrees above the horizon
sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()


def rig_mat(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (*rgb, 1)
    return m


def rig_box(name, x0, x1, y0, y1, z0, z1, mat):
    """Bake-only box (rebuilt every run)."""
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


# ground: roads and the passage 0.15 below the sidewalk; the Main St sidewalk at 0
warm = rig_mat("RB_GroundWarm", (0.34, 0.28, 0.19))
rig_box("RB_Ground", -120, 120, -120, 120, -0.35, -0.15, warm)
rig_box("RB_Sidewalk", -120, HW, -4.33, 0.0, -0.35, 0.0, warm)
# occluders (PLAN.md Placement): the 44-46 frame building north of the passage, the Bank
# Building across Bloomfield Ave (front 1.39 m behind this one, 22.14 m along Main St)
rig_box("RB_Occ4446", -26.0, -10.28, -0.55, 16.0, 0.0, 8.0, rig_mat("RB_OccFrame", (0.45, 0.42, 0.36)))
rig_box("RB_OccBank", 20.48, 42.62, 1.39, 21.71, -0.15, 12.2, rig_mat("RB_OccBank", (0.30, 0.13, 0.08)))

if scene.world is None:
    scene.world = bpy.data.worlds.new("RB_Sky")
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

# Hide every other collection (and loose helper objects) from render while baking.
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
    """Cycles bakes into each material's active Image Texture node."""
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
    light_img = bake_target("RB_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask (RGB) ----------------------------------------------------------
    grime_mat = bpy.data.materials.get("RB_GrimeBake") or bpy.data.materials.new("RB_GrimeBake")
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

    def near(sock, centres, r0, r1):
        """1 within r0 of any centre, fading to 0 at r1."""
        d = None
        for c in centres:
            dd = math_op("ABSOLUTE", math_op("SUBTRACT", sock, c))
            d = dd if d is None else math_op("MINIMUM", d, dd)
        return map_range(d, r0, r1, 1.0, 0.0)

    # grime and splash on the bottom ~0.4 m (steps, plinths, water table), fading by 0.9 m
    height = map_range(Z, -0.15, 0.9, 0.78, 1.0)
    blotch = map_range(noise_tex(geo.outputs["Position"], 0.6, 6.0), 0.0, 1.0, 0.90, 1.03)
    stretch = N("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (4.0, 4.0, 0.18)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_n = noise_tex(stretch.outputs["Vector"], 1.7, 2.0)
    streaks = map_range(streak_n, 0.35, 0.75, 0.93, 1.0)
    # soot under the main cornice / pediment moulding (frieze 9.75 - 10.55), clean on top
    soot = math_op("ADD", map_range(Z, 9.0, 10.55, 1.0, 0.84), map_range(Z, 10.55, 10.62, 0.0, 0.16))
    ped = mult(map_range(Z, 10.62, 11.0, 0.0, 1.0), map_range(Z, 12.0, 12.15, 1.0, 0.0),
               map_range(NZ, -0.2, 0.2, 1.0, 0.0))                              # under the arch mouldings
    soot = math_op("SUBTRACT", soot, mult(ped, 0.10))
    # dark streaks below sills and keystones (front and Bloomfield windows) and bracket feet
    front = map_range(NY, -0.6, -0.8, 0.0, 1.0)
    south = map_range(NX, 0.6, 0.8, 0.0, 1.0)
    fx = near(X, list(FRONT_X), 0.30, 0.50)
    sy = near(Y, list(SOUTH_Y) + [16.60, 19.70], 0.30, 0.50)
    win_col = math_op("MAXIMUM", mult(front, fx), mult(south, sy))
    under_sill = math_op("ADD", math_op("ADD",
                         mult(map_range(Z, 4.0, 4.70, 0.0, 1.0), map_range(Z, 4.70, 4.73, 1.0, 0.0)),
                         mult(map_range(Z, 7.1, 7.73, 0.0, 1.0), map_range(Z, 7.73, 7.76, 1.0, 0.0))),
                         mult(map_range(Z, 0.7, 1.08, 0.0, 1.0), map_range(Z, 1.08, 1.11, 1.0, 0.0), south))
    drips = math_op("SUBTRACT", 1.0, mult(win_col, under_sill, map_range(streak_n, 0.3, 0.7, 0.16, 0.05)))
    brk = near(X, [-7.725, -7.475, -2.475, -2.225, 2.225, 2.475, 7.475, 7.725], 0.08, 0.16)
    under_brk = mult(front, brk, map_range(Z, 8.6, 9.7, 0.0, 1.0), map_range(Z, 9.7, 9.75, 1.0, 0.0))
    drips = math_op("SUBTRACT", drips, mult(under_brk, map_range(streak_n, 0.3, 0.7, 0.14, 0.04)))
    # chimney soot (top 12.60)
    chim = mult(map_range(X, 7.3, 7.4, 0.0, 1.0), map_range(Y, 10.9, 11.0, 0.0, 1.0), map_range(Y, 12.0, 12.1, 1.0, 0.0))
    chim_soot = math_op("SUBTRACT", 1.0, mult(chim, map_range(Z, 12.0, 12.6, 0.0, 0.45)))
    # worn step treads in front of the doors (48 and 52 shop doors, the two arch doors)
    up = map_range(NZ, 0.8, 0.95, 0.0, 1.0)
    on_steps = mult(map_range(Y, 0.05, 0.0, 0.0, 1.0), map_range(Z, 0.62, 0.66, 1.0, 0.0))
    doors = near(X, [-5.11, 5.11, -1.45, 1.45], 0.35, 0.80)
    wear = map_range(mult(doors, up, on_steps), 0.0, 1.0, 1.0, 0.80)
    # treads generally a touch darker
    treads = map_range(mult(up, on_steps), 0.0, 1.0, 1.0, 0.93)
    # north wall and the passage: darker toward the ground
    north = map_range(NX, -0.6, -0.8, 0.0, 1.0)
    n_low = map_range(mult(north, map_range(Z, 0.0, 4.0, 1.0, 0.0)), 0.0, 1.0, 1.0, 0.85)
    # cupola: chalky, darker under its cornice
    cup = mult(map_range(Z, 12.0, 12.2, 0.0, 1.0), map_range(math_op("ABSOLUTE", X), 2.2, 2.4, 1.0, 0.0))
    cup_soot = math_op("SUBTRACT", 1.0, mult(cup, map_range(Z, 14.1, 14.7, 0.0, 0.12), map_range(Z, 14.7, 14.72, 1.0, 0.0)))
    cup_chalk = map_range(mult(cup, map_range(noise_tex(geo.outputs["Position"], 2.5, 4.0), 0.35, 0.7, 0.0, 1.0)),
                          0.0, 1.0, 1.0, 1.05)
    # awnings: sun-bleached on top (upward faces of the canvas), soiled valance hems
    canvas_top = mult(map_range(Y, -0.1, -0.2, 0.0, 1.0), map_range(Y, -2.25, -2.15, 0.0, 1.0),
                      map_range(Z, 2.6, 2.7, 0.0, 1.0), map_range(Z, 3.4, 3.5, 1.0, 0.0), up)
    bleach = map_range(canvas_top, 0.0, 1.0, 1.0, 1.06)
    hem = mult(map_range(Y, -2.25, -2.20, 1.0, 0.0), map_range(Y, -2.22, -2.19, 0.0, 1.0),
               map_range(Z, 2.40, 2.55, 1.0, 0.0))
    hem_dirt = map_range(hem, 0.0, 1.0, 1.0, 0.86)
    grey = mult(height, blotch, streaks, soot, drips, chim_soot, wear, treads, n_low, cup_soot, cup_chalk,
                bleach, hem_dirt)
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    # shaded north side a touch cooler and greyer near the ground; dull tin roofs
    col_n = vmix(mult(north, map_range(Z, 0.0, 3.0, 1.0, 0.0)), (1.0, 1.0, 1.0), (0.95, 0.97, 0.96))
    attr = N("ShaderNodeAttribute")
    attr.attribute_name = "Tint"
    rgb = vmul(vmul(gc.outputs["Vector"], col_n), attr.outputs["Color"])
    L(rgb, emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    grime_img = bake_target("RB_Grime", True)
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
# Warm the shade: sky-only light is blue; pull each pixel toward a warm grey of the same
# brightness, much more in the shade than in the sun, so the north wall and the shaded parts
# stay warm while the sunlit front does not turn yellow.
lum = combined.mean(axis=1, keepdims=True)
ref = np.percentile(lum[baked], 99.0)
shade = np.clip(1.0 - lum / (0.9 * ref), 0.0, 1.0)
w = 0.12 + 0.63 * shade
combined = combined * (1 - w) + lum * np.array([[1.0, 0.94, 0.80]]) * w
scale = float(np.percentile(combined[baked].max(axis=1), 99.5))
# Fill every unbaked pixel (gaps between islands) from its baked neighbours.
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
out_img = bpy.data.images.get("RB_Lightmap") or bpy.data.images.new("RB_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
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

# Remove the bake helper nodes and the tint attribute so they are not exported.
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
r_obj["lightmap_scale"] = LIGHTMAP_SCALE            # read by rea_building_preview.py
