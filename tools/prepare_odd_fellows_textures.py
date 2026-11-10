"""
prepare_odd_fellows_textures.py - the one derived texture for the Odd Fellows Hall (82-84 Main St).

Usage:  python tools/prepare_odd_fellows_textures.py
Output: assets/textures/odd-fellows-hall/awning_faint.jpg (1024 x 1024, quality 85)

Nothing is downloaded. The 1907-1910s cards show the two awnings as pale canvas with only faint
stripes, so the bank's generated stripes (bank-building/awning_stripes.jpg, original work by
tools/prepare_bank_textures.py) are pulled 75% of the way toward its cream stripe colour:
the stripe pattern and weave stay, the contrast drops to about a quarter.
"""

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "textures" / "bank-building" / "awning_stripes.jpg"
OUT = ROOT / "assets" / "textures" / "odd-fellows-hall"
CREAM = (0xDD, 0xD3, 0xBC)
KEEP = 0.25

OUT.mkdir(parents=True, exist_ok=True)
src = Image.open(SRC).convert("RGB")
flat = Image.new("RGB", src.size, CREAM)
Image.blend(flat, src, KEEP).save(OUT / "awning_faint.jpg", quality=85)
print("wrote", OUT / "awning_faint.jpg")
