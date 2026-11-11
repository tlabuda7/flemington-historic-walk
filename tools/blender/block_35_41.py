"""
block_35_41.py - builds the block at 35-41 Main St, Flemington (west side), c. 1920, as on the
1921 Sanborn map (sheet 2) and the photos in PLAN.md "Block at 35-41 Main St":
  A  35-37 (old 517) 3-storey frame grocery ("Gro."), eave 8.53, low hip roof, scroll-bracketed
     boxed eave, brick chimney near the north wall
  B  its two-tier front porch: 4 round Tuscan columns per tier, raised floor with two steps,
     upper deck with turned balusters and the 1920s card's tall close bars, spindle frieze with a
     cut-out drop fringe, shed roof; the stair in the south bay (B2); a striped awning whose
     scalloped valance reads "PRODUCE | JACOB R. HALL | GROCER" (owner's decision 3b)
  C  2-storey frame rear wing, D 1-storey north shed
  E  39-41 (old 516) 2-storey-and-basement brick "Cobbler", set back 1.90: shallow balcony with
     flat sawn balusters, two tall shuttered windows onto it, basement door down an areaway with a
     blank board over it, plain parapet
  F  1-storey brick rear with its notch
  plus the concrete paving in front of the porch and in the brick court.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/block_35_41.py").read())

Every run deletes and rebuilds the "Block3541" collection. Materials, lightmap bake and GLB
export: block_35_41_bake.py (runs this file first). Pattern: palace_theatre.py (builders per
material, closed wall shells with shallow boolean recesses) and union_hotel.py / bank_building.py
for the windows.

Windows (PLAN.md "E. Windows that don't read as flat black", 2026-11-10): every pane is ONE glass
face (builder Glass -> material `glass`, transparent, see the bake) 4 cm in front of a "window
back" face. Upper floors, the 39-41 windows and its basement door use cells of the shared atlas
assets/textures/shared/window_backs.jpg (builder WindowBack); the grocery's shop window and door
glass use assets/textures/block-35-41/grocery_interior.jpg (tools/prepare_grocery_interior.py,
builder Grocery). Their atlas UVs (layer "UVMap") are set here; so are the UVs on the signs atlas
(awning stripes, lettered valance, louvred shutters, blank board; builder Signs). The bake keeps
them.

Coordinates (metres, Blender Z-up), origin = scene (-11.12, 0.15, -129.89), rotation 0 90 0:
    X  along the street, +X = north (alley, Palace Theatre), -X = south (County Hotel)
    Y  depth: y = 0 is the porch front of 35-37; front walls at 1.98 (35-37) and 1.90 (39-41)
    Z  up from the sidewalk top; walls skirt to -0.20; alley and yards at -0.15
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
# Dimensions (PLAN.md massing table)
# ---------------------------------------------------------------------------
AX0, AX1, AY0, AY1 = -0.47, 5.93, 1.98, 15.89      # A main block
EAVE, SOFFIT, FRIEZE0 = 8.53, 8.33, 8.05
RIDGE_X, RIDGE_Y0, RIDGE_Y1, RIDGE_Z = 2.73, 5.0, 12.9, 9.45
CX1, CY1, C_TOP = 4.06, 32.10, 6.10                  # C wing X -0.47 ... 4.06
DX0, DX1, DY1, D_TOP = 4.06, 5.65, 20.50, 3.10       # D shed
EX0, EX1, EY0, EY1 = -5.94, -0.92, 1.90, 12.43       # E brick
E_ROOF, E_TOP = 8.00, 8.53
FY1, FY2, FX_NOTCH, F_TOP = 15.43, 18.37, -3.11, 3.60
SKIRT, YARD = -0.20, -0.15
DECK = 0.45                                          # porch floor / shop floor
COL_X = (-0.35, 1.70, 3.76, 5.81)
COL_Y = 0.14
BEAM0, BEAM1 = 3.20, 3.70                            # beam between the tiers, upper deck
TOP0, TOP1 = 6.30, 6.45                              # top beam
ROOF_WALL, ROOF_FRONT = 6.85, 6.45                   # porch roof
WIN_X = (0.73, 2.73, 4.73)
E_WIN_X = (-4.68, -2.18)
STAIR_Y0, STAIR_Y1 = 0.30, 1.45                      # lower flight (front to back)
UP_X0, UP_X1 = 0.85, 2.45                            # upper flight / deck opening (south to north)
AW_Y, AW_Z0, AW_Z1, VAL_BOT = -1.30, 3.15, 2.50, 2.25
WELL = (-3.30, -1.80, 0.80, 1.90)                    # areaway X0, X1, Y0, Y1

# ---------------------------------------------------------------------------
# Materials (plain stand-ins; block_35_41_bake.py swaps in the textures)
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


COLOURS = {"Clapboard": "#D8CFB8", "Trim": "#A39A88", "Brick": "#7A4436", "Roof": "#5A3D34",
           "Wood": "#2E2E26", "Signs": "#B8A88E", "Paving": "#8A8780", "Glass": "#1A1916",
           "WindowBack": "#3A332C", "Grocery": "#2E2822"}
MATS = {k: plain("BL_" + k, c) for k, c in COLOURS.items()}
# builder -> material (the bake gives every builder its own UVs and bake tint)
BUILDER_MAT = {"Clap": "Clapboard", "Trim": "Trim", "Steps": "Trim", "Brick": "Brick", "Chimney": "Brick",
               "Roof": "Roof", "Wood": "Wood", "Iron": "Wood", "Signs": "Signs", "Paving": "Paving",
               "Glass": "Glass", "WindowBack": "WindowBack", "Grocery": "Grocery"}
ATLAS_BUILDERS = ("Signs", "WindowBack", "Grocery", "Glass")      # UVs set here, kept by the bake

# ---------------------------------------------------------------------------
# Atlases
# ---------------------------------------------------------------------------
WB_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\window_backs.json"))["cells"]
GI_CELLS = json.load(open(PROJECT + r"\assets\textures\block-35-41\grocery_interior.json"))["cells"]
# signs_atlas.jpg boxes (pixels from the top-left; tools/prepare_block_35_41_textures.py REGIONS)
REGIONS = {"stripes": (0, 0, 768, 384), "louvre": (768, 0, 1024, 640), "val_s": (0, 384, 768, 512),
           "val_n": (0, 512, 768, 640), "canvas": (0, 640, 768, 1024), "green": (768, 640, 1024, 832),
           "spare": (768, 832, 1024, 1024)}

# Flats over a grocery and a cobbler's: blinds at different heights, lace, a few curtains, dark rooms.
UPPER_WEIGHTS = {"blind_cream_high": 3, "blind_cream_half": 3, "blind_cream_low": 2, "blind_green_high": 2,
                 "blind_green_half": 2, "lace": 3, "lace_blind_cream": 3, "lace_full_blind_cream": 2,
                 "curtains_beige": 2, "curtains_olive": 1, "curtains_maroon_blind": 1, "dark_room": 1,
                 "dark_room_frame": 1}
_wb_rng = random.Random(1921)
_wb_grid = {}


def pick_cell(weights, wall, row, colm):
    avoid = {_wb_grid.get((wall, row), {}).get(colm - 1), _wb_grid.get((wall, row - 1), {}).get(colm),
             _wb_grid.get((wall, row), {}).get(colm + 1)}
    names = [n for n in weights if n not in avoid]
    cell = _wb_rng.choices(names, weights=[weights[n] for n in names])[0]
    _wb_grid.setdefault((wall, row), {})[colm] = cell
    return cell


def region_uv(region, fu, fv, inset=2):
    """fu left -> right, fv top -> bottom of a signs-atlas region, as (u, v) in Blender UV space."""
    c0, r0, c1, r1 = REGIONS[region]
    col_ = c0 + inset + (c1 - c0 - 2 * inset) * min(max(fu, 0.0), 1.0)
    row = r0 + inset + (r1 - r0 - 2 * inset) * min(max(fv, 0.0), 1.0)
    return (col_ / 1024, 1 - row / 1024)


# ---------------------------------------------------------------------------
# Mesh builder
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

    def u_of(self, co):
        return (co[0] - self.p0[0]) * self.t[0] + (co[1] - self.p0[1]) * self.t[1]


class MB:
    """Collects closed solids (and a few single faces) for one builder."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uvl = self.bm.loops.layers.uv.new("UVMap")

    def _extrude(self, a_co, b_co, caps=True, recalc=True):
        bm = self.bm
        a = [bm.verts.new(c) for c in a_co]
        b = [bm.verts.new(c) for c in b_co]
        faces = [bm.faces.new(a), bm.faces.new(list(reversed(b)))] if caps else []
        n = len(a)
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
        if recalc:
            bmesh.ops.recalc_face_normals(bm, faces=faces)
        return faces

    @staticmethod
    def _pt(axis, u, d, v):
        if axis == "y":
            return (u, d, v)
        if axis == "x":
            return (d, u, v)
        return (u, v, d)

    def prism(self, pts, d0, d1, axis="y"):
        """Extrude a 2D outline between depths d0 and d1 along an axis ('y': outline in X-Z;
        'x': outline in Y-Z; 'z': plan outline in X-Y)."""
        return self._extrude([self._pt(axis, u, d0, v) for u, v in pts], [self._pt(axis, u, d1, v) for u, v in pts])

    def box(self, x0, x1, y0, y1, z0, z1):
        return self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)

    def wprism(self, wall, pts, d0, d1):
        return self._extrude([wall.pt(u, z, d0) for u, z in pts], [wall.pt(u, z, d1) for u, z in pts])

    def wbox(self, wall, u0, u1, z0, z1, d0, d1):
        return self.wprism(wall, rect(u0, u1, z0, z1), d0, d1)

    def face(self, cos, want):
        f = self.bm.faces.new([self.bm.verts.new(c) for c in cos])
        f.normal_update()
        if f.normal.dot(Vector(want)) < 0:
            f.normal_flip()
        return [f]

    def wface(self, wall, pts, d):
        """One flat face in a wall plane (glass, window back), facing out of the wall."""
        return self.face([wall.pt(u, z, d) for u, z in pts], (wall.n[0], wall.n[1], 0))

    def lathe(self, cx, cy, rings, sides=8, rot=0.5, caps=True):
        """Vertical solid of revolution: rings [(radius, z), ...] bottom to top."""
        bm = self.bm
        loops = [[bm.verts.new((cx + r * math.cos(2 * math.pi * (i + rot) / sides),
                                cy + r * math.sin(2 * math.pi * (i + rot) / sides), z)) for i in range(sides)]
                 for r, z in rings]
        faces = [bm.faces.new(list(reversed(loops[0]))), bm.faces.new(loops[-1])] if caps else []
        for a, b in zip(loops, loops[1:]):
            for i in range(sides):
                j = (i + 1) % sides
                faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
        if caps:
            bmesh.ops.recalc_face_normals(bm, faces=faces)
        return faces

    def tube(self, p0, p1, r, sides=6):
        """Round bar between two points (pipes, rails, iron arms)."""
        a, b = Vector(p0), Vector(p1)
        ax = (b - a).normalized()
        ref = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
        e1 = ax.cross(ref).normalized()
        e2 = ax.cross(e1)
        ring = [e1 * math.cos(2 * math.pi * (i + 0.5) / sides) * r + e2 * math.sin(2 * math.pi * (i + 0.5) / sides) * r
                for i in range(sides)]
        return self._extrude([tuple(a + v) for v in ring], [tuple(b + v) for v in ring])

    def solid(self, cos, faces_idx):
        vs = [self.bm.verts.new(c) for c in cos]
        faces = [self.bm.faces.new([vs[i] for i in f]) for f in faces_idx]
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        return faces

    def set_uv(self, faces, fn):
        """fn(co, normal) -> (u, v) for every corner of the faces."""
        for f in faces:
            f.normal_update()
            for loop in f.loops:
                loop[self.uvl].uv = fn(loop.vert.co, f.normal)

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


