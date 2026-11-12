"""
house_91_93.py - builds 91-93 Main St, Flemington (west side, old no. 505): a mid-19th-century
2 1/2-storey frame house used as offices in 1921 ("OFF."), with a narrower 2-storey dwelling
ell ("D", no. 93) on its south side, a rear wing and a 1-storey rear part (PLAN.md "91-93 Main
St: frame house used as offices ("Off.") with a dwelling ell ("D")").

Evidence: 1921 Sanborn sheet 3 footprints and storeys (MAP; same in 1910 and 1948); the 1980
National Register text "2 1/2-story, frame, mid-19th Century ... cross-gable, metal roof.
Modillions decorate the eaves" (TEXT). No photo exists: everything else is a plain GUESS (owner
go-ahead 2026-11-12 with the recommended choices: plain front, porch across the front,
cross-gabled metal roof with small modillion blocks, two plain windows per floor on the north
side wall, white-cream paint; no sign, no lettering).

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/house_91_93.py").read())

Every run deletes and rebuilds the "House9193" collection. Materials, lightmap bake and GLB
export: house_91_93_bake.py (runs this file first). Pattern: store_79.py (one builder per
material, Wall frames, closed wall shells cut by boolean pockets, section-E window backs).

Windows (PLAN.md section E): every pane is ONE glass face (builder Glass -> material `glass`)
4 cm in front of a window back showing a cell of assets/textures/shared/window_backs.jpg
(builder WBack): offices in the front block (half-drawn blinds, one dark room), lace and
curtains in the dwelling ell. BACKREC[rid] -> UV record (read by the bake).

Coordinates (metres, Blender Z-up), origin = scene (-13.18, 0.02, 38.63) = centre of the porch
front at lawn level, rotation 0 90 0:
    X  along Main St, +X = north (83-87's yard), -X = south (95-97)
    Y  depth: y = 0 is the porch front; the steps run out to -0.60; main front wall 2.19
    Z  up from the lawn; foundations reach down to -0.20
Scene: world x = -13.18 - Y, world z = 38.63 - X.
"""

import json
import math
import random
import bpy
import bmesh

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md massing table; X, Y = MAP, heights GUESS)
# ---------------------------------------------------------------------------
HW = 3.78                       # half front of the main block A (7.55 m)
YF, YA = 2.19, 10.47            # A front / rear wall
YR_A = (YF + YA) / 2            # A ridge line (6.33)
FT = 0.40                       # foundation top = bottom of the clapboard shells
FLOOR = 0.45                    # floors and porch decks
SKIRT = -0.20
TP = math.tan(math.radians(35.0))
RIDGE_A = 9.45
SLAB = 0.12                     # roof slab thickness (vertical)
OV, RK = 0.30, 0.25             # eave overhang, rake overhang
RET = 0.45                      # cornice returns on the gable walls
FRZ0 = 6.00                     # frieze bottom on A (soffit 6.18)
XG, PEAK_X = 1.60, 9.00         # front cross gable: half width, peak
KX = (PEAK_X - 6.55) / XG       # its slope (56.9 deg)
RKX = 0.25                      # its rake overhang (front)
# ell B (no. 93)
BX0, BX1, BY0, BY1 = -7.27, -HW, 3.93, 10.32
BXC = (BX0 + BX1) / 2
B_EAVE, B_RIDGE = 6.25, 8.00
KB = (B_RIDGE - B_EAVE) / (BXC - BX0)
FRZ0_B = 5.62
# rear wing C, rear part D, wing porch C2
CX0, CX1, CY1 = -3.67, 1.28, 17.51
CXC = (CX0 + CX1) / 2
C_EAVE, C_RIDGE = 6.00, 7.60
KC = (C_RIDGE - C_EAVE) / (CX1 - CXC)
DX1, DY1 = 2.63, 19.33
D_HI, D_LO = 3.20, 2.85
C2Y1 = 15.94
# porches
P1_FRONT, P1_WALL = 3.36, 3.66          # P1 roof top at the front edge / at the wall
P2X0, P2Y0 = -6.90, 2.13
P2_FRONT, P2_WALL = 3.16, 3.46
C2_OUT, C2_WALL = 3.06, 3.36
POST = 0.14
CB_W, CB_T = 0.15, 0.025        # corner boards
WT = 0.60                       # water table top
CHIMS = ((-2.65, -2.15, 6.10, 6.56, 9.0, 10.30), (CXC - 0.22, CXC + 0.22, 16.30, 16.74, 7.2, 8.50))


def zA(y):
    """Top of A's roof (both slopes) at depth y."""
    return RIDGE_A - abs(y - YR_A) * TP


def zX(x):
    """Top of the cross-gable roof at x."""
    return PEAK_X - abs(x) * KX


def zB(x):
    return B_RIDGE - abs(x - BXC) * KB


def zC(x):
    return C_RIDGE - abs(x - CXC) * KC


def zD(y):
    return D_HI - (y - CY1) * (D_HI - D_LO) / (DY1 - CY1)


def zP1(y):
    return P1_FRONT + (P1_WALL - P1_FRONT) * y / YF


def zP2(y):
    return P2_FRONT + (P2_WALL - P2_FRONT) * (y - P2Y0) / (BY0 - P2Y0)


def zC2(x):
    return C2_WALL - (C2_WALL - C2_OUT) * (x - CX1) / (DX1 - CX1)


# ---------------------------------------------------------------------------
# Materials (plain stand-ins; house_91_93_bake.py swaps in the textures)
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


