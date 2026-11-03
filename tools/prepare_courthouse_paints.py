"""
prepare_courthouse_paints.py - re-coloured courthouse textures (review round 1).

Usage:  python tools/prepare_courthouse_paints.py
Reads the local CC0 Poly Haven maps already in assets/textures/ and writes
(1024 x 1024, JPEG quality 85) into assets/textures/courthouse/:
  paint_white.jpg     columns, entablature, brackets, cupola: smooth painted white #F2EFE6,
                      from trim_paint_cream.jpg (painted_plaster_wall) with the blotches
                      reduced to a quarter of their contrast
  stucco_cream.jpg    walls: warm cream stucco #E8DDC6, from white_stucco.jpg
  rock_wall_grey.jpg  jail-yard wall: mid-grey fieldstone, from rock_wall_08.jpg
"""
from pathlib import Path
from PIL import Image, ImageOps, ImageStat

ROOT = Path(__file__).resolve().parent.parent / "assets" / "textures"
OUT = ROOT / "courthouse"


def tint(image, color, contrast=1.0):
    """Keep the texture's light/dark variation (scaled by `contrast`) but repaint it `color`."""
    grey = ImageOps.grayscale(image)
    mean = sum(i * n for i, n in enumerate(grey.histogram())) / (grey.width * grey.height)
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))

    def channel(c):
        return grey.point(lambda v: max(0, min(255, int(c * (1 + (v / mean - 1) * contrast)))))
    return Image.merge("RGB", (channel(r), channel(g), channel(b)))


def shift(image, color):
    """Scale each channel so the average becomes `color`."""
    means = ImageStat.Stat(image).mean
    target = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    bands = [b.point(lambda v, k=t / m: max(0, min(255, int(v * k))))
             for b, m, t in zip(image.split(), means, target)]
    return Image.merge("RGB", bands)


def load(path):
    return Image.open(path).convert("RGB")


tint(load(ROOT / "polyhaven" / "trim_paint_cream.jpg"), "#f2efe6", 0.25).save(OUT / "paint_white.jpg", quality=85)
tint(load(OUT / "white_stucco.jpg"), "#e8ddc6", 2.0).save(OUT / "stucco_cream.jpg", quality=85)
shift(load(OUT / "rock_wall_08.jpg"), "#8a857c").save(OUT / "rock_wall_grey.jpg", quality=85)
for name in ("paint_white", "stucco_cream", "rock_wall_grey"):
    f = OUT / f"{name}.jpg"
    print(f.name, [round(m) for m in ImageStat.Stat(load(f)).mean], f.stat().st_size // 1024, "KB")
