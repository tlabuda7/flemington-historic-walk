"""
prepare_window_backs.py - draws the shared "window backs" atlas: what you see behind the
glass of a c. 1920 Main Street window (own work, Pillow only, no download, no lettering).

    python tools/prepare_window_backs.py

Writes
    assets/textures/shared/window_backs.jpg    1024 x 1024, sRGB, JPEG quality 88
    assets/textures/shared/window_backs.json   cell layout (pixel rects, row 0 = top) +
                                               Blender UV rects (v = 0 at the bottom)

Layout
    rows y 0-319 and 320-639: 16 upper-floor cells, 128 x 320 (aspect 1 : 2.5)
        roller blinds (cream / dark green linen) at different heights, lace curtains,
        plain curtain pairs, dark rooms with a faint back wall and door frame
    row y 640-991: "shop_a", "shop_b" 384 x 352 (dim dry-goods interior: shelves of cloth
        bolts and boxes, counter, a low window display), "door" and "return" 128 x 352
        (narrow interior views for door glass and the entrance's glass returns)
    strip y 992-1023: "transom" 1024 x 32 (dim shop ceiling)

Everything is subtle and soft (2x supersampled, gentle light falloff, fabric grain), since
it sits behind dark-tinted glass and is multiplied by the building's baked lightmap.
v2 (owner, 2026-11-10: "slightly unrealistic"): every cell is darkened to DARKEN and gets a
soft reveal shadow (darker at the head and the sides, as if the reveal blocks the light),
and the blinds and curtains use muted c. 1920 tones. Shop display windows that need sharper
content use the dedicated `shop_interior.jpg` (tools/prepare_shop_interior.py) instead.
"""

import json
import math
import os
import random
import zlib

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets", "textures", "shared")
SIZE = 1024
SS = 2                         # supersampling


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def smooth_noise(w, h, cell, rng, lo=0.0, hi=1.0):
    """Value noise: random grey at (w/cell x h/cell), upscaled bicubic -> 'L' image."""
    sw, sh = max(2, int(w / cell) + 2), max(2, int(h / cell) + 2)
    small = Image.new("L", (sw, sh))
    small.putdata([int(255 * (lo + (hi - lo) * rng.random())) for _ in range(sw * sh)])
    return small.resize((w, h), Image.BICUBIC)


def grain(w, h, rng, amount):
    """Fine luminance grain 'L' centred on 128."""
    a = Image.frombytes("L", (w, h), rng.randbytes(w * h))
    b = Image.frombytes("L", (w, h), rng.randbytes(w * h))
    g = Image.blend(a, b, 0.5)                    # triangular, centred on ~128
    return g.point(lambda v: max(0, min(255, int(128 + (v - 128) * amount / 40))))


def mul_l(img, l_img):
    """img x (L / 255)."""
    return ImageChops.multiply(img, Image.merge("RGB", (l_img, l_img, l_img)))


def apply_grain(img, rng, amount=10):
    g = grain(img.width, img.height, rng, amount)
    # around 1.0: (g - 128) / 255 added in multiply space
    lut = [max(0, min(255, int(232 + (v - 128) * 0.25))) for v in range(256)]
    g = g.point(lut)
    out = mul_l(img, g)
    return out.point(lambda v: min(255, int(v * 255 / 232)))


def field(w, h, fn):
    """'L' image from a per-pixel function fn(x, y) -> 0..1."""
    data = bytearray(w * h)
    i = 0
    for y in range(h):
        for x in range(w):
            v = fn(x, y)
            data[i] = 0 if v <= 0 else (255 if v >= 1 else int(v * 255))
            i += 1
    return Image.frombytes("L", (w, h), bytes(data))


def vgrad(w, h, top, bottom):
    """'L' vertical gradient top -> bottom (0..1 factors)."""
    col = Image.new("L", (1, h))
    col.putdata([int(255 * (top + (bottom - top) * y / max(1, h - 1))) for y in range(h)])
    return col.resize((w, h))


