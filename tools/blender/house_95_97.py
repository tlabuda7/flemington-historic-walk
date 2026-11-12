"""
house_95_97.py - builds 95-97 Main St, Flemington (west side, old nos. 504-503): a 2-storey
red-brick dwelling ("D", "2 1/2" in 1910) set back behind a front yard, with a 1-storey open
porch across its front, a narrow 1-storey frame office ("OFF.") on its north side set 1.8 m
further back, a 2-storey brick rear wing and 1-storey frame rear parts (PLAN.md "95-97 Main St:
brick house ("D") with a frame office annex ("Off.")").

Evidence: 1910 and 1921 Sanborn maps (footprints, storeys, brick / frame, "OFF."; MAP). No photo
exists and there is no 1980 NRHP entry (the house was gone by 1948): everything else is a plain
GUESS (owner go-ahead 2026-11-12 with the recommended choices: plain front with a full-width
porch, side-gabled slate roof with small attic windows in both gable ends for the 1910 "2 1/2",
the office annex plain with one door and one window, no sign). No lettering, shutters or
chimneys (spec).

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/house_95_97.py").read())

Every run deletes and rebuilds the "House9597" collection. Materials, lightmap bake and GLB
export: house_95_97_bake.py (runs this file first). Pattern: house_91_93.py / store_79.py (one
builder per material, Wall frames, closed wall shells cut by boolean pockets, section-E window
backs).

Windows (PLAN.md section E): every pane is ONE glass face (builder Glass -> material `glass`)
4 cm in front of a window back showing a cell of assets/textures/shared/window_backs.jpg
(builder WBack): lace, curtains, blinds and one dark room in the dwelling; blinds in the office.

Coordinates (metres, Blender Z-up), origin = scene (-13.00, 0.02, 54.01) = centre of the porch
front at lawn level, rotation 0 90 0:
    X  along Main St, +X = north (the office, then 91-93), -X = south (the empty lot 101)
    Y  depth: y = 0 is the porch front; the steps run out to -0.90; house front wall 2.21
    Z  up from the lawn; foundations reach down to -0.20
Scene: world x = -13.00 - Y, world z = 54.01 - X.
"""

import json
import math
import bpy
import bmesh

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md massing table; X, Y = MAP, heights GUESS)
# ---------------------------------------------------------------------------
HW = 4.31                       # half front of the house A (8.62 m)
YF, YA = 2.21, 11.57            # A front / rear wall
YR_A = 6.89                     # ridge line
FT = 0.45                       # stone foundation top = bottom of the brick shells
FLOOR = 0.55                    # floors and porch deck
SKIRT = -0.20
TP = math.tan(math.radians(35.0))
RIDGE_A = 10.18
SLAB = 0.12                     # roof slab thickness (vertical)
OV, RK = 0.35, 0.25             # eave overhang (spec 0.35), rake overhang
RET = 0.35                      # cornice returns on the gable walls
FRZ0 = 6.32                     # frieze bottom (soffit 6.50)
# rear wing B (brick), frame parts C1 (rear strip) and C2 (south of B), office D
BX0, BX1, BY1 = -2.47, 3.43, 19.77
BXC = (BX0 + BX1) / 2
B_EAVE, B_RIDGE = 6.40, 8.40
KB = (B_RIDGE - B_EAVE) / (BX1 - BXC)
C1 = (-HW, 4.87, BY1, 22.25)
C_HI, C_LO = 3.40, 3.00
DX0, DX1, DY0, DY1 = HW, 7.44, 4.01, 15.31   # office (map X 4.42: drawn touching the house wall)
D_HI, D_LO = 3.60, 3.10
FT_D, FLOOR_D = 0.30, 0.35                    # frame parts: low foundations, floors
P_FRONT, P_WALL = 3.46, 3.76                  # porch roof top at the front edge / at the wall
POST = 0.14
CB_W, CB_T = 0.15, 0.025


