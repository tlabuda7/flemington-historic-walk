"""
store_27.py - builds the dry goods and clothing store at 27 Main St, Flemington (west side,
old nos. 519 A/B, "D.G. & Clo." on the Sept 1921 Sanborn; possibly the "Potter Building"),
as it stood in 1921, directly north of the Palace Theatre:
  A  front part, 12.35 m wide, 4.22 m deep: the 1910s build-out over the old 2-storey frame
     porch, to the street line and ~2 m wider on the south (research/sanborn-and-today-
     findings.md). Deep plain cornice, blank brick frieze, pale head and sill bands between
     pale corner strips, four tall 1/1 windows with pale side strips, dark shop cornice,
     pale piers, a plain shop front (two display windows, one recessed door; a guess, hidden
     under the awning on the card), one long plain awning, one opal globe lamp
  B  main block behind (10.24 m wide, the south light court beside it), low gable roof with
     its ridge parallel to Main St, one chimney at the north end
  C  2-storey frame gallery across the rear (plain closed lean-to)
  D  1-storey frame wing behind, plain rear door
No lettering, no sign, no sign board anywhere (owner rule).

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/store_27.py").read())

Every run deletes and rebuilds the "Store27" collection. Materials, lightmap bake and GLB
export: store_27_bake.py (runs this file first). Pattern: palace_theatre.py / block_40_46.py
(builders per material, Wall frames, one closed wall shell per part with boolean recesses).

Windows (PLAN.md section E, as the Bank Building and 40-46 Main): every pane is ONE glass face
(builder Glass -> material `glass`, transparent, not lightmapped) 4 cm in front of a window back:
upstairs cells of the shared assets/textures/shared/window_backs.jpg (builder WBack), the shop
windows, door lights and the glazed vestibule returns cells of shared/shop_interior.jpg
(builder ShopInt: shelves of cloth bolts, counters). The awning iron and the lamp fitter take
one dark texel of the window-back atlas. BACKREC[rid] -> UV record (read by the bake).

Sources: PLAN.md "Dry goods and clothing store (27 Main St, old nos. 519 A/B)" spec (1921
Sanborn sheet 2 footprint and heights; front from the "Palace Theatre & Potter Building" card by
perspective fit, +-0.3 m). Owner approval 2026-11-10: plain guessed front.

Coordinates (metres, Blender Z-up), origin = scene (-10.30, 0.15, -158.49), rotation 0 90 0:
    X  along the street, +X = north (open ground to no. 17), -X = south (Palace Theatre)
    Y  depth: y = 0 is the front wall (property line); awning out to -1.90, cornice to -0.59
    Z  up from the sidewalk top; walls skirt down to -0.20; alley and yards at -0.15
Scene: world x = -10.30 - Y, world z = -158.49 - X.
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".
"""

import json
import math
import random
import bpy
import bmesh

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md massing table and front elevation)
# ---------------------------------------------------------------------------
HW = 6.175                      # half front (12.35 m)
AY = 4.22                       # A: front part depth (the south light court starts behind it)
BX0, BY1 = -4.06, 24.16         # B: south wall (light court side), rear brick wall
EAVE_F, RIDGE_Y, RIDGE_Z, EAVE_R = 7.55, 7.0, 8.10, 7.00   # low gable, ridge parallel to Main
CY1, C_TOP, C_TOP_R = 25.61, 6.40, 6.20       # C: rear frame gallery (shed roof)
DX0, DX1, DY1, D_TOP, D_TOP_R = -4.06, 1.10, 41.60, 3.60, 3.30   # D: 1-storey frame wing
SKIRT = -0.20
YARD = -0.15