COLOURS = {"Clap": "#E3DED0", "Trim": "#DDD5C2", "Door": "#3A2A1F", "Roof": "#5A3D34", "Brick": "#8A4A36",
           "Glass": "#1A1916", "WBack": "#2A2420"}
MATS = {k: plain("H91_" + k, c) for k, c in COLOURS.items()}
# builder -> material (Deck = painted grey porch floors and steps: trim paint, grey tint in the bake)
BUILDER_MAT = {k: k for k in COLOURS}
BUILDER_MAT["Deck"] = "Trim"


# ---------------------------------------------------------------------------
# Mesh builder (as store_79.py)
# ---------------------------------------------------------------------------
class Wall:
    """A vertical wall plane: p0 (x, y) on the face, n = unit outward normal, t = (-n.y, n.x)
    runs to the right as seen from outside. Wall coordinates: u along t, z up, d outward."""

    def __init__(self, p0, n, cut=None):
        self.p0, self.n, self.cut = p0, n, cut
        self.t = (-n[1], n[0])

    def pt(self, u, z, d):
        return (self.p0[0] + self.t[0] * u + self.n[0] * d,
                self.p0[1] + self.t[1] * u + self.n[1] * d, z)


class MB:
    """Collects closed solids for one builder. Faces get the current `rid` (back record)."""

    def __init__(self):
        self.bm = bmesh.new()
        self.rid_layer = self.bm.faces.layers.int.new("rid")
        self.rid = 0

    def _closed(self, faces):
        for f in faces:
            f[self.rid_layer] = self.rid
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)

    @staticmethod
    def _pt(axis, u, d, v):
        if axis == "y":
            return (u, d, v)
        if axis == "x":
            return (d, u, v)
        return (u, v, d)

    def _extrude(self, a_co, b_co):
        bm = self.bm
        a = [bm.verts.new(c) for c in a_co]
        b = [bm.verts.new(c) for c in b_co]
        faces = [bm.faces.new(a), bm.faces.new(list(reversed(b)))]
        n = len(a)
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
        self._closed(faces)

    def prism(self, pts, d0, d1, axis="y"):
        self._extrude([self._pt(axis, u, d0, v) for u, v in pts],
                      [self._pt(axis, u, d1, v) for u, v in pts])

    def box(self, x0, x1, y0, y1, z0, z1):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)

    def wprism(self, wall, pts, d0, d1):
        self._extrude([wall.pt(u, z, d0) for u, z in pts], [wall.pt(u, z, d1) for u, z in pts])

    def wbox(self, wall, u0, u1, z0, z1, d0, d1):
        self.wprism(wall, rect(u0, u1, z0, z1), d0, d1)

    def solid(self, cos, faces_idx):
        vs = [self.bm.verts.new(c) for c in cos]
        self._closed([self.bm.faces.new([vs[i] for i in f]) for f in faces_idx])

    def slab(self, plan, ztop, t=SLAB):
        """Roof slab: plan outline (x, y) (convex), top surface z = ztop(x, y), t thick."""
        n = len(plan)
        cos = [(x, y, ztop(x, y)) for x, y in plan] + [(x, y, ztop(x, y) - t) for x, y in plan]
        faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
        faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        self.solid(cos, faces)

    def rings(self, rings):
        """Closed tube through rings of points (same length), capped at both ends."""
        bm = self.bm
        vs = [[bm.verts.new(c) for c in r] for r in rings]
        faces = []
        n = len(rings[0])
        for a, b in zip(vs[:-1], vs[1:]):
            for i in range(n):
                j = (i + 1) % n
                faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
        faces.append(bm.faces.new(vs[0]))
        faces.append(bm.faces.new(list(reversed(vs[-1]))))
        self._closed(faces)

    def quad(self, wall, u0, u1, z0, z1, d):
        """ONE single-sided face on a wall plane (d out from the wall face), facing outward."""
        vs = [self.bm.verts.new(wall.pt(u, z, d)) for u, z in ((u0, z0), (u1, z0), (u1, z1), (u0, z1))]
        f = self.bm.faces.new(vs)
        f[self.rid_layer] = self.rid
        return f

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


def sweep_plan(mb, path, profile):
    """Moulding swept along a plan polyline (mitred corners). profile: closed outline of
    (d, z), d = distance out from the path (outward = right of travel)."""
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
    mb.rings(rings)


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


col = fresh_collection("House9193")
G = {k: MB() for k in BUILDER_MAT}
CL, TR, DR, R, BR, GL, WB, DK = (G[k] for k in ("Clap", "Trim", "Door", "Roof", "Brick", "Glass", "WBack", "Deck"))
# wall shells (closed solids, clapboard) and their cutters
SHELLS = {k: (MB(), MB()) for k in ("ShellA", "ShellX", "ShellB", "ShellC", "ShellD")}
(SA, KA), (SX, KXc), (SB, KBc), (SC, KCc), (SD, KDc) = SHELLS.values()

FRONT = Wall((0.0, YF), (0, -1), KA)            # u = X
NORTH = Wall((HW, 0.0), (1, 0), KA)             # u = Y
GABLE = Wall((0.0, YF), (0, -1), KXc)           # cross gable, u = X
B_FRONT = Wall((0.0, BY0), (0, -1), KBc)        # ell front, u = X
B_REAR = Wall((0.0, BY1), (0, 1), KBc)          # ell rear, u = -X
C_NORTH = Wall((CX1, 0.0), (1, 0), KCc)         # wing north (under its porch), u = Y
D_REAR = Wall((0.0, DY1), (0, 1), KDc)          # rear part, u = -X

