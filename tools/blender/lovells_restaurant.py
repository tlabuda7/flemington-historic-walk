"""
lovells_restaurant.py - builds Lovell's Restaurant (68 Main St, Flemington; a 2-storey frame
restaurant with a pool room upstairs, front of 1870 with an arch in the roofline, as it stood
c. 1920) in Blender.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/lovells_restaurant.py").read())

Every run deletes and rebuilds the "LovellsRestaurant" collection. Materials, lightmap bake
and GLB export: lovells_restaurant_bake.py (runs this file first). Pattern: house_65_main.py
(4 materials, builders per UV kind) and nevius_store.py (shop front, awning, signs).

Sources: PLAN.md "Lovell's Restaurant (68 Main St)" spec and its orchestrator decisions
(1921 Sanborn sheet 2 footprint; Lovell's photo after 1910 for the shop front, signs and
awning; the c. 1900 "Oysters" photo for the upper floor, cornice blocks and arch; c. 1900
Bank / Oyster House photo and 1908-1910s cards for the clapboard south wall).

Coordinates (metres, Blender Z-up):
    X  across the front, +X = south (Union Hotel side), -X = north (against the bank)
    Y  depth: y = 0 is the front wall face; steps run out to y = -0.95, the awning to -1.56;
       rear wall y = 18.39
    Z  up from the sidewalk top; walls skirt down to -0.10; shop floor 0.45
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".

Seven materials (draw calls): paint (cream clapboard texture; the front and all trim
read as smooth paint through squeezed UVs), dark (plain), signs (generated atlas: awning
canvas, valance lettering, sign boards), stone (steps, stone course, roof, coping), and for
the windows glass, window_back and restaurant_interior (below). The geometry is split into
named builders so the bake can give each its UVs and tint.

Windows (PLAN.md "E. Windows that don't read as flat black", 2026-11-10, same treatment as the
Nevius Store, the Union Hotel and the Bank Building): every pane is ONE glass face (builder
Glass -> material `glass`, transparent, see lovells_restaurant_bake.py) 4 cm in front of a
"window back" face. Upper floor (pool room), the north wall's rear windows and the cellar
lights use cells of the shared atlas assets/textures/shared/window_backs.jpg (blinds at varied
heights, lace, curtains; builder WinBack); the ground-floor glass of the dining room (Ladies'
Entrance door and transom, the centre doors and transom, the display window and the three
south windows) uses assets/textures/shared/restaurant_interior.jpg, made by
tools/prepare_restaurant_interior.py (builder Interior). The backs carry their atlas UVs
(layer "UVMap") from here; the bake keeps them.
"""

import json
import math
import random
import bpy
import bmesh
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md)
# ---------------------------------------------------------------------------
HW = 3.00                 # half width (6.00 m)
DEPTH = 18.39
FL = 0.45                 # shop floor / top of the stone course
SKIRT = -0.10
RZ0, RZ1 = 6.49, 6.27     # top of the wall shell (under the tin roof) at the front / rear
FRIEZE, EAVE, CORN_TOP = 6.05, 6.30, 6.55
BANK_Y = 11.05            # the north wall is against the bank up to here
RECESS = 0.28             # window / door openings are shallow recesses this deep
WIN_X = 1.65              # upper front windows (spec 1.50; photos ~1.6, clears the LOVELL'S board)
W_UP = (0.85, 4.30, 5.75)     # side windows (width, sill, head)
W_DN = (0.85, 1.25, 2.95)
ARCH_HALF, ARCH_SPRING, ARCH_RISE = 1.45, 6.70, 0.75    # intrados apex 7.45, crown 7.65
BLOCK_IN = 1.45           # inner end of the cornice blocks


def rz(y):
    """Top of the wall shell / underside of the roof at depth y."""
    return RZ0 + (RZ1 - RZ0) * y / DEPTH


# ---------------------------------------------------------------------------
# Materials (plain stand-ins; lovells_restaurant_bake.py swaps in the textures)
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


COLOURS = {"Paint": "#e4ddcb", "Dark": "#2b302c", "Signs": "#e8e2d2", "Stone": "#8e8c86",
           "Glass": "#1a1916", "WindowBack": "#3a332c", "Interior": "#2e2822"}
