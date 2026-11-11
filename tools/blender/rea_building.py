"""
rea_building.py - builds the Rea Building / "Clock Tower Building", the old Post Office block
(48-52 Main St, Flemington; 3-storey red-brick Italianate block of 1874 on the NE corner of
Main St and Bloomfield Ave, as it stood c. 1920) in Blender.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/rea_building.py").read())

Every run deletes and rebuilds the "ReaBuilding" collection. Materials, lightmap bake and GLB
export: rea_building_bake.py (runs this file first). Pattern: lovells_restaurant.py (builders
per UV kind, Wall frames, shallow boolean recesses) and bank_building.py (brick block, hoods,
cornice bands).

Sources: PLAN.md "Rea Building / Clock Tower Building" spec (1921 Sanborn sheet 2 footprint;
modern frontal photo for the upper floors and roofline; 1906-07 cards for the ground floor,
steps and awnings; 1908 cards for the Bloomfield side and the cupola). Owner decision
2026-11-04: landmark detail, <= 15k triangles.

Coordinates (metres, Blender Z-up):
    X  across the front, +X = south (Bloomfield Ave), -X = north (passage)
    Y  depth: y = 0 is the front wall face; steps run out to -1.20, awnings to -2.20,
       main-block rear 15.20, Flats wing rear 23.07
    Z  up from the sidewalk top; walls skirt down to -0.20; shop floors 0.60
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".

Eight materials: brick, trim, stone, dark, signs, WindowBack, ShopInterior (lightmapped, merged
into one draw call by the scene) and glass. Every builder below has one material plus a bake
tint (cupola cream, door varnish, iron); faces of the "Atlas" builder carry a face attribute
"rid" that tells the bake which atlas box they show.

Windows (PLAN.md "E. Windows that don't read as flat black", rolled out here 2026-11-11, same
method as the Bank Building and 40-46 Main): every pane is ONE outward glass face (builder
Glass -> material `glass`, transparent, see rea_building_bake.py) 4 cm in front of a window
back: ONE rectangular face (the pane's bounding box; its corners beyond an arched head sit
inside the solid wall, where nobody sees them). Builder WBack shows cells of the shared atlas
assets/textures/shared/window_backs.jpg (upper floors: blinds, lace, curtains, dark rooms, no
two alike side by side or above/below; plain dark rooms behind the cobbler's door, the stair
door, the fanlights, the oval window and the cupola windows); builder Shop shows cells of
assets/textures/shared/shop_interior.jpg behind the display windows, door lights and door
transoms of the two shops (48 drugs; 52 jeweler, the old post-office front: the same cells
mirrored). BACKREC[rid] tells the bake which atlas rectangle each back shows.
"""

import math
import json
import random
import bpy
import bmesh

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md)
# ---------------------------------------------------------------------------
HW = 7.97                  # half front (15.94 m)
DEPTH = 15.20              # main block
FX0, FY1 = -0.96, 23.07    # Flats wing: north face x, rear face y
CH_A, CH_B = (-0.96, 21.60), (0.34, 23.07)     # chamfered NE corner of the Flats
FL = 0.60                  # shop floors
SKIRT = -0.20
TOP = 10.75                # top of the wall shell (roof base)
RECESS = 0.30              # openings are shallow recesses this deep
CORN_IN = 0.35             # cornice bands reach this far into the wall (roof starts behind)
DECK = 11.95
CUP = (0.0, 7.60)          # cupola centre
CB = 1.65                  # cupola body half width (3.30)

UP_FLOORS = ((4.82, 6.57), (7.85, 9.40))       # (sill, crown) 2nd and 3rd floor
WIN_W = 0.90
RISE = 0.15

# ---------------------------------------------------------------------------
# Materials (plain stand-ins; rea_building_bake.py swaps in the textures)
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


COLOURS = {"Brick": "#8a4030", "Trim": "#b5ac98", "Stone": "#8e8c86", "Dark": "#4a4c50", "Signs": "#e2daca",
           "Glass": "#1a1916", "WBack": "#2a2420", "Shop": "#2a2420"}
MATS = {k: plain("RB_" + k, c) for k, c in COLOURS.items()}
# builder -> material (the bake gives every builder its own UVs and tint)
BUILDER_MAT = {"Brick": "Brick", "Trim": "Trim", "Cupola": "Trim", "Stone": "Stone",
               "Roof": "Dark", "Door": "Dark", "Iron": "Dark", "Atlas": "Signs",
               "Glass": "Glass", "WBack": "WBack", "Shop": "Shop"}

# ---------------------------------------------------------------------------
# Mesh builder
# ---------------------------------------------------------------------------


class Wall:
    """A vertical wall plane: p0 (x, y) on the face, n = unit outward normal, t = (-n.y, n.x)
    runs to the right as seen from outside (so lettering reads correctly). Wall coordinates:
    u along t, z up, d outward from the face."""

    def __init__(self, p0, n, cut=None):
        self.p0, self.n, self.cut = p0, n, cut
        self.t = (-n[1], n[0])

    def pt(self, u, z, d):
        return (self.p0[0] + self.t[0] * u + self.n[0] * d,
                self.p0[1] + self.t[1] * u + self.n[1] * d, z)

    def u_of(self, x, y):
        return (x - self.p0[0]) * self.t[0] + (y - self.p0[1]) * self.t[1]


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

    def oprism(self, wall, pts_dz, u0, u1):
        """Profile [(d, z), ...] across a wall, extruded along it from u0 to u1."""
        self._extrude([wall.pt(u0, z, d) for d, z in pts_dz], [wall.pt(u1, z, d) for d, z in pts_dz])

    def lathe(self, cx, cy, rings, sides=8, rot=0.5):
        """Vertical solid of revolution: rings [(radius, z), ...] bottom to top; a ring of
        radius 0 is a single apex vertex. sides=4 with rot=0.5 gives an axis-aligned square
        of half width r / sqrt(2)."""
        bm = self.bm
        loops = []
        for r, z in rings:
            if r < 1e-6:
                loops.append([bm.verts.new((cx, cy, z))])
            else:
                loops.append([bm.verts.new((cx + r * math.cos(2 * math.pi * (i + rot) / sides),
                                            cy + r * math.sin(2 * math.pi * (i + rot) / sides), z))
                              for i in range(sides)])
        faces = []
        if len(loops[0]) > 1:
            faces.append(bm.faces.new(list(reversed(loops[0]))))
        if len(loops[-1]) > 1:
            faces.append(bm.faces.new(loops[-1]))
        for a, b in zip(loops, loops[1:]):
            for i in range(sides):
                j = (i + 1) % sides
                if len(a) == 1:
                    faces.append(bm.faces.new([a[0], b[j], b[i]]))
                elif len(b) == 1:
                    faces.append(bm.faces.new([a[i], a[j], b[0]]))
                else:
                    faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
        self._closed(faces)

    def wring(self, wall, outer, inner, d0, d1):
        """Closed ring between two outlines with the same number of points (wall plane)."""
        bm = self.bm
        o0 = [bm.verts.new(wall.pt(u, z, d0)) for u, z in outer]
        o1 = [bm.verts.new(wall.pt(u, z, d1)) for u, z in outer]
        i0 = [bm.verts.new(wall.pt(u, z, d0)) for u, z in inner]
        i1 = [bm.verts.new(wall.pt(u, z, d1)) for u, z in inner]
        n = len(outer)
        faces = []
        for i in range(n):
            j = (i + 1) % n
            faces += [bm.faces.new([o1[i], o1[j], i1[j], i1[i]]), bm.faces.new([o0[i], i0[i], i0[j], o0[j]]),
                      bm.faces.new([o0[i], o0[j], o1[j], o1[i]]), bm.faces.new([i0[i], i1[i], i1[j], i0[j]])]
        self._closed(faces)

    def face(self, wall, pts, d):
        """ONE single-sided face (outline [(u, z), ...] on a wall plane, d out from the wall
        face), facing outward. Used for glass panes and window backs."""
        f = self.bm.faces.new([self.bm.verts.new(wall.pt(u, z, d)) for u, z in pts])
        f.normal_update()
        if f.normal.x * wall.n[0] + f.normal.y * wall.n[1] < 0:
            f.normal_flip()
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
    return zs + rise - R, R, math.asin(min(1.0, (chord / 2) / R))


