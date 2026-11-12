"""
A1, the grocer's boy at 35-37 Main (anonymous), c. 1920 - geometry + rig build.

Run inside Blender (MPFB 2.0.18 extension installed, MakeHuman CC0 system-asset pack loaded):
    exec(open(r"<project>/tools/blender/npc_grocer_boy.py").read())

Same pipeline as John B. Pickell / Albert Rittenhouse: this script loads tools/blender/npc_pickell.py
as a library (PICKELL_LIB_ONLY) and overrides what makes the grocer's boy:
  * MakeHuman male about 17-19 (age 0.36, height slider tuned so the body is 1.71 m like
    Pickell's, so all of Pickell's garment heights still fit), slim (weight 0.42), with face
    targets for a young, open face: rounder head, small slightly upturned nose, fuller cheeks,
    mouth corners a little up (a faint smile), ears standing out a touch; young skin, blue eyes,
    eyebrow010 (natural, fairly full). Clean-shaven.
  * Hair: light-to-mid brown, full young hairline, short back and sides, fuller on top, centre
    parting (the young men's fashion c. 1920). Bareheaded.
  * Clothes: light tan duck work jacket (photo), a chore coat buttoned high (four
    buttons) with a small V and a turn-down collar, no lapels, a breast patch pocket; white shirt with a plain soft turn-down collar buttoned at
    the throat, no tie; dark trousers (Pickell's cut, with turn-ups); brown work shoes (Pickell's
    oxford last); a LONG WHITE GROCER'S APRON tied at the waist over the jacket (waistband all
    round, bow and tails at the back), hanging to mid-shin.
  * Clips: Idle (Pickell's, glance to his right, spine eased upright, feet close: 0.24 m, front-to-
    back stagger cut to 6 cm so the knees stay behind the apron, level gaze, tiny friendly head
    tilt), Talk (right-arm gestures calmed 25 %), Walk only if the apron check passes.
  * Final height 1.72 m: the bake script scales rig + mesh uniformly just before export.
Materials/atlas/AO/export: npc_grocer_boy_bake.py.  Previews: npc_grocer_boy_preview.py.

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
BLEND = os.path.join(ROOT, r"assets\models\source\npc-grocer-boy.blend")
COLL = "NPC_GrocerBoy"
WORK = "NPC_GrocerBoy_Work"
RIG_NAME = "GrocerBoy_Rig"
# MakeHuman age slider: 0.1875 = 11 y, 0.5 = 25 y (linear between) -> 0.36 ~ 19 y on MakeHuman's
# growth curve, which reads as a lad of 17-18 with a full-grown frame; height slider tuned so the
# body is 1.71 m (as Pickell's) - the young targets alone give 1.55 m
MACRO = dict(gender=1.0, age=0.36, muscle=0.45, weight=0.42, proportions=0.6, height=0.627)
PROXIES = (("Eyes", r"eyes\low-poly\low-poly.mhclo"),
           ("Eyebrows", r"eyebrows\eyebrow010\eyebrow010.mhclo"),
           ("Hair", r"hair\short02\short02.mhclo"))
MH_TARGETS = os.path.join(os.environ["APPDATA"], r"Blender Foundation\Blender\5.2\extensions"
                          r"\user_default\mpfb\data\targets")
FACE_TARGETS = [            # (relative path, weight)
    (r"head\head-round.target.gz", 0.30),
    (r"head\head-invertedtriangular.target.gz", 0.20),
    (r"nose\nose-point-up.target.gz", 0.35),
    (r"nose\nose-scale-vert-decr.target.gz", 0.25),
    (r"nose\nose-volume-decr.target.gz", 0.15),
    (r"chin\chin-width-decr.target.gz", 0.15),
    (r"cheek\l-cheek-volume-incr.target.gz", 0.25),
    (r"cheek\r-cheek-volume-incr.target.gz", 0.25),
    (r"mouth\mouth-angles-up.target.gz", 0.45),
    (r"mouth\mouth-scale-horiz-incr.target.gz", 0.10),
    (r"ears\l-ear-wing-incr.target.gz", 0.25),
    (r"ears\r-ear-wing-incr.target.gz", 0.25),
]
HEAD_TRIS = 2700
HAND_TRIS = 1500
HAIR_TRIS = 650
PART_X = 0.0                # centre parting

ANKLE_SEP = 0.24            # feet close (reviewed fault: wide stance)
STAGGER = 0.06              # UAL idle has one foot ~27 cm ahead: cut back so the knees stay under the apron
TOE_OUT = math.radians(12)

# garment design heights (m, Blender z) - Pickell's frame (same body height)
Z = dict(jk_b1=1.315, jk_b2=1.225, jk_b3=1.135, jk_b4=1.045,   # jacket buttons, all fastened
         gorge=1.405, tr_top=1.03, wc_v=1.30, wc_bot=0.925)
ZA = dict(band_lo=0.985, band_hi=1.015, hem=0.385, wrap=math.radians(98))   # apron (3 cm tape)


def stage_rig_b():
    arm = stage_rig()
    arm.name = arm.data.name = RIG_NAME
    return arm


def arm_global():
    return bpy.data.objects[RIG_NAME]


# ---------------------------------------------------------------------------------------------
# clips (replaces npc_pickell.build_clips, which stage_rig calls)
# ---------------------------------------------------------------------------------------------
def adjust_stagger(arm, name, stagger=0.06):
    """(npc_shopper) swing each leg about the hip's X axis so the ankles end `stagger` apart
    front-to-back; feet keep their world orientation; the drop is taken out by the pelvis."""
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
    sgn = 1.0 if yl <= yr else -1.0                       # keep whichever foot was forward, forward
    tgt = {"l": m - sgn * stagger / 2, "r": m + sgn * stagger / 2}
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
    print("CLIP", name, "stagger", round(abs(yr - yl), 3), "->", stagger, "pelvis", round(-rise, 4))


def straighten_spine(arm, name, amounts=(("spine_01", 0.15), ("spine_02", 0.30), ("spine_03", 0.35),
                                          ("neck_01", 0.35))):
    """(npc_shopper) ease the UAL idle's slouch part of the way back to upright (rotation only)."""
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


