"""
R2-W, Furman R. Williamson, president of the Flemington National Bank (Bank Building, 56-66 Main),
c. 1920 - geometry + rig build.

Run inside Blender (MPFB 2.0.18 extension installed, MakeHuman CC0 system-asset pack loaded):
    exec(open(r"<project>/tools/blender/npc_williamson.py").read())

Same pipeline as John B. Pickell / Albert Rittenhouse: this script loads tools/blender/npc_pickell.py
as a library (PICKELL_LIB_ONLY), borrows a few clip / garment helpers from npc_grocer_boy.py
(spine straightening, front-to-back stagger, calmer Talk arm, flat jacket front) and overrides what
makes Williamson a different man:
  * MakeHuman male about 62 (age 0.785), slim to medium build (weight 0.50), upright; face
    targets for a lean, older face (oval, narrower, cheekbones a little marked, a slightly
    aquiline nose, larger ears, light eye bags); light blue eyes; eyebrow006 painted white-grey.
  * Hair: white, short back and sides, fuller at the temples (not receded), with an irregular
    edge and a painted fade (no hard skullcap line); the top is under the hat.
  * A full, trimmed white moustache (modelled, over the whole upper lip to just past the mouth
    corners, thickest in the middle, tapering to nothing at its edges - not a toothbrush).
  * Straw boater (lathe crown, flat brim with a rolled edge, black grosgrain ribbon with a flat
    bow on his left), rigid on the Head bone, sitting on the hair; white hair shows below it at
    the temples, over the ears and at the back.
  * Light warm-grey summer three-piece suit (Pickell's sack coat / waistcoat / trousers cut),
    white shirt front, stiff WING collar and a dark navy bow tie with small white spots; no
    watch chain; dark brown oxfords.
  * Clips Idle / Talk / Walk: Pickell's, spine eased upright, feet close (0.26 m), the UAL
    front-to-back stagger cut to 7 cm, level gaze, glance to his left; Talk's gesturing arm
    calmed 25 %.
  * Final height 1.74 m to the crown of the head (hat top ~1.81 m): the bake script scales rig +
    mesh uniformly just before export.
Materials/atlas/AO/export: npc_williamson_bake.py.  Previews: npc_williamson_preview.py.

Blender: Z up, metres, front faces -Y, origin on the ground between the feet.
"""
import bpy, bmesh, math, os, re
import numpy as np
from mathutils import Vector, Matrix, Quaternion

_ROOT = r"C:\Users\Tarik\AppFactory\Flemington Historic Walk"
PICKELL_LIB_ONLY = True
exec(open(os.path.join(_ROOT, r"tools\blender\npc_pickell.py"), encoding="utf-8").read())
PICKELL_LIB_ONLY = False


def _borrow(fname, names):
    """exec the top-level functions `names` from another build script into this namespace."""
    src = open(os.path.join(_ROOT, "tools", "blender", fname), encoding="utf-8").read()
    for n in names:
        i = src.index(f"\ndef {n}(") + 1
        m = re.compile(r"\n(?=\S)").search(src, src.index("\n", i) + 1)
        exec(src[i:m.start() if m else len(src)], globals())


_borrow("npc_grocer_boy.py", ["smooth01", "adjust_stagger", "straighten_spine", "calm_arm", "flatten_front",
                              "set_weights", "pose_at", "_eval_world"])
SLOPE = 0.075

# ---------------------------------------------------------------------------------------------
# overrides
# ---------------------------------------------------------------------------------------------
BLEND = os.path.join(ROOT, r"assets\models\source\npc-williamson.blend")
COLL = "NPC_Williamson"
WORK = "NPC_Williamson_Work"
RIG_NAME = "Williamson_Rig"
# MakeHuman age slider: 0.5 = 25 y, 1.0 = 90 y  ->  62 y = 0.5 + 37/65*0.5 = 0.785
MACRO = dict(gender=1.0, age=0.785, muscle=0.42, weight=0.50, proportions=0.6, height=0.45)
PROXIES = (("Eyes", r"eyes\low-poly\low-poly.mhclo"),
           ("Eyebrows", r"eyebrows\eyebrow006\eyebrow006.mhclo"),
           ("Hair", r"hair\short02\short02.mhclo"))
MH_TARGETS = os.path.join(os.environ["APPDATA"], r"Blender Foundation\Blender\5.2\extensions"
                          r"\user_default\mpfb\data\targets")
FACE_TARGETS = [            # (relative path, weight)
    (r"head\head-oval.target.gz", 0.40),
    (r"head\head-fat-decr.target.gz", 0.30),
    (r"head\head-scale-horiz-decr.target.gz", 0.12),
    (r"nose\nose-hump-incr.target.gz", 0.30),
    (r"nose\nose-scale-vert-incr.target.gz", 0.20),
    (r"nose\nose-point-down.target.gz", 0.15),
    (r"cheek\l-cheek-bones-incr.target.gz", 0.25),
    (r"cheek\r-cheek-bones-incr.target.gz", 0.25),
    (r"cheek\l-cheek-volume-decr.target.gz", 0.25),
    (r"cheek\r-cheek-volume-decr.target.gz", 0.25),
    (r"chin\chin-prominent-incr.target.gz", 0.20),
    (r"ears\l-ear-scale-incr.target.gz", 0.25),
    (r"ears\r-ear-scale-incr.target.gz", 0.25),
    (r"eyes\l-eye-bag-incr.target.gz", 0.25),
    (r"eyes\r-eye-bag-incr.target.gz", 0.25),
]
HEAD_TRIS = 2800
HAND_TRIS = 1800
HAIR_TRIS = 560
MOUSTACHE_TRIS = 220
PART_X = 0.030              # parting on his left (+x), as Pickell (under the hat)

ANKLE_SEP = 0.26
SQUASH = True              # inner walls of the leg tubes eased to the mid-plane (no overlap)
SQ = (0.010, 0.014, 0.024)  # wall offset, softness, start (m)
SHARE = False
STAGGER = 0.03
GAZE = 0.015               # head pitch target (rad): level, chin a touch up (no downward gaze)
TOE_OUT = math.radians(12)


def stage_rig_w():
    arm = stage_rig()
    arm.name = arm.data.name = RIG_NAME
    return arm


def arm_global():
    return bpy.data.objects[RIG_NAME]