col = fresh_collection("Block3541")
G = {k: MB() for k in BUILDER_MAT}
CL, T, ST, BR, CH, R, WD, IR, SG, PV, GL, WB, GR = (
    G[k] for k in ("Clap", "Trim", "Steps", "Brick", "Chimney", "Roof", "Wood", "Iron", "Signs", "Paving",
                   "Glass", "WindowBack", "Grocery"))
# wall shells (closed solids) and their cutters: name -> (shell, cutter, material)
SHELLS = {k: (MB(), MB(), m) for k, m in (("ShellA", "Clapboard"), ("ShellC", "Clapboard"),
                                          ("ShellD", "Clapboard"), ("ShellE", "Brick"), ("ShellF", "Brick"))}
SA, SC, SD, SE, SF = (SHELLS[k][0] for k in SHELLS)
KA, KC, KD, KE, KF = (SHELLS[k][1] for k in SHELLS)

FRONT_A = Wall((0.0, AY0), (0, -1), KA)        # u = X (north to the right)
FRONT_E = Wall((0.0, EY0), (0, -1), KE)
REAR_C = Wall((0.0, CY1), (0, 1), KC)          # u = -X
REAR_F = Wall((0.0, FY2), (0, 1), KF)


def uv_window_back(builder, faces, wall, u0, u1, z0, z1, cell_uv):
    U0, V0, U1, V1 = cell_uv
    builder.set_uv(faces, lambda co, n: (U0 + (U1 - U0) * (wall.u_of(co) - u0) / (u1 - u0),
                                         V0 + (V1 - V0) * (co[2] - z0) / (z1 - z0)))


