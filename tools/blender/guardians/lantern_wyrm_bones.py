"""The Abyssal Lantern Wyrm's skeleton: bone: (parent, head, tail) in Roblox studs (x right, y up, the wyrm facing -Z, left is -X), and the
numbers its body is built on (no Blender here, so the motion code shares them).

Bound in a straight line along Z, its belly on the ground (the spine at y = 2.6): Hips at the origin, a neck of eight bones (2.75 studs each)
running forward to the Head, a trunk of eleven (2.0) and a tail of eleven (2.0 to 2.3, ending in a fin) running back. Every pose is a
curve the spine is laid along (lantern_wyrm_motion.py solves the bone turns that put the joints on it), so the bind is the plainest
possible: straight, symmetric about the long axis, every bone either along -Z or +Z.

Bones (72): Root; Hips; Neck1..8; Head, Jaw, Eyes; Lure1..3 (the stalk; the lamp rides Lure3); per side: BarbelA1..4 (the long
whisker-barbel from the muzzle), BarbelB1..3 (the short beard), Frill1..10 (the ribs of the mane-frill along the neck and the first third
of the back); Body1..11 (the trunk) and Tail1..11 (the tail, the fin on the last three).
"""
import math

BONES = {}
Y0 = 2.6                      # the spine's height: the belly of the thickest part rests on the ground
NECK_N, BODY_N, TAIL_N = 8, 11, 11
NECK_LEN = [2.75] * NECK_N
BODY_LEN = [2.0] * BODY_N
TAIL_LEN = [2.3, 2.3, 2.2, 2.2, 2.1, 2.1, 2.0, 2.0, 1.9, 1.9, 2.0]
NECK_TOP = -sum(NECK_LEN)                   # z of the neck's top, where the Head begins (-22)
TRUNK_END = sum(BODY_LEN)                   # z where the trunk ends (22)
TAIL_END = TRUNK_END + sum(TAIL_LEN)        # z of the tail's tip (45)
HEAD_LEN = 9.0
LENGTH = HEAD_LEN - NECK_TOP + TAIL_END     # snout to tail tip: 76


def _add(name, parent, head, tail):
    BONES[name] = (parent, tuple(round(c, 4) for c in head), tuple(round(c, 4) for c in tail))


_add("Root", None, (0, 0, 0), (0, 0, -3))
_add("Hips", "Root", (0, Y0, 0), (0, Y0 + 1.0, 0))

NECK, BODY, TAIL = [], [], []
z = 0.0
prev = "Hips"
for k in range(NECK_N):
    n = "Neck%d" % (k + 1)
    _add(n, prev, (0, Y0, z), (0, Y0, z - NECK_LEN[k]))
    z -= NECK_LEN[k]
    prev = n
    NECK.append(n)
HEAD_BASE = z
_add("Head", prev, (0, Y0, z), (0, Y0, z - HEAD_LEN))
_add("Jaw", "Head", (0, Y0 - 0.6, z - 2.3), (0, Y0 - 0.9, z - 8.4))
_add("Eyes", "Head", (0, Y0 + 0.4, z - 3.5), (0, Y0 + 0.4, z - 4.5))
# the lantern's stalk: up from the brow's eminence, over, and down before the face; the lamp rides the last bone
_add("Lure1", "Head", (0, Y0 + 1.4, z - 3.0), (0, Y0 + 4.0, z - 3.4))
_add("Lure2", "Lure1", (0, Y0 + 4.0, z - 3.4), (0, Y0 + 5.6, z - 5.6))
_add("Lure3", "Lure2", (0, Y0 + 5.6, z - 5.6), (0, Y0 + 5.0, z - 9.4))
LAMP = (0.0, Y0 + 4.7, z - 10.2)            # the lamp's centre, just before the end of the last bone

z = 0.0
prev = "Hips"
for k in range(BODY_N):
    n = "Body%d" % (k + 1)
    _add(n, prev, (0, Y0, z), (0, Y0, z + BODY_LEN[k]))
    z += BODY_LEN[k]
    prev = n
    BODY.append(n)
for k in range(TAIL_N):
    n = "Tail%d" % (k + 1)
    _add(n, prev, (0, Y0, z), (0, Y0, z + TAIL_LEN[k]))
    z += TAIL_LEN[k]
    prev = n
    TAIL.append(n)
SPINE_BACK = BODY + TAIL                    # the chain behind the hips, root to tip
SPINE = NECK + ["Head"]


def radius_at(u):
    """The body's radius at distance u along the bind axis (u < 0 toward the head, u > 0 toward the tail): a neck of 1.7 that thickens into a
    girth of 2.7 at the shoulders and the belly, holds it, and tapers over the last third (from u = 15) to a fine tail."""
    if u <= NECK_TOP:
        return 1.7
    if u < 0:
        t = u / NECK_TOP                               # 0 at the hips, 1 at the head
        return 2.55 - 0.85 * (t ** 1.1)
    if u < 8:
        return 2.55 + 0.15 * math.sin(math.pi * 0.5 * u / 8)
    if u < 15:
        return 2.7
    t = min(1.0, (u - 15) / (TAIL_END - 15))
    return max(0.1, 2.7 * (1 - t ** 1.25) ** 0.8)


