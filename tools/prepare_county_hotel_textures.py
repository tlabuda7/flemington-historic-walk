"""
prepare_county_hotel_textures.py - the two generated textures for the County Hotel (47-49 Main St).

Usage:  python tools/prepare_county_hotel_textures.py
Output (1024 x 1024, quality 88), in assets/textures/county-hotel/:
  brick_painted_cream.jpg  polyhaven/red_brick.jpg repainted pale cream-buff #D8CDB4: the
                           brick's own light/dark detail is inverted (the pale mortar joints
                           become shadowed joints under the paint) and kept at ~30 % contrast,
                           so the coursing just shows.
  signs_atlas.jpg          original work drawn with Pillow: dark green louvred shutter leaf,
                           veranda post faces with long sunk "X" panels (double for the ground
                           posts, single for the upper posts), lantern pane lettered
                           "COUNTY / HOTEL" (Georgia Bold, installed with Windows; no font file
                           is shipped), plain off-white and dark green fills.

Layout (pixels from the top-left; county_hotel_bake.py maps UVs into these boxes):
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parent.parent
TX = ROOT / "assets" / "textures"
OUT = TX / "county-hotel"
OUT.mkdir(parents=True, exist_ok=True)
FONTS = Path(r"C:\Windows\Fonts")
rnd = random.Random(47)

REGIONS = {
    "louvre":  (0, 0, 256, 640),       # one shutter leaf (0.40 x 1.20 .. 0.45 x 1.70)
    "post2":   (256, 0, 352, 1024),    # ground post face 0.26 x 2.58, two stacked X panels
    "post1":   (352, 0, 448, 1024),    # upper post face 0.24 x 2.53, one X panel
    "lantern": (448, 0, 704, 448),     # lantern pane 0.36 x 0.60, "COUNTY / HOTEL"
    "white":   (704, 0, 1024, 256),    # plain off-white (post ends, edges)
    "green":   (704, 256, 1024, 512),  # plain dark green (shutter edges and backs)
    "spare":   (0, 640, 256, 1024),
}
for k, v in REGIONS.items():
    __doc__ += "  %-8s %s\n" % (k, v)


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


# --- painted brick -------------------------------------------------------------------
lum = Image.open(TX / "polyhaven" / "red_brick.jpg").convert("L")
st = ImageStat.Stat(lum)
mean, std = st.mean[0], st.stddev[0]
target = rgb("#D8CDB4")
chans = []
for t in target:
    a = 0.30 * 0.18 * t / std            # ~5 % of the colour per standard deviation, inverted
    chans.append(lum.point([max(0, min(255, int(round(t - a * (v - mean))))) for v in range(256)]))
img = Image.merge("RGB", chans)
img.save(OUT / "brick_painted_cream.jpg", quality=88)
print("brick_painted_cream.jpg mean", [round(c) for c in ImageStat.Stat(img).mean])

# --- signs atlas -----------------------------------------------------------------------
atlas = Image.new("RGB", (1024, 1024), rgb("#E4DED0"))
WHITE = rgb("#E4DED0")
GREEN = rgb("#34432F")


def noisy(img, amount=10):
    w, h = img.size
    n = Image.effect_noise((w, h), amount).convert("L")
    return ImageChops.multiply(img, Image.merge("RGB", [n.point(lambda v: 228 + v // 9)] * 3))


def fill(name, colour):
    c0, r0, c1, r1 = REGIONS[name]
    atlas.paste(noisy(Image.new("RGB", (c1 - c0, r1 - r0), colour), 8), (c0, r0))


def draw_louvre(w, h):
    img = Image.new("RGB", (w, h), GREEN)
    d = ImageDraw.Draw(img)
    st, rail = int(w * 0.13), int(h * 0.035)
    n = 30
    top, bot = rail, h - rail
    pitch = (bot - top) / n
    for k in range(n):
        y = top + k * pitch
        d.rectangle([st, y, w - st, y + pitch], fill=tuple(int(c * 1.10) for c in GREEN))
        d.rectangle([st, y + pitch * 0.60, w - st, y + pitch], fill=tuple(int(c * 0.45) for c in GREEN))
        d.line([(st, y + 1), (w - st, y + 1)], fill=tuple(min(255, int(c * 1.30)) for c in GREEN), width=2)
    d.rectangle([0, h // 2 - rail // 2, w, h // 2 + rail // 2], fill=GREEN)     # mid rail
    d.rectangle([st, 0, w - st, h], outline=tuple(int(c * 0.55) for c in GREEN), width=3)
    return noisy(img, 12)


def draw_post(w, h, n_x):
    """Off-white post face, n_x long sunk panels stacked, each with a raised 'X' in it.
    The face is drawn at its real aspect (x4) then squeezed into the box."""
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    m = int(w * 0.18)
    top, bot = int(h * 0.03), int(h * 0.97)
    gap = int(h * 0.03)
    ph = (bot - top - gap * (n_x - 1)) / n_x
    sh = tuple(int(c * 0.62) for c in WHITE)
    lit = tuple(min(255, int(c * 1.05)) for c in WHITE)
    for k in range(n_x):
        y0 = top + k * (ph + gap)
        y1 = y0 + ph
        box = [m, y0, w - m, y1]
        d.rectangle(box, fill=tuple(int(c * 0.86) for c in WHITE))
        e = max(3, w // 24)
        d.rectangle([m, y0, w - m, y0 + e], fill=sh)                 # shadow under the top edge
        d.rectangle([m, y0, m + e, y1], fill=sh)                     # shadow at the left edge
        d.rectangle([m, y1 - e, w - m, y1], fill=lit)
        xw = max(4, int(w * 0.11))
        for (xa, ya), (xb, yb) in (((m + e, y0 + e), (w - m - e, y1 - e)), ((w - m - e, y0 + e), (m + e, y1 - e))):
            d.line([(xa, ya), (xb, yb)], fill=WHITE, width=xw)
            d.line([(xa + xw * 0.45, ya), (xb + xw * 0.45, yb)], fill=sh, width=max(2, xw // 4))
    return noisy(img, 8)


def draw_lantern(w, h):
    glass = rgb("#E8D9A8")
    img = Image.new("RGB", (w, h), glass)
    d = ImageDraw.Draw(img)
    for y in range(h):                                               # warm glow, darker at the edges
        k = 1.0 - 0.18 * abs(y / h - 0.5) * 2
        d.line([(0, y), (w, y)], fill=tuple(int(c * k) for c in glass))
    ink = rgb("#2A2018")
    for word, (ya, yb) in (("COUNTY", (0.18, 0.42)), ("HOTEL", (0.58, 0.82))):
        size = int(h * (yb - ya) * 1.3)
        while size > 8:
            font = ImageFont.truetype(str(FONTS / "georgiab.ttf"), size)
            bb = font.getbbox(word)
            if bb[2] - bb[0] <= w * 0.86 and bb[3] - bb[1] <= h * (yb - ya):
                break
            size -= 2
        bb = font.getbbox(word)
        x = (w - (bb[2] - bb[0])) / 2 - bb[0]
        y = h * (ya + yb) / 2 - (bb[3] - bb[1]) / 2 - bb[1]
        d.text((x, y), word, font=font, fill=ink)
    d.rectangle([0, 0, w - 1, h - 1], outline=rgb("#3A3530"), width=max(3, w // 40))
    return img.filter(ImageFilter.GaussianBlur(0.6))


def put(name, im):
    c0, r0, c1, r1 = REGIONS[name]
    atlas.paste(im.resize((c1 - c0, r1 - r0), Image.LANCZOS), (c0, r0))


put("louvre", draw_louvre(400, 1200))
put("post2", draw_post(260, 2580, 2))
put("post1", draw_post(240, 2530, 1))
put("lantern", draw_lantern(360, 600))
fill("white", WHITE)
fill("green", GREEN)
fill("spare", WHITE)
out = OUT / "signs_atlas.jpg"
atlas.save(out, quality=88)
print(out, out.stat().st_size // 1024, "KB")
print(__doc__.split("Layout")[1])
