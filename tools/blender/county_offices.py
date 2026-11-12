"""
county_offices.py - builds the Hunterdon County Offices / Hall of Records (69-71 Main St,
Flemington, 1870-71, as it stood c. 1920) in Blender.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/county_offices.py").read())

Every run deletes and rebuilds the "CountyOffices" collection, so edit the numbers below
and run again. Materials, lightmap bake and GLB export: county_offices_bake.py (runs this
first). Pattern: courthouse.py.

Sources: PLAN.md "Hunterdon County Offices / Hall of Records" spec and its orchestrator
decisions (1921 Sanborn sheet 2; the 1905/1906/1908/1912 postcards): one 13.9 x 15.2 m
brick block, raised rough-stone basement, W-D-W-D-W-D-W front with three stone stoops,
paired upper centre window, bracketed cornice broken by a segmental roof arch with an
oculus, low hipped tin roof, no chimneys.

Coordinates (metres, Blender Z-up):
    X  across the front, +X = north, -X = south (towards the courthouse)
    Y  depth: y = 0 is the front (brick) wall face; the stoops run out to y = -2.4;
       the rear wall is at y = 15.21.
    Z  up from grade (lawn level).
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".

Windows (PLAN.md "E. Windows that don't read as flat black", rolled out here 2026-11-11, Rea /
County Hotel method): every pane is ONE outward glass face (builder Glass -> material `glass`,
transparent, see county_offices_bake.py) 4 cm in front of ONE window back (builder WBack, a
rectangle; the oculus a 12-gon) showing a cell of the shared atlas
assets/textures/shared/window_backs.jpg. Offices and record rooms: cream / green blinds at
varied heights, plain dark rooms; basement, door lights and fanlights: dark rooms. No window
repeats the cell of one within 4 m of it on the same wall. BACKREC[rid] tells the bake which
atlas rectangle each back shows. The door leaves are now really glazed (stiles and rails round
the light).
"""

import math
import json
import random
import bpy
import bmesh

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md)
# ---------------------------------------------------------------------------
HW = 6.95              # half width (13.9 m front)
BACK = 15.21           # rear wall face
FOUND = 1.20           # top of the stone basement = first floor
WALL_TOP = 8.25        # top of the brick frieze
SOFFIT = 8.40          # underside of the cornice corona
CORONA_TOP = 8.56
CORN_TOP = 8.62        # top of the cornice (spec 8.6)
OVER = 0.70            # cornice overhang, front and sides
OVER_REAR = 0.40
RIDGE = 10.80          # hip roof ridge
RECESS = 0.30          # openings are shallow recesses this deep (glass closes them)
REVEAL = 0.20          # glass / door plane behind the wall face
STRING_BOT, STRING_TOP = 4.83, 5.05
ARCH_X = 2.60          # the roof arch springs at x = +-2.6 ...
ARCH_TOP = 10.80       # ... and rises to here at x = 0
ARCH_R = (ARCH_X ** 2 + (ARCH_TOP - CORN_TOP) ** 2) / (2 * (ARCH_TOP - CORN_TOP))
ARCH_ZC = ARCH_TOP - ARCH_R
ARCH_A0 = math.acos(ARCH_X / ARCH_R)

GROUND_X = (-5.5, -2.1, 2.1, 5.5)          # front ground windows (and upper singles)
DOOR_X = (-3.8, 0.0, 3.8)
SIDE_BAYS = (2.0, 5.7, 9.4, 13.1)
SIDE_BRACKETS = (3.85, 7.55, 11.25)

# ---------------------------------------------------------------------------
# Materials (plain stand-ins; county_offices_bake.py swaps in the textures)
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


COLOURS = {
    "BrickFront": "#8e3f2c",   # red pressed brick, front
    "BrickSide": "#87452f",    # duller common brick, sides and rear
    "Stone": "#cdbfa2",        # pale buff sandstone: string course, sills, keystones, stoops
    "Trim": "#bdb4a0",         # light drab paint: cornice, brackets, frames, sash
    "Shutter": "#d9cfb4",      # cream shutters
    "Roof": "#5a3e34",         # painted tin
    "Door": "#3a2a1f",         # dark varnished doors
    "Rock": "#77706a",         # rough stone basement
    "Glass": "#1a1916",
    "WBack": "#2a2420",
    "Iron": "#1b1b1b",         # railings, grilles, knobs
}
MATS = {k: plain("CO_" + k, c) for k, c in COLOURS.items()}

