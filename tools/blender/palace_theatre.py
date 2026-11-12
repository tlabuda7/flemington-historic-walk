"""
palace_theatre.py - builds the Palace Theatre, 31 Main St, Flemington (west side, old no. 518),
as on the 1921 Sanborn map and the card "Palace Theatre & Potter Building, Flemington, N.J.":
  A  2-storey brick front block: shop window, shop door and the theatre entrance (dark lobby)
     on the ground floor, a projecting belt course, four paired 1/1 windows with dark
     segmental soldier-course hoods and pale keystones, a stepped low gable parapet with a
     BLANK pale panel (owner, 2026-11-08: no lettering), three opal globe lamps
  B  1-storey (+ basement) hollow-tile auditorium, low gable roof (height guessed)
  C  stage house, flat roof at 7.92 m (map 26')

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/palace_theatre.py").read())

Every run deletes and rebuilds the "PalaceTheatre" collection. Materials, lightmap bake and GLB
export: palace_theatre_bake.py (runs this file first). Pattern: block_40_46.py / union_hotel.py
(builders per material, closed wall shells with shallow boolean recesses).

Windows (PLAN.md section E, 2026-11-12): every pane is ONE outward glass face (builder Glass ->
material `glass`, transparent in the scene) with a window back 4 cm behind it: upstairs a cell of
assets/textures/shared/window_backs.jpg (dim rooms and blinds, never the same cell beside or
above / below itself), the shop window and shop-door lights the shared shop interior
(shared/shop_interior.jpg), the lobby-door lights and transom the dim hotel-lobby rooms
(shared/hotel_lobby.jpg). Sashes, frames, sills, poster frames and the ticket window (still the
plain dark glass) are unchanged. The door leaves are now open frames round their lights.

Sources: PLAN.md "Palace Theatre (31 Main St, old no. 518)" spec (1921 Sanborn sheet 2
footprints and heights; facade from the card by perspective fit, +-0.3 m).

Coordinates (metres, Blender Z-up), origin = scene (-10.30, 0.15, -145.52), rotation 0 90 0:
    X  along the street, +X = north (no. 27), -X = south (alley, no. 35)
    Y  depth: y = 0 is the front wall (property line); rear wall of C at 62.78
    Z  up from the sidewalk top; walls skirt down to -0.20; alley and yard at -0.15
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".
"""

import json
import math
import random
import bpy
import bmesh

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md massing table)
# ---------------------------------------------------------------------------
AX0, AX1 = -6.30, 6.30          # A front block along X (12.60)
AY1 = 22.82                     # A rear wall
A_SIDE = 7.40                   # A side walls / roof deck
PAR_T = 0.40                    # front wall (parapet) thickness
SHOULDER, STEP_X, STEP_UP, APEX = 7.92, 3.95, 0.25, 8.65
BX0, BX1 = -6.30, 7.40          # B and C along X (1.10 wider on the north side)
BY1 = 50.95                     # B rear = C front
CY1 = 62.78                     # C rear wall
B_EAVE, B_RIDGE, B_RIDGE_X = 6.40, 7.70, (BX0 + BX1) / 2
C_TOP = 7.92
SKIRT = -0.20
ALLEY = -0.15
RECESS = 0.25
GF_HEAD = 4.05                  # ground-floor opening heads
BAND0 = 2.85                    # pale panelled band 2.85 ... 4.05 over every opening
BELT0, BELT1, BELT_OUT = 4.25, 4.80, 0.15
WIN_X = (-4.50, -1.50, 1.50, 4.50)
WIN_Z0, WIN_Z1, WIN_W = 4.95, 7.05, 2.00
LAMP_X = (-5.54, 0.45, 2.88)
SHOP = (-5.74, -0.60)
SHOP_DOOR = (0.00, 1.70)
ENTR = (2.55, 5.45)
LOBBY_D = 1.00

# ---------------------------------------------------------------------------
# Materials (plain stand-ins; palace_theatre_bake.py swaps in the textures)
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


