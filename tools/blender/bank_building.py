"""
bank_building.py - builds the Bank Building / Flemington National Bank ("Richards Building",
56-66 Main St, Flemington, 1897, as it stood c. 1920) in Blender.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/bank_building.py").read())

Every run deletes and rebuilds the "BankBuilding" collection, so edit the numbers below and
run again. Materials, lightmap bake and GLB export: bank_building_bake.py (runs this first).
Pattern: county_offices.py / wurts_law_office.py.

Sources: PLAN.md "Bank Building / Flemington National Bank" spec and its orchestrator
decisions (1921 Sanborn sheet 2; the 1906/1907/1908 postcards): one continuous 3-storey
facade on an L-shaped plan, rock-faced stone ground storey with 6 bays (bank window, arched
bank entrance with stoop and railings, four shop fronts with awnings), stone belt course,
12 brick upper bays on the front and 11 on the Bloomfield Ave side (rectangular 2nd-floor
windows with pale lintels, round-arched 3rd-floor windows, roundels), panelled frieze and
modillion cornice.

Only 6 materials (= 6 draw calls), in this slot order on every part:
    0 Brick, 1 Stone, 2 Trim, 3 Glass, 4 Dark, 5 Awning
Shells and boolean cutters carry a material index per face; the boolean copies the cutter's
index onto the faces it creates, so reveals, frames and glass need no extra geometry.

Coordinates (metres, Blender Z-up):
    X  along the front, +X = south (towards 68 Main), -X = north (Bloomfield Ave)
    Y  depth: y = 0 is the front (ground-storey stone) wall face; stoops run out to -1.8,
       awnings to -1.77, the cornice to -0.8. North part rear y = 20.32, south part 11.05.
    Z  up from the sidewalk top; walls skirt down to -0.20.
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".
"""

import math
import bpy
import bmesh

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md)
# ---------------------------------------------------------------------------
HW = 11.07             # half front (22.14 m)
BN = 20.32             # rear of the north part (56-58)
BS = 11.05             # rear of the south part (62-66)
XC = 0.39              # courtyard face of the north part (x), from y = BS to BN
GF = 0.90              # raised ground floor
BELT0, BELT1 = 4.30, 4.60
ROOF_F, ROOF_R = 11.40, 10.60      # shed roofs, front and rear edge (hidden behind the cornice)
PIL_TOP, CAP_TOP = 10.45, 10.60
FRIEZE0, FRIEZE1 = 10.60, 11.45
CORN_TOP = 12.20
SKIRT = -0.20

BAY = 1.712                                     # front upper bays
FRONT_WIN = [(-11 + 2 * i) * BAY / 2 for i in range(12)]          # +-0.856 ... +-9.416
FRONT_PIL = [k * BAY for k in range(-5, 6)]                        # 0, +-1.712 ... +-8.560
SBAY = 1.72                                     # north (Bloomfield) side bays
SIDE_WIN = [1.66 + SBAY * k for k in range(11)]
SIDE_PIL = [0.80 + SBAY * k for k in range(1, 11)]

W2, S2, H2 = 0.95, 5.00, 6.95                    # 2nd floor windows
W3, S3, SP3 = 0.95, 7.75, 9.30                   # 3rd floor arched windows (crown 9.775)
ROUNDEL_Z = 10.15

BRICK, STONE, TRIM, GLASS, DARK, AWNING = range(6)
NAMES = ["Brick", "Stone", "Trim", "Glass", "Dark", "Awning"]

# ---------------------------------------------------------------------------
# Materials (plain stand-ins; bank_building_bake.py swaps in the textures)
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


COLOURS = ["#8a4030", "#a8a294", "#b5ac98", "#1e2226", "#3a2a1f", "#9a4a3e"]
MATS = [plain("BK_" + n, c) for n, c in zip(NAMES, COLOURS)]

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


