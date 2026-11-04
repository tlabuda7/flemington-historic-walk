"""
John B. Pickell, clerk at the Nevius store (78 Main St), c. 1920 - geometry + rig build.

Run inside Blender (MPFB 2.0.18 extension installed, MakeHuman CC0 system-asset pack loaded):
    exec(open(r"<project>/tools/blender/npc_pickell.py").read())

What it does (all rebuildable):
  1. New empty file -> assets/models/source/npc_pickell.blend, collection "NPC_Pickell".
  2. Imports the Quaternius UAL Standard rig (in-place GLB) unchanged except a uniform scale to
     1.72 m (applied; location keys of the kept clips scaled by the same factor).
     Builds the clips Idle (Idle_Loop x2, slowed, with an upper-body glance), Talk
     (Idle_Talking_Loop) and Walk (Walk_Formal_Loop); every other clip is deleted.
  3. Makes an MPFB2 (MakeHuman, CC0) male, ~41 years, 1.72 m, with the game_engine rig (bone names
     = UAL names), low-poly eyes, the eyebrow001 proxy (its texture is painted onto the skin in the
     bake) and short02 hair (used as the thickness guide of a scalp-grown hair shell), then moves the mesh
     from MakeHuman's A-pose into the UAL T-pose by linear-blend skinning (torso translated,
     limbs mapped bone-to-bone onto the UAL joints).
  4. Keeps only head, neck and hands of that body (decimated), and builds the 1920 clothes
     (sack coat, waistcoat, shirt front, collar, tie, trousers with turn-ups, oxfords, tape
     measure, watch chain, pencil) as lofted shells around the posed body.
  5. Skins everything to the UAL rig: Data Transfer of the MakeHuman game_engine weights (same bone
     names, joints moved onto the UAL joints in step 3); coat-covered layers take the coat's
     weights; coat collar on the upper spine, coat skirt on the pelvis, sleeve heads on the
     clavicles, trouser legs on their thighs. (The UAL Mannequin stays in the work collection as
     a reference only: every new surface was derived from the MakeHuman body, whose own weights
     line up with it exactly.)
Materials/atlas/AO/export: npc_pickell_bake.py.  Previews: npc_pickell_preview.py.

Blender: Z up, metres, front faces -Y, origin on the ground between the feet.
"""
import bpy, bmesh, math, os
import numpy as np
from mathutils import Vector, Matrix, Quaternion, kdtree

ROOT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
BLEND = os.path.join(ROOT, r"assets\models\source\npc_pickell.blend")
UAL_GLB = os.path.join(ROOT, r"assets\characters\source\quaternius_ual_standard"
                       r"\Universal Animation Library[Standard]\Unreal-Godot\UAL1_Standard.glb")
MH_DATA = os.path.join(os.environ["APPDATA"], r"Blender Foundation\Blender\5.2\extensions\.user"
                       r"\user_default\mpfb\data")
TARGET_H = 1.72
COLL = "NPC_Pickell"
WORK = "NPC_Pickell_Work"

KEEP_CLIPS = {"Idle_Loop": "Idle", "Idle_Talking_Loop": "Talk", "Walk_Formal_Loop": "Walk"}


# ----------------------------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------------------------
def coll(name, parent=None, hide_render=False):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    par = parent.children if parent else bpy.context.scene.collection.children
    if c.name not in [x.name for x in par]:
        par.link(c)
    c.hide_render = hide_render
    return c


def win_ctx():
    """Context override with a real window / 3D view (needed after read_homefile in a script)."""
    win = bpy.context.window_manager.windows[0]
    scr = win.screen
    area = next((a for a in scr.areas if a.type == "VIEW_3D"), scr.areas[0])
    region = next((r for r in area.regions if r.type == "WINDOW"), area.regions[0])
    return bpy.context.temp_override(window=win, screen=scr, area=area, region=region,
                                     scene=bpy.context.scene,
                                     view_layer=bpy.context.scene.view_layers[0])


def move_to(obj, c):
    for uc in list(obj.users_collection):
        uc.objects.unlink(obj)
    c.objects.link(obj)


def activate(obj):
    cur = getattr(bpy.context, "object", None)
    if cur is not None and cur.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def mesh_from_arrays(name, verts, faces, c, uvs=None, uv_name="UVMap"):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    if uvs is not None:
        layer = me.uv_layers.new(name=uv_name)
        layer.data.foreach_set("uv", np.asarray(uvs, dtype=np.float32).ravel())
    ob = bpy.data.objects.new(name, me)
    c.objects.link(ob)
    return ob


# ----------------------------------------------------------------------------------------------
# 1. file + rig + clips
# ----------------------------------------------------------------------------------------------
def new_file():
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)


def stage_rig():
    sc = bpy.context.scene
    sc.render.fps = 24          # UAL clips are authored at 24 fps; glTF stores seconds
    sc.unit_settings.system = "METRIC"
    main = coll(COLL)
    work = coll(WORK, hide_render=True)

    bpy.ops.import_scene.gltf(filepath=UAL_GLB, disable_bone_shape=True)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    man = next(o for o in bpy.data.objects if o.type == "MESH" and o.parent == arm)
    for c in list(bpy.data.collections):
        if c.name.startswith("glTF_not_exported"):
            for o in list(c.objects):
                bpy.data.objects.remove(o)
            bpy.data.collections.remove(c)
    arm.name = arm.data.name = "Pickell_Rig"
    man.name = "UAL_Mannequin_donor"
    move_to(arm, main)
    move_to(man, work)

    # uniform scale to 1.72 m (mannequin is 1.829 m), applied
    h = max((man.matrix_world @ Vector(b)).z for b in man.bound_box)
    s = TARGET_H / h
    arm.scale = (s, s, s)
    bpy.context.view_layer.update()
    activate(arm)
    man.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # clips: keep three, scale their location keys
    for act in list(bpy.data.actions):
        if act.name not in KEEP_CLIPS:
            bpy.data.actions.remove(act)
    for act in bpy.data.actions:
        for fc in iter_fcurves(act):
            if fc.data_path.endswith(".location") or fc.data_path == "location":
                for kp in fc.keyframe_points:
                    kp.co.y *= s
                    kp.handle_left.y *= s
                    kp.handle_right.y *= s
    build_clips(arm)
    print("RIG scale", round(s, 5), "bones", len(arm.data.bones))
    return arm


def iter_fcurves(act):
    """Blender 4.4+ layered actions and older flat actions."""
    if hasattr(act, "layers") and len(act.layers):
        for lay in act.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        yield fc
    else:
        for fc in act.fcurves:
            yield fc


def new_action_like(name, arm):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    return act


def sample_action(act, arm, t):
    """Return {bone: (loc, quat, scale)} of action at frame t (fcurve evaluation)."""
    out = {}
    for fc in iter_fcurves(act):
        dp = fc.data_path
        if not dp.startswith('pose.bones["'):
            continue
        bone = dp.split('"')[1]
        prop = dp.rsplit(".", 1)[1]
        d = out.setdefault(bone, {})
        d.setdefault(prop, {})[fc.array_index] = fc.evaluate(t)
    return out


def write_pose_keys(arm, act, frames_data):
    """frames_data: list of (frame, {bone: {prop: {idx: val}}}). Writes keys via a temp slot."""
    arm.animation_data_create()
    arm.animation_data.action = act
    for f, data in frames_data:
        for bone, props in data.items():
            pb = arm.pose.bones.get(bone)
            if pb is None:
                continue
            for prop, comps in props.items():
                for idx, val in comps.items():
                    getattr(pb, prop)[idx] = val
                pb.keyframe_insert(prop, frame=f, group=bone)
    arm.animation_data.action = None


def relax_fingers(arm, amount=0.5, thumb=0.3):
    """UAL clips hold tight fists; ease every finger rotation part-way back toward the open rest
    pose (a relaxed clerk's hand). Rotation-only, so no foot sliding is introduced."""
    for name in ("Idle", "Talk", "Walk"):
        act = bpy.data.actions[name]
        groups = {}
        for fc in iter_fcurves(act):
            if fc.data_path.endswith("rotation_quaternion"):
                bone = fc.data_path.split('"')[1]
                if bone.split("_")[0] in ("index", "middle", "ring", "pinky", "thumb"):
                    groups.setdefault(bone, {})[fc.array_index] = fc
        for bone, fcs in groups.items():
            if len(fcs) < 4:
                continue
            k = thumb if bone.startswith("thumb") else amount
            frames = sorted({kp.co.x for fc in fcs.values() for kp in fc.keyframe_points})
            vals = []
            for f in frames:
                q = Quaternion([fcs[i].evaluate(f) for i in range(4)])
                vals.append((f, q.slerp(Quaternion((1, 0, 0, 0)), k)))
            for i in range(4):
                fc = fcs[i]
                fc.keyframe_points.clear()
                fc.keyframe_points.add(len(vals))
                for kp, (f, q) in zip(fc.keyframe_points, vals):
                    kp.co = (f, q[i]); kp.interpolation = "LINEAR"