# ---------------------------------------------------------------------------
# Mesh builder (as in courthouse.py, plus a Z axis and partial arcs)
# ---------------------------------------------------------------------------


class MB:
    """Collects geometry for one material. Shapes are added in place."""

    def __init__(self):
        self.bm = bmesh.new()
        self.rid_layer = self.bm.faces.layers.int.new("rid")
        self.rid = 0

    def face(self, pts, d, axis, out):
        """ONE single-sided face (outline [(u, v), ...] at depth d), facing `out` along the
        axis (+1 / -1). Used for glass panes and window backs."""
        f = self.bm.faces.new([self.bm.verts.new(self._pt(axis, u, d, v)) for u, v in pts])
        f.normal_update()
        k = {"y": 1, "x": 0, "z": 2}[axis]
        if f.normal[k] * out < 0:
            f.normal_flip()
        f[self.rid_layer] = self.rid
        return f

    def _closed(self, faces):
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)

    @staticmethod
    def _pt(axis, u, d, v):
        # axis 'y': outline in the X-Z plane, depth along Y (front/back faces)
        # axis 'x': outline in the Y-Z plane, depth along X (side faces)
        # axis 'z': outline in the X-Y plane (plan), depth along Z
        if axis == "y":
            return (u, d, v)
        if axis == "x":
            return (d, u, v)
        return (u, v, d)

    def prism(self, pts, d0, d1, axis="y", caps=True):
        """Extrude a 2D outline [(u, v), ...] between depths d0 and d1."""
        bm = self.bm
        a = [bm.verts.new(self._pt(axis, u, d0, v)) for u, v in pts]
        b = [bm.verts.new(self._pt(axis, u, d1, v)) for u, v in pts]
        faces = [bm.faces.new(a), bm.faces.new(list(reversed(b)))] if caps else []
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
        self._closed(faces)

    def box(self, x0, x1, y0, y1, z0, z1):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)

    def arc_band(self, cu, cv, r_in, r_out, a0, a1, d0, d1, axis="y", segs=8):
        """Curved band between radii r_in and r_out, angles a0..a1 (0 = +u, pi/2 = up)."""
        bm = self.bm
        ts = [a0 + (a1 - a0) * i / segs for i in range(segs + 1)]

        def ring(r, d):
            return [bm.verts.new(self._pt(axis, cu + r * math.cos(t), d, cv + r * math.sin(t))) for t in ts]
        of, inf, ob, ib = ring(r_out, d0), ring(r_in, d0), ring(r_out, d1), ring(r_in, d1)
        faces = []
        for i in range(segs):
            faces.append(bm.faces.new([of[i], of[i + 1], inf[i + 1], inf[i]]))
            faces.append(bm.faces.new([ob[i], ib[i], ib[i + 1], ob[i + 1]]))
            faces.append(bm.faces.new([of[i], ob[i], ob[i + 1], of[i + 1]]))
            faces.append(bm.faces.new([inf[i], inf[i + 1], ib[i + 1], ib[i]]))
        faces.append(bm.faces.new([of[0], inf[0], ib[0], ob[0]]))
        faces.append(bm.faces.new([of[-1], ob[-1], ib[-1], inf[-1]]))
        self._closed(faces)

    def ring(self, cu, cv, r_in, r_out, d0, d1, axis="y", segs=12):
        """Full circular ring (oculus surround)."""
        bm = self.bm
        ts = [2 * math.pi * i / segs for i in range(segs)]

        def loop(r, d):
            return [bm.verts.new(self._pt(axis, cu + r * math.cos(t), d, cv + r * math.sin(t))) for t in ts]
        of, inf, ob, ib = loop(r_out, d0), loop(r_in, d0), loop(r_out, d1), loop(r_in, d1)
        faces = []
        for i in range(segs):
            j = (i + 1) % segs
            faces.append(bm.faces.new([of[i], of[j], inf[j], inf[i]]))
            faces.append(bm.faces.new([ob[i], ib[i], ib[j], ob[j]]))
            faces.append(bm.faces.new([of[i], ob[i], ob[j], of[j]]))
            faces.append(bm.faces.new([inf[i], inf[j], ib[j], ib[i]]))
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


