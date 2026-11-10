"""
prepare_bank_hall.py - draws `assets/textures/shared/bank_hall.jpg`: what you see through the
ground-floor glass of the Bank Building (56-66 Main St), c. 1920. Own work (no download, no
lettering, no signs). Run INSIDE Blender (numpy; the image is saved with bpy), before
tools/blender/bank_building.py:

    exec(open(r"<project>/tools/prepare_bank_hall.py").read())

Same method as tools/prepare_hotel_lobby.py / prepare_shop_interior.py: every ground-floor pane
gets its own cell, ray-traced through a simple box model of the ground floor, seen from a
person on the sidewalk in front of that window, so the perspective is right. Rooms (1921
Sanborn tenants, north -> south):
  - 56 Flemington National Bank (x -10.62 ... -3.85, full 20 m depth): the banking room. Public
    space at the front with a tiled floor and a stand-up writing desk; a plain panelled oak
    counter across the room with a return along the public strip, a dark bronze grille on top
    with two teller openings in each run; desks, chairs and a filing cabinet behind it; a cross
    wall at y 14 with a plain dark steel vault door and a doorway to a back room (long table,
    chairs). Oak wainscot, buff plaster, pressed-tin ceiling, unlit globe pendants. Seen through
    the big bank window, the entrance door (glazed leaves + fanlight) and the 11 tall windows on
    the Bloomfield Ave side.
  - 58 Men's furnishings, 62 Drugs, 64 Boots & shoes, 66 Confectionery: narrow shops behind
    the four shop fronts - a low window display (plain boxes / jars), wall shelving with stock
    in muted colours, a counter or glass cases, chairs in the shoe store, small tables in the
    confectionery, pressed-tin ceiling, a dark doorway at the back. No lettering anywhere.
Daylight comes only through the windows, so it falls off quickly into the rooms. Slightly out
of focus (more with distance), dark, with a soft reveal shadow at the head and sides.

Writes
    assets/textures/shared/bank_hall.jpg    1024 x 1024, sRGB, JPEG quality 90
    assets/textures/shared/bank_hall.json   cell layout (same format as window_backs.json)

Local frame = the Bank Building model's (tools/blender/bank_building.py): x along the front
(+x = south, -x = north / Bloomfield Ave), y into the building (front stone face y = 0), z up
from the sidewalk; ground floor at z 0.90. Every cell's plane (origin, direction, length,
z0, z1) is the window back's bounding box in bank_building.py - keep the numbers in step.
"""

import json
import math
import os
import random
import zlib

import numpy as np

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
OUT = os.path.join(PROJECT, "assets", "textures", "shared", "bank_hall")
SIZE = 1024
SS = 3                         # supersampling per axis
EXPOSURE = 1.05
EYE_Z = 1.65                   # a person on the Main St sidewalk (z 0)
EYE_Y = -3.2

# bank numbers (keep in step with bank_building.py)
HW, BN, BS, XC = 11.07, 20.32, 11.05, 0.39
GF = 0.90
CEIL = 4.45
SIDE_WIN = [1.66 + 1.72 * k for k in range(11)]
SHOP_D, REC_D = 0.20, 0.90
SHOPS = [(-3.024, -0.40, -1.712), (0.40, 3.024, 1.712), (3.824, 6.448, 5.136), (7.248, 10.27, 9.37)]
GAP = 0.04                     # window back behind the glass

# ---------------------------------------------------------------------------
# Cells: name -> dict(origin (x, y), dir (dx, dy) left -> right as seen from outside,
#                     length, z0, z1, eye, px per metre)
# ---------------------------------------------------------------------------
CELLS = {}


def cell(name, origin, d, length, z0, z1, eye, pxm):
    CELLS[name] = dict(origin=origin, dir=d, length=length, z0=z0, z1=z1, eye=eye,
                       size=(max(8, round(length * pxm)), max(8, round((z1 - z0) * pxm))))


_c = (-10.27 - 7.248) / 2
cell("bank_window", (_c - 0.92, 0.20 + GAP), (1, 0), 1.84, 1.28, 3.62, (_c, EYE_Y, EYE_Z), 132)
cell("bank_door", (-5.136 - 0.75, 0.45), (1, 0), 1.50, GF, 3.80, (-5.136, EYE_Y, EYE_Z), 120)
for k, y in enumerate(SIDE_WIN):            # Bloomfield Ave side: plane x = -HW + 0.15 + GAP
    cell("north_%d" % k, (-HW + 0.15 + GAP, y + 0.405), (0, -1), 0.81, 1.07, 3.53,
         (-HW - 3.0, y, 1.50), 105)
