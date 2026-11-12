"""Distant landscape (pass 1): builds assets/models/landscape.glb (PLAN.md -> Background ->
"Distant landscape (pass 1)").

Two root nodes:
  landscape_far   (empty at the origin; children landscape_far_terrain + landscape_far_trees)
                  distance-compressed ring 330-800 m, unlit, haze baked into COLOR_0,
                  the scene moves it with the player rig (f = 0.85), fog off.
  landscape_town  fixed, true scale houses / trees / one steeple at the street ends, fog on.

Axes: Blender X = scene x, Blender Y = -scene z (north = +Y), Z up. Entity rotation 0 0 0.
Unlit: no lightmap bake. Run in Blender:
  exec(open(r"<root>/tools/blender/landscape.py").read())
Needs assets/maps/landscape-dem.png/.json and assets/textures/landscape/tree_silhouettes.png
(python -I tools/prepare_landscape_textures.py).
"""
import bpy, bmesh, json, math, os, random, struct
import numpy as np

ROOT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
DEM_PNG = os.path.join(ROOT, "assets", "maps", "landscape-dem.png")
DEM_JSON = os.path.join(ROOT, "assets", "maps", "landscape-dem.json")
TEX = os.path.join(ROOT, "assets", "textures", "landscape", "tree_silhouettes.png")
BLEND = os.path.join(ROOT, "assets", "models", "source", "landscape.blend")
GLB = os.path.join(ROOT, "assets", "models", "landscape.glb")
PREV = os.path.join(ROOT, "assets", "models", "previews")

EXAG = 1.0          # vertical exaggeration knob (spec: 1.0; reviewer may allow <= 1.5 beyond 6 km)
EXAG_MIN_KM = 6.0   # exaggeration only applies beyond this true distance
EYE = 1.75
AZ_SEG, RINGS = 120, 24
R_IN, R_OUT = 700.0, 13000.0
SUN = np.array([-0.86, -0.36, 0.36]); SUN /= np.linalg.norm(SUN)
CB, SB = math.cos(math.radians(5.5)), math.sin(math.radians(5.5))
random.seed(1920)


def hexc(h):
    h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def lin(c):
    c = np.clip(c, 0, 1); return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def mix(a, b, t):
    return a + (b - a) * t


def sstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


SKY_H = hexc("#ebe4cb"); HAZE = hexc("#bfc6c2")
SEAM = mix(hexc("#6f6a45"), SKY_H, 0.93)

# ---------------------------------------------------------------- DEM
meta = json.load(open(DEM_JSON))
W, S_, E_, N_ = meta["bbox_wsen_deg"]
LAT0, LON0 = meta["origin_lat_lon"]
MLAT, MLON = meta["m_per_deg"]["lat"], meta["m_per_deg"]["lon"]
ELEV0 = meta["origin_ground_elev_m"]
_img = bpy.data.images.load(DEM_PNG, check_existing=False)
_img.colorspace_settings.name = "Non-Color"
DW, DH = _img.size
DEM = np.array(_img.pixels[:], dtype=np.float64).reshape(DH, DW, _img.channels)[::-1, :, 0] * 6553.5  # row 0 = north
bpy.data.images.remove(_img)


def elev(X, Y):
    """True ground elevation (m) at Blender X, Y (true metres from the origin)."""
    x, z = X, -Y
    e = CB * x + SB * z; n = SB * x - CB * z
    lon = LON0 + e / MLON; lat = LAT0 + n / MLAT
    c = (lon - W) / (E_ - W) * DW - 0.5; r = (N_ - lat) / (N_ - S_) * DH - 0.5
    c = min(max(c, 0), DW - 1.001); r = min(max(r, 0), DH - 1.001)
    c0, r0 = int(c), int(r); fc, fr = c - c0, r - r0
    a = DEM[r0, c0] * (1 - fc) + DEM[r0, c0 + 1] * fc
    b = DEM[r0 + 1, c0] * (1 - fc) + DEM[r0 + 1, c0 + 1] * fc
    return a * (1 - fr) + b * fr


def rel_y(X, Y, el):
    d = math.hypot(X, Y)
    y = el - ELEV0
    if d > EXAG_MIN_KM * 1000: y *= EXAG
    return y - d * d / (2 * 6371000.0) * 0.87


def rprime(r):
    return 330 + 470 * math.log(r / 700) / math.log(13000 / 700)


