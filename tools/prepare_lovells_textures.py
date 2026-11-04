"""
prepare_lovells_textures.py - the one generated texture for Lovell's Restaurant (68 Main St).

Usage:  python tools/prepare_lovells_textures.py
Output: assets/textures/lovells-restaurant/signs_atlas.jpg (1024 x 1024, quality 88)
        assets/textures/lovells-restaurant/stone_bluestone.jpg (1024 x 1024, quality 85)

stone_bluestone.jpg (review round 1): polyhaven/concrete_floor_worn_001.jpg (Poly Haven
`concrete_floor_worn_001`, CC0), lightened so it averages the spec's pale weathered bluestone
#8E8C86 (the original averages ~#565654, too dark for the steps in Lovell's photo).

Nothing is downloaded: the atlas is drawn here with Pillow (original work). Letters are set
in fonts installed with Windows (rendered into a baked image, no font file is shipped):
  - valance "LOVELL'S RESTAURANT."  Bookman Old Style (BOOKOS.TTF), dark brown #3A2E26
  - board   "RESTAURANT"            Georgia Bold (georgiab.ttf), cream #E6DFCC on #5B5F55
  - board   "LOVELL'S"              Arial Bold (arialbd.ttf), black on white #EEEAE0
  - panel   "ICE CREAM"             Arial Bold (arialbd.ttf), white on dark #2E2A26

Layout (pixel rows from the top; lovells_restaurant_bake.py maps the UVs to these boxes,
REGIONS below is the single source of truth and is printed for checking):
  canvas     0 - 384   plain off-white awning canvas #E8E2D2, faint weave, soft soiling
  valance  384 - 512   same canvas, the lettering
  board    512 - 672   RESTAURANT sign board (5.45 x 0.42 m on the building)
  lovells  672 - 800   cols 0 - 512    LOVELL'S board (1.34 x 0.32 m)
  icecream 672 - 800   cols 512 - 1024 ICE CREAM panel (1.35 x 0.39 m)
  spare    800 - 1024  canvas (used for the awning cheeks and the valance back)
Each lettered box is drawn at the sign's real proportions and then squeezed into its box,
so on the building the letters come out with their natural shapes.
"""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "textures" / "lovells-restaurant"
OUT.mkdir(parents=True, exist_ok=True)
FONTS = Path(r"C:\Windows\Fonts")
SIZE = 1024
rnd = random.Random(68)

# name: (col0, row0, col1, row1, metres wide, metres high)
REGIONS = {
    "canvas":   (0, 0, 1024, 384, None, None),
    "valance":  (0, 384, 1024, 512, 5.80, 0.30),
    "board":    (0, 512, 1024, 672, 5.45, 0.42),
    "lovells":  (0, 672, 512, 800, 1.34, 0.32),
    "icecream": (512, 672, 1024, 800, 1.35, 0.39),
    "spare":    (0, 800, 1024, 1024, None, None),
}


def rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def canvas(w, h, base="#E8E2D2"):
    """Off-white canvas: fine weave (crossed thread lines), low-frequency soiling blotches."""
    img = Image.new("RGB", (w, h), rgb(base))
    d = ImageDraw.Draw(img)
    r0, g0, b0 = rgb(base)
    for y in range(0, h, 3):                     # weft
        k = rnd.uniform(-4, 2)
        d.line([(0, y), (w, y)], fill=(int(r0 + k), int(g0 + k), int(b0 + k - 1)))
    weave = Image.new("L", (w, h), 128)
    dw = ImageDraw.Draw(weave)
    for x in range(0, w, 3):                     # warp
        dw.line([(x, 0), (x, h)], fill=int(128 + rnd.uniform(-5, 3)))
    img = ImageChops.multiply(img, Image.merge("RGB", [weave.point(lambda v: min(255, v * 2))] * 3))
    # soft soiling: a few large faint brownish blotches
    soil = Image.new("L", (w, h), 0)
    ds = ImageDraw.Draw(soil)
    for _ in range(int(w * h / 9000)):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(12, 60)
        ds.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=int(rnd.uniform(10, 30)))
    soil = soil.filter(ImageFilter.GaussianBlur(18))
    dirt = Image.new("RGB", (w, h), (150, 132, 108))
    return Image.composite(dirt, img, soil)


def fit_text(draw, text, font_file, box_w, box_h, spacing=0.0):
    """Largest font size whose text (with extra letter spacing as a fraction of the size)
    fits box_w x box_h; returns (font, total width)."""
    size = int(box_h * 1.6)
    while size > 6:
        font = ImageFont.truetype(str(FONTS / font_file), size)
        widths = [draw.textlength(ch, font=font) for ch in text]
        total = sum(widths) + spacing * size * (len(text) - 1)
        bb = font.getbbox("ELR")
        if total <= box_w and (bb[3] - bb[1]) <= box_h:
            return font, total
        size -= 1
    return font, total


