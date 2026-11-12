"""
street_tree.py - a light-weight deciduous street tree (maple/elm type) for the scene,
like the row in front of the Union Hotel in the 1920s postcards, standing in a plain
round soil pit cut into the concrete sidewalk.

Run inside Blender:
    exec(open(r"<project>/tools/blender/street_tree.py").read())

Builds the tree in the "StreetTree" collection at the origin (z = 0 is the sidewalk
surface; the scene places the tree at y = 0.15), exports assets/models/street-tree.glb,
then moves it aside (x = 80) so it does not shade the hotel bake.

Under 1,000 triangles:
- Bark: a 12-sided, slightly irregular, gently leaning trunk with a buttressed root
  flare that ends just below ground, a central leader running up into the crown, five
  curved limbs leaving between 2.8 and 5 m, and a short side branch on each limb.
  Cylinder UVs in real metres (U around, V up the wood) on bark_willow_02.
- Leaves: ~120 crossed leaf cards (leaf_cluster.png, alpha cut-out) - unchanged from
  the first version (same random sequence), normals point out from the crown centre.
- Pit: a plain round soil opening 1.2 m across (mud_forest), flush with the walk, no
  edging stones and no tree guard (PLAN.md "Street details pass 2", F8; 1908 and c. 1910
  cards). Its rim sits at z = -0.02, i.e. 5 mm above the 0.15 walk when the scene stands
  the tree at y = 0.175. (Until 2026-11-11 it was a square pit with granite edging; that
  version is kept locally as assets/models/source/street-tree-before-pits.glb.)
Vertex colours ("Col") darken bark near the ground and the inside of the crown.
Materials are plain Principled (lit in the scene, no lightmap).

Backdrop variant (for lawns and yards, e.g. the big Court St maples scaled 2.1-2.35):
    TREE_BACKDROP = True
    exec(open(r"<project>/tools/blender/street_tree.py").read())
builds the same tree WITHOUT the pit (no soil disc) and with the trunk
running on 0.3 m below ground (so it never floats on uneven lawn), in the "BackdropTree"
collection, and exports assets/models/backdrop-tree.glb. Same materials, textures, leaf cards
and bark (same random sequences); only the bottom trunk ring moves from -0.03 to -0.30 m.
"""

import math
import random
import bpy
import bmesh
from mathutils import Vector, Matrix

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
BACKDROP = bool(globals().get("TREE_BACKDROP", False))   # True: no pit, trunk sunk 0.3 m
OUT = PROJECT + (r"\assets\models\backdrop-tree.glb" if BACKDROP else r"\assets\models\street-tree.glb")
NAME = "BackdropTree" if BACKDROP else "StreetTree"
TEX = PROJECT + r"\assets\textures"
LEAF_TEX = TEX + r"\leaf_cluster.png"
BARK_TEX = TEX + r"\street-tree\bark_willow_02_q85.jpg"
# the pit only covers ~1.4 m, so its maps are 512 px (keeps the GLB under 1 MB)
SOIL_TEX = TEX + r"\street-tree\mud_forest_512_q85.jpg"
BARK_TILE, SOIL_TILE = 2.15, 2.35   # real-world size of one texture tile (m)

CANOPY_CENTRE = Vector((0, 0, 7.4))
CANOPY_RADII = Vector((3.3, 3.3, 2.9))
CARDS = 120
CARD_SIZE = 1.8

PIT = 1.2          # round soil opening, diameter (m)
PIT_SIDES = 16
SOIL_Z = -0.02     # soil rim: the scene stands the tree at y 0.175, so this is 5 mm above the 0.15 walk

col = bpy.data.collections.get(NAME)
if col:
    for o in list(col.objects):
        mesh = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if mesh and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
else:
    col = bpy.data.collections.new(NAME)
    bpy.context.scene.collection.children.link(col)


