"""
county_hotel.py - builds the County Hotel (47-49 Main St, Flemington; 3-storey Italianate
brick hotel with a full-width two-storey veranda, painted pale cream-buff by 1920) in Blender.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/county_hotel.py").read())

Every run deletes and rebuilds the "CountyHotel" collection. Materials, lightmap bake and GLB
export: county_hotel_bake.py (runs this file first). Pattern: rea_building.py (builders per
UV kind, Wall frames, shallow 0.30 m boolean recesses, atlas records).

Sources: PLAN.md "County Hotel (47-49 Main St)" spec (1921 Sanborn sheet 2 footprint and
height; proportions and details from the c. 1905 "Mount's Hotel" photo and the 1906 / 1908
cards, viewed online). Owner decisions 2026-11-04: pale painted walls, landmark detail,
<= 15k triangles.

Coordinates (metres, Blender Z-up), origin = centre of the veranda front line at sidewalk level:
    X  across the front, +X = north (39-41 Main), -X = south (open lot)
    Y  depth: y = 0 veranda front (property line), main front wall 2.52, rear wall 11.58,
       Bar & Pool Room wing to 26.00
    Z  up from the sidewalk / veranda paving top; walls skirt down to -0.20
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".

Eight materials: walls, trim, shutters, dark, brick, paving, clapboard, signs. Faces of the
"Atlas" builder carry a face attribute "rid" that tells the bake which atlas box they show.
"""

import math
import bpy
import bmesh

# ---------------------------------------------------------------------------
# Dimensions (PLAN.md)
# ---------------------------------------------------------------------------
HW = 11.93                 # half front (23.86 m)
FY, RY = 2.52, 11.58       # main front wall, rear wall
SKIRT = -0.20
TOP = 8.10                 # top of the wall shell (frieze band starts here)
RECESS = 0.30
CORN_IN = 0.35             # frieze / cornice rings reach this far into the wall
ROOF_Z = 9.04
POST_X = [-11.80 + 2.95 * k for k in range(9)]
BAY_C = [(a + b) / 2 for a, b in zip(POST_X, POST_X[1:])]
ENC_X = POST_X[7]          # enclosed north bay starts here (8.85)
WING = [(-HW, RY), (-5.55, RY), (-3.95, 26.00), (-9.95, 26.00)]
WING_Z = (3.60, 4.20)      # wall tops: south side, north side

# ---------------------------------------------------------------------------
# Materials (plain stand-ins; county_hotel_bake.py swaps in the textures)
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


COLOURS = {"Walls": "#d8cdb4", "Trim": "#e4ded0", "Shutters": "#34432f", "Dark": "#4a4c50",
           "Brick": "#8a4030", "Paving": "#8e8c86", "Clapboard": "#e5dfcc", "Signs": "#e4ded0"}
MATS = {k: plain("CH_" + k, c) for k, c in COLOURS.items()}
# builder -> material (the bake gives every builder its own UVs and tint)
BUILDER_MAT = {"Trim": "Trim", "Door": "Shutters", "Glass": "Dark", "Etched": "Dark", "Roof": "Dark",
               "Iron": "Dark", "Brick": "Brick", "Paving": "Paving", "Clap": "Clapboard", "Atlas": "Signs"}
