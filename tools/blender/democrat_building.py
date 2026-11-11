"""
democrat_building.py - builds the Democrat building, 96-98 Main St, Flemington (east side, old
no. 533; J. C. Hopewell, 1875): cigar store in front, the Hunterdon Democrat's printing office
behind, and the 1-storey frame "News" lean-to on the south side, as in Sept 1921.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/democrat_building.py").read())

Every run deletes and rebuilds the "DemocratBuilding" collection. Materials, lightmap bake and
GLB export: democrat_building_bake.py (runs this file first). Pattern: masonic_hall.py (north
neighbour, same builder): one bmesh per part, a material index per face, closed shells cut by
nested boolean pockets whose faces keep the cutter's material index.

Sources: PLAN.md "Democrat building: cigar store, news stand and printing office (96-98 Main
St, old no. 533)" (Sept 1921 Sanborn sheet 3; Goodspeed's frontal c. 1900 and c. 1918 photos,
view only; heights +-0.25 m). Owner decisions 2026-11-11: the "DEMOCRAT" board over the north
door is lettered (texture democrat-building/signs.jpg, made by
tools/prepare_democrat_building_textures.py); the cigar advert over the show window is a plain
dark panel; the News lean-to is a plain guess without lettering; brick width 4.96 m; no
shutters, no awning.

Windows (PLAN.md "E. Windows that don't read as flat black"): every pane is ONE glass face
(material Glass -> exported as `glass`) 4 cm in front of a window back: the back of the pane's
boolean pocket, with atlas UVs into assets/textures/shared/window_backs.jpg (upper floor: a
cream blind half down, a dark room, a green blind; show window and cigar-store doors: the dim
counter-and-shelves cells; Democrat office door and the News lean-to: dark rooms).

Coordinates (metres, Blender Z-up), origin = scene (10.08, 0.15, 43.85), rotation 0 -90 0:
    X  along the street, +X = south (News lean-to, 100-102), -X = north (slot, Masonic Hall)
    Y  depth: y = 0 is the shop cornice's face; the brick wall is at y = 0.22; the main cornice
       reaches y = -0.22; rear of the front block 22.70, rear extension to 30.44
    Z  up from the sidewalk top; walls skirt down to -0.20
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".
"""

import json
import math
import bpy
import bmesh
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md placement, massing and elevation notes)
# ---------------------------------------------------------------------------
HW = 2.48               # half width of the brick front (4.96, 1921 map)
YW = 0.22               # brick wall face (the shop cornice projects to y = 0)
YR = 22.70              # rear of the front block
SKIRT = -0.20
RF, RR = 6.00, 5.40     # shed roof: at the front wall, at the rear
SHOP_T = 3.00           # top of the shop-front zone (fascia top); shop cornice 3.00-3.15
CT = 6.10               # main cornice top (1910 map: 20 ft)
CB = 5.85               # main cornice underside = top of the frieze
FZ = 5.45               # frieze bottom
ARCH_R = 0.98           # outer radius of the cornice arch (centre at CB): apex 6.83 + crown = 6.85
ARCH_W = 0.25           # arch band = the cornice's own height
CY = YW - 0.40          # main cornice face (projects 0.40)
EXT = (-1.65, 2.55, 30.44, 5.40)      # rear extension: x0, x1, rear y, height
NEWS_X1, NEWS_YR, NEWS_F, NEWS_R = 4.43, 9.57, 3.00, 2.60    # News lean-to
XN = lambda xn: xn - HW # "Xn" (metres from the north wall) -> X

WIN_X = (XN(0.90), XN(2.48), XN(4.06))   # upper windows, 0.85 wide
WIN_W, SILL, WTOP, RISE = 0.85, 3.40, 5.35, 0.15
SIDE_WIN_Y = (13.0, 19.0)                 # south wall, upper floor (map ticks)
SIGN = (XN(0.20), XN(1.25), 2.50, 2.74)   # "DEMOCRAT" board: x0, x1, z0, z1

BRICK, DARK, PALE, CLAP, ROOF, GLASS, WBACK, SIGNS = range(8)
NAMES = ["Brick", "Dark", "Pale", "Clapboard", "Roof", "Glass", "WindowBack", "Signs"]


# ---------------------------------------------------------------------------
# Materials (plain stand-ins; democrat_building_bake.py swaps in the textures)
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


