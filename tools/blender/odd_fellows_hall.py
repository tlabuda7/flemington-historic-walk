"""
odd_fellows_hall.py - builds the Odd Fellows Hall / Hopewell Building, 82-84 Main St, Flemington
(east side, old nos. 537-538), as on the 1921 Sanborn map and the 1907-1910s cards
("Some Business Blocks"):
  A  3-storey frame front block (Y 0 ... 10.65): pale smooth front with 7 + 7 two-over-two
     windows under flat hoods, belt course, bracketed cornice (top 10.67), the big arched
     crest with a half-round louvred vent, two dark shop fronts with a stair door between,
     two BLANK pale signboards (owner, 2026-11-10: no lettering), two scalloped awnings;
     clapboard side walls, one column of windows near the front of the north wall
  B  3-storey brick rear (Y 10.65 ... 21.26), plain, with a low parapet
  Low tin hip roof over both, roof box on the ridge.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/odd_fellows_hall.py").read())

Every run deletes and rebuilds the "OddFellowsHall" collection. Materials, lightmap bake and
GLB export: odd_fellows_hall_bake.py (runs this file first). Pattern: palace_theatre.py /
union_hotel.py (builders per material, closed wall shells with shallow boolean recesses).

Windows (PLAN.md section E, 2026-11-12): every pane is ONE outward glass face (builder Glass ->
material `glass`, transparent in the scene) with a window back 4 cm behind it: upper floors and
side / rear windows a cell of assets/textures/shared/window_backs.jpg (lodge hall: blinds well
down; offices: blinds at varied heights and dim rooms; never the same cell beside or above /
below itself), the four display windows and the door lights the shared shop interior
(shared/shop_interior.jpg). Sashes, muntins, casings, hoods and sills are unchanged; the shop-door
leaves are now open frames round their lights; the crest vent keeps its plain dark back.

Sources: PLAN.md "Odd Fellows Hall / Hopewell Building (82-84 Main St, old nos. 537-538)"
(1921 Sanborn sheet 3 footprint; elevations from a perspective fit of the 1910s card, +-0.3 m).

Coordinates (metres, Blender Z-up), origin = scene (10.30, 0.15, 9.09), rotation 0 -90 0:
    X  along the street, +X = south (no. 90-94), -X = north (alley, Nevius store)
    Y  depth: y = 0 is the front wall; rear wall at 21.26
    Z  up from the sidewalk top; walls skirt down to -0.20; alleys at -0.15
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".
"""

import json
import math
import random
import bpy
import bmesh

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md massing table and elevation notes)
# ---------------------------------------------------------------------------
HW = 7.765                      # half width (15.53)
AY1 = 10.65                     # frame part A / brick part B
BY1 = 21.26                     # rear wall
EAVE = 10.00                    # wall tops, roof eaves
CORN_TOP = 10.67                # cornice top (map 35')
RIDGE, RIDGE_Y0, RIDGE_Y1 = 11.30, 4.0, 18.0
SLAB = 0.30                     # front wall thickness
SKIRT = -0.20
ALLEY = -0.15
SHOP_HEAD = 2.75                # top of the shop-front openings (fascia 2.75 ... 3.55)
WIN_X = (-5.85, -3.75, -1.85, 0.0, 1.85, 3.75, 5.85)
WIN_W = 0.86                    # sash opening; surround 1.10
W3 = (7.60, 9.25)               # 3rd floor opening
W2 = (4.05, 5.45)               # 2nd floor opening
BELT = (6.58, 6.78)
FRIEZE0, SOFFIT = 9.50, 9.77
BRACKET_X = (-6.85, -4.80, -2.80, -0.95, 0.95, 2.80, 4.80, 6.85)
ARCH_A, ARCH_APEX, ARCH_Y = 4.40, 12.90, 0.35
NORTH_WIN_Y = 1.80

# shop front, X from north (PLAN.md table)
PIER_N = (-HW, -7.32)
WIN_N1 = (-7.32, -5.21)
DOOR_N = (-5.21, -3.49)
WIN_N2 = (-3.49, -1.41)
POST = (-1.41, -1.25)
STAIR = (-1.25, 0.17)
WPOST = (0.17, 0.88)
WIN_S1 = (0.88, 3.14)
DOOR_S = (3.14, 5.09)
WIN_S2 = (5.09, 7.37)
PIER_S = (7.37, HW)
VEST = 0.60                     # door recess depth
AWNINGS = ((-6.80, 0.15), (0.65, 7.40))
SIGNS = ((-5.60, -1.90), (2.30, 6.90))

