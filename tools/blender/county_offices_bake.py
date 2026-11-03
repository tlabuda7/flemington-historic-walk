"""
county_offices_bake.py - textures and baked lighting for the Hunterdon County Offices /
Hall of Records (69-71 Main St), then export to assets/models/county-offices.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/county_offices_bake.py").read())

Steps (pattern: courthouse_bake.py):
 1. Rebuild the geometry (county_offices.py).
 2. Give every surface a CC0 colour texture tiled in real-world metres (box UVs; the
    roof is projected along its slope). The red brick texture is too light and orange,
    so it is multiplied by a constant colour (one for the front, one for the sides) that
    the glTF exporter writes as baseColorFactor; the web page keeps it.
 3. Join the parts into one object, cut it along the wall planes and delete the faces
    nobody can see (inside walls, under the cornice and roof), then unwrap "Lightmap".
 4. Bake warm late-afternoon sun + sky (direct and bounced light) into one 2K lightmap
    with Cycles. West side of Main St (front faces east): the sun comes from behind the
    south-west corner, so the south side is lit and the front is in shade.
 5. Bake a grime mask (dirt near the ground, blotches, faint streaks, a damp band above
    the basement, soot under the cornice, worn stoop treads) and multiply it in.
 6. Export the GLB. Other collections are hidden from render during the bake.
"""

import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PH = PROJECT + r"\assets\textures\polyhaven" + "\\"
CO = PROJECT + r"\assets\textures\county-offices" + "\\"
CT = PROJECT + r"\assets\textures\courthouse" + "\\"
GLB = PROJECT + r"\assets\models\county-offices.glb"
LIGHTMAP = PROJECT + r"\assets\textures\county-offices-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 384
TO_SUN = (-0.40, 0.90, 0.36)          # west-side building (front faces east)

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\county_offices.py").read())

# 2. Materials ----------------------------------------------------------------


def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    """Constant colour that turns a texture averaging `avg` (sRGB 0-255) into `target`."""
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


BRICK_AVG = (142, 103, 80)            # measured mean of polyhaven/red_brick.jpg
# part -> (texture file, metres per repeat, roughness, plain colour (linear) or None, tint or None)
LOOK = {
    "BrickFront": (PH + "red_brick.jpg", 1.4, 0.9, None, tint(BRICK_AVG, (0x8E, 0x3F, 0x2C))),
    "BrickSide":  (PH + "red_brick.jpg", 1.4, 0.9, None, tint(BRICK_AVG, (0x87, 0x45, 0x2F))),
    "Stone":      (CO + "stone_buff.jpg", 1.6, 0.9, None, None),
    "Trim":       (CO + "trim_paint_drab.jpg", 2.0, 0.7, None, None),
    "Shutter":    (PH + "trim_paint_cream.jpg", 2.0, 0.7, None, tint((230, 218, 191), (0xD9, 0xCF, 0xB4))),
    "Roof":       (CO + "roof_tin_redbrown.jpg", 2.0, 0.6, None, None),
    "Door":       (CO + "door_varnish_dark.jpg", 0.8, 0.5, None, None),
    "Rock":       (CT + "rock_wall_08.jpg", 1.8, 0.95, None, None),
    "Glass":      (None, 1.0, 0.08, (0.010, 0.012, 0.013), None),    # old window glass, very dark
    "Iron":       (None, 1.0, 0.6, (0.011, 0.011, 0.011), None),     # black iron
}


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


FINAL = {k: textured_material("COR_" + k, LOOK[k][0], *LOOK[k][2:]) for k in LOOK}


