"""
wurts_law_office.py - builds the Alexander Wurts (Samuel Southard) Law Office (59 Main St,
Flemington; c. 1811, Greek Revival front c. 1840, as it stood c. 1920) in Blender.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/wurts_law_office.py").read())

Every run deletes and rebuilds the "WurtsLawOffice" collection, so edit the numbers below
and run again. Materials, lightmap bake and GLB export: wurts_law_office_bake.py (runs this
first). Pattern: county_offices.py.

Sources: PLAN.md "Wurts Law Office (59 Main St)" spec and its orchestrator decisions (1921
Sanborn sheet 2; HABS NJ-772-1 east front and NJ-772-2 south side): a 1-storey white frame
office 4.70 x 8.0 m, a 1.6 m deep portico of four square pillars across the whole front,
a deep entablature (architrave, dentil course, frieze with carved wreaths, cornice) around
a flat roof, W-D-W front with dark green shutters and door, clapboard sides, one brick
chimney, a small frame lean-to at the rear. No later T-wing, no sign.

Coordinates (metres, Blender Z-up):
    X  across the front, +X = north, -X = south
    Y  depth: y = 0 is the portico front (pillar front faces / porch edge); the step runs
       out to y = -0.30; the front wall is at y = 1.6, the rear wall at y = 8.0, the
       lean-to reaches y = 9.1.
    Z  up from grade (lawn level).
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".

Five materials only (draw calls): WL_White, WL_Green, WL_Glass, WL_Brick, WL_Grey.
"""

import math
import bpy
import bmesh

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md)
# ---------------------------------------------------------------------------
HW = 2.35              # half width (4.70 m)
FRONT_Y = 1.60         # front wall face (portico 0 ... 1.6)
BACK = 8.00            # rear wall face
FOUND = 0.25           # top of the stone underpinning
PORCH = 0.30           # porch floor
BASE_TOP = 0.40        # top of the base board; clapboard starts here
ARCH_BOT = 3.30        # underside of the architrave = top of the walls = porch ceiling
CLAP = 0.018           # clapboard butt thickness
COURSES = 15           # clapboard courses 0.40 -> 3.30 (0.193 m exposure)
RECESS = 0.22          # openings are shallow recesses this deep
ENT = 0.04             # architrave / frieze face proud of the wall line
PILLAR_X = (-2.16, -0.72, 0.72, 2.16)
WIN_FRONT = (-1.32, 1.32)
WIN_SIDE = (3.32, 6.79)
PILASTER_Y = 4.40

# Lean-to (rear, frame, shed roof falling west)
LT_X0, LT_X1 = -1.35, 1.55
LT_Y1 = 9.10
LT_HI, LT_LO = 2.98, 2.40

# ---------------------------------------------------------------------------
# Materials (plain stand-ins; wurts_law_office_bake.py swaps in the textures)
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
    "White": "#eeebe2",    # all painted wood
    "Green": "#2f3b2c",    # shutters and doors
    "Glass": "#1e2226",
    "Brick": "#8a4a36",    # chimney
    "Grey": "#8a877f",     # porch, step, underpinning, roofs
}
MATS = {k: plain("WL_" + k, c) for k, c in COLOURS.items()}

