"""
Parked period vehicles (Main Street, Flemington, c. 1920) - geometry, version 2 ("less blocky").
PLAN.md, Street details pass 2, filler objects F12-F14 and "C. Blender batch 2, vehicles".
Owner 2026-11-11 on version 1: "they look too blocky, like a video game polygon".

Run in Blender (Z up, metres):
    exec(open(r"<project>/tools/blender/vehicles.py").read())

Builds three mesh objects in the collection "vehicles", each at the file origin:

    model-t         Ford Model T touring car, 1917-20 form: black radiator shell with filler cap
                    and finned core, plain hood (no louvres before 1926), curved cowl, tub body
                    with rounded rear and door lines (no driver's door on the left), crowned
                    fenders with rolled edges, running boards on brackets, electric headlamps,
                    oil cowl lamps and tail lamp, two-piece windshield, one-man top up (header +
                    3 bows on one pivot a side, sag, rear curtain with a small back light),
                    pleated seats, steering column and wheel, transverse springs, front axle
                    with radius rods, fitted starting crank, 12-spoke artillery wheels with 30 x 3 / 30 x 3 1/2
                    clincher tyres on demountable-look rims (lugs).
    buggy           piano-box top buggy: moulded body, rolled cushion and pleated lazy back,
                    patent-leather dash, folding top with 4 bows, top joints and sag, transverse
                    elliptic springs, axles and beds, fifth wheel, reach and stays, step plates,
                    dished carriage wheels on steel tyres (14 / 16 spokes), shafts with
                    crossbar and singletree, tips resting on the ground.
    delivery-wagon  open-box light delivery wagon: individual side, end, floor and tailgate
                    boards, iron stake straps, corner irons and top bands, tailgate chains,
                    sills and bolsters, front elliptic and rear side springs, footboard and dash,
                    seat on iron risers with back rail, dished wheels on steel tyres (12 / 14
                    spokes), shafts resting on the ground. Unlettered.

Frame: origin on the ground midway between the axles; FRONT towards -Y (glTF +Z after export),
width along X (+X = the vehicle's left), Z up.

Every face is smooth-shaded; sharp edges only above 52 degrees, then a Weighted Normal pass
(keep sharp) so flat panels stay flat and bevels / rolls catch the light. Every closed part has
its normals recalculated outward. "UVMap" (real-world metres; wood along the grain, each wagon
board on one plank of the texture) is written here; vehicles_bake.py adds "Lightmap", materials,
the bake and the export.
"""
import bpy, bmesh, math
from contextlib import contextmanager
from mathutils import Vector, Matrix

ROOT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
COLL = "vehicles"

# material name -> viewport colour (sRGB hex). "enamel" and "glass" names are fixed (scene).
MATS = {
    "enamel": "0A0A0A", "satin_black": "1A1A1A", "leather": "1E1C1A", "top_fabric": "2A2826",
    "rubber": "2C2A28", "iron": "2E2D2B", "gear_paint": "3A2B26", "wagon_wood": "7E705E",
    "glass": "1A1916", "reflector": "A8A69E", "radiator_core": "1C1C1A",
}
MNAMES = list(MATS)
MI = {n: i for i, n in enumerate(MNAMES)}
TILE = {"wagon_wood": 1.0, "top_fabric": 0.15}
PLANK_U = [0.176, 0.292, 0.409, 0.522, 0.636, 0.752, 0.866, 0.068]   # plank starts in weathered_planks
SHARP_DEG = 52

ROT_Y90 = Matrix.Rotation(math.radians(90), 4, "Y")     # local Z -> +X
ROT_YM90 = Matrix.Rotation(math.radians(-90), 4, "Y")   # local Z -> -X
ROT_X90 = Matrix.Rotation(math.radians(90), 4, "X")     # local Z -> -Y (forward)
ROT_XM90 = Matrix.Rotation(math.radians(-90), 4, "X")   # local Z -> +Y


def T(x, y, z):
    return Matrix.Translation((x, y, z))


def RY(a):
    return Matrix.Rotation(a, 4, "Y")


def RX(a):
    return Matrix.Rotation(a, 4, "X")


def lerp(a, b, t):
    return a + (b - a) * t


def sstep(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def catmull(pts, sub=4):
    P = [Vector(p) for p in pts]
    out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for k in range(sub):
            t = k / sub
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-1].copy())
    return out


def resample(pts, n):
    P = [Vector(p) for p in pts]
    d = [0.0]
    for i in range(1, len(P)):
        d.append(d[-1] + (P[i] - P[i - 1]).length)
    out, j = [], 0
    for k in range(n):
        s = d[-1] * k / (n - 1)
        while j < len(P) - 2 and d[j + 1] < s:
            j += 1
        t = (s - d[j]) / max(d[j + 1] - d[j], 1e-9)
        out.append(P[j].lerp(P[j + 1], min(max(t, 0.0), 1.0)))
    return out


def smooth_path(pts, n, sub=6):
    return resample(catmull(pts, sub), n)


def frame_from(t, hint=(0, 0, 1)):
    """Matrix whose local Z is t and local Y is as close to hint as possible."""
    t = Vector(t).normalized()
    a = Vector(hint).cross(t)
    if a.length < 1e-6:
        a = Vector((1, 0, 0)).cross(t)
    a.normalize()
    b = t.cross(a)
    return Matrix((a, b, t)).transposed().to_4x4()