def arched(cu, w, z0, zs, segs=8):
    """Outline of a round-headed opening: straight sides from z0 up to zs, half-circle above."""
    r = w / 2
    return [(cu - r, z0), (cu + r, z0)] + [
        (cu + r * math.cos(math.pi * i / segs), zs + r * math.sin(math.pi * i / segs))
        for i in range(segs + 1)]


def circle(cu, cv, r, segs=12):
    return [(cu + r * math.cos(2 * math.pi * i / segs), cv + r * math.sin(2 * math.pi * i / segs)) for i in range(segs)]


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


col = fresh_collection("CountyOffices")
G = {k: MB() for k in MATS}      # geometry per material
WALLS, CUT = MB(), MB()          # brick shell (front + sides + rear), cut by CUT
FOUNDATION, CUT_F = MB(), MB()   # rough stone basement shell, cut by CUT_F

# Each wall: (axis, outer face depth, outward sign)
FRONT = ("y", 0.0, -1)
REAR = ("y", BACK, 1)
SOUTH = ("x", -HW, -1)
NORTH = ("x", HW, 1)


# ---------------------------------------------------------------------------
# Glass panes and window backs (PLAN.md section E)
# ---------------------------------------------------------------------------
PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
WB_CELLS = json.load(open(PROJECT + r"\assets\textures\shared\window_backs.json"))["cells"]
GAP = 0.04                      # window back this far behind the glass
# offices and record rooms (front, sides, upper floor): blinds at varied heights, dark rooms
OFFICE = {"blind_cream_high": 3, "blind_cream_half": 3, "blind_cream_low": 2, "blind_cream_full": 1,
          "blind_green_high": 2, "blind_green_half": 2, "blind_green_low": 1,
          "dark_room": 2, "dark_room_frame": 2}
# rear (back offices, stair): more dark rooms
BACKSIDE = {"blind_cream_high": 2, "blind_cream_half": 2, "blind_green_half": 1,
            "dark_room": 3, "dark_room_frame": 3}
DIM = {"dark_room": 1, "dark_room_frame": 1}          # basement, halls behind the doors
_wb_rng = random.Random(1871)
_wb_seen = {}
BACKREC = {}                    # rid -> record (read by county_offices_bake.py)


def pick(weights, wall, u, near=4.0):
    """A cell that differs from every window already placed within `near` metres along the
    same wall (beside it, or on the floor above / below)."""
    seen = _wb_seen.setdefault(wall, [])
    avoid = {c for uu, c in seen if abs(uu - u) < near}
    names = [n for n in weights if n not in avoid] or list(weights)
    cell = _wb_rng.choices(names, weights=[weights[n] for n in names])[0]
    seen.append((u, cell))
    return cell


def pane(wall, outline, k_glass, cell, grow=0.0, crop=None, back_outline=None):
    """Glass face (the pane's outline) k_glass from the wall face (negative = inside) and its
    window back GAP behind it: the outline's bounding box (or back_outline), `grow` larger all
    round where frames hide its edge; crop = (fu0, fu1, fv0, fv1) part of the atlas cell."""
    axis, face, out = wall
    D = lambda k: face + out * k
    G["Glass"].face(outline, D(k_glass), axis, out)
    us, vs = [p[0] for p in outline], [p[1] for p in outline]
    u0, u1, v0, v1 = min(us) - grow, max(us) + grow, min(vs) - grow, max(vs) + grow
    U0, V0, U1, V1 = WB_CELLS[cell]["uv"]
    if crop:
        U0, U1, V0, V1 = (U0 + (U1 - U0) * crop[0], U0 + (U1 - U0) * crop[1],
                          V0 + (V1 - V0) * crop[2], V0 + (V1 - V0) * crop[3])
    rid = len(BACKREC) + 1
    BACKREC[rid] = dict(axis=axis, u0=u0, u1=u1, z0=v0, z1=v1, uv=(U0, V0, U1, V1))
    G["WBack"].rid = rid
    G["WBack"].face(back_outline or rect(u0, u1, v0, v1), D(k_glass - GAP), axis, out)
    G["WBack"].rid = 0


