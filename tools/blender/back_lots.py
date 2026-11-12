"""
back_lots.py - the back-lot buildings of PLAN.md "Street details pass 2", section 5, list A
(build split D): barns, sheds and shops standing in the yards behind the Main St buildings,
seen from Main St through a lane, a gap or a carriageway. Sept 1921 Sanborn footprints
(sheet 2, +-0.5 m); everything else PLAIN-GUESS (no photo shows any of them).

  A1  Blacksmith ("Bl. Sm.", 49 1/2), 1-storey frame, gable along its length, double doors
      in the east gable end at the head of the blacksmith's lane, forge chimney
  A2  Auto Repair Shop (32 1/2), 1-storey brick, L plan, flat roof behind a parapet, garage
      doors in the west wall at the head of the lane at 32
  A3  "Auto" shed, 1-storey frame, gable end with a wide door to the lane at 32
  A4  "Auto" garage behind 40, 2-storey brick, flat roof behind a parapet, garage doors in
      the west wall facing carriageway 40
  A5  Barn (crossed box), 2-storey frame, gable along its length, wagon doors and a hay door
      in the west gable end
  A6  Harness Shop, 1-storey frame (painted clapboard), door and window to the lane 68 / hotel;
      west wall 0.30 m east of the map line (31.10, not 30.80): Lovell's rear reaches x 31.08
  A7  Wagon Shed, 1-storey, open on the south side (posts), brick north wall, frame ends,
      shed roof falling to the open side; north wall 0.30 m south of the map line (z -54.7):
      the Bloomfield model's machine shop B8 has its eave over the line
Skipped (already built in other models): A8-A13 (sidestreet-bloomfield.glb), A14, A15
(sidestreet-southeast.glb), A16 = K1 Fire Dept House (sidestreet-court.glb).

Run inside Blender:
    exec(open(r"<project>/tools/blender/back_lots.py").read())
Every run deletes and rebuilds the "BackLots" collection. Materials, lightmap bake and GLB
export: back_lots_bake.py (runs this file first).

Shared helpers are taken with `ast` from sidestreet_court.py and sidestreet_bloomfield.py.

Coordinates: SCENE AXES (the GLB is placed at "0 0 0", rotation "0 0 0"):
    Blender X = scene x (east), Blender Y = -scene z (north = +Y), Blender Z = scene y (up).
Ground: A4-A7 stand on the backdrop lots at y 0.15; A1-A3 stand on the bare scene disc (y 0),
so they get trodden-earth pads at y 0.012 (the height of js/ground.js's lanes, which the pads
continue). Walls skirt down to 0.0. Windows and doors are flat quads 3 cm proud of the wall,
mapped to cells of assets/textures/shared/backdrop_windows.jpg.
"""

import ast
import json
import math
import random
import bpy
import bmesh
from mathutils import Vector

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
COURT = PROJECT + r"\tools\blender\sidestreet_court.py"
BLOOM = PROJECT + r"\tools\blender\sidestreet_bloomfield.py"
COLL = "BackLots"
G = 0.15                       # backdrop lot level (A4-A7)
GL = 0.012                     # earth pads / lanes level (A1-A3)
ATLAS = json.load(open(PROJECT + r"\assets\textures\shared\backdrop_windows.json"))["cells"]
TILE = {"boards": 1.6, "clap": 1.0, "brick": 1.4, "tin": 2.0, "earth": 3.0}
rng = random.Random(1921)
BUCKETS = {}


def _take(path, names):
    tree = ast.parse(open(path, encoding="utf8").read())
    mod = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names],
                     type_ignores=[])
    exec(compile(mod, path, "exec"), globals())
    missing = set(names) - {n.name for n in mod.body}
    assert not missing, missing


_take(COURT, {"P", "newell", "add", "face_out", "solid", "box", "gable_walls", "slab", "gable_roof",
              "shed", "window", "win_row", "cream", "green", "clear_collection", "uv_for", "make_objects"})
_take(BLOOM, {"fp", "front_row", "sill_lintel", "bflat", "bskirt"})