class Builder:
    def __init__(self):
        self.bm = bmesh.new()
        self.gl = self.bm.faces.layers.float_vector.new("grain")
        self.bl = self.bm.faces.layers.int.new("board")
        self.sl = self.bm.faces.layers.int.new("soft")
        self.soft = 0
        self.uvl = self.bm.loops.layers.uv.new("UVMap")
        self.depth = 0
        self.cur = []
        self.recalc = True
        self.grain = None
        self.board = -1

    # -- bookkeeping ---------------------------------------------------------------------
    @contextmanager
    def part(self, grain=None, board=None, recalc=True):
        if self.depth == 0:
            self.cur = []
            self.recalc = recalc
        old = (self.grain, self.board)
        if grain is not None:
            self.grain = Vector(grain).normalized()
        if board is not None:
            self.board = board
        self.depth += 1
        try:
            yield
        finally:
            self.depth -= 1
            self.grain, self.board = old
            if self.depth == 0:
                fs = [f for f in self.cur if f.is_valid]
                if self.recalc and fs:
                    bmesh.ops.recalc_face_normals(self.bm, faces=fs)
                self.uv(fs)
                self.cur = []

    def uv(self, faces):
        for f in faces:
            mat = MNAMES[f.material_index]
            tile = TILE.get(mat, 1.0)
            g = Vector(f[self.gl])
            n = f.normal
            if g.length > 0.5:
                w = n.cross(g)
                if w.length > 0.3:
                    w.normalize()
                    us = [l.vert.co.dot(w) for l in f.loops]
                    u0 = min(us)
                    bi = f[self.bl]
                    for l, u in zip(f.loops, us):
                        if bi >= 0:
                            uu = PLANK_U[bi % len(PLANK_U)] + (u - u0) * 0.9 / tile
                            vv = l.vert.co.dot(g) / tile + 0.37 * bi
                        else:
                            uu, vv = u / tile, l.vert.co.dot(g) / tile
                        l[self.uvl].uv = (uu, vv)
                    continue
            ax = max(range(3), key=lambda i: abs(n[i]))
            for l in f.loops:
                co = l.vert.co
                u, v = (co.x, co.y) if ax == 2 else (co.y, co.z) if ax == 0 else (co.x, co.z)
                l[self.uvl].uv = (u / tile, v / tile)

    def vert(self, co):
        return self.bm.verts.new(co)

    def face(self, vs, mat, d=None):
        u = []
        for v in vs:
            if not u or u[-1] is not v:
                u.append(v)
        if len(u) > 1 and u[0] is u[-1]:
            u.pop()
        if len(u) < 3:
            return None
        try:
            f = self.bm.faces.new(u)
        except ValueError:
            return None
        f.material_index = MI[mat]
        f.smooth = True
        if self.grain is not None:
            f[self.gl] = self.grain
        f[self.bl] = self.board
        f[self.sl] = self.soft
        if d is not None:
            f.normal_update()
            if f.normal.dot(Vector(d)) < 0:
                f.normal_flip()
        if self.depth == 0:          # stray face: orient now, UV now
            self.uv([f])
        else:
            self.cur.append(f)
        return f

    def grid(self, rows, mats, closed_v=False, closed_u=False, d=None):
        nr = len(rows)
        for i in range(nr if closed_u else nr - 1):
            A, Bv = rows[i], rows[(i + 1) % nr]
            nc = len(A)
            for j in range(nc if closed_v else nc - 1):
                j2 = (j + 1) % nc
                m = mats if isinstance(mats, str) else mats(i, j)
                dd = d(i, j) if callable(d) else d
                self.face((A[j], A[j2], Bv[j2], Bv[j]), m, dd)

    def ring_verts(self, pts):
        return [self.vert(p) for p in pts]

    # -- primitives -----------------------------------------------------------------------
    def lathe(self, prof, n, mats, M=Matrix(), phase=0.0, closed=False, cap0=None, cap1=None):
        with self.part():
            rings = []
            for r, z in prof:
                if r < 1e-7:
                    v = self.vert(M @ Vector((0, 0, z)))
                    rings.append([v] * n)
                else:
                    rings.append([self.vert(M @ Vector((r * math.cos(phase + 2 * math.pi * j / n),
                                                        r * math.sin(phase + 2 * math.pi * j / n), z)))
                                  for j in range(n)])
            mf = (lambda i, j: mats) if isinstance(mats, str) else (lambda i, j: mats[min(i, len(mats) - 1)])
            self.grid(rings, mf, closed_v=True, closed_u=closed)
            if cap0:
                self.face(rings[0], cap0)
            if cap1:
                self.face(rings[-1], cap1)
        return rings

    def sweep(self, pts, sec, mat, lat=None, nrm=None, closed=False, caps=True):
        """Sweep a closed section [(a, b), ...] (or sec(i) -> section) along pts. With lat: a is
        along the fixed lateral axis, b along lat x tangent. Else parallel transport from nrm:
        b along the normal N, a along tangent x N."""
        P = [Vector(p) for p in pts]
        cnt = len(P)
        tans = []
        for i in range(cnt):
            if closed:
                d = P[(i + 1) % cnt] - P[i - 1]
            else:
                d = P[min(i + 1, cnt - 1)] - P[max(i - 1, 0)]
            tans.append(d.normalized())
        N = None
        if lat is None:
            N = Vector(nrm) if nrm is not None else None
            if N is None or abs(N.dot(tans[0])) > 0.99:
                N = Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0))
            N = (N - tans[0] * N.dot(tans[0])).normalized()
        else:
            L0 = Vector(lat).normalized()
        with self.part():
            rings = []
            for i in range(cnt):
                t = tans[i]
                if lat is None:
                    if i > 0:
                        N = (N - t * N.dot(t)).normalized()
                    A = t.cross(N)
                    Bn = N
                else:
                    A = (L0 - t * L0.dot(t)).normalized()
                    Bn = A.cross(t).normalized()
                S = sec(i) if callable(sec) else sec
                rings.append([self.vert(P[i] + a * A + b * Bn) for a, b in S])
            mf = mat if isinstance(mat, str) else (lambda i, j: mat[min(i, len(mat) - 1)])
            self.grid(rings, mf, closed_v=True, closed_u=closed)
            if caps and not closed:
                m0 = mat if isinstance(mat, str) else mat[0]
                self.face(rings[0], m0)
                self.face(rings[-1], m0 if isinstance(mat, str) else mat[-1])
        return rings

    def tube(self, pts, r, n, mat, closed=False, caps=True, nrm=None, phase=0.0):
        """r: radius, (ra, rb) ellipse (ra along the normal), or a list of either per point."""
        def rad(i):
            x = r[i] if isinstance(r, list) else r
            return (x, x) if isinstance(x, (int, float)) else x

        def sec(i):
            ra, rb = rad(i)
            return [(rb * math.cos(phase + 2 * math.pi * j / n), ra * math.sin(phase + 2 * math.pi * j / n))
                    for j in range(n)]
        self.soft = 1
        try:
            return self.sweep(pts, sec, mat, nrm=nrm, closed=closed, caps=caps)
        finally:
            self.soft = 0

    def ring(self, centre, R, r, nM, nm, mat, axis, ellipse=None):
        ax = Vector(axis).normalized()
        u = Vector((1, 0, 0)) if abs(ax.x) < 0.9 else Vector((0, 1, 0))
        u = (u - ax * u.dot(ax)).normalized()
        v = ax.cross(u)
        c = Vector(centre)
        pts = [c + R * (math.cos(2 * math.pi * i / nM) * u + math.sin(2 * math.pi * i / nM) * v) for i in range(nM)]
        return self.tube(pts, ellipse or r, nm, mat, closed=True, nrm=ax)

    def rbox(self, c, s, mat, M=Matrix(), bev=0.006, seg=1):
        hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2
        with self.part():
            vs = [self.vert(M @ Vector((c[0] + (hx if i & 1 else -hx), c[1] + (hy if i & 2 else -hy),
                                        c[2] + (hz if i & 4 else -hz)))) for i in range(8)]
            F = ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5))
            fs = [self.face([vs[i] for i in idx], mat) for idx in F]
            bev = min(bev, 0.45 * min(s))
            if bev > 1e-5:
                bmesh.ops.recalc_face_normals(self.bm, faces=[f for f in fs if f])
                edges = list({e for f in fs if f for e in f.edges})
                res = bmesh.ops.bevel(self.bm, geom=vs + edges, offset=bev, offset_type="OFFSET",
                                      segments=seg, profile=0.5, affect="EDGES", clamp_overlap=True)
                for f in res["faces"]:
                    f.smooth = True
                    f.material_index = MI[mat]
                    if self.grain is not None:
                        f[self.gl] = self.grain
                    f[self.bl] = self.board
                    self.cur.append(f)

    def beam(self, p0, p1, w, h, mat, hint=(0, 0, 1), bev=0.004, seg=1):
        """Box from p0 to p1; h measured along hint, w across."""
        p0, p1 = Vector(p0), Vector(p1)
        M = frame_from(p1 - p0, hint)
        M.translation = p0
        self.rbox((0, 0, (p1 - p0).length / 2), (w, h, (p1 - p0).length), mat, M, bev, seg)

    def sheet(self, G, thick, mat, mat_back=None):
        """Closed thin shell from a grid of points (rows x cols)."""
        nr, nc = len(G), len(G[0])
        top, bot = [], []
        for i in range(nr):
            rt, rb = [], []
            for j in range(nc):
                du = G[min(i + 1, nr - 1)][j] - G[max(i - 1, 0)][j]
                dv = G[i][min(j + 1, nc - 1)] - G[i][max(j - 1, 0)]
                n = du.cross(dv)
                n = n.normalized() if n.length > 1e-9 else Vector((0, 0, 1))
                rt.append(self.vert(G[i][j] + n * thick / 2))
                rb.append(self.vert(G[i][j] - n * thick / 2))
            top.append(rt)
            bot.append(rb)
        with self.part():
            self.grid(top, mat)
            self.grid(bot, mat_back or mat)
            def perim(R):
                p = [R[0][j] for j in range(nc)] + [R[i][nc - 1] for i in range(1, nr)]
                p += [R[nr - 1][j] for j in range(nc - 2, -1, -1)] + [R[i][0] for i in range(nr - 2, 0, -1)]
                return p
            self.grid([perim(top), perim(bot)], mat, closed_v=True)

    def sheet_holed(self, G, thick, mat, skip=()):
        """Closed thin shell from a grid of points (rows x cols) with the cells in `skip`
        ((row, col) of the cell's lower-left corner) left open; walls round every opening."""
        nr, nc = len(G), len(G[0])
        top, bot = [], []
        for i in range(nr):
            rt, rb = [], []
            for j in range(nc):
                du = G[min(i + 1, nr - 1)][j] - G[max(i - 1, 0)][j]
                dv = G[i][min(j + 1, nc - 1)] - G[i][max(j - 1, 0)]
                n = du.cross(dv)
                n = n.normalized() if n.length > 1e-9 else Vector((0, 0, 1))
                rt.append(self.vert(G[i][j] + n * thick / 2))
                rb.append(self.vert(G[i][j] - n * thick / 2))
            top.append(rt)
            bot.append(rb)
        keep = {(i, j) for i in range(nr - 1) for j in range(nc - 1)} - set(skip)
        with self.part():
            for i, j in keep:
                q = ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))
                self.face([top[a][b] for a, b in q], mat)
                self.face([bot[a][b] for a, b in reversed(q)], mat)
                for (a, b), nb in ((((i, j), (i, j + 1)), (i - 1, j)), (((i + 1, j + 1), (i + 1, j)), (i + 1, j)),
                                   (((i, j + 1), (i + 1, j + 1)), (i, j + 1)), (((i + 1, j), (i, j)), (i, j - 1))):
                    if nb not in keep:
                        self.face([top[a[0]][a[1]], top[b[0]][b[1]], bot[b[0]][b[1]], bot[a[0]][a[1]]], mat)

    def loop_loft(self, loops, mat, closed=True, caps=False):
        with self.part():
            R = [self.ring_verts(l) for l in loops]
            self.grid(R, mat, closed_v=True, closed_u=closed)
            if caps and not closed:
                self.face(R[0], mat)
                self.face(R[-1], mat)
        return R


def rect_sec(w, t):
    return [(-w / 2, -t / 2), (w / 2, -t / 2), (w / 2, t / 2), (-w / 2, t / 2)]


def round_rect_sec(w, t, r=None, k=2):
    """Rectangle w x t with rounded corners (k points per corner)."""
    r = min(r if r is not None else min(w, t) * 0.3, w / 2 - 1e-4, t / 2 - 1e-4)
    out = []
    for cx, cy, a0 in ((w / 2 - r, -t / 2 + r, -90), (w / 2 - r, t / 2 - r, 0), (-w / 2 + r, t / 2 - r, 90),
                       (-w / 2 + r, -t / 2 + r, 180)):
        for i in range(k + 1):
            a = math.radians(a0 + 90 * i / k)
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def ellipse_sec(a, b, n):
    return [(a * math.cos(2 * math.pi * j / n), b * math.sin(2 * math.pi * j / n)) for j in range(n)]


# ----------------------------------------------------------------------------------------------
# wheels
# ----------------------------------------------------------------------------------------------
def wheel_M(x, y, zc, side, tilt=0.0):
    return T(x, y, zc) @ RY(side * tilt) @ (ROT_Y90 if side > 0 else ROT_YM90)


def spokes(B, M, n, r0, r1, z0, z1, sec0, sec1, mat, phase=0.0, sides=6, mid=None):
    """n spokes from radius r0 (axial z0) to r1 (z1) in wheel-local coords. sec = (tangential half,
    axial half)."""
    nrm = (M.to_3x3() @ Vector((0, 0, 1))).normalized()
    for k in range(n):
        a = phase + 2 * math.pi * k / n
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = [Vector((0, 0, z0)) + d * r0, Vector((0, 0, z1)) + d * r1]
        rads = [(sec0[1], sec0[0]), (sec1[1], sec1[0])]
        if mid:
            pts.insert(1, Vector((0, 0, lerp(z0, z1, mid[0]))) + d * lerp(r0, r1, mid[0]))
            rads.insert(1, (mid[2], mid[1]))
        B.tube([M @ p for p in pts], rads, sides, mat, nrm=nrm, caps=False)


def wheel_model_t(B, x, y, side, R, rear, camber=0.0):
    """Wood artillery wheel, 12 spokes, clincher rim on the felloe (demountable lugs), tyre.
    camber: positive = top of the wheel leans outward (front wheels of a T: about 3 degrees)."""
    zc = R * math.cos(camber) - 0.006    # tyre slightly flattened under load
    M = wheel_M(x, y, zc, side, camber)
    a = 0.044 if rear else 0.039         # tyre section half height (3 1/2 / 3 in)
    b = 0.045 if rear else 0.038         # half width
    rc = R - a
    prof = []
    for k in range(7):
        p = math.radians(-125 + 250 * k / 6)
        prof.append((rc + a * math.cos(p), b * math.sin(p)))
    rs = rc - 0.574 * a                  # where the tyre meets the rim
    prof += [(rs - 0.003, b * 0.93), (rs - 0.014, 0.027), (rs - 0.064, 0.020),
             (rs - 0.064, -0.020), (rs - 0.014, -0.027), (rs - 0.003, -b * 0.93)]
    mats = ["rubber"] * 6 + ["rubber"] + ["enamel"] * 5 + ["rubber"]
    B.lathe(prof, 32, mats, M, phase=math.pi / 32, closed=True)
    # 12 spokes, wedge-shaped at the hub
    spokes(B, M, 12, 0.055, rs - 0.05, 0.0, 0.0, (0.0175, 0.024), (0.013, 0.016), "enamel",
           phase=math.pi / 12, sides=5)
    # hub: inner flange, spoke barrel, outer flange with bolt ring, hub cap
    hub = [(0.0, -0.06), (0.084, -0.05), (0.066, -0.030), (0.066, 0.030), (0.088, 0.042),
           (0.050, 0.056), (0.044, 0.092), (0.025, 0.112), (0.0, 0.117)] if rear else \
          [(0.0, -0.055), (0.078, -0.045), (0.064, -0.030), (0.064, 0.030), (0.082, 0.040),
           (0.046, 0.052), (0.040, 0.084), (0.022, 0.103), (0.0, 0.108)]
    B.lathe(hub, 12, "enamel", M)
    # demountable rim lugs (6) on the outer felloe face
    for k in range(6):
        ang = 2 * math.pi * (k + 0.5) / 6
        L = M @ T(math.cos(ang) * (rs - 0.036), math.sin(ang) * (rs - 0.036), 0.026) @ \
            Matrix.Rotation(ang, 4, "Z")
        B.rbox((0, 0, 0), (0.026, 0.030, 0.014), "enamel", L, bev=0)