MATS = {k: plain("LV_" + k, c) for k, c in COLOURS.items()}
# builder -> material (the bake gives every builder its own UVs and tint)
BUILDER_MAT = {"Trim": "Paint", "Chimney": "Paint", "Dark": "Dark", "Stone": "Stone", "Roof": "Stone",
               "Awning": "Signs", "Canvas": "Signs", "Valance": "Signs",
               "BoardR": "Signs", "BoardL": "Signs", "BoardIce": "Signs",
               "DoorFrame": "Paint",       # door stiles, rails, panels, transom bars: paint + dark bake tint
               "Glass": "Glass", "WinBack": "WindowBack", "Interior": "Interior"}

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
        """Extrude a 2D outline [(u, v), ...] between depths d0 and d1 along an axis
        ('y': outline in X-Z; 'x': outline in Y-Z; 'z': plan outline in X-Y)."""
        self._extrude([self._pt(axis, u, d0, v) for u, v in pts],
                      [self._pt(axis, u, d1, v) for u, v in pts])

    def box(self, x0, x1, y0, y1, z0, z1):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)

    def wprism(self, wall, pts, d0, d1):
        """Outline [(u, z), ...] in a wall's plane, extruded from depth d0 to d1."""
        self._extrude([wall.pt(u, z, d0) for u, z in pts], [wall.pt(u, z, d1) for u, z in pts])

    def wbox(self, wall, u0, u1, z0, z1, d0, d1):
        self.wprism(wall, rect(u0, u1, z0, z1), d0, d1)

    def lathe(self, cx, cy, rings, sides=8):
        """Vertical solid of revolution: rings [(radius, z), ...] bottom to top, capped."""
        bm = self.bm
        loops = []
        for r, z in rings:
            loops.append([bm.verts.new((cx + r * math.cos(2 * math.pi * (i + 0.5) / sides),
                                        cy + r * math.sin(2 * math.pi * (i + 0.5) / sides), z))
                          for i in range(sides)])
        faces = [bm.faces.new(list(reversed(loops[0]))), bm.faces.new(loops[-1])]
        for a, b in zip(loops, loops[1:]):
            for i in range(sides):
                j = (i + 1) % sides
                faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
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


def seg_geom(chord, zs, rise):
    """Circle of a segmental arc of the given chord springing at zs: (centre z, radius, half angle)."""
    R = ((chord / 2) ** 2 + rise ** 2) / (2 * rise)
    return zs + rise - R, R, math.asin((chord / 2) / R)


def arc_pts(cu, zc, r, a0, a1, segs):
    return [(cu + r * math.cos(a0 + (a1 - a0) * i / segs), zc + r * math.sin(a0 + (a1 - a0) * i / segs))
            for i in range(segs + 1)]


def band(cu, zc, r_in, r_out, a0, a1, segs):
    """Outline of a curved band (annulus segment) between angles a0 and a1."""
    return arc_pts(cu, zc, r_out, a0, a1, segs) + arc_pts(cu, zc, r_in, a1, a0, segs)


# ---------------------------------------------------------------------------
# Window backs and glass
# ---------------------------------------------------------------------------
WB_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\window_backs.json"))["cells"]
RI_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\restaurant_interior.json"))["cells"]
GAP = 0.04             # window back this far behind the glass
# Pool room upstairs: roller blinds at different heights, lace, a few curtains.
UPPER_WEIGHTS = {"blind_cream_high": 2, "blind_cream_half": 3, "blind_cream_low": 1, "blind_green_high": 1,
                 "blind_green_half": 2, "lace": 2, "lace_blind_cream": 2, "lace_blind_green": 1,
                 "lace_full_blind_cream": 1, "curtains_beige": 1, "curtains_olive": 1, "curtains_maroon_blind": 1}
# Kitchen / back room (north wall, rear, ground floor): plain blinds and curtains.
KITCHEN_WEIGHTS = {"blind_cream_half": 2, "blind_cream_low": 1, "blind_green_half": 1, "curtains_beige": 1,
                   "lace_blind_cream": 1}
_wb_rng = random.Random(1870)
_wb_grid = {}          # (wall, row) -> {column: cell}, so neighbours (side by side, above/below) differ


def pick_cell(weights, wall, row, colm):
    avoid = {_wb_grid.get((wall, row), {}).get(colm - 1), _wb_grid.get((wall, row - 1), {}).get(colm),
             _wb_grid.get((wall, row + 1), {}).get(colm), _wb_grid.get((wall, row), {}).get(colm + 1)}
    names = [n for n in weights if n not in avoid]
    cell = _wb_rng.choices(names, weights=[weights[n] for n in names])[0]
    _wb_grid.setdefault((wall, row), {})[colm] = cell
    return cell


def flat_face(mb, wall, pts, d, uv=None):
    """One flat face [(u, z), ...] in a wall's plane at depth d, facing out (wall.n). With
    uv = (U0, V0, U1, V1) its bounding box is mapped onto that atlas rectangle, left to right
    as seen from outside."""
    bm = mb.bm
    f = bm.faces.new([bm.verts.new(wall.pt(u, z, d)) for u, z in pts])
    f.normal_update()
    if f.normal.dot(Vector((wall.n[0], wall.n[1], 0.0))) < 0:
        f.normal_flip()
    if uv:
        layer = bm.loops.layers.uv.get("UVMap") or bm.loops.layers.uv.new("UVMap")
        us, zs = [p[0] for p in pts], [p[1] for p in pts]
        u0, u1, z0, z1 = min(us), max(us), min(zs), max(zs)
        right = (-wall.n[1], wall.n[0])                   # viewer's right, facing the wall
        flip = wall.t[0] * right[0] + wall.t[1] * right[1] < 0
        U0, V0, U1, V1 = uv
        for loop in f.loops:
            co = loop.vert.co
            u = (co.x - wall.p0[0]) * wall.t[0] + (co.y - wall.p0[1]) * wall.t[1]
            t = (u - u0) / (u1 - u0)
            t = 1 - t if flip else t
            loop[layer].uv = (U0 + (U1 - U0) * t, V0 + (V1 - V0) * (co.z - z0) / (z1 - z0))