# ---------------------------------------------------------------------------
# Materials (plain stand-ins; odd_fellows_hall_bake.py swaps in the textures)
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


COLOURS = {"Front": "#CFC2A4", "Trim": "#DDD5C2", "Clapboard": "#8A8072", "Brick": "#7A4436",
           "Roof": "#5A3D34", "Shopfront": "#2A2E28", "Dark": "#1E2226", "Awning": "#D8CDB4",
           "WBack": "#3A3632", "Shop": "#3A3632", "Glass": "#1A1916"}
MATS = {k: plain("OF_" + k, c) for k, c in COLOURS.items()}
# builder -> material (the bake gives every builder its own UVs and tint)
BUILDER_MAT = {"FrontAdd": "Front", "Trim": "Trim", "Sash": "Trim", "Bracket": "Trim", "Shutter": "Trim",
               "Sill": "Trim", "Clap": "Clapboard", "BrickAdd": "Brick", "Roof": "Roof", "Shop": "Shopfront",
               "Glass": "Glass", "Vent": "Dark", "Iron": "Dark", "Awning": "Awning",
               "WBack": "WBack", "ShopInt": "Shop"}

# ---------------------------------------------------------------------------
# Mesh builder (as palace_theatre.py)
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
    """Collects closed solids for one builder. Faces get the current `rid` (window-back record)."""

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
        """Extrude a 2D outline between depths d0 and d1 along an axis ('y': outline in X-Z;
        'x': outline in Y-Z; 'z': plan outline in X-Y)."""
        self._extrude([self._pt(axis, u, d0, v) for u, v in pts],
                      [self._pt(axis, u, d1, v) for u, v in pts])

    def box(self, x0, x1, y0, y1, z0, z1):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)

    def wprism(self, wall, pts, d0, d1):
        self._extrude([wall.pt(u, z, d0) for u, z in pts], [wall.pt(u, z, d1) for u, z in pts])

    def wbox(self, wall, u0, u1, z0, z1, d0, d1):
        self.wprism(wall, rect(u0, u1, z0, z1), d0, d1)

    def band(self, outer, inner, d0, d1, axis="y"):
        """Closed strip between two open polylines of equal length (outline in the axis
        plane), extruded between depths d0 and d1: arches and curved mouldings without
        concave n-gons."""
        bm = self.bm
        P = lambda p, d: bm.verts.new(self._pt(axis, p[0], d, p[1]))
        o0, o1 = [P(p, d0) for p in outer], [P(p, d1) for p in outer]
        i0, i1 = [P(p, d0) for p in inner], [P(p, d1) for p in inner]
        faces = []
        for k in range(len(outer) - 1):
            faces.append(bm.faces.new([o0[k], o0[k + 1], i0[k + 1], i0[k]]))
            faces.append(bm.faces.new([o1[k], i1[k], i1[k + 1], o1[k + 1]]))
            faces.append(bm.faces.new([o0[k], o1[k], o1[k + 1], o0[k + 1]]))
            faces.append(bm.faces.new([i0[k], i0[k + 1], i1[k + 1], i1[k]]))
        for k in (0, len(outer) - 1):
            faces.append(bm.faces.new([o0[k], i0[k], i1[k], o1[k]]))
        self._closed(faces)

    def tube(self, p0, p1, r, sides=6):
        from mathutils import Vector
        a, b = Vector(p0), Vector(p1)
        ax = (b - a).normalized()
        ref = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
        e1 = ax.cross(ref).normalized()
        e2 = ax.cross(e1)
        ring = [e1 * math.cos(2 * math.pi * (i + 0.5) / sides) * r + e2 * math.sin(2 * math.pi * (i + 0.5) / sides) * r
                for i in range(sides)]
        self._extrude([tuple(a + v) for v in ring], [tuple(b + v) for v in ring])

    def solid(self, cos, faces_idx):
        vs = [self.bm.verts.new(c) for c in cos]
        self._closed([self.bm.faces.new([vs[i] for i in f]) for f in faces_idx])

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


def ellipse(a, b, zc, off, segs, t0=0.0, t1=math.pi):
    """Half-ellipse (centre (0, zc), semi-axes a, b) offset inward by `off` along its normal,
    from angle t0 (right, +X) to t1 (left)."""
    pts = []
    for i in range(segs + 1):
        t = t0 + (t1 - t0) * i / segs
        x, z = a * math.cos(t), b * math.sin(t)
        nx, nz = b * math.cos(t), a * math.sin(t)
        L = math.hypot(nx, nz)
        pts.append((x - off * nx / L, zc + z - off * nz / L))
    return pts


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


