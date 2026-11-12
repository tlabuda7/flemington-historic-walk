"""
block_83_87.py - builds 83-87 Main St, Flemington (west side, old nos. 507-506): the 3-storey
red-brick Italianate grocery ("Gro.", 32 ft) with a bracketed cornice and a segmental roof arch
in the middle of the front, two segment-headed windows per upper floor with hood moulds and
closed green louvred shutters, and a 1-storey flat-roofed porch over the whole sidewalk on
five thin posts at the curb (PLAN.md "83-87 Main St: brick grocery ... with roof arch and
sidewalk porch"; evidence: Goodspeed card "Main Street looking S.", c. 1905-12, and the 1910 /
1921 Sanborn maps). Owner decisions 2026-11-12: the card is the 1920 look; shutters closed; no
goods under the porch; no signs or lettering.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/block_83_87.py").read())

Every run deletes and rebuilds the "Block8387" collection. Materials, lightmap bake and GLB
export: block_83_87_bake.py (runs this file first). Pattern: store_106.py (one bmesh per part,
a material index per face, closed shells cut by nested boolean pockets whose faces keep the
cutter's material index).

Windows (PLAN.md "E. Windows that don't read as flat black"): the show windows, the shop-door
lights and the transoms are ONE glass face (material `glass`) 4 cm in front of a window back
with atlas UVs into assets/textures/block-35-41/grocery_interior.jpg (the grocery atlas made for
35-41, reused). The upper windows are filled by closed shutters (no glass behind them).
Shutter leaves: assets/textures/block-83-87/shutter_louvres.jpg (tools/prepare_block_83_87_textures.py).

Coordinates (metres, Blender Z-up), origin = scene (-4.58, 0.15, 23.11) = centre of the porch
front at walk level, rotation 0 90 0:
    X  along the street, +X = north (79 Main, alley), -X = south (91-93's yard)
    Y  depth: y = 0 is the porch front (fascia face, at the curb); front wall 4.09
    Z  up from the sidewalk top; walls skirt down to -0.20
Scene -> local: X = 23.11 - z, Y = -4.58 - x.
"""

import json
import math
import bpy
import bmesh
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md massing table and elevation details)
# ---------------------------------------------------------------------------
HW = 3.31               # half width of the front block (6.62)
YW = 4.09               # front wall (map: 0.62 behind the street line)
YA = 12.22              # rear of the front block A
SKIRT = -0.20
TOPA = 9.45             # roof (flat tin) of block A behind the cornice
FRZ = (8.85, 9.30)      # frieze
CT = 9.75               # cornice top (map 32 ft)
CPROJ = 0.55            # cornice projection
ARCH_SPAN, ARCH_TOP = 3.0, 10.35
PIER = 0.35             # corner pilasters
WIN_X = (-1.85, 1.85)
WIN2 = (4.35, 6.10)     # 2nd floor opening: sill, crown of the segmental head
WIN3 = (6.95, 8.55)
WIN_W = 0.90
WIN_RISE = 0.20         # rise of the segmental heads
POST_X = (-3.20, -1.60, 0.0, 1.60, 3.20)
POST = 0.12
POST_Y = 0.09           # post centre line (spec 0.07; 2 cm back so the fascia face stays at y 0)
FASCIA = (3.25, 3.60)   # porch fascia at the front (scallops hang 0.10 lower)
PR_FRONT, PR_WALL = 3.67, 4.00   # porch roof top at the front edge and at the wall
PR_T = 0.07             # porch roof thickness
SF_D = 0.12             # shop front set back behind the brick face
YS = YW + SF_D

# rear parts (map; heights GUESS)
A2 = (-6.17, -3.31, 7.81, 10.94, 9.40)          # south brick piece, 3 storeys
A3 = (-6.17, -3.31, 6.20, 7.81, 3.40, 3.00)     # frame piece, 1 storey shed (high at the rear)
B = (-5.71, 2.53, YA, 21.26)                    # rear block, brick 2 1/2
B_EAVE, B_RIDGE = 6.40, 8.40
B_SOUTH = (-8.21, -5.71, 16.30, 21.26)          # its south extension (lean-to, GUESS)
B2 = (2.53, HW, YA, 16.40, 3.60)                # north 1-storey brick piece
C_Y = (21.26, 23.81)                            # rear frame strips
C2 = (-1.90, 2.53, 6.00, 5.60)                  # "2" part: shed high / low
C1 = (-8.21, -1.90, 3.40, 3.00)                 # "1" part

BRICK, TRIMB, SHUT, PTRIM, ROOF, SHOP, CLAP, GLASS, GROC = range(9)
NAMES = ["Brick", "TrimBrown", "Shutters", "PorchTrim", "Roof", "Shopfront", "Clapboard", "Glass", "Grocery"]
COLOURS = ["#9A5038", "#5A4332", "#5F7F62", "#D8D6CC", "#4F6A4A", "#22291F", "#8C846E", "#1A1916", "#2E2822"]


# ---------------------------------------------------------------------------
# Materials (plain stand-ins; block_83_87_bake.py swaps in the textures)
# ---------------------------------------------------------------------------
def _hex(h):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, 1.0)