def arc_pts(cu, zc, r, a0, a1, segs):
    return [(cu + r * math.cos(a0 + (a1 - a0) * i / segs), zc + r * math.sin(a0 + (a1 - a0) * i / segs))
            for i in range(segs + 1)]


def band(cu, zc, r_in, r_out, a0, a1, segs):
    """Outline of a curved band (annulus segment) between angles a0 and a1."""
    return arc_pts(cu, zc, r_out, a0, a1, segs) + arc_pts(cu, zc, r_in, a1, a0, segs)


def seg_outline(cu, w, z0, crown, rise, segs):
    zs = crown - rise
    zc, R, th = seg_geom(w, zs, rise)
    return [(cu - w / 2, z0), (cu + w / 2, z0)] + arc_pts(cu, zc, R, math.pi / 2 - th, math.pi / 2 + th, segs)


def round_outline(cu, w, z0, zs, segs):
    r = w / 2
    return [(cu - r, z0), (cu + r, z0)] + arc_pts(cu, zs, r, 0.0, math.pi, segs)


def ellipse(cu, cz, a, b, segs=16):
    return [(cu + a * math.cos(2 * math.pi * i / segs), cz + b * math.sin(2 * math.pi * i / segs)) for i in range(segs)]


def offset_line(poly, p):
    """Open polyline (x, y) along walls, outside on the right; offset outward by p (mitred)."""
    n = len(poly)
    norms = []
    for i in range(n - 1):
        dx, dy = poly[i + 1][0] - poly[i][0], poly[i + 1][1] - poly[i][1]
        L = math.hypot(dx, dy)
        norms.append((dy / L, -dx / L))
    out = []
    for i, (x, y) in enumerate(poly):
        if i == 0:
            nx, ny = norms[0]
            out.append((x + p * nx, y + p * ny))
        elif i == n - 1:
            nx, ny = norms[-1]
            out.append((x + p * nx, y + p * ny))
        else:
            a, b = norms[i - 1], norms[i]
            k = 1 + a[0] * b[0] + a[1] * b[1]
            out.append((x + p * (a[0] + b[0]) / k, y + p * (a[1] + b[1]) / k))
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


col = fresh_collection("ReaBuilding")
G = {k: MB() for k in BUILDER_MAT}
B, T, CP, ST, R, GL, DR, IR, AT, WB, SH = (G[k] for k in ("Brick", "Trim", "Cupola", "Stone", "Roof", "Glass", "Door",
                                                          "Iron", "Atlas", "WBack", "Shop"))
SHELL, CUT = MB(), MB()          # brick wall shell (main block + Flats) and its openings
STUC, CUT_S = MB(), MB()         # rusticated stucco face of the middle ground section
TYMP, CUT_T = MB(), MB()         # front tympanum (oval window)
CUPB, CUT_C = MB(), MB()         # cupola body (windows, sunk panels)

# Atlas records: rid -> dict (read by rea_building_bake.py)
ATLAS = {}


def atlas_rec(**kw):
    rid = len(ATLAS) + 1
    ATLAS[rid] = kw
    AT.rid = rid
    return rid


def wall_rec(w):
    return (w.p0, w.n)


class MultiCut:
    """Cutter that adds the same solid to several cut sets."""

    def __init__(self, *cuts):
        self.cuts = cuts

    def wprism(self, wall, pts, d0, d1):
        for c in self.cuts:
            c.wprism(wall, pts, d0, d1)

    def wbox(self, wall, u0, u1, z0, z1, d0, d1):
        for c in self.cuts:
            c.wbox(wall, u0, u1, z0, z1, d0, d1)


FRONT = Wall((0.0, 0.0), (0, -1), CUT)
SOUTH = Wall((HW, 0.0), (1, 0), CUT)                 # u = y
NORTH = Wall((-HW, 0.0), (-1, 0), CUT)               # u = -y
REAR = Wall((0.0, DEPTH), (0, 1), CUT)               # u = -x  (main block rear, x -7.97 ... -0.96)
FL_E = Wall((0.0, FY1), (0, 1), CUT)                 # u = -x  (Flats rear)
FL_N = Wall((FX0, 0.0), (-1, 0), CUT)                # u = -y  (Flats yard face)
STUC_W = Wall((0.0, -0.05), (0, -1), MultiCut(CUT, CUT_S))   # front of the stucco face

# Wall planes ((x, y), normal) used by the bake to cut / weight faces
WALL_PLANES = [(w.p0, w.n) for w in (FRONT, SOUTH, NORTH, REAR, FL_E, FL_N)]

# ---------------------------------------------------------------------------
# Shell: one closed prism on the plan (main block + Flats), skirt to the roof base
# ---------------------------------------------------------------------------
PLAN = [(-HW, 0.0), (HW, 0.0), (HW, FY1), CH_B, CH_A, (FX0, DEPTH), (-HW, DEPTH)]
SHELL.prism(PLAN, SKIRT, TOP, axis="z")

# ---------------------------------------------------------------------------
# Glass panes and window backs (PLAN.md section E)
# ---------------------------------------------------------------------------
WB_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\window_backs.json"))["cells"]
SHOP_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\shop_interior.json"))["cells"]
GAP = 0.04                      # window back this far behind the glass
# upper floors of the main block (offices, club rooms, rooms): blinds, lace, dark rooms
UPPER = {"blind_cream_high": 3, "blind_cream_half": 3, "blind_cream_low": 2, "blind_green_high": 2,
         "blind_green_half": 2, "blind_green_low": 1, "lace": 2, "lace_blind_cream": 2,
         "dark_room": 2, "dark_room_frame": 2, "curtains_beige": 1}
# the Flats (dwellings)
ROOMS = {"lace": 2, "lace_blind_cream": 2, "lace_blind_green": 2, "lace_full_blind_cream": 1,
         "curtains_beige": 2, "curtains_olive": 1, "curtains_maroon_blind": 1, "blind_cream_half": 2,
         "blind_green_half": 1, "dark_room": 1}
# north (passage), rear and yard walls
BACKSIDE = {"blind_cream_high": 2, "blind_cream_half": 2, "blind_green_half": 1, "blind_green_low": 1,
            "dark_room": 3, "dark_room_frame": 3}
# ground-floor side windows of the 52 shop room (Bloomfield Ave): plain dim rooms, a blind or two
SIDE_GROUND = {"dark_room": 3, "dark_room_frame": 3, "blind_cream_high": 2, "blind_green_high": 2}
_wb_rng = random.Random(1874)
_wb_grid = {}
BACKREC = {}                    # rid -> record (read by rea_building_bake.py)


def pick(weights, wall, row, colm):
    """A cell for the window at (row, column) of a wall that differs from its neighbours."""
    g = _wb_grid.setdefault(wall, {})
    avoid = {g.get((row, colm - 1)), g.get((row, colm + 1)), g.get((row - 1, colm)), g.get((row + 1, colm))}
    names = [n for n in weights if n not in avoid]
    cell = _wb_rng.choices(names, weights=[weights[n] for n in names])[0]
    g[(row, colm)] = cell
    return cell