# ---------------------------------------------------------------------------------------------
# clips (replaces npc_pickell.build_clips, which stage_rig calls)
# ---------------------------------------------------------------------------------------------
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
        # glance to his left (toward visitors coming up from the south) and back
        for bone, ang in (("neck_01", 0.09), ("Head", 0.14), ("spine_03", 0.03)):
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
    calm_arm(arm, "Talk", "Idle_Loop_src", k=0.25)
    bpy.data.actions.remove(a)
    for name in ("Idle", "Talk"):
        straighten_spine(arm, name)
        adjust_stance_and_gaze(arm, name, ankle_sep=ANKLE_SEP, gaze_amount=1.0, gaze_target=GAZE,
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
# garments: Pickell's sack coat, waistcoat and trousers in a light grey summer suit; a white
# shirt front, a stiff wing collar and a bow tie; no watch chain, no tape, no pencil
# ---------------------------------------------------------------------------------------------
for _m in ("STRAW", "RIBBON", "MOUST", "BOWTIE"):
    if _m not in MATS:
        MATS.append(_m)

WING = dict(h_front=0.044, h_back=0.048, gap=math.radians(7))


def zb_collar(p):
    """Base height of the shirt collar (higher at the back), as npc_pickell.build_front."""
    return 1.428 + 0.028 * (0.5 - 0.5 * math.cos(p))


def wing_h(p):
    pf = abs(((p + math.pi) % TAU) - math.pi)
    return WING["h_front"] + (WING["h_back"] - WING["h_front"]) * (pf / math.pi)


class GarmentsW(Garments):
    def __init__(self, body_ob, arm):
        super().__init__(body_ob, arm)
        B = self.B; co = B.co
        # neck field from all the skin round the neck (as npc_grocer_boy: Pickell's took only
        # neck/Head-weighted points, which can leave the back of the neck out)
        armw = B.ws(["upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r", "hand_l", "hand_r"])
        headw = B.ws(["Head"])
        nk = ((co[:, 2] > 1.36) & (co[:, 2] < 1.56) & (np.abs(co[:, 0]) < 0.066) & (armw < 0.05)
              & ~((headw > 0.5) & (co[:, 1] < 0.0)) & ~((headw > 0.5) & (co[:, 2] > 1.50)))
        self.N = Field(co[nk], s0=1.38, s1=1.54, ds=0.01, half=0.008, **TORSO_FRAME)
        # worsted bridges the chest (no pectoral mounds through the coat or waistcoat: the
        # reviewed 'bust-like chest'), then the fronts fall flat from the collarbone
        self.J = offset_field(self.J, lambda s, ph: 0.0 * ph, smooth=8, floor=0.0)
        self.J = flatten_front(self.J)
        # the back of a sack coat hangs smooth from the shoulder blades: fill the dips between
        # the body's bumps along the height (upward-only smoothing) so the light cloth shows no
        # horizontal ripples across the back
        R0 = self.J.R.copy()
        R = R0.copy()
        phis = np.arange(self.J.K) * TAU / self.J.K
        top = int(np.argmin(np.abs(self.J.ss - 1.36)))
        for _ in range(40):
            R2 = R.copy()
            R2[1:top] = 0.25 * R[:top - 1] + 0.5 * R[1:top] + 0.25 * R[2:top + 1]
            R = np.maximum(R, R2)
        wb = np.array([smooth01((-math.cos(p) + 0.1) / 0.5) for p in phis])     # 1 over the back
        self.J.R = R0 + (R - R0) * wb[None, :]
        self.W = offset_field(self.W, lambda s, ph: 0.0 * ph, smooth=6, floor=0.0)
        self.W = flatten_front(self.W, z_lo=1.10, z_top=1.38)
        # the waistcoat always stays at least 6 mm inside the coat (its lower edge poked through
        # the coat at the hips, below the pocket flaps: a dark ragged patch)
        if self.W.R.shape == self.J.R.shape:
            self.W.R = np.minimum(self.W.R, self.J.R - 0.006)

    # ---------------------------------------------------------------- lapels
    def _lapel(self, mb, J, side):
        """Round 1 (reviewer: lapels 'puffed-up shields' with a loose notch tab): the lapel lies
        flat on the coat front - 2.5-3.5 mm off it, no roll - with a straight outer edge from the
        top button to the notch (normal 1920 width, ~7.5 cm at the notch) and a small step notch
        set back inside that line, then up to the gorge."""
        b1 = Z["jk_b1"]
        inner = [(0.0, b1)] + [(self.x_open(z), z) for z in np.linspace(b1 + 0.02, Z["gorge"], 9)]
        zn = Z["notch"]
        outer = [(0.0, b1), (0.096, zn - 0.002), (0.098, zn), (0.084, zn + 0.010),
                 (inner[-1][0] + 0.004, Z["gorge"])]
        n = 14
        I = resample(inner, n); O = resample(outer, n)
        rows = []
        for t, off in ((0.0, 0.0034), (0.5, 0.0034), (1.0, 0.0030), (1.0, 0.0012)):
            row = []
            for k in range(n):
                x, z = I[k] * (1 - t) + O[k] * t
                phi = solve_phi_for_x(J, z, max(x, 0.0005), side)
                row.append(J.surf(z, phi, off))
            rows.append(row)
        mb.grid(rows, "SUIT")

    # ---------------------------------------------------------------- sack coat
    def build_jacket(self, c):
        """npc_pickell.Garments.build_jacket, with the hip-pocket flaps kept well inside the
        cutaway front edge and lying flatter (Pickell's flap could overhang the open front in
        the idle pose and showed a dark slit under it, read as a torn, jagged coat front)."""
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
        n0 = len(rows[0])
        for k, p in enumerate(rows[0]):
            d = Vector((p.x, p.y - cy, 0.0)).normalized()
            e = min(1.0, min(k, n0 - 1 - k) / 4.0)
            hem_in.append(p - d * 0.005 * e + Vector((0, 0, 0.010 * e)))
        mb.grid([hem_in] + rows, "SUIT")
        for side in (1, -1):
            self._lapel(mb, J, side)
        for z in (Z["jk_b1"], Z["jk_b2"], Z["jk_b3"]):
            if z < Z["jk_b2"] - 0.01:
                ph = solve_phi_for_x(J, z, self.x_open(z) + 0.018, -1)
            else:
                ph = TAU - 0.05
            p = J.surf(z, ph, 0.0015)
            n = (p - Vector((0.0, -J.centre(z)[0], z))).normalized()
            mb.disc(p, n, 0.0095, "BUTTON", n=8, depth=0.003)
        # hip-pocket flaps: front end at least 3.5 cm inside the open edge (at the flap's lower
        # edge, where the cutaway is widest), flap only 3 mm proud at its lower edge
        for side in (1, -1):
            z0 = 0.885
            p_edge = solve_phi_for_x(J, z0, self.x_open(z0) + 0.035, side)
            a0 = max(math.radians(42), abs(((p_edge + math.pi) % TAU) - math.pi))
            phis_p = [(p * side) % TAU for p in np.linspace(a0, a0 + math.radians(32), 5)]
            top = [J.surf(z0 + 0.050, p, 0.0030) for p in phis_p]
            bot = [J.surf(z0, p, 0.0042) for p in phis_p]
            mb.grid([bot, top], "SUIT")
        phis_b = np.linspace(math.radians(30), math.radians(52), 4)
        # round 1: welt and handkerchief lie flat (the welt's raised open end showed as a dark
        # triangle beside the handkerchief); the handkerchief spans the whole welt
        wb = [J.surf(1.252, p, 0.0014) for p in phis_b]
        wt = [J.surf(1.272, p, 0.0020) for p in phis_b]
        mb.grid([wb, wt], "SUIT")
        hk = [J.surf(1.284, p, 0.0020) for p in phis_b]
        mb.grid([wt, hk], "HANKY")
        return mb.build(c, orient=self.ref_torso())

    # ---------------------------------------------------------------- coat collar
    def build_collar(self, c):
        """Pickell's coat collar (notch to notch round the back of the neck: stand, roll, fall),
        but the fall is laid on the jacket's OWN shoulder surface (the rows bridged from the
        1.37 m ring to the neckline, as npc_grocer_boy.build_collar) and kept 8-9 mm off it, so
        it never dips under the coat: no jagged 'torn collar' line on the shoulders."""
        J = self.J
        mb = MB("collar")
        from mathutils.bvhtree import BVHTree
        jo = bpy.data.objects["PART_jacket"]
        bt = BVHTree.FromObject(jo, bpy.context.evaluated_depsgraph_get())

        def on_jacket(q, gap):
            loc, n, i, d = bt.find_nearest(q)
            if loc is None:
                return q
            return loc + n * gap if (q - loc).dot(n) < gap else q

        def bridge(p, d, off):
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
        zb = zb_collar
        phis = np.linspace(math.radians(50), math.radians(310), 30)
        r0, r1, r2, r2b, r3 = [], [], [], [], []
        for p in phis:
            pf = abs(((p + math.pi) % TAU) - math.pi)
            front = max(0.0, 1 - pf / math.radians(80))          # collar ends meet the lapels
            r0.append(self.neckline(p, 0.001))
            r1.append(self.N.surf(zb(p) + 0.027, p, 0.0245))      # stand top
            r2.append(self.N.surf(zb(p) + 0.029, p, 0.0315))      # roll
            rad = Vector((math.sin(p), -math.cos(p), 0.0))
            r2b.append(on_jacket(r2[-1] + Vector((0.0, 0.0, -0.011)) + rad * 0.003, 0.009))
            r3.append(on_jacket(bridge(p, 0.034 + 0.012 * front, 0.0080), 0.008))   # fall on the coat
        mb.grid([r0, r1, r2, r2b, r3], "SUIT")
        return mb.build(c, orient=lambda p: (0.0, -self.N.centre(1.45)[0], p.z - 0.12))

    # ---------------------------------------------------------------- waistcoat, wing collar, bow tie
    def build_front(self, c):
        W, N = self.W, self.N
        mb = MB("front")
        # round 1 (reviewer: 'zig-zag lower edge'): one clean pair of points. Every row follows
        # the shaped lower edge (rows interpolate from it to the top), so no row crosses another;
        # 13 columns per side: a short straight rise from the point to a small centre notch, and a
        # straight edge rising from the point to the side
        def wc_bottom(u):
            up = 0.11                                   # the point, ~2.5 cm out from the centre
            if u < up:
                return Z["wc_bot"] + 0.018 * (1.0 - u / up)
            return Z["wc_bot"] + 0.050 * ((u - up) / (1.0 - up))
        NR, NC = 16, 13
        for side in (1, -1):
            rows = []
            p1 = (math.radians(105) * side) % TAU
            for i in range(NR):
                f = i / (NR - 1)
                z0 = wc_bottom(0.0) + (1.44 - wc_bottom(0.0)) * f
                xo = lin([(Z["wc_v"], 0.0), (1.36, 0.042), (1.44, 0.066)], z0) if z0 > Z["wc_v"] else 0.0
                p0 = solve_phi_for_x(W, z0, max(xo, 0.0004), side)
                row = []
                for k in range(NC):
                    u = k / (NC - 1)
                    p = p0 + (p1 - p0) * u
                    b = wc_bottom(u)
                    zz = b + (1.44 - b) * f
                    pf = abs(((p + math.pi) % TAU) - math.pi)
                    zz = min(zz, lin([(0.0, 1.44), (0.6, 1.43), (1.0, 1.385), (1.85, 1.35)], pf))
                    row.append(W.surf(zz, p % TAU))
                rows.append(row)
            mb.grid(rows, "SUIT")
        for k in range(6):   # waistcoat buttons
            z = Z["wc_v"] - 0.014 - k * 0.046
            p = W.surf(z, TAU - 0.03, 0.0012)
            mb.disc(p, Vector((0.0, -1.0, 0.0)), 0.0062, "BUTTON", n=6, depth=0.002)
        # stiff wing collar: a tall starched band closed at the throat, rolled top edge
        g = WING["gap"]
        phis = np.linspace(g, TAU - g, 32)
        stand_b = [N.surf(zb_collar(p) - 0.016, p, 0.0065) for p in phis]     # shirt yoke under it
        stand0 = [N.surf(zb_collar(p), p, 0.0042) for p in phis]
        stand1 = [N.surf(zb_collar(p) + wing_h(p), p, 0.0046) for p in phis]
        stand2 = [N.surf(zb_collar(p) + wing_h(p) + 0.0018, p, 0.0030) for p in phis]
        stand3 = [N.surf(zb_collar(p) + wing_h(p) - 0.002, p, 0.0012) for p in phis]  # inner face of the edge
        mb.grid([stand_b, stand0, stand1, stand2, stand3], "SHIRT")
        # the two wings: the front corners of the band turned down and out over the bow tie
        for sg in (1, -1):
            fold, tip = [], []
            n = 5
            for k in range(n):
                u = k / (n - 1)
                pf_ = g + (math.radians(36) - g) * u
                p = pf_ if sg > 0 else TAU - pf_
                zt = zb_collar(p) + wing_h(p)
                fold.append(N.surf(zt + 0.0005, p, 0.0052))
                # lower edge of the wing: lowest at the front (the tip), up to the fold at the back
                pt_ = math.radians(10) + (math.radians(36) - math.radians(10)) * u
                pt = pt_ if sg > 0 else TAU - pt_
                drop = 0.023 * (1 - u) ** 1.25 + 0.0015
                tip.append(N.surf(zb_collar(pt) + wing_h(pt) - drop, pt, 0.0072 + 0.002 * (1 - u)))
            mb.grid([fold, tip] if sg > 0 else [tip, fold], "SHIRT")
        # bow tie: a knot and two butterfly wings lying round the front of the collar band
        zc = zb_collar(0.0) + 0.0105
        knot_c = N.surf(zc, 0.0, 0.0150)
        rings = []

        def ring_at(x, y, z, hh, dd, n=8):
            return [Vector((x, y - dd * math.cos(TAU * j / n), z + hh * math.sin(TAU * j / n))) for j in range(n)]
        for xx in (-0.0075, 0.0075):
            rings.append(ring_at(knot_c.x + xx, knot_c.y, zc, 0.0088, 0.0058))
        b0 = mb.grid(rings, "BOWTIE", closed=True)
        mb.fan(list(range(b0, b0 + 8)), Vector((knot_c.x - 0.0075, knot_c.y, zc)), "BOWTIE", flip=True)
        mb.fan(list(range(b0 + 8, b0 + 16)), Vector((knot_c.x + 0.0075, knot_c.y, zc)), "BOWTIE")
        stations = [(0.006, 0.0070, 0.0040), (0.013, 0.0105, 0.0046), (0.024, 0.0160, 0.0050),
                    (0.036, 0.0185, 0.0050), (0.045, 0.0165, 0.0042), (0.050, 0.0110, 0.0030)]
        self.bow_axis = []
        for sg in (1, -1):
            rows = []
            for x, hh, dd in stations:
                # the wing lies a little back round the neck, always at least 6 mm before the collar
                y = knot_c.y + 0.0006 + 0.009 * (x / 0.05) ** 2
                ph = solve_phi_for_x(N, zc, x, sg, off=0.0046)
                ys = N.surf(zc, ph, 0.0046).y
                y = min(y, ys - 0.006 - dd)
                z = zc - 0.0008 * (x / 0.05)
                self.bow_axis.append(Vector((sg * x, y, z)))
                rows.append(ring_at(sg * x, y, z, hh, dd))
            b1 = mb.grid(rows if sg > 0 else rows[::-1], "BOWTIE", closed=True)
            end = rows[-1]
            cend = Vector(np.mean([np.array(p) for p in end], 0)) + Vector((sg * 0.0015, 0, 0))
            last = list(range(b1 + 5 * 8, b1 + 6 * 8)) if sg > 0 else list(range(b1, b1 + 8))
            mb.fan(last, cend, "BOWTIE")
        self.bow_axis.append(Vector((0.0, knot_c.y, zc)))
        ob = mb.build(c, orient=self.ref_torso(0.02))
        # the bow tie faces outward from its own centre line (the torso reference sits behind it)
        bm_ = bmesh.new(); bm_.from_mesh(ob.data)
        ib = MATS.index("BOWTIE")
        flip = []
        for f in bm_.faces:
            if f.material_index != ib:
                continue
            cc = f.calc_center_median()
            ax = min(self.bow_axis, key=lambda a: abs(a.x - cc.x))
            ax = Vector((cc.x, ax.y, ax.z))
            if f.normal.dot(cc - ax) < 0:
                flip.append(f)
        bmesh.ops.reverse_faces(bm_, faces=flip)
        bm_.to_mesh(ob.data); bm_.free()
        return ob

    def build_shirt(self, c):
        """White shirt front in the waistcoat's V (own part: its crease shading is baked without
        the coat or collar over it, so no grey stripe can read as a tie)."""
        S = self.S
        mb = MB("shirt")
        # round 1: it runs on up under the wing collar and bow tie (the throat skin showed between
        # them as a dark wedge, read as a necktie)
        zs = np.linspace(Z["wc_v"] - 0.03, 1.452, 9)
        rows = [[S.surf(min(z, 1.452 - 0.014 * abs(p) / 0.62), p % TAU) for p in np.linspace(-0.62, 0.62, 9)]
                for z in zs]
        mb.grid(rows, "SHIRT")
        return mb.build(c, orient=self.ref_torso(0.02))

    def build_accessories(self, c):
        return None

    # ---------------------------------------------------------------- trousers + shoes
    def build_legs(self, c):
        tro, sho = super().build_legs(c)
        # the two leg tubes overlap along the inner thighs (their union reads as a web, a 'drop
        # crotch'): ease each tube's inside back to 4 mm off the mid-plane, so they just touch;
        # drop the turned-under band in the cuffs (npc_grocer_boy)
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
            if abs(cx) < 0.03:
                continue
            sg = 1.0 if cx > 0 else -1.0
            inner_band.update(sorted(isl, key=lambda v: v.index)[:16])
            for v in isl if SQUASH else []:
                u = v.co.x * sg
                if u < SQ[2] and v.co.z > 0.45:     # monotone clamp of the inner wall toward the mid-plane
                    v.co.x = sg * (SQ[0] + SQ[1] * math.exp((u - SQ[2]) / SQ[1]))
        if inner_band:
            bmesh.ops.delete(bm_, geom=list({f for v in inner_band for f in v.link_faces}), context="FACES")
            bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if not v.link_faces], context="VERTS")
        bm_.to_mesh(tro.data); bm_.free()
        # which leg tube each vertex belongs to (+1 his left, -1 his right, 0 the hip tube), for
        # the rigid-ring leg weights in stage_weights
        side = {}
        me = tro.data
        adj = {i: set() for i in range(len(me.vertices))}
        for e in me.edges:
            adj[e.vertices[0]].add(e.vertices[1]); adj[e.vertices[1]].add(e.vertices[0])
        for i0 in range(len(me.vertices)):
            if i0 in side:
                continue
            isl, stack = [], [i0]
            side[i0] = 0
            while stack:
                i = stack.pop(); isl.append(i)
                for j in adj[i]:
                    if j not in side:
                        side[j] = 0; stack.append(j)
            cx = sum(me.vertices[i].co.x for i in isl) / len(isl)
            sg = 0 if abs(cx) < 0.03 else (1 if cx > 0 else -1)
            for i in isl:
                side[i] = sg
        at = me.attributes.new("legside", "INT", "POINT")
        at.data.foreach_set("value", [side[i] for i in range(len(me.vertices))])
        # the tops of the leg tubes (under the coat skirt) stay >= 1 cm inside the coat: they
        # poked out through it at the hips as a dark crescent below the pocket flaps
        J = self.J
        zh = self.crotch - 0.035
        n_in = 0
        for v in me.vertices:
            if side[v.index] == 0 or v.co.z < zh - 0.015:
                continue
            z = min(max(v.co.z, J.ss[0]), J.ss[-1])
            c0, c1 = J.centre(z)
            u1, u2 = -v.co.y - c0, v.co.x - c1
            r = math.hypot(u1, u2)
            lim = J.radius(z, math.atan2(u2, u1) % TAU) - 0.010
            if r > lim > 0:
                k = lim / r
                v.co.x = c1 + u2 * k
                v.co.y = -(c0 + u1 * k)
                n_in += 1
        print("LEGS top pulled inside the coat:", n_in, "vertices")
        # every leg-tube face faces away from its OWN thigh axis (npc_pickell.build_legs picks the
        # reference thigh by the sign of the face centre's x, so inner-wall faces that crossed the
        # mid-plane were turned toward the other leg: inverted faces = jagged shading in motion)
        tx = {1: self.bones["thigh_l"][0].x, -1: self.bones["thigh_r"][0].x}
        bm_ = bmesh.new(); bm_.from_mesh(me); bm_.normal_update()
        flip = []
        for f in bm_.faces:
            sg = side[f.verts[0].index]
            if sg == 0:
                continue
            cc = f.calc_center_median()
            if f.normal.dot(cc - Vector((tx[sg], 0.02, cc.z))) < 0:
                flip.append(f)
        bmesh.ops.reverse_faces(bm_, faces=flip)
        bm_.to_mesh(me); bm_.free()
        print("LEGS faces re-oriented", len(flip))
        # round 1 (reviewer: 'the top of the trousers shows as a lighter boxy panel with a notch'):
        # Pickell's short hip tube is replaced by one seat piece that wraps both legs: from the
        # waist down to 3 cm below the crotch it follows the outer surface of the two leg tubes
        # (bridging straight across between the thighs at the front = the fly, and at the back =
        # the seat), so the leg tubes come out of it with no step
        cr = self.crotch
        bm_ = bmesh.new(); bm_.from_mesh(me)
        sl = bm_.verts.layers.int.get("legside")
        bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if v[sl] == 0], context="VERTS")
        bm_.to_mesh(me); bm_.free()
        from mathutils.bvhtree import BVHTree
        lbvh = BVHTree.FromObject(tro, bpy.context.evaluated_depsgraph_get())
        T = self.T
        K = 40
        phis = np.linspace(0, TAU, K, endpoint=False)
        z_leg_top = cr + 0.060
        zrows = [cr - 0.030, cr - 0.012, cr + 0.010, cr + 0.035, z_leg_top, 0.90, 0.95, 1.00, Z["tr_top"]]
        RR = np.zeros((len(zrows), K))
        GAP = np.zeros((len(zrows), K))
        CC = []
        for i, z in enumerate(zrows):
            c0, c1 = T.centre(min(max(z, T.ss[0]), T.ss[-1]))
            CC.append((c0, c1))
            for k, p in enumerate(phis):
                d = Vector((math.sin(p), -math.cos(p), 0.0))
                o = Vector((c1, -c0, z))
                r_leg = None
                if z <= z_leg_top + 1e-6:
                    h = lbvh.ray_cast(o + d * 0.40, -d, 0.40)
                    if h[0] is not None:
                        r_leg = (h[0] - o).length + 0.0025
                r_t = T.radius(z, p) + 0.008 if z > cr + 0.045 else 0.0
                RR[i, k] = max(r_leg or 0.0, r_t)
            # angles with no leg under them (between the thighs): straight bridge across = the
            # largest radius allowed by the neighbours (interpolated over the gap)
            row = RR[i].copy()
            good = row > 1e-4
            GAP[i] = ~good
            if 2 < good.sum() < K:
                # each run of empty angles: the straight chord between the two leg points either
                # side of it (a flat fly / seat panel, not a bulging arc)
                for k in range(K):
                    if good[k]:
                        continue
                    a = k
                    while not good[a % K]:
                        a -= 1
                    b = k
                    while not good[b % K]:
                        b += 1
                    pa = row[a % K] * np.array([math.sin(phis[a % K]), math.cos(phis[a % K])])
                    pb = row[b % K] * np.array([math.sin(phis[b % K]), math.cos(phis[b % K])])
                    d = np.array([math.sin(phis[k]), math.cos(phis[k])])
                    e = pb - pa
                    den = d[0] * e[1] - d[1] * e[0]
                    RR[i, k] = (pa[0] * e[1] - pa[1] * e[0]) / den if abs(den) > 1e-9 else 0.5 * (row[a % K] + row[b % K])
        # upward-only smoothing along the height (no waist dip / steps between rows)
        for _ in range(4):
            R2 = RR.copy()
            R2[1:-1] = 0.25 * RR[:-2] + 0.5 * RR[1:-1] + 0.25 * RR[2:]
            RR[1:-1] = np.maximum(RR[1:-1], R2[1:-1])
        smb = MB("seat")
        rows = []
        # where the lower rows bridge between the thighs, they rise to the crotch seam (a small
        # inverted V at the bottom of the fly / seat, no straight 'shorts hem' across the legs)
        lift = {0: cr - 0.004 - zrows[0], 1: cr + 0.008 - zrows[1]}
        for i, z in enumerate(zrows):
            c0, c1 = CC[i]
            g = GAP[i] if i in lift else np.zeros(K)
            g = np.maximum(g, 0.5 * (np.roll(g, 1) + np.roll(g, -1)) * 0.6)
            rows.append([Vector((c1 + RR[i, k] * math.sin(p), -(c0 + RR[i, k] * math.cos(p)),
                                 z + lift.get(i, 0.0) * g[k])) for k, p in enumerate(phis)])
        smb.grid(rows, "SUIT", closed=True)
        self.seat = smb.build(c, orient=lambda q: (0.0, -T.centre(min(max(q.z, T.ss[0]), T.ss[-1]))[0], q.z))
        # the leg tubes' tops, now inside the seat, ease 4 mm in toward their thigh axis so they
        # never show through it in motion
        txs = {1: self.bones["thigh_l"][0].x, -1: self.bones["thigh_r"][0].x}
        sides = np.zeros(len(me.vertices), np.int32); me.attributes["legside"].data.foreach_get("value", sides)
        for v in me.vertices:
            k = smooth01((v.co.z - (cr - 0.045)) / 0.040)
            if k <= 0 or sides[v.index] == 0:
                continue
            ax = Vector((txs[int(sides[v.index])], 0.01, v.co.z))
            d = v.co - ax
            if d.length > 0.01:
                v.co -= d.normalized() * 0.005 * k
        me.update()
        # (npc_grocer_boy round 1) a gusset of trouser cloth in the mid-plane closes the slit
        # between the tops of the two leg tubes (seen from behind below the seat)
        gm = MB("gusset")
        # (back half only, so it never shows as a dark fly line from the front)
        ys = np.linspace(0.005, 0.055, 5)
        sag = lambda y: math.sin(math.pi * (y - 0.005) / 0.050)
        top = [Vector((0.0, y, cr + 0.04)) for y in ys]
        mid = [Vector((0.0, y, cr - 0.020 - 0.012 * sag(y))) for y in ys]
        bot = [Vector((0.0, y, cr - 0.045 - 0.015 * sag(y))) for y in ys]
        gm.grid([top, mid, bot], "SUIT")
        self.gusset = gm.build(c)
        return tro, sho


