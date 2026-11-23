"""The Cinder Roc's motion: how it stands, walks, runs and strikes, solved here and played by the game (run inside Blender).

A pose is {bone: (pitch, yaw, roll) in degrees} and the hips' (lift, slide) in studs, in the guardian's own axes, each bone's turn on top
of its parent's, exactly as the game's joints work (GuardianAnim: Bone.Transform = rest^-1 * turn * rest). A positive pitch lifts the
front of a forward-pointing bone (the beak, the chest) and tips a vertical one (the neck) back; positive yaw turns a bone's far end to
its left; for a wing, yaw is its sweep forward and back and roll is its flap, mirrored by the left wing.

The legs are solved, not keyed: a foot stays planted at its world spot while the hips move over it (a three-bone digitigrade leg in the
vertical plane through the hip and the foot: the tarsus's slope is chosen, the thigh and shin reach the hock, the foot stays flat).
The wings are placed by where each segment points and which way its face looks (the arm is a chain: upper arm, forearm, hand), and the
primaries and secondaries by how far their fans open.

    import cinder_roc_motion as M
    pose, shift = M.solve(M.Stance(...))
"""
import math

from mathutils import Matrix, Vector

from cinder_roc_bones import BONES, PRIM_ANGLES, PRIM_LENGTHS, PRIM_ROOTS, _trail, _unit, joints, wing_frame

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


def orient(pose, state_fn, bone, want_dir, want_up, rest_up=(0, 1, 0)):
    """Turn `bone` (under its parent as now posed) so its length points along want_dir and its face (rest: up) looks along want_up."""
    parent = BONES[bone][0]
    pr = state_fn(pose)[parent][0]
    rest = frame(rest_dir(bone), rest_up)
    want = frame(want_dir, want_up)
    pose[bone] = euler(pr.inverted() @ want @ rest.inverted())


# ---------------------------------------------------------------- the legs: three bones in a plane, a foot that stays flat
def _len(a, b):
    return (V(BONES[b][1]) - V(BONES[a][1])).length


L_THIGH, L_SHIN, L_TARSUS = _len("RightThigh", "RightShin"), _len("RightShin", "RightTarsus"), _len("RightTarsus", "RightFoot")


def _plane_angle(name):
    """The bone's lean in the leg's plane at rest: degrees from straight down toward the front."""
    d = V(BONES[name][2]) - V(BONES[name][1])
    return DEG(math.atan2(-d.z, -d.y))


A_THIGH, A_SHIN, A_TARSUS, A_FOOT = (_plane_angle("Right" + n) for n in ("Thigh", "Shin", "Tarsus", "Foot"))
BALL_REST = V(BONES["RightFoot"][1])        # the foot's joint at the root of the toes: where a foot "stands"
HOCK_REST = V(BONES["RightShin"][2])


def leg(pose, shift, tag, ball, tau=None, foot=0.0, toes=0.0, hallux=0.0, knee_floor=2.0):
    """Plants a leg: `ball` is the world spot of the foot's joint (x, y, z); `tau` the tarsus's lean in the leg's plane (degrees from
    straight down toward the front; None keeps the hock where the reach is easiest); `foot` the foot's pitch (0 flat; + toes up); `toes`
    and `hallux` their curl (- curls down). The leg lies in the vertical plane through the hip and the ball."""
    state = fk(pose, shift)
    sign = -1 if tag == "Left" else 1
    hr, hp = state["Hips"]
    hip = hp + hr @ (V(BONES[tag + "Thigh"][1]) - V(BONES["Hips"][1]))
    B = V(ball)
    d = B - hip
    # the plane: forward turned by psi so it holds the hip and the ball
    psi = math.atan2(-d.x, -d.z)
    s = math.hypot(d.x, d.z)
    if abs(psi) > math.pi / 2:
        psi, s = psi - math.copysign(math.pi, psi), -s
    plane = Matrix.Rotation(psi, 3, "Y")
    if tau is None:
        tau = A_TARSUS
    t = RAD(tau)
    hock_f, hock_y = s - L_TARSUS * math.sin(t), B.y + L_TARSUS * math.cos(t)
    df, dy = hock_f, hock_y - hip.y
    dist = max(min(math.hypot(df, dy), (L_THIGH + L_SHIN) * 0.998), abs(L_THIGH - L_SHIN) + 0.05)
    aim = math.atan2(df, -dy)                                  # from straight down toward the front
    alpha = math.acos(max(-1, min(1, (L_THIGH ** 2 + dist ** 2 - L_SHIN ** 2) / (2 * L_THIGH * dist))))
    beta = math.acos(max(-1, min(1, (L_SHIN ** 2 + dist ** 2 - L_THIGH ** 2) / (2 * L_SHIN * dist))))
    w_thigh, w_shin = aim + alpha, aim - beta                  # the knee in front: the thigh leans further forward than the line
    w_tarsus = t
    targets = {"Thigh": w_thigh - RAD(A_THIGH), "Shin": w_shin - RAD(A_SHIN), "Tarsus": w_tarsus - RAD(A_TARSUS), "Foot": RAD(foot)}
    parent_rot = hr
    for n in ("Thigh", "Shin", "Tarsus", "Foot"):
        world = plane @ Matrix.Rotation(targets[n], 3, "X")
        pose[tag + n] = euler(parent_rot.inverted() @ world)
        parent_rot = world
    pose[tag + "Toes"] = (toes, 0, 0)
    pose[tag + "Hallux"] = (hallux, 0, 0)
    return {"reach": dist, "thigh": DEG(w_thigh), "shin": DEG(w_shin), "hock_y": hock_y}


# ---------------------------------------------------------------- the wing: sweep, lift, bank, elbow, wrist, and the fans
MIRROR = Matrix(((-1, 0, 0), (0, 1, 0), (0, 0, 1)))


def wing(pose, shift, sign, sweep=0.0, lift=0.0, bank=0.0, elbow=0.0, wrist=0.0, fan=1.0, sec_fan=1.0, prim_roll=0.0, sec_roll=0.0,
         prim_twist=0.0, clavicle=(0, 0, 0), tip_curl=0.0, wave=None):
    """One wing, its numbers written for the RIGHT wing (the left mirrors them), measured on the chest: `sweep` turns it forward (+) or
    back (-) from out to the side, `lift` raises it (+) or lowers it, `bank` twists it about its own length (+ lifts its trailing edge's
    side down: negative turns its face outward), `elbow` and `wrist` bend the forearm and the hand in the wing's plane (+ forward).
    fan / sec_fan: how far the five primary and two secondary groups spread (1 as bound, 0 shut, above 1 wider); prim_roll / sec_roll
    curl the feather tips up (+); tip_curl bends each chain's outer bone up (+); wave: per-group extra yaw for a ripple."""
    tag = "Left" if sign < 0 else "Right"
    mirror = (lambda m: MIRROR @ m @ MIRROR) if sign < 0 else (lambda m: m)
    state = fk(pose, shift)
    chest = state["Chest"][0]
    cl = (clavicle[0], clavicle[1] * sign, clavicle[2] * sign)
    pose[tag + "Clavicle"] = cl
    p_clav = chest @ mat(cl)
    rw = Matrix.Rotation(RAD(sweep), 3, "Y") @ Matrix.Rotation(RAD(lift), 3, "Z") @ Matrix.Rotation(RAD(bank), 3, "X")
    targets = {"UpperArm": rw, "Forearm": rw @ Matrix.Rotation(RAD(elbow), 3, "Y"), "Hand": rw @ Matrix.Rotation(RAD(elbow + wrist), 3, "Y")}
    parent = p_clav
    for bone in ("UpperArm", "Forearm", "Hand"):
        world = chest @ mirror(targets[bone])
        pose[tag + bone] = euler(parent.inverted() @ world)
        parent = world
    wave = wave or (0, 0, 0, 0, 0)
    for g in range(5):
        pose[tag + "Prim%dA" % (g + 1)] = (prim_twist, ((1.0 - fan) * PRIM_ANGLES[g] + wave[g]) * sign, prim_roll * sign)
        pose[tag + "Prim%dB" % (g + 1)] = (0, 0, tip_curl * sign)
    for g in range(2):
        pose[tag + "Sec%dA" % (g + 1)] = (0, (1.0 - sec_fan) * 80.0 * sign, sec_roll * sign)
        pose[tag + "Sec%dB" % (g + 1)] = (0, 0, 0.5 * tip_curl * sign)


