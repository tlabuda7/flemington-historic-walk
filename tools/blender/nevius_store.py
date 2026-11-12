"""
nevius_store.py - builds the Nevius Store / Fulper's Dry Goods Building (78 Main St,
Flemington; Italianate brick front of c. 1880, as it stood c. 1920) in Blender.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/nevius_store.py").read())

Every run deletes and rebuilds the "NeviusStore" collection, so edit the numbers below and
run again. Materials, lightmap bake and GLB export: nevius_store_bake.py (runs this first).
Pattern: bank_building.py.

Sources: PLAN.md "Nevius Store / Fulper's Dry Goods Building" spec and its orchestrator
decisions (1921 Sanborn sheet 3; 1909 "Nevius Store and Union Hotel" card; HABS NJ-732
1963 views; Pickell's description): a narrow 3-storey red-brick store, 8.00 x 32.25 m,
1 + 2 + 1 upper windows with the pair in a slightly projecting central section, segmental
2nd-floor windows with stone arches and keystones, round-headed 3rd-floor windows with brick
hood moulds on a stone sill band, brick quoins, bracketed cornice with a segmental pediment,
painted wood shop front with a recessed double door and a bracketed cornice, one plain pale
canvas awning with a fringed scalloped valance and side curtains (1912 card, 2026-11-11 fixes).

Only 6 materials, in this slot order on every part:
    0 Brick, 1 Trim, 2 Glass, 3 Dark, 4 Awning, 5 WindowBack
Glass is a thin pane (its own material `glass`, see nevius_store_bake.py) a few cm in front
of a "window back" (shared atlas assets/textures/shared/window_backs.jpg: blinds, lace,
curtains, dark rooms); WB_FRAMES records where each back is and which atlas cell it
shows (PLAN.md "E. Windows that don't read as flat black"). The shop-front panes (display
windows, door glass, returns, transoms) use cells of the dedicated, sharper
assets/textures/shared/shop_interior.jpg instead; the bake script moves those faces to a
seventh material, NVR_ShopInterior.
Shells and boolean cutters carry a material index per face; the boolean copies the cutter's
index onto the faces it creates, so reveals, frames and glass need no extra geometry.

Coordinates (metres, Blender Z-up):
    X  along the front, +X = south (alley / 82 Main), -X = north (Union Hotel side)
    Y  depth: y = 0 is the front brick wall face (on the property line); the central
       section stands 0.10 proud (y = -0.10), the step runs out to -0.25, the main
       cornice to -0.65, the awning to -1.91. Rear wall y = 32.25.
    Z  up from the sidewalk top; walls skirt down to -0.20.
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".
"""

import math
import bpy
import bmesh

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md)
# ---------------------------------------------------------------------------
HW = 4.00              # half front (8.00 m)
DEPTH = 32.25
T_FRONT, T_SIDE = 0.40, 0.35
SKIRT = -0.20
SHOP_FL = 0.12         # shop floor / top of the step
WALL_TOP = 10.20       # side and rear walls
FRONT_TOP = 10.70      # front wall behind the cornice
ROOF_F, ROOF_R = 9.90, 9.42
XC = 1.35              # half width of the projecting central section
PROJ = 0.10            # its projection
SEC0, SEC1 = 4.20, 9.50                    # central section up to the bed moulding (review round 1)

PAIR_X, PAIR_W = 0.575, 0.85
SING_X, SING_W = 2.40, 0.90
S2, SP2, RISE2 = 4.55, 6.45, 0.25          # 2nd floor: sill, spring, segmental rise
BAND0, BAND1 = 7.25, 7.45                  # 3rd floor sill band
S3, SP3 = 7.45, 8.95                       # 3rd floor: sill, spring (semicircular; crown ~9.40, review round 1)

BRICK, TRIM, GLASS, DARK, AWNING, WBACK = range(6)
NAMES = ["Brick", "Trim", "Glass", "Dark", "Awning", "WindowBack"]

# ---------------------------------------------------------------------------
# Materials (plain stand-ins; nevius_store_bake.py swaps in the textures)
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


COLOURS = ["#8e4632", "#d8cdb4", "#1e2226", "#3a2a1f", "#b06050", "#3a3028"]
MATS = [plain("NV_" + n, c) for n, c in zip(NAMES, COLOURS)]

# ---------------------------------------------------------------------------
# Mesh builder: one bmesh, a material index per face
# ---------------------------------------------------------------------------