def keystone(wall, cu, crown):
    axis, face, out = wall
    D = lambda k: face + out * k
    G["Stone"].prism([(cu - 0.075, crown - 0.06), (cu + 0.075, crown - 0.06), (cu + 0.11, crown + 0.20),
                      (cu - 0.11, crown + 0.20)], D(0.045), D(-0.01), axis)


def arched_window(wall, cu, w, z_sill, crown, shutters=False, key=True, sill=True, sill_w=None, segs=None,
                  cell="dark_room"):
    """Round-arched 2/2 double-hung window in a shallow recess: drab frame and sash, one
    glass face with a window back (atlas `cell`), pale stone sill and keystone, optional open
    cream shutters."""
    axis, face, out = wall
    D = lambda k: face + out * k        # k > 0 is outside the wall, k < 0 inside
    r = w / 2
    zs = crown - r
    segs = segs or (8 if wall is FRONT else 6)       # side and rear arches a little coarser
    CUT.prism(arched(cu, w, z_sill, zs, segs), D(0.25), D(-RECESS), axis)
    pane(wall, arched(cu, w, z_sill, zs, segs), -REVEAL - 0.005, cell)
    S = G["Trim"]
    f = 0.07                                                       # frame
    S.prism(rect(cu - r, cu - r + f, z_sill, zs), D(-0.09), D(-REVEAL), axis)
    S.prism(rect(cu + r - f, cu + r, z_sill, zs), D(-0.09), D(-REVEAL), axis)
    S.arc_band(cu, zs, r - f, r, 0.0, math.pi, D(-0.09), D(-REVEAL), axis, segs=segs)
    S.prism(rect(cu - r + f, cu + r - f, z_sill, z_sill + 0.09), D(-0.12), D(-REVEAL), axis)   # bottom rail
    zm = (z_sill + zs) / 2 + 0.15                                                               # meeting rail
    S.prism(rect(cu - r + f, cu + r - f, zm - 0.03, zm + 0.03), D(-0.13), D(-REVEAL), axis)
    S.prism(rect(cu - 0.015, cu + 0.015, z_sill + 0.09, zs + r - f), D(-0.15), D(-REVEAL), axis)  # 2/2 muntin
    if sill:
        sw = (sill_w or w + 0.2) / 2
        G["Stone"].prism(rect(cu - sw, cu + sw, z_sill - 0.12, z_sill + 0.01), D(0.06), D(-REVEAL), axis)
    if key:
        keystone(wall, cu, crown)
    if shutters:
        sh = 2.35
        for s in (-1, 1):
            u0, u1 = sorted((cu + s * r, cu + s * (r + 0.5)))
            G["Shutter"].prism(rect(u0, u1, z_sill, z_sill + sh), D(0.03), D(0.07), axis)
            for zb, zt in ((z_sill + 0.10, z_sill + 1.02), (z_sill + 1.14, z_sill + sh - 0.10)):
                G["Shutter"].prism(rect(u0 + 0.07, u1 - 0.07, zb, zt), D(0.07), D(0.085), axis)


def basement_window(wall, cu, cell="dark_room"):
    """Segmental-headed 0.9 x 0.5 m basement light, sill 0.35, with a 3-bar iron grille."""
    axis, face, out = wall
    D = lambda k: face + out * k
    w, z0, zs, top = 0.9, 0.35, 0.73, 0.85
    rr = ((w / 2) ** 2 + (top - zs) ** 2) / (2 * (top - zs))
    a0 = math.acos((w / 2) / rr)
    head = [(cu + rr * math.cos(a0 + (math.pi - 2 * a0) * i / 4), top - rr + rr * math.sin(a0 + (math.pi - 2 * a0) * i / 4))
            for i in range(5)]
    pts = [(cu - w / 2, z0), (cu + w / 2, z0)] + head
    CUT_F.prism(pts, D(0.25), D(-0.25), axis)
    # window back 4 cm behind the glass (the recess goes 0.25 deep): the cell's middle strip
    pane(wall, pts, -0.18, cell, crop=(0.0, 1.0, 0.30, 0.52))
    for k in (-1, 0, 1):
        u = cu + k * 0.22
        G["Iron"].prism(rect(u - 0.0125, u + 0.0125, z0, top), D(-0.04), D(-0.065), axis)
    G["Iron"].prism(rect(cu - w / 2, cu + w / 2, 0.58, 0.605), D(-0.04), D(-0.065), axis)