def circle(cu, cv, r, segs=8):
    return [(cu + r * math.cos(2 * math.pi * (i + 0.5) / segs), cv + r * math.sin(2 * math.pi * (i + 0.5) / segs))
            for i in range(segs)]


def roof_z(x, y):
    """Shed roofs: north part falls over 20.32 m, south part over 11.05 m."""
    depth = BN if x < XC - 1e-6 else BS
    return ROOF_F - (ROOF_F - ROOF_R) * y / depth


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


col = fresh_collection("BankBuilding")
P = MB()                       # all added parts
GROUND, CUT_G = MB(), MB()     # ground storey shell (stone front/north, brick elsewhere)
UPPER, CUT_U = MB(), MB()      # upper storeys + roof shell (brick, dark roof)

# Each wall: (axis, outer face depth, outward sign)
FRONT = ("y", 0.0, -1)
NORTH = ("x", -HW, -1)
REAR_N = ("y", BN, 1)
REAR_S = ("y", BS, 1)
COURT = ("x", XC, 1)


def Dfun(wall):
    axis, face, out = wall
    return axis, (lambda k: face + out * k)   # k > 0 outside the wall, k < 0 inside


def cutter(z_top):
    return CUT_G if z_top <= BELT0 + 1e-6 else CUT_U


# ---------------------------------------------------------------------------
# Shells
# ---------------------------------------------------------------------------

L_PLAN = [(-HW, 0), (XC, 0), (HW, 0), (HW, BS), (XC, BS), (XC, BN), (-HW, BN)]
GROUND.prism(L_PLAN, SKIRT, BELT0, axis="z", mi=STONE)


def upper_shell():
    """Closed L-shaped solid from the belt course up to the two shed roofs."""
    bm = UPPER.bm
    B = [bm.verts.new((x, y, BELT0)) for x, y in L_PLAN]           # B0..B6
    Tn0 = bm.verts.new((-HW, 0, ROOF_F))
    Tn1 = bm.verts.new((XC, 0, ROOF_F))
    Tn4 = bm.verts.new((XC, BS, roof_z(-1, BS)))
    Tn5 = bm.verts.new((XC, BN, ROOF_R))
    Tn6 = bm.verts.new((-HW, BN, ROOF_R))
    Ts2 = bm.verts.new((HW, 0, ROOF_F))
    Ts3 = bm.verts.new((HW, BS, ROOF_R))
    Ts4 = bm.verts.new((XC, BS, ROOF_R))
    spec = [
        (list(reversed(B)), BRICK),                         # bottom (hidden)
        ([Tn0, Tn1, Tn4, Tn5, Tn6], DARK),                  # north roof
        ([Tn1, Ts2, Ts3, Ts4], DARK),                       # south roof
        ([Tn1, Ts4, Tn4], BRICK),                           # step between the roofs
        ([B[0], B[1], B[2], Ts2, Tn1, Tn0], BRICK),         # front
        ([B[2], B[3], Ts3, Ts2], BRICK),                    # south
        ([B[3], B[4], Ts4, Ts3], BRICK),                    # south part rear
        ([B[4], B[5], Tn5, Tn4, Ts4], BRICK),               # courtyard
        ([B[5], B[6], Tn6, Tn5], BRICK),                    # north part rear
        ([B[6], B[0], Tn0, Tn6], BRICK),                    # north (Bloomfield)
    ]
    faces = []
    for verts, mi in spec:
        f = bm.faces.new(verts)
        f.material_index = mi
        faces.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=faces)


upper_shell()

# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------
FR = 0.07          # frame width
D_FRAME = 0.08     # frame face behind the wall face
D_GLASS = 0.15     # glass behind the wall face


def framed_opening(wall, outer, inner, wall_mat, z_top, d_frame=D_FRAME, d_glass=D_GLASS):
    """Two nested cutters: the outer pocket's reveal keeps the wall material and its back
    becomes the painted frame; the inner pocket's sides are frame, its back is the glass."""
    axis, D = Dfun(wall)
    C = cutter(z_top)
    C.prism(outer, D(0.25), D(-d_frame), axis, mi=(wall_mat, TRIM, wall_mat))
    C.prism(inner, D(0.25), D(-d_glass), axis, mi=(TRIM, GLASS, TRIM))