for i, (x0, x1, dc) in enumerate(SHOPS):
    for side, (a, b) in (("l", (x0 + 0.08, dc - 0.5)), ("r", (dc + 0.5, x1 - 0.08))):
        if b - a > 0.2:
            cx = (a + b) / 2
            cell("s%d_%s" % (i, side), (a, SHOP_D + GAP), (1, 0), b - a, 1.32, 3.20, (cx, EYE_Y, EYE_Z), 145)
            cell("s%d_%st" % (i, side), (a, SHOP_D + GAP), (1, 0), b - a, 3.26, 3.56, (cx, EYE_Y, EYE_Z), 145)
    cell("s%d_door" % i, (dc - 0.36, REC_D + 0.015), (1, 0), 0.72, GF + 1.15, 3.05, (dc, EYE_Y, EYE_Z), 145)
    cell("s%d_dt" % i, (dc - 0.45, REC_D + 0.03), (1, 0), 0.90, 3.26, 3.54, (dc, EYE_Y, EYE_Z), 145)


def pack():
    """Shelf packing, tallest first; returns name -> [x, y, w, h] (row 0 at the top)."""
    order = sorted(CELLS, key=lambda n: (-CELLS[n]["size"][1], n))
    rects, x, y, row_h = {}, 0, 0, 0
    for n in order:
        w, h = CELLS[n]["size"]
        if x + w > SIZE:
            x, y, row_h = 0, y + row_h + 2, 0
        rects[n] = [x, y, w, h]
        x += w + 2
        row_h = max(row_h, h)
    assert y + row_h <= SIZE, "cells do not fit: %d px" % (y + row_h)
    return rects


def lin(rgb):
    c = np.array(rgb, dtype=np.float64) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# ---------------------------------------------------------------------------
# Ground-floor model: interior box + axis-aligned boxes, each with a room id
# rooms: 0 bank, 1 men's furnishings (58), 2 drugs (62), 3 boots & shoes (64), 4 confectionery (66)
# ---------------------------------------------------------------------------
ROOM_LO, ROOM_HI = np.array([-HW + 0.10, 0.18, GF]), np.array([HW - 0.45, BN - 0.42, CEIL])
PARTS = [-3.85, XC, 3.42, 6.85]
REAR = [BN - 0.42, BN - 0.42, BS - 0.40, BS - 0.40, BS - 0.40]
ROOM_X = [(-HW + 0.45, -3.93), (-3.77, XC - 0.15), (XC + 0.15, 3.34), (3.50, 6.77), (6.93, HW - 0.45)]
(K_PART, K_COUNTER, K_GRILLE_X, K_GRILLE_Y, K_DESK, K_CHAIR, K_CAB, K_VAULT, K_DOORWAY, K_TABLE,
 K_LAMP, K_SHELF, K_GOODS, K_CASE, K_PLATFORM, K_PICTURE, K_WRITING) = range(17)
boxes = []
rng = random.Random(19201110)


def room_of(x):
    return np.searchsorted(np.array(PARTS), x)


def add(lo, hi, kind, room=-1, colour=(0.1, 0.08, 0.06)):
    boxes.append((np.array(lo, float), np.array(hi, float), kind, room, np.array(colour, float)))


# structure: partitions (full height, no openings between the tenants), the south part's rear
for x, t in zip(PARTS, (0.08, 0.15, 0.08, 0.08)):
    add((x - t, 0.0, GF), (x + t, BN, CEIL), K_PART)
add((XC + 0.15, BS - 0.40, GF), (HW, BN, CEIL), K_PART)
# piers between the front openings (the inside of the front wall)
for x in (-6.848, -3.424, 0.0, 3.424, 6.848):
    add((x - 0.40, 0.0, GF), (x + 0.40, 0.45, CEIL), K_PART)


