"""Tiangou v3's motion: how it stands, walks, gallops, bites, howls, leaps, wakes, rages and weakens, solved here and played by the game (run inside Blender).

A pose is {bone: (pitch, yaw, roll) in degrees} and the hips' (lift, slide) in studs, in the guardian's own axes, each bone's turn on top of its
parent's, exactly as the game's joints work (GuardianAnim: Bone.Transform = rest^-1 * turn * rest). A positive pitch lifts the front of a
forward-pointing bone and tips a vertical one back; it lowers the tip of a back-pointing one (the tail: its raise is written negative); it swings a
down-pointing limb's far end FORWARD. Positive yaw turns a bone's far end to its left.

The legs are solved, not keyed: a foot stays planted at its world spot while the hips move over it (three bones in the vertical plane through the
hip and the foot: the pastern's lean is chosen, the foot stays flat). A foreleg's elbow is behind its line (the upper arm runs down and back) and a
hind leg's stifle is in front of it. A foot with no ground under it is just a target in the air.
"""
import math

from mathutils import Matrix, Quaternion, Vector

from tiangou_v3_bones import BONES, ECLIPSE, ECLIPSE_R, STREAMS, joints, stream_dir

V = Vector
RAD = math.radians
DEG = math.degrees
LEGS = ("FrontLeft", "FrontRight", "BackLeft", "BackRight")
FRONT = ("FrontLeft", "FrontRight")


# ---------------------------------------------------------------- rotations
def mat(a):
    """Rx(pitch) Ry(yaw) Rz(roll), as CFrame.Angles."""
    return Matrix.Rotation(RAD(a[0]), 3, "X") @ Matrix.Rotation(RAD(a[1]), 3, "Y") @ Matrix.Rotation(RAD(a[2]), 3, "Z")


def euler(m):
    e = m.to_euler("ZYX")
    return (DEG(e.x), DEG(e.y), DEG(e.z))


def frame(a, b):
    a = V(a).normalized()
    b = V(b) - a * V(b).dot(a)
    b = b.normalized()
    return Matrix((a, b, a.cross(b))).transposed()


def rb_rot(m):
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


def orient(pose, shift, bone, want_dir, want_up, rest_up=(0, 0, 1)):
    """Turn `bone` (under its parent as now posed) so its length points along want_dir and its face (rest: toward +Z) looks along want_up."""
    parent = BONES[bone][0]
    pr = fk(pose, shift)[parent][0]
    rest = frame(rest_dir(bone), rest_up)
    want = frame(want_dir, want_up)
    pose[bone] = euler(pr.inverted() @ want @ rest.inverted())


# ---------------------------------------------------------------- the legs
def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _plane_angle(name):
    d = V(BONES[name][2]) - V(BONES[name][1])
    return DEG(math.atan2(-d.z, -d.y))


def _len(name):
    return (V(BONES[name][2]) - V(BONES[name][1])).length


LEG = {}
for _leg in LEGS:
    _front = _leg in FRONT
    _names = ("Upper", "Lower", "Paw", "Toes") if _front else ("Thigh", "Shin", "Meta", "Toes")
    LEG[_leg] = dict(front=_front, U=_leg + _names[0], L=_leg + _names[1], P=_leg + _names[2], F=_leg + _names[3], S=(_leg + "Scapula") if _front else None,
                     lu=_len(_leg + _names[0]), ll=_len(_leg + _names[1]), lp=_len(_leg + _names[2]),
                     a={n: _plane_angle(_leg + n) for n in _names}, ball=V(BONES[_leg + _names[3]][1]), tau=_plane_angle(_leg + _names[2]))
REST_BALL = {leg: LEG[leg]["ball"] for leg in LEGS}
REST_TAU = {leg: LEG[leg]["tau"] for leg in LEGS}


def leg(pose, shift, name, ball, tau=None, foot=0.0):
    """Puts the leg `name` (a key of LEGS) on `ball`, the world spot of its toes' joint (x, y, z): the pastern leans `tau` degrees (from straight
    down toward the front; None keeps it as at rest), the foot's pitch is `foot` (0 as at rest). The leg lies in the vertical plane through its
    shoulder or hip and the ball. A foreleg's scapula must already be posed. Returns the reach and the bone angles used."""
    d = LEG[name]
    state = fk(pose, shift)
    parent_rot = state[BONES[d["U"]][0]][0]
    hip = state[d["U"]][1]
    B = V(ball)
    v = B - hip
    # the leg's plane: it holds the hip and the ball, but a ball straight under the hip leaves it undecided, so there it keeps the parent's heading
    fwd = parent_rot @ V((0, 0, -1))
    psi_p = math.atan2(-fwd.x, -fwd.z)
    wrap = lambda x: (x + math.pi) % (2 * math.pi) - math.pi
    # the foot is planted along the body's heading only: a yawed spine moves the shoulder sideways and the paw does not chase it (the game's own
    # foot solve works in the leg's plane too); a commanded stray from the standing line (a sidestep) is kept
    f_p = V((-math.sin(psi_p), 0, -math.cos(psi_p)))
    r_p = V((math.cos(psi_p), 0, -math.sin(psi_p)))
    stray = B.x - d["ball"].x
    v = f_p * v.dot(f_p) + r_p * stray + V((0, v.y, 0))
    vh = math.hypot(v.x, v.z)
    psi_v = math.atan2(-v.x, -v.z)
    dpsi = wrap(psi_v - psi_p)
    if abs(dpsi) > math.pi / 2:
        dpsi = wrap(dpsi - math.copysign(math.pi, dpsi))
    w = smooth01((vh - 0.3) / 1.4)
    psi = psi_p + w * dpsi
    s = v.x * -math.sin(psi) + v.z * -math.cos(psi)
    plane = Matrix.Rotation(psi, 3, "Y")
    t = RAD(d["tau"] if tau is None else tau)
    wrist_f, wrist_y = s - d["lp"] * math.sin(t), B.y + d["lp"] * math.cos(t)
    df, dy = wrist_f, wrist_y - hip.y
    dist = max(min(math.hypot(df, dy), (d["lu"] + d["ll"]) * 0.998), abs(d["lu"] - d["ll"]) + 0.05)
    aim = math.atan2(df, -dy)
    alpha = math.acos(max(-1, min(1, (d["lu"] ** 2 + dist ** 2 - d["ll"] ** 2) / (2 * d["lu"] * dist))))
    beta = math.acos(max(-1, min(1, (d["ll"] ** 2 + dist ** 2 - d["lu"] ** 2) / (2 * d["ll"] * dist))))
    if d["front"]:
        w_up, w_lo = aim - alpha, aim + beta           # the elbow behind the line
    else:
        w_up, w_lo = aim + alpha, aim - beta           # the stifle in front of it
    a = d["a"]
    names = (d["U"], d["L"], d["P"], d["F"])
    keys = list(a)
    targets = [w_up - RAD(a[keys[0]]), w_lo - RAD(a[keys[1]]), t - RAD(a[keys[2]]), RAD(foot)]
    prev = parent_rot
    for n, tg in zip(names, targets):
        world = plane @ Matrix.Rotation(tg, 3, "X")
        pose[n] = euler(prev.inverted() @ world)
        prev = world
    return {"reach": dist, "max": d["lu"] + d["ll"]}