class MB:
    def __init__(self):
        self.bm = bmesh.new()

    @staticmethod
    def _pt(axis, u, d, v):
        # axis 'y': outline in the X-Z plane, depth along Y (front/back walls)
        # axis 'x': outline in the Y-Z plane, depth along X (side walls)
        # axis 'z': outline in the X-Y plane (plan), depth along Z
        if axis == "y":
            return (u, d, v)
        if axis == "x":
            return (d, u, v)
        return (u, v, d)

    def prism(self, pts, d0, d1, axis="y", mi=TRIM, caps=True):
        """Extrude a 2D outline [(u, v), ...] between depths d0 and d1.
        mi: one material index, or (cap at d0, cap at d1, sides) where sides is an index or a
        list with one index per outline edge (edge i runs from point i to point i+1)."""
        bm = self.bm
        if isinstance(mi, int):
            m0 = m1 = mi
            ms = [mi] * len(pts)
        else:
            m0, m1, ms = mi
            ms = ms if isinstance(ms, (list, tuple)) else [ms] * len(pts)
        a = [bm.verts.new(self._pt(axis, u, d0, v)) for u, v in pts]
        b = [bm.verts.new(self._pt(axis, u, d1, v)) for u, v in pts]
        faces = []
        if caps:
            fa = bm.faces.new(a)
            fa.material_index = m0
            fb = bm.faces.new(list(reversed(b)))
            fb.material_index = m1
            faces += [fa, fb]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new([a[i], a[j], b[j], b[i]])
            f.material_index = ms[i]
            faces.append(f)
        bmesh.ops.recalc_face_normals(bm, faces=faces)

    def face(self, pts, d, axis, outward, mi):
        """One flat n-gon (outline [(u, v), ...] at depth d) whose normal points along
        `outward` (+1/-1 on the depth axis)."""
        f = self.bm.faces.new([self.bm.verts.new(self._pt(axis, u, d, v)) for u, v in pts])
        f.normal_update()
        k = {"x": 0, "y": 1, "z": 2}[axis]
        if f.normal[k] * outward < 0:
            f.normal_flip()
        f.material_index = mi
        return f

    def quad3(self, a, b, z0, z1, outward, mi):
        """Vertical quad from plan point a to b (x, y), z0..z1, normal toward `outward` (x, y)."""
        vs = [self.bm.verts.new(p) for p in ((a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1))]
        f = self.bm.faces.new(vs)
        f.normal_update()
        if f.normal.x * outward[0] + f.normal.y * outward[1] < 0:
            f.normal_flip()
        f.material_index = mi
        return f

    def box(self, x0, x1, y0, y1, z0, z1, mi=TRIM):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, "y", mi)

    def arc_band(self, cu, cv, r_in, r_out, a0, a1, d0, d1, axis="y", segs=8, mi=TRIM):
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


def arched(cu, w, z0, zs, segs=8):
    """Outline of a round-headed opening: straight sides from z0 up to zs, half-circle above."""
    r = w / 2
    return [(cu - r, z0), (cu + r, z0)] + [
        (cu + r * math.cos(math.pi * i / segs), zs + r * math.sin(math.pi * i / segs))
        for i in range(segs + 1)]


def seg_geom(w, zs, rise):
    """Circle of a segmental head of chord w springing at zs: (centre z, radius, half angle)."""
    R = ((w / 2) ** 2 + rise ** 2) / (2 * rise)
    return zs + rise - R, R, math.asin((w / 2) / R)


def seg_outline(cu, half, z0, zc, R, segs=6):
    """Opening with straight jambs at cu +- half from z0 up to circle (cu, zc, R)."""
    th = math.asin(half / R)
    a0, a1 = math.pi / 2 - th, math.pi / 2 + th
    return [(cu - half, z0), (cu + half, z0)] + [
        (cu + R * math.cos(a0 + (a1 - a0) * i / segs), zc + R * math.sin(a0 + (a1 - a0) * i / segs))
        for i in range(segs + 1)]


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


col = fresh_collection("NeviusStore")
P = MB()                 # all added parts
SHELL, ADD, CUT = MB(), MB(), MB()   # brick shell, solids unioned onto it, cutters

# Each wall: (axis, outer face depth, outward sign)
FRONT = ("y", 0.0, -1)
CENTRE = ("y", -PROJ, -1)
NORTH = ("x", -HW, -1)
SOUTH = ("x", HW, 1)
REAR = ("y", DEPTH, 1)


def Dfun(wall):
    axis, face, out = wall
    return axis, (lambda k: face + out * k)   # k > 0 outside the wall, k < 0 inside


# ---------------------------------------------------------------------------
# Shell: one closed brick solid (front wall up to 10.70 behind the cornice, the rest to
# 10.20); the roof well is cut out of it, the central section is unioned onto it
# ---------------------------------------------------------------------------
SHELL.prism([(0.0, SKIRT), (DEPTH, SKIRT), (DEPTH, WALL_TOP), (T_FRONT, WALL_TOP), (T_FRONT, FRONT_TOP),
             (0.0, FRONT_TOP)], -HW, HW, axis="x", mi=BRICK)
