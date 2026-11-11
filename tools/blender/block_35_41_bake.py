"""
block_35_41_bake.py - textures and baked lighting for the block at 35-41 Main St (35-37 frame
grocery with the two-tier porch, 39-41 brick "Cobbler"), then export to
assets/models/block-35-41.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/block_35_41_bake.py").read())

Steps (pattern: palace_theatre_bake.py / bank_building_bake.py):
 1. Rebuild the geometry (block_35_41.py).
 2. Ten materials (the opaque ones are merged into one draw call by `baked-lighting`):
      clapboard        house-65-main/clapboard_cream.jpg, tile 1.27 m (0.14 m boards), x factor ->
                       warm pale cream #D8CFB8 (35-37 and its wing and shed)
      trim             block-35-41/trim_stone_grey.jpg, tile 2.0 m (#A39A88: columns, rails, spindles,
                       fascias, eave, brackets, frames, sashes, sills; porch floor and steps)
      brick            polyhaven/red_brick.jpg, tile 1.4 m (0.07 m courses, as the Palace), x factor ->
                       unpainted red-brown #7A4436 (39-41, its rear, the areaway, the chimney)
      roof             county-offices/roof_tin_redbrown.jpg, tile 2.0 m (dulled by a bake tint)
      shopfront        county-offices/door_varnish_dark.jpg, tile 0.8 m (doors, shop front, stair
                       boards; the iron awning arms, bars and pipe rails darker by a bake tint)
      signs            block-35-41/signs_atlas.jpg: awning stripes, the valance lettered
                       "PRODUCE | JACOB R. HALL | GROCER" (owner's decision 3b), louvred shutters,
                       the blank board over the basement door
      paving           polyhaven/sidewalk_concrete.jpg, tile 3.0 m (as the scene's sidewalk)
      glass            plain #1A1916, alpha 0.40 BLEND, roughness 0.05, single-sided, NOT lightmapped
                       in the scene (`baked-lighting` keeps it; `glass-reflect` adds the sky)
      window_back      shared/window_backs.jpg (blinds, lace, curtains; the basement door's interior)
      grocery_interior block-35-41/grocery_interior.jpg (tools/prepare_grocery_interior.py): the shop
                       window and the glazed door of the grocery
 3. Join, delete the faces nobody can see (the glass does not block that test), unwrap "Lightmap"
    (the two fronts and the alley side weighted up; rear parts, roofs and window backs down).
 4. Bake warm late-afternoon sun + sky into one 2K lightmap with Cycles. West side of Main St
    (front faces east): to-sun (-0.40, 0.90, 0.36), so the fronts are in shade and lit by the sky.
    Bake-only occluders: the County Hotel (south) and the Palace Theatre (north, across the alley).
    The ground has a hole over the areaway. Other collections are hidden from render; the glass is
    fully transparent during the bake so the window backs get their light.
 5. Bake an RGB grime mask (dirt band on the bottom 0.4 m, soot under the eave and the porch roof,
    brick streaked below the sills and the balcony, the areaway darker and damp, the porch steps
    worn paler at the middle, the slab darker along the walls) and multiply it in.
 6. Fill empty lightmap pixels, warm the shade, save the sRGB JPEG, print LIGHTMAP_SCALE, export
    the GLB (TEXCOORD_0 + TEXCOORD_1).
"""

import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
TX = PROJECT + r"\assets\textures" + "\\"
GLB = PROJECT + r"\assets\models\block-35-41.glb"
LIGHTMAP = PROJECT + r"\assets\textures\block-35-41-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 384
TO_SUN = (-0.40, 0.90, 0.36)          # west-side building (front faces east)
COLL, RIG = "Block3541", "BL_BakeRig"
GLASS_ALPHA = 0.40
GLASS_RGB = (0x1A, 0x19, 0x16)        # faint warm grey dust tint (as the Nevius Store, Union Hotel)

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\block_35_41.py").read())

