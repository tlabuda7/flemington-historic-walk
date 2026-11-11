"""
block_24_30.py - builds the three small frame buildings at 24-30 Main St, Flemington (east side,
north of the 32-38 row), as they stood in Sept 1921 (Sanborn sheet 2), in ONE model:
  A  no. 24, dwelling ("D"): 2-storey front part with its GABLE END to the street (A1), a
     narrower 2-storey rear part (A2), a 1-storey rear part (A3), an open 1-storey front porch on
     4 plain posts (A4) and an open rear porch with a shingle roof (A5)
  B  no. 26, millinery ("Mill'y"), touching 24: 2 storeys, low shed roof (B1), 1-storey rear
     cells (B2a, B2b), a deep open 1-storey porch over the WHOLE sidewalk on 3 plain posts
     standing on the curb (B3, full map depth 4.30 m, owner decision 2026-11-11 via the street-
     geometry addendum) and a 5-facet bay shop window on the ground floor (B4)
  -- an open 2.66 m gap --
  C  nos. 28-30, "Conf'y" and "Barber": one 2-storey block (C1) with a 1-storey open notch at
     30's rear (C2), a 1-storey rear addition behind 28 (C3) and a narrow open TWO-TIER porch on
     5 plain posts per tier, railing on the upper tier only (C4)

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/block_24_30.py").read())

Every run deletes and rebuilds the "Block2430" collection. Materials, lightmap bake and GLB
export: block_24_30_bake.py (runs this file first). Pattern: block_32_38.py (builders per
material, Wall frames, closed wall shells with shallow boolean recesses); section-E windows as
store_100_102.py (every pane one glass face 4 cm in front of a window back; the backs, shop
cells included, come from assets/textures/shared/window_backs.jpg, room views cropped to the
pane's aspect, never stretched).

Sources: PLAN.md "Houses and shops at 24-30 Main St" (1921 Sanborn footprints, storeys, porches,
bay). No photo shows any of these fronts: every elevation is a plain GUESS approved by the owner
on 2026-11-11 (no signs, lettering, awnings, shutters, brackets, barber pole or chimneys).

Coordinates (metres, Blender Z-up), origin = scene (7.29, 0.15, -152.365), rotation 0 -90 0:
    X  along the street, +X = south (32-38), -X = north (no. 22)
    Y  depth: y = 0 is 24's porch front; 24 and 26 front wall 1.41; 28-30 front wall 1.94;
       26's porch reaches y = -2.89 (world x 4.40, the curb)
    Z  up from the sidewalk top; walls skirt down to -0.20; yards at -0.15
Scene <- local: x = 7.29 + Y, z = -152.365 + X.
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".
"""

import json
import math
import random
import bpy
import bmesh

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md massing table; every height is a guess, the map writes none)
# ---------------------------------------------------------------------------
SKIRT = -0.20
DECK = 0.15
RECESS = 0.25
T30 = math.tan(math.radians(30))
# A: no. 24
AX0, AX1 = -11.51, -4.82            # front part (A1)
AFW, AY1 = 1.41, 10.00
A_EAVE, A_RIDGE = 5.90, 5.90 + (AX1 - AX0) / 2 * T30      # 7.83
A_XC = (AX0 + AX1) / 2
A2X1, A2Y1 = -6.77, 18.08           # rear part (A2)
A2_EAVE = 5.60
A2_XC = (AX0 + A2X1) / 2
A2_RIDGE = A2_EAVE + (A2X1 - AX0) / 2 * T30                # 6.97
A3Y1 = 22.14                         # 1-storey rear (A3)
A5X1, A5Y0 = -5.65, 13.96           # rear porch (A5)
A_DECK = 0.18
# B: no. 26
BX0, BX1 = -4.82, -0.18
BFW, BY1 = 1.41, 10.00
B_TOP_F, B_TOP_R = 6.10, 5.60
B2A = (-6.77, -0.13, 10.00, 13.94)
B2B = (-3.23, -0.05, 13.94, 17.69)
B_PORCH_X = (-4.82, -0.20)
B_PORCH_Y0 = -2.89                   # roof edge = map front of the porch (world x 4.40)
B_POST_Y = -2.80                     # post centres (faces -2.87 ... -2.73, on the curb)
# C: nos. 28-30
CX0, CX1, CP = 2.55, 11.51, 7.09
CFW, CY1 = 1.94, 15.89
C_TOP_F, C_TOP_R = 6.30, 5.60
NOTCH = (7.09, 8.86, 13.96)          # C2: X from, X to, Y from (to CY1)
C3 = (4.32, 7.16, 19.59)             # rear addition: X from, X to, Y to
C_PORCH_Y0 = 0.65
LOW_TOP = 3.00                       # 1-storey rear parts at their front
LOW_FALL = 0.20                      # ... falling to the rear by this much


def b_top(y):
    return B_TOP_F + (B_TOP_R - B_TOP_F) * (y - BFW) / (BY1 - BFW)


def c_top(y):
    return C_TOP_F + (C_TOP_R - C_TOP_F) * (y - CFW) / (CY1 - CFW)


# ---------------------------------------------------------------------------
# Materials (plain stand-ins; block_24_30_bake.py swaps in the textures)
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


