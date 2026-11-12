"""
courthouse_bake.py - textures and baked lighting for the Hunterdon County Court House,
then export to assets/models/courthouse.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/courthouse_bake.py").read())

Steps (pattern: union_hotel_bake.py):
 1. Rebuild the geometry (courthouse.py).
 2. Give every surface a Poly Haven colour texture (CC0), tiled in real-world metres
    (box UVs; sloping roofs are projected along the slope so the slate courses run level).
 3. Join the parts into one object, delete faces nobody can see (inside walls, attic,
    under the podium), and unwrap a second UV map, "Lightmap".
 4. Bake warm late-afternoon sun + sky (direct and bounced light) into one 2K lightmap
    with Cycles. The courthouse is on the west side of Main St (front faces east), so the
    sun comes from behind its south-west corner: the south side is lit, the front in shade.
 5. Bake a grime mask (darker near the ground, blotches, faint vertical streaks, damp tint
    above the base course, soot at the chimney tops) and multiply it in.
 6. Export the GLB. Other buildings' collections are hidden from render during the bake.

Windows (PLAN.md section E, 2026-11-11): the window backs (material CHR_WBack, cells of
assets/textures/shared/window_backs.jpg, UVs from BACKREC) are lightmapped like everything
else; the panes are one material named exactly `glass` (#1A1916, alpha 0.40, roughness 0.05,
BLEND, single-sided) that the scene leaves unlit and gives a sky reflection (`glass-reflect`).
The glass is fully transparent during the bake, ignored by the hidden-face pass, and its
Lightmap UVs are squeezed small (it does not use them).
"""

import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PH = PROJECT + r"\assets\textures\polyhaven" + "\\"
CT = PROJECT + r"\assets\textures\courthouse" + "\\"
GLB = PROJECT + r"\assets\models\courthouse.glb"
LIGHTMAP = PROJECT + r"\assets\textures\courthouse-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 384
GLASS_ALPHA = 0.40
TO_SUN = (-0.40, 0.90, 0.36)          # west-side building (front faces east)

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\courthouse.py").read())

# 2. Materials ----------------------------------------------------------------
# part -> (texture file, metres covered by one repeat, roughness, plain colour if no texture)
LOOK = {
    # review round 1: warmer cream stucco and smoother, whiter paint (tools/prepare_courthouse_paints.py)
    "Walls":      (CT + "stucco_cream.jpg", 2.0, 0.9, None),
    "Stucco":     (CT + "stucco_cream.jpg", 2.0, 0.9, None),
    "Trim":       (CT + "paint_white.jpg", 2.0, 0.7, None),
    "Drum":       (CT + "paint_white.jpg", 2.0, 0.7, None),
    "Brownstone": (CT + "brownstone.jpg", 2.15, 0.9, None),
    "Slate":      (PH + "roof_slates_03.jpg", 3.0, 0.8, None),
    "Dome":       (CT + "dome_paint_green.jpg", 1.0, 0.5, None),
    "Brick":      (PH + "red_brick.jpg", 1.4, 0.9, None),
    "Wing":       (CT + "clapboard_buff.jpg", 1.0, 0.8, None),
    "Clapboard":  (CT + "clapboard_buff.jpg", 1.0, 0.8, None),
    "RockWall":   (CT + "rock_wall_grey.jpg", 1.8, 0.95, None),
    "Door":       (PH + "door_paint_green.jpg", 0.8, 0.7, None),
    "Sash":       (None, 1.0, 0.6, (0.012, 0.018, 0.014)),     # dark green-black paint
    "Glass":      (None, 1.0, 0.05, (0.01033, 0.00972, 0.00802)),  # section E: #1A1916 dust tint
    "WBack":      (PROJECT + r"\assets\textures\shared\window_backs.jpg", 1.0, 0.9, None),
    "Iron":       (None, 1.0, 0.6, (0.012, 0.012, 0.012)),
    "Alarm":      (None, 1.0, 0.6, (0.25, 0.025, 0.017)),      # fire-alarm red
}


def textured_material(name, image_file, roughness, colour):
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