ADD.box(-XC, XC, -PROJ, 0.05, SEC0, SEC1, mi=BRICK)
# roof well: flat tin roof 9.90 at the front falling to 9.42 at the rear; parapets 0.35
CUT.prism([(T_FRONT, ROOF_F), (DEPTH - T_SIDE, ROOF_R), (DEPTH - T_SIDE, 12.0), (T_FRONT, 12.0)],
          -HW + T_SIDE, HW - T_SIDE, axis="x", mi=(BRICK, BRICK, [DARK, BRICK, BRICK, BRICK]))

# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------
FR = 0.07          # frame width
D_FRAME = 0.12     # frame face behind the wall face
D_GLASS = 0.20     # glass behind the wall face
BACK_GAP = 0.04    # window back (blind, lace, curtains, interior) this far behind the glass

# Window backs: one entry per pane -> atlas cell. origin (x, y) at the left end of the back
# as seen from outside, u = unit plan direction along it, length, z0..z1, outward normal
# (plan), cell name in assets/textures/shared/window_backs.json. Read by the bake script.
WB_FRAMES = []
# upper-floor cells, in an order where no two neighbours (side by side or one above the
# other) repeat; mostly blinds and lace, a few curtains and unscreened dark rooms
UPPER_CYCLE = ["blind_cream_half", "lace", "blind_green_high", "lace_blind_cream", "blind_cream_low",
               "curtains_olive", "blind_green_half", "blind_cream_high", "lace_full_blind_cream",
               "dark_room", "blind_green_low", "lace_blind_green", "blind_cream_full", "curtains_beige",
               "blind_green_half", "dark_room_frame", "curtains_maroon_blind"]
_cycle = [0]


def next_variant():
    v = UPPER_CYCLE[_cycle[0] % len(UPPER_CYCLE)]
    _cycle[0] += 1
    return v


def wb_frame(origin, udir, length, z0, z1, outward, cell):
    n = (udir[1], -udir[0])                      # true plan normal of the back, on the outward side
    if n[0] * outward[0] + n[1] * outward[1] < 0:
        n = (-n[0], -n[1])
    WB_FRAMES.append(dict(origin=origin, u=udir, length=length, z0=z0, z1=z1, n=n, cell=cell))


def frame_on_wall(wall, d, u0, u1, z0, z1, cell):
    """Window back on a wall plane at depth coordinate d, spanning u0..u1 along the wall."""
    axis, face, out = wall
    if axis == "y":                    # front / rear: seen from -Y (front) runs +X, from +Y runs -X
        if out < 0:
            wb_frame((u0, d), (1, 0), u1 - u0, z0, z1, (0, -1), cell)
        else:
            wb_frame((u1, d), (-1, 0), u1 - u0, z0, z1, (0, 1), cell)
    else:                              # side walls: north (out -1) seen from -X runs -Y ... keep left-to-right
        if out < 0:
            wb_frame((d, u1), (0, -1), u1 - u0, z0, z1, (-1, 0), cell)
        else:
            wb_frame((d, u0), (0, 1), u1 - u0, z0, z1, (1, 0), cell)


def framed_opening(wall, outer, inner, wall_mat=BRICK, d_frame=D_FRAME, d_glass=D_GLASS, cell=None):
    """Two nested cutters: the outer pocket's reveal keeps the wall material and its back
    becomes the painted frame; the inner pocket's sides are frame and its back is the window
    back (BACK_GAP behind the glass). The glass is a separate pane in the inner outline."""
    axis, D = Dfun(wall)
    CUT.prism(outer, D(0.25), D(-d_frame), axis, mi=(wall_mat, TRIM, wall_mat))
    CUT.prism(inner, D(0.25), D(-d_glass - BACK_GAP), axis, mi=(TRIM, WBACK, TRIM))
    P.face(inner, D(-d_glass), axis, wall[2], GLASS)
    us, vs = [p[0] for p in inner], [p[1] for p in inner]
    frame_on_wall(wall, D(-d_glass - BACK_GAP), min(us), max(us), min(vs), max(vs), cell or next_variant())


def meeting_rail(wall, cu, w, z):
    axis, D = Dfun(wall)
    P.prism(rect(cu - w / 2 + FR, cu + w / 2 - FR, z - 0.03, z + 0.03), D(-D_FRAME + 0.02), D(-D_GLASS), axis, mi=TRIM)