COLOURS = {"Brick": "#7A4436", "Stucco": "#A79F8B", "Trim": "#DDD5C2", "Stone": "#CDBFA2",
           "Roof": "#5A3D34", "Doors": "#22302A", "Dark": "#1E2226", "Signs": "#D8CDB4",
           "WBack": "#3A3632", "Shop": "#3A3632", "HLobby": "#3A3632", "Glass": "#1A1916"}
MATS = {k: plain("PT_" + k, c) for k, c in COLOURS.items()}
# builder -> material (the bake gives every builder its own UVs and tint)
BUILDER_MAT = {"Brick": "Brick", "Hood": "Brick", "Stucco": "Stucco", "Trim": "Trim", "Globe": "Trim",
               "Stone": "Stone", "Roof": "Roof", "Doors": "Doors", "FireDoor": "Doors",
               "Glass": "Glass", "Ticket": "Dark", "Iron": "Dark", "Lobby": "Dark", "Atlas": "Signs",
               "WBack": "WBack", "Shop": "Shop", "HLobby": "HLobby"}

# ---------------------------------------------------------------------------
# Mesh builder (as block_40_46.py)
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

    def face(self, wall, pts, d):
        """ONE single-sided face (outline [(u, z), ...] on a wall plane, d out from the wall
        face), facing outward. Used for glass panes and window backs."""
        f = self.bm.faces.new([self.bm.verts.new(wall.pt(u, z, d)) for u, z in pts])
        f.normal_update()
        if f.normal.x * wall.n[0] + f.normal.y * wall.n[1] < 0:
            f.normal_flip()
        f[self.rid_layer] = self.rid
        return f

    def wprism(self, wall, pts, d0, d1):
        self._extrude([wall.pt(u, z, d0) for u, z in pts], [wall.pt(u, z, d1) for u, z in pts])

    def wbox(self, wall, u0, u1, z0, z1, d0, d1):
        self.wprism(wall, rect(u0, u1, z0, z1), d0, d1)

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

    def tube(self, p0, p1, r, sides=8):
        """Round bar between two points (pipes, lamp rods)."""
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
        """Closed solid from explicit vertices and faces (index lists)."""
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


def arc_pts(cu, zc, r, a0, a1, segs):
    return [(cu + r * math.cos(a0 + (a1 - a0) * i / segs), zc + r * math.sin(a0 + (a1 - a0) * i / segs))
            for i in range(segs + 1)]


def offset_line(poly, p):
    """Open polyline (x, y) with the outside on the right; offset outward by p (mitred)."""
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


col = fresh_collection("PalaceTheatre")
G = {k: MB() for k in BUILDER_MAT}
BR, HD, SU, T, GB, ST, R, DR, FD, GL, IR, LB, AT, TK, WB, SH, HL = (
    G[k] for k in ("Brick", "Hood", "Stucco", "Trim", "Globe", "Stone", "Roof", "Doors", "FireDoor",
                   "Glass", "Iron", "Lobby", "Atlas", "Ticket", "WBack", "Shop", "HLobby"))
# wall shells (closed solids) and their cutters: name -> (shell, cutter, material)
SHELLS = {k: (MB(), MB(), m) for k, m in (("ShellA", "Brick"), ("ShellB", "Stucco"), ("ShellC", "Stucco"))}
SA, SB, SC = (SHELLS[k][0] for k in SHELLS)
KA, KB, KC = (SHELLS[k][1] for k in SHELLS)

ATLAS = {}                      # rid -> record (read by palace_theatre_bake.py)


def atlas_rec(**kw):
    rid = len(ATLAS) + 1
    ATLAS[rid] = kw
    AT.rid = rid
    return rid


def wall_rec(w):
    return (w.p0, w.n)