def back(wall, u0, u1, z0, z1, d, cell, crop=None, mirror=False):
    """Window back: one rectangle on the wall plane at depth d (negative = into the wall)
    showing an atlas cell; crop = (fu0, fu1, fv0, fv1) part of the cell (v up), mirror = flipped
    left to right."""
    shop = cell in SHOP_CELLS
    mb = SH if shop else WB
    U0, V0, U1, V1 = (SHOP_CELLS if shop else WB_CELLS)[cell]["uv"]
    if crop:
        U0, U1, V0, V1 = (U0 + (U1 - U0) * crop[0], U0 + (U1 - U0) * crop[1],
                          V0 + (V1 - V0) * crop[2], V0 + (V1 - V0) * crop[3])
    if mirror:
        U0, U1 = U1, U0
    rid = len(BACKREC) + 1
    BACKREC[rid] = dict(wall=(wall.p0, wall.n), u0=u0, u1=u1, z0=z0, z1=z1, uv=(U0, V0, U1, V1))
    mb.rid = rid
    mb.face(wall, rect(u0, u1, z0, z1), d)
    mb.rid = 0


def pane(wall, outline, d_glass, cell, grow=0.0, crop=None, mirror=False):
    """Glass face (the pane's outline) at depth d_glass and its window back GAP behind it: the
    outline's bounding box, `grow` larger all round where sash or stiles hide its edge."""
    GL.face(wall, outline, d_glass)
    us, zs = [p[0] for p in outline], [p[1] for p in outline]
    back(wall, min(us) - grow, max(us) + grow, min(zs) - grow, max(zs) + grow, d_glass - GAP, cell, crop, mirror)


# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------


def shutters(wall, cu, half, z0, z1, leaf=0.45, gap=0.02):
    """Open louvred shutters flat beside an opening, 0.03 off the wall (atlas louvres)."""
    for sgn in (-1, 1):
        u0, u1 = sorted((cu + sgn * (half + gap), cu + sgn * (half + gap + leaf)))
        atlas_rec(region="louvre", mode="rect", wall=wall_rec(wall), u0=u0, u1=u1, z0=z0, z1=z1)
        AT.wbox(wall, u0, u1, z0, z1, 0.03, 0.065)


def seg_window(wall, cu, z0, crown, w=WIN_W, full=True, keystone=True, shut=0.45, segs=6, cell="dark_room"):
    """Segmental-headed 2/2 window in a 0.30 recess: glass with a window back, trim frame set 0.12 in,
    sash rails and muntin, raised brick hood 0.14 wide / 0.05 proud, pale keystone, stone
    sill 0.06 proud, optional open louvred shutters (leaf width `shut`, 0 = none).
    full=False: plainer side/rear window (no frame band, fewer parts)."""
    h = w / 2
    zs = crown - RISE
    zc, Rr, th = seg_geom(w, zs, RISE)
    outline = seg_outline(cu, w, z0, crown, RISE, segs)
    wall.cut.wprism(wall, outline, -RECESS, 0.25)
    pane(wall, outline, -0.21, cell)                                          # glass + window back
    zm = (z0 + zs) / 2 + 0.05
    if full:
        f = 0.06
        for a, b in ((cu - h, cu - h + f), (cu + h - f, cu + h)):            # frame jambs
            T.wbox(wall, a, b, z0, zs + 0.02, -0.21, -0.12)
        T.wprism(wall, band(cu, zc, Rr - f, Rr, math.pi / 2 - th, math.pi / 2 + th, segs), -0.21, -0.12)   # head
        T.wbox(wall, cu - h + f, cu + h - f, z0, z0 + 0.08, -0.21, -0.13)    # bottom rail
        T.wbox(wall, cu - h + f, cu + h - f, zm - 0.03, zm + 0.03, -0.21, -0.15)   # meeting rail
        T.wbox(wall, cu - 0.018, cu + 0.018, z0 + 0.08, zc + Rr - f, -0.21, -0.17)  # muntin
    else:
        T.wbox(wall, cu - h, cu + h, zm - 0.03, zm + 0.03, -0.21, -0.15)     # meeting rail
        T.wbox(wall, cu - 0.018, cu + 0.018, z0, zc + Rr, -0.21, -0.17)      # muntin
    # raised brick hood: band from just above the opening to 0.15 over it, ends past the jambs
    r0, r1 = Rr + 0.01, Rr + 0.15
    th2 = math.asin(min(0.99, (h + 0.10) / r1))
    B.wprism(wall, band(cu, zc, r0, r1, math.pi / 2 - th2, math.pi / 2 + th2, segs), -0.05, 0.05)
    if keystone:
        top = zc + r1 + 0.11
        T.wprism(wall, [(cu - 0.075, zc + Rr - 0.02), (cu + 0.075, zc + Rr - 0.02),
                        (cu + 0.09, top), (cu - 0.09, top)], -0.05, 0.08)
    # stone sill 1.15 x 0.10, 0.06 proud
    T.wbox(wall, cu - 0.575, cu + 0.575, z0 - 0.10, z0, -0.21, 0.06)
    if shut:
        shutters(wall, cu, h, z0, zs + 0.05, leaf=shut)


def leaf_widths(centres, edges, w=WIN_W):
    """Shutter leaf width per window: 0.45, narrower where the pier to a neighbour is short."""
    out = []
    for i, c in enumerate(centres):
        left = (c - centres[i - 1] - w) / 2 if i > 0 else c - edges[0] - w / 2 - 0.25
        right = (centres[i + 1] - c - w) / 2 if i < len(centres) - 1 else edges[1] - c - w / 2 - 0.25
        out.append(max(0.0, min(0.45, min(left, right) - 0.04)))
    return out


# Front upper floors: 7 bays (2-3-2), shuttered
FRONT_X = (-6.13, -3.84, -1.56, 0.0, 1.56, 3.84, 6.13)
FRONT_LEAF = leaf_widths(FRONT_X, (-HW, HW))
for k, (x, lw) in enumerate(zip(FRONT_X, FRONT_LEAF)):
    for row, (sill, crown) in enumerate(UP_FLOORS, 1):
        seg_window(FRONT, x, sill, crown, shut=lw, cell=pick(UPPER, "front", row, k))

# Bloomfield (south) side, main block: 4 bays, upper floors as the front, tall ground windows
SOUTH_Y = (2.30, 6.60, 8.56, 12.86)
SOUTH_LEAF = leaf_widths(SOUTH_Y, (0.0, DEPTH))
for k, (y, lw) in enumerate(zip(SOUTH_Y, SOUTH_LEAF)):
    for row, (sill, crown) in enumerate(UP_FLOORS, 1):
        seg_window(SOUTH, y, sill, crown, shut=lw, cell=pick(UPPER, "south", row, k))
    seg_window(SOUTH, y, 1.20, 3.60, w=0.95, shut=min(lw, 0.47), cell=pick(SIDE_GROUND, "south", 0, k))

# Flats, Bloomfield face: 2 bays all floors (no shutters, no keystones), door with a step
for k, y in enumerate((16.60, 19.70), 4):
    for row, (sill, crown) in enumerate(UP_FLOORS, 1):
        seg_window(SOUTH, y, sill, crown, full=False, keystone=False, shut=0, cell=pick(ROOMS, "south", row, k))
    seg_window(SOUTH, y, 1.20, 3.20, full=False, keystone=False, shut=0, cell=pick(ROOMS, "south", 0, k))
# Flats rear (east) face and yard (north) face: 2 windows per floor
FLOORS_PLAIN = ((1.20, 3.20),) + UP_FLOORS
for k, x in enumerate((2.25, 6.00)):
    for row, (sill, crown) in enumerate(FLOORS_PLAIN):
        seg_window(FL_E, -x, sill, crown, full=False, keystone=False, shut=0, segs=4, cell=pick(ROOMS, "fl_e", row, k))
for k, y in enumerate((16.60, 19.60)):
    for row, (sill, crown) in enumerate(FLOORS_PLAIN):
        seg_window(FL_N, -y, sill, crown, full=False, keystone=False, shut=0, segs=4, cell=pick(ROOMS, "fl_n", row, k))