def pane(wall, u0, u1, z0, z1, d_glass, cell, grocery=False):
    """Glass face at d_glass and its window back 4 cm behind, UV'd onto `cell`."""
    GL.wface(wall, rect(u0, u1, z0, z1), d_glass)
    if grocery:
        x0, x1, gz0, gz1, yb = GI_CELLS[cell]["plane"]
        uv_window_back(GR, GR.wface(wall, rect(x0, x1, gz0, gz1), -(yb - wall.p0[1])), wall, x0, x1, gz0, gz1,
                       GI_CELLS[cell]["uv"])
    else:
        uv_window_back(WB, WB.wface(wall, rect(u0, u1, z0, z1), d_glass - 0.04), wall, u0, u1, z0, z1,
                       WB_CELLS[cell]["uv"])


def shutter_leaf(wall, u0, u1, z0, z1, d0, d1):
    """Louvred shutter leaf (signs atlas `louvre` on the face, plain green on the edges)."""
    faces = SG.wbox(wall, u0, u1, z0, z1, d0, d1)
    nx, ny = wall.n

    def fn(co, n):
        if n.x * nx + n.y * ny > 0.9:
            return region_uv("louvre", (wall.u_of(co) - u0) / (u1 - u0), (z1 - co[2]) / (z1 - z0))
        return region_uv("green", 0.5, 0.5)
    SG.set_uv(faces, fn)


def sash_window(wall, cu, z0, w, h, cell, row, colm, wname, shut=0.0, head=False, casing=True, stone=False):
    """2/2 sash window in a 0.16 recess: window back, glass, sash rails and muntin, plain casing
    (frame walls) or stone sill and lintel (brick), optional open louvred shutters."""
    hw, z1 = w / 2, z0 + h
    wall.cut.wbox(wall, cu - hw, cu + hw, z0, z1, -0.16, 0.25)
    cell = cell or pick_cell(UPPER_WEIGHTS, wname, row, colm)
    pane(wall, cu - hw, cu + hw, z0, z1, -0.10, cell)
    zm = (z0 + z1) / 2 + 0.03
    T.wbox(wall, cu - hw, cu - hw + 0.05, z0, z1, -0.09, -0.04)                  # sash stiles
    T.wbox(wall, cu + hw - 0.05, cu + hw, z0, z1, -0.09, -0.04)
    T.wbox(wall, cu - hw + 0.05, cu + hw - 0.05, z1 - 0.05, z1, -0.09, -0.04)    # top rail
    T.wbox(wall, cu - hw + 0.05, cu + hw - 0.05, z0, z0 + 0.07, -0.09, -0.04)    # bottom rail
    T.wbox(wall, cu - hw + 0.05, cu + hw - 0.05, zm - 0.03, zm + 0.03, -0.09, -0.03)   # meeting rail
    T.wbox(wall, cu - 0.017, cu + 0.017, z0 + 0.07, z1 - 0.05, -0.09, -0.05)      # muntin (2/2)
    if casing and head:                       # side casings and a plain projecting head 0.06 thick
        T.wbox(wall, cu - hw - 0.10, cu - hw, z0, z1, 0.0, 0.03)
        T.wbox(wall, cu + hw, cu + hw + 0.10, z0, z1, 0.0, 0.03)
        T.wbox(wall, cu - hw - 0.15, cu + hw + 0.15, z1, z1 + 0.06, -0.01, 0.09)
    elif casing:                                                                 # plain casing 0.10
        T.wprism(wall, [(cu - hw - 0.10, z0), (cu - hw, z0), (cu - hw, z1), (cu + hw, z1), (cu + hw, z0),
                        (cu + hw + 0.10, z0), (cu + hw + 0.10, z1 + 0.10), (cu - hw - 0.10, z1 + 0.10)], 0.0, 0.03)
    if casing:
        T.wbox(wall, cu - hw - 0.14, cu + hw + 0.14, z0 - 0.06, z0, -0.10, 0.06)   # sill
    if stone:
        T.wbox(wall, cu - hw - 0.08, cu + hw + 0.08, z0 - 0.08, z0, -0.16, 0.06)   # stone sill
        T.wbox(wall, cu - hw - 0.10, cu + hw + 0.10, z1, z1 + 0.18, -0.02, 0.02)   # stone lintel
    if shut:
        off = 0.11 if casing else 0.03
        for s in (-1, 1):
            a, b = sorted((cu + s * (hw + off), cu + s * (hw + off + shut)))
            shutter_leaf(wall, a, b, z0, z1, 0.03 if casing else 0.0, 0.06 if casing else 0.03)


# ---------------------------------------------------------------------------
# A. 35-37 main block: shell, front openings, eave, roof, chimney
# ---------------------------------------------------------------------------
SA.box(AX0, AX1, AY0, AY1, SKIRT, SOFFIT)

# 2nd floor: three 2/2 windows with open shutters; 3rd floor: three smaller ones with heads
for k, x in enumerate(WIN_X):
    sash_window(FRONT_A, x, 4.25, 0.90, 1.65, None, 1, k, "a", shut=0.45)
    sash_window(FRONT_A, x, 6.95, 0.75, 1.05, None, 2, k, "a", shut=0.375, head=True)

# ground floor: south window with closed louvred shutters
gx0, gx1, gz0, gz1 = 0.15, 1.15, 1.05, 2.75
KA.box(gx0, gx1, AY0 - 0.25, AY0 + 0.10, gz0, gz1)
for a, b in ((gx0, (gx0 + gx1) / 2), ((gx0 + gx1) / 2, gx1)):
    shutter_leaf(FRONT_A, a + 0.004, b - 0.004, gz0, gz1, -0.07, -0.04)
