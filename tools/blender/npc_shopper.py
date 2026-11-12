"""
A2 - an anonymous woman shopping on the east walk (before the Bank Building), September 1920 -
geometry + rig build.

Run inside Blender (MPFB 2.0.18 extension enabled, MakeHuman CC0 system-asset pack loaded):
    exec(open(r"<project>/tools/blender/npc_shopper.py").read())

Same pipeline as John B. Pickell (tools/blender/npc_pickell.py, loaded here as a library with
PICKELL_LIB_ONLY); what differs:
  * MakeHuman FEMALE, about 35 (age 0.577), slim-average build; head, neck (with the V of the
    blouse), hands and the stockinged lower legs are kept from the body.
  * The UAL rig is scaled uniformly to her size and then its JOINTS are moved onto hers (bone
    orientations unchanged, so the UAL clips play as authored): no limb stretching, no
    man's shoulders. Location keys are scaled with the uniform factor.
  * Clips: Idle (Idle_Loop x2 slowed, glance) and Talk (Idle_Talking_Loop), re-keyed with the
    feet close together (ankles 0.15 m, toes out 14 deg), level gaze, and her LEFT arm held in a
    fixed basket-carrying pose (forearm forward, relative to the chest) in every frame; the
    gesturing right arm is calmed (blended 35 % toward the Idle arm); the spine is eased toward
    upright and the UAL's 27 cm front-to-back stagger of the feet cut to 7 cm. No Walk clip (the
    UAL stride swings the legs through a mid-calf skirt).
  * Clothes (1920): loose white shirtwaist blouse (long sleeves, button cuffs, flat collar, open
    V neck, placket buttons), dropped waist with a sash and side bow at the hips, mid-calf
    skirt with soft folds, dark stockings, laced low-heeled shoes; hair pinned up with a low bun;
    wide-brimmed straw hat with a ribbon band and bow; a wicker market basket with a cloth
    cover hooked over the left forearm.
  * Skirt weighting: pelvis, with a smooth share of the thighs that grows toward the hem and
    toward each side (checked against the legs in every Idle / Talk frame by shopper_check()).
  * Final height (head/hair top) is set by the bake script (uniform rescale before export).
Materials/atlas/AO/export: npc_shopper_bake.py.  Previews: npc_shopper_preview.py.

Blender: Z up, metres, front faces -Y, origin on the ground between the feet.
"""
import bpy, bmesh, math, os
import numpy as np
from mathutils import Vector, Matrix, Quaternion

_ROOT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PICKELL_LIB_ONLY = True
exec(open(os.path.join(_ROOT, r"tools\blender\npc_pickell.py"), encoding="utf-8").read())
PICKELL_LIB_ONLY = False

# ---------------------------------------------------------------------------------------------
# overrides
# ---------------------------------------------------------------------------------------------
BLEND = os.path.join(ROOT, r"assets\models\source\npc-shopper.blend")
COLL = "NPC_Shopper"
WORK = "NPC_Shopper_Work"
RIG_NAME = "Shopper_Rig"
TARGET_H = 1.615            # first uniform UAL scale (mannequin 1.829 m); joints then fitted
TORSO_DY = 0.0              # rig joints are moved onto hers: no torso offset
MACRO = dict(gender=0.0, age=0.577, muscle=0.42, weight=0.52, proportions=0.62, height=0.52,
             cupsize=0.45, firmness=0.5)
# MakeHuman age slider: 0.5 = 25 y, 1.0 = 90 y  ->  35 y = 0.5 + 10/65*0.5 = 0.577
PROXIES = (("Eyes", r"eyes\low-poly\low-poly.mhclo"),
           ("Eyebrows", r"eyebrows\eyebrow004\eyebrow004.mhclo"))
MH_TARGETS = os.path.join(os.environ["APPDATA"], r"Blender Foundation\Blender\5.2\extensions"
                          r"\user_default\mpfb\data\targets")
FACE_TARGETS = [            # (relative path, weight): a little character, not a doll face
    (r"head\head-oval.target.gz", 0.35),
    (r"nose\nose-scale-vert-incr.target.gz", 0.15),
    (r"nose\nose-hump-incr.target.gz", 0.12),
    (r"chin\chin-prominent-incr.target.gz", 0.10),
    (r"mouth\mouth-scale-horiz-decr.target.gz", 0.10),
    (r"cheek\l-cheek-bones-incr.target.gz", 0.25),
    (r"cheek\r-cheek-bones-incr.target.gz", 0.25),
]
ANKLE_SEP = 0.15
TOE_OUT = math.radians(14)
STAGGER = 0.07

# Pickell's stance tool only turns toes IN; the UAL idle stands with one foot turned in and one
# far out, so here each foot is turned (either way) to TOE_OUT.
_psrc = open(os.path.join(_ROOT, r"tools\blender\npc_pickell.py"), encoding="utf-8").read()
_psrc = _psrc[_psrc.index("def adjust_stance_and_gaze"):_psrc.index("def build_clips")]
for _a, _b in (("turn[side] = max(0.0, t0 - toe_out_target)", "turn[side] = abs(t0 - toe_out_target)"),
               ("if best is None or val < best[0]:\n                best = (val, sgn)",
                "if best is None or abs(val - toe_out_target) < best[0]:\n"
                "                best = (abs(val - toe_out_target), sgn)")):
    assert _a in _psrc, _a
    _psrc = _psrc.replace(_a, _b)
exec(_psrc)


def arm_global():
    return bpy.data.objects[RIG_NAME]


# ---------------------------------------------------------------------------------------------
# 1. rig: import + uniform scale (clips built only after the joints are fitted)
# ---------------------------------------------------------------------------------------------
def stage_rig_s():
    sc = bpy.context.scene
    sc.render.fps = 24
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
    arm.name = arm.data.name = RIG_NAME
    man.name = "UAL_Mannequin_donor"
    move_to(arm, main)
    move_to(man, work)
    h = max((man.matrix_world @ Vector(b)).z for b in man.bound_box)
    s = TARGET_H / h
    arm.scale = (s, s, s)
    bpy.context.view_layer.update()
    activate(arm)
    man.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
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
    print("RIG scale", round(s, 5), "bones", len(arm.data.bones))
    return arm


# ---------------------------------------------------------------------------------------------
# 2. MPFB woman; the rig's joints are moved onto hers
# ---------------------------------------------------------------------------------------------
MPFB2UAL = {"head": "Head", "Root": "root"}


def fit_deltas(rig, arm):
    """Where each MakeHuman joint lands when her limbs are swung (not stretched) onto the UAL
    bone directions: {MPFB bone: new joint position}."""
    Rm = {b.name: b.matrix_local.copy() for b in rig.data.bones}
    Ru = {b.name: b.matrix_local.copy() for b in arm.data.bones}
    hm = {n: m.translation.copy() for n, m in Rm.items()}
    D = {n: Matrix.Identity(4) for n in Rm}
    Q = {}

    def make(n, h_new, q):
        M = q.to_matrix().to_4x4()
        D[n] = Matrix.Translation(h_new) @ M @ Matrix.Translation(-hm[n])
        Q[n] = q
    ym = lambda n: bone_y(Rm[n])
    yu = lambda n: bone_y(Ru[n])
    for side in ("l", "r"):
        up, lo, ha = f"upperarm_{side}", f"lowerarm_{side}", f"hand_{side}"
        make(up, hm[up], swing(ym(up), yu(up)))
        make(lo, D[up] @ hm[lo], swing(Q[up] @ ym(lo), yu(lo)) @ Q[up])
        make(ha, D[lo] @ hm[ha], swing(Q[lo] @ ym(ha), yu(ha)) @ Q[lo])
        for f in ("thumb", "index", "middle", "ring", "pinky"):
            parent = ha
            for i in (1, 2, 3):
                n = f"{f}_0{i}_{side}"
                if n not in Rm or n not in Ru:
                    continue
                make(n, D[parent] @ hm[n], swing(Q[parent] @ ym(n), yu(n)) @ Q[parent])
                parent = n
        th, ca, fo, ba = (f"thigh_{side}", f"calf_{side}", f"foot_{side}", f"ball_{side}")
        make(th, hm[th], swing(ym(th), yu(th)))
        make(ca, D[th] @ hm[ca], swing(Q[th] @ ym(ca), yu(ca)) @ Q[th])
        make(fo, D[ca] @ hm[fo], swing(Q[ca] @ ym(fo), yu(fo)) @ Q[ca])
        make(ba, D[fo] @ hm[ba], swing(Q[fo] @ ym(ba), yu(ba)) @ Q[fo])
    return {MPFB2UAL.get(n, n): D[n] @ hm[n] for n in Rm}


def fit_rig(rig, arm):
    """Move every UAL joint onto the MakeHuman joint (orientation and length of each bone kept;
    UAL-only leaf bones follow their parent)."""
    new = fit_deltas(rig, arm)
    activate(arm)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    delta = {}
    # parents first
    order = []

    def walk(b):
        order.append(b)
        for c_ in b.children:
            walk(c_)
    for b in eb:
        if b.parent is None:
            walk(b)
    moved = []
    for b in order:
        if b.name in new:
            d = new[b.name] - b.head
        elif b.parent is not None and b.parent.name in delta:
            d = delta[b.parent.name]
        else:
            d = Vector((0, 0, 0))
        delta[b.name] = d.copy()
        roll = b.roll
        b.head = b.head + d
        b.tail = b.tail + d
        b.roll = roll
        if d.length > 0.003:
            moved.append((b.name, round(d.length, 3)))
    bpy.ops.object.mode_set(mode="OBJECT")
    print("FIT moved", moved[:30])


def stage_human_s(arm):
    from bl_ext.user_default.mpfb.services.humanservice import HumanService
    from bl_ext.user_default.mpfb.services.targetservice import TargetService
    work = bpy.data.collections[WORK]
    md = TargetService.get_default_macro_info_dict()
    md.update(MACRO)
    md["race"] = {"asian": 0.0, "caucasian": 1.0, "african": 0.0}
    bm_obj = HumanService.create_human(macro_detail_dict=md)
    for rel, w in FACE_TARGETS:
        p = os.path.join(MH_TARGETS, rel)
        if os.path.exists(p):
            TargetService.load_target(bm_obj, p, weight=w)
        else:
            print("TARGET missing", rel)
    bpy.context.view_layer.update()
    activate(bm_obj)
    rig = HumanService.add_builtin_rig(bm_obj, "game_engine")
    prox = {}
    for kind, rel in PROXIES:
        activate(bm_obj)
        prox[kind] = HumanService.add_mhclo_asset(os.path.join(MH_DATA, rel), bm_obj, asset_type=kind,
                                                  subdiv_levels=0, material_type="NONE")
    bpy.context.view_layer.update()
    fit_rig(rig, arm)
    D = retarget_deltas(rig, arm)
    src = {}
    co = evaluated_coords(bm_obj)
    src["Body"] = bake_copy(bm_obj, lbs(bm_obj, co, D), "SRC_Body", work, keep_group="body")
    for kind, ob in prox.items():
        co = evaluated_coords(ob)
        src[kind] = bake_copy(ob, lbs(ob, co, D), "SRC_" + kind, work)
    for ob in [bm_obj, rig] + list(prox.values()):
        bpy.data.objects.remove(ob, do_unlink=True)
    for o in src.values():
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
    z = np.array([v.co.z for v in src["Body"].data.vertices])
    print("HUMAN", {k: len(v.data.vertices) for k, v in src.items()}, "height", round(float(z.max()), 4),
          "soles", round(float(z.min()), 4))
    return src


