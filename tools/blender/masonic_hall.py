"""
masonic_hall.py - builds the Masonic Hall / Hunterdon County National Bank, 90-94 Main St,
Flemington (east side, old nos. 536-534; J. C. Hopewell, 1864-66), as it stood in Sept 1921:
the new 1920-21 rusticated stone bank front on the north 11.5 m, the old brick arcade kept on
the vacant south part (94).

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/masonic_hall.py").read())

Every run deletes and rebuilds the "MasonicHall" collection. Materials, lightmap bake and GLB
export: masonic_hall_bake.py (runs this file first). Pattern: bank_building.py (one bmesh per
part, a material index per face, closed shells cut by nested boolean pockets whose faces keep
the cutter's material index) and odd_fellows_hall.py (same builder, Hopewell, next door).

Sources: PLAN.md "Masonic Hall / Hunterdon County National Bank (90-94 Main St, old nos.
536-534)" (Sept 1921 Sanborn sheet 3; perspective fits of the c. 1918 and 1938-published
Goodspeed photos, +-0.3 m). Owner decisions 2026-11-10: 1921 state; only the small carved
"THE HUNTERDON COUNTY NATIONAL BANK" inscription + round plaque on the corner pier (the letters
are baked into the lightmap by masonic_hall_bake.py, the plaque is modelled); ordinary detail.

Eaves (checked against the c. 1918 and 1938 photos, 2026-11-10): under the boxed raking and side
cornices runs a row of small pale wooden blocks (modillions), then a plain brick frieze, then a
stepped brick corbel course; every pilaster ends in a pair of tall pale brackets that span the
frieze. Neither photo shows "arched wood trim" (NRHP 1980), so none is modelled.

Windows (PLAN.md "E. Windows that don't read as flat black"): every pane is ONE glass face
(material Glass -> exported as `glass`) 4 cm in front of a window back: the back of the
window's inner boolean pocket. Upper floors, side walls, rear, the wheel window and the vacant
94: cells of assets/textures/shared/window_backs.jpg (offices on the 2nd floor: blinds at varied
heights, a few dark rooms; lodge rooms on the 3rd: mostly dark green blinds pulled down, a little
lace; 94 and the side door: dark empty rooms). Bank windows, the main door and the north wall's
ground floor: cells of assets/textures/shared/bank_hall.jpg (the banking room). Each back is
registered in BACKS and gets its atlas UVs (layer "UVMap") after the booleans.

Coordinates (metres, Blender Z-up), origin = scene (10.00, 0.15, 30.92), rotation 0 -90 0:
    X  along the street, +X = south (the Democrat building), -X = north (alley, Odd Fellows)
    Y  depth: y = 0 is the 1921 stone / arcade face; the brick wall above is at y = 0.30;
       rear wall at 18.59; the 94 steps run out to -0.60, cornices to -0.25
    Z  up from the sidewalk top; walls skirt down to -0.20
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".
"""

import json
import math
import random
import bpy
import bmesh
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md massing and elevation notes)
# ---------------------------------------------------------------------------
HW = 9.25               # half width (18.50, map)
YW = 0.30               # brick wall face (stone front 0.30 in front of it)
YR = 18.59              # rear wall
GT = 4.40               # top of the ground storey / its cornice
SKIRT = -0.20
CT = 11.60              # side cornice top (map 38')
SOF = 11.25             # side soffit
APEX = 15.60            # raking cornice top at the apex
OVER = 0.55             # cornice projection
K = (APEX - CT) / (HW + OVER)         # rake slope (~22 deg)
# eave bands, measured down from the cornice top (raking: from the rake line)
O_SOF, O_MOD, O_FRZ, O_C1, O_C2 = 0.35, 0.52, 0.74, 0.82, 0.90
SHELL_DROP = 0.08       # gable wall top sits this far under the roof top line
XN = lambda xn: xn - HW # "Xn" (metres from the north wall) -> X

# upper front windows (all round-arched)
BAYS = (-7.45, -3.85, 3.85, 7.45)     # single, 1.00 wide
PAIR = (-0.65, 0.65)                  # middle bay, 0.80 wide
F3 = (8.05, 9.95)                     # 3rd floor sill, springing (single: top 10.45)
F2 = (4.75, 6.05)                     # 2nd floor
PILASTERS = ((-5.6, 0.45), (-2.2, 0.45), (2.2, 0.45), (5.6, 0.45))
CORNER_W = 0.60
WHEEL_Z, WHEEL_R = 13.2, 0.65

BRICK, STONE, SMOOTH, CORNICE, SASH, DARK, ROOF, GLASS, WBACK, HALL = range(10)
NAMES = ["Brick", "Stone", "Smooth", "Cornice", "Sash", "Dark", "Roof", "Glass", "WindowBack", "BankHall"]


def rake(x):
    """Top of the raking cornice above x."""
    return APEX - K * abs(x)


# ---------------------------------------------------------------------------
# Materials (plain stand-ins; masonic_hall_bake.py swaps in the textures)
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


