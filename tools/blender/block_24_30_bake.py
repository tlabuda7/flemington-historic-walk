"""
block_24_30_bake.py - textures and baked lighting for the three frame buildings at 24-30 Main St
(24 dwelling, 26 Mill'y, 28-30 Conf'y / Barber), then export to assets/models/block-24-30.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/block_24_30_bake.py").read())

Steps (pattern: block_32_38_bake.py; section-E windows as store_100_102_bake.py):
 1. Rebuild the geometry (block_24_30.py).
 2. Ten materials, all textures reused (merged into one draw call by `baked-lighting`, plus
    the glass):
      clap_24     house-65-main/clapboard_cream.jpg, tile 1.0 m, untinted (its palest: off-white,
                  avg #E5DFCC; spec #E2DED2 cannot be reached by a factor, blue would exceed 1)
      clap_26     the same, x factor -> cream #D9C9A3 (spec #D8CFB8, made a touch yellower so it
                  reads apart from 24 beside it)
      clap_2830   the same, x factor -> drab buff #BBAE90 (spec #C4B99F, a touch deeper)
      trim        polyhaven/trim_paint_cream.jpg, tile 2.0 m, x factor -> #DDD5C2
      roof_tin    county-offices/roof_tin_redbrown.jpg, tile 2.0 m; bake tint a touch greyer
                  (dulled), 24's rear porch darker (weathered shingle, map "x")
      roof_slate  polyhaven/roof_slates_03.jpg, tile 1.5 m (24's two gable roofs, map "o")
      shopfront   county-offices/door_varnish_dark.jpg, tile 0.8 m, x factor -> #2E2E26
      deck        polyhaven/weathered_planks.jpg, tile 2.0 m, boards running front to back
      WindowBack  shared/window_backs.jpg cells (blinds, lace, curtains; the shop cells for the
                  shop windows, the bay and the shop-door lights)
      glass       plain #1A1916, alpha 0.40, roughness 0.05, BLEND, single-sided; not
                  lightmapped in the scene (`glass-reflect`); fully transparent during the bake
 3. Split wall faces where other parts cover them, join, delete the faces nobody can see,
    unwrap "Lightmap" (fronts, porches and the gap walls weighted up; roofs and rears down).
 4. Bake warm late-afternoon sun + sky into one 2K lightmap with Cycles. East side of Main St
    (front faces west): to-sun (0.40, -0.90, 0.36). Bake-only occluder (not exported): the
    built block-32-38.glb to the south, shifted into place. Every other collection is hidden
    from render during the bake.
 5. Bake an RGB grime mask (dirt band on the bottom 0.4 m, soot under the eaves and porch
    roofs, drips under the sills, chalky side walls on the gaps, decks darker at the doors,
    dull tin with rust streaks) and multiply it in.
 6. Fill empty lightmap pixels, warm the shade, save the sRGB JPEG, print LIGHTMAP_SCALE,
    export the GLB (TEXCOORD_0 + TEXCOORD_1).
"""

import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
TX = PROJECT + r"\assets\textures" + "\\"
GLB = PROJECT + r"\assets\models\block-24-30.glb"
GLB_3238 = PROJECT + r"\assets\models\block-32-38.glb"
LIGHTMAP = PROJECT + r"\assets\textures\block-24-30-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 384
TO_SUN = (0.40, -0.90, 0.36)          # east-side building (front faces west)
COLL, RIG = "Block2430", "HS_BakeRig"
OFF_3238 = (21.61, 1.25, 0.0)         # block-32-38 local -> this frame (its origin (8.54, -130.755))

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\block_24_30.py").read())

# 2. Materials ----------------------------------------------------------------
def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    """Constant colour that turns a texture averaging `avg` (sRGB 0-255) into `target`."""
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