def chair(x, y, face, room, k=K_CHAIR):
    dx, dy = face
    w, sh = 0.44, 0.46
    add((x - w / 2, y - w / 2, GF + 0.40), (x + w / 2, y + w / 2, GF + sh), k, room)
    for lx in (-1, 1):
        for ly in (-1, 1):
            add((x + lx * 0.19 - 0.02, y + ly * 0.19 - 0.02, GF), (x + lx * 0.19 + 0.02, y + ly * 0.19 + 0.02, GF + 0.4), k, room)
    bx, by = x - dx * (w / 2 - 0.025), y - dy * (w / 2 - 0.025)
    hx, hy = (0.025 if dx else w / 2), (0.025 if dy else w / 2)
    add((bx - hx, by - hy, GF + sh - 0.02), (bx + hx, by + hy, GF + 0.95), k, room)


def table(x0, x1, y0, y1, h, room, k=K_TABLE):
    add((x0, y0, GF + h - 0.05), (x1, y1, GF + h), k, room)
    for lx, ly in ((x0 + 0.05, y0 + 0.05), (x1 - 0.05, y0 + 0.05), (x0 + 0.05, y1 - 0.05), (x1 - 0.05, y1 - 0.05)):
        add((lx - 0.025, ly - 0.025, GF), (lx + 0.025, ly + 0.025, GF + h - 0.05), k, room)


def lamp(x, y, room):
    add((x - 0.16, y - 0.16, CEIL - 1.05), (x + 0.16, y + 0.16, CEIL - 0.75), K_LAMP, room)
    add((x - 0.012, y - 0.012, CEIL - 0.75), (x + 0.012, y + 0.012, CEIL), K_LAMP, room)


# --- 56: the banking room ------------------------------------------------------------------
B = 0
add((-10.62, 5.20, GF), (-5.90, 5.85, GF + 1.08), K_COUNTER, B)            # counter across
add((-10.62, 5.15, GF + 1.08), (-5.85, 5.90, GF + 1.13), K_COUNTER, B)
add((-6.55, 5.85, GF), (-5.90, 11.50, GF + 1.08), K_COUNTER, B)            # return along the public strip
add((-6.60, 5.85, GF + 1.08), (-5.85, 11.55, GF + 1.13), K_COUNTER, B)
add((-10.62, 5.52, GF + 1.13), (-5.90, 5.54, GF + 2.30), K_GRILLE_X, B)    # bronze grille
add((-6.235, 5.54, GF + 1.13), (-6.215, 11.50, GF + 2.30), K_GRILLE_Y, B)
GRILLE_OPEN_X = ((-9.45, -8.95), (-7.65, -7.15))                           # teller openings
GRILLE_OPEN_Y = ((7.25, 7.75), (9.75, 10.25))
add((-10.62, 5.50, GF + 2.30), (-5.90, 5.56, GF + 2.36), K_GRILLE_X, B)   # top rail
add((-6.255, 5.56, GF + 2.30), (-6.195, 11.50, GF + 2.36), K_GRILLE_Y, B)
for x, y in ((-9.5, 8.3), (-9.5, 11.4), (-7.7, 9.6)):                      # desks behind the counter
    table(x - 0.70, x + 0.70, y - 0.40, y + 0.40, 0.76, B, K_DESK)
    add((x + 0.25, y - 0.35, GF), (x + 0.65, y + 0.35, GF + 0.70), K_DESK, B)   # pedestal
    chair(x, y + 0.75, (0, -1), B)
add((-10.62, 12.6, GF), (-10.10, 13.6, GF + 1.40), K_CAB, B)               # filing cabinet
add((-7.0, 12.9, GF), (-6.7, 13.85, GF + 1.90), K_CAB, B)                  # tall letter cabinet
add((-10.62, 13.85, GF), (-3.85, 14.15, CEIL), K_PART, B)                 # cross wall ...
add((-5.55, 13.80, GF), (-4.55, 14.20, GF + 2.30), K_DOORWAY, B)           # ... with a doorway
add((-9.30, 13.80, GF), (-7.90, 13.85, GF + 2.10), K_VAULT, B)             # vault door
add((-9.42, 13.82, GF), (-7.78, 13.85, GF + 2.22), K_PART, B)              # its stone surround
table(-9.6, -7.2, 15.6, 18.4, 0.76, B)                                     # back room
for y in (16.2, 17.2):
    chair(-10.0, y + 0.3, (1, 0), B)
    chair(-6.8, y + 0.3, (-1, 0), B)