# ---------------------------------------------------------------------------
# Window backs (section E)
# ---------------------------------------------------------------------------
WB_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\window_backs.json"))["cells"]
GAP = 0.04
BACKREC = {}


def crop_uv(uv, aspect):
    """Centred crop of an atlas rectangle to aspect w/h (rooms not stretched), 1.5 px inset."""
    U0, V0, U1, V1 = uv
    e = 1.5 / 1024
    U0, V0, U1, V1 = U0 + e, V0 + e, U1 - e, V1 - e
    a = (U1 - U0) / (V1 - V0)
    if aspect < a:
        w, c = (U1 - U0) * aspect / a, (U0 + U1) / 2
        U0, U1 = c - w / 2, c + w / 2
    else:
        h, c = (V1 - V0) * a / aspect, (V0 + V1) / 2
        V0, V1 = c - h / 2, c + h / 2
    return (U0, V0, U1, V1)


def back(wall, u0, u1, z0, z1, d, cell, flip=False):
    rid = len(BACKREC) + 1
    U0, V0, U1, V1 = crop_uv(WB_CELLS[cell]["uv"], (u1 - u0) / (z1 - z0))
    if flip:
        U0, U1 = U1, U0
    BACKREC[rid] = dict(wall=(wall.p0, wall.n), u0=u0, u1=u1, z0=z0, z1=z1, uv=(U0, V0, U1, V1))
    WB.rid = rid
    WB.quad(wall, u0, u1, z0, z1, d)
    WB.rid = 0


def pane(wall, u0, u1, z0, z1, d_glass, cell, flip=False):
    """Glass face at depth d_glass with its window back GAP behind it."""
    back(wall, u0, u1, z0, z1, d_glass - GAP, cell, flip)
    GL.quad(wall, u0, u1, z0, z1, d_glass)


# ---------------------------------------------------------------------------
# Shells (one closed solid per mass, bottoms on the foundations at FT)
# ---------------------------------------------------------------------------
SA.prism([(YF, FT), (YA, FT), (YA, zA(YA) - SLAB), (YR_A, RIDGE_A - SLAB), (YF, zA(YF) - SLAB)], -HW, HW, "x")
SX.prism([(-XG, zX(XG) - SLAB), (XG, zX(XG) - SLAB), (0.0, PEAK_X - SLAB)], YF, 5.2, "y")
SB.prism([(BX0, FT), (BX1, FT), (BX1, zB(BX1) - SLAB), (BXC, B_RIDGE - SLAB), (BX0, zB(BX0) - SLAB)], BY0, BY1, "y")
SC.prism([(CX0, FT), (CX1, FT), (CX1, zC(CX1) - SLAB), (CXC, C_RIDGE - SLAB), (CX0, zC(CX0) - SLAB)], YA - 0.05, CY1, "y")
SD.prism([(CY1 - 0.05, FT), (DY1, FT), (DY1, zD(DY1) - SLAB), (CY1 - 0.05, zD(CY1 - 0.05) - SLAB)], CX0, DX1, "x")

# brick foundations, 2 cm proud of the clapboard
o = 0.02
BR.box(-HW - o, HW + o, YF - o, YA + o, SKIRT, FT)
BR.box(BX0 - o, BX1, BY0 - o, BY1 + o, SKIRT, FT)
BR.box(CX0 - o, CX1 + o, YA, CY1, SKIRT, FT)
BR.box(CX0 - o, DX1 + o, CY1, DY1 + o, SKIRT, FT)


# ---------------------------------------------------------------------------
# Double-hung window (6/6 by default): cased opening, frame, dark sashes, sill and apron
# ---------------------------------------------------------------------------
def window(wall, cu, z0, z1, cell, w=0.85, lites=(3, 2), flip=False, head=0.12):
    hw = w / 2
    u0, u1 = cu - hw, cu + hw
    wall.cut.wbox(wall, u0, u1, z0, z1, 0.25, -0.22)                     # opening
    TR.wbox(wall, u0, u0 + 0.05, z0, z1, -0.22, 0.0)                     # frame lining
    TR.wbox(wall, u1 - 0.05, u1, z0, z1, -0.22, 0.0)
    TR.wbox(wall, u0 + 0.05, u1 - 0.05, z1 - 0.05, z1, -0.22, 0.0)
    TR.wbox(wall, u0 + 0.05, u1 - 0.05, z0, z0 + 0.04, -0.22, 0.0)
    a, b = u0 + 0.05, u1 - 0.05
    g0, g1 = z0 + 0.04, z1 - 0.05
    pane(wall, a, b, g0, g1, -0.13, cell, flip)
    zm = (g0 + g1) / 2
    # sashes: stiles, top / meeting / bottom rails
    DR.wbox(wall, a, a + 0.045, g0, g1, -0.115, -0.045)
    DR.wbox(wall, b - 0.045, b, g0, g1, -0.115, -0.045)
    DR.wbox(wall, a + 0.045, b - 0.045, g1 - 0.055, g1, -0.115, -0.045)
    DR.wbox(wall, a + 0.045, b - 0.045, zm - 0.025, zm + 0.025, -0.115, -0.04)
    DR.wbox(wall, a + 0.045, b - 0.045, g0, g0 + 0.075, -0.115, -0.07)
    # muntins: lites[0] panes across, lites[1] panes up per sash
    nx, ny = lites
    ia, ib = a + 0.045, b - 0.045
    for k in range(1, nx):
        x = ia + (ib - ia) * k / nx
        DR.wbox(wall, x - 0.011, x + 0.011, g0 + 0.075, g1 - 0.055, -0.105, -0.075)
    for s0, s1 in ((g0 + 0.075, zm - 0.025), (zm + 0.025, g1 - 0.055)):
        for k in range(1, ny):
            z = s0 + (s1 - s0) * k / ny
            DR.wbox(wall, ia, ib, z - 0.011, z + 0.011, -0.105, -0.075)
    # casing: side boards, head board with a drip cap; sill and apron
    TR.wbox(wall, u0 - 0.10, u0, z0, z1, 0.0, 0.025)
    TR.wbox(wall, u1, u1 + 0.10, z0, z1, 0.0, 0.025)
    TR.wbox(wall, u0 - 0.10, u1 + 0.10, z1, z1 + head, 0.0, 0.03)
    TR.wbox(wall, u0 - 0.13, u1 + 0.13, z1 + head, z1 + head + 0.03, 0.0, 0.06)
    TR.wbox(wall, u0 - 0.14, u1 + 0.14, z0 - 0.045, z0, -0.03, 0.065)
    TR.wbox(wall, u0 - 0.08, u1 + 0.08, z0 - 0.15, z0 - 0.045, 0.0, 0.02)


