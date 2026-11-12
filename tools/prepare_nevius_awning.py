"""
prepare_nevius_awning.py - plain pale canvas for the Nevius store awning (78 Main St).

The 1912 "Some Business Blocks" card (PLAN.md, Nevius addendum 2026-11-11) shows a plain
off-white awning, not stripes. This takes the generated striped canvas
(assets/textures/bank-building/awning_stripes.jpg; stripes run along V, so every pixel
column is one stripe colour), divides every pixel by its column's mean brightness (the
stripes vanish, the weave, fading and stains stay) and lays the result over #E3DCCB.

    python tools/prepare_nevius_awning.py

Writes assets/textures/nevius-store/awning_canvas.jpg (1024 x 1024, tiles like the source:
0.6 m per repeat). Pillow only.
"""

import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "textures", "bank-building", "awning_stripes.jpg")
OUT = os.path.join(ROOT, "assets", "textures", "nevius-store", "awning_canvas.jpg")
BASE = (0xE3, 0xDC, 0xCB)
CONTRAST = 0.8          # keep 80 % of the weave / fading contrast


def lum(p):
    return 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]


src = Image.open(SRC).convert("RGB")
w, h = src.size
col_mean = src.resize((w, 1), Image.BOX)
col_l = [max(1.0, lum(col_mean.getpixel((x, 0)))) for x in range(w)]
px = src.load()
out = Image.new("RGB", (w, h))
po = out.load()
for y in range(h):
    for x in range(w):
        f = 1.0 + (lum(px[x, y]) / col_l[x] - 1.0) * CONTRAST
        po[x, y] = tuple(max(0, min(255, round(c * f))) for c in BASE)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
out.save(OUT, quality=90)
print("wrote", OUT, out.size)