def zA(y):
    return RIDGE_A - abs(y - YR_A) * TP


def zB(x):
    return B_RIDGE - abs(x - BXC) * KB


def zC1(y):
    return C_HI - (y - BY1) * (C_HI - C_LO) / (C1[3] - BY1)


def zC2(x):
    return C_HI - (BX0 - x) * (C_HI - C_LO) / (BX0 + HW)


def zD(y):
    return D_HI - (y - DY0) * (D_HI - D_LO) / (DY1 - DY0)


def zP(y):
    return P_FRONT + (P_WALL - P_FRONT) * y / YF


# ---------------------------------------------------------------------------
# Materials (plain stand-ins; house_95_97_bake.py swaps in the textures)
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


COLOURS = {"Brick": "#8A4A38", "Stone": "#CDBFA2", "Trim": "#DDD5C2", "Slate": "#6E6C68", "Tin": "#5A3D34",
           "Clap": "#BDB4A0", "Door": "#3A2A1F", "Glass": "#1A1916", "WBack": "#2A2420"}
MATS = {k: plain("H95_" + k, c) for k, c in COLOURS.items()}
# builder -> material (Deck = painted grey porch floor and steps: trim paint, grey tint in the bake)
BUILDER_MAT = {k: k for k in COLOURS}
BUILDER_MAT["Deck"] = "Trim"


# ---------------------------------------------------------------------------
# Mesh builder (as house_91_93.py)
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


col = fresh_collection("House9597")
G = {k: MB() for k in BUILDER_MAT}
BR, ST, TR, SL, TN, CL, DR, GL, WB, DK = (G[k] for k in ("Brick", "Stone", "Trim", "Slate", "Tin", "Clap", "Door",
                                                         "Glass", "WBack", "Deck"))
# wall shells (closed solids) and their cutters: name -> (shell, cutter, material)
SHELLS = {k: (MB(), MB(), m) for k, m in (("ShellA", "Brick"), ("ShellB", "Brick"), ("ShellC1", "Clap"),
                                          ("ShellC2", "Clap"), ("ShellD", "Clap"))}
(SA, KA, _), (SB, KB_, _), (SC1, KC1, _), (SC2, KC2, _), (SD, KD, _) = SHELLS.values()

FRONT = Wall((0.0, YF), (0, -1), KA)            # u = X
SOUTH = Wall((-HW, 0.0), (-1, 0), KA)           # u = -Y
NORTH = Wall((HW, 0.0), (1, 0), KA)             # u = Y
D_FRONT = Wall((0.0, DY0), (0, -1), KD)         # u = X
C1_REAR = Wall((0.0, C1[3]), (0, 1), KC1)       # u = -X

# ---------------------------------------------------------------------------
# Window backs (section E)
# ---------------------------------------------------------------------------
WB_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\window_backs.json"))["cells"]
GAP = 0.04
BACKREC = {}


def crop_uv(uv, aspect):
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
    back(wall, u0, u1, z0, z1, d_glass - GAP, cell, flip)
    GL.quad(wall, u0, u1, z0, z1, d_glass)


# ---------------------------------------------------------------------------
# Shells
# ---------------------------------------------------------------------------
SA.prism([(YF, FT), (YA, FT), (YA, zA(YA) - SLAB), (YR_A, RIDGE_A - SLAB), (YF, zA(YF) - SLAB)], -HW, HW, "x")
SB.prism([(BX0, FT), (BX1, FT), (BX1, zB(BX1) - SLAB), (BXC, B_RIDGE - SLAB), (BX0, zB(BX0) - SLAB)], YA - 0.05, BY1, "y")
SC1.prism([(BY1 - 0.05, FT_D), (C1[3], FT_D), (C1[3], zC1(C1[3]) - 0.10), (BY1 - 0.05, zC1(BY1 - 0.05) - 0.10)],
          C1[0], C1[1], "x")