T.wprism(FRONT_A, [(gx0 - 0.10, gz0), (gx0, gz0), (gx0, gz1), (gx1, gz1), (gx1, gz0), (gx1 + 0.10, gz0),
                   (gx1 + 0.10, gz1 + 0.10), (gx0 - 0.10, gz1 + 0.10)], 0.0, 0.03)
T.wbox(FRONT_A, gx0 - 0.14, gx1 + 0.14, gz0 - 0.06, gz0, -0.10, 0.06)

# ground floor: single four-panel door, glazed upper half, dark
dx0, dx1, dz1 = 2.30, 3.20, 2.85
KA.box(dx0, dx1, AY0 - 0.25, AY0 + 0.30, DECK, dz1)
gl = GI_CELLS["door"]["plane"]                       # glass X 2.42 ... 3.08, Z 1.70 ... 2.68
WD.box(dx0, dx1, AY0 + 0.08, AY0 + 0.13, DECK, gl[2])                         # lower leaf
WD.box(dx0, gl[0], AY0 + 0.08, AY0 + 0.13, gl[2], dz1)                        # stiles beside the glass
WD.box(gl[1], dx1, AY0 + 0.08, AY0 + 0.13, gl[2], dz1)
WD.box(gl[0], gl[1], AY0 + 0.08, AY0 + 0.13, gl[3], dz1)                      # top rail
for a, b in ((dx0 + 0.12, (dx0 + dx1) / 2 - 0.05), ((dx0 + dx1) / 2 + 0.05, dx1 - 0.12)):
    WD.box(a, b, AY0 + 0.065, AY0 + 0.08, DECK + 0.18, gl[2] - 0.14)          # two raised panels
pane(FRONT_A, gl[0], gl[1], gl[2], gl[3], -0.115, "door", grocery=True)
T.box(gl[0] - 0.02, gl[1] + 0.02, AY0 + 0.06, AY0 + 0.08, gl[2] - 0.03, gl[2])   # glazing bead / ledge
T.wprism(FRONT_A, [(dx0 - 0.10, DECK), (dx0, DECK), (dx0, dz1), (dx1, dz1), (dx1, DECK), (dx1 + 0.10, DECK),
                   (dx1 + 0.10, dz1 + 0.12), (dx0 - 0.10, dz1 + 0.12)], 0.0, 0.03)
T.wbox(FRONT_A, dx0 - 0.16, dx1 + 0.16, dz1 + 0.12, dz1 + 0.18, -0.01, 0.07)     # door head
IR.box(dx1 - 0.13, dx1 - 0.10, AY0 + 0.05, AY0 + 0.08, 1.38, 1.44)              # knob

# ground floor: large shop window on a panelled bulkhead, dark wood frame
sx0, sx1, sz0, sz1 = 3.95, 5.60, 1.05, 2.85
sg = GI_CELLS["shop"]["plane"]                       # glass X 4.03 ... 5.52, Z 1.11 ... 2.79
KA.box(sx0, sx1, AY0 - 0.25, AY0 + 0.08, DECK, sz1)
KA.box(sg[0], sg[1], AY0, AY0 + 0.30, sg[2], sg[3])
pane(FRONT_A, sg[0], sg[1], sg[2], sg[3], -0.08, "shop", grocery=True)
WD.box(sx0, sx1, AY0 + 0.02, AY0 + 0.08, DECK, sz0)                           # bulkhead
for a, b in ((sx0 + 0.10, (sx0 + sx1) / 2 - 0.05), ((sx0 + sx1) / 2 + 0.05, sx1 - 0.10)):
    WD.box(a, b, AY0 + 0.005, AY0 + 0.02, DECK + 0.12, sz0 - 0.12)            # raised panels
WD.box(sx0, sx1, AY0 + 0.0, AY0 + 0.08, sz0, sg[2])                           # sill rail
WD.box(sx0, sx1, AY0 + 0.01, AY0 + 0.08, sg[3], sz1)                          # head rail
WD.box(sx0, sg[0], AY0 + 0.01, AY0 + 0.08, sg[2], sg[3])                      # jambs
WD.box(sg[1], sx1, AY0 + 0.01, AY0 + 0.08, sg[2], sg[3])
WD.box(sx0 - 0.06, sx1 + 0.06, AY0 - 0.03, AY0 + 0.01, sz0 - 0.04, sz0 + 0.02)   # ledge
T.wprism(FRONT_A, [(sx0 - 0.10, DECK), (sx0, DECK), (sx0, sz1), (sx1, sz1), (sx1, DECK), (sx1 + 0.10, DECK),
                   (sx1 + 0.10, sz1 + 0.12), (sx0 - 0.10, sz1 + 0.12)], 0.0, 0.03)
T.wbox(FRONT_A, sx0 - 0.16, sx1 + 0.16, sz1 + 0.12, sz1 + 0.18, -0.01, 0.07)

# corner boards (front and both sides) and the frieze board
for x0 in (AX0, AX1 - 0.15):
    T.box(x0, x0 + 0.15, AY0 - 0.03, AY0, SKIRT + 0.2, FRIEZE0)
T.box(AX0 - 0.03, AX0, AY0 - 0.03, AY0 + 0.15, SKIRT + 0.2, FRIEZE0)
T.box(AX1, AX1 + 0.03, AY0 - 0.03, AY0 + 0.15, SKIRT + 0.2, FRIEZE0)
T.box(AX0 - 0.03, AX0, AY1 - 0.15, AY1, C_TOP, FRIEZE0)
T.box(AX1, AX1 + 0.03, AY1 - 0.15, AY1, SKIRT + 0.2, FRIEZE0)
T.box(AX0 - 0.04, AX1 + 0.04, AY0 - 0.04, AY0, FRIEZE0, SOFFIT)                  # frieze board
T.box(AX0 - 0.04, AX0, AY0, AY1, FRIEZE0, SOFFIT)
T.box(AX1, AX1 + 0.04, AY0, AY1, FRIEZE0, SOFFIT)

