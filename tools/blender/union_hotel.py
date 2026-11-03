"""
union_hotel.py - builds the Union Hotel (70-76 Main St, Flemington, c. 1920) in Blender.

Run inside Blender (Scripting tab, or via the MCP connection):
    exec(open(r"<project>/tools/blender/union_hotel.py").read())

Every run deletes and rebuilds the "UnionHotel" collection, so edit the numbers
below and run again.

Sources: 1921 Sanborn map sheet 2 (footprint, 4 storeys, brick, frame veranda),
1910s postcard and 1963 HABS photos (elevation details). See SOURCES.md.

Coordinates (metres, Blender Z-up):
    X  along Main Street, centred on the building
    Y  depth: y = 0 is the front edge of the veranda; the brick front wall is at
       y = 3.0 and the building extends toward +Y. The street is toward -Y.
    Z  up from the sidewalk
glTF export turns -Y into +Z, which matches the A-Frame scene's "front faces +Z".
"""

import math
import bpy
import bmesh

# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------
W = 29.7            # frontage along Main Street (map: 97 ft)
FRONT = 3.0         # brick front wall, behind the veranda
BACK = 11.6         # back wall (map: 8.6 m deep main block)
WALL = 0.5          # wall thickness
PLINTH = 0.8        # veranda floor / ground floor level
FLOOR = 3.6         # storey height
WALL_TOP = PLINTH + 3 * FLOOR          # 11.6, top of the brick
CORNICE_TOP = WALL_TOP + 0.5           # 12.1
BAYS = 11
BAY = W / BAYS

# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

def _new_material(name):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat, nt, bsdf


def _hex(h):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, 1.0)


def plain(name, color, rough=0.8):
    mat, nt, bsdf = _new_material(name)
    bsdf.inputs["Base Color"].default_value = _hex(color)
    bsdf.inputs["Roughness"].default_value = rough
    mat.diffuse_color = _hex(color)
    return mat


PROJECT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
BRICK_TILE = 0.84   # metres of wall covered by one repeat of brick_red.jpg


def brick(name, image_path):
    """Image-textured brick (exports to glTF). UVs come from brick_uvs()."""
    mat, nt, bsdf = _new_material(name)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(image_path, check_existing=True)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    mat.diffuse_color = _hex("#8c3b2a")
    return mat


def brick_uvs(obj):
    """Wrap the brick image round the walls: u follows x + y, v follows height."""
    mesh = obj.data
    uv = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        co = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = ((co.x + co.y) / BRICK_TILE, co.z / BRICK_TILE)


def slate(name, color):
    mat, nt, bsdf = _new_material(name)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 40.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Base Color"].default_value = _hex(color)
    bsdf.inputs["Roughness"].default_value = 0.75
    mat.diffuse_color = _hex(color)
    return mat


MATS = {
    "Brick": brick("UH_Brick", PROJECT + r"\assets\textures\brick_red.jpg"),
    "Trim": plain("UH_Trim", "#ece3cd", 0.6),
    "Slate": slate("UH_Slate", "#4e5756"),
    "Glass": plain("UH_Glass", "#15191d", 0.12),
    "Wood": plain("UH_Wood", "#6f5a45", 0.8),
    "Door": plain("UH_Door", "#5d6b5c", 0.7),       # painted grey-green doors
    "Boards": plain("UH_Boards", "#857a69", 0.85),
    "Stone": plain("UH_Stone", "#a39b8e", 0.9),
    "Sign": plain("UH_Sign", "#2f3a2c", 0.7),
    "Roof": plain("UH_Roof", "#5a5e5d", 0.55),     # flat tin roofs
}

# ---------------------------------------------------------------------------
# Mesh builder
# ---------------------------------------------------------------------------