def door(wall, cu, w, z0, h, transom=0.0, cell="dark_room", plank=False):
    """Cased 4-panel door (or a plain batten door) with an optional transom light above."""
    u0, u1 = cu - w / 2, cu + w / 2
    top = z0 + h + (transom + 0.06 if transom else 0.0)
    wall.cut.wbox(wall, u0, u1, z0 - 0.05, top, 0.25, -0.20)
    TR.wbox(wall, u0, u0 + 0.05, z0, top, -0.20, 0.0)                    # jamb linings
    TR.wbox(wall, u1 - 0.05, u1, z0, top, -0.20, 0.0)
    TR.wbox(wall, u0 + 0.05, u1 - 0.05, top - 0.05, top, -0.20, 0.0)
    TR.wbox(wall, u0 - 0.03, u1 + 0.03, z0 - 0.05, z0 + 0.02, -0.20, 0.05)    # threshold
    a, b = u0 + 0.05, u1 - 0.05
    DR.wbox(wall, a, b, z0 + 0.02, z0 + h, -0.15, -0.11)                  # leaf
    if plank:
        for z in (z0 + 0.25, z0 + h / 2, z0 + h - 0.30):
            DR.wbox(wall, a + 0.05, b - 0.05, z, z + 0.12, -0.11, -0.095)   # battens
    else:
        pw = (b - a - 0.30) / 2
        for p0, p1 in ((z0 + 0.20, z0 + 0.95), (z0 + 1.15, z0 + h - 0.18)):
            for k in range(2):
                pa = a + 0.10 + k * (pw + 0.10)
                DR.wbox(wall, pa, pa + pw, p0, p1, -0.11, -0.095)          # raised panels
    if transom:
        TR.wbox(wall, a, b, z0 + h, z0 + h + 0.06, -0.20, -0.02)            # transom bar
        pane(wall, a, b, z0 + h + 0.06, top - 0.05, -0.12, cell)
    TR.wbox(wall, u0 - 0.11, u0, z0 - 0.02, top, 0.0, 0.03)                # casing
    TR.wbox(wall, u1, u1 + 0.11, z0 - 0.02, top, 0.0, 0.03)
    TR.wbox(wall, u0 - 0.11, u1 + 0.11, top, top + 0.14, 0.0, 0.035)
    TR.wbox(wall, u0 - 0.14, u1 + 0.14, top + 0.14, top + 0.17, 0.0, 0.07)


# --- openings (GUESS, plain; spec elevation details) ---------------------------------------
GF = (1.30, 3.10)               # ground-floor windows of A (sill, head)
UF = (4.30, 5.82)               # upper windows of A (spec 5.90: lowered so the heads clear the frieze)
for u, c in ((-2.40, "blind_cream_half"), (2.40, "blind_green_half")):
    window(FRONT, u, *GF, c, w=0.90)
for u, c, f in ((-2.40, "dark_room", False), (0.0, "blind_cream_high", False), (2.40, "blind_cream_half", True)):
    window(FRONT, u, *UF, c, flip=f)
door(FRONT, 0.0, 0.95, FLOOR, 2.25, transom=0.30, cell="dark_room_frame")
window(GABLE, 0.0, 6.75, 7.70, "dark_room_frame", w=0.70, lites=(2, 2))       # attic (spec 1.10 tall; rakes)
for u, (cg, cu_) in zip((4.5, 8.5), (("blind_cream_low", "blind_cream_half"), ("blind_green_half", "blind_cream_high"))):
    window(NORTH, u, *GF, cg, w=0.90)
    window(NORTH, u, *UF, cu_)
# ell (dwelling): door and window under its porch, one window above
door(B_FRONT, -4.55, 0.90, FLOOR, 2.20)
window(B_FRONT, -6.30, 1.20, 2.90, "lace_blind_cream")
window(B_FRONT, -5.50, 4.00, 5.40, "lace")
# rear doors (GUESS): ell rear, rear part, the wing under its north porch (+ one window)
door(B_REAR, 5.50, 0.85, FLOOR, 2.05, plank=True)
door(D_REAR, -0.20, 0.85, FLOOR, 2.05, plank=True)
door(C_NORTH, 12.40, 0.85, FLOOR, 2.10)
window(C_NORTH, 14.40, 1.25, 2.75, "curtains_beige", lites=(2, 2))

