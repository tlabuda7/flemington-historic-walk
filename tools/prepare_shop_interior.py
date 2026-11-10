"""
prepare_shop_interior.py - draws `assets/textures/shared/shop_interior.jpg`: what you see
through the shop-front glass of the Nevius Store (78 Main St) - a dim c. 1920 dry-goods
store. Own work (no download, no lettering, no signs). Run INSIDE Blender (it needs numpy,
which Blender's Python has; the image is saved with bpy):

    exec(open(r"<project>/tools/prepare_shop_interior.py").read())

Why: the shared window_backs atlas gave each 2.4 m display window only 384 px, so the shop
interior looked blurry and blocky. Here every glass panel of the shop front gets its own
cell (about 250 px per metre), and the cells are not painted flat but ray-traced through a
simple box model of the store, seen from a person on the sidewalk, so the perspective is
right: a low window display just behind the glass (folded cloth, standing bolts, boxes),
long counters down both sides, wall shelving full of cloth bolts and boxes, drawers under
them, two centre tables, plank floor, pressed-tin ceiling with unlit lamps, and the far
rear window glowing faintly 32 m back. Daylight comes only from the front, so it falls off
quickly into the store. Slightly out of focus (more with distance), dark, no text.

Writes
    assets/textures/shared/shop_interior.jpg    1024 x 1024, sRGB, JPEG quality 90
    assets/textures/shared/shop_interior.json   cell layout (same format as window_backs.json)

Local frame = the Nevius model's: x across the front (-x = north), y into the building,
z up, shop floor at z 0.12. The cells and their window-back planes match
tools/blender/nevius_store.py (display windows, door glass, splayed returns, transoms).
"""

import json
import math
import os
import random
import zlib

import numpy as np

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
OUT = os.path.join(PROJECT, "assets", "textures", "shared", "shop_interior")
SIZE = 1024
SS = 3                         # supersampling per axis
EXPOSURE = 0.38
EYE_Z = 1.65

# name -> (px rect [x, y, w, h] (row 0 at top), plane origin (x, y), plane direction (unit,
#          left -> right as seen from outside), length, z0, z1, eye (x, y, z))
CELLS = {
    "shop_a":      ([0, 0, 600, 552], (-3.35, 0.08), (1, 0), 2.42, 0.72, 2.95, (-2.14, -3.0, EYE_Z)),
    "shop_b":      ([600, 0, 392, 552], (0.83, 0.08), (1, 0), 1.59, 0.72, 2.95, (1.62, -3.0, EYE_Z)),
    "door_l":      ([0, 552, 132, 392], (-0.66, 1.235), (1, 0), 0.515, 1.05, 2.58, (0.0, -3.0, EYE_Z)),
    "door_r":      ([132, 552, 132, 392], (0.045, 1.235), (1, 0), 0.515, 1.05, 2.58, (0.0, -3.0, EYE_Z)),
    "return_n":    ([264, 552, 220, 392], (-0.85, 0.10), None, None, 0.70, 2.85, (0.6, -0.8, EYE_Z)),
    "return_s":    ([484, 552, 220, 392], (0.65, 1.30), None, None, 0.70, 2.85, (-0.6, -0.8, EYE_Z)),
    "transom_door": ([704, 552, 320, 40], (-0.75, 1.28), (1, 0), 1.40, 2.75, 2.92, (0.0, -2.5, EYE_Z)),
    "transom":     ([0, 944, 1024, 80], (-3.45, 0.08), (1, 0), 6.90, 3.05, 3.55, (0.0, -5.0, EYE_Z)),
}
# the splayed returns run from the front to the back (north) and back to front (south)
for _n, (a, b) in (("return_n", ((-0.85, 0.10), (-0.75, 1.30))), ("return_s", ((0.65, 1.30), (0.75, 0.10)))):
    L = math.dist(a, b)
    c = list(CELLS[_n])
    c[2], c[3] = ((b[0] - a[0]) / L, (b[1] - a[1]) / L), L
    CELLS[_n] = tuple(c)