CORN0, CORN1, CORN_OUT = 7.28, 7.62, 0.55     # plain box cornice
HEAD0, HEAD1 = 5.82, 6.02                     # head band
SILL0, SILL1 = 3.60, 3.90                     # sill band
STRIP_W, PROUD = 0.20, 0.03                   # corner strips, band projection
WIN_X = (-4.71, -1.57, 1.57, 4.71)
WIN_W, WIN_Z0, WIN_Z1 = 0.95, SILL1, HEAD0   # opening; sashes from 3.95 (spec)
SIDE_W = 0.18                                 # pale side strips beside the windows
BEAM0, BEAM1, BEAM_OUT = 2.95, 3.35, 0.12     # dark shop cornice
PIER_S, PIER_N = -5.55, 5.60                  # pale piers outside these
SF_D = 0.10                                   # shop front set back 0.10
GL_Z0, GL_Z1 = 0.55, 2.75                     # display glass on the bulkhead
DOOR0, DOOR1, DOOR_D, DOOR_H = 0.25, 1.95, 0.90, 2.75
MULLION = -2.65
LAMP = (-5.85, -0.35, 3.35)                   # one opal globe at the south corner
AW0, AW1, AWY, AWZ0, AWZ1 = PIER_S, HW, -1.90, 2.95, 2.30   # plain awning
CHIM = (4.90, 5.90, 5.70, 6.30, 9.00)         # chimney x0, x1, y0, y1, top


def roof_z(y):
    """Top of the brick walls under the roof: front eave 7.55 rising to the ridge 8.10 at
    Y 7.0, falling to the rear eave 7.00 at Y 24.16."""
    if y <= RIDGE_Y:
        return EAVE_F + (RIDGE_Z - EAVE_F) * y / RIDGE_Y
    return RIDGE_Z - (RIDGE_Z - EAVE_R) * (y - RIDGE_Y) / (BY1 - RIDGE_Y)


# ---------------------------------------------------------------------------
# Materials (plain stand-ins; store_27_bake.py swaps in the textures)
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


COLOURS = {"Brick": "#7A4436", "Bands": "#CDBFA2", "Shop": "#2E2E26", "Roof": "#5A3D34",
           "Clap": "#C3BDAD", "Awning": "#8C8573", "Glass": "#1A1916", "WBack": "#2A2420",
           "ShopInt": "#2A2420"}
MATS = {k: plain("S27_" + k, c) for k, c in COLOURS.items()}
# builder -> material (the bake gives every builder its own UVs and tint)
BUILDER_MAT = {"Brick": "Brick", "Bands": "Bands", "Globe": "Bands", "Shop": "Shop", "Roof": "Roof",
               "Clap": "Clap", "Awning": "Awning", "Glass": "Glass", "Iron": "WBack", "WBack": "WBack",
               "ShopInt": "ShopInt"}

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
    """Collects closed solids for one builder. Faces get the current `rid` (back record)."""

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
        """Round bar between two points (lamp arm, awning arms)."""
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

    def quad(self, wall, u0, u1, z0, z1, d):
        """ONE single-sided face on a wall plane (d out from the wall face), facing outward."""
        vs = [self.bm.verts.new(wall.pt(u, z, d)) for u, z in ((u0, z0), (u1, z0), (u1, z1), (u0, z1))]
        f = self.bm.faces.new(vs)
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


col = fresh_collection("Store27")
G = {k: MB() for k in BUILDER_MAT}
BR, BD, GB, SP, R, CL, AW, GL, IR, WB, SH = (G[k] for k in ("Brick", "Bands", "Globe", "Shop", "Roof", "Clap",
                                                           "Awning", "Glass", "Iron", "WBack", "ShopInt"))
# wall shells (closed solids) and their cutters: name -> (shell, cutter, material)
SHELLS = {k: (MB(), MB(), m) for k, m in (("ShellAB", "Brick"), ("ShellC", "Clap"), ("ShellD", "Clap"))}
SAB, SC, SD = (SHELLS[k][0] for k in SHELLS)
KAB, KC, KD = (SHELLS[k][1] for k in SHELLS)

