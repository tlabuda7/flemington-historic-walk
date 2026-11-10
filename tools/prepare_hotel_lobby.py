"""
prepare_hotel_lobby.py - draws `assets/textures/shared/hotel_lobby.jpg`: what you see through
the ground-floor windows and door fanlights of the Union Hotel (70-76 Main St), c. 1920: dim
public rooms behind the veranda. Own work (no download, no lettering, no signs). Run INSIDE
Blender (numpy; the image is saved with bpy), before tools/blender/union_hotel.py:

    exec(open(r"<project>/tools/prepare_hotel_lobby.py").read())

Same method as tools/prepare_shop_interior.py: every ground-floor pane gets its own cell, and
each cell is ray-traced through a simple box model of the ground floor, seen from a person on
the sidewalk in front of that window, so the perspective is right. Three rooms behind the
eleven front bays (partitions with doorways at x = +-4.05):
  - north (bays 0-3): parlour / reading room - armchairs, a round centre table, an upright
    piano and framed pictures on the back wall, muted green wallpaper;
  - centre (bays 4-6): lobby / office - a plain panelled counter with an empty pigeonhole key
    rack behind it, a few wooden chairs, a doorway to the back, brown wallpaper;
  - south (bays 7-10): dining room - small tables with dull white cloths, bentwood-ish chairs,
    a sideboard, faded red wallpaper.
Parlour and dining-room windows have heavy curtains tied back at both sides (drawn flat in the
window plane). Dark wood wainscot, picture rail, plain plaster ceiling with unlit pendant lamps. Daylight
only from the windows (under a 3 m veranda), so it falls off quickly into the rooms. Slightly
out of focus (more with distance), dark, with a soft reveal shadow at the head and sides.

Writes
    assets/textures/shared/hotel_lobby.jpg    1024 x 1024, sRGB, JPEG quality 90
    assets/textures/shared/hotel_lobby.json   cell layout (same format as window_backs.json)

Local frame = the Union Hotel model's (tools/blender/union_hotel.py): x along the front (-x =
north), y into the building (brick front wall face y = 3.0, 0.5 thick), z up from the
sidewalk; ground floor at z 0.8.
"""

import json
import math
import os
import random
import zlib

import numpy as np

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
OUT = os.path.join(PROJECT, "assets", "textures", "shared", "hotel_lobby")
SIZE = 1024
SS = 3                         # supersampling per axis
EXPOSURE = 1.8                 # under a 3 m veranda the window backs get little light in the bake
EYE_Z = 1.65                   # a person on the sidewalk (z 0)
EYE_Y = -3.0

# hotel numbers (keep in step with union_hotel.py)
W, FRONT, WALL, PLINTH, FLOOR = 29.7, 3.0, 0.5, 0.8, 3.6
BAYS = 11
BAY = W / BAYS
BAY_X = [-W / 2 + BAY * (i + 0.5) for i in range(BAYS)]
PLANE_Y = FRONT + 0.25         # the window backs (union_hotel.py: WB_DEPTH)
FAN_Y = FRONT + 0.26
FL = PLINTH                    # floor
CEIL = PLINTH + FLOOR          # 4.4
PX_M = 160                     # pixels per metre