FINAL_MAT = {"boards": "boards", "clap": "clap", "brick": "brick", "tin": "tin", "earth": "earth",
             "atlas": "atlas"}
TAN = lambda deg: math.tan(math.radians(deg))
TRIM = "sw:wood_grey"


def chimney(part, x, y, z_base, z_top, w=0.6, d=0.6):
    box(part, "brick", x - w / 2, x + w / 2, y - d / 2, y + d / 2, z_base, z_top)
    box(part, "brick", x - w / 2 - 0.07, x + w / 2 + 0.07, y - d / 2 - 0.07, y + d / 2 + 0.07,
        z_top - 0.18, z_top + 0.02, sides=("t", "n", "s", "e", "w", "b"))


def door_frame(p, n, wall, a, z, w, h, t=0.12, proud=0.06, mat=TRIM):
    """plank casing round a door: two jambs and a head board, `proud` off the wall"""
    s = 1 if n in ("+x", "+y") else -1
    f = {"+y": "n", "-y": "s", "+x": "e", "-x": "w"}[n]
    out = sorted((wall, wall + s * proud))
    pieces = [(a - w / 2 - t, a - w / 2, z, z + h), (a + w / 2, a + w / 2 + t, z, z + h),
              (a - w / 2 - t, a + w / 2 + t, z + h, z + h + t)]
    for u0, u1, z0, z1 in pieces:
        sides = (f, "t", "e", "w") if n in ("+y", "-y") else (f, "t", "n", "s")
        if n in ("+y", "-y"):
            box(p, mat, u0, u1, out[0], out[1], z0, z1, sides=sides)
        else:
            box(p, mat, out[0], out[1], u0, u1, z0, z1, sides=sides)


def opening(p, cell, n, wall, a, z, w, h, frame=True):
    """window / door quad + plank casing"""
    if n in ("+y", "-y"):
        window(p, cell, n, (a, wall, z), w, h)
    else:
        window(p, cell, n, (wall, a, z), w, h)
    if frame:
        door_frame(p, n, wall, a, z, w, h)


def hood(p, n, wall, a, z, w, depth=0.45, rise=0.25):
    """small tin pent hood over a door or hay door"""
    s = 1 if n in ("+x", "+y") else -1
    if n in ("+y", "-y"):
        pts = [(a - w / 2, wall, z + rise), (a + w / 2, wall, z + rise),
               (a + w / 2, wall + s * depth, z), (a - w / 2, wall + s * depth, z)]
    else:
        pts = [(wall, a - w / 2, z + rise), (wall, a + w / 2, z + rise),
               (wall + s * depth, a + w / 2, z), (wall + s * depth, a - w / 2, z)]
    slab(p, "tin", TRIM, pts, 0.06)


def brick_row(p, n, wall, xs, z, w, h, cells=None):
    front_row(p, n, wall, xs, z, w, h, cells or cream)
    for a in xs:
        sill_lintel(p, n, wall, a, z, w, h)


def flat_top(part, wall, x0, x1, y0, y1, top, coping="sw:stone_cream", roof="tin"):
    """walls to `top` + a coping slab over the footprint (its top face is the roof)"""
    box(part, wall, x0, x1, y0, y1, 0.0, top - 0.15, sides=("n", "s", "e", "w"))
    box(part, coping, x0 - 0.06, x1 + 0.06, y0 - 0.06, y1 + 0.06, top - 0.15, top + 0.03,
        sides=("t", "n", "s", "e", "w", "b"), top=roof)


