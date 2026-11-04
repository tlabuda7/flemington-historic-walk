"""
lovells_restaurant_bake.py - textures and baked lighting for Lovell's Restaurant (68 Main St),
then export to assets/models/lovells-restaurant.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/lovells_restaurant_bake.py").read())

Steps (pattern: house_65_main_bake.py):
 1. Rebuild the geometry (lovells_restaurant.py).
 2. Four materials only (= four draw calls):
      paint  house-65-main/clapboard_cream.jpg, tile 1.6 m; boards on the side and rear walls,
             the front and all trim squeezed onto one board so they read as smooth paint;
             the chimney too (brick red by a bake tint)
      dark   plain #2B302C (glass, doors, shutters, lantern, iron work)
      signs  lovells-restaurant/signs_atlas.jpg (tools/prepare_lovells_textures.py): awning
             canvas, valance lettering, RESTAURANT / LOVELL'S / ICE CREAM boards
      stone  lovells-restaurant/stone_bluestone.jpg (concrete_floor_worn_001 lightened), tile 2.0 m (steps, stone course, roof and
             coping; the roof is turned tin grey by a bake tint)
 3. Cut the wall shell where other parts cover it, join everything into one object, delete
    the faces nobody can see, then unwrap "Lightmap" (front and south wall weighted up).
 4. Bake warm late-afternoon sun + sky (direct and bounced light) into one 2K lightmap with
    Cycles. East side of Main St (front faces west): the front is sunlit and the south wall
    grazed. Bake-only occluder boxes (Union Hotel with its veranda and mansard, the Bank
    Building) throw the hotel's shadow on the rear part of the south wall; they are hidden
    from the export. Other collections are hidden from render during the bake.
 5. Bake an RGB grime mask and multiply it in (dirt splash on the stone course and pilaster
    bases, worn treads in front of both doors, grey streaks under the cornice blocks and
    sills, a soiled valance edge, the south wall chalkier and darker near the ground in the
    narrow gap, chimney soot, and the roof / chimney tints as a colour attribute).
 6. Fill empty lightmap pixels from their neighbours, warm the shade, save the sRGB JPEG,
    print LIGHTMAP_SCALE, export the GLB (TEXCOORD_0 + TEXCOORD_1).
"""

import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
TX = PROJECT + r"\assets\textures" + "\\"
GLB = PROJECT + r"\assets\models\lovells-restaurant.glb"
LIGHTMAP = PROJECT + r"\assets\textures\lovells-restaurant-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 384
TO_SUN = (0.40, -0.90, 0.36)          # east-side building (front faces west)
COLL, RIG = "LovellsRestaurant", "LV_BakeRig"
CLAP_TILE = 1.6                       # 9 boards per tile -> 0.18 m exposure
TRIM_V = 0.937                        # flattest board row (tools/prepare_house_65_textures.py)

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\lovells_restaurant.py").read())

# 2. Materials ----------------------------------------------------------------


def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    """Constant colour that turns a texture averaging `avg` (sRGB 0-255) into `target`."""
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


# spec #E4DDCB, a shade down and a touch cooler so the sunlit front (warm sun) does not burn
# out to white or turn yellow
PAINT_TARGET = (0xD8, 0xD3, 0xC6)
# material -> (texture file, metres per repeat, roughness, plain colour (linear) or None, factor or None)
LOOK = {
    "Paint": (TX + r"house-65-main\clapboard_cream.jpg", CLAP_TILE, 0.8, None, tint((229, 223, 204), PAINT_TARGET)),
    "Dark":  (None, 1.0, 0.3, tuple(srgb_to_lin(c) for c in (0x2B, 0x30, 0x2C)), None),
    "Signs": (TX + r"lovells-restaurant\signs_atlas.jpg", 1.0, 0.85, None, None),
    "Stone": (TX + r"lovells-restaurant\stone_bluestone.jpg", 2.0, 0.9, None, None),   # review round 1: lighter
}
FINAL_NAMES = {"Paint": "paint", "Dark": "dark", "Signs": "signs", "Stone": "stone"}


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

# Bake tints (multiplied into the lightmap through the grime mask): tin-grey roof and coping;
# the chimney (paint) turned dull brick red (#87452F) from the cream paint.
BRICK = (0x87, 0x45, 0x2F)
# DoorFrame: cream paint -> dark green door paint (~#4F5749), lighter than the dark glass
TINTS = {"Roof": (0.21, 0.215, 0.23),                 # on the lightened stone: same tin grey as before
         "DoorFrame": (0.115, 0.145, 0.125),
         "Chimney": tuple(srgb_to_lin(b) / srgb_to_lin(p) for b, p in zip(BRICK, PAINT_TARGET))}