# North (passage) wall: 3 upper windows per floor, 2 small high ground windows
for k, y in enumerate((3.0, 7.6, 12.2)):
    for row, (sill, crown) in enumerate(UP_FLOORS, 1):
        seg_window(NORTH, -y, sill, crown, full=False, shut=0, segs=4, cell=pick(BACKSIDE, "north", row, k))
for y, cell in ((5.0, "dark_room_frame"), (10.0, "dark_room")):
    seg_window(NORTH, -y, 2.00, 3.00, full=False, keystone=False, shut=0, segs=4, cell=cell)
# Main-block rear wall above the yard: 2 windows per floor
for k, x in enumerate((-5.80, -3.10)):
    for row, (sill, crown) in enumerate(FLOORS_PLAIN):
        seg_window(REAR, -x, sill, crown, full=False, keystone=False, shut=0, segs=4, cell=pick(BACKSIDE, "rear", row, k))

# Flats door (Bloomfield face, y 21.80): 4-panel varnished door, transom, hood, one stone step
DY = 21.80
SOUTH.cut.wprism(SOUTH, seg_outline(DY, 0.95, 0.20, 2.80, RISE, 4), -RECESS, 0.25)
DR.wbox(SOUTH, DY - 0.475, DY + 0.475, 0.20, 2.30, -0.20, -0.16)
for ua, ub in ((DY - 0.38, DY - 0.04), (DY + 0.04, DY + 0.38)):
    for za, zb in ((0.35, 1.05), (1.20, 2.15)):
        DR.wbox(SOUTH, ua, ub, za, zb, -0.16, -0.145)
T.wbox(SOUTH, DY - 0.475, DY + 0.475, 2.30, 2.38, -0.20, -0.14)                # transom bar
pane(SOUTH, seg_outline(DY, 0.95, 2.38, 2.80, RISE, 4), -0.20, "dark_room", crop=(0, 1, 0.60, 0.85))   # transom light
zc_d, R_d, _ = seg_geom(0.95, 2.80 - RISE, RISE)
B.wprism(SOUTH, band(DY, zc_d, R_d + 0.01, R_d + 0.15, math.pi / 2 - 0.75, math.pi / 2 + 0.75, 4), -0.05, 0.05)
ST.box(HW - 0.01, HW + 0.40, DY - 0.70, DY + 0.70, SKIRT, 0.20)                 # step

# ---------------------------------------------------------------------------
# Ground storey front: shop fronts (48, 52) and the rusticated middle section (50 + stair)
# ---------------------------------------------------------------------------
SIGN0, SIGN1 = 3.40, 3.95          # sign band
SF_Y = 0.14                        # shop-front glass plane (behind the wall face)


def display_window(x0, x1, cell, crop=None, mirror=False):
    """Panelled bulkhead 0.60-1.10, glass 1.10 -> segmental head 3.35 in a trim frame; the shop
    behind the glass on a window back (hidden at its edges by the posts and the spandrel)."""
    T.box(x0, x1, 0.02, SF_Y, FL, 1.10)                                       # bulkhead
    T.box(x0 + 0.10, x1 - 0.10, 0.0, 0.02, FL + 0.10, 1.00)                   # raised panel
    T.box(x0 - 0.02, x1 + 0.02, -0.02, SF_Y, 1.06, 1.12)                       # sill rail
    pane(FRONT, rect(x0, x1, 1.10, SIGN0), -SF_Y, cell, crop=crop, mirror=mirror)   # glass, the shop behind
    for a, b in ((x0, x0 + 0.08), (x1 - 0.08, x1)):
        T.box(a, b, 0.0, SF_Y, 1.10, 3.20)                                    # frame posts
    zc, Rr, th = seg_geom(x1 - x0 - 0.16, 3.15, 0.20)
    cu = (x0 + x1) / 2
    # the arc runs left to right (angles pi/2+th -> pi/2-th) from (x0+0.08, 3.15) to (x1-0.08, 3.15)
    spandrel = [(x0, 3.15)] + arc_pts(cu, zc, Rr, math.pi / 2 + th, math.pi / 2 - th, 8) + \
        [(x1, 3.15), (x1, SIGN0), (x0, SIGN0)]
    T.prism(spandrel, 0.02, SF_Y, axis="y")
    T.prism(band(cu, zc, Rr, Rr + 0.04, math.pi / 2 - th, math.pi / 2 + th, 8), 0.0, 0.02, axis="y")  # bead


def door_leaf(x0, x1, z0, z1, yf, glass_from, cell, crop=None, mirror=False):
    """Glazed door leaf, front face at yf: stiles and rails 0.10, raised lower panel, glass
    (one face 0.03 into the leaf, the room seen through it on a window back behind the leaf)."""
    yb = yf + 0.05
    DR.box(x0, x0 + 0.10, yf, yb, z0, z1)
    DR.box(x1 - 0.10, x1, yf, yb, z0, z1)
    DR.box(x0 + 0.10, x1 - 0.10, yf, yb, z0, z0 + 0.22)
    DR.box(x0 + 0.10, x1 - 0.10, yf, yb, glass_from - 0.12, glass_from)
    DR.box(x0 + 0.10, x1 - 0.10, yf, yb, z1 - 0.12, z1)
    DR.box(x0 + 0.10, x1 - 0.10, yf + 0.02, yb, z0 + 0.22, glass_from - 0.12)
    DR.box(x0 + 0.16, x1 - 0.16, yf + 0.005, yf + 0.02, z0 + 0.30, glass_from - 0.20)
    pane(FRONT, rect(x0 + 0.10, x1 - 0.10, glass_from, z1 - 0.12), -(yf + 0.03), cell, grow=0.09,
         crop=crop, mirror=mirror)


# shop_interior.jpg cells per pane; shop_a is cropped to the display window's proportions.
# 52 shows the same room mirrored.
SHOP_A_CROP = (0.0, 0.70, 0.0, 1.0)


def shop(x0, x1, sign=None, mirror=False):
    xc = (x0 + x1) / 2
    CUT.box(x0, x1, -0.25, SF_Y + GAP + 0.02, FL, SIGN1)                      # shop-front opening
    e0, e1 = xc - 0.75, xc + 0.75
    CUT.box(e0, e1, -0.25, 0.95, FL - 0.15, SIGN0)                           # entrance recess
    ST.box(e0, e1, -0.01, 0.90, FL - 0.15, FL)                               # recess floor (stone)
    disp = [("shop_a", SHOP_A_CROP), ("shop_b", None)]
    doors = ["door_l", "door_r"]
    if mirror:
        disp.reverse()
        doors.reverse()
    display_window(x0, e0, disp[0][0], disp[0][1], mirror)
    display_window(e1, x1, disp[1][0], disp[1][1], mirror)
    for xa, xb in ((e0, e0 + 0.03), (e1 - 0.03, e1)):                         # panelled reveals
        T.box(xa, xb, SF_Y, 0.90, FL, SIGN0)
    T.box(e0, e1, 0.0, 0.90, SIGN0 - 0.03, SIGN0)                             # recess ceiling board
    # glazed double doors 2 x 0.70 x 2.40 at the back, transom 3.05-3.30
    T.box(e0, e1, 0.84, 0.90, 3.00, 3.05)                                     # transom bar
    T.box(e0, e0 + 0.05, 0.84, 0.90, FL, SIGN0)
    T.box(e1 - 0.05, e1, 0.84, 0.90, FL, SIGN0)
    pane(FRONT, rect(e0 + 0.05, e1 - 0.05, 3.05, 3.30), -0.87, "transom_door", mirror=mirror)   # transom light
    T.box(e0, e1, 0.84, 0.90, 3.30, SIGN0)
    T.box(xc - 0.015, xc + 0.015, 0.85, 0.87, 3.05, 3.30)
    door_leaf(xc - 0.70, xc - 0.005, FL, 3.00, 0.80, 1.40, doors[0], mirror=mirror)
    door_leaf(xc + 0.005, xc + 0.70, FL, 3.00, 0.80, 1.40, doors[1], mirror=mirror)
    # sign band and its mouldings
    T.box(x0, x1, -0.02, SF_Y, SIGN0, SIGN1)
    T.box(x0, x1, -0.05, 0.0, SIGN0, SIGN0 + 0.05)
    T.box(x0, x1, -0.05, 0.0, SIGN1 - 0.04, SIGN1)
    if sign:
        atlas_rec(region=sign, mode="rect", wall=wall_rec(FRONT), u0=xc - 1.40, u1=xc + 1.40, z0=3.48, z1=3.88)
        AT.box(xc - 1.40, xc + 1.40, -0.045, -0.02, 3.48, 3.88)


