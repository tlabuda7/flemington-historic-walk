"""
prepare_rea_textures.py - the one generated texture for the Rea Building / "Clock Tower
Building" (48-52 Main St).

Usage:  python tools/prepare_rea_textures.py
Output: assets/textures/rea-building/signs_atlas.jpg (1024 x 1024, quality 88)

Nothing is downloaded: the atlas is drawn here with Pillow (original work). The red/cream
stripes are resampled from bank-building/awning_stripes.jpg (also generated, see
tools/prepare_bank_textures.py). Letters are set in fonts installed with Windows (rendered
into the image, no font file is shipped):
  - valance "GREEN'S APOTHECARY"  Bookman Old Style (BOOKOS.TTF), dark brown #3A2E26 on cream
  - board   "JEWELER"             Georgia Bold (georgiab.ttf), gold-cream #E3CF9A on black
  - board   "SHOES REPAIRED"      Georgia Bold (georgiab.ttf), cream #E6DFCC on dark green #2F4232
  - clock numerals                Times New Roman (times.ttf), black

Layout (pixels from the top-left; rea_building_bake.py maps the UVs to these boxes,
REGIONS below is the single source of truth and is printed for checking):
  canvas48  plain cream canvas #E2DACA (awning 48: top, underside, cheeks)
  stripes   red/cream stripes running down the slope, 32 stripes across the 4.90 m awning (52)
  val48     scalloped valance strip, "GREEN'S APOTHECARY" (4.90 x 0.25 m)
  val52     the same 32 stripes for the striped valance (lines up with the awning top)
  dial      clock dial: white face, black Roman numerals and minute ring, hands at ~4:50
  louvre    one shutter leaf: pale drab stiles and rails, horizontal louvre slats with shadows
  dentil    1.20 m of dentil course (8 dentils at 0.15 m), 0.15 m tall
  jeweler   "JEWELER" sign board (2.80 x 0.40 m)
  shoes     "SHOES REPAIRED" board (1.10 x 0.30 m)
  spare     plain canvas (valance backs, spare)
Each lettered box is drawn at the sign's real proportions and then squeezed into its box,
so on the building the letters come out with their natural shapes.
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "textures" / "rea-building"
OUT.mkdir(parents=True, exist_ok=True)
FONTS = Path(r"C:\Windows\Fonts")
SIZE = 1024
rnd = random.Random(50)

# name: (col0, row0, col1, row1, metres wide, metres high)
REGIONS = {
    "canvas48": (0, 0, 512, 320, None, None),
    "stripes":  (512, 0, 1024, 320, None, None),
    "val48":    (0, 320, 1024, 416, 4.90, 0.25),
    "val52":    (0, 416, 1024, 480, None, None),
    "dial":     (0, 480, 384, 864, None, None),
    "louvre":   (384, 480, 576, 864, None, None),
    "dentil":   (576, 480, 1024, 544, 1.20, 0.15),
    "jeweler":  (576, 544, 1024, 640, 2.80, 0.40),
    "shoes":    (576, 640, 1024, 736, 1.10, 0.30),
    "spare":    (576, 736, 1024, 864, None, None),
    "spare2":   (0, 864, 1024, 1024, None, None),
}
N_STRIPES = 32


def rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def canvas(w, h, base="#E2DACA"):
    """Cream canvas: fine weave (crossed thread lines), low-frequency soiling blotches."""
    img = Image.new("RGB", (w, h), rgb(base))
    d = ImageDraw.Draw(img)
    r0, g0, b0 = rgb(base)
    for y in range(0, h, 3):
        k = rnd.uniform(-4, 2)
        d.line([(0, y), (w, y)], fill=(int(r0 + k), int(g0 + k), int(b0 + k - 1)))
    weave = Image.new("L", (w, h), 128)
    dw = ImageDraw.Draw(weave)
    for x in range(0, w, 3):
        dw.line([(x, 0), (x, h)], fill=int(128 + rnd.uniform(-5, 3)))
    img = ImageChops.multiply(img, Image.merge("RGB", [weave.point(lambda v: min(255, v * 2))] * 3))
    soil = Image.new("L", (w, h), 0)
    ds = ImageDraw.Draw(soil)
    for _ in range(int(w * h / 9000)):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(12, 60)
        ds.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=int(rnd.uniform(8, 24)))
    soil = soil.filter(ImageFilter.GaussianBlur(18))
    dirt = Image.new("RGB", (w, h), (150, 132, 108))
    return Image.composite(dirt, img, soil)


def stripes(w, h):
    """N_STRIPES red/cream stripes across w, running down (resampled from the bank's awning
    texture: 1024 px there = 4 stripes)."""
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


def sign(name, draw_fn, widen=1.0):
    """Draw at the sign's real aspect (height = box height x 3), then squeeze into the box."""
    c0, r0, c1, r1, wm, hm = REGIONS[name]
    h = (r1 - r0) * 3
    w = int(round(h * wm / hm / widen))
    img = draw_fn(w, h)
    atlas.paste(img.resize((c1 - c0, r1 - r0), Image.LANCZOS), (c0, r0))