def window_back(wall, pts, d, cell):
    if cell in RI_CELLS:
        flat_face(G["Interior"], wall, pts, d, RI_CELLS[cell]["uv"])
    else:
        flat_face(G["WinBack"], wall, pts, d, WB_CELLS[cell]["uv"])


def pane(wall, glass_pts, d_glass, cell, back_pts=None):
    """Glass face at depth d_glass (< 0: behind the wall face), window back GAP behind it
    (back_pts: a larger outline hidden at its edges by the sash, default the glass outline)."""
    flat_face(G["Glass"], wall, glass_pts, d_glass)
    window_back(wall, back_pts or glass_pts, d_glass - GAP, cell)


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


col = fresh_collection("LovellsRestaurant")
G = {k: MB() for k in BUILDER_MAT}
T, D, ST, R = G["Trim"], G["Dark"], G["Stone"], G["Roof"]
DF = G["DoorFrame"]
SHELL, CUT = MB(), MB()

FRONT_W = Wall((0.0, 0.0), (1, 0), (0, -1), CUT)
SOUTH_W = Wall((HW, 0.0), (0, 1), (1, 0), CUT)
NORTH_W = Wall((-HW, 0.0), (0, 1), (-1, 0), CUT)
REAR_W = Wall((0.0, DEPTH), (1, 0), (0, 1), CUT)

# Wall planes (point, normal) for the bake: the clapboarded ones (sides and rear) and all four
SIDE_PLANES = [((w.p0[0], w.p0[1]), w.n) for w in (SOUTH_W, NORTH_W, REAR_W)]
WALL_PLANES = SIDE_PLANES + [((0.0, 0.0), (0, -1))]
SIGN_RECTS = {}           # builder -> (x0, x1, z0, z1) of its lettered front face

# ---------------------------------------------------------------------------
# Shell (one closed solid, cut by the openings), roof, parapet
# ---------------------------------------------------------------------------
SHELL.prism([(0.0, SKIRT), (DEPTH, SKIRT), (DEPTH, rz(DEPTH)), (0.0, rz(0.0))], -HW, HW, axis="x")

# tin shed roof slab on top of the shell, inside the side cornices
R.prism([(0.20, rz(0.20)), (DEPTH, rz(DEPTH)), (DEPTH, rz(DEPTH) + 0.06), (0.20, rz(0.20) + 0.06)],
        -HW + 0.01, HW - 0.01, axis="x")

# front parapet: ends behind the cornice blocks up to 6.68, flat boarded tympanum under the arch
azc, aR, ath = seg_geom(2 * ARCH_HALF, ARCH_SPRING, ARCH_RISE)
tymp = [(-HW, RZ0), (HW, RZ0), (HW, 6.68), (ARCH_HALF, 6.68)] + \
    arc_pts(0.0, azc, aR, math.pi / 2 - ath, math.pi / 2 + ath, 16) + [(-ARCH_HALF, 6.68), (-HW, 6.68)]
T.wprism(FRONT_W, tymp, -0.20, 0.0)


def arch_band(mb, r_in, r_out, d0, d1):
    """Archivolt band springing from the cornice-block tops (z 6.70 at its outer radius)."""
    a = math.asin((ARCH_SPRING - azc) / r_out)
    mb.wprism(FRONT_W, band(0.0, azc, r_in, r_out, a, math.pi - a, 16), d0, d1)


arch_band(T, aR, aR + 0.10, -0.20, 0.18)            # inner fascia
arch_band(T, aR + 0.10, aR + 0.20, -0.20, 0.30)     # crown moulding
arch_band(R, aR + 0.20, aR + 0.23, -0.22, 0.32)     # thin coping (tin grey)
T.wbox(FRONT_W, -BLOCK_IN, BLOCK_IN, 6.10, 6.18, -0.01, 0.05)   # moulding at the wall head under the arch

# ---------------------------------------------------------------------------
# Stone course 0 ... 0.45 all round (0.03 proud), cellar windows in it
# ---------------------------------------------------------------------------
SC = 0.03
CELLAR_F = (1.525, 2.225, 0.08, 0.38)          # under the display window (0.70 x 0.30)
CELLAR_S = [(4.5, 0.60), (12.5, 0.60)]         # south wall (y, width)


def stone_course(wall, a, b, holes):
    """holes: [(u0, u1, z0, z1)] cellar windows: the course is built round them."""
    for u0, u1 in spans(a, b, [(h[0], h[1]) for h in holes]):
        ST.wbox(wall, u0, u1, SKIRT, FL, -0.01, SC)
    for u0, u1, z0, z1 in holes:
        ST.wbox(wall, u0, u1, SKIRT, z0, -0.01, SC)
        ST.wbox(wall, u0, u1, z1, FL, -0.01, SC)


def cellar_window(wall, u0, u1, z0, z1, cell="dark_room"):
    wall.cut.wbox(wall, u0, u1, z0, z1, -0.16, 0.25)
    pane(wall, rect(u0, u1, z0, z1), -0.11, cell)                # glass, dark cellar behind
    for k in (1, 2, 3):                                          # iron bars
        u = u0 + (u1 - u0) * k / 4
        D.wbox(wall, u - 0.012, u + 0.012, z0, z1, -0.10, -0.075)


