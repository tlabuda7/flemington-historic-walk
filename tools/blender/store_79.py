"""
store_79.py - builds 79 Main St, Flemington (west side, south-west corner of Main and Court
Streets): the 3-storey frame "Hardw. & Paints" store of the Sept 1921 Sanborn (32 ft, flat
roof), with its 1-storey rear wing (PLAN.md "79 Main St: "Hardw. & Paints", 3-storey frame
store at the Court St corner").

Evidence: 1921 Sanborn sheet 3 (footprint, 3 storeys, 32 ft, frame, wing; MAP) and the 1950s
colour card flmingtnhtrdnctycrthse50s.jpg (Court St side: 4 windows per upper floor, flat roof
behind a plain cornice band, one chimney about mid-length; PHOTO, used for rhythm and roof form
only). No photo of the Main St front exists: it is a plain GUESS (owner decision 2026-11-12):
two show windows and a recessed centre door, 3 windows per upper floor, plain cornice without
brackets, no sign, no lettering, no awning.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/store_79.py").read())

Every run deletes and rebuilds the "Store79" collection. Materials, lightmap bake and GLB
export: store_79_bake.py (runs this file first). Pattern: store_27.py (one builder per
material, Wall frames, closed wall shells cut by boolean pockets, section-E window backs).

Windows (PLAN.md section E): every pane is ONE glass face (builder Glass -> material `glass`,
not lightmapped in the scene) 4 cm in front of a window back: upper and side windows use cells
of assets/textures/shared/window_backs.jpg (builder WBack), the show windows, door lights and
the door transom cells of assets/textures/shared/shop_interior.jpg (builder ShopInt).
BACKREC[rid] -> UV record (read by the bake).

Coordinates (metres, Blender Z-up), origin = scene (-9.74, 0.15, 14.22) = centre of the front
line at walk level, rotation 0 90 0:
    X  along Main St, +X = north (Court St), -X = south (the 1.77 m alley to 83-87)
    Y  depth: y = 0 is the front wall face; the shop fascia and cornice project to -0.15 / -0.40
    Z  up from the walk top; walls skirt down to -0.20
Scene: world x = -9.74 - Y, world z = 14.22 - X.  North wall X 3.83 = scene z 10.39.
"""

import json
import math
import random
import bpy
import bmesh

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md massing table and elevation details)
# ---------------------------------------------------------------------------
HW = 3.83                       # half front (7.66 m, MAP)
YR = 21.86                      # rear wall of the store (MAP)
SX_REAR = -3.15                 # south wall at the rear (lot line slants 0.68 m, MAP)
SKIRT = -0.20
ROOF_F, ROOF_R = 9.40, 9.10     # flat tin roof behind the cornice, falling to the rear
CORN0, FRZ1, CT, COUT = 9.02, 9.45, 9.75, 0.40   # cornice: bed, frieze top, crown top, projection
RET_S = 1.00                    # cornice return along the south side
WT = 0.22                       # water table top
CB_W, CB_T = 0.15, 0.025        # corner boards
WIN_W = 0.85
UPPER = ((4.65, 6.35), (7.22, 8.84))     # opening bottom (sill) / top, 2nd and 3rd floors
FRONT_U = (-2.45, 0.0, 2.45)
NORTH_U = (3.0, 7.4, 11.8, 16.2)
REAR_X = (-1.26, 1.94)
GF_NORTH = ((3.0, 7.4), (0.90, 2.80))    # north ground-floor windows: Y centres, sill / top
NDOOR = (12.5, 0.95, 2.20)               # north door: Y centre, width, height
# shop front (GUESS, spec)
PIER = 3.45                     # show windows run to +-3.45; corner pilasters outside
SF_D = 0.10                     # shop-front plane set back behind the wall face
BULK, GL0, GL1, BAND1 = 0.55, 0.55, 2.85, 3.35
FAS0, FAS1, FAS_OUT = 3.40, 3.80, 0.15
SW = (0.75, PIER)               # show window |X| range
VX = 0.65                       # vestibule half width
DOOR_D = 0.90                   # door recess
DOOR_T, REC_T = 2.35, 2.85
# rear wing (MAP footprint, height GUESS); its rear end brick (MAP pink part, extent GUESS)
WX0, WX1, WY1 = -3.03, 2.16, 31.78
W_TOP, W_TOP_R = 3.60, 3.25
WB_Y = 29.40                    # brick part from here to the rear
CHIM = (3.08, 3.68, 10.05, 10.95, 11.0)  # chimney x0, x1, y0, y1, top (PHOTO 1950s, height GUESS)