COLOURS = ["#84493A", "#3A3A2E", "#D8D0BC", "#9A917C", "#5A3D34", "#1A1916", "#3a332c", "#E4DECC"]
MATS = [plain("DB_" + n, c) for n, c in zip(NAMES, COLOURS)]

# ---------------------------------------------------------------------------
# Mesh builder: one bmesh, a material index per face (as masonic_hall.py)
# ---------------------------------------------------------------------------


class MB:
    def __init__(self):
        self.bm = bmesh.new()

    @staticmethod
    def _pt(axis, u, d, v):
        # 'y': outline in X-Z, depth along Y; 'x': outline in Y-Z, depth along X;
        # 'z': plan outline in X-Y, depth along Z
        if axis == "y":
            return (u, d, v)
        if axis == "x":
            return (d, u, v)
        return (u, v, d)

    def prism(self, pts, d0, d1, axis="y", mi=DARK):
        """Extrude a 2D outline between depths d0 and d1. mi: one index, or (cap at d0, cap at
        d1, sides) where sides is an index or a list with one index per outline edge."""
        bm = self.bm
        if isinstance(mi, int):
            m0 = m1 = mi
            ms = [mi] * len(pts)
        else:
            m0, m1, ms = mi
            ms = ms if isinstance(ms, (list, tuple)) else [ms] * len(pts)
        a = [bm.verts.new(self._pt(axis, u, d0, v)) for u, v in pts]
        b = [bm.verts.new(self._pt(axis, u, d1, v)) for u, v in pts]
        fa = bm.faces.new(a)
        fa.material_index = m0
        fb = bm.faces.new(list(reversed(b)))
        fb.material_index = m1
        faces = [fa, fb]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new([a[i], a[j], b[j], b[i]])
            f.material_index = ms[i]
            faces.append(f)
        bmesh.ops.recalc_face_normals(bm, faces=faces)

    def face(self, pts, d, axis, out, mi=GLASS):
        """One flat face (a glass pane) with its normal pointing out (+-axis)."""
        f = self.bm.faces.new([self.bm.verts.new(self._pt(axis, u, d, v)) for u, v in pts])
        f.material_index = mi
        f.normal_update()
        want = Vector((0, out, 0)) if axis == "y" else Vector((out, 0, 0))
        if f.normal.dot(want) < 0:
            f.normal_flip()

    def box(self, x0, x1, y0, y1, z0, z1, mi=DARK):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, "y", mi)

    def arc_band(self, cu, cv, r_in, r_out, a0, a1, d0, d1, axis="y", segs=8, mi=BRICK):
        """Curved band between radii r_in and r_out, angles a0..a1 (0 = +u, pi/2 = up)."""
        bm = self.bm
        ts = [a0 + (a1 - a0) * i / segs for i in range(segs + 1)]

        def ring(r, d):
            return [bm.verts.new(self._pt(axis, cu + r * math.cos(t), d, cv + r * math.sin(t))) for t in ts]
        of, inf, ob, ib = ring(r_out, d0), ring(r_in, d0), ring(r_out, d1), ring(r_in, d1)
        faces = []
        for i in range(segs):
            j = i + 1
            faces.append(bm.faces.new([of[i], of[j], inf[j], inf[i]]))
            faces.append(bm.faces.new([ob[i], ib[i], ib[j], ob[j]]))
            faces.append(bm.faces.new([of[i], ob[i], ob[j], of[j]]))
            faces.append(bm.faces.new([inf[i], inf[j], ib[j], ib[i]]))
        faces.append(bm.faces.new([of[0], inf[0], ib[0], ob[0]]))
        faces.append(bm.faces.new([of[-1], ob[-1], ib[-1], inf[-1]]))
        for f in faces:
            f.material_index = mi
        bmesh.ops.recalc_face_normals(bm, faces=faces)

    def to_object(self, name, col):
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        for m in MATS:
            mesh.materials.append(m)
        obj = bpy.data.objects.new(name, mesh)
        col.objects.link(obj)
        return obj


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def segmental(cu, w, z0, zs, rise, segs=4):
    """Segment-headed opening: sides to zs, a shallow arc rising `rise` above zs."""
    r = w / 2
    R = (r * r + rise * rise) / (2 * rise)
    zc = zs + rise - R
    a = math.asin(r / R)
    pts = [(cu - r, z0), (cu + r, z0)]
    for i in range(segs + 1):
        t = math.pi / 2 - a + 2 * a * i / segs
        pts.append((cu + R * math.cos(t), zc + R * math.sin(t)))
    return pts


