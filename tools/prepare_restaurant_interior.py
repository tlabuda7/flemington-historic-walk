"""
prepare_restaurant_interior.py - draws `assets/textures/shared/restaurant_interior.jpg`: what you
see through the ground-floor glass of Lovell's Restaurant (68 Main St), c. 1920. Own work (no
download, no lettering, no signs). Run INSIDE Blender (numpy; the image is saved with bpy),
before tools/blender/lovells_restaurant.py:

    exec(open(r"<project>/tools/prepare_restaurant_interior.py").read())

Same method as tools/prepare_bank_hall.py / prepare_hotel_lobby.py / prepare_shop_interior.py:
every ground-floor pane gets its own cell, ray-traced through a simple box model of the dining
room, seen from a person in front of that window, so the perspective is right.
The room (one plain dining room, 1921 Sanborn "Restr't"): board floor, oak wainscot, dull
buff-green walls, pressed-tin ceiling, unlit globe pendants; a plain panelled counter along the
north wall with a back bar of shelves (plain jars, glasses, crockery in muted colours); small
tables with white cloths and bentwood-style chairs down the south side and the middle; a low
display platform behind the display window with a few plain jars and covered cake stands; a
cross wall at the back with a dark doorway to the kitchen; one plain framed picture. No
lettering anywhere. Daylight comes only through the front and the three south windows, so it
falls off quickly into the room. Slightly out of focus (more with distance), dark, with a soft
reveal shadow at the head and sides.

Writes
    assets/textures/shared/restaurant_interior.jpg    1024 x 1024, sRGB, JPEG quality 90
    assets/textures/shared/restaurant_interior.json   cell layout (same format as window_backs.json)

Local frame = the Lovell's model's (tools/blender/lovells_restaurant.py): x along the front
(+x = south, hotel side), y into the building (front wall face y = 0), z up from the sidewalk;
shop floor at z 0.45. Every cell's plane (origin, direction, length, z0, z1) is the window
back's bounding box in lovells_restaurant.py - keep the numbers in step.
"""

import json
import math
import os
import random
import zlib

import numpy as np

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
OUT = os.path.join(PROJECT, "assets", "textures", "shared", "restaurant_interior")
SIZE = 1024
SS = 3                         # supersampling per axis
EXPOSURE = 1.10
EYE_Z = 1.65                   # a person on the sidewalk (z 0)
EYE_Y = -3.2

# Lovell's numbers (keep in step with lovells_restaurant.py)
HW = 3.00
FL = 0.45
CEIL = 4.10
GAP = 0.04
LD0, LD1 = -2.65, -1.70
CD0, CD1, CREC = -1.05, 0.65, 0.45
DW0, DW1 = 1.10, 2.65
SOUTH_DN = (2.5, 6.5, 10.5)
W_DN = (0.85, 1.25, 2.95)
BACK_Y = 13.0                  # cross wall to the kitchen

# ---------------------------------------------------------------------------
# Cells: name -> dict(origin (x, y), dir (dx, dy) left -> right as seen from outside,
#                     length, z0, z1, eye, px per metre)
# ---------------------------------------------------------------------------
CELLS = {}


def cell(name, origin, d, length, z0, z1, eye, pxm):
    CELLS[name] = dict(origin=origin, dir=d, length=length, z0=z0, z1=z1, eye=eye,
                       size=(max(8, round(length * pxm)), max(8, round((z1 - z0) * pxm))))


PXM = 230
# Ladies' Entrance: leaf glass (leaf face y 0.12, glass 0.145, back 0.185) and transom
cell("ladies_door", (LD0 + 0.13, 0.12 + 0.025 + GAP), (1, 0), (LD1 - 0.13) - (LD0 + 0.13), 1.45, 2.63,
     ((LD0 + LD1) / 2, EYE_Y, EYE_Z), PXM)
cell("ladies_t", (LD0, 0.13 + GAP), (1, 0), LD1 - LD0, 2.85, 3.45, ((LD0 + LD1) / 2, EYE_Y, EYE_Z), PXM)
# centre double door: two leaves (leaf face y 0.34, glass 0.365, back 0.405) and transom (back 0.46)
_xm = (CD0 + CD1) / 2
for nm, (x0, x1) in (("door_l", (CD0 + 0.10, _xm - 0.005)), ("door_r", (_xm + 0.005, CD1 - 0.10))):
    cell(nm, (x0 + 0.10, CREC - 0.11 + 0.025 + GAP), (1, 0), (x1 - 0.10) - (x0 + 0.10), 1.15, 2.73,
         (_xm, EYE_Y, EYE_Z), PXM)