def calm_arm(arm, name, ref_name, k=0.25, side="r"):
    """(npc_shopper) blend the gesturing arm's rotations k of the way toward the Idle arm."""
    act = bpy.data.actions[name]
    ref = bpy.data.actions[ref_name]
    for bone in (f"clavicle_{side}", f"upperarm_{side}", f"lowerarm_{side}", f"hand_{side}"):
        fcs = {fc.array_index: fc for fc in iter_fcurves(act)
               if fc.data_path == f'pose.bones["{bone}"].rotation_quaternion'}
        rfc = {fc.array_index: fc for fc in iter_fcurves(ref)
               if fc.data_path == f'pose.bones["{bone}"].rotation_quaternion'}
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


HEAD_TILT = math.radians(2.5)       # a small friendly tilt of the head in Idle (toward his left)


def build_clips(arm):
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
    total = int(round(2 * L * slow))                   # 144 frames = 6.0 s
    idle = new_action_like("Idle", arm)
    frames = []
    for f in range(0, total + 1):
        t = (f / slow) % L
        if f == total:
            t = 0.0
        pose = sample_action(a, arm, t)
        u = (f - total * 0.5) / (total * 0.5)
        w = math.sin(math.pi * u) ** 2 if 0.0 <= u <= 1.0 else 0.0
        # glance to his right (down the street, toward visitors coming up from the south) and back,
        # plus a constant small head tilt
        for bone, ang, roll in (("neck_01", -0.09, 0.0), ("Head", -0.14, HEAD_TILT), ("spine_03", -0.03, 0.0)):
            if bone in pose and "rotation_quaternion" in pose[bone]:
                q = pose[bone]["rotation_quaternion"]
                qb = Quaternion((q.get(0, 1), q.get(1, 0), q.get(2, 0), q.get(3, 0)))
                rest = arm.data.bones[bone].matrix_local.to_3x3()
                ax = (rest.inverted() @ Vector((0, 0, 1))).normalized()
                fw = (rest.inverted() @ Vector((0, -1, 0))).normalized()
                qn = qb @ Quaternion(ax, ang * w) @ Quaternion(fw, roll)
                pose[bone]["rotation_quaternion"] = {0: qn.w, 1: qn.x, 2: qn.y, 3: qn.z}
        frames.append((f, pose))
    write_pose_keys(arm, idle, frames)
    idle.use_frame_range = True
    idle.frame_start, idle.frame_end = 0, total
    relax_fingers(arm)
    calm_arm(arm, "Talk", "Idle_Loop_src", k=0.25)
    bpy.data.actions.remove(a)
    for name, gaze in (("Idle", 1.0), ("Talk", 0.8)):
        straighten_spine(arm, name)
        adjust_stance_and_gaze(arm, name, ankle_sep=ANKLE_SEP, gaze_amount=gaze, gaze_target=-0.03,
                               toe_out_target=TOE_OUT)
        adjust_stagger(arm, name, STAGGER)
    arm.animation_data_create()
    for tr in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(tr)
    for name in ("Idle", "Talk", "Walk"):
        act = bpy.data.actions.get(name)
        if act is None:
            continue
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


def drop_walk(arm):
    """Remove the Walk clip (and its NLA track) - used when the apron check fails in Walk."""
    ad = arm.animation_data
    for tr in list(ad.nla_tracks):
        if tr.name == "Walk":
            ad.nla_tracks.remove(tr)
    act = bpy.data.actions.get("Walk")
    if act:
        bpy.data.actions.remove(act)


def pose_at(arm, action, frame):
    arm.animation_data_create()
    arm.animation_data.action = bpy.data.actions[action] if action else None
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()


# ---------------------------------------------------------------------------------------------
# MakeHuman body with face targets (as npc_rittenhouse.stage_human)
# ---------------------------------------------------------------------------------------------
def stage_human():
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
    D = retarget_deltas(rig, arm_global())
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
    print("HUMAN", {k: len(v.data.vertices) for k, v in src.items()})
    return src


def head_landmarks(body, eyes):
    co = np.array([v.co[:] for v in body.data.vertices])
    hw = BodyData(body).ws(["Head"])
    hd = co[hw > 0.5]
    ec = np.array([v.co[:] for v in eyes.data.vertices])
    out = dict(top=float(hd[:, 2].max()), front_y=float(hd[:, 1].min()), back_y=float(hd[:, 1].max()),
               half_w=float(np.abs(hd[:, 0]).max()), chin=float(hd[:, 2].min()),
               eye_z=float(ec[:, 2].mean()), eye_x=float(np.abs(ec[:, 0]).mean()), eye_front=float(ec[:, 1].min()))
    print("HEAD", {k: round(v, 4) for k, v in out.items()})
    return out


# ---------------------------------------------------------------------------------------------
# hairline: full young hairline, low and straight across the forehead, squared temples, short
# back and sides (azimuth 0 = forehead centre, 180 = nape; ear az ~76..101)
# ---------------------------------------------------------------------------------------------
HEAD_C = Vector((0.0, -0.012, 1.60))
HAIRLINE = [(0, 1.661), (12, 1.661), (24, 1.657), (36, 1.649), (46, 1.640), (54, 1.628), (61, 1.613),
            (67, 1.600), (73, 1.590), (79, 1.612), (98, 1.614), (104, 1.586), (115, 1.570), (130, 1.556),
            (150, 1.540), (165, 1.530), (180, 1.527)]




def z_hair(az):
    """Round 1: hairline with a short irregular fringe at the front and temples (tufts of
    3-6 mm) instead of a hard even arc."""
    base = lin(HAIRLINE, az)
    if az < 78:
        r = math.radians(az)
        fade = 1.0 - smooth01((az - 62) / 16)
        base += fade * (0.0050 * math.sin(r * 14 + 0.7) + 0.0030 * math.sin(r * 31 + 2.1)
                        + 0.0015 * math.sin(r * 53 + 0.3))
    return base


# ---------------------------------------------------------------------------------------------
# garments
# ---------------------------------------------------------------------------------------------
if "TROUSERS" not in MATS:
    MATS += ["TROUSERS", "APRON"]