# ===========================================================================
# A1  Blacksmith, 49 1/2 (west side; its east gable end closes the blacksmith's lane)
# ===========================================================================
def build_a1():
    p = "A1"
    x0, x1, y0, y1 = fp(-73.0, -57.5, -101.5, -96.5)
    eave = GL + 3.0
    rise = (y1 - y0) / 2 * TAN(32)
    gable_walls(p, "boards", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.35, og=0.3, top="tin", under=TRIM)
    # east gable end, facing the lane (lane z -100.1 .. -94.5 -> door centre z -98.4)
    opening(p, "barn_doors", "+x", x1, 98.4, GL, 2.8, 2.7)
    hood(p, "+x", x1, 98.4, GL + 2.85, 3.2)
    opening(p, "small_window", "+x", x1, 100.75, GL + 1.1, 0.6, 0.8)
    opening(p, "barn_doors", "+x", x1, 99.0, eave + 0.1, 0.9, 1.0)                 # loft hatch
    # long sides: small shop windows (south side faces the lane's far edge), a side door
    for xx in (-61.0, -64.5, -68.5):
        opening(p, "small_window", "-y", y0, xx, GL + 1.1, 0.8, 0.9)
    opening(p, "barn_doors", "-y", y0, -71.2, GL, 1.2, 2.2)
    for xx in (-62.5, -67.0):
        opening(p, "small_window", "+y", y1, xx, GL + 1.1, 0.8, 0.9)
    # forge chimney (brick) through the south slope near the west end
    chimney(p, -69.5, (y0 + y1) / 2 - 0.5, eave + 0.3, eave + rise + 1.3)


# ===========================================================================
# A2  Auto Repair Shop, 32 1/2 (east side; L plan, brick)
# ===========================================================================
def build_a2():
    p = "A2"
    x0, x1, y0, y1 = fp(61.0, 70.0, -151.5, -138.0)
    top = GL + 4.4
    flat_top(p, "brick", x0, x1, y0, y1, top)
    # west wall at the head of the lane at 32 (lane z -140.9 .. -137.8)
    window(p, "engine_doors", "-x", (x0, 139.75, GL), 2.8, 3.0)
    sill_lintel(p, "-x", x0, 139.75, GL + 3.0 - 3.0, 2.8, 3.0)
    brick_row(p, "-x", x0, (143.6,), GL + 1.1, 1.0, 1.6)
    # south wall (faces the yards of 32-38): three windows
    brick_row(p, "-y", y0, (63.2, 65.9, 68.6), GL + 1.1, 1.0, 1.6)
    brick_row(p, "+y", y1, (63.0, 67.8), GL + 1.1, 1.0, 1.6)
    brick_row(p, "+x", x1, (141.0, 144.8, 148.6), GL + 1.1, 1.0, 1.6)
    # wing 58 .. 61, z -151.5 .. -146.5, a little lower
    w = "A2W"
    wx0, wx1, wy0, wy1 = fp(58.0, 61.0, -151.5, -146.5)
    flat_top(w, "brick", wx0, wx1, wy0, wy1, GL + 3.8)
    window(w, "door_green", "-y", (59.5, wy0, GL), 1.0, 2.2)
    sill_lintel(w, "-y", wy0, 59.5, GL, 1.0, 2.2)
    brick_row(w, "-x", wx0, (149.0,), GL + 1.1, 0.9, 1.5)


# ===========================================================================
# A3  "Auto" shed (east side, north of the lane at 32)
# ===========================================================================
def build_a3():
    p = "A3"
    x0, x1, y0, y1 = fp(53.0, 57.0, -148.5, -142.5)
    eave = GL + 2.8
    rise = (x1 - x0) / 2 * TAN(30)
    gable_walls(p, "boards", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "y", oe=0.3, og=0.3, top="tin", under=TRIM)
    opening(p, "barn_doors", "-y", y0, 55.0, GL, 2.7, 2.5)                        # to the lane
    opening(p, "small_window", "-x", x0, 145.5, GL + 1.2, 0.7, 0.7)
    opening(p, "small_window", "+x", x1, 146.0, GL + 1.2, 0.7, 0.7)


