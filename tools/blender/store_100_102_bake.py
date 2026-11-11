"""
store_100_102_bake.py - textures and baked lighting for the auto supplies store (100-102 Main
St), then export to assets/models/store-100-102.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/store_100_102_bake.py").read())

Steps (pattern: democrat_building_bake.py, block_32_38_bake.py):
 1. Rebuild the geometry (store_100_102.py).
 2. Seven materials, all textures reused (one draw call after the scene's merge, + the glass):
      Clapboard  house-65-main/clapboard_cream.jpg, tile 1.0 m (0.11 m boards), x factor ->
                 light grey-buff #B4AC98
      Trim       polyhaven/trim_paint_cream.jpg, tile 1.0 m, x factor -> cream #D8D0BC (posts,
                 rails, balusters, corner boards, casings, sash, cornice)
      Shopfront  polyhaven/door_paint_green.jpg, tile 0.8 m, x factor -> #3A3A2E (as the
                 Democrat building: county-offices/door_varnish_dark.jpg has too little green
                 for a multiply factor to reach #3A3A2E)
      Deck       block-35-41/trim_stone_grey.jpg, tile 2.0 m, x factor -> grey paint #8E8B82
      Roof       county-offices/roof_tin_redbrown.jpg, tile 2.0 m, dulled
      glass      plain #1A1916, alpha 0.40, roughness 0.05, alpha blend, single-sided, NOT
                 lightmapped by the scene (glass-reflect)
      WindowBack shared/window_backs.jpg (atlas UVs from store_100_102.py; the shop cells of
                 the same atlas serve the show windows, so no separate ShopInterior material)
 3. Join, cut along the planes where parts cover the walls, delete the faces nobody can see,
    unwrap "Lightmap" (weighted to the street front and galleries; roofs, the rear, the light
    court and the party wall down).
 4. Bake warm late-afternoon sun + sky into one 2K lightmap with Cycles. East side (front faces
    west): to-sun (0.40, -0.90, 0.36). Bake-only occluders: the built democrat-building.glb
    (shifted into this frame) to the north; 106 Main to the south as a box body with its open
    3-tier front porch (decks, roof, posts). Other collections hidden from render.
 5. Bake a grime mask (dirt splash on the bottom 0.4 m, blotches, chalky streaks under the
    cornice and under the deck edges, worn thresholds) and multiply it in.
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
PH = PROJECT + r"\assets\textures\polyhaven" + "\\"
CO = PROJECT + r"\assets\textures\county-offices" + "\\"
H65 = PROJECT + r"\assets\textures\house-65-main" + "\\"
B35 = PROJECT + r"\assets\textures\block-35-41" + "\\"
SHARED = PROJECT + r"\assets\textures\shared" + "\\"
GLB = PROJECT + r"\assets\models\store-100-102.glb"
GLB_DB = PROJECT + r"\assets\models\democrat-building.glb"
OFF_DB = (43.85 - 52.01, 10.08 - 10.30, 0.0)   # democrat-building local -> this frame
LIGHTMAP = PROJECT + r"\assets\textures\store-100-102-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 384
GLASS_ALPHA = 0.40
GLASS_RGB = (0x1A, 0x19, 0x16)
ATLAS = ("WindowBack",)
TO_SUN = (0.40, -0.90, 0.36)          # east-side building (front faces west)
COLL, RIG, PREFIX, FPREFIX = "Store100102", "SS_BakeRig", "SS_", "SSR_"
ALLEY = -0.15
CURB_Y = 6.52 - 10.30                 # east curb in this frame

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\store_100_102.py", encoding="utf-8").read())

# 2. Materials ----------------------------------------------------------------
def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    """Constant colour that turns a texture averaging `avg` (sRGB 0-255) into `target`."""
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


# part -> (texture file, metres per repeat, roughness, plain colour (linear) or None, tint or None)
LOOK = {
    "Clapboard": (H65 + "clapboard_cream.jpg", 1.0, 0.85, None, tint((229, 223, 204), (0xB4, 0xAC, 0x98))),
    "Trim":      (PH + "trim_paint_cream.jpg", 1.0, 0.6, None, tint((230, 218, 191), (0xD8, 0xD0, 0xBC))),
    "Shopfront": (PH + "door_paint_green.jpg", 0.8, 0.6, None, tint((93, 107, 92), (0x3A, 0x3A, 0x2E))),
    "Deck":      (B35 + "trim_stone_grey.jpg", 2.0, 0.85, None, tint((162, 154, 135), (0x8E, 0x8B, 0x82))),
    "Roof":      (CO + "roof_tin_redbrown.jpg", 2.0, 0.8, None, (0.78, 0.78, 0.80)),
    "Glass":     (None, 1.0, 0.05, tuple(srgb_to_lin(c) for c in GLASS_RGB), None),
    "WindowBack": (SHARED + "window_backs.jpg", None, 0.9, None, None),
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


FINAL = {k: textured_material("glass" if k == "Glass" else FPREFIX + k, LOOK[k][0], *LOOK[k][2:]) for k in LOOK}


def box_uvs(obj):
    """Project each face from its dominant axis so textures keep real-world scale; sloping
    faces are projected along the slope. Window backs keep their atlas UVs."""
    mesh = obj.data
    for layer in [l for l in mesh.uv_layers if l.name != "UVMap"]:
        mesh.uv_layers.remove(layer)
    uv = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    keys = [m.name[len(PREFIX):] for m in mesh.materials]
    for poly in mesh.polygons:
        key = keys[poly.material_index]
        if key in ATLAS:
            continue
        tile = LOOK[key][1]
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
    box_uvs(obj)
    for i, m in enumerate(obj.data.materials):
        obj.data.materials[i] = FINAL[m.name[len(PREFIX):]]

# 3. Join, drop hidden faces, unwrap the lightmap UVs --------------------------
ss_obj = bpy.data.objects["SS_Main"]
with bpy.context.temp_override(active_object=ss_obj, selected_objects=parts, selected_editable_objects=parts):
    bpy.ops.object.join()
ss_obj.name = ss_obj.data.name = COLL
mesh = ss_obj.data


def fibonacci(n):
    pts = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        a = i * math.pi * (3 - math.sqrt(5))
        pts.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    return pts


def face_samples(f, tris, rng):
    """Points spread over the face (about one per 0.01 m2, 6 to 3000), pulled in from the edges."""
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
    (the glass does not block). Downward faces at or below grade go too."""
    import random
    rng = random.Random(7)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for co, no, only in CUT_PLANES:
        bm.normal_update()
        if only:
            faces = [f for f in bm.faces if only(f)]
            geom = faces + list({e for f in faces for e in f.edges}) + list({v for f in faces for v in f.verts})
        else:
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-4, plane_co=co, plane_no=no)
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


