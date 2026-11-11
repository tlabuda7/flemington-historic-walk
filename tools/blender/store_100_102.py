"""
store_100_102.py - builds the auto supplies store, 100-102 Main St, Flemington (east side, old
no. 532): a 3-storey frame store, 30 ft high, as on the Sept 1921 Sanborn map ("Auto
Supplies"): a closed shop front on the ground floor, built out to the front line, with two
open gallery tiers above it (owner decision 2026-11-11, front form (a)).

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/store_100_102.py").read())

Every run deletes and rebuilds the "Store100102" collection. Materials, lightmap bake and GLB
export: store_100_102_bake.py (runs this file first). Pattern: democrat_building.py (north
neighbour): one bmesh per part, a material index per face, closed shells cut by nested boolean
pockets whose faces keep the cutter's material index.

Sources: PLAN.md "Auto supplies store (100-102 Main St, old no. 532)". No photo of this front
exists: everything on the front is a PLAIN GUESS on the map's footprint (owner decisions
2026-11-11): square posts, plain rails with square balusters, plain boxed cornice, no
brackets, no sign, no lettering, no awning; the show windows show a plain dim shop.

Windows (PLAN.md "E. Windows that don't read as flat black"): every pane is ONE glass face
(material Glass -> exported as `glass`) 4 cm in front of a window back: the back of the pane's
boolean pocket, with atlas UVs into assets/textures/shared/window_backs.jpg (upstairs:
dwelling rooms, lace, half-drawn blinds, one dark room; show windows and the shop doors: the
dim shop cells).

Coordinates (metres, Blender Z-up), origin = scene (10.30, 0.15, 52.01), rotation 0 -90 0:
    X  along the street, +X = south (106, party wall), -X = north (Democrat building, News)
    Y  depth: y = 0 is the front line (shop front, gallery posts); main wall 2.16; rear 18.68;
       the cornice reaches y = -0.35; rear porch to 20.63
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
HW = 3.71               # half width (7.42, 1921 map)
YM = 2.16               # main wall (behind the front strip)
YR = 18.68              # rear wall
YP = 20.63              # rear porch edge
SKIRT = -0.20
RF, RR = 9.14, 8.50     # shed roof of the main body: at the main wall, at the rear (map: 30 ft)
BUMP = (-5.27, 9.48, 15.81)          # north bump: outer face X, Y from, Y to
COURT = (1.55, 11.02)                # light court: X from (to HW), Y from (to YR)
SHOP_T = 3.30                        # top of the shop front (fascia 2.95-3.30)
DECKS = ((3.30, 3.50), (6.15, 6.35)) # gallery decks (2nd, 3rd floor)
CB, CT = 8.84, 9.14                  # boxed cornice underside, top
CPROJ = 0.35                         # cornice projection (front and north return)
POST_X = (-3.60, -1.20, 1.20, 3.60)  # gallery posts, 0.14 square
POST = 0.14
RAIL_H = 0.90                        # rail top above the deck
BAL, BAL_C = 0.03, 0.13              # balusters: size, centres


def roof_z(y):
    """Height of the main body's shed roof at depth y."""
    return RF - (y - YM) * (RF - RR) / (YR - YM)


CLAP, TRIM, SHOP, DECK, ROOF, GLASS, WBACK = range(7)
NAMES = ["Clapboard", "Trim", "Shopfront", "Deck", "Roof", "Glass", "WindowBack"]


# ---------------------------------------------------------------------------
# Materials (plain stand-ins; store_100_102_bake.py swaps in the textures)
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


COLOURS = ["#B4AC98", "#D8D0BC", "#3A3A2E", "#8E8B82", "#5A3D34", "#1A1916", "#3a332c"]
MATS = [plain("SS_" + n, c) for n, c in zip(NAMES, COLOURS)]

# ---------------------------------------------------------------------------
# Mesh builder: one bmesh, a material index per face (as democrat_building.py)
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

    def prism(self, pts, d0, d1, axis="y", mi=TRIM):
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
        return a + b

    def face(self, pts, d, axis, out, mi=GLASS):
        """One flat face (a glass pane) with its normal pointing out (+-axis)."""
        f = self.bm.faces.new([self.bm.verts.new(self._pt(axis, u, d, v)) for u, v in pts])
        f.material_index = mi
        f.normal_update()
        want = Vector((0, out, 0)) if axis == "y" else Vector((out, 0, 0))
        if f.normal.dot(want) < 0:
            f.normal_flip()

    def box(self, x0, x1, y0, y1, z0, z1, mi=TRIM):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, "y", mi)

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


