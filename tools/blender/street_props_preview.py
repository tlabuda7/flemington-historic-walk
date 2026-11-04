"""
Preview renders of the street props kit for the reviewer.

Run in Blender after street_props_bake.py:
    exec(open(r"<project>/tools/blender/street_props_preview.py").read())

EEVEE, view transform "Standard", lit roughly like the scene (the kit uses a lit material):
warm directional light from the scene's key-light position (-40, 35, 25) -> Blender (-40, -25, 35),
plus a warm-grey ambient world standing in for the hemisphere light. The props are laid out in a
row (the bake's LINEUP) with a 1.75 m person-height reference, then put back at the origin.
Writes assets/models/previews/street-props-*.png (1280 px wide) and restores the scene settings.
"""
import bpy, os, math
from mathutils import Vector

ROOT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
OUT = os.path.join(ROOT, r"assets\models\previews")
BLEND = os.path.join(ROOT, r"assets\models\source\street-props.blend")
KEY_DIR = Vector((-40, -25, 35)).normalized()
LINEUP = {"pole": (0, 0, 0), "pole_lamp": (0, 0, 0), "arc_lamp": (2.2, 0, 8.35), "fountain": (4.6, 0, 0),
          "hitching_post": (6.6, 0, 0), "carriage_step": (8.0, 0, 0), "hydrant": (9.6, 0, 0),
          "shop_goods": (11.4, 0, 0), "sandwich_board_groceries": (13.4, 0, 0),
          "sandwich_board_icecream": (14.8, 0, 0), "bicycle": (16.4, 0, 0), "gas_pump": (18.2, 0, 0)}
PERSON_X = 3.2


def look_from(cam, eye, target):
    cam.location = eye
    d = (Vector(target) - Vector(eye)).normalized()
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def plain_mat(name, rgb, rough=0.95):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


def setup():
    sc = bpy.context.scene
    saved = dict(engine=sc.render.engine, vt=sc.view_settings.view_transform, look=sc.view_settings.look,
                 x=sc.render.resolution_x, y=sc.render.resolution_y, cam=sc.camera, world=sc.world,
                 fp=sc.render.filepath, pct=sc.render.resolution_percentage)
    c = bpy.data.collections.get("SP_Preview") or bpy.data.collections.new("SP_Preview")
    if c.name not in sc.collection.children:
        sc.collection.children.link(c)
    c.hide_render = False
    for o in list(c.objects):
        bpy.data.objects.remove(o)
    ld = bpy.data.lights.get("SP_Key") or bpy.data.lights.new("SP_Key", "SUN")
    ld.energy = 3.0; ld.color = (1.0, 0.85, 0.64); ld.angle = math.radians(1.5)
    sun = bpy.data.objects.new("SP_Key", ld); c.objects.link(sun)
    sun.rotation_euler = (-KEY_DIR).to_track_quat("-Z", "Y").to_euler()
    w = bpy.data.worlds.get("SP_Sky") or bpy.data.worlds.new("SP_Sky")
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.62, 0.60, 0.56, 1.0); bg.inputs[1].default_value = 0.85
    sc.world = w
    me = bpy.data.meshes.new("SP_PvGround")
    me.from_pydata([(-12, -14, 0), (32, -14, 0), (32, 10, 0), (-12, 10, 0)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new("SP_PvGround", me); c.objects.link(g)
    me.materials.append(plain_mat("SP_PvGround", (0.30, 0.29, 0.27)))
    # person-height reference: 1.75 m grey figure (body + head) with a band every 0.25 m
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.17, depth=1.52, location=(PERSON_X, 0, 0.76))
    body = bpy.context.object; body.name = "SP_PvPerson"
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.115, location=(PERSON_X, 0, 1.635))
    head = bpy.context.object; head.name = "SP_PvHead"
    for o in (body, head):
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        c.objects.link(o)
        o.data.materials.append(plain_mat("SP_PvPerson", (0.55, 0.62, 0.75), 0.6))
    for i in range(1, 7):
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.175, depth=0.012, location=(PERSON_X, 0, 0.25 * i))
        b = bpy.context.object; b.name = "SP_PvBand"
        for cc in list(b.users_collection):
            cc.objects.unlink(b)
        c.objects.link(b)
        b.data.materials.append(plain_mat("SP_PvBand", (0.12, 0.14, 0.2), 0.6))
    cd = bpy.data.cameras.get("SP_Cam") or bpy.data.cameras.new("SP_Cam")
    cam = bpy.data.objects.new("SP_Cam", cd); c.objects.link(cam)
    sc.camera = cam
    try:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.resolution_percentage = 100
    for n, p in LINEUP.items():
        bpy.data.objects[n].location = p
    return saved, c, cam


