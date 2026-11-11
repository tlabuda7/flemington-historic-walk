"""
store_106.py - builds the corner drugstore, 106 Main St, Flemington (east side, old no. 531,
north corner of Higgins Ave): a 3-storey frame drugstore, 30 ft high, as on the Sept 1921
Sanborn map ("Drugs", "3", 30'), with the map's three-tier open front porch (owner decisions
2026-11-11: porch plain, four square posts per tier, plain rails; map-true position; no
lettering; gabled bracketed cornice and pale clapboard front with three windows per upper floor
and louvred blinds as in the 1890s photo; show windows = plain dim shop).

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/store_106.py").read())

Every run deletes and rebuilds the "Store106" collection. Materials, lightmap bake and GLB
export: store_106_bake.py (runs this file first). Pattern: store_100_102.py (north neighbour):
one bmesh per part, a material index per face, a closed shell cut by nested boolean pockets
whose faces keep the cutter's material index.

Windows (PLAN.md "E. Windows that don't read as flat black"): every pane is ONE glass face
(material Glass -> exported as `glass`) 4 cm in front of a window back: the back of the pane's
boolean pocket, with atlas UVs into assets/textures/shared/window_backs.jpg (upstairs and side
windows: dwelling rooms; show windows and the shop doors: the atlas's dim shop cells).
Louvred blinds: the `louvre` cell of assets/textures/county-hotel/signs_atlas.jpg (reused).

Coordinates (metres, Blender Z-up), origin = scene (8.06, 0.15, 58.80) = centre of the porch
front, rotation 0 -90 0:
    X  along the street, +X = south (Higgins Ave), -X = north (100-102, party wall)
    Y  depth: y = 0 is the porch front (posts); main front wall 2.24; rear wall 20.89; rear
       porch to 22.87; the gable rakes reach y = 1.72
    Z  up from the sidewalk top; walls skirt down to -0.20
Map lines (sheet 3): north wall X -3.09, south wall X +3.09.

Deviation from the spec's heights (to keep the photographed frieze and brackets visible above
the porch roof): porch roof slab 8.24-8.38 (spec 8.60-8.80), frieze 8.38-8.84, 2nd-floor window
heads 5.80 (under the 3rd-floor deck at 6.05), 3rd-floor heads 8.12.
"""

import json
import math
import bpy
import bmesh
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md "Corner drugstore (106 Main St ...)": placement, massing, elevations)
# ---------------------------------------------------------------------------
HW = 3.09               # half width (6.18 between the map's wall lines)
YM = 2.24               # main front wall
YR = 20.89              # rear wall
YP = 22.87              # rear porch edge
SKIRT = -0.20
RF, RR = 9.14, 8.50     # shed roof of the main body: at the front wall, at the rear (map: 30 ft)
SHOP_T = 3.20           # top of the shop front (fascia 2.95-3.20)
DECKS = ((3.15, 3.35), (6.05, 6.25))  # front porch decks (2nd, 3rd floor)
PROOF = (8.24, 8.38)                  # front porch roof slab
FB, CB, CT = 8.38, 8.84, 9.14         # frieze bottom, boxed cornice underside, top
CPROJ = 0.45                          # cornice projection (front, first 0.6 m of the south return)
APEX = 9.75                           # gable apex
GHW = 1.30                            # gable half width at the rake feet
POST_X = (-3.00, -1.00, 1.00, 3.00)   # porch posts, 0.16 square, centred on y 0.08
POST = 0.16
RAIL_H = 0.90                         # rail top above the deck
BAL, BAL_C = 0.03, 0.13               # balusters: size, centres
RDECKS = ((3.30, 3.50), (6.15, 6.35))  # rear porch decks: level with 100-102's rear porch
RROOF = (8.80, 9.00)


def roof_z(y):
    """Height of the main body's shed roof at depth y."""
    return RF - (y - YM) * (RF - RR) / (YR - YM)


CLAPF, CLAPS, TRIM, SHOP, DECK, ROOF, GLASS, WBACK, BLIND = range(9)
NAMES = ["ClapFront", "ClapSide", "Trim", "Shopfront", "Deck", "Roof", "Glass", "WindowBack", "Blinds"]