def arched_door(wall, cu, w=1.15, z0=FOUND + 0.01, crown=4.10):
    """Round-arched doorway: drab frame, fanlight with radiating bars over a transom bar,
    double-leaf door with glazed upper panels (stiles and rails round the light, glass with a
    dark hall behind) and a raised lower panel, stone threshold."""
    axis, face, out = wall
    D = lambda k: face + out * k
    r = w / 2
    zs = crown - r
    f = 0.08
    CUT.prism(arched(cu, w, FOUND - 0.10, zs, 10), D(0.25), D(-RECESS), axis)
    G["Stone"].prism(rect(cu - r, cu + r, FOUND - 0.10, z0), D(0.02), D(-RECESS), axis)       # threshold
    pane(wall, arched(cu, w, zs - 0.10, zs, 10), -REVEAL - 0.02, pick(DIM, wall, cu, near=0.1),
         crop=(0.0, 1.0, 0.72, 0.98))                                                       # fanlight
    for a in (math.pi / 6, math.pi / 3, math.pi / 2, 2 * math.pi / 3, 5 * math.pi / 6):    # fanlight bars
        ca, sa = math.cos(a), math.sin(a)
        nx, nz = -sa * 0.016, ca * 0.016
        x1, z1 = cu + (r - f) * ca, zs + (r - f) * sa
        G["Trim"].prism([(cu + nx, zs + nz), (cu - nx, zs - nz), (x1 - nx, z1 - nz), (x1 + nx, z1 + nz)],
                        D(-REVEAL + 0.03), D(-REVEAL - 0.02), axis)
    G["Trim"].arc_band(cu, zs, 0.001, 0.16, 0.0, math.pi, D(-REVEAL + 0.04), D(-REVEAL - 0.02), axis, segs=4)
    T = G["Trim"]
    T.prism(rect(cu - r, cu - r + f, z0, zs), D(-0.08), D(-RECESS), axis)                      # jambs
    T.prism(rect(cu + r - f, cu + r, z0, zs), D(-0.08), D(-RECESS), axis)
    T.prism(rect(cu - r + f, cu + r - f, zs - 0.12, zs), D(-0.10), D(-REVEAL - 0.02), axis)    # transom bar
    T.arc_band(cu, zs, r - f, r, 0.0, math.pi, D(-0.08), D(-RECESS), axis, segs=10)
    keystone(wall, cu, crown)
    # two leaves
    top = zs - 0.12
    inner = w - 2 * f
    leaf = inner / 2
    for i in range(2):
        x0 = cu - inner / 2 + i * leaf + 0.005
        x1 = x0 + leaf - 0.010
        gz0, gz1 = z0 + 1.05, top - 0.10                       # the light
        Dr = G["Door"]
        Dr.prism(rect(x0, x1, z0, gz0), D(-REVEAL), D(-REVEAL - 0.05), axis)                 # lower leaf
        Dr.prism(rect(x0, x0 + 0.07, gz0, top), D(-REVEAL), D(-REVEAL - 0.05), axis)         # stiles
        Dr.prism(rect(x1 - 0.07, x1, gz0, top), D(-REVEAL), D(-REVEAL - 0.05), axis)
        Dr.prism(rect(x0 + 0.07, x1 - 0.07, gz1, top), D(-REVEAL), D(-REVEAL - 0.05), axis)  # top rail
        Dr.prism(rect(x0 + 0.07, x1 - 0.07, z0 + 0.15, z0 + 0.85), D(-REVEAL + 0.015), D(-REVEAL), axis)
        # glass 2 cm into the leaf, its back just behind the leaf (its edges hidden by the leaf)
        pane(wall, rect(x0 + 0.07, x1 - 0.07, gz0, gz1), -REVEAL - 0.02,
             pick(DIM, wall, cu + (i - 0.5) * 0.5, near=0.3), grow=0.04)
        kx = x1 - 0.05 if i == 0 else x0 + 0.05
        G["Iron"].prism(rect(kx - 0.02, kx + 0.02, z0 + 0.98, z0 + 1.02), D(-REVEAL + 0.05), D(-REVEAL), axis)


# ---------------------------------------------------------------------------
# Shells: rough stone basement and the brick walls (openings cut by booleans)
# ---------------------------------------------------------------------------