def south_x(y):
    return -HW + (HW + SX_REAR) * y / YR


def roof_z(y):
    return ROOF_F + (ROOF_R - ROOF_F) * y / YR


def wing_z(y):
    return W_TOP + (W_TOP_R - W_TOP) * (y - YR) / (WY1 - YR)


# ---------------------------------------------------------------------------
# Materials (plain stand-ins; store_79_bake.py swaps in the textures)
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


COLOURS = {"Clap": "#B8AF98", "Trim": "#D8D0BC", "Shop": "#2E2E26", "Roof": "#6A4A3C", "Brick": "#8A4A36",
           "Glass": "#1A1916", "WBack": "#2A2420", "ShopInt": "#2A2420"}
MATS = {k: plain("S79_" + k, c) for k, c in COLOURS.items()}
BUILDER_MAT = {k: k for k in COLOURS}


# ---------------------------------------------------------------------------
# Mesh builder (as store_27.py)
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


col = fresh_collection("Store79")
G = {k: MB() for k in BUILDER_MAT}
CL, TR, SP, R, BR, GL, WB, SH = (G[k] for k in ("Clap", "Trim", "Shop", "Roof", "Brick", "Glass", "WBack", "ShopInt"))
# wall shells (closed solids) and their cutters: name -> (shell, cutter, material)
SHELLS = {k: (MB(), MB(), m) for k, m in (("ShellA", "Clap"), ("ShellB", "Clap"), ("ShellBb", "Brick"))}
SA, SB, SBb = (SHELLS[k][0] for k in SHELLS)
KA, KB, KBb = (SHELLS[k][1] for k in SHELLS)

FRONT = Wall((0.0, 0.0), (0, -1), KA)          # u = X
NORTH = Wall((HW, 0.0), (1, 0), KA)            # u = Y (to the right seen from Court St)
REAR = Wall((0.0, YR), (0, 1), KA)             # u = -X
W_REAR = Wall((0.0, WY1), (0, 1), KBb)         # wing rear (brick part), u = -X

# ---------------------------------------------------------------------------
# Window backs (section E): cells of the shared atlases, no repeats side by side
# ---------------------------------------------------------------------------
WB_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\window_backs.json"))["cells"]
SHOP_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\shop_interior.json"))["cells"]
GAP = 0.04
# upstairs over a hardware store: stock rooms (blinds, dark) and a dwelling (lace, curtains)
UPSTAIRS = {"blind_cream_high": 3, "blind_cream_half": 3, "blind_cream_low": 2, "blind_green_half": 2,
            "dark_room": 2, "dark_room_frame": 2, "lace_blind_cream": 2, "lace": 1, "curtains_beige": 1,
            "blind_cream_full": 1}
_wb_rng = random.Random(1921 + 79)
BACKREC = {}


def pick_row(weights, n):
    out = []
    for _ in range(n):
        names = [k for k in weights if not out or k != out[-1]]
        out.append(_wb_rng.choices(names, weights=[weights[k] for k in names])[0])
    return out


def crop_uv(uv, aspect):
    """Centred crop of an atlas rectangle to aspect w/h (rooms not stretched), 1.5 px inset."""
    U0, V0, U1, V1 = uv
    e = 1.5 / 1024
    U0, V0, U1, V1 = U0 + e, V0 + e, U1 - e, V1 - e
    a = (U1 - U0) / (V1 - V0) * 1.0
    if aspect < a:
        w, c = (U1 - U0) * aspect / a, (U0 + U1) / 2
        U0, U1 = c - w / 2, c + w / 2
    else:
        h, c = (V1 - V0) * a / aspect, (V0 + V1) / 2
        V0, V1 = c - h / 2, c + h / 2
    return (U0, V0, U1, V1)