def half_disc(cu, cv, r, segs=12):
    return [(cu + r * math.cos(math.pi * i / segs), cv + r * math.sin(math.pi * i / segs)) for i in range(segs + 1)]


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


col = fresh_collection("DemocratBuilding")
P = MB()                       # all added parts
MAIN, CUT_M = MB(), MB()       # front block (brick shell)
NEWS, CUT_N = MB(), MB()       # News lean-to (clapboard shell)
REARX = MB()                   # rear extension (plain brick box)

# Each wall: (axis, outer face depth, outward sign)
FRONT = ("y", YW, -1)
SOUTH = ("x", HW, 1)


def Dfun(wall):
    axis, face, out = wall
    return axis, (lambda k: face + out * k)   # k > 0 outside the wall, k < 0 inside


# ---------------------------------------------------------------------------
# Window backs and glass
# ---------------------------------------------------------------------------
WB_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\window_backs.json"))["cells"]
GAP = 0.04
CROPPED = ("shop_a", "shop_b", "door", "return", "transom")    # room views: never stretched
BACKS = []             # (axis, plane, out, u0, u1, z0, z1, uv rect)


def cell_uv(cell, aspect=None):
    """Atlas rectangle of a cell; the shop cells are cropped (centred) to `aspect` (w/h) so
    the room is not stretched. 1.5 px inset against bleeding from the neighbour."""
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


def register_back(wall, outline, d_back, cell, frame=None):
    """Remember a window back so its faces get `cell`'s atlas UVs after the booleans.
    frame = (u0, u1, z0, z1): the cell spans this whole rectangle (a window of several panes)
    and this back gets its part of it."""
    axis, face, out = wall
    us, vs = [p[0] for p in outline], [p[1] for p in outline]
    u0, u1, z0, z1 = min(us), max(us), min(vs), max(vs)
    fu0, fu1, fz0, fz1 = frame or (u0, u1, z0, z1)
    U0, V0, U1, V1 = cell_uv(cell, (fu1 - fu0) / (fz1 - fz0))
    su = lambda u: U0 + (U1 - U0) * (u - fu0) / (fu1 - fu0)
    sv = lambda z: V0 + (V1 - V0) * (z - fz0) / (fz1 - fz0)
    BACKS.append((axis, face - out * d_back, out, u0, u1, z0, z1, (su(u0), sv(z0), su(u1), sv(z1))))


def pane(C, wall, outline, d_glass, cell, side_mat, frame=None):
    """One pane: a pocket (sides `side_mat`, back = window back GAP behind the glass) cut by
    cutter C, and one glass face."""
    axis, D = Dfun(wall)
    C.prism(outline, D(0.25), D(-d_glass - GAP), axis, mi=(side_mat, WBACK, side_mat))
    register_back(wall, outline, d_glass + GAP, cell, frame)
    P.face(outline, D(-d_glass), axis, wall[2])


def assign_atlas_uvs(obj):
    """Window-back faces -> their atlas cell, left to right as seen from outside."""
    me = obj.data
    uvl = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    missed = 0
    for p in me.polygons:
        if p.material_index != WBACK:
            continue
        c, n = p.center, p.normal
        hit = None
        for b in BACKS:
            axis, plane, out, u0, u1, z0, z1, uv = b
            k = 1 if axis == "y" else 0
            cu = c.x if axis == "y" else c.y
            if n[k] * out > 0.9 and abs(c[k] - plane) < 0.003 and u0 - 1e-3 <= cu <= u1 + 1e-3 \
                    and z0 - 1e-3 <= c.z <= z1 + 1e-3:
                hit = b
                break
        if hit is None:
            missed += 1
            continue
        axis, plane, out, u0, u1, z0, z1, (U0, V0, U1, V1) = hit
        flip = (axis == "y" and out > 0) or (axis == "x" and out < 0)
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            t = ((co.x if axis == "y" else co.y) - u0) / (u1 - u0)
            t = 1 - t if flip else t
            s = (co.z - z0) / (z1 - z0)
            uvl.data[li].uv = (U0 + (U1 - U0) * t, V0 + (V1 - V0) * s)
    if missed:
        print("WARNING:", missed, "window-back faces of", obj.name, "found no atlas cell")


