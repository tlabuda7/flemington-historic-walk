"""
prepare_block_40_46_textures.py - the one generated texture for the block at 40-46 Main St
(40-42 "Auto Sales", 44-46 "Shoe Shine & Fruits").

Usage:  python tools/prepare_block_40_46_textures.py
Output: assets/textures/block-40-46/signs_atlas.jpg (1024 x 1024, quality 88)

Nothing is downloaded: the atlas is drawn here with Pillow (original work). The red/cream
stripes are resampled from bank-building/awning_stripes.jpg (also generated, see
tools/prepare_bank_textures.py). Letters are set in fonts installed with Windows (rendered
into the image, no font file is shipped):
  - board "AUTO SALES"    Georgia Bold (georgiab.ttf), cream #E6DFCC on dark green #2F4A36
  - board "SHOES SHINED"  Georgia Bold (georgiab.ttf), dark #2A2622 on cream #DDD5BF
  - board "FRUITS"        Georgia Bold (georgiab.ttf), dark #2A2622 on cream #DDD5BF

Layout (pixels from the top-left; tools/blender/block_40_46_bake.py maps the UVs to these
boxes, REGIONS below is the single source of truth and is printed for checking):
  stripes  red/cream stripes running down the slope, 32 across the 5.45 m awning of 44-46
  louvre   one dark green shutter leaf (stiles, rails, louvre slats with shadows)
  canvas   plain cream canvas (awning cheeks, valance back)
  val      the same 32 stripes for the valance (lines up with the awning top), hem line
  auto     "AUTO SALES" board on the 42 porch fascia (4.00 x 0.50 m)
  shoes    "SHOES SHINED" board, north half of the 44-46 sign band (2.45 x 0.38 m)
  fruits   "FRUITS" board, south half (2.45 x 0.38 m)
  spare    plain canvas
Each lettered box is drawn at the sign's real proportions and then squeezed into its box.
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "textures" / "block-40-46"
OUT.mkdir(parents=True, exist_ok=True)
FONTS = Path(r"C:\Windows\Fonts")
SIZE = 1024
rnd = random.Random(4046)

# name: (col0, row0, col1, row1, metres wide, metres high)
REGIONS = {
    "stripes": (0, 0, 512, 384, None, None),
    "louvre":  (512, 0, 704, 384, None, None),
    "canvas":  (704, 0, 1024, 384, None, None),
    "val":     (0, 384, 1024, 448, None, None),
    "auto":    (0, 448, 1024, 576, 4.00, 0.50),
    "shoes":   (0, 576, 512, 672, 2.45, 0.38),
    "fruits":  (512, 576, 1024, 672, 2.45, 0.38),
    "spare":   (0, 672, 1024, 1024, None, None),
}
N_STRIPES = 32


def rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def canvas(w, h, base="#E2DACA"):
    """Cream canvas: fine weave, low-frequency soiling blotches."""
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
    src = Image.open(ROOT / "assets" / "textures" / "bank-building" / "awning_stripes.jpg").convert("RGB")
    tiles = N_STRIPES / 4
    strip = Image.new("RGB", (int(1024 * math.ceil(tiles)), 1024))
    for k in range(math.ceil(tiles)):
        strip.paste(src, (k * 1024, 0))
    strip = strip.crop((0, 0, int(1024 * tiles), 1024))
    return strip.resize((w, h), Image.LANCZOS)


def fit_text(draw, text, font_file, box_w, box_h, spacing=0.0):
    size = int(box_h * 1.6)
    while size > 6:
        font = ImageFont.truetype(str(FONTS / font_file), size)
        widths = [draw.textlength(ch, font=font) for ch in text]
        total = sum(widths) + spacing * size * (len(text) - 1)
        bb = font.getbbox("EHR")
        if total <= box_w and (bb[3] - bb[1]) <= box_h:
            return font, total
        size -= 1
    return font, total


def letters(img, text, font_file, colour, box, spacing=0.0):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    font, total = fit_text(d, text, font_file, x1 - x0, y1 - y0, spacing)
    bb = font.getbbox("EHR")
    cap_h = bb[3] - bb[1]
    y = (y0 + y1) / 2 - cap_h / 2 - bb[1]
    x = (x0 + x1) / 2 - total / 2
    for ch in text:
        d.text((x, y), ch, font=font, fill=colour)
        x += d.textlength(ch, font=font) + spacing * font.size


def board(w, h, ground, ink, edge, text, spacing):
    img = Image.new("RGB", (w, h), ground)
    d = ImageDraw.Draw(img)
    for y in range(0, h, 2):
        k = rnd.uniform(-4, 4)
        d.line([(0, y), (w, y)], fill=tuple(int(c + k) for c in ground))
    m = int(h * 0.08)
    d.rectangle([m, m, w - m, h - m], outline=edge, width=max(3, h // 40))
    letters(img, text, "georgiab.ttf", ink, (int(w * 0.07), int(h * 0.24), int(w * 0.93), int(h * 0.76)), spacing)
    noise = Image.effect_noise((w, h), 12).convert("L")
    return ImageChops.multiply(img, Image.merge("RGB", [noise.point(lambda v: 228 + v // 9)] * 3))


def sign(name, draw_fn):
    """Draw at the sign's real aspect (height = box height x 3), then squeeze into the box."""
    c0, r0, c1, r1, wm, hm = REGIONS[name]
    h = (r1 - r0) * 3
    w = int(round(h * wm / hm))
    atlas.paste(draw_fn(w, h).resize((c1 - c0, r1 - r0), Image.LANCZOS), (c0, r0))


