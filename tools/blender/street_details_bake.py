"""
street_details_bake.py - materials, baked lighting and export for the street-details kit,
pass 2 batch B (assets/models/street-details.glb). Same pipeline as sidestreet_bloomfield_bake.py,
except that the objects stay separate (one glTF node per placed fence run / prop, built in scene
coordinates) and share one lightmap.

Run inside Blender:
    exec(open(r"<project>/tools/blender/street_details_bake.py").read())

 1. Rebuild the geometry (street_details.py).
 2. Six materials (colour maps 1024 px, box UVs in metres):
      sd_paint_white     courthouse/paint_white.jpg, tile 1 m (pickets, posts, urn, barber pole)
      sd_metal           plain dark grey, no map (wire, pipe rail, line posts, hinges; the
                         wire is lifted to mid-grey by the Tint attribute)
      sd_wood_weathered  wurts-law-office/planks_grey.jpg (board fence: one texture strip per board)
      sd_stone           street-details/stone_pale.jpg, tile 1 m (stone post)
      sd_atlas           street-details/details_atlas.jpg (barber stripes, lettered box, paint,
                         hedge core leaves)
      sd_hedge_cutout    leaf_cluster.png, alpha-tested (MASK 0.5), double-sided: hedge leaf cards
 3. "Lightmap" UVs for all eight objects together (smart project, weighted, one pack).
 4. Cycles bake DIFFUSE direct + indirect into one 2K lightmap, sun to-vector (-0.90, -0.40, 0.36),
    sky (0.42, 0.55, 0.78) x 0.9. Bake-only casters (collection SD_Context, never exported): the
    placed neighbours (Wurts, 65 Main, County Offices, courthouse, 57 Main, Rea, Union Hotel,
    68 Main) and six street trees at their index.html places, ground and walk slabs.
 5. Grime mask (darker toward the ground, splash band, blotches) x Tint.
 6. Fill empty pixels, warm the shade, save sRGB JPEG, print LIGHTMAP_SCALE, export the GLB.
"""
import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
TX = PROJECT + r"\assets\textures" + "\\"
GLB = PROJECT + r"\assets\models\street-details.glb"
LIGHTMAP = PROJECT + r"\assets\textures\street-details-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 256
TO_SUN = (-0.90, -0.40, 0.36)
RIG = "SD_BakeRig"

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\street_details.py").read())
objs = list(OBJECTS.values())
ctx = load_context()


# 2. Materials ----------------------------------------------------------------
def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def tint(avg, target):
    return tuple(min(1.0, srgb_to_lin(t) / srgb_to_lin(a)) for a, t in zip(avg, target))


def material(name, image_file=None, roughness=0.85, factor=None, colour=None, cutout=False):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = roughness
    if image_file is None:
        bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
        mat.diffuse_color = (*colour, 1.0)
        mat.use_backface_culling = True
        return mat
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
    if cutout:
        rnd = nt.nodes.new("ShaderNodeMath")       # glTF exporter: Round -> alphaMode MASK, cutoff 0.5
        rnd.operation = "ROUND"
        nt.links.new(tex.outputs["Alpha"], rnd.inputs[0])
        nt.links.new(rnd.outputs[0], bsdf.inputs["Alpha"])
        mat.use_backface_culling = False
        try:
            mat.surface_render_method = "DITHERED"
        except (AttributeError, TypeError):
            pass
    else:
        mat.use_backface_culling = True
    return mat


FINAL = {
    "sd_paint_white": material("sd_paint_white", TX + r"courthouse\paint_white.jpg", 0.8),
    "sd_metal": material("sd_metal", None, 0.6, colour=(srgb_to_lin(66), srgb_to_lin(66), srgb_to_lin(64))),
    "sd_wood_weathered": material("sd_wood_weathered", TX + r"wurts-law-office\planks_grey.jpg", 0.95),
    "sd_stone": material("sd_stone", TX + r"street-details\stone_pale.jpg", 0.9,
                         tint((174, 170, 163), (0xC4, 0xBF, 0xB2))),
    "sd_atlas": material("sd_atlas", TX + r"street-details\details_atlas.jpg", 0.8),
    "sd_hedge_cutout": material("sd_hedge_cutout", TX + r"leaf_cluster.png", 0.9,
                                tint((70, 110, 50), (58, 88, 40)), cutout=True),
}
for o in objs:
    for i, name in enumerate(MATS):
        o.data.materials[i] = FINAL[name]

# 3. Lightmap UVs ---------------------------------------------------------------
for o in bpy.context.view_layer.objects:
    o.select_set(o in objs)
