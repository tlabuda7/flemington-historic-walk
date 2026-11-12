"""
north_approach.py - the ten houses along Main St between the last shops (z about -180) and the
Soldiers' Monument (PLAN.md "Side streets, backdrop buildings", subsection 7.9 "North approach"),
as one cheap model, with the lawns, paths and the narrowed west walk in front of them.

WEST SIDE (fronts face scene +x = Blender +X), Sept 1921 Sanborn sheet 6 (+-2.5 m)
  NW1  9-11 Main "Capnerhurst": 2-storey rubble stone, tin gable roof (ridge along the street),
       5 bays, centre door with transom, 1-storey porch on plain posts; rear 1-storey stone part,
       plumber's 2-storey frame annex and the 2-storey frame "Storage" along Capner St
                                                    PLAIN-GUESS (MAP + TEXT NRHP-1980)
  NW2  7 Main: 2-storey frame L-plan, low bracketed gables, porch on round columns with a spindle
       frieze                                       PLAIN-GUESS (MAP + TEXT NRHP-1980)
  NW3  5 Main: 2 1/2-storey frame L-plan, front gable to the street with a bracketed raking
       cornice, segment-arched window hoods, dark shutters, cream clapboard; arcaded porch
       (pierced flat-sawn posts, pointed-arch spandrels, white baluster rail) with the NE corner
       pavilion to x -14.7; white garden urn on a pedestal       PHOTO-BASED (1913) + MAP + TEXT
  NW4  3 Main: 2 1/2-storey frame L-plan, intersecting slate gables, square tower over the
       entrance with a steep pyramid roof and finial, 2-storey canted bays front and south,
       segment-arched hoods; wide arcaded porch to x -17.0       PHOTO-BASED (1913, 1908) + MAP + TEXT
  NW5  1 Main, Capner / Brodhead House: 2 1/2-storey red brick, pale trim, 5 bays, gable ends
       N and S, central gambrel gable with a Palladian window, two dormers, pair of tall
       chimneys on the south gable, semicircular 2-storey bay with a balcony rail (south),
       keystoned architraves; wrap porch (front + north) on slender columns with balusters;
       diagonal porte-cochere with a pediment at the SE corner    PHOTO-BASED (1906, c.1910, 1914) + MAP + TEXT
EAST SIDE (fronts face -X), Sept 1921 Sanborn sheet 2 (+-0.5 m)
  NE1  10 Main "Off.": 2 storeys, brick below, iron-clad above, flat roof, small porch    PLAIN-GUESS (MAP)
  NE2  8 Main "Boarding": 3 storeys + basement, brick, low hip (shingle), full porch       PLAIN-GUESS (MAP)
  NE3  6 Main: 2-storey frame, front gable, north wing, full porch                        PLAIN-GUESS (MAP)
  NE4  4 Main: 2 1/2-storey brick Italianate, low front gable with heavy bargeboards,
       paired brackets, tall narrow windows, arcaded porch front + north   PLAIN-GUESS (MAP + TEXT NRHP-1980)
  NE5  2 Main (W. D. Bloom?): 2 1/2-storey pale scored stucco, T-plan, cross gables, wide
       bracketed eaves, 2-storey bay south, 3-bay arcaded porch; turned 11.2 deg to the bend
                                                    PHOTO-BASED (c.1905-10 monument cards) + MAP + TEXT
No signs, lettering or glass. No trees (the scene instances old-maple.glb; positions in
north_approach_bake.py TREES).

GROUND (this model draws it; street-ends.glb no longer does):
  west  lawn x -110 .. -10.4 (R-a 2026-11-12; was -60) and the 1913 walk: concrete x -10.4 .. -8.6 (1.8 m), grass strip
        x -8.6 .. -6.4 (2.2 m), curb face at x -6.4; all for z -202.4 .. -328.7
  east  lawns from the east walk's property line (6.29, -192.4) .. (6.0, -247.8) ..
        (12.0, -279.6) .. (25.7, -307.2) east to x 95 (R-a; was 50 / 80), z -192.4 .. -307.2,
        SE edge (25.7, -307.2) .. (80, -294.9) .. (95, -291.5)
OUTBUILDINGS (R-a, PLAN.md "Rough-spot fixes"): 26 plain massing boxes from the 1921 maps (OE1-14,
  OW1-12), see build_outbuildings()
  1.2 m concrete paths cut into the lawns (no overlap) from the walk to each porch's steps,
  NW5's curving walk (c.1910 card). Road, east walk, Capner St and everything north of
  z -328.7 (west) / beyond the east walk's bend stay in street-ends.glb.

Run inside Blender:
    exec(open(r"<project>/tools/blender/north_approach.py", encoding="utf8").read())
Every run deletes and rebuilds the "NorthApproach" collection. Helpers are taken with `ast`
from sidestreet_court.py, sidestreet_bloomfield.py and street_ends.py.

Coordinates: SCENE AXES (the GLB is placed at "0 0 0", rotation "0 0 0"):
    Blender X = scene x (east), Blender Y = -scene z (north = +Y), Blender Z = scene y (up).
Lots and walks at y 0.15; walls skirt down to 0.0.
"""

import ast
import json
import math
import random
import bpy
import bmesh
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
COURT = PROJECT + r"\tools\blender\sidestreet_court.py"
BLOOM = PROJECT + r"\tools\blender\sidestreet_bloomfield.py"
ENDS = PROJECT + r"\tools\blender\street_ends.py"
COLL = "NorthApproach"
G = 0.15
ROAD_Y = 0.01
ATLAS = json.load(open(PROJECT + r"\assets\textures\shared\backdrop_windows.json"))["cells"]
TILE = {"clap": 1.0, "brick": 1.4, "slate": 1.5, "block": 2.0, "concrete": 3.0, "grass": 4.0, "stucco": 2.5}
rng = random.Random(1913)
BUCKETS = {}


def _take(path, names):
    tree = ast.parse(open(path, encoding="utf8").read())
    mod = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names],
                     type_ignores=[])
    exec(compile(mod, path, "exec"), globals())
    missing = set(names) - {n.name for n in mod.body}
    assert not missing, missing


_take(COURT, {"P", "newell", "add", "face_out", "solid", "box", "sbox", "gable_walls", "slab", "gable_roof",
              "shed", "window", "win_row", "cream", "green", "clear_collection", "uv_for", "make_objects",
              "cross_gable"})
_take(BLOOM, {"fp", "foundation", "chimney", "front_row", "split"})
_take(ENDS, {"WP", "U_of", "arch2d", "ring", "prism", "pyramid", "hip_roof", "poly_flat", "edge_skirt",
             "lintel", "wall_poly", "cell_uvs"})

FINAL_MAT = {"clap": "clap", "brick": "brick", "slate": "slate", "block": "block", "concrete": "concrete",
             "grass": "grass", "atlas": "atlas", "stucco": "stucco"}
TAN = lambda deg: math.tan(math.radians(deg))
UP = Vector((0, 0, 1))
NRM = {"-x": Vector((-1, 0, 0)), "+x": Vector((1, 0, 0)), "+y": Vector((0, 1, 0)), "-y": Vector((0, -1, 0))}


# ===========================================================================
# helpers
# ===========================================================================
def frame(n, wall):
    """porch / wall frame: Q(d, a, z) = wall point + d outward + a along the wall + z up"""
    N = NRM[n]
    T = Vector((0, 1, 0)) if n in ("+x", "-x") else Vector((1, 0, 0))
    O = Vector((wall, 0, 0)) if n in ("+x", "-x") else Vector((0, wall, 0))
    return N, T, (lambda d, a, z: O + N * d + T * a + Vector((0, 0, z)))


def pt(n, wall, a, z):
    return (wall, a, z) if n in ("+x", "-x") else (a, wall, z)


def wins(p, n, wall, along, z, w, h, cells=None, hood=False, shut=False, frame_=False):
    """windows on a wall (Blender along-coordinates), with optional segment-arched hoods, dark
    shutters, or keystoned architraves (NW5)"""
    N, T, Q = frame(n, wall)
    for a in along:
        cell = cells if isinstance(cells, str) else (cells or cream)()
        window(p, cell, n, pt(n, wall, a, z), w, h, off=0.035 if frame_ else 0.03)
        if shut:
            for s in (-1, 1):
                window(p + "S", "paint_green_s", n, pt(n, wall, a + s * (w / 2 + 0.24), z), 0.44, h, off=0.025)
        if hood:
            r, zt = w / 2 + 0.1, z + h + 0.02
            rise = 0.2
            pts = [Q(0.045, a - r, zt), Q(0.045, a + r, zt), Q(0.045, a + r, zt + 0.12)]
            for k in (1, 2, 3):
                t = k / 4
                pts.append(Q(0.045, a + r - 2 * r * t, zt + 0.12 + rise * math.sin(math.pi * t)))
            pts.append(Q(0.045, a - r, zt + 0.12))
            face_out(p + "T", "sw:paint_cream", pts, N)
        if frame_:
            face_out(p + "T", "sw:stone_cream",
                     [Q(0.018, a - w / 2 - 0.17, z - 0.14), Q(0.018, a + w / 2 + 0.17, z - 0.14),
                      Q(0.018, a + w / 2 + 0.17, z + h + 0.17), Q(0.018, a - w / 2 - 0.17, z + h + 0.17)], N)
            face_out(p + "T", "sw:stone_cream",
                     [Q(0.05, a - 0.13, z + h - 0.06), Q(0.05, a + 0.13, z + h - 0.06),
                      Q(0.05, a + 0.17, z + h + 0.3), Q(0.05, a - 0.17, z + h + 0.3)], N)


def bracket(p, n, wall, a, z_top, depth=0.45, h=0.55, w=0.12, mat="sw:paint_white"):
    """scroll bracket under an eave: two side profiles + curved underside (10 tris)"""
    N, T, Q = frame(n, wall)
    prof = [(0.0, z_top), (depth, z_top), (depth, z_top - 0.14), (depth * 0.42, z_top - h * 0.5), (0.0, z_top - h)]
    for s in (-1, 1):
        face_out(p, mat, [Q(d, a + s * w / 2, z) for d, z in prof], T * s)
    for (d0, z0), (d1, z1) in ((prof[2], prof[3]), (prof[3], prof[4])):
        face_out(p, mat, [Q(d0, a - w / 2, z0), Q(d0, a + w / 2, z0), Q(d1, a + w / 2, z1), Q(d1, a - w / 2, z1)],
                 N * 0.5 - UP)