# ---------------------------------------------------------------------------
# Window backs (section E): cells of the shared atlases, no repeats side by side.
# ---------------------------------------------------------------------------
WB_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\window_backs.json"))["cells"]
SHOP_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\shop_interior.json"))["cells"]
GAP = 0.04                      # window back this far behind the glass
# upstairs over a dry goods store: stock rooms and a workroom - blinds and plain dark rooms
UPSTAIRS = {"blind_cream_high": 3, "blind_cream_half": 3, "blind_cream_low": 2, "blind_green_high": 2,
            "blind_green_half": 2, "dark_room": 2, "dark_room_frame": 2, "blind_cream_full": 1}
_wb_rng = random.Random(1921)
BACKREC = {}


def pick_row(weights, n):
    out = []
    for _ in range(n):
        names = [k for k in weights if not out or k != out[-1]]
        out.append(_wb_rng.choices(names, weights=[weights[k] for k in names])[0])
    return out


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


def pane(wall, u0, u1, z0, z1, d_glass, cell):
    """Glass face at depth d_glass with its window back GAP behind it."""
    back(wall, u0, u1, z0, z1, d_glass - GAP, cell)
    GL.quad(wall, u0, u1, z0, z1, d_glass)


FRONT = Wall((0.0, 0.0), (0, -1), KAB)        # u = X (north to the right)
D_REAR = Wall((0.0, DY1), (0, 1), KD)          # u = -X

# ---------------------------------------------------------------------------
# Shells
# ---------------------------------------------------------------------------
# A + B: one closed L-shaped solid (A full width to Y 4.22, then B 2.11 m narrower on the south),
# walls up to the roof line (front slope to the ridge at Y 7.0, rear slope down to the rear wall).
zA = roof_z(AY)
cos = [(-HW, 0, SKIRT), (HW, 0, SKIRT), (HW, BY1, SKIRT), (BX0, BY1, SKIRT), (BX0, AY, SKIRT), (-HW, AY, SKIRT),
       (-HW, 0, EAVE_F), (HW, 0, EAVE_F), (HW, RIDGE_Y, RIDGE_Z), (HW, BY1, EAVE_R), (BX0, BY1, EAVE_R),
       (BX0, RIDGE_Y, RIDGE_Z), (BX0, AY, zA), (-HW, AY, zA)]
SAB.solid(cos, [[5, 4, 3, 2, 1, 0],                 # bottom
                [0, 1, 7, 6],                       # front
                [1, 2, 9, 8, 7],                    # north
                [2, 3, 10, 9],                      # rear
                [3, 4, 12, 11, 10],                 # B south (light court)
                [4, 5, 13, 12],                     # step at Y 4.22 (faces the light court)
                [5, 0, 6, 13],                      # A south (the slit to the Palace)
                [6, 7, 8, 11, 12, 13],              # roof plane, front slope
                [11, 8, 9, 10]])                    # roof plane, rear slope
# C: frame gallery, shed roof falling to the rear; D: 1-storey wing
SC.prism([(BY1, SKIRT), (CY1, SKIRT), (CY1, C_TOP_R), (BY1, C_TOP)], BX0, HW, axis="x")
SD.prism([(CY1, SKIRT), (DY1, SKIRT), (DY1, D_TOP_R), (CY1, D_TOP)], DX0, DX1, axis="x")