def sill(wall, cu, w, z, mat=TRIM, thick=0.08, proj=0.06):
    axis, D = Dfun(wall)
    P.prism(rect(cu - w / 2 - 0.08, cu + w / 2 + 0.08, z - thick + 0.02, z + 0.02), D(proj), D(-D_FRAME), axis, mi=mat)


def rect_window(wall, cu, w, z0, z1, wall_mat=BRICK, lintel=True, muntin=False, sill_mat=TRIM):
    axis, D = Dfun(wall)
    framed_opening(wall, rect(cu - w / 2, cu + w / 2, z0, z1),
                   rect(cu - w / 2 + FR, cu + w / 2 - FR, z0 + FR, z1 - FR), wall_mat, z1)
    zm = (z0 + z1) / 2 + 0.05
    P.prism(rect(cu - w / 2 + FR, cu + w / 2 - FR, zm - 0.03, zm + 0.03), D(-0.10), D(-D_GLASS), axis, mi=TRIM)
    if muntin:     # 2/2 sash
        P.prism(rect(cu - 0.015, cu + 0.015, z0 + FR, z1 - FR), D(-0.12), D(-D_GLASS), axis, mi=TRIM)
    sill(wall, cu, w, z0, sill_mat)
    if lintel:     # flat pale lintel 1.25 x 0.30, 0.04 proud
        P.prism(rect(cu - 0.625, cu + 0.625, z1, z1 + 0.30), D(0.04), D(0.0), axis, mi=TRIM)


def arched_window(wall, cu, w=W3, z0=S3, zs=SP3, segs=6):
    axis, D = Dfun(wall)
    r = w / 2
    framed_opening(wall, arched(cu, w, z0, zs, segs), arched(cu, w - 2 * FR, z0 + FR, zs, segs), BRICK, zs + r)
    zm = (z0 + zs) / 2 + 0.05
    P.prism(rect(cu - r + FR, cu + r - FR, zm - 0.03, zm + 0.03), D(-0.10), D(-D_GLASS), axis, mi=TRIM)
    sill(wall, cu, w, z0)
    # brick hood ring 0.15 wide, 0.05 proud, and a small pale keystone
    P.arc_band(cu, zs, r, r + 0.15, 0.0, math.pi, D(0.05), D(0.0), axis, segs=segs, mi=BRICK)
    crown = zs + r
    P.prism([(cu - 0.08, crown - 0.04), (cu + 0.08, crown - 0.04), (cu + 0.10, crown + 0.26), (cu - 0.10, crown + 0.26)],
            D(0.075), D(0.0), axis, mi=TRIM)


def simple_opening(wall, cu, w, z0, z1, side_mat, back_mat, depth=0.15):
    axis, D = Dfun(wall)
    cutter(z1).prism(rect(cu - w / 2, cu + w / 2, z0, z1), D(0.25), D(-depth), axis, mi=(side_mat, back_mat, side_mat))


# --- upper floors: front (12 bays) and north side (11 bays) ---
for wall, centres in ((FRONT, FRONT_WIN), (NORTH, SIDE_WIN)):
    for cu in centres:
        rect_window(wall, cu, W2, S2, H2)
        arched_window(wall, cu)


def pilaster(wall, u0, u1, z0=BELT1, z1=PIL_TOP, proud=0.08):
    axis, D = Dfun(wall)
    P.prism(rect(u0, u1, z0, z1), D(proud), D(0.0), axis, mi=BRICK)
    P.prism(rect(u0 - 0.08, u1 + 0.08, z1, CAP_TOP), D(proud + 0.04), D(0.0), axis, mi=BRICK)   # corbelled cap


