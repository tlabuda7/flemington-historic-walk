"""
Preview renders of R2-W Furman R. Williamson (npc) for the reviewer (same set-up as Pickell).

Run in Blender after npc_williamson_bake.py:
    exec(open(r"<project>/tools/blender/npc_williamson_preview.py").read())

EEVEE, view transform "Standard", lit like the scene: warm late-afternoon sun from the WSW
(east-side "to sun" vector (0.40, -0.90, 0.36) in his frame - he stands on the bank forecourt, east side,
facing the street), sky (0.42, 0.55, 0.78) at 0.9. Writes assets/models/previews/npc-williamson-*.png
(1280 px wide) and restores the scene settings.
"""
import bpy, os, math
from mathutils import Vector

ROOT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
OUT = os.path.join(ROOT, r"assets\models\previews")
BLEND = os.path.join(ROOT, r"assets\models\source\npc-williamson.blend")
SUN_DIR = Vector((0.40, -0.90, 0.36)).normalized()


def look_from(cam, eye, target):
    cam.location = eye
    d = (Vector(target) - Vector(eye)).normalized()
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def setup():
    sc = bpy.context.scene
    saved = dict(engine=sc.render.engine, vt=sc.view_settings.view_transform, look=sc.view_settings.look,
                 x=sc.render.resolution_x, y=sc.render.resolution_y, cam=sc.camera, world=sc.world,
                 frame=sc.frame_current, fp=sc.render.filepath, pct=sc.render.resolution_percentage)
    c = bpy.data.collections.get("PK_Preview") or bpy.data.collections.new("PK_Preview")
    if c.name not in sc.collection.children:
        sc.collection.children.link(c)
    c.hide_render = False
    for o in list(c.objects):
        bpy.data.objects.remove(o)
    # sun
    ld = bpy.data.lights.get("PK_Sun") or bpy.data.lights.new("PK_Sun", "SUN")
    ld.energy = 3.2; ld.color = (1.0, 0.86, 0.70); ld.angle = math.radians(1.5)
    sun = bpy.data.objects.new("PK_Sun", ld); c.objects.link(sun)
    sun.rotation_euler = (-SUN_DIR).to_track_quat("-Z", "Y").to_euler()
    # sky
    w = bpy.data.worlds.get("PK_Sky") or bpy.data.worlds.new("PK_Sky")
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.42, 0.55, 0.78, 1.0); bg.inputs[1].default_value = 0.9
    sc.world = w
    # ground: plain warm-grey concrete
    me = bpy.data.meshes.new("PK_Ground")
    me.from_pydata([(-4, -4, 0), (4, -4, 0), (4, 4, 0), (-4, 4, 0)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new("PK_Ground", me); c.objects.link(g)
    gm = bpy.data.materials.get("PK_Ground") or bpy.data.materials.new("PK_Ground")
    gm.use_nodes = True
    gb = next(n for n in gm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    gb.inputs["Base Color"].default_value = (0.36, 0.34, 0.31, 1); gb.inputs["Roughness"].default_value = 0.95
    me.materials.append(gm)
    # 1.70 m reference pole (10 cm bands)
    cube_v = [(x, y, z) for z in (-0.5, 0.5) for y in (-0.5, 0.5) for x in (-0.5, 0.5)]
    cube_f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for k in range(17):
        cm = bpy.data.meshes.new(f"PK_Ref_{k:02d}")
        cm.from_pydata(cube_v, [], cube_f)
        b = bpy.data.objects.new(f"PK_Ref_{k:02d}", cm)
        c.objects.link(b)
        b.scale = (0.04, 0.04, 0.1); b.location = (0.62, 0.0, 0.05 + 0.1 * k)
        mn = "PK_RefW" if k % 2 == 0 else "PK_RefB"
        mm = bpy.data.materials.get(mn) or bpy.data.materials.new(mn)
        mm.use_nodes = True
        mb = next(n for n in mm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        mb.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1) if k % 2 == 0 else (0.03, 0.03, 0.03, 1)
        b.data.materials.append(mm)
        b.hide_render = True
    camd = bpy.data.cameras.get("PK_Cam") or bpy.data.cameras.new("PK_Cam")
    cam = bpy.data.objects.new("PK_Cam", camd); c.objects.link(cam)
    sc.camera = cam
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.resolution_percentage = 100
    if hasattr(sc.eevee, "use_shadows"):
        sc.eevee.use_shadows = True
    return saved, c, cam


def render(name, cam, eye, target, lens, res, action, frame, show_ref=False):
    sc = bpy.context.scene
    arm = bpy.data.objects["Williamson_Rig"]
    arm.animation_data.action = bpy.data.actions[action] if action else None
    sc.frame_set(frame)
    for o in bpy.data.objects:
        if o.name.startswith("PK_Ref_"):
            o.hide_render = not show_ref
    cam.data.lens = lens
    look_from(cam, eye, target)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(OUT, f"npc-williamson-{name}.png")
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", sc.render.filepath)


def run():
    os.makedirs(OUT, exist_ok=True)
    saved, c, cam = setup()
    # hide the build helpers
    hidden = []
    for o in bpy.data.objects:
        if o.type == "MESH" and not (o.name == "Williamson" or o.name.startswith("PK_")) and not o.hide_render:
            o.hide_render = True; hidden.append(o)
    full = (1280, 1600)
    render("front", cam, (0.0, -3.7, 0.95), (0.0, 0.0, 0.86), 50, full, "Idle", 30)
    render("three-quarter", cam, (2.15, -3.0, 1.2), (0.0, 0.0, 0.86), 50, full, "Idle", 100)
    render("closeup", cam, (0.30, -1.00, 1.58), (0.0, -0.02, 1.535), 60, (1280, 1024), "Idle", 4)
    render("talk", cam, (1.15, -3.1, 1.3), (0.0, 0.0, 0.88), 50, (1280, 1280), "Talk", 40)
    render("scale", cam, (0.3, -4.2, 0.9), (0.3, 0.0, 0.88), 50, full, "Idle", 30, show_ref=True)
    render("back", cam, (-1.2, 3.4, 1.35), (0.0, 0.0, 0.90), 50, full, "Idle", 60)
    # restore
    sc = bpy.context.scene
    arm = bpy.data.objects["Williamson_Rig"]
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
    for o in hidden:
        o.hide_render = False
    sc.render.engine = saved["engine"]
    sc.view_settings.view_transform = saved["vt"]; sc.view_settings.look = saved["look"]
    sc.render.resolution_x, sc.render.resolution_y = saved["x"], saved["y"]
    sc.render.resolution_percentage = saved["pct"]
    sc.camera = saved["cam"]; sc.world = saved["world"]; sc.frame_set(saved["frame"])
    sc.render.filepath = saved["fp"]
    for o in list(c.objects):
        o.hide_render = True
        o.hide_set(True)
    c.hide_render = True
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)


if not globals().get("WILLIAMSON_LIB_ONLY"):
    _w = bpy.context.window_manager.windows[0]
    _a = next(a for a in _w.screen.areas if a.type == "VIEW_3D")
    with bpy.context.temp_override(window=_w, screen=_w.screen, area=_a):
        run()