cell("door_t", (CD0 + 0.10, CREC - 0.03 + GAP), (1, 0), (CD1 - 0.10) - (CD0 + 0.10), 2.95, 3.45, (_xm, EYE_Y, EYE_Z), PXM)
# display window (glass y 0.10, back 0.14): main pane and the 2-light top row
cell("display", (DW0, 0.10 + GAP), (1, 0), DW1 - DW0, 1.05, 2.95, ((DW0 + DW1) / 2, EYE_Y, EYE_Z), PXM)
cell("display_t", (DW0, 0.10 + GAP), (1, 0), DW1 - DW0, 2.95, 3.45, ((DW0 + DW1) / 2, EYE_Y, EYE_Z), PXM)
# south wall ground-floor windows (glass at x 2.89, back at x 2.85), seen from the gap to the hotel
for k, y in enumerate(SOUTH_DN):
    w, z0, z1 = W_DN
    cell("south_%d" % k, (HW - 0.15, y - w / 2), (0, 1), w, z0, z1, (HW + 3.0, y - 1.5, 1.60), 150)


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
# Room model: interior box + axis-aligned boxes
# ---------------------------------------------------------------------------
ROOM_LO, ROOM_HI = np.array([-HW + 0.15, 0.20, FL]), np.array([HW - 0.15, BACK_Y + 0.15, CEIL])
(K_PART, K_COUNTER, K_BACKBAR, K_TABLE, K_CLOTH, K_CHAIR, K_LAMP, K_DOORWAY, K_PLATFORM, K_GOODS,
 K_DOME, K_PICTURE, K_STOVE) = range(13)
boxes = []
rng = random.Random(19201068)


def add(lo, hi, kind, colour=None):
    boxes.append((np.array(lo, float), np.array(hi, float), kind))


# inside of the front wall between the openings, and the cross wall with the kitchen doorway
for x0, x1 in ((-HW, LD0), (LD1, CD0), (CD1, DW0), (DW1, HW)):
    add((x0, 0.0, FL), (x1, 0.30, CEIL), K_PART)
add((-HW, 0.0, 3.45), (HW, 0.30, CEIL), K_PART)
add((-HW, BACK_Y, FL), (HW, BACK_Y + 0.15, CEIL), K_PART)
add((0.75, BACK_Y - 0.03, FL), (1.65, BACK_Y + 0.2, FL + 2.15), K_DOORWAY)


def chair(x, y, face):
    dx, dy = face
    w, sh = 0.40, 0.46
    add((x - w / 2, y - w / 2, FL + 0.42), (x + w / 2, y + w / 2, FL + sh), K_CHAIR)
    for lx in (-1, 1):
        for ly in (-1, 1):
            add((x + lx * 0.17 - 0.015, y + ly * 0.17 - 0.015, FL), (x + lx * 0.17 + 0.015, y + ly * 0.17 + 0.015, FL + 0.42), K_CHAIR)
    bx, by = x - dx * (w / 2 - 0.02), y - dy * (w / 2 - 0.02)
    hx, hy = (0.02 if dx else w / 2 - 0.03), (0.02 if dy else w / 2 - 0.03)
    for zz in (0.62, 0.84):                                          # two back rails between posts
        add((bx - hx, by - hy, FL + zz), (bx + hx, by + hy, FL + zz + 0.06), K_CHAIR)
    for s in (-1, 1):                                                # back posts
        px, py = (bx, by + s * (w / 2 - 0.03)) if dx else (bx + s * (w / 2 - 0.03), by)
        add((px - 0.02, py - 0.02, FL + sh), (px + 0.02, py + 0.02, FL + 0.92), K_CHAIR)