bpy.context.view_layer.objects.active = objs[0]
for o in objs:
    me = o.data
    lm = me.uv_layers.get("Lightmap") or me.uv_layers.new(name="Lightmap")
    me.uv_layers.active = lm
    me.uv_layers["UVMap"].active_render = True
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.002, area_weight=0.0,
                         correct_aspect=True, scale_to_bounds=False)
bpy.ops.object.mode_set(mode="OBJECT")
WEIGHT = {"fence-59-wurts": 1.0, "fence-65-picket": 0.9, "post-stone-39": 1.2, "fence-69-pipe-rail": 1.0,
          "fence-69-board": 0.75, "hedge-rea": 0.6, "waste-paper-box": 1.6, "barber-pole-72": 1.6}
for o in objs:
    me = o.data
    lm_data = me.uv_layers["Lightmap"].data
    for p in me.polygons:
        f = WEIGHT[o.name]
        if MATS[p.material_index] == "sd_metal":
            f *= 1.6          # thin wire / rail: keep a few texels across
        if MATS[p.material_index] == "sd_hedge_cutout":
            f *= 0.7
        if p.normal.z < -0.5:
            f *= 0.5
        for li in p.loop_indices:
            lm_data[li].uv = lm_data[li].uv * f
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION",
                        margin=0.002, shape_method="CONCAVE")
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light rig ------------------------------------------------------------------
scene = bpy.context.scene
rig = bpy.data.collections.get(RIG)
if not rig:
    rig = bpy.data.collections.new(RIG)
    scene.collection.children.link(rig)
for o in list(rig.objects):
    bpy.data.objects.remove(o, do_unlink=True)
rig.hide_viewport = False
rig.hide_render = False
sun = bpy.data.objects.new("SD_Sun", bpy.data.lights.new("SD_Sun", "SUN"))
rig.objects.link(sun)
sun.data.energy = 3.2
sun.data.color = (1.0, 0.80, 0.58)
sun.data.angle = math.radians(1.5)
to_sun = Vector(TO_SUN).normalized()
sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()

if scene.world is None:
    scene.world = bpy.data.worlds.new("SD_Sky")
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

render_state = {c.name: c.hide_render for c in bpy.data.collections}
for c in bpy.data.collections:
    c.hide_render = c.name not in (COLL, RIG, CTX)
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
scene.cycles.transparent_max_bounces = 16
print("Cycles device:", prefs.compute_device_type, [d.name for d in prefs.devices if d.use])


def bake_target(name, float_buffer):
    img = bpy.data.images.get(name)
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(name, LIGHTMAP_SIZE, LIGHTMAP_SIZE, alpha=True, float_buffer=float_buffer)
    img.generated_color = (0, 0, 0, 0)
    return img


def point_materials_at(mats, img):
    for mat in mats:
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
    o.select_set(o in objs)
