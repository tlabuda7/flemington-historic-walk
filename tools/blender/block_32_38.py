"""
block_32_38.py - builds the frame row at 32-38 Main St, Flemington (east side, directly north of
the block at 40-46), as it stood in Sept 1921: three small 2-storey frame shops behind one
continuous 1-storey open porch. North to south (1921 Sanborn sheet 2): millinery ("Mill'y"),
"Bakery", "Meats"; the south strip and the long back building of Meats are 1 storey.
  A  Mill'y: 2 storeys, long rear part, open rear porch (F1, shingle roof)
  B  Bakery: 2 storeys, 1-storey back addition (F2)
  C  Meats 2-storey block; D Meats 1-storey L (south strip + rear building)
  E  the continuous open porch: plain deck, 6 plain square posts, fascia, shed tin roof
  G  a plain buff clapboard patch over 40-42's north wall above D's roof (40-42's faces there
     were deleted from block-40-46.glb because the old placeholder covered them)

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/block_32_38.py").read())

Every run deletes and rebuilds the "Block3238" collection. Materials, lightmap bake and GLB
export: block_32_38_bake.py (runs this file first). Pattern: block_40_46.py (builders per
material, Wall frames, closed wall shells with shallow boolean recesses, section-E windows).

Sources: PLAN.md "Block at 32-38 Main St" spec (1921 Sanborn footprints and storeys). No photo
shows these fronts (building demolished mid-1900s); the owner approved a plain guessed front
on 2026-11-10: no signs, lettering, awnings, shutters, brackets or chimneys.

Coordinates (metres, Blender Z-up), origin = scene (8.54, 0.15, -130.755), rotation 0 -90 0:
    X  along the street, +X = south (40-42), -X = north (3.4 m gap to 24-30)
    Y  depth: y = 0 is the porch front; front wall at 1.63
    Z  up from the sidewalk top; walls skirt down to -0.20; yards at -0.15
Scene <- local: x = 8.54 + Y, z = -130.755 + X.
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".
"""

import json
import math
import random
import bpy
import bmesh

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md massing table; every height is a guess, the map writes none)
# ---------------------------------------------------------------------------
HW = 6.705                      # half length along the street (13.41 m)
FW = 1.63                       # front wall (porch depth)
P1, P2 = -2.57, 1.94            # partitions Mill'y | Bakery | Meats
C_X1 = 5.14                     # Meats 2-storey block south wall
TOP_F = 6.10                    # 2-storey fronts
A_Y1, A_TOP_R = 22.12, 5.50     # Mill'y rear wall, roof height there
B_Y1, B_TOP_R = 16.70, 5.60
C_Y1, C_TOP_R = 7.89, 5.90
D_Y1, D_TOP_F, D_TOP_R = 25.06, 3.80, 3.60
F1_Y1 = 23.42                   # Mill'y rear porch
F2_X0, F2_Y1, F2_TOP_F, F2_TOP_R = 0.04, 20.63, 3.00, 2.85
PORCH_X1 = 6.55                 # porch south end
SKIRT = -0.20
DECK = 0.15
RECESS = 0.25


def d_top(y):
    """D's roof line (nearly flat, 3.80 at the front wall to 3.60 at the rear)."""
    return D_TOP_F + (D_TOP_R - D_TOP_F) * (y - FW) / (D_Y1 - FW)


# ---------------------------------------------------------------------------
# Materials (plain stand-ins; block_32_38_bake.py swaps in the textures)
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


COLOURS = {"Clap": "#D8CFB8", "ClapA": "#B9AE96", "Trim": "#DDD5C2", "Roof": "#5A3D34",
           "Wood": "#2E2E26", "Deck": "#8E8C86", "Glass": "#1A1916", "WBack": "#2A2420", "Shop": "#2A2420"}
MATS = {k: plain("RW_" + k, c) for k, c in COLOURS.items()}
# builder -> material (the bake gives every builder its own UVs and tint)
BUILDER_MAT = {"Clap": "Clap", "ClapA": "ClapA", "Trim": "Trim", "Roof": "Roof", "Shingle": "Roof",
               "Wood": "Wood", "Deck": "Deck", "Glass": "Glass", "WBack": "WBack", "Shop": "Shop"}

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


col = fresh_collection("Block3238")
G = {k: MB() for k in BUILDER_MAT}
CL, CA, T, R, SG, W, DK, GL, WB, SH = (G[k] for k in ("Clap", "ClapA", "Trim", "Roof", "Shingle", "Wood",
                                                      "Deck", "Glass", "WBack", "Shop"))
