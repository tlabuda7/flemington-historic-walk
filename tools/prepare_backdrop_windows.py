"""
prepare_backdrop_windows.py - the shared 1K "backdrop" sheet for the side-street GLBs
(PLAN.md, "Side streets, backdrop buildings", section 3): cheap opaque windows, doors, a
picket-fence strip and a few plain paint swatches, all on one 1024 x 1024 JPEG so a whole
side-street GLB stays one texture layer for its openings.

    python tools/prepare_backdrop_windows.py

Made only from the project's own `shared/window_backs.jpg` (the room-behind-the-glass cells)
plus painted sash frames, a faint sky tint on the upper pane, and drawn doors. Writes
assets/textures/shared/backdrop_windows.jpg and backdrop_windows.json (cell -> uv rectangle,
Blender convention, v = 0 at the bottom).

Layout (px, row 0 at the top):
  y   0-256  8 sash windows, cream frames     (win_cream_0 ... 7)
  y 256-512  8 sash windows, dark green frames (win_green_0 ... 7)
  y 512-768  door_cream (0-128), door_green (128-256), engine_doors (256-512),
             barn_doors (512-768), attic window (768-896, top half), small_window (bottom half),
             swatches 896-1024: paint_white, iron_dark, stone_cream, paint_green (64 px each)
  y 768-896  picket fence strip, full width (tiles in U: 1024 px = 2.0 m of fence)
  y 896-1024 swatches, 256 px each: white, weathered wood, dark tin, cream paint
"""
import json
import os
import random
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "textures", "shared", "window_backs.jpg")
OUT = os.path.join(ROOT, "assets", "textures", "shared", "backdrop_windows.jpg")
OUT_JSON = os.path.join(ROOT, "assets", "textures", "shared", "backdrop_windows.json")
S = 1024

back = Image.open(SRC).convert("RGB")
img = Image.new("RGB", (S, S), (60, 56, 50))
d = ImageDraw.Draw(img)
cells = {}
random.seed(3)


def uv(x, y, w, h, inset=2):
    return [(x + inset) / S, 1 - (y + h - inset) / S, (x + w - inset) / S, 1 - (y + inset) / S]


# interiors taken from window_backs.jpg (128 x 320 cells, rows at y 0 and 320)
INTERIORS = [(0, 0), (128, 0), (512, 0), (768, 0), (512, 320), (640, 320), (256, 0), (896, 320)]