# ---------------------------------------------------------------- applying a pose to the Blender armature, for the renders
def set_pose(pose, shift=(0.0, 0.0), rig="CinderRocRig"):
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


# ---------------------------------------------------------------- one pose from its parts
RIGHT_FOOT = V(BONES["RightFoot"][1])
FEET = {"Left": V((-RIGHT_FOOT.x, RIGHT_FOOT.y, RIGHT_FOOT.z)), "Right": V((RIGHT_FOOT.x, RIGHT_FOOT.y, RIGHT_FOOT.z))}
FOLDED = dict(sweep=-72.0, lift=-8.0, bank=-42.0, elbow=152.0, wrist=-152.0, fan=0.05, sec_fan=0.1)
BOUND_WING = dict()
TAIL_BONES_ALL = [n for n in BONES if "Tail" in n and n != "TailBase"]
CREST_BONES_ALL = [n for n in BONES if "Crest" in n]


def build_pose(body=None, shift=(0.0, 0.0), wl=None, wr=None, feet=None, tail=None, crest=None):
    """A whole pose: body {bone: euler}, hips shift, a dict of wing numbers each side, the feet (see leg: {"Left": dict(ball=..., tau=...,
    foot=..., toes=..., hallux=...)} or {"Left": {"free": {bone: euler}}}), tail and crest {bone: euler}."""
    pose = dict(body or {})
    for bone in (tail or {}):
        e = tail[bone]
        pose[bone] = (-e[0], e[1], e[2]) if bone == "TailBase" else e      # TailBase points back: written as how far it is raised
    for bone in (crest or {}):
        pose[bone] = crest[bone]
    for sign, spec in ((-1, wl), (1, wr)):
        wing(pose, shift, sign, **(spec or {}))
    feet = feet or {}
    plants = {}
    for tag in ("Left", "Right"):
        f = dict(feet.get(tag, {}))
        if "free" in f:
            for bone, e in f["free"].items():
                pose[tag + bone] = e
            plants[tag] = False
        else:
            ball = f.pop("ball", FEET[tag])
            leg(pose, shift, tag, ball, **f)
            plants[tag] = True
    return pose, shift, plants


# ---------------------------------------------------------------- keys: what a move is made of
# A key holds the numbers of a pose; between two keys every number moves along the later key's ease, each channel (a bone, a wing, a leg)
# after its own lag, so the body leads and the neck, the head and the tail follow: the overlap that gives a move weight.
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


LAG = {"Hips": 0.0, "Spine": 0.012, "Chest": 0.024, "Neck1": 0.034, "Neck2": 0.05, "Neck3": 0.066, "Head": 0.082, "Jaw": 0.05}


def slerp_euler(a, b, u):
    """Between two rotations along the short way, u beyond 0..1 carries on past them (an ease that overshoots)."""
    from mathutils import Quaternion
    qa, qb = mat(a).to_quaternion(), mat(b).to_quaternion()
    if qa.dot(qb) < 0:
        qb = -qb
    axis, angle = qa.rotation_difference(qb).to_axis_angle()
    return euler((qa @ Quaternion(axis, angle * u)).to_matrix())


def lerp(a, b, u):
    return a + (b - a) * u


GUARDIAN_BODY = {"Hips": (1.0, 0.0, 2.5), "Spine": (0, 0, -1.0), "Chest": (3.0, 0, -1.5), "Neck1": (-4.0, 0, 0), "Neck2": (7.0, 0, 0), "Neck3": (-3.0, 0, 0),
                 "Head": (5.0, 0, 0), "Jaw": (0, 0, 0)}
GUARDIAN = dict(body=GUARDIAN_BODY, shift=(-0.5, 0.0), wl=FOLDED, wr=FOLDED,
                feet={"Left": dict(ball=FEET["Left"], tau=44.0), "Right": dict(ball=V((3.4, 1.0, -2.7)), tau=52.0)},
                tail={"TailBase": (6.0, 0, 0)}, crest={"CrestA": (4.0, 0, 0)})


def merge(base, over):
    """A key's numbers: the base's, with each part of `over` laid over it (dicts merge one level deep)."""
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base.items()}
    for k, v in over.items():
        if k == "feet":
            for tag, spec in v.items():
                out["feet"][tag] = spec if "free" in spec else {**({} if "free" in out["feet"].get(tag, {}) else out["feet"].get(tag, {})), **spec}
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


def key(t, ease_name="smooth", base=GUARDIAN, lag=None, **over):
    k = merge(base, over)
    k["t"], k["ease"], k["lag"] = t, ease_name, dict(LAG, **(lag or {}))
    return k


def _planted_euler(k, tag):
    """The leg's solved angles for a planted key (to blend with a free one)."""
    pose, shift, _ = build_pose(body=k["body"], shift=k["shift"], wl=k["wl"], wr=k["wr"], feet={tag: k["feet"][tag]})
    return {n: pose[tag + n] for n in ("Thigh", "Shin", "Tarsus", "Foot", "Toes", "Hallux")}


