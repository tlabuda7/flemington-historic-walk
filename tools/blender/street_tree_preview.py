"""
street_tree_preview.py - render review previews of the street tree (run after street_tree.py).

    exec(open(r"<project>/tools/blender/street_tree_preview.py").read())

Writes assets/models/previews/street-tree-base.png (lower 4 m at eye height) and
street-tree-full.png. Preview-only objects (a grey sidewalk with a hole for the pit, a
camera) live in the "StreetTree_Preview" collection, which is hidden from render again
afterwards. The hotel and its preview ground are hidden from render only while rendering;
the view transform, camera, engine and resolution are restored at the end.
"""

import math
import bpy
import bmesh
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PREV = PROJECT + r"\assets\models\previews"
X = 80.0                     # where street_tree.py parks the tree
H = 0.6 + 0.12               # half size of the pit's outer edge

scene = bpy.context.scene
pcol = bpy.data.collections.get("StreetTree_Preview")
if pcol:
    for o in list(pcol.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    pcol = bpy.data.collections.new("StreetTree_Preview")
    scene.collection.children.link(pcol)

# grey "sidewalk" at z = 0 with a square hole for the pit
bm = bmesh.new()
R = 25.0
outer = [bm.verts.new((X + x * R, y * R, 0)) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
inner = [bm.verts.new((X + x * H, y * H, 0)) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
for s in range(4):
    s2 = (s + 1) % 4
    bm.faces.new([inner[s], outer[s], outer[s2], inner[s2]])
gmesh = bpy.data.meshes.new("TreePreview_Ground")
bm.to_mesh(gmesh)
bm.free()
gmat = bpy.data.materials.get("TreePreview_Grey") or bpy.data.materials.new("TreePreview_Grey")
gmat.use_nodes = True
next(n for n in gmat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.32, 0.31, 0.29, 1)
gmesh.materials.append(gmat)
ground = bpy.data.objects.new("TreePreview_Ground", gmesh)
pcol.objects.link(ground)

cam_data = bpy.data.cameras.new("TreePreview_Cam")
cam = bpy.data.objects.new("TreePreview_Cam", cam_data)
pcol.objects.link(cam)


def aim(eye, target, lens):
    cam.location = eye
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = lens


# --- remember and change settings -------------------------------------------------
saved = dict(camera=scene.camera, engine=scene.render.engine, vt=scene.view_settings.view_transform,
             look=scene.view_settings.look, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
             pct=scene.render.resolution_percentage)
hidden = [o for o in scene.objects if o.users_collection[0].name in ("UnionHotel", "Preview") and not o.hide_render]
for o in hidden:
    o.hide_render = True
pcol.hide_render = False
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

try:
    aim((X + 3.4, -3.9, 1.6), (X, 0, 1.55), 24)
    scene.render.filepath = PREV + r"\street-tree-base.png"
    bpy.ops.render.render(write_still=True)
    aim((X + 9.5, -12.5, 1.7), (X, 0, 4.4), 30)
    scene.render.filepath = PREV + r"\street-tree-full.png"
    bpy.ops.render.render(write_still=True)
finally:
    for o in hidden:
        o.hide_render = False
    pcol.hide_render = True
    scene.camera = saved["camera"]
    scene.render.engine = saved["engine"]
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = saved["look"]
    scene.render.resolution_x, scene.render.resolution_y = saved["rx"], saved["ry"]
    scene.render.resolution_percentage = saved["pct"]
print("previews written to", PREV)