stone_course(FRONT_W, 0.80, HW + SC, [CELLAR_F])                 # the steps cover x -3.00 ... 0.80
cellar_window(FRONT_W, *CELLAR_F, cell="dark_room_frame")
stone_course(SOUTH_W, 0.0, DEPTH + SC, [(y - w / 2, y + w / 2, 0.08, 0.38) for y, w in CELLAR_S])
for k, (y, w) in enumerate(CELLAR_S):
    cellar_window(SOUTH_W, y - w / 2, y + w / 2, 0.08, 0.38, cell=("dark_room", "dark_room_frame")[k])
stone_course(NORTH_W, 0.0, DEPTH + SC, [])
stone_course(REAR_W, -HW, HW, [])

# ---------------------------------------------------------------------------
# Windows, shutters, doors
# ---------------------------------------------------------------------------


def shutters(wall, cu, half, z0, z1, gap=0.11, leaf=0.43, ribs=5):
    """Louvred shutters open flat beside an opening, 0.03 off the wall."""
    for sgn in (-1, 1):
        u0, u1 = sorted((cu + sgn * (half + gap), cu + sgn * (half + gap + leaf)))
        D.wbox(wall, u0, u1, z0, z1, 0.03, 0.06)                   # leaf
        for k in range(ribs):                                       # louvre ribs that catch the light
            zc = z0 + (z1 - z0) * (k + 0.5) / ribs
            D.wbox(wall, u0 + 0.05, u1 - 0.05, zc - 0.03, zc + 0.03, 0.06, 0.075)


def window(wall, cu, size, shut=True, cell="dark_room"):
    """2/2 double-hung side window in a shallow recess: glass inside the sash with a window
    back behind it, sash (stiles, rails, meeting rail, one vertical muntin), flat 0.10 casing
    with a capped head, sill 0.05 proud."""
    w, z0, z1 = size
    h = w / 2
    s = 0.05
    wall.cut.wbox(wall, cu - h, cu + h, z0, z1, -RECESS, 0.25)
    pane(wall, rect(cu - h + s, cu + h - s, z0 + 0.07, z1 - 0.05), -0.11, cell, rect(cu - h, cu + h, z0, z1))
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
    T.wbox(wall, cu - h - c - 0.03, cu + h + c + 0.03, z1 + 0.10, z1 + 0.13, -0.01, 0.065)   # head cap
    T.wbox(wall, cu - h - c - 0.03, cu + h + c + 0.03, z0 - 0.05, z0, -0.14, 0.05)          # sill
    if shut:
        shutters(wall, cu, h + c, z0, z1, gap=0.01, ribs=5)


def front_window(cu, cell="dark_room"):
    """Upper front window: 2/2 sash 0.85 x 1.45, segmental head (rise 0.12), flat casing
    following the head, segmental moulded hood to ~5.82, sill, louvred shutters."""
    W = FRONT_W
    w, z0, zs, rise = 0.85, 4.20, 5.53, 0.12
    h = w / 2
    zc, Rr, th = seg_geom(w, zs, rise)
    outline = [(cu - h, z0), (cu + h, z0)] + arc_pts(cu, zc, Rr, math.pi / 2 - th, math.pi / 2 + th, 6)
    W.cut.wprism(W, outline, -RECESS, 0.25)
    pane(W, outline, -0.11, cell)                                           # glass + window back
    s = 0.05
    for a, b in ((cu - h, cu - h + s), (cu + h - s, cu + h)):
        T.wbox(W, a, b, z0, zs + 0.02, -0.14, -0.08)                       # stiles
    zm = (z0 + zs) / 2 + 0.05
    for za, zb in ((z0, z0 + 0.07), (zm - 0.02, zm + 0.02)):
        T.wbox(W, cu - h + s, cu + h - s, za, zb, -0.14, -0.08)            # bottom / meeting rail
    T.wprism(W, band(cu, zc, Rr - 0.06, Rr, math.pi / 2 - th, math.pi / 2 + th, 6), -0.14, -0.08)   # head rail
    T.wbox(W, cu - 0.015, cu + 0.015, z0 + 0.07, zc + Rr - 0.06, -0.13, -0.09)                    # muntin
    c = 0.10
    for a, b in ((cu - h - c, cu - h), (cu + h, cu + h + c)):
        T.wbox(W, a, b, z0, zs + 0.03, -0.01, 0.025)                       # casing jambs
    tc = math.asin((h + c) / (Rr + c))
    T.wprism(W, band(cu, zc, Rr, Rr + c, math.pi / 2 - tc, math.pi / 2 + tc, 6), -0.01, 0.025)   # head casing
    th2 = math.asin(min(0.99, (h + c + 0.04) / (Rr + c + 0.07)))
    T.wprism(W, band(cu, zc, Rr + c - 0.02, Rr + c + 0.05, math.pi / 2 - th2, math.pi / 2 + th2, 6), -0.01, 0.08)  # hood
    T.wprism(W, band(cu, zc, Rr + c + 0.05, Rr + c + 0.07, math.pi / 2 - th2, math.pi / 2 + th2, 6), -0.01, 0.05)  # fillet
    T.wbox(W, cu - h - c - 0.03, cu + h + c + 0.03, z0 - 0.05, z0, -0.14, 0.05)                   # sill
    shutters(W, cu, h + c, z0, zs + 0.08, gap=0.01, ribs=5)


