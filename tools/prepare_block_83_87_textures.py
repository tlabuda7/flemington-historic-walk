"""
prepare_block_83_87_textures.py - draws the one texture the 83-87 Main St grocery needs that
does not exist yet: `assets/textures/block-83-87/shutter_louvres.jpg`, a closed louvred
shutter leaf (stiles, top / middle / bottom rails, fixed louvres with a light upper edge and a
shadow under each slat), painted the card's toned-down green (about #5F7F62).

Own work: the paint grain is the existing CC0 map `assets/textures/polyhaven/door_paint_green.jpg`
(Poly Haven "door paint green", already logged in SOURCES.md), re-tinted; the louvre pattern
is drawn here. No download, no lettering.

Run with the normal Python (Pillow):  python tools/prepare_block_83_87_textures.py

UV layout used by tools/blender/block_83_87.py: the whole image = one leaf (u across, v up);
the left stile (u < 0.12) is plain paint and also serves the leaf edges.
"""

import os
from PIL import Image, ImageChops, ImageDraw, ImageFilter

PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
SRC = os.path.join(PROJECT, "assets", "textures", "polyhaven", "door_paint_green.jpg")
OUT_DIR = os.path.join(PROJECT, "assets", "textures", "block-83-87")
OUT = os.path.join(OUT_DIR, "shutter_louvres.jpg")
W, H = 256, 1024                      # a leaf is about 0.45 x 1.75 m
TARGET = (0x5F, 0x7F, 0x62)
SRC_AVG = (93, 107, 92)

os.makedirs(OUT_DIR, exist_ok=True)

# painted grain: the Poly Haven paint map, tinted to the target green
grain = Image.open(SRC).convert("RGB").resize((W, H), Image.LANCZOS)
r, g, b = grain.split()
tinted = Image.merge("RGB", [ch.point(lambda v, k=t / a: min(255, int(v * k)))
                             for ch, t, a in zip((r, g, b), TARGET, SRC_AVG)])

# light / shade pattern (128 = unchanged)
shade = Image.new("L", (W, H), 128)
d = ImageDraw.Draw(shade)
STILE = int(W * 0.12)
RAIL_T, RAIL_M, RAIL_B = int(H * 0.06), int(H * 0.035), int(H * 0.08)
mid = H // 2
# panel openings (between stiles and rails) are recessed: dark rim
openings = [(STILE, RAIL_T, W - STILE, mid - RAIL_M), (STILE, mid + RAIL_M, W - STILE, H - RAIL_B)]
for x0, y0, x1, y1 in openings:
    d.rectangle((x0, y0, x1, y1), fill=96)                     # shadowed back of the opening
    pitch = 22                                                 # louvre pitch, px (about 4 cm)
    y = y0 + 3
    while y + pitch <= y1 - 2:
        # one slat: bright upper edge, face shading down, dark gap under it
        d.rectangle((x0 + 2, y, x1 - 2, y + 2), fill=178)
        for k in range(3, pitch - 6):
            d.line((x0 + 2, y + k, x1 - 2, y + k), fill=int(160 - 40 * k / pitch))
        d.rectangle((x0 + 2, y + pitch - 6, x1 - 2, y + pitch - 1), fill=58)
        y += pitch
    # stile / rail edges: highlight on the upper and left inner edge, shadow on the other two
    d.line((x0, y0, x1, y0), fill=70, width=3)
    d.line((x0, y0, x0, y1), fill=84, width=3)
    d.line((x1, y0, x1, y1), fill=150, width=2)
    d.line((x0, y1, x1, y1), fill=156, width=2)
# outer edge of the leaf: thin dark line (gap to the neighbour leaf / frame)
d.rectangle((0, 0, W - 1, H - 1), outline=72, width=2)
shade = shade.filter(ImageFilter.GaussianBlur(0.8))

# apply: out = tinted * shade / 128 (multiply darkens; shade 128 -> factor 1)
lut = [min(255, int(i * 2)) for i in range(256)]
light = shade.point(lut)                                       # 128 -> 255
out = ImageChops.multiply(tinted, Image.merge("RGB", [light] * 3))
# shade above 128 is clipped by the multiply: add those highlights separately
hi = shade.point(lambda v: max(0, v - 128) * 2)
out = ImageChops.add(out, Image.merge("RGB", [hi.point(lambda v: v // 3)] * 3))
out.save(OUT, quality=90)
avg = out.resize((1, 1), Image.BOX).getpixel((0, 0))
print("wrote", OUT, out.size, "average", avg)
