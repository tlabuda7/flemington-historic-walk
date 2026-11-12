"""
house_65_main.py - builds the frame dwelling "D" at 65 Main St (old no. 510), Flemington,
as it stood c. 1920 (a 2 1/2-storey front-gabled L-plan house, gone today), in Blender.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/house_65_main.py").read())

Every run deletes and rebuilds the "House65Main" collection. Materials, lightmap bake and
GLB export: house_65_main_bake.py (runs this file first). Pattern: wurts_law_office.py.

Sources: PLAN.md "Frame Dwelling "D" at 65 Main St" spec and its orchestrator decisions
(1921 Sanborn sheet 2 footprint; 1908/1909/1912 county-building cards for the cream
clapboard south wall and the receding eave). The whole front is a guess (no photo).

Coordinates (metres, Blender Z-up):
    X  across the front, +X = north, -X = south
    Y  depth: y = 0 is the front edge of the porch; the steps run out to y = -0.84; the
       front wall is at y = 2.00, the front block's rear wall at 11.72, the rear ell's rear
       wall at 18.96, the rear porch reaches y = 20.37.
    Z  up from grade (lawn level).
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".

Six materials: paint (clapboard walls and all trim), dark (shutters, doors), roof (slate),
brick, WindowBack and glass. The geometry is split into named builders so the bake can give
each its UVs: shells = clapboard, Trim = flat paint, Deck / Skirt = paint with a grey tint in
the bake's grime mask.

Windows (PLAN.md "E. Windows that don't read as flat black", rolled out here 2026-11-11, Rea /
County Hotel method): every pane is ONE outward glass face (builder Glass -> material `glass`,
transparent, see house_65_main_bake.py) 4 cm in front of ONE rectangular window back (builder
WBack) showing a cell of the shared atlas assets/textures/shared/window_backs.jpg: a dwelling,
so mostly lace, curtains and lace with a blind; attic and back rooms also blinds and a few dark
rooms; the front door's transom a dark hall. No window repeats the cell of one within 3 m of it
on the same wall. BACKREC[rid] tells the bake which atlas rectangle each back shows.
"""

import math
import json
import random
import bpy
import bmesh

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md; see the notes where the spec's numbers had to give)
# ---------------------------------------------------------------------------
HW = 4.30                 # half width of the front block (8.60 m)
FRONT = 2.00              # front wall face
MAIN_BACK = 11.72         # rear wall of the front block
ELL_X0 = 0.03             # ell south wall (the ell is flush with the north wall x = +4.30)
ELL_BACK = 18.96          # ell rear wall
ELL_CX = (ELL_X0 + HW) / 2
FOUND = 0.70              # top of the brick foundation
WT_TOP = 0.84             # top of the water-table board; clapboard above
RECESS = 0.25             # window / door openings are shallow recesses this deep

PITCH = math.radians(37.0)
TP = math.tan(PITCH)
OVER = 0.35               # eave overhang (horizontal)
RAKE = 0.25               # rake overhang at the gable ends
EDGE_X = HW + OVER        # eave edge
EDGE_Z = 6.98             # top of the roof at the eave edge (top of the fascia)
ROOF_T = 0.10 / math.cos(PITCH)      # roof slab thickness, measured vertically
SOFFIT = 6.80             # underside of the boxed cornice
FRIEZE = 6.48             # bottom of the frieze board (frieze 6.48 ... 6.80)
ELL_EDGE_S = ELL_X0 - OVER


def RT(x):
    """Top of the main roof at x (both slopes)."""
    return EDGE_Z + (EDGE_X - abs(x)) * TP


def RTE(x):
    """Top of the ell roof at x."""
    return EDGE_Z + min(x - ELL_EDGE_S, EDGE_X - x) * TP


RIDGE = RT(0.0)
ELL_RIDGE = RTE(ELL_CX)

# windows: (width, sill, head)
W1 = (0.90, 1.45, 3.25)
W2 = (0.90, 4.70, 6.35)
WA = (0.70, 7.55, 8.70)
W2_BAY = (0.90, 4.60, 6.25)          # a little lower so the bay cornice clears the heads
W1_ELL_REAR = (0.90, 1.30, 2.90)     # under the rear-porch roof
WIN_X = 2.95                          # front outer windows (spec 2.85; clears the porch pilasters' shutters)

# ---------------------------------------------------------------------------
# Materials (plain stand-ins; house_65_main_bake.py swaps in the textures)
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


COLOURS = {"Paint": "#e6dfcc", "Dark": "#27322a", "Roof": "#4c5155", "Brick": "#87452f",
           "Glass": "#1a1916", "WBack": "#2a2420"}