# ---------------------------------------------------------------------------------------------
# 3. clips: narrow stance, level gaze, basket arm, calmer gestures
# ---------------------------------------------------------------------------------------------
# carry pose of her left arm, in the rest frame of the chest (spine_03), armature axes:
# +X her left, -Y front, +Z up.  (bone axis direction, palm/flexion reference direction)
CARRY = dict(
    upperarm=((0.20, -0.16, -1.0), (0.05, -1.0, 0.25)),     # hangs, a little out and forward
    lowerarm=((0.14, -1.0, 0.10), (-1.0, 0.0, 0.25)),       # forearm forward, thumb up
    hand=((0.10, -1.0, -0.22), (-1.0, 0.05, 0.15)),         # wrist relaxed, slightly dropped
)


def _basis(axis, ref):
    y = Vector(axis).normalized()
    x = (Vector(ref) - Vector(ref).dot(y) * y).normalized()
    z = x.cross(y)
    return Matrix((x, y, z)).transposed()          # columns x, y, z


def carry_rotations(arm):
    """Armature-space 3x3 rotations of the three left-arm bones in the carry pose, expressed
    relative to the chest's rest frame (pose = chest_now @ rel)."""
    B = arm.data.bones
    chest0 = B["spine_03"].matrix_local.to_3x3()
    out = {}
    # rest references: the bone's own axis and its T-pose reference direction
    rest_ref = {"upperarm": Vector((0, -1, 0)), "lowerarm": Vector((0, 0, -1)), "hand": Vector((0, 0, -1))}
    for n, (axis, ref) in CARRY.items():
        R0 = B[f"{n}_l"].matrix_local.to_3x3()
        b_rest = _basis(R0 @ Vector((0, 1, 0)), rest_ref[n])
        b_new = _basis(axis, ref)
        Rw = b_new @ b_rest.inverted() @ R0          # world rotation of the posed bone
        out[n] = chest0.inverted() @ Rw
    return out


def apply_carry(arm, name, rel):
    sc = bpy.context.scene
    act = bpy.data.actions[name]
    arm.animation_data_create()
    arm.animation_data.action = act
    P = arm.pose.bones
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        chest = P["spine_03"].matrix.to_3x3()
        for n in ("upperarm", "lowerarm", "hand"):
            pb = P[f"{n}_l"]
            t = pb.matrix.translation.copy()
            pb.matrix = Matrix.Translation(t) @ (chest @ rel[n]).to_4x4()
            bpy.context.view_layer.update()
            pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
    arm.animation_data.action = None


def calm_arm(arm, name, ref_name, k=0.35, side="r"):
    """Blend the right arm's rotations k of the way toward the Idle arm (smaller gestures)."""
    act = bpy.data.actions[name]
    ref = bpy.data.actions[ref_name]
    L = ref.frame_range[1] - ref.frame_range[0]
    for bone in (f"clavicle_{side}", f"upperarm_{side}", f"lowerarm_{side}", f"hand_{side}"):
        fcs = {}
        for fc in iter_fcurves(act):
            if fc.data_path == f'pose.bones["{bone}"].rotation_quaternion':
                fcs[fc.array_index] = fc
        rfc = {}
        for fc in iter_fcurves(ref):
            if fc.data_path == f'pose.bones["{bone}"].rotation_quaternion':
                rfc[fc.array_index] = fc
        if len(fcs) < 4 or len(rfc) < 4:
            continue
        frames = sorted({kp.co.x for fc in fcs.values() for kp in fc.keyframe_points})
        vals = []
        for f in frames:
            q = Quaternion([fcs[i].evaluate(f) for i in range(4)])
            qr = Quaternion([rfc[i].evaluate(ref.frame_range[0]) for i in range(4)])
            if q.dot(qr) < 0:
                qr.negate()
            vals.append((f, q.slerp(qr, k)))
        for i in range(4):
            fc = fcs[i]
            fc.keyframe_points.clear()
            fc.keyframe_points.add(len(vals))
            for kp, (f, q) in zip(fc.keyframe_points, vals):
                kp.co = (f, q[i]); kp.interpolation = "LINEAR"


def adjust_stagger(arm, name, stagger=0.07):
    """The UAL idle stands with one foot ~27 cm ahead of the other (a man's stance): swing each
    leg about the hip's X axis so the ankles end `stagger` apart front-to-back (her left foot a
    little forward), feet keep their world orientation (flat), the small drop is taken out by
    the pelvis. Rotation-only per frame, so the feet stay planted."""
    sc = bpy.context.scene
    act = bpy.data.actions[name]
    arm.animation_data_create()
    arm.animation_data.action = act
    P = arm.pose.bones
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    frames = list(range(f0, f1 + 1))
    rec = []
    for f in frames:
        sc.frame_set(f)
        rec.append({n: P[n].matrix.copy() for n in ("thigh_l", "thigh_r", "foot_l", "foot_r")})
    yl = float(np.mean([r["foot_l"].translation.y for r in rec]))
    yr = float(np.mean([r["foot_r"].translation.y for r in rec]))
    m = 0.5 * (yl + yr)
    tgt = {"l": m - stagger / 2, "r": m + stagger / 2}
    X = Vector((1, 0, 0))

    def about(pivot, ang):
        return Matrix.Translation(pivot) @ Matrix.Rotation(ang, 4, X) @ Matrix.Translation(-pivot)
    rises = []
    for f, r in zip(frames, rec):
        sc.frame_set(f)
        for side in ("l", "r"):
            th0 = r[f"thigh_{side}"]; hip = th0.translation.copy()
            ank0 = r[f"foot_{side}"].translation.copy()
            lo_, hi_ = -0.7, 0.7
            for _ in range(40):
                mid = 0.5 * (lo_ + hi_)
                if (about(hip, mid) @ ank0).y < tgt[side]:
                    lo_ = mid
                else:
                    hi_ = mid
            R = about(hip, 0.5 * (lo_ + hi_))
            P[f"thigh_{side}"].matrix = R @ th0
            bpy.context.view_layer.update()
            newpos = P[f"foot_{side}"].matrix.translation.copy()
            rises.append(newpos.z - ank0.z)
            P[f"foot_{side}"].matrix = Matrix.Translation(newpos) @ r[f"foot_{side}"].to_3x3().to_4x4()
            bpy.context.view_layer.update()
            for n in (f"thigh_{side}", f"foot_{side}"):
                P[n].keyframe_insert("rotation_quaternion", frame=f, group=n)
                P[n].keyframe_insert("location", frame=f, group=n)
    rise = float(np.mean(rises))
    d_local = arm.data.bones["pelvis"].matrix_local.to_3x3().inverted() @ Vector((0, 0, -rise))
    for fc in iter_fcurves(act):
        if fc.data_path == 'pose.bones["pelvis"].location':
            for kp in fc.keyframe_points:
                for attr in ("co", "handle_left", "handle_right"):
                    vv = getattr(kp, attr); vv.y += d_local[fc.array_index]
    arm.animation_data.action = None
    print("CLIP", name, "stagger", round(yr - yl, 3), "->", stagger, "pelvis", round(-rise, 4),
          "rise spread mm", round((max(rises) - min(rises)) * 1000, 1))


def hold_fingers(src="Idle", dst=("Talk",), side="l"):
    """The basket hand keeps Idle's relaxed fingers in every clip (no Talk finger gestures over
    the basket)."""
    a = bpy.data.actions[src]
    fingers = [f"{f}_0{i}_{side}" for f in ("thumb", "index", "middle", "ring", "pinky") for i in (1, 2, 3)]
    for bone in fingers:
        path = f'pose.bones["{bone}"].rotation_quaternion'
        q = {fc.array_index: fc.evaluate(a.frame_range[0]) for fc in iter_fcurves(a) if fc.data_path == path}
        if len(q) < 4:
            continue
        for name in dst:
            act = bpy.data.actions[name]
            f0, f1 = act.frame_range
            for fc in iter_fcurves(act):
                if fc.data_path == path:
                    fc.keyframe_points.clear()
                    fc.keyframe_points.add(2)
                    for kp, f in zip(fc.keyframe_points, (f0, f1)):
                        kp.co = (f, q[fc.array_index]); kp.interpolation = "LINEAR"


def straighten_spine(arm, name, amounts=(("spine_01", 0.25), ("spine_02", 0.45), ("spine_03", 0.5),
                                          ("neck_01", 0.5))):
    """The UAL idle carries the chest back and the head well forward (a slouch); ease each
    spine/neck rotation part of the way back to the upright rest pose (rotation only)."""
    act = bpy.data.actions[name]
    for bone, k in amounts:
        fcs = {}
        for fc in iter_fcurves(act):
            if fc.data_path == f'pose.bones["{bone}"].rotation_quaternion':
                fcs[fc.array_index] = fc
        if len(fcs) < 4:
            continue
        frames = sorted({kp.co.x for fc in fcs.values() for kp in fc.keyframe_points})
        vals = [(f, Quaternion([fcs[i].evaluate(f) for i in range(4)]).slerp(Quaternion((1, 0, 0, 0)), k))
                for f in frames]
        for i in range(4):
            fc = fcs[i]
            fc.keyframe_points.clear()
            fc.keyframe_points.add(len(vals))
            for kp, (f, q) in zip(fc.keyframe_points, vals):
                kp.co = (f, q[i]); kp.interpolation = "LINEAR"