def sample(keys, t):
    """(pose, shift, plants) of a move at time t."""
    if t >= keys[-1]["t"]:
        a = b = keys[-1]
        u = 1.0
    else:
        i = max(j for j in range(len(keys) - 1) if keys[j]["t"] <= t) if t >= keys[0]["t"] else 0
        a, b = keys[i], keys[i + 1]
    span = max(b["t"] - a["t"], 1e-6)

    def u_of(lag):
        return ease(b["ease"], (t - lag - a["t"]) / span)

    lag = b["lag"]
    body = {}
    for bone in set(a["body"]) | set(b["body"]):
        body[bone] = slerp_euler(a["body"].get(bone, (0, 0, 0)), b["body"].get(bone, (0, 0, 0)), u_of(lag.get(bone, 0.0)))
    ub = u_of(0.0)
    shift = (lerp(a["shift"][0], b["shift"][0], ub), lerp(a["shift"][1], b["shift"][1], ub))
    ew = ease(b.get("ease_wing", b["ease"]), (t - lag.get("Wing", 0.0) - a["t"]) / span)
    wings = []
    for side in ("wl", "wr"):
        spec = {}
        for name in set(a[side]) | set(b[side]):
            av = a[side].get(name, 1.0 if name in ("fan", "sec_fan") else 0.0)
            bv = b[side].get(name, 1.0 if name in ("fan", "sec_fan") else 0.0)
            spec[name] = lerp(av, bv, ew) if not isinstance(av, (tuple, list)) else tuple(lerp(x, y, ew) for x, y in zip(av, bv))
        wings.append(spec)
    tail = {n: slerp_euler(a["tail"].get(n, (0, 0, 0)), b["tail"].get(n, (0, 0, 0)), u_of(lag.get("Tail", 0.04))) for n in set(a["tail"]) | set(b["tail"])}
    crest = {n: slerp_euler(a["crest"].get(n, (0, 0, 0)), b["crest"].get(n, (0, 0, 0)), u_of(lag.get("Crest", 0.06))) for n in set(a["crest"]) | set(b["crest"])}
    feet = {}
    for tag in ("Left", "Right"):
        fa, fb = a["feet"][tag], b["feet"][tag]
        ul = u_of(lag.get("Feet", 0.0))
        if "free" not in fa and "free" not in fb:
            spec = {"ball": V(fa.get("ball", FEET[tag])).lerp(V(fb.get("ball", FEET[tag])), ul)}
            for name, dflt in (("tau", A_TARSUS), ("foot", 0.0), ("toes", 0.0), ("hallux", 0.0)):
                spec[name] = lerp(fa.get(name, dflt), fb.get(name, dflt), ul)
            feet[tag] = spec
        else:
            ea = fa["free"] if "free" in fa else _planted_euler(a, tag)
            eb = fb["free"] if "free" in fb else _planted_euler(b, tag)
            feet[tag] = {"free": {n: slerp_euler(ea.get(n, (0, 0, 0)), eb.get(n, (0, 0, 0)), ul) for n in set(ea) | set(eb)}}
    return build_pose(body=body, shift=shift, wl=wings[0], wr=wings[1], feet=feet, tail=tail, crest=crest)


# ---------------------------------------------------------------- the postures and the moves
W_HALF = dict(sweep=-25, lift=18, bank=-15, elbow=40, wrist=-45, fan=0.7, sec_fan=0.8)
W_UP = dict(sweep=-30, lift=72, bank=-25, elbow=25, wrist=-20, fan=0.95, sec_fan=1.0)
W_UPWIDE = dict(sweep=-34, lift=78, bank=-30, elbow=14, wrist=-10, fan=1.12, sec_fan=1.1)
W_DOWN = dict(sweep=14, lift=-30, bank=20, elbow=10, wrist=-5, fan=0.8, sec_fan=0.9)
W_DOWNLOW = dict(sweep=22, lift=-36, bank=24, elbow=6, wrist=-2, fan=0.55, sec_fan=0.7, tip_curl=-12.0)
W_COCK = dict(sweep=-16, lift=44, bank=-22, elbow=14, wrist=-6, fan=1.12, sec_fan=1.0)
W_COCKMORE = dict(sweep=-22, lift=50, bank=-20, elbow=14, wrist=-6, fan=1.2, sec_fan=1.05)
W_CUT = dict(sweep=76, lift=2, bank=10, elbow=0, wrist=0, fan=0.08, sec_fan=0.2)
W_CUTOVER = dict(sweep=92, lift=-2, bank=16, elbow=-4, wrist=2, fan=0.45, sec_fan=0.5, tip_curl=-8.0)
W_FULL = dict(sweep=0, lift=6, bank=0, elbow=0, wrist=0, fan=1.15, sec_fan=1.1)
W_FULLUP = dict(sweep=-6, lift=24, bank=-8, elbow=0, wrist=0, fan=1.18, sec_fan=1.12)
W_GLIDE = dict(sweep=-12, lift=14, bank=-10, elbow=8, wrist=-8, fan=0.92, sec_fan=1.0)
W_LOOSE = dict(sweep=-45, lift=-6, bank=-38, elbow=110, wrist=-112, fan=0.2, sec_fan=0.3)      # folded, slack
W_DRAG = dict(sweep=-6, lift=-24, bank=14, elbow=12, wrist=-4, fan=0.5, sec_fan=0.7, tip_curl=-10.0)   # hanging, dragging


def stand_feet(lz=-1.9, rz=-2.7, taul=44.0, taur=52.0, spread=0.0):
    spread = 0.0
    return {"Left": dict(ball=V((-3.4 - spread, 1.0, lz)), tau=taul), "Right": dict(ball=V((3.4 + spread, 1.0, rz)), tau=taur)}


def crouch_feet(spread=0.0, z=None, tau=62.0):
    """The same two spots it stands on, the legs folded to `tau` (a crouch moves the hips over its feet; the feet do not walk)."""
    return {"Left": dict(ball=V((-3.4, 1.0, -1.9)), tau=tau), "Right": dict(ball=V((3.4, 1.0, -2.7)), tau=tau + 6.0)}


STATES = {}


def states():
    """The poses it holds in each state (whole poses, every joint)."""
    out = {}
    out["Guardian"] = key(0.0)
    out["Returning"] = key(0.0, wl=W_HALF, wr=W_HALF, body=dict(Head=(2.0, 0, 0), Chest=(2.0, 0, 0)), shift=(-0.3, 0.0), feet=stand_feet(-2.1, -2.1, 46, 46))
    # roosting: low on its legs, the wings drawn round it like a cloak, the head tucked back under the near wing
    out["Dormant"] = key(0.0, shift=(-2.6, 0.3), wl=dict(FOLDED, bank=-62, sweep=-48, elbow=126, wrist=-128), wr=dict(FOLDED, bank=-62, sweep=-48, elbow=126, wrist=-128),
                         body=dict(Hips=(-4, 0, 0), Spine=(2, 0, 0), Chest=(-6, -14, 0), Neck1=(-34, -26, 8), Neck2=(40, -30, 6), Neck3=(26, -34, 4), Head=(14, -30, 10)),
                         feet=crouch_feet(0.3, -2.3, 58.0), tail={"TailBase": (-2, 0, 0)}, crest={"CrestA": (-12, 0, 0)})
    out["Resting"] = out["Dormant"]
    # worn out: sunk onto its breast, the near wing dragging, the head low, the tail on the ground
    out["Weakened"] = key(0.0, shift=(-5.0, -1.0), wl=W_LOOSE, wr=W_DRAG,
                          body=dict(Hips=(-10, 0, 3), Spine=(-8, 0, 0), Chest=(-14, 0, -2), Neck1=(-28, 0, 0), Neck2=(22, 0, 0), Neck3=(-24, 0, 0), Head=(-6, 0, 0)),
                          feet=crouch_feet(0.9, -3.4, 70.0), tail={"TailBase": (-6, 0, 0)}, crest={"CrestA": (-26, 0, 0)})
    # the threat display: up on its legs, the wings half spread and held high, the head low on a coiled neck, the crest erect
    out["Enraged"] = key(0.0, shift=(0.2, 0.0), wl=dict(W_HALF, lift=26, fan=0.85, sweep=-12), wr=dict(W_HALF, lift=26, fan=0.85, sweep=-12),
                         body=dict(Hips=(-3, 0, 0), Spine=(-2, 0, 0), Chest=(6, 0, 0), Neck1=(-14, 0, 0), Neck2=(16, 0, 0), Neck3=(-12, 0, 0), Head=(-4, 0, 0), Jaw=(-8, 0, 0)),
                         feet=stand_feet(-2.2, -2.6, 40, 40, 0.9), tail={"TailBase": (14, 0, 0)}, crest={"CrestA": (-6, 0, 0)})
    return out


