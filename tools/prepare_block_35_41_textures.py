"""
prepare_block_35_41_textures.py - the two new textures for the block at 35-41 Main St
(35-37 frame "Gro." with the two-tier porch, 39-41 brick "Cobbler").

Usage:  python tools/prepare_block_35_41_textures.py
Output: assets/textures/block-35-41/trim_stone_grey.jpg  (1024 x 1024, quality 85)
        assets/textures/block-35-41/signs_atlas.jpg      (1024 x 1024, quality 88)

Nothing is downloaded.
  trim_stone_grey.jpg  re-tint of polyhaven/trim_paint_cream.jpg (Poly Haven
                       `painted_plaster_wall`, CC0) to the spec's mid stone-grey #A39A88
                       (trim darker than the walls in both photos). Tile 2.0 m.
  signs_atlas.jpg      drawn here with Pillow (original work). Stripes resampled from the
                       generated bank-building/awning_stripes.jpg; the shutter leaf is the
                       County Hotel's louvre cell copied unchanged from
                       county-hotel/signs_atlas.jpg (tools/prepare_county_hotel_textures.py).
                       Valance letters set in Bookman Old Style Bold (BOOKOSB.TTF, installed
                       with Windows; rendered into the image, no font file is shipped).

Atlas layout (pixels from the top-left; REGIONS is the single source of truth, printed):
  stripes  awning top: 42 red/cream stripes across the 6.40 m width (X -0.47 .. +5.93),
           stripes run down the slope (image top = Y 0 under the deck, bottom = Y -1.30)
  val_s    valance, SOUTH half X -0.47 .. +2.73 (3.20 x 0.25 m), image left = south
  val_n    valance, NORTH half X +2.73 .. +5.93 (3.20 x 0.25 m), image left = south
           Whole valance reads "PRODUCE | JACOB R. HALL | GROCER" from south to north
           (left to right seen from the street). Top of each box = Z 2.50, bottom = Z 2.25.
           The lettering sits in the top 70%; the bottom carries a scalloped hem line with a
           0.15 m period (scallop points at X -0.47 + k*0.15) so a scallop-cut edge matches.
  louvre   one dark green louvred shutter leaf (County Hotel cell, 256 x 640)
  canvas   plain cream canvas (awning cheeks, valance back)
  green    plain dark green (shutter edges and backs)
  spare    plain canvas
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops, ImageOps

ROOT = Path(__file__).resolve().parent.parent
TX = ROOT / "assets" / "textures"
OUT = TX / "block-35-41"
OUT.mkdir(parents=True, exist_ok=True)
FONTS = Path(r"C:\Windows\Fonts")
SIZE = 1024
rnd = random.Random(3541)

REGIONS = {
    "stripes": (0, 0, 768, 384),
    "louvre":  (768, 0, 1024, 640),
    "val_s":   (0, 384, 768, 512),
    "val_n":   (0, 512, 768, 640),
    "canvas":  (0, 640, 768, 1024),
    "green":   (768, 640, 1024, 832),
    "spare":   (768, 832, 1024, 1024),
}
N_STRIPES = 42                       # 6.40 m / 42 = 0.152 m, as the bank's 0.15 m stripes
VAL_W, VAL_H = 6.40, 0.25            # metres
PANELS = [("PRODUCE", 1.80), ("JACOB R. HALL", 2.80), ("GROCER", 1.80)]   # south -> north
INK = (0x2A, 0x26, 0x22)
VAL_GROUND = "#DDD3BC"               # the bank stripes' cream


def rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def tint(image, color, contrast=1.0):
    """As tools/prepare_textures.py: keep the light/dark variation, new paint colour."""
    grey = ImageOps.grayscale(image)
    mean = sum(i * n for i, n in enumerate(grey.histogram())) / (grey.width * grey.height)
    r, g, b = rgb(color)

    def channel(c):
        return grey.point(lambda v: max(0, min(255, int(c * (1 + (v / mean - 1) * contrast)))))
    return Image.merge("RGB", (channel(r), channel(g), channel(b)))


def noisy(img, amount):
    noise = Image.effect_noise(img.size, amount).convert("L")
    return ImageChops.multiply(img, Image.merge("RGB", [noise.point(lambda v: 225 + v // 8)] * 3))


def canvas(w, h, base="#E2DACA"):
    """Cream canvas: fine weave, low-frequency soiling blotches (as block 40-46)."""
    img = Image.new("RGB", (w, h), rgb(base))
    d = ImageDraw.Draw(img)
    r0, g0, b0 = rgb(base)
    for y in range(0, h, 3):
        k = rnd.uniform(-4, 2)
        d.line([(0, y), (w, y)], fill=(int(r0 + k), int(g0 + k), int(b0 + k - 1)))
    soil = Image.new("L", (w, h), 0)
    ds = ImageDraw.Draw(soil)
    for _ in range(int(w * h / 9000) + 1):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(12, 60)
        ds.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=int(rnd.uniform(8, 24)))
    soil = soil.filter(ImageFilter.GaussianBlur(18))
    dirt = Image.new("RGB", (w, h), (150, 132, 108))
    return Image.composite(dirt, img, soil)


def stripes(w, h):
    """N_STRIPES red/cream stripes across w, running down (bank texture: 1024 px = 4 stripes)."""
    src = Image.open(TX / "bank-building" / "awning_stripes.jpg").convert("RGB")
    tiles = N_STRIPES / 4
    strip = Image.new("RGB", (int(1024 * math.ceil(tiles)), 1024))
    for k in range(math.ceil(tiles)):
        strip.paste(src, (k * 1024, 0))
    strip = strip.crop((0, 0, int(1024 * tiles), 1024))
    return strip.resize((w, h), Image.LANCZOS)


def valance():
    """Whole 6.40 x 0.25 m valance at real aspect (H px tall), lettered in three panels."""
    H = 384
    W = int(round(H * VAL_W / VAL_H))
    px = W / VAL_W
    img = canvas(W, H, VAL_GROUND)
    d = ImageDraw.Draw(img)
    edge = (95, 80, 66)
    text_bot = int(H * 0.72)
    d.line([(0, int(H * 0.05)), (W, int(H * 0.05))], fill=edge, width=6)        # top hem
    # scalloped hem line, period 0.15 m, points at k*0.15 m from the south end
    per = 0.15 * px
    pts = []
    for i in range(int(W / per * 24) + 1):
        x = i * per / 24
        t = (x % per) / per
        pts.append((x, H * 0.80 + H * 0.12 * math.sin(math.pi * t)))
    d.line(pts, fill=edge, width=6)
    font_file = str(FONTS / "BOOKOSB.TTF")
    x = 0.0
    for k, (text, wm) in enumerate(PANELS):
        x0, x1 = x * px, (x + wm) * px
        if k:
            d.line([(x0, int(H * 0.05)), (x0, text_bot + int(H * 0.06))], fill=edge, width=8)
        box_w, box_h = (x1 - x0) * 0.84, (text_bot - H * 0.15)
        size = int(box_h * 1.6)
        while size > 8:
            font = ImageFont.truetype(font_file, size)
            spacing = 0.10 * size
            total = sum(d.textlength(ch, font=font) for ch in text) + spacing * (len(text) - 1)
            bb = font.getbbox("EHR")
            if total <= box_w and bb[3] - bb[1] <= box_h:
                break
            size -= 2
        cap = bb[3] - bb[1]
        y = (H * 0.15 + text_bot) / 2 - cap / 2 - bb[1]
        cx = (x0 + x1) / 2 - total / 2
        for ch in text:
            d.text((cx, y), ch, font=font, fill=INK)
            cx += d.textlength(ch, font=font) + spacing
        x += wm
    img = img.filter(ImageFilter.GaussianBlur(1.2))                              # slightly soft paint
    return noisy(img, 10)


def box(name):
    c0, r0, c1, r1 = REGIONS[name]
    return c0, r0, c1 - c0, r1 - r0


# 1. trim tint
trim = tint(Image.open(TX / "polyhaven" / "trim_paint_cream.jpg").convert("RGB"), "#A39A88", 1.0)
trim.save(OUT / "trim_stone_grey.jpg", quality=85)

# 2. atlas
atlas = Image.new("RGB", (SIZE, SIZE))
for name in ("canvas", "spare"):
    c0, r0, w, h = box(name)
    atlas.paste(canvas(w, h), (c0, r0))
c0, r0, w, h = box("stripes")
atlas.paste(stripes(w, h), (c0, r0))
val = valance()
half = val.width // 2
for name, part in (("val_s", val.crop((0, 0, half, val.height))),
                   ("val_n", val.crop((half, 0, val.width, val.height)))):
    c0, r0, w, h = box(name)
    atlas.paste(part.resize((w, h), Image.LANCZOS), (c0, r0))
hotel = Image.open(TX / "county-hotel" / "signs_atlas.jpg").convert("RGB")
c0, r0, w, h = box("louvre")
atlas.paste(hotel.crop((0, 0, 256, 640)).resize((w, h), Image.LANCZOS), (c0, r0))
c0, r0, w, h = box("green")
atlas.paste(noisy(Image.new("RGB", (w, h), (44, 56, 39)), 8), (c0, r0))

out = OUT / "signs_atlas.jpg"
atlas.save(out, quality=88)
for f in (OUT / "trim_stone_grey.jpg", out):
    print(f, f.stat().st_size // 1024, "KB")
for k, v in REGIONS.items():
    print(k, v)