def clothed_table(x, y, half=0.38, h=0.76, seats="y"):
    """Small square table with a white cloth hanging 0.22 down all round, two or four chairs."""
    add((x - half, y - half, FL + h - 0.22), (x + half, y + half, FL + h), K_CLOTH)
    add((x - 0.04, y - 0.04, FL), (x + 0.04, y + 0.04, FL + h - 0.22), K_TABLE)      # pedestal
    add((x - 0.25, y - 0.25, FL), (x + 0.25, y + 0.25, FL + 0.04), K_TABLE)          # foot
    off = half + 0.22
    if "y" in seats:
        chair(x, y - off, (0, 1))
        chair(x, y + off, (0, -1))
    if "x" in seats:
        chair(x - off, y, (1, 0))
        chair(x + off, y, (-1, 0))


def lamp(x, y):
    add((x - 0.15, y - 0.15, CEIL - 1.00), (x + 0.15, y + 0.15, CEIL - 0.72), K_LAMP)
    add((x - 0.01, y - 0.01, CEIL - 0.72), (x + 0.01, y + 0.01, CEIL), K_LAMP)


# counter along the north wall, back bar behind it
add((-2.10, 4.6, FL), (-1.55, 10.8, FL + 1.02), K_COUNTER)
add((-2.14, 4.56, FL + 1.02), (-1.50, 10.84, FL + 1.07), K_COUNTER)
add((-HW + 0.15, 4.2, FL), (-2.45, 11.2, FL + 0.95), K_BACKBAR)                   # lower cupboards
add((-HW + 0.15, 4.2, FL + 0.95), (-2.62, 11.2, FL + 2.55), K_BACKBAR)            # shelves above
add((-HW + 0.15, 4.2, FL + 2.55), (-2.40, 11.2, FL + 2.70), K_BACKBAR)            # cornice
for y in (5.4, 7.0, 8.6, 10.2):                                                   # stools at the counter
    add((-1.38, y - 0.17, FL + 0.66), (-1.04, y + 0.17, FL + 0.72), K_CHAIR)
    add((-1.23, y - 0.03, FL), (-1.19, y + 0.03, FL + 0.66), K_CHAIR)
# a few covered dishes and jars on the counter
for y in (5.2, 6.6, 9.4):
    add((-1.95, y - 0.14, FL + 1.07), (-1.70, y + 0.14, FL + 1.35), K_DOME)
# tables with cloths: south row (4) and middle row (3)
for y in (2.4, 5.0, 7.6, 10.2):
    clothed_table(2.05, y, seats="y")
for y in (3.6, 6.3, 9.0, 11.7):
    clothed_table(0.15, y, 0.40, seats="x" if y < 11 else "y")
# display platform behind the display window, plain jars and cake stands on it
add((DW0, 0.30, FL), (DW1, 1.00, FL + 0.30), K_PLATFORM)
for k in range(4):
    cx = DW0 + 0.22 + k * 0.37 + rng.uniform(-0.04, 0.04)
    cy = rng.uniform(0.50, 0.80)
    if k % 2:
        add((cx - 0.13, cy - 0.13, FL + 0.30), (cx + 0.13, cy + 0.13, FL + 0.34), K_GOODS)   # stand foot
        add((cx - 0.12, cy - 0.12, FL + 0.34), (cx + 0.12, cy + 0.12, FL + 0.58), K_DOME)
    else:
        h = rng.uniform(0.22, 0.34)
        add((cx - 0.08, cy - 0.08, FL + 0.30), (cx + 0.08, cy + 0.08, FL + 0.30 + h), K_GOODS)
add((-0.4, BACK_Y - 0.04, FL + 1.65), (0.3, BACK_Y, FL + 2.20), K_PICTURE)
add((-2.85, BACK_Y - 0.65, FL), (-2.25, BACK_Y - 0.05, FL + 1.85), K_STOVE)     # plain dark cupboard
for x, y in ((-0.9, 3.0), (-0.9, 8.0), (1.3, 5.5), (1.3, 10.5)):
    lamp(x, y)

B_LO = np.array([b[0] for b in boxes])
B_HI = np.array([b[1] for b in boxes])
B_KIND = np.array([b[2] for b in boxes])