# ---------------------------------------------------------------------------
# Materials (plain stand-ins; store_106_bake.py swaps in the textures)
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


COLOURS = ["#D6D0BE", "#8C8470", "#D8D0BC", "#2F3A2C", "#8E8B82", "#5A3D34", "#1A1916", "#3a332c", "#34432F"]
MATS = [plain("DS_" + n, c) for n, c in zip(NAMES, COLOURS)]

# ---------------------------------------------------------------------------
# Mesh builder: one bmesh, a material index per face (as store_100_102.py)
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


col = fresh_collection("Store106")
P = MB()                       # all added parts
MAIN, CUT_M = MB(), MB()       # main body: one closed clapboard shell, cut by the openings

# Each wall: (axis, outer face depth, outward sign)
FRONT = ("y", YM, -1)          # main front wall, behind the porch
SOUTH = ("x", HW, 1)           # Higgins Ave side
REAR = ("y", YR, 1)


def Dfun(wall):
    axis, face, out = wall
    return axis, (lambda k: face + out * k)   # k > 0 outside the wall, k < 0 inside


def wbox(wall, u0, u1, k0, k1, z0, z1, mi=TRIM):
    """Box on a wall: u along the wall, k = distance out of the wall face, z up."""
    axis, D = Dfun(wall)
    P.prism(rect(u0, u1, z0, z1), D(k0), D(k1), axis, mi)


# ---------------------------------------------------------------------------
# Window backs and glass (as store_100_102.py)
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
    """Remember a window back so its faces get `cell`'s atlas UVs after the booleans."""
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


# Louvred blinds: county-hotel/signs_atlas.jpg, region `louvre` (px 0,0 - 256,640) on the leaf
# face, a plain patch of the `green` region (px 704,256 - 1024,512) on its edges
LOUVRE_UV = (0.0 + 2 / 1024, 1 - 640 / 1024 + 2 / 1024, 256 / 1024 - 2 / 1024, 1.0 - 2 / 1024)
GREEN_UV = (0.84, 0.62)
SHUTTERS = []          # (u0, u1, z0, z1) of each leaf on the front wall


def assign_blind_uvs(obj):
    me = obj.data
    uvl = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    U0, V0, U1, V1 = LOUVRE_UV
    for p in me.polygons:
        if p.material_index != BLIND:
            continue
        c, n = p.center, p.normal
        hit = None
        if n.y < -0.9:
            hit = next((s for s in SHUTTERS if s[0] - 1e-3 <= c.x <= s[1] + 1e-3 and s[2] - 1e-3 <= c.z <= s[3] + 1e-3), None)
        for li in p.loop_indices:
            if hit:
                co = me.vertices[me.loops[li].vertex_index].co
                t = (co.x - hit[0]) / (hit[1] - hit[0])
                s = (co.z - hit[2]) / (hit[3] - hit[2])
                uvl.data[li].uv = (U0 + (U1 - U0) * t, V0 + (V1 - V0) * s)
            else:
                uvl.data[li].uv = GREEN_UV


# ---------------------------------------------------------------------------
# Shell: the main body, Y 2.24 ... 20.89, top tilted into the shed roof falling to the rear.
# Outline sides: front (pale), south, rear, north (the darker side clapboard)
# ---------------------------------------------------------------------------
PLAN_PTS = [(-HW, YM), (HW, YM), (HW, YR), (-HW, YR)]
verts = MAIN.prism(PLAN_PTS, SKIRT, RF, axis="z", mi=(CLAPS, ROOF, [CLAPF, CLAPS, CLAPS, CLAPS]))
for v in verts:
    if v.co.z > RF - 0.01:
        v.co.z = roof_z(v.co.y)

# ---------------------------------------------------------------------------
# Windows and doors
# ---------------------------------------------------------------------------
FR = 0.06          # sash frame width
D_SASH = 0.06      # sash set back
D_GLASS = 0.10     # glass behind the wall face
CAS = 0.07         # flat casing width