FOUNDATION.box(-HW, HW, 0.0, BACK, -0.20, FOUND)       # 0.2 m hidden skirt below grade
WALLS.box(-HW, HW, 0.0, BACK, FOUND, WALL_TOP)

# water-table cap at 1.2 m (two steps read as a chamfer) and the string course at ~5 m
G["Stone"].prism(rect(-HW - 0.05, HW + 0.05, -0.05, BACK + 0.05), FOUND - 0.08, FOUND - 0.035, axis="z")
G["Stone"].prism(rect(-HW - 0.025, HW + 0.025, -0.025, BACK + 0.025), FOUND - 0.035, FOUND, axis="z")
G["Stone"].prism(rect(-HW - 0.08, HW + 0.08, -0.08, BACK - 0.01), STRING_BOT, STRING_TOP, axis="z")

# Front (east): W D W D W D W on the ground floor
for x in GROUND_X:
    arched_window(FRONT, x, 1.0, 1.75, 4.10, shutters=True, cell=pick(OFFICE, FRONT, x))
    basement_window(FRONT, x, cell=pick(DIM, FRONT, x + 100, near=2.0))
for x in DOOR_X:
    arched_door(FRONT, x)
# upper floor: four singles over the ground windows, the paired window in the centre
for x in GROUND_X:
    if x == 2.1:   # north inner: the window stands on the plain stone sign panel
        arched_window(FRONT, x, 0.9, 5.40, 7.25, sill=False, cell=pick(OFFICE, FRONT, x))
    else:
        arched_window(FRONT, x, 0.9, 5.20, 7.25, cell=pick(OFFICE, FRONT, x))
for x in (-0.5, 0.5):
    arched_window(FRONT, x, 0.75, 5.20, 7.25, sill=False, cell=pick(OFFICE, FRONT, x, near=1.2))
G["Stone"].prism(rect(-1.0, 1.0, 5.08, 5.21), 0.06, -REVEAL, axis="y")        # one sill across both lights
G["Stone"].box(2.1 - 0.75, 2.1 + 0.75, -0.05, 0.0, STRING_TOP, STRING_TOP + 0.35)   # sign panel (no lettering)

# Sides: four bays, shuttered ground windows, plain upper windows, basement lights
for wall in (SOUTH, NORTH):
    for y in SIDE_BAYS:
        arched_window(wall, y, 1.0, 1.75, 4.10, shutters=True, cell=pick(OFFICE, wall, y))
        arched_window(wall, y, 0.9, 5.20, 7.25, cell=pick(OFFICE, wall, y))
        basement_window(wall, y, cell=pick(DIM, wall, y + 100, near=2.0))

# Rear (west, guess): three bays, back door in the middle on a wooden step
for x in (-3.7, 3.7):
    arched_window(REAR, x, 1.0, 1.75, 4.10, key=False, cell=pick(BACKSIDE, REAR, x))
for x in (-3.7, 0.0, 3.7):
    arched_window(REAR, x, 0.9, 5.20, 7.25, key=False, cell=pick(BACKSIDE, REAR, x))
CUT.prism(rect(-0.5, 0.5, FOUND - 0.10, 3.40), BACK + 0.25, BACK - RECESS)
G["Door"].prism(rect(-0.5, 0.5, FOUND, 3.40), BACK - REVEAL, BACK - REVEAL - 0.05)
for zb, zt in ((FOUND + 0.15, FOUND + 1.05), (FOUND + 1.20, 3.25)):
    G["Door"].prism(rect(-0.40, 0.40, zb, zt), BACK - REVEAL + 0.015, BACK - REVEAL)
G["Trim"].prism(rect(-0.5, 0.5, FOUND - 0.10, FOUND + 0.01), BACK + 0.02, BACK - RECESS)        # sill board
G["Stone"].prism([(-0.62, 3.40), (0.62, 3.40), (0.62, 3.58), (-0.62, 3.58)], BACK + 0.04, BACK - 0.01)  # lintel
R4 = FOUND / 4                                                        # 4-riser wooden step + platform
step = [(BACK, -0.05), (BACK + 1.84, -0.05), (BACK + 1.84, R4)]
for k in range(1, 4):
    y = BACK + 1.84 - 0.28 * k
    step += [(y, R4 * k), (y, R4 * (k + 1))]
step += [(BACK, FOUND)]
G["Trim"].prism(step, -0.75, 0.75, axis="x")

