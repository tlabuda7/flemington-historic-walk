"""
union_hotel_bake.py - realistic materials and baked lighting for the Union Hotel,
then export to assets/models/union-hotel.glb.

Run inside Blender (after `python tools/prepare_textures.py`):
    exec(open(r"<project>/tools/blender/union_hotel_bake.py").read())

Steps:
 1. Rebuild the geometry (union_hotel.py).
 2. Give every surface a Poly Haven colour texture (CC0), tiled in real-world metres.
 3. Join the parts into one object and unwrap a second UV map, "Lightmap".
 4. Bake warm late-afternoon sun + sky (direct and bounced light, which includes
    ambient occlusion and shadows) into one 2K lightmap with Cycles.
 5. Bake a grime mask (darker near the ground, blotchy fading) and multiply it in.
 6. Export the GLB. The lightmap is saved next to it as a JPEG and applied in
    A-Frame by the `baked-lighting` component (unlit material: colour x lightmap),
    which is also the cheapest way to draw it on a Quest 2.
"""

import math
import bpy
import numpy as np
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
TEX = PROJECT + r"\assets\textures\polyhaven" + "\\"
GLB = PROJECT + r"\assets\models\union-hotel.glb"
LIGHTMAP = PROJECT + r"\assets\textures\union-hotel-lightmap.jpg"
LIGHTMAP_SIZE = 2048
SAMPLES = 128

# 1. Geometry -----------------------------------------------------------------
exec(open(PROJECT + r"\tools\blender\union_hotel.py").read())

# 2. Materials ----------------------------------------------------------------
# part -> (texture file, metres covered by one repeat, roughness).  None = plain colour.
LOOK = {
    "UH_Walls":   ("red_brick.jpg", 1.4, 0.9),
    "UH_Brick":   ("red_brick.jpg", 1.4, 0.9),
    "UH_Trim":    ("trim_paint_cream.jpg", 2.0, 0.7),
    "UH_Letters": ("trim_paint_cream.jpg", 2.0, 0.7),
    "UH_Slate":   ("roof_slates_03.jpg", 3.0, 0.8),
    "UH_Roof":    ("metal_plate_02.jpg", 2.0, 0.6),
    "UH_Boards":  ("weathered_planks.jpg", 2.0, 0.9),
    "UH_Stone":   ("concrete_floor_worn_001.jpg", 3.0, 0.9),
    "UH_Wood":    ("wood_table_worn.jpg", 0.55, 0.7),
    "UH_Sign":    ("sign_paint_green.jpg", 2.0, 0.7),
    "UH_Glass":   None,
}


def textured_material(name, image_file, roughness):
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
        tex.image = bpy.data.images.load(TEX + image_file, check_existing=True)
        nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    else:   # old window glass: very dark, slightly green, glossy
        bsdf.inputs["Base Color"].default_value = (0.012, 0.016, 0.016, 1)
        bsdf.inputs["Roughness"].default_value = 0.08
    return mat


def box_uvs(obj, tile):
    """Project each face from its dominant axis, so textures keep real-world scale."""
    mesh = obj.data
    while mesh.uv_layers:
        mesh.uv_layers.remove(mesh.uv_layers[0])
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            if ax == 2:
                u, v = co.x, co.y
            elif ax == 0:
                u, v = co.y, co.z
            else:
                u, v = co.x, co.z
            uv.data[li].uv = (u / tile, v / tile)


parts = [o for o in col.objects if o.type == "MESH"]
for obj in parts:
    look = LOOK[obj.name.split(".")[0]]
    image_file, tile, rough = look if look else (None, 1.0, 0.1)
    obj.data.materials.clear()
    obj.data.materials.append(textured_material("UHR_" + obj.name[3:], image_file, rough))
    box_uvs(obj, tile)

# 3. Join and unwrap the lightmap UVs -------------------------------------------
hotel = bpy.data.objects["UH_Walls"]
with bpy.context.temp_override(active_object=hotel, selected_objects=parts,
                               selected_editable_objects=parts):
    bpy.ops.object.join()
hotel.name = hotel.data.name = "UnionHotel"

mesh = hotel.data
lm = mesh.uv_layers.new(name="Lightmap")
mesh.uv_layers.active = lm
mesh.uv_layers["UVMap"].active_render = True
for o in bpy.context.view_layer.objects:
    o.select_set(o == hotel)
bpy.context.view_layer.objects.active = hotel
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004,
                         area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.object.mode_set(mode="OBJECT")

# 4. Light: warm late-afternoon sun from the west-south-west, plus sky ---------
# The hotel's front (-Y here) faces west on Main Street, so the sun is in front of it.
sun = bpy.data.objects.get("Light")
sun.data.type = "SUN"
sun.data.energy = 3.2
sun.data.color = (1.0, 0.80, 0.58)
sun.data.angle = math.radians(1.5)
to_sun = Vector((0.40, -0.90, 0.36)).normalized()     # about 21 degrees above the horizon
sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()