# ---------------------------------------------------------------------------
# Shells
# ---------------------------------------------------------------------------
# front block: side outline (Y-Z) with the shed roof falling to the rear; edges: bottom, rear,
# roof, front
MAIN.prism([(YW, SKIRT), (YR, SKIRT), (YR, RR), (YW, RF)], -HW, HW, axis="x",
           mi=(BRICK, BRICK, [BRICK, BRICK, ROOF, BRICK]))
# rear extension (1921 map; not on the 1910 one): plain brick box, flat tin roof
REARX.prism(rect(EXT[0], EXT[1], YR, EXT[2]), SKIRT, EXT[3], axis="z", mi=(BRICK, ROOF, BRICK))
# News lean-to: frame, shed roof falling to the rear
NEWS.prism([(YW, SKIRT), (NEWS_YR, SKIRT), (NEWS_YR, NEWS_R), (YW, NEWS_F)], HW, NEWS_X1, axis="x",
           mi=(CLAP, CLAP, [CLAP, CLAP, ROOF, CLAP]))

# ---------------------------------------------------------------------------
# Upper windows: segment-headed, 1-over-1 sash set back 0.12, brick hood with a pale painted
# top edge, pale stone sill
# ---------------------------------------------------------------------------
FR = 0.06          # sash frame width
D_FRAME = 0.12
D_GLASS = 0.17


def seg_window(C, wall, cu, w, z0, z1, cell, hood=True):
    axis, D = Dfun(wall)
    zs = z1 - RISE
    outer = segmental(cu, w, z0, zs, RISE)
    inner = segmental(cu, w - 2 * FR, z0 + FR, zs, RISE - FR * 0.5)
    C.prism(outer, D(0.25), D(-D_FRAME), axis, mi=(BRICK, PALE, BRICK))
    pane(C, wall, inner, D_GLASS, cell, PALE)
    zm = (z0 + zs) / 2 + 0.04                                       # meeting rail
    P.prism(rect(cu - w / 2 + FR, cu + w / 2 - FR, zm - 0.03, zm + 0.03), D(-D_FRAME), D(-D_GLASS), axis, mi=PALE)
    # sill 0.10 tall, 0.06 proud; its top 2 cm above the reveal floor (no coplanar faces)
    P.prism(rect(cu - w / 2 - 0.08, cu + w / 2 + 0.08, z0 - 0.10 + 0.02, z0 + 0.02), D(0.06), D(-D_FRAME), axis,
            mi=PALE)
    if hood:
        r = w / 2
        R = (r * r + RISE * RISE) / (2 * RISE)
        zc = z1 - R
        a = math.asin(min(1.0, (r + 0.10) / R))                     # the hood laps 0.10 past each jamb
        P.arc_band(cu, zc, R, R + 0.13, math.pi / 2 - a, math.pi / 2 + a, D(0.08), D(0.0), axis, segs=5, mi=BRICK)
        P.arc_band(cu, zc, R + 0.13, R + 0.18, math.pi / 2 - a, math.pi / 2 + a, D(0.10), D(0.0), axis, segs=5,
                   mi=PALE)


for cu, cell in zip(WIN_X, ("blind_cream_half", "dark_room", "blind_green_half")):
    seg_window(CUT_M, FRONT, cu, WIN_W, SILL, WTOP, cell)
for y, cell in zip(SIDE_WIN_Y, ("blind_cream_low", "dark_room_frame")):
    seg_window(CUT_M, SOUTH, y, WIN_W, SILL, WTOP, cell, hood=False)

# ---------------------------------------------------------------------------
# Main cornice: panelled frieze, 6 brackets, boxed cornice, round arch over the middle with a
# recessed dark tympanum (a front piece 0.5 m deep)
# ---------------------------------------------------------------------------
BRK_X = (XN(0.10), XN(0.34), XN(1.45), XN(3.51), XN(4.62), XN(4.86))
P.box(-HW - 0.02, HW + 0.02, YW - 0.04, YW + 0.01, FZ, CB, mi=DARK)                 # frieze board
for a, b in ((BRK_X[1], BRK_X[2]), (BRK_X[2], BRK_X[3]), (BRK_X[3], BRK_X[4])):     # raised panels
    P.box(a + 0.14, b - 0.14, YW - 0.055, YW - 0.04, FZ + 0.08, CB - 0.08, mi=DARK)