COLOURS = {"Clap24": "#E2DED2", "Clap26": "#D8CFB8", "Clap2830": "#C4B99F", "Trim": "#DDD5C2",
           "Roof": "#5A3D34", "Slate": "#6E6B66", "Wood": "#2E2E26", "Deck": "#5A4C42",
           "Glass": "#1A1916", "WBack": "#2A2420"}
MATS = {k: plain("HS_" + k, c) for k, c in COLOURS.items()}
# builder -> material (the bake gives every builder its own UVs and tint)
BUILDER_MAT = {"Trim": "Trim", "Roof": "Roof", "Shingle": "Roof", "Slate": "Slate", "Wood": "Wood",
               "Deck": "Deck", "Glass": "Glass", "WBack": "WBack"}

# ---------------------------------------------------------------------------
# Mesh builder (as block_32_38.py)
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
    """Collects closed solids for one builder. Faces get the current `rid` (atlas record)."""

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
        return a, b

    def prism(self, pts, d0, d1, axis="y"):
        """Extrude a 2D outline between depths d0 and d1 along an axis ('y': outline in X-Z;
        'x': outline in Y-Z; 'z': plan outline in X-Y)."""
        return self._extrude([self._pt(axis, u, d0, v) for u, v in pts],
                             [self._pt(axis, u, d1, v) for u, v in pts])

    def plan_shed(self, pts, z0, top):
        """Plan outline (X-Y) extruded from z0 up; the top vertices set to top(y)."""
        a, b = self.prism(pts, z0, 1.0, axis="z")
        for v in b:
            v.co.z = top(v.co.y)
        bmesh.ops.recalc_face_normals(self.bm, faces=list({f for v in a + b for f in v.link_faces}))

    def box(self, x0, x1, y0, y1, z0, z1):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)

    def wprism(self, wall, pts, d0, d1):
        self._extrude([wall.pt(u, z, d0) for u, z in pts], [wall.pt(u, z, d1) for u, z in pts])

    def wbox(self, wall, u0, u1, z0, z1, d0, d1):
        self.wprism(wall, rect(u0, u1, z0, z1), d0, d1)

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


col = fresh_collection("Block2430")
G = {k: MB() for k in BUILDER_MAT}
T, R, SG, SL, W, DK, GL, WB = (G[k] for k in ("Trim", "Roof", "Shingle", "Slate", "Wood", "Deck", "Glass",
                                              "WBack"))
# wall shells (closed solids) and their cutters: name -> (shell, cutter, material)
SHELL_MAT = {"ShellA1": "Clap24", "ShellA2": "Clap24", "ShellA3": "Clap24",
             "ShellB1": "Clap26", "ShellB2a": "Clap26", "ShellB2b": "Clap26",
             "ShellC1": "Clap2830", "ShellC3": "Clap2830"}
SHELLS = {k: (MB(), MB(), m) for k, m in SHELL_MAT.items()}
S = {k: v[0] for k, v in SHELLS.items()}
K = {k: v[1] for k, v in SHELLS.items()}

# ---------------------------------------------------------------------------
# Window backs (section E, as store_100_102.py): cells of shared/window_backs.jpg, picked so
# that no two windows side by side show the same cell; the room views (shop cells) are cropped
# to the pane's aspect. BACKREC[rid] -> UV record (read by the bake).
# ---------------------------------------------------------------------------
WB_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\window_backs.json"))["cells"]
CROPPED = ("shop_a", "shop_b", "door", "return", "transom")
GAP = 0.04                      # window back this far behind the glass
UPPER = {"lace": 2, "lace_blind_cream": 2, "lace_blind_green": 1, "curtains_beige": 2, "curtains_olive": 1,
         "blind_cream_half": 2, "blind_cream_high": 1, "blind_green_half": 1, "dark_room_frame": 1,
         "curtains_maroon_blind": 1}
_wb_rng = random.Random(2430)
_wb_grid = {}
BACKREC = {}


def pick(weights, wall, row, colm):
    g = _wb_grid.setdefault(wall, {})
    avoid = {g.get((row, colm - 1)), g.get((row, colm + 1)), g.get((row - 1, colm)), g.get((row + 1, colm))}
    names = [n for n in weights if n not in avoid]
    cell = _wb_rng.choices(names, weights=[weights[n] for n in names])[0]
    g[(row, colm)] = cell
    return cell


def cell_uv(cell, aspect=None):
    """Atlas rectangle of a cell; room views cropped (centred) to `aspect` (w/h). 1.5 px inset."""
    U0, V0, U1, V1 = WB_CELLS[cell]["uv"]
    e = 1.5 / 1024
    U0, V0, U1, V1 = U0 + e, V0 + e, U1 - e, V1 - e
    if aspect and cell in CROPPED:
        a = (U1 - U0) / (V1 - V0)
        if aspect < a:
            w, c = (U1 - U0) * aspect / a, (U0 + U1) / 2
            U0, U1 = c - w / 2, c + w / 2
        else:
            h, c = (V1 - V0) * a / aspect, (V0 + V1) / 2
            V0, V1 = c - h / 2, c + h / 2
    return U0, V0, U1, V1