def lin(rgb):
    c = np.array(rgb, dtype=np.float64) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# muted cloth and box colours (sRGB), c. 1920 dry goods
CLOTH = [(58, 62, 84), (92, 70, 52), (120, 104, 82), (70, 48, 44), (96, 98, 92), (150, 140, 120),
         (54, 66, 58), (110, 76, 60), (128, 118, 96), (80, 80, 96), (170, 160, 138), (66, 54, 46),
         (140, 120, 100), (84, 92, 104), (180, 172, 150), (100, 60, 52)]
BOXES = [(150, 140, 120), (128, 118, 100), (166, 158, 140), (110, 100, 86), (140, 128, 104)]
CLOTH_L = [lin(c) for c in CLOTH]
BOX_L = [lin(c) for c in BOXES]

# ---------------------------------------------------------------------------
# Store model: interior box + axis-aligned boxes
# ---------------------------------------------------------------------------
ROOM_LO, ROOM_HI = np.array([-3.72, 0.0, 0.12]), np.array([3.72, 31.9, 4.30])
SHELF_X = 3.30                 # face of the wall shelving (both sides)
SHELF_Y0, SHELF_Y1 = 1.4, 24.0
K_SHELF_N, K_SHELF_S, K_COUNTER, K_TABLE, K_PLATFORM, K_CLOTH, K_BOLT, K_BOX, K_LAMP, K_RECESS = range(10)
boxes = []                     # (lo, hi, kind, colour)
rng = random.Random(20261110)


def add(lo, hi, kind, colour=(0.1, 0.08, 0.06)):
    boxes.append((np.array(lo, float), np.array(hi, float), kind, np.array(colour, float)))


add((-3.72, SHELF_Y0, 0.12), (-SHELF_X, SHELF_Y1, 3.75), K_SHELF_N)
add((SHELF_X, SHELF_Y0, 0.12), (3.72, SHELF_Y1, 3.75), K_SHELF_S)
add((-3.00, 2.6, 0.12), (-2.30, 21.0, 0.98), K_COUNTER)
add((2.30, 2.6, 0.12), (3.00, 21.0, 0.98), K_COUNTER)
for y0 in (6.0, 12.5):
    add((-0.65, y0, 0.12), (0.65, y0 + 2.2, 0.80), K_TABLE)
    x = -0.58
    while x < 0.5:                                           # stacks of folded cloth on the tables
        w = rng.uniform(0.25, 0.4)
        z = 0.80
        for _ in range(rng.randint(2, 5)):
            h = rng.uniform(0.04, 0.08)
            yy = y0 + rng.uniform(0.1, 0.4)
            add((x, yy, z), (x + w, yy + rng.uniform(0.3, 0.5), z + h), K_CLOTH, rng.choice(CLOTH_L))
            z += h
        x += w + rng.uniform(0.04, 0.12)
for y in (4.0, 9.0, 14.0, 19.0, 24.0):                       # unlit pendant lamps
    for x in (-1.3, 1.3):
        add((x - 0.18, y - 0.18, 3.45), (x + 0.18, y + 0.18, 3.62), K_LAMP)
        add((x - 0.012, y - 0.012, 3.62), (x + 0.012, y + 0.012, 4.30), K_LAMP)
add((-0.85, 0.0, 0.12), (0.75, 1.30, 2.95), K_RECESS)        # the entrance recess, seen from the displays: its
                                                             # panelled side partitions