def on_main_wall(f):
    """Faces in the main wall's plane (y = 2.16), facing the street."""
    return f.normal.y < -0.9 and all(abs(v.co.y - YM) < 1e-3 for v in f.verts)


def on_north_wall(f):
    return f.normal.x < -0.9 and all(abs(v.co.x + HW) < 1e-3 for v in f.verts)


# the decks and the cornice cover strips of the main wall; the News lean-to's roof line
# (3.0 m) splits the north wall so the part behind it can be weighted down in the lightmap
CUT_PLANES = [((0, 0, z), (0, 0, 1), on_main_wall) for z in (DECKS[0][1], DECKS[1][0], DECKS[1][1], CB)] + \
             [((0, 0, 3.0), (0, 0, 1), on_north_wall), ((0, 9.35, 0), (0, 1, 0), on_north_wall)]
before = sum(len(p.vertices) - 2 for p in mesh.polygons)
removed = remove_hidden_faces(ss_obj)
after = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("hidden faces removed:", removed, "| triangles", before, "->", after)

# every visible face must point out of the model (no inward faces)
bvh_all = BVHTree.FromPolygons([v.co for v in mesh.vertices], [list(p.vertices) for p in mesh.polygons])
inward = 0
for p in mesh.polygons:
    hit = bvh_all.ray_cast(p.center + p.normal * 0.002, p.normal, 0.004)
    if hit[0] is not None:
        inward += 1
print("faces with something touching right in front of them:", inward)

lm = mesh.uv_layers.new(name="Lightmap")
mesh.uv_layers.active = lm
mesh.uv_layers["UVMap"].active_render = True
for o in bpy.context.view_layer.objects:
    o.select_set(o == ss_obj)
bpy.context.view_layer.objects.active = ss_obj
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004,
                         area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.object.mode_set(mode="OBJECT")