add((-9.0, BN - 0.46, GF + 1.7), (-7.8, BN - 0.42, GF + 2.5), K_PICTURE, B)
add((-9.3, 2.30, GF), (-7.9, 2.95, GF + 1.10), K_WRITING, B)               # stand-up writing desk
add((-4.40, 1.6, GF), (-3.95, 4.2, GF + 0.45), K_CHAIR, B)                 # bench by the partition
add((-4.10, 1.6, GF + 0.45), (-3.95, 4.2, GF + 0.95), K_CHAIR, B)
for x, y in ((-8.2, 3.0), (-8.2, 9.0), (-5.0, 8.5), (-8.2, 17.0)):
    lamp(x, y, B)

# --- the four shops ----------------------------------------------------------------------
PALETTE = {
    1: [(196, 192, 178), (150, 138, 116), (66, 70, 82), (112, 106, 98), (176, 166, 146), (90, 60, 48)],  # men's
    2: [(124, 72, 32), (58, 88, 68), (196, 190, 176), (92, 60, 42), (150, 120, 84), (70, 96, 104)],     # drugs
    3: [(146, 114, 82), (92, 82, 72), (58, 48, 40), (172, 150, 118), (120, 92, 64)],                     # shoes
    4: [(196, 162, 146), (190, 178, 138), (116, 82, 56), (160, 118, 108), (206, 196, 176), (128, 140, 110)],  # sweets
}
WALL = {0: (150, 136, 110), 1: (110, 112, 96), 2: (138, 126, 102), 3: (112, 100, 80), 4: (150, 140, 120)}


def shop(i):
    r = i + 1
    xl, xr = ROOM_X[r]
    yb = REAR[r]
    x0, x1, dc = SHOPS[i]
    top = CEIL - 0.15 if r == 3 else GF + 2.70
    add((xl, 2.2, GF), (xl + 0.42, yb - 0.3, top), K_SHELF, r)              # wall shelving
    add((xr - 0.42, 2.2, GF), (xr, yb - 0.3, top), K_SHELF, r)
    add((xl, yb - 0.42, GF), (dc - 0.6, yb, top), K_SHELF, r)               # back wall shelving
    add((dc - 0.5, yb - 0.04, GF), (dc + 0.5, yb + 0.1, GF + 2.25), K_DOORWAY, r)
    add((dc + 0.6, yb - 0.42, GF), (xr, yb, top), K_SHELF, r)
    # window displays: low platform behind each display window, a few boxes / jars on it
    for a, b in ((x0 + 0.08, dc - 0.5), (dc + 0.5, x1 - 0.08)):
        if b - a > 0.2:
            add((a, 0.25, GF), (b, 1.00, GF + 0.32), K_PLATFORM, r)
            n = max(1, int((b - a) / 0.28))
            for k in range(n):
                cx = a + (k + 0.5) * (b - a) / n + rng.uniform(-0.05, 0.05)
                w, d, h = rng.uniform(0.12, 0.22), rng.uniform(0.12, 0.25), rng.uniform(0.08, 0.38 if r != 2 else 0.24)
                cy = rng.uniform(0.40, 0.85)
                add((cx - w / 2, cy - d / 2, GF + 0.32), (cx + w / 2, cy + d / 2, GF + 0.32 + h), K_GOODS, r)
    if r == 1:      # men's furnishings: counter on the north side, two tables of folded goods
        add((xl + 0.95, 3.0, GF), (xl + 1.50, yb - 3.0, GF + 0.95), K_COUNTER, r)
        for y in (6.0, 11.0):
            table(xr - 1.70, xr - 0.90, y, y + 1.4, 0.80, r)
            for k in range(4):
                add((xr - 1.65 + 0.18 * k, y + 0.2, GF + 0.80), (xr - 1.50 + 0.18 * k, y + 1.2, GF + 0.80 + rng.uniform(0.05, 0.18)), K_GOODS, r)
    elif r == 2:    # drugs: counters both sides, a show case in the middle, prescription wall
        add((xl + 0.95, 2.8, GF), (xl + 1.45, 7.2, GF + 0.95), K_COUNTER, r)
        add((xr - 1.45, 2.8, GF), (xr - 0.95, 7.2, GF + 0.95), K_CASE, r)
        add((xl, 8.0, GF), (dc - 0.5, 8.12, GF + 2.6), K_PART, r)
        add((dc + 0.5, 8.0, GF), (xr, 8.12, GF + 2.6), K_PART, r)
        add((dc - 0.5, 8.0, GF + 2.25), (dc + 0.5, 8.12, GF + 2.6), K_PART, r)
    elif r == 3:    # boots & shoes: stock to the ceiling, fitting chairs down the middle
        for k in range(5):
            chair(dc - 0.35, 3.4 + 0.9 * k, (1, 0), r)
        add((dc + 0.35, 4.0, GF), (dc + 0.55, 4.5, GF + 0.30), K_CHAIR, r)       # fitting stool
        add((dc + 0.35, 6.2, GF), (dc + 0.55, 6.7, GF + 0.30), K_CHAIR, r)
    else:           # confectionery: glass cases along the north side, small tables at the back
        add((xl + 0.95, 2.6, GF), (xl + 1.50, 6.8, GF + 1.00), K_CASE, r)
        for x, y in ((dc - 0.2, 7.6), (xr - 1.2, 8.8)):
            table(x - 0.35, x + 0.35, y - 0.35, y + 0.35, 0.74, r)
            chair(x - 0.6, y, (1, 0), r)
            chair(x + 0.6, y, (-1, 0), r)
    for y in (3.5, yb - 3.5):
        lamp((xl + xr) / 2, y, r)