def adjust_stance_and_gaze(arm, name, ankle_sep=0.28, gaze_amount=1.0, gaze_target=-0.05,
                           toe_out_target=math.radians(12)):
    """Re-key a clip with the feet closer together and the head raised to a level gaze.

    Each thigh is turned about the forward axis through its hip joint so the ankles end up
    `ankle_sep` apart; each foot keeps its original world orientation (sole flat); the small rise
    of the feet is taken out by lowering the pelvis. The head pitch is corrected by the mean
    difference to `gaze_target` (radians, slightly down), 40 % in the neck, 60 % in the head.
    Rotation-only per frame on top of the original pose, so the feet stay planted (no sliding).
    """
    sc = bpy.context.scene
    act = bpy.data.actions[name]
    arm.animation_data_create()
    arm.animation_data.action = act
    P = arm.pose.bones
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    frames = list(range(f0, f1 + 1))
    names = ("thigh_l", "thigh_r", "foot_l", "foot_r", "ball_l", "ball_r", "neck_01", "Head")
    rec = []
    for f in frames:
        sc.frame_set(f)
        rec.append({n: P[n].matrix.copy() for n in names})
    hr = arm.data.bones["Head"].matrix_local.to_3x3().inverted()
    face = lambda m: (m.to_3x3() @ hr @ Vector((0, -1, 0))).normalized()
    right = lambda m: (m.to_3x3() @ hr @ Vector((1, 0, 0))).normalized()
    sep = float(np.mean([r["foot_l"].translation.x - r["foot_r"].translation.x for r in rec]))
    shift = max(0.0, (sep - ankle_sep) / 2.0)

    def toe_out(r, side, sg):
        d = r[f"ball_{side}"].translation - r[f"foot_{side}"].translation
        return math.atan2(sg * d.x, -d.y)
    turn = {}
    for side, sg in (("l", 1.0), ("r", -1.0)):
        t0 = float(np.mean([toe_out(r, side, sg) for r in rec]))
        turn[side] = max(0.0, t0 - toe_out_target)
        # sign that turns this toe inward: about +Z the left (+x) toe swings toward -x when the toe
        # points -y... test it numerically on the first frame
        r0 = rec[0]
        best = None
        for sgn in (1.0, -1.0):
            R = Matrix.Rotation(sgn * turn[side], 4, "Z")
            d = R @ (r0[f"ball_{side}"].translation - r0[f"foot_{side}"].translation)
            val = math.atan2(sg * d.x, -d.y)
            if best is None or val < best[0]:
                best = (val, sgn)
        turn[side] *= best[1]
        print("CLIP", name, side, "toe-out deg", round(math.degrees(t0), 1), "->",
              round(math.degrees(toe_out_target), 1))
    pitch = float(np.mean([math.asin(max(-1, min(1, face(r["Head"]).z))) for r in rec]))
    dpitch = (gaze_target - pitch) * gaze_amount
    print("CLIP", name, "ankle sep", round(sep, 3), "->", ankle_sep, "head pitch deg", round(math.degrees(pitch), 1),
          "raise", round(math.degrees(dpitch), 1))

    def about(pivot, axis, ang):
        return Matrix.Translation(pivot) @ Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-pivot)

    def key(pb, f):
        pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
        pb.keyframe_insert("location", frame=f, group=pb.name)

    rises = []
    for f, r in zip(frames, rec):
        sc.frame_set(f)
        for side, sg in (("l", 1.0), ("r", -1.0)):
            th0 = r[f"thigh_{side}"]; hip = th0.translation
            R1 = about(hip, Vector((0, 0, 1)), turn[side])          # turn the whole leg in
            th = R1 @ th0
            ank0 = r[f"foot_{side}"].translation
            ank = R1 @ ank0
            v = ank - hip
            rad_ = math.hypot(v.x, v.z)
            a_now = math.asin(max(-1, min(1, v.x / rad_)))
            a_new = math.asin(max(-1, min(1, (v.x - (ank.x - ank0.x) - sg * shift) / rad_)))
            best = None
            for sgn in (1.0, -1.0):
                R = about(hip, Vector((0, 1, 0)), sgn * abs(a_new - a_now))
                nx = (R @ ank).x
                err = abs(nx - (ank0.x - sg * shift))
                if best is None or err < best[0]:
                    best = (err, R)
            R = best[1]
            P[f"thigh_{side}"].matrix = R @ th
            bpy.context.view_layer.update()
            newpos = P[f"foot_{side}"].matrix.translation.copy()
            rises.append(newpos.z - ank0.z)
            frot = (R1.to_3x3() @ r[f"foot_{side}"].to_3x3()).to_4x4()      # flat, toes turned in
            P[f"foot_{side}"].matrix = Matrix.Translation(newpos) @ frot
            bpy.context.view_layer.update()
            key(P[f"thigh_{side}"], f); key(P[f"foot_{side}"], f)
        if abs(dpitch) > 1e-4:
            ax = right(r["Head"])
            fz = face(r["Head"])
            sgn = 1.0 if (Matrix.Rotation(0.1, 3, ax) @ fz).z > fz.z else -1.0
            Rn = about(r["neck_01"].translation, ax, sgn * 0.4 * dpitch)
            P["neck_01"].matrix = Rn @ r["neck_01"]
            bpy.context.view_layer.update()
            base = Rn @ r["Head"]
            P["Head"].matrix = about(base.translation, ax, sgn * 0.6 * dpitch) @ base
            bpy.context.view_layer.update()
            key(P["neck_01"], f); key(P["Head"], f)
    # take the feet's rise out with the pelvis
    rise = float(np.mean(rises)) if rises else 0.0
    d_local = arm.data.bones["pelvis"].matrix_local.to_3x3().inverted() @ Vector((0, 0, -rise))
    for fc in iter_fcurves(act):
        if fc.data_path == 'pose.bones["pelvis"].location':
            for kp in fc.keyframe_points:
                for attr in ("co", "handle_left", "handle_right"):
                    vv = getattr(kp, attr); vv.y += d_local[fc.array_index]
    arm.animation_data.action = None
    print("CLIP", name, "pelvis lowered", round(rise, 4))


def build_clips(arm):
    src = {k: bpy.data.actions[k] for k in KEEP_CLIPS}
    for a in arm.pose.bones:
        a.rotation_mode = "QUATERNION"

    # --- Talk and Walk: straight copies (renamed) ---
    for sname, dname, frames in (("Idle_Talking_Loop", "Talk", 72), ("Walk_Formal_Loop", "Walk", 32)):
        a = src[sname]
        a.name = dname
        a.use_fake_user = True
        f0, f1 = a.frame_range
        k = frames / (f1 - f0)            # whole-frame loop length (Talk 70.4 -> 72 f = 3.0 s)
        if abs(k - 1.0) > 1e-6:
            for fc in iter_fcurves(a):
                for kp in fc.keyframe_points:
                    for attr in ("co", "handle_left", "handle_right"):
                        v = getattr(kp, attr); v.x = f0 + (v.x - f0) * k
        a.use_frame_range = True
        a.frame_start, a.frame_end = f0, f0 + frames

    # --- Idle: Idle_Loop twice, slowed x1.2, with a slow glance (upper body only, loop-safe) ---
    a = src["Idle_Loop"]
    a.name = "Idle_Loop_src"
    L = a.frame_range[1] - a.frame_range[0]           # 60 frames = 2.5 s
    slow = 1.2
    total = int(round(2 * L * slow))                   # 144 frames = 6.0 s
    idle = new_action_like("Idle", arm)
    frames = []
    for f in range(0, total + 1):
        t = (f / slow) % L
        if f == total:
            t = 0.0
        pose = sample_action(a, arm, t)
        # glance: during the 2nd cycle turn head/neck ~14 deg to his left and back, smooth in/out
        u = (f - total * 0.5) / (total * 0.5)
        if 0.0 <= u <= 1.0:
            w = math.sin(math.pi * u) ** 2
            for bone, ang, tilt in (("neck_01", 0.10, 0.0), ("Head", 0.15, 0.0), ("spine_03", 0.04, 0.0)):
                if bone in pose and "rotation_quaternion" in pose[bone]:
                    q = pose[bone]["rotation_quaternion"]
                    qb = Quaternion((q.get(0, 1), q.get(1, 0), q.get(2, 0), q.get(3, 0)))
                    # rotate about the armature's vertical axis expressed in bone space
                    rest = arm.data.bones[bone].matrix_local.to_3x3()
                    ax = (rest.inverted() @ Vector((0, 0, 1))).normalized()
                    ax2 = (rest.inverted() @ Vector((1, 0, 0))).normalized()
                    qa = Quaternion(ax, ang * w) @ Quaternion(ax2, tilt * w)
                    qn = qb @ qa
                    pose[bone]["rotation_quaternion"] = {0: qn.w, 1: qn.x, 2: qn.y, 3: qn.z}
        frames.append((f, pose))
    write_pose_keys(arm, idle, frames)
    idle.use_frame_range = True
    idle.frame_start, idle.frame_end = 0, total
    bpy.data.actions.remove(a)
    relax_fingers(arm)
    # reviewer round 1: relaxed narrow stance (UAL idle/talk stand 0.5 m wide) and a level gaze
    adjust_stance_and_gaze(arm, "Idle", ankle_sep=0.28, gaze_amount=1.0)
    adjust_stance_and_gaze(arm, "Talk", ankle_sep=0.28, gaze_amount=0.6)
    # put each clip on its own NLA track so the glTF exporter writes all three
    arm.animation_data_create()
    for tr in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(tr)
    for name in ("Idle", "Talk", "Walk"):
        act = bpy.data.actions[name]
        tr = arm.animation_data.nla_tracks.new()
        tr.name = name
        st = tr.strips.new(name, int(act.frame_range[0]), act)
        st.name = name
        tr.mute = True
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)


# ----------------------------------------------------------------------------------------------
# 2. MPFB human, moved into the UAL rest pose
# ----------------------------------------------------------------------------------------------
MACRO = dict(gender=1.0, age=0.62, muscle=0.5, weight=0.6, proportions=0.6, height=0.45)
# MakeHuman age slider: 0.5 = 25 y, 1.0 = 90 y  ->  41 y = 0.5 + 16/65*0.5 = 0.62
PROXIES = (("Eyes", r"eyes\low-poly\low-poly.mhclo"),
           ("Eyebrows", r"eyebrows\eyebrow001\eyebrow001.mhclo"),
           ("Hair", r"hair\short02\short02.mhclo"))
TORSO_DY = 0.035          # MakeHuman body sits ~3.5 cm in front of the UAL spine
TORSO = {"Root", "root", "pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head", "Head"}
LIMB_CHAINS = {
    "arm": ["upperarm", "lowerarm", "hand"],
    "fingers": [f"{f}_0{i}" for f in ("thumb", "index", "middle", "ring", "pinky") for i in (1, 2, 3)],
    "leg": ["thigh", "calf", "foot", "ball"],
}


def swing(a, b):
    a = a.normalized(); b = b.normalized()
    return a.rotation_difference(b)


def bone_y(m):
    return (m.to_3x3() @ Vector((0, 1, 0))).normalized()