LM_SHRINK = {"glass": 0.03, FPREFIX + "WindowBack": 0.6, FPREFIX + "Roof": 0.3}
lm_data = mesh.uv_layers["Lightmap"].data
mat_names = [m.name for m in mesh.materials]
for p in mesh.polygons:
    name = mat_names[p.material_index]
    f = LM_SHRINK.get(name)
    c, n = p.center, p.normal
    if name == "glass":
        pass
    elif c.y > YR - 0.01:
        f = 0.2                                   # rear wall and the rear porch
    elif n.x > 0.9 and c.x > HW - 0.01:
        f = 0.1                                   # party wall with 106
    elif (n.x > 0.9 and abs(c.x - COURT[0]) < 0.01 and c.y > COURT[1]) or \
            (n.y > 0.9 and abs(c.y - COURT[1]) < 0.01 and c.x > COURT[0]):
        f = 0.15                                  # light court
    elif n.x < -0.9 and c.x < BUMP[0] + 0.01:
        f = min(f or 1.0, 0.25)                   # the bump's north face: 0.41 m from the Democrat wall
    elif name == FPREFIX + "Deck" and n.z > 0.9 and c.z > 3.0:
        f = 0.5                                   # gallery deck tops (above eye level)
    elif n.x < -0.9 and c.x < -HW + 0.01 and c.z < 3.0 and c.y < 9.35:
        f = 0.1                                   # north wall behind the News lean-to
    elif n.x < -0.9 and c.x < -HW + 0.01 and c.y > YM + 0.5:
        f = min(f or 1.0, 0.55)                   # north wall and the bump (seen over the News roof)
    elif c.y > BUMP[1] - 0.01 and c.x < -HW + 0.01:
        f = min(f or 1.0, 0.4)                    # the bump's front face
    if f:
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.0015, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig: sun, sky, ground, occluders (in SS_BakeRig, not exported) ----------
scene = bpy.context.scene
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
for o in list(rig.objects):
    bpy.data.objects.remove(o, do_unlink=True)
rig.hide_viewport = False
rig.hide_render = False
sun = bpy.data.objects.new("SS_Sun", bpy.data.lights.get("SS_Sun") or bpy.data.lights.new("SS_Sun", "SUN"))
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
    v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    m = bpy.data.meshes.new(name)
    m.from_pydata(v, [], [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)])
    m.materials.append(mat)
    o = bpy.data.objects.new(name, m)
    rig.objects.link(o)
    return o


# ground: road and yards 0.15 below the sidewalk (east sidewalk from the curb to the front line)
warm = rig_mat("SS_GroundWarm", (0.34, 0.28, 0.19))
rig_box("SS_Ground", -150, 150, -150, 150, -0.35, ALLEY, warm)
rig_box("SS_Sidewalk", -150, 150, CURB_Y, 0.0, -0.35, 0.0, warm)
# 106 Main to the south (PLAN.md): body box from its front wall (y 0) back, and its open 3-tier
# front porch out to y -2.24 (decks, roof, plain posts) instead of a solid box
occ = rig_mat("SS_OccFrame", (0.50, 0.46, 0.38))
rig_box("SS_Occ106", HW, 9.91, 0.0, 18.7, ALLEY, 9.14, occ)
for i, (z0, z1) in enumerate(((3.30, 3.50), (6.15, 6.35), (8.84, 9.14))):
    rig_box("SS_Occ106Deck%d" % i, HW, 9.91, -2.24, 0.0, z0, z1, occ)
for i, x in enumerate((HW + 0.10, 6.81, 9.77)):
    rig_box("SS_Occ106Post%d" % i, x - 0.07, x + 0.07, -2.24, -2.10, 0.0, 8.84, occ)