shop(-7.62, -2.60)
shop(2.60, 7.62, sign="jeweler", mirror=True)        # the old post-office front

# Pilasters 0.35 wide, 0.06 proud, panelled shafts, console caps 3.80-3.95
for xc in (-7.795, -2.425, 2.425, 7.795):
    x0, x1 = xc - 0.175, xc + 0.175
    T.box(x0, x1, -0.06, 0.0, FL, SIGN1)
    T.box(x0 + 0.06, x1 - 0.06, -0.075, -0.06, FL + 0.25, 3.60)               # raised panel
    T.box(x0 - 0.02, x1 + 0.02, -0.08, 0.0, FL, FL + 0.18)                     # base
    T.prism([(-0.06, 3.70), (-0.10, 3.80), (-0.14, 3.86), (-0.14, SIGN1), (0.0, SIGN1), (0.0, 3.70)],
            x0 - 0.02, x1 + 0.02, axis="x")                                    # console cap
SOUTH_CORNER = Wall((HW, 0.0), (1, 0))
T.wbox(SOUTH_CORNER, 0.0, 0.35, FL, SIGN1, -0.01, 0.06)                        # corner pilaster return

# Middle section X -2.25 ... +2.25: pale rusticated stucco face, three round arches
MX = 2.25
ARCH_X = (-1.45, 0.0, 1.45)
ARCH_R, ARCH_SPR = 0.50, 2.90
STUC.box(-MX, MX, -0.05, 0.0, FL, SIGN1)
for i, ax in enumerate(ARCH_X):
    z0 = 1.20 if i == 1 else FL - 0.15
    STUC_W.cut.wprism(STUC_W, round_outline(ax, 1.0, z0, ARCH_SPR, 8), -RECESS - 0.05, 0.30)
    T.wring(FRONT, round_outline(ax, 1.0, z0, ARCH_SPR, 8), round_outline(ax, 0.96, z0 + 0.02, ARCH_SPR, 8),
            -RECESS - 0.02, 0.0)                                                # stucco reveal lining
# rusticated courses 0.34 tall, 0.02 proud, 0.06 channels; stop at the archivolts
for k in range(8):
    za, zb = FL + 0.06 + 0.40 * k, FL + 0.40 + 0.40 * k
    zb = min(zb, SIGN1 - 0.10)
    if zb - za < 0.08:
        continue
    holes = []
    for ax in ARCH_X:
        r = 0.66
        if ax == ARCH_X[1] and zb <= 1.12:
            hw = 0.0                                  # under the middle (window) arch's sill
        elif zb <= ARCH_SPR:
            hw = r
        elif za >= ARCH_SPR + r:
            hw = 0.0
        else:
            hw = math.sqrt(max(0.0, r * r - max(0.0, za - ARCH_SPR) ** 2))
        if hw > 0:
            holes.append((ax - hw, ax + hw))
    for x0, x1 in spans(-MX, MX, holes):
        T.box(x0, x1, -0.07, -0.05, za, zb)
for ax in ARCH_X:
    T.prism(band(ax, ARCH_SPR, ARCH_R, ARCH_R + 0.15, 0.0, math.pi, 8), -0.08, -0.05, axis="y")   # archivolt
    T.box(ax - ARCH_R - 0.15, ax - ARCH_R, -0.08, -0.05, FL + 0.15, ARCH_SPR)     # jamb strips
    T.box(ax + ARCH_R, ax + ARCH_R + 0.15, -0.08, -0.05, FL + 0.15, ARCH_SPR)
    T.box(ax - ARCH_R - 0.18, ax - ARCH_R + 0.0, -0.10, -0.05, ARCH_SPR - 0.10, ARCH_SPR)   # impost
    T.box(ax + ARCH_R, ax + ARCH_R + 0.18, -0.10, -0.05, ARCH_SPR - 0.10, ARCH_SPR)
    top = ARCH_SPR + ARCH_R + 0.22
    if ax != ARCH_X[0]:                                       # keystone (north one under the board)
        T.prism([(ax - 0.07, ARCH_SPR + ARCH_R - 0.02), (ax + 0.07, ARCH_SPR + ARCH_R - 0.02),
                 (ax + 0.09, top), (ax - 0.09, top)], -0.11, -0.05, axis="y")
T.box(-MX, MX, -0.08, -0.05, FL, FL + 0.08)                                    # base fillet


def fanlight(ax, yb, cell):
    """Half-round fanlight glass with radial bars, a sill bar at the springing; a plain dark
    room behind it."""
    pane(FRONT, arc_pts(ax, ARCH_SPR, 0.45, 0.0, math.pi, 8), -yb, cell, crop=(0, 1, 0.60, 0.80))
    for a in (math.pi / 4, math.pi / 2, 3 * math.pi / 4):
        ca, sa = math.cos(a), math.sin(a)
        nx, nz = -sa * 0.015, ca * 0.015
        x1, z1 = ax + 0.45 * ca, ARCH_SPR + 0.45 * sa
        T.prism([(ax + nx, ARCH_SPR + nz), (ax - nx, ARCH_SPR - nz), (x1 - nx, z1 - nz), (x1 + nx, z1 + nz)],
                yb - 0.03, yb, axis="y")
    T.box(ax - 0.50, ax + 0.50, yb - 0.04, yb + 0.02, ARCH_SPR - 0.06, ARCH_SPR)


DOOR_Y = 0.20                      # door / window plane in the arches (y)
# north arch: glazed door (cobbler, 50) + fanlight
ax = ARCH_X[0]
ST.box(ax - 0.50, ax + 0.50, -0.06, DOOR_Y + 0.05, FL - 0.15, FL)
door_leaf(ax - 0.45, ax + 0.45, FL, ARCH_SPR - 0.06, DOOR_Y, 1.35, "dark_room_frame")   # plain dim room
fanlight(ax, DOOR_Y + 0.04, "dark_room")
# middle arch: window, sill 1.20, 2/2 sash, arched top sash
ax = ARCH_X[1]
pane(FRONT, round_outline(ax, 1.0, 1.20, ARCH_SPR, 8), -(DOOR_Y + 0.02), "blind_cream_high")
T.box(ax - 0.62, ax + 0.62, -0.12, DOOR_Y, 1.12, 1.20)                          # sill
for a, b in ((ax - 0.50, ax - 0.44), (ax + 0.44, ax + 0.50)):
    T.box(a, b, DOOR_Y - 0.05, DOOR_Y + 0.02, 1.20, ARCH_SPR)
T.prism(band(ax, ARCH_SPR, 0.44, 0.50, 0.0, math.pi, 8), DOOR_Y - 0.05, DOOR_Y + 0.02, axis="y")
for za, zb in ((1.20, 1.28), (2.02, 2.08), (ARCH_SPR - 0.04, ARCH_SPR + 0.02)):
    T.box(ax - 0.44, ax + 0.44, DOOR_Y - 0.04, DOOR_Y + 0.02, za, zb)
