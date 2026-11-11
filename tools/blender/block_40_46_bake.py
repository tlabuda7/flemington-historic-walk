"""
block_40_46_bake.py - textures and baked lighting for the block at 40-46 Main St (40-42 "Auto
Sales", 44-46 "Shoe Shine & Fruits"), then export to assets/models/block-40-46.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/block_40_46_bake.py").read())

Steps (pattern: rea_building_bake.py / county_hotel_bake.py):
 1. Rebuild the geometry (block_40_46.py).
 2. Ten materials (merged into one draw call by `baked-lighting`):
      clap_a  house-65-main/clapboard_cream.jpg, tile 1.0 m (0.11 m boards), x factor -> pale
              buff-grey #B9AE96 (40-42 and its rear wing)
      clap_b  the same texture, x factor -> cream #D6D0BE (44-46; spec #DCD6C4, a shade down so
              the sunlit front is not white)
      trim    polyhaven/trim_paint_cream.jpg, tile 2.0 m, x factor -> off-white #DCD7C8
      green   polyhaven/door_paint_green.jpg, tile 0.8 m, x factor -> dark green #2F4A36
      roof    county-offices/roof_tin_redbrown.jpg, tile 2.0 m (bake tint a touch greyer)
      stone   lovells-restaurant/stone_bluestone.jpg, tile 2.0 m (apron, porch deck, sills)
      signs   block-40-46/signs_atlas.jpg (tools/prepare_block_40_46_textures.py)
      WindowBack   shared/window_backs.jpg cells (blinds, lace, curtains, dark rooms; the 42
              show window and sale-room door look into a plain dark room)
      ShopInterior shared/shop_interior.jpg cells (44-46 display window, door lights, transoms)
      glass   plain #1A1916, alpha 0.40, BLEND, single-sided; not lightmapped in the scene
              (`glass-reflect`); fully transparent during the bake, ignored by the hidden-face pass
    The tunnel lining and the awning iron use one dark-brown texel of the window-back atlas.
 3. Split the wall faces where other parts cover them, join, delete the faces nobody can see
    (and A's north wall below 6.10, which stands against 36-38), unwrap "Lightmap" (fronts
    weighted up; passage wall, tunnel, rear and roofs down).
 4. Bake warm late-afternoon sun + sky into one 2K lightmap with Cycles. East side of Main St
    (front faces west): to-sun (0.40, -0.90, 0.36). Bake-only occluders (hidden from export):
    the Rea Building south of the passage and 36-38 to the north. Other collections are hidden
    from render during the bake.
 5. Bake an RGB grime mask (ground splash, soot under the cornices, drips under sills, a
    greyer passage wall, oil and tyre stains in the drive-through) and multiply it in.
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
GLB = PROJECT + r"\assets\models\block-40-46.glb"
LIGHTMAP = PROJECT + r"\assets\textures\block-40-46-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 384
TO_SUN = (0.40, -0.90, 0.36)          # east-side building (front faces west)
COLL, RIG = "Block4046", "BK_BakeRig"

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\block_40_46.py").read())

# 2. Materials ----------------------------------------------------------------
def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    """Constant colour that turns a texture averaging `avg` (sRGB 0-255) into `target`."""
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


def ratio(target, base):
    return tuple(srgb_to_lin(t) / srgb_to_lin(b) for t, b in zip(target, base))


GLASS_ALPHA = 0.40
GLASS_RGB = (0x1A, 0x19, 0x16)        # faint warm grey dust tint (as the Bank Building, Nevius Store)
SHARED = TX + "shared" + "\\"
CLAP = (229, 223, 204)                # clapboard_cream.jpg average (sRGB)
# material -> (texture file, metres per repeat, roughness, plain colour (linear) or None, factor or None)
LOOK = {
    "ClapA": (TX + r"house-65-main\clapboard_cream.jpg", 1.0, 0.85, None, tint(CLAP, (0xB9, 0xAE, 0x96))),
    "ClapB": (TX + r"house-65-main\clapboard_cream.jpg", 1.0, 0.85, None, tint(CLAP, (0xD6, 0xD0, 0xBE))),
    "Trim":  (TX + r"polyhaven\trim_paint_cream.jpg", 2.0, 0.7, None, tint((230, 218, 191), (0xDC, 0xD7, 0xC8))),
    "Green": (TX + r"polyhaven\door_paint_green.jpg", 0.8, 0.6, None, tint((93, 107, 92), (0x2F, 0x4A, 0x36))),
    "Roof":  (TX + r"county-offices\roof_tin_redbrown.jpg", 2.0, 0.6, None, None),
    "Stone": (TX + r"lovells-restaurant\stone_bluestone.jpg", 2.0, 0.9, None, None),
    "Signs": (TX + r"block-40-46\signs_atlas.jpg", 1.0, 0.85, None, None),
    "WBack": (SHARED + "window_backs.jpg", 1.0, 0.9, None, None),
    "Shop":  (SHARED + "shop_interior.jpg", 1.0, 0.9, None, None),
    "Glass": (None, 1.0, 0.05, tuple(srgb_to_lin(c) for c in GLASS_RGB), None),
}
FINAL_NAMES = {"ClapA": "clap_a", "ClapB": "clap_b", "Trim": "trim", "Green": "green", "Roof": "roof",
               "Stone": "stone", "Signs": "signs", "WBack": "WindowBack", "Shop": "ShopInterior",
               "Glass": "glass"}

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
# the dark texel (sRGB ~#140F0C) lifted to plank brown / iron grey (grey tints survive the shade warming)
TINTS = {"Tunnel": (2.6, 2.6, 2.6),
         "Iron": (1.8, 1.8, 1.9),
         "Roof": (0.90, 0.92, 0.96)}
OBJ_MAT = {"ShellA": "ClapA", "ShellB": "ClapA", "ShellC": "ClapB", "ShellC2": "ClapB",
           "Bay1": "ClapB", "Bay2": "ClapB", "Bay42": "ClapA"}

# Atlas boxes (pixels from the top-left; must match tools/prepare_block_40_46_textures.py)
REGIONS = {"stripes": (0, 0, 512, 384), "louvre": (512, 0, 704, 384), "canvas": (704, 0, 1024, 384),
           "val": (0, 384, 1024, 448), "auto": (0, 448, 1024, 576), "shoes": (0, 576, 512, 672),
           "fruits": (512, 576, 1024, 672), "spare": (0, 672, 1024, 1024)}
EDGE = {"louvre": (0.03, 0.5)}

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
        if kind in ("Tunnel", "Iron"):                   # one dark texel of the window-back atlas
            u0, v0, u1, v1 = WB_CELLS["dark_room_frame"]["uv"]
            for li in poly.loop_indices:
                uv.data[li].uv = ((u0 + u1) / 2, v0 + 0.2 * (v1 - v0))
            continue
        if kind in ("WBack", "Shop"):                    # window backs: their atlas cell
            rec = BACKREC.get(rid_attr.data[poly.index].value)
            for li in poly.loop_indices:
                co = mesh.vertices[mesh.loops[li].vertex_index].co
                if "const" in rec:
                    uv.data[li].uv = rec["const"]
                    continue
                (px, py), (nx, ny) = rec["wall"]
                u = (co.x - px) * -ny + (co.y - py) * nx
                fu = (u - rec["u0"]) / (rec["u1"] - rec["u0"])
                fz = (co.z - rec["z0"]) / (rec["z1"] - rec["z0"])
                U0, V0, U1, V1 = rec["uv"]
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


slope_c = (C_TOP_F - C_TOP_R) / CY1
SPLITS = {
    # name: [(select, cuts)]
    "ShellA": [(lambda f: f.normal.x < -0.99 and abs(f.calc_center_median().x - AX0) < 0.01, [((0, 0, 6.10), (0, 0, 1))]),
               # the front wall behind the hanging bay becomes its own (hidden) piece
               (lambda f: f.normal.y < -0.99 and abs(f.calc_center_median().y - AY0) < 0.01,
                [((-3.21, 0, 0), (1, 0, 0)), ((-0.11, 0, 0), (1, 0, 0)), ((0, 0, BAY_Z0), (0, 0, 1))]),
               (lambda f: f.normal.x > 0.99 and abs(f.calc_center_median().x - AX1) < 0.01,
                [((AX1, 0, C_TOP_F), (0, slope_c, 1))]),
               (lambda f: f.normal.y > 0.99 and abs(f.calc_center_median().y - AY1) < 0.01,
                [((BX0, 0, 0), (1, 0, 0)), ((BX1, 0, 0), (1, 0, 0)), ((0, 0, B_TOP), (0, 0, 1))])],
    "Bay42": [(lambda f: abs(f.normal.z) < 0.1, [((0, AY0, 0), (0, 1, 0))])],
    "Roof": [(lambda f: abs(f.normal.z) < 0.99 and -3.9 < f.calc_center_median().x < 0.6
              and 6.1 < f.calc_center_median().z < 6.7, [((0, AY0, 0), (0, 1, 0))])],
    "Trim": [(lambda f: -3.9 < f.calc_center_median().x < 0.6 and 1.0 < f.calc_center_median().y < 2.5
              and 3.6 < f.calc_center_median().z < 6.3, [((0, AY0, 0), (0, 1, 0))])],
    "ShellC": [(lambda f: f.normal.x < -0.99 and abs(f.calc_center_median().x - CX0) < 0.01,
                [((0, AY0, 0), (0, 1, 0)), ((0, AY1, 0), (0, 1, 0))]),
               (lambda f: f.normal.x > 0.99 and abs(f.calc_center_median().x - CX1) < 0.01,
                [((0, 5.00, 0), (0, 1, 0)), ((0, 7.97, 0), (0, 1, 0)), ((0, 14.06, 0), (0, 1, 0)),
                 ((0, 0, BAY_Z0), (0, 0, 1)), ((0, 0, BAY_Z1), (0, 0, 1))]),
               (lambda f: f.normal.y > 0.99 and abs(f.calc_center_median().y - CY1) < 0.01,
                [((0, 0, C2_TOP), (0, 0, 1))])],
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
r_obj = bpy.data.objects["BK_ShellA"]
with bpy.context.temp_override(active_object=r_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
r_obj.name = r_obj.data.name = "Block4046"
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
# A's north wall below 6.10 and the apron end stand against 36-38 (2-storey frame): never seen
bm = bmesh.new()
bm.from_mesh(mesh)
bm.normal_update()
against = [f for f in bm.faces if f.normal.x < -0.99 and abs(f.calc_center_median().x - AX0) < 0.01
           and f.calc_center_median().z < 6.10]
bmesh.ops.delete(bm, geom=against, context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bm.to_mesh(mesh)
bm.free()
after = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("hidden faces removed:", removed, "+", len(against), "against 36-38 | triangles", before, "->", after)

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
# Give the lightmap's pixels to what matters: the two fronts, the shop front and porch.
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    f = 1.0
    c, n = p.center, p.normal
    m = mat_names[p.material_index]
    if m == "glass":
        f *= 0.03                                  # not lightmapped in the scene
    elif m in ("WindowBack", "ShopInterior"):
        f *= 0.6
    if n.z < -0.5:
        f *= 0.7                                   # soffits, awning underside
    if n.y < -0.7 and c.z < 9.2:
        f *= 1.15                                  # fronts
    if TUN_X0 - 0.01 < c.x < TUN_X1 + 0.01 and AY0 + 0.25 < c.y < AY1 - 0.25 and c.z < TUN_TOP + 0.01:
        f *= 0.45                                  # tunnel
    if n.x > 0.7 and c.x > CX1 - 0.05:
        f *= 0.7                                   # passage wall and bays
    if n.x < -0.7:
        f *= 0.55                                  # north faces (yard, slot)
    if n.y > 0.7:
        f *= 0.5                                   # rear walls
    if m == "roof" and n.z > 0.97:
        f *= 0.4                                   # flat roofs and decks
    elif m == "roof" and n.z > 0.5 and c.x > CX0 + 0.1:
        f *= 0.5                                   # 44-46 shed roof (barely seen)
    if f != 1.0:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.0015, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig: sun, sky, ground, occluders (in BK_BakeRig, not exported) ---------------
scene = bpy.context.scene
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
rig.hide_viewport = False
rig.hide_render = False
sun = bpy.data.objects.get("BK_Sun")
if not sun:
    sun = bpy.data.objects.new("BK_Sun", bpy.data.lights.new("BK_Sun", "SUN"))
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



# ground: roads, the passage and the yard 0.15 below the sidewalk (east sidewalk Y -2.20 ... 1.70)
warm = rig_mat("BK_GroundWarm", (0.34, 0.28, 0.19))
rig_box("BK_Ground", -120, 120, -120, 120, -0.35, -0.15, warm)
rig_box("BK_Sidewalk", -120, 120, -2.20, 1.70, -0.35, 0.0, warm)
# occluders (PLAN.md Placement): the Rea Building south of the passage, 36-38 to the north
rig_box("BK_OccRea", 10.79, 26.70, 2.25, 17.45, -0.15, 11.0, rig_mat("BK_OccBrick", (0.30, 0.13, 0.08)))
rig_box("BK_Occ3638", -20.0, AX0, 0.40, 18.0, -0.15, 6.1, rig_mat("BK_OccFrame", (0.45, 0.42, 0.36)))

if scene.world is None:
    scene.world = bpy.data.worlds.new("BK_Sky")
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
    light_img = bake_target("BK_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask (RGB) ----------------------------------------------------------
    grime_mat = bpy.data.materials.get("BK_GrimeBake") or bpy.data.materials.new("BK_GrimeBake")
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


    # grime and splash on the bottom ~0.4 m, fading by 0.9 m
    height = map_range(Z, -0.15, 0.9, 0.80, 1.0)
    blotch = map_range(noise_tex(geo.outputs["Position"], 0.6, 6.0), 0.0, 1.0, 0.91, 1.03)
    stretch = N("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (4.0, 4.0, 0.18)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_n = noise_tex(stretch.outputs["Vector"], 1.7, 2.0)
    streaks = map_range(streak_n, 0.35, 0.75, 0.94, 1.0)
    # darker paint under the cornices (frieze), clean above
    side_c = map_range(X, CX0 - 0.10, CX0 + 0.05, 0.0, 1.0)
    soot_a = mult(map_range(Z, 7.9, 8.86, 0.0, 0.14), map_range(Z, 8.86, 8.90, 1.0, 0.0))
    soot_c = mult(side_c, map_range(Z, 4.9, 5.82, 0.0, 0.12), map_range(Z, 5.82, 5.86, 1.0, 0.0))
    soot = math_op("SUBTRACT", 1.0, math_op("ADD", soot_a, soot_c))
    # dark streaks below the front window sills
    front = map_range(NY, -0.6, -0.8, 0.0, 1.0)
    fx = near(X, list(A_BAYS) + [3.25, 5.85], 0.35, 0.55)
    under_sill = math_op("ADD", math_op("ADD",
                         mult(map_range(Z, 3.75, 4.28, 0.0, 1.0), map_range(Z, 4.28, 4.31, 1.0, 0.0)),
                         mult(map_range(Z, 6.25, 6.78, 0.0, 1.0), map_range(Z, 6.78, 6.81, 1.0, 0.0))),
                         mult(side_c, map_range(Z, 3.56, 3.73, 0.0, 1.0), map_range(Z, 3.73, 3.76, 1.0, 0.0)))
    drips = math_op("SUBTRACT", 1.0, mult(front, fx, under_sill, map_range(streak_n, 0.3, 0.7, 0.16, 0.05)))
    # oil and tyre stains in the drive-through and on the apron in front of it
    up = map_range(NZ, 0.8, 0.95, 0.0, 1.0)
    drive = mult(up, map_range(Z, 0.05, 0.02, 0.0, 1.0), map_range(X, TUN_X1 + 0.15, TUN_X1, 0.0, 1.0),
                 map_range(Y, AY1 + 0.3, AY1, 0.0, 1.0))
    oil_n = noise_tex(geo.outputs["Position"], 1.4, 3.0)
    tyres = near(X, [ARCH_C - 0.70, ARCH_C + 0.70], 0.08, 0.26)
    oil = math_op("SUBTRACT", 1.0, mult(drive, math_op("ADD", map_range(oil_n, 0.45, 0.70, 0.0, 0.40),
                                                       mult(tyres, 0.18))))
    # worn step and thresholds: general darker treads near the doors
    treads = map_range(mult(up, map_range(Z, 0.20, 0.16, 0.0, 1.0), map_range(Z, -0.02, 0.0, 0.0, 1.0)),
                       0.0, 1.0, 1.0, 0.94)
    # passage (south) wall of 44-46: greyer and darker, most near the ground
    south = mult(map_range(NX, 0.6, 0.8, 0.0, 1.0), map_range(X, CX1 - 0.05, CX1, 0.0, 1.0))
    s_dark = map_range(mult(south, map_range(Z, 0.0, 6.0, 1.0, 0.4)), 0.0, 1.0, 1.0, 0.86)
    # awning canvas: sun-bleached top, soiled hem
    canvas_top = mult(map_range(Y, -0.1, -0.2, 0.0, 1.0), map_range(Y, -1.65, -1.55, 0.0, 1.0),
                      map_range(Z, 2.3, 2.4, 0.0, 1.0), map_range(Z, 2.95, 3.05, 1.0, 0.0), up)
    bleach = map_range(canvas_top, 0.0, 1.0, 1.0, 1.05)
    hem = mult(map_range(Y, -1.66, -1.60, 1.0, 0.0), map_range(Y, -1.62, -1.59, 0.0, 1.0),
               map_range(Z, 2.15, 2.30, 1.0, 0.0))
    hem_dirt = map_range(hem, 0.0, 1.0, 1.0, 0.86)
    grey = mult(height, blotch, streaks, soot, drips, oil, treads, s_dark, bleach, hem_dirt)
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    # shaded passage wall a touch cooler and greyer
    col_s = vmix(south, (1.0, 1.0, 1.0), (0.95, 0.97, 0.97))
    attr = N("ShaderNodeAttribute")
    attr.attribute_name = "Tint"
    rgb = vmul(vmul(gc.outputs["Vector"], col_s), attr.outputs["Color"])
    L(rgb, emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    grime_img = bake_target("BK_Grime", True)
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
out_img = bpy.data.images.get("BK_Lightmap") or bpy.data.images.new("BK_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
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
r_obj["lightmap_scale"] = LIGHTMAP_SCALE            # read by block_40_46_preview.py

