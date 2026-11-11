"""
block_40_46.py - builds the block of frame buildings at 40-46 Main St, Flemington (east side,
just north of the Rea Building across a 3.3 m passage), as it stood c. 1920:
  A  40-42 "Auto Sales": 3-storey pale buff clapboard, arched drive-through at No. 40,
     1-storey porch with a canted show window and an "AUTO SALES" board at No. 42
  B  42's 2-storey rear wing
  C  44-46 "Shoe Shine & Fruits": 2-storey cream clapboard on the street line, shop front with
     two doors, display window, "SHOES SHINED" / "FRUITS" boards and a striped awning, two
     2nd-floor box bays over the passage, 1-storey rear part with a slanting south wall

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/block_40_46.py").read())

Every run deletes and rebuilds the "Block4046" collection. Materials, lightmap bake and GLB
export: block_40_46_bake.py (runs this file first). Pattern: rea_building.py (builders per
material, Wall frames, closed wall shells with shallow boolean recesses).

Sources: PLAN.md "Block at 40-46 Main St" spec (1921 Sanborn sheet 2 footprints and heights;
no photo shows the fronts, so all facade detail is a period-typical guess). Owner decision
2026-11-04: map-true placement (44-46 on the 1921 street line), ordinary building <= 10k tris.

Addendum 2026-11-11 (owner-approved; HCHS Stryker plate c. 1906-10 + NRHP 1980 + 1921 Sanborn):
  - a canted two-storey bay hangs from 42's 2nd and 3rd floors (centred X -1.66, 3.10 m wide at
    the wall, front face 1.40 m, 0.85 m out), bracketed band and pent roof between the storeys,
    paired brackets at the top; as in the plate, the north side face is panelled and the front
    and south faces carry 1/1 windows. 42's other two window columns move to X -3.96 / +0.64 and
    lose their shutters; the middle column is gone.
  - decision 1: the 42 porch gets a flat tin deck with a railing of sawn (cut-out) flat balusters.
  - decision 2: 40-42 gets a hipped roof (35 deg, flat deck on top) over its bracketed eave; the
    eave wraps round the bay and the bay carries its own canted hip rising into the main roof,
    with a turned finial spike at its peak (as in the plate). 44-46 keeps its shed roof.
  - decision 3 + section E: every pane is ONE glass face (builder Glass -> material `glass`)
    4 cm in front of a window back (builder WBack: shared/window_backs.jpg cells, no repeats
    side by side or above/below; builder Shop: shared/shop_interior.jpg cells for the 44-46 shop).
    The 42 show window and sale-room door look into a plain dark room.

Coordinates (metres, Blender Z-up), origin = scene (8.60, 0.15, -116.55), rotation 0 -90 0:
    X  along the street, +X = south (passage / Rea Building), -X = north (36-38)
    Y  depth: y = 0 is the 44-46 front wall (street line); 40-42 front wall at 1.98,
       porch posts at 0.30, apron slab 0 ... 1.98; awning out to -1.60
    Z  up from the sidewalk top; walls skirt down to -0.20; passage and yard at -0.15
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".
"""

import json
import math
import random
import bpy
import bmesh

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md massing table)
# ---------------------------------------------------------------------------
HW = 7.45                       # half length along the street (14.90 m)
AX0, AX1 = -HW, 1.67            # A (40-42) along X
AY0, AY1 = 1.98, 11.20          # A front / rear wall
A_TOP = 8.95                    # A wall shell top (roof deck)
BX0, BX1, BY1 = -3.95, 1.05, 18.65   # B rear wing
B_TOP = 6.00
CX0, CX1, CY1 = 1.67, HW, 17.45     # C (44-46)
C_TOP_F, C_TOP_R = 6.00, 5.65       # C shell top at the front / rear (shed roof to the rear)
C2_Y1, C2_SX = 21.36, 6.36          # C2 rear part: rear wall, slanting south wall end
C2_TOP = 3.15
SKIRT = -0.20
DECK = 0.15                     # 42 porch deck (one step up from the apron)
RECESS = 0.25                   # openings are shallow recesses this deep
ARCH_C, ARCH_W, ARCH_SPR = -5.98, 2.60, 2.25    # 40 drive-through arch (crown 3.55)
TUN_X0, TUN_X1, TUN_TOP = -7.30, -4.66, 3.60    # tunnel inside A's ground storey

# ---------------------------------------------------------------------------
# Materials (plain stand-ins; block_40_46_bake.py swaps in the textures)
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


COLOURS = {"ClapA": "#B9AE96", "ClapB": "#DCD6C4", "Trim": "#E4DFD2", "Green": "#2F4A36",
           "Roof": "#5A3D34", "Stone": "#8E8C86", "Glass": "#1A1916", "Signs": "#E2DACA",
           "WBack": "#2A2420", "Shop": "#2A2420"}
MATS = {k: plain("BK_" + k, c) for k, c in COLOURS.items()}
# builder -> material (the bake gives every builder its own UVs and tint). The tunnel lining
# and the awning iron take one dark texel of the window-back atlas (no separate material).
BUILDER_MAT = {"ClapA": "ClapA", "ClapB": "ClapB", "Trim": "Trim", "Green": "Green", "Roof": "Roof",
               "Stone": "Stone", "Glass": "Glass", "Iron": "WBack", "Tunnel": "WBack", "Atlas": "Signs",
               "WBack": "WBack", "Shop": "Shop"}

# ---------------------------------------------------------------------------
# Mesh builder (as rea_building.py)
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

    def oprism(self, wall, pts_dz, u0, u1):
        """Profile [(d, z), ...] across a wall, extruded along it from u0 to u1."""
        self._extrude([wall.pt(u0, z, d) for d, z in pts_dz], [wall.pt(u1, z, d) for d, z in pts_dz])

    def lathe(self, cx, cy, rings, sides=8, rot=0.5):
        """Vertical solid of revolution: rings [(radius, z), ...] bottom to top."""
        bm = self.bm
        loops = [[bm.verts.new((cx + r * math.cos(2 * math.pi * (i + rot) / sides),
                                cy + r * math.sin(2 * math.pi * (i + rot) / sides), z)) for i in range(sides)]
                 for r, z in rings]
        faces = [bm.faces.new(list(reversed(loops[0]))), bm.faces.new(loops[-1])]
        for a, b in zip(loops, loops[1:]):
            for i in range(sides):
                j = (i + 1) % sides
                faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
        self._closed(faces)

    def solid(self, cos, faces_idx):
        """Closed solid from explicit vertices and faces (index lists)."""
        vs = [self.bm.verts.new(c) for c in cos]
        self._closed([self.bm.faces.new([vs[i] for i in f]) for f in faces_idx])

    def quad(self, wall, u0, u1, z0, z1, d):
        """ONE single-sided face on a wall plane (d out from the wall face), facing outward."""
        vs = [self.bm.verts.new(wall.pt(u, z, d)) for u, z in ((u0, z0), (u1, z0), (u1, z1), (u0, z1))]
        f = self.bm.faces.new(vs)
        f[self.rid_layer] = self.rid
        return f

    def flat(self, pts, z, up=True):
        """ONE horizontal single-sided face (plan outline), facing up or down."""
        vs = [self.bm.verts.new((x, y, z)) for x, y in pts]
        f = self.bm.faces.new(vs)
        f.normal_update()
        if (f.normal.z > 0) != up:
            f.normal_flip()
        f[self.rid_layer] = self.rid
        return f

    def sweep(self, line, profile, closed=False):
        """Profile [(p, z), ...] (p = out from the wall line, mitred) swept along a plan
        polyline that has the outside on its right; closed loops need no end caps."""
        off = offset_closed if closed else offset_line
        rings = [[self.bm.verts.new((x, y, z)) for x, y in off(line, p)] for p, z in profile]
        n, m = len(line), len(profile)
        faces = []
        for j in range(m):
            r0, r1 = rings[j], rings[(j + 1) % m]
            for i in range(n if closed else n - 1):
                i2 = (i + 1) % n
                faces.append(self.bm.faces.new([r0[i], r0[i2], r1[i2], r1[i]]))
        if not closed:
            faces.append(self.bm.faces.new([r[0] for r in rings]))
            faces.append(self.bm.faces.new([r[-1] for r in reversed(rings)]))
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


