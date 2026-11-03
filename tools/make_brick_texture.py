"""
make_brick_texture.py - draws a tileable red-brick texture for the scene.

Usage:  python tools/make_brick_texture.py
Output: assets/textures/brick_red.jpg (512 x 512, covers 0.84 m x 0.84 m of wall:
        4 bricks of 0.21 m across, 12 courses of 0.07 m up, running bond).
"""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

SIZE = 512
COLS, ROWS = 4, 12
MORTAR = (184, 171, 152)
BASES = [(140, 59, 42), (122, 51, 36), (150, 66, 46), (131, 55, 39), (112, 47, 34)]

random.seed(1920)
img = Image.new("RGB", (SIZE, SIZE), MORTAR)
draw = ImageDraw.Draw(img)
gap = 4
for row in range(ROWS):
    y0 = round(row * SIZE / ROWS)
    y1 = round((row + 1) * SIZE / ROWS)
    offset = 0 if row % 2 == 0 else SIZE / COLS / 2
    for col in range(-1, COLS + 1):
        x0 = round(col * SIZE / COLS + offset)
        x1 = round((col + 1) * SIZE / COLS + offset)
        base = random.choice(BASES)
        shade = random.randint(-10, 10)
        color = tuple(max(0, min(255, c + shade)) for c in base)
        # draw wrapped so the texture tiles seamlessly left/right
        for dx in (-SIZE, 0, SIZE):
            draw.rectangle([x0 + dx + gap // 2, y0 + gap // 2, x1 + dx - gap // 2, y1 - gap // 2], fill=color)

# a little surface grain
noise = Image.effect_noise((SIZE, SIZE), 18).convert("RGB")
img = Image.blend(img, noise, 0.06).filter(ImageFilter.SMOOTH)

out = Path(__file__).resolve().parent.parent / "assets" / "textures" / "brick_red.jpg"
out.parent.mkdir(parents=True, exist_ok=True)
img.save(out, quality=85)
print(out, out.stat().st_size // 1024, "KB")