COLOURS = ["#8A4A38", "#C4BFB4", "#C4BFB4", "#6E6250", "#DDD5C2", "#3A2A1F", "#5A3D34", "#1A1916",
           "#3a332c", "#2e2822"]
MATS = [plain("MH_" + n, c) for n, c in zip(NAMES, COLOURS)]

# ---------------------------------------------------------------------------
# Mesh builder: one bmesh, a material index per face (as bank_building.py)
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

    def prism(self, pts, d0, d1, axis="y", mi=SASH):
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

    def box(self, x0, x1, y0, y1, z0, z1, mi=SASH):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, "y", mi)

    def arc_band(self, cu, cv, r_in, r_out, a0, a1, d0, d1, axis="y", segs=8, mi=BRICK, closed=False):
        """Curved band between radii r_in and r_out, angles a0..a1 (0 = +u, pi/2 = up)."""
        bm = self.bm
        n = segs if closed else segs + 1
        ts = [a0 + (a1 - a0) * i / segs for i in range(n)]

        def ring(r, d):
            return [bm.verts.new(self._pt(axis, cu + r * math.cos(t), d, cv + r * math.sin(t))) for t in ts]
        of, inf, ob, ib = ring(r_out, d0), ring(r_in, d0), ring(r_out, d1), ring(r_in, d1)
        faces = []
        for i in range(segs):
            j = (i + 1) % n
            faces.append(bm.faces.new([of[i], of[j], inf[j], inf[i]]))
            faces.append(bm.faces.new([ob[i], ib[i], ib[j], ob[j]]))
            faces.append(bm.faces.new([of[i], ob[i], ob[j], of[j]]))
            faces.append(bm.faces.new([inf[i], inf[j], ib[j], ib[i]]))
        if not closed:
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


def arched(cu, w, z0, zs, segs=6):
    """Round-headed opening: straight sides from z0 up to zs, half-circle above."""
    r = w / 2
    return [(cu - r, z0), (cu + r, z0)] + [
        (cu + r * math.cos(math.pi * i / segs), zs + r * math.sin(math.pi * i / segs)) for i in range(segs + 1)]


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


def circle(cu, cv, r, segs=8, phase=0.5):
    return [(cu + r * math.cos(2 * math.pi * (i + phase) / segs), cv + r * math.sin(2 * math.pi * (i + phase) / segs))
            for i in range(segs)]


def rake_band(x0, x1, o_top, o_bot):
    """Outline (X-Z) of a band that follows the rake between offsets o_top / o_bot below it."""
    return [(x0, rake(x0) - o_bot), (x1, rake(x1) - o_bot), (x1, rake(x1) - o_top), (x0, rake(x0) - o_top)]


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


col = fresh_collection("MasonicHall")
P = MB()                       # all added parts
GROUND, CUT_G = MB(), MB()     # ground storey shell (stone / brick front, brick sides)
UPPER, CUT_U = MB(), MB()      # upper storeys with both gables

# Each wall: (axis, outer face depth, outward sign)
FRONT_G = ("y", 0.0, -1)
FRONT_U = ("y", YW, -1)
NORTH = ("x", -HW, -1)
SOUTH = ("x", HW, 1)
REAR = ("y", YR, 1)


def Dfun(wall):
    axis, face, out = wall
    return axis, (lambda k: face + out * k)   # k > 0 outside the wall, k < 0 inside


def cutter(z_top):
    return CUT_G if z_top <= GT + 1e-6 else CUT_U


# ---------------------------------------------------------------------------
# Window backs and glass
# ---------------------------------------------------------------------------
WB_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\window_backs.json"))["cells"]
BH_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\bank_hall.json"))["cells"]
GAP = 0.04
OFFICE = {"blind_cream_high": 3, "blind_cream_half": 3, "blind_cream_low": 2, "blind_green_half": 2,
          "blind_green_high": 1, "dark_room": 2, "dark_room_frame": 2, "curtains_beige": 1, "lace_blind_cream": 1}
LODGE = {"blind_green_low": 4, "blind_green_half": 3, "lace_blind_green": 2, "blind_green_high": 1,
         "blind_cream_low": 1, "dark_room": 1}
EMPTY = {"dark_room": 1, "dark_room_frame": 1}
_rng = random.Random(1866)
_grid = {}
BACKS = []             # (axis, plane, out, u0, u1, z0, z1, uv rect)


def pick_cell(weights, wall, row, colm):
    """No repeat side by side or above/below."""
    avoid = {_grid.get((wall, row), {}).get(colm - 1), _grid.get((wall, row - 1), {}).get(colm),
             _grid.get((wall, row), {}).get(colm + 1)}
    names = [n for n in weights if n not in avoid]
    cell = _rng.choices(names, weights=[weights[n] for n in names])[0]
    _grid.setdefault((wall, row), {})[colm] = cell
    return cell


def back_mat(cell):
    return HALL if cell in BH_CELLS else WBACK