col = fresh_collection("OddFellowsHall")
G = {k: MB() for k in BUILDER_MAT}
FA, T, SA, BK, SH, SL, CL, BA, R, SP, GL, IR, AW, VT, WB, SI = (
    G[k] for k in ("FrontAdd", "Trim", "Sash", "Bracket", "Shutter", "Sill", "Clap", "BrickAdd", "Roof",
                   "Shop", "Glass", "Iron", "Awning", "Vent", "WBack", "ShopInt"))
# wall shells (closed solids) and their cutters: name -> (shell, cutter, material)
SHELLS = {k: (MB(), MB(), m) for k, m in (("ShellF", "Front"), ("ShellA", "Clapboard"), ("ShellB", "Brick"))}
SF_, SA_, SB_ = (SHELLS[k][0] for k in SHELLS)
KF, KA, KB = (SHELLS[k][1] for k in SHELLS)


class Both:
    """Front cutters go through the front slab and the clapboard block behind it."""

    def wbox(self, *a):
        KF.wbox(*a)
        KA.wbox(*a)

    def box(self, *a):
        KF.box(*a)
        KA.box(*a)


KFA = Both()
FRONT = Wall((0.0, 0.0), (0, -1), KFA)          # u = X (south to the right), d = -Y
NORTH = Wall((-HW, 0.0), (-1, 0), KA)           # u = -Y
NORTH_B = Wall((-HW, 0.0), (-1, 0), KB)
SOUTH_B = Wall((HW, 0.0), (1, 0), KB)           # u = +Y

# ---------------------------------------------------------------------------
# Glass panes and window backs (PLAN.md section E)
# ---------------------------------------------------------------------------
PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
CELLS = {}                      # cell name -> (builder, uv); shop_interior first (window_backs
for _f, _mb in (("shop_interior", "ShopInt"), ("window_backs", "WBack")):   # has old shop_a/_b)
    for _k, _v in json.load(open(PROJECT + r"\assets\textures\shared\%s.json" % _f))["cells"].items():
        CELLS.setdefault(_k, (_mb, _v["uv"]))
GAP = 0.04                      # window back this far behind the glass
# 3rd floor: the lodge hall - blinds drawn well down, a dim room or two
LODGE = {"blind_cream_low": 3, "blind_green_low": 3, "blind_cream_full": 2, "blind_cream_half": 1,
         "blind_green_half": 1, "dark_room": 1, "dark_room_frame": 1}
# 2nd floor and side windows: offices - blinds at varied heights, dim rooms
OFFICE = {"blind_cream_high": 3, "blind_cream_half": 3, "blind_cream_low": 1, "blind_green_high": 2,
          "blind_green_half": 2, "dark_room": 2, "dark_room_frame": 2}
# brick rear (back rooms, stair): more dim rooms
BACKSIDE = {"blind_cream_high": 2, "blind_cream_half": 2, "blind_green_half": 1, "dark_room": 3,
            "dark_room_frame": 3}
_wb_rng = random.Random(1882)
_wb_grid = {}
BACKREC = {}                    # rid -> record (read by odd_fellows_hall_bake.py)


def pick(weights, wall, row, colm):
    """A cell for the window at (row, column) of a wall that differs from its neighbours."""
    g = _wb_grid.setdefault(id(wall), {})
    avoid = {g.get((row, colm - 1)), g.get((row, colm + 1)), g.get((row - 1, colm)), g.get((row + 1, colm))}
    names = [n for n in weights if n not in avoid]
    cell = _wb_rng.choices(names, weights=[weights[n] for n in names])[0]
    g[(row, colm)] = cell
    return cell