def arc_pts(cu, zc, r, a0, a1, segs):
    return [(cu + r * math.cos(a0 + (a1 - a0) * i / segs), zc + r * math.sin(a0 + (a1 - a0) * i / segs))
            for i in range(segs + 1)]


def band(cu, zc, r_in, r_out, a0, a1, segs):
    return arc_pts(cu, zc, r_out, a0, a1, segs) + arc_pts(cu, zc, r_in, a1, a0, segs)


def round_outline(cu, w, z0, zs, segs):
    r = w / 2
    return [(cu - r, z0), (cu + r, z0)] + arc_pts(cu, zs, r, 0.0, math.pi, segs)


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
        if i == 0 or i == n - 1:
            nx, ny = norms[0] if i == 0 else norms[-1]
            out.append((x + p * nx, y + p * ny))
        else:
            a, b = norms[i - 1], norms[i]
            k = 1 + a[0] * b[0] + a[1] * b[1]
            out.append((x + p * (a[0] + b[0]) / k, y + p * (a[1] + b[1]) / k))
    return out


def offset_closed(poly, p):
    """Closed plan loop (outside on the right), offset outward by p (mitred at every corner)."""
    n = len(poly)
    norms = []
    for i in range(n):
        (xa, ya), (xb, yb) = poly[i], poly[(i + 1) % n]
        L = math.hypot(xb - xa, yb - ya)
        norms.append(((yb - ya) / L, -(xb - xa) / L))
    out = []
    for i, (x, y) in enumerate(poly):
        a, b = norms[i - 1], norms[i]
        k = 1 + a[0] * b[0] + a[1] * b[1]
        out.append((x + p * (a[0] + b[0]) / k, y + p * (a[1] + b[1]) / k))
    return out


def plan_band(line, p, z0, z1, mb, p_in=0.0):
    """Band along an open wall polyline: outer edge offset p, inner edge p_in (negative = into the wall)."""
    outer = offset_line(line, p)
    inner = offset_line(line, p_in)
    mb.prism(outer + inner[::-1], z0, z1, axis="z")


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


col = fresh_collection("Block4046")
G = {k: MB() for k in BUILDER_MAT}
CA, CB, T, GR, R, ST, GL, IR, TU, AT, WB, SH = (G[k] for k in ("ClapA", "ClapB", "Trim", "Green", "Roof", "Stone",
                                                               "Glass", "Iron", "Tunnel", "Atlas", "WBack", "Shop"))
# wall shells (closed solids) and their cutters: name -> (shell, cutter, material)
SHELLS = {k: (MB(), MB(), m) for k, m in (("ShellA", "ClapA"), ("ShellB", "ClapA"), ("ShellC", "ClapB"),
                                          ("ShellC2", "ClapB"), ("Bay1", "ClapB"), ("Bay2", "ClapB"),
                                          ("Bay42", "ClapA"))}
SA, SB, SC, SC2, SY1, SY2, SH42 = (SHELLS[k][0] for k in SHELLS)
KA, KB, KC, KC2, KY1, KY2, K42 = (SHELLS[k][1] for k in SHELLS)

# ---------------------------------------------------------------------------
# Window backs (section E): cells of the shared atlases, picked so that no two windows side
# by side or above/below show the same cell. BACKREC[rid] -> UV record (read by the bake).
# ---------------------------------------------------------------------------
WB_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\window_backs.json"))["cells"]
SHOP_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\shop_interior.json"))["cells"]
GAP = 0.04                      # window back this far behind the glass
OFFICE = {"blind_cream_high": 3, "blind_cream_half": 3, "blind_cream_low": 2, "blind_green_high": 2,
          "blind_green_half": 2, "blind_green_low": 1, "dark_room": 2, "dark_room_frame": 2}
ROOMS = {"lace": 2, "lace_blind_cream": 2, "lace_blind_green": 2, "lace_full_blind_cream": 1,
         "curtains_beige": 2, "curtains_olive": 1, "curtains_maroon_blind": 1, "blind_cream_half": 1}
BACKSIDE = {"blind_cream_high": 2, "blind_cream_half": 2, "blind_green_half": 1, "blind_green_low": 1,
            "dark_room": 3, "dark_room_frame": 3}
_wb_rng = random.Random(4042)
_wb_grid = {}
BACKREC = {}


def pick(weights, wall, row, colm):
    g = _wb_grid.setdefault(wall, {})
    avoid = {g.get((row, colm - 1)), g.get((row, colm + 1)), g.get((row - 1, colm)), g.get((row + 1, colm))}
    names = [n for n in weights if n not in avoid]
    cell = _wb_rng.choices(names, weights=[weights[n] for n in names])[0]
    g[(row, colm)] = cell
    return cell


def back(wall, u0, u1, z0, z1, d, cell):
    """Window back: one face on the wall plane at depth d (negative = into the wall)."""
    shop = cell in SHOP_CELLS
    mb = SH if shop else WB
    rid = len(BACKREC) + 1
    BACKREC[rid] = dict(wall=(wall.p0, wall.n), u0=u0, u1=u1, z0=z0, z1=z1,
                        uv=(SHOP_CELLS if shop else WB_CELLS)[cell]["uv"])
    mb.rid = rid
    mb.quad(wall, u0, u1, z0, z1, d)
    mb.rid = 0


def dark_flat(pts, z, up):
    """Floor / ceiling of the dark sale room behind the show window (one dark texel)."""
    rid = len(BACKREC) + 1
    u0, v0, u1, v1 = WB_CELLS["dark_room_frame"]["uv"]
    BACKREC[rid] = dict(const=((u0 + u1) / 2, v0 + 0.2 * (v1 - v0)))
    WB.rid = rid
    WB.flat(pts, z, up)
    WB.rid = 0