SC2.prism([(-HW, FT_D), (BX0 + 0.05, FT_D), (BX0 + 0.05, zC2(BX0 + 0.05) - 0.10), (-HW, zC2(-HW) - 0.10)], YA - 0.05,
          BY1, "y")
SD.prism([(DY0, FT_D), (DY1, FT_D), (DY1, zD(DY1) - 0.10), (DY0, zD(DY0) - 0.10)], DX0 - 0.05, DX1, "x")

# foundations: buff stone under the brick house and wing (2 cm proud, the top a ledge), low
# stone under the frame parts
o = 0.02
ST.box(-HW - o, HW + o, YF - o, YA + o, SKIRT, FT)
ST.box(BX0 - o, BX1 + o, YA, BY1, SKIRT, FT)
ST.box(C1[0] - o, C1[1] + o, BY1, C1[3] + o, SKIRT, FT_D)
ST.box(-HW - o, BX0, YA, BY1, SKIRT, FT_D)
ST.box(DX0, DX1 + o, DY0 - o, DY1 + o, SKIRT, FT_D)


# ---------------------------------------------------------------------------
# Windows: brick reveal 0.10, cream frame, dark 2/2 sashes, stone lintel and sill (brick walls);
# cased like 91-93 on the frame office
# ---------------------------------------------------------------------------
def sashes(wall, a, b, g0, g1, lites, d0):
    """Two sashes (stiles, rails) and muntins, front face at d0 (negative = in the wall)."""
    zm = (g0 + g1) / 2
    f, k = d0, d0 - 0.07
    DR.wbox(wall, a, a + 0.045, g0, g1, k, f)
    DR.wbox(wall, b - 0.045, b, g0, g1, k, f)
    DR.wbox(wall, a + 0.045, b - 0.045, g1 - 0.055, g1, k, f)
    DR.wbox(wall, a + 0.045, b - 0.045, zm - 0.025, zm + 0.025, k, f + 0.005)
    DR.wbox(wall, a + 0.045, b - 0.045, g0, g0 + 0.075, k, f - 0.025)
    nx, ny = lites
    ia, ib = a + 0.045, b - 0.045
    for i in range(1, nx):
        x = ia + (ib - ia) * i / nx
        DR.wbox(wall, x - 0.012, x + 0.012, g0 + 0.075, g1 - 0.055, k + 0.01, f - 0.03)
    for s0, s1 in ((g0 + 0.075, zm - 0.025), (zm + 0.025, g1 - 0.055)):
        for i in range(1, ny):
            z = s0 + (s1 - s0) * i / ny
            DR.wbox(wall, ia, ib, z - 0.012, z + 0.012, k + 0.01, f - 0.03)


def brick_window(wall, cu, z0, z1, cell, w=0.95, lites=(2, 1), flip=False, lintel=0.20):
    hw = w / 2
    u0, u1 = cu - hw, cu + hw
    wall.cut.wbox(wall, u0, u1, z0, z1, 0.25, -0.32)                      # opening (brick reveal)
    R0 = -0.10                                                            # frame face
    TR.wbox(wall, u0, u0 + 0.06, z0, z1, -0.32, R0)                       # frame
    TR.wbox(wall, u1 - 0.06, u1, z0, z1, -0.32, R0)
    TR.wbox(wall, u0 + 0.06, u1 - 0.06, z1 - 0.06, z1, -0.32, R0)
    TR.wbox(wall, u0 + 0.06, u1 - 0.06, z0, z0 + 0.05, -0.32, R0 - 0.02)
    a, b = u0 + 0.06, u1 - 0.06
    g0, g1 = z0 + 0.05, z1 - 0.06
    pane(wall, a, b, g0, g1, -0.22, cell, flip)
    sashes(wall, a, b, g0, g1, lites, -0.13)
    ST.wbox(wall, u0 - 0.10, u1 + 0.10, z1, z1 + lintel, 0.0, 0.03)        # stone lintel
    ST.wbox(wall, u0 - 0.07, u1 + 0.07, z0 - 0.08, z0 + 0.015, -0.12, 0.06)  # stone sill
    TR.wbox(wall, u0 - 0.01, u1 + 0.01, z1 - 0.02, z1 + 0.005, -0.12, -0.0)  # head flashing / brick mould