# boxed eave: 0.45 at the front (with 0.5 m returns), 0.15 at the sides and rear
T.box(AX0 - 0.15, AX1 + 0.15, AY0 - 0.45, AY1 + 0.15, SOFFIT, EAVE)
T.box(AX0 - 0.30, AX1 + 0.30, AY0 - 0.45, AY0 + 0.50, SOFFIT, EAVE)
# five scroll brackets under the soffit
BRACKET = [(0.0, SOFFIT), (-0.40, SOFFIT), (-0.40, SOFFIT - 0.05), (-0.33, SOFFIT - 0.07), (-0.25, SOFFIT - 0.12),
           (-0.18, SOFFIT - 0.15), (-0.12, SOFFIT - 0.20), (-0.09, SOFFIT - 0.25), (-0.06, SOFFIT - 0.30),
           (0.0, SOFFIT - 0.30)]
for x in (-0.30, 1.25, 2.73, 4.21, 5.76):
    T.prism([(AY0 + y, z) for y, z in BRACKET], x - 0.09, x + 0.09, axis="x")
# low hip roof (tin), ridge along Y
ex0, ex1, ey0, ey1 = AX0 - 0.15, AX1 + 0.15, AY0 - 0.45, AY1 + 0.15
R.solid([(ex0, ey0, EAVE), (ex1, ey0, EAVE), (ex1, ey1, EAVE), (ex0, ey1, EAVE),
         (RIDGE_X, RIDGE_Y0, RIDGE_Z), (RIDGE_X, RIDGE_Y1, RIDGE_Z)],
        [[0, 3, 2, 1], [0, 1, 4], [1, 2, 5, 4], [2, 3, 5], [3, 0, 4, 5]])
# brick chimney near the north wall (1920s card)
CH.box(5.20 - 0.275, 5.20 + 0.275, 7.00 - 0.275, 7.00 + 0.275, 8.45, 10.30)
CH.box(5.20 - 0.33, 5.20 + 0.33, 7.00 - 0.33, 7.00 + 0.33, 10.30, 10.40)

# ---------------------------------------------------------------------------
# B. The two-tier porch
# ---------------------------------------------------------------------------
# raised floor with a board fascia, two steps along the whole front
T.box(AX0, AX1, 0.0, AY0, SKIRT, DECK)
ST.box(AX0, AX1, -0.60, -0.30, -0.02, 0.15)
ST.box(AX0, AX1, -0.30, 0.0, -0.02, 0.30)

# round Tuscan columns, both tiers: square plinth, torus base, tapering shaft, capital, abacus


def tuscan(x, z0, z1):
    h = z1 - z0
    T.box(x - 0.14, x + 0.14, COL_Y - 0.14, COL_Y + 0.14, z0, z0 + 0.08)                     # plinth
    T.lathe(x, COL_Y, [(0.135, z0 + 0.08), (0.14, z0 + 0.11), (0.12, z0 + 0.15), (0.11, z0 + 0.17),
                       (0.095, z1 - 0.20), (0.10, z1 - 0.18), (0.10, z1 - 0.14), (0.13, z1 - 0.08)],
            sides=10, rot=0.5, caps=False)
    T.box(x - 0.14, x + 0.14, COL_Y - 0.14, COL_Y + 0.14, z1 - 0.08, z1)                     # abacus


for x in COL_X:
    tuscan(x, DECK, BEAM0)
    tuscan(x, BEAM1, TOP0)

# beam and plain fascia between the tiers, upper deck with the stair opening
T.box(AX0 - 0.08, AX1 + 0.08, -0.08, 0.28, BEAM0, BEAM1)
for x0, x1, y0, y1 in ((AX0, AX1, 0.28, STAIR_Y1), (AX0, UP_X0, STAIR_Y1, AY0), (UP_X1, AX1, STAIR_Y1, AY0)):
    T.box(x0, x1, y0, y1, 3.40, BEAM1)
T.box(AX0 - 0.03, AX0, 0.28, AY0, 3.40, BEAM1)                     # end boards
T.box(AX1, AX1 + 0.03, 0.28, AY0, 3.40, BEAM1)


def bays(a0, a1, pitch, gap=0.02):
    """Centres at `pitch` (about) between a0 and a1."""
    n = max(1, int(round((a1 - a0 - 2 * gap) / pitch)))
    step = (a1 - a0 - 2 * gap) / n
    return [a0 + gap + (k + 0.5) * step for k in range(n)]


BAL = [(0.026, 0.0), (0.040, 0.24), (0.020, 0.60), (0.026, 0.73)]          # turned baluster (belly low)
SPN = [(0.014, 0.0), (0.024, 0.15), (0.014, 0.30)]                          # turned spindle
rail_spans = [(COL_X[i] + 0.11, COL_X[i + 1] - 0.11) for i in range(3)]
# upper-deck rail: bottom rail, turned balusters at 0.12, flat top rail 0.10 x 0.06 (front)
for a, b in rail_spans:
    T.box(a, b, 0.10, 0.18, BEAM1, BEAM1 + 0.06)
    T.box(a, b, 0.09, 0.19, 4.49, 4.55)
    for x in bays(a, b, 0.12):
        T.lathe(x, COL_Y, [(r, BEAM1 + 0.06 + z) for r, z in BAL], sides=6, rot=0.0, caps=False)
# north return (Y 0.28 ... 1.98); the south end stays open for the stair
RX = COL_X[3]
T.box(RX - 0.04, RX + 0.04, 0.28, AY0, BEAM1, BEAM1 + 0.06)
T.box(RX - 0.05, RX + 0.05, 0.28, AY0, 4.49, 4.55)
for y in bays(0.28, AY0, 0.12):
    T.lathe(RX, y, [(r, BEAM1 + 0.06 + z) for r, z in BAL], sides=6, rot=0.0, caps=False)
# tall close bars above the rail (1920s card), on a thin head rail, just behind the front line
for a, b in rail_spans:
    T.box(a, b, 0.19, 0.26, 5.80, 5.86)
    for x in bays(a, b, 0.12):
        T.box(x - 0.025, x + 0.025, 0.20, 0.25, 4.60, 5.80)
# spindle frieze (rails 0.05, turned spindles at 0.09) and the cut-out drop fringe under it


def fringe(a, b, y):
    """Flat board Z 5.75 ... 5.90 with a pendant lower edge, 0.15 period; front and back faces."""
    n = max(1, int(round((b - a) / 0.15)))
    p = (b - a) / n
    edge = []
    for k in range(n):
        x = a + k * p
        edge += [(x, 5.84), (x + 0.27 * p, 5.77), (x + 0.5 * p, 5.75), (x + 0.73 * p, 5.77)]
    edge.append((b, 5.84))
    outline = [(b, 5.90), (a, 5.90)] + edge
    T.face([(x, y, z) for x, z in outline], (0, -1, 0))
    T.face([(x, y + 0.015, z) for x, z in outline], (0, 1, 0))


