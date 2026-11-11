"""
store_57.py - builds the brick house with shop fronts at 57 Main St, Flemington (west side,
old nos. 513-512), as on the Sept 1921 Sanborn map (owner decisions 2026-11-11):
  A  the old house: two full brick storeys (wall top 7.00, GUESS) and
  B  a slate mansard all round (third storey, top 9.75 = the map's 32 ft), deck edge 1.25 m
     inside the walls; four flat-topped dormers on the front, two on each side
  C  the "D.G." front: 2 storeys, 28 ft, flat parapet, plain 1910s brick front
  D  "Conf'y" and E "Gro.": two 1-storey (14 ft) brick shops in front of the house
  F  2-storey brick rear wing ("Cobbler"), G 1-storey brick rear part, H little frame shed
  P  forecourt paving from the shop fronts to the street line (Y -2.10)
Plain guesses everywhere on the elevations: no brackets, chimneys, shutters, creeper, awnings,
signs or lettering (owner rule). One continuous plain fascia over the three shop fronts.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/store_57.py").read())

Every run deletes and rebuilds the "Store57" collection. Materials, lightmap bake and GLB
export: store_57_bake.py (runs this file first). Pattern: store_100_102.py (one bmesh per
part, a material index per face, closed shells cut by nested boolean pockets whose faces keep
the cutter's material index); the mansard as union_hotel.py's stepped roof.

Windows (PLAN.md "E. Windows that don't read as flat black"): every pane is ONE glass face
(material Glass -> exported as `glass`) 4 cm in front of a window back: the back of the pane's
boolean pocket, with atlas UVs into assets/textures/shared/window_backs.jpg (dwelling rooms,
lace, blinds; the show windows, shop doors and transoms: the dim shop cells of the same atlas).

Coordinates (metres, Blender Z-up), origin = scene (-12.40, 0.15, -84.94), rotation 0 90 0:
    X  along the street, +X = north (open lot to the County Hotel), -X = south (Wurts office)
    Y  depth: y = 0 is the shop front wall; house front 3.64, house rear 13.92, wing to 24.22;
       the shop fascia reaches y = -0.29, the paving y = -2.10 (= the street line)
    Z  up from the sidewalk top; walls skirt down to -0.20
Scene: world x = -12.40 - Y, world z = -84.94 - X.
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".
"""

import json
import bpy
import bmesh
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md massing table and elevation notes)
# ---------------------------------------------------------------------------
HW = 8.17                     # half front (16.34 m)
YH, YB = 3.64, 13.92          # house front and rear wall
HTOP = 7.00                   # house wall top (GUESS)
MI, MTOP = 1.25, 9.75         # mansard inset, top (MAP 32 ft)
XDG = 2.20                    # D.G. / Conf'y party wall
XCG = -3.71                   # Conf'y / Gro. partition
DG_ROOF, DG_PAR = 8.10, 8.45  # D.G. flat roof, parapet (coping to 8.53)
SH_ROOF, SH_PAR = 3.95, 4.19  # shops' flat roof, parapet (coping to 4.27)
PAR_T = 0.25                  # parapet thickness
FAS0, FAS1, FAS_OUT = 3.10, 3.45, 0.29   # shop fascia (MAP heavy dashed line 0.29 in front)
COR0, COR1, COR_OUT = 6.70, 7.00, 0.35   # house cornice
F_X0, F_X1, F_Y1, F_T0, F_T1 = 0.98, 6.92, 24.22, 6.40, 6.10   # rear wing "Cobbler"
G_X0, G_Y1, G_T0, G_T1 = -2.80, 21.59, 3.00, 2.80               # 1-storey rear part
H_X0, H_Y1, H_T0, H_T1 = 6.92, 15.85, 2.40, 2.20                # frame shed
PAVE_Y = -2.10
SKIRT = -0.20


def slope_in(z):
    """Mansard: horizontal inset from the wall face at height z."""
    return (z - HTOP) * MI / (MTOP - HTOP)


BRICKH, BRICKS, STONE, TRIM, SLATE, ROOF, SHOP, PAVE, CLAP, GLASS, WBACK = range(11)
NAMES = ["BrickHouse", "BrickShop", "Stone", "Trim", "Slate", "Roof", "Shopfront", "Paving",
         "Clapboard", "Glass", "WindowBack"]


# ---------------------------------------------------------------------------
# Materials (plain stand-ins; store_57_bake.py swaps in the textures)
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