def smooth01(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


SLOPE = 0.075          # the jacket front may fall back 7.5 cm per metre below the chest


def flatten_front(F, z_lo=1.10, z_top=1.40):
    """Round 1 (reviewer: 'chest looks like a bust'): over the front half the jacket falls flat
    from the collarbone to the hem. Per front column: from z_top down to the chest's fullest point
    the surface is at least a straight line, below it it only tapers evenly (no undercut); then the
    front rows are smoothed round (upward only) so the mounds either side of the buttons merge
    into one flat front."""
    import copy
    G = copy.copy(F)
    R = F.R.copy()
    ss = F.ss
    phis = np.arange(F.K) * TAU / F.K
    w = np.clip(np.cos(phis), 0.0, 1.0) ** 0.6
    i_lo = int(np.argmin(np.abs(ss - z_lo))); i_top = int(np.argmin(np.abs(ss - z_top)))
    C = F.C
    for k in range(F.K):
        if w[k] <= 0:
            continue
        cphi = math.cos(phis[k])
        if cphi < 0.3:
            continue
        # work on the FORWARD coordinate of the surface (hull centres move back toward the waist,
        # so equal radii would still recede): it may not fall back below the chest's fullest
        # point, and runs straight from the collarbone down to that point
        f = C[:, 0] + R[:, k] * cphi
        ip = i_lo + int(np.argmax(f[i_lo:i_top + 1]))
        fn = f.copy()
        for i in range(0, ip):           # no undercut below the chest: an even, gentle taper
            fn[i] = max(f[i], f[ip] - SLOPE * (ss[ip] - ss[i]))
        for i in range(ip + 1, i_top + 1):
            t = (ss[i] - ss[ip]) / max(ss[i_top] - ss[ip], 1e-6)
            fn[i] = max(f[i], f[ip] + (f[i_top] - f[ip]) * t)
        new = (fn - C[:, 0]) / cphi
        R[:, k] = R[:, k] * (1 - w[k]) + np.maximum(R[:, k], new) * w[k]
    front = w > 0.05
    n = i_top + 1
    for _ in range(30):
        R2 = smooth_circ(R[:n], 1)
        sub = R[:n].copy()
        sub[:, front] = np.maximum(sub[:, front], R2[:, front])
        R[:n] = sub
    G.R = R
    return G


class GarmentsB(Garments):
    def __init__(self, body_ob, arm):
        super().__init__(body_ob, arm)
        # neck field from ALL skin round the neck (Pickell's took only neck/Head-weighted points,
        # which on this body leaves out the back of the neck below 1.46 m: the neckline then ran
        # inside the nape); the face / chin (Head-weighted, in front) stays out
        B = self.B; co = B.co
        armw = B.ws(["upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r", "hand_l", "hand_r"])
        headw = B.ws(["Head"])
        nk = ((co[:, 2] > 1.36) & (co[:, 2] < 1.56) & (np.abs(co[:, 0]) < 0.066) & (armw < 0.05)
              & ~((headw > 0.5) & (co[:, 1] < 0.0)) & ~((headw > 0.5) & (co[:, 2] > 1.50)))
        self.N = Field(co[nk], s0=1.38, s1=1.54, ds=0.01, half=0.008, **TORSO_FRAME)
        # Pickell's waistcoat / shirt fields stay as built (only the shirt panel S is used here)
        # duck cloth bridges the young chest (no pectoral mounds through the jacket): upward-only
        # smoothing of the jacket field fills every dip between bumps
        self.J = offset_field(self.J, lambda s, ph: 0.0 * ph, smooth=10, floor=0.0)
        # a boxy duck jacket hangs straight down from the chest (no waist suppression)
        self.J = offset_field(self.J, lambda s, ph: 0.0 * ph, hang_from=1.32, hang_rate=0.0004, smooth=2,
                              floor=0.0)
        self.J = flatten_front(self.J)
        self._apron_env = {}

    # ---------------------------------------------------------------- jacket (closed, high)
    def x_open(self, z):
        b1 = Z["jk_b1"]
        if z >= b1:              # a small V from the top button to the collar (no lapels)
            return lin([(b1, 0.0), (Z["gorge"], 0.040), (1.44, 0.050), (1.6, 0.06)], z)
        return 0.0

    def build_jacket(self, c):
        J = self.J
        mb = MB("jacket")
        zh = self.crotch - 0.155               # a chore coat's length: covers the seat and the top of the inseam (round 1: +4 cm)
        zs = list(np.linspace(zh, 1.20, 13)) + list(np.linspace(1.225, 1.37, 6))
        M = 36
        rows = []
        for z in zs:
            xo = self.x_open(z)
            pl = solve_phi_for_x(J, z, xo, +1) if xo > 1e-4 else 0.0
            pr = solve_phi_for_x(J, z, xo, -1) if xo > 1e-4 else TAU
            if pr <= pl:
                pr += TAU
            rows.append([J.surf(z, p) for p in np.linspace(pl, pr, M)])
        last_phis = np.linspace(pl, pr, M)
        neck_row = [self.neckline(p) for p in last_phis]
        for t in (0.4, 0.75):
            mid = []
            for a_, b_ in zip(rows[-1], neck_row):
                q = a_.lerp(b_, t)
                q.z += 0.012 * math.sin(math.pi * t)
                mid.append(q)
            rows.append(mid)
        rows.append(neck_row)
        cy = -J.centre(zh)[0]
        hem_in = []
        for p in rows[0]:
            d = Vector((p.x, p.y - cy, 0.0)).normalized()
            hem_in.append(p - d * 0.005 + Vector((0, 0, 0.010)))
        mb.grid([hem_in] + rows, "SUIT")
        self.p_open = pl                       # where the V meets the neckline (collar ends)
        # four buttons down the closed front
        for z in (Z["jk_b1"], Z["jk_b2"], Z["jk_b3"], Z["jk_b4"]):
            p = J.surf(z, TAU - 0.045, 0.0015)
            n = (p - Vector((0.0, -J.centre(z)[0], z))).normalized()
            mb.disc(p, n, 0.0090, "BUTTON", n=8, depth=0.003)
        # a narrow fly edge over the buttoning line (the overlapping left front)
        fz = np.linspace(ZA["band_hi"] + 0.004, Z["jk_b1"] + 0.004, 8)
        mb.grid([[J.surf(z, 0.020, 0.0012), J.surf(z, 0.006, 0.0018)] for z in fz], "SUIT")
        # breast patch pocket on his left
        phis_b = np.linspace(math.radians(24), math.radians(54), 5)
        rows_p = [[J.surf(z, p, 0.0022) for p in phis_b] for z in (1.165, 1.205, 1.245, 1.262)]
        mb.grid(rows_p, "SUIT")
        return mb.build(c, orient=self.ref_torso())

    def build_collar(self, c):
        """Turn-down work-jacket collar (no lapels): from one edge of the small front V round the
        back of the neck to the other; stand hugging the shirt collar, rolled edge, fall lying on
        the shoulders; the ends come down to points at the V. Own part (AO stays clean)."""
        J = self.J
        mb = MB("collar")
        zb = lambda p: 1.428 + 0.028 * (0.5 - 0.5 * math.cos(p))
        p0 = getattr(self, "p_open", math.radians(18))
        phis = np.linspace(p0, TAU - p0, 34)
        r0 = [self.neckline(p, 0.001) for p in phis]
        from mathutils.bvhtree import BVHTree
        jo = bpy.data.objects["PART_jacket"]
        bt = BVHTree.FromObject(jo, bpy.context.evaluated_depsgraph_get())

        def on_jacket(q, gap, snap=False):
            loc, n, i, d = bt.find_nearest(q)
            if loc is None:
                return q
            return loc + n * gap if (snap or (q - loc).dot(n) < gap) else q
        def bridge(p, d, off):
            """Point on the jacket's own shoulder surface (the rows bridged from the 1.37 m ring
            to the neckline in build_jacket) d metres out from the neckline, lifted `off` along
            its normal; below the 1.37 ring it continues on the J field."""
            A = J.surf(1.37, p); Bn = self.neckline(p)
            L = (A - Bn).length

            def q(t, pp=p):
                a_ = J.surf(1.37, pp); b_ = self.neckline(pp)
                return a_.lerp(b_, t) + Vector((0.0, 0.0, 0.012 * math.sin(math.pi * t)))
            if d < L:
                t = 1.0 - d / L
                pt = q(t)
                t1 = q(min(t + 0.02, 1.0)) - q(max(t - 0.02, 0.0))
                t2 = q(t, p + 0.02) - q(t, p - 0.02)
            else:
                z = 1.37 - (d - L)
                pt = J.surf(z, p)
                t1 = J.surf(z + 0.01, p) - J.surf(z - 0.01, p)
                t2 = J.surf(z, p + 0.02) - J.surf(z, p - 0.02)
            n = t1.cross(t2).normalized()
            radial = Vector((pt.x, pt.y + J.centre(min(pt.z, J.ss[-1]))[0], 0.0))
            if n.dot(radial) + n.z * 0.5 < 0:
                n = -n
            return pt + n * off
        r1, r2, r2b, r3 = [], [], [], []
        for p, a0 in zip(phis, r0):
            pf = abs(((p + math.pi) % TAU) - math.pi)
            front = max(0.0, 1 - (pf - p0) / math.radians(55))          # 1 at the V edge
            # the stand leans in to hug the shirt's neckband (4 mm off it): no gap to look into
            r1.append(self.N.surf(zb(p) + 0.020 - 0.014 * front, p, 0.0110 + 0.006 * front))
            r2.append(self.N.surf(zb(p) + 0.023 - 0.014 * front, p, 0.0175 + 0.008 * front))
            # the fall drops close outside the stand, then lies on the jacket's shoulders; the
            # ends come down to points at the V
            rad = Vector((math.sin(p), -math.cos(p), 0.0))
            r2b.append(on_jacket(r2[-1] + Vector((0.0, 0.0, -0.011)) + rad * 0.003, 0.009))
            r3.append(bridge(p, 0.034 + 0.030 * front ** 1.3, 0.0080))
        mb.grid([r0, r1, r2, r2b, r3], "SUIT")
        return mb.build(c, orient=lambda p: (0.0, -self.N.centre(1.45)[0], p.z - 0.12))

    # ---------------------------------------------------------------- shirt front + soft collar
    def build_front(self, c):
        S, N = self.S, self.N
        mb = MB("front")
        # shirt front in the jacket's V, with a placket and two buttons
        zs = np.linspace(Z["jk_b1"] - 0.03, 1.435, 9)
        rows = [[S.surf(min(z, 1.435 - 0.03 * abs(p) / 0.62), p % TAU) for p in np.linspace(-0.62, 0.62, 9)]
                for z in zs]
        mb.grid(rows, "SHIRT")
        pz = np.linspace(Z["jk_b1"] - 0.01, 1.425, 5)
        mb.grid([[S.surf(z, -0.05 % TAU, 0.0006), S.surf(z, 0.0, 0.0010), S.surf(z, 0.05, 0.0006)] for z in pz],
                "SHIRT")
        for z in (1.372,):
            p = S.surf(z, 0.0, 0.0020)
            mb.disc(p, Vector((0.0, -1.0, 0.0)), 0.0048, "BUTTON", n=6, depth=0.0015)
        # neckband shirt (the detachable collar left off, as working lads often did): a plain
        # white band closed at the throat with a collar stud
        zb = lambda p: 1.428 + 0.028 * (0.5 - 0.5 * math.cos(p))
        phis = np.linspace(math.radians(2), math.radians(358), 30)
        # shirt yoke filling the jacket's neck opening out to under the coat collar (no view down
        # into the jacket between the band and the collar)
        yoke = [self.neckline(p, -0.0025) for p in phis]           # just inside the jacket's neckline
        stand_b = [N.surf(zb(p) - 0.012, p, 0.0080) for p in phis]
        stand0 = [N.surf(zb(p), p, 0.0065) for p in phis]
        stand1 = [N.surf(zb(p) + 0.026, p, 0.0062) for p in phis]
        stand2 = [N.surf(zb(p) + 0.029, p, 0.0045) for p in phis]          # rolled top edge
        mb.grid([yoke, stand_b, stand0, stand1, stand2], "SHIRT")
        q = N.surf(zb(0.0) + 0.013, 0.0, 0.0050)
        mb.disc(q, Vector((0.0, -1.0, 0.0)), 0.0034, "BUTTON", n=6, depth=0.0015)
        return mb.build(c, orient=self.ref_torso(0.02))

    # ---------------------------------------------------------------- trousers + shoes
    def build_legs(self, c):
        tro, sho = super().build_legs(c)
        # the two leg tubes cut into each other along the inner thighs (jagged dark seams seen
        # from behind): ease each tube's inside back to 1 cm off the mid-plane
        bm_ = bmesh.new(); bm_.from_mesh(tro.data)
        seen = set()
        inner_band = set()
        for v0 in bm_.verts:
            if v0.index in seen:
                continue
            isl, stack = [], [v0]
            seen.add(v0.index)
            while stack:
                v = stack.pop(); isl.append(v)
                for e in v.link_edges:
                    o = e.other_vert(v)
                    if o.index not in seen:
                        seen.add(o.index); stack.append(o)
            cx = sum(v.co.x for v in isl) / len(isl)
            if abs(cx) < 0.03:            # the hip tube
                continue
            sg = 1.0 if cx > 0 else -1.0
            # round 1: drop the turned-under band inside the cuff (its folded faces made UV
            # islands that the packer slid other islands into)
            # (npc_pickell.build_legs makes each leg one grid whose first row of 16 vertices is
            # that inner band; vertex order is kept, so it is the island's 16 lowest indices)
            inner_band.update(sorted(isl, key=lambda v: v.index)[:16])
            for v in isl:                 # smooth, monotone squash of the inside toward the plane
                u = v.co.x * sg
                if u < 0.024 and v.co.z > 0.45:
                    v.co.x = sg * (0.010 + 0.014 * math.exp((u - 0.024) / 0.014))
        if inner_band:
            bmesh.ops.delete(bm_, geom=list({f for v in inner_band for f in v.link_faces}), context="FACES")
            bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if not v.link_faces], context="VERTS")
        bm_.to_mesh(tro.data); bm_.free()
        # round 1: a gusset in the mid-plane closes the gap between the tops of the two leg tubes
        # (a dark crumpled shape showed below the jacket hem from behind): a flat web of trouser
        # cloth from the crotch seam down to where the thighs part
        cr = self.crotch
        gm = MB("gusset")
        ys = np.linspace(-0.055, 0.105, 9)
        sag = lambda y: math.sin(math.pi * (y + 0.055) / 0.16)
        top = [Vector((0.0, y, cr + 0.04)) for y in ys]
        mid = [Vector((0.0, y, cr - 0.06 - 0.03 * sag(y))) for y in ys]
        bot = [Vector((0.0, y, cr - 0.11 - 0.03 * sag(y))) for y in ys]
        gm.grid([top, mid, bot], "TROUSERS")
        self.gusset = gm.build(c)
        # trousers get their own (dark) slot
        i_s, i_t = MATS.index("SUIT"), MATS.index("TROUSERS")
        for p in tro.data.polygons:
            if p.material_index == i_s:
                p.material_index = i_t
        return tro, sho

    # ---------------------------------------------------------------- the grocer's apron
    APRON_EASE = 0.0075

    def apron_radius(self, z, p, ease=None):
        """Radius (from a fixed vertical axis through the waist centre) of a cloth hanging
        straight down from the waistband: at height z the outer envelope (2D convex hull) of the
        jacket's cross-sections from the waist down to z, plus ease. Never narrows going down.
        (Round 1: at or above the band bottom only the section at z itself is used - the old
        loop was empty there and collapsed the apron's top row onto the axis, leaving a strip of
        jacket showing between the band and the apron.)"""
        ease = self.APRON_EASE if ease is None else ease
        key = (round(z, 4), round(ease, 5))
        if key not in self._apron_env:
            J = self.J
            yc = -J.centre(ZA["band_lo"])[0]
            ph = np.linspace(0, TAU, 72, endpoint=False)
            if z >= ZA["band_lo"]:
                levels = [z]
            else:
                levels = list(np.arange(ZA["band_lo"], max(z, J.ss[0]) - 1e-6, -0.01)) + [max(z, J.ss[0])]
            pts = []
            for zz in levels:
                pts += [tuple(J.surf(zz, q, ease))[:2] for q in ph]
            H = hull2d(np.array(pts))
            self._apron_env[key] = (H, yc)
        H, yc = self._apron_env[key]
        d = np.array([math.sin(p), -math.cos(p)])
        return ray_poly(H, np.array([0.0, yc]), d), yc

    def apron_pt(self, z, p, off=0.0, ease=None):
        r, yc = self.apron_radius(z, p, ease)
        amp = 0.0045 * smooth01((0.86 - z) / 0.40)
        fold = 0.6 * math.sin(7 * p + 0.6) + 0.4 * math.sin(13 * p + 2.1)
        # round 1: the side edges stand a little clear of the legs low down (no leg through the
        # edge near the hem); no folds right at the edges (a straight, clean side edge)
        pf = abs(((p + math.pi) % TAU) - math.pi)
        side = 0.012 * smooth01((pf - 1.05) / 0.55) * smooth01((0.80 - z) / 0.30)
        r += amp * fold * (1.0 - smooth01((pf - 1.3) / 0.3)) + side + off
        return Vector((r * math.sin(p), yc - r * math.cos(p), z))

    def build_accessories(self, c):
        """Long white waist apron over the jacket: front panel wrapping round to the back of the
        hips, from the waistband to mid-shin; waistband all round; bow + tails at the back."""
        J = self.J
        mb = MB("apron")
        W = ZA["wrap"]
        n = 34
        phis = [(-W + 2 * W * k / (n - 1)) % TAU for k in range(n)]
        hem = ZA["hem"]
        hem_z = lambda p: hem
        zs = [0.955, 0.925] + list(np.linspace(0.89, 0.42, 11))
        rows = [[self.apron_pt(hem_z(p), p) for p in phis]]
        for z in sorted(zs):
            rows.append([self.apron_pt(z, p) for p in phis])
        # the top is gathered into the tape: snug on the jacket, tucked up under the tape
        rows.append([self.apron_pt(ZA["band_lo"] - 0.008, p, ease=0.0050) for p in phis])
        rows.append([self.apron_pt(ZA["band_lo"] + 0.012, p, ease=0.0030) for p in phis])
        # (round 1: no turned-up hem band - where it met the side edges it showed as a V-shaped
        # tear near the hem; the cloth edge is a single clean surface)
        mb.grid(rows, "APRON")
        # waistband all round, over the jacket and the apron's gathered top
        K = 48
        ph = np.linspace(0, TAU, K, endpoint=False)
        lo, hi = ZA["band_lo"], ZA["band_hi"]
        rb = [[J.surf(z, p, d) for p in ph] for z, d in ((lo - 0.001, 0.0048), (lo + 0.003, 0.0062),
                                                         (hi - 0.003, 0.0062), (hi + 0.001, 0.0048))]
        mb.grid(rb, "APRON", closed=True)
        # bow at the back: knot, two flat loops, two tails hanging down the seat
        zc = 0.5 * (lo + hi)
        p0 = math.pi
        ctr = J.surf(zc, p0, 0.0070)
        cy = -J.centre(zc)[0]
        nrm = Vector((0.0, 1.0, 0.0))
        tan = Vector((1.0, 0.0, 0.0)); up = Vector((0, 0, 1))
        hk, hz = 0.013, 0.016
        knot = [ctr + nrm * 0.008 + tan * sx * hk + up * sz * hz for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        kb = [p - nrm * 0.009 for p in knot]
        mb.poly(list(reversed(knot)), "APRON")
        for i in range(4):
            j = (i + 1) % 4
            mb.poly([knot[i], knot[j], kb[j], kb[i]], "APRON")
        # two flat bow wings (no folded loops: they made self-overlapping UV islands)
        for sgn in (1, -1):
            rows_w = []
            for k in range(5):
                u = k / 4
                dx = 0.010 + 0.050 * u
                hw = 0.007 + 0.011 * u * (1.0 - 0.25 * u)
                p_ = (p0 - sgn * dx / 0.15) % TAU
                base = J.surf(zc, p_, 0.0080 + 0.003 * math.sin(math.pi * u))
                rows_w.append([base + up * (-hw), base + up * (0.002 * u), base + up * hw])
            mb.grid(rows_w, "APRON")
        # two tails hanging straight down over the seat (fixed x; pushed out only where the
        # jacket bulges), a slanted cut at the ends
        for dx, ln in ((-0.016, 0.20), (0.018, 0.17)):
            rows_t = []
            z0 = zc - 0.010
            for k in range(6):
                u = k / 5
                z = z0 - ln * u
                row = []
                for sx in (-0.014, 0.0, 0.014):
                    x = dx + sx * (1.0 + 0.15 * u)
                    ph = (math.pi - math.atan2(x, 0.12)) % TAU         # back of the jacket at this x
                    y = max(J.surf(zz, ph, 0.0080).y for zz in np.linspace(z, z0, 6))
                    zz_ = z + (0.012 * (sx / 0.014 + 1) / 2 if k == 5 else 0.0)
                    row.append(Vector((x, y + 0.001 * u, zz_)))
                rows_t.append(row)
            mb.grid(rows_t, "APRON")
        return mb.build(c, orient=lambda p: (0.0, -self.T.centre(min(max(p.z, self.T.ss[0]), self.T.ss[-1]))[0],
                                             p.z))


# ---------------------------------------------------------------------------------------------
# head, neck, hands, hair, eyes (as npc_rittenhouse.stage_skin: young full hair with a centre
# parting, short back and sides, clean-shaven, nothing on the head)
# ---------------------------------------------------------------------------------------------
def stage_skin(src, garments):
    work = bpy.data.collections[WORK]
    main = bpy.data.collections[COLL]
    body = src["Body"]
    B = garments.B
    co = B.co
    from mathutils.bvhtree import BVHTree
    proxy = src["Hair"]
    pbvh = BVHTree.FromObject(proxy, bpy.context.evaluated_depsgraph_get())
    top = float(co[:, 2].max())
    above_v = np.array([p[2] > z_hair(az_of(p)) for p in co]) & (co[:, 2] > 1.45)
    above_v &= B.ws(["ears"]) < 0.3 if "ears" in B.w else True
    me_b = body.data
    vm = np.zeros(len(co), bool)
    for poly in me_b.polygons:
        if sum(above_v[i] for i in poly.vertices) >= 2 and co[poly.vertices[0], 2] > 1.45:
            for i in poly.vertices:
                vm[i] = True
    hair = keep_faces(body, "PART_hair", vm, main)
    hm = hair.data
    bm_ = bmesh.new(); bm_.from_mesh(hm)
    kill = [f for f in bm_.faces if sum(1 for v in f.verts if v.co.z > z_hair(az_of(v.co))) < 2]
    bmesh.ops.delete(bm_, geom=kill, context="FACES")
    bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if not v.link_faces], context="VERTS")
    sbvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    for it in range(4):
        new = {}
        for v in bm_.verts:
            # round 1: the front/temple edge is relaxed only once, so the irregular fringe stays
            if v.is_boundary and (it == 0 or az_of(v.co) > 75):
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
        hit = pbvh.ray_cast(p + n * 0.0005, n, 0.05)
        d_short = hit[3] if hit[0] is not None else 0.004
        t = min(0.0100, max(0.0030, 0.50 * d_short))
        t += 0.0045 * smooth01((p.z - (top - 0.050)) / 0.035)      # round 1: a little volume on top
        # short back and sides: thin below the crown's widest point, full on top
        side = smooth01((top - 0.055 - p.z) / 0.035)
        t *= 1.0 - 0.45 * side
        above = p.z - z_hair(az_of(p))
        taper = min(1.0, max(0.0, above / 0.016)) ** 0.8         # thins out toward the hairline
        t = 0.0015 + (t - 0.0015) * taper
        if v.index in bnd:
            t = 0.0010
        if p.z > top - 0.05 and p.y < 0.035:            # centre parting groove
            g = math.exp(-((p.x - PART_X) / 0.0045) ** 2)
            t = max(0.0012, t - 0.0040 * g)
        v.co = p + n * t
    hm.update()
    decimate_to(hair, HAIR_TRIS)
    # ---- high-res head (bake source) + low-res head
    neck_r = np.hypot(co[:, 0] / 0.064, (co[:, 1] - 0.0) / 0.075)
    head_mask = (co[:, 2] > 1.398) & (np.abs(co[:, 0]) < 0.11) & ((co[:, 2] > 1.47) | (neck_r < 1.0))
    hi = keep_faces(body, "HI_head", head_mask, work)
    at = hi.data.attributes.new("hairzone", "FLOAT", "POINT")
    # round 1: 1.5 cm fade below the hairline (short hair growing in), broken up in the shader
    at.data.foreach_set("value", [min(1.0, max(0.0, (v.co.z - z_hair(az_of(v.co)) + 0.016) / 0.018))
                                  for v in hi.data.vertices])
    hbvh = BVHTree.FromObject(hair, bpy.context.evaluated_depsgraph_get())
    lo = keep_faces(hi, "PART_head", np.ones(len(hi.data.vertices), bool), main)
    bm_ = bmesh.new(); bm_.from_mesh(lo.data)
    covered = set()
    for v in bm_.verts:
        loc, nrm_, idx, d = hbvh.find_nearest(v.co)
        if v.co.z - z_hair(az_of(v.co)) < 0.008:
            continue
        if loc is not None and d < 0.016 and (loc - v.co).dot(v.normal) > 0:
            hit = hbvh.ray_cast(v.co + v.normal * 0.0005, v.normal, 0.03)
            if hit[0] is not None:
                covered.add(v.index)
    kill = [f for f in bm_.faces if all(v.index in covered for v in f.verts)]
    bmesh.ops.delete(bm_, geom=kill, context="FACES")
    bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if not v.link_faces], context="VERTS")
    bm_.to_mesh(lo.data); bm_.free()
    decimate_to(lo, HEAD_TRIS)
    # the decimated scalp must not poke through the hair shell: sink it 2 mm under the hair
    bm_ = bmesh.new(); bm_.from_mesh(lo.data); bm_.normal_update()
    for v in bm_.verts:
        t = min(1.0, max(0.0, (v.co.z - z_hair(az_of(v.co)) + 0.002) / 0.004))
        if t > 0:
            v.co -= v.normal * 0.0020 * t
    bm_.to_mesh(lo.data); bm_.free()
    at2 = lo.data.attributes.new("hairdist", "FLOAT", "POINT")
    at2.data.foreach_set("value", [v.co.z - z_hair(az_of(v.co)) for v in lo.data.vertices])
    # ---- hands
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
    print("SKIN parts", {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in (hair, lo, hands, eyes)})
    src["Eyebrows"].hide_render = True
    src["Eyebrows"].hide_set(True)
    hi.hide_set(True); hands_hi.hide_set(True)
    return dict(hair=hair, head=lo, hands=hands, eyes=eyes, head_hi=hi, hands_hi=hands_hi)


