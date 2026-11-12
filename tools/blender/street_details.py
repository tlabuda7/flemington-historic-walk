"""
Street details kit, pass 2 batch B (Main Street, Flemington, c. 1920) - geometry.

Run in Blender (Z up, metres):
    exec(open(r"<project>/tools/blender/street_details.py").read())

PLAN.md "Street details pass 2", sections 4 and 6, build split B, as approved by the owner on
2026-11-11. Unlike the pass-1 kit (street_props.py) everything here is PLACED: built in scene
coordinates (Blender X = scene x, Blender Y = -scene z, Blender Z = height), one object per
placed thing or fence run, each with its origin at its own anchor (listed in ANCHORS). The scene
entity sits at "0 0 0".

  fence-59-wurts      woven-wire hoop-top fence, 0.9 m, in front of the Wurts Law Office, with
                      thin iron line posts and two square white gate posts at the open walk; the
                      north post carries a turned urn (PHOTO: flmngtnmainstdrtompkinsoffice.jpg;
                      line posts TYPICAL, the photo shows no panel post)
  fence-65-picket     white picket fence, 1.0 m, square posts with chamfered caps, two rails,
                      pointed pickets, a picket gate at the path (PHOTO: 1908 "north from hotel")
  post-stone-39       pale square stone post 0.30 x 1.2 m between 65 Main and the County Offices
  fence-69-pipe-rail  iron post-and-single-pipe-rail fence, 0.7 m, County Offices, open at the
                      three walks with 3 m returns (PHOTO: 1908-1912 County Building cards)
  fence-69-board      2.0 m vertical-board fence with a ledged door, between the County Offices
                      and the courthouse (PHOTO: 1909 / 1912 cards)
  hedge-rea           clipped hedge along the Rea Building's Bloomfield Ave wall (PHOTO: 1910
                      colour card): lumpy core + leaf cards
  waste-paper-box     dark box lettered FOR / WASTE / PAPER at the Rea north stoop (PHOTO:
                      Stryker plate; colour guess dark green)
  barber-pole-72      striped barber pole with ball top on a plinth, foot of the Union Hotel
                      steps (MAP 1921 "Barber" + form from the Stryker plate; colours TYPICAL)

Every face carries one of six materials (filled in by street_details_bake.py) and a "UVMap":
box UVs in metres (world-continuous) or atlas UVs (details_atlas.jpg regions, see
tools/prepare_street_details_textures.py). A float colour attribute "Tint" (multiplied into the
lightmap by the bake) separates dark iron from galvanised wire etc.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise

ROOT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
COLL = "street_details"

MATS = ["sd_paint_white", "sd_metal", "sd_wood_weathered", "sd_stone", "sd_atlas", "sd_hedge_cutout"]
MI = {n: i for i, n in enumerate(MATS)}
VIEW = {"sd_paint_white": (0.85, 0.84, 0.80), "sd_metal": (0.25, 0.25, 0.25), "sd_wood_weathered": (0.45, 0.44, 0.40),
        "sd_stone": (0.62, 0.60, 0.56), "sd_atlas": (0.2, 0.3, 0.2), "sd_hedge_cutout": (0.15, 0.35, 0.1)}
TILE = {"sd_paint_white": 1.0, "sd_metal": 0.6, "sd_wood_weathered": 2.0, "sd_stone": 1.0}

# Tints (linear multipliers baked into the lightmap)
T_WIRE = (1.45, 1.45, 1.48)       # wire: mid-grey (galvanised or grey paint; photo)
T_IRON = (0.80, 0.80, 0.80)       # dark painted iron (pipe rail, posts, hinges)
T_NONE = (1.0, 1.0, 1.0)


def P(x, z, h):
    """scene (x, z, height) -> Blender vector"""
    return Vector((x, -z, h))


# ----------------------------------------------------------------------------------------------
# builder
# ----------------------------------------------------------------------------------------------
class Builder:
    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.tint = self.bm.loops.layers.float_color.new("Tint")
        self.expl = self.bm.faces.layers.int.new("explicit_uv")
        self.cur_tint = T_NONE

    def face(self, verts, mat, smooth=False, uvs=None):
        f = self.bm.faces.new(verts)
        f.material_index = MI[mat]
        f.smooth = smooth
        for lp in f.loops:
            lp[self.tint] = (*self.cur_tint, 1.0)
        if uvs is not None:
            for lp, uv in zip(f.loops, uvs):
                lp[self.uv].uv = uv
            f[self.expl] = 1
        return f

    def V(self, co):
        return self.bm.verts.new(co)

    def quad_box(self, corners, mat, skip=(), smooth=False):
        """8 corners in the order of a unit box: index bits x(1) y(2) z(4)."""
        vs = [self.V(c) for c in corners]
        F = {"-Z": (0, 2, 3, 1), "+Z": (4, 5, 7, 6), "-Y": (0, 1, 5, 4), "+Y": (2, 6, 7, 3),
             "-X": (0, 4, 6, 2), "+X": (1, 3, 7, 5)}
        out = {}
        for k, idx in F.items():
            if k in skip:
                continue
            out[k] = self.face([vs[i] for i in idx], mat, smooth)
        return out

    def box(self, x0, x1, y0, y1, z0, z1, mat, skip=("-Z",)):
        """axis box in Blender coordinates"""
        c = [Vector((x1 if i & 1 else x0, y1 if i & 2 else y0, z1 if i & 4 else z0)) for i in range(8)]
        return self.quad_box(c, mat, skip)

    def prism(self, poly, z0, z1, mat, skip_bottom=True, smooth=False, top=True):
        """vertical prism: poly = [(x, y)] counter-clockwise from above (Blender XY)"""
        n = len(poly)
        lo = [self.V((x, y, z0)) for x, y in poly]
        hi = [self.V((x, y, z1)) for x, y in poly]
        for i in range(n):
            j = (i + 1) % n
            self.face((lo[i], lo[j], hi[j], hi[i]), mat, smooth)
        if top:
            self.face(hi, mat)
        if not skip_bottom:
            self.face(lo[::-1], mat)
        return lo, hi

    def loft(self, rings, mat, smooth=False, cap_top=False, closed=True):
        """connect rings of equal length (each counter-clockwise seen from outside-top)"""
        for a, b in zip(rings[:-1], rings[1:]):
            n = len(a)
            for i in range(n if closed else n - 1):
                j = (i + 1) % n
                self.face((a[i], a[j], b[j], b[i]), mat, smooth)
        if cap_top:
            self.face(rings[-1], mat)

    def lathe(self, prof, n, mat, centre, smooth=True, uvfn=None, phase=0.0):
        """revolve (r, z) around a vertical axis at centre (Blender XY + z offset). r == 0 = apex.
        uvfn(k, j) -> (u, v) gives explicit UVs (a seam column j = n is added)."""
        cx, cy, cz = centre
        cols = n + 1 if uvfn else n
        rings = []
        for k, (r, z) in enumerate(prof):
            if r < 1e-9:
                rings.append(None)
                continue
            ring = []
            for j in range(cols):
                a = phase + 2 * math.pi * (j % n) / n
                ring.append(self.V((cx + r * math.cos(a), cy + r * math.sin(a), cz + z)))
            rings.append(ring)
        apex = {}
        for k, (r, z) in enumerate(prof):
            if rings[k] is None:
                apex[k] = self.V((cx, cy, cz + z))
        for k in range(len(prof) - 1):
            A, B = rings[k], rings[k + 1]
            for j in range(n):
                j2 = j + 1 if uvfn else (j + 1) % n
                uvs = None
                if A is None and B is None:
                    continue
                if A is None:
                    vs = (apex[k], B[j2], B[j])
                    if uvfn:
                        uvs = (uvfn(k, j + 0.5), uvfn(k + 1, j + 1), uvfn(k + 1, j))
                elif B is None:
                    vs = (A[j], A[j2], apex[k + 1])
                    if uvfn:
                        uvs = (uvfn(k, j), uvfn(k, j + 1), uvfn(k + 1, j + 0.5))
                else:
                    vs = (A[j], A[j2], B[j2], B[j])
                    if uvfn:
                        uvs = (uvfn(k, j), uvfn(k, j + 1), uvfn(k + 1, j + 1), uvfn(k + 1, j))
                self.face(vs, mat, smooth, uvs)
        if uvfn:   # weld the seam column so shading stays smooth; UVs stay split per loop
            for ring in rings:
                if ring:
                    bmesh.ops.pointmerge(self.bm, verts=[ring[0], ring[-1]], merge_co=ring[0].co)

    def tube(self, pts, r, n, mat, closed=False, phase=0.0, nrm=None):
        P_ = [Vector(p) for p in pts]
        cnt = len(P_)
        tans = []
        for i in range(cnt):
            if closed:
                d = P_[(i + 1) % cnt] - P_[i - 1]
            else:
                d = P_[min(i + 1, cnt - 1)] - P_[max(i - 1, 0)]
            tans.append(d.normalized())
        N = Vector(nrm) if nrm else (Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0)))
        N = (N - tans[0] * N.dot(tans[0])).normalized()
        rings = []
        for i in range(cnt):
            t = tans[i]
            if i > 0:
                N = (N - t * N.dot(t)).normalized()
            Bv = t.cross(N)
            rings.append([self.V(P_[i] + r * (math.cos(phase + 2 * math.pi * j / n) * N +
                                               math.sin(phase + 2 * math.pi * j / n) * Bv)) for j in range(n)])
        segs = cnt if closed else cnt - 1
        for i in range(segs):
            A, B = rings[i], rings[(i + 1) % cnt]
            for j in range(n):
                j2 = (j + 1) % n
                self.face((A[j], A[j2], B[j2], B[j]), mat, True)
        return rings

    def sphere(self, c, r, nu, nv, mat):
        prof = [(0.0, -r)] + [(r * math.cos(a), r * math.sin(a))
                              for a in [-math.pi / 2 + math.pi * k / nv for k in range(1, nv)]] + [(0.0, r)]
        self.lathe(prof, nu, mat, (c[0], c[1], c[2]))


def box_uvs(B, offset=Vector()):
    """world-metre box projection for faces without explicit UVs"""
    for f in B.bm.faces:
        if f[B.expl]:
            continue
        mat = MATS[f.material_index]
        if mat == "sd_metal":          # plain colour, no map: one constant UV
            for lp in f.loops:
                lp[B.uv].uv = (0.5, 0.5)
            continue
        t = TILE.get(mat, 1.0)
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for lp in f.loops:
            p = lp.vert.co + offset
            if ax == 0:
                uv = (p.y * (1 if n.x > 0 else -1), p.z)
            elif ax == 1:
                uv = (p.x * (-1 if n.y > 0 else 1), p.z)
            else:
                uv = (p.x, p.y)
            lp[B.uv].uv = (uv[0] / t, uv[1] / t)


def chamfer_square(cx, cy, hw, c):
    """octagon (square with chamfered corners) counter-clockwise"""
    return [(cx - hw + c, cy - hw), (cx + hw - c, cy - hw), (cx + hw, cy - hw + c), (cx + hw, cy + hw - c),
            (cx + hw - c, cy + hw), (cx - hw + c, cy + hw), (cx - hw, cy + hw - c), (cx - hw, cy - hw + c)]


def atlas_uv(px0, py0, px1, py1, fu, fv, inset=2):
    """fraction (fu, fv) inside an atlas pixel rectangle (y down) -> UV"""
    x = px0 + inset + (px1 - px0 - 2 * inset) * fu
    y = py1 - inset - (py1 - py0 - 2 * inset) * fv
    return (x / 1024.0, 1.0 - y / 1024.0)


# ----------------------------------------------------------------------------------------------
# shared parts
# ----------------------------------------------------------------------------------------------
def square_post(B, x, z, w, h0, h1, mat, cap=None, chamf=0.012):
    """square post centred at scene (x, z), chamfered vertical edges; cap = 'pyramid' | 'flat' | None"""
    cx, cy = x, -z
    hw = w / 2
    B.prism(chamfer_square(cx, cy, hw, chamf), h0, h1, mat, top=cap is None)
    if cap == "pyramid":       # cap board, chamfered, then a low pyramid
        cw = hw + 0.015
        lo, hi = B.prism(chamfer_square(cx, cy, cw, 0.006), h1, h1 + 0.03, mat, top=False)
        inner = [B.V((cx + (px - cx) * 0.92, cy + (py - cy) * 0.92, h1 + 0.042)) for px, py in chamfer_square(cx, cy, cw, 0.006)]
        for i in range(8):
            j = (i + 1) % 8
            B.face((hi[i], hi[j], inner[j], inner[i]), mat)
        apex = B.V((cx, cy, h1 + 0.042 + hw * 0.55))
        for i in range(8):
            j = (i + 1) % 8
            B.face((inner[i], inner[j], apex), mat)
        return h1 + 0.042 + hw * 0.55
    if cap == "flat":          # cap board with chamfered top edge
        cw = hw + 0.02
        lo, hi = B.prism(chamfer_square(cx, cy, cw, 0.006), h1, h1 + 0.03, mat, top=False)
        top = [B.V((cx + (px - cx) * 0.88, cy + (py - cy) * 0.88, h1 + 0.045)) for px, py in chamfer_square(cx, cy, cw, 0.006)]
        for i in range(8):
            j = (i + 1) % 8
            B.face((hi[i], hi[j], top[j], top[i]), mat)
        B.face(top, mat)
        return h1 + 0.045
    return h1


# ----------------------------------------------------------------------------------------------
# 59 Main (Wurts): woven-wire hoop-top fence
# ----------------------------------------------------------------------------------------------
XW = -10.42                    # fence line (scene x)
WURTS_PATH_Z = -68.69
WURTS_N_END = -76.65           # 57 Main's built paving strip ends at z -76.73 (map lot line -78.5)
PICKET_N_END = -58.70          # 65 Main's corner post (shared)
GP_W = 0.18                    # gate posts
GP_S = WURTS_PATH_Z + 0.60 + GP_W / 2      # -67.99 (south post, flat cap)
GP_N = WURTS_PATH_Z - 0.60 - GP_W / 2      # -69.38 (north post, urn)


def wire_run(B, z0, z1, posts_at):
    """wire panel from z0 to z1 (z0 < z1, scene). Vertical wires every 0.10 m bend over into
    0.20 m round hoops (each wire is a leg of two overlapping hoops, alternate hoops 6 mm apart
    so they cross like the woven original); line wires at 0.62 and 0.06."""
    RW = 0.0024
    HS, R = 0.80, 0.10           # springing height, hoop radius (top at 0.90)
    n = int(round((z1 - z0 - 0.06) / 0.10)) + 1
    zs = [z0 + 0.03 + k * (z1 - z0 - 0.06) / (n - 1) for k in range(n)]
    B.cur_tint = T_WIRE
    for k, z in enumerate(zs):
        off = 0.003 if k % 2 else -0.003
        B.tube([P(XW + off, z, -0.04), P(XW + off, z, HS)], RW, 3, "sd_metal")
        if k + 2 < n:
            zc = (z + zs[k + 2]) / 2
            rr = (zs[k + 2] - z) / 2
            arc = [P(XW + off, zc - rr * math.cos(math.pi * s / 5), HS + rr * math.sin(math.pi * s / 5)) for s in range(6)]
            arc[0] = P(XW + off, z, HS - 0.004)
            arc[-1] = P(XW + off, zs[k + 2], HS - 0.004)
            B.tube(arc, RW, 3, "sd_metal")
    for h, r in ((0.62, 0.0032), (0.06, 0.0028)):
        B.tube([P(XW, z0 - 0.01, h), P(XW, z1 + 0.01, h)], r, 4, "sd_metal")
    B.cur_tint = T_IRON
    for z in posts_at:           # thin iron pipe line posts with a domed cap (TYPICAL)
        B.lathe([(0.021, -0.15), (0.021, 0.87), (0.026, 0.885), (0.0, 0.91)],
                6, "sd_metal", (XW - 0.03, z * -1, 0.0))
    B.cur_tint = T_NONE


def build_wurts():
    B = Builder()
    # north run: end post by 57 Main -> north gate post; south run: south gate post -> 65's post
    n0, n1 = WURTS_N_END, GP_N - GP_W / 2
    s0, s1 = GP_S + GP_W / 2, PICKET_N_END - 0.06
    def posts(a, b, end_post):
        k = max(1, math.ceil((b - a) / 2.4))
        ps = [a + (b - a) * i / k for i in range(1, k)]
        return ([a] if end_post else []) + ps
    wire_run(B, n0, n1, posts(n0, n1, True))
    wire_run(B, s0, s1, posts(s0, s1, False))
    # gate posts: square white wood 0.18, 1.05 high
    for z, kind in ((GP_S, "flat"), (GP_N, "urn")):
        top = square_post(B, XW, z, GP_W, -0.12, 1.0, "sd_paint_white", cap="flat", chamf=0.01)
        if kind == "urn":    # turned urn finial ~0.35 m on a small square plinth
            B.prism(chamfer_square(XW, -z, 0.06, 0.004), top, top + 0.03, "sd_paint_white", top=True)
            b = top + 0.03
            prof = [(0.0, 0.0), (0.055, 0.0), (0.055, 0.012), (0.030, 0.035), (0.040, 0.060),
                    (0.072, 0.100), (0.082, 0.145), (0.074, 0.190), (0.044, 0.228), (0.036, 0.245),
                    (0.052, 0.260), (0.046, 0.276), (0.026, 0.302), (0.012, 0.318), (0.018, 0.332),
                    (0.0, 0.346)]
            prof = [(r * 1.04, h * 0.82) for r, h in prof]
            B.lathe(prof, 12, "sd_paint_white", (XW, -z, b))
    return B


# ----------------------------------------------------------------------------------------------
# 65 Main: picket fence and gate
# ----------------------------------------------------------------------------------------------
XP = -10.44                     # post centre line (posts 0.12: x -10.50 ... -10.38)
H65_PATH_Z = -51.19
STONE_Z, STONE_X, STONE_W = -39.20, -10.46, 0.30
RAIL_H = (0.22, 0.80)


def picket(B, z, h0=0.04, top=1.0, x0=-10.340, t=0.022, w=0.06):
    """pointed picket, street face at x0 + t (scene x), centred on scene z"""
    sh = top - w / 2 * 0.9      # shoulder
    y0, y1 = -(z - w / 2), -(z + w / 2)   # Blender y (y1 < y0)
    xa, xb = x0, x0 + t
    # front (+X) and back (-X) pentagons
    fa = [B.V((xb, y1, h0)), B.V((xb, y0, h0)), B.V((xb, y0, sh)), B.V((xb, -z, top)), B.V((xb, y1, sh))]
    ba = [B.V((xa, y1, h0)), B.V((xa, y0, h0)), B.V((xa, y0, sh)), B.V((xa, -z, top)), B.V((xa, y1, sh))]
    B.face(fa, "sd_paint_white")
    # (no back face: visitors stay on the walk, the lawn side is never seen)
    for i in range(5):
        j = (i + 1) % 5
        if i == 0:
            continue             # bottom
        B.face((fa[i], ba[i], ba[j], fa[j]), "sd_paint_white")


def picket_run(B, za, zb):
    """pickets at 0.12 m centres between za and zb (scene, za < zb)"""
    n = int((zb - za - 0.06) / 0.12) + 1
    span = (n - 1) * 0.12
    z = za + (zb - za - span) / 2
    for i in range(n):
        picket(B, z + i * 0.12)


def rails(B, za, zb, x0=-10.38, x1=-10.34):
    for h in RAIL_H:
        B.box(x0, x1, -zb, -za, h - 0.04, h + 0.04, "sd_paint_white", skip=())


def build_65():
    B = Builder()
    g0, g1 = H65_PATH_Z - 0.62, H65_PATH_Z + 0.62     # gate post centres
    stone_face = STONE_Z - STONE_W / 2                  # -39.35
    north = [PICKET_N_END + (g0 - PICKET_N_END) * i / 3 for i in range(4)]
    south = [g1 + (stone_face - 0.02 - g1) * i / 5 for i in range(5)]   # last wood post before the stone
    for z in north + south:
        square_post(B, XP, z, 0.12, -0.12, 1.10, "sd_paint_white", cap="pyramid")
    # rails on the street face of the posts, pickets on the rails
    rails(B, PICKET_N_END - 0.06, g0 + 0.06)
    rails(B, g1 - 0.06, stone_face + 0.005)
    picket_run(B, PICKET_N_END - 0.03, g0 + 0.03)
    picket_run(B, g1 - 0.03, stone_face - 0.02)
    # gate leaf between the gate posts (hinged on the north post, closed): rails + brace behind
    la, lb = g0 + 0.06 + 0.012, g1 - 0.06 - 0.012
    for h in RAIL_H:
        B.box(-10.38, -10.34, -lb, -la, h - 0.04, h + 0.04, "sd_paint_white", skip=())
    # diagonal brace from the bottom rail at the hinge (north) side to the top rail at the latch side
    a = P(-10.36, la + 0.05, RAIL_H[0] + 0.03)
    b = P(-10.36, lb - 0.05, RAIL_H[1] - 0.03)
    d = (b - a).normalized()
    up = Vector((1, 0, 0)).cross(d).normalized()
    c = [a - up * 0.035, a + up * 0.035, b - up * 0.035, b + up * 0.035]
    corners = []
    for i in range(8):
        base = c[(1 if i & 4 else 0) + (2 if i & 2 else 0)]
        corners.append(base + Vector((0.02 if i & 1 else -0.02, 0, 0)))
    B.quad_box(corners, "sd_paint_white", skip=())
    n = int((lb - la - 0.06) / 0.12) + 1
    span = (n - 1) * 0.12
    for i in range(n):
        picket(B, la + (lb - la - span) / 2 + i * 0.12)
    return B


def build_stone_post():
    B = Builder()
    cx, cy, hw = STONE_X, -STONE_Z, STONE_W / 2
    lo, hi = B.prism(chamfer_square(cx, cy, hw, 0.015), -0.18, 1.12, "sd_stone", top=False)
    top = [B.V((cx + (x - cx) * 0.82, cy + (y - cy) * 0.82, 1.15)) for x, y in chamfer_square(cx, cy, hw, 0.015)]
    for i in range(8):
        j = (i + 1) % 8
        B.face((hi[i], hi[j], top[j], top[i]), "sd_stone")
    apex = B.V((cx, cy, 1.20))
    for i in range(8):
        B.face((top[i], top[(i + 1) % 8], apex), "sd_stone")
    rnd = random.Random(5)
    for v in B.bm.verts:
        if v.co.z > 0.0:
            v.co.x += rnd.uniform(-1, 1) * 0.004
            v.co.y += rnd.uniform(-1, 1) * 0.004
    return B


# ----------------------------------------------------------------------------------------------
# County Offices: iron post-and-pipe-rail fence with returns at the three walks
# ----------------------------------------------------------------------------------------------
XR = -10.42
CO_WALKS = (-31.67, -27.87, -24.07)
CO_SOUTH_END = -21.0


def build_pipe_rail():
    B = Builder()
    B.cur_tint = T_IRON
    RH, RR = 0.70, 0.02
    e = [w + s * 0.85 for w in CO_WALKS for s in (-1, 1)]       # opening edges
    segs = [(STONE_Z + STONE_W / 2 - 0.04, e[0], False, True), (e[1], e[2], True, True),
            (e[3], e[4], True, True), (e[5], CO_SOUTH_END, True, False)]
    corner_pts = []
    for za, zb, ret_a, ret_b in segs:
        path = []
        if ret_a:
            path.append(P(XR - 3.0, za, RH))
        path.append(P(XR, za, RH))
        path.append(P(XR, zb, RH))
        if ret_b:
            path.append(P(XR - 3.0, zb, RH))
        for a, b in zip(path[:-1], path[1:]):
            B.tube([a, b], RR, 6, "sd_metal")
        # posts: segment ends (not inside the stone post), every <= 2.4 m, and along the returns
        k = max(1, math.ceil(abs(zb - za) / 2.4))
        zs = [za + (zb - za) * i / k for i in range(k + 1)]
        if not ret_a:
            zs = zs[1:]
        for z in zs:
            B.box(XR - 0.025, XR + 0.025, -z - 0.025, -z + 0.025, -0.15, RH - 0.01, "sd_metal", skip=("-Z", "+Z"))
        for z, flag in ((za, ret_a), (zb, ret_b)):
            if flag:
                corner_pts.append((XR, z))
                for xx in (XR - 1.5, XR - 3.0):
                    B.box(xx - 0.025, xx + 0.025, -z - 0.025, -z + 0.025, -0.15, RH - 0.01, "sd_metal", skip=("-Z", "+Z"))
                B.sphere(P(XR - 3.0, z, RH), RR * 1.05, 6, 3, "sd_metal")      # end knob
        if not ret_b:
            B.sphere(P(XR, zb, RH), RR * 1.05, 6, 3, "sd_metal")
    for x, z in corner_pts:      # elbows
        B.sphere(P(x, z, RH), RR * 1.02, 6, 3, "sd_metal")
    B.cur_tint = T_NONE
    return B


# ----------------------------------------------------------------------------------------------
# board fence with a ledged door (County Offices - courthouse gap)
# ----------------------------------------------------------------------------------------------
XB = -17.70                       # street face of the boards
BOARD_Z0, BOARD_Z1 = -20.80, -13.75   # CO south wall (-20.84) to just before the courthouse steps (-13.59)
DOOR_Z0, DOOR_Z1 = -17.35, -16.45
# board edges in planks_grey.jpg (pixels of 1024 = 2.0 m): one strip per board keeps the
# modelled joints on the painted ones
STRIPS = [(62, 172), (172, 287), (287, 403), (403, 517), (517, 632), (632, 746), (746, 862), (862, 975)]


def boards(B, za, zb, rnd, door=False):
    """vertical boards from za to zb (scene, za < zb), 0.022 thick, 6 mm gaps"""
    widths = [(b - a) / 1024 * 2.0 for a, b in STRIPS]
    seq = []
    total = 0.0
    i = rnd.randrange(len(STRIPS))
    while total < (zb - za) - 0.08:
        seq.append(i)
        total += widths[i] + 0.006
        i = (i + 3) % len(STRIPS)
    s = (zb - za) / total
    z = za
    for i in seq:
        w = widths[i] * s
        a, b = STRIPS[i]
        top = 2.0 + rnd.uniform(-0.012, 0.008) - (0.0 if not door else 0.02)
        bot = -0.03 if not door else 0.04
        x0, x1 = XB - 0.022, XB
        y0, y1 = -(z + w), -z
        c = [Vector((x1 if k & 1 else x0, y1 if k & 2 else y0, top if k & 4 else bot)) for k in range(8)]
        fs = B.quad_box(c, "sd_wood_weathered", skip=("-Z",))
        # explicit UVs on the street face: the board's own strip of the texture
        u0, u1 = a / 1024, b / 1024
        v0, v1 = (bot + 0.03) / 2.0, (top + 0.03) / 2.0
        f = fs["+X"]
        for lp in f.loops:
            co = lp.vert.co
            fu = (y1 - co.y) / (y1 - y0)
            lp[B.uv].uv = (u0 + (u1 - u0) * fu, v0 + (v1 - v0) * ((co.z - bot) / (top - bot)))
        f[B.expl] = 1
        z += w + 0.006 * s


def build_board_fence():
    B = Builder()
    rnd = random.Random(23)
    boards(B, BOARD_Z0, DOOR_Z0 - 0.008, rnd)
    boards(B, DOOR_Z0 + 0.004, DOOR_Z1 - 0.004, rnd, door=True)
    boards(B, DOOR_Z1 + 0.008, BOARD_Z1, rnd)
    W = "sd_wood_weathered"
    # rails and posts behind (west side), at the nail rows of the texture (0.60 / 1.42 m)
    for h in (0.60, 1.42):
        for za, zb in ((BOARD_Z0, DOOR_Z0 - 0.01), (DOOR_Z1 + 0.01, BOARD_Z1)):
            B.box(XB - 0.022 - 0.045, XB - 0.022, -zb, -za, h - 0.045, h + 0.045, W, skip=())
    zs = [BOARD_Z0 + 0.06, DOOR_Z0 - 0.07, DOOR_Z1 + 0.07, -15.10, BOARD_Z1 - 0.06]
    for z in zs:
        B.box(XB - 0.022 - 0.045 - 0.10, XB - 0.022 - 0.045, -z - 0.05, -z + 0.05, -0.15, 1.98, W)
    # ledged door: two ledges and a brace on the street face, two strap hinges, a thumb latch
    xf = XB
    for h in (0.42, 1.52):
        B.box(xf, xf + 0.024, -(DOOR_Z1 - 0.03), -(DOOR_Z0 + 0.03), h - 0.075, h + 0.075, W, skip=())
    a = P(xf + 0.012, DOOR_Z1 - 0.12, 0.42 + 0.075)      # hinge (south) side low -> latch side high
    b = P(xf + 0.012, DOOR_Z0 + 0.12, 1.52 - 0.075)
    d = (b - a).normalized()
    up = Vector((1, 0, 0)).cross(d).normalized()
    c4 = [a - up * 0.06, a + up * 0.06, b - up * 0.06, b + up * 0.06]
    B.quad_box([c4[(1 if i & 4 else 0) + (2 if i & 2 else 0)] + Vector((0.012 if i & 1 else -0.012, 0, 0))
                for i in range(8)], W, skip=())
    B.cur_tint = T_IRON
    for h in (0.42, 1.52):        # strap hinges over the ledges, from the south edge
        B.box(xf + 0.024, xf + 0.030, -(DOOR_Z1 + 0.02), -(DOOR_Z1 - 0.50), h - 0.02, h + 0.02, "sd_metal", skip=())
    B.box(xf, xf + 0.05, -(DOOR_Z0 + 0.10), -(DOOR_Z0 + 0.07), 1.00, 1.12, "sd_metal", skip=())   # latch handle
    B.cur_tint = T_NONE
    return B


# ----------------------------------------------------------------------------------------------
# Rea Building hedge (Bloomfield Ave)
# ----------------------------------------------------------------------------------------------
HEDGE_X0, HEDGE_X1 = 14.0, 30.0
HEDGE_WALL_Z, HEDGE_DEPTH = -89.70, 0.80        # back against the wall (-89.82 + base course)
HEDGE_BASE, HEDGE_H = 0.13, 0.92                 # walk top 0.15; top at 1.05


def hedge_section(t):
    """cross-section (d from the wall toward the street, h) for t in 0..1 around the profile"""
    prof = [(0.0, HEDGE_H), (0.36, HEDGE_H + 0.01), (0.64, HEDGE_H - 0.01), (0.75, HEDGE_H - 0.07),
            (0.80, HEDGE_H - 0.25), (0.81, 0.45), (0.80, 0.0)]
    return prof


def build_hedge():
    B = Builder()
    rnd = random.Random(41)
    prof = hedge_section(0)
    nx = 40
    L = HEDGE_X1 - HEDGE_X0
    xs = [HEDGE_X0 + L * i / nx for i in range(nx + 1)]

    def disp(x, d, h):
        n = noise.noise(Vector((x * 1.7, d * 1.7, h * 1.7)))
        return 0.035 * n

    def pt(x, d, h, end_taper=1.0):
        # ends rounded in plan: pull the profile in near the two ends
        e = min(x - HEDGE_X0, HEDGE_X1 - x)
        k = 1.0 if e > 0.35 else 0.75 + 0.25 * (e / 0.35)
        dd = d * k
        hh = HEDGE_BASE + h * (1.0 if e > 0.25 else 0.92 + 0.08 * e / 0.25)
        out = Vector((x, -(HEDGE_WALL_Z + dd), hh))
        n = disp(x, dd, hh)
        out.y -= n * (1 if d > 0.5 else 0.3)
        out.z += n * (1 if h > HEDGE_H - 0.1 else 0.3)
        return out

    grid = [[B.V(pt(x, d, h)) for (d, h) in prof] for x in xs]
    # faces: along x between profile points; UVs in 0.5 m atlas squares (H1 / H2)
    for i in range(nx):
        for k in range(len(prof) - 1):
            a, b, c2, d = grid[i][k], grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k]
            region = (256, 640, 640, 1024) if (i + k) % 2 else (640, 640, 1024, 1024)
            seg = (b.co - a.co).length
            x0 = a.co.x
            uvs = [atlas_uv(*region, 0.05 + 0.9 * (v.co.x - x0) / 0.5, 0.05 + 0.9 * t / 0.5)
                   for v, t in ((a, 0.0), (b, seg), (c2, seg), (d, 0.0))]
            B.face((a, b, c2, d), "sd_atlas", smooth=True, uvs=uvs)
    # end caps (fan from a centre point)
    for i, sgn in ((0, -1), (nx, 1)):
        x = xs[i]
        c = B.V(pt(x, 0.40, HEDGE_H * 0.5) + Vector((sgn * 0.05, 0, 0)))
        ring = grid[i] + [grid[i][0]]
        for k in range(len(prof)):
            vs = (ring[k], c, ring[k + 1]) if sgn < 0 else (ring[k + 1], c, ring[k])
            uvs = [atlas_uv(256, 640, 640, 1024, min(1, max(0, -v.co.y - HEDGE_WALL_Z) / 0.9),
                            min(1, max(0, v.co.z - HEDGE_BASE) / 1.0)) for v in vs]   # planar, ~1 m square
            B.face(vs, "sd_atlas", smooth=True, uvs=uvs)
    # leaf cards: on the top and the street face, tilted out of the surface
    cards = 0
    target = 320
    while cards < target:
        x = rnd.uniform(HEDGE_X0 + 0.05, HEDGE_X1 - 0.05)
        side = rnd.random()
        s = rnd.uniform(0.26, 0.40)
        if side < 0.30:          # top
            d, h = rnd.uniform(0.05, 0.66), HEDGE_H + rnd.uniform(-0.01, 0.03)
            nrm = Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.35, 0.15), 1.0)).normalized()
        elif side < 0.48:        # the clipped top edge: cards leaning out at 45 deg
            d, h = rnd.uniform(0.68, 0.80), HEDGE_H - rnd.uniform(0.0, 0.12)
            nrm = Vector((rnd.uniform(-0.3, 0.3), -1.0, rnd.uniform(0.7, 1.3))).normalized()
        elif side < 0.92:        # street face
            d, h = 0.80 + rnd.uniform(-0.01, 0.03), rnd.uniform(0.12, HEDGE_H - 0.06)
            nrm = Vector((rnd.uniform(-0.3, 0.3), -1.0, rnd.uniform(-0.2, 0.45))).normalized()
        else:                    # ends
            e = rnd.choice((0, 1))
            x = HEDGE_X0 + 0.03 if e == 0 else HEDGE_X1 - 0.03
            d, h = rnd.uniform(0.1, 0.7), rnd.uniform(0.15, HEDGE_H - 0.05)
            nrm = Vector(((-1.0 if e == 0 else 1.0), rnd.uniform(-0.3, 0.3), rnd.uniform(-0.2, 0.3))).normalized()
        c = pt(x, d, h)
        tvec = nrm.cross(Vector((0, 0, 1)) if abs(nrm.z) < 0.9 else Vector((1, 0, 0))).normalized()
        rot = Matrix.Rotation(rnd.uniform(0, math.pi), 3, nrm)
        tu = rot @ tvec
        tv = nrm.cross(tu)
        c = c + nrm * rnd.uniform(-0.02, 0.03)
        vs = [B.V(c + (tu * a + tv * b) * s / 2) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        if any(v.co.z < HEDGE_BASE + 0.02 for v in vs) or any(-v.co.y < HEDGE_WALL_Z + 0.03 for v in vs):
            for v in vs:
                B.bm.verts.remove(v)
            continue
        B.face(vs, "sd_hedge_cutout", uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
        cards += 1
    return B


# ----------------------------------------------------------------------------------------------
# waste-paper box (Rea Building north stoop) and barber pole (Union Hotel)
# ----------------------------------------------------------------------------------------------
BOX_X, BOX_Z = 9.40, -105.50          # in front of the stoop's north cheek (x 9.65, z -105.76 .. -105.44)
BOX_W, BOX_H, WALK = 0.45, 0.68, 0.15


def build_box():
    B = Builder()
    cx, cy = BOX_X, -BOX_Z
    hw = BOX_W / 2
    z0, z1 = WALK + 0.03, WALK + 0.03 + BOX_H
    G = (640, 0, 1024, 384)
    # body: octagonal prism (chamfered vertical edges), lettered face toward the north (scene -z = +Y)
    poly = chamfer_square(cx, cy, hw, 0.012)
    lo = [B.V((x, y, z0)) for x, y in poly]
    hi = [B.V((x, y, z1)) for x, y in poly]
    for i in range(8):
        j = (i + 1) % 8
        a, b = poly[i], poly[j]
        vs = (lo[i], lo[j], hi[j], hi[i])
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if i == 4:      # +Y face (north): the lettering (atlas L), face runs from +x to -x
            fu = [(cx + hw - 0.012 - p[0]) / (BOX_W - 0.024) for p in (a, b, b, a)]
            fv = [0, 0, 1, 1]
            uvs = [atlas_uv(256, 0, 640, 580, u, v, inset=4) for u, v in zip(fu, fv)]
        else:
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            uvs = [atlas_uv(*G, u, v, inset=4) for u, v in ((0.1, 0.05), (0.1 + L / 0.75, 0.05),
                                                             (0.1 + L / 0.75, 0.05 + BOX_H / 0.75), (0.1, 0.05 + BOX_H / 0.75))]
        B.face(vs, "sd_atlas", uvs=uvs)
    # plinth strip (slightly inset) under the body, then the lid with an overhang and chamfer
    for zz0, zz1, w, c in ((WALK - 0.02, z0, hw - 0.015, 0.01),):
        ps = chamfer_square(cx, cy, w, c)
        l2 = [B.V((x, y, zz0)) for x, y in ps]
        h2 = [B.V((x, y, zz1)) for x, y in ps]
        for i in range(8):
            j = (i + 1) % 8
            B.face((l2[i], l2[j], h2[j], h2[i]), "sd_atlas",
                   uvs=[atlas_uv(*G, u, v) for u, v in ((0.1, 0.1), (0.3, 0.1), (0.3, 0.15), (0.1, 0.15))])
    lw = hw + 0.03
    ps = chamfer_square(cx, cy, lw, 0.02)
    l3 = [B.V((x, y, z1)) for x, y in ps]
    m3 = [B.V((x, y, z1 + 0.035)) for x, y in ps]
    t3 = [B.V((cx + (x - cx) * 0.93, cy + (y - cy) * 0.93, z1 + 0.055)) for x, y in ps]
    for i in range(8):
        j = (i + 1) % 8
        for A, Bv in ((l3, m3), (m3, t3)):
            B.face((A[i], A[j], Bv[j], Bv[i]), "sd_atlas",
                   uvs=[atlas_uv(*G, u, v) for u, v in ((0.5, 0.5), (0.7, 0.5), (0.7, 0.55), (0.5, 0.55))])
    B.face([B.V(v.co.copy()) for v in t3], "sd_atlas",
           uvs=[atlas_uv(*G, 0.5 + 0.4 * (v.co.x - cx) / lw, 0.5 + 0.4 * (v.co.y - cy) / lw) for v in t3])
    B.face(l3[::-1], "sd_atlas", uvs=[atlas_uv(*G, 0.5 + 0.4 * (v.co.x - cx) / lw, 0.5 + 0.4 * (v.co.y - cy) / lw)
                                       for v in l3[::-1]])
    return B


POLE_X, POLE_Z = 10.00, -38.30


def build_barber_pole():
    B = Builder()
    cx, cy = POLE_X, -POLE_Z
    W = "sd_paint_white"
    # plinth 0.30 high, 0.26 square, chamfered edges and a small sloped top
    lo, hi = B.prism(chamfer_square(cx, cy, 0.13, 0.015), WALK - 0.03, WALK + 0.27, W, top=False)
    top = [B.V((cx + (x - cx) * 0.80, cy + (y - cy) * 0.80, WALK + 0.30)) for x, y in chamfer_square(cx, cy, 0.13, 0.015)]
    for i in range(8):
        j = (i + 1) % 8
        B.face((hi[i], hi[j], top[j], top[i]), W)
    B.face(top, W)
    b = WALK + 0.30
    # turned base moulding, striped shaft (atlas S), top collar, neck and ball (total 2.10 m)
    B.lathe([(0.0, 0.0), (0.098, 0.0), (0.100, 0.02), (0.092, 0.035), (0.106, 0.055), (0.100, 0.075),
             (0.090, 0.085), (0.090, 0.10)], 12, W, (cx, cy, b))
    SH0, SH1 = b + 0.10, b + 0.10 + 1.44
    prof = [(0.090, 0.0), (0.090, 1.44)]

    def uv(k, j):
        return atlas_uv(0, 0, 256, 1024, j / 12, prof[k][1] / 1.44, inset=1)
    B.lathe(prof, 12, "sd_atlas", (cx, cy, SH0), uvfn=uv)
    B.lathe([(0.090, 0.0), (0.104, 0.012), (0.104, 0.035), (0.094, 0.045), (0.098, 0.060), (0.070, 0.075),
             (0.034, 0.090), (0.030, 0.110), (0.0, 0.112)], 12, W, (cx, cy, SH1))
    B.sphere(Vector((cx, cy, SH1 + 0.110 + 0.085)), 0.09, 12, 7, W)
    return B



# ----------------------------------------------------------------------------------------------
# bake / preview context: the placed neighbours (GLBs at their index.html transforms), street
# trees, ground and walk slabs. Never exported (collection SD_Context).
# ----------------------------------------------------------------------------------------------
MODELS = ROOT + r"\assets\models" + "\\"
CONTEXT_GLBS = [   # (file, scene position, y rotation) as in index.html
    ("wurts-law-office.glb", (-14.95, 0.02, -68.69), 90),
    ("house-65-main.glb", (-14.07, 0.02, -51.19), 90),
    ("county-offices.glb", (-17.71, 0.02, -27.87), 90),
    ("courthouse.glb", (-18.34, 0.15, -6.85), 90),
    ("store-57.glb", (-12.40, 0.15, -84.94), 90),
    ("rea-building.glb", (10.85, 0.15, -97.79), -90),
    ("union-hotel.glb", (11.6, 0.15, -30.75), -90),
    ("lovells-restaurant.glb", (12.66, 0.15, -52.13), -90),
]
CONTEXT_TREES = [   # street-tree.glb instances near the details: (x, y, z, rot, sx, sy, sz)
    (-7.5, 0.175, -24, 90, 1.15, 1.12, 1.15), (-7.5, 0.175, -33, 180, 1.05, 1.1, 1.05),
    (-7.5, 0.175, -60, 270, 1, 1, 1), (7.5, 0.175, -44, 0, 1.05, 1.05, 1.05),
    (7.5, 0.175, -39.8, 90, 0.92, 0.95, 0.92), (7.5, 0.175, -35.6, 180, 1.1, 1.08, 1.1),
]
CTX = "SD_Context"


def load_context():
    scene = bpy.context.scene
    coll = bpy.data.collections.get(CTX)
    if not coll:
        coll = bpy.data.collections.new(CTX)
        scene.collection.children.link(coll)
    for o in list(coll.all_objects):
        bpy.data.objects.remove(o, do_unlink=True)

    def place(path, pos, rot, scale=(1, 1, 1), name=None):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        e = bpy.data.objects.new(name or ("CTX_" + path.split("\\")[-1]), None)
        coll.objects.link(e)
        e.location = (pos[0], -pos[2], pos[1])
        e.rotation_euler = (0, 0, math.radians(rot))
        e.scale = (scale[0], scale[2], scale[1])
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            coll.objects.link(o)
            if o.parent is None:
                o.parent = e
    for f, pos, rot in CONTEXT_GLBS:
        place(MODELS + f, pos, rot)
    for i, (x, y, z, rot, sx, sy, sz) in enumerate(CONTEXT_TREES):
        place(MODELS + "street-tree.glb", (x, y, z), rot, (sx, sy, sz), "CTX_tree%d" % i)

    def slab(name, x0, x1, z0, z1, top, rgb):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), -(z0 + z1) / 2 - v.co.y * (z1 - z0),
                           (top - 0.3) / 2 + v.co.z * (top + 0.3)))
        bm.to_mesh(me)
        bm.free()
        m = bpy.data.materials.get(name + "_m") or bpy.data.materials.new(name + "_m")
        m.use_nodes = True
        next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (*rgb, 1)
        m.diffuse_color = (*rgb, 1)
        me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
    GRASS, CONC, ROAD = (0.10, 0.13, 0.05), (0.42, 0.40, 0.37), (0.22, 0.19, 0.15)
    slab("CTX_ground", -80, 80, -130, 20, 0.0, ROAD)
    slab("CTX_lawn", -45, -10.30, -77.4, 0.0, 0.015, GRASS)
    slab("CTX_walk_w", -10.30, -6.40, -100, 0.0, 0.15, CONC)
    slab("CTX_walk_e", 6.40, 10.40, -110, -10, 0.15, CONC)
    slab("CTX_walk_bloom", 6.40, 34.0, -89.9, -87.7, 0.15, CONC)
    slab("CTX_verge_bloom", 8.5, 30.0, -87.7, -86.5, 0.15, GRASS)
    slab("CTX_forecourt", -18.5, -10.30, -13.55, 0.0, 0.15, CONC)
    return coll

# ----------------------------------------------------------------------------------------------
# build all
# ----------------------------------------------------------------------------------------------
# anchors (scene x, z, height): each object's origin
ANCHORS = {
    "fence-59-wurts": ((XW, WURTS_PATH_Z, 0.015), build_wurts),
    "fence-65-picket": ((XP, H65_PATH_Z, 0.015), build_65),
    "post-stone-39": ((STONE_X, STONE_Z, 0.015), build_stone_post),
    "fence-69-pipe-rail": ((XR, -27.87, 0.015), build_pipe_rail),
    "fence-69-board": ((XB, (BOARD_Z0 + BOARD_Z1) / 2, 0.015), build_board_fence),
    "hedge-rea": (((HEDGE_X0 + HEDGE_X1) / 2, HEDGE_WALL_Z, 0.15), build_hedge),
    "waste-paper-box": ((BOX_X, BOX_Z, 0.15), build_box),
    "barber-pole-72": ((POLE_X, POLE_Z, 0.15), build_barber_pole),
}


def get_mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*VIEW[name], 1.0)
    return m


def build_all():
    coll = bpy.data.collections.get(COLL)
    if not coll:
        coll = bpy.data.collections.new(COLL)
        bpy.context.scene.collection.children.link(coll)
    for o in list(coll.objects):
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)
    out = {}
    for name, ((ax, az, ah), fn) in ANCHORS.items():
        B = fn()
        B.bm.normal_update()
        box_uvs(B)
        anchor = P(ax, az, ah)
        for v in B.bm.verts:
            v.co -= anchor
        me = bpy.data.meshes.new(name)
        for m in MATS:                  # slots first: to_mesh clamps indices to existing slots
            me.materials.append(get_mat(m))
        B.bm.to_mesh(me)
        B.bm.free()
        ob = bpy.data.objects.new(name, me)
        ob.location = anchor
        coll.objects.link(ob)
        out[name] = ob
    tris = 0
    for name, ob in out.items():
        t = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        tris += t
        print("%-20s %6d tris" % (name, t))
    print("TOTAL", tris, "triangles")
    return out


OBJECTS = build_all()
