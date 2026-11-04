"""
Street props kit (Main Street, Flemington, c. 1920) - geometry.

Run in Blender (Z up, metres):
    exec(open(r"<project>/tools/blender/street_props.py").read())

Builds 12 separate mesh objects in the collection "street_props", every one at the file origin
(not placed), so the scene can stamp each one many times. Conventions (PLAN.md, Street ambiance,
Pass 1, section A): front faces -Y (glTF +Z), origin at the centre of the footprint at ground level,
except pole_lamp (origin on the pole axis, arm height built in) and arc_lamp (origin at the top
hook, everything hangs below).

    pole, pole_lamp, arc_lamp, fountain, hitching_post, carriage_step, hydrant, shop_goods,
    sandwich_board_groceries, sandwich_board_icecream, bicycle, gas_pump

Every face carries one of the SRC_* source materials (filled in by street_props_bake.py) and a
second UV map "Aux" with local coordinates for slats, staves and lettering. The bake script packs
everything into one 2K atlas and one material.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise

ROOT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
BLEND = ROOT + r"\assets\models\source\street-props.blend"
COLL = "street_props"

# source materials (slot order is the same on every prop) and viewport colours (sRGB hex)
MATS = {
    "SRC_wood_pole": "5E5446", "SRC_wood_arm": "6E665A", "SRC_wood_crate": "8A7A62",
    "SRC_barrel": "6A4426", "SRC_board_green": "2E4A36", "SRC_board_letters": "2E4A36",
    "SRC_granite_rough": "A5A39D", "SRC_granite_dressed": "AEABA4", "SRC_water": "1C2224",
    "SRC_iron": "2A2622", "SRC_rust": "6A3A20", "SRC_hydrant": "5A2A22",
    "SRC_glass_green": "A8C8B0", "SRC_opal": "F0EEE6", "SRC_enamel_green": "1F4A30",
    "SRC_enamel_white": "E8E8E2", "SRC_bulb": "E6E2C8", "SRC_black_enamel": "1A1A1A",
    "SRC_nickel": "A8A8A2", "SRC_leather": "5A3A22", "SRC_rubber": "2A2828",
    "SRC_pump_red": "8A1E16", "SRC_gas_globe": "B02418", "SRC_brass": "A08040",
}
MNAMES = list(MATS)
MI = {n: i for i, n in enumerate(MNAMES)}

# lettering mask layout (u ranges in the Aux UV; the bake script renders the mask to match)
LETTER_REGIONS = {"groceries": (0.00, 0.30), "icecream": (0.35, 0.65), "gas": (0.70, 0.9825)}
GAS_BAND_V = (0.45, 0.55)

ROT_X90 = Matrix.Rotation(math.radians(90), 4, "X")
ROT_Y90 = Matrix.Rotation(math.radians(90), 4, "Y")


def T(x, y, z):
    return Matrix.Translation((x, y, z))


# ----------------------------------------------------------------------------------------------
# bmesh builder
# ----------------------------------------------------------------------------------------------
class Builder:
    def __init__(self, bm=None):
        self.bm = bm or bmesh.new()
        self.aux = self.bm.loops.layers.uv.get("Aux") or self.bm.loops.layers.uv.new("Aux")
        self.band = self.bm.faces.layers.int.get("band") or self.bm.faces.layers.int.new("band")

    def face(self, verts, mat):
        f = self.bm.faces.new(verts)
        f.material_index = MI[mat]
        f.smooth = True
        f.normal_update()
        return f

    def lathe(self, prof, n, mats, M=Matrix(), phase=0.0, rmod=None):
        """Revolve (r, z) profile points around local Z. r == 0 gives an apex. Traverse the
        profile so the outside is on the right of the direction of travel (normals outward)."""
        rings = []
        for k, (r, z) in enumerate(prof):
            if r < 1e-9:
                rings.append([self.bm.verts.new(M @ Vector((0, 0, z)))])
                continue
            ring = []
            for j in range(n):
                a = phase + 2 * math.pi * j / n
                rr = r * (rmod(k, j) if rmod else 1.0)
                ring.append(self.bm.verts.new(M @ Vector((rr * math.cos(a), rr * math.sin(a), z))))
            rings.append(ring)
        faces = []
        for k in range(len(prof) - 1):
            m = mats if isinstance(mats, str) else mats[k]
            A, B = rings[k], rings[k + 1]
            for j in range(n):
                j2 = (j + 1) % n
                if len(A) == 1 and len(B) == 1:
                    continue
                if len(A) == 1:
                    vs = (A[0], B[j2], B[j])
                elif len(B) == 1:
                    vs = (A[j], A[j2], B[0])
                else:
                    vs = (A[j], A[j2], B[j2], B[j])
                f = self.face(vs, m)
                f[self.band] = k
                faces.append(f)
        return faces

    def box(self, c, s, mat, M=Matrix(), skip=(), taper=None):
        """Axis box centre c, size s, in the frame M. skip: faces to leave out ('-Z', '+Y' ...).
        taper(v) may move the local corner positions before M is applied."""
        hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2
        loc = []
        for i in range(8):
            v = Vector((c[0] + (hx if i & 1 else -hx), c[1] + (hy if i & 2 else -hy), c[2] + (hz if i & 4 else -hz)))
            if taper:
                v = taper(v)
            loc.append(v)
        vs = [self.bm.verts.new(M @ v) for v in loc]
        F = {"-Z": (0, 2, 3, 1), "+Z": (4, 5, 7, 6), "-Y": (0, 1, 5, 4), "+Y": (2, 6, 7, 3),
             "-X": (0, 4, 6, 2), "+X": (1, 3, 7, 5)}
        out = {}
        for k, idx in F.items():
            if k in skip:
                continue
            out[k] = self.face([vs[i] for i in idx], mat)
        return out

    def beam(self, p0, p1, w, h, mat, hint=(0, 0, 1), skip_ends=False):
        """Box of section w x h running from p0 to p1. Local x = w side (perpendicular to hint)."""
        p0, p1 = Vector(p0), Vector(p1)
        t = (p1 - p0)
        L = t.length
        t.normalize()
        a = Vector(hint).cross(t)
        if a.length < 1e-6:
            a = Vector((1, 0, 0)).cross(t)
        a.normalize()
        b = t.cross(a)
        M = Matrix((a, b, t)).transposed().to_4x4()
        M.translation = p0
        return self.box((0, 0, L / 2), (w, h, L), mat, M, skip=("-Z", "+Z") if skip_ends else ())

    def tube(self, pts, r, n, mats, closed=False, nrm=None, phase=0.0, cap_end=False):
        """Sweep an n-sided ring of radius r (float or list) along a polyline."""
        P = [Vector(p) for p in pts]
        cnt = len(P)
        tans = []
        for i in range(cnt):
            if closed:
                d = P[(i + 1) % cnt] - P[i - 1]
            else:
                d = P[min(i + 1, cnt - 1)] - P[max(i - 1, 0)]
            tans.append(d.normalized())
        N = Vector(nrm) if nrm else None
        if N is None or abs(N.dot(tans[0])) > 0.99:
            N = Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0))
        N = (N - tans[0] * N.dot(tans[0])).normalized()
        rings = []
        for i in range(cnt):
            t = tans[i]
            if i > 0:
                N = (N - t * N.dot(t)).normalized()
            Bv = t.cross(N)
            rr = r[i] if isinstance(r, (list, tuple)) else r
            ring = []
            for j in range(n):
                a = phase + 2 * math.pi * j / n
                ring.append(self.bm.verts.new(P[i] + rr * (math.cos(a) * N + math.sin(a) * Bv)))
            rings.append(ring)
        faces = []
        segs = cnt if closed else cnt - 1
        for i in range(segs):
            A, B = rings[i], rings[(i + 1) % cnt]
            m = mats if isinstance(mats, str) else mats[i]
            for j in range(n):
                j2 = (j + 1) % n
                faces.append(self.face((A[j], A[j2], B[j2], B[j]), m))
        if cap_end and not closed:
            m = mats if isinstance(mats, str) else mats[-1]
            faces.append(self.face(rings[-1], m))
        return faces

    def ring(self, centre, R, r, nM, nm, mat, axis):
        """Torus around 'axis' (unit vector), as a closed sweep."""
        ax = Vector(axis).normalized()
        u = Vector((1, 0, 0)) if abs(ax.x) < 0.9 else Vector((0, 1, 0))
        u = (u - ax * u.dot(ax)).normalized()
        v = ax.cross(u)
        c = Vector(centre)
        pts = [c + R * (math.cos(2 * math.pi * i / nM) * u + math.sin(2 * math.pi * i / nM) * v) for i in range(nM)]
        return self.tube(pts, r, nm, mat, closed=True, nrm=ax)

    def prism(self, poly, depth, mat, M=Matrix(), back=False):
        """Polygon in the local XZ plane (u -> x, v -> z), from y = 0 out to y = -depth."""
        area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))
        if area < 0:
            poly = poly[::-1]
        F = [self.bm.verts.new(M @ Vector((u, -depth, v))) for u, v in poly]
        Bk = [self.bm.verts.new(M @ Vector((u, 0, v))) for u, v in poly]
        n = len(poly)
        front = self.face(F, mat)
        out = [front]
        if back:
            out.append(self.face(Bk[::-1], mat))
        for i in range(n):
            i2 = (i + 1) % n
            out.append(self.face((F[i], Bk[i], Bk[i2], F[i2]), mat))
        tri = bmesh.ops.triangulate(self.bm, faces=[front], quad_method="BEAUTY", ngon_method="BEAUTY")
        return out

    def set_aux(self, faces, fn):
        """fn(face, loop) -> (u, v)."""
        for f in faces:
            for lp in f.loops:
                lp[self.aux].uv = fn(f, lp)


def grid_box(B, nx, ny, nz, mapfn, mat, bottom=False):
    """Closed (bottomless) box surface on an nx x ny x nz grid; mapfn(u, v, w) -> Vector."""
    vmap = {}

    def V(i, j, k):
        key = (i, j, k)
        if key not in vmap:
            vmap[key] = B.bm.verts.new(mapfn(i / nx, j / ny, k / nz))
        return vmap[key]
    for i in range(nx):
        for k in range(nz):
            B.face((V(i, 0, k), V(i + 1, 0, k), V(i + 1, 0, k + 1), V(i, 0, k + 1)), mat)
            B.face((V(i, ny, k), V(i, ny, k + 1), V(i + 1, ny, k + 1), V(i + 1, ny, k)), mat)
    for j in range(ny):
        for k in range(nz):
            B.face((V(0, j, k), V(0, j, k + 1), V(0, j + 1, k + 1), V(0, j + 1, k)), mat)
            B.face((V(nx, j, k), V(nx, j + 1, k), V(nx, j + 1, k + 1), V(nx, j, k + 1)), mat)
    for i in range(nx):
        for j in range(ny):
            B.face((V(i, j, nz), V(i + 1, j, nz), V(i + 1, j + 1, nz), V(i, j + 1, nz)), mat)
    if bottom:   # one ngon, clockwise from above (normal down)
        ring = [V(i, 0, 0) for i in range(nx)] + [V(nx, j, 0) for j in range(ny)] +                [V(i, ny, 0) for i in range(nx, 0, -1)] + [V(0, j, 0) for j in range(ny, 0, -1)]
        B.face(ring[::-1], mat)
    return vmap


def round2(a, b, ha, hb_top, Ra, Rb, ha_lo=None):
    """Square-to-circle rounding of the corner regions of a 2D shape (a horizontal, b vertical
    or second horizontal). Corners at +-ha and at hb_top (and -hb_top if ha_lo given)."""
    qa = max(-(ha - Ra), min(a, ha - Ra))
    if ha_lo is None:
        qb = min(b, hb_top - Rb)
    else:
        qb = max(-(hb_top - Rb), min(b, hb_top - Rb))
    da, db = (a - qa) / Ra, (b - qb) / Rb
    L2 = math.hypot(da, db)
    if L2 > 1e-9 and abs(da) > 1e-9 and abs(db) > 1e-9:
        s = max(abs(da), abs(db)) / L2
        da, db = da * s, db * s
    return qa + da * Ra, qb + db * Rb


# ----------------------------------------------------------------------------------------------
# props
# ----------------------------------------------------------------------------------------------
def pole_r(z):
    return 0.15 - 0.05 * (z + 0.2) / 11.0


INSULATOR_Y = (-1.05, -0.75, -0.40, 0.40, 0.75, 1.05)
ARM_Z = (10.2, 9.5)


def arm_x(z):
    return pole_r(z) + 0.045


def build_pole():
    B = Builder()
    W = "SRC_wood_pole"
    top = 10.8
    prof = [(pole_r(-0.2), -0.2), (pole_r(top - 0.06), top - 0.06), (0.07, top), (0.0, top + 0.015)]
    B.lathe(prof, 10, W)
    for za in ARM_Z:
        ax = arm_x(za)
        B.box((ax, 0, za), (0.09, 2.4, 0.11), "SRC_wood_arm")
        # two diagonal iron braces from the pole to the arm underside
        for sy in (-1, 1):
            B.beam((pole_r(za - 0.6) - 0.01, 0, za - 0.6), (ax, sy * 0.62, za - 0.055), 0.04, 0.008,
                   "SRC_iron", hint=(1, 0, 0))
        # pin insulators (pale green glass), 8-sided bells sitting on the arm
        for y in INSULATOR_Y:
            M = T(ax, y, za + 0.055)
            B.lathe([(0.040, 0.0), (0.036, 0.05), (0.018, 0.09), (0.0, 0.10)], 8, "SRC_glass_green", M)
    # eye bolt on the street (-Y) face for the cross-street span wire
    ze = 8.6
    re = pole_r(ze)
    B.beam((0, -re + 0.02, ze), (0, -re - 0.045, ze), 0.014, 0.014, "SRC_rust", hint=(0, 0, 1))
    B.ring((0, -re - 0.068, ze), 0.024, 0.0065, 6, 3, "SRC_rust", (1, 0, 0))
    return B


def build_pole_lamp():
    B = Builder()
    zr = 4.6
    rp = pole_r(zr)
    B.box((0, -rp - 0.008, zr - 0.22), (0.08, 0.02, 0.62), "SRC_iron", skip=("+Y",))
    B.tube([(0, -rp - 0.01, zr), (0, -1.06, zr), (0, -1.10, zr - 0.04), (0, -1.10, zr - 0.10)], 0.017, 6,
           "SRC_iron")
    # scroll brace under the arm
    brace = [(0, -rp - 0.01, 4.10), (0, -0.25, 4.28), (0, -0.42, 4.44), (0, -0.62, 4.545),
             (0, -0.80, 4.585), (0, -0.87, 4.56), (0, -0.85, 4.515)]
    B.tube(brace, 0.011, 4, "SRC_iron", nrm=(1, 0, 0), phase=math.pi / 4)
    # radial-wave reflector: white inside, dark green enamel outside
    M = T(0, -1.10, 0)

    def wave(k, j):
        return 1.0 + (0.07 if j % 2 else -0.03) if k in (1, 2) else 1.0
    B.lathe([(0.028, 4.485), (0.20, 4.375), (0.21, 4.38), (0.036, 4.50)], 12,
            ["SRC_enamel_white", "SRC_enamel_white", "SRC_enamel_green"], M, rmod=wave)
    B.lathe([(0.03, 4.44), (0.03, 4.50)], 8, "SRC_brass", M)
    B.lathe([(0.0, 4.31), (0.028, 4.335), (0.038, 4.38), (0.02, 4.445)], 8, "SRC_bulb", M)
    return B


def build_arc_lamp():
    B = Builder()
    B.ring((0, 0, -0.03), 0.024, 0.006, 6, 3, "SRC_iron", (1, 0, 0))
    B.tube([(0, 0, -0.05), (0, 0, -0.15)], 0.012, 6, "SRC_iron")
    B.lathe([(0.08, -0.62), (0.08, -0.19), (0.05, -0.15), (0.0, -0.14)], 10, "SRC_iron")
    B.lathe([(0.07, -0.712), (0.24, -0.675), (0.24, -0.66), (0.08, -0.60)], 14,
            ["SRC_enamel_white", "SRC_iron", "SRC_iron"])
    zc, a, b = -0.89, 0.15, 0.19
    prof = [(0.0, zc - b)]
    for lat in (-60, -30, 0, 30, 58):
        t = math.radians(lat)
        prof.append((a * math.cos(t), zc + b * math.sin(t)))
    prof.append((0.09, -0.706))
    B.lathe(prof, 12, "SRC_opal")
    return B


MONO_W, MONO_D, MONO_H = 1.05, 0.65, 1.95
FACE_Y = -MONO_D / 2
MED_Z = 1.35
BOWL_Y = FACE_Y - 0.485


def mono_map(u, v, w):
    hx, hy = MONO_W / 2, MONO_D / 2
    x, y, z = (u - 0.5) * MONO_W, (v - 0.5) * MONO_D, w * MONO_H
    # rounded, slightly lopsided top (left shoulder rounder)
    Rx = 0.46 if x < 0 else 0.38
    x, z = round2(x, z, hx, MONO_H, Rx, 0.42)
    # softly rounded vertical edges
    x, y = round2(x, y, hx, hy, 0.07, 0.07, ha_lo=True)
    p = Vector((x, y, z))
    if w > 0:
        core = Vector((0, 0, min(max(z, 0.3), 1.55)))
        n = (p - core)
        n.z *= 0.6
        n.normalize()
        d = 0.018 * noise.noise(p * 5.0 + Vector((3.1, 7.7, 1.3))) + 0.008 * noise.noise(p * 13.0)
        d += 0.006
        # smooth, recessed oval for the medallion; flat seat for the lamp holder
        if y < -0.2:
            e = (x / 0.36) ** 2 + ((z - MED_Z) / 0.30) ** 2
            if e < 1.0:
                d = d * e - 0.034 * (1 - e) ** 0.5
        sd = math.hypot(x, y) / 0.18 + max(0.0, (1.80 - z) / 0.1)
        if sd < 1.0:
            d *= sd
        p += n * d
    return p


# horse head in side view, facing the viewer's left (u right, v up, 0..1): rounded muzzle at the
# lower left, chin and jaw, round cheek, throat, neck down to the bottom of the oval, mane crest,
# two upright ears, forehead and nose line back down to the muzzle
HORSE = [(0.03, 0.24), (0.02, 0.17), (0.05, 0.11), (0.10, 0.07), (0.16, 0.06), (0.24, 0.10), (0.33, 0.17),
         (0.41, 0.22), (0.49, 0.24), (0.56, 0.29), (0.60, 0.36), (0.61, 0.43), (0.63, 0.38), (0.65, 0.26),
         (0.67, 0.14), (0.69, 0.02), (0.92, 0.02), (0.95, 0.20), (0.93, 0.40), (0.86, 0.58), (0.77, 0.72),
         (0.68, 0.81), (0.65, 0.86), (0.67, 0.95), (0.64, 1.03), (0.59, 0.93), (0.56, 0.90), (0.55, 1.00),
         (0.50, 0.90), (0.45, 0.84), (0.38, 0.76), (0.30, 0.64), (0.21, 0.50), (0.13, 0.38), (0.07, 0.30)]
HORSE_RIDGES = [   # raised lines: mane locks, cheek / jaw line, nostril
    [(0.88, 0.30), (0.84, 0.46), (0.78, 0.58)],
    [(0.80, 0.52), (0.74, 0.63), (0.67, 0.72)],
    [(0.31, 0.27), (0.43, 0.33), (0.52, 0.42), (0.55, 0.53)],
    [(0.08, 0.21), (0.12, 0.25)],
]
HORSE_EYE = (0.41, 0.69)


def ribbon(pts, w):
    """Closed outline of a polyline thickened to width w (2D)."""
    P = [Vector((x, y)) for x, y in pts]
    left, right = [], []
    for i, p in enumerate(P):
        d = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        n = Vector((-d.y, d.x)) * (w / 2)
        left.append(p + n); right.append(p - n)
    return [(v.x, v.y) for v in left + right[::-1]]


def build_fountain():
    # 1. the monolith with its niche (boolean), as a temporary object
    Bm = Builder()
    grid_box(Bm, 7, 4, 10, mono_map, "SRC_granite_rough", bottom=True)
    mono = finish(Bm, "SP_tmp_monolith")
    Bc = Builder()
    nx0, nw, nz0, nh = -0.29, 0.30, 0.04, 0.28
    arch = [(nx0 - nw / 2, nz0), (nx0 + nw / 2, nz0), (nx0 + nw / 2, nz0 + nh - nw / 2)]
    for i in range(1, 6):
        a = math.pi * i / 6
        arch.append((nx0 + nw / 2 * math.cos(a), nz0 + nh - nw / 2 + nw / 2 * math.sin(a)))
    arch.append((nx0 - nw / 2, nz0 + nh - nw / 2))
    Bc.prism(arch, 0.30, "SRC_granite_dressed", T(0, FACE_Y + 0.17, 0), back=True)
    cutter = finish(Bc, "SP_tmp_cutter")
    mod = mono.modifiers.new("niche", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    try:
        mod.solver = "EXACT"
    except TypeError:
        pass
    try:
        mod.material_mode = "TRANSFER"
    except (TypeError, AttributeError):
        pass
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(mono.evaluated_get(dg))
    bm = bmesh.new()
    bm.from_mesh(me)
    for o in (mono, cutter):
        m = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(m)
    bpy.data.meshes.remove(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.9 and f.calc_center_median().z < 0.01],
                     context="FACES_ONLY")
    B = Builder(bm)
    # small basin lip in the niche (dog trough)
    B.box((nx0, FACE_Y - 0.01, nz0 + 0.03), (0.27, 0.12, 0.06), "SRC_granite_dressed", skip=("-Z",))
    # 2. smooth oval medallion with the horse head in low relief
    oval = [(0.275 * math.cos(2 * math.pi * i / 16), MED_Z + 0.225 * math.sin(2 * math.pi * i / 16))
            for i in range(16)]
    B.prism(oval, 0.040, "SRC_granite_dressed", T(0, FACE_Y + 0.038, 0))
    hs = 0.34

    def hp(u, v):
        return (-0.17 + u * hs, MED_Z - 0.18 + v * hs)
    B.prism([hp(u, v) for u, v in HORSE], 0.075, "SRC_granite_dressed", T(0, FACE_Y + 0.038, 0))
    for r in HORSE_RIDGES:      # ~7 mm proud of the head
        B.prism(ribbon([hp(u, v) for u, v in r], 0.008), 0.016, "SRC_granite_dressed", T(0, FACE_Y - 0.030, 0))
    ex, ez = hp(*HORSE_EYE)
    eye = [(ex + 0.014 * math.cos(2 * math.pi * i / 6), ez + 0.010 * math.sin(2 * math.pi * i / 6)) for i in range(6)]
    B.prism(eye, 0.016, "SRC_granite_dressed", T(0, FACE_Y - 0.030, 0))
    # 3. dark iron spout plate and spout above the bowl
    B.box((0, FACE_Y - 0.012, 0.90), (0.45, 0.05, 0.30), "SRC_iron", skip=("+Y",))
    B.tube([(0, FACE_Y - 0.015, 0.88), (0, FACE_Y - 0.09, 0.88), (0, FACE_Y - 0.12, 0.835)], 0.016, 6, "SRC_rust",
           cap_end=True)
    # 4. round dressed-granite bowl on a short pedestal, water 5 cm below the rim
    Mb = T(0, BOWL_Y, 0)
    B.lathe([(0.0, 0.08), (0.22, 0.10), (0.36, 0.17), (0.45, 0.28), (0.495, 0.42), (0.50, 0.53), (0.507, 0.585),
             (0.49, 0.625), (0.44, 0.63), (0.425, 0.585), (0.0, 0.575)], 16,
            ["SRC_granite_dressed"] * 9 + ["SRC_water"], Mb)
    B.lathe([(0.21, 0.0), (0.17, 0.11)], 8, "SRC_granite_dressed", Mb)
    # 5. cast-iron 4-arm scroll holder and white opal globe (top at 2.55 m)
    B.lathe([(0.10, 1.91), (0.10, 1.95), (0.055, 1.98), (0.035, 2.05), (0.05, 2.12), (0.065, 2.17), (0.0, 2.175)],
            8, "SRC_iron")
    for k in range(4):
        a = math.radians(90 * k)
        c, s = math.cos(a), math.sin(a)
        path = [(0.04, 2.03), (0.12, 2.07), (0.17, 2.14), (0.20, 2.24), (0.235, 2.31), (0.27, 2.325),
                (0.29, 2.30), (0.275, 2.272)]
        B.tube([(r * c, r * s, z) for r, z in path], 0.013, 4, "SRC_iron", nrm=(-s, c, 0), phase=math.pi / 4)
    zc, R = 2.55 - 0.19, 0.19
    prof = [(0.06, 2.55 - 2 * R + 0.012)]
    for lat in (-50, -20, 15, 50):
        t = math.radians(lat)
        prof.append((R * math.cos(t), zc + R * math.sin(t)))
    prof.append((0.0, 2.55))
    B.lathe(prof, 16, "SRC_opal")
    return B


def build_hitching_post():
    B = Builder()
    h = 0.11 * math.sqrt(2)
    B.lathe([(h, 0.0), (h, 0.86), (h - 0.035, 0.895), (0.0, 0.95)], 4, "SRC_granite_dressed",
            phase=math.pi / 4)
    B.box((0, -0.11 - 0.01, 0.80), (0.05, 0.03, 0.025), "SRC_rust", skip=("+Y",))
    B.ring((0, -0.11 - 0.022, 0.75), 0.048, 0.007, 8, 3, "SRC_rust", (0, 1, 0))
    return B


def build_carriage_step():
    """Granite block 0.90 (X, along the curb) x 0.45 x 0.35 with chamfered top edges: a 4-sided
    lathe squashed to the rectangle, corners nudged a little for a hand-dressed look."""
    B = Builder()
    h = 0.5 * math.sqrt(2)
    M = Matrix.Diagonal((0.90, 0.45, 1.0, 1.0))
    B.lathe([(h, 0.0), (h, 0.315), (h - 0.07 * math.sqrt(2) * 0.5 / 0.45 * 0.6, 0.35), (0.0, 0.35)], 4,
            "SRC_granite_dressed", M, phase=math.pi / 4)
    rnd = random.Random(7)
    for v in B.bm.verts:
        if v.co.z > 0.01:
            v.co += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.5, 0.5))) * 0.007
    return B


def build_hydrant():
    B = Builder()
    H = "SRC_hydrant"
    B.lathe([(0.15, 0.0), (0.15, 0.08), (0.12, 0.09), (0.12, 0.60), (0.14, 0.62), (0.14, 0.67), (0.11, 0.70),
             (0.08, 0.77), (0.0, 0.80)], 10, H)
    B.lathe([(0.035, 0.785), (0.035, 0.88), (0.0, 0.88)], 5, "SRC_rust", phase=math.pi / 2)
    # two hose nozzles at the sides, caps hanging on chains
    for sx in (-1, 1):
        M = T(0, 0, 0.45) @ Matrix.Rotation(sx * math.radians(90), 4, "Y")
        B.lathe([(0.04, 0.10), (0.047, 0.15), (0.047, 0.19), (0.0, 0.19)], 6, [H, "SRC_rust", "SRC_rust"], M,
                phase=math.pi / 6)
        B.beam((sx * 0.17, 0, 0.40), (sx * 0.13, 0.0, 0.28), 0.010, 0.005, "SRC_rust", hint=(0, 1, 0))
    # steamer nozzle to the front (-Y)
    M = T(0, 0, 0.40) @ Matrix.Rotation(math.radians(90), 4, "X")
    B.lathe([(0.06, 0.10), (0.068, 0.16), (0.068, 0.20), (0.0, 0.20)], 8, [H, "SRC_rust", "SRC_rust"], M,
            phase=math.pi / 8)
    return B


CRATE = (0.60, 0.40, 0.35)


def add_crate(B, M):
    sx, sy, sz = CRATE
    f = B.box((0, 0, sz / 2), (sx, sy, sz), "SRC_wood_crate", M, skip=("-Z",))
    for ex in (-1, 1):   # end cleats
        g = B.box((ex * (sx / 2 + 0.008), 0, sz / 2), (0.016, sy - 0.02, sz - 0.01), "SRC_wood_crate", M,
                  skip=("-X",) if ex > 0 else ("+X",))
        f.update({"c" + k: v for k, v in g.items()})
    Mi = M.inverted()

    def aux(face, lp):
        p = Mi @ lp.vert.co
        n = (Mi.to_3x3() @ face.normal)
        if abs(n.z) > 0.7:
            return (p.x, p.y + sy / 2)
        if abs(n.y) > 0.7:
            return (p.x, p.z)
        return (p.y + 3.0, p.z)
    B.set_aux(list(f.values()), aux)


def build_shop_goods():
    B = Builder()
    rz = Matrix.Rotation(math.radians(90), 4, "Z")
    add_crate(B, T(-0.475, 0.0, 0.0) @ rz)
    add_crate(B, T(-0.065, 0.02, 0.0) @ Matrix.Rotation(math.radians(92), 4, "Z"))
    add_crate(B, T(-0.27, 0.0, 0.35) @ Matrix.Rotation(math.radians(5), 4, "Z") @ Matrix.Rotation(math.radians(2.0), 4, "Y"))
    # barrel: 12 staves, three iron hoops, lid
    hoops = {(0.07, 0.12), (0.37, 0.43), (0.68, 0.73)}
    zs = [0.0, 0.07, 0.12, 0.37, 0.43, 0.68, 0.73, 0.80]

    def rb(z):
        return 0.235 + 0.04 * math.sin(math.pi * z / 0.80)
    prof, mats = [], []
    for i, z in enumerate(zs):
        prof.append((rb(z) + (0.006 if any(z in h for h in hoops) else 0.0), z))
        if i < len(zs) - 1:
            mats.append("SRC_rust" if (z, zs[i + 1]) in hoops else "SRC_barrel")
    prof += [(rb(0.80) - 0.02, 0.78), (0.0, 0.78)]
    mats += ["SRC_barrel", "SRC_barrel"]
    bx = 0.40
    faces = B.lathe(prof, 12, mats, T(bx, 0.0, 0.0))
    band = B.bm.faces.layers.int.get("band")

    def aux(face, lp):
        p = lp.vert.co - Vector((bx, 0, 0))
        if face[band] >= len(zs) - 1:
            return (p.x / 0.11 + 40.0, p.y + 0.3)
        c = face.calc_center_median() - Vector((bx, 0, 0))
        ac = math.atan2(c.y, c.x)
        a = math.atan2(p.y, p.x)
        while a - ac > math.pi:
            a -= 2 * math.pi
        while ac - a > math.pi:
            a += 2 * math.pi
        return (a / (2 * math.pi) * 12 + 12.0, p.z)
    B.set_aux(faces, aux)
    return B


def build_sandwich_board(which):
    B = Builder()
    u0, u1 = LETTER_REGIONS[which]
    panels = []
    for sy in (-1, 1):
        f = B.beam((0, sy * 0.225, 0.0), (0, sy * 0.012, 1.0), 0.60, 0.022, "SRC_board_green", hint=(0, 0, 1))
        # the outer face carries the lettering
        outer = max(f.values(), key=lambda fc: fc.normal.y * sy)
        outer.material_index = MI["SRC_board_letters"]

        def aux(face, lp, sy=sy):
            p = lp.vert.co
            t = (p.x + 0.30) / 0.60 if sy < 0 else (0.30 - p.x) / 0.60
            return (u0 + t * (u1 - u0), min(max(p.z, 0.0), 1.0))
        B.set_aux([outer], aux)
    # spreader bar between the legs
    B.beam((-0.27, -0.16, 0.30), (-0.27, 0.16, 0.30), 0.012, 0.012, "SRC_rust", hint=(0, 0, 1))
    return B


def build_bicycle():
    B = Builder()
    R = 0.355
    yr, yf = -0.53, 0.53
    for yc in (yr, yf):
        c = Vector((0, yc, R))
        pts = [c + Vector((0, (R - 0.018) * math.cos(2 * math.pi * i / 16), (R - 0.018) * math.sin(2 * math.pi * i / 16)))
               for i in range(16)]
        B.tube(pts, 0.019, 3, "SRC_rubber", closed=True, nrm=(1, 0, 0))
        for k in range(12):
            a = 2 * math.pi * (k + 0.5 * (k % 2)) / 12
            side = 0.025 if k % 2 else -0.025
            p0 = c + Vector((side, 0.03 * math.cos(a), 0.03 * math.sin(a)))
            p1 = c + Vector((0, 0.305 * math.cos(a), 0.305 * math.sin(a)))
            B.tube([p0, p1], 0.0028, 3, "SRC_nickel")
        B.tube([c + Vector((-0.05, 0, 0)), c + Vector((0.05, 0, 0))], 0.022, 6, "SRC_nickel")
    BB = Vector((0, -0.08, 0.28))
    ST = Vector((0, -0.20, 0.80))
    HT = Vector((0, 0.40, 0.84))
    HB = Vector((0, 0.44, 0.68))
    Rr, Fr = Vector((0, yr, R)), Vector((0, yf, R))
    K = "SRC_black_enamel"
    tubes = [(BB, ST), (BB, HB), (Vector((0, -0.185, 0.76)), Vector((0, 0.405, 0.81))), (HB, HT)]
    for sx in (-0.04, 0.04):
        tubes += [(Rr + Vector((sx, 0, 0)), BB + Vector((sx * 0.5, 0, 0))),
                  (Rr + Vector((sx, 0, 0)), Vector((sx * 0.4, -0.19, 0.76)))]
    for sx in (-0.045, 0.045):
        tubes.append((HB + Vector((sx * 0.5, 0, 0)), Fr + Vector((sx, 0, 0))))
    for a, b in tubes:
        B.tube([a, b], 0.015, 4, K)
    B.tube([HT, Vector((0, 0.38, 0.98))], 0.012, 4, "SRC_nickel")
    B.tube([ST, Vector((0, -0.215, 0.89))], 0.012, 4, "SRC_nickel")
    bars = [(-0.28, 0.20, 1.00), (-0.20, 0.35, 0.99), (0, 0.395, 0.98), (0.20, 0.35, 0.99), (0.28, 0.20, 1.00)]
    B.tube(bars, 0.011, 4, ["SRC_leather", "SRC_nickel", "SRC_nickel", "SRC_leather"])

    def saddle(v):
        if v.y > 0:
            v.x *= 0.32
            v.z -= 0.012
        return v
    B.box((0, -0.225, 0.925), (0.17, 0.26, 0.055), "SRC_leather", taper=saddle)
    # chainring, cranks, pedals, chain
    M = T(0.05, BB.y, BB.z) @ ROT_Y90
    B.lathe([(0.0, -0.004), (0.10, -0.004), (0.10, 0.004), (0.0, 0.004)], 10, "SRC_nickel", M)
    for s in (-1, 1):
        x = 0.07 * s
        end = BB + Vector((x, 0.15 * s, -0.04 * s))
        B.beam(BB + Vector((x, 0, 0)), end, 0.025, 0.012, "SRC_nickel", hint=(1, 0, 0))
        B.box((end.x + 0.04 * s, end.y, end.z), (0.09, 0.05, 0.022), "SRC_rubber")
    for dz in (0.10, -0.10):
        B.beam((0.05, BB.y, BB.z + dz), (0.05, yr, R + dz * 0.4), 0.01, 0.012, "SRC_iron", hint=(1, 0, 0))
    # lean 12 degrees to its left (-X) about the long axis on the ground
    rot = Matrix.Rotation(math.radians(-12), 4, "Y")
    bmesh.ops.transform(B.bm, matrix=rot, verts=B.bm.verts)
    return B


def build_gas_pump():
    B = Builder()
    P = "SRC_pump_red"
    B.box((0, 0, 0.05), (0.55, 0.55, 0.10), "SRC_iron", skip=("-Z",))
    B.box((0, 0, 0.875), (0.45, 0.45, 1.55), P, skip=("-Z", "+Z"))
    B.box((0, -0.225 - 0.006, 0.85), (0.34, 0.012, 1.0), P, skip=("+Y",))
    B.box((0, 0, 1.67), (0.50, 0.50, 0.04), P, skip=())
    B.lathe([(0.22, 1.69), (0.19, 1.76), (0.11, 1.81), (0.05, 1.83), (0.065, 1.855)], 12, P)
    zc, R = 2.20 - 0.18, 0.18
    zs = [1.85, 1.90, 1.965, 2.075, 2.14, 2.19]
    prof = [(math.sqrt(max(R * R - (z - zc) ** 2, 0.0)), z) for z in zs] + [(0.0, 2.20)]
    mats = ["SRC_opal", "SRC_opal", "SRC_gas_globe", "SRC_opal", "SRC_opal", "SRC_opal"]
    faces = B.lathe(prof, 16, mats)
    band_faces = [f for f in faces if f.material_index == MI["SRC_gas_globe"]]
    u0, u1 = LETTER_REGIONS["gas"]
    v0, v1 = GAS_BAND_V

    def aux(face, lp):
        c = face.calc_center_median()
        p = lp.vert.co
        a = math.atan2(p.y, p.x) % (2 * math.pi)
        front = (math.atan2(c.y, c.x) % (2 * math.pi)) > math.pi
        if front:
            if a < math.pi / 2:
                a += 2 * math.pi
            t = (a - math.pi) / math.pi
        else:
            if a > 1.5 * math.pi:
                a -= 2 * math.pi
            t = a / math.pi
        return (u0 + t * (u1 - u0), v0 + (p.z - 1.965) / 0.11 * (v1 - v0))
    B.set_aux(band_faces, aux)
    # crank handle on the right (+X) side
    M = T(0.225, 0, 1.20) @ ROT_Y90
    B.lathe([(0.05, 0.0), (0.05, 0.03), (0.0, 0.03)], 8, "SRC_iron", M)
    B.beam((0.262, 0, 1.20), (0.262, 0, 1.42), 0.03, 0.014, "SRC_iron", hint=(1, 0, 0))
    B.tube([(0.262, 0, 1.40), (0.34, 0, 1.40)], 0.013, 6, "SRC_rubber", cap_end=True)
    # hose coiled on a hook on the left (-X) side, brass nozzle
    B.beam((-0.225, 0, 1.40), (-0.31, 0, 1.43), 0.02, 0.02, "SRC_iron", hint=(0, 1, 0))
    B.tube([(-0.225, 0.10, 1.56), (-0.265, 0.08, 1.50), (-0.285, 0.03, 1.415)], 0.017, 8, "SRC_rubber")
    c = Vector((-0.285, 0.0, 1.22))
    loop = [c + Vector((0, 0.19 * math.sin(2 * math.pi * i / 12), 0.19 * math.cos(2 * math.pi * i / 12)))
            for i in range(12)]
    B.tube(loop, 0.017, 8, "SRC_rubber", closed=True, nrm=(1, 0, 0))
    B.tube([(-0.29, -0.03, 1.035), (-0.30, -0.06, 0.88)], 0.013, 6, "SRC_brass", cap_end=True)
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
    c = bpy.data.collections.get(COLL)
    if c is None:
        c = bpy.data.collections.new(COLL)
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
    B.bm.to_mesh(me)
    B.bm.free()
    for n in MNAMES:
        me.materials.append(bpy.data.materials[n])
    if "band" in me.attributes:
        me.attributes.remove(me.attributes["band"])
    try:
        me.set_sharp_from_angle(angle=math.radians(46))
    except AttributeError:
        pass
    ob = bpy.data.objects.new(name, me)
    collection().objects.link(ob)
    return ob


BUILDERS = [
    ("pole", build_pole), ("pole_lamp", build_pole_lamp), ("arc_lamp", build_arc_lamp),
    ("fountain", build_fountain), ("hitching_post", build_hitching_post),
    ("carriage_step", build_carriage_step), ("hydrant", build_hydrant), ("shop_goods", build_shop_goods),
    ("sandwich_board_groceries", lambda: build_sandwich_board("groceries")),
    ("sandwich_board_icecream", lambda: build_sandwich_board("icecream")),
    ("bicycle", build_bicycle), ("gas_pump", build_gas_pump),
]


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
    print("TRIS", report, "total", sum(report.values()))
    return report


if not globals().get("STREET_PROPS_LIB_ONLY"):
    build_all()