# ---------------------------------------------------------------- applying a pose to the Blender armature, for the renders
def set_pose(pose, shift=(0.0, 0.0), rig="TiangouV3Rig"):
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
TAIL = ["Tail%d" % i for i in range(1, 7)]
EARS = {"Left": ("LeftEarA", "LeftEarB"), "Right": ("RightEarA", "RightEarB")}
STREAM_NAMES = [("Stream%dA" % (i + 1), "Stream%dB" % (i + 1)) for i in range(STREAMS)]


def tail_pose(raise_=0.0, sway=0.0, curl=0.0, wag=0.0):
    """The tail as six bones: `raise_` degrees up over the whole tail (spread, the tip more), `sway` yaw, `curl` a bend that grows toward the tip,
    `wag` extra yaw at the tip."""
    out = {}
    for i, n in enumerate(TAIL):
        f = (i + 1) / 6.0
        out[n] = (-(raise_ / 6.0) * (0.6 + 0.8 * f) + curl * f * 0.9, sway / 6.0 + wag * f * f, 0.0)
    return out


def ear_pose(back=0.0, splay=0.0, twist=0.0, left=None, right=None):
    """Both ears: tipped back `back` degrees, splayed out `splay`; left/right override (back, splay)."""
    out = {}
    for tag, sign, over in (("Left", -1, left), ("Right", 1, right)):
        b, s = over if over else (back, splay)
        a, c = EARS[tag]
        out[a] = (b * 0.55, 0.0, sign * s * 0.5 + twist)
        out[c] = (b * 0.45, 0.0, sign * s * 0.5)
    return out


def ruff_pose(up=0.0, flare=0.0):
    out = {"RuffTopA": (-up * 0.6, 0, 0), "RuffTopB": (-up * 0.8, 0, 0), "ChestTuftA": (up * 0.3, 0, 0), "ChestTuftB": (up * 0.4, 0, 0)}
    for tag, sign in (("Left", -1), ("Right", 1)):
        out[tag + "Ruff1"] = (-up * 0.3, 0, sign * flare)
        out[tag + "Ruff2"] = (-up * 0.4, 0, sign * flare)
    return out


def stream_pose(pose, shift, lean=(0.5, 0.9), flare=0.0, droop=0.0):
    """The corona's streamers: each lies in the ring's plane turned back by `lean` (a, b) as a share of its length, plus `flare` (bends it upward),
    with `droop` pulling the lower ones down."""
    for i, (a, b) in enumerate(STREAM_NAMES):
        dx, dy = stream_dir(i)
        up_share = flare * max(0.0, dy) + droop * max(0.0, -dy)
        for name, k in ((a, lean[0]), (b, lean[1])):
            d = V((dx, dy + up_share * 0.4, k)).normalized()
            orient(pose, shift, name, d, (0, 0, 1), (0, 0, 1))


def build_pose(spec):
    """A whole pose from a key's numbers: body {bone: euler}, shift (lift, slide), feet {leg: dict(ball, tau, foot, scap) or {"free": {bone: euler}}},
    stream dict(lean, flare, droop). Returns (pose, shift, planted {leg: bool})."""
    pose = dict(spec.get("body", {}))
    shift = spec.get("shift", (0.0, 0.0))
    feet = spec.get("feet", {})
    plants = {}
    # the scapulas first (they move the shoulder the foreleg hangs from)
    for name in FRONT:
        f = feet.get(name, {})
        if "free" not in f:
            pose[name + "Scapula"] = (f.get("scap", 0.0), 0.0, 0.0)
    for name in LEGS:
        f = dict(feet.get(name, {}))
        if "free" in f:
            for bone, e in f["free"].items():
                pose[bone] = e
            plants[name] = False
        else:
            f.pop("scap", None)
            ball = f.pop("ball", REST_BALL[name])
            leg(pose, shift, name, ball, f.get("tau"), f.get("foot", 0.0))
            plants[name] = ball[1] < 1.05 and not f.get("air")
    # the eclipse floats on its stalk: it keeps itself nearly upright while the chest pitches under it
    cp = euler(fk(pose, shift)["Chest"][0])[0]
    for n, k in (("Stalk1", -0.45), ("Stalk2", -0.25), ("EclipseRing", -0.1)):
        if n not in pose:
            pose[n] = (k * cp, 0.0, 0.0)
    st = spec.get("stream")
    if st is not None:
        stream_pose(pose, shift, **st)
    return pose, shift, plants


# ---------------------------------------------------------------- keys
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


LAG = {"Hips": 0.0, "SpineA": 0.012, "SpineB": 0.024, "Chest": 0.036, "Neck1": 0.05, "Neck2": 0.066, "Neck3": 0.082, "Head": 0.096, "Jaw": 0.03}
for _i, _n in enumerate(TAIL):
    LAG[_n] = 0.03 + 0.025 * _i
for _t in ("Left", "Right"):
    for _s in ("A", "B"):
        LAG["%sEar%s" % (_t, _s)] = 0.05 + 0.03 * (_s == "B")
    LAG[_t + "Ruff1"], LAG[_t + "Ruff2"] = 0.06, 0.09
LAG.update({"RuffTopA": 0.05, "RuffTopB": 0.08, "ChestTuftA": 0.05, "ChestTuftB": 0.08, "Stalk1": 0.05, "Stalk2": 0.07, "EclipseRing": 0.1})


def slerp_euler(a, b, u):
    qa, qb = mat(a).to_quaternion(), mat(b).to_quaternion()
    if qa.dot(qb) < 0:
        qb = -qb
    axis, angle = qa.rotation_difference(qb).to_axis_angle()
    return euler((qa @ Quaternion(axis, angle * u)).to_matrix())


def lerp(a, b, u):
    return a + (b - a) * u


def merge(base, over):
    """A key's numbers: the base's with each part of `over` laid over it (body and stream merge key by key; feet merge per leg)."""
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base.items()}
    for k, v in over.items():
        if k == "feet":
            out["feet"] = dict(out.get("feet", {}))
            for tag, spec in v.items():
                old = out["feet"].get(tag, {})
                out["feet"][tag] = spec if "free" in spec else {**({} if "free" in old else old), **spec}
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