def box_uvs(obj):
    """Project each face from its dominant axis so textures keep real-world scale; the
    tile size comes from the face's material. Sloping roof faces are projected along
    the slope (u level, v up-slope)."""
    mesh = obj.data
    while mesh.uv_layers:
        mesh.uv_layers.remove(mesh.uv_layers[0])
    uv = mesh.uv_layers.new(name="UVMap")
    tiles = [LOOK[m.name[3:]][1] for m in mesh.materials]
    for poly in mesh.polygons:
        tile = tiles[poly.material_index]
        n = poly.normal
        h = math.hypot(n.x, n.y)
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            if 0.25 < abs(n.z) < 0.97:
                tx, ty = -n.y / h, n.x / h
                u, v = co.x * tx + co.y * ty, co.z / h
            elif ax == 2:
                u, v = co.x, co.y
            elif ax == 0:
                u, v = co.y, co.z
            else:
                u, v = co.x, co.z
            uv.data[li].uv = (u / tile, v / tile)


parts = [o for o in col.objects if o.type == "MESH"]
for obj in parts:
    box_uvs(obj)                                  # reads the CO_<key> slot names
    for i, m in enumerate(obj.data.materials):
        obj.data.materials[i] = FINAL[m.name[3:]]

# 3. Join, drop hidden faces, unwrap the lightmap UVs --------------------------
co_obj = bpy.data.objects["CO_Walls"]
with bpy.context.temp_override(active_object=co_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
co_obj.name = co_obj.data.name = "CountyOffices"
mesh = co_obj.data


def fibonacci(n):
    pts = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        a = i * math.pi * (3 - math.sqrt(5))
        pts.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    return pts


def face_samples(f, tris, rng):
    """Points spread over the face (about one per 0.02 m2, 6 to 3000), so a face that
    is only partly covered still finds its visible part."""
    area = f.calc_area()
    n = int(min(3000, max(6, area / 0.02)))
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
    # Pull points a little in from the edges: a point right on the edge of a face that is
    # covered by a touching solid (cornice top under the roof) would otherwise "see" past it.
    c = pts[0]
    out = []
    for p in pts:
        v = c - p
        d = v.length
        out.append(p + v * (min(0.015, 0.25 * d) / d) if d > 1e-6 else p)
    return out


def remove_hidden_faces(obj, rays=120):
    """Delete faces that no ray from any of their sample points can leave the model
    through (inside walls, under the cornice and roof, behind glass). Downward faces at
    or below grade go too; the 0.2 m skirt's outer faces stay."""
    import random
    rng = random.Random(7)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    # Cut the stacked plan slabs (cornice layers, water table, string course) and the
    # shells along the wall lines first, so their hidden middles become separate faces.
    for co, no in CUT_PLANES:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-4,
                               plane_co=co, plane_no=no)
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
        if n.z < -0.9 and c.z < 0.01:                     # undersides at or below grade
            dead.append(f)
            continue
        hemi = [d for d in dirs if d.dot(n) > 0.04]
        samples = face_samples(f, face_tris.get(f, []), rng)
        seen = False
        for p in samples:
            o = p + n * 0.004
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


CUT_PLANES = [((HW, 0, 0), (1, 0, 0)), ((-HW, 0, 0), (1, 0, 0)),
              ((0, 0, 0), (0, 1, 0)), ((0, BACK, 0), (0, 1, 0)),
              # window/door frames start 8-9 cm inside the wall face: cut the reveals there
              # so the visible brick strip is its own face and the part behind the frame goes
              ((HW - 0.075, 0, 0), (1, 0, 0)), ((-HW + 0.075, 0, 0), (1, 0, 0)),
              ((0, 0.075, 0), (0, 1, 0)), ((0, BACK - 0.075, 0), (0, 1, 0))]
before = sum(len(p.vertices) - 2 for p in mesh.polygons)
removed = remove_hidden_faces(co_obj)
after = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("hidden faces removed:", removed, "| triangles", before, "->", after)

lm = mesh.uv_layers.new(name="Lightmap")
mesh.uv_layers.active = lm
mesh.uv_layers["UVMap"].active_render = True
for o in bpy.context.view_layer.objects:
    o.select_set(o == co_obj)
