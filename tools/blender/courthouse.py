"""
courthouse.py - builds the Hunterdon County Court House (75 Main St, Flemington, c. 1920)
in Blender.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/courthouse.py").read())

Every run deletes and rebuilds the "Courthouse" collection, so edit the numbers below
and run again. Materials, lightmap bake and GLB export: courthouse_bake.py (runs this first).

Sources: PLAN.md "Hunterdon County Court House" spec (1921 Sanborn sheet 2, the c.1910
dead-on postcard, the 1909 colour card, HABS NJ-771), including the owner decisions
(slate roof, green ribbed dome, paired scroll brackets, jail yard, no window bars,
fire-alarm post, three chimneys per slope) and the cross-check corrections.

Coordinates (metres, Blender Z-up):
    X  across the front, +X = north (the north wing is at +X), -X = south (Court St)
    Y  depth: y = 0 is the front edge of the portico podium; the steps run out to
       y = -1.65 (toward the street); the body runs back to y = 24.91.
    Z  up from the foot of the steps (forecourt level).
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".
"""

import math
import bpy
import bmesh
from mathutils import Matrix

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md)
# ---------------------------------------------------------------------------
HW = 6.70              # half width of body and portico (13.4 m)
PORT = 4.43            # front wall of the body (portico depth)
BACK = 24.91           # rear wall
WALL_T = 0.60          # stone wall thickness
PODIUM = 1.10          # portico floor / top of the brownstone base course
ARCH_BOT = 7.45        # underside of the entablature = portico ceiling
FRIEZE_BOT = 8.00
CORN_BOT = 8.65
CORONA_BOT = 8.75
EAVE = 9.00            # top of the horizontal cornice
OVER = 0.60            # cornice overhang
RIDGE = 13.20          # top of the roof at the ridge
ROOF_X = 7.25          # roof slab reaches out to here at the eaves
PITCH = (RIDGE - 9.03) / ROOF_X            # tan of the roof pitch (~30 deg)
FRONT_FACE = 0.05      # front face of the entablature and tympanum
COLS_X = (-6.13, -2.04, 2.04, 6.13)
COL_Y = 0.58
CUP_Y = 6.50           # cupola centre
SIDE_BAYS = (9.0, 12.2, 15.4, 18.6, 21.8)
RECESS = 0.32          # window/door openings are recesses this deep (glass and doors close
                       # them), so the walls stay solid and the hidden interior can be culled


def roof_z(x):
    """Top of the roof (and the raking cornice) above the point x."""
    return RIDGE - abs(x) * PITCH


# ---------------------------------------------------------------------------
# Materials (plain stand-ins; courthouse_bake.py swaps in the textures)
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


COLOURS = {
    "Stucco": "#e6e1d4",      # walls, antae, tympanum, cupola base
    "Trim": "#f2efe6",        # columns, entablature, brackets, cupola drum
    "Brownstone": "#6e4a3c",  # steps, pedestals, base course, sills
    "Slate": "#4b5052",
    "Dome": "#4a5a46",
    "Brick": "#8c3b2a",
    "Clapboard": "#9c8566",
    "RockWall": "#77736b",
    "Door": "#3f5443",
    "Sash": "#1e2621",        # dark green-black sash, frames, louvre backs, wing trim
    "Glass": "#15191d",
    "Iron": "#1b1b1b",
    "Alarm": "#8a2a20",       # fire-alarm post
}
MATS = {k: plain("CH_" + k, c) for k, c in COLOURS.items()}

# ---------------------------------------------------------------------------
# Mesh builder (as in union_hotel.py, plus rotation and lathe phase)
# ---------------------------------------------------------------------------