class MB:
    """Collects geometry for one material. Shapes are added in place."""

    def __init__(self):
        self.bm = bmesh.new()

    def _closed(self, faces):
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)

    @staticmethod
    def _pt(axis, u, d, v):
        # axis 'y': outline in the X-Z plane, depth along Y (front/back walls)
        # axis 'x': outline in the Y-Z plane, depth along X (side walls)
        return (u, d, v) if axis == "y" else (d, u, v)

    def prism(self, pts, d0, d1, axis="y"):
        """Extrude a 2D outline [(u, v), ...] between depths d0 and d1."""
        bm = self.bm
        a = [bm.verts.new(self._pt(axis, u, d0, v)) for u, v in pts]
        b = [bm.verts.new(self._pt(axis, u, d1, v)) for u, v in pts]
        faces = [bm.faces.new(a), bm.faces.new(list(reversed(b)))]
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
        self._closed(faces)

    def box(self, x0, x1, y0, y1, z0, z1):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)

    def ring_arch(self, cu, zs, r_in, r_out, d0, d1, axis="y", segs=12):
        """Half-round band (hood mould, archivolt) springing at height zs."""
        bm = self.bm
        ts = [math.pi * i / segs for i in range(segs + 1)]
        def ring(r, d):
            return [bm.verts.new(self._pt(axis, cu + r * math.cos(t), d, zs + r * math.sin(t))) for t in ts]
        of, inf, ob, ib = ring(r_out, d0), ring(r_in, d0), ring(r_out, d1), ring(r_in, d1)
        faces = []
        for i in range(segs):
            faces.append(bm.faces.new([of[i], of[i + 1], inf[i + 1], inf[i]]))
            faces.append(bm.faces.new([ob[i], ib[i], ib[i + 1], ob[i + 1]]))
            faces.append(bm.faces.new([of[i], ob[i], ob[i + 1], of[i + 1]]))
            faces.append(bm.faces.new([inf[i], inf[i + 1], ib[i + 1], ib[i]]))
        faces.append(bm.faces.new([of[0], inf[0], ib[0], ob[0]]))
        faces.append(bm.faces.new([of[-1], ob[-1], ib[-1], inf[-1]]))
        self._closed(faces)

    def lathe(self, profile, cx, cy, z0=0.0, segs=12):
        """Turned column from a profile [(radius, height), ...], bottom to top."""
        bm = self.bm
        rings = []
        for r, z in profile:
            if r == 0:
                rings.append([bm.verts.new((cx, cy, z0 + z))])
            else:
                rings.append([bm.verts.new((cx + r * math.cos(2 * math.pi * k / segs),
                                            cy + r * math.sin(2 * math.pi * k / segs), z0 + z))
                              for k in range(segs)])
        faces = []
        for a, b in zip(rings, rings[1:]):
            for k in range(segs):
                k2 = (k + 1) % segs
                if len(a) == 1:
                    faces.append(bm.faces.new([a[0], b[k], b[k2]]))
                elif len(b) == 1:
                    faces.append(bm.faces.new([a[k], a[k2], b[0]]))
                else:
                    faces.append(bm.faces.new([a[k], a[k2], b[k2], b[k]]))
        self._closed(faces)

    def stepped_roof(self, x0, x1, y0, y1, z0, profile):
        """Mansard-style roof: rectangles inset by d at height z, open underneath."""
        bm = self.bm
        rings = []
        for d, dz in profile:
            rings.append([bm.verts.new(p) for p in [
                (x0 + d, y0 + d, z0 + dz), (x1 - d, y0 + d, z0 + dz),
                (x1 - d, y1 - d, z0 + dz), (x0 + d, y1 - d, z0 + dz)]])
        for a, b in zip(rings, rings[1:]):
            for i in range(4):
                j = (i + 1) % 4
                bm.faces.new([a[i], a[j], b[j], b[i]])
        bm.faces.new(rings[-1])

    def to_object(self, name, mat, col):
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        obj = bpy.data.objects.new(name, mesh)
        mesh.materials.append(mat)
        col.objects.link(obj)
        return obj


def arched(cu, w, z0, zs, segs=10):
    """Outline of a round-headed opening: straight sides from z0 up to zs, half-circle above."""
    r = w / 2
    return [(cu - r, z0), (cu + r, z0)] + [
        (cu + r * math.cos(math.pi * i / segs), zs + r * math.sin(math.pi * i / segs))
        for i in range(segs + 1)]


# ---------------------------------------------------------------------------
# Scene setup
# ---------------------------------------------------------------------------

