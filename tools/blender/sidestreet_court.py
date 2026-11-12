"""
sidestreet_court.py - the Court St backdrop west of Main St (PLAN.md "Side streets, backdrop
buildings", sections 1a, 3, 4 and 7): every building a visitor sees looking west down Court St
from Main St, at its Sept 1921 Sanborn footprint, as one cheap model, plus the side-street
ground beyond x -60 (where js/ground.js stops), the park edge and the house fences.

  K1  Fire Dept House, 7 Court (2-storey brick, 6.7 m, front gable, two engine doors,
      frame lean-to W and N)                                  PLAIN-GUESS (no hose tower)
  K2  Stone cutting, 6 Court: brick part 1 1/2 storeys, low slate gable + frame part
      2 storeys                                               PLAIN-GUESS (NRHP-1980 form)
  K3  Am. Legion Room, 8 Court: brick ground storey with pilasters and a pale entablature,
      stucco upper storey, flat roof behind a parapet (7.3 m); 1-storey frame rear
                                                              PLAIN-GUESS (NRHP-1980 form)
  K4  Double dwelling 10-12 Court, 2-storey frame, on the street line     PLAIN-GUESS
  K5  Flemington Steam Laundry, 14 Court: gable along the length, boiler lean-to, 9 m iron
      stack                                                   PLAIN-GUESS (NRHP-1980 form)
  K6-K10  houses 16-26 Court behind porches and low picket fences          PLAIN-GUESS
          (NRHP-1980 forms; fences, stone curb and earth road: PHOTO, c. 1910 parade card)
  K11 livery wagon shed behind the laundry (tier 2)                        PLAIN-GUESS
  Park edge: 0.4 m bank + white X-braced rail along z 0, lawn, two gravel paths, one lamp
      pole                                                    PHOTO (park cards, parade card)
  Not built: band stand (owner: hidden from Main St), Lyceum (decision 7.3-2), signs.

Run inside Blender:
    exec(open(r"<project>/tools/blender/sidestreet_court.py").read())
Every run deletes and rebuilds the "SidestreetCourt" collection. Materials, lightmap bake and
GLB export: sidestreet_court_bake.py (runs this file first).

Coordinates: SCENE AXES (the GLB is placed at "0 0 0", rotation "0 0 0"):
    Blender X = scene x (east), Blender Y = -scene z (north = +Y), Blender Z = scene y (up).
Ground level: lots, walks and the bottom of every wall at y 0.15 (the sidewalk top); the walls
skirt down to 0.0. Road 0.01 (as js/ground.js's Court St arm). Park lawn 0.55 (0.4 m bank).
Windows and doors are flat quads 3 cm proud of the wall, mapped to cells of
assets/textures/shared/backdrop_windows.jpg (tools/prepare_backdrop_windows.py).
"""

import json
import math
import random
import bpy
import bmesh
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
COLL = "SidestreetCourt"
G = 0.15                       # lot / sidewalk top
ROAD_Y = 0.01
PARK = 0.55                    # park lawn (0.4 m bank above the walk)
X_END = -172.0                 # Park Ave (west end of the walks and road)
X_JOIN = -60.0                 # js/ground.js draws Court St east of this
ATLAS = json.load(open(PROJECT + r"\assets\textures\shared\backdrop_windows.json"))["cells"]
TILE = {"clap": 1.0, "brick": 1.4, "slate": 1.5, "concrete": 3.0, "grass": 4.0}
rng = random.Random(1921)

# ---------------------------------------------------------------------------
# mesh buckets: (part, material) -> verts, faces (+ explicit uvs or None)
# materials: clap, brick, slate, concrete, grass, road, atlas, and "sw:<cell>" = a plain
# colour taken from one atlas swatch cell
# ---------------------------------------------------------------------------
BUCKETS = {}


def P(x, z, y):
    """scene (x, z, y) -> Blender vector"""
    return Vector((x, -z, y))


def newell(pts):
    n = Vector((0, 0, 0))
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        n.x += (a.y - b.y) * (a.z + b.z)
        n.y += (a.z - b.z) * (a.x + b.x)
        n.z += (a.x - b.x) * (a.y + b.y)
    return n.normalized() if n.length > 1e-9 else n


def add(part, mat, pts, uvs=None):
    pts = [Vector(p) for p in pts]
    b = BUCKETS.setdefault((part, mat), ([], []))
    base = len(b[0])
    b[0].extend(pts)
    b[1].append((tuple(range(base, base + len(pts))), uvs))


def face_out(part, mat, pts, outward, uvs=None):
    """add a face, turned so its normal points along `outward`"""
    pts = [Vector(p) for p in pts]
    if newell(pts).dot(Vector(outward)) < 0:
        pts = pts[::-1]
        uvs = uvs[::-1] if uvs else None
    add(part, mat, pts, uvs)


def solid(part, faces, mats):
    """convex solid: every face turned outward from the centroid. mats: one or per face"""
    allp = [Vector(p) for f in faces for p in f]
    c = sum(allp, Vector()) / len(allp)
    for i, f in enumerate(faces):
        f = [Vector(p) for p in f]
        fc = sum(f, Vector()) / len(f)
        face_out(part, mats if isinstance(mats, str) else mats[i], f, fc - c)


def box(part, mat, x0, x1, y0, y1, z0, z1, sides=("t", "n", "s", "e", "w"), top=None):
    """Blender-coordinate box; sides: t top, b bottom, s (-Y), n (+Y), w (-X), e (+X)"""
    q = {
        "t": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        "b": [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)],
        "s": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
        "n": [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)],
        "w": [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)],
        "e": [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
    }
    for k in sides:
        add(part, (top or mat) if k == "t" else mat, q[k])


def sbox(part, mat, x0, x1, z0, z1, y0, y1, **kw):
    """box from scene coordinates (x, z ranges; y = height)"""
    box(part, mat, x0, x1, -z1, -z0, y0, y1, **kw)