def build_clips_s(arm):
    src = {k: bpy.data.actions[k] for k in KEEP_CLIPS}
    for a in arm.pose.bones:
        a.rotation_mode = "QUATERNION"
    for sname, dname, frames in (("Idle_Talking_Loop", "Talk", 72), ("Walk_Formal_Loop", "Walk", 32)):
        a = src[sname]
        a.name = dname
        a.use_fake_user = True
        f0, f1 = a.frame_range
        k = frames / (f1 - f0)
        if abs(k - 1.0) > 1e-6:
            for fc in iter_fcurves(a):
                for kp in fc.keyframe_points:
                    for attr in ("co", "handle_left", "handle_right"):
                        v = getattr(kp, attr); v.x = f0 + (v.x - f0) * k
        a.use_frame_range = True
        a.frame_start, a.frame_end = f0, f0 + frames
    a = src["Idle_Loop"]
    a.name = "Idle_Loop_src"
    L = a.frame_range[1] - a.frame_range[0]
    slow = 1.2
    total = int(round(2 * L * slow))
    idle = new_action_like("Idle", arm)
    frames = []
    for f in range(0, total + 1):
        t = (f / slow) % L
        if f == total:
            t = 0.0
        pose = sample_action(a, arm, t)
        u = (f - total * 0.5) / (total * 0.5)
        if 0.0 <= u <= 1.0:            # glance to her right (away from the basket) and back
            w = math.sin(math.pi * u) ** 2
            for bone, ang in (("neck_01", -0.09), ("Head", -0.13), ("spine_03", -0.03)):
                if bone in pose and "rotation_quaternion" in pose[bone]:
                    q = pose[bone]["rotation_quaternion"]
                    qb = Quaternion((q.get(0, 1), q.get(1, 0), q.get(2, 0), q.get(3, 0)))
                    rest = arm.data.bones[bone].matrix_local.to_3x3()
                    ax = (rest.inverted() @ Vector((0, 0, 1))).normalized()
                    qn = qb @ Quaternion(ax, ang * w)
                    pose[bone]["rotation_quaternion"] = {0: qn.w, 1: qn.x, 2: qn.y, 3: qn.z}
        frames.append((f, pose))
    write_pose_keys(arm, idle, frames)
    idle.use_frame_range = True
    idle.frame_start, idle.frame_end = 0, total
    relax_fingers(arm)
    calm_arm(arm, "Talk", "Idle_Loop_src", k=0.35)
    bpy.data.actions.remove(a)
    for name, gaze in (("Idle", 1.0), ("Talk", 0.6)):
        straighten_spine(arm, name)
        adjust_stance_and_gaze(arm, name, ankle_sep=ANKLE_SEP, gaze_amount=gaze, toe_out_target=TOE_OUT)
        adjust_stagger(arm, name, STAGGER)
    rel = carry_rotations(arm)
    for name in ("Idle", "Talk"):
        apply_carry(arm, name, rel)
    hold_fingers(dst=("Talk",))
    # no Walk: the UAL stride swings the legs ~10 cm through a mid-calf skirt (she only stands)
    bpy.data.actions.remove(bpy.data.actions["Walk"])
    arm.animation_data_create()
    for tr in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(tr)
    for name in ("Idle", "Talk"):
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


def pose_at(arm, action, frame):
    arm.animation_data_create()
    arm.animation_data.action = bpy.data.actions[action] if action else None
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()


# ---------------------------------------------------------------------------------------------
# 4. clothes (built round her rest-pose body; Field / MB / offset_field from npc_pickell)
# ---------------------------------------------------------------------------------------------
MATS = ["SKIN", "HAIR", "EYE", "BLOUSE", "SKIRT", "SASH", "STOCKING", "SHOE", "STRAW", "RIBBON",
        "WICKER", "CLOTH", "BUTTON"]
ZS = dict(v_bot=1.262, neck_f=1.372, shoulder=1.335, blouse_lo=0.872, sash_lo=0.862, sash_hi=0.934,
          skirt_top=0.925, hem=0.272)