def cell_uv(cell, aspect=None):
    """Atlas rectangle of a cell; banking-room cells are cropped (centred) to `aspect` (w/h)
    so the room is not stretched. 1.5 px inset against bleeding from the neighbour."""
    table = BH_CELLS if cell in BH_CELLS else WB_CELLS
    U0, V0, U1, V1 = table[cell]["uv"]
    e = 1.5 / 1024
    U0, V0, U1, V1 = U0 + e, V0 + e, U1 - e, V1 - e
    if aspect and cell in BH_CELLS:
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


def glass(wall, outline, d_glass):
    axis, D = Dfun(wall)
    P.face(outline, D(-d_glass), axis, wall[2])


def assign_atlas_uvs(obj):
    """Window-back faces -> their atlas cell, left to right as seen from outside."""
    me = obj.data
    uvl = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    missed = 0
    for p in me.polygons:
        if p.material_index not in (WBACK, HALL):
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
XS = XN(11.5)          # end of the 1921 stone front (X 2.25)
# ground storey: plan outline from the north wall's stone return round the front and back;
# edges: north return (stone), front 90 (stone), front 94 (brick), south, rear, north (brick)
G_PLAN = [(-HW, 0.60), (-HW, 0.0), (XS, 0.0), (HW, 0.0), (HW, YR), (-HW, YR)]
GROUND.prism(G_PLAN, SKIRT, GT, axis="z", mi=(BRICK, SMOOTH, [STONE, STONE, BRICK, BRICK, BRICK, BRICK]))
# upper storeys: pentagon (both gables) from the ground storey's top up under the roof
U_OUT = [(-HW, GT), (HW, GT), (HW, rake(HW) - SHELL_DROP), (0.0, APEX - SHELL_DROP), (-HW, rake(HW) - SHELL_DROP)]
UPPER.prism(U_OUT, YW, YR, axis="y", mi=BRICK)

# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------
FR = 0.07          # frame width
D_FRAME = 0.15     # sash frame face behind the wall face ("set back 0.15")
D_GLASS = 0.20     # glass behind the wall face


def framed_opening(wall, outer, inner, wall_mat, z_top, cell, d_frame=D_FRAME, d_glass=D_GLASS,
                   frame_mat=SASH, frame=None):
    """Two nested pockets: the outer one's reveal keeps the wall material and its back is the
    painted frame; the inner one's sides are frame, its back is the window back (GAP behind
    the glass face)."""
    axis, D = Dfun(wall)
    C = cutter(z_top)
    C.prism(outer, D(0.25), D(-d_frame), axis, mi=(wall_mat, frame_mat, wall_mat))
    C.prism(inner, D(0.25), D(-d_glass - GAP), axis, mi=(frame_mat, back_mat(cell), frame_mat))
    register_back(wall, inner, d_glass + GAP, cell, frame)
    glass(wall, inner, d_glass)


def sill(wall, cu, w, z, proj=0.08, thick=0.10, ext=0.10):
    """Pale stone sill; its top 2 cm above the reveal floor (no coplanar faces)."""
    axis, D = Dfun(wall)
    P.prism(rect(cu - w / 2 - ext, cu + w / 2 + ext, z - thick + 0.02, z + 0.02), D(proj), D(-D_FRAME), axis,
            mi=SMOOTH)


def arched_window(wall, cu, w, z0, zs, cell, knob=False, segs=6):
    """2-over-2 round-arched sash, set back 0.15, brick hood mould with drops, stone sill."""
    axis, D = Dfun(wall)
    r = w / 2
    framed_opening(wall, arched(cu, w, z0, zs, segs), arched(cu, w - 2 * FR, z0 + FR, zs, segs), BRICK,
                   zs + r, cell)
    zm = (z0 + zs) / 2 + 0.05
    P.prism(rect(cu - r + FR, cu + r - FR, zm - 0.03, zm + 0.03), D(-D_FRAME), D(-D_GLASS), axis, mi=SASH)
    P.prism(rect(cu - 0.018, cu + 0.018, z0 + FR, zs + r - FR - 0.01), D(-D_FRAME - 0.01), D(-D_GLASS), axis,
            mi=SASH)
    sill(wall, cu, w, z0)
    # hood mould 0.12 wide, 0.12 proud, following the arch, with short drops at the springing
    P.arc_band(cu, zs, r, r + 0.12, 0.0, math.pi, D(0.12), D(0.0), axis, segs=segs, mi=BRICK)
    for s in (-1, 1):
        a, b = sorted((cu + s * r, cu + s * (r + 0.12)))
        P.prism(rect(a, b, zs - 0.22, zs), D(0.12), D(0.0), axis, mi=BRICK)
    if knob:     # the small pointed finial on top of each hood (1938 photo)
        crown = zs + r + 0.12
        P.prism([(cu - 0.05, crown - 0.01), (cu + 0.05, crown - 0.01), (cu, crown + 0.12)], D(0.10), D(0.0), axis,
                mi=BRICK)