def post(p, kind, Q, d, a, z0, z1, pw, mat="sw:paint_white"):
    if kind == "col":                              # round column, 6 sides, with a square base
        c = Q(d, a, 0)
        prism(p, mat, ring(c.x, c.y, pw / 2, 6, z0 + 0.25), ring(c.x, c.y, pw / 2 * 0.85, 6, z1 - 0.1))
        bb = [Q(d + dx, a + da, 0) for dx, da in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        r = pw / 2 + 0.05
        sq = [Vector((c.x + sx * r, c.y + sy * r, 0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        prism(p, mat, [v + Vector((0, 0, z0)) for v in sq], [v + Vector((0, 0, z0 + 0.25)) for v in sq], cap=True)
        return
    if kind == "flat":                             # pierced flat-sawn board post
        wd, th = 0.34, 0.1
    elif kind == "chamf":                          # chamfered post on a pedestal
        wd = th = pw
        c = Q(d, a, 0)
        sq = [Vector((c.x + sx * 0.2, c.y + sy * 0.2, 0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        prism(p, mat, [v + Vector((0, 0, z0)) for v in sq], [v + Vector((0, 0, z0 + 0.95)) for v in sq], cap=True)
        prism(p, mat, ring(c.x, c.y, pw / 2 * 1.2, 8, z0 + 0.95, math.pi / 8),
              ring(c.x, c.y, pw / 2 * 1.2, 8, z1, math.pi / 8))
        return
    else:
        wd = th = pw
    N = (Q(1, 0, 0) - Q(0, 0, 0))
    T = (Q(0, 1, 0) - Q(0, 0, 0))
    c = Q(d, a, 0)
    sq = [c + N * (sn * th / 2) + T * (st * wd / 2) for sn, st in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    prism(p, mat, [v + Vector((0, 0, z0)) for v in sq], [v + Vector((0, 0, z1)) for v in sq])


def spandrels(p, Q, N, d, a_list, pw, z_top, kind, h_arch, mat="sw:paint_white", out=None):
    """arch spandrel per bay on the plane d (in front of the posts), facing `out` (default N)"""
    for al, ar in zip(a_list, a_list[1:]):
        lo, hi = min(al, ar) + pw / 2, max(al, ar) - pw / 2
        w = hi - lo
        if w < 0.3:
            continue
        cu = (lo + hi) / 2
        if kind == "pointed":
            rf = 0.62
            R = rf * w
            th = math.acos((R - w / 2) / R)
            apex = R * math.sin(th)
            vs = z_top - 0.12 - apex
            arc = arch2d(cu, w, 0.0, vs, "pointed", n=4, rf=rf)[2:]
        elif kind == "round":
            vs = z_top - 0.12 - w / 2 * h_arch
            arc = [(cu + w / 2 * math.cos(math.pi * k / 8), vs + w / 2 * h_arch * math.sin(math.pi * k / 8))
                   for k in range(9)]
        else:                                      # flat lambrequin with corner quadrants
            vs = z_top - h_arch
            arc = [(hi, vs), (hi - 0.25, vs + 0.06), (hi - 0.4, vs + 0.22), (lo + 0.4, vs + 0.22),
                   (lo + 0.25, vs + 0.06), (lo, vs)]
        pts = [Q(d, lo, z_top), Q(d, hi, z_top)] + [Q(d, u, v) for u, v in arc]
        face_out(p, mat, pts, out if out is not None else N)


def pickets(p, Q, N, d, a0, a1, z0, h, tile=1.6):
    u0, v0, u1, v1 = ATLAS["pickets"]
    L = abs(a1 - a0)
    face_out(p, "atlas", [Q(d, a0, z0), Q(d, a1, z0), Q(d, a1, z0 + h), Q(d, a0, z0 + h)], N,
             [(0, v0), (L / tile, v0), (L / tile, v1), (0, v1)])


def porch_g(p, n, wall, depth, a0, a1, deck, top, nb, kind="sq", pw=0.18, arch=None, arch_h=0.6,
            rail=False, steps=(), rise=0.3, frieze=None, ends=(), roof_mat="sw:tin_dark", side_bays=1,
            post_mat="sw:paint_white", roof=True, skip_end_wall=()):
    """open porch on the wall facing n: deck, posts on the outer edge, arch spandrels / spindle
    frieze, baluster rail, shed roof falling outward, steps. ends = (0 and/or 1): also posts and
    arches along the deck's end edges (wraps)."""
    N, T, Q = frame(n, wall)
    face_out(p, "sw:wood_grey", [Q(0, a0, deck), Q(depth, a0, deck), Q(depth, a1, deck), Q(0, a1, deck)], UP)
    face_out(p, "sw:wood_grey", [Q(depth, a0, 0), Q(depth, a1, 0), Q(depth, a1, deck), Q(depth, a0, deck)], N)
    for e, a, s in ((0, a0, -1), (1, a1, 1)):
        if e not in skip_end_wall:
            face_out(p, "sw:wood_grey", [Q(0, a, 0), Q(depth, a, 0), Q(depth, a, deck), Q(0, a, deck)], T * s)
    dp = depth - pw / 2 - 0.05
    As = [a0 + pw / 2 + 0.05 + (a1 - a0 - pw - 0.1) * k / nb for k in range(nb + 1)]
    zt = top
    for a in As:
        post(p, kind, Q, dp, a, deck, zt, pw, post_mat)
    if arch:
        spandrels(p, Q, N, dp + (0.06 if kind == "flat" else pw / 2) + 0.01, As, pw, zt, arch, arch_h)
    if frieze:
        for al, ar in zip(As, As[1:]):
            pickets(p, Q, N, dp + 0.01, al + pw / 2, ar - pw / 2, zt - frieze - 0.06, frieze, tile=1.0)
    if rail:
        for al, ar in zip(As, As[1:]):
            if any(min(al, ar) < s < max(al, ar) for s in steps):
                continue
            pickets(p, Q, N, dp, al + pw / 2, ar - pw / 2, deck, 0.78)
            face_out(p, "sw:paint_white", [Q(dp - 0.06, al, deck + 0.78), Q(dp + 0.06, al, deck + 0.78),
                                           Q(dp + 0.06, ar, deck + 0.78), Q(dp - 0.06, ar, deck + 0.78)], UP)
    for e in ends:
        a = As[0] if e == 0 else As[-1]
        s = -1 if e == 0 else 1
        ds = [dp - (dp - 0.25) * k / side_bays for k in range(side_bays + 1)]
        for dd in ds[1:-1]:
            post(p, kind, Q, dd, a, deck, zt, pw, post_mat)
        if arch:
            # spandrels on the end plane, from the corner post back to the wall
            for d_hi, d_lo in zip(ds, ds[1:]):
                lo, hi = (0.05 if d_lo < 0.3 else d_lo + pw / 2), d_hi - pw / 2
                w = hi - lo
                if w < 0.3:
                    continue
                cu = (lo + hi) / 2
                if arch == "pointed":
                    rf = 0.62
                    R = rf * w
                    th = math.acos((R - w / 2) / R)
                    vs = zt - 0.12 - R * math.sin(th)
                    arc = arch2d(cu, w, 0.0, vs, "pointed", n=4, rf=rf)[2:]
                else:
                    vs = zt - 0.12 - w / 2 * arch_h
                    arc = [(cu + w / 2 * math.cos(math.pi * k / 8), vs + w / 2 * arch_h * math.sin(math.pi * k / 8))
                           for k in range(9)]
                aa = a + s * (pw / 2 + 0.01)
                pts = [Q(lo, aa, zt), Q(hi, aa, zt)] + [Q(u, aa, v) for u, v in arc]
                face_out(p, "sw:paint_white", pts, T * s)
        if rail:
            face_out(p, "atlas", [Q(0.1, a, deck), Q(dp, a, deck), Q(dp, a, deck + 0.78), Q(0.1, a, deck + 0.78)],
                     T * s, [(0, ATLAS["pickets"][1]), (dp / 1.6, ATLAS["pickets"][1]),
                             (dp / 1.6, ATLAS["pickets"][3]), (0, ATLAS["pickets"][3])])
    if roof:
        slab(p, roof_mat, "sw:paint_white",
             [Q(0, a0 - 0.12, zt + rise), Q(depth + 0.18, a0 - 0.12, zt), Q(depth + 0.18, a1 + 0.12, zt),
              Q(0, a1 + 0.12, zt + rise)], 0.16)
    for st in steps:
        for k, frac in enumerate((1 / 3, 2 / 3)):
            dfar = depth + 0.33 * (2 - k)
            zz = deck * frac
            for f, nn in (([Q(depth, st - 0.75, zz), Q(dfar, st - 0.75, zz), Q(dfar, st + 0.75, zz),
                            Q(depth, st + 0.75, zz)], UP),
                          ([Q(dfar, st - 0.75, 0), Q(dfar, st + 0.75, 0), Q(dfar, st + 0.75, zz),
                            Q(dfar, st - 0.75, zz)], N),
                          ([Q(depth, st - 0.75, 0), Q(dfar, st - 0.75, 0), Q(dfar, st - 0.75, zz),
                            Q(depth, st - 0.75, zz)], -T),
                          ([Q(depth, st + 0.75, 0), Q(dfar, st + 0.75, 0), Q(dfar, st + 0.75, zz),
                            Q(depth, st + 0.75, zz)], T)):
                face_out(p, "sw:wood_grey", f, nn)
    return As


def canted_bay(p, mat, n, wall, a, w, dep, z0, z1, roof_mat="sw:tin_dark", win=None):
    """2-storey canted bay on a wall: 3 faces, flat tin roof, windows on the faces"""
    N, T, Q = frame(n, wall)
    s = dep * 0.8
    pts = [(0, a - w / 2), (dep, a - w / 2 + s), (dep, a + w / 2 - s), (0, a + w / 2)]
    faces = []
    for (d0, a0_), (d1, a1_) in zip(pts, pts[1:]):
        nrm = (Q(d1, a1_, 0) - Q(d0, a0_, 0)).cross(UP)
        if nrm.dot(N) < 0:
            nrm = -nrm
        face_out(p, mat, [Q(d0, a0_, z0), Q(d1, a1_, z0), Q(d1, a1_, z1), Q(d0, a0_, z1)], nrm)
        faces.append((Q(d0, a0_, 0), Q(d1, a1_, 0), nrm))
    slab(p, roof_mat, "sw:paint_white", [Q(0, a - w / 2 - 0.15, z1), Q(dep + 0.15, a - w / 2 + s - 0.1, z1),
                                         Q(dep + 0.15, a + w / 2 - s + 0.1, z1), Q(0, a + w / 2 + 0.15, z1)], 0.18)
    if win:
        for z, h in win:
            for A, B, nrm in faces:
                c = (A + B) / 2
                L = (B - A).length
                ww = min(0.9, L - 0.3)
                if ww < 0.35:
                    continue
                tdir = (B - A).normalized()
                o = c + nrm.normalized() * 0.03
                face_out(p, "atlas", [o - tdir * ww / 2 + UP * z, o + tdir * ww / 2 + UP * z,
                                      o + tdir * ww / 2 + UP * (z + h), o - tdir * ww / 2 + UP * (z + h)],
                         nrm, None)
                # uv: a cream window cell
                b = BUCKETS[(p, "atlas")]
                u0, v0, u1, v1 = ATLAS[cream()]
                idx, _ = b[1][-1]
                pts3 = [b[0][i] for i in idx]
                # order-independent mapping: lowest two verts = bottom
                uvs = []
                for q in pts3:
                    along = (q - o).dot(tdir)
                    uvs.append((u0 if along < 0 else u1, v0 if q.z < z + h / 2 else v1))
                b[1][-1] = (idx, uvs)


def chim(p, x, y, z0, z1, w=0.6, d=0.6, mat="brick"):
    chimney(p, x, y, z0, z1, w, d, mat)


# ===========================================================================
# WEST SIDE
# ===========================================================================
def build_nw1():
    p = "NW1"
    x0, x1, y0, y1 = fp(-25.1, -16.0, -214.5, -202.45)
    eave = G + 5.6
    rise = (x1 - x0) / 2 * TAN(33)
    gable_walls(p, "block", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "y", oe=0.3, og=0.2, top="sw:tin_dark")
    for yy in (y0 + 0.45, y1 - 0.45):
        chim(p, (x0 + x1) / 2, yy, eave + rise - 0.6, eave + rise + 0.8)
    ys = [y0 + (y1 - y0) * (i + 0.5) / 5 for i in range(5)]
    window(p, "door_brown", "+x", (x1, ys[2], G + 0.4), 1.1, 2.2)
    window(p, "small_window", "+x", (x1, ys[2], G + 2.68), 1.1, 0.42)
    wins(p, "+x", x1, [ys[0], ys[1], ys[3], ys[4]], G + 1.0, 0.95, 1.75)
    wins(p, "+x", x1, ys, G + 3.5, 0.95, 1.45)
    for a in ys:
        lintel(p, "+x", x1, a, G + 4.95, 0.95, mat="sw:stone_cream", hh=0.2)
    for a in (ys[0], ys[1], ys[3], ys[4]):
        lintel(p, "+x", x1, a, G + 2.75, 0.95, mat="sw:stone_cream", hh=0.2)
    # Capner St gable (south) and the north gable
    wins(p, "-y", y0, (-22.6, -18.5), G + 1.0, 0.95, 1.75)
    wins(p, "-y", y0, (-22.6, -18.5), G + 3.5, 0.95, 1.45)
    window(p, "attic_window", "-y", ((x0 + x1) / 2, y0, eave + 0.45), 0.7, 0.8)
    wins(p, "+y", y1, (-22.6, -18.5), G + 3.5, 0.95, 1.45)
    porch_g(p + "P", "+x", x1, 1.8, y0 + 0.4, y1 - 0.4, G + 0.45, G + 3.0, 5, kind="sq", pw=0.18,
            steps=(ys[2],), rise=0.3)
    # rear 1-storey stone part, plumber's annex and the "Storage" along Capner St
    shed(p, "block", "sw:tin_dark", -30.7, x0, 209.8, 214.5, G + 3.4, G + 2.6, "w", oe=0.2)
    a = "NW1A"
    ax0, ax1, ay0, ay1 = fp(-33.7, -25.1, -208.3, -202.6)
    e = G + 5.6
    r = (ay1 - ay0) / 2 * TAN(30)
    gable_walls(a, "clap", ax0, ax1, ay0, ay1, e, r, "x")
    gable_roof(a, ax0, ax1, ay0, ay1, e, r, "x", oe=0.3, og=0.2, top="sw:tin_dark")
    window(a, "door_brown", "-y", (-27.0, ay0, G + 0.1), 1.0, 2.2)
    wins(a, "-y", ay0, (-31.6, -29.3), G + 0.9, 0.9, 1.6)
    wins(a, "-y", ay0, (-31.6, -29.3, -27.0), G + 3.5, 0.9, 1.5)
    s = "NW1B"
    sx0, sx1, sy0, sy1 = fp(-57.3, -33.7, -209.3, -202.6)
    e = G + 5.8
    r = (sy1 - sy0) / 2 * TAN(28)
    gable_walls(s, "clap", sx0, sx1, sy0, sy1, e, r, "x")
    gable_roof(s, sx0, sx1, sy0, sy1, e, r, "x", oe=0.3, og=0.2, top="sw:tin_dark")
    window(s, "barn_doors", "-y", (-38.0, sy0, G), 2.6, 2.6)
    window(s, "barn_doors", "-y", (-47.0, sy0, G), 2.6, 2.6)
    wins(s, "-y", sy0, (-36.5, -41.0, -45.5, -50.0, -54.5), G + 3.6, 0.85, 1.4, cells=green)


def build_nw2():
    p = "NW2"
    x0, x1, y0, y1 = fp(-22.6, -16.0, -225.6, -216.0)
    eave = G + 6.0
    rise = (x1 - x0) / 2 * TAN(24)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "y", oe=0.55, og=0.45, top="slate")
    foundation(p, x0, x1, y0, y1, G + 0.55, ("e", "n", "s"), mat="concrete")
    # rear ell (L-plan), ridge across
    rx0, rx1, ry0, ry1 = fp(-28.9, -22.6, -221.6, -216.0)
    r2 = (ry1 - ry0) / 2 * TAN(24)
    gable_walls(p, "clap", rx0, rx1 + 0.4, ry0, ry1, G + 5.8, r2, "x")
    gable_roof(p, rx0, rx1 + 0.4, ry0, ry1, G + 5.8, r2, "x", oe=0.5, og=0.45, top="slate")
    chim(p, -20.6, (y0 + y1) / 2, eave + rise - 0.5, eave + rise + 0.9)
    ys = (217.9, 220.8, 223.7)
    window(p, "door_brown", "+x", (x1, ys[1], G + 0.55), 1.05, 2.3)
    wins(p, "+x", x1, (ys[0], ys[2]), G + 1.15, 0.95, 1.9)
    wins(p, "+x", x1, ys, G + 3.7, 0.95, 1.7)
    for a in (216.9, 218.8, 220.8, 222.8, 224.7):
        bracket(p + "P", "+x", x1, a, eave - 0.02, depth=0.5, h=0.45)
    wins(p, "+y", y1, (-20.6, -17.8), G + 1.15, 0.9, 1.8)
    wins(p, "+y", y1, (-20.6, -17.8), G + 3.7, 0.9, 1.6)
    wins(p, "-y", y0, (-20.6, -17.8), G + 3.7, 0.9, 1.6)
    window(p, "attic_window", "+y", ((x0 + x1) / 2, y1, eave + 0.2), 0.6, 0.65)
    window(p, "attic_window", "-y", ((x0 + x1) / 2, y0, eave + 0.2), 0.6, 0.65)
    # porch on round columns with a spindle frieze, wrapping the front and the north side
    porch_g(p + "P", "+x", x1, 2.3, y0 + 0.1, y1 + 1.8, G + 0.55, G + 3.25, 5, kind="col", pw=0.22,
            frieze=0.32, rail=True, steps=(ys[1],), rise=0.3)
    porch_g(p + "P", "+y", y1, 1.8, -20.2, x1, G + 0.55, G + 3.25, 2, kind="col", pw=0.22,
            frieze=0.32, rail=True, rise=0.3, skip_end_wall=(1,))


def build_nw3():
    p = "NW3"
    x0, x1, y0, y1 = fp(-29.2, -18.9, -239.1, -230.5)
    eave = G + 6.4
    rise = (y1 - y0) / 2 * TAN(42)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.45, og=0.55, t=0.2, top="slate")
    foundation(p, x0, x1, y0, y1, G + 0.6, ("e", "s"), mat="concrete")
    # north part (cross gable facing north)
    nx0, nx1, ny0, ny1 = fp(-25.4, -18.9, -244.2, -239.1)
    nr = (nx1 - nx0) / 2 * TAN(42)
    gable_walls(p, "clap", nx0, nx1, ny0 - 0.5, ny1, eave, nr, "y")
    gable_roof(p, nx0, nx1, ny0 - 1.2, ny1, eave, nr, "y", oe=0.45, og=0.45, t=0.2, top="slate")
    foundation(p, nx0, nx1, ny0, ny1, G + 0.6, ("e", "n"), mat="concrete")
    # rear 1-storey part
    shed(p, "clap", "sw:tin_dark", -31.8, x0, 230.5, 235.0, G + 3.3, G + 2.6, "w", oe=0.2)
    chim(p, -24.0, (y0 + y1) / 2, eave + rise - 1.4, eave + rise + 0.8)
    # bracketed raking cornice on the front gable (1913)
    ym, hh = (y0 + y1) / 2, (y1 - y0) / 2
    for f in (0.04, 0.38, 0.7):
        for s in (-1, 1):
            yy = ym + s * hh * (1 - f)
            bracket(p + "P", "+x", x1, yy, eave + rise * f - 0.05, depth=0.5, h=0.55, w=0.1)
    # front: door + window below (under the porch), two windows above, attic window
    window(p, "door_green", "+x", (x1, 235.0, G + 0.6), 1.05, 2.35)
    wins(p, "+x", x1, (232.4,), G + 1.2, 0.95, 2.0, hood=True, shut=True)
    wins(p, "+x", x1, (232.4, 236.9), G + 3.9, 0.95, 1.85, hood=True, shut=True)
    wins(p, "+x", x1, (ym,), eave + 0.55, 0.8, 1.3, hood=True)
    wins(p, "+x", x1, (241.7,), G + 1.2, 0.95, 2.0, hood=True)
    wins(p, "+x", x1, (241.7,), G + 3.9, 0.95, 1.85, hood=True, shut=True)
    # south side (faces the walk limit) and the north gable
    wins(p, "-y", y0, (-21.2, -24.1, -27.0), G + 1.2, 0.95, 2.0, hood=True, shut=True)
    wins(p, "-y", y0, (-21.2, -24.1, -27.0), G + 3.9, 0.95, 1.85, hood=True, shut=True)
    wins(p, "+y", ny1, (-23.6, -20.7), G + 3.9, 0.9, 1.8, hood=True, shut=True)
    wins(p, "+y", ny1, (-23.6, -20.7), G + 1.2, 0.9, 1.9, hood=True)
    window(p, "attic_window", "+y", ((nx0 + nx1) / 2, ny1, eave + 0.4), 0.6, 0.8)
    wins(p, "+y", y1, (-27.4,), G + 3.9, 0.9, 1.8, hood=True)
    # arcaded porch: front and the NE corner pavilion to x -14.7 (map)
    porch_g(p + "P", "+x", x1, 2.1, 230.6, 240.5, G + 0.6, G + 3.35, 4, kind="flat", arch="pointed", rail=True,
            steps=(235.0,), ends=(0,), side_bays=1, skip_end_wall=(1,))
    porch_g(p + "P", "+x", x1, 4.2, 240.5, 244.1, G + 0.6, G + 3.35, 2, kind="flat", arch="pointed", rail=True,
            ends=(0, 1), side_bays=2, skip_end_wall=(0,))
    # garden urn on a pedestal (1913)
    u = "NW3U"
    ux, uy = -13.0, 233.0
    box(u, "sw:paint_white", ux - 0.24, ux + 0.24, uy - 0.24, uy + 0.24, 0.0, G + 0.85, sides=("t", "n", "s", "e", "w"))
    rings = [(0.12, G + 0.85), (0.3, G + 1.12), (0.36, G + 1.35), (0.28, G + 1.5)]
    rr = [ring(ux, uy, r, 8, z) for r, z in rings]
    for b, t in zip(rr, rr[1:]):
        prism(u, "sw:paint_white", b, t)
    face_out(u, "sw:iron_dark", rr[-1], UP)


def build_nw4():
    p = "NW4"
    eave = G + 6.6
    # south wing, gable to the street (the cream gable left of the turret in the 1913 card)
    x0, x1, y0, y1 = fp(-31.2, -20.5, -256.8, -249.5)
    rise = (y1 - y0) / 2 * TAN(45)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.4, og=0.4, top="slate")
    foundation(p, x0, x1, y0, y1, G + 0.6, ("e", "s"), mat="concrete")
    # north wing (gable to the north), its front 2 m back
    nx0, nx1, ny0, ny1 = fp(-31.2, -22.5, -263.3, -256.8)
    nr = (nx1 - nx0) / 2 * TAN(40)
    gable_walls(p, "clap", nx0, nx1, ny0 - 0.5, ny1, eave, nr, "y")
    gable_roof(p, nx0, nx1, ny0 - 0.6, ny1, eave, nr, "y", oe=0.4, og=0.4, top="slate")
    foundation(p, nx0, nx1, ny0, ny1, G + 0.6, ("e", "n"), mat="concrete")
    chim(p, -27.5, 256.8, eave + 2.4, eave + nr + 1.0)
    # square tower over the entrance (north of the gable: right of it in the 1913 and 1908
    # cards), steep pyramid roof, finial
    t = "NW4T"
    tx0, tx1, ty0, ty1 = -23.3, -20.3, 256.8, 259.8
    tz = G + 9.4
    box(t, "clap", tx0, tx1, ty0, ty1, 0.0, tz, sides=("n", "s", "e", "w"))
    box(t, "sw:paint_white", tx0 - 0.08, tx1 + 0.08, ty0 - 0.08, ty1 + 0.08, tz - 0.3, tz,
        sides=("n", "s", "e", "w"))
    o = 0.32
    base = [Vector((tx0 - o, ty0 - o, tz)), Vector((tx1 + o, ty0 - o, tz)), Vector((tx1 + o, ty1 + o, tz)),
            Vector((tx0 - o, ty1 + o, tz))]
    apex = Vector(((tx0 + tx1) / 2, (ty0 + ty1) / 2, tz + 4.6))
    pyramid(t + "R", "slate", base, apex)
    face_out(t, "sw:paint_white", base, (0, 0, -1))
    box(t, "sw:iron_dark", apex.x - 0.05, apex.x + 0.05, apex.y - 0.05, apex.y + 0.05, apex.z - 0.2, apex.z + 0.9,
        sides=("n", "s", "e", "w"))
    tm = (ty0 + ty1) / 2
    wins(t, "+x", tx1, (tm,), G + 3.9, 0.85, 1.75, hood=True)
    wins(t, "+x", tx1, (tm,), G + 7.0, 0.75, 1.4, hood=True)
    wins(t, "+y", ty1, (-21.8,), G + 7.0, 0.7, 1.4, hood=True)
    wins(t, "-y", ty0, (-21.8,), G + 7.0, 0.7, 1.4, hood=True)
    window(t, "door_green", "+x", (tx1, tm, G + 0.6), 1.05, 2.4)
    # 2-storey canted bays: front (gable wing) and south side
    canted_bay(p, "clap", "+x", x1, (y0 + y1) / 2, 2.8, 0.85, 0.0, G + 6.1,
               win=[(G + 1.25, 1.9), (G + 3.9, 1.75)])
    canted_bay(p, "clap", "-y", y0, -26.4, 3.0, 0.85, 0.0, G + 6.1,
               win=[(G + 1.25, 1.9), (G + 3.9, 1.75)])
    wins(p, "+x", x1, ((y0 + y1) / 2,), eave + 0.6, 0.8, 1.2, hood=True)
    wins(p, "-y", y0, (-22.4, -29.9), G + 3.9, 0.85, 1.75, hood=True, shut=True)
    wins(p, "-y", y0, (-22.4, -29.9), G + 1.25, 0.85, 1.9, hood=True)
    wins(p, "+x", nx1, (262.0,), G + 3.9, 0.85, 1.75, hood=True, shut=True)
    wins(p, "+x", nx1, (262.0,), G + 1.25, 0.85, 1.9, hood=True)
    wins(p, "+y", ny1, (-29.0, -24.8), G + 1.25, 0.85, 1.9, hood=True)
    wins(p, "+y", ny1, (-29.0, -24.8), G + 3.9, 0.85, 1.75, hood=True, shut=True)
    window(p, "attic_window", "+y", ((nx0 + nx1) / 2, ny1, eave + 0.5), 0.6, 0.9)
    # wide arcaded porch in front of the north wing and the tower, wrapping the NE corner
    porch_g(p + "P", "+x", nx1, 5.5, 256.8, 263.2, G + 0.6, G + 3.4, 4, kind="flat", arch="pointed", rail=True,
            steps=(261.6,), ends=(1,), side_bays=2, rise=0.35)


def build_nw5():
    p = "NW5"
    x0, x1, y0, y1 = fp(-40.8, -29.3, -306.3, -293.8)
    eave = G + 7.3
    rise = (x1 - x0) / 2 * TAN(40)
    s = rise / ((x1 - x0) / 2)
    gable_walls(p, "brick", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "y", oe=0.4, og=0.3, top="slate", t=0.18)
    box(p, "sw:paint_cream", x0 - 0.12, x1 + 0.12, y0 - 0.06, y1 + 0.06, eave - 0.35, eave,
        sides=("e", "w", "n", "s"))                                                  # pale cornice band
    foundation(p, x0, x1, y0, y1, G + 0.75, ("e", "n", "s"), mat="concrete")
    ys = [y0 + (y1 - y0) * (i + 0.5) / 5 for i in range(5)]
    window(p, "door_green", "+x", (x1, ys[2], G + 0.75), 1.25, 2.55, off=0.035)
    face_out(p + "T", "sw:paint_cream", [(x1 + 0.05, ys[2] - 1.0, G + 3.45), (x1 + 0.05, ys[2] + 1.0, G + 3.45),
                                         (x1 + 0.05, ys[2], G + 4.05)], (1, 0, 0))   # door pediment
    wins(p, "+x", x1, [ys[0], ys[1], ys[3], ys[4]], G + 1.25, 1.05, 2.15, cells=green, frame_=True)
    wins(p, "+x", x1, ys, G + 4.4, 1.05, 1.95, cells=green, frame_=True)
    # central gambrel gable with a Palladian window
    cy, gw = ys[2], 2.7
    prof = [(-gw, 0.0), (-gw + 0.55, 1.75), (0.0, 2.9), (gw - 0.55, 1.75), (gw, 0.0)]
    face_out(p, "brick", [(x1, cy + u, eave + v) for u, v in prof], (1, 0, 0))
    depth = 2.9 / s + 0.4
    for (u0, v0), (u1, v1) in zip(prof, prof[1:]):
        ov = 0.35
        a = Vector((x1 + ov, cy + u0 * 1.06, eave + v0 - 0.05))
        b = Vector((x1 + ov, cy + u1 * 1.06, eave + v1 - 0.05))
        face_out(p + "R", "slate", [a, b, b - Vector((depth + ov, 0, 0)), a - Vector((depth + ov, 0, 0))],
                 (0.2, (u0 + u1) / 2 * 0.3, 1.0))
        face_out(p + "R", "sw:paint_white", [a, b, b + Vector((0, 0, -0.16)), a + Vector((0, 0, -0.16))], (1, 0, 0))
    window(p, "win_green_2", "+x", (x1, cy, eave + 0.35), 0.8, 1.35, off=0.035)
    arch = [(cy + 0.4 * math.cos(math.pi * k / 6), eave + 1.7 + 0.4 * math.sin(math.pi * k / 6)) for k in range(7)]
    face_out(p, "sw:iron_dark", [(x1 + 0.035, a_, z_) for a_, z_ in arch], (1, 0, 0))
    wins(p, "+x", x1, (cy - 0.85, cy + 0.85), eave + 0.35, 0.42, 1.15, cells="win_green_5")
    face_out(p + "T", "sw:stone_cream",
             [(x1 + 0.02, cy - 1.2, eave + 0.2), (x1 + 0.02, cy + 1.2, eave + 0.2), (x1 + 0.02, cy + 1.2, eave + 1.6),
              (x1 + 0.02, cy + 0.6, eave + 1.6)] + [(x1 + 0.02, cy + 0.55 * math.cos(math.pi * k / 6),
                                                     eave + 1.7 + 0.55 * math.sin(math.pi * k / 6)) for k in range(1, 6)]
             + [(x1 + 0.02, cy - 0.6, eave + 1.6), (x1 + 0.02, cy - 1.2, eave + 1.6)], (1, 0, 0))
    # two dormers on the front slope
    for dy in (ys[0] + 0.4, ys[4] - 0.4):
        d0, wd, hh = 1.1, 0.75, 1.25
        xf = x1 - d0
        zb = eave + d0 * s
        fr = [(xf, dy - wd, zb), (xf, dy + wd, zb), (xf, dy + wd, zb + hh), (xf, dy, zb + hh + 0.55),
              (xf, dy - wd, zb + hh)]
        face_out(p, "sw:paint_white", fr, (1, 0, 0))
        back_e = xf - hh / s
        for sg in (-1, 1):
            face_out(p, "sw:paint_white", [(xf, dy + sg * wd, zb), (xf, dy + sg * wd, zb + hh),
                                           (back_e, dy + sg * wd, zb + hh)], (0, sg, 0))
        back_r = xf - (hh + 0.55) / s
        for sg in (-1, 1):
            face_out(p + "R", "slate", [(xf + 0.18, dy + sg * (wd + 0.15), zb + hh - 0.1), (xf + 0.18, dy, zb + hh + 0.6),
                                        (back_r, dy, zb + hh + 0.6), (back_e, dy + sg * (wd + 0.15), zb + hh - 0.1)],
                     (0.3, sg, 1))
        window(p, "win_green_1", "+x", (xf, dy, zb + 0.15), 0.8, 1.0)
    # south gable: semicircular 2-storey bay with a balcony rail, windows, arched attic window
    cxb, rb, db = -37.35, 3.15, 2.6
    zt = G + 6.7
    seg = 7
    arc_pts = [Vector((cxb + rb * math.cos(math.pi * k / seg), y0 - db * math.sin(math.pi * k / seg), 0))
               for k in range(seg + 1)]
    for k, (A, B) in enumerate(zip(arc_pts, arc_pts[1:])):
        nrm = ((A + B) / 2 - Vector((cxb, y0, 0))) * Vector((1, 1, 0))
        face_out(p, "brick", [A, B, B + UP * zt, A + UP * zt], nrm)
        if k in (1, 3, 5):
            c = (A + B) / 2 + nrm.normalized() * 0.03
            tdir = (B - A).normalized()
            for z, h in ((G + 1.25, 2.0), (G + 4.4, 1.85)):
                q = [c - tdir * 0.5 + UP * z, c + tdir * 0.5 + UP * z, c + tdir * 0.5 + UP * (z + h),
                     c - tdir * 0.5 + UP * (z + h)]
                u0, v0, u1, v1 = ATLAS["win_green_%d" % k]
                face_out(p, "atlas", q, nrm, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    top = [a + UP * zt for a in arc_pts]
    face_out(p, "sw:tin_dark", top, UP)
    cap = [Vector((cxb + (rb + 0.12) * math.cos(math.pi * k / seg), y0 - (db + 0.12) * math.sin(math.pi * k / seg),
                   zt)) for k in range(seg + 1)]
    for A, B, a_, b_ in zip(cap, cap[1:], arc_pts, arc_pts[1:]):
        nrm = ((A + B) / 2 - Vector((cxb, y0, zt))) * Vector((1, 1, 0))
        face_out(p + "T", "sw:paint_cream", [A - UP * 0.3, B - UP * 0.3, B, A], nrm)
        u0, v0, u1, v1 = ATLAS["pickets"]
        L = (B - A).length
        face_out(p + "T", "atlas", [A, B, B + UP * 0.75, A + UP * 0.75], nrm, [(0, v0), (L / 1.6, v0), (L / 1.6, v1), (0, v1)])
    wins(p, "-y", y0, (-31.3,), G + 1.25, 1.0, 2.0, cells=green, frame_=True)
    wins(p, "-y", y0, (-31.3,), G + 4.4, 1.0, 1.85, cells=green, frame_=True)
    gx = (x0 + x1) / 2
    window(p, "win_green_6", "-y", (gx, y0, eave + 0.5), 0.9, 1.3, off=0.035)
    face_out(p, "sw:paint_cream", [(gx + 0.6 * math.cos(math.pi * k / 6), y0 - 0.03, eave + 1.8 + 0.6 * math.sin(math.pi * k / 6))
                                   for k in range(7)] + [(gx - 0.6, y0 - 0.03, eave + 1.8), (gx + 0.6, y0 - 0.03, eave + 1.8)][:0],
             (0, -1, 0))
    # pair of tall stepped chimneys on the south gable (1914)
    for cx in (gx - 0.9, gx + 0.9):
        chim(p, cx, y0 + 0.4, eave + rise - 1.2, eave + rise + 2.2, w=0.7, d=0.6)
    box(p, "brick", gx - 1.25, gx + 1.25, y0 + 0.1, y0 + 0.7, eave + rise - 0.6, eave + rise + 0.6,
        sides=("t", "n", "s", "e", "w"))
    # north gable windows
    wins(p, "+y", y1, (-38.2, -32.0), G + 4.4, 1.0, 1.85, cells=green, frame_=True)
    window(p, "win_green_4", "+y", (gx, y1, eave + 0.5), 0.9, 1.3, off=0.035)
    # rear part (brick 1st, frame 2nd), low hip
    r = "NW5R"
    rx0, rx1, ry0, ry1 = fp(-50.4, -40.8, -302.7, -291.5)
    box(r, "brick", rx0, rx1, ry0, ry1, 0.0, G + 3.4, sides=("n", "s", "w"))
    box(r, "clap", rx0, rx1, ry0, ry1, G + 3.4, G + 6.3, sides=("n", "s", "w"))
    hip_roof(r, "slate", rx0, rx1, ry0, ry1, G + 6.3, 2.2, oe=0.3)
    wins(r, "-y", ry0, (-48.0, -44.0), G + 3.9, 0.9, 1.6, cells=green)
    wins(r, "-y", ry0, (-48.0, -44.0), G + 1.1, 0.9, 1.8, cells=green)
    # wrap porch on slender columns with balusters: front to x -25.3 and the north side to -308.4
    porch_g(p + "P", "+x", x1, 4.0, 295.0, 308.4, G + 0.75, G + 4.0, 6, kind="col", pw=0.3, rail=True,
            steps=(ys[2],), rise=0.35, skip_end_wall=(1,))
    porch_g(p + "P", "+y", y1, 2.1, -38.0, -29.3, G + 0.75, G + 4.0, 3, kind="col", pw=0.3, rail=True,
            rise=0.3, skip_end_wall=(1,))
    box(p + "P", "sw:paint_white", x1, x1 + 4.18, 295.0 - 0.12, 308.4 + 0.12, G + 3.75, G + 4.0,
        sides=("e", "n", "s"))                                                         # porch entablature
    # porte-cochere: diagonal strip at the SE corner, gable along it, pediment on the outer end
    A_, B_, C_, D_ = Vector((-29.3, 295.0)), Vector((-23.1, 290.5)), Vector((-26.4, 287.2)), Vector((-31.5, 292.0))
    m0, m1 = (A_ + D_) / 2, (B_ + C_) / 2
    u = (m1 - m0).normalized()
    v = Vector((-u.y, u.x))
    hw = 2.0
    zc, zr = G + 4.0, G + 5.35

    def W(t, sv, z):
        q = m0 + u * t + v * sv
        return Vector((q.x, q.y, z))
    L = (m1 - m0).length
    t0 = -1.5                                      # run the roof back into the house / porch corner
    pc = p + "C"
    for t in (0.6, L - 0.25):
        for sv in (-hw + 0.25, hw - 0.25):
            q = W(t, sv, 0)
            prism(pc, "sw:paint_white", ring(q.x, q.y, 0.17, 6, G), ring(q.x, q.y, 0.15, 6, zc - 0.35))
    for sv in (-hw, hw):
        face_out(pc, "sw:paint_white", [W(t0, sv, zc - 0.4), W(L, sv, zc - 0.4), W(L, sv, zc), W(t0, sv, zc)],
                 (v.x * sv, v.y * sv, 0))
    face_out(pc, "sw:paint_white", [W(t0, -hw, zc - 0.4), W(L, -hw, zc - 0.4), W(L, hw, zc - 0.4),
                                    W(t0, hw, zc - 0.4)], (0, 0, -1))
    face_out(pc, "sw:paint_white", [W(L, -hw, zc - 0.4), W(L, hw, zc - 0.4), W(L, hw, zc), W(L, -hw, zc)], (u.x, u.y, 0))
    face_out(pc, "sw:paint_white", [W(L, -hw, zc), W(L, hw, zc), W(L, 0, zr)], (u.x, u.y, 0))   # pediment
    for sv in (-1, 1):
        slab(pc, "slate", "sw:paint_white", [W(t0, sv * (hw + 0.2), zc - 0.05), W(t0, 0, zr + 0.05),
                                             W(L + 0.2, 0, zr + 0.05), W(L + 0.2, sv * (hw + 0.2), zc - 0.05)], 0.14)


# ===========================================================================
# EAST SIDE
# ===========================================================================
def build_ne1():
    p = "NE1"
    x0, x1, y0, y1 = fp(15.9, 21.9, -209.1, -200.4)
    box(p, "brick", x0, x1, y0, y1, 0.0, G + 3.4, sides=("n", "s", "w"))
    box(p + "I", "clap", x0, x1, y0, y1, G + 3.4, G + 6.3, sides=("n", "s", "w", "e"))
    box(p, "sw:paint_white", x0 - 0.3, x1 + 0.05, y0 - 0.3, y1 + 0.3, G + 6.3, G + 6.75,
        sides=("t", "n", "s", "w", "b"), top="sw:tin_dark")
    shed(p + "I", "clap", "sw:tin_dark", x1, 23.7, 203.8, 208.7, G + 3.3, G + 2.7, "e", oe=0.2)
    window(p, "door_brown", "-x", (x0, 202.8, G + 0.45), 1.0, 2.3)
    wins(p, "-x", x0, (206.9,), G + 1.0, 1.0, 1.9, cells=green)
    wins(p + "I", "-x", x0, (202.0, 204.75, 207.5), G + 4.0, 0.9, 1.6, cells=green)
    wins(p + "I", "+y", y1, (17.6, 20.2), G + 4.0, 0.9, 1.6, cells=green)
    wins(p, "+y", y1, (17.6, 20.2), G + 1.0, 0.9, 1.8, cells=green)
    wins(p + "I", "-y", y0, (17.6, 20.2), G + 4.0, 0.9, 1.6, cells=green)
    porch_g(p + "P", "-x", x0, 2.0, 200.5, 205.2, G + 0.45, G + 3.0, 2, kind="sq", steps=(202.8,), rise=0.25)


def build_ne2():
    p = "NE2"
    x0, x1, y0, y1 = fp(15.9, 23.7, -223.0, -209.1)
    top = G + 10.2
    box(p, "brick", x0, x1, y0, y1, 0.0, top, sides=("n", "s", "e", "w"))
    hip_roof(p, "slate", x0, x1, y0, y1, top, 1.7, oe=0.45)
    chim(p, 20.5, 214.0, top + 0.6, top + 2.2)
    ys = [y0 + (y1 - y0) * (i + 0.5) / 5 for i in range(5)]
    window(p, "door_brown", "-x", (x0, ys[2], G + 0.9), 1.1, 2.3)
    wins(p, "-x", x0, (ys[0], ys[1], ys[3], ys[4]), G + 1.5, 0.95, 1.9)
    for z, h in ((G + 4.5, 1.85), (G + 7.6, 1.7)):
        wins(p, "-x", x0, ys, z, 0.95, h)
        for a in ys:
            lintel(p, "-x", x0, a, z + h, 0.95)
    wins(p, "+y", y1, (17.6, 20.0, 22.3), G + 1.5, 0.9, 1.8)
    wins(p, "+y", y1, (17.6, 20.0, 22.3), G + 4.5, 0.9, 1.8)
    wins(p, "+y", y1, (17.6, 20.0, 22.3), G + 7.6, 0.9, 1.7)
    wins(p, "-y", y0, (17.6, 20.0, 22.3), G + 7.6, 0.9, 1.7)
    porch_g(p + "P", "-x", x0, 2.0, y0 + 0.1, y1 - 0.1, G + 0.9, G + 3.9, 5, kind="sq", steps=(ys[2],),
            rail=True, rise=0.3)
    r = "NE2R"
    shed(r, "clap", "sw:tin_dark", x1, 29.9, 210.8, 217.4, G + 6.3, G + 5.5, "e", oe=0.25)
    shed(r, "clap", "sw:tin_dark", 29.9, 37.4, 210.8, 217.4, G + 3.2, G + 2.6, "e", oe=0.25)
    wins(r, "+y", 217.4, (25.5, 28.5), G + 3.8, 0.85, 1.5)


def build_ne3():
    p = "NE3"
    x0, x1, y0, y1 = fp(16.2, 30.8, -237.5, -229.7)
    eave = G + 6.0
    rise = (y1 - y0) / 2 * TAN(35)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.35, og=0.3, top="slate")
    foundation(p, x0, x1, y0, y1, G + 0.55, ("w", "s", "n"), mat="concrete")
    wx0, wx1, wy0, wy1 = 22.6, 27.7, 237.5 - 0.5, 240.0
    wr = (wx1 - wx0) / 2 * TAN(35)
    gable_walls(p, "clap", wx0, wx1, wy0, wy1, eave - 0.3, wr, "y")
    gable_roof(p, wx0, wx1, wy0 - 0.6, wy1, eave - 0.3, wr, "y", oe=0.3, og=0.3, top="slate")
    shed(p, "clap", "sw:tin_dark", x1, 33.5, 230.5, 236.7, G + 3.1, G + 2.5, "e", oe=0.2)
    chim(p, 24.0, (y0 + y1) / 2, eave + rise - 0.6, eave + rise + 0.8)
    window(p, "door_brown", "-x", (x0, 235.4, G + 0.55), 1.0, 2.3)
    wins(p, "-x", x0, (231.6,), G + 1.15, 0.95, 1.85)
    wins(p, "-x", x0, (231.6, 235.4), G + 3.7, 0.95, 1.7)
    window(p, "attic_window", "-x", (x0, (y0 + y1) / 2, eave + 0.3), 0.6, 0.85)
    wins(p, "-y", y0, (18.6, 23.0, 27.5), G + 1.15, 0.9, 1.8)
    wins(p, "-y", y0, (18.6, 23.0, 27.5), G + 3.7, 0.9, 1.7)
    wins(p, "+y", y1, (18.6, 20.8), G + 3.7, 0.9, 1.7)
    wins(p, "+y", wy1, (25.15,), G + 3.5, 0.9, 1.6)
    porch_g(p + "P", "-x", x0, 2.0, y0 + 0.1, y1 - 0.1, G + 0.55, G + 3.2, 4, kind="sq", steps=(235.4,),
            rise=0.3)


def build_ne4():
    p = "NE4"
    x0, x1, y0, y1 = fp(16.0, 28.2, -255.2, -246.7)
    eave = G + 7.0
    rise = (y1 - y0) / 2 * TAN(25)
    gable_walls(p, "brick", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.65, og=0.6, t=0.3, top="slate")
    shed(p, "brick", "sw:tin_dark", x1, 31.7, 250.6, 255.2, G + 3.4, G + 2.8, "e", oe=0.2)
    # south 2-storey bay
    box(p, "brick", 20.2, 23.1, 245.7, y0, 0.0, G + 6.0, sides=("s", "e", "w"))
    slab(p, "sw:tin_dark", "sw:paint_white", [(20.0, 245.5, G + 6.0), (23.3, 245.5, G + 6.0), (23.3, y0, G + 6.0),
                                              (20.0, y0, G + 6.0)], 0.2)
    wins(p, "-y", 245.7, (21.65,), G + 1.2, 0.85, 2.2, cells=green)
    wins(p, "-y", 245.7, (21.65,), G + 4.0, 0.85, 1.9, cells=green)
    chim(p, 25.5, y0 + 0.6, eave + 0.6, eave + rise + 1.0)
    # paired brackets under the south eave (faces the walk limit) and at the front eave returns
    for xb in (18.0, 25.5):
        for d in (-0.2, 0.2):
            bracket(p + "P", "-y", y0, xb + d, eave - 0.02, depth=0.62, h=0.7, w=0.12)
    window(p, "door_brown", "-x", (x0, 253.4, G + 0.6), 1.05, 2.5)
    wins(p, "-x", x0, (248.3, 250.6), G + 1.2, 0.8, 2.3, cells=green)
    wins(p, "-x", x0, (248.3, 250.95, 253.6), G + 4.0, 0.8, 2.0, cells=green)
    window(p, "attic_window", "-x", (x0, (y0 + y1) / 2, eave + 0.2), 0.6, 0.9)
    wins(p, "-y", y0, (17.6, 26.5), G + 1.2, 0.8, 2.2, cells=green)
    wins(p, "-y", y0, (17.6, 26.5), G + 4.0, 0.8, 1.9, cells=green)
    wins(p, "+y", y1, (18.3, 21.5, 25.6), G + 4.0, 0.8, 1.9, cells=green)
    porch_g(p + "P", "-x", x0, 1.3, y0 + 0.1, y1, G + 0.6, G + 3.3, 3, kind="sq", arch="round", arch_h=0.45,
            steps=(253.4,), rise=0.25, skip_end_wall=(1,))
    porch_g(p + "P", "+y", y1, 1.3, x0 - 1.3, 23.0, G + 0.6, G + 3.3, 3, kind="sq", arch="round", arch_h=0.45,
            rise=0.25)


def build_ne5():
    """built square to the axes (front at x 19.9, Blender y 271.5 .. 285.4), then turned 11.2 deg
    about the front-south corner to the bend of the street line"""
    p = "NE5"
    x0, x1, y0, y1 = 19.9, 28.9, 271.5, 285.4
    eave = G + 7.0
    rise = (x1 - x0) / 2 * TAN(26)
    gable_walls(p, "stucco", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "y", oe=0.8, og=0.7, t=0.2, top="slate")
    foundation(p, x0, x1, y0, y1, G + 0.6, ("w", "n", "s"), mat="concrete")
    cross_gable(p, "stucco", "w", (y0 + y1) / 2, 4.4, x0, eave, 1.55, rise / ((x1 - x0) / 2), oe=0.6, t=0.2)
    # rear stem of the T and the frame ell
    gable_walls(p, "stucco", x1 - 0.5, 35.5, 273.4, 279.6, eave - 0.6, 3.1 * TAN(26), "x")
    gable_roof(p, x1 - 0.5, 35.5, 273.4, 279.6, eave - 0.6, 3.1 * TAN(26), "x", oe=0.6, og=0.5, t=0.2, top="slate")
    shed(p + "E", "clap", "sw:tin_dark", 35.5, 39.7, 274.0, 279.0, G + 5.6, G + 4.8, "e", oe=0.25)
    for yc in (275.9, 281.0):
        chim(p, 24.4, yc, eave + rise - 0.5, eave + rise + 1.1)
    # wide bracketed eaves: brackets along the front eave and the cross gable
    for yb in (272.0, 274.2, 276.0, 280.8, 282.6, 284.9):
        bracket(p + "P", "-x", x0, yb, eave - 0.02, depth=0.75, h=0.6, w=0.13)
    ys = [y0 + (y1 - y0) * (i + 0.5) / 5 for i in range(5)]
    window(p, "door_brown", "-x", (x0, ys[2], G + 0.6), 1.15, 2.5)
    wins(p, "-x", x0, (ys[0], ys[1], ys[3], ys[4]), G + 1.15, 0.95, 2.2, cells=green, shut=True)
    wins(p, "-x", x0, ys, G + 4.2, 0.95, 1.95, cells=green, shut=True)
    wins(p, "-x", x0, (ys[2],), eave + 0.2, 0.8, 0.9, cells="attic_window")
    # 2-storey canted bay on the south side, windows on both sides
    canted_bay(p, "stucco", "-y", y0, 24.4, 3.2, 0.95, 0.0, G + 6.2, win=[(G + 1.15, 2.1), (G + 4.2, 1.85)])
    wins(p, "-y", y0, (21.3, 27.6), G + 4.2, 0.9, 1.8, cells=green)
    wins(p, "+y", y1, (21.6, 24.4, 27.2), G + 1.15, 0.9, 2.1, cells=green)
    wins(p, "+y", y1, (21.6, 24.4, 27.2), G + 4.2, 0.9, 1.85, cells=green)
    window(p, "attic_window", "+y", ((x0 + x1) / 2, y1, eave + 0.4), 0.7, 0.9)
    window(p, "attic_window", "-y", ((x0 + x1) / 2, y0, eave + 0.4), 0.7, 0.9)
    # 3-bay arcaded porch, chamfered posts on pedestals
    porch_g(p + "P", "-x", x0, 2.0, 274.3, 282.6, G + 0.6, G + 3.6, 3, kind="chamf", pw=0.22, arch="round",
            arch_h=0.55, steps=(ys[2],), rise=0.3)


def turn_ne5():
    th = math.radians(-11.2)
    c, s = math.cos(th), math.sin(th)
    px, py = 19.9, 271.5
    for (part, mat), (verts, faces) in BUCKETS.items():
        if not part.startswith("NE5"):
            continue
        for v in verts:
            dx, dy = v.x - px, v.y - py
            v.x, v.y = px + dx * c - dy * s, py + dx * s + dy * c


def ne5_point(dx, dy):
    """scene (x, z) of a point given in NE5's square frame (Blender dx, dy from the pivot)"""
    th = math.radians(-11.2)
    c, s = math.cos(th), math.sin(th)
    return (19.9 + dx * c - dy * s, -(271.5 + dx * s + dy * c))


# ===========================================================================
# OUTBUILDINGS (PLAN.md "Rough-spot fixes" R-a, 2026-11-12). Footprints: Sept 1921 sheet 2 (east,
# +-0.5 m) and sheet 6 (west, +-2.5 m). Plain massing: weathered clapboard, 35 deg gable with the
# ridge along the long side, 0.25 m eaves, slate-grey or brown-shingle roof, one dark door on the
# side facing the house. Heights GUESS (1 storey 2.6 m eave, 1 1/2 = 3.6 m, 2 = 5.2 m).
# ===========================================================================
OUT_EAVE = {1: 2.6, 1.5: 3.6, 2: 5.2}
OUT_ROOF = {"grey": (0.62, 0.62, 0.66), "brown": (0.82, 0.70, 0.58)}
OUT_WALL = [(0.42, 0.37, 0.31), (0.38, 0.36, 0.32), (0.45, 0.40, 0.33), (0.40, 0.37, 0.34)]   # weathered grey-brown
OUT_TINTS = {}      # (part, final material) -> Tint, merged into the bake's TINTS
OUT_BOXES = []      # Blender (x0, x1, y0, y1) per outbuilding, for the bake's lightmap density
TO_HOUSE = {"E": Vector((-1, 0)), "W": Vector((1, 0)), "S": Vector((0, -1))}   # Blender XY


def rect_b(x0, x1, z0, z1):
    """scene ranges -> Blender XY corners (counter-clockwise)"""
    return [Vector((x0, -z1)), Vector((x1, -z1)), Vector((x1, -z0)), Vector((x0, -z0))]


def turned_b(x0, x1, z0, z1, deg):
    """rectangle turned by deg (Blender, about Z) whose bounding box is the given scene ranges"""
    W, H = x1 - x0, z1 - z0
    c, s = math.cos(math.radians(abs(deg))), math.sin(math.radians(abs(deg)))
    w, h = (W * c - H * s) / (c * c - s * s), (H * c - W * s) / (c * c - s * s)
    m = Vector(((x0 + x1) / 2, -(z0 + z1) / 2))
    th = math.radians(deg)
    rot = lambda v: Vector((v.x * math.cos(th) - v.y * math.sin(th), v.x * math.sin(th) + v.y * math.cos(th)))
    return [m + rot(Vector((sx * w / 2, sy * h / 2))) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def outb(p, corners, storeys, kind="gable", door="E", cell="door_brown", dw=1.0, dh=2.0, wall="clap",
         roof="slate", roof_tint="grey", wall_tint=None, pitch=35.0, eave=None, hi=None, gable_mat=None,
         under="sw:wood_grey", oe=0.25):
    """one outbuilding from four Blender XY corners (any rectangle-ish quad, in order).
    kind 'gable' (ridge along the long side) or 'lean' (one slope, falling to the -v long side).
    Returns Q(a, b, z) in the box's own frame (a along the ridge, b across) for extra details."""
    A, B, C, D = corners
    e1, e2 = (B - A + C - D) / 2, (C - B + D - A) / 2
    if e1.length >= e2.length:
        u, L, W = e1.normalized(), e1.length, e2.length
    else:
        u, L, W = e2.normalized(), e2.length, e1.length
    v = Vector((-u.y, u.x))
    m = (A + B + C + D) / 4
    U3, V3 = Vector((u.x, u.y, 0)), Vector((v.x, v.y, 0))

    def Q(a, b, z):
        q = m + u * a + v * b
        return Vector((q.x, q.y, z))
    z_e = G + (eave if eave is not None else OUT_EAVE[storeys])
    xs = [q.x for q in corners]
    ys = [q.y for q in corners]
    OUT_BOXES.append((min(xs), max(xs), min(ys), max(ys)))
    if kind == "gable":
        rise = W / 2 * TAN(pitch)
        for s in (-1, 1):                                   # long walls
            face_out(p, wall, [Q(-L / 2, s * W / 2, 0), Q(L / 2, s * W / 2, 0), Q(L / 2, s * W / 2, z_e),
                               Q(-L / 2, s * W / 2, z_e)], V3 * s)
        for s in (-1, 1):                                   # gable ends
            a = s * L / 2
            if gable_mat:
                face_out(p, wall, [Q(a, -W / 2, 0), Q(a, W / 2, 0), Q(a, W / 2, z_e), Q(a, -W / 2, z_e)], U3 * s)
                face_out(p, gable_mat, [Q(a, -W / 2, z_e), Q(a, W / 2, z_e), Q(a, 0, z_e + rise)], U3 * s)
            else:
                face_out(p, wall, [Q(a, -W / 2, 0), Q(a, W / 2, 0), Q(a, W / 2, z_e), Q(a, 0, z_e + rise),
                                   Q(a, -W / 2, z_e)], U3 * s)
        sl = TAN(pitch)
        for s in (-1, 1):                                   # roof: top + underside, no edges
            pts = [Q(-L / 2 - oe, s * (W / 2 + oe), z_e - oe * sl), Q(L / 2 + oe, s * (W / 2 + oe), z_e - oe * sl),
                   Q(L / 2 + oe, 0, z_e + rise), Q(-L / 2 - oe, 0, z_e + rise)]
            nrm = V3 * s * sl + Vector((0, 0, 1))
            face_out(p + "R", roof, pts, nrm)
            face_out(p, under, [q - Vector((0, 0, 0.1)) for q in pts], -nrm)
    else:                                                   # lean-to, high on +v
        z_lo = z_e
        z_hi = G + hi if hi is not None else z_e + 0.7
        zt = lambda b: z_lo + (z_hi - z_lo) * (b + W / 2) / W
        for s in (-1, 1):
            b = s * W / 2
            face_out(p, wall, [Q(-L / 2, b, 0), Q(L / 2, b, 0), Q(L / 2, b, zt(b)), Q(-L / 2, b, zt(b))], V3 * s)
            a = s * L / 2
            face_out(p, wall, [Q(a, -W / 2, 0), Q(a, W / 2, 0), Q(a, W / 2, z_hi), Q(a, -W / 2, z_lo)], U3 * s)
        sl = (z_hi - z_lo) / W
        pts = [Q(-L / 2 - oe, -W / 2 - oe, z_lo - oe * sl), Q(L / 2 + oe, -W / 2 - oe, z_lo - oe * sl),
               Q(L / 2 + oe, W / 2 + oe, z_hi + oe * sl), Q(-L / 2 - oe, W / 2 + oe, z_hi + oe * sl)]
        nrm = Vector((0, 0, 1)) - V3 * sl
        face_out(p + "R", roof, pts, nrm)
        face_out(p, under, [q - Vector((0, 0, 0.1)) for q in pts], -nrm)
    fm = "atlas" if wall.startswith("sw:") else wall
    OUT_TINTS[(p, fm)] = wall_tint or OUT_WALL[len(OUT_TINTS) % len(OUT_WALL)]
    if not roof.startswith("sw:"):
        OUT_TINTS[(p + "R", roof)] = OUT_ROOF[roof_tint]
    if door is None:
        return Q
    # the door: on the wall whose outward normal points most toward the house
    d = TO_HOUSE[door]
    walls = [(u, L / 2, W), (-u, L / 2, W), (v, W / 2, L), (-v, W / 2, L)]
    nrm, off, span = max(walls, key=lambda w_: w_[0].dot(d))
    c2 = m + nrm * (off + 0.03)
    t2 = Vector((-nrm.y, nrm.x))
    ww = min(dw, span - 0.5)
    hh = min(dh, z_e - G - 0.2)
    q = [Vector((c2.x, c2.y, G)) + Vector((t2.x, t2.y, 0)) * k for k in (-ww / 2, ww / 2)]
    u0, v0, u1, v1 = ATLAS[cell]
    face_out(p, "atlas", [q[0], q[1], q[1] + Vector((0, 0, hh)), q[0] + Vector((0, 0, hh))],
             Vector((nrm.x, nrm.y, 0)), [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    return Q


def build_outbuildings():
    E, Wd = "E", "W"
    BD = dict(cell="barn_doors", dw=2.6, dh=2.4)
    # --- east side (sheet 2) ---
    outb("OE1", turned_b(43.1, 46.5, -277.6, -272.9, -11.2), 1, door=E, roof_tint="brown")
    outb("OE2", rect_b(57.7, 59.8, -271.9, -270.0), 1, door=E, dw=0.8, dh=1.9)
    outb("OE3", rect_b(68.7, 78.3, -274.4, -266.5), 2, door=E, **BD)
    outb("OE4", rect_b(76.7, 83.0, -255.5, -253.4), 1, kind="lean", door=E, roof_tint="brown", dh=1.8)
    outb("OE5", rect_b(50.4, 52.3, -255.0, -253.2), 1, door=E, dw=0.8, dh=1.9, roof_tint="brown")
    outb("OE6", rect_b(33.0, 40.5, -246.9, -244.0), 1, door=E)
    outb("OE7", rect_b(44.4, 47.0, -247.2, -245.4), 1, door=E, roof_tint="brown")
    outb("OE8", rect_b(53.3, 59.3, -246.9, -243.0), 1, door="S", **BD)
    outb("OE9", rect_b(76.5, 82.0, -233.9, -224.2), 2, door=E, roof_tint="brown", **BD)
    outb("OE10", rect_b(61.9, 66.3, -229.0, -226.9), 1, kind="lean", door=E, roof_tint="brown", dh=1.8)
    outb("OE11", rect_b(52.3, 54.3, -223.3, -220.7), 1, door=E)
    outb("OE12", rect_b(58.0, 63.7, -223.5, -217.3), 1, door=E, **BD)
    stone = (168, 162, 147)
    buff = tuple(min(1.0, srgb_lin(t) / srgb_lin(a)) for a, t in zip(stone, (176, 160, 132)))
    outb("OE13", rect_b(74.7, 92.0, -222.8, -213.6), 1, kind="lean", door=E, wall="block", eave=3.0, hi=3.5,
         wall_tint=buff, **BD)
    outb("OE14", rect_b(74.7, 87.7, -196.7, -193.0), 1, kind="lean", door="S", roof_tint="brown", **BD)
    # --- west side (sheet 6) ---
    outb("OW1", rect_b(-103.2, -93.1, -283.2, -270.3), 2, door=Wd, **BD)
    outb("OW2", [Vector((x, -z)) for x, z in ((-90.6, -269.8), (-85.4, -268.3), (-88.9, -254.8), (-94.4, -255.7))],
         1.5, door=Wd, roof_tint="brown", **BD)
    outb("OW3", rect_b(-104.1, -98.1, -259.4, -254.7), 1, door=Wd)
    outb("OW4", rect_b(-75.8, -72.0, -298.2, -294.9), 1, door=Wd, roof_tint="brown")
    outb("OW5", rect_b(-71.0, -67.9, -298.2, -289.8), 1, door=Wd)
    for p, z0, z1 in (("OW6", -298.4, -294.1), ("OW7", -293.4, -289.2)):     # glass-roofed ranges (opaque)
        outb(p, rect_b(-66.8, -57.9, z0, z1), 1, door=None, wall="brick", eave=0.8, pitch=30.0,
             roof="sw:paint_white", gable_mat="sw:paint_white", under="sw:paint_white", dw=0.9, dh=0.6,
             wall_tint=(0.9, 0.84, 0.8))
        OUT_TINTS[(p, "atlas")] = (0.86, 0.88, 0.88)
    outb("OW8", rect_b(-73.1, -68.3, -286.9, -282.9), 1, door=Wd, roof_tint="brown")
    outb("OW9", rect_b(-70.4, -62.9, -263.1, -253.8), 1.5, door=Wd, **BD)
    outb("OW9S", [Vector((x, -z)) for x, z in ((-70.4, -263.1), (-70.4, -253.8), (-73.4, -253.8), (-73.4, -263.1))],
         1, kind="lean", door="S", eave=2.3, hi=3.1)
    outb("OW10", rect_b(-65.7, -57.6, -235.8, -227.7), 2, door=Wd, **BD)
    outb("OW11", rect_b(-62.1, -57.1, -225.9, -219.8), 1, door=Wd, roof_tint="brown", **BD)
    # OW12, 106 Capner St: 2-storey frame dwelling, 3-bay front to Capner St (south = Blender -Y)
    outb("OW12", rect_b(-72.8, -63.1, -208.8, -203.7), 2, door="S", cell="door_brown", dw=1.0, dh=2.2,
         wall_tint=(0.95, 0.92, 0.84), under="sw:paint_white")
    y0 = 203.7
    for xb in (-70.2, -67.95, -65.7):
        window("OW12", cream(), "-y", (xb, y0, G + 3.3), 0.9, 1.5)
    for xb in (-70.2, -65.7):
        window("OW12", cream(), "-y", (xb, y0, G + 0.8), 0.9, 1.7)
    window("OW12", cream(), "+x", (-63.1, 206.25, G + 3.3), 0.9, 1.5)
    window("OW12", cream(), "+x", (-63.1, 206.25, G + 0.8), 0.9, 1.7)


def srgb_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


# ===========================================================================
# GROUND (scene x, z)
# ===========================================================================
EAST_PROP = [(6.36, -180.0), (6.0, -247.8), (12.0, -279.6), (25.7, -307.2)]


def xw_east(z):
    for (ax, az), (bx, bz) in zip(EAST_PROP, EAST_PROP[1:]):
        if bz <= z <= az:
            t = (z - az) / (bz - az)
            return ax + (bx - ax) * t
    raise ValueError(z)


def ribbon_edges(pts, w):
    left, right = [], []
    for i, (x, z) in enumerate(pts):
        a = Vector(pts[max(0, i - 1)])
        b = Vector(pts[min(len(pts) - 1, i + 1)])
        d = (b - a).normalized()
        nrm = Vector((-d.y, d.x)) * (w / 2)
        left.append((x + nrm.x, z + nrm.y))
        right.append((x - nrm.x, z - nrm.y))
    return left, right


# path centre z and outer x (the porch steps), scene coordinates
PATHS_W = [(-208.47, -13.5), (-220.8, -13.0), (-235.0, -16.1), (-261.6, -16.3)]
NW5_WALK = [(-10.4, -305.0), (-12.5, -305.0), (-15.5, -304.6), (-18.3, -303.4), (-20.6, -301.4),
            (-22.6, -300.05), (-24.6, -300.05)]
PATHS_E = [(-202.8, 13.2), (-216.05, 13.2), (-235.4, 13.5), (-250.95, 14.0), (None, None)]


def build_ground():
    X_W, X_S, X_C = -10.4, -8.6, -6.4
    Z0, Z1 = -202.4, -328.7
    # --- west lawn with notches for the paths and NW5's curving walk ---
    XW_OUT = -110.0                                         # R-a 2026-11-12: lawn widened from x -60
    loop = [(XW_OUT, Z0), (X_W, Z0)]
    for zc, xe in PATHS_W:
        zs, zn = zc + 0.6, zc - 0.6
        loop += [(X_W, zs), (xe, zs), (xe, zn), (X_W, zn)]
        poly_flat("Paths", "concrete", [(X_W, zs), (xe, zs), (xe, zn), (X_W, zn)], G)
    L, R = ribbon_edges(NW5_WALK, 1.5)
    # NW5_WALK runs -x: the "left" edge (normal (-d.y, d.x)) is at higher z
    hi, lo = (L, R) if L[0][1] > R[0][1] else (R, L)
    loop += hi + list(reversed(lo))
    for i in range(len(NW5_WALK) - 1):
        poly_flat("Paths", "concrete", [hi[i], hi[i + 1], lo[i + 1], lo[i]], G)
    loop += [(X_W, Z1), (XW_OUT, Z1)]
    poly_flat("LotW", "grass", loop, G)
    edge_skirt("LotW", "grass", [(XW_OUT, Z0), (XW_OUT, Z1)], G, -0.05, (-30, -260))
    edge_skirt("LotW", "grass", [(XW_OUT, Z0), (-52.0, Z0)], G, -0.05, (-56, -220))
    edge_skirt("LotW", "grass", [(XW_OUT, Z1), (-60.0, Z1)], G, -0.05, (-80, -300))
    # --- the 1913 walk: concrete 1.8 m, grass strip 2.2 m, curb ---
    for za, zb in zip(split(Z0, Z1, 25.0), split(Z0, Z1, 25.0)[1:]):
        poly_flat("WalkW", "concrete", [(X_W, za), (X_S, za), (X_S, zb), (X_W, zb)], G)
        poly_flat("Strip", "grass", [(X_S, za), (X_C, za), (X_C, zb), (X_S, zb)], G)
    edge_skirt("Curb", "concrete", [(X_C, Z0), (X_C, Z1)], G, ROAD_Y - 0.03, (-8.0, -260))
    edge_skirt("WalkW", "concrete", [(-10.3, Z0), (X_C, Z0)], G, -0.03, (-8.0, -210))
    # --- east lawns with notches ---
    zc5 = -278.8
    paths = list(PATHS_E)
    ne5_steps = ne5_point(-2.0 - 0.66, 278.45 - 271.5)      # outer edge of NE5's porch steps
    paths[4] = (zc5, ne5_steps[0] + 0.1)
    # R-a 2026-11-12: widened to x 95; the SE edge carries Pennsylvania Ave's walk line (25.7, -307.2) ->
    # (80, -294.9) on to (95, -291.5) (the street-ends road and walk end at x 80)
    loop = [(6.29, -192.4), (95.0, -192.4), (95.0, -291.5), (80.0, -294.9), (25.7, -307.2), (12.0, -279.6)]
    order = sorted(paths, key=lambda q: q[0])               # increasing z (from the bend toward -192.4)
    inserted_v = False
    for zc, xe in order:
        if not inserted_v and zc > -247.8:
            loop.append((6.0, -247.8))
            inserted_v = True
        za, zb = zc - 0.6, zc + 0.6
        loop += [(xw_east(za), za), (xe, za), (xe, zb), (xw_east(zb), zb)]
        poly_flat("Paths", "concrete", [(xw_east(za), za), (xe, za), (xe, zb), (xw_east(zb), zb)], G)
    poly_flat("LotE", "grass", loop, G)
    edge_skirt("LotE", "grass", [(50.0, -192.4), (95.0, -192.4), (95.0, -291.5), (80.0, -294.9)], G, -0.05,
               (40, -250))


# ===========================================================================
# build
# ===========================================================================
BUCKETS.clear()
col = clear_collection()
build_nw1()
build_nw2()
build_nw3()
build_nw4()
build_nw5()
build_ne1()
build_ne2()
build_ne3()
build_ne4()
build_ne5()
turn_ne5()
build_outbuildings()
build_ground()
OBJS = make_objects(col)
for o in OBJS:
    o.name = o.data.name = o.name.replace("SC_", "NA_", 1)
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in OBJS)
import re
by = {}
for o in OBJS:
    m = re.match(r"N[WE]\d|O[WE]", o["part"])
    k = m.group(0) if m else "ground"
    by[k] = by.get(k, 0) + sum(len(p.vertices) - 2 for p in o.data.polygons)
print("NorthApproach built:", len(OBJS), "objects,", tris, "triangles")
print(sorted(by.items()))
