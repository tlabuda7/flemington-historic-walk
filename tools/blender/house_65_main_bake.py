"""
house_65_main_bake.py - textures and baked lighting for the frame dwelling at 65 Main St,
then export to assets/models/house-65-main.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/house_65_main_bake.py").read())

Steps (pattern: wurts_law_office_bake.py):
 1. Rebuild the geometry (house_65_main.py).
 2. Four materials only (= four draw calls): paint (cream clapboard texture; the trim's
    UVs are squeezed onto the middle of one board so trim reads as flat paint; porch deck
    boards run east-west), dark (plain colour: glass, shutters, doors), roof (slate,
    tinted by a colour factor) and brick (tinted by a colour factor). Box UVs in
    real-world metres.
 3. Cut the wall shells where other parts cover them, join everything into one object,
    delete the faces nobody can see, then unwrap "Lightmap".
 4. Bake warm late-afternoon sun + sky (direct and bounced light) into one 2K lightmap
    with Cycles. West side of Main St (front faces east): the sun comes from the
    WSW, so the south side and the bay are lit and the front is in shade.
 5. Bake an RGB grime mask and multiply it in: dirt splash near the ground, light
    blotches and streaks, grey under the eaves, chimney soot and a stain on the slate
    below, worn porch boards, a cooler north wall near the ground, a warmer sunlit south
    side, and the grey tint of the porch deck / steps / stoops and the porch skirt
    (a colour attribute, so no extra material is needed).
 6. Export the GLB (TEXCOORD_0 + TEXCOORD_1). Other collections are hidden from render
    during the bake.
"""

import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PH = PROJECT + r"\assets\textures\polyhaven" + "\\"
HT = PROJECT + r"\assets\textures\house-65-main" + "\\"
GLB = PROJECT + r"\assets\models\house-65-main.glb"
LIGHTMAP = PROJECT + r"\assets\textures\house-65-main-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 384
TO_SUN = (-0.40, 0.90, 0.36)          # west-side building (front faces east)
COLL, RIG = "House65Main", "H65_BakeRig"
CLAP_TILE = 1.6                       # 9 boards per tile -> 0.18 m exposure
TRIM_V = 0.937                        # flattest board row (tools/prepare_house_65_textures.py)

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\house_65_main.py").read())

# 2. Materials ----------------------------------------------------------------


def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    """Constant colour that turns a texture averaging `avg` (sRGB 0-255) into `target`."""
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


