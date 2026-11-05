"""Prepare the distant-landscape heightmap for Flemington (pass 1).

Source: USGS 3DEP elevation (public domain), fetched without login from the
3DEPElevation ImageServer "exportImage" endpoint, e.g.

  https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage
    ?bbox=-75.04,40.377,-74.68,40.647&bboxSR=4326&imageSR=4326&size=640,480
    &format=tiff&pixelType=F32&interpolation=RSP_BilinearInterpolation
    &compression=None&f=image

Usage:  python -I tools/prepare_landscape_dem.py <downloaded dem.tif> [out_dir]

Writes (default out_dir = assets/maps):
  landscape-dem.png   16-bit greyscale, value = elevation in decimetres (m x 10), row 0 = north
  landscape-dem.json  geo bounds, size, encoding, scene transform, horizon profile
Needs only Pillow (no numpy).
"""
import json
import math
import os
import sys

from PIL import Image

BBOX = (-75.04, 40.377, -74.68, 40.647)  # west, south, east, north (deg, WGS84 / NAD83)
ORIGIN = (40.51030, -74.85890)           # Main St centreline x Court St line (scene x=0, z=0), from OSM
MAIN_ST_BEARING = -5.5                   # deg east of true north for scene -Z (OSM way 28039047)
EYE = 1.75                               # eye height above street (m)


def main():
    src = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "assets", "maps")
    im = Image.open(src)
    if im.mode != "F":
        im = im.convert("F")
    w, h = im.size
    px = im.load()
    W, S, E, N = BBOX
    m_per_deg_lat = 111132.0
    m_per_deg_lon = 111320.0 * math.cos(math.radians(ORIGIN[0]))

    def elev(lat, lon):
        fx = (lon - W) / (E - W) * w - 0.5
        fy = (N - lat) / (N - S) * h - 0.5
        x0, y0 = int(math.floor(fx)), int(math.floor(fy))
        tx, ty = fx - x0, fy - y0
        def g(x, y):
            return px[min(max(x, 0), w - 1), min(max(y, 0), h - 1)]
        return ((g(x0, y0) * (1 - tx) + g(x0 + 1, y0) * tx) * (1 - ty)
                + (g(x0, y0 + 1) * (1 - tx) + g(x0 + 1, y0 + 1) * tx) * ty)

    # 16-bit PNG, decimetres.
    out = Image.new("I", (w, h))
    op = out.load()
    lo, hi = 1e9, -1e9
    for y in range(h):
        for x in range(w):
            v = px[x, y]
            if v < -100 or v > 3000:  # nodata guard
                v = 0.0
            lo, hi = min(lo, v), max(hi, v)
            op[x, y] = int(round(max(v, 0) * 10))
    os.makedirs(out_dir, exist_ok=True)
    out.convert("I;16").save(os.path.join(out_dir, "landscape-dem.png"))

    base = elev(*ORIGIN)
    # Horizon profile: for each azimuth, the highest elevation angle seen from the
    # street (eye at base + EYE), searching 0.6-15 km out.
    prof = []
    for az in range(0, 360, 5):
        a = math.radians(az)
        best = (-90.0, 0, 0)
        r = 600.0
        while r <= 15000:
            dn, de = r * math.cos(a), r * math.sin(a)
            lat = ORIGIN[0] + dn / m_per_deg_lat
            lon = ORIGIN[1] + de / m_per_deg_lon
            if not (S <= lat <= N and W <= lon <= E):
                break
            e = elev(lat, lon)
            # earth curvature + refraction drop: d^2 / (2R) * (1 - 0.13)
            drop = r * r / (2 * 6371000.0) * 0.87
            ang = math.degrees(math.atan2(e - drop - base - EYE, r))
            if ang > best[0]:
                best = (ang, r, e)
            r += 60.0
        prof.append({"az": az, "max_angle_deg": round(best[0], 3),
                     "at_km": round(best[1] / 1000, 2), "elev_m": round(best[2], 1)})
        print(f"az {az:3d}  {best[0]:6.2f} deg at {best[1]/1000:5.2f} km  elev {best[2]:6.1f} m")

    meta = {
        "source": "USGS 3DEP (The National Map) 3DEPElevation ImageServer exportImage; public domain",
        "bbox_wsen_deg": BBOX,
        "crs": "EPSG:4326 (lat/lon grid)",
        "size_px": [w, h],
        "encoding": "uint16 = elevation metres x 10 (decimetres), NAVD88; row 0 = north edge",
        "elev_range_m": [round(lo, 1), round(hi, 1)],
        "origin_lat_lon": ORIGIN,
        "origin_ground_elev_m": round(base, 1),
        "m_per_deg": {"lat": m_per_deg_lat, "lon": round(m_per_deg_lon, 1)},
        "scene_transform": ("east_m = (lon - lon0) * m_per_deg.lon; north_m = (lat - lat0) * m_per_deg.lat; "
                            "rotate by MAIN_ST_BEARING b: x = east*cos(b) - north*sin(b), "
                            "z = -(east*sin(b) + north*cos(b)); y = elev - origin_ground_elev_m"),
        "main_st_bearing_deg": MAIN_ST_BEARING,
        "horizon_profile_eye_1p75m": prof,
    }
    with open(os.path.join(out_dir, "landscape-dem.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("base elev", round(base, 1), "range", round(lo, 1), round(hi, 1))


if __name__ == "__main__":
    main()