def plain_window(wall, cu, w, z0, z1, cell, seg=False):
    """Plain (rear) or segment-headed (side ground floor) window with a stone sill."""
    axis, D = Dfun(wall)
    if seg:
        outer = segmental(cu, w, z0, z1 - 0.15, 0.15)
        inner = segmental(cu, w - 2 * FR, z0 + FR, z1 - 0.15, 0.15 - FR * 0.5)
    else:
        outer = rect(cu - w / 2, cu + w / 2, z0, z1)
        inner = rect(cu - w / 2 + FR, cu + w / 2 - FR, z0 + FR, z1 - FR)
    framed_opening(wall, outer, inner, BRICK, z1, cell, d_frame=0.12, d_glass=0.17)
    zm = (z0 + z1) / 2
    P.prism(rect(cu - w / 2 + FR, cu + w / 2 - FR, zm - 0.03, zm + 0.03), D(-0.12), D(-0.17), axis, mi=SASH)
    sill(wall, cu, w, z0, ext=0.06)


# --- upper front: 4 single windows and the middle pair on each floor ---
k = 0
for cu, w in [(BAYS[0], 1.0), (BAYS[1], 1.0), (PAIR[0], 0.8), (PAIR[1], 0.8), (BAYS[2], 1.0), (BAYS[3], 1.0)]:
    top3 = F3[1] + 0.50          # 3rd floor arch tops 10.45, 2nd 6.55 (the pair's springing is higher)
    top2 = F2[1] + 0.50
    arched_window(FRONT_U, cu, w, F2[0], top2 - w / 2, pick_cell(OFFICE, "front", 1, k), knob=True)
    arched_window(FRONT_U, cu, w, F3[0], top3 - w / 2, pick_cell(LODGE, "front", 2, k), knob=True)
    k += 1

# --- side walls: two columns each (map ticks), ground floor segment-headed ---
for wall, wname, ys in ((NORTH, "north", (3.4, 13.6)), (SOUTH, "south", (3.7, 14.1))):
    for k, y in enumerate(ys):
        u = y                                     # side-wall outlines use plain Y as u
        arched_window(wall, u, 1.0, F2[0], F2[1], pick_cell(OFFICE, wname, 1, k))
        arched_window(wall, u, 1.0, F3[0], F3[1], pick_cell(LODGE, wname, 2, k))
        cell = ("north_1", "north_7")[k] if wall is NORTH else ("dark_room", "dark_room_frame")[k]
        plain_window(wall, u, 1.0, 1.0, 3.0, cell, seg=True)

# --- rear: one column of three plain windows (map tick) ---
for i, (z0, z1) in enumerate(((1.0, 3.0), (4.9, 6.6), (8.1, 10.0))):
    plain_window(REAR, -2.55, 0.9, z0, z1, pick_cell(OFFICE if i < 2 else LODGE, "rear", i, 0))

# --- wheel window in the gable: stone ring, 8-spoke rosette, dark room behind ---
axis, D = Dfun(FRONT_U)
r_open = WHEEL_R - 0.15
wheel = circle(0.0, WHEEL_Z, r_open, 16)
CUT_U.prism(wheel, D(0.25), D(-0.16 - GAP), "y", mi=(SMOOTH, WBACK, SMOOTH))
register_back(FRONT_U, wheel, 0.16 + GAP, "dark_room")
glass(FRONT_U, wheel, 0.16)
P.arc_band(0.0, WHEEL_Z, r_open, WHEEL_R, 0.0, 2 * math.pi, D(0.05), D(-0.02), "y", segs=16, mi=SMOOTH,
           closed=True)
for i in range(8):                                   # spokes, 0.05 wide
    t = 2 * math.pi * i / 8 + math.pi / 8
    c, s = math.cos(t), math.sin(t)
    nx, nz = -s * 0.025, c * 0.025
    r0, r1 = 0.09, r_open + 0.01
    P.prism([(r0 * c + nx, WHEEL_Z + r0 * s + nz), (r0 * c - nx, WHEEL_Z + r0 * s - nz),
             (r1 * c - nx, WHEEL_Z + r1 * s - nz), (r1 * c + nx, WHEEL_Z + r1 * s + nz)], D(-0.04), D(-0.16), "y",
            mi=SMOOTH)
P.arc_band(0.0, WHEEL_Z, 0.26, 0.31, 0.0, 2 * math.pi, D(-0.04), D(-0.16), "y", segs=12, mi=SMOOTH, closed=True)
P.prism(circle(0.0, WHEEL_Z, 0.10, 8), D(-0.03), D(-0.16), "y", mi=SMOOTH)     # hub

# ---------------------------------------------------------------------------
# Pilasters, eaves: boxed cornices, modillions, brick frieze, stepped corbel course,
# paired brackets at every pilaster head
# ---------------------------------------------------------------------------
axis, D = Dfun(FRONT_U)
XC_IN = HW - CORNER_W                      # inner edge of the corner pilasters (8.65)
for xc, w in PILASTERS:
    x0, x1 = xc - w / 2, xc + w / 2
    P.prism([(x0, GT), (x1, GT), (x1, rake(x1) - O_C2), (x0, rake(x0) - O_C2)], D(0.06), D(0.0), "y", mi=BRICK)