# window displays: platform just under the sill, goods on it
for x0, x1 in ((-3.35, -0.93), (0.83, 2.42)):
    add((x0, 0.10, 0.12), (x1, 1.20, 0.64), K_PLATFORM)
    x = x0 + rng.uniform(0.05, 0.15)
    while x < x1 - 0.15:
        r = rng.random()
        if r < 0.40:                                         # stacked folded cloth
            w, d = rng.uniform(0.28, 0.42), rng.uniform(0.25, 0.35)
            y = rng.uniform(0.2, 0.75)
            z = 0.64
            for _ in range(rng.randint(2, 6)):
                h = rng.uniform(0.04, 0.09)
                add((x, y, z), (x + w, y + d, z + h), K_CLOTH, rng.choice(CLOTH_L))
                z += h
        elif r < 0.75:                                       # a few bolts standing on end
            w = rng.uniform(0.09, 0.13)
            for _ in range(rng.randint(1, 3)):
                y = rng.uniform(0.35, 0.95)
                add((x, y, 0.64), (x + w, y + 0.12, 0.64 + rng.uniform(0.55, 1.05)), K_BOLT, rng.choice(CLOTH_L))
                x += w + 0.02
        else:                                                # plain boxes, one on another
            w, d = rng.uniform(0.25, 0.4), rng.uniform(0.2, 0.35)
            y = rng.uniform(0.25, 0.8)
            z = 0.64
            for _ in range(rng.randint(1, 3)):
                h = rng.uniform(0.10, 0.18)
                add((x, y, z), (x + w, y + d, z + h), K_BOX, rng.choice(BOX_L))
                z += h
                w *= 0.85
        x += w + rng.uniform(0.04, 0.16)

B_LO = np.array([b[0] for b in boxes])
B_HI = np.array([b[1] for b in boxes])
B_KIND = np.array([b[2] for b in boxes])
B_COL = np.array([b[3] for b in boxes])

# wall shelving goods, one row per shelf: slot ends along y, type, colour, fill height
SHELF_Z0, SHELF_DZ, SHELF_ROWS = 1.05, 0.33, 8
shelf_rows = {}
for side in (K_SHELF_N, K_SHELF_S):
    rows = []
    for k in range(SHELF_ROWS):
        ends, types, cols, fills, counts = [], [], [], [], []
        y = SHELF_Y0
        while y < SHELF_Y1:
            r = rng.random()
            if r < 0.08:
                w, t, c, f, n = rng.uniform(0.08, 0.25), 0, lin((20, 16, 12)), 0.0, 1        # gap
            elif r < 0.75:
                w, t, c, f, n = rng.uniform(0.3, 0.75), 1, rng.choice(CLOTH_L), rng.uniform(0.55, 0.85), rng.randint(2, 4)
            else:
                w, t, c, f, n = rng.uniform(0.25, 0.55), 2, rng.choice(BOX_L), rng.uniform(0.45, 0.8), rng.randint(1, 3)
            y += w
            ends.append(y), types.append(t), cols.append(c), fills.append(f), counts.append(n)
        rows.append((np.array(ends), np.array(types), np.array(cols), np.array(fills), np.array(counts)))
    shelf_rows[side] = rows


# ---------------------------------------------------------------------------
# Ray tracing
# ---------------------------------------------------------------------------
def trace(O, D):
    n = O.shape[0]
    with np.errstate(divide="ignore", invalid="ignore"):
        inv = 1.0 / np.where(np.abs(D) < 1e-12, 1e-12, D)
    # the room (from inside): exit point
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