def plain(name, color, rough=0.8):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Base Color"].default_value = _hex(color)
    bsdf.inputs["Roughness"].default_value = rough
    mat.diffuse_color = _hex(color)
    return mat


MATS = [plain("GB_" + n, c) for n, c in zip(NAMES, COLOURS)]


# ---------------------------------------------------------------------------
# Mesh builder (as store_106.py) + sweeps for mouldings
# ---------------------------------------------------------------------------
class MB:
    def __init__(self):
        self.bm = bmesh.new()

    @staticmethod
    def _pt(axis, u, d, v):
        # 'y': outline in X-Z, depth along Y; 'x': outline in Y-Z, depth along X;
        # 'z': plan outline in X-Y, depth along Z
        if axis == "y":
            return (u, d, v)
        if axis == "x":
            return (d, u, v)
        return (u, v, d)

    def prism(self, pts, d0, d1, axis="y", mi=TRIMB):
        """Extrude a 2D outline between depths d0 and d1. mi: one index, or (cap at d0, cap at
        d1, sides) where sides is an index or a list with one index per outline edge."""
        bm = self.bm
        if isinstance(mi, int):
            m0 = m1 = mi
            ms = [mi] * len(pts)
        else:
            m0, m1, ms = mi
            ms = ms if isinstance(ms, (list, tuple)) else [ms] * len(pts)
        a = [bm.verts.new(self._pt(axis, u, d0, v)) for u, v in pts]
        b = [bm.verts.new(self._pt(axis, u, d1, v)) for u, v in pts]
        fa = bm.faces.new(a)
        fa.material_index = m0
        fb = bm.faces.new(list(reversed(b)))
        fb.material_index = m1
        faces = [fa, fb]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new([a[i], a[j], b[j], b[i]])
            f.material_index = ms[i]
            faces.append(f)
        bmesh.ops.recalc_face_normals(bm, faces=faces)
        return faces

    def rings(self, rings, mi, cap=True):
        """Closed tube through a list of rings (lists of co-ordinates, same length, each ring a
        closed outline); end caps on both ends. Returns the faces."""
        bm = self.bm
        vs = [[bm.verts.new(c) for c in r] for r in rings]
        faces = []
        n = len(rings[0])
        for a, b in zip(vs[:-1], vs[1:]):
            for i in range(n):
                j = (i + 1) % n
                faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
        if cap:
            faces.append(bm.faces.new(vs[0]))
            faces.append(bm.faces.new(list(reversed(vs[-1]))))
        for f in faces:
            f.material_index = mi
        bmesh.ops.recalc_face_normals(bm, faces=faces)
        return faces

    def face(self, pts, d, axis, out, mi=GLASS):
        """One flat face (a glass pane) with its normal pointing out (+-axis)."""
        f = self.bm.faces.new([self.bm.verts.new(self._pt(axis, u, d, v)) for u, v in pts])
        f.material_index = mi
        f.normal_update()
        want = Vector((0, out, 0)) if axis == "y" else Vector((out, 0, 0))
        if f.normal.dot(want) < 0:
            f.normal_flip()
        return f

    def box(self, x0, x1, y0, y1, z0, z1, mi=TRIMB):
        return self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, "y", mi)

    def to_object(self, name, col):
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        for m in MATS:
            mesh.materials.append(m)
        obj = bpy.data.objects.new(name, mesh)
        col.objects.link(obj)
        return obj


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def sweep_plan(B_, path, profile, mi):
    """Moulding swept along a plan polyline (mitred corners). profile: (d, z) with d = distance
    out from the path (outward = right of travel), closed outline."""
    def outn(p, q):
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy)
        return (dy / L, -dx / L)
    rings = []
    for i, p in enumerate(path):
        ns = []
        if i > 0:
            ns.append(outn(path[i - 1], p))
        if i < len(path) - 1:
            ns.append(outn(p, path[i + 1]))
        if len(ns) == 1:
            m = ns[0]
        else:
            a, b = ns
            k = 1 + a[0] * b[0] + a[1] * b[1]
            m = ((a[0] + b[0]) / k, (a[1] + b[1]) / k)
        rings.append([(p[0] + m[0] * d, p[1] + m[1] * d, z) for d, z in profile])
    return B_.rings(rings, mi)


def seg_arc(cu, w, z_spring, rise, n, grow=0.0):
    """Points of a segmental arc over a chord w (springing z_spring, given rise), concentric
    arc grown radially by `grow`, from left to right. Returns pts, centre z, radius."""
    c = w / 2
    R = (c * c + rise * rise) / (2 * rise)
    zc = z_spring + rise - R
    t0 = math.asin(c / R)
    Rg = R + grow
    pts = [(cu + Rg * math.sin(-t0 + 2 * t0 * i / n), zc + Rg * math.cos(-t0 + 2 * t0 * i / n)) for i in range(n + 1)]
    return pts, zc, R


def circle_z(cu, zc, R, x):
    return zc + math.sqrt(max(0.0, R * R - (x - cu) ** 2))


# ---------------------------------------------------------------------------
# Scene setup
# ---------------------------------------------------------------------------
def fresh_collection(name):
    col = bpy.data.collections.get(name)
    if col:
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    for mesh in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(mesh)
    return col