for a, b in rail_spans:
    T.box(a, b, 0.10, 0.18, 5.90, 5.95)
    T.box(a, b, 0.10, 0.18, 6.25, TOP0)
    for x in bays(a, b, 0.09):
        T.lathe(x, COL_Y, [(r, 5.95 + z) for r, z in SPN], sides=4, rot=0.0, caps=False)
    fringe(a, b, 0.095)
# top beam, porch ceiling and shed roof (tin) from 6.85 at the wall to 6.45 at the front
T.box(AX0 - 0.08, AX1 + 0.08, -0.02, 0.28, TOP0, TOP1)
slope = (ROOF_WALL - ROOF_FRONT) / AY0
T.prism([(-0.15, 6.40), (AY0, 6.40), (AY0, ROOF_WALL), (-0.15, ROOF_FRONT - 0.15 * slope)],
        AX0 - 0.15, AX1 + 0.15, axis="x")
R.prism([(-0.17, ROOF_FRONT - 0.17 * slope + 0.005), (AY0, ROOF_WALL + 0.005), (AY0, ROOF_WALL + 0.035),
         (-0.17, ROOF_FRONT - 0.17 * slope + 0.035)], AX0 - 0.17, AX1 + 0.17, axis="x")

# --- B2: the stair in the south bay ----------------------------------------------
n_lo = 8
r_lo = (2.05 - DECK) / n_lo
t_lo = (STAIR_Y1 - STAIR_Y0) / (n_lo - 1)
for k in range(n_lo - 1):                                       # 7 treads, then the landing
    T.box(-0.43, 0.43, STAIR_Y0 + k * t_lo, STAIR_Y1, DECK + k * r_lo, DECK + (k + 1) * r_lo)
for x0 in (-0.47, 0.43):                                        # closed stringers, boarded solid
    T.prism([(STAIR_Y0 - 0.02, DECK), (STAIR_Y1, DECK), (STAIR_Y1, 2.05 + 0.12), (STAIR_Y0 - 0.02, DECK + 0.32)],
             x0, x0 + 0.04, axis="x")
    xc = x0 + 0.02
    T.box(xc - 0.05, xc + 0.05, STAIR_Y0 - 0.12, STAIR_Y0 - 0.02, DECK, 1.45)          # newels
    T.box(xc - 0.05, xc + 0.05, STAIR_Y1 - 0.10, STAIR_Y1, 2.05, 2.95)
    T.tube((xc, STAIR_Y0 - 0.07, 1.43), (xc, STAIR_Y1 - 0.05, 2.90), 0.025)             # handrails
# landing (guess) on two posts
T.box(-0.47, UP_X0, STAIR_Y1, AY0, 1.95, 2.05)
T.box(UP_X0 - 0.08, UP_X0, STAIR_Y1, STAIR_Y1 + 0.08, DECK, 1.95)
# upper flight (guess) along the wall, rising north to the deck
n_up = 8
r_up = (BEAM1 - 2.05) / n_up
t_up = (UP_X1 - UP_X0) / n_up
for k in range(n_up):
    T.box(UP_X0 + k * t_up, UP_X1, STAIR_Y1 + 0.04, AY0, 2.05 + k * r_up, 2.05 + (k + 1) * r_up)
T.prism([(UP_X0, 1.95), (UP_X1, BEAM1 - 0.25), (UP_X1, BEAM1 + 0.10), (UP_X0, 2.05 + 0.30)],
         STAIR_Y1, STAIR_Y1 + 0.04, axis="y")                    # outer stringer
T.box(UP_X1 - 0.08, UP_X1, STAIR_Y1 - 0.04, STAIR_Y1 + 0.04, BEAM1, 4.55)               # post at the top
T.tube((UP_X0 + 0.05, STAIR_Y1 + 0.02, 2.05 + 0.90), (UP_X1 - 0.08, STAIR_Y1 + 0.02, BEAM1 + 0.85), 0.025)
T.box(UP_X0, UP_X0 + 0.08, STAIR_Y1, STAIR_Y1 + 0.08, 1.95, 2.95)                       # post at the landing

# --- awning: striped canvas from under the beam, lettered scalloped valance ----------
AW_X0, AW_X1 = AX0, AX1
W_AW = AW_X1 - AW_X0
can = SG.prism([(-0.06, AW_Z0), (AW_Y, AW_Z1), (AW_Y, AW_Z1 - 0.02), (-0.06, AW_Z0 - 0.02)], AW_X0, AW_X1, axis="x")
L_AW = math.hypot(AW_Y + 0.06, AW_Z0 - AW_Z1)


def aw_uv(co, n):
    if abs(n.x) > 0.9:                                          # cheeks: plain canvas
        return region_uv("canvas", 0.5, 0.5)
    s = math.hypot(co[1] + 0.06, co[2] - AW_Z0 + (0.0 if n.z > 0 else 0.02)) / L_AW
    return region_uv("stripes", (co[0] - AW_X0) / W_AW, s)


SG.set_uv(can, aw_uv)
XM = (AW_X0 + AW_X1) / 2                                        # valance halves meet at X 2.73
for name, a, b in (("val_s", AW_X0, XM), ("val_n", XM, AW_X1)):
    edge = [(a, 2.27)]
    for k in range(int(W_AW / 0.15) + 1):                       # scallop points at AW_X0 + k * 0.15
        x = AW_X0 + k * 0.15
        for px, pz in ((x, 2.285), (x + 0.04, 2.262), (x + 0.075, VAL_BOT), (x + 0.11, 2.262)):
            if a + 0.005 < px < b - 0.005:
                edge.append((px, pz))
    edge.append((b, 2.27))
    outline = [(b, AW_Z1), (a, AW_Z1)] + edge
    front = SG.face([(x, AW_Y - 0.012, z) for x, z in outline], (0, -1, 0))
    SG.set_uv(front, lambda co, n, a=a, b=b, name=name: region_uv(name, (co[0] - a) / (b - a),
                                                                  (AW_Z1 - co[2]) / (AW_Z1 - VAL_BOT), inset=1))
    back = SG.face([(x, AW_Y - 0.004, z) for x, z in outline], (0, 1, 0))
    SG.set_uv(back, lambda co, n: region_uv("canvas", 0.3, 0.3))