def compress(X, Y, y):
    """True (X, Y, rel height) -> compressed ring position (keeps bearing + eye elevation angle)."""
    r = max(math.hypot(X, Y), 1.0); rp = rprime(r); k = rp / r
    return (X * k, Y * k, EYE + (y - EYE) * k), rp


def haze_h(r):
    return max(1 - math.exp(-r / 4500), sstep(10000, 13000, r))


def haze_col(r):
    return mix(HAZE, SKY_H, sstep(8000, 13000, r))


def noise(X, Y):
    return (math.sin(X / 900 + 1.3) * math.sin(Y / 1100 + 0.4)
            + 0.5 * math.sin(X / 410 - Y / 530 + 2.0) + 0.3 * math.sin(Y / 260 + X / 330))


# ---------------------------------------------------------------- helpers
def new_obj(name, verts, faces, coll, parent=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    if parent: ob.parent = parent
    return ob


def set_point_colors(ob, cols):
    a = ob.data.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    flat = np.ones((len(cols), 4)); flat[:, :3] = np.array(cols)
    a.data.foreach_set("color", flat.ravel())
    ob.data.color_attributes.active_color = a; ob.data.color_attributes.render_color_index = 0


def make_mat(name, tex=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.0
    ca = nt.nodes.new("ShaderNodeVertexColor"); ca.layer_name = "Col"
    if tex:
        it = nt.nodes.new("ShaderNodeTexImage"); it.image = bpy.data.images.load(tex, check_existing=True)
        mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
        mul.inputs[0].default_value = 1.0
        nt.links.new(ca.outputs["Color"], mul.inputs[6]); nt.links.new(it.outputs["Color"], mul.inputs[7])
        nt.links.new(mul.outputs[2], em.inputs["Color"])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); ms = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(it.outputs["Alpha"], ms.inputs[0]); nt.links.new(tr.outputs[0], ms.inputs[1])
        nt.links.new(em.outputs[0], ms.inputs[2]); nt.links.new(ms.outputs[0], out.inputs["Surface"])
        m.use_backface_culling = False
        try: m.surface_render_method = "DITHERED"
        except Exception: pass
    else:
        nt.links.new(ca.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs[0], out.inputs["Surface"])
        m.use_backface_culling = True
    return m


def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


# ---------------------------------------------------------------- terrain ring
def build_terrain(coll, parent):
    verts, cols, faces = [], [], []
    radii = [R_IN * (R_OUT / R_IN) ** (i / (RINGS - 1)) for i in range(RINGS)]
    for i, r in enumerate(radii):
        for j in range(AZ_SEG):
            phi = 2 * math.pi * j / AZ_SEG
            X, Y = r * math.sin(phi), r * math.cos(phi)
            el = elev(X, Y); y = rel_y(X, Y, el)
            (cx, cy, cz), rp = compress(X, Y, y)
            if i == 0: cz = -0.30
            elif i == 1: cz = mix(-0.30, cz, 0.5)
            if rp < 400 and cz < -0.30: cz = -0.30
            verts.append((cx, cy, cz))
            # colour
            g = 60.0
            dE = (elev(X + g, Y) - elev(X - g, Y)) / (2 * g); dN = (elev(X, Y + g) - elev(X, Y - g)) / (2 * g)
            nrm = np.array([-dE, -dN, 1.0]); nrm /= np.linalg.norm(nrm)
            slope = math.hypot(dE, dN)
            if el > 120 or slope > 0.08: base = hexc("#47512f")
            else:
                nz = noise(X, Y)
                base = hexc("#5a6236") if nz > 0.75 else hexc("#8a8752") if nz > -0.1 else hexc("#6f7a3e")
            c = base * (0.78 + 0.22 * max(0.0, float(nrm @ SUN)))
            c = mix(c, haze_col(r), haze_h(r))
            c = mix(SEAM, c, sstep(330, 400, rp))
            cols.append(lin(c))
    n = len(verts)
    for j in range(AZ_SEG):  # outer skirt
        x, y, z = verts[(RINGS - 1) * AZ_SEG + j]; verts.append((x * 1.001, y * 1.001, -40.0)); cols.append(lin(SKY_H))
    for j in range(AZ_SEG):
        cols[(RINGS - 1) * AZ_SEG + j] = lin(SKY_H)
    for i in range(RINGS):
        for j in range(AZ_SEG):
            j2 = (j + 1) % AZ_SEG
            a, b = i * AZ_SEG + j, i * AZ_SEG + j2
            c, d = (i + 1) * AZ_SEG + j2, (i + 1) * AZ_SEG + j
            if i == RINGS - 1: c, d = n + j2, n + j
            # ring faces wound to point up; skirt faces wound to point toward the origin
            faces.append((a, d, c, b) if i == RINGS - 1 else (a, b, c, d))
    ob = new_obj("landscape_far_terrain", verts, faces, coll, parent)
    set_point_colors(ob, cols)
    return ob


# ---------------------------------------------------------------- tree lines
def build_trees(coll, parent):
    quads = []  # (X, Y, yaw, width, height, row/cell, colour hex)

    def add(r, phi, w, h, kind, colhex, jitter=25):
        X, Y = r * math.sin(phi), r * math.cos(phi)
        yaw = phi + math.radians(random.uniform(-jitter, jitter))  # quad spans perpendicular to the radius
        quads.append((X, Y, yaw, w, h, kind, colhex))

    for _ in range(110):   # Band A: town-edge trees, orchards, groves
        add(random.uniform(800, 1600), random.uniform(0, 2 * math.pi), random.uniform(30, 70),
            random.uniform(12, 22), random.choice((0, 2, 2)), "#3f4a2c")
    for _ in range(300):   # Band B: hedgerows + woodlots
        if random.random() < 0.6:
            add(random.uniform(1600, 5000), random.uniform(0, 2 * math.pi), random.uniform(80, 200),
                random.uniform(8, 14), 1, "#3f4a2c", 60)
        else:
            add(random.uniform(1600, 5000), random.uniform(0, 2 * math.pi), random.uniform(60, 150),
                random.uniform(15, 22), 0, "#3f4a2c")
    for _ in range(6):     # farm buildings (atlas row 3)
        cell = random.choice((0, 1, 2, 2))
        add(random.uniform(1800, 4000), random.uniform(0, 2 * math.pi), 20, 20, 10 + cell,
            "#d8d2c0" if cell == 0 else "#7d4a36", 10)
    for hp in meta["horizon_profile_eye_1p75m"]:   # ridge crown fringe along the skyline
        d = hp["at_km"] * 1000
        if d < 1600: continue
        phi0 = math.radians(hp["az"] + 5.5)
        for k in (-1, 1):
            add(d * random.uniform(0.97, 1.0), phi0 + math.radians(1.25 * k), d * 0.06, random.uniform(18, 22), 0, "#3f4a2c", 8)

    verts, faces, uvs, cols = [], [], [], []
    for (X, Y, yaw, w, h, kind, colhex) in quads:
        tx, ty = math.cos(yaw), -math.sin(yaw)  # tangent (perpendicular to the radial dir)
        corners = []
        for s in (-0.5, 0.5):
            px, py = X + tx * w * s, Y + ty * w * s
            gy = rel_y(px, py, elev(px, py))
            corners.append((px, py, gy - 1.5)); corners.append((px, py, gy + h))
        if kind >= 10:  # building cell
            cell = kind - 10; u0, u1 = cell / 4, (cell + 1) / 4; row = 3
        else:
            row = kind; span = min(1.0, (w / h) / 4); u0 = random.uniform(0, 1 - span); u1 = u0 + span
        v0, v1 = 1 - (row + 1) / 4 + 0.002, 1 - row / 4 - 0.002
        r = math.hypot(X, Y)
        col = lin(mix(hexc(colhex), haze_col(r), min(1.0, haze_h(r) + 0.05)))
        b = len(verts)
        for (px, py, pz) in corners:
            (cx, cy, cz), _ = compress(px, py, pz); verts.append((cx, cy, cz)); cols.append(col)
        faces.append((b, b + 2, b + 3, b + 1))
        uvs += [(u0, v0), (u0, v1), (u1, v0), (u1, v1)]  # per vertex
    ob = new_obj("landscape_far_trees", verts, faces, coll, parent)
    uvl = ob.data.uv_layers.new(name="UVMap")
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[ob.data.loops[li].vertex_index]
    set_point_colors(ob, cols)
    return ob


# ---------------------------------------------------------------- town silhouettes
def build_town(coll):
    verts, faces, fcols = [], [], []
    mute = [False]      # True: build nothing but still draw the random numbers (the rest stays identical)

    def face(vs, colhex):
        if mute[0]:
            return
        b = len(verts); verts.extend(vs); faces.append(tuple(range(b, b + len(vs)))); fcols.append(colhex)

    def gone(fn, *a, **k):
        """a silhouette replaced by assets/models/street-ends.glb: skipped, random draws kept"""
        mute[0] = True; fn(*a, **k); mute[0] = False

    def keep(fn, *a, **k):
        fn(*a, **k)

    def house(cx, cy, w, d, eave, ridge_along_x, wall, base=0.0, roof="#4a4a4e"):
        x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2
        z0, z1 = base - 0.6, base + eave
        rh = (d if ridge_along_x else w) * 0.35
        zr = z1 + rh
        if ridge_along_x:   # gables at the x ends
            face([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], wall)
            face([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], wall)
            face([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, cy, zr), (x0, y1, z1)], wall)
            face([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, cy, zr), (x1, y0, z1)], wall)
            face([(x0, y0, z1), (x1, y0, z1), (x1, cy, zr), (x0, cy, zr)], roof)
            face([(x1, y1, z1), (x0, y1, z1), (x0, cy, zr), (x1, cy, zr)], roof)
        else:               # gables at the y ends
            face([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], wall)
            face([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], wall)
            face([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (cx, y0, zr), (x0, y0, z1)], wall)
            face([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (cx, y1, zr), (x1, y1, z1)], wall)
            face([(x1, y0, z1), (x1, y1, z1), (cx, y1, zr), (cx, y0, zr)], roof)
            face([(x0, y1, z1), (x0, y0, z1), (cx, y0, zr), (cx, y1, zr)], roof)

    def tree(cx, cy, h=None, rad=None, base=0.0):
        h = h or random.uniform(10, 16); rad = rad or random.uniform(4, 6)
        zb, zl, zm, zt = base + 2.5, base + h * 0.3, base + h * 0.6, base + h
        n = 6; a0 = random.uniform(0, 1)
        ring = [(cx + rad * math.cos(a0 + 2 * math.pi * k / n), cy + rad * math.sin(a0 + 2 * math.pi * k / n), zm + random.uniform(-0.8, 0.8)) for k in range(n)]
        low = [(cx + 0.75 * rad * math.cos(a0 + 2 * math.pi * (k + 0.5) / n), cy + 0.75 * rad * math.sin(a0 + 2 * math.pi * (k + 0.5) / n), zl) for k in range(n)]
        for k in range(n):
            p, q = ring[k], ring[(k + 1) % n]; lp, lq = low[(k - 1) % n], low[k]
            face([p, q, (cx, cy, zt)], "#46532f")
            face([q, p, lq], "#46532f"); face([lp, lq, p], "#46532f")
            face([low[(k + 1) % n], lq, (cx, cy, zb)], "#3c4728")

    def steeple(cx, cy, base=0.0):
        s = 2.2; zt, zs = base + 18, base + 31
        c = [(cx - s, cy - s), (cx + s, cy - s), (cx + s, cy + s), (cx - s, cy + s)]
        for k in range(4):
            (ax, ay), (bx, by) = c[k], c[(k + 1) % 4]
            face([(ax, ay, base - 0.6), (bx, by, base - 0.6), (bx, by, zt), (ax, ay, zt)], "#ece8de")
            face([(ax, ay, zt), (bx, by, zt), (cx, cy, zs)], "#4a4a4e")

    CREAM, WHITE, BRICK = "#e2d9bf", "#ece8de", "#8a4b3a"
    walls = [CREAM, WHITE, BRICK, CREAM, WHITE]
    # Street ends (2026-11-11): assets/models/street-ends.glb now carries E1-E11 (hotel, 12-22 Main,
    # Soldiers' Monument, Presbyterian church at the head of the street; Vosseller Building, Doric
    # House, Methodist church, library, Deats Building) and the scene's backdrop-tree instances the
    # big trees there. Silhouettes standing on those buildings, on Capner St or on the lawns now
    # planted with backdrop trees are skipped with gone() (their random draws are kept, so every
    # other silhouette keeps its shape). The interim Presbyterian church is deleted.
    # north end (scene z -175..-250 -> Blender Y 175..250)
    for i, (y, w, d, e) in enumerate([(182, 12, 14, 10), (198, 10, 12, 8.5), (214, 14, 12, 11), (246, 11, 8, 8)]):
        (gone if y in (182, 198) else keep)(house, 20 + random.uniform(0, 3), y, w, d, e, i % 2 == 0, walls[i])
    for i, (y, w, d, e) in enumerate([(181, 11, 12, 9), (199, 13, 14, 11), (246, 12, 8, 8.5)]):
        (gone if y in (181, 199) else keep)(house, -20 - random.uniform(0, 3), y, w, d, e, i % 2 == 1, walls[i + 1])
    # (2026-11-11: the guessed white church + steeple that stood here, west side z -229, is gone:
    #  it was the Presbyterian church in the wrong place; street-ends.glb now has it, E8.)
    for y in (176, 191, 207, 222, 238):
        (gone if y in (176, 191) else keep)(tree, 12.8, y)
        (gone if y in (176, 191) else keep)(tree, -12.8, y + 5)
    for (x, y) in ((36, 190), (-37, 210), (34, 226), (-36, 244)):
        tree(x, y, 15, 6)
    # south end (scene z +70..+140 -> Blender Y -70..-140): west-side houses stay; east-side houses
    # and all eight trees are replaced (E5-E7, E10, backdrop trees on the west lawns)
    for i, y in enumerate((-80, -98, -118, -134)):
        house(-20 - random.uniform(0, 3), y, 10, 12, random.uniform(7.5, 9), i % 2 == 0, walls[i])
    for i, y in enumerate((-82, -104, -128)):
        gone(house, 20 + random.uniform(0, 3), y, 11, 12, random.uniform(7.5, 9), i % 2 == 1, walls[i + 2])
    for y in (-74, -91, -110, -126):
        gone(tree, 12.8, y); gone(tree, -12.8, y - 6)
    # Court St west: removed 2026-11-11 (assets/models/sidestreet-court.glb now carries
    #   the real buildings and the scene's backdrop-tree instances the maples).
    # Bloomfield Ave (east, scene z -89.8..-77.6 -> Blender Y 77.6..89.8), land falls to the east.
    #   x 60..146 removed 2026-11-11 (assets/models/sidestreet-bloomfield.glb: B1-B9, A8-A13, G1);
    #   only the silhouettes beyond the Opera House / G1 stay.
    for i, x in ((3, 168),):
        house(x, 97, 10, 10, 8, True, walls[i], base=-(x - 65) * 0.03)
    for i, x in ((2, 156),):
        house(x, 70.5, 10, 10, 8, True, walls[i + 1], base=-(x - 65) * 0.03)
    tree(150, 75.8, 13, 5, base=-(150 - 65) * 0.03)
    for x in (185,):
        tree(x, 91.6, 14, 5.5, base=-(x - 65) * 0.03); tree(x + 8, 75.8, 13, 5, base=-(x - 65) * 0.03)
    # (The interim Presbyterian church silhouette at (7.5, -368) was deleted 2026-11-11: E8 in
    #  assets/models/street-ends.glb.)

    ob = new_obj("landscape_town", verts, faces, coll)
    a = ob.data.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    for poly in ob.data.polygons:
        n = np.array(poly.normal[:])
        c = lin(hexc(fcols[poly.index]) * (0.78 + 0.22 * max(0.0, float(n @ SUN))))
        for li in poly.loop_indices:
            a.data[li].color = (*c, 1.0)
    ob.data.color_attributes.active_color = a; ob.data.color_attributes.render_color_index = 0
    return ob


