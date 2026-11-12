"""
sidestreet_bloomfield.py - the Bloomfield Ave backdrop east of Main St (PLAN.md "Side streets,
backdrop buildings", sections 1b, 3, 4 and 7): every building a visitor sees looking east down
Bloomfield Ave from Main St, at its Sanborn footprint, as one cheap model, plus the side-street
ground beyond x 60 (where js/ground.js stops), the Spring St stub and the back lots.

North side (fronts face Bloomfield Ave = scene +z = Blender -Y):
  B1   Glass cutting (48 1/2 Main, in the yard), 2-storey brick, 5.5 m, flat     PLAIN-GUESS
  A8/A9 Bakery with flats (12) + bake house (14), 3-storey plastered, 9.75 m, flat roof with
       a wide overhang on paired brackets, 5 bays; 1-storey frame rear and brick oven
                                                              PLAIN-GUESS (NRHP-1980 form)
  A10  Hats & Shoes (16), 2-storey stucco, flat, shop front   PLAIN-GUESS (NRHP-1980 form)
  A11  Photos, 2-storey frame 4 m back, 1-storey front porch, bay on the east side
  B2   Dwelling 20, front gable, 2nd-storey bay on the west side, porch
  B3, B4 Dwellings 22, 24, front gable + west cross gable, canted bay on the west, porch
  B5   Opera House: 2-storey frame hall, gable end to the street (front 9.1 m, rear 6.1 m),
       built intact (decision 7.3-1)                          PLAIN-GUESS
South side (fronts face scene -z = Blender +Y):
  A12  Chinese Laundry (17), 2-storey frame, flat roof with a storefront, front porch strip
  A13  Dwelling (19), front gable, 3-bay porch
  B6   Garage (21), 2-storey red brick, 6.7 m, flat, corbelled cornice, 4 bays, wide garage
       front; office and auto-supply corners               PLAIN-GUESS (NRHP-1980 form)
  B7   Dwelling (23), front gable, shingle roof, porch
  B8   Mallory Mfg. Co. machine shop, 1-storey frame (tier 2)
  B9   "Boarding" stable, 2-storey brick, gable along its length, closing the lane view
       between 68 Main and the Union Hotel
  G1   Flemington Garage (1909), SE corner of Bloomfield Ave and Spring St: 1-storey rock-faced
       concrete block (4.3 m), pale sills and lintels, flat parapet on the Bloomfield part,
       stepped gable parapet (3 steps each side) over the south part of the Spring St side
       with a BLANK bordered panel, grey pitched iron roof behind it, open garage door, two
       block chimneys                                   PHOTO-BASED (1909 card, c. 1910 float)
Ground: Bloomfield Ave road + walks x 60 .. 146, the Spring St stub (x 108.6 .. 124.3) to
z -40, back lots (trodden earth / worn grass) north z -130 .. -89.9 and south z -77.3 .. -45.
No signs or lettering anywhere. No trees (the scene instances backdrop-tree.glb).

Run inside Blender:
    exec(open(r"<project>/tools/blender/sidestreet_bloomfield.py").read())
Every run deletes and rebuilds the "SidestreetBloomfield" collection. Materials, lightmap bake
and GLB export: sidestreet_bloomfield_bake.py (runs this file first).

Shared helpers (boxes, gables, porches, windows, buckets -> objects) are taken from
sidestreet_court.py with `ast`, so both backdrops are built by the same code.

Coordinates: SCENE AXES (the GLB is placed at "0 0 0", rotation "0 0 0"):
    Blender X = scene x (east), Blender Y = -scene z (north = +Y), Blender Z = scene y (up).
So a footprint "x 84.3 .. 91.1; z -109.8 .. -94.6" is Blender y 94.6 .. 109.8.
Ground level: lots, walks and the bottom of every wall at y 0.15; walls skirt down to 0.0.
Road 0.01 (as js/ground.js's Bloomfield Ave arm).
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
COLL = "SidestreetBloomfield"
G = 0.15                       # lot / sidewalk top
ROAD_Y = 0.01
X_JOIN = 60.0                  # js/ground.js draws Bloomfield Ave west of this
X_END = 146.0                  # east end of the modelled road / walks / lots
ATLAS = json.load(open(PROJECT + r"\assets\textures\shared\backdrop_windows.json"))["cells"]
TILE = {"clap": 1.0, "brick": 1.4, "slate": 1.5, "concrete": 3.0, "block": 1.4, "earth": 6.4}
rng = random.Random(1923)
BUCKETS = {}

# --- shared helpers from the Court St backdrop --------------------------------------
_HELPERS = {"P", "newell", "add", "face_out", "solid", "box", "sbox", "gable_walls", "slab", "gable_roof",
            "shed", "cross_gable", "window", "win_row", "cream", "green", "porch", "flat", "skirt",
            "clear_collection", "uv_for", "make_objects"}
_tree = ast.parse(open(COURT, encoding="utf8").read())
_mod = ast.Module(body=[n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name in _HELPERS],
                  type_ignores=[])
exec(compile(_mod, COURT, "exec"), globals())
missing = _HELPERS - {n.name for n in _mod.body}
assert not missing, missing

# material keys -> final material ("earth" = lots, drawn with the road's earth map, box UVs)
FINAL_MAT = {"clap": "clap", "brick": "brick", "slate": "slate", "concrete": "concrete", "road": "road",
             "earth": "road", "atlas": "atlas", "block": "block"}

TAN = lambda deg: math.tan(math.radians(deg))


def fp(x0, x1, z0, z1):
    """scene footprint (x range, z range) -> Blender (x0, x1, y0, y1)"""
    return x0, x1, -z1, -z0


def foundation(part, x0, x1, y0, y1, top, sides, mat="block"):
    """stone base band 3 cm proud of a frame wall"""
    box(part, mat, x0 - 0.03, x1 + 0.03, y0 - 0.03, y1 + 0.03, 0.0, top, sides=sides)


def chimney(part, x, y, z_base, z_top, w=0.55, d=0.55, mat="brick"):
    box(part, mat, x - w / 2, x + w / 2, y - d / 2, y + d / 2, z_base, z_top)
    box(part, mat, x - w / 2 - 0.07, x + w / 2 + 0.07, y - d / 2 - 0.07, y + d / 2 + 0.07,
        z_top - 0.18, z_top + 0.02, sides=("t", "n", "s", "e", "w", "b"))


def flat_top(part, wall, x0, x1, y0, y1, top, coping="sw:stone_cream", roof="sw:tin_dark", walls=True):
    """walls to `top` + a coping slab over the whole footprint (its top face is the roof)"""
    if walls:
        box(part, wall, x0, x1, y0, y1, 0.0, top - 0.15, sides=("n", "s", "e", "w"))
    box(part, coping, x0 - 0.06, x1 + 0.06, y0 - 0.06, y1 + 0.06, top - 0.15, top + 0.03,
        sides=("t", "n", "s", "e", "w", "b"), top=roof)


def front_row(p, n, wall, xs, z, w, h, cells):
    win_row(p, cells if isinstance(cells, list) else [cells() for _ in xs], n, wall, xs, z, w, h)


def sill_lintel(p, n, wall, a, z_sill, w, h, proud=0.07):
    """pale smooth sill under and lintel over an opening (front, top and ends only)"""
    f = {"+y": "n", "-y": "s", "+x": "e", "-x": "w"}[n]
    for z0, z1, ww, sides in ((z_sill - 0.1, z_sill, w + 0.2, (f, "t")), (z_sill + h, z_sill + h + 0.2, w + 0.16, (f, "b"))):
        if n in ("+y", "-y"):
            s = 1 if n == "+y" else -1
            yy = (wall, wall + s * proud)
            box(p, "sw:stone_cream", a - ww / 2, a + ww / 2, min(yy), max(yy), z0, z1, sides=sides)
        else:
            s = 1 if n == "+x" else -1
            xx = (wall, wall + s * proud)
            box(p, "sw:stone_cream", min(xx), max(xx), a - ww / 2, a + ww / 2, z0, z1, sides=sides)


def gable_dwelling(p, x0, x1, y0, y1, front, porch_out, pitch, xs_ground, door_x, xs_up, side_ys,
                   eave=G + 6.0, roof="slate", posts=None, cross=None, west_bay=None, chim_y=None):
    """2-storey frame dwelling, gable end to the street. front 's' = faces -Y (north side of the
    street), 'n' = faces +Y. porch_out = the porch's outer edge (Blender y)."""
    fl = G + 0.6
    rise = (x1 - x0) / 2 * TAN(pitch)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "y", oe=0.4, og=0.35, top=roof)
    foundation(p, x0, x1, y0, y1, fl, ("n", "s", "e", "w"))
    yr = chim_y if chim_y is not None else ((y1 - 1.8) if front == "s" else (y0 + 1.8))
    chimney(p, (x0 + x1) / 2, yr, eave + rise - 0.9, eave + rise + 0.7)
    nf, yf = ("-y", y0) if front == "s" else ("+y", y1)
    posts = posts or [x0 + 0.3 + (x1 - x0 - 0.6) * k / 3 for k in range(4)]
    if front == "s":
        porch(p, x0, x1, porch_out, y0, "s", fl, G + 3.35, posts, steps_x=(door_x,))
    else:
        porch(p, x0, x1, y1, porch_out, "n", fl, G + 3.35, posts, steps_x=(door_x,))
    for cx in xs_ground:
        if cx == door_x:
            window(p, "door_brown" if rng.random() < 0.6 else "door_green", nf, (cx, yf, fl), 0.95, 2.15)
        else:
            window(p, cream(), nf, (cx, yf, fl + 0.75), 0.9, 1.7)
    win_row(p, [cream() for _ in xs_up], nf, yf, xs_up, fl + 3.55, 0.9, 1.6)
    window(p, "attic_window", nf, ((x0 + x1) / 2, yf, eave + 0.55), 0.7, 0.75)
    for n, xw in (("-x", x0), ("+x", x1)):
        win_row(p, [cream() for _ in side_ys], n, xw, side_ys, fl + 0.75, 0.9, 1.7)
        win_row(p, [cream() for _ in side_ys], n, xw, side_ys, fl + 3.55, 0.9, 1.6)
    if cross:                                          # cross gable on the west slope
        yc, wc = cross
        cross_gable(p, "clap", "w", yc, wc, x0, eave, wc / 2 * TAN(pitch), rise / ((x1 - x0) / 2))
        window(p, "attic_window", "-x", (x0, yc, eave + 0.3), 0.6, 0.7)
    if west_bay:                                       # (y0, y1, z0, z1, canted)
        by0, by1, bz0, bz1 = west_bay
        bx0 = x0 - 0.85
        box(p, "clap", bx0, x0, by0, by1, bz0, bz1, sides=("w", "n", "s", "b") if bz0 > G + 0.1 else ("w", "n", "s"))
        box(p, "sw:tin_dark", bx0 - 0.12, x0, by0 - 0.12, by1 + 0.12, bz1, bz1 + 0.12,
            sides=("t", "w", "n", "s", "b"))
        window(p, cream(), "-x", (bx0, (by0 + by1) / 2, bz0 + 0.75 if bz0 < 1 else bz0 + 0.5), 0.9,
               1.6 if bz0 < 1 else 1.5)