def back_uvs(obj):
    """Window backs: each face shows its atlas cell (BACKREC, by the face's rid)."""
    mesh = obj.data
    while mesh.uv_layers:
        mesh.uv_layers.remove(mesh.uv_layers[0])
    uv = mesh.uv_layers.new(name="UVMap")
    rid_attr = mesh.attributes.get("rid")
    for poly in mesh.polygons:
        rec = BACKREC[rid_attr.data[poly.index].value]
        U0, V0, U1, V1 = rec["uv"]
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            u = co.x if rec["axis"] == "y" else co.y
            fu = (u - rec["u0"]) / (rec["u1"] - rec["u0"])
            fz = (co.z - rec["z0"]) / (rec["z1"] - rec["z0"])
            uv.data[li].uv = (U0 + (U1 - U0) * fu, V0 + (V1 - V0) * fz)


def box_uvs(obj, tile):
    """Project each face from its dominant axis, so textures keep real-world scale.
    Sloping faces (roofs, dome) are projected along their slope: u level, v up-slope."""
    mesh = obj.data
    while mesh.uv_layers:
        mesh.uv_layers.remove(mesh.uv_layers[0])
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
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


# Parts that look the same share one material (one draw call each in the scene).
SHARE = {"Walls": "Stucco", "Drum": "Trim", "Wing": "Clapboard", "Iron": "Sash"}
parts = [o for o in col.objects if o.type == "MESH"]
for obj in parts:
    key = obj.name.split(".")[0][3:]
    image_file, tile, rough, colour = LOOK[key]
    name = "glass" if key == "Glass" else "CHR_" + SHARE.get(key, key)
    mat = bpy.data.materials.get(name)
    if not (mat and any(o.data.materials and o.data.materials[0] == mat for o in parts)):
        mat = textured_material(name, image_file, rough, colour)
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    if key == "WBack":
        back_uvs(obj)
    else:
        box_uvs(obj, tile)

# soot on the chimney tops (a vertex value the grime bake reads; removed before export)
brick = bpy.data.objects["CH_Brick"]
soot = brick.data.attributes.new("soot", "FLOAT", "POINT")
for v in brick.data.vertices:
    soot.data[v.index].value = min(max((v.co.z - 13.6) / 1.2, 0.0), 1.0)

# The whole front lies in shade under the deep portico: lift its window backs in the lightmap
# (x FRONT_BACK_LIFT, through the grime bake) so the rooms still read behind the glass, as the
# County Hotel does under its veranda. A vertex value, removed before export.
FRONT_BACK_LIFT = 1.5
wb_obj = bpy.data.objects["CH_WBack"]
lift = wb_obj.data.attributes.new("lift", "FLOAT", "POINT")
for v in wb_obj.data.vertices:
    lift.data[v.index].value = 1.0 if (v.co.y < PORT + 0.4 and v.co.z < ARCH_BOT) else 0.0

# 3. Join, drop hidden faces, unwrap the lightmap UVs --------------------------
ch = bpy.data.objects["CH_Walls"]
with bpy.context.temp_override(active_object=ch, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
ch.name = ch.data.name = "Courthouse"
mesh = ch.data


def fibonacci(n):
    pts = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        a = i * math.pi * (3 - math.sqrt(5))
        pts.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    return pts


def face_samples(f, tris, rng):
    """Points spread over the face: about one per 0.02 m2 (at least 6, at most 3000),
    so a face that is only partly covered (a floor under a pedestal, glass behind a
    meeting rail, a cornice soffit that is mostly inside the entablature) still finds
    its visible part."""
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
    return pts


def remove_hidden_faces(obj, rays=120):
    """Delete faces that no ray from any of their sample points can leave the model
    through: faces inside walls, the attic, under the podium. They would only waste
    triangles and lightmap space. Downward faces at ground level go too."""
    import random
    rng = random.Random(7)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    # Cut the big stacked boxes (podium, entablature layers, cornice, roof slabs) along the
    # wall lines first, so their hidden middles become separate faces that can be dropped
    # while the visible edge strips stay.
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
        if n.z < -0.9 and c.z < 0.01:
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
              ((0, FRONT_FACE, 0), (0, 1, 0)), ((0, FRONT_FACE + 0.10, 0), (0, 1, 0)),
              ((0, PORT, 0), (0, 1, 0)), ((0, BACK - 0.10, 0), (0, 1, 0)), ((0, BACK, 0), (0, 1, 0)),
              ((0, PORT + RECESS, 0), (0, 1, 0)),                       # door threshold
              ((0, WY0, 0), (0, 1, 0)), ((0, WY1, 0), (0, 1, 0)),        # where the wing meets the body
              ((ROOF_X - 0.12, 0, 0), (1, 0, 0)), ((-ROOF_X + 0.12, 0, 0), (1, 0, 0))]   # slate meets cornice