def side_door(wall, cu, w, z0, z1):
    """4-panel dark door set 0.10 in, flat 0.12 casing with a capped head."""
    h = w / 2
    wall.cut.wbox(wall, cu - h, cu + h, z0 - 0.03, z1, -RECESS, 0.25)
    D.wbox(wall, cu - h, cu + h, z0, z1, -0.14, -0.10)                     # leaf
    for ua, ub in ((cu - h + 0.10, cu - 0.04), (cu + 0.04, cu + h - 0.10)):
        for za, zb in ((z0 + 0.15, z0 + 0.95), (z0 + 1.10, z1 - 0.12)):
            D.wbox(wall, ua, ub, za, zb, -0.10, -0.085)                    # raised panels
    T.wbox(wall, cu - h - 0.05, cu + h + 0.05, z0 - 0.08, z0, -0.14, 0.04)  # threshold
    c = 0.12
    for a, b in ((cu - h - c, cu - h), (cu + h, cu + h + c)):
        T.wbox(wall, a, b, z0 - 0.08, z1, -0.01, 0.03)
    T.wbox(wall, cu - h - c, cu + h + c, z1, z1 + 0.10, -0.01, 0.035)
    T.wbox(wall, cu - h - c - 0.03, cu + h + c + 0.03, z1 + 0.10, z1 + 0.13, -0.01, 0.07)


# Upper front: two shuttered windows with segmental hoods
for k, x in enumerate((-WIN_X, WIN_X)):
    front_window(x, cell=pick_cell(UPPER_WEIGHTS, "front", 1, k))

# South wall: 4 windows upstairs, 3 + the kitchen door downstairs, all shuttered (the ground
# floor ones look into the dining room)
for k, y in enumerate((2.5, 6.5, 10.5, 14.5)):
    window(SOUTH_W, y, W_UP, cell=pick_cell(UPPER_WEIGHTS, "south", 1, k))
for k, y in enumerate((2.5, 6.5, 10.5)):
    window(SOUTH_W, y, W_DN, cell="south_%d" % k)
side_door(SOUTH_W, 15.5, 0.90, FL, FL + 2.10)
ST.box(HW + 0.0, HW + 0.40, 14.95, 16.05, SKIRT, 0.30)                      # kitchen-door step

# North wall: blank against the bank (0 ... 11.05); 2 windows per floor on the rear part, no shutters
for k, y in enumerate((13.0, 16.5)):
    window(NORTH_W, y, W_UP, shut=False, cell=pick_cell(UPPER_WEIGHTS, "north", 1, k))
    window(NORTH_W, y, W_DN, shut=False, cell=pick_cell(KITCHEN_WEIGHTS, "north", 0, k))

# ---------------------------------------------------------------------------
# Shop front (Lovell's photo): pilaster - Ladies' door - pier - recessed double door -
# pier - display window - pilaster; sign board with end consoles and crown moulding
# ---------------------------------------------------------------------------
TOP_SF = 3.45                     # top of the openings (transoms)

# corner pilasters 0.08 proud with plinths, a sunk panel (raised margins) and caps
for s in (-1, 1):
    x0, x1 = sorted((s * 2.65, s * HW))
    T.box(x0, x1, -0.08, 0.0, FL, 3.45)                                       # shaft
    T.box(x0 - 0.01, x1 + 0.01, -0.10, 0.0, FL, 0.75)                          # plinth
    T.box(x0 - 0.02, x1 + 0.02, -0.12, 0.0, 3.38, 3.55)                        # cap
    for a, b, za, zb in ((x0 + 0.04, x0 + 0.08, 0.85, 3.28), (x1 - 0.08, x1 - 0.04, 0.85, 3.28),
                         (x0 + 0.08, x1 - 0.08, 0.85, 0.89), (x0 + 0.08, x1 - 0.08, 3.24, 3.28)):
        T.box(a, b, -0.10, -0.08, za, zb)                                      # panel margins

# piers: one raised panel each
for x0, x1 in ((-1.70, -1.05), (0.65, 1.10)):
    T.box(x0 + 0.08, x1 - 0.08, -0.02, 0.0, 0.65, 3.25)

# Left door (Ladies' Entrance): x -2.65 ... -1.70, door 0.45 - 2.75, transom 2.85 - 3.45
LD0, LD1 = -2.65, -1.70
CUT.box(LD0, LD1, -0.25, RECESS, FL, TOP_SF)
ST.box(LD0, LD1, -0.02, RECESS, FL - 0.02, FL + 0.01)                         # threshold