for x in FRONT_PIL:
    pilaster(FRONT, x - 0.325, x + 0.325)
for y in SIDE_PIL:
    pilaster(NORTH, y - 0.325, y + 0.325)
# corner piers run full height as pilasters: NW (wraps the corner), SW, rear of the north side
P.box(-HW - 0.08, -10.27, -0.08, 0.0, BELT1, PIL_TOP, mi=BRICK)
P.prism(rect(0.0, 0.80, BELT1, PIL_TOP), -HW - 0.08, -HW, axis="x", mi=BRICK)
P.box(-HW - 0.12, -10.19, -0.12, 0.0, PIL_TOP, CAP_TOP, mi=BRICK)
P.prism(rect(0.0, 0.88, PIL_TOP, CAP_TOP), -HW - 0.12, -HW, axis="x", mi=BRICK)
P.box(10.27, HW, -0.08, 0.0, BELT1, PIL_TOP, mi=BRICK)
P.box(10.19, HW, -0.12, 0.0, PIL_TOP, CAP_TOP, mi=BRICK)
P.prism(rect(BN - 0.60, BN, BELT1, PIL_TOP), -HW - 0.08, -HW, axis="x", mi=BRICK)
P.prism(rect(BN - 0.68, BN, PIL_TOP, CAP_TOP), -HW - 0.12, -HW, axis="x", mi=BRICK)

# roundels (8-sided pale discs) on the pilaster faces, one centred over each ground bay
for x in (-8.560, -5.136, -1.712, 1.712, 5.136, 8.560):
    P.prism(circle(x, ROUNDEL_Z, 0.275), -0.14, -0.08, "y", mi=TRIM)
for k in (0, 2, 4, 6, 8):
    P.prism(circle(SIDE_PIL[k], ROUNDEL_Z, 0.275), -HW - 0.14, -HW - 0.08, "x", mi=TRIM)

# ---------------------------------------------------------------------------
# Belt course, frieze, cornice (plan bands on the front + full north side, with returns
# of 0.8 m round the SW corner and the rear (NE) corner of the north side)
# ---------------------------------------------------------------------------


def band(p, ret=0.8):
    return [(-HW - p, -p), (HW + p, -p), (HW + p, ret), (HW, ret), (HW, 0.0), (-HW, 0.0),
            (-HW, BN), (-HW + ret, BN), (-HW + ret, BN + p), (-HW - p, BN + p)]


P.prism([(-HW - 0.12, -0.12), (HW, -0.12), (HW, 0.0), (-HW, 0.0), (-HW, BN), (-HW - 0.12, BN)],
        BELT0, BELT1, axis="z", mi=STONE)                        # belt course, ends flush
P.prism(band(0.10), FRIEZE0, FRIEZE1, axis="z", mi=TRIM)         # frieze
P.prism(band(0.22), FRIEZE1, FRIEZE1 + 0.10, axis="z", mi=TRIM)  # bed moulding
P.prism(band(0.16), FRIEZE1 + 0.10, 11.75, axis="z", mi=TRIM)    # band behind the modillions
P.prism(band(0.75), 11.75, 12.12, axis="z", mi=TRIM)             # corona
P.prism(band(0.80), 12.12, CORN_TOP, axis="z", mi=TRIM)          # cap moulding

# frieze panels: two per bay, 0.35 x 0.45, 0.02 proud
FZ = (FRIEZE0 + FRIEZE1) / 2
for x in FRONT_WIN:
    for s in (-0.428, 0.428):
        P.box(x + s - 0.175, x + s + 0.175, -0.12, -0.10, FZ - 0.225, FZ + 0.225, mi=TRIM)
for y in SIDE_WIN:
    for s in (-0.43, 0.43):
        P.prism(rect(y + s - 0.175, y + s + 0.175, FZ - 0.225, FZ + 0.225), -HW - 0.12, -HW - 0.10, "x", mi=TRIM)