def wheel_carriage(B, x, y, side, R, nspk, tyre_w, felloe_d, felloe_w, hub_r, hub_len, dish,
                   gear="gear_paint", nseg=32, hub_seg=14):
    """Wood carriage wheel: steel tyre on a wood felloe, round tapered spokes, dish (hub inboard of
    the rim plane), wheel tilted so the lowest spoke stands plumb."""
    tilt = math.atan(dish / (R - felloe_d))
    zc = R * math.cos(tilt) - 0.002
    M = wheel_M(x, y, zc, side, tilt)
    w = max(tyre_w, felloe_w) / 2
    prof = [(R, -w), (R, w), (R - 0.011, w), (R - felloe_d, w * 0.85), (R - felloe_d, -w * 0.85), (R - 0.011, -w)]
    mats = ["iron", "iron", gear, gear, gear, "iron"]
    B.lathe(prof, nseg, mats, M, phase=math.pi / nseg, closed=True)
    # spokes: from the hub (dished inboard) to the felloe, tapered oval
    spokes(B, M, nspk, hub_r * 0.85, R - felloe_d + 0.012, -dish, 0.0,
           (0.0115 if R > 0.5 else 0.011, 0.015), (0.009, 0.011), gear, phase=math.pi / nspk, sides=5)
    # hub (Sarven-type): barrel with bands and sand box, iron cap
    h = hub_len
    zc_h = -dish
    hub = [(0.0, zc_h - 0.55 * h), (hub_r * 0.80, zc_h - 0.50 * h), (hub_r * 1.18, zc_h - 0.06 * h),
           (hub_r * 1.18, zc_h + 0.06 * h), (hub_r * 0.66, zc_h + 0.40 * h), (hub_r * 0.56, zc_h + 0.60 * h),
           (0.0, zc_h + 0.64 * h)]
    mats = [gear] * 4 + ["iron"] * 2
    B.lathe(hub, hub_seg, mats, M)


# ----------------------------------------------------------------------------------------------
# shared pieces
# ----------------------------------------------------------------------------------------------
def leaf_spring(B, pts_fn, length, leaves, w, t, mat, lat):
    """Stacked leaves along an arc: pts_fn(u in -1..1, layer) -> point. Main leaf full length,
    each further leaf shorter and stacked on the concave side."""
    for k in range(leaves):
        frac = 1.0 - 0.28 * k
        n = 8 if k == 0 else 6
        pts = [pts_fn(-frac + 2 * frac * i / (n - 1), k) for i in range(n)]
        B.sweep(pts, rect_sec(w, t), mat, lat=lat)


def elliptic_spring(B, c, half_w, half_h, along, mat, w=0.038, t=0.008, leaves=2):
    """Full elliptic spring: upper and lower arcs joined by eyes at both ends."""
    c = Vector(c)
    u = Vector((1, 0, 0)) if along == "x" else Vector((0, 1, 0))
    lat = (0, 1, 0) if along == "x" else (1, 0, 0)
    for sgn in (1, -1):
        def f(s, k, sgn=sgn):
            h = half_h * (1 - abs(s) ** 2.2) ** 0.8
            return c + u * (s * half_w) + Vector((0, 0, sgn * (h - k * t * 0.95)))
        leaf_spring(B, f, half_w, leaves, w, t, mat, lat)
    for s in (-1, 1):
        B.lathe([(0.0, -w / 2 - 0.004), (0.011, -w / 2 - 0.004), (0.011, w / 2 + 0.004), (0.0, w / 2 + 0.004)],
                6, mat, T(*(c + u * s * half_w)) @ (ROT_XM90 if along == "x" else ROT_Y90))


def shafts(B, fa, attach_z, x_att, x_tip, mat, length, z_tip=0.035, heavy=1.0):
    """Two shafts hinged at the front axle, lying with their tips on the ground; crossbar and a
    singletree on the crossbar."""
    for s in (1, -1):
        raw = [(s * x_att, fa + 0.06, attach_z), (s * x_att, fa - 0.20, attach_z - 0.03),
               (s * lerp(x_att, x_tip, 0.25), fa - 0.65, attach_z - 0.13),
               (s * lerp(x_att, x_tip, 0.55), fa - 1.25, lerp(attach_z, z_tip, 0.55)),
               (s * lerp(x_att, x_tip, 0.85), fa - 1.85, lerp(attach_z, z_tip, 0.86)),
               (s * x_tip, fa - length + 0.12, z_tip - 0.008), (s * x_tip, fa - length, z_tip + 0.012)]
        pts = smooth_path(raw, 11)
        rad = [(lerp(0.024, 0.016, i / 10) * heavy, lerp(0.020, 0.014, i / 10) * heavy) for i in range(11)]
        B.tube(pts, rad, 6, mat, nrm=(0, 0, 1))
        # iron tip ferrule and the shaft coupling at the axle
        B.lathe([(0.0, -0.004), (0.016 * heavy, -0.004), (0.016 * heavy, 0.05), (0.0, 0.056)], 6, "iron",
                T(*pts[-1]) @ frame_from(pts[-1] - pts[-3]))
        B.beam((s * x_att, fa + 0.10, attach_z), (s * x_att, fa - 0.04, attach_z), 0.05, 0.05, "iron", bev=0)
    yb = fa - 0.42
    zb = attach_z - 0.07
    xb = lerp(x_att, x_tip, 0.12)
    B.beam((-xb, yb, zb), (xb, yb, zb), 0.055 * heavy, 0.05 * heavy, mat, hint=(0, 0, 1), bev=0.01, seg=1)
    # singletree: tapered round bar on a clip in front of the crossbar, iron end hooks
    st = [(-0.34, yb - 0.08, zb + 0.005), (0.0, yb - 0.08, zb + 0.005), (0.34, yb - 0.08, zb + 0.005)]
    B.tube(st, [(0.016, 0.016), (0.026, 0.026), (0.016, 0.016)], 6, mat, nrm=(0, 1, 0))
    B.beam((0, yb - 0.02, zb), (0, yb - 0.09, zb + 0.005), 0.03, 0.02, "iron", bev=0)
    for s in (1, -1):
        B.lathe([(0.0, -0.01), (0.019, -0.01), (0.019, 0.03), (0.0, 0.03)], 6, "iron",
                T(s * 0.335, yb - 0.08, zb + 0.005) @ (ROT_Y90 if s > 0 else ROT_YM90))


def folding_top(B, hw_top, hw_bot, bows, zr, pivot, back_y, z_bot, rc_bot, fabric, bow_mat,
                valance=0.045, pads=None, sag=0.016, bow_size=(0.016, 0.009), front_valance=True,
                rows=12, corner=5, hood_ws=(0.0, 0.14, 0.32, 0.52, 0.72, 0.88, 0.97), hood_from=-1):
    """Roof sheet from the front bow to the rear bow (crown, pads, sag between bows, valance), a
    rear hood (back curtain + quarters) down to the body, bows whose legs pivot at `pivot`
    (y, z) on both sides, and a welt over the roof / hood seam."""
    yf, yr = bows[0] - 0.02, bows[-1] + 0.03
    crown = 0.032

    def sagf(y):
        for a, b in zip(bows, bows[1:]):
            if a <= y <= b:
                return sag * math.sin(math.pi * (y - a) / (b - a)) ** 1.5
        return 0.0

    lat = [(-hw_top, -valance, False), (-hw_top - 0.002, -0.014, False), (-hw_top + 0.014, 0.0, False)]
    if pads:
        lat += [(-pads - 0.03, None, True), (-pads, "pad", True), (-pads + 0.04, None, True)]
    else:
        lat += [(-hw_top * 0.75, None, True)]
    lat += [(-hw_top * 0.4, None, True), (0.0, None, True)]
    lat = lat + [(-l, n, s) for l, n, s in reversed(lat[:-1])]

    def roof_row(y, dz=0.0, dy=0.0):
        row = []
        for l, n, interior in lat:
            if n is None or n == "pad":
                nn = crown * (1 - (l / hw_top) ** 2) - sagf(y) * (1 - (l / hw_top) ** 2) ** 0.6
                if n == "pad":
                    nn += 0.006
            else:
                nn = n
            row.append(Vector((l, y + dy, zr(y) + nn + dz)))
        return row

    ys = sorted(set([round(yf + (yr - yf) * i / rows, 4) for i in range(rows + 1)] + list(bows)))
    ys = [y for i, y in enumerate(ys) if i == 0 or y - ys[i - 1] > 0.03 or y in bows]
    G = []
    if front_valance:
        G.append(roof_row(yf, -valance, 0.004))
        G.append(roof_row(yf, -0.014, 0.0))
    for y in ys:
        G.append(roof_row(y))
    B.sheet(G, 0.006, fabric)

    # rear hood: U-shaped plan loops from the rear-bow legs round the back, w = 0 (body) .. 1
    py, pz = pivot
    yrb = bows[-1]
    ztop = zr(yrb) - valance * 0.6
    loops = []
    for w in hood_ws:
        s = math.sin(w * math.pi / 2)
        yb = yrb + (back_y - yrb) * math.cos(w * math.pi / 2)
        zb = z_bot + (ztop - z_bot) * s
        yl = py + (bows[hood_from] - py) * s
        hw = lerp(hw_bot, hw_top, w)
        rc = min(lerp(rc_bot, 0.05, w), hw - 0.01, max(yb - yl - 0.002, 0.001))
        pts, nrm = [], []
        for k in range(3):                                 # left side, front to back
            yy = lerp(yl, yb - rc, k / 3)
            pts.append(Vector((hw, yy, zb)))
            nrm.append(Vector((1, 0, 0)))
        for k in range(corner + 1):                        # left rear corner
            a = math.radians(90 * k / corner)
            pts.append(Vector((hw - rc + rc * math.cos(a), yb - rc + rc * math.sin(a), zb)))
            nrm.append(Vector((math.cos(a), math.sin(a), 0)))
        for k in (1, 2):
            pts.append(Vector((lerp(hw - rc, -(hw - rc), k / 3), yb, zb)))
            nrm.append(Vector((0, 1, 0)))
        for k in range(corner + 1):
            a = math.radians(90 + 90 * k / corner)
            pts.append(Vector((-(hw - rc) + rc * math.cos(a), yb - rc + rc * math.sin(a), zb)))
            nrm.append(Vector((math.cos(a), math.sin(a), 0)))
        for k in range(1, 4):
            yy = lerp(yb - rc, yl, k / 3)
            pts.append(Vector((-hw, yy, zb)))
            nrm.append(Vector((-1, 0, 0)))
        sg = 0.014 * math.sin(math.pi * w)
        loops.append([p - n * sg for p, n in zip(pts, nrm)])
    B.sheet(loops, 0.006, fabric)

    # bows: legs from the pivots up to the roof edge, across under the fabric
    for yb_ in bows:
        top = []
        for l in (-hw_top + 0.012, -hw_top * 0.6, 0.0, hw_top * 0.6, hw_top - 0.012):
            n = crown * (1 - (l / hw_top) ** 2) - 0.012
            top.append(Vector((l, yb_, zr(yb_) + n)))
        pl = Vector((-hw_bot - 0.012, py, pz))
        pr = Vector((hw_bot + 0.012, py, pz))
        el = Vector((-hw_top + 0.004, yb_, zr(yb_) - valance + 0.006))
        er = Vector((hw_top - 0.004, yb_, zr(yb_) - valance + 0.006))
        pts = [pl, pl.lerp(el, 0.5), el] + top + [er, pr.lerp(er, 0.5), pr]
        pts = smooth_path(pts, 11, 4)
        B.tube(pts, bow_size, 4, bow_mat, nrm=(0, 1, 0), phase=math.pi / 4)
    # pivot sockets
    for s in (1, -1):
        B.lathe([(0.0, -0.02), (0.022, -0.02), (0.022, 0.02), (0.0, 0.02)], 10, "iron",
                T(s * (hw_bot + 0.012), py, pz) @ (ROT_Y90 if s > 0 else ROT_YM90))
    # welt over the roof / rear hood seam
    row = roof_row(yrb + 0.012)
    pts = [p + Vector((0, 0, 0.004)) for p in row[1:-1]]
    B.tube(smooth_path(pts, 13, 4), 0.0065, 4, fabric, nrm=(0, 1, 0))
    return lat


