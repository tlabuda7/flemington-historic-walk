"""
odd_fellows_hall_bake.py - textures and baked lighting for the Odd Fellows Hall / Hopewell
Building (82-84 Main St), then export to assets/models/odd-fellows-hall.glb.

Run inside Blender (after `python tools/prepare_odd_fellows_textures.py`):
    exec(open(r"<project>/tools/blender/odd_fellows_hall_bake.py").read())

Steps (pattern: palace_theatre_bake.py / union_hotel_bake.py):
 1. Rebuild the geometry (odd_fellows_hall.py).
 2. Eight materials, all reused textures (merged into one draw call by `baked-lighting`):
      front      polyhaven/trim_paint_cream.jpg, tile 2.0 m, x factor -> pale buff #CFC2A4
      trim       the same map, x factor -> cream #DDD5C2 (hoods, surrounds, sashes, cornice,
                 brackets and shutters a little darker by bake tints, arch, signboards, sills)
      clapboard  house-65-main/clapboard_cream.jpg, tile 1.26 m (0.14 m boards), x factor ->
                 warm mid drab #8A8072
      brick      polyhaven/red_brick.jpg, tile 1.4 m, x factor -> red-brown #7A4436 (rear B)
      roof       county-offices/roof_tin_redbrown.jpg, tile 2.0 m, dulled by a bake tint
      shopfront  polyhaven/door_paint_green.jpg, tile 0.8 m, x factor -> green-black #2A2E28
                 (spec named county-offices/door_varnish_dark.jpg, but that map is brown and a
                 glTF colour factor cannot exceed 1, so it cannot reach the spec's green-black)
      dark       plain #1E2226 (glass, vent back, awning irons)
      awning     odd-fellows-hall/awning_faint.jpg (tools/prepare_odd_fellows_textures.py: the
                 bank's stripes faded to pale canvas with faint stripes, as on the cards)
 3. Split faces where other parts cover them, join, delete the faces nobody can see,
    unwrap "Lightmap" (front and north wall weighted up; rear, brick and roof down).
 4. Bake warm late-afternoon sun + sky into one 2K lightmap with Cycles. East side of Main St
    (front faces west): to-sun (0.40, -0.90, 0.36) - the front and the south wall are sunlit,
    the north wall (alley) is in shade, as on the card. Bake-only occluders: the Nevius store
    north of the alley and 90-94 Main to the south. Other collections are hidden from render.
 5. Bake an RGB grime mask (dark band on the bottom 0.4 m of the clapboard and brick, soot
    under the cornice and on the hood tops, faint streaks below the sills, duller brick rear)
    and multiply it in.
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
GLB = PROJECT + r"\assets\models\odd-fellows-hall.glb"
LIGHTMAP = PROJECT + r"\assets\textures\odd-fellows-hall-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 384
TO_SUN = (0.40, -0.90, 0.36)          # east-side building (front faces west)
COLL, RIG = "OddFellowsHall", "OF_BakeRig"

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\odd_fellows_hall.py").read())

# 2. Materials ----------------------------------------------------------------
def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    """Constant colour that turns a texture averaging `avg` (sRGB 0-255) into `target`."""
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


def ratio(target, base):
    return tuple(srgb_to_lin(t) / srgb_to_lin(b) for t, b in zip(target, base))


DARK_BASE = (0x1E, 0x22, 0x26)
CREAM_AVG = (230, 218, 191)            # trim_paint_cream.jpg average (sRGB)
CLAP_TILE = 1.26                       # 9 boards per repeat -> 0.14 m boards
AWN_TILE = 0.60
# material -> (texture file, metres per repeat, roughness, plain colour (linear) or None, factor or None)
LOOK = {
    "Front":     (TX + r"polyhaven\trim_paint_cream.jpg", 2.0, 0.8, None, tint(CREAM_AVG, (0xCF, 0xC2, 0xA4))),
    "Trim":      (TX + r"polyhaven\trim_paint_cream.jpg", 2.0, 0.7, None, tint(CREAM_AVG, (0xDD, 0xD5, 0xC2))),
    "Clapboard": (TX + r"house-65-main\clapboard_cream.jpg", CLAP_TILE, 0.85, None,
                  tint((229, 223, 204), (0x8A, 0x80, 0x72))),
    "Brick":     (TX + r"polyhaven\red_brick.jpg", 1.4, 0.9, None, tint((142, 103, 80), (0x7A, 0x44, 0x36))),
    "Roof":      (TX + r"county-offices\roof_tin_redbrown.jpg", 2.0, 0.6, None, None),
    "Shopfront": (TX + r"polyhaven\door_paint_green.jpg", 0.8, 0.6, None, tint((93, 107, 92), (0x2A, 0x2E, 0x28))),
    "Dark":      (None, 1.0, 0.3, tuple(srgb_to_lin(c) for c in DARK_BASE), None),
    "Awning":    (TX + r"odd-fellows-hall\awning_faint.jpg", AWN_TILE, 0.9, None, None),
}
FINAL_NAMES = {"Front": "front", "Trim": "trim", "Clapboard": "clapboard", "Brick": "brick", "Roof": "roof",
               "Shopfront": "shopfront", "Dark": "dark", "Awning": "awning"}


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
TINTS = {"Bracket": (0.86, 0.85, 0.83),
         "Shutter": (0.80, 0.79, 0.77),
         "Sash": (0.92, 0.91, 0.90),
         "Iron": ratio((0x2A, 0x2A, 0x2B), DARK_BASE),
         "Roof": (0.86, 0.88, 0.92),
         "BrickAdd": (0.95, 0.95, 0.95),
         "ShellB": (0.95, 0.95, 0.95)}
OBJ_MAT = {"ShellF": "Front", "ShellA": "Clapboard", "ShellB": "Brick"}


def set_uvs(obj, kind):
    """Box UVs in real-world metres (tile from the builder's material). Awning canvas: U along
    the front (x), V down the slope, so the stripes run downhill on the canvas and valance."""
    mesh = obj.data
    while mesh.uv_layers:
        mesh.uv_layers.remove(mesh.uv_layers[0])
    uv = mesh.uv_layers.new(name="UVMap")
    mat_key = OBJ_MAT.get(kind) or BUILDER_MAT[kind]
    tile = LOOK[mat_key][1]
    for poly in mesh.polygons:
        n = poly.normal
        h = math.hypot(n.x, n.y)
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            if kind == "Awning":
                u, v = co.x, -(0.942 * co.y + 0.336 * co.z)
            elif 0.25 < abs(n.z) < 0.97:                 # slopes: along the slope
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


def cornice_inner(f):
    c, n = f.calc_center_median(), f.normal
    return c.z > 9.4 and ((abs(n.x) > 0.99 and abs(abs(c.x) - HW) < 0.005) or (n.y > 0.99 and abs(c.y) < 0.005))


# Faces partly covered by other parts are cut along the cover's edge, so the covered part can
# be deleted (no dark lightmap texels bleeding out from under the cornice).
SPLITS = {
    "ShellF": [(lambda f: f.normal.y < -0.99, [((0, 0, FRIEZE0), (0, 0, 1))])],
    "ShellA": [(lambda f: abs(f.normal.x) > 0.99, [((0, 0, FRIEZE0), (0, 0, 1)), ((0, 0.18, 0), (0, 1, 0))])],
    "Trim": [(cornice_inner, [((0, 0, EAVE), (0, 0, 1))])],
}

parts = [o for o in col.objects if o.type == "MESH"]
for obj in parts:
    kind = obj.name[3:]
    for select, cuts in SPLITS.get(kind, []):
        bisect_faces(obj, select, cuts)
    set_uvs(obj, kind)
    add_tint(obj, TINTS.get(kind, (1.0, 1.0, 1.0)))
    obj.data.materials[0] = FINAL[OBJ_MAT.get(kind) or BUILDER_MAT[kind]]

# 3. Join, drop hidden faces, unwrap the lightmap UVs --------------------------
r_obj = bpy.data.objects["OF_ShellF"]
with bpy.context.temp_override(active_object=r_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
r_obj.name = r_obj.data.name = "OddFellowsHall"
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
# Give the lightmap's pixels to what matters: the front and the north wall (seen from the
# street and the alley); the south wall at a slant; brick rear, roof and back walls little.
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    f = 1.0
    c, n = p.center, p.normal
    m = mat_names[p.material_index]
    if m == "dark":
        f *= 0.6
    if n.z < -0.5:
        f *= 0.7                                   # soffits, undersides
    if c.y < 1.2 and c.z < 13.5:
        f *= 1.35                                  # the front and everything on it
    if n.x > 0.7 and c.y < AY1:
        f *= 0.7                                   # south wall of A (blank, seen at a slant)
    if c.y > AY1 + 0.01:
        f *= 0.45                                  # brick rear
    if n.y > 0.7 and c.y > 1.2:
        f *= 0.6                                   # rear-facing faces
    if m == "roof" and n.z > 0.5:
        f *= 0.3                                   # roof
    if f != 1.0:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.0015, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig: sun, sky, ground, occluders (in OF_BakeRig, not exported) ---------------
scene = bpy.context.scene
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
rig.hide_viewport = False
rig.hide_render = False
sun = bpy.data.objects.get("OF_Sun")
if not sun:
    sun = bpy.data.objects.new("OF_Sun", bpy.data.lights.new("OF_Sun", "SUN"))
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


# ground: road, alleys and yards 0.15 below the sidewalk (east sidewalk Y -3.90 ... 0)
warm = rig_mat("OF_GroundWarm", (0.34, 0.28, 0.19))
rig_box("OF_Ground", -150, 150, -150, 150, -0.35, ALLEY, warm)
rig_box("OF_Sidewalk", -150, 150, -3.90, 0.0, -0.35, 0.0, warm)
# occluders (PLAN.md Placement): the Nevius store north of the alley, 90-94 Main to the south
rig_box("OF_OccNevius", -20.42, -12.42, 0.0, 32.25, ALLEY, 10.7, rig_mat("OF_OccBrick", (0.30, 0.13, 0.08)))
rig_box("OF_Occ90", 12.5, 32.0, 0.0, 26.0, ALLEY, 11.6, rig_mat("OF_OccBrick", (0.30, 0.13, 0.08)))

if scene.world is None:
    scene.world = bpy.data.worlds.new("OF_Sky")
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
    light_img = bake_target("OF_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask (RGB) ----------------------------------------------------------
    grime_mat = bpy.data.materials.get("OF_GrimeBake") or bpy.data.materials.new("OF_GrimeBake")
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

    rear_part = map_range(Y, AY1 + 0.02, AY1 + 0.10, 0.0, 1.0)          # brick B
    side = map_range(math_op("ABSOLUTE", NX), 0.6, 0.8, 0.0, 1.0)       # side walls (clapboard, brick)
    rearwall = map_range(NY, 0.6, 0.8, 0.0, 1.0)
    walls_low = math_op("MAXIMUM", math_op("MAXIMUM", side, rearwall), rear_part)
    # dark band on the bottom 0.4 m of the clapboard and brick, fading by 0.8 m; lighter on the front
    band = mult(walls_low, map_range(Z, -0.15, 0.80, 1.0, 0.0))
    height = math_op("SUBTRACT", map_range(Z, -0.15, 0.6, 0.88, 1.0), mult(band, 0.16))
    blotch = map_range(noise_tex(geo.outputs["Position"], 0.6, 6.0), 0.0, 1.0, 0.92, 1.03)
    stretch = N("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (4.0, 4.0, 0.18)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_n = noise_tex(stretch.outputs["Vector"], 1.7, 2.0)
    streaks = map_range(streak_n, 0.35, 0.75, 0.95, 1.0)
    # brick rear: duller, streakier
    bc = math_op("SUBTRACT", 1.0, mult(rear_part, math_op("ADD", 0.05, map_range(streak_n, 0.3, 0.75, 0.10, 0.0))))
    # soot under the cornice (front and side walls, fading 0.6 m down from the frieze)
    under_corn = mult(map_range(Z, FRIEZE0 - 0.60, FRIEZE0, 0.0, 1.0), map_range(Z, FRIEZE0 + 0.30, FRIEZE0 + 0.32, 1.0, 0.0),
                      map_range(Y, AY1 - 0.05, AY1, 1.0, 0.0))
    # soot on upward faces of the front (hood tops, sills, belt) above the shop front
    up = map_range(NZ, 0.8, 0.95, 0.0, 1.0)
    front_zone = mult(map_range(Y, 0.30, 0.20, 0.0, 1.0), map_range(Z, 3.65, 3.75, 0.0, 1.0),
                      map_range(Z, 10.0, 10.1, 1.0, 0.0))
    soot = math_op("SUBTRACT", 1.0, math_op("ADD", mult(under_corn, 0.14), mult(up, front_zone, 0.22)))
    # faint streaks below the front window sills
    front = map_range(NY, -0.6, -0.8, 0.0, 1.0)
    fx = near(X, list(WIN_X), 0.50, 0.62)
    under_sill = None
    for z0 in (W3[0], W2[0]):
        s = mult(map_range(Z, z0 - 0.75, z0 - 0.10, 0.0, 1.0), map_range(Z, z0 - 0.09, z0 - 0.07, 1.0, 0.0))
        under_sill = s if under_sill is None else math_op("MAXIMUM", under_sill, s)
    drips = math_op("SUBTRACT", 1.0, mult(front, fx, under_sill, map_range(streak_n, 0.3, 0.7, 0.14, 0.04)))
    # worn treads in the door recesses
    treads = map_range(mult(up, map_range(Z, 0.05, 0.03, 0.0, 1.0), map_range(Z, -0.02, 0.0, 0.0, 1.0)),
                       0.0, 1.0, 1.0, 0.93)
    grey = mult(height, blotch, streaks, bc, soot, drips, treads)
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    col_bc = vmix(rear_part, (1.0, 1.0, 1.0), (0.97, 0.97, 0.98))
    attr = N("ShaderNodeAttribute")
    attr.attribute_name = "Tint"
    rgb = vmul(vmul(gc.outputs["Vector"], col_bc), attr.outputs["Color"])
    L(rgb, emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    grime_img = bake_target("OF_Grime", True)
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
out_img = bpy.data.images.get("OF_Lightmap") or bpy.data.images.new("OF_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
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
r_obj["lightmap_scale"] = LIGHTMAP_SCALE            # read by odd_fellows_hall_preview.py