def back(wall, u0, u1, z0, z1, d, cell, frame=None):
    """Window back: one face on the wall plane at depth d (negative = into the wall). frame =
    (u0, u1, z0, z1) the cell spans (several panes of one window share one view)."""
    fu0, fu1, fz0, fz1 = frame or (u0, u1, z0, z1)
    U0, V0, U1, V1 = cell_uv(cell, (fu1 - fu0) / (fz1 - fz0))
    su = lambda u: U0 + (U1 - U0) * (u - fu0) / (fu1 - fu0)
    sv = lambda z: V0 + (V1 - V0) * (z - fz0) / (fz1 - fz0)
    rid = len(BACKREC) + 1
    BACKREC[rid] = dict(wall=(wall.p0, wall.n), u0=u0, u1=u1, z0=z0, z1=z1,
                        uv=(su(u0), sv(z0), su(u1), sv(z1)))
    WB.rid = rid
    WB.quad(wall, u0, u1, z0, z1, d)
    WB.rid = 0


def pane(wall, u0, u1, z0, z1, d_glass, cell, frame=None):
    """Glass face at depth d_glass with its window back GAP behind it."""
    back(wall, u0, u1, z0, z1, d_glass - GAP, cell, frame)
    GL.quad(wall, u0, u1, z0, z1, d_glass)


# ---------------------------------------------------------------------------
# Shells
# ---------------------------------------------------------------------------


def gable_shell(sh, x0, x1, y0, y1, eave, ridge):
    xc = (x0 + x1) / 2
    sh.prism([(x0, SKIRT), (x1, SKIRT), (x1, eave), (xc, ridge), (x0, eave)], y0, y1, axis="y")


def shed_shell(sh, x0, x1, y0, y1, z_f, z_r):
    sh.prism([(y0, SKIRT), (y1, SKIRT), (y1, z_r), (y0, z_f)], x0, x1, axis="x")


gable_shell(S["ShellA1"], AX0, AX1, AFW, AY1, A_EAVE, A_RIDGE)
gable_shell(S["ShellA2"], AX0, A2X1, AY1, A2Y1, A2_EAVE, A2_RIDGE)
shed_shell(S["ShellA3"], AX0, A2X1, A2Y1, A3Y1, LOW_TOP, LOW_TOP - LOW_FALL)
shed_shell(S["ShellB1"], BX0, BX1, BFW, BY1, B_TOP_F, B_TOP_R)
shed_shell(S["ShellB2a"], B2A[0], B2A[1], B2A[2], B2A[3], LOW_TOP, LOW_TOP - 0.15)
shed_shell(S["ShellB2b"], B2B[0], B2B[1], B2B[2], B2B[3], LOW_TOP, LOW_TOP - LOW_FALL)
C_PLAN = [(CX0, CFW), (CX1, CFW), (CX1, CY1), (NOTCH[1], CY1), (NOTCH[1], NOTCH[2]), (NOTCH[0], NOTCH[2]),
          (NOTCH[0], CY1), (CX0, CY1)]
S["ShellC1"].plan_shed(C_PLAN, SKIRT, c_top)
shed_shell(S["ShellC3"], C3[0], C3[1], CY1, C3[2], LOW_TOP, LOW_TOP - LOW_FALL)

# Walls (u: FRONT +x, rear walls -x)
A_FRONT = Wall((0.0, AFW), (0, -1), K["ShellA1"])
B_FRONT = Wall((0.0, BFW), (0, -1), K["ShellB1"])
C_FRONT = Wall((0.0, CFW), (0, -1), K["ShellC1"])
A3_REAR = Wall((0.0, A3Y1), (0, 1), K["ShellA3"])
B2B_REAR = Wall((0.0, B2B[3]), (0, 1), K["ShellB2b"])
C3_REAR = Wall((0.0, C3[2]), (0, 1), K["ShellC3"])
C2_BACK = Wall((0.0, NOTCH[2]), (0, 1), K["ShellC1"])

# ---------------------------------------------------------------------------
# Openings (all GUESS, plain)
# ---------------------------------------------------------------------------


def window(wall, cu, z0, w, h, cell, muntin=False):
    """Sash window in a 0.25 recess: one glass face 4 cm in front of a window back (section E),
    sash rails (2/2 with a centre muntin when muntin=True), plain pale casing 0.10 and sill."""
    hw = w / 2
    z1 = z0 + h
    wall.cut.wbox(wall, cu - hw, cu + hw, z0, z1, -RECESS, 0.25)
    pane(wall, cu - hw, cu + hw, z0, z1, -0.17, cell)
    zm = z0 + h / 2
    s = 0.05
    T.wbox(wall, cu - hw, cu + hw, z1 - s, z1, -0.15, -0.09)                 # top rail
    T.wbox(wall, cu - hw, cu + hw, z0, z0 + 0.07, -0.15, -0.09)              # bottom rail
    for a in (cu - hw, cu + hw - s):
        T.wbox(wall, a, a + s, z0 + 0.07, z1 - s, -0.15, -0.09)              # stiles
    T.wbox(wall, cu - hw, cu + hw, zm - 0.03, zm + 0.03, -0.15, -0.10)       # meeting rail
    if muntin:
        T.wbox(wall, cu - 0.015, cu + 0.015, z0 + 0.07, z1 - s, -0.15, -0.115)
    c = 0.10
    T.wbox(wall, cu - hw - c, cu - hw, z0, z1 + c, -0.02, 0.03)              # casing
    T.wbox(wall, cu + hw, cu + hw + c, z0, z1 + c, -0.02, 0.03)
    T.wbox(wall, cu - hw, cu + hw, z1, z1 + c, -0.02, 0.03)
    T.wbox(wall, cu - hw - c - 0.03, cu + hw + c + 0.03, z0 - 0.05, z0, -0.16, 0.06)   # sill