# Atlas boxes (pixels from the top-left; must match tools/prepare_lovells_textures.py)
REGIONS = {"canvas": (0, 0, 1024, 384), "valance": (0, 384, 1024, 512), "board": (0, 512, 1024, 672),
           "lovells": (0, 672, 512, 800), "icecream": (512, 672, 1024, 800), "spare": (0, 800, 1024, 1024)}
SIGN_REGION = {"BoardR": "board", "BoardL": "lovells", "BoardIce": "icecream", "Valance": "valance"}


def atlas_uv(region, fu, fv, inset=2):
    """UV of the point (fu across, fv down from the top, both 0..1) inside an atlas box."""
    c0, r0, c1, r1 = REGIONS[region]
    col_ = c0 + inset + (c1 - c0 - 2 * inset) * min(max(fu, 0.0), 1.0)
    row = r0 + inset + (r1 - r0 - 2 * inset) * min(max(fv, 0.0), 1.0)
    return (col_ / 1024, 1 - row / 1024)


def on_plane(c, n, planes):
    """True if a vertical face (centre c, normal n) lies on one of the given wall planes."""
    for (px, py), (nx, ny) in planes:
        if nx * n.x + ny * n.y > 0.98 and abs((c.x - px) * nx + (c.y - py) * ny) < 0.012:
            return True
    return False


def set_uvs(obj, kind):
    """Box UVs in real-world metres. kind: Clap (wall shell: boards on the side / rear wall
    faces, flat paint elsewhere), Trim / Chimney (flat paint), Dark / Stone / Roof (box),
    Awning (canvas box, along the slope), Canvas (spare canvas), sign boards and the valance
    (lettered front face fitted to its atlas box, other faces on the box's edge colour)."""
    mesh = obj.data
    while mesh.uv_layers:
        mesh.uv_layers.remove(mesh.uv_layers[0])
    uv = mesh.uv_layers.new(name="UVMap")
    mat_key = BUILDER_MAT.get(kind, "Paint")
    tile = LOOK[mat_key][1]
    for poly in mesh.polygons:
        n = poly.normal
        h = math.hypot(n.x, n.y)
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            if kind == "Awning":                        # top and underside: across = x, down the slope
                t = (-co.y - AW_D) / (-AWY - AW_D)
                uv.data[li].uv = atlas_uv("canvas", (co.x - AW0) / (AW1 - AW0), t)
                continue
            if kind in SIGN_REGION:
                region = SIGN_REGION[kind]
                x0, x1, z0, z1 = SIGN_RECTS[kind]
                if n.y < -0.9:
                    uv.data[li].uv = atlas_uv(region, (co.x - x0) / (x1 - x0), (z1 - co.z) / (z1 - z0))
                elif kind == "Valance":                 # back and edges: plain canvas
                    uv.data[li].uv = atlas_uv("spare", (co.x - x0) / (x1 - x0), (z1 - co.z) / 0.6, 4)
                else:                                   # board edges: the board's border colour
                    uv.data[li].uv = atlas_uv(region, 0.004, 0.5, 2)
                continue
            if 0.25 < abs(n.z) < 0.97:                   # slopes: along the slope
                tx, ty = -n.y / h, n.x / h
                u, v = co.x * tx + co.y * ty, co.z / h
            elif abs(n.z) >= 0.97:
                u, v = co.x, co.y
            else:                                        # vertical: along the face
                tx, ty = -n.y / h, n.x / h
                u, v = co.x * tx + co.y * ty, co.z
            if kind == "Canvas":                         # cheeks: spare canvas, 4 m per atlas width
                uv.data[li].uv = atlas_uv("spare", (u % 4.0) / 4.0, 1 - (v - 2.5) / 1.2, 4)
                continue
            flat = kind in ("Trim", "Chimney", "DoorFrame") or (kind == "Clap" and not (h > 0.98 and on_plane(poly.center, n, SIDE_PLANES)))
            if flat:
                uv.data[li].uv = (u / tile * 0.02, TRIM_V + (v - 5.0) / tile * 0.003)
            else:
                uv.data[li].uv = (u / tile, v / tile)


def add_tint(obj, rgb):
    attr = obj.data.color_attributes.new("Tint", "FLOAT_COLOR", "CORNER")
    data = np.tile(np.array([*rgb, 1.0], dtype=np.float32), len(obj.data.loops))
    attr.data.foreach_set("color", data)


# split the shell where the stone course, pilasters, sign board and side cornices cover it
SHELL_CUTS = [((0, 0, FL), (0, 0, 1)), ((0, 0, 3.55), (0, 0, 1)), ((0, 0, 3.98), (0, 0, 1)),
              ((0, 0, FRIEZE), (0, 0, 1)), ((0, 0, EAVE), (0, 0, 1)),
              ((2.65, 0, 0), (1, 0, 0)), ((-2.65, 0, 0), (1, 0, 0)),
              ((2.725, 0, 0), (1, 0, 0)), ((-2.725, 0, 0), (1, 0, 0))]