def pane(wall, u0, u1, z0, z1, d_glass, cell):
    """Glass face at depth d_glass with its window back GAP behind it."""
    back(wall, u0, u1, z0, z1, d_glass - GAP, cell)
    GL.quad(wall, u0, u1, z0, z1, d_glass)

ATLAS = {}                      # rid -> record (read by block_40_46_bake.py)


def atlas_rec(**kw):
    rid = len(ATLAS) + 1
    ATLAS[rid] = kw
    AT.rid = rid
    return rid


def wall_rec(w):
    return (w.p0, w.n)


# Walls (u: FRONT x, SOUTH y, NORTH -y, REAR -x)
A_FRONT = Wall((0.0, AY0), (0, -1), KA)
A_NORTH = Wall((AX0, 0.0), (-1, 0), KA)
A_SOUTH = Wall((AX1, 0.0), (1, 0), KA)
A_REAR = Wall((0.0, AY1), (0, 1), KA)
B_NORTH = Wall((BX0, 0.0), (-1, 0), KB)
B_REAR = Wall((0.0, BY1), (0, 1), KB)
C_FRONT = Wall((0.0, 0.0), (0, -1), KC)
C_SOUTH = Wall((CX1, 0.0), (1, 0), KC)
C_REAR = Wall((0.0, CY1), (0, 1), KC)
C2_REAR = Wall((0.0, C2_Y1), (0, 1), KC2)
BAY_S = Wall((CX1 + 0.63, 0.0), (1, 0), None)        # bay south faces (cut set per bay)

# ---------------------------------------------------------------------------
# Shells
# ---------------------------------------------------------------------------
SA.box(AX0, AX1, AY0, AY1, SKIRT, A_TOP)
SB.box(BX0, BX1, AY1, BY1, SKIRT, B_TOP)
SC.prism([(0.0, SKIRT), (CY1, SKIRT), (CY1, C_TOP_R), (0.0, C_TOP_F)], CX0, CX1, axis="x")
SC2.prism([(CX0, CY1), (CX1, CY1), (C2_SX, C2_Y1), (CX0, C2_Y1)], SKIRT, C2_TOP, axis="z")
BAYS = ((5.00, 7.97, SY1, KY1), (14.06, 17.45, SY2, KY2))
BAY_Z0, BAY_Z1, BAY_OUT = 3.55, 5.85, 0.63
for y0, y1, sh, _ in BAYS:
    sh.box(CX1, CX1 + BAY_OUT, y0, y1, BAY_Z0, BAY_Z1)

# ---------------------------------------------------------------------------
# Windows, shutters, doors
# ---------------------------------------------------------------------------


def shutters(wall, cu, half, z0, z1, leaf=0.40):
    """Open louvred shutters flat beside the casing, 0.03 off the wall (atlas louvres)."""
    for sgn in (-1, 1):
        u0, u1 = sorted((cu + sgn * (half + 0.13), cu + sgn * (half + 0.13 + leaf)))
        atlas_rec(region="louvre", mode="rect", wall=wall_rec(wall), u0=u0, u1=u1, z0=z0, z1=z1)
        AT.wbox(wall, u0, u1, z0, z1, 0.03, 0.06)
    AT.rid = 0


def window(wall, cu, z0, w, h, cell, shut=0.40, full=True, cut=None, muntin=True):
    """2/2 (or 1/1) sash window in a 0.25 recess: one glass face 4 cm in front of a window
    back (section E), sash rails and muntin, cased trim 0.12 with a small cap cornice (full)
    or plain casing 0.09, sill, optional open louvred shutters."""
    hw = w / 2
    z1 = z0 + h
    (cut or wall.cut).wbox(wall, cu - hw, cu + hw, z0, z1, -RECESS, 0.25)
    pane(wall, cu - hw, cu + hw, z0, z1, -0.17, cell)
    zm = z0 + h / 2
    s = 0.05
    if full:
        T.wbox(wall, cu - hw, cu + hw, z1 - s, z1, -0.15, -0.09)                 # top rail
        T.wbox(wall, cu - hw, cu + hw, z0, z0 + 0.07, -0.15, -0.09)              # bottom rail
        for a in (cu - hw, cu + hw - s):
            T.wbox(wall, a, a + s, z0 + 0.07, z1 - s, -0.15, -0.09)              # stiles
    T.wbox(wall, cu - hw, cu + hw, zm - 0.03, zm + 0.03, -0.15, -0.10)           # meeting rail
    if muntin:
        T.wbox(wall, cu - 0.016, cu + 0.016, z0, z1, -0.15, -0.12)               # muntin
    c = 0.12 if full else 0.09
    T.wbox(wall, cu - hw - c, cu - hw, z0, z1 + c, -0.02, 0.03)                  # casing
    T.wbox(wall, cu + hw, cu + hw + c, z0, z1 + c, -0.02, 0.03)
    T.wbox(wall, cu - hw, cu + hw, z1, z1 + c, -0.02, 0.03)
    if full:
        T.wbox(wall, cu - hw - c - 0.05, cu + hw + c + 0.05, z1 + c, z1 + c + 0.06, -0.02, 0.08)   # cap
    T.wbox(wall, cu - hw - c - 0.03, cu + hw + c + 0.03, z0 - 0.05, z0, -0.16, 0.07)            # sill
    if shut:
        shutters(wall, cu, hw, z0, z1, leaf=shut)


def panel_door(wall, cu, w, z0, z1, mb, d=-0.14, glazed_from=None, cut=True, transom=0.0, cells=None):
    """Door leaf (green) in a recess: stiles/rails, raised panels or a glazed upper half
    (glass face with a window back in the leaf's thickness); optional transom light above;
    plain casing on the wall."""
    hw = w / 2
    if cut:
        wall.cut.wbox(wall, cu - hw, cu + hw, z0, z1 + transom, -RECESS, 0.25)
    top = z1 - 0.12
    if glazed_from:
        g0, g1 = cu - hw + 0.11, cu + hw - 0.11
        mb.wbox(wall, cu - hw, g0, z0, z1, d - 0.05, d)                            # stiles
        mb.wbox(wall, g1, cu + hw, z0, z1, d - 0.05, d)
        mb.wbox(wall, g0, g1, z0, glazed_from, d - 0.05, d)                        # lower half
        mb.wbox(wall, g0, g1, top, z1, d - 0.05, d)                                # top rail
        pane(wall, g0, g1, glazed_from, top, d - 0.008, cells[0])
        mb.wbox(wall, cu - hw + 0.14, cu + hw - 0.14, z0 + 0.22, glazed_from - 0.14, d, d + 0.015)
    else:
        mb.wbox(wall, cu - hw, cu + hw, z0, z1, d - 0.05, d)
        for ua, ub in ((cu - hw + 0.12, cu - 0.04), (cu + 0.04, cu + hw - 0.12)):
            for za, zb in ((z0 + 0.20, z0 + (z1 - z0) * 0.42), (z0 + (z1 - z0) * 0.50, top)):
                mb.wbox(wall, ua, ub, za, zb, d, d + 0.015)
    if transom:
        T.wbox(wall, cu - hw, cu + hw, z1, z1 + 0.05, d - 0.05, d + 0.02)          # transom bar
        pane(wall, cu - hw, cu + hw, z1 + 0.05, z1 + transom, d - 0.03, cells[1])
    T.wbox(wall, cu - hw - 0.10, cu - hw, z0, z1 + transom + 0.10, -0.02, 0.03)    # casing
    T.wbox(wall, cu + hw, cu + hw + 0.10, z0, z1 + transom + 0.10, -0.02, 0.03)
    T.wbox(wall, cu - hw, cu + hw, z1 + transom, z1 + transom + 0.10, -0.02, 0.03)


