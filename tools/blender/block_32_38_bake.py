"""
block_32_38_bake.py - textures and baked lighting for the frame row at 32-38 Main St (Mill'y,
Bakery, Meats), then export to assets/models/block-32-38.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/block_32_38_bake.py").read())

Steps (pattern: block_40_46_bake.py):
 1. Rebuild the geometry (block_32_38.py).
 2. Nine materials, all textures reused (merged into one draw call by `baked-lighting`, plus
    the glass):
      clap_row  house-65-main/clapboard_cream.jpg, tile 1.0 m (0.11 m boards), x factor -> warm
                pale cream #D8CFB8 (spec 1)
      clap_a    the same texture, tile and factor as 40-42's `clap_a` (#B9AE96), so part G (the
                patch over 40-42's north wall) matches the wall it continues (spec 2 named
                courthouse/clapboard_buff.jpg "tiled as on 40-42"; 40-42 is in fact built from
                this texture, so this one is used)
      trim      polyhaven/trim_paint_cream.jpg, tile 2.0 m, x factor -> #DDD5C2
      roof      county-offices/roof_tin_redbrown.jpg, tile 2.0 m; bake tint a touch greyer
                (dulled), the Mill'y rear porch darker (weathered shingle, map "x")
      shopfront county-offices/door_varnish_dark.jpg, tile 0.8 m, x factor -> #2E2E26
      deck      lovells-restaurant/stone_bluestone.jpg, tile 2.0 m (porch deck, thresholds)
      WindowBack   shared/window_backs.jpg cells (blinds, lace, curtains; Meats shop window)
      ShopInterior shared/shop_interior.jpg cells (Mill'y and Bakery windows and door lights)
      glass     plain #1A1916, alpha 0.40, BLEND, single-sided; not lightmapped in the scene
                (`glass-reflect`); fully transparent during the bake
 3. Split wall faces where other parts cover them, join, delete the faces nobody can see,
    unwrap "Lightmap" (front and porch weighted up; north wall a little down; roofs, rear and
    the faces against 40-42 down).
 4. Bake warm late-afternoon sun + sky into one 2K lightmap with Cycles. East side of Main St
    (front faces west): to-sun (0.40, -0.90, 0.36). Bake-only occluders (not exported): the
    built block-40-46.glb itself to the south, a box for 24-30 to the north. Every other
    collection is hidden from render during the bake.
 5. Bake an RGB grime mask (dirt band on the bottom 0.4 m, soot under the eave and the porch
    roof, drips under the sills, chalky north wall, deck darker at the wall and the doors) and
    multiply it in.
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
GLB = PROJECT + r"\assets\models\block-32-38.glb"
GLB_4046 = PROJECT + r"\assets\models\block-40-46.glb"
LIGHTMAP = PROJECT + r"\assets\textures\block-32-38-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 384
TO_SUN = (0.40, -0.90, 0.36)          # east-side building (front faces west)
COLL, RIG = "Block3238", "RW_BakeRig"
OFF_4046 = (14.205, 0.06, 0.0)        # block-40-46 local -> this frame (its origin (8.60, -116.55))

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\block_32_38.py").read())

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
    "Clap":  (TX + r"house-65-main\clapboard_cream.jpg", 1.0, 0.85, None, tint(CLAP, (0xD8, 0xCF, 0xB8))),
    "ClapA": (TX + r"house-65-main\clapboard_cream.jpg", 1.0, 0.85, None, tint(CLAP, (0xB9, 0xAE, 0x96))),
    "Trim":  (TX + r"polyhaven\trim_paint_cream.jpg", 2.0, 0.7, None, tint((230, 218, 191), (0xDD, 0xD5, 0xC2))),
    "Roof":  (TX + r"county-offices\roof_tin_redbrown.jpg", 2.0, 0.6, None, None),
    "Wood":  (TX + r"county-offices\door_varnish_dark.jpg", 0.8, 0.5, None, tint((58, 42, 31), (0x2E, 0x2E, 0x26))),
    "Deck":  (TX + r"lovells-restaurant\stone_bluestone.jpg", 2.0, 0.9, None, None),
    "WBack": (SHARED + "window_backs.jpg", 1.0, 0.9, None, None),
    "Shop":  (SHARED + "shop_interior.jpg", 1.0, 0.9, None, None),
    "Glass": (None, 1.0, 0.05, tuple(srgb_to_lin(c) for c in GLASS_RGB), None),
}
FINAL_NAMES = {"Clap": "clap_row", "ClapA": "clap_a", "Trim": "trim", "Roof": "roof", "Wood": "shopfront",
               "Deck": "deck", "WBack": "WindowBack", "Shop": "ShopInterior", "Glass": "glass"}


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
OBJ_MAT = {"ShellA": "Clap", "ShellB": "Clap", "ShellC": "Clap", "ShellD1": "Clap", "ShellD2": "Clap",
           "ShellF2": "Clap"}


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
        if kind in ("WBack", "Shop"):                    # window backs: their atlas cell
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


# D's roof plane (z = D_TOP_F + s_d (y - FW)) and the walls it covers the bottom of
s_d = (D_TOP_R - D_TOP_F) / (D_Y1 - FW)
D_PLANE = ((0, FW, D_TOP_F), (0, -s_d, 1))


def on(f, axis, value, sign):
    c = f.calc_center_median()
    n = f.normal
    return getattr(n, axis) * sign > 0.99 and abs(getattr(c, axis) - value) < 0.01


SPLITS = {
    # name: [(select, cuts)]
    "ShellA": [(lambda f: on(f, "x", P1, 1), [((0, B_Y1, 0), (0, 1, 0))])],
    "ShellB": [(lambda f: on(f, "x", P2, 1), [((0, C_Y1, 0), (0, 1, 0)), D_PLANE]),
               (lambda f: on(f, "y", B_Y1, 1), [((F2_X0, 0, 0), (1, 0, 0)), ((0, 0, F2_TOP_F), (0, 0, 1))])],
    "ShellC": [(lambda f: on(f, "x", C_X1, 1), [D_PLANE]),
               (lambda f: on(f, "y", C_Y1, 1), [D_PLANE])],
    "ShellD2": [(lambda f: on(f, "x", P2, -1), [((0, B_Y1, 0), (0, 1, 0)), ((0, F2_Y1, 0), (0, 1, 0)),
                                                 ((0, 0, F2_TOP_F), (0, 0, 1))])],
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
r_obj = bpy.data.objects["RW_ShellA"]
with bpy.context.temp_override(active_object=r_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
r_obj.name = r_obj.data.name = "Block3238"
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
# D's south face is kept on purpose: it closes 40-42's open north side (its tunnel) at Y 2.04-11.26.

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
# Give the lightmap's pixels to what matters: the front, the porch and the north wall.
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
        f *= 0.7                                   # soffits, porch ceiling
    if n.y < -0.7 and c.y < FW + 0.5:
        f *= 1.15                                  # the front
    if n.x < -0.7 and c.x < -HW + 0.1:
        f *= 0.8                                   # north wall (seen across the gap)
    if n.x > 0.7 and c.x > HW - 0.1:
        f *= 0.35                                  # against 40-42 (only the tunnel and a sliver show)
    if n.y > 0.7 and c.y > 7.0:
        f *= 0.5                                   # rear walls
    if m == "roof" and n.z > 0.9 and c.z > 3.3:
        f *= 0.35                                  # main roofs (barely seen)
    if f != 1.0:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.0015, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig: sun, sky, ground, occluders (in RW_BakeRig, not exported) ---------------
scene = bpy.context.scene
for name in ("Ref4046",):                          # a stray reference copy from building: drop it
    c = bpy.data.collections.get(name)
    if c:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(c)
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
rig.hide_viewport = False
rig.hide_render = False
sun = bpy.data.objects.get("RW_Sun")
if not sun:
    sun = bpy.data.objects.new("RW_Sun", bpy.data.lights.new("RW_Sun", "SUN"))
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


# ground: road and yards 0.15 below the sidewalk (east sidewalk Y -2.14 ... 1.76)
warm = rig_mat("RW_GroundWarm", (0.34, 0.28, 0.19))
rig_box("RW_Ground", -120, 120, -120, 120, -0.35, -0.15, warm)
rig_box("RW_Sidewalk", -120, 120, -2.14, 1.76, -0.35, 0.0, warm)
# occluders (PLAN.md Placement): 24-30 to the north as a box, 40-46 as the built model
rig_box("RW_Occ2430", -26.55, -10.15, 1.76, 13.76, -0.15, 7.5, rig_mat("RW_OccFrame", (0.45, 0.42, 0.36)))
old = bpy.data.objects.get("RW_Occ4046")
if old:
    bpy.data.objects.remove(old, do_unlink=True)
before_objs = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_4046)
for o in [o for o in bpy.data.objects if o not in before_objs]:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    rig.objects.link(o)
    o.location = Vector(OFF_4046)
    o.name = "RW_Occ4046"
    o.select_set(False)

if scene.world is None:
    scene.world = bpy.data.worlds.new("RW_Sky")
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
    light_img = bake_target("RW_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask (RGB) ----------------------------------------------------------
    grime_mat = bpy.data.materials.get("RW_GrimeBake") or bpy.data.materials.new("RW_GrimeBake")
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
    on_front = mult(front, map_range(Y, FW + 0.30, FW + 0.10, 0.0, 1.0))
    # soot under the boxed eave (2-storey fronts) and under the porch roof on the front wall
    soot_eave = mult(map_range(Z, 5.0, 5.88, 0.0, 0.14), map_range(Z, 5.88, 5.90, 1.0, 0.0))
    soot_porch = mult(on_front, map_range(Y, FW - 0.05, FW + 0.01, 0.0, 1.0),
                      map_range(Z, 2.3, 3.40, 0.0, 0.16), map_range(Z, 3.40, 3.46, 1.0, 0.0))
    soot = math_op("SUBTRACT", 1.0, math_op("ADD", soot_eave, soot_porch))
    # dark streaks below the upper window sills
    fx = near(X, list(UP_X), 0.35, 0.55)
    under_sill = mult(map_range(Z, 3.30, 3.83, 0.0, 1.0), map_range(Z, 3.83, 3.86, 1.0, 0.0))
    drips = math_op("SUBTRACT", 1.0, mult(front, fx, under_sill, map_range(streak_n, 0.3, 0.7, 0.16, 0.05)))
    # porch deck: darker toward the wall and at the shop doors (wear)
    up = map_range(NZ, 0.8, 0.95, 0.0, 1.0)
    deck = mult(up, map_range(Z, 0.10, 0.14, 0.0, 1.0), map_range(Z, 0.17, 0.155, 0.0, 1.0),
                map_range(Y, -0.05, 0.05, 0.0, 1.0))
    wall_band = map_range(Y, 0.9, FW, 0.0, 1.0)
    doors_x = near(X, [(a + b) / 2 for _, _, (a, b), _, _ in SHOPS], 0.35, 0.90)
    wear = mult(deck, math_op("ADD", mult(wall_band, 0.10),
                              mult(doors_x, map_range(Y, 0.3, 1.2, 0.0, 1.0), 0.10)))
    deck_dark = math_op("SUBTRACT", 1.0, wear)
    # north wall: chalky (faded, a touch lighter, blotchy)
    north = mult(map_range(NX, -0.6, -0.8, 0.0, 1.0), map_range(X, -HW + 0.06, -HW + 0.01, 0.0, 1.0))
    chalk_amt = mult(north, map_range(blotch_n, 0.3, 0.7, 0.6, 1.0))
    chalk = map_range(chalk_amt, 0.0, 1.0, 1.0, 1.05)
    grey = mult(height, blotch, streaks, soot, drips, deck_dark, chalk)
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    col_n = vmix(chalk_amt, (1.0, 1.0, 1.0), (0.96, 0.985, 1.0))    # chalky paint: cooler, less yellow
    attr = N("ShaderNodeAttribute")
    attr.attribute_name = "Tint"
    rgb = vmul(vmul(gc.outputs["Vector"], col_n), attr.outputs["Color"])
    L(rgb, emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    grime_img = bake_target("RW_Grime", True)
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
out_img = bpy.data.images.get("RW_Lightmap") or bpy.data.images.new("RW_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
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
r_obj["lightmap_scale"] = LIGHTMAP_SCALE            # read by block_32_38_preview.py