# ===========================================================================
# A4  "Auto" garage behind 40 (east side; faces carriageway 40, z -124.2 .. -121.5)
# ===========================================================================
def build_a4():
    p = "A4"
    x0, x1, y0, y1 = fp(39.5, 50.0, -123.5, -115.5)
    top = G + 7.0
    flat_top(p, "brick", x0, x1, y0, y1, top)
    box(p, "sw:stone_cream", x0 - 0.05, x1 + 0.05, y0 - 0.05, y1 + 0.05, G + 3.55, G + 3.7,
        sides=("n", "s", "e", "w", "t", "b"))                                     # floor band
    window(p, "engine_doors", "-x", (x0, 121.9, G), 2.8, 3.0)
    sill_lintel(p, "-x", x0, 121.9, G, 2.8, 3.0)
    brick_row(p, "-x", x0, (118.0,), G + 1.0, 1.0, 1.7)
    brick_row(p, "-x", x0, (117.6, 119.7, 121.9), G + 4.3, 0.95, 1.6)              # upper floor
    brick_row(p, "-y", y0, (41.6, 44.75, 47.9), G + 1.0, 1.0, 1.7)
    brick_row(p, "-y", y0, (41.6, 44.75, 47.9), G + 4.3, 0.95, 1.6)
    brick_row(p, "+y", y1, (43.0, 47.0), G + 4.3, 0.95, 1.6)
    brick_row(p, "+x", x1, (118.0, 121.0), G + 4.3, 0.95, 1.6)


# ===========================================================================
# A5  Barn (crossed box), 2-storey frame, west gable end toward Main St
# ===========================================================================
def build_a5():
    p = "A5"
    x0, x1, y0, y1 = fp(66.5, 76.0, -123.0, -117.0)
    eave = G + 5.6
    rise = (y1 - y0) / 2 * TAN(40)
    gable_walls(p, "boards", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.4, og=0.35, top="tin", under=TRIM)
    yc = (y0 + y1) / 2
    opening(p, "barn_doors", "-x", x0, yc, G, 3.2, 3.3)                          # wagon doors
    hood(p, "-x", x0, yc, G + 3.5, 3.6)
    opening(p, "barn_doors", "-x", x0, yc, G + 4.1, 1.4, 1.6)                    # hay door
    box(p, TRIM, x0 - 1.0, x0, yc - 0.1, yc + 0.1, eave + 1.35, eave + 1.55,
        sides=("t", "b", "n", "s", "w"))                                         # hay hoist beam
    opening(p, "small_window", "-x", x0, y0 + 0.8, G + 1.6, 0.6, 0.6)
    # long sides: stable door and stall windows
    opening(p, "barn_doors", "-y", y0, 70.0, G, 1.2, 2.2)
    for xx in (68.2, 72.3, 74.4):
        opening(p, "small_window", "-y", y0, xx, G + 1.6, 0.6, 0.6)
    for xx in (68.6, 71.2, 73.8):
        opening(p, "small_window", "+y", y1, xx, G + 1.6, 0.6, 0.6)
    opening(p, "barn_doors", "+x", x1, yc, G, 2.4, 2.6)


# ===========================================================================
# A6  Harness Shop (east side; south wall to the lane between 68 Main and the hotel)
# ===========================================================================
def build_a6():
    p = "A6"
    x0, x1, y0, y1 = fp(31.10, 36.3, -55.0, -48.5)        # nudged 0.30 m east of the map (Lovell's rear)
    eave = G + 3.1
    rise = (y1 - y0) / 2 * TAN(30)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.3, og=0.0, top="tin", under="sw:paint_white")
    box(p, "sw:stone_cream", x0, x1 + 0.0, y0 - 0.03, y0, 0.0, G + 0.3, sides=("s", "t"))      # base
    opening(p, "door_green", "-y", y0, 32.4, G + 0.3, 0.95, 2.15, frame=False)
    box(p, "sw:stone_cream", 31.8, 33.0, y0 - 0.55, y0, 0.0, G + 0.15, sides=("s", "t", "e", "w"))  # step
    opening(p, "win_cream_3", "-y", y0, 34.6, G + 0.9, 1.1, 1.6, frame=False)
    opening(p, cream(), "+y", y1, 33.7, G + 1.0, 0.9, 1.5, frame=False)


