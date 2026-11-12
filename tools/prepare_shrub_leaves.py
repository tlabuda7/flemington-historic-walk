"""
prepare_shrub_leaves.py - seamless 1024 x 1024 "dense small leaves on dark green" colour map for
the Methodist church's foundation shrubs and ivy (PLAN.md "Rough-spot fixes" R-b). Made the way
the street-details hedge core (H1) was made: the project's own leaf_cluster.png (drawn by
tools/make_leaf_texture.py, original work) scattered small over a dark green ground. Every cluster
is also pasted shifted by +-1024 px, so the tile wraps without a seam. Opaque.

    python tools/prepare_shrub_leaves.py

Writes assets/textures/shared/shrub_leaves.jpg (1024 x 1024, sRGB, q80). Intended tile: ~0.8 m.
"""
import os
import random
from PIL import Image, ImageEnhance, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TX = os.path.join(ROOT, "assets", "textures")
OUT = os.path.join(TX, "shared", "shrub_leaves.jpg")
SIZE = 1024

leaf = Image.open(os.path.join(TX, "leaf_cluster.png")).convert("RGBA")
rng = random.Random(1909)
tile = Image.new("RGBA", (SIZE, SIZE), (26, 38, 20, 255))
# a soft darker / lighter mottle under the leaves so the gaps are not one flat colour
small = Image.effect_noise((SIZE // 32, SIZE // 32), 40)
wrap = Image.new("L", (SIZE // 32 * 3, SIZE // 32 * 3))
for i in range(3):
    for j in range(3):
        wrap.paste(small, (i * SIZE // 32, j * SIZE // 32))            # 3 x 3 so the blur wraps
wrap = wrap.resize((SIZE * 3, SIZE * 3), Image.BICUBIC).filter(ImageFilter.GaussianBlur(24))
mottle = wrap.crop((SIZE, SIZE, 2 * SIZE, 2 * SIZE))
dark = Image.new("RGBA", (SIZE, SIZE), (18, 28, 14, 255))
tile = Image.composite(tile, dark, mottle.point(lambda v: min(255, max(0, v * 2 - 128))))

# leaf_cluster.png's leaves are 22-38 px in 512 px: clusters of 380-640 px give 2-4 cm leaves at 0.8 m
for layer, (count, smin, smax, bmin, bmax) in enumerate(((90, 520, 640, 0.5, 0.75),
                                                         (150, 380, 520, 0.68, 1.0))):
    for _ in range(count):
        s = rng.randint(smin, smax)
        lc = leaf.resize((s, s), Image.LANCZOS).rotate(rng.uniform(0, 360), resample=Image.BICUBIC)
        lc = ImageEnhance.Brightness(lc).enhance(rng.uniform(bmin, bmax))
        x, y = rng.randint(0, SIZE - 1) - s // 2, rng.randint(0, SIZE - 1) - s // 2
        for dx in (-SIZE, 0, SIZE):
            for dy in (-SIZE, 0, SIZE):
                px, py = x + dx, y + dy
                if px + s <= 0 or py + s <= 0 or px >= SIZE or py >= SIZE:
                    continue
                tile.alpha_composite(lc, (max(0, px), max(0, py)), (max(0, -px), max(0, -py)))

tile.convert("RGB").save(OUT, quality=80)
print("wrote", OUT, tile.size, os.path.getsize(OUT) // 1024, "KB")