def fresh_collection(name):
    col = bpy.data.collections.get(name)
    if col:
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    for mesh in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(mesh)
    return col


col = fresh_collection("UnionHotel")
G = {k: MB() for k in MATS}      # geometry per material
CUT = MB()                       # window cutters for the walls
WALLS = MB()                     # brick walls (cut by CUT, then merged into Brick)

# Each wall: (axis, outer face depth, outward sign)
FRONT_WALL = ("y", FRONT, -1)
LEFT_WALL = ("x", -W / 2, -1)
RIGHT_WALL = ("x", W / 2, 1)


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def window(wall, cu, w, z_sill, z_spring, door=False):
    """A round-headed window (or door, see door_leaves): opening, glass, bars, sill, hood."""
    axis, face, out = wall
    D = lambda k: face + out * k        # k > 0 is outside the wall, k < 0 inside
    r = w / 2
    CUT.prism(arched(cu, w, z_sill, z_spring), D(0.2), D(-WALL - 0.2), axis)
    G["Trim"].ring_arch(cu, z_spring, r + 0.02, r + 0.17, D(0.09), D(-0.02), axis)
    if door:
        door_leaves(wall, cu, w, z_sill, z_spring)
        return
    G["Glass"].prism(arched(cu, w, z_sill, z_spring), D(-0.2), D(-0.23), axis)
    # sash: one meeting rail and a centre bar (two-over-two)
    mid = z_sill + (z_spring - z_sill) * 0.5
    G["Trim"].prism(rect(cu - 0.03, cu + 0.03, z_sill, z_spring + r * 0.95), D(-0.16), D(-0.2), axis)
    G["Trim"].prism(rect(cu - r, cu + r, mid - 0.04, mid + 0.04), D(-0.16), D(-0.2), axis)
    G["Trim"].prism(rect(cu - r, cu + r, z_spring - 0.03, z_spring + 0.03), D(-0.16), D(-0.2), axis)
    G["Trim"].prism(rect(cu - r - 0.12, cu + r + 0.12, z_sill - 0.1, z_sill), D(0.12), D(-0.1), axis)


def door_leaves(wall, cu, w, z_sill, z_spring):
    """Doorway as in the 1910s postcards and HABS photo: white frame, glass fanlight
    with radiating bars in the arch, and painted panelled doors below (two leaves if wide)."""
    axis, face, out = wall
    D = lambda k: face + out * k
    r = w / 2
    f = 0.09                                         # frame width
    # fanlight glass and its radiating bars
    G["Glass"].prism([(cu + (r - f) * math.cos(math.pi * i / 12), z_spring + (r - f) * math.sin(math.pi * i / 12))
                      for i in range(13)], D(-0.2), D(-0.23), axis)
    for a in (math.pi / 4, math.pi / 2, 3 * math.pi / 4):
        ca, sa = math.cos(a), math.sin(a)
        nx, nz = -sa * 0.015, ca * 0.015
        x1, z1 = cu + (r - f) * ca, z_spring + (r - f) * sa
        G["Trim"].prism([(cu + nx, z_spring + nz), (cu - nx, z_spring - nz), (x1 - nx, z1 - nz), (x1 + nx, z1 + nz)],
                        D(-0.16), D(-0.2), axis)
    # white frame: jambs, transom bar, inner arch
    G["Trim"].prism(rect(cu - r, cu - r + f, z_sill, z_spring), D(0.0), D(-0.25), axis)
    G["Trim"].prism(rect(cu + r - f, cu + r, z_sill, z_spring), D(0.0), D(-0.25), axis)
    G["Trim"].prism(rect(cu - r, cu + r, z_spring - 0.12, z_spring), D(0.0), D(-0.25), axis)
    G["Trim"].ring_arch(cu, z_spring, r - f, r, D(0.0), D(-0.25), axis)
    # door leaves with two raised panels each (tall upper, short lower)
    top = z_spring - 0.12
    leaves = 2 if w > 1.3 else 1
    inner = w - 2 * f
    leaf = inner / leaves
    for i in range(leaves):
        x0 = cu - inner / 2 + i * leaf + 0.008
        x1 = x0 + leaf - 0.016
        G["Door"].prism(rect(x0, x1, z_sill, top), D(-0.15), D(-0.21), axis)
        p0, p1 = x0 + 0.1, x1 - 0.1
        G["Door"].prism(rect(p0, p1, z_sill + 0.22, z_sill + 0.8), D(-0.13), D(-0.15), axis)
        G["Door"].prism(rect(p0, p1, z_sill + 1.0, top - 0.18), D(-0.13), D(-0.15), axis)
        knob_x = x1 - 0.09 if i == leaves - 1 or leaves == 1 else x1 - 0.06
        G["Trim"].prism(rect(knob_x - 0.025, knob_x + 0.025, z_sill + 0.98, z_sill + 1.03), D(-0.11), D(-0.15), axis)