col = fresh_collection("Block8387")
P = MB()                        # all added parts
MAIN, CUT_M = MB(), MB()        # front block A: one closed brick shell, cut by the openings
REARS = MB()                    # rear masses (closed shells, no openings)

FRONT = ("y", YW, -1)
SHOPF = ("y", YS, -1)


def Dfun(wall):
    axis, face, out = wall
    return axis, (lambda k: face + out * k)   # k > 0 outside the wall face, k < 0 inside


def wbox(wall, u0, u1, k0, k1, z0, z1, mi=TRIMB):
    axis, D = Dfun(wall)
    P.prism(rect(u0, u1, z0, z1), D(k0), D(k1), axis, mi)


def wprism(wall, pts, k0, k1, mi=TRIMB):
    axis, D = Dfun(wall)
    return P.prism(pts, D(k0), D(k1), axis, mi)


# ---------------------------------------------------------------------------
# Window backs (grocery atlas) and glass
# ---------------------------------------------------------------------------
GI = json.load(open(PROJECT + r"\assets\textures\block-35-41\grocery_interior.json"))["cells"]
GI_UV = {k: v["uv"] for k, v in GI.items()}
U0_, V0_, U1_, V1_ = GI_UV["shop"]
GI_UV["shop_top"] = [U0_, V0_ + (V1_ - V0_) * 0.70, U1_, V1_]   # transoms: the top of the shop view
GAP = 0.04
BACKS = []             # (axis, plane, out, u0, u1, z0, z1, uv rect)


def cell_uv(cell, aspect=None):
    """Atlas rectangle of a cell, cropped (centred) to `aspect` (w/h) so the room is not
    stretched. 1.5 px inset against bleeding from the neighbour."""
    U0, V0, U1, V1 = GI_UV[cell]
    e = 1.5 / 1024
    U0, V0, U1, V1 = U0 + e, V0 + e, U1 - e, V1 - e
    if aspect:
        a = (U1 - U0) / (V1 - V0)
        if aspect < a:
            w, c = (U1 - U0) * aspect / a, (U0 + U1) / 2
            U0, U1 = c - w / 2, c + w / 2
        else:
            h, c = (V1 - V0) * a / aspect, (V0 + V1) / 2
            V0, V1 = c - h / 2, c + h / 2
    return U0, V0, U1, V1


def register_back(wall, outline, d_back, cell, frame=None):
    axis, face, out = wall
    us, vs = [p[0] for p in outline], [p[1] for p in outline]
    u0, u1, z0, z1 = min(us), max(us), min(vs), max(vs)
    fu0, fu1, fz0, fz1 = frame or (u0, u1, z0, z1)
    U0, V0, U1, V1 = cell_uv(cell, (fu1 - fu0) / (fz1 - fz0))
    su = lambda u: U0 + (U1 - U0) * (u - fu0) / (fu1 - fu0)
    sv = lambda z: V0 + (V1 - V0) * (z - fz0) / (fz1 - fz0)
    BACKS.append((axis, face - out * d_back, out, u0, u1, z0, z1, (su(u0), sv(z0), su(u1), sv(z1))))


def pane(C, wall, outline, d_glass, cell, side_mat, frame=None):
    """One pane: a pocket (sides `side_mat`, back = grocery view GAP behind the glass) cut by
    cutter C, and one glass face."""
    axis, D = Dfun(wall)
    C.prism(outline, D(0.25), D(-d_glass - GAP), axis, mi=(side_mat, GROC, side_mat))
    register_back(wall, outline, d_glass + GAP, cell, frame)
    P.face(outline, D(-d_glass), axis, wall[2])


def assign_atlas_uvs(obj):
    me = obj.data
    uvl = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    missed = 0
    for p in me.polygons:
        if p.material_index != GROC:
            continue
        c, n = p.center, p.normal
        hit = None
        for b in BACKS:
            axis, plane, out, u0, u1, z0, z1, uv = b
            k = 1 if axis == "y" else 0
            cu = c.x if axis == "y" else c.y
            if n[k] * out > 0.9 and abs(c[k] - plane) < 0.003 and u0 - 1e-3 <= cu <= u1 + 1e-3 \
                    and z0 - 1e-3 <= c.z <= z1 + 1e-3:
                hit = b
                break
        if hit is None:
            missed += 1
            continue
        axis, plane, out, u0, u1, z0, z1, (U0, V0, U1, V1) = hit
        flip = (axis == "y" and out > 0) or (axis == "x" and out < 0)
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            t = ((co.x if axis == "y" else co.y) - u0) / (u1 - u0)
            t = 1 - t if flip else t
            s = (co.z - z0) / (z1 - z0)
            uvl.data[li].uv = (U0 + (U1 - U0) * t, V0 + (V1 - V0) * s)
    if missed:
        print("WARNING:", missed, "grocery faces of", obj.name, "found no atlas cell")


# shutter leaves: front face -> the whole louvre image; edges -> a plain stile pixel
LEAVES = []            # (u0, u1, z0, z1, y_front) of each leaf front
STILE_UV = (0.05, 0.30)