before = sum(len(p.vertices) - 2 for p in mesh.polygons)
removed = remove_hidden_faces(ch)
after = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("hidden faces removed:", removed, "| triangles", before, "->", after)

lm = mesh.uv_layers.new(name="Lightmap")
mesh.uv_layers.active = lm
mesh.uv_layers["UVMap"].active_render = True
for o in bpy.context.view_layer.objects:
    o.select_set(o == ch)
bpy.context.view_layer.objects.active = ch
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004,
                         area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.object.mode_set(mode="OBJECT")
# Give the lightmap's pixels to what matters: shrink the islands of dark or out-of-the-way
# parts (sash, glass, ironwork, the jail yard, the barely visible roof), then repack.
LM_SHRINK = {"CHR_Sash": 0.35, "glass": 0.03, "CHR_WBack": 0.6, "CHR_Door": 0.6,
             "CHR_RockWall": 0.5, "CHR_Clapboard": 0.5, "CHR_Slate": 0.7}
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    f = LM_SHRINK.get(mat_names[p.material_index])
    if f:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, scale=True, margin_method="FRACTION", margin=0.0015,
                        shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig: sun, sky, ground (in the "CH_BakeRig" collection, not exported) -----
scene = bpy.context.scene
rig = bpy.data.collections.get("CH_BakeRig")
if not rig:
    rig = bpy.data.collections.new("CH_BakeRig")
    scene.collection.children.link(rig)
sun = bpy.data.objects.get("CH_Sun")
if not sun:
    sun = bpy.data.objects.new("CH_Sun", bpy.data.lights.new("CH_Sun", "SUN"))
    rig.objects.link(sun)
sun.data.energy = 3.2
sun.data.color = (1.0, 0.80, 0.58)
sun.data.angle = math.radians(1.5)
to_sun = Vector(TO_SUN).normalized()            # about 21 degrees above the horizon
sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()

ground = bpy.data.objects.get("CH_Ground")
if not ground:
    gm = bpy.data.meshes.new("CH_Ground")
    S = 120.0
    gm.from_pydata([(-S, -S, 0), (S, -S, 0), (S, S, 0), (-S, S, 0)], [], [(0, 1, 2, 3)])
    gmat = bpy.data.materials.get("CH_GroundGrey") or bpy.data.materials.new("CH_GroundGrey")
    gmat.use_nodes = True
    next(n for n in gmat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.28, 0.26, 0.23, 1)
    gm.materials.append(gmat)
    ground = bpy.data.objects.new("CH_Ground", gm)
    rig.objects.link(ground)

if scene.world is None:
    scene.world = bpy.data.worlds.new("CH_Sky")
world = scene.world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.42, 0.55, 0.78, 1)
bg.inputs[1].default_value = 0.9

# Hide every other collection from render while baking (other buildings, previews).
render_state = {}
for c in bpy.data.collections:
    render_state[c.name] = c.hide_render
    c.hide_render = c.name not in ("Courthouse", "CH_BakeRig")

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


glass_alpha = next(n for n in bpy.data.materials["glass"].node_tree.nodes
                   if n.type == "BSDF_PRINCIPLED").inputs["Alpha"]
