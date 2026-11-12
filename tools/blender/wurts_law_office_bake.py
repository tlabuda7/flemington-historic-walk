"""
wurts_law_office_bake.py - textures and baked lighting for the Wurts Law Office (59 Main St),
then export to assets/models/wurts-law-office.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/wurts_law_office_bake.py").read())

Steps (pattern: county_offices_bake.py):
 1. Rebuild the geometry (wurts_law_office.py).
 2. Give every surface a CC0 colour texture tiled in real-world metres (box UVs). Only five
    materials (= five draw calls): white paint, dark green paint, glass, brick, grey. The
    green door paint and the brick are pulled to the spec colours by a constant colour
    that the glTF exporter writes as baseColorFactor.
 3. Join the parts into one object, cut it along the wall planes and delete the faces
    nobody can see (inside walls, under the entablature slabs and roof), then unwrap
    "Lightmap".
 4. Bake warm late-afternoon sun + sky (direct and bounced light) into one 1K lightmap
    with Cycles. West side of Main St (front faces east): the sun comes from the
    south-west, so the south side is lit and the front is in shade.
 5. Bake a grime mask (dirt splash near the ground, light blotches, faint streaks, soot
    under the cornice and on the chimney top, worn porch boards before the door) and
    multiply it in.
 6. Export the GLB. Other collections are hidden from render during the bake.

Windows (PLAN.md section E, 2026-11-11): the window backs (material WLR_WBack, cells of
assets/textures/shared/window_backs.jpg, UVs from BACKREC) are lightmapped like everything
else; the panes are one material named exactly `glass` (#1A1916, alpha 0.40, roughness 0.05,
BLEND, single-sided) that the scene leaves unlit and gives a sky reflection (`glass-reflect`).
The glass is fully transparent during the bake, ignored by the hidden-face pass, and its
Lightmap UVs are squeezed small. The name board is WLR_Dark (the old dark glass colour).
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
WT = PROJECT + r"\assets\textures\wurts-law-office" + "\\"
GLB = PROJECT + r"\assets\models\wurts-law-office.glb"
LIGHTMAP = PROJECT + r"\assets\textures\wurts-law-office-lightmap.jpg"
LIGHTMAP_SIZE = 1024
SAMPLES = 384
TX = PROJECT + r"\assets\textures" + "\\"
GLASS_ALPHA = 0.40
TO_SUN = (-0.40, 0.90, 0.36)          # west-side building (front faces east)
COLL, RIG, PREFIX = "WurtsLawOffice", "WL_BakeRig", "WL_"

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\wurts_law_office.py").read())

# 2. Materials ----------------------------------------------------------------


def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    """Constant colour that turns a texture averaging `avg` (sRGB 0-255) into `target`."""
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


# part -> (texture file, metres per repeat, roughness, plain colour (linear) or None, tint or None)
LOOK = {
    "White": (CT + "paint_white.jpg", 2.0, 0.7, None, tint((242, 239, 230), (0xEE, 0xEB, 0xE2))),
    "Green": (PH + "door_paint_green.jpg", 0.8, 0.6, None, tint((93, 107, 92), (0x2F, 0x3B, 0x2C))),
    "Dark":  (None, 1.0, 0.15, tuple(srgb_to_lin(c) for c in (0x1E, 0x22, 0x26)), None),   # name board
    "Glass": (None, 1.0, 0.05, tuple(srgb_to_lin(c) for c in (0x1A, 0x19, 0x16)), None),   # section E
    "WBack": (TX + r"shared\window_backs.jpg", 1.0, 0.9, None, None),
    "Brick": (PH + "red_brick.jpg", 1.4, 0.9, None, tint((142, 103, 80), (0x87, 0x45, 0x2F))),
    "Grey":  (WT + "planks_grey.jpg", 2.0, 0.85, None, None),
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


FINAL = {k: textured_material("glass" if k == "Glass" else "WLR_" + k, LOOK[k][0], *LOOK[k][2:]) for k in LOOK}


def box_uvs(obj):
    """Project each face from its dominant axis so textures keep real-world scale; the
    tile size comes from the face's material. Sloping faces (lean-to roof, louvres) are
    projected along the slope."""
    mesh = obj.data
    while mesh.uv_layers:
        mesh.uv_layers.remove(mesh.uv_layers[0])
    uv = mesh.uv_layers.new(name="UVMap")
    tiles = [LOOK[m.name[3:]][1] for m in mesh.materials]
    boards = [m.name[3:] == "Grey" for m in mesh.materials]
    keys = [m.name[3:] for m in mesh.materials]
    rid_attr = mesh.attributes.get("rid")
    for poly in mesh.polygons:
        tile = tiles[poly.material_index]
        if keys[poly.material_index] == "WBack":        # window backs: their atlas cell
            rec = BACKREC[rid_attr.data[poly.index].value]
            U0, V0, U1, V1 = rec["uv"]
            for li in poly.loop_indices:
                co = mesh.vertices[mesh.loops[li].vertex_index].co
                u = co.x if rec["axis"] == "y" else co.y
                fu = (u - rec["u0"]) / (rec["u1"] - rec["u0"])
                fz = (co.z - rec["z0"]) / (rec["z1"] - rec["z0"])
                uv.data[li].uv = (U0 + (U1 - U0) * fu, V0 + (V1 - V0) * fz)
            continue
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
            if boards[poly.material_index] and ax != 2:
                u, v = v, u                  # grey planks run horizontally on risers and facings
            uv.data[li].uv = (u / tile, v / tile)


parts = [o for o in col.objects if o.type == "MESH"]
for obj in parts:
    box_uvs(obj)                                  # reads the WL_<key> slot names
    for i, m in enumerate(obj.data.materials):
        obj.data.materials[i] = FINAL[m.name[3:]]

# 3. Join, drop hidden faces, unwrap the lightmap UVs --------------------------
wl_obj = bpy.data.objects["WL_Walls"]
with bpy.context.temp_override(active_object=wl_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
wl_obj.name = wl_obj.data.name = "WurtsLawOffice"
mesh = wl_obj.data


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
    through (inside walls, under the entablature slabs and roof, behind glass). Downward
    faces at or below grade go too."""
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