def key(t, ease_name="smooth", base=None, lag=None, **over):
    k = merge(base if base is not None else GUARDIAN, over)
    k["t"], k["ease"], k["lag"] = t, ease_name, dict(LAG, **(lag or {}))
    return k


def _planted_euler(k, tag):
    pose, shift, _ = build_pose({**k, "feet": {tag: k["feet"][tag]}})
    return {n: pose[n] for n in (LEG[tag]["U"], LEG[tag]["L"], LEG[tag]["P"], LEG[tag]["F"])}


STREAM_DEFAULT = dict(lean=(0.5, 0.9), flare=0.0, droop=0.0)


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
    feet = {}
    for tag in LEGS:
        fa, fb = a["feet"].get(tag, {}), b["feet"].get(tag, {})
        ul = u_of(0.0)
        if "free" not in fa and "free" not in fb:
            spec = {"ball": V(fa.get("ball", REST_BALL[tag])).lerp(V(fb.get("ball", REST_BALL[tag])), ul)}
            for name, dflt in (("tau", REST_TAU[tag]), ("foot", 0.0), ("scap", 0.0)):
                spec[name] = lerp(fa.get(name, dflt), fb.get(name, dflt), ul)
            spec["air"] = fa.get("air", False) or fb.get("air", False) if ul > 0.5 else fa.get("air", False)
            feet[tag] = spec
        else:
            ea = fa["free"] if "free" in fa else _planted_euler(a, tag)
            eb = fb["free"] if "free" in fb else _planted_euler(b, tag)
            feet[tag] = {"free": {n: slerp_euler(ea.get(n, (0, 0, 0)), eb.get(n, (0, 0, 0)), ul) for n in set(ea) | set(eb)}}
    sa, sb = a.get("stream", STREAM_DEFAULT), b.get("stream", STREAM_DEFAULT)
    us = u_of(lag.get("EclipseRing", 0.1))
    stream = dict(lean=tuple(lerp(x, y, us) for x, y in zip(sa["lean"], sb["lean"])), flare=lerp(sa["flare"], sb["flare"], us), droop=lerp(sa["droop"], sb["droop"], us))
    return build_pose({"body": body, "shift": shift, "feet": feet, "stream": stream})


# ---------------------------------------------------------------- the poses and the moves
def B(**kw):
    """A body dict from keyword euler tuples (bone names without 'Left'... as is) merged with helper dicts."""
    return dict(kw)


def feet(front=(-9.4, -9.4), back=(4.9, 4.9), y=0.9, x_front=2.6, x_back=2.55, tauf=None, taub=None, foot=0.0, scap=0.0, lifts=None):
    """Four feet: the z of each foot's toe joint (front left/right, back left/right), planted at height y unless `lifts` {leg: y}."""
    lifts = lifts or {}
    out = {}
    for name, z, x in (("FrontLeft", front[0], -x_front), ("FrontRight", front[1], x_front), ("BackLeft", back[0], -x_back), ("BackRight", back[1], x_back)):
        out[name] = dict(ball=V((x, lifts.get(name, y), z)), tau=(tauf if name in FRONT else taub) if (tauf if name in FRONT else taub) is not None else REST_TAU[name],
                         foot=foot, scap=scap if name in FRONT else 0.0)
    return out


def join(*dicts):
    out = {}
    for d in dicts:
        out.update(d)
    return out


GUARDIAN_BODY = join(
    {"Hips": (0.0, 0, 0), "SpineA": (0.0, 0, 0), "SpineB": (0.0, 0, 0), "Chest": (0.0, 0, 0), "Neck1": (0, 0, 0), "Neck2": (0, 0, 0), "Neck3": (0, 0, 0), "Head": (0, 0, 0), "Jaw": (0, 0, 0)},
    tail_pose(0, 0, 0))
GUARDIAN = dict(body=GUARDIAN_BODY, shift=(0.0, 0.0), feet=feet(), stream=dict(STREAM_DEFAULT))


def with_(base, **over):
    return merge(base, over)


STATES = {}


def states():
    """Whole poses held in each state."""
    out = {}
    out["Guardian"] = key(0.0)
    out["Returning"] = key(0.0, body={"Neck1": (-3, 0, 0), "Neck2": (-3, 0, 0), "Head": (6, 0, 0)}, stream=dict(lean=(0.7, 1.2), flare=0.0, droop=0.0))
    # asleep: curled on the cold court, nose under the tail
    lie = dict(front=(-12.6, -12.0), back=(1.8, 1.0))
    flat = key(0.0, shift=(-4.8, 1.2), body=join({"Hips": (-4, 0, 0), "SpineA": (2, 0, 0), "SpineB": (0, 0, 0), "Chest": (4, 0, 0)}), feet=feet(front=lie["front"], back=lie["back"], tauf=60, taub=55))
    # the legs of a curled body are solved with the curl taken out and then follow the curled spine (a foot planted in the world would twist them)
    legs_free = {l: {"free": _planted_euler(flat, l)} for l in LEGS}
    out["Dormant"] = key(0.0, shift=(-4.8, 1.2), body=join(
        {"Hips": (-4, 14, 0), "SpineA": (2, 22, 0), "SpineB": (0, 26, 0), "Chest": (4, 26, 0), "Neck1": (14, 36, 0), "Neck2": (22, 38, 0), "Neck3": (6, 30, 0), "Head": (-24, 18, 0), "Jaw": (0, 0, 0)},
        tail_pose(26, 10, -6), ear_pose(back=50, splay=-10), ruff_pose(-6, -4)),
        feet=legs_free, stream=dict(lean=(0.3, 0.5), flare=0.0, droop=0.9))
    out["Resting"] = out["Dormant"]
    out["Weakened"] = key(0.0, shift=(-4.6, 0.5), body=join(
        {"Hips": (6, 0, 0), "SpineA": (-2, 0, 0), "SpineB": (-4, 0, 0), "Chest": (-12, 0, 0), "Neck1": (18, 0, 0), "Neck2": (16, 0, 0), "Neck3": (-26, 0, 0), "Head": (-14, 0, 0), "Jaw": (-5, 0, 0)},
        tail_pose(22, 6, -4), ear_pose(back=40, splay=6), ruff_pose(-8, -6)),
        feet=feet(front=(-12.4, -12.2), back=(2.4, 2.4), tauf=48, taub=40), stream=dict(lean=(0.25, 0.4), flare=0.0, droop=1.0))
    out["Enraged"] = key(0.0, shift=(-2.6, -0.8), body=join(
        {"Hips": (10, 0, 0), "SpineA": (4, 0, 0), "SpineB": (-4, 0, 0), "Chest": (-14, 0, 0), "Neck1": (6, 0, 0), "Neck2": (-6, 0, 0), "Neck3": (-18, 0, 0), "Head": (-10, 0, 0), "Jaw": (-14, 0, 0)},
        tail_pose(16, 0, -10), ear_pose(back=70, splay=4), ruff_pose(16, 10)),
        feet=feet(front=(-11.4, -11.4), back=(3.0, 3.0), tauf=50, taub=30, scap=10), stream=dict(lean=(0.8, 1.3), flare=0.8, droop=0.0))
    return out