T.box(ax - 0.018, ax + 0.018, DOOR_Y - 0.02, DOOR_Y + 0.02, 1.28, ARCH_SPR + 0.44)
# south arch: panelled stair-hall door with glazed upper panels + fanlight
ax = ARCH_X[2]
ST.box(ax - 0.50, ax + 0.50, -0.06, DOOR_Y + 0.05, FL - 0.15, FL)
GZ_TOP = ARCH_SPR - 0.20
DR.box(ax - 0.45, ax + 0.45, DOOR_Y, DOOR_Y + 0.05, FL, 1.55)                   # lower half (solid)
DR.box(ax - 0.45, ax + 0.45, DOOR_Y, DOOR_Y + 0.05, GZ_TOP, ARCH_SPR - 0.06)    # top rail
for ua, ub in ((ax - 0.45, ax - 0.37), (ax - 0.04, ax + 0.04), (ax + 0.37, ax + 0.45)):
    DR.box(ua, ub, DOOR_Y, DOOR_Y + 0.05, 1.55, GZ_TOP)                         # stiles round the two lights
for ua, ub in ((ax - 0.37, ax - 0.04), (ax + 0.04, ax + 0.37)):
    DR.box(ua, ub, DOOR_Y - 0.015, DOOR_Y, FL + 0.15, 1.40)                     # raised lower panels
    GL.face(FRONT, rect(ua, ub, 1.55, GZ_TOP), -(DOOR_Y + 0.015))               # glazed upper panels
# one window back behind both lights: the dark stair hall
back(FRONT, ax - 0.43, ax + 0.43, 1.49, GZ_TOP + 0.06, -(DOOR_Y + 0.015 + GAP), "dark_room", crop=(0, 1, 0.20, 0.80))
fanlight(ax, DOOR_Y + 0.04, "dark_room_frame")
# "SHOES REPAIRED" board over the north arch
atlas_rec(region="shoes", mode="rect", wall=wall_rec(FRONT), u0=ARCH_X[0] - 0.55, u1=ARCH_X[0] + 0.55, z0=3.60, z1=3.90)
AT.box(ARCH_X[0] - 0.55, ARCH_X[0] + 0.55, -0.12, -0.08, 3.60, 3.90)

# Shop entablature, full front + 0.35 return on the Bloomfield side: architrave, frieze, cornice
SE_LINE = [(-HW, 0.0), (HW, 0.0), (HW, 0.35)]


def plan_band(line, p, z0, z1, mb, p_in=0.0):
    """Band along an open wall polyline: outer edge offset p, inner edge p_in (negative = into the wall)."""
    outer = offset_line(line, p)
    inner = offset_line(line, p_in)
    mb.prism(outer + inner[::-1], z0, z1, axis="z")


for p, z0, z1 in ((0.08, 3.95, 4.10), (0.06, 4.10, 4.45), (0.16, 4.45, 4.53), (0.30, 4.53, 4.64), (0.26, 4.64, 4.70)):
    plan_band(SE_LINE, p, z0, z1, T)
for xc in (-7.795, -2.425, 2.425, 7.795):                                       # consoles over the pilasters
    T.prism([(0.0, 4.10), (-0.06, 4.10), (-0.10, 4.20), (-0.15, 4.38), (-0.15, 4.45), (0.0, 4.45)],
            xc - 0.12, xc + 0.12, axis="x")

# ---------------------------------------------------------------------------
# Main entablature: moulded band, dentil course, bracketed cornice (all round except the two
# pediments), front and side pediments
# ---------------------------------------------------------------------------
PED_F = 2.20                       # front cornice stops at X +-2.20
PED_S = (7.60 - 1.75, 7.60 + 1.75)    # side cornice gap (y)
LINE_A = [(PED_F, 0.0), (HW, 0.0), (HW, PED_S[0])]
LINE_B = [(HW, PED_S[1]), (HW, FY1), CH_B, CH_A, (FX0, DEPTH), (-HW, DEPTH), (-HW, 0.0), (-PED_F, 0.0)]
CORNICE = ((0.78, 10.55, 10.62), (0.78, 10.62, 10.84), (0.84, 10.84, 10.90), (0.86, 10.90, 10.95), (0.80, 10.95, 11.00))
for line in (LINE_A, LINE_B):
    plan_band(line, 0.06, 10.32, 10.40, T)                                      # moulded band
    for p, z0, z1 in CORNICE:
        plan_band(line, p, z0, z1, T, p_in=-CORN_IN)


def dentil_course(line, z0=10.40, z1=10.55, d=0.04, piece=1.2):
    """Dentil band 0.04 proud, cut into ~1.2 m pieces, each showing one atlas dentil strip."""
    for i in range(len(line) - 1):
        (xa, ya), (xb, yb) = line[i], line[i + 1]
        L = math.hypot(xb - xa, yb - ya)
        n = (yb - ya) / L, -(xb - xa) / L
        w = Wall((xa, ya), n)
        ua, ub = w.u_of(xa, ya), w.u_of(xb, yb)
        lo, hi = min(ua, ub), max(ua, ub)
        k = max(1, round((hi - lo) / piece))
        for j in range(k):
            u0, u1 = lo + (hi - lo) * j / k, lo + (hi - lo) * (j + 1) / k
            if j == 0:
                u0 -= d
            if j == k - 1:
                u1 += d
            atlas_rec(region="dentil", mode="rect", wall=wall_rec(w), u0=u0, u1=u1, z0=z0, z1=z1)
            AT.wbox(w, u0, u1, z0, z1, 0.0, d)


dentil_course(LINE_A)
dentil_course(LINE_B)

# Scroll brackets (0.80 tall, 0.75 deep, 0.20 wide) with drop pendants
BRACKET = [(0.0, 10.55), (0.75, 10.55), (0.75, 10.45), (0.62, 10.37), (0.47, 10.33), (0.32, 10.22),
           (0.22, 10.06), (0.17, 9.90), (0.12, 9.75), (0.0, 9.75)]


def bracket(wall, u):
    T.oprism(wall, BRACKET, u - 0.10, u + 0.10)
    T.wbox(wall, u - 0.06, u + 0.06, 10.27, 10.40, 0.60, 0.72)                  # drop pendant
    T.wbox(wall, u - 0.08, u + 0.08, 9.70, 9.76, 0.0, 0.15)                     # foot block


for xc in (-7.60, -2.35, 2.35, 7.60):
    for s in (-0.125, 0.125):
        bracket(FRONT, xc + s)
for y in (0.37, 5.10, 10.10):
    for s in (-0.125, 0.125):
        bracket(SOUTH, y + s)
for y in (13.60, 16.00, 18.40, 20.80, 22.75):
    bracket(SOUTH, y)
for s in (-0.125, 0.125):
    bracket(NORTH, -(0.37 + s))


def pediment(wall, half, crown, depth, oval=False, segs=20):
    """Segmental arched pediment springing at 11.00 on the cornice ends: dentil strip on the
    inner edge, fascia, crown roll, tin coping; brick tympanum; tin barrel roof behind."""
    r_out = (half ** 2 + (crown - 11.0) ** 2) / (2 * (crown - 11.0))
    zc = crown - r_out
    r_in = r_out - 0.30
    a = math.asin((11.0 - zc) / r_out)
    # dentil strip, one atlas strip per 3 segments
    da = (math.pi - 2 * a) / segs
    for k in range(segs):
        a0, a1 = a + k * da, a + (k + 1) * da
        f0 = (k % 3) / 3
        atlas_rec(region="dentil", mode="arc", wall=wall_rec(wall), cu=0.0, zc=zc, a0=a0, a1=a1,
                  r0=r_in - 0.15, r1=r_in, f0=f0, f1=f0 + 1 / 3)
        AT.wprism(wall, band(0.0, zc, r_in - 0.15, r_in, a0, a1, 1), -0.30, 0.05)
    AT.rid = 0
    T.wprism(wall, band(0.0, zc, r_in, r_in + 0.18, a, math.pi - a, segs), -0.30, 0.20)        # fascia
    T.wprism(wall, band(0.0, zc, r_in + 0.18, r_out, a, math.pi - a, segs), -0.30, 0.25)       # crown roll
    R.wprism(wall, band(0.0, zc, r_out, r_out + 0.03, a, math.pi - a, segs), -0.32, 0.27)      # coping
    # tympanum: brick, from the roof base up under the dentil strip
    ri = r_in - 0.10
    a_t = math.asin(min(1.0, (11.0 - 0.02 - zc) / ri))
    xt = ri * math.cos(a_t)
    tymp = [(-PED_W, TOP), (PED_W, TOP), (PED_W, 10.98)] + \
        arc_pts(0.0, zc, ri, a_t, math.pi - a_t, segs) + [(-PED_W, 10.98)]
    (TYMP if oval else B).wprism(wall, tymp, -0.32, 0.0)
    # barrel roof behind, same profile
    rb = r_out - 0.04
    ab = math.asin((TOP - zc) / rb)
    R.wprism(wall, arc_pts(0.0, zc, rb, ab, math.pi - ab, segs), -0.28, -0.28 - depth)
    return zc, r_out