FRONT = Wall((0.0, 0.0), (0, -1), KA)          # u = X (north to the right)
SOUTH_A = Wall((AX0, 0.0), (-1, 0), KA)        # u = -Y
SOUTH_B = Wall((BX0, 0.0), (-1, 0), KB)
REAR_C = Wall((0.0, CY1), (0, 1), KC)          # u = -X

# ---------------------------------------------------------------------------
# Glass panes and window backs (PLAN.md section E)
# ---------------------------------------------------------------------------
PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
CELLS = {}                      # cell name -> (builder, uv) over the three shared atlases
for _f, _mb in (("shop_interior", "Shop"), ("hotel_lobby", "HLobby"), ("window_backs", "WBack")):
    for _k, _v in json.load(open(PROJECT + r"\assets\textures\shared\%s.json" % _f))["cells"].items():
        CELLS.setdefault(_k, (_mb, _v["uv"]))
GAP = 0.04                      # window back this far behind the glass
# theatre upper floor (offices, store rooms over the lobby): dim rooms and blinds
UPPER = {"dark_room": 3, "dark_room_frame": 3, "blind_cream_high": 2, "blind_cream_half": 2,
         "blind_cream_low": 1, "blind_green_high": 2, "blind_green_half": 2, "blind_green_low": 1}
_wb_rng = random.Random(1918)
_wb_grid = {}
BACKREC = {}                    # rid -> record (read by palace_theatre_bake.py)


def pick(weights, row, colm):
    """A cell for the window at (row, column) of the front that differs from its neighbours."""
    avoid = {_wb_grid.get((row, colm - 1)), _wb_grid.get((row, colm + 1)),
             _wb_grid.get((row - 1, colm)), _wb_grid.get((row + 1, colm))}
    names = [n for n in weights if n not in avoid]
    cell = _wb_rng.choices(names, weights=[weights[n] for n in names])[0]
    _wb_grid[(row, colm)] = cell
    return cell


def pane(wall, u0, u1, z0, z1, d_glass, cell, grow=0.03, crop=None, gap=GAP):
    """Glass face (u0..u1 x z0..z1) at depth d_glass (negative = into the wall) and its window
    back `gap` behind it, `grow` larger all round where frames hide its edge; crop = (fu0, fu1,
    fv0, fv1) part of the atlas cell (v up)."""
    GL.face(wall, rect(u0, u1, z0, z1), d_glass)
    mb_key, (U0, V0, U1, V1) = CELLS[cell]
    if crop:
        U0, U1, V0, V1 = (U0 + (U1 - U0) * crop[0], U0 + (U1 - U0) * crop[1],
                          V0 + (V1 - V0) * crop[2], V0 + (V1 - V0) * crop[3])
    b = (u0 - grow, u1 + grow, z0 - grow, z1 + grow)
    rid = len(BACKREC) + 1
    BACKREC[rid] = dict(wall=(wall.p0, wall.n), u0=b[0], u1=b[1], z0=b[2], z1=b[3], uv=(U0, V0, U1, V1))
    mb = G[mb_key]
    mb.rid = rid
    mb.face(wall, rect(*b), d_glass - gap)
    mb.rid = 0

# ---------------------------------------------------------------------------
# Shells
# ---------------------------------------------------------------------------
# A: one closed solid - the front wall with its stepped gable parapet (0.40 thick) and the
# block behind it up to the side-wall top 7.40.
GABLE = [(AX0, SKIRT), (AX1, SKIRT), (AX1, SHOULDER), (STEP_X, SHOULDER), (STEP_X, SHOULDER + STEP_UP),
         (0.0, APEX), (-STEP_X, SHOULDER + STEP_UP), (-STEP_X, SHOULDER), (AX0, SHOULDER)]