MATS = {k: plain("H65_" + k, c) for k, c in COLOURS.items()}
# builder -> material
BUILDER_MAT = {"Trim": "Paint", "Deck": "Paint", "Skirt": "Paint", "Dark": "Dark",
               "Roof": "Roof", "Brick": "Brick", "Glass": "Glass", "WBack": "WBack"}

# ---------------------------------------------------------------------------
# Mesh builder
# ---------------------------------------------------------------------------


class Wall:
    """A vertical wall plane: p0 (x, y) on the face, t = unit direction along it,
    n = unit outward normal. Wall coordinates: u along t, z up, d outward from the face."""

    def __init__(self, p0, t, n, cut):
        self.p0, self.t, self.n, self.cut = p0, t, n, cut

    def pt(self, u, z, d):
        return (self.p0[0] + self.t[0] * u + self.n[0] * d,
                self.p0[1] + self.t[1] * u + self.n[1] * d, z)


class MB:
    """Collects closed solids for one builder."""

    def __init__(self):
        self.bm = bmesh.new()
        self.rid_layer = self.bm.faces.layers.int.new("rid")
        self.rid = 0

    def face(self, wall, pts, d):
        """ONE single-sided face (outline [(u, z), ...] on a wall plane, d out from the wall
        face), facing outward. Used for glass panes and window backs."""
        f = self.bm.faces.new([self.bm.verts.new(wall.pt(u, z, d)) for u, z in pts])
        f.normal_update()
        if f.normal.x * wall.n[0] + f.normal.y * wall.n[1] < 0:
            f.normal_flip()
        f[self.rid_layer] = self.rid
        return f

    def _closed(self, faces):
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
        """Extrude a 2D outline [(u, v), ...] between depths d0 and d1 along an axis."""
        self._extrude([self._pt(axis, u, d0, v) for u, v in pts],
                      [self._pt(axis, u, d1, v) for u, v in pts])

    def box(self, x0, x1, y0, y1, z0, z1):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)

    def wprism(self, wall, pts, d0, d1):
        """Outline [(u, z), ...] in a wall's plane, extruded from depth d0 to d1."""
        self._extrude([wall.pt(u, z, d0) for u, z in pts], [wall.pt(u, z, d1) for u, z in pts])

    def wbox(self, wall, u0, u1, z0, z1, d0, d1):
        self.wprism(wall, rect(u0, u1, z0, z1), d0, d1)

    def plan(self, pts, z0, z1):
        """Plan outline [(x, y), ...] extruded from z0 to z1."""
        self._extrude([(x, y, z0) for x, y in pts], [(x, y, z1) for x, y in pts])

    def solid(self, verts, faces):
        bm = self.bm
        v = [bm.verts.new(c) for c in verts]
        self._closed([bm.faces.new([v[i] for i in f]) for f in faces])

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


col = fresh_collection("House65Main")
G = {k: MB() for k in BUILDER_MAT}
T, D, R, BR = G["Trim"], G["Dark"], G["Roof"], G["Brick"]
SHELL_MAIN, CUT_MAIN = MB(), MB()
SHELL_ELL, CUT_ELL = MB(), MB()
SHELL_BAY, CUT_BAY = MB(), MB()

s5 = math.hypot(1.0, 0.4)
FRONT_W = Wall((0.0, FRONT), (1, 0), (0, -1), CUT_MAIN)
SOUTH_W = Wall((-HW, 0.0), (0, 1), (-1, 0), CUT_MAIN)
NORTH_W = Wall((HW, 0.0), (0, 1), (1, 0), CUT_MAIN)
NORTH_E = Wall((HW, 0.0), (0, 1), (1, 0), CUT_ELL)
REAR_W = Wall((0.0, MAIN_BACK), (1, 0), (0, 1), CUT_MAIN)
ELL_S = Wall((ELL_X0, 0.0), (0, 1), (-1, 0), CUT_ELL)
ELL_R = Wall((0.0, ELL_BACK), (1, 0), (0, 1), CUT_ELL)
BAY_O = Wall((-HW - 1.0, 0.0), (0, 1), (-1, 0), CUT_BAY)
BAY_F = Wall((-HW - 0.5, 2.70), (-1 / s5, 0.4 / s5), (-0.4 / s5, -1 / s5), CUT_BAY)
BAY_R = Wall((-HW - 0.5, 5.30), (1 / s5, 0.4 / s5), (-0.4 / s5, 1 / s5), CUT_BAY)