# ---------------------------------------------------------------------------
# building pieces (Blender coordinates: footprint x0..x1, y0..y1)
# ---------------------------------------------------------------------------
def gable_walls(part, mat, x0, x1, y0, y1, eave, rise, ridge, z0=0.0):
    if ridge == "y":              # gables at y0 and y1
        xm = (x0 + x1) / 2
        faces = [[(x0, y0, z0), (x1, y0, z0), (x1, y0, eave), (xm, y0, eave + rise), (x0, y0, eave)],
                 [(x0, y1, z0), (x1, y1, z0), (x1, y1, eave), (xm, y1, eave + rise), (x0, y1, eave)],
                 [(x0, y0, z0), (x0, y1, z0), (x0, y1, eave), (x0, y0, eave)],
                 [(x1, y0, z0), (x1, y1, z0), (x1, y1, eave), (x1, y0, eave)]]
    else:                         # gables at x0 and x1
        ym = (y0 + y1) / 2
        faces = [[(x0, y0, z0), (x0, y1, z0), (x0, y1, eave), (x0, ym, eave + rise), (x0, y0, eave)],
                 [(x1, y0, z0), (x1, y1, z0), (x1, y1, eave), (x1, ym, eave + rise), (x1, y0, eave)],
                 [(x0, y0, z0), (x1, y0, z0), (x1, y0, eave), (x0, y0, eave)],
                 [(x0, y1, z0), (x1, y1, z0), (x1, y1, eave), (x0, y1, eave)]]
    solid(part, faces, mat)


def slab(part, top_mat, under_mat, corners_bottom, t):
    """roof slab: 4 bottom corners (quad, any order around), top = bottom + t (vertical)"""
    b = [Vector(p) for p in corners_bottom]
    tp = [p + Vector((0, 0, t)) for p in b]
    faces = [tp, b] + [[b[i], b[(i + 1) % 4], tp[(i + 1) % 4], tp[i]] for i in range(4)]
    mats = [top_mat, under_mat] + [under_mat] * 4
    solid(part, faces, mats)


def gable_roof(part, x0, x1, y0, y1, eave, rise, ridge, oe=0.35, og=0.25, t=0.14,
               top="slate", under="sw:paint_white", skip_ridge_end=None):
    """two slabs meeting at the ridge; eave overhang oe, gable overhang og"""
    if ridge == "y":
        xm, h = (x0 + x1) / 2, (x1 - x0) / 2
        s = rise / h
        ya, yb = y0 - og, y1 + og
        for xe, sign in ((x0, -1), (x1, 1)):
            xl = xe + sign * oe
            zl = eave - oe * s
            slab(part, top, under, [(xl, ya, zl), (xm, ya, eave + rise), (xm, yb, eave + rise), (xl, yb, zl)], t)
    else:
        ym, h = (y0 + y1) / 2, (y1 - y0) / 2
        s = rise / h
        xa, xb = x0 - og, x1 + og
        for ye, sign in ((y0, -1), (y1, 1)):
            yl = ye + sign * oe
            zl = eave - oe * s
            slab(part, top, under, [(xa, yl, zl), (xa, ym, eave + rise), (xb, ym, eave + rise), (xb, yl, zl)], t)


def shed(part, wall_mat, roof_mat, x0, x1, y0, y1, z_hi, z_lo, low_side, oe=0.25, t=0.12,
         under="sw:paint_white", z0=0.0):
    """lean-to: walls up to a single slope, falling toward low_side ('w','e','s','n')"""
    def zt(x, y):
        f = {"w": (x1 - x) / (x1 - x0), "e": (x - x0) / (x1 - x0),
             "s": (y1 - y) / (y1 - y0), "n": (y - y0) / (y1 - y0)}[low_side]
        return z_hi + (z_lo - z_hi) * f
    c = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    faces = [[(x, y, z0) for x, y in c][::-1], [(x, y, zt(x, y)) for x, y in c]]
    for i in range(4):
        (ax, ay), (bx, by) = c[i], c[(i + 1) % 4]
        faces.append([(ax, ay, z0), (bx, by, z0), (bx, by, zt(bx, by)), (ax, ay, zt(ax, ay))])
    solid(part, faces[2:], wall_mat)
    # roof slab, overhanging on the three free sides
    ex = {"w": (oe, 0, oe, oe), "e": (0, oe, oe, oe), "s": (oe, oe, oe, 0), "n": (oe, oe, 0, oe)}[low_side]
    rx0, rx1, ry0, ry1 = x0 - ex[0], x1 + ex[1], y0 - ex[2], y1 + ex[3]
    slope = (z_hi - z_lo) / ((x1 - x0) if low_side in "we" else (y1 - y0))

    def zr(x, y):
        if low_side == "w":
            return z_hi - (x1 - x) * slope
        if low_side == "e":
            return z_hi - (x - x0) * slope
        if low_side == "s":
            return z_hi - (y1 - y) * slope
        return z_hi - (y - y0) * slope
    slab(part, roof_mat, under, [(x, y, zr(x, y)) for x, y in
                                 [(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1)]], t)


def chimney(part, x, y, z_base, z_top, w=0.55, d=0.55):
    box(part, "brick", x - w / 2, x + w / 2, y - d / 2, y + d / 2, z_base, z_top)
    box(part, "brick", x - w / 2 - 0.07, x + w / 2 + 0.07, y - d / 2 - 0.07, y + d / 2 + 0.07,
        z_top - 0.18, z_top + 0.02, sides=("t", "n", "s", "e", "w", "b"))


def cross_gable(part, wall_mat, side, xc, w, y_wall, eave, rc, main_slope, oe=0.25, t=0.14, rise_dir=1):
    """a small gable rising from the wall at Blender y = y_wall (side 'n' or 's' = +Y / -Y
    facing) or x = y_wall (side 'e' / 'w'), centred on xc along the wall, back into the main
    roof until its ridge meets the main slope."""
    out = {"n": Vector((0, 1, 0)), "s": Vector((0, -1, 0)), "e": Vector((1, 0, 0)), "w": Vector((-1, 0, 0))}[side]
    along = Vector((1, 0, 0)) if side in "ns" else Vector((0, 1, 0))
    base = (Vector((xc, y_wall, 0)) if side in "ns" else Vector((y_wall, xc, 0)))
    depth = (rc + 0.3) / main_slope + 0.3           # how far back the ridge runs into the roof

    def at(u, back, z):
        return base + along * u - out * back + Vector((0, 0, z))
    # gable triangle on the wall (wall material)
    face_out(part, wall_mat, [at(-w / 2, 0, eave), at(w / 2, 0, eave), at(0, 0, eave + rc)], out)
    s = rc / (w / 2)
    for sign in (-1, 1):
        ue = sign * (w / 2 + oe)
        ze = eave - oe * s
        slab(part, "slate", "sw:paint_white",
             [at(ue, -0.25, ze), at(0, -0.25, eave + rc), at(0, depth, eave + rc), at(ue, depth, ze)], t)