def assign_shutter_uvs(obj):
    me = obj.data
    uvl = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        if p.material_index != SHUT:
            continue
        c, n = p.center, p.normal
        hit = None
        if n.y < -0.9:
            hit = next((s for s in LEAVES if s[0] - 1e-3 <= c.x <= s[1] + 1e-3 and s[2] - 1e-3 <= c.z <= s[3] + 1e-3
                        and abs(c.y - s[4]) < 0.003), None)
        for li in p.loop_indices:
            if hit:
                co = me.vertices[me.loops[li].vertex_index].co
                uvl.data[li].uv = ((co.x - hit[0]) / (hit[1] - hit[0]), (co.z - hit[2]) / (hit[3] - hit[2]))
            else:
                uvl.data[li].uv = STILE_UV


# ---------------------------------------------------------------------------
# A. Front block: closed brick shell, flat roof at 9.45 (behind the cornice)
# ---------------------------------------------------------------------------
MAIN.prism([(-HW, YW), (HW, YW), (HW, YA), (-HW, YA)], SKIRT, TOPA, axis="z",
           mi=(BRICK, ROOF, BRICK))

# ---------------------------------------------------------------------------
# Upper windows (card): two per floor at X +-1.85, segmental heads, moulded hood moulds with
# dropped label ends, sills on two small brackets, closed louvred shutters 0.10 back
# ---------------------------------------------------------------------------
ARC_N = 8


def upper_window(cu, z0, z1):
    zs = z1 - WIN_RISE
    arc, zc, R = seg_arc(cu, WIN_W, zs, WIN_RISE, ARC_N)
    # opening: right jamb up, arc right->left, left jamb down
    outline = [(cu - WIN_W / 2, z0), (cu + WIN_W / 2, z0)] + arc[::-1]
    axis, D = Dfun(FRONT)
    CUT_M.prism(outline, D(0.25), D(-0.30), axis, mi=(BRICK, SHOP, BRICK))   # reveal 0.30 deep
    # two closed louvred shutter leaves, 0.10 back, 0.035 thick, split at the centre
    g = 0.006
    za = lambda x: circle_z(cu, zc, R, x) - g               # leaf top under the arc
    L, Rj = cu - WIN_W / 2 + g, cu + WIN_W / 2 - g
    inner = [(x, z - g) for x, z in arc[::-1]]              # arc right -> left
    for s in (-1, 1):
        if s < 0:
            pts = [(L, z0 + g), (cu - g, z0 + g), (cu - g, za(cu - g))] + \
                  [p for p in inner if L + 0.01 < p[0] < cu - g - 0.01] + [(L, za(L))]
        else:
            pts = [(cu + g, z0 + g), (Rj, z0 + g), (Rj, za(Rj))] + \
                  [p for p in inner if cu + g + 0.01 < p[0] < Rj - 0.01] + [(cu + g, za(cu + g))]
        wprism(FRONT, pts, -0.10, -0.135, mi=SHUT)
        us = [p[0] for p in pts]
        LEAVES.append((min(us), max(us), z0 + g, z1 - g, YW + 0.10))
    # frame: plain wood frame inside the reveal around the shutters (dark green-black)
    wprism(FRONT, outline, -0.135, -0.16, mi=SHOP)
    # hood mould: arched band (inner edge 0.06 above the opening, 0.13 wide) with dropped label
    # ends 0.25 long; two steps of relief (0.07 and 0.11 proud) + label stops
    gi, wd = 0.06, 0.13
    drop = 0.25
    xi, xo = WIN_W / 2 + gi, WIN_W / 2 + gi + wd
    for k0, k1, a, b in ((0.0, 0.07, 0.0, wd), (0.0, 0.11, wd * 0.45, wd)):
        ri, ro = R + gi + a, R + gi + b
        xin, xout = WIN_W / 2 + gi + a, WIN_W / 2 + gi + b
        ti, to = math.asin(min(1.0, xin / ri)), math.asin(min(1.0, xout / ro))
        inner = [(cu + ri * math.sin(-ti + 2 * ti * i / ARC_N), zc + ri * math.cos(-ti + 2 * ti * i / ARC_N))
                 for i in range(ARC_N + 1)]
        outer = [(cu + ro * math.sin(-to + 2 * to * i / ARC_N), zc + ro * math.cos(-to + 2 * to * i / ARC_N))
                 for i in range(ARC_N + 1)]
        zb = zs - drop
        pts = [(cu - xout, zb), (cu - xin, zb)] + inner + [(cu + xin, zb), (cu + xout, zb)] + outer[::-1]
        wprism(FRONT, pts, k0, k1, mi=TRIMB)
    for s in (-1, 1):                                       # label stops (small blocks)
        a, b = sorted((cu + s * (xi - 0.02), cu + s * (xo + 0.03)))
        wbox(FRONT, a, b, 0.0, 0.12, zs - drop - 0.07, zs - drop + 0.0)
    # sill 0.08 proud (stone-like, painted) on two small console brackets
    wbox(FRONT, cu - WIN_W / 2 - 0.10, cu + WIN_W / 2 + 0.10, -0.10, 0.08, z0 - 0.08, z0)
    wbox(FRONT, cu - WIN_W / 2 - 0.12, cu + WIN_W / 2 + 0.12, 0.0, 0.10, z0 - 0.105, z0 - 0.08)
    BRK = [(0.0, z0 - 0.105), (0.07, z0 - 0.105), (0.07, z0 - 0.14), (0.05, z0 - 0.19), (0.03, z0 - 0.22),
           (0.02, z0 - 0.27), (0.0, z0 - 0.27)]
    for xb in (cu - WIN_W / 2 + 0.02, cu + WIN_W / 2 - 0.02):
        axis, D = Dfun(FRONT)
        P.prism([(D(d), z) for d, z in BRK], xb - 0.035, xb + 0.035, "x", mi=TRIMB)