class MB:
    """Collects geometry for one material. Shapes are added in place."""

    def __init__(self):
        self.bm = bmesh.new()

    def _closed(self, faces):
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)

    @staticmethod
    def _pt(axis, u, d, v):
        # axis 'y': outline in the X-Z plane, depth along Y (front/back faces)
        # axis 'x': outline in the Y-Z plane, depth along X (side faces)
        return (u, d, v) if axis == "y" else (d, u, v)

    def prism(self, pts, d0, d1, axis="y"):
        """Extrude a 2D outline [(u, v), ...] between depths d0 and d1."""
        bm = self.bm
        a = [bm.verts.new(self._pt(axis, u, d0, v)) for u, v in pts]
        b = [bm.verts.new(self._pt(axis, u, d1, v)) for u, v in pts]
        faces = [bm.faces.new(a), bm.faces.new(list(reversed(b)))]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
        self._closed(faces)

    def box(self, x0, x1, y0, y1, z0, z1):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)

    def ring_arch(self, cu, zs, r_in, r_out, d0, d1, axis="y", segs=12):
        """Half-round band (archivolt, fanlight frame) springing at height zs."""
        bm = self.bm
        ts = [math.pi * i / segs for i in range(segs + 1)]

        def ring(r, d):
            return [bm.verts.new(self._pt(axis, cu + r * math.cos(t), d, zs + r * math.sin(t))) for t in ts]
        of, inf, ob, ib = ring(r_out, d0), ring(r_in, d0), ring(r_out, d1), ring(r_in, d1)
        faces = []
        for i in range(segs):
            faces.append(bm.faces.new([of[i], of[i + 1], inf[i + 1], inf[i]]))
            faces.append(bm.faces.new([ob[i], ib[i], ib[i + 1], ob[i + 1]]))
            faces.append(bm.faces.new([of[i], ob[i], ob[i + 1], of[i + 1]]))
            faces.append(bm.faces.new([inf[i], inf[i + 1], ib[i + 1], ib[i]]))
        faces.append(bm.faces.new([of[0], inf[0], ib[0], ob[0]]))
        faces.append(bm.faces.new([of[-1], ob[-1], ib[-1], inf[-1]]))
        self._closed(faces)

    def lathe(self, profile, cx, cy, z0=0.0, segs=12, phase=0.0, rfun=None):
        """Turned solid from a profile [(radius, height), ...], bottom to top.
        phase rotates the first vertex; rfun(k, r) can reshape ring k (ribs, octagons)."""
        bm = self.bm
        rings = []
        for r, z in profile:
            if r == 0:
                rings.append([bm.verts.new((cx, cy, z0 + z))])
            else:
                ring = []
                for k in range(segs):
                    a = phase + 2 * math.pi * k / segs
                    rk = rfun(k, r) if rfun else r
                    ring.append(bm.verts.new((cx + rk * math.cos(a), cy + rk * math.sin(a), z0 + z)))
                rings.append(ring)
        faces = []
        for a, b in zip(rings, rings[1:]):
            for k in range(segs):
                k2 = (k + 1) % segs
                if len(a) == 1:
                    faces.append(bm.faces.new([a[0], b[k], b[k2]]))
                elif len(b) == 1:
                    faces.append(bm.faces.new([a[k], a[k2], b[0]]))
                else:
                    faces.append(bm.faces.new([a[k], a[k2], b[k2], b[k]]))
        self._closed(faces)

    def mark(self):
        return len(self.bm.verts)

    def rotate_since(self, start, angle, cx, cy):
        """Rotate every vertex added since mark() about the vertical axis at (cx, cy)."""
        self.bm.verts.ensure_lookup_table()
        verts = self.bm.verts[start:]
        bmesh.ops.rotate(self.bm, verts=verts, cent=(cx, cy, 0), matrix=Matrix.Rotation(angle, 3, "Z"))

    def to_object(self, name, mat, col):
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        obj = bpy.data.objects.new(name, mesh)
        mesh.materials.append(mat)
        col.objects.link(obj)
        return obj


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def arched(cu, w, z0, zs, segs=10):
    """Outline of a round-headed opening: straight sides from z0 up to zs, half-circle above."""
    r = w / 2
    return [(cu - r, z0), (cu + r, z0)] + [
        (cu + r * math.cos(math.pi * i / segs), zs + r * math.sin(math.pi * i / segs))
        for i in range(segs + 1)]


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


col = fresh_collection("Courthouse")
G = {k: MB() for k in MATS}      # geometry per material
WALLS, CUT = MB(), MB()          # stucco shells (body + tympana), cut by CUT
DRUM, CUT_DRUM = MB(), MB()      # cupola drum (painted wood), cut by CUT_DRUM
WING, CUT_WING = MB(), MB()      # clapboard north wing, cut by CUT_WING

# Each wall: (axis, outer face depth, outward sign)
FRONT_WALL = ("y", PORT, -1)
REAR_WALL = ("y", BACK, 1)
SOUTH_WALL = ("x", -HW, -1)
NORTH_WALL = ("x", HW, 1)
TYMPANUM = ("y", FRONT_FACE, -1)
REAR_TYMPANUM = ("y", BACK, 1)
WING_EAST = ("y", 5.11, -1)


