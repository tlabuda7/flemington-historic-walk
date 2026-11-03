"""
prepare_county_offices_textures.py - textures for the County Offices / Hall of Records (69-71 Main St).

Usage:  python tools/prepare_county_offices_textures.py <folder with scuffed_cement.jpg>
        (the Poly Haven 1K Diffuse JPG, scuffed_cement_diff_1k.jpg, renamed to <id>.jpg)
Output: assets/textures/county-offices/*.jpg (1024 x 1024, quality 85)

All sources are CC0 from https://polyhaven.com (see SOURCES.md). The untinted new source is
kept as <id>.jpg; coloured versions are named for their use. Re-tinted copies of textures
already in the project are made from assets/textures/polyhaven/.
Unchanged reuse (not copied): polyhaven/red_brick.jpg, polyhaven/trim_paint_cream.jpg
(shutters), courthouse/rock_wall_08.jpg (foundation).
"""
import sys
from pathlib import Path
from PIL import Image, ImageOps, ImageStat

SRC = Path(sys.argv[1])
ROOT = Path(__file__).resolve().parent.parent
PH = ROOT / "assets" / "textures" / "polyhaven"
OUT = ROOT / "assets" / "textures" / "county-offices"
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
    """Scale each channel so the average becomes `color`; keeps the material's own colour variation."""
    means = ImageStat.Stat(image).mean
    target = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    bands = [b.point(lambda v, k=t / m: max(0, min(255, int(v * k))))
             for b, m, t in zip(image.split(), means, target)]
    return Image.merge("RGB", bands)


# New: Scuffed Cement (1.62 m real size) - fine-grained, no joints; shifted to pale buff
# sandstone (spec #CDBFA2) for the string course, sills, keystones, oculus ring, panel, stoops.
cement = Image.open(SRC / "scuffed_cement.jpg").convert("RGB")
cement.save(OUT / "scuffed_cement.jpg", quality=85)
shift(cement, "#cdbfa2").save(OUT / "stone_buff.jpg", quality=85)

# Cornice, brackets, window frames: light warm grey "stone drab" paint (spec #BDB4A0).
tint(Image.open(PH / "trim_paint_cream.jpg").convert("RGB"), "#bdb4a0", 1.0).save(
    OUT / "trim_paint_drab.jpg", quality=85)
# Roof: tin painted dark red-brown (spec #5A3E34), keeping the plate seams and wear.
shift(Image.open(PH / "metal_plate_02.jpg").convert("RGB"), "#5a3e34").save(
    OUT / "roof_tin_redbrown.jpg", quality=85)
# Doors: dark varnished brown wood (spec #3A2A1F); grain kept a little stronger.
tint(Image.open(PH / "wood_table_worn.jpg").convert("RGB"), "#3a2a1f", 1.3).save(
    OUT / "door_varnish_dark.jpg", quality=85)

for f in sorted(OUT.glob("*.jpg")):
    print(f.name, f.stat().st_size // 1024, "KB", [round(x) for x in ImageStat.Stat(Image.open(f)).mean])