# ---------------------------------------------------------------------------
# Brick walls with window openings
# ---------------------------------------------------------------------------

# One solid block, hollowed out by an inner cutter: the boolean needs a single
# closed shell (four separate touching slabs confuse it).
WALLS.box(-W / 2, W / 2, FRONT, BACK, 0, WALL_TOP)
CUT.box(-W / 2 + WALL, W / 2 - WALL, FRONT + WALL, BACK - WALL, -1, WALL_TOP + 1)

bay_x = [-W / 2 + BAY * (i + 0.5) for i in range(BAYS)]
for x in bay_x:
    window(FRONT_WALL, x, 1.05, PLINTH + FLOOR + 0.75, PLINTH + FLOOR + 2.5)      # 2nd floor
    window(FRONT_WALL, x, 1.0, PLINTH + 2 * FLOOR + 0.7, PLINTH + 2 * FLOOR + 2.25)  # 3rd floor
for i, x in enumerate(bay_x):                                                    # ground floor
    if i == 5:
        window(FRONT_WALL, x, 1.6, PLINTH, PLINTH + 2.7, door=True)              # main entrance
    elif i in (2, 8):
        window(FRONT_WALL, x, 1.15, PLINTH, PLINTH + 2.7, door=True)
    else:
        window(FRONT_WALL, x, 1.1, PLINTH + 0.5, PLINTH + 2.7)
for wall in (LEFT_WALL, RIGHT_WALL):
    for y in (5.6, 9.0):
        window(wall, y, 1.0, PLINTH + 0.5, PLINTH + 2.6)
        window(wall, y, 1.0, PLINTH + FLOOR + 0.75, PLINTH + FLOOR + 2.5)
        window(wall, y, 1.0, PLINTH + 2 * FLOOR + 0.7, PLINTH + 2 * FLOOR + 2.25)

# Rear wing (map: offset 2.35 m north of centre, 3 storeys).
G["Brick"].box(-2.35 - 3.4, -2.35 + 3.4, BACK, BACK + 10.3, 0, 10.8)
G["Trim"].box(-2.35 - 3.6, -2.35 + 3.6, BACK, BACK + 10.5, 10.8, 11.0)
G["Roof"].box(-2.35 - 3.5, -2.35 + 3.5, BACK, BACK + 10.4, 11.0, 11.05)

# ---------------------------------------------------------------------------
# Cornice with paired brackets
# ---------------------------------------------------------------------------

G["Trim"].box(-W / 2 - 0.5, W / 2 + 0.5, FRONT - 0.5, BACK + 0.5, WALL_TOP, WALL_TOP + 0.15)
G["Trim"].box(-W / 2 - 0.6, W / 2 + 0.6, FRONT - 0.6, BACK + 0.6, WALL_TOP + 0.15, CORNICE_TOP)
G["Trim"].box(-W / 2 - 0.02, W / 2 + 0.02, FRONT - 0.04, BACK, WALL_TOP - 0.35, WALL_TOP)   # frieze
bracket = [(FRONT, WALL_TOP), (FRONT - 0.45, WALL_TOP), (FRONT - 0.45, WALL_TOP - 0.12),
           (FRONT - 0.2, WALL_TOP - 0.3), (FRONT - 0.1, WALL_TOP - 0.55), (FRONT, WALL_TOP - 0.55)]
for k in range(BAYS + 1):
    x = -W / 2 + k * BAY
    for dx in (-0.2, 0.2):
        bx = min(max(x + dx, -W / 2 + 0.1), W / 2 - 0.1)
        G["Trim"].prism(bracket, bx - 0.07, bx + 0.07, axis="x")