def pane(wall, u0, u1, z0, z1, d_glass, cell, grow=0.0, crop=None, mirror=False, gap=GAP):
    """Glass face (u0..u1 x z0..z1) at depth d_glass (negative = into the wall) and its window
    back `gap` behind it, `grow` larger all round where frames hide its edge; crop = (fu0, fu1,
    fv0, fv1) part of the atlas cell (v up); mirror = the cell flipped left to right."""
    GL.face(wall, rect(u0, u1, z0, z1), d_glass)
    mb_key, (U0, V0, U1, V1) = CELLS[cell]
    if crop:
        U0, U1, V0, V1 = (U0 + (U1 - U0) * crop[0], U0 + (U1 - U0) * crop[1],
                          V0 + (V1 - V0) * crop[2], V0 + (V1 - V0) * crop[3])
    if mirror:
        U0, U1 = U1, U0
    b = (u0 - grow, u1 + grow, z0 - grow, z1 + grow)
    rid = len(BACKREC) + 1
    BACKREC[rid] = dict(wall=(wall.p0, wall.n), u0=b[0], u1=b[1], z0=b[2], z1=b[3], uv=(U0, V0, U1, V1))
    mb = G[mb_key]
    mb.rid = rid
    mb.face(wall, rect(*b), d_glass - gap)
    mb.rid = 0

# ---------------------------------------------------------------------------
# Shells: front slab (pale, smooth), frame block A (clapboard), brick block B.
# The slab is 1 cm narrower than A and A starts 2 cm behind the front, so no faces are
# coplanar; the 1 cm strip is under the corner boards.
# ---------------------------------------------------------------------------
SF_.box(-HW + 0.01, HW - 0.01, 0.0, SLAB, SKIRT, EAVE)
SA_.box(-HW, HW, 0.02, AY1, SKIRT, EAVE)
SB_.box(-HW, HW, AY1, BY1, SKIRT, EAVE)

# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------


def sash_window(wall, cu, w, z0, z1, cell, grid=(2, 1), casing=0.12, hood=False, sill_w=None, cutter=None):
    """Recessed double-hung window: one glass face 0.09 back with a window back (atlas `cell`)
    4 cm behind it, two sashes (grid = panes across, panes down per sash), casings, flat hood
    or plain head casing, sill."""
    hw = w / 2
    (cutter or wall.cut).wbox(wall, cu - hw, cu + hw, z0, z1, -0.20, 0.25)
    pane(wall, cu - hw, cu + hw, z0, z1, -0.09, cell)
    zm = (z0 + z1) / 2
    SA.wbox(wall, cu - hw, cu - hw + 0.05, z0, z1, -0.08, -0.04)          # stiles
    SA.wbox(wall, cu + hw - 0.05, cu + hw, z0, z1, -0.08, -0.04)
    SA.wbox(wall, cu - hw, cu + hw, z1 - 0.06, z1, -0.08, -0.04)          # top rail
    SA.wbox(wall, cu - hw, cu + hw, z0, z0 + 0.08, -0.08, -0.04)          # bottom rail
    SA.wbox(wall, cu - hw, cu + hw, zm - 0.03, zm + 0.03, -0.08, -0.03)   # meeting rails
    cols, rows = grid
    for k in range(1, cols):
        uu = cu - hw + 0.05 + k * (w - 0.10) / cols
        SA.wbox(wall, uu - 0.0125, uu + 0.0125, z0 + 0.08, z1 - 0.06, -0.08, -0.05)
    for za, zb in ((z0 + 0.08, zm - 0.03), (zm + 0.03, z1 - 0.06)):
        for k in range(1, rows):
            zz = za + k * (zb - za) / rows
            SA.wbox(wall, cu - hw + 0.05, cu + hw - 0.05, zz - 0.0125, zz + 0.0125, -0.08, -0.05)
    # casings
    T.wbox(wall, cu - hw - casing, cu - hw, z0, z1, 0.0, 0.03)
    T.wbox(wall, cu + hw, cu + hw + casing, z0, z1, 0.0, 0.03)
    if hood:
        T.wbox(wall, cu - 0.65, cu + 0.65, z1, z1 + 0.16, 0.0, 0.10)       # flat hood 1.30 wide
        T.wbox(wall, cu - 0.68, cu + 0.68, z1 + 0.16, z1 + 0.20, 0.0, 0.13)
    else:
        T.wbox(wall, cu - hw - casing, cu + hw + casing, z1, z1 + casing, 0.0, 0.03)
    sw = (sill_w or (w + 2 * casing + 0.10)) / 2
    SL.wbox(wall, cu - sw, cu + sw, z0 - 0.08, z0, -0.02, 0.05)          # sill, 0.05 proud


