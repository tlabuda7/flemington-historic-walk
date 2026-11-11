"""
prepare_democrat_building_textures.py - the one generated texture for the Democrat building
(96-98 Main St).

Usage:  python tools/prepare_democrat_building_textures.py
Output: assets/textures/democrat-building/signs.jpg (1024 x 256, quality 90)

The whole image is the face of the "DEMOCRAT" sign board over the north door (1.05 x 0.24 m
on the building; tools/blender/democrat_building_bake.py maps the board's front face to the
full 0-1 UV square). Both Goodspeed photos (c. 1900 frontal, c. 1918) show a white board with
heavy dark slab-serif capitals that fill it almost from end to end.

Nothing is downloaded: drawn here with Pillow (original work). The word is set in Rockwell
Bold (ROCKB.TTF, installed with Windows / Office; Georgia Bold as a fallback) and rendered into
the image; no font file is shipped. The board is drawn at its real proportions and then
squeezed into the 4:1 image. The word is condensed sideways to fit the board, as the photo's
narrow letters do.
"""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "textures" / "democrat-building"
OUT.mkdir(parents=True, exist_ok=True)
FONTS = Path(r"C:\Windows\Fonts")
BOARD_W, BOARD_H = 1.05, 0.24          # metres
W, H = 1024, 256                       # output
SS = 4                                 # supersampling
BOARD = (0xE4, 0xDE, 0xCC)             # white paint, a little yellowed
INK = (0x24, 0x22, 0x1E)               # black paint, weathered
rnd = random.Random(96)

# draw at the board's real proportions
h = H * SS
w = round(h * BOARD_W / BOARD_H)
img = Image.new("RGB", (w, h), BOARD)
d = ImageDraw.Draw(img)

font_file = next(f for f in (FONTS / "ROCKB.TTF", FONTS / "georgiab.ttf") if f.exists())
TEXT = "DEMOCRAT"
cap_h = 0.60 * h                       # capitals about 0.145 m tall on the 0.24 m board
size = 10
while True:                            # font size whose capital height is cap_h
    f = ImageFont.truetype(str(font_file), size)
    b = f.getbbox("D")
    if b[3] - b[1] >= cap_h:
        break
    size += 4
font = f
# Set the word on its own strip, then condense it sideways to 88 % of the board: the photo's
# letters are a condensed slab serif (Rockwell Bold is wider), about 0.6 of the board tall.
widths = [font.getlength(c) for c in TEXT]
gap = 0.06 * cap_h
total = sum(widths) + gap * (len(TEXT) - 1)
strip = Image.new("L", (round(total) + 8, h), 0)
sd0 = ImageDraw.Draw(strip)
top = font.getbbox("D")[1]
x = 4.0
y = (h - cap_h) / 2 - top
for c, cw in zip(TEXT, widths):
    sd0.text((x, y), c, font=font, fill=255)
    x += cw + gap
strip = strip.crop(strip.getbbox())
tw = min(strip.size[0], round(0.88 * w))
strip = strip.resize((tw, strip.size[1]), Image.LANCZOS)
img.paste(Image.new("RGB", strip.size, INK), ((w - tw) // 2, round((h - strip.size[1]) / 2)), strip)

# thin dark edge line (the board's moulded rim in the photo)
e = round(0.012 / BOARD_H * h)
d.rectangle([0, 0, w - 1, h - 1], outline=(0x55, 0x50, 0x46), width=e)

img = img.resize((W, H), Image.LANCZOS)

# weathering: faint horizontal brush / grain lines and soft soiling, heavier along the bottom
shade = Image.new("L", (W, H), 255)
sd = ImageDraw.Draw(shade)
for _ in range(140):
    yy = rnd.randrange(H)
    x0 = rnd.randrange(W)
    sd.line([(x0, yy), (x0 + rnd.randrange(60, 400), yy)], fill=rnd.randrange(236, 250))
blot = Image.new("L", (W // 16, H // 16))
blot.putdata([rnd.randrange(225, 256) for _ in range((W // 16) * (H // 16))])
blot = blot.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
shade = ImageChops.multiply(shade, blot)
grad = Image.new("L", (1, H))
grad.putdata([255 - int(18 * max(0.0, (r / H - 0.6) / 0.4)) for r in range(H)])
shade = ImageChops.multiply(shade, grad.resize((W, H)))
img = ImageChops.multiply(img, Image.merge("RGB", [shade] * 3))

img.save(OUT / "signs.jpg", quality=90)
print("wrote", OUT / "signs.jpg", img.size, "font", font_file.name, "size", size)