def frame_window(wall, cu, z0, z1, cell, w=0.80, lites=(2, 1)):
    hw = w / 2
    u0, u1 = cu - hw, cu + hw
    wall.cut.wbox(wall, u0, u1, z0, z1, 0.25, -0.22)
    TR.wbox(wall, u0, u0 + 0.05, z0, z1, -0.22, 0.0)
    TR.wbox(wall, u1 - 0.05, u1, z0, z1, -0.22, 0.0)
    TR.wbox(wall, u0 + 0.05, u1 - 0.05, z1 - 0.05, z1, -0.22, 0.0)
    TR.wbox(wall, u0 + 0.05, u1 - 0.05, z0, z0 + 0.04, -0.22, 0.0)
    a, b = u0 + 0.05, u1 - 0.05
    g0, g1 = z0 + 0.04, z1 - 0.05
    pane(wall, a, b, g0, g1, -0.13, cell)
    sashes(wall, a, b, g0, g1, lites, -0.045)
    TR.wbox(wall, u0 - 0.10, u0, z0, z1, 0.0, 0.025)
    TR.wbox(wall, u1, u1 + 0.10, z0, z1, 0.0, 0.025)
    TR.wbox(wall, u0 - 0.10, u1 + 0.10, z1, z1 + 0.12, 0.0, 0.03)
    TR.wbox(wall, u0 - 0.13, u1 + 0.13, z1 + 0.12, z1 + 0.15, 0.0, 0.06)
    TR.wbox(wall, u0 - 0.14, u1 + 0.14, z0 - 0.045, z0, -0.03, 0.065)
    TR.wbox(wall, u0 - 0.08, u1 + 0.08, z0 - 0.15, z0 - 0.045, 0.0, 0.02)


def door(wall, cu, w, z0, h, transom=0.0, cell="dark_room", brick=True, plank=False, step=None):
    """4-panel door (or batten door) in a brick reveal with a stone lintel, or cased in a frame
    wall; optional transom light; optional stone step (depth out, top z)."""
    u0, u1 = cu - w / 2, cu + w / 2
    top = z0 + h + (transom + 0.05 if transom else 0.0)
    dp = -0.32 if brick else -0.20
    wall.cut.wbox(wall, u0, u1, z0 - 0.05, top, 0.25, dp)
    f = -0.10 if brick else 0.0
    TR.wbox(wall, u0, u0 + 0.06, z0, top, dp, f)                         # frame / jamb linings
    TR.wbox(wall, u1 - 0.06, u1, z0, top, dp, f)
    TR.wbox(wall, u0 + 0.06, u1 - 0.06, top - 0.06, top, dp, f)
    a, b = u0 + 0.06, u1 - 0.06
    lf = f - 0.06                                                         # leaf face
    DR.wbox(wall, a, b, z0 + 0.02, z0 + h, lf - 0.045, lf)
    if plank:
        for z in (z0 + 0.25, z0 + h / 2, z0 + h - 0.30):
            DR.wbox(wall, a + 0.05, b - 0.05, z, z + 0.12, lf, lf + 0.015)
    else:
        pw = (b - a - 0.30) / 2
        for p0, p1 in ((z0 + 0.20, z0 + 0.95), (z0 + 1.15, z0 + h - 0.18)):
            for k in range(2):
                pa = a + 0.10 + k * (pw + 0.10)
                DR.wbox(wall, pa, pa + pw, p0, p1, lf, lf + 0.015)
    if transom:
        TR.wbox(wall, a, b, z0 + h, z0 + h + 0.05, dp, f - 0.02)
        pane(wall, a, b, z0 + h + 0.05, top - 0.06, f - 0.10, cell)
    if brick:
        ST.wbox(wall, u0 - 0.10, u1 + 0.10, top, top + 0.20, 0.0, 0.03)        # stone lintel
        ST.wbox(wall, u0 - 0.04, u1 + 0.04, z0 - 0.06, z0 + 0.01, dp, 0.04)     # stone sill
    else:
        TR.wbox(wall, u0 - 0.03, u1 + 0.03, z0 - 0.05, z0 + 0.02, dp, 0.05)
        TR.wbox(wall, u0 - 0.11, u0, z0 - 0.02, top, 0.0, 0.03)
        TR.wbox(wall, u1, u1 + 0.11, z0 - 0.02, top, 0.0, 0.03)
        TR.wbox(wall, u0 - 0.11, u1 + 0.11, top, top + 0.14, 0.0, 0.035)
        TR.wbox(wall, u0 - 0.14, u1 + 0.14, top + 0.14, top + 0.17, 0.0, 0.07)
    if step:
        out, ztop = step
        ST.wbox(wall, u0 - 0.20, u1 + 0.20, SKIRT + 0.15, ztop, 0.0, out)