SHELL_MAT = {"Shell": "Walls", "Bay": "Walls", "Frieze": "Trim", "Encl": "Trim"}

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

    def u_of(self, x, y):
        return (x - self.p0[0]) * self.t[0] + (y - self.p0[1]) * self.t[1]


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
        bm = self.bm
        loops = []
        for r, z in rings:
            if r < 1e-6:
                loops.append([bm.verts.new((cx, cy, z))])
            else:
                loops.append([bm.verts.new((cx + r * math.cos(2 * math.pi * (i + rot) / sides),
                                            cy + r * math.sin(2 * math.pi * (i + rot) / sides), z))
                              for i in range(sides)])
        faces = []
        if len(loops[0]) > 1:
            faces.append(bm.faces.new(list(reversed(loops[0]))))
        if len(loops[-1]) > 1:
            faces.append(bm.faces.new(loops[-1]))
        for a, b in zip(loops, loops[1:]):
            for i in range(sides):
                j = (i + 1) % sides
                if len(a) == 1:
                    faces.append(bm.faces.new([a[0], b[j], b[i]]))
                elif len(b) == 1:
                    faces.append(bm.faces.new([a[i], a[j], b[0]]))
                else:
                    faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
        self._closed(faces)

    def ring_z(self, outer, inner, z0, z1):
        """Closed horizontal ring between two plan outlines (same point count), z0 .. z1."""
        bm = self.bm
        o0 = [bm.verts.new((x, y, z0)) for x, y in outer]
        o1 = [bm.verts.new((x, y, z1)) for x, y in outer]
        i0 = [bm.verts.new((x, y, z0)) for x, y in inner]
        i1 = [bm.verts.new((x, y, z1)) for x, y in inner]
        n = len(outer)
        faces = []
        for i in range(n):
            j = (i + 1) % n
            faces += [bm.faces.new([o1[i], o1[j], i1[j], i1[i]]), bm.faces.new([o0[i], i0[i], i0[j], o0[j]]),
                      bm.faces.new([o0[i], o0[j], o1[j], o1[i]]), bm.faces.new([i0[i], i1[i], i1[j], i0[j]])]
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


def u_shape(cu, hw, f, z0, z1):
    """Outline of a frame: two jambs f wide (outside hw) and a head over z1 (an upside-down U)."""
    return [(cu - hw - f, z0), (cu - hw, z0), (cu - hw, z1), (cu + hw, z1), (cu + hw, z0), (cu + hw + f, z0),
            (cu + hw + f, z1 + f), (cu - hw - f, z1 + f)]


def offset_line(poly, p):
    """Open polyline (x, y), outside on the right; offset outward by p (mitred)."""
    n = len(poly)
    norms = []
    for i in range(n - 1):
        dx, dy = poly[i + 1][0] - poly[i][0], poly[i + 1][1] - poly[i][1]
        L = math.hypot(dx, dy)
        norms.append((dy / L, -dx / L))
    out = []
    for i, (x, y) in enumerate(poly):
        if i == 0:
            nx, ny = norms[0]
            out.append((x + p * nx, y + p * ny))
        elif i == n - 1:
            nx, ny = norms[-1]
            out.append((x + p * nx, y + p * ny))
        else:
            a, b = norms[i - 1], norms[i]
            k = 1 + a[0] * b[0] + a[1] * b[1]
            out.append((x + p * (a[0] + b[0]) / k, y + p * (a[1] + b[1]) / k))
    return out