# 2. Materials ----------------------------------------------------------------


def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    """Constant colour that turns a texture averaging `avg` (sRGB 0-255) into `target`."""
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


def ratio(target, base):
    return tuple(srgb_to_lin(t) / srgb_to_lin(b) for t, b in zip(target, base))


# material -> (texture file, metres per repeat (None = atlas UVs), roughness, plain colour, factor)
LOOK = {
    "Clapboard":  (TX + r"house-65-main\clapboard_cream.jpg", 1.27, 0.85, None, tint((229, 223, 204), (0xD8, 0xCF, 0xB8))),
    "Trim":       (TX + r"block-35-41\trim_stone_grey.jpg", 2.0, 0.7, None, None),
    "Brick":      (TX + r"polyhaven\red_brick.jpg", 1.4, 0.9, None, tint((142, 103, 80), (0x7A, 0x44, 0x36))),
    "Roof":       (TX + r"county-offices\roof_tin_redbrown.jpg", 2.0, 0.6, None, None),
    "Wood":       (TX + r"county-offices\door_varnish_dark.jpg", 0.8, 0.5, None, None),
    "Signs":      (TX + r"block-35-41\signs_atlas.jpg", None, 0.85, None, None),
    "Paving":     (TX + r"polyhaven\sidewalk_concrete.jpg", 3.0, 0.95, None, None),
    "Glass":      (None, None, 0.05, tuple(srgb_to_lin(c) for c in GLASS_RGB), None),
    "WindowBack": (TX + r"shared\window_backs.jpg", None, 0.9, None, None),
    "Grocery":    (TX + r"block-35-41\grocery_interior.jpg", None, 0.9, None, None),
}
FINAL_NAMES = {"Clapboard": "clapboard", "Trim": "trim", "Brick": "brick", "Roof": "roof", "Wood": "shopfront",
               "Signs": "signs", "Paving": "paving", "Glass": "glass", "WindowBack": "window_back",
               "Grocery": "grocery_interior"}


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
WOOD_AVG = (58, 42, 31)
TINTS = {"Iron": ratio((0x24, 0x24, 0x24), WOOD_AVG),           # dark painted iron
         "Roof": (0.84, 0.86, 0.90),
         "Chimney": (0.92, 0.90, 0.90),
         "Steps": (1.04, 1.03, 1.02)}
OBJ_MAT = {"ShellA": "Clapboard", "ShellC": "Clapboard", "ShellD": "Clapboard", "ShellE": "Brick", "ShellF": "Brick"}


def set_uvs(obj, kind):
    """Box UVs in real-world metres (tile from the builder's material); atlas builders keep the
    UVs block_35_41.py gave them."""
    mesh = obj.data
    if kind in ATLAS_BUILDERS:
        return
    while mesh.uv_layers:
        mesh.uv_layers.remove(mesh.uv_layers[0])
    uv = mesh.uv_layers.new(name="UVMap")
    tile = LOOK[OBJ_MAT.get(kind) or BUILDER_MAT[kind]][1]
    for poly in mesh.polygons:
        n = poly.normal
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
    data = np.tile(np.array([*rgb, 1.0], dtype=np.float32), (len(obj.data.loops), 1))
    attr.data.foreach_set("color", data.ravel())


parts = [o for o in col.objects if o.type == "MESH"]
for obj in parts:
    kind = obj.name[3:]
    set_uvs(obj, kind)
    add_tint(obj, TINTS.get(kind, (1.0, 1.0, 1.0)))
    obj.data.materials[0] = FINAL[OBJ_MAT.get(kind) or BUILDER_MAT[kind]]