def sill(wall, cu, w, z, thick=0.10, proj=0.05, ext=0.15):
    """Stone sill whose top is 0.02 above the opening's bottom (covers the pocket floor)."""
    axis, D = Dfun(wall)
    P.prism(rect(cu - w / 2 - ext, cu + w / 2 + ext, z + 0.02 - thick, z + 0.02), D(proj), D(-D_FRAME), axis, mi=TRIM)


def second_floor_window(wall, cu, w, arch_proud=0.03):
    """Segmental head (rise 0.25), stone arch 0.22 deep, keystone, stone sill."""
    axis, D = Dfun(wall)
    zc, R, th = seg_geom(w, SP2, RISE2)
    framed_opening(wall, seg_outline(cu, w / 2, S2, zc, R), seg_outline(cu, w / 2 - FR, S2 + FR, zc, R - FR))
    meeting_rail(wall, cu, w, (S2 + SP2) / 2 + 0.10)
    sill(wall, cu, w, S2)
    P.arc_band(cu, zc, R, R + 0.22, math.pi / 2 - th, math.pi / 2 + th, D(arch_proud), D(0.0), axis, segs=6, mi=TRIM)
    crown = SP2 + RISE2
    P.prism([(cu - 0.10, crown - 0.08), (cu + 0.10, crown - 0.08), (cu + 0.12, 6.95), (cu - 0.12, 6.95)],
            D(0.05), D(0.0), axis, mi=TRIM)                          # keystone, top 6.95


def third_floor_window(wall, cu, w):
    """Semicircular head, slim brick hood mould ending in square blocks."""
    axis, D = Dfun(wall)
    r = w / 2
    framed_opening(wall, arched(cu, w, S3, SP3, 8), arched(cu, w - 2 * FR, S3 + FR, SP3, 8))
    meeting_rail(wall, cu, w, (S3 + SP3) / 2 + 0.05)
    P.prism(rect(cu - r - 0.05, cu + r + 0.05, S3 - 0.02, S3 + 0.02), D(0.0), D(-D_FRAME), axis, mi=TRIM)  # sill in the pocket
    P.arc_band(cu, SP3, r, r + 0.10, 0.0, math.pi, D(0.05), D(0.0), axis, segs=8, mi=BRICK)
    for s in (-1, 1):
        bx = cu + s * (r + 0.05)
        P.prism(rect(bx - 0.10, bx + 0.10, SP3 - 0.10, SP3 + 0.10), D(0.06), D(0.0), axis, mi=BRICK)


for x, w in ((-SING_X, SING_W), (SING_X, SING_W)):
    second_floor_window(FRONT, x, w)
    third_floor_window(FRONT, x, w)
for x, w, pr in ((-PAIR_X, PAIR_W, 0.030), (PAIR_X, PAIR_W, 0.034)):   # arches meet over the mullion
    second_floor_window(CENTRE, x, w, pr)
    third_floor_window(CENTRE, x, w)

# pilaster strips edging the central section, 0.03 proud
for s in (-1, 1):
    x0, x1 = sorted((s * 1.19, s * XC))
    P.box(x0, x1, -PROJ - 0.03, -PROJ, SEC0, SEC1, mi=BRICK)

# 3rd-floor sill band, quoin to quoin, breaking forward over the central section
P.prism([(-3.45, 0.0), (-3.45, -0.08), (-XC - 0.08, -0.08), (-XC - 0.08, -PROJ - 0.08), (XC + 0.08, -PROJ - 0.08),
         (XC + 0.08, -0.08), (3.45, -0.08), (3.45, 0.0)], BAND0, BAND1, axis="z", mi=TRIM)

# ---------------------------------------------------------------------------
# Quoins: 30 courses on both front corners, 0.03 proud, alternating 0.55 / 0.38 on the
# front face and 0.38 / 0.55 on the side face, 0.015 joints
# ---------------------------------------------------------------------------
NQ = 30
QH = (SEC1 - SHOP_FL) / NQ
for k in range(NQ):
    z0 = SHOP_FL + k * QH
    z1 = z0 + QH - 0.015
    wf, ws = (0.55, 0.38) if k % 2 == 0 else (0.38, 0.55)
    for s in (-1, 1):
        pts = [(s * (HW + 0.03), -0.03), (s * (HW - wf), -0.03), (s * (HW - wf), 0.0), (s * HW, 0.0),
               (s * HW, ws), (s * (HW + 0.03), ws)]
        P.prism(pts, z0, z1, axis="z", mi=BRICK)

# ---------------------------------------------------------------------------
# Main cornice (front, with 0.6 m returns round both corners; breaks forward 0.10 over
# the central section), dentils, paired brackets, segmental pediment
# ---------------------------------------------------------------------------
RET = 0.60