# ---------------------------------------------------------------------------
# Mansard roof, end towers, dormers, central pavilion, chimneys
# ---------------------------------------------------------------------------

TOWER_W = 3.2
G["Slate"].stepped_roof(-W / 2 + 0.1, W / 2 - 0.1, FRONT + 0.1, BACK - 0.1, CORNICE_TOP,
                        [(0, 0), (0.12, 0.3), (0.75, 3.0), (0.85, 3.3)])
G["Trim"].box(-W / 2 + 0.8, W / 2 - 0.8, FRONT + 0.8, BACK - 0.8, CORNICE_TOP + 3.3, CORNICE_TOP + 3.4)
G["Roof"].box(-W / 2 + 0.9, W / 2 - 0.9, FRONT + 0.9, BACK - 0.9, CORNICE_TOP + 3.4, CORNICE_TOP + 3.45)

for s in (-1, 1):
    x0, x1 = (-W / 2, -W / 2 + TOWER_W) if s < 0 else (W / 2 - TOWER_W, W / 2)
    G["Slate"].stepped_roof(x0 + 0.1, x1 - 0.1, FRONT + 0.1, BACK - 0.1, CORNICE_TOP,
                            [(0, 0), (0.1, 0.3), (0.45, 4.6), (0.5, 4.9)])
    G["Trim"].box(x0 + 0.45, x1 - 0.45, FRONT + 0.45, BACK - 0.45, CORNICE_TOP + 4.9, CORNICE_TOP + 5.15)
    G["Roof"].box(x0 + 0.6, x1 - 0.6, FRONT + 0.6, BACK - 0.6, CORNICE_TOP + 5.15, CORNICE_TOP + 5.25)


def dormer(cx, z0, w, h, y_face):
    """Dormer with an arched window and a round hood, its face at y_face."""
    zs = z0 + h
    G["Slate"].prism(arched(cx, w + 0.3, z0, zs), y_face, y_face + 1.8)
    G["Trim"].prism(arched(cx, w + 0.16, z0 + 0.05, zs), y_face - 0.04, y_face + 0.02)
    G["Glass"].prism(arched(cx, w - 0.12, z0 + 0.2, zs), y_face - 0.07, y_face - 0.04)
    G["Trim"].prism([(cx - 0.025, z0 + 0.2), (cx + 0.025, z0 + 0.2), (cx + 0.025, zs + w * 0.4),
                     (cx - 0.025, zs + w * 0.4)], y_face - 0.1, y_face - 0.07)
    G["Trim"].ring_arch(cx, zs, w / 2 + 0.15, w / 2 + 0.32, y_face - 0.2, y_face + 0.3)
    G["Trim"].box(cx - w / 2 - 0.25, cx + w / 2 + 0.25, y_face - 0.2, y_face + 0.2, z0 - 0.08, z0 + 0.04)


for i in (1, 2, 3, 7, 8, 9):
    dormer(bay_x[i], CORNICE_TOP + 0.35, 0.9, 1.25, FRONT + 0.25)
for s in (-1, 1):
    dormer(s * (W / 2 - TOWER_W / 2), CORNICE_TOP + 1.2, 1.0, 1.6, FRONT + 0.2)

# Central pavilion: straight front, curved top, the hotel's name, paired windows.
PW, PY0, PY1, PH = 5.0, FRONT + 0.15, FRONT + 4.5, 3.3
pz = CORNICE_TOP + PH
G["Slate"].box(-PW / 2, PW / 2, PY0, PY1, CORNICE_TOP, pz)
G["Slate"].prism([(PW / 2 * math.cos(math.pi * i / 16), pz + PW / 2 * math.sin(math.pi * i / 16))
                  for i in range(17)], PY0, PY1)
G["Trim"].ring_arch(0, pz, PW / 2 - 0.05, PW / 2 + 0.25, PY0 - 0.2, PY0 + 0.25, segs=16)
G["Trim"].box(-PW / 2 - 0.25, PW / 2 + 0.25, PY0 - 0.2, PY0 + 0.25, pz - 0.25, pz)
for s in (-1, 1):
    G["Trim"].box(s * PW / 2 - 0.15, s * PW / 2 + 0.15, PY0 - 0.12, PY0 + 0.1, CORNICE_TOP, pz)
