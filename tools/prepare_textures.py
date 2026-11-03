"""
prepare_textures.py - turns downloaded Poly Haven colour maps into the project's textures.

Usage:  python tools/prepare_textures.py <folder with the downloaded *_diff_1k jpgs renamed to <id>.jpg>
Output: assets/textures/polyhaven/*.jpg (1024 x 1024)

All source textures are CC0 from https://polyhaven.com (see SOURCES.md).
Painted surfaces are re-tinted from the neutral plaster texture so their colour
matches the period photos.
"""
import sys
from pathlib import Path
from PIL import Image, ImageOps

SRC = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent.parent / "assets" / "textures" / "polyhaven"
OUT.mkdir(parents=True, exist_ok=True)


def tint(image, color, contrast=1.0):
    """Keep the texture's light/dark variation but give it a new paint colour."""
    grey = ImageOps.grayscale(image)
    mean = sum(i * n for i, n in enumerate(grey.histogram())) / (grey.width * grey.height)
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    def channel(c):
        return grey.point(lambda v: max(0, min(255, int(c * (1 + (v / mean - 1) * contrast)))))
    return Image.merge("RGB", (channel(r), channel(g), channel(b)))


plaster = Image.open(SRC / "painted_plaster_wall.jpg").convert("RGB")
tint(plaster, "#e6dac0", 1.4).save(OUT / "trim_paint_cream.jpg", quality=85)
tint(plaster, "#2f3a2c", 1.2).save(OUT / "sign_paint_green.jpg", quality=85)

for name in ["red_brick", "weathered_planks", "roof_slates_03", "metal_plate_02",
             "concrete_floor_worn_001", "wood_table_worn"]:
    Image.open(SRC / f"{name}.jpg").convert("RGB").save(OUT / f"{name}.jpg", quality=85)

for f in sorted(OUT.glob("*.jpg")):
    print(f.name, f.stat().st_size // 1024, "KB")