def moves():
    """Every timed move: a list of keys. The blow of each lands at the fight's wind-up time."""
    M = {}
    # ---- WingScythe: turns its shoulder, throws the near (right) wing back and up, holds, whips it across in a flat arc
    turn = dict(Hips=(2, -7, 5.0), Spine=(0, -5, -1), Chest=(4, -16, -2), Neck1=(-6, 8, 0), Neck2=(8, 11, 0), Neck3=(-3, 6, 0), Head=(5, 4, 0))
    cock = dict(Hips=(3, -12, 6.0), Spine=(0, -8, -1), Chest=(6, -25, -3), Neck1=(-6, 10, 0), Neck2=(8, 14, 0), Neck3=(-3, 9, 0), Head=(5, 6, 0))
    cut = dict(Hips=(-2, 10, 4.0), Spine=(-2, 8, -1), Chest=(-6, 26, -4), Neck1=(-8, -8, 0), Neck2=(6, -12, 0), Neck3=(-5, -8, 0), Head=(2, -5, 0))
    over = dict(Hips=(-3, 13, 4.0), Spine=(-3, 11, -1), Chest=(-8, 32, -5), Neck1=(-10, -10, 0), Neck2=(6, -14, 0), Neck3=(-6, -10, 0), Head=(0, -6, 0))
    ft = stand_feet(-1.9, -2.7, 40, 58)
    M["WingScythe"] = [
        key(0.0),
        key(0.28, "out", body=turn, shift=(-1.2, 0.0), wr=dict(W_HALF, sweep=-35, lift=12, bank=-40, elbow=70, wrist=-72, fan=0.5), wl=dict(W_HALF, lift=8), feet=ft,
            tail={"TailBase": (8, -6, 0)}),
        key(0.50, "inout", body=cock, shift=(-1.7, 0.0), wr=W_COCK, wl=dict(sweep=-40, lift=24, bank=-20, elbow=20, wrist=-20, fan=0.7, sec_fan=0.8), feet=ft,
            tail={"TailBase": (10, -10, 0)}, crest={"CrestA": (-10, 0, 0)}),
        key(0.58, "inout", body=cock, shift=(-1.8, 0.0), wr=W_COCKMORE, wl=dict(sweep=-42, lift=27, bank=-20, elbow=20, wrist=-20, fan=0.72, sec_fan=0.8), feet=ft,
            tail={"TailBase": (10, -12, 0)}),
        key(0.80, "in2", body=cut, shift=(-2.1, 0.0), wr=W_CUT, wl=dict(sweep=-56, lift=36, bank=-24, elbow=26, wrist=-28, fan=0.85, sec_fan=0.9), feet=ft,
            tail={"TailBase": (8, 16, 0)}, lag=dict(Wing=0.0, Chest=0.03, Neck1=0.05, Neck2=0.07, Neck3=0.09, Head=0.11)),
        key(0.92, "snap", body=over, shift=(-2.0, 0.0), wr=W_CUTOVER, wl=dict(sweep=-60, lift=40, bank=-26, elbow=30, wrist=-30, fan=0.9, sec_fan=0.9), feet=ft,
            tail={"TailBase": (8, 22, 0)}),
        key(1.28, "out", body=dict(Hips=(1, 4, 3), Spine=(0, 3, -1), Chest=(3, 10, -2), Neck1=(-5, -2, 0), Neck2=(7, -3, 0), Neck3=(-3, -2, 0), Head=(5, -1, 0)), shift=(-1.0, 0.0),
            wr=dict(sweep=44, lift=22, bank=-20, elbow=40, wrist=-45, fan=0.55, sec_fan=0.6), wl=W_HALF, feet=ft, tail={"TailBase": (6, 8, 0)}),
        key(1.60, "inout", feet=ft, tail={"TailBase": (6, 0, 0)}),
        key(1.90, "inout"),
    ]
    # ---- CinderGale: sinks, both wings sweep up and back overhead, the chest swells, the head thrown back, beak open; holds; hammers down
    sink = dict(Hips=(-5, 0, 0), Spine=(-3, 0, 0), Chest=(-8, 0, 0), Neck1=(-16, 0, 0), Neck2=(14, 0, 0), Neck3=(-10, 0, 0), Head=(-8, 0, 0))
    up = dict(Hips=(2, 0, 0), Spine=(3, 0, 0), Chest=(14, 0, 0), Neck1=(6, 0, 0), Neck2=(12, 0, 0), Neck3=(14, 0, 0), Head=(26, 0, 0), Jaw=(-26, 0, 0))
    top = dict(Hips=(3, 0, 0), Spine=(4, 0, 0), Chest=(18, 0, 0), Neck1=(8, 0, 0), Neck2=(14, 0, 0), Neck3=(16, 0, 0), Head=(32, 0, 0), Jaw=(-34, 0, 0))
    hammer = dict(Hips=(-10, 0, 0), Spine=(-9, 0, 0), Chest=(-17, 0, 0), Neck1=(-17, 0, 0), Neck2=(8, 0, 0), Neck3=(-10, 0, 0), Head=(-10, 0, 0), Jaw=(-4, 0, 0))
    after = dict(Hips=(-12, 0, 0), Spine=(-10, 0, 0), Chest=(-19, 0, 0), Neck1=(-19, 0, 0), Neck2=(8, 0, 0), Neck3=(-12, 0, 0), Head=(-12, 0, 0), Jaw=(-2, 0, 0))
    cf = crouch_feet(0.7, -2.5, 60)
    cf2 = crouch_feet(0.9, -2.6, 68)
    M["CinderGale"] = [
        key(0.0),
        key(0.38, "out", body=sink, shift=(-3.0, 0.0), wl=dict(W_HALF, lift=8, sweep=-40), wr=dict(W_HALF, lift=8, sweep=-40), feet=cf, tail={"TailBase": (-8, 0, 0)}, crest={"CrestA": (-8, 0, 0)}),
        key(0.78, "inout", body=up, shift=(-1.8, 0.0), wl=W_UP, wr=W_UP, feet=crouch_feet(0.6, -2.4, 52), tail={"TailBase": (14, 0, 0)}, crest={"CrestA": (-26, 0, 0)}),
        key(1.12, "out", body=top, shift=(-1.0, 0.0), wl=W_UPWIDE, wr=W_UPWIDE, feet=crouch_feet(0.6, -2.3, 46), tail={"TailBase": (20, 0, 0)}, crest={"CrestA": (-34, 0, 0)}),
        key(1.30, "in2", body=hammer, shift=(-3.6, -0.4), wl=W_DOWN, wr=W_DOWN, feet=cf2, tail={"TailBase": (26, 0, 0)}, crest={"CrestA": (-4, 0, 0)}),
        key(1.46, "snap", body=after, shift=(-3.9, -0.5), wl=W_DOWNLOW, wr=W_DOWNLOW, feet=cf2, tail={"TailBase": (34, 0, 0)}),
        key(1.95, "out", body=dict(Hips=(-4, 0, 0), Spine=(-3, 0, 0), Chest=(-6, 0, 0), Neck1=(-10, 0, 0), Neck2=(10, 0, 0), Neck3=(-6, 0, 0), Head=(-4, 0, 0)), shift=(-2.0, 0.0),
            wl=dict(W_HALF, lift=4, sweep=-35, fan=0.6), wr=dict(W_HALF, lift=4, sweep=-35, fan=0.6), feet=cf, tail={"TailBase": (4, 0, 0)}),
        key(2.5, "inout"),
    ]
    return M