# ---------------------------------------------------------------------------
# Mesh builder (as in county_offices.py, plus frustum and swept ring)
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
        # axis 'z': outline in the X-Y plane (plan), depth along Z
        if axis == "y":
            return (u, d, v)
        if axis == "x":
            return (d, u, v)
        return (u, v, d)

    def prism(self, pts, d0, d1, axis="y", caps=True):
        """Extrude a 2D outline [(u, v), ...] between depths d0 and d1."""
        bm = self.bm
        a = [bm.verts.new(self._pt(axis, u, d0, v)) for u, v in pts]
        b = [bm.verts.new(self._pt(axis, u, d1, v)) for u, v in pts]
        faces = [bm.faces.new(a), bm.faces.new(list(reversed(b)))] if caps else []
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
        self._closed(faces)

    def box(self, x0, x1, y0, y1, z0, z1):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)

    def frustum(self, cx, cy, hx0, hy0, z0, hx1, hy1, z1):
        """Square/rectangular frustum: half sizes (hx0, hy0) at z0 to (hx1, hy1) at z1."""
        bm = self.bm
        lo = [bm.verts.new((cx + sx * hx0, cy + sy * hy0, z0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        hi = [bm.verts.new((cx + sx * hx1, cy + sy * hy1, z1)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        faces = [bm.faces.new(lo), bm.faces.new(list(reversed(hi)))]
        for i in range(4):
            j = (i + 1) % 4
            faces.append(bm.faces.new([lo[i], lo[j], hi[j], hi[i]]))
        self._closed(faces)

    def ring(self, axis, cu, cv, face, out, profile, major=12):
        """Ring lying in a wall plane, centre (cu, cv): the closed cross-section `profile`
        [(radius, height above the wall face), ...] swept round the centre."""
        bm = self.bm
        rings = []
        for i in range(major):
            a = 2 * math.pi * (i + 0.5) / major
            ca, sa = math.cos(a), math.sin(a)
            rings.append([bm.verts.new(self._pt(axis, cu + rr * ca, face + out * hh, cv + rr * sa))
                          for rr, hh in profile])
        faces = []
        m = len(profile)
        for i in range(major):
            i2 = (i + 1) % major
            for j in range(m):
                j2 = (j + 1) % m
                faces.append(bm.faces.new([rings[i][j], rings[i2][j], rings[i2][j2], rings[i][j2]]))
        self._closed(faces)

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


def spans(a, b, holes):
    """Pieces of the interval a..b that are not inside any (h0, h1) hole."""
    out, cur = [], a
    for h0, h1 in sorted(holes):
        if h1 <= cur or h0 >= b:
            continue
        if h0 > cur:
            out.append((cur, h0))
        cur = max(cur, h1)
    if cur < b:
        out.append((cur, b))
    return out


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


col = fresh_collection("WurtsLawOffice")
G = {k: MB() for k in MATS}      # geometry per material
W = G["White"]
WALLS, CUT = MB(), MB()          # main frame shell, cut by CUT
LEAN, CUT_L = MB(), MB()         # lean-to shell, cut by CUT_L

# Each wall: (axis, base face depth, outward sign, skin = clapboard thickness on the face)
FRONT = ("y", FRONT_Y, -1, 0.0)
REAR = ("y", BACK, 1, CLAP)
SOUTH = ("x", -HW, -1, CLAP)
NORTH = ("x", HW, 1, CLAP)

# ---------------------------------------------------------------------------
# Shells
# ---------------------------------------------------------------------------

# Main body: one closed prism along Y whose X-Z section carries the side clapboard
# (stepped: each course's butt stands CLAP proud and tapers back to the wall line).
EXPO = (ARCH_BOT - BASE_TOP) / COURSES
CZ = [BASE_TOP + EXPO * k for k in range(COURSES + 1)]
right = [(HW, BASE_TOP)]
for k in range(COURSES):
    right += [(HW + CLAP, CZ[k]), (HW, CZ[k + 1])]
left = [(-x, z) for x, z in reversed(right)]
WALLS.prism([(-HW, FOUND), (HW, FOUND)] + right + left, FRONT_Y, BACK)

# Rear clapboard (separate wedges on the rear face; the lean-to hides the middle)
for k in range(COURSES):
    W.prism([(BACK, CZ[k]), (BACK + CLAP, CZ[k]), (BACK, CZ[k + 1])], -HW, HW, axis="x")

# Stone underpinning (grey), 0.2 m hidden skirt below grade
G["Grey"].box(-HW - 0.01, HW + 0.01, FRONT_Y, BACK + 0.01, -0.20, FOUND)

# Base boards: sides, rear, and the front wall either side of the door (above the porch floor)
for s in (-1, 1):
    W.box(*sorted((s * (HW - 0.01), s * (HW + 0.045))), FRONT_Y, BACK + 0.045, FOUND, BASE_TOP)
    W.box(*sorted((s * 0.47, s * HW)), FRONT_Y - 0.025, FRONT_Y + 0.01, PORCH, BASE_TOP)
W.box(-HW - 0.045, HW + 0.045, BACK - 0.01, BACK + 0.045, FOUND, BASE_TOP)

# Corner boards at the rear corners; flat pilaster mid-way along each side (HABS south)
for s in (-1, 1):
    W.box(*sorted((s * (HW - 0.20), s * (HW + 0.045))), BACK - 0.20, BACK + 0.045, BASE_TOP, ARCH_BOT)
    W.box(*sorted((s * (HW - 0.01), s * (HW + 0.045))), PILASTER_Y - 0.10, PILASTER_Y + 0.10, BASE_TOP, ARCH_BOT)

# ---------------------------------------------------------------------------
# Windows, shutters, door
# ---------------------------------------------------------------------------


def head_cap(wall, cu, half, z0):
    """Flat head casing's little cornice cap: a 0.12 band and a projecting 0.03 crown."""
    axis, face, out, skin = wall
    D = lambda k: face + out * k
    W.prism(rect(cu - half - 0.04, cu + half + 0.04, z0, z0 + 0.12), D(-0.01), D(skin + 0.045), axis)
    W.prism(rect(cu - half - 0.06, cu + half + 0.06, z0 + 0.12, z0 + 0.15), D(-0.01), D(skin + 0.07), axis)


def shutter_pair(wall, cu, half, z0, z1):
    """Two open louvred leaves, flat against the wall 0.03 off it: back board, stiles and
    rails, and sloping louvre slats (wedges) in two panels."""
    axis, face, out, skin = wall
    D = lambda k: face + out * k
    S = G["Green"]
    slat_axis = "x" if axis == "y" else "y"
    b0, b1, b2 = D(skin + 0.02), D(skin + 0.04), D(skin + 0.06)
    zm = (z0 + z1) / 2
    for s in (-1, 1):
        u0, u1 = sorted((cu + s * (half + 0.05), cu + s * (half + 0.39)))
        S.prism(rect(u0, u1, z0, z1), b0, b1, axis)                                  # back board
        for a, b in ((u0, u0 + 0.05), (u1 - 0.05, u1)):                              # stiles
            S.prism(rect(a, b, z0, z1), b1, b2, axis)
        for za, zb in ((z0, z0 + 0.07), (zm - 0.03, zm + 0.03), (z1 - 0.06, z1)):    # rails
            S.prism(rect(u0 + 0.05, u1 - 0.05, za, zb), b1, b2, axis)
        for pa, pb in ((z0 + 0.07, zm - 0.03), (zm + 0.03, z1 - 0.06)):              # louvres
            n = max(1, round((pb - pa) / 0.105))
            h = (pb - pa) / n
            for i in range(n):
                zb = pa + h * i
                S.prism([(b1, zb), (b2, zb), (b1, zb + h)], u0 + 0.05, u1 - 0.05, slat_axis)


def window(wall, cu, w=0.78, z0=1.05, z1=2.75, shutters=True, panes=3, cutter=None):
    """6/6 (panes=3) or 2/2 (panes=1) double-hung window in a shallow recess: flat casing
    with a capped head, sill board, white sash and muntins, dark glass, optional shutters."""
    axis, face, out, skin = wall
    D = lambda k: face + out * k
    h = w / 2
    (cutter or CUT).prism(rect(cu - h, cu + h, z0, z1), D(0.25), D(-RECESS), axis)
    G["Glass"].prism(rect(cu - h, cu + h, z0, z1), D(-0.12), D(-0.14), axis)
    # sash: stiles, top/bottom rails, meeting rail
    zm = (z0 + z1) / 2
    for a, b in ((cu - h, cu - h + 0.05), (cu + h - 0.05, cu + h)):
        W.prism(rect(a, b, z0, z1), D(-0.06), D(-0.12), axis)
    for za, zb in ((z0, z0 + 0.08), (z1 - 0.05, z1), (zm - 0.02, zm + 0.02)):
        W.prism(rect(cu - h + 0.05, cu + h - 0.05, za, zb), D(-0.06), D(-0.12), axis)
    # muntins: (panes) x 2 lights per sash
    m = 0.0125
    inner = w - 0.10
    for i in range(1, panes):
        u = cu - h + 0.05 + inner * i / panes
        for za, zb in ((z0 + 0.08, zm - 0.02), (zm + 0.02, z1 - 0.05)):
            W.prism(rect(u - m, u + m, za, zb), D(-0.08), D(-0.12), axis)
    if panes > 1:
        for za, zb in ((z0 + 0.08, zm - 0.02), (zm + 0.02, z1 - 0.05)):
            zc = (za + zb) / 2
            W.prism(rect(cu - h + 0.05, cu + h - 0.05, zc - m, zc + m), D(-0.08), D(-0.12), axis)
    # casing, head cap, sill board
    c = 0.07
    for a, b in ((cu - h - c, cu - h), (cu + h, cu + h + c)):
        W.prism(rect(a, b, z0, z1 + c), D(-0.01), D(skin + 0.025), axis)
    W.prism(rect(cu - h, cu + h, z1, z1 + c), D(-0.01), D(skin + 0.025), axis)
    head_cap(wall, cu, h + c, z1 + c)
    W.prism(rect(cu - h - c - 0.03, cu + h + c + 0.03, z0 - 0.05, z0), D(-0.12), D(skin + 0.05), axis)
    if shutters:
        shutter_pair(wall, cu, h, z0, z1)


DOOR_HEAD_TOP = 2.85    # top of the plain door head board (photo "Dr. Tompkins", PLAN addendum 2026-11-11)
NAME_Z, NAME_W, NAME_H = 2.675, 0.70, 0.13   # "DR. TOMPKINS" board, centred on the head board


def front_door():
    """Centred door: 0.78 x 2.20 opening, half-glazed dark green leaf set 0.10 in (stiles
    and rails, one big light above a mid rail at 1.15 m over the porch floor, one plain
    panel below), flat casing 0.08, a plain head board 2.50-2.85 with the cornice cap on
    top (top 2.95). No fanlight or sidelights. Photo: flmngtnmainstdrtompkinsoffice.jpg."""
    axis, face, out, skin = FRONT
    D = lambda k: face + out * k
    h = 0.39
    z0, z1 = PORCH, 2.50
    CUT.prism(rect(-h, h, z0 - 0.01, z1), D(0.25), D(-RECESS), axis)
    S = G["Green"]
    S.prism(rect(-h, h, z0, z1), D(-0.10), D(-0.14), axis)              # leaf (flat panel field)
    st, mid = 0.12, z0 + 1.15                                            # stile width, mid-rail centre
    for a, b in ((-h, -h + st), (h - st, h)):                            # stiles
        S.prism(rect(a, b, z0, z1), D(-0.085), D(-0.10), axis)
    for za, zb in ((z0, z0 + 0.24), (mid - 0.08, mid + 0.08), (z1 - 0.12, z1)):   # rails
        S.prism(rect(-h + st, h - st, za, zb), D(-0.085), D(-0.10), axis)
    G["Glass"].prism(rect(-h + st, h - st, mid + 0.08, z1 - 0.12), D(-0.093), D(-0.10), axis)  # light
    c = 0.08
    for a, b in ((-h - c, -h), (h, h + c)):
        W.prism(rect(a, b, z0, z1), D(-0.01), D(0.025), axis)
    W.prism(rect(-h - c, h + c, z1, DOOR_HEAD_TOP), D(-0.01), D(0.025), axis)        # head board
    W.prism(rect(-h - c - 0.04, h + c + 0.04, DOOR_HEAD_TOP, 2.92), D(-0.01), D(0.045), axis)
    W.prism(rect(-h - c - 0.06, h + c + 0.06, 2.92, 2.95), D(-0.01), D(0.07), axis)
    # name board (dark) on the head board; its lettering is added below as WL_Letters
    G["Glass"].prism(rect(-NAME_W / 2, NAME_W / 2, NAME_Z - NAME_H / 2, NAME_Z + NAME_H / 2),
                     D(0.02), D(0.04), axis)


front_door()
for x in WIN_FRONT:
    window(FRONT, x)
for wall in (SOUTH, NORTH):
    for y in WIN_SIDE:
        window(wall, y)

# ---------------------------------------------------------------------------
# Porch and step (grey)
# ---------------------------------------------------------------------------

G["Grey"].box(-HW, HW, 0.0, FRONT_Y + 0.01, -0.20, PORCH - 0.03)                 # facing / platform
G["Grey"].box(-HW - 0.03, HW + 0.03, -0.03, FRONT_Y + 0.01, PORCH - 0.03, PORCH)  # deck with nosing
G["Grey"].box(-1.30, 1.30, -0.30, 0.0, -0.20, 0.15)                              # one wide step

# ---------------------------------------------------------------------------
# Pillars and antae (square, plain shafts, stepped capitals)
# ---------------------------------------------------------------------------


def square_order(cx, cy, hx, hy, z_base):
    """Plinth, shaft, necking, flared echinus, abacus around a shaft of half sizes hx, hy."""
    W.frustum(cx, cy, hx + 0.04, hy + 0.04, z_base, hx + 0.04, hy + 0.04, 0.42)    # plinth
    W.frustum(cx, cy, hx + 0.02, hy + 0.02, 0.42, hx, hy, 0.46)                    # base fillet
    W.frustum(cx, cy, hx, hy, 0.46, hx, hy, 3.08)                                  # shaft
    W.frustum(cx, cy, hx + 0.01, hy + 0.01, 3.08, hx + 0.01, hy + 0.01, 3.12)      # necking band
    W.frustum(cx, cy, hx + 0.01, hy + 0.01, 3.12, hx + 0.04, hy + 0.04, 3.22)      # echinus
    W.frustum(cx, cy, hx + 0.06, hy + 0.06, 3.22, hx + 0.06, hy + 0.06, ARCH_BOT)  # abacus


for x in PILLAR_X:
    square_order(x, 0.19, 0.19, 0.19, PORCH)
# antae: corner pilasters on the front-wall corners, 0.24 on both faces, 0.04 proud
for s in (-1, 1):
    x0, x1 = HW - 0.24, HW + 0.04
    y0, y1 = FRONT_Y - 0.04, FRONT_Y + 0.24
    square_order(s * (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, FOUND)

# ---------------------------------------------------------------------------
# Entablature: architrave, dentil course, frieze with wreaths, cornice (plan slabs)
# ---------------------------------------------------------------------------


def slab(p_side, p_front, p_rear, z0, z1, mb=W):
    mb.prism(rect(-HW - p_side, HW + p_side, -p_front, BACK + p_rear), z0, z1, axis="z")


slab(ENT, 0.02, ENT, ARCH_BOT, 3.52)          # architrave (plain fascia); underside = porch ceiling
slab(ENT, 0.02, ENT, 3.52, 3.61)              # dentil band
slab(ENT + 0.06, 0.08, ENT, 3.61, 3.64)       # fillet over the dentils
slab(ENT, 0.02, ENT, 3.64, 4.06)              # frieze
slab(0.14, 0.12, 0.12, 4.06, 4.14)            # bed moulding
slab(0.32, 0.30, 0.20, 4.14, 4.32)            # corona (0.30 overhang front and sides)
# top moulding: a 0.10 parapet lip round the flat roof
po, pf, pr, wl = 0.29, 0.27, 0.17, 0.25
W.prism(rect(-HW - po, HW + po, -pf, -pf + wl), 4.32, 4.42, axis="z")
W.prism(rect(-HW - po, HW + po, BACK + pr - wl, BACK + pr), 4.32, 4.42, axis="z")
for s in (-1, 1):
    W.prism(rect(*sorted((s * (HW + po), s * (HW + po - wl))), -pf + wl, BACK + pr - wl), 4.32, 4.42, axis="z")
# flat tin roof deck, slight fall to the rear (kept above the corona top), inside the lip
G["Grey"].prism([(-pf + wl - 0.01, 4.20), (BACK + pr - wl + 0.01, 4.20), (BACK + pr - wl + 0.01, 4.34),
                 (-pf + wl - 0.01, 4.40)], -HW - po + wl - 0.01, HW + po - wl + 0.01, axis="x")

# Dentils: 0.07 wide, 0.05 deep at 0.12 centres, front and both sides
n_front = int((2 * HW) / 0.12)
for i in range(n_front):
    x = -0.12 * (n_front - 1) / 2 + 0.12 * i
    W.box(x - 0.035, x + 0.035, -0.07, -0.02, 3.52, 3.61)
n_side = int(BACK / 0.12)
for s in (-1, 1):
    for i in range(n_side):
        y = 0.04 + 0.12 * i
        W.box(*sorted((s * (HW + ENT), s * (HW + ENT + 0.05))), y - 0.035, y + 0.035, 3.52, 3.61)

# Wreaths: ring 0.34 across, ~0.07 band with a ridge 0.05 proud of the frieze,
# centred at 3.85; the back lies on the frieze face (hidden, removed by the bake; not 5 mm
# inside it, or the bake's bisect planes along the frieze face would cut every ring)
WZ = 3.85
WREATH = [(0.100, 0.0), (0.135, 0.05), (0.170, 0.0)]
for i in range(7):
    W.ring("y", -2.16 + 0.72 * i, WZ, -0.02, -1, WREATH)
for s in (-1, 1):
    for i in range(9):
        W.ring("x", 0.35 + 0.8875 * i, WZ, s * (HW + ENT), s, WREATH)

# ---------------------------------------------------------------------------
# Chimney: brick, south of centre, corbelled cap
# ---------------------------------------------------------------------------

G["Brick"].box(-1.30, -0.70, 4.05, 4.75, 4.25, 6.35)
G["Brick"].box(-1.35, -0.65, 4.00, 4.80, 6.35, 6.50)

# ---------------------------------------------------------------------------
# Rear lean-to: frame, clapboard, shed roof falling west, door south, small window west
# ---------------------------------------------------------------------------

LT_SLOPE = (LT_HI - LT_LO) / (LT_Y1 - BACK)
LEAN.prism([(BACK - 0.05, FOUND), (LT_Y1, FOUND), (LT_Y1, LT_LO), (BACK - 0.05, LT_HI + 0.05 * LT_SLOPE)],
           LT_X0, LT_X1, axis="x")
G["Grey"].box(LT_X0 - 0.01, LT_X1 + 0.01, BACK, LT_Y1 + 0.01, -0.20, FOUND)
LT_DOOR_Y, LT_DOOR_W, LT_DOOR_TOP = 8.55, 0.75, 2.20
LT_WIN_X, LT_WIN_W, LT_WIN_Z = 0.10, 0.60, (1.20, 2.00)
L_SOUTH = ("x", LT_X0, -1, CLAP)
L_NORTH = ("x", LT_X1, 1, CLAP)
L_REAR = ("y", LT_Y1, 1, CLAP)
n_lt = 11
lz = [FOUND + (LT_LO - FOUND) * k / n_lt for k in range(n_lt + 1)]
for k in range(n_lt):
    z0, z1 = lz[k], lz[k + 1]
    door_hole = [(LT_DOOR_Y - LT_DOOR_W / 2 - 0.07, LT_DOOR_Y + LT_DOOR_W / 2 + 0.07)] if z0 < LT_DOOR_TOP + 0.22 else []
    for a, b in spans(BACK, LT_Y1 - 0.12, door_hole):          # south side (door)
        W.prism([(LT_X0, z0), (LT_X0 - CLAP, z0), (LT_X0, z1)], a, b, axis="y")
    W.prism([(LT_X1, z0), (LT_X1 + CLAP, z0), (LT_X1, z1)], BACK, LT_Y1 - 0.12, axis="y")   # north side
    win_hole = [(LT_WIN_X - LT_WIN_W / 2 - 0.10, LT_WIN_X + LT_WIN_W / 2 + 0.10)] \
        if (z1 > LT_WIN_Z[0] - 0.05 and z0 < LT_WIN_Z[1] + 0.22) else []
    for a, b in spans(LT_X0 + 0.12, LT_X1 - 0.12, win_hole):   # rear (west) face
        W.prism([(LT_Y1, z0), (LT_Y1 + CLAP, z0), (LT_Y1, z1)], a, b, axis="x")
for xs in (LT_X0, LT_X1):                                     # corner boards
    s = 1 if xs > 0 else -1
    W.box(*sorted((xs - s * 0.14, xs + s * 0.04)), LT_Y1 - 0.14, LT_Y1 + 0.04, FOUND, LT_LO)
# shed roof (grey), 0.15 overhang at the sides and eaves
def lt_roof_z(y):
    return LT_HI + 0.06 - LT_SLOPE * (y - BACK)


G["Grey"].prism([(BACK - 0.08, lt_roof_z(BACK - 0.08)), (LT_Y1 + 0.18, lt_roof_z(LT_Y1 + 0.18)),
                 (LT_Y1 + 0.18, lt_roof_z(LT_Y1 + 0.18) + 0.06), (BACK - 0.08, lt_roof_z(BACK - 0.08) + 0.06)],
                LT_X0 - 0.15, LT_X1 + 0.15, axis="x")
# lean-to door (south face): plain board door with a casing
a_, f_, o_, sk_ = L_SOUTH
D = lambda k: f_ + o_ * k
CUT_L.prism(rect(LT_DOOR_Y - LT_DOOR_W / 2, LT_DOOR_Y + LT_DOOR_W / 2, FOUND - 0.01, LT_DOOR_TOP), D(0.25), D(-0.15), "x")
G["Green"].prism(rect(LT_DOOR_Y - LT_DOOR_W / 2, LT_DOOR_Y + LT_DOOR_W / 2, FOUND, LT_DOOR_TOP), D(-0.08), D(-0.11), "x")
for zb, zt in ((FOUND + 0.15, 1.10), (1.25, LT_DOOR_TOP - 0.12)):
    G["Green"].prism(rect(LT_DOOR_Y - 0.26, LT_DOOR_Y + 0.26, zb, zt), D(-0.07), D(-0.08), "x")
for a, b in ((LT_DOOR_Y - LT_DOOR_W / 2 - 0.07, LT_DOOR_Y - LT_DOOR_W / 2), (LT_DOOR_Y + LT_DOOR_W / 2, LT_DOOR_Y + LT_DOOR_W / 2 + 0.07)):
    W.prism(rect(a, b, FOUND, LT_DOOR_TOP + 0.07), D(-0.01), D(sk_ + 0.025), "x")
W.prism(rect(LT_DOOR_Y - LT_DOOR_W / 2, LT_DOOR_Y + LT_DOOR_W / 2, LT_DOOR_TOP, LT_DOOR_TOP + 0.07), D(-0.01), D(sk_ + 0.025), "x")
# lean-to window (west face): small 2/2, no shutters, no cap
window(L_REAR, LT_WIN_X, w=LT_WIN_W, z0=LT_WIN_Z[0], z1=LT_WIN_Z[1], shutters=False, panes=2, cutter=CUT_L)

# ---------------------------------------------------------------------------
# Build objects (boolean the cut shells)
# ---------------------------------------------------------------------------


def cut_shell(shell, cutter, name, mat):
    walls = shell.to_object(name, mat, col)
    cutters = cutter.to_object(name + "_Cutters", mat, col)
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


cut_shell(WALLS, CUT, "WL_Walls", MATS["White"])
cut_shell(LEAN, CUT_L, "WL_LeanTo", MATS["White"])
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("WL_" + key, MATS[key], col)
    else:
        builder.bm.free()

# Lettering "DR. TOMPKINS" (light capitals on the dark name board over the door; the only
# lettering on the building, as in the photo). Text is scaled to fill the board's width.
_curve = bpy.data.curves.new("WL_NameText", "FONT")
_curve.body = "DR. TOMPKINS"
_curve.align_x = "CENTER"
_curve.align_y = "CENTER"
_curve.size = 0.10
_curve.extrude = 0.004
_curve.resolution_u = 3          # coarse curves: the letters are 6 cm tall
_text = bpy.data.objects.new("WL_NameText_tmp", _curve)
col.objects.link(_text)
_text.rotation_euler = (math.radians(90), 0, 0)
_dg = bpy.context.evaluated_depsgraph_get()
letters = bpy.data.meshes.new_from_object(_text.evaluated_get(_dg))
bpy.data.objects.remove(_text, do_unlink=True)
bpy.data.curves.remove(_curve)
_xs = [v.co.x for v in letters.vertices]
_ys = [v.co.y for v in letters.vertices]
_fit = min((NAME_W - 0.07) / (max(_xs) - min(_xs)), (NAME_H - 0.05) / (max(_ys) - min(_ys)))
_cx, _cy = (max(_xs) + min(_xs)) / 2, (max(_ys) + min(_ys)) / 2
for v in letters.vertices:          # local text plane (x, y), extrude along z -> world
    x, y, z = v.co
    v.co = ((x - _cx) * _fit, FRONT_Y - 0.04 - 0.004 + z * -1.0, NAME_Z + (y - _cy) * _fit)
letters.name = "WL_Letters"
_bm = bmesh.new()                   # text faces can come out pointing inward: make every
_bm.from_mesh(letters)              # letter solid face outward, then drop the back caps that
bmesh.ops.recalc_face_normals(_bm, faces=_bm.faces[:])   # lie on the board
_bm.normal_update()
_caps = [f for f in _bm.faces if abs(f.normal.y) > 0.5]
_back = [f for f in _caps if f.calc_center_median().y > FRONT_Y - 0.044]
bmesh.ops.reverse_faces(_bm, faces=[f for f in _caps if f not in _back and f.normal.y > 0])
bmesh.ops.delete(_bm, geom=_back, context="FACES")
_bm.to_mesh(letters)
_bm.free()
letters.materials.clear()
letters.materials.append(MATS["White"])
col.objects.link(bpy.data.objects.new("WL_Letters", letters))

tris =sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Wurts Law Office built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)")
# Materials, baked lighting and GLB export: run wurts_law_office_bake.py (it runs this file first).