# Wall planes (point, normal) for the bake's UV classification and hidden-face cuts.
WALL_PLANES = [((w.p0[0], w.p0[1]), w.n) for w in
               (FRONT_W, SOUTH_W, NORTH_W, REAR_W, ELL_S, ELL_R, BAY_O, BAY_F, BAY_R)]

# ---------------------------------------------------------------------------
# Shells (solid, cut by the openings), foundation, water table
# ---------------------------------------------------------------------------

ZW = RT(HW) - 0.06            # wall tops run inside the roof slab
SHELL_MAIN.prism([(-HW, -0.20), (HW, -0.20), (HW, ZW), (0.0, RIDGE - 0.06), (-HW, ZW)],
                 FRONT, MAIN_BACK)
SHELL_ELL.prism([(ELL_X0, -0.20), (HW, -0.20), (HW, ZW), (ELL_CX, ELL_RIDGE - 0.06), (ELL_X0, ZW)],
                MAIN_BACK - 0.12, ELL_BACK)


def bay_outline(d, xw):
    """Plan of the canted bay, every outer face moved out by d; the two ends meet the
    line x = xw (on or inside the south wall)."""
    nf = (-0.4 / s5, -1 / s5)
    nr = (-0.4 / s5, 1 / s5)
    a = (-HW + nf[0] * d, 2.50 + nf[1] * d)          # front cant, through (-4.30, 2.50)
    b = (-HW + nr[0] * d, 5.50 + nr[1] * d)          # rear cant, through (-4.30, 5.50)
    xo = -HW - 1.0 - d
    # front cant direction (-1, 0.4), rear cant direction (1, 0.4) (as y grows, x grows)
    o0 = (xw, a[1] + (xw - a[0]) * -0.4)
    o1 = (xo, a[1] + (xo - a[0]) * -0.4)
    o2 = (xo, b[1] + (xo - b[0]) * 0.4)
    o3 = (xw, b[1] + (xw - b[0]) * 0.4)
    return [o0, o1, o2, o3]


SHELL_BAY.plan(bay_outline(0.0, -HW + 0.20), -0.20, 6.45)

# brick foundation, 0.02 proud, 0.2 m hidden skirt below grade
BR.box(-HW - 0.02, HW + 0.02, FRONT - 0.02, MAIN_BACK + 0.02, -0.20, FOUND)
BR.box(ELL_X0 - 0.02, HW + 0.02, MAIN_BACK - 0.05, ELL_BACK + 0.02, -0.20, FOUND)
BR.plan(bay_outline(0.02, -HW + 0.05), -0.20, FOUND)

# water table board 0.70 ... 0.84, 0.035 proud (gaps at the doors and behind the porch)
WT_D = 0.035
for wall, a, b, holes in (
        (FRONT_W, -HW - WT_D, HW + WT_D, [(-2.0, 2.0)]),
        (SOUTH_W, FRONT - WT_D, MAIN_BACK + WT_D, [(2.45, 5.55)]),
        (NORTH_W, FRONT - WT_D, ELL_BACK + WT_D, []),
        (REAR_W, -HW - WT_D, ELL_X0 + WT_D, []),
        (ELL_S, MAIN_BACK, ELL_BACK + WT_D, [(14.2 - 0.57, 14.2 + 0.57)]),
        (ELL_R, ELL_X0 - WT_D, HW + WT_D, [(2.95 - 0.57, 2.95 + 0.57)])):
    for u0, u1 in spans(a, b, holes):
        T.wbox(wall, u0, u1, FOUND, WT_TOP, -0.01, WT_D)
T.plan(bay_outline(WT_D, -HW + 0.05), FOUND, WT_TOP)
for u0, u1 in spans(-1.98, 1.98, [(-0.60, 0.60)]):          # base board on the porch deck
    T.wbox(FRONT_W, u0, u1, 0.66, 0.80, -0.01, 0.03)

# ---------------------------------------------------------------------------
# Glass panes and window backs (PLAN.md section E)
# ---------------------------------------------------------------------------
PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
WB_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\window_backs.json"))["cells"]
GAP = 0.04                      # window back this far behind the glass
GL, WB = G["Glass"], G["WBack"]
# living rooms and bedrooms: lace, curtains, lace with a blind
HOME = {"lace": 3, "lace_blind_cream": 3, "lace_blind_green": 1, "lace_full_blind_cream": 1,
        "curtains_beige": 3, "curtains_olive": 2, "curtains_maroon_blind": 2,
        "blind_cream_half": 1, "blind_green_half": 1}
# attic and back rooms (kitchen, stair, store rooms)
BACKROOM = {"blind_cream_high": 2, "blind_cream_half": 2, "blind_green_high": 1, "lace": 1,
            "curtains_beige": 1, "dark_room": 2, "dark_room_frame": 1}