# --- A (40-42) upper floors: 40's column shuttered; 42's two columns beside the bay -----
A_BAYS = (-5.98, -3.96, 0.64)                    # 42's middle column gave way to the hanging bay
A_FLOORS = ((4.35, 1.65), (6.85, 1.40))          # (sill, height); 3rd floor fits under the frieze
A_COLS = {-5.98: 0, -3.96: 1, 0.64: 4}           # window-back grid columns (bay = 2, 3)
for x in A_BAYS:
    for row, (sill, h) in enumerate(A_FLOORS):
        cell = pick(OFFICE if row == 0 else ROOMS, "A_FRONT", row, A_COLS[x])
        if x < -5:
            window(A_FRONT, x, sill, 0.85, h, cell)
        else:
            window(A_FRONT, x, sill, 0.80, h, cell, shut=0)
# side walls above 44-46 / 36-38 (3rd floor only), rear wall
for i, y in enumerate((4.5, 8.5)):
    window(A_NORTH, -y, 6.85, 0.85, 1.40, pick(BACKSIDE, "A_NORTH", 0, i), shut=0, full=False)
    window(A_SOUTH, y, 6.85, 0.85, 1.40, pick(BACKSIDE, "A_SOUTH", 0, i), shut=0, full=False)
window(A_REAR, 5.98, 4.35, 0.85, 1.65, pick(BACKSIDE, "A_REAR", 0, 1), shut=0, full=False)
for x in (-5.98, -1.42):
    window(A_REAR, -x, 6.85, 0.85, 1.40, pick(BACKSIDE, "A_REAR", 1, 1 if x < -5 else 0), shut=0, full=False)

# corner boards 0.15 (front, both ends; side faces where exposed above 6.10)
for x0 in (AX0, AX1 - 0.15):
    T.box(x0, x0 + 0.15, AY0 - 0.03, AY0, ARCH_SPR if x0 < 0 else DECK, 8.40)
for wall, u0 in ((A_NORTH, -AY0 - 0.15), (A_SOUTH, AY0)):
    T.wbox(wall, u0, u0 + 0.15, 6.0, 8.40, -0.01, 0.03)
for wall, u0 in ((A_NORTH, -AY1), (A_SOUTH, AY1 - 0.15)):
    T.wbox(wall, u0, u0 + 0.15, 6.0, 8.40, -0.01, 0.03)

# --- 42: canted two-storey bay hanging from the 2nd and 3rd floors ----------------------
# Plan at the wall X -3.21 ... -0.11, front face X -2.36 ... -0.96 at Y 1.13 (0.85 out), sides
# at 45 deg. The plan lines run on into the wall (Y 2.40) so every sweep ends inside it.
BAY_Z0, BAY_TOP = 3.70, 9.10
BAY_IN = [(-3.21, AY0), (-2.36, 1.13), (-0.96, 1.13), (-0.11, AY0)]
BAY_LINE = [(-3.63, 2.40), (-2.36, 1.13), (-0.96, 1.13), (0.31, 2.40)]
SH42.prism(BAY_LINE, BAY_Z0, BAY_TOP, axis="z")
F_N = Wall(BAY_IN[0], (-math.sqrt(0.5), -math.sqrt(0.5)), K42)    # north face, u 0 (wall) ... 1.20 (angle)
F_F = Wall(BAY_IN[1], (0.0, -1.0), K42)                             # front face, u 0 ... 1.40
F_S = Wall(BAY_IN[2], (math.sqrt(0.5), -math.sqrt(0.5)), K42)      # south face, u 0 (angle) ... 1.20
LS = math.hypot(0.85, 0.85)                                         # side face length 1.20
BAY_LOW, BAY_UP = (4.35, 1.50), (6.85, 1.40)                        # (sill, height) per storey
for row, (sill, h) in enumerate((BAY_LOW, BAY_UP)):
    w_ = OFFICE if row == 0 else ROOMS
    window(F_F, 0.70, sill, 0.90, h, pick(w_, "A_FRONT", row, 2), shut=0, full=False, muntin=False)
    window(F_S, LS / 2, sill, 0.55, h, pick(w_, "A_FRONT", row, 3), shut=0, full=False, muntin=False)


def panel(wall, u0, u1, z0, z1):
    """Flat panel: a board with a smaller raised board on it (reads as a moulded panel)."""
    T.wbox(wall, u0, u1, z0, z1, -0.01, 0.015)
    T.wbox(wall, u0 + 0.05, u1 - 0.05, z0 + 0.05, z1 - 0.05, 0.0, 0.03)


panel(F_F, 0.36, 1.04, 3.92, 4.24)                                   # under the windows
panel(F_S, 0.24, LS - 0.24, 3.92, 4.24)
panel(F_F, 0.36, 1.04, 6.60, 6.78)
panel(F_S, 0.24, LS - 0.24, 6.60, 6.78)
panel(F_N, 0.30, LS - 0.30, 3.92, 4.24)                              # north face: panels only (plate)
panel(F_N, 0.30, LS - 0.30, 4.35, 5.85)
panel(F_N, 0.30, LS - 0.30, 6.60, 6.78)
panel(F_N, 0.30, LS - 0.30, 6.85, 8.25)
for x, y in BAY_IN[1:3]:                                             # corner posts at the angles
    T.lathe(x, y, [(0.07, BAY_Z0 + 0.15), (0.07, 8.40)], sides=8, rot=0.0)
# moulded skirt at the bottom, bracketed band and pent roof between the storeys
T.sweep(BAY_LINE, [(-0.05, BAY_Z0), (0.05, BAY_Z0), (0.05, BAY_Z0 + 0.15), (-0.05, BAY_Z0 + 0.15)])
T.sweep(BAY_LINE, [(-0.05, 5.95), (0.03, 5.95), (0.03, 6.22), (-0.05, 6.22)])
R.sweep(BAY_LINE, [(-0.05, 6.20), (0.32, 6.20), (0.32, 6.27), (-0.05, 6.62)])
BRACKET_M = [(0.0, 6.20), (0.26, 6.20), (0.26, 6.16), (0.18, 6.11), (0.10, 6.05), (0.05, 5.95), (0.0, 5.95)]
for wall, u in ((F_F, 0.10), (F_F, 1.30), (F_N, 0.12), (F_S, LS - 0.12)):
    T.oprism(wall, BRACKET_M, u - 0.045, u + 0.045)