def box(name):
    c0, r0, c1, r1 = REGIONS[name][:4]
    return c0, r0, c1 - c0, r1 - r0


def draw_louvre(w, h):
    base = rgb("#35503C")
    img = Image.new("RGB", (w, h), base)
    d = ImageDraw.Draw(img)
    st = int(w * 0.14)
    rail = int(h * 0.05)
    n = 26
    top, bot = rail, h - rail
    pitch = (bot - top) / n
    for k in range(n):
        y = top + k * pitch
        d.rectangle([st, y, w - st, y + pitch], fill=tuple(int(c * 0.92) for c in base))
        d.rectangle([st, y + pitch * 0.62, w - st, y + pitch], fill=tuple(int(c * 0.50) for c in base))
        d.line([(st, y + 1), (w - st, y + 1)], fill=tuple(min(255, int(c * 1.12)) for c in base), width=1)
    for x0, x1 in ((0, st), (w - st, w)):
        d.rectangle([x0, 0, x1, h], fill=base)
    d.rectangle([0, 0, w, rail], fill=base)
    d.rectangle([0, h - rail, w, h], fill=base)
    d.rectangle([0, h // 2 - rail // 2, w, h // 2 + rail // 2], fill=base)
    d.rectangle([st, 0, w - st, h], outline=tuple(int(c * 0.6) for c in base), width=2)
    noise = Image.effect_noise((w, h), 10).convert("L")
    return ImageChops.multiply(img, Image.merge("RGB", [noise.point(lambda v: 225 + v // 8)] * 3))


atlas = Image.new("RGB", (SIZE, SIZE))
for name in ("canvas", "spare"):
    c0, r0, w, h = box(name)
    atlas.paste(canvas(w, h), (c0, r0))
c0, r0, w, h = box("stripes")
atlas.paste(stripes(w, h), (c0, r0))
c0, r0, w, h = box("val")
val = stripes(w, h)
ImageDraw.Draw(val).line([(0, 3), (w, 3)], fill=(150, 120, 105), width=3)          # hem stitching
atlas.paste(val, (c0, r0))
c0, r0, w, h = box("louvre")
atlas.paste(draw_louvre(w, h), (c0, r0))
sign("auto", lambda w, h: board(w, h, rgb("#2F4A36"), rgb("#E6DFCC"), (200, 192, 170), "AUTO SALES", 0.30))
sign("shoes", lambda w, h: board(w, h, rgb("#DDD5BF"), rgb("#2A2622"), (60, 56, 50), "SHOES SHINED", 0.08))
sign("fruits", lambda w, h: board(w, h, rgb("#DDD5BF"), rgb("#2A2622"), (60, 56, 50), "FRUITS", 0.40))

out = OUT / "signs_atlas.jpg"
atlas.save(out, quality=88)
print(out, out.stat().st_size // 1024, "KB")
for k, v in REGIONS.items():
    print(k, v[:4])