col = fresh_collection("Store100102")
P = MB()                       # all added parts
MAIN, CUT_M = MB(), MB()       # main body (clapboard shell, with the bump and the light court)
STRIP, CUT_S = MB(), MB()      # ground floor of the front strip (the shop front)

# Each wall: (axis, outer face depth, outward sign)
FRONT_S = ("y", 0.0, -1)       # shop front
FRONT_M = ("y", YM, -1)        # main wall inside the galleries
NORTH = ("x", -HW, -1)         # north wall in front of the bump
BUMP_N = ("x", BUMP[0], -1)    # north face of the bump
REAR = ("y", YR, 1)


def Dfun(wall):
    axis, face, out = wall
    return axis, (lambda k: face + out * k)   # k > 0 outside the wall, k < 0 inside


def wbox(wall, u0, u1, k0, k1, z0, z1, mi=TRIM):
    """Box on a wall: u along the wall, k = distance out of the wall face, z up."""
    axis, D = Dfun(wall)
    P.prism(rect(u0, u1, z0, z1), D(k0), D(k1), axis, mi)


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
# main body: plan outline with the north bump and the south-east light court, extruded up,
# then the top tilted into the shed roof falling to the rear
PLAN_PTS = [(-HW, YM), (HW, YM), (HW, COURT[1]), (COURT[0], COURT[1]), (COURT[0], YR), (-HW, YR),
            (-HW, BUMP[2]), (BUMP[0], BUMP[2]), (BUMP[0], BUMP[1]), (-HW, BUMP[1])]
verts = MAIN.prism(PLAN_PTS, SKIRT, RF, axis="z", mi=(CLAP, ROOF, CLAP))
for v in verts:
    if v.co.z > RF - 0.01:
        v.co.z = roof_z(v.co.y)
# front strip, ground floor: shop front at y = 0, its top under the 2nd-floor deck. Sides of
# the outline: bottom, south (x1), top, north (x0)
STRIP.prism(rect(-HW, HW, SKIRT, SHOP_T), 0.0, YM, "y", mi=(SHOP, CLAP, [CLAP, CLAP, DECK, CLAP]))

# ---------------------------------------------------------------------------
# Plain 1-over-1 windows and half-glazed doors (all GUESS)
# ---------------------------------------------------------------------------
FR = 0.06          # sash frame width
D_SASH = 0.06      # sash set back
D_GLASS = 0.10     # glass behind the wall face


def window(C, wall, cu, w, z0, z1, cell, wall_mat=CLAP):
    axis, D = Dfun(wall)
    C.prism(rect(cu - w / 2, cu + w / 2, z0, z1), D(0.25), D(-D_SASH), axis, mi=(wall_mat, TRIM, TRIM))
    zm = (z0 + z1) / 2 + 0.03                                          # meeting rail
    frame = (cu - w / 2 + FR, cu + w / 2 - FR, z0 + FR, z1 - FR)
    pane(C, wall, rect(frame[0], frame[1], zm + 0.025, frame[3]), D_GLASS, cell, TRIM, frame)
    pane(C, wall, rect(frame[0], frame[1], frame[2], zm - 0.025), D_GLASS, cell, TRIM, frame)
    # flat casing (0.08) and sill board (top 1.5 cm above the reveal floor: no coplanar faces)
    wbox(wall, cu - w / 2 - 0.08, cu - w / 2, 0.0, 0.022, z0 + 0.015, z1)
    wbox(wall, cu + w / 2, cu + w / 2 + 0.08, 0.0, 0.022, z0 + 0.015, z1)
    wbox(wall, cu - w / 2 - 0.08, cu + w / 2 + 0.08, 0.0, 0.03, z1, z1 + 0.09)
    wbox(wall, cu - w / 2 - 0.10, cu + w / 2 + 0.10, 0.0, 0.06, z0 - 0.05, z0 + 0.015)