def smooth01(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class GarmentsS:
    def __init__(self, body_ob, arm):
        self.B = BodyData(body_ob)
        self.arm = arm
        B = self.B
        co = B.co
        z = co[:, 2]
        tor = B.ws(["pelvis", "spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r", "neck_01"])
        legs = B.ws(["thigh_l", "thigh_r"])
        armw = B.ws(["upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r", "hand_l", "hand_r"])
        headw = B.ws(["Head"])
        low = ((tor >= 0.5) | (legs >= 0.3)) & (armw < 0.35) & (z <= 1.10)
        # above 1.20 m only the trunk (|x| < 0.14): the blouse follows a natural sloping shoulder
        # and leaves the deltoid to the set-in sleeve (round 1: no man's square shoulders)
        high = (z > 1.10) & (np.abs(co[:, 0]) < np.where(z > 1.20, 0.14, 0.165)) & (z < 1.40)
        m = (low | high) & (headw < 0.3) & (np.abs(co[:, 0]) < 0.24)
        self.T = Field(co[m], s0=0.20, s1=1.42, ds=0.02, half=0.012, **TORSO_FRAME)
        neck = co[(B.ws(["neck_01", "Head"]) >= 0.5) & (z > 1.32) & (z < 1.47) & (armw < 0.05)
                  & (np.abs(co[:, 0]) < 0.065)]
        self.N = Field(neck, s0=1.33, s1=1.46, ds=0.01, half=0.008, **TORSO_FRAME)
        self.bones = {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in arm.data.bones}
        back = lambda phis: 0.5 - 0.5 * np.cos(phis)
        # blouse: eased over the bust, then hangs straight (the 1920 tube), never clings
        self.J = offset_field(self.T, lambda s, ph: 0.013 + 0.005 * back(ph), hang_from=1.17,
                              hang_rate=0.0012, smooth=8, floor=0.011)
        # skirt: eased over the hips, then a slight A-line flare down to the hem
        # (+1.6 cm over the front of the thighs below the hips: room for the forward leg)
        self.K = offset_field(self.T, lambda s, ph: 0.012 + 0.004 * back(ph)
                              + 0.016 * np.maximum(np.cos(ph), 0.0) ** 0.4 * smooth01((0.88 - s) / 0.08),
                              hang_from=0.80,
                              hang_rate=-0.0011, smooth=4, floor=0.010)
        mid = co[(np.abs(co[:, 0]) < 0.02) & (B.ws(["pelvis"]) >= 0.3)]
        self.crotch = float(mid[:, 2].min())
        print("GARMENTS crotch", round(self.crotch, 3))

    def centre_y(self, z):
        T = self.T
        return -T.centre(min(max(z, T.ss[0]), T.ss[-1]))[0]

    def ref_torso(self, extra=0.0):
        return lambda p: (0.0, self.centre_y(p.z) + extra, p.z - (0.10 if p.z > 1.28 else 0.0))

    # ---------------------------------------------------------------- blouse
    def zneck(self, p):
        pf = abs(((p + math.pi) % TAU) - math.pi)
        return ZS["neck_f"] + 0.034 * (pf / math.pi) ** 0.8

    def neckline(self, p, extra=0.0):
        return self.N.surf(self.zneck(p), p, 0.006 + extra)

    def x_open(self, z):
        if z < ZS["v_bot"]:
            return 0.0
        return lin([(ZS["v_bot"], 0.0), (1.30, 0.026), (ZS["shoulder"], 0.034), (1.40, 0.05)], z)

    def bl_surf(self, z, p, off=0.0):
        """Blouse surface: bloused J above 1.0 m, tucked under the sash below 0.95 m."""
        a = self.J.surf(z, p, off)
        if z >= 1.0:
            return a
        b = self.T.surf(z, p, 0.016 + off)
        return b.lerp(a, smooth01((z - 0.95) / 0.05))

    def phi_open(self, z, side):
        xo = self.x_open(z)
        if xo <= 1e-4:
            return 0.0 if side > 0 else TAU
        return solve_phi_for_x(self.J, z, xo, side)

    PN = math.radians(52)          # where the open neckline meets the neck (each side)

    def build_blouse(self, c):
        mb = MB("blouse")
        zs = (list(np.linspace(ZS["blouse_lo"], 0.95, 3)) + [0.975, 1.0] + list(np.linspace(1.04, 1.235, 7))
              + list(np.linspace(ZS["v_bot"], ZS["shoulder"], 6)))
        M = 36
        rows = []
        for z in zs:
            pl, pr = self.phi_open(z, 1), self.phi_open(z, -1)
            if pr <= pl:
                pr += TAU
            rows.append([self.bl_surf(z, p) for p in np.linspace(pl, pr, M)])
        neck_row = [self.neckline(p) for p in np.linspace(self.PN, TAU - self.PN, M)]
        for t in (0.4, 0.75):
            mid = []
            for a_, b_ in zip(rows[-1], neck_row):
                q = a_.lerp(b_, t)
                q.z += 0.008 * math.sin(math.pi * t)
                mid.append(q)
            rows.append(mid)
        rows.append(neck_row)
        mb.grid(rows, "BLOUSE")
        # the opening edge (left column up from the V point, the neckline round the back, the
        # right column down) - the collar follows it exactly
        i_v = next(i for i, z in enumerate(zs) if z >= ZS["v_bot"] - 1e-6)
        self.open_edge = ([r[0] for r in rows[i_v:]] + neck_row[1:-1]
                          + [r[-1] for r in reversed(rows[i_v:])])
        # button placket and five small pearl buttons down the closed front
        zp = list(np.linspace(0.945, ZS["v_bot"] - 0.004, 7))
        pk = []
        for z in zp:
            pk.append([self.bl_surf(z, -0.075 % TAU, 0.0012), self.bl_surf(z, 0.0, 0.0022),
                       self.bl_surf(z, 0.075, 0.0012)])
        mb.grid(pk, "BLOUSE")
        for z in np.linspace(ZS["v_bot"] - 0.03, 0.975, 5):
            p = self.bl_surf(z, 0.0, 0.0024)
            n = (p - Vector((0.0, self.centre_y(z), z))).normalized()
            mb.disc(p, n, 0.0052, "BUTTON", n=6, depth=0.0018)
        return mb.build(c, orient=self.ref_torso())

    def build_collar(self, c, blouse):
        """Flat turn-down collar lying on the blouse along its whole opening edge: up the left
        side of the V, round the back of the neck, down the right side (one continuous strip,
        so no notches open at the shoulders). Width 0.6 cm at the V point, 5 cm on the shoulders
        and at the back (a 1920 shirtwaist / middy collar)."""
        from mathutils.bvhtree import BVHTree
        mb = MB("collar")
        bt = BVHTree.FromObject(blouse, bpy.context.evaluated_depsgraph_get())

        def snap(q, off):
            loc, n, i, d = bt.find_nearest(q)
            return (loc + n * off, n) if loc is not None else (q, Vector((0, 0, 1)))
        E = resample([tuple(p) for p in self.open_edge], 60)
        E = [Vector(tuple(p)) for p in E]
        inner, mid, outer = [], [], []
        # "away from the opening" direction in the cloth surface, made continuous along the strip
        # starting from the back of the neck (where it plainly points down the back)
        O = []
        for k, p in enumerate(E):
            t = (E[min(k + 1, len(E) - 1)] - E[max(k - 1, 0)]).normalized()
            q, n = snap(p, 0.0)
            O.append(n.cross(t).normalized())
        kb = max(range(len(E)), key=lambda k: E[k].y)
        if O[kb].z > 0:
            O[kb] = -O[kb]
        for rng in (range(kb + 1, len(E)), range(kb - 1, -1, -1)):
            prev = kb
            for k in rng:
                if O[k].dot(O[prev]) < 0:
                    O[k] = -O[k]
                prev = k
        for _ in range(3):                             # soften the turn at the neck corners
            O = [(O[max(k - 1, 0)] + 2 * O[k] + O[min(k + 1, len(O) - 1)]).normalized() for k in range(len(O))]
        for k, p in enumerate(E):
            o = O[k]
            w = lin([(ZS["v_bot"], 0.006), (ZS["v_bot"] + 0.025, 0.030), (ZS["shoulder"], 0.048), (1.45, 0.052)], p.z)
            back = p.z > ZS["shoulder"] + 0.02
            a_, n_ = snap(p, 0.0)
            a_ = a_ + n_ * 0.0045 - o * 0.004             # 4 mm past the blouse edge: no cloth teeth
            if back:                                   # a small stand round the back of the neck
                a_ = a_ + Vector((0, 0, 0.006))
            b_, _ = snap(p + o * w, 0.0055)
            m_, _ = snap(p + o * w * 0.35, 0.0080)
            inner.append(a_); mid.append(m_); outer.append(b_)
        # round 1: one clean line - smooth each row along the strip (snapping to the coarse
        # blouse left mm-size saw-teeth), then lift any point that sank to within 4 mm of the blouse
        def smooth_row(R_, passes=5):
            R_ = [q.copy() for q in R_]
            for _ in range(passes):
                R_ = [R_[0]] + [R_[k - 1] * 0.25 + R_[k] * 0.5 + R_[k + 1] * 0.25 for k in range(1, len(R_) - 1)] + [R_[-1]]
            return R_
        inner, mid, outer = smooth_row(inner, 3), smooth_row(mid), smooth_row(outer)
        for R_, off in ((mid, 0.006), (outer, 0.0045)):
            for k, q in enumerate(R_):
                loc, n, i, d = bt.find_nearest(q)
                if loc is not None and (q - loc).dot(n) < off:
                    R_[k] = q + n * (off - (q - loc).dot(n))
        mb.grid([inner, mid, outer], "BLOUSE")
        return mb.build(c, orient=lambda p: (0.0, self.centre_y(min(p.z, 1.40)), p.z - 0.10))

    # ---------------------------------------------------------------- sleeves with cuffs
    def build_sleeves(self, c, blouse=None):
        mb = MB("sleeves")
        cmb = MB("capfill")
        B = self.B; co = B.co
        for side, sg in (("l", 1), ("r", -1)):
            sh = self.bones[f"upperarm_{side}"][0]
            wr = self.bones[f"hand_{side}"][0]
            w = B.ws([f"upperarm_{side}", f"lowerarm_{side}", f"hand_{side}"])
            m = (w >= 0.5) & (co[:, 0] * sg > abs(sh.x) - 0.04) & (co[:, 0] * sg < abs(wr.x) + 0.005)
            m &= np.hypot(co[:, 1] - sh.y, co[:, 2] - sh.z) < 0.068
            F = Field(co[m], o=tuple(sh), a=(sg, 0, 0), e1=(0, 0, 1), e2=(0, -sg, 0),
                      s0=-0.04, s1=abs(wr.x - sh.x) + 0.005, ds=0.015, half=0.01, K=48)
            L = abs(wr.x - sh.x)
            K = 14
            phis = np.linspace(0, TAU, K, endpoint=False)
            s_cuff = L - 0.052
            ss = [-0.06, -0.03, 0.0, 0.03, 0.08] + list(np.linspace(0.12, s_cuff - 0.012, 8))

            def rad(s, p):
                r_min = lin([(-0.045, 0.046), (0.03, 0.049), (0.2, 0.045), (s_cuff, 0.041)], s)
                # plain set-in sleeve: a smooth cap with little ease (no puff), fuller lower down
                ease = lin([(-0.06, 0.007), (0.0, 0.009), (0.08, 0.014), (0.5 * L, 0.020), (s_cuff, 0.024)], s)
                r = max(F.radius(s, p) + ease, r_min * lin([(-0.06, 0.8), (0.05, 1.0)], s))
                r *= lin([(-0.06, 0.6), (-0.025, 0.88), (0.015, 1.0)], s)
                # set-in cap: flatter on top near the shoulder point, so the dropped arm's sleeve
                # does not ride up into a hump above the shoulder line
                # and slimmer all round there (the dropped arm folds the underarm/back of a T-pose
                # sleeve outward behind the shoulder otherwise)
                return r * (1.0 - lin([(-0.06, 0.32), (0.0, 0.24), (0.11, 0.0)], s)
                            * (0.55 + 0.45 * max(math.cos(p), 0.0) ** 1.5))
            rows = [[F.point(s, p, rad(s, p)) for p in phis] for s in ss]
            if blouse is not None:
                # round 1: the cap rows stay 4 mm inside the bodice (no cap edge showing at the seam)
                from mathutils.bvhtree import BVHTree
                bt = BVHTree.FromObject(blouse, bpy.context.evaluated_depsgraph_get())
                for j, s_ in enumerate(ss):
                    if s_ > 0.03:
                        continue
                    for k, q in enumerate(rows[j]):
                        ctr = F.point(s_, phis[k], 0.0)
                        d = q - ctr
                        L_ = d.length
                        h = bt.ray_cast(ctr, d.normalized(), L_ + 0.02)
                        if h[0] is not None and (h[0] - ctr).length - 0.004 < L_:
                            rows[j][k] = ctr + d.normalized() * max(0.01, (h[0] - ctr).length - 0.004)
            cuff_r = lambda s, p, d: F.radius(s, p) + d
            for s, d in ((s_cuff - 0.004, 0.0085), (s_cuff + 0.002, 0.0075), (L - 0.004, 0.0072),
                         (L - 0.001, 0.0060), (L - 0.0015, 0.0012)):     # flat end ring, no dark inner band
                rows.append([F.point(s, p, cuff_r(s, p, d)) for p in phis])
            mb.grid(rows, "BLOUSE", closed=True)
            # round 1: the cap end is closed (own part, AO white in the bake), so where the dropped
            # arm brings it out behind the shoulder you see cloth, never the dark inside of the tube
            cf0 = cmb.grid([rows[0], [r_.lerp(F.point(ss[0], 0.0, 0.0), 0.5) for r_ in rows[0]]], "BLOUSE", closed=True)
            cmb.fan(list(range(cf0 + K, cf0 + 2 * K)), F.point(ss[0], 0.0, 0.0), "BLOUSE")
            for k in range(2):        # two cuff buttons on the outer side
                s = L - 0.016 - k * 0.018
                p = math.radians(205)
                q = F.point(s, p, cuff_r(s, p, 0.0080))
                nrm = (q - F.point(s, p, 0.0)).normalized()
                mb.disc(q, nrm, 0.0040, "BUTTON", n=6, depth=0.0014)
        ax = self.bones["upperarm_l"][0]          # interior reference ON the arm axis (round 1: the
        sl_ = mb.build(c, orient=lambda p: (p.x, ax.y, ax.z))   # slim cap faces were flipped inward)
        self.capfill = cmb.build(c)
        return sl_

    # ---------------------------------------------------------------- skirt, sash, bow
    def skirt_r(self, z, p):
        amp = 0.0075 * smooth01((0.80 - z) / 0.45)
        fold = (0.55 * math.sin(9 * p + 0.4) + 0.30 * math.sin(15 * p + 1.7) + 0.15 * math.sin(23 * p + 0.3))
        return self.K.radius(z, p) + amp * fold

    def skirt_pt(self, z, p, off=0.0):
        return self.K.point(z, p, self.skirt_r(z, p) + off)

    def build_skirt(self, c):
        mb = MB("skirt")
        Kn = 56
        phis = np.linspace(0, TAU, Kn, endpoint=False)
        hem_z = lambda p: ZS["hem"] + 0.005 * math.sin(3 * p + 0.5) + 0.004 * (0.5 + 0.5 * math.cos(p))
        zs = sorted(list(np.linspace(0.735, 0.30, 10)) + [0.78, 0.82, 0.86, 0.895, ZS["skirt_top"]])
        rows = [[self.skirt_pt(hem_z(p), p) for p in phis]]
        for z in zs:
            if z > 0.86:          # under the sash: snug on the hips
                rows.append([self.T.surf(z, p, 0.011) for p in phis])
            else:
                rows.append([self.skirt_pt(z, p) for p in phis])
        hem_in = [self.skirt_pt(hem_z(p) + 0.014, p, -0.005) for p in phis]
        mb.grid([hem_in] + rows, "SKIRT", closed=True)
        # the sash's hanging tails, lying on the skirt at her right front hip
        for dp, ln, w0 in ((-0.10, 0.215, 0.038), (0.06, 0.185, 0.034)):
            p0 = (math.radians(-62) + dp) % TAU
            zt = ZS["sash_lo"] + 0.012
            rows_t = []
            for k in range(7):
                u = k / 6
                z = zt - ln * u
                p = (p0 + dp * 0.4 * u) % TAU
                r = self.skirt_r(z, p) + 0.006 + 0.003 * u
                hw = (w0 * (1 + 0.15 * u)) / max(r, 0.1) / 2
                a_ = self.K.point(z, p - hw, self.skirt_r(z, p - hw) + 0.006 + 0.003 * u)
                b_ = self.K.point(z, p + hw, self.skirt_r(z, p + hw) + 0.006 + 0.003 * u)
                if k == 6:              # V-cut end
                    a_.z += 0.012; b_.z += 0.012
                rows_t.append([a_, a_.lerp(b_, 0.5), b_])
            mb.grid(rows_t, "SASH")
        return mb.build(c, orient=lambda p: (0.0, self.centre_y(max(p.z, 0.30)), p.z))

    def build_sash(self, c):
        mb = MB("sash")
        Kn = 56
        phis = np.linspace(0, TAU, Kn, endpoint=False)
        lo, hi = ZS["sash_lo"], ZS["sash_hi"]
        rows = [[self.T.surf(z, p, d) for p in phis]
                for z, d in ((lo - 0.002, 0.016), (lo + 0.006, 0.0215), (hi - 0.006, 0.0215), (hi + 0.002, 0.016))]
        mb.grid(rows, "SASH", closed=True)
        # bow at her right front hip: knot + two flat loops
        p0 = math.radians(-62) % TAU
        zc = 0.5 * (lo + hi)
        ctr = self.T.surf(zc, p0, 0.0245)
        nrm = (ctr - Vector((0.0, self.centre_y(zc), zc))); nrm.z = 0.0; nrm.normalize()
        tan = Vector((0, 0, 1)).cross(nrm).normalized()
        up = Vector((0, 0, 1))
        hk, hz = 0.016, 0.019
        knot = [ctr + nrm * 0.008 + tan * sx * hk + up * sz * hz for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        kb = [p - nrm * 0.010 for p in knot]
        mb.poly(knot, "SASH")
        for i in range(4):
            j = (i + 1) % 4
            mb.poly([kb[i], kb[j], knot[j], knot[i]], "SASH")
        for sgn in (1, -1):
            path = []
            for th in np.linspace(0.0, TAU, 13):
                a = 0.080 * (1 - math.cos(th)) / 2
                b = 0.013 * math.sin(th)
                path.append(ctr + nrm * (0.010 + abs(b) * 0.9) + tan * sgn * (0.012 + a * 0.85)
                            + up * (0.006 * math.sin(th) + 0.004 * sgn * (a / 0.08)))
            rows_b = [[p + up * (0.020 * (1 - 0.25 * abs(math.sin(k * TAU / 24)))) * s_ for s_ in (-1, 1)]
                      for k, p in enumerate(path)]
            mb.grid(rows_b, "SASH")
        return mb.build(c, orient=lambda p: (0.0, self.centre_y(p.z), p.z))

    # ---------------------------------------------------------------- shoes (laced, low Louis heel)
    def build_shoes(self, c):
        B = self.B; co = B.co
        mb = MB("shoes")
        HEEL = 0.024
        for side, sg in (("l", 1), ("r", -1)):
            fw = B.ws([f"foot_{side}", f"ball_{side}"])
            fm = (fw >= 0.4) & (co[:, 0] * sg > 0.0) & (co[:, 2] < 0.09)
            F_ = co[fm]
            heel_y = float(F_[:, 1].max()) + 0.007
            toe_y = float(F_[:, 1].min()) - 0.014
            Ls = heel_y - toe_y
            heel_x = float(np.mean(F_[F_[:, 1] > heel_y - 0.05][:, 0]))
            toe_x = float(np.mean(F_[F_[:, 1] < toe_y + 0.06][:, 0]))
            z0 = max(0.0, float(F_[:, 2].min()))          # soles on the ground (the foot inside is not kept)
            prof = [(0.0, 0.017, 0.058), (0.03, 0.024, 0.064), (0.12, 0.028, 0.070), (0.28, 0.030, 0.074),
                    (0.42, 0.033, 0.064), (0.55, 0.037, 0.054), (0.68, 0.040, 0.045), (0.80, 0.037, 0.038),
                    (0.89, 0.030, 0.031), (0.95, 0.021, 0.025), (0.985, 0.010, 0.019), (1.0, 0.003, 0.015)]
            srows = []
            for u, hw, hh in prof:
                y = heel_y - u * Ls
                xc = heel_x + (toe_x - heel_x) * u - sg * 0.008 * max(0.0, (u - 0.5) / 0.5)
                lift = z0 + HEEL * smooth01((0.62 - u) / 0.42) + 0.007 * max(0.0, (u - 0.75) / 0.25) ** 1.6
                row = [Vector((xc + sg * (hw + 0.0025), y, lift)), Vector((xc + sg * (hw + 0.0025), y, lift + 0.008))]
                for th in np.linspace(0.0, math.pi, 9):
                    ex = math.cos(th); ez = math.sin(th) ** 0.85
                    row.append(Vector((xc + sg * hw * ex, y, lift + 0.009 + (hh - 0.009) * ez)))
                row += [Vector((xc - sg * (hw + 0.0025), y, lift + 0.008)), Vector((xc - sg * (hw + 0.0025), y, lift)),
                        Vector((xc, y, lift))]
                srows.append(row)
            base = mb.grid(srows, "SHOE", closed=True)
            n = len(srows[0])
            first = list(range(base, base + n))
            last = list(range(base + (len(srows) - 1) * n, base + len(srows) * n))
            cb = Vector(np.mean([np.array(p) for p in srows[0]], 0)); cb.y += 0.005
            ct = Vector(np.mean([np.array(p) for p in srows[-1]], 0)); ct.y -= 0.003
            mb.fan(first, cb, "SHOE")
            mb.fan(last, ct, "SHOE")
            # Louis heel: a waisted block under the heel
            hrows = []
            for u, hw_top, hw_bot in ((0.015, 0.016, 0.013), (0.09, 0.017, 0.011), (0.17, 0.016, 0.012)):
                y = heel_y - u * Ls
                xc = heel_x
                top = z0 + HEEL * smooth01((0.62 - u) / 0.42) + 0.001
                hrows.append([Vector((xc + sg * hw_bot, y, z0)), Vector((xc + sg * hw_top * 0.8, y, z0 + 0.6 * (top - z0))),
                              Vector((xc + sg * hw_top, y, top)), Vector((xc - sg * hw_top, y, top)),
                              Vector((xc - sg * hw_top * 0.8, y, z0 + 0.6 * (top - z0))), Vector((xc - sg * hw_bot, y, z0))])
            hb = mb.grid(hrows, "SHOE", closed=True)
            mb.fan(list(range(hb, hb + 6)), Vector(np.mean([np.array(p) for p in hrows[0]], 0)) + Vector((0, 0.002, 0)), "SHOE")
            mb.fan(list(range(hb + 12, hb + 18)), Vector(np.mean([np.array(p) for p in hrows[-1]], 0)) - Vector((0, 0.002, 0)), "SHOE")
        fl, fr = self.bones["foot_l"][0].x, self.bones["foot_r"][0].x
        return mb.build(c, orient=lambda p: ((fl if p.x > 0 else fr), -0.035, 0.035))


# ---------------------------------------------------------------------------------------------
# 5. head, neck + V, hands, stockinged legs, pinned-up hair with a bun, straw hat
# ---------------------------------------------------------------------------------------------
HEAD_TRIS = 2800
HAND_TRIS = 1600
HAIR_TRIS = 520
LEG_TRIS = 520
HEAD_C = Vector((0.0, -0.05, 1.53))
HAIRLINE = [(0, 1.578), (15, 1.576), (30, 1.568), (45, 1.552), (58, 1.532), (68, 1.515), (76, 1.505),
            (80, 1.517), (100, 1.517), (106, 1.497), (115, 1.480), (130, 1.463), (150, 1.451),
            (165, 1.447), (180, 1.446)]
HAT = dict(z_band=1.566, tip=0.005, brim=0.118, crown_h=0.098, axis_y=-0.048)   # round 1: 9 mm higher


def hat_band_z(p):
    return HAT["z_band"] - HAT["tip"] * math.cos(p)          # tipped a touch forward


def hat_phi(p):
    return math.atan2(p[0], -(p[1] - HAT["axis_y"]))


BRIM_DROOP = [(0.0, 0.0), (0.035, 0.005), (0.075, 0.013), (0.118, 0.025), (0.3, 0.027)]


def build_hat(c, hair, head, *extra):
    """Wide-brimmed straw hat: lathe crown + brim (upper and under surface, rolled edge), ribbon
    band with a flat bow at her left side-back. Rigid on the Head bone."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    trees = [BVHTree.FromObject(o, dg) for o in (hair, head) + extra]
    K = 36
    phis = np.linspace(0, TAU, K, endpoint=False)
    ax_y = HAT["axis_y"]
    rr = []
    for p in phis:
        d = Vector((math.sin(p), -math.cos(p), 0.0))
        best = 0.0
        for zz, k_ in ((hat_band_z(p), 1.0), (hat_band_z(p) + 0.03, 0.98), (hat_band_z(p) + 0.06, 0.96)):
            o = Vector((0.0, ax_y, zz))
            for t in trees:
                h = t.ray_cast(o + d * 0.2, -d, 0.2)
                if h[0] is not None:
                    best = max(best, (h[0] - o).length * k_)
        rr.append(best + 0.005)
    rr = np.array(rr)
    rr = 0.25 * np.roll(rr, 1) + 0.5 * rr + 0.25 * np.roll(rr, -1)
    mb = MB("hat")
    dfac = lambda p: 0.55 + 0.45 * abs(math.cos(p))          # brim dips more front and back

    def ring(scale, dz, extra=0.0, droop=0.0):
        out = []
        for k, p in enumerate(phis):
            d = Vector((math.sin(p), -math.cos(p), 0.0))
            out.append(Vector((0.0, ax_y, hat_band_z(p) + dz - droop * dfac(p))) + d * (rr[k] * scale + extra))
        return out
    H = HAT["crown_h"]
    crown = [ring(1.0, 0.0), ring(1.03, 0.025), ring(1.04, 0.05), ring(1.0, 0.072), ring(0.88, 0.086),
             ring(0.62, H - 0.003), ring(0.30, H)]
    b0 = mb.grid(crown, "STRAW", closed=True)
    top_c = Vector((0.0, ax_y, HAT["z_band"] + H + 0.004))
    mb.fan(list(range(b0 + 6 * K, b0 + 7 * K)), top_c, "STRAW")
    W = HAT["brim"]
    dr = lambda e: lin(BRIM_DROOP, e)
    brim = [ring(1.0, 0.0, 0.002), ring(1.0, -0.002, 0.035, dr(0.035)), ring(1.0, -0.002, 0.075, dr(0.075)),
            ring(1.0, -0.001, W, dr(W)), ring(1.0, -0.0035, W + 0.0025, dr(W)),
            ring(1.0, -0.006, W - 0.004, dr(W - 0.004)), ring(1.0, -0.006, 0.075, dr(0.075)),
            ring(1.0, -0.006, 0.035, dr(0.035)), ring(1.0, -0.005, 0.002)]
    mb.grid(brim, "STRAW", closed=True)
    rib = [ring(1.0, 0.003, 0.0045), ring(1.016, 0.016, 0.005), ring(1.02, 0.031, 0.0045)]
    mb.grid(rib, "RIBBON", closed=True)
    # flat bow on the band, her left side towards the back
    p0 = math.radians(115)
    d = Vector((math.sin(p0), -math.cos(p0), 0.0))
    tan = Vector((0, 0, 1)).cross(d).normalized()
    k0 = int(round(p0 / TAU * K)) % K
    ctr = Vector((0.0, ax_y, hat_band_z(p0) + 0.017)) + d * (rr[k0] * 1.016 + 0.007)
    for sgn in (1, -1):
        path = []
        for th in np.linspace(0.0, TAU, 11):
            a = 0.030 * (1 - math.cos(th)) / 2
            path.append(ctr + d * (0.004 * abs(math.sin(th)) + 0.002) + tan * sgn * (0.008 + a)
                        + Vector((0, 0, 0.004 * math.sin(th))))
        mb.grid([[p + Vector((0, 0, s_ * 0.012)) for s_ in (-1, 1)] for p in path], "RIBBON")
    kn = [ctr + d * 0.005 + tan * sx * 0.008 + Vector((0, 0, sz * 0.011)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    mb.poly(kn, "RIBBON")

    def orient(c_):
        p = hat_phi(c_)
        k = int(round((p % TAU) / TAU * K)) % K
        rad = math.hypot(c_.x, c_.y - ax_y)
        rel = rad - rr[k]
        if rel > 0.012 and c_.z < hat_band_z(p) + 0.004:          # brim: inside = its mid-plane
            mz = hat_band_z(p) - 0.0035 - lin(BRIM_DROOP, rel) * dfac(p)
            return (c_.x, c_.y, mz)
        return (0.0, ax_y, min(c_.z, HAT["z_band"] + H - 0.03))
    ob = mb.build(c, orient=orient)
    print("HAT band radius", round(float(rr.min()), 3), round(float(rr.max()), 3))
    return ob


def build_bun(c):
    mb = MB("bun")
    cz, cy = 1.497, 0.046
    rx, ry, rz = 0.037, 0.024, 0.027
    rows = []
    for th in np.linspace(0.15, math.pi - 0.15, 7):
        rows.append([Vector((rx * math.sin(th) * math.cos(f), cy + ry * math.sin(th) * math.sin(f) + 0.004 * math.sin(th),
                             cz + rz * math.cos(th))) for f in np.linspace(0, TAU, 12, endpoint=False)])
    b0 = mb.grid(rows, "HAIR", closed=True)
    mb.fan(list(range(b0, b0 + 12)), Vector((0, cy, cz + rz)), "HAIR", flip=True)
    mb.fan(list(range(b0 + 6 * 12, b0 + 7 * 12)), Vector((0, cy, cz - rz)), "HAIR")
    return mb.build(c, orient=lambda p: (0.0, cy, cz))


HAIR_LOW = [(0, 1.548), (20, 1.545), (35, 1.534), (50, 1.516), (65, 1.500), (80, 1.488), (100, 1.484),
            (120, 1.476), (145, 1.462), (180, 1.455)]            # lower edge of the hair by azimuth
HAIR_FULL = [(0, 0.006), (30, 0.009), (55, 0.015), (90, 0.019), (130, 0.014), (180, 0.011)]


def build_hair_volume(c, body, shell):
    """Round 1: soft, full 1920 hair worn low - a band of hair all round under the brim: a light
    wave over the forehead, full over the temples and the tops of the ears, swept back into the
    nape bun. Lofted round the head (radius = outermost skin/ear/hair-shell surface + fullness),
    with a rounded lower edge tucked onto the skin."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    trees = [BVHTree.FromObject(body, dg), BVHTree.FromObject(shell, dg)]
    ax_y = HAT["axis_y"]
    K = 48
    phis = np.linspace(0, TAU, K, endpoint=False)
    us = [0.0, 0.3, 0.55, 0.78, 0.92, 1.0]

    def surf_r(p, z):
        d = Vector((math.sin(p), -math.cos(p), 0.0))
        o = Vector((0.0, ax_y, z))
        best = None
        for t in trees:
            h = t.ray_cast(o + d * 0.25, -d, 0.25)
            if h[0] is not None:
                r = (h[0] - o).length
                best = r if best is None else max(best, r)
        return best if best is not None else 0.08
    zt = np.array([[hat_band_z(p) + 0.012] for p in phis])[:, 0]
    zb = np.array([lin(HAIR_LOW, abs(math.degrees(((p + math.pi) % TAU) - math.pi))) for p in phis])
    rows_z = [[zt[k] + (zb[k] - zt[k]) * u for k in range(K)] for u in us]
    RS = np.array([[surf_r(phis[k], rows_z[j][k]) for k in range(K)] for j in range(len(us))])
    RSs = RS.copy()
    for _ in range(3):                                   # soft over the ear bumps, never inside
        RSs = 0.25 * np.roll(RSs, 1, 1) + 0.5 * RSs + 0.25 * np.roll(RSs, -1, 1)
        RSs[1:-1] = 0.25 * RSs[:-2] + 0.5 * RSs[1:-1] + 0.25 * RSs[2:]
        RSs = np.maximum(RSs, RS)
    full = np.array([lin(HAIR_FULL, abs(math.degrees(((p + math.pi) % TAU) - math.pi))) for p in phis])
    mb = MB("hairvol")
    rows = []
    for j, u in enumerate(us):
        puff = 0.8 + 0.35 * math.sin(math.pi * min(1.0, u / 0.85))
        if u >= 1.0:
            puff = 0.75
        rows.append([Vector((0.0, ax_y, rows_z[j][k])) + Vector((math.sin(phis[k]), -math.cos(phis[k]), 0.0))
                     * (RSs[j, k] + full[k] * puff) for k in range(K)])
    # rounded lower edge: down a little and in onto the skin
    tuck = []
    for k in range(K):
        z = zb[k] + 0.004
        tuck.append(Vector((0.0, ax_y, z)) + Vector((math.sin(phis[k]), -math.cos(phis[k]), 0.0))
                    * (surf_r(phis[k], z) + 0.0005))
    rows.append(tuck)
    mb.grid(rows, "HAIR", closed=True)
    ob = mb.build(c, orient=lambda q: (0.0, ax_y, q.z))
    return ob


def stage_skin_s(src, garments):
    from mathutils.bvhtree import BVHTree
    work = bpy.data.collections[WORK]
    main = bpy.data.collections[COLL]
    body = src["Body"]
    B = garments.B
    co = B.co
    # ---- hair shell off the scalp, above the hairline; full at the sides, centre parting
    above_v = np.array([p[2] > z_hair(az_of(p)) for p in co]) & (co[:, 2] > 1.42)
    above_v &= B.ws(["ears"]) < 0.3
    vm = np.zeros(len(co), bool)
    for poly in body.data.polygons:
        if sum(above_v[i] for i in poly.vertices) >= 2 and co[poly.vertices[0], 2] > 1.42:
            for i in poly.vertices:
                vm[i] = True
    hair = keep_faces(body, "PART_hair", vm, main)
    hm = hair.data
    bm_ = bmesh.new(); bm_.from_mesh(hm)
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
    for v in hm.vertices:
        p = v.co.copy()
        n = nrm[v.index]
        az = az_of(p)
        t = 0.0085 + 0.0065 * math.exp(-((az - 88) / 26) ** 2) * smooth01((1.575 - p.z) / 0.04)
        t += 0.002 * smooth01((az - 120) / 40)                     # swept up toward the bun
        above = p.z - z_hair(az)
        t = 0.0015 + (t - 0.0015) * min(1.0, max(0.0, above / 0.011)) ** 0.55
        if v.index in bnd:
            t = 0.0010
        if p.y < -0.06 and abs(p.x) < 0.012:                       # centre parting
            t -= 0.0030 * math.exp(-(p.x / 0.0045) ** 2) * smooth01((p.z - 1.585) / 0.01)
        v.co = p + n * max(t, 0.0010)
    hm.update()
    # hair wholly under the hat crown is never seen
    bm_ = bmesh.new(); bm_.from_mesh(hm)
    kill = [f for f in bm_.faces if all(v.co.z > hat_band_z(hat_phi(v.co)) + 0.018 for v in f.verts)]
    bmesh.ops.delete(bm_, geom=kill, context="FACES")
    bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if not v.link_faces], context="VERTS")
    bm_.to_mesh(hm); bm_.free()
    decimate_to(hair, HAIR_TRIS)
    # ---- head + neck + the V of the blouse (high-res bake source, low-res part)
    # face + chin (her chin is at 1.40 m), the neck column above the blouse, and the skin of the V
    # opening (3 cm beyond its edge, under the blouse and collar)
    neck_r = np.hypot(co[:, 0] / 0.062, (co[:, 1] + 0.012) / 0.068)
    xo = np.array([garments.x_open(max(z, ZS["v_bot"] + 1e-4)) for z in co[:, 2]])
    vreg = ((co[:, 2] > ZS["v_bot"] - 0.03) & (co[:, 2] < 1.40) & (co[:, 1] < -0.035)
            & (np.abs(co[:, 0]) < xo + 0.030))
    head_mask = ((co[:, 2] > 1.345) & (np.abs(co[:, 0]) < 0.105) & ((co[:, 2] > 1.395) | (neck_r < 1.0))) | vreg
    head_mask &= B.ws(["upperarm_l", "upperarm_r"]) < 0.2
    hi = keep_faces(body, "HI_head", head_mask, work)
    at = hi.data.attributes.new("hairzone", "FLOAT", "POINT")
    at.data.foreach_set("value", [min(1.0, max(0.0, (v.co.z - z_hair(az_of(v.co)) + 0.003) / 0.006))
                                  for v in hi.data.vertices])
    hbvh = BVHTree.FromObject(hair, bpy.context.evaluated_depsgraph_get())
    lo = keep_faces(hi, "PART_head", np.ones(len(hi.data.vertices), bool), main)
    bm_ = bmesh.new(); bm_.from_mesh(lo.data)
    covered = set()
    for v in bm_.verts:
        if v.co.z - z_hair(az_of(v.co)) < 0.008:
            continue
        under_hat = v.co.z > hat_band_z(hat_phi(v.co)) + 0.012
        loc, nrm_, idx, d = hbvh.find_nearest(v.co)
        if under_hat or (loc is not None and d < 0.02 and (loc - v.co).dot(v.normal) > 0
                         and hbvh.ray_cast(v.co + v.normal * 0.0005, v.normal, 0.03)[0] is not None):
            covered.add(v.index)
    kill = [f for f in bm_.faces if all(v.index in covered for v in f.verts)]
    bmesh.ops.delete(bm_, geom=kill, context="FACES")
    bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if not v.link_faces], context="VERTS")
    bm_.to_mesh(lo.data); bm_.free()
    decimate_to(lo, HEAD_TRIS)
    bm_ = bmesh.new(); bm_.from_mesh(lo.data); bm_.normal_update()
    for v in bm_.verts:                       # scalp sunk under the hair edge (no skin poking)
        t = min(1.0, max(0.0, (v.co.z - z_hair(az_of(v.co)) + 0.002) / 0.004))
        if t > 0:
            v.co -= v.normal * 0.0025 * t
    bm_.to_mesh(lo.data); bm_.free()
    # neck/chest skin that pokes through (or lies within 4 mm under) the blouse or collar goes
    # 4 mm under the cloth (the blouse's shoulder rows are interpolated and can dip into the skin)
    cloth_t = [BVHTree.FromObject(bpy.data.objects[n], bpy.context.evaluated_depsgraph_get())
               for n in ("PART_blouse", "PART_collar") if n in bpy.data.objects]
    bm_ = bmesh.new(); bm_.from_mesh(lo.data); bm_.normal_update()
    pushed = 0
    for v in bm_.verts:
        if v.co.z > 1.42:
            continue
        n = v.normal
        best = None
        for t in cloth_t:
            h_out = t.ray_cast(v.co - n * 0.02, n, 0.026)          # cloth from 2 cm inside to 6 mm out
            if h_out[0] is not None:
                dd = (h_out[0] - v.co).dot(n)                    # >0: cloth above the skin
                if best is None or dd < best[1]:
                    best = (h_out[0], dd)
        if best is not None and best[1] < 0.004:
            v.co = best[0] - n * 0.004
            pushed += 1
    bm_.to_mesh(lo.data); bm_.free()
    print("SKIN pushed under the blouse", pushed)
    at2 = lo.data.attributes.new("hairdist", "FLOAT", "POINT")
    at2.data.foreach_set("value", [v.co.z - z_hair(az_of(v.co)) for v in lo.data.vertices])
    # ---- hands (wrist inside the cuff)
    hand_x = abs(garments.bones["hand_l"][0].x) - 0.035
    hmask = np.abs(co[:, 0]) > hand_x
    hands_hi = keep_faces(body, "HI_hands", hmask, work)
    hands = keep_faces(body, "PART_hands", hmask, main)
    decimate_to(hands, HAND_TRIS)
    # ---- stockinged lower legs (into the shoes, up under the skirt)
    lw = B.ws(["calf_l", "calf_r", "thigh_l", "thigh_r", "foot_l", "foot_r"])
    lmask = (lw > 0.5) & (co[:, 2] < ZS["hem"] + 0.11) & (co[:, 2] > 0.045)
    legs = keep_faces(body, "PART_legs", lmask, main)
    decimate_to(legs, LEG_TRIS)
    # ---- eyes, bun, hat
    eyes = src["Eyes"]
    eyes.name = "PART_eyes"; eyes.data.name = "PART_eyes"
    move_to(eyes, main)
    for ob, mname in ((hair, "HAIR"), (lo, "SKIN"), (hands, "SKIN"), (eyes, "EYE"), (legs, "STOCKING")):
        ob.data.materials.clear()
        for m in MATS:
            ob.data.materials.append(bpy.data.materials.get("SRC_" + m) or bpy.data.materials.new("SRC_" + m))
        ob.data.polygons.foreach_set("material_index", [MATS.index(mname)] * len(ob.data.polygons))
        for p in ob.data.polygons:
            p.use_smooth = True
    bun = build_bun(main)
    hairvol = build_hair_volume(main, body, hair)
    hat = build_hat(main, hair, lo, hairvol)
    src["Eyebrows"].hide_render = True
    src["Eyebrows"].hide_set(True)
    hi.hide_set(True); hands_hi.hide_set(True)
    print("SKIN parts", {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons)
                         for o in (hair, lo, hands, eyes, legs, bun, hat, hairvol)})
    return dict(hair=hair, head=lo, hands=hands, eyes=eyes, legs=legs, bun=bun, hat=hat, hairvol=hairvol,
                head_hi=hi, hands_hi=hands_hi)


