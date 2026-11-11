"""
prepare_grocery_interior.py - draws `assets/textures/block-35-41/grocery_interior.jpg`: what
you see through the shop window and the glazed door of the grocery at 35-37 Main St
("Gro." on the 1921 Sanborn map) - a dim c. 1920 grocery. Own work (no download, no
lettering, no labels, no signs). Grocery variant of tools/prepare_shop_interior.py (same
method). Run INSIDE Blender (it needs numpy; the image is saved with bpy):

    exec(open(r"<project>/tools/prepare_grocery_interior.py").read())

Each glass panel gets its own cell, ray-traced through a simple box model of the store from a
person on the sidewalk, so the perspective is right: a window display just behind the glass
(open crates of apples, potatoes, onions, cabbages, oranges; stacked tins; baskets), long
counters down both sides, wall shelving full of tins, jars and packets (plain colour bands,
no labels), barrels and sacks in the aisle, plank floor, pressed-tin ceiling with unlit lamps,
a dim back door. Daylight comes only from the front, under the two-storey porch, so it falls
off quickly into the store. Slightly out of focus (more with distance), dark, no text.

Writes
    assets/textures/block-35-41/grocery_interior.jpg    1024 x 1024, sRGB, JPEG quality 90
    assets/textures/block-35-41/grocery_interior.json   cell layout (same format as
        shared/window_backs.json) + "plane": the window-back rectangle in the model's frame
        (x0, x1, z0, z1, y) - tools/blender/block_35_41.py builds its backs from it.

Frame = tools/blender/block_35_41.py: x along the front (+x = north), y into the building
(front wall of 35-37 at y 1.98), z up from the sidewalk top; shop floor (= porch deck) z 0.45.
"""

import json
import math
import os
import random
import zlib

import numpy as np

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
OUT = os.path.join(PROJECT, "assets", "textures", "block-35-41", "grocery_interior")
SIZE = 1024
SS = 3                         # supersampling per axis
EXPOSURE = 0.36
EYE_Z = 1.65                   # eye on the sidewalk (sidewalk top = z 0)
FLOOR = 0.45

# name -> (px rect [x, y, w, h] (row 0 at top), plane (x0, x1, z0, z1, y), eye (x, y, z))
CELLS = {
    "shop": ([0, 0, 600, 676], (4.03, 5.52, 1.11, 2.79, 2.10), (4.40, -3.2, EYE_Z)),
    "door": ([600, 0, 216, 320], (2.42, 3.08, 1.70, 2.68, 2.13), (2.75, -3.2, EYE_Z)),
}


def lin(rgb):
    c = np.array(rgb, dtype=np.float64) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# muted c. 1920 colours (sRGB)
PRODUCE = [(132, 40, 32), (150, 58, 36), (128, 100, 62), (146, 118, 76), (94, 120, 64), (176, 104, 34),
           (168, 140, 56), (110, 50, 40), (120, 134, 78)]
TINS = [(120, 44, 38), (58, 70, 96), (150, 120, 62), (70, 86, 60), (170, 160, 130), (96, 60, 44),
        (140, 96, 50), (82, 82, 88), (160, 140, 100), (110, 36, 40)]
PACKETS = [(176, 160, 124), (150, 132, 98), (190, 176, 146), (124, 104, 80), (160, 120, 80)]
JARS = [(120, 110, 80), (140, 96, 60), (100, 90, 70), (150, 140, 110)]
PRODUCE_L = [lin(c) for c in PRODUCE]
TIN_L = [lin(c) for c in TINS]
PACKET_L = [lin(c) for c in PACKETS]
JAR_L = [lin(c) for c in JARS]

# ---------------------------------------------------------------------------
# Store model: interior box + axis-aligned boxes
# ---------------------------------------------------------------------------
ROOM_LO, ROOM_HI = np.array([-0.32, 2.14, FLOOR]), np.array([5.78, 15.70, 3.55])
SHELF_S, SHELF_N = 0.05, 5.40          # faces of the wall shelving (south and north walls)
SHELF_Y0, SHELF_Y1 = 3.4, 14.6
(K_SHELF_S, K_SHELF_N, K_COUNTER, K_PLATFORM, K_CRATE, K_PRODUCE, K_TIN, K_BASKET, K_BARREL, K_SACK,
 K_LAMP, K_BACKSHELF) = range(12)
boxes = []                             # (lo, hi, kind, colour)
rng = random.Random(19201110)