# --- openings (GUESS, plain; spec elevation details) ---------------------------------------
GF = (1.35, 3.30)
UF = (4.35, 6.10)
AT = (7.40, 8.30)
for u, c in ((-2.70, "lace_blind_cream"), (2.70, "curtains_beige")):
    brick_window(FRONT, u, *GF, c)
for u, c, f in ((-2.70, "lace", False), (0.0, "lace_full_blind_cream", False), (2.70, "lace", True)):
    brick_window(FRONT, u, *UF, c, flip=f, lintel=0.18)
door(FRONT, 0.0, 1.00, FLOOR, 2.40, transom=0.30, cell="dark_room_frame")
# south gable wall (in full view over the empty lot 101): two windows per floor + two attic windows
# SOUTH: u = -Y, so Y 5.0 -> u -5.0
for y, cg, cu_ in ((5.0, "curtains_maroon_blind", "lace_blind_cream"), (8.8, "dark_room", "curtains_olive")):
    brick_window(SOUTH, -y, *GF, cg)
    brick_window(SOUTH, -y, *UF, cu_, lintel=0.18)
for y, c in ((5.5, "blind_cream_half"), (8.3, "dark_room_frame")):
    brick_window(SOUTH, -y, *AT, c, w=0.60, lintel=0.16)
for y, c in ((5.5, "dark_room_frame"), (8.3, "blind_cream_high")):
    brick_window(NORTH, y, *AT, c, w=0.60, lintel=0.16)
# office: one door (one step) and one window, blinds
door(D_FRONT, 5.40, 0.90, FLOOR_D, 2.20, brick=False, step=(0.32, 0.17))
frame_window(D_FRONT, 6.75, 0.95, 2.45, "blind_cream_half")
# one rear door on the frame part C1
door(C1_REAR, 0.80, 0.85, FLOOR_D, 2.05, brick=False, plank=True, step=(0.30, 0.16))

# ---------------------------------------------------------------------------
# Roofs: A side-gabled slate, B gable running back (slate), tin sheds on C1, C2, D and the porch
# ---------------------------------------------------------------------------
EF, ER = YF - OV - 0.02, YA + OV + 0.02
SL.slab([(-HW - RK, EF), (HW + RK, EF), (HW + RK, YR_A), (-HW - RK, YR_A)], lambda x, y: zA(y))
SL.slab([(-HW - RK, YR_A), (HW + RK, YR_A), (HW + RK, ER), (-HW - RK, ER)], lambda x, y: zA(y))
SL.prism([(YR_A - 0.09, zA(YR_A - 0.09) - 0.01), (YR_A + 0.09, zA(YR_A + 0.09) - 0.01),
          (YR_A + 0.05, RIDGE_A + 0.06), (YR_A - 0.05, RIDGE_A + 0.06)], -HW - RK, HW + RK, "x")     # ridge cap