def hold(base, t, ease_name="smooth", lag=None, **over):
    """A key laid over another key's numbers at time t."""
    return key(t, ease_name, base=base, lag=lag, **over)


def neck(n1=0, n2=0, n3=0, head=0, jaw=0, yaw=(0, 0, 0, 0), roll=0):
    return {"Neck1": (n1, yaw[0], roll * 0.3), "Neck2": (n2, yaw[1], roll * 0.3), "Neck3": (n3, yaw[2], roll * 0.4), "Head": (head, yaw[3], roll), "Jaw": (jaw, 0, 0)}


def spine(h=0, a=0, b=0, c=0, yaw=(0, 0, 0, 0), roll=(0, 0, 0, 0)):
    return {"Hips": (h, yaw[0], roll[0]), "SpineA": (a, yaw[1], roll[1]), "SpineB": (b, yaw[2], roll[2]), "Chest": (c, yaw[3], roll[3])}


def moves():
    """Every timed move: a list of keys. The blow of each lands at the fight's wind-up time."""
    M = {}
    # ---- Bite (0.5 s): the haunches load and the weight settles back, the head draws back and low, the lips lift and the ruff bristles (held); then the
    # body drives forward off the hind legs, the forefeet reach and plant, the neck extends, and the jaws snap shut on the contact frame
    load = join(spine(6, 2, -2, -4), neck(14, 10, -8, -10, -8), tail_pose(8, 0, 0), ear_pose(back=55, splay=4), ruff_pose(14, 8))
    drawn = join(spine(8, 2, -3, -6), neck(20, 14, -12, -14, -18), tail_pose(12, 0, 0), ear_pose(back=62, splay=4), ruff_pose(22, 12))
    reach = join(spine(-2, -2, -3, -4), neck(-22, 2, 0, 34, -46), tail_pose(20, 0, 4), ear_pose(back=70), ruff_pose(8, 4))
    snap = join(spine(-3, -3, -4, -5), neck(-28, 4, 2, 32, 0), tail_pose(24, 0, 6), ear_pose(back=72), ruff_pose(6, 2))
    hb = feet(back=(4.0, 4.0), tauf=None, taub=34, scap=-3)
    M["Bite"] = [
        key(0.0),
        key(0.22, "out", shift=(-1.5, 0.5), body=load, feet=hb, stream=dict(lean=(0.8, 1.3), flare=0.5, droop=0.0)),
        key(0.40, "inout", shift=(-1.9, 1.0), body=drawn, feet=feet(back=(3.8, 3.8), taub=32, scap=-5), stream=dict(lean=(0.9, 1.5), flare=0.8, droop=0.0)),
        key(0.47, "in", shift=(-0.6, -3.0), body=reach, feet=join(feet(back=(4.9, 4.9), taub=40), {"FrontLeft": dict(ball=V((-2.6, 1.8, -12.6)), scap=10), "FrontRight": dict(ball=V((2.6, 1.8, -12.6)), scap=10)}),
            stream=dict(lean=(0.3, 0.5), flare=0.6, droop=0.0), lag=dict(Neck1=0.02, Neck2=0.03, Neck3=0.04, Head=0.05, Jaw=0.0)),
        key(0.50, "snap", shift=(0.0, -4.4), body=snap, feet=feet(front=(-13.2, -13.2), back=(4.9, 4.9), scap=14, taub=44), stream=dict(lean=(0.2, 0.4), flare=0.2, droop=0.0), lag=dict(Jaw=0.0, Head=0.02)),
        key(0.60, "out", shift=(-0.6, -3.6), body=join(spine(-2, -2, -3, -4), neck(-24, 3, 1, 30, -8, yaw=(0, 3, 7, 9)), tail_pose(20, 0, 3), ear_pose(back=70), ruff_pose(10, 6)),
            feet=feet(front=(-13.2, -13.2), back=(4.9, 4.9), scap=12, taub=44), stream=dict(lean=(0.5, 0.9), flare=0.3, droop=0.0)),
        key(0.72, "inout", shift=(-0.8, -3.0), body=join(spine(-2, -2, -3, -4), neck(-18, 2, 0, 24, -6, yaw=(0, -3, -6, -8)), tail_pose(16, 0, 2), ear_pose(back=66), ruff_pose(12, 6)),
            feet=feet(front=(-13.2, -13.2), back=(4.9, 4.9), scap=10, taub=42), stream=dict(lean=(0.7, 1.1), flare=0.3, droop=0.0)),
        key(0.90, "inout", shift=(-1.2, -0.9), body=join(spine(0, -2, -3, -4), neck(-8, 0, 0, 10, -4, yaw=(0, 2, 4, 6)), tail_pose(10, 0, 0), ear_pose(back=58), ruff_pose(10, 6)),
            feet=feet(front=(-13.0, -13.0), back=(4.9, 4.9), scap=8, taub=40)),
        key(1.12, "inout", shift=(-0.9, -0.3), body=join(spine(2, 1, -1, -3), neck(0, 0, 0, 0, 0), tail_pose(6, 0, 0), ear_pose(back=40), ruff_pose(6, 3)),
            feet=feet(front=(-11.6, -11.6), back=(4.9, 4.9), scap=4, lifts={"FrontLeft": 2.6, "FrontRight": 0.9})),
        key(1.35, "inout", shift=(-0.3, 0.0), feet=feet(front=(-10.0, -10.4), lifts={"FrontLeft": 0.9, "FrontRight": 2.2})),
        key(1.8, "inout"),
    ]
    # ---- EclipseHowl (1.0 s): it sits back and rears onto its haunches, the forelegs lift off, the chest swells, the head is thrown to the sky, the
    # mouth open while the eclipse swells and the corona flares; at the contact the full howl; then the forelegs drop and the ground takes the weight
    sit = join(spine(14, 3, 2, 4), neck(6, 8, 2, 4, 0), tail_pose(24, 0, 0), ear_pose(back=40), ruff_pose(10, 4))
    rear = join(spine(28, 5, 3, 5), neck(8, 12, 8, 10, -22), tail_pose(48, 0, 0), ear_pose(back=34, splay=6), ruff_pose(22, 12))
    howl = join(spine(31, 6, 4, 6), neck(8, 12, 8, 4, -42), tail_pose(62, 0, 0), ear_pose(back=28, splay=8), ruff_pose(30, 18))
    up_front = {"FrontLeft": dict(ball=V((-2.6, 7.4, -12.2)), tau=78, foot=-30, scap=14), "FrontRight": dict(ball=V((2.6, 7.4, -12.2)), tau=78, foot=-30, scap=14)}
    M["EclipseHowl"] = [
        key(0.0),
        key(0.38, "out", shift=(-2.6, 1.4), body=sit, feet=feet(back=(3.6, 3.6), taub=22), stream=dict(lean=(0.7, 1.1), flare=0.6, droop=0.0)),
        key(0.80, "inout", shift=(-4.4, 2.2), body=rear, feet=join(feet(back=(3.2, 3.2), taub=16), up_front), stream=dict(lean=(0.3, 0.5), flare=1.0, droop=0.0)),
        key(1.0, "snap", shift=(-4.8, 2.4), body=howl, feet=join(feet(back=(3.2, 3.2), taub=16), up_front), stream=dict(lean=(0.0, 0.1), flare=1.5, droop=0.0), lag=dict(Head=0.03, Jaw=0.0)),
        key(1.28, "linear", shift=(-4.8, 2.4), body=join(howl, {"Head": (6, 0, 0)}), feet=join(feet(back=(3.2, 3.2), taub=16), up_front), stream=dict(lean=(0.1, 0.2), flare=1.3, droop=0.0)),
        key(1.52, "in", shift=(-4.0, 1.6), body=join(spine(22, 4, 2, 2), neck(6, 8, 4, 14, -10), tail_pose(30, 0, 0), ear_pose(back=40), ruff_pose(14, 8)),
            feet=join(feet(back=(3.4, 3.4), taub=18), {"FrontLeft": dict(ball=V((-2.6, 3.0, -11.6)), tau=60, scap=8), "FrontRight": dict(ball=V((2.6, 3.0, -11.6)), tau=60, scap=8)}), stream=dict(lean=(0.5, 0.8), flare=0.8, droop=0.0)),
        key(1.66, "snap", shift=(-3.2, 0.8), body=join(spine(6, 1, -1, -6), neck(-4, -4, -2, -4, -6), tail_pose(6, 0, 0), ear_pose(back=50), ruff_pose(8, 4)),
            feet=feet(front=(-11.0, -11.0), back=(3.6, 3.6), scap=8, taub=20), stream=dict(lean=(0.6, 1.0), flare=0.2, droop=0.2)),
        key(2.0, "out", shift=(-1.0, 0.3), body=join(spine(1, 0, 0, -1), neck(0, 0, 0, 0, 0), tail_pose(4, 0, 0), ear_pose(back=20), ruff_pose(4, 2)), feet=feet(front=(-10.0, -10.0), back=(4.6, 4.6), scap=2)),
        key(2.6, "inout"),
    ]
    # ---- MoonLeap (0.55 s on the ground, then 1.2 s in the air): a fast crouch, the spring, a flight stretched flat, the forelegs reaching for the ground
    crouch = join(spine(8, 2, -2, -14), neck(-4, -8, -8, 6, -4), tail_pose(12, 0, 0), ear_pose(back=48), ruff_pose(12, 6))
    coil = join(spine(12, 3, -3, -18), neck(-6, -10, -8, 8, -6), tail_pose(14, 0, 0), ear_pose(back=54), ruff_pose(16, 8))
    spring = join(spine(-6, -6, -6, -8), neck(-12, -10, -4, 0, -8), tail_pose(22, 0, 0), ear_pose(back=66), ruff_pose(10, 4))
    flat = join(spine(-4, -3, -2, -3), neck(-16, -12, -4, -2, -12), tail_pose(26, 0, 0), ear_pose(back=72), ruff_pose(8, 4))
    pre = join(spine(-2, 0, 2, 6), neck(-10, -6, -2, 0, -4), tail_pose(18, 0, 0), ear_pose(back=62), ruff_pose(8, 4))
    reach_down = {"FrontLeft": dict(ball=V((-2.6, 1.0, -14.2)), tau=30, scap=16, air=True), "FrontRight": dict(ball=V((2.6, 1.0, -14.2)), tau=30, scap=16, air=True),
                  "BackLeft": dict(ball=V((-2.55, 3.4, 8.2)), tau=40, air=True), "BackRight": dict(ball=V((2.55, 3.4, 8.2)), tau=40, air=True)}
    M["MoonLeap"] = [
        key(0.0),
        key(0.30, "out", shift=(-3.4, 0.4), body=crouch, feet=feet(front=(-12.0, -12.0), back=(4.2, 4.2), taub=14, scap=8), stream=dict(lean=(0.8, 1.2), flare=0.4, droop=0.0)),
        key(0.46, "inout", shift=(-3.8, 1.0), body=coil, feet=feet(front=(-12.4, -12.4), back=(4.6, 4.6), taub=12, scap=10), stream=dict(lean=(0.9, 1.4), flare=0.6, droop=0.0)),
        key(0.55, "snap", shift=(1.0, -1.8), body=spring, feet={"FrontLeft": dict(ball=V((-2.6, 3.6, -12.6)), tau=48, scap=14, air=True), "FrontRight": dict(ball=V((2.6, 3.6, -12.6)), tau=48, scap=14, air=True),
                                                              "BackLeft": dict(ball=V((-2.55, 2.4, 7.2)), tau=60, foot=-26, air=True), "BackRight": dict(ball=V((2.55, 2.4, 7.2)), tau=60, foot=-26, air=True)},
            stream=dict(lean=(0.6, 1.2), flare=0.4, droop=0.0), lag=dict(Hips=0.0, SpineA=0.01, SpineB=0.02, Chest=0.03)),
        key(0.82, "out", shift=(1.4, -2.4), body=flat, feet={"FrontLeft": dict(ball=V((-2.6, 5.6, -16.6)), tau=26, foot=14, scap=20, air=True), "FrontRight": dict(ball=V((2.6, 5.4, -16.8)), tau=26, foot=14, scap=20, air=True),
                                                              "BackLeft": dict(ball=V((-2.55, 4.4, 11.6)), tau=70, foot=-30, air=True), "BackRight": dict(ball=V((2.55, 4.8, 11.4)), tau=70, foot=-30, air=True)},
            stream=dict(lean=(1.2, 2.0), flare=0.0, droop=0.0)),
        key(1.30, "inout", shift=(1.0, -1.8), body=pre, feet=join(reach_down, {"FrontLeft": dict(ball=V((-2.6, 2.6, -15.0)), tau=28, scap=18, air=True), "FrontRight": dict(ball=V((2.6, 2.6, -15.0)), tau=28, scap=18, air=True),
                                                                              "BackLeft": dict(ball=V((-2.55, 4.6, 10.0)), tau=50, air=True), "BackRight": dict(ball=V((2.55, 4.6, 10.0)), tau=50, air=True)}),
            stream=dict(lean=(1.0, 1.7), flare=0.0, droop=0.0)),
        key(1.75, "inout", shift=(0.4, -1.5), body=join(spine(-4, -2, 0, 4), neck(-8, -4, 0, 4, -4), tail_pose(14, 0, 0), ear_pose(back=60), ruff_pose(6, 3)), feet=reach_down,
            stream=dict(lean=(0.9, 1.5), flare=0.0, droop=0.0)),
    ]
    # ---- Land (1.2 s): the forepaws first, the forelegs absorbing, the spine compressing, the hind legs coming through, a skid and a settle
    land_front = {"FrontLeft": dict(ball=V((-2.6, 0.9, -14.2)), tau=30, scap=16), "FrontRight": dict(ball=V((2.6, 0.9, -14.2)), tau=30, scap=16)}
    M["Land"] = [
        key(0.0, "smooth", shift=(0.4, -1.5), body=join(spine(-4, -2, 0, 4), neck(-8, -4, 0, 4, -4), tail_pose(14, 0, 0), ear_pose(back=60), ruff_pose(6, 3)),
            feet=join(land_front, {"BackLeft": dict(ball=V((-2.55, 3.4, 8.2)), tau=40, air=True), "BackRight": dict(ball=V((2.55, 3.4, 8.2)), tau=40, air=True)}), stream=dict(lean=(0.9, 1.5), flare=0.0, droop=0.0)),
        key(0.10, "snap", shift=(-2.6, -2.0), body=join(spine(8, 3, -4, -14), neck(8, 10, 4, -2, 0), tail_pose(26, 0, 0), ear_pose(back=66), ruff_pose(14, 8)),
            feet=join(feet(front=(-13.6, -13.6), back=(7.0, 7.0), scap=14, lifts={"BackLeft": 2.6, "BackRight": 2.2}), {}), stream=dict(lean=(0.4, 0.6), flare=0.5, droop=0.0)),
        key(0.22, "out", shift=(-3.4, -1.2), body=join(spine(12, 4, -6, -16), neck(10, 12, 4, 0, 0), tail_pose(18, 0, 0), ear_pose(back=60), ruff_pose(16, 8)),
            feet=feet(front=(-13.0, -13.0), back=(6.0, 6.0), scap=14, taub=30), stream=dict(lean=(0.5, 0.8), flare=0.6, droop=0.0)),
        key(0.55, "out", shift=(-1.8, -0.4), body=join(spine(4, 1, -2, -6), neck(2, 2, 0, 0, 0), tail_pose(8, 0, 0), ear_pose(back=40), ruff_pose(8, 4)),
            feet=feet(front=(-11.4, -11.4), back=(5.4, 5.4), scap=6, taub=30)),
        key(0.90, "inout", shift=(-0.4, 0.0), feet=feet(front=(-9.8, -9.8), back=(5.0, 5.0))),
        key(1.2, "inout"),
    ]
    # ---- Awaken (2.8 s): from the curl: the head lifts, the forelegs push up, then the haunches; a shake from nose to tail that throws the ruff and plume, a
    # stretch (forelegs forward, haunches high), the ears coming up one after the other
    dorm = states()["Dormant"]
    stir = hold(dorm, 0.55, "inout", body=join(neck(14, 20, 6, -14, 0, yaw=(30, 32, 26, 10)), spine(-2, 2, 0, 4, yaw=(10, 16, 18, 20))), shift=(-4.7, 1.1))
    head_up = hold(dorm, 1.05, "inout", body=join(spine(0, 0, 4, 10, yaw=(4, 8, 8, 8)), neck(6, 10, 2, -6, 0, yaw=(14, 14, 10, 4)), ear_pose(left=(30, 0), right=(55, 0)), tail_pose(26, 4, -6)),
                   shift=(-5.0, 0.8), feet=feet(front=(-12.0, -11.8), back=(1.8, 1.4), tauf=50, taub=45))
    sit_up = hold(dorm, 1.45, "inout", body=join(spine(10, 4, 2, 6, yaw=(0, 2, 2, 2)), neck(4, 6, 0, 0, 0), ear_pose(back=20), tail_pose(30, 0, -4)), shift=(-3.2, 0.6),
                  feet=feet(front=(-11.0, -11.0), back=(2.6, 2.6), tauf=44, taub=30), stream=dict(lean=(0.7, 1.1), flare=0.2, droop=0.2))
    wave = dict(Head=0.0, Neck3=0.01, Neck2=0.02, Neck1=0.03, Chest=0.04, SpineB=0.06, SpineA=0.08, Hips=0.10)
    wave.update({n: 0.10 + 0.02 * i for i, n in enumerate(TAIL)})
    shake = lambda t, y, ease_name="inout": key(t, ease_name, body=join(spine(0, 0, 0, 0, yaw=(-y, -y * 0.6, y * 0.4, y * 0.9)), neck(0, 0, 0, 0, 0, yaw=(y * 0.6, y * 0.4, 0, -y * 0.5)), tail_pose(6, -y * 2.2, 0), ruff_pose(8, 4)),
                                               shift=(0, 0), lag=wave)
    stretch = key(2.3, "inout", shift=(0.8, -0.8), body=join(spine(-12, -6, -4, -6), neck(-6, -4, -2, 6, -16), tail_pose(22, 0, 0), ear_pose(back=10), ruff_pose(10, 6)),
                  feet=feet(front=(-13.4, -13.4), back=(4.9, 4.9), scap=14, taub=24), stream=dict(lean=(0.6, 1.0), flare=0.6, droop=0.0))
    M["Awaken"] = [
        key(0.0, "smooth", base=dorm),
        stir, head_up, sit_up,
        key(1.75, "out", shift=(0.0, 0.0), feet=feet(), stream=dict(lean=(0.5, 0.9), flare=0.3, droop=0.0)),
        shake(1.9, 9, "out"), shake(2.02, -11), shake(2.14, 8), shake(2.26, -4),
        key(2.28, "inout", body=GUARDIAN_BODY, lag=wave),
        stretch,
        key(2.62, "inout", shift=(0.0, 0.0), stream=dict(lean=(0.5, 0.9), flare=0.0, droop=0.0)),
        key(2.8, "inout"),
    ]
    # ---- Enrage (about 1.3 s): it snaps round, drops into the hunting crouch with a throat-deep snarl, the ruff and tail bristling; it does not howl
    en = states()["Enraged"]
    M["Enrage"] = [
        key(0.0),
        key(0.14, "snap", shift=(-1.6, -0.5), body=join(spine(4, 0, 0, 0, yaw=(-1, -2, -2, -3)), neck(-2, -2, -4, -2, -16, yaw=(20, 26, 22, 14)), tail_pose(14, 0, 0), ear_pose(back=66), ruff_pose(16, 8)),
            feet=feet(front=(-10.0, -10.0), back=(4.6, 4.6), scap=4, taub=40), stream=dict(lean=(0.5, 0.9), flare=0.8, droop=0.0), lag=dict(Head=0.0, Neck3=0.01, Neck2=0.02, Neck1=0.03)),
        hold(en, 0.45, "out", body=join(neck(6, -4, -14, -8, -22, yaw=(-4, -3, -2, -1)), ruff_pose(22, 12)), shift=(-3.0, -0.9), stream=dict(lean=(0.7, 1.2), flare=1.1, droop=0.0)),
        hold(en, 0.9, "linear", body=join(neck(6, -4, -18, -10, -26)), shift=(-2.8, -0.9)),
        hold(en, 1.3, "back"),
    ]
    # ---- Weaken (1.9 s): a stagger (a hard sidestep, the head dropping), the forelegs buckling, the body sinking to the court, the corona guttering
    wk = states()["Weakened"]
    M["Weaken"] = [
        key(0.0),
        key(0.16, "snap", shift=(-0.9, 0.3), body=join(spine(2, 0, 0, 0, yaw=(2, 3, 2, 1), roll=(3, 2, 1, 0)), neck(10, 8, -8, -22, -12, yaw=(-4, -4, -3, 0)), tail_pose(6, 0, 0), ear_pose(back=50, splay=6), ruff_pose(2, 0)),
            feet=join(feet(front=(-9.4, -9.4), back=(4.9, 4.9)), {"FrontLeft": dict(ball=V((-3.4, 2.2, -9.8)), scap=2)}), stream=dict(lean=(0.8, 1.2), flare=0.0, droop=0.3)),
        key(0.52, "inout", shift=(-3.0, 0.3), body=join(spine(5, 1, -2, -8), neck(14, 12, -10, -16, -8), tail_pose(2, 0, 4), ear_pose(back=48, splay=6), ruff_pose(-2, -2)),
            feet=feet(front=(-11.0, -11.2), back=(4.0, 4.0), tauf=44, taub=30, scap=6), stream=dict(lean=(0.5, 0.8), flare=0.0, droop=0.6)),
        key(0.95, "in", shift=wk["shift"], body=wk["body"], feet=wk["feet"], stream=wk["stream"]),
        key(1.28, "back", shift=(wk["shift"][0] + 0.25, wk["shift"][1]), body=wk["body"], feet=wk["feet"], stream=wk["stream"]),
        hold(wk, 1.9, "inout"),
    ]
    return M