def plain_window(wall, cu, z0, z1, cell, w=0.85):
    """Plain window in the brick rear: 0.15 reveal, glass with a window back behind it,
    meeting rail, stone sill."""
    hw = w / 2
    wall.cut.wbox(wall, cu - hw, cu + hw, z0, z1, -0.20, 0.25)
    pane(wall, cu - hw, cu + hw, z0, z1, -0.14, cell)
    SA.wbox(wall, cu - hw, cu + hw, (z0 + z1) / 2 - 0.03, (z0 + z1) / 2 + 0.03, -0.13, -0.09)
    SL.wbox(wall, cu - hw - 0.06, cu + hw + 0.06, z0 - 0.08, z0, -0.02, 0.05)


# front: 7 + 7 two-over-two windows with flat hoods (sill 1.20, hood 1.30, surround 1.10)
for i, x in enumerate(WIN_X):
    sash_window(FRONT, x, WIN_W, *W3, pick(LODGE, FRONT, 3, i), grid=(2, 1), hood=True, sill_w=1.20)
    sash_window(FRONT, x, WIN_W, *W2, pick(OFFICE, FRONT, 2, i), grid=(2, 1), hood=True, sill_w=1.20)

# north wall of A: one column near the front (surround 1.05; Z = surround extents).
# The card shows small panes in the 2nd-floor and ground windows (read as 6/6) and a dark
# 3rd-floor window (2/2).
NW = 0.81
sash_window(NORTH, -NORTH_WIN_Y, NW, 7.80, 9.33, pick(LODGE, NORTH, 3, 0), grid=(2, 1))
sash_window(NORTH, -NORTH_WIN_Y, NW, 4.25, 5.38, pick(OFFICE, NORTH, 2, 0), grid=(3, 2))
sash_window(NORTH, -NORTH_WIN_Y, NW, 0.85, 2.28, pick(OFFICE, NORTH, 1, 0), grid=(3, 2))
# two open plain shutters, flat against the wall beside the ground window
for s in (-1, 1):
    u0 = -NORTH_WIN_Y + s * (NW / 2 + 0.12 + 0.01)
    u1 = u0 + s * 0.45
    a, b = sorted((u0, u1))
    SH.wbox(NORTH, a, b, 0.85, 2.40, 0.0, 0.035)
    for za, zb in ((0.95, 1.55), (1.70, 2.30)):                       # two flat panels
        SH.wbox(NORTH, a + 0.06, b - 0.06, za, zb, 0.035, 0.045)

# brick rear: map "///" ticks = one column of three plain windows
for wall, ys in ((NORTH_B, (-16.8,)), (SOUTH_B, (11.8, 16.8))):
    for c, u in enumerate(ys):
        for row, (z0, z1) in enumerate(((0.85, 2.40), W2, W3)):
            plain_window(wall, u, z0, z1, pick(BACKSIDE, wall, row, c))

# ---------------------------------------------------------------------------
# Front: belt course, corner boards, cornice, brackets
# ---------------------------------------------------------------------------
T.box(-HW, HW, -0.08, 0.0, BELT[0], BELT[1] - 0.04)
T.box(-HW - 0.02, HW + 0.02, -0.10, 0.0, BELT[1] - 0.04, BELT[1])
for s in (-1, 1):
    a, b = sorted((s * (HW + 0.03), s * (HW - 0.18)))
    T.box(a, b, -0.03, 0.0, 3.60, FRIEZE0)                             # front face, 0.18 wide
    a, b = sorted((s * (HW + 0.025), s * HW))                         # 5 mm inside the pier and fascia ends
    T.box(a, b, -0.03, 0.18, SKIRT, FRIEZE0)                           # side face


def u_band(p):
    """Plan outline of a band of projection p round the front and both sides of A."""
    return [(-HW - p, AY1), (-HW - p, -p), (HW + p, -p), (HW + p, AY1), (HW, AY1), (HW, 0.0), (-HW, 0.0),
            (-HW, AY1)]


T.prism(u_band(0.04), FRIEZE0, SOFFIT, axis="z")                     # frieze
T.prism(u_band(0.10), SOFFIT - 0.05, SOFFIT, axis="z")               # bed moulding
T.prism(u_band(0.60), SOFFIT, 10.40, axis="z")                       # soffit and fascia
T.prism(u_band(0.63), 10.40, 10.52, axis="z")                        # crown
T.prism(u_band(0.65), 10.52, CORN_TOP, axis="z")                     # cap

# scroll brackets 0.15 wide, 0.35 tall, 0.35 deep under the soffit (side profile d, z)
BRACKET = [(0.02, SOFFIT), (0.35, SOFFIT), (0.35, 9.71), (0.29, 9.66), (0.20, 9.63), (0.13, 9.56),
           (0.09, 9.48), (0.07, 9.42), (0.02, 9.42)]