Z_C2 = CT - O_C2                            # side corbel course bottom (10.70)
for s in (-1, 1):
    a, b = sorted((s * XC_IN, s * HW))
    P.box(a, b, YW - 0.06, YW, GT, Z_C2, mi=BRICK)                         # front face 0.60
    a, b = sorted((s * HW, s * (HW + 0.06)))
    P.box(a, b, YW - 0.06, YW + 0.30, GT, Z_C2, mi=BRICK)                  # return on the side, 0.30

# raking cornice (front and rear) and side cornices: boxed, fascia 0.35, crown strip
for s in (-1, 1):
    x1 = s * (HW + OVER)
    P.prism(rake_band(0.0, x1, 0.0, O_SOF), -0.25, YW, "y", mi=CORNICE)            # front rake
    P.prism(rake_band(0.0, x1, -0.02, 0.10), -0.30, -0.25, "y", mi=CORNICE)        # crown
    P.prism(rake_band(0.0, x1, 0.0, O_SOF), YR, YR + 0.30, "y", mi=CORNICE)        # rear rake
    a, b = sorted((s * HW, s * (HW + OVER)))
    P.box(a, b, -0.25, YR + 0.30, SOF, CT, mi=CORNICE)                              # side cornice
    a, b = sorted((s * (HW + OVER), s * (HW + OVER + 0.05)))
    P.box(a, b, -0.30, YR + 0.30, CT - 0.10, CT + 0.02, mi=CORNICE)                 # crown

# front rake bands from the apex to the corner pilasters, then horizontal returns on the
# corner pilasters and along both side walls
for s in (-1, 1):
    xa, xb = 0.0, s * XC_IN
    P.prism(rake_band(xa, xb, O_FRZ, O_C1), D(0.10), D(0.0), "y", mi=BRICK)       # corbel course, upper
    P.prism(rake_band(xa, xb, O_C1, O_C2), D(0.05), D(0.0), "y", mi=BRICK)        # lower step
    n = int(XC_IN / 0.40)
    for i in range(n):                                                            # modillions
        xm = s * (0.25 + i * (XC_IN - 0.40) / (n - 1))
        P.prism(rake_band(xm - 0.05, xm + 0.05, O_SOF, O_MOD), D(0.15), D(0.0), "y", mi=SASH)
    # horizontal returns across the corner pilaster (front face)
    a, b = sorted((s * XC_IN, s * HW))
    P.box(a, b, YW - 0.10, YW, CT - O_C1, CT - O_FRZ, mi=BRICK)
    P.box(a, b, YW - 0.05, YW, Z_C2, CT - O_C1, mi=BRICK)
    # side walls (u = Y)
    a, b = sorted((s * HW, s * (HW + 0.10)))
    P.box(a, b, YW - 0.10, YR, CT - O_C1, CT - O_FRZ, mi=BRICK)
    a, b = sorted((s * HW, s * (HW + 0.05)))
    P.box(a, b, YW - 0.05, YR, Z_C2, CT - O_C1, mi=BRICK)
    a, b = sorted((s * HW, s * (HW + 0.15)))
    n = int((YR - 1.15) / 0.40)
    for i in range(n + 1):
        y = 0.85 + i * (YR - 1.15) / n
        P.box(a, b, y - 0.05, y + 0.05, CT - O_MOD, SOF, mi=SASH)


def bracket_pair(xc):
    """Two tall pale brackets 0.08 wide, 0.14 proud, on a pilaster head, from 0.15 below the
    corbel course up to the soffit (sloping with the rake on the gable)."""
    for dx in (-0.09, 0.09):
        x0, x1 = xc + dx - 0.04, xc + dx + 0.04
        if abs(xc) < XC_IN:
            pts = rake_band(x0, x1, O_SOF, O_C2 + 0.15)
        else:
            pts = [(x0, Z_C2 - 0.15), (x1, Z_C2 - 0.15), (x1, rake(x1) - O_SOF), (x0, rake(x0) - O_SOF)]
        P.prism(pts, D(0.14), D(0.0), "y", mi=SASH)


for xc, w in PILASTERS:
    bracket_pair(xc)
for s in (-1, 1):
    bracket_pair(s * (HW - CORNER_W / 2))
    a, b = sorted((s * HW, s * (HW + 0.14)))                       # pair on the side return
    for y in (0.40, 0.58):
        P.box(a, b, y - 0.04, y + 0.04, Z_C2 - 0.15, SOF, mi=SASH)

# roof: two tin slopes (ridge along Y) between the front and rear raking cornices
for s in (-1, 1):
    P.prism([(0.0, APEX - 0.12), (s * (HW + OVER), CT - 0.12), (s * (HW + OVER), CT), (0.0, APEX)], YW, YR, "y",
            mi=ROOF)