# ---------------------------------------------------------------------------
# Upper floor: four tall 1/1 windows, pale side strips, head and sill bands, corner strips
# ---------------------------------------------------------------------------
cells_up = pick_row(UPSTAIRS, len(WIN_X))
for cx, cell in zip(WIN_X, cells_up):
    hw = WIN_W / 2
    x0, x1 = cx - hw, cx + hw
    KAB.box(x0, x1, -0.25, 0.25, WIN_Z0, WIN_Z1)                         # opening, 0.25 deep
    SP.box(x0, x1, 0.0, 0.25, WIN_Z0, 3.96)                              # wooden sub-sill
    z0, z1 = 3.96, WIN_Z1
    pane(FRONT, x0, x1, z0, z1, -0.19, cell)                             # glass 0.19 in (spec 0.20)
    # frame: jambs and head
    SP.box(x0, x0 + 0.06, 0.12, 0.25, z0, z1)
    SP.box(x1 - 0.06, x1, 0.12, 0.25, z0, z1)
    SP.box(x0, x1, 0.12, 0.25, z1 - 0.07, z1)
    # 1/1 sashes: stiles, top and bottom rails, meeting rail (in front of the glass)
    a, b = x0 + 0.06, x1 - 0.06
    zm = (z0 + z1 - 0.07) / 2
    SP.box(a, a + 0.05, 0.13, 0.18, z0, z1 - 0.07)
    SP.box(b - 0.05, b, 0.13, 0.18, z0, z1 - 0.07)
    SP.box(a, b, 0.13, 0.18, z0, z0 + 0.09)
    SP.box(a, b, 0.13, 0.18, z1 - 0.13, z1 - 0.07)
    SP.box(a, b, 0.12, 0.18, zm - 0.035, zm + 0.035)
    # pale side strips 0.18 each side, 0.03 proud, between the bands
    BD.box(x0 - SIDE_W, x0, -PROUD, 0.01, SILL1, HEAD0)
    BD.box(x1, x1 + SIDE_W, -PROUD, 0.01, SILL1, HEAD0)

# head band and sill band between the corner strips; corner strips (wrap 0.01 round the corners)
for z0, z1 in ((HEAD0, HEAD1), (SILL0, SILL1)):
    BD.box(-HW + STRIP_W, HW - STRIP_W, -PROUD, 0.01, z0, z1)
for x0, x1 in ((-HW - 0.01, -HW + STRIP_W), (HW - STRIP_W, HW + 0.01)):
    BD.box(x0, x1, -PROUD, 0.01, SILL0, CORN0)

# ---------------------------------------------------------------------------
# Cornice: plain wooden box, dark soffit, pale upper edge (no brackets); returns at both ends
# ---------------------------------------------------------------------------
SP.box(-HW - 0.02, HW + 0.12, -0.12, 0.02, CORN0, CORN0 + 0.06)                     # bed moulding
SP.box(-HW - 0.03, HW + 0.14, -CORN_OUT, 0.02, CORN0 + 0.06, CORN1 - 0.045)         # box: fascia + soffit
BD.box(-HW - 0.05, HW + 0.16, -CORN_OUT - 0.03, 0.02, CORN1 - 0.045, CORN1)         # pale upper edge

# ---------------------------------------------------------------------------
# Roof: tin over both slopes (0.08 over the side walls, 0.12 over the rear wall), chimney
# ---------------------------------------------------------------------------
RT = 0.06


def roof_sheet(x0, x1, y0, y1, z0, z1):
    """Thin sheet whose top runs from z0 at y0 to z1 at y1 (straight slope)."""
    R.solid([(x0, y0, z0 - RT), (x1, y0, z0 - RT), (x1, y1, z1 - RT), (x0, y1, z1 - RT),
             (x0, y0, z0), (x1, y0, z0), (x1, y1, z1), (x0, y1, z1)],
            [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])


rs_f = (RIDGE_Z - EAVE_F) / RIDGE_Y
rs_r = (RIDGE_Z - EAVE_R) / (BY1 - RIDGE_Y)
o = 0.08
roof_sheet(-HW - o, HW + o, 0.02, AY, roof_z(0.02) + RT, roof_z(AY) + RT)                   # over A
roof_sheet(-HW - o, BX0 - o, AY, AY + o, roof_z(AY) + RT, roof_z(AY + o) + RT)              # A's eave over the court
roof_sheet(BX0 - o, HW + o, AY, RIDGE_Y, roof_z(AY) + RT, RIDGE_Z + RT)
roof_sheet(BX0 - o, HW + o, RIDGE_Y, BY1 + 0.12, RIDGE_Z + RT, EAVE_R - 0.12 * rs_r + RT)
# ridge cap
R.box(BX0 - o, HW + o, RIDGE_Y - 0.08, RIDGE_Y + 0.08, RIDGE_Z + RT - 0.02, RIDGE_Z + RT + 0.03)
# chimney (card: low flat-topped block at the north end of the roof), corbelled cap
cx0, cx1, cy0, cy1, ctop = CHIM
BR.box(cx0, cx1, cy0, cy1, 7.60, ctop - 0.12)
BR.box(cx0 - 0.04, cx1 + 0.04, cy0 - 0.04, cy1 + 0.04, ctop - 0.12, ctop - 0.04)
BR.box(cx0 - 0.02, cx1 + 0.02, cy0 - 0.02, cy1 + 0.02, ctop - 0.04, ctop)