# ===========================================================================
# North side
# ===========================================================================
def build_b1():
    p = "B1"
    x0, x1, y0, y1 = fp(33.0, 41.7, -107.7, -102.8)
    top = G + 5.5
    flat_top(p, "brick", x0, x1, y0, y1, top)
    window(p, "door_green", "-y", (34.2, y0, G), 1.0, 2.2)
    front_row(p, "-y", y0, (36.4, 39.6), G + 0.9, 1.0, 1.7, green)
    front_row(p, "-y", y0, (34.4, 37.3, 40.2), G + 3.3, 0.9, 1.5, green)
    front_row(p, "-x", x0, (104.0, 106.5), G + 0.9, 0.9, 1.6, green)
    front_row(p, "-x", x0, (104.0, 106.5), G + 3.3, 0.9, 1.5, green)


def build_a8_a9():
    p = "A8"
    x0, x1, y0, y1 = fp(39.9, 54.2, -102.4, -90.7)
    top = G + 9.75
    box(p, "sw:paint_cream", x0, x1, y0, y1, 0.0, top, sides=("n", "s", "e", "w"))
    # flat roof with a wide overhang (0.65 m) on paired simple brackets (front and west side)
    box(p, "sw:paint_white", x0 - 0.65, x1 + 0.65, y0 - 0.65, y1 + 0.3, top, top + 0.22,
        sides=("t", "n", "s", "e", "w", "b"), top="sw:tin_dark")
    for bx in (40.15, 43.0, 45.9, 48.75, 51.6, 53.95):
        for dx in (-0.16, 0.16):
            box(p, "sw:paint_white", bx + dx - 0.06, bx + dx + 0.06, y0 - 0.6, y0, top - 0.45, top,
                sides=("s", "e", "w", "b"))
    for by in (91.5, 95.4, 99.3, 102.0):
        for dy in (-0.16, 0.16):
            box(p, "sw:paint_white", x0 - 0.6, x0, by + dy - 0.06, by + dy + 0.06, top - 0.45, top,
                sides=("w", "n", "s", "b"))
    # band between the shop storey and the flats
    box(p, "sw:paint_white", x0 - 0.06, x1 + 0.06, y0 - 0.06, y0, G + 3.4, G + 3.65, sides=("s", "t", "b", "e", "w"))
    bays = (41.3, 44.15, 47.05, 49.9, 52.8)
    # ground floor: bakery shop window + door (12), bake-house door + windows (14)
    window(p, cream(), "-y", (41.6, y0, G + 0.55), 2.3, 2.3)
    window(p, "door_brown", "-y", (43.8, y0, G + 0.1), 1.1, 2.5)
    window(p, cream(), "-y", (45.9, y0, G + 0.55), 2.0, 2.3)
    window(p, "door_green", "-y", (48.3, y0, G + 0.1), 1.0, 2.4)
    window(p, "barn_doors", "-y", (50.6, y0, G), 2.2, 2.7)
    window(p, cream(), "-y", (52.95, y0, G + 0.8), 0.9, 1.8)
    for z in (G + 4.15, G + 7.0):
        front_row(p, "-y", y0, bays, z, 0.95, 1.75, cream)
    # west side (towards Main St, above the Rea flats)
    ys = (92.4, 95.4, 98.4, 101.2)
    for z in (G + 1.0, G + 4.15, G + 7.0):
        front_row(p, "-x", x0, ys, z, 0.9, 1.7, cream)
    front_row(p, "+x", x1, ys, G + 4.15, 0.9, 1.7, cream)
    front_row(p, "+x", x1, ys, G + 7.0, 0.9, 1.7, cream)
    chimney(p, 44.0, 101.6, top, top + 1.4)
    chimney(p, 50.0, 101.6, top, top + 1.6)
    # rear: 1-storey frame part (shed roof falling north) and the brick oven
    r = "A8R"
    shed(r, "clap", "sw:tin_dark", 42.0, 47.2, y1, 107.9, G + 3.4, G + 2.8, "n", oe=0.15)
    flat_top(r, "brick", 48.4, 53.6, y1, 107.4, G + 3.0)
    chimney(r, 51.0, 106.5, G + 3.0, G + 6.5, w=0.7, d=0.7)