def front_band(p, brk=PROJ):
    return [(-HW - p, RET), (-HW - p, -p), (-XC - p, -p), (-XC - p, -p - brk), (XC + p, -p - brk), (XC + p, -p),
            (HW + p, -p), (HW + p, RET), (HW, RET), (HW, 0.0), (-HW, 0.0), (-HW, RET)]


P.prism(front_band(0.10), 9.50, 9.58, axis="z", mi=TRIM)     # bed moulding (tightened over the 3rd-floor heads)
P.prism(front_band(0.06), 9.58, 10.15, axis="z", mi=TRIM)    # frieze
P.prism(front_band(0.08), 10.15, 10.25, axis="z", mi=TRIM)   # dentil backing
P.prism(front_band(0.55), 10.25, 10.60, axis="z", mi=TRIM)   # corona
P.prism(front_band(0.60), 10.60, FRONT_TOP, axis="z", mi=TRIM)   # cap

GROUPS = (-3.725, -1.175, 1.175, 3.725)


def face_y(x, p):
    """Front of a band of projection p at x (with the central break)."""
    return -p - (PROJ if abs(x) < XC + p else 0.0)


# frieze panels, 0.02 proud: one per bay between the bracket groups
for x0, x1 in ((-3.35, -1.55), (-0.85, 0.85), (1.55, 3.35)):
    fy = face_y((x0 + x1) / 2, 0.06)
    P.box(x0, x1, fy - 0.02, fy, 9.70, 10.05, mi=TRIM)

# dentils 0.06 wide at 0.12 m, 0.08 deep, skipping the bracket groups
x = -HW + 0.06
while x < HW - 0.05:
    if all(abs(x - g) > 0.30 for g in GROUPS):
        fy = face_y(x, 0.08)
        P.box(x - 0.03, x + 0.03, fy - 0.08, fy, 10.15, 10.25, mi=TRIM)
    x += 0.12

# brackets: 2 per group, 0.12 wide, 0.08 apart; scroll side profile, pendant drop below
BRACKET = [(0.0, 10.25), (0.46, 10.25), (0.46, 10.12), (0.38, 10.04), (0.26, 9.98), (0.18, 9.80),
           (0.15, 9.55), (0.15, 9.30), (0.10, 9.15), (0.0, 9.15)]
for g in GROUPS:
    fy = face_y(g, 0.06)
    for s in (-0.10, 0.10):
        bx = g + s
        prof = [(fy - t if t > 0 else 0.02, z) for t, z in BRACKET]
        P.prism(prof, bx - 0.06, bx + 0.06, axis="x", mi=TRIM)

# segmental pediment: chord 3.40 on the cornice top, crown 11.95; raking moulding 0.25
# high, 0.30 proud of the tympanum (set at the central section's face)
PED_HALF, PED_CROWN = 1.70, 11.95
pzc, pR, pth = seg_geom(2 * PED_HALF, FRONT_TOP, PED_CROWN - FRONT_TOP)
pa0, pa1 = math.pi / 2 - pth, math.pi / 2 + pth
P.arc_band(0.0, pzc, pR - 0.25, pR, pa0, pa1, -PROJ - 0.30, T_FRONT, "y", segs=12, mi=TRIM)
P.prism([((pR - 0.25) * math.cos(pa0 + (pa1 - pa0) * i / 12), pzc + (pR - 0.25) * math.sin(pa0 + (pa1 - pa0) * i / 12))
         for i in range(13)], -PROJ, T_FRONT, "y", mi=TRIM)                # tympanum
P.box(-PED_HALF + 0.05, PED_HALF - 0.05, -PROJ - 0.05, T_FRONT, FRONT_TOP, FRONT_TOP + 0.06, mi=TRIM)   # base fillet

# ---------------------------------------------------------------------------
# Side cornices (full length) and the chimney
# ---------------------------------------------------------------------------
for s in (-1, 1):
    a, b = sorted((s * HW, s * (HW + 0.04)))
    P.prism(rect(a, b, 0.0, DEPTH), 9.40, 10.00, axis="z", mi=TRIM)       # plain frieze
    a, b = sorted((s * HW, s * (HW + 0.20)))
    P.prism(rect(a, b, 0.0, DEPTH), 10.00, WALL_TOP, axis="z", mi=TRIM)   # corona
P.prism(rect(-HW, HW, DEPTH, DEPTH + 0.05), WALL_TOP - 0.10, WALL_TOP + 0.04, axis="z", mi=TRIM)   # rear coping

CH_X0, CH_Y0, CH_Y1, CH_TOP = HW - 0.60, 15.55, 16.45, 11.40
P.box(CH_X0, HW, CH_Y0, CH_Y1, 9.60, CH_TOP, mi=BRICK)
P.box(CH_X0 - 0.05, HW + 0.05, CH_Y0 - 0.05, CH_Y1 + 0.05, CH_TOP, CH_TOP + 0.08, mi=DARK)