def add(lo, hi, kind, colour=(0.1, 0.08, 0.06)):
    boxes.append((np.array(lo, float), np.array(hi, float), kind, np.array(colour, float)))


add((-0.32, SHELF_Y0, FLOOR), (SHELF_S, SHELF_Y1, 3.30), K_SHELF_S)
add((SHELF_N, 2.14, FLOOR), (5.78, SHELF_Y1, 3.30), K_SHELF_N)        # runs right up to the shop front
add((0.55, 4.2, FLOOR), (1.20, 13.4, 1.38), K_COUNTER)               # south counter
add((4.55, 4.2, FLOOR), (5.10, 13.4, 1.38), K_COUNTER)               # north counter
add((-0.32, 15.30, FLOOR), (5.78, 15.70, 3.10), K_BACKSHELF)         # back wall shelving
for y in (5.0, 9.0, 13.0):                                           # unlit pendant lamps
    for x in (1.6, 3.9):
        add((x - 0.16, y - 0.16, 3.05), (x + 0.16, y + 0.16, 3.20), K_LAMP)
        add((x - 0.012, y - 0.012, 3.20), (x + 0.012, y + 0.012, 3.55), K_LAMP)
# barrels, sacks and a few crates in the aisle
for x, y in ((1.75, 5.4), (2.35, 5.5), (3.5, 7.8), (1.9, 10.2)):
    add((x - 0.24, y - 0.24, FLOOR), (x + 0.24, y + 0.24, FLOOR + 0.78), K_BARREL, lin((96, 72, 48)))
for x, y in ((3.3, 5.2), (3.85, 5.0), (2.7, 9.2)):
    add((x - 0.22, y - 0.16, FLOOR), (x + 0.22, y + 0.16, FLOOR + rng.uniform(0.55, 0.7)), K_SACK,
        lin((150, 134, 104)))
# goods on the counters (a few stacks and jars)
for x0, x1 in ((0.62, 1.12), (4.62, 5.02)):
    y = 4.6
    while y < 12.5:
        h = rng.uniform(0.12, 0.35)
        add((x0 + 0.08, y, 1.38), (x1 - 0.08, y + rng.uniform(0.18, 0.35), 1.38 + h), K_TIN, rng.choice(JAR_L))
        y += rng.uniform(0.9, 2.2)

# window display behind the shop window: a stepped platform, crates of produce, tins, baskets
PX0, PX1 = 3.90, 5.70
add((PX0, 2.14, FLOOR), (PX1, 3.30, 0.98), K_PLATFORM)
add((PX0, 2.70, 0.98), (PX1, 3.30, 1.28), K_PLATFORM)                # back step
for zt, y0, y1 in ((0.98, 2.22, 2.66), (1.28, 2.78, 3.24)):
    x = PX0 + rng.uniform(0.02, 0.06)
    while x < PX1 - 0.2:
        r = rng.random()
        if r < 0.62:                                                 # open crate heaped with produce
            w = rng.uniform(0.34, 0.46)
            h = rng.uniform(0.16, 0.24)
            add((x, y0, zt), (x + w, y1, zt + h), K_CRATE, lin((120, 96, 66)))
            add((x + 0.02, y0 + 0.02, zt + h), (x + w - 0.02, y1 - 0.02, zt + h + 0.05), K_PRODUCE,
                rng.choice(PRODUCE_L))
        elif r < 0.85:                                               # pyramid of tins
            w = rng.uniform(0.30, 0.42)
            c = rng.choice(TIN_L)
            z = zt
            ww = w
            for _ in range(rng.randint(2, 4)):
                add((x + (w - ww) / 2, y0 + 0.06, z), (x + (w + ww) / 2, y0 + 0.18, z + 0.11), K_TIN, c)
                z += 0.11
                ww -= 0.09
        else:                                                        # basket of produce
            w = rng.uniform(0.28, 0.36)
            add((x, y0 + 0.05, zt), (x + w, y1 - 0.05, zt + 0.16), K_BASKET, lin((140, 112, 70)))
            add((x + 0.03, y0 + 0.08, zt + 0.16), (x + w - 0.03, y1 - 0.08, zt + 0.20), K_PRODUCE,
                rng.choice(PRODUCE_L))
        x += w + rng.uniform(0.03, 0.08)

B_LO = np.array([b[0] for b in boxes])
B_HI = np.array([b[1] for b in boxes])
B_KIND = np.array([b[2] for b in boxes])
B_COL = np.array([b[3] for b in boxes])