# ---------------------------------------------------------------------------------------------
# head: hairline (fuller than Rittenhouse's, not receded; the top is under the hat), boater,
# moustache.  Azimuth 0 = forehead centre, 180 = nape; ear ~76..101.
# ---------------------------------------------------------------------------------------------
HEAD_C = Vector((0.0, -0.012, 1.60))
# round 1 (reviewer: bare temples under the brim): the hairline comes lower and further forward
# at the temples, in a rounded curve (no hard diagonal), so a band of white hair shows under the
# brim at both temples from the front
HAIRLINE = [(0, 1.662), (10, 1.659), (20, 1.649), (30, 1.637), (40, 1.627), (50, 1.619), (60, 1.611),
            (67, 1.603), (73, 1.594), (76, 1.590), (79, 1.614), (98, 1.619), (104, 1.590), (115, 1.570), (130, 1.553), (145, 1.544), (160, 1.540),
            (180, 1.538)]                    # a neat, nearly level nape (no V)


def z_hair(az):
    """Hairline with a slightly irregular edge (short tufts of 2-4 mm) at the temples, the
    sideburns and round the back: no hard, even skullcap line."""
    base = lin(HAIRLINE, az)
    r = math.radians(az)
    amp = 1.0 if az > 40 else max(0.0, (az - 20) / 20)
    if az < 82:
        amp *= 0.4                                   # round 1: a soft, rounded temple edge
    base += amp * (0.0026 * math.sin(r * 17 + 0.7) + 0.0016 * math.sin(r * 37 + 2.1)
                   + 0.0008 * math.sin(r * 61 + 0.3))
    return base