# wall shells (closed solids) and their cutters: name -> (shell, cutter, material)
SHELLS = {k: (MB(), MB(), "Clap") for k in ("ShellA", "ShellB", "ShellC", "ShellD1", "ShellD2", "ShellF2")}
SA, SB, SC, SD1, SD2, SF2 = (SHELLS[k][0] for k in SHELLS)
KA, KB, KC, KD1, KD2, KF2 = (SHELLS[k][1] for k in SHELLS)

# ---------------------------------------------------------------------------
# Window backs (section E): cells of the shared atlases, picked so that no two windows side
# by side show the same cell. BACKREC[rid] -> UV record (read by the bake).
# ---------------------------------------------------------------------------
WB_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\window_backs.json"))["cells"]
SHOP_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\shop_interior.json"))["cells"]
GAP = 0.04                      # window back this far behind the glass
# rooms over small shops: living rooms and the milliner's / baker's workrooms
UPPER = {"lace": 2, "lace_blind_cream": 2, "lace_blind_green": 1, "curtains_beige": 2, "curtains_olive": 1,
         "blind_cream_half": 2, "blind_cream_high": 1, "blind_green_half": 1, "dark_room_frame": 1}
_wb_rng = random.Random(3238)
_wb_grid = {}
BACKREC = {}


def pick(weights, wall, row, colm):
    g = _wb_grid.setdefault(wall, {})
    avoid = {g.get((row, colm - 1)), g.get((row, colm + 1)), g.get((row - 1, colm)), g.get((row + 1, colm))}
    names = [n for n in weights if n not in avoid]
    cell = _wb_rng.choices(names, weights=[weights[n] for n in names])[0]
    g[(row, colm)] = cell
    return cell


def back(wall, u0, u1, z0, z1, d, cell, shop=False):
    """Window back: one face on the wall plane at depth d (negative = into the wall).
    shop=True takes the cell from shared/shop_interior.jpg, else from window_backs.jpg."""
    mb = SH if shop else WB
    rid = len(BACKREC) + 1
    BACKREC[rid] = dict(wall=(wall.p0, wall.n), u0=u0, u1=u1, z0=z0, z1=z1,
                        uv=(SHOP_CELLS if shop else WB_CELLS)[cell]["uv"])
    mb.rid = rid
    mb.quad(wall, u0, u1, z0, z1, d)
    mb.rid = 0


def pane(wall, u0, u1, z0, z1, d_glass, cell, shop=False):
    """Glass face at depth d_glass with its window back GAP behind it."""
    back(wall, u0, u1, z0, z1, d_glass - GAP, cell, shop)
    GL.quad(wall, u0, u1, z0, z1, d_glass)


# Walls (u: FRONT +x, SOUTH +y, NORTH -y, REAR -x)
FRONT = {k: Wall((0.0, FW), (0, -1), cut) for k, cut in (("A", KA), ("B", KB), ("C", KC), ("D", KD1))}
A_NORTH = Wall((-HW, 0.0), (-1, 0), KA)
A_REAR = Wall((0.0, A_Y1), (0, 1), KA)
D_REAR = Wall((0.0, D_Y1), (0, 1), KD2)

# ---------------------------------------------------------------------------
# Shells: shed tops falling to the rear (outline in Y-Z, extruded along X)
# ---------------------------------------------------------------------------


def shed_shell(sh, x0, x1, y0, y1, z_f, z_r):
    sh.prism([(y0, SKIRT), (y1, SKIRT), (y1, z_r), (y0, z_f)], x0, x1, axis="x")


shed_shell(SA, -HW, P1, FW, A_Y1, TOP_F, A_TOP_R)
shed_shell(SB, P1, P2, FW, B_Y1, TOP_F, B_TOP_R)
shed_shell(SC, P2, C_X1, FW, C_Y1, TOP_F, C_TOP_R)
shed_shell(SD1, C_X1, HW, FW, C_Y1, D_TOP_F, d_top(C_Y1))
shed_shell(SD2, P2, HW, C_Y1, D_Y1, d_top(C_Y1), D_TOP_R)
shed_shell(SF2, F2_X0, P2, B_Y1, F2_Y1, F2_TOP_F, F2_TOP_R)

# ---------------------------------------------------------------------------
# Openings
# ---------------------------------------------------------------------------