def window(part, cell, n, bottom_centre, w, h, off=0.03):
    """flat window / door quad on a wall: n = outward axis ('+x','-x','+y','-y' in Blender),
    bottom_centre = point on the wall plane"""
    nv = {"+x": Vector((1, 0, 0)), "-x": Vector((-1, 0, 0)), "+y": Vector((0, 1, 0)), "-y": Vector((0, -1, 0))}[n]
    up = Vector((0, 0, 1))
    r = up.cross(nv)
    c = Vector(bottom_centre) + nv * off
    pts = [c - r * w / 2, c + r * w / 2, c + r * w / 2 + up * h, c - r * w / 2 + up * h]
    u0, v0, u1, v1 = ATLAS[cell]
    add(part, "atlas", pts, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])


def win_row(part, cells, n, wall, along, z_bottom, w, h):
    """a row of windows: wall = the wall plane coordinate, along = centre positions"""
    for i, a in enumerate(along):
        cell = cells[i % len(cells)] if isinstance(cells, list) else cells
        if n in ("+y", "-y"):
            window(part, cell, n, (a, wall, z_bottom), w, h)
        else:
            window(part, cell, n, (wall, a, z_bottom), w, h)


def cream():
    return "win_cream_%d" % rng.randrange(8)


def green():
    return "win_green_%d" % rng.randrange(8)


def porch(part, x0, x1, y0, y1, front, deck, roof_z, posts, steps_x=(), roof_fall=0.25):
    """open porch: deck, posts on the outer edge, shallow shed roof (tin), steps"""
    box(part, "sw:wood_grey", x0, x1, y0, y1, 0.0, deck)
    out = {"n": 1, "s": -1}[front]
    ye = y1 if out > 0 else y0                     # outer edge
    yw = y0 if out > 0 else y1                     # house wall
    for px in posts:
        py = ye - out * 0.15
        box(part, "sw:paint_white", px - 0.08, px + 0.08, py - 0.08, py + 0.08, deck, roof_z,
            sides=("n", "s", "e", "w"))
    # roof slab: high at the wall, falling toward the outer edge, 0.2 m overhang
    yo = ye + out * 0.2
    zl = roof_z - roof_fall * 0.15
    slab(part, "sw:tin_dark", "sw:paint_white",
         [(x0 - 0.15, yw, roof_z + roof_fall), (x1 + 0.15, yw, roof_z + roof_fall),
          (x1 + 0.15, yo, zl), (x0 - 0.15, yo, zl)], 0.12)
    for sx in steps_x:
        for k, (dy, h) in enumerate(((0.35, deck * 0.66), (0.7, deck * 0.33))):
            yy0, yy1 = (ye, ye + out * dy) if out > 0 else (ye + out * dy, ye)
            box(part, "sw:wood_grey", sx - 0.7, sx + 0.7, min(yy0, yy1), max(yy0, yy1), 0.0, h,
                sides=("t", "n", "s", "e", "w"))


def foundation(part, x0, x1, y0, y1, top, sides):
    """stone base band 3 cm proud of a frame wall, on the given sides"""
    box(part, "concrete", x0 - 0.03, x1 + 0.03, y0 - 0.03, y1 + 0.03, 0.0, top, sides=sides)


# ===========================================================================
# K1  Fire Dept House (north side, front faces Court St = Blender -Y at y = 0)
# brick core x -61.3 .. -54.5, scene z -12.8 .. 0  ->  Blender y 0 .. 12.8
# ===========================================================================
def build_k1():
    p = "K1"
    x0, x1, y0, y1 = -61.3, -54.5, 0.0, 12.8
    eave = G + 6.7
    rise = (x1 - x0) / 2 * math.tan(math.radians(30))
    gable_walls(p, "brick", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "y", oe=0.3, og=0.3)
    chimney(p, -57.0, 11.2, eave + 0.6, eave + rise + 0.9)
    # front: two engine doors under a stone lintel band, three meeting-room windows, gable light
    for cx in (-59.45, -56.35):
        window(p, "engine_doors", "-y", (cx, y0, G), 2.8, 3.2)
    box(p, "sw:stone_cream", x0 + 0.05, x1 - 0.05, y0 - 0.06, y0, G + 3.25, G + 3.5, sides=("t", "s", "e", "w", "b"))
    box(p, "sw:stone_cream", x0 - 0.02, x1 + 0.02, y0 - 0.04, y0 + 0.2, eave - 0.3, eave, sides=("s", "e", "w"))
    win_row(p, [green(), green(), green()], "-y", y0, (-59.9, -57.9, -55.9), G + 4.0, 0.9, 1.75)
    window(p, "attic_window", "-y", (-57.9, y0, eave + 0.45), 0.8, 0.8)
    # east wall (toward the courthouse / Main St): two rows of three
    win_row(p, [green() for _ in range(3)], "+x", x1, (2.6, 6.4, 10.2), G + 1.0, 0.9, 1.75)
    win_row(p, [green() for _ in range(3)], "+x", x1, (2.6, 6.4, 10.2), G + 4.0, 0.9, 1.75)
    # west wall above the lean-to, and the rear
    win_row(p, [green(), green()], "-x", x0, (4.0, 9.0), G + 4.0, 0.9, 1.75)
    win_row(p, [green(), green()], "+y", y1, (-59.6, -56.2), G + 4.0, 0.9, 1.75)

    # frame lean-to along the west side (shed falling west) and across the rear (falling north)
    lp = "K1L"
    shed(lp, "clap", "slate", -64.1, x0, 0.0, 14.1, G + 3.9, G + 3.0, "w")
    shed(lp, "clap", "slate", x0, x1, y1, 14.1, G + 3.9, G + 3.35, "n")
    shed(lp, "clap", "slate", -58.4, -56.5, 14.1, 15.4, G + 3.0, G + 2.6, "n")
    foundation(lp, -64.1, x0, 0.0, 14.1, G + 0.25, ("s", "w", "n"))
    window(lp, "door_green", "-y", (-63.3, 0.0, G), 0.9, 2.1)
    window(lp, cream(), "-y", (-62.1, 0.0, G + 0.95), 0.8, 1.5)
    win_row(lp, [cream(), cream(), cream()], "-x", -64.1, (3.5, 7.5, 11.5), G + 0.95, 0.8, 1.5)