G["Sign"].box(-2.0, 2.0, PY0 - 0.06, PY0, pz - 0.95, pz - 0.35)
for x in (-0.6, 0.6):
    G["Trim"].prism(arched(x, 0.95, CORNICE_TOP + 0.35, CORNICE_TOP + 1.85), PY0 - 0.05, PY0 + 0.01)
    G["Glass"].prism(arched(x, 0.75, CORNICE_TOP + 0.45, CORNICE_TOP + 1.85), PY0 - 0.08, PY0 - 0.05)
G["Glass"].prism(arched(0, 1.6, pz + 0.2, pz + 0.55), PY0 - 0.03, PY0 + 0.02)   # lunette in the arch

for x, y in ((-9.6, 8.5), (-4.2, 9.5), (4.2, 9.5), (9.6, 8.5)):
    G["Brick"].box(x - 0.45, x + 0.45, y - 0.3, y + 0.3, CORNICE_TOP + 2.0, CORNICE_TOP + 5.4)
    G["Trim"].box(x - 0.55, x + 0.55, y - 0.4, y + 0.4, CORNICE_TOP + 5.4, CORNICE_TOP + 5.6)

# ---------------------------------------------------------------------------
# Two-storey veranda
# ---------------------------------------------------------------------------

G["Brick"].box(-W / 2, W / 2, 0.1, FRONT, 0, PLINTH - 0.2)                  # foundation
G["Boards"].box(-W / 2, W / 2, 0, FRONT, PLINTH - 0.2, PLINTH)              # porch floor
for k in range(3):                                                         # steps
    G["Stone"].box(-W / 2 + 0.6, W / 2 - 0.6, -0.4 * (k + 1), -0.4 * k, 0, PLINTH - 0.2 * (k + 1))

POST_Y = 0.3
posts = [-W / 2 + 0.2 + i * (W - 0.4) / 11 for i in range(12)]
GALLERY = PLINTH + FLOOR + 0.45        # top of the gallery floor (4.85)
TOP = 7.65                             # underside of the veranda roof


def turned(h, r):
    return [(0, 0), (r * 1.5, 0), (r * 1.5, 0.12), (r * 1.15, 0.2), (r, 0.32),
            (r * 0.85, h - 0.42), (r * 1.05, h - 0.3), (r * 1.35, h - 0.14), (r * 1.4, h), (0, h)]


for x in posts:
    G["Trim"].lathe(turned(FLOOR, 0.11), x, POST_Y, PLINTH)
    G["Trim"].lathe(turned(TOP - GALLERY, 0.095), x, POST_Y, GALLERY)

# Spindle frieze under the gallery floor, between the ground-floor posts.
G["Trim"].box(-W / 2, W / 2, POST_Y - 0.06, POST_Y + 0.06, PLINTH + FLOOR - 0.5, PLINTH + FLOOR - 0.44)
for a, b in zip(posts, posts[1:]):
    n = int((b - a - 0.3) / 0.16)
    for k in range(n):
        x = a + 0.15 + (k + 0.5) * (b - a - 0.3) / n
        G["Trim"].box(x - 0.022, x + 0.022, POST_Y - 0.022, POST_Y + 0.022, PLINTH + FLOOR - 0.44, PLINTH + FLOOR)

# Gallery floor fascia and balustrade.
G["Trim"].box(-W / 2, W / 2, 0, FRONT, PLINTH + FLOOR, GALLERY)
G["Trim"].box(-W / 2, W / 2, POST_Y - 0.08, POST_Y + 0.08, GALLERY + 0.04, GALLERY + 0.12)
G["Trim"].box(-W / 2, W / 2, POST_Y - 0.1, POST_Y + 0.1, GALLERY + 0.85, GALLERY + 0.97)
for a, b in zip(posts, posts[1:]):
    n = int((b - a - 0.3) / 0.15)
    for k in range(n):
        x = a + 0.15 + (k + 0.5) * (b - a - 0.3) / n
        G["Trim"].box(x - 0.025, x + 0.025, POST_Y - 0.025, POST_Y + 0.025, GALLERY + 0.12, GALLERY + 0.85)

