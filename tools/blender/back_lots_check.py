"""
back_lots_check.py - overlap check of the back-lot buildings against the placed neighbours
(BL_Context, loaded by back_lots_context.py). Prints every pair of intersecting triangles whose
neighbour triangle rises above the lot ground (walls going down through the backdrops' lot
surfaces at y 0.15 are expected and ignored).

    exec(open(r"<project>/tools/blender/back_lots_check.py").read())
"""

import bmesh
import bpy
from mathutils.bvhtree import BVHTree

dg = bpy.context.evaluated_depsgraph_get()


def _bm(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)                 # works while the collection is hidden, too
    bm.transform(o.matrix_world)
    bm.faces.ensure_lookup_table()
    return bm


_ctx = []
for o in bpy.data.collections["BL_Context"].objects:
    if o.type == "MESH":
        bm = _bm(o)
        _ctx.append((o.name, bm, BVHTree.FromBMesh(bm)))
_clashes = 0
for o in bpy.data.collections["BackLots"].objects:
    if o.get("part", "").startswith("Pad"):
        continue
    bm = _bm(o)
    t = BVHTree.FromBMesh(bm)
    for name, cbm, c in _ctx:
        ov = t.overlap(c)
        real = [(i, j) for i, j in ov if min(v.co.z for v in cbm.faces[j].verts) > 0.2
                or max(v.co.z for v in bm.faces[i].verts) < 0.0]
        ground = len(ov) - len(real)
        if real:
            _clashes += len(real)
            j = real[0][1]
            print("CLASH", o.name, name, len(real), "e.g. at", tuple(round(c, 2) for c in cbm.faces[j].calc_center_median()))
        elif ov:
            print("ground only", o.name, name, ground)
    bm.free()
print("overlap check:", _clashes, "clashing triangle pairs")
