"""
store_57_preview.py - review previews of the baked brick house with shop fronts, 57 Main St
(run after store_57_bake.py).

    exec(open(r"<project>/tools/blender/store_57_preview.py").read())

Renders with EEVEE, view transform "Standard", and every material swapped for an unlit
emission of colour x lightmap x LIGHTMAP_SCALE - the same maths as the web page's
`baked-lighting` component (MeshBasicMaterial: map x color x lightMap x intensity), so
the pictures match what the headset shows. The colour tints (glTF baseColorFactor) are
included. Writes assets/models/previews/store-57-*.png (1280 px wide). The camera, engine,
view transform, resolution and the building's own materials are restored.
The NE, SE and context views add the built neighbours with their own lightmaps (same unlit
maths): the County Hotel to the north, the Wurts Law Office to the south. No photo shows the
1921 shop fronts (the c. 1906-10 Stryker plate shows the earlier jeweller's front), so there
is no "match" view.
"""

import bpy
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews" + "\\"
LIGHTMAP = PROJECT + r"\assets\textures\store-57-lightmap.jpg"
# neighbour -> (GLB, its lightmap, its LIGHTMAP_SCALE from index.html, offset of its local frame
# in this one; both rotation 0 90 0: X += -84.94 - z_entity, Y += -12.40 - x_entity,
# Z += y_entity - 0.15)
NEIGHBOUR_GLBS = {
    "S57P_CountyHotel": (PROJECT + r"\assets\models\county-hotel.glb",
                         PROJECT + r"\assets\textures\county-hotel-lightmap.jpg", 1.1088, (27.13, -2.10, 0.0)),
    "S57P_Wurts": (PROJECT + r"\assets\models\wurts-law-office.glb",
                   PROJECT + r"\assets\textures\wurts-law-office-lightmap.jpg", 1.1647, (-16.25, 2.55, -0.13)),
}

scene = bpy.context.scene
bk_obj = bpy.data.objects["Store57"]
mesh = bk_obj.data
scale = float(bk_obj.get("lightmap_scale", 1.0))

pcol = bpy.data.collections.get("S57_Preview")
if not pcol:
    pcol = bpy.data.collections.new("S57_Preview")
    scene.collection.children.link(pcol)
pcol.hide_render = False
cam_data = bpy.data.cameras.get("S57_Cam") or bpy.data.cameras.new("S57_Cam")
cam = bpy.data.objects.get("S57_Cam") or bpy.data.objects.new("S57_Cam", cam_data)
if cam.name not in pcol.objects:
    pcol.objects.link(cam)
cam_data.clip_start = 0.1
cam_data.clip_end = 600


def load_lm(path):
    img = bpy.data.images.load(path, check_existing=True)
    img.reload()
    img.colorspace_settings.name = "sRGB"          # three.js decodes it as sRGB too
    return img


lm_img = load_lm(LIGHTMAP)


def sock(socks, name):
    return next(x for x in socks if x.name == name and x.type == "RGBA")