OB = 0.25
for xa, xb in ((BX0 - OB - 0.02, BXC), (BXC, BX1 + OB + 0.02)):
    SL.slab([(xa, 9.3), (xb, 9.3), (xb, BY1 + 0.22), (xa, BY1 + 0.22)], lambda x, y: zB(x))
SL.prism([(BXC - 0.08, zB(BXC - 0.08) - 0.01), (BXC + 0.08, zB(BXC + 0.08) - 0.01), (BXC + 0.05, B_RIDGE + 0.05),
          (BXC - 0.05, B_RIDGE + 0.05)], 9.4, BY1 + 0.22, "y")
TN.slab([(C1[0] - 0.22, BY1 - 0.05), (C1[1] + 0.22, BY1 - 0.05), (C1[1] + 0.22, C1[3] + 0.27),
         (C1[0] - 0.22, C1[3] + 0.27)], lambda x, y: zC1(y), t=0.10)
TN.slab([(-HW - 0.27, YA - 0.02), (BX0 + 0.02, YA - 0.02), (BX0 + 0.02, BY1 - 0.05), (-HW - 0.27, BY1 - 0.05)],
        lambda x, y: zC2(x), t=0.10)
TN.slab([(DX0 - 0.02, DY0 - 0.27), (DX1 + 0.15, DY0 - 0.27), (DX1 + 0.15, DY1 + 0.22), (DX0 - 0.02, DY1 + 0.22)],
        lambda x, y: zD(y), t=0.10)


def cornice_profile(eave_z, k, frz0, ov=OV):
    """(d, z) outline of a boxed cornice under a roof whose top is eave_z at the wall line and
    falls k per metre outward. Frieze from frz0; soffit 0.16 under the roof edge."""
    zr = lambda d: eave_z - d * k
    soff = zr(ov) - 0.16
    return [(-0.08, frz0), (0.025, frz0), (0.025, soff - 0.03), (0.045, soff - 0.015), (0.045, soff),
            (ov - 0.025, soff), (ov - 0.025, soff - 0.02), (ov, soff - 0.02), (ov, zr(ov) - 0.01),
            (-0.08, zr(-0.08) - 0.01)], soff


def rake_band(mb, axis, pts_top, d_wall, d_out, depth=0.28):
    up = [(u, z - 0.015) for u, z in pts_top]
    lo = [(u, z - depth) for u, z in pts_top[::-1]]
    mb.prism(up + lo, d_wall, d_out, axis)


CP_A, SOFF_A = cornice_profile(zA(YF), TP, FRZ0)
sweep_plan(TR, [(-HW, YF + RET), (-HW, YF), (HW, YF), (HW, YF + RET)], CP_A)
sweep_plan(TR, [(HW, YA - RET), (HW, YA), (BX1, YA)], CP_A)
sweep_plan(TR, [(BX0, YA), (-HW, YA), (-HW, YA - RET)], CP_A)
pts = [(EF, zA(EF)), (YR_A, RIDGE_A), (ER, zA(ER))]
rake_band(TR, "x", pts, HW - 0.02, HW + RK + 0.025)
rake_band(TR, "x", pts, -HW + 0.02, -HW - RK - 0.025)
CP_B, _ = cornice_profile(zB(BX0), KB, B_EAVE - 0.55, ov=OB)
sweep_plan(TR, [(BX0, BY1), (BX0, YA)], CP_B)
sweep_plan(TR, [(BX1, YA), (BX1, BY1)], CP_B)
rake_band(TR, "y", [(BX0 - OB - 0.02, zB(BX0 - OB - 0.02)), (BXC, B_RIDGE), (BX1 + OB + 0.02, zB(BX1 + OB + 0.02))],
          BY1 - 0.02, BY1 + 0.22 + 0.025, depth=0.26)