STRIP_TIMES = {"Bite": [0.0, 0.22, 0.40, 0.47, 0.50, 0.60, 0.90, 1.35], "EclipseHowl": [0.0, 0.38, 0.80, 1.0, 1.28, 1.52, 1.66, 2.0],
               "MoonLeap": [0.0, 0.30, 0.46, 0.55, 0.82, 1.30, 1.75, 1.75], "Land": [0.0, 0.05, 0.10, 0.16, 0.22, 0.40, 0.70, 1.2],
               "Awaken": [0.0, 0.55, 1.05, 1.45, 1.9, 2.14, 2.3, 2.8], "Enrage": [0.0, 0.07, 0.14, 0.30, 0.45, 0.9, 1.1, 1.3],
               "Weaken": [0.0, 0.16, 0.34, 0.52, 0.75, 0.95, 1.28, 1.9]}
CONTACT = {"Bite": 0.50, "EclipseHowl": 1.0, "MoonLeap": 0.55, "Land": 0.0, "Weaken": 0.95}
MOVE_LENGTH = {"Bite": 1.8, "EclipseHowl": 2.6, "MoonLeap": 1.75, "Land": 1.2, "Awaken": 2.8, "Enrage": 1.3, "Weaken": 1.9}


# ---------------------------------------------------------------- the gaits: a heavy walk and the gallop it chases at
GAITS = {
    "walk": dict(stride=11.0, speed=14.0, duty=0.64, phase={"BackLeft": 0.0, "FrontLeft": 0.25, "BackRight": 0.5, "FrontRight": 0.75}, lift=3.0, yaw=1.4, roll=1.2, bob=0.35, flex=1.5, tail=4.0, lean=0.0),
    "run": dict(stride=17.5, speed=27.0, duty=0.30, phase={"BackLeft": 0.0, "BackRight": 0.09, "FrontRight": 0.48, "FrontLeft": 0.57}, lift=5.2, yaw=1.0, roll=0.9, bob=0.8, flex=9.0, tail=14.0, lean=-3.0),
}
STEPS = 32


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def stride_of(g):
    return g["stride"]