BRACKET = [(YW + 0.01, FZ), (YW - 0.04, FZ), (YW - 0.07, FZ + 0.06), (YW - 0.10, FZ + 0.20), (YW - 0.20, FZ + 0.30),
           (YW - 0.30, FZ + 0.34), (YW - 0.33, CB), (YW + 0.01, CB)]
for xb in BRK_X:
    P.prism(BRACKET, xb - 0.06, xb + 0.06, "x", mi=DARK)
P.box(-HW - 0.04, HW + 0.04, YW - 0.12, YW + 0.01, CB - 0.07, CB, mi=DARK)             # bed mould
XA = 0.85                                     # the level cornice stops inside the arch's feet
for s in (-1, 1):
    a, b = sorted((s * XA, s * (HW + 0.15)))
    P.box(a, b, CY, YW + 0.08, CB, CT, mi=DARK)                                     # boxed cornice
    a, b = sorted((s * 0.95, s * (HW + 0.19)))
    P.box(a, b, CY - 0.04, CY, CT - 0.10, CT + 0.02, mi=DARK)                       # crown strip
    a, b = sorted((s * (HW + 0.15), s * (HW + 0.19)))
    P.box(a, b, CY - 0.04, YW + 0.08, CT - 0.10, CT + 0.02, mi=DARK)                # crown return
P.box(-XA, XA, CY + 0.08, YW + 0.08, CB, CB + 0.10, mi=DARK)                        # bed under the arch
P.arc_band(0.0, CB, ARCH_R - ARCH_W, ARCH_R, 0.0, math.pi, CY, CY + 0.50, "y", segs=16, mi=DARK)
P.arc_band(0.0, CB, ARCH_R - 0.03, ARCH_R + 0.02, 0.0, math.pi, CY - 0.04, CY, "y", segs=16, mi=DARK)   # crown
P.prism(half_disc(0.0, CB + 0.10, ARCH_R - ARCH_W + 0.01, 16), CY + 0.15, CY + 0.48, "y", mi=DARK)     # tympanum

# ---------------------------------------------------------------------------
# Shop front (c. 1900 and c. 1918 photos): brick end piers; between them a wooden front 3 cm
# behind the pier faces: north door, post, show window, post, south door; fascia; moulded shop
# cornice with a scrolled console on each pier
# ---------------------------------------------------------------------------
axis, D = Dfun(FRONT)
SF0, SF1 = XN(0.24), XN(4.66)                 # between the piers
YS = YW + 0.03                                # the wooden front's plane
CUT_M.prism(rect(SF0, SF1, -0.10, SHOP_T), D(0.25), YS, "y", mi=(BRICK, DARK, BRICK))

ND = (XN(0.30), XN(1.18))                     # north door (Democrat office), recessed 0.25
SW = (XN(1.40), XN(3.34))                     # show window
SD = (XN(3.46), XN(4.60))                     # south door (cigar store), recessed 0.60
ND_Y, SD_Y = YW + 0.25, YW + 0.60
DOOR_T, BAR_T = 2.12, 2.18                    # door leaf top, transom bar top


def threshold(x0, x1, y_back):
    """Worn wooden sill / recess floor, 2 cm above the sidewalk."""
    P.box(x0, x1, YW - 0.02, y_back + 0.01, -0.10, 0.02, mi=DARK)


def leaf(x0, x1, y, cell, frame=None):
    """Half-glazed door leaf on the recess back at depth y: raised lower panel, glass above."""
    P.box(x0 + 0.11, x1 - 0.11, y - 0.015, y + 0.005, 0.22, 0.90, mi=DARK)
    pane(CUT_M, FRONT, rect(x0 + 0.11, x1 - 0.11, 1.05, 1.98), y - YW + 0.03, cell, DARK, frame)


# north door: one half-glazed door to 2.12, transom bar, plain transom light, under the board
x0, x1 = ND
CUT_M.prism(rect(x0, x1, -0.10, 2.48), D(0.25), ND_Y, "y", mi=(DARK, DARK, DARK))
threshold(x0, x1, ND_Y)
leaf(x0 + 0.04, x1 - 0.04, ND_Y, "dark_room_frame")
for a, b in ((x0, x0 + 0.045), (x1 - 0.045, x1)):                                    # door frame
    P.box(a, b, ND_Y - 0.03, ND_Y + 0.005, 0.02, 2.48, mi=DARK)