# ---------------------------------------------------------------------------
# Stoops: three identical pale-stone stoops, 7 risers, iron railings
# ---------------------------------------------------------------------------

RISER = FOUND / 7
TREAD = 0.27
STOOP_Y0 = -2.4
SW = 0.80                     # half width (1.6 m)
NOSE = lambda y: RISER * (1 + (y - STOOP_Y0) / TREAD)        # nosing line height above y


def stoop(cx):
    prof = [(STOOP_Y0, -0.20), (STOOP_Y0, RISER)]
    for k in range(1, 7):
        y = STOOP_Y0 + TREAD * k
        prof += [(y, RISER * k), (y, RISER * (k + 1))]
    prof += [(0.0, FOUND), (0.0, -0.20)]
    G["Stone"].prism(prof, cx - SW, cx + SW, axis="x")
    I = G["Iron"]
    y_land = STOOP_Y0 + TREAD * 6                       # front edge of the landing (-0.78)
    for s in (-1, 1):
        x = cx + s * (SW - 0.06)
        x0, x1 = x - 0.02, x + 0.02
        yn = STOOP_Y0 + 0.08                            # newel post on the first tread
        I.box(x - 0.04, x + 0.04, yn - 0.04, yn + 0.04, RISER, RISER + 1.0)
        # top rail along the slope, then level along the landing back to the wall
        for off, t in ((0.90, 0.025), (0.12, 0.02)):
            ya, yb = yn + 0.04, y_land
            I.prism([(ya, NOSE(ya) + off - t), (yb, NOSE(yb) + off - t), (yb, NOSE(yb) + off + t), (ya, NOSE(ya) + off + t)],
                    x0, x1, axis="x")
            zl = FOUND + off
            I.prism(rect(y_land - 0.02, 0.0, zl - t, zl + t), x0, x1, axis="x")
        # pickets every 0.15 m (4-sided bars)
        y = yn + 0.15
        while y < -0.05:
            z0 = RISER * (1 + math.floor((y - STOOP_Y0) / TREAD)) if y < y_land else FOUND
            z1 = (NOSE(min(y, y_land)) + 0.90) if y < y_land else FOUND + 0.90
            I.prism(rect(y - 0.01, y + 0.01, z0, z1), x - 0.01, x + 0.01, axis="x", caps=False)
            y += 0.15


for x in DOOR_X:
    stoop(x)

# ---------------------------------------------------------------------------
# Cornice: bed moulding, corona, cap (stacked plan prisms), broken over the roof arch
# ---------------------------------------------------------------------------


def cornice_outline(p, p_rear):
    # the notch over the roof arch stops 5 cm behind the tympanum face (no coplanar faces)
    return [(-HW - p, -p), (-ARCH_X, -p), (-ARCH_X, 0.05), (ARCH_X, 0.05), (ARCH_X, -p), (HW + p, -p),
            (HW + p, BACK + p_rear), (-HW - p, BACK + p_rear)]


T = G["Trim"]
T.prism(cornice_outline(0.15, 0.10), WALL_TOP, SOFFIT, axis="z")              # bed / fascia
T.prism(cornice_outline(OVER, OVER_REAR), SOFFIT, CORONA_TOP, axis="z")       # corona
T.prism(cornice_outline(OVER + 0.06, OVER_REAR + 0.05), CORONA_TOP, CORN_TOP, axis="z")   # cap moulding

# Scroll bracket profile: (projection from the wall, height below the soffit); 0.6 deep, 0.9 high
BRACKET = [(0.0, 0.0), (0.60, 0.0), (0.60, -0.08), (0.46, -0.15), (0.31, -0.28), (0.23, -0.47),
           (0.20, -0.66), (0.12, -0.80), (0.0, -0.90)]
BW = 0.18
PAIR = 0.175


def bracket_front(x):
    T.prism([(-o, SOFFIT + z) for o, z in BRACKET], x - BW / 2, x + BW / 2, axis="x")


def bracket_side(s, y):
    T.prism([(s * (HW + o), SOFFIT + z) for o, z in BRACKET], y - BW / 2, y + BW / 2, axis="y")