bpy.context.view_layer.objects.active = objs[0]
grime_mat = None
try:
    light_img = bake_target("SD_Light", True)
    point_materials_at(FINAL.values(), light_img)
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=0, use_clear=True)
    print("lighting baked")

    # 5. Grime mask -------------------------------------------------------------
    grime_mat = bpy.data.materials.get("SD_GrimeBake") or bpy.data.materials.new("SD_GrimeBake")
    grime_mat.use_nodes = True
    nt = grime_mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    emit = N("ShaderNodeEmission")
    geo = N("ShaderNodeNewGeometry")
    sep = N("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs["Vector"])
    nsep = N("ShaderNodeSeparateXYZ")
    L(geo.outputs["Normal"], nsep.inputs["Vector"])
    Z = sep.outputs["Z"]
    NZ = nsep.outputs["Z"]

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

    def noise_tex(vec, scale, detail):
        t = N("ShaderNodeTexNoise")
        t.inputs["Scale"].default_value = scale
        t.inputs["Detail"].default_value = detail
        L(vec, t.inputs["Vector"])
        return t.outputs["Fac"]

    # darker toward the ground (splash and soil up to ~0.35 m above the base), fading by 0.8 m
    band = map_range(Z, 0.02, 0.8, 0.68, 1.0)
    blotch = map_range(noise_tex(geo.outputs["Position"], 1.6, 6.0), 0.0, 1.0, 0.82, 1.06)
    stretch = N("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (6.0, 6.0, 0.4)
    L(geo.outputs["Position"], stretch.inputs[0])
    streaks = map_range(noise_tex(stretch.outputs["Vector"], 2.5, 2.0), 0.35, 0.75, 0.90, 1.0)
    # tops of rails, caps and the hedge top catch a little dust: slightly paler/greyer is not
    # possible with a multiply mask, so only the undersides darken a bit more
    under = map_range(NZ, -0.2, -0.9, 1.0, 0.85)
    grey = mult(band, blotch, streaks, under)
    gc = N("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        L(grey, gc.inputs[k])
    attr = N("ShaderNodeAttribute")
    attr.attribute_name = "Tint"
    vm = N("ShaderNodeVectorMath")
    vm.operation = "MULTIPLY"
    L(gc.outputs["Vector"], vm.inputs[0])
    L(attr.outputs["Color"], vm.inputs[1])
    L(vm.outputs["Vector"], emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    grime_img = bake_target("SD_Grime", True)
    target = N("ShaderNodeTexImage")
    target.image = grime_img
    target_uv = N("ShaderNodeUVMap")
    target_uv.uv_map = "Lightmap"
    L(target_uv.outputs["UV"], target.inputs["Vector"])
    nt.nodes.active = target
    for o in objs:
        for i in range(len(o.data.materials)):
            o.data.materials[i] = grime_mat
    bpy.ops.object.bake(type="EMIT", margin=0, use_clear=True)
    print("grime baked")
finally:
    for o in objs:
        for i, name in enumerate(MATS):
            o.data.materials[i] = FINAL[name]
    for name, state in render_state.items():
        if bpy.data.collections.get(name):
            bpy.data.collections[name].hide_render = state
    for name, state in loose_state.items():
        if bpy.data.objects.get(name):
            bpy.data.objects[name].hide_render = state
    rig.hide_render = True
    rig.hide_viewport = True
    ctx.hide_render = True

# 6. Combine, normalise, save ---------------------------------------------------
px = LIGHTMAP_SIZE * LIGHTMAP_SIZE
light = np.empty(px * 4, dtype=np.float32)
grime = np.empty(px * 4, dtype=np.float32)
light_img.pixels.foreach_get(light)
grime_img.pixels.foreach_get(grime)
light = light.reshape(-1, 4)
grime = grime.reshape(-1, 4)
baked = light[:, 3] > 0.5
combined = light[:, :3] * np.where(baked[:, None], grime[:, :3], 1.0)
lum = combined.mean(axis=1, keepdims=True)
ref = np.percentile(lum[baked], 99.0)
shade = np.clip(1.0 - lum / (0.9 * ref), 0.0, 1.0)
w = 0.12 + 0.63 * shade
combined = combined * (1 - w) + lum * np.array([[1.0, 0.94, 0.80]]) * w
scale = float(np.percentile(combined[baked].max(axis=1), 99.5))
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
out_img = bpy.data.images.get("SD_Lightmap") or bpy.data.images.new("SD_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
out_img.scale(LIGHTMAP_SIZE, LIGHTMAP_SIZE)
out_img.colorspace_settings.name = "Non-Color"
out_img.pixels.foreach_set(rgba.ravel())
out_img.filepath_raw = LIGHTMAP
out_img.file_format = "JPEG"
scene.render.image_settings.quality = 88
out_img.save()
LIGHTMAP_SCALE = round(scale, 4)
print("lightmap coverage: %.1f%% of pixels baked" % (100 * baked.mean()))
print("LIGHTMAP_SCALE =", LIGHTMAP_SCALE)

for mat in FINAL.values():
    for name in ("BakeTarget", "BakeUV"):
        node = mat.node_tree.nodes.get(name)
        if node:
            mat.node_tree.nodes.remove(node)
for o in objs:
    me = o.data
    for a in ("Tint", "explicit_uv"):
        if me.attributes.get(a):
            me.attributes.remove(me.attributes[a])
    # drop unused material slots so each node only carries what it uses
    used = sorted({p.material_index for p in me.polygons})
    remap = {old: new for new, old in enumerate(used)}
    mi = np.empty(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get("material_index", mi)
    keep = [me.materials[i] for i in used]
    me.materials.clear()
    for m in keep:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", np.array([remap[i] for i in mi], dtype=np.int32))

# 7. Export ---------------------------------------------------------------------
for o in bpy.context.scene.objects:
    o.select_set(o in objs)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_texcoords=True,
                          export_normals=True)
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
import os
print("exported", GLB, "|", tris, "triangles |", round(os.path.getsize(GLB) / 1e6, 3), "MB")
for o in objs:
    o["lightmap_scale"] = LIGHTMAP_SCALE