# office: plain boxed cornice along its front, a sloping fascia on the north side
kd = (D_HI - D_LO) / (DY1 - DY0)
CP_D, _ = cornice_profile(zD(DY0), -kd, 3.20, ov=0.25)
sweep_plan(TR, [(DX0, DY0), (DX1, DY0), (DX1, DY0 + 0.25)], CP_D)
TR.prism([(DY0 - 0.27, zD(DY0 - 0.27) - 0.20), (DY1 + 0.22, zD(DY1 + 0.22) - 0.20), (DY1 + 0.22, zD(DY1 + 0.22) - 0.01),
          (DY0 - 0.27, zD(DY0 - 0.27) - 0.01)], DX1 + 0.15, DX1 + 0.175, "x")
TR.box(DX0, DX1 + 0.175, DY1 + 0.22, DY1 + 0.245, zD(DY1 + 0.22) - 0.20, zD(DY1 + 0.22) - 0.01)
# C1 / C2 fascias
TR.box(C1[0] - 0.245, C1[1] + 0.245, C1[3] + 0.27, C1[3] + 0.295, zC1(C1[3] + 0.27) - 0.20, zC1(C1[3] + 0.27) - 0.01)
for x in (C1[0] - 0.245, C1[1] + 0.22):
    TR.prism([(BY1 - 0.05, zC1(BY1 - 0.05) - 0.20), (C1[3] + 0.27, zC1(C1[3] + 0.27) - 0.20),
              (C1[3] + 0.27, zC1(C1[3] + 0.27) - 0.01), (BY1 - 0.05, zC1(BY1 - 0.05) - 0.01)], x, x + 0.025, "x")
TR.box(-HW - 0.295, -HW - 0.27, YA - 0.02, BY1 - 0.05, zC2(-HW - 0.27) - 0.20, zC2(-HW - 0.27) - 0.01)

# ---------------------------------------------------------------------------
# Corner boards on the frame parts; stone foundations already proud
# ---------------------------------------------------------------------------


def corner(x, y, sx, sy, z0, z1):
    xa, xb = sorted((x - sx * CB_W, x + sx * CB_T))
    ya, yb = sorted((y, y + sy * CB_T))
    TR.box(xa, xb, ya, yb, z0, z1)
    xa, xb = sorted((x, x + sx * CB_T))
    ya, yb = sorted((y - sy * CB_W, y + sy * CB_T))
    TR.box(xa, xb, ya, yb, z0, z1)


corner(DX1, DY0, 1, -1, FT_D, 3.20)
corner(DX1, DY1, 1, 1, FT_D, zD(DY1) - 0.20)
corner(C1[0], C1[3], -1, 1, FT_D, zC1(C1[3]) - 0.20)
corner(C1[1], C1[3], 1, 1, FT_D, zC1(C1[3]) - 0.20)
corner(C1[1], BY1, 1, -1, FT_D, zC1(BY1) - 0.20)

# ---------------------------------------------------------------------------
# Porch: full front, 4 chamfered posts with bases and caps, beam, fascia, sloping end boards,
# board ceiling, tin shed roof; painted grey floor on a plain skirt; three centre steps; no rail
# ---------------------------------------------------------------------------


def post(xc, yc, z0, z1, s=POST, ch=0.02):
    h = s / 2
    octo = [(-h + ch, -h), (h - ch, -h), (h, -h + ch), (h, h - ch), (h - ch, h), (-h + ch, h), (-h, h - ch), (-h, -h + ch)]
    zb, zt = z0 + 0.25, z1 - 0.17
    TR.prism([(xc + u, yc + v) for u, v in octo], zb - 0.01, zt + 0.01, "z")
    TR.box(xc - h - 0.03, xc + h + 0.03, yc - h - 0.03, yc + h + 0.03, z0, z0 + 0.20)
    TR.box(xc - h - 0.015, xc + h + 0.015, yc - h - 0.015, yc + h + 0.015, z0 + 0.20, zb)
    TR.box(xc - h - 0.012, xc + h + 0.012, yc - h - 0.012, yc + h + 0.012, zt, zt + 0.035)
    TR.box(xc - h, xc + h, yc - h, yc + h, zt + 0.035, z1 - 0.05)
    TR.box(xc - h - 0.035, xc + h + 0.035, yc - h - 0.035, yc + h + 0.035, z1 - 0.05, z1)