def retarget_deltas(rig, arm):
    """Per MPFB bone: 4x4 matrix taking a rest-pose MPFB point to the UAL rest pose.

    Torso/neck/head: translated by TORSO_DY only (the MakeHuman head keeps its own height).
    Clavicle: translated so the shoulder joint lands on the UAL shoulder.
    Limb chains: each bone starts where its (already mapped) parent puts its joint, is swung
    onto the UAL bone direction and, for upper arm / forearm / thigh / shin, stretched along
    its axis to the UAL joint-to-joint length. The hand gets a palm twist (half in the forearm).
    """
    Rm = {b.name: b.matrix_local.copy() for b in rig.data.bones}
    Ru = {b.name: b.matrix_local.copy() for b in arm.data.bones}
    hm = {n: m.translation.copy() for n, m in Rm.items()}
    hu = {n: m.translation.copy() for n, m in Ru.items()}
    T0 = Matrix.Translation((0, TORSO_DY, 0))
    D = {n: T0.copy() for n in Rm}
    Q = {}

    def make(n, h_new, q, s=1.0):
        R3 = Rm[n].to_3x3()
        Sw = R3 @ Matrix.Diagonal((1.0, s, 1.0)) @ R3.transposed()
        M = (q.to_matrix() @ Sw).to_4x4()
        D[n] = Matrix.Translation(h_new) @ M @ Matrix.Translation(-hm[n])
        Q[n] = q

    def ym(n):
        return bone_y(Rm[n])

    def yu(n):
        return bone_y(Ru[n])

    def palm(H, side):
        return H[f"index_01_{side}"] - H[f"pinky_01_{side}"]

    for side in ("l", "r"):
        sh = f"upperarm_{side}"
        D[f"clavicle_{side}"] = Matrix.Translation(hu[sh] - (T0 @ hm[sh])) @ T0
        # arm chain
        up, lo, ha = sh, f"lowerarm_{side}", f"hand_{side}"
        s_up = (hu[lo] - hu[up]).length / (hm[lo] - hm[up]).length
        make(up, hu[up], swing(ym(up), yu(up)), s_up)
        s_lo = (hu[ha] - hu[lo]).length / (hm[ha] - hm[lo]).length
        q_lo0 = swing(Q[up] @ ym(lo), yu(lo)) @ Q[up]
        # palm twist: compare palm vectors after the swing chain
        q_ha0 = swing(q_lo0 @ ym(ha), yu(ha)) @ q_lo0
        y = yu(ha)
        a_ = q_ha0 @ palm(hm, side); b_ = palm(hu, side)
        a_ = (a_ - a_.dot(y) * y).normalized(); b_ = (b_ - b_.dot(y) * y).normalized()
        tau = math.atan2(a_.cross(b_).dot(y), a_.dot(b_))
        make(lo, D[up] @ hm[lo], Quaternion(yu(lo), tau * 0.5) @ q_lo0, s_lo)
        q_ha = swing(Q[lo] @ ym(ha), yu(ha)) @ Q[lo]
        a_ = q_ha @ palm(hm, side)
        a_ = (a_ - a_.dot(y) * y).normalized()
        tau2 = math.atan2(a_.cross(b_).dot(y), a_.dot(b_))
        make(ha, D[lo] @ hm[ha], Quaternion(y, tau2) @ q_ha, 1.0)
        # fingers (keep MakeHuman finger lengths; follow the hand, aim along UAL fingers)
        for f in ("thumb", "index", "middle", "ring", "pinky"):
            parent = ha
            for i in (1, 2, 3):
                n = f"{f}_0{i}_{side}"
                if n not in Rm or n not in Ru:
                    continue
                q = swing(Q[parent] @ ym(n), yu(n)) @ Q[parent]
                make(n, D[parent] @ hm[n], q, 1.0)
                parent = n
        # leg chain
        th, ca, fo, ba = (f"thigh_{side}", f"calf_{side}", f"foot_{side}", f"ball_{side}")
        s_th = (hu[ca] - hu[th]).length / (hm[ca] - hm[th]).length
        make(th, hu[th], swing(ym(th), yu(th)), s_th)
        s_ca = (hu[fo] - hu[ca]).length / (hm[fo] - hm[ca]).length
        make(ca, D[th] @ hm[ca], swing(Q[th] @ ym(ca), yu(ca)) @ Q[th], s_ca)
        make(fo, D[ca] @ hm[fo], swing(Q[ca] @ ym(fo), yu(fo)) @ Q[ca], 1.0)
        make(ba, D[fo] @ hm[ba], swing(Q[fo] @ ym(ba), yu(ba)) @ Q[fo], 1.0)
    return D


def lbs(obj, coords, D):
    """coords: (N,3) array. Uses obj's vertex groups named after bones in D."""
    gi = {vg.index: vg.name for vg in obj.vertex_groups if vg.name in D}
    out = np.zeros_like(coords)
    Dn = {k: np.array(v) for k, v in D.items()}
    for i, v in enumerate(obj.data.vertices):
        acc = np.zeros(3); wsum = 0.0
        p = np.append(coords[i], 1.0)
        for g in v.groups:
            if g.group in gi and g.weight > 1e-4:
                acc += g.weight * (Dn[gi[g.group]] @ p)[:3]
                wsum += g.weight
        out[i] = acc / wsum if wsum > 0 else (Dn["pelvis"] @ p)[:3]
    return out


def evaluated_coords(obj):
    """Vertex coords with shape keys, without armature/mask/subsurf modifiers."""
    states = [(m, m.show_viewport) for m in obj.modifiers]
    for m, _ in states:
        m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    for m, s in states:
        m.show_viewport = s
    mw = np.array(obj.matrix_world)
    co = co.reshape(-1, 3)
    return (co @ mw[:3, :3].T) + mw[:3, 3]


def bake_copy(obj, coords, name, c, keep_group=None):
    """Static copy of obj's mesh with new coords; optionally keep only verts in keep_group."""
    me = obj.data.copy()
    me.name = name
    ob = bpy.data.objects.new(name, me)
    c.objects.link(ob)
    if me.shape_keys:
        ob.shape_key_clear()
    me.vertices.foreach_set("co", coords.ravel())
    # Blender 5 keeps vertex-group names and weights on the mesh, so the copy already has them;
    # rename MakeHuman's bones to the UAL spelling
    if not len(ob.vertex_groups):
        for vg in obj.vertex_groups:
            ob.vertex_groups.new(name=vg.name)
    for vg in ob.vertex_groups:
        if vg.name in ("head", "Root"):
            vg.name = {"head": "Head", "Root": "root"}[vg.name]
    if keep_group:
        g = ob.vertex_groups[keep_group].index
        bm_ = bmesh.new(); bm_.from_mesh(me)
        dl = bm_.verts.layers.deform.verify()
        kill = [v for v in bm_.verts if v[dl].get(g, 0.0) < 0.5]
        bmesh.ops.delete(bm_, geom=kill, context="VERTS")
        bm_.to_mesh(me); bm_.free()
    me.update()
    ob.data.materials.clear()
    return ob


def stage_human(arm):
    from bl_ext.user_default.mpfb.services.humanservice import HumanService
    from bl_ext.user_default.mpfb.services.targetservice import TargetService
    work = bpy.data.collections[WORK]
    md = TargetService.get_default_macro_info_dict()
    md.update(MACRO)
    md["race"] = {"asian": 0.0, "caucasian": 1.0, "african": 0.0}
    bm_obj = HumanService.create_human(macro_detail_dict=md)
    activate(bm_obj)
    rig = HumanService.add_builtin_rig(bm_obj, "game_engine")
    prox = {}
    for kind, rel in PROXIES:
        activate(bm_obj)
        prox[kind] = HumanService.add_mhclo_asset(os.path.join(MH_DATA, rel), bm_obj, asset_type=kind,
                                                  subdiv_levels=0, material_type="NONE")
    bpy.context.view_layer.update()
    D = retarget_deltas(rig, arm)
    src = {}
    co = evaluated_coords(bm_obj)
    src["Body"] = bake_copy(bm_obj, lbs(bm_obj, co, D), "SRC_Body", work, keep_group="body")
    for kind, ob in prox.items():
        co = evaluated_coords(ob)
        src[kind] = bake_copy(ob, lbs(ob, co, D), "SRC_" + kind, work)
    # remove the MPFB objects
    for ob in [bm_obj, rig] + list(prox.values()):
        bpy.data.objects.remove(ob, do_unlink=True)
    for o in src.values():
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
    print("HUMAN", {k: len(v.data.vertices) for k, v in src.items()})
    return src


# ----------------------------------------------------------------------------------------------
# 3. body sampling helpers (cross-section hulls of the posed MakeHuman body)
# ----------------------------------------------------------------------------------------------
TAU = 2 * math.pi


class BodyData:
    def __init__(self, ob):
        n = len(ob.data.vertices)
        co = np.empty(n * 3)
        ob.data.vertices.foreach_get("co", co)
        self.co = co.reshape(-1, 3)
        names = {vg.index: vg.name for vg in ob.vertex_groups}
        self.w = {}
        for v in ob.data.vertices:
            for g in v.groups:
                self.w.setdefault(names[g.group], np.zeros(n))[v.index] = g.weight

    def ws(self, bones):
        out = np.zeros(len(self.co))
        for b in bones:
            if b in self.w:
                out += self.w[b]
        return out


def hull2d(P):
    P = sorted(set(map(tuple, np.round(P, 5))))
    if len(P) < 3:
        return P

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def ray_poly(poly, c, d):
    """Largest t with c + t d on the polygon boundary (c inside)."""
    best = 0.0
    n = len(poly)
    for i in range(n):
        a = np.array(poly[i]); b = np.array(poly[(i + 1) % n])
        e = b - a
        den = d[0] * (-e[1]) - d[1] * (-e[0])
        if abs(den) < 1e-12:
            continue
        r = a - c
        t = (r[0] * (-e[1]) - r[1] * (-e[0])) / den
        u = (d[0] * r[1] - d[1] * r[0]) / den
        if t > 0 and -1e-6 <= u <= 1 + 1e-6:
            best = max(best, t)
    return best


def smooth_circ(r, k=2):
    out = r.copy()
    for _ in range(k):
        out = 0.25 * np.roll(out, 1, axis=-1) + 0.5 * out + 0.25 * np.roll(out, -1, axis=-1)
    return out


class Field:
    """Radius table r(s, phi) of hull cross-sections along an axis.

    axis frame: origin(s) = o + s*a ; phi measured in the plane spanned by e1 (phi=0) and e2
    (phi=90 deg). Point = centre(s) + r * (cos phi * e1 + sin phi * e2) + s*a.
    """

    def __init__(self, pts, o, a, e1, e2, s0, s1, ds=0.02, half=0.012, K=72, fixed_centre=None):
        self.o, self.a, self.e1, self.e2 = (np.array(o, float), np.array(a, float),
                                            np.array(e1, float), np.array(e2, float))
        self.K = K
        self.ss = np.arange(s0, s1 + 1e-9, ds)
        rel = pts - self.o
        sv = rel @ self.a
        u1 = rel @ self.e1
        u2 = rel @ self.e2
        R = np.zeros((len(self.ss), K))
        C = np.zeros((len(self.ss), 2))
        phis = np.arange(K) * TAU / K
        dirs = np.stack([np.cos(phis), np.sin(phis)], 1)
        valid = np.zeros(len(self.ss), bool)
        for i, s in enumerate(self.ss):
            m = np.abs(sv - s) < half
            if m.sum() < 6:
                continue
            P = np.stack([u1[m], u2[m]], 1)
            H = hull2d(P)
            if len(H) < 3:
                continue
            Hn = np.array(H)
            c = Hn.mean(0) if fixed_centre is None else np.array(fixed_centre(s))
            C[i] = c
            R[i] = [ray_poly(H, c, d) for d in dirs]
            valid[i] = True
        # fill invalid rows from neighbours
        idx = np.where(valid)[0]
        for i in range(len(self.ss)):
            if not valid[i]:
                j = idx[np.argmin(np.abs(idx - i))]
                R[i] = R[j]; C[i] = C[j]
        # smooth along s and phi
        R = smooth_circ(R, 2)
        for _ in range(2):
            R[1:-1] = 0.25 * R[:-2] + 0.5 * R[1:-1] + 0.25 * R[2:]
            C[1:-1] = 0.25 * C[:-2] + 0.5 * C[1:-1] + 0.25 * C[2:]
        self.R, self.C = R, C

    def _interp(self, s):
        f = np.clip((s - self.ss[0]) / (self.ss[1] - self.ss[0]), 0, len(self.ss) - 1.0001)
        i = int(f); t = f - i
        return i, t

    def radius(self, s, phi):
        i, t = self._interp(s)
        k = (phi % TAU) / TAU * self.K
        k0 = int(k) % self.K; k1 = (k0 + 1) % self.K; tk = k - int(k)
        r0 = self.R[i, k0] * (1 - tk) + self.R[i, k1] * tk
        r1 = self.R[i + 1, k0] * (1 - tk) + self.R[i + 1, k1] * tk
        return r0 * (1 - t) + r1 * t

    def centre(self, s):
        i, t = self._interp(s)
        return self.C[i] * (1 - t) + self.C[i + 1] * t

    def point(self, s, phi, r):
        c = self.centre(s)
        p = self.o + s * self.a + (c[0] + r * math.cos(phi)) * self.e1 + (c[1] + r * math.sin(phi)) * self.e2
        return Vector(p)

    def surf(self, s, phi, off=0.0):
        return self.point(s, phi, self.radius(s, phi) + off)


