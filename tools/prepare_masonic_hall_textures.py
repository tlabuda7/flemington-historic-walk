"""
prepare_masonic_hall_textures.py - derived textures for the Masonic Hall / Hunterdon County
National Bank (90-94 Main St).

Usage:  python tools/prepare_masonic_hall_textures.py
Output (assets/textures/masonic-hall/):
  stone_grey.jpg        1024 x 1024, q 85: county-offices/stone_buff.jpg (from Poly Haven, CC0)
                        desaturated and recoloured to a pale grey ashlar averaging ~#C4BFB4
                        (sills, plinths, frieze and cornice of the 1921 front, wheel window,
                        steps; tile 1.6 m)
  stone_rusticated.jpg  1024 x 1024, q 85: the same grey stone with horizontal V-channels every
                        0.40 m (4 per 1.6 m tile), for the rusticated piers of the 1921 bank front.
                        Box UVs use v = z / 1.6, so the channels sit at z = 0.35 + 0.40 k
                        (1.15, 1.55, ... 3.95 m: the first block starts on the 0.75 m plinth).
  inscription_mask.png  1024 x 836 (the 0.98 x 0.80 m tablet), white letters on black: "THE / HUNTERDON / COUNTY /
                        NATIONAL / BANK" (decision 2 (i)). Bake input only (not exported): the
                        grime bake darkens the corner-pier tablet with it, so the letters are
                        "cut" into the stone in the lightmap. Set in Times New Roman Bold
                        (timesbd.ttf, installed with Windows; rendered into the image, no font
                        file is shipped).

Nothing is downloaded. Pillow only.
"""

from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageStat

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "textures" / "county-offices" / "stone_buff.jpg"
OUT = ROOT / "assets" / "textures" / "masonic-hall"
TARGET = (0xC4, 0xBF, 0xB4)
TILE = 1.6                     # metres per repeat (bake script uses the same)
PITCH = 0.40                   # channel spacing
CH0 = 0.35                     # first channel centre (z mod PITCH)
CH_W = 0.03                    # channel width

OUT.mkdir(parents=True, exist_ok=True)

# --- grey stone ---------------------------------------------------------------------------
src = Image.open(SRC).convert("RGB")
grey = ImageOps.grayscale(src)
mean = ImageStat.Stat(grey).mean[0]
# keep 80 % of the texture's contrast round the target colour
chans = []
for t in TARGET:
    chans.append(grey.point(lambda v, t=t: max(0, min(255, round(t + (v - mean) * 0.8)))))
stone = Image.merge("RGB", chans)
stone.save(OUT / "stone_grey.jpg", quality=85)
print("wrote", OUT / "stone_grey.jpg", ImageStat.Stat(stone).mean)

# --- rusticated: horizontal V-channels ----------------------------------------------------
S = stone.size[1]
px_per_m = S / TILE
shade = Image.new("L", stone.size, 255)
d = ImageDraw.Draw(shade)
for k in range(int(TILE / PITCH)):
    zc = CH0 + k * PITCH                      # channel centre in metres (v = z / TILE)
    yc = (1.0 - zc / TILE) * S                # image row (row 0 at the top = v 1)
    half = CH_W / 2 * px_per_m
    top, bot = yc - half, yc + half
    rows = int(round(bot - top))
    for r in range(rows + 1):
        y = top + r
        f = r / max(1, rows)                  # 0 at the upper edge, 1 at the lower edge
        # upper bevel faces down (dark), lower bevel faces up (lit by the sky)
        v = 120 + 70 * f if f < 0.5 else 175 + 60 * (f - 0.5) * 2
        d.line([(0, y % S), (S, y % S)], fill=int(v))
    # a hair-line of shadow right under the upper arris
    d.line([(0, (top - 1) % S), (S, (top - 1) % S)], fill=200)
shade = shade.filter(ImageFilter.GaussianBlur(0.8))
rust = ImageChops.multiply(stone, Image.merge("RGB", [shade] * 3))
rust.save(OUT / "stone_rusticated.jpg", quality=85)
print("wrote", OUT / "stone_rusticated.jpg")

# --- inscription mask (bake input) -----------------------------------------------------------
# The tablet on the corner pier (masonic_hall.py TABLET) is 0.98 x 0.80 m; the image covers it
# exactly. Five lines on a 0.14 m pitch, capitals about 0.09 m tall, letter-spaced, centred.
TW, TH = 0.98, 0.80
W = 1024
H = round(W * TH / TW)
mask = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(mask)
lines = ["THE", "HUNTERDON", "COUNTY", "NATIONAL", "BANK"]
ppm = W / TW
cap = 0.09 * ppm
size = 200
while True:
    font = ImageFont.truetype("C:/Windows/Fonts/timesbd.ttf", size)
    l, t, r, b = d.textbbox((0, 0), "H", font=font)
    track = 0.012 * ppm
    widest = max(sum(d.textbbox((0, 0), ch, font=font)[2] - d.textbbox((0, 0), ch, font=font)[0] for ch in text)
                 + track * (len(text) - 1) for text in lines)
    if (b - t) <= cap and widest <= 0.92 * ppm:
        break
    size -= 2
pitch = 0.14 * ppm
y0 = (H - pitch * (len(lines) - 1) - (b - t)) / 2      # top of the first line's capitals
for i, text in enumerate(lines):
    widths = [d.textbbox((0, 0), ch, font=font)[2] - d.textbbox((0, 0), ch, font=font)[0] for ch in text]
    total = sum(widths) + track * (len(text) - 1)
    x = (W - total) / 2
    y = y0 + pitch * i - t
    for ch, w in zip(text, widths):
        cl = d.textbbox((0, 0), ch, font=font)[0]
        d.text((x - cl, y), ch, fill=255, font=font)
        x += w + track
mask = mask.filter(ImageFilter.GaussianBlur(1.0))
mask.save(OUT / "inscription_mask.png")
print("wrote", OUT / "inscription_mask.png", mask.size, "font size", size, "cap px", b - t)