CUT_PLANES = [((HW, 0, 0), (1, 0, 0)), ((-HW, 0, 0), (1, 0, 0)),
              ((HW + ENT, 0, 0), (1, 0, 0)), ((-HW - ENT, 0, 0), (1, 0, 0)),
              ((0, FRONT_Y, 0), (0, 1, 0)), ((0, BACK, 0), (0, 1, 0)),
              ((0, -0.02, 0), (0, 1, 0)), ((0, BACK + ENT, 0), (0, 1, 0)),
              ((LT_X0, 0, 0), (1, 0, 0)), ((LT_X1, 0, 0), (1, 0, 0)), ((0, LT_Y1, 0), (0, 1, 0))]
before = sum(len(p.vertices) - 2 for p in mesh.polygons)
removed = remove_hidden_faces(wl_obj)
after = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("hidden faces removed:", removed, "| triangles", before, "->", after)

lm = mesh.uv_layers.new(name="Lightmap")
mesh.uv_layers.active = lm
mesh.uv_layers["UVMap"].active_render = True
for o in bpy.context.view_layer.objects:
    o.select_set(o == wl_obj)
bpy.context.view_layer.objects.active = wl_obj
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004,
                         area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.object.mode_set(mode="OBJECT")
# Give the lightmap's pixels to what matters: shrink dark or out-of-the-way parts.
LM_SHRINK = {"WLR_Dark": 0.35, "glass": 0.03, "WLR_WBack": 0.6}
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    f = LM_SHRINK.get(mat_names[p.material_index])
    if f is None and p.center.z > 4.33 and mat_names[p.material_index] != "WLR_Brick":
        f = 0.35                                 # roof deck and lip tops (never seen from the street)
    if f is None and p.center.y > BACK - 0.3:
        f = 0.6                                  # the rear and the lean-to
    if f:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.003, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig: sun, sky, ground (in WL_BakeRig, not exported) -------------------
scene = bpy.context.scene
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
sun = bpy.data.objects.get("WL_Sun")
if not sun:
    sun = bpy.data.objects.new("WL_Sun", bpy.data.lights.new("WL_Sun", "SUN"))
    rig.objects.link(sun)
sun.data.energy = 3.2
sun.data.color = (1.0, 0.80, 0.58)
sun.data.angle = math.radians(1.5)
to_sun = Vector(TO_SUN).normalized()            # about 21 degrees above the horizon
sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()

ground = bpy.data.objects.get("WL_Ground")
if not ground:
    gm = bpy.data.meshes.new("WL_Ground")
    S = 120.0
    gm.from_pydata([(-S, -S, 0), (S, -S, 0), (S, S, 0), (-S, S, 0)], [], [(0, 1, 2, 3)])
    gmat = bpy.data.materials.get("WL_GroundWarm") or bpy.data.materials.new("WL_GroundWarm")
    gmat.use_nodes = True
    # warm lawn / paving bounce (keeps the shaded front from turning blue)
    next(n for n in gmat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.34, 0.28, 0.18, 1)
    gm.materials.append(gmat)
    ground = bpy.data.objects.new("WL_Ground", gm)
    rig.objects.link(ground)