cos = [(x, 0.0, z) for x, z in GABLE]                                   # 0..8 front
cos += [(x, PAR_T, z) for x, z in GABLE[2:]]                            # 9..15 parapet back
cos += [(AX1, PAR_T, A_SIDE), (AX0, PAR_T, A_SIDE)]                     # 16, 17
cos += [(AX0, AY1, SKIRT), (AX1, AY1, SKIRT), (AX1, AY1, A_SIDE), (AX0, AY1, A_SIDE)]   # 18..21
faces = [list(range(9)), [16, 9, 10, 11, 12, 13, 14, 15, 17]]
faces += [[i, i + 1, i + 8, i + 7] for i in range(2, 8)]                # parapet top (F_i, F_i+1, P_i+1, P_i)
faces += [[1, 19, 20, 16, 9, 2], [0, 8, 15, 17, 21, 18], [17, 16, 20, 21], [0, 18, 19, 1], [18, 21, 20, 19]]
SA.solid(cos, faces)
# B: gable prism along Y; C: box
SB.prism([(BX0, SKIRT), (BX1, SKIRT), (BX1, B_EAVE), (B_RIDGE_X, B_RIDGE), (BX0, B_EAVE)], AY1, BY1)
SC.box(BX0, BX1, BY1, CY1, SKIRT, C_TOP)

# ---------------------------------------------------------------------------
# Front, upper floor: four paired 1/1 windows, hoods, keystones, sills
# ---------------------------------------------------------------------------
HOOD_W, HOOD_Z0, HOOD_END, HOOD_TOP = 2.20, 7.05, 7.20, 7.35


def segment_top(cx, half, z_end, z_crown, segs=8):
    """Points of a shallow segmental curve from (cx+half, z_end) over the crown to (cx-half, z_end)."""
    s = z_crown - z_end
    r = (half * half + s * s) / (2 * s)
    zc = z_crown - r
    a = math.atan2(z_end - zc, half)
    return arc_pts(cx, zc, r, a, math.pi - a, segs)


def window_pair(cx, colm):
    hw = WIN_W / 2
    z0, z1 = WIN_Z0, WIN_Z1
    zm = (z0 + z1) / 2
    KA.box(cx - hw, cx + hw, -0.25, RECESS, z0, z1)                         # recess 0.25
    # one glass face per 1/1 window (1 cm behind the sashes), a window back behind each
    for k, (a, b) in enumerate(((cx - hw + 0.07, cx - 0.04), (cx + 0.04, cx + hw - 0.07))):
        pane(FRONT, a, b, z0 + 0.06, z1 - 0.07, -0.18, pick(UPPER, 1, 2 * colm + k))
    # frame: jambs, head, sill rail, centre mullion 0.08
    T.box(cx - hw, cx - hw + 0.07, 0.10, RECESS, z0, z1)
    T.box(cx + hw - 0.07, cx + hw, 0.10, RECESS, z0, z1)
    T.box(cx - hw, cx + hw, 0.10, RECESS, z1 - 0.07, z1)
    T.box(cx - hw, cx + hw, 0.08, RECESS, z0, z0 + 0.06)
    T.box(cx - 0.04, cx + 0.04, 0.10, RECESS, z0, z1)
    # two 1/1 sashes: stiles, top and bottom rails, meeting rail
    for a, b in ((cx - hw + 0.07, cx - 0.04), (cx + 0.04, cx + hw - 0.07)):
        T.box(a, a + 0.05, 0.13, 0.17, z0 + 0.06, z1 - 0.07)
        T.box(b - 0.05, b, 0.13, 0.17, z0 + 0.06, z1 - 0.07)
        T.box(a, b, 0.13, 0.17, z0 + 0.06, z0 + 0.15)
        T.box(a, b, 0.13, 0.17, z1 - 0.13, z1 - 0.07)
        T.box(a, b, 0.12, 0.17, zm - 0.035, zm + 0.035)
    # stone sill just above the belt
    ST.box(cx - hw - 0.08, cx + hw + 0.08, -0.06, RECESS, z0 - 0.08, z0)
    # dark soldier-course hood with a shallow segmental crown, pale keystone
    hh = HOOD_W / 2
    HD.prism([(cx - hh, HOOD_Z0), (cx + hh, HOOD_Z0)] + segment_top(cx, hh, HOOD_END, HOOD_TOP),
             -0.06, 0.05)
    ST.prism([(cx - 0.09, 7.10), (cx + 0.09, 7.10), (cx + 0.11, 7.55), (cx - 0.11, 7.55)], -0.09, 0.05)