# two small corbels under the front angles, standing on the porch deck
CORBEL = [(-0.28, BAY_Z0), (0.02, BAY_Z0), (0.02, BAY_Z0 - 0.06), (-0.06, BAY_Z0 - 0.14),
          (-0.10, 3.48), (-0.28, 3.48)]
for u in (0.12, 1.28):
    T.oprism(F_F, CORBEL, u - 0.05, u + 0.05)

# --- 40: drive-through arch, tunnel, rear doors ----------------------------------
arch = round_outline(ARCH_C, ARCH_W, -0.30, ARCH_SPR, 12)
A_FRONT.cut.wprism(A_FRONT, arch, -0.40, 0.25)
KA.box(TUN_X0, TUN_X1, AY0 + 0.30, AY1 - 0.30, -0.30, TUN_TOP)
A_REAR.cut.wprism(A_REAR, round_outline(-ARCH_C, ARCH_W, -0.30, ARCH_SPR, 12), -0.40, 0.25)
# dark plank lining inside the tunnel, stone floor through it
TU.box(TUN_X0, TUN_X0 + 0.02, AY0 + 0.30, AY1 - 0.30, 0.0, TUN_TOP)
TU.box(TUN_X1 - 0.02, TUN_X1, AY0 + 0.30, AY1 - 0.30, 0.0, TUN_TOP)
TU.box(TUN_X0, TUN_X1, AY0 + 0.30, AY1 - 0.30, TUN_TOP - 0.02, TUN_TOP)
ST.box(TUN_X0, TUN_X1, AY0, AY1 - 0.15, SKIRT, 0.01)
# archivolt 0.17 with a keyblock, jamb strips
R_A = ARCH_W / 2
T.wprism(A_FRONT, band(ARCH_C, ARCH_SPR, R_A, R_A + 0.17, 0.0, math.pi, 12), -0.01, 0.035)
for u0 in (ARCH_C - R_A - 0.17, ARCH_C + R_A):
    T.wbox(A_FRONT, u0, u0 + 0.17, 0.01, ARCH_SPR, -0.01, 0.035)
T.wbox(A_FRONT, ARCH_C - R_A - 0.21, ARCH_C - R_A, ARCH_SPR - 0.10, ARCH_SPR, -0.01, 0.06)   # imposts
T.wbox(A_FRONT, ARCH_C + R_A, ARCH_C + R_A + 0.21, ARCH_SPR - 0.10, ARCH_SPR, -0.01, 0.06)
crown = ARCH_SPR + R_A
T.wprism(A_FRONT, [(ARCH_C - 0.09, crown - 0.04), (ARCH_C + 0.09, crown - 0.04),
                   (ARCH_C + 0.12, crown + 0.27), (ARCH_C - 0.12, crown + 0.27)], -0.01, 0.07)
# closed plank double doors in the rear arch (green), meeting stile and battens
rear_arch = round_outline(-ARCH_C, ARCH_W, 0.0, ARCH_SPR, 12)
GR.wprism(A_REAR, rear_arch, -0.22, -0.16)
GR.wbox(A_REAR, -ARCH_C - 0.04, -ARCH_C + 0.04, 0.0, crown - 0.02, -0.16, -0.13)
for z in (0.45, 1.80):
    GR.wbox(A_REAR, -ARCH_C - R_A + 0.02, -ARCH_C + R_A - 0.02, z, z + 0.14, -0.16, -0.14)
# the same doors seen from inside the tunnel are the back of that solid; rear sill
ST.box(TUN_X0, TUN_X1, AY1 - 0.15, AY1 + 0.25, SKIRT, 0.0)

# --- 42: canted show window, shop door, stair door ------------------------------
PORCH_X0, PORCH_X1, PORCH_Y0 = -4.51, AX1, 0.21
BAY_PLAN = [(-3.28, AY0 + 0.02), (-2.65, 0.85), (-0.67, 0.85), (0.11, AY0 + 0.02)]
T.prism(BAY_PLAN, DECK, 0.75, axis="z")                                        # bulkhead
# plate glass: one face per side 0.04 inside the outline, the plain dark sale room behind it
# (decision 3): window backs 0.04 further in, a dark floor and ceiling
SW_G, SW_B = offset_line(BAY_PLAN, -0.04), offset_line(BAY_PLAN, -0.08)
for i, cell in enumerate(("dark_room", "dark_room_frame", "dark_room")):
    (xa, ya), (xb, yb) = SW_G[i], SW_G[i + 1]
    L_ = math.hypot(xb - xa, yb - ya)
    side = Wall((xa, ya), ((yb - ya) / L_, -(xb - xa) / L_))
    GL.quad(side, 0.0, L_, 0.78, 2.86, 0.0)
    (xa, ya), (xb, yb) = SW_B[i], SW_B[i + 1]
    L_ = math.hypot(xb - xa, yb - ya)
    back(Wall((xa, ya), ((yb - ya) / L_, -(xb - xa) / L_)), 0.0, L_, 0.78, 2.86, 0.0, cell)
dark_flat(SW_B, 0.782, True)
dark_flat(SW_B, 2.858, False)
T.prism(offset_line(BAY_PLAN, 0.03), 0.72, 0.78, axis="z")                       # sill rail
T.prism(offset_line(BAY_PLAN, 0.02), 2.86, 2.98, axis="z")                       # head
T.prism(offset_line(BAY_PLAN, 0.08), 2.98, 3.10, axis="z")                       # small cornice
for (x, y) in BAY_PLAN[1:3]:
    T.lathe(x, y, [(0.06, 0.75), (0.06, 2.88)], sides=4, rot=0.5)               # corner posts
for (xa, ya), (xb, yb) in zip(BAY_PLAN, BAY_PLAN[1:]):                          # bulkhead panels
    L = math.hypot(xb - xa, yb - ya)
    nx, ny = (yb - ya) / L, -(xb - xa) / L
    side = Wall((xa, ya), (nx, ny))
    T.wbox(side, 0.14, L - 0.14, DECK + 0.12, 0.62, -0.01, 0.015)
panel_door(A_FRONT, 0.90, 1.00, DECK, 2.45, GR, glazed_from=1.20, transom=0.40,
           cells=("dark_room_frame", "dark_room"))                               # sale-room door
panel_door(A_FRONT, -3.90, 0.90, DECK, 2.45, GR)                                 # stair door

# --- 42 porch: stone deck, 4 chamfered posts, fascia, "AUTO SALES" board, shed roof ---
ST.box(PORCH_X0, PORCH_X1, PORCH_Y0, AY0, 0.0, DECK)
ST.box(-HW, AX1, 0.0, AY0, SKIRT, 0.01)                                          # apron slab
for x in (-4.40, -2.80, 0.05, 1.56):
    T.lathe(x, 0.30, [(0.10, DECK), (0.10, 0.45)], sides=4)                      # base block
    T.lathe(x, 0.30, [(0.075, 0.45), (0.075, 2.82)], sides=8, rot=0.0)           # chamfered shaft
    T.lathe(x, 0.30, [(0.10, 2.82), (0.10, 3.00)], sides=4)                      # cap block