def shutters(wall, cu, w, z0, z1, leaf=0.42):
    """Open louvred blinds flat against the wall beside the casing (front wall only)."""
    for s in (-1, 1):
        u0, u1 = sorted((cu + s * (w / 2 + CAS), cu + s * (w / 2 + CAS + leaf)))
        wbox(wall, u0, u1, 0.012, 0.042, z0, z1, mi=BLIND)
        SHUTTERS.append((u0, u1, z0, z1))


def head(wall, cu, w, z1, hood):
    """Head over an opening: a shallow segmental hood board 0.10 proud (2nd floor) or a flat
    head board (3rd floor, sides and rear)."""
    a = w / 2 + CAS + 0.03
    if hood:
        axis, D = Dfun(wall)
        n = 6
        pts = [(cu - a, z1), (cu + a, z1)]
        for i in range(n + 1):                      # top edge: segmental arc, rise 0.12
            t = i / n
            pts.append((cu + a - 2 * a * t, z1 + 0.10 + 0.12 * math.sin(math.pi * t)))
        P.prism(pts, D(0.0), D(0.10), axis, mi=TRIM)
    else:
        wbox(wall, cu - a, cu + a, 0.0, 0.04, z1, z1 + 0.10)


def window(C, wall, cu, w, z0, z1, cell, wall_mat=CLAPF, hood=False, blinds=False):
    """1-over-1 sash window in a pocket: sash frame, two panes (glass + window back), casing,
    sill, head (hood or board), optional open louvred blinds."""
    axis, D = Dfun(wall)
    C.prism(rect(cu - w / 2, cu + w / 2, z0, z1), D(0.25), D(-D_SASH), axis, mi=(wall_mat, TRIM, TRIM))
    zm = (z0 + z1) / 2 + 0.03                                          # meeting rail
    frame = (cu - w / 2 + FR, cu + w / 2 - FR, z0 + FR, z1 - FR)
    pane(C, wall, rect(frame[0], frame[1], zm + 0.025, frame[3]), D_GLASS, cell, TRIM, frame)
    pane(C, wall, rect(frame[0], frame[1], frame[2], zm - 0.025), D_GLASS, cell, TRIM, frame)
    wbox(wall, cu - w / 2 - CAS, cu - w / 2, 0.0, 0.022, z0 + 0.015, z1)
    wbox(wall, cu + w / 2, cu + w / 2 + CAS, 0.0, 0.022, z0 + 0.015, z1)
    head(wall, cu, w, z1, hood)
    wbox(wall, cu - w / 2 - 0.10, cu + w / 2 + 0.10, 0.0, 0.06, z0 - 0.05, z0 + 0.015)
    if blinds:
        shutters(wall, cu, w, z0, z1)


def door(C, wall, cu, w, z0, z1, cell, wall_mat=CLAPF, hood=False, blinds=False):
    """Half-glazed door: leaf set back 0.06, raised lower panel, glass above, casing, head,
    threshold board, optional blinds."""
    axis, D = Dfun(wall)
    C.prism(rect(cu - w / 2, cu + w / 2, z0, z1), D(0.25), D(-0.06), axis, mi=(wall_mat, SHOP, TRIM))
    a, b = cu - w / 2 + 0.12, cu + w / 2 - 0.12
    wbox(wall, a, b, -0.06, -0.045, z0 + 0.15, z0 + 0.88, mi=SHOP)
    pane(C, wall, rect(a, b, z0 + 1.02, z1 - 0.12), 0.09, cell, SHOP)
    wbox(wall, cu - w / 2 - CAS, cu - w / 2, 0.0, 0.022, z0, z1)
    wbox(wall, cu + w / 2, cu + w / 2 + CAS, 0.0, 0.022, z0, z1)
    head(wall, cu, w, z1, hood)
    wbox(wall, cu - w / 2, cu + w / 2, -0.06, 0.04, z0 - 0.03, z0 + 0.02, mi=DECK)
    if blinds:
        shutters(wall, cu, w, z0, z1)