_wb_rng = random.Random(1865)
_wb_seen = {}
BACKREC = {}                    # rid -> record (read by house_65_main_bake.py)


def pick(weights, wall, u, near=3.0):
    """A cell that differs from every window already placed within `near` metres along the
    same wall (beside it, or on the floor above / below)."""
    seen = _wb_seen.setdefault((wall.p0, wall.n), [])
    avoid = {c for uu, c in seen if abs(uu - u) < near}
    names = [n for n in weights if n not in avoid] or list(weights)
    cell = _wb_rng.choices(names, weights=[weights[n] for n in names])[0]
    seen.append((u, cell))
    return cell


def pane(wall, u0, u1, z0, z1, d_glass, cell, crop=None):
    """Glass face at depth d_glass and its window back (same rectangle) GAP behind it;
    crop = (fu0, fu1, fv0, fv1) part of the atlas cell (v up)."""
    GL.face(wall, rect(u0, u1, z0, z1), d_glass)
    U0, V0, U1, V1 = WB_CELLS[cell]["uv"]
    if crop:
        U0, U1, V0, V1 = (U0 + (U1 - U0) * crop[0], U0 + (U1 - U0) * crop[1],
                          V0 + (V1 - V0) * crop[2], V0 + (V1 - V0) * crop[3])
    rid = len(BACKREC) + 1
    BACKREC[rid] = dict(wall=(wall.p0, wall.t), u0=u0, u1=u1, z0=z0, z1=z1, uv=(U0, V0, U1, V1))
    WB.rid = rid
    WB.face(wall, rect(u0, u1, z0, z1), d_glass - GAP)
    WB.rid = 0


def crop_for(w, h):
    """Part of a 0.4-aspect atlas cell that fits a w x h pane at the cell's own scale."""
    a = w / h
    if a > 0.4:                       # wider: full width, a band of the height (a little above centre)
        f = 0.4 / a
        return (0.0, 1.0, 0.55 - f / 2, 0.55 + f / 2) if f < 0.98 else None
    f = a / 0.4                       # narrower: full height, the middle of the width
    return (0.5 - f / 2, 0.5 + f / 2, 0.0, 1.0) if f < 0.98 else None


# ---------------------------------------------------------------------------
# Windows, shutters, doors
# ---------------------------------------------------------------------------


def window(wall, cu, size, shutters=True, cap=True, rooms=None):
    """2/2 double-hung window in a shallow recess: glass + window back (section E), sash (stiles, rails,
    meeting rail, one vertical muntin) set 0.08 in, flat 0.10 casing with a capped head,
    sill 0.05 proud; optional louvred shutters open flat beside it."""
    w, z0, z1 = size
    h = w / 2
    wall.cut.wbox(wall, cu - h, cu + h, z0, z1, -RECESS, 0.25)
    pane(wall, cu - h, cu + h, z0, z1, -0.11, pick(rooms or HOME, wall, cu),
         crop=crop_for(w, z1 - z0))                                         # glass + window back
    s = 0.05
    for a, b in ((cu - h, cu - h + s), (cu + h - s, cu + h)):              # stiles
        T.wbox(wall, a, b, z0, z1, -0.14, -0.08)
    zm = (z0 + z1) / 2
    for za, zb in ((z0, z0 + 0.07), (z1 - 0.05, z1), (zm - 0.02, zm + 0.02)):
        T.wbox(wall, cu - h + s, cu + h - s, za, zb, -0.14, -0.08)       # rails
    T.wbox(wall, cu - 0.015, cu + 0.015, z0 + 0.07, z1 - 0.05, -0.13, -0.09)   # muntin
    c = 0.10
    for a, b in ((cu - h - c, cu - h), (cu + h, cu + h + c)):              # casing
        T.wbox(wall, a, b, z0, z1, -0.01, 0.025)
    T.wbox(wall, cu - h - c, cu + h + c, z1, z1 + 0.10, -0.01, 0.03)        # head board
    if cap:
        T.wbox(wall, cu - h - c - 0.03, cu + h + c + 0.03, z1 + 0.10, z1 + 0.13, -0.01, 0.065)
    T.wbox(wall, cu - h - c - 0.03, cu + h + c + 0.03, z0 - 0.05, z0, -0.14, 0.05)   # sill
    if shutters:
        for sgn in (-1, 1):
            u0, u1 = sorted((cu + sgn * (h + c + 0.01), cu + sgn * (h + c + 0.01 + h)))
            D.wbox(wall, u0, u1, z0, z1, -0.005, 0.035)                    # leaf
            for k in range(4):              # louvres: 4 shallow ribs that catch the light
                zc = z0 + (z1 - z0) * (k + 0.5) / 4
                D.wbox(wall, u0 + 0.05, u1 - 0.05, zc - 0.025, zc + 0.025, 0.035, 0.05)