THRUST = {"Thigh": (76, 0, 0), "Shin": (-12, 0, 0), "Tarsus": (24, 0, 0), "Foot": (14, 0, 0), "Toes": (20, 0, 0), "Hallux": (44, 0, 0)}
THRUST2 = {"Thigh": (84, 0, 0), "Shin": (-16, 0, 0), "Tarsus": (30, 0, 0), "Foot": (12, 0, 0), "Toes": (26, 0, 0), "Hallux": (48, 0, 0)}
BRACE = {"Thigh": (62, 0, 0), "Shin": (-8, 0, 0), "Tarsus": (14, 0, 0), "Foot": (6, 0, 0), "Toes": (-2, 0, 0), "Hallux": (34, 0, 0)}


def free(d):
    return {"free": {k: v for k, v in d.items()}}


AHEAD = {"Left": dict(ball=V((-3.4, 1.0, -5.4)), tau=30.0), "Right": dict(ball=V((3.4, 1.0, -5.4)), tau=30.0)}
FLARE_BODY = dict(Hips=(2, 0, 0), Spine=(2, 0, 0), Chest=(8, 0, 0), Neck1=(-6, 0, 0), Neck2=(8, 0, 0), Neck3=(-4, 0, 0), Head=(4, 0, 0))


def reach_legs():
    """The legs as they are when the talons touch down ahead: solved once, then held as free angles by the end of the dive."""
    k = key(0.0, body=FLARE_BODY, shift=(0.0, 0.0), wl=dict(sweep=-6, lift=24, bank=-8, elbow=0, wrist=0, fan=1.18, sec_fan=1.12), wr=dict(sweep=-6, lift=24, bank=-8, elbow=0, wrist=0, fan=1.18, sec_fan=1.12), feet=AHEAD)
    return {tag: _planted_euler(k, tag) for tag in ("Left", "Right")}