# ----------------------------------------------------------------------------------------------
# F12 Ford Model T touring car (1917-20)
# ----------------------------------------------------------------------------------------------
FA_T, RA_T, TR_T = -1.27, 1.27, 0.71           # 100 in wheelbase, 56 in tread
BODY_W = 0.56                                  # body half width
BODY_Y0, BODY_Y1, BODY_RC, BODY_CY = -0.45, 1.70, 0.42, 1.28


def t_plan(groove_ys):
    """Body plan path (x, y, nx, ny, groove) from the left front round the rear to the right front."""
    W, rc = BODY_W, BODY_RC
    pts = []

    def side(x, ys, sgn, grooves):
        out = []
        marks = sorted(ys)
        allys = set(marks)
        for g in grooves:
            allys |= {g - 0.006, g, g + 0.006}
        for y in sorted(allys, reverse=(sgn < 0)):
            out.append((x, y, sgn, 0.0, any(abs(y - g) < 1e-6 for g in grooves)))
        return out

    pts += side(W, [BODY_Y0, BODY_CY], 1, groove_ys["left"])
    cx = W - rc
    for k in range(1, 7):
        a = math.radians(90 * k / 6)
        pts.append((cx + rc * math.cos(a), BODY_CY + rc * math.sin(a), math.cos(a), math.sin(a), False))
    for k in (1,):
        pts.append((0.0, BODY_Y1, 0.0, 1.0, False))
    for k in range(0, 6):
        a = math.radians(90 + 90 * k / 6)
        pts.append((-cx + rc * math.cos(a), BODY_CY + rc * math.sin(a), math.cos(a), math.sin(a), False))
    pts += side(-W, [BODY_Y0, BODY_CY], -1, groove_ys["right"])
    return pts


def t_body(B):
    K = "enamel"
    # three opening doors (right front, both rear); on the driver's (left, +X) side the front "door"
    # is only a stamped outline, as on 1912-25 Ford open cars. No outside handles (latch inside).
    plan = t_plan({"left": [-0.38, 0.14, 0.60, 1.08], "right": [-0.38, 0.14, 0.60, 1.08]})
    prof = [(-0.015, 0.585), (0.0, 0.600), (0.003, 0.70), (0.003, 0.90), (-0.003, 0.985), (-0.014, 1.022),
            (-0.032, 1.041), (-0.051, 1.038), (-0.064, 1.020), (-0.066, 0.98), (-0.064, 0.625),
            (-0.042, 0.585)]
    rings = []
    for x, y, nx, ny, groove in plan:
        ring = []
        for k, (o, z) in enumerate(prof):
            oo = o
            if ny > 0.25 and z < 0.80:                      # rear of the tub curves under
                oo -= ny * 0.075 * ((0.80 - z) / 0.215) ** 2
            if groove and k < 9:
                oo -= 0.005
            ring.append(Vector((x + nx * oo, y + ny * oo, z)))
        rings.append(ring)
    B.loop_loft(rings, K, closed=False, caps=True)
    # floor (rubber mat) and the pleated seats
    B.rbox((0, 0.62, 0.63), (1.0, 2.12, 0.02), "rubber", bev=0)
    # front seat: base, rounded cushion, pleated back on a painted panel
    B.rbox((0, 0.10, 0.70), (1.06, 0.50, 0.14), K, bev=0)
    B.rbox((0, 0.10, 0.83), (1.02, 0.50, 0.13), "leather", bev=0.045, seg=2)
    pleated_back(B, -0.50, 0.50, 0.89, 1.29, 0.38, math.radians(12), 7, panel=K)
    # rear seat
    B.rbox((0, 1.28, 0.70), (1.0, 0.48, 0.14), K, bev=0)
    B.rbox((0, 1.27, 0.835), (0.98, 0.50, 0.14), "leather", bev=0.045, seg=2)
    pleated_back(B, -0.30, 0.30, 0.90, 1.035, 1.57, math.radians(16), 6, panel=None, depth=0.07)
    # rear seat end rolls (side upholstery against the tub corners)
    for s in (1, -1):
        B.tube([(s * 0.47, 0.98, 0.88), (s * 0.465, 1.28, 0.90), (s * 0.36, 1.46, 0.93)], 0.05, 6, "leather")


def pleated_back(B, x0, x1, z0, z1, y, lean, npleat, panel="enamel", depth=0.05):
    """Seat back facing -Y: vertical rolls (pleats) with a rolled top, leaning back by `lean`."""
    cols = npleat * 3 + 1
    rows = 4
    G = []
    for i in range(rows):
        t = i / (rows - 1)
        z = lerp(z0, z1, t)
        row = []
        for j in range(cols):
            u = j / (cols - 1)
            x = lerp(x0, x1, u)
            ph = (u * npleat) % 1.0
            d = 0.016 * math.sin(math.pi * ph) ** 0.6
            d *= math.sin(math.pi * min(t * 1.4 + 0.15, 1.0)) ** 0.3
            yy = y - d + (z - z0) * math.tan(lean)
            row.append(Vector((x, yy, z)))
        G.append(row)
    with B.part(recalc=False):
        R = [[B.vert(p) for p in row] for row in G]
        B.grid(R, "leather", d=(0, -1, 0.2))
    # rolled top
    zt = z1 + 0.012
    yt = y + (z1 - z0) * math.tan(lean) - 0.004
    B.tube([(x0 - 0.01, yt, zt), (x1 + 0.01, yt, zt)], 0.03, 8, "leather")
    if panel:
        M = T(0, y + 0.03 + (z1 - z0) / 2 * math.tan(lean), (z0 + z1) / 2) @ RX(-lean)
        B.rbox((0, 0, 0), (x1 - x0 + 0.04, 0.05, z1 - z0 + 0.04), panel, M, bev=0.012, seg=1)
    else:
        M = T(0, y + depth / 2 + (z1 - z0) / 2 * math.tan(lean), (z0 + z1) / 2) @ RX(-lean)
        B.rbox((0, 0, 0), (x1 - x0 + 0.02, depth, z1 - z0), "leather", M, bev=0)


def hood_section(y, hw, zb, zs, zt, n_exp, k=5):
    pts = [Vector((hw, y, zb)), Vector((hw, y, (zb + zs) / 2))]
    for i in range(k + 1):
        t = (math.pi / 2) * i / k
        pts.append(Vector((hw * math.cos(t) ** (2 / n_exp), y, zs + (zt - zs) * math.sin(t) ** (2 / n_exp))))
    for i in range(k - 1, -1, -1):
        t = (math.pi / 2) * i / k
        pts.append(Vector((-hw * math.cos(t) ** (2 / n_exp), y, zs + (zt - zs) * math.sin(t) ** (2 / n_exp))))
    pts += [Vector((-hw, y, (zb + zs) / 2)), Vector((-hw, y, zb))]
    return pts


def t_hood_cowl(B):
    secs = [hood_section(-1.535, 0.236, 0.64, 1.05, 1.135, 3.2),
            hood_section(-0.88, 0.252, 0.64, 1.07, 1.168, 3.2)]
    for i in range(1, 11):
        t = i / 10
        e = sstep(t)
        y = lerp(-0.88, BODY_Y0 + 0.004, t)
        secs.append(hood_section(y, lerp(0.252, BODY_W + 0.002, e), 0.60 + 0.04 * (1 - e),
                                 lerp(1.07, 1.035, e), lerp(1.168, 1.236, t ** 0.85), lerp(3.2, 3.0, t)))
    B.loop_loft(secs, "enamel", closed=False, caps=True)


def outline_offset(pts, d):
    """Offset a closed 2D outline (x, z) by d along its outward normals (counter-clockwise)."""
    out = []
    n = len(pts)
    for i in range(n):
        p, a, b = Vector(pts[i]), Vector(pts[i - 1]), Vector(pts[(i + 1) % n])
        e1 = (p - a).normalized()
        e2 = (b - p).normalized()
        n1 = Vector((e1.y, -e1.x))
        n2 = Vector((e2.y, -e2.x))
        bis = (n1 + n2).normalized()
        out.append(p + bis * d / max(0.4, bis.dot(n1)))
    return out


def radiator_outline(hx, z0, zs, zt, rc, k=5):
    """Counter-clockwise (seen from the front, x to the right = -X world... we use plain x) outline:
    flat bottom, straight sides, rounded shoulders, arched top."""
    pts = [(-hx, z0), (hx, z0)]
    for i in range(k + 1):
        a = math.radians(90 * i / k)
        pts.append((hx - rc + rc * math.cos(a), zs - rc + rc * math.sin(a)))
    # arch from (hx - rc, zs) to (-(hx - rc), zs), peak zt
    for i in range(1, 6):
        u = i / 6
        x = lerp(hx - rc, -(hx - rc), u)
        pts.append((x, zs + (zt - zs) * math.sin(math.pi * u)))
    for i in range(k + 1):
        a = math.radians(90 + 90 * i / k)
        pts.append((-(hx - rc) + rc * math.cos(a), zs - rc + rc * math.sin(a)))
    return pts


def t_radiator(B):
    yf, yb = -1.645, -1.53
    outer = radiator_outline(0.25, 0.60, 1.165, 1.212, 0.06)
    inner = radiator_outline(0.198, 0.665, 1.105, 1.135, 0.035)
    bev = 0.012

    def loop(pts2, y):
        return [Vector((p[0], y, p[1])) for p in pts2]
    o_in = outline_offset(outer, -bev)
    i_out = outline_offset(inner, 0.008)
    # outer and inner outlines must have the same point count for the loft
    loops = [loop(outer, yb), loop(outer, yf + bev), loop(o_in, yf), loop(i_out, yf), loop(inner, yf + 0.008),
             loop(inner, yb)]
    B.loop_loft(loops, "enamel", closed=True)
    # core: vertical tubes (zigzag), recessed
    n = 24
    with B.part(recalc=False):
        top = []
        bot = []
        for j in range(n * 2 + 1):
            x = lerp(-0.205, 0.205, j / (n * 2))
            y = -1.612 if j % 2 == 0 else -1.600
            top.append(B.vert((x, y, 1.15)))
            bot.append(B.vert((x, y, 0.655)))
        B.grid([bot, top], "radiator_core", d=(0, -1, 0))
        # horizontal fin bands
    for z in (0.72, 0.82, 0.92, 1.02):
        B.rbox((0, -1.613, z), (0.41, 0.004, 0.006), "radiator_core", bev=0)
    # filler neck and cap on the top tank
    B.lathe([(0.0, 0.0), (0.024, 0.0), (0.024, 0.022), (0.036, 0.026), (0.038, 0.040), (0.032, 0.050),
             (0.012, 0.054), (0.0, 0.055)], 10, "enamel", T(0, -1.588, 1.200))
    # radiator apron / splash below the shell and the front crossmember
    B.rbox((0, -1.585, 0.575), (0.56, 0.10, 0.05), "enamel", bev=0.012, seg=1)