PED_W = PED_F
zc_f, r_f = pediment(FRONT, 3.00, 12.10, 1.50, oval=True)
SIDE_PED = Wall((HW, 7.60), (1, 0))
PED_W = 7.60 - PED_S[0]
zc_s, r_s = pediment(SIDE_PED, 2.50, 11.95, 1.20, segs=16)

# Oval window in the front tympanum: 0.82 x 0.90, dark glass 0.10 in, stone surround, 4 keystones
OV = (0.0, 10.45, 0.41, 0.45)
TYMP_W = Wall((0.0, 0.0), (0, -1), MultiCut(CUT, CUT_T))
TYMP_W.cut.wprism(TYMP_W, ellipse(0.0, OV[1], OV[2], OV[3]), -0.16, 0.25)
pane(FRONT, ellipse(0.0, OV[1], OV[2], OV[3]), -0.10, "dark_room_frame", crop=(0, 1, 0.30, 0.74))   # attic
T.wring(FRONT, ellipse(0.0, OV[1], OV[2] + 0.12, OV[3] + 0.12), ellipse(0.0, OV[1], OV[2], OV[3]), -0.02, 0.05)
for ang in (0, 90, 180, 270):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    def P(r_a, r_b, off):
        return (OV[0] + (OV[2] + r_a) * c - off * s, OV[1] + (OV[3] + r_b) * s + off * c)
    T.wprism(FRONT, [P(-0.03, -0.03, -0.06), P(-0.03, -0.03, 0.06), P(0.20, 0.20, 0.08), P(0.20, 0.20, -0.08)], -0.02, 0.08)

# ---------------------------------------------------------------------------
# Roofs: low hip on the main block up to the deck, flat roof on the Flats, chimney
# ---------------------------------------------------------------------------
IN = CORN_IN
bm = R.bm
base = [(-HW + IN, IN), (HW - IN, IN), (HW - IN, DEPTH - IN), (-HW + IN, DEPTH - IN)]
deck = [(-1.85, CUP[1] - 1.85), (1.85, CUP[1] - 1.85), (1.85, CUP[1] + 1.85), (-1.85, CUP[1] + 1.85)]
vb = [bm.verts.new((x, y, TOP)) for x, y in base]
vt = [bm.verts.new((x, y, DECK)) for x, y in deck]
faces = [bm.faces.new(list(reversed(vb))), bm.faces.new(vt)]
for i in range(4):
    j = (i + 1) % 4
    faces.append(bm.faces.new([vb[i], vb[j], vt[j], vt[i]]))
R.rid = 0
R._closed(faces)
FLATS_PLAN = [(FX0, DEPTH), (HW, DEPTH), (HW, FY1), CH_B, CH_A]
R.prism(FLATS_PLAN, TOP, TOP + 0.03, axis="z")
# chimney: south wall at y 11.5, 0.90 x 0.50, top 12.60, corbel cap
B.box(HW - 0.55, HW - 0.05, 11.05, 11.95, TOP - 0.2, 12.52)
B.box(HW - 0.59, HW - 0.01, 11.01, 11.99, 12.44, 12.52)
B.box(HW - 0.55, HW - 0.05, 11.05, 11.95, 12.52, 12.60)
IR.box(HW - 0.45, HW - 0.15, 11.25, 11.75, 12.59, 12.61)                       # flue opening (dark)

# ---------------------------------------------------------------------------
# Cupola (wood, cream): plinth, body with pilasters and windows, cornice with brackets,
# four segmental clock gables with dials, barrel roofs, pyramid, iron pole and ball
# ---------------------------------------------------------------------------
cx, cy = CUP
SQ = math.sqrt(2)
CP.lathe(cx, cy, [(1.85 * SQ, DECK - 0.15), (1.85 * SQ, 12.20), (1.68 * SQ, 12.30)], sides=4)   # plinth
CUPB.box(cx - CB, cx + CB, cy - CB, cy + CB, 12.28, 14.70)                                      # body
CUP_W = [Wall((cx, cy - CB), (0, -1), CUT_C), Wall((cx + CB, cy), (1, 0), CUT_C),
         Wall((cx, cy + CB), (0, 1), CUT_C), Wall((cx - CB, cy), (-1, 0), CUT_C)]
GZ0, GZS = 14.95, 15.12            # gable base, top of its straight legs
GR = 0.85                          # gable arc radius (crown 15.97)
DIAL_Z, DIAL_R = 15.42, 0.50
for k, w in enumerate(CUP_W):
    # tall window 0.80 x 1.78 (sill 12.60), segmental head, glass with the dark clock room behind, sash bars
    ol = seg_outline(0.0, 0.80, 12.60, 14.38, 0.10, 6)
    w.cut.wprism(w, ol, -0.17, 0.25)
    pane(w, ol, -0.11, ("dark_room", "dark_room_frame")[k % 2])
    CP.wbox(w, -0.40, 0.40, 13.45, 13.51, -0.11, -0.06)                        # meeting rail
    CP.wbox(w, -0.018, 0.018, 12.60, 14.30, -0.11, -0.07)                      # muntin
    CP.wbox(w, -0.50, 0.50, 12.52, 12.60, -0.12, 0.05)                         # sill
    zc_w, R_w, th_w = seg_geom(0.80, 14.28, 0.10)
    CP.wprism(w, band(0.0, zc_w, R_w, R_w + 0.06, math.pi / 2 - th_w - 0.12, math.pi / 2 + th_w + 0.12, 6), -0.01, 0.04)
    for s in (-1, 1):                                                          # casing
        a, b = sorted((s * 0.40, s * 0.46))
        CP.wbox(w, a, b, 12.60, 14.30, -0.01, 0.03)
        a, b = sorted((s * 0.62, s * 0.97))                                    # sunk panels 0.35 wide
        w.cut.wbox(w, a, b, 12.75, 14.15, -0.025, 0.25)
    # frieze fillet, consoles at the corners, small brackets under the cornice
    for s in (-1, 1):
        u0, u1 = sorted((s * (CB - 0.30), s * (CB + 0.04)))
        CP.oprism(w, [(0.0, 14.10), (0.08, 14.10), (0.12, 14.22), (0.15, 14.40), (0.15, 14.46), (0.0, 14.46)], u0, u1)
        for ub in (s * 0.75,):
            CP.oprism(w, [(0.0, 14.46), (0.06, 14.46), (0.10, 14.56), (0.24, 14.70), (0.24, 14.78), (0.0, 14.78)],
                      ub - 0.05, ub + 0.05)
# corner pilasters 0.30, 0.04 proud on both faces
for sx in (-1, 1):
    for sy in (-1, 1):
        x0, x1 = sorted((cx + sx * (CB - 0.26), cx + sx * (CB + 0.04)))
        y0, y1 = sorted((cy + sy * (CB - 0.26), cy + sy * (CB + 0.04)))
        CP.box(x0, x1, y0, y1, 12.30, 14.10)