# ---------------------------------------------------------------------------
# Ray tracing
# ---------------------------------------------------------------------------
def trace(O, D):
    n = O.shape[0]
    with np.errstate(divide="ignore", invalid="ignore"):
        inv = 1.0 / np.where(np.abs(D) < 1e-12, 1e-12, D)
    tb = (np.where(D > 0, ROOM_HI, ROOM_LO) - O) * inv
    best_t = tb.min(axis=1)
    axis = tb.argmin(axis=1)
    kind = np.full(n, -1)                                     # -1 = room surface
    for i in range(len(boxes)):
        t0 = (B_LO[i] - O) * inv
        t1 = (B_HI[i] - O) * inv
        tmin = np.minimum(t0, t1)
        tn = tmin.max(axis=1)
        tf = np.maximum(t0, t1).min(axis=1)
        hit = (tn <= tf) & (tn > 1e-5) & (tn < best_t)
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
OAK = lin((100, 74, 46))
DARK_WOOD = lin((44, 31, 21))
WALL = lin((140, 134, 108))                         # dull buff-green paint
CLOTH = lin((194, 190, 178))
STOCK = [lin(c) for c in ((182, 178, 164), (120, 112, 96), (86, 94, 80), (150, 128, 96), (96, 72, 52),
                          (170, 160, 140), (70, 80, 84))]


def albedo(P, N, kind):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    A = np.zeros_like(P)
    surf = kind == -1
    along = np.where(np.abs(N[:, 0]) > 0.5, y, x)
    floor = surf & (N[:, 2] > 0.5)
    A[floor] = lin((84, 64, 44)) * (0.8 + 0.25 * hashf(np.floor(x / 0.09), 0.0, 1))[floor, None]
    ceil = surf & (N[:, 2] < -0.5)
    grid = (np.abs((x / 0.6) % 1 - 0.5) > 0.46) | (np.abs((y / 0.6) % 1 - 0.5) > 0.46)
    A[ceil] = (lin((160, 154, 138)) * np.where(grid, 0.82, 1.0)[:, None])[ceil]
    walls = (surf | (kind == K_PART)) & (np.abs(N[:, 2]) < 0.5)
    A[walls] = WALL
    A[walls & (z > CEIL - 0.30)] = lin((164, 156, 136))
    A[walls & (np.abs(z - (CEIL - 0.31)) < 0.03)] = DARK_WOOD
    wain_top = FL + 1.05
    wain = walls & (z < wain_top)
    pan = (np.abs((along / 0.60) % 1 - 0.5) > 0.44) | (z > wain_top - 0.08) | (z < FL + 0.14)
    A[wain] = OAK * 0.85
    A[wain & pan] = DARK_WOOD
    A[(kind == K_PART) & (np.abs(N[:, 2]) > 0.5)] = DARK_WOOD
    A[kind == K_DOORWAY] = lin((14, 11, 9))
    m = kind == K_COUNTER                                     # panelled front, worn top
    A[m] = OAK * 0.75
    A[m & (N[:, 2] > 0.5)] = lin((150, 146, 136))             # pale marble top
    pan = m & (np.abs(N[:, 2]) < 0.5) & ((np.abs((along / 0.55) % 1 - 0.5) > 0.42) | (z > FL + 0.94) | (z < FL + 0.14))
    A[pan] = DARK_WOOD * 0.8
    m = kind == K_BACKBAR                                     # shelves of plain jars, glasses, crockery
    A[m] = OAK * 0.6
    face = m & (N[:, 0] > 0.5) & (z > FL + 0.95) & (z < FL + 2.55)
    fz = (z - FL - 0.95) / 0.40                               # shelf rows 0.40 apart
    r_i = np.floor(fz)
    fu = along / 0.10                                         # one jar / glass / plate stack per 0.10
    c_i = np.floor(fu)
    h = hashf(c_i, r_i, 2)
    stock = np.array(STOCK)[(h * len(STOCK)).astype(int) % len(STOCK)] * (0.7 + 0.35 * hashf(c_i, r_i, 9))[:, None]
    in_row = fz % 1
    tall = 0.12 + 0.30 + 0.45 * hashf(c_i, r_i, 5)           # item top inside its row
    item = (in_row > 0.12) & (in_row < tall) & (np.abs(fu % 1 - 0.5) < 0.30 + 0.12 * hashf(c_i, r_i, 6)) \
        & (hashf(c_i, r_i, 3) > 0.22)
    A[face] = DARK_WOOD[None, :] * 0.45                       # shadowed shelf back
    A[face & item] = stock[face & item]
    A[face & (in_row < 0.10)] = OAK * 0.7                     # shelf boards
    low = m & (N[:, 0] > 0.5) & (z < FL + 0.95)
    A[low & (np.abs((y / 0.7) % 1 - 0.5) > 0.44)] = DARK_WOOD * 0.6         # cupboard doors
    m = kind == K_CLOTH
    A[m] = (CLOTH * (0.92 + 0.08 * hashf(np.floor(x / 0.05), np.floor(z / 0.05), 7))[:, None])[m]
    A[m & (N[:, 2] < 0.5) & (np.abs(((z - FL) / 0.07) % 1 - 0.5) > 0.47)] = CLOTH * 0.85   # folds
    A[kind == K_TABLE] = DARK_WOOD * 1.2
    A[kind == K_CHAIR] = lin((58, 38, 25))
    A[kind == K_LAMP] = lin((156, 152, 134))
    A[kind == K_PLATFORM] = lin((70, 56, 44))
    A[(kind == K_PLATFORM) & (N[:, 2] > 0.5)] = lin((120, 112, 98))           # plain paper cover
    m = kind == K_GOODS
    A[m] = np.array(STOCK)[(hashf(np.floor(x / 0.2), np.floor(y / 0.2), 4) * len(STOCK)).astype(int) % len(STOCK)][m] * 0.7
    A[kind == K_DOME] = lin((128, 132, 128))                  # glass cover / dish: dull grey
    m = kind == K_PICTURE
    A[m] = lin((96, 78, 50))
    inner = m & (x > -0.33) & (x < 0.23) & (z > FL + 1.72) & (z < FL + 2.13)
    A[inner] = lin((76, 80, 64)) * (0.85 + 0.3 * hashf(np.floor(x / 0.07), np.floor(z / 0.07), 5))[inner, None]
    A[kind == K_STOVE] = DARK_WOOD * 0.9
    return A