def shop_window(wall, x0, x1, cell, base=DECK):
    """Shop window in the wall plane: dark wood bulkhead with a raised panel (base-0.75), sill
    rail, stiles, head rail, centre mullion, one glass face per light over the shop view
    (0.80-2.75), dark wood casing on the wall."""
    wall.cut.wbox(wall, x0, x1, base, 2.85, -RECESS, 0.25)
    W.wbox(wall, x0, x1, base, 0.75, -0.14, 0.0)                              # bulkhead
    W.wbox(wall, x0 + 0.10, x1 - 0.10, base + 0.10, 0.65, 0.0, 0.015)          # raised panel
    W.wbox(wall, x0, x1, 0.75, 0.80, -0.14, 0.04)                              # sill rail
    W.wbox(wall, x0, x0 + 0.08, 0.80, 2.75, -0.14, 0.0)                        # stiles
    W.wbox(wall, x1 - 0.08, x1, 0.80, 2.75, -0.14, 0.0)
    W.wbox(wall, x0, x1, 2.75, 2.85, -0.14, 0.0)                               # head rail
    xm = (x0 + x1) / 2
    W.wbox(wall, xm - 0.03, xm + 0.03, 0.80, 2.75, -0.13, -0.05)               # mullion
    pane(wall, x0 + 0.08, x1 - 0.08, 0.80, 2.75, -0.10, cell)
    W.wbox(wall, x0 - 0.10, x0, base, 2.95, -0.02, 0.03)                       # casing
    W.wbox(wall, x1, x1 + 0.10, base, 2.95, -0.02, 0.03)
    W.wbox(wall, x0, x1, 2.85, 2.95, -0.02, 0.03)


def door(wall, x0, x1, z0, head, glazed_cell=None, case=W, transom_cell=None):
    """Door in a 0.25 recess: dark wood leaf (stiles and rails), glazed upper half (one glass face
    over a window back) or four raised panels; an optional transom light above the leaf; casing."""
    wall.cut.wbox(wall, x0, x1, z0, head, -RECESS, 0.25)
    d = -0.14
    leaf_top = head
    if transom_cell:
        leaf_top = head - 0.30
        W.wbox(wall, x0, x1, leaf_top, leaf_top + 0.05, d - 0.05, d + 0.03)    # transom bar
        W.wbox(wall, x0, x1, head - 0.04, head, d - 0.05, d)                    # transom head
        pane(wall, x0 + 0.04, x1 - 0.04, leaf_top + 0.05, head - 0.04, d - 0.008, transom_cell)
    g0, g1 = x0 + 0.11, x1 - 0.11
    top = leaf_top - 0.12
    W.wbox(wall, x0, g0, z0, leaf_top, d - 0.05, d)                             # stiles
    W.wbox(wall, g1, x1, z0, leaf_top, d - 0.05, d)
    W.wbox(wall, g0, g1, top, leaf_top, d - 0.05, d)                            # top rail
    if glazed_cell:
        mid = z0 + 1.15
        W.wbox(wall, g0, g1, z0, mid, d - 0.05, d)                              # lower half
        W.wbox(wall, g0 + 0.03, g1 - 0.03, z0 + 0.22, mid - 0.14, d, d + 0.015)   # raised panel
        pane(wall, g0, g1, mid, top, d - 0.008, glazed_cell)
    else:
        W.wbox(wall, g0, g1, z0, top, d - 0.05, d)
        gm = (g0 + g1) / 2
        for za, zb in ((z0 + 0.20, z0 + (leaf_top - z0) * 0.42), (z0 + (leaf_top - z0) * 0.50, top - 0.08)):
            for ua, ub in ((g0 + 0.03, gm - 0.04), (gm + 0.04, g1 - 0.03)):
                W.wbox(wall, ua, ub, za, zb, d, d + 0.015)
        W.wbox(wall, gm - 0.04, gm + 0.04, z0, top, d, d + 0.008)              # centre muntin
    case.wbox(wall, x0 - 0.10, x0, z0, head + 0.10, -0.02, 0.03)               # casing
    case.wbox(wall, x1, x1 + 0.10, z0, head + 0.10, -0.02, 0.03)
    case.wbox(wall, x0, x1, head, head + 0.10, -0.02, 0.03)


# --- A: no. 24, dwelling --------------------------------------------------------------------
door(A_FRONT, -6.60, -5.60, A_DECK, 2.45, case=T, transom_cell="transom")
DK.box(-6.60, -5.60, AFW - 0.02, AFW + 0.12, 0.12, A_DECK + 0.01)               # threshold
for i, x in enumerate((-10.10, -8.00)):
    window(A_FRONT, x, 0.85, 0.85, 1.60, pick(UPPER, "A", 0, i), muntin=True)