def build_a10():
    p = "A10"
    x0, x1, y0, y1 = fp(55.9, 60.6, -106.9, -90.7)
    top = G + 6.7
    flat_top(p, "sw:paint_cream", x0, x1, y0, y1, top)
    box(p, "sw:paint_white", x0 - 0.05, x1 + 0.05, y0 - 0.12, y0, G + 3.1, G + 3.45, sides=("s", "t", "b", "e", "w"))
    window(p, cream(), "-y", (57.0, y0, G + 0.5), 1.9, 2.2)
    window(p, "door_brown", "-y", (59.4, y0, G + 0.1), 1.0, 2.4)
    front_row(p, "-y", y0, (57.1, 59.4), G + 3.9, 0.9, 1.6, cream)
    ys = (93.0, 96.8, 100.6, 104.4)
    front_row(p, "-x", x0, ys, G + 1.0, 0.9, 1.6, cream)
    front_row(p, "-x", x0, ys, G + 3.9, 0.9, 1.6, cream)


def build_a11():
    p = "A11"
    x0, x1, y0, y1 = fp(60.62, 66.3, -106.9, -95.1)
    gable_dwelling(p, x0, x1, y0, y1, "s", 93.3, 36, (61.8, 63.6, 65.2), 63.6, (61.9, 65.0),
                   (97.6, 101.2, 104.8))
    # bay on the east side (1 storey, flat top)
    box(p, "clap", x1, x1 + 1.0, 96.1, 98.2, 0.0, G + 3.3, sides=("e", "n", "s"))
    box(p, "sw:tin_dark", x1, x1 + 1.12, 95.98, 98.32, G + 3.3, G + 3.42, sides=("t", "e", "n", "s", "b"))
    window(p, cream(), "+x", (x1 + 1.0, 97.15, G + 1.35), 1.2, 1.7)