# ===========================================================================
# K2  Stone cutting (south side; fronts face Court St = Blender +Y)
# ===========================================================================
def build_k2():
    p = "K2"
    # brick part (old carriage house): 1 1/2 storeys, low slate front gable
    x0, x1, y0, y1 = -60.7, -56.5, -15.1, -10.5
    eave = G + 4.5
    rise = (x1 - x0) / 2 * math.tan(math.radians(22))
    gable_walls(p, "brick", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "y", oe=0.25, og=0.25)
    window(p, "barn_doors", "+y", (-58.15, y1, G), 2.3, 2.5)
    window(p, "small_window", "+y", (-60.1, y1, G + 1.2), 0.75, 0.75)
    window(p, green(), "+y", (-58.6, y1, G + 3.0), 0.8, 1.3)
    window(p, "attic_window", "+y", (-58.6, y1, eave + 0.2), 0.55, 0.55)
    box(p, "sw:stone_cream", -59.4, -56.9, y1, y1 + 0.06, G + 2.5, G + 2.72, sides=("t", "n", "e", "w", "b"))
    win_row(p, [green(), green()], "-x", x0, (-13.9, -11.7), G + 1.0, 0.8, 1.4)
    # frame part: 2 storeys, side gable
    f = "K2F"
    x0, x1, y0, y1 = -56.5, -50.6, -16.7, -10.5
    eave = G + 6.0
    rise = (y1 - y0) / 2 * math.tan(math.radians(33))
    gable_walls(f, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(f, x0, x1, y0, y1, eave, rise, "x")
    foundation(f, x0, x1, y0, y1, G + 0.3, ("n", "e", "s"))
    chimney(f, -51.6, (y0 + y1) / 2 - 0.4, eave + 0.8, eave + rise + 0.8)
    window(f, "door_brown", "+y", (-55.6, y1, G + 0.05), 1.0, 2.2)
    win_row(f, [cream(), cream()], "+y", y1, (-53.7, -51.8), G + 0.95, 0.9, 1.7)
    win_row(f, [cream(), cream(), cream()], "+y", y1, (-55.5, -53.6, -51.7), G + 3.7, 0.9, 1.6)
    win_row(f, [cream(), cream()], "+x", x1, (-14.9, -12.3), G + 0.95, 0.9, 1.7)
    win_row(f, [cream(), cream()], "+x", x1, (-14.9, -12.3), G + 3.7, 0.9, 1.6)
    window(f, "attic_window", "+x", (x1, (y0 + y1) / 2, eave + 0.35), 0.6, 0.6)


# ===========================================================================
# K3  American Legion Room (front 2.2 m behind the street line)
# ===========================================================================
def build_k3():
    p = "K3"
    x0, x1, y0, y1 = -75.1, -67.0, -19.5, -12.6
    top = G + 7.3
    box(p, "brick", x0, x1, y0, y1, 0.0, G + 3.9, sides=("n", "e", "w", "s"))
    box(p, "sw:paint_cream", x0, x1, y0, y1, G + 3.9, top - 0.2, sides=("n", "e", "w", "s", "t"))
    # coping and the pale entablature over the ground storey (front and short returns)
    box(p, "sw:stone_cream", x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.12, top - 0.2, top,
        sides=("t", "n", "e", "w", "s", "b"))
    box(p, "sw:paint_white", x0 - 0.2, x1 + 0.2, y1 - 0.5, y1 + 0.24, G + 3.45, G + 4.15,
        sides=("t", "n", "e", "w", "b"))
    box(p, "sw:paint_white", x0 - 0.26, x1 + 0.26, y1 - 0.5, y1 + 0.32, G + 3.95, G + 4.15,
        sides=("t", "n", "e", "w", "b"))
    for px in (-74.88, -72.45, -69.65, -67.22):            # brick pilasters
        box(p, "brick", px - 0.22, px + 0.22, y1, y1 + 0.14, 0.0, G + 3.45, sides=("n", "e", "w"))
    window(p, "door_brown", "+y", (-71.05, y1, G + 0.3), 1.1, 2.4)
    box(p, "concrete", -72.0, -70.1, y1, y1 + 0.9, 0.0, G + 0.3)               # step
    win_row(p, [green(), green()], "+y", y1, (-73.65, -68.45), G + 0.8, 1.2, 2.2)
    win_row(p, [green(), green(), green()], "+y", y1, (-73.65, -71.05, -68.45), G + 4.7, 0.95, 1.7)
    win_row(p, [green(), green()], "+x", x1, (-17.8, -14.4), G + 0.9, 0.95, 1.9)
    win_row(p, [green(), green()], "+x", x1, (-17.8, -14.4), G + 4.7, 0.95, 1.7)
    # 1-storey frame rear (storeys not legible: assume 1), low shed roof falling south
    r = "K3R"
    shed(r, "clap", "sw:tin_dark", -75.6, -66.2, -30.8, y0, G + 4.0, G + 3.3, "s", oe=0.2)
    foundation(r, -75.6, -66.2, -30.8, y0, G + 0.25, ("e", "w", "s"))
    win_row(r, [cream(), cream(), cream()], "+x", -66.2, (-28.6, -25.1, -21.6), G + 1.0, 0.85, 1.5)
    # paved forecourt between the walk and the front
    sbox("K3G", "concrete", x0, x1, 10.4, 12.6, 0.0, G + 0.01, sides=("t",))


# ===========================================================================
# K4  Double dwelling 10-12 Court (on the street line)
# ===========================================================================
def build_k4():
    p = "K4"
    x0, x1, y0, y1 = -89.0, -79.8, -17.0, -10.7
    eave = G + 6.1
    rise = (y1 - y0) / 2 * math.tan(math.radians(35))
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x")
    foundation(p, x0, x1, y0, y1, G + 0.55, ("n", "e", "w"))
    ridge = eave + rise
    for cx in (-86.9, -81.9):
        chimney(p, cx, (y0 + y1) / 2, ridge - 0.6, ridge + 0.85)
    fl = G + 0.55
    for cx in (-85.35, -83.45):
        window(p, "door_brown", "+y", (cx, y1, fl), 0.95, 2.15)
        box(p, "concrete", cx - 0.6, cx + 0.6, y1, y1 + 0.75, 0.0, fl - 0.2)
        box(p, "concrete", cx - 0.6, cx + 0.6, y1, y1 + 0.4, 0.0, fl)
        box(p, "sw:paint_white", cx - 0.65, cx + 0.65, y1, y1 + 0.35, fl + 2.3, fl + 2.42)    # hood
    win_row(p, [cream(), cream()], "+y", y1, (-87.7, -81.1), fl + 0.75, 0.9, 1.7)
    win_row(p, [cream() for _ in range(4)], "+y", y1, (-87.7, -85.4, -83.4, -81.1), fl + 3.6, 0.9, 1.6)
    win_row(p, [cream(), cream()], "+x", x1, (-15.3, -12.4), fl + 0.75, 0.9, 1.7)
    win_row(p, [cream(), cream()], "+x", x1, (-15.3, -12.4), fl + 3.6, 0.9, 1.6)
    window(p, "attic_window", "+x", (x1, (y0 + y1) / 2, eave + 0.45), 0.6, 0.6)
    # rear part, 2 storeys, gable to the rear, ridge lower than the main one
    r = "K4R"
    rx0, rx1, ry0, ry1 = -87.4, -79.8, -23.6, y0
    rr = (rx1 - rx0) / 2 * math.tan(math.radians(27))
    gable_walls(r, "clap", rx0, rx1, ry0, ry1 + 0.3, eave - 0.3, rr, "y")
    gable_roof(r, rx0, rx1, ry0, ry1, eave - 0.3, rr, "y", og=0.25)
    win_row(r, [cream(), cream()], "+x", rx1, (-22.1, -19.0), fl + 0.75, 0.9, 1.7)
    win_row(r, [cream(), cream()], "+x", rx1, (-22.1, -19.0), fl + 3.6, 0.9, 1.6)


# ===========================================================================
# K5  Flemington Steam Laundry (1.1 m behind the line), boiler lean-to and stack
# ===========================================================================
def build_k5():
    p = "K5"
    x0, x1, y0, y1 = -108.2, -99.8, -34.5, -11.5
    eave = G + 6.0
    rise = (x1 - x0) / 2 * math.tan(math.radians(30))
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "y", top="sw:tin_dark")
    foundation(p, x0, x1, y0, y1, G + 0.3, ("n", "e", "w", "s"))
    window(p, "barn_doors", "+y", (-105.6, y1, G), 2.6, 2.8)
    window(p, "door_brown", "+y", (-102.6, y1, G + 0.3), 0.95, 2.15)
    box(p, "concrete", -103.2, -102.0, y1, y1 + 0.5, 0.0, G + 0.3)
    window(p, cream(), "+y", (-101.0, y1, G + 1.0), 0.9, 1.7)
    win_row(p, [cream(), cream(), cream()], "+y", y1, (-106.6, -104.0, -101.4), G + 3.7, 0.9, 1.6)
    window(p, "attic_window", "+y", (-104.0, y1, eave + 0.5), 0.7, 0.7)
    ys = [y1 - 1.9 - 2.85 * i for i in range(8)]
    win_row(p, [cream() for _ in ys], "+x", x1, ys, G + 1.0, 0.9, 1.7)
    win_row(p, [cream() for _ in ys], "+x", x1, ys, G + 3.7, 0.9, 1.6)
    win_row(p, [cream() for _ in ys], "-x", x0, ys, G + 3.7, 0.9, 1.6)
    # boiler lean-to and the iron stack
    b = "K5B"
    shed(b, "clap", "sw:tin_dark", -102.4, x1, -39.5, y0, G + 3.6, G + 3.0, "s", oe=0.2)
    sx, sy, r = -101.3, -36.4, 0.32
    n = 10
    ring = [(sx + r * math.cos(2 * math.pi * k / n), sy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    faces = [[(ring[k][0], ring[k][1], G + 2.5), (ring[(k + 1) % n][0], ring[(k + 1) % n][1], G + 2.5),
              (ring[(k + 1) % n][0], ring[(k + 1) % n][1], G + 9.0), (ring[k][0], ring[k][1], G + 9.0)]
             for k in range(n)]
    solid(b, faces, "sw:iron_dark")
    rr = r + 0.07
    ring2 = [(sx + rr * math.cos(2 * math.pi * k / n), sy + rr * math.sin(2 * math.pi * k / n)) for k in range(n)]
    faces = [[(ring2[k][0], ring2[k][1], G + 8.75), (ring2[(k + 1) % n][0], ring2[(k + 1) % n][1], G + 8.75),
              (ring2[(k + 1) % n][0], ring2[(k + 1) % n][1], G + 9.0), (ring2[k][0], ring2[k][1], G + 9.0)]
             for k in range(n)]
    solid(b, faces, "sw:iron_dark")


# ===========================================================================
# K6-K10 dwellings behind porches (tier 2 per section 3, with cheap atlas windows)
# ===========================================================================
def house_front(p, x0, x1, y_front, fl, xs_ground, xs_up, door_x):
    for i, cx in enumerate(xs_ground):
        if cx in door_x:
            window(p, "door_brown" if rng.random() < 0.6 else "door_green", "+y", (cx, y_front, fl), 0.95, 2.15)
        else:
            window(p, cream(), "+y", (cx, y_front, fl + 0.75), 0.9, 1.7)
    win_row(p, [cream() for _ in xs_up], "+y", y_front, xs_up, fl + 3.55, 0.9, 1.6)


def build_k6():
    p = "K6"
    x0, x1, y0, y1 = -122.9, -113.7, -28.9, -18.2
    eave, fl = G + 6.0, G + 0.6
    rise = (y1 - y0) / 2 * math.tan(math.radians(24))
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.45)
    foundation(p, x0, x1, y0, y1, fl, ("n", "e", "w"))
    ex0, ex1 = -119.7, -115.0                         # rear ell, low gable to the rear
    er = (ex1 - ex0) / 2 * math.tan(math.radians(24))
    gable_walls(p, "clap", ex0, ex1, -34.3, y0 + 0.3, eave - 0.4, er, "y")
    gable_roof(p, ex0, ex1, -34.3, y0, eave - 0.4, er, "y", oe=0.4)
    chimney(p, -116.4, (y0 + y1) / 2, eave + rise - 0.6, eave + rise + 0.8)
    porch(p, x0, x1, y1, -16.6, "n", fl, G + 3.35, (-122.6, -119.6, -116.9, -114.0), steps_x=(-118.25,))
    house_front(p, x0, x1, y1, fl, (-121.4, -119.6, -116.9, -115.2), (-121.4, -119.6, -116.9, -115.2), (-118.25,))
    window(p, "door_brown", "+y", (-118.25, y1, fl), 0.95, 2.15)
    win_row(p, [cream(), cream(), cream()], "+x", x1, (-27.0, -23.6, -20.2), fl + 0.75, 0.9, 1.7)
    win_row(p, [cream(), cream(), cream()], "+x", x1, (-27.0, -23.6, -20.2), fl + 3.55, 0.9, 1.6)


def front_gable_house(p, x0, x1, y0, y1, porch_y, pitch, posts, door_x, xs_ground, xs_up,
                      side_ys, eave=G + 6.0, cross=None):
    fl = G + 0.6
    rise = (x1 - x0) / 2 * math.tan(math.radians(pitch))
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "y", oe=0.4, og=0.35)
    foundation(p, x0, x1, y0, y1, fl, ("n", "e", "w"))
    chimney(p, (x0 + x1) / 2, y0 + 1.8, eave + rise - 0.9, eave + rise + 0.7)
    porch(p, x0, x1, y1, porch_y, "n", fl, G + 3.35, posts, steps_x=(door_x,))
    house_front(p, x0, x1, y1, fl, xs_ground, xs_up, (door_x,))
    window(p, "attic_window", "+y", ((x0 + x1) / 2, y1, eave + 0.55), 0.7, 0.75)
    win_row(p, [cream() for _ in side_ys], "+x", x1, side_ys, fl + 0.75, 0.9, 1.7)
    win_row(p, [cream() for _ in side_ys], "+x", x1, side_ys, fl + 3.55, 0.9, 1.6)
    if cross:                                          # cross gable on the east slope
        yc, wc = cross
        cross_gable(p, "clap", "e", yc, wc, x1, eave, wc / 2 * math.tan(math.radians(pitch)),
                    rise / ((x1 - x0) / 2))
        window(p, "attic_window", "+x", (x1, yc, eave + 0.3), 0.6, 0.7)