def shade(P, N, kind):
    """Daylight only through the front openings and the three south windows."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    d = np.maximum(y - 0.30, 0)
    front = 1.0 * np.exp(-d / 3.0) + 0.14 * np.exp(-d / 9.0)
    facing = 0.55 + 0.45 * np.maximum(0, -N[:, 1]) + 0.25 * np.maximum(0, N[:, 2]) - 0.30 * np.maximum(0, -N[:, 2])
    L = front * facing
    ds = np.maximum((HW - 0.15) - x, 0)
    near_win = np.zeros_like(y)
    for yw in SOUTH_DN:
        near_win = np.maximum(near_win, np.exp(-((y - yw) / 1.6) ** 2))
    side = 0.40 * np.exp(-ds / 2.0) * (0.35 + 0.65 * near_win)
    L = L + side * (0.55 + 0.45 * np.maximum(0, -N[:, 0]) + 0.2 * np.maximum(0, N[:, 2]))
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
    t, P, N, kind = trace(P0, D)
    # the south wall is in the hotel's shade: lift those cells a little
    exposure = EXPOSURE * (1.25 if name.startswith("south") else 1.0)
    C = albedo(P, N, kind) * shade(P, N, kind)[:, None] * exposure
    img = to_srgb(C).reshape(H, Wd, 3)
    dist = t.reshape(H, Wd)
    img = img.reshape(ph, SS, pw, SS, 3).mean(axis=(1, 3))
    dist = dist.reshape(ph, SS, pw, SS).mean(axis=(1, 3))
    near, far = blur(img, 0.5), blur(img, 1.6)
    m = np.clip((dist - 0.8) / 5.0, 0, 1)[..., None]
    img = blur(near * (1 - m) + far * m, 0.4)
    img = img * reveal(ph, pw, name.endswith("_t"))[..., None]
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
    img = bpy.data.images.get("RI_Restaurant") or bpy.data.images.new("RI_Restaurant", SIZE, SIZE)
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
                   "Blender/glTF-before-flip convention (v = 0 at the bottom). Cells match Lovell's "
                   "Restaurant's ground-floor glass in tools/blender/lovells_restaurant.py: ladies_door, "
                   "ladies_t (Ladies' Entrance leaf and transom), door_l / door_r / door_t (centre double "
                   "door), display / display_t (display window, top row), south_<k> (south wall windows); "
                   "each cell spans the window back's bounding box.",
                   "cells": cells}, f, indent=1)
    print("wrote", OUT + ".jpg", "with", len(cells), "cells,", len(boxes), "boxes")


main()