# material -> (texture file, metres per repeat, roughness, plain colour (linear) or None, factor or None)
PAINT_TARGET = (0xDC, 0xD5, 0xC1)     # spec #E6DFCC, a shade down so the sunlit south wall is not white
LOOK = {
    "Paint": (HT + "clapboard_cream.jpg", CLAP_TILE, 0.8, None, tint((229, 223, 204), PAINT_TARGET)),
    "Dark":  (None, 1.0, 0.3, tuple(srgb_to_lin(c) for c in (0x27, 0x32, 0x2A)), None),
    "Roof":  (PH + "roof_slates_03.jpg", 3.0, 0.8, None, tint((113, 110, 104), (0x4C, 0x51, 0x55))),
    "Brick": (PH + "red_brick.jpg", 1.4, 0.9, None, tint((142, 103, 80), (0x87, 0x45, 0x2F))),
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


FINAL = {k: textured_material("H65R_" + k, LOOK[k][0], *LOOK[k][2:]) for k in LOOK}

# Spec tints (0.60, 0.60, 0.58) / (0.80, 0.80, 0.78) left the deck beige on the cream paint;
# these also cancel the cream's yellow so the deck and steps read as worn grey paint.
TINTS = {"Deck": (0.52, 0.56, 0.70), "Skirt": (0.74, 0.78, 0.90)}


def on_wall_plane(c, n):
    """True if a vertical face (centre c, normal n) lies on one of the outer wall planes."""
    for (px, py), (nx, ny) in WALL_PLANES:
        if nx * n.x + ny * n.y > 0.98 and abs((c.x - px) * nx + (c.y - py) * ny) < 0.012:
            return True
    return False


def set_uvs(obj, kind):
    """Box UVs in real-world metres. kind: Clap (wall shells: boards on the wall faces,
    flat paint elsewhere), Trim / Skirt (flat paint), Deck (boards east-west on the tops,
    flat paint elsewhere), Dark / Roof / Brick (plain box projection, slopes along the
    slope)."""
    mesh = obj.data
    while mesh.uv_layers:
        mesh.uv_layers.remove(mesh.uv_layers[0])
    uv = mesh.uv_layers.new(name="UVMap")
    mat_key = BUILDER_MAT.get(kind, "Paint")
    tile = LOOK[mat_key][1]
    for poly in mesh.polygons:
        n = poly.normal
        h = math.hypot(n.x, n.y)
        flat = "trim"
        if kind == "Clap":
            flat = "boards" if (h > 0.98 and on_wall_plane(poly.center, n)) else "trim"
        elif kind == "Deck":
            flat = "deck" if n.z > 0.9 else "trim"
        elif kind not in ("Trim", "Skirt"):
            flat = "box"
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
            if flat == "deck":
                u, v = co.y, co.x                        # deck boards run east-west (along Y)
            if flat == "trim":
                uv.data[li].uv = (u / tile * 0.02, TRIM_V + (v - 5.0) / tile * 0.003)
            else:
                uv.data[li].uv = (u / tile, v / tile)


def add_tint(obj, rgb):
    attr = obj.data.color_attributes.new("Tint", "FLOAT_COLOR", "CORNER")
    data = np.tile(np.array([*rgb, 1.0], dtype=np.float32), len(obj.data.loops))
    attr.data.foreach_set("color", data)


SHELL_CUTS = {
    "H65_ShellMain": [((0, 0, 0.80), (0, 0, 1)), ((0, 0, FRIEZE), (0, 0, 1)), ((0, 0, SOFFIT), (0, 0, 1)),
                      ((0, 2.50, 0), (0, 1, 0)), ((0, 5.50, 0), (0, 1, 0)), ((ELL_X0, 0, 0), (1, 0, 0))],
    "H65_ShellEll": [((0, 0, 0.80), (0, 0, 1)), ((0, 0, FRIEZE), (0, 0, 1)), ((0, 0, SOFFIT), (0, 0, 1)),
                     ((0, MAIN_BACK, 0), (0, 1, 0))],
    "H65_ShellBay": [((0, 0, 0.80), (0, 0, 1)), ((-HW, 0, 0), (1, 0, 0))],
}

parts = [o for o in col.objects if o.type == "MESH"]
for obj in parts:
    kind = "Clap" if obj.name.startswith("H65_Shell") else obj.name[4:]
    if obj.name in SHELL_CUTS:              # split the shells where the ell, bay, brick and eaves cover them
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        for co, no in SHELL_CUTS[obj.name]:
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-4,
                                   plane_co=co, plane_no=no)
        bm.to_mesh(obj.data)
        bm.free()
    set_uvs(obj, kind)
    add_tint(obj, TINTS.get(kind, (1.0, 1.0, 1.0)))
    obj.data.materials[0] = FINAL[BUILDER_MAT.get(kind, "Paint")]