def build_k7_k9():
    # K7 (18 Court): front gable with a cross gable on the east side
    front_gable_house("K7", -139.9, -131.3, -31.2, -18.4, -16.6, 35, (-139.6, -136.7, -134.5, -131.6),
                      -133.2, (-138.4, -136.0, -133.2), (-138.4, -135.6, -132.8),
                      (-29.0, -24.6, -20.6), cross=(-24.6, 3.4))
    # K8, K9 (20, 22 Court): gable end to the street, 3-bay porches
    front_gable_house("K8", -148.1, -142.0, -27.0, -17.2, -15.5, 38, (-147.8, -145.95, -144.15, -142.3),
                      -146.9, (-146.9, -145.0, -143.2), (-146.7, -143.4), (-25.2, -21.8, -18.9))
    front_gable_house("K9", -155.8, -149.3, -27.0, -17.2, -15.5, 38, (-155.5, -153.5, -151.6, -149.6),
                      -150.6, (-154.5, -152.6, -150.6), (-154.4, -150.7), (-25.2, -21.8, -18.9))


def build_k10():
    p = "K10"
    x0, x1, y0, y1 = -168.1, -157.1, -26.7, -17.2
    eave, fl = G + 6.6, G + 0.6
    rise = (y1 - y0) / 2 * math.tan(math.radians(36))
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.5, og=0.35)
    foundation(p, x0, x1, y0, y1, fl, ("n", "e", "w"))
    cross_gable(p, "clap", "n", -162.6, 3.4, y1, eave, 1.7 * math.tan(math.radians(42)), rise / ((y1 - y0) / 2))
    window(p, "attic_window", "+y", (-162.6, y1, eave + 0.25), 0.65, 0.8)
    ridge = eave + rise
    for cx in (-166.2, -159.0):
        chimney(p, cx, (y0 + y1) / 2, ridge - 0.7, ridge + 0.8)
    # rear wing
    gable_walls(p, "clap", x0, -162.3, -31.4, y0 + 0.3, eave - 0.9, 2.9 * math.tan(math.radians(30)), "y")
    gable_roof(p, x0, -162.3, -31.4, y0, eave - 0.9, 2.9 * math.tan(math.radians(30)), "y", oe=0.4)
    # 3-bay porch across the centre bays, 5-bay front (two doors: a duplex)
    porch(p, -166.3, -158.9, y1, -15.5, "n", fl, G + 3.4, (-166.0, -163.6, -161.6, -159.2),
          steps_x=(-164.6, -160.6))
    house_front(p, x0, x1, y1, fl, (-167.0, -164.6, -162.6, -160.6, -158.2),
                (-167.0, -164.6, -162.6, -160.6, -158.2), (-164.6, -160.6))
    win_row(p, [cream(), cream()], "+x", x1, (-24.4, -19.6), fl + 0.75, 0.9, 1.7)
    win_row(p, [cream(), cream()], "+x", x1, (-24.4, -19.6), fl + 3.55, 0.9, 1.6)
    window(p, "attic_window", "+x", (x1, (y0 + y1) / 2, eave + 0.6), 0.7, 0.8)