# front, 2nd floor (1890s photo): three tall windows with segmental hoods and louvred blinds;
# the middle one a half-glazed door onto the porch deck (guess)
W2 = (4.10, 5.80)
window(CUT_M, FRONT, -1.95, 0.85, *W2, "lace_blind_cream", hood=True, blinds=True)
window(CUT_M, FRONT, 1.95, 0.85, *W2, "curtains_olive", hood=True, blinds=True)
door(CUT_M, FRONT, 0.0, 0.85, DECKS[0][1] + 0.02, W2[1], "dark_room_frame", hood=True, blinds=True)
# front, 3rd floor: a little shorter, flat head boards, blinds; middle = door (guess)
W3 = (6.90, 8.12)
window(CUT_M, FRONT, -1.95, 0.85, *W3, "blind_green_half", blinds=True)
window(CUT_M, FRONT, 1.95, 0.85, *W3, "lace", blinds=True)
door(CUT_M, FRONT, 0.0, 0.85, DECKS[1][1] + 0.02, W3[1], "dark_room", blinds=True)

# south wall (Higgins Ave): blank for its first 8 m (photo); beyond, three plain 1/1 windows
# per upper floor at Y 11, 14.5, 18, and a side door (Y 12) and a window (Y 16) on the ground
# floor (all guess)
for (z0, z1), cells in (((4.20, 5.80), ("blind_cream_high", "dark_room", "curtains_beige")),
                        ((6.90, 8.00), ("lace_blind_green", "blind_cream_low", "dark_room_frame"))):
    for y, cell in zip((11.0, 14.5, 18.0), cells):
        window(CUT_M, SOUTH, y, 0.85, z0, z1, cell, wall_mat=CLAPS)
door(CUT_M, SOUTH, 12.0, 0.90, 0.02, 2.20, "door", wall_mat=CLAPS)
window(CUT_M, SOUTH, 16.0, 0.85, 0.90, 2.40, "dark_room", wall_mat=CLAPS)

# rear wall (onto the rear porch): two plain windows per floor
for z0, z1, cells in ((0.90, 2.40, ("dark_room", "curtains_maroon_blind")),
                      (4.25, 5.85, ("lace_full_blind_cream", "dark_room_frame")),
                      (7.10, 8.10, ("blind_green_low", "dark_room"))):
    for x, cell in zip((-1.30, 1.30), cells):
        window(CUT_M, REAR, x, 0.85, z0, z1, cell, wall_mat=CLAPS)

# ---------------------------------------------------------------------------
# Shop front (GUESS on the photo's dark shop front; main wall y = 2.24, Z 0 ... 3.20):
# corner pilaster boards 0.20, two show windows X -2.75 ... -0.70 and 0.70 ... 2.75 (riser
# 0.55, glass to 2.45, plain transom band to 2.90), a centre pair of half-glazed doors
# X -0.60 ... 0.60 recessed 0.50, plain fascia 2.95-3.20. No sign, no lettering.
# ---------------------------------------------------------------------------
axis, D = Dfun(FRONT)
WZ0, WZ1 = 0.55, 2.45
for (x0, x1), cell in (((-2.75, -0.70), "shop_a"), ((0.70, 2.75), "shop_b")):
    CUT_M.prism(rect(x0, x1, WZ0, WZ1), D(0.25), D(-0.05), "y", mi=(SHOP, SHOP, SHOP))
    f, bar = 0.06, 0.05
    xm = (x0 + x1) / 2
    frame = (x0 + f, x1 - f, WZ0 + f, WZ1 - f)
    for a, b in ((x0 + f, xm - bar / 2), (xm + bar / 2, x1 - f)):
        pane(CUT_M, FRONT, rect(a, b, WZ0 + f, WZ1 - f), 0.09, cell, SHOP, frame)
    P.box(x0 - 0.05, x1 + 0.05, YM - 0.07, YM, WZ0 - 0.05, WZ0 + 0.015, mi=SHOP)       # sill ledge
    P.box(x0, x1, YM - 0.02, YM, SKIRT, WZ0 - 0.05, mi=SHOP)                          # riser
    P.box(x0 + 0.08, x1 - 0.08, YM - 0.035, YM - 0.02, 0.10, WZ0 - 0.12, mi=SHOP)     # its raised panel
    P.box(x0 - 0.03, x1 + 0.03, YM - 0.04, YM, WZ1, WZ1 + 0.05, mi=SHOP)              # head moulding