for x in WIN_X:
    upper_window(x, *WIN2)
    upper_window(x, *WIN3)

# ---------------------------------------------------------------------------
# Corner pilasters, frieze, bracketed cornice with returns, roof arch
# ---------------------------------------------------------------------------
for a, b in ((-HW, -HW + PIER), (HW - PIER, HW)):
    wbox(FRONT, a, b, 0.0, 0.06, SKIRT, FRZ[0], mi=BRICK)
    wbox(FRONT, a - 0.02, b + (0.0 if b == HW else 0.02), 0.0, 0.09, FRZ[0] - 0.12, FRZ[0], mi=TRIMB)  # cap
# frieze board with a bead under it; returns on both sides for 0.6 m
wbox(FRONT, -HW, HW, 0.0, 0.05, FRZ[0], FRZ[1])
wbox(FRONT, -HW - 0.01, HW + 0.01, 0.0, 0.08, FRZ[0] - 0.04, FRZ[0] + 0.03)
for s in (-1, 1):
    x0, x1 = sorted((s * HW, s * (HW + 0.05)))
    P.box(x0, x1, YW - 0.05, YW + 0.60, FRZ[0], FRZ[1])
    x0, x1 = sorted((s * HW, s * (HW + 0.08)))
    P.box(x0, x1, YW - 0.08, YW + 0.60, FRZ[0] - 0.04, FRZ[0] + 0.03)

# cornice profile (d out of the wall, z): bed moulding, soffit, fascia, cyma crown
CPROF = [(-0.15, 9.28), (0.07, 9.28), (0.07, 9.31), (0.12, 9.35), (0.47, 9.35), (0.47, 9.42),
         (0.50, 9.45), (0.50, 9.58), (0.52, 9.61), (0.55, 9.67), (0.55, 9.75), (-0.15, 9.75)]
CPATH = [(-HW, YW + 0.60), (-HW, YW), (HW, YW), (HW, YW + 0.60)]
sweep_plan(P, CPATH, CPROF, TRIMB)

# brackets: scroll consoles 0.12 wide under the soffit, 4 pairs (corners, either side of the arch)
BRACKET = [(0.0, 9.35), (0.44, 9.35), (0.44, 9.30), (0.41, 9.25), (0.36, 9.21), (0.29, 9.19),
           (0.22, 9.17), (0.16, 9.13), (0.12, 9.06), (0.11, 8.98), (0.12, 8.92), (0.10, 8.86),
           (0.06, 8.80), (0.0, 8.80)]
BRACKET_X = (-3.12, -2.84, -1.86, -1.58, 1.58, 1.86, 2.84, 3.12)
for xb in BRACKET_X:
    P.prism([(YW - d, z) for d, z in BRACKET], xb - 0.06, xb + 0.06, "x", mi=TRIMB)
for s in (-1, 1):                                          # one under each cornice return
    P.prism([(s * (HW + d), z) for d, z in BRACKET], YW + 0.30, YW + 0.42, "y", mi=TRIMB)

# roof arch: a segmental arched cornice (span 3.0, top 10.35) rising from the cornice top,
# swept along the arc with its own smaller profile; plain boarded tympanum under it
A_RISE = ARCH_TOP - CT
A_C = ARCH_SPAN / 2
A_R = (A_C ** 2 + A_RISE ** 2) / (2 * A_RISE)
A_ZC = ARCH_TOP - A_R
A_T0 = math.asin(A_C / A_R)
APROF = [(-0.30, 0.0), (0.55, 0.0), (0.55, -0.07), (0.51, -0.10), (0.48, -0.14), (0.48, -0.20),
         (0.40, -0.26), (-0.30, -0.26)]                    # (d out of the wall, radial h): crown flush
                                                           # with the cornice crown, as on the card
A_N = 14
rings = []
for i in range(A_N + 1):
    t = -A_T0 + 2 * A_T0 * i / A_N
    rings.append([(math.sin(t) * (A_R + h), YW - d, A_ZC + math.cos(t) * (A_R + h)) for d, h in APROF])
P.rings(rings, TRIMB)
# tympanum: boards between the cornice top and the arch's underside, 0.04 proud of the wall
ti = math.asin(min(1.0, (A_C - 0.05) / (A_R - 0.26)))
tym = [(math.sin(-ti + 2 * ti * i / A_N) * (A_R - 0.25), A_ZC + math.cos(-ti + 2 * ti * i / A_N) * (A_R - 0.25))
       for i in range(A_N + 1)]
tym = [(x, max(z, CT - 0.05)) for x, z in tym]
P.prism([(tym[0][0], CT - 0.05)] + tym[1:-1] + [(tym[-1][0], CT - 0.05)], YW - 0.04, YW + 0.25, "y",
        mi=TRIMB)