glass_alpha.default_value = 0.0             # light passes the panes to the window backs
try:
    light_img = bake_target("CH_Light", True)
    point_materials_at(light_img)
    # No bake margin: the dilation after the bake fills every empty pixel (gaps between
    # islands and window holes inside the wall islands) from its baked neighbours.
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask --------------------------------------------------------------
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

    def map_range(value_socket, a, b, c, d):
        m = N("ShaderNodeMapRange")
        m.inputs["From Min"].default_value, m.inputs["From Max"].default_value = a, b
        m.inputs["To Min"].default_value, m.inputs["To Max"].default_value = c, d
        L(value_socket, m.inputs["Value"])
        return m.outputs["Result"]

    def mult(a, b):
        m = N("ShaderNodeMath")
        m.operation = "MULTIPLY"
        L(a, m.inputs[0])
        L(b, m.inputs[1])
        return m.outputs["Value"]

    height = map_range(sep.outputs["Z"], 0.0, 1.5, 0.74, 1.0)          # dirt splashed up from the ground
    noise = N("ShaderNodeTexNoise")                                       # blotchy fading
    noise.inputs["Scale"].default_value = 0.5
    noise.inputs["Detail"].default_value = 6.0
    L(geo.outputs["Position"], noise.inputs["Vector"])
    blotch = map_range(noise.outputs["Fac"], 0.0, 1.0, 0.88, 1.03)
    stretch = N("ShaderNodeVectorMath")                                   # faint vertical streaks
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (3.0, 3.0, 0.15)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_noise = N("ShaderNodeTexNoise")
    streak_noise.inputs["Scale"].default_value = 1.6
    streak_noise.inputs["Detail"].default_value = 2.0
    L(stretch.outputs["Vector"], streak_noise.inputs["Vector"])
    streaks = map_range(streak_noise.outputs["Fac"], 0.35, 0.75, 0.93, 1.0)
    soot_attr = N("ShaderNodeAttribute")
    soot_attr.attribute_name = "soot"
    soot_f = map_range(soot_attr.outputs["Fac"], 0.0, 1.0, 1.0, 0.45)
    lift_attr = N("ShaderNodeAttribute")
    lift_attr.attribute_name = "lift"
    lift_f = map_range(lift_attr.outputs["Fac"], 0.0, 1.0, 1.0, FRONT_BACK_LIFT)
    grey = mult(mult(mult(mult(height, blotch), streaks), soot_f), lift_f)
    # greenish-grey damp band just above the brownstone base
    damp = map_range(sep.outputs["Z"], 1.15, 1.9, 1.0, 0.0)
    band = N("ShaderNodeMath")
    band.operation = "MULTIPLY"
    L(damp, band.inputs[0])
    L(map_range(sep.outputs["Z"], 1.0, 1.12, 0.0, 1.0), band.inputs[1])
    def sock(socks, name):        # the Mix node has float/vector/colour sockets with the same name
        return next(x for x in socks if x.name == name and x.type == "RGBA")

    tint = N("ShaderNodeMix")
    tint.data_type = "RGBA"
    L(band.outputs["Value"], tint.inputs["Factor"])
    sock(tint.inputs, "A").default_value = (1, 1, 1, 1)
    sock(tint.inputs, "B").default_value = (0.86, 0.91, 0.84, 1)
    col_mul = N("ShaderNodeMix")
    col_mul.data_type = "RGBA"
    col_mul.blend_type = "MULTIPLY"
    col_mul.inputs["Factor"].default_value = 1.0
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    L(gc.outputs["Vector"], sock(col_mul.inputs, "A"))
    L(sock(tint.outputs, "Result"), sock(col_mul.inputs, "B"))
    L(sock(col_mul.outputs, "Result"), emit.inputs["Color"])
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
scale = float(np.percentile(combined[baked].max(axis=1), 99.5))
# Fill every unbaked pixel (window holes inside wall islands, gaps between islands) with
# its baked neighbours, so texture filtering never pulls black into the edges.
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
out_img = bpy.data.images.get("CH_Lightmap") or bpy.data.images.new("CH_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
out_img.scale(LIGHTMAP_SIZE, LIGHTMAP_SIZE)
out_img.colorspace_settings.name = "Non-Color"
out_img.pixels.foreach_set(rgba.ravel())
out_img.filepath_raw = LIGHTMAP
out_img.file_format = "JPEG"
scene.render.image_settings.quality = 88
out_img.save()
LIGHTMAP_SCALE = round(scale, 4)
print("LIGHTMAP_SCALE =", LIGHTMAP_SCALE, "(use baked-lighting intensity:", LIGHTMAP_SCALE, ")")

# Remove the bake helper nodes and the soot attribute so they are not exported.
for mat in mesh.materials:
    for name in ("BakeTarget", "BakeUV"):
        node = mat.node_tree.nodes.get(name)
        if node:
            mat.node_tree.nodes.remove(node)
for attr_name in ("soot", "lift"):
    if mesh.attributes.get(attr_name):
        mesh.attributes.remove(mesh.attributes[attr_name])

# 6. Export ---------------------------------------------------------------------
for o in bpy.context.scene.objects:
    o.select_set(o == ch)
bpy.context.view_layer.objects.active = ch
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_texcoords=True,
                          export_normals=True)
tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("exported", GLB, "|", tris, "triangles |", len(mesh.materials), "materials")
ch["lightmap_scale"] = LIGHTMAP_SCALE            # read by courthouse_preview.py
