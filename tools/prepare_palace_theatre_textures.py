"""
prepare_palace_theatre_textures.py - the one generated texture for the Palace Theatre (31 Main St).

Usage:  python tools/prepare_palace_theatre_textures.py
Output: assets/textures/palace-theatre/signs_atlas.jpg (1024 x 1024, quality 88)

Nothing is downloaded: the atlas is drawn here with Pillow (original work).
Owner decisions: 2026-11-08 no invented film titles and no lettering at all; 2026-11-10 the two
poster frames are PLAIN and EMPTY (realism). Each frame therefore holds only a bare backing
board: dark green-grey paint over three vertical boards, worn and sun-faded, with a few old
tack holes and paler rectangles where earlier bills were pasted. No figures, no print, no text.

Layout (pixels from the top-left; tools/blender/palace_theatre_bake.py maps the UVs to these
boxes, REGIONS below is the single source of truth):
  poster1  empty backing board in the frame on the pier south of the entrance (0.56 x 0.94 m)
  poster2  empty backing board in the frame on the north corner pier (0.56 x 0.94 m)
  spare    plain paint
"""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageChops

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


def noise_layer(w, h, cell, blur):
    """Low-frequency random field 0-255 (blotchy fading)."""
    small = Image.new("L", (w // cell + 2, h // cell + 2))
    sp = small.load()
    for y in range(small.height):
        for x in range(small.width):
            sp[x, y] = rnd.randint(0, 255)
    return small.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur))


def grain(img, amount, stretch_y=6):
    """Fine grain, stretched vertically like brushed paint on upright boards."""
    w, h = img.size
    g = Image.new("L", (w, h // stretch_y + 1))
    gp = g.load()
    for y in range(g.height):
        for x in range(w):
            gp[x, y] = 128 + rnd.randint(-amount, amount)
    g = g.resize((w, h), Image.BILINEAR)
    return ImageChops.subtract(img, Image.merge("RGB", [g] * 3), 1, 128)   # img - (g - 128)


def board(w, h, base, faded):
    """Plain painted backing board: three vertical boards, fading, wear, old tack holes."""
    img = Image.new("RGB", (w, h), rgb(base))
    # sun-faded, chalky patches
    img = Image.composite(Image.new("RGB", (w, h), rgb(faded)), img,
                          noise_layer(w, h, 40, 30).point(lambda v: int(max(0, v - 110) * 1.1)))
    # faint paler rectangles where old bills were pasted and torn off (blank, no print)
    ghost = Image.new("L", (w, h), 0)
    gd = ImageDraw.Draw(ghost)
    for _ in range(2):
        x0 = rnd.randint(20, 70)
        y0 = rnd.randint(30, 160)
        gd.rectangle([x0, y0, w - rnd.randint(20, 70), y0 + rnd.randint(420, 600)], fill=26)
    ghost = ghost.filter(ImageFilter.GaussianBlur(6))
    ghost = ImageChops.multiply(ghost, noise_layer(w, h, 24, 10).point(lambda v: min(255, v + 80)))
    img = Image.composite(Image.new("RGB", (w, h), rgb(faded)), img, ghost)
    img = grain(img, 9)
    d = ImageDraw.Draw(img)
    # board joints (dark V-groove with a lit edge)
    for k in (1, 2):
        x = int(w * k / 3) + rnd.randint(-4, 4)
        d.line([(x, 0), (x, h)], fill=(18, 20, 18), width=4)
        d.line([(x + 3, 0), (x + 3, h)], fill=tuple(min(255, c + 14) for c in rgb(base)), width=1)
    # old tack / nail holes
    for _ in range(26):
        x, y = rnd.randint(14, w - 14), rnd.randint(14, h - 14)
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(22, 22, 20))
    # grime gathering toward the bottom and the frame edges
    vy = Image.linear_gradient("L").resize((w, h)).point(lambda v: int(max(0, v - 150) * 0.9))
    edge = Image.new("L", (w, h), 0)
    ImageDraw.Draw(edge).rectangle([0, 0, w - 1, h - 1], outline=110, width=18)
    edge = edge.filter(ImageFilter.GaussianBlur(14))
    img = Image.composite(Image.new("RGB", (w, h), (20, 20, 18)), img, ImageChops.lighter(vy, edge))
    return img.filter(ImageFilter.GaussianBlur(0.7))


# (base paint, faded paint) per frame: dark green-grey, one a touch browner
SCHEMES = {
    "poster1": ("#33392F", "#55594C"),
    "poster2": ("#30362F", "#504F45"),
}

atlas = Image.new("RGB", (SIZE, SIZE), rgb("#33392F"))
for name, (c0, r0, c1, r1) in REGIONS.items():
    base, faded = SCHEMES.get(name, ("#33392F", "#55594C"))
    atlas.paste(board(c1 - c0, r1 - r0, base, faded), (c0, r0))
atlas.save(OUT / "signs_atlas.jpg", quality=88)
print("wrote", OUT / "signs_atlas.jpg", "| regions:", REGIONS)