for i, x in enumerate((-10.10, -8.00, -6.10)):
    window(A_FRONT, x, 3.75, 0.85, 1.45, pick(UPPER, "A", 1, i), muntin=True)
for x0, z0 in ((AX0, A_DECK), (AX1 - 0.15, A_DECK)):
    T.box(x0, x0 + 0.15, AFW - 0.03, AFW, z0, A_EAVE)                            # corner boards
A_NORTH = Wall((AX0, 0.0), (-1, 0))
T.wbox(A_NORTH, -AFW - 0.15, -AFW, A_DECK, A_EAVE, -0.01, 0.03)
T.wbox(A_NORTH, -A2Y1, -A2Y1 + 0.15, -0.05, A2_EAVE - 0.15, -0.01, 0.03)


def gable_roof(mb, x0, x1, y0, y1, eave, ridge, ov_l, ov_r, th=0.07):
    """Two slabs th thick, 0.03 above the shell's roof line, overhanging ov_l / ov_r at the eaves."""
    xc = (x0 + x1) / 2
    s = (ridge - eave) / (xc - x0)
    zt = lambda x: ridge - s * abs(x - xc) + 0.03
    for xe in (x0 - ov_l, x1 + ov_r):
        mb.prism([(xe, zt(xe) - th), (xc, zt(xc) - th), (xc, zt(xc)), (xe, zt(xe))], y0, y1, axis="y")
    return zt


zt_a1 = gable_roof(SL, AX0, AX1, AFW - 0.30, AY1 + 0.10, A_EAVE, A_RIDGE, 0.25, 0.0)
zt_a2 = gable_roof(SL, AX0, A2X1, AY1, A2Y1 + 0.20, A2_EAVE, A2_RIDGE, 0.20, 0.20)
# rake boards on 24's front gable (plain, no ornament) and the boxed eave under the overhangs
for xa, xb in ((AX0 - 0.25, A_XC), (A_XC, AX1)):
    T.prism([(xa, zt_a1(xa) - 0.24), (xb, zt_a1(xb) - 0.24), (xb, zt_a1(xb) - 0.02), (xa, zt_a1(xa) - 0.02)],
            AFW - 0.33, AFW - 0.28, axis="y")
T.box(AX0 - 0.27, AX0, AFW - 0.30, AY1 + 0.10, A_EAVE - 0.34, A_EAVE - 0.18)    # A1 north eave
T.box(AX0 - 0.22, AX0, AY1, A2Y1 + 0.20, A2_EAVE - 0.30, A2_EAVE - 0.14)         # A2 eaves
T.box(A2X1, A2X1 + 0.22, AY1, A2Y1 + 0.20, A2_EAVE - 0.30, A2_EAVE - 0.14)
T.prism([(AX0 - 0.20, zt_a2(AX0 - 0.20) - 0.24), (A2_XC, zt_a2(A2_XC) - 0.24),
         (A2_XC, zt_a2(A2_XC) - 0.02), (AX0 - 0.20, zt_a2(AX0 - 0.20) - 0.02)], A2Y1 + 0.17, A2Y1 + 0.22, axis="y")
T.prism([(A2_XC, zt_a2(A2_XC) - 0.24), (A2X1 + 0.20, zt_a2(A2X1 + 0.20) - 0.24),
         (A2X1 + 0.20, zt_a2(A2X1 + 0.20) - 0.02), (A2_XC, zt_a2(A2_XC) - 0.02)], A2Y1 + 0.17, A2Y1 + 0.22, axis="y")


def shed_roof(mb, x0, x1, ya, za, yb, zb, y0, y1, th=0.05):
    """Roof slab th thick on the line through (ya, za) and (yb, zb), from y0 to y1; its top
    stands 0.03 above the shell top."""
    s = (zb - za) / (yb - ya)
    z = lambda y: za + s * (y - ya)
    mb.prism([(y0, z(y0) - 0.02), (y1, z(y1) - 0.02), (y1, z(y1) + th - 0.02), (y0, z(y0) + th - 0.02)],
             x0, x1, axis="x")


shed_roof(R, AX0 - 0.06, A2X1 + 0.06, A2Y1, LOW_TOP, A3Y1, LOW_TOP - LOW_FALL, A2Y1, A3Y1 + 0.12)   # A3

# 24's front porch (A4): deck with one riser, 4 plain square posts, fascia, shed tin roof
DK.box(AX0, AX1, 0.0, AFW, SKIRT, A_DECK)
for x in (-11.40, -9.24, -7.09, -4.93):
    T.box(x - 0.07, x + 0.07, 0.03, 0.17, A_DECK, 2.95)
T.box(AX0, AX1, 0.03, 0.21, 2.95, 3.15)                                           # fascia / beam
a4_top = lambda y: 3.20 + (3.35 - 3.20) * (y + 0.05) / (AFW + 0.05)
T.prism([(0.03, 2.95), (AFW, 2.95), (AFW, a4_top(AFW) - 0.05), (0.03, a4_top(0.03) - 0.05)],
        AX0, AX0 + 0.06, axis="x")                                                # north end fascia