# ---------------------------------------------------------------------------
# Side and rear walls: segmental windows (relief brick arch, stone sill)
# ---------------------------------------------------------------------------


def side_window(wall, cu, z0, h, w=0.85, rise=0.20):
    axis, D = Dfun(wall)
    zs = z0 + h - rise
    zc, R, th = seg_geom(w, zs, rise)
    framed_opening(wall, seg_outline(cu, w / 2, z0, zc, R, 4), seg_outline(cu, w / 2 - FR, z0 + FR, zc, R - FR, 4),
                   d_frame=0.10, d_glass=0.18)
    meeting_rail(wall, cu, w, (z0 + zs) / 2 + 0.08)
    sill(wall, cu, w, z0, thick=0.08, proj=0.04, ext=0.08)
    P.arc_band(cu, zc, R, R + 0.12, math.pi / 2 - th, math.pi / 2 + th, D(0.02), D(0.0), axis, segs=4, mi=BRICK)


for wall in (NORTH, SOUTH):
    for y in (7.0, 14.0, 21.0, 28.0):
        side_window(wall, y, 4.70, 1.90)
        side_window(wall, y, 7.60, 1.70)          # crown 9.30, under the side frieze
for y in (18.0, 26.0):
    side_window(SOUTH, y, 1.60, 1.40, w=0.80)
for x in (-2.0, 2.0):                             # rear (never seen from the street)
    side_window(REAR, x, 4.70, 1.90)
    side_window(REAR, x, 7.60, 1.70)
side_window(REAR, 2.0, 1.20, 1.60)
CUT.prism(rect(-2.5, -1.5, 0.0, 2.20), DEPTH + 0.25, DEPTH - 0.12, "y", mi=(BRICK, DARK, BRICK))   # rear door

# ---------------------------------------------------------------------------
# Shop front (z 0 - 4.20 between the corner piers): painted wood front set 0.10 back,
# north display window, recessed central double door with splayed glass returns, south
# display window, upper-floor street door, transom band, fascia, shop-front cornice
# ---------------------------------------------------------------------------
SF = 0.10                      # shop-front plane behind the brick face
REC = SF + 1.20                # back of the entrance recess
CUT.prism(rect(-3.45, 3.45, SHOP_FL, 3.95), -0.25, SF, "y", mi=(TRIM, TRIM, [TRIM, BRICK, TRIM, BRICK]))
CUT.prism([(-0.85, -0.25), (0.75, -0.25), (0.75, SF), (0.65, REC), (-0.75, REC), (-0.85, SF)], SHOP_FL, 2.95, "z",
          mi=(TRIM, TRIM, [TRIM, TRIM, WBACK, TRIM, WBACK, TRIM]))
# the splayed glass returns: shop interior behind, glass on the bulkheads' inner line
for a, b, inner, out, cell in (((-0.85, SF), (-0.75, REC), ((-0.80, SF), (-0.70, REC)), (1, 0), "return_n"),
                               ((0.65, REC), (0.75, SF), ((0.60, REC), (0.70, SF)), (-1, 0), "return_s")):
    wb_frame(a, ((b[0] - a[0]) / math.dist(a, b), (b[1] - a[1]) / math.dist(a, b)), math.dist(a, b), 0.70, 2.85,
             out, cell)
    P.quad3(inner[0], inner[1], 0.70, 2.85, out, GLASS)
CUT.prism(rect(2.50, 3.35, SHOP_FL, SHOP_FL + 2.50), -0.25, SF + 0.10, "y", mi=(TRIM, DARK, TRIM))

# stone step along the front
P.box(-3.45, 3.45, -0.25, 0.0, SKIRT, SHOP_FL, mi=TRIM)

# posts (jambs) on the shop-front plane
for x0, x1 in ((-3.45, -3.35), (-0.93, -0.85), (0.75, 0.83), (2.42, 2.50), (3.35, 3.45)):
    P.box(x0, x1, 0.0, SF, SHOP_FL, 2.95, mi=TRIM)


def display(x0, x1, cell):
    """Display window between x0 and x1: panelled bulkhead, sill rail, glass with one
    central mullion."""
    P.box(x0 + 0.08, x1 - 0.08, SF - 0.02, SF, SHOP_FL + 0.10, 0.60, mi=TRIM)      # raised bulkhead panel
    P.box(x0, x1, SF - 0.05, SF, 0.66, 0.72, mi=TRIM)                              # sill rail
    P.box(x0, x1, SF - 0.02, SF, 0.72, 2.95, mi=WBACK)                             # shop interior behind the glass
    wb_frame((x0, SF - 0.02), (1, 0), x1 - x0, 0.72, 2.95, (0, -1), cell)
    P.face(rect(x0, x1, 0.72, 2.95), SF - 0.045, "y", -1, GLASS)                     # display glass
    xm = (x0 + x1) / 2
    P.box(xm - 0.04, xm + 0.04, SF - 0.05, SF - 0.02, 0.72, 2.95, mi=TRIM)          # mullion