# ===========================================================================
# A7  Wagon Shed (east side; open to the south, brick north wall)
# ===========================================================================
def build_a7():
    p = "A7"
    # north wall 0.30 m south of the map line (z -54.7, not -55.0): the Bloomfield model's
    # machine shop B8 (z -62.8 .. -55.1) has its south eave overhanging to z -54.8
    x0, x1, y0, y1 = fp(36.3, 74.5, -54.7, -47.5)
    z_hi, z_lo = G + 4.2, G + 3.4
    slope = (z_hi - z_lo) / (y1 - y0)
    zt = lambda y: z_lo + (y - y0) * slope
    box(p, "brick", x0 + 0.2, x1 - 0.2, y1 - 0.35, y1, 0.0, z_hi, sides=("s", "n"))       # back wall
    for xa, xb in ((x0, x0 + 0.2), (x1 - 0.2, x1)):                                     # frame ends
        for xx, o in ((xa, -1), (xb, 1)):
            face_out(p, "boards", [(xx, y0, 0.0), (xx, y1, 0.0), (xx, y1, zt(y1)), (xx, y0, zt(y0))], (o, 0, 0))
        face_out(p, "boards", [(xa, y0, 0.0), (xb, y0, 0.0), (xb, y0, zt(y0)), (xa, y0, zt(y0))], (0, -1, 0))
    # roof slab: overhangs the open front by 0.45 m, the ends by 0.2 m (only 1 m to B9 at x 75.5),
    # flush with the back wall (B8's eave is 0.1 m behind it)
    slab(p, "tin", TRIM,
         [(x0 - 0.2, y0 - 0.45, z_lo - 0.45 * slope), (x1 + 0.2, y0 - 0.45, z_lo - 0.45 * slope),
          (x1 + 0.2, y1, z_hi), (x0 - 0.2, y1, z_hi)], 0.12)
    # plate beam and posts along the open front (10 bays), and a fascia under the eave
    box(p, TRIM, x0, x1, y0, y0 + 0.2, z_lo - 0.3, z_lo, sides=("s", "n", "b"))
    n = 10
    for k in range(1, n):
        px = x0 + (x1 - x0) * k / n
        box(p, TRIM, px - 0.1, px + 0.1, y0 + 0.02, y0 + 0.22, 0.0, z_lo - 0.3, sides=("s", "n", "e", "w"))
    # brick wall: a few small vents high up, seen from the bank's yard
    for xx in (42.0, 55.4, 68.8):
        window(p, "small_window", "+y", (xx, y1, G + 2.6), 0.6, 0.6)


# ===========================================================================
# Earth pads (A1-A3 stand on the bare scene disc), y 0.012 like js/ground.js's lanes
# ===========================================================================
def pad(part, x0, x1, z0, z1):
    bx0, bx1, by0, by1 = fp(x0, x1, z0, z1)
    bflat(part, "earth", bx0, bx1, by0, by1, GL)


def build_pads():
    # blacksmith's yard: west of the lane end (lane x -57.5 .. -10.3, z -100.1 .. -94.5)
    pad("PadA1", -76.5, -57.5, -104.5, -93.0)
    pad("PadA1", -57.5, -54.0, -104.5, -100.1)
    pad("PadA1", -57.5, -54.0, -94.5, -93.0)
    # yard at the head of the lane at 32 (lane x 7.6 .. 58, z -140.9 .. -137.8)
    pad("PadA2", 49.0, 58.0, -154.5, -140.9)
    pad("PadA2", 49.0, 58.0, -137.8, -135.5)
    pad("PadA2", 58.0, 73.0, -154.5, -135.5)


# ===========================================================================
# build
# ===========================================================================
BUCKETS.clear()
col = clear_collection()
build_a1()
build_a2()
build_a3()
build_a4()
build_a5()
build_a6()
build_a7()
build_pads()
OBJS = make_objects(col)
for o in OBJS:
    o.name = o.data.name = o.name.replace("SC_", "BL_", 1)
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in OBJS)
print("BackLots built:", len(OBJS), "objects,", tris, "triangles")