# coping along the side and rear walls of A (tin cap over the brick parapet line)
for x0, x1 in ((-HW - 0.04, -HW + 0.20), (HW - 0.20, HW + 0.04)):
    P.box(x0, x1, YW + 0.60, YA + 0.04, TOPA, TOPA + 0.08, mi=ROOF)
P.box(-HW - 0.04, HW + 0.04, YA - 0.20, YA + 0.04, TOPA, TOPA + 0.08, mi=ROOF)

# ---------------------------------------------------------------------------
# Ground floor shop front (GUESS behind the porch; card too dark): the whole bay between the
# corner piers is set back 0.12; two show windows on panelled bulkheads, a transom band, a
# centre pair of half-glazed doors in a 0.80 recess, a plain fascia. Dark green-black.
# ---------------------------------------------------------------------------
axis, D = Dfun(FRONT)
SFX = HW - PIER                                  # 2.96
SF_TOP = PR_WALL - PR_T                          # 3.93: under the porch roof at the wall
CUT_M.prism(rect(-SFX, SFX, SKIRT - 0.1, SF_TOP), D(0.25), D(-SF_D), axis, mi=(BRICK, SHOP, BRICK))
axis, DS = Dfun(SHOPF)
BULK, GL0, GL1 = 0.50, 0.60, 2.86
TR0, TR1 = 2.98, 3.46
for x0, x1 in ((-SFX, -0.65), (0.65, SFX)):
    a, b = x0 + 0.07, x1 - 0.07
    pane(CUT_M, SHOPF, rect(a, b, GL0, GL1), 0.06, "shop", SHOP)
    pane(CUT_M, SHOPF, rect(a, b, TR0, TR1), 0.06, "shop_top", SHOP)
    wbox(SHOPF, x0, x1, 0.0, 0.07, BULK, GL0 - 0.03)                      # sill rail
    wbox(SHOPF, x0 - 0.02, x1 + 0.02, 0.0, 0.10, GL0 - 0.04, GL0, mi=SHOP)  # sill ledge
    wbox(SHOPF, x0, x1, 0.0, 0.03, -0.02, BULK, mi=SHOP)                  # bulkhead
    xm = (x0 + x1) / 2
    for pa, pb in ((x0 + 0.10, xm - 0.04), (xm + 0.04, x1 - 0.10)):         # raised panels
        wbox(SHOPF, pa, pb, 0.03, 0.05, 0.10, BULK - 0.10, mi=SHOP)
    wbox(SHOPF, x0, x1, 0.0, 0.05, GL1, TR0, mi=SHOP)                     # transom bar
    wbox(SHOPF, x0, x1, 0.0, 0.08, GL1 + 0.02, GL1 + 0.06, mi=SHOP)       # its drip moulding
    for xt in (a + (b - a) / 3, a + 2 * (b - a) / 3):                      # transom muntins
        wbox(SHOPF, xt - 0.025, xt + 0.025, 0.0, 0.05, TR0, TR1, mi=SHOP)
    for pa, pb in ((x0, a), (b, x1)):                                      # jamb boards
        wbox(SHOPF, pa, pb, 0.0, 0.03, BULK, TR1 + 0.04, mi=SHOP)

# centre doors: recess 0.80 deep, a pair of half-glazed leaves, transom light above
DX = 0.55
DR = 0.80
DOOR_T, BAR_T, REC_T = 2.30, 2.38, 2.88
CUT_M.prism(rect(-DX, DX, 0.02, REC_T), DS(0.25), DS(-DR), "y", mi=(SHOP, SHOP, SHOP))
YD = YS + DR
P.box(-DX, DX, YS - 0.02, YD + 0.01, -0.10, 0.025, mi=SHOP)                  # recess floor / sill
dframe = (-DX + 0.05 + 0.10, DX - 0.05 - 0.10, 1.05, 2.12)


def leaf(a, b):
    P.box(a + 0.10, b - 0.10, YD - 0.012, YD, 0.20, 0.90, mi=SHOP)          # raised lower panel
    P.box(a, b, YD - 0.006, YD, 0.02, 0.12, mi=SHOP)                         # kick rail
    pane(CUT_M, SHOPF, rect(a + 0.10, b - 0.10, 1.05, 2.12), DR + 0.02, "door", SHOP, dframe)


leaf(-DX + 0.05, -0.01)
leaf(0.01, DX - 0.05)
P.box(-0.02, 0.02, YD - 0.025, YD, 0.02, DOOR_T, mi=SHOP)                     # astragal
for a, b in ((-DX, -DX + 0.05), (DX - 0.05, DX)):                              # door frame
    P.box(a, b, YD - 0.03, YD, 0.02, REC_T, mi=SHOP)
P.box(-DX + 0.05, DX - 0.05, YD - 0.04, YD, DOOR_T, BAR_T, mi=SHOP)            # transom bar
pane(CUT_M, SHOPF, rect(-DX + 0.08, DX - 0.08, BAR_T + 0.03, REC_T - 0.04), DR + 0.02, "shop_top", SHOP)
# door head and the narrow posts beside the recess
wbox(SHOPF, -0.65, 0.65, 0.0, 0.05, REC_T, TR0 - 0.02, mi=SHOP)
for a, b in ((-0.65, -DX), (DX, 0.65)):
    wbox(SHOPF, a, b, 0.0, 0.05, -0.02, TR1 + 0.04, mi=SHOP)