# chimney 1 at the apex just behind the front, corbelled cap; chimney 2 on the south slope
for (x0, x1, y0, y1, zb, zt) in ((-0.45, 0.45, 0.90, 1.50, 15.0, 17.0), (7.0, 7.8, 8.7, 9.3, 12.2, 14.5)):
    P.box(x0, x1, y0, y1, zb, zt - 0.30, mi=BRICK)
    P.box(x0 - 0.06, x1 + 0.06, y0 - 0.06, y1 + 0.06, zt - 0.30, zt - 0.20, mi=BRICK)
    P.box(x0 - 0.11, x1 + 0.11, y0 - 0.11, y1 + 0.11, zt - 0.20, zt - 0.08, mi=BRICK)
    P.box(x0 - 0.04, x1 + 0.04, y0 - 0.04, y1 + 0.04, zt - 0.08, zt, mi=BRICK)

# ---------------------------------------------------------------------------
# Ground storey 90 (bank): 1921 rusticated stone front
# ---------------------------------------------------------------------------
axis, D = Dfun(FRONT_G)
PIER_N = (XN(0.0), XN(1.10))
WIN1 = (XN(1.10), XN(3.15))
DOOR = (XN(4.50), XN(6.30))
WIN2 = (XN(7.35), XN(9.00))
SDOOR = (XN(9.70), XN(10.95))

# smooth plinth to 0.75 (stops at the doors), frieze 3.95-4.20, cornice 4.20-4.40 (0.20 proud),
# all returning 0.60 along the north wall
for x0, x1 in ((-HW - 0.03, DOOR[0]), (DOOR[1], SDOOR[0]), (SDOOR[1], XS)):
    P.box(x0, x1, -0.03, 0.01, SKIRT, 0.75, mi=SMOOTH)
P.box(-HW - 0.03, -HW + 0.01, -0.03, 0.60, SKIRT, 0.75, mi=SMOOTH)
P.box(-HW - 0.02, XS, -0.02, 0.01, 3.95, 4.20, mi=SMOOTH)
P.box(-HW - 0.02, -HW + 0.01, -0.02, 0.60, 3.95, 4.20, mi=SMOOTH)
CORN = [(0.01, 4.20), (-0.06, 4.20), (-0.10, 4.25), (-0.20, 4.33), (-0.20, 4.40), (0.01, 4.40)]
P.prism(CORN, -HW - 0.20, XS, "x", mi=SMOOTH)
P.prism([(-HW + y, z) for y, z in CORN], -0.20, 0.60, "y", mi=SMOOTH)

# inscription tablet on the corner pier (letters baked into the lightmap; see the bake script)
TABLET = (-9.21, -8.23, 2.35, 3.15)
P.box(TABLET[0], TABLET[1], -0.01, 0.005, TABLET[2], TABLET[3], mi=SMOOTH)
# round bronze plaque, dark rim
pc = (PIER_N[0] + PIER_N[1]) / 2
P.prism(circle(pc, 1.60, 0.20, 12), -0.015, 0.005, "y", mi=DARK)
P.prism(circle(pc, 1.60, 0.17, 12), -0.025, -0.005, "y", mi=CORNICE)


def bank_window(x0, x1, cell):
    """Big bank window: stone reveal, pale frame 0.12 back, one big pane to the transom bar
    at 3.05, two lights above, stone sill 0.10 (0.08 proud). The cell spans the whole window."""
    z0, zt, z1 = 0.95, 3.05, 3.85
    CUT_G.prism(rect(x0, x1, z0, z1), D(0.25), D(-0.12), "y", mi=(STONE, SASH, STONE))
    f = 0.08
    xm = (x0 + x1) / 2
    frame = (x0 + f, x1 - f, z0 + f, z1 - f)
    for pane in (rect(x0 + f, x1 - f, z0 + f, zt - 0.03), rect(x0 + f, xm - 0.03, zt + 0.03, z1 - f),
                 rect(xm + 0.03, x1 - f, zt + 0.03, z1 - f)):
        CUT_G.prism(pane, D(0.25), D(-0.17 - GAP), "y", mi=(SASH, HALL, SASH))
        register_back(FRONT_G, pane, 0.17 + GAP, cell, frame)
        glass(FRONT_G, pane, 0.17)
    P.box(x0 - 0.06, x1 + 0.06, -0.08, 0.12, z0 - 0.10 + 0.02, z0 + 0.02, mi=SMOOTH)        # sill


bank_window(*WIN1, "bank_window")
bank_window(*WIN2, "bank_door")