def door(C, wall, cu, w, z0, z1, cell):
    """Half-glazed door (gallery doors): leaf set back 0.06, raised lower panel, glass above,
    flat casing, threshold board."""
    axis, D = Dfun(wall)
    C.prism(rect(cu - w / 2, cu + w / 2, z0, z1), D(0.25), D(-0.06), axis, mi=(CLAP, SHOP, TRIM))
    a, b = cu - w / 2 + 0.12, cu + w / 2 - 0.12
    wbox(wall, a, b, -0.06, -0.045, z0 + 0.15, z0 + 0.88, mi=SHOP)
    pane(C, wall, rect(a, b, z0 + 1.02, z1 - 0.12), 0.09, cell, SHOP)
    wbox(wall, cu - w / 2 - 0.08, cu - w / 2, 0.0, 0.022, z0, z1)
    wbox(wall, cu + w / 2, cu + w / 2 + 0.08, 0.0, 0.022, z0, z1)
    wbox(wall, cu - w / 2 - 0.08, cu + w / 2 + 0.08, 0.0, 0.03, z1, z1 + 0.09)
    wbox(wall, cu - w / 2, cu + w / 2, -0.06, 0.04, z0 - 0.03, z0 + 0.02, mi=DECK)


# gallery walls (main wall y = 2.16): per floor a door at X 0 and two windows at X +-2.20
# (0.85 x 1.70, sill 0.75 above the deck). Dwelling rooms, no two alike side by side.
GAL_CELLS = (("lace", "dark_room_frame", "blind_cream_half"),
             ("blind_green_low", "door", "lace_blind_cream"))
for (d0, d1), (cn, cd, cs) in zip(DECKS, GAL_CELLS):
    top = min(d1 + 0.75 + 1.70, CB - 0.12)
    window(CUT_M, FRONT_M, -2.20, 0.85, d1 + 0.75, top, cn)
    window(CUT_M, FRONT_M, 2.20, 0.85, d1 + 0.75, top, cs)
    door(CUT_M, FRONT_M, 0.0, 0.85, d1 + 0.02, d1 + 2.10, "dark_room_frame" if cd == "door" else "dark_room")

# north wall (seen above the News lean-to and the Democrat building): two windows per upper
# floor, at Y 5 (main wall) and Y 13 (the bump's face)
for (d0, d1), cells in zip(DECKS, (("blind_cream_low", "curtains_beige"), ("lace_blind_green", "dark_room"))):
    window(CUT_M, NORTH, 5.0, 0.85, d1 + 0.75, d1 + 2.45, cells[0])
    window(CUT_M, BUMP_N, 13.0, 0.85, d1 + 0.75, d1 + 2.45, cells[1])

# rear wall (X -3.71 ... 1.55, onto the rear porch): three plain windows per floor
for z0, cells in ((0.90, ("dark_room", "curtains_olive", "dark_room_frame")),
                  (4.25, ("blind_cream_high", "dark_room", "lace")),
                  (7.10, ("dark_room_frame", "blind_green_high", "dark_room"))):
    for x, cell in zip((-2.60, -1.10, 0.40), cells):
        window(CUT_M, REAR, x, 0.85, z0, z0 + 1.60, cell)

# ---------------------------------------------------------------------------
# Shop front (GUESS, plain; face y = 0, Z 0 ... 3.30): corner boards, two show windows (riser
# 0.55, glass to 2.45, plain transom band 2.50-2.90), a centre pair of half-glazed doors
# recessed 0.60, plain fascia 2.95-3.30 projecting 0.10. No sign, no lettering, no awning.
# ---------------------------------------------------------------------------
axis, D = Dfun(FRONT_S)
for (x0, x1), cell in (((-3.35, -0.75), "shop_a"), ((0.75, 3.35), "shop_b")):
    WZ0, WZ1 = 0.55, 2.45
    CUT_S.prism(rect(x0, x1, WZ0, WZ1), D(0.25), D(-0.05), "y", mi=(SHOP, SHOP, SHOP))
    f, bar = 0.06, 0.05
    xm = (x0 + x1) / 2
    frame = (x0 + f, x1 - f, WZ0 + f, WZ1 - f)
    for a, b in ((x0 + f, xm - bar / 2), (xm + bar / 2, x1 - f)):
        pane(CUT_S, FRONT_S, rect(a, b, WZ0 + f, WZ1 - f), 0.09, cell, SHOP, frame)
    P.box(x0 - 0.05, x1 + 0.05, -0.07, 0.0, WZ0 - 0.05, WZ0 + 0.015, mi=SHOP)       # sill ledge
    P.box(x0 + 0.08, x1 - 0.08, -0.018, 0.0, 0.10, WZ0 - 0.10, mi=SHOP)              # riser panel
    P.box(x0, x1, -0.02, 0.0, 2.50, 2.90, mi=SHOP)                                   # transom band
    P.box(x0 - 0.03, x1 + 0.03, -0.04, 0.0, 2.45, 2.50, mi=SHOP)                     # head moulding