# ---------------------------------------------------------------- export + GLB patch
def patch_glb(path):
    """Tree material: alphaMode MASK 0.5, double-sided (exporter may not infer it)."""
    data = open(path, "rb").read()
    jl = struct.unpack_from("<I", data, 12)[0]
    js = json.loads(data[20:20 + jl].decode("utf8")); rest = data[20 + jl:]
    for m in js.get("materials", []):   # emission -> KHR_materials_unlit (base colour = COLOR_0 x map)
        tex = m.pop("emissiveTexture", None); m.pop("emissiveFactor", None)
        m["pbrMetallicRoughness"] = {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 1}
        if tex: m["pbrMetallicRoughness"]["baseColorTexture"] = tex
        m["extensions"] = {"KHR_materials_unlit": {}}
        if m.get("name") == "M_Landscape_Trees":
            m["alphaMode"] = "MASK"; m["alphaCutoff"] = 0.5; m["doubleSided"] = True
    js["extensionsUsed"] = sorted(set(js.get("extensionsUsed", [])) | {"KHR_materials_unlit"})
    nj = json.dumps(js, separators=(",", ":")).encode("utf8")
    nj += b" " * ((4 - len(nj) % 4) % 4)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(nj) + len(rest)) + struct.pack("<II", len(nj), 0x4E4F534A) + nj + rest
    open(path, "wb").write(out)