T.box(AX0 + 0.06, AX1, 0.21, AFW, 3.10, 3.12)                                     # ceiling boards
R.prism([(-0.05, a4_top(-0.05) - 0.05), (AFW + 0.02, a4_top(AFW + 0.02) - 0.05),
         (AFW + 0.02, a4_top(AFW + 0.02)), (-0.05, a4_top(-0.05))], AX0 - 0.10, AX1, axis="x")

# 24's rear porch (A5): open, plain posts, wood-shingle shed roof falling south
DK.box(A2X1, A5X1, A5Y0, A2Y1, SKIRT, 0.05)
for y in (A5Y0 + 0.10, A2Y1 - 0.08):
    T.box(A5X1 - 0.14, A5X1 - 0.02, y - 0.06, y + 0.06, 0.05, 2.45)
T.box(A5X1 - 0.16, A5X1, A5Y0 + 0.02, A2Y1, 2.40, 2.55)                          # beam
SG.prism([(A2X1 - 0.02, 2.82), (A5X1 + 0.15, 2.58), (A5X1 + 0.15, 2.64), (A2X1 - 0.02, 2.88)],
         A5Y0 + 0.02, A2Y1 + 0.12, axis="y")
door(Wall((A2X1, 0.0), (1, 0), K["ShellA2"]), 15.20, 16.10, 0.05, 2.15, case=T)  # onto the rear porch
door(A3_REAR, 8.70, 9.60, -0.15, 2.05, case=T)
DK.box(-9.65, -8.65, A3Y1 - 0.02, A3Y1 + 0.30, SKIRT, -0.10)                     # step

# --- B: no. 26, Mill'y --------------------------------------------------------------------------
door(B_FRONT, -1.35, -0.45, DECK, 2.60, "door")
DK.box(-1.35, -0.45, BFW - 0.02, BFW + 0.12, 0.10, DECK + 0.01)
for i, x in enumerate((-3.60, -1.40)):
    window(B_FRONT, x, 3.90, 0.80, 1.45, pick(UPPER, "B", 1, i))
T.box(BX1 - 0.15, BX1, BFW - 0.03, BFW, DECK, 5.90)                              # south corner board
T.box(BX0, BX0 + 0.08, BFW - 0.03, BFW, 3.30, 5.90)                              # board on the 24 | 26 line
T.box(BX0, BX1 + 0.04, BFW - 0.30, BFW + 0.02, 5.90, B_TOP_F)                    # boxed eave
T.box(BX0, BX1 + 0.04, BFW - 0.32, BFW - 0.30, 5.88, B_TOP_F)                    # fascia lip
B_SOUTH = Wall((BX1, 0.0), (1, 0), K["ShellB1"])
T.wprism(B_SOUTH, [(BFW, B_TOP_F - 0.20), (BY1, B_TOP_R - 0.20), (BY1, B_TOP_R - 0.01), (BFW, B_TOP_F - 0.01)],
         -0.01, 0.04)                                                             # rake board
T.wbox(B_SOUTH, BFW, BFW + 0.15, DECK, 5.90, -0.01, 0.03)                        # corner board
shed_roof(R, BX0, BX1 + 0.06, BFW, B_TOP_F, BY1, B_TOP_R, BFW - 0.32, BY1 + 0.12)
shed_roof(R, B2A[0], B2A[1] + 0.06, B2A[2], LOW_TOP, B2A[3], LOW_TOP - 0.15, B2A[2], B2A[3] + 0.06)
shed_roof(R, B2B[0] - 0.06, B2B[1] + 0.06, B2B[2], LOW_TOP, B2B[3], LOW_TOP - LOW_FALL, B2B[2], B2B[3] + 0.12)
door(B2B_REAR, 1.20, 2.10, -0.15, 2.05, case=T)
DK.box(-2.15, -1.15, B2B[3] - 0.02, B2B[3] + 0.30, SKIRT, -0.10)

# B4: bay (bow) shop window, 5 flat facets on the map's curve (chord 2.50, 0.85 out)
BAY_X0, BAY_X1, BAY_Y = -4.09, -1.59, 0.56
_c, _s = BAY_X1 - BAY_X0, BFW - BAY_Y
BAY_R = (_c * _c / 4 + _s * _s) / (2 * _s)
BAY_CX, BAY_CY = (BAY_X0 + BAY_X1) / 2, BAY_Y + BAY_R
BAY_A = math.asin(_c / 2 / BAY_R)


def bay_pts(grow=0.0, n=5):
    """Facet corners (plan), north to south, the polygon pushed out by `grow`."""
    r = BAY_R + grow / math.cos(BAY_A / n)
    pts = []
    for i in range(n + 1):
        a = -BAY_A + 2 * BAY_A * i / n
        pts.append((BAY_CX + r * math.sin(a), BAY_CY - r * math.cos(a)))
    return pts


def bay_slab(mb, grow, z0, z1):
    pts = bay_pts(grow)
    outline = pts + [(pts[-1][0], BFW - 0.02), (pts[0][0], BFW - 0.02)]
    mb.prism(outline, z0, z1, axis="z")


