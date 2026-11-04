"""Colour copies for the street-props kit (PLAN.md, Street ambiance, Pass 1).

Reads the 1K Poly Haven colour maps in assets/textures/street-props/ (and two reused maps)
and writes painted / re-coloured copies next to them. Run from the project root:
    python tools/prepare_street_props_textures.py
"""
from pathlib import Path
from PIL import Image, ImageChops, ImageOps

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "assets" / "textures"
OUT = TEX / "street-props"


def tint(image, color, contrast=1.0):
    """Keep the texture's light/dark variation but give it a new colour (as prepare_textures.py)."""
    grey = ImageOps.grayscale(image)
    mean = sum(i * n for i, n in enumerate(grey.histogram())) / (grey.width * grey.height)
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    def channel(c):
        return grey.point(lambda v: max(0, min(255, int(c * (1 + (v / mean - 1) * contrast)))))
    return Image.merge("RGB", (channel(r), channel(g), channel(b)))


# Rough-pitched light-grey granite for the fountain monolith: rock_boulder_dry (beige, 1.8 m,
# no block joints) turned light cool grey like the fountain photo.
rock = Image.open(OUT / "rock_boulder_dry.jpg").convert("RGB")
tint(rock, "#a5a39d", 1.25).save(OUT / "granite_rough_grey.jpg", quality=88)

# Dressed light granite (fountain bowl, hitching posts, carriage steps): granite_tile_03 has
# joints every 0.6 x 0.9 m, so take one joint-free 320 px square from inside a tile, make it
# seamless by blending it with a half-offset copy (centre from the original, edges from the
# copy), and repeat it 2 x 2. 320 px of the 1.8 m map = 0.5625 m -> the result tiles at 1.125 m.
gran = Image.open(TEX / "street-tree" / "granite_tile_03.jpg").convert("RGB")
crop = gran.crop((14, 14, 334, 334))
shifted = ImageChops.offset(crop, 160, 160)
mask = Image.new("L", (320, 320))
mask.putdata([int(255 * max(0.0, 1 - max(abs(x - 159.5), abs(y - 159.5)) / 160) ** 0.5)
              for y in range(320) for x in range(320)])
seamless = Image.composite(crop, shifted, mask)
tile = Image.new("RGB", (640, 640))
for ox in (0, 320):
    for oy in (0, 320):
        tile.paste(seamless, (ox, oy))
tile = tile.resize((1024, 1024), Image.LANCZOS)
tint(tile, "#aeaba4", 1.0).save(OUT / "granite_dressed_light.jpg", quality=88)

# Painted cast iron for the hydrant: metal_plate_02 under dark red-brown paint #5A2A22.
plate = Image.open(TEX / "polyhaven" / "metal_plate_02.jpg").convert("RGB")
tint(plate, "#5a2a22", 1.3).save(OUT / "iron_paint_redbrown.jpg", quality=88)