IR.box(AW_X0, AW_X1, AW_Y - 0.002, AW_Y + 0.025, AW_Z1 - 0.04, AW_Z1)                   # front bar
IR.box(AW_X0, AW_X1, -0.11, -0.02, AW_Z0 - 0.06, BEAM0)                                  # roller box
for x in (COL_X[0] + 0.16, COL_X[3] - 0.16):                                              # two iron arms
    IR.tube((x, -0.02, 2.05), (x, AW_Y + 0.02, AW_Z1 - 0.02), 0.013)

# ---------------------------------------------------------------------------
# C. Frame rear wing, D. north shed
# ---------------------------------------------------------------------------
SC.box(AX0, CX1, AY1, CY1, SKIRT, C_TOP - 0.15)
R.box(AX0 - 0.10, CX1 + 0.10, AY1, CY1 + 0.12, C_TOP - 0.15, C_TOP)
T.box(AX0 - 0.10, CX1 + 0.10, CY1 + 0.12, CY1 + 0.15, C_TOP - 0.25, C_TOP)               # rear fascia


def plain_door(wall, cu, w, z0, z1):
    """Plain four-panel door in a 0.20 recess, plain casing, wooden step."""
    hw = w / 2
    wall.cut.wbox(wall, cu - hw, cu + hw, z0, z1, -0.20, 0.25)
    WD.wbox(wall, cu - hw, cu + hw, z0, z1, -0.20, -0.14)
    for ua, ub in ((cu - hw + 0.12, cu - 0.04), (cu + 0.04, cu + hw - 0.12)):
        for za, zb in ((z0 + 0.18, z0 + (z1 - z0) * 0.45), (z0 + (z1 - z0) * 0.52, z1 - 0.14)):
            WD.wbox(wall, ua, ub, za, zb, -0.14, -0.125)
    T.wprism(wall, [(cu - hw - 0.10, z0), (cu - hw, z0), (cu - hw, z1), (cu + hw, z1), (cu + hw, z0),
                    (cu + hw + 0.10, z0), (cu + hw + 0.10, z1 + 0.10), (cu - hw - 0.10, z1 + 0.10)], 0.0, 0.03)
    ST.wbox(wall, cu - hw - 0.10, cu + hw + 0.10, SKIRT, z0, -0.20, 0.35)


plain_door(REAR_C, -1.8, 0.90, 0.25, 2.30)
slope_d = 0.30 / (DY1 - AY1)
SD.prism([(AY1, SKIRT), (DY1, SKIRT), (DY1, D_TOP - 0.30), (AY1, D_TOP)], DX0, DX1, axis="x")
R.prism([(AY1, D_TOP), (DY1 + 0.12, D_TOP - 0.30 - 0.12 * slope_d), (DY1 + 0.12, D_TOP - 0.25 - 0.12 * slope_d),
         (AY1, D_TOP + 0.05)], DX0, DX1 + 0.10, axis="x")

# ---------------------------------------------------------------------------
# E. 39-41 brick: shell, parapet, balcony, windows, basement door and areaway
# ---------------------------------------------------------------------------
SE.box(EX0, EX1, EY0, EY1, -1.05, E_ROOF)
for x0, x1, y0, y1 in ((EX0, EX1, EY0, EY0 + 0.20), (EX0, EX0 + 0.20, EY0 + 0.20, EY1),
                       (EX1 - 0.20, EX1, EY0 + 0.20, EY1), (EX0 + 0.20, EX1 - 0.20, EY1 - 0.20, EY1)):
    BR.box(x0, x1, y0, y1, E_ROOF, E_TOP - 0.08)                 # plain parapet
T.box(EX0, EX1 + 0.04, EY0 - 0.04, EY0 + 0.24, E_TOP - 0.08, E_TOP)                      # flat coping
T.box(EX1 - 0.24, EX1 + 0.04, EY0 + 0.24, EY1, E_TOP - 0.08, E_TOP)
T.box(EX0, EX0 + 0.24, EY0 + 0.24, EY1, E_TOP - 0.08, E_TOP)
R.box(EX0 + 0.20, EX1 - 0.20, EY0 + 0.20, EY1 - 0.20, E_ROOF - 0.02, E_ROOF + 0.03)    # flat tin roof

# first floor: two tall windows / French doors onto the balcony, louvred shutters open (c. 1905)
FRENCH_CELLS = ("lace_full_blind_cream", "curtains_beige")
for k, x in enumerate(E_WIN_X):
    hw, z0, z1 = 0.475, 1.58, 3.68
    KE.wbox(FRONT_E, x - hw, x + hw, z0, z1, -0.20, 0.25)
    pane(FRONT_E, x - hw, x + hw, z0, z1, -0.12, FRENCH_CELLS[k])
    T.wbox(FRONT_E, x - hw, x - hw + 0.07, z0, z1, -0.11, -0.05)            # frame
    T.wbox(FRONT_E, x + hw - 0.07, x + hw, z0, z1, -0.11, -0.05)
    T.wbox(FRONT_E, x - hw + 0.07, x + hw - 0.07, z1 - 0.07, z1, -0.11, -0.05)
    T.wbox(FRONT_E, x - hw + 0.07, x + hw - 0.07, z0, z0 + 0.12, -0.11, -0.05)
    T.wbox(FRONT_E, x - 0.03, x + 0.03, z0 + 0.12, z1 - 0.07, -0.11, -0.04)   # meeting stiles
    for zz in (2.35, 3.00):                                                  # glazing bars
        T.wbox(FRONT_E, x - hw + 0.07, x + hw - 0.07, zz - 0.02, zz + 0.02, -0.11, -0.06)
    T.wbox(FRONT_E, x - hw - 0.06, x + hw + 0.06, z0 - 0.06, z0, -0.20, 0.04)  # stone threshold
    T.wbox(FRONT_E, x - hw - 0.10, x + hw + 0.10, z1, z1 + 0.18, -0.02, 0.02)  # stone lintel
    for s in (-1, 1):
        a, b = sorted((x + s * (hw + 0.03), x + s * (hw + 0.03 + 0.475)))
        shutter_leaf(FRONT_E, a, b, z0, z1, 0.0, 0.03)
# 2nd floor (guess): two 2/2 windows, stone sills and lintels, shutters open
for k, x in enumerate(E_WIN_X):
    sash_window(FRONT_E, x, 5.00, 0.95, 1.70, None, 1, k, "e", shut=0.475, casing=False, stone=True)

