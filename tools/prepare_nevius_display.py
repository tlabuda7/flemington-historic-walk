"""
prepare_nevius_display.py - Nevius-only 1K atlas for the 3D shop-window displays trial
(78 Main St; PLAN.md "Window displays trial (owner, 2026-11-11)").

    python tools/prepare_nevius_display.py

Reads the shared assets/textures/shared/shop_interior.jpg (NOT modified; 4 other buildings
use it) and writes assets/textures/nevius-store/shop_display.jpg (1024 x 1024) + .json:
  - transom, transom_door: copied pixel for pixel from shop_interior.jpg
  - store_back: shop_a + shop_b side by side, resized to 1024 x 576 (the 5.8 x 3.3 m back
    wall of the short store space behind the displays), lifted (gamma 0.5; see below)
  - one 128 px swatch per goods colour (+ floor_cloth): flat colour with a faint weave
    noise; nothing lettered.
Cell UVs in the .json use the Blender/glTF-before-flip convention (v = 0 at the bottom),
like shop_interior.json. Pillow only. Own work (derived from own work), logged in SOURCES.md.
"""

import json
import math
import os
import random
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "textures", "shared", "shop_interior")
OUT = os.path.join(ROOT, "assets", "textures", "nevius-store", "shop_display")
S = 1024

src = Image.open(SRC + ".jpg").convert("RGB")
src_cells = json.load(open(SRC + ".json"))["cells"]
atlas = Image.new("RGB", (S, S), (20, 18, 16))
cells = {}


def put(name, img, x, y):
    atlas.paste(img, (x, y))
    w, h = img.size
    cells[name] = {"px": [x, y, w, h], "uv": [x / S, 1 - (y + h) / S, (x + w) / S, 1 - y / S]}


def crop(name):
    x, y, w, h = src_cells[name]["px"]
    return src.crop((x, y, x + w, y + h))


# store_back: shop_a + shop_b side by side, recomposed so the deep aisle of shop_a (its
# vanishing point, x ~360 of 600, at eye height) sits right behind the glazed door
# (u 0.58 of the 5.84 m back wall), and without the window mullion painted into the
# pictures (shop_a x 530 ... shop_b x 40). Left strip: shop_b mirrored (near shelving).
a, b = crop("shop_a"), crop("shop_b")
k = 576 / a.height
A = a.crop((100, 0, 530, a.height)).resize((round(430 * k), 576), Image.LANCZOS)   # without the post at the left
B = b.crop((40, 0, b.width, b.height)).resize((round((b.width - 40) * k), 576), Image.LANCZOS)
x_a = round(0.58 * S - 260 * k)
both = Image.new("RGB", (S, 576))
both.paste(B.transpose(Image.FLIP_LEFT_RIGHT), (x_a - B.width, 0))
both.paste(A, (x_a, 0))
both.paste(B, (x_a + A.width, 0))
# The pictures are pre-lit renders of a dim store (sRGB ~30-60). On the back wall 1.5 m into the
# dim store space (lightmap ~0.3-0.5) the planned 15 % darkening left them black behind the
# glass's sky reflection, so they are LIFTED instead (gamma 0.5: 45 -> 107, 220 -> 237).
both = both.point(lambda c: round(255 * (c / 255) ** 0.5))
put("store_back", both, 0, 0)
put("transom", crop("transom"), 0, 576)
put("transom_door", crop("transom_door"), 0, 656)

SWATCHES = {
    "floor_cloth": "#7A6F5E", "form_white": "#E6E0D2", "form_cream": "#D9CFB8", "navy_serge": "#2E3448",
    "linen_white": "#E9E5DC", "bolt_brown": "#6B4E35", "bolt_grey": "#8A8780", "bolt_green": "#3E4F3C",
    "straw": "#CDBB8E", "hat_band": "#2A2420", "muslin": "#E2DACA", "chambray": "#8FA3B8",
    "card_box": "#8C7D68", "wood_dark": "#4A3628",
}
rng = random.Random(78)
SW = 128
for i, (name, hexc) in enumerate(SWATCHES.items()):
    base = [int(hexc[k:k + 2], 16) for k in (1, 3, 5)]
    img = Image.new("RGB", (SW, SW))
    px = img.load()
    for y in range(SW):
        for x in range(SW):
            # faint plain weave (warp/weft threads ~2 px) + a little grain
            weave = 0.025 * math.sin(x * math.pi / 2) * math.sin(y * math.pi / 2)
            f = 1.0 + weave + rng.uniform(-0.02, 0.02)
            px[x, y] = tuple(max(0, min(255, round(c * f))) for c in base)
    put(name, img, (i % 8) * SW, 704 + (i // 8) * SW)

atlas.save(OUT + ".jpg", quality=90)
json.dump({"size": S, "inset_px": 4,
           "note": "px = [x, y, w, h], row 0 at the top; uv = [u0, v0, u1, v1], v = 0 at the bottom. "
                   "Nevius Store displays trial (tools/blender/nevius_store.py). Goods UVs sit inside "
                   "their swatch cell with a 4 px inset.",
           "cells": cells}, open(OUT + ".json", "w"), indent=1)
print("wrote", OUT + ".jpg", atlas.size, len(cells), "cells")