# 3. Join, drop hidden faces, unwrap the lightmap UVs --------------------------
r_obj = bpy.data.objects["BL_ShellA"]
with bpy.context.temp_override(active_object=r_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
r_obj.name = r_obj.data.name = COLL
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
    """Delete faces that no ray from any of their sample points can leave the model through
    (inside walls, under trim, behind shutters). The glass does not block the rays. Downward
    faces at or below grade go too (except in the areaway, where nothing faces down anyway)."""
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
# Give the lightmap's pixels to what matters: the two fronts, the porch and the alley side.
LM_SHRINK = {"glass": 0.03, "window_back": 0.6, "grocery_interior": 0.8}
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    m = mat_names[p.material_index]
    f = LM_SHRINK.get(m, 1.0)
    c, n = p.center, p.normal
    if m not in LM_SHRINK:
        if c.y < AY0 + 0.5:
            f *= 1.3                                   # the fronts, the porch, the court
        elif c.y > AY1 - 0.05 or (c.x < EX1 + 0.05 and c.y > EY1 - 0.05):
            f *= 0.4                                   # wing, shed, brick rear
        elif n.x > 0.7 and c.x > AX1 - 0.05:
            f *= 0.9                                   # alley (north) side of 35-37
        else:
            f *= 0.5                                   # the slot between the buildings, south side
        if m == "roof" and n.z > 0.3:
            f *= 0.45
        if n.z < -0.5:
            f *= 0.7                                   # soffits, ceilings
    if f != 1.0:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.0015, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig: sun, sky, ground, occluders (in BL_BakeRig, not exported) ---------------
scene = bpy.context.scene
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
rig.hide_viewport = False
rig.hide_render = False
sun = bpy.data.objects.get("BL_Sun")
if not sun:
    sun = bpy.data.objects.new("BL_Sun", bpy.data.lights.new("BL_Sun", "SUN"))
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


warm = rig_mat("BL_GroundWarm", (0.34, 0.28, 0.19))
wx0, wx1, wy0, wy1 = WELL
# ground (alley, yards, road) at -0.15, with a hole over the areaway; west sidewalk Y -4.72 ... -0.82
rig_box("BL_Ground_S", -150, wx0, -150, 150, -0.45, YARD, warm)
rig_box("BL_Ground_N", wx1, 150, -150, 150, -0.45, YARD, warm)
rig_box("BL_Ground_F", wx0, wx1, -150, wy0, -0.45, YARD, warm)
rig_box("BL_Ground_B", wx0, wx1, wy1, 150, -0.45, YARD, warm)
rig_box("BL_Sidewalk", -150, 150, -4.72, -0.82, -0.45, 0.0, warm)
# occluders (PLAN.md Placement): the County Hotel to the south, the Palace Theatre north of the alley
rig_box("BL_OccHotel", -29.75, -5.89, -0.82, 10.76, 0.0, 9.15, rig_mat("BL_OccHotel", (0.62, 0.58, 0.50)))
rig_box("BL_OccPalace", 9.33, 21.93, -0.82, 22.0, 0.0, 8.65, rig_mat("BL_OccPalace", (0.30, 0.13, 0.08)))

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
    light_img = bake_target("BL_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask (RGB) ----------------------------------------------------------
    grime_mat = bpy.data.materials.get("BL_GrimeBake") or bpy.data.materials.new("BL_GrimeBake")
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

    up = map_range(NZ, 0.8, 0.95, 0.0, 1.0)
    vertical = map_range(math_op("ABSOLUTE", NZ), 0.3, 0.1, 0.0, 1.0)
    brick_e = mult(map_range(X, EX1 + 0.02, EX1 - 0.02, 0.0, 1.0))          # 39-41 and its rear
    # dirt band on the bottom ~0.4 m (from the deck on the porch, from grade elsewhere), blotchy
    base_z = math_op("ADD", mult(map_range(X, AX0 - 0.05, AX0 + 0.05, 0.0, 1.0),
                                 map_range(Y, -0.05, 0.05, 0.0, 1.0), map_range(Y, AY0 + 0.2, AY0 + 0.3, 1.0, 0.0),
                                 DECK), 0.0)
    above = math_op("SUBTRACT", Z, base_z)
    blotch = map_range(noise_tex(geo.outputs["Position"], 0.7, 6.0), 0.0, 1.0, 0.88, 1.04)
    band = map_range(mult(vertical, map_range(above, -0.05, 0.6, 1.0, 0.0)), 0.0, 1.0, 1.0, 0.80)
    band = math_op("ADD", band, mult(math_op("SUBTRACT", 1.0, band), map_range(blotch, 0.88, 1.04, 0.6, 0.0)))
    stretch = N("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (4.0, 4.0, 0.18)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_n = noise_tex(stretch.outputs["Vector"], 1.7, 2.0)
    streaks = map_range(streak_n, 0.35, 0.75, 0.93, 1.0)
    # soot under the main eave (35-37 front and sides) and under the porch roof
    a_part = mult(map_range(X, AX0 - 0.1, AX0 + 0.1, 0.0, 1.0), map_range(Y, AY1, AY1 - 0.1, 0.0, 1.0))
    eave = mult(a_part, vertical, map_range(Z, 7.3, FRIEZE0, 0.0, 1.0), map_range(Z, SOFFIT - 0.01, SOFFIT + 0.01, 1.0, 0.0))
    porch_top = mult(a_part, map_range(Y, AY0 - 0.02, AY0 + 0.02, 1.0, 0.0), map_range(Z, 6.0, 6.5, 0.0, 1.0),
                     map_range(Z, 6.9, 7.0, 1.0, 0.0))
    soot = math_op("SUBTRACT", 1.0, math_op("ADD", mult(eave, 0.18), mult(porch_top, 0.16)))
    # brick: streaks below the window sills / thresholds and below the balcony
    fx = near(X, list(E_WIN_X), 0.40, 0.70)
    under = math_op("ADD", mult(fx, map_range(Z, 3.9, 4.95, 0.0, 1.0), map_range(Z, 4.96, 4.98, 1.0, 0.0)),
                    mult(map_range(Z, 0.2, 1.40, 0.0, 1.0), map_range(Z, 1.40, 1.42, 1.0, 0.0)))
    drips = math_op("SUBTRACT", 1.0, mult(brick_e, vertical, under, map_range(streak_n, 0.3, 0.7, 0.20, 0.06)))
    # the areaway: darker and damp below grade
    well = map_range(Z, 0.0, -0.9, 1.0, 0.66)
    # porch steps and deck: worn paler down the middle of the treads in front of the door
    tread = mult(up, map_range(Y, AY0 - 0.05, AY0 - 0.15, 0.0, 1.0), map_range(Z, -0.01, 0.02, 0.0, 1.0),
                 map_range(Z, DECK + 0.01, DECK + 0.03, 1.0, 0.0), near(X, [2.75], 0.4, 1.6))
    worn = map_range(tread, 0.0, 1.0, 1.0, 1.10)
    # the paving darker along the walls
    slab = mult(up, map_range(Z, 0.02, 0.0, 0.0, 1.0), map_range(Z, -0.02, 0.0, 0.0, 1.0))
    by_wall = math_op("MAXIMUM", map_range(Y, -0.25, 0.0, 0.0, 1.0),
                      mult(brick_e, map_range(Y, EY0 - 0.4, EY0, 0.0, 1.0)))
    slab_dark = map_range(mult(slab, by_wall), 0.0, 1.0, 1.0, 0.86)
    grey = mult(band, blotch, streaks, soot, drips, well, worn, slab_dark)
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    # the damp areaway slightly green-grey
    damp = vmix(map_range(Z, -0.05, -0.6, 0.0, 1.0), (1.0, 1.0, 1.0), (0.93, 0.96, 0.92))
    attr = N("ShaderNodeAttribute")
    attr.attribute_name = "Tint"
    rgb = vmul(vmul(gc.outputs["Vector"], damp), attr.outputs["Color"])
    L(rgb, emit.inputs["Color"])
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
r_obj["lightmap_scale"] = LIGHTMAP_SCALE            # read by block_35_41_preview.py