def foot_at(g, leg_name, p):
    """The ball of a foot at the gait's phase p: (ball, tau, foot)."""
    q = (p - g["phase"][leg_name]) % 1.0
    r = g["duty"] * g["stride"] / 2.0
    z0, x = REST_BALL[leg_name].z, REST_BALL[leg_name].x
    tau0 = REST_TAU[leg_name]
    if q < g["duty"]:
        u = q / g["duty"]
        return V((x, 0.9, z0 - r + 2 * r * u)), tau0 + 14.0 * (u - 0.3), -14.0 * smooth01((u - 0.75) / 0.25)
    w = (q - g["duty"]) / (1 - g["duty"])
    z = z0 + r - 2 * r * smooth01(w)
    y = 0.9 + g["lift"] * math.sin(math.pi * w) ** 1.15
    tau = tau0 + 4.0 + 26.0 * math.sin(math.pi * w)
    return V((x, y, z)), tau, 16.0 * math.sin(math.pi * min(1.0, w * 1.3))


def gait_key(name, phase):
    """One moment of a gait as a pose."""
    g = GAITS[name]
    a = 2 * math.pi * phase
    feet_spec = {}
    for leg_name in LEGS:
        ball, tau, foot = foot_at(g, leg_name, phase)
        z0 = REST_BALL[leg_name].z
        feet_spec[leg_name] = dict(ball=ball, tau=tau, foot=foot, scap=max(-10.0, min(12.0, -(ball.z - z0) * 2.2)) if leg_name in FRONT else 0.0)
    run = name == "run"
    # the spine's yaw runs from the hips forward in a wave; the head counters it and stays steady
    body = {}
    yaws = []
    for i, bone in enumerate(("Hips", "SpineA", "SpineB", "Chest", "Neck1", "Neck2")):
        yaw = g["yaw"] * math.sin(a - 0.7 * i)
        yaws.append(yaw)
        body[bone] = [0.0, yaw, g["roll"] * math.cos(a - 0.7 * i) * (1.0 if i < 4 else 0.3)]
    body["Neck3"] = [0.0, 0.0, 0.0]
    body["Head"] = [0.0, -sum(yaws) * 0.8, -body["Chest"][2] * 0.6]
    body["Jaw"] = [(-6.0 + 5.0 * math.sin(a * 2)) if run else 0.0, 0, 0]
    # the spine flexes (gallop: one bend a stride, flexed with the feet gathered, extended at full reach)
    F = math.cos(2 * math.pi * (phase - 0.93)) if run else math.cos(4 * math.pi * (phase - 0.1))
    fl = g["flex"]
    for bone, k in (("Hips", 1.0), ("SpineA", 0.5), ("SpineB", -0.5), ("Chest", -1.0)):
        body[bone][0] += fl * F * k
    body["Hips"][0] += g["lean"]
    # the neck and head hold their line against the body's pitch
    for bone, k in (("Neck1", 0.3), ("Neck2", 0.3), ("Neck3", 0.2), ("Head", 0.2)):
        body[bone][0] += -fl * F * 0.2 * k * 2 + (2.0 if run else 0.0) * -1
    if run:
        body["Neck1"][0] += -4.0
        body["Neck2"][0] += -4.0
        body["Head"][0] += 4.0
    bob = g["bob"] * (math.cos(4 * math.pi * (phase - 0.43)) if run else math.cos(4 * math.pi * (phase - 0.0)))
    shift = (bob - (1.3 if run else 0.5), 0.0)
    tail = tail_pose(g["tail"], 4.0 * math.sin(a + 1.0), 0.0, 3.0 * math.sin(a * (1 if run else 2) + 0.5))
    ears = ear_pose(back=(46 if run else 6))
    ruff = ruff_pose(10 if run else 2, 4)
    body = {k: tuple(v) for k, v in body.items()}
    spec = dict(body=join(body, tail, ears, ruff), shift=shift, feet=feet_spec, stream=dict(lean=((0.9, 1.6) if run else (0.5, 0.9)), flare=0.0, droop=0.0))
    return build_pose(spec)