def build_k11():
    p = "K11"
    x0, x1, y0, y1 = -119.7, -112.5, -46.2, -39.4
    eave = G + 5.6
    rise = (x1 - x0) / 2 * math.tan(math.radians(30))
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "y", top="sw:tin_dark")
    window(p, "barn_doors", "+y", (-116.1, y1, G), 2.8, 2.9)
    window(p, "attic_window", "+y", (-116.1, y1, G + 3.6), 0.9, 0.9)
    x0, x1, y0, y1 = -126.4, -112.5, -60.9, -46.2
    rise = (y1 - y0) / 2 * math.tan(math.radians(25))
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", top="sw:tin_dark")
    window(p, "barn_doors", "+x", (x1, -53.5, G), 2.8, 2.9)


# ===========================================================================
# Ground beyond x -60, park edge, fences, park paths, lamp
# ===========================================================================
def flat(part, mat, x0, x1, z0, z1, y):
    """horizontal quad from scene ranges, facing up"""
    face_out(part, mat, [P(x0, z0, y), P(x1, z0, y), P(x1, z1, y), P(x0, z1, y)], (0, 0, 1))


def skirt(part, mat, a, b, y_top, y_bot, outward):
    """vertical face between scene points a=(x,z) and b"""
    face_out(part, mat, [P(a[0], a[1], y_bot), P(b[0], b[1], y_bot), P(b[0], b[1], y_top), P(a[0], a[1], y_top)],
             outward)