def glass_preview(src):
    """The `glass` material: not lightmapped in the scene; plain dark tint over the
    window backs at its own alpha (the scene adds the sky reflection later)."""
    bsdf = next(n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    mat = bpy.data.materials.new("S57P_" + src.name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    emit = N("ShaderNodeEmission")
    emit.inputs["Color"].default_value = bsdf.inputs["Base Color"].default_value
    tr = N("ShaderNodeBsdfTransparent")
    mix = N("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.40
    L(tr.outputs[0], mix.inputs[1])
    L(emit.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs["Surface"])
    mat.use_backface_culling = True
    return mat


def preview_material(src, lm, lm_scale, uv_col="UVMap", uv_lm="Lightmap"):
    """Unlit copy: emission = base colour (texture x tint, or plain) x lightmap x scale."""
    if src.name.startswith("glass"):
        return glass_preview(src)
    mat = bpy.data.materials.new("S57P_" + src.name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    emit = N("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = lm_scale
    uv1 = N("ShaderNodeUVMap")
    uv1.uv_map = uv_lm
    lmn = N("ShaderNodeTexImage")
    lmn.image = lm
    L(uv1.outputs["UV"], lmn.inputs["Vector"])
    mix = N("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    bsdf = next(n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    src_tex = next((n for n in src.node_tree.nodes if n.type == "TEX_IMAGE" and n.name != "BakeTarget"), None)
    src_tint = next((n for n in src.node_tree.nodes if n.type == "MIX" and n.blend_type == "MULTIPLY"), None)
    if src_tex:
        uv0 = N("ShaderNodeUVMap")
        uv0.uv_map = uv_col
        tex = N("ShaderNodeTexImage")
        tex.image = src_tex.image
        L(uv0.outputs["UV"], tex.inputs["Vector"])
        colour = tex.outputs["Color"]
        tint = None
        if src_tint:
            tint = sock(src_tint.inputs, "B").default_value
        elif not bsdf.inputs["Base Color"].is_linked:
            tint = bsdf.inputs["Base Color"].default_value
        if tint is not None:
            t = N("ShaderNodeMix")
            t.data_type = "RGBA"
            t.blend_type = "MULTIPLY"
            t.inputs["Factor"].default_value = 1.0
            L(colour, sock(t.inputs, "A"))
            sock(t.inputs, "B").default_value = tint
            colour = sock(t.outputs, "Result")
        L(colour, sock(mix.inputs, "A"))
    else:
        sock(mix.inputs, "A").default_value = bsdf.inputs["Base Color"].default_value
    L(lmn.outputs["Color"], sock(mix.inputs, "B"))
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


# context (unlit, flat colours): the west sidewalk from the curb (local Y -5.88) to the street
# line; road, side lots and yards 0.15 lower
flat("S57P_Walk", -150, 150, -5.88, -2.10, -0.005, unlit("S57P_WalkMat", (0.36, 0.34, 0.31)))
flat("S57P_Lots", -150, 150, -150, 150, -0.15, unlit("S57P_LotMat", (0.30, 0.28, 0.22)))
NEIGHBOURS = []
for nb_name, (glb, lm_path, nb_scale, off) in NEIGHBOUR_GLBS.items():
    nb = bpy.data.objects.get(nb_name)
    if not nb:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=glb)
        new = [o for o in bpy.data.objects if o not in before]
        nb = next(o for o in new if o.type == "MESH")
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            if o is not nb:
                bpy.data.objects.remove(o, do_unlink=True)
        pcol.objects.link(nb)
        nb.name = nb_name
        nb.parent = None
        nb.location = Vector(off)
        nb.rotation_mode = "XYZ"
        nb.rotation_euler = (0, 0, 0)
        uvs = [u.name for u in nb.data.uv_layers]
        lm_nb = load_lm(lm_path)
        for i, m in enumerate(list(nb.data.materials)):
            nb.data.materials[i] = preview_material(m, lm_nb, nb_scale, uvs[0], uvs[1])
    NEIGHBOURS.append(nb)

# --- remember and change settings ----------------------------------------------------
originals = list(mesh.materials)
previews = [preview_material(m, lm_img, scale) for m in originals]
saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
render_state = {c.name: c.hide_render for c in bpy.data.collections}
for c in bpy.data.collections:
    c.hide_render = c.name not in ("Store57", "S57_Preview")
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

# name -> (eye, target, lens). Local frame: -Y = Main St (east), +X = north (County Hotel lot),
# -X = south (Wurts lawn). Scene -> local: X = -84.94 - z, Y = -12.40 - x, Z = y - 0.15. The far
# (east) sidewalk is ~21 m in front of the shop fronts; eye height 1.6-1.7 m.
VIEWS = {
    "front":          ((0.0, -24.0, 1.7), (0.0, 2.0, 4.6), 26),          # straight on, east walk
    "three-quarter":  ((14.0, -17.0, 1.7), (0.0, 3.0, 4.6), 26),         # from the NE, across Main St
    "detail":         ((0.6, -6.8, 1.6), (0.0, 0.3, 1.9), 24),           # the shop fronts
    "ne":             ((13.5, -7.5, 1.7), (2.0, 7.0, 5.0), 22),          # north wall over the hotel lot
    "se":             ((-13.0, -8.5, 1.7), (-3.0, 7.0, 4.6), 22),        # south wall over the Wurts lawn
    "context":        ((20.0, -24.0, 1.7), (2.0, 4.0, 4.2), 20),         # from the NE, both neighbours
}
VIEWS = globals().get("PREVIEW_VIEWS") or VIEWS     # set PREVIEW_VIEWS before exec() for other views
PREFIX = globals().get("PREVIEW_PREFIX") or "store-57-"
CONTEXT = ("ne", "se", "context")
written = []
try:
    for name, (eye, target, lens) in VIEWS.items():
        cam.location = eye
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = lens
        for nb in NEIGHBOURS:
            nb.hide_render = name not in CONTEXT
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