display(-3.35, -0.93, "shop_a")
display(0.83, 2.42, "shop_b")

# transom bar, 6 transom lights, fascia (plain, no lettering)
P.box(-3.45, 3.45, 0.0, SF, 2.95, 3.05, mi=TRIM)
P.box(-3.45, 3.45, SF - 0.02, SF, 3.05, 3.55, mi=WBACK)                              # ceiling seen through
wb_frame((-3.45, SF - 0.02), (1, 0), 6.90, 3.05, 3.55, (0, -1), "transom")
P.face(rect(-3.45, 3.45, 3.05, 3.55), SF - 0.045, "y", -1, GLASS)                   # transom glass
for k in range(1, 6):
    xb = -3.45 + 6.90 * k / 6
    P.box(xb - 0.03, xb + 0.03, SF - 0.05, SF - 0.02, 3.05, 3.55, mi=TRIM)
P.box(-3.45, 3.45, 0.0, SF, 3.55, 3.60, mi=TRIM)                                    # fascia bottom rail
P.box(-3.45, 3.45, 0.02, SF, 3.60, 4.05, mi=TRIM)                                   # frieze (fascia) 0.45

# shop-front cornice 4.02 - 4.20, projecting 0.35, small bed moulding; across the piers;
# painted dark brown (`dark` material, 1909 card, review round 1). Bracketed (1912 card,
# PLAN addendum 2026-11-11): 10 small console brackets on the frieze under the corona.
P.prism([(0.0, 4.02), (-0.06, 4.02), (-0.08, 4.06), (-0.30, 4.10), (-0.35, 4.14), (-0.35, 4.20), (0.0, 4.20)],
        -HW - 0.05, HW + 0.05, "x", mi=DARK)
SHOP_BRACKET = [(0.03, 4.03), (-0.26, 4.03), (-0.26, 3.97), (-0.19, 3.93), (-0.12, 3.89), (-0.08, 3.82),
                (-0.065, 3.74), (-0.04, 3.68), (0.03, 3.66)]                    # (y, z) side profile
for k in range(10):
    xb = -3.37 + 6.74 * k / 9
    P.prism(SHOP_BRACKET, xb - 0.045, xb + 0.045, "x", mi=DARK)

# entrance recess: splayed returns with bulkheads, glazed double door at the back
for pts in ([(-0.85, SF), (-0.80, SF), (-0.70, REC), (-0.75, REC)], [(0.70, SF), (0.75, SF), (0.65, REC), (0.60, REC)]):
    P.prism(pts, SHOP_FL, 0.70, "z", mi=TRIM)                                       # bulkheads
    P.prism(pts, 2.85, 2.95, "z", mi=TRIM)                                          # head rail
for x0, x1, cell in ((-0.75, -0.055, "door_l"), (-0.045, 0.65, "door_r")):
    P.box(x0, x1, REC - 0.05, REC, SHOP_FL, SHOP_FL + 2.60, mi=DARK)               # leaves
    P.box(x0 + 0.09, x1 - 0.09, REC - 0.065, REC - 0.05, 1.05, 2.58, mi=WBACK)     # shop seen through the door
    wb_frame((x0 + 0.09, REC - 0.065), (1, 0), x1 - x0 - 0.18, 1.05, 2.58, (0, -1), cell)
    P.face(rect(x0 + 0.09, x1 - 0.09, 1.05, 2.58), REC - 0.08, "y", -1, GLASS)       # glass upper two-thirds
    P.box(x0 + 0.09, x1 - 0.09, REC - 0.065, REC - 0.05, 0.25, 0.90, mi=DARK)      # raised lower panel
P.box(-0.75, 0.65, REC - 0.02, REC, 2.75, 2.92, mi=WBACK)                           # door transom
wb_frame((-0.75, REC - 0.02), (1, 0), 1.40, 2.75, 2.92, (0, -1), "transom_door")
P.face(rect(-0.75, 0.65, 2.75, 2.92), REC - 0.04, "y", -1, GLASS)

# upper-floor street door: two raised panels on the door face (0.20 behind the front plane)
for z0, z1 in ((0.30, 1.20), (1.40, 2.45)):
    P.box(2.62, 3.23, SF + 0.08, SF + 0.10, z0, z1, mi=DARK)