def build_ground():
    # Court St road (earth, flat like js/ground.js's arm), z 2.0 .. 8.4
    xs = [X_END + (X_JOIN - X_END) * k / 8 for k in range(9)]
    for a, b in zip(xs, xs[1:]):
        flat("Road", "road", a, b, 2.0, 8.4, ROAD_Y)
    # walks 2.0 m each side with a stone curb strip (0.24 m) and curb faces
    for a, b in zip(xs, xs[1:]):
        flat("Walk", "concrete", a, b, 0.0, 1.76, G)
        flat("Curb", "concrete", a, b, 1.76, 2.0, G + 0.01)
        flat("Walk", "concrete", a, b, 8.64, 10.4, G)
        flat("Curb", "concrete", a, b, 8.4, 8.64, G + 0.01)
    skirt("Curb", "concrete", (X_END, 2.0), (X_JOIN, 2.0), G + 0.01, ROAD_Y - 0.02, (0, -1, 0))
    skirt("Curb", "concrete", (X_END, 8.4), (X_JOIN, 8.4), G + 0.01, ROAD_Y - 0.02, (0, 1, 0))
    for z0, z1 in ((0.0, 2.0), (8.4, 10.4)):
        skirt("Curb", "concrete", (X_END, z0), (X_END, z1), G + 0.01, 0.0, (-1, 0, 0))
    # paths from the walk to the houses and the Legion
    for cx, z1 in ((-118.25, 16.6), (-133.2, 16.6), (-146.9, 15.5), (-150.6, 15.5), (-164.6, 15.5), (-160.6, 15.5)):
        flat("Walk", "concrete", cx - 0.6, cx + 0.6, 10.4, z1, G + 0.012)
    # south lots (yards), z 10.4 .. 62, x -172 .. -45, at the walk top; edges skirt down
    lot_x = [X_END, -150.0, -128.0, -110.0, -90.0, -70.0, -45.0]
    for a, b in zip(lot_x, lot_x[1:]):
        for z0, z1 in ((10.4, 36.0), (36.0, 62.0)):
            flat("Lots", "grass", a, b, z0, z1, G)
    skirt("Lots", "grass", (X_END, 10.4), (X_END, 62.0), G, -0.05, (-1, 0, 0))
    skirt("Lots", "grass", (X_END, 62.0), (-45.0, 62.0), G, -0.05, (0, -1, 0))
    skirt("Lots", "grass", (-45.0, 62.0), (-45.0, 17.7), G, -0.05, (1, 0, 0))
    # north lot behind the fire house (x -64.1 .. -49.5, clear of the jail yard)
    flat("LotN", "grass", -64.1, -49.5, -60.0, 0.0, G)
    skirt("LotN", "grass", (-64.1, -60.0), (-49.5, -60.0), G, -0.05, (0, 1, 0))
    skirt("LotN", "grass", (-49.5, -60.0), (-49.5, -14.5), G, -0.05, (1, 0, 0))
    # the Public Park: lawn 0.4 m above the walk, dark stone bank along the walk
    px = [X_END, -150.0, -128.0, -108.0, -86.0, -64.1]
    for a, b in zip(px, px[1:]):
        for z0, z1 in ((-60.0, -30.0), (-30.0, -0.15)):
            flat("Park", "grass", a, b, z0, z1, PARK)
    skirt("Bank", "concrete", (X_END, 0.0), (-64.1, 0.0), PARK, G - 0.02, (0, -1, 0))
    flat("Bank", "concrete", X_END, -64.1, -0.15, 0.0, PARK)
    skirt("Park", "grass", (X_END, -60.0), (X_END, 0.0), PARK, -0.05, (-1, 0, 0))
    skirt("Park", "grass", (X_END, -60.0), (-64.1, -60.0), PARK, -0.05, (0, 1, 0))
    skirt("Park", "grass", (-64.1, -60.0), (-64.1, -14.1), PARK, G - 0.02, (1, 0, 0))
    # gravel paths (photo: curving walks): from the gate at x -95 into the park
    paths = [[(-95.0, 0.0), (-96.0, -6.0), (-101.0, -12.5), (-110.0, -17.5), (-121.0, -21.0),
              (-134.0, -24.5), (-148.0, -29.0), (-160.0, -32.5), (-172.0, -34.0)],
             [(-101.0, -12.5), (-96.0, -22.0), (-90.0, -31.0), (-81.0, -40.0), (-70.0, -47.0), (-64.1, -49.0)]]
    for pts in paths:
        ribbon("Paths", "sw:stone_cream", pts, 1.8, PARK + 0.012)


def ribbon(part, mat, pts, w, y):
    """flat strip along scene points (x, z), width w"""
    left, right = [], []
    for i, (x, z) in enumerate(pts):
        a = Vector(pts[max(0, i - 1)])
        b = Vector(pts[min(len(pts) - 1, i + 1)])
        d = (b - a).normalized()
        nrm = Vector((-d.y, d.x)) * (w / 2)
        left.append((x + nrm.x, z + nrm.y))
        right.append((x - nrm.x, z - nrm.y))
    for i in range(len(pts) - 1):
        face_out(part, mat, [P(*left[i], y), P(*right[i], y), P(*right[i + 1], y), P(*left[i + 1], y)], (0, 0, 1))