# torso frame: phi = 0 -> front (-Y), phi = 90 deg -> his left (+X); s = z
TORSO_FRAME = dict(o=(0, 0, 0), a=(0, 0, 1), e1=(0, -1, 0), e2=(1, 0, 0))


# ----------------------------------------------------------------------------------------------
# 4. clothes
# ----------------------------------------------------------------------------------------------
MATS = ["SKIN", "HAIR", "EYE", "SUIT", "SHIRT", "TIE", "SHOE", "GOLD", "TAPE", "PENCIL", "BUTTON",
        "HANKY"]

# design heights (m, Blender z) for a 1.72 m man
Z = dict(jk_b1=1.135, jk_b2=1.045, jk_b3=0.955,     # sack coat buttons (top two fastened)
         wc_v=1.275, wc_bot=0.925,                  # waistcoat V bottom, points
         gorge=1.372, notch=1.292, tr_top=1.03)


class MB:
    """Collects verts/faces/material names for one part."""

    def __init__(self, name):
        self.name = name; self.v = []; self.f = []; self.fm = []

    def grid(self, P, mat, closed=False, flip=False):
        base = len(self.v); rows = len(P); cols = len(P[0])
        for row in P:
            assert len(row) == cols
            self.v.extend([Vector(tuple(p)) for p in row])
        uc = cols if closed else cols - 1
        for i in range(rows - 1):
            for j in range(uc):
                a = base + i * cols + j; b = base + i * cols + (j + 1) % cols
                c = b + cols; d = a + cols
                self.f.append((a, d, c, b) if flip else (a, b, c, d)); self.fm.append(mat)
        return base

    def fan(self, ring_idx, centre, mat, flip=False):
        ci = len(self.v); self.v.append(Vector(tuple(centre)))
        n = len(ring_idx)
        for j in range(n):
            a, b = ring_idx[j], ring_idx[(j + 1) % n]
            self.f.append((a, ci, b) if not flip else (a, b, ci)); self.fm.append(mat)

    def poly(self, pts, mat):
        base = len(self.v); self.v.extend([Vector(tuple(p)) for p in pts])
        self.f.append(tuple(range(base, base + len(pts)))); self.fm.append(mat)

    def disc(self, centre, normal, radius, mat, n=8, depth=0.0025):
        """Button: a low cylinder (top fan + side) facing `normal`."""
        nrm = Vector(normal).normalized()
        t1 = nrm.orthogonal().normalized(); t2 = nrm.cross(t1)
        c = Vector(centre)
        bot = [c + radius * (math.cos(TAU * k / n) * t1 + math.sin(TAU * k / n) * t2) for k in range(n)]
        top = [p + nrm * depth for p in bot]
        b0 = self.grid([bot, top], mat, closed=True)
        self.fan(list(range(b0 + n, b0 + 2 * n)), c + nrm * depth * 1.25, mat)

    def build(self, c, orient=None):
        ob = mesh_from_arrays("PART_" + self.name, self.v, self.f, c)
        me = ob.data
        for m in MATS:
            mat = bpy.data.materials.get("SRC_" + m) or bpy.data.materials.new("SRC_" + m)
            me.materials.append(mat)
        me.polygons.foreach_set("material_index", [MATS.index(m) for m in self.fm])
        if orient is not None:
            flip_outward(ob, orient)
        for p in me.polygons:
            p.use_smooth = True
        me.update()
        return ob


def flip_outward(ob, ref_fn):
    """Flip faces whose normal points toward ref_fn(face centre) (an interior reference point)."""
    bm_ = bmesh.new(); bm_.from_mesh(ob.data)
    flip = []
    for f in bm_.faces:
        c = f.calc_center_median()
        if f.normal.dot(c - Vector(ref_fn(c))) < 0:
            flip.append(f)
    bmesh.ops.reverse_faces(bm_, faces=flip)
    bm_.to_mesh(ob.data); bm_.free()


def solve_phi_for_x(F, s, x, side=1, off=0.0):
    """phi in (0, 0.75 pi) (side=+1, his left) or mirrored, where the surface point has world x."""
    lo, hi = 0.0, math.pi * 0.75
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        px = F.surf(s, (mid * side) % TAU, off).x * side
        if px < x:
            lo = mid
        else:
            hi = mid
    return (0.5 * (lo + hi) * side) % TAU


def lin(pts, z):
    """Piecewise-linear value at z through (z, value) pairs."""
    pts = sorted(pts)
    if z <= pts[0][0]:
        return pts[0][1]
    for (z0, x0), (z1, x1) in zip(pts, pts[1:]):
        if z <= z1:
            t = (z - z0) / (z1 - z0)
            return x0 + t * (x1 - x0)
    return pts[-1][1]


def resample(poly, n):
    """Resample a polyline to n points by arc length."""
    P = [np.array(p, float) for p in poly]
    L = [0.0]
    for a, b in zip(P, P[1:]):
        L.append(L[-1] + np.linalg.norm(b - a))
    out = []
    for k in range(n):
        t = L[-1] * k / (n - 1)
        for i in range(len(P) - 1):
            if t <= L[i + 1] + 1e-9:
                u = (t - L[i]) / max(L[i + 1] - L[i], 1e-9)
                out.append(P[i] * (1 - u) + P[i + 1] * u)
                break
        else:
            out.append(P[-1])
    return out


def offset_field(F, add, hang_from=None, hang_rate=0.0, smooth=0, floor=None):
    """Copy of a Field with radius + add(s, phis), an optional straight hang below hang_from and
    extra smoothing along s (cloth bridges the body's bumps)."""
    import copy
    G = copy.copy(F)
    R = F.R.copy()
    phis = np.arange(F.K) * TAU / F.K
    for i, s in enumerate(F.ss):
        R[i] = R[i] + add(s, phis)
    if hang_from is not None:
        i0 = int(np.argmin(np.abs(F.ss - hang_from)))
        for i in range(i0 - 1, -1, -1):
            R[i] = np.maximum(R[i], R[i + 1] - hang_rate)
    for _ in range(smooth):
        R2 = R.copy()
        R2[1:-1] = 0.25 * R[:-2] + 0.5 * R[1:-1] + 0.25 * R[2:]
        R2 = smooth_circ(R2, 1)
        # smoothing may pull cloth in, but not into the layer below
        R = np.maximum(R2, F.R + floor) if floor is not None else np.maximum(R2, R - 0.002)
    G.R = R
    return G