# straw boater: level, a touch lower at the front; band (crown base) height at the front
HAT = dict(z_band=1.652, tip=0.004, crown_h=0.068, brim=0.058, axis_y=-0.022, ease=0.0035, K=26)


def hat_band_z(p):
    return HAT["z_band"] + HAT["tip"] * (0.5 - 0.5 * math.cos(p))


def hat_phi(q):
    return math.atan2(q[0], -(q[1] - HAT["axis_y"]))


def hat_radii(objs):
    """Crown radius per azimuth: outermost hair/skin round the axis at and just above the band
    height, plus a little ease (the hat sits on the hair)."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    trees = [BVHTree.FromObject(o, dg) for o in objs]
    K = HAT["K"]
    phis = np.linspace(0, TAU, K, endpoint=False)
    rr = []
    for p in phis:
        d = Vector((math.sin(p), -math.cos(p), 0.0))
        best = 0.0
        for dz, k_ in ((0.0, 1.0), (0.012, 1.0), (0.025, 0.99), (0.045, 0.97)):
            o = Vector((0.0, HAT["axis_y"], hat_band_z(p) + dz))
            for t in trees:
                h = t.ray_cast(o + d * 0.25, -d, 0.25)
                if h[0] is not None:
                    best = max(best, (h[0] - o).length * k_)
        rr.append(best + HAT["ease"])
    rr = np.array(rr)
    for _ in range(2):
        rr = np.maximum(rr, 0.25 * np.roll(rr, 1) + 0.5 * rr + 0.25 * np.roll(rr, -1))
    return phis, rr


def build_hat(c, objs):
    """Straw boater: straight-sided oval crown with a flat top, flat stiff brim with a rolled
    edge, black grosgrain ribbon round the crown with a flat bow on his left. Rigid on Head."""
    phis, rr = hat_radii(objs)
    K = len(phis)
    ax_y = HAT["axis_y"]
    H = HAT["crown_h"]
    W = HAT["brim"]
    mb = MB("hat")

    def ring(dr, dz, scale=1.0):
        return [Vector((0.0, ax_y, hat_band_z(p) + dz)) + Vector((math.sin(p), -math.cos(p), 0.0)) * (rr[k] * scale + dr)
                for k, p in enumerate(phis)]
    crown = [ring(0.0, -0.001), ring(0.0, H - 0.004), ring(-0.005, H)]
    b0 = mb.grid(crown, "STRAW", closed=True)
    top = Vector((0.0, ax_y, HAT["z_band"] + HAT["tip"] * 0.5 + H + 0.0015))
    mb.fan(list(range(b0 + 2 * K, b0 + 3 * K)), top, "STRAW")
    brim = [ring(0.0, 0.0), ring(W - 0.003, 0.0), ring(W, -0.0035), ring(0.0, -0.0065)]
    mb.grid(brim, "STRAW", closed=True)
    rib = [ring(0.0012, 0.0005), ring(0.0016, 0.034)]
    mb.grid(rib, "RIBBON", closed=True)
    # flat bow on his left side
    p0 = math.radians(90)
    d = Vector((math.sin(p0), -math.cos(p0), 0.0))
    tan = Vector((0, 0, 1)).cross(d).normalized()
    k0 = int(round(p0 / TAU * K)) % K
    ctr = Vector((0.0, ax_y, hat_band_z(p0) + 0.0175)) + d * (rr[k0] + 0.0030)
    for sgn in (1, -1):
        rows = []
        for u in np.linspace(0.0, 1.0, 4):
            hw = 0.0075 + 0.0055 * math.sin(math.pi * min(1.0, u * 1.15))
            q = ctr + tan * sgn * (0.004 + 0.024 * u) + d * (0.0012 * math.sin(math.pi * u))
            rows.append([q + Vector((0, 0, -hw)), q + Vector((0, 0, hw))])
        mb.grid(rows, "RIBBON")
    kn = [ctr + d * 0.0016 + tan * sx * 0.005 + Vector((0, 0, sz * 0.0085)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    mb.poly(kn, "RIBBON")

    def orient(c_):
        p = hat_phi(c_)
        k = int(round((p % TAU) / TAU * K)) % K
        rel = math.hypot(c_.x, c_.y - ax_y) - rr[k]
        if rel > 0.006 and c_.z < hat_band_z(p) + 0.002:            # brim: inside = its mid-plane
            return (c_.x, c_.y, hat_band_z(p) - 0.00325)
        return (0.0, ax_y, min(c_.z, hat_band_z(p) + H - 0.03))
    ob = mb.build(c, orient=orient)
    print("HAT radius", round(float(rr.min()), 4), round(float(rr.max()), 4), "tris",
          sum(len(p.vertices) - 2 for p in ob.data.polygons))
    return ob


# full trimmed moustache (front projection, metres; measured on this face: subnasale z 1.539,
# lip line z 1.5255, mouth corners x +-0.028 at z 1.525)
MOUST = dict(half_w=0.0330, T=0.0026)


def moust_top(ax):
    return lin([(0.0, 1.5405), (0.010, 1.5415), (0.018, 1.5398), (0.026, 1.5352), (0.033, 1.5272)], ax)


def moust_bot(ax):
    return lin([(0.0, 1.5258), (0.012, 1.5252), (0.022, 1.5236), (0.028, 1.5210), (0.033, 1.5195)], ax)


def build_moustache(c, face_objs):
    """Shell lofted over the upper lip: grid projected onto the face from the front, lifted along
    the surface normal by a thickness that is fullest in the middle and tapers to the edges;
    the lower edge overhangs the lip a little, the top edge tucks under the nose."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    trees = [BVHTree.FromObject(o, dg) for o in face_objs]

    def hit(x, z):
        best = None
        for t in trees:
            h = t.ray_cast(Vector((x, -0.30, z)), Vector((0, 1, 0)), 0.4)
            if h[0] is not None and (best is None or h[0].y < best[0].y):
                best = (h[0], h[1])
        return best
    hw, T = MOUST["half_w"], MOUST["T"]
    nx = 17
    xs = [hw * math.sin(0.5 * math.pi * (-1 + 2 * k / (nx - 1))) for k in range(nx)]
    # rows (fraction from bottom to top, lift factor): a crisp, trimmed lower edge (the first row
    # tucks back onto the lip just above the edge), a flat full body, thinning toward the nose
    vrows = [(0.10, 0.0), (0.0, 0.80), (0.20, 1.0), (0.45, 1.0), (0.70, 0.80), (0.88, 0.45), (1.0, 0.08)]
    rows = []
    for v, lift in vrows:
        row = []
        for x in xs:
            ax = abs(x)
            zt, zb = moust_top(ax), moust_bot(ax)
            end = ax / hw
            # rounded ends: the band narrows toward the tips
            mid = 0.5 * (zt + zb); half = 0.5 * (zt - zb) * (1 - 0.65 * end ** 4)
            z = mid - half + 2 * half * v
            hp = hit(x, z)
            if hp is None:
                p, n = Vector((x, -0.10, z)), Vector((0, -1, 0))
            else:
                p, n = hp
            n = (n + Vector((0, -0.6, 0))).normalized()
            prof = (1 - end ** 2.5) ** 0.6
            part = 1.0 - 0.30 * math.exp(-(x / 0.0045) ** 2) * v            # a faint centre parting
            t = 0.0004 + T * lift * part * (0.35 + 0.65 * prof)
            q = p + n * t
            if v == 0.0 and lift > 0:
                q.z -= 0.0010                      # the trimmed edge hangs just over the lip
            row.append(q)
        rows.append(row)
    mb = MB("moustache")
    mb.grid(rows, "MOUST")
    ob = mb.build(c, orient=lambda q: (q.x, -0.06, q.z))
    print("MOUSTACHE tris", sum(len(p.vertices) - 2 for p in ob.data.polygons))
    return ob