COLOURS = ["#8A4A3A", "#6E4438", "#A8A49A", "#DDD5C2", "#5E6466", "#5A3D34", "#2E2E26", "#9A968C",
           "#C3BDAD", "#1A1916", "#3a332c"]
MATS = [plain("S57_" + n, c) for n, c in zip(NAMES, COLOURS)]

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
        return self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, "y", mi)

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


col = fresh_collection("Store57")
P = MB()                                   # all added parts (not cut)
SHELLS = {k: (MB(), MB()) for k in ("House", "DG", "Shops", "WingF", "WingG", "ShedH", "Dormers")}
HOUSE, CUT_H = SHELLS["House"]
DG, CUT_DG = SHELLS["DG"]
SHOPS, CUT_S = SHELLS["Shops"]
WF, CUT_F = SHELLS["WingF"]
WG, CUT_G = SHELLS["WingG"]
SH, _ = SHELLS["ShedH"]
DORM, CUT_D = SHELLS["Dormers"]

# Walls: (axis, outer face depth, outward sign); u = X on 'y' walls, Y on 'x' walls
FRONT = ("y", 0.0, -1)          # shop fronts and the D.G. front
H_FRONT = ("y", YH, -1)         # house front above the shops
H_NORTH = ("x", HW, 1)          # house + D.G. north side
H_SOUTH = ("x", -HW, -1)        # house south side
H_REAR = ("y", YB, 1)
F_NORTH = ("x", F_X1, 1)
F_SOUTH = ("x", F_X0, -1)
F_REAR = ("y", F_Y1, 1)
G_SOUTH = ("x", G_X0, -1)
G_REAR = ("y", G_Y1, 1)


def Dfun(wall):
    axis, face, out = wall
    return axis, (lambda k: face + out * k)   # k > 0 outside the wall, k < 0 inside


def wbox(wall, u0, u1, k0, k1, z0, z1, mi=TRIM, mb=None):
    """Box on a wall: u along the wall, k = distance out of the wall face, z up."""
    axis, D = Dfun(wall)
    (mb or P).prism(rect(u0, u1, z0, z1), D(k0), D(k1), axis, mi)


# ---------------------------------------------------------------------------
# Window backs and glass (store_100_102.py)
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


# window-back cells: dwelling rooms in the house, stock rooms over the dry-goods store,
# a workshop in the wing; no two alike side by side (lists are walked in order)
HOUSE_CELLS = ["lace", "blind_cream_half", "curtains_beige", "lace_blind_green", "dark_room_frame",
               "blind_green_half", "lace_blind_cream", "curtains_olive", "blind_cream_low", "lace",
               "dark_room", "blind_green_low", "curtains_maroon_blind", "lace_full_blind_cream",
               "blind_cream_high", "lace_blind_cream", "dark_room_frame", "curtains_beige"]
ATTIC_CELLS = ["blind_green_high", "dark_room", "blind_cream_full", "lace", "blind_green_half",
               "dark_room_frame", "blind_cream_high", "dark_room"]
STOCK_CELLS = ["blind_cream_high", "dark_room_frame", "blind_cream_half", "blind_green_high"]
WING_CELLS = ["dark_room", "blind_cream_low", "dark_room_frame", "curtains_olive", "blind_green_half",
              "dark_room", "lace", "dark_room_frame"]
_cell_pos = {}


def next_cell(cells):
    i = _cell_pos.get(id(cells), 0)
    _cell_pos[id(cells)] = i + 1
    return cells[i % len(cells)]


# ---------------------------------------------------------------------------
# Shells
# ---------------------------------------------------------------------------
# A: the house, a closed brick box to the wall top (the mansard sits on it)
HOUSE.box(-HW, HW, YH, YB, SKIRT, HTOP, mi=BRICKH)
# C: the D.G. front, closed to the parapet top; the roof pocket is cut from above
DG.box(XDG, HW, 0.0, YH, SKIRT, DG_PAR, mi=BRICKS)
CUT_DG.box(XDG + PAR_T, HW - PAR_T, PAR_T, YH - PAR_T, DG_ROOF, DG_PAR + 1.0,
           mi=(BRICKS, BRICKS, [ROOF, BRICKS, BRICKS, BRICKS]))
# D + E: the two 1-storey shops, parapet on the front and the south side only (the roof runs
# into the house wall and the D.G. wall)
SHOPS.box(-HW, XDG, 0.0, YH, SKIRT, SH_PAR, mi=BRICKS)
CUT_S.box(-HW + PAR_T, XDG + 0.05, PAR_T, YH + 0.05, SH_ROOF, SH_PAR + 1.0,
          mi=(BRICKS, BRICKS, [ROOF, BRICKS, BRICKS, BRICKS]))