# ---------------------------------------------------------------- tables for the game
def continuous(e, ref):
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
        pose, shift, _ = build_pose(k)
        sp[name] = (pose, shift)
    return sp


def bake_move(keys, fps=30):
    """Dense frames of a move: ([{joint: values}], [{leg: planted}])."""
    base = {n: (0, 0, 0) for n in JOINTS}
    frames, plants, prev = [], [], None
    length = keys[-1]["t"]
    for f in range(int(round(length * fps)) + 1):
        pose, shift, pl = sample(keys, min(f / fps, length))
        ref = prev or full(*state_tables()["Guardian"], base)
        v = full(pose, shift, {n: ref[n][:3] for n in JOINTS})
        frames.append(v)
        plants.append(pl)
        prev = v
    return frames, plants


def bake_gait(name, steps=STEPS):
    guardian = full(*state_tables()["Guardian"], {n: (0, 0, 0) for n in JOINTS})
    frames, prev = [], guardian
    for i in range(steps):
        pose, shift, _ = gait_key(name, i / steps)
        v = full(pose, shift, {n: prev[n][:3] for n in JOINTS})
        frames.append({n: [v[n][k] - guardian[n][k] for k in range(len(v[n]))] for n in JOINTS})
        prev = v
    return frames


def reduce_track(rows, tol):
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
    """Where things truly are, for the effects (the guardian's own axes, feet on y = 0)."""
    out = {}
    mv = moves()

    def at(name, t, bone, end=True):
        pose, shift, _ = sample(mv[name], t)
        st = fk(pose, shift)
        p = tip(st, bone) if end else st[bone][1]
        return [round(p.x, 1), round(p.y, 1), round(p.z, 1)]

    out["BiteMouth"] = at("Bite", 0.50, "Head")
    out["BiteGround"] = [0.0, 0.6, round(at("Bite", 0.50, "Head")[2] * 0.85, 1)]
    out["HowlMouth"] = at("EclipseHowl", 1.0, "Head")
    out["HowlCrown"] = at("EclipseHowl", 1.0, "EclipseRing", end=False)
    out["Eclipse"] = [round(c, 1) for c in ECLIPSE]
    out["LeapFeet"] = [0.0, 0.6, round(at("MoonLeap", 0.55, "Hips", end=False)[2] + 1.0, 1)]
    out["LandFeet"] = [0.0, 0.6, at("Land", 0.0, "FrontLeftToes")[2]]
    out["Mouth"] = at("Enrage", 0.45, "Head")
    out["Crown"] = at("Awaken", 2.3, "Head", end=False)
    out["Chest"] = [0.0, 6.0, -6.0]
    out["TailTip"] = [0.0, round(BONES["Tail6"][2][1], 1), round(BONES["Tail6"][2][2], 1)]
    return out