# ---------------------------------------------------------------------------------------------
# head, neck, hands, hair, eyes, boater, moustache
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
    above_v = np.array([p[2] > z_hair(az_of(p)) for p in co]) & (co[:, 2] > 1.45)
    above_v &= B.ws(["ears"]) < 0.3 if "ears" in B.w else True
    vm = np.zeros(len(co), bool)
    for poly in body.data.polygons:
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
    for it in range(3):
        new = {}
        for v in bm_.verts:
            # (npc_grocer_boy) the edge is relaxed lightly so the irregular tufts survive
            if v.is_boundary and (it == 0 or az_of(v.co) < 82 or (v.co.z < 1.56 and az_of(v.co) > 110)):
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
        t = min(0.0078, max(0.0028, 0.45 * d_short))          # short back and sides, neat
        az_ = az_of(p)
        if az_ < 85:                                          # temples: close to the skull
            t = min(t, 0.0042)
        above = p.z - z_hair(az_of(p))
        # thins out toward the edge (round 1: a long, rounded taper at the temples, no step)
        taper = min(1.0, max(0.0, above / (0.022 if az_ < 85 else 0.014))) ** (1.3 if az_ < 85 else 0.7)
        t = 0.0012 + (t - 0.0012) * taper
        if v.index in bnd:
            t = 0.0009
        v.co = p + n * t
    hm.update()
    # ---- high-res head (bake source) + low-res head
    neck_r = np.hypot(co[:, 0] / 0.066, (co[:, 1] - 0.0) / 0.077)
    head_mask = (co[:, 2] > 1.398) & (np.abs(co[:, 0]) < 0.115) & ((co[:, 2] > 1.47) | (neck_r < 1.0))
    hi = keep_faces(body, "HI_head", head_mask, work)
    # (npc_grocer_boy round 1) a soft 1.5 cm fade of short hair below the hairline, broken up in
    # the shader - no hard skullcap edge
    at = hi.data.attributes.new("hairzone", "FLOAT", "POINT")
    at.data.foreach_set("value", [min(1.0, max(0.0, (v.co.z - z_hair(az_of(v.co)) + 0.015) / 0.017))
                                  for v in hi.data.vertices])
    # ---- the boater sits on the hair; hair and scalp wholly inside its crown are never seen
    hat = build_hat(main, [hair, body])
    bm_ = bmesh.new(); bm_.from_mesh(hm)
    kill = [f for f in bm_.faces if all(v.co.z > hat_band_z(hat_phi(v.co)) + 0.014 for v in f.verts)]
    bmesh.ops.delete(bm_, geom=kill, context="FACES")
    bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if not v.link_faces], context="VERTS")
    bm_.to_mesh(hm); bm_.free()
    decimate_to(hair, HAIR_TRIS)
    hbvh = BVHTree.FromObject(hair, bpy.context.evaluated_depsgraph_get())
    lo = keep_faces(hi, "PART_head", np.ones(len(hi.data.vertices), bool), main)
    bm_ = bmesh.new(); bm_.from_mesh(lo.data)
    covered = set()
    for v in bm_.verts:
        if v.co.z - z_hair(az_of(v.co)) < 0.008:
            continue
        under_hat = v.co.z > hat_band_z(hat_phi(v.co)) + 0.010
        loc, nrm_, idx, d = hbvh.find_nearest(v.co)
        if under_hat or (loc is not None and d < 0.016 and (loc - v.co).dot(v.normal) > 0
                         and hbvh.ray_cast(v.co + v.normal * 0.0005, v.normal, 0.03)[0] is not None):
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
    # (npc_shopper) neck skin that pokes through, or lies within 4 mm under, the tall wing collar
    # goes 4 mm under it (no skin specks along the collar's top edge)
    ct = BVHTree.FromObject(bpy.data.objects["PART_front"], bpy.context.evaluated_depsgraph_get())
    st = BVHTree.FromObject(bpy.data.objects["PART_shirt"], bpy.context.evaluated_depsgraph_get())
    bm_ = bmesh.new(); bm_.from_mesh(lo.data); bm_.normal_update()
    pushed = 0
    for v in bm_.verts:
        if v.co.z > 1.53 or v.co.z < 1.40:
            continue
        n = v.normal
        h = ct.ray_cast(v.co - n * 0.02, n, 0.026)
        if h[0] is None or (h[0] - v.co).dot(n) >= 0.004:
            h = st.ray_cast(v.co - n * 0.02, n, 0.026)
        if h[0] is not None and (h[0] - v.co).dot(n) < 0.004:
            v.co = h[0] - n * 0.004
            pushed += 1
    bm_.to_mesh(lo.data); bm_.free()
    print("SKIN pushed under the collar", pushed)
    at2 = lo.data.attributes.new("hairdist", "FLOAT", "POINT")
    at2.data.foreach_set("value", [v.co.z - z_hair(az_of(v.co)) for v in lo.data.vertices])
    # ---- moustache (projected on the full-resolution face)
    moust = build_moustache(main, [hi])
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
    for ob, mname in ((hair, "HAIR"), (lo, "SKIN"), (hands, "SKIN"), (eyes, "EYE")):
        ob.data.materials.clear()
        for m in MATS:
            ob.data.materials.append(bpy.data.materials.get("SRC_" + m) or bpy.data.materials.new("SRC_" + m))
        ob.data.polygons.foreach_set("material_index", [MATS.index(mname)] * len(ob.data.polygons))
        for p in ob.data.polygons:
            p.use_smooth = True
    print("SKIN parts", {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons)
                         for o in (hair, lo, hands, eyes, hat, moust)})
    src["Eyebrows"].hide_render = True
    src["Eyebrows"].hide_set(True)
    hi.hide_set(True); hands_hi.hide_set(True)
    return dict(hair=hair, head=lo, hands=hands, eyes=eyes, hat=hat, moustache=moust, head_hi=hi, hands_hi=hands_hi)