# ---------------------------------------------------------------------------
# Roofs (tin, N80 "metal roof"): A side gable with the front cross gable, B gable to the street,
# C gable running back, D shed; ridge rolls; boxed cornices with modillions on A and B
# ---------------------------------------------------------------------------
yv0 = YF + (PEAK_X - zA(YF)) / TP          # valley of the cross gable at x = 0 (5.69)
EF = YF - OV - 0.02                         # front / rear eave edges (2 cm drip past the fascia)
ER = YA + OV + 0.02
for s in (-1, 1):
    # A front slope, either side of the cross gable; rear slope in one piece
    x0, x1 = sorted((s * XG, s * (HW + RK)))
    R.slab([(x0, EF), (x1, EF), (x1, YR_A), (x0, YR_A)], lambda x, y: zA(y))
    # A front slope behind the cross gable (above its valleys)
    x0, x1 = sorted((0.0, s * XG))
    pts = [(s * XG, YF), (0.0, yv0), (0.0, YR_A), (s * XG, YR_A)]
    R.slab(pts if s > 0 else pts[::-1], lambda x, y: zA(y))
    # cross-gable slopes
    pts = [(0.0, YF - RKX), (s * XG, YF - RKX), (s * XG, YF), (0.0, yv0)]
    R.slab(pts if s < 0 else pts[::-1], lambda x, y: zX(x))
R.slab([(-HW - RK, YR_A), (HW + RK, YR_A), (HW + RK, ER), (-HW - RK, ER)], lambda x, y: zA(y))
# ridge roll on A and on the cross gable
R.prism([(YR_A - 0.08, zA(YR_A - 0.08) - 0.01), (YR_A + 0.08, zA(YR_A + 0.08) - 0.01),
         (YR_A + 0.05, RIDGE_A + 0.05), (YR_A - 0.05, RIDGE_A + 0.05)], -HW - RK, HW + RK, "x")
R.prism([(-0.07, zX(0.07) - 0.01), (0.07, zX(0.07) - 0.01), (0.045, PEAK_X + 0.05), (-0.045, PEAK_X + 0.05)],
        YF - RKX, yv0 + 0.05, "y")

# B: gable to the street; south eave, the north slope runs into A's south wall
EB = BX0 - OV - 0.02
R.slab([(EB, BY0 - 0.20), (BXC, BY0 - 0.20), (BXC, BY1 + 0.20), (EB, BY1 + 0.20)], lambda x, y: zB(x))
R.slab([(BXC, BY0 - 0.20), (BX1 + 0.02, BY0 - 0.20), (BX1 + 0.02, BY1 + 0.20), (BXC, BY1 + 0.20)], lambda x, y: zB(x))
R.prism([(BXC - 0.08, zB(BXC - 0.08) - 0.01), (BXC + 0.08, zB(BXC + 0.08) - 0.01), (BXC + 0.05, B_RIDGE + 0.05),
         (BXC - 0.05, B_RIDGE + 0.05)], BY0 - 0.20, BY1 + 0.20, "y")

# C: gable running back from inside A's rear slope
OC = 0.25
for xa, xb in ((CX0 - OC - 0.02, CXC), (CXC, CX1 + OC + 0.02)):
    R.slab([(xa, 8.9), (xb, 8.9), (xb, CY1 + 0.20), (xa, CY1 + 0.20)], lambda x, y: zC(x))
R.prism([(CXC - 0.08, zC(CXC - 0.08) - 0.01), (CXC + 0.08, zC(CXC + 0.08) - 0.01), (CXC + 0.05, C_RIDGE + 0.05),
         (CXC - 0.05, C_RIDGE + 0.05)], 9.0, CY1 + 0.20, "y")
# D: shed falling to the rear
R.slab([(CX0 - 0.22, CY1 - 0.05), (DX1 + 0.22, CY1 - 0.05), (DX1 + 0.22, DY1 + 0.27), (CX0 - 0.22, DY1 + 0.27)],
       lambda x, y: zD(y), t=0.10)

# --- boxed cornices (frieze, bed mould, soffit, fascia; top inside the roof slab) -----------


def cornice_profile(eave_z, k, frz0, ov=OV):
    """(d, z) outline of a boxed cornice under a roof whose top is eave_z at the wall line and
    falls k per metre outward. Frieze from frz0; soffit 0.16 under the roof edge."""
    zr = lambda d: eave_z - d * k
    soff = zr(ov) - 0.16
    return [(-0.08, frz0), (0.025, frz0), (0.025, soff - 0.03), (0.045, soff - 0.015), (0.045, soff),
            (ov - 0.025, soff), (ov - 0.025, soff - 0.02), (ov, soff - 0.02), (ov, zr(ov) - 0.01),
            (-0.08, zr(-0.08) - 0.01)], soff


CP_A, SOFF_A = cornice_profile(zA(YF), TP, FRZ0)
sweep_plan(TR, [(-HW, YF + RET), (-HW, YF), (HW, YF), (HW, YF + RET)], CP_A)
sweep_plan(TR, [(HW, YA - RET), (HW, YA), (CX1, YA)], CP_A)
CP_B, SOFF_B = cornice_profile(zB(BX0), KB, FRZ0_B)
sweep_plan(TR, [(BX0 + RET, BY1), (BX0, BY1), (BX0, BY0), (BX0 + RET, BY0)], CP_B)
CP_C, _ = cornice_profile(zC(CX0), KC, 5.62, ov=OC)
sweep_plan(TR, [(CX0, CY1), (CX0, YA)], CP_C)
sweep_plan(TR, [(CX1, YA), (CX1, CY1)], CP_C)