# F, G: brick rear parts, shed roofs falling to the rear (outline sides: bottom, rear, roof, front)
WF.prism([(YB, SKIRT), (F_Y1, SKIRT), (F_Y1, F_T1), (YB, F_T0)], F_X0, F_X1, "x",
         mi=(BRICKH, BRICKH, [BRICKH, BRICKH, ROOF, BRICKH]))
WG.prism([(YB, SKIRT), (G_Y1, SKIRT), (G_Y1, G_T1), (YB, G_T0)], G_X0, F_X0, "x",
         mi=(BRICKH, BRICKH, [BRICKH, BRICKH, ROOF, BRICKH]))
# H: little frame shed (clapboard, blank)
SH.prism([(YB, SKIRT), (H_Y1, SKIRT), (H_Y1, H_T1), (YB, H_T0)], H_X0, HW, "x",
         mi=(CLAP, CLAP, [CLAP, CLAP, ROOF, CLAP]))

# ---------------------------------------------------------------------------
# Sash windows in brick (GUESS): 0.12 brick reveal, sash plane, 1/1 or 2/2 panes, flat stone
# lintel and sill
# ---------------------------------------------------------------------------
FR = 0.06          # sash frame width
REV = 0.12         # reveal depth to the sash plane
D_GLASS = 0.15     # glass behind the wall face


def window(C, wall, cu, w, z0, z1, cell, wall_mat=BRICKH, muntin=False, stone=True):
    axis, D = Dfun(wall)
    C.prism(rect(cu - w / 2, cu + w / 2, z0, z1), D(0.25), D(-REV), axis, mi=(wall_mat, TRIM, wall_mat))
    zm = (z0 + z1) / 2 + 0.03                                          # meeting rail
    frame = (cu - w / 2 + FR, cu + w / 2 - FR, z0 + FR, z1 - FR)
    pane(C, wall, rect(frame[0], frame[1], zm + 0.025, frame[3]), D_GLASS, cell, TRIM, frame)
    pane(C, wall, rect(frame[0], frame[1], frame[2], zm - 0.025), D_GLASS, cell, TRIM, frame)
    if muntin:                                                         # 2/2: one vertical bar
        wbox(wall, cu - 0.015, cu + 0.015, -D_GLASS + 0.004, -REV - 0.003, frame[2], frame[3])
    if stone:
        wbox(wall, cu - w / 2 - 0.10, cu + w / 2 + 0.10, 0.0, 0.03, z1, z1 + 0.22, mi=STONE)      # lintel
        wbox(wall, cu - w / 2 - 0.06, cu + w / 2 + 0.06, 0.0, 0.05, z0 - 0.08, z0 + 0.015, mi=STONE)  # sill
        wbox(wall, cu - w / 2, cu + w / 2, -REV, 0.0, z0, z0 + 0.015, mi=STONE)                 # its back


def plain_door(C, wall, cu, w, h, wall_mat=BRICKH):
    """Plain panelled back door in a 0.12 recess, stone step and lintel."""
    axis, D = Dfun(wall)
    C.prism(rect(cu - w / 2, cu + w / 2, 0.0, h), D(0.25), D(-0.12), axis, mi=(wall_mat, SHOP, wall_mat))
    wbox(wall, cu - 0.02, cu + 0.02, -0.12, -0.105, 0.0, h, mi=SHOP)
    for z in (0.30, 1.00, 1.70):
        wbox(wall, cu - w / 2 + 0.07, cu + w / 2 - 0.07, -0.12, -0.105, z, z + 0.12, mi=SHOP)
    wbox(wall, cu - w / 2 - 0.10, cu + w / 2 + 0.10, 0.0, 0.03, h, h + 0.20, mi=STONE)
    wbox(wall, cu - w / 2 - 0.10, cu + w / 2 + 0.10, -0.12, 0.35, SKIRT, 0.0, mi=STONE)


# house front over the shops: four 2/2 windows (2nd floor)
HF_X = (-6.87, -4.28, -1.69, 0.90)
for x in HF_X:
    window(CUT_H, H_FRONT, x, 0.90, 4.65, 6.45, next_cell(HOUSE_CELLS), muntin=True)
