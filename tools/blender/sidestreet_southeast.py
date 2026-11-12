"""
sidestreet_southeast.py - the south-east backdrop (PLAN.md "Side streets, backdrop buildings",
sections 1c, 1d, 3, 4 and 7; pass 2 list A): every building a visitor sees from Main St down the
alley at No. 80 (between the Nevius store and the Odd Fellows Hall), down alley 86 and along
Higgins Ave (today's Chorister Place), at the Sept 1921 Sanborn footprints (sheet 3, +-1.5 m),
as one cheap model, plus the ground js/ground.js does not draw there.

Alley 80, north side (lane walls face scene +z = Blender -Y):
  L1  Feed House, 2-storey brick, 7.3 m ("24'"), flat roof behind a parapet, two compartments,
      hoist beam over a loft door                                       PLAIN-GUESS
  L2  Vacant, 2-storey brick, 5.5 m ("18'"), flat                         PLAIN-GUESS
  L3  Ice House, "1=2" frame, 7.3 m, gable along the lane, tin            PLAIN-GUESS
  L4  Wagon Shed, 1-storey frame, open on the lane side, brick back wall, shed roof
                                                                          PLAIN-GUESS
Alley 80, south side (lane walls face scene -z = Blender +Y):
  A15 "Auto" garage (1 storey brick, flat) + Ice House ("1=2" frame 7.3 m, gable end to
      the lane)                                                           PLAIN-GUESS
  L5  Cold Storage, 2-storey brick, 6.7 m ("22'"), flat                   PLAIN-GUESS
  L6  Shed, 2-storey brick, flat                                         PLAIN-GUESS
  L7  Storage, 2-storey frame, gable along the lane, 1-storey east end to Spring St
                                                                          PLAIN-GUESS
Alley 86 (pass 2 list A):
  A14 two 2-storey brick dwellings ("86 1/2"), gable along their length, fronts to the north
      yard, west gable end closing the alley view                         PLAIN-GUESS
Higgins Ave (south side; fronts face scene -z = Blender +Y):
  H1  "Auto 1st, Hall 2d (stuccoed)" = Children's Choir School (built as a stable): 2-storey
      stuccoed brick, composition roof (flat behind a parapet), wide auto door  PLAIN-GUESS
  H2  Dwelling 5 Higgins: 2-storey frame, front gable + east wing (L plan), porch across the
      front                                                               PLAIN-GUESS
Tier 2 (box + roof, few or no windows):
  H3  Dwelling 6 Higgins (north side) with rear ell                      PLAIN-GUESS
  H4  Blacksmith, 19 Spring St, 1 1/2-storey frame                        PLAIN-GUESS
  H5  Double dwelling on Spring St                                        PLAIN-GUESS
Ground: alley 80 lane east of x 57 (js/ground.js draws x 10.3 .. 57, z -3.3 .. 1.3) to Spring
St, Higgins Ave east of x 40 (road z 62.9 .. 67.9, earth margins) to Spring St, Spring St
z -40 (end of the Bloomfield model's stub) .. 90, back lots (trodden earth by the alley and
north of it, worn grass elsewhere, lawns on Higgins Ave). No signs or lettering. No trees (the
scene instances backdrop-tree.glb; positions in sidestreet_southeast_bake.py).

Run inside Blender:
    exec(open(r"<project>/tools/blender/sidestreet_southeast.py").read())
Every run deletes and rebuilds the "SidestreetSoutheast" collection. Materials, lightmap bake
and GLB export: sidestreet_southeast_bake.py (runs this file first).

Shared helpers are taken with `ast` from sidestreet_court.py (boxes, gables, porches, windows,
buckets -> objects) and sidestreet_bloomfield.py (flat_top, front_row, fp), so all three
backdrops are built by the same code.

Coordinates: SCENE AXES (the GLB is placed at "0 0 0", rotation "0 0 0"):
    Blender X = scene x (east), Blender Y = -scene z (north = +Y), Blender Z = scene y (up).
Ground level: lots, walks and the bottom of every wall at y 0.15; walls skirt down to 0.0.
Lanes 0.012 (as js/ground.js's lanes), Higgins Ave and Spring St roads 0.01.
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
COLL = "SidestreetSoutheast"
G = 0.15                       # lot / sidewalk top
ROAD_Y = 0.01
LANE_Y = 0.012                 # js/ground.js's lanes
ALLEY_JOIN = 57.0              # js/ground.js draws alley 80 west of this
HIGGINS_JOIN = 40.0            # ... and Higgins Ave west of this
SPRING_W, SPRING_E = 108.6, 124.3        # Spring St property lines (road 111.0 .. 121.9)
ATLAS = json.load(open(PROJECT + r"\assets\textures\shared\backdrop_windows.json"))["cells"]
TILE = {"clap": 1.0, "brick": 1.4, "slate": 1.5, "concrete": 3.0, "grass": 4.0, "earth": 2.0}
rng = random.Random(1880)
BUCKETS = {}

# --- shared helpers --------------------------------------------------------------------
def _take(path, names):
    tree = ast.parse(open(path, encoding="utf8").read())
    mod = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names],
                     type_ignores=[])
    exec(compile(mod, path, "exec"), globals())
    missing = set(names) - {n.name for n in mod.body}
    assert not missing, missing


_take(COURT, {"P", "newell", "add", "face_out", "solid", "box", "sbox", "gable_walls", "slab", "gable_roof",
              "shed", "chimney", "cross_gable", "window", "win_row", "cream", "green", "porch", "foundation",
              "clear_collection", "uv_for", "make_objects"})
_take(BLOOM, {"fp", "flat_top", "front_row", "sill_lintel", "bflat", "bskirt", "split"})


def brick_row(p, n, wall, xs, z, w, h, cells=None):
    """windows in a brick wall, each with a pale stone sill and lintel"""
    front_row(p, n, wall, xs, z, w, h, cells or green)
    for a in xs:
        sill_lintel(p, n, wall, a, z, w, h)

FINAL_MAT = {"clap": "clap", "brick": "brick", "slate": "slate", "concrete": "concrete", "road": "road",
             "grass": "grass", "earth": "earth", "atlas": "atlas"}
TAN = lambda deg: math.tan(math.radians(deg))


# ===========================================================================
# Alley 80, north side (lane walls at Blender y = -z, facing -Y)
# ===========================================================================
def build_l1():
    """Feed House: two compartments under one flat roof, hoist beam over a loft door."""
    p = "L1"
    x0, x1, y0, y1 = fp(42.62, 65.3, -11.0, -4.3)      # west end against the Nevius rear wall (x 42.55)
    top = G + 7.3
    box(p, "brick", x0, x1, y0, y1, 0.0, top - 0.15, sides=("n", "s", "e"))
    box(p, "sw:stone_cream", x0, x1 + 0.06, y0 - 0.06, y1 + 0.06, top - 0.15, top + 0.03,
        sides=("t", "n", "s", "e", "b"), top="sw:tin_dark")
    # the party wall between the compartments shows as a pilaster strip on the lane wall
    box(p, "brick", 53.75, 54.25, y0 - 0.1, y0, 0.0, top - 0.15, sides=("s", "e", "w"))
    # west compartment: wide door, window, upper windows; loft door under the hoist
    window(p, "barn_doors", "-y", (46.0, y0, G), 2.6, 2.8)
    brick_row(p, "-y", y0, (43.9, 49.2, 51.9), G + 1.1, 0.95, 1.6)
    brick_row(p, "-y", y0, (43.9, 51.9), G + 4.3, 0.95, 1.6)
    window(p, "barn_doors", "-y", (47.6, y0, G + 3.9), 1.5, 2.1)              # loft door
    # hoist beam and its little hood, over the loft door
    box(p, "sw:wood_grey", 47.48, 47.72, y0 - 1.1, y0, G + 6.5, G + 6.75, sides=("s", "e", "w", "b", "t"))
    slab(p, "sw:tin_dark", "sw:wood_grey", [(46.9, y0, G + 7.25), (48.3, y0, G + 7.25),
                                            (48.3, y0 - 1.3, G + 6.85), (46.9, y0 - 1.3, G + 6.85)], 0.08)
    # east compartment
    window(p, "barn_doors", "-y", (59.6, y0, G), 2.6, 2.8)
    brick_row(p, "-y", y0, (56.1, 63.3), G + 1.1, 0.95, 1.6)
    brick_row(p, "-y", y0, (56.1, 59.6, 63.3), G + 4.3, 0.95, 1.6)
    # east end above L2 (5.5 m)
    front_row(p, "+x", x1, (6.5, 9.0), G + 5.6, 0.85, 1.2, green)


def build_l2():
    p = "L2"
    x0, x1, y0, y1 = fp(65.3, 77.4, -11.0, -5.1)
    top = G + 5.5
    box(p, "brick", x0, x1, y0, y1, 0.0, top - 0.15, sides=("n", "s"))
    box(p, "sw:stone_cream", x0, x1, y0 - 0.06, y1 + 0.06, top - 0.15, top + 0.03,
        sides=("t", "n", "s", "b"), top="sw:tin_dark")
    window(p, "door_green", "-y", (67.0, y0, G + 0.05), 1.0, 2.3)
    brick_row(p, "-y", y0, (69.6, 72.4, 75.2), G + 0.9, 0.95, 1.55)
    brick_row(p, "-y", y0, (67.0, 69.6, 72.4, 75.2), G + 3.25, 0.9, 1.4)


def build_l3():
    """Ice House: tall frame block ("1=2"), gable along the lane, one door and a hatch."""
    p = "L3"
    x0, x1, y0, y1 = fp(77.4, 86.4, -11.0, -5.0)
    eave = G + 7.3
    rise = (y1 - y0) / 2 * TAN(28)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.3, og=0.25, top="sw:tin_dark")
    foundation(p, x0, x1, y0, y1, G + 0.3, ("s", "e", "w"))
    window(p, "barn_doors", "-y", (80.2, y0, G + 0.3), 1.8, 2.6)
    window(p, "barn_doors", "-y", (83.8, y0, G + 4.0), 1.2, 1.6)              # ice hatch
    window(p, "small_window", "-x", (x0, (y0 + y1) / 2, G + 6.2), 0.6, 0.6)
    window(p, "small_window", "+x", (x1, (y0 + y1) / 2, eave + 0.3), 0.6, 0.6)


def build_l4():
    """Wagon Shed: open on the lane, brick back wall, frame ends, shed roof falling to the lane."""
    p = "L4"
    x0, x1, y0, y1 = fp(86.4, 107.7, -11.0, -5.0)
    z_hi, z_lo = G + 4.3, G + 3.5
    zt = lambda y: z_lo + (z_hi - z_lo) * (y - y0) / (y1 - y0)
    box(p, "brick", x0 + 0.2, x1 - 0.2, y1 - 0.35, y1, 0.0, z_hi, sides=("s", "n"))          # back wall
    for xa, xb, out in ((x0, x0 + 0.2, (-1, 0, 0)), (x1 - 0.2, x1, (1, 0, 0))):           # frame ends
        for xx, o in ((xa, -1), (xb, 1)):
            face_out(p, "clap", [(xx, y0, 0.0), (xx, y1, 0.0), (xx, y1, zt(y1)), (xx, y0, zt(y0))], (o, 0, 0))
        face_out(p, "clap", [(xa, y0, 0.0), (xb, y0, 0.0), (xb, y0, zt(y0)), (xa, y0, zt(y0))], (0, -1, 0))
    # roof slab (overhangs the lane by 0.4 m), plate beam and posts along the open front
    slab(p, "sw:tin_dark", "sw:wood_grey",
         [(x0 - 0.2, y0 - 0.4, z_lo - 0.4 * (z_hi - z_lo) / (y1 - y0)), (x1 + 0.2, y0 - 0.4, z_lo - 0.4 * (z_hi - z_lo) / (y1 - y0)),
          (x1 + 0.2, y1 + 0.2, z_hi + 0.2 * (z_hi - z_lo) / (y1 - y0)), (x0 - 0.2, y1 + 0.2, z_hi + 0.2 * (z_hi - z_lo) / (y1 - y0))], 0.12)
    box(p, "sw:wood_grey", x0, x1, y0, y0 + 0.2, z_lo - 0.3, z_lo, sides=("s", "n", "b"))
    for k in range(1, 6):
        px = x0 + (x1 - x0) * k / 6
        box(p, "sw:wood_grey", px - 0.1, px + 0.1, y0 + 0.02, y0 + 0.22, 0.0, z_lo - 0.3, sides=("s", "n", "e", "w"))


# ===========================================================================
# Alley 80, south side (lane walls at Blender y = -z, facing +Y)
# ===========================================================================
def build_a15():
    p = "A15"
    # "Auto" garage, 1 storey brick, flat roof behind a low parapet
    x0, x1, y0, y1 = fp(55.9, 64.2, 1.5, 10.7)
    top = G + 4.2
    flat_top(p, "brick", x0, x1, y0, y1, top)
    window(p, "barn_doors", "+y", (59.0, y1, G), 3.0, 2.8)
    brick_row(p, "+y", y1, (62.6,), G + 1.0, 1.0, 1.5, cream)
    brick_row(p, "-x", x0, (-9.2, -6.1, -3.0), G + 1.0, 1.0, 1.5, cream)
    # ice house, "1=2" frame, 7.3 m, gable end to the lane
    i = "A15I"
    x0, x1, y0, y1 = fp(64.5, 70.9, 1.5, 10.7)
    eave = G + 7.3
    rise = (x1 - x0) / 2 * TAN(30)
    gable_walls(i, "clap", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(i, x0, x1, y0, y1, eave, rise, "y", oe=0.3, og=0.25, top="sw:tin_dark")
    foundation(i, x0, x1, y0, y1, G + 0.3, ("n", "e", "w"))
    window(i, "barn_doors", "+y", (67.7, y1, G + 0.3), 1.8, 2.6)
    window(i, "barn_doors", "+y", (67.7, y1, G + 4.2), 1.2, 1.6)
    window(i, "attic_window", "+y", (67.7, y1, eave + 0.5), 0.6, 0.6)


def build_l5():
    p = "L5"
    x0, x1, y0, y1 = fp(70.9, 79.0, 2.4, 10.7)
    top = G + 6.7
    flat_top(p, "brick", x0, x1, y0, y1, top)
    window(p, "door_green", "+y", (72.6, y1, G + 0.3), 1.2, 2.3)
    box(p, "concrete", 71.8, 73.4, y1, y1 + 0.8, 0.0, G + 0.3)                    # loading step
    window(p, "barn_doors", "+y", (72.6, y1, G + 3.6), 1.2, 1.8)                 # upper loading door
    brick_row(p, "+y", y1, (75.2, 77.6), G + 1.3, 0.8, 1.1)
    brick_row(p, "+y", y1, (75.2, 77.6), G + 4.2, 0.8, 1.1)
    chimney(p, 77.8, -9.6, top - 0.2, top + 1.5)


def build_l6():
    p = "L6"
    x0, x1, y0, y1 = fp(80.3, 86.5, 4.5, 10.7)
    top = G + 6.0
    flat_top(p, "brick", x0, x1, y0, y1, top)
    window(p, "barn_doors", "+y", (82.4, y1, G), 2.4, 2.7)
    window(p, green(), "+y", (85.0, y1, G + 1.0), 0.9, 1.5)
    brick_row(p, "+y", y1, (82.0, 84.8), G + 3.7, 0.9, 1.4)
    brick_row(p, "-x", x0, (-8.8, -6.4), G + 3.7, 0.9, 1.4)


def build_l7():
    """Storage, 2-storey frame, gable along the lane; 1-storey shed end to Spring St."""
    p = "L7"
    x0, x1, y0, y1 = fp(86.5, 103.4, 4.5, 10.7)
    eave = G + 6.0
    rise = (y1 - y0) / 2 * TAN(30)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.3, og=0.25, top="sw:tin_dark")
    foundation(p, x0, x1, y0, y1, G + 0.3, ("n", "w", "s"))
    for xx in (89.6, 95.0, 100.4):
        window(p, "barn_doors", "+y", (xx, y1, G + 0.05), 2.4, 2.7)
    front_row(p, "+y", y1, (88.0, 92.3, 97.7, 101.9), G + 3.6, 0.9, 1.5, cream)
    window(p, "attic_window", "-x", (x0, (y0 + y1) / 2, eave + 0.45), 0.7, 0.7)
    e = "L7E"
    shed(e, "clap", "sw:tin_dark", x1, 107.5, y0, y1, G + 3.6, G + 3.0, "e", oe=0.25)
    foundation(e, x1, 107.5, y0, y1, G + 0.3, ("n", "e", "s"))
    window(e, "barn_doors", "+y", (105.4, y1, G + 0.05), 2.3, 2.5)
    window(e, "door_brown", "+x", (107.5, -7.6, G + 0.3), 1.0, 2.2)


# ===========================================================================
# Alley 86: A14, two brick dwellings "86 1/2" (fronts to the north yard = Blender +Y)
# ===========================================================================
def build_a14():
    p = "A14"
    x0, x1, y0, y1 = fp(29.05, 51.4, 19.9, 26.1)
    eave = G + 6.0
    rise = (y1 - y0) / 2 * TAN(35)
    gable_walls(p, "brick", x0, x1, y0, y1, eave, rise, "x")
    # west gable overhang kept short: the Masonic Hall's rear wall is 0.46 m away (x 28.59)
    gable_roof(p, x0 + 0.15, x1, y0, y1, eave, rise, "x", oe=0.3, og=0.15)
    ridge = eave + rise
    for cx in (35.0, 40.2, 45.4):
        chimney(p, cx, (y0 + y1) / 2, ridge - 0.6, ridge + 0.9)
    fl = G + 0.45
    for doors, xs in (((31.6, 37.6), (30.4, 33.4, 35.6, 38.9)), ((42.8, 48.8), (41.6, 44.6, 46.8, 50.1))):
        for d in doors:
            window(p, "door_brown" if d < 40 else "door_green", "+y", (d, y1, fl), 0.95, 2.15)
            box(p, "concrete", d - 0.6, d + 0.6, y1, y1 + 0.7, 0.0, fl)
        brick_row(p, "+y", y1, [x for x in xs if all(abs(x - d) > 0.9 for d in doors)], fl + 0.75, 0.9, 1.6)
        brick_row(p, "+y", y1, xs, fl + 3.4, 0.9, 1.5)
    # west gable end, seen down alley 86
    brick_row(p, "-x", x0, (-24.6, -21.4), fl + 0.75, 0.9, 1.6)
    brick_row(p, "-x", x0, (-24.6, -21.4), fl + 3.4, 0.9, 1.5)
    window(p, "attic_window", "-x", (x0, (y0 + y1) / 2, eave + 0.4), 0.6, 0.7)
    front_row(p, "-y", y0, (32.0, 38.0, 43.4, 49.2), fl + 3.4, 0.9, 1.5, green)


# ===========================================================================
# Higgins Ave, south side (fronts at Blender y1 = -z, facing +Y)
# ===========================================================================
def build_h1():
    """Children's Choir School (built as a stable): 2-storey stuccoed brick, flat composition
    roof behind a parapet; auto room below, hall above."""
    p = "H1"
    x0, x1, y0, y1 = fp(34.4, 43.3, 70.3, 83.0)
    top = G + 7.0
    flat_top(p, "sw:paint_cream", x0, x1, y0, y1, top, roof="sw:tin_dark")
    box(p, "sw:paint_white", x0 - 0.05, x1 + 0.05, y0 - 0.05, y1 + 0.08, G + 3.3, G + 3.5,
        sides=("n", "e", "w", "t", "b"))                                         # band at the hall floor
    window(p, "barn_doors", "+y", (38.85, y1, G), 3.2, 2.9)                     # auto door
    window(p, "door_brown", "+y", (41.9, y1, G + 0.15), 1.0, 2.3)
    window(p, cream(), "+y", (35.7, y1, G + 1.0), 1.0, 1.6)
    front_row(p, "+y", y1, (35.9, 38.85, 41.8), G + 4.0, 1.0, 2.2, cream)       # tall hall windows
    ys = (-81.0, -77.8, -74.6, -71.6)
    front_row(p, "-x", x0, ys, G + 4.0, 1.0, 2.2, cream)
    front_row(p, "-x", x0, ys[1:3], G + 1.1, 0.9, 1.4, cream)
    front_row(p, "+x", x1, ys, G + 4.0, 1.0, 2.2, cream)
    chimney(p, x1 - 0.8, -81.5, top - 0.2, top + 1.3)


def build_h2():
    """Dwelling 5 Higgins: main block with a front gable, east wing (side gable) across the
    front, porch across both."""
    p = "H2"
    x0, x1, y0, y1 = fp(45.8, 50.7, 71.5, 84.8)
    eave, fl = G + 6.0, G + 0.6
    pitch = 38
    rise = (x1 - x0) / 2 * TAN(pitch)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "y", oe=0.4, og=0.35)
    foundation(p, x0, x1, y0, y1, fl, ("n", "s", "e", "w"))
    chimney(p, 48.25, -80.5, eave + rise - 0.9, eave + rise + 0.7)
    # east wing 50.7 .. 55.9, z 71.5 .. 75.8, lower ridge along x
    wx0, wx1, wy0, wy1 = 50.4, 55.9, -75.8, -71.5
    weave = G + 5.6
    wrise = (wy1 - wy0) / 2 * TAN(35)
    gable_walls(p, "clap", wx0, wx1, wy0, wy1, weave, wrise, "x")
    gable_roof(p, x1, wx1, wy0, wy1, weave, wrise, "x", oe=0.35, og=0.3)
    foundation(p, x1, wx1, wy0, wy1, fl, ("n", "s", "e"))
    porch(p, 46.8, 54.3, y1, -69.7, "n", fl, G + 3.35, (47.0, 49.5, 51.9, 54.1), steps_x=(49.0,))
    # front: door + window in the gable block, two windows in the wing; upper floor
    window(p, "door_brown", "+y", (49.0, y1, fl), 0.95, 2.15)
    window(p, cream(), "+y", (47.0, y1, fl + 0.75), 0.9, 1.7)
    front_row(p, "+y", y1, (52.0, 54.6), fl + 0.75, 0.9, 1.7, cream)
    front_row(p, "+y", y1, (47.0, 49.5, 52.0, 54.6), fl + 3.55, 0.9, 1.6, cream)
    window(p, "attic_window", "+y", (48.25, y1, eave + 0.55), 0.7, 0.75)
    # west side (towards Main St) and the wing's east end, the main block's east side behind it
    front_row(p, "-x", x0, (-74.0, -77.8, -81.6), fl + 0.75, 0.9, 1.7, cream)
    front_row(p, "-x", x0, (-74.0, -77.8, -81.6), fl + 3.55, 0.9, 1.6, cream)
    front_row(p, "+x", wx1, (-73.65,), fl + 0.75, 0.9, 1.7, cream)
    front_row(p, "+x", x1, (-78.6, -82.4), fl + 0.75, 0.9, 1.7, cream)
    front_row(p, "+x", x1, (-78.6, -82.4), fl + 3.55, 0.9, 1.6, cream)


# ===========================================================================
# Tier 2: H3 (north side of Higgins), H4 blacksmith, H5 double dwelling on Spring St
# ===========================================================================
def build_h3():
    p = "H3"
    x0, x1, y0, y1 = fp(61.8, 73.5, 52.4, 58.6)          # front at y0 = -58.6, facing Higgins (-Y)
    eave = G + 6.0
    rise = (y1 - y0) / 2 * TAN(35)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.35, og=0.3)
    rx0, rx1, ry0, ry1 = 66.6, 73.5, -52.7, -44.4      # rear ell, ridge along y
    rr = (rx1 - rx0) / 2 * TAN(32)
    gable_walls(p, "clap", rx0, rx1, ry0, ry1, eave - 0.4, rr, "y")
    gable_roof(p, rx0, rx1, -52.4, ry1, eave - 0.4, rr, "y", oe=0.3, og=0.3)
    box(p, "sw:wood_grey", 62.6, 72.7, y0 - 1.6, y0, 0.0, G + 0.5, sides=("t", "s", "e", "w"))     # porch deck
    slab(p, "sw:tin_dark", "sw:paint_white", [(62.45, y0, G + 3.6), (72.85, y0, G + 3.6),
                                              (72.85, y0 - 1.8, G + 3.3), (62.45, y0 - 1.8, G + 3.3)], 0.12)
    for px in (62.75, 67.65, 72.55):
        box(p, "sw:paint_white", px - 0.08, px + 0.08, y0 - 1.55, y0 - 1.39, G + 0.5, G + 3.3,
            sides=("n", "s", "e", "w"))
    window(p, "door_brown", "-y", (67.7, y0, G + 0.6), 0.95, 2.15)
    front_row(p, "-y", y0, (63.8, 65.8, 69.6, 71.6), G + 1.35, 0.9, 1.7, cream)
    front_row(p, "-y", y0, (63.8, 65.8, 69.6, 71.6), G + 4.15, 0.9, 1.6, cream)
    chimney(p, 64.5, (y0 + y1) / 2, eave + rise - 0.6, eave + rise + 0.8)


def build_h4():
    p = "H4"
    x0, x1, y0, y1 = fp(91.9, 102.8, 45.8, 53.0)
    eave = G + 4.5
    rise = (y1 - y0) / 2 * TAN(35)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.3, og=0.25, top="sw:tin_dark")
    window(p, "barn_doors", "+x", (x1, (y0 + y1) / 2, G), 2.8, 2.8)
    chimney(p, 94.0, (y0 + y1) / 2, eave + rise - 0.5, eave + rise + 1.2)


def build_h5():
    p = "H5"
    x0, x1, y0, y1 = fp(88.2, 102.2, 72.7, 84.1)          # front on Spring St = +x
    eave = G + 6.0
    rise = (x1 - x0) / 2 * TAN(30)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "y", oe=0.4, og=0.3)
    box(p, "sw:wood_grey", x1, x1 + 1.8, y0 + 0.6, y1 - 0.6, 0.0, G + 0.5, sides=("t", "e", "n", "s"))
    slab(p, "sw:tin_dark", "sw:paint_white", [(x1, y0 + 0.45, G + 3.6), (x1, y1 - 0.45, G + 3.6),
                                              (x1 + 2.0, y1 - 0.45, G + 3.3), (x1 + 2.0, y0 + 0.45, G + 3.3)], 0.12)
    front_row(p, "+y", y1, (90.6, 94.4, 98.2), G + 4.15, 0.9, 1.6, cream)        # north side, seen down Higgins
    front_row(p, "+y", y1, (90.6, 98.2), G + 1.35, 0.9, 1.7, cream)
    for cy in (-80.5, -76.3):
        chimney(p, 95.2, cy, eave + rise - 0.6, eave + rise + 0.6)


# ===========================================================================
# Ground (scene x, z in comments; Blender y = -z)
# ===========================================================================
def lane_quad(part, x0, x1, y0, y1, y=LANE_Y):
    """earth lane surface (box UVs as js/ground.js's lanes: 2 m tile)"""
    bflat(part, "earth", x0, x1, y0, y1, y)


def road_quad(part, x0, x1, y0, y1, along_x):
    pts = [Vector((x0, y0, ROAD_Y)), Vector((x1, y0, ROAD_Y)), Vector((x1, y1, ROAD_Y)), Vector((x0, y1, ROAD_Y))]
    if along_x:        # Higgins Ave: js/ground.js's arm, u = (z - 65.4) / 6.4 + 0.5, v = x / 6.4
        uvs = [((-p.y - 65.4) / 6.4 + 0.5, p.x / 6.4) for p in pts]
    else:              # Spring St, as the Bloomfield model: u = (x - 116.45) / 6.4 + 0.5, v = z / 6.4
        uvs = [((p.x - 116.45) / 6.4 + 0.5, -p.y / 6.4) for p in pts]
    add(part, "road", pts, uvs)


def build_ground():
    # --- alley 80 east of x 57 (lane follows the building lines), across the Spring St walk ---
    # Blender y: north edge (L1 4.3, L2 5.1, L3/L4 5.0), south edge (A15 -1.5, L5 -2.4, L6/L7 -4.5)
    lane_quad("Alley", ALLEY_JOIN, 65.3, -1.5, 4.3)
    lane_quad("Alley", 65.3, 70.9, -1.5, 5.1)
    lane_quad("Alley", 70.9, 77.4, -2.4, 5.1)
    lane_quad("Alley", 77.4, 80.3, -2.4, 5.0)
    lane_quad("Alley", 80.3, 95.0, -4.5, 5.0)
    lane_quad("Alley", 95.0, SPRING_W, -4.5, 5.0)
    lane_quad("Alley", SPRING_W, 111.0, -4.5, 5.0)                     # across the walk to the road
    lane_quad("Alley", 42.62, ALLEY_JOIN, 3.3, 4.3)                     # beside L1, north of js/ground.js's lane
    lane_quad("Alley", 86.4, 107.7, 5.0, 10.65)                          # floor of the open wagon shed
    lane_quad("Alley", 107.7, SPRING_W, 5.0, 11.0)                       # yard gate beside the wagon shed
    bskirt("Alley", "earth", (SPRING_W, 5.0), (SPRING_W, 11.0), G, LANE_Y - 0.02, (-1, 0, 0))
    bskirt("Alley", "earth", (107.7, 11.0), (SPRING_W, 11.0), G, LANE_Y - 0.02, (0, -1, 0))
    # --- back lots south of the alley (z 1.3 .. 62.1), worn grass / trodden earth ---
    bflat("LotAlley", "earth", 31.56, ALLEY_JOIN, -16.9, -1.3, G)
    bflat("LotAlley", "earth", ALLEY_JOIN, 70.9, -16.9, -1.5, G)
    bflat("LotAlley", "earth", 70.9, 80.3, -16.9, -2.4, G)
    bflat("LotAlley", "earth", 80.3, SPRING_W, -16.9, -4.5, G)
    bskirt("LotAlley", "earth", (31.56, -1.3), (ALLEY_JOIN, -1.3), G, -0.02, (0, 1, 0))
    bskirt("LotAlley", "earth", (ALLEY_JOIN, -1.3), (ALLEY_JOIN, -1.5), G, -0.02, (1, 0, 0))
    for (a, ya), (b, yb) in (((ALLEY_JOIN, -1.5), (70.9, -1.5)), ((70.9, -2.4), (80.3, -2.4)),
                             ((80.3, -4.5), (SPRING_W, -4.5))):
        bskirt("LotAlley", "earth", (a, ya), (b, yb), G, -0.02, (0, 1, 0))
    bskirt("LotAlley", "earth", (70.9, -1.5), (70.9, -2.4), G, -0.02, (1, 0, 0))
    bskirt("LotAlley", "earth", (80.3, -2.4), (80.3, -4.5), G, -0.02, (1, 0, 0))
    yards = [(29.0, SPRING_W, -21.7, -16.9), (28.6, SPRING_W, -41.2, -21.7), (40.6, SPRING_W, -48.4, -41.2),
             (31.0, SPRING_W, -62.1, -48.4)]
    for x0, x1, y0, y1 in yards:
        xm = (x0 + x1) / 2 if x1 - x0 > 50 else None
        for a, b in ((x0, xm), (xm, x1)) if xm else ((x0, x1),):
            bflat("Yards", "grass", a, b, y0, y1, G)
    bskirt("Yards", "grass", (29.0, -16.9), (29.0, -21.7), G, -0.02, (-1, 0, 0))      # end of alley 86
    # --- north of the alley, behind L1-L4 (meets the Bloomfield model's lots at z -49.1 / -45 / -40) ---
    bflat("LotN", "earth", 33.7, 45.0, 15.9, 49.1, G)
    bflat("LotN", "earth", 45.0, 75.5, 11.0, 49.1, G)
    bflat("LotN", "earth", 75.5, 98.0, 11.0, 45.0, G)
    bflat("LotN", "earth", 98.0, SPRING_W, 11.0, 40.0, G)
    bskirt("LotN", "earth", (33.7, 15.9), (45.0, 15.9), G, -0.02, (0, -1, 0))
    bskirt("LotN", "earth", (45.0, 11.3), (45.0, 15.9), G, -0.02, (-1, 0, 0))
    # --- Higgins Ave east of x 40: road z 62.9 .. 67.9, earth margins, to the Spring St road ---
    xs = split(HIGGINS_JOIN, 111.0, 18.0)
    for a, b in zip(xs, xs[1:]):
        road_quad("Road", a, b, -67.9, -62.9, True)
    for a, b in zip(split(HIGGINS_JOIN, SPRING_W, 18.0), split(HIGGINS_JOIN, SPRING_W, 18.0)[1:]):
        bflat("Margin", "earth", a, b, -62.9, -62.1, G)
        bflat("Margin", "earth", a, b, -68.7, -67.9, G)
    bskirt("Margin", "earth", (HIGGINS_JOIN, -62.9), (SPRING_W, -62.9), G, ROAD_Y - 0.02, (0, -1, 0))
    bskirt("Margin", "earth", (HIGGINS_JOIN, -67.9), (SPRING_W, -67.9), G, ROAD_Y - 0.02, (0, 1, 0))
    # --- lots south of Higgins Ave (H1, H2, H5), lawns ---
    for a, b in ((31.5, 44.0), (44.0, 70.0), (70.0, SPRING_W)):
        bflat("Lawns", "grass", a, b, -90.0, -68.7, G)
    bskirt("Lawns", "grass", (31.5, -68.7), (31.5, -90.0), G, -0.02, (-1, 0, 0))
    bskirt("Lawns", "grass", (31.5, -90.0), (SPRING_W, -90.0), G, -0.02, (0, -1, 0))
    for cx, y_porch in ((49.0, -69.7),):                                        # H2 path to the porch steps
        bflat("Walk", "concrete", cx - 0.6, cx + 0.6, y_porch + 0.7, -68.7, G + 0.012)
    bflat("Walk", "concrete", 38.85 - 1.8, 38.85 + 1.8, -70.3, -68.7, G + 0.012)        # H1 drive apron
    # --- Spring St, z -40 (end of the Bloomfield stub) .. 90 ---
    ys = split(-90.0, 40.0, 13.0)
    for a, b in zip(ys, ys[1:]):
        road_quad("Road", 111.0, 121.9, a, b, False)
        bflat("Walk", "concrete", 121.9, SPRING_E, a, b, G)
    for a, b in ((-90.0, -68.7), (-62.1, -4.5), (5.0, 40.0)):                   # west walk, cut at the lane mouths
        for c, d in zip(split(a, b, 15.0), split(a, b, 15.0)[1:]):
            bflat("Walk", "concrete", SPRING_W, 111.0, c, d, G)
    road_quad("Road", SPRING_W, 111.0, -67.9, -62.9, True)                      # Higgins mouth
    bflat("Margin", "earth", SPRING_W, 111.0, -68.7, -67.9, G)
    bflat("Margin", "earth", SPRING_W, 111.0, -62.9, -62.1, G)
    bskirt("Curb", "concrete", (111.0, -90.0), (111.0, -68.7), G, ROAD_Y - 0.02, (1, 0, 0))
    bskirt("Curb", "concrete", (111.0, -62.1), (111.0, -4.5), G, ROAD_Y - 0.02, (1, 0, 0))
    bskirt("Curb", "concrete", (111.0, 5.0), (111.0, 40.0), G, ROAD_Y - 0.02, (1, 0, 0))
    bskirt("Curb", "concrete", (121.9, -90.0), (121.9, 40.0), G, ROAD_Y - 0.02, (-1, 0, 0))
    for (a, ya), (b, yb), o in (((SPRING_W, -62.9), (111.0, -62.9), (0, -1, 0)), ((SPRING_W, -67.9), (111.0, -67.9), (0, 1, 0)),
                                ((SPRING_W, -4.5), (111.0, -4.5), (0, 1, 0)), ((SPRING_W, 5.0), (111.0, 5.0), (0, -1, 0))):
        bskirt("Curb", "concrete", (a, ya), (b, yb), G, LANE_Y - 0.02 if abs(ya) < 6 else ROAD_Y - 0.02, o)
    bskirt("Curb", "concrete", (SPRING_E, -90.0), (SPRING_E, 40.0), G, -0.02, (1, 0, 0))
    for a, b in ((SPRING_W, 111.0), (121.9, SPRING_E)):
        bskirt("Curb", "concrete", (a, -90.0), (b, -90.0), G, -0.02, (0, -1, 0))
    bskirt("Road", "road", (111.0, -90.0), (121.9, -90.0), ROAD_Y, -0.02, (0, -1, 0))


# ===========================================================================
# build
# ===========================================================================
BUCKETS.clear()
col = clear_collection()
build_l1()
build_l2()
build_l3()
build_l4()
build_a15()
build_l5()
build_l6()
build_l7()
build_a14()
build_h1()
build_h2()
build_h3()
build_h4()
build_h5()
build_ground()
OBJS = make_objects(col)
for o in OBJS:
    o.name = o.data.name = o.name.replace("SC_", "SE_", 1)
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in OBJS)
print("SidestreetSoutheast built:", len(OBJS), "objects,", tris, "triangles")