def window(wall, cu, z0, w, h, cell):
    """1/1 sash window in a 0.25 recess: one glass face 4 cm in front of a window back
    (section E), sash rails, plain pale casing 0.10 and a plain sill. No shutters, no cap."""
    hw = w / 2
    z1 = z0 + h
    wall.cut.wbox(wall, cu - hw, cu + hw, z0, z1, -RECESS, 0.25)
    pane(wall, cu - hw, cu + hw, z0, z1, -0.17, cell)
    zm = z0 + h / 2
    s = 0.05
    T.wbox(wall, cu - hw, cu + hw, z1 - s, z1, -0.15, -0.09)                 # top rail
    T.wbox(wall, cu - hw, cu + hw, z0, z0 + 0.07, -0.15, -0.09)              # bottom rail
    for a in (cu - hw, cu + hw - s):
        T.wbox(wall, a, a + s, z0 + 0.07, z1 - s, -0.15, -0.09)              # stiles
    T.wbox(wall, cu - hw, cu + hw, zm - 0.03, zm + 0.03, -0.15, -0.10)       # meeting rail
    c = 0.10
    T.wbox(wall, cu - hw - c, cu - hw, z0, z1 + c, -0.02, 0.03)              # casing
    T.wbox(wall, cu + hw, cu + hw + c, z0, z1 + c, -0.02, 0.03)
    T.wbox(wall, cu - hw, cu + hw, z1, z1 + c, -0.02, 0.03)
    T.wbox(wall, cu - hw - c - 0.03, cu + hw + c + 0.03, z0 - 0.05, z0, -0.16, 0.06)   # sill


def shop_window(wall, x0, x1, cell, shop):
    """Shop window in the wall plane: dark wood bulkhead with a raised panel (0.15-0.75),
    sill rail, stiles, head rail, centre mullion, one glass face per light over the shop
    interior (0.80-2.75), dark wood casing on the wall."""
    wall.cut.wbox(wall, x0, x1, DECK, 2.85, -RECESS, 0.25)
    W.wbox(wall, x0, x1, DECK, 0.75, -0.14, 0.0)                              # bulkhead
    W.wbox(wall, x0 + 0.10, x1 - 0.10, 0.25, 0.65, 0.0, 0.015)                 # raised panel
    W.wbox(wall, x0, x1, 0.75, 0.80, -0.14, 0.04)                              # sill rail
    W.wbox(wall, x0, x0 + 0.08, 0.80, 2.75, -0.14, 0.0)                        # stiles
    W.wbox(wall, x1 - 0.08, x1, 0.80, 2.75, -0.14, 0.0)
    W.wbox(wall, x0, x1, 2.75, 2.85, -0.14, 0.0)                               # head rail
    xm = (x0 + x1) / 2
    W.wbox(wall, xm - 0.03, xm + 0.03, 0.80, 2.75, -0.13, -0.05)               # mullion
    pane(wall, x0 + 0.08, x1 - 0.08, 0.80, 2.75, -0.10, cell, shop)
    W.wbox(wall, x0 - 0.10, x0, DECK, 2.95, -0.02, 0.03)                       # casing
    W.wbox(wall, x1, x1 + 0.10, DECK, 2.95, -0.02, 0.03)
    W.wbox(wall, x0, x1, 2.85, 2.95, -0.02, 0.03)


def door(wall, x0, x1, z0, head, glazed_cell=None, shop=False, case=W):
    """Door in a 0.25 recess: dark wood leaf (stiles and rails), glazed upper half (one glass
    face over a window back) or two raised panels; casing on the wall."""
    wall.cut.wbox(wall, x0, x1, z0, head, -RECESS, 0.25)
    d = -0.14
    g0, g1 = x0 + 0.11, x1 - 0.11
    top = head - 0.12
    W.wbox(wall, x0, g0, z0, head, d - 0.05, d)                                 # stiles
    W.wbox(wall, g1, x1, z0, head, d - 0.05, d)
    W.wbox(wall, g0, g1, top, head, d - 0.05, d)                                # top rail
    if glazed_cell:
        mid = 1.30
        W.wbox(wall, g0, g1, z0, mid, d - 0.05, d)                              # lower half
        W.wbox(wall, g0 + 0.03, g1 - 0.03, z0 + 0.22, mid - 0.14, d, d + 0.015)   # raised panel
        pane(wall, g0, g1, mid, top, d - 0.008, glazed_cell, shop)
    else:
        W.wbox(wall, g0, g1, z0, top, d - 0.05, d)
        for za, zb in ((z0 + 0.20, z0 + (head - z0) * 0.42), (z0 + (head - z0) * 0.50, top - 0.08)):
            W.wbox(wall, g0 + 0.03, g1 - 0.03, za, zb, d, d + 0.015)
    case.wbox(wall, x0 - 0.10, x0, z0, head + 0.10, -0.02, 0.03)               # casing
    case.wbox(wall, x1, x1 + 0.10, z0, head + 0.10, -0.02, 0.03)
    case.wbox(wall, x0, x1, head, head + 0.10, -0.02, 0.03)


