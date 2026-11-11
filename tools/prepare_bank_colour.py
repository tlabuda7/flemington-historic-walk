"""
prepare_bank_colour.py - colour fix for the Bank Building / Flemington National Bank (56-66 Main St).

Usage:  python tools/prepare_bank_colour.py
Output: assets/textures/bank-building/{brick_buff,stone_brown,terracotta_ornament}.jpg (1024 px, quality 85)

Why (PLAN.md Progress log 2026-11-10 "Bank Building colour CONFIRMED wrong", research/nrhp-findings.md):
the brick is unpainted BUFF / yellow-tan, the rock-faced ground storey and piers are BROWN stone
(brownstone colour), and a terra cotta frieze with an anthemion (leaf) pattern and roundels runs
under the cornice, with small terra cotta ornaments over the arched top-floor windows.

- brick_buff.jpg     : polyhaven/red_brick.jpg (Poly Haven `red_brick`, CC0) recoloured: bricks
                       (the saturated pixels) -> buff #C29A66 keeping their light/dark variation,
                       mortar (the grey pixels) -> lighter cream-grey #D4CCBA. Tile 1.4 m as before.
- stone_brown.jpg    : bank-building/sandstone_blocks_05.jpg (Poly Haven `sandstone_blocks_05`, CC0)
                       75% desaturated, then shifted to warm brown-grey #786050. Tile 3.4 m as before.
- terracotta_ornament.jpg : drawn here (original work, no download). An atlas:
      top half (rows 0-511)        frieze strip, ONE front bay (1.712 m) wide x 0.85 m tall,
                                   seamless left-right (the frieze wraps in U): bead mouldings top
                                   and bottom, an anthemion of palmettes and lotus joined by
                                   scrolls, and a wreathed roundel at the centre (sits over each
                                   pilaster).
      bottom-left 512 x 512        rosette roundel (the 0.55 m discs on the pilasters)
      x 512-767, rows 512-895      keystone ornament (leaf on a tapered block, 0.20 x 0.30 m)
      x 768-1023, rows 512-1023    plain terra cotta (edges and sides)
  Relief is faked: a height map is drawn, blurred and lit from the upper left.
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps, ImageStat

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "textures" / "bank-building"
SIZE = 1024


def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def shift(image, color):
    """Scale each channel so the average becomes `color` (keeps the material's own variation)."""
    means = ImageStat.Stat(image).mean
    target = rgb(color)
    bands = [b.point(lambda v, k=t / m: max(0, min(255, int(v * k))))
             for b, m, t in zip(image.split(), means, target)]
    return Image.merge("RGB", bands)


def colourise(lum, color, mean_lum, contrast=1.0):
    """Greyscale -> colour: `color` at the mean luminance, brighter/darker with the luminance."""
    c = rgb(color)
    bands = [lum.point(lambda v, t=t: max(0, min(255, int(t * (1 + contrast * (v / mean_lum - 1))))))
             for t in c]
    return Image.merge("RGB", bands)


# --- 1. Buff brick ----------------------------------------------------------------------------
brick = Image.open(ROOT / "assets" / "textures" / "polyhaven" / "red_brick.jpg").convert("RGB")
sat = brick.convert("HSV").split()[1]
# bricks are saturated (S > ~95), mortar grey (S < ~55): soft mask, 1 = brick
mask = sat.point(lambda s: max(0, min(255, int((s - 55) * 255 / 40)))).filter(ImageFilter.GaussianBlur(0.8))
lum = ImageOps.grayscale(brick)
lum_brick = ImageStat.Stat(lum, mask).mean[0]
lum_mortar = ImageStat.Stat(lum, ImageOps.invert(mask)).mean[0]
# Keep a little of each brick's own hue variation (burnt / pale bricks) on top of the buff.
buff = colourise(lum, "#c29a66", lum_brick, 1.0)
orig_tint = shift(brick, "#c29a66")
buff = Image.blend(buff, orig_tint, 0.15)
mortar = colourise(lum, "#d4ccba", lum_mortar, 0.8)
out = Image.composite(buff, mortar, mask)
out.save(OUT / "brick_buff.jpg", quality=85)
print("brick_buff.jpg mean", [round(v) for v in ImageStat.Stat(out).mean],
      "| brick", [round(v) for v in ImageStat.Stat(out, mask).mean],
      "| mortar", [round(v) for v in ImageStat.Stat(out, ImageOps.invert(mask)).mean])

# --- 2. Brown stone ---------------------------------------------------------------------------
stone = Image.open(OUT / "sandstone_blocks_05.jpg").convert("RGB")
grey = ImageOps.grayscale(stone).convert("RGB")
brown = shift(Image.blend(stone, grey, 0.75), "#786050")
brown.save(OUT / "stone_brown.jpg", quality=85)
print("stone_brown.jpg mean", [round(v) for v in ImageStat.Stat(brown).mean])

# --- 3. Terra cotta ornament atlas ------------------------------------------------------------
SS = 2                                   # draw at 2x, then downsample
W = SIZE * SS
H = SIZE * SS
hmap = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(hmap)
FH = 512 * SS                            # frieze strip height (top half)


def lobe(base, ang, length, width, bend=0.0, n=14):
    """Teardrop leaf outline from `base`, pointing at angle `ang` (radians, 0 = up), with its
    tip bending by `bend` radians."""
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        a = ang + bend * t * t
        cx = base[0] + math.sin(ang) * length * t + math.sin(a) * 0.0
        cy = base[1] - math.cos(ang) * length * t
        # bend: shift the centre line sideways progressively
        cx += math.sin(ang + math.pi / 2) * bend * length * 0.35 * t * t
        cy -= math.cos(ang + math.pi / 2) * bend * length * 0.35 * t * t
        hw = width * (math.sin(math.pi * min(1.0, t * 1.15)) ** 0.7) * (1 - 0.35 * t)
        nx, ny = math.cos(ang), math.sin(ang)
        left.append((cx - nx * hw, cy - ny * hw))
        right.append((cx + nx * hw, cy + ny * hw))
    return left + right[::-1]


def palmette(draw, x, y, scale, value=200, down=False, lobes=7, spread_deg=58):
    """Fan of leaves from (x, y); upright (or hanging if `down`)."""
    s = -1 if down else 1
    spread = math.radians(spread_deg)
    for i in range(lobes):
        f = (i - (lobes - 1) / 2) / ((lobes - 1) / 2)          # -1 .. 1
        ang = f * spread
        length = scale * (1.0 - 0.32 * abs(f) ** 1.5)
        pts = lobe((0, 0), ang, length, scale * 0.085, bend=-0.30 * f)
        draw.polygon([(x + px, y + s * py) for px, py in pts], fill=value)
    # heart-shaped base (calyx)
    r = scale * 0.16
    draw.ellipse([x - r, y - s * r * 0.4 - r * 0.7, x + r, y - s * r * 0.4 + r * 0.7], fill=min(255, value + 30))


def lotus(draw, x, y, scale, value=190):
    """Three pointed petals (centre one tall), the alternate motif of the anthemion."""
    draw.polygon([(x + px, y + py) for px, py in lobe((0, 0), 0.0, scale, scale * 0.16)], fill=value)
    for sgn in (-1, 1):
        draw.polygon([(x + px, y + py) for px, py in lobe((0, 0), sgn * math.radians(32), scale * 0.72,
                                                           scale * 0.13, bend=sgn * 0.6)], fill=value - 15)


def scroll(draw, x0, x1, y, amp, width, value=170, steps=60):
    """S-curve tendril from x0 to x1 along the frieze, ending in small curls."""
    pts = []
    for i in range(steps + 1):
        t = i / steps
        pts.append((x0 + (x1 - x0) * t, y - amp * math.sin(math.pi * t) * (1 if t < 0.5 else 1) * math.cos(math.pi * t)))
    draw.line(pts, fill=value, width=int(width))
    for (cx, cy), sg in ((pts[0], 1), (pts[-1], -1)):
        rr = width * 2.2
        draw.arc([cx - rr, cy - rr, cx + rr, cy + rr], 0, 300, fill=value, width=int(width * 0.8))


def roundel(draw, cx, cy, r, value=210, petals=8, wreath=True):
    """Wreathed roundel: raised rim, ring of small leaves, sunk field, 8-petal rosette, boss."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=value)                  # rim
    ri = r * 0.86
    draw.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=value - 70)         # sunk band
    if wreath:
        n = 20
        for i in range(n):
            a = 2 * math.pi * i / n
            bx, by = cx + math.cos(a) * r * 0.70, cy + math.sin(a) * r * 0.70
            pts = lobe((0, 0), a + math.pi / 2 + 0.5, r * 0.26, r * 0.07)
            draw.polygon([(bx + px, by + py) for px, py in pts], fill=value - 10)
    rf = r * 0.56
    draw.ellipse([cx - rf, cy - rf, cx + rf, cy + rf], fill=value - 85)        # field
    for i in range(petals):
        a = 2 * math.pi * i / petals
        pts = lobe((0, 0), a, rf * 0.92, rf * 0.26)
        draw.polygon([(cx + px, cy + py) for px, py in pts], fill=value - 5)
    rb = rf * 0.26
    draw.ellipse([cx - rb, cy - rb, cx + rb, cy + rb], fill=255)                # boss


def bead_row(draw, y0, y1, x0, x1, pitch, value=200):
    """Bead-and-reel: long beads with small discs between them."""
    cy = (y0 + y1) / 2
    h = (y1 - y0) / 2
    x = x0
    while x < x1:
        draw.ellipse([x + pitch * 0.08, cy - h, x + pitch * 0.62, cy + h], fill=value)
        draw.ellipse([x + pitch * 0.70, cy - h * 0.7, x + pitch * 0.92, cy + h * 0.7], fill=value - 20)
        x += pitch


# Frieze strip (drawn 3 bays wide and the middle cut out, so it wraps seamlessly).
strip = Image.new("L", (W * 3, FH), 60)                 # recessed ground
sd = ImageDraw.Draw(strip)
sd.rectangle([0, 0, W * 3, 22 * SS], fill=225)                         # top fillet
bead_row(sd, 26 * SS, 48 * SS, 0, W * 3, 32 * SS, 205)                 # bead and reel
sd.rectangle([0, 52 * SS, W * 3, 58 * SS], fill=170)
sd.rectangle([0, 456 * SS, W * 3, 462 * SS], fill=170)
bead_row(sd, 466 * SS, 486 * SS, 16 * SS, W * 3, 32 * SS, 200)
sd.rectangle([0, 490 * SS, W * 3, FH], fill=225)                       # bottom fillet
for rep in range(3):
    ox = rep * W
    base_y = 395 * SS
    # scrolls along the bottom joining every motif (palmettes at 0, 256, 768; lotus at 128, 896)
    for a, b in ((0, 128), (128, 256), (256, 340), (684, 768), (768, 896), (896, 1024)):
        scroll(sd, ox + a * SS, ox + b * SS, base_y + 20 * SS, 26 * SS, 7 * SS, 165)
    for px in (0, 256, 768, 1024):
        palmette(sd, ox + px * SS, base_y, 250 * SS, 205)
    for px in (128, 896):
        lotus(sd, ox + px * SS, base_y + 10 * SS, 200 * SS, 190)
    roundel(sd, ox + 512 * SS, 255 * SS, 158 * SS, 215)
hmap.paste(strip.crop((W, 0, 2 * W, FH)), (0, 0))

# bottom half: plain terra cotta ground
d.rectangle([0, FH, W, H], fill=150)
# rosette roundel (bottom-left 512 x 512)
roundel(d, 256 * SS, (512 + 256) * SS, 250 * SS, 215)
# keystone (x 512-767, rows 512-895): tapered block with a raised border and a hanging leaf
kx0, kx1, ky0, ky1 = 512 * SS, 768 * SS, 512 * SS, 896 * SS
d.rectangle([kx0, ky0, kx1, ky1], fill=110)
d.polygon([(kx0 + 10 * SS, ky0 + 8 * SS), (kx1 - 10 * SS, ky0 + 8 * SS),
           (kx1 - 34 * SS, ky1 - 8 * SS), (kx0 + 34 * SS, ky1 - 8 * SS)], fill=215)
d.polygon([(kx0 + 26 * SS, ky0 + 24 * SS), (kx1 - 26 * SS, ky0 + 24 * SS),
           (kx1 - 46 * SS, ky1 - 24 * SS), (kx0 + 46 * SS, ky1 - 24 * SS)], fill=120)
palmette(d, 640 * SS, ky0 + 70 * SS, 230 * SS, 220, down=True, lobes=5, spread_deg=28)
scroll(d, kx0 + 50 * SS, kx1 - 50 * SS, ky0 + 64 * SS, 14 * SS, 9 * SS, 225)

hmap = hmap.filter(ImageFilter.GaussianBlur(2.2 * SS))

# Light from the upper left: compare each pixel with its neighbour towards the light.
off = 3 * SS
lit = ImageChops.offset(hmap, off, off)              # value of the pixel up-left
shade = ImageChops.subtract(hmap, lit, scale=1.0, offset=128)     # >128: faces the light
shade2 = ImageChops.subtract(lit, hmap, scale=1.0, offset=0)      # >0: faces away
rng = random.Random(1897)
base = Image.new("RGB", (W, H), rgb("#d6b088"))      # terra cotta, a little lighter and pinker than the brick
# depth darkening: the recessed ground is darker (ambient occlusion)
ao = hmap.point(lambda v: int(150 + 105 * min(1.0, v / 200)))
col = ImageChops.multiply(base, Image.merge("RGB", [ao] * 3))
hi = shade.point(lambda v: max(0, (v - 128)) * 3)
lo = shade2.point(lambda v: min(255, v * 3))
col = ImageChops.add(col, Image.merge("RGB", [hi.point(lambda v: v * 0.55), hi.point(lambda v: v * 0.48), hi.point(lambda v: v * 0.38)]))
col = ImageChops.subtract(col, Image.merge("RGB", [lo.point(lambda v: v * 0.45), lo.point(lambda v: v * 0.50), lo.point(lambda v: v * 0.52)]))
col = col.resize((SIZE, SIZE), Image.LANCZOS)

# clay variation: fine grain and soft blotches (seamless enough at this scale)
grain = Image.effect_noise((SIZE, SIZE), 18).point(lambda v: int(232 + (v - 128) * 0.12))
small = Image.new("L", (16, 16))
small.putdata([rng.randrange(225, 256) for _ in range(256)])
big = Image.new("L", (48, 48))
for i in range(3):
    for j in range(3):
        big.paste(small, (i * 16, j * 16))
blot = big.resize((SIZE * 3, SIZE * 3), Image.BICUBIC).crop((SIZE, SIZE, 2 * SIZE, 2 * SIZE))   # tiles seamlessly
col = ImageChops.multiply(col, Image.merge("RGB", [grain] * 3))
col = ImageChops.multiply(col, Image.merge("RGB", [blot] * 3))
col = ImageChops.add(col, Image.new("RGB", (SIZE, SIZE), (10, 9, 7)))
col.save(OUT / "terracotta_ornament.jpg", quality=85)
print("terracotta_ornament.jpg mean (frieze)", [round(v) for v in ImageStat.Stat(col.crop((0, 0, SIZE, 512))).mean])
