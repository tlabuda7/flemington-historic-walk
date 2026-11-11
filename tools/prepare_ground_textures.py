"""Ground textures for the street (PLAN.md, "Street details pass 2", sections 2-3 and 9).

Reads Poly Haven CC0 colour maps that are already in assets/textures/ and writes the street's
ground maps to assets/textures/ground/. Pure Pillow, fixed random seed (same output every run).
Run from the project root:
    python tools/prepare_ground_textures.py

Output (all used by the `street-ground` component in js/ground.js):
    road_oiled_earth.jpg     1024 px = 6.4 m. Oiled earth-and-stone road: compacted grey-brown
                             gravel with paler, dusty wheel / tyre tracks running along V.
                             U = 0 is the crown of the road, so each half gets one strong pair
                             of tracks (U 0.5) and the middle a fainter pair (U 0).
    walk_bluestone_flags.jpg 1024 px = 3.6 m. Big bluestone flags, 1.8 x 1.2 m, open joints.
    walk_brick.jpg           512 px = 1 m. Worn brick paving (running bond), earth in the joints.
    curb_stone.jpg           1024 x 64 px = 8 m of curb: long stone slabs with joints.
    ground_detail.jpg        256 px. Neutral light mottling; grass and earth are this map times
                             a vertex colour (one draw call for both).
    street_decals.png        512 px RGBA, four 256 px cells: horse droppings, flattened
                             droppings, paper scraps, a pair of turning wheel tracks.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "assets" / "textures"
OUT = TEX / "ground"
OUT.mkdir(parents=True, exist_ok=True)
random.seed(1920)


def tile2(image, size):
    """2 x 2 copies of a tileable image, each `size` px."""
    small = image.resize((size, size), Image.LANCZOS)
    out = Image.new(image.mode, (size * 2, size * 2))
    for i in range(2):
        for j in range(2):
            out.paste(small, (i * size, j * size))
    return out


def tint(image, color, contrast=1.0):
    """Keep the light/dark variation, give it a new mean colour."""
    grey = ImageOps.grayscale(image)
    mean = sum(i * n for i, n in enumerate(grey.histogram())) / (grey.width * grey.height)
    def channel(c):
        return grey.point(lambda v: max(0, min(255, int(c * (1 + (v / mean - 1) * contrast)))))
    return Image.merge("RGB", tuple(channel(c) for c in color))


def soft_noise(size, cells, lo, hi):
    """Tileable low-frequency noise, greyscale, values lo..hi."""
    small = Image.new("L", (cells, cells))
    small.putdata([random.randint(lo, hi) for _ in range(cells * cells)])
    big = Image.new("L", (cells * 3, cells * 3))
    for i in range(3):
        for j in range(3):
            big.paste(small, (i * cells, j * cells))
    big = big.resize((size * 3, size * 3), Image.BICUBIC)
    return big.crop((size, size, size * 2, size * 2))


def multiply_l(image, mask_l):
    """image x (mask / 255) per pixel; mask 255 = unchanged."""
    return ImageChops.multiply(image, Image.merge("RGB", (mask_l, mask_l, mask_l)))


# ---------------------------------------------------------------- road
def make_road():
    S = 1024                       # 6.4 m -> 160 px per metre
    gravel = Image.open(TEX / "polyhaven" / "gravel_ground_01.jpg").convert("RGB")
    fine = tile2(gravel, S // 2)                                   # stones at about true size
    coarse = ImageChops.offset(gravel.resize((S, S), Image.LANCZOS), 311, 173)
    base = Image.blend(fine, coarse, 0.30)                         # hides the 2 x 2 repeat
    # Oiled: darker and greyer than the dry yellow gravel, a little of its own colour kept.
    base = Image.blend(tint(base, (99, 95, 88), 0.95), base.point(lambda v: int(v * 0.72)), 0.15)
    # Slow light/dark patches (patched and re-oiled stretches).
    patches = soft_noise(S, 5, 218, 255)
    base = multiply_l(base, patches)

    # Wheel tracks along V: (centre in metres from U = 0, half-gauge, band width, strength)
    px = S / 6.4
    mask = Image.new("L", (S, S), 0)
    draw = ImageDraw.Draw(mask)
    tracks = [(3.20, 0.72, 0.24, 235), (3.20 + 0.16, 0.71, 0.10, 130), (0.0, 0.72, 0.20, 110)]
    for centre, half, width, strength in tracks:
        for side in (-1, 1):
            phase = random.uniform(0, 6.28)
            k = random.choice((1, 2))
            pts = []
            for y in range(-8, S + 9, 8):
                wob = 0.05 * math.sin(2 * math.pi * k * y / S + phase) * px
                pts.append(((centre + side * half) * px + wob, y))
            for shift in (-S, 0, S):                               # wrap across the U seam
                draw.line([(x + shift, y) for x, y in pts], fill=strength, width=int(width * px))
    mask = mask.filter(ImageFilter.GaussianBlur(5))
    # Patchy: the dust lies thicker in places.
    mask = ImageChops.multiply(mask, soft_noise(S, 9, 120, 255))
    grit = ImageOps.autocontrast(ImageOps.grayscale(fine)).point(lambda v: 150 + v * 105 // 255)
    mask = ImageChops.multiply(mask, grit)
    dusty = tint(base, (150, 143, 130), 0.75)
    road = Image.composite(dusty, base, mask.point(lambda v: v * 115 // 255))

    # Slightly darker middle of each strong pair (hoof path, oil drips).
    dark = Image.new("L", (S, S), 255)
    d = ImageDraw.Draw(dark)
    for shift in (-S, 0, S):
        d.rectangle([3.20 * px - 0.32 * px + shift, 0, 3.20 * px + 0.32 * px + shift, S], fill=232)
    dark = dark.filter(ImageFilter.GaussianBlur(14))
    road = multiply_l(road, dark)
    road.save(OUT / "road_oiled_earth.jpg", quality=88)


# ---------------------------------------------------------------- bluestone flags
def make_flags():
    S = 1024                       # 3.6 m: 2 flags of 1.8 m across U, 3 courses of 1.2 m along V
    stone = Image.open(TEX / "lovells-restaurant" / "stone_bluestone.jpg").convert("RGB")
    src = tile2(stone, 569)        # 2 m per 569 px = the same px per metre as the output
    out = Image.new("RGB", (S, S))
    joints = Image.new("L", (S, S), 0)
    jd = ImageDraw.Draw(joints)
    course_h = S / 3
    offsets = (0, 256, 128)
    for i in range(3):
        y0, y1 = round(i * course_h), round((i + 1) * course_h)
        for j in range(2):
            x0 = offsets[i] + j * 512
            w, h = 512, y1 - y0
            sx, sy = random.randint(0, src.width - w), random.randint(0, src.height - h)
            slab = src.crop((sx, sy, sx + w, sy + h))
            f = random.uniform(0.86, 1.08)
            warm = random.uniform(-5, 5)
            r, g, b = slab.split()
            slab = Image.merge("RGB", (r.point(lambda v: int(v * f + warm)), g.point(lambda v: int(v * f)),
                                       b.point(lambda v: int(v * f - warm))))
            for shift in (-S, 0):
                out.paste(slab, (x0 + shift, y0))
            for shift in (-S, 0, S):
                jd.line([(x0 + shift, y0), (x0 + shift, y1)], fill=255, width=random.choice((3, 4, 5)))
        jd.line([(0, y0), (S, y0)], fill=255, width=random.choice((3, 4)))
    jd.line([(0, S - 1), (S, S - 1)], fill=255, width=2)
    out = tint(out, (104, 109, 114), 1.0)
    # Soft worn edges round each flag, then the dark open joint itself.
    worn = joints.filter(ImageFilter.GaussianBlur(7)).point(lambda v: 255 - v * 60 // 255)
    out = multiply_l(out, worn)
    out = Image.composite(Image.new("RGB", (S, S), (52, 50, 46)), out,
                          joints.filter(ImageFilter.GaussianBlur(0.8)).point(lambda v: v * 215 // 255))
    out.save(OUT / "walk_bluestone_flags.jpg", quality=88)


# ---------------------------------------------------------------- brick paving
def make_brick():
    brick = Image.open(TEX / "polyhaven" / "red_brick.jpg").convert("RGB").resize((512, 512), Image.LANCZOS)
    r, g, b = brick.split()
    brick = Image.merge("RGB", (r.point(lambda v: int(v * 0.74)), g.point(lambda v: int(v * 0.68)),
                                b.point(lambda v: int(v * 0.64))))
    earth = Image.new("RGB", brick.size, (104, 92, 76))
    brick = Image.blend(brick, earth, 0.22)
    brick = multiply_l(brick, soft_noise(512, 6, 215, 255))
    brick.save(OUT / "walk_brick.jpg", quality=88)


# ---------------------------------------------------------------- curb
def make_curb():
    W, H = 1024, 64                # 8 m of curb, 128 px per metre
    granite = Image.open(TEX / "street-props" / "granite_dressed_light.jpg").convert("RGB")
    strip = Image.new("RGB", (W, H))
    joints_m = (0.0, 1.9, 4.1, 6.0, 8.0)
    for a, b in zip(joints_m, joints_m[1:]):
        x0, x1 = round(a * 128), round(b * 128)
        sx, sy = random.randint(0, 1024 - (x1 - x0)), random.randint(0, 1024 - H)
        slab = granite.crop((sx, sy, sx + x1 - x0, sy + H))
        slab = tint(slab, (148, 146, 140), 0.4).point(lambda v, f=random.uniform(0.9, 1.05): int(v * f))
        strip.paste(slab, (x0, 0))
    d = ImageDraw.Draw(strip)
    for a in joints_m[:-1]:
        x = round(a * 128)
        d.line([(x, 0), (x, H)], fill=(60, 57, 52), width=2)
        d.line([(x + 2, 0), (x + 2, H)], fill=(132, 126, 117), width=1)
    strip.save(OUT / "curb_stone.jpg", quality=88)


# ---------------------------------------------------------------- neutral detail
def make_detail():
    gravel = Image.open(TEX / "polyhaven" / "gravel_ground_01.jpg").convert("L").resize((256, 256), Image.LANCZOS)
    grain = ImageOps.autocontrast(gravel).point(lambda v: 196 + v * 44 // 255)
    slow = soft_noise(256, 5, 225, 255)
    detail = ImageChops.multiply(grain, slow)
    Image.merge("RGB", (detail, detail, detail)).save(OUT / "ground_detail.jpg", quality=88)


# ---------------------------------------------------------------- decals
def blob(draw, cx, cy, rx, ry, fill):
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill)


def make_decals():
    C = 256
    sheet = Image.new("RGBA", (C * 2, C * 2), (0, 0, 0, 0))

    def cell(colour_fn, alpha_fn, base_rgb):
        rgb = Image.new("RGB", (C, C), base_rgb)
        a = Image.new("L", (C, C), 0)
        colour_fn(ImageDraw.Draw(rgb))
        alpha_fn(ImageDraw.Draw(a))
        return rgb, a

    # Cell (0,0): fresh horse droppings, a loose pile about 0.35 m across in a 0.6 m quad.
    apples = [(random.gauss(128, 30), random.gauss(128, 26), random.uniform(11, 17)) for _ in range(11)]
    def col(d):
        for x, y, r in apples:
            c = random.randint(-8, 10)
            blob(d, x, y, r, r * 0.85, (62 + c, 50 + c, 30 + c))
            blob(d, x - r * 0.3, y - r * 0.3, r * 0.4, r * 0.3, (86 + c, 72 + c, 44 + c))
    def alp(d):
        for x, y, r in apples:
            blob(d, x, y, r, r * 0.85, 255)
    rgb, a = cell(col, alp, (62, 50, 30))
    stain = Image.new("L", (C, C), 0)
    blob(ImageDraw.Draw(stain), 128, 128, 80, 66, 90)
    a = ImageChops.lighter(a.filter(ImageFilter.GaussianBlur(1.2)), stain.filter(ImageFilter.GaussianBlur(16)))
    rgb = rgb.filter(ImageFilter.GaussianBlur(0.8))
    sheet.paste(Image.merge("RGBA", (*rgb.split(), a)), (0, 0))

    # Cell (1,0): old droppings, flattened and dried by wheels: a pale, ragged smear.
    lumps = [(random.gauss(128, 44), random.gauss(128, 20), random.uniform(10, 26)) for _ in range(16)]
    def col2(d):
        for x, y, r in lumps:
            c = random.randint(-10, 10)
            blob(d, x, y, r * 1.5, r * 0.7, (96 + c, 83 + c, 58 + c))
    def alp2(d):
        for x, y, r in lumps:
            blob(d, x, y, r * 1.5, r * 0.7, random.randint(120, 200))
    rgb, a = cell(col2, alp2, (96, 83, 58))
    sheet.paste(Image.merge("RGBA", (*rgb.filter(ImageFilter.GaussianBlur(1.5)).split(),
                                     a.filter(ImageFilter.GaussianBlur(2.5)))), (C, 0))

    # Cell (0,1): scraps of paper (a 0.7 m quad): three small crumpled off-white pieces.
    scraps = []
    for cx, cy, s in ((78, 92, 26), (170, 150, 20), (120, 196, 14)):
        ang = random.uniform(0, 3.14)
        pts = []
        for k in range(5):
            t = ang + k * 2 * math.pi / 5 + random.uniform(-0.3, 0.3)
            rr = s * random.uniform(0.6, 1.0)
            pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t) * 0.7))
        scraps.append((pts, random.choice(((214, 207, 189), (196, 187, 166), (224, 219, 204)))))
    def col3(d):
        for pts, c in scraps:
            d.polygon(pts, fill=c)
            d.line([pts[0], pts[2]], fill=tuple(v - 28 for v in c), width=1)
    def alp3(d):
        for pts, c in scraps:
            d.polygon(pts, fill=255)
    rgb, a = cell(col3, alp3, (205, 198, 180))
    sheet.paste(Image.merge("RGBA", (*rgb.split(), a.filter(ImageFilter.GaussianBlur(0.7)))), (0, C))

    # Cell (1,1): a pair of pale wheel tracks along V (cell = 2.0 m wide, gauge 1.44 m), for the
    # curved tracks at the two junctions.
    def alp4(d):
        for x in (128 - 92, 128 + 92):
            d.line([(x, 0), (x, C)], fill=255, width=26)
    rgb, a = cell(lambda d: None, alp4, (160, 149, 130))
    a = a.filter(ImageFilter.GaussianBlur(6))
    a = ImageChops.multiply(a, soft_noise(C, 7, 110, 255)).point(lambda v: v * 68 // 255)
    sheet.paste(Image.merge("RGBA", (*rgb.split(), a)), (C, C))

    sheet.save(OUT / "street_decals.png", optimize=True)


if __name__ == "__main__":
    make_road()
    make_flags()
    make_brick()
    make_curb()
    make_detail()
    make_decals()
    for f in sorted(OUT.iterdir()):
        print(f.name, f.stat().st_size // 1024, "KB")