def build_fences():
    # low picket fence on the walk line in front of K6-K10 (photo: dark posts, pale pickets),
    # gates at the house paths
    z = 10.5
    gates = [(-118.25, 1.3), (-133.2, 1.3), (-146.9, 1.3), (-150.6, 1.3), (-164.6, 1.3), (-160.6, 1.3)]
    runs, x = [], X_END + 0.1
    for gx, gw in sorted(gates):
        runs.append((x, gx - gw / 2))
        x = gx + gw / 2
    runs.append((x, -111.5))
    h = 0.95
    u0, v0, u1, v1 = ATLAS["pickets"]
    for a, b in runs:
        L = b - a
        uvs = [(0, v0), (L / 2.0, v0), (L / 2.0, v1), (0, v1)]
        for side, zz in ((-1, z - 0.015), (1, z + 0.015)):
            face_out("Fence", "atlas", [P(a, zz, G), P(b, zz, G), P(b, zz, G + h), P(a, zz, G + h)], (0, -side, 0),
                     uvs)
        posts = [a] + [a + L * k / max(1, round(L / 2.4)) for k in range(1, round(L / 2.4))] + [b]
        for px in posts:
            sbox("Fence", "sw:iron_dark", px - 0.06, px + 0.06, z - 0.06, z + 0.06, 0.0, G + h + 0.1,
                 sides=("t", "n", "s", "e", "w"))
    # white X-braced rail on the park bank (photo, c. 1910), with a gate gap at x -95
    zr, y0 = -0.3, PARK
    top = y0 + 0.85
    for a, b in ((X_END, -96.0), (-94.0, -64.6)):
        n = max(1, round((b - a) / 3.0))
        xs = [a + (b - a) * k / n for k in range(n + 1)]
        for px in xs:
            sbox("Rail", "sw:paint_white", px - 0.06, px + 0.06, zr - 0.06, zr + 0.06, y0 - 0.1, top + 0.05,
                 sides=("t", "n", "s", "e", "w"))
        sbox("Rail", "sw:paint_white", a, b, zr - 0.045, zr + 0.045, top - 0.09, top, sides=("t", "n", "s", "b"))
        sbox("Rail", "sw:paint_white", a, b, zr - 0.03, zr + 0.03, y0 + 0.08, y0 + 0.15, sides=("t", "n", "s"))
        for p0, p1 in zip(xs, xs[1:]):
            for (xa, ya), (xb, yb) in (((p0 + 0.06, y0 + 0.15), (p1 - 0.06, top - 0.09)),
                                       ((p0 + 0.06, top - 0.09), (p1 - 0.06, y0 + 0.15))):
                dx, dy = xb - xa, yb - ya
                ln = math.hypot(dx, dy)
                ox, oy = -dy / ln * 0.035, dx / ln * 0.035          # bar half-width
                for side in (-1, 1):
                    zz = zr + side * 0.02
                    face_out("Rail", "sw:paint_white",
                             [P(xa - ox, zz, ya - oy), P(xb - ox, zz, yb - oy), P(xb + ox, zz, yb + oy),
                              P(xa + ox, zz, ya + oy)], (0, -side, 0))
    # one tall lamp pole in the park (photo: thin pole with an arm lamp)
    lx, lz = -104.0, -9.0
    sbox("Lamp", "sw:iron_dark", lx - 0.07, lx + 0.07, lz - 0.07, lz + 0.07, PARK - 0.1, PARK + 7.5,
         sides=("n", "s", "e", "w", "t"))
    sbox("Lamp", "sw:iron_dark", lx, lx + 1.2, lz - 0.04, lz + 0.04, PARK + 7.1, PARK + 7.18,
         sides=("n", "s", "t", "b", "e"))
    sbox("Lamp", "sw:iron_dark", lx + 1.0, lx + 1.24, lz - 0.12, lz + 0.12, PARK + 6.75, PARK + 7.1,
         sides=("n", "s", "e", "w", "b"))


# ===========================================================================
# build
# ===========================================================================
def clear_collection():
    col = bpy.data.collections.get(COLL)
    if col:
        for o in list(col.objects):
            m = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if m and m.users == 0:
                bpy.data.meshes.remove(m)
    else:
        col = bpy.data.collections.new(COLL)
        bpy.context.scene.collection.children.link(col)
    return col


def uv_for(mat, pts, n):
    if mat.startswith("sw:"):
        u0, v0, u1, v1 = ATLAS[mat[3:]]
        return [((u0 + u1) / 2, (v0 + v1) / 2)] * len(pts)
    if mat == "road":     # js/ground.js's Court St arm: u = (z - 5.2) / 6.4 + 0.5, v = x / 6.4
        return [((-p.y - 5.2) / 6.4 + 0.5, p.x / 6.4) for p in pts]
    tile = TILE[mat]
    out = []
    h = math.hypot(n.x, n.y)
    for co in pts:
        if 0.25 < abs(n.z) < 0.97:
            tx, ty = -n.y / h, n.x / h
            u, v = co.x * tx + co.y * ty, co.z / h
        elif abs(n.z) >= 0.97:
            u, v = co.x, co.y
        else:
            tx, ty = -n.y / h, n.x / h
            u, v = co.x * tx + co.y * ty, co.z
        out.append((u / tile, v / tile))
    return out


FINAL_MAT = {"clap": "clap", "brick": "brick", "slate": "slate", "concrete": "concrete", "grass": "grass",
             "road": "road", "atlas": "atlas"}


def make_objects(col):
    groups = {}
    for (part, mat), data in BUCKETS.items():
        fm = "atlas" if mat.startswith("sw:") else FINAL_MAT[mat]
        groups.setdefault((part, fm), []).append((mat, data))
    objs = []
    for (part, fm), items in sorted(groups.items()):
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new("UVMap")
        for mat, (verts, faces) in items:
            for idx, uvs in faces:
                pts = [verts[i] for i in idx]
                bv = [bm.verts.new(p) for p in pts]
                try:
                    f = bm.faces.new(bv)
                except ValueError:
                    continue
                n = newell(pts)
                uvs = uvs or uv_for(mat, pts, n)
                for loop, uv in zip(f.loops, uvs):
                    loop[uvl].uv = uv
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        me = bpy.data.meshes.new("SC_%s_%s" % (part, fm))
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(me.name, me)
        ob["part"], ob["mat"] = part, fm
        col.objects.link(ob)
        objs.append(ob)
    return objs


BUCKETS.clear()
col = clear_collection()
build_k1()
build_k2()
build_k3()
build_k4()
build_k5()
build_k6()
build_k7_k9()
build_k10()
build_k11()
build_ground()
build_fences()
OBJS = make_objects(col)
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in OBJS)
print("SidestreetCourt built:", len(OBJS), "objects,", tris, "triangles")