parts = [o for o in col.objects if o.type == "MESH"]
for obj in parts:
    kind = "Clap" if obj.name == "LV_Shell" else obj.name[3:]
    if obj.name == "LV_Shell":
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        for co, no in SHELL_CUTS:
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-4,
                                   plane_co=co, plane_no=no)
        bm.to_mesh(obj.data)
        bm.free()
    set_uvs(obj, kind)
    add_tint(obj, TINTS.get(kind, (1.0, 1.0, 1.0)))
    obj.data.materials[0] = FINAL[BUILDER_MAT.get(kind, "Paint")]

# 3. Join, drop hidden faces, unwrap the lightmap UVs --------------------------
h_obj = bpy.data.objects["LV_Shell"]
with bpy.context.temp_override(active_object=h_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
h_obj.name = h_obj.data.name = "LovellsRestaurant"
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
# Give the lightmap's pixels to what matters: the front and the south wall. Shrink dark,
# downward, north, rear and roof faces.
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    f = 1.0
    if mat_names[p.material_index] == "dark":
        f *= 0.6
    if p.normal.z < -0.5:
        f *= 0.6                                  # soffits, awning underside
    if p.normal.x < -0.7:
        f *= 0.55                                 # north wall (mostly against the bank)
    if p.normal.y > 0.7 and p.center.y > DEPTH - 0.2:
        f *= 0.45                                 # rear wall (against the harness shop)
    if p.normal.z > 0.5 and p.center.z > 6.2:
        f *= 0.5                                  # roof, cornice tops
    if f < 1.0:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.002, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig: sun, sky, ground, occluders (in LV_BakeRig, not exported) ---------------
scene = bpy.context.scene
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
rig.hide_viewport = False
sun =bpy.data.objects.get("LV_Sun")
if not sun:
    sun = bpy.data.objects.new("LV_Sun", bpy.data.lights.new("LV_Sun", "SUN"))
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


ground = bpy.data.objects.get("LV_Ground")
if not ground:
    gm = bpy.data.meshes.new("LV_Ground")
    S = 120.0
    gm.from_pydata([(-S, -S, 0), (S, -S, 0), (S, S, 0), (-S, S, 0)], [], [(0, 1, 2, 3)])
    gm.materials.append(rig_mat("LV_GroundWarm", (0.36, 0.29, 0.18)))   # warm paving bounce
    ground = bpy.data.objects.new("LV_Ground", gm)
    rig.objects.link(ground)

# Occluder proxies (PLAN.md Placement): Union Hotel block, its mansard and veranda; the bank
hotel_mat = rig_mat("LV_OccHotel", (0.40, 0.33, 0.26))
bank_mat = rig_mat("LV_OccBank", (0.30, 0.13, 0.08))
rig_box("LV_OccHotel", 6.53, 36.0, 1.94, 10.54, 0.0, 12.25, hotel_mat)
rig_box("LV_OccHotelMansard", 7.13, 35.4, 2.54, 9.94, 12.25, 15.6, hotel_mat)
rig_box("LV_OccHotelVeranda", 6.53, 36.0, -1.06, 1.94, 0.0, 7.6, hotel_mat)
rig_box("LV_OccBank", -25.18, -3.04, -0.42, 10.63, 0.0, 12.35, bank_mat)

if scene.world is None:
    scene.world = bpy.data.worlds.new("LV_Sky")
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
    o.select_set(o == h_obj)
bpy.context.view_layer.objects.active = h_obj
try:
    light_img = bake_target("LV_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask (RGB) ----------------------------------------------------------
    grime_mat = bpy.data.materials.get("LV_GrimeBake") or bpy.data.materials.new("LV_GrimeBake")
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
        """a where fac = 0, b where fac = 1 (a, b constant colours)."""
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

    # dirt splash on the bottom ~0.4 m (stone course, steps, pilaster bases), fading by 0.7 m
    height = map_range(Z, 0.0, 0.7, 0.80, 1.0)
    blotch = map_range(noise_tex(geo.outputs["Position"], 0.7, 6.0), 0.0, 1.0, 0.91, 1.03)
    stretch = N("ShaderNodeVectorMath")                                   # faint vertical streaks
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (4.0, 4.0, 0.2)
    L(geo.outputs["Position"], stretch.inputs[0])
    streak_n = noise_tex(stretch.outputs["Vector"], 1.6, 2.0)
    streaks = map_range(streak_n, 0.35, 0.75, 0.94, 1.0)
    # grey streaks below the cornice blocks / brackets (front, x beyond the arch) and the sills
    front = map_range(NY, -0.6, -0.8, 0.0, 1.0)
    under_blocks = mult(front, map_range(math_op("ABSOLUTE", X), 1.35, 1.55, 0.0, 1.0),
                        map_range(Z, 4.6, 5.85, 0.0, 1.0), map_range(Z, 5.85, 5.9, 1.0, 0.0),
                        map_range(streak_n, 0.3, 0.7, 1.0, 0.3))
    sill_x = map_range(math_op("ABSOLUTE", math_op("SUBTRACT", math_op("ABSOLUTE", X), WIN_X)), 0.30, 0.45, 1.0, 0.0)
    under_sills = mult(front, sill_x, map_range(Z, 3.75, 4.12, 0.0, 1.0), map_range(Z, 4.12, 4.15, 1.0, 0.0),
                       map_range(streak_n, 0.3, 0.7, 1.0, 0.4))
    drips = math_op("SUBTRACT", 1.0, math_op("ADD", mult(under_blocks, 0.12), mult(under_sills, 0.10)))
    # under the eaves / cornice: faint grey on the walls just below
    eave = map_range(Z, 5.6, 6.05, 1.0, 0.93)
    eave = math_op("ADD", eave, map_range(Z, 6.05, 6.1, 0.0, 0.07))
    # chimney soot (top 7.90)
    soot = map_range(Z, 7.45, 7.90, 1.0, 0.60)
    # worn treads in front of both doors (x -2.65 ... -1.70 and -1.05 ... +0.65)
    door_l = map_range(math_op("ABSOLUTE", math_op("SUBTRACT", X, -2.175)), 0.30, 0.55, 1.0, 0.0)
    door_c = map_range(math_op("ABSOLUTE", math_op("SUBTRACT", X, -0.20)), 0.55, 0.90, 1.0, 0.0)
    up = map_range(NZ, 0.8, 0.95, 0.0, 1.0)
    on_steps = mult(map_range(Y, 0.30, 0.25, 0.0, 1.0), map_range(Z, 0.47, 0.50, 1.0, 0.0))
    wear = map_range(mult(math_op("MAXIMUM", door_l, door_c), up, on_steps), 0.0, 1.0, 1.0, 0.82)
    # soiled valance edge (front of the valance, bottom 0.12 m)
    valance = mult(map_range(Y, AWY + 0.05, AWY + 0.02, 0.0, 1.0), map_range(Z, VAL_BOT + 0.17, VAL_BOT, 0.0, 1.0),
                   map_range(Z, VAL_BOT - 0.05, VAL_BOT - 0.01, 0.0, 1.0))
    val_dirt = map_range(valance, 0.0, 1.0, 1.0, 0.86)
    # south wall: chalkier blotches, darker toward the ground in the narrow gap
    south = map_range(NX, 0.6, 0.8, 0.0, 1.0)
    s_low = map_range(mult(south, map_range(Z, 0.4, 2.6, 1.0, 0.0)), 0.0, 1.0, 1.0, 0.88)
    s_blot = map_range(mult(south, map_range(noise_tex(geo.outputs["Position"], 1.3, 4.0), 0.4, 0.7, 0.0, 1.0)),
                       0.0, 1.0, 1.0, 0.93)
    grey = mult(height, blotch, streaks, drips, eave, soot, wear, val_dirt, s_low, s_blot)
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    # north wall (exposed rear part) a touch cooler near the ground; south side warm and chalky
    north = mult(map_range(NX, -0.6, -0.8, 0.0, 1.0), map_range(Z, 0.4, 2.2, 1.0, 0.0))
    col_n = vmix(north, (1.0, 1.0, 1.0), (0.94, 0.98, 0.95))
    col_s = vmix(south, (1.0, 1.0, 1.0), (1.0, 0.985, 0.955))
    attr = N("ShaderNodeAttribute")                                       # roof / chimney tints
    attr.attribute_name = "Tint"
    rgb = vmul(vmul(vmul(gc.outputs["Vector"], col_n), col_s), attr.outputs["Color"])
    L(rgb, emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    grime_img = bake_target("LV_Grime", True)
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
# brightness, much more in the shade than in the sun, so the south wall in the hotel's shadow
# stays warm cream while the sunlit front does not turn yellow.
lum = combined.mean(axis=1, keepdims=True)
ref = np.percentile(lum[baked], 99.0)
shade = np.clip(1.0 - lum / (0.9 * ref), 0.0, 1.0)            # 1 in deep shade, 0 in sun
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
out_img = bpy.data.images.get("LV_Lightmap") or bpy.data.images.new("LV_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
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
h_obj["lightmap_scale"] = LIGHTMAP_SCALE            # read by lovells_restaurant_preview.py
