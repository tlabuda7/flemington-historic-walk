"""
prepare_palace_theatre_textures.py - the one generated texture for the Palace Theatre (31 Main St).

Usage:  python tools/prepare_palace_theatre_textures.py
Output: assets/textures/palace-theatre/signs_atlas.jpg (1024 x 1024, quality 88)

Nothing is downloaded: the atlas is drawn here with Pillow (original work). Owner decision
2026-11-08: only two GENERIC poster frames, with no invented film titles and no lettering at all.
Each poster is a faded one-sheet layout: a coloured border, a pictorial panel of plain shapes
and grey bars standing in for print (unreadable at any distance, no letters).

Layout (pixels from the top-left; tools/blender/palace_theatre_bake.py maps the UVs to these
boxes, REGIONS below is the single source of truth):
  poster1  generic poster in the frame on the pier south of the entrance (0.56 x 0.94 m)
  poster2  generic poster in the frame on the north corner pier (0.56 x 0.94 m)
  spare    plain paper
"""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "textures" / "palace-theatre"
OUT.mkdir(parents=True, exist_ok=True)
SIZE = 1024
rnd = random.Random(518)

REGIONS = {
    "poster1": (0, 0, 512, 860),
    "poster2": (512, 0, 1024, 860),
    "spare":   (0, 860, 1024, 1024),
}


def rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def paper(w, h, base):
    img = Image.new("RGB", (w, h), rgb(base))
    px = img.load()
    for y in range(h):
        for x in range(w):
            n = rnd.randint(-7, 7)
            r, g, b = px[x, y]
            px[x, y] = (max(0, r + n), max(0, g + n), max(0, b + n))
    # low-frequency fading / soiling
    blot = Image.new("L", (w // 16 + 1, h // 16 + 1))
    bp = blot.load()
    for y in range(blot.height):
        for x in range(blot.width):
            bp[x, y] = rnd.randint(0, 255)
    blot = blot.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(18))
    dark = Image.new("RGB", (w, h), (120, 105, 80))
    return Image.composite(dark, img, blot.point(lambda v: int(max(0, v - 150) * 0.5)))


def bars(d, x0, x1, y, h, n, gap, colour, rag=True):
    """Grey bars standing in for lines of print (no letters)."""
    for i in range(n):
        w = x1 - x0
        if rag:
            cut = rnd.randint(0, w // 5)
            a, b = x0 + cut // 2, x1 - cut // 2
        else:
            a, b = x0, x1
        d.rectangle([a, y + i * (h + gap), b, y + i * (h + gap) + h], fill=colour)


def poster(w, h, scheme):
    border, field, ink, accent, sky = scheme
    img = paper(w, h, field)
    d = ImageDraw.Draw(img)
    m = 26
    d.rectangle([m, m, w - m, h - m], outline=rgb(border), width=14)
    # head band: a solid colour block (where a title would be) left blank
    d.rectangle([m + 30, m + 34, w - m - 30, m + 120], fill=rgb(accent))
    bars(d, m + 90, w - m - 90, m + 140, 14, 1, 0, rgb(ink), rag=False)
    # pictorial panel: plain shapes (sky, hills, two figures as silhouettes)
    px0, py0, px1, py1 = m + 40, m + 185, w - m - 40, h - m - 230
    d.rectangle([px0, py0, px1, py1], fill=rgb(sky))
    d.polygon([(px0, py1 - 120), (px0 + 140, py1 - 210), (px0 + 260, py1 - 150), (px1, py1 - 230),
               (px1, py1), (px0, py1)], fill=rgb(border))
    for cx, s in ((px0 + 150, 1.0), (px0 + 270, 0.9)):
        d.ellipse([cx - 22 * s, py1 - 300 * s, cx + 22 * s, py1 - 256 * s], fill=rgb(ink))
        d.polygon([(cx - 40 * s, py1 - 40), (cx - 28 * s, py1 - 250 * s), (cx + 28 * s, py1 - 250 * s),
                   (cx + 40 * s, py1 - 40)], fill=rgb(ink))
    d.rectangle([px0, py0, px1, py1], outline=rgb(ink), width=4)
    # lower print block
    bars(d, m + 60, w - m - 60, py1 + 36, 22, 2, 18, rgb(accent))
    bars(d, m + 90, w - m - 90, py1 + 120, 10, 4, 12, rgb(ink))
    return img.filter(ImageFilter.GaussianBlur(0.8))


SCHEMES = {
    "poster1": ("#5B2A22", "#E4D8B8", "#2C2622", "#A0442E", "#C9B48A"),
    "poster2": ("#2F3F55", "#E2DAC0", "#26292C", "#3E5E7A", "#B7B49A"),
}

atlas = Image.new("RGB", (SIZE, SIZE), rgb("#D8CDB4"))
for name, (c0, r0, c1, r1) in REGIONS.items():
    if name in SCHEMES:
        atlas.paste(poster(c1 - c0, r1 - r0, SCHEMES[name]), (c0, r0))
    else:
        atlas.paste(paper(c1 - c0, r1 - r0, "#D8CDB4"), (c0, r0))
atlas.save(OUT / "signs_atlas.jpg", quality=88)
print("wrote", OUT / "signs_atlas.jpg", "| regions:", REGIONS)