def hgrad_edges(w, h, edge, centre):
    """'L' horizontal falloff: `edge` at both sides, `centre` in the middle (cosine)."""
    row = Image.new("L", (w, 1))
    row.putdata([int(255 * (edge + (centre - edge) * math.sin(math.pi * (x + 0.5) / w) ** 0.6)) for x in range(w)])
    return row.resize((w, h))


def shade(rgb, f):
    return tuple(max(0, min(255, int(c * f))) for c in rgb)


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

def dark_room(w, h, rng, door=True, tone=1.0):
    """Unlit room seen from outside: very dark warm brown, a faint back wall (lighter
    wallpaper area with a picture rail), a faint door frame, floor glow near the window."""
    base = shade((24, 20, 17), tone)
    img = Image.new("RGB", (w, h), base)
    d = ImageDraw.Draw(img)
    wall = shade((40, 34, 29), tone)
    x0, x1 = int(w * rng.uniform(0.05, 0.15)), int(w * rng.uniform(0.85, 0.95))
    d.rectangle([x0, int(h * 0.08), x1, int(h * 0.80)], fill=wall)
    d.rectangle([x0, int(h * 0.17), x1, int(h * 0.175)], fill=shade(wall, 1.2))          # picture rail
    d.rectangle([x0, int(h * 0.62), x1, int(h * 0.80)], fill=shade(wall, 0.8))           # wainscot
    if door:
        dx = int(w * rng.uniform(0.25, 0.55))
        dw = int(w * 0.32)
        d.rectangle([dx, int(h * 0.30), dx + dw, int(h * 0.80)], fill=shade(base, 0.9))  # doorway
        d.rectangle([dx - 3 * SS, int(h * 0.29), dx + dw + 3 * SS, int(h * 0.30)], fill=shade(wall, 1.25))
        d.rectangle([dx - 3 * SS, int(h * 0.29), dx, int(h * 0.80)], fill=shade(wall, 1.15))
        d.rectangle([dx + dw, int(h * 0.29), dx + dw + 3 * SS, int(h * 0.80)], fill=shade(wall, 1.15))
    else:
        # a picture frame on the back wall
        px, py = int(w * rng.uniform(0.3, 0.5)), int(h * 0.27)
        d.rectangle([px, py, px + int(w * 0.28), py + int(h * 0.12)], outline=shade(wall, 1.3), width=2 * SS)
    d.rectangle([0, int(h * 0.80), w, h], fill=shade((34, 27, 21), tone))                # floor
    img = img.filter(ImageFilter.GaussianBlur(3 * SS))                                   # out of focus
    # light falls off away from the window: brighter low and in the middle
    img = mul_l(img, vgrad(w, h, 0.70, 1.0))
    img = mul_l(img, hgrad_edges(w, h, 0.72, 1.0))
    return img