def rake_band(mb, axis, pts_top, d_wall, d_out, depth=0.28):
    """Rake board + soffit under a roof edge: band between the roof top (less 1.5 cm) and
    `depth` below it, along the outline pts_top (u, z_top), from the wall plane d_wall out to
    d_out (the fascia face, 2.5 cm past the slab end)."""
    up = [(u, z - 0.015) for u, z in pts_top]
    lo = [(u, z - depth) for u, z in pts_top[::-1]]
    mb.prism(up + lo, d_wall, d_out, axis)


# A gable ends (N and S): rakes along Y
pts = [(EF, zA(EF)), (YR_A, RIDGE_A), (ER, zA(ER))]
rake_band(TR, "x", pts, HW - 0.02, HW + RK + 0.025)
rake_band(TR, "x", pts, -HW + 0.02, -HW - RK - 0.025)
# cross gable front rakes
rake_band(TR, "y", [(-XG, zX(XG)), (0.0, PEAK_X), (XG, zX(XG))], YF + 0.02, YF - RKX - 0.025, depth=0.30)
# B front and rear rakes (north end stops at A's wall)
pts = [(EB, zB(EB)), (BXC, B_RIDGE), (BX1, zB(BX1))]
rake_band(TR, "y", pts, BY0 + 0.02, BY0 - 0.20 - 0.025)
rake_band(TR, "y", pts, BY1 - 0.02, BY1 + 0.20 + 0.025)
# C rear rake; D fascia boards
pts = [(CX0 - OC - 0.02, zC(CX0 - OC - 0.02)), (CXC, C_RIDGE), (CX1 + OC + 0.02, zC(CX1 + OC + 0.02))]
rake_band(TR, "y", pts, CY1 - 0.02, CY1 + 0.20 + 0.025, depth=0.24)
TR.prism([(CY1 - 0.05, zD(CY1 - 0.05) - 0.22), (DY1 + 0.27, zD(DY1 + 0.27) - 0.22), (DY1 + 0.27, zD(DY1 + 0.27) - 0.01),
          (CY1 - 0.05, zD(CY1 - 0.05) - 0.01)], DX1 + 0.22, DX1 + 0.245, "x")
TR.prism([(CY1 - 0.05, zD(CY1 - 0.05) - 0.22), (DY1 + 0.27, zD(DY1 + 0.27) - 0.22), (DY1 + 0.27, zD(DY1 + 0.27) - 0.01),
          (CY1 - 0.05, zD(CY1 - 0.05) - 0.01)], CX0 - 0.245, CX0 - 0.22, "x")
TR.box(CX0 - 0.245, DX1 + 0.245, DY1 + 0.27, DY1 + 0.295, zD(DY1 + 0.27) - 0.20, zD(DY1 + 0.27) - 0.01)

# --- modillions (N80): small blocks 0.10 x 0.18 x 0.08 at 0.40 centres --------------------
MOD = (0.10, 0.18, 0.08)


def modillions_along(x0, x1, fixed, axis, sign, soff):
    """Blocks under a level soffit along a wall: axis 'x' = wall runs along X at y = fixed,
    blocks project in sign*Y; axis 'y' = wall along Y at x = fixed."""
    n = int(round((x1 - x0) / 0.40))
    cs = [x0 + (x1 - x0) * i / n for i in range(n + 1)] if n > 0 else [x0]
    for c in cs:
        d0, d1 = sorted((fixed + sign * 0.025, fixed + sign * (0.025 + MOD[1])))
        if axis == "x":
            TR.box(c - MOD[0] / 2, c + MOD[0] / 2, d0, d1, soff - MOD[2], soff + 0.005)
        else:
            TR.box(d0, d1, c - MOD[0] / 2, c + MOD[0] / 2, soff - MOD[2], soff + 0.005)


modillions_along(-HW + 0.20, HW - 0.20, YF, "x", -1, SOFF_A)
modillions_along(CX1 + 0.25, HW - 0.20, YA, "x", 1, SOFF_A)
for x in (HW, -HW):
    modillions_along(YF + 0.25, YF + 0.25, x, "y", 1 if x > 0 else -1, SOFF_A)    # one under each return
modillions_along(YA - 0.25, YA - 0.25, HW, "y", 1, SOFF_A)
modillions_along(BY0 + 0.20, BY1 - 0.20, BX0, "y", -1, SOFF_B)
# up the cross-gable rakes: blocks hanging under the sloping soffit (vertical sides)
L = math.hypot(XG, PEAK_X - zX(XG))
n = int(L / 0.40)
for s in (-1, 1):
    for i in range(1, n):
        x = s * XG * i / n
        xa, xb = sorted((x - MOD[0] / 2, x + MOD[0] / 2))
        zs = lambda xx: zX(xx) - 0.30
        TR.prism([(xa, zs(xa) - MOD[2]), (xb, zs(xb) - MOD[2]), (xb, zs(xb) + 0.005), (xa, zs(xa) + 0.005)],
                 YF - 0.025 - MOD[1], YF + 0.01, "y")