def door(wall, cu, w, z0, z1, transom=False):
    """4-panel dark door set 0.10 in, threshold, flat 0.12 casing with a capped head;
    optional 4-light transom above a painted transom bar, in the same casing."""
    h = w / 2
    top = z1 + 0.48 if transom else z1
    wall.cut.wbox(wall, cu - h, cu + h, z0 - 0.03, top, -RECESS, 0.25)
    D.wbox(wall, cu - h, cu + h, z0, z1, -0.14, -0.10)                     # leaf
    for ua, ub in ((cu - h + 0.10, cu - 0.04), (cu + 0.04, cu + h - 0.10)):
        for za, zb in ((z0 + 0.15, z0 + 0.95), (z0 + 1.10, z1 - 0.12)):
            D.wbox(wall, ua, ub, za, zb, -0.10, -0.085)                    # raised panels
    T.wbox(wall, cu - h - 0.05, cu + h + 0.05, z0 - 0.08, z0, -0.14, 0.04)  # threshold
    if transom:
        T.wbox(wall, cu - h, cu + h, z1, z1 + 0.08, -0.14, -0.06)          # transom bar
        pane(wall, cu - h, cu + h, z1 + 0.08, top, -0.11, "dark_room",
             crop=(0.0, 1.0, 0.70, 0.70 + 0.4 * (top - z1 - 0.08) / w))       # transom: dark hall
        for i in (1, 2, 3):
            u = cu - h + w * i / 4
            T.wbox(wall, u - 0.015, u + 0.015, z1 + 0.08, top, -0.12, -0.09)
    c = 0.12
    for a, b in ((cu - h - c, cu - h), (cu + h, cu + h + c)):
        T.wbox(wall, a, b, z0 - 0.08, top, -0.01, 0.03)
    T.wbox(wall, cu - h - c, cu + h + c, top, top + 0.10, -0.01, 0.035)
    T.wbox(wall, cu - h - c - 0.03, cu + h + c + 0.03, top + 0.10, top + 0.13, -0.01, 0.07)


# Front (east): W-D-W, three windows above, two attic windows; cellar vents
door(FRONT_W, 0.0, 0.95, 0.75, 3.00, transom=True)
for x in (-WIN_X, WIN_X):
    window(FRONT_W, x, W1)
    D.wbox(FRONT_W, x - 0.30, x + 0.30, 0.25, 0.55, -0.01, 0.035)          # cellar vent
for x in (-WIN_X, 0.0, WIN_X):
    window(FRONT_W, x, W2)
for x in (-0.90, 0.90):
    window(FRONT_W, x, WA, shutters=False, rooms=BACKROOM)

# South wall of the front block: one window per floor at y 9.0 (the bay is near the front)
for size in (W1, W2):
    window(SOUTH_W, 9.0, size)

# North wall (continuous to the rear): y 4.0 and 8.6 on the front block, 13.8 and 17.2 on the ell
for y in (4.0, 8.6, 13.8, 17.2):
    for size in (W1, W2):
        window(NORTH_W if y < MAIN_BACK else NORTH_E, y, size)

# Ell south wall: side door and window below, two windows above
door(ELL_S, 14.2, 0.90, 0.72, 2.87)
window(ELL_S, 17.2, W1, rooms=BACKROOM)
for y in (14.2, 17.2):
    window(ELL_S, y, W2)

# Rear wall of the front block (south part, clear of the ell): no shutters
for size in (W1, W2):
    window(REAR_W, -2.15, size, shutters=False, rooms=BACKROOM)
window(REAR_W, -1.00, WA, shutters=False, rooms=BACKROOM)

# Ell rear: door onto the rear porch, a window beside it, one window above
door(ELL_R, 2.95, 0.90, 0.72, 2.87)
window(ELL_R, 1.20, W1_ELL_REAR, rooms=BACKROOM)
window(ELL_R, 2.17, W2, rooms=BACKROOM)

# ---------------------------------------------------------------------------
# South bay: 2 storeys, canted, own cornice and hipped roof; no shutters
# ---------------------------------------------------------------------------

for wall, w in ((BAY_O, 0.90), (BAY_F, 0.50), (BAY_R, 0.50)):
    cu = 4.0 if wall is BAY_O else 0.0
    window(wall, cu, (w, W1[1], W1[2]), shutters=False)
    window(wall, cu, (w, W2_BAY[1], W2_BAY[2]), shutters=False)
    T.wbox(wall, cu - w / 2, cu + w / 2, 0.98, W1[1] - 0.12, -0.01, 0.02)    # panel under the sill