# ---------------------------------------------------------------------------------------------
# skinning (as npc_rittenhouse.stage_weights; rigid on the Head: eyes, boater, moustache)
# ---------------------------------------------------------------------------------------------
RIGID = ("eyes", "hat", "moustache")


def stick_islands(ob, max_verts=400):
    """Lapels, pocket flaps, welt, handkerchief and buttons are separate islands lying a few mm
    on the coat: give each of their vertices exactly the (final, smoothed) weights of the coat
    surface under it, so in motion they move with it and never sink into it (jagged dark
    slits at the pockets / lapel edges)."""
    from mathutils.bvhtree import BVHTree
    me = ob.data
    nv = len(me.vertices)
    adj = [[] for _ in range(nv)]
    for e in me.edges:
        a, b = e.vertices
        adj[a].append(b); adj[b].append(a)
    isl = [-1] * nv
    sizes = []
    for i0 in range(nv):
        if isl[i0] >= 0:
            continue
        k = len(sizes); stack = [i0]; isl[i0] = k; n = 0
        while stack:
            i = stack.pop(); n += 1
            for j in adj[i]:
                if isl[j] < 0:
                    isl[j] = k; stack.append(j)
        sizes.append(n)
    main = int(np.argmax(sizes))
    faces = [p for p in me.polygons if isl[p.vertices[0]] == main]
    bvh = BVHTree.FromPolygons([v.co for v in me.vertices], [p.vertices for p in faces])
    names = {vg.index: vg.name for vg in ob.vertex_groups}
    W = [{names[g.group]: g.weight for g in v.groups} for v in me.vertices]
    n_set = 0
    for v in me.vertices:
        if isl[v.index] == main or sizes[isl[v.index]] > max_verts:
            continue
        loc, nrm, fi, d = bvh.find_nearest(v.co)
        if loc is None:
            continue
        f = faces[fi]
        acc = {}
        ws = [1.0 / max((me.vertices[i].co - loc).length, 1e-5) for i in f.vertices]
        tot = sum(ws)
        for i, w_ in zip(f.vertices, ws):
            for b, w in W[i].items():
                acc[b] = acc.get(b, 0.0) + w * w_ / tot
        for g in list(v.groups):
            ob.vertex_groups[g.group].remove([v.index])
        for b, w in acc.items():
            if w > 1e-4:
                ob.vertex_groups[b].add([v.index], w, "REPLACE")
        n_set += 1
    print("JACKET islands stuck to the coat:", len(sizes) - 1, "islands,", n_set, "vertices")