class Garments:
    def __init__(self, body_ob, arm):
        self.B = BodyData(body_ob)
        self.arm = arm
        B = self.B
        co = B.co
        tor = B.ws(["pelvis", "spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r", "neck_01"])
        legs = B.ws(["thigh_l", "thigh_r"])
        armw = B.ws(["upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r", "hand_l", "hand_r"])
        headw = B.ws(["Head"])
        low = ((tor >= 0.5) | ((legs >= 0.3) & (co[:, 2] < 0.98))) & (armw < 0.35) & (co[:, 2] <= 1.15)
        high = (co[:, 2] > 1.15) & (np.abs(co[:, 0]) < 0.175) & (co[:, 2] < 1.46)   # T-pose: x>0.175 = arm
        m = (low | high) & (headw < 0.3) & (np.abs(co[:, 0]) < 0.26)
        self.torso_pts = co[m]
        mid = co[(np.abs(co[:, 0]) < 0.02) & (B.ws(["pelvis"]) >= 0.3)]   # inner thighs touch below
        self.crotch = float(mid[:, 2].min())
        self.T = Field(self.torso_pts, s0=0.66, s1=1.50, ds=0.02, half=0.012, **TORSO_FRAME)
        neck = co[(B.ws(["neck_01", "Head"]) >= 0.5) & (co[:, 2] > 1.36) & (co[:, 2] < 1.56)
                  & (armw < 0.05) & (np.abs(co[:, 0]) < 0.068)]
        self.N = Field(neck, s0=1.38, s1=1.54, ds=0.01, half=0.008, **TORSO_FRAME)
        self.bones = {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in arm.data.bones}
        back = lambda phis: 0.5 - 0.5 * np.cos(phis)
        cr = self.crotch
        self.J = offset_field(self.T, lambda s, ph: 0.017 + 0.006 * back(ph)
                              + 0.020 * min(1.0, max(0.0, (cr + 0.11 - s) / 0.12))    # skirt clears the seat
                              + 0.012 * np.maximum(np.cos(ph), 0.0) * min(1.0, max(0.0, (cr + 0.16 - s) / 0.12)),
                              # ... and the thighs in front
                              hang_from=1.22, hang_rate=0.0022, smooth=10, floor=0.0165)
        self.W = offset_field(self.T, lambda s, ph: 0.011 + max(0.0, s - 1.38) * 0.08 + 0 * ph
                              + 0.003 * min(1.0, max(0.0, (1.0 - s) / 0.06)),
                              hang_from=1.22, hang_rate=0.0035)
        self.S = offset_field(self.T, lambda s, ph: 0.004 + 0 * ph)
        print("GARMENTS crotch", round(self.crotch, 3))

    def ref_torso(self, extra=0.0):
        T = self.T
        return lambda p: (0.0, -T.centre(min(max(p.z, T.ss[0]), T.ss[-1]))[0] + extra,
                          p.z - (0.14 if p.z > 1.3 else 0.0))

    # -------------------------------------------------------------- jacket
    def zneck(self, p):
        """Height of the jacket neckline (back of the neck high, sides lower)."""
        pf = abs(((p + math.pi) % TAU) - math.pi)          # 0 front .. pi back
        return 1.405 + 0.04 * (pf / math.pi) ** 0.8

    def neckline(self, p, extra=0.0):
        return self.N.surf(self.zneck(p), p, 0.021 + extra)

    def x_open(self, z):
        """Half-width (x) of the coat's front opening at height z."""
        b1, b2 = Z["jk_b1"], Z["jk_b2"]
        if z >= b1:   # roll line up to the neck
            return lin([(b1, 0.0), (Z["gorge"], 0.066), (1.44, 0.074), (1.6, 0.08)], z)
        if z >= b2:
            return 0.0
        zh = self.crotch - 0.035
        u = max(0.0, (b2 - z) / (b2 - zh))
        return 0.115 * u ** 0.85

    def build_jacket(self, c):
        J = self.J
        mb = MB("jacket")
        zh = self.crotch - 0.035
        zs = list(np.linspace(zh, 1.20, 14)) + list(np.linspace(1.225, 1.37, 7))
        M = 40
        rows = []
        for z in zs:
            xo = self.x_open(z)
            pl = solve_phi_for_x(J, z, xo, +1) if xo > 1e-4 else 0.0
            pr = solve_phi_for_x(J, z, xo, -1) if xo > 1e-4 else TAU
            if pr <= pl:
                pr += TAU
            rows.append([J.surf(z, p) for p in np.linspace(pl, pr, M)])
        # shoulders: bridge from the 1.37 ring to the neckline ring round the shirt collar
        last_phis = np.linspace(pl, pr, M)
        neck_row = [self.neckline(p) for p in last_phis]
        for t in (0.4, 0.75):
            mid = []
            for a_, b_ in zip(rows[-1], neck_row):
                q = a_.lerp(b_, t)
                q.z += 0.012 * math.sin(math.pi * t)          # slight crown over the shoulder
                mid.append(q)
            rows.append(mid)
        rows.append(neck_row)
        # hem turn-up (inner band gives the cloth an edge thickness)
        cy = -J.centre(zh)[0]
        hem_in = []
        n0 = len(rows[0])
        for k, p in enumerate(rows[0]):
            d = Vector((p.x, p.y - cy, 0.0)).normalized()
            # band fades out toward the open front edges (it would flip out on the cutaway curve)
            e = min(1.0, min(k, n0 - 1 - k) / 4.0)
            hem_in.append(p - d * 0.005 * e + Vector((0, 0, 0.010 * e)))
        mb.grid([hem_in] + rows, "SUIT")
        for side in (1, -1):
            self._lapel(mb, J, side)
        # buttons: top two fastened at the front edge, bottom one on the open right front
        for z in (Z["jk_b1"], Z["jk_b2"], Z["jk_b3"]):
            if z < Z["jk_b2"] - 0.01:
                ph = solve_phi_for_x(J, z, self.x_open(z) + 0.018, -1)
            else:
                ph = TAU - 0.05
            p = J.surf(z, ph, 0.0015)
            n = (p - Vector((0.0, -J.centre(z)[0], z))).normalized()
            mb.disc(p, n, 0.0095, "BUTTON", n=8, depth=0.003)
        # pockets: flaps at the hips, welt breast pocket (his left) with handkerchief edge
        for side in (1, -1):
            z0 = 0.885
            phis_p = [(p * side) % TAU for p in np.linspace(math.radians(40), math.radians(74), 5)]
            top = [J.surf(z0 + 0.052, p, 0.0035) for p in phis_p]
            bot = [J.surf(z0, p, 0.0055) for p in phis_p]
            mb.grid([bot, top], "SUIT")
        phis_b = np.linspace(math.radians(30), math.radians(52), 4)
        wb = [J.surf(1.252, p, 0.002) for p in phis_b]
        wt = [J.surf(1.272, p, 0.0035) for p in phis_b]
        mb.grid([wb, wt], "SUIT")
        hk = [J.surf(1.286, p, 0.003) for p in phis_b[:3]]
        mb.grid([wt[:3], hk], "HANKY")
        return mb.build(c, orient=self.ref_torso())

    def build_collar(self, c):
        """Turn-down coat collar from lapel notch to lapel notch round the back of the neck:
        stand hugging the shirt collar (about 1 cm of it shows above at the back), rolled edge,
        fall lying on the coat shoulders. Own part so its AO never blackens the coat under it."""
        J = self.J
        mb = MB("collar")
        zb = lambda p: 1.428 + 0.028 * (0.5 - 0.5 * math.cos(p))          # shirt-collar base
        phis = np.linspace(math.radians(50), math.radians(310), 30)
        r0 = [self.neckline(p, 0.001) for p in phis]
        r1 = [self.N.surf(zb(p) + 0.027, p, 0.0245) for p in phis]          # stand top
        r2 = [self.N.surf(zb(p) + 0.029, p, 0.0315) for p in phis]          # roll
        r3 = []
        for p in phis:
            pf = abs(((p + math.pi) % TAU) - math.pi)
            drop = 0.034 + 0.012 * max(0.0, 1 - pf / math.radians(80))   # collar ends meet the lapels
            r3.append(J.surf(self.zneck(p) - drop, p, 0.0075))              # fall lies on the coat
        mb.grid([r0, r1, r2, r3], "SUIT")
        return mb.build(c, orient=lambda p: (0.0, -self.N.centre(1.45)[0], p.z - 0.12))

    def _lapel(self, mb, J, side):
        b1 = Z["jk_b1"]
        inner = [(0.0, b1)] + [(self.x_open(z), z) for z in np.linspace(b1 + 0.02, Z["gorge"], 9)]
        outer = [(0.0, b1), (0.035, b1 + 0.045), (0.078, b1 + 0.11), (0.112, Z["notch"] - 0.035),
                 (0.122, Z["notch"]), (0.098, Z["notch"] + 0.036), (inner[-1][0] + 0.004, Z["gorge"])]
        n = 12
        I = resample(inner, n); O = resample(outer, n)
        rows = []
        for t, off in ((0.0, 0.0085), (0.5, 0.0075), (1.0, 0.0065), (1.0, 0.0015)):
            row = []
            for k in range(n):
                x, z = I[k] * (1 - t) + O[k] * t
                phi = solve_phi_for_x(J, z, max(x, 0.0005), side)
                row.append(J.surf(z, phi, off))
            rows.append(row)
        mb.grid(rows, "SUIT")

    # -------------------------------------------------------------- sleeves + shirt cuffs
    def build_sleeves(self, c):
        mb = MB("sleeves")
        cmb = MB("cuffs")
        B = self.B; co = B.co
        for side, sg in (("l", 1), ("r", -1)):
            sh = self.bones[f"upperarm_{side}"][0]
            wr = self.bones[f"hand_{side}"][0]
            w = B.ws([f"upperarm_{side}", f"lowerarm_{side}", f"hand_{side}"])
            m = (w >= 0.5) & (co[:, 0] * sg > abs(sh.x) - 0.04) & (co[:, 0] * sg < abs(wr.x) + 0.005)
            m &= np.hypot(co[:, 1] - sh.y, co[:, 2] - sh.z) < 0.075      # no chest/back points
            F = Field(co[m], o=tuple(sh), a=(sg, 0, 0), e1=(0, 0, 1), e2=(0, -sg, 0),
                      s0=-0.04, s1=abs(wr.x - sh.x) + 0.005, ds=0.015, half=0.01, K=48)
            s_end = abs(wr.x - sh.x) - 0.012
            ss = list(np.linspace(-0.045, 0.08, 5)) + list(np.linspace(0.10, s_end, 12))
            K = 16
            phis = np.linspace(0, TAU, K, endpoint=False)

            def rad(s, p):
                r_min = lin([(-0.045, 0.055), (0.03, 0.058), (0.2, 0.056), (s_end, 0.049)], s)
                ease = lin([(-0.045, 0.012), (0.1, 0.017), (s_end, 0.013)], s)
                r = max(F.radius(s, p) + ease, r_min)
                # the part inside the coat body narrows to a cone, so it stays hidden when the arm drops
                return r * lin([(-0.045, 0.5), (-0.01, 0.82), (0.02, 1.0)], s)
            rows = [[F.point(s, p, rad(s, p)) for p in phis] for s in ss]
            mb.grid(rows, "SUIT", closed=True)
            for k in range(4):   # small cuff buttons on the back of the sleeve, clear of the edge
                s = s_end - 0.03 - k * 0.013
                p = math.radians(200)
                q = F.point(s, p, rad(s, p) + 0.0008)
                nrm = (q - F.point(s, p, 0.0)).normalized()
                mb.disc(q, nrm, 0.0042, "BUTTON", n=6, depth=0.0015)
            # starched shirt cuff: ~1 cm showing beyond the sleeve, rolled edge, plain ivory
            cr = [[F.point(s, p, F.radius(s, p) + dr) for p in phis]
                  for s, dr in ((s_end - 0.03, 0.0062), (s_end + 0.008, 0.0062), (s_end + 0.0115, 0.0045))]
            cmb.grid(cr, "SHIRT", closed=True)
            self._cuff_axis = getattr(self, "_cuff_axis", {})
        sl = mb.build(c, orient=lambda p: (p.x, 0.063, 1.355))
        cf = cmb.build(c, orient=lambda p: (p.x, 0.063, 1.355))
        return sl, cf

    # -------------------------------------------------------------- waistcoat, shirt, collar, tie
    def build_front(self, c):
        W, S, N = self.W, self.S, self.N
        mb = MB("front")
        for side in (1, -1):
            zs = np.linspace(Z["wc_bot"], 1.44, 16)
            rows = []
            for zi, z in enumerate(zs):
                xo = lin([(Z["wc_v"], 0.0), (1.36, 0.042), (1.44, 0.066)], z) if z > Z["wc_v"] else 0.0
                p0 = solve_phi_for_x(W, z, max(xo, 0.0004), side)
                p1 = (math.radians(105) * side) % TAU
                row = []
                for k in range(8):
                    u = k / 7.0
                    p = p0 + (p1 - p0) * u
                    zz = z
                    if zi == 0:   # classic points: notch at the centre, points ~3 cm out, rising to the side
                        zz = (Z["wc_bot"] + 0.028 * (1.0 - u / 0.143) if u < 0.143
                              else Z["wc_bot"] + 0.05 * ((u - 0.143) / 0.857) ** 0.9)
                    pf = abs(((p + math.pi) % TAU) - math.pi)
                    zz = min(zz, lin([(0.0, 1.44), (0.6, 1.43), (1.0, 1.385), (1.85, 1.35)], pf))
                    row.append(W.surf(zz, p % TAU))
                rows.append(row)
            mb.grid(rows, "SUIT")
        for k in range(6):   # waistcoat buttons
            z = Z["wc_v"] - 0.014 - k * 0.046
            p = W.surf(z, TAU - 0.03, 0.0012)
            mb.disc(p, Vector((0.0, -1.0, 0.0)), 0.0062, "BUTTON", n=6, depth=0.002)
        # shirt front panel visible in the waistcoat V
        zs = np.linspace(Z["wc_v"] - 0.03, 1.435, 8)
        rows = [[S.surf(min(z, 1.435 - 0.03 * abs(p) / 0.62), p % TAU) for p in np.linspace(-0.62, 0.62, 9)]
                for z in zs]
        mb.grid(rows, "SHIRT")
        # starched turn-down collar (club): stand + fall, open at the front
        zb = lambda p: 1.428 + 0.028 * (0.5 - 0.5 * math.cos(p))
        phis = np.linspace(math.radians(9), math.radians(351), 30)
        stand_b = [N.surf(zb(p) - 0.016, p, 0.0065) for p in phis]     # shirt yoke under the collar
        stand0 = [N.surf(zb(p), p, 0.004) for p in phis]
        stand1 = [N.surf(zb(p) + 0.04, p, 0.004) for p in phis]
        mb.grid([stand_b, stand0, stand1], "SHIRT")
        fall = []
        rows_t = ((0.0, 0.041, 0.0075), (0.3, 0.030, 0.0115), (0.65, 0.012, 0.0140), (1.0, -0.006, 0.0160))
        for t, dz, dr in rows_t:
            p0 = math.radians(11 + 16 * t ** 1.4)                # V gap widens downward
            row = []
            for u in np.linspace(0.0, 1.0, 30):
                p = p0 + (TAU - 2 * p0) * u
                pf = abs(((p + math.pi) % TAU) - math.pi)
                # club corner: the lowest row rounds up toward the front edge
                corner = max(0.0, 1 - (pf - p0) / math.radians(14)) if t > 0.9 else 0.0
                zz = zb(p) + dz + 0.010 * corner ** 1.5
                row.append(N.surf(zz, p, dr))
            fall.append(row)
        mb.grid(fall, "SHIRT")
        # tie: knot + blade down into the waistcoat V
        fz = 1.43
        kc = N.surf(fz + 0.014, 0.0, 0.0175)
        w0, w1 = 0.0165, 0.0105
        knot = [kc + Vector((-w0, 0.002, 0.017)), kc + Vector((w0, 0.002, 0.017)),
                kc + Vector((w1, -0.003, -0.016)), kc + Vector((-w1, -0.003, -0.016))]
        back = [p + Vector((0, 0.016, 0)) for p in knot]
        mb.poly(list(reversed(knot)), "TIE")
        for i in range(4):
            j = (i + 1) % 4
            mb.poly([knot[i], knot[j], back[j], back[i]], "TIE")
        blade = []
        for z, w in ((fz - 0.004, 0.010), (1.37, 0.020), (1.30, 0.026), (Z["wc_v"] - 0.02, 0.029)):
            phw = w / 0.11
            blade.append([S.surf(z, -phw % TAU, 0.0018), S.surf(z, 0.0, 0.0028), S.surf(z, phw, 0.0018)])
        mb.grid(blade, "TIE")
        return mb.build(c, orient=self.ref_torso(0.02))

    # -------------------------------------------------------------- trousers + shoes
    def build_legs(self, c):
        B = self.B; co = B.co
        mb = MB("trousers")
        T = self.T
        zs = np.linspace(self.crotch + 0.048, Z["tr_top"], 5)     # ends above the crotch, inside the legs
        phis = np.linspace(0, TAU, 32, endpoint=False)
        mb.grid([[T.surf(z, p, 0.008 if z > self.crotch + 0.06 else 0.002) for p in phis] for z in zs],
                "SUIT", closed=True)
        shoe_mb = MB("shoes")
        for side, sg in (("l", 1), ("r", -1)):
            w = B.ws([f"thigh_{side}", f"calf_{side}", f"foot_{side}"])
            m = (w >= 0.5) & (co[:, 0] * sg > 0.0) & (co[:, 2] < self.crotch + 0.05)
            th = self.bones[f"thigh_{side}"][0]
            ank = self.bones[f"foot_{side}"][0]
            L0 = Field(co[m & (co[:, 2] > 0.09)], o=(th.x, 0, 0), a=(0, 0, 1), e1=(0, -1, 0), e2=(1, 0, 0),
                       s0=0.06, s1=self.crotch + 0.04, ds=0.02, half=0.012, K=48)
            # trousers hang straight from the seat: radius may shrink only slowly going down
            L = offset_field(L0, lambda s_, ph_: 0.0 * ph_ + 0.002, hang_from=self.crotch - 0.02,
                             hang_rate=0.0016, smooth=2)
            ph = np.linspace(0, TAU, 16, endpoint=False)

            def rad(z, p):
                prof = lin([(0.0, 0.066), (0.5, 0.072), (0.7, 0.083)], z)
                r = max(L.radius(max(z, 0.08), p) + 0.013, prof)
                if abs(math.cos(p)) > 0.99:     # pressed crease front and back
                    r += 0.004
                return r

            def hem_z(p, base):
                return base + 0.036 * max(0.0, math.cos(p)) ** 1.5    # front rests on the instep
            zs = list(np.linspace(0.11, 0.5, 8)) + list(np.linspace(0.55, self.crotch + 0.065, 7))
            rows = [[L.point(z, p, rad(z, p)) for p in ph] for z in zs]
            inner = [L.point(hem_z(p, 0.042), p, rad(0.08, p) - 0.004) for p in ph]
            cuff = [[L.point(hem_z(p, base), p, rad(0.08, p) + dr) for p in ph]
                    for base, dr in ((0.034, 0.0045), (0.074, 0.0045), (0.077, 0.0005))]
            mb.grid([inner] + cuff + rows, "SUIT", closed=True)
            # shoe: a parametric oxford last along the foot (heel -> toe)
            fw = B.ws([f"foot_{side}", f"ball_{side}"])
            fm = (fw >= 0.4) & (co[:, 0] * sg > 0.0) & (co[:, 2] < 0.10)
            F_ = co[fm]
            heel_y = float(F_[:, 1].max()) + 0.009
            toe_y = float(F_[:, 1].min()) - 0.016
            Ls = heel_y - toe_y
            heel_x = float(np.mean(F_[F_[:, 1] > heel_y - 0.05][:, 0]))
            toe_x = float(np.mean(F_[F_[:, 1] < toe_y + 0.06][:, 0]))
            # (u, half-width, upper height, centre shift toward the big toe)
            prof = [(0.0, 0.020, 0.064, 0.0), (0.03, 0.030, 0.070, 0.0), (0.12, 0.034, 0.078, 0.0),
                    (0.28, 0.036, 0.083, 0.0), (0.42, 0.040, 0.072, 0.0), (0.55, 0.045, 0.060, 0.002),
                    (0.68, 0.048, 0.050, 0.004), (0.80, 0.045, 0.042, 0.006), (0.89, 0.037, 0.035, 0.008),
                    (0.95, 0.026, 0.028, 0.009), (0.985, 0.013, 0.021, 0.010), (1.0, 0.004, 0.016, 0.010)]
            ring = []
            for th in np.linspace(0.0, math.pi, 11):           # upper arc (outer side -> inner side)
                ring.append(("arc", th))
            srows = []
            for u, hw, hh, shift in prof:
                y = heel_y - u * Ls
                xc = heel_x + (toe_x - heel_x) * u - sg * shift   # toe swings toward the big toe
                lift = 0.009 * max(0.0, (u - 0.72) / 0.28) ** 1.6   # toe spring
                row = []
                welt = 0.0035 if 0.02 < u < 0.99 else 0.0015
                row.append(Vector((xc + sg * (hw + welt), y, lift)))
                row.append(Vector((xc + sg * (hw + welt), y, lift + 0.011)))
                for th in np.linspace(0.0, math.pi, 11):
                    ex = math.cos(th); ez = math.sin(th) ** 0.85
                    row.append(Vector((xc + sg * hw * ex, y, lift + 0.012 + (hh - 0.012) * ez)))
                row.append(Vector((xc - sg * (hw + welt), y, lift + 0.011)))
                row.append(Vector((xc - sg * (hw + welt), y, lift)))
                row.append(Vector((xc, y, lift)))
                srows.append(row)
            base = shoe_mb.grid(srows, "SHOE", closed=True)
            n = len(srows[0])
            first = list(range(base, base + n))
            last = list(range(base + (len(srows) - 1) * n, base + len(srows) * n))
            cb = Vector(np.mean([np.array(p) for p in srows[0]], 0)); cb.y += 0.006
            ct = Vector(np.mean([np.array(p) for p in srows[-1]], 0)); ct.y -= 0.004
            shoe_mb.fan(first, cb, "SHOE")
            shoe_mb.fan(last, ct, "SHOE")
        lx, rx = self.bones["thigh_l"][0].x, self.bones["thigh_r"][0].x
        tro = mb.build(c, orient=lambda p: ((lx if p.x > 0 else rx) if p.z < self.crotch + 0.0 else 0.0,
                                            -T.centre(min(max(p.z, T.ss[0]), T.ss[-1]))[0] if p.z >= self.crotch else 0.02,
                                            p.z))
        fl, fr = self.bones["foot_l"][0].x, self.bones["foot_r"][0].x
        sho = shoe_mb.build(c, orient=lambda p: ((fl if p.x > 0 else fr), -0.07, 0.035))
        return tro, sho

    # -------------------------------------------------------------- tape measure, watch chain
    def build_accessories(self, c):
        J, W, N = self.J, self.W, self.N
        mb = MB("accessories")
        for side in (1, -1):
            path = []
            for p_deg, dz in ((180, 0.026), (140, 0.024), (100, 0.018), (70, 0.004)):
                ph = (math.radians(p_deg) * side) % TAU
                path.append(N.surf(self.zneck(ph) + dz, ph, 0.032))
            for z, x in ((1.38, 0.093), (1.30, 0.092), (1.22, 0.088), (1.15, 0.083), (1.09, 0.08)):
                ph = solve_phi_for_x(J, z, x, side)
                path.append(J.surf(z, ph, 0.0115 if z > 1.13 else 0.0045))
            P = [Vector(tuple(p)) for p in resample(path, 18)]
            for k, q in enumerate(P):
                if q.z < 1.415:
                    ph = math.atan2(q.x, -(q.y + J.centre(q.z)[0])) % TAU
                    P[k] = J.surf(q.z, ph, 0.0115 if q.z > 1.13 else 0.0045)
            left, right = [], []
            for k in range(len(P)):
                t = (P[min(k + 1, len(P) - 1)] - P[max(k - 1, 0)]).normalized()
                cz = min(max(P[k].z, self.T.ss[0]), self.T.ss[-1])
                outn = (P[k] - Vector((0.0, -J.centre(cz)[0], P[k].z))).normalized()
                bi = t.cross(outn).normalized()
                left.append(P[k] - bi * 0.008); right.append(P[k] + bi * 0.008)
            mb.grid([left, right], "TAPE")
        # watch chain: one shallow curve from pocket to pocket (about 8 cm each side of the
        # buttons), lowest in the middle where a T-bar hooks into a waistcoat buttonhole
        z_end, sag = 1.006, 0.015
        n = 15
        pts = []
        for k in range(n):
            u = k / (n - 1)
            x = -0.082 + 0.164 * u
            z = z_end - sag * math.sin(math.pi * u)
            phi = solve_phi_for_x(W, z, max(abs(x), 0.0004), 1 if x >= 0 else -1)
            pts.append(W.surf(z, phi, 0.0035))
        rows = []
        for k, p in enumerate(pts):
            t = (pts[min(k + 1, n - 1)] - pts[max(k - 1, 0)]).normalized()
            n1 = t.orthogonal().normalized(); n2 = t.cross(n1)
            rows.append([p + 0.0021 * (math.cos(TAU * j / 4) * n1 + math.sin(TAU * j / 4) * n2) for j in range(4)])
        mb.grid(rows, "GOLD", closed=True)
        zc = z_end - sag
        a = W.surf(zc + 0.006, 0.0, 0.0035)
        nrm = (a - Vector((0.0, -W.centre(zc)[0], zc))).normalized()
        mb.disc(a, nrm, 0.0042, "GOLD", n=6, depth=0.002)              # T-bar at the buttonhole
        return mb.build(c, orient=self.ref_torso(0.03))