# chimneys (brick, corbelled cap; GUESS)
for x0, x1, y0, y1, zb, zt in CHIMS:
    BR.box(x0, x1, y0, y1, zb, zt - 0.16)
    BR.box(x0 - 0.05, x1 + 0.05, y0 - 0.05, y1 + 0.05, zt - 0.16, zt - 0.06)
    BR.box(x0 - 0.02, x1 + 0.02, y0 - 0.02, y1 + 0.02, zt - 0.06, zt)

# ---------------------------------------------------------------------------
# Corner boards and water tables
# ---------------------------------------------------------------------------


def corner(x, y, sx, sy, z0, z1):
    """Outside corner at (x, y); sx, sy = outward directions (+-1). Two boards."""
    xa, xb = sorted((x - sx * CB_W, x + sx * CB_T))
    ya, yb = sorted((y, y + sy * CB_T))
    TR.box(xa, xb, ya, yb, z0, z1)                                     # on the Y face
    xa, xb = sorted((x, x + sx * CB_T))
    ya, yb = sorted((y - sy * CB_W, y + sy * CB_T))
    TR.box(xa, xb, ya, yb, z0, z1)                                     # on the X face


corner(HW, YF, 1, -1, FLOOR, FRZ0)
corner(-HW, YF, -1, -1, FLOOR, FRZ0)
corner(HW, YA, 1, 1, FT, FRZ0)
corner(BX0, BY0, -1, -1, FLOOR, FRZ0_B)
corner(BX0, BY1, -1, 1, FT, FRZ0_B)
corner(DX1, DY1, 1, 1, FT, zD(DY1) - 0.22)
corner(CX0, DY1, -1, 1, FT, zD(DY1) - 0.22)
corner(DX1, CY1, 1, -1, FT, zD(CY1) - 0.22)
WTPROF = [(-0.05, FT), (0.03, FT), (0.03, WT - 0.01), (0.05, WT), (0.05, WT + 0.02), (0.0, WT + 0.05), (-0.05, WT + 0.05)]
sweep_plan(TR, [(HW, YF), (HW, YA), (CX1, YA)], WTPROF)
sweep_plan(TR, [(BX1, BY1), (BX0, BY1), (BX0, BY0 + 0.05)], WTPROF)
sweep_plan(TR, [(CX1, C2Y1), (CX1, CY1), (DX1, CY1), (DX1, DY1), (CX0, DY1), (CX0, YA)], WTPROF)

# ---------------------------------------------------------------------------
# Porches: P1 across the main front (4 posts, centre steps), P2 at the ell (2 posts, one step),
# C2 on the wing's north side (3 posts). Painted grey floors on plain skirts, chamfered posts
# with bases and caps, beams, sloping end boards, tin shed roofs over board ceilings. No rail.
# ---------------------------------------------------------------------------


def post(xc, yc, z0, z1, s=POST, ch=0.02):
    h = s / 2
    octo = [(-h + ch, -h), (h - ch, -h), (h, -h + ch), (h, h - ch), (h - ch, h), (-h + ch, h), (-h, h - ch), (-h, -h + ch)]
    zb, zt = z0 + 0.25, z1 - 0.17
    TR.prism([(xc + u, yc + v) for u, v in octo], zb - 0.01, zt + 0.01, "z")                 # chamfered shaft
    TR.box(xc - h - 0.03, xc + h + 0.03, yc - h - 0.03, yc + h + 0.03, z0, z0 + 0.20)          # base block
    TR.box(xc - h - 0.015, xc + h + 0.015, yc - h - 0.015, yc + h + 0.015, z0 + 0.20, zb)      # base mould
    TR.box(xc - h - 0.012, xc + h + 0.012, yc - h - 0.012, yc + h + 0.012, zt, zt + 0.035)     # collar
    TR.box(xc - h, xc + h, yc - h, yc + h, zt + 0.035, z1 - 0.05)                              # neck
    TR.box(xc - h - 0.035, xc + h + 0.035, yc - h - 0.035, yc + h + 0.035, z1 - 0.05, z1)      # cap


def porch(x0, x1, y0, y1, zroof, fascia0, posts, skirt_ends, roof_ends):
    """Open porch along a front wall at y1 (front edge y0): deck, skirt, posts, beam, fascia,
    end boards, ceiling and tin roof. zroof(y) = roof top. skirt_ends / roof_ends: which ends
    (x0, x1) are free."""
    DK.box(x0 - 0.03 * roof_ends[0], x1 + 0.03 * roof_ends[1], y0, y1 + 0.02, FLOOR - 0.05, FLOOR)   # floor
    TR.box(x0, x1, y0 + 0.03, y0 + 0.055, SKIRT + 0.15, FLOOR - 0.05)                                 # skirt
    for e, x in zip(skirt_ends, (x0, x1)):
        if e:
            xa, xb = sorted((x, x + (0.025 if x == x0 else -0.025)))
            TR.box(xa, xb, y0 + 0.03, y1, SKIRT + 0.15, FLOOR - 0.05)
    for xp in posts:
        post(xp, y0 + 0.10, FLOOR, fascia0)
    zc = lambda y: zroof(y) - 0.10                    # ceiling underside
    TR.box(x0, x1, y0 + 0.03, y0 + 0.17, fascia0, zc(y0 + 0.17) + 0.02)          # beam
    TR.box(x0 - 0.02 * roof_ends[0], x1 + 0.02 * roof_ends[1], y0, y0 + 0.03, fascia0 - 0.02, zroof(y0) - 0.03)  # fascia
    TR.box(x0 - 0.01, x1 + 0.01, y0 + 0.03, y0 + 0.06, fascia0 - 0.06, fascia0 - 0.02)   # bead under it
    for e, x in zip(roof_ends, (x0, x1)):
        if e:
            xa, xb = sorted((x, x + (0.14 if x == x0 else -0.14)))
            TR.prism([(y0 + 0.03, fascia0), (y1, fascia0 + (zroof(y1) - zroof(y0))), (y1, zc(y1) + 0.01),
                      (y0 + 0.03, zc(y0 + 0.03) + 0.01)], xa, xb, "x")
    xr0, xr1 = x0 - 0.04 * roof_ends[0], x1 + 0.04 * roof_ends[1]
    TR.prism([(y0 + 0.03, zc(y0 + 0.03)), (y1 + 0.02, zc(y1 + 0.02)), (y1 + 0.02, zroof(y1 + 0.02) - 0.03),
              (y0 + 0.03, zroof(y0 + 0.03) - 0.03)], xr0, xr1, "x")                 # board ceiling
    R.prism([(y0, zroof(y0) - 0.03), (y1 + 0.02, zroof(y1 + 0.02) - 0.03), (y1 + 0.02, zroof(y1 + 0.02)),
             (y0, zroof(y0))], xr0 - 0.01, xr1 + 0.01, "x")                          # tin


