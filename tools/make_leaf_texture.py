"""
make_leaf_texture.py - draws a cluster of summer leaves on a transparent background,
used on the leaf cards of the street trees.

Usage:  python tools/make_leaf_texture.py
Output: assets/textures/leaf_cluster.png (512 x 512, RGBA)
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw

SIZE = 512
GREENS = [(52, 78, 34), (66, 94, 40), (80, 108, 46), (44, 66, 30), (94, 120, 54), (60, 86, 38)]

random.seed(7)
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

# a few thin twigs first, so leaves sit on top of them
draw = ImageDraw.Draw(img)
for _ in range(6):
    a = random.uniform(0, 2 * math.pi)
    x0, y0 = SIZE / 2, SIZE / 2
    x1, y1 = x0 + math.cos(a) * SIZE * 0.42, y0 + math.sin(a) * SIZE * 0.42
    draw.line([(x0, y0), (x1, y1)], fill=(78, 62, 44, 255), width=3)


def leaf(length, width, color):
    """One leaf: a pointed oval with a lighter midrib, drawn pointing right."""
    pad = 4
    im = Image.new("RGBA", (length + 2 * pad, width + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = []
    for i in range(21):
        t = i / 20
        x = pad + t * length
        half = math.sin(math.pi * t) ** 0.8 * width / 2
        pts.append((x, pad + width / 2 - half))
    for i in range(20, -1, -1):
        t = i / 20
        x = pad + t * length
        half = math.sin(math.pi * t) ** 0.8 * width / 2
        pts.append((x, pad + width / 2 + half))
    d.polygon(pts, fill=color + (255,))
    light = tuple(min(255, c + 30) for c in color) + (255,)
    d.line([(pad, pad + width / 2), (pad + length, pad + width / 2)], fill=light, width=1)
    return im


# leaves, denser in the middle of the cluster
for _ in range(420):
    r = SIZE * 0.46 * math.sqrt(random.random()) ** 1.3
    a = random.uniform(0, 2 * math.pi)
    cx, cy = SIZE / 2 + math.cos(a) * r, SIZE / 2 + math.sin(a) * r
    base = random.choice(GREENS)
    shade = random.randint(-12, 12)
    color = tuple(max(0, min(255, c + shade)) for c in base)
    lf = leaf(random.randint(22, 38), random.randint(11, 18), color)
    lf = lf.rotate(random.uniform(0, 360), expand=True, resample=Image.BICUBIC)
    img.alpha_composite(lf, (int(cx - lf.width / 2), int(cy - lf.height / 2)))

out = Path(__file__).resolve().parent.parent / "assets" / "textures" / "leaf_cluster.png"
img.save(out, optimize=True)
print(out, out.stat().st_size // 1024, "KB")