# modillions: 0.12 w x 0.20 h x 0.40 deep, 0.57 m centres (3 per bay) under the corona
MZ0, MZ1 = 11.55, 11.75
for x in FRONT_WIN:
    for s in (-0.57, 0.0, 0.57):
        P.box(x + s - 0.06, x + s + 0.06, -0.56, -0.16, MZ0, MZ1, mi=TRIM)
for x in (-10.67, 10.67):
    P.box(x - 0.06, x + 0.06, -0.56, -0.16, MZ0, MZ1, mi=TRIM)
for y in SIDE_WIN:
    for s in (-0.57, 0.0, 0.57):
        P.prism(rect(y + s - 0.06, y + s + 0.06, MZ0, MZ1), -HW - 0.56, -HW - 0.16, "x", mi=TRIM)
for y in (0.40, BN - 0.30):
    P.prism(rect(y - 0.06, y + 0.06, MZ0, MZ1), -HW - 0.56, -HW - 0.16, "x", mi=TRIM)
P.prism(rect(0.40 - 0.06, 0.40 + 0.06, MZ0, MZ1), HW + 0.56, HW + 0.16, "x", mi=TRIM)   # SW return
P.box(-HW + 0.40 - 0.06, -HW + 0.40 + 0.06, BN + 0.16, BN + 0.56, MZ0, MZ1, mi=TRIM)   # NE return

# chimney on the south wall near the front, flush outside, rising from the roof
bm = P.bm
cx0, cx1, cy0, cy1, ctop = HW - 0.55, HW, 1.15, 2.05, 13.10      # cap to 13.20 (review round 1, 1908 SW card)
cv = [bm.verts.new((x, y, roof_z(HW, y) if z is None else z))
      for z in (None, ctop) for x, y in ((cx0, cy0), (cx1, cy0), (cx1, cy1), (cx0, cy1))]
cf = [bm.faces.new([cv[i] for i in idx]) for idx in
      ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))]
for f in cf:
    f.material_index = BRICK
bmesh.ops.recalc_face_normals(bm, faces=cf)
P.box(cx0 - 0.10, cx1 + 0.10, cy0 - 0.10, cy1 + 0.10, ctop, ctop + 0.10, mi=DARK)       # cap course

# ---------------------------------------------------------------------------
# Ground storey: front
# ---------------------------------------------------------------------------

# stone piers 0.80 wide, 0.04 proud, at the corners and between the ground bays
for x in (-6.848, -3.424, 0.0, 3.424, 6.848):
    P.box(x - 0.40, x + 0.40, -0.04, 0.0, SKIRT, BELT0, mi=STONE)
P.box(-HW - 0.04, -10.27, -0.04, 0.0, SKIRT, BELT0, mi=STONE)
P.prism(rect(0.0, 0.80, SKIRT, BELT0), -HW - 0.04, -HW, axis="x", mi=STONE)
P.box(10.27, HW, -0.04, 0.0, SKIRT, BELT0, mi=STONE)

# G1: bank window 2.0 x 2.5 (4 lights), stone sill and flush lintel, basement window below
c = (-10.27 - 7.248) / 2
framed_opening(FRONT, rect(c - 1.0, c + 1.0, 1.20, 3.70), rect(c - 0.92, c + 0.92, 1.28, 3.62), STONE, 3.70,
               d_frame=0.10, d_glass=0.20)
P.box(c - 0.06, c + 0.06, 0.12, 0.20, 1.28, 3.62, mi=TRIM)                       # mullion
P.box(c - 0.92, c + 0.92, 0.12, 0.20, 3.07, 3.13, mi=TRIM)                       # transom bar
P.box(c - 1.10, c + 1.10, -0.06, 0.10, 1.10, 1.22, mi=STONE)                     # sill
P.box(c - 1.15, c + 1.15, -0.02, 0.0, 3.70, 4.05, mi=STONE)                      # lintel
simple_opening(FRONT, c, 1.2, 0.25, 0.70, STONE, GLASS, 0.12)                    # basement light