def clip_poly(poly, a, b, c):
    """Keep the part of a convex polygon [(u, z)] where a*u + b*z <= c (Sutherland-Hodgman)."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp <= 0:
            out.append(p)
        if (fp < 0 < fq) or (fq < 0 < fp):
            t = fp / (fp - fq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def poly_area(p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2

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


col = fresh_collection("CountyHotel")
G = {k: MB() for k in BUILDER_MAT}
T, DR, GL, ET, R, IR, B, PV, CL, AT = (G[k] for k in ("Trim", "Door", "Glass", "Etched", "Roof", "Iron", "Brick",
                                                       "Paving", "Clap", "Atlas"))
SHELL, CUT = MB(), MB()          # painted brick main block and its openings
BAY, CUT_B = MB(), MB()          # canted 1-storey bay on the south side
FRIEZE, CUT_F = MB(), MB()       # main frieze band with sunk panels
ENCL, CUT_E = MB(), MB()         # enclosed north veranda bay (boarded / glazed)

ATLAS = {}                       # rid -> record (read by county_hotel_bake.py)


def atlas_rec(**kw):
    rid = len(ATLAS) + 1
    ATLAS[rid] = kw
    AT.rid = rid
    return rid


def wall_rec(w):
    return (w.p0, w.n)


FRONT = Wall((0.0, FY), (0, -1), CUT)          # u = x
SOUTH = Wall((-HW, 0.0), (-1, 0), CUT)         # u = -y
NORTH = Wall((HW, 0.0), (1, 0), CUT)           # u = y
REAR = Wall((0.0, RY), (0, 1), CUT)            # u = -x

# ---------------------------------------------------------------------------
# Shell: main block, skirt to the frieze band
# ---------------------------------------------------------------------------
SHELL.prism(rect(-HW, HW, FY, RY), SKIRT, TOP, axis="z")

# ---------------------------------------------------------------------------
# Windows and doors
# ---------------------------------------------------------------------------


def shutters(wall, cu, hw, z0, z1, leaf, off=0.11):
    """Open louvred shutters flat beside an opening (atlas louvres, dark green)."""
    for s in (-1, 1):
        u0, u1 = sorted((cu + s * (hw + off), cu + s * (hw + off + leaf)))
        atlas_rec(region="louvre", edge="green", mode="rect", wall=wall_rec(wall), u0=u0, u1=u1, z0=z0, z1=z1)
        AT.wbox(wall, u0, u1, z0, z1, 0.035, 0.065)
    AT.rid = 0


def window(wall, cu, z0, w, h, shut=0.0, full=True, recess=RECESS, head=True, muntin=True, sill=True):
    """2/2 sash window in a recess: dark glass, frame, sash rails, muntin, plain casing 0.10,
    head cap, sill; optional open louvred shutters (leaf width `shut`).
    full=False: plain side/rear window (glass, meeting rail, muntin, sill)."""
    hw, z1 = w / 2, z0 + h
    wall.cut.wbox(wall, cu - hw, cu + hw, z0, z1, -recess, 0.25)
    gd = -recess + 0.07
    GL.wbox(wall, cu - hw, cu + hw, z0, z1, gd - 0.02, gd)
    zm = (z0 + z1) / 2 + 0.03
    if full:
        T.wprism(wall, u_shape(cu, hw - 0.05, 0.05, z0, z1 - 0.05), gd, gd + 0.06)     # sash frame
        T.wbox(wall, cu - hw + 0.05, cu + hw - 0.05, z0, z0 + 0.07, gd, gd + 0.05)     # bottom rail
        T.wprism(wall, u_shape(cu, hw, 0.10, z0, z1), -0.01, 0.035)                  # casing
        if head:
            T.wbox(wall, cu - hw - 0.16, cu + hw + 0.16, z1 + 0.10, z1 + 0.17, -0.01, 0.08)
    T.wbox(wall, cu - hw + 0.03, cu + hw - 0.03, zm - 0.03, zm + 0.03, gd, gd + 0.05)   # meeting rail
    if muntin:
        T.wbox(wall, cu - 0.018, cu + 0.018, z0 + 0.05, z1 - 0.05, gd, gd + 0.035)
    if sill:
        e = hw + (0.13 if full else 0.06)
        T.wbox(wall, cu - e, cu + e, z0 - 0.07, z0, -recess + 0.08, 0.07)
    if shut:
        shutters(wall, cu, hw, z0, z1, shut, off=0.11 if full else 0.03)


def door(wall, cu, z0, w, h, leaves=1, glass_from=None, transom=0.0, recess=RECESS, casing_top=None,
         etched=False, step=True):
    """Panelled door (one or two leaves) in a recess: dark green leaves with raised lower
    panels, optional glazed upper panels, transom light, plain casing, one stone step."""
    hw, z1 = w / 2, z0 + h
    zt = z1 + transom
    wall.cut.wbox(wall, cu - hw, cu + hw, z0, zt, -recess, 0.25)
    ld = -recess + 0.08                                    # leaf front face
    lw = w / leaves
    for k in range(leaves):
        a, b = cu - hw + k * lw, cu - hw + (k + 1) * lw
        DR.wbox(wall, a, b, z0, z1, ld - 0.05, ld)
        gz = glass_from if glass_from else z1
        for za, zb in ((z0 + 0.15, min(gz, z0 + 0.95) - 0.10),) + (((z0 + 1.05, gz - 0.10),) if gz > z0 + 1.30 else ()):
            DR.wbox(wall, a + 0.09, b - 0.09, za, zb, ld, ld + 0.015)                # raised panels
        if glass_from:
            (ET if etched else GL).wbox(wall, a + 0.09, b - 0.09, glass_from, z1 - 0.12, ld - 0.02, ld + 0.005)
    if transom:
        T.wbox(wall, cu - hw, cu + hw, z1, z1 + 0.05, ld - 0.05, ld + 0.01)
        GL.wbox(wall, cu - hw, cu + hw, z1 + 0.05, zt, ld - 0.05, ld - 0.03)
    casing = u_shape(cu, hw, 0.12, z0, zt)
    if casing_top:                                         # main door: casing stops under the deck
        casing[6], casing[7] = (cu + hw + 0.12, casing_top), (cu - hw - 0.12, casing_top)
    T.wprism(wall, casing, -0.01, 0.04)
    if step:
        PV.wbox(wall, cu - hw - 0.15, cu + hw + 0.15, SKIRT, z0, -recess, 0.32)


# --- main front, ground floor (behind the veranda) -------------------------------------
window(FRONT, -10.88, 0.60, 1.60, 1.90, muntin=False)                         # display window
door(FRONT, -9.40, 0.15, 0.90, 2.30, glass_from=1.45)
window(FRONT, BAY_C[1], 1.10, 0.90, 1.70, shut=0.45)
door(FRONT, BAY_C[2], 0.15, 1.30, 2.60, leaves=2, glass_from=1.20, transom=0.17, casing_top=2.99, etched=True)
for x in BAY_C[3:7]:
    window(FRONT, x, 1.10, 0.90, 1.70, shut=0.45)
# --- 2nd floor: windows in bays 1, 3, 5, 7, glazed doors onto the deck in 2, 4, 6 ---------
for i, x in enumerate(BAY_C[:7]):
    if i % 2 == 0:
        window(FRONT, x, 3.60, 0.85, 1.70, shut=0.425)
    else:
        door(FRONT, x, 3.10, 0.85, 2.30, glass_from=4.00, step=False)
# --- 3rd floor: 12 shuttered windows ------------------------------------------------------
THIRD_X = [-10.94 + 1.99 * k for k in range(12)]
for x in THIRD_X:
    window(FRONT, x, 6.70, 0.80, 1.20, shut=0.40)

# --- south side (open lot): 3 / 2 / 1 windows ---------------------------------------------
SOUTH_Y3, SOUTH_Y2 = (3.6, 6.9, 10.1), (3.6, 10.1)
for y in SOUTH_Y3:
    window(SOUTH, -y, 6.70, 0.80, 1.20, shut=0.40)
for y in SOUTH_Y2:
    window(SOUTH, -y, 3.60, 0.85, 1.70, shut=0.425)
window(SOUTH, -3.6, 1.10, 0.90, 1.70, shut=0.45)
# --- north side: only the top floor shows above 39-41 (7 m) ----------------------------------
for y in (3.6, 6.9, 10.1):
    window(NORTH, y, 6.70, 0.80, 1.20, full=False)
# --- rear: 5 + 4 windows above the wing, 2 on the ground north of it (plain) ----------------
for x in (-9.5, -4.75, 0.0, 4.75, 9.5):
    window(REAR, -x, 6.70, 0.80, 1.20, full=False)
for x in (-3.5, 0.5, 4.5, 8.5):
    window(REAR, -x, 3.60, 0.85, 1.70, full=False)
for x in (2.0, 7.0):
    window(REAR, -x, 1.10, 0.90, 1.70, full=False)

# ---------------------------------------------------------------------------
# South-wall canted bay (1 storey)
# ---------------------------------------------------------------------------
BAY_LINE = [(-HW, 11.43), (-13.13, 10.38), (-13.13, 8.30), (-HW, 7.00)]       # outside on the right
BAY_PLAN = [(-11.80, 11.544)] + BAY_LINE + [(-11.80, 6.859)]
BAY.prism(BAY_PLAN, SKIRT, 3.30, axis="z")
for (xa, ya), (xb, yb) in zip(BAY_LINE, BAY_LINE[1:]):
    L = math.hypot(xb - xa, yb - ya)
    n = ((yb - ya) / L, -(xb - xa) / L)
    w = Wall(((xa + xb) / 2, (ya + yb) / 2), n, CUT_B)
    if L > 2.0:
        window(w, 0.0, 1.10, 1.10, 1.70, head=False)
    else:
        window(w, 0.0, 1.10, 0.60, 1.70, shut=0.30, head=False)
for p, z0, z1 in ((0.04, 3.18, 3.30), (0.16, 3.30, 3.42), (0.22, 3.42, 3.50)):
    outer, inner = offset_line(BAY_LINE, p), offset_line(BAY_LINE, -0.15)
    T.prism(outer + inner[::-1], z0, z1, axis="z")
R.prism(BAY_PLAN, 3.30, 3.46, axis="z")

# ---------------------------------------------------------------------------
# Veranda: paving, posts, deck, railing, porch entablature, roof, enclosed north bay
# ---------------------------------------------------------------------------
PV.box(-HW, HW, 0.0, FY, SKIRT, 0.0)

for k, x in enumerate(POST_X):
    T.box(x - 0.16, x + 0.16, -0.03, 0.29, 0.0, 0.10)                          # plinth
    atlas_rec(region="post2", mode="post", cx=x, cy=0.13, hw=0.13, z0=0.10, z1=2.68)
    AT.box(x - 0.13, x + 0.13, 0.0, 0.26, 0.10, 2.68)
    atlas_rec(region="post1", mode="post", cx=x, cy=0.13, hw=0.12, z0=3.10, z1=5.63)
    AT.box(x - 0.12, x + 0.12, 0.01, 0.25, 3.10, 5.63)
    AT.rid = 0
    for z0, z1, zc0, zc1 in ((2.68, 2.73, 2.73, 2.80), (5.63, 5.68, 5.68, 5.75)):     # moulded caps
        T.box(x - 0.15, x + 0.15, -0.02, 0.28, z0, z1)
        T.box(x - 0.17, x + 0.17, -0.04, 0.30, zc0, zc1)

# deck: fascia beam across the front and the south end, slab behind
T.box(-HW, HW, 0.0, 0.26, 2.80, 3.10)
T.box(-HW, -HW + 0.26, 0.26, FY, 2.80, 3.10)
T.box(-HW + 0.26, HW, 0.26, FY, 3.00, 3.10)


def lattice(wall, ua, ub, za=3.26, zb=3.94, pitch=0.25, half=0.02):
    """Diamond lattice of crossed diagonal slats (0.04 x 0.03) between two rails."""
    box = rect(ua - 0.01, ub + 0.01, za - 0.02, zb + 0.02)
    cu, cz = (ua + ub) / 2, (za + zb) / 2
    h = half * math.sqrt(2)
    for s, d0, d1 in ((1, -0.03, 0.0), (-1, 0.0, 0.03)):
        base = cu - s * cz
        lo = min(ua - s * za, ua - s * zb, ub - s * za, ub - s * zb)
        hi = max(ua - s * za, ua - s * zb, ub - s * za, ub - s * zb)
        k0, k1 = math.floor((lo - base) / pitch) - 1, math.ceil((hi - base) / pitch) + 1
        for k in range(k0, k1 + 1):
            c = base + k * pitch
            poly = clip_poly(box, 1, -s, c + h)
            poly = clip_poly(poly, -1, s, -(c - h)) if poly else poly
            if len(poly) >= 3 and poly_area(poly) > 0.002:
                T.wprism(wall, poly, d0, d1)


def railing(wall, ua, ub):
    T.wbox(wall, ua, ub, 3.94, 4.00, -0.05, 0.05)
    T.wbox(wall, ua, ub, 3.20, 3.26, -0.05, 0.05)
    lattice(wall, ua, ub)


RAIL_F = Wall((0.0, 0.13), (0, -1))
for a, b in zip(POST_X[:7], POST_X[1:8]):
    railing(RAIL_F, a + 0.12, b - 0.12)
RAIL_S = Wall((POST_X[0], 0.0), (-1, 0))               # u = -y
railing(RAIL_S, -FY, -0.25)

# porch entablature: frieze boards, scroll brackets, cornice, tin roof sloping to the wall
T.box(-HW, HW, 0.0, 0.22, 5.75, 6.25)
T.box(-HW, -HW + 0.22, 0.22, FY, 5.75, 6.25)
T.box(HW - 0.22, HW, 0.22, FY, 5.75, 6.25)
PORCH_BR = [(0.0, 6.25), (0.30, 6.25), (0.30, 6.20), (0.22, 6.16), (0.14, 6.12), (0.10, 6.03), (0.08, 5.93),
            (0.05, 5.84), (0.03, 5.80), (0.0, 5.80)]
PF = Wall((0.0, 0.0), (0, -1))
for k in range(25):
    x = -11.80 + 23.60 * k / 24
    T.oprism(PF, PORCH_BR, x - 0.05, x + 0.05)
for wall in (Wall((-HW, 0.0), (-1, 0)), Wall((HW, 0.0), (1, 0))):
    for y in (0.75, 1.50, 2.25):
        u = wall.u_of(-HW if wall.n[0] < 0 else HW, y)
        T.oprism(wall, PORCH_BR, u - 0.05, u + 0.05)
T.box(-HW - 0.30, HW + 0.30, -0.30, FY, 6.25, 6.33)                            # soffit / corona
T.box(-HW - 0.33, HW + 0.33, -0.33, FY, 6.33, 6.40)                            # crown
R.prism([(-0.33, 6.40), (FY, 6.40), (FY, 6.57), (-0.33, 6.43)], -HW - 0.33, HW + 0.33, axis="x")

# enclosed north bay: boarded ground floor, glazed upper room on a panelled dado
ENCL.box(ENC_X, HW, 0.10, FY, 0.0, 3.00)
ENCL.box(ENC_X, HW, 0.10, FY, 3.10, 5.75)
EF = Wall((0.0, 0.10), (0, -1), CUT_E)                  # u = x
EN = Wall((HW, 0.0), (1, 0), CUT_E)                     # u = y
ES = Wall((ENC_X, 0.0), (-1, 0), CUT_E)                 # u = -y
window(EF, 10.39, 1.10, 0.90, 1.70, recess=0.10, head=False)
window(EN, 1.31, 1.10, 0.90, 1.70, recess=0.10, head=False)
for x in (9.62, 11.16):
    window(EF, x, 3.92, 0.90, 1.80, recess=0.10, head=False, sill=False)
for y in (0.78, 1.86):
    window(EN, y, 3.92, 0.85, 1.80, recess=0.10, head=False, sill=False)
for wall, (ua, ub) in ((EF, (ENC_X + 0.13, HW)), (EN, (0.26, FY)), (ES, (-FY, -0.26))):
    T.wbox(wall, ua, ub, 0.0, 0.18, -0.01, 0.03)                               # base board
    T.wbox(wall, ua, ub, 0.95, 1.02, -0.01, 0.04)                              # chair rail
    T.wbox(wall, ua, ub, 3.85, 3.92, -0.01, 0.06)                              # dado cap / sill
for x in (9.62, 11.16):
    T.wbox(EF, x - 0.42, x + 0.42, 3.22, 3.75, 0.0, 0.02)                      # raised dado panels
for y in (0.78, 1.86):
    T.wbox(EN, y - 0.40, y + 0.40, 3.22, 3.75, 0.0, 0.02)
for ua, ub in ((-2.30, -1.45), (-1.25, -0.40)):
    T.wbox(ES, ua, ub, 3.22, 3.75, 0.0, 0.02)
    T.wbox(ES, ua, ub, 1.20, 2.60, 0.0, 0.02)
    T.wbox(ES, ua, ub, 0.30, 0.85, 0.0, 0.02)
T.wbox(EF, ENC_X + 0.25, 9.80, 0.30, 0.85, 0.0, 0.02)
T.wbox(EF, 11.00, 11.75, 0.30, 0.85, 0.0, 0.02)

# ---------------------------------------------------------------------------
# Main entablature: frieze with sunk panels, scroll brackets, cornice rings; roof; chimneys
# ---------------------------------------------------------------------------


def grow(p):
    return [(-HW - p, FY - p), (HW + p, FY - p), (HW + p, RY + p), (-HW - p, RY + p)]


T.ring_z(grow(0.09), grow(-CORN_IN), 8.02, 8.10)                                # architrave fillet
FRIEZE.ring_z(grow(0.05), grow(-CORN_IN), 8.10, 8.75)
for p, z0, z1 in ((0.50, 8.75, 8.80), (0.58, 8.80, 8.98), (0.65, 8.98, 9.08), (0.60, 9.08, 9.15)):
    T.ring_z(grow(p), grow(-CORN_IN), z0, z1)
MAIN_BR = [(0.0, 8.75), (0.48, 8.75), (0.48, 8.68), (0.38, 8.62), (0.25, 8.58), (0.18, 8.47), (0.15, 8.33),
           (0.11, 8.21), (0.07, 8.15), (0.0, 8.15)]
FRONT_BR = [-11.81, -11.61] + [-11.61 + 23.22 * k / 21 for k in range(1, 21)] + [11.61, 11.81]
SIDE_BR = [2.64, 2.84] + [2.84 + 1.078 * k for k in range(1, 8)]
FW = Wall((0.0, FY), (0, -1), CUT_F)
SW = Wall((-HW, 0.0), (-1, 0), CUT_F)
NW = Wall((HW, 0.0), (1, 0), CUT_F)
for wall, us in ((FW, FRONT_BR), (SW, [-y for y in SIDE_BR]), (NW, SIDE_BR)):
    us = sorted(us)
    for u in us:
        T.oprism(wall, MAIN_BR, u - 0.06, u + 0.06)
    for a, b in zip(us, us[1:]):
        if b - a > 0.5:
            wall.cut.wbox(wall, a + 0.16, b - 0.16, 8.24, 8.64, 0.03, 0.30)     # sunk frieze panel
R.prism(grow(-CORN_IN), ROOF_Z - 0.06, ROOF_Z, axis="z")

for sx in (-1, 1):                                                              # chimneys, Y 4.5
    x0, x1 = sorted((sx * (HW - 0.50), sx * HW))
    B.box(x0, x1, 4.05, 4.95, 8.60, 10.14)
    B.box(x0 - 0.04, x1 + 0.04, 4.01, 4.99, 10.14, 10.22)
    B.box(x0, x1, 4.05, 4.95, 10.22, 10.30)
    IR.box(x0 + 0.10, x1 - 0.10, 4.20, 4.80, 10.29, 10.31)                    # flue opening

# ---------------------------------------------------------------------------
# Bar & Pool Room wing (1-storey clapboard, shed roof falling south)
# ---------------------------------------------------------------------------
wz = [WING_Z[0], WING_Z[1], WING_Z[1], WING_Z[0]]
CL._extrude([(x, y, SKIRT) for x, y in WING], [(x, y, z) for (x, y), z in zip(WING, wz)])
CL.rid = 0
eave = [(-HW - 0.25, RY), (-5.55 + 0.25, RY), (-3.95 + 0.25, 26.25), (-9.95 - 0.25, 26.25)]
ez = [WING_Z[0] - 0.02, WING_Z[1] + 0.02, WING_Z[1] + 0.02, WING_Z[0] - 0.02]
R._extrude([(x, y, z) for (x, y), z in zip(eave, ez)], [(x, y, z + 0.08) for (x, y), z in zip(eave, ez)])
# south face: 2 windows and a door with a step (surface-mounted frames on the clapboard)
(xa, ya), (xb, yb) = WING[0], WING[3]
L = math.hypot(xb - xa, yb - ya)
WS = Wall((xa, ya), (-(yb - ya) / L, (xb - xa) / L))                          # u = -(distance along +Y)
for s in (4.0, 11.0):
    u = -s
    GL.wbox(WS, u - 0.45, u + 0.45, 1.10, 2.70, -0.02, 0.01)
    T.wprism(WS, u_shape(u, 0.45, 0.10, 1.10, 2.70), -0.01, 0.04)
    T.wbox(WS, u - 0.45, u + 0.45, 1.88, 1.94, 0.0, 0.03)
    T.wbox(WS, u - 0.58, u + 0.58, 1.03, 1.10, -0.01, 0.08)
s = (19.0 - RY) / (yb - ya) * L
DR.wbox(WS, -s - 0.45, -s + 0.45, 0.15, 2.25, -0.02, 0.03)
T.wprism(WS, u_shape(-s, 0.45, 0.10, 0.15, 2.25), -0.01, 0.05)
PV.wbox(WS, -s - 0.60, -s + 0.60, SKIRT, 0.15, -0.01, 0.40)

# ---------------------------------------------------------------------------
# Cast-iron lamp standard with a lettered lantern (south end, in front of the veranda)
# ---------------------------------------------------------------------------
LX, LY = -9.90, -0.60
IR.lathe(LX, LY, [(0.17, -0.05), (0.17, 0.08), (0.15, 0.12), (0.14, 0.45), (0.10, 0.52), (0.05, 0.60),
                  (0.045, 2.88), (0.08, 2.92), (0.08, 3.00)], sides=8, rot=0.0)
IR.box(LX - 0.22, LX + 0.22, LY - 0.22, LY + 0.22, 3.00, 3.05)
IR.box(LX - 0.22, LX + 0.22, LY - 0.22, LY + 0.22, 3.65, 3.70)
for sx in (-1, 1):
    for sy in (-1, 1):
        IR.box(LX + sx * 0.20 - 0.02, LX + sx * 0.20 + 0.02, LY + sy * 0.20 - 0.02, LY + sy * 0.20 + 0.02, 3.05, 3.65)
atlas_rec(region="lantern", mode="post", cx=LX, cy=LY, hw=0.18, z0=3.05, z1=3.65)
AT.box(LX - 0.18, LX + 0.18, LY - 0.18, LY + 0.18, 3.05, 3.65)
AT.rid = 0
IR.lathe(LX, LY, [(0.33, 3.70), (0.0, 3.95)], sides=4, rot=0.5)                # pyramid cap
IR.lathe(LX, LY, [(0.03, 3.94), (0.03, 3.98), (0.0, 3.985), (0.06, 4.03), (0.0, 4.10)], sides=6)

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


cut_shell(SHELL, CUT, "CH_Shell", "Walls")
cut_shell(BAY, CUT_B, "CH_Bay", "Walls")
cut_shell(FRIEZE, CUT_F, "CH_Frieze", "Trim")
cut_shell(ENCL, CUT_E, "CH_Encl", "Trim")
for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("CH_" + key, MATS[BUILDER_MAT[key]], col)
    else:
        builder.bm.free()

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("County Hotel built:", len(col.objects), "objects,", tris, "triangles (before hidden-face removal)",
      "| atlas records", len(ATLAS))
# Materials, baked lighting and GLB export: run county_hotel_bake.py (it runs this file first).