# centre doors: recess 0.60 deep, a pair of half-glazed leaves, transom light
x0, x1 = -0.65, 0.65
DY = 0.60
DOOR_T, BAR_T, REC_T = 2.15, 2.21, 2.45
CUT_S.prism(rect(x0, x1, -0.10, REC_T), D(0.25), D(-DY), "y", mi=(SHOP, SHOP, SHOP))
P.box(x0, x1, -0.02, DY + 0.01, -0.10, 0.02, mi=DECK)                                # recess floor
xm = 0.0
dframe = (x0 + 0.05 + 0.11, x1 - 0.05 - 0.11, 1.05, 1.98)       # one room view across both leaves


def leaf(a, b, cell, frame):
    P.box(a + 0.11, b - 0.11, DY - 0.015, DY + 0.005, 0.22, 0.90, mi=SHOP)
    pane(CUT_S, FRONT_S, rect(a + 0.11, b - 0.11, 1.05, 1.98), DY + 0.03, cell, SHOP, frame)


leaf(x0 + 0.05, xm - 0.01, "door", dframe)
leaf(xm + 0.01, x1 - 0.05, "door", dframe)
P.box(xm - 0.02, xm + 0.02, DY - 0.025, DY + 0.005, 0.02, DOOR_T, mi=SHOP)           # astragal
for a, b in ((x0, x0 + 0.05), (x1 - 0.05, x1)):                                     # door frame
    P.box(a, b, DY - 0.03, DY + 0.005, 0.02, REC_T, mi=SHOP)
P.box(x0 + 0.05, x1 - 0.05, DY - 0.04, DY + 0.005, DOOR_T, BAR_T, mi=SHOP)           # transom bar
pane(CUT_S, FRONT_S, rect(x0 + 0.08, x1 - 0.08, BAR_T + 0.03, REC_T - 0.04), DY + 0.03, "transom", SHOP)
P.box(x0 - 0.03, x1 + 0.03, -0.04, 0.0, REC_T, 2.50, mi=SHOP)                        # head moulding
P.box(x0 - 0.10, x1 + 0.10, -0.02, 0.0, 2.50, 2.90, mi=SHOP)                         # band over the doors

P.box(-HW, HW, -0.10, 0.0, 2.95, SHOP_T, mi=SHOP)                                    # fascia
P.box(-HW - 0.005, HW, -0.13, -0.10, 3.20, SHOP_T, mi=SHOP)                          # its cap strip
for a, b in ((-HW, -HW + 0.15), (HW - 0.15, HW)):                                    # corner boards
    P.box(a, b, -0.022, 0.0, SKIRT, 2.95, mi=TRIM)

# ---------------------------------------------------------------------------
# Galleries: two decks, four plain square posts per tier, plain rails with square balusters
# along the front and across both open ends; boxed cornice over the top tier
# ---------------------------------------------------------------------------
# 2nd-floor deck lies on the shop (edge = trim); 3rd-floor deck: a full slab
P.box(-HW, HW, 0.0, YM, DECKS[0][0], DECKS[0][1], mi=(TRIM, TRIM, [DECK, TRIM, DECK, TRIM]))
P.box(-HW, HW, 0.0, YM, DECKS[1][0], DECKS[1][1], mi=(TRIM, TRIM, [DECK, TRIM, DECK, TRIM]))
TIERS = ((DECKS[0][1], DECKS[1][0]), (DECKS[1][1], CB))
RY0, RY1 = 0.03, 0.11            # rail depth (centred on the posts)
BY0, BY1 = 0.07 - BAL / 2, 0.07 + BAL / 2


def rail_run(along, fixed, a0, a1, zt):
    """Top rail, bottom rail and balusters from a0 to a1. along 'x': front rail at y = fixed
    (centre); along 'y': end rail at x = fixed."""
    def bx(u0, u1, w0, w1, z0, z1):
        if along == "x":
            P.box(u0, u1, fixed - 0.07 + w0, fixed - 0.07 + w1, z0, z1, mi=TRIM)
        else:
            P.prism(rect(u0, u1, z0, z1), fixed - 0.07 + w0, fixed - 0.07 + w1, "x", mi=TRIM)
    bx(a0, a1, RY0, RY1, zt + RAIL_H - 0.06, zt + RAIL_H)
    bx(a0, a1, RY0 + 0.01, RY1 - 0.01, zt + 0.05, zt + 0.11)
    n = int((a1 - a0) / BAL_C)
    step = (a1 - a0) / (n + 1)
    for i in range(1, n + 1):
        u = a0 + step * i
        bx(u - BAL / 2, u + BAL / 2, BY0 - 0.07 + 0.07, BY1 - 0.07 + 0.07, zt + 0.11, zt + RAIL_H - 0.06)