# --- shop fronts (all guesses, plain): Mill'y, Bakery, Meats ---------------------------------
SHOPS = (("A", (-6.30, -4.00), (-3.70, -2.80), ("shop_a", True), ("door_l", True)),
         ("B", (-2.20, 0.45), (0.75, 1.65), ("shop_b", True), ("door_r", True)),
         ("C", (2.30, 4.00), (4.20, 5.10), ("shop_b", False), ("door", False)))
for key, (wx0, wx1), (dx0, dx1), (wcell, wshop), (dcell, dshop) in SHOPS:
    shop_window(FRONT[key], wx0, wx1, wcell, wshop)
    door(FRONT[key], dx0, dx1, DECK, 2.60, dcell, dshop)
    DK.box(dx0, dx1, FW - 0.02, FW + 0.12, 0.10, DECK + 0.01)                  # threshold

# --- upper floor: six 1/1 windows, plain pale frames -----------------------------------------
UP_X = (-5.67, -3.61, -1.44, 0.81, 2.79, 4.29)
for i, x in enumerate(UP_X):
    key = "A" if x < P1 else ("B" if x < P2 else "C")
    window(FRONT[key], x, 3.90, 0.80, 1.45, pick(UPPER, "FRONT", 0, i))

# --- boxed eave across the 2-storey fronts, corner and partition boards -------------------------
T.box(-HW, C_X1, FW - 0.30, FW + 0.02, 5.90, TOP_F)                             # boxed eave
T.box(-HW, C_X1, FW - 0.32, FW - 0.30, 5.88, TOP_F)                             # fascia lip
for x0, z0, z1 in ((-HW, DECK, 5.90), (C_X1 - 0.15, D_TOP_F, 5.90)):
    T.box(x0, x0 + 0.15, FW - 0.03, FW, z0, z1)                                 # corner boards
for xc, z0, z1 in ((P1, DECK, 5.90), (P2, DECK, 5.90), (C_X1, 2.80, D_TOP_F - 0.18)):
    T.box(xc - 0.05, xc + 0.05, FW - 0.025, FW, z0, z1)
T.box(HW - 0.15, HW, FW - 0.03, FW, DECK, D_TOP_F - 0.18)                       # D's south corner
T.wbox(A_NORTH, -FW - 0.15, -FW, DECK, 5.90, -0.01, 0.03)                        # north wall corners
T.wbox(A_NORTH, -A_Y1, -A_Y1 + 0.15, -0.05, A_TOP_R - 0.20, -0.01, 0.03)
# D strip: plain fascia board under its eave at the front
T.box(C_X1, HW + 0.04, FW - 0.04, FW, D_TOP_F - 0.18, D_TOP_F)

# --- roofs: shed tin, overhang 0.12 at the rear; sloping fascia on the exposed sides ---------------


def shed_roof(mb, x0, x1, ya, za, yb, zb, y0, y1, th=0.05):
    """Roof slab th thick on the line through (ya, za) and (yb, zb), from y0 to y1; its top
    stands 0.03 above the shell top."""
    s = (zb - za) / (yb - ya)
    z = lambda y: za + s * (y - ya)
    mb.prism([(y0, z(y0) - 0.02), (y1, z(y1) - 0.02), (y1, z(y1) + th - 0.02), (y0, z(y0) + th - 0.02)],
             x0, x1, axis="x")


EV = FW - 0.32                                       # front edge of the boxed eave
shed_roof(R, -HW - 0.06, P1, FW, TOP_F, A_Y1, A_TOP_R, EV, A_Y1 + 0.12)
shed_roof(R, P1, P2, FW, TOP_F, B_Y1, B_TOP_R, EV, B_Y1 + 0.12)
shed_roof(R, P2, C_X1 + 0.06, FW, TOP_F, C_Y1, C_TOP_R, EV, C_Y1 + 0.06)
shed_roof(R, C_X1, HW + 0.04, FW, D_TOP_F, D_Y1, D_TOP_R, FW - 0.10, C_Y1)      # D strip
shed_roof(R, P2, HW + 0.04, FW, D_TOP_F, D_Y1, D_TOP_R, C_Y1, D_Y1 + 0.12)      # D rear building
shed_roof(R, F2_X0 - 0.06, P2, B_Y1, F2_TOP_F, F2_Y1, F2_TOP_R, B_Y1, F2_Y1 + 0.12)
# rake boards along A's north wall and C's south wall (above D)
T.wprism(A_NORTH, [(-A_Y1, A_TOP_R - 0.20), (-FW, TOP_F - 0.20), (-FW, TOP_F - 0.01), (-A_Y1, A_TOP_R - 0.01)],
         -0.01, 0.04)