for i, x in enumerate(WIN_X):
    window_pair(x, i)

# belt course 4.25-4.80, plain brick band projecting 0.15 across the full front
BR.box(AX0, AX1, -BELT_OUT, 0.02, BELT0, BELT1)

# ---------------------------------------------------------------------------
# Parapet: thin stone coping along the stepped gable, blank pale panel, south corner pier
# ---------------------------------------------------------------------------
# top edge, walked north to south so the outside (up) is on the right
TOP_LINE = [(AX1, SHOULDER), (STEP_X, SHOULDER), (STEP_X, SHOULDER + STEP_UP), (0.0, APEX),
            (-STEP_X, SHOULDER + STEP_UP), (-STEP_X, SHOULDER), (AX0, SHOULDER)]
outer = offset_line(TOP_LINE, 0.07)
inner = offset_line(TOP_LINE, 0.0)
ST.prism(outer + inner[::-1], -0.04, PAR_T + 0.04, axis="y")
ST.box(-0.73, 0.73, -0.035, 0.01, 7.37, 8.06)                          # blank pale panel (no lettering)
# south corner pier rising to 8.05 with a corbelled cap (card)
BR.box(AX0, AX0 + 0.56, 0.0, 0.56, A_SIDE - 0.10, 7.93)
BR.box(AX0 - 0.03, AX0 + 0.59, -0.03, 0.59, 7.93, 7.99)
BR.box(AX0 - 0.06, AX0 + 0.62, -0.06, 0.62, 7.99, 8.05)
# side-wall copings, flat tin roof deck behind the parapet, small vent pipe
ST.box(AX0 - 0.04, AX0 + 0.20, PAR_T, AY1, A_SIDE, A_SIDE + 0.07)
ST.box(AX1 - 0.20, AX1 + 0.04, PAR_T, AY1, A_SIDE, A_SIDE + 0.07)
R.box(AX0 + 0.20, AX1 - 0.20, PAR_T, AY1, A_SIDE - 0.02, A_SIDE + 0.03)
IR.lathe(-4.50, 1.40, [(0.06, A_SIDE), (0.06, 8.30), (0.10, 8.30), (0.10, 8.38)], sides=8)

# ---------------------------------------------------------------------------
# Ground floor (S -> N): shop window, shop door, theatre entrance; panelled bands
# ---------------------------------------------------------------------------


def panel_band(x0, x1, n):
    """Pale panelled band in the opening head 2.85 ... 4.05: plate, rails and stiles."""
    T.box(x0, x1, 0.18, RECESS, BAND0, GF_HEAD)
    T.box(x0, x1, 0.13, 0.18, GF_HEAD - 0.09, GF_HEAD)
    T.box(x0, x1, 0.13, 0.18, BAND0, BAND0 + 0.09)
    step = (x1 - x0 - 0.09) / n
    for i in range(n + 1):
        a = x0 + i * step
        T.box(a, a + 0.09, 0.13, 0.18, BAND0 + 0.09, GF_HEAD - 0.09)