def moves_more(M):
    # ---- TalonDive (0.9 s on the ground, 1.0 s in the air): crouch, spring, glide with the talons forward, land
    aim = dict(Hips=(-6, 0, 0), Spine=(-4, 0, 0), Chest=(-18, 0, 0), Neck1=(-26, 0, 0), Neck2=(10, 0, 0), Neck3=(-14, 0, 0), Head=(-22, 0, 0))
    aim2 = dict(Hips=(-8, 0, 0), Spine=(-6, 0, 0), Chest=(-22, 0, 0), Neck1=(-30, 0, 0), Neck2=(12, 0, 0), Neck3=(-16, 0, 0), Head=(-26, 0, 0))
    drive = dict(Hips=(-12, 0, 0), Spine=(-10, 0, 0), Chest=(-26, 0, 0), Neck1=(-10, 0, 0), Neck2=(4, 0, 0), Neck3=(-8, 0, 0), Head=(-18, 0, 0))
    glide = dict(Hips=(-16, 0, 0), Spine=(-12, 0, 0), Chest=(-22, 0, 0), Neck1=(2, 0, 0), Neck2=(0, 0, 0), Neck3=(0, 0, 0), Head=(-12, 0, 0), Jaw=(0, 0, 0))
    stoop = dict(Hips=(-18, 0, 0), Spine=(-14, 0, 0), Chest=(-26, 0, 0), Neck1=(4, 0, 0), Neck2=(-2, 0, 0), Neck3=(0, 0, 0), Head=(-16, 0, 0))
    flare = dict(Hips=(2, 0, 0), Spine=(2, 0, 0), Chest=(8, 0, 0), Neck1=(-6, 0, 0), Neck2=(8, 0, 0), Neck3=(-4, 0, 0), Head=(4, 0, 0))
    reach = (reach_legs()["Left"], reach_legs()["Right"])
    c70 = crouch_feet(0.0, 0.0, 72)
    cw = dict(sweep=-30, lift=52, bank=-20, elbow=34, wrist=-30, fan=0.75, sec_fan=0.85)
    cw2 = dict(sweep=-32, lift=60, bank=-22, elbow=30, wrist=-26, fan=0.85, sec_fan=0.9)
    push = {"Left": dict(ball=V((-3.4, 3.2, -1.9)), tau=16.0, foot=-20.0, toes=-12.0), "Right": dict(ball=V((3.4, 3.2, -2.7)), tau=16.0, foot=-20.0, toes=-12.0)}
    M["TalonDive"] = [
        key(0.0),
        key(0.34, "out", body=aim, shift=(-4.4, 0.0), wl=cw, wr=cw, feet=c70, tail={"TailBase": (22, 0, 0)}, crest={"CrestA": (-14, 0, 0)}),
        key(0.66, "inout", body=aim2, shift=(-4.8, 0.2), wl=cw2, wr=cw2, feet=crouch_feet(0.8, -2.8, 76), tail={"TailBase": (26, 0, 0)}),
        key(0.82, "in2", body=drive, shift=(1.2, -1.0), wl=W_DOWN, wr=W_DOWN, feet=push, tail={"TailBase": (-6, 0, 0)}),
        key(0.90, "snap", body=drive, shift=(2.4, -2.0), wl=W_DOWNLOW, wr=W_DOWNLOW, feet=push, tail={"TailBase": (-10, 0, 0)}),
        key(1.14, "out", body=glide, shift=(0.0, 0.0), wl=W_GLIDE, wr=W_GLIDE, feet={"Left": free(THRUST), "Right": free(THRUST)}, tail={"TailBase": (-12, 0, 0)}, crest={"CrestA": (-30, 0, 0)}),
        key(1.60, "inout", body=stoop, shift=(0.0, 0.0), wl=dict(W_GLIDE, lift=26, fan=1.0), wr=dict(W_GLIDE, lift=26, fan=1.0), feet={"Left": free(THRUST2), "Right": free(THRUST2)}, tail={"TailBase": (-14, 0, 0)}),
        key(1.80, "inout", body=flare, shift=(0.0, 0.0), wl=W_FULLUP, wr=W_FULLUP, feet={"Left": free(BRACE), "Right": free(BRACE)}, tail={"TailBase": (4, 0, 0)}),
        key(1.95, "out", body=flare, shift=(0.0, 0.0), wl=W_FULLUP, wr=W_FULLUP, feet={"Left": free(reach[0]), "Right": free(reach[1])}, tail={"TailBase": (4, 0, 0)}),
    ]
    # ---- Land: the talons reach the ground ahead, the legs take the weight in a deep crush, the wings flaring for balance, then it rises
    ahead = {"Left": dict(ball=V((-3.4, 1.0, -5.4)), tau=30.0, toes=0.0), "Right": dict(ball=V((3.4, 1.0, -5.4)), tau=30.0, toes=0.0)}
    ahead2 = {"Left": dict(ball=V((-3.6, 1.0, -5.0)), tau=70.0), "Right": dict(ball=V((3.6, 1.0, -5.0)), tau=70.0)}
    M["Land"] = [
        key(0.0, "smooth", body=flare, shift=(0.0, 0.0), wl=W_FULLUP, wr=W_FULLUP, feet=AHEAD, tail={"TailBase": (4, 0, 0)}),
        key(0.08, "snap", body=dict(Hips=(-6, 0, 0), Spine=(-4, 0, 0), Chest=(-8, 0, 0), Neck1=(-6, 0, 0), Neck2=(8, 0, 0), Neck3=(-8, 0, 0), Head=(-2, 0, 0)), shift=(-3.4, -0.6),
            wl=dict(W_FULLUP, lift=30, fan=1.2), wr=dict(W_FULLUP, lift=30, fan=1.2), feet=ahead, tail={"TailBase": (14, 0, 0)}),
        key(0.20, "out", body=dict(Hips=(-9, 0, 0), Spine=(-6, 0, 0), Chest=(-12, 0, 0), Neck1=(-10, 0, 0), Neck2=(8, 0, 0), Neck3=(-8, 0, 0), Head=(-4, 0, 0)), shift=(-5.0, -1.0),
            wl=dict(W_FULL, lift=20, fan=1.2), wr=dict(W_FULL, lift=20, fan=1.2), feet=ahead2, tail={"TailBase": (22, 0, 0)}),
        key(0.50, "inout", body=dict(Hips=(-3, 0, 0), Spine=(-2, 0, 0), Chest=(-2, 0, 0), Neck1=(-6, 0, 0), Neck2=(8, 0, 0), Neck3=(-5, 0, 0), Head=(2, 0, 0)), shift=(-2.4, -0.4),
            wl=dict(W_HALF, lift=12, fan=0.9), wr=dict(W_HALF, lift=12, fan=0.9), feet={"Left": dict(ball=V((-3.4, 1.0, -3.6)), tau=58.0), "Right": dict(ball=V((3.4, 1.0, -3.8)), tau=58.0)}, tail={"TailBase": (8, 0, 0)}),
        key(0.90, "inout", feet={"Left": dict(ball=V((-3.4, 1.0, -2.2)), tau=44.0), "Right": dict(ball=V((3.4, 1.0, -2.8)), tau=52.0)}),
    ]
    # ---- Awaken (2.8 s): the veins flicker, the head lifts from under the wing and shakes, the wings unfold to their full span, a shiver, it stands tall and lowers into its stance
    dorm = states()["Dormant"]
    lift1 = dict(Neck1=(-24, -14, 6), Neck2=(30, -18, 4), Neck3=(14, -20, 4), Head=(8, -16, 6), Chest=(-3, -8, 0))
    free_head = dict(Neck1=(-6, -4, 0), Neck2=(10, -3, 0), Neck3=(-2, -2, 0), Head=(4, -2, 0), Chest=(0, -2, 0))
    base_up = dict(dorm, body=dict(dorm["body"], **free_head))
    M["Awaken"] = [
        merge_key(dorm, 0.0),
        merge_key(dorm, 0.45, "inout", body=dict(Chest=(-3, -14, 0), Hips=(-3, 0, 0))),
        merge_key(dorm, 0.85, "inout", body=lift1),
        merge_key(dorm, 1.10, "out", body=dict(free_head, Head=(4, 14, 0)), shift=(-2.2, 0.2)),
        merge_key(dorm, 1.24, "inout", body=dict(free_head, Head=(4, -13, 0))),
        merge_key(dorm, 1.36, "inout", body=dict(free_head, Head=(4, 9, 0))),
        merge_key(dorm, 1.48, "inout", body=dict(free_head, Head=(4, -4, 0))),
        merge_key(dorm, 1.62, "inout", body=dict(free_head, Head=(4, 0, 0)), wl=dict(W_LOOSE, lift=2, sweep=-40), wr=dict(W_LOOSE, lift=2, sweep=-40)),
        merge_key(dorm, 2.06, "inout", body=dict(Hips=(2, 0, 0), Spine=(3, 0, 0), Chest=(14, 0, 0), Neck1=(2, 0, 0), Neck2=(10, 0, 0), Neck3=(6, 0, 0), Head=(18, 0, 0), Jaw=(-14, 0, 0)), shift=(0.4, 0.0),
                  wl=W_FULLUP, wr=W_FULLUP, feet=stand_feet(-2.0, -2.2, 38, 38, 0.8), tail={"TailBase": (22, 0, 0)}, crest={"CrestA": (-34, 0, 0)}),
        merge_key(dorm, 2.30, "inout", body=dict(Hips=(2, 0, 0), Spine=(3, 0, 0), Chest=(12, 0, 0), Neck1=(2, 0, 0), Neck2=(10, 0, 0), Neck3=(6, 0, 0), Head=(14, 0, 0), Jaw=(-4, 0, 0)), shift=(0.4, 0.0),
                  wl=W_FULLUP, wr=W_FULLUP, feet=stand_feet(-2.0, -2.2, 38, 38, 0.8), tail={"TailBase": (22, 0, 0)}, crest={"CrestA": (-30, 0, 0)}),
        key(2.8, "inout"),
    ]
    # ---- Enrage (1.4 s): rears up on its toes, the wings flung wide, the head thrown back screeching, the crest erect; then settles into the half-spread threat
    rear = dict(Hips=(-2, 0, 0), Spine=(2, 0, 0), Chest=(15, 0, 0), Neck1=(3, 0, 0), Neck2=(6, 0, 0), Neck3=(4, 0, 0), Head=(30, 0, 0), Jaw=(-38, 0, 0))
    toes = {"Left": dict(ball=V((-3.4, 3.7, -1.9)), tau=14.0, foot=-22.0, toes=-14.0), "Right": dict(ball=V((3.4, 3.7, -2.7)), tau=14.0, foot=-22.0, toes=-14.0)}
    drop = dict(Hips=(-4, 0, 0), Spine=(-3, 0, 0), Chest=(-6, 0, 0), Neck1=(-18, 0, 0), Neck2=(18, 0, 0), Neck3=(-14, 0, 0), Head=(-10, 0, 0), Jaw=(-10, 0, 0))
    en = states()["Enraged"]
    M["Enrage"] = [
        key(0.0),
        key(0.20, "snap", body=rear, shift=(2.4, -0.2), wl=W_FULL, wr=W_FULL, feet=toes, tail={"TailBase": (30, 0, 0)}, crest={"CrestA": (-46, 0, 0)}),
        key(0.62, "linear", body=dict(rear, Head=(27, 0, 0), Chest=(13, 0, 0)), shift=(2.2, -0.2), wl=dict(W_FULL, lift=12, fan=1.2), wr=dict(W_FULL, lift=12, fan=1.2), feet=toes, tail={"TailBase": (28, 0, 0)}, crest={"CrestA": (-46, 0, 0)}),
        key(0.98, "in2", body=drop, shift=(-1.2, -0.4), wl=dict(W_HALF, lift=30, fan=0.95), wr=dict(W_HALF, lift=30, fan=0.95), feet=stand_feet(-2.2, -2.6, 52, 52, 1.0), tail={"TailBase": (6, 0, 0)}, crest={"CrestA": (-10, 0, 0)}),
        merge_key(en, 1.40, "back"),
    ]
    # ---- Weaken (1.9 s): a stagger, the legs buckling, one wing falling and dragging, sinking onto its breast, the head dropping
    wk = states()["Weakened"]
    M["Weaken"] = [
        key(0.0),
        key(0.16, "snap", body=dict(Hips=(2, 0, 3), Chest=(14, 0, -2), Neck1=(6, 0, 0), Neck2=(10, 0, 0), Neck3=(6, 0, 0), Head=(22, 0, 0), Jaw=(-22, 0, 0)), shift=(-0.9, 0.2),
            wl=dict(W_HALF, lift=20, fan=1.0), wr=dict(W_HALF, lift=20, fan=1.0), tail={"TailBase": (14, 0, 0)}, crest={"CrestA": (-30, 0, 0)}),
        key(0.55, "inout", body=dict(Hips=(-4, 0, 4), Spine=(-3, 0, 0), Chest=(-6, 0, -2), Neck1=(-14, 0, 0), Neck2=(12, 0, 0), Neck3=(-8, 0, 0), Head=(-2, 0, 0)), shift=(-2.8, -0.3),
            wl=W_LOOSE, wr=dict(W_DRAG, lift=-12), feet=crouch_feet(0.6, -2.8, 62), tail={"TailBase": (-4, 0, 0)}, crest={"CrestA": (-16, 0, 0)}),
        key(0.95, "in", body=wk["body"], shift=wk["shift"], wl=W_LOOSE, wr=W_DRAG, feet=wk["feet"], tail=wk["tail"], crest=wk["crest"]),
        key(1.30, "back", body=wk["body"], shift=wk["shift"], wl=W_LOOSE, wr=W_DRAG, feet=wk["feet"], tail=wk["tail"], crest=wk["crest"]),
        merge_key(wk, 1.9, "inout"),
    ]
    return M