# ---------------------------------------------------------------------------
# Ground floor: piers, shop cornice, shop front (plain, a guess), recessed door
# ---------------------------------------------------------------------------
# pale piers (flush with the wall, a 1.5 cm facing), dark shop cornice beam with a small cap
BD.box(-HW - 0.01, PIER_S, -0.015, 0.02, SKIRT, BEAM0)
BD.box(PIER_N, HW + 0.01, -0.015, 0.02, SKIRT, BEAM0)
SP.box(-HW - 0.015, HW + 0.015, -BEAM_OUT, 0.02, BEAM0, BEAM1 - 0.06)
SP.box(-HW - 0.03, HW + 0.03, -BEAM_OUT - 0.04, 0.02, BEAM1 - 0.06, BEAM1)

# the shop-front opening: 0.30 pocket between the piers, the vestibule 0.95 deep
KAB.box(PIER_S, PIER_N, -0.25, 0.30, 0.0, BEAM0)
KAB.box(DOOR0, DOOR1, -0.25, DOOR_D + 0.05, 0.0, DOOR_H)
# dark panel over the glass and the vestibule (2.75 ... 2.95)
SP.box(PIER_S, PIER_N, SF_D, 0.30, GL_Z1, BEAM0)
SP.box(DOOR0, DOOR1, 0.0, SF_D + 0.01, GL_Z1, BEAM0)


def display(x0, x1, cells, mullions=()):
    """Display window between x0 and x1 in the shop-front plane (Y 0.10): dark bulkhead with
    raised panels, sill rail, glass on shop_interior cells, head rail, mullions."""
    SP.box(x0, x1, SF_D, 0.30, 0.0, GL_Z0)                                         # bulkhead
    n = max(1, round((x1 - x0) / 1.45))
    step = (x1 - x0 - 0.10) / n
    for k in range(n):
        a = x0 + 0.10 + k * step
        SP.box(a + 0.04, a + step - 0.06, SF_D - 0.015, SF_D, 0.12, GL_Z0 - 0.12)     # raised panel
    SP.box(x0, x1, SF_D - 0.04, 0.30, GL_Z0 - 0.03, GL_Z0 + 0.03)                  # sill rail
    SP.box(x0, x1, SF_D - 0.01, 0.30, GL_Z1 - 0.05, GL_Z1)                         # head rail
    edges = [x0] + list(mullions) + [x1]
    for (a, b), cell in zip(zip(edges, edges[1:]), cells):
        pane(FRONT, a, b, GL_Z0 + 0.03, GL_Z1 - 0.05, -(SF_D + 0.04), cell)
    for m in mullions:
        SP.box(m - 0.035, m + 0.035, SF_D - 0.01, 0.30, GL_Z0, GL_Z1)


display(PIER_S + 0.10, DOOR0 - 0.08, ("shop_b", "shop_a"), mullions=(MULLION,))
display(DOOR1 + 0.08, PIER_N - 0.10, ("shop_b",))
# outer jambs against the piers, corner posts at the vestibule (full height to the panel)
SP.box(PIER_S, PIER_S + 0.10, 0.0, 0.30, 0.0, GL_Z1)
SP.box(PIER_N - 0.10, PIER_N, 0.0, 0.30, 0.0, GL_Z1)
SP.box(DOOR0 - 0.08, DOOR0 + 0.06, 0.0, 0.30, 0.0, GL_Z1)
SP.box(DOOR1 - 0.06, DOOR1 + 0.08, 0.0, 0.30, 0.0, GL_Z1)