# centre doors: recess 0.50 deep, a pair of half-glazed leaves, transom light
x0, x1 = -0.60, 0.60
DY = 0.50
DOOR_T, BAR_T, REC_T = 2.15, 2.21, 2.45
CUT_M.prism(rect(x0, x1, -0.10, REC_T), D(0.25), D(-DY), "y", mi=(SHOP, SHOP, SHOP))
P.box(x0, x1, YM - 0.02, YM + DY + 0.01, -0.10, 0.02, mi=DECK)                         # recess floor
dframe = (x0 + 0.05 + 0.11, x1 - 0.05 - 0.11, 1.05, 1.98)       # one room view across both leaves
YD = YM + DY                                                    # door plane


def leaf(a, b, cell, frame):
    P.box(a + 0.11, b - 0.11, YD - 0.005, YD + 0.015, 0.22, 0.90, mi=SHOP)
    pane(CUT_M, FRONT, rect(a + 0.11, b - 0.11, 1.05, 1.98), DY + 0.03, cell, SHOP, frame)


leaf(x0 + 0.05, -0.01, "door", dframe)
leaf(0.01, x1 - 0.05, "door", dframe)
P.box(-0.02, 0.02, YD - 0.005, YD + 0.025, 0.02, DOOR_T, mi=SHOP)                     # astragal
for a, b in ((x0, x0 + 0.05), (x1 - 0.05, x1)):                                     # door frame
    P.box(a, b, YD - 0.005, YD + 0.03, 0.02, REC_T, mi=SHOP)
P.box(x0 + 0.05, x1 - 0.05, YD - 0.005, YD + 0.04, DOOR_T, BAR_T, mi=SHOP)           # transom bar
pane(CUT_M, FRONT, rect(x0 + 0.08, x1 - 0.08, BAR_T + 0.03, REC_T - 0.04), DY + 0.03, "transom", SHOP)
P.box(x0 - 0.03, x1 + 0.03, YM - 0.04, YM, REC_T, REC_T + 0.05, mi=SHOP)              # head moulding

# boards covering the rest of the ground-floor front: piers, transom band, fascia, pilasters
for a, b in ((-2.89, -2.75), (-0.70, -0.60), (0.60, 0.70), (2.75, 2.89)):
    P.box(a, b, YM - 0.02, YM, SKIRT, 2.95, mi=SHOP)
P.box(-2.89, 2.89, YM - 0.02, YM, 2.50, 2.95, mi=SHOP)                               # transom band
for a, b in ((-2.75, -0.70), (0.70, 2.75)):                                         # transom panels
    P.box(a + 0.06, b - 0.06, YM - 0.035, YM - 0.02, 2.57, 2.88, mi=SHOP)
P.box(-HW, HW, YM - 0.10, YM, 2.95, SHOP_T, mi=SHOP)                                 # fascia
P.box(-HW, HW, YM - 0.13, YM - 0.10, 3.10, SHOP_T, mi=SHOP)                          # its cap strip
for a, b in ((-HW, -HW + 0.20), (HW - 0.20, HW)):                                   # corner pilasters
    P.box(a, b, YM - 0.04, YM, SKIRT, 2.95, mi=TRIM)

# ---------------------------------------------------------------------------
# Three-tier open porch (map: 2.24 deep, "3", dashed front; form GUESS, plain): four square
# posts per tier, decks with a plain board edge, plain beams, plain rails with square balusters
# on the two upper tiers (front and both ends), flat tin roof under the main cornice.
# Ground tier open: the sidewalk runs under it (no deck, no step).
# ---------------------------------------------------------------------------
for z0, z1 in DECKS:                     # sides: soffit, south end, top, north end
    P.box(-HW, HW, 0.0, YM, z0, z1, mi=(TRIM, TRIM, [DECK, TRIM, DECK, TRIM]))
P.box(-HW - 0.15, HW + 0.15, -0.15, YM, PROOF[0], PROOF[1], mi=(TRIM, TRIM, [TRIM, TRIM, ROOF, TRIM]))
TIERS = ((0.20, DECKS[0][0]), (DECKS[0][1], DECKS[1][0]), (DECKS[1][1], PROOF[0]))
PC = POST / 2                            # post centre line y


