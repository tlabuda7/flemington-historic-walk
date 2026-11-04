"""
prepare_bank_textures.py - textures for the Bank Building / Flemington National Bank (56-66 Main St).

Usage:  python tools/prepare_bank_textures.py <folder with sandstone_blocks_05.jpg>
        (the Poly Haven 1K Diffuse JPG, sandstone_blocks_05_diff_1k.jpg, renamed to <id>.jpg)
Output: assets/textures/bank-building/*.jpg (1024 x 1024, quality 85)

- sandstone_blocks_05.jpg : untinted CC0 source from https://polyhaven.com (see SOURCES.md)
- stone_rockfaced.jpg     : that texture, mostly desaturated and shifted to light warm grey #A8A294
                            (rock-faced ground storey; real-world tile 3.0 m, about 7 courses)
- awning_stripes.jpg      : generated here (no download): faded red #9A4A3E / cream #DDD3BC canvas
                            stripes, 0.15 m each, 4 stripes = 0.6 m tile across the stripes;
                            stripes run along V (down the awning slope). Seamless in both directions.
Unchanged reuse (not copied): polyhaven/red_brick.jpg, county-offices/trim_paint_drab.jpg,
county-offices/door_varnish_dark.jpg.
"""
import random
import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

SRC = Path(sys.argv[1])
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "textures" / "bank-building"
OUT.mkdir(parents=True, exist_ok=True)
SIZE = 1024


def shift(image, color):
    """Scale each channel so the average becomes `color`; keeps the material's own variation."""
    means = ImageStat.Stat(image).mean
    target = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    bands = [b.point(lambda v, k=t / m: max(0, min(255, int(v * k))))
             for b, m, t in zip(image.split(), means, target)]
    return Image.merge("RGB", bands)


def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def tileable_noise(rng, cells, size=SIZE):
    """Smooth random greyscale noise that repeats seamlessly: a small random grid, tiled 3 x 3,
    scaled up and the middle copy cut out."""
    small = Image.new("L", (cells, cells))
    small.putdata([rng.randrange(256) for _ in range(cells * cells)])
    big = Image.new("L", (cells * 3, cells * 3))
    for i in range(3):
        for j in range(3):
            big.paste(small, (i * cells, j * cells))
    big = big.resize((size * 3, size * 3), Image.BICUBIC)
    return big.crop((size, size, size * 2, size * 2))


# --- Stone: Sandstone Blocks 05 (3.0 m real size), rock-faced coursed ashlar -------------------
stone = Image.open(SRC / "sandstone_blocks_05.jpg").convert("RGB")
stone.save(OUT / "sandstone_blocks_05.jpg", quality=85)
# The source is cream sandstone: take 75% of the colour out first so the shift lands on a grey,
# not a beige, then move the average to the spec's light warm grey.
grey = ImageOps.grayscale(stone).convert("RGB")
shift(Image.blend(stone, grey, 0.75), "#a8a294").save(OUT / "stone_rockfaced.jpg", quality=85)

# --- Awning: generated striped canvas ----------------------------------------------------------
rng = random.Random(1920)
red, cream = rgb("#9a4a3e"), rgb("#ddd3bc")
stripe = SIZE // 4                       # 0.15 m of a 0.6 m tile = 256 px

# Base stripes (columns), with a 2 px soft edge where the dye meets the cream.
cols = Image.new("RGB", (SIZE, 1))
cols.putdata([red if (x // stripe) % 2 == 0 else cream for x in range(SIZE)])
canvas = cols.resize((SIZE, SIZE), Image.NEAREST).filter(ImageFilter.GaussianBlur(1.2))

# Uneven fading: large soft patches where the red is bleached toward the cream.
fade = tileable_noise(rng, 6).point(lambda v: int(max(0, v - 90) * 0.55))   # 0..90
bleached = Image.blend(canvas, Image.new("RGB", (SIZE, SIZE), cream), 0.45)
canvas = Image.composite(bleached, canvas, fade)

# Medium blotches (dirt / weather), +-6%.
blotch = tileable_noise(rng, 24)
canvas = ImageChops.multiply(canvas, Image.merge("RGB", [blotch.point(lambda v: int(240 + v * 15 / 255))] * 3))

# Canvas weave: fine per-pixel grain plus faint thread lines every 4 px in both directions
# (1024 is a multiple of 4, so it stays seamless).
grain = Image.new("L", (SIZE, SIZE))
grain.putdata([rng.randrange(236, 256) for _ in range(SIZE * SIZE)])
grain = grain.filter(ImageFilter.GaussianBlur(0.6))
lines = Image.new("L", (SIZE, SIZE), 255)
px = lines.load()
for y in range(SIZE):
    for x in range(SIZE):
        d = (8 if x % 4 == 0 else 0) + (8 if y % 4 == 0 else 0)
        px[x, y] = 255 - d
weave = ImageChops.multiply(grain, lines)
canvas = ImageChops.multiply(canvas, Image.merge("RGB", [weave] * 3))

# Faint darker seam line where the canvas widths are sewn together (every stripe edge).
seam = Image.new("L", (SIZE, SIZE), 255)
sp = seam.load()
for x in range(0, SIZE, stripe):
    for dx, val in ((-1, 225), (0, 215), (1, 225)):
        for y in range(SIZE):
            sp[(x + dx) % SIZE, y] = val
canvas = ImageChops.multiply(canvas, Image.merge("RGB", [seam] * 3))
canvas.save(OUT / "awning_stripes.jpg", quality=85)

for f in sorted(OUT.glob("*.jpg")):
    print(f.name, f.stat().st_size // 1024, "KB", [round(x) for x in ImageStat.Stat(Image.open(f)).mean])