# Round arches between the gallery posts.
for a, b in zip(posts, posts[1:]):
    cx, span = (a + b) / 2, b - a
    r = span / 2 - 0.13
    zs = TOP - r - 0.12
    panel = [(cx - span / 2, TOP), (cx - span / 2, zs)] + [
        (cx + r * math.cos(math.pi * (1 - i / 12)), zs + r * math.sin(math.pi * (1 - i / 12)))
        for i in range(13)] + [(cx + span / 2, zs), (cx + span / 2, TOP)]
    G["Trim"].prism(panel, POST_Y - 0.04, POST_Y + 0.04)
    G["Trim"].ring_arch(cx, zs, r, r + 0.07, POST_Y - 0.08, POST_Y + 0.06)

# Veranda roof: fascia and a projecting cornice.
G["Trim"].box(-W / 2 - 0.1, W / 2 + 0.1, -0.1, FRONT, TOP, TOP + 0.3)
G["Trim"].box(-W / 2 - 0.25, W / 2 + 0.25, -0.25, FRONT, TOP + 0.3, TOP + 0.42)
G["Roof"].box(-W / 2 - 0.15, W / 2 + 0.15, -0.15, FRONT, TOP + 0.42, TOP + 0.47)

# ---------------------------------------------------------------------------
# Build objects
# ---------------------------------------------------------------------------

walls = WALLS.to_object("UH_Walls", MATS["Brick"], col)
cutters = CUT.to_object("UH_Cutters", MATS["Trim"], col)
mod = walls.modifiers.new("Windows", "BOOLEAN")
mod.operation = "DIFFERENCE"
solvers = [i.identifier for i in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items]
mod.solver = "EXACT" if "EXACT" in solvers else solvers[0]
mod.object = cutters
dg = bpy.context.evaluated_depsgraph_get()
cut_mesh = bpy.data.meshes.new_from_object(walls.evaluated_get(dg))
walls.modifiers.clear()
old = walls.data
walls.data = cut_mesh
cut_mesh.name = "UH_Walls"
bpy.data.meshes.remove(old)
bpy.data.objects.remove(cutters, do_unlink=True)

for key, builder in G.items():
    if builder.bm.faces:
        builder.to_object("UH_" + key, MATS[key], col)
    else:
        builder.bm.free()

brick_uvs(walls)
brick_uvs(bpy.data.objects["UH_Brick"])

# Lettering on the pavilion sign.
curve = bpy.data.curves.new("UH_SignText", "FONT")
curve.body = "UNION HOTEL"
curve.align_x = "CENTER"
curve.size = 0.42
curve.extrude = 0.015
text = bpy.data.objects.new("UH_SignText_tmp", curve)
col.objects.link(text)
text.location = (0, PY0 - 0.08, pz - 0.8)
text.rotation_euler = (math.radians(90), 0, 0)
dg = bpy.context.evaluated_depsgraph_get()
letters = bpy.data.meshes.new_from_object(text.evaluated_get(dg))
letters.transform(text.matrix_world)
bpy.data.objects.remove(text, do_unlink=True)
bpy.data.curves.remove(curve)
letters.name = "UH_Letters"
_bm = bmesh.new()                       # text meshes come with their flat faces pointing
_bm.from_mesh(letters)                  # into the sign; turn them toward the street (-Y)
_bm.normal_update()                     # so the lettering bakes lit
bmesh.ops.reverse_faces(_bm, faces=[f for f in _bm.faces if f.normal.y > 0.5])
_bm.to_mesh(letters)
_bm.free()
lobj = bpy.data.objects.new("UH_Letters", letters)
letters.materials.clear()
letters.materials.append(MATS["Trim"])
col.objects.link(lobj)

tris = sum(len(p.vertices) - 2 for o in col.objects for p in o.data.polygons)
print("Union Hotel built:", len(col.objects), "objects,", tris, "triangles")
# Materials, baked lighting and GLB export: run union_hotel_bake.py (it runs this file first).