# ---------------------------------------------------------------------------------------------
# skinning (as npc_rittenhouse.stage_weights; apron like the shopper's skirt)
# ---------------------------------------------------------------------------------------------
RIGID = ("eyes",)


def set_weights(ob, fn):
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


APRON_THIGH = 0.62


def apron_weights(p):
    if p.z > ZA["band_lo"] - 0.006 or p.y > 0.0:          # band, bow, tails, back wrap: the waist
        k = smooth01((p.z - 0.95) / 0.06)
        return {"pelvis": 1.0 - 0.25 * k, "spine_01": 0.25 * k}
    t = APRON_THIGH * smooth01((0.88 - p.z) / 0.50)
    sx = max(-1.0, min(1.0, p.x / 0.10))
    return {"pelvis": 1.0 - t, "thigh_l": t * (0.5 + 0.5 * sx), "thigh_r": t * (0.5 - 0.5 * sx)}


def jacket_collar_f(p):
    """Jacket neckline and coat collar ride on the upper spine (no gap when the head nods)."""
    rr = math.hypot(p.x, p.y + 0.005)
    return 0.85 * min(1.0, max(0.0, (p.z - 1.37) / 0.03)) * min(1.0, max(0.0, (0.15 - rr) / 0.04))


def stage_weights(parts, donor, arm, crotch):
    sh_x = abs(arm.data.bones["upperarm_l"].head_local.x)
    order = ["jacket"] + [k for k in parts if k != "jacket"]
    for name in order:
        ob = parts[name]
        if name in RIGID:
            transfer_weights(ob, donor, arm, rigid="Head")
            m = ob.modifiers.new("Armature", "ARMATURE"); m.object = arm
            continue
        if name == "apron":
            set_weights(ob, apron_weights)
        elif name == "gusset":
            set_weights(ob, lambda p: {"pelvis": 0.5, "thigh_l": 0.25, "thigh_r": 0.25})
        else:
            transfer_weights(ob, parts["jacket"] if name in ("front", "collar") else donor, arm)
        if name == "trousers":
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
            for side, sg in (("l", 1.0), ("r", -1.0)):
                blend_to_bone(ob, f"thigh_{side}", lambda p, sg=sg: 0.0 if p.x * sg <= 0.0 else
                              0.8 * min(1.0, max(0.0, (crotch + 0.07 - p.z) / 0.06))
                              * min(1.0, max(0.0, (p.z - 0.45) / 0.15)))
        # collar: exactly the jacket's (final) weights below it - no relative slide, no extra blend
        if name == "front":          # the neckband rides on the neck
            nz = lambda p: (p.z > 1.41 and math.hypot(p.x, p.y + 0.01) < 0.085)
            blend_to_bone(ob, "neck_01", lambda p: 0.85 if nz(p) else 0.0)
        if name == "sleeves":
            for side, sg in (("l", 1.0), ("r", -1.0)):
                blend_to_bone(ob, f"clavicle_{side}",
                              lambda p, sg=sg: 0.0 if p.x * sg < 0 else
                              0.85 * min(1.0, max(0.0, (sh_x + 0.05 - p.x * sg) / 0.09)))
        if name == "jacket":
            blend_to_bone(ob, "spine_03", jacket_collar_f)
            # the jacket below the apron band hangs from the pelvis like the apron (never crosses it)
            blend_to_bone(ob, "pelvis", lambda p: 0.9 * smooth01((ZA["band_lo"] + 0.02 - p.z) / 0.10))
        finish_weights(ob, smooth=0 if name in ("head", "hands", "hair") else (4 if name in ("jacket", "apron") else 2))
        m = ob.modifiers.new("Armature", "ARMATURE")
        m.object = arm
    for ob in parts.values():
        ob.parent = arm
        ob.matrix_parent_inverse = arm.matrix_world.inverted()


