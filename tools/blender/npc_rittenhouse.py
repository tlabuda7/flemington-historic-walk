"""
Albert H. Rittenhouse, cashier of the Hunterdon County National Bank (90-94 Main), c. 1920 -
geometry + rig build.

Run inside Blender (MPFB 2.0.18 extension installed, MakeHuman CC0 system-asset pack loaded):
    exec(open(r"<project>/tools/blender/npc_rittenhouse.py").read())

Same pipeline as John B. Pickell: this script loads tools/blender/npc_pickell.py as a library
(PICKELL_LIB_ONLY) and overrides only what makes Rittenhouse a different man:
  * MakeHuman male about 55 years old (age 0.73), heavier (weight 0.70, less muscle), with face
    targets for a longer, heavier older face (oval/rectangular head, jowls, eye bags, a longer
    nose with a slight hump, a firmer chin); grey eyes; eyebrow002.
  * Hair: thinner shell, receding at the temples and higher at the front, combed back with a
    side parting on his RIGHT (Pickell: left); iron grey (colour in the bake). Clean-shaven.
  * Round wire spectacles (gold-filled) modelled by script, rigid on the Head bone.
  * Same 1920 three-piece suit construction (sack coat, waistcoat, collar, tie, trousers with
    turn-ups, oxfords, watch chain); no tape measure and no pencil.
  * Idle / Talk exactly as Pickell's round-1 fixes (narrow stance, feet locked, level gaze,
    relaxed fingers).
  * Final height 1.69 m: the bake script scales the finished rig + mesh uniformly (0.9826) just
    before export, so all object-space bake masks stay valid.
Materials/atlas/AO/export: npc_rittenhouse_bake.py.  Previews: npc_rittenhouse_preview.py.

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
BLEND = os.path.join(ROOT, r"assets\models\source\npc-rittenhouse.blend")
COLL = "NPC_Rittenhouse"
WORK = "NPC_Rittenhouse_Work"
RIG_NAME = "Rittenhouse_Rig"
MACRO = dict(gender=1.0, age=0.73, muscle=0.42, weight=0.70, proportions=0.6, height=0.45)
# MakeHuman age slider: 0.5 = 25 y, 1.0 = 90 y  ->  55 y = 0.5 + 30/65*0.5 = 0.73
PROXIES = (("Eyes", r"eyes\low-poly\low-poly.mhclo"),
           ("Eyebrows", r"eyebrows\eyebrow002\eyebrow002.mhclo"),
           ("Hair", r"hair\short02\short02.mhclo"))
MH_TARGETS = os.path.join(os.environ["APPDATA"], r"Blender Foundation\Blender\5.2\extensions"
                          r"\user_default\mpfb\data\targets")
FACE_TARGETS = [            # (relative path, weight)
    (r"head\head-oval.target.gz", 0.45),
    (r"head\head-rectangular.target.gz", 0.30),
    (r"head\head-fat-incr.target.gz", 0.35),
    (r"head\head-scale-vert-incr.target.gz", 0.20),
    (r"nose\nose-hump-incr.target.gz", 0.45),
    (r"nose\nose-scale-vert-incr.target.gz", 0.35),
    (r"nose\nose-point-down.target.gz", 0.25),
    (r"nose\nose-scale-horiz-decr.target.gz", 0.25),
    (r"chin\chin-prominent-incr.target.gz", 0.30),
    (r"eyes\l-eye-bag-incr.target.gz", 0.45),
    (r"eyes\r-eye-bag-incr.target.gz", 0.45),
    (r"mouth\mouth-scale-horiz-decr.target.gz", 0.20),
    (r"mouth\mouth-angles-down.target.gz", 0.30),
]
HAIR_THIN = 0.72            # hair shell thickness factor (thinner than Pickell's)
PART_X = -0.030             # parting on his right (-x)


def stage_rig_r():
    arm = stage_rig()
    arm.name = arm.data.name = RIG_NAME
    return arm


def stage_human():
    """As npc_pickell.stage_human, plus the face targets (loaded before the rig is fitted)."""
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


def arm_global():
    return bpy.data.objects[RIG_NAME]


def head_landmarks(body, eyes):
    """Print the head measurements the hairline / collar constants depend on."""
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
# hairline: receding at the temples, front a touch higher than Pickell's (same azimuth scheme:
# 0 = forehead centre, 180 = nape; ear az 76..101)
# ---------------------------------------------------------------------------------------------
HAIRLINE = [(0, 1.674), (12, 1.677), (24, 1.686), (34, 1.694), (44, 1.692), (54, 1.672), (62, 1.640),
            (68, 1.610), (74, 1.594), (79, 1.617), (98, 1.619), (104, 1.590), (115, 1.574), (130, 1.562),
            (150, 1.548), (165, 1.538), (180, 1.535)]


# ---------------------------------------------------------------------------------------------
# garments: as Pickell, accessories = watch chain + small fob only (no tape measure)
# ---------------------------------------------------------------------------------------------
class GarmentsR(Garments):
    def build_accessories(self, c):
        W = self.W
        mb = MB("accessories")
        z_end, sag = 1.006, 0.017
        n = 15
        pts = []
        for k in range(n):
            u = k / (n - 1)
            x = -0.085 + 0.170 * u
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
        f = W.surf(zc - 0.022, 0.0, 0.0040)                            # small fob below it
        mb.disc(f, nrm, 0.0075, "GOLD", n=8, depth=0.0025)
        link = [W.surf(zc - 0.001, 0.0, 0.0036), W.surf(zc - 0.015, 0.0, 0.0038)]
        mb.grid([[q + Vector((dx, 0, 0)) for q in link] for dx in (-0.0012, 0.0012)], "GOLD")
        return mb.build(c, orient=self.ref_torso(0.03))


# ---------------------------------------------------------------------------------------------
# spectacles: round gold-filled wire frames, saddle bridge, riding-bow temples round the ears
# ---------------------------------------------------------------------------------------------
if "WIRE" not in MATS:
    MATS.append("WIRE")


def tube(mb, path, r, mat, sides=4, closed_loop=False):
    rows = []
    n = len(path)
    for k in range(n):
        if closed_loop:
            t = (path[(k + 1) % n] - path[(k - 1) % n]).normalized()
        else:
            t = (path[min(k + 1, n - 1)] - path[max(k - 1, 0)]).normalized()
        n1 = t.cross(Vector((0, 0, 1)))
        if n1.length < 1e-4:
            n1 = t.orthogonal()
        n1.normalize(); n2 = t.cross(n1)
        rows.append([path[k] + r * (math.cos(TAU * j / sides + math.pi / 4) * n1
                                    + math.sin(TAU * j / sides + math.pi / 4) * n2) for j in range(sides)])
    if closed_loop:
        rows.append(rows[0])
    return mb.grid(rows, mat, closed=True)


def build_spectacles(body, eyes, c, hair=None):
    from mathutils.bvhtree import BVHTree
    ec = np.array([v.co[:] for v in eyes.data.vertices])
    ears = body.vertex_groups["ears"].index
    ear_v = {1: [], -1: []}
    for v in body.data.vertices:
        if any(g.group == ears and g.weight > 0.5 for g in v.groups):
            ear_v[1 if v.co.x > 0 else -1].append(v.co[:])
    bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    mb = MB("specs")
    a, b = SPEC_A, SPEC_B
    tilt = math.radians(8)              # pantoscopic tilt (bottom closer to the cheeks)
    rim = 0.00105
    hinge, inner = {}, {}
    for sg in (1, -1):
        e = ec[ec[:, 0] * sg > 0]
        cx, cz = float(e[:, 0].mean()), float(e[:, 2].mean())
        cy = float(e[:, 1].min()) - SPEC_FWD
        C = Vector((cx + sg * 0.002, cy, cz + 0.002))
        ring = []
        N = 16
        for k in range(N):
            th = TAU * k / N
            dx, dz = a * math.cos(th), b * math.sin(th)
            ring.append(C + Vector((dx, dz * math.sin(tilt), dz * math.cos(tilt))))
        tube(mb, ring, rim, "WIRE", closed_loop=True)
        hinge[sg] = C + Vector((sg * a, 0.0, 0.004))
        inner[sg] = C + Vector((-sg * a, 0.0, 0.003))
    br = []                               # saddle bridge over the nose
    for k in range(7):
        u = k / 6
        p = inner[1].lerp(inner[-1], u)
        p.z += 0.0055 * math.sin(math.pi * u)
        p.y -= 0.0015 * math.sin(math.pi * u)
        br.append(p)
    tube(mb, br, rim, "WIRE")
    # temples (reviewer round 1): from the hinge each arm bends straight back and follows the side
    # of the head SPEC_GAP off the outermost surface (skin or hair shell), over the top of the
    # ear, then bows down behind the ear against the skull - no free ends in the air
    hbvh = BVHTree.FromObject(hair, bpy.context.evaluated_depsgraph_get()) if hair else None

    def side_x(sg, y, z, inside_out=False):
        """Outermost |x| of skin / hair at (y, z) on side sg (None if nothing there)."""
        best = None
        for tree in (bvh, hbvh):
            if tree is None:
                continue
            if inside_out:
                hit = tree.ray_cast(Vector((0.0, y, z)), Vector((sg, 0.0, 0.0)), 0.3)
            else:
                hit = tree.ray_cast(Vector((sg * 0.3, y, z)), Vector((-sg, 0.0, 0.0)), 0.3)
            if hit[0] is not None:
                ax = abs(hit[0].x)
                best = ax if best is None else max(best, ax)
        return best

    for sg in (1, -1):
        E = np.array(ear_v[sg])
        ear_top = float(E[:, 2].max()); ear_front = float(E[:, 1].min()); ear_back = float(E[:, 1].max())
        h = hinge[sg]
        z_ear = ear_top + 0.002
        pts = [h]
        # along the temple to the front of the ear (outside-in: the first surface met)
        for u in np.linspace(0.0, 1.0, 8):
            y = h.y + 0.006 + (ear_front + 0.004 - (h.y + 0.006)) * u
            z = h.z + (z_ear - h.z) * (u ** 0.8)
            sx = side_x(sg, y, z)
            if sx is None:
                continue
            pts.append(Vector((sg * (sx + SPEC_GAP), y, z)))
        # over the ear and down behind it (inside-out: the skull, not the ear)
        for ang in (0.0, 0.35, 0.8, 1.3):
            y = ear_front + 0.012 + (ear_back - ear_front - 0.012) * math.sin(ang * 0.9) if ang > 0 \
                else ear_front + 0.012
            z = z_ear - 0.028 * (1 - math.cos(ang)) / (1 - math.cos(1.3))
            sx = side_x(sg, y, z, inside_out=True)
            if sx is None:
                continue
            pts.append(Vector((sg * (sx + SPEC_GAP), y, z)))
        # a short straight end piece at the hinge so the bend is clean
        if len(pts) > 1:
            d = pts[1] - h
            pts.insert(1, h + Vector((0.0, min(0.004, d.y * 0.5), 0.0)))
        tube(mb, pts, rim * 0.95, "WIRE")
        print("SPECS temple", sg, "points", len(pts), "max |x|", round(max(abs(p.x) for p in pts), 4))
    ob = mb.build(c)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


SPEC_A, SPEC_B, SPEC_FWD = 0.0205, 0.0170, 0.0135
SPEC_GAP = 0.004            # temple arms 4 mm off the skin / hair


# ---------------------------------------------------------------------------------------------
# head, neck, hands, hair, eyes (as npc_pickell.stage_skin: thinner receding hair parted on his
# right, clean-shaven, spectacles instead of the pencil)
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
    part_x = PART_X
    for v in hm.vertices:
        p = v.co.copy()
        n = nrm[v.index]
        hit = pbvh.ray_cast(p + n * 0.0005, n, 0.05)
        d_short = hit[3] if hit[0] is not None else 0.004
        t = min(0.0080, max(0.0024, 0.45 * d_short * HAIR_THIN))
        above = p.z - z_hair(az_of(p))
        taper = min(1.0, max(0.0, above / 0.010)) ** 0.6
        t = 0.0014 + (t - 0.0014) * taper
        if v.index in bnd:
            t = 0.0009
        if p.z > 1.668 and p.y < 0.04:               # parting groove (his right)
            g = math.exp(-((p.x - part_x) / 0.0050) ** 2)
            t = max(0.0011, t - 0.0035 * g)
            if p.x > part_x:                         # combed-over side a touch fuller
                t += 0.0010 * min(1.0, (p.x - part_x) / 0.03)
        v.co = p + n * t
    hm.update()
    decimate_to(hair, HAIR_TRIS)
    # ---- high-res head (bake source) + low-res head
    neck_r = np.hypot(co[:, 0] / 0.066, (co[:, 1] - 0.0) / 0.077)
    head_mask = (co[:, 2] > 1.398) & (np.abs(co[:, 0]) < 0.115) & ((co[:, 2] > 1.47) | (neck_r < 1.0))
    hi = keep_faces(body, "HI_head", head_mask, work)
    at = hi.data.attributes.new("hairzone", "FLOAT", "POINT")
    # (+4 mm: no skin specks in the notches of the receded hairline)
    at.data.foreach_set("value", [min(1.0, max(0.0, (v.co.z - z_hair(az_of(v.co)) + 0.004) / 0.006))
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
    # the decimated scalp can poke through the thin hair shell at the receded corners: sink it
    # 2.5 mm under the hair (fading in from 2 mm below the hairline)
    bm_ = bmesh.new(); bm_.from_mesh(lo.data); bm_.normal_update()
    for v in bm_.verts:
        t = min(1.0, max(0.0, (v.co.z - z_hair(az_of(v.co)) + 0.002) / 0.004))
        if t > 0:
            v.co -= v.normal * 0.0025 * t
    bm_.to_mesh(lo.data); bm_.free()
    # reviewer round 1: signed height above the hairline (m) for the atlas clean-up of the
    # hairline in npc_rittenhouse_bake.paint_hairline
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
    specs = build_spectacles(body, eyes, main, hair=hair)
    print("SKIN parts", {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons)
                         for o in (hair, lo, hands, eyes, specs)})
    src["Eyebrows"].hide_render = True
    src["Eyebrows"].hide_set(True)
    hi.hide_set(True); hands_hi.hide_set(True)
    return dict(hair=hair, head=lo, hands=hands, eyes=eyes, specs=specs, head_hi=hi, hands_hi=hands_hi)


# ---------------------------------------------------------------------------------------------
# skinning (as npc_pickell.stage_weights; rigid on the Head: eyes, spectacles)
# ---------------------------------------------------------------------------------------------
RIGID = ("specs", "eyes")


def stage_weights(parts, donor, arm, crotch):
    sh_x = abs(arm.data.bones["upperarm_l"].head_local.x)
    order = ["jacket"] + [k for k in parts if k != "jacket"]
    for name in order:
        ob = parts[name]
        if name in RIGID:
            transfer_weights(ob, donor, arm, rigid="Head")
            continue
        transfer_weights(ob, parts["jacket"] if name in ("front", "accessories", "collar") else donor, arm)
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
        if name == "collar":
            blend_to_bone(ob, "spine_03", lambda p: 0.85)
        if name == "front":
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
        m = ob.modifiers.new("Armature", "ARMATURE")
        m.object = arm
    for name in RIGID:
        m = parts[name].modifiers.new("Armature", "ARMATURE"); m.object = arm
    for ob in parts.values():
        ob.parent = arm
        ob.matrix_parent_inverse = arm.matrix_world.inverted()


# ---------------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------------
def build_all():
    new_file()
    with win_ctx():
        arm = stage_rig_r()
        src = stage_human()
        head_landmarks(src["Body"], src["Eyes"])
        main = bpy.data.collections[COLL]
        G = GarmentsR(src["Body"], arm)
        parts = dict(jacket=G.build_jacket(main), collar=G.build_collar(main))
        parts["sleeves"], parts["cuffs"] = G.build_sleeves(main)
        parts["front"] = G.build_front(main)
        parts["trousers"], parts["shoes"] = G.build_legs(main)
        parts["accessories"] = G.build_accessories(main)
        sk = stage_skin(src, G)
        for k in ("hair", "head", "hands", "eyes", "specs"):
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


if not globals().get("RITTENHOUSE_LIB_ONLY"):
    PARTS = build_all()