# corner boards on the bay's two outer corners
for x, y in bay_outline(0.0, -HW)[1:3]:
    T.box(x - 0.035, x + 0.07, y - 0.06, y + 0.06, WT_TOP, 6.38)
T.plan(bay_outline(0.10, -HW + 0.05), 6.38, 6.56)                           # cornice
o0, o1, o2, o3 = bay_outline(0.16, -HW)
ZB0, ZB1 = 6.56, 6.84
t1, t2 = (-HW, o1[1], ZB1), (-HW, o2[1], ZB1)
R.solid([(*o0, ZB0), (*o1, ZB0), (*o2, ZB0), (*o3, ZB0), t1, t2],
        [(0, 1, 2, 3), (0, 1, 4), (1, 2, 5, 4), (2, 3, 5), (3, 0, 4, 5)])

# ---------------------------------------------------------------------------
# Trim: corner boards, frieze, boxed cornices, front returns, rakes
# ---------------------------------------------------------------------------


def corner(x, y, ox, oy, z1):
    T.box(*sorted((x - ox * 0.15, x + ox * 0.03)), *sorted((y - oy * 0.15, y + oy * 0.03)), WT_TOP, z1)


corner(-HW, FRONT, -1, -1, SOFFIT)
corner(HW, FRONT, 1, -1, SOFFIT)
corner(-HW, MAIN_BACK, -1, 1, FRIEZE)
corner(HW, ELL_BACK, 1, 1, FRIEZE)
corner(ELL_X0, ELL_BACK, -1, 1, FRIEZE)

# frieze boards under the eaves
for wall, a, b in ((SOUTH_W, FRONT, MAIN_BACK), (NORTH_W, FRONT, ELL_BACK), (ELL_S, MAIN_BACK, ELL_BACK)):
    T.wbox(wall, a - 0.03, b + 0.03, FRIEZE, SOFFIT, -0.01, 0.025)
    # boxed cornice: soffit board and fascia (the fascia covers the roof slab's edge)
    a2 = a - RAKE if wall is not ELL_S else a
    b2 = b + RAKE
    T.wbox(wall, a2, b2, SOFFIT, SOFFIT + 0.06, -0.01, OVER + 0.02)
    T.wbox(wall, a2, b2, SOFFIT - 0.02, EDGE_Z + 0.015, OVER - 0.02, OVER + 0.03)

# front cornice returns (Greek-Revival type), 0.60 along the front, with a little slate cap
for sgn in (-1, 1):
    x0, x1 = sorted((sgn * (HW - 0.60), sgn * (EDGE_X + 0.03)))
    T.box(x0, x1, FRONT - OVER - 0.03, FRONT + 0.02, SOFFIT - 0.02, EDGE_Z + 0.015)
    R.prism([(FRONT - OVER - 0.06, EDGE_Z + 0.015), (FRONT + 0.02, EDGE_Z + 0.015),
             (FRONT + 0.02, EDGE_Z + 0.30)], x0 - 0.02, x1 + 0.02, axis="x")


def rake(xa, xb, y0, y1, top, drop=0.22):
    """Raking fascia under a gable roof's edge between xa and xb (top(x) = roof top)."""
    T.prism([(xa, top(xa) - drop), (xb, top(xb) - drop), (xb, top(xb) + 0.015), (xa, top(xa) + 0.015)],
            y0, y1)


for sgn in (-1, 1):
    rake(sgn * (EDGE_X + 0.03), 0.0, FRONT - RAKE - 0.03, FRONT + 0.02, RT)            # front fascia
    rake(sgn * (EDGE_X + 0.03), 0.0, FRONT - RAKE - 0.06, FRONT - RAKE - 0.02,
         lambda x: RT(x) + 0.015, drop=0.07)                                           # small crown
rake(-EDGE_X - 0.03, 0.0, MAIN_BACK - 0.02, MAIN_BACK + RAKE + 0.03, RT)              # rear, south half
rake(0.0, 1.95, MAIN_BACK - 0.02, MAIN_BACK + RAKE + 0.03, RT)                       # rear, above the ell
rake(ELL_EDGE_S - 0.03, ELL_CX, ELL_BACK - 0.02, ELL_BACK + RAKE + 0.03, RTE)        # ell rear
rake(ELL_CX, EDGE_X + 0.03, ELL_BACK - 0.02, ELL_BACK + RAKE + 0.03, RTE)

# ---------------------------------------------------------------------------
# Roofs (slate): main gable, ell gable, ridge caps
# ---------------------------------------------------------------------------