wbox(SHOPF, -0.65, 0.65, 0.0, 0.05, TR0 - 0.02, TR1, mi=SHOP)
# fascia over the shop front (plain; no lettering) with a cap moulding
wbox(SHOPF, -SFX, SFX, 0.0, 0.06, TR1 + 0.04, SF_TOP)
wbox(SHOPF, -SFX, SFX, 0.0, 0.10, TR1 + 0.04, TR1 + 0.09)

# ---------------------------------------------------------------------------
# Porch over the walk (map 1921: 4.09 deep, to the curb): 5 thin chamfered posts, a beam, a
# pale fascia with a scalloped lower edge on the front and both ends, flat tin roof falling to
# the street; the walk is its floor. No rail, no lettering.
# ---------------------------------------------------------------------------
def pr_under(y):
    """Underside of the porch roof at depth y."""
    return (PR_FRONT - PR_T) + (PR_WALL - PR_FRONT) * y / YW


def chamfered_post(xc, yc, z0, z1, s=POST, ch=0.022):
    """Square post with chamfered arrises (8-sided), square plinth, neck and cap blocks."""
    h = s / 2
    oct_pts = [(-h + ch, -h), (h - ch, -h), (h, -h + ch), (h, h - ch), (h - ch, h), (-h + ch, h), (-h, h - ch), (-h, -h + ch)]
    zb, zt = z0 + 0.26, z1 - 0.30
    P.prism([(xc + u, yc + v) for u, v in oct_pts], zb, zt, "z", mi=PTRIM)
    P.box(xc - h - 0.015, xc + h + 0.015, yc - h - 0.015, yc + h + 0.015, z0, z0 + 0.20, mi=PTRIM)   # plinth
    P.prism([(xc + u * 1.06, yc + v * 1.06) for u, v in oct_pts], z0 + 0.20, zb, "z", mi=PTRIM)      # base mould
    P.box(xc - h, xc + h, yc - h, yc + h, zt, z1, mi=PTRIM)                                           # head
    P.box(xc - h - 0.012, xc + h + 0.012, yc - h - 0.012, yc + h + 0.012, zt, zt + 0.04, mi=PTRIM)   # neck


for xp in POST_X:
    chamfered_post(xp, POST_Y, 0.0, FASCIA[0])

# beam on the posts behind the fascia, and along both ends to the wall
P.box(-HW, HW, 0.035, POST_Y + POST / 2, FASCIA[0], FASCIA[1], mi=PTRIM)
for s in (-1, 1):
    x0, x1 = sorted((s * (HW - 0.025), s * (HW - 0.025 - 0.10)))
    P.prism([(0.025, FASCIA[0] + 0.0), (YW, pr_under(YW) - 0.35), (YW, pr_under(YW)), (0.025, pr_under(0.025))],
            x0, x1, "x", mi=PTRIM)


def scallop_board(u0, u1, ztop, depth=0.35, lobe=0.30, sag=0.10, segs=4):
    """Outline (u, z) of a fascia board: straight top following ztop(u), lower edge a row of
    hanging lobes (scallops) `sag` below the board's plain bottom line."""
    n = max(1, round((u1 - u0) / lobe))
    step = (u1 - u0) / n
    bottom = []
    for i in range(n):
        for k in range(segs + (1 if i == n - 1 else 0)):
            u = u0 + step * i + step * k / segs
            z = ztop(u) - depth - sag * math.sin(math.pi * k / segs) ** 0.6     # rounded lobes
            bottom.append((u, z))
    return bottom + [(u1, ztop(u1)), (u0, ztop(u0))]


# front fascia (y 0.01 ... 0.035), top at 3.60, with a bead along its top at y 0 (front-most)
P.prism(scallop_board(-HW, HW, lambda u: FASCIA[1]), 0.01, 0.035, "y", mi=PTRIM)
P.box(-HW - 0.01, HW + 0.01, 0.0, 0.05, FASCIA[1] - 0.05, FASCIA[1], mi=PTRIM)        # top bead
# end fascias (x = +-3.31 ... +-3.285), top following the roof underside
for s in (-1, 1):
    x0, x1 = sorted((s * HW, s * (HW - 0.025)))
    P.prism(scallop_board(0.0, YW, lambda y: pr_under(y) - 0.0), x0, x1, "x", mi=PTRIM)
# roof sheet: tin on top, painted boards (porch trim) underneath; its back end 2 cm into the wall
P.prism([(0.0, pr_under(0.0)), (YW + 0.02, pr_under(YW + 0.02)),
         (YW + 0.02, pr_under(YW + 0.02) + PR_T), (0.0, pr_under(0.0) + PR_T)],
        -HW - 0.03, HW + 0.03, "x", mi=(PTRIM, PTRIM, [PTRIM, PTRIM, ROOF, PTRIM]))