def rail_run(along, fixed, a0, a1, zt):
    """Top rail, bottom rail and balusters from a0 to a1, centred on y = fixed (along 'x', the
    front) or x = fixed (along 'y', the ends)."""
    def bx(u0, u1, half, z0, z1):
        if along == "x":
            P.box(u0, u1, fixed - half, fixed + half, z0, z1, mi=TRIM)
        else:
            P.prism(rect(u0, u1, z0, z1), fixed - half, fixed + half, "x", mi=TRIM)
    bx(a0, a1, 0.045, zt + RAIL_H - 0.06, zt + RAIL_H)
    bx(a0, a1, 0.035, zt + 0.05, zt + 0.11)
    n = int((a1 - a0) / BAL_C)
    step = (a1 - a0) / (n + 1)
    for i in range(1, n + 1):
        u = a0 + step * i
        bx(u - BAL / 2, u + BAL / 2, BAL / 2, zt + 0.11, zt + RAIL_H - 0.06)


for t, (zt, zb) in enumerate(TIERS):
    for xp in POST_X:
        P.box(xp - POST / 2, xp + POST / 2, 0.0, POST, zt, zb, mi=TRIM)
        if t == 0:                       # stone block under each ground-tier post
            P.box(xp - 0.13, xp + 0.13, PC - 0.13, PC + 0.13, -0.05, 0.20, mi=DECK)
    # half-posts on the main wall at the two corners
    for xp in (-HW + PC, HW - PC):
        if t > 0:
            P.box(xp - PC, xp + PC, YM - 0.08, YM, zt, zb, mi=TRIM)
    # plain beam under the deck (or roof) edge between the posts, and along both ends
    for a, b in zip(POST_X[:-1], POST_X[1:]):
        P.box(a + PC, b - PC, 0.01, POST - 0.01, zb - 0.20, zb, mi=TRIM)
    for xe in (POST_X[0], POST_X[-1]):
        P.prism(rect(POST, YM - 0.08, zb - 0.20, zb), xe - 0.07, xe + 0.07, "x", mi=TRIM)
    if t > 0:
        for a, b in zip(POST_X[:-1], POST_X[1:]):
            rail_run("x", PC, a + PC, b - PC, zt)
        for xe in (POST_X[0], POST_X[-1]):
            rail_run("y", xe, POST, YM - 0.08, zt)

# ---------------------------------------------------------------------------
# Cornice (1890s photo): frieze board with 8 brackets, boxed cornice 8.84-9.14 projecting 0.45,
# returning 0.45 along the south side for 0.6 m, then a plain 0.25 eave along the avenue;
# a low pediment (gable) over the middle bay, apex 9.75, plain boarded tympanum
# ---------------------------------------------------------------------------
P.box(-HW, HW, YM - 0.03, YM, FB, CB, mi=TRIM)                                         # frieze
P.prism(rect(YM, YM + 0.6, FB, CB), HW, HW + 0.03, "x", mi=TRIM)                        # south frieze
P.box(-HW, HW + CPROJ, YM - CPROJ, YM, CB, CT, mi=(TRIM, TRIM, [TRIM, TRIM, ROOF, TRIM]))
P.box(HW, HW + CPROJ, YM, YM + 0.6, CB, CT, mi=(TRIM, TRIM, [TRIM, TRIM, ROOF, TRIM]))   # return
P.box(-HW, HW + CPROJ + 0.04, YM - CPROJ - 0.04, YM - CPROJ, CT - 0.11, CT + 0.015)     # crown strip
P.prism(rect(YM - CPROJ - 0.04, YM + 0.6, CT - 0.11, CT + 0.015), HW + CPROJ, HW + CPROJ + 0.04, "x")
P.box(-HW, HW, YM - CPROJ, YM - 0.03, CB - 0.03, CB, mi=TRIM)                           # bed moulding

# plain boxed eave along Higgins Ave, following the shed roof, with a frieze board under it
E0 = YM + 0.6
P.prism([(E0, roof_z(E0) - 0.22), (YR, roof_z(YR) - 0.22), (YR, roof_z(YR) + 0.03), (E0, roof_z(E0) + 0.03)],
        HW, HW + 0.25, "x", mi=TRIM)