def letters(img, text, font_file, colour, box, spacing=0.0):
    """Draw `text` centred in box (x0, y0, x1, y1) of img, letters spaced individually."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    font, total = fit_text(d, text, font_file, x1 - x0, y1 - y0, spacing)
    bb = font.getbbox("ELR")
    cap_h = bb[3] - bb[1]
    y = (y0 + y1) / 2 - cap_h / 2 - bb[1]
    x = (x0 + x1) / 2 - total / 2
    for ch in text:
        d.text((x, y), ch, font=font, fill=colour)
        x += d.textlength(ch, font=font) + spacing * font.size


def sign(name, draw_fn, widen=1.0):
    """Draw at the sign's real aspect (height = box height x 3 for crisp letters), then squeeze.
    widen > 1 draws on a narrower sheet, so the letters come out that much wider on the sign."""
    c0, r0, c1, r1, wm, hm = REGIONS[name]
    h = (r1 - r0) * 3
    w = int(round(h * wm / hm / widen))
    img = draw_fn(w, h)
    img = img.resize((c1 - c0, r1 - r0), Image.LANCZOS)
    atlas.paste(img, (c0, r0))


atlas = Image.new("RGB", (SIZE, SIZE))
atlas.paste(canvas(1024, 384), (0, 0))
atlas.paste(canvas(1024, 224), (0, 800))


def draw_valance(w, h):
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    # stitched hem near the top edge and a faint seam above the scallops
    d.line([(0, int(h * 0.06)), (w, int(h * 0.06))], fill=(188, 178, 160), width=max(2, h // 60))
    d.line([(0, int(h * 0.72)), (w, int(h * 0.72))], fill=(205, 196, 178), width=max(2, h // 90))
    # letters in the flat band above the scallops (valance 0.30 m: letters 0.30 ... 0.86 of the height
    # from the bottom, i.e. image rows 0.14 ... 0.68)
    letters(img, "LOVELL'S RESTAURANT.", "BOOKOS.TTF", rgb("#3A2E26"),
            (int(w * 0.03), int(h * 0.13), int(w * 0.97), int(h * 0.66)), spacing=0.16)
    return img


def draw_board(w, h):
    img = Image.new("RGB", (w, h), rgb("#5B5F55"))
    d = ImageDraw.Draw(img)
    # weathered paint: faint horizontal brush streaks
    for y in range(0, h, 2):
        k = rnd.uniform(-5, 5)
        d.line([(0, y), (w, y)], fill=(int(0x5B + k), int(0x5F + k), int(0x55 + k)))
    # thin darker sunk border
    m = int(h * 0.07)
    d.rectangle([m, m, w - m, h - m], outline=(70, 73, 66), width=max(2, h // 45))
    letters(img, "RESTAURANT", "georgiab.ttf", rgb("#E6DFCC"),
            (int(w * 0.07), int(h * 0.18), int(w * 0.93), int(h * 0.82)), spacing=0.55)
    return img


def draw_lovells(w, h):
    img = Image.new("RGB", (w, h), rgb("#EEEAE0"))
    d = ImageDraw.Draw(img)
    m = int(h * 0.06)
    d.rectangle([m, m, w - m, h - m], outline=(30, 28, 26), width=max(3, h // 30))
    letters(img, "LOVELL'S", "arialbd.ttf", (22, 20, 18),
            (int(w * 0.07), int(h * 0.20), int(w * 0.93), int(h * 0.80)), spacing=0.06)
    return img


def draw_icecream(w, h):
    img = Image.new("RGB", (w, h), rgb("#2E2A26"))
    d = ImageDraw.Draw(img)
    m = int(h * 0.06)
    d.rectangle([m, m, w - m, h - m], outline=(90, 84, 76), width=max(3, h // 40))
    letters(img, "ICE CREAM", "arialbd.ttf", (236, 232, 222),
            (int(w * 0.08), int(h * 0.26), int(w * 0.92), int(h * 0.74)), spacing=0.08)
    return img


# lightened stone: scale each channel so the mean becomes #8E8C86, at 85 % contrast so the
# bright spots do not clip
from PIL import ImageStat
src = Image.open(ROOT / "assets" / "textures" / "polyhaven" / "concrete_floor_worn_001.jpg").convert("RGB")
means = ImageStat.Stat(src).mean
bands = []
for band_img, m, t in zip(src.split(), means, rgb("#8E8C86")):
    bands.append(band_img.point(lambda v, m=m, t=t: max(0, min(255, int(round(t * (1 + (v / m - 1) * 0.85)))))))
stone = Image.merge("RGB", bands)
stone.save(OUT / "stone_bluestone.jpg", quality=85)
print("stone_bluestone.jpg mean", [round(x) for x in ImageStat.Stat(stone).mean])

sign("valance", draw_valance, widen=1.35)          # wide letters, as in Lovell's photo
sign("board", draw_board)
sign("lovells", draw_lovells)
sign("icecream", draw_icecream)
out = OUT / "signs_atlas.jpg"
atlas.save(out, quality=88)
print(out, out.stat().st_size // 1024, "KB")
for k, v in REGIONS.items():
    print(k, v)
