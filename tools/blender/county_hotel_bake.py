"""
county_hotel_bake.py - textures and baked lighting for the County Hotel (47-49 Main St), then
export to assets/models/county-hotel.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/county_hotel_bake.py").read())

Steps (pattern: rea_building_bake.py):
 1. Rebuild the geometry (county_hotel.py).
 2. Ten lightmapped materials (merged into one draw call by `baked-lighting`) and glass:
      walls      county-hotel/brick_painted_cream.jpg, tile 1.4 m (painted brick #D8CDB4)
      trim       courthouse/paint_white.jpg, tile 2.0 m, x factor -> off-white #E0DACB
      shutters   polyhaven/door_paint_green.jpg, tile 1.0 m, x factor -> dark green #34432F (doors)
      dark       plain tin grey #4A4C50 (roofs); etched glass and iron by bake tints
      brick      polyhaven/red_brick.jpg, tile 1.4 m, x factor -> #8A4030 (chimneys)
      paving     lovells-restaurant/stone_bluestone.jpg, tile 2.0 m (veranda flags, steps)
      clapboard  house-65-main/clapboard_cream.jpg, tile 1.6 m (Bar & Pool Room wing)
      signs      county-hotel/signs_atlas.jpg (tools/prepare_county_hotel_textures.py): shutter
                 louvres, X-panel post faces, "COUNTY HOTEL" lantern panes
      WindowBack shared/window_backs.jpg cells (blinds, lace, curtains, dark rooms)
      HotelLobby shared/hotel_lobby.jpg cells (ground-floor windows under the veranda, the
                 main door's transom)
      glass      plain #1A1916, alpha 0.40, BLEND, single-sided; not lightmapped in the scene
                 (`glass-reflect`); fully transparent during the bake, ignored by the hidden-face pass
    Windows: PLAN.md "E. Windows that don't read as flat black" (rolled out here 2026-11-11, as
    on the Rea Building): the window backs keep the atlas UVs recorded by county_hotel.py
    (BACKREC) and are lightmapped like everything else; the glass keeps Lightmap UVs (squeezed
    to almost nothing) but the scene draws it without the lightmap.
 3. Split the wall faces where the veranda, bay, wing and cornice cover them, join, delete the
    faces nobody can see, unwrap "Lightmap" (front, veranda and south side weighted up).
 4. Bake warm late-afternoon sun + sky into one 2K lightmap with Cycles. West side of Main St
    (front faces east): to-sun (-0.40, 0.90, 0.36) - the front and veranda are in shade, the
    south wall grazed, the rear sunlit. Bake-only occluder: the 39-41 building north of the
    hotel (7 m, as the scene placeholder). Other collections hidden from render.
 5. Bake an RGB grime mask and multiply it in.
 6. Fill empty lightmap pixels, warm the shade, save the sRGB JPEG, print LIGHTMAP_SCALE,
    export the GLB (TEXCOORD_0 + TEXCOORD_1).
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
GLB = PROJECT + r"\assets\models\county-hotel.glb"
LIGHTMAP = PROJECT + r"\assets\textures\county-hotel-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 384
TO_SUN = (-0.40, 0.90, 0.36)          # west-side building (front faces east)
COLL, RIG = "CountyHotel", "CH_BakeRig"
GLASS_ALPHA = 0.40
GLASS_RGB = (0x1A, 0x19, 0x16)        # faint warm grey dust tint (as the Rea Building, Nevius Store)

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\county_hotel.py").read())

# 2. Materials ----------------------------------------------------------------


def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    """Constant colour that turns a texture averaging `avg` (sRGB 0-255) into `target`."""
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


def ratio(target, base):
    return tuple(srgb_to_lin(t) / srgb_to_lin(b) for t, b in zip(target, base))


DARK_BASE = (0x4A, 0x4C, 0x50)
# material -> (texture file, metres per repeat, roughness, plain colour (linear) or None, factor or None)
LOOK = {
    "Walls":     (TX + r"county-hotel\brick_painted_cream.jpg", 1.4, 0.9, None, None),
    "Trim":      (TX + r"courthouse\paint_white.jpg", 2.0, 0.7, None, tint((242, 239, 230), (0xE0, 0xDA, 0xCB))),
    "Shutters":  (TX + r"polyhaven\door_paint_green.jpg", 1.0, 0.6, None, tint((93, 107, 92), (0x34, 0x43, 0x2F))),
    "Dark":      (None, 1.0, 0.4, tuple(srgb_to_lin(c) for c in DARK_BASE), None),
    "Brick":     (TX + r"polyhaven\red_brick.jpg", 1.4, 0.9, None, tint((142, 103, 80), (0x8A, 0x40, 0x30))),
    "Paving":    (TX + r"lovells-restaurant\stone_bluestone.jpg", 2.0, 0.9, None, None),
    "Clapboard": (TX + r"house-65-main\clapboard_cream.jpg", 1.6, 0.85, None, None),
    "Signs":     (TX + r"county-hotel\signs_atlas.jpg", 1.0, 0.8, None, None),
    "WBack":     (TX + r"shared\window_backs.jpg", 1.0, 0.9, None, None),
    "Lobby":     (TX + r"shared\hotel_lobby.jpg", 1.0, 0.9, None, None),
    "Glass":     (None, 1.0, 0.05, tuple(srgb_to_lin(c) for c in GLASS_RGB), None),
}
FINAL_NAMES = {k: k.lower() for k in LOOK}
FINAL_NAMES.update({"WBack": "WindowBack", "Lobby": "HotelLobby", "Glass": "glass"})


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
    if name == "glass":   # transparent, drawn with a sky reflection by the scene
        bsdf.inputs["Alpha"].default_value = GLASS_ALPHA
        mat.use_backface_culling = True
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        elif hasattr(mat, "blend_method"):
            mat.blend_method = "BLEND"
    return mat


FINAL = {k: textured_material(FINAL_NAMES[k], LOOK[k][0], *LOOK[k][2:]) for k in LOOK}

TINTS = {"Etched": ratio((0x62, 0x66, 0x66), DARK_BASE),
         "Iron": ratio((0x24, 0x26, 0x2A), DARK_BASE)}
# The whole front is in shade (the sun is behind the hotel) and most of its windows are under
# the veranda as well: the window backs on the front get this much more light in the lightmap,
# so the rooms still read behind the glass (as the Bank Building's shaded Bloomfield Ave cells).
FRONT_BACK_LIFT = {"Lobby": 1.6, "WBack": 1.3}

# Atlas boxes (pixels from the top-left; must match tools/prepare_county_hotel_textures.py)
REGIONS = {"louvre": (0, 0, 256, 640), "post2": (256, 0, 352, 1024), "post1": (352, 0, 448, 1024),
           "lantern": (448, 0, 704, 448), "white": (704, 0, 1024, 256), "green": (704, 256, 1024, 512),
           "spare": (0, 640, 256, 1024)}


def atlas_uv(region, fu, fv, inset=2):
    c0, r0, c1, r1 = REGIONS[region]
    col_ = c0 + inset + (c1 - c0 - 2 * inset) * min(max(fu, 0.0), 1.0)
    row = r0 + inset + (r1 - r0 - 2 * inset) * min(max(fv, 0.0), 1.0)
    return (col_ / 1024, 1 - row / 1024)


def atlas_face_uvs(rec, n, cos):
    out = []
    if rec["mode"] == "rect":
        (px, py), (nx, ny) = rec["wall"]
        tx, ty = -ny, nx
        front = n.x * nx + n.y * ny > 0.9
        for co in cos:
            if front:
                u = (co.x - px) * tx + (co.y - py) * ty
                out.append(atlas_uv(rec["region"], (u - rec["u0"]) / (rec["u1"] - rec["u0"]),
                                    (rec["z1"] - co.z) / (rec["z1"] - rec["z0"])))
            else:
                out.append(atlas_uv(rec.get("edge", "white"), 0.5, 0.5))
    elif rec["mode"] == "post":
        vertical = abs(n.z) < 0.5
        h = math.hypot(n.x, n.y) or 1.0
        tx, ty = -n.y / h, n.x / h
        for co in cos:
            if vertical:
                u = (co.x - rec["cx"]) * tx + (co.y - rec["cy"]) * ty
                out.append(atlas_uv(rec["region"], 0.5 + u / (2 * rec["hw"]),
                                    (rec["z1"] - co.z) / (rec["z1"] - rec["z0"])))
            else:
                out.append(atlas_uv("white", 0.5, 0.5))
    return out


def set_uvs(obj, kind):
    """Box UVs in real-world metres (tile from the builder's material); atlas faces from records."""
    mesh = obj.data
    while mesh.uv_layers:
        mesh.uv_layers.remove(mesh.uv_layers[0])
    uv = mesh.uv_layers.new(name="UVMap")
    mat_key = SHELL_MAT.get(kind) or BUILDER_MAT[kind]
    tile = LOOK[mat_key][1]
    rid_attr = mesh.attributes.get("rid")
    for poly in mesh.polygons:
        n = poly.normal
        if kind in ("WBack", "Lobby"):                   # window backs: their atlas cell
            rec = BACKREC[rid_attr.data[poly.index].value]
            (px, py), (nx, ny) = rec["wall"]
            U0, V0, U1, V1 = rec["uv"]
            for li in poly.loop_indices:
                co = mesh.vertices[mesh.loops[li].vertex_index].co
                u = (co.x - px) * -ny + (co.y - py) * nx
                fu = (u - rec["u0"]) / (rec["u1"] - rec["u0"])
                fz = (co.z - rec["z0"]) / (rec["z1"] - rec["z0"])
                uv.data[li].uv = (U0 + (U1 - U0) * fu, V0 + (V1 - V0) * fz)
            continue
        if kind == "Atlas":
            rid = rid_attr.data[poly.index].value if rid_attr else 0
            rec = ATLAS.get(rid)
            cos = [mesh.vertices[mesh.loops[li].vertex_index].co for li in poly.loop_indices]
            uvs = atlas_face_uvs(rec, n, cos) if rec else [atlas_uv("spare", 0.5, 0.5)] * len(cos)
            for li, t in zip(poly.loop_indices, uvs):
                uv.data[li].uv = t
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


def add_tint(obj, rgb, front_lift=1.0):
    """Per-corner bake tint; faces that look out to the street (-Y) get `front_lift` on top."""
    attr = obj.data.color_attributes.new("Tint", "FLOAT_COLOR", "CORNER")
    data = np.tile(np.array([*rgb, 1.0], dtype=np.float32), len(obj.data.loops)).reshape(-1, 4)
    if front_lift != 1.0:
        for poly in obj.data.polygons:
            if poly.normal.y < -0.9:
                data[list(poly.loop_indices), :3] *= front_lift
    attr.data.foreach_set("color", data.ravel())


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


Z = lambda z: ((0, 0, z), (0, 0, 1))
XP = lambda x: ((x, 0, 0), (1, 0, 0))
YP = lambda y: ((0, y, 0), (0, 1, 0))
slope = Vector((-(WING_Z[1] - WING_Z[0]), 0, HW - 5.55)).normalized()        # wing roof line
SHELL_CUTS = [
    (lambda f: f.normal.y < -0.99 and abs(f.calc_center_median().y - FY) < 0.01,
     [Z(0.0), Z(3.00), Z(3.10), Z(6.25), Z(6.57), Z(8.02), XP(ENC_X)]),
    (lambda f: f.normal.x < -0.99 and abs(f.calc_center_median().x + HW) < 0.01,
     [YP(7.00), YP(11.43), Z(3.50), Z(8.02)]),
    (lambda f: f.normal.x > 0.99 and abs(f.calc_center_median().x - HW) < 0.01, [Z(8.02)]),
    (lambda f: f.normal.y > 0.99 and abs(f.calc_center_median().y - RY) < 0.01,
     [XP(-5.55), ((-HW, RY, WING_Z[0]), tuple(slope)), Z(8.02)]),
]

parts = [o for o in col.objects if o.type == "MESH"]
for obj in parts:
    kind = obj.name[3:]
    if kind == "Shell":
        for sel, cuts in SHELL_CUTS:
            bisect_faces(obj, sel, cuts)
    if kind == "Paving":
        bisect_faces(obj, lambda f: f.normal.z > 0.99 and abs(f.calc_center_median().z) < 0.01, [XP(ENC_X)])
    set_uvs(obj, kind)
    add_tint(obj, TINTS.get(kind, (1.0, 1.0, 1.0)), FRONT_BACK_LIFT.get(kind, 1.0))
    obj.data.materials[0] = FINAL[SHELL_MAT.get(kind) or BUILDER_MAT[kind]]
    if obj.data.attributes.get("rid"):
        obj.data.attributes.remove(obj.data.attributes["rid"])

# 3. Join, drop hidden faces, unwrap the lightmap UVs --------------------------
c_obj = bpy.data.objects["CH_Shell"]
with bpy.context.temp_override(active_object=c_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
c_obj.name = c_obj.data.name = "CountyHotel"
mesh = c_obj.data
slots, remap = {}, []
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
    """Delete faces that no ray from any of their sample points can leave the model through."""
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
removed = remove_hidden_faces(c_obj)
after = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("hidden faces removed:", removed, "| triangles", before, "->", after)

lm = mesh.uv_layers.new(name="Lightmap")
mesh.uv_layers.active = lm
mesh.uv_layers["UVMap"].active_render = True
for o in bpy.context.view_layer.objects:
    o.select_set(o == c_obj)
bpy.context.view_layer.objects.active = c_obj
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003,
                         area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.object.mode_set(mode="OBJECT")
# Give the lightmap's pixels to what matters: the front, the veranda and the south side.
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    f = 1.0
    c, n = p.center, p.normal
    if mat_names[p.material_index] == "dark":
        f *= 0.6
    elif mat_names[p.material_index] == "glass":
        f *= 0.03                                  # not lightmapped in the scene
    elif mat_names[p.material_index] in ("WindowBack", "HotelLobby"):
        f *= 0.6
    if n.z < -0.5:
        f *= 0.75                                  # soffits, ceilings
    if n.x > 0.7 and c.y > FY + 0.1:
        f *= 0.5                                   # north wall (mostly behind 39-41)
    if n.y > 0.7:
        f *= 0.5                                   # rear walls
    if n.z > 0.5 and c.z > 8.9:
        f *= 0.45                                  # roof, cornice tops
    if c.y > RY + 0.05:
        f *= 0.6                                   # Bar & Pool Room wing
    if f != 1.0:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.0015, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig: sun, sky, ground, occluder (in CH_BakeRig, not exported) ---------------
scene = bpy.context.scene
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
rig.hide_viewport = False
rig.hide_render = False
sun = bpy.data.objects.get("CH_Sun")
if not sun:
    sun = bpy.data.objects.new("CH_Sun", bpy.data.lights.new("CH_Sun", "SUN"))
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


# ground: road, side lot and yards 0.15 below the sidewalk (local z 0 = sidewalk top)
warm = rig_mat("CH_GroundWarm", (0.34, 0.28, 0.19))
rig_box("CH_Ground", -120, 120, -120, 120, -0.35, -0.15, warm)
rig_box("CH_Sidewalk", -120, 120, -3.90, 0.0, -0.35, 0.0, warm)
# 39-41 Main north of the hotel (front 0.28 behind the hotel front; 7 m as the scene placeholder)
rig_box("CH_Occ3941", HW, 17.1, 2.80, 11.6, -0.15, 7.0, rig_mat("CH_OccBrick", (0.30, 0.15, 0.10)))

if scene.world is None:
    scene.world = bpy.data.worlds.new("CH_Sky")
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
    o.select_set(o == c_obj)
bpy.context.view_layer.objects.active = c_obj
glass_alpha = next(n for n in FINAL["Glass"].node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"]
glass_alpha.default_value = 0.0             # light passes the panes to the window backs
try:
    light_img = bake_target("CH_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask (RGB) ----------------------------------------------------------
    grime_mat = bpy.data.materials.get("CH_GrimeBake") or bpy.data.materials.new("CH_GrimeBake")
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
    X, Y, Zs = sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]
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
        d = None
        for c in centres:
            dd = math_op("ABSOLUTE", math_op("SUBTRACT", sock, c))
            d = dd if d is None else math_op("MINIMUM", d, dd)
        return map_range(d, r0, r1, 1.0, 0.0)

    def band(sock, a, b, ramp):
        """1 between a and b, fading over `ramp` outside."""
        return mult(map_range(sock, a - ramp, a, 0.0, 1.0), map_range(sock, b, b + ramp, 1.0, 0.0))

    up = map_range(NZ, 0.8, 0.95, 0.0, 1.0)
    front = map_range(NY, -0.6, -0.8, 0.0, 1.0)
    south = map_range(NX, -0.6, -0.8, 0.0, 1.0)
    # dark scuffing on the lower 0.6 m of walls and post plinths, fading by 1.0 m
    height = map_range(Zs, -0.15, 1.0, 0.80, 1.0)
    blotch = map_range(noise_tex(geo.outputs["Position"], 0.6, 6.0), 0.0, 1.0, 0.90, 1.03)
    stretch = N("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (4.0, 4.0, 0.18)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_n = noise_tex(stretch.outputs["Vector"], 1.7, 2.0)
    streaks = map_range(streak_n, 0.35, 0.75, 0.93, 1.0)
    # soot under the main cornice (frieze 8.10-8.75) and the porch cornice (5.75-6.25)
    soot = mult(map_range(Zs, 7.4, 8.75, 1.0, 0.84), map_range(Zs, 8.75, 8.80, 0.0, 1.0))
    soot = math_op("ADD", soot, map_range(Zs, 8.75, 8.80, 1.0, 0.0))
    soot = math_op("MINIMUM", soot, 1.0)
    porch_soot = map_range(mult(band(Zs, 5.30, 6.25, 0.30), map_range(Y, 2.6, 2.4, 0.0, 1.0)), 0.0, 1.0, 1.0, 0.90)
    # grey streaks below the 3rd-floor sills (front and south) and the main bracket feet
    fx = near(X, THIRD_X, 0.30, 0.50)
    sy = near(Y, list(SOUTH_Y3), 0.30, 0.50)
    win_col = math_op("MAXIMUM", mult(front, fx), mult(south, sy))
    under_sill = band(Zs, 6.0, 6.62, 0.05)
    drips = math_op("SUBTRACT", 1.0, mult(win_col, under_sill, map_range(streak_n, 0.3, 0.7, 0.16, 0.05)))
    brk = near(X, FRONT_BR, 0.05, 0.12)
    under_brk = mult(front, brk, band(Zs, 7.4, 8.12, 0.05), map_range(Y, FY + 0.1, FY - 0.02, 0.0, 1.0))
    drips = math_op("SUBTRACT", drips, mult(under_brk, map_range(streak_n, 0.3, 0.7, 0.12, 0.04)))
    # south wall: chalkier and a little dirtier
    south_dirt = map_range(mult(south, map_range(X, -11.8, -11.95, 0.0, 1.0),
                                map_range(noise_tex(geo.outputs["Position"], 1.8, 4.0), 0.3, 0.7, 0.0, 1.0)),
                           0.0, 1.0, 0.97, 0.90)
    # paving: darker and worn along the door line and at the bay-3 entrance
    on_pav = mult(up, map_range(Zs, 0.02, 0.0, 0.0, 1.0), map_range(Y, -0.05, 0.05, 0.0, 1.0),
                  map_range(Y, FY + 0.35, FY + 0.30, 0.0, 1.0))
    door_line = map_range(Y, 1.4, 2.4, 0.0, 1.0)
    entrance = mult(near(X, [BAY_C[2], -9.40], 0.5, 1.4), map_range(Y, 0.0, 1.8, 0.0, 1.0))
    wear = map_range(mult(on_pav, math_op("MAXIMUM", mult(door_line, 0.6), entrance)), 0.0, 1.0, 1.0, 0.80)
    pav_dark = map_range(on_pav, 0.0, 1.0, 1.0, 0.94)
    # railing paint a little grey (upper deck rails and lattice)
    rail = mult(band(Zs, 3.18, 4.02, 0.01), math_op("MAXIMUM", map_range(Y, 0.25, 0.20, 0.0, 1.0),
                                                     map_range(X, -11.6, -11.7, 0.0, 1.0)))
    rail_grey = map_range(rail, 0.0, 1.0, 1.0, 0.92)
    # chimney tops sooty
    chim = mult(map_range(math_op("ABSOLUTE", X), HW - 0.65, HW - 0.55, 0.0, 1.0), band(Y, 4.0, 5.0, 0.05))
    chim_soot = math_op("SUBTRACT", 1.0, mult(chim, map_range(Zs, 9.3, 10.3, 0.0, 0.45)))
    # Bar & Pool Room wing: greyer than the hotel
    wing = mult(map_range(Y, RY + 0.02, RY + 0.08, 0.0, 1.0), map_range(Zs, 4.3, 4.4, 1.0, 0.0))
    wing_grey = map_range(wing, 0.0, 1.0, 1.0, 0.88)
    # tin roofs dull
    roof = mult(up, map_range(Zs, 6.3, 6.4, 0.0, 1.0))
    roof_dull = map_range(roof, 0.0, 1.0, 1.0, 0.92)
    grey = mult(height, blotch, streaks, soot, porch_soot, drips, south_dirt, wear, pav_dark, rail_grey,
                chim_soot, wing_grey, roof_dull)
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    # rust stain under the lamp lantern; the wing a touch cooler
    lamp = mult(near(X, [LX], 0.06, 0.25), near(Y, [LY], 0.06, 0.25), band(Zs, 2.6, 3.05, 0.1))
    col_rust = vmix(lamp, (1.0, 1.0, 1.0), (1.25, 0.85, 0.65))
    col_wing = vmix(wing, (1.0, 1.0, 1.0), (0.97, 0.98, 0.99))
    attr = N("ShaderNodeAttribute")
    attr.attribute_name = "Tint"
    rgb = vmul(vmul(vmul(gc.outputs["Vector"], col_rust), col_wing), attr.outputs["Color"])
    L(rgb, emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    grime_img = bake_target("CH_Grime", True)
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
# brightness, much more in the shade than in the sun (the whole front is in shade here).
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
    grow_ = (~filled) & (cnt > 0)
    img2[grow_] = acc[grow_] / cnt[grow_][:, None]
    filled |= grow_
combined = img2.reshape(-1, 3)
encoded = np.clip(combined / scale, 0, 1) ** (1 / 2.2)
rgba = np.ones((px, 4), dtype=np.float32)
rgba[:, :3] = encoded
out_img = bpy.data.images.get("CH_Lightmap") or bpy.data.images.new("CH_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
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
    o.select_set(o == c_obj)
bpy.context.view_layer.objects.active = c_obj
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_texcoords=True,
                          export_normals=True)
tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("exported", GLB, "|", tris, "triangles |", len(mesh.materials), "materials")
c_obj["lightmap_scale"] = LIGHTMAP_SCALE            # read by county_hotel_preview.py