# G2: round-arched bank entrance, recessed 0.45, double doors, fanlight, voussoirs
c = -5.136
R = 0.75
SPR = 3.05
CUT_G.prism(arched(c, 1.5, GF, SPR, 10), -0.25, 0.45, "y", mi=(STONE, GLASS, STONE))
P.arc_band(c, SPR, R, R + 0.30, 0.0, math.pi, -0.04, 0.0, "y", segs=10, mi=STONE)   # voussoir ring
P.prism([(c - 0.12, SPR + R - 0.03), (c + 0.12, SPR + R - 0.03), (c + 0.16, SPR + R + 0.36), (c - 0.16, SPR + R + 0.36)],
        -0.08, 0.0, "y", mi=STONE)                                                  # keystone
P.box(c - R, c - R + 0.08, 0.37, 0.45, GF, SPR, mi=TRIM)                          # door frame
P.box(c + R - 0.08, c + R, 0.37, 0.45, GF, SPR, mi=TRIM)
P.arc_band(c, SPR, R - 0.08, R, 0.0, math.pi, 0.37, 0.45, "y", segs=10, mi=TRIM)
P.box(c - R + 0.08, c + R - 0.08, 0.38, 0.45, 2.80, 2.92, mi=TRIM)               # transom bar
for a in (math.pi / 4, math.pi / 2, 3 * math.pi / 4):                             # fanlight bars
    ca, sa = math.cos(a), math.sin(a)
    nx, nz = -sa * 0.02, ca * 0.02
    x1, z1 = c + (R - 0.08) * ca, SPR + (R - 0.08) * sa
    P.prism([(c + nx, SPR + nz), (c - nx, SPR - nz), (x1 - nx, z1 - nz), (x1 + nx, z1 + nz)], 0.41, 0.45, "y", mi=TRIM)
P.box(c - R + 0.08, c + R - 0.08, 0.41, 0.45, SPR - 0.02, SPR + 0.02, mi=TRIM)    # fanlight sill bar
inner = 2 * (R - 0.08)
for i in range(2):                                                                  # two leaves 0.90-2.80
    x0 = c - inner / 2 + i * inner / 2 + 0.005
    x1 = x0 + inner / 2 - 0.01
    P.box(x0, x1, 0.40, 0.45, GF, 2.80, mi=DARK)
    P.box(x0 + 0.08, x1 - 0.08, 0.385, 0.40, GF + 0.15, GF + 0.85, mi=DARK)         # raised lower panel
    P.box(x0 + 0.08, x1 - 0.08, 0.395, 0.40, GF + 1.05, 2.68, mi=GLASS)             # glazed upper panel

# bank stoop: 5 risers x 0.18, 4 treads x 0.30 (y -1.80 ... -0.60), landing to the wall,
# stone cheek walls 0.25 with sloping tops, one black iron handrail on each cheek
RIS = GF / 5


bank_prof = [(-1.80, SKIRT), (-1.80, RIS)]
for k in range(1, 5):
    y = -1.80 + 0.30 * k
    bank_prof += [(y, RIS * k), (y, RIS * (k + 1))]
bank_prof += [(0.0, GF), (0.0, SKIRT)]
P.prism(bank_prof, c - 0.80, c + 0.80, "x", mi=STONE)
CHEEK_B = [(-1.80, SKIRT), (-1.80, 0.50), (-0.60, 1.30), (0.0, 1.30), (0.0, SKIRT)]
for s in (-1, 1):
    x0, x1 = sorted((c + s * 0.80, c + s * 1.05))
    P.prism(CHEEK_B, x0, x1, "x", mi=STONE)
    xm = c + s * 0.925
    zc = lambda y: 0.50 + 0.80 * (y + 1.80) / 1.20       # cheek top on the slope
    P.prism(rect(-1.745, -1.695, zc(-1.72), zc(-1.72) + 0.80), xm - 0.025, xm + 0.025, "x", mi=DARK)   # posts
    P.prism(rect(-0.125, -0.075, 1.30, 2.10), xm - 0.025, xm + 0.025, "x", mi=DARK)
    P.prism([(-1.745, zc(-1.745) + 0.775), (-0.60, 2.075), (-0.075, 2.075), (-0.075, 2.125), (-0.60, 2.125),
             (-1.745, zc(-1.745) + 0.825)], xm - 0.02, xm + 0.02, "x", mi=DARK)                           # rail