# house sides: three 2/2 windows per floor
for wall in (H_NORTH, H_SOUTH):
    for z0, z1 in ((1.20, 3.00), (4.65, 6.45)):
        for y in (5.6, 8.8, 12.0):
            window(CUT_H, wall, y, 0.90, z0, z1, next_cell(HOUSE_CELLS), muntin=True)
# house rear: one door (south of the low rear part)
plain_door(CUT_H, H_REAR, -5.5, 0.95, 2.20)

# D.G. upper floor: three 1/1 windows on the front, one on the north side
for x in (3.45, 5.19, 6.93):
    window(CUT_DG, FRONT, x, 0.90, 4.75, 6.45, next_cell(STOCK_CELLS), wall_mat=BRICKS)
window(CUT_DG, H_NORTH, 1.82, 0.90, 4.75, 6.45, next_cell(STOCK_CELLS), wall_mat=BRICKS)

# rear wing F: 1/1 windows 0.80 x 1.45; the low part G covers its south face below 3.0 up to
# Y 21.59, so there the ground floor has one window beyond G and the door is on the rear face
for wall, ground in ((F_NORTH, (17.0, 21.5)), (F_SOUTH, (23.2,))):
    for y in (17.0, 21.5):
        window(CUT_F, wall, y, 0.80, 3.75, 5.20, next_cell(WING_CELLS))
    for y in ground:
        window(CUT_F, wall, y, 0.80, 0.95, 2.40, next_cell(WING_CELLS))
plain_door(CUT_F, F_REAR, 3.95, 0.90, 2.10)
window(CUT_F, F_REAR, 2.40, 0.80, 3.75, 5.20, next_cell(WING_CELLS))
window(CUT_F, F_REAR, 5.50, 0.80, 3.75, 5.20, next_cell(WING_CELLS))
# G: one door (rear), one window (south)
plain_door(CUT_G, G_REAR, -1.0, 0.90, 2.10)
window(CUT_G, G_SOUTH, 17.5, 0.80, 0.95, 2.40, next_cell(WING_CELLS))

# ---------------------------------------------------------------------------
# Shop fronts (GUESS, plain; Y 0): brick piers 0.35 at both ends and at the two division lines,
# each front recessed 0.10 between its piers (dark wood face), bulkheads Z 0-0.65 with raised
# panels, plate glass 0.65-2.60, transom lights 2.60-3.05, doors glazed in the upper half
# (0.90 wide, head 2.60) set back 0.08 more. No sign, no lettering, no awning.
# ---------------------------------------------------------------------------
PIER = 0.35
SF_REC = 0.10          # shop-front plane behind the brick face
GL0, GL1, TR0, TR1 = 0.65, 2.60, 2.66, 3.00
SHOPFRONTS = [   # (cutter, recess x0, x1, [(kind, a, b)])
    (CUT_DG, XDG + PIER / 2, HW - PIER, [("win", 2.60, 4.55), ("door", 4.75, 5.65), ("win", 5.85, 7.80)]),
    (CUT_S, XCG + PIER / 2, XDG - PIER / 2, [("win", -3.35, -1.45), ("door", -1.20, -0.30), ("win", -0.05, 1.85)]),
    (CUT_S, -HW + PIER, XCG - PIER / 2, [("win", -7.80, -5.55), ("door", -5.30, -4.40)]),
]
shop_cells = iter(["shop_a", "shop_b", "shop_b", "shop_a", "shop_a"])
axis, D = Dfun(FRONT)
for C, rx0, rx1, items in SHOPFRONTS:
    # recess: floor stone, sides brick, top (under the fascia) dark wood
    C.prism(rect(rx0, rx1, 0.0, FAS0), D(0.25), D(-SF_REC), "y",
            mi=(BRICKS, SHOP, [STONE, BRICKS, SHOP, BRICKS]))
    for kind, a, b in items:
        a, b = max(a, rx0 + 0.06), min(b, rx1 - 0.06)
        if kind == "win":
            cell = next(shop_cells)
            C.prism(rect(a, b, GL0, GL1), D(0.25), D(-SF_REC - 0.04), "y", mi=(SHOP, SHOP, SHOP))
            f, bar = 0.05, 0.05
            xm = (a + b) / 2
            frame = (a + f, b - f, GL0 + f, GL1 - f)
            for p0, p1 in ((a + f, xm - bar / 2), (xm + bar / 2, b - f)):
                pane(C, FRONT, rect(p0, p1, GL0 + f, GL1 - f), SF_REC + 0.06, cell, SHOP, frame)
            P.box(a - 0.03, b + 0.03, -0.04, SF_REC, GL0 - 0.05, GL0 + 0.015, mi=SHOP)        # sill rail
            P.box(a + 0.08, b - 0.08, SF_REC - 0.018, SF_REC, 0.12, GL0 - 0.12, mi=SHOP)      # raised panel
        else:
            DY = SF_REC + 0.08
            C.prism(rect(a, b, 0.0, GL1), D(0.25), D(-DY), "y", mi=(SHOP, SHOP, [STONE, SHOP, SHOP, SHOP]))
            P.box(a + 0.13, b - 0.13, DY - 0.018, DY, 0.20, 1.05, mi=SHOP)                    # raised panel
            pane(C, FRONT, rect(a + 0.11, b - 0.11, 1.22, GL1 - 0.14), DY + 0.02, "door", SHOP)
            P.box(a - 0.02, b + 0.02, -0.03, DY, -0.05, 0.02, mi=STONE)                         # threshold
        pane(C, FRONT, rect(a + 0.05, b - 0.05, TR0, TR1), SF_REC + 0.04, "transom", SHOP)      # transom

