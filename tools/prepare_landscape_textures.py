"""Generate the landscape tree-silhouette atlas (1024 x 1024 RGBA, no download, CC0 by us).

Rows (256 px each, row 0 = top of the image):
  0  dense woods / ridge crown fringe (tiles horizontally)
  1  hedgerow: low mixed crowns with small gaps (tiles horizontally)
  2  orchard / grove with a few pointed cedars (tiles horizontally)
  3  four 256 px cells: farmhouse, barn, house + barn, windbreak clump
Colour is light grey shading (the mesh's vertex colour tints it); alpha is the silhouette
(cut out with alphaTest 0.5 in the scene).

Usage: python -I tools/prepare_landscape_textures.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "textures", "landscape", "tree_silhouettes.png")
S = 1024
R = 256


def crown(draw, cx, base, w, h, tile=True):
    """Round deciduous crown built from overlapping blobs; base = bottom y."""
    for _ in range(int(6 + w / 6)):
        bx = cx + random.uniform(-w / 2, w / 2) * 0.8
        by = base - h * random.uniform(0.35, 0.8)
        br = random.uniform(0.22, 0.38) * min(w, h) + 4
        for dx in ((-S, 0, S) if tile else (0,)):
            draw.ellipse([bx - br + dx, by - br, bx + br + dx, by + br], fill=255)
    for dx in ((-S, 0, S) if tile else (0,)):
        draw.ellipse([cx - w * 0.45 + dx, base - h * 0.55, cx + w * 0.45 + dx, base], fill=255)


def cedar(draw, cx, base, w, h):
    for dx in (-S, 0, S):
        draw.polygon([(cx - w / 2 + dx, base), (cx + dx, base - h), (cx + w / 2 + dx, base)], fill=255)


def main():
    random.seed(1920)
    alpha = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(alpha)
    # row 0: dense woods
    y0 = R
    for i in range(70):
        crown(d, random.uniform(0, S), y0, random.uniform(40, 90), random.uniform(120, 230))
    d.rectangle([0, y0 - 80, S, y0], fill=255)
    # row 1: hedgerow (lower, gaps)
    y1 = 2 * R
    x = 0
    while x < S:
        w = random.uniform(30, 80)
        crown(d, x + w / 2, y1, w, random.uniform(70, 170))
        x += w * random.uniform(0.6, 1.4)
    d.rectangle([0, y1 - 25, S, y1], fill=255)
    # row 2: orchard / grove with cedars
    y2 = 3 * R
    x = 10
    while x < S:
        if random.random() < 0.25:
            cedar(d, x, y2, random.uniform(25, 40), random.uniform(130, 220))
        else:
            crown(d, x, y2, random.uniform(50, 90), random.uniform(80, 160))
        x += random.uniform(35, 75)
    d.rectangle([0, y2 - 15, S, y2], fill=255)
    # row 3: farm buildings (no horizontal tiling)
    y3 = S - 2
    # cell 0: farmhouse (2 storeys, gable, chimney)
    d.rectangle([40, y3 - 120, 216, y3], fill=255)
    d.polygon([(30, y3 - 120), (128, y3 - 190), (226, y3 - 120)], fill=255)
    d.rectangle([170, y3 - 200, 184, y3 - 150], fill=255)
    # cell 1: barn (wide, gambrel)
    d.rectangle([276, y3 - 110, 492, y3], fill=255)
    d.polygon([(266, y3 - 110), (300, y3 - 175), (384, y3 - 215), (468, y3 - 175), (502, y3 - 110)], fill=255)
    # cell 2: house + barn + small crown
    d.rectangle([530, y3 - 90, 620, y3], fill=255)
    d.polygon([(524, y3 - 90), (575, y3 - 140), (626, y3 - 90)], fill=255)
    d.rectangle([640, y3 - 80, 760, y3], fill=255)
    d.polygon([(634, y3 - 80), (700, y3 - 130), (766, y3 - 80)], fill=255)
    crown(d, 620, y3, 50, 150, tile=False)
    # cell 3: windbreak clump
    for k in range(6):
        crown(d, 800 + k * 36, y3, 60, random.uniform(150, 230), tile=False)
    alpha = alpha.filter(ImageFilter.GaussianBlur(1.5))
    # shading: light grey, a little darker low down and with leafy noise
    grey = Image.new("L", (S, S), 0)
    gp = grey.load()
    for yy in range(S):
        row_t = (yy % R) / R
        for xx in range(S):
            n = (math.sin(xx * 0.21 + yy * 0.13) * math.sin(xx * 0.07 - yy * 0.19)) * 18
            gp[xx, yy] = int(max(0, min(255, 230 - row_t * 45 + n)))
    img = Image.merge("RGBA", (grey, grey, grey, alpha))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, optimize=True)
    print("wrote", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