def leaf(x0, x1, z0, z1, y_face, glass_from, cell):
    """Door leaf at depth y_face (its front): stiles and rails 0.10, raised lower panel
    (DoorFrame: painted dark green), glass (one face, 0.025 into the leaf, the dining room
    seen through it on a window back behind the leaf) from glass_from up to the top rail."""
    yb = y_face + 0.05
    DF.box(x0, x0 + 0.10, y_face, yb, z0, z1)
    DF.box(x1 - 0.10, x1, y_face, yb, z0, z1)
    DF.box(x0 + 0.10, x1 - 0.10, y_face, yb, z0, z0 + 0.22)                    # bottom rail
    DF.box(x0 + 0.10, x1 - 0.10, y_face, yb, glass_from - 0.12, glass_from)    # lock rail
    DF.box(x0 + 0.10, x1 - 0.10, y_face, yb, z1 - 0.12, z1)                    # top rail
    DF.box(x0 + 0.10, x1 - 0.10, y_face + 0.02, yb, z0 + 0.22, glass_from - 0.12)   # panel field
    DF.box(x0 + 0.16, x1 - 0.16, y_face + 0.005, y_face + 0.02, z0 + 0.30, glass_from - 0.20)   # raised panel
    pane(FRONT_W, rect(x0 + 0.10, x1 - 0.10, glass_from, z1 - 0.12), -(y_face + 0.025), cell)   # glass


leaf(LD0 + 0.03, LD1 - 0.03, FL, 2.75, 0.12, 1.45, "ladies_door")
DF.box(LD0, LD1, 0.02, RECESS - 0.02, 2.75, 2.85)                              # transom bar
pane(FRONT_W, rect(LD0, LD1, 2.85, TOP_SF), -0.13, "ladies_t")                 # transom glass
DF.box(-2.19, -2.16, 0.10, 0.13, 2.85, TOP_SF)                                  # transom muntin

# Centre double door: x -1.05 ... +0.65, recessed 0.45, panelled reveals
CD0, CD1, CREC = -1.05, 0.65, 0.45
# recess cutter; 6 cm deeper at the transom so its window back sits behind the glass
CUT.prism([(-0.25, FL), (CREC, FL), (CREC, 2.95), (CREC + 0.06, 2.95), (CREC + 0.06, TOP_SF), (-0.25, TOP_SF)],
          CD0, CD1, axis="x")
ST.box(CD0, CD1, -0.02, CREC, FL - 0.02, FL + 0.01)                           # recess floor / threshold
T.box(CD0, CD0 + 0.10, CREC - 0.06, CREC, FL, TOP_SF)                          # door frame jambs
T.box(CD1 - 0.10, CD1, CREC - 0.06, CREC, FL, TOP_SF)
DF.box(CD0, CD1, CREC - 0.07, CREC, 2.85, 2.95)                                # transom bar
pane(FRONT_W, rect(CD0 + 0.10, CD1 - 0.10, 2.95, TOP_SF), -(CREC - 0.03), "door_t")   # transom glass
DF.box(-0.215, -0.185, CREC - 0.05, CREC - 0.03, 2.95, TOP_SF)                  # transom muntin
xm = (CD0 + CD1) / 2
leaf(CD0 + 0.10, xm - 0.005, FL, 2.85, CREC - 0.11, 1.15, "door_l")
leaf(xm + 0.005, CD1 - 0.10, FL, 2.85, CREC - 0.11, 1.15, "door_r")
for xr, sgn in ((CD0, 1), (CD1, -1)):                                          # panelled reveals
    xa, xb = sorted((xr, xr + sgn * 0.02))
    for za, zb in ((0.62, 1.30), (1.45, 3.30)):
        T.box(xa, xb, 0.06, CREC - 0.10, za, zb)

# Display window: x 1.10 ... 2.65, bulkhead 0.45 - 1.05 with the ICE CREAM panel, glass
# 1.05 - 2.95 in one pane, 2-light top row 2.95 - 3.45
DW0, DW1 = 1.10, 2.65
CUT.box(DW0, DW1, -0.25, 0.20, 1.05, TOP_SF)
pane(FRONT_W, rect(DW0, DW1, 1.05, 2.95), -0.10, "display")                     # glass, the dining room
pane(FRONT_W, rect(DW0, DW1, 2.95, TOP_SF), -0.10, "display_t")                 # top row
for a, b in ((DW0, DW0 + 0.06), (DW1 - 0.06, DW1)):
    T.box(a, b, 0.04, 0.12, 1.05, TOP_SF)                                      # frame stiles
T.box(DW0, DW1, 0.04, 0.12, 3.39, TOP_SF)                                      # head
T.box(DW0, DW1, 0.04, 0.12, 2.92, 2.98)                                        # transom bar
T.box(1.85, 1.90, 0.04, 0.12, 2.98, 3.39)                                      # top-row mullion
T.box(DW0 - 0.06, DW1 + 0.06, -0.06, 0.20, 1.00, 1.06)                         # sill
# bulkhead: moulded frame round the ICE CREAM panel
for a, b, za, zb in ((DW0, DW0 + 0.08, FL, 1.00), (DW1 - 0.08, DW1, FL, 1.00),
                     (DW0, DW1, FL, 0.52), (DW0, DW1, 0.95, 1.00)):
    T.box(a, b, -0.03, 0.0, za, zb)