bpy.context.view_layer.objects.active = co_obj
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004,
                         area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.object.mode_set(mode="OBJECT")
# Give the lightmap's pixels to what matters: shrink dark or out-of-the-way parts.
LM_SHRINK = {"COR_Glass": 0.35, "COR_Iron": 0.4, "COR_Door": 0.6, "COR_Roof": 0.5}
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    f = LM_SHRINK.get(mat_names[p.material_index])
    if f is None and p.center.y > BACK - 0.5:
        f = 0.6                                  # the rear (unseen from the street)
    if f:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.0015, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig: sun, sky, ground (in "CO_BakeRig", not exported) ---------------------
scene = bpy.context.scene
rig = bpy.data.collections.get("CO_BakeRig")
if not rig:
    rig = bpy.data.collections.new("CO_BakeRig")
    scene.collection.children.link(rig)
sun = bpy.data.objects.get("CO_Sun")
if not sun:
    sun = bpy.data.objects.new("CO_Sun", bpy.data.lights.new("CO_Sun", "SUN"))
    rig.objects.link(sun)
sun.data.energy = 3.2
sun.data.color = (1.0, 0.80, 0.58)
sun.data.angle = math.radians(1.5)
to_sun = Vector(TO_SUN).normalized()            # about 21 degrees above the horizon
sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()

ground = bpy.data.objects.get("CO_Ground")
if not ground:
    gm = bpy.data.meshes.new("CO_Ground")
    S = 120.0
    gm.from_pydata([(-S, -S, 0), (S, -S, 0), (S, S, 0), (-S, S, 0)], [], [(0, 1, 2, 3)])
    gmat = bpy.data.materials.get("CO_GroundWarm") or bpy.data.materials.new("CO_GroundWarm")
    gmat.use_nodes = True
    # warm lawn / paving bounce (keeps the shaded front from turning blue)
    next(n for n in gmat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.30, 0.26, 0.19, 1)
    gm.materials.append(gmat)
    ground = bpy.data.objects.new("CO_Ground", gm)
    rig.objects.link(ground)

if scene.world is None:
    scene.world = bpy.data.worlds.new("CO_Sky")
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

# Hide every other collection from render while baking (other buildings, previews).
render_state = {}
for c in bpy.data.collections:
    render_state[c.name] = c.hide_render
    c.hide_render = c.name not in ("CountyOffices", "CO_BakeRig")

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