for _i in range(4):
    shop(_i)

B_LO = np.array([b[0] for b in boxes])
B_HI = np.array([b[1] for b in boxes])
B_KIND = np.array([b[2] for b in boxes])
B_ROOM = np.array([b[3] for b in boxes])


# ---------------------------------------------------------------------------
# Ray tracing
# ---------------------------------------------------------------------------
def grille_gap(P, k):
    """True where a ray passes between the bars of the counter grille (or a teller opening)."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    along = x if k == K_GRILLE_X else y
    opens = GRILLE_OPEN_X if k == K_GRILLE_X else GRILLE_OPEN_Y
    bar = np.abs((along / 0.11) % 1 - 0.5) > 0.40
    rail = (np.abs(z - (GF + 1.75)) < 0.025)
    gap = ~(bar | rail)
    for a, b in opens:
        gap |= (along > a) & (along < b) & (z < GF + 1.70)
    return gap


def trace(O, D, room):
    n = O.shape[0]
    with np.errstate(divide="ignore", invalid="ignore"):
        inv = 1.0 / np.where(np.abs(D) < 1e-12, 1e-12, D)
    tb = (np.where(D > 0, ROOM_HI, ROOM_LO) - O) * inv
    best_t = tb.min(axis=1)
    axis = tb.argmin(axis=1)
    kind = np.full(n, -1)                                     # -1 = room surface
    for i in np.nonzero((B_ROOM == -1) | (B_ROOM == room))[0]:
        t0 = (B_LO[i] - O) * inv
        t1 = (B_HI[i] - O) * inv
        tmin = np.minimum(t0, t1)
        tn = tmin.max(axis=1)
        tf = np.maximum(t0, t1).min(axis=1)
        hit = (tn <= tf) & (tn > 1e-5) & (tn < best_t)
        if B_KIND[i] in (K_GRILLE_X, K_GRILLE_Y) and hit.any():
            idx = np.nonzero(hit)[0]
            P = O[idx] + D[idx] * tn[idx, None]
            hit[idx[grille_gap(P, B_KIND[i])]] = False
        if hit.any():
            best_t[hit] = tn[hit]
            axis[hit] = tmin[hit].argmax(axis=1)
            kind[hit] = B_KIND[i]
    N = np.zeros((n, 3))
    N[np.arange(n), axis] = -np.sign(D[np.arange(n), axis])
    P = O + D * best_t[:, None]
    return best_t, P, N, kind


def hashf(a, b, seed=0):
    v = np.sin(a * 12.9898 + b * 78.233 + seed * 37.719) * 43758.5453
    return v - np.floor(v)


WOOD = lin((84, 60, 38))
OAK = lin((96, 70, 44))
DARK_WOOD = lin((44, 31, 21))


def palette_pick(room, h):
    out = np.zeros((h.shape[0], 3))
    for r, pal in PALETTE.items():
        m = room == r
        if m.any():
            cols = np.array([lin(c) for c in pal])
            out[m] = cols[(h[m] * len(pal)).astype(int) % len(pal)]
    return out


def albedo(P, N, kind, room):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    n = P.shape[0]
    A = np.zeros_like(P)
    rm = np.full(n, room)
    surf = kind == -1
    along = np.where(np.abs(N[:, 0]) > 0.5, y, x)
    # floor: boards; the bank's public area is small white-and-grey tile
    floor = surf & (N[:, 2] > 0.5)
    A[floor] = lin((78, 58, 40)) * (0.8 + 0.25 * hashf(np.floor(x / 0.1), 0.0, 1))[floor, None]
    if room == 0:
        pub = floor & ((y < 5.2) | ((x > -5.9) & (y < 13.8)))
        tile = 0.85 + 0.25 * (((np.floor(x / 0.12) + np.floor(y / 0.12)) % 2) == 0)
        A[pub] = (lin((150, 144, 128)) * tile[:, None])[pub]
        A[pub & ((np.abs(y - 0.9) < 0.08) | (np.abs(y - 4.6) < 0.08))] = lin((70, 52, 46))   # border
    # pressed-tin ceiling
    ceil = surf & (N[:, 2] < -0.5)
    grid = (np.abs((x / 0.6) % 1 - 0.5) > 0.46) | (np.abs((y / 0.6) % 1 - 0.5) > 0.46)
    A[ceil] = (lin((156, 150, 134)) * np.where(grid, 0.82, 1.0)[:, None])[ceil]
    # walls (incl. partitions and the inside of the front piers): plaster/paint over a wainscot
    walls = (surf | (kind == K_PART)) & (np.abs(N[:, 2]) < 0.5)
    A[walls] = lin(WALL[room])
    A[walls & (z > CEIL - 0.35)] = lin((160, 152, 132))
    A[walls & (np.abs(z - (CEIL - 0.36)) < 0.03)] = DARK_WOOD
    wain_top = GF + (1.25 if room == 0 else 0.95)
    wain = walls & (z < wain_top)
    pan = (np.abs((along / 0.65) % 1 - 0.5) > 0.44) | (z > wain_top - 0.08) | (z < GF + 0.15)
    A[wain] = (OAK if room == 0 else WOOD) * 0.85
    A[wain & pan] = DARK_WOOD
    A[(kind == K_PART) & (np.abs(N[:, 2]) > 0.5)] = DARK_WOOD
    A[kind == K_DOORWAY] = lin((14, 11, 9))
    # counters: panelled front, worn top
    m = kind == K_COUNTER
    A[m] = OAK * 0.75
    A[m & (N[:, 2] > 0.5)] = OAK * 1.1
    pan = m & (np.abs(N[:, 2]) < 0.5) & ((np.abs((along / 0.55) % 1 - 0.5) > 0.42) | (z > GF + 0.98) | (z < GF + 0.16))
    A[pan] = DARK_WOOD * 0.8
    A[(kind == K_GRILLE_X) | (kind == K_GRILLE_Y)] = lin((58, 46, 30))       # dark bronze
    A[kind == K_DESK] = OAK * 0.8
    A[(kind == K_DESK) & (N[:, 2] > 0.5)] = lin((60, 66, 52))                # green baize / blotter
    A[kind == K_WRITING] = OAK * 0.8
    A[kind == K_CHAIR] = lin((60, 40, 27))
    A[kind == K_TABLE] = DARK_WOOD * 1.25
    m = kind == K_CAB
    A[m] = OAK * 0.7
    A[m & (np.abs(((z - GF) / 0.3) % 1 - 0.5) > 0.46)] = DARK_WOOD * 0.6     # drawer lines
    m = kind == K_VAULT                                                     # plain dark steel door
    A[m] = lin((52, 56, 56))
    cx, cz = -8.60, GF + 1.10
    rr = np.hypot(x - cx, z - cz)
    A[m & (np.abs(rr - 0.18) < 0.025)] = lin((120, 112, 92))               # dull brass wheel
    A[m & (np.abs(x - cx) > 0.62)] = lin((40, 42, 42))                      # hinge side / frame
    A[kind == K_LAMP] = lin((150, 146, 128))
    m = kind == K_PICTURE
    A[m] = lin((100, 82, 52))
    inner = m & (x > -8.92) & (x < -7.88) & (z > GF + 1.78) & (z < GF + 2.42)
    A[inner] = lin((70, 72, 58)) * (0.85 + 0.3 * hashf(np.floor(x / 0.08), np.floor(z / 0.08), 5))[inner, None]
    # shelving: rows of stock in the shop's colours, wood shelf boards between
    m = kind == K_SHELF
    if m.any():
        row_h = 0.24 if room == 3 else 0.36
        col_w = 0.30 if room == 3 else (0.16 if room in (2, 4) else 0.42)
        yb = REAR[room] if room > 0 else BN
        side = (np.abs(N[:, 0]) > 0.5) & (y < yb - 0.45)                  # long faces only, not
        back = (np.abs(N[:, 1]) > 0.5) & (y > yb - 0.5)                   # the shelving's ends
        face = m & (side | back)
        r_i = np.floor((z - GF) / row_h)
        c_i = np.floor(along / col_w)
        h = hashf(c_i, r_i, room)
        stock = palette_pick(rm, h) * (0.75 + 0.35 * hashf(c_i, r_i, 9))[:, None]
        board = (((z - GF) / row_h) % 1 < 0.12) | (np.abs((along / col_w) % 1 - 0.5) > 0.47)
        empty = hashf(c_i, r_i, 3) < 0.07
        A[m] = WOOD * 0.7
        A[face] = stock[face]
        A[face & (board | empty)] = DARK_WOOD * 0.7
        A[face & (z < GF + 0.75) & (room != 3)] = (WOOD * 0.8)                # drawers below
        A[face & (z < GF + 0.75) & (room != 3) & (np.abs(((z - GF) / 0.25) % 1 - 0.5) > 0.44)] = DARK_WOOD * 0.6
    m = kind == K_GOODS
    if m.any():
        A[m] = palette_pick(rm, hashf(np.floor(x / 0.2), np.floor(y / 0.2), 4))[m] * (0.6 + 0.15 * (N[m, 2:3] > 0.5))
    m = kind == K_PLATFORM
    A[m] = lin((70, 56, 44))
    A[m & (N[:, 2] > 0.5)] = lin({1: (92, 84, 74), 2: (74, 70, 60), 3: (88, 74, 60), 4: (118, 108, 92)}.get(room, (80, 70, 60)))
    m = kind == K_CASE                                                      # glass show case
    A[m] = WOOD * 0.8
    up = m & (z > GF + 0.40) & (np.abs(N[:, 2]) < 0.5)
    dots = palette_pick(rm, hashf(np.floor(along / 0.12), np.floor(z / 0.12), 6))
    A[up] = (dots * 0.55 + lin((70, 74, 72)) * 0.45)[up]
    A[m & (N[:, 2] > 0.5)] = lin((96, 102, 100))
    return A


def shade(P, N, kind, room, north):
    """Daylight only through the windows: the front (and for the bank the long Bloomfield
    side), falling off into the room; faces turned to the light get more."""
    x, y = P[:, 0], P[:, 1]
    d = np.maximum(y - 0.45, 0)
    front = 1.0 * np.exp(-d / 3.0) + 0.16 * np.exp(-d / 10.0)
    facing = 0.55 + 0.45 * np.maximum(0, -N[:, 1]) + 0.25 * np.maximum(0, N[:, 2]) - 0.30 * np.maximum(0, -N[:, 2])
    L = front * facing
    if room == 0:
        dn = np.maximum(x - (-HW + 0.45), 0)
        side = 0.65 * np.exp(-dn / 2.6) + 0.12
        L = L * 0.7 + side * (0.55 + 0.45 * np.maximum(0, -N[:, 0]) + 0.2 * np.maximum(0, N[:, 2]))
    return L + 0.02


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def blur(img, sigma):
    if sigma <= 0:
        return img
    r = int(math.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    out = img
    for ax in (0, 1):
        pad = [(0, 0)] * 3
        pad[ax] = (r, r)
        p = np.pad(out, pad, mode="edge")
        acc = np.zeros_like(out)
        for i, w in enumerate(k):
            sl = [slice(None)] * 3
            sl[ax] = slice(i, i + out.shape[ax])
            acc += w * p[tuple(sl)]
        out = acc
    return out


def reveal(h, w, short=False):
    """Soft shadow of the window reveal (darker at the head and sides)."""
    yy, xx = np.mgrid[0:h, 0:w]
    ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
    if short:                                   # transoms: just a darker head
        return 0.65 + 0.35 * ss(yy / (h * 0.7))
    ft = 0.6 + 0.4 * ss(yy / (h * 0.25))
    fs = 0.75 + 0.25 * ss(np.minimum(xx, w - 1 - xx) / (w * 0.18))
    return ft * fs


def render_cell(name, pw, ph):
    c = CELLS[name]
    Wd, H = pw * SS, ph * SS
    u = (np.arange(Wd) + 0.5) / Wd
    v = 1 - (np.arange(H) + 0.5) / H                         # row 0 = top = z1
    uu, vv = np.meshgrid(u, v)
    ox, oy = c["origin"]
    dx, dy = c["dir"]
    P0 = np.stack([ox + dx * c["length"] * uu, oy + dy * c["length"] * uu,
                   c["z0"] + (c["z1"] - c["z0"]) * vv], axis=-1).reshape(-1, 3)
    E = np.array(c["eye"], float)
    D = P0 - E
    D /= np.linalg.norm(D, axis=1, keepdims=True)
    room = int(room_of(np.array([ox + dx * c["length"] / 2]))[0])
    t, P, N, kind = trace(P0, D, room)
    # the Bloomfield Ave side is in shade all afternoon (darker lightmap): lift those cells a little
    exposure = EXPOSURE * (1.3 if name.startswith("north") else 1.0)
    C = albedo(P, N, kind, room) * shade(P, N, kind, room, name.startswith("north"))[:, None] * exposure
    img = to_srgb(C).reshape(H, Wd, 3)
    dist = t.reshape(H, Wd)
    img = img.reshape(ph, SS, pw, SS, 3).mean(axis=(1, 3))
    dist = dist.reshape(ph, SS, pw, SS).mean(axis=(1, 3))
    near, far = blur(img, 0.5), blur(img, 1.6)
    m = np.clip((dist - 0.8) / 5.0, 0, 1)[..., None]
    img = blur(near * (1 - m) + far * m, 0.4)
    short = name.endswith(("_lt", "_rt", "_dt"))
    img = img * reveal(ph, pw, short)[..., None]
    nrng = np.random.default_rng(zlib.crc32(name.encode()))
    img = img + nrng.normal(0, 0.006, img.shape)
    return np.clip(img, 0, 1)


def main():
    rects = pack()
    atlas = np.full((SIZE, SIZE, 3), 0.06)
    cells = {}
    for name in CELLS:
        x, y, w, h = rects[name]
        atlas[y:y + h, x:x + w] = render_cell(name, w, h)
        cells[name] = {"px": [x, y, w, h], "uv": [x / SIZE, 1 - (y + h) / SIZE, (x + w) / SIZE, 1 - y / SIZE]}
    import bpy
    img = bpy.data.images.get("BH_BankHall") or bpy.data.images.new("BH_BankHall", SIZE, SIZE)
    img.scale(SIZE, SIZE)
    img.colorspace_settings.name = "Non-Color"                # values are already sRGB-encoded
    rgba = np.ones((SIZE, SIZE, 4), dtype=np.float32)
    rgba[..., :3] = atlas[::-1]                               # Blender rows start at the bottom
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = OUT + ".jpg"
    img.file_format = "JPEG"
    scene = bpy.context.scene
    q = scene.render.image_settings.quality
    scene.render.image_settings.quality = 90
    img.save()
    scene.render.image_settings.quality = q
    bpy.data.images.remove(img)
    with open(OUT + ".json", "w") as f:
        json.dump({"size": SIZE, "note": "px = [x, y, w, h], row 0 at the top; uv = [u0, v0, u1, v1], "
                   "Blender/glTF-before-flip convention (v = 0 at the bottom). Cells match the Bank "
                   "Building's ground-floor glass in tools/blender/bank_building.py: bank_window, "
                   "bank_door, north_<k> (Bloomfield Ave side), s<shop>_l / _r (display windows), "
                   "_lt / _rt (their transoms), _door, _dt (door transom); each cell spans the "
                   "window back's bounding box.",
                   "cells": cells}, f, indent=1)
    print("wrote", OUT + ".jpg", "with", len(cells), "cells,", len(boxes), "boxes")


main()