SIGN_RECTS["BoardIce"] = (DW0 + 0.10, DW1 - 0.10, 0.54, 0.93)
G["BoardIce"].box(DW0 + 0.10, DW1 - 0.10, -0.025, 0.0, 0.54, 0.93)

# sign board ("RESTAURANT") 3.55 - 3.98 between the consoles, crown moulding, consoles
SB0, SB1 = 2.725, 2.975
SIGN_RECTS["BoardR"] = (-SB0, SB0, 3.56, 3.98)
G["BoardR"].box(-SB0, SB0, -0.06, 0.0, 3.56, 3.98)
T.box(-SB0, SB0, -0.08, 0.0, 3.52, 3.56)                                       # bottom moulding
T.prism([(0.0, 3.98), (-0.07, 3.98), (-0.09, 4.02), (-0.15, 4.06), (-0.15, 4.10), (0.0, 4.10)],
        -SB0, SB0, axis="x")                                                   # crown moulding
for s in (-1, 1):                                                              # end consoles
    x0, x1 = sorted((s * SB0, s * SB1))
    T.prism([(0.0, 3.45), (-0.07, 3.45), (-0.10, 3.53), (-0.12, 3.68), (-0.15, 3.86), (-0.18, 4.02),
             (-0.18, 4.15), (0.0, 4.15)], x0, x1, axis="x")
    T.box(x0 - 0.02, x1 + 0.02, -0.21, 0.0, 4.15, 4.20)                        # console cap

# ---------------------------------------------------------------------------
# Upper front trim: corner boards, LOVELL'S board, frieze boards under the cornice blocks
# ---------------------------------------------------------------------------
for s in (-1, 1):
    x0, x1 = sorted((s * 2.85, s * HW))
    T.box(x0, x1, -0.03, 0.0, 4.20, 5.85)
    x0, x1 = sorted((s * BLOCK_IN, s * HW))
    T.box(x0, x1, -0.03, 0.0, 5.85, 6.45)                                      # frieze board
SIGN_RECTS["BoardL"] = (-0.67, 0.67, 4.12, 4.44)
G["BoardL"].box(-0.67, 0.67, -0.05, 0.0, 4.12, 4.44)

# ---------------------------------------------------------------------------
# Cornice blocks (bed, corona, cap; 0.45 projection, 0.45 return along the sides) on 3 scroll
# brackets each; one more bracket on the south side face at the front corner
# ---------------------------------------------------------------------------
for s in (-1, 1):
    for z0, z1, p in ((6.45, 6.52, 0.30), (6.52, 6.63, 0.42), (6.63, 6.70, 0.45)):
        sp = p - 0.15 if s > 0 else 0.03          # north side: tight against the bank
        x0, x1 = sorted((s * BLOCK_IN, s * (HW + sp)))
        T.box(x0, x1, -p, 0.45, z0, z1)

BRACKET = [(0.03, 6.448), (0.40, 6.448), (0.40, 6.37), (0.33, 6.31), (0.22, 6.28), (0.15, 6.17),
           (0.12, 6.03), (0.10, 5.90), (0.03, 5.90)]          # (projection, z)
for s in (-1, 1):
    for bx in (2.95, 2.35, 1.65):
        x = s * bx
        T.prism([(-d, z) for d, z in BRACKET], x - 0.06, x + 0.06, axis="x")
        T.box(x - 0.035, x + 0.035, -0.11, -0.04, 5.84, 5.90)                  # drop pendant
T.prism([(HW + d * 0.55, z) for d, z in BRACKET], 0.24, 0.36, axis="y")       # south corner bracket

# ---------------------------------------------------------------------------
# Side cornices (frieze board, bed moulding, boxed cornice 0.30 overhang), rear fascia,
# corner boards
# ---------------------------------------------------------------------------
for wall, a, b, over in ((SOUTH_W, 0.45, DEPTH, 0.30), (NORTH_W, 0.45, BANK_Y, 0.03), (NORTH_W, BANK_Y, DEPTH, 0.30)):
    T.wbox(wall, a if wall is NORTH_W and a > 1 else 0.0, b, FRIEZE, EAVE, -0.01, 0.025)    # frieze
    if over > 0.1:
        T.wbox(wall, a, b, EAVE - 0.06, EAVE, -0.01, 0.10)                     # bed moulding
    T.wbox(wall, a, b, EAVE, CORN_TOP, -0.01, over)                            # boxed cornice
T.box(-HW - 0.03, HW + 0.03, DEPTH - 0.01, DEPTH + 0.03, FRIEZE, rz(DEPTH) + 0.09)   # rear fascia
for wall, us in ((SOUTH_W, ((0.0, 0.15), (DEPTH - 0.15, DEPTH + 0.03))), (NORTH_W, ((DEPTH - 0.15, DEPTH + 0.03),)),
                 (REAR_W, ((-HW - 0.03, -HW + 0.12), (HW - 0.12, HW + 0.03)))):
    for u0, u1 in us:
        T.wbox(wall, u0, u1, FL, FRIEZE, -0.01, 0.03)

