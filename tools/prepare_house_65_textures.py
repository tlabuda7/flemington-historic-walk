"""
prepare_house_65_textures.py - the one re-coloured texture for the frame dwelling at 65 Main St.

Usage:  python tools/prepare_house_65_textures.py
Output: assets/textures/house-65-main/clapboard_cream.jpg (1024 x 1024, quality 85)

Nothing new is downloaded. courthouse/brown_planks_05.jpg (Poly Haven `brown_planks_05`, CC0,
the untinted source) has ~9 horizontal lap boards per 1024 px. This makes a warm-cream painted
copy (#E6DFCC) at 35 % contrast, so the lap shadows stay but the wood grain and knots mostly
disappear. Tiled at 1.6 m in Blender that gives a ~0.18 m board exposure.

It also prints the image row of the cleanest board centre: house_65_main_bake.py squeezes the
trim's UVs onto that row so trim reads as flat paint (TRIM_V there = 1 - row / 1024).
The roof (polyhaven/roof_slates_03.jpg) and brick (polyhaven/red_brick.jpg) are reused
unchanged and tinted in Blender with a colour factor.
"""
from pathlib import Path
from PIL import Image, ImageOps, ImageStat

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "textures" / "courthouse" / "brown_planks_05.jpg"
OUT = ROOT / "assets" / "textures" / "house-65-main"
OUT.mkdir(parents=True, exist_ok=True)


def tint(image, color, contrast=1.0):
    """Keep the texture's light/dark variation but give it a new colour (as prepare_wurts_textures.py)."""
    grey = ImageOps.grayscale(image)
    mean = sum(i * n for i, n in enumerate(grey.histogram())) / (grey.width * grey.height)
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))

    def channel(c):
        return grey.point(lambda v: max(0, min(255, int(c * (1 + (v / mean - 1) * contrast)))))
    return Image.merge("RGB", (channel(r), channel(g), channel(b)))


src = Image.open(SRC).convert("RGB")
out = tint(src, "#e6dfcc", 0.35)
out.save(OUT / "clapboard_cream.jpg", quality=85)

# Find the flattest band (least row-to-row variation, away from lap shadows) for the trim.
grey = ImageOps.grayscale(out)
w, h = grey.size
rows = [sum(grey.crop((0, y, w, y + 1)).getdata()) / w for y in range(h)]
best, best_row = 1e9, 0
for y in range(12, h - 12):
    win = rows[y - 12:y + 13]
    m = sum(win) / len(win)
    score = sum((v - m) ** 2 for v in win) + (max(win) - min(win)) * 10
    if score < best:
        best, best_row = score, y
print("trim row", best_row, "-> TRIM_V =", round(1 - (best_row + 0.5) / h, 4))
for f in sorted(OUT.glob("*.jpg")):
    print(f.name, f.stat().st_size // 1024, "KB", [round(x) for x in ImageStat.Stat(Image.open(f)).mean])