def albedo(P, N, kind, col):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    A = np.zeros_like(P)
    wood = lin((70, 50, 34))
    dark_wood = lin((44, 32, 22))
    # room surfaces
    room = kind == -1
    floor = room & (N[:, 2] > 0.5)
    planks = 0.8 + 0.25 * hashf(np.floor(x / 0.11), 0.0, 1)
    A[floor] = lin((86, 64, 44)) * planks[floor, None]
    ceil = room & (N[:, 2] < -0.5)
    tin = 0.85 + 0.15 * ((np.floor(x / 0.6) + np.floor(y / 0.6)) % 2)
    A[ceil] = lin((176, 168, 146)) * tin[ceil, None]
    walls = room & (np.abs(N[:, 2]) < 0.5)
    A[walls] = lin((112, 98, 80))
    back = room & (N[:, 1] < -0.5)
    win = back & (np.abs(x - 2.0) < 0.42) & (z > 1.2) & (z < 2.8)
    A[back] = lin((70, 60, 50))
    A[win] = lin((235, 230, 215))                              # rear window (lit from behind, see shade())
    front = room & (N[:, 1] > 0.5)
    A[front] = lin((60, 52, 44))
    # wall shelving
    for side in (K_SHELF_N, K_SHELF_S):
        m = kind == side
        face = m & (np.abs(N[:, 0]) > 0.5)
        A[m & ~face] = dark_wood
        lower = face & (z < SHELF_Z0)                          # drawers under the shelving
        dr = (np.abs(((z - 0.12) / 0.23) % 1 - 0.5) > 0.44) | (np.abs((y / 0.55) % 1 - 0.5) > 0.46)
        A[lower] = wood * 0.75
        A[lower & dr] = dark_wood * 0.6
        knob = lower & (np.abs((y / 0.55) % 1 - 0.5) < 0.03) & (np.abs(((z - 0.12) / 0.23) % 1 - 0.5) < 0.08)
        A[knob] = lin((150, 130, 100))
        upper = face & (z >= SHELF_Z0) & (z < SHELF_Z0 + SHELF_DZ * SHELF_ROWS)
        A[face & (z >= SHELF_Z0 + SHELF_DZ * SHELF_ROWS)] = wood
        k = np.clip(((z - SHELF_Z0) / SHELF_DZ).astype(int), 0, SHELF_ROWS - 1)
        fz = (z - SHELF_Z0) / SHELF_DZ - k
        for r in range(SHELF_ROWS):
            mr = upper & (k == r)
            if not mr.any():
                continue
            ends, types, cols, fills, counts = shelf_rows[side][r]
            idx = np.clip(np.searchsorted(ends, y[mr]), 0, len(ends) - 1)
            f = fz[mr]
            t, c, fill, cnt = types[idx], cols[idx], fills[idx], counts[idx]
            a = np.tile(lin((18, 14, 10)), (mr.sum(), 1))            # dark back of the shelf
            g = (f - 0.07) / np.maximum(fill, 1e-3)                  # 0..1 inside the goods
            inside = (f > 0.07) & (g < 1) & (t > 0)
            band = (g * cnt) % 1
            bolt = 0.55 + 0.45 * np.sin(np.pi * band) ** 0.7         # rolled cloth: round in section
            boxl = np.where(band > 0.9, 0.7, 1.0)                    # box lids
            a = np.where(inside[:, None], c * np.where(t == 1, bolt, boxl)[:, None], a)
            a = np.where((f <= 0.07)[:, None], wood, a)              # shelf board
            A[mr] = a
        upright = upper & (np.abs(((y - SHELF_Y0) / 1.2) % 1 - 0.5) > 0.48)
        A[upright] = dark_wood
    # counters: dark panelled fronts, a lighter worn top
    m = kind == K_COUNTER
    A[m] = dark_wood
    A[m & (N[:, 2] > 0.5)] = wood * 1.3
    pan = m & (np.abs(N[:, 0]) > 0.5) & ((np.abs((y / 0.9) % 1 - 0.5) > 0.44) | (z > 0.88) | (z < 0.25))
    A[pan] = dark_wood * 0.7
    A[kind == K_TABLE] = wood
    A[kind == K_PLATFORM] = lin((96, 84, 70))                  # cloth-covered platform
    A[(kind == K_PLATFORM) & (N[:, 2] < 0.5)] = dark_wood
    for kk in (K_CLOTH, K_BOX):
        m = kind == kk
        A[m] = col[m] * np.where(N[m, 2] > 0.5, 1.1, 0.9)[:, None]
    m = kind == K_BOLT                                         # bolt on end: wound cloth, rounder at the edges
    side_u = np.where(np.abs(N[:, 1]) > 0.5, (x * 8.3) % 1, (y * 8.3) % 1)
    A[m] = col[m] * (0.6 + 0.4 * np.sin(np.pi * side_u[m]) ** 0.6)[:, None]
    A[kind == K_LAMP] = lin((40, 40, 36))
    m = kind == K_RECESS                                       # plain dark partition beside the displays
    A[m] = dark_wood * 0.8
    return A