def export(coll):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in coll.objects: ob.select_set(True)
    kw = dict(filepath=GLB, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
              export_texcoords=True, export_normals=True, export_materials="EXPORT", export_extras=False)
    try: bpy.ops.export_scene.gltf(**kw, export_vertex_color="ACTIVE")
    except TypeError: bpy.ops.export_scene.gltf(**kw, export_colors=True)
    patch_glb(GLB)


# ---------------------------------------------------------------- previews
def preview(name, yaw_deg, pitch_deg=1.0, lens=35):
    sc = bpy.context.scene
    cam = bpy.data.objects.get("PV_Cam")
    if not cam:
        cam = bpy.data.objects.new("PV_Cam", bpy.data.cameras.new("PV_Cam")); sc.collection.objects.link(cam)
    cam.data.lens = lens; cam.data.clip_end = 5000; cam.location = (0, 0, EYE)
    cam.rotation_euler = (math.radians(90 + pitch_deg), 0, -math.radians(yaw_deg))
    sc.camera = cam
    sc.render.filepath = os.path.join(PREV, f"landscape-{name}.png"); bpy.ops.render.render(write_still=True)


def setup_preview_scene():
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try: sc.render.engine = eng; break
        except TypeError: pass
    sc.render.resolution_x, sc.render.resolution_y = 1280, 560
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.get("LS_World") or bpy.data.worlds.new("LS_World"); sc.world = w
    w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputWorld"); bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = 0.35
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
    mx.inputs[6].default_value = (*lin(SKY_H), 1); mx.inputs[7].default_value = (0.42, 0.55, 0.78, 1)
    nt.links.new(tc.outputs["Generated"], sp.inputs[0]); nt.links.new(sp.outputs[2], mr.inputs[0])
    nt.links.new(mr.outputs[0], mx.inputs[0]); nt.links.new(mx.outputs[2], bg.inputs[0])
    nt.links.new(bg.outputs[0], o.inputs[0])
    # temporary ground disc (scene: 335 m disc #6f6a45, partly fogged)
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=335, fill_type="NGON", location=(0, 0, 0))
    g = bpy.context.active_object; g.name = "PV_Ground"
    gm = bpy.data.materials.new("PV_Ground"); gm.use_nodes = True; gn = gm.node_tree; gn.nodes.clear()
    ge = gn.nodes.new("ShaderNodeEmission"); ge.inputs[0].default_value = (*lin(mix(hexc("#6f6a45"), SKY_H, 0.55)), 1)
    go = gn.nodes.new("ShaderNodeOutputMaterial"); gn.links.new(ge.outputs[0], go.inputs[0]); g.data.materials.append(gm)
    return g