def build_b2_b4():
    # B2 (20 Bloomfield): narrow end to the street, 2nd-storey bay on the west side
    x0, x1, y0, y1 = fp(84.3, 91.1, -109.8, -94.6)
    gable_dwelling("B2", x0, x1, y0, y1, "s", 93.2, 38, (85.5, 87.7, 89.9), 87.7, (85.6, 87.7, 89.8),
                   (97.2, 101.0, 104.8, 108.2), west_bay=(98.6, 100.5, G + 3.4, G + 6.0))
    # B3, B4 (22, 24): front gable + cross gable and a canted bay on the west side
    x0, x1, y0, y1 = fp(96.6, 102.2, -108.4, -95.0)
    gable_dwelling("B3", x0, x1, y0, y1, "s", 93.3, 38, (97.7, 99.4, 101.1), 101.1, (97.8, 101.0),
                   (97.0, 104.5, 107.2), cross=(102.6, 3.2), west_bay=(98.0, 100.6, G, G + 3.4))
    x0, x1, y0, y1 = fp(107.7, 113.4, -107.3, -95.1)
    gable_dwelling("B4", x0, x1, y0, y1, "s", 93.4, 38, (108.8, 110.5, 112.3), 112.3, (108.9, 112.2),
                   (97.0, 104.0, 106.4), cross=(102.2, 3.2), west_bay=(98.0, 100.6, G, G + 3.4))


def build_b5():
    """Opera House: 2-storey frame hall, gable end to the street (south), front part 9.1 m,
    rear part 6.1 m, small annex; plain, intact."""
    p = "B5"
    x0, x1, y0, y1 = fp(116.5, 127.8, -116.7, -98.0)
    eave = G + 9.1
    rise = (x1 - x0) / 2 * TAN(34)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "y")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "y", oe=0.45, og=0.4)
    foundation(p, x0, x1, y0, y1, G + 0.5, ("n", "s", "e", "w"))
    xm = (x0 + x1) / 2
    # front: double doors under a small hood, two windows each side, upper hall windows, gable light
    for dx in (-0.6, 0.6):
        window(p, "door_brown", "-y", (xm + dx, y0, G + 0.5), 1.15, 2.6)
    box(p, "sw:paint_white", xm - 1.7, xm + 1.7, y0 - 0.9, y0, G + 3.3, G + 3.45, sides=("t", "s", "e", "w", "b"))
    box(p, "concrete", xm - 1.8, xm + 1.8, y0 - 1.2, y0, 0.0, G + 0.25)
    box(p, "concrete", xm - 1.8, xm + 1.8, y0 - 0.6, y0, 0.0, G + 0.5)
    front_row(p, "-y", y0, (x0 + 1.4, x0 + 3.5, x1 - 3.5, x1 - 1.4), G + 1.3, 0.95, 1.8, cream)
    front_row(p, "-y", y0, (x0 + 1.9, xm - 1.9, xm, xm + 1.9, x1 - 1.9), G + 4.7, 1.0, 2.5, cream)
    window(p, "attic_window", "-y", (xm, y0, eave + 0.9), 1.1, 1.1)
    box(p, "sw:paint_white", x0 - 0.05, x1 + 0.05, y0 - 0.08, y0, G + 4.0, G + 4.25, sides=("s", "t", "b", "e", "w"))
    ys = [y0 + 2.2 + 3.6 * k for k in range(5)]
    for n, xw in (("-x", x0), ("+x", x1)):
        front_row(p, n, xw, ys, G + 1.3, 0.95, 1.8, cream)
        front_row(p, n, xw, ys, G + 4.7, 1.0, 2.6, cream)
    # rear part (stage end), lower gable
    r = "B5R"
    ry0, ry1 = y1, 126.9
    reave = G + 6.1
    gable_walls(r, "clap", x0, x1, ry0 - 0.3, ry1, reave, rise, "y")
    gable_roof(r, x0, x1, ry0, ry1, reave, rise, "y", oe=0.45, og=0.3)
    foundation(r, x0, x1, ry0, ry1, G + 0.5, ("n", "e", "w"))
    window(r, "door_green", "-x", (x0, 122.0, G + 0.5), 1.0, 2.2)
    front_row(r, "-x", x0, (119.0, 124.8), G + 3.4, 0.9, 1.6, cream)
    shed(r, "clap", "sw:tin_dark", 120.4, 124.0, ry1, 130.3, G + 3.4, G + 2.8, "n", oe=0.15)
    chimney(r, 126.6, 124.5, reave + 1.0, reave + rise + 0.6)