def linen(w, h, colour, rng):
    """Roller-blind linen: slubby horizontal threads, fine grain, soft side shading."""
    img = Image.new("RGB", (w, h), colour)
    slub = smooth_noise(max(2, w // 24), h, 1.5, rng, 0.90, 1.0).resize((w, h), Image.BICUBIC)
    img = mul_l(img, slub)
    blot = smooth_noise(w, h, w / 2.5, rng, 0.93, 1.0)
    img = mul_l(img, blot)
    img = mul_l(img, hgrad_edges(w, h, 0.84, 1.0))
    return img


def blind_over(room, colour, drop, rng, sun=1.0):
    """Roller blind pulled down to `drop` (0..1 of the height) over the room."""
    w, h = room.size
    yb = int(h * drop)
    out = room.copy()
    # soft shadow of the blind's hem on the room just below it
    sh = Image.new("L", (w, h), 255)
    ImageDraw.Draw(sh).rectangle([0, yb, w, yb + int(h * 0.05)], fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(4 * SS))
    out = mul_l(out, sh)
    cloth = linen(w, yb, shade(colour, sun), rng)
    cloth = mul_l(cloth, vgrad(w, yb, 1.0, 0.93))           # the roll at the top glows a little more
    out.paste(cloth, (0, 0))
    d = ImageDraw.Draw(out)
    slat = int(max(4 * SS, h * 0.018))
    d.rectangle([0, yb - slat, w, yb], fill=shade(colour, 0.72 * sun))           # hem with its wooden slat
    d.line([0, yb - slat, w, yb - slat], fill=shade(colour, 1.05 * sun), width=SS)
    cx, r = w // 2, int(w * 0.03)
    d.line([cx, yb, cx, yb + 3 * r], fill=shade(colour, 0.6 * sun), width=SS)   # cord
    d.ellipse([cx - r, yb + 3 * r, cx + r, yb + 5 * r], outline=shade((200, 190, 160), 0.7), width=SS)  # pull ring
    return out


def lace_over(room, rng, top=0.0, density=1.0):
    """Lace panel from `top` to the bottom: net mesh + rosette motifs + scalloped border,
    gentle vertical folds, room faintly showing through."""
    w, h = room.size
    y0 = int(h * top)
    lh = h - y0
    ph = rng.uniform(0, 6.28)
    fold_w = w / rng.uniform(2.6, 3.4)
    a = 2 * math.pi / (7 * SS)           # rosette period
    m = 2 * math.pi / (3 * SS)           # net period

    def alpha(x, y):
        yy = y
        fold = 0.5 + 0.5 * math.sin(2 * math.pi * x / fold_w + ph)
        xs = x + 3 * SS * math.sin(2 * math.pi * x / fold_w + ph)       # pattern follows the folds
        net = 0.5 + 0.5 * math.sin(xs * m) * math.sin(yy * m)
        ros = math.sin(xs * a) * math.sin((yy + (xs // (7 * SS)) * 3.5 * SS) * a) + 0.25 * math.sin(xs * a * 0.31) * math.cos(yy * a * 0.23)
        motif = 1.0 if ros > 0.75 else (0.0 if ros < 0.45 else (ros - 0.45) / 0.3)
        border = 1.0 if (lh - yy) < h * 0.07 and math.sin(xs * a * 1.2) > -0.3 else 0.0
        if (lh - yy) < h * 0.07 * (0.55 + 0.45 * abs(math.sin(xs * a * 0.6))) and (lh - yy) > h * 0.012:
            border = 1.0
        elif (lh - yy) <= h * 0.012 or (lh - yy) >= h * 0.07:
            border = 0.0
        v = (0.52 + 0.10 * net + 0.24 * motif) * density
        v = max(v, border * 0.85)
        return v * (0.82 + 0.18 * fold)

    al = field(w, lh, alpha).filter(ImageFilter.GaussianBlur(0.9 * SS))
    fold_l = field(w, lh, lambda x, y: 0.80 + 0.20 * (0.5 + 0.5 * math.sin(2 * math.pi * x / fold_w + ph + 0.8)))
    lace_col = mul_l(Image.new("RGB", (w, lh), LACE), fold_l)
    lace_col = mul_l(lace_col, vgrad(w, lh, 0.95, 0.85))
    out = room.copy()
    region = out.crop((0, y0, w, h))
    out.paste(Image.composite(lace_col, region, al), (0, y0))
    return out


def curtains_over(room, colour, gap, rng):
    """Plain curtain pair hanging straight, a `gap` (0..1 of the width) open in the middle."""
    w, h = room.size
    pw = int(w * (1 - gap) / 2)
    out = room.copy()
    # shadow cast by the panels' inner edges onto the room
    sh = Image.new("L", (w, h), 255)
    dd = ImageDraw.Draw(sh)
    dd.rectangle([pw, 0, pw + int(w * 0.06), h], fill=160)
    dd.rectangle([w - pw - int(w * 0.06), 0, w - pw, h], fill=160)
    out = mul_l(out, sh.filter(ImageFilter.GaussianBlur(3 * SS)))
    for side in (0, 1):
        folds = rng.uniform(2.6, 3.6)
        ph = rng.uniform(0, 6.28)

        def f(x, y, folds=folds, ph=ph):
            t = 2 * math.pi * folds * x / pw + ph
            v = 0.5 + 0.5 * math.sin(t + 0.3 * math.sin(2 * t))
            return 0.62 + 0.38 * v ** 0.8
        lum = field(pw, h, f)
        cloth = mul_l(linen(pw, h, colour, rng), lum)
        cloth = mul_l(cloth, vgrad(pw, h, 0.92, 1.0))
        # a darker hem band at the bottom
        ImageDraw.Draw(cloth).rectangle([0, h - int(h * 0.025), pw, h], fill=shade(colour, 0.6))
        x0 = 0 if side == 0 else w - pw
        out.paste(cloth if side == 0 else cloth.transpose(Image.FLIP_LEFT_RIGHT), (x0, 0))
    return out


GOODS = [(58, 62, 84), (92, 70, 52), (120, 104, 82), (70, 48, 44), (96, 98, 92), (140, 128, 104),
         (54, 66, 58), (110, 76, 60), (128, 118, 96), (80, 80, 96), (150, 140, 120), (66, 54, 46)]


def shop_interior(w, h, rng, shelves=5, counter=True, display=True):
    """Dim dry-goods shop seen through the window: wall shelving full of cloth bolts and
    boxes at the back, a counter, a low display of folded goods behind the glass; light
    falls off into the room."""
    img = Image.new("RGB", (w, h), (30, 25, 21))
    d = ImageDraw.Draw(img)
    top, bot = int(h * 0.06), int(h * 0.66)
    d.rectangle([0, top, w, bot], fill=(44, 37, 30))                      # shelving back
    sh = (bot - top) / shelves
    for k in range(shelves):
        y1 = int(top + (k + 1) * sh)
        x = rng.randint(0, 4 * SS)
        while x < w:
            r = rng.random()
            if r < 0.10:
                x += rng.randint(4, 10) * SS                               # gap
                continue
            if r < 0.72:                                                   # pile of cloth bolts lying flat
                bw = rng.randint(16, 26) * SS
                n = rng.randint(2, 4)
                bh = int(sh * rng.uniform(0.17, 0.22))
                for j in range(n):
                    c = shade(rng.choice(GOODS), rng.uniform(0.75, 1.05))
                    yb1 = y1 - 2 * SS - j * bh
                    d.rounded_rectangle([x, yb1 - bh + SS, x + bw - 2 * SS, yb1], radius=bh // 2, fill=c)
                    d.line([x + bh // 3, yb1 - bh // 2 - SS, x + bw - 2 * SS - bh // 3, yb1 - bh // 2 - SS],
                           fill=shade(c, 1.22), width=SS)                  # roundness highlight
            else:                                                          # stack of boxes
                bw = rng.randint(14, 22) * SS
                c = shade(rng.choice(((128, 120, 104), (110, 100, 84), (140, 132, 116), (96, 90, 80))),
                          rng.uniform(0.8, 1.0))
                bh = int(sh * rng.uniform(0.25, 0.35))
                for j in range(rng.randint(1, 3)):
                    yb1 = y1 - 2 * SS - j * bh
                    d.rectangle([x, yb1 - bh + SS, x + bw - 2 * SS, yb1], fill=c)
                    d.line([x, yb1 - bh + 3 * SS, x + bw - 2 * SS, yb1 - bh + 3 * SS], fill=shade(c, 0.8), width=SS)  # lid
            x += bw
        d.rectangle([0, y1 - 2 * SS, w, y1 + SS], fill=(92, 74, 54))       # shelf board
    # uprights of the shelving
    for k in range(0, w, max(40 * SS, w // 4)):
        d.rectangle([k, top, k + 3 * SS, bot], fill=(58, 46, 35))
    d.rectangle([0, bot, w, h], fill=(36, 29, 23))                         # floor
    if counter:
        cy0, cy1 = int(h * 0.60), int(h * 0.78)
        cx0, cx1 = int(w * rng.uniform(0.0, 0.15)), int(w * rng.uniform(0.7, 1.0))
        d.rectangle([cx0, cy0, cx1, cy1], fill=(50, 36, 26))               # counter front
        d.rectangle([cx0, cy0 - 2 * SS, cx1, cy0 + SS], fill=(110, 88, 62))  # counter top edge
        for k in range(cx0 + 6 * SS, cx1 - 6 * SS, 26 * SS):               # panels
            d.rectangle([k, cy0 + 6 * SS, k + 20 * SS, cy1 - 6 * SS], outline=(62, 46, 34), width=SS)
    img = img.filter(ImageFilter.GaussianBlur(1.6 * SS))                   # depth of field
    if display:
        # low display platform just behind the glass: folded cloth and a few boxes, sharper
        d = ImageDraw.Draw(img)
        py = int(h * 0.86)
        d.rectangle([0, py, w, h], fill=(70, 56, 42))
        d.line([0, py, w, py], fill=(120, 98, 72), width=SS)
        x = rng.randint(2, 10) * SS
        while x < w - 12 * SS:
            fw = rng.randint(16, 30) * SS
            fh = rng.randint(4, 12) * SS
            c = shade(rng.choice(GOODS), rng.uniform(0.95, 1.25))
            for layer in range(rng.randint(1, 3)):                          # stacked folded cloth
                yy = py - (layer + 1) * fh
                d.rectangle([x, yy, x + fw, yy + fh - SS], fill=c)
                d.line([x, yy, x + fw, yy], fill=shade(c, 1.2), width=SS)
                c = shade(rng.choice(GOODS), rng.uniform(0.95, 1.25))
            x += fw + rng.randint(6, 26) * SS
        img = img.filter(ImageFilter.GaussianBlur(0.6 * SS))
    # light falloff: brightest low near the glass, darker up and to the sides
    img = mul_l(img, vgrad(w, h, 0.62, 1.0))
    img = mul_l(img, hgrad_edges(w, h, 0.70, 1.0))
    return img


def ceiling(w, h, rng):
    """Transom view: a dim plastered shop ceiling, a little lighter toward the glass."""
    img = Image.new("RGB", (w, h), (52, 46, 40))
    img = mul_l(img, smooth_noise(w, h, h * 1.5, rng, 0.85, 1.0))
    img = mul_l(img, vgrad(w, h, 0.7, 1.0))
    d = ImageDraw.Draw(img)
    for k in range(rng.randint(40, 120) * SS, w, rng.randint(250, 330) * SS):   # beams / lamp drops
        d.rectangle([k, 0, k + 6 * SS, h], fill=(34, 29, 24))
    return img.filter(ImageFilter.GaussianBlur(1.5 * SS))


# ---------------------------------------------------------------------------
# Cells
# ---------------------------------------------------------------------------
# muted c. 1920 tones (v2, owner 2026-11-10: "slightly unrealistic"): dull cream, faded dark
# green, browns; nothing saturated
CREAM = (196, 184, 152)
GREEN = (60, 76, 62)
OLIVE = (96, 88, 70)
MAROON = (88, 64, 56)
BEIGE = (176, 165, 142)
LACE = (210, 202, 182)

UPPER = [   # (name, recipe)
    ("blind_cream_high", lambda r: blind_over(dark_room(W, H, r), CREAM, 0.30, r)),
    ("blind_cream_half", lambda r: blind_over(dark_room(W, H, r, door=False), CREAM, 0.52, r)),
    ("blind_cream_low", lambda r: blind_over(dark_room(W, H, r), CREAM, 0.80, r)),
    ("blind_green_high", lambda r: blind_over(dark_room(W, H, r, door=False), GREEN, 0.26, r)),
    ("blind_green_half", lambda r: blind_over(dark_room(W, H, r), GREEN, 0.50, r)),
    ("blind_green_low", lambda r: blind_over(dark_room(W, H, r), GREEN, 0.84, r)),
    ("lace", lambda r: lace_over(dark_room(W, H, r), r)),
    ("lace_blind_cream", lambda r: blind_over(lace_over(dark_room(W, H, r, door=False), r, 0.10), CREAM, 0.22, r)),
    ("curtains_olive", lambda r: curtains_over(dark_room(W, H, r), OLIVE, 0.30, r)),
    ("dark_room", lambda r: dark_room(W, H, r)),
    ("lace_blind_green", lambda r: blind_over(lace_over(dark_room(W, H, r), r, 0.0, 0.9), GREEN, 0.40, r)),
    ("blind_cream_full", lambda r: blind_over(dark_room(W, H, r), CREAM, 0.93, r)),
    ("curtains_beige", lambda r: curtains_over(dark_room(W, H, r, door=False), BEIGE, 0.22, r)),
    ("dark_room_frame", lambda r: dark_room(W, H, r, door=False, tone=1.1)),
    ("lace_full_blind_cream", lambda r: blind_over(lace_over(dark_room(W, H, r), r, 0.0, 1.1), CREAM, 0.15, r)),
    ("curtains_maroon_blind", lambda r: blind_over(curtains_over(dark_room(W, H, r), MAROON, 0.35, r), CREAM, 0.35, r)),
]
W, H = 128 * SS, 320 * SS


DARKEN = 0.64                  # a room behind glass is far darker than daylit brick (v2)


def reveal(w, h, top=0.48, side=0.68, bottom=0.90, top_len=0.32, side_len=0.22):
    """'L' shadow of the window reveal and head: darkest at the top, darker at both sides
    and a little at the sill, full brightness in the lower middle; times DARKEN."""
    def ss(t):
        t = min(1.0, max(0.0, t))
        return t * t * (3 - 2 * t)

    def f(x, y):
        ft = top + (1 - top) * ss(y / (h * top_len))
        fs = side + (1 - side) * ss(min(x, w - 1 - x) / (w * side_len))
        fb = bottom + (1 - bottom) * ss((h - 1 - y) / (h * 0.12))
        return DARKEN * ft * fs * fb
    return field(w, h, f)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    atlas = Image.new("RGB", (SIZE * SS, SIZE * SS), (24, 20, 17))
    cells = {}

    def put(name, img, x, y):
        img = apply_grain(img, random.Random(zlib.crc32(name.encode())), 12)
        if name == "transom":
            img = mul_l(img, reveal(img.width, img.height, top=0.7, side=0.8, bottom=1.0, top_len=0.8, side_len=0.05))
        else:
            img = mul_l(img, reveal(img.width, img.height))
        atlas.paste(img, (x * SS, y * SS))
        w, h = img.width // SS, img.height // SS
        cells[name] = {"px": [x, y, w, h],
                       "uv": [x / SIZE, 1 - (y + h) / SIZE, (x + w) / SIZE, 1 - y / SIZE]}

    for i, (name, recipe) in enumerate(UPPER):
        rng = random.Random(100 + i)
        put(name, recipe(rng), (i % 8) * 128, (i // 8) * 320)
    put("shop_a", shop_interior(384 * SS, 352 * SS, random.Random(7)), 0, 640)
    put("shop_b", shop_interior(384 * SS, 352 * SS, random.Random(8), shelves=4), 384, 640)
    put("door", shop_interior(128 * SS, 352 * SS, random.Random(9), shelves=5, display=False), 768, 640)
    put("return", shop_interior(128 * SS, 352 * SS, random.Random(10), shelves=4, counter=False), 896, 640)
    put("transom", ceiling(1024 * SS, 32 * SS, random.Random(11)), 0, 992)

    atlas = atlas.resize((SIZE, SIZE), Image.LANCZOS)
    path = os.path.join(OUT_DIR, "window_backs.jpg")
    atlas.save(path, quality=88, subsampling=0)
    with open(os.path.join(OUT_DIR, "window_backs.json"), "w") as f:
        json.dump({"size": SIZE, "note": "px = [x, y, w, h], row 0 at the top; uv = [u0, v0, u1, v1], "
                   "Blender/glTF-before-flip convention (v = 0 at the bottom)", "cells": cells}, f, indent=1)
    print("wrote", path, "with", len(cells), "cells")


if __name__ == "__main__":
    main()