def leg_ring_weights(ob, arm, crotch):
    """Each leg tube moves as rigid rings: a vertex's weights depend only on its height and side
    (thigh above the knee, calf below, pelvis rising toward the top), never on which bit of skin
    lies nearest. The skin-nearest weights let the flattened inner walls fold through each other
    (jagged 'torn seams' between the thighs, seen from behind)."""
    at = ob.data.attributes.get("legside")
    if at is None:
        return
    sides = np.zeros(len(ob.data.vertices), np.int32); at.data.foreach_get("value", sides)
    for b in ("pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r"):
        if b not in ob.vertex_groups:
            ob.vertex_groups.new(name=b)
    gid = {vg.name: vg for vg in ob.vertex_groups}
    for v in ob.data.vertices:
        sg = sides[v.index]
        if sg == 0:
            continue
        s_ = "l" if sg > 0 else "r"
        knee = arm.data.bones[f"calf_{s_}"].head_local.z
        z = v.co.z
        wc = smooth01((knee + 0.05 - z) / 0.10)
        wp = 0.55 * smooth01((z - (crotch - 0.07)) / 0.15)
        new = {"pelvis": wp, f"thigh_{s_}": (1 - wc) * (1 - wp), f"calf_{s_}": wc * (1 - wp)}
        for g in list(v.groups):
            gid_name = ob.vertex_groups[g.group].name
            if gid_name not in new:
                ob.vertex_groups[g.group].remove([v.index])
        for k, w in new.items():
            if w > 1e-4:
                gid[k].add([v.index], w, "REPLACE")
            else:
                gid[k].remove([v.index])
    print("LEGS rigid-ring weights set")
CROTCH_SHARED = {"pelvis": 0.40, "thigh_l": 0.30, "thigh_r": 0.30}


