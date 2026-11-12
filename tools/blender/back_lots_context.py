"""
back_lots_context.py - loads the placed neighbours of the back-lot buildings into the
"BL_Context" collection, at their index.html transforms (parsed from index.html, so they always
match the scene). Used by back_lots_bake.py (shadow casters, bake only, never exported) and by
the overlap check in back_lots.py.

Run inside Blender (after back_lots.py has defined PROJECT), or on its own:
    exec(open(r"<project>/tools/blender/back_lots_context.py").read())
"""

import math
import re
import bpy

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
CONTEXT = "BL_Context"
# GLBs around the back lots (Main St fronts, side-street and street-end backdrops)
CONTEXT_GLBS = ["county-hotel.glb", "store-57.glb", "palace-theatre.glb", "block-35-41.glb",
                "block-24-30.glb", "block-32-38.glb", "block-40-46.glb", "rea-building.glb",
                "bank-building.glb", "lovells-restaurant.glb", "union-hotel.glb",
                "sidestreet-bloomfield.glb", "sidestreet-southeast.glb", "street-ends.glb"]


def scene_transforms():
    """{glb file name: (position (x, y, z), rotation y degrees)} from index.html"""
    html = open(PROJECT + r"\index.html", encoding="utf8").read()
    out = {}
    for ent in re.findall(r"<a-entity\b[^>]*?>", html, re.S):
        m = re.search(r'gltf-model="url\(([^)?]*)', ent)
        if not m:
            continue
        name = m.group(1).split("/")[-1]
        pos = re.search(r'\sposition="([^"]*)"', ent)
        rot = re.search(r'\srotation="([^"]*)"', ent)
        p = [float(v) for v in (pos.group(1) if pos else "0 0 0").split()]
        r = [float(v) for v in (rot.group(1) if rot else "0 0 0").split()]
        out[name] = (tuple(p), r[1])
    return out


def load_context():
    scene = bpy.context.scene
    ctx = bpy.data.collections.get(CONTEXT)
    if not ctx:
        ctx = bpy.data.collections.new(CONTEXT)
        scene.collection.children.link(ctx)
    for o in list(ctx.objects):
        me = o.data if o.type == "MESH" else None
        bpy.data.objects.remove(o, do_unlink=True)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)
    tf = scene_transforms()
    for glb in CONTEXT_GLBS:
        (px, py, pz), rot = tf[glb]
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=PROJECT + r"\assets\models" + "\\" + glb)
        for o in [o for o in bpy.data.objects if o not in before]:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            ctx.objects.link(o)
            o.name = "CTX_" + glb[:-4]
            if o.parent is None:
                o.rotation_mode = "XYZ"
                o.location = (px, -pz, py)
                o.rotation_euler = (0, 0, math.radians(rot))
    bpy.context.view_layer.update()
    return ctx


CTX = load_context()
print("context loaded:", len(CTX.objects), "objects")