def t_fenders(B):
    K = "enamel"

    def fsec(hw, c=0.028):
        pts = []
        for i in range(5):
            l = -hw + 2 * hw * i / 4
            pts.append((l, c * (1 - (l / hw) ** 2)))
        pts += [(hw + 0.007, -0.009), (hw - 0.002, -0.018)]
        for l in (0.5 * hw, -0.5 * hw):
            pts.append((l, c * (1 - (l / hw) ** 2) * 0.95 - 0.0055))
        pts += [(-hw + 0.002, -0.018), (-hw - 0.007, -0.009)]
        return pts

    zc = 0.375
    Rf = 0.455
    front = []
    for a in (168, 150, 130, 110, 90, 70, 52):
        front.append((FA_T + Rf * math.cos(math.radians(a)), zc + Rf * math.sin(math.radians(a))))
    front += [(-0.925, 0.665), (-0.865, 0.545), (-0.81, 0.462), (-0.74, 0.440), (-0.70, 0.438)]
    # front tip turns down a little (the "bill")
    front.insert(0, (FA_T + Rf * math.cos(math.radians(178)) - 0.01, zc + Rf * math.sin(math.radians(178)) - 0.03))
    rear = [(0.70, 0.438), (0.76, 0.442), (0.83, 0.475), (0.89, 0.55), (0.95, 0.65)]
    for a in (124, 105, 85, 65, 45, 25, 8):
        rear.append((RA_T + 0.47 * math.cos(math.radians(a)), 0.38 + 0.47 * math.sin(math.radians(a))))
    for s in (1, -1):
        for path, hw, n in ((front, 0.112, 14), (rear, 0.122, 12)):
            pts = smooth_path([(s * (TR_T + 0.004), y, z) for y, z in path], n)
            B.sweep(pts, fsec(hw), K, lat=(1, 0, 0))     # same lateral axis both sides: crown up on both
    # running boards (linoleum-topped steel, rolled edge) on three brackets each, splash aprons
    for s in (1, -1):
        B.rbox((s * 0.705, -0.01, 0.428), (0.25, 1.55, 0.022), K, bev=0.008, seg=1)
        B.rbox((s * 0.705, -0.01, 0.4405), (0.225, 1.50, 0.004), "rubber", bev=0)
        B.rbox((s * 0.566, -0.01, 0.512), (0.008, 1.50, 0.15), K, bev=0)
        for y in (-0.55, 0.0, 0.55):
            B.beam((s * 0.37, y, 0.505), (s * 0.80, y, 0.405), 0.03, 0.008, "iron", hint=(0, 0, 1), bev=0)
            B.beam((s * 0.37, y, 0.505), (s * 0.40, y, 0.405), 0.03, 0.008, "iron", hint=(1, 0, 0), bev=0)
        # splash shelf between the hood and the front fender
        B.rbox((s * 0.43, -1.20, 0.625), (0.33, 0.66, 0.008), K, bev=0)


def t_lamps(B):
    K = "enamel"
    # electric headlamps on fork brackets from the frame horns
    for s in (1, -1):
        c = Vector((s * 0.385, -1.585, 0.985))
        M = T(*c) @ ROT_X90
        prof = [(0.0, -0.125), (0.062, -0.112), (0.096, -0.076), (0.107, -0.030), (0.107, 0.0),
                (0.115, 0.008), (0.113, 0.021), (0.099, 0.025), (0.095, 0.015),
                (0.050, -0.030), (0.0, -0.052)]
        mats = [K] * 8 + ["reflector"] * 3
        B.lathe(prof, 14, mats, M)
        with B.part(recalc=False):
            rings = []
            for r, z in ((0.098, 0.019), (0.055, 0.031), (0.0, 0.036)):
                if r == 0:
                    v = B.vert(M @ Vector((0, 0, z)))
                    rings.append([v] * 14)
                else:
                    rings.append([B.vert(M @ Vector((r * math.cos(2 * math.pi * j / 14), r * math.sin(2 * math.pi * j / 14), z)))
                                  for j in range(14)])
            B.grid(rings, "glass", closed_v=True, d=(0, -1, 0))
        # fork bracket and stem down to the frame horn
        for d in (-1, 1):
            B.tube([c + Vector((d * 0.104, 0.0, 0.0)), c + Vector((d * 0.10, 0.0, -0.07)),
                    c + Vector((d * 0.006, 0.0, -0.125))], 0.008, 6, "iron")
        B.tube([c + Vector((0, 0, -0.115)), Vector((s * 0.372, -1.575, 0.70)), Vector((s * 0.36, -1.565, 0.54))],
               0.012, 6, "iron")
        # oil side lamps on the cowl
        cy, cz = -0.58, 1.00
        cx = s * 0.575
        B.rbox((cx, cy, cz), (0.085, 0.095, 0.14), K, bev=0.012, seg=1)
        B.lathe([(0.0, 0.0), (0.048, 0.0), (0.050, 0.012), (0.028, 0.03), (0.016, 0.07), (0.022, 0.08), (0.0, 0.085)],
                8, K, T(cx, cy, cz + 0.07))
        B.lathe([(0.0, 0.0), (0.036, 0.0), (0.040, 0.012), (0.0, 0.016)], 14, K, T(cx, cy - 0.047, cz) @ ROT_X90)
        with B.part(recalc=False):
            B.face([B.vert(T(cx, cy - 0.064, cz) @ ROT_X90 @ Vector((0.03 * math.cos(2 * math.pi * j / 14),
                                                                      0.03 * math.sin(2 * math.pi * j / 14), 0)))
                    for j in range(14)], "glass", d=(0, -1, 0))
        B.beam((cx, cy, cz - 0.02), (s * 0.475, cy, cz - 0.03), 0.02, 0.012, "iron", hint=(0, 0, 1))
    # tail lamp on a bracket at the left rear
    c = Vector((0.40, 1.80, 0.70))
    M = T(*c) @ ROT_XM90
    B.lathe([(0.0, -0.05), (0.04, -0.05), (0.046, -0.03), (0.046, 0.03), (0.04, 0.04), (0.03, 0.042),
             (0.0, 0.04)], 12, K, M)
    with B.part(recalc=False):
        B.face([B.vert(M @ Vector((0.031 * math.cos(2 * math.pi * j / 12), 0.031 * math.sin(2 * math.pi * j / 12), 0.0425)))
                for j in range(12)], "glass", d=(0, 1, 0))
    B.lathe([(0.0, 0.0), (0.02, 0.0), (0.018, 0.05), (0.0, 0.055)], 8, K, T(*c) @ T(0, 0, 0.046))
    B.beam((0.40, 1.74, 0.62), (0.40, 1.80, 0.655), 0.03, 0.006, "iron", hint=(1, 0, 0))
    B.beam((0.40, 1.54, 0.58), (0.40, 1.74, 0.62), 0.03, 0.006, "iron", hint=(1, 0, 0))


def t_windshield(B):
    K = "enamel"
    WY = -0.44
    zb, zm, zt = 1.236, 1.512, 1.792
    for s in (1, -1):
        B.beam((s * 0.548, WY, 1.00), (s * 0.548, WY, zt + 0.012), 0.026, 0.024, K, hint=(0, 1, 0), bev=0.006, seg=1)
        B.beam((s * 0.548, WY - 0.004, 1.02), (s * 0.535, WY - 0.08, 1.07), 0.03, 0.01, "iron", hint=(1, 0, 0))
    for z in (zb, zm - 0.008, zm + 0.008, zt):
        B.beam((-0.536, WY, z), (0.536, WY, z), 0.022, 0.026, K, hint=(0, 0, 1), bev=0.005, seg=1)
    for z0, z1 in ((zb + 0.008, zm - 0.016), (zm + 0.016, zt - 0.008)):
        B.rbox((0, WY, (z0 + z1) / 2), (1.07, 0.006, z1 - z0 + 0.01), "glass", bev=0)
    # two leather straps from the top's front bow down to the windshield frame (buckled round the
    # top rail beside the posts)
    for s in (1, -1):
        x = s * 0.47
        pts = [(x, WY - 0.006, zt - 0.012), (x, WY - 0.016, zt + 0.006), (x, WY + 0.0, zt + 0.022),
               (x, -0.405, 1.846), (x, T_HEADER + 0.004, 1.866)]
        B.sweep(smooth_path(pts, 7, 3), rect_sec(0.032, 0.004), "leather", lat=(1, 0, 0))
        B.rbox((x, WY - 0.016, zt + 0.004), (0.038, 0.006, 0.026), "iron", bev=0)      # buckle


def t_steering(B):
    K = "enamel"
    col0 = Vector((0.27, -0.56, 0.90))
    col1 = Vector((0.27, -0.16, 1.24))
    B.tube([col0, col1], 0.021, 10, K, nrm=(1, 0, 0))
    ax = (col1 - col0).normalized()
    hub = col1 + ax * 0.03
    B.ring(hub + ax * 0.015, 0.19, 0.013, 28, 4, K, ax, ellipse=(0.014, 0.012))
    u = ax.cross(Vector((1, 0, 0))).normalized()
    v = ax.cross(u)
    for k in range(4):
        a = 2 * math.pi * (k + 0.5) / 4
        d = math.cos(a) * u + math.sin(a) * v
        B.tube([hub, hub + ax * 0.012 + d * 0.18], [(0.006, 0.012), (0.005, 0.009)], 6, K, nrm=ax)
    B.lathe([(0.0, -0.03), (0.032, -0.03), (0.036, 0.0), (0.028, 0.025), (0.0, 0.03)], 12, K,
            T(*hub) @ frame_from(ax))
    # spark and throttle quadrant with the two levers under the wheel
    q = col1 - ax * 0.06
    B.lathe([(0.0, -0.006), (0.075, -0.006), (0.075, 0.006), (0.0, 0.006)], 14, "iron", T(*q) @ frame_from(ax))
    for k, a in enumerate((0.6, 2.4)):
        d = math.cos(a) * u + math.sin(a) * v
        B.tube([q + ax * 0.012, q + ax * 0.012 + d * 0.13], [0.005, 0.004], 5, "iron", nrm=ax)


