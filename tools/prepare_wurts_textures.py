"""
prepare_wurts_textures.py - the one re-coloured texture for the Wurts Law Office (59 Main St).

Usage:  python tools/prepare_wurts_textures.py
Output: assets/textures/wurts-law-office/planks_grey.jpg (1024 x 1024, quality 85)

Nothing new is downloaded. polyhaven/weathered_planks.jpg (CC0, Poly Haven) is brown; the
spec wants a mid grey (#8A877F) for the porch deck, step, foundation and roofs. A multiply
tint cannot take the brown out, so this makes a grey copy that keeps the planks' light/dark
variation. The other textures are reused unchanged: courthouse/paint_white.jpg,
polyhaven/door_paint_green.jpg (darkened in Blender with a colour factor), polyhaven/red_brick.jpg.
"""
from pathlib import Path
from PIL import Image, ImageOps, ImageStat

ROOT = Path(__file__).resolve().parent.parent
PH = ROOT / "assets" / "textures" / "polyhaven"
OUT = ROOT / "assets" / "textures" / "wurts-law-office"
OUT.mkdir(parents=True, exist_ok=True)


def tint(image, color, contrast=1.0):
    """Keep the texture's light/dark variation but give it a new colour (as prepare_textures.py)."""
    grey = ImageOps.grayscale(image)
    mean = sum(i * n for i, n in enumerate(grey.histogram())) / (grey.width * grey.height)
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))

    def channel(c):
        return grey.point(lambda v: max(0, min(255, int(c * (1 + (v / mean - 1) * contrast)))))
    return Image.merge("RGB", (channel(r), channel(g), channel(b)))


# Porch deck, step, stone underpinning, roofs: mid grey #8A877F; grain softened (0.7) so the
# planks read as weathered grey paint rather than raw wood.
tint(Image.open(PH / "weathered_planks.jpg").convert("RGB"), "#8a877f", 0.7).save(
    OUT / "planks_grey.jpg", quality=85)

for f in sorted(OUT.glob("*.jpg")):
    print(f.name, f.stat().st_size // 1024, "KB", [round(x) for x in ImageStat.Stat(Image.open(f)).mean])