# wall shelving goods, one row per shelf: slot ends along y, type, colour, fill, count
SHELF_Z0, SHELF_DZ, SHELF_ROWS = 1.25, 0.30, 7
shelf_rows = {}
for side in (K_SHELF_S, K_SHELF_N, K_BACKSHELF):
    rows = []
    for k in range(SHELF_ROWS):
        ends, types, cols, fills, counts = [], [], [], [], []
        y = 0.0
        while y < 14.0:
            r = rng.random()
            if r < 0.07:
                w, t, c, f, n = rng.uniform(0.08, 0.25), 0, lin((20, 16, 12)), 0.0, 1          # gap
            elif r < 0.60:
                w, t, c, f, n = rng.uniform(0.3, 0.9), 1, rng.choice(TIN_L), rng.choice((0.38, 0.45, 0.72, 0.8)), 0  # tins
            elif r < 0.82:
                w, t, c, f, n = rng.uniform(0.25, 0.6), 2, rng.choice(PACKET_L), rng.uniform(0.5, 0.8), 0  # packets
            else:
                w, t, c, f, n = rng.uniform(0.2, 0.5), 3, rng.choice(JAR_L), rng.uniform(0.5, 0.75), 0  # jars
            y += w
            ends.append(y), types.append(t), cols.append(c), fills.append(f), counts.append(n)
        rows.append((np.array(ends), np.array(types), np.array(cols), np.array(fills)))
    shelf_rows[side] = rows


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
    col = np.zeros((n, 3))
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
            col[hit] = B_COL[i]
    N = np.zeros((n, 3))
    N[np.arange(n), axis] = -np.sign(D[np.arange(n), axis])
    P = O + D * best_t[:, None]
    return best_t, P, N, kind, col


def hashf(a, b, seed=0):
    v = np.sin(a * 12.9898 + b * 78.233 + seed * 37.719) * 43758.5453
    return v - np.floor(v)


def produce_pattern(u, v, size):
    """Heaped round fruit/vegetables: discs on a jittered grid, dark gaps between."""
    gu, gv = np.floor(u / size), np.floor(v / size)
    fu, fv = u / size - gu - 0.5, v / size - gv - 0.5
    jit = hashf(gu, gv, 5) * 0.25
    d = np.sqrt(fu * fu + fv * fv)
    shade_ = np.clip(1.0 - (d / (0.48 - jit * 0.3)) ** 2, 0.0, 1.0)
    var = 0.80 + 0.35 * hashf(gu, gv, 9)
    return np.where(d < 0.48 - jit * 0.3, (0.55 + 0.45 * shade_) * var, 0.22)