CP.lathe(cx, cy, [((CB + 0.05) * SQ, 14.40), ((CB + 0.05) * SQ, 14.45)], sides=4)            # frieze fillet
CP.lathe(cx, cy, [((CB + 0.10) * SQ, 14.70), ((CB + 0.12) * SQ, 14.78)], sides=4)            # bed mould
CP.lathe(cx, cy, [((CB + 0.30) * SQ, 14.78), ((CB + 0.30) * SQ, 14.90)], sides=4)            # corona
CP.lathe(cx, cy, [((CB + 0.26) * SQ, 14.90), ((CB + 0.20) * SQ, GZ0)], sides=4)              # cap
# pyramid roof behind the gables (tin)
R.lathe(cx, cy, [((CB + 0.12) * SQ, GZ0 - 0.01), (0.0, 15.70)], sides=4)
for w in CUP_W:
    gable = [(-GR, GZ0), (GR, GZ0)] + arc_pts(0.0, GZS, GR, 0.0, math.pi, 10)
    CP.wprism(w, gable, -0.12, 0.0)                                            # gable face, flush with the body
    R.wprism(w, [(-GR - 0.03, GZ0), (GR + 0.03, GZ0)] + arc_pts(0.0, GZS, GR + 0.03, 0.0, math.pi, 10),
             -0.10, -CB)                                                       # barrel roof
    CP.wprism(w, band(0.0, GZS, GR - 0.08, GR + 0.02, 0.0, math.pi, 10), -0.05, 0.06)   # arch moulding
    for s in (-1, 1):
        a, b = sorted((s * (GR - 0.08), s * (GR + 0.02)))
        CP.wbox(w, a, b, GZ0, GZS, -0.05, 0.06)                                # leg mouldings
    atlas_rec(region="dial", mode="disc", wall=wall_rec(w), cu=0.0, cz=DIAL_Z, r=DIAL_R)
    AT.wprism(w, ellipse(0.0, DIAL_Z, DIAL_R, DIAL_R, 16), -0.02, 0.04)        # clock dial
    AT.rid = 0
    CP.wring(w, ellipse(0.0, DIAL_Z, DIAL_R + 0.05, DIAL_R + 0.05, 16), ellipse(0.0, DIAL_Z, DIAL_R, DIAL_R, 16),
             -0.02, 0.06)                                                      # bezel
# iron pole and ball
IR.lathe(cx, cy, [(0.06, GZS + GR - 0.05), (0.025, GZS + GR + 0.15), (0.025, 18.64)], sides=6)
IR.lathe(cx, cy, [(0.0, 18.58), (0.045, 18.61), (0.06, 18.64), (0.045, 18.67), (0.0, 18.70)], sides=6)

# ---------------------------------------------------------------------------
# Steps along the whole front (4 risers x 0.15, treads 0.30, y -1.20 ... 0), cheek blocks
# ---------------------------------------------------------------------------
STEPS = [(-1.20, SKIRT), (-1.20, 0.15), (-0.90, 0.15), (-0.90, 0.30), (-0.60, 0.30), (-0.60, 0.45),
         (-0.30, 0.45), (-0.30, FL), (0.0, FL), (0.0, SKIRT)]
CHEEKS = ((-HW, -7.65), (-2.57, -2.27), (2.27, 2.57), (7.65, HW))
for (a0, a1), (b0, b1) in zip(CHEEKS, CHEEKS[1:]):
    ST.prism(STEPS, a1, b0, axis="x")
for x0, x1 in CHEEKS:
    ST.prism([(-1.20, SKIRT), (-1.20, 0.30), (-1.05, 0.36), (0.0, 0.75), (0.0, SKIRT)], x0, x1, axis="x")

# Water table on the Bloomfield side (stone, 0 -> 0.60, 0.03 proud) and the Flats
ST.wbox(SOUTH, 0.0, FY1 + 0.03, SKIRT, FL, -0.01, 0.03)
ST.wbox(FL_E, -HW - 0.03, -CH_B[0], SKIRT, 0.30, -0.01, 0.03)

# ---------------------------------------------------------------------------
# Awnings (48 plain cream, "GREEN'S APOTHECARY" valance; 52 red/cream stripes): roller at 3.35
# on the wall, sloping to 2.65 at y -2.20, scalloped valance 0.25 (bottom 2.40), cloth cheeks,
# 2 iron arms each
# ---------------------------------------------------------------------------
AWY, AWZ0, AWZ1 = -2.20, 3.35, 2.65
VAL_BOT = AWZ1 - 0.25
AW_D = 0.06
AWNINGS = {"48": (-7.55, -2.65, "canvas48", "val48"), "52": (2.65, 7.55, "stripes", "val52")}
for key, (a0, a1, top_reg, val_reg) in AWNINGS.items():
    atlas_rec(region=top_reg, mode="slope", wall=wall_rec(FRONT), u0=a0, u1=a1, d0=AW_D, d1=-AWY)
    AT.prism([(-AW_D, AWZ0), (AWY, AWZ1), (AWY, AWZ1 - 0.02), (-AW_D, AWZ0 - 0.02)], a0, a1, axis="x")
    NS = 14
    pitch = (a1 - a0) / NS
    val = [(a1, AWZ1), (a0, AWZ1)]
    for k in range(NS):
        x0 = a0 + k * pitch
        val += [(x0, VAL_BOT + 0.07), (x0 + 0.2 * pitch, VAL_BOT + 0.02), (x0 + 0.5 * pitch, VAL_BOT),
                (x0 + 0.8 * pitch, VAL_BOT + 0.02)]
    val += [(a1, VAL_BOT + 0.07)]
    atlas_rec(region=val_reg, mode="rect", wall=wall_rec(FRONT), u0=a0, u1=a1, z0=VAL_BOT, z1=AWZ1,
              back="spare" if key == "48" else "val52")
    AT.prism(val, AWY - 0.01, AWY, axis="y")
    for x in (a0, a1):                                                         # side cheeks
        atlas_rec(region=top_reg if key == "52" else "spare", mode="side", wall=wall_rec(FRONT),
                  d0=AW_D, d1=-AWY, z0=AWZ1 - 0.02, z1=AWZ0)
        AT.prism([(-AW_D, AWZ0 - 0.02), (AWY, AWZ1 - 0.02), (-AW_D, AWZ1 - 0.02)], x - 0.005, x + 0.005, axis="x")
    AT.rid = 0
    IR.box(a0, a1, AWY + 0.005, AWY + 0.03, AWZ1 - 0.05, AWZ1 - 0.02)          # front bar
    IR.box(a0, a1, -0.10, -0.02, AWZ0 - 0.02, AWZ0 + 0.06)                     # roller box
    for x in (a0 + 0.10, a1 - 0.10):                                           # iron arms
        IR.prism([(0.0, 2.25), (0.0, 2.29), (AWY + 0.03, AWZ1 - 0.02), (AWY + 0.03, AWZ1 - 0.06)],
                 x - 0.012, x + 0.012, axis="x")

# ---------------------------------------------------------------------------
# Build objects (boolean the cut shells)
# ---------------------------------------------------------------------------


def cut_shell(shell, cutter, name, mat):
    walls = shell.to_object(name, MATS[mat], col)
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


cut_shell(SHELL, CUT, "RB_Shell", "Brick")
cut_shell(STUC, CUT_S, "RB_Stucco", "Trim")
cut_shell(TYMP, CUT_T, "RB_Tymp", "Brick")
cut_shell(CUPB, CUT_C, "RB_CupBody", "Trim")
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("RB_" + key, MATS[BUILDER_MAT[key]], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Rea Building built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)",
      "| front pediment crown %.2f, side %.2f" % (zc_f + r_f, zc_s + r_s), "| atlas records", len(ATLAS),
      "| window backs", len(BACKREC))
# Materials, baked lighting and GLB export: run rea_building_bake.py (it runs this file first).