def material(name, image=None, alpha=False, roughness=0.85):
    """Principled material; colour map x vertex colour (the web multiplies COLOR_0 too)."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = roughness
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(image, check_existing=True)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(tex.outputs["Color"], mix.inputs[6])
    nt.links.new(vc.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    if alpha:
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    mat.use_backface_culling = not alpha     # bark and pit are closed/one-sided; leaf cards double-sided
    return mat


# ================================================================================
# Leaves: identical to the first version (its random sequence is replayed: the old
# script drew 10 numbers for the trunk before the cards).
# ================================================================================
rng = random.Random(1920)
for _ in range(10):
    rng.random()

bm = bmesh.new()
uv_layer = bm.loops.layers.uv.new("UVMap")
for _ in range(CARDS):
    while True:
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
        if 0.05 < d.length <= 1:
            break
    d = d.normalized() * (0.55 + 0.45 * rng.random() ** 0.5)
    pos = CANOPY_CENTRE + Vector((d.x * CANOPY_RADII.x, d.y * CANOPY_RADII.y, d.z * CANOPY_RADII.z))
    outward = (pos - CANOPY_CENTRE).normalized()
    m = (outward + Vector((rng.uniform(-.6, .6), rng.uniform(-.6, .6), rng.uniform(-.6, .6)))) \
        .normalized().to_track_quat("Z", "Y").to_matrix() @ Matrix.Rotation(rng.uniform(0, 6.283), 3, "Z")
    s = CARD_SIZE * rng.uniform(0.8, 1.15) / 2
    corners = [m @ Vector(c) * s + pos for c in ((-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0))]
    face = bm.faces.new([bm.verts.new(c) for c in corners])
    for loop, uv in zip(face.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv_layer].uv = uv
leaf_mesh = bpy.data.meshes.new(NAME + "_Leaves")
bm.to_mesh(leaf_mesh)
bm.free()
leaf_mesh.materials.append(material("Tree_Leaves", LEAF_TEX, alpha=True))

loop_normals = []
for poly in leaf_mesh.polygons:
    centre = sum((leaf_mesh.vertices[v].co for v in poly.vertices), Vector()) / poly.loop_total
    n = (centre - CANOPY_CENTRE)
    n = Vector((n.x / CANOPY_RADII.x, n.y / CANOPY_RADII.y, n.z / CANOPY_RADII.z)).normalized()
    loop_normals.extend([n] * poly.loop_total)
leaf_mesh.normals_split_custom_set(loop_normals)


# ================================================================================
# Bark
# ================================================================================
rng = random.Random(1921)
bm = bmesh.new()
buv = bm.loops.layers.uv.new("UVMap")


def frames(points):
    """Tangents and parallel-transported normals along a polyline."""
    tans = []
    for i in range(len(points)):
        a = points[max(0, i - 1)]
        b = points[min(len(points) - 1, i + 1)]
        tans.append((b - a).normalized())
    n = tans[0].orthogonal().normalized()
    norms = [n]
    for i in range(1, len(tans)):
        q = tans[i - 1].rotation_difference(tans[i])
        n = (q @ norms[-1]).normalized()
        norms.append(n)
    return tans, norms


def tube(points, radii, sides, noise=0.0, shape=None, v0=0.0):
    """Closed-top tube along `points`. shape(ring_index, angle) -> radius factor.
    UVs: U around (metres of circumference / tile), V along the length (metres / tile)."""
    tans, norms = frames(points)
    rings, ring_u = [], []
    for i, (p, r) in enumerate(zip(points, radii)):
        t, n = tans[i], norms[i]
        b = t.cross(n)
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            f = 1.0 + rng.uniform(-noise, noise)
            if shape:
                f *= shape(i, a)
            ring.append(bm.verts.new(p + (n * math.cos(a) + b * math.sin(a)) * r * f))
        rings.append(ring)
        ring_u.append(2 * math.pi * r / BARK_TILE)
    vs = [v0]
    for i in range(1, len(points)):
        vs.append(vs[-1] + (points[i] - points[i - 1]).length / BARK_TILE)
    for i in range(len(rings) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            f = bm.faces.new([rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]])
            uvs = ((ring_u[i] * k / sides, vs[i]), (ring_u[i] * (k + 1) / sides, vs[i]),
                   (ring_u[i + 1] * (k + 1) / sides, vs[i + 1]), (ring_u[i + 1] * k / sides, vs[i + 1]))
            for loop, uv in zip(f.loops, uvs):
                loop[buv].uv = uv
    cap = bm.faces.new(rings[-1])
    for loop in cap.loops:
        loop[buv].uv = (0.0, vs[-1])
    return rings


# --- trunk + central leader ------------------------------------------------------
lean_dir = Vector((0.8, 0.6, 0)).normalized()
sway_dir = Vector((-lean_dir.y, lean_dir.x, 0))


def axis(z):
    """Trunk centre line: a gentle lean that curves back a little higher up."""
    zz = max(0.0, z)
    return Vector((0, 0, z)) + lean_dir * (0.16 * (zz / 4.0) ** 1.4) \
        + sway_dir * (0.08 * math.sin(zz / 7.6 * math.pi))


def trunk_r(z):
    """Base radius of the trunk (0.185 m at chest height, ~0.37 m diameter)."""
    table = ((0.0, 0.195), (1.3, 0.185), (2.8, 0.165), (4.0, 0.135), (5.4, 0.095), (6.6, 0.06), (7.6, 0.03))
    for (z0, r0), (z1, r1) in zip(table, table[1:]):
        if z <= z1:
            t = max(0.0, (z - z0) / (z1 - z0))
            return r0 + (r1 - r0) * t
    return table[-1][1]


TRUNK_Z = (-0.30 if BACKDROP else -0.03, 0.08, 0.20, 0.45, 1.3, 2.4, 3.4, 4.4, 5.4, 6.5, 7.6)
FLARE = (1.70, 1.40, 1.16, 1.0)          # radius factor of the bottom rings
BUTTRESS = (0.36, 0.26, 0.10, 0.0)       # buttress bulge strength of the bottom rings
butt_angles = [i * 2 * math.pi / 5 + rng.uniform(-0.35, 0.35) for i in range(5)]
butt_size = [rng.uniform(0.7, 1.0) for _ in range(5)]


def trunk_shape(i, a):
    if i >= len(FLARE):
        return 1.0
    lobe = 0.0
    for ba, bs in zip(butt_angles, butt_size):
        d = math.atan2(math.sin(a - ba), math.cos(a - ba))
        lobe += bs * math.exp(-(d / 0.42) ** 2)
    return FLARE[i] * (1.0 + BUTTRESS[i] * (min(lobe, 1.2) - 0.35))


tube([axis(z) for z in TRUNK_Z], [trunk_r(z) for z in TRUNK_Z], 12, noise=0.05, shape=trunk_shape)


# --- limbs ------------------------------------------------------------------------
def bezier(a, c, b, t):
    return a * (1 - t) ** 2 + c * 2 * t * (1 - t) + b * t * t


def crown_norm(p):
    rel = p - CANOPY_CENTRE
    return Vector((rel.x / CANOPY_RADII.x, rel.y / CANOPY_RADII.y, rel.z / CANOPY_RADII.z)).length


def into_crown(p, limit):
    """Pull a tip toward the crown centre until it is well inside the leaves."""
    while crown_norm(p) > limit:
        p = CANOPY_CENTRE + (p - CANOPY_CENTRE) * 0.97
    return p


LIMBS = (  # (height, tip distance out, tip height)
    (2.85, 2.25, 6.3),
    (3.35, 2.05, 6.8),
    (3.85, 1.85, 7.2),
    (4.40, 1.60, 7.7),
    (4.95, 1.30, 8.2),
)
az0 = rng.uniform(0, 2 * math.pi)
for i, (h, out, tz) in enumerate(LIMBS):
    az = az0 + i * math.radians(137.5) + rng.uniform(-0.25, 0.25)
    d = Vector((math.cos(az), math.sin(az), 0))
    start = axis(h)
    tip = into_crown(Vector((d.x * out, d.y * out, tz)) + Vector((0, 0, 0)), 0.78)
    rise = tip.z - start.z
    ctrl = start + d * (0.55 * out) + Vector((0, 0, 0.30 * rise))
    ts = (0.0, 0.38, 0.70, 1.0)
    pts = [bezier(start, ctrl, tip, t) for t in ts]
    r0 = trunk_r(h) * 0.58
    radii = [r0, r0 * 0.68, r0 * 0.45, 0.022]
    tube(pts, radii, 7, noise=0.04, v0=rng.random())

    # one short side branch from the outer half of the limb
    p = bezier(start, ctrl, tip, 0.55)
    tdir = (bezier(start, ctrl, tip, 0.6) - bezier(start, ctrl, tip, 0.5)).normalized()
    side = 1 if i % 2 else -1
    bdir = (Matrix.Rotation(side * math.radians(rng.uniform(40, 60)), 3, "Z") @ tdir
            + Vector((0, 0, 0.6))).normalized()
    btip = into_crown(p + bdir * rng.uniform(1.1, 1.4), 0.80)
    bmid = p + (btip - p) * 0.5 + Vector((0, 0, 0.12))
    br = r0 * 0.45
    tube([p - tdir * 0.05, bmid, btip], [br, br * 0.6, 0.014], 5, noise=0.03, v0=rng.random())

bark_mesh = bpy.data.meshes.new(NAME + "_Bark")
bm.to_mesh(bark_mesh)
bm.free()
for p in bark_mesh.polygons:
    p.use_smooth = True
bark_mesh.materials.append(material("Tree_Bark", BARK_TEX, roughness=0.9))


# ================================================================================
# Tree pit: a plain round soil opening, flush with the walk, no edging (PLAN.md "Street
# details pass 2", F8: the 1908 "north from hotel" and c. 1910 courthouse cards show dark
# round soil pits about 1.2 m across cut straight into the concrete, no stones, no guards).
# ================================================================================
bm = bmesh.new()
puv = bm.loops.layers.uv.new("UVMap")
h = PIT / 2

# the outline wanders a little (+-3 %) so it reads as a hand-cut opening, not a stamped disc
rim_f = [1.0 + rng.uniform(-0.03, 0.03) for _ in range(PIT_SIDES)]
centre = bm.verts.new((0, 0, SOIL_Z + 0.012))
rings = []
for rf, hump in ((0.45, 0.008), (1.0, 0.0)):        # inner ring mounded toward the trunk, rim flat
    ring = []
    for k in range(PIT_SIDES):
        a = 2 * math.pi * k / PIT_SIDES
        r = h * rf * (rim_f[k] if rf == 1.0 else 1.0)
        z = SOIL_Z + hump + (0.0 if rf == 1.0 else rng.uniform(-0.003, 0.003))
        ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
    rings.append(ring)
for k in range(PIT_SIDES):
    k2 = (k + 1) % PIT_SIDES
    bm.faces.new([centre, rings[0][k], rings[0][k2]])
    bm.faces.new([rings[0][k], rings[1][k], rings[1][k2], rings[0][k2]])
for f in bm.faces:
    f.material_index = 0
    for loop in f.loops:
        co = loop.vert.co
        loop[puv].uv = (co.x / SOIL_TILE + 0.3, co.y / SOIL_TILE + 0.2)
bm.normal_update()
for f in bm.faces:                                   # every face up
    if f.normal.z < 0:
        f.normal_flip()
pit_mesh = bpy.data.meshes.new(NAME + "_Pit")
bm.to_mesh(pit_mesh)
bm.free()
pit_mesh.materials.append(material("Tree_Soil", SOIL_TEX, roughness=1.0))


# ================================================================================
# Vertex colours: cheap ambient occlusion
# ================================================================================
def paint(mesh, fn):
    attr = mesh.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            attr.data[li].color = fn(co, poly)
    mesh.color_attributes.active_color = attr


def leaf_col(co, poly):
    rel = co - CANOPY_CENTRE
    depth = Vector((rel.x / CANOPY_RADII.x, rel.y / CANOPY_RADII.y, rel.z / CANOPY_RADII.z)).length
    under = max(0.0, -rel.z / CANOPY_RADII.z)
    v = max(0.3, min(1.0, 0.55 + 0.45 * min(1.0, depth) - 0.25 * under))
    return (v, v, v, 1.0)


def bark_col(co, poly):
    # mid grey-brown: darker at the foot, lighter up the trunk, a touch darker inside the crown
    v = 0.40 + 0.22 * min(1.0, max(0.0, co.z) / 3.5)
    v *= 0.78 + 0.22 * min(1.0, max(0.0, co.z) / 0.35)
    return (v * 0.96, v * 0.97, v, 1.0)


def pit_col(co, poly):
    # soil: dark and damp-looking, a little darker at the rim where it meets the concrete
    edge = (co.x * co.x + co.y * co.y) ** 0.5 / h
    v = 0.80 - 0.22 * max(0.0, edge - 0.6) / 0.4
    return (v, v * 0.97, v * 0.94, 1.0)


paint(leaf_mesh, leaf_col)
paint(bark_mesh, bark_col)
paint(pit_mesh, pit_col)

bark = bpy.data.objects.new(NAME + "_Bark", bark_mesh)
leaves = bpy.data.objects.new(NAME + "_Leaves", leaf_mesh)
if BACKDROP:            # no tree pit: drop the soil disc
    bpy.data.meshes.remove(pit_mesh)
    TREE = (bark, leaves)
else:
    pit = bpy.data.objects.new(NAME + "_Pit", pit_mesh)
    TREE = (bark, leaves, pit)
for o in TREE:
    col.objects.link(o)

# --- export, then move aside ------------------------------------------------------
for o in bpy.context.scene.objects:
    o.select_set(o in TREE)
vc_modes = [i.identifier for i in bpy.ops.export_scene.gltf.get_rna_type().properties["export_vertex_color"].enum_items]
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_yup=True,
                          export_vertex_color="ACTIVE" if "ACTIVE" in vc_modes else vc_modes[0])
for o in TREE:
    o.location.x = 80
tris = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in TREE}
print(NAME, "exported:", OUT, "|", sum(tris.values()), "triangles", tris)