def main(render=True):
    coll = bpy.data.collections.get("Landscape")
    if coll:
        for ob in list(coll.objects): bpy.data.objects.remove(ob, do_unlink=True)
    else:
        coll = bpy.data.collections.new("Landscape"); bpy.context.scene.collection.children.link(coll)
    for m in [m for m in bpy.data.materials if m.name.startswith(("M_Landscape", "PV_"))]: bpy.data.materials.remove(m)
    far = bpy.data.objects.new("landscape_far", None); coll.objects.link(far)
    for me in [me for me in bpy.data.meshes if me.users == 0]: bpy.data.meshes.remove(me)
    t = build_terrain(coll, far); tr = build_trees(coll, far); tw = build_town(coll)
    t.data.shade_smooth()   # shared vertices (no lighting is used; keeps the GLB small)
    t.data.materials.append(make_mat("M_Landscape_Terrain"))
    tr.data.materials.append(make_mat("M_Landscape_Trees", TEX))
    tw.data.materials.append(make_mat("M_Landscape_Town"))
    for ob in (t, tr, tw): print("TRIS", ob.name, tri_count(ob))
    print("TRIS total", sum(tri_count(o) for o in (t, tr, tw)))
    export(coll); print("GLB", GLB, os.path.getsize(GLB), "bytes")
    if render:
        vt = bpy.context.scene.view_settings.view_transform
        g = setup_preview_scene()
        preview("north", 0); preview("west-ridge", -55)
        bpy.data.objects.remove(g, do_unlink=True)
        bpy.context.scene.view_settings.view_transform = vt
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("saved", BLEND)


main()
