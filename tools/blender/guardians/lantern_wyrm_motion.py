"""The Lantern Wyrm's motion: how it lies, rears, strikes, leaps and slithers, solved here and played by the game (run inside Blender).

A pose is {bone: (pitch, yaw, roll) in degrees} and the hips' (lift, slide) in studs, in the guardian's own axes, each bone's turn on top of
its parent's, exactly as the game's joints work (GuardianAnim: Bone.Transform = rest^-1 * turn * rest).

The wyrm has no limbs: the pose of its 31 spine bones is the shape of a curve, so a pose is AUTHORED as a curve and solved into turns:
  - the NECK (eight bones, forward from the hips) by a pitch and a yaw profile (five control values each, spline-interpolated over the
    bones: a swan's S is a pitch that goes steep, over the vertical and forward again);
  - the TRUNK and TAIL (twenty-two bones, back from the hips) by a CURVATURE profile along the arc (degrees turned per stud: a coil is a
    constant curvature that tightens, a lash is a wave) laid on the ground (each joint's height follows the body's own radius so the
    belly rests on the floor) with lift added where it rears up; the chord of each bone is exactly its length, so nothing stretches;
  - the head, jaw and lantern's stalk by their own turns; the mane-frill by an openness (0 shut flat, 1 as bound, more flared wide).
Between two keys every number (a profile's control value, a phase, an opening) moves along the later key's ease, each bone of a chain
after its own lag, so a blow runs down the body as a wave: the overlap that gives a move weight. Each bone's turn is read from the pose
built a moment earlier for that bone, the way an animator offsets a chain.

    import lantern_wyrm_motion as M
    pose, shift = M.solve(M.state_spec("Guardian"))
"""
import math

from mathutils import Matrix, Quaternion, Vector

import lantern_wyrm_bones as B
from lantern_wyrm_bones import BONES, joints
from lantern_wyrm_curve import frames as _frames

V = Vector
RAD = math.radians
DEG = math.degrees


# ---------------------------------------------------------------- rotations
def mat(a):
    """Rx(pitch) Ry(yaw) Rz(roll), as CFrame.Angles."""
    return Matrix.Rotation(RAD(a[0]), 3, "X") @ Matrix.Rotation(RAD(a[1]), 3, "Y") @ Matrix.Rotation(RAD(a[2]), 3, "Z")


def euler(m):
    e = m.to_euler("ZYX")
    return (DEG(e.x), DEG(e.y), DEG(e.z))


def frame(a, b):
    """The rotation whose first axis is a and whose second is (b made square to a)."""
    a = V(a).normalized()
    b = V(b) - a * V(b).dot(a)
    b = b.normalized()
    return Matrix((a, b, a.cross(b))).transposed()


def rb_rot(m):
    """A rotation in the guardian's axes, as Blender's."""
    C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    return C @ m @ C.transposed()


def near_angle(angle, ref):
    return angle + 360 * round((ref - angle) / 360)


def slerp_euler(a, b, u):
    qa, qb = mat(a).to_quaternion(), mat(b).to_quaternion()
    if qa.dot(qb) < 0:
        qb = -qb
    axis, angle = qa.rotation_difference(qb).to_axis_angle()
    return euler((qa @ Quaternion(axis, angle * u)).to_matrix())


# ---------------------------------------------------------------- forward kinematics
CHILDREN = {}
for _n, (_p, _h, _t) in BONES.items():
    CHILDREN.setdefault(_p, []).append(_n)


def fk(pose, shift=(0.0, 0.0)):
    """{bone: (accumulated rotation, head position)} for a pose; shift = the hips' (lift, slide)."""
    out = {}

    def walk(name, parent):
        pa, head, tail = BONES[name]
        r = mat(pose.get(name, (0, 0, 0)))
        if parent is None:
            world, at = r, V(head)
        else:
            pr, pp = out[parent]
            world = pr @ r
            at = pp + pr @ (V(head) - V(BONES[parent][1]))
            if name == "Hips":
                at = at + V((0, shift[0], shift[1]))
        out[name] = (world, at)
        for child in CHILDREN.get(name, []):
            walk(child, name)

    walk("Root", None)
    return out


def tip(state, name):
    r, at = state[name]
    return at + r @ (V(BONES[name][2]) - V(BONES[name][1]))


def rest_dir(name):
    return (V(BONES[name][2]) - V(BONES[name][1])).normalized()