def write_clips(path, fps=30):
    """src/client/Guardians/GuardianRigs/TiangouV3Clips.lua, generated: the poses, the gaits and the moves as data the rig plays."""
    sts = state_tables()
    base = {n: (0, 0, 0) for n in JOINTS}
    guardian = full(*sts["Guardian"], base)
    lines = ["-- Written by tools/blender/guardians/tiangou_v3.py (tiangou_v3_motion.write_clips): do not edit by hand. Angles in degrees,",
             "-- [pitch, yaw, roll]; the hips also carry [lift, slide] in studs. Poses are whole poses (every joint); Gaits are changes from how it",
             "-- stands (%d frames a cycle, with each leg's touchdown Phase and stance Duty); Moves are tracks of [frame, values...] at Fps, only for the" % STEPS,
             "-- joints the move drives, each held to a tolerance of 0.2 degrees (0.03 studs); Plants lists the frames each leg is off the ground.", "local Clips = {}", "Clips.Fps = %d" % fps,
             "Clips.Steps = %d" % STEPS, "Clips.Joints = " + _lua(JOINTS), "Clips.Anchors = " + _lua(anchors()),
             "Clips.Strides = " + _lua({n: stride_of(g) for n, g in GAITS.items()}), "Clips.Duty = " + _lua({n: g["duty"] for n, g in GAITS.items()}),
             "Clips.Phase = " + _lua({n: g["phase"] for n, g in GAITS.items()}), "Clips.Speed = " + _lua({n: g["speed"] for n, g in GAITS.items()})]
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
        for leg_name in LEGS:
            spans, start = [], None
            for f, pl in enumerate(plants):
                if not pl[leg_name] and start is None:
                    start = f
                if pl[leg_name] and start is not None:
                    spans.append([start, f - 1])
                    start = None
            if start is not None:
                spans.append([start, len(plants) - 1])
            free[leg_name] = spans
        lines.append("%s={Length=%s,Tracks=%s,Plants=%s}," % (name, _lua(keys[-1]["t"]), _lua(tracks), _lua(free)))
    lines.append("}")
    lines.append("return Clips")
    with open(path, "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")
    import os as _os
    return {"bytes": _os.path.getsize(path), "worst reduction error (x tolerance)": {k: round(v, 2) for k, v in worst.items()}, "anchors": anchors()}