# ===========================================================================
# South side (fronts at Blender +Y)
# ===========================================================================
def build_a12():
    p = "A12"
    x0, x1, y0, y1 = fp(57.6, 63.4, -75.6, -64.5)
    flat_top(p, "clap", x0, x1, y0, y1, G + 6.5)
    foundation(p, x0, x1, y0, y1, G + 0.4, ("n", "e", "w"))
    # 1-storey porch strip across the front (flat roof on posts)
    porch(p, x0, x1, y1, 77.3, "n", G + 0.3, G + 3.2, (x0 + 0.25, (x0 + x1) / 2, x1 - 0.25), steps_x=(61.9,),
          roof_fall=0.1)
    window(p, cream(), "+y", (59.4, y1, G + 0.75), 2.2, 2.1)
    window(p, "door_green", "+y", (61.9, y1, G + 0.3), 1.0, 2.3)
    front_row(p, "+y", y1, (59.1, 61.9), G + 3.9, 0.9, 1.6, cream)
    ys = (73.5, 70.0, 66.6)
    front_row(p, "-x", x0, ys, G + 1.0, 0.9, 1.6, cream)
    front_row(p, "-x", x0, ys, G + 3.9, 0.9, 1.6, cream)
    chimney(p, 62.6, 66.0, G + 6.5, G + 7.8)


def build_a13():
    p = "A13"
    x0, x1, y0, y1 = fp(66.9, 74.4, -75.6, -66.9)
    gable_dwelling(p, x0, x1, y0, y1, "n", 77.3, 36, (68.3, 70.65, 73.0), 70.65, (68.3, 70.65, 73.0),
                   (68.6, 72.0, 74.4), chim_y=y0 + 1.2)
    r = "A13R"
    rx0, rx1, ry0, ry1 = 69.2, 74.4, 63.1, y0
    rr = (rx1 - rx0) / 2 * TAN(30)
    gable_walls(r, "clap", rx0, rx1, ry0, ry1 + 0.3, G + 5.4, rr, "y")
    gable_roof(r, rx0, rx1, ry0, ry1, G + 5.4, rr, "y", og=0.25)
    foundation(r, rx0, rx1, ry0, ry1, G + 0.6, ("s", "e", "w"))
    front_row(r, "-x", rx0, (65.0,), G + 1.35, 0.9, 1.6, cream)


def build_b6():
    """Garage, 21 Bloomfield: 2-storey red brick, flat roof, corbelled brick cornice, 4 bays,
    wide wooden garage front, office and auto-supply corners (no lettering)."""
    p = "B6"
    x0, x1, y0, y1 = fp(76.4, 92.7, -77.3, -55.7)
    top = G + 6.7
    box(p, "brick", x0, x1, y0, y1, 0.0, top - 0.55, sides=("n", "s", "e", "w"))
    # corbelled cornice: two stepped brick courses, then a plain parapet with a stone coping
    box(p, "brick", x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, top - 0.55, top - 0.4, sides=("n", "s", "e", "w", "b"))
    box(p, "brick", x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, top - 0.4, top - 0.2, sides=("n", "s", "e", "w", "b"))
    box(p, "sw:stone_cream", x0 - 0.24, x1 + 0.24, y0 - 0.24, y1 + 0.24, top - 0.2, top,
        sides=("t", "n", "s", "e", "w", "b"), top="sw:tin_dark")
    # ground floor: office (west corner), wide garage doors (centre), auto supply (east corner)
    box(p, "sw:wood_grey", x0 + 0.3, x1 - 0.3, y1, y1 + 0.06, G + 3.15, G + 3.45, sides=("n", "t", "b", "e", "w"))
    window(p, cream(), "+y", (78.2, y1, G + 0.6), 2.4, 2.3)
    window(p, "door_brown", "+y", (80.2, y1, G + 0.05), 1.0, 2.5)
    window(p, "engine_doors", "+y", (84.55, y1, G), 6.0, 3.1)
    window(p, "door_brown", "+y", (88.9, y1, G + 0.05), 1.0, 2.5)
    window(p, cream(), "+y", (90.9, y1, G + 0.6), 2.4, 2.3)
    # upper floor: 4 bays of paired windows
    for bx in (78.6, 82.75, 86.35, 90.5):
        front_row(p, "+y", y1, (bx - 0.6, bx + 0.6), G + 4.0, 0.95, 1.7, green)
    # west wall (towards Main St): 6 bays up, 4 down (a door to the yard)
    ys = [y0 + 2.0 + 3.55 * k for k in range(6)]
    front_row(p, "-x", x0, ys, G + 4.0, 0.95, 1.7, green)
    front_row(p, "-x", x0, ys[1:5], G + 1.1, 0.95, 1.8, green)
    window(p, "barn_doors", "-x", (x0, ys[0], G), 2.4, 2.8)
    front_row(p, "+x", x1, ys, G + 4.0, 0.95, 1.7, green)
    chimney(p, 91.6, 57.0, top - 0.2, top + 1.6, w=0.7, d=0.7)


def build_b7():
    x0, x1, y0, y1 = fp(99.0, 105.6, -75.2, -63.1)
    gable_dwelling("B7", x0, x1, y0, y1, "n", 76.7, 38, (100.3, 102.3, 104.3), 102.3, (100.3, 104.3),
                   (65.0, 68.6, 72.4), chim_y=y0 + 2.0)