# name -> (px rect [x, y, w, h], plane origin (x, y), length, z0, z1, eye (x, y, z))
CELLS = {}
_ground = [i for i in range(BAYS) if i not in (2, 5, 8)]
for k, i in enumerate(_ground):
    w, z0, z1 = 1.1, PLINTH + 0.5, PLINTH + 2.7 + 0.55
    pw, ph = round(w * PX_M), round((z1 - z0) * PX_M)          # 176 x 440
    px, py = (k % 5) * pw, (k // 5) * ph
    CELLS["lobby_%d" % i] = ([px, py, pw, ph], (BAY_X[i] - w / 2, PLANE_Y), w, z0, z1, (BAY_X[i], EYE_Y, EYE_Z))
_fx = 3 * 176
for i, r, (px, py) in ((5, 0.71, (_fx, 440)), (2, 0.485, (_fx + 228, 440)), (8, 0.485, (_fx + 228, 520))):
    z0, z1 = PLINTH + 2.7, PLINTH + 2.7 + r
    CELLS["fan_%d" % i] = ([px, py, round(2 * r * PX_M), round(r * PX_M)], (BAY_X[i] - r, FAN_Y), 2 * r, z0, z1,
                           (BAY_X[i], EYE_Y, EYE_Z))


def lin(rgb):
    c = np.array(rgb, dtype=np.float64) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# ---------------------------------------------------------------------------
# Ground-floor model: interior box + axis-aligned boxes
# ---------------------------------------------------------------------------
IX = W / 2 - WALL                                  # 14.35
ROOM_LO, ROOM_HI = np.array([-IX, FRONT + 0.2, FL]), np.array([IX, 11.6 - WALL, CEIL])
BACK_Y = 11.6 - WALL
PART_X = 1.5 * BAY                                 # 4.05
(K_PART, K_COUNTER, K_RACK, K_CHAIR, K_ARMCHAIR, K_TABLE, K_CLOTH, K_PIANO, K_PICTURE,
 K_LAMP, K_DOORWAY, K_SIDEBOARD, K_SETTEE) = range(13)
boxes = []
rng = random.Random(19201110)


def add(lo, hi, kind, colour=(0.1, 0.08, 0.06)):
    boxes.append((np.array(lo, float), np.array(hi, float), kind, np.array(colour, float)))


# partitions with a doorway (y 6.6 - 7.8, up to z 3.0)
for s in (-1, 1):
    x0, x1 = s * PART_X - 0.08, s * PART_X + 0.08
    add((x0, FRONT + WALL, FL), (x1, 6.6, CEIL), K_PART)
    add((x0, 7.8, FL), (x1, BACK_Y, CEIL), K_PART)
    add((x0, 6.6, FL + 2.3), (x1, 7.8, CEIL), K_PART)
# dark doorways in the back wall (to the hall / kitchen)
for x in (2.9, -9.0, 9.5):
    add((x - 0.5, BACK_Y - 0.02, FL), (x + 0.5, BACK_Y, FL + 2.3), K_DOORWAY)


def chair(x, y, face, arm=False):
    """Wooden side chair (or upholstered armchair) facing `face` = (dx, dy) unit."""
    dx, dy = face
    k = K_ARMCHAIR if arm else K_CHAIR
    w = 0.62 if arm else 0.44
    sh = 0.44 if arm else 0.46
    add((x - w / 2, y - w / 2, FL + (0.0 if arm else 0.40)), (x + w / 2, y + w / 2, FL + sh), k)
    if not arm:
        for lx in (-1, 1):
            for ly in (-1, 1):
                add((x + lx * 0.19 - 0.02, y + ly * 0.19 - 0.02, FL), (x + lx * 0.19 + 0.02, y + ly * 0.19 + 0.02, FL + 0.4), k)
    bh = 1.0 if arm else 0.95
    bt = 0.16 if arm else 0.05
    bx, by = x - dx * (w / 2 - bt / 2), y - dy * (w / 2 - bt / 2)       # back on the far side
    hx, hy = (bt / 2 if dx else w / 2), (bt / 2 if dy else w / 2)
    add((bx - hx, by - hy, FL + sh - 0.02), (bx + hx, by + hy, FL + bh), k)
    if arm:                                                              # arms
        for s in (-1, 1):
            ax, ay = (x + s * (w / 2 - 0.06), y) if dy else (x, y + s * (w / 2 - 0.06))
            ex, ey = (0.06, w / 2) if dy else (w / 2, 0.06)
            add((ax - ex, ay - ey, FL + sh), (ax + ex, ay + ey, FL + 0.65), k)


# lobby / office (centre)
add((-1.8, 8.6, FL), (1.8, 9.3, FL + 1.08), K_COUNTER)
add((-1.9, 8.55, FL + 1.08), (1.9, 9.35, FL + 1.13), K_COUNTER)           # top
add((-1.2, BACK_Y - 0.25, FL + 1.35), (1.2, BACK_Y, FL + 2.45), K_RACK)   # empty pigeonholes
for x, y, f in ((-3.1, 5.3, (1, 0)), (-3.1, 6.2, (1, 0)), (3.2, 5.6, (-1, 0)), (1.0, 6.4, (0, -1))):
    chair(x, y, f)
add((-3.95, 7.9, FL), (-3.45, 9.8, FL + 0.45), K_SETTEE)                  # bench against the partition
add((-3.95, 7.9, FL + 0.45), (-3.85, 9.8, FL + 0.95), K_SETTEE)
# parlour (north)
for x, y, f in ((-12.6, 5.0, (0, 1)), (-7.0, 5.2, (0, 1)), (-10.8, 8.4, (1, 0)), (-8.0, 8.6, (-1, 0)),
                (-5.4, 7.6, (-1, 0)), (-13.4, 8.0, (1, 0))):
    chair(x, y, f, arm=True)
add((-9.9, 7.1, FL + 0.70), (-9.0, 8.0, FL + 0.75), K_TABLE)              # round-ish centre table
add((-9.55, 7.45, FL), (-9.35, 7.65, FL + 0.70), K_TABLE)
add((-12.2, BACK_Y - 0.65, FL), (-10.7, BACK_Y, FL + 1.32), K_PIANO)      # upright piano
for x0, x1, z0, z1 in ((-13.6, -12.7, 2.6, 3.4), (-7.6, -6.4, 2.5, 3.3), (-5.6, -5.0, 2.6, 3.2)):
    add((x0, BACK_Y - 0.04, z0), (x1, BACK_Y, z1), K_PICTURE)
# dining room (south)
for x in (6.3, 9.3, 12.3):
    for y in (5.4, 8.4):
        add((x - 0.5, y - 0.5, FL + 0.50), (x + 0.5, y + 0.5, FL + 0.77), K_CLOTH)   # cloth hangs down
        add((x - 0.08, y - 0.08, FL), (x + 0.08, y + 0.08, FL + 0.5), K_TABLE)
        for f in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            if rng.random() < 0.8:
                chair(x - f[0] * 0.75, y - f[1] * 0.75, f)
add((6.0, BACK_Y - 0.55, FL), (8.0, BACK_Y, FL + 1.0), K_SIDEBOARD)
for x0, x1 in ((6.4, 7.6),):
    add((x0, BACK_Y - 0.04, FL + 1.9), (x1, BACK_Y, FL + 2.7), K_PICTURE)
# unlit pendant lamps
for x, y in ((0.0, 6.6), (-9.45, 7.5), (7.8, 6.9), (10.8, 6.9)):
    add((x - 0.22, y - 0.22, CEIL - 0.95), (x + 0.22, y + 0.22, CEIL - 0.75), K_LAMP)
    add((x - 0.012, y - 0.012, CEIL - 0.75), (x + 0.012, y + 0.012, CEIL), K_LAMP)

B_LO = np.array([b[0] for b in boxes])
B_HI = np.array([b[1] for b in boxes])
B_KIND = np.array([b[2] for b in boxes])
B_COL = np.array([b[3] for b in boxes])


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
    N = np.zeros((n, 3))
    N[np.arange(n), axis] = -np.sign(D[np.arange(n), axis])
    P = O + D * best_t[:, None]
    return best_t, P, N, kind, col


def hashf(a, b, seed=0):
    v = np.sin(a * 12.9898 + b * 78.233 + seed * 37.719) * 43758.5453
    return v - np.floor(v)


WOOD = lin((74, 52, 34))
DARK_WOOD = lin((42, 30, 21))
PAPER = {"n": lin((104, 110, 86)), "c": lin((120, 100, 76)), "s": lin((118, 76, 66))}


def room_of(x):
    return np.where(x < -PART_X, 0, np.where(x > PART_X, 2, 1))


def albedo(P, N, kind):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    A = np.zeros_like(P)
    room = kind == -1
    rm = room_of(x)
    floor = room & (N[:, 2] > 0.5)
    boards = 0.8 + 0.25 * hashf(np.floor(x / 0.1), 0.0, 1)
    A[floor] = lin((78, 58, 40)) * boards[floor, None]
    carpet = floor & (rm != 1) & (np.abs(y - 7.3) < 2.6)
    A[carpet] = lin((92, 52, 44)) * (0.85 + 0.15 * hashf(np.floor(x / 0.3), np.floor(y / 0.3), 2))[carpet, None]
    ceil = room & (N[:, 2] < -0.5)
    A[ceil] = lin((150, 142, 122))
    walls = room & (np.abs(N[:, 2]) < 0.5)
    paper = np.where(rm[:, None] == 0, PAPER["n"], np.where(rm[:, None] == 2, PAPER["s"], PAPER["c"]))
    along = np.where(np.abs(N[:, 0]) > 0.5, y, x)
    stripe = 0.92 + 0.08 * (np.abs((along / 0.09) % 1 - 0.5) < 0.18)
    A[walls] = (paper * stripe[:, None])[walls]
    A[walls & (z > CEIL - 0.5)] = lin((160, 150, 128))                     # plain frieze
    A[walls & (np.abs(z - (CEIL - 0.52)) < 0.03)] = DARK_WOOD              # picture rail
    wain = walls & (z < FL + 1.0)
    pan = (np.abs(((along) / 0.7) % 1 - 0.5) > 0.44) | (z > FL + 0.92) | (z < FL + 0.15)
    A[wain] = WOOD * 0.8
    A[wain & pan] = DARK_WOOD
    # partitions: same finish as the room they face
    m = kind == K_PART
    pr = room_of(x - N[:, 0] * 0.2)
    pp = np.where(pr[:, None] == 0, PAPER["n"], np.where(pr[:, None] == 2, PAPER["s"], PAPER["c"]))
    A[m] = pp[m]
    A[m & (z < FL + 1.0)] = WOOD * 0.8
    A[m & (z > CEIL - 0.5)] = lin((160, 150, 128))
    A[m & (np.abs(N[:, 1]) > 0.5)] = DARK_WOOD                             # door casing edges
    A[kind == K_DOORWAY] = lin((14, 11, 9))
    # counter: dark panelled front, worn top
    m = kind == K_COUNTER
    A[m] = DARK_WOOD
    A[m & (N[:, 2] > 0.5)] = WOOD * 1.25
    pan = m & (np.abs(N[:, 1]) > 0.5) & ((np.abs((x / 0.6) % 1 - 0.5) > 0.42) | (z > FL + 0.98) | (z < FL + 0.18))
    A[pan] = DARK_WOOD * 0.65
    # key rack: grid of empty pigeonholes
    m = kind == K_RACK
    hole = (np.abs((x / 0.15) % 1 - 0.5) < 0.38) & (np.abs(((z - FL) / 0.14) % 1 - 0.5) < 0.36)
    A[m] = WOOD
    A[m & hole & (N[:, 1] < -0.5)] = lin((20, 15, 11))
    A[(kind == K_CHAIR)] = lin((58, 38, 26))
    A[(kind == K_ARMCHAIR)] = lin((88, 58, 50)) * (0.9 + 0.1 * (N[:, 2] > 0.5))[:, None][kind == K_ARMCHAIR]
    A[(kind == K_SETTEE)] = lin((60, 44, 32))
    A[kind == K_TABLE] = DARK_WOOD * 1.2
    A[kind == K_CLOTH] = lin((150, 146, 132))
    A[kind == K_PIANO] = lin((30, 20, 15))
    A[(kind == K_PIANO) & (N[:, 2] > 0.5)] = lin((44, 30, 22))
    m = kind == K_PICTURE                                                 # gilt frame, dim painting
    A[m] = lin((110, 90, 56))
    lo, hi = B_LO[B_KIND == K_PICTURE], B_HI[B_KIND == K_PICTURE]
    for a, b in zip(lo, hi):
        inner = m & (x > a[0] + 0.07) & (x < b[0] - 0.07) & (z > a[2] + 0.07) & (z < b[2] - 0.07)
        A[inner] = lin((62, 64, 50)) * (0.85 + 0.3 * hashf(np.floor(x / 0.08), np.floor(z / 0.08), 5))[inner, None]
    A[kind == K_SIDEBOARD] = DARK_WOOD * 1.1
    A[kind == K_LAMP] = lin((52, 48, 40))
    return A


def shade(P, N, kind):
    """Daylight only through the front windows (shaded by the veranda): falls off into the
    rooms; faces turned to the front get the most. The end rooms get a little from their side
    windows."""
    x, y = P[:, 0], P[:, 1]
    d = np.maximum(y - (FRONT + WALL), 0)
    front = 1.0 * np.exp(-d / 2.8) + 0.18 * np.exp(-d / 9.0)
    facing = 0.55 + 0.45 * np.maximum(0, -N[:, 1]) + 0.25 * np.maximum(0, N[:, 2]) - 0.30 * np.maximum(0, -N[:, 2])
    side = 0.22 * (np.exp(-(x + IX) / 2.5) + np.exp(-(IX - x) / 2.5)) * (0.6 + 0.4 * np.maximum(0, np.abs(N[:, 0])))
    return front * facing + side + 0.02


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


def reveal(h, w, fan=False):
    """Soft shadow of the window reveal and arched head (darker at the top and sides)."""
    yy, xx = np.mgrid[0:h, 0:w]
    ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
    if fan:
        return 0.55 + 0.35 * ss(yy / (h * 0.6))
    ft = 0.55 + 0.45 * ss(yy / (h * 0.3))
    fs = 0.72 + 0.28 * ss(np.minimum(xx, w - 1 - xx) / (w * 0.2))
    fb = 0.9 + 0.1 * ss((h - 1 - yy) / (h * 0.1))
    return ft * fs * fb


DRAPES = {0: lin((74, 78, 56)), 2: lin((86, 44, 38))}      # parlour olive, dining maroon (room index)


def drapes(img, name, room):
    """Heavy curtains tied back at both sides of a parlour / dining-room window (they hang in
    the window plane, so they are drawn flat and sharp over the traced room)."""
    if name.startswith("fan") or room not in DRAPES:
        return img
    h, w = img.shape[:2]
    v = (np.arange(h) + 0.5) / h                              # 0 at the top
    tie = 0.58
    frac = np.where(v < tie, 0.20 - 0.11 * (v / tie) ** 1.5, 0.09 + 0.07 * ((v - tie) / (1 - tie)) ** 0.7)
    x = (np.arange(w) + 0.5) / w
    out = img.copy()
    col = to_srgb(DRAPES[room] * 0.55 * EXPOSURE * 1.6)
    for side in (0, 1):
        d = x if side == 0 else 1 - x                         # distance from the cell edge
        t = d[None, :] / frac[:, None]                         # 0 at the edge, 1 at the curtain's inner edge
        inside = t < 1
        fold = 0.72 + 0.28 * np.sin(t * math.pi * 3.2 + side) ** 2
        edge = 1 - 0.25 * np.clip((t - 0.8) / 0.2, 0, 1)       # the inner edge turns away, darker
        c = col[None, None, :] * (fold * edge)[..., None]
        out = np.where(inside[..., None], c, out)
    return out


def render_cell(name):
    (px, py, pw, ph), origin, length, z0, z1, eye = CELLS[name]
    Wd, H = pw * SS, ph * SS
    u = (np.arange(Wd) + 0.5) / Wd
    v = 1 - (np.arange(H) + 0.5) / H                         # row 0 = top = z1
    uu, vv = np.meshgrid(u, v)
    P0 = np.stack([origin[0] + length * uu, np.full_like(uu, origin[1]), z0 + (z1 - z0) * vv], axis=-1).reshape(-1, 3)
    E = np.array(eye, float)
    D = P0 - E
    D /= np.linalg.norm(D, axis=1, keepdims=True)
    t, P, N, kind, _ = trace(P0, D)
    C = albedo(P, N, kind) * shade(P, N, kind)[:, None] * EXPOSURE
    img = to_srgb(C).reshape(H, Wd, 3)
    dist = t.reshape(H, Wd)
    img = img.reshape(ph, SS, pw, SS, 3).mean(axis=(1, 3))
    dist = dist.reshape(ph, SS, pw, SS).mean(axis=(1, 3))
    near, far = blur(img, 0.6), blur(img, 1.8)
    m = np.clip((dist - 0.8) / 5.0, 0, 1)[..., None]
    img = near * (1 - m) + far * m
    img = blur(drapes(img, name, int(room_of(np.array([origin[0] + length / 2]))[0])), 0.5)
    img = img * reveal(ph, pw, name.startswith("fan"))[..., None]
    nrng = np.random.default_rng(zlib.crc32(name.encode()))
    img = img + nrng.normal(0, 0.006, img.shape)
    return np.clip(img, 0, 1)


def main():
    atlas = np.full((SIZE, SIZE, 3), 0.06)
    cells = {}
    for name, c in CELLS.items():
        x, y, w, h = c[0]
        atlas[y:y + h, x:x + w] = render_cell(name)
        cells[name] = {"px": [x, y, w, h], "uv": [x / SIZE, 1 - (y + h) / SIZE, (x + w) / SIZE, 1 - y / SIZE]}
    import bpy
    img = bpy.data.images.get("HL_HotelLobby") or bpy.data.images.new("HL_HotelLobby", SIZE, SIZE)
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
                   "Blender/glTF-before-flip convention (v = 0 at the bottom). Cells match the Union "
                   "Hotel's ground-floor windows (lobby_<bay>) and door fanlights (fan_<bay>) in "
                   "tools/blender/union_hotel.py; the cell spans the opening's bounding box.",
                   "cells": cells}, f, indent=1)
    print("wrote", OUT + ".jpg", "with", len(cells), "cells,", len(boxes), "boxes")


main()