# ---------------------------------------------------------------------------
# Rear masses (MAP footprints; heights GUESS): A2 3-storey brick piece and A3 1-storey frame
# piece on the south side; B 2 1/2-storey brick block with a gable running back and a lean-to
# on its south side; B2 1-storey brick piece on the north; C frame strips at the back.
# All blank walls (GUESS, plain).
# ---------------------------------------------------------------------------
x0, x1, y0, y1, zt = A2
REARS.prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], SKIRT, zt, "z", mi=(BRICK, ROOF, BRICK))
P.box(x0 - 0.04, x1, y0 - 0.04, y0 + 0.20, zt, zt + 0.08, mi=ROOF)                     # coping
P.box(x0 - 0.04, x0 + 0.20, y0 - 0.04, y1 + 0.04, zt, zt + 0.08, mi=ROOF)
P.box(x0 - 0.04, x1, y1 - 0.20, y1 + 0.04, zt, zt + 0.08, mi=ROOF)

x0, x1, y0, y1, zh, zl = A3                    # shed falls to the front (east)
REARS.prism([(y0, SKIRT), (y1, SKIRT), (y1, zh), (y0, zl)], x0, x1, "x", mi=(CLAP, CLAP, [CLAP, CLAP, ROOF, CLAP]))
P.prism([(y0 - 0.15, zl - 0.04), (y1, zh), (y1, zh + 0.06), (y0 - 0.15, zl + 0.02)], x0 - 0.12, x1, "x", mi=ROOF)

# B: gable block; ridge along Y at its centre
bx0, bx1, by0, by1 = B
bxc = (bx0 + bx1) / 2
REARS.prism([(bx0, SKIRT), (bx1, SKIRT), (bx1, B_EAVE), (bxc, B_RIDGE), (bx0, B_EAVE)], by0, by1, "y",
            mi=(BRICK, BRICK, [BRICK, BRICK, ROOF, ROOF, BRICK]))
OV = 0.25
slope = (B_RIDGE - B_EAVE) / (bxc - bx0)
for s in (-1, 1):                              # roof slabs with an overhang
    xe = bx0 - OV if s < 0 else bx1 + OV
    ze = B_EAVE - OV * slope
    P.prism([(xe, ze), (bxc, B_RIDGE), (bxc, B_RIDGE + 0.07), (xe, ze + 0.07)], by0 - 0.0, by1 + OV, "y",
            mi=(ROOF, ROOF, ROOF))
# lean-to on the south side of B
lx0, lx1, ly0, ly1 = B_SOUTH
REARS.prism([(lx0, SKIRT), (lx1, SKIRT), (lx1, 5.95), (lx0, 5.45)], ly0, ly1, "y",
            mi=(BRICK, BRICK, [BRICK, BRICK, ROOF, BRICK]))
P.prism([(lx0 - 0.20, 5.41), (lx1, 5.95), (lx1, 6.01), (lx0 - 0.20, 5.47)], ly0 - 0.15, ly1 + 0.15, "y", mi=ROOF)

x0, x1, y0, y1, zt = B2
REARS.prism([(x0 - 0.30, y0), (x1, y0), (x1, y1), (x0 - 0.30, y1)], SKIRT, zt, "z", mi=(BRICK, ROOF, BRICK))
P.box(x0, x1 + 0.04, y0, y1 + 0.04, zt, zt + 0.06, mi=ROOF)

y0, y1 = C_Y
for (x0, x1, zh, zl), mat in ((C2, CLAP), (C1, CLAP)):     # sheds falling to the rear
    REARS.prism([(y0 - 0.05, SKIRT), (y1, SKIRT), (y1, zl), (y0 - 0.05, zh)], x0, x1, "x",
                mi=(mat, mat, [mat, mat, ROOF, mat]))
    P.prism([(y0 - 0.05, zh), (y1 + 0.20, zl - 0.03), (y1 + 0.20, zl + 0.03), (y0 - 0.05, zh + 0.06)],
            x0 - 0.10, x1 + 0.10, "x", mi=ROOF)

# ---------------------------------------------------------------------------
# Build objects (boolean the cut shell)
# ---------------------------------------------------------------------------
def cut_shell(shell, cut, name):
    walls = shell.to_object(name, col)
    cutters = cut.to_object(name + "_Cutters", col)
    mod = walls.modifiers.new("Openings", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    solvers = [i.identifier for i in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items]
    mod.solver = "EXACT" if "EXACT" in solvers else solvers[0]
    mod.use_self = True
    mod.material_mode = "INDEX"
    mod.object = cutters
    dg = bpy.context.evaluated_depsgraph_get()
    cut_mesh = bpy.data.meshes.new_from_object(walls.evaluated_get(dg))
    walls.modifiers.clear()
    old = walls.data
    walls.data = cut_mesh
    cut_mesh.name = name
    bpy.data.meshes.remove(old)
    bpy.data.objects.remove(cutters, do_unlink=True)
    return walls


main = cut_shell(MAIN, CUT_M, "GB_Main")
assign_atlas_uvs(main)
rears = REARS.to_object("GB_Rears", col)
parts = P.to_object("GB_Parts", col)
assign_atlas_uvs(parts)
assign_shutter_uvs(parts)

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("83-87 Main built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)")
# Materials, baked lighting and GLB export: run block_83_87_bake.py (it runs this file first).