def seat_weights(ob, crotch):
    """Round 1: the seat piece's lower part follows the thighs with exactly the share the leg
    rings have at the same height (leg_ring_weights), split left/right across the middle (the
    fly and seat bridge between the thighs take both); its upper part keeps the coat's weights."""
    for b in ("pelvis", "thigh_l", "thigh_r"):
        if b not in ob.vertex_groups:
            ob.vertex_groups.new(name=b)
    names = {vg.index: vg.name for vg in ob.vertex_groups}
    gid = {vg.name: vg for vg in ob.vertex_groups}
    for v in ob.data.vertices:
        p = v.co
        f = smooth01((crotch + 0.10 - p.z) / 0.06)
        if f <= 0:
            continue
        s_ = 1.0 - 0.55 * smooth01((p.z - (crotch - 0.07)) / 0.15)
        sx = max(-1.0, min(1.0, p.x / 0.04))
        tgt = {"pelvis": 1.0 - s_, "thigh_l": s_ * (0.5 + 0.5 * sx), "thigh_r": s_ * (0.5 - 0.5 * sx)}
        old = {names[g.group]: g.weight for g in v.groups}
        tot = sum(old.values()) or 1.0
        new = {k: (1 - f) * w / tot for k, w in old.items()}
        for k, w in tgt.items():
            new[k] = new.get(k, 0.0) + f * w
        for k, w in new.items():
            if w > 1e-4:
                gid[k].add([v.index], w, "REPLACE")
            else:
                gid[k].remove([v.index])


def share_crotch(ob, crotch):
    """The inner sides of the two leg tubes near the crotch follow one shared blend (pelvis +
    both thighs), as a real crotch seam does: they move together instead of cutting into each
    other front-to-back when the legs part (the reviewed 'torn seams' / 'drop crotch')."""
    names = {vg.index: vg.name for vg in ob.vertex_groups}
    for b in CROTCH_SHARED:
        if b not in ob.vertex_groups:
            ob.vertex_groups.new(name=b)
    gid = {vg.name: vg for vg in ob.vertex_groups}
    n = 0
    for v in ob.data.vertices:
        p = v.co
        f = smooth01((0.050 - abs(p.x)) / 0.035) * smooth01((p.z - (crotch - 0.15)) / 0.08)
        if f <= 0:
            continue
        old = {names[g.group]: g.weight for g in v.groups}
        tot = sum(old.values()) or 1.0
        new = {k: (1 - f) * w / tot for k, w in old.items()}
        for k, w in CROTCH_SHARED.items():
            new[k] = new.get(k, 0.0) + f * w
        for k, w in new.items():
            gid[k].add([v.index], w, "REPLACE")
        n += 1
    print("CROTCH shared blend on", n, "trouser vertices")


def stage_weights(parts, donor, arm, crotch):
    sh_x = abs(arm.data.bones["upperarm_l"].head_local.x)
    order = ["jacket"] + [k for k in parts if k != "jacket"]
    for name in order:
        ob = parts[name]
        if name in RIGID:
            transfer_weights(ob, donor, arm, rigid="Head")
            m = ob.modifiers.new("Armature", "ARMATURE"); m.object = arm
            continue
        if name == "gusset":
            set_weights(ob, lambda p: dict(CROTCH_SHARED))
        else:
            transfer_weights(ob, parts["jacket"] if name in ("front", "shirt", "collar") else donor, arm)
        if name in ("trousers", "seat"):
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
            if name == "seat":
                seat_weights(ob, crotch)
            for side, sg in (("l", 1.0), ("r", -1.0)) if name == "trousers" else ():
                blend_to_bone(ob, f"thigh_{side}", lambda p, sg=sg: 0.0 if p.x * sg <= 0.0 else
                              0.8 * min(1.0, max(0.0, (crotch + 0.07 - p.z) / 0.06))
                              * min(1.0, max(0.0, (p.z - 0.45) / 0.15)))
            if SHARE and name == "trousers":
                share_crotch(ob, crotch)
            if name == "trousers":
                leg_ring_weights(ob, arm, crotch)
        if name == "collar":
            blend_to_bone(ob, "spine_03", lambda p: 0.85)
        if name == "front":
            # the wing collar and bow tie ride on the neck
            nz = lambda p: (p.z > 1.41 and math.hypot(p.x, p.y + 0.01) < 0.085)
            blend_to_bone(ob, "neck_01", lambda p: 0.7 if nz(p) else 0.0)
        if name == "sleeves":
            for side, sg in (("l", 1.0), ("r", -1.0)):
                blend_to_bone(ob, f"clavicle_{side}",
                              lambda p, sg=sg: 0.0 if p.x * sg < 0 else
                              0.85 * min(1.0, max(0.0, (sh_x + 0.05 - p.x * sg) / 0.09)))
        if name == "jacket":
            def collar_f(p):
                rr = math.hypot(p.x, p.y + 0.005)
                return 0.85 * min(1.0, max(0.0, (p.z - 1.37) / 0.03)) * min(1.0, max(0.0, (0.15 - rr) / 0.04))
            blend_to_bone(ob, "spine_03", collar_f)
            blend_to_bone(ob, "pelvis", lambda p: min(1.0, max(0.0, (crotch + 0.12 - p.z) / 0.14)) * 0.85)

            def front_f(p):
                if p.y > -0.03 or p.z > 1.07:
                    return 0.0
                return 0.75 * min(1.0, (1.07 - p.z) / 0.07) * min(1.0, (-0.03 - p.y) / 0.04)
            blend_to_bone(ob, "spine_01", lambda p: 0.5 * front_f(p) if p.z > 0.95 else 0.0)
            blend_to_bone(ob, "pelvis", front_f)
        finish_weights(ob, smooth=0 if name in ("head", "hands", "hair") else (4 if name == "jacket" else 2))
        if name == "jacket":
            stick_islands(ob)
            finish_weights(ob, smooth=0)          # back to <= 4 influences, normalised
        m = ob.modifiers.new("Armature", "ARMATURE")
        m.object = arm
    for ob in parts.values():
        ob.parent = arm
        ob.matrix_parent_inverse = arm.matrix_world.inverted()


# ---------------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------------
def build_all():
    new_file()
    with win_ctx():
        arm = stage_rig_w()
        src = stage_human()
        head_landmarks(src["Body"], src["Eyes"])
        main = bpy.data.collections[COLL]
        G = GarmentsW(src["Body"], arm)
        parts = dict(jacket=G.build_jacket(main), collar=G.build_collar(main))
        parts["sleeves"], parts["cuffs"] = G.build_sleeves(main)
        parts["front"] = G.build_front(main)
        parts["shirt"] = G.build_shirt(main)
        parts["trousers"], parts["shoes"] = G.build_legs(main)
        parts["seat"] = G.seat
        parts["gusset"] = G.gusset
        sk = stage_skin(src, G)
        for k in ("hair", "head", "hands", "eyes", "hat", "moustache"):
            parts[k] = sk[k]
        # (npc_grocer_boy) zero-area faces get wild UV islands in smart-project: dissolve them
        for k, ob in parts.items():
            if k in ("head", "hands", "eyes"):
                continue
            bm_ = bmesh.new(); bm_.from_mesh(ob.data)
            n0 = len(bm_.faces)
            bmesh.ops.dissolve_degenerate(bm_, dist=2e-4, edges=bm_.edges[:])
            bmesh.ops.delete(bm_, geom=[f for f in bm_.faces if f.calc_area() < 1e-8], context="FACES")
            # slivers (pinched rows, e.g. the waistcoat's shoulder edge under the coat): smart-project
            # stretches them into long crossed UV strips that overlap other islands
            sl = [f for f in bm_.faces if k not in ("hair", "moustache", "hat") and f.calc_area() < 3e-6 and max(e.calc_length() for e in f.edges) > 0.004
                  and f.calc_area() / max(e.calc_length() for e in f.edges) ** 2 < 0.08]
            bmesh.ops.delete(bm_, geom=sl, context="FACES")
            bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if not v.link_faces], context="VERTS")
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


if not globals().get("WILLIAMSON_LIB_ONLY"):
    PARTS = build_all()