# the built Democrat building (with its News lean-to) to the north
before_objs = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_DB)
for o in [o for o in bpy.data.objects if o not in before_objs]:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    rig.objects.link(o)
    o.location = Vector(OFF_DB)
    o.name = "SS_OccDemocrat"
    o.select_set(False)
    for slot in o.material_slots:          # its glass fully transparent, like ours
        if slot.material and slot.material.name.startswith("glass"):
            b = next((n for n in slot.material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if b:
                b.inputs["Alpha"].default_value = 0.0

if scene.world is None:
    scene.world = bpy.data.worlds.new("SS_Sky")
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


# how much of the grime each material takes
DIRT = {"Clapboard": 1.0, "Trim": 0.75, "Shopfront": 0.7, "Deck": 0.9, "Roof": 0.8, "Glass": 0.0,
        "WindowBack": 0.3}


def grime_material(key, grime_img):
    """Emission = grey grime factor for one material slot (DIRT[key] scales the dirt)."""
    name = "SS_GrimeBake_" + key
    gm = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    gm.use_nodes = True
    nt = gm.node_tree
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

    def map_range(value_socket, a, b, c, d):
        m = N("ShaderNodeMapRange")
        m.inputs["From Min"].default_value, m.inputs["From Max"].default_value = a, b
        m.inputs["To Min"].default_value, m.inputs["To Max"].default_value = c, d
        L(value_socket, m.inputs["Value"])
        return m.outputs["Result"]

    def op(o, a, b=None):
        m = N("ShaderNodeMath")
        m.operation = o
        for i, s in enumerate((a, b)):
            if s is None:
                continue
            if isinstance(s, (int, float)):
                m.inputs[i].default_value = s
            else:
                L(s, m.inputs[i])
        return m.outputs["Value"]

    mult = lambda a, b: op("MULTIPLY", a, b)
    # dirt splash on the bottom ~0.4 m, fading out by 1.0 m
    height = map_range(Z, -0.1, 1.0, 0.74, 1.0)
    noise = N("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.5
    noise.inputs["Detail"].default_value = 6.0
    L(geo.outputs["Position"], noise.inputs["Vector"])
    blotch = map_range(noise.outputs["Fac"], 0.0, 1.0, 0.86, 1.03)
    stretch = N("ShaderNodeVectorMath")                        # vertical streaks (chalky paint runs)
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (3.5, 3.5, 0.15)
    L(geo.outputs["Position"], stretch.inputs[0])
    sn = N("ShaderNodeTexNoise")
    sn.inputs["Scale"].default_value = 1.8
    sn.inputs["Detail"].default_value = 2.0
    L(stretch.outputs["Vector"], sn.inputs["Vector"])
    streaks = map_range(sn.outputs["Fac"], 0.35, 0.75, 0.90, 1.0)
    # streaked under the cornice and under the two deck edges (strongest right under them)
    under = mult(map_range(Z, CB - 0.9, CB - 0.16, 1.0, 0.86), map_range(Z, CB - 0.16, CB - 0.12, 1.0, 1.16))
    under = mult(under, mult(map_range(Z, DECKS[1][0] - 0.7, DECKS[1][0], 1.0, 0.90),
                             map_range(Z, DECKS[1][0], DECKS[1][0] + 0.03, 1.0, 1.11)))
    under = mult(under, mult(map_range(Z, 2.40, 2.95, 1.0, 0.90), map_range(Z, 2.95, 2.98, 1.0, 1.11)))
    # worn, dirty thresholds and recess floor: upward faces at sidewalk level
    up = map_range(nsep.outputs["Z"], 0.8, 0.95, 0.0, 1.0)
    low = map_range(Z, 0.04, 0.08, 1.0, 0.0)
    wear = map_range(mult(up, low), 0.0, 1.0, 1.0, 0.80)
    # deck tops darker near the main wall and the doors (foot traffic, dust)
    deck = mult(up, map_range(Y, YM - 0.8, YM, 0.0, 1.0))
    deck = map_range(mult(deck, map_range(Z, 3.0, 3.4, 0.0, 1.0)), 0.0, 1.0, 1.0, 0.88)
    grey = mult(mult(mult(height, blotch), mult(streaks, under)), mult(wear, deck))
    grey = op("MINIMUM", grey, 1.0)
    # DIRT: 1 - d * (1 - grey)
    grey = op("SUBTRACT", 1.0, mult(op("SUBTRACT", 1.0, grey), DIRT[key]))
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    L(gc.outputs["Vector"], emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    target = N("ShaderNodeTexImage")
    target.image = grime_img
    target_uv = N("ShaderNodeUVMap")
    target_uv.uv_map = "Lightmap"
    L(target_uv.outputs["UV"], target.inputs["Vector"])
    nt.nodes.active = target
    return gm


glass_alpha = next(n for n in FINAL["Glass"].node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"]
glass_alpha.default_value = 0.0             # light passes the panes to the window backs
for o in bpy.context.view_layer.objects:
    o.select_set(o == ss_obj)
bpy.context.view_layer.objects.active = ss_obj
saved = list(mesh.materials)
try:
    light_img = bake_target("SS_Light", True)
    point_materials_at(light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask --------------------------------------------------------------
    grime_img = bake_target("SS_Grime", True)
    for i, m in enumerate(saved):
        key = "Glass" if m.name == "glass" else m.name[len(FPREFIX):]
        mesh.materials[i] = grime_material(key, grime_img)
    bpy.ops.object.bake(type="EMIT", margin=0, use_clear=True)
    print("grime baked")
finally:
    for i, mat in enumerate(saved):
        mesh.materials[i] = mat
    glass_alpha.default_value = GLASS_ALPHA
    for name, state in render_state.items():
        if bpy.data.collections.get(name):
            bpy.data.collections[name].hide_render = state
    for name, state in loose_state.items():
        if bpy.data.objects.get(name):
            bpy.data.objects[name].hide_render = state
for m in [m for m in bpy.data.materials if m.name.startswith("SS_GrimeBake_")]:
    bpy.data.materials.remove(m)

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
# Warm the shade a little (sky-only light is blue).
lum = combined.mean(axis=1, keepdims=True)
combined = combined * 0.75 + lum * np.array([[1.0, 0.96, 0.88]]) * 0.25
scale = float(np.percentile(combined[baked].max(axis=1), 99.5))
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
out_img = bpy.data.images.get("SS_Lightmap") or bpy.data.images.new("SS_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
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
    o.select_set(o == ss_obj)
bpy.context.view_layer.objects.active = ss_obj
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_texcoords=True,
                          export_normals=True)
tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("exported", GLB, "|", tris, "triangles |", len(mesh.materials), "materials")
ss_obj["lightmap_scale"] = LIGHTMAP_SCALE            # read by store_100_102_preview.py
