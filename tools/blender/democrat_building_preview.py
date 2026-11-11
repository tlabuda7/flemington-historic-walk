"""
democrat_building_preview.py - review previews of the baked Democrat building, 96-98 Main St
(run after democrat_building_bake.py).

    exec(open(r"<project>/tools/blender/democrat_building_preview.py").read())

Renders with EEVEE, view transform "Standard", and every material swapped for an unlit
emission of colour x lightmap x LIGHTMAP_SCALE - the same maths as the web page's
`baked-lighting` component (MeshBasicMaterial: map x color x lightMap x intensity), so
the pictures match what the headset shows. The colour tints (glTF baseColorFactor) are
included. Writes assets/models/previews/democrat-building-*.png (1280 px wide). The camera,
engine, view transform, resolution and the building's own materials are restored.
The "context" view adds plain unlit boxes for the two neighbours (Masonic Hall, 100-102).
"""

import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\democrat-building-lightmap.jpg"

scene = bpy.context.scene
bk_obj = bpy.data.objects["DemocratBuilding"]
mesh = bk_obj.data
scale = float(bk_obj.get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("DB_Preview")
if not pcol:
    pcol = bpy.data.collections.new("DB_Preview")
    scene.collection.children.link(pcol)
cam_data = bpy.data.cameras.get("DB_Cam") or bpy.data.cameras.new("DB_Cam")
cam = bpy.data.objects.get("DB_Cam") or bpy.data.objects.new("DB_Cam", cam_data)
if cam.name not in pcol.objects:
    pcol.objects.link(cam)
cam_data.clip_start = 0.1
cam_data.clip_end = 600

lm_img = bpy.data.images.load(LIGHTMAP, check_existing=True)
lm_img.reload()
lm_img.colorspace_settings.name = "sRGB"          # three.js decodes it as sRGB too


def sock(socks, name):
    return next(x for x in socks if x.name == name and x.type == "RGBA")


def glass_preview(src):
    """The `glass` material: not lightmapped in the scene; plain dark tint over the
    window backs at its own alpha (the scene adds the sky reflection later)."""
    bsdf = next(n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    mat = bpy.data.materials.new("DBP_" + src.name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    emit = N("ShaderNodeEmission")
    emit.inputs["Color"].default_value = bsdf.inputs["Base Color"].default_value
    tr = N("ShaderNodeBsdfTransparent")
    mix = N("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = bsdf.inputs["Alpha"].default_value
    L(tr.outputs[0], mix.inputs[1])
    L(emit.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs["Surface"])
    mat.use_backface_culling = True
    return mat


def preview_material(src):
    """Unlit copy: emission = base colour (texture x tint, or plain) x lightmap x scale."""
    if src.name == "glass":
        return glass_preview(src)
    mat = bpy.data.materials.new("DBP_" + src.name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    emit = N("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = scale
    uv1 = N("ShaderNodeUVMap")
    uv1.uv_map = "Lightmap"
    lm = N("ShaderNodeTexImage")
    lm.image = lm_img
    L(uv1.outputs["UV"], lm.inputs["Vector"])
    mix = N("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    src_tex = next((n for n in src.node_tree.nodes if n.type == "TEX_IMAGE"), None)
    src_tint = next((n for n in src.node_tree.nodes if n.type == "MIX" and n.blend_type == "MULTIPLY"), None)
    if src_tex:
        uv0 = N("ShaderNodeUVMap")
        uv0.uv_map = "UVMap"
        tex = N("ShaderNodeTexImage")
        tex.image = src_tex.image
        L(uv0.outputs["UV"], tex.inputs["Vector"])
        colour = tex.outputs["Color"]
        if src_tint:
            t = N("ShaderNodeMix")
            t.data_type = "RGBA"
            t.blend_type = "MULTIPLY"
            t.inputs["Factor"].default_value = 1.0
            L(colour, sock(t.inputs, "A"))
            sock(t.inputs, "B").default_value = sock(src_tint.inputs, "B").default_value
            colour = sock(t.outputs, "Result")
        L(colour, sock(mix.inputs, "A"))
    else:
        bsdf = next(n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        sock(mix.inputs, "A").default_value = bsdf.inputs["Base Color"].default_value
    L(lm.outputs["Color"], sock(mix.inputs, "B"))
    L(sock(mix.outputs, "Result"), emit.inputs["Color"])
    L(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def unlit(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*rgb, 1)
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs["Emission"], o.inputs["Surface"])
    return m


def flat(name, x0, x1, y0, y1, z, mat):
    obj = bpy.data.objects.get(name)
    if not obj:
        gm = bpy.data.meshes.new(name)
        gm.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
        gm.materials.append(mat)
        obj = bpy.data.objects.new(name, gm)
        pcol.objects.link(obj)
    return obj


# context (unlit, flat colours): east sidewalk at the sidewalk top from the curb (local
# y = -3.56) back to the wall, the road and the slot 0.15 lower
flat("DBP_Walk", -150, 150, -3.56, 0.22, -0.005, unlit("DBP_WalkMat", (0.36, 0.34, 0.31)))
flat("DBP_Road", -150, 150, -150, 150, -0.15, unlit("DBP_RoadMat", (0.30, 0.27, 0.23)))


def block(name, x0, x1, y0, y1, z0, z1, mat, gable=None):
    """Plain neighbour box (optionally with a front gable up to `gable`), context view only."""
    obj = bpy.data.objects.get(name)
    if not obj:
        v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
        f = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
        if gable:
            xm = (x0 + x1) / 2
            v += [(xm, y0, gable), (xm, y1, gable)]
            f += [(4, 5, 8), (6, 9, 7), (4, 8, 9, 6), (5, 7, 9, 8)]
        gm = bpy.data.meshes.new(name)
        gm.from_pydata(v, [], f)
        gm.materials.append(mat)
        obj = bpy.data.objects.new(name, gm)
        pcol.objects.link(obj)
    return obj


NEIGHBOURS = [block("DBP_Masonic", -22.2, -3.68, 0.2, 18.5, -0.15, 11.6, unlit("DBP_MasonicMat", (0.20, 0.10, 0.07)), 15.6),
              block("DBP_100102", 4.44, 11.86, 0.2, 18.9, -0.15, 9.14, unlit("DBP_100102Mat", (0.33, 0.31, 0.26)))]

# --- remember and change settings ----------------------------------------------------
originals = list(mesh.materials)
previews = [preview_material(m) for m in originals]
saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
render_state = {c.name: c.hide_render for c in bpy.data.collections}
for c in bpy.data.collections:
    c.hide_render = c.name not in ("DemocratBuilding", "DB_Preview")
for i, m in enumerate(previews):
    mesh.materials[i] = m
world = scene.world
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
saved_bg = (tuple(bg.inputs[0].default_value), bg.inputs[1].default_value)
bg.inputs[0].default_value = (0.42, 0.55, 0.78, 1)
bg.inputs[1].default_value = 1.0
scene.camera = cam
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = eng
        break
    except TypeError:
        pass
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1280, 960, 100

# name -> (eye, target, lens). Local frame: -Y = Main St (west), +X = south (News lean-to,
# 100-102), -X = north (slot, Masonic Hall). Scene -> local: X = z - 43.85, Y = x - 10.08,
# Z = y - 0.15. The far (west) sidewalk is ~20 m in front of the wall; eye height 1.6-1.7 m.
VIEWS = {
    "front":          ((0.9, -13.0, 1.7), (0.9, 0.2, 3.35), 30),         # straight on, with the News lean-to
    "three-quarter":  ((-9.0, -11.0, 1.7), (0.6, 0.2, 3.2), 30),         # from the NW
    "detail":         ((-0.4, -4.8, 1.6), (-0.3, 0.3, 1.75), 26),        # shop front: doors, show window, board
    "match-DemocratOffice": ((0.3, -11.0, 1.6), (0.1, 0.2, 3.45), 34),   # Goodspeed frontal view, c. 1900
    "match-OriginalFacade-ca1918": ((9.5, -13.0, 1.6), (0.4, 0.2, 3.6), 34),   # Goodspeed c. 1918, from the SW
    "context":        ((-1.5, -17.0, 1.7), (-1.5, 0.2, 5.6), 24),        # with plain boxes for the neighbours
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS     # set PREVIEW_VIEWS before exec() for other views
PREFIX = globals().get("PREVIEW_PREFIX") or "democrat-building-"   # and PREVIEW_PREFIX for other file names
written = []
try:
    for name, (eye, target, lens) in VIEWS.items():
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = lens
        for nb in NEIGHBOURS:
            nb.hide_render = name != "context"
        scene.render.filepath = PREV + PREFIX + name + ".png"
        bpy.ops.render.render(write_still=True)
        written.append(scene.render.filepath)
finally:
    for i, m in enumerate(originals):
        mesh.materials[i] = m
    for m in previews:
        bpy.data.materials.remove(m)
    for name, state in render_state.items():
        if bpy.data.collections.get(name):
            bpy.data.collections[name].hide_render = state
    pcol.hide_render = True
    bg.inputs[0].default_value, bg.inputs[1].default_value = saved_bg
    scene.camera = saved["camera"] or cam
    scene.render.engine = saved["engine"]
    scene.view_settings.view_transform = saved["vt"]
    scene.view_settings.look = saved["look"]
    scene.render.resolution_x, scene.render.resolution_y = saved["rx"], saved["ry"]
    scene.render.resolution_percentage = saved["pct"]
print("previews written:", *written, sep="\n  ")