def build_b8():
    p = "B8"
    x0, x1, y0, y1 = fp(55.9, 68.6, -62.8, -55.1)
    eave = G + 3.6
    rise = (y1 - y0) / 2 * TAN(24)
    gable_walls(p, "clap", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", top="sw:tin_dark", oe=0.3, og=0.25)
    window(p, "barn_doors", "-x", (x0, 58.9, G), 2.6, 2.7)
    front_row(p, "+y", y1, (58.0, 61.0, 64.0, 67.0), G + 1.0, 1.0, 1.5, cream)
    front_row(p, "-y", y0, (58.0, 62.2, 66.4), G + 1.0, 1.0, 1.5, cream)
    chimney(p, 64.2, (y0 + y1) / 2, eave + rise - 0.4, eave + rise + 1.4)


def build_b9():
    """'Boarding' stable: 2-storey brick, gable along its length (ridge E-W); its west gable end
    closes the view down the lane between 68 Main and the Union Hotel."""
    p = "B9"
    x0, x1, y0, y1 = fp(75.5, 102.8, -54.4, -45.7)
    eave = G + 6.0
    rise = (y1 - y0) / 2 * TAN(35)
    gable_walls(p, "brick", x0, x1, y0, y1, eave, rise, "x")
    gable_roof(p, x0, x1, y0, y1, eave, rise, "x", oe=0.3, og=0.3)
    ym = (y0 + y1) / 2
    window(p, "barn_doors", "-x", (x0, ym, G), 2.8, 3.0)
    window(p, "barn_doors", "-x", (x0, ym, G + 3.6), 1.6, 1.9)       # hay door
    window(p, "attic_window", "-x", (x0, ym, eave + 1.0), 0.8, 0.8)
    front_row(p, "-x", x0, (y0 + 1.3, y1 - 1.3), G + 1.4, 0.8, 1.1, green)
    xs = [x0 + 2.2 + 3.3 * k for k in range(8)]
    front_row(p, "+y", y1, xs, G + 3.9, 0.8, 1.2, green)
    front_row(p, "+y", y1, xs[::2], G + 1.4, 0.8, 1.1, green)
    for k, xx in enumerate((80.0, 89.0, 98.0)):
        window(p, "barn_doors", "+y", (xx, y1, G), 2.6, 2.8)


# ===========================================================================
# G1  Flemington Garage (1909 card, c. 1910 float card)
# ===========================================================================
def build_g1():
    p = "G1"
    x0, x1, y0, y1 = fp(124.2, 145.8, -77.3, -55.7)     # north wall on the property line (map -77.6 +-1.5)
    wall = G + 4.3
    ys0, ys1 = 55.7, 66.1                      # south part under the stepped gable / iron roof
    yc = (ys0 + ys1) / 2                       # 60.9: garage door, sign and gable centre
    # north part (Bloomfield): walls to the parapet top, flat roof
    box(p, "block", x0, x1, ys1, y1, 0.0, wall, sides=("n", "e", "w"))
    box(p, "block", x0, x1, ys1, y1, wall - 0.12, wall, sides=("t",), top="sw:tin_dark")
    # south part: walls to the eave, gable roof (ridge E-W) behind the stepped parapet
    rise = 1.25
    box(p, "block", x0, x0 + 0.3, ys0, ys1, 0.0, wall, sides=("w", "s"))
    gable_walls(p, "block", x0 + 0.3, x1, ys0, ys1, wall, rise, "x")
    gable_roof(p, x0 + 0.3, x1, ys0, ys1, wall, rise, "x", oe=0.12, og=0.15, t=0.1, top="sw:tin_dark")
    # stepped gable parapet on the Spring St wall: 3 steps each side, flat top (peak ~5.85 m)
    steps = [(ys0, G + 4.8), (57.45, G + 5.3), (59.2, G + 5.85), (62.6, G + 5.3), (64.35, G + 4.8)]
    prof = []                                  # (y, z) outline, south to north, along the top
    for i, (ya, za) in enumerate(steps):
        yb = steps[i + 1][0] if i + 1 < len(steps) else ys1
        prof += [(ya, za), (yb, za)]
    outline = [(ys0, wall)] + prof + [(ys1, wall)]
    t = 0.3
    front = [Vector((x0, yy, zz)) for yy, zz in outline]
    back = [Vector((x0 + t, yy, zz)) for yy, zz in outline]
    faces = [front, back[::-1]]
    for i in range(len(outline) - 1):
        faces.append([front[i], front[i + 1], back[i + 1], back[i]])
    solid(p, faces, "block")
    for i in range(1, len(outline) - 2, 2):    # pale caps on the step treads
        (ya, za), (yb, zb) = outline[i], outline[i + 1]
        box(p, "sw:stone_cream", x0 - 0.05, x0 + t + 0.05, ya, yb, za, za + 0.07, sides=("t", "w"))
    # blank sign panel with a raised border, centred over the garage door
    sw, sz0, sz1 = 3.0, G + 3.45, G + 4.5
    box(p, "sw:stone_cream", x0 - 0.05, x0, yc - sw / 2, yc + sw / 2, sz0, sz1, sides=("w", "t", "b", "n", "s"))
    for a0, a1, b0, b1 in ((yc - sw / 2, yc + sw / 2, sz0, sz0 + 0.12), (yc - sw / 2, yc + sw / 2, sz1 - 0.12, sz1),
                           (yc - sw / 2, yc - sw / 2 + 0.12, sz0 + 0.12, sz1 - 0.12),
                           (yc + sw / 2 - 0.12, yc + sw / 2, sz0 + 0.12, sz1 - 0.12)):
        box(p, "sw:paint_white", x0 - 0.1, x0 - 0.05, a0, a1, b0, b1, sides=("w",))
    # Spring St side, north to south: window, door, window, small window, large window,
    # open garage door (~3 x 2.8 m), window
    sp = [("win", 76.25, 1.0, 1.55, G + 1.0), ("door", 74.1, 1.0, 2.2, G + 0.05), ("win", 72.0, 1.0, 1.55, G + 1.0),
          ("small", 69.2, 0.75, 0.8, G + 1.75), ("large", 65.0, 1.9, 1.8, G + 0.8),
          ("garage", yc, 3.0, 2.8, G + 0.02), ("win", 57.6, 1.0, 1.55, G + 1.0)]
    for kind, a, w, h, z in sp:
        if kind == "garage":
            window(p, "iron_dark", "-x", (x0, a, z), w, h, off=0.01)
            box(p, "sw:stone_cream", x0 - 0.06, x0, a - w / 2 - 0.1, a + w / 2 + 0.1, z + h, z + h + 0.22,
                sides=("w", "t", "b", "n", "s"))
            continue
        cell = {"win": cream(), "door": "door_brown", "small": "small_window", "large": "win_cream_3"}[kind]
        window(p, cell, "-x", (x0, a, z), w, h)
        if kind == "door":
            box(p, "sw:stone_cream", x0 - 0.06, x0, a - w / 2 - 0.1, a + w / 2 + 0.1, z + h, z + h + 0.2,
                sides=("w", "t", "b", "n", "s"))
        else:
            sill_lintel(p, "-x", x0, a, z, w, h)
    # Bloomfield Ave side: six evenly spaced windows
    for k in range(6):
        a = 126.0 + 3.56 * k
        window(p, cream(), "+y", (a, y1, G + 1.0), 1.0, 1.55)
        sill_lintel(p, "+y", y1, a, G + 1.0, 1.0, 1.55)
    # east and south walls: a few plain windows
    front_row(p, "+x", x1, (60.0, 70.0), G + 1.0, 1.0, 1.55, cream)
    front_row(p, "-y", y0, (130.0, 138.0), G + 1.0, 1.0, 1.55, cream)
    # two block chimneys: a tall one mid-roof behind the flat parapet, one near the east end
    chimney(p, 131.5, 70.5, wall - 0.1, G + 7.4, w=0.6, d=0.6, mat="block")
    chimney(p, 142.6, 74.0, wall - 0.1, G + 6.0, w=0.55, d=0.55, mat="block")


# ===========================================================================
# Ground beyond x 60: road, walks, the Spring St stub, lots, house paths
# ===========================================================================
def road_quad(part, x0, x1, y0, y1, along_x=True):
    """road surface (scene axes, Blender y) with js/ground.js's arm UVs: u across the street
    (6.4 m tile), v along it, so the wheel tracks line up at x 60"""
    pts = [Vector((x0, y0, ROAD_Y)), Vector((x1, y0, ROAD_Y)), Vector((x1, y1, ROAD_Y)), Vector((x0, y1, ROAD_Y))]
    if along_x:        # Bloomfield Ave: u = (z - -83.2) / 6.4 + 0.5, v = x / 6.4
        uvs = [((-p.y + 83.2) / 6.4 + 0.5, p.x / 6.4) for p in pts]
    else:              # Spring St: u = (x - 116.45) / 6.4 + 0.5, v = z / 6.4
        uvs = [((p.x - 116.45) / 6.4 + 0.5, -p.y / 6.4) for p in pts]
    add(part, "road", pts, uvs)


def bflat(part, mat, x0, x1, y0, y1, z):
    face_out(part, mat, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], (0, 0, 1))