T.box(PORCH_X0, PORCH_X1, PORCH_Y0, 0.36, 3.00, 3.30)                            # front fascia / beam
T.box(PORCH_X0, PORCH_X0 + 0.08, PORCH_Y0, AY0, 3.00, 3.30)                      # north fascia
T.box(PORCH_X0, PORCH_X1, 0.36, AY0, 3.24, 3.27)                                 # porch ceiling boards
# flat tin deck (decision 1): 3.45 at the front, 3.55 at the wall, under the hanging bay
DECK_F, DECK_W = 3.45, 3.55
R.prism([(PORCH_Y0 - 0.02, 3.29), (AY0, 3.29), (AY0, DECK_W), (PORCH_Y0 - 0.02, DECK_F)],
        PORCH_X0 - 0.06, PORCH_X1, axis="x")
AUTO = (-3.66, 0.34, 2.98, 3.48)
atlas_rec(region="auto", mode="rect", wall=wall_rec(A_FRONT), u0=AUTO[0], u1=AUTO[1], z0=AUTO[2], z1=AUTO[3])
AT.box(AUTO[0], AUTO[1], PORCH_Y0 - 0.04, PORCH_Y0, AUTO[2], AUTO[3])
AT.rid = 0

# --- 42 porch railing: posts over the porch posts, rails, sawn (cut-out) flat balusters ---
# (Stryker plate: flat boards whose shaped edges leave round-headed openings between them)
RAIL_Y = 0.30
RZ = DECK_F + 0.005                                  # rail base at the front of the deck
BAL = [(0.045, 0.0), (0.045, 0.07), (0.026, 0.30), (0.045, 0.45), (0.084, 0.55), (0.084, 0.62)]
BAL = BAL + [(-u, v) for u, v in reversed(BAL)]
PITCH = 0.17


def balusters(wall, u0, u1, z0):
    n = max(1, int(round((u1 - u0) / PITCH)))
    step = (u1 - u0) / n
    for k in range(n):
        uc = u0 + (k + 0.5) * step
        T.wprism(wall, [(uc + u, z0 + v) for u, v in BAL], -0.0125, 0.0125)


R_FRONT = Wall((0.0, RAIL_Y), (0, -1))
R_NORTH = Wall((PORCH_X0 + 0.06, 0.0), (-1, 0))
for x in (-4.40, -2.80, 0.05, 1.56):                                              # newel posts
    T.lathe(x, RAIL_Y, [(0.085, DECK_F - 0.02), (0.085, RZ + 0.86), (0.11, RZ + 0.86), (0.11, RZ + 0.92)], sides=4)
T.lathe(PORCH_X0 + 0.06, AY0 - 0.06, [(0.085, DECK_W - 0.02), (0.085, RZ + 0.86), (0.11, RZ + 0.86),
                                      (0.11, RZ + 0.92)], sides=4)
for wall, u0, u1 in ((R_FRONT, -4.40, 1.56), (R_NORTH, -(AY0 - 0.06), -RAIL_Y)):
    T.wbox(wall, u0, u1, RZ + 0.06, RZ + 0.12, -0.03, 0.03)                       # bottom rail
    T.wbox(wall, u0, u1, RZ + 0.74, RZ + 0.80, -0.025, 0.025)                     # sub rail
    T.wbox(wall, u0, u1, RZ + 0.80, RZ + 0.86, -0.05, 0.05)                       # top rail (cap)
for a, b in ((-4.40, -2.80), (-2.80, 0.05), (0.05, 1.56)):
    balusters(R_FRONT, a + 0.06, b - 0.06, RZ + 0.12)
balusters(R_NORTH, -(AY0 - 0.12), -(RAIL_Y + 0.06), RZ + 0.12)

# --- A eave (frieze, bracketed cornice) all round, wrapping round the bay ---------------
A_LOOP = [(AX0, AY0)] + BAY_IN + [(AX1, AY0), (AX1, AY1), (AX0, AY1)]
EAVE = [(-0.30, 8.40), (0.035, 8.40), (0.035, 8.85), (0.12, 8.85), (0.12, 8.92), (0.50, 8.92),
        (0.50, 9.06), (0.55, 9.06), (0.55, 9.15), (-0.30, 9.15)]
T.sweep(A_LOOP, EAVE, closed=True)

BRACKET_A = [(0.0, 8.92), (0.45, 8.92), (0.45, 8.86), (0.36, 8.79), (0.24, 8.73), (0.15, 8.62),
             (0.10, 8.50), (0.08, 8.40), (0.0, 8.40)]
for x in (-7.33, -7.11, -5.43, -4.56, -3.33, 0.03, 1.33, 1.55):
    T.oprism(A_FRONT, BRACKET_A, x - 0.06, x + 0.06)
# on the bay: paired at the two front angles, single where it meets the wall
for wall, u in ((F_N, 0.14), (F_N, LS - 0.12), (F_F, 0.12), (F_F, 1.28), (F_S, 0.12), (F_S, LS - 0.14)):
    T.oprism(wall, BRACKET_A, u - 0.055, u + 0.055)

# --- A roof (decision 2): hipped, 35 deg, flat deck on top; the bay's own canted hip rises
# into it, with a turned finial spike at its peak (Stryker plate) -------------------------
EAVE_Z0, EAVE_Z1 = 9.15, 9.22
ROOF_RISE = 1.25
ROOF_IN = ROOF_RISE / math.tan(math.radians(35))
RX0, RX1, RY0, RY1 = AX0 - 0.55, AX1 + 0.55, AY0 - 0.55, AY1 + 0.55
TOP_Z = EAVE_Z1 + ROOF_RISE
rect_b = [(RX0, RY0), (RX1, RY0), (RX1, RY1), (RX0, RY1)]
rect_t = [(RX0 + ROOF_IN, RY0 + ROOF_IN), (RX1 - ROOF_IN, RY0 + ROOF_IN),
          (RX1 - ROOF_IN, RY1 - ROOF_IN), (RX0 + ROOF_IN, RY1 - ROOF_IN)]
R.solid([(x, y, EAVE_Z0) for x, y in rect_b] + [(x, y, EAVE_Z1) for x, y in rect_b] +
        [(x, y, TOP_Z) for x, y in rect_t],
        [(3, 2, 1, 0), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
         (4, 5, 9, 8), (5, 6, 10, 9), (6, 7, 11, 10), (7, 4, 8, 11), (8, 9, 10, 11)])
eave_pts = offset_closed(A_LOOP, 0.55)[1:5]          # W_L, F_L, F_R, W_R (W on the main eave line)
PEAK = ((eave_pts[0][0] + eave_pts[3][0]) / 2, RY0 + ROOF_IN, TOP_Z)
R.solid([(x, y, EAVE_Z0) for x, y in eave_pts] + [(x, y, EAVE_Z1) for x, y in eave_pts] + [PEAK],
        [(3, 2, 1, 0), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
         (4, 5, 8), (5, 6, 8), (6, 7, 8), (7, 4, 8)])