for x in BRACKET_X:
    BK.prism([(-d, z) for d, z in BRACKET], x - 0.075, x + 0.075, axis="x")
for y in (0.5, 2.5, 4.5, 6.5, 8.5):                                   # north wall, 2 m centres
    BK.prism([(-HW - d, z) for d, z in BRACKET], y - 0.075, y + 0.075, axis="y")

# ---------------------------------------------------------------------------
# Arched crest (false front at Y 0.35 behind the cornice), half-round louvred vent
# ---------------------------------------------------------------------------
B_OUT = ARCH_APEX - CORN_TOP
SEG = 28
outer = [(ARCH_A, EAVE)] + ellipse(ARCH_A, B_OUT, CORN_TOP, 0.0, SEG) + [(-ARCH_A, EAVE)]
inner = [(ARCH_A - 0.30, EAVE)] + ellipse(ARCH_A, B_OUT, CORN_TOP, 0.30, SEG) + [(-ARCH_A + 0.30, EAVE)]
T.band(outer, inner, ARCH_Y, ARCH_Y + 0.45)                          # outer band, 0.45 thick
FA.prism(inner[::-1], ARCH_Y + 0.10, ARCH_Y + 0.45)                 # tympanum, 0.10 behind the band
im_o = ellipse(ARCH_A, B_OUT, CORN_TOP, 0.65, SEG)
im_i = ellipse(ARCH_A, B_OUT, CORN_TOP, 0.77, SEG)
im_o = [(im_o[0][0], 10.40)] + im_o + [(im_o[-1][0], 10.40)]
im_i = [(im_i[0][0], 10.40)] + im_i + [(im_i[-1][0], 10.40)]
T.band(im_o, im_i, ARCH_Y + 0.04, ARCH_Y + 0.12)                     # inner moulding
# vent: Z 10.90-11.60, 1.30 wide: frame ring, sill, dark back, horizontal louvres
VZ, VR = 10.95, 0.65
vo = [(VR * math.cos(math.pi * i / 12), VZ + VR * math.sin(math.pi * i / 12)) for i in range(13)]
vi = [((VR - 0.09) * math.cos(math.pi * i / 12), VZ + (VR - 0.09) * math.sin(math.pi * i / 12)) for i in range(13)]
T.band(vo, vi, ARCH_Y + 0.03, ARCH_Y + 0.11)
T.box(-VR - 0.05, VR + 0.05, ARCH_Y + 0.02, ARCH_Y + 0.11, 10.90, VZ)
VT.prism(vi[::-1], ARCH_Y + 0.08, ARCH_Y + 0.11)             # plain dark back (louvred, not glazed)
for k in range(5):
    z = VZ + 0.05 + k * 0.10
    hx = math.sqrt(max(0.0, (VR - 0.09) ** 2 - (z + 0.04 - VZ) ** 2))
    SA.prism([(-hx, z), (hx, z), (hx, z + 0.05), (-hx, z + 0.03)], ARCH_Y + 0.05, ARCH_Y + 0.09)

# ---------------------------------------------------------------------------
# Roof: low tin hip over A and B, brick parapets on B, roof box on the ridge
# ---------------------------------------------------------------------------
cos = [(-HW, 0.0, EAVE), (HW, 0.0, EAVE), (HW, BY1, EAVE), (-HW, BY1, EAVE),
       (0.0, RIDGE_Y0, RIDGE), (0.0, RIDGE_Y1, RIDGE),
       (-HW, 0.0, EAVE - 0.06), (HW, 0.0, EAVE - 0.06), (HW, BY1, EAVE - 0.06), (-HW, BY1, EAVE - 0.06)]
R.solid(cos, [[0, 1, 4], [1, 2, 5, 4], [2, 3, 5], [3, 0, 4, 5], [9, 8, 7, 6],
              [6, 7, 1, 0], [7, 8, 2, 1], [8, 9, 3, 2], [9, 6, 0, 3]])