def albedo(P, N, kind, col):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    A = np.zeros_like(P)
    wood = lin((74, 54, 36))
    dark_wood = lin((44, 32, 22))
    room = kind == -1
    floor = room & (N[:, 2] > 0.5)
    planks = 0.8 + 0.25 * hashf(np.floor(x / 0.10), 0.0, 1)
    A[floor] = lin((92, 70, 48)) * planks[floor, None]
    ceil = room & (N[:, 2] < -0.5)
    tin = 0.85 + 0.15 * ((np.floor(x / 0.6) + np.floor(y / 0.6)) % 2)
    A[ceil] = lin((170, 162, 140)) * tin[ceil, None]
    walls = room & (np.abs(N[:, 2]) < 0.5)
    A[walls] = lin((118, 104, 84))
    front = room & (N[:, 1] > 0.5)
    A[front] = lin((60, 52, 44))
    back = room & (N[:, 1] < -0.5)
    A[back] = lin((70, 60, 50))
    # wall shelving (sides and back)
    for side in (K_SHELF_S, K_SHELF_N, K_BACKSHELF):
        m = kind == side
        if not m.any():
            continue
        face_axis = 1 if side == K_BACKSHELF else 0
        face = m & (np.abs(N[:, face_axis]) > 0.5)
        A[m & ~face] = dark_wood
        along = x if side == K_BACKSHELF else y
        lower = face & (z < SHELF_Z0)                          # drawers / bins under the shelving
        dr = (np.abs(((z - FLOOR) / 0.26) % 1 - 0.5) > 0.44) | (np.abs((along / 0.5) % 1 - 0.5) > 0.46)
        A[lower] = wood * 0.75
        A[lower & dr] = dark_wood * 0.6
        knob = lower & (np.abs((along / 0.5) % 1 - 0.5) < 0.03) & (np.abs(((z - FLOOR) / 0.26) % 1 - 0.5) < 0.08)
        A[knob] = lin((150, 130, 100))
        upper = face & (z >= SHELF_Z0) & (z < SHELF_Z0 + SHELF_DZ * SHELF_ROWS)
        A[face & (z >= SHELF_Z0 + SHELF_DZ * SHELF_ROWS)] = wood
        k = np.clip(((z - SHELF_Z0) / SHELF_DZ).astype(int), 0, SHELF_ROWS - 1)
        fz = (z - SHELF_Z0) / SHELF_DZ - k
        for r in range(SHELF_ROWS):
            mr = upper & (k == r)
            if not mr.any():
                continue
            ends, types, cols, fills = shelf_rows[side][r]
            a_ = along[mr] - (SHELF_Y0 if side != K_BACKSHELF else -0.32)
            idx = np.clip(np.searchsorted(ends, a_), 0, len(ends) - 1)
            f = fz[mr]
            t, c, fill = types[idx], cols[idx], fills[idx]
            a = np.tile(lin((18, 14, 10)), (mr.sum(), 1))            # dark back of the shelf
            g = (f - 0.07) / np.maximum(fill, 1e-3)                  # 0..1 inside the goods
            inside = (f > 0.07) & (g < 1) & (t > 0)
            # tins: narrow round cans (bright rim at the top, shaded sides); label band in the middle
            can = (a_ / 0.085) % 1
            stack = np.where(fill > 0.5, 2.0, 1.0)                     # one or two tins high
            gg = (g * stack) % 1
            label = (gg > 0.12) & (gg < 0.88)
            round_ = 0.5 + 0.5 * np.sin(np.pi * can) ** 0.6
            tin_s = round_ * np.where(can < 0.07, 0.35, 1.0)
            c = np.where((label | (t != 1))[:, None], c, lin((92, 90, 84)))   # bare tin rims
            pk = (a_ / 0.13) % 1                                       # packets: flat boxes side by side
            pk_s = np.where(pk > 0.93, 0.6, 1.0) * np.where(g > 0.9, 1.15, 1.0)
            jr = (a_ / 0.11) % 1                                       # jars: glassy, darker contents
            jr_s = (0.45 + 0.4 * np.sin(np.pi * jr) ** 2) * np.where(g > 0.85, 1.4, 1.0)
            s_ = np.where(t == 1, tin_s, np.where(t == 2, pk_s, jr_s))
            a = np.where(inside[:, None], c * s_[:, None], a)
            a = np.where((f <= 0.07)[:, None], wood, a)              # shelf board
            A[mr] = a
        upright = upper & (np.abs((along / 1.1) % 1 - 0.5) > 0.48)
        A[upright] = dark_wood
    # counters: dark panelled fronts, a lighter worn top
    m = kind == K_COUNTER
    A[m] = dark_wood
    A[m & (N[:, 2] > 0.5)] = wood * 1.3
    pan = m & (np.abs(N[:, 0]) > 0.5) & ((np.abs((y / 0.8) % 1 - 0.5) > 0.44) | (z > 1.28) | (z < 0.58))
    A[pan] = dark_wood * 0.7
    m = kind == K_PLATFORM                                     # green baize-covered display steps
    A[m] = lin((62, 70, 52))
    A[m & (N[:, 2] < 0.5)] = dark_wood
    m = kind == K_CRATE                                        # slatted crate sides
    slat = np.where(np.abs(N[:, 0]) > 0.5, (z / 0.06) % 1, (z / 0.06) % 1)
    A[m] = (col[m] * np.where(slat[m] > 0.82, 0.45, 1.0)[:, None])
    m = kind == K_BASKET                                       # woven basket
    weave = 0.75 + 0.25 * ((np.floor(x / 0.025) + np.floor(z / 0.025)) % 2)
    A[m] = col[m] * weave[m, None]
    m = kind == K_PRODUCE
    top = N[:, 2] > 0.5
    u = np.where(top, x, np.where(np.abs(N[:, 0]) > 0.5, y, x))
    v = np.where(top, y, z)
    pat = produce_pattern(u, v, 0.075)
    A[m] = col[m] * pat[m, None]
    m = kind == K_TIN
    can = np.where(np.abs(N[:, 1]) > 0.5, (x / 0.075) % 1, (y / 0.075) % 1)
    A[m] = col[m] * (0.6 + 0.4 * np.sin(np.pi * can[m]) ** 0.6)[:, None] * np.where(N[m, 2] > 0.5, 1.25, 1.0)[:, None]
    m = kind == K_BARREL                                       # staves and two dark hoops
    stave = np.where(np.abs(N[:, 1]) > 0.5, (x / 0.09) % 1, (y / 0.09) % 1)
    hoop = (np.abs(z - (FLOOR + 0.16)) < 0.03) | (np.abs(z - (FLOOR + 0.62)) < 0.03)
    A[m] = col[m] * (0.65 + 0.35 * np.sin(np.pi * stave[m]) ** 0.5)[:, None]
    A[m & hoop] = lin((40, 36, 32))
    A[m & (N[:, 2] > 0.5)] = lin((120, 96, 66))
    m = kind == K_SACK
    A[m] = col[m] * (0.85 + 0.15 * hashf(np.floor(x / 0.03), np.floor(z / 0.03), 3))[m, None]
    A[kind == K_LAMP] = lin((40, 40, 36))
    return A