# ----------------------------------------------------------------------------------------------
# 5. head, neck, hands, hair, eyes, pencil (from the MakeHuman body)
# ----------------------------------------------------------------------------------------------
HEAD_TRIS = 3000
HAND_TRIS = 2000
HAIR_TRIS = 700
# hairline height (m) by azimuth round the head (0 = forehead centre, 180 = nape), both sides
HAIRLINE = [(0, 1.663), (20, 1.666), (36, 1.671), (50, 1.657), (60, 1.630), (68, 1.600), (74, 1.588),
            (79, 1.617), (98, 1.619), (104, 1.588), (115, 1.572), (130, 1.560), (150, 1.546), (165, 1.536),
            (180, 1.533)]                  # ear: az 76..101 (hair stops just above it)
HEAD_C = Vector((0.0, -0.012, 1.60))          # head centre for hairline azimuth


def az_of(p):
    return abs(math.degrees(math.atan2(p[0] - HEAD_C.x, -(p[1] - HEAD_C.y))))


def z_hair(az):
    return lin(HAIRLINE, az)


def keep_faces(src, name, vmask, c):
    """Copy of src with only the faces whose verts are all in vmask."""
    me = src.data.copy(); me.name = name
    ob = bpy.data.objects.new(name, me); c.objects.link(ob)
    if not len(ob.vertex_groups):
        for vg in src.vertex_groups:
            ob.vertex_groups.new(name=vg.name)
    bm_ = bmesh.new(); bm_.from_mesh(me)
    kill = [f for f in bm_.faces if not all(vmask[v.index] for v in f.verts)]
    bmesh.ops.delete(bm_, geom=kill, context="FACES")
    loose = [v for v in bm_.verts if not v.link_faces]
    bmesh.ops.delete(bm_, geom=loose, context="VERTS")
    bm_.to_mesh(me); bm_.free(); me.update()
    return ob


