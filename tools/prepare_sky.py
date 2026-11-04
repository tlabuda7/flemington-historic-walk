"""Turn a Poly Haven equirectangular .hdr into the scene's LDR sky JPG.

Usage:
    python tools/prepare_sky.py <input.hdr> <exposure> [--wb R,G,B] [--out path.jpg]

- Reads Radiance .hdr (RGBE, new-style RLE) with a small built-in reader (numpy only).
- Multiplies by <exposure> and an optional white-balance (--wb), applies a soft
  shoulder (1 - exp(-x)) so the sun glow rolls off instead of clipping hard,
  encodes sRGB and saves a 2048 x 1024 JPG (quality 85).
- Prints the sun position (brightest region): u (0..1 across the image, left to
  right) and elevation in degrees, plus average colours near the horizon and zenith
  so the exposure can be matched to the scene's fog (#ecdfc4) and sky (#a9bfd2).
"""
import argparse
import numpy as np
from PIL import Image


def read_hdr(path):
    with open(path, "rb") as f:
        data = f.read()
    # header ends with an empty line, then the resolution line "-Y H +X W"
    pos = data.index(b"\n\n") + 2
    end = data.index(b"\n", pos)
    parts = data[pos:end].split()
    if parts[0] != b"-Y" or parts[2] != b"+X":
        raise ValueError("unsupported .hdr orientation: %r" % data[pos:end])
    h, w = int(parts[1]), int(parts[3])
    buf = np.frombuffer(data, dtype=np.uint8, offset=end + 1)
    img = np.zeros((h, w, 4), dtype=np.uint8)
    p = 0
    for y in range(h):
        if buf[p] == 2 and buf[p + 1] == 2 and (int(buf[p + 2]) << 8 | int(buf[p + 3])) == w:
            p += 4
            for c in range(4):
                x = 0
                row = img[y, :, c]
                while x < w:
                    n = int(buf[p]); p += 1
                    if n > 128:
                        n -= 128
                        row[x:x + n] = buf[p]; p += 1
                    else:
                        row[x:x + n] = buf[p:p + n]; p += n
                    x += n
        else:  # flat (uncompressed) scanline
            img[y] = buf[p:p + w * 4].reshape(w, 4)
            p += w * 4
    e = img[..., 3].astype(np.int32)
    scale = np.where(e > 0, np.ldexp(1.0, e - 136), 0.0)
    return img[..., :3].astype(np.float32) * scale[..., None].astype(np.float32)


def srgb(x):
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hdr")
    ap.add_argument("exposure", type=float)
    ap.add_argument("--wb", default="1,1,1", help="white-balance multipliers R,G,B")
    ap.add_argument("--warm", type=float, default=0.0,
                    help="0..1 warm grade near the horizon (fades out by 30 deg up)")
    ap.add_argument("--out", default="assets/textures/sky/sky-late-afternoon.jpg")
    a = ap.parse_args()

    hdr = read_hdr(a.hdr)
    h, w, _ = hdr.shape

    # sun: brightest luminance after a coarse block average (ignores single hot pixels)
    lum = hdr @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    b = 8
    blk = lum[: h // b * b, : w // b * b].reshape(h // b, b, w // b, b).mean(axis=(1, 3))
    by, bx = np.unravel_index(np.argmax(blk), blk.shape)
    sy, sx = (by + 0.5) * b, (bx + 0.5) * b
    print("sun: u = %.3f, elevation = %.1f deg (peak luminance %.0f)"
          % (sx / w, 90 - sy / h * 180, blk[by, bx]))

    wb = np.array([float(v) for v in a.wb.split(",")], dtype=np.float32)
    # optional warm grade that fades out from the horizon (0 deg) to 30 deg up,
    # so the low sky matches the scene's cream fog while the zenith stays blue
    elev = 90 - (np.arange(h) + 0.5) / h * 180
    f = (np.clip(1 - elev / 30, 0, 1) * a.warm).astype(np.float32)[:, None, None]
    warm = 1 + f * (np.array([1.02, 0.97, 0.84], dtype=np.float32) - 1)
    ldr = srgb(1.0 - np.exp(-hdr * a.exposure * wb * warm))
    im = Image.fromarray((ldr * 255 + 0.5).astype(np.uint8)).resize((2048, 1024), Image.LANCZOS)
    im.save(a.out, quality=85, optimize=True)

    arr = np.asarray(im).astype(np.float32)
    def band(e0, e1):  # mean colour between two elevations (degrees)
        r0, r1 = int((90 - e1) / 180 * 1024), int((90 - e0) / 180 * 1024)
        return "#%02x%02x%02x" % tuple(int(v) for v in arr[r0:r1].reshape(-1, 3).mean(0))
    print("horizon band 1-8 deg:", band(1, 8), " (fog target #ecdfc4)")
    print("mid band 20-40 deg:  ", band(20, 40))
    print("zenith band 60-90 deg:", band(60, 90), " (target #a9bfd2)")
    print("saved", a.out, im.size)


if __name__ == "__main__":
    main()