porch(-HW, HW, 0.0, YF, zP1, 3.15, (-3.65, -1.25, 1.25, 3.65), (True, True), (True, True))
porch(P2X0, BX1, P2Y0, BY0, zP2, 2.96, (P2X0 + 0.10, BX1 - 0.12), (True, False), (True, False))


def steps(x0, x1, y_front, n, rise, yfront_edge):
    """n wooden steps up to the porch floor (grey paint), with sloping cheek boards."""
    run = 0.30
    for i in range(n):
        ztop = rise * (i + 1)
        yb = yfront_edge - run * (n - i)
        DK.box(x0, x1, yb, y_front, SKIRT + 0.15 if i == 0 else ztop - rise, ztop - 0.03)
        DK.box(x0 - 0.02, x1 + 0.02, yb - 0.025, y_front, ztop - 0.03, ztop)            # tread with nosing
    yb = yfront_edge - run * n
    for x in (x0, x1):
        xa, xb = sorted((x, x + (-0.04 if x == x0 else 0.04)))
        TR.prism([(yb - 0.03, SKIRT + 0.15), (y_front, SKIRT + 0.15), (y_front, FLOOR - 0.02),
                  (yfront_edge - 0.02, FLOOR - 0.02), (yb - 0.03, rise + 0.04)], xa, xb, "x")


steps(-0.80, 0.80, 0.03, 2, 0.15, 0.0)
steps(-5.10, -4.00, P2Y0 + 0.03, 1, 0.22, P2Y0)

# C2: wing porch on the north side, open, shed roof falling north (map "1")
DK.box(CX1, DX1 + 0.03, YA + 0.02, C2Y1, FLOOR - 0.05, FLOOR)
TR.box(DX1 - 0.055, DX1 - 0.03, YA + 0.02, C2Y1, SKIRT + 0.15, FLOOR - 0.05)
TR.box(CX1, DX1 - 0.03, C2Y1 - 0.055, C2Y1 - 0.03, SKIRT + 0.15, FLOOR - 0.05)
for yp in (YA + 0.20, (YA + C2Y1) / 2, C2Y1 - 0.15):
    post(DX1 - 0.12, yp, FLOOR, 2.86)
TR.box(DX1 - 0.19, DX1 - 0.03, YA + 0.02, C2Y1, 2.86, zC2(DX1 - 0.19) - 0.08)
TR.box(DX1 - 0.03, DX1, YA + 0.02, C2Y1 + 0.03, 2.84, zC2(DX1) - 0.03)
R.prism([(CX1 - 0.02, zC2(CX1 - 0.02) - 0.03), (DX1 + 0.03, zC2(DX1 + 0.03) - 0.03), (DX1 + 0.03, zC2(DX1 + 0.03)),
         (CX1 - 0.02, zC2(CX1 - 0.02))], YA + 0.02, C2Y1 + 0.04, "y")
TR.prism([(CX1 - 0.02, zC2(CX1 - 0.02) - 0.10), (DX1 - 0.03, zC2(DX1 - 0.03) - 0.10), (DX1 - 0.03, zC2(DX1 - 0.03) - 0.03),
          (CX1 - 0.02, zC2(CX1 - 0.02) - 0.03)], YA + 0.02, C2Y1, "y")
DK.box(CX1 + 0.6, CX1 + 1.3, C2Y1, C2Y1 + 0.30, SKIRT + 0.15, 0.22)           # one step off the porch end

# ---------------------------------------------------------------------------
# Build objects (boolean the cut shells)
# ---------------------------------------------------------------------------


def cut_shell(shell, cutter, name, mat):
    walls = shell.to_object(name, MATS[mat], col)
    if not cutter.bm.faces:
        cutter.bm.free()
        return walls
    cutters = cutter.to_object(name + "_Cutters", MATS[mat], col)
    mod = walls.modifiers.new("Openings", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    solvers = [i.identifier for i in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items]
    mod.solver = "EXACT" if "EXACT" in solvers else solvers[0]
    mod.use_self = True
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


for name, (shell, cutter) in SHELLS.items():
    cut_shell(shell, cutter, "H91_" + name, "Clap")
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("H91_" + key, MATS[BUILDER_MAT[key]], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("91-93 Main built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)",
      "| window backs", len(BACKREC))
# Materials, baked lighting and GLB export: run house_91_93_bake.py (it runs this file first).