def shade(P, N, kind, t, D):
    """Daylight only from the shop front (y ~ 2.1), under the deep porch: falls off quickly;
    faces turned to the front and tops near the front get the most."""
    y = P[:, 1] - 2.1
    front = 1.0 * np.exp(-np.maximum(y, 0) / 2.8) + 0.12 * np.exp(-np.maximum(y, 0) / 9.0)
    facing = 0.55 + 0.45 * np.maximum(0, -N[:, 1]) + 0.25 * np.maximum(0, N[:, 2]) - 0.05 * np.maximum(0, -N[:, 2])
    rear = 0.12 * np.exp(-(15.70 - P[:, 1]) / 2.0)
    return front * facing + rear + 0.015


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


def render_cell(name):
    (px, py, pw, ph), (x0, x1, z0, z1, yb), eye = CELLS[name]
    W, H = pw * SS, ph * SS
    u = (np.arange(W) + 0.5) / W
    v = 1 - (np.arange(H) + 0.5) / H                         # row 0 = top = z1
    uu, vv = np.meshgrid(u, v)
    P0 = np.stack([x0 + (x1 - x0) * uu, np.full_like(uu, yb), z0 + (z1 - z0) * vv], axis=-1).reshape(-1, 3)
    E = np.array(eye, float)
    D = P0 - E
    D /= np.linalg.norm(D, axis=1, keepdims=True)
    P0 = P0 + D * 0.05                                       # start just inside the shop front
    t, P, N, kind, col = trace(P0, D)
    C = albedo(P, N, kind, col) * shade(P, N, kind, t, D)[:, None] * EXPOSURE
    img = to_srgb(C).reshape(H, W, 3)
    dist = t.reshape(H, W)
    img = img.reshape(ph, SS, pw, SS, 3).mean(axis=(1, 3))
    dist = dist.reshape(ph, SS, pw, SS).mean(axis=(1, 3))
    near, far = blur(img, 0.6), blur(img, 1.8)               # out of focus, more with distance
    m = np.clip((dist - 0.6) / 4.0, 0, 1)[..., None]
    img = near * (1 - m) + far * m
    nrng = np.random.default_rng(zlib.crc32(name.encode()))
    img = img + nrng.normal(0, 0.006, img.shape)
    return np.clip(img, 0, 1)


def main():
    atlas = np.full((SIZE, SIZE, 3), 0.03)
    cells = {}
    for name, c in CELLS.items():
        x, y, w, h = c[0]
        atlas[y:y + h, x:x + w] = render_cell(name)
        x0, x1, z0, z1, yb = c[1]
        cells[name] = {"px": [x, y, w, h], "uv": [x / SIZE, 1 - (y + h) / SIZE, (x + w) / SIZE, 1 - y / SIZE],
                       "plane": [x0, x1, z0, z1, yb]}
    import bpy
    img = bpy.data.images.get("GI_GroceryInterior") or bpy.data.images.new("GI_GroceryInterior", SIZE, SIZE)
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
                   "Blender/glTF-before-flip convention (v = 0 at the bottom); plane = window-back rectangle "
                   "[x0, x1, z0, z1, y] in tools/blender/block_35_41.py's frame.", "cells": cells}, f, indent=1)
    print("wrote", OUT + ".jpg", "with", len(cells), "cells,", len(boxes), "boxes")


main()
