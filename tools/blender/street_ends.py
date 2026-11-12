"""
street_ends.py - what closes the views north and south along Main St beyond the walkable
stretch (PLAN.md "Side streets, backdrop buildings", sections 1f, 7.1, 7.2, 7.5, 7.7, 7.8):
the E-rows, at the Sanborn footprints (north end: Sept 1921 sheet 2, +-0.5 m; south end: sheet 3,
+-1.5 m; Presbyterian church: sheet 5 via the planner, +-5 m), as one cheap model, plus the
ground js/ground.js does not draw at the two ends.

NORTH END (west side fronts face scene +x = Blender +X; east side fronts face -X)
  E1  former Hotel Flemington / "Hotel Hunterdon" (Capner corner, old 520-522): 3 storeys +
      basement, red brick, flat roof behind a bracketed cornice, full-length 2-storey frame porch
      (square posts, arched lattice friezes, baluster railings on both decks, deck raised 0.9 m),
      two gabled entrance hoods with steps; iron-clad rear wing     PHOTO-BASED (1908 cards)
  E2  12-16 Main: 3-storey frame, flat roof, 2-storey front porch on square posts
                                                                 PLAIN-GUESS (NRHP-1980 form)
  E3  18 Main "Boarding" and E4 20-22 Main "Gro.": 2-storey frame Italianate, low slate front
      gables with wide eaves, 3-bay porch (E3), canted 2-storey bay / oriel (E4)
                                                                 PLAIN-GUESS (NRHP-1980 form)
  E9  Soldiers' Monument on its railed, raised grass triangle at the fork of Main St, Branch St
      and Pennsylvania Ave: stepped base, die, pedestal, standing soldier; low dark spear-top
      railing on a stone curb, one dark iron post at the east corner     PHOTO-BASED
  E8  First Presbyterian Church (10 East Main), dark grey stone, square SW tower with a broach
      spire to 33.5 m, gabled lucarnes and a vane; steep south gable with a rose window, low
      front range with five round-headed windows, gabled entrance porch, east wing gable,
      hipped chapel with a stone chimney; lawn with curving paths     PHOTO-BASED (1898-1923)
SOUTH END (all on the east side, fronts face -X)
  E5  Vosseller Building 108-112 Main: 3-storey dark red brick, flat roof behind a cornice,
      pale window heads, three shop fronts, second-storey porch across the front on diagonal
      braces (no ground posts)                                    PHOTO-BASED (1907)
  E6  Doric House 114 Main: frame, white, Greek Revival, flat roof, full-width 2-storey portico
      on 4 SQUARE PANELLED PIERS (HABS), deep entablature with 3 cast-iron frieze grilles,
      3-bay front, shutters, door in the right-hand bay; iron fence on a stone curb
                                                                  PHOTO-BASED (HABS, 1906)
  E7  Methodist Episcopal Church 116 Main: warm buff-grey rock-faced stone, two steep gables
      (west to Main St, south to Maple Ave) with large pointed traceried windows and roses,
      SW tower with paired louvred lancets, corbel band, four pinnacles and an octagonal spire,
      squat hipped "24'" tower, lower hipped chapel with a canted east end, ivy on the west
      gable, slate roofs, lamp post                                PHOTO-BASED (1906-1909)
  E10 Public Library 118 Main: 2 storeys, dark red brick, pale stone giant pilasters, base,
      band course, plain (blank) frieze and cornice, low hipped roof, a door on each face
                                                                  PHOTO-BASED (undated card)
  E11 Deats Building 120-124 Main (Club Room / Post Office): 3 storeys red brick "40'",
      bracketed cornice with a small central pediment, pale window heads, shop front with an
      entrance, four chimneys on the south wall                   PHOTO-BASED (1908)
Not built: W1 Reading-Large House (optional, not marked to build), Lyceum, band stand, any
sign or lettering (the library frieze stays blank). No trees (the scene instances
backdrop-tree.glb; positions in street_ends_bake.py).

Ground: Main St road (crowned exactly as js/ground.js), walks, curbs, lots and lawns north of
z -180 and south of z +80 (js/ground.js draws Main St from z -180 to +80), the junction with
Branch St and Pennsylvania Ave, Capner St and Maple Ave stubs, the monument plot, the church lots.
2026-11-12 (PLAN.md 7.9): NOT the west side z -202.4 .. -328.7 (west walk x -10.4 .. -6.4, its
grass strip and the lawns of 1-11 Main) nor the east lawns z -192.4 .. -307.2 (2-10 Main): those
are drawn by north-approach.glb (tools/blender/north_approach.py), which also has the houses.
North of z -328.7 the west walk keeps the 1913 section: grass strip 2.2 m, concrete 1.8 m.

Run inside Blender:
    exec(open(r"<project>/tools/blender/street_ends.py").read())
Every run deletes and rebuilds the "StreetEnds" collection. Materials, lightmap bake and GLB
export: street_ends_bake.py (runs this file first). Shared helpers are taken with `ast` from
sidestreet_court.py and sidestreet_bloomfield.py, as in the other backdrops.

Coordinates: SCENE AXES (the GLB is placed at "0 0 0", rotation "0 0 0"):
    Blender X = scene x (east), Blender Y = -scene z (north = +Y), Blender Z = scene y (up).
Ground level: lots, walks and the bottom of every wall at y 0.15; walls skirt down to 0.0.
Road 0.01 at the curbs (+0.10 crown on the straight stretches, as js/ground.js).
"""

import ast
import json
import math
import random
import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.geometry import tessellate_polygon

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
COURT = PROJECT + r"\tools\blender\sidestreet_court.py"
BLOOM = PROJECT + r"\tools\blender\sidestreet_bloomfield.py"
COLL = "StreetEnds"
G = 0.15
ROAD_Y = 0.01
CROWN = 0.10
ATLAS = json.load(open(PROJECT + r"\assets\textures\shared\backdrop_windows.json"))["cells"]
TILE = {"clap": 1.0, "brick": 1.4, "slate": 1.5, "block": 2.0, "concrete": 3.0, "grass": 4.0, "earth": 2.0}
rng = random.Random(1888)
BUCKETS = {}


def _take(path, names):
    tree = ast.parse(open(path, encoding="utf8").read())
    mod = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names],
                     type_ignores=[])
    exec(compile(mod, path, "exec"), globals())
    missing = set(names) - {n.name for n in mod.body}
    assert not missing, missing


_take(COURT, {"P", "newell", "add", "face_out", "solid", "box", "sbox", "gable_walls", "slab", "gable_roof",
              "shed", "window", "win_row", "cream", "green", "clear_collection", "uv_for", "make_objects"})
_take(BLOOM, {"fp", "foundation", "chimney", "front_row", "sill_lintel", "split"})

FINAL_MAT = {k: k for k in ("clap", "brick", "slate", "block", "concrete", "grass", "earth", "road", "atlas")}
TAN = lambda deg: math.tan(math.radians(deg))
UP = Vector((0, 0, 1))


# ===========================================================================
# extra helpers
# ===========================================================================
NRM = {"-x": Vector((-1, 0, 0)), "+x": Vector((1, 0, 0)), "+y": Vector((0, 1, 0)), "-y": Vector((0, -1, 0))}


def WP(n, c, u, v):
    """point on a wall plane: n = outward axis, c = plane coordinate, u = to the right as seen
    from outside, v = height (Blender z)"""
    if n == "-x":
        return Vector((c, -u, v))
    if n == "+x":
        return Vector((c, u, v))
    if n == "+y":
        return Vector((-u, c, v))
    return Vector((u, c, v))


def U_of(n, p):
    """u coordinate of a Blender point on wall n"""
    return {"-x": -p[1], "+x": p[1], "+y": -p[0], "-y": p[0]}[n]


def arch2d(cu, w, v0, vs, kind="pointed", n=4, rf=0.9):
    """opening outline (u, v): bottom, right jamb, arch, left jamb (counter-clockwise from outside)"""
    r = w / 2
    pts = [(cu - r, v0), (cu + r, v0), (cu + r, vs)]
    if kind == "flat":
        return pts + [(cu - r, vs)]
    if kind == "round":
        for k in range(1, n * 2):
            a = math.pi * k / (2 * n)
            pts.append((cu + r * math.cos(a), vs + r * math.sin(a)))
        return pts + [(cu - r, vs)]
    R = rf * w
    th = math.acos((R - r) / R)
    for k in range(1, n + 1):                                   # right arc, centre left of the axis
        a = th * k / n
        pts.append((cu + r - R + R * math.cos(a), vs + R * math.sin(a)))
    for k in range(n - 1, -1, -1):                              # left arc (mirror), apex excluded
        a = th * k / n
        pts.append((cu - r + R - R * math.cos(a), vs + R * math.sin(a)))
    return pts