# ---------------------------------------------------------------------------------------------
# check: trouser legs in front of the apron, hands inside the apron, over the clips
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


def apron_check(actions=("Idle", "Talk"), step=6, verbose=True):
    """Per frame: trouser / jacket vertices (front, within the apron's wrap, above its hem) that
    lie in front of the apron surface; hand vertices behind it (inside, within 3 cm)."""
    from mathutils.bvhtree import BVHTree
    arm = arm_global()
    tro = bpy.data.objects["PART_trousers"]; jac = bpy.data.objects["PART_jacket"]
    apr = bpy.data.objects["PART_apron"]
    # rest-pose selection of the tested vertices
    arm.animation_data_create(); arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
    bpy.context.view_layer.update()
    sel = {}
    for ob in (tro, jac):
        co = np.array([v.co[:] for v in ob.data.vertices])
        ang = np.degrees(np.abs(np.arctan2(co[:, 0], -(co[:, 1] - 0.02))))
        sel[ob.name] = np.where((co[:, 1] < 0.0) & (ang < math.degrees(ZA["wrap"]) - 3)
                                & (co[:, 2] > ZA["hem"] + 0.03) & (co[:, 2] < ZA["band_lo"] - 0.02))[0]
    jz = min(v.co.z for v in jac.data.vertices)
    co = np.array([v.co[:] for v in tro.data.vertices])
    sel["back"] = np.where((co[:, 1] > 0.02) & (co[:, 2] > jz + 0.03) & (co[:, 2] < ZA["band_lo"] - 0.02))[0]
    worst = {}
    for act in actions:
        a = bpy.data.actions.get(act)
        if a is None:
            continue
        f0, f1 = int(a.frame_range[0]), int(a.frame_range[1])
        for f in range(f0, f1 + 1, step):
            pose_at(arm, act, f)
            S, SF = _eval_world(apr)
            bt = BVHTree.FromPolygons([Vector(v) for v in S], SF)
            res = {}
            for ob in (tro, jac):
                C, _ = _eval_world(ob)
                out = 0; dmax = 0.0
                for i in sel[ob.name]:
                    v = Vector(C[i])
                    loc, n, idx, d = bt.find_nearest(v)
                    if loc is not None and (v - loc).dot(n) > 0.0:
                        out += 1; dmax = max(dmax, d)
                res[ob.name[5:] + "_out"] = (out, round(dmax * 1000, 1))
            # trouser seat / thighs poking out through the back of the jacket
            Jc, JF = _eval_world(jac)
            jt = BVHTree.FromPolygons([Vector(v) for v in Jc], JF)
            C, _ = _eval_world(tro)
            out = 0; dmax = 0.0
            for i in sel["back"]:
                v = Vector(C[i])
                loc, n, idx, d = jt.find_nearest(v)
                if loc is not None and (v - loc).dot(n) > 0.0 and d < 0.05:
                    out += 1; dmax = max(dmax, d)
            res["seat_out"] = (out, round(dmax * 1000, 1))
            H, _ = _eval_world(bpy.data.objects["PART_hands"])
            bad = 0; dm = 0.0
            for v in H[::2]:
                loc, n, idx, d = bt.find_nearest(Vector(v))
                if loc is not None and (Vector(v) - loc).dot(n) < 0 and d < 0.03:
                    bad += 1; dm = max(dm, d)
            res["hands_in"] = (bad, round(dm * 1000, 1))
            worst[(act, f)] = res
            if verbose:
                print("CHECK", act, f, res)
    arm.animation_data.action = None
    return worst