def bone_span(name):
    p, h, t = BONES[name]
    return h[2], t[2]


# the mane-frill: ten ribs a side, the largest behind the head, running from the neck's top to the first third of the back
FRILL_N = 10
FRILL_Z = [NECK_TOP + 1.0 + 2.9 * k for k in range(FRILL_N)]
FRILL_LEN = [7.2, 8.0, 8.4, 8.2, 7.6, 6.8, 5.8, 4.8, 3.8, 2.8]
FRILL_ANGLE = 38.0                          # where each rib roots: this many degrees off the top, round the body
FRILL_DIR = (0.62, 0.76)                    # open: out and up (the right side's; the left mirrors it); the ribs also fan: see frill_dir
FRILL_TILT = (-0.35, 0.60)                  # the first rib (behind the head) leans forward, the last (on the back) leans back: a fan


def _carrier(z):
    """The spine bone whose span holds z."""
    for n in SPINE_BACK + NECK:
        a, b = bone_span(n)
        lo, hi = min(a, b), max(a, b)
        if lo - 1e-6 <= z <= hi + 1e-6:
            return n
    return "Neck%d" % NECK_N


def frill_root(k, sign):
    z = FRILL_Z[k]
    r = radius_at(z) * 0.93
    a = math.radians(FRILL_ANGLE)
    return (sign * r * math.sin(a), Y0 + r * math.cos(a), z)


for _sign, _tag in ((-1, "Left"), (1, "Right")):
    for _k in range(FRILL_N):
        _root = frill_root(_k, _sign)
        _d = (_sign * FRILL_DIR[0], FRILL_DIR[1], FRILL_TILT[0] + (FRILL_TILT[1] - FRILL_TILT[0]) * _k / (FRILL_N - 1))
        _l = math.sqrt(sum(c * c for c in _d))
        _add("%sFrill%d" % (_tag, _k + 1), _carrier(FRILL_Z[_k]), _root, tuple(_root[i] + _d[i] / _l * FRILL_LEN[_k] for i in range(3)))
    # the barbels: the long whisker from the muzzle's corner trailing back and out, the short beard from the chin
    _add(_tag + "BarbelA1", "Head", (_sign * 0.55, Y0 + 0.05, HEAD_BASE - 7.0), (_sign * 1.7, Y0 + 0.28, HEAD_BASE - 6.3))
    for _k in range(1, 4):
        _p = BONES[_tag + "BarbelA%d" % _k][2]
        _add(_tag + "BarbelA%d" % (_k + 1), _tag + "BarbelA%d" % _k, _p, (_p[0] + _sign * 0.9, _p[1] + 0.12, _p[2] + 2.5))
    _add(_tag + "BarbelB1", "Head", (_sign * 0.55, Y0 - 0.9, HEAD_BASE - 7.4), (_sign * 0.75, Y0 - 1.4, HEAD_BASE - 6.0))
    for _k in range(1, 3):
        _p = BONES[_tag + "BarbelB%d" % _k][2]
        _add(_tag + "BarbelB%d" % (_k + 1), _tag + "BarbelB%d" % _k, _p, (_p[0] + _sign * 0.2, _p[1] - 0.45, _p[2] + 1.4))

FRILL = {tag: ["%sFrill%d" % (tag, k + 1) for k in range(FRILL_N)] for tag in ("Left", "Right")}
BARBELS = {tag: ["%sBarbelA%d" % (tag, k) for k in range(1, 5)] + ["%sBarbelB%d" % (tag, k) for k in range(1, 4)] for tag in ("Left", "Right")}
LURE = ["Lure1", "Lure2", "Lure3"]


def joints():
    """The bones the game poses: every bone but the root and the eyes' (posed by hand)."""
    return [n for n in BONES if n not in ("Root", "Eyes")]


def checks():
    """Plain facts about the table: counts, the length, the mirror error."""
    err = 0.0
    for n, (p, h, t) in BONES.items():
        if n.startswith("Left"):
            q = BONES["Right" + n[4:]]
            for a, b in ((h, q[1]), (t, q[2])):
                err = max(err, math.dist((a[0], a[1], a[2]), (-b[0], b[1], b[2])))
    return {"bones": len(BONES), "spine bones (neck, head, trunk, tail)": len(NECK) + 1 + len(BODY) + len(TAIL), "length (studs)": round(LENGTH, 2),
            "tail tip z": round(TAIL_END, 2), "mirror error": round(err, 6)}


if __name__ == "__main__":
    print(checks())