for zt, zb in TIERS:
    for xp in POST_X:
        P.box(xp - POST / 2, xp + POST / 2, 0.0, POST, zt, zb, mi=TRIM)
    for a, b in zip(POST_X[:-1], POST_X[1:]):
        rail_run("x", 0.07, a + POST / 2, b - POST / 2, zt)
    for xe in (POST_X[0], POST_X[-1]):                 # open ends: rail from the post to the wall
        rail_run("y", xe, POST, YM, zt)
    # corner board on the main wall's north-west corner (seen through the open north end)
    P.box(-HW, -HW + 0.12, YM - 0.022, YM, zt, zb, mi=TRIM)

# boxed cornice (plain, no brackets): front and a short return on the north side; flat tin top.
# Outline sides: bottom (soffit), south end, top, north end
P.box(-HW - CPROJ, HW, -CPROJ, YM, CB, CT, mi=(TRIM, TRIM, [TRIM, TRIM, ROOF, TRIM]))
P.box(-HW - CPROJ, -HW, YM, YM + CPROJ, CB, CT, mi=(TRIM, TRIM, [TRIM, TRIM, ROOF, TRIM]))
P.box(-HW - CPROJ - 0.04, HW, -CPROJ - 0.04, -CPROJ, CT - 0.11, CT + 0.015, mi=TRIM)          # crown strip
P.prism(rect(-CPROJ - 0.04, YM + CPROJ, CT - 0.11, CT + 0.015), -HW - CPROJ - 0.04, -HW - CPROJ, "x", mi=TRIM)
P.box(-HW - CPROJ, -HW, YM + CPROJ, YM + CPROJ + 0.04, CT - 0.11, CT + 0.015, mi=TRIM)        # return end
P.box(-HW, HW, -0.05, 0.0, CB - 0.16, CB, mi=TRIM)                                           # frieze board

# corner boards of the north side (main wall rear corner, bump corners); frieze board under
# the eaves along the north side
for y, x, z1 in ((YR, -HW, roof_z(YR)), (BUMP[1], BUMP[0], roof_z(BUMP[1])), (BUMP[2], BUMP[0], roof_z(BUMP[2]))):
    s = -1 if y > 10 and y != BUMP[1] else 1           # board on the wall face away from the corner
    P.box(x - 0.022, x, y if s > 0 else y - 0.12, y + 0.12 if s > 0 else y, SKIRT, z1 - 0.02, mi=TRIM)
P.prism([(YM + CPROJ + 0.04, roof_z(YM + 0.4) - 0.20), (BUMP[1], roof_z(BUMP[1]) - 0.20),
         (BUMP[1], roof_z(BUMP[1]) - 0.02), (YM + CPROJ + 0.04, roof_z(YM + 0.4) - 0.02)],
        -HW - 0.025, -HW, "x", mi=TRIM)
P.prism([(BUMP[1], roof_z(BUMP[1]) - 0.20), (BUMP[2], roof_z(BUMP[2]) - 0.20),
         (BUMP[2], roof_z(BUMP[2]) - 0.02), (BUMP[1], roof_z(BUMP[1]) - 0.02)],
        BUMP[0] - 0.025, BUMP[0], "x", mi=TRIM)

# ---------------------------------------------------------------------------
# Rear porch (3 tiers, open, plain; out of view from the street): two decks, a flat roof,
# four plain posts
# ---------------------------------------------------------------------------
for z0, z1 in DECKS:
    P.box(-HW, HW, YR, YP, z0, z1, mi=(TRIM, TRIM, [DECK, TRIM, DECK, TRIM]))
P.box(-HW, HW, YR, YP, 8.80, 9.00, mi=(TRIM, TRIM, [DECK, TRIM, ROOF, TRIM]))
for xp in POST_X:
    for z0, z1 in ((0.0, DECKS[0][0]), (DECKS[0][1], DECKS[1][0]), (DECKS[1][1], 8.80)):
        P.box(xp - POST / 2, xp + POST / 2, YP - POST, YP, z0, z1, mi=TRIM)

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


main = cut_shell(MAIN, CUT_M, "SS_Main")
strip = cut_shell(STRIP, CUT_S, "SS_Strip")
assign_atlas_uvs(main)
assign_atlas_uvs(strip)
P.to_object("SS_Parts", col)

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("100-102 Main built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)")
# Materials, baked lighting and GLB export: run store_100_102_bake.py (it runs this file first).