bay_slab(W, 0.0, DECK, 0.75)                                                      # panelled base
bay_slab(W, 0.03, 0.75, 0.80)                                                     # sill
bay_slab(W, 0.0, 2.75, 2.95)                                                      # head
bay_slab(R, 0.06, 2.95, 3.01)                                                     # own small tin top
_bp = bay_pts()
_fw = math.dist(_bp[0], _bp[1])
for i in range(5):
    (xa, ya), (xb, yb) = _bp[i], _bp[i + 1]
    L = math.dist(_bp[i], _bp[i + 1])
    n = ((yb - ya) / L, -(xb - xa) / L)                                            # outward (to -Y)
    fw = Wall(((xa + xb) / 2, (ya + yb) / 2), n)
    # the five facets share one shop view, each showing its fifth of it
    pane(fw, -L / 2 + 0.03, L / 2 - 0.03, 0.80, 2.75, -0.02, "shop_a",
         frame=(-L / 2 - i * L, -L / 2 + (5 - i) * L, 0.80, 2.75))
    W.wbox(fw, -L / 2 + 0.06, L / 2 - 0.06, 0.24, 0.66, 0.0, 0.015)                # raised panel
for i, (x, y) in enumerate(_bp):                                                  # corner mullions
    W.box(x - 0.035, x + 0.035, y - 0.035, y + 0.035, 0.80, 2.75)

# B3: the deep open porch over the sidewalk, posts on the curb (full map depth)
DK.box(B_PORCH_X[0], B_PORCH_X[1], 0.0, BFW, SKIRT, DECK)                         # deck at the wall
for x in (-4.72, -2.51, -0.30):
    T.box(x - 0.07, x + 0.07, B_POST_Y - 0.07, B_POST_Y + 0.07, 0.0, 2.95)
T.box(B_PORCH_X[0], B_PORCH_X[1], B_PORCH_Y0 + 0.02, B_PORCH_Y0 + 0.20, 2.95, 3.15)   # front fascia
b3_top = lambda y: 3.20 + (3.35 - 3.20) * (y - B_PORCH_Y0) / (BFW - B_PORCH_Y0)
for x0, x1 in ((B_PORCH_X[0], B_PORCH_X[0] + 0.06), (B_PORCH_X[1] - 0.06, B_PORCH_X[1])):  # end fascias
    T.prism([(B_PORCH_Y0 + 0.02, 2.95), (BFW, 2.95), (BFW, b3_top(BFW) - 0.05),
             (B_PORCH_Y0 + 0.02, b3_top(B_PORCH_Y0 + 0.02) - 0.05)], x0, x1, axis="x")
T.box(B_PORCH_X[0] + 0.06, B_PORCH_X[1] - 0.06, B_PORCH_Y0 + 0.20, BFW, 3.10, 3.12)    # ceiling boards
R.prism([(B_PORCH_Y0, b3_top(B_PORCH_Y0) - 0.05), (BFW + 0.02, b3_top(BFW + 0.02) - 0.05),
         (BFW + 0.02, b3_top(BFW + 0.02)), (B_PORCH_Y0, b3_top(B_PORCH_Y0))],
        B_PORCH_X[0], B_PORCH_X[1] + 0.06, axis="x")

# --- C: nos. 28-30, Conf'y and Barber -----------------------------------------------------------
shop_window(C_FRONT, 2.95, 5.35, "shop_a")
door(C_FRONT, 5.75, 6.65, DECK, 2.60, "door")
door(C_FRONT, 7.50, 8.40, DECK, 2.60, "door")
shop_window(C_FRONT, 8.80, 11.10, "shop_b")
for x0, x1 in ((5.75, 6.65), (7.50, 8.40)):
    DK.box(x0, x1, CFW - 0.02, CFW + 0.12, 0.10, DECK + 0.01)
window(C_FRONT, 4.15, 3.95, 0.80, 1.45, pick(UPPER, "C", 1, 0))
window(C_FRONT, 9.95, 3.95, 0.80, 1.45, pick(UPPER, "C", 1, 2))
door(C_FRONT, 5.75, 6.60, 3.25, 5.35, pick(UPPER, "C", 1, 1))
door(C_FRONT, 7.55, 8.40, 3.25, 5.35, pick(UPPER, "C", 1, 3))
for x0, z0 in ((CX0, DECK), (CX1 - 0.15, DECK)):
    T.box(x0, x0 + 0.15, CFW - 0.03, CFW, z0, 6.10)                              # corner boards
T.box(CP - 0.05, CP + 0.05, CFW - 0.025, CFW, DECK, 6.10)                        # partition board
T.box(CX0 - 0.04, CX1 + 0.04, CFW - 0.30, CFW + 0.02, 6.10, C_TOP_F)              # boxed eave
T.box(CX0 - 0.04, CX1 + 0.04, CFW - 0.32, CFW - 0.30, 6.08, C_TOP_F)
for wall_x, n in ((CX0, (-1, 0)), (CX1, (1, 0))):
    wl = Wall((wall_x, 0.0), n, K["ShellC1"])
    sgn = n[0]                                                                    # u = -Y on the north wall
    T.wprism(wl, [(sgn * CFW, C_TOP_F - 0.20), (sgn * CY1, C_TOP_R - 0.20), (sgn * CY1, C_TOP_R - 0.01),
                  (sgn * CFW, C_TOP_F - 0.01)], -0.01, 0.04)                      # rake boards
    u0 = sgn * CFW
    T.wbox(wl, min(u0, u0 + sgn * 0.15), max(u0, u0 + sgn * 0.15), DECK, 6.10, -0.01, 0.03)   # corner