C_SOUTH = Wall((C_X1, 0.0), (1, 0), KC)
T.wprism(C_SOUTH, [(FW, TOP_F - 0.20), (C_Y1, C_TOP_R - 0.20), (C_Y1, C_TOP_R - 0.01), (FW, TOP_F - 0.01)],
         -0.01, 0.04)

# --- porch: plain deck, 6 plain square posts, fascia, shed tin roof (3.45 at the wall, 3.20 at Y 0) ---
DK.box(-HW, PORCH_X1, 0.0, FW, SKIRT, DECK)
POSTS = (-6.60, -3.99, -1.38, 1.23, 3.84, 6.45)
PY = 0.17                                            # post centre: front face on Y 0.10
for x in POSTS:
    T.box(x - 0.07, x + 0.07, PY - 0.07, PY + 0.07, DECK, 2.95)
T.box(-HW, PORCH_X1, 0.08, 0.26, 2.95, 3.15)                                     # front fascia / beam
P_S = 0.25 / FW                                                                  # roof slope
P_TOP = lambda y: 3.20 + P_S * y                                                 # roof top surface
for x0, x1 in ((-HW, -HW + 0.06), (PORCH_X1 - 0.06, PORCH_X1)):                  # end fascias
    T.prism([(0.08, 2.95), (FW, 2.95), (FW, P_TOP(FW) - 0.05), (0.08, P_TOP(0.08) - 0.05)], x0, x1, axis="x")
T.box(-HW + 0.06, PORCH_X1 - 0.06, 0.26, FW, 3.13, 3.15)                         # ceiling boards
R.prism([(-0.10, P_TOP(-0.10) - 0.05), (FW + 0.02, P_TOP(FW + 0.02) - 0.05),
         (FW + 0.02, P_TOP(FW + 0.02)), (-0.10, P_TOP(-0.10))], -HW - 0.10, PORCH_X1 + 0.10, axis="x")

# --- back: Mill'y rear porch (F1), rear doors -----------------------------------------------------
DK.box(-HW, P1, A_Y1, F1_Y1, SKIRT, 0.05)                                        # porch floor
for x in (-HW + 0.10, (-HW + P1) / 2, P1 - 0.10):
    T.box(x - 0.06, x + 0.06, F1_Y1 - 0.16, F1_Y1 - 0.04, 0.05, 2.55)
T.box(-HW, P1, F1_Y1 - 0.18, F1_Y1 - 0.02, 2.40, 2.55)                           # beam
f1_s = (2.60 - 2.90) / (F1_Y1 - A_Y1)
SG.prism([(A_Y1 - 0.02, 2.88), (F1_Y1 + 0.15, 2.60 + f1_s * 0.15),
          (F1_Y1 + 0.15, 2.66 + f1_s * 0.15), (A_Y1 - 0.02, 2.94)], -HW - 0.08, P1 + 0.08, axis="x")
door(A_REAR, 5.50 - 0.45, 5.50 + 0.45, 0.05, 2.15, case=T)                      # onto the rear porch
door(D_REAR, -4.30 - 0.45, -4.30 + 0.45, -0.15, 2.05, case=T)
DK.box(3.80, 4.80, D_Y1 - 0.02, D_Y1 + 0.30, SKIRT, -0.10)                       # step

# --- G: buff clapboard patch over 40-42's north wall above D's roof (repair, 40-42's material) ---
G_PATCH = Wall((HW, 0.0), (-1, 0))                   # faces north, u = -Y
CA.quad(G_PATCH, -11.26, -2.04, 3.60, 6.12, 0.0)

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
    cut_shell(shell, cutter, "RW_" + name, mat)
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("RW_" + key, MATS[BUILDER_MAT[key]], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Block 32-38 built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)",
      "| window backs", len(BACKREC))
# Materials, baked lighting and GLB export: run block_32_38_bake.py (it runs this file first).