def slope(xa, xb, top, y0, y1):
    R.prism([(xa, top(xa)), (xb, top(xb)), (xb, top(xb) - ROOF_T), (xa, top(xa) - ROOF_T)], y0, y1)


Y_FRONT_EDGE = FRONT - RAKE
Y_MAIN_EDGE = MAIN_BACK + RAKE
Y_ELL_EDGE = ELL_BACK + RAKE
slope(-EDGE_X, 0.0, RT, Y_FRONT_EDGE, Y_MAIN_EDGE)
slope(0.0, EDGE_X, RT, Y_FRONT_EDGE, Y_MAIN_EDGE)
slope(ELL_CX, EDGE_X, RTE, Y_MAIN_EDGE, Y_ELL_EDGE)          # coplanar with the main north slope
slope(ELL_EDGE_S, ELL_CX, RTE, MAIN_BACK - 0.02, Y_ELL_EDGE)
R.box(-0.07, 0.07, Y_FRONT_EDGE, Y_MAIN_EDGE, RIDGE - 0.06, RIDGE + 0.05)
R.box(ELL_CX - 0.07, ELL_CX + 0.07, Y_MAIN_EDGE, Y_ELL_EDGE, ELL_RIDGE - 0.06, ELL_RIDGE + 0.05)

# ---------------------------------------------------------------------------
# Chimneys (brick, guess): A on the main ridge toward the rear, B on the ell ridge
# ---------------------------------------------------------------------------

for cx, cy, hx, hy, z0, ztop in ((0.0, 9.0, 0.275, 0.40, 9.6, 11.43),
                                 (ELL_CX, 17.8, 0.25, 0.325, 8.0, 9.75)):
    BR.box(cx - hx, cx + hx, cy - hy, cy + hy, z0, ztop - 0.28)
    BR.box(cx - hx - 0.05, cx + hx + 0.05, cy - hy - 0.05, cy + hy + 0.05, ztop - 0.28, ztop - 0.18)
    BR.box(cx - hx, cx + hx, cy - hy, cy + hy, ztop - 0.18, ztop)

# ---------------------------------------------------------------------------
# Front porch: deck, skirt, steps, posts, railing, frieze, low hipped roof
# ---------------------------------------------------------------------------

DECK = 0.68
DK, SK = G["Deck"], G["Skirt"]
SK.box(-1.98, 1.98, 0.02, FRONT, -0.05, DECK - 0.04)                         # skirt boards
DK.box(-2.02, 2.02, -0.02, FRONT, DECK - 0.04, DECK)                          # deck + nosing
for k, (y0, ztop) in enumerate(((-0.84, 0.17), (-0.56, 0.34), (-0.28, 0.51))):
    DK.box(-0.625, 0.625, y0, 0.0, -0.05, ztop)                               # 3 steps
for sgn in (-1, 1):                                                           # closed stringers
    x0, x1 = sorted((sgn * 0.625, sgn * 0.665))
    T.prism([(-0.86, -0.05), (0.0, -0.05), (0.0, DECK + 0.01), (-0.86, 0.22)], x0, x1, axis="x")

OCT = [(0.075, -0.045), (0.075, 0.045), (0.045, 0.075), (-0.045, 0.075),
       (-0.075, 0.045), (-0.075, -0.045), (-0.045, -0.075), (0.045, -0.075)]
POST_Y = 0.15
POST_X = (-1.90, -0.70, 0.70, 1.90)
for px in POST_X:
    T.box(px - 0.095, px + 0.095, POST_Y - 0.095, POST_Y + 0.095, DECK, 0.88)       # base block
    T.box(px - 0.075, px + 0.075, POST_Y - 0.075, POST_Y + 0.075, 0.88, 1.05)
    T.plan([(px + x, POST_Y + y) for x, y in OCT], 1.05, 2.70)                       # chamfered shaft
    T.box(px - 0.075, px + 0.075, POST_Y - 0.075, POST_Y + 0.075, 2.70, 2.88)
    T.box(px - 0.095, px + 0.095, POST_Y - 0.095, POST_Y + 0.095, 2.88, 3.05)       # cap block
for sgn in (-1, 1):                                                                  # half pilasters
    T.box(sgn * 1.86 - 0.08, sgn * 1.86 + 0.08, FRONT - 0.04, FRONT + 0.01, DECK, 3.05)