if scene.world is None:
    scene.world = bpy.data.worlds.new("WL_Sky")
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
    light_img = bake_target("WL_Light", True)
    point_materials_at(light_img)
    # No bake margin: the fill after the bake covers every empty pixel from its neighbours.
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask --------------------------------------------------------------
    grime_mat = bpy.data.materials.get("WL_GrimeBake") or bpy.data.materials.new("WL_GrimeBake")
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

    # light dirt splash on the bottom ~0.3 m of walls and pillar bases, fading by 0.9 m
    height = map_range(sep.outputs["Z"], 0.05, 0.9, 0.80, 1.0)
    noise = N("ShaderNodeTexNoise")                                       # blotchy fading
    noise.inputs["Scale"].default_value = 0.8
    noise.inputs["Detail"].default_value = 6.0
    L(geo.outputs["Position"], noise.inputs["Vector"])
    blotch = map_range(noise.outputs["Fac"], 0.0, 1.0, 0.93, 1.02)       # light: a cared-for building
    stretch = N("ShaderNodeVectorMath")                                   # faint vertical streaks
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (4.0, 4.0, 0.2)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_noise = N("ShaderNodeTexNoise")
    streak_noise.inputs["Scale"].default_value = 1.6
    streak_noise.inputs["Detail"].default_value = 2.0
    L(stretch.outputs["Vector"], streak_noise.inputs["Vector"])
    streaks = map_range(streak_noise.outputs["Fac"], 0.35, 0.75, 0.95, 1.0)
    # faint grey under the cornice corona: darkening up to the soffit (4.14), clean above
    soot = math_op("ADD", map_range(sep.outputs["Z"], 3.4, 4.12, 1.0, 0.92),
                   map_range(sep.outputs["Z"], 4.12, 4.2, 0.0, 0.08))
    # soot on the chimney top
    chim = map_range(sep.outputs["Z"], 5.8, 6.5, 1.0, 0.62)
    # worn porch boards in front of the door: upward faces at porch level near x = 0
    centre = map_range(math_op("ABSOLUTE", sep.outputs["X"]), 0.3, 0.9, 1.0, 0.0)
    up = map_range(nsep.outputs["Z"], 0.8, 0.95, 0.0, 1.0)
    on_porch = mult(map_range(sep.outputs["Z"], 0.25, 0.28, 0.0, 1.0), map_range(sep.outputs["Z"], 0.32, 0.36, 1.0, 0.0))
    wear = map_range(mult(mult(centre, up), on_porch), 0.0, 1.0, 1.0, 0.82)
    grey = mult(mult(mult(height, blotch), mult(streaks, soot)), mult(chim, wear))
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    L(gc.outputs["Vector"], emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    grime_img = bake_target("WL_Grime", True)
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
# Warm the shade slightly: sky-only light is blue; pull each pixel's blue/green toward
# its red a little so the white paint in shade stays warm (courthouse lesson).
lum = combined.mean(axis=1, keepdims=True)
combined = combined * 0.65 + lum * np.array([[1.0, 0.96, 0.88]]) * 0.35
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
out_img = bpy.data.images.get("WL_Lightmap") or bpy.data.images.new("WL_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
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

# The "DR. TOMPKINS" letters are too small to bake reliably and sit flat on the name board:
# point all their lightmap UVs at the board's front face (union_hotel_bake.py pattern).
mat_names = [m.name for m in mesh.materials]
white_i, glass_i = mat_names.index("WLR_White"), mat_names.index("WLR_Dark")   # glass_i = the board
lm_data = mesh.uv_layers["Lightmap"].data
board = max((p for p in mesh.polygons if p.material_index == glass_i and p.normal.y < -0.5
             and abs(p.center.z - NAME_Z) < 0.03 and p.center.y < FRONT_Y - 0.035), key=lambda p: p.area)
board_uv = [sum(lm_data[li].uv[k] for li in board.loop_indices) / board.loop_total for k in (0, 1)]
n_letters = 0
for p in mesh.polygons:
    c = p.center
    if p.material_index == white_i and abs(c.x) < NAME_W / 2 and abs(c.z - NAME_Z) < NAME_H / 2 \
            and c.y < FRONT_Y - 0.0395:
        n_letters += 1
        for li in p.loop_indices:
            lm_data[li].uv = board_uv
print("letter faces re-pointed at the name board's lightmap:", n_letters)

# Remove the bake helper nodes so they are not exported.
for mat in mesh.materials:
    for name in ("BakeTarget", "BakeUV"):
        node = mat.node_tree.nodes.get(name)
        if node:
            mat.node_tree.nodes.remove(node)

# 6. Export ---------------------------------------------------------------------
for o in bpy.context.scene.objects:
    o.select_set(o == wl_obj)
bpy.context.view_layer.objects.active = wl_obj
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_texcoords=True,
                          export_normals=True)
tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("exported", GLB, "|", tris, "triangles |", len(mesh.materials), "materials")
wl_obj["lightmap_scale"] = LIGHTMAP_SCALE            # read by wurts_law_office_preview.py