def decimate_to(ob, tris, keep_group=None):
    cur = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    if cur <= tris:
        return
    m = ob.modifiers.new("Decimate", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = tris / cur
    if keep_group:
        m.vertex_group = keep_group          # weighted verts resist collapsing
        m.invert_vertex_group = True
        m.vertex_group_factor = 10.0
    m.use_symmetry = True
    m.symmetry_axis = "X"
    m.use_collapse_triangulate = True
    activate(ob)
    bpy.ops.object.modifier_apply(modifier=m.name)


def project_uv_from(target, proxy, uv_name, max_dist=0.012):
    """For each target vertex near the proxy surface, store the proxy's UV at the nearest point
    in a new UV layer (far vertices get UV (0.001, 0.001), a transparent corner)."""
    from mathutils.bvhtree import BVHTree
    from mathutils.geometry import barycentric_transform
    pm = proxy.data
    bvh = BVHTree.FromPolygons([v.co for v in pm.vertices], [p.vertices for p in pm.polygons])
    puv = pm.uv_layers.active.data
    poly_loops = [list(p.loop_indices) for p in pm.polygons]
    tm = target.data
    layer = tm.uv_layers.new(name=uv_name)
    vert_uv = {}
    for v in tm.vertices:
        loc, nrm, idx, d = bvh.find_nearest(v.co)
        if loc is None or d > max_dist:
            vert_uv[v.index] = (0.001, 0.001)
            continue
        p = pm.polygons[idx]
        vs = [pm.vertices[i].co for i in p.vertices]
        uvs = [Vector((puv[li].uv[0], puv[li].uv[1], 0.0)) for li in poly_loops[idx]]
        # split polygon into a fan of triangles, use the one containing loc
        best = None
        for k in range(1, len(vs) - 1):
            a, b, c_ = vs[0], vs[k], vs[k + 1]
            uv = barycentric_transform(loc, a, b, c_, uvs[0], uvs[k], uvs[k + 1])
            best = uv
            from mathutils.geometry import intersect_point_tri
            if intersect_point_tri(loc, a, b, c_):
                break
        vert_uv[v.index] = (best.x, best.y)
    for poly in tm.polygons:
        for li, vi in zip(poly.loop_indices, poly.vertices):
            layer.data[li].uv = vert_uv[vi]


def stage_skin(src, garments):
    work = bpy.data.collections[WORK]
    main = bpy.data.collections[COLL]
    body = src["Body"]
    B = garments.B
    co = B.co
    # ---- hair: a shell grown off the scalp, inside a 1920 hairline; thickness from short02,
    #      flattened (pomade); parting groove on his left
    from mathutils.bvhtree import BVHTree
    proxy = src["Hair"]
    pbvh = BVHTree.FromObject(proxy, bpy.context.evaluated_depsgraph_get())
    above_v = np.array([p[2] > z_hair(az_of(p)) for p in co]) & (co[:, 2] > 1.45)
    above_v &= B.ws(["ears"]) < 0.3 if "ears" in B.w else True
    # keep faces with at least half their verts above the line, then relax the edge loop
    me_b = body.data
    vm = np.zeros(len(co), bool)
    for poly in me_b.polygons:
        if sum(above_v[i] for i in poly.vertices) >= 2 and co[poly.vertices[0], 2] > 1.45:
            for i in poly.vertices:
                vm[i] = True
    hair = keep_faces(body, "PART_hair", vm, main)
    hm = hair.data
    bm_ = bmesh.new(); bm_.from_mesh(hm)
    # drop faces not mostly above the hairline (keep_faces kept any face whose verts are in vm)
    kill = [f for f in bm_.faces if sum(1 for v in f.verts if v.co.z > z_hair(az_of(v.co))) < 2]
    bmesh.ops.delete(bm_, geom=kill, context="FACES")
    bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if not v.link_faces], context="VERTS")
    sbvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    for _ in range(4):
        new = {}
        for v in bm_.verts:
            if v.is_boundary:
                nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
                if len(nb) == 2:
                    new[v] = v.co * 0.4 + (nb[0].co + nb[1].co) * 0.3
        for v, c_ in new.items():
            loc, _n, _i, _d = sbvh.find_nearest(c_)
            v.co = loc if loc is not None else c_
    bm_.to_mesh(hm); bm_.free()
    bm_ = bmesh.new(); bm_.from_mesh(hm); bm_.normal_update()
    bnd = {v.index for v in bm_.verts if v.is_boundary}
    nrm = {v.index: v.normal.copy() for v in bm_.verts}
    bm_.free()
    part_x = 0.030
    for v in hm.vertices:
        p = v.co.copy()
        n = nrm[v.index]
        hit = pbvh.ray_cast(p + n * 0.0005, n, 0.05)
        d_short = hit[3] if hit[0] is not None else 0.004
        t = min(0.0095, max(0.0028, 0.45 * d_short))
        above = p.z - z_hair(az_of(p))
        taper = min(1.0, max(0.0, above / 0.009)) ** 0.6
        t = 0.0016 + (t - 0.0016) * taper
        if v.index in bnd:
            t = 0.0010
        if p.z > 1.665 and p.y < 0.04:               # parting groove
            g = math.exp(-((p.x - part_x) / 0.0055) ** 2)
            t = max(0.0012, t - 0.0045 * g)
            if p.x < part_x:                         # combed-over side a touch fuller
                t += 0.0012 * min(1.0, (part_x - p.x) / 0.03)
        v.co = p + n * t
    hm.update()
    decimate_to(hair, HAIR_TRIS)
    # ---- high-res head (bake source) + low-res head
    neck_r = np.hypot(co[:, 0] / 0.064, (co[:, 1] - 0.0) / 0.075)
    head_mask = (co[:, 2] > 1.398) & (np.abs(co[:, 0]) < 0.11) & ((co[:, 2] > 1.47) | (neck_r < 1.0))
    hi = keep_faces(body, "HI_head", head_mask, work)
    # scalp under the hair edge gets the hair colour in the bake (no skin glints at the hairline)
    at = hi.data.attributes.new("hairzone", "FLOAT", "POINT")
    at.data.foreach_set("value", [min(1.0, max(0.0, (v.co.z - z_hair(az_of(v.co)) + 0.002) / 0.006))
                                  for v in hi.data.vertices])
    # moustache relief: push the upper-lip area 1.5 mm forward
    for v in hi.data.vertices:
        p = v.co
        if 1.5405 < p.z < 1.5545 and abs(p.x) < 0.026 and p.y < -0.10:
            k = (1 - (abs(p.x) / 0.026) ** 3)
            v.co.y -= 0.0015 * k
    # delete scalp faces fully covered by the hair shell
    hbvh = BVHTree.FromObject(hair, bpy.context.evaluated_depsgraph_get())
    lo = keep_faces(hi, "PART_head", np.ones(len(hi.data.vertices), bool), main)
    bm_ = bmesh.new(); bm_.from_mesh(lo.data)
    covered = set()
    for v in bm_.verts:
        loc, nrm, idx, d = hbvh.find_nearest(v.co)
        if v.co.z - z_hair(az_of(v.co)) < 0.008:
            continue
        if loc is not None and d < 0.016 and (loc - v.co).dot(v.normal) > 0:
            # ray along the normal must hit the hair shell
            hit = hbvh.ray_cast(v.co + v.normal * 0.0005, v.normal, 0.03)
            if hit[0] is not None:
                covered.add(v.index)
    kill = [f for f in bm_.faces if all(v.index in covered for v in f.verts)]
    bmesh.ops.delete(bm_, geom=kill, context="FACES")
    bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if not v.link_faces], context="VERTS")
    bm_.to_mesh(lo.data); bm_.free()
    decimate_to(lo, HEAD_TRIS)
    # ---- hands (+ wrist inside the shirt cuff)
    hand_x = abs(garments.bones["hand_l"][0].x) - 0.035
    hmask = np.abs(co[:, 0]) > hand_x
    hands_hi = keep_faces(body, "HI_hands", hmask, work)
    hands = keep_faces(body, "PART_hands", hmask, main)
    decimate_to(hands, HAND_TRIS)
    # ---- eyes
    eyes = src["Eyes"]
    eyes.name = "PART_eyes"; eyes.data.name = "PART_eyes"
    move_to(eyes, main)
    for ob in (hair, lo, hands, eyes):
        ob.data.materials.clear()
        for m in MATS:
            ob.data.materials.append(bpy.data.materials.get("SRC_" + m) or bpy.data.materials.new("SRC_" + m))
    hair.data.polygons.foreach_set("material_index", [MATS.index("HAIR")] * len(hair.data.polygons))
    lo.data.polygons.foreach_set("material_index", [MATS.index("SKIN")] * len(lo.data.polygons))
    hands.data.polygons.foreach_set("material_index", [MATS.index("SKIN")] * len(hands.data.polygons))
    eyes.data.polygons.foreach_set("material_index", [MATS.index("EYE")] * len(eyes.data.polygons))
    for ob in (hair, lo, hands, eyes):
        for p in ob.data.polygons:
            p.use_smooth = True
    # ---- pencil behind his right ear
    ears = body.vertex_groups["ears"].index
    ev = np.array([v.co[:] for v in body.data.vertices
                   if v.co.x < 0 and any(g.group == ears and g.weight > 0.5 for g in v.groups)])
    ear_top = Vector((float(ev[:, 0].mean()) + 0.006, float(ev[:, 1].mean()) + 0.004, float(ev[:, 2].max()) - 0.004))
    d = Vector((0.18, -0.92, -0.34)).normalized()
    mb = MB("pencil")
    L = 0.088; r = 0.0036
    n1 = d.orthogonal().normalized(); n2 = d.cross(n1)
    back_end = ear_top - d * (L * 0.45)
    ring = lambda c_, rr: [c_ + rr * (math.cos(TAU * k / 6) * n1 + math.sin(TAU * k / 6) * n2) for k in range(6)]
    r0 = ring(back_end, r); r1 = ring(back_end + d * (L - 0.016), r)
    b0 = mb.grid([r0, r1], "PENCIL", closed=True)
    mb.fan(list(range(b0, b0 + 6)), back_end - d * 0.001, "PENCIL", flip=True)
    r2 = ring(back_end + d * (L - 0.004), r * 0.35)
    b1 = mb.grid([r1, r2], "TAPE", closed=True)
    mb.fan(list(range(b1 + 6, b1 + 12)), back_end + d * L, "BUTTON")
    pen = mb.build(main, orient=lambda p: back_end + (p - back_end).project(d))
    print("SKIN parts", {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in (hair, lo, hands, eyes, pen)})
    for k in ("Eyebrows",):
        src[k].hide_render = True
        src[k].hide_set(True)
    hi.hide_set(True); hands_hi.hide_set(True)
    return dict(hair=hair, head=lo, hands=hands, eyes=eyes, pencil=pen, head_hi=hi, hands_hi=hands_hi)