def merge_key(base, t, ease_name="smooth", lag=None, **over):
    """A key laid over another key's numbers (a state's), at time t."""
    return key(t, ease_name, base=base, lag=lag, **over)


_moves_first = moves


def moves():
    return moves_more(_moves_first())


STRIP_TIMES = {"WingScythe": [0.0, 0.28, 0.50, 0.64, 0.74, 0.80, 0.92, 1.28], "CinderGale": [0.0, 0.38, 0.78, 1.12, 1.26, 1.30, 1.46, 1.95],
               "TalonDive": [0.0, 0.34, 0.66, 0.82, 0.90, 1.14, 1.60, 1.95], "Land": [0.0, 0.04, 0.08, 0.14, 0.20, 0.35, 0.50, 0.90],
               "Awaken": [0.0, 0.85, 1.10, 1.36, 1.62, 2.06, 2.30, 2.8], "Enrage": [0.0, 0.10, 0.20, 0.62, 0.80, 0.98, 1.20, 1.40],
               "Weaken": [0.0, 0.16, 0.35, 0.55, 0.75, 0.95, 1.30, 1.9]}


# ---------------------------------------------------------------- the gaits: a heavy walk and the run it chases at
GAITS = {"walk": dict(reach=2.6, stance=0.62, lift=2.4, bob=0.35, drop=0.7, lean=-2.0, roll=3.2, yaw=3.0, speed=9.0, wings=dict(FOLDED, lift=-3)),
         "run": dict(reach=3.8, stance=0.45, lift=3.6, bob=0.8, drop=1.2, lean=-9.0, roll=2.6, yaw=3.0, speed=20.0,
                     wings=dict(sweep=-40, lift=4, bank=-45, elbow=118, wrist=-120, fan=0.3, sec_fan=0.4))}
Z0 = FEET["Right"].z


def stride_of(g):
    return 2 * g["reach"] / g["stance"]


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def foot_at(g, p):
    """The ball of a foot at share p of its cycle (0: it comes down ahead of the body): (ball, tau, foot, toes)."""
    p %= 1.0
    S = g["stance"]
    r = g["reach"]
    if p < S:
        u = p / S
        return V((0, 1.0, Z0 - r + 2 * r * u)), lerp(54.0, 2.0, u ** 1.15), 0.0, 14.0 * (1 - smooth01(u / 0.12))
    w = (p - S) / (1 - S)
    z = Z0 + r - 2 * r * smooth01(w)
    y = 1.0 + g["lift"] * math.sin(math.pi * w) ** 1.2
    tau = lerp(2.0, 54.0, smooth01(w)) + 26.0 * math.sin(math.pi * w)
    foot = 14.0 * math.sin(math.pi * min(1.0, w * 1.4))
    clear = smooth01((y - 1.0) / (0.7 * g["lift"]))                  # the toes curl only once the foot is clear of the ground
    toes = -22.0 * clear * (1 - smooth01((w - 0.7) / 0.3)) + 14.0 * smooth01((w - 0.85) / 0.15)
    return V((0, y, z)), tau, foot, toes


def gait_key(name, phase):
    """One moment of a gait as a pose: the left foot comes down at phase 0, the right at 0.5."""
    g = GAITS[name]
    a = 2 * math.pi * phase
    mid = g["stance"] / 2
    body = {"Hips": (g["lean"] * 0.4, g["yaw"] * math.sin(a - mid * 6.283), -g["roll"] * math.cos(a - mid * 6.283) + 2.5),
            "Spine": (0, -g["yaw"] * 0.5 * math.sin(a - mid * 6.283), g["roll"] * 0.5 * math.cos(a - mid * 6.283)),
            "Chest": (3.0 + g["lean"] * 0.8, -g["yaw"] * 0.9 * math.sin(a - mid * 6.283), g["roll"] * 0.6 * math.cos(a - mid * 6.283) - 1.5),
            "Neck1": (-4.0 - g["lean"] * 0.3 + 3.0 * math.sin(2 * a + 0.4), 0, 0), "Neck2": (7.0 - g["lean"] * 0.2 + 4.0 * math.sin(2 * a + 0.2), 0, 0),
            "Neck3": (-3.0 + 2.0 * math.sin(2 * a), 0, 0), "Head": (5.0 - g["lean"] * 0.4 - 3.0 * math.sin(2 * a + 0.2), 0, 0), "Jaw": (0, 0, 0)}
    shift = (-g["drop"] + g["bob"] * math.cos(4 * math.pi * (phase - mid)), 0.0)
    feet = {}
    for tag, off in (("Left", 0.0), ("Right", 0.5)):
        ball, tau, foot, toes = foot_at(g, phase + off)
        feet[tag] = dict(ball=V((FEET[tag].x, ball.y, ball.z)), tau=tau, foot=foot, toes=toes, hallux=-toes * 0.5)
    w = dict(g["wings"])
    wl = dict(w, lift=w.get("lift", 0) + 1.6 * math.sin(4 * math.pi * phase + 0.6))
    wr = dict(w, lift=w.get("lift", 0) + 1.6 * math.sin(4 * math.pi * phase + 1.2))
    tail = {"TailBase": (6.0 + (8.0 if name == "run" else 2.0) * math.sin(4 * math.pi * phase + 1.0), 5.0 * math.sin(a + 0.5), 0)}
    crest = {"CrestA": (4.0 - (10.0 if name == "run" else 0.0), 0, 0)}
    return build_pose(body=body, shift=shift, wl=wl, wr=wr, feet=feet, tail=tail, crest=crest)


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
    for name, k in states().items():
        pose, shift, _ = build_pose(body=k["body"], shift=k["shift"], wl=k["wl"], wr=k["wr"], feet=k["feet"], tail=k["tail"], crest=k["crest"])
        sp[name] = (pose, shift)
    # two held flourishes the idle layer blends in now and then
    g = states()["Guardian"]
    disp = merge(g, dict(wl=dict(W_HALF, lift=22, fan=0.9), wr=dict(W_HALF, lift=22, fan=0.9), body=dict(Chest=(9, 0, 0), Neck1=(-2, 0, 0), Neck2=(9, 0, 0), Neck3=(-1, 0, 0), Head=(9, 0, 0)), crest={"CrestA": (-26, 0, 0)}, shift=(0.0, 0.0)))
    pr = merge(g, dict(wr=dict(sweep=-10, lift=34, bank=-30, elbow=80, wrist=-55, fan=0.8, sec_fan=0.9), body=dict(Chest=(2, -16, 0), Neck1=(-26, -22, 6), Neck2=(34, -28, 6), Neck3=(18, -26, 4), Head=(18, -22, 8)), shift=(-0.9, 0.0)))
    for name, k in (("Display", disp), ("Preen", pr)):
        pose, shift, _ = build_pose(body=k["body"], shift=k["shift"], wl=k["wl"], wr=k["wr"], feet=k["feet"], tail=k["tail"], crest=k["crest"])
        sp[name] = (pose, shift)
    return sp


