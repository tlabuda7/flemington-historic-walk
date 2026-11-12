"""
old_maple_preview.py - review previews of the old-maple variant of the street tree (run after
street_tree.py with TREE_OLD = True, which parks the tree at x = 80).

    exec(open(r"<project>/tools/blender/old_maple_preview.py").read())

Writes assets/models/previews/old-maple.png (the whole tree from across the street, eye
height) and old-maple-vs-figure.png (the tree beside a 1.75 m reference box = a person and a
plain 2-storey wall 7 m tall, for scale). EEVEE, view transform "Standard", late-afternoon sun
(CLAUDE.md east-side "to sun" vector) and the sky colour; the trees are lit in the scene, so
their own Principled materials are used. Preview-only objects live in "OldMaple_Preview",
hidden from render again afterwards; every other collection is hidden while rendering; camera,
engine, view transform and resolution are restored.
"""

import bpy
import bmesh
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews"
X = 80.0                     # where street_tree.py parks the tree

scene = bpy.context.scene
pcol = bpy.data.collections.get("OldMaple_Preview")
if pcol:
    for o in list(pcol.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    pcol = bpy.data.collections.new("OldMaple_Preview")
    scene.collection.children.link(pcol)


def plain(name, rgb, rough=0.9):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


def box(name, x0, x1, y0, y1, z0, z1, mat):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0),
                       (z0 + z1) / 2 + v.co.z * (z1 - z0)))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    pcol.objects.link(o)
    return o


# grass strip / lawn round the tree, 0.15 below a pale walk in front; the tree origin is the ground
box("OMP_Lawn", X - 40, X + 40, -3.0, 40, -0.30, 0.0, plain("OMP_Grass", (0.10, 0.16, 0.05)))
box("OMP_Walk", X - 40, X + 40, -6.5, -3.0, -0.30, 0.0, plain("OMP_Concrete", (0.36, 0.35, 0.32)))
box("OMP_Road", X - 40, X + 40, -40, -6.5, -0.45, -0.15, plain("OMP_Earth", (0.28, 0.24, 0.19)))
# scale references: a 1.75 m person-sized box 2.5 m in front-right of the trunk; a plain
# 2-storey wall 7 m tall, 9 m wide, 7 m to the right of the tree (front at the tree's line)
box("OMP_Figure", X + 2.3, X + 2.75, -2.7, -2.4, 0.0, 1.75, plain("OMP_Red", (0.45, 0.05, 0.04)))
box("OMP_Wall", X + 7.5, X + 16.5, 0.0, 10.0, 0.0, 7.0, plain("OMP_Brick", (0.30, 0.12, 0.08)))
box("OMP_WallBand", X + 7.45, X + 16.55, -0.05, 0.0, 3.40, 3.55, plain("OMP_Band", (0.55, 0.52, 0.46)))

if not any(o.type == "LIGHT" and o.data.type == "SUN" and o.users_collection[0].name == "OldMaple_Preview"
           for o in scene.objects):
    sun_data = bpy.data.lights.get("OMP_Sun") or bpy.data.lights.new("OMP_Sun", "SUN")
    sun_data.energy = 3.5
    sun_data.color = (1.0, 0.92, 0.80)
    sun = bpy.data.objects.new("OMP_Sun", sun_data)
    sun.rotation_euler = (-Vector((0.40, -0.90, 0.36))).to_track_quat("-Z", "Y").to_euler()
    pcol.objects.link(sun)
if scene.world is None:
    scene.world = bpy.data.worlds.new("OMP_World")
scene.world.use_nodes = True
bg = next((n for n in scene.world.node_tree.nodes if n.type == "BACKGROUND"), None)
if bg:
    bg.inputs[0].default_value = (0.42, 0.55, 0.78, 1)
    bg.inputs[1].default_value = 0.9

cam_data = bpy.data.cameras.new("OMP_Cam")
cam = bpy.data.objects.new("OMP_Cam", cam_data)
pcol.objects.link(cam)


def aim(eye, target, lens):
    cam.location = eye
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = lens


saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
render_state = {c.name: c.hide_render for c in bpy.data.collections}
for c in bpy.data.collections:
    c.hide_render = c.name not in ("OldMaple", "OldMaple_Preview")
loose = {o.name: o.hide_render for o in scene.collection.objects}
for o in scene.collection.objects:
    o.hide_render = True
scene.camera = cam
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = eng
        break
    except TypeError:
        pass
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.resolution_percentage = 100

written = []
try:
    # the whole tree from the far side of the street, eye height
    scene.render.resolution_x, scene.render.resolution_y = 1280, 1280
    aim((X - 6.0, -26.0, 1.6), (X, 0.0, 8.6), 26)
    scene.render.filepath = PREV + r"\old-maple.png"
    bpy.ops.render.render(write_still=True)
    written.append(scene.render.filepath)
    # beside the person box and the 2-storey wall
    scene.render.resolution_x, scene.render.resolution_y = 1280, 960
    aim((X + 4.0, -32.0, 1.6), (X + 4.5, 0.0, 8.0), 26)
    scene.render.filepath = PREV + r"\old-maple-vs-figure.png"
    bpy.ops.render.render(write_still=True)
    written.append(scene.render.filepath)
finally:
    for name, state in render_state.items():
        if bpy.data.collections.get(name):
            bpy.data.collections[name].hide_render = state
    for name, state in loose.items():
        if bpy.data.objects.get(name):
            bpy.data.objects[name].hide_render = state
    pcol.hide_render = True
    pcol.hide_viewport = True
    scene.camera = saved["camera"]
    scene.render.engine = saved["engine"]
    scene.view_settings.view_transform = saved["vt"]
    scene.view_settings.look = saved["look"]
    scene.render.resolution_x, scene.render.resolution_y = saved["rx"], saved["ry"]
    scene.render.resolution_percentage = saved["pct"]
print("previews written:", *written, sep="\n  ")