# vestibule: stone floor and threshold, dark ceiling, glazed returns on both sides
BD.box(DOOR0, DOOR1, -0.03, DOOR_D + 0.05, SKIRT, 0.02)
SP.box(DOOR0, DOOR1, SF_D, DOOR_D + 0.05, DOOR_H - 0.02, DOOR_H)
RET_S = Wall((DOOR0, 0.0), (1, 0), None)        # south return, faces north into the vestibule, u = +Y
RET_N = Wall((DOOR1, 0.0), (-1, 0), None)       # north return, faces south, u = -Y
for wall, (u0, u1), cell in ((RET_S, (0.30, DOOR_D - 0.05), "return_s"),
                             (RET_N, (-(DOOR_D - 0.05), -0.30), "return_n")):
    SP.wbox(wall, u0, u1, 0.0, GL_Z0, 0.0, 0.10)                                   # bulkhead
    SP.wbox(wall, u0, u1, GL_Z0 - 0.03, GL_Z0 + 0.03, 0.0, 0.13)                   # sill rail
    SP.wbox(wall, u0, u1, GL_Z1 - 0.07, GL_Z1 - 0.02, 0.0, 0.11)                   # head rail
    pane(wall, u0, u1, GL_Z0 + 0.03, GL_Z1 - 0.07, 0.08, cell)
# door frame and a pair of plain glazed doors at the back of the vestibule (head 2.75)
DY = DOOR_D
SP.box(DOOR0, DOOR0 + 0.08, DY - 0.05, DY + 0.05, 0.0, DOOR_H)
SP.box(DOOR1 - 0.08, DOOR1, DY - 0.05, DY + 0.05, 0.0, DOOR_H)
SP.box(DOOR0, DOOR1, DY - 0.05, DY + 0.05, DOOR_H - 0.12, DOOR_H)
mid = (DOOR0 + DOOR1) / 2
for (a, b), cell in (((DOOR0 + 0.08, mid), "door_l"), ((mid, DOOR1 - 0.08), "door_r")):
    g0, g1 = a + 0.11, b - 0.11
    SP.box(a, g0, DY - 0.02, DY + 0.03, 0.02, DOOR_H - 0.12)                       # stiles
    SP.box(g1, b, DY - 0.02, DY + 0.03, 0.02, DOOR_H - 0.12)
    SP.box(g0, g1, DY - 0.02, DY + 0.03, 0.02, 0.85)                               # bottom rail / panel
    SP.box(g0, g1, DY - 0.02, DY + 0.03, DOOR_H - 0.26, DOOR_H - 0.12)             # top rail
    SP.box(g0 + 0.04, g1 - 0.04, DY - 0.035, DY - 0.02, 0.18, 0.72)                # raised panel
    pane(FRONT, g0, g1, 0.85, DOOR_H - 0.26, -(DY + 0.005), cell)
SP.box(mid - 0.02, mid + 0.02, DY - 0.035, DY - 0.02, 0.02, DOOR_H - 0.12)        # meeting astragal

# ---------------------------------------------------------------------------
# One opal globe lamp at the south corner on a short iron bracket
# ---------------------------------------------------------------------------
lx, ly, lz = LAMP
arm_z = lz + 0.21
IR.box(lx - 0.045, lx + 0.045, -0.02, 0.01, arm_z - 0.09, arm_z + 0.09)            # wall plate
IR.tube((lx, 0.0, arm_z), (lx, ly - 0.02, arm_z), 0.016, 6)                        # arm
IR.tube((lx, -0.10, arm_z), (lx, -0.02, arm_z - 0.10), 0.010, 6)                   # brace
IR.lathe(lx, ly, [(0.035, lz + 0.135), (0.07, lz + 0.155), (0.07, lz + 0.19), (0.02, lz + 0.205),
                  (0.02, arm_z + 0.02)], sides=8)                                     # fitter
rings = [(0.14 * math.sin(math.pi * k / 9) + (0.0 if 0 < k < 9 else 0.001), lz - 0.14 * math.cos(math.pi * k / 9))
         for k in range(10)]
rings[-1] = (0.045, lz + 0.14)                                                      # open neck into the fitter
GB.lathe(lx, ly, rings, sides=16)