def window(wall, cu, w, h, z_sill, cols=3, rows=2, sashes=2, sill="Brownstone", cut=None):
    """Rectangular double-hung window: opening, glass, dark sash with muntins, stone sill.
    cols x rows panes in each of `sashes` sashes (6/6 = cols 3, rows 2, sashes 2)."""
    axis, face, out = wall
    D = lambda k: face + out * k        # k > 0 is outside the wall, k < 0 inside
    z_top = z_sill + h
    u0, u1 = cu - w / 2, cu + w / 2
    (cut or CUT).prism(rect(u0, u1, z_sill, z_top), D(0.25), D(-RECESS), axis)
    G["Glass"].prism(rect(u0, u1, z_sill, z_top), D(-0.20), D(-0.23), axis)
    S = G["Sash"]
    f = 0.06                                                    # frame
    S.prism(rect(u0, u0 + f, z_sill, z_top), D(-0.12), D(-0.20), axis)
    S.prism(rect(u1 - f, u1, z_sill, z_top), D(-0.12), D(-0.20), axis)
    S.prism(rect(u0 + f, u1 - f, z_top - f, z_top), D(-0.12), D(-0.20), axis)
    S.prism(rect(u0 + f, u1 - f, z_sill, z_sill + 0.08), D(-0.12), D(-0.20), axis)
    iu0, iu1, iz0, iz1 = u0 + f, u1 - f, z_sill + 0.08, z_top - f
    for k in range(1, cols):                                    # vertical muntins
        u = iu0 + (iu1 - iu0) * k / cols
        S.prism(rect(u - 0.0125, u + 0.0125, iz0, iz1), D(-0.15), D(-0.20), axis)
    n = rows * sashes
    for k in range(1, n):                                       # horizontal muntins / meeting rail
        z = iz0 + (iz1 - iz0) * k / n
        t = 0.025 if (sashes == 2 and k == n // 2) else 0.0125
        S.prism(rect(iu0, iu1, z - t, z + t), D(-0.15), D(-0.20), axis)
    if sill:
        G[sill].prism(rect(u0 - 0.08, u1 + 0.08, z_sill - 0.07, z_sill + 0.03), D(0.08), D(-0.12), axis)


def arched_door(wall, cu, w, z0, zs, cut=None):
    """Round-arched doorway: white frame, fanlight with radiating bars, double
    6-panel doors (each leaf 2 x 3 panels)."""
    axis, face, out = wall
    D = lambda k: face + out * k
    r = w / 2
    f = 0.09
    (cut or CUT).prism(arched(cu, w, z0 - 0.05, zs, 14), D(0.25), D(-RECESS), axis)
    G["Glass"].prism(arched(cu, w - 2 * f, zs - 0.14, zs, 14), D(-0.22), D(-0.25), axis)
    # radiating bars and a small half-round hub
    for a in (math.pi / 6, math.pi / 3, math.pi / 2, 2 * math.pi / 3, 5 * math.pi / 6):
        ca, sa = math.cos(a), math.sin(a)
        nx, nz = -sa * 0.018, ca * 0.018
        x1, z1 = cu + (r - f) * ca, zs + (r - f) * sa
        G["Sash"].prism([(cu + nx, zs + nz), (cu - nx, zs - nz), (x1 - nx, z1 - nz), (x1 + nx, z1 + nz)],
                        D(-0.17), D(-0.22), axis)
    G["Sash"].ring_arch(cu, zs, 0.0 + 0.001, 0.2, D(-0.16), D(-0.22), axis, segs=6)
    G["Sash"].ring_arch(cu, zs, r - f - 0.03, r - f, D(-0.16), D(-0.22), axis, segs=12)
    # white frame: jambs, transom bar, arch
    G["Trim"].prism(rect(cu - r, cu - r + f, z0, zs), D(0.02), D(-0.28), axis)
    G["Trim"].prism(rect(cu + r - f, cu + r, z0, zs), D(0.02), D(-0.28), axis)
    G["Trim"].prism(rect(cu - r, cu + r, zs - 0.14, zs), D(0.02), D(-0.28), axis)
    G["Trim"].ring_arch(cu, zs, r - f, r, D(0.02), D(-0.28), axis, segs=14)
    G["Trim"].ring_arch(cu, zs, r, r + 0.14, D(0.04), D(-0.02), axis, segs=14)   # archivolt
    # leaves
    top = zs - 0.14
    inner = w - 2 * f
    leaf = inner / 2
    for i in range(2):
        x0 = cu - inner / 2 + i * leaf + 0.006
        x1 = x0 + leaf - 0.012
        G["Door"].prism(rect(x0, x1, z0, top), D(-0.16), D(-0.22), axis)
        pw = (x1 - x0 - 0.3) / 2                                     # two panels wide
        hs = [(z0 + 0.15, z0 + 0.62), (z0 + 0.78, top - 0.62), (top - 0.48, top - 0.12)]
        for c in range(2):
            p0 = x0 + 0.1 + c * (pw + 0.1)
            for zb, zt in hs:
                G["Door"].prism(rect(p0, p0 + pw, zb, zt), D(-0.14), D(-0.16), axis)
        kx = x1 - 0.07 if i == 0 else x0 + 0.07
        G["Iron"].prism(rect(kx - 0.025, kx + 0.025, z0 + 1.0, z0 + 1.05), D(-0.11), D(-0.16), axis)


# ---------------------------------------------------------------------------
# Podium, steps, base course
# ---------------------------------------------------------------------------

# podium under the portico, and the brownstone water table round the body as a separate
# block (so the hidden top under the body can be dropped before the lightmap is unwrapped)
G["Brownstone"].box(-HW - 0.04, HW + 0.04, 0.0, PORT, 0.0, PODIUM)
G["Brownstone"].box(-HW - 0.04, HW + 0.04, PORT, BACK + 0.04, 0.0, PODIUM)
# five steps + the podium face = 6 risers of 0.183 m; treads 0.33 m out to y = -1.65
RISER = PODIUM / 6
stair = [(-1.65, 0.0)]
for k in range(5):
    y = -1.65 + 0.33 * k
    stair += [(y, RISER * (k + 1)), (y + 0.33, RISER * (k + 1))]
stair += [(0.02, RISER * 5), (0.02, 0.0)]
G["Brownstone"].prism(stair, -6.5, 6.5, axis="x")

# ---------------------------------------------------------------------------
# Body walls (one hollow stucco shell, windows cut by booleans)
# ---------------------------------------------------------------------------

WALLS.box(-HW, HW, PORT, BACK, PODIUM, ARCH_BOT)
CUT.box(-HW + WALL_T, HW - WALL_T, PORT + WALL_T, BACK - WALL_T, PODIUM + 0.3, ARCH_BOT + 1.0)

# Front wall: 3 bays. Round-arched door, windows on two floors, attic lights.
arched_door(FRONT_WALL, 0.0, 1.85, PODIUM, 2.92)
for x in (-3.7, 3.7):
    window(FRONT_WALL, x, 1.1, 1.8, 2.0)
    window(FRONT_WALL, x, 1.1, 1.9, 4.45)
    window(FRONT_WALL, x, 0.9, 0.6, 6.55, cols=3, rows=1, sashes=2)
window(FRONT_WALL, 0.0, 1.1, 1.9, 4.45)

# Side walls: 3.5 m blank at the front, then 5 bays. The wing hides two north ground bays.
for wall in (SOUTH_WALL, NORTH_WALL):
    for i, y in enumerate(SIDE_BAYS):
        if not (wall is NORTH_WALL and i < 2):
            window(wall, y, 1.0, 1.8, 2.0)
        window(wall, y, 1.0, 2.6, 4.4, rows=2)

# Rear wall (guess): 3 bays of the same windows.
for x in (-3.7, 0.0, 3.7):
    window(REAR_WALL, x, 1.0, 1.8, 2.0)
    window(REAR_WALL, x, 1.0, 2.6, 4.4)

# Antae / corner pilasters (flat stucco strips, 0.6 m) with a simple cap.
for s in (-1, 1):
    x_in, x_out = s * (HW - 0.6), s * HW
    G["Stucco"].box(min(x_in, x_out), max(x_in, x_out), PORT - 0.10, PORT + 0.01, PODIUM, ARCH_BOT)
    G["Trim"].box(min(x_in, x_out) - 0.04, max(x_in, x_out) + 0.0, PORT - 0.15, PORT + 0.01, ARCH_BOT - 0.25, ARCH_BOT)
    for y0, y1 in ((PORT - 0.10, PORT + 0.6), (BACK - 0.6, BACK + 0.10)):
        G["Stucco"].box(min(s * HW, s * (HW + 0.10)), max(s * HW, s * (HW + 0.10)), y0, y1, PODIUM, ARCH_BOT)
        G["Trim"].box(min(s * (HW - 0.01), s * (HW + 0.15)), max(s * (HW - 0.01), s * (HW + 0.15)),
                      y0 - 0.04, y1 + 0.04, ARCH_BOT - 0.25, ARCH_BOT)
for s in (-1, 1):   # rear-wall corner strips
    G["Stucco"].box(min(s * (HW - 0.6), s * HW), max(s * (HW - 0.6), s * HW), BACK - 0.01, BACK + 0.10, PODIUM, ARCH_BOT)

# ---------------------------------------------------------------------------
# Portico: pedestals, four unfluted Tuscan columns
# ---------------------------------------------------------------------------

COLUMN = [  # (radius, height above the pedestal top at 1.55 m)
    (0.0, 0.0), (0.53, 0.0), (0.53, 0.07), (0.50, 0.13), (0.46, 0.20), (0.45, 0.26),
    (0.444, 1.9), (0.425, 3.7), (0.39, 5.48), (0.42, 5.50), (0.42, 5.56), (0.39, 5.58),
    (0.43, 5.64), (0.50, 5.75), (0.0, 5.75)]
for x in COLS_X:
    G["Brownstone"].box(x - 0.575, x + 0.575, COL_Y - 0.575, COL_Y + 0.575, PODIUM, 1.49)
    G["Brownstone"].box(x - 0.61, x + 0.61, COL_Y - 0.61, COL_Y + 0.61, 1.49, 1.55)
    G["Trim"].lathe(COLUMN, x, COL_Y, 1.55, segs=32)
    G["Trim"].box(x - 0.525, x + 0.525, COL_Y - 0.525, COL_Y + 0.525, 7.30, ARCH_BOT)   # abacus

# ---------------------------------------------------------------------------
# Entablature, cornice, scroll brackets, modillions
# ---------------------------------------------------------------------------

T = G["Trim"]
T.box(-HW, HW, FRONT_FACE, PORT, ARCH_BOT, CORN_BOT)          # over the portico (its underside is the ceiling)
T.box(-HW, HW, PORT, BACK, ARCH_BOT, CORN_BOT)                # over the body
T.box(-HW - 0.02, HW + 0.02, FRONT_FACE - 0.02, BACK + 0.02, 7.73, FRIEZE_BOT)     # upper fascia
T.box(-HW - 0.06, HW + 0.06, FRONT_FACE - 0.06, BACK + 0.06, 7.96, 8.03)           # taenia
T.box(-HW - 0.15, HW + 0.15, FRONT_FACE - 0.15, BACK + 0.15, CORN_BOT, CORONA_BOT)  # bed moulding
T.box(-HW - OVER, HW + OVER, FRONT_FACE - OVER, BACK + OVER, CORONA_BOT, EAVE)      # corona
# datestone, centred in the front frieze
T.box(-0.5, 0.5, FRONT_FACE - 0.05, FRONT_FACE + 0.01, 8.15, 8.50)
T.box(-0.42, 0.42, FRONT_FACE - 0.07, FRONT_FACE - 0.04, 8.20, 8.45)

# Scroll bracket profile: (projection from the frieze, height); hangs from the corona soffit.
BRACKET = [(0.0, CORONA_BOT), (0.46, CORONA_BOT), (0.46, CORONA_BOT - 0.07), (0.38, CORONA_BOT - 0.12),
           (0.29, CORONA_BOT - 0.20), (0.22, CORONA_BOT - 0.32), (0.18, CORONA_BOT - 0.46),
           (0.19, CORONA_BOT - 0.58), (0.15, CORONA_BOT - 0.68), (0.09, CORONA_BOT - 0.78),
           (0.05, CORONA_BOT - 0.92), (0.0, CORONA_BOT - 0.92)]
BW = 0.12            # bracket thickness
PAIR = 0.17          # half spacing of a pair


def bracket_front(x, face=FRONT_FACE, out=-1):
    pts = [(face + out * o, z) for o, z in BRACKET]
    T.prism(pts, x - BW / 2, x + BW / 2, axis="x")


def bracket_side(s, y):
    pts = [(s * (HW + o), z) for o, z in BRACKET]
    T.prism(pts, y - BW / 2, y + BW / 2, axis="y")


def modillion_front(x, face=FRONT_FACE, out=-1):
    T.box(x - 0.05, x + 0.05, min(face, face + out * 0.32), max(face, face + out * 0.32), CORN_BOT - 0.05, CORONA_BOT)


def modillion_side(s, y):
    T.box(min(s * HW, s * (HW + 0.32)), max(s * HW, s * (HW + 0.32)), y - 0.05, y + 0.05, CORN_BOT - 0.05, CORONA_BOT)


def fill_modillions(a, b, put, avoid):
    n = int((b - a) / 0.6)
    for k in range(n + 1):
        t = a + (b - a) * k / max(n, 1)
        if all(abs(t - c) > PAIR + 0.25 for c in avoid):
            put(t)


# front: a pair over each column; corner pairs wrap round onto the sides
for x in COLS_X:
    for d in (-PAIR, PAIR):
        bracket_front(min(max(x + d, -HW + 0.08), HW - 0.08))
fill_modillions(-HW + 0.3, HW - 0.3, modillion_front, COLS_X)
side_pairs = [COL_Y] + [4.6 + 4.0 * k for k in range(5)] + [BACK - 0.5]
for s in (-1, 1):
    for y in side_pairs:
        for d in (-PAIR, PAIR):
            bracket_side(s, max(y + d, FRONT_FACE + 0.08))
    fill_modillions(FRONT_FACE + 0.3, BACK - 0.3, lambda y, s=s: modillion_side(s, y), side_pairs)
# rear: corner pairs only (the rear pediment is plain)
for x in (-HW + 0.45, HW - 0.45):
    for d in (-PAIR, PAIR):
        bracket_front(x + d, BACK, 1)

# ---------------------------------------------------------------------------
# Pediments, roof
# ---------------------------------------------------------------------------

# Tympana (stucco, part of the cut wall shells). Their sloping edges hide under the rake.
TYMP_APEX = RIDGE - 0.30
WALLS.prism([(-HW, EAVE), (HW, EAVE), (0, TYMP_APEX)], FRONT_FACE, FRONT_FACE + 0.55)
WALLS.prism([(-HW, EAVE), (HW, EAVE), (0, TYMP_APEX)], BACK - 0.55, BACK)
for x in (-2.1, 2.1):                       # two 6-light windows (cross-check: 0.95 x 1.45, sill 9.4)
    window(TYMPANUM, x, 0.95, 1.45, 9.4, cols=2, rows=3, sashes=1, sill="Trim")
window(REAR_TYMPANUM, 0.0, 0.95, 1.45, 9.4, cols=2, rows=3, sashes=1, sill="Trim")


def rake_band(top_off, bot_off, y0, y1, mb):
    """One layer of the raking cornice: between top_off and bot_off below the roof line,
    standing on the horizontal cornice (z = EAVE)."""
    for s in (-1, 1):
        x_t = min(ROOF_X, (RIDGE - top_off - EAVE) / PITCH)
        x_b = (RIDGE - bot_off - EAVE) / PITCH
        pts = [(s * x_b, EAVE), (s * x_t, EAVE), (s * x_t, RIDGE - x_t * PITCH - top_off),
               (0, RIDGE - top_off), (0, RIDGE - bot_off)]
        if s < 0:
            pts = list(reversed(pts))
        mb.prism(pts, y0, y1)


SLAB = 0.10
for y_out, y_in, sgn in ((FRONT_FACE - OVER - 0.05, FRONT_FACE + 0.10, -1), (BACK + OVER + 0.05, BACK - 0.10, 1)):
    yo = y_out - sgn * 0.05                     # corona front 5 cm behind the slate edge
    rake_band(SLAB, SLAB + 0.25, min(yo, y_in), max(yo, y_in), T)
    yb = y_in + sgn * (0.30 + 0.10)             # bed moulding 0.30 m out from the tympanum
    rake_band(SLAB + 0.25, SLAB + 0.45, min(yb, y_in), max(yb, y_in), T)

# Roof: two slate slabs from the front rake to the rear rake.
for s in (-1, 1):
    pts = [(s * ROOF_X, roof_z(ROOF_X)), (0, RIDGE), (0, RIDGE - SLAB), (s * ROOF_X, roof_z(ROOF_X) - SLAB)]
    if s < 0:
        pts = list(reversed(pts))
    G["Slate"].prism(pts, FRONT_FACE - OVER - 0.05, BACK + OVER + 0.05)
G["Slate"].box(-0.12, 0.12, FRONT_FACE - OVER - 0.05, BACK + OVER + 0.05, RIDGE - 0.05, RIDGE + 0.06)  # ridge roll


def rake_soffit(x):
    """Underside of the raking bed moulding above x."""
    return roof_z(x) - SLAB - 0.45


# Pendant scroll brackets on the front rake: three pairs a side, small modillions between.
RAKE_PAIRS = (1.25, 3.35, 5.45)
for s in (-1, 1):
    for xc in RAKE_PAIRS:
        for d in (-PAIR, PAIR):
            x = s * (xc + d)
            top = rake_soffit(abs(x) + BW / 2) + 0.06
            pts = [(FRONT_FACE - o * 0.75, top - (CORONA_BOT - z) * 0.85) for o, z in BRACKET]
            T.prism(pts, x - BW / 2, x + BW / 2, axis="x")
    k = 0.5
    while k < 6.3:
        if all(abs(k - c) > PAIR + 0.25 for c in RAKE_PAIRS):
            x = s * k
            top = rake_soffit(k + 0.05) + 0.05
            T.box(x - 0.05, x + 0.05, FRONT_FACE - 0.26, FRONT_FACE + 0.02, top - 0.16, top)
        k += 0.6

# ---------------------------------------------------------------------------
# Chimneys: three on each slope at the rear, one in front of the cupola (north-east)
# ---------------------------------------------------------------------------


def chimney(x, y, top, wx=0.6, wy=0.8):
    """Brick stack wx (across) x wy (along the ridge) with a two-course corbelled cap."""
    hx, hy = wx / 2, wy / 2
    base = roof_z(abs(x) + hx) - 0.4
    G["Brick"].box(x - hx, x + hx, y - hy, y + hy, base, top - 0.32)
    G["Brick"].box(x - hx - 0.06, x + hx + 0.06, y - hy - 0.06, y + hy + 0.06, top - 0.32, top - 0.2)
    G["Brick"].box(x - hx - 0.10, x + hx + 0.10, y - hy - 0.10, y + hy + 0.10, top - 0.2, top)


# Rear stacks (review round 1): 0.9 x 1.2 m and about 3.5 m above the roof, so they read
# as masonry stacks (HABS, 1909 card) rather than thin smokestacks.
for s in (-1, 1):
    for y in (15.0, 18.5, 22.0):
        chimney(s * (HW - 1.2), y, 13.9, 0.9, 1.2)
# Front stack: north-east of the cupola with roof between them, top about level with the
# drum's base (1909 card; review round 1).
chimney(3.0, 4.6, 14.2)

# ---------------------------------------------------------------------------
# Cupola: square stucco base, octagonal louvred drum, cornice, ribbed bell dome, finial
# ---------------------------------------------------------------------------

CB = 1.5
G["Stucco"].prism([(-CB, roof_z(CB) - 0.25), (0, RIDGE - 0.25), (CB, roof_z(CB) - 0.25), (CB, 13.75), (-CB, 13.75)],
                  CUP_Y - CB, CUP_Y + CB)
T.box(-CB - 0.08, CB + 0.08, CUP_Y - CB - 0.08, CUP_Y + CB + 0.08, 13.75, 13.88)
T.box(-CB - 0.14, CB + 0.14, CUP_Y - CB - 0.14, CUP_Y + CB + 0.14, 13.88, 13.95)

APO = 1.40                          # drum: 2.8 m across flats
RC = APO / math.cos(math.pi / 8)    # corner radius
OCT = math.pi / 8                   # phase: flats face +-X and +-Y
DRUM.lathe([(0, 13.90), (RC, 13.90), (RC, 16.30), (0, 16.30)], 0, CUP_Y, segs=8, phase=OCT)
FY = CUP_Y - APO                    # the -Y face of the drum
for m in range(8):
    ang = m * math.pi / 4
    marks = {mb: mb.mark() for mb in (CUT_DRUM, G["Sash"], T)}
    CUT_DRUM.prism(arched(0, 0.80, 14.25, 15.45), FY - 0.2, FY + 0.15)
    G["Sash"].prism(arched(0, 0.80, 14.25, 15.45), FY + 0.14, FY + 0.17)        # dark interior
    for i in range(6):                                                          # louvre slats
        zc = 14.38 + i * 0.19
        T.prism([(FY + 0.03, zc - 0.06), (FY + 0.05, zc - 0.08), (FY + 0.145, zc + 0.03), (FY + 0.125, zc + 0.05)],
                -0.4, 0.4, axis="x")
    T.box(-0.5, 0.5, FY - 0.08, FY + 0.06, 14.17, 14.25)                        # sill
    T.ring_arch(0, 15.45, 0.40, 0.48, FY - 0.04, FY + 0.01, segs=10)            # arch moulding
    T.box(-0.09, 0.09, CUP_Y - RC - 0.05, CUP_Y - RC + 0.14, 13.90, 16.30)      # corner pilaster
    for mb, start in marks.items():
        if mb is T:
            # everything but the pilaster turns with the face; the pilaster goes to a corner
            T.rotate_since(start, ang, 0, CUP_Y)
            pil = T.bm.verts[len(T.bm.verts) - 8:]          # the pilaster box is the last 8 verts
            bmesh.ops.rotate(T.bm, verts=pil, cent=(0, CUP_Y, 0), matrix=Matrix.Rotation(OCT, 3, "Z"))
        else:
            mb.rotate_since(start, ang, 0, CUP_Y)

T.lathe([(0, 16.28), (RC + 0.04, 16.28), (RC + 0.04, 16.38), (RC + 0.16, 16.46), (RC + 0.30, 16.54),
         (RC + 0.32, 16.65), (0, 16.65)], 0, CUP_Y, segs=8, phase=OCT)

DOME = [(1.56, 0.0), (1.50, 0.10), (1.45, 0.26), (1.38, 0.48), (1.22, 0.78), (0.98, 1.03),
        (0.68, 1.24), (0.36, 1.38), (0.10, 1.45), (0.0, 1.45)]


def dome_shape(k, r):
    if k % 2:                              # middle of a flat: octagon apothem
        return r * math.cos(OCT)
    return r + (0.045 if r > 0.15 else 0)  # corner: a raised rib


G["Dome"].lathe(DOME, 0, CUP_Y, 16.65, segs=16, phase=OCT, rfun=dome_shape)
BALL = [(0.0, 0.0), (0.06, 0.0), (0.12, 0.03), (0.165, 0.09), (0.175, 0.175), (0.165, 0.26),
        (0.12, 0.32), (0.06, 0.345), (0.0, 0.35)]
T.lathe([(0.0, 0.0), (0.10, 0.0), (0.06, 0.08), (0.0, 0.08)], 0, CUP_Y, 18.08, segs=10)
T.lathe(BALL, 0, CUP_Y, 18.14, segs=12)
G["Iron"].lathe([(0.0, 0.0), (0.025, 0.0), (0.02, 0.9), (0.0, 1.0)], 0, CUP_Y, 18.45, segs=6)
G["Iron"].prism([(-0.40, 18.98), (0.28, 18.98), (0.28, 18.93), (0.40, 19.0), (0.28, 19.07), (0.28, 19.02),
                 (-0.40, 19.02)], CUP_Y - 0.008, CUP_Y + 0.008)            # weathervane arrow
G["Iron"].prism([(-0.42, 18.92), (-0.30, 18.92), (-0.36, 19.0), (-0.30, 19.08), (-0.42, 19.08)],
                CUP_Y - 0.008, CUP_Y + 0.008)                                 # its tail

# ---------------------------------------------------------------------------
# North wing ("jail kitchen"): one-storey frame, stone strip against the body
# ---------------------------------------------------------------------------

WX0, WXS, WX1 = HW, HW + 1.04, 10.50   # body wall, end of the stone strip, north face
WY0, WY1 = 5.11, 12.93
W_HI, W_LO = 4.2, 3.4                  # shed roof: high at the body, low at the north face


def wing_top(x):
    return W_HI + (W_LO - W_HI) * (x - WX0) / (WX1 - WX0)


G["Brownstone"].box(WXS, WX1, WY0, WY1, 0.0, 0.45)                                   # foundation
G["Stucco"].prism([(WX0 - 0.05, PODIUM), (WXS, PODIUM), (WXS, wing_top(WXS)), (WX0 - 0.05, wing_top(WX0))],
                  WY0, WY1)
G["Brownstone"].box(WX0, WXS, WY0 - 0.04, WY1 + 0.04, 0.0, PODIUM)
WING.prism([(WXS, 0.45), (WX1, 0.45), (WX1, wing_top(WX1)), (WXS, wing_top(WXS))], WY0, WY1)
window(WING_EAST, 9.70, 1.4, 1.2, 1.0, cols=3, rows=2, sashes=2, sill="Sash", cut=CUT_WING)
# plain door with four panels under a shed hood
CUT_WING.prism(rect(7.85, 8.75, 0.45, 2.55), WY0 - 0.25, WY0 + 0.15)
G["Door"].prism(rect(7.85, 8.75, 0.45, 2.55), WY0 + 0.08, WY0 + 0.12)
for zb, zt in ((0.6, 1.4), (1.55, 2.4)):
    for x0 in (7.95, 8.33):
        G["Door"].prism(rect(x0, x0 + 0.32, zb, zt), WY0 + 0.06, WY0 + 0.08)
for x0, x1, z0, z1 in ((7.75, 7.85, 0.45, 2.63), (8.75, 8.85, 0.45, 2.63), (7.75, 8.85, 2.55, 2.65)):
    G["Sash"].box(x0, x1, WY0 - 0.04, WY0 + 0.02, z0, z1)                      # door casing
# shed hood over door and window (0.6 m deep, at 2.7 m) on two small brackets
G["Slate"].prism([(WY0 + 0.02, 2.95), (WY0 - 0.62, 2.70), (WY0 - 0.62, 2.64), (WY0 + 0.02, 2.89)], WXS + 0.1, WX1 + 0.1,
                 axis="x")
for x in (8.92, WX1 - 0.06):
    G["Sash"].prism([(WY0, 2.66), (WY0 - 0.5, 2.66), (WY0, 2.2)], x - 0.04, x + 0.04, axis="x")
# corner boards (dark trim) and the shed roof
for y in (WY0, WY1):
    G["Sash"].box(WX1 - 0.02, WX1 + 0.04, y - 0.06, y + 0.06, 0.45, wing_top(WX1))
G["Slate"].prism([(WX0 - 0.03, W_HI + 0.12), (WX1 + 0.32, wing_top(WX1 + 0.32) + 0.12),
                  (WX1 + 0.32, wing_top(WX1 + 0.32) + 0.02), (WX0 - 0.03, W_HI + 0.02)], WY0 - 0.32, WY1 + 0.32)
G["Sash"].prism([(WX1 + 0.24, wing_top(WX1 + 0.24) + 0.03), (WX1 + 0.32, wing_top(WX1 + 0.32) + 0.03),
                 (WX1 + 0.32, wing_top(WX1 + 0.32) - 0.15), (WX1 + 0.24, wing_top(WX1 + 0.24) - 0.15)],
                WY0 - 0.32, WY1 + 0.32)                                              # eave fascia

# ---------------------------------------------------------------------------
# Jail yard (low detail): 20 ft rubble stone wall and a two-storey frame building
# ---------------------------------------------------------------------------

YARD_X0, YARD_X1, YARD_Y1, YW, YH = -6.69, 8.75, 36.2, 0.6, 6.1
R = G["RockWall"]
R.box(YARD_X0, YARD_X0 + YW, BACK, YARD_Y1, 0, YH)               # south (Court St) side
R.box(YARD_X0 + YW, YARD_X1 - YW, YARD_Y1 - YW, YARD_Y1, 0, YH)  # west side
R.box(YARD_X1 - YW, YARD_X1, BACK, YARD_Y1, 0, YH)               # north side
R.box(HW, YARD_X1 - YW, BACK, BACK + YW, 0, YH)                  # short return to the body corner
for x0, x1, y0, y1 in ((YARD_X0, YARD_X0 + YW, BACK, YARD_Y1), (YARD_X0 + YW, YARD_X1 - YW, YARD_Y1 - YW, YARD_Y1),
                       (YARD_X1 - YW, YARD_X1, BACK, YARD_Y1), (HW, YARD_X1 - YW, BACK, BACK + YW)):
    G["Brownstone"].box(x0, x1, y0, y1, YH, YH + 0.15)                                             # coping

BY0, BY1, BX0, BX1, BE = 25.79, 30.74, YARD_X0 + YW + 0.05, -0.34, 6.0
BYM = (BY0 + BY1) / 2
G["Clapboard"].box(BX0, BX1, BY0, BY1, 0, BE)
G["Clapboard"].prism([(BY0, BE), (BY1, BE), (BYM, BE + 1.2)], BX0, BX1, axis="x")
for s in (-1, 1):
    ye = BY0 - 0.3 if s < 0 else BY1 + 0.3
    pts = [(ye, BE - 0.17 + 0.1), (BYM, BE + 1.2 + 0.1), (BYM, BE + 1.2), (ye, BE - 0.17)]
    G["Slate"].prism(pts if s < 0 else list(reversed(pts)), BX0 - 0.3, BX1 + 0.3, axis="x")
for i, x in enumerate((-4.6, -2.0)):                             # yard-side windows (dark panes, no cut)
    for z in (1.2, 3.9):
        G["Glass"].box(x - 0.45, x + 0.45, BY1, BY1 + 0.03, z, z + 1.5)
        G["Sash"].box(x - 0.55, x + 0.55, BY1, BY1 + 0.05, z - 0.08, z)

# ---------------------------------------------------------------------------
# Fire-alarm post (map "F.A."), beside the south end of the steps
# ---------------------------------------------------------------------------

FA = (-7.3, -1.0)
A = G["Alarm"]
A.lathe([(0.0, 0.0), (0.16, 0.0), (0.16, 0.08), (0.11, 0.16), (0.075, 0.30), (0.065, 1.05), (0.09, 1.10),
         (0.0, 1.10)], FA[0], FA[1], 0.0, segs=10)
A.box(FA[0] - 0.15, FA[0] + 0.15, FA[1] - 0.11, FA[1] + 0.11, 1.10, 1.48)
A.prism([(FA[0] - 0.19, 1.48), (FA[0] + 0.19, 1.48), (FA[0], 1.62)], FA[1] - 0.14, FA[1] + 0.14)
G["Iron"].box(FA[0] - 0.08, FA[0] + 0.08, FA[1] - 0.115, FA[1] - 0.105, 1.22, 1.38)   # little door on the box

# ---------------------------------------------------------------------------
# Build objects (boolean the cut shells)
# ---------------------------------------------------------------------------


def cut_shell(shell, cutter, name, mat):
    walls = shell.to_object(name, mat, col)
    cutters = cutter.to_object(name + "_Cutters", MATS["Trim"], col)
    mod = walls.modifiers.new("Openings", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    solvers = [i.identifier for i in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items]
    mod.solver = "EXACT" if "EXACT" in solvers else solvers[0]
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


cut_shell(WALLS, CUT, "CH_Walls", MATS["Stucco"])
cut_shell(DRUM, CUT_DRUM, "CH_Drum", MATS["Trim"])
cut_shell(WING, CUT_WING, "CH_Wing", MATS["Clapboard"])
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("CH_" + key, MATS[key], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Courthouse built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)")
# Materials, baked lighting and GLB export: run courthouse_bake.py (it runs this file first).