# ----------------------------------------------------------------------------------------------
# 6. skinning
# ----------------------------------------------------------------------------------------------
def transfer_weights(ob, donor, arm, rigid=None):
    """Copy deform weights from donor (nearest face, interpolated); rigid = bone name for 100 %."""
    bone_names = {b.name for b in arm.data.bones}
    for vg in list(ob.vertex_groups):
        ob.vertex_groups.remove(vg)
    if rigid:
        g = ob.vertex_groups.new(name=rigid)
        g.add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")
    else:
        for vg in donor.vertex_groups:
            if vg.name in bone_names:
                ob.vertex_groups.new(name=vg.name)
        m = ob.modifiers.new("DT", "DATA_TRANSFER")
        m.object = donor
        m.use_vert_data = True
        m.data_types_verts = {"VGROUP_WEIGHTS"}
        m.vert_mapping = "POLYINTERP_NEAREST"
        m.layers_vgroup_select_src = "ALL"
        m.layers_vgroup_select_dst = "NAME"
        activate(ob)
        bpy.ops.object.modifier_apply(modifier=m.name)
    # drop non-bone groups
    for vg in list(ob.vertex_groups):
        if vg.name not in bone_names:
            ob.vertex_groups.remove(vg)


def blend_to_bone(ob, bone, fn):
    """Blend each vertex's weights toward 100 % `bone` by factor fn(co) in 0..1."""
    g = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
    for v in ob.data.vertices:
        t = fn(v.co)
        if t <= 0:
            continue
        for ge in v.groups:
            ge.weight *= (1 - t)
        g.add([v.index], 0.0, "ADD")
        cur = next((ge.weight for ge in v.groups if ge.group == g.index), 0.0)
        g.add([v.index], cur + t, "REPLACE")


def finish_weights(ob, smooth=0):
    activate(ob)
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    if smooth:
        bpy.ops.object.vertex_group_smooth(group_select_mode="ALL", factor=0.5, repeat=smooth)
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
    bpy.ops.object.vertex_group_clean(group_select_mode="ALL", limit=0.01)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def stage_weights(parts, donor, arm, crotch):
    sh_x = abs(arm.data.bones["upperarm_l"].head_local.x)
    order = ["jacket"] + [k for k in parts if k != "jacket"]
    for name in order:
        ob = parts[name]
        if name in ("pencil", "eyes"):
            transfer_weights(ob, donor, arm, rigid="Head")
            continue
        # layers under / on the coat front move with the coat, so they never cross it
        transfer_weights(ob, parts["jacket"] if name in ("front", "accessories", "collar") else donor, arm)
        if name == "trousers":
            # the waist (under the coat) moves with the coat
            mask = ob.vertex_groups.new(name="HIPMASK")
            for v in ob.data.vertices:
                t = min(1.0, max(0.0, (v.co.z - (crotch + 0.06)) / 0.08))
                if t > 0:
                    mask.add([v.index], t, "REPLACE")
            m = ob.modifiers.new("DT2", "DATA_TRANSFER")
            m.object = parts["jacket"]; m.use_vert_data = True
            m.data_types_verts = {"VGROUP_WEIGHTS"}; m.vert_mapping = "POLYINTERP_NEAREST"
            m.layers_vgroup_select_src = "ALL"; m.layers_vgroup_select_dst = "NAME"
            m.vertex_group = "HIPMASK"; m.mix_mode = "REPLACE"; m.mix_factor = 1.0
            for vg in parts["jacket"].vertex_groups:
                if vg.name not in ob.vertex_groups:
                    ob.vertex_groups.new(name=vg.name)
            activate(ob)
            bpy.ops.object.modifier_apply(modifier=m.name)
            ob.vertex_groups.remove(ob.vertex_groups["HIPMASK"])
            # each trouser leg tube belongs to its own thigh (no "drop crotch" when the legs part);
            # the hip tube above stays with the pelvis / coat
            for side, sg in (("l", 1.0), ("r", -1.0)):
                blend_to_bone(ob, f"thigh_{side}", lambda p, sg=sg: 0.0 if p.x * sg <= 0.0 else
                              0.8 * min(1.0, max(0.0, (crotch + 0.07 - p.z) / 0.06))
                              * min(1.0, max(0.0, (p.z - 0.45) / 0.15)))
        if name == "collar":
            def collar_f2(p):
                return 0.85
            blend_to_bone(ob, "spine_03", collar_f2)
        if name == "front":
            nz = lambda p: (p.z > 1.41 and math.hypot(p.x, p.y + 0.01) < 0.085)
            blend_to_bone(ob, "neck_01", lambda p: 0.7 if nz(p) else 0.0)
        if name == "sleeves":
            # sleeve head stays with the shoulder girdle instead of swinging up with the arm
            for side, sg in (("l", 1.0), ("r", -1.0)):
                blend_to_bone(ob, f"clavicle_{side}",
                              lambda p, sg=sg: 0.0 if p.x * sg < 0 else
                              0.85 * min(1.0, max(0.0, (sh_x + 0.05 - p.x * sg) / 0.09)))
        if name == "jacket":
            # coat collar and neckline ride on the upper spine, not on the neck (no gap opens
            # under the collar when the head nods)
            def collar_f(p):
                rr = math.hypot(p.x, p.y + 0.005)
                return 0.85 * min(1.0, max(0.0, (p.z - 1.37) / 0.03)) * min(1.0, max(0.0, (0.15 - rr) / 0.04))
            blend_to_bone(ob, "spine_03", collar_f)
            # coat skirt hangs from the pelvis instead of splitting with the legs
            blend_to_bone(ob, "pelvis", lambda p: min(1.0, max(0.0, (crotch + 0.12 - p.z) / 0.14)) * 0.85)
            # open fronts below the 2nd button hang from the waist (spine_01 / pelvis), never the thighs
            def front_f(p):
                if p.y > -0.03 or p.z > 1.07:
                    return 0.0
                return 0.75 * min(1.0, (1.07 - p.z) / 0.07) * min(1.0, (-0.03 - p.y) / 0.04)
            blend_to_bone(ob, "spine_01", lambda p: 0.5 * front_f(p) if p.z > 0.95 else 0.0)
            blend_to_bone(ob, "pelvis", front_f)
        finish_weights(ob, smooth=0 if name in ("head", "hands", "hair") else (4 if name == "jacket" else 2))
        m = ob.modifiers.new("Armature", "ARMATURE")
        m.object = arm
    for ob in (parts["pencil"], parts["eyes"]):
        m = ob.modifiers.new("Armature", "ARMATURE"); m.object = arm
    for ob in parts.values():
        ob.parent = arm
        ob.matrix_parent_inverse = arm.matrix_world.inverted()


# ----------------------------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------------------------
def build_all():
    new_file()
    with win_ctx():
        arm = stage_rig()
        src = stage_human(arm)
        main = bpy.data.collections[COLL]
        G = Garments(src["Body"], arm)
        parts = dict(jacket=G.build_jacket(main), collar=G.build_collar(main))
        parts["sleeves"], parts["cuffs"] = G.build_sleeves(main)
        parts["front"] = G.build_front(main)
        parts["trousers"], parts["shoes"] = G.build_legs(main)
        parts["accessories"] = G.build_accessories(main)
        sk = stage_skin(src, G)
        for k in ("hair", "head", "hands", "eyes", "pencil"):
            parts[k] = sk[k]
        stage_weights(parts, src["Body"], arm, G.crotch)
        src["Body"].hide_set(True)
        src["Body"].hide_render = True
        tot = 0
        for k, ob in parts.items():
            t = sum(len(p.vertices) - 2 for p in ob.data.polygons); tot += t
            print("PART", k, t)
        print("TOTAL TRIS", tot)
        bpy.ops.wm.save_mainfile()
    return parts


if not globals().get("PICKELL_LIB_ONLY"):
    PARTS = build_all()