# main door: recessed 0.50, pair of glazed oak doors to 2.75, transom 2.85-3.65, plain
# architrave, two scroll consoles carrying a small hood cornice 3.85-4.00
x0, x1 = DOOR
REC = 0.50
DT = 3.75
CUT_G.prism(rect(x0, x1, 0.0, DT), D(0.25), D(-REC), "y", mi=(SMOOTH, HALL, [SMOOTH, SMOOTH, SMOOTH, SMOOTH]))
register_back(FRONT_G, rect(x0, x1, 0.0, DT), REC, "north_4")
fy0, fy1 = REC - 0.06, REC
P.box(x0, x0 + 0.10, fy0, fy1, 0.0, DT, mi=DARK)                       # frame jambs, head, transom bar
P.box(x1 - 0.10, x1, fy0, fy1, 0.0, DT, mi=DARK)
P.box(x0 + 0.10, x1 - 0.10, fy0, fy1, 3.65, DT, mi=DARK)
P.box(x0 + 0.10, x1 - 0.10, fy0, fy1, 2.75, 2.85, mi=DARK)
xm = (x0 + x1) / 2
P.box(xm - 0.03, xm + 0.03, fy0, fy1, 2.85, 3.65, mi=DARK)            # transom mullion
for a, b in ((x0 + 0.10, xm - 0.03), (xm + 0.03, x1 - 0.10)):
    P.face(rect(a, b, 2.85, 3.65), fy1 - 0.04, "y", -1)               # transom lights
for a, b in ((x0 + 0.10, xm), (xm, x1 - 0.10)):
    a1, b1 = a + 0.005, b - 0.005
    P.box(a1, b1, fy0 + 0.01, fy1, 0.0, 1.10, mi=DARK)                # bottom rail / panel zone
    P.box(a1, a1 + 0.12, fy0 + 0.01, fy1, 1.10, 2.62, mi=DARK)        # stiles
    P.box(b1 - 0.12, b1, fy0 + 0.01, fy1, 1.10, 2.62, mi=DARK)
    P.box(a1, b1, fy0 + 0.01, fy1, 2.62, 2.75, mi=DARK)               # top rail
    P.box(a1 + 0.10, b1 - 0.10, fy0 - 0.005, fy0 + 0.01, 0.15, 0.95, mi=DARK)   # raised panel
    P.face(rect(a1 + 0.12, b1 - 0.12, 1.10, 2.62), fy1 - 0.04, "y", -1)        # glass
for a, b in ((x0 - 0.14, x0), (x1, x1 + 0.14)):                        # architrave
    P.box(a, b, -0.03, 0.01, 0.0, 3.10, mi=SMOOTH)
CONSOLE = [(0.01, 3.10), (-0.05, 3.10), (-0.09, 3.32), (-0.12, 3.50), (-0.17, 3.68), (-0.22, 3.85), (0.01, 3.85)]
for a, b in ((x0 - 0.17, x0 + 0.01), (x1 - 0.01, x1 + 0.17)):
    P.prism(CONSOLE, a, b, "x", mi=SMOOTH)
    P.prism([(-0.13, 3.40), (-0.035, 3.40), (-0.035, 3.48), (-0.13, 3.48)], a + 0.02, b - 0.02, "x", mi=SMOOTH)
P.box(x0 - 0.30, x1 + 0.30, -0.27, 0.01, 3.85, 3.93, mi=SMOOTH)        # hood cornice
P.box(x0 - 0.33, x1 + 0.33, -0.30, 0.01, 3.93, 4.00, mi=SMOOTH)
P.box(x0, x1, -0.02, 0.0, -0.01, 0.0, mi=SMOOTH)                       # (threshold edge)

# side door to the upper floors: recessed 0.20, four-panel door to 2.40, glazed transom
x0, x1 = SDOOR
CUT_G.prism(rect(x0, x1, 0.0, 3.20), D(0.25), D(-0.20), "y", mi=(SMOOTH, DARK, SMOOTH))
tr = rect(x0 + 0.12, x1 - 0.12, 2.52, 3.08)
CUT_G.prism(tr, D(0.25), D(-0.22 - GAP), "y", mi=(DARK, WBACK, DARK))
register_back(FRONT_G, tr, 0.22 + GAP, "dark_room_frame")
glass(FRONT_G, tr, 0.22)
xm = (x0 + x1) / 2
for a, b in ((x0 + 0.20, xm - 0.05), (xm + 0.05, x1 - 0.20)):
    for za, zb in ((0.20, 1.05), (1.25, 2.25)):
        P.box(a, b, 0.185, 0.20, za, zb, mi=DARK)
P.box(x0 + 0.12, x1 - 0.12, 0.185, 0.20, 2.40, 2.52, mi=DARK)           # transom bar

# ---------------------------------------------------------------------------
# Ground storey 94 (vacant): the old brick arcade (c. 1918 photo)
# ---------------------------------------------------------------------------
for x0, x1 in ((XS, XN(15.7) - 1.20), (XN(15.7) + 1.20, HW + 0.03)):
    P.box(x0, x1, -0.03, 0.01, SKIRT, 0.45, mi=SMOOTH)                 # stone plinth
P.box(HW - 0.01, HW + 0.03, -0.03, YW, SKIRT, 0.45, mi=SMOOTH)
P.box(XS, HW + 0.20, -0.20, 0.01, 4.10, 4.40, mi=SMOOTH)                # cornice band, 0.20 proud
P.box(HW - 0.01, HW + 0.20, -0.20, YW + 0.05, 4.10, 4.40, mi=SMOOTH)


