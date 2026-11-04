"""Pre-bake the mini map image from the 1921 Sanborn sheets (public domain, LoC).

Crops the strip around the walkable part of Main Street from sheet 2 (north of Court St)
and sheet 3 (Court St and south), fades it onto a cream paper tint ("style B, the mix"),
and saves:
  assets/maps/minimap-1921.jpg  - the faded map, north up, PPM pixels per metre
  data/minimap.json             - the image's world bounds + labels (drawn live by js/minimap.js)

Run from the project root:  python tools/prepare_minimap.py
"""
import json
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parent.parent
M_PER_PX = 0.0521                 # Sanborn sheet scale (50 ft = 292 px)
X0, X1 = -45.0, 45.0              # world bounds of the image (metres)
Z0, Z1 = -165.0, 50.0             # north (−Z) … south
SHEET3_FROM_Z = 8.0               # rows south of this come from sheet 3 (sheet 2 is blank there)
SHEET3_DY = 5593                  # sheet-3 y + 5593 = sheet-2 y
PPM = 6                           # output pixels per metre
PAPER = (244, 236, 216)
INK = (70, 52, 38)


def px(x):  # world x -> sheet px
    return round(3797 + x / M_PER_PX)


def py(z):  # world z -> sheet-2 py
    return round(6900 + z / M_PER_PX)


def fade(img):
    """Style B: grayscale, autocontrast, a bit more contrast, ink-on-cream, faded 45 %."""
    g = ImageOps.grayscale(img)
    g = ImageOps.autocontrast(g, cutoff=2)
    g = ImageEnhance.Contrast(g).enhance(1.3)
    tinted = ImageOps.colorize(g, black=INK, white=PAPER)
    return Image.blend(tinted, Image.new('RGB', tinted.size, PAPER), 0.45)


def main():
    s2 = Image.open(ROOT / 'assets/maps/flemington-1921-sanborn-sheet-02.jpg').convert('RGB')
    s3 = Image.open(ROOT / 'assets/maps/flemington-1921-sanborn-sheet-03.jpg').convert('RGB')
    left, right = px(X0), px(X1)
    top, split, bottom = py(Z0), py(SHEET3_FROM_Z), py(Z1)
    a = s2.crop((left, top, right, split))
    b = s3.crop((left, split - SHEET3_DY, right, bottom - SHEET3_DY))
    faded = Image.new('RGB', (right - left, bottom - top))
    faded.paste(fade(a), (0, 0))          # each sheet faded on its own so the tones match
    faded.paste(fade(b), (0, split - top))
    out = faded.resize((round((X1 - X0) * PPM), round((Z1 - Z0) * PPM)), Image.LANCZOS)
    out.save(ROOT / 'assets/maps/minimap-1921.jpg', quality=86, optimize=True)

    # Labels: tag = where the rounded tag sits, at = the building's front (leader line).
    # Tags stand behind the frontage, away from the street numbers the Sanborn prints
    # along the property line; js/minimap.js keeps them inside the map window.
    def bldg(name, addr, x, z, side, tag_dz=0.0):
        tx = x - 11 if side == 'W' else x + 11
        return {'name': name, 'addr': addr, 'x': round(tx, 2), 'z': round(z + tag_dz, 2),
                'atX': x, 'atZ': z}
    labels = [
        bldg('Court House', 'No. 75', -18.34, -6.85, 'W'),
        bldg('County Offices', 'No. 69–71', -17.71, -27.87, 'W'),
        bldg('Frame House', 'No. 65', -14.07, -51.19, 'W'),
        bldg('Wurts Law Office', 'No. 59', -14.95, -68.69, 'W'),
        bldg('County Hotel', 'No. 47–49', -10.3, -112.07, 'W'),
        bldg('Nevius Store', 'No. 78', 10.3, -7.33, 'E', 5.5),  # tag south: Mr. Pickell's caption
        bldg('Union Hotel', 'No. 70–76', 11.6, -30.75, 'E'),
        bldg("Lovell's Restaurant", 'No. 68', 12.66, -52.13, 'E'),
        bldg('Bank Building', 'No. 56–66', 12.24, -66.24, 'E'),
        bldg('Clock Tower Bldg', 'No. 48–52', 10.85, -97.79, 'E'),
        bldg('Auto Sales · Shoe Shine', 'No. 40–46', 8.6, -116.55, 'E'),
    ]
    data = {
        'image': 'assets/maps/minimap-1921.jpg',
        'source': '1921 Sanborn Fire Insurance Map, Flemington NJ, sheets 2-3 (LoC, public domain)',
        'bounds': {'x0': X0, 'x1': X1, 'z0': Z0, 'z1': Z1},
        'pixelsPerMetre': PPM,
        'streets': [
            {'name': 'MAIN STREET', 'x0': -6.4, 'x1': 6.4, 'z0': Z0, 'z1': Z1, 'vertical': True},
            {'name': 'COURT ST', 'x0': -45, 'x1': -6.4, 'z0': 0, 'z1': 12.2},
            {'name': 'BLOOMFIELD AVE', 'x0': 6.4, 'x1': 45, 'z0': -89.8, 'z1': -77.6},
        ],
        'labels': labels,
        'people': [
            {'name': 'Mr. Pickell', 'note': 'talk', 'x': 9.5, 'z': -8.45},
        ],
    }
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'data/minimap.json').write_text(json.dumps(data, indent=2, ensure_ascii=False),
                                            encoding='utf-8')
    print('saved', out.size, 'px')


if __name__ == '__main__':
    main()