P.prism([(E0, roof_z(E0) - 0.42), (YR, roof_z(YR) - 0.42), (YR, roof_z(YR) - 0.22), (E0, roof_z(E0) - 0.22)],
        HW, HW + 0.025, "x", mi=TRIM)

# brackets: console profile (Y-Z) 0.12 wide, pairs at the corners and under the gable feet
BR = [(YM - 0.03, FB + 0.04), (YM - 0.03, CB), (YM - CPROJ + 0.05, CB), (YM - CPROJ + 0.05, CB - 0.07),
      (YM - 0.30, CB - 0.14), (YM - 0.20, CB - 0.19), (YM - 0.12, CB - 0.27), (YM - 0.10, FB + 0.10),
      (YM - 0.10, FB + 0.04)]
for xc in (-3.02, -2.84, -1.24, -1.06, 1.06, 1.24, 2.84, 3.02):
    P.prism(BR, xc - 0.06, xc + 0.06, "x", mi=TRIM)
# and a pair under the south return (the front ones hide behind the porch roof from the
# sidewalk; these show from Higgins Ave and the SW, where the 1890s photo was taken)
BR_S = [(HW + (YM - y), z) for y, z in BR]
for yc in (2.48, 2.70):
    P.prism(BR_S, yc - 0.06, yc + 0.06, "y", mi=TRIM)

# pediment: a chevron of raking cornice (front 0.07 ahead of the cornice crown) and a recessed
# boarded tympanum; both run back over the roof to y 2.70
RT = 0.24                                  # rake depth (vertical)
P.prism([(-GHW, CT), (0.0, APEX), (GHW, CT), (GHW, CT - RT), (0.0, APEX - RT), (-GHW, CT - RT)],
        YM - CPROJ - 0.07, YM + 0.46, "y", mi=TRIM)
xt = GHW - RT * GHW / (APEX - CT)          # where the rake's underside meets the cornice top
P.prism([(-xt, CT), (xt, CT), (0.0, APEX - RT)], YM - 0.24, YM + 0.46, "y", mi=TRIM)

# corner boards on the south wall (front and rear corners) and the rear north corner
P.prism(rect(YM, YM + 0.16, SKIRT, FB), HW, HW + 0.022, "x", mi=TRIM)
P.prism(rect(YR - 0.16, YR, SKIRT, roof_z(YR) - 0.42), HW, HW + 0.022, "x", mi=TRIM)
P.box(HW - 0.16, HW, YR, YR + 0.022, SKIRT, RR - 0.02, mi=TRIM)
P.box(-HW, -HW + 0.16, YR, YR + 0.022, SKIRT, RR - 0.02, mi=TRIM)

# ---------------------------------------------------------------------------
# Rear porch (3 tiers, open, plain; shared row with 100-102's, decks level with its decks):
# two decks, a flat roof, three posts (100-102's south post stands right beside the north edge)
# ---------------------------------------------------------------------------
for z0, z1 in RDECKS:
    P.box(-HW, HW, YR, YP, z0, z1, mi=(TRIM, TRIM, [DECK, TRIM, DECK, TRIM]))
P.box(-HW, HW, YR, YP, RROOF[0], RROOF[1], mi=(TRIM, TRIM, [DECK, TRIM, ROOF, TRIM]))
for xp in (-1.00, 1.00, 3.00):
    for z0, z1 in ((0.0, RDECKS[0][0]), (RDECKS[0][1], RDECKS[1][0]), (RDECKS[1][1], RROOF[0])):
        P.box(xp - 0.07, xp + 0.07, YP - 0.14, YP, z0, z1, mi=TRIM)

# ---------------------------------------------------------------------------
# Build objects (boolean the cut shell)
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


main = cut_shell(MAIN, CUT_M, "DS_Main")
assign_atlas_uvs(main)
parts = P.to_object("DS_Parts", col)
assign_blind_uvs(parts)

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("106 Main built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)")
# Materials, baked lighting and GLB export: run store_106_bake.py (it runs this file first).