P.box(x0 + 0.045, x1 - 0.045, ND_Y - 0.04, ND_Y + 0.005, DOOR_T, BAR_T, mi=DARK)    # transom bar
pane(CUT_M, FRONT, rect(x0 + 0.07, x1 - 0.07, BAR_T + 0.03, 2.43), ND_Y - YW + 0.03, "dark_room", DARK)

# "DEMOCRAT" board (owner decision 1): white board 1.05 x 0.24, 0.04 proud of the piers; only
# its face carries the Signs material (UVs set in the bake script)
P.box(SIGN[0], SIGN[1], YW - 0.04, YS + 0.005, SIGN[2], SIGN[3], mi=(SIGNS, PALE, PALE))

# show window: stall riser 0-0.60, glass 0.60-2.25 in 2 x 2 panes with thin bars, plain dark
# transom panel above (the c. 1918 cigar advert is left off, decision 2)
x0, x1 = SW
WZ0, WZ1 = 0.60, 2.25
CUT_M.prism(rect(x0, x1, WZ0, WZ1), D(0.25), YS + 0.05, "y", mi=(DARK, DARK, DARK))
f, bar = 0.05, 0.03
xm, zm = (x0 + x1) / 2, (WZ0 + WZ1) / 2
frame = (x0 + f, x1 - f, WZ0 + f, WZ1 - f)
for a, b in ((x0 + f, xm - bar / 2), (xm + bar / 2, x1 - f)):
    for za, zb in ((WZ0 + f, zm - bar / 2), (zm + bar / 2, WZ1 - f)):
        pane(CUT_M, FRONT, rect(a, b, za, zb), YS - YW + 0.08, "shop_a", DARK, frame)
P.box(x0 - 0.05, x1 + 0.05, YW - 0.03, YS + 0.05, WZ0 - 0.04, WZ0 + 0.015, mi=DARK)   # sill ledge
P.box(x0 + 0.10, x1 - 0.10, YS - 0.015, YS + 0.005, 0.08, 0.50, mi=DARK)             # riser panel
P.box(x0 + 0.06, x1 - 0.06, YS - 0.015, YS + 0.005, 2.32, 2.70, mi=DARK)             # transom panel
for a, b in ((ND[1] + 0.02, x0 - 0.02), (x1 + 0.02, SD[0] - 0.02)):                   # posts
    P.box(a, b, YS - 0.02, YS + 0.005, 0.0, 2.74, mi=DARK)

# south door: recess 0.60 deep, pair of narrow half-glazed doors, transom light
x0, x1 = SD
CUT_M.prism(rect(x0, x1, -0.10, 2.60), D(0.25), SD_Y, "y", mi=(DARK, DARK, DARK))
threshold(x0, x1, SD_Y)
xm = (x0 + x1) / 2
dframe = (x0 + 0.05 + 0.11, x1 - 0.05 - 0.11, 1.05, 1.98)       # one room view across both leaves
leaf(x0 + 0.05, xm - 0.01, SD_Y, "shop_b", dframe)
leaf(xm + 0.01, x1 - 0.05, SD_Y, "shop_b", dframe)
P.box(xm - 0.02, xm + 0.02, SD_Y - 0.025, SD_Y + 0.005, 0.02, DOOR_T, mi=DARK)       # astragal
for a, b in ((x0, x0 + 0.05), (x1 - 0.05, x1)):
    P.box(a, b, SD_Y - 0.03, SD_Y + 0.005, 0.02, 2.60, mi=DARK)
P.box(x0 + 0.05, x1 - 0.05, SD_Y - 0.04, SD_Y + 0.005, DOOR_T, BAR_T, mi=DARK)
pane(CUT_M, FRONT, rect(x0 + 0.08, x1 - 0.08, BAR_T + 0.03, 2.54), SD_Y - YW + 0.03, "transom", DARK)