# shop fascia: one plain board across all three fronts, 0.29 out (MAP), with a cap and bed mould
P.box(-HW - 0.02, HW + 0.02, -FAS_OUT, 0.0, FAS0, FAS1, mi=TRIM)
P.box(-HW - 0.04, HW + 0.04, -FAS_OUT - 0.04, 0.0, FAS1 - 0.06, FAS1 + 0.02, mi=TRIM)

# 1-storey parapet: one projecting brick course and a stone coping (front and south side)
P.box(-HW - 0.03, XDG, -0.03, 0.0, 4.00, 4.07, mi=BRICKS)
P.prism(rect(0.0, YH, 4.00, 4.07), -HW, -HW - 0.03, "x", mi=BRICKS)
P.box(-HW - 0.04, XDG, -0.04, PAR_T, SH_PAR, SH_PAR + 0.08, mi=STONE)
P.prism(rect(PAR_T, YH, SH_PAR, SH_PAR + 0.08), -HW - 0.04, -HW + PAR_T, "x", mi=STONE)

# D.G. top: two-course brick corbel band (front, north and south faces), stone coping all round
for z0, z1, o in ((7.70, 7.80, 0.03), (7.80, 7.90, 0.06)):
    P.box(XDG - o, HW + o, -o, 0.0, z0, z1, mi=BRICKS)
    P.prism(rect(0.0, YH, z0, z1), HW, HW + o, "x", mi=BRICKS)
    P.prism(rect(0.0, YH, z0, z1), XDG, XDG - o, "x", mi=BRICKS)
P.box(XDG - 0.04, HW + 0.04, -0.04, PAR_T, DG_PAR, DG_PAR + 0.08, mi=STONE)
P.prism(rect(PAR_T, YH, DG_PAR, DG_PAR + 0.08), HW - PAR_T, HW + 0.04, "x", mi=STONE)
P.prism(rect(PAR_T, YH, DG_PAR, DG_PAR + 0.08), XDG - 0.04, XDG + PAR_T, "x", mi=STONE)
P.box(XDG + PAR_T, HW - PAR_T, YH - PAR_T, YH, DG_PAR, DG_PAR + 0.08, mi=STONE)

# end piers' stone bases (plinth course along the fronts, Z 0 ... 0.15 at the piers)
for x0, x1 in ((-HW - 0.02, -HW + PIER), (XCG - PIER / 2, XCG + PIER / 2), (XDG - PIER / 2, XDG + PIER / 2),
               (HW - PIER, HW + 0.02)):
    P.box(x0, x1, -0.02, 0.0, SKIRT, 0.15, mi=STONE)

# ---------------------------------------------------------------------------
# House cornice: plain boxed, Z 6.70-7.00, 0.35 out, all four sides (front only south of the
# D.G. block), bed moulding under it. No brackets.
# ---------------------------------------------------------------------------
O = COR_OUT
P.box(-HW - O, XDG, YH - O, YH, COR0, COR1)                          # front (to the D.G. wall)
P.prism(rect(YH, YB, COR0, COR1), HW, HW + O, "x")                   # north
P.prism(rect(YH, YB, COR0, COR1), -HW, -HW - O, "x")                 # south
P.box(-HW - O, HW + O, YB, YB + O, COR0, COR1)                       # rear
P.box(-HW - 0.08, XDG, YH - 0.08, YH, COR0 - 0.08, COR0)             # bed mouldings
P.prism(rect(YH, YB, COR0 - 0.08, COR0), HW, HW + 0.08, "x")
P.prism(rect(YH, YB, COR0 - 0.08, COR0), -HW, -HW - 0.08, "x")
P.box(-HW - 0.08, HW + 0.08, YB, YB + 0.08, COR0 - 0.08, COR0)