def t_chassis(B):
    K = "enamel"
    for s in (1, -1):                       # side rails, running forward to the frame horns
        B.rbox((s * 0.36, -0.0175, 0.525), (0.045, 3.185, 0.095), K, bev=0.006)
    # front cross-member between the horns, under the radiator apron
    B.beam((-0.38, -1.585, 0.515), (0.38, -1.585, 0.515), 0.05, 0.08, K, hint=(0, 0, 1), bev=0.008, seg=1)
    # front: I-beam axle, spindles, transverse spring, radius rods, crank
    zc = 0.375
    B.beam((-0.63, FA_T, zc - 0.012), (0.63, FA_T, zc - 0.012), 0.042, 0.06, K, hint=(0, 0, 1), bev=0.008, seg=1)
    for s in (1, -1):
        B.lathe([(0.0, -0.05), (0.03, -0.05), (0.03, 0.05), (0.0, 0.05)], 10, K, T(s * 0.645, FA_T, zc))
        # spindle stub from the king pin into the hub (front wheels have 3 deg positive camber)
        B.tube([(s * 0.64, FA_T, zc), (s * (TR_T - 0.02), FA_T, zc + 0.002)], 0.016, 6, "iron", nrm=(0, 0, 1))
        B.tube([(s * 0.62, FA_T + 0.02, zc - 0.01), (s * 0.30, -0.95, zc + 0.01), (0, -0.62, 0.40)], 0.013, 6, K)
    leaf_spring(B, lambda u, k: Vector((u * 0.56, FA_T, 0.445 + 0.11 * (1 - u * u) + k * 0.009)), 0.56, 2, 0.045,
                0.008, K, (0, 1, 0))
    for s in (1, -1):
        B.beam((s * 0.56, FA_T, 0.44), (s * 0.56, FA_T, zc + 0.01), 0.03, 0.03, "iron", hint=(1, 0, 0))
    B.rbox((0, FA_T, 0.575), (0.78, 0.07, 0.05), K, bev=0.01)
    # starting crank, permanently fitted: shaft from the crankcase nose through a bearing boss in the
    # front cross-member, arm hanging straight down at rest, grip pointing forward
    zk, yk = 0.505, -1.715
    B.tube([(0, -1.50, zk), (0, yk + 0.006, zk)], 0.012, 8, "iron", nrm=(0, 0, 1))
    B.lathe([(0.0, 0.0), (0.032, 0.0), (0.032, 0.035), (0.020, 0.05), (0.0, 0.05)], 12, "iron",
            T(0, -1.605, zk) @ ROT_X90)                          # bearing boss on the cross-member
    B.lathe([(0.0, -0.012), (0.019, -0.012), (0.019, 0.012), (0.0, 0.012)], 10, "iron", T(0, yk, zk) @ ROT_X90)
    B.beam((0, yk, zk), (0, yk, zk - 0.17), 0.028, 0.012, "iron", hint=(0, 1, 0), bev=0.003)
    B.lathe([(0.0, -0.01), (0.014, -0.01), (0.018, 0.02), (0.018, 0.085), (0.012, 0.10), (0.0, 0.10)], 8,
            "iron", T(0, yk + 0.004, zk - 0.165) @ ROT_X90)        # grip on its pin, pointing forward
    # engine, pan, transmission, torque tube, rear axle with the differential, rear spring, muffler
    B.rbox((0, -1.17, 0.70), (0.34, 0.62, 0.34), "iron", bev=0.03, seg=1)
    B.rbox((0, -1.0, 0.47), (0.30, 1.05, 0.14), "iron", bev=0.04, seg=1)
    B.tube([(0, -0.48, 0.47), (0, 0.2, 0.43), (0, RA_T - 0.10, 0.385)], [0.06, 0.04, 0.035], 8, "iron")
    rprof = [(0.0, -0.68), (0.042, -0.68), (0.035, -0.60), (0.035, -0.22), (0.07, -0.14),
             (0.112, 0.0), (0.07, 0.14), (0.035, 0.22), (0.035, 0.60), (0.042, 0.68), (0.0, 0.68)]
    B.lathe(rprof, 8, "iron", T(0, RA_T, 0.38) @ ROT_Y90)
    leaf_spring(B, lambda u, k: Vector((u * 0.56, RA_T + 0.02, 0.44 + 0.10 * (1 - u * u) + k * 0.009)), 0.56, 2,
                0.045, 0.008, K, (0, 1, 0))
    B.rbox((0, RA_T + 0.02, 0.565), (0.78, 0.07, 0.05), K, bev=0.01)
    B.tube([(-0.22, -0.70, 0.46), (-0.22, -0.40, 0.42), (-0.22, 0.25, 0.42)], 0.055, 6, "iron")
    B.tube([(-0.22, 0.25, 0.42), (-0.24, 0.70, 0.42)], 0.016, 6, "iron")
    # exhaust pipe from the manifold (engine side) and two hanger straps to the right frame rail
    B.tube(smooth_path([(-0.22, -0.66, 0.47), (-0.21, -0.92, 0.55), (-0.15, -1.12, 0.66)], 6, 3), 0.02, 6, "iron")
    for y in (-0.45, 0.12):
        B.beam((-0.22, y, 0.45), (-0.36, y, 0.505), 0.03, 0.006, "iron", hint=(0, 0, 1), bev=0)


T_HEADER = -0.385                              # front bow (header) of the Model T top
T_BOWS = [0.30, 0.90, 1.46]                    # bows hinged at the pivot, front to rear
T_PIVOT = (1.18, 1.052)                        # (y, z) on the body side behind the rear door
T_HW = 0.585                                   # half width of the roof


def t_zr(y):
    t = (y + 0.43) / 1.75
    return 1.862 + 0.022 * t + 0.012 * math.sin(math.pi * t)


def t_top(B):
    """1917-20 Ford 'one-man' touring top, up: fabric roof from the front bow (header) to the rear
    bow with a slight sag between the bows and a short valance, rear curtain with quarters down to
    the body behind the pivots and a small celluloid back light, open sides (no side curtains up).
    Three bows hinge on one iron pivot each side; the header rides on the side rails (top irons) and
    is strapped to the windshield (t_windshield)."""
    F, hw, val, crown = "top_fabric", T_HW, 0.045, 0.032
    zr = t_zr
    allb = [T_HEADER] + T_BOWS
    yf, yr = T_HEADER - 0.02, T_BOWS[-1] + 0.07

    def sagf(y):
        for a, b in zip(allb, allb[1:]):
            if a <= y <= b:
                return 0.018 * math.sin(math.pi * (y - a) / (b - a)) ** 1.5
        return 0.0
    pads = 0.49
    lat = [(-hw, -val, False), (-hw - 0.002, -0.014, False), (-hw + 0.014, 0.0, False),
           (-pads - 0.03, None, True), (-pads, "pad", True), (-pads + 0.04, None, True),
           (-hw * 0.4, None, True), (0.0, None, True)]
    lat = lat + [(-l, n, i) for l, n, i in reversed(lat[:-1])]

    def roof_z(l, y):
        return zr(y) + crown * (1 - (l / hw) ** 2) - sagf(y) * (1 - (l / hw) ** 2) ** 0.6

    def roof_row(y, dz=0.0, dy=0.0):
        row = []
        for l, n, _ in lat:
            if n is None or n == "pad":
                z = roof_z(l, y) + (0.006 if n == "pad" else 0.0)
            else:
                z = zr(y) + n
            row.append(Vector((l, y + dy, z + dz)))
        return row
    ys = sorted(set([round(yf + (yr - yf) * i / 7, 4) for i in range(8)] + allb))
    ys = [y for i, y in enumerate(ys) if i == 0 or y - ys[i - 1] > 0.03 or y in allb]
    G = [roof_row(yf, -val, 0.004), roof_row(yf, -0.014)] + [roof_row(y) for y in ys] +         [roof_row(yr, -0.014), roof_row(yr, -0.03, -0.004)]
    B.sheet(G, 0.006, F)

    # rear curtain + quarters: loft from the body rim (behind the pivots, round the back) up to the
    # roof's rear edge; columns: side 3, corner 5, back 3, corner 5, side 3
    def plan_loop(xs, y0, ycs, xc, rc, yb):
        pts = []
        for k in range(3):
            pts.append((Vector((xs, lerp(y0, ycs, k / 2), 0)), Vector((1, 0, 0))))
        for k in range(1, 6):
            a = math.radians(90 * k / 5)
            n = Vector((math.cos(a), math.sin(a), 0))
            pts.append((Vector((xc, ycs, 0)) + n * rc, n))
        for x in (0.16, 0.0, -0.16):
            pts.append((Vector((x, yb, 0)), Vector((0, 1, 0))))
        for k in range(0, 5):
            a = math.radians(90 + 90 * k / 5)
            n = Vector((math.cos(a), math.sin(a), 0))
            pts.append((Vector((-xc, ycs, 0)) + n * rc, n))
        for k in range(2, -1, -1):
            pts.append((Vector((-xs, lerp(y0, ycs, k / 2), 0)), Vector((-1, 0, 0))))
        return pts
    py, pz = T_PIVOT
    bot = plan_loop(0.545, py, 1.33, 0.205, 0.34, 1.67)
    yrb = T_BOWS[-1]
    top = plan_loop(hw - 0.004, yrb, yr - 0.046, hw - 0.044, 0.04, yr - 0.006)
    ws = (0.0, 0.25, 0.50, 0.72, 1.0)
    C = []
    for w in ws:
        row = []
        for (pb, nb), (pt, nt) in zip(bot, top):
            p = pb.lerp(pt, w)
            zt = roof_z(min(abs(pt.x), hw), pt.y) - 0.012
            p.z = lerp(1.040, zt, w)
            p -= nb * 0.012 * math.sin(math.pi * w)           # fabric sags in a little
            row.append(p)
        C.append(row)
    win = [(2, 8), (2, 9)]                                     # back light: rows 2-3, x -0.16..0.16
    B.sheet_holed(C, 0.006, F, skip=win)
    # back light: celluloid pane and its stitched binding
    corners = [C[2][8], C[2][9], C[2][10], C[3][10], C[3][9], C[3][8]]
    with B.part(recalc=False):
        B.face([B.vert(p) for p in corners], "glass", d=(0, 1, 0))
    B.tube(corners, 0.0055, 4, "leather", closed=True, nrm=(0, 1, 0))
    # welt over the roof / curtain seam and a binding along the curtain foot on the body rim
    B.tube(smooth_path([p + Vector((0, 0.004, 0.002)) for p in C[-1]], 21, 3), 0.006, 4, F, nrm=(0, 0, 1))
    B.tube(smooth_path([p + Vector((0, 0, 0.004)) for p in C[0]], 21, 3), 0.007, 4, "leather", nrm=(0, 0, 1))

    # bows: across under the fabric; the three hinged bows have legs down to the pivots
    for yb in allb:
        acr = [Vector((l, yb, roof_z(l, yb) - 0.013)) for l in (-hw + 0.012, -hw * 0.6, 0.0, hw * 0.6, hw - 0.012)]
        el = Vector((-hw + 0.004, yb, zr(yb) - val + 0.008))
        er = Vector((hw - 0.004, yb, zr(yb) - val + 0.008))
        if yb == T_HEADER:
            pts = [el] + acr + [er]
        else:
            pl, pr = Vector((-0.572, py, pz)), Vector((0.572, py, pz))
            pts = [pl, pl.lerp(el, 0.5), el] + acr + [er, pr.lerp(er, 0.5), pr]
        B.tube(smooth_path(pts, 13 if yb != T_HEADER else 7, 4), (0.017, 0.010), 4, "enamel",
               nrm=(0, 1, 0), phase=math.pi / 4)
    # side rails (top irons) under the roof edge from the header to the rear bow
    for s in (1, -1):
        B.tube([Vector((s * (hw - 0.016), y, zr(y) - 0.012)) for y in (T_HEADER, T_BOWS[0], T_BOWS[1], yrb)],
               0.008, 4, "enamel", nrm=(0, 0, 1))
        # pivot: iron plate on the body side with the hinge bolt
        B.rbox((s * 0.566, py, pz - 0.02), (0.014, 0.07, 0.08), "iron", bev=0.004)
        B.lathe([(0.0, -0.016), (0.026, -0.016), (0.026, 0.016), (0.012, 0.024), (0.0, 0.024)], 10, "iron",
                T(s * 0.578, py, pz) @ (ROT_Y90 if s > 0 else ROT_YM90))