# ---------------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------------
def build_all():
    new_file()
    with win_ctx():
        arm = stage_rig_b()
        drop_walk(arm)           # apron_check: the UAL stride swings the knees 2-20 cm through the apron
        src = stage_human()
        head_landmarks(src["Body"], src["Eyes"])
        main = bpy.data.collections[COLL]
        G = GarmentsB(src["Body"], arm)
        parts = dict(jacket=G.build_jacket(main), collar=G.build_collar(main))
        parts["sleeves"], parts["cuffs"] = G.build_sleeves(main)
        parts["front"] = G.build_front(main)
        parts["trousers"], parts["shoes"] = G.build_legs(main)
        parts["gusset"] = G.gusset
        parts["apron"] = G.build_accessories(main)
        sk = stage_skin(src, G)
        for k in ("hair", "head", "hands", "eyes"):
            parts[k] = sk[k]
        # zero-area faces (where rows pinch, e.g. the shirt yoke at the front V) get wild UV
        # islands in smart-project and can land on top of other islands: dissolve them
        for k, ob in parts.items():
            if k in ("head", "hands", "eyes"):
                continue
            bm_ = bmesh.new(); bm_.from_mesh(ob.data)
            n0 = len(bm_.faces)
            bmesh.ops.dissolve_degenerate(bm_, dist=2e-4, edges=bm_.edges[:])
            bmesh.ops.delete(bm_, geom=[f for f in bm_.faces if f.calc_area() < 1e-8], context="FACES")
            bm_.to_mesh(ob.data); bm_.free()
            if len(ob.data.polygons) != n0:
                print("DEGENERATE", k, n0, "->", len(ob.data.polygons))
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


if not globals().get("GROCER_LIB_ONLY"):
    PARTS = build_all()