# ---------------------------------------------------------------- curves into turns
def spline(vals, t):
    """Catmull-Rom through evenly spaced control values at t in 0..1."""
    n = len(vals)
    x = max(0.0, min(1.0, t)) * (n - 1)
    i = min(int(x), n - 2)
    u = x - i
    p0, p1, p2, p3 = vals[max(i - 1, 0)], vals[i], vals[i + 1], vals[min(i + 2, n - 1)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def solve_chain(names, points, parent_T, rest, up0=(0, 1, 0)):
    """The turns that lay the bones `names` through the joint positions `points` (len(names) + 1). The face of each bone (rest: up) is carried
    along with no twist: `rest` is the chain's rest direction. Returns ({bone: euler}, the last bone's accumulated rotation)."""
    pose, pr = {}, parent_T
    accum = {}
    up = V(up0)
    prev = None
    rf = frame(rest, (0, 1, 0)).inverted()
    for i, n in enumerate(names):
        d = (points[i + 1] - points[i]).normalized()
        if prev is not None:
            up = prev.rotation_difference(d) @ up
        up = up - d * up.dot(d)
        if up.length < 1e-4:
            up = V((0, 0, 1)) - d * d.z
        up.normalize()
        want = frame(d, up)
        e = euler(pr.inverted() @ want @ rf)
        pose[n] = e
        pr = pr @ mat(e)
        accum[n] = pr
        prev = d
    return pose, accum


def trunk_points(spec, y0, slide):
    """Joint positions of the twenty-two bones behind the hips: heading h0, curvature profile, lying on the ground (the belly on it) plus lift."""
    lens = B.BODY_LEN + B.TAIL_LEN
    pts = [V((0.0, y0, slide))]
    h = RAD(spec["h0"])
    s = 0.0
    total = sum(lens)
    amp, wavelength, phase = spec["ripple"]
    for l in lens:
        sm = s + l / 2
        k = spline(spec["kappa"], sm / total)
        k += amp * math.sin(TAU * sm / wavelength - phase) if wavelength else 0.0
        hm = h + 0.5 * RAD(k) * l
        ground = 0.9 * B.radius_at(s + l) + 0.03
        air = spec.get("air", 0.0)
        target = ground * (1 - air) + y0 * air + spline(spec["lift_c"], (s + l) / total)
        dy = max(-0.92 * l, min(0.92 * l, target - pts[-1].y))
        p = math.asin(dy / l)
        pts.append(pts[-1] + V((math.sin(hm) * math.cos(p), math.sin(p), math.cos(hm) * math.cos(p))) * l)
        h += RAD(k) * l
        s += l
    return pts


TAU = 2 * math.pi


def neck_points(spec, y0, slide):
    """Joint positions of the eight neck bones forward from the hips (pitch from the horizontal, yaw toward the right)."""
    pts = [V((0.0, y0, slide))]
    for i, l in enumerate(B.NECK_LEN):
        t = (i + 0.5) / B.NECK_N
        p, y = RAD(spline(spec["neck_pitch"], t)), RAD(spline(spec["neck_yaw"], t))
        h = math.pi - y                      # heading 180 degrees is straight ahead (-Z); less turns it toward +X
        pts.append(pts[-1] + V((math.sin(h) * math.cos(p), math.sin(p), math.cos(h) * math.cos(p))) * l)
    return pts


def _on_polyline(poly, z):
    """The point of a spine polyline [(bind z, world position)] sorted by z, at bind distance z along it (carried on past the ends)."""
    if z <= poly[0][0]:
        a, b = poly[0], poly[1]
    elif z >= poly[-1][0]:
        a, b = poly[-2], poly[-1]
    else:
        i = max(j for j in range(len(poly) - 1) if poly[j][0] <= z)
        a, b = poly[i], poly[i + 1]
    u = (z - a[0]) / max(b[0] - a[0], 1e-9)
    return a[1].lerp(b[1], u)


def frill_turns(sp, st, hips_T=None):
    """The turn of each rib of the mane for the pose whose forward kinematics is `st`: a rib folds to lie ALONG the body (toward the chord of the spine
    behind it, a little out), so it hugs the neck's S and the coils as they bend; openness 1 is as bound, 0 shut, above 1 flared wider than bound."""
    poly = [(B.NECK_TOP, st["Head"][1])] + [(-sum(B.NECK_LEN[:i]), st["Neck%d" % (i + 1)][1]) for i in range(B.NECK_N - 1, -1, -1)]
    z = 0.0
    for n, l in zip(B.SPINE_BACK, B.BODY_LEN + B.TAIL_LEN):
        z += l
        poly.append((z, tip(st, n)))
    out = {}
    a0, a1 = sp["frill"]
    f_amp, f_ph = sp["flutter"]
    for tag in ("Left", "Right"):
        for k in range(B.FRILL_N):
            name = "%sFrill%d" % (tag, k + 1)
            carrier = B.BONES[name][0]
            zr = B.FRILL_Z[k]
            pr, p_head = st[carrier]
            ch_head = V(B.BONES[carrier][1])
            parent = B.BONES[carrier][0]
            pr_par = st[parent][0] if parent in st else Matrix.Identity(3)
            p_axis = p_head + pr @ V((0, 0, zr - ch_head.z))
            root_b = V(B.frill_root(k, 1 if tag == "Right" else -1))
            out_dir = (pr @ (root_b - V((0, B.Y0, zr)))).normalized()
            behind = _on_polyline(poly, zr + 0.8 * B.FRILL_LEN[k])
            tangent = (behind - p_axis).normalized()
            d_fold = (tangent + 0.3 * out_dir).normalized()
            d0 = (V(B.BONES[name][2]) - V(B.BONES[name][1])).normalized()
            d_open = (pr @ d0).normalized()
            op = a0 + (a1 - a0) * k / (B.FRILL_N - 1) + f_amp * math.sin(f_ph - 0.7 * k)
            cosang = max(-1.0, min(1.0, d_open.dot(d_fold)))
            angle = math.acos(cosang)
            axis = d_open.cross(d_fold)
            if axis.length < 1e-4:
                axis = out_dir
            axis.normalize()
            Q = Quaternion(axis, angle * (1.0 - op))
            # the rib's turn relative to its carrier: the carrier's own accumulated turn is `pr`, the rib adds T so that pr @ T @ d0 = Q @ pr @ d0
            out[name] = euler(pr.inverted() @ Q.to_matrix() @ pr)
    return out


FOLD = (0.30, 0.12, 0.95)       # the folded rib: back along the body, a little out and up


DEFAULT = dict(lift=0.0, slide=0.0, neck_pitch=[62, 92, 100, 80, 38], neck_yaw=[0, 0, 0, 0, 0], head=(0, 0, 0), jaw=0.0, lure=(0, 0, 0), lure_yaw=(0, 0, 0),
               h0=65.0, kappa=[-8, -8, -10, -14, -18, -22], lift_c=[0, 0, 0, 0], ripple=(0.0, 0.0, 0.0), frill=(0.0, 0.0), flutter=(0.0, 0.0), air=0.0)


def coil_kappa(r0, r1, total=45.0, sign=-1.0, n=6):
    """A spiral that closes from radius r0 to r1 over the trunk and tail: the curvature (degrees a stud) at n control points."""
    return [sign * DEG(1.0 / (r0 + (r1 - r0) * i / (n - 1))) for i in range(n)]


def solve_core(sp):
    """Every bone's turn but the frill's, for one full spec: (pose, shift). Chains are laid through the curves."""
    y0 = B.Y0 + sp["lift"]
    slide = sp["slide"]
    tp = trunk_points(sp, y0, slide)
    npoints = neck_points(sp, y0, slide)
    # the hips stay square to the guardian's axes (the walk's chain is laid in the same frame), so the first bone of the trunk turns the whole of its heading
    pose = {"Hips": (0.0, 0.0, 0.0)}
    T_h = mat(pose["Hips"])
    neck_pose, _ = solve_chain(B.NECK, npoints, T_h, (0, 0, -1))
    pose.update(neck_pose)
    pose["Head"] = tuple(sp["head"])
    back_pose, _ = solve_chain(B.SPINE_BACK, tp, T_h, (0, 0, 1))
    pose.update(back_pose)
    pose["Jaw"] = (-sp["jaw"], 0, 0)
    for i, n in enumerate(B.LURE):
        pose[n] = (sp["lure"][i], sp["lure_yaw"][i], 0)
    return pose, (sp["lift"], slide)


GROUND_EASE = 0.10
HEAD_FLOOR = 1.7           # the head's axis never nearer the floor than this at its tip (its jaw hangs below the axis)
FIN_REACH = 3.4            # the tail's fin trails this far past the last bone


def _clamp_chain(names, P, floor, parent_T, rest, extra=None):
    """Re-lays a chain whose joints P (len(names) + 1) may be under their floors: each bone is turned up just far enough to put its far joint on its floor
    (the lengths kept); `extra` = (a distance past the last joint, its floor) holds the last bone up so what trails past it stays above the floor too."""
    Q = [P[0]]
    for j in range(len(names)):
        l = (P[j + 1] - P[j]).length
        dv = (P[j + 1] - P[j]).normalized()
        want = floor[j + 1]
        lift_to = (want - Q[-1].y) / l
        if Q[-1].y + dv.y * l < want:
            dy = max(-0.99, min(0.99, lift_to))
            hxz = V((dv.x, 0, dv.z))
            hxz = hxz.normalized() * math.sqrt(1 - dy * dy) if hxz.length > 1e-6 else V((0, 0, 1 if rest[2] > 0 else -1)) * math.sqrt(1 - dy * dy)
            dv = V((hxz.x, dy, hxz.z))
        if extra and j == len(names) - 1:
            reach, efloor = extra
            if Q[-1].y + dv.y * (l + reach) < efloor:
                dy = max(-0.99, min(0.99, (efloor - Q[-1].y) / (l + reach)))
                hxz = V((dv.x, 0, dv.z)).normalized() * math.sqrt(1 - dy * dy)
                dv = V((hxz.x, dy, hxz.z))
        Q.append(Q[-1] + dv * l)
    new, _ = solve_chain(names, Q, parent_T, rest)
    return new


def ground_clamp(pose, shift, air=0.0):
    """Keeps the wyrm from going under the floor where the lag has mixed two moments' turns or a key asks for too much: the hips are not let sink below
    the belly's own height, every joint of the trunk, tail and neck is lifted to its body's height over the ground (the lengths kept), the tail's fin and the
    head's tip are held up. Left alone when nothing is under it, or when it flies (air above a half). Returns (pose, shift)."""
    if air > 0.5:
        return pose, shift
    lift = max(shift[0], -0.25)
    shift = (lift, shift[1])
    st = fk(pose, shift)
    out = dict(pose)
    # the trunk and tail
    lens = B.BODY_LEN + B.TAIL_LEN
    P = [st["Body1"][1]] + [tip(st, n) for n in B.SPINE_BACK]
    floor, d = [0.0], 0.0
    for l in lens:
        d += l
        floor.append(0.9 * B.radius_at(d) + GROUND_EASE)
    reach = (FIN_REACH, 0.25)
    last = (P[-1] - P[-2]).normalized()
    if any(P[j].y < floor[j] - 0.02 for j in range(1, len(P))) or P[-1].y + last.y * FIN_REACH < 0.2:
        out.update(_clamp_chain(B.SPINE_BACK, P, floor, mat(pose["Hips"]), (0, 0, 1), extra=reach))
    # the neck
    st = fk(out, shift)
    N = [st["Neck1"][1]] + [tip(st, n) for n in B.NECK]
    nfloor, u = [0.0], 0.0
    for l in B.NECK_LEN:
        u -= l
        nfloor.append(0.9 * B.radius_at(u) + GROUND_EASE)
    if any(N[j].y < nfloor[j] - 0.02 for j in range(1, len(N))):
        out.update(_clamp_chain(B.NECK, N, nfloor, mat(pose["Hips"]), (0, 0, -1)))
    # the head: its tip held off the floor by turning it up
    st = fk(out, shift)
    hd = tip(st, "Head") - st["Head"][1]
    if st["Head"][1].y + hd.y < HEAD_FLOOR:
        d_new = hd.normalized()
        dy = max(-0.99, min(0.99, (HEAD_FLOOR - st["Head"][1].y) / hd.length))
        hxz = V((d_new.x, 0, d_new.z))
        hxz = hxz.normalized() * math.sqrt(1 - dy * dy) if hxz.length > 1e-6 else V((0, 0, -1)) * math.sqrt(1 - dy * dy)
        d_new = V((hxz.x, dy, hxz.z))
        fix = hd.normalized().rotation_difference(d_new).to_matrix()
        T_parent = st["Neck%d" % B.NECK_N][0]
        out["Head"] = euler(T_parent.inverted() @ fix @ st["Head"][0])
    # the jaw: opened no further than its tip can open without going through the floor
    if tip(fk(out, shift), "Jaw").y < 0.6 and out["Jaw"][0] < 0:
        lo, hi = 0.0, 1.0
        for _ in range(12):
            mid = (lo + hi) / 2
            trial = dict(out)
            trial["Jaw"] = (out["Jaw"][0] * mid, 0, 0)
            if tip(fk(trial, shift), "Jaw").y >= 0.6:
                lo = mid
            else:
                hi = mid
        out["Jaw"] = (out["Jaw"][0] * lo, 0, 0)
    return out, shift


def finish(pose, shift, sp):
    """The ground clamp and the frill (laid on the pose as it ended up) added to a pose. Returns (pose, shift)."""
    pose, shift = ground_clamp(pose, shift, sp.get("air", 0.0))
    st = fk(pose, shift)
    out = dict(pose)
    out.update(frill_turns(sp, st))
    return out, shift


def solve(spec):
    """Every bone's turn for one spec: (pose, shift)."""
    sp = dict(DEFAULT, **spec)
    pose, shift = solve_core(sp)
    return finish(pose, shift, sp)


def points_of(pose, shift):
    """The joints as posed (for checks and renders): {bone: head position}."""
    st = fk(pose, shift)
    return {n: st[n][1] for n in BONES}


# ---------------------------------------------------------------- applying a pose to the Blender armature, for the renders
def set_pose(pose, shift=(0.0, 0.0), rig="LanternWyrmRig"):
    import bpy
    arm = bpy.data.objects[rig]
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        rest = pb.bone.matrix_local.to_3x3()
        t = rb_rot(mat(pose.get(pb.name, (0, 0, 0))))
        pb.rotation_quaternion = (rest.inverted() @ t @ rest).to_quaternion()
        pb.location = (0, 0, 0)
    hips = arm.pose.bones["Hips"]
    C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    hips.location = hips.bone.matrix_local.to_3x3().inverted() @ (C @ V((0, shift[0], shift[1])))
    bpy.context.view_layer.update()


# ---------------------------------------------------------------- the states
S_REST = [45, 90, 112, 90, 18]        # the swan's S: forward and up, over the vertical, forward again at the top
YAW_REST = [0, 10, 6, -6, 0]
COIL = coil_kappa(8.0, 2.6)


def state_specs():
    """The poses it holds in each state: specs (see DEFAULT)."""
    S = {}
    S["Guardian"] = dict(neck_pitch=S_REST, neck_yaw=YAW_REST, head=(-20, 0, 0), kappa=COIL, h0=65.0, frill=(0.0, 0.0))
    # Returning: the neck lowered, the frill half open
    S["Returning"] = dict(S["Guardian"], neck_pitch=[34, 78, 98, 70, 8], head=(-14, 0, 0), frill=(0.5, 0.5))
    # Dormant: one long spiral, the tail inside it, the neck lying outward round it and the head resting on the coils
    S["Dormant"] = dict(S["Guardian"], neck_pitch=[-3, -3, -2, 0, 14], neck_yaw=[0, -57, -115, -172, -180], head=(-4, 48, 0), kappa=coil_kappa(7.4, 2.4), frill=(0.0, 0.0),
                        lure=(-10, -10, -20), jaw=0.0)
    # Weakened: the neck drooping forward, the head on the ground before it, the coils slack
    S["Weakened"] = dict(S["Guardian"], neck_pitch=[20, 28, 6, -18, -34], neck_yaw=[0, -12, -26, -40, -50], head=(26, 10, 6), kappa=coil_kappa(8.8, 3.0), frill=(0.0, 0.0), lift=-0.4,
                         lure=(15, 10, 20))
    # Enraged: reared high, the frill flared wide, the coils drawn tight
    S["Enraged"] = dict(S["Guardian"], neck_pitch=[70, 92, 100, 92, 62], neck_yaw=[0, 4, 0, -4, 0], head=(-38, 0, 0), kappa=coil_kappa(6.6, 2.3), frill=(1.25, 1.15), jaw=18.0)
    # two held flourishes the idle layer blends in now and then: the frill half raised, displeased; and flared wide
    S["Display"] = dict(S["Guardian"], neck_pitch=[48, 92, 114, 92, 22], head=(-16, 0, 0), frill=(0.75, 0.65), lure=(-10, -8, -6))
    S["Flare"] = dict(S["Guardian"], frill=(1.2, 1.1))
    return S


def state_spec(name):
    return state_specs()[name]


# ---------------------------------------------------------------- keys: what a move is made of
# A key holds a whole spec; between two keys every number moves along the later key's ease. Each chain's bones follow after their own lag: the
# turn of bone i at time t is read from the pose built at t - lag(i), so a blow starts at the base and runs down the body.
def ease(name, x):
    x = max(0.0, min(1.0, x))
    if name == "linear":
        return x
    if name == "in":
        return x * x * x
    if name == "out":
        return 1 - (1 - x) ** 3
    if name == "snap":
        return 1 - (1 - x) ** 5
    if name == "back":
        c = 2.0
        return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
    if name == "in2":
        return x * x
    return x * x * (3 - 2 * x)


def lerp_value(a, b, u):
    if isinstance(a, (int, float)):
        return a + (b - a) * u
    return type(a)(lerp_value(x, y, u) for x, y in zip(a, b))


def K(t, ease_name="inout", base=None, lag=None, **over):
    k = dict(DEFAULT)
    k.update(base or state_specs()["Guardian"])
    k.update(over)
    k["t"], k["ease"], k["lag"] = t, ease_name, dict(lag or {})
    return k


def spec_at(keys, t):
    """The spec of a move at time t (the keys' numbers, eased)."""
    t = max(0.0, min(t, keys[-1]["t"]))
    if t >= keys[-1]["t"]:
        a = b = keys[-1]
        u = 1.0
    else:
        i = max(j for j in range(len(keys) - 1) if keys[j]["t"] <= t)
        a, b = keys[i], keys[i + 1]
        u = ease(b["ease"], (t - a["t"]) / max(b["t"] - a["t"], 1e-9))
    return {k: lerp_value(a[k], b[k], u) for k in DEFAULT}, b


def lag_of(lag):
    """{bone: seconds} from a key's lag settings: neck / trunk (per bone along the chain), neck0 / trunk0 (a start), head, jaw, lure, frill."""
    out = {"Hips": 0.0}
    for i, n in enumerate(B.NECK):
        out[n] = lag.get("neck0", 0.0) + lag.get("neck", 0.0) * i
    out["Head"] = lag.get("neck0", 0.0) + lag.get("neck", 0.0) * B.NECK_N + lag.get("head", 0.0)
    out["Jaw"] = out["Head"] + lag.get("jaw", 0.0)
    for i, n in enumerate(B.LURE):
        out[n] = out["Head"] + lag.get("lure", 0.0) * (i + 1)
    for j, n in enumerate(B.SPINE_BACK):
        out[n] = lag.get("trunk0", 0.0) + lag.get("trunk", 0.0) * j
    for tag in ("Left", "Right"):
        for k in range(B.FRILL_N):
            out["%sFrill%d" % (tag, k + 1)] = lag.get("frill0", 0.0) + lag.get("frill", 0.0) * k
    return out


def pose_at(keys, t, lag=None):
    """(pose, shift) of a move at time t, with each bone read from its own moment, then grounded, then the frill laid on it."""
    spec, b = spec_at(keys, t)
    sp = dict(DEFAULT, **spec)
    pose, shift = solve_core(sp)
    lag = lag_of(lag if lag is not None else b["lag"])
    cache = {}
    out = dict(pose)
    for bone, l in lag.items():
        if l == 0.0 or bone.startswith(("Left", "Right")):
            continue
        key = round(l * 1000)
        if key not in cache:
            sp2, _ = spec_at(keys, t - l)
            cache[key] = solve_core(dict(DEFAULT, **sp2))[0]
        out[bone] = cache[key][bone]
    return finish(out, shift, sp)


def state_pose(name):
    return solve(state_specs()[name])


# ---------------------------------------------------------------- the moves
def moves():
    G = state_specs()["Guardian"]
    D, W, E = state_specs()["Dormant"], state_specs()["Weakened"], state_specs()["Enraged"]
    M = {}
    # ---- CoilLash (0.9 s to the blow): the neck draws back and to one side in a tight S, the frill snapping half open, the head counter-turned to keep
    # its eyes on the target, the body gathering; holds; then the neck whips across the front arc, head leading, the body following in a wave
    tight = coil_kappa(7.0, 2.3)
    tighter = coil_kappa(6.3, 2.1)
    M["CoilLash"] = [
        K(0.0),
        K(0.30, "out", neck_pitch=[52, 105, 135, 112, 52], neck_yaw=[0, 30, 56, 52, 34], head=(-30, -42, 0), frill=(0.6, 0.6), kappa=tight, lift=0.2, lure=(0, 0, 0),
          lag=dict(neck=0.012, head=0.02, trunk=0.01)),
        K(0.62, "inout", neck_pitch=[56, 108, 140, 118, 56], neck_yaw=[0, 36, 64, 60, 40], head=(-34, -50, 0), frill=(0.7, 0.7), kappa=tighter, lift=0.3, jaw=4,
          lag=dict(neck=0.012, head=0.02, trunk=0.01)),
        K(0.74, "in2", neck_pitch=[46, 82, 104, 80, 36], neck_yaw=[0, 20, 38, 32, 20], head=(-20, -28, 0), frill=(0.85, 0.85), kappa=tight, lift=0.1, jaw=10,
          lag=dict(neck=0.014, head=0.02, trunk=0.012)),
        K(0.90, "in", neck_pitch=[22, 16, 10, 6, 2], neck_yaw=[0, -6, -16, -22, -24], head=(-4, 8, 0), frill=(1.0, 1.0), kappa=coil_kappa(7.6, 2.5), jaw=28, slide=-3.5,
          ripple=(3.0, 16.0, 0.0), lag=dict(neck=0.014, head=0.025, trunk=0.014)),
        K(0.99, "out", neck_pitch=[26, 20, 14, 8, 4], neck_yaw=[0, -18, -40, -56, -66], head=(-8, 18, 0), frill=(1.2, 1.15), kappa=coil_kappa(7.8, 2.6), jaw=22, slide=-3.0,
          ripple=(5.0, 16.0, 1.4), lag=dict(neck=0.014, head=0.025, trunk=0.014)),
        K(1.25, "out", neck_pitch=[40, 70, 92, 64, 24], neck_yaw=[0, -22, -34, -22, -6], head=(-14, 6, 0), frill=(0.7, 0.7), ripple=(4.0, 16.0, 4.0),
          lag=dict(neck=0.016, head=0.03, trunk=0.018)),
        K(1.60, "inout", frill=(0.15, 0.15), ripple=(1.8, 16.0, 8.5), lag=dict(neck=0.014, trunk=0.02)),
        K(2.0, "inout", ripple=(0.0, 16.0, 11.0)),
    ]
    # ---- LanternGaze (1.2 s): the head lowers and levels at the target, the neck draws straight, the lantern swings forward on its stalk and flares, the jaw
    # opens, the light gathers (the rings: the rig); it holds a beat; then the head thrusts forward and the light is released
    M["LanternGaze"] = [
        K(0.0),
        K(0.50, "out", neck_pitch=[30, 52, 46, 30, 12], neck_yaw=[0, 0, 0, 0, 0], head=(-16, 0, 0), frill=(0.45, 0.45), lure=(-14, -8, -6), lift=0.1,
          lag=dict(neck=0.016, head=0.03, lure=0.02)),
        # gathered: the head drawn back and raised, the neck bowed, the jaw opening, the light building in the lantern
        K(0.95, "inout", neck_pitch=[34, 44, 40, 28, 12], head=(-12, 0, 0), frill=(0.7, 0.7), lure=(-20, -12, -8), jaw=22, kappa=coil_kappa(7.4, 2.5), slide=1.4,
          lag=dict(neck=0.01, head=0.02, lure=0.02)),
        # the release: the head thrusts forward and low, the neck straight, the whole body going with it
        K(1.20, "in", neck_pitch=[16, 10, 4, 0, -4], head=(-4, 0, 0), frill=(1.0, 1.0), lure=(-28, -16, -10), jaw=44, slide=-4.6, lift=-0.1, kappa=coil_kappa(7.0, 2.4),
          lag=dict(neck=0.008, head=0.014, lure=0.015)),
        K(1.50, "out", neck_pitch=[26, 28, 20, 10, 2], head=(-8, 0, 0), frill=(0.8, 0.8), lure=(-20, -12, -8), jaw=30, slide=-2.4, lag=dict(neck=0.012, head=0.02)),
        K(1.80, "inout", frill=(0.2, 0.2), lure=(-8, -6, -6), lag=dict(neck=0.014)),
        K(2.1, "inout"),
    ]
    # ---- VoidSurge (1.4 s): it rears to its full height, the frill flaring to its widest, the coils beneath tightening and rising; then everything slams DOWN:
    # the head and neck onto the coils, the whole body hitting the ground in one wave that runs out from the middle to the tail tip, the frill snapping shut
    M["VoidSurge"] = [
        K(0.0),
        K(0.55, "out", neck_pitch=[78, 90, 92, 88, 82], neck_yaw=[0, 0, 0, 0, 0], head=(-26, 0, 0), jaw=10, frill=(1.15, 1.15), kappa=coil_kappa(6.2, 2.2),
          lift_c=[0, 2.0, 3.0, 1.5], lift=0.5, lag=dict(neck=0.02, head=0.03, trunk=0.01)),
        K(1.05, "inout", neck_pitch=[86, 92, 93, 91, 87], head=(-22, 0, 0), jaw=16, frill=(1.35, 1.3), kappa=coil_kappa(5.6, 2.0), lift_c=[0, 4.0, 5.2, 2.8], lift=0.8,
          lure=(12, 8, 0), lag=dict(neck=0.01, head=0.02, trunk=0.01)),
        K(1.40, "in", neck_pitch=[85, 93, 135, 153, 274], head=(29, 0, 0), jaw=0, frill=(0.0, 0.0), kappa=coil_kappa(7.6, 2.6), lift_c=[0, 0, 0, 0], lift=-0.4,
          ripple=(4.0, 14.0, 0.0), lure=(0, 0, 0), lag=dict(neck=0.012, head=0.01, trunk=0.02)),
        K(1.58, "out", neck_pitch=[84, 95, 138, 160, 250], head=(22, 0, 0), frill=(0.0, 0.0), kappa=coil_kappa(7.9, 2.7), lift=0.1, ripple=(3.2, 14.0, 2.5),
          lag=dict(neck=0.012, trunk=0.022)),
        K(1.95, "inout", neck_pitch=[48, 88, 110, 86, 26], frill=(0.1, 0.1), ripple=(1.6, 14.0, 6.0), lag=dict(neck=0.014, trunk=0.02)),
        K(2.3, "inout", ripple=(0.0, 14.0, 9.0)),
    ]
    # ---- SerpentLeap (0.8 s on the ground, then the air): a tight coil, the neck drawn back in a spring-loaded S, the head low and aiming; the spring (the body
    # uncoiling from the tail forward, the head launching first); a flight in which the body flies as a long undulating ribbon, the jaw open; to the strike
    M["SerpentLeap"] = [
        K(0.0),
        K(0.35, "out", neck_pitch=[35, 85, 125, 110, 30], head=(-25, 0, 0), kappa=coil_kappa(5.6, 2.0), lift=-0.1, jaw=8, frill=(0.6, 0.6), lag=dict(neck=0.012, trunk=0.01)),
        K(0.65, "inout", neck_pitch=[18, 66, 130, 126, 48], head=(-30, 0, 0), kappa=coil_kappa(5.0, 1.9), lift=-0.2, jaw=10, frill=(0.8, 0.8), lag=dict(neck=0.01, trunk=0.01)),
        K(0.80, "in", neck_pitch=[40, 40, 36, 32, 26], head=(-4, 0, 0), kappa=coil_kappa(9.0, 4.0), lift=0.0, jaw=32, frill=(1.0, 1.0), air=0.4, lift_c=[0, -1, -2, -3],
          ripple=(2.0, 20.0, 0.0), lag=dict(neck=0.01, trunk=0.016)),
        K(1.10, "out", neck_pitch=[42, 36, 30, 26, 22], head=(-2, 0, 0), kappa=[-1, -1, -2, -2, -3, -3], air=1.0, lift_c=[0, -1.2, -3, -4.5], jaw=36, frill=(1.0, 1.0),
          ripple=(5.0, 20.0, 2.0), lag=dict(neck=0.01, trunk=0.02)),
        K(1.70, "inout", neck_pitch=[36, 30, 24, 16, 8], head=(-4, 0, 0), kappa=[-1, -1, -2, -2, -3, -3], air=1.0, lift_c=[0, -1.5, -3.5, -5], jaw=36, frill=(1.1, 1.1),
          ripple=(7.0, 20.0, 5.5), lag=dict(neck=0.01, trunk=0.024)),
        K(2.10, "inout", neck_pitch=[18, 8, -2, -10, -16], head=(-6, 0, 0), kappa=[-1, -1, -2, -2, -3, -3], air=1.0, lift_c=[0, -1.5, -3.2, -4.6], jaw=40, frill=(1.1, 1.1),
          ripple=(6.0, 20.0, 9.0), lag=dict(neck=0.01, trunk=0.024)),
        K(2.30, "out", neck_pitch=[16, 8, -2, -12, -20], head=(-4, 0, 0), kappa=[-2, -2, -3, -3, -4, -4], air=0.45, lift_c=[0, -1.5, -3, -4], jaw=42, frill=(1.15, 1.15),
          ripple=(5.0, 20.0, 11.5), lag=dict(neck=0.01, trunk=0.024)),
    ]
    # ---- Land (0.9 s): the head strikes down first, then the body piles down behind it in loose coils, the frill flaring for balance, then the neck rising into its S
    M["Land"] = [
        K(0.0, neck_pitch=[16, 8, -2, -12, -20], head=(-4, 0, 0), kappa=[-2, -2, -3, -3, -4, -4], air=0.45, lift_c=[0, -1.5, -3, -4], jaw=42, frill=(1.15, 1.15),
          ripple=(5.0, 20.0, 11.5)),
        K(0.10, "snap", neck_pitch=[8, -2, -14, -26, -34], head=(0, 0, 0), kappa=coil_kappa(10.0, 4.0), air=0.3, lift_c=[0, -0.5, -1.2, -1.8], jaw=30, frill=(1.2, 1.2), lift=-0.2,
          ripple=(4.0, 18.0, 13.0), lag=dict(neck=0.008, trunk=0.016)),
        K(0.40, "out", neck_pitch=[22, 50, 56, 36, 8], head=(-12, 0, 0), kappa=coil_kappa(9.0, 3.4), air=0.0, lift_c=[0, 0, 0, 0], jaw=10, frill=(0.8, 0.8), lift=-0.2,
          ripple=(3.0, 18.0, 16.0), lag=dict(neck=0.012, trunk=0.02)),
        K(0.48, "inout", ripple=(0.0, 18.0, 19.0), lag=dict(neck=0.012, trunk=0.02)),
    ]
    # ---- Awaken (3.0 s): from the sleeping ring: the lantern ignites (the rig), the head lifts off the coils and shakes, the frill opens and shudders, the body
    # uncoils one loop at a time, the neck rising into its S, the head settling into its alert sway
    M["Awaken"] = [
        K(0.0, base=D),
        K(0.45, "inout", base=D, neck_pitch=[-3, -3, -2, 2, 20], head=(-4, 46, 0), lure=(-4, -4, -8), lag=dict(neck=0.02)),
        K(1.0, "inout", base=D, neck_pitch=[10, 6, 4, 20, 44], neck_yaw=[0, -57, -110, -160, -165], head=(-14, 40, 0), jaw=6, lure=(0, 0, 0), lag=dict(neck=0.03, head=0.04)),
        K(1.25, "inout", base=D, neck_pitch=[14, 10, 8, 26, 50], neck_yaw=[0, -55, -105, -150, -150], head=(-10, 20, 4), jaw=4, lag=dict(neck=0.02)),
        K(1.42, "inout", base=D, neck_pitch=[14, 10, 8, 26, 50], neck_yaw=[0, -55, -105, -150, -150], head=(-10, 68, -4), jaw=4, lag=dict(neck=0.02)),
        K(1.58, "inout", base=D, neck_pitch=[16, 12, 10, 28, 52], neck_yaw=[0, -55, -105, -150, -150], head=(-10, 30, 3), frill=(0.7, 0.7), lag=dict(neck=0.02)),
        K(1.75, "inout", base=D, neck_pitch=[18, 20, 16, 30, 54], neck_yaw=[0, -50, -95, -140, -140], head=(-10, 50, 0), frill=(1.0, 1.0), flutter=(0.18, 6.0), lag=dict(neck=0.02)),
        K(2.2, "inout", neck_pitch=[40, 80, 100, 90, 30], neck_yaw=[0, 4, -2, -10, -20], head=(-6, 10, 0), kappa=coil_kappa(9.6, 3.4), frill=(1.0, 1.0), flutter=(0.14, 8.0),
          lag=dict(neck=0.05, trunk=0.03, head=0.06)),
        K(2.55, "inout", neck_pitch=[48, 94, 116, 94, 22], neck_yaw=YAW_REST, head=(-24, 0, 0), kappa=coil_kappa(8.2, 2.7), frill=(0.4, 0.4), flutter=(0.05, 10.0),
          lag=dict(neck=0.03, trunk=0.02, head=0.04)),
        K(2.9, "inout"),
    ]
    # ---- Enrage (1.4 s): the neck rears up fast, the frill thrown wide, the mouth open in a hiss, the lantern blazing, the whole body thrashing in violent waves;
    # then it settles into a coiled, swaying threat with the frill half open
    M["Enrage"] = [
        K(0.0),
        K(0.20, "out", neck_pitch=[80, 98, 102, 96, 74], head=(-48, 0, 0), jaw=38, frill=(1.35, 1.25), kappa=coil_kappa(6.4, 2.2), lift=0.5, ripple=(6.0, 14.0, 0.0),
          lag=dict(neck=0.01, head=0.02, trunk=0.008)),
        K(0.42, "inout", neck_pitch=[84, 92, 96, 92, 66], neck_yaw=[0, 16, 28, 16, 4], head=(-44, 22, 4), jaw=34, frill=(1.45, 1.3), ripple=(11.0, 14.0, 4.0), lift=0.7, lift_c=[0, 1.5, 2.0, 1.0],
          kappa=coil_kappa(6.0, 2.1), lure=(10, 8, 6), lag=dict(neck=0.014, trunk=0.014)),
        K(0.66, "inout", neck_pitch=[78, 100, 104, 98, 70], neck_yaw=[0, -16, -28, -16, -4], head=(-40, -22, -4), jaw=30, frill=(1.45, 1.3), ripple=(11.0, 14.0, 8.0), lift=0.2,
          lift_c=[0, 0.4, 0.6, 0.3], kappa=coil_kappa(6.6, 2.3), lure=(-8, -6, -4), lag=dict(neck=0.014, trunk=0.014)),
        K(0.88, "inout", neck_pitch=[84, 92, 98, 94, 66], neck_yaw=[0, 12, 22, 12, 2], head=(-42, 14, 3), jaw=26, frill=(1.3, 1.2), ripple=(8.0, 14.0, 12.0), lift=0.6, lift_c=[0, 1.2, 1.6, 0.8],
          kappa=coil_kappa(6.1, 2.2), lag=dict(neck=0.014, trunk=0.014)),
        K(1.12, "back", base=E, ripple=(0.0, 14.0, 15.0), lag=dict(neck=0.01, trunk=0.012)),
    ]
    # ---- Weaken (1.9 s): a stagger, the neck whipping back then collapsing, the lantern guttering, the frill folding, the head sinking to the coils, then a held,
    # laboured pose
    M["Weaken"] = [
        K(0.0),
        K(0.16, "out", neck_pitch=[62, 118, 150, 132, 84], head=(24, 0, 0), jaw=26, frill=(0.8, 0.8), kappa=coil_kappa(7.0, 2.4), lift=0.3, lag=dict(neck=0.01, head=0.02)),
        K(0.55, "inout", neck_pitch=[40, 62, 40, 4, -24], neck_yaw=[0, 10, 24, 30, 30], head=(-6, 8, 8), jaw=4, frill=(0.3, 0.3), kappa=coil_kappa(8.4, 2.9), lift=-0.2,
          lag=dict(neck=0.02, head=0.03, trunk=0.014)),
        K(0.95, "in", base=W, lag=dict(neck=0.016, head=0.02, trunk=0.014)),
        K(1.30, "back", base=W, lift=-0.25, lag=dict(neck=0.012, trunk=0.012)),
        K(1.45, "inout", base=W),
    ]
    for name, keys in M.items():
        want = MOVE_LENGTH[name]
        if keys[-1]["t"] < want - 1e-6:
            hold = dict(keys[-1])
            hold["t"], hold["ease"] = want, "linear"
            keys.append(hold)
    return M


MOVE_LENGTH = {"CoilLash": 2.45, "LanternGaze": 2.45, "VoidSurge": 2.6, "SerpentLeap": 2.3, "Land": 0.9, "Awaken": 3.0, "Enrage": 1.4, "Weaken": 1.9}
STRIP_TIMES = {"CoilLash": [0.0, 0.30, 0.62, 0.78, 0.90, 0.99, 1.40, 2.0], "LanternGaze": [0.0, 0.50, 0.95, 1.10, 1.20, 1.50, 1.9, 2.4],
               "VoidSurge": [0.0, 0.55, 1.05, 1.30, 1.40, 1.50, 1.58, 2.3], "SerpentLeap": [0.0, 0.35, 0.65, 0.80, 1.10, 1.70, 2.10, 2.30],
               "Land": [0.0, 0.05, 0.10, 0.20, 0.30, 0.45, 0.65, 0.9], "Awaken": [0.0, 0.45, 1.0, 1.42, 1.75, 2.25, 2.65, 3.0],
               "Enrage": [0.0, 0.1, 0.2, 0.45, 0.7, 1.0, 1.2, 1.4], "Weaken": [0.0, 0.16, 0.35, 0.55, 0.75, 0.95, 1.3, 1.9]}


# ---------------------------------------------------------------- the walk and the run: a body that follows its leader
# Lateral undulation: the body lies on the path the root has taken (a recorded trail of its positions, each bone reading the trail back at its
# own distance along the body, so a turn is followed, never sheared), carrying a bending wave that is FIXED in the world, so every body point
# slides along the track and none skates. The wave's amplitude grows from nothing at the hips (the head and neck stay steady and level, as a
# serpent's do) over `ramp` studs; its wavelength and amplitude follow the ground speed. The game does the same live (LanternWyrmSkinned.lua,
# `Chain`); this is the reference it is checked against.
CHAIN = dict(speed_walk=12.0, speed_run=28.0, amp_walk=1.7, amp_run=2.4, lam_walk=15.0, lam_run=26.0, ramp=12.0)


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def gallop(speed, lo=16.0, hi=24.0):
    return smooth01((speed - lo) / (hi - lo))


def wave_params(speed):
    g = gallop(speed)
    k = smooth01(speed / 6.0)
    return (CHAIN["amp_walk"] + (CHAIN["amp_run"] - CHAIN["amp_walk"]) * g) * k, CHAIN["lam_walk"] + (CHAIN["lam_run"] - CHAIN["lam_walk"]) * g


class Trail:
    """The root's recorded path: points in the ground plane with the distance travelled at each, newest last. Pushed when it has moved 0.3 studs."""

    def __init__(self, heading_back=(0.0, 1.0)):
        self.pts, self.s = [], []
        self.back = V((heading_back[0], 0.0, heading_back[1]))

    def push(self, p):
        p = V((p[0], 0.0, p[2]))
        if not self.pts:
            self.pts.append(p)
            self.s.append(0.0)
        elif (p - self.pts[-1]).length >= 0.3:
            self.s.append(self.s[-1] + (p - self.pts[-1]).length)
            self.pts.append(p)
        self.now = p
        self.s_now = self.s[-1] + (p - self.pts[-1]).length
        while len(self.pts) > 400 or (len(self.s) > 2 and self.s_now - self.s[1] > 110.0):
            self.pts.pop(0)
            self.s.pop(0)

    def _tangent(self, i):
        """Unit direction of travel at stored point i (central difference; the newest point looks on to the root)."""
        pts = self.pts + [self.now]
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        d = b - a
        return d.normalized() if d.length > 1e-6 else V((0, 0, -1))

    def at(self, behind):
        """(point, unit tangent of travel, distance along the path) `behind` studs behind the root; the tangent is blended between the points on either
        side so the path bends smoothly; beyond the start the path carries straight back."""
        target = self.s_now - behind
        if len(self.pts) < 2 or target <= self.s[0]:
            d = self._tangent(0) if len(self.pts) > 1 else -self.back
            return self.pts[0] + d * (target - self.s[0]), d, target
        i = max(j for j in range(len(self.pts)) if self.s[j] <= target)
        if i >= len(self.pts) - 1:
            a, b = self.pts[-1], self.now
            s_a, s_b = self.s[-1], self.s_now
            ta, tb = self._tangent(len(self.pts) - 1), self._tangent(len(self.pts))
        else:
            a, b = self.pts[i], self.pts[i + 1]
            s_a, s_b = self.s[i], self.s[i + 1]
            ta, tb = self._tangent(i), self._tangent(i + 1)
        u = (target - s_a) / max(s_b - s_a, 1e-9)
        t = ta.lerp(tb, max(0.0, min(1.0, u)))
        return a.lerp(b, max(0.0, min(1.0, u))) if (b - a).length > 1e-9 else a, (t.normalized() if t.length > 1e-6 else ta), target


def chain_points(trail, speed, to_local, wave=True):
    """The twenty-three joints of the trunk and tail in the guardian's frame: laid along the trail with the wave added, each joint exactly one bone's
    length (a chord) from the one before it, lying on the ground. `to_local(point)` takes a world ground-plane point to the guardian's axes."""
    amp, lam = wave_params(speed)

    def track(b):
        p, t, s_star = trail.at(b)
        n = V((-t.z, 0.0, t.x))                       # to the left of travel
        off = amp * smooth01(b / CHAIN["ramp"]) * math.sin(TAU * s_star / lam) if wave else 0.0
        return p + n * off
    lens = B.BODY_LEN + B.TAIL_LEN
    world = [track(0.0)]
    b = 0.0
    for l in lens:
        a = world[-1]
        lo, hi = b, b + l * 1.8 + 2 * amp + 0.5
        for _ in range(30):
            mid = (lo + hi) / 2
            if (track(mid) - a).length < l:
                lo = mid
            else:
                hi = mid
        b = (lo + hi) / 2
        world.append(track(b))
    pts, d = [], 0.0
    for j, w in enumerate(world):
        q = to_local(w)
        pts.append(V((q.x, B.Y0 if j == 0 else 0.9 * B.radius_at(d) + GROUND_EASE, q.z)))
        if j < len(lens):
            d += lens[j]
    return pts


def chain_pose(points):
    """The trunk's turns for the joints (the hips square to the guardian's axes)."""
    pose, _ = solve_chain(B.SPINE_BACK, points, Matrix.Identity(3), (0, 0, 1))
    return pose


# ---------------------------------------------------------------- tables for the game
def continuous(e, ref):
    """The same rotation written closest to `ref` (angle tables must run smoothly, or the game's springs flail)."""
    a = tuple(near_angle(e[k], ref[k]) for k in range(3))
    b0 = (e[0] + 180, 180 - e[1], e[2] + 180)
    b = tuple(near_angle(b0[k], ref[k]) for k in range(3))
    d = lambda v: sum(abs(v[k] - ref[k]) for k in range(3))
    return a if d(a) <= d(b) else b


JOINTS = joints()


def full(pose, shift, base):
    """{joint: [pitch, yaw, roll]} (the hips also [lift, slide]) written close to `base`'s numbers."""
    out = {}
    for n in JOINTS:
        out[n] = list(continuous(pose.get(n, (0, 0, 0)), base.get(n, (0, 0, 0))[:3]))
    out["Hips"] = out["Hips"] + [shift[0], shift[1]]
    return out


def state_tables():
    sp = {}
    for name in state_specs():
        sp[name] = solve(state_specs()[name])
    return sp


def bake_move(keys, fps=30):
    """Dense frames of a move: [{joint: values}]."""
    base = {n: (0, 0, 0) for n in JOINTS}
    frames, prev = [], None
    length = keys[-1]["t"]
    guardian = full(*state_tables()["Guardian"], base)
    for f in range(int(round(length * fps)) + 1):
        pose, shift = pose_at(keys, min(f / fps, length))
        ref = prev or full(*pose_at(keys, 0.0), guardian)
        v = full(pose, shift, {n: ref[n][:3] for n in JOINTS})
        frames.append(v)
        prev = v
    return frames


# ---------------------------------------------------------------- Clips.lua
def _lua(v):
    if isinstance(v, dict):
        return "{" + ",".join(k + "=" + _lua(x) for k, x in v.items()) + "}"
    if isinstance(v, (list, tuple)):
        return "{" + ",".join(_lua(x) for x in v) + "}"
    if isinstance(v, str):
        return '"' + v + '"'
    t = "%.2f" % v
    t = t.rstrip("0").rstrip(".") if "." in t else t
    return "0" if t in ("-0", "") else t


def reduce_track(rows, tol):
    """Keeps the frames a track needs: the fewest whose straight lines stay within `tol` of every frame (Ramer-Douglas-Peucker)."""
    keep = {0, len(rows) - 1}

    def span(a, b):
        worst, at = 0.0, None
        for i in range(a + 1, b):
            u = (i - a) / (b - a)
            d = max(abs(rows[i][k] - (rows[a][k] + (rows[b][k] - rows[a][k]) * u)) / (tol[k] if isinstance(tol, (list, tuple)) else tol) for k in range(len(rows[0])))
            if d > worst:
                worst, at = d, i
        if worst > 1.0 and at is not None:
            keep.add(at)
            span(a, at)
            span(at, b)

    span(0, len(rows) - 1)
    return sorted(keep)


CONTACT = {"CoilLash": 0.90, "LanternGaze": 1.20, "VoidSurge": 1.40, "SerpentLeap": 0.80, "Land": 0.10, "Weaken": 1.05}


def anchors():
    """Where things truly are at each blow, for the effects (the guardian's own axes, the floor y = 0)."""
    out = {}
    mv = moves()

    def pt(name, t, bone, end=True):
        pose, shift = pose_at(mv[name], t)
        st = fk(pose, shift)
        p = tip(st, bone) if end else st[bone][1]
        return [round(p.x, 1), round(p.y, 1), round(p.z, 1)]

    def lamp(name, t):
        pose, shift = pose_at(mv[name], t)
        st = fk(pose, shift)
        r, h = st["Lure3"]
        p = h + r @ (V(B.LAMP) - V(B.BONES["Lure3"][1]))
        return [round(p.x, 1), round(p.y, 1), round(p.z, 1)]

    def coil_centre(name, t):
        pose, shift = pose_at(mv[name], t)
        st = fk(pose, shift)
        pts = [st[n][1] for n in B.SPINE_BACK]
        c = sum(pts, V()) / len(pts)
        return [round(c.x, 1), 0.6, round(c.z, 1)]
    out["LashHead"] = pt("CoilLash", 0.90, "Head")
    out["LashNeck"] = pt("CoilLash", 0.90, "Neck4", end=False)
    out["GazeLamp"] = lamp("LanternGaze", 1.20)
    out["GazeMouth"] = pt("LanternGaze", 1.20, "Head")
    best = min((pt("VoidSurge", 1.40 + 0.02 * i, "Head") + [1.40 + 0.02 * i] for i in range(16)), key=lambda q: q[1])
    out["SurgeHead"] = best[:3]
    out["SurgeCoils"] = coil_centre("VoidSurge", best[3])
    out["SurgeTop"] = pt("VoidSurge", 1.05, "Head")
    out["LandHead"] = pt("Land", 0.10, "Head")
    out["Crown"] = pt("Awaken", 2.25, "Head", end=False)
    out["EnrageMouth"] = pt("Enrage", 0.45, "Head")
    out["Coil"] = coil_centre("CoilLash", 0.0)
    out["LampRest"] = lamp("CoilLash", 0.0)
    out["TailTip"] = pt("CoilLash", 0.0, "Tail11")
    out["Hips"] = [0.0, 2.6, 0.0]
    return out


def neck_alpha():
    """For each neck bone and the head: how far its PARENT's long axis is raised (degrees) in the awake pose. A turn about the vertical, laid on a bone, is
    cos(alpha) of yaw and -sin(alpha) of roll (the bones are turned in their parent's frame), which the rig's look, gaze and sway layers use."""
    pose, shift = state_pose("Guardian")
    st = fk(pose, shift)
    out = {}
    prev = 0.0
    for n in B.NECK + ["Head"]:
        out[n] = round(prev, 1)
        d = st[n][0] @ V((0, 0, -1))
        prev = DEG(math.atan2(d.y, -d.z))
    return out


def write_clips(path, fps=30):
    """src/client/Guardians/GuardianRigs/LanternWyrmClips.lua, generated: the poses, the moves and the walk's constants as data the rig plays."""
    sts = state_tables()
    base = {n: (0, 0, 0) for n in JOINTS}
    guardian = full(*sts["Guardian"], base)
    lines = ["-- Written by tools/blender/guardians/lantern_wyrm.py (lantern_wyrm_motion.write_clips): do not edit by hand. Angles in degrees,",
             "-- [pitch, yaw, roll]; the hips also carry [lift, slide] in studs. Poses are whole poses (every joint); Moves are tracks of [frame, values...]",
             "-- at Fps, only for the joints the move drives, each held to a tolerance of 0.25 degrees (0.04 studs). Chain holds the walk's constants.",
             "local Clips = {}", "Clips.Fps = %d" % fps, "Clips.Joints = " + _lua(JOINTS), "Clips.Anchors = " + _lua(anchors()),
             "Clips.Chain = " + _lua(dict(CHAIN, lengths=B.BODY_LEN + B.TAIL_LEN, ground=[B.Y0] + [round(0.9 * B.radius_at(sum((B.BODY_LEN + B.TAIL_LEN)[:i])) + GROUND_EASE, 3) for i in range(1, len(B.BODY_LEN + B.TAIL_LEN) + 1)])),
             "Clips.Alpha = " + _lua(neck_alpha()),
             "Clips.Poses = {"]
    for name, (pose, shift) in sts.items():
        v = full(pose, shift, guardian)
        lines.append("%s=%s," % (name, _lua({n: [round(x, 2) for x in v[n]] for n in JOINTS})))
    lines.append("}")
    lines.append("Clips.Moves = {")
    worst = {}
    for name, keys in moves().items():
        frames = bake_move(keys, fps)
        tracks = {}
        for n in JOINTS:
            rows = [fr[n] for fr in frames]
            ref = guardian[n]
            if not any(abs(r[k] - ref[k]) > 0.25 for r in rows for k in range(len(r))):
                continue
            tol = [0.25, 0.25, 0.25, 0.04, 0.04][:len(rows[0])]
            kept = reduce_track(rows, tol)
            err = 0.0
            for a, b in zip(kept, kept[1:]):
                for i in range(a, b + 1):
                    u = (i - a) / (b - a)
                    err = max(err, max(abs(rows[i][k] - (rows[a][k] + (rows[b][k] - rows[a][k]) * u)) / tol[k] for k in range(len(tol))))
            worst[name] = max(worst.get(name, 0.0), err)
            tracks[n] = [[f] + [round(x, 2) for x in rows[f]] for f in kept]
        lines.append("%s={Length=%s,Tracks=%s}," % (name, _lua(keys[-1]["t"]), _lua(tracks)))
    lines.append("}")
    lines.append("return Clips")
    with open(path, "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")
    import os as _os
    return {"bytes": _os.path.getsize(path), "worst reduction error (x tolerance)": {k: round(v, 2) for k, v in worst.items()}, "anchors": anchors()}