# ---------------------------------------------------------------------------
# Mansard (straight ~65 deg slate slopes from the wall top to the deck edge, 1.25 in), flat tin
# deck with a 0.10 curb
# ---------------------------------------------------------------------------
bm = P.bm
ring0 = [bm.verts.new(p) for p in ((-HW, YH, HTOP), (HW, YH, HTOP), (HW, YB, HTOP), (-HW, YB, HTOP))]
ring1 = [bm.verts.new(p) for p in ((-HW + MI, YH + MI, MTOP), (HW - MI, YH + MI, MTOP),
                                   (HW - MI, YB - MI, MTOP), (-HW + MI, YB - MI, MTOP))]
for i in range(4):
    j = (i + 1) % 4
    f = bm.faces.new([ring0[i], ring0[j], ring1[j], ring1[i]])
    f.material_index = SLATE
deck = bm.faces.new(ring1)          # rings run anticlockwise seen from above: slopes face out,
deck.material_index = ROOF           # the deck faces up
X0, X1, Y0, Y1 = -HW + MI, HW - MI, YH + MI, YB - MI
C_W = 0.10
P.box(X0, X1, Y0, Y0 + C_W, MTOP, MTOP + 0.10, mi=ROOF)
P.box(X0, X1, Y1 - C_W, Y1, MTOP, MTOP + 0.10, mi=ROOF)
P.prism(rect(Y0 + C_W, Y1 - C_W, MTOP, MTOP + 0.10), X0, X0 + C_W, "x", mi=ROOF)
P.prism(rect(Y0 + C_W, Y1 - C_W, MTOP, MTOP + 0.10), X1 - C_W, X1, "x", mi=ROOF)

# ---------------------------------------------------------------------------
# Dormers: flat-topped, 1/1 sash 0.75 x 1.30 (Z 7.60-8.90), plain painted cheeks, tin top.
# Front 4 over the 2nd-floor windows; north 2 and south 2 at Y 6.9 and 10.6; rear none.
# ---------------------------------------------------------------------------
DW, DZ0, DZ1, DTOP = 0.75, 7.60, 8.90, 9.10
D_BACK = slope_in(DTOP + 0.1) + 0.25          # body runs this far into the roof


def dormer(wall, cu):
    axis, face, out = wall
    wbox(wall, cu - DW / 2 - 0.15, cu + DW / 2 + 0.15, 0.0, -D_BACK, DZ0 - 0.25, DTOP, mi=TRIM, mb=DORM)
    window(CUT_D, wall, cu, DW, DZ0, DZ1, next_cell(ATTIC_CELLS), wall_mat=TRIM, stone=False)
    wbox(wall, cu - DW / 2 - 0.22, cu + DW / 2 + 0.22, 0.08, -D_BACK, DTOP, DTOP + 0.06, mi=ROOF)   # tin top
    wbox(wall, cu - DW / 2 - 0.08, cu + DW / 2 + 0.08, 0.0, 0.05, DZ0 - 0.06, DZ0 + 0.015, mi=TRIM)  # sill


for x in HF_X:
    dormer(("y", YH + 0.02, -1), x)
for y in (6.9, 10.6):
    dormer(("x", HW - 0.02, 1), y)
    dormer(("x", -HW + 0.02, -1), y)

# ---------------------------------------------------------------------------
# Rear parts: tin roof edges (small overhang strips), forecourt paving
# ---------------------------------------------------------------------------
P.box(-HW, HW, PAVE_Y, 0.0, -0.05, 0.0, mi=PAVE)

# ---------------------------------------------------------------------------
# Build objects (boolean the cut shells)
# ---------------------------------------------------------------------------


def cut_shell(shell, cut, name):
    walls = shell.to_object(name, col)
    if not cut.bm.faces:
        cut.bm.free()
        return walls
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


for key, (shell, cut) in SHELLS.items():
    obj = cut_shell(shell, cut, "S57_" + key)
    assign_atlas_uvs(obj)
P.to_object("S57_Parts", col)

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("57 Main built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)")
# Materials, baked lighting and GLB export: run store_57_bake.py (it runs this file first).