try:
    light_img = bake_target("CO_Light", True)
    point_materials_at(light_img)
    # No bake margin: the fill after the bake covers every empty pixel from its neighbours.
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask --------------------------------------------------------------
    grime_mat = bpy.data.materials.get("CO_GrimeBake") or bpy.data.materials.new("CO_GrimeBake")
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

    def mult(a, b):
        return math_op("MULTIPLY", a, b)

    height = map_range(sep.outputs["Z"], 0.0, 1.4, 0.76, 1.0)            # dirt splashed up from the ground
    noise = N("ShaderNodeTexNoise")                                       # blotchy fading
    noise.inputs["Scale"].default_value = 0.5
    noise.inputs["Detail"].default_value = 6.0
    L(geo.outputs["Position"], noise.inputs["Vector"])
    blotch = map_range(noise.outputs["Fac"], 0.0, 1.0, 0.89, 1.03)
    stretch = N("ShaderNodeVectorMath")                                   # faint vertical streaks
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (3.0, 3.0, 0.15)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_noise = N("ShaderNodeTexNoise")
    streak_noise.inputs["Scale"].default_value = 1.6
    streak_noise.inputs["Detail"].default_value = 2.0
    L(stretch.outputs["Vector"], streak_noise.inputs["Vector"])
    streaks = map_range(streak_noise.outputs["Fac"], 0.35, 0.75, 0.93, 1.0)
    # soot under the cornice: a band darkening up to the soffit, clean again above it
    soot = math_op("ADD", map_range(sep.outputs["Z"], 7.2, 8.35, 1.0, 0.84),
                   map_range(sep.outputs["Z"], 8.35, 8.7, 0.0, 0.16))
    # worn stoop treads: upward faces in front of the wall, below the first floor, near a
    # stoop's centre line (x = 0, +-3.8)
    ax_ = math_op("ABSOLUTE", sep.outputs["X"])
    d_side = math_op("ABSOLUTE", math_op("SUBTRACT", ax_, 3.8))
    d = math_op("MINIMUM", ax_, d_side)
    centre = map_range(d, 0.15, 0.6, 1.0, 0.0)
    up = map_range(nsep.outputs["Z"], 0.8, 0.95, 0.0, 1.0)
    in_front = map_range(sep.outputs["Y"], -0.05, 0.05, 1.0, 0.0)
    low = map_range(sep.outputs["Z"], 1.22, 1.3, 1.0, 0.0)
    wear = map_range(mult(mult(centre, up), mult(in_front, low)), 0.0, 1.0, 1.0, 0.86)
    grey = mult(mult(mult(height, blotch), mult(streaks, soot)), wear)
    # greenish-grey damp band in the brick just above the stone basement
    band = mult(map_range(sep.outputs["Z"], 1.2, 1.55, 1.0, 0.0), map_range(sep.outputs["Z"], 1.15, 1.22, 0.0, 1.0))

    def sock(socks, name):        # the Mix node has float/vector/colour sockets with the same name
        return next(x for x in socks if x.name == name and x.type == "RGBA")

    tint_n = N("ShaderNodeMix")
    tint_n.data_type = "RGBA"
    L(band, tint_n.inputs["Factor"])
    sock(tint_n.inputs, "A").default_value = (1, 1, 1, 1)
    sock(tint_n.inputs, "B").default_value = (0.84, 0.90, 0.82, 1)
    col_mul = N("ShaderNodeMix")
    col_mul.data_type = "RGBA"
    col_mul.blend_type = "MULTIPLY"
    col_mul.inputs["Factor"].default_value = 1.0
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    L(gc.outputs["Vector"], sock(col_mul.inputs, "A"))
    L(sock(tint_n.outputs, "Result"), sock(col_mul.inputs, "B"))
    L(sock(col_mul.outputs, "Result"), emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    grime_img = bake_target("CO_Grime", True)
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
# Warm the shade slightly: sky-only light is blue; pull each pixel's blue/green toward
# its red a little so painted trim in shade stays warm (courthouse lesson).
lum = combined.mean(axis=1, keepdims=True)
combined = combined * 0.85 + lum * np.array([[1.0, 0.97, 0.90]]) * 0.15
scale = float(np.percentile(combined[baked].max(axis=1), 99.5))
# Fill every unbaked pixel (window holes, gaps between islands) from its baked neighbours.
img2 = combined.reshape(LIGHTMAP_SIZE, LIGHTMAP_SIZE, 3).copy()
filled = baked.reshape(LIGHTMAP_SIZE, LIGHTMAP_SIZE).copy()
for _ in range(96):
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
out_img = bpy.data.images.get("CO_Lightmap") or bpy.data.images.new("CO_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
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

# Remove the bake helper nodes so they are not exported.
for mat in mesh.materials:
    for name in ("BakeTarget", "BakeUV"):
        node = mat.node_tree.nodes.get(name)
        if node:
            mat.node_tree.nodes.remove(node)

# 6. Export ---------------------------------------------------------------------
for o in bpy.context.scene.objects:
    o.select_set(o == co_obj)
bpy.context.view_layer.objects.active = co_obj
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_texcoords=True,
                          export_normals=True)
tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("exported", GLB, "|", tris, "triangles |", len(mesh.materials), "materials")
co_obj["lightmap_scale"] = LIGHTMAP_SCALE            # read by county_offices_preview.py