# shop window: stone ledge, pale bulkhead, plate glass with one mullion, band
s0, s1 = SHOP
KA.box(s0, s1, -0.25, RECESS, 0.15, GF_HEAD)
ST.box(s0 - 0.06, s1 + 0.06, -0.10, 0.10, SKIRT, 0.17)                  # low ledge
ST.box(s0, s1, 0.08, RECESS, 0.15, 0.60)                                # bulkhead
T.box(s0, s1, 0.06, RECESS, 0.60, 0.66)                                 # sill rail
# plate glass either side of the mullion, the shared shop interior behind (narrow south light:
# shop_b; wide north light: shop_a cropped to its proportions)
pane(FRONT, s0 + 0.08, -4.18, 0.66, BAND0 - 0.07, -0.17, "shop_b")
pane(FRONT, -4.10, s1 - 0.08, 0.66, BAND0 - 0.07, -0.17, "shop_a", crop=(0.0, 1.0, 0.12, 0.79))
T.box(s0, s0 + 0.08, 0.10, RECESS, 0.60, BAND0)
T.box(s1 - 0.08, s1, 0.10, RECESS, 0.60, BAND0)
T.box(s0, s1, 0.10, RECESS, BAND0 - 0.07, BAND0)                       # head rail
T.box(-4.18, -4.10, 0.10, RECESS, 0.60, BAND0)                          # mullion at -4.14
panel_band(s0, s1, 4)

# shop door: pair of glazed doors, head rail, band, stone threshold
d0, d1 = SHOP_DOOR
KA.box(d0, d1, -0.25, RECESS, 0.0, GF_HEAD)
ST.box(d0, d1, -0.04, RECESS, SKIRT, 0.02)
T.box(d0, d0 + 0.10, 0.12, RECESS, 0.0, BAND0)
T.box(d1 - 0.10, d1, 0.12, RECESS, 0.0, BAND0)
T.box(d0, d1, 0.12, RECESS, 2.72, BAND0)
for k, (a, b) in enumerate(((d0 + 0.10, (d0 + d1) / 2), ((d0 + d1) / 2, d1 - 0.10))):
    DR.box(a, b, 0.18, 0.23, 0.02, 1.05)                                # leaf: lower part
    DR.box(a, a + 0.11, 0.18, 0.23, 1.05, 2.58)                         # stiles round the light
    DR.box(b - 0.11, b, 0.18, 0.23, 1.05, 2.58)
    DR.box(a, b, 0.18, 0.23, 2.58, 2.72)                                # top rail
    pane(FRONT, a + 0.11, b - 0.11, 1.05, 2.58, -0.20, ("door_l", "door_r")[k], grow=0.04)   # glazed upper
    DR.box(a + 0.13, b - 0.13, 0.165, 0.18, 0.24, 0.90)                 # raised lower panel
T.box((d0 + d1) / 2 - 0.02, (d0 + d1) / 2 + 0.02, 0.16, 0.18, 0.02, 2.72)   # meeting astragal
panel_band(d0, d1, 2)

# theatre entrance: 0.25 recess for the band, a 1.00-deep dark lobby below 2.85
e0, e1 = ENTR
KA.box(e0, e1, -0.25, RECESS, 0.0, GF_HEAD)
KA.box(e0, e1, -0.25, LOBBY_D, 0.0, BAND0)
panel_band(e0, e1, 3)
LB.box(e0, e0 + 0.02, RECESS, LOBBY_D, 0.0, BAND0)                       # lobby lining
LB.box(e1 - 0.02, e1, RECESS, LOBBY_D, 0.0, BAND0)
LB.box(e0, e1, LOBBY_D - 0.02, LOBBY_D, 0.0, BAND0)
LB.box(e0, e1, RECESS - 0.07, LOBBY_D, BAND0 - 0.02, BAND0)
ST.box(e0, e1, -0.04, LOBBY_D, SKIRT, 0.02)                              # lobby floor, threshold
# pair of panelled lobby doors with small glazed lights and a transom (guess)
LD0, LD1, LDY = 3.45, 5.05, LOBBY_D - 0.02
T.box(LD0 - 0.08, LD0, LDY - 0.05, LDY, 0.02, 2.70)
T.box(LD1, LD1 + 0.08, LDY - 0.05, LDY, 0.02, 2.70)
T.box(LD0 - 0.08, LD1 + 0.08, LDY - 0.05, LDY, 2.30, 2.38)
T.box(LD0 - 0.08, LD1 + 0.08, LDY - 0.05, LDY, 2.70, 2.78)
# lights: glass 1 cm into the leaf, the dim foyer (hotel_lobby.jpg) 3.5 cm behind it, just in
# front of the lobby lining
pane(FRONT, LD0, LD1, 2.38, 2.70, -(LDY - 0.04), "lobby_4", grow=0.04, crop=(0.0, 1.0, 0.72, 0.98), gap=0.035)
for k, (a, b) in enumerate(((LD0, (LD0 + LD1) / 2), ((LD0 + LD1) / 2, LD1))):
    DR.box(a, b, LDY - 0.05, LDY, 0.02, 1.30)                           # leaf: lower part
    DR.box(a, a + 0.12, LDY - 0.05, LDY, 1.30, 2.12)                    # stiles round the light
    DR.box(b - 0.12, b, LDY - 0.05, LDY, 1.30, 2.12)
    DR.box(a, b, LDY - 0.05, LDY, 2.12, 2.30)                           # top rail
    pane(FRONT, a + 0.12, b - 0.12, 1.30, 2.12, -(LDY - 0.04), ("lobby_4", "lobby_6")[k], grow=0.04,
         crop=(0.0, 1.0, 0.05, 0.85), gap=0.035)
    DR.box(a + 0.14, b - 0.14, LDY - 0.065, LDY - 0.05, 0.22, 1.10)