# ---------------------------------------------------------------------------------------------
# 6. the basket: built where it hangs in the Idle pose, stored in the forearm's rest frame
# ---------------------------------------------------------------------------------------------
BASKET = dict(along=0.115, half_l=0.145, half_w=0.095, depth=0.115, handle_h=0.120, yaw=math.radians(40),
              sleeve_r=0.047)


def build_basket(c, arm):
    pose_at(arm, "Idle", 0)
    P = arm.pose.bones
    Mp = arm.matrix_world @ P["lowerarm_l"].matrix
    Mr = arm.matrix_world @ arm.data.bones["lowerarm_l"].matrix_local
    a = (Mp.to_3x3() @ Vector((0, 1, 0))).normalized()
    e = Mp.translation.copy()
    h = e + a * BASKET["along"]
    up = Vector((0, 0, 1))
    perp = a.cross(up); perp.z = 0; perp.normalize()
    if perp.x < 0:
        perp = -perp
    # long axis: square across the forearm, turned (yaw) so the outer end swings back beside her
    # hip and the inner end forward, clear of her front
    L = (perp * math.cos(BASKET["yaw"]) + Vector((0, 1, 0)) * math.sin(BASKET["yaw"])).normalized()
    Wd = up.cross(L).normalized()
    z_top = h.z + BASKET["sleeve_r"] + 0.006
    z_rim = z_top - BASKET["handle_h"]
    z_bot = z_rim - BASKET["depth"]
    ctr = Vector((h.x, h.y, 0.0))
    mb = MB("basket")
    N = 28

    def oval(hl, hw, z, n=N, pw=3.0):
        pts = []
        for k in range(n):
            th = TAU * k / n
            cx, sx = math.cos(th), math.sin(th)
            x = hl * math.copysign(abs(cx) ** (2 / pw), cx)
            y = hw * math.copysign(abs(sx) ** (2 / pw), sx)
            pts.append(ctr + L * x + Wd * y + Vector((0, 0, z)))
        return pts
    hl, hw = BASKET["half_l"], BASKET["half_w"]
    outer = [oval(hl * 0.86, hw * 0.84, z_bot + 0.004), oval(hl * 0.90, hw * 0.89, z_bot + 0.03),
             oval(hl * 0.96, hw * 0.95, z_rim - 0.035), oval(hl, hw, z_rim - 0.004),
             oval(hl + 0.006, hw + 0.006, z_rim + 0.002), oval(hl + 0.003, hw + 0.003, z_rim + 0.009),
             oval(hl - 0.006, hw - 0.006, z_rim + 0.007), oval(hl - 0.008, hw - 0.008, z_rim - 0.005)]
    mb.grid(outer, "WICKER", closed=True)
    foot = oval(hl * 0.84, hw * 0.82, z_bot)
    bf = mb.grid([foot, outer[0]], "WICKER", closed=True)
    mb.fan(list(range(bf, bf + N)), ctr + Vector((0, 0, z_bot)), "WICKER", flip=True)
    # cloth cover tucked in at the rim, softly domed, an edge hanging over the outer side
    cov = []
    for t, dz in ((0.93, -0.004), (0.75, 0.012), (0.45, 0.022), (0.15, 0.026)):
        cov.append(oval((hl - 0.008) * t, (hw - 0.008) * t, z_rim + dz, n=20))
    bc = mb.grid(cov, "CLOTH", closed=True)
    mb.fan(list(range(bc + 3 * 20, bc + 4 * 20)), ctr + Vector((0, 0, z_rim + 0.027)), "CLOTH")
    flap_c = ctr - Wd * (hw + 0.004)
    flap = [[flap_c + L * s_ + Vector((0, 0, z_rim + 0.010)) for s_ in (-0.05, 0.0, 0.05)],
            [flap_c - Wd * 0.008 + L * s_ * 0.8 + Vector((0, 0, z_rim - 0.035 + 0.01 * abs(s_) / 0.05))
             for s_ in (-0.05, 0.0, 0.05)]]
    mb.grid(flap, "CLOTH")
    # handle: a flat bent-willow band from end to end over the forearm
    path = []
    for k in range(15):
        th = math.pi * k / 14
        x = -(hl - 0.012) * math.cos(th)
        zz = z_rim - 0.012 + (z_top - z_rim + 0.012) * math.sin(th) ** 0.75
        path.append(ctr + L * x + Vector((0, 0, zz)))
    rows = []
    for k, p in enumerate(path):
        t = (path[min(k + 1, 14)] - path[max(k - 1, 0)]).normalized()
        nb = t.cross(Wd).normalized()
        rows.append([p + Wd * sw * 0.011 + nb * sn * 0.0045 for sw, sn in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    mb.grid(rows, "WICKER", closed=True)
    ob = mb.build(c, orient=lambda p: (ctr.x, ctr.y, (z_bot + z_rim) * 0.5) if p.z < z_rim + 0.012
                  else (ctr.x, ctr.y, z_rim - 0.03))
    ob.data.transform(Mr @ Mp.inverted())          # into the forearm's rest frame
    ob.data.update()
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    print("BASKET hook", tuple(round(x, 3) for x in h), "rim z", round(z_rim, 3), "bottom z", round(z_bot, 3))
    return ob


# ---------------------------------------------------------------------------------------------
# 7. skinning
# ---------------------------------------------------------------------------------------------
RIGID = {"eyes": "Head", "hat": "Head", "bun": "Head", "basket": "lowerarm_l"}


def set_weights(ob, fn):
    """fn(co) -> {bone: weight}; replaces all groups."""
    for vg in list(ob.vertex_groups):
        ob.vertex_groups.remove(vg)
    groups = {}
    for v in ob.data.vertices:
        for b, w in fn(v.co).items():
            if w <= 1e-4:
                continue
            g = groups.get(b) or ob.vertex_groups.new(name=b)
            groups[b] = g
            g.add([v.index], w, "REPLACE")


def skirt_weights(p):
    t = 0.58 * smooth01((0.86 - p.z) / 0.52)
    sx = max(-1.0, min(1.0, p.x / 0.10))
    return {"pelvis": 1.0 - t, "thigh_l": t * (0.5 + 0.5 * sx), "thigh_r": t * (0.5 - 0.5 * sx)}


SLEEVE_MODE = "donor"      # round 1: bodice shoulder + sleeve cap both take the skin's own weights


def stage_weights_s(parts, donor, arm):
    sh_x = abs(arm.data.bones["upperarm_l"].head_local.x)
    order = ["blouse"] + [k for k in parts if k != "blouse"]
    for name in order:
        ob = parts[name]
        if name in RIGID:
            transfer_weights(ob, donor, arm, rigid=RIGID[name])
        elif name == "skirt":
            set_weights(ob, skirt_weights)
        elif name == "sash":
            set_weights(ob, lambda p: {"pelvis": 0.78, "spine_01": 0.22})
        else:
            transfer_weights(ob, parts["blouse"] if name == "collar" else
                             (parts["sleeves"] if name == "capfill" else donor), arm)
        if name == "blouse":
            def neck_f(p):
                rr = math.hypot(p.x, p.y + 0.01)
                return 0.85 * smooth01((p.z - 1.33) / 0.03) * smooth01((0.13 - rr) / 0.04)
            blend_to_bone(ob, "spine_03", neck_f)
            blend_to_bone(ob, "spine_01", lambda p: 0.5 * smooth01((1.02 - p.z) / 0.06) if p.z > 0.93 else 0.0)
            blend_to_bone(ob, "pelvis", lambda p: 0.85 * smooth01((0.97 - p.z) / 0.06))
            # round 1: the shoulder of the bodice rides on the shoulder girdle, not on the upper
            # arm (otherwise its corners are dragged out over the sleeve cap as flaps)
            for side, sg in (("l", 1.0), ("r", -1.0)) if SLEEVE_MODE != "donor" else ():
                blend_to_bone(ob, f"clavicle_{side}", lambda p, sg=sg: 0.0 if p.x * sg <= 0 else
                              0.9 * smooth01((p.x * sg - 0.085) / 0.045) * smooth01((p.z - 1.15) / 0.07))
        if name == "collar":
            blend_to_bone(ob, "spine_03", lambda p: 0.8)
        if name == "sleeves" and SLEEVE_MODE != "donor":
            # round 1: the sleeve cap moves exactly like the blouse it meets (weights copied from
            # the blouse, fading to the arm's own weights 3-9 cm out), so no gap opens at the seam
            mask = ob.vertex_groups.new(name="CAPMASK")
            for v in ob.data.vertices:
                t = smooth01((sh_x + 0.06 - abs(v.co.x)) / 0.08)
                if t > 0:
                    mask.add([v.index], t, "REPLACE")
            for vg in parts["blouse"].vertex_groups:
                if vg.name not in ob.vertex_groups:
                    ob.vertex_groups.new(name=vg.name)
            m = ob.modifiers.new("DT2", "DATA_TRANSFER")
            m.object = parts["blouse"]; m.use_vert_data = True
            m.data_types_verts = {"VGROUP_WEIGHTS"}; m.vert_mapping = "POLYINTERP_NEAREST"
            m.layers_vgroup_select_src = "ALL"; m.layers_vgroup_select_dst = "NAME"
            m.vertex_group = "CAPMASK"; m.mix_mode = "REPLACE"; m.mix_factor = 1.0
            activate(ob)
            bpy.ops.object.modifier_apply(modifier=m.name)
            ob.vertex_groups.remove(ob.vertex_groups["CAPMASK"])
        if name not in RIGID:
            finish_weights(ob, smooth=0 if name in ("head", "hands", "hair", "legs", "shoes")
                           else (4 if name in ("blouse", "skirt") else 2))
        m = ob.modifiers.new("Armature", "ARMATURE")
        m.object = arm
    for ob in parts.values():
        ob.parent = arm
        ob.matrix_parent_inverse = arm.matrix_world.inverted()


# ---------------------------------------------------------------------------------------------
# 8. checks: legs through the skirt, basket through the clothes, over Idle / Talk
# ---------------------------------------------------------------------------------------------
def _eval_world(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    mw = np.array(ob.matrix_world)
    out = co @ mw[:3, :3].T + mw[:3, 3]
    faces = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return out, faces


def shopper_check(actions=("Idle", "Talk"), step=6, verbose=True):
    """Per frame: leg vertices of the (hidden) donor body above the hem that lie outside the
    skirt shell, hand vertices inside the skirt / sash, and basket vertices inside the skirt /
    blouse / sash."""
    from mathutils.bvhtree import BVHTree
    arm = arm_global()
    body = bpy.data.objects["SRC_Body"]
    if body.parent != arm:
        body.parent = arm
        body.matrix_parent_inverse = arm.matrix_world.inverted()
    mod = body.modifiers.get("CheckArm") or body.modifiers.new("CheckArm", "ARMATURE")
    mod.object = arm
    B = BodyData(body)
    lw = B.ws(["thigh_l", "thigh_r", "calf_l", "calf_r"])
    zr = B.co[:, 2]
    leg_idx = np.where((lw > 0.5) & (zr > ZS["hem"] + 0.03) & (zr < 0.80))[0]
    worst = {}
    for act in actions:
        a = bpy.data.actions[act]
        f0, f1 = int(a.frame_range[0]), int(a.frame_range[1])
        for f in range(f0, f1 + 1, step):
            pose_at(arm, act, f)
            S, SF = _eval_world(bpy.data.objects["PART_skirt"])
            bt = BVHTree.FromPolygons([Vector(v) for v in S], SF)
            Bc, _ = _eval_world(body)
            out = 0; dmax = 0.0
            for i in leg_idx:
                v = Vector(Bc[i])
                loc, n, idx, d = bt.find_nearest(v)
                if loc is not None and (v - loc).dot(n) > 0.0:
                    out += 1; dmax = max(dmax, d)
            res = {"legs_out": out, "max_mm": round(dmax * 1000, 1)}
            # hands (the gesturing right one above all) through the skirt / sash
            H, _ = _eval_world(bpy.data.objects["PART_hands"])
            for nm in ("PART_skirt", "PART_sash"):
                Cc, CF = _eval_world(bpy.data.objects[nm])
                tr = BVHTree.FromPolygons([Vector(v) for v in Cc], CF)
                bad = 0; dm = 0.0
                for v in H[::2]:
                    loc, n, idx, d = tr.find_nearest(Vector(v))
                    if loc is not None and (Vector(v) - loc).dot(n) < 0 and d < 0.03:
                        bad += 1; dm = max(dm, d)
                res["hand_in_" + nm[5:]] = (bad, round(dm * 1000, 1))
            if "PART_basket" in bpy.data.objects:
                K, KF = _eval_world(bpy.data.objects["PART_basket"])
                for nm in ("PART_skirt", "PART_blouse", "PART_sash"):
                    Cc, CF = _eval_world(bpy.data.objects[nm])
                    tr = BVHTree.FromPolygons([Vector(v) for v in Cc], CF)
                    bad = 0; dm = 0.0
                    for v in K:
                        loc, n, idx, d = tr.find_nearest(Vector(v))
                        if loc is not None and (Vector(v) - loc).dot(n) < 0 and d < 0.08:
                            bad += 1; dm = max(dm, d)
                    res["basket_in_" + nm[5:]] = (bad, round(dm * 1000, 1))
            worst[(act, f)] = res
            if verbose:
                print("CHECK", act, f, res)
    arm.animation_data.action = None
    body.modifiers.remove(mod)
    return worst


def tuck_caps(iters=6, step=12):
    """Round 1: any sleeve-cap vertex (rest |x| < shoulder + 3.5 cm) that stands out of the bodice
    in a sampled Idle / Talk frame is drawn 20 % toward the arm's axis in the rest mesh, repeated
    until none does (at most to 55 % of its radius): no flap or dark wedge at the armhole."""
    from mathutils.bvhtree import BVHTree
    arm = arm_global()
    sl = bpy.data.objects["PART_sleeves"]; bl = bpy.data.objects["PART_blouse"]
    sh = arm.data.bones["upperarm_l"].head_local
    me = sl.data
    r0 = {}
    cap = [v.index for v in me.vertices if abs(v.co.x) < abs(sh.x) + 0.035]
    for i in cap:
        v = me.vertices[i].co
        r0[i] = math.hypot(v.y - sh.y, v.z - sh.z)
    frames = [("Idle", f) for f in range(0, 145, step)] + [("Talk", f) for f in range(0, 73, step)]
    for it in range(iters):
        bad = set()
        for act, f in frames:
            pose_at(arm, act, f)
            S, _ = _eval_world(sl); Bc, BF = _eval_world(bl)
            bt = BVHTree.FromPolygons([Vector(v) for v in Bc], BF)
            for i in cap:
                loc, n, idx, d = bt.find_nearest(Vector(S[i]))
                if loc is not None and d < 0.05 and (Vector(S[i]) - loc).dot(n) > 0.001:
                    bad.add(i)
        print("TUCK pass", it, "cap verts out", len(bad))
        if not bad:
            break
        for i in bad:
            v = me.vertices[i].co
            c = Vector((v.x, sh.y, sh.z))
            r = (v - c).length
            if r > 0.55 * r0[i]:
                me.vertices[i].co = c + (v - c) * max(0.8, 0.55 * r0[i] / max(r, 1e-6))
        me.update()
    arm.animation_data.action = None
    return len(bad)


def seam_check(actions=("Idle", "Talk"), step=6):
    """Round 1: sleeve-cap vertices (rest |x| < shoulder + 3 cm) standing out of the bodice,
    and bodice vertices near the armhole standing out over the sleeve, per frame (max mm)."""
    from mathutils.bvhtree import BVHTree
    arm = arm_global()
    sl = bpy.data.objects["PART_sleeves"]; bl = bpy.data.objects["PART_blouse"]
    sh_x = abs(arm.data.bones["upperarm_l"].head_local.x)
    rest = np.array([v.co[:] for v in sl.data.vertices])
    cap = np.where(np.abs(rest[:, 0]) < sh_x + 0.03)[0]
    worst = 0.0; nworst = 0
    for act in actions:
        a = bpy.data.actions[act]
        for f in range(int(a.frame_range[0]), int(a.frame_range[1]) + 1, step):
            pose_at(arm, act, f)
            S, _ = _eval_world(sl); Bc, BF = _eval_world(bl)
            bt = BVHTree.FromPolygons([Vector(v) for v in Bc], BF)
            n_out = 0; m = 0.0
            for i in cap:
                loc, n, idx, d = bt.find_nearest(Vector(S[i]))
                sd = (Vector(S[i]) - loc).dot(n)
                if sd > 0.002 and d < 0.04:
                    n_out += 1; m = max(m, sd)
            worst = max(worst, m); nworst = max(nworst, n_out)
    arm.animation_data.action = None
    print("SEAM cap verts out of the bodice: max count", nworst, "max mm", round(worst * 1000, 1))
    return nworst, worst


# ---------------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------------
def build_all():
    new_file()
    with win_ctx():
        arm = stage_rig_s()
        if arm.animation_data:
            arm.animation_data.action = None
        src = stage_human_s(arm)
        build_clips_s(arm)
        main = bpy.data.collections[COLL]
        G = GarmentsS(src["Body"], arm)
        bl = G.build_blouse(main)
        parts = dict(blouse=bl, collar=None, sleeves=G.build_sleeves(main, bl),
                     skirt=G.build_skirt(main), sash=G.build_sash(main), shoes=G.build_shoes(main))
        parts["capfill"] = G.capfill
        parts["collar"] = G.build_collar(main, parts["blouse"])
        sk = stage_skin_s(src, G)
        for k in ("hair", "head", "hands", "eyes", "legs", "bun", "hat", "hairvol"):
            parts[k] = sk[k]
        parts["basket"] = build_basket(main, arm)
        stage_weights_s(parts, src["Body"], arm)
        src["Body"].hide_set(True)
        src["Body"].hide_render = True
        tot = 0
        for k, ob in parts.items():
            t = sum(len(p.vertices) - 2 for p in ob.data.polygons); tot += t
            print("PART", k, t)
        print("TOTAL TRIS", tot)
        bpy.ops.wm.save_mainfile()
    return parts


if not globals().get("SHOPPER_LIB_ONLY"):
    PARTS = build_all()