def circle2d(cu, cv, r, n=16):
    return [(cu + r * math.cos(2 * math.pi * k / n), cv + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def cell_uvs(cell, pts2d):
    u0, v0, u1, v1 = ATLAS[cell]
    us = [p[0] for p in pts2d]
    vs = [p[1] for p in pts2d]
    a, b, c, d = min(us), max(us), min(vs), max(vs)
    return [(u0 + (u1 - u0) * (p[0] - a) / max(1e-6, b - a), v0 + (v1 - v0) * (p[1] - c) / max(1e-6, d - c))
            for p in pts2d]


def wall_poly(part, mat, n, c, pts2d, off=0.03, cell=None):
    """flat polygon on a wall plane, `off` metres proud; cell = atlas cell stretched over it"""
    N = NRM[n]
    pts = [WP(n, c, u, v) + N * off for u, v in pts2d]
    if cell:
        face_out(part, "atlas", pts, N, cell_uvs(cell, pts2d))
    else:
        face_out(part, mat, pts, N)


def wall_holes(part, mat, n, c, outer, holes, depth=0.3, back=None, reveal=None):
    """wall face with openings: outer / holes as (u, v) loops; every hole gets reveal faces
    `depth` deep and (if back = (part, mat or cell)) a back face"""
    N = NRM[n]
    loops = [outer] + list(holes)
    tris = tessellate_polygon([[(u, v, 0.0) for u, v in L] for L in loops])
    allp = [WP(n, c, u, v) for L in loops for u, v in L]
    for a, b, cc in tris:
        face_out(part, mat, [allp[a], allp[b], allp[cc]], N)
    for h in holes:
        P3 = [WP(n, c, u, v) for u, v in h]
        hc = sum(P3, Vector()) / len(P3)
        for i in range(len(P3)):
            a, b = P3[i], P3[(i + 1) % len(P3)]
            face_out(part, reveal or mat, [a, b, b - N * depth, a - N * depth], hc - (a + b) / 2)
        if back:
            bpart, bmat = back
            wall_poly(bpart, bmat if bmat in BLOCKMATS else None, n, c - (depth if n[0] == "+" else -depth), h,
                      off=0.0, cell=None if bmat in BLOCKMATS else bmat)


BLOCKMATS = {"clap", "brick", "slate", "block", "concrete", "grass", "earth"} | {
    "sw:" + k for k in ATLAS}


def gable2d(u0, u1, eave, ridge, z0=0.0):
    return [(u0, z0), (u1, z0), (u1, eave), ((u0 + u1) / 2, ridge), (u0, eave)]


def ring(cx, cy, r, n, z, rot=0.0):
    return [Vector((cx + r * math.cos(rot + 2 * math.pi * k / n), cy + r * math.sin(rot + 2 * math.pi * k / n), z))
            for k in range(n)]


def prism(part, mat, bot, top, cap=False):
    c = sum(bot, Vector()) / len(bot)
    n = len(bot)
    for k in range(n):
        a, b = bot[k], bot[(k + 1) % n]
        face_out(part, mat, [a, b, top[(k + 1) % n], top[k]], ((a + b) / 2 - c) * Vector((1, 1, 0)))
    if cap:
        face_out(part, mat, top, UP)


def pyramid(part, mat, base, apex):
    c = sum(base, Vector()) / len(base)
    n = len(base)
    for k in range(n):
        a, b = base[k], base[(k + 1) % n]
        mid = (a + b) / 2
        face_out(part, mat, [a, b, apex], (mid - c) * Vector((1, 1, 0)) + UP * 0.2)


def beam(part, mat, a, b, w, h=None):
    """square-section prism between two points (no end caps)"""
    a, b = Vector(a), Vector(b)
    h = h or w
    d = (b - a).normalized()
    s = d.cross(UP) if abs(d.dot(UP)) < 0.99 else d.cross(Vector((1, 0, 0)))
    s.normalize()
    t = s.cross(d).normalized()
    ca = [a + s * sx * w / 2 + t * tx * h / 2 for sx, tx in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    cb = [p + (b - a) for p in ca]
    for k in range(4):
        p0, p1 = ca[k], ca[(k + 1) % 4]
        face_out(part, mat, [p0, p1, cb[(k + 1) % 4], cb[k]], (p0 + p1) / 2 - a)


def hip_roof(part, top, x0, x1, y0, y1, eave, rise, oe=0.35, under="sw:paint_white"):
    """hipped roof surface over a rectangle (equal slopes), eave overhang oe, soffit below"""
    W = min(x1 - x0, y1 - y0)
    s = rise / (W / 2)
    X0, X1, Y0, Y1 = x0 - oe, x1 + oe, y0 - oe, y1 + oe
    ze = eave - oe * s
    zr = eave + rise
    h = (min(X1 - X0, Y1 - Y0)) / 2
    c = Vector(((X0 + X1) / 2, (Y0 + Y1) / 2, ze))
    if abs((X1 - X0) - (Y1 - Y0)) < 0.05:
        apex = Vector(((X0 + X1) / 2, (Y0 + Y1) / 2, zr))
        corners = [Vector((X0, Y0, ze)), Vector((X1, Y0, ze)), Vector((X1, Y1, ze)), Vector((X0, Y1, ze))]
        pyramid(part, top, corners, apex)
    elif X1 - X0 > Y1 - Y0:
        r0, r1 = Vector((X0 + h, (Y0 + Y1) / 2, zr)), Vector((X1 - h, (Y0 + Y1) / 2, zr))
        for f in ([(X0, Y0, ze), (X1, Y0, ze), r1, r0], [(X1, Y1, ze), (X0, Y1, ze), r0, r1],
                  [(X0, Y1, ze), (X0, Y0, ze), r0], [(X1, Y0, ze), (X1, Y1, ze), r1]):
            f = [Vector(p) for p in f]
            fc = sum(f, Vector()) / len(f)
            face_out(part, top, f, (fc - c) * Vector((1, 1, 0)) + UP * 0.3)
    else:
        r0, r1 = Vector(((X0 + X1) / 2, Y0 + h, zr)), Vector(((X0 + X1) / 2, Y1 - h, zr))
        for f in ([(X1, Y0, ze), (X1, Y1, ze), r1, r0], [(X0, Y1, ze), (X0, Y0, ze), r0, r1],
                  [(X0, Y0, ze), (X1, Y0, ze), r0], [(X1, Y1, ze), (X0, Y1, ze), r1]):
            f = [Vector(p) for p in f]
            fc = sum(f, Vector()) / len(f)
            face_out(part, top, f, (fc - c) * Vector((1, 1, 0)) + UP * 0.3)
    # soffit ring (eave underside) between the wall line and the eave edge
    if oe < 0.01:
        return
    for a, b, aa, bb in (((x0, y0), (x1, y0), (X0, Y0), (X1, Y0)), ((x1, y0), (x1, y1), (X1, Y0), (X1, Y1)),
                         ((x1, y1), (x0, y1), (X1, Y1), (X0, Y1)), ((x0, y1), (x0, y0), (X0, Y1), (X0, Y0))):
        face_out(part, under, [(a[0], a[1], eave), (b[0], b[1], eave), (bb[0], bb[1], ze), (aa[0], aa[1], ze)],
                 (0, 0, -1))


def cross(part, x, y, z, h=1.1, w=0.55, t=0.1, mat="sw:stone_cream", axis="x"):
    box(part, mat, x - t / 2, x + t / 2, y - t / 2, y + t / 2, z, z + h, sides=("t", "n", "s", "e", "w"))
    ax, ay = (w / 2, t / 2) if axis == "x" else (t / 2, w / 2)
    box(part, mat, x - ax, x + ax, y - ay, y + ay, z + h * 0.58, z + h * 0.58 + t,
        sides=("t", "b", "n", "s", "e", "w"))


def rail_quad(part, a, b, z0, h, both=False, tile=2.0):
    """picket / baluster strip between Blender points a, b (x, y) from z0, h high (atlas pickets)"""
    u0, v0, u1, v1 = ATLAS["pickets"]
    L = (Vector(b) - Vector(a)).length
    uvs = [(0, v0), (L / tile, v0), (L / tile, v1), (0, v1)]
    d = Vector((b[0] - a[0], b[1] - a[1], 0)).normalized()
    nrm = Vector((-d.y, d.x, 0))
    for sgn in ((1, -1) if both else (1,)):
        o = nrm * 0.012 * sgn
        pts = [Vector((a[0], a[1], z0)) + o, Vector((b[0], b[1], z0)) + o,
               Vector((b[0], b[1], z0 + h)) + o, Vector((a[0], a[1], z0 + h)) + o]
        face_out(part, "atlas", pts, nrm * sgn, uvs)


def lintel(p, n, wall, a, z, w, mat="sw:stone_cream", hh=0.22, proud=0.06):
    """pale window head: front + underside only"""
    f = {"+y": "n", "-y": "s", "+x": "e", "-x": "w"}[n]
    if n in ("+y", "-y"):
        s = 1 if n == "+y" else -1
        yy = sorted((wall, wall + s * proud))
        box(p, mat, a - w / 2 - 0.08, a + w / 2 + 0.08, yy[0], yy[1], z, z + hh, sides=(f, "b"))
    else:
        s = 1 if n == "+x" else -1
        xx = sorted((wall, wall + s * proud))
        box(p, mat, xx[0], xx[1], a - w / 2 - 0.08, a + w / 2 + 0.08, z, z + hh, sides=(f, "b"))


def porch_x(p, xw, xo, ya, yb, decks, roof_z, n_bays, rails=(), stairs=(), post=0.2,
            frieze=None, rail_h=0.85, roof_rise=0.2, lower_mat="sw:iron_dark"):
    """porch on a wall facing +-x (xw = wall plane, xo = outer edge), decks = deck-top heights
    (a first deck below 1.35 m stands on the ground), posts at n_bays + 1 positions, railings on
    the decks listed in `rails` (bays holding stairs left open on the ground deck), arched
    lattice friezes under each upper level if frieze = depth. Returns the post y positions."""
    s = 1 if xo > xw else -1
    xa, xb = min(xw, xo), max(xw, xo)
    out = "e" if s > 0 else "w"
    px = xo - s * (post / 2 + 0.02)
    ys = [ya + post / 2 + 0.02 + (yb - ya - post - 0.04) * k / n_bays for k in range(n_bays + 1)]
    for i, d in enumerate(decks):
        if i == 0 and d < G + 1.35:
            box(p, lower_mat, xa, xb, ya, yb, 0.0, d - 0.12, sides=(out, "n", "s"))
            box(p, "sw:wood_grey", xa, xb, ya, yb, d - 0.12, d, sides=("t", out, "n", "s"))
        else:
            box(p, "sw:wood_grey", xa, xb + (0.05 if s > 0 else 0), ya - 0.05, yb + 0.05, d - 0.25, d,
                sides=("t", out, "n", "s"))
            box(p, "sw:paint_white", xa, xb, ya, yb, d - 0.25, d, sides=("b",))
    levels = list(decks) + [roof_z]
    for i, d in enumerate(decks):
        z_hi = levels[i + 1] - (0.25 if i + 1 < len(decks) else 0.0)
        for y in ys:
            box(p, "sw:paint_white", px - post / 2, px + post / 2, y - post / 2, y + post / 2, d, z_hi,
                sides=("n", "s", "e", "w"))
        if frieze and i + 1 <= len(decks):
            zt = z_hi
            for k in range(n_bays):
                y0, y1 = ys[k] + post / 2, ys[k + 1] - post / 2
                pts = [(px + s * post / 2 + s * 0.01, y0, zt), (px + s * post / 2 + s * 0.01, y1, zt)]
                pts.append((pts[0][0], y1, zt - frieze))
                for u in (0.85, 0.68, 0.5, 0.32, 0.15):
                    pts.append((pts[0][0], y0 + (y1 - y0) * u, zt - frieze + frieze * 0.62 * math.sin(math.pi * u) ** 0.6))
                pts.append((pts[0][0], y0, zt - frieze))
                face_out(p + "L", "sw:paint_white", pts, (s, 0, 0))
        if i in rails:
            for k in range(n_bays):
                yc = (ys[k] + ys[k + 1]) / 2
                if i == 0 and any(abs(yc - st) < (ys[1] - ys[0]) / 2 for st in stairs):
                    continue
                rail_quad(p + "R", (px, ys[k] + post / 2), (px, ys[k + 1] - post / 2), d, rail_h)
            box(p, "sw:paint_white", px - 0.06, px + 0.06, ya, yb, d + rail_h, d + rail_h + 0.08,
                sides=("t", "b", out))
    # roof: high at the wall, falling outward
    slab(p, "sw:tin_dark", "sw:paint_white",
         [(xw, ya - 0.12, roof_z + roof_rise), (xo + s * 0.22, ya - 0.12, roof_z),
          (xo + s * 0.22, yb + 0.12, roof_z), (xw, yb + 0.12, roof_z + roof_rise)], 0.12)
    for st in stairs:
        d = decks[0]
        for k, frac in enumerate((1 / 3, 2 / 3, 1.0)):
            x_far = xo + s * 0.4 * (3 - k)
            box(p, "sw:wood_grey", min(xo, x_far), max(xo, x_far), st - 1.0, st + 1.0, 0.0, d * frac,
                sides=("t", out, "n", "s"))
    return ys


def poly_flat(part, mat, pts_xz, y, holes=(), uvfn=None):
    """flat (horizontal) polygon from scene (x, z) points at height y, triangulated, facing up"""
    loops = [list(pts_xz)] + [list(h) for h in holes]
    tris = tessellate_polygon([[(x, -z, 0.0) for x, z in L] for L in loops])
    allp = [(x, z) for L in loops for x, z in L]
    for a, b, c in tris:
        pts = [P(allp[i][0], allp[i][1], y) for i in (a, b, c)]
        uvs = [uvfn(allp[i][0], allp[i][1]) for i in (a, b, c)] if uvfn else None
        face_out(part, mat, pts, (0, 0, 1), uvs)


def edge_skirt(part, mat, pts_xz, y_top, y_bot, side_point):
    """vertical faces down from a polyline (scene x, z), facing away from side_point (x, z)"""
    sp = Vector((side_point[0], -side_point[1], 0))
    for (ax, az), (bx, bz) in zip(pts_xz, pts_xz[1:]):
        a, b = P(ax, az, y_bot), P(bx, bz, y_bot)
        mid = (a + b) / 2
        d = (b - a).normalized()
        nrm = Vector((-d.y, d.x, 0))
        if nrm.dot(mid - sp) < 0:
            nrm = -nrm
        face_out(part, mat, [a, b, P(bx, bz, y_top), P(ax, az, y_top)], nrm)


# ===========================================================================
# E1  former Hotel Flemington (west side, front faces +X)
# ===========================================================================
def build_e1():
    p = "E1"
    x0, x1, y0, y1 = fp(-25.6, -15.1, -192.5, -167.9)          # Blender y 167.9 .. 192.5
    fl = G + 0.9
    top = G + 11.6
    box(p, "brick", x0, x1, y0, y1, 0.0, top - 0.55, sides=("n", "s", "e", "w"))
    box(p, "sw:wood_grey", x0 - 0.1, x1 + 0.12, y0 - 0.12, y1 + 0.12, top - 1.05, top - 0.55,
        sides=("n", "s", "e", "w", "b"))                                         # frieze / bracket band
    box(p, "sw:paint_cream", x0 - 0.15, x1 + 0.45, y0 - 0.45, y1 + 0.45, top - 0.55, top,
        sides=("t", "n", "s", "e", "w", "b"), top="sw:tin_dark")                 # cornice, flat roof
    bay = (y1 - y0) / 9
    ys = [y0 + bay * (i + 0.5) for i in range(9)]
    doors = (ys[4], ys[8])
    for i, y in enumerate(ys):
        if any(abs(y - d) < 0.01 for d in doors):
            window(p, "door_brown", "+x", (x1, y, fl), 1.1, 2.4)
        else:
            window(p, cream(), "+x", (x1, y, fl + 0.5), 1.0, 2.1)
        window(p, cream(), "+x", (x1, y, G + 5.0), 1.0, 2.0)
        window(p, cream(), "+x", (x1, y, G + 8.55), 0.95, 1.7)
        sill_lintel(p, "+x", x1, y, G + 8.55, 0.95, 1.7)
    # Capner St wall (north) and the strip of the south wall seen above 27 Main
    xs = (-23.9, -21.3, -18.7, -16.4)
    for z in (fl + 0.7, G + 5.0, G + 8.55):
        front_row(p, "+y", y1, xs, z, 0.95, 1.8 if z < 8 else 1.7, cream)
        for a in xs:
            lintel(p, "+y", y1, a, z + (1.8 if z < 8 else 1.7), 0.95)
    front_row(p, "+y", y1, (-23.9, -18.7), G + 0.25, 0.8, 0.5, ["small_window"])
    front_row(p, "-y", y0, (-23.4, -20.1, -16.8), G + 8.55, 0.95, 1.7, cream)
    # two-tier porch, lattice friezes, railings, two gabled entrance hoods with steps
    hoods = (ys[4], ys[8])
    porch_x(p, x1, -13.1, 168.2, 192.25, [fl, G + 4.5], G + 8.05, 10, rails=(0, 1), stairs=hoods,
            frieze=0.75, lower_mat="sw:iron_dark")
    xo = -13.1
    for yc in hoods:
        ze, zr, xh = G + 3.6, G + 4.6, xo + 1.35
        face_out(p, "sw:paint_white", [(xh, yc - 1.25, ze), (xh, yc + 1.25, ze), (xh, yc, zr)], (1, 0, 0))
        for sgn in (-1, 1):
            slab(p, "sw:tin_dark", "sw:paint_white",
                 [(xo, yc + sgn * 1.45, ze - 0.12), (xo, yc, zr + 0.02), (xh + 0.15, yc, zr + 0.02),
                  (xh + 0.15, yc + sgn * 1.45, ze - 0.12)], 0.1)
            box(p, "sw:paint_white", xh - 0.18, xh - 0.02, yc + sgn * 1.15 - 0.08, yc + sgn * 1.15 + 0.08,
                0.0, ze, sides=("n", "s", "e", "w"))
    # iron-clad rear wing, 3 storeys (hidden from Main St but for its top)
    w = "E1W"
    wx0, wx1, wy0, wy1 = fp(-43.2, -25.6, -175.6, -167.9)
    box(w, "clap", wx0, wx1, wy0, wy1, 0.0, G + 9.9, sides=("n", "s", "w"))
    box(w, "sw:tin_dark", wx0 - 0.1, wx1, wy0 - 0.1, wy1 + 0.1, G + 9.9, G + 10.15,
        sides=("t", "n", "s", "w"))
    front_row(w, "+y", wy1, (-40.5, -36.5, -32.5, -28.5), G + 1.0, 0.9, 1.6, green)
    front_row(w, "+y", wy1, (-40.5, -36.5, -32.5, -28.5), G + 4.4, 0.9, 1.6, green)
    front_row(w, "+y", wy1, (-40.5, -36.5, -32.5, -28.5), G + 7.6, 0.9, 1.5, green)


# ===========================================================================
# E2  12-16 Main (east side, front faces -X at x 10.6)
# ===========================================================================
def build_e2():
    p = "E2"
    x0, x1, y0, y1 = fp(10.6, 28.4, -192.4, -179.7)            # y 179.7 .. 192.4
    top = G + 10.4
    box(p, "clap", x0, x1, y0, y1, 0.0, top - 0.5, sides=("n", "s", "e", "w"))
    box(p, "sw:paint_white", x0 - 0.35, x1 + 0.1, y0 - 0.35, y1 + 0.35, top - 0.5, top,
        sides=("t", "n", "s", "e", "w", "b"), top="sw:tin_dark")
    foundation(p, x0, x1, y0, y1, G + 0.45, ("w", "s", "n"), mat="concrete")
    ys = (181.3, 184.5, 187.7, 190.8)
    window(p, cream(), "-x", (x0, ys[0], G + 1.1), 1.0, 1.9)
    window(p, "door_green", "-x", (x0, ys[1], G + 0.45), 1.1, 2.3)
    window(p, "door_brown", "-x", (x0, ys[2], G + 0.45), 1.0, 2.3)
    window(p, cream(), "-x", (x0, ys[3], G + 1.1), 1.0, 1.9)
    front_row(p, "-x", x0, list(ys), G + 4.3, 0.95, 1.8, cream)
    front_row(p, "-x", x0, list(ys), G + 7.6, 0.95, 1.7, cream)
    front_row(p, "-y", y0, (13.2, 17.0, 20.8, 24.6), G + 7.6, 0.9, 1.6, cream)
    front_row(p, "+y", y1, (13.2, 17.0, 20.8, 24.6), G + 4.3, 0.9, 1.7, cream)
    front_row(p, "+y", y1, (13.2, 17.0, 20.8, 24.6), G + 7.6, 0.9, 1.6, cream)
    porch_x(p, x0, 8.9, 179.9, 192.2, [G + 0.45, G + 3.95], G + 7.0, 5, rails=(1,), stairs=())
    for st in (ys[1], ys[2]):
        box(p, "concrete", 8.3, 8.9, -0 + st - 0.7, st + 0.7, 0.0, G + 0.25, sides=("t", "w", "n", "s"))


# ===========================================================================
# E3, E4  18 and 20-22 Main (2-storey frame Italianate, front gables, fronts face -X)
# ===========================================================================
def build_e3_e4():
    p = "E3"
    x0, x1, y0, y1 = fp(10.6, 25.3, -177.8, -171.3)            # y 171.3 .. 177.8
    eave = G + 6.3
    rise = (y1 - y0) / 2 * TAN(24)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.6, og=0.55)
    foundation(p, x0, x1, y0, y1, G + 0.55, ("w", "s", "n"), mat="concrete")
    chimney(p, 21.0, (y0 + y1) / 2, eave + rise - 0.6, eave + rise + 0.9)
    porch_x(p, x0, 9.3, y0 + 0.1, y1 - 0.1, [G + 0.55], G + 3.5, 3, rails=(0,), stairs=(176.4,))
    window(p, "door_brown", "-x", (x0, 176.4, G + 0.55), 1.0, 2.2)
    front_row(p, "-x", x0, (172.6, 174.4), G + 1.3, 0.9, 1.7, cream)
    front_row(p, "-x", x0, (172.6, 174.55, 176.5), G + 4.0, 0.9, 1.6, cream)
    window(p, "attic_window", "-x", (x0, (y0 + y1) / 2, eave + 0.2), 0.7, 0.75)
    front_row(p, "-y", y0, (14.0, 18.0, 22.0), G + 4.0, 0.9, 1.6, cream)
    front_row(p, "+y", y1, (14.0, 18.0, 22.0), G + 4.0, 0.9, 1.6, cream)
    q = "E4"
    x0, x1, y0, y1 = fp(8.4, 18.4, -171.2, -166.7)             # y 166.7 .. 171.2
    eave = G + 6.0
    rise = (y1 - y0) / 2 * TAN(24)
    gable_walls(q, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(q, x0, x1, y0, y1, eave, rise, "x", oe=0.6, og=0.55)
    foundation(q, x0, x1, y0, y1, G + 0.4, ("s", "n"), mat="concrete")
    chimney(q, 15.5, (y0 + y1) / 2, eave + rise - 0.5, eave + rise + 0.8)
    # canted 2-storey bay (shop window below, the "hanging oriel" above), flat roof
    bay = [(8.4, 167.15), (7.45, 167.85), (7.45, 170.05), (8.4, 170.75)]
    zt = G + 5.75
    for (ax, ay), (bx, by) in zip(bay, bay[1:]):
        nrm = Vector((-(by - ay), bx - ax, 0)).normalized()
        if nrm.x > 0:
            nrm = -nrm
        face_out(q, "clap", [(ax, ay, 0.0), (bx, by, 0.0), (bx, by, zt), (ax, ay, zt)], nrm)
    slab(q, "sw:tin_dark", "sw:paint_white", [(8.4, 167.0, zt), (7.3, 167.8, zt), (7.3, 170.1, zt),
                                              (8.4, 170.9, zt)], 0.15)
    box(q, "sw:wood_grey", 7.4, 8.4, 167.4, 170.4, G + 3.1, G + 3.35, sides=("w",))
    window(q, "door_green", "-x", (7.45, 168.95, G + 0.15), 1.0, 2.3)
    window(q, green(), "-x", (7.45, 167.95, G + 0.9), 0.6, 1.9)
    window(q, green(), "-x", (7.45, 169.95, G + 0.9), 0.6, 1.9)
    front_row(q, "-x", 7.45, (168.4, 169.5), G + 3.7, 0.85, 1.6, cream)
    front_row(q, "-y", y0, (11.5, 14.5), G + 3.9, 0.9, 1.6, cream)
    window(q, "attic_window", "-x", (x0, (y0 + y1) / 2, eave + 0.15), 0.6, 0.6)


# ===========================================================================
# E5  Vosseller Building 108-112 Main (front faces -X at x 9.3)
# ===========================================================================
def build_e5():
    p = "E5"
    x0, x1, y0, y1 = fp(9.3, 31.5, 69.0, 85.8)                 # y -85.8 .. -69.0
    top = G + 11.9
    box(p, "brick", x0, x1, y0, y1, 0.0, top - 0.6, sides=("n", "s", "e", "w"))
    box(p, "sw:wood_grey", x0 - 0.45, x1 + 0.05, y0 - 0.1, y1 + 0.45, top - 0.6, top,
        sides=("t", "n", "s", "e", "w", "b"), top="sw:tin_dark")
    box(p, "sw:wood_grey", x0 - 0.18, x0, y0 + 0.1, y1 - 0.1, G + 3.45, G + 3.8, sides=("w", "t", "b", "n", "s"))
    # three shop fronts: door between two display windows each
    for yc in (-83.0, -77.4, -71.8):
        window(p, "door_green" if yc != -77.4 else "door_brown", "-x", (x0, yc, G + 0.1), 1.0, 2.5)
        for d in (-1.55, 1.55):
            window(p, green(), "-x", (x0, yc + d, G + 0.65), 1.9, 2.5)
        box(p, "sw:wood_grey", x0 - 0.06, x0, yc - 2.6, yc + 2.6, 0.0, G + 0.65, sides=("w", "t"))
    ys = [-84.4 + 2.86 * i for i in range(6)]
    for z, h in ((G + 4.55, 1.9), (G + 8.0, 1.75)):
        front_row(p, "-x", x0, list(ys), z, 0.95, h, green)
        for a in ys:
            sill_lintel(p, "-x", x0, a, z, 0.95, h)
    xs = (11.6, 14.6, 17.6, 20.6, 23.6, 26.6, 29.4)
    for z, h in ((G + 4.55, 1.8), (G + 8.0, 1.7)):
        front_row(p, "+y", y1, xs, z, 0.95, h, green)
        for a in xs:
            lintel(p, "+y", y1, a, z + h, 0.95)
    front_row(p, "+y", y1, (14.6, 20.6, 26.6), G + 0.9, 1.0, 2.0, green)
    window(p, "door_brown", "+y", (29.6, y1, G + 0.05), 1.0, 2.3)
    # second-storey porch across the front: deck on diagonal braces, thin posts, shallow roof
    ys_p = porch_x(p, x0, 8.2, y0 + 0.2, y1 - 0.2, [G + 4.0], G + 7.45, 6, rails=(0,), post=0.13)
    for y in ys_p:
        beam(p, "sw:wood_grey", (x0, y, G + 2.65), (8.35, y, G + 3.78), 0.11)


# ===========================================================================
# E6  Doric House 114 Main (front faces -X at x 16.0; portico to x 14.2)
# ===========================================================================
def build_e6():
    p = "E6"
    x0, x1, y0, y1 = fp(16.0, 27.8, 92.4, 100.5)               # y -100.5 .. -92.4
    xp = 14.2                                                  # portico front
    fl = G + 0.45
    e0, e1 = G + 7.0, G + 8.4
    box(p, "clap", x0, x1, y0, y1, 0.0, e0, sides=("n", "s", "e", "w"))
    foundation(p, x0, x1, y0, y1, fl, ("w", "n", "s"), mat="concrete")
    box(p, "sw:paint_white", xp - 0.02, x1 + 0.1, y0 - 0.1, y1 + 0.1, e0, e1, sides=("w", "n", "s", "e", "b"))
    box(p, "sw:paint_white", xp - 0.1, x1 + 0.14, y0 - 0.14, y1 + 0.14, e0, e0 + 0.42,
        sides=("w", "n", "s", "e", "b"))                                           # architrave
    box(p, "sw:paint_white", xp - 0.38, x1 + 0.38, y0 - 0.38, y1 + 0.38, e1, e1 + 0.36,
        sides=("t", "w", "n", "s", "e", "b"), top="sw:tin_dark")                  # cornice, flat roof
    for yc in (-98.9, -96.45, -93.98):                                             # cast-iron frieze grilles
        window(p, "iron_dark", "-x", (xp - 0.02, yc, e0 + 0.55), 0.95, 0.5, off=0.012)
    # portico floor and steps
    box(p, "concrete", xp, x0, y0, y1, 0.0, fl, sides=("t", "w", "n", "s"))
    box(p, "concrete", 13.45, xp, -99.85, -97.95, 0.0, G + 0.22, sides=("t", "w", "n", "s"))
    # four square panelled piers and two antae
    piers = (y0 + 0.36, -97.68, -95.22, y1 - 0.36)
    for yc in piers:
        box(p, "sw:paint_white", xp, xp + 0.72, yc - 0.36, yc + 0.36, fl + 0.3, e0 - 0.3, sides=("n", "s", "w"))
        box(p, "sw:paint_white", xp - 0.08, xp + 0.8, yc - 0.44, yc + 0.44, e0 - 0.3, e0, sides=("n", "s", "w", "b"))
        box(p, "sw:paint_white", xp - 0.08, xp + 0.8, yc - 0.44, yc + 0.44, fl, fl + 0.3, sides=("n", "s", "w", "t"))
        hh = e0 - 0.3 - fl - 1.0
        window("E6N", "paint_white_s", "-x", (xp, yc, fl + 0.65), 0.42, hh, off=0.008)
        window("E6N", "paint_white_s", "-y", (xp + 0.36, yc - 0.36, fl + 0.65), 0.42, hh, off=0.008)
        window("E6N", "paint_white_s", "+y", (xp + 0.36, yc + 0.36, fl + 0.65), 0.42, hh, off=0.008)
    for yc in (y0 + 0.36, y1 - 0.36):
        box(p, "sw:paint_white", x0 - 0.14, x0, yc - 0.32, yc + 0.32, fl, e0, sides=("w", "n", "s"))
    # front: door in the right-hand (south) bay with a cornice head, windows with dark shutters
    window(p, "door_green", "-x", (x0, -98.9, fl), 1.05, 2.45)
    box(p, "sw:paint_white", x0 - 0.1, x0, -99.75, -98.05, fl + 2.45, fl + 2.8, sides=("w", "t", "b", "n", "s"))
    for yc in (-99.55, -98.25):
        box(p, "sw:paint_white", x0 - 0.06, x0, yc - 0.1, yc + 0.1, fl, fl + 2.45, sides=("w", "n", "s"))
    for yc, z, h in ((-96.45, fl + 0.55, 2.0), (-93.98, fl + 0.55, 2.0), (-98.9, G + 3.95, 1.8),
                     (-96.45, G + 3.95, 1.8), (-93.98, G + 3.95, 1.8)):
        window(p, cream(), "-x", (x0, yc, z), 0.95, h)
        for d in (-0.78, 0.78):
            window(p, "paint_green_s", "-x", (x0, yc + d, z), 0.5, h, off=0.02)
    # sides: north (Higgins side) and south
    front_row(p, "+y", y1, (18.1,), fl + 0.6, 0.9, 1.9, cream)
    front_row(p, "+y", y1, (18.1,), G + 3.95, 0.9, 1.7, cream)
    front_row(p, "-y", y0, (18.4, 21.9, 25.3), fl + 0.6, 0.9, 1.9, cream)
    front_row(p, "-y", y0, (18.4, 21.9, 25.3), G + 3.95, 0.9, 1.7, cream)
    for yc in (y0 + 0.45, y1 - 0.45):
        chimney(p, 21.9, yc, e1 - 0.2, e1 + 1.5)
    # 2-storey north wing
    w = "E6W"
    box(w, "clap", 20.3, 27.7, -92.4, -89.4, 0.0, G + 6.3, sides=("n", "e", "w"))
    box(w, "sw:paint_white", 20.2, 27.8, -92.4, -89.3, G + 6.3, G + 6.6, sides=("t", "n", "e", "w"))
    front_row(w, "+y", -89.4, (22.2, 25.6), G + 1.1, 0.9, 1.8, cream)
    front_row(w, "+y", -89.4, (22.2, 25.6), G + 3.9, 0.9, 1.6, cream)
    # cast-iron fence on a stone curb along the street line, gate at the path
    f = "E6F"
    for za, zb in ((86.3, 98.4), (99.4, 106.3)):
        sbox(f, "concrete", 9.35, 9.6, za, zb, 0.0, G + 0.25, sides=("t", "w", "e", "n", "s"))
        rail_quad(f, (9.47, -za), (9.47, -zb), G + 0.25, 0.85, both=True, tile=1.4)
        for zz in (za, zb):
            sbox(f, "sw:iron_dark", 9.4, 9.55, zz - 0.075, zz + 0.075, G + 0.25, G + 1.25,
                 sides=("t", "n", "s", "e", "w"))


# ===========================================================================
# E7  Methodist Episcopal Church 116 Main (west gable faces -X at x 15.9)
# ===========================================================================
def tracery_window(part, n, c, cu, w, v0, vs, rose_r=None, depth=0.35, mullions=3):
    """recessed pointed window: reveal + dark glass back face + pale mullions, transom and rose"""
    out = arch2d(cu, w, v0, vs, "pointed", n=5, rf=0.9)
    cb = c - depth if n[0] == "+" else c + depth
    # (the wall face with this hole is made by the caller with wall_holes)
    wall_poly(part + "G", "sw:iron_dark", n, cb, out, off=0.0)
    for k in range(1, mullions + 1):
        u = cu - w / 2 + w * k / (mullions + 1)
        wall_poly(part + "T", "sw:stone_cream", n, cb, [(u - 0.06, v0), (u + 0.06, v0), (u + 0.06, vs + 0.15),
                                                        (u - 0.06, vs + 0.15)], off=0.02)
    tv = v0 + (vs - v0) * 0.55
    wall_poly(part + "T", "sw:stone_cream", n, cb, [(cu - w / 2, tv), (cu + w / 2, tv), (cu + w / 2, tv + 0.12),
                                                    (cu - w / 2, tv + 0.12)], off=0.02)
    if rose_r:
        R = arch2d(cu, w, v0, vs, "pointed", n=5, rf=0.9)
        apex = max(p[1] for p in R)
        cv = vs + (apex - vs) * 0.42
        ro = circle2d(cu, cv, rose_r, 16)
        ri = circle2d(cu, cv, rose_r * 0.8, 16)
        for k in range(16):
            wall_poly(part + "T", "sw:stone_cream", n, cb,
                      [ro[k], ro[(k + 1) % 16], ri[(k + 1) % 16], ri[k]], off=0.03)
        wall_poly(part + "T", "sw:stone_cream", n, cb, circle2d(cu, cv, rose_r * 0.3, 8), off=0.03)
        for k in range(4):                                     # four spokes (plate tracery)
            a = math.pi / 4 + k * math.pi / 2
            cs, sn = math.cos(a), math.sin(a)
            r0, r1 = rose_r * 0.3, rose_r * 0.8
            q = lambda r, t: (cu + r * cs - t * sn, cv + r * sn + t * cs)
            wall_poly(part + "T", "sw:stone_cream", n, cb, [q(r0, -0.07), q(r1, -0.07), q(r1, 0.07), q(r0, 0.07)],
                      off=0.03)
    return out


def build_e7():
    p = "E7"
    eave = G + 5.6
    pitch = 48
    ax0, ax1, ay0, ay1 = 15.9, 38.0, -119.0, -106.8          # auditorium, E-W ridge, west gable
    ewr = (ay1 - ay0) / 2 * TAN(pitch)
    sx0, sx1, sy0 = 21.9, 33.3, -123.7                       # south gable block, N-S ridge
    nsr = (sx1 - sx0) / 2 * TAN(pitch)
    # west gable (faces Main St) with the big traceried window and rose
    hole = tracery_window(p, "-x", ax0, -ay0 - (ay1 - ay0) / 2 + 0.0, 4.0, G + 1.9, G + 6.0, rose_r=1.05)
    wall_holes(p, "block", "-x", ax0, gable2d(-ay1, -ay0, eave, eave + ewr), [hole], depth=0.35)
    # ivy over the lower north half of the west gable (1909 colour card)
    # (jagged outlines kept under the gable's roof line and clear of the window)
    ivy = [(106.8, 0.2), (110.6, 0.2), (110.85, 0.9), (110.5, 1.7), (110.75, 2.8), (110.55, 4.2), (110.8, 5.4),
           (110.3, 6.4), (110.0, 8.0), (109.6, 8.6), (109.0, 8.1), (108.4, 7.25), (107.7, 6.6), (107.2, 6.0),
           (106.8, 5.4)]
    wall_poly("E7I", "sw:paint_green_s", "-x", ax0, ivy, off=0.05)
    wall_poly("E7I", "sw:paint_green_s", "-x", ax0, [(116.6, 0.2), (119.0, 0.2), (119.0, 2.6), (118.5, 3.0),
                                                    (118.0, 2.3), (117.4, 2.7), (116.9, 1.6)], off=0.05)
    # north wall (towards the Doric House) with three plain pointed windows, north gable of the
    # cross block
    face_out(p, "block", [(ax0, ay1, 0.0), (ax1, ay1, 0.0), (ax1, ay1, eave), (ax0, ay1, eave)], (0, 1, 0))
    face_out(p, "block", [(sx0, ay1, eave), (sx1, ay1, eave), ((sx0 + sx1) / 2, ay1, eave + nsr)], (0, 1, 0))
    for xc in (18.7, 27.6, 35.4):
        wall_poly(p + "G", "sw:iron_dark", "+y", ay1, arch2d(-xc, 1.4, G + 1.6, G + 4.0, "pointed", 3), off=0.03)
    wall_poly(p + "G", "sw:iron_dark", "+y", ay1, circle2d(-27.6, eave + nsr * 0.45, 0.6, 10), off=0.03)
    # the bit of the auditorium's south wall west of the tower
    face_out(p, "block", [(ax0, ay0, 0.0), (17.6, ay0, 0.0), (17.6, ay0, eave), (ax0, ay0, eave)], (0, -1, 0))
    # south gable (faces Maple Ave)
    hole = tracery_window(p, "-y", sy0, (sx0 + sx1) / 2, 3.8, G + 1.9, G + 6.0, rose_r=1.0)
    wall_holes(p, "block", "-y", sy0, gable2d(sx0, sx1, eave, eave + nsr), [hole], depth=0.35)
    # roofs (slate), crossing
    gable_roof(p, ax0, ax1 + 0.4, ay0, ay1, eave, ewr, "x", oe=0.35, og=0.4, t=0.15)
    gable_roof(p, sx0, sx1, sy0, ay1, eave, nsr, "y", oe=0.35, og=0.4, t=0.15)
    # basement band, paler dressed stone
    b = "E7B"
    box(b, "block", ax0 - 0.07, ax1, ay0, ay1 + 0.07, 0.0, G + 0.75, sides=("w", "n"))
    box(b, "block", sx0, sx1, sy0 - 0.07, sy0, 0.0, G + 0.75, sides=("s",))
    for yy, zz in ((ay1 - 0.01, eave - 0.25), ):
        box(b, "block", ax0 - 0.06, ax1, ay1, ay1 + 0.06, zz, zz + 0.25, sides=("n", "t", "b"))
    # SW tower: door, small window, paired louvred lancets, corbel band, pinnacles, spire
    t = "E7S"
    tx0, tx1, ty0, ty1 = 17.6, 21.9, sy0, ay0
    ttop = G + 11.6
    door = arch2d(-(ty0 + ty1) / 2, 1.5, G + 0.6, G + 2.7, "pointed", 4)
    wall_holes(t, "block", "-x", tx0, [(-ty1, 0.0), (-ty0, 0.0), (-ty0, ttop), (-ty1, ttop)], [door], depth=0.4,
               back=(t, "door_brown"))
    box(t, "block", tx0, tx1, ty0, ty1, 0.0, ttop, sides=("s", "e", "n"))
    box(b, "block", tx0 - 0.07, tx1, ty0 - 0.07, ty1, 0.0, G + 0.75, sides=("s",))
    wall_poly(t + "G", "sw:iron_dark", "-x", tx0, arch2d(-(ty0 + ty1) / 2, 0.6, G + 4.6, G + 5.5, "pointed", 3))
    wall_poly(t + "G", "sw:iron_dark", "-y", ty0, arch2d((tx0 + tx1) / 2, 0.6, G + 4.6, G + 5.5, "pointed", 3))
    cy = (ty0 + ty1) / 2
    cx = (tx0 + tx1) / 2
    for n, c, cu in (("-x", tx0, -cy), ("+x", tx1, cy), ("-y", ty0, cx), ("+y", ty1, -cx)):
        for d in (-0.62, 0.62):
            wall_poly(t + "G", None, n, c, arch2d(cu + d, 0.56, G + 7.9, G + 10.3, "pointed", 3), cell="barn_doors")
    box(t, "block", tx0 - 0.16, tx1 + 0.16, ty0 - 0.16, ty1 + 0.16, ttop, ttop + 0.55,
        sides=("t", "n", "s", "e", "w", "b"))
    zb = ttop + 0.55
    oct_ = ring(cx, cy, 2.05, 8, zb, rot=math.pi / 8)
    pyramid(t, "slate", oct_, Vector((cx, cy, G + 19.0)))
    for sx in (tx0 + 0.1, tx1 - 0.1):
        for sy in (ty0 + 0.1, ty1 - 0.1):
            box(t, "block", sx - 0.24, sx + 0.24, sy - 0.24, sy + 0.24, zb, zb + 1.0, sides=("n", "s", "e", "w"))
            pyramid(t, "block", [Vector((sx - 0.27, sy - 0.27, zb + 1.0)), Vector((sx + 0.27, sy - 0.27, zb + 1.0)),
                                 Vector((sx + 0.27, sy + 0.27, zb + 1.0)), Vector((sx - 0.27, sy + 0.27, zb + 1.0))],
                    Vector((sx, sy, zb + 2.3)))
    cross(t, cx, cy, G + 18.9, h=0.9, w=0.45, t=0.08)
    cross(p, ax0 - 0.2, (ay0 + ay1) / 2, eave + ewr - 0.05, h=1.0, axis="y")
    cross(p, (sx0 + sx1) / 2, sy0 - 0.2, eave + nsr - 0.05, h=1.0)
    for k, (dy, h) in enumerate(((1.5, G + 0.2), (1.0, G + 0.4), (0.5, G + 0.6))):
        box(t, "concrete", tx0 - dy, tx0, cy - 1.1, cy + 1.1, 0.0, h, sides=("t", "w", "n", "s"))
    # squat "24'" tower with a pyramid roof and its doorway
    q = "E7Q"
    qx0, qx1 = 33.3, 37.7
    box(q, "block", qx0, qx1, sy0, ay0, 0.0, G + 7.3, sides=("s", "e"))
    hip_roof(q, "slate", qx0, qx1, sy0, ay0, G + 7.3, 2.6, oe=0.3)
    wall_poly(q + "G", None, "-y", sy0, arch2d(35.5, 1.3, G + 0.3, G + 2.3, "round", 3), cell="door_brown")
    front_row(q, "-y", sy0, (34.6, 36.4), G + 5.0, 0.45, 1.0, ["small_window"])
    box(b, "block", qx0, qx1 + 0.07, sy0 - 0.07, ay0, 0.0, G + 0.75, sides=("s", "e"))
    # rear chapel (Sunday school): canted east end, hipped roof; lower south range
    c = "E7C"
    ce = G + 4.6
    box(c, "block", ax1, 49.2, ay0, ay1, 0.0, ce, sides=("n",))
    cant = [(49.2, ay1), (51.3, -109.6), (51.3, -116.2), (49.2, ay0)]
    for (ax, ay), (bx, by) in zip(cant, cant[1:]):
        face_out(c, "block", [(ax, ay, 0.0), (bx, by, 0.0), (bx, by, ce), (ax, ay, ce)],
                 (bx + ax - 2 * 49.0, by + ay - 2 * (-112.9), 0))
    hip_roof(c, "slate", ax1, 51.3, ay0, ay1, ce, 3.4, oe=0.35)
    for xc in (40.5, 44.0, 47.2):
        wall_poly(c + "G", "sw:iron_dark", "+y", ay1, arch2d(-xc, 1.0, G + 1.4, G + 3.3, "pointed", 3))
    wall_poly(c + "G", "sw:iron_dark", "+x", 51.3, arch2d(-112.9, 1.1, G + 1.4, G + 3.3, "pointed", 3))
    r = "E7R"
    shed(r, "block", "slate", 37.7, 51.5, sy0, ay0, G + 4.3, G + 3.4, "s", oe=0.25)
    for xc in (40.4, 43.8, 47.3):
        wall_poly(r + "G", "sw:iron_dark", "-y", sy0, arch2d(xc, 0.9, G + 1.0, G + 2.4, "pointed", 3))
    window(r, "door_brown", "-y", (50.0, sy0, G + 0.2), 1.0, 2.2)
    # lamp post at the walk in front of the tower (1906 card)
    lp = "E7L"
    sbox(lp, "sw:iron_dark", 7.15, 7.27, 121.2, 121.32, G, G + 3.3, sides=("n", "s", "e", "w"))
    sbox(lp, "sw:iron_dark", 7.0, 7.42, 121.05, 121.47, G + 3.3, G + 3.85, sides=("t", "b", "n", "s", "e", "w"))


# ===========================================================================
# E8  First Presbyterian Church, built in a local frame (front at local Y 357 facing -Y,
#     X = 4.4 + a along the front), then turned 9.3 deg to follow N Main St
# ===========================================================================
E8_PIVOT = Vector((4.4, 357.0, 0.0))
E8_ANGLE = -math.atan2(5.0, 30.5)


def build_e8():
    p = "E8"
    stone = "block"
    # --- tower, local a 0.2..6.2, b 6..12 ---
    tx0, tx1, ty0, ty1 = 4.6, 10.6, 363.0, 369.0
    ttop = G + 20.0
    door = arch2d(7.6, 1.8, G + 0.25, G + 2.8, "pointed", 4)
    wall_holes(p, stone, "-y", ty0, [(tx0, 0.0), (tx1, 0.0), (tx1, ttop), (tx0, ttop)], [door], depth=0.45,
               back=(p, "door_brown"))
    box(p, stone, tx0, tx1, ty0, ty1, 0.0, ttop, sides=("n", "e", "w"))
    wall_poly(p + "G", "sw:iron_dark", "-y", ty0, circle2d(7.6, G + 7.2, 0.55, 10))
    wall_poly(p + "G", "sw:iron_dark", "-x", tx0, arch2d(-366.0, 0.7, G + 6.0, G + 7.4, "pointed", 3))
    cx, cy = (tx0 + tx1) / 2, (ty0 + ty1) / 2
    for n, c, cu in (("-x", tx0, -cy), ("+x", tx1, cy), ("-y", ty0, cx), ("+y", ty1, -cx)):
        for d in (-0.85, 0.85):
            wall_poly(p + "G", None, n, c, arch2d(cu + d, 0.75, G + 15.6, G + 18.4, "pointed", 3), cell="barn_doors")
        wall_poly(p + "G", "sw:iron_dark", n, c, arch2d(cu, 0.45, G + 11.0, G + 12.2, "pointed", 3))
    box(p, stone, tx0 - 0.15, tx1 + 0.15, ty0 - 0.15, ty1 + 0.15, ttop, ttop + 0.5,
        sides=("t", "n", "s", "e", "w", "b"))
    # --- broach spire to 33.5 m with four gabled lucarnes and a vane ---
    s = "E8S"
    z0, ztip = ttop + 0.5, G + 33.35
    ap = 3.15                                                   # apothem = half the corbel
    R = ap / math.cos(math.pi / 8)
    octv = ring(cx, cy, R, 8, z0, rot=math.pi / 8)
    apex = Vector((cx, cy, ztip))
    pyramid(s, "slate", octv, apex)
    for k in range(4):                                          # broaches at the square corners
        ang = math.pi / 4 + k * math.pi / 2
        corner = Vector((cx + ap * math.sqrt(2) * math.cos(ang), cy + ap * math.sqrt(2) * math.sin(ang), z0))
        mid = Vector((cx + ap * math.cos(ang), cy + ap * math.sin(ang), z0))
        pb = mid + (apex - mid) * 0.2
        va = min(octv, key=lambda v: (v - corner).length)
        vb = sorted(octv, key=lambda v: (v - corner).length)[1]
        for a_, b_ in ((va, pb), (pb, vb)):
            face_out(s, "slate", [corner, a_, b_], (corner - Vector((cx, cy, z0))) + UP * 0.6)
    hl = z0 + 4.2
    for k in range(4):                                          # lucarnes on the cardinal faces
        ang = k * math.pi / 2
        d = Vector((math.cos(ang), math.sin(ang), 0))
        side = Vector((-d.y, d.x, 0))
        rf = ap * (1 - (hl - z0) / (ztip - z0)) + 0.35
        rb = rf - 1.0
        f0 = Vector((cx, cy, 0)) + d * rf
        b0 = Vector((cx, cy, 0)) + d * rb
        w2, wh, gh = 0.34, 0.6, 0.45
        front = [f0 + side * -w2 + UP * hl, f0 + side * w2 + UP * hl, f0 + side * w2 + UP * (hl + wh),
                 f0 + UP * (hl + wh + gh), f0 + side * -w2 + UP * (hl + wh)]
        face_out(s, "slate", front, d)
        for sg in (-1, 1):
            face_out(s, "slate", [f0 + side * sg * w2 + UP * hl, b0 + side * sg * w2 + UP * hl,
                                  b0 + side * sg * w2 + UP * (hl + wh), f0 + side * sg * w2 + UP * (hl + wh)], side * sg)
            face_out(s, "slate", [f0 + side * sg * (w2 + 0.08) + UP * (hl + wh - 0.06), b0 + side * sg * (w2 + 0.08) + UP * (hl + wh - 0.06),
                                  b0 + UP * (hl + wh + gh + 0.04), f0 + d * 0.08 + UP * (hl + wh + gh + 0.04)],
                     side * sg + UP)
        opening = [f0 + d * 0.01 + side * -0.17 + UP * (hl + 0.1), f0 + d * 0.01 + side * 0.17 + UP * (hl + 0.1),
                   f0 + d * 0.01 + side * 0.17 + UP * (hl + 0.6), f0 + d * 0.01 + UP * (hl + 0.8),
                   f0 + d * 0.01 + side * -0.17 + UP * (hl + 0.6)]
        face_out(s + "G", "sw:iron_dark", opening, d)
    box(s, "sw:iron_dark", cx - 0.035, cx + 0.035, cy - 0.035, cy + 0.035, ztip - 0.1, ztip + 1.3,
        sides=("n", "s", "e", "w", "t"))
    box(s, "sw:iron_dark", cx - 0.5, cx + 0.5, cy - 0.025, cy + 0.025, ztip + 0.95, ztip + 1.05,
        sides=("n", "s", "e", "w", "t", "b"))
    # --- nave, gable to the south with the rose window ---
    n0, n1, ny0, ny1 = 10.6, 25.4, 363.0, 390.0
    ne = G + 6.0
    nr = (n1 - n0) / 2 * TAN(50)
    rose = circle2d((n0 + n1) / 2, G + 9.7, 1.75, 16)
    wall_holes(p, stone, "-y", ny0, gable2d(n0, n1, ne, ne + nr), [rose], depth=0.35)
    wall_poly(p + "G", "sw:iron_dark", "-y", ny0 + 0.35, rose, off=0.0)
    ri = circle2d((n0 + n1) / 2, G + 9.7, 1.3, 16)
    ro = circle2d((n0 + n1) / 2, G + 9.7, 1.45, 16)
    for k in range(16):
        wall_poly(p + "T", "sw:stone_cream", "-y", ny0 + 0.35, [ro[k], ro[(k + 1) % 16], ri[(k + 1) % 16], ri[k]],
                  off=0.03)
    for k in range(6):
        a = k * math.pi / 3
        cs, sn = math.cos(a), math.sin(a)
        cu, cv = (n0 + n1) / 2, G + 9.7
        q = lambda r, t: (cu + r * cs - t * sn, cv + r * sn + t * cs)
        wall_poly(p + "T", "sw:stone_cream", "-y", ny0 + 0.35, [q(0.25, -0.07), q(1.3, -0.07), q(1.3, 0.07),
                                                                 q(0.25, 0.07)], off=0.03)
    face_out(p, stone, [(n0, ny1, 0.0), (n0, ny0, 0.0), (n0, ny0, ne), (n0, ny1, ne)], (-1, 0, 0))
    face_out(p, stone, [(n1, ny0, 0.0), (n1, ny1, 0.0), (n1, ny1, ne), (n1, ny0, ne)], (1, 0, 0))
    face_out(p, stone, [(n0, ny1, ne), (n1, ny1, ne), ((n0 + n1) / 2, ny1, ne + nr)], (0, 1, 0))
    for yc in (372.5, 377.5, 382.5, 387.0):
        wall_poly(p + "G", "sw:iron_dark", "-x", n0, arch2d(-yc, 1.15, G + 1.8, G + 4.4, "pointed", 3))
    gable_roof(p, n0, n1, ny0, ny1, ne, nr, "y", oe=0.35, og=0.4, t=0.16)
    cross(p, (n0 + n1) / 2, ny0 - 0.25, ne + nr - 0.05, h=1.1)
    # --- low front range (lean-to) with five round-headed windows ---
    f = "E8F"
    shed(f, stone, "slate", n0, 21.8, 357.0, ny0, G + 5.3, G + 3.4, "s", oe=0.3)
    for xc in (12.3, 14.3, 16.3, 18.3, 20.3):
        wall_poly(f + "G", None, "-y", 357.0, arch2d(xc, 0.75, G + 1.1, G + 2.6, "round", 3), cell=green())
    wall_poly(f + "G", None, "-x", n0, arch2d(-360.0, 0.75, G + 1.1, G + 2.6, "round", 3), cell=green())
    # --- gabled entrance porch ---
    e = "E8P"
    px0, px1, py0 = 21.8, 25.4, 356.4
    pr = (px1 - px0) / 2 * TAN(55)
    door = arch2d((px0 + px1) / 2, 1.5, G + 0.3, G + 2.3, "pointed", 4)
    wall_holes(e, stone, "-y", py0, gable2d(px0, px1, G + 3.4, G + 3.4 + pr), [door], depth=0.4,
               back=(e, "door_brown"))
    face_out(e, stone, [(px0, ny0, 0.0), (px0, py0, 0.0), (px0, py0, G + 3.4), (px0, ny0, G + 3.4)], (-1, 0, 0))
    gable_roof(e, px0, px1, py0, ny0, G + 3.4, pr, "y", oe=0.2, og=0.25)
    for k, (dy, h) in enumerate(((1.2, G + 0.1), (0.8, G + 0.2), (0.4, G + 0.3))):
        box(e, "concrete", 22.6, 24.6, py0 - dy, py0, 0.0, h, sides=("t", "s", "e", "w"))
    cross(e, (px0 + px1) / 2, py0 - 0.2, G + 3.4 + pr - 0.05, h=0.7, w=0.36, t=0.07)
    # --- east wing, gable to the south ---
    w = "E8W"
    w0, w1, wy0, wy1 = 25.4, 34.9, 359.0, 383.0
    we = G + 5.5
    wr = (w1 - w0) / 2 * TAN(50)
    win = arch2d((w0 + w1) / 2, 2.6, G + 1.5, G + 4.4, "pointed", 4)
    wall_holes(w, stone, "-y", wy0, gable2d(w0, w1, we, we + wr), [win], depth=0.3)
    wall_poly(w + "G", "sw:iron_dark", "-y", wy0 + 0.3, win, off=0.0)
    for k in (1, 2):
        u = w0 + 3.45 + 0.85 * k
        u = (w0 + w1) / 2 - 1.3 + 2.6 * k / 3
        wall_poly(w + "T", "sw:stone_cream", "-y", wy0 + 0.3, [(u - 0.06, G + 1.5), (u + 0.06, G + 1.5),
                                                                (u + 0.06, G + 4.6), (u - 0.06, G + 4.6)], off=0.02)
    face_out(w, stone, [(w1, wy0, 0.0), (w1, wy1, 0.0), (w1, wy1, we), (w1, wy0, we)], (1, 0, 0))
    face_out(w, stone, [(w0, wy0, 0.0), (w0, ny0, 0.0), (w0, ny0, we), (w0, wy0, we)], (-1, 0, 0))
    face_out(w, stone, [(w0, wy1, 0.0), (w1, wy1, 0.0), (w1, wy1, we), (w0, wy1, we)], (0, 1, 0))
    face_out(w, stone, [(w0, wy1, we), (w1, wy1, we), ((w0 + w1) / 2, wy1, we + wr)], (0, 1, 0))
    for yc in (364.0, 369.0, 374.0, 379.0):
        wall_poly(w + "G", "sw:iron_dark", "+x", w1, arch2d(yc, 1.1, G + 1.6, G + 3.9, "pointed", 3))
    gable_roof(w, w0, w1, wy0, wy1, we, wr, "y", oe=0.3, og=0.35, t=0.15)
    # --- hipped chapel behind, large stone chimney ---
    c = "E8C"
    c0, c1, cy0, cy1 = 7.4, 32.4, 390.0, 406.0
    ce = G + 5.0
    box(c, stone, c0, c1, cy0, cy1, 0.0, ce, sides=("n", "s", "e", "w"))
    hip_roof(c, "slate", c0, c1, cy0, cy1, ce, 4.2, oe=0.4)
    for xc in (9.0, 28.0, 30.8):
        wall_poly(c + "G", "sw:iron_dark", "-y", cy0, arch2d(xc, 1.0, G + 1.4, G + 3.4, "pointed", 3))
    for yc in (393.0, 397.0, 401.0):
        wall_poly(c + "G", "sw:iron_dark", "-x", c0, arch2d(-yc, 1.0, G + 1.4, G + 3.4, "pointed", 3))
        wall_poly(c + "G", "sw:iron_dark", "+x", c1, arch2d(yc, 1.0, G + 1.4, G + 3.4, "pointed", 3))
    box(c, stone, 29.3, 30.7, 397.0, 398.4, ce - 0.5, G + 11.5, sides=("n", "s", "e", "w"))
    box(c, stone, 29.15, 30.85, 396.85, 398.55, G + 11.2, G + 11.6, sides=("t", "n", "s", "e", "w", "b"))


def turn_e8():
    rot = Matrix.Rotation(E8_ANGLE, 3, "Z")
    for (part, mat), (verts, faces) in BUCKETS.items():
        if part.startswith("E8"):
            for i, v in enumerate(verts):
                verts[i] = E8_PIVOT + rot @ (v - E8_PIVOT)


def e8_point(a, b):
    """scene (x, z) of the church's local frame point (a along the front, b back from it)"""
    d = Vector((math.cos(E8_ANGLE), math.sin(E8_ANGLE)))
    n = Vector((-d.y, d.x))
    q = Vector((E8_PIVOT.x, E8_PIVOT.y)) + d * a + n * b
    return (q.x, -q.y)


# ===========================================================================
# E9  Soldiers' Monument and its railed plot (road fork, sheet 2)
# ===========================================================================
TRI = [(1.9, -319.5), (16.0, -318.6), (8.2, -296.2), (4.4, -296.2)]
PLOT_Y = 0.36


def build_e9():
    p = "E9"
    # raised plot: stone curb ring and the grass top
    inner = []
    c = Vector((sum(x for x, z in TRI) / 4, sum(z for x, z in TRI) / 4))
    for x, z in TRI:
        v = Vector((x, z))
        inner.append(tuple(v + (c - v).normalized() * 0.35))
    poly_flat("E9P", "grass", inner, PLOT_Y)
    for i in range(4):
        a, b = TRI[i], TRI[(i + 1) % 4]
        ia, ib = inner[i], inner[(i + 1) % 4]
        face_out(p, "concrete", [P(a[0], a[1], PLOT_Y + 0.04), P(b[0], b[1], PLOT_Y + 0.04),
                                 P(ib[0], ib[1], PLOT_Y + 0.04), P(ia[0], ia[1], PLOT_Y + 0.04)], (0, 0, 1))
    edge_skirt(p, "concrete", TRI + [TRI[0]], PLOT_Y + 0.04, 0.0, tuple(c))
    # low spear-top railing on the curb, posts at the corners, dark iron post at the east corner
    rail = []
    for x, z in TRI:
        v = Vector((x, z))
        rail.append(tuple(v + (c - v).normalized() * 0.17))
    for i in range(4):
        a, b = rail[i], rail[(i + 1) % 4]
        rail_quad("E9R", (a[0], -a[1]), (b[0], -b[1]), PLOT_Y + 0.04, 0.8, both=True, tile=1.2)
        sbox("E9R", "sw:iron_dark", a[0] - 0.07, a[0] + 0.07, a[1] - 0.07, a[1] + 0.07, PLOT_Y, PLOT_Y + 1.0,
             sides=("t", "n", "s", "e", "w"))
    ex, ez = rail[1]
    sbox("E9R", "sw:iron_dark", ex - 0.09, ex + 0.09, ez - 0.09, ez + 0.09, PLOT_Y, PLOT_Y + 2.7,
         sides=("n", "s", "e", "w"))
    sbox("E9R", "sw:iron_dark", ex - 0.2, ex + 0.2, ez - 0.2, ez + 0.2, PLOT_Y + 2.7, PLOT_Y + 3.15,
         sides=("t", "b", "n", "s", "e", "w"))
    # the monument: three granite steps, die, tall pedestal with a cap, plinth, soldier (faces south)
    m = "E9M"
    mx, mz = 8.2, -312.6
    my = -mz
    z = PLOT_Y
    for half, h in ((1.5, 0.25), (1.2, 0.25), (0.9, 0.25)):
        box(m, "sw:paint_white", mx - half, mx + half, my - half, my + half, z, z + h, sides=("t", "n", "s", "e", "w"))
        z += h
    box(m, "sw:paint_white", mx - 0.68, mx + 0.68, my - 0.68, my + 0.68, z, z + 0.95, sides=("n", "s", "e", "w"))
    box(m, "sw:paint_white", mx - 0.78, mx + 0.78, my - 0.78, my + 0.78, z + 0.95, z + 1.12,
        sides=("t", "n", "s", "e", "w", "b"))
    z += 1.12
    box(m, "sw:paint_white", mx - 0.46, mx + 0.46, my - 0.46, my + 0.46, z, z + 1.65, sides=("n", "s", "e", "w"))
    z += 1.65
    box(m, "sw:paint_white", mx - 0.62, mx + 0.62, my - 0.62, my + 0.62, z, z + 0.28, sides=("t", "n", "s", "e", "w", "b"))
    z += 0.28
    box(m, "sw:paint_white", mx - 0.36, mx + 0.36, my - 0.36, my + 0.36, z, z + 0.32, sides=("t", "n", "s", "e", "w"))
    z += 0.32
    soldier(m, mx, my, z)


def soldier(m, x, y, z):
    """standing Union soldier at parade rest, about 1.85 m, facing -Y (south), low poly"""
    W = "sw:paint_white"
    for sx in (-0.11, 0.11):                                    # legs
        box(m, W, x + sx - 0.085, x + sx + 0.085, y - 0.1, y + 0.1, z, z + 0.62, sides=("n", "s", "e", "w"))
    box(m, W, x - 0.25, x + 0.25, y - 0.17, y + 0.15, z + 0.5, z + 0.98, sides=("n", "s", "e", "w", "b"))  # coat skirt
    box(m, W, x - 0.23, x + 0.23, y - 0.14, y + 0.13, z + 0.98, z + 1.42, sides=("n", "s", "e", "w"))   # torso
    box(m, W, x - 0.27, x + 0.27, y - 0.14, y + 0.13, z + 1.36, z + 1.5, sides=("t", "n", "s", "e", "w", "b"))
    box(m, W, x - 0.05, x + 0.05, y - 0.05, y + 0.05, z + 1.5, z + 1.56, sides=("n", "s", "e", "w"))
    box(m, W, x - 0.1, x + 0.1, y - 0.11, y + 0.1, z + 1.56, z + 1.75, sides=("n", "s", "e", "w"))       # head
    box(m, W, x - 0.11, x + 0.11, y - 0.12, y + 0.11, z + 1.73, z + 1.86, sides=("t", "n", "s", "e", "w"))  # kepi
    box(m, W, x - 0.1, x + 0.1, y - 0.2, y - 0.12, z + 1.73, z + 1.76, sides=("t", "s", "e", "w", "b"))   # visor
    for sx in (-1, 1):                                          # arms down to the hands on the muzzle
        beam(m, W, (x + sx * 0.25, y, z + 1.42), (x + sx * 0.12, y - 0.22, z + 1.02), 0.1)
        beam(m, W, (x + sx * 0.12, y - 0.22, z + 1.02), (x + sx * 0.04, y - 0.3, z + 1.16), 0.09)
    box(m, W, x - 0.03, x + 0.03, y - 0.35, y - 0.29, z, z + 1.28, sides=("n", "s", "e", "w", "t"))       # rifle
    box(m, W, x - 0.05, x + 0.05, y - 0.37, y - 0.27, z, z + 0.32, sides=("n", "s", "e", "w", "t"))       # butt


# ===========================================================================
# E10  Public Library 118 Main (front -X at x 16.8; Maple Ave face +Y)
# ===========================================================================
def build_e10():
    p = "E10"
    x0, x1, y0, y1 = fp(16.8, 27.9, 136.3, 147.4)              # y -147.4 .. -136.3
    base, band, ent0, ent1 = G + 0.7, G + 3.95, G + 7.35, G + 8.35
    box(p, "sw:stone_cream", x0 - 0.06, x1, y0 - 0.06, y1 + 0.06, 0.0, base, sides=("t", "w", "n", "s", "e"))
    box(p, "brick", x0, x1, y0, y1, base, ent0, sides=("n", "s", "e", "w"))
    box(p, "sw:stone_cream", x0 - 0.08, x1 + 0.08, y0 - 0.08, y1 + 0.08, ent0, ent1, sides=("n", "s", "e", "w", "b"))
    box(p, "sw:stone_cream", x0 - 0.45, x1 + 0.45, y0 - 0.45, y1 + 0.45, ent1, ent1 + 0.3,
        sides=("n", "s", "e", "w", "b"))
    hip_roof(p, "sw:tin_dark", x0 - 0.45, x1 + 0.45, y0 - 0.45, y1 + 0.45, ent1 + 0.3, 1.5, oe=0.0)
    box(p, "sw:stone_cream", x0 - 0.05, x0, y0, y1, band, band + 0.25, sides=("w", "t", "b"))
    box(p, "sw:stone_cream", x0, x1, y1, y1 + 0.05, band, band + 0.25, sides=("n", "t", "b"))
    # giant stone pilasters: corners and between the three bays on the west and north faces
    bw = (y1 - y0) / 3
    for k in range(4):
        yc = y0 + bw * k
        yc = min(max(yc, y0 + 0.3), y1 - 0.3)
        box(p, "sw:stone_cream", x0 - 0.13, x0, yc - 0.3, yc + 0.3, base, ent0, sides=("w", "n", "s"))
        xc = x0 + (x1 - x0) / 3 * k
        xc = min(max(xc, x0 + 0.3), x1 - 0.3)
        box(p, "sw:stone_cream", xc - 0.3, xc + 0.3, y1, y1 + 0.13, base, ent0, sides=("n", "e", "w"))
    wc = [y0 + bw * (k + 0.5) for k in range(3)]
    for k, yc in enumerate(wc):                                 # west face: door in the middle bay
        if k == 1:
            window(p, "door_brown", "-x", (x0, yc, base), 1.3, 2.75)
            box(p, "sw:stone_cream", x0 - 0.12, x0, yc - 0.85, yc + 0.85, base + 2.75, base + 3.05,
                sides=("w", "t", "b", "n", "s"))
        else:
            for d in (-0.48, 0.48):
                window(p, cream(), "-x", (x0, yc + d, base + 0.6), 0.75, 1.75)
            box(p, "sw:stone_cream", x0 - 0.07, x0, yc - 1.0, yc + 1.0, base + 0.48, base + 0.6, sides=("w", "t"))
        window(p, cream(), "-x", (x0, yc, band + 0.95), 0.95, 1.75)
        box(p, "sw:stone_cream", x0 - 0.07, x0, yc - 0.6, yc + 0.6, band + 0.83, band + 0.95, sides=("w", "t"))
    nc = [x0 + (x1 - x0) / 3 * (k + 0.5) for k in range(3)]
    for k, xc in enumerate(nc):                                 # north (Maple Ave) face: door at the east end
        if k == 2:
            window(p, "door_brown", "+y", (xc, y1, base), 1.2, 2.6)
        else:
            for d in (-0.48, 0.48):
                window(p, cream(), "+y", (xc + d, y1, base + 0.6), 0.75, 1.75)
        window(p, cream(), "+y", (xc, y1, band + 0.95), 0.95, 1.75)
    for k, (dd, h) in enumerate(((1.35, G + 0.18), (0.9, G + 0.38), (0.45, G + 0.56))):
        box(p, "sw:stone_cream", x0 - dd, x0, wc[1] - 1.1, wc[1] + 1.1, 0.0, h, sides=("t", "w", "n", "s"))
        box(p, "sw:stone_cream", nc[2] - 1.0, nc[2] + 1.0, y1, y1 + dd, 0.0, h, sides=("t", "n", "e", "w"))


# ===========================================================================
# E11  Deats Building 120-124 Main (front -X at x 11.0)
# ===========================================================================
def build_e11():
    p = "E11"
    x0, x1, y0, y1 = fp(11.0, 32.3, 151.0, 165.4)              # y -165.4 .. -151.0
    top = G + 12.2
    box(p, "brick", x0, x1, y0, y1, 0.0, top - 0.6, sides=("n", "s", "e", "w"))
    box(p, "sw:wood_grey", x0 - 0.5, x1 + 0.1, y0 - 0.5, y1 + 0.5, top - 0.6, top,
        sides=("t", "n", "s", "e", "w", "b"), top="sw:tin_dark")
    box(p, "sw:wood_grey", x0 - 0.12, x0, y0 - 0.12, y1 + 0.12, top - 1.0, top - 0.6, sides=("w", "n", "s", "b"))
    # small central pediment on the cornice
    yc = (y0 + y1) / 2
    face_out(p, "sw:wood_grey", [(x0 - 0.5, yc - 2.4, top), (x0 - 0.5, yc + 2.4, top), (x0 - 0.5, yc, top + 1.1)],
             (-1, 0, 0))
    for sg in (-1, 1):
        slab(p, "sw:tin_dark", "sw:wood_grey", [(x0 - 0.6, yc + sg * 2.55, top - 0.02), (x0 - 0.6, yc, top + 1.15),
                                               (x0 + 1.6, yc, top + 1.15), (x0 + 1.6, yc + sg * 2.55, top - 0.02)], 0.1)
    face_out(p, "sw:wood_grey", [(x0 + 1.6, yc - 2.55, top), (x0 + 1.6, yc + 2.55, top), (x0 + 1.6, yc, top + 1.1)],
             (1, 0, 0))
    # front: shop front (post office) with a cornice, entrance with steps; 5 bays above
    box(p, "sw:wood_grey", x0 - 0.2, x0, y0 + 0.2, y1 - 0.2, G + 3.75, G + 4.15, sides=("w", "t", "b", "n", "s"))
    for yy in (-163.6, -160.6, -154.9, -151.9):
        window(p, green(), "-x", (x0, yy, G + 0.85), 2.1, 2.6)
    window(p, "door_brown", "-x", (x0, -157.75, G + 0.55), 1.5, 2.85)
    for k, (dd, h) in enumerate(((1.2, G + 0.18), (0.8, G + 0.36), (0.4, G + 0.55))):
        box(p, "concrete", x0 - dd, x0, -158.9, -156.6, 0.0, h, sides=("t", "w", "n", "s"))
    ys = (-164.0, -161.2, -158.2, -155.2, -152.4)
    for z, h in ((G + 4.85, 2.0), (G + 8.45, 1.9)):
        front_row(p, "-x", x0, list(ys), z, 1.0, h, cream)
        for a in ys:
            sill_lintel(p, "-x", x0, a, z, 1.0, h)
    # long sides: paired windows (photo), pale heads on the south side
    xs = (13.6, 14.8, 19.0, 20.2, 24.4, 25.6, 29.4, 30.6)
    for n, wall in (("-y", y0), ("+y", y1)):
        for z, h in ((G + 1.0, 2.4), (G + 4.85, 2.0), (G + 8.45, 1.9)):
            front_row(p, n, wall, xs, z, 0.95, h, cream)
            if n == "-y" and z > 2:
                for a in xs:
                    lintel(p, n, wall, a, z + h, 0.95)
    for xc in (12.6, 17.8, 23.3, 28.4):                         # four chimneys on the south wall
        box(p, "brick", xc - 0.38, xc + 0.38, y0 + 0.1, y0 + 0.75, top - 0.3, top + 1.9, sides=("t", "n", "s", "e", "w"))


# ===========================================================================
# Ground (scene x, z)
# ===========================================================================
def road_uv(c):
    return lambda x, z: ((x - c) / 6.4, z / 6.4)


def crowned_road(part, z_list, w, c, e, crown_at=None):
    """Main St road rows exactly as js/ground.js (9 points across, crowned 10 cm), flat beyond.
    The outer 0.5 m columns go to part + 'D' (the damp strip along each curb)."""
    ts = [-1, -1 + 0.5 / (c - w), -0.6, -0.3, 0, 0.3, 0.6, 1 - 0.5 / (e - c), 1]
    rows = []
    for z in z_list:
        cr = crown_at(z) if crown_at else CROWN
        row = []
        for t in ts:
            x = c + t * (c - w) if t < 0 else c + t * (e - c)
            row.append((x, z, ROAD_Y + cr * (1 - t * t)))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(1, 9):
            q = [r0[j - 1], r0[j], r1[j], r1[j - 1]]
            pts = [P(x, z, y) for x, z, y in q]
            uvs = [((x - c) / 6.4, z / 6.4) for x, z, y in q]
            face_out(part + ("D" if j in (1, 8) else ""), "road", pts, (0, 0, 1), uvs)


def walk_strip(part, road_path, prop_path, ends=(True, True), mat="concrete", curb=True):
    """sidewalk polygon between a road-edge path and a property-line path (scene x, z) at G,
    with the curb face down to the road and skirts at the open ends"""
    poly = list(road_path) + list(reversed(prop_path))
    poly_flat(part, mat, poly, G)
    if curb:
        far = prop_path[len(prop_path) // 2]
        edge_skirt("Curb", "concrete", road_path, G, ROAD_Y - 0.03, far)
    for use, a, b, other in ((ends[0], road_path[0], prop_path[0], road_path[1]),
                             (ends[1], road_path[-1], prop_path[-1], road_path[-2])):
        if use:
            edge_skirt(part, mat, [a, b], G, -0.03, other)


def lot(part, mat, pts, skirt_edges=(), y=G):
    poly_flat(part, mat, pts, y)
    c = (sum(x for x, z in pts) / len(pts), sum(z for x, z in pts) / len(pts))
    for i in skirt_edges:
        edge_skirt(part, mat, [pts[i], pts[(i + 1) % len(pts)]], y, -0.05, c)


def build_ground_north():
    # --- Main St, crowned as js/ground.js from z -180 to -230, crown fading to -250 ---
    W, C, E = -6.40, -1.45, 3.51
    zl = [-180.0, -190.0, -202.4, -192.5, -215.0, -230.0, -240.0, -250.0]
    zl = sorted(set(zl), reverse=True)
    crowned_road("RoadN", zl, W, C, E, crown_at=lambda z: CROWN * min(1.0, max(0.0, (z + 250.0) / 20.0)))
    # junction with Branch St and Pennsylvania Ave (flat, 0.01), monument plot as a hole
    junction = [(-6.4, -250.0), (-6.4, -328.7), (-13.8, -355.0), (-25.2, -412.0), (-14.7, -412.0), (-3.3, -355.0),
                (0.2, -329.6), (22.9, -328.0), (42.6, -368.9), (53.0, -371.0), (30.0, -317.4), (79.5, -306.7),
                (80.5, -297.2), (24.0, -309.0), (9.8, -281.0), (3.51, -250.0)]
    poly_flat("RoadJ", "road", junction, ROAD_Y, holes=[TRI], uvfn=road_uv(C))
    edge_skirt("RoadJ", "road", [(-25.2, -412.0), (-14.7, -412.0)], ROAD_Y, -0.03, (-20, -400))
    edge_skirt("RoadJ", "road", [(42.6, -368.9), (53.0, -371.0)], ROAD_Y, -0.03, (45, -360))
    edge_skirt("RoadJ", "road", [(79.5, -306.7), (80.5, -297.2)], ROAD_Y, -0.03, (70, -302))
    # --- west walk (cut at Capner St), Capner St stub ---
    walk_strip("WalkN", [(-6.4, -180.0), (-6.4, -192.5)], [(-10.3, -180.0), (-10.3, -192.5)], ends=(False, True))
    # (2026-11-12, PLAN.md 7.9: z -202.4 .. -328.7 of the west walk, its grass strip and the lawns
    #  behind it are drawn by north-approach.glb. North of z -328.7 the same 1913 section carries
    #  on: grass strip 2.2 m at the curb, concrete walk 1.8 m, then lawn.)
    road_w = [(-6.4, -328.7), (-13.8, -355.0), (-25.2, -412.0)]
    prop_w = [(-10.6, -328.7), (-16.8, -355.0), (-28.2, -412.0)]
    at = lambda t: [(rx + (px - rx) * t, rz + (pz - rz) * t) for (rx, rz), (px, pz) in zip(road_w, prop_w)]
    strip_in, walk_in = at(2.2 / 4.2), at(4.0 / 4.2)
    lot("LotW", "grass", road_w + list(reversed(strip_in)))
    edge_skirt("Curb", "concrete", road_w, G, ROAD_Y - 0.03, prop_w[1])
    edge_skirt("LotW", "grass", [road_w[-1], strip_in[-1]], G, -0.03, (-20.0, -400.0))
    walk_strip("WalkN", strip_in, walk_in, ends=(False, True), curb=False)
    capner = [(-10.3, -192.5), (-10.3, -202.4), (-6.4, -202.4), (-6.4, -192.5)]
    poly_flat("RoadN", "road", capner, ROAD_Y, uvfn=lambda x, z: ((z + 197.45) / 6.4 + 0.5, x / 6.4))
    for a, b in zip(split(-52.0, -10.3, 14.0), split(-52.0, -10.3, 14.0)[1:]):
        poly_flat("RoadN", "road", [(a, -200.4), (b, -200.4), (b, -194.5), (a, -194.5)], ROAD_Y,
                  uvfn=lambda x, z: ((z + 197.45) / 6.4 + 0.5, x / 6.4))
        poly_flat("WalkN", "concrete", [(a, -202.4), (b, -202.4), (b, -200.4), (a, -200.4)], G)
        poly_flat("WalkN", "concrete", [(a, -194.5), (b, -194.5), (b, -192.5), (a, -192.5)], G)
    edge_skirt("Curb", "concrete", [(-52.0, -200.4), (-10.3, -200.4)], G, ROAD_Y - 0.03, (-30, -202))
    edge_skirt("Curb", "concrete", [(-52.0, -194.5), (-10.3, -194.5)], G, ROAD_Y - 0.03, (-30, -193))
    edge_skirt("Curb", "concrete", [(-10.3, -192.5), (-10.3, -194.5)], G, ROAD_Y - 0.03, (-12, -193))
    edge_skirt("Curb", "concrete", [(-10.3, -202.4), (-10.3, -200.4)], G, ROAD_Y - 0.03, (-12, -201))
    edge_skirt("RoadN", "road", [(-52.0, -200.4), (-52.0, -194.5)], ROAD_Y, -0.03, (-40, -197))
    # --- hotel front pavement, the E1 lot, the gap to 27 Main ---
    lot("WalkN", "concrete", [(-13.1, -192.5), (-10.3, -192.5), (-10.3, -168.2), (-13.1, -168.2)])
    lot("LotN", "earth", [(-52.0, -192.5), (-25.6, -192.5), (-25.6, -167.9), (-52.0, -167.9)], skirt_edges=(3,))
    lot("LotN", "earth", [(-52.4, -167.9), (-10.3, -168.2), (-10.3, -165.15), (-52.4, -165.15)], skirt_edges=(2, 3))
    lot("LotN", "earth", [(-25.6, -192.5), (-13.1, -192.5), (-13.1, -168.2), (-25.6, -167.9)])
    edge_skirt("LotN", "earth", [(-52.0, -192.5), (-52.0, -165.15)], G, -0.05, (-30, -180))
    # --- west side north of Capner St. Correction 2026-11-12 (PLAN.md 7.9): this is not empty
    #     Water Co. ground: five houses (1-11 Main) stood here on Sept 1921 sheet 6. Their lawns
    #     from Capner St to z -328.7 are in north-approach.glb; only the lawn north of that stays.
    lot("LotW", "grass", [(-60.0, -328.7), walk_in[0], walk_in[1], walk_in[2], (-60.0, -412.0)],
        skirt_edges=(3, 4))
    # --- east side: walk, front strip, lots ---
    walk_strip("WalkN", [(3.51, -180.0), (3.51, -250.0), (9.8, -281.0), (24.0, -309.0), (80.5, -297.2)],
               [(6.36, -180.0), (6.0, -247.8), (12.0, -279.6), (25.7, -307.2), (80.0, -294.9)], ends=(False, True))
    lot("LotE", "earth", [(6.36, -180.0), (10.6, -180.0), (10.6, -192.4), (6.29, -192.4)])
    lot("LotE", "earth", [(10.35, -180.0), (50.0, -180.0), (50.0, -164.4), (10.35, -164.4)], skirt_edges=(1, 2))
    edge_skirt("LotE", "earth", [(6.36, -180.0), (10.35, -180.0)], G, -0.03, (8, -170))
    edge_skirt("LotE", "earth", [(10.35, -180.0), (10.35, -164.4)], G, -0.03, (20, -170))
    # (2026-11-12: the lawns of 2-10 Main, z -192.4 .. -307.2, are in north-approach.glb)
    lot("LotE", "grass", [(10.6, -180.0), (50.0, -180.0), (50.0, -192.4), (10.6, -192.4)])
    edge_skirt("LotE", "grass", [(50.0, -180.0), (50.0, -192.4)], G, -0.05, (30, -186))
    # --- church block: walks round it, lawn ---
    walk_strip("WalkC", [(-14.7, -412.0), (-3.3, -355.0), (0.2, -329.6), (22.9, -328.0), (42.6, -368.9)],
               [(-12.3, -412.0), (-0.9, -355.0), (2.8, -332.0), (21.0, -330.6), (40.4, -370.0)])
    church_lot = [(2.8, -332.0), (21.0, -330.6), (40.4, -370.0), (50.0, -412.0), (-12.3, -412.0), (-0.9, -355.0)]
    lot("LotC", "grass", church_lot, skirt_edges=(2, 3))
    # curving paths from the corner to the porch and to the tower door, two flower beds
    pa = e8_point(23.6, -1.0)
    pb = e8_point(3.2, 5.6)
    ribbon_xz("Paths", "concrete", [(12.0, -331.0), (13.5, -336.0), (17.5, -341.0), (22.0, -345.0), (24.0, -349.0),
                                    pa], 1.6, G + 0.012)
    ribbon_xz("Paths", "concrete", [(3.2, -332.6), (4.8, -340.0), (6.4, -347.0), (7.5, -353.0), pb], 1.4, G + 0.012)
    for bx, bz, r in ((13.0, -343.5, 2.2), (2.5, -346.0, 1.6)):
        poly_flat("Beds", "earth", [(bx + r * 1.3 * math.cos(2 * math.pi * k / 10), bz + r * math.sin(2 * math.pi * k / 10))
                                    for k in range(10)], G + 0.02)
    # --- Branch St east / Pennsylvania Ave north: walk and lot ---
    walk_strip("WalkN", [(53.0, -371.0), (30.0, -317.4), (79.5, -306.7)], [(55.2, -370.0), (31.7, -319.9), (80.0, -309.0)])
    lot("LotB", "grass", [(31.7, -319.9), (80.0, -309.0), (80.0, -375.0), (57.5, -375.0)], skirt_edges=(1, 2, 3))


def ribbon_xz(part, mat, pts, w, y):
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


def build_ground_south():
    W, C, E = -4.19, 1.08, 6.40
    zl = [80.0, 110.0, 123.7, 136.4, 170.0, 215.0, 260.0]
    crowned_road("RoadS", zl, W, C, E)
    edge_skirt("RoadS", "road", [(W, 260.0), (E, 260.0)], ROAD_Y, -0.03, (0, 250))
    # walks (east side cut at Maple Ave), curbs
    walk_strip("WalkS", [(W, 80.0), (W, 260.0)], [(-7.76, 80.0), (-7.76, 260.0)], ends=(False, True))
    walk_strip("WalkS", [(E, 80.0), (E, 125.9)], [(9.3, 80.0), (9.3, 125.9)], ends=(False, True))
    walk_strip("WalkS", [(E, 134.2), (E, 260.0)], [(9.3, 134.2), (9.3, 260.0)])
    # Maple Ave east of Main St: road z 125.9 .. 134.2, walks
    mz = (125.9 + 134.2) / 2
    poly_flat("RoadS", "road", [(E, 125.9), (E, 134.2), (9.3, 134.2), (9.3, 125.9)], ROAD_Y,
              uvfn=lambda x, z: ((z - mz) / 6.4 + 0.5, x / 6.4))
    xs = split(9.3, 60.0, 17.0)
    for a, b in zip(xs, xs[1:]):
        poly_flat("RoadS", "road", [(a, 125.9), (b, 125.9), (b, 134.2), (a, 134.2)], ROAD_Y,
                  uvfn=lambda x, z: ((z - mz) / 6.4 + 0.5, x / 6.4))
    walk_strip("WalkS", [(9.3, 125.9), (60.0, 125.9)], [(9.3, 123.7), (60.0, 123.7)], ends=(False, True))
    walk_strip("WalkS", [(9.3, 134.2), (60.0, 134.2)], [(9.3, 136.4), (60.0, 136.4)], ends=(False, True))
    edge_skirt("RoadS", "road", [(60.0, 125.9), (60.0, 134.2)], ROAD_Y, -0.03, (50, 130))
    # east lots: strip by Higgins Ave, Vosseller rear yard, Doric House, church, library, Deats
    lot("LotS", "earth", [(9.3, 68.7), (31.5, 68.7), (31.5, 69.05), (9.3, 69.05)])
    lot("LotS", "earth", [(9.3, 85.8), (31.5, 85.8), (31.5, 90.0), (9.3, 90.0)])
    lot("LotS", "grass", [(9.3, 90.0), (60.0, 90.0), (60.0, 106.6), (9.3, 106.6)], skirt_edges=(1,))
    lot("LotS", "grass", [(9.3, 106.6), (60.0, 106.6), (60.0, 123.7), (9.3, 123.7)], skirt_edges=(1,))
    lot("LotS", "grass", [(9.3, 136.4), (60.0, 136.4), (60.0, 150.2), (9.3, 150.2)], skirt_edges=(1,))
    lot("LotS", "earth", [(9.3, 150.2), (60.0, 150.2), (60.0, 175.0), (9.3, 175.0)], skirt_edges=(1,))
    lot("LotS", "grass", [(9.3, 175.0), (60.0, 175.0), (60.0, 210.0), (9.3, 210.0)], skirt_edges=(1, 2))
    edge_skirt("LotS", "grass", [(9.3, 210.0), (9.3, 260.0)], G, -0.05, (12, 230))
    # front paths: Doric House gate to its steps, library door, church tower steps
    lot("Paths", "concrete", [(9.6, 98.35), (13.45, 98.35), (13.45, 99.45), (9.6, 99.45)], y=G + 0.012)
    lot("Paths", "concrete", [(9.3, 120.6), (16.1, 120.6), (16.1, 122.1), (9.3, 122.1)], y=G + 0.012)
    lot("Paths", "concrete", [(9.3, 141.1), (15.45, 141.1), (15.45, 142.6), (9.3, 142.6)], y=G + 0.012)
    # west side: lawns behind the walk (houses set back behind lawns, big trees: 1907 card)
    for z0, z1 in ((58.4, 110.0), (110.0, 160.0), (160.0, 210.0)):
        lot("LawnW", "grass", [(-45.0, z0), (-7.76, z0), (-7.76, z1), (-45.0, z1)], skirt_edges=(3,))
    edge_skirt("LawnW", "grass", [(-45.0, 58.4), (-7.76, 58.4)], G, -0.05, (-20, 70))
    edge_skirt("LawnW", "grass", [(-45.0, 210.0), (-7.76, 210.0)], G, -0.05, (-20, 200))
    edge_skirt("WalkS", "concrete", [(-7.76, 210.0), (-7.76, 260.0)], G, -0.05, (-6, 230))


# ===========================================================================
# build
# ===========================================================================
BUCKETS.clear()
col = clear_collection()
build_e1()
build_e2()
build_e3_e4()
build_e5()
build_e6()
build_e7()
build_e8()
turn_e8()
build_e9()
build_e10()
build_e11()
build_ground_north()
build_ground_south()
OBJS = make_objects(col)
for o in OBJS:
    o.name = o.data.name = o.name.replace("SC_", "EN_", 1)
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in OBJS)
import re
by = {}
for o in OBJS:
    m = re.match(r"E\d+", o["part"])
    k = m.group(0) if m else "ground"
    by[k] = by.get(k, 0) + sum(len(p.vertices) - 2 for p in o.data.polygons)
print("StreetEnds built:", len(OBJS), "objects,", tris, "triangles")
print(sorted(by.items()))