# G3-G6: shop fronts in the 2.62 m openings, recessed entrance, display windows, transoms,
# fascia, small stone stoops with cheek walls, striped awnings
SHOP_D = 0.20          # shop front plane behind the stone face
REC_D = 0.90           # entrance recess depth
OP_TOP = 4.22          # top of the shop opening (stone above, then the belt course)
SHOP_STOOP = [(-1.20, SKIRT)]
for k in range(4):
    SHOP_STOOP += [(-1.20 + 0.30 * k, RIS * (k + 1)), (-1.20 + 0.30 * (k + 1), RIS * (k + 1))]
SHOP_STOOP += [(0.0, SKIRT)]
CHEEK_S = [(-1.20, SKIRT), (-1.20, 0.40), (0.0, 1.05), (0.0, SKIRT)]


def display(x0, x1):
    """Display window between x0 and x1 on the shop front plane: bulkhead panel, glass,
    rail, 3-light transom."""
    yb = SHOP_D
    P.box(x0 + 0.08, x1 - 0.08, yb - 0.02, yb, GF + 0.12, 1.20, mi=TRIM)            # raised bulkhead panel
    P.box(x0, x1, yb - 0.04, yb, 1.26, 1.32, mi=TRIM)                               # sill rail
    P.box(x0, x1, yb - 0.03, yb, 1.32, 3.20, mi=GLASS)                              # display glass
    P.box(x0, x1, yb - 0.06, yb, 3.20, 3.26, mi=TRIM)                               # transom rail
    P.box(x0, x1, yb - 0.02, yb, 3.26, 3.56, mi=GLASS)                              # transom lights
    for k in (1, 2):
        xb = x0 + (x1 - x0) * k / 3
        P.box(xb - 0.02, xb + 0.02, yb - 0.04, yb - 0.02, 3.26, 3.56, mi=TRIM)


def shop(x0, x1, dc, side_door=False):
    axis, D = Dfun(FRONT)
    CUT_G.prism(rect(x0, x1, GF, OP_TOP), -0.25, SHOP_D, "y", mi=(STONE, TRIM, STONE))
    CUT_G.prism(rect(dc - 0.5, dc + 0.5, GF, 3.60), -0.25, REC_D, "y",
                mi=(TRIM, TRIM, [STONE, TRIM, TRIM, TRIM]))                          # recess, stone floor
    # corner posts and fascia
    P.box(x0, x0 + 0.08, SHOP_D - 0.08, SHOP_D, GF, 3.60, mi=TRIM)
    P.box(x1 - 0.08, x1, SHOP_D - 0.08, SHOP_D, GF, 3.60, mi=TRIM)
    P.box(x0, x1, SHOP_D - 0.10, SHOP_D, 3.60, OP_TOP - 0.02, mi=TRIM)
    if dc - 0.5 - (x0 + 0.08) > 0.2:
        display(x0 + 0.08, dc - 0.5)
    if (x1 - 0.08) - (dc + 0.5) > 0.2:
        display(dc + 0.5, x1 - 0.08)
    # half-glazed door 0.95 x 2.30 at the back of the recess, transom over it
    P.box(dc - 0.475, dc + 0.475, REC_D - 0.05, REC_D, GF, 3.20, mi=DARK)
    P.box(dc - 0.36, dc + 0.36, REC_D - 0.065, REC_D - 0.05, GF + 1.15, 3.05, mi=GLASS)
    P.box(dc - 0.33, dc + 0.33, REC_D - 0.065, REC_D - 0.05, GF + 0.15, GF + 0.95, mi=DARK)
    P.box(dc - 0.45, dc + 0.45, REC_D - 0.02, REC_D, 3.26, 3.54, mi=GLASS)
    if side_door:      # G6: door to the upper floors in the recess's south side wall
        P.prism(rect(0.12, 0.82, GF, 3.10), dc + 0.5 - 0.05, dc + 0.5, "x", mi=DARK)
        P.prism(rect(0.22, 0.72, GF + 1.25, 2.95), dc + 0.5 - 0.065, dc + 0.5 - 0.05, "x", mi=GLASS)
    # stoop in the recess line, cheek walls 0.20 each side
    P.prism(SHOP_STOOP, dc - 0.5, dc + 0.5, "x", mi=STONE)
    for s in (-1, 1):
        a, b = sorted((dc + s * 0.5, dc + s * 0.7))
        P.prism(CHEEK_S, a, b, "x", mi=STONE)
    # striped awning: from under the belt course out 1.75 m, with a 0.25 m valance
    P.prism([(0.0, 4.15), (-1.75, 3.05), (-1.75, 2.80), (-1.77, 2.80), (-1.77, 3.07), (0.0, 4.18)],
            x0 - 0.05, x1 + 0.05, "x", mi=AWNING)