x0, x1, y0, y1 = -HW, HW, 0.0, YF
FAS0 = 3.25
DK.box(x0 - 0.03, x1 + 0.03, y0, y1 + 0.02, FLOOR - 0.05, FLOOR)                     # floor
TR.box(x0, x1, y0 + 0.03, y0 + 0.055, SKIRT + 0.15, FLOOR - 0.05)                     # skirt
for x in (x0, x1):
    xa, xb = sorted((x, x + (0.025 if x == x0 else -0.025)))
    TR.box(xa, xb, y0 + 0.03, y1, SKIRT + 0.15, FLOOR - 0.05)
for xp in (-4.18, -1.35, 1.35, 4.18):
    post(xp, y0 + 0.10, FLOOR, FAS0)
zc = lambda y: zP(y) - 0.10
TR.box(x0, x1, y0 + 0.03, y0 + 0.17, FAS0, zc(y0 + 0.17) + 0.02)                     # beam
TR.box(x0 - 0.02, x1 + 0.02, y0, y0 + 0.03, FAS0 - 0.02, zP(y0) - 0.03)                # fascia
TR.box(x0 - 0.01, x1 + 0.01, y0 + 0.03, y0 + 0.06, FAS0 - 0.06, FAS0 - 0.02)           # bead
for x in (x0, x1):
    xa, xb = sorted((x, x + (0.14 if x == x0 else -0.14)))
    TR.prism([(y0 + 0.03, FAS0), (y1, FAS0 + (zP(y1) - zP(y0))), (y1, zc(y1) + 0.01), (y0 + 0.03, zc(y0 + 0.03) + 0.01)],
             xa, xb, "x")
TR.prism([(y0 + 0.03, zc(y0 + 0.03)), (y1 + 0.02, zc(y1 + 0.02)), (y1 + 0.02, zP(y1 + 0.02) - 0.03),
          (y0 + 0.03, zP(y0 + 0.03) - 0.03)], x0 - 0.04, x1 + 0.04, "x")                # ceiling
TN.prism([(y0, zP(y0) - 0.03), (y1 + 0.02, zP(y1 + 0.02) - 0.03), (y1 + 0.02, zP(y1 + 0.02)), (y0, zP(y0))],
         x0 - 0.05, x1 + 0.05, "x")                                                    # tin roof

# three steps X +-0.90, Y -0.90 ... 0 (risers 0.1375), cheek boards
RISE, RUN = FLOOR / 4, 0.30
for i in range(3):
    ztop = RISE * (i + 1)
    yb = -RUN * (3 - i)
    DK.box(-0.90, 0.90, yb, 0.03, SKIRT + 0.15 if i == 0 else ztop - RISE, ztop - 0.03)
    DK.box(-0.92, 0.92, yb - 0.025, 0.03, ztop - 0.03, ztop)
for x in (-0.90, 0.90):
    xa, xb = sorted((x, x + (-0.04 if x < 0 else 0.04)))
    TR.prism([(-0.93, SKIRT + 0.15), (0.03, SKIRT + 0.15), (0.03, FLOOR - 0.02), (-0.02, FLOOR - 0.02),
              (-0.93, RISE + 0.04)], xa, xb, "x")


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


for name, (shell, cutter, mat) in SHELLS.items():
    cut_shell(shell, cutter, "H95_" + name, mat)
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("H95_" + key, MATS[BUILDER_MAT[key]], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("95-97 Main built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)",
      "| window backs", len(BACKREC))
# Materials, baked lighting and GLB export: run house_95_97_bake.py (it runs this file first).