# 3. Join, drop hidden faces, unwrap the lightmap UVs --------------------------
h_obj = bpy.data.objects["H65_ShellMain"]
with bpy.context.temp_override(active_object=h_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
h_obj.name = h_obj.data.name = "House65Main"
mesh = h_obj.data
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
    """Points spread over the face (about one per 0.01 m2, 6 to 3000)."""
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
removed = remove_hidden_faces(h_obj)
after = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("hidden faces removed:", removed, "| triangles", before, "->", after)

lm = mesh.uv_layers.new(name="Lightmap")
mesh.uv_layers.active = lm
mesh.uv_layers["UVMap"].active_render = True
for o in bpy.context.view_layer.objects:
    o.select_set(o == h_obj)
bpy.context.view_layer.objects.active = h_obj
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003,
                         area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.object.mode_set(mode="OBJECT")
# Give the lightmap's pixels to what matters: shrink dark, downward and rear parts.
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    f = 1.0
    if mat_names[p.material_index] == "H65R_Dark":
        f *= 0.55
    if p.normal.z < -0.5:
        f *= 0.6                                  # soffits, porch ceiling
    if p.center.y > MAIN_BACK + 0.3 and p.normal.y > 0.5:
        f *= 0.75                                 # rear faces of the ell and rear porch
    if f < 1.0:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.002, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig: sun, sky, ground (in H65_BakeRig, not exported) ------------------
scene = bpy.context.scene
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
sun = bpy.data.objects.get("H65_Sun")
if not sun:
    sun = bpy.data.objects.new("H65_Sun", bpy.data.lights.new("H65_Sun", "SUN"))
    rig.objects.link(sun)
sun.data.energy = 3.2
sun.data.color = (1.0, 0.80, 0.58)
sun.data.angle = math.radians(1.5)
to_sun = Vector(TO_SUN).normalized()            # about 21 degrees above the horizon
sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()

ground = bpy.data.objects.get("H65_Ground")
if not ground:
    gm = bpy.data.meshes.new("H65_Ground")
    S = 120.0
    gm.from_pydata([(-S, -S, 0), (S, -S, 0), (S, S, 0), (-S, S, 0)], [], [(0, 1, 2, 3)])
    gmat = bpy.data.materials.get("H65_GroundWarm") or bpy.data.materials.new("H65_GroundWarm")
    gmat.use_nodes = True
    # warm lawn / paving bounce (keeps the shaded front from turning blue)
    next(n for n in gmat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.36, 0.29, 0.18, 1)
    gm.materials.append(gmat)
    ground = bpy.data.objects.new("H65_Ground", gm)
    rig.objects.link(ground)

if scene.world is None:
    scene.world = bpy.data.worlds.new("H65_Sky")
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


try:
    light_img = bake_target("H65_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask (RGB) ----------------------------------------------------------
    grime_mat = bpy.data.materials.get("H65_GrimeBake") or bpy.data.materials.new("H65_GrimeBake")
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
    NX, NZ = nsep.outputs["X"], nsep.outputs["Z"]

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
        """a where fac = 0, b where fac = 1 (a, b constant colours)."""
        m = N("ShaderNodeMix")
        m.data_type = "RGBA"
        L(fac, m.inputs["Factor"])
        sock = lambda socks, n: next(x for x in socks if x.name == n and x.type == "RGBA")
        sock(m.inputs, "A").default_value = (*a, 1)
        sock(m.inputs, "B").default_value = (*b, 1)
        return sock(m.outputs, "Result")

    # dirt splash on the bottom ~0.4 m (foundation, porch skirt, steps), fading by 0.6 m
    height = map_range(Z, 0.0, 0.6, 0.80, 1.0)
    noise = N("ShaderNodeTexNoise")                                       # blotchy fading
    noise.inputs["Scale"].default_value = 0.7
    noise.inputs["Detail"].default_value = 6.0
    L(geo.outputs["Position"], noise.inputs["Vector"])
    blotch = map_range(noise.outputs["Fac"], 0.0, 1.0, 0.91, 1.03)
    stretch = N("ShaderNodeVectorMath")                                   # faint vertical streaks
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (4.0, 4.0, 0.2)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_noise = N("ShaderNodeTexNoise")
    streak_noise.inputs["Scale"].default_value = 1.6
    streak_noise.inputs["Detail"].default_value = 2.0
    L(stretch.outputs["Vector"], streak_noise.inputs["Vector"])
    streaks = map_range(streak_noise.outputs["Fac"], 0.35, 0.75, 0.94, 1.0)
    # faint grey below the eave soffit (walls 5.9 ... 6.8), clean above
    eave = math_op("ADD", map_range(Z, 5.9, 6.78, 1.0, 0.92), map_range(Z, 6.78, 6.9, 0.0, 0.08))
    # soot on both chimney tops (A reaches 11.43 on the main ridge, B 9.75 at the rear)
    soot_a = map_range(Z, 10.95, 11.43, 1.0, 0.60)
    soot_b = math_op("SUBTRACT", 1.0, mult(map_range(Z, 9.30, 9.75, 0.0, 0.40), map_range(Y, 16.5, 17.0, 0.0, 1.0)))
    # faint dark stain on the slate below each chimney
    up = map_range(NZ, 0.5, 0.7, 0.0, 1.0)
    stain_a = mult(map_range(math_op("ABSOLUTE", math_op("SUBTRACT", Y, 9.0)), 0.35, 0.75, 0.12, 0.0),
                   map_range(Z, 9.0, 10.4, 0.0, 1.0), up)
    stain_b = mult(map_range(math_op("ABSOLUTE", math_op("SUBTRACT", Y, 17.8)), 0.30, 0.65, 0.12, 0.0),
                   map_range(Z, 7.6, 8.8, 0.0, 1.0), up)
    stain = math_op("SUBTRACT", 1.0, math_op("ADD", stain_a, stain_b))
    # worn porch boards and top step down the middle, toward the door
    centre = map_range(math_op("ABSOLUTE", X), 0.25, 0.65, 1.0, 0.0)
    flat_up = map_range(NZ, 0.8, 0.95, 0.0, 1.0)
    on_porch = mult(map_range(Z, 0.45, 0.50, 0.0, 1.0), map_range(Z, 0.69, 0.72, 1.0, 0.0),
                    map_range(Y, 2.1, 1.9, 0.0, 1.0), map_range(Y, -0.35, -0.25, 0.0, 1.0))
    wear = map_range(mult(centre, flat_up, on_porch), 0.0, 1.0, 1.0, 0.84)
    grey = mult(height, blotch, streaks, eave, soot_a, soot_b, stain, wear)
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    # north wall a touch cooler / greener near the ground; sunlit south side warmer, chalky
    north = mult(map_range(NX, 0.6, 0.8, 0.0, 1.0), map_range(Z, 0.4, 2.2, 1.0, 0.0))
    south = map_range(NX, -0.6, -0.8, 0.0, 1.0)
    col_n = vmix(north, (1.0, 1.0, 1.0), (0.94, 0.98, 0.95))
    col_s = vmix(south, (1.0, 1.0, 1.0), (1.0, 0.985, 0.95))
    attr = N("ShaderNodeAttribute")                                       # porch deck / skirt tints
    attr.attribute_name = "Tint"
    rgb = vmul(vmul(vmul(gc.outputs["Vector"], col_n), col_s), attr.outputs["Color"])
    L(rgb, emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    grime_img = bake_target("H65_Grime", True)
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
# brightness, more in the shade than in the sun, so the shaded east front stays warm cream.
lum = combined.mean(axis=1, keepdims=True)
ref = np.percentile(lum[baked], 99.0)
shade = np.clip(1.0 - lum / (0.9 * ref), 0.0, 1.0)            # 1 in deep shade, 0 in sun
w = 0.30 + 0.60 * shade
combined = combined * (1 - w) + lum * np.array([[1.0, 0.92, 0.74]]) * w
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
out_img = bpy.data.images.get("H65_Lightmap") or bpy.data.images.new("H65_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
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
    o.select_set(o == h_obj)
bpy.context.view_layer.objects.active = h_obj
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_texcoords=True,
                          export_normals=True)
tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("exported", GLB, "|", tris, "triangles |", len(mesh.materials), "materials")
h_obj["lightmap_scale"] = LIGHTMAP_SCALE            # read by house_65_main_preview.py