def build_model_t():
    B = Builder()
    for y, rear in ((FA_T, False), (RA_T, True)):
        for s in (1, -1):
            wheel_model_t(B, s * TR_T, y, s, 0.381, rear, 0.0 if rear else math.radians(3.0))
    t_chassis(B)
    t_body(B)
    t_hood_cowl(B)
    t_radiator(B)
    t_fenders(B)
    t_lamps(B)
    t_windshield(B)
    t_steering(B)
    t_top(B)
    return B


# ----------------------------------------------------------------------------------------------
# F13 piano-box top buggy, shafts down, no horse
# ----------------------------------------------------------------------------------------------
def box_body(B, hw, y0, y1, rc, prof, mat, ridges=(), closed_floor=None):
    """Closed plan loop (rounded rectangle) swept with a closed profile; vertical moulding ridges at
    the given y on both long sides."""
    plan = []

    def add_side(x, ya, yb, sgn):
        ys = {ya, yb}
        for r in ridges:
            ys |= {r - 0.008, r, r + 0.008}
        for y in sorted(ys, reverse=yb < ya):
            if min(ya, yb) <= y <= max(ya, yb):
                plan.append((x, y, sgn, 0.0, any(abs(y - r) < 1e-6 for r in ridges)))
    add_side(hw, y0 + rc, y1 - rc, 1)
    for k in range(1, 3):
        a = math.radians(90 * k / 3)
        plan.append((hw - rc + rc * math.cos(a), y1 - rc + rc * math.sin(a), math.cos(a), math.sin(a), False))
    plan.append((hw - rc, y1, 0, 1, False))
    plan.append((-(hw - rc), y1, 0, 1, False))
    for k in range(1, 3):
        a = math.radians(90 + 90 * k / 3)
        plan.append((-(hw - rc) + rc * math.cos(a), y1 - rc + rc * math.sin(a), math.cos(a), math.sin(a), False))
    add_side(-hw, y1 - rc, y0 + rc, -1)
    for k in range(1, 3):
        a = math.radians(180 + 90 * k / 3)
        plan.append((-(hw - rc) + rc * math.cos(a), y0 + rc + rc * math.sin(a), math.cos(a), math.sin(a), False))
    plan.append((-(hw - rc), y0, 0, -1, False))
    plan.append(((hw - rc), y0, 0, -1, False))
    for k in range(1, 3):
        a = math.radians(270 + 90 * k / 3)
        plan.append(((hw - rc) + rc * math.cos(a), y0 + rc + rc * math.sin(a), math.cos(a), math.sin(a), False))
    rings = []
    for x, y, nx, ny, ridge in plan:
        rings.append([Vector((x + nx * (o + (0.006 if ridge and o > -0.001 else 0)),
                              y + ny * (o + (0.006 if ridge and o > -0.001 else 0)), z)) for o, z in prof])
    B.loop_loft(rings, mat, closed=True)


def build_buggy():
    B = Builder()
    K, G = "satin_black", "gear_paint"
    FA, RA, RF, RR, TR = -0.80, 0.82, 0.49, 0.535, 0.69
    for y, R, n in ((FA, RF, 14), (RA, RR, 16)):
        for s in (1, -1):
            wheel_carriage(B, s * TR, y, s, R, n, 0.024, 0.042, 0.030, 0.052, 0.20, 0.022)
    # axles (iron, in wood beds), beds, head block, fifth wheel, springs, reach and stays
    for y, R in ((FA, RF), (RA, RR)):
        B.beam((-0.60, y, R), (0.60, y, R), 0.032, 0.032, "iron", hint=(0, 0, 1), bev=0.005)
        B.beam((-0.58, y, R + 0.035), (0.58, y, R + 0.035), 0.05, 0.042, G, hint=(0, 0, 1), bev=0.008, seg=2)
    B.ring((0, FA, RF + 0.060), 0.16, 0.0, 18, 4, "iron", (0, 0, 1), ellipse=(0.008, 0.012))
    B.beam((-0.42, FA, RF + 0.095), (0.42, FA, RF + 0.095), 0.06, 0.045, G, hint=(0, 0, 1), bev=0.01, seg=2)
    elliptic_spring(B, (0, FA, (RF + 0.12 + 0.795) / 2), 0.30, (0.795 - RF - 0.12) / 2, "x", "iron", leaves=1, t=0.011)
    elliptic_spring(B, (0, RA, (RR + 0.06 + 0.795) / 2), 0.31, (0.795 - RR - 0.06) / 2, "x", "iron", leaves=1, t=0.011)
    for y in (FA, RA):
        B.beam((-0.33, y, 0.80), (0.33, y, 0.80), 0.05, 0.03, G, hint=(0, 0, 1), bev=0.008)   # spring bars
    reach = smooth_path([(0, RA + 0.05, RR + 0.01), (0, 0.1, RR + 0.045), (0, FA + 0.05, RF + 0.11)], 8)
    B.tube(reach, (0.022, 0.018), 6, G, nrm=(0, 0, 1))
    for s in (1, -1):
        B.tube([(s * 0.45, RA, RR + 0.005), (s * 0.12, RA - 0.45, RR + 0.03), (0, 0.0, RR + 0.04)], 0.009, 6, "iron")
    # piano-box body with moulding lines
    prof = [(-0.012, 0.795), (0.008, 0.805), (0.008, 0.826), (0.0, 0.836), (0.0, 1.000),
            (0.008, 1.012), (0.008, 1.036), (-0.004, 1.048), (-0.020, 1.044), (-0.022, 0.84)]
    box_body(B, 0.31, -0.72, 0.76, 0.025, prof, K, ridges=(-0.26, 0.30))
    B.rbox((0, 0.02, 0.845), (0.58, 1.44, 0.016), K, bev=0.003)
    B.rbox((0, 0.02, 0.81), (0.30, 1.70, 0.055), G, bev=0.006)       # body sills, resting on the spring bars
    # seat: panelled seat box, rolled cushion, pleated lazy back with roll, iron arm rails
    B.rbox((0, 0.42, 1.10), (0.68, 0.52, 0.10), K, bev=0.008, seg=1)
    B.rbox((0, 0.40, 1.185), (0.64, 0.46, 0.085), "leather", bev=0.035, seg=2)
    B.tube([(-0.31, 0.18, 1.19), (0.31, 0.18, 1.19)], 0.032, 8, "leather")
    pleated_back(B, -0.30, 0.30, 1.14, 1.50, 0.64, math.radians(10), 6, panel=K)
    for s in (1, -1):
        B.tube(smooth_path([(s * 0.335, 0.70, 1.46), (s * 0.345, 0.55, 1.36), (s * 0.34, 0.30, 1.29),
                            (s * 0.335, 0.18, 1.18)], 7), 0.008, 5, "iron")
    # dash: patent leather on an iron rod frame, curved, leaning forward
    G2 = []
    for i in range(5):
        t = i / 4
        y = lerp(-0.735, -0.86, t) - 0.012 * math.sin(math.pi * t)
        z = lerp(1.045, 1.36, t)
        G2.append([Vector((lerp(-0.30, 0.30, j / 6), y + 0.025 * (1 - (lerp(-1, 1, j / 6)) ** 2), z)) for j in range(7)])
    B.sheet(G2, 0.008, "leather")
    rim = [G2[0][0], G2[-1][0], G2[-1][3], G2[-1][6], G2[0][6]]
    B.tube(smooth_path([G2[i][0] for i in range(5)] + [G2[4][j] for j in range(1, 7)] + [G2[i][6] for i in range(3, -1, -1)], 24, 3),
           0.006, 5, "iron")
    for s in (1, -1):
        B.tube([(s * 0.30, -0.80, 1.20), (s * 0.31, -0.70, 1.05)], 0.006, 6, "iron")
    # step plates on iron shanks
    for s in (1, -1):
        B.tube([(s * 0.30, 0.10, 0.82), (s * 0.36, 0.07, 0.70), (s * 0.40, 0.06, 0.61)], 0.011, 6, "iron")
        B.lathe([(0.0, -0.006), (0.055, -0.006), (0.06, 0.0), (0.055, 0.006), (0.0, 0.006)], 14, "iron",
                T(s * 0.42, 0.06, 0.60))
    # folding top with bows, joints and the back curtain
    def zr(y):
        t = (y + 0.12) / 0.86
        return 2.11 + 0.012 * t + 0.01 * math.sin(math.pi * t)
    folding_top(B, 0.40, 0.345, [-0.10, 0.17, 0.42, 0.64], zr, (0.46, 1.30), 0.78, 1.24, 0.08, "top_fabric",
                K, sag=0.014, bow_size=(0.014, 0.008), rows=8, corner=3, hood_ws=(0.0, 0.25, 0.5, 0.75, 0.97), hood_from=2)
    for s in (1, -1):        # top joints: jointed props from the front bow leg to the third bow leg
        def leg(yb, w):
            e = Vector((s * (0.40 - 0.004), yb, zr(yb) - 0.039))
            p = Vector((s * (0.345 + 0.012), 0.46, 1.30))
            return p.lerp(e, w)
        a = leg(-0.10, 0.42)
        b = leg(0.42, 0.40)
        k = (a + b) / 2 + Vector((s * 0.03, 0, -0.035))
        B.tube([a, k], 0.007, 6, "iron")
        B.tube([k, b], 0.007, 6, "iron")
        B.lathe([(0.0, -0.012), (0.014, -0.008), (0.014, 0.008), (0.0, 0.012)], 8, "iron",
                T(*k) @ (ROT_Y90 if s > 0 else ROT_YM90))
        for p in (a, b):
            B.lathe([(0.0, -0.008), (0.011, -0.008), (0.011, 0.012), (0.0, 0.012)], 8, "iron",
                    T(*p) @ (ROT_Y90 if s > 0 else ROT_YM90))
    for s in (1, -1):        # seat irons carrying the top pivots down to the seat box sides
        B.beam((s * 0.349, 0.46, 1.318), (s * 0.349, 0.46, 1.10), 0.03, 0.012, "iron", hint=(1, 0, 0), bev=0)
    shafts(B, FA, RF, 0.39, 0.33, G, 2.40)
    return B