def shot(cam, name, eye, target, res=(1280, 720), lens=50, ortho=None):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    cam.data.type = "ORTHO" if ortho else "PERSP"
    if ortho:
        cam.data.ortho_scale = ortho
    cam.data.lens = lens
    cam.data.clip_end = 300
    look_from(cam, eye, target)
    sc.render.filepath = os.path.join(OUT, "street-props-%s.png" % name)
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", sc.render.filepath)


def restore(saved, c):
    sc = bpy.context.scene
    for o in list(c.objects):
        d = o.data
        bpy.data.objects.remove(o)
        if isinstance(d, bpy.types.Mesh) and d.users == 0:
            bpy.data.meshes.remove(d)
    bpy.data.collections.remove(c)
    for n in LINEUP:
        bpy.data.objects[n].location = (0, 0, 0)
    try:
        sc.render.engine = saved["engine"]
    except TypeError:
        pass
    sc.view_settings.view_transform = saved["vt"]; sc.view_settings.look = saved["look"]
    sc.render.resolution_x, sc.render.resolution_y = saved["x"], saved["y"]
    sc.render.resolution_percentage = saved["pct"]
    sc.camera = saved["cam"] if saved["cam"] and saved["cam"].name in bpy.data.objects else None
    sc.world = saved["world"]
    sc.render.filepath = saved["fp"]


def run():
    saved, c, cam = setup()
    try:
        # whole kit, straight on (orthographic, so the person reference reads true)
        shot(cam, "lineup", (9.2, -60, 5.6), (9.2, 0, 5.6), ortho=20.4)
        # ground-level props, three-quarter
        shot(cam, "three-quarter", (0.6, -8.0, 2.4), (11.0, 0, 0.8), lens=28)
        # fountain (spec photo viewpoint: from the street side, a little right, eye ~1.4 m)
        shot(cam, "match-fountain", (4.6 + 0.8, -4.3, 1.30), (4.6 + 0.02, -0.45, 1.22), res=(1280, 1600), lens=40)
        shot(cam, "fountain", (4.6 - 2.2, -2.6, 1.7), (4.6, -0.4, 1.1), lens=40)
        # horse-head medallion close-up, framed like the reference photo (from the street, a little right)
        shot(cam, "horse-head", (4.6 + 0.25, -1.75, 1.42), (4.6, -0.33, 1.35), res=(1280, 1280), lens=50)
        # pole head: two crossarms, insulators, braces, eye bolt
        shot(cam, "pole-top", (2.6, -3.4, 10.6), (0.05, 0, 9.65), lens=40)
        # bracket lamp on the pole
        shot(cam, "pole-lamp", (1.8, -3.2, 3.6), (0.0, -0.55, 4.35), lens=45)
        shot(cam, "hydrant", (9.6 + 0.9, -1.9, 1.0), (9.6, 0, 0.44), lens=45)
        shot(cam, "gas-pump", (18.2 - 1.4, -3.4, 1.6), (18.2, 0, 1.12), res=(1280, 1280), lens=40)
        shot(cam, "gas-pump-right", (18.2 + 1.6, -2.6, 1.6), (18.2, 0, 1.12), res=(1280, 1280), lens=40)
        shot(cam, "gas-globe", (18.2 + 0.5, -1.6, 2.15), (18.2, 0, 2.02), res=(1280, 1280), lens=60)
        shot(cam, "goods-boards-bicycle", (13.0, -4.6, 1.6), (14.6, 0, 0.5), lens=35)
    finally:
        restore(saved, c)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)


run()