shed_roof(R, CX0 - 0.06, CX1 + 0.06, CFW, C_TOP_F, CY1, C_TOP_R, CFW - 0.32, CY1 + 0.12)
# C2: the open notch at 30's rear (deck, small tin roof between the 2-storey walls)
DK.box(NOTCH[0], NOTCH[1], NOTCH[2], CY1, SKIRT, 0.05)
shed_roof(R, NOTCH[0], NOTCH[1], NOTCH[2], LOW_TOP, CY1, LOW_TOP - 0.15, NOTCH[2], CY1 + 0.12)
T.box(NOTCH[0], NOTCH[1], CY1 - 0.04, CY1 + 0.10, 2.70, 2.86)                    # fascia
door(C2_BACK, -8.42, -7.52, 0.05, 2.15, case=T)
# C3: 28's rear addition
shed_roof(R, C3[0] - 0.06, C3[1] + 0.06, CY1, LOW_TOP, C3[2], LOW_TOP - LOW_FALL, CY1, C3[2] + 0.12)
door(C3_REAR, -6.20, -5.30, -0.15, 2.05, case=T)
DK.box(5.25, 6.25, C3[2] - 0.02, C3[2] + 0.30, SKIRT, -0.10)

# C4: two-tier open porch, 5 plain posts per tier, rail on the upper tier only
C_POST_X = (2.65, 4.84, 7.03, 9.22, 11.41)
C_POST_Y = 0.72
DK.box(CX0, CX1, C_PORCH_Y0, CFW, SKIRT, DECK)                                    # lower deck
for x in C_POST_X:
    T.box(x - 0.06, x + 0.06, C_POST_Y - 0.06, C_POST_Y + 0.06, DECK, 3.10)       # lower posts
    T.box(x - 0.06, x + 0.06, C_POST_Y - 0.06, C_POST_Y + 0.06, 3.25, 5.60)       # upper posts
DK.box(CX0, CX1, C_PORCH_Y0, CFW, 3.10, 3.25)                                     # upper deck
T.box(CX0, CX1, C_PORCH_Y0 - 0.03, C_PORCH_Y0 + 0.01, 3.04, 3.27)                 # deck edge board
T.box(CX0, CX1, C_PORCH_Y0 + 0.01, C_PORCH_Y0 + 0.17, 5.60, 5.75)                 # fascia
c4_top = lambda y: 5.80 + (5.97 - 5.80) * (y - (C_PORCH_Y0 - 0.10)) / (CFW - C_PORCH_Y0 + 0.10)
for x0, x1 in ((CX0, CX0 + 0.06), (CX1 - 0.06, CX1)):
    T.prism([(C_PORCH_Y0 + 0.01, 5.60), (CFW, 5.60), (CFW, c4_top(CFW) - 0.05),
             (C_PORCH_Y0 + 0.01, c4_top(C_PORCH_Y0 + 0.01) - 0.05)], x0, x1, axis="x")
T.box(CX0 + 0.06, CX1 - 0.06, C_PORCH_Y0 + 0.17, CFW, 5.70, 5.72)                 # ceiling boards
R.prism([(C_PORCH_Y0 - 0.10, c4_top(C_PORCH_Y0 - 0.10) - 0.05), (CFW + 0.02, c4_top(CFW + 0.02) - 0.05),
         (CFW + 0.02, c4_top(CFW + 0.02)), (C_PORCH_Y0 - 0.10, c4_top(C_PORCH_Y0 - 0.10))],
        CX0 - 0.08, CX1 + 0.08, axis="x")
# upper rail: top rail 4.04-4.10, bottom rail 3.37-3.42, square pickets 0.03 at 0.12 centres
RT0, RT1, RB0, RB1 = 4.04, 4.10, 3.37, 3.42


def rail_run(a0, a1, fixed, along_x):
    """One rail between two posts (centres a0, a1), along X (front) or along Y (ends)."""
    s0, s1 = a0 + 0.06, a1 - 0.06
    h = 0.03

    def bx(u0, u1, w0, w1, z0, z1):
        if along_x:
            T.box(u0, u1, w0, w1, z0, z1)
        else:
            T.box(w0, w1, u0, u1, z0, z1)
    bx(s0, s1, fixed - 0.035, fixed + 0.035, RT0, RT1)
    bx(s0, s1, fixed - 0.025, fixed + 0.025, RB0, RB1)
    n = max(1, int(round((s1 - s0) / 0.12)))
    step = (s1 - s0) / n
    for k in range(1, n):
        u = s0 + k * step
        bx(u - h / 2, u + h / 2, fixed - h / 2, fixed + h / 2, RB1, RT0)


for a, b in zip(C_POST_X, C_POST_X[1:]):
    rail_run(a, b, C_POST_Y, True)
for x in (C_POST_X[0], C_POST_X[-1]):
    rail_run(C_POST_Y, CFW + 0.06, x, False)

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
    cut_shell(shell, cutter, "HS_" + name, mat)
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("HS_" + key, MATS[BUILDER_MAT[key]], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Block 24-30 built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)",
      "| window backs", len(BACKREC))
# Materials, baked lighting and GLB export: run block_24_30_bake.py (it runs this file first).