def sash_window(x0, y0, frame, interior, w=128, h=256):
    fw, mr, mu = 11, 7, 4                  # frame, meeting rail, muntin (px; 142 px per m)
    ix, iy = INTERIORS[interior]
    pane = back.crop((ix, iy, ix + 128, iy + 320)).resize((w - 2 * fw, h - 2 * fw), Image.LANCZOS)
    # faint sky reflection on the upper half, fading downward
    sky = Image.new("RGB", pane.size, (150, 165, 185))
    mask = Image.linear_gradient("L").resize(pane.size).transpose(Image.FLIP_TOP_BOTTOM)
    mask = mask.point(lambda v: int(v * 0.22))
    pane = Image.composite(sky, pane, mask)
    img.paste(pane, (x0 + fw, y0 + fw))
    d.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], outline=frame, width=fw)
    mid = y0 + h // 2
    d.rectangle([x0, mid - mr // 2, x0 + w - 1, mid + mr // 2], fill=frame)        # meeting rail
    cx = x0 + w // 2
    d.rectangle([cx - mu // 2, y0, cx + mu // 2, y0 + h - 1], fill=frame)           # 2/2 muntin
    # sill shadow line and a darker outer reveal edge
    shade = tuple(int(c * 0.55) for c in frame)
    d.rectangle([x0, y0 + h - 4, x0 + w - 1, y0 + h - 1], fill=shade)
    d.rectangle([x0, y0, x0 + w - 1, y0 + 2], fill=shade)


CREAM, GREEN = (226, 218, 198), (48, 66, 52)
for i in range(8):
    sash_window(i * 128, 0, CREAM, i)
    cells["win_cream_%d" % i] = uv(i * 128, 0, 128, 256)
    sash_window(i * 128, 256, GREEN, (i + 3) % 8)
    cells["win_green_%d" % i] = uv(i * 128, 256, 128, 256)


def panel_door(x0, y0, w, h, colour, glass_top=True):
    dark = tuple(int(c * 0.62) for c in colour)
    light = tuple(min(255, int(c * 1.18)) for c in colour)
    d.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], fill=(222, 214, 194))           # frame / casing
    tx0, ty0 = x0 + 10, y0 + 10
    # transom light
    tr_h = int(h * 0.14)
    pane = back.crop((640, 320, 768, 640)).resize((w - 20, tr_h - 6))
    img.paste(pane, (tx0, ty0))
    ly0 = ty0 + tr_h
    d.rectangle([tx0, ly0, x0 + w - 11, y0 + h - 1], fill=colour)
    lw = w - 20
    # leaf: upper glass (or panel), two lower panels
    if glass_top:
        g = back.crop((128, 320, 256, 640)).resize((lw - 28, int(h * 0.26)))
        img.paste(g, (tx0 + 14, ly0 + 14))
    else:
        d.rectangle([tx0 + 14, ly0 + 14, tx0 + lw - 14, ly0 + 14 + int(h * 0.26)], outline=dark, width=4)
    py = ly0 + 28 + int(h * 0.26)
    ph = (y0 + h - 14 - py) // 2 - 6
    for k in range(2):
        yy = py + k * (ph + 10)
        d.rectangle([tx0 + 14, yy, tx0 + lw - 14, yy + ph], outline=dark, width=4)
        d.line([tx0 + 16, yy + ph - 2, tx0 + lw - 16, yy + ph - 2], fill=light, width=2)
    d.ellipse([tx0 + lw - 16, ly0 + h * 0.45, tx0 + lw - 9, ly0 + h * 0.45 + 7], fill=(150, 130, 80))


panel_door(0, 512, 128, 256, (92, 62, 40))          # varnished brown door, light over
cells["door_brown"] = uv(0, 512, 128, 256)
panel_door(128, 512, 128, 256, (52, 72, 56), glass_top=False)
cells["door_green"] = uv(128, 512, 128, 256)


def double_doors(x0, y0, w, h, colour, kind):
    dark = tuple(int(c * 0.6) for c in colour)
    light = tuple(min(255, int(c * 1.2)) for c in colour)
    d.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], fill=(200, 190, 170))
    fx0, fy0, fx1, fy1 = x0 + 8, y0 + 8, x0 + w - 9, y0 + h - 1
    d.rectangle([fx0, fy0, fx1, fy1], fill=colour)
    mid = (fx0 + fx1) // 2
    if kind == "engine":
        # two leaves, each: a row of 3 small lights on top, 2 x 3 raised panels below
        for lx0, lx1 in ((fx0, mid - 2), (mid + 2, fx1)):
            lw = lx1 - lx0
            for k in range(3):
                gx = lx0 + 8 + k * (lw - 16) // 3
                g = back.crop((640, 320, 768, 640)).resize(((lw - 16) // 3 - 6, 40))
                img.paste(g, (gx + 3, fy0 + 10))
            for r in range(3):
                for c in range(2):
                    px0 = lx0 + 10 + c * (lw - 20) // 2
                    py0 = fy0 + 62 + r * 60
                    d.rectangle([px0, py0, px0 + (lw - 20) // 2 - 8, py0 + 50], outline=dark, width=4)
                    d.line([px0 + 2, py0 + 48, px0 + (lw - 20) // 2 - 10, py0 + 48], fill=light, width=2)
        d.line([mid, fy0, mid, fy1], fill=dark, width=4)
    else:
        # vertical boards with a Z brace on each leaf
        for xx in range(fx0, fx1, 14):
            d.line([xx, fy0, xx, fy1], fill=dark, width=2)
        for lx0, lx1 in ((fx0, mid), (mid, fx1)):
            for yy in (fy0 + 20, fy1 - 30):
                d.rectangle([lx0 + 6, yy, lx1 - 6, yy + 12], fill=light)
            d.line([lx0 + 10, fy1 - 24, lx1 - 10, fy0 + 32], fill=light, width=10)
        d.line([mid, fy0, mid, fy1], fill=(30, 26, 22), width=5)
    # a little random weathering
    for _ in range(400):
        px, py = random.randint(fx0, fx1), random.randint(fy0, fy1)
        c = img.getpixel((px, py))
        img.putpixel((px, py), tuple(max(0, v - 18) for v in c))


double_doors(256, 512, 256, 256, (118, 46, 36), "engine")     # dark red engine-house doors
cells["engine_doors"] = uv(256, 512, 256, 256)
double_doors(512, 512, 256, 256, (128, 112, 92), "barn")      # weathered plank wagon doors
cells["barn_doors"] = uv(512, 512, 256, 256)

# small windows: attic (4 lights, square) and a low 2-light window
for (y0, name, cols, rows) in ((512, "attic_window", 2, 2), (640, "small_window", 2, 1)):
    x0, w, h = 768, 128, 128
    pane = back.crop((640, 0, 768, 320)).resize((w - 22, h - 22))
    img.paste(pane, (x0 + 11, y0 + 11))
    d.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], outline=CREAM, width=11)
    for c in range(1, cols):
        xx = x0 + c * w // cols
        d.rectangle([xx - 3, y0, xx + 3, y0 + h - 1], fill=CREAM)
    for r in range(1, rows):
        yy = y0 + r * h // rows
        d.rectangle([x0, yy - 3, x0 + w - 1, yy + 3], fill=CREAM)
    cells[name] = uv(x0, y0, w, h)


def swatch(name, x0, y0, w, h, rgb, noise=6):
    for yy in range(y0, y0 + h):
        for xx in range(x0, x0 + w):
            n = random.randint(-noise, noise)
            img.putpixel((xx, yy), tuple(max(0, min(255, c + n)) for c in rgb))
    cells[name] = uv(x0, y0, w, h, inset=6)


swatch("paint_white_s", 896, 512, 128, 64, (232, 228, 216))
swatch("iron_dark", 896, 576, 128, 64, (44, 42, 40))
swatch("stone_cream", 896, 640, 128, 64, (205, 196, 176))
swatch("paint_green_s", 896, 704, 128, 64, (52, 70, 54))

# picket fence strip: 1024 px = 2.0 m of fence, 128 px = the full fence height
y0, H = 768, 128
bg = Image.new("RGB", (S, H), (58, 70, 42))
gd = ImageDraw.Draw(bg)
for yy in range(H):                                      # garden behind: darker near the ground
    t = yy / H
    gd.line([0, yy, S, yy], fill=(int(70 - 22 * t), int(82 - 26 * t), int(50 - 16 * t)))
for _ in range(2500):
    px, py = random.randint(0, S - 1), random.randint(0, H - 1)
    gd.point((px, py), fill=(40 + random.randint(0, 40), 55 + random.randint(0, 40), 30 + random.randint(0, 20)))
bg = bg.filter(ImageFilter.GaussianBlur(1.2))
img.paste(bg, (0, y0))
d.rectangle([0, y0 + 30, S - 1, y0 + 38], fill=(96, 92, 80))      # rails behind the pickets
d.rectangle([0, y0 + 94, S - 1, y0 + 102], fill=(96, 92, 80))
pitch, pw = 73, 40                                       # 14 pickets per 2 m (0.14 m), 0.08 m wide
for k in range(14):
    x = k * pitch + 16
    top = y0 + 10
    d.polygon([(x, top + 12), (x + pw // 2, top), (x + pw, top + 12), (x + pw, y0 + H - 6), (x, y0 + H - 6)],
              fill=(228, 224, 210))
    d.line([x + pw - 3, top + 12, x + pw - 3, y0 + H - 6], fill=(170, 166, 152), width=3)    # shaded edge
d.rectangle([0, y0 + H - 6, S - 1, y0 + H - 1], fill=(48, 44, 36))                         # ground line
cells["pickets"] = [0.0, 1 - (y0 + H - 2) / S, 1.0, 1 - (y0 + 2) / S]

swatch("paint_white", 0, 896, 256, 128, (234, 230, 220), 5)
swatch("wood_grey", 256, 896, 256, 128, (120, 110, 96), 12)
swatch("tin_dark", 512, 896, 256, 128, (70, 72, 76), 6)
swatch("paint_cream", 768, 896, 256, 128, (214, 202, 172), 5)

img.save(OUT, quality=90)
with open(OUT_JSON, "w") as f:
    json.dump({"size": S, "note": "uv = [u0, v0, u1, v1], Blender convention (v = 0 at the bottom); "
               "'pickets' spans the full width and tiles in U (1 repeat = 2.0 m)", "cells": cells}, f, indent=1)
print("wrote", OUT, len(cells), "cells")


# ---------------------------------------------------------------------------------------------
# backdrop_grass.jpg: a seamless 1K lawn map (tile 4 m) for the side-street yards and the park.
# Made from tiled multi-octave value noise (no download): mottled green with worn, browner patches
# and fine blade speckle. The concrete map was tried first and showed its slab joints as a grid.
# ---------------------------------------------------------------------------------------------
from PIL import ImageChops

GRASS_OUT = os.path.join(ROOT, "assets", "textures", "shared", "backdrop_grass.jpg")


def seamless_noise(cells, seed):
    r = random.Random(seed)
    small = Image.new("L", (cells, cells))
    small.putdata([r.randint(0, 255) for _ in range(cells * cells)])
    tiled = Image.new("L", (cells * 3, cells * 3))
    for i in range(3):
        for j in range(3):
            tiled.paste(small, (i * cells, j * cells))
    big = tiled.resize((S * 3, S * 3), Image.BICUBIC)
    return big.crop((S, S, 2 * S, 2 * S))


octaves = [(4, 0.30), (8, 0.25), (32, 0.20), (128, 0.15), (512, 0.10)]
acc = None
for k, (cells, wgt) in enumerate(octaves):
    n = seamless_noise(cells, 100 + k).point(lambda v, w=wgt: int(v * w))
    acc = n if acc is None else ImageChops.add(acc, n)
lo, hi = acc.getextrema()
acc = acc.point(lambda v: int(255 * (v - lo) / max(1, hi - lo)))
wear = seamless_noise(6, 7)
dark, light, worn = (68, 92, 40), (118, 140, 66), (122, 112, 74)
base = Image.composite(Image.new("RGB", (S, S), light), Image.new("RGB", (S, S), dark), acc)
wear_mask = wear.point(lambda v: max(0, min(255, (v - 150) * 4)) // 2)
base = Image.composite(Image.new("RGB", (S, S), worn), base, wear_mask)
speck = seamless_noise(1024, 9).point(lambda v: 255 if v > 200 else 0).filter(ImageFilter.GaussianBlur(0.6))
base = Image.composite(Image.new("RGB", (S, S), (138, 156, 84)), base, speck.point(lambda v: v // 3))
base.save(GRASS_OUT, quality=88)
print("wrote", GRASS_OUT)
