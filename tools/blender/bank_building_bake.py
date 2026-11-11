"""
bank_building_bake.py - textures and baked lighting for the Bank Building / Flemington
National Bank (56-66 Main St), then export to assets/models/bank-building.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/bank_building_bake.py").read())

Steps (pattern: county_offices_bake.py / wurts_law_office_bake.py):
 1. Rebuild the geometry (bank_building.py).
 2. Give every surface a CC0 colour texture tiled in real-world metres (box UVs). Nine
    materials (= nine draw calls): brick (buff), stone (brown), trim, glass, dark, awning,
    window backs, bank hall and terra cotta ornament (atlas UVs from bank_building.py). The
    trim paint is a shade too light, so it is multiplied by a constant colour that the glTF
    exporter writes as baseColorFactor.
    The awning stripes run down the slope (U along the front, V down the canvas).
 3. Join the parts into one object, cut it along the wall planes and delete the faces
    nobody can see (inside walls, behind bands and stoops), then unwrap "Lightmap".
 4. Bake warm late-afternoon sun + sky (direct and bounced light) into one 2K lightmap
    with Cycles. East side of Main St (front faces west): the low WSW sun lights the front
    and the south wall; the Bloomfield (north) side is in shade.
 5. Bake a grime mask (dirt splash near the ground, blotches, faint streaks, soot under
    the cornice and on the chimney top, a darker shaded north side, worn stoop treads)
    and multiply it in.
 6. Export the GLB. Other collections are hidden from render during the bake.

Windows (PLAN.md "E. Windows that don't read as flat black", 2026-11-10; same as the Nevius
Store and the Union Hotel): every pane is a single glass face in its own material named `glass`
(warm grey dust tint GLASS_RGB, alpha GLASS_ALPHA, roughness 0.05, alpha blend, single-sided)
about 4 cm in front of a window back: BKR_WindowBack (shared atlas
assets/textures/shared/window_backs.jpg) upstairs, at the rear, the basement lights and the
stair door; BKR_BankHall (assets/textures/shared/bank_hall.jpg, tools/prepare_bank_hall.py)
behind the bank window and door, the banking room's Bloomfield Ave windows and the shop fronts.
Their atlas UVs come from bank_building.py. The backs are lightmapped like everything else; the
glass keeps Lightmap UVs (squeezed to almost nothing) but the scene draws it WITHOUT the
lightmap, with a sky reflection (`glass-reflect`). During the bake the glass is fully
transparent so the backs behind it get their light, and the hidden-face pass looks through it.
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
BB = PROJECT + r"\assets\textures\bank-building" + "\\"
GLB = PROJECT + r"\assets\models\bank-building.glb"
LIGHTMAP = PROJECT + r"\assets\textures\bank-building-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 384
SHARED = PROJECT + r"\assets\textures\shared" + "\\"
GLASS_ALPHA = 0.40
GLASS_RGB = (0x1A, 0x19, 0x16)       # faint warm grey dust tint (as the Nevius Store, Union Hotel)
ATLAS = ("WindowBack", "BankHall", "Ornament")   # keep the atlas UVs made by bank_building.py
TO_SUN = (0.40, -0.90, 0.36)          # east-side building (front faces west)
COLL, RIG, PREFIX = "BankBuilding", "BK_BakeRig", "BK_"

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\bank_building.py").read())

# 2. Materials ----------------------------------------------------------------


def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    """Constant colour that turns a texture averaging `avg` (sRGB 0-255) into `target`."""
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


# part -> (texture file, metres per repeat, roughness, plain colour (linear) or None, tint or None)
LOOK = {
    # colour fix 2026-11-11: unpainted buff brick and brown rock-faced stone (modern photo + NRHP);
    # the colours are in the textures (tools/prepare_bank_colour.py), no tint
    "Brick":  (BB + "brick_buff.jpg", 1.4, 0.9, None, None),
    "Stone":  (BB + "stone_brown.jpg", 3.4, 0.95, None, None),
    "Trim":   (CO + "trim_paint_drab.jpg", 2.0, 0.7, None, tint((0xBD, 0xB4, 0xA0), (0xB5, 0xAC, 0x98))),
    "Glass":  (None, 1.0, 0.05, tuple(srgb_to_lin(c) for c in GLASS_RGB), None),
    "Dark":   (CO + "door_varnish_dark.jpg", 0.8, 0.5, None, None),
    "Awning": (BB + "awning_stripes.jpg", 0.6, 0.9, None, None),
    "WindowBack": (SHARED + "window_backs.jpg", None, 0.9, None, None),
    "BankHall":   (SHARED + "bank_hall.jpg", None, 0.9, None, None),
    "Ornament":   (BB + "terracotta_ornament.jpg", None, 0.85, None, None),   # terra cotta frieze, roundels, keystones
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
    if name == "glass":   # transparent, drawn with a sky reflection by the scene
        bsdf.inputs["Alpha"].default_value = GLASS_ALPHA
        mat.use_backface_culling = True
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        elif hasattr(mat, "blend_method"):
            mat.blend_method = "BLEND"
    return mat


FINAL = {k: textured_material("glass" if k == "Glass" else "BKR_" + k, LOOK[k][0], *LOOK[k][2:]) for k in LOOK}


def box_uvs(obj):
    """Project each face from its dominant axis so textures keep real-world scale; the
    tile size comes from the face's material. Sloping faces are projected along the
    slope. Awning canvas: U along the front (x), V down the slope, so the stripes run
    downhill on the top, the underside and the valance alike."""
    mesh = obj.data
    for layer in [l for l in mesh.uv_layers if l.name != "UVMap"]:
        mesh.uv_layers.remove(layer)
    uv = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    keys = [m.name[len(PREFIX):] for m in mesh.materials]
    for poly in mesh.polygons:
        key = keys[poly.material_index]
        if key in ATLAS:               # window backs keep their atlas UVs
            continue
        tile = LOOK[key][1]
        n = poly.normal
        h = math.hypot(n.x, n.y)
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            if key == "Awning":
                u, v = co.x, -(0.846 * co.y + 0.532 * co.z)    # distance down the slope
            elif 0.25 < abs(n.z) < 0.97:
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
    box_uvs(obj)                                  # reads the BK_<key> slot names
    for i, m in enumerate(obj.data.materials):
        obj.data.materials[i] = FINAL[m.name[len(PREFIX):]]

# 3. Join, drop hidden faces, unwrap the lightmap UVs --------------------------
bk_obj = bpy.data.objects["BK_Upper"]
with bpy.context.temp_override(active_object=bk_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
bk_obj.name = bk_obj.data.name = COLL
mesh = bk_obj.data


def fibonacci(n):
    pts = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        a = i * math.pi * (3 - math.sqrt(5))
        pts.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    return pts


def face_samples(f, tris, rng):
    """Points spread over the face (about one per 0.01 m2, 6 to 3000), so a face that
    is only partly covered still finds its visible part."""
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
    # Pull points a little in from the edges: a point right on the edge of a face that is
    # covered by a touching solid would otherwise "see" past it.
    c = pts[0]
    out = []
    for p in pts:
        v = c - p
        d = v.length
        out.append(p + v * (min(0.008, 0.25 * d) / d) if d > 1e-6 else p)
    return out


def remove_hidden_faces(obj, rays=120):
    """Delete faces that no ray from any of their sample points can leave the model
    through (inside walls, behind bands, piers, stoops and glass). Downward faces at or
    below grade go too."""
    import random
    rng = random.Random(7)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for co, no in CUT_PLANES:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-4,
                               plane_co=co, plane_no=no)
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
        if n.z < -0.9 and c.z < 0.01:                     # undersides at or below grade
            dead.append(f)
            continue
        hemi = [d for d in dirs if d.dot(n) > 0.04]
        samples = face_samples(f, face_tris.get(f, []), rng)
        seen = False
        for p in samples:
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


# the main wall planes: sills, piers and bands that run into or along the walls are cut
# there so their hidden parts become separate faces
CUT_PLANES = [((0, 0, 0), (0, 1, 0)), ((-HW, 0, 0), (1, 0, 0)), ((HW, 0, 0), (1, 0, 0))]
before = sum(len(p.vertices) - 2 for p in mesh.polygons)
removed = remove_hidden_faces(bk_obj)
after = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("hidden faces removed:", removed, "| triangles", before, "->", after)

lm = mesh.uv_layers.new(name="Lightmap")
mesh.uv_layers.active = lm
mesh.uv_layers["UVMap"].active_render = True
for o in bpy.context.view_layer.objects:
    o.select_set(o == bk_obj)
bpy.context.view_layer.objects.active = bk_obj
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004,
                         area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.object.mode_set(mode="OBJECT")
# Give the lightmap's pixels to what matters: shrink dark, hidden-from-the-street parts.
LM_SHRINK = {"glass": 0.03, "BKR_Dark": 0.6, "BKR_WindowBack": 0.6, "BKR_BankHall": 0.8}
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    f = LM_SHRINK.get(mat_names[p.material_index])
    c = p.center
    if mat_names[p.material_index] == "BKR_Dark" and p.normal.z > 0.5:
        f = 0.2                                  # roof (never seen from the street)
    elif mat_names[p.material_index] not in ("glass", "BKR_WindowBack") and \
            (c.y > BS - 0.3 and c.x > XC - 0.3 or c.y > BN - 0.3):
        f = 0.5                                  # rear and courtyard walls
    if f:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.0015, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig: sun, sky, ground (in BK_BakeRig, not exported) -------------------
scene = bpy.context.scene
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
sun = bpy.data.objects.get("BK_Sun")
if not sun:
    sun = bpy.data.objects.new("BK_Sun", bpy.data.lights.new("BK_Sun", "SUN"))
    rig.objects.link(sun)
sun.data.energy = 3.2
sun.data.color = (1.0, 0.80, 0.58)
sun.data.angle = math.radians(1.5)
to_sun = Vector(TO_SUN).normalized()            # about 21 degrees above the horizon
sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()

ground = bpy.data.objects.get("BK_Ground")
if not ground:
    gm = bpy.data.meshes.new("BK_Ground")
    S = 120.0
    # sidewalk / front strip at 0; Bloomfield Ave (north of the building) 0.15 lower
    gm.from_pydata([(-HW, -S, 0), (S, -S, 0), (S, S, 0), (-HW, S, 0),
                    (-S, -S, -0.15), (-HW, -S, -0.15), (-HW, S, -0.15), (-S, S, -0.15)], [],
                   [(0, 1, 2, 3), (4, 5, 6, 7)])
    gmat = bpy.data.materials.get("BK_GroundWarm") or bpy.data.materials.new("BK_GroundWarm")
    gmat.use_nodes = True
    # warm paving / dirt-road bounce (keeps the shaded north side from turning blue)
    next(n for n in gmat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.32, 0.27, 0.19, 1)
    gm.materials.append(gmat)
    ground = bpy.data.objects.new("BK_Ground", gm)
    rig.objects.link(ground)

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

# Hide every other collection from render while baking (other buildings, previews).
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


glass_alpha = next(n for n in FINAL["Glass"].node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"]
glass_alpha.default_value = 0.0             # light passes the panes to the window backs
try:
    light_img = bake_target("BK_Light", True)
    point_materials_at(light_img)
    # No bake margin: the fill after the bake covers every empty pixel from its neighbours.
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask --------------------------------------------------------------
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

    # dirt and splash on the bottom ~0.5 m of the stone, fading out by 1.3 m
    height = map_range(sep.outputs["Z"], -0.1, 1.3, 0.74, 1.0)
    noise = N("ShaderNodeTexNoise")                                       # blotchy fading
    noise.inputs["Scale"].default_value = 0.5
    noise.inputs["Detail"].default_value = 6.0
    L(geo.outputs["Position"], noise.inputs["Vector"])
    blotch = map_range(noise.outputs["Fac"], 0.0, 1.0, 0.88, 1.03)
    stretch = N("ShaderNodeVectorMath")                                   # streaks under sills and lintels
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (3.5, 3.5, 0.15)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_noise = N("ShaderNodeTexNoise")
    streak_noise.inputs["Scale"].default_value = 1.8
    streak_noise.inputs["Detail"].default_value = 2.0
    L(stretch.outputs["Vector"], streak_noise.inputs["Vector"])
    streaks = map_range(streak_noise.outputs["Fac"], 0.35, 0.75, 0.91, 1.0)
    # soot under the cornice corona and on the frieze; clean above the corona
    soot = math_op("ADD", map_range(sep.outputs["Z"], 9.6, 11.74, 1.0, 0.80),
                   map_range(sep.outputs["Z"], 11.74, 11.80, 0.0, 0.20))
    chim = map_range(sep.outputs["Z"], 12.6, 13.2, 1.0, 0.60)            # chimney top
    # shaded north (Bloomfield) side a little darker
    north = map_range(nsep.outputs["X"], -0.9, -0.6, 0.92, 1.0)
    # worn stoop treads: upward faces in front of the wall, below the floor, near a stoop's
    # centre line (bank -5.136, shops -1.712, 1.712, 5.136, 9.37)
    d = None
    for sx in (-5.136, -1.712, 1.712, 5.136, 9.37):
        dd = math_op("ABSOLUTE", math_op("SUBTRACT", sep.outputs["X"], sx))
        d = dd if d is None else math_op("MINIMUM", d, dd)
    centre = map_range(d, 0.12, 0.5, 1.0, 0.0)
    up = map_range(nsep.outputs["Z"], 0.8, 0.95, 0.0, 1.0)
    in_front = map_range(sep.outputs["Y"], 0.0, 0.05, 1.0, 0.0)
    low = map_range(sep.outputs["Z"], 0.92, 1.0, 1.0, 0.0)
    wear = map_range(mult(mult(centre, up), mult(in_front, low)), 0.0, 1.0, 1.0, 0.84)
    grey = mult(mult(mult(height, blotch), mult(streaks, soot)), mult(mult(chim, north), wear))
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    L(gc.outputs["Vector"], emit.inputs["Color"])
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
# Warm the shade: sky-only light is blue; pull each pixel's blue/green toward its red a
# little so the shaded north side and the pale trim in shade stay warm.
lum = combined.mean(axis=1, keepdims=True)
combined = combined * 0.75 + lum * np.array([[1.0, 0.96, 0.88]]) * 0.25
scale = float(np.percentile(combined[baked].max(axis=1), 99.5))
# Fill every unbaked pixel (gaps between islands) from its baked neighbours.
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

# Remove the bake helper nodes so they are not exported.
for mat in mesh.materials:
    for name in ("BakeTarget", "BakeUV"):
        node = mat.node_tree.nodes.get(name)
        if node:
            mat.node_tree.nodes.remove(node)

# 6. Export ---------------------------------------------------------------------
for o in bpy.context.scene.objects:
    o.select_set(o == bk_obj)
bpy.context.view_layer.objects.active = bk_obj
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_texcoords=True,
                          export_normals=True)
tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("exported", GLB, "|", tris, "triangles |", len(mesh.materials), "materials")
bk_obj["lightmap_scale"] = LIGHTMAP_SCALE            # read by bank_building_preview.py