world = bpy.context.scene.world
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.42, 0.55, 0.78, 1)
bg.inputs[1].default_value = 0.9

for name in ("Preview_Road", "Preview_Sidewalk"):
    if bpy.data.objects.get(name):
        bpy.data.objects[name].hide_render = True    # only the ground bounces light

scene = bpy.context.scene
try:
    scene.render.engine = "CYCLES"
except TypeError as e:
    print("engine choices:", e)
scene.cycles.device = "GPU"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = False


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


light_img = bake_target("UH_Light", True)
point_materials_at(light_img)
bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"}, margin=8, use_clear=True)
print("lighting baked")

# 5. Grime mask: darker near the ground, plus soft blotches of faded paint ------
grime_mat = bpy.data.materials.get("UH_GrimeBake") or bpy.data.materials.new("UH_GrimeBake")
grime_mat.use_nodes = True
nt = grime_mat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
emit = nt.nodes.new("ShaderNodeEmission")
geo = nt.nodes.new("ShaderNodeNewGeometry")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
height = nt.nodes.new("ShaderNodeMapRange")     # 0 m -> 0.62, 1.8 m and above -> 1.0
height.inputs["From Min"].default_value = 0.0
height.inputs["From Max"].default_value = 1.8
height.inputs["To Min"].default_value = 0.62
height.inputs["To Max"].default_value = 1.0
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 0.6
noise.inputs["Detail"].default_value = 6.0
blotch = nt.nodes.new("ShaderNodeMapRange")     # noise -> 0.86 .. 1.04
blotch.inputs["To Min"].default_value = 0.86
blotch.inputs["To Max"].default_value = 1.04
mult = nt.nodes.new("ShaderNodeMath")
mult.operation = "MULTIPLY"
nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
nt.links.new(sep.outputs["Z"], height.inputs["Value"])
nt.links.new(geo.outputs["Position"], noise.inputs["Vector"])
nt.links.new(noise.outputs["Fac"], blotch.inputs["Value"])
nt.links.new(height.outputs["Result"], mult.inputs[0])
nt.links.new(blotch.outputs["Result"], mult.inputs[1])
nt.links.new(mult.outputs["Value"], emit.inputs["Color"])
nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
grime_img = bake_target("UH_Grime", True)
target = nt.nodes.new("ShaderNodeTexImage")
target.image = grime_img
target_uv = nt.nodes.new("ShaderNodeUVMap")
target_uv.uv_map = "Lightmap"
nt.links.new(target_uv.outputs["UV"], target.inputs["Vector"])
nt.nodes.active = target

saved = list(mesh.materials)
for i in range(len(mesh.materials)):
    mesh.materials[i] = grime_mat
bpy.ops.object.bake(type="EMIT", margin=8, use_clear=True)
for i, mat in enumerate(saved):
    mesh.materials[i] = mat
print("grime baked")

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
encoded = np.clip(combined / scale, 0, 1) ** (1 / 2.2)
rgba = np.ones((px, 4), dtype=np.float32)
rgba[:, :3] = encoded
out_img = bpy.data.images.get("UH_Lightmap") or bpy.data.images.new("UH_Lightmap", LIGHTMAP_SIZE, LIGHTMAP_SIZE)
out_img.scale(LIGHTMAP_SIZE, LIGHTMAP_SIZE)
out_img.colorspace_settings.name = "Non-Color"
out_img.pixels.foreach_set(rgba.ravel())
out_img.filepath_raw = LIGHTMAP
out_img.file_format = "JPEG"
scene.render.image_settings.quality = 88
out_img.save()
print("LIGHTMAP_SCALE =", round(scale, 4), "(use baked-lighting intensity:", round(scale, 4), ")")

# The letters are too small to bake reliably, and they sit flat on the sign board,
# so give them the board's lighting: point all their lightmap UVs at the board's face.
mat_names = [m.name for m in mesh.materials]
sign_i, letters_i = mat_names.index("UHR_Sign"), mat_names.index("UHR_Letters")
lm_data = mesh.uv_layers["Lightmap"].data
board = max((p for p in mesh.polygons if p.material_index == sign_i and p.normal.y < -0.5),
            key=lambda p: p.area)
board_uv = [sum(lm_data[li].uv[k] for li in board.loop_indices) / board.loop_total for k in (0, 1)]
for p in mesh.polygons:
    if p.material_index == letters_i:
        for li in p.loop_indices:
            lm_data[li].uv = board_uv

# Remove the bake helper nodes so they are not exported.
for mat in mesh.materials:
    for name in ("BakeTarget", "BakeUV"):
        node = mat.node_tree.nodes.get(name)
        if node:
            mat.node_tree.nodes.remove(node)

# 6. Export ---------------------------------------------------------------------
for o in bpy.context.scene.objects:
    o.select_set(o == hotel)
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_texcoords=True,
                          export_normals=True)
tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
print("exported", GLB, "|", tris, "triangles |", len(mesh.materials), "materials")