# ----------------------------------------------------------------------------------------------
# F14 light delivery wagon, open plank box, shafts down, no horse, unlettered
# ----------------------------------------------------------------------------------------------
def build_delivery_wagon():
    B = Builder()
    K, W, G = "satin_black", "wagon_wood", "gear_paint"
    FA, RA, RF, RR, TR = -0.95, 0.95, 0.45, 0.53, 0.73
    for y, R, n in ((FA, RF, 12), (RA, RR, 14)):
        for s in (1, -1):
            wheel_carriage(B, s * TR, y, s, R, n, 0.038, 0.05, 0.038, 0.06, 0.24, 0.026, nseg=32, hub_seg=12)
    # axles, sand board, fifth wheel, front cross spring, rear side springs, bolsters, reach
    for y, R in ((FA, RF), (RA, RR)):
        B.beam((-0.64, y, R), (0.64, y, R), 0.04, 0.04, "iron", hint=(0, 0, 1), bev=0.006)
        B.beam((-0.60, y, R + 0.045), (0.60, y, R + 0.045), 0.065, 0.05, G, hint=(0, 0, 1), bev=0.01)
    B.ring((0, FA, RF + 0.08), 0.20, 0.0, 16, 3, "iron", (0, 0, 1), ellipse=(0.009, 0.014))
    B.rbox((0, FA, RF + 0.085), (0.30, 0.07, 0.036), G, bev=0.006)          # head block under the spring
    for s in (1, -1):                                                         # rear spring seats on the bed
        B.rbox((s * 0.44, RA, RR + 0.076), (0.05, 0.08, 0.016), "iron", bev=0)
    elliptic_spring(B, (0, FA, (RF + 0.10 + 0.84) / 2), 0.36, (0.84 - RF - 0.10) / 2, "x", "iron", w=0.045,
                    t=0.012, leaves=1)
    for s in (1, -1):
        elliptic_spring(B, (s * 0.44, RA, (RR + 0.075 + 0.84) / 2), 0.38, (0.84 - RR - 0.075) / 2, "y", "iron",
                        w=0.045, t=0.012, leaves=1)
    B.beam((-0.56, FA, 0.865), (0.56, FA, 0.865), 0.08, 0.05, G, hint=(0, 0, 1), bev=0.01)   # bolsters
    B.beam((-0.56, RA, 0.865), (0.56, RA, 0.865), 0.08, 0.05, G, hint=(0, 0, 1), bev=0.01)
    B.tube(smooth_path([(0, RA + 0.05, RR + 0.02), (0, 0.0, 0.56), (0, FA + 0.05, RF + 0.11)], 8), (0.026, 0.022), 8, G)
    # box: sills, floor boards, three boards a side, front end boards, tailgate
    x_in, x_out = 0.52, 0.542
    y0, y1 = -1.10, 1.48
    for s in (1, -1):
        B.beam((s * 0.40, y0, 0.905), (s * 0.40, y1, 0.905), 0.07, 0.05, G, hint=(0, 0, 1), bev=0.008)
    bi = 0
    for k in range(6):
        x = lerp(-0.45, 0.45, k / 5)
        with B.part(grain=(0, 1, 0), board=bi):
            B.rbox((x, (y0 + y1) / 2, 0.938), (0.178, y1 - y0, 0.022), W, bev=0)
        bi += 1
    zs = [(0.950, 1.064), (1.068, 1.182), (1.186, 1.300)]
    for s in (1, -1):
        for z0, z1 in zs:
            with B.part(grain=(0, 1, 0), board=bi):
                B.rbox((s * (x_in + x_out) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x_out - x_in, y1 - y0 + 0.044, z1 - z0),
                       W, bev=0.004)
            bi += 1
    for yy in (y0 - 0.011, y1 + 0.011):
        for z0, z1 in zs:
            with B.part(grain=(1, 0, 0), board=bi):
                B.rbox((0, yy, (z0 + z1) / 2), (2 * x_in, 0.022, z1 - z0), W, bev=0.004)
            bi += 1
    # tailgate cleats, iron hinge rod and chains to the sides
    for s in (1, -1):
        with B.part(grain=(0, 0, 1), board=bi):
            B.rbox((s * 0.36, y1 + 0.033, 1.125), (0.06, 0.022, 0.35), W, bev=0.004)
        bi += 1
    B.tube([(-0.56, y1 + 0.03, 0.952), (0.56, y1 + 0.03, 0.952)], 0.009, 6, "iron")
    for s in (1, -1):
        a = Vector((s * 0.50, y1 + 0.03, 1.285))
        b = Vector((s * (x_out + 0.008), y1 - 0.20, 1.285))
        for k in range(3):
            t0 = (k + 0.5) / 3
            p = a.lerp(b, t0) + Vector((0, 0, -0.035 * math.sin(math.pi * t0)))
            d = (b - a).normalized()
            axis = Vector((0, 0, 1)) if k % 2 == 0 else d.cross(Vector((0, 0, 1)))
            B.ring(p, 0.019, 0.0, 6, 3, "iron", axis, ellipse=(0.0035, 0.0035))
        B.lathe([(0.0, -0.01), (0.012, -0.01), (0.012, 0.012), (0.0, 0.015)], 8, "iron",
                T(*b) @ (ROT_Y90 if s > 0 else ROT_YM90))
    # iron: stake straps, corner irons, top bands, stake pockets
    for s in (1, -1):
        for y in (-0.80, -0.10, 0.60, 1.25):
            B.rbox((s * (x_out + 0.004), y, 1.115), (0.008, 0.04, 0.39), "iron", bev=0)
            B.rbox((s * (x_out + 0.012), y, 0.905), (0.026, 0.05, 0.06), "iron", bev=0)
        for y in (y0 - 0.02, y1 + 0.02):
            B.rbox((s * (x_out + 0.003), y, 1.12), (0.008, 0.06, 0.37), "iron", bev=0)
        B.rbox((s * (x_in + x_out) / 2, (y0 + y1) / 2, 1.303), (x_out - x_in + 0.012, y1 - y0 + 0.06, 0.008),
               "iron", bev=0)
    # footboard and dash in front of the box, braces
    with B.part(grain=(1, 0, 0), board=bi):
        M = T(0, -1.27, 1.005) @ RX(math.radians(-14))
        B.rbox((0, 0, 0), (1.06, 0.34, 0.024), W, M, bev=0.004)
    bi += 1
    for z0 in (1.03, 1.15):
        with B.part(grain=(1, 0, 0), board=bi):
            B.rbox((0, -1.445, z0 + 0.057), (1.06, 0.022, 0.114), W, bev=0.004)
        bi += 1
    for s in (1, -1):
        B.beam((s * 0.50, -1.10, 0.95), (s * 0.50, -1.43, 1.04), 0.03, 0.008, "iron", hint=(1, 0, 0), bev=0)
        B.beam((s * 0.50, -1.43, 1.0), (s * 0.50, -1.43, 1.27), 0.03, 0.008, "iron", hint=(1, 0, 0), bev=0)
    # driver's seat on bent iron risers, cushion, back rail on spindles
    sy = -0.80
    for s in (1, -1):
        for dy in (-0.14, 0.14):
            B.tube(smooth_path([(s * 0.535, sy + dy * 1.4, 1.30), (s * 0.52, sy + dy * 1.15, 1.36),
                                (s * 0.50, sy + dy, 1.405)], 5, 3), 0.009, 5, "iron")
    with B.part(grain=(1, 0, 0), board=bi):
        B.rbox((0, sy, 1.418), (1.12, 0.38, 0.03), W, bev=0.006, seg=1)
    bi += 1
    B.rbox((0, sy, 1.465), (1.06, 0.34, 0.07), "leather", bev=0.03, seg=1)
    with B.part(grain=(1, 0, 0), board=bi):
        B.rbox((0, sy + 0.20, 1.62), (1.12, 0.03, 0.10), W, bev=0.006, seg=1)
    bi += 1
    for x in (-0.50, -0.17, 0.17, 0.50):
        B.tube([(x, sy + 0.17, 1.43), (x, sy + 0.20, 1.57)], 0.008, 5, "iron")
    shafts(B, FA, RF, 0.42, 0.34, G, 2.55, heavy=1.12)
    return B


# ----------------------------------------------------------------------------------------------
# objects
# ----------------------------------------------------------------------------------------------
def ensure_materials():
    for n, hx in MATS.items():
        m = bpy.data.materials.get(n) or bpy.data.materials.new(n)
        c = [int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        m.diffuse_color = (*[((x + 0.055) / 1.055) ** 2.4 for x in c], 1.0)


def collection():
    sc = bpy.context.scene
    c = bpy.data.collections.get(COLL) or bpy.data.collections.new(COLL)
    if c.name not in sc.collection.children:
        sc.collection.children.link(c)
    return c


def finish(B, name):
    old = bpy.data.objects.get(name)
    if old:
        m = old.data
        bpy.data.objects.remove(old)
        if m and m.users == 0:
            bpy.data.meshes.remove(m)
    me = bpy.data.meshes.new(name)
    B.bm.normal_update()
    for e in B.bm.edges:                                   # sharp only at real creases
        if len(e.link_faces) == 2:
            f0, f1 = e.link_faces
            a = f0.normal.angle(f1.normal, 0.0)
            soft = f0[B.sl] and f1[B.sl]
            e.smooth = a < math.radians(80 if soft else SHARP_DEG)
        else:
            e.smooth = True
    B.bm.to_mesh(me)
    B.bm.free()
    used = sorted({p.material_index for p in me.polygons})
    remap = {old_i: new_i for new_i, old_i in enumerate(used)}
    for i in used:
        me.materials.append(bpy.data.materials[MNAMES[i]])
    for p in me.polygons:
        p.material_index = remap[p.material_index]
    for a in ("grain", "board", "soft"):
        if a in me.attributes:
            me.attributes.remove(me.attributes[a])
    ob = bpy.data.objects.new(name, me)
    collection().objects.link(ob)
    # weighted normals (keep sharp), applied so the custom normals go into the GLB
    mod = ob.modifiers.new("WN", "WEIGHTED_NORMAL")
    mod.keep_sharp = True
    mod.weight = 50
    mod.mode = "FACE_AREA"
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return ob


BUILDERS = [("model-t", build_model_t), ("buggy", build_buggy), ("delivery-wagon", build_delivery_wagon)]


def build_all():
    ensure_materials()
    c = collection()
    for o in list(c.objects):
        m = o.data
        bpy.data.objects.remove(o)
        if m and m.users == 0:
            bpy.data.meshes.remove(m)
    report = {}
    for name, fn in BUILDERS:
        ob = finish(fn(), name)
        report[name] = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        d = ob.dimensions
        print(name, "tris", report[name], "size x %.2f y %.2f z %.2f" % tuple(d))
    return report


if not globals().get("VEHICLES_LIB_ONLY"):
    build_all()