# ---------------------------------------------------------------------------
# One long plain awning (no stripes, no scallops, no letters), iron arms at both ends
# ---------------------------------------------------------------------------
AW_T = 0.02
AW.prism([(-0.06, AWZ0 - 0.02), (AWY, AWZ1), (AWY, AWZ1 - AW_T), (-0.06, AWZ0 - 0.02 - AW_T)], AW0, AW1, axis="x")
AW.box(AW0, AW1, AWY - 0.012, AWY, AWZ1 - 0.17, AWZ1)                              # plain straight valance
IR.box(AW0, AW1, -0.10, -0.02, AWZ0 - 0.07, AWZ0 - 0.005)                          # roller box under the beam
IR.box(AW0, AW1, AWY + 0.005, AWY + 0.035, AWZ1 - 0.06, AWZ1 - 0.02)               # front bar
for x in (AW0 + 0.06, AW1 - 0.06):                                                 # side arms
    IR.tube((x, -0.02, 1.95), (x, AWY + 0.03, AWZ1 - 0.04), 0.012, 6)
    IR.box(x - 0.04, x + 0.04, -0.02, 0.005, 1.88, 2.02)                           # wall plate

# ---------------------------------------------------------------------------
# C and D: plain clapboard, shed roofs; one plain rear door on D
# ---------------------------------------------------------------------------
c_sl = (C_TOP - C_TOP_R) / (CY1 - BY1)
R.prism([(BY1 - 0.05, C_TOP + 0.05 * c_sl - 0.02), (CY1 + 0.12, C_TOP_R - 0.12 * c_sl - 0.02),
         (CY1 + 0.12, C_TOP_R - 0.12 * c_sl + 0.04), (BY1 - 0.05, C_TOP + 0.05 * c_sl + 0.04)],
        BX0 - 0.08, HW + 0.08, axis="x")
d_sl = (D_TOP - D_TOP_R) / (DY1 - CY1)
R.prism([(CY1 - 0.02, D_TOP + 0.02 * d_sl - 0.02), (DY1 + 0.15, D_TOP_R - 0.15 * d_sl - 0.02),
         (DY1 + 0.15, D_TOP_R - 0.15 * d_sl + 0.04), (CY1 - 0.02, D_TOP + 0.02 * d_sl + 0.04)],
        DX0 - 0.10, DX1 + 0.10, axis="x")
# rear door (u = -X on the rear wall): plank door in a 0.12 recess, cased, stone step
du, dw, dh = 1.5, 0.90, 2.05
KD.wbox(D_REAR, du - dw / 2, du + dw / 2, 0.0, dh, -0.12, 0.25)
SP.wbox(D_REAR, du - dw / 2, du + dw / 2, 0.0, dh, -0.12, -0.08)
SP.wbox(D_REAR, du - 0.02, du + 0.02, 0.0, dh, -0.08, -0.065)
for z in (0.30, 1.00, 1.70):
    SP.wbox(D_REAR, du - dw / 2 + 0.05, du + dw / 2 - 0.05, z, z + 0.12, -0.08, -0.065)
for a, b in ((du - dw / 2 - 0.10, du - dw / 2), (du + dw / 2, du + dw / 2 + 0.10)):
    SP.wbox(D_REAR, a, b, 0.0, dh + 0.10, -0.01, 0.025)                            # casing
SP.wbox(D_REAR, du - dw / 2 - 0.10, du + dw / 2 + 0.10, dh, dh + 0.10, -0.01, 0.025)
BD.wbox(D_REAR, du - dw / 2 - 0.10, du + dw / 2 + 0.10, SKIRT, 0.0, -0.05, 0.40)  # step

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
    cut_shell(shell, cutter, "S27_" + name, mat)
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("S27_" + key, MATS[BUILDER_MAT[key]], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Store 27 built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)",
      "| window backs", len(BACKREC), "| upstairs cells", cells_up)
# Materials, baked lighting and GLB export: run store_27_bake.py (it runs this file first).