# ---------------------------------------------------------------------------
# Chimney (brick, guess): kitchen range flue on the north side at y 15.0, top 7.90
# ---------------------------------------------------------------------------
CH = G["Chimney"]
CH.box(-2.95, -2.45, 14.70, 15.30, 6.20, 7.72)
CH.box(-3.00, -2.40, 14.65, 15.35, 7.72, 7.80)                                 # corbel course
CH.box(-2.95, -2.45, 14.70, 15.30, 7.80, 7.90)

# ---------------------------------------------------------------------------
# Steps (stone): 3 risers across x -3.00 ... +0.80 (both doors); display bay has none
# ---------------------------------------------------------------------------
for y0, y1, ztop in ((-0.95, -0.65, 0.15), (-0.65, -0.35, 0.30), (-0.35, 0.0, FL)):
    ST.box(-HW, 0.80, y0, y1, SKIRT, ztop)

# ---------------------------------------------------------------------------
# Hanging gas lantern over the centre door (under the awning)
# ---------------------------------------------------------------------------
LX, LY = -0.20, -0.35
# iron arm at 3.40, fixed to the centre door's transom frame at the back of the recess
D.prism([(CREC - 0.06, 3.38), (CREC - 0.06, 3.42), (LY - 0.02, 3.40), (LY - 0.02, 3.36)], LX - 0.015, LX + 0.015, axis="x")
D.box(LX - 0.012, LX + 0.012, LY - 0.012, LY + 0.012, 3.09, 3.38)             # hanger rod
# body 2.65 - 3.10 (spec): dark iron bottom and cap; the glass body is pale (paint) so it
# reads against the doors, as the lit glass does in the photo
D.lathe(LX, LY, [(0.02, 2.65), (0.06, 2.69), (0.10, 2.73), (0.135, 2.77), (0.135, 2.79), (0.02, 2.79)], sides=8)
T.lathe(LX, LY, [(0.115, 2.785), (0.125, 2.82), (0.125, 2.97), (0.115, 3.005)], sides=8)
D.lathe(LX, LY, [(0.02, 3.00), (0.135, 3.00), (0.16, 3.02), (0.16, 3.05), (0.06, 3.09), (0.02, 3.10)], sides=8)
for k in range(4):                                                             # corner posts
    a = math.pi / 4 + k * math.pi / 2
    px, py = LX + 0.122 * math.cos(a), LY + 0.122 * math.sin(a)
    D.box(px - 0.012, px + 0.012, py - 0.012, py + 0.012, 2.78, 3.01)

# ---------------------------------------------------------------------------
# Awning (review round 1: shallow hood as in Lovell's and the Oysters photos): pale canvas
# x -2.90 ... +2.90 hung at 3.52 (clear of the pilaster caps), out to 3.30 at y -0.95;
# scalloped valance 3.30 -> 3.00 (18 scallops) just under the RESTAURANT board; side cheeks;
# iron arms. The transoms, doors and the lantern show below it.
# ---------------------------------------------------------------------------
AW0, AW1, AWY, AWZ0, AWZ1 = -2.90, 2.90, -0.95, 3.52, 3.30
VAL_BOT = AWZ1 - 0.30
AW_D = 0.13                                          # starts this far out from the wall
G["Awning"].prism([(-AW_D, AWZ0), (AWY, AWZ1), (AWY, AWZ1 - 0.02), (-AW_D, AWZ0 - 0.02)], AW0, AW1, axis="x")
NS = 18
pitch = (AW1 - AW0) / NS
val = [(AW1, AWZ1), (AW0, AWZ1)]
for k in range(NS):
    x0 = AW0 + k * pitch
    val += [(x0, VAL_BOT + 0.08), (x0 + 0.15 * pitch, VAL_BOT + 0.025), (x0 + 0.5 * pitch, VAL_BOT),
            (x0 + 0.85 * pitch, VAL_BOT + 0.025)]
val += [(AW1, VAL_BOT + 0.08)]
G["Valance"].prism(val, AWY - 0.01, AWY, axis="y")
SIGN_RECTS["Valance"] = (AW0, AW1, VAL_BOT, AWZ1)
for x in (AW0, AW1):                                 # side cheeks (canvas triangles)
    G["Canvas"].prism([(-AW_D, AWZ0 - 0.02), (AWY, AWZ1 - 0.02), (-AW_D, AWZ1 - 0.02)], x - 0.005, x + 0.005, axis="x")
D.box(AW0, AW1, AWY + 0.005, AWY + 0.03, AWZ1 - 0.05, AWZ1 - 0.02)            # front bar behind the valance
for x in (-2.80, 2.80):                                                        # iron arms
    D.prism([(0.0, 3.08), (0.0, 3.12), (AWY + 0.03, AWZ1 - 0.02), (AWY + 0.03, AWZ1 - 0.06)],
            x - 0.012, x + 0.012, axis="x")

# ---------------------------------------------------------------------------
# Build objects (boolean the cut shell)
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


cut_shell(SHELL, CUT, "LV_Shell")
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("LV_" + key, MATS[BUILDER_MAT[key]], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Lovell's Restaurant built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)",
      "| arch crown %.2f" % (azc + aR + 0.23))
# Materials, baked lighting and GLB export: run lovells_restaurant_bake.py (it runs this file first).