px, py, pz = PEAK
R.lathe(px, py, [(0.10, pz - 0.06), (0.10, pz + 0.10), (0.06, pz + 0.13), (0.06, pz + 0.22),
                 (0.08, pz + 0.27), (0.045, pz + 0.33), (0.035, pz + 0.42), (0.05, pz + 0.47),
                 (0.012, pz + 0.80)], sides=8)

# --- B rear wing ----------------------------------------------------------------
for i, y in enumerate((13.0, 16.8)):
    window(B_NORTH, -y, 1.00, 0.80, 1.50, pick(BACKSIDE, "B_NORTH", 0, 1 - i), shut=0, full=False)
    window(B_NORTH, -y, 4.00, 0.80, 1.45, pick(BACKSIDE, "B_NORTH", 1, 1 - i), shut=0, full=False)
for i, x in enumerate((-2.60, -0.30)):
    window(B_REAR, -x, 1.00, 0.80, 1.50, pick(BACKSIDE, "B_REAR", 0, 1 - i), shut=0, full=False)
    window(B_REAR, -x, 4.00, 0.80, 1.45, pick(BACKSIDE, "B_REAR", 1, 1 - i), shut=0, full=False)
panel_door(B_NORTH, -15.0, 0.90, 0.0, 2.15, GR)
ST.box(BX0 - 0.35, BX0, 14.45, 15.55, SKIRT, 0.0)
plan_band([(BX1, AY1), (BX1, BY1), (BX0, BY1), (BX0, AY1)], 0.06, 5.80, 6.08, T, p_in=-0.20)
R.box(BX0 + 0.05, BX1 - 0.05, AY1, BY1 - 0.05, B_TOP - 0.05, B_TOP + 0.03)

# --- C (44-46) shop front -------------------------------------------------------
SF0, SF1 = CX0 + 0.25, CX1 - 0.25          # between the corner pilasters
SF_TOP = 2.95
KC.box(SF0, SF1, -0.25, 0.20, 0.0, SF_TOP)                                       # shop-front opening
for x0, x1 in ((CX0, SF0), (SF1, CX1)):                                          # corner pilasters (green)
    GR.box(x0, x1, -0.05, 0.02, 0.0, SF_TOP)
    GR.box(x0 + 0.05, x1 - 0.05, -0.065, -0.05, 0.25, SF_TOP - 0.15)              # raised panel
    T.box(x0 - 0.02, x1 + 0.02, -0.08, 0.02, SF_TOP - 0.12, SF_TOP)              # cap
DOORS_C = (2.40, 6.70)
DW = 0.90
DISP = (2.90, 6.20)
# display window: green bulkhead with a raised panel, sill rail, glass, head rail
GR.box(DISP[0], DISP[1], 0.06, 0.20, 0.0, 0.70)
GR.box(DISP[0] + 0.12, DISP[1] - 0.12, 0.045, 0.06, 0.14, 0.58)
T.box(DISP[0] - 0.02, DISP[1] + 0.02, 0.0, 0.20, 0.68, 0.74)
pane(C_FRONT, DISP[0], DISP[1], 0.74, 2.85, -0.12, "shop_a")         # the fruit shop behind the glass
T.box(DISP[0], DISP[1], 0.06, 0.20, 2.85, SF_TOP)
T.box((DISP[0] + DISP[1]) / 2 - 0.03, (DISP[0] + DISP[1]) / 2 + 0.03, 0.08, 0.12, 0.74, 2.85)   # mullion
# posts between the doors and the window, and beside the doors
for x0, x1 in ((SF0, DOORS_C[0] - DW / 2), (DOORS_C[0] + DW / 2, DISP[0]),
               (DISP[1], DOORS_C[1] - DW / 2), (DOORS_C[1] + DW / 2, SF1)):
    if x1 - x0 > 0.005:
        T.box(x0, x1, 0.0, 0.20, 0.0, SF_TOP)
# recessed doors (0.40): glazed leaf, transom, stone threshold
for xc in DOORS_C:
    x0, x1 = xc - DW / 2, xc + DW / 2
    KC.box(x0, x1, -0.25, 0.42, 0.0, SF_TOP)
    ST.box(x0, x1, -0.01, 0.42, SKIRT, 0.15)
    g0, g1 = x0 + 0.11, x1 - 0.11
    GR.box(x0, g0, 0.35, 0.40, 0.15, 2.45)                                       # leaf: stiles
    GR.box(g1, x1, 0.35, 0.40, 0.15, 2.45)
    GR.box(g0, g1, 0.35, 0.40, 0.15, 1.15)                                       # lower half, top rail
    GR.box(g0, g1, 0.35, 0.40, 2.33, 2.45)
    pane(C_FRONT, g0, g1, 1.15, 2.33, -0.357, "door_l" if xc < 4 else "door_r")
    GR.box(x0 + 0.14, x1 - 0.14, 0.335, 0.35, 0.37, 1.01)
    T.box(x0, x1, 0.34, 0.42, 2.45, 2.50)                                        # transom bar
    pane(C_FRONT, x0, x1, 2.50, SF_TOP, -0.37, "transom_door")
# sign band 2.95-3.40 (green fascia) with two lettered boards, shop cornice 3.40-3.55
GR.box(CX0, CX1, -0.03, 0.0, SF_TOP, 3.40)
for name, u0, u1 in (("shoes", 1.92, 4.37), ("fruits", 4.75, 7.20)):
    atlas_rec(region=name, mode="rect", wall=wall_rec(C_FRONT), u0=u0, u1=u1, z0=2.99, z1=3.37)
    AT.box(u0, u1, -0.05, -0.03, 2.99, 3.37)
AT.rid = 0
T.prism([(0.0, 3.40), (-0.06, 3.40), (-0.10, 3.45), (-0.14, 3.50), (-0.14, 3.55), (0.0, 3.55)],
        CX0 - 0.02, CX1 + 0.02, axis="x")
# corner boards above the shop front, and on the passage side
for x0 in (CX0, CX1 - 0.15):
    T.box(x0, x0 + 0.15, -0.03, 0.0, 3.55, 5.40)
T.wbox(C_SOUTH, 0.0, 0.15, 0.0, 5.40, -0.01, 0.03)
T.wbox(C_SOUTH, CY1 - 0.15, CY1, 0.0, 5.60, -0.01, 0.03)

# striped awning X 1.85 ... 7.30: roller at 2.95, out to y -1.60 at 2.35, valance 0.20
AW0, AW1 = 1.85, 7.30
AWY, AWZ0, AWZ1 = -1.60, 2.95, 2.35
VAL_BOT = AWZ1 - 0.20
AW_D = 0.06
atlas_rec(region="stripes", mode="slope", wall=wall_rec(C_FRONT), u0=AW0, u1=AW1, d0=AW_D, d1=-AWY)
AT.prism([(-AW_D, AWZ0), (AWY, AWZ1), (AWY, AWZ1 - 0.02), (-AW_D, AWZ0 - 0.02)], AW0, AW1, axis="x")
NS = 16
pitch = (AW1 - AW0) / NS
val = [(AW1, AWZ1), (AW0, AWZ1)]
for k in range(NS):
    x0 = AW0 + k * pitch
    val += [(x0, VAL_BOT + 0.06), (x0 + 0.2 * pitch, VAL_BOT + 0.02), (x0 + 0.5 * pitch, VAL_BOT),
            (x0 + 0.8 * pitch, VAL_BOT + 0.02)]