# balcony: floor at 1.50, flat sawn balusters, flat top rail, four plain brackets
BX0, BX1, BY0 = -5.80, -1.06, 1.46
T.box(BX0, BX1, BY0, EY0, 1.42, 1.50)
T.box(BX0, BX1, BY0, BY0 + 0.08, 1.50, 1.58)                     # bottom rail
T.box(BX0 - 0.02, BX1 + 0.02, BY0 - 0.01, BY0 + 0.09, 2.32, 2.40)  # top rail
SAWN = [(-0.05, 0.0), (0.05, 0.0), (0.05, 0.12), (0.022, 0.37), (0.05, 0.62), (0.05, 0.74),
        (-0.05, 0.74), (-0.05, 0.62), (-0.022, 0.37), (-0.05, 0.12)]
for x in bays(BX0 + 0.04, BX1 - 0.04, 0.14):
    T.prism([(x + u, 1.58 + z) for u, z in SAWN], BY0 + 0.03, BY0 + 0.05)
for x in (BX0, BX1):                                              # short return ends
    T.box(x - 0.02, x + 0.02, BY0, EY0, 1.50, 2.40)
    for y in bays(BY0 + 0.08, EY0, 0.14):
        T.prism([(y + u, 1.58 + z) for u, z in SAWN], x - 0.01, x + 0.01, axis="x")
BRK = [(EY0, 1.42), (BY0 + 0.02, 1.42), (BY0 + 0.02, 1.36), (EY0 - 0.25, 1.12), (EY0, 1.10)]
for x in (-5.62, -4.30, -1.62, -1.20):
    T.prism(BRK, x - 0.04, x + 0.04, axis="x")

# basement shop door (c. 1905), glazed upper half, blank board over it
bx0, bx1, bz0, bz1 = -3.00, -2.10, -0.95, 1.10
KE.wbox(FRONT_E, bx0, bx1, bz0, bz1, -0.18, 0.25)
bg_ = (-2.88, -2.22, 0.20, 0.98)
WD.box(bx0, bx1, EY0 + 0.10, EY0 + 0.15, bz0, bg_[2])
WD.box(bx0, bg_[0], EY0 + 0.10, EY0 + 0.15, bg_[2], bz1)
WD.box(bg_[1], bx1, EY0 + 0.10, EY0 + 0.15, bg_[2], bz1)
WD.box(bg_[0], bg_[1], EY0 + 0.10, EY0 + 0.15, bg_[3], bz1)
for za, zb in ((bz0 + 0.15, -0.30), (-0.20, bg_[2] - 0.12)):
    WD.box(bx0 + 0.12, bx1 - 0.12, EY0 + 0.085, EY0 + 0.10, za, zb)
pane(FRONT_E, bg_[0], bg_[1], bg_[2], bg_[3], -0.125, "door")
T.wbox(FRONT_E, bx0 - 0.06, bx1 + 0.06, bz1, bz1 + 0.05, -0.02, 0.03)    # head
board = SG.wbox(FRONT_E, -3.20, -1.90, 1.15, 1.40, 0.0, 0.03)
SG.set_uv(board, lambda co, n: region_uv("green", 0.3 + 0.4 * (co[0] + 3.2) / 1.3, 0.3 + 0.4 * (1.40 - co[2]) / 0.25))
# areaway: brick-lined well, five steps down to the door sill, iron pipe rails both sides
wx0, wx1, wy0, wy1 = WELL
BR.box(wx0 - 0.12, wx0, wy0 - 0.12, wy1, -1.05, -0.05)
BR.box(wx1, wx1 + 0.12, wy0 - 0.12, wy1, -1.05, -0.05)
BR.box(wx0, wx1, wy0 - 0.12, wy0, -1.05, -0.05)
for k in range(1, 6):                                            # concrete steps
    PV.box(wx0, wx1, wy0 + 0.22 * (k - 1), wy0 + 0.22 * k, -1.05, -0.19 * k)   # each step its own block
for x in (wx0 + 0.04, wx1 - 0.04):
    IR.tube((x, wy0 + 0.05, -0.02), (x, wy0 + 0.05, 0.90), 0.022)
    IR.tube((x, wy1 - 0.05, -0.02), (x, wy1 - 0.05, 0.90), 0.022)
    IR.tube((x, wy0 + 0.03, 0.90), (x, wy1 - 0.03, 0.90), 0.022)
    IR.tube((x, wy0 + 0.05, 0.45), (x, wy1 - 0.05, 0.45), 0.018)

# ---------------------------------------------------------------------------
# F. 1-storey brick rear with its notch
# ---------------------------------------------------------------------------
F_PLAN = [(EX0, EY1), (EX1, EY1), (EX1, FY2), (FX_NOTCH, FY2), (FX_NOTCH, FY1), (EX0, FY1)]
SF.prism(F_PLAN, SKIRT, F_TOP, axis="z")
R.prism([(EX0 - 0.05, EY1), (EX1 + 0.05, EY1), (EX1 + 0.05, FY2 + 0.05), (FX_NOTCH - 0.05, FY2 + 0.05),
         (FX_NOTCH - 0.05, FY1 + 0.05), (EX0 - 0.05, FY1 + 0.05)], F_TOP, F_TOP + 0.06, axis="z")
plain_door(REAR_F, 2.00, 0.90, 0.0, 2.10)

# ---------------------------------------------------------------------------
# Paving: front strip and the brick court, with the areaway opening
# ---------------------------------------------------------------------------
PV.box(EX0, AX1, -0.82, 0.0, SKIRT, 0.0)
for x0, x1, y0, y1 in ((EX0, wx0 - 0.12, 0.0, EY0), (wx1 + 0.12, AX0, 0.0, EY0), (wx0 - 0.12, wx1 + 0.12, 0.0, wy0 - 0.12)):
    PV.box(x0, x1, y0, y1, SKIRT, 0.0)
PV.box(wx0 - 0.12, wx0, wy0 - 0.12, EY0, -0.05, 0.0)             # stone kerb round the well
PV.box(wx1, wx1 + 0.12, wy0 - 0.12, EY0, -0.05, 0.0)
PV.box(wx0, wx1, wy0 - 0.12, wy0, -0.05, 0.0)

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
    cut_shell(shell, cutter, "BL_" + name, mat)
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("BL_" + key, MATS[BUILDER_MAT[key]], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Block 35-41 built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)")
# Materials, baked lighting and GLB export: run block_35_41_bake.py (it runs this file first).