# fascia 2.75-3.00, moulded cornice 3.00-3.15 out to y = 0, a scrolled console on each pier
P.box(SF0, SF1, YW - 0.015, YS + 0.005, 2.76, SHOP_T, mi=DARK)
SHOP_CORN = [(YW + 0.01, 3.00), (0.13, 3.00), (0.10, 3.05), (0.03, 3.10), (0.0, 3.10), (0.0, 3.15), (YW + 0.01, 3.15)]
P.prism(SHOP_CORN, -HW - 0.02, HW, "x", mi=DARK)
CONSOLE = [(YW + 0.01, 2.55), (YW - 0.03, 2.55), (YW - 0.07, 2.60), (YW - 0.07, 2.68), (YW - 0.04, 2.74),
           (YW - 0.06, 2.84), (YW - 0.13, 2.92), (YW - 0.17, 2.96), (YW - 0.17, 3.00), (YW + 0.01, 3.00)]
for a in (XN(0.03), XN(4.72)):
    P.prism(CONSOLE, a, a + 0.18, "x", mi=DARK)

# ---------------------------------------------------------------------------
# News lean-to front (PURE GUESS, plain, no lettering): clapboard, half-glazed door, one small
# window, flat fascia board, corner board
# ---------------------------------------------------------------------------
x0, x1 = 2.75, 3.55                            # door 0.80 x 2.05
NY = YW + 0.08
CUT_N.prism(rect(x0, x1, -0.10, 2.05), D(0.25), NY, "y", mi=(PALE, DARK, PALE))
P.box(x0, x1, YW - 0.02, NY + 0.01, -0.10, 0.02, mi=DARK)                            # sill
P.box(x0 + 0.13, x1 - 0.13, NY - 0.015, NY + 0.005, 0.22, 0.90, mi=DARK)             # lower panel
pane(CUT_N, FRONT, rect(x0 + 0.13, x1 - 0.13, 1.05, 1.90), NY - YW + 0.03, "dark_room_frame", DARK)
for a, b, za, zb in ((x0 - 0.06, x0, 0.0, 2.11), (x1, x1 + 0.06, 0.0, 2.11), (x0, x1, 2.05, 2.11)):   # casing
    P.box(a, b, YW - 0.02, YW + 0.01, za, zb, mi=PALE)
wx0, wx1, wz0, wz1 = 3.70, 4.30, 1.00, 2.00    # window 0.60 x 1.00, sill 1.00
CUT_N.prism(rect(wx0, wx1, wz0, wz1), D(0.25), D(-0.05), "y", mi=(CLAP, PALE, PALE))
pane(CUT_N, FRONT, rect(wx0 + 0.05, wx1 - 0.05, wz0 + 0.05, wz1 - 0.05), 0.09, "dark_room", PALE)
P.box(wx0 + 0.05, wx1 - 0.05, YW + 0.05, YW + 0.09, 1.48, 1.53, mi=PALE)             # meeting rail
P.box(wx0 - 0.06, wx1 + 0.06, YW - 0.04, YW + 0.05, wz0 - 0.05, wz0 + 0.015, mi=PALE)   # sill
for a, b, za, zb in ((wx0 - 0.06, wx0, wz0, wz1 + 0.06), (wx1, wx1 + 0.06, wz0, wz1 + 0.06),
                     (wx0, wx1, wz1, wz1 + 0.06)):
    P.box(a, b, YW - 0.02, YW + 0.01, za, zb, mi=PALE)
P.box(HW, NEWS_X1 + 0.03, YW - 0.10, YW + 0.01, 2.80, NEWS_F + 0.02, mi=PALE)        # fascia board
P.box(NEWS_X1 - 0.10, NEWS_X1 + 0.02, YW - 0.02, YW + 0.01, SKIRT, 2.80, mi=PALE)    # corner board

# ---------------------------------------------------------------------------
# Build objects (boolean the cut shells)
# ---------------------------------------------------------------------------


def cut_shell(shell, cut, name):
    walls = shell.to_object(name, col)
    cutters = cut.to_object(name + "_Cutters", col)
    mod = walls.modifiers.new("Openings", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    solvers = [i.identifier for i in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items]
    mod.solver = "EXACT" if "EXACT" in solvers else solvers[0]
    mod.use_self = True                     # nested frame/glass cutters overlap
    mod.material_mode = "INDEX"             # cutter faces keep their material index
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


main = cut_shell(MAIN, CUT_M, "DB_Main")
news = cut_shell(NEWS, CUT_N, "DB_News")
assign_atlas_uvs(main)
assign_atlas_uvs(news)
REARX.to_object("DB_RearExt", col)
P.to_object("DB_Parts", col)

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Democrat building built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)")
# Materials, baked lighting and GLB export: run democrat_building_bake.py (it runs this file first).