for s in (-1, 1):
    bracket_front(s * (HW - 0.12))          # corner pair wraps: one on the front ...
    bracket_side(s, 0.12)                   # ... one on the side
    for xc in (4.6, ARCH_X):
        for d in (-PAIR, PAIR):
            bracket_front(s * (xc + d))
    for yc in SIDE_BRACKETS:
        for d in (-PAIR, PAIR):
            bracket_side(s, yc + d)
    bracket_side(s, BACK - 0.12)            # rear corner (the rear cornice is plain)

# ---------------------------------------------------------------------------
# Roof arch: brick tympanum on the front wall, arched cornice, oculus
# ---------------------------------------------------------------------------

tymp = [(-ARCH_X - 0.05, WALL_TOP), (ARCH_X + 0.05, WALL_TOP), (ARCH_X + 0.05, CORN_TOP)]
ts = [ARCH_A0 + (math.pi - 2 * ARCH_A0) * i / 14 for i in range(15)]
tymp += [(0 + (ARCH_R - 0.12) * math.cos(t), ARCH_ZC + (ARCH_R - 0.12) * math.sin(t)) for t in ts]
tymp += [(-ARCH_X - 0.05, CORN_TOP)]
G["BrickFront"].prism(tymp, 0.0, 0.40)
# arched cornice: corona band (0.45 out) over a smaller bed band, following the arch
T.arc_band(0, ARCH_ZC, ARCH_R - 0.24, ARCH_R, ARCH_A0, math.pi - ARCH_A0, -0.45, 0.42, segs=14)
T.arc_band(0, ARCH_ZC, ARCH_R - 0.40, ARCH_R - 0.24, ARCH_A0, math.pi - ARCH_A0, -0.20, 0.02, segs=14)
T.arc_band(0, ARCH_ZC, ARCH_R - 0.02, ARCH_R + 0.04, ARCH_A0, math.pi - ARCH_A0, -0.50, 0.42, segs=14)   # cap
# oculus: pale stone ring, dark glass
OC_Z = 9.30
G["Stone"].ring(0, OC_Z, 0.40, 0.52, -0.06, 0.02, segs=12)
# glass 4.5 cm out from the tympanum inside the 6 cm deep ring, a round window back on the brick
pane(FRONT, circle(0, OC_Z, 0.41), 0.045, "dark_room_frame", crop=(0.0, 1.0, 0.30, 0.70),
     back_outline=circle(0, OC_Z, 0.41))

# ---------------------------------------------------------------------------
# Roof: low hip (~18 deg), painted tin, short E-W ridge
# ---------------------------------------------------------------------------

bm = G["Roof"].bm
v = [bm.verts.new(p) for p in ((-HW, 0, CORN_TOP), (HW, 0, CORN_TOP), (HW, BACK, CORN_TOP), (-HW, BACK, CORN_TOP),
                                (0, HW, RIDGE), (0, BACK - HW, RIDGE))]
rf = [bm.faces.new(f) for f in ((v[0], v[1], v[4]), (v[1], v[2], v[5], v[4]), (v[2], v[3], v[5]),
                                (v[3], v[0], v[4], v[5]), (v[3], v[2], v[1], v[0]))]
bmesh.ops.recalc_face_normals(bm, faces=rf)

# ---------------------------------------------------------------------------
# Build objects (boolean the cut shells)
# ---------------------------------------------------------------------------


def cut_shell(shell, cutter, name, mat):
    walls = shell.to_object(name, mat, col)
    cutters = cutter.to_object(name + "_Cutters", MATS["Trim"], col)
    mod = walls.modifiers.new("Openings", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    solvers = [i.identifier for i in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items]
    mod.solver = "EXACT" if "EXACT" in solvers else solvers[0]
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


walls = cut_shell(WALLS, CUT, "CO_Walls", MATS["BrickFront"])
# front wall (and its reveals) get the front brick, sides and rear the duller common brick
walls.data.materials.clear()
walls.data.materials.append(MATS["BrickFront"])
walls.data.materials.append(MATS["BrickSide"])
for p in walls.data.polygons:
    c = p.center
    p.material_index = 0 if (c.y < RECESS + 0.01 and abs(c.x) < HW - 0.001) else 1
cut_shell(FOUNDATION, CUT_F, "CO_Foundation", MATS["Rock"])
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("CO_" + key, MATS[key], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("County Offices built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)")
# Materials, baked lighting and GLB export: run county_offices_bake.py (it runs this file first).