shop(-3.024, -0.40, -1.712)
shop(0.40, 3.024, 1.712)
shop(3.824, 6.448, 5.136)
shop(7.248, 10.27, 9.37, side_door=True)          # G6: display 1.62 m on the north, recess to the south

# ---------------------------------------------------------------------------
# Ground storey: north (Bloomfield) side - one tall 2/2 window per bay, basement lights
# ---------------------------------------------------------------------------
for y in SIDE_WIN:
    rect_window(NORTH, y, 0.95, 1.00, 3.60, wall_mat=STONE, lintel=False, muntin=True, sill_mat=STONE)
    simple_opening(NORTH, y, 0.80, 0.15, 0.55, STONE, GLASS, 0.12)

# ---------------------------------------------------------------------------
# Rear and courtyard walls (never photographed): plain recessed windows, one back door each
# ---------------------------------------------------------------------------
FLOORS = ((1.30, 3.50), (5.10, 6.90), (7.80, 9.60))
for wall, xs, door_x in ((REAR_N, (-9.5, -6.6, -3.7, -0.8), -0.8), (REAR_S, (2.4, 5.7, 9.0), 2.4)):
    for x in xs:
        for i, (z0, z1) in enumerate(FLOORS):
            if i == 0 and x == door_x:
                simple_opening(wall, x, 0.9, 0.0, 2.1, BRICK, DARK, 0.12)
            else:
                simple_opening(wall, x, 0.9, z0, z1 if i else z0 + 2.2, BRICK, GLASS)
for y in (13.7, 17.6):
    for z0, z1 in FLOORS[1:]:
        simple_opening(COURT, y, 0.9, z0, z1, BRICK, GLASS)

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


ground = cut_shell(GROUND, CUT_G, "BK_Ground")
# the ground storey is rock-faced stone on the front and the Bloomfield side only: south,
# rear and courtyard walls are common brick
for p in ground.data.polygons:
    if p.material_index != STONE:
        continue
    c, n = p.center, p.normal
    if (abs(c.x - HW) < 0.01 and n.x > 0.9) or (abs(c.y - BS) < 0.01 and n.y > 0.9) or \
       (abs(c.x - XC) < 0.01 and n.x > 0.9) or (abs(c.y - BN) < 0.01 and n.y > 0.9):
        p.material_index = BRICK
cut_shell(UPPER, CUT_U, "BK_Upper")
P.to_object("BK_Parts", col)

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Bank Building built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)")
# Materials, baked lighting and GLB export: run bank_building_bake.py (it runs this file first).