# small ticket opening in the lobby back wall (guess): frame, glass, shelf
TK0, TK1 = 2.72, 3.20
T.box(TK0 - 0.06, TK1 + 0.06, LDY - 0.04, LDY, 1.00, 1.62)
TK.box(TK0, TK1, LDY - 0.05, LDY - 0.035, 1.06, 1.56)                   # plain dark glass (as built)
ST.box(TK0 - 0.08, TK1 + 0.08, LDY - 0.20, LDY, 1.00, 1.05)
# two poster frames on the piers beside the entrance (artistic): dark frame, plain empty backing board
for i, pc in enumerate(((SHOP_DOOR[1] + ENTR[0]) / 2, (ENTR[1] + AX1) / 2)):
    DR.box(pc - 0.33, pc + 0.33, -0.05, 0.01, 0.90, 1.98)
    atlas_rec(region="poster%d" % (i + 1), mode="rect", wall=wall_rec(FRONT),
              u0=pc - 0.28, u1=pc + 0.28, z0=0.97, z1=1.91)
    AT.box(pc - 0.28, pc + 0.28, -0.06, -0.04, 0.97, 1.91)
AT.rid = 0

# three opal globe lamps on short iron arms under the belt
for x in LAMP_X:
    IR.box(x - 0.04, x + 0.04, -0.02, 0.01, 4.06, 4.24)                 # wall plate
    IR.tube((x, 0.0, 4.15), (x, -0.37, 4.15), 0.016, 6)                 # arm
    IR.tube((x, -0.35, 4.15), (x, -0.35, 3.99), 0.014, 6)               # drop rod
    IR.lathe(x, -0.35, [(0.035, 3.95), (0.075, 3.97), (0.075, 4.02), (0.035, 4.02)], sides=8)   # fitter
    rings = [(0.18 * math.sin(math.pi * k / 9) + (0.0 if 0 < k < 9 else 0.001), 3.80 - 0.18 * math.cos(math.pi * k / 9))
             for k in range(10)]
    rings[-1] = (0.05, 3.96)                                            # open neck into the fitter
    GB.lathe(x, -0.35, rings, sides=16)