def arcade_arch(cu, w, zs, d0=0.0):
    """Brick voussoir ring 0.25 wide, 0.03 proud, round the arch."""
    P.arc_band(cu, zs, w / 2, w / 2 + 0.25, 0.0, math.pi, -0.03, 0.0, "y", segs=8, mi=BRICK)


# old bank window, Xn 13.1: 1.30 wide, sill 0.95, top 3.65, vertical iron bars, empty room
cu, w, zs = XN(13.1), 1.30, 3.00
framed_opening(FRONT_G, arched(cu, w, 0.95, zs, 8), arched(cu, w - 2 * FR, 0.95 + FR, zs, 8), BRICK, GT,
               "dark_room", d_frame=0.18, d_glass=0.23)
P.prism(rect(cu - w / 2 + FR, cu + w / 2 - FR, 2.17, 2.23), D(-0.18), D(-0.23), "y", mi=SASH)
P.box(cu - w / 2 - 0.08, cu + w / 2 + 0.08, -0.08, 0.10, 0.85 + 0.02, 0.95 + 0.02, mi=SMOOTH)
arcade_arch(cu, w, zs)
for i in range(6):                                                      # bars, 0.025 square
    xb = cu - w / 2 + w * (i + 0.5) / 6
    top = zs + math.sqrt(max(0.0, (w / 2) ** 2 - (xb - cu) ** 2)) - 0.01
    P.box(xb - 0.0125, xb + 0.0125, 0.06, 0.085, 0.96, top, mi=DARK)
for zb in (1.30, 2.95):
    P.box(cu - w / 2, cu + w / 2, 0.055, 0.09, zb - 0.02, zb + 0.02, mi=DARK)

# stair-hall entrance, Xn 15.7: 1.80 wide, top 3.95, pair of panelled doors to 2.90, glazed
# fanlight, two stone steps 0.17 high out to y -0.60
cu, w = XN(15.7), 1.80
zs = 3.95 - w / 2
REC94 = 0.40
CUT_G.prism(arched(cu, w, 0.0, zs, 10), D(0.25), D(-REC94), "y", mi=(BRICK, DARK, BRICK))
fan = arched(cu, w - 0.20, 2.98, zs, 10)
CUT_G.prism(fan, D(0.25), D(-REC94 - 0.02 - GAP), "y", mi=(DARK, WBACK, DARK))
register_back(FRONT_G, fan, REC94 + 0.02 + GAP, "dark_room")
P.face(fan, REC94 + 0.02, "y", -1)
arcade_arch(cu, w, zs)
P.box(cu - w / 2, cu + w / 2, REC94 - 0.04, REC94, 2.90, 2.98, mi=DARK)    # transom bar
for a, b in ((cu - w / 2 + 0.08, cu), (cu, cu + w / 2 - 0.08)):
    for za, zb in ((0.55, 1.45), (1.65, 2.75)):
        P.box(a + 0.12, b - 0.12, REC94 - 0.015, REC94, za, zb, mi=DARK)       # raised panels
P.box(cu - 0.015, cu + 0.015, REC94 - 0.02, REC94, 0.34, 2.90, mi=DARK)     # astragal
P.box(cu - 1.20, cu + 1.20, -0.60, 0.0, SKIRT, 0.17, mi=SMOOTH)            # steps
P.box(cu - 1.20, cu + 1.20, -0.30, 0.0, SKIRT, 0.34, mi=SMOOTH)
P.box(cu - w / 2 + 0.005, cu + w / 2 - 0.005, -0.01, REC94 + 0.01, SKIRT, 0.34, mi=SMOOTH)   # landing

# arched window, Xn 17.6 (a guess; a tree hides it in c. 1918): 1.20 wide, top 3.60
cu, w, zs = XN(17.6), 1.20, 3.00
framed_opening(FRONT_G, arched(cu, w, 0.95, zs, 8), arched(cu, w - 2 * FR, 0.95 + FR, zs, 8), BRICK, GT,
               "dark_room_frame", d_frame=0.18, d_glass=0.23)
P.prism(rect(cu - w / 2 + FR, cu + w / 2 - FR, 2.17, 2.23), D(-0.18), D(-0.23), "y", mi=SASH)
P.prism(rect(cu - 0.018, cu + 0.018, 0.95 + FR, zs + w / 2 - FR), D(-0.19), D(-0.23), "y", mi=SASH)
P.box(cu - w / 2 - 0.08, cu + w / 2 + 0.08, -0.08, 0.10, 0.85 + 0.02, 0.95 + 0.02, mi=SMOOTH)
arcade_arch(cu, w, zs)

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


ground = cut_shell(GROUND, CUT_G, "MH_Ground")
upper = cut_shell(UPPER, CUT_U, "MH_Upper")
assign_atlas_uvs(ground)
assign_atlas_uvs(upper)
P.to_object("MH_Parts", col)

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Masonic Hall built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)")
# Materials, baked lighting and GLB export: run masonic_hall_bake.py (it runs this file first).