val += [(AW1, VAL_BOT + 0.06)]
atlas_rec(region="val", mode="rect", wall=wall_rec(C_FRONT), u0=AW0, u1=AW1, z0=VAL_BOT, z1=AWZ1, back="canvas")
AT.prism(val, AWY - 0.01, AWY, axis="y")
for x in (AW0, AW1):                                                             # side cheeks
    atlas_rec(region="stripes", mode="side", wall=wall_rec(C_FRONT), d0=AW_D, d1=-AWY, z0=AWZ1 - 0.02, z1=AWZ0)
    AT.prism([(-AW_D, AWZ0 - 0.02), (AWY, AWZ1 - 0.02), (-AW_D, AWZ1 - 0.02)], x - 0.005, x + 0.005, axis="x")
AT.rid = 0
IR.box(AW0, AW1, AWY + 0.005, AWY + 0.03, AWZ1 - 0.05, AWZ1 - 0.02)              # front bar
IR.box(AW0, AW1, -0.10, -0.03, AWZ0 - 0.03, AWZ0 + 0.05)                          # roller box
for x in (AW0 + 0.10, AW1 - 0.10):                                               # iron arms
    IR.prism([(-0.03, 1.95), (-0.03, 1.99), (AWY + 0.03, AWZ1 - 0.02), (AWY + 0.03, AWZ1 - 0.06)],
             x - 0.012, x + 0.012, axis="x")

# --- C upper floor, cornice, roof -------------------------------------------------
for x in (3.25, 5.85):
    window(C_FRONT, x, 3.80, 0.80, 1.45, pick(ROOMS, "C_FRONT", 0, 0 if x < 4 else 1))
C_LINE = [(CX0, 0.45), (CX0, 0.0), (CX1, 0.0), (CX1, 0.45)]
for p, z0, z1 in ((0.035, 5.40, 5.80), (0.10, 5.80, 5.86), (0.40, 5.86, 6.02), (0.45, 6.02, 6.10)):
    plan_band(C_LINE, p, z0, z1, T, p_in=-0.30)
BRACKET_C = [(0.0, 5.86), (0.36, 5.86), (0.36, 5.81), (0.28, 5.75), (0.19, 5.70), (0.12, 5.60),
             (0.08, 5.49), (0.06, 5.40), (0.0, 5.40)]
for x in (1.79, 3.60, 5.52, 7.33):
    T.oprism(C_FRONT, BRACKET_C, x - 0.06, x + 0.06)
# shed roof falling to the rear (tin), sloping fascia board along the passage side
slope = (C_TOP_F - C_TOP_R) / CY1
R.prism([(0.0, C_TOP_F - 0.02), (CY1 + 0.12, C_TOP_R - 0.12 * slope - 0.02),
         (CY1 + 0.12, C_TOP_R - 0.12 * slope + 0.03), (0.0, C_TOP_F + 0.03)], CX0, CX1 + 0.06, axis="x")
T.wprism(C_SOUTH, [(0.45, C_TOP_F - 0.45 * slope - 0.22), (CY1, C_TOP_R - 0.22),
                   (CY1, C_TOP_R + 0.01), (0.45, C_TOP_F - 0.45 * slope + 0.01)], -0.01, 0.04)

# --- C passage (south) wall: ground windows, side door, 2nd-floor box bays ---------
for i, y in enumerate((3.0, 9.5, 12.5)):
    window(C_SOUTH, y, 1.00, 0.80, 1.50, pick(BACKSIDE, "C_SOUTH", 0, (0, 2, 4)[i]), shut=0, full=False)
panel_door(C_SOUTH, 11.0, 0.90, 0.0, 2.20, GR)
ST.box(CX1, CX1 + 0.35, 10.45, 11.55, SKIRT, 0.0)
window(C_SOUTH, 11.0, 3.90, 0.75, 1.40, pick(ROOMS, "C_SOUTH", 1, 3), shut=0, full=False)
BAY_WIN = ((5.85, 7.12), (14.95, 16.55))
BRACKET_BAY = [(0.0, 3.45), (0.58, 3.45), (0.50, 3.38), (0.30, 3.25), (0.12, 3.10), (0.0, 3.05)]
for (y0, y1, sh, cut), wins in zip(BAYS, BAY_WIN):
    face = Wall((CX1 + BAY_OUT, 0.0), (1, 0), cut)
    for y in wins:
        colm = {5.85: 1, 7.12: 2, 14.95: 5, 16.55: 6}[y]
        window(face, y, 3.90, 0.75, 1.40, pick(ROOMS, "C_SOUTH", 1, colm), shut=0, full=False)
    T.box(CX1, CX1 + BAY_OUT + 0.04, y0 - 0.04, y1 + 0.04, 3.45, BAY_Z0)         # floor apron
    T.box(CX1 + BAY_OUT, CX1 + BAY_OUT + 0.03, y0, y1, 5.65, BAY_Z1)               # frieze board
    for y in (y0 + 0.25, (y0 + y1) / 2, y1 - 0.25):
        T.oprism(C_SOUTH, BRACKET_BAY, y - 0.05, y + 0.05)
    # hipped tin cap 5.85 -> 6.05
    xo, e = CX1 + BAY_OUT + 0.05, 0.05
    R.solid([(CX1, y0 - e, BAY_Z1), (xo, y0 - e, BAY_Z1), (xo, y1 + e, BAY_Z1), (CX1, y1 + e, BAY_Z1),
             (CX1, y0 + 0.25, 6.05), (CX1, y1 - 0.25, 6.05)],
            [(3, 2, 1, 0), (1, 2, 5, 4), (0, 1, 4), (2, 3, 5), (3, 0, 4, 5)])

# --- C rear wall above C2, C2 rear part ---------------------------------------------
window(C_REAR, -4.50, 3.90, 0.75, 1.20, pick(BACKSIDE, "C_REAR", 1, 0), shut=0, full=False)
window(C2_REAR, -3.60, 1.00, 0.80, 1.40, pick(BACKSIDE, "C_REAR", 0, 0), shut=0, full=False)
c2_plan = [(CX0 - 0.05, CY1), (CX1 + 0.08, CY1), (C2_SX + 0.06, C2_Y1 + 0.08), (CX0 - 0.05, C2_Y1 + 0.08)]
R.prism(c2_plan, C2_TOP - 0.03, C2_TOP + 0.05, axis="z")
T.prism(c2_plan, C2_TOP - 0.15, C2_TOP - 0.03, axis="z")                         # fascia

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
    cut_shell(shell, cutter, "BK_" + name, mat)
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("BK_" + key, MATS[BUILDER_MAT[key]], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Block 40-46 built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)",
      "| atlas records", len(ATLAS), "| window backs", len(BACKREC))
# Materials, baked lighting and GLB export: run block_40_46_bake.py (it runs this file first).
