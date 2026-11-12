"""
prepare_street_details_textures.py - the one small atlas of the street-details kit
(PLAN.md "Street details pass 2", build split B). Run with the system Python (Pillow):

    python tools/prepare_street_details_textures.py

Writes assets/textures/street-details/details_atlas.jpg (1024 x 1024, sRGB). Regions (pixels,
y down; tools/blender/street_details.py uses the same numbers as UVs):

  S  x   0-255, y   0-1023  barber-pole stripes (red, white, blue, white) running as a helix:
                            u = once round the pole, v = the 1.44 m shaft, pitch 0.48 m
                            (colours TYPICAL: the Stryker plate is black and white)
  L  x 256-639, y   0-579   front of the waste-paper box: dark green paint, pale lettering
                            "FOR / WASTE / PAPER" as read from the Stryker plate (PHOTO)
  G  x 640-1023, y  0-383   plain dark green paint (box sides, lid; colour guess)
  H1 x 256-639, y 640-1023  hedge core: dense leaves on dark green, 0.5 m square, opaque
  H2 x 640-1023, y 640-1023 second hedge-core variant
Also writes street-details/stone_pale.jpg (granite_dressed_light.jpg re-saved at q72) for the
stone post.
Sources (all already in the project, CC0): polyhaven/sign_paint_green.jpg (Painted Plaster
Wall, tinted green), leaf_cluster.png (street-tree leaves).
"""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TX = os.path.join(ROOT, "assets", "textures")
OUT = os.path.join(TX, "street-details", "details_atlas.jpg")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

rnd = random.Random(11)
atlas = Image.new("RGB", (1024, 1024), (40, 48, 36))

# --- dark green paint (G and the background of L) -----------------------------------------
green_src = Image.open(os.path.join(TX, "polyhaven", "sign_paint_green.jpg")).convert("RGB")
green = ImageEnhance.Brightness(green_src).enhance(0.92)
atlas.paste(green.crop((0, 0, 384, 384)), (640, 0))
# filler between the regions (never sampled)
atlas.paste(green.crop((300, 300, 1024, 556)), (256, 384 + 196))

# --- L: lettered front of the box ---------------------------------------------------------
face = green.crop((420, 380, 804, 960)).copy()          # 384 x 580
d = ImageDraw.Draw(face)
font_path = r"C:\Windows\Fonts\arialbd.ttf"
lines = ["FOR", "WASTE", "PAPER"]
# letters about 0.09 m high on a 0.68 m face (580 px), three lines spread over the face; widest line fills
# ~88 % of the 0.45 m width, as on the plate
size = 100
while True:
    font = ImageFont.truetype(font_path, size)
    widest = max(d.textbbox((0, 0), t, font=font)[2] for t in lines)
    if widest <= 0.88 * 384:
        break
    size -= 2
pale = (226, 222, 206)
y = 78
for t in lines:
    bb = d.textbbox((0, 0), t, font=font)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((384 - w) / 2 - bb[0], y - bb[1]), t, font=font, fill=pale)
    y += h + 92
# weathering: soften, then knock a few flecks out of the paint
face = face.filter(ImageFilter.GaussianBlur(0.6))
fd = ImageDraw.Draw(face)
for _ in range(260):
    x, yy = rnd.randrange(384), rnd.randrange(580)
    r = rnd.choice((1, 1, 1, 2))
    c = green_src.getpixel((rnd.randrange(1024), rnd.randrange(1024)))
    fd.ellipse((x - r, yy - r, x + r, yy + r), fill=c)
atlas.paste(face, (256, 0))

# --- S: barber stripes --------------------------------------------------------------------
RED, WHITE, BLUE = (168, 34, 30), (232, 230, 222), (38, 52, 120)
bands = [RED, WHITE, BLUE, WHITE]
SHAFT_H, PITCH = 1.44, 0.48
stripes = Image.new("RGB", (256, 1024))
px = stripes.load()
for j in range(1024):
    hgt = (1023 - j) / 1023 * SHAFT_H          # v up the shaft
    for i in range(256):
        u = (i + 0.5) / 256
        phase = (u + hgt / PITCH) % 1.0
        px[i, j] = bands[int(phase * 4) % 4]
stripes = stripes.filter(ImageFilter.GaussianBlur(0.7))
# slight paint mottling from the white paint texture
paint = Image.open(os.path.join(TX, "courthouse", "paint_white.jpg")).convert("L").resize((256, 1024))
mott = Image.merge("RGB", [paint] * 3)
stripes = Image.blend(stripes, Image.composite(stripes, mott, Image.new("L", (256, 1024), 200)), 0.25)
atlas.paste(stripes, (0, 0))

# --- H: hedge core (two variants) ---------------------------------------------------------
leaf = Image.open(os.path.join(TX, "leaf_cluster.png")).convert("RGBA")
for k, ox in enumerate((256, 640)):
    tile = Image.new("RGBA", (384, 384), (30, 42, 22, 255))
    r2 = random.Random(31 + k)
    for _ in range(170):
        s = r2.randint(110, 190)
        lc = leaf.resize((s, s), Image.LANCZOS).rotate(r2.uniform(0, 360), resample=Image.BICUBIC)
        lc = ImageEnhance.Brightness(lc).enhance(r2.uniform(0.65, 1.05))
        x, yy = r2.randint(-s // 2, 384 - s // 2), r2.randint(-s // 2, 384 - s // 2)
        tile.alpha_composite(lc, (max(0, x), max(0, yy)), (max(0, -x), max(0, -yy)))
    atlas.paste(tile.convert("RGB"), (ox, 640))

atlas.save(OUT, quality=90)
print("wrote", OUT, atlas.size)

# --- pale stone for the square post: street-props/granite_dressed_light.jpg re-saved smaller --
stone = Image.open(os.path.join(TX, "street-props", "granite_dressed_light.jpg")).convert("RGB")
stone.save(os.path.join(TX, "street-details", "stone_pale.jpg"), quality=72)
print("wrote stone_pale.jpg")