# ---------------------------------------------------------------------------
# South wall of A (sunlit, seen from the alley): iron downpipe, two plain doors
# ---------------------------------------------------------------------------
PX, PY = AX0 - 0.07, 0.35
IR.tube((PX, PY, 0.32), (PX, PY, 7.16), 0.05, 8)                         # downpipe
IR.tube((PX, PY, 0.34), (PX - 0.05, PY, 0.12), 0.05, 8)                  # curved foot
IR.tube((PX - 0.04, PY, 0.15), (PX - 0.26, PY, -0.07), 0.05, 8)
ST.box(PX - 0.50, PX - 0.12, PY - 0.17, PY + 0.17, SKIRT, ALLEY + 0.05)  # splash block
IR.box(PX - 0.12, AX0, PY - 0.13, PY + 0.13, 7.10, 7.36)                 # rain head (bracket)
IR.box(PX - 0.02, AX0, PY - 0.04, PY + 0.04, 7.24, 7.32)                 # scupper through the wall
for z in (1.6, 3.6, 5.6):
    IR.box(PX - 0.06, AX0, PY - 0.065, PY + 0.065, z, z + 0.04)          # straps


def plain_door(wall, cu, w, z0, z1, mb, panels=True):
    """Plain door in a 0.20 recess: leaf with four raised panels (or ledged planks), stone step."""
    hw = w / 2
    wall.cut.wbox(wall, cu - hw, cu + hw, z0, z1, -0.20, 0.25)
    mb.wbox(wall, cu - hw, cu + hw, z0, z1, -0.20, -0.14)
    if panels:
        for ua, ub in ((cu - hw + 0.12, cu - 0.04), (cu + 0.04, cu + hw - 0.12)):
            for za, zb in ((z0 + 0.18, z0 + (z1 - z0) * 0.45), (z0 + (z1 - z0) * 0.52, z1 - 0.14)):
                mb.wbox(wall, ua, ub, za, zb, -0.14, -0.125)
    else:
        mb.wbox(wall, cu - 0.03, cu + 0.03, z0, z1, -0.14, -0.12)          # meeting stile
        for z in (z0 + 0.30, (z0 + z1) / 2, z1 - 0.35):
            mb.wbox(wall, cu - hw + 0.06, cu + hw - 0.06, z, z + 0.14, -0.14, -0.12)   # ledges
    ST.wbox(wall, cu - hw - 0.08, cu + hw + 0.08, SKIRT, z0, -0.20, 0.30)    # step / pad
    ST.wbox(wall, cu - hw - 0.04, cu + hw + 0.04, z1, z1 + 0.10, -0.02, 0.04)  # stone lintel


for y in (7.7, 14.0):
    plain_door(SOUTH_A, -y, 0.95, 0.0, 2.20, DR)

# ---------------------------------------------------------------------------
# B / C: plain hollow-tile walls, fire exits, rear door, roofs
# ---------------------------------------------------------------------------
for y in (28.6, 39.6):
    plain_door(SOUTH_B, -y, 1.60, -0.08, 2.20, FD, panels=False)
    ST.wbox(SOUTH_B, -y - 1.10, -y + 1.10, SKIRT, -0.08, 0.0, 1.20)    # concrete pad
plain_door(REAR_C, 2.5, 1.00, 0.0, 2.15, DR, panels=False)

# B: low tin gable roof (0.15 eaves overhang), C: flat tin roof
slope = (B_RIDGE - B_EAVE) / (B_RIDGE_X - BX0)
ze = B_EAVE - 0.15 * slope
R.prism([(BX0 - 0.15, ze), (B_RIDGE_X, B_RIDGE), (BX1 + 0.15, ze), (BX1 + 0.15, ze + 0.06),
         (B_RIDGE_X, B_RIDGE + 0.06), (BX0 - 0.15, ze + 0.06)], AY1, BY1)
R.box(BX0 - 0.05, BX1 + 0.05, BY1, CY1 + 0.05, C_TOP, C_TOP + 0.04)
SU.box(BX0 - 0.05, BX1 + 0.05, CY1, CY1 + 0.05, C_TOP - 0.20, C_TOP)    # thin fascia at the rear

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
    cut_shell(shell, cutter, "PT_" + name, mat)
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("PT_" + key, MATS[BUILDER_MAT[key]], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Palace Theatre built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)",
      "| atlas records", len(ATLAS), "| panes", len(BACKREC))
# Materials, baked lighting and GLB export: run palace_theatre_bake.py (it runs this file first).