# ---------------------------------------------------------------------------
# Awning (1912 card, PLAN addendum 2026-11-11): plain pale canvas x -3.40 ... +3.40, hung at
# 3.50 on the front, 2.70 at 1.90 m out; a deep scalloped valance (16 lobes ~0.43 m, cusps
# 2.52, lobe bottoms 2.38) with a hanging fringe (thin teeth, 7 cm) along its lower edge;
# side curtains at both ends, from the canvas down to 1.0 m above the step.
# ---------------------------------------------------------------------------
AW0, AW1 = -3.40, 3.40
AW_FRONT = -1.90
P.prism([(0.0, 3.50), (AW_FRONT, 2.70), (AW_FRONT, 2.68), (0.0, 3.48)], AW0, AW1, "x", mi=AWNING)
NS = 16
pitch = (AW1 - AW0) / NS
LOBE = [(0.0, 2.52), (0.12, 2.44), (0.28, 2.395), (0.5, 2.38), (0.72, 2.395), (0.88, 2.44)]   # (t, z)
edge = []                                     # the valance's lower edge, west to east
for k in range(NS):
    x0 = AW0 + k * pitch
    edge += [(x0 + t * pitch, z) for t, z in LOBE]
edge += [(AW1, 2.52)]
P.prism([(AW1, 2.71), (AW0, 2.71)] + edge, AW_FRONT - 0.01, AW_FRONT, "y", mi=AWNING)
# fringe: one flat saw-tooth strip per lobe, 4 mm in front of the valance (the canvas material
# exports double-sided), 0.03 wide teeth hanging 0.07 below the edge
FR_LEN, FR_W = 0.07, 0.03


def edge_z(x):
    for (xa, za), (xb, zb) in zip(edge, edge[1:]):
        if xa <= x <= xb:
            return za + (zb - za) * (x - xa) / (xb - xa)
    return edge[-1][1]


for k in range(NS):
    xa, xb = AW0 + k * pitch + 0.01, AW0 + (k + 1) * pitch - 0.01
    n_t = max(2, int((xb - xa) / FR_W))
    xs = [xa + (xb - xa) * i / n_t for i in range(n_t + 1)]
    top = [(x, edge_z(x) + 0.02) for x in reversed(xs)]
    teeth = []
    for i in range(n_t):
        xm = (xs[i] + xs[i + 1]) / 2
        teeth += [(xs[i], edge_z(xs[i]) - 0.005), (xm, edge_z(xm) - FR_LEN)]
    teeth.append((xs[-1], edge_z(xs[-1]) - 0.005))
    P.face(teeth + top, AW_FRONT - 0.014, "y", -1, AWNING)
# side curtains: canvas panels in the awning's end planes, from the front edge back 0.65 m
for xc in (AW0, AW1):
    s = 1 if xc > 0 else -1
    z_top = lambda y: 3.50 + 0.80 * y / 1.90
    P.prism([(AW_FRONT, SHOP_FL + 1.00), (AW_FRONT + 0.65, SHOP_FL + 1.06),
             (AW_FRONT + 0.65, z_top(AW_FRONT + 0.65)), (AW_FRONT, z_top(AW_FRONT))],
            xc, xc + s * 0.01, "x", mi=AWNING)

# ---------------------------------------------------------------------------
# Build objects (union the central section, boolean the openings)
# ---------------------------------------------------------------------------


def build_shell(name):
    walls = SHELL.to_object(name, col)
    add = ADD.to_object(name + "_Add", col)
    cutters = CUT.to_object(name + "_Cutters", col)
    solvers = [i.identifier for i in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items]
    solver = "EXACT" if "EXACT" in solvers else solvers[0]
    m1 = walls.modifiers.new("Centre", "BOOLEAN")
    m1.operation = "UNION"
    m1.solver = solver
    m1.object = add
    m2 = walls.modifiers.new("Openings", "BOOLEAN")
    m2.operation = "DIFFERENCE"
    m2.solver = solver
    m2.use_self = True                      # nested frame/glass cutters overlap
    m2.material_mode = "INDEX"              # cutter faces keep their material index
    m2.object = cutters
    dg = bpy.context.evaluated_depsgraph_get()
    cut_mesh = bpy.data.meshes.new_from_object(walls.evaluated_get(dg))
    walls.modifiers.clear()
    old = walls.data
    walls.data = cut_mesh
    cut_mesh.name = name
    bpy.data.meshes.remove(old)
    bpy.data.objects.remove(cutters, do_unlink=True)
    bpy.data.objects.remove(add, do_unlink=True)
    return walls


build_shell("NV_Shell")
P.to_object("NV_Parts", col)

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Nevius Store built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)")
# Materials, baked lighting and GLB export: run nevius_store_bake.py (it runs this file first).