def shade(P, N, kind, t, D):
    """Daylight only from the shop front (y ~ 0): falls off into the store; faces turned to
    the windows and tops near the front get the most; the rear window glows faintly."""
    y = P[:, 1]
    front = 1.0 * np.exp(-np.maximum(y, 0) / 3.4) + 0.14 * np.exp(-np.maximum(y, 0) / 12.0)
    facing = 0.55 + 0.45 * np.maximum(0, -N[:, 1]) + 0.25 * np.maximum(0, N[:, 2]) - 0.05 * np.maximum(0, -N[:, 2])
    rear = 0.25 * np.exp(-(31.9 - y) / 2.5)
    Lt = front * facing + rear + 0.015
    back = (kind == -1) & (N[:, 1] < -0.5) & (np.abs(P[:, 0] - 2.0) < 0.42) & (P[:, 2] > 1.2) & (P[:, 2] < 2.8)
    Lt[back] = 0.40                                            # the rear window itself, faint
    return Lt


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
    (px, py, pw, ph), origin, udir, length, z0, z1, eye = CELLS[name]
    W, H = pw * SS, ph * SS
    u = (np.arange(W) + 0.5) / W
    v = 1 - (np.arange(H) + 0.5) / H                         # row 0 = top = z1
    uu, vv = np.meshgrid(u, v)
    P0 = np.stack([origin[0] + udir[0] * length * uu, origin[1] + udir[1] * length * uu,
                   z0 + (z1 - z0) * vv], axis=-1).reshape(-1, 3)
    E = np.array(eye, float)
    D = P0 - E
    D /= np.linalg.norm(D, axis=1, keepdims=True)
    t, P, N, kind, col = trace(P0, D)
    C = albedo(P, N, kind, col) * shade(P, N, kind, t, D)[:, None] * EXPOSURE
    img = to_srgb(C).reshape(H, W, 3)
    dist = t.reshape(H, W)
    img = img.reshape(ph, SS, pw, SS, 3).mean(axis=(1, 3))
    dist = dist.reshape(ph, SS, pw, SS).mean(axis=(1, 3))
    # out of focus, more with distance (focus on the glass, as seen from the sidewalk)
    near, far = blur(img, 0.55), blur(img, 1.7)
    m = np.clip((dist - 0.8) / 5.0, 0, 1)[..., None]
    img = near * (1 - m) + far * m
    nrng = np.random.default_rng(zlib.crc32(name.encode()))
    img = img + nrng.normal(0, 0.006, img.shape)
    return np.clip(img, 0, 1)


def main():
    atlas = np.zeros((SIZE, SIZE, 3))
    atlas[:] = to_srgb(lin((22, 18, 15)) * 0.0 + 0.004)
    cells = {}
    for name, c in CELLS.items():
        x, y, w, h = c[0]
        atlas[y:y + h, x:x + w] = render_cell(name)
        cells[name] = {"px": [x, y, w, h], "uv": [x / SIZE, 1 - (y + h) / SIZE, (x + w) / SIZE, 1 - y / SIZE]}
    import bpy
    img = bpy.data.images.get("SI_ShopInterior") or bpy.data.images.new("SI_ShopInterior", SIZE, SIZE)
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
                   "Blender/glTF-before-flip convention (v = 0 at the bottom). Cells match the Nevius "
                   "Store shop front (tools/blender/nevius_store.py).", "cells": cells}, f, indent=1)
    print("wrote", OUT + ".jpg", "with", len(cells), "cells,", len(boxes), "boxes")


main()