def railing(axis, a, b, c):
    """Top rail 0.06 x 0.10 at deck + 0.80, bottom rail at deck + 0.08, square 0.04
    balusters at 0.12 centres, running from a to b along `axis` ('x' or 'y') at c."""
    def bx(u0, u1, w, z0, z1):
        if axis == "x":
            T.box(u0, u1, c - w, c + w, z0, z1)
        else:
            T.box(c - w, c + w, u0, u1, z0, z1)
    bx(a, b, 0.05, DECK + 0.74, DECK + 0.80)
    bx(a, b, 0.03, DECK + 0.08, DECK + 0.12)
    n = int((b - a) / 0.12)
    for i in range(n):
        u = a + (b - a) * (i + 0.5) / n
        bx(u - 0.02, u + 0.02, 0.02, DECK + 0.12, DECK + 0.74)


for sgn in (-1, 1):
    railing("x", *sorted((sgn * 0.775, sgn * 1.825)), POST_Y)
    railing("y", POST_Y + 0.075, FRONT - 0.04, sgn * 1.90)

# frieze on the three open sides
T.box(-2.0, 2.0, 0.05, 0.25, 3.05, 3.24)
for sgn in (-1, 1):
    T.box(*sorted((sgn * 1.81, sgn * 2.0)), 0.25, FRONT, 3.05, 3.24)

# low hipped roof (3.35 at the eave -> 3.85 against the wall): slate on top, painted
# ceiling and fascia below (two thin solids of the same hip shape)
PE0, PE1, PEY = 3.35, 3.85, -0.10
PX = 2.15


def hip(dz):
    return [(-PX, PEY, PE0 + dz), (PX, PEY, PE0 + dz), (0.05, FRONT + 0.02, PE1 + dz),
            (-0.05, FRONT + 0.02, PE1 + dz), (-PX, FRONT + 0.02, PE0 + dz), (PX, FRONT + 0.02, PE0 + dz)]


HIP_TOP = [(0, 1, 2, 3), (1, 5, 2), (0, 3, 4)]
HIP_RING = [0, 1, 5, 2, 3, 4]


def hip_solid(mb, dz_top, dz_bot):
    verts = hip(dz_top) + hip(dz_bot)
    faces = [f for f in HIP_TOP] + [tuple(i + 6 for i in reversed(f)) for f in HIP_TOP]
    for i in range(6):
        a, b = HIP_RING[i], HIP_RING[(i + 1) % 6]
        faces.append((a, b, b + 6, a + 6))
    mb.solid(verts, faces)


hip_solid(R, 0.0, -0.06)
hip_solid(T, -0.06, -0.12)

# ---------------------------------------------------------------------------
# Rear porch (deck, step, 3 posts, beam, shed roof) and the ell's side stoop
# ---------------------------------------------------------------------------

RP_Y1 = 20.37
DK.box(0.23, HW, ELL_BACK - 0.02, RP_Y1, -0.05, 0.50)
DK.box(1.70, 2.70, RP_Y1 - 0.02, RP_Y1 + 0.28, -0.05, 0.25)
for px in (0.33, 2.27, 4.20):
    T.box(px - 0.06, px + 0.06, 20.19, 20.31, 0.50, 2.86)
T.box(0.23, HW, 20.18, 20.32, 2.72, 2.86)
RS = (3.30 - 2.90) / (RP_Y1 - ELL_BACK)


def rp_top(y):
    return 3.30 - RS * (y - ELL_BACK)


R.prism([(ELL_BACK - 0.06, rp_top(ELL_BACK - 0.06)), (20.50, rp_top(20.50)),
         (20.50, rp_top(20.50) - 0.08), (ELL_BACK - 0.06, rp_top(ELL_BACK - 0.06) - 0.08)],
        0.13, HW + 0.12, axis="x")
DK.box(-0.77, ELL_X0, 13.70, 14.70, -0.05, 0.50)                             # side stoop
DK.box(-1.05, -0.77, 13.80, 14.60, -0.05, 0.25)

# ---------------------------------------------------------------------------
# Build objects (boolean the cut shells)
# ---------------------------------------------------------------------------


def cut_shell(shell, cutter, name):
    walls = shell.to_object(name, MATS["Paint"], col)
    cutters = cutter.to_object(name + "_Cutters", MATS["Paint"], col)
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


cut_shell(SHELL_MAIN, CUT_MAIN, "H65_ShellMain")
cut_shell(SHELL_ELL, CUT_ELL, "H65_ShellEll")
cut_shell(SHELL_BAY, CUT_BAY, "H65_ShellBay")
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("H65_" + key, MATS[BUILDER_MAT[key]], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("House 65 Main built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)",
      "| ridge %.2f, ell ridge %.2f" % (RIDGE, ELL_RIDGE))
# Materials, baked lighting and GLB export: run house_65_main_bake.py (it runs this file first).