GLASS_ALPHA = 0.40
GLASS_RGB = (0x1A, 0x19, 0x16)        # faint warm grey dust tint (section E)
SHARED = TX + "shared" + "\\"
CLAP = (229, 223, 204)                # clapboard_cream.jpg average (sRGB)
# material -> (texture file, metres per repeat, roughness, plain colour (linear) or None, factor or None)
LOOK = {
    "Clap24":   (TX + r"house-65-main\clapboard_cream.jpg", 1.0, 0.85, None, None),    # the map as is: the palest
    "Clap26":   (TX + r"house-65-main\clapboard_cream.jpg", 1.0, 0.85, None, tint(CLAP, (0xD9, 0xC9, 0xA3))),
    "Clap2830": (TX + r"house-65-main\clapboard_cream.jpg", 1.0, 0.85, None, tint(CLAP, (0xBB, 0xAE, 0x90))),
    "Trim":  (TX + r"polyhaven\trim_paint_cream.jpg", 2.0, 0.7, None, tint((230, 218, 191), (0xDD, 0xD5, 0xC2))),
    "Roof":  (TX + r"county-offices\roof_tin_redbrown.jpg", 2.0, 0.6, None, None),
    "Slate": (TX + r"polyhaven\roof_slates_03.jpg", 1.5, 0.75, None, None),
    "Wood":  (TX + r"county-offices\door_varnish_dark.jpg", 0.8, 0.5, None, tint((58, 42, 31), (0x2E, 0x2E, 0x26))),
    "Deck":  (TX + r"polyhaven\weathered_planks.jpg", 2.0, 0.9, None, None),
    "WBack": (SHARED + "window_backs.jpg", 1.0, 0.9, None, None),
    "Glass": (None, 1.0, 0.05, tuple(srgb_to_lin(c) for c in GLASS_RGB), None),
}
FINAL_NAMES = {"Clap24": "clap_24", "Clap26": "clap_26", "Clap2830": "clap_2830", "Trim": "trim",
               "Roof": "roof_tin", "Slate": "roof_slate", "Wood": "shopfront", "Deck": "deck",
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
    if name == "glass":   # transparent, drawn with a sky reflection by the scene
        bsdf.inputs["Alpha"].default_value = GLASS_ALPHA
        mat.use_backface_culling = True
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        elif hasattr(mat, "blend_method"):
            mat.blend_method = "BLEND"
    return mat


FINAL = {k: textured_material(FINAL_NAMES[k], LOOK[k][0], *LOOK[k][2:]) for k in LOOK}

# Bake tints per builder (multiplied into the lightmap through the grime mask)
TINTS = {"Roof": (0.88, 0.90, 0.94),          # dulled tin
         "Shingle": (0.55, 0.53, 0.52)}       # weathered shingle on the Mill'y rear porch
OBJ_MAT = dict(SHELL_MAT)


def set_uvs(obj, kind):
    """Box UVs in real-world metres (tile from the builder's material); window backs from
    their atlas cells."""
    mesh = obj.data
    while mesh.uv_layers:
        mesh.uv_layers.remove(mesh.uv_layers[0])
    uv = mesh.uv_layers.new(name="UVMap")
    mat_key = OBJ_MAT.get(kind) or BUILDER_MAT[kind]
    tile = LOOK[mat_key][1]
    rid_attr = mesh.attributes.get("rid")
    for poly in mesh.polygons:
        n = poly.normal
        if kind == "WBack":                              # window backs: their atlas cell
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


def on(f, axis, value, sign):
    c = f.calc_center_median()
    n = f.normal
    return getattr(n, axis) * sign > 0.99 and abs(getattr(c, axis) - value) < 0.01


# planes of the roofs that cover the bottom of a taller neighbour's wall
s_b = (B_TOP_R - B_TOP_F) / (BY1 - BFW)
B_PLANE = ((0, BFW, B_TOP_F), (0, -s_b, 1))                       # 26's shed roof
A2_N = ((AX0, 0, A2_EAVE), (-T30, 0, 1))                         # 24 rear part, both slopes
A2_S = ((A2X1, 0, A2_EAVE), (T30, 0, 1))
LOW = ((0, 0, LOW_TOP), (0, 0, 1))
SPLITS = {
    # name: [(select, cuts)]
    "ShellA1": [(lambda f: on(f, "x", AX1, 1), [B_PLANE]),
                (lambda f: on(f, "y", AY1, 1), [((A2X1, 0, 0), (1, 0, 0)), LOW, A2_N, A2_S])],
    "ShellB1": [(lambda f: on(f, "x", BX0, -1), [((0, 0, A_EAVE), (0, 0, 1))]),
                (lambda f: on(f, "y", BY1, 1), [LOW])],
    "ShellB2a": [(lambda f: on(f, "y", B2A[3], 1), [((B2B[0], 0, 0), (1, 0, 0))])],
    "ShellA2": [(lambda f: on(f, "x", A2X1, 1), [((0, B2A[3], 0), (0, 1, 0)), LOW]),
                (lambda f: on(f, "y", A2Y1, 1), [LOW])],
    "ShellC1": [(lambda f: on(f, "y", CY1, 1), [((C3[0], 0, 0), (1, 0, 0)), LOW])],
}

parts = [o for o in col.objects if o.type == "MESH"]
for obj in parts:
    kind = obj.name[3:]
    for select, cuts in SPLITS.get(kind, []):
        bisect_faces(obj, select, cuts)
    set_uvs(obj, kind)
    add_tint(obj, TINTS.get(kind, (1.0, 1.0, 1.0)))
    obj.data.materials[0] = FINAL[OBJ_MAT.get(kind) or BUILDER_MAT[kind]]
    if obj.data.attributes.get("rid"):
        obj.data.attributes.remove(obj.data.attributes["rid"])

# 3. Join, drop hidden faces, unwrap the lightmap UVs --------------------------
r_obj = bpy.data.objects["HS_ShellA1"]
with bpy.context.temp_override(active_object=r_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
r_obj.name = r_obj.data.name = "Block2430"
mesh = r_obj.data
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
    # the glass does not block the view: rays pass it to reach (or leave) the window backs
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
# Give the lightmap's pixels to what matters: the fronts, the porches and the gap walls.
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    f = 1.0
    c, n = p.center, p.normal
    m = mat_names[p.material_index]
    if m == "glass":
        f *= 0.03                                  # not lightmapped in the scene
    elif m == "WindowBack":
        f *= 0.6
    if n.z < -0.5:
        f *= 0.7                                   # soffits, porch ceilings
    if n.y < -0.7 and c.y < CFW + 0.5:
        f *= 1.15                                  # the fronts
    if n.y > 0.7 and c.y > 9.0:
        f *= 0.5                                   # rear walls
    if abs(n.x) > 0.7 and c.y > 11.0:
        f *= 0.7                                   # side walls of the rear parts
    if m in ("roof_tin", "roof_slate") and n.z > 0.5 and c.z > 3.6:
        f *= 0.4                                   # main roofs (barely seen)
    if f != 1.0:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.0015, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig: sun, sky, ground, occluder (in HS_BakeRig, not exported) ---------------
scene = bpy.context.scene
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
rig.hide_viewport = False
rig.hide_render = False
sun = bpy.data.objects.get("HS_Sun")
if not sun:
    sun = bpy.data.objects.new("HS_Sun", bpy.data.lights.new("HS_Sun", "SUN"))
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


def rig_slab(name, pts, z0, z1, mat):
    """Bake-only plan slab (rebuilt every run)."""
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    m = bpy.data.meshes.new(name)
    bm = bmesh.new()
    a = [bm.verts.new((x, y, z0)) for x, y in pts]
    b = [bm.verts.new((x, y, z1)) for x, y in pts]
    faces = [bm.faces.new(a), bm.faces.new(b[::-1])]
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    bm.to_mesh(m)
    bm.free()
    m.materials.append(mat)
    o = bpy.data.objects.new(name, m)
    rig.objects.link(o)
    return o


# ground: road and yards 0.15 below the sidewalk. The east road edge slants (street-geometry
# addendum 9.2: scene x = 6.40 + 0.0321 (z + 89.9)), i.e. local y = -2.895 + 0.0321 X; the walk
# runs from it to the fronts.
warm = rig_mat("HS_GroundWarm", (0.34, 0.28, 0.19))
rig_box("HS_Ground", -120, 120, -120, 120, -0.35, -0.15, warm)
edge = lambda x: -2.895 + 0.0321 * x
rig_slab("HS_Sidewalk", [(-60, edge(-60)), (60, edge(60)), (60, 1.94), (-60, 1.94)], -0.35, 0.0, warm)
# occluder (PLAN.md Placement): the built 32-38 to the south
old = bpy.data.objects.get("HS_Occ3238")
if old:
    bpy.data.objects.remove(old, do_unlink=True)
before_objs = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_3238)
for o in [o for o in bpy.data.objects if o not in before_objs]:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    rig.objects.link(o)
    o.location = Vector(OFF_3238)
    o.name = "HS_Occ3238"
    o.select_set(False)
    for slot in o.material_slots:                  # its glass fully transparent, like ours
        if slot.material and slot.material.name.startswith("glass"):
            bsdf = next(n for n in slot.material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            bsdf.inputs["Alpha"].default_value = 0.0

if scene.world is None:
    scene.world = bpy.data.worlds.new("HS_Sky")
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
glass_alpha = next(n for n in FINAL["Glass"].node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"]
glass_alpha.default_value = 0.0             # light passes the panes to the window backs
try:
    light_img = bake_target("HS_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask (RGB) ----------------------------------------------------------
    grime_mat = bpy.data.materials.get("HS_GrimeBake") or bpy.data.materials.new("HS_GrimeBake")
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

    # dirt band and splash on the bottom ~0.4 m, fading by 0.9 m
    height = map_range(Z, -0.15, 0.9, 0.80, 1.0)
    blotch_n = noise_tex(geo.outputs["Position"], 0.6, 6.0)
    blotch = map_range(blotch_n, 0.0, 1.0, 0.90, 1.03)
    stretch = N("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (4.0, 4.0, 0.18)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_n = noise_tex(stretch.outputs["Vector"], 1.7, 2.0)
    streaks = map_range(streak_n, 0.35, 0.75, 0.93, 1.0)
    front = map_range(NY, -0.6, -0.8, 0.0, 1.0)
    on_front = mult(front, map_range(Y, CFW + 0.30, CFW + 0.10, 0.0, 1.0),
                    map_range(Y, AFW - 0.20, AFW - 0.05, 0.0, 1.0))
    is_c = map_range(X, 2.0, 2.5, 0.0, 1.0)                   # 28-30
    not_c = math_op("SUBTRACT", 1.0, is_c)
    is_b = mult(map_range(X, BX0 - 0.05, BX0 + 0.05, 0.0, 1.0), not_c)    # 26
    # soot under the porch roofs (front walls), under 26's boxed eave and both tiers at 28-30
    band_ab = mult(not_c, map_range(Z, 2.4, 3.10, 0.0, 0.16), map_range(Z, 3.10, 3.40, 1.0, 0.0))
    band_c = mult(is_c, math_op("ADD",
                                mult(map_range(Z, 2.5, 3.08, 0.0, 0.16), map_range(Z, 3.08, 3.12, 1.0, 0.0)),
                                mult(map_range(Z, 5.0, 5.68, 0.0, 0.16), map_range(Z, 5.68, 5.72, 1.0, 0.0))))
    band_b = mult(is_b, map_range(Z, 5.0, 5.88, 0.0, 0.14), map_range(Z, 5.88, 5.90, 1.0, 0.0))
    soot = math_op("SUBTRACT", 1.0, mult(on_front, math_op("ADD", math_op("ADD", band_ab, band_c), band_b)))
    # dark streaks below the upper window sills
    fx = near(X, [-10.10, -8.00, -6.10, -3.60, -1.40, 4.15, 9.95], 0.35, 0.55)
    under_sill = mult(map_range(Z, 3.20, 3.70, 0.0, 1.0), map_range(Z, 3.70, 3.86, 1.0, 0.0))
    drips = math_op("SUBTRACT", 1.0, mult(front, fx, under_sill, map_range(streak_n, 0.3, 0.7, 0.16, 0.05)))
    # porch decks: darker toward the wall and at the doors (wear)
    up = map_range(NZ, 0.8, 0.95, 0.0, 1.0)
    deck = mult(up, map_range(Z, 0.10, 0.14, 0.0, 1.0), map_range(Z, 0.20, 0.185, 0.0, 1.0),
                map_range(Y, -0.05, 0.05, 0.0, 1.0), map_range(Y, CFW + 0.05, CFW - 0.05, 0.0, 1.0))
    wall_band = math_op("ADD", mult(not_c, map_range(Y, 0.7, AFW, 0.0, 1.0)),
                        mult(is_c, map_range(Y, 1.2, CFW, 0.0, 1.0)))
    doors_x = near(X, [-6.10, -0.90, 6.20, 7.95], 0.35, 0.90)
    wear = mult(deck, math_op("ADD", mult(wall_band, 0.10), mult(doors_x, map_range(Y, 0.3, 1.2, 0.0, 1.0), 0.12)))
    deck_dark = math_op("SUBTRACT", 1.0, wear)
    # side walls on the gaps: chalky (faded, a touch lighter, blotchy)
    side = map_range(math_op("ABSOLUTE", NX), 0.6, 0.8, 0.0, 1.0)
    chalk_amt = mult(side, map_range(Z, 0.6, 1.2, 0.0, 1.0), map_range(blotch_n, 0.3, 0.7, 0.6, 1.0))
    chalk = map_range(chalk_amt, 0.0, 1.0, 1.0, 1.05)
    # tin roofs: dull, darker and rusty in streaks (slate on 24 left alone)
    roof_up = mult(map_range(NZ, 0.55, 0.75, 0.0, 1.0), map_range(Z, 2.3, 2.5, 0.0, 1.0))
    slate = mult(map_range(X, AX1 + 0.05, AX1 - 0.05, 0.0, 1.0), map_range(Z, 5.2, 5.4, 0.0, 1.0))
    tin = mult(roof_up, math_op("SUBTRACT", 1.0, slate))
    rust_n = noise_tex(stretch.outputs["Vector"], 3.1, 3.0)
    rust_amt = mult(tin, map_range(rust_n, 0.40, 0.70, 0.0, 1.0))
    rust = map_range(rust_amt, 0.0, 1.0, 1.0, 0.86)
    grey = mult(height, blotch, streaks, soot, drips, deck_dark, chalk, rust)
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    col_n = vmul(vmix(chalk_amt, (1.0, 1.0, 1.0), (0.96, 0.985, 1.0)),    # chalky paint: cooler
                 vmix(rust_amt, (1.0, 1.0, 1.0), (1.0, 0.88, 0.78)))          # rust: redder
    attr = N("ShaderNodeAttribute")
    attr.attribute_name = "Tint"
    rgb = vmul(vmul(gc.outputs["Vector"], col_n), attr.outputs["Color"])
    L(rgb, emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    grime_img = bake_target("HS_Grime", True)
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
# brightness, much more in the shade than in the sun.
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
out_img = bpy.data.images.get("HS_Lightmap") or bpy.data.images.new("HS_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
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
print("exported", GLB, "|", tris, "triangles |", len(mesh.materials), "materials:",
      [m.name for m in mesh.materials])
r_obj["lightmap_scale"] = LIGHTMAP_SCALE            # read by block_24_30_preview.py