def bake_move(keys, fps=30):
    """Dense frames of a move: ([{joint: values}], [(planted left, planted right)])."""
    base = {n: (0, 0, 0) for n in JOINTS}
    frames, plants, prev = [], [], None
    length = keys[-1]["t"]
    for f in range(int(round(length * fps)) + 1):
        pose, shift, pl = sample(keys, min(f / fps, length))
        ref = prev or full(*state_tables()["Guardian"], base)
        v = full(pose, shift, {n: ref[n][:3] for n in JOINTS})
        frames.append(v)
        plants.append((pl["Left"], pl["Right"]))
        prev = v
    return frames, plants


def bake_gait(name, steps=24):
    guardian = full(*state_tables()["Guardian"], {n: (0, 0, 0) for n in JOINTS})
    frames, prev = [], guardian
    for i in range(steps):
        pose, shift, _ = gait_key(name, i / steps)
        v = full(pose, shift, {n: prev[n][:3] for n in JOINTS})
        frames.append({n: [v[n][k] - guardian[n][k] for k in range(len(v[n]))] for n in JOINTS})
        prev = v
    return frames


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


def anchors():
    """Where things truly are at each blow, for the effects (the guardian's own axes, feet on y = 0)."""
    out = {}
    mv = moves()

    def at(name, t, bone, end=True):
        pose, shift, _ = sample(mv[name], t)
        st = fk(pose, shift)
        p = tip(st, bone) if end else st[bone][1]
        return [round(p.x, 1), round(p.y, 1), round(p.z, 1)]

    out["ScytheTip"] = at("WingScythe", 0.80, "RightPrim2B")
    out["ScytheMid"] = at("WingScythe", 0.80, "RightHand", end=False)
    out["GaleLeft"] = at("CinderGale", 1.30, "LeftPrim2B")
    out["GaleRight"] = at("CinderGale", 1.30, "RightPrim2B")
    out["GaleGround"] = [0.0, 0.6, round(min(out["GaleLeft"][2], out["GaleRight"][2]) * 0.55, 1)]
    out["DiveFeet"] = [0.0, 0.6, -2.3]
    out["LandFeet"] = [0.0, 0.6, -5.4]
    out["Mouth"] = at("Enrage", 0.62, "Head")
    out["Crown"] = at("Awaken", 2.3, "Head", end=False)
    out["Keel"] = [0.0, 0.6, -6.0]
    out["TailTip"] = at("WingScythe", 0.0, "Tail0C")
    out["CrestTip"] = at("WingScythe", 0.0, "CrestB")
    return out


def write_clips(path, fps=30):
    """src/client/Guardians/GuardianRigs/CinderRocClips.lua, generated: the poses, the gaits and the moves as data the rig plays."""
    sts = state_tables()
    base = {n: (0, 0, 0) for n in JOINTS}
    guardian = full(*sts["Guardian"], base)
    lines = ["-- Written by tools/blender/guardians/cinder_roc.py (cinder_roc_motion.write_clips): do not edit by hand. Angles in degrees,",
             "-- [pitch, yaw, roll]; the hips also carry [lift, slide] in studs. Poses are whole poses (every joint); Gaits are changes from how it",
             "-- stands (24 frames a cycle); Moves are tracks of [frame, values...] at Fps, only for the joints the move drives, each held to a",
             "-- tolerance of 0.2 degrees (0.03 studs); Plants lists the frames a foot is off the ground.", "local Clips = {}", "Clips.Fps = %d" % fps,
             "Clips.Joints = " + _lua(JOINTS), "Clips.Anchors = " + _lua(anchors()),
             "Clips.Strides = " + _lua({n: round(stride_of(g), 2) for n, g in GAITS.items()}), "Clips.Stance = " + _lua({n: g["stance"] for n, g in GAITS.items()}),
             "Clips.Speed = " + _lua({n: g["speed"] for n, g in GAITS.items()})]
    lines.append("Clips.Poses = {")
    for name, (pose, shift) in sts.items():
        v = full(pose, shift, guardian)
        lines.append("%s=%s," % (name, _lua({n: [round(x, 2) for x in v[n]] for n in JOINTS})))
    lines.append("}")
    lines.append("Clips.Gaits = {")
    for name in GAITS:
        frames = bake_gait(name)
        keep = {n: [fr[n] for fr in frames] for n in JOINTS if any(abs(x) > 0.3 for fr in frames for x in fr[n])}
        lines.append("%s=%s," % (name, _lua(keep)))
    lines.append("}")
    lines.append("Clips.Moves = {")
    worst = {}
    for name, keys in moves().items():
        frames, plants = bake_move(keys, fps)
        tracks = {}
        for n in JOINTS:
            rows = [fr[n] for fr in frames]
            ref = guardian[n]
            if not any(abs(r[k] - ref[k]) > 0.2 for r in rows for k in range(len(r))):
                continue
            tol = [0.2, 0.2, 0.2, 0.03, 0.03][:len(rows[0])]
            kept = reduce_track(rows, tol)
            err = 0.0
            for a, b in zip(kept, kept[1:]):
                for i in range(a, b + 1):
                    u = (i - a) / (b - a)
                    err = max(err, max(abs(rows[i][k] - (rows[a][k] + (rows[b][k] - rows[a][k]) * u)) / tol[k] for k in range(len(tol))))
            worst[name] = max(worst.get(name, 0.0), err)
            tracks[n] = [[f] + [round(x, 2) for x in rows[f]] for f in kept]
        free = {}
        for i, tag in enumerate(("Left", "Right")):
            spans, start = [], None
            for f, pl in enumerate(plants):
                if not pl[i] and start is None:
                    start = f
                if pl[i] and start is not None:
                    spans.append([start, f - 1])
                    start = None
            if start is not None:
                spans.append([start, len(plants) - 1])
            free[tag] = spans
        lines.append("%s={Length=%s,Tracks=%s,Plants=%s}," % (name, _lua(keys[-1]["t"]), _lua(tracks), _lua(free)))
    lines.append("}")
    lines.append("return Clips")
    with open(path, "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")
    import os as _os
    return {"bytes": _os.path.getsize(path), "worst reduction error (x tolerance)": {k: round(v, 2) for k, v in worst.items()}, "anchors": anchors()}