def back(wall, u0, u1, z0, z1, d, cell, flip=False):
    """Window back: one face on the wall plane at depth d. Cells "S:<name>" come from the
    shop_interior atlas, the others from window_backs. flip mirrors the cell."""
    shop = cell.startswith("S:")
    key = cell[2:] if shop else cell
    cells = SHOP_CELLS if shop else WB_CELLS
    mb = SH if shop else WB
    rid = len(BACKREC) + 1
    U0, V0, U1, V1 = crop_uv(cells[key]["uv"], (u1 - u0) / (z1 - z0))
    if flip:
        U0, U1 = U1, U0
    BACKREC[rid] = dict(wall=(wall.p0, wall.n), u0=u0, u1=u1, z0=z0, z1=z1, uv=(U0, V0, U1, V1))
    mb.rid = rid
    mb.quad(wall, u0, u1, z0, z1, d)
    mb.rid = 0


def pane(wall, u0, u1, z0, z1, d_glass, cell, flip=False):
    """Glass face at depth d_glass with its window back GAP behind it."""
    back(wall, u0, u1, z0, z1, d_glass - GAP, cell, flip)
    GL.quad(wall, u0, u1, z0, z1, d_glass)


# ---------------------------------------------------------------------------
# Shells: A (store, one closed solid with a sloping top), B (wing, clapboard) + Bb (brick end)
# ---------------------------------------------------------------------------
sxr = SX_REAR
SA.solid([(-HW, 0, SKIRT), (HW, 0, SKIRT), (HW, YR, SKIRT), (sxr, YR, SKIRT),
          (-HW, 0, roof_z(0)), (HW, 0, roof_z(0)), (HW, YR, roof_z(YR)), (sxr, YR, roof_z(YR))],
         [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
SB.prism([(YR - 0.05, SKIRT), (WB_Y, SKIRT), (WB_Y, wing_z(WB_Y)), (YR - 0.05, wing_z(YR - 0.05))], WX0, WX1, "x")
SBb.prism([(WB_Y, SKIRT), (WY1, SKIRT), (WY1, wing_z(WY1)), (WB_Y, wing_z(WB_Y))], WX0, WX1, "x")


# ---------------------------------------------------------------------------
# Double-hung 2/2 window: cased opening, frame, dark sashes, sill and apron
# ---------------------------------------------------------------------------
def window(wall, cu, z0, z1, cell, w=WIN_W):
    hw = w / 2
    u0, u1 = cu - hw, cu + hw
    wall.cut.wbox(wall, u0, u1, z0, z1, 0.25, -0.22)                     # opening
    # frame (cream) lining the reveal; sub-sill
    TR.wbox(wall, u0, u0 + 0.05, z0, z1, -0.22, 0.0)
    TR.wbox(wall, u1 - 0.05, u1, z0, z1, -0.22, 0.0)
    TR.wbox(wall, u0 + 0.05, u1 - 0.05, z1 - 0.05, z1, -0.22, 0.0)
    TR.wbox(wall, u0 + 0.05, u1 - 0.05, z0, z0 + 0.04, -0.22, 0.0)
    a, b = u0 + 0.05, u1 - 0.05
    g0, g1 = z0 + 0.04, z1 - 0.05
    pane(wall, a, b, g0, g1, -0.13, cell)
    # sashes (dark): stiles, top / meeting / bottom rails, one muntin per sash (2/2)
    zm = (g0 + g1) / 2
    SP.wbox(wall, a, a + 0.045, g0, g1, -0.115, -0.045)
    SP.wbox(wall, b - 0.045, b, g0, g1, -0.115, -0.045)
    SP.wbox(wall, a + 0.045, b - 0.045, g1 - 0.055, g1, -0.115, -0.045)
    SP.wbox(wall, a + 0.045, b - 0.045, zm - 0.03, zm + 0.03, -0.115, -0.04)
    SP.wbox(wall, a + 0.045, b - 0.045, g0, g0 + 0.08, -0.115, -0.07)
    SP.wbox(wall, cu - 0.012, cu + 0.012, g0 + 0.08, g1 - 0.055, -0.105, -0.06)
    # casing: side boards, head board with a drip cap; sill and apron
    TR.wbox(wall, u0 - 0.10, u0, z0, z1, 0.0, 0.025)
    TR.wbox(wall, u1, u1 + 0.10, z0, z1, 0.0, 0.025)
    TR.wbox(wall, u0 - 0.10, u1 + 0.10, z1, z1 + 0.14, 0.0, 0.03)
    TR.wbox(wall, u0 - 0.13, u1 + 0.13, z1 + 0.14, z1 + 0.17, 0.0, 0.06)
    TR.wbox(wall, u0 - 0.14, u1 + 0.14, z0 - 0.045, z0, -0.03, 0.065)
    TR.wbox(wall, u0 - 0.08, u1 + 0.08, z0 - 0.15, z0 - 0.045, 0.0, 0.02)


cells_front = [pick_row(UPSTAIRS, 3) for _ in UPPER]
for (z0, z1), cells in zip(UPPER, cells_front):
    for u, c in zip(FRONT_U, cells):
        window(FRONT, u, z0, z1, c)
cells_north = [pick_row(UPSTAIRS, 4) for _ in UPPER]
for (z0, z1), cells in zip(UPPER, cells_north):
    for u, c in zip(NORTH_U, cells):
        window(NORTH, u, z0, z1, c)
for u, c in zip(GF_NORTH[0], ("dark_room_frame", "blind_cream_low")):   # stock room behind the shop
    window(NORTH, u, GF_NORTH[1][0], GF_NORTH[1][1], c)
for z0, z1 in UPPER:
    for x, c in zip(REAR_X, pick_row(UPSTAIRS, 2)):
        window(REAR, -x, z0, z1, c)

# ---------------------------------------------------------------------------
# Cornice: plain boxed frieze 9.05-9.45 and crown to 9.75 projecting 0.40, no brackets; along
# the front, the whole Court St side, and a 1 m return on the south side (PHOTO 1950s: band)
# ---------------------------------------------------------------------------
CPROF = [(-0.15, CORN0), (0.06, CORN0), (0.06, CORN0 + 0.05), (0.035, CORN0 + 0.07), (0.035, FRZ1 - 0.06),
         (0.07, FRZ1 - 0.04), (0.10, FRZ1), (COUT - 0.04, FRZ1), (COUT - 0.04, CT - 0.15),
         (COUT - 0.02, CT - 0.12), (COUT, CT - 0.08), (COUT, CT), (-0.15, CT)]
sweep_plan(TR, [(south_x(RET_S), RET_S), (-HW, 0.0), (HW, 0.0), (HW, YR)], CPROF)

# roof: tin slab on the store (top 4 cm over the shell; 3 cm over the south and rear walls),
# coping on the rear wall; chimney (brick, corbelled cap) near the north edge
RT = 0.06
rz = lambda y: roof_z(y) + 0.04
o = 0.03
R.solid([(-HW - o, 0.0, rz(0) - RT), (HW, 0.0, rz(0) - RT), (HW, YR + o, rz(YR + o) - RT), (sxr - o, YR + o, rz(YR + o) - RT),
         (-HW - o, 0.0, rz(0)), (HW, 0.0, rz(0)), (HW, YR + o, rz(YR + o)), (sxr - o, YR + o, rz(YR + o))],
        [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
cx0, cx1, cy0, cy1, ctop = CHIM
BR.box(cx0, cx1, cy0, cy1, roof_z(cy1) - 0.1, ctop - 0.16)
BR.box(cx0 - 0.05, cx1 + 0.05, cy0 - 0.05, cy1 + 0.05, ctop - 0.16, ctop - 0.06)
BR.box(cx0 - 0.02, cx1 + 0.02, cy0 - 0.02, cy1 + 0.02, ctop - 0.06, ctop)

# ---------------------------------------------------------------------------
# Corner boards, water table
# ---------------------------------------------------------------------------
TOPB = CORN0 + 0.02
# front corners above the shop fascia (the pilasters below), and down the side walls
for s in (-1, 1):
    xa, xb = sorted((s * (HW - CB_W), s * (HW + CB_T)))
    TR.box(xa, xb, -CB_T, 0.01, FAS1, TOPB)
    xa, xb = sorted((s * (HW - 0.01), s * (HW + CB_T)))
    TR.box(xa, xb, -CB_T, CB_W, FAS0, TOPB)        # below the fascia the pilaster return
# rear corners
TR.box(HW - CB_W, HW + CB_T, YR - 0.01, YR + CB_T, WT, TOPB)
TR.box(HW - 0.01, HW + CB_T, YR - CB_W, YR + CB_T, WT, TOPB)
TR.box(sxr - CB_T, sxr + CB_W, YR - 0.01, YR + CB_T, WT, roof_z(YR) + 0.04)
TR.box(sxr - CB_T, sxr + 0.01, YR - CB_W, YR + CB_T, WT, roof_z(YR) + 0.04)
# water table (plain board with a drip cap) around the side and rear walls
WTPROF = [(-0.05, SKIRT), (0.03, SKIRT), (0.03, WT - 0.01), (0.05, WT), (0.05, WT + 0.02), (0.0, WT + 0.05),
          (-0.05, WT + 0.05)]
sweep_plan(TR, [(HW, CB_W), (HW, YR), (sxr, YR), (south_x(CB_W), CB_W)], WTPROF)

# ---------------------------------------------------------------------------
# Shop front (GUESS, plain): corner pilasters, fascia, two show windows on panelled bulkheads,
# plain panelled transom band, centre pair of half-glazed doors in a 0.90 recess
# ---------------------------------------------------------------------------
KA.box(-PIER, PIER, -0.25, 0.30, -0.30, FAS0)                              # shop-front pocket
KA.box(-VX, VX, -0.25, SF_D + DOOR_D + 0.05, -0.30, REC_T)                 # door recess
# corner pilasters: board facing, plinth and cap
for s in (-1, 1):
    xa, xb = sorted((s * PIER, s * (HW + CB_T)))
    SP.box(xa, xb, -0.03, 0.01, SKIRT, FAS0 - 0.10)
    xa2, xb2 = sorted((s * (PIER - 0.01), s * (HW + CB_T + 0.01)))
    SP.box(xa2, xb2, -0.05, 0.01, SKIRT, 0.30)
    SP.box(xa2, xb2, -0.06, 0.01, FAS0 - 0.10, FAS0)
    # the pilaster returns on the side walls (the first 0.15 m)
    xa, xb = sorted((s * (HW - 0.01), s * (HW + CB_T + 0.01)))
    SP.box(xa, xb, -0.03, CB_W, SKIRT, FAS0)
# fascia board with a bed mould and a cap moulding, returned on the side walls
SP.box(-HW - 0.04, HW + 0.04, -FAS_OUT, 0.01, FAS0, FAS1)
SP.box(-HW - 0.05, HW + 0.05, -FAS_OUT - 0.02, 0.01, FAS0 - 0.04, FAS0 + 0.02)
TR.box(-HW - 0.07, HW + 0.07, -FAS_OUT - 0.05, 0.01, FAS1, FAS1 + 0.05)
TR.box(-HW - 0.05, HW + 0.05, -FAS_OUT - 0.03, 0.01, FAS1 + 0.05, FAS1 + 0.08)
for s in (-1, 1):
    xa, xb = sorted((s * HW, s * (HW + 0.04)))
    SP.box(xa, xb, -FAS_OUT, CB_W + 0.02, FAS0, FAS1)
    xa, xb = sorted((s * HW, s * (HW + 0.07)))
    TR.box(xa, xb, -FAS_OUT - 0.05, CB_W + 0.04, FAS1, FAS1 + 0.05)

Y0 = SF_D                                       # shop-front face


def show_window(x0, x1, cell, flip):
    """Dark bulkhead with two raised panels, sill rail, plate glass on a shop_interior cell,
    head rail, plain panelled transom band."""
    SP.box(x0, x1, Y0, 0.30, -0.02, BULK)                                    # bulkhead
    xm = (x0 + x1) / 2
    for a, b in ((x0 + 0.14, xm - 0.05), (xm + 0.05, x1 - 0.14)):
        SP.box(a, b, Y0 - 0.015, Y0, 0.12, BULK - 0.12)                       # raised panels
    SP.box(x0 - 0.02, x1 + 0.02, Y0 - 0.06, 0.30, GL0 - 0.04, GL0 + 0.03)      # sill rail
    SP.box(x0, x1, Y0 - 0.01, 0.30, GL1 - 0.05, GL1 + 0.05)                    # head rail
    for a, b in ((x0, x0 + 0.09), (x1 - 0.09, x1)):
        SP.box(a, b, Y0 - 0.01, 0.30, GL0, GL1)                               # jamb posts
    pane(FRONT, x0 + 0.09, x1 - 0.09, GL0 + 0.03, GL1 - 0.05, -(Y0 + 0.04), cell, flip)
    SP.box(x0, x1, Y0, 0.30, GL1 + 0.05, BAND1)                               # transom band
    SP.box(x0 + 0.12, x1 - 0.12, Y0 - 0.015, Y0, GL1 + 0.14, BAND1 - 0.09)      # its raised panel
    SP.box(x0 - 0.02, x1 + 0.02, Y0 - 0.04, 0.30, BAND1, FAS0)                 # head moulding


for s in (-1, 1):                                                          # pocket side linings
    xa, xb = sorted((s * (PIER - 0.02), s * PIER))
    SP.box(xa, xb, -0.01, Y0 + 0.01, -0.02, FAS0)
SP.box(-PIER, PIER, -0.01, 0.30, FAS0 - 0.02, FAS0)                         # pocket soffit lining
show_window(-SW[1], -SW[0], "S:shop_a", False)
show_window(SW[0], SW[1], "S:shop_a", True)
# posts between the show windows and the vestibule, band over the vestibule opening
for s in (-1, 1):
    xa, xb = sorted((s * VX, s * SW[0]))
    SP.box(xa, xb, Y0 - 0.01, 0.30, -0.02, BAND1)
SP.box(-VX, VX, Y0, 0.30, REC_T, BAND1)
SP.box(-VX - 0.02, VX + 0.02, Y0 - 0.04, 0.30, BAND1, FAS0)

# vestibule: floor (pale stone), dark panelled linings and ceiling, door frame, doors, transom
YD = Y0 + DOOR_D
TR.box(-VX, VX, -0.02, YD + 0.02, SKIRT, 0.02)                                 # floor / threshold
for s in (-1, 1):
    xa, xb = sorted((s * VX, s * (VX - 0.03)))
    SP.box(xa, xb, Y0, YD, 0.02, REC_T)                                       # side linings
    xa, xb = sorted((s * (VX - 0.03), s * (VX - 0.045)))
    for z0, z1 in ((0.15, 1.00), (1.15, 2.65)):
        SP.box(xa, xb, Y0 + 0.12, YD - 0.12, z0, z1)                          # raised panels
SP.box(-VX, VX, Y0, YD, REC_T - 0.03, REC_T)                                  # ceiling
for a, b in ((-VX + 0.03, -VX + 0.08), (VX - 0.08, VX - 0.03)):
    SP.box(a, b, YD - 0.03, YD + 0.03, 0.02, REC_T)                           # door frame
SP.box(-VX + 0.03, VX - 0.03, YD - 0.04, YD + 0.03, DOOR_T, DOOR_T + 0.08)      # transom bar
pane(FRONT, -VX + 0.08, VX - 0.08, DOOR_T + 0.08, REC_T - 0.03, -(YD + 0.01), "S:transom_door")
DL = -VX + 0.08
for (a, b), cell in (((DL, 0.0), "S:door_l"), ((0.0, -DL), "S:door_r")):
    g0, g1 = a + 0.10, b - 0.10
    SP.box(a, g0, YD - 0.02, YD + 0.02, 0.02, DOOR_T)                          # stiles
    SP.box(g1, b, YD - 0.02, YD + 0.02, 0.02, DOOR_T)
    SP.box(g0, g1, YD - 0.02, YD + 0.02, 0.02, 1.00)                           # lock rail + panel
    SP.box(g0, g1, YD - 0.02, YD + 0.02, DOOR_T - 0.12, DOOR_T)                # top rail
    SP.box(g0 + 0.04, g1 - 0.04, YD - 0.035, YD - 0.02, 0.18, 0.86)            # raised panel
    pane(FRONT, g0, g1, 1.00, DOOR_T - 0.12, -(YD + 0.005), cell)
SP.box(-0.015, 0.015, YD - 0.035, YD - 0.02, 0.02, DOOR_T)                    # astragal

# ---------------------------------------------------------------------------
# North door (Court St, GUESS): plain 4-panel door, cased, with a stone sill
# ---------------------------------------------------------------------------
du, dw, dh = NDOOR
u0, u1 = du - dw / 2, du + dw / 2
KA.wbox(NORTH, u0, u1, -0.30, dh, 0.25, -0.20)
TR.wbox(NORTH, u0, u0 + 0.05, -0.02, dh, -0.20, 0.0)
TR.wbox(NORTH, u1 - 0.05, u1, -0.02, dh, -0.20, 0.0)
TR.wbox(NORTH, u0 + 0.05, u1 - 0.05, dh - 0.05, dh, -0.20, 0.0)
a, b = u0 + 0.05, u1 - 0.05
SP.wbox(NORTH, a, b, 0.04, dh - 0.05, -0.16, -0.12)                          # door leaf
pw = (b - a - 0.30) / 2
for z0, z1 in ((0.20, 0.95), (1.15, dh - 0.20)):
    for k in range(2):
        pa = a + 0.10 + k * (pw + 0.10)
        SP.wbox(NORTH, pa, pa + pw, z0, z1, -0.12, -0.105)                    # raised panels
TR.wbox(NORTH, u0 - 0.12, u0, -0.02, dh, 0.0, 0.03)                           # casing
TR.wbox(NORTH, u1, u1 + 0.12, -0.02, dh, 0.0, 0.03)
TR.wbox(NORTH, u0 - 0.12, u1 + 0.12, dh, dh + 0.16, 0.0, 0.035)
TR.wbox(NORTH, u0 - 0.15, u1 + 0.15, dh + 0.16, dh + 0.19, 0.0, 0.07)
TR.wbox(NORTH, u0 - 0.05, u1 + 0.05, SKIRT, 0.04, -0.20, 0.12)                # stone sill

# ---------------------------------------------------------------------------
# Rear wing B: shed roof falling to the rear; clapboard front part, brick rear end (MAP); one
# plain plank rear door (GUESS); corner boards and water table on the clapboard part
# ---------------------------------------------------------------------------
sl = (W_TOP - W_TOP_R) / (WY1 - YR)
R.prism([(YR - 0.02, wing_z(YR - 0.02) - 0.01), (WY1 + 0.15, wing_z(WY1 + 0.15) - 0.01),
         (WY1 + 0.15, wing_z(WY1 + 0.15) + 0.05), (YR - 0.02, wing_z(YR - 0.02) + 0.05)], WX0 - 0.12, WX1 + 0.12, "x")
for x in (WX0, WX1):
    s = 1 if x > 0 else -1
    xa, xb = sorted((x - s * 0.01, x + s * CB_T))
    TR.box(xa, xb, WB_Y - CB_W, WB_Y + 0.01, WT, wing_z(WB_Y))            # corner boards at the brick part
    TR.box(xa, xb, YR, YR + CB_W, WT, wing_z(YR + CB_W))
    TR.box(xa, xb, YR, WB_Y, SKIRT, WT)                                     # water table
    xa, xb = sorted((x - s * 0.01, x + s * 0.05))
    TR.box(xa, xb, YR, WB_Y, WT, WT + 0.03)
du, dw, dh = 1.5, 0.90, 2.05
KBb.wbox(W_REAR, du - dw / 2, du + dw / 2, -0.30, dh, 0.25, -0.12)
SP.wbox(W_REAR, du - dw / 2, du + dw / 2, -0.02, dh, -0.12, -0.08)
for z in (0.30, 1.00, 1.70):
    SP.wbox(W_REAR, du - dw / 2 + 0.05, du + dw / 2 - 0.05, z, z + 0.12, -0.08, -0.065)    # battens
SP.wbox(W_REAR, du - 0.02, du + 0.02, 0.0, dh, -0.08, -0.065)
TR.wbox(W_REAR, du - dw / 2 - 0.06, du + dw / 2 + 0.06, SKIRT, 0.02, -0.10, 0.25)          # stone step
TR.wbox(W_REAR, du - dw / 2 - 0.05, du + dw / 2 + 0.05, dh, dh + 0.12, -0.02, 0.04)        # lintel


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
    cut_shell(shell, cutter, "S79_" + name, mat)
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("S79_" + key, MATS[BUILDER_MAT[key]], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Store 79 built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)",
      "| window backs", len(BACKREC))
# Materials, baked lighting and GLB export: run store_79_bake.py (it runs this file first).