def box(name):
    c0, r0, c1, r1 = REGIONS[name][:4]
    return c0, r0, c1 - c0, r1 - r0


atlas = Image.new("RGB", (SIZE, SIZE))
for name in ("canvas48", "spare", "spare2"):
    c0, r0, w, h = box(name)
    atlas.paste(canvas(w, h), (c0, r0))
c0, r0, w, h = box("stripes")
atlas.paste(stripes(w, h), (c0, r0))
c0, r0, w, h = box("val52")
v52 = stripes(w, h)
dv = ImageDraw.Draw(v52)
dv.line([(0, 3), (w, 3)], fill=(150, 120, 105), width=3)        # hem stitching
atlas.paste(v52, (c0, r0))


def draw_val48(w, h):
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    d.line([(0, int(h * 0.06)), (w, int(h * 0.06))], fill=(186, 176, 158), width=max(2, h // 60))
    d.line([(0, int(h * 0.74)), (w, int(h * 0.74))], fill=(204, 195, 177), width=max(2, h // 90))
    # letters in the flat band above the scallops (top 0.12 ... 0.68 of the height)
    letters(img, "GREEN'S APOTHECARY", "BOOKOS.TTF", rgb("#3A2E26"),
            (int(w * 0.04), int(h * 0.14), int(w * 0.96), int(h * 0.66)), spacing=0.14)
    return img


def draw_jeweler(w, h):
    img = Image.new("RGB", (w, h), (24, 22, 20))
    d = ImageDraw.Draw(img)
    for y in range(0, h, 2):
        k = rnd.uniform(-4, 4)
        d.line([(0, y), (w, y)], fill=(int(24 + k), int(22 + k), int(20 + k)))
    m = int(h * 0.08)
    d.rectangle([m, m, w - m, h - m], outline=(170, 150, 100), width=max(3, h // 40))
    letters(img, "JEWELER", "georgiab.ttf", rgb("#E3CF9A"),
            (int(w * 0.12), int(h * 0.22), int(w * 0.88), int(h * 0.78)), spacing=0.45)
    return img


def draw_shoes(w, h):
    img = Image.new("RGB", (w, h), rgb("#2F4232"))
    d = ImageDraw.Draw(img)
    for y in range(0, h, 2):
        k = rnd.uniform(-4, 4)
        d.line([(0, y), (w, y)], fill=(int(0x2F + k), int(0x42 + k), int(0x32 + k)))
    m = int(h * 0.07)
    d.rectangle([m, m, w - m, h - m], outline=(200, 192, 170), width=max(3, h // 40))
    letters(img, "SHOES REPAIRED", "georgiab.ttf", rgb("#E6DFCC"),
            (int(w * 0.07), int(h * 0.24), int(w * 0.93), int(h * 0.76)), spacing=0.10)
    return img


def draw_dentil(w, h):
    """8 dentils across: pale blocks, dark gaps (shadow), a lighter top fillet."""
    base = rgb("#B5AC98")
    img = Image.new("RGB", (w, h), tuple(int(c * 0.42) for c in base))
    d = ImageDraw.Draw(img)
    pitch = w / 8
    dw = pitch * 0.55
    for k in range(8):
        x0 = k * pitch + (pitch - dw) / 2
        d.rectangle([x0, h * 0.18, x0 + dw, h * 0.95], fill=base)
        d.rectangle([x0, h * 0.86, x0 + dw, h * 0.95], fill=tuple(int(c * 0.78) for c in base))   # underside shade
        d.rectangle([x0 + dw * 0.86, h * 0.18, x0 + dw, h * 0.95], fill=tuple(int(c * 0.84) for c in base))
    d.rectangle([0, 0, w, h * 0.16], fill=tuple(int(c * 1.03) for c in base))                       # fillet above
    d.line([(0, h * 0.16), (w, h * 0.16)], fill=tuple(int(c * 0.6) for c in base), width=max(2, int(h * 0.03)))
    return img


def draw_louvre(w, h):
    base = rgb("#C2B9A4")
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
        d.rectangle([st, y + pitch * 0.62, w - st, y + pitch], fill=tuple(int(c * 0.55) for c in base))   # shadow under slat
        d.line([(st, y + 1), (w - st, y + 1)], fill=tuple(min(255, int(c * 1.04)) for c in base), width=1)
    # stiles and rails with a thin dark edge line
    for x0, x1 in ((0, st), (w - st, w)):
        d.rectangle([x0, 0, x1, h], fill=base)
    d.rectangle([0, 0, w, rail], fill=base)
    d.rectangle([0, h - rail, w, h], fill=base)
    d.rectangle([0, h // 2 - rail // 2, w, h // 2 + rail // 2], fill=base)                 # mid rail
    d.rectangle([st, 0, w - st, h], outline=tuple(int(c * 0.7) for c in base), width=2)
    noise = Image.effect_noise((w, h), 10).convert("L")
    return ImageChops.multiply(img, Image.merge("RGB", [noise.point(lambda v: 225 + v // 8)] * 3))


def draw_dial(s):
    """White dial with a black rim, minute ring, Roman numerals (IIII), hands at ~4:50."""
    sc = 3
    S = s * sc
    img = Image.new("RGB", (S, S), (30, 30, 30))
    d = ImageDraw.Draw(img)
    c = S / 2
    R = S / 2
    d.ellipse([c - R * 0.97, c - R * 0.97, c + R * 0.97, c + R * 0.97], fill=(236, 233, 222))
    # minute ring: two circles and ticks
    for rr in (0.86, 0.78):
        d.ellipse([c - R * rr, c - R * rr, c + R * rr, c + R * rr], outline=(20, 20, 20), width=int(S * 0.006))
    for m in range(60):
        a = math.radians(m * 6)
        r0, r1 = R * 0.78, R * (0.86 if m % 5 == 0 else 0.82)
        d.line([(c + r0 * math.sin(a), c - r0 * math.cos(a)), (c + r1 * math.sin(a), c - r1 * math.cos(a))],
               fill=(20, 20, 20), width=int(S * (0.010 if m % 5 == 0 else 0.005)))
    font = ImageFont.truetype(str(FONTS / "times.ttf"), int(S * 0.105))
    nums = ["XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
    for k, t in enumerate(nums):
        a = k * 30
        tw = int(d.textlength(t, font=font)) + 8
        th = int(S * 0.13)
        tile = Image.new("L", (tw, th), 0)
        ImageDraw.Draw(tile).text((tw / 2, th / 2), t, font=font, fill=255, anchor="mm")
        tile = tile.rotate(-a, expand=True, resample=Image.BICUBIC)
        r = R * 0.64
        px = c + r * math.sin(math.radians(a)) - tile.width / 2
        py = c - r * math.cos(math.radians(a)) - tile.height / 2
        img.paste((15, 15, 15), (int(px), int(py)), tile)

    def hand(angle_deg, length, width, tail):
        a = math.radians(angle_deg)
        ux, uy = math.sin(a), -math.cos(a)
        nx, ny = -uy, ux
        pts = [(c - ux * tail * R + nx * width * R, c - uy * tail * R + ny * width * R),
               (c + ux * length * R * 0.8 + nx * width * R * 1.6, c + uy * length * R * 0.8 + ny * width * R * 1.6),
               (c + ux * length * R, c + uy * length * R),
               (c + ux * length * R * 0.8 - nx * width * R * 1.6, c + uy * length * R * 0.8 - ny * width * R * 1.6),
               (c - ux * tail * R - nx * width * R, c - uy * tail * R - ny * width * R)]
        d.polygon(pts, fill=(12, 12, 12))

    hand((4 + 50 / 60) * 30, 0.48, 0.022, 0.10)        # hour hand
    hand(50 * 6, 0.74, 0.014, 0.14)                    # minute hand
    d.ellipse([c - R * 0.04, c - R * 0.04, c + R * 0.04, c + R * 0.04], fill=(12, 12, 12))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    return img.resize((s, s), Image.LANCZOS)


sign("val48", draw_val48, widen=1.2)
sign("jeweler", draw_jeweler)
sign("shoes", draw_shoes)
sign("dentil", draw_dentil)
c0, r0, w, h = box("dial")
atlas.paste(draw_dial(w), (c0, r0))
c0, r0, w, h = box("louvre")
atlas.paste(draw_louvre(w, h), (c0, r0))

out = OUT / "signs_atlas.jpg"
atlas.save(out, quality=88)
print(out, out.stat().st_size // 1024, "KB")
for k, v in REGIONS.items():
    print(k, v[:4])