BA.box(-HW, -HW + 0.30, AY1, BY1, EAVE, CORN_TOP)            # brick parapets (top 10.67)
BA.box(HW - 0.30, HW, AY1, BY1, EAVE, CORN_TOP)
BA.box(-HW + 0.30, HW - 0.30, BY1 - 0.30, BY1, EAVE, CORN_TOP)
# roof box (position a guess): body 2.2 x 2.0, flared cap, top 12.90
BX0, BX1, BY0_, BY1_ = -1.10, 1.10, 7.0, 9.0
CL.box(BX0, BX1, BY0_, BY1_, 11.00, 12.55)
c0 = [(BX0, BY0_), (BX1, BY0_), (BX1, BY1_), (BX0, BY1_)]
c1 = [(BX0 - 0.16, BY0_ - 0.16), (BX1 + 0.16, BY0_ - 0.16), (BX1 + 0.16, BY1_ + 0.16), (BX0 - 0.16, BY1_ + 0.16)]
T.solid([(x, y, 12.55) for x, y in c0] + [(x, y, 12.80) for x, y in c1],
        [[3, 2, 1, 0], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
T.box(BX0 - 0.16, BX1 + 0.16, BY0_ - 0.16, BY1_ + 0.16, 12.80, 12.90)

# ---------------------------------------------------------------------------
# Shop fronts (dark painted wood), stair door, fascia, signboards, cornice, stone sill
# ---------------------------------------------------------------------------
KFA.box(PIER_N[1], PIER_S[0], -0.25, SLAB + 0.01, SKIRT, SHOP_HEAD)       # opening through the slab
for x0, x1 in (DOOR_N, DOOR_S):
    KA.box(x0, x1, 0.0, VEST + 0.01, SKIRT, SHOP_HEAD)                    # door recesses 0.60

# piers and posts
for x0, x1 in ((PIER_N[0] - 0.03, PIER_N[1]), POST, WPOST, (PIER_S[0], PIER_S[1] + 0.03)):
    SP.box(x0, x1, -0.05, SLAB + 0.02, 0.0, SHOP_HEAD)
    SP.box(x0 - 0.02, x1 + 0.02, -0.08, SLAB + 0.02, 0.0, 0.30)             # plinth


def display(x0, x1, mirror=False):
    """Display window: panelled bulkhead 0-0.45, sill rail, plate glass to 2.60 with the shared
    shop interior 4 cm behind it, head."""
    SP.box(x0, x1, 0.02, SLAB + 0.02, 0.0, 0.45)
    SP.box(x0 + 0.08, x1 - 0.08, 0.0, 0.02, 0.08, 0.37)                  # raised panel
    SP.box(x0, x1, -0.03, SLAB + 0.02, 0.45, 0.51)                       # sill rail
    pane(FRONT, x0 + 0.06, x1 - 0.06, 0.51, 2.60, -0.13, "shop_a", grow=0.03, mirror=mirror)
    SP.box(x0, x0 + 0.06, 0.04, SLAB + 0.02, 0.51, 2.60)                 # frame stiles
    SP.box(x1 - 0.06, x1, 0.04, SLAB + 0.02, 0.51, 2.60)
    SP.box(x0, x1, -0.02, SLAB + 0.02, 2.60, SHOP_HEAD)                  # head rail


for w, m in ((WIN_N1, False), (WIN_N2, True), (WIN_S1, False), (WIN_S2, True)):
    display(*w, mirror=m)


def shop_door(x0, x1):
    """Pair of glazed doors at the back of a 0.60 recess: dark linings, head, stone floor."""
    SP.box(x0, x0 + 0.04, -0.02, VEST + 0.02, 0.0, SHOP_HEAD)            # side linings
    SP.box(x1 - 0.04, x1, -0.02, VEST + 0.02, 0.0, SHOP_HEAD)
    SP.box(x0, x1, -0.02, VEST + 0.02, 2.55, SHOP_HEAD)                  # head
    T.box(x0, x1, -0.02, VEST + 0.02, SKIRT, 0.02)                        # stone floor
    a0, a1 = x0 + 0.04, x1 - 0.04
    xm = (a0 + a1) / 2
    for k, (a, b) in enumerate(((a0, xm), (xm, a1))):
        SP.box(a, b, VEST - 0.05, VEST, 0.02, 1.05)                       # leaf: lower part
        SP.box(a, a + 0.11, VEST - 0.05, VEST, 1.05, 2.40)                # stiles round the light
        SP.box(b - 0.11, b, VEST - 0.05, VEST, 1.05, 2.40)
        SP.box(a, b, VEST - 0.05, VEST, 2.40, 2.55)                       # top rail
        # glass 1.5 cm into the leaf, the shop 4 cm behind it (just in front of the recess back)
        pane(FRONT, a + 0.11, b - 0.11, 1.05, 2.40, -(VEST - 0.035), ("door_l", "door_r")[k], grow=0.04)
        SP.box(a + 0.13, b - 0.13, VEST - 0.065, VEST - 0.05, 0.22, 0.88)   # raised lower panel
    SP.box(xm - 0.02, xm + 0.02, VEST - 0.07, VEST - 0.05, 0.02, 2.55)    # astragal


shop_door(*DOOR_N)
shop_door(*DOOR_S)

# single plain door to the upper floors: frame, four-panel leaf 0.20 back, head board
s0, s1 = STAIR
SP.box(s0, s0 + 0.15, -0.02, SLAB + 0.02, 0.0, SHOP_HEAD)
SP.box(s1 - 0.15, s1, -0.02, SLAB + 0.02, 0.0, SHOP_HEAD)
SP.box(s0, s1, -0.02, SLAB + 0.02, 2.45, SHOP_HEAD)
SP.box(s0 + 0.15, s1 - 0.15, 0.20, SLAB + 0.02, 0.0, 2.45)
cm = (s0 + s1) / 2
for a, b in ((s0 + 0.27, cm - 0.05), (cm + 0.05, s1 - 0.27)):
    for za, zb in ((0.20, 1.05), (1.20, 2.30)):
        SP.box(a, b, 0.185, 0.20, za, zb)

# fascia 2.75-3.55, shallow cornice 3.55-3.60 projecting 0.25
SP.box(-HW - 0.03, HW + 0.03, -0.06, 0.0, SHOP_HEAD, 3.55)
SP.box(-HW - 0.03, HW + 0.03, -0.12, 0.0, 3.51, 3.55)
SP.box(-HW - 0.05, HW + 0.05, -0.25, 0.0, 3.55, 3.60)

# two BLANK pale signboards on the fascia, Z 3.03-3.50, raised pale border 0.04
for x0, x1 in SIGNS:
    T.box(x0, x1, -0.09, -0.06, 3.03, 3.50)
    T.box(x0, x1, -0.11, -0.09, 3.03, 3.07)
    T.box(x0, x1, -0.11, -0.09, 3.46, 3.50)
    T.box(x0, x0 + 0.04, -0.11, -0.09, 3.07, 3.46)
    T.box(x1 - 0.04, x1, -0.11, -0.09, 3.07, 3.46)

# low pale stone sill Z 0-0.12, 0.25 deep, stopping at the door recesses
for x0, x1 in ((-HW - 0.03, DOOR_N[0]), (DOOR_N[1], DOOR_S[0]), (DOOR_S[1], HW + 0.03)):
    T.box(x0, x1, -0.25, 0.02, SKIRT, 0.12)

# ---------------------------------------------------------------------------
# Two scalloped awnings: Z 3.00 at the wall to 2.45 at Y -1.60, valance to 2.25,
# two thin iron arms and a front bar each (no lettering)
# ---------------------------------------------------------------------------
AW_Z0, AW_Z1, AW_Y = 3.00, 2.45, -1.60
for x0, x1 in AWNINGS:
    AW.prism([(-0.06, AW_Z0), (AW_Y, AW_Z1), (AW_Y, AW_Z1 - 0.02), (-0.06, AW_Z0 - 0.02)], x0, x1, axis="x")
    ns = max(1, round((x1 - x0) / 0.30))
    pitch = (x1 - x0) / ns
    val = [(x1, AW_Z1), (x0, AW_Z1)]
    for k in range(ns):
        a = x0 + k * pitch
        val += [(a, 2.36), (a + 0.2 * pitch, 2.28), (a + 0.5 * pitch, 2.25), (a + 0.8 * pitch, 2.28)]
    val += [(x1, 2.36)]
    AW.prism(val, AW_Y - 0.01, AW_Y, axis="y")
    IR.tube((x0 + 0.05, AW_Y + 0.03, AW_Z1 - 0.03), (x1 - 0.05, AW_Y + 0.03, AW_Z1 - 0.03), 0.015)
    for xa in (x0 + 0.30, x1 - 0.30):
        IR.tube((xa, -0.06, 2.05), (xa, AW_Y + 0.04, AW_Z1 - 0.03), 0.014)
        IR.box(xa - 0.04, xa + 0.04, -0.07, -0.05, 2.00, 2.10)            # wall plate

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
    cut_shell(shell, cutter, "OF_" + name, mat)
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("OF_" + key, MATS[BUILDER_MAT[key]], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Odd Fellows Hall built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)",
      "| panes", len(BACKREC))
# Materials, baked lighting and GLB export: run odd_fellows_hall_bake.py (it runs this file first).