def bskirt(part, mat, a, b, z_top, z_bot, outward):
    face_out(part, mat, [(a[0], a[1], z_bot), (b[0], b[1], z_bot), (b[0], b[1], z_top), (a[0], a[1], z_top)],
             outward)


def split(a, b, step):
    n = max(1, round((b - a) / step))
    return [a + (b - a) * k / n for k in range(n + 1)]


def build_ground():
    # Bloomfield Ave road (z -86.5 .. -79.9 -> y 79.9 .. 86.5) and walks to x 146
    xs = split(X_JOIN, X_END, 10.0)
    for a, b in zip(xs, xs[1:]):
        road_quad("Road", a, b, 79.9, 86.5)
        bflat("Walk", "concrete", a, b, 86.5, 89.9, G)                    # north walk (3.4 m)
    for a, b in zip(split(X_JOIN, 108.6, 10.0), split(X_JOIN, 108.6, 10.0)[1:]):
        bflat("Walk", "concrete", a, b, 77.3, 79.9, G)                    # south walk (2.6 m)
    bflat("Walk", "concrete", 124.3, X_END, 77.3, 79.9, G)
    bskirt("Curb", "concrete", (X_JOIN, 86.5), (X_END, 86.5), G, ROAD_Y - 0.02, (0, -1, 0))
    bskirt("Curb", "concrete", (X_JOIN, 79.9), (111.0, 79.9), G, ROAD_Y - 0.02, (0, 1, 0))
    bskirt("Curb", "concrete", (121.9, 79.9), (X_END, 79.9), G, ROAD_Y - 0.02, (0, 1, 0))
    for y0, y1 in ((86.5, 89.9), (77.3, 79.9)):
        bskirt("Curb", "concrete", (X_END, y0), (X_END, y1), G, 0.0, (1, 0, 0))
    # Spring St (50 ft: x 108.6 .. 124.3), south from Bloomfield Ave to z -40
    ys = split(40.0, 79.9, 10.0)
    for a, b in zip(ys, ys[1:]):
        road_quad("Road", 111.0, 121.9, a, b, along_x=False)
        bflat("Walk", "concrete", 108.6, 111.0, a, b, G)
        bflat("Walk", "concrete", 121.9, 124.3, a, b, G)
    bskirt("Curb", "concrete", (111.0, 40.0), (111.0, 79.9), G, ROAD_Y - 0.02, (1, 0, 0))
    bskirt("Curb", "concrete", (121.9, 40.0), (121.9, 79.9), G, ROAD_Y - 0.02, (-1, 0, 0))
    for a, b in ((108.6, 111.0), (121.9, 124.3)):
        bskirt("Curb", "concrete", (a, 40.0), (b, 40.0), G, 0.0, (0, -1, 0))
    # house paths and the Opera House walk (walk -> porch steps)
    for cx, y_porch in ((87.7, 93.2), (101.1, 93.3), (112.3, 93.4)):
        bflat("Walk", "concrete", cx - 0.6, cx + 0.6, 89.9, y_porch - 0.7, G + 0.012)
    bflat("Walk", "concrete", 120.35, 123.95, 89.9, 98.0 - 1.2, G + 0.012)
    bflat("Walk", "concrete", 62.9, 64.3, 89.9, 93.3 - 0.7, G + 0.012)
    for cx, y_porch in ((70.65, 77.3), (102.3, 76.7)):
        if y_porch + 0.7 < 77.3:
            bflat("Walk", "concrete", cx - 0.6, cx + 0.6, y_porch + 0.7, 77.3, G + 0.012)
    # north lots (z -130 .. -89.9), from behind the Rea flats (x 34.8) to x 146
    lx = [34.8, 47.0, 60.0, 72.0, 84.0, 96.0, 108.0, 120.0, 133.0, X_END]
    for a, b in zip(lx, lx[1:]):
        for y0, y1 in ((89.9, 108.0), (108.0, 130.0)):
            bflat("LotsN", "earth", a, b, y0, y1, G)
    bskirt("LotsN", "earth", (34.8, 130.0), (34.8, 99.6), G, -0.05, (-1, 0, 0))
    bskirt("LotsN", "earth", (34.8, 130.0), (X_END, 130.0), G, -0.05, (0, 1, 0))
    bskirt("LotsN", "earth", (X_END, 89.9), (X_END, 130.0), G, -0.05, (1, 0, 0))
    # south lots (z -77.3 .. -49.1 / -45), behind the bank (x 33.4) to Spring St; and the G1 lot
    sx = [33.4, 45.0, 56.0, 66.0, 75.5, 87.0, 98.0, 108.6]
    for a, b in zip(sx, sx[1:]):
        y0 = 49.1 if b <= 75.5 else 45.0
        for ya, yb in ((y0, 63.0), (63.0, 77.3)):
            bflat("LotsS", "earth", a, b, ya, yb, G)
    bskirt("LotsS", "earth", (33.4, 49.1), (33.4, 77.3), G, -0.05, (-1, 0, 0))
    bskirt("LotsS", "earth", (33.4, 49.1), (75.5, 49.1), G, -0.05, (0, -1, 0))
    bskirt("LotsS", "earth", (75.5, 45.0), (75.5, 49.1), G, -0.05, (-1, 0, 0))
    bskirt("LotsS", "earth", (75.5, 45.0), (108.6, 45.0), G, -0.05, (0, -1, 0))
    bskirt("LotsS", "earth", (108.6, 40.0), (108.6, 45.0), G, -0.05, (-1, 0, 0))
    for a, b in ((124.3, 135.0), (135.0, X_END)):
        for ya, yb in ((45.0, 61.0), (61.0, 77.3)):
            bflat("LotsG", "earth", a, b, ya, yb, G)
    bskirt("LotsG", "earth", (124.3, 45.0), (X_END, 45.0), G, -0.05, (0, -1, 0))
    bskirt("LotsG", "earth", (X_END, 45.0), (X_END, 77.3), G, -0.05, (1, 0, 0))
    bskirt("LotsG", "earth", (124.3, 40.0), (124.3, 45.0), G, -0.05, (1, 0, 0))
    bflat("LotsG", "earth", 124.3, 135.0, 40.0, 45.0, G)
    bflat("LotsS", "earth", 98.0, 108.6, 40.0, 45.0, G)
    bskirt("LotsS", "earth", (98.0, 40.0), (108.6, 40.0), G, -0.05, (0, -1, 0))
    bskirt("LotsS", "earth", (98.0, 40.0), (98.0, 45.0), G, -0.05, (-1, 0, 0))
    bskirt("LotsG", "earth", (124.3, 40.0), (135.0, 40.0), G, -0.05, (0, -1, 0))
    bskirt("LotsG", "earth", (135.0, 40.0), (135.0, 45.0), G, -0.05, (1, 0, 0))


# ===========================================================================
# build
# ===========================================================================
BUCKETS.clear()
col = clear_collection()
build_b1()
build_a8_a9()
build_a10()
build_a11()
build_b2_b4()
build_b5()
build_a12()
build_a13()
build_b6()
build_b7()
build_b8()
build_b9()
build_g1()
build_ground()
OBJS = make_objects(col)
for o in OBJS:
    o.name = o.data.name = o.name.replace("SC_", "SB_", 1)
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in OBJS)
print("SidestreetBloomfield built:", len(OBJS), "objects,", tris, "triangles")
