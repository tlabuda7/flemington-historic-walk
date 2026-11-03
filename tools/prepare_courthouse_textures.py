"""
prepare_courthouse_textures.py - the Hunterdon County Court House's new Poly Haven textures.

Usage:  python tools/prepare_courthouse_textures.py <folder with the downloaded *_diff_1k jpgs renamed to <id>.jpg>
Output: assets/textures/courthouse/*.jpg (1024 x 1024, quality 85)

All sources are CC0 from https://polyhaven.com (see SOURCES.md). Each untinted source is
kept as <id>.jpg; painted/coloured versions are named for their use.
The courthouse also reuses the Union Hotel's textures in assets/textures/polyhaven/.
"""
import sys
from pathlib import Path
from PIL import Image, ImageOps, ImageStat

SRC = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent.parent / "assets" / "textures" / "courthouse"
OUT.mkdir(parents=True, exist_ok=True)


def tint(image, color, contrast=1.0):
    """Keep the texture's light/dark variation but give it a new paint colour (as prepare_textures.py)."""
    grey = ImageOps.grayscale(image)
    mean = sum(i * n for i, n in enumerate(grey.histogram())) / (grey.width * grey.height)
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    def channel(c):
        return grey.point(lambda v: max(0, min(255, int(c * (1 + (v / mean - 1) * contrast)))))
    return Image.merge("RGB", (channel(r), channel(g), channel(b)))


def shift(image, color):
    """Scale each channel so the average becomes `color`; keeps the stone's own colour variation."""
    means = ImageStat.Stat(image).mean
    target = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    bands = [b.point(lambda v, k=t / m: max(0, min(255, int(v * k))))
             for b, m, t in zip(image.split(), means, target)]
    return Image.merge("RGB", bands)


def load(name):
    return Image.open(SRC / f"{name}.jpg").convert("RGB")


# Untinted sources (kept for reference / re-tinting).
for name in ["white_stucco", "red_sandstone_pavement", "brown_planks_05", "rock_wall_08",
             "green_metal_rust"]:
    load(name).save(OUT / f"{name}.jpg", quality=85)

# Walls: lime stucco painted warm off-white (spec #E6E1D4). The source is very even,
# so contrast is raised a little to keep a visible trowel grain.
tint(load("white_stucco"), "#e6e1d4", 2.0).save(OUT / "stucco_offwhite.jpg", quality=85)
# Steps, pedestals, base course, sills: red-brown brownstone ashlar (spec #6E4A3C).
# Half-and-half with the natural stone so it stays chocolate brown, not brick orange.
stone = load("red_sandstone_pavement")
Image.blend(stone, shift(stone, "#6e4a3c"), 0.5).save(OUT / "brownstone.jpg", quality=85)
# North wing: lap clapboard painted dull buff-brown (1909 colour card).
tint(load("brown_planks_05"), "#9c8566", 1.0).save(OUT / "clapboard_buff.jpg", quality=85)
# Cupola dome: painted sheet metal, muted grey-green, with the source's light rust streaks.
shift(load("green_metal_rust"), "#4a5a46").save(OUT / "dome_paint_green.jpg", quality=85)

for f in sorted(OUT.glob("*.jpg")):
    print(f.name, f.stat().st_size // 1024, "KB")
