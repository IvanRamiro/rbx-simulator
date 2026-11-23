"""The Cinder Roc's skeleton: bone: (parent, head, tail) in Roblox studs (x right, y up, the bird facing -Z, left is -X), and the
numbers the feathers hang on (no Blender here, so the motion code can share it). 78 bones: the spine, the S of the neck, the head and
its jaw, a crest of three plumes, a tail of five ribbons, two legs of thigh, shin, tarsus, foot, toes and hallux with a feathered
trouser each, and two wings of clavicle, upper arm, forearm and hand with five primary and two secondary chains each."""
import math

from mathutils import Vector

V = Vector

BONES = {}


def _add(name, parent, head, tail):
    BONES[name] = (parent, tuple(round(c, 4) for c in head), tuple(round(c, 4) for c in tail))


_add("Root", None, (0, 0, 0), (0, 0, -3))
_add("Hips", "Root", (0, 12.1, 2.6), (0, 13.0, -0.6))
_add("Spine", "Hips", (0, 13.0, -0.6), (0, 14.1, -3.6))
_add("Chest", "Spine", (0, 14.1, -3.6), (0, 15.1, -6.3))
_add("Neck1", "Chest", (0, 14.9, -5.5), (0, 16.7, -7.8))
_add("Neck2", "Neck1", (0, 16.7, -7.8), (0, 18.7, -7.8))
_add("Neck3", "Neck2", (0, 18.7, -7.8), (0, 19.7, -8.6))
_add("Head", "Neck3", (0, 19.7, -8.6), (0, 18.4, -14.6))
_add("Jaw", "Head", (0, 19.3, -9.9), (0, 18.3, -13.2))
_add("Eyes", "Head", (0, 20.2, -10.6), (0, 20.2, -11.6))        # both eyes: slid into their sockets to blink and to glare
# the crest: a long centre plume and a pair either side, swept back like flame
_add("CrestA", "Head", (0, 20.9, -9.0), (0, 21.9, -6.4))
_add("CrestB", "CrestA", (0, 21.9, -6.4), (0, 21.5, -2.6))
# the tail: a root on the rump and five ribbons that fan from it, drooping under their own weight
_add("TailBase", "Hips", (0, 12.4, 2.6), (0, 12.0, 5.6))


def _ribbon_bones(prefix, parent, root, yaw, length, count, drop=0.02, spread=0.0):
    """A chain of `count` bones along a drooping curve from `root`, `yaw` degrees out from straight back."""
    s, c = math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
    pts = []
    for k in range(count + 1):
        u = length * k / count
        pts.append((root[0] + spread + s * u, root[1] - drop * u * u, root[2] + c * u))
    names = []
    for k in range(count):
        n = prefix + "ABC"[k]
        _add(n, parent if k == 0 else names[-1], pts[k], pts[k + 1])
        names.append(n)
    return names


_ribbon_bones("Tail0", "TailBase", (0, 12.0, 5.6), 0, 18.5, 3)
for _sign, _tag in ((-1, "Left"), (1, "Right")):
    _ribbon_bones(_tag + "Tail1", "TailBase", (0, 12.0, 5.6), _sign * 11, 16.0, 2, spread=_sign * 0.4)
    _ribbon_bones(_tag + "Tail2", "TailBase", (0, 12.0, 5.6), _sign * 23, 13.5, 2, spread=_sign * 0.8)

PRIM_ANGLES = (12, 29, 46, 63, 80)          # degrees each primary group fans from the hand toward the trailing edge
PRIM_ROOTS = (4.2, 3.2, 2.2, 1.2, 0.2)      # studs from the wrist along the hand to where each group's root sits
PRIM_LENGTHS = (7.4, 9.4, 9.2, 8.2, 7.0)
SEC_ROOTS = (0.78, 0.22)                    # outer and inner secondaries: the share along the forearm from the elbow
SEC_LENGTHS = (7.0, 7.4)


def _unit(v):
    return V(v).normalized()


def wing_frame(sign):
    """The right wing's arm points (shoulder, elbow, wrist, hand tip) and the trailing direction at each segment; mirrored by `sign`."""
    p = [V((1.4, 14.5, -4.8)), V((3.6, 14.9, -4.5)), V((8.8, 15.2, -3.1)), V((15.3, 15.4, -5.1)), V((19.5, 15.5, -3.4))]
    return [V((q.x * sign, q.y, q.z)) for q in p]


def _trail(d):
    """Where the trailing edge points for a segment lying along d: straight back, square to the segment."""
    back = V((0, 0, 1))
    return (back - d * back.dot(d)).normalized()


def _side(sign, tag):
    pts = wing_frame(sign)
    b = {}
    b["Clavicle"] = ("Chest", pts[0], pts[1])
    b["UpperArm"] = ("Clavicle", pts[1], pts[2])
    b["Forearm"] = ("UpperArm", pts[2], pts[3])
    b["Hand"] = ("Forearm", pts[3], pts[4])
    hd = _unit(pts[4] - pts[3])
    tr = _trail(hd)
    for g in range(5):
        a = math.radians(PRIM_ANGLES[g])
        d = hd * math.cos(a) + tr * math.sin(a)
        root = pts[3] + hd * PRIM_ROOTS[g]
        b["Prim%dA" % (g + 1)] = ("Hand", root, root + d * PRIM_LENGTHS[g] * 0.5)
        b["Prim%dB" % (g + 1)] = ("Prim%dA" % (g + 1), root + d * PRIM_LENGTHS[g] * 0.5, root + d * PRIM_LENGTHS[g])
    fd = _unit(pts[3] - pts[2])
    ftr = _trail(fd)
    for g in range(2):
        root = pts[2].lerp(pts[3], SEC_ROOTS[g])
        d = (ftr * math.cos(math.radians(10)) - fd * math.sin(math.radians(10))).normalized()
        b["Sec%dA" % (g + 1)] = ("Forearm", root, root + d * SEC_LENGTHS[g] * 0.5)
        b["Sec%dB" % (g + 1)] = ("Sec%dA" % (g + 1), root + d * SEC_LENGTHS[g] * 0.5, root + d * SEC_LENGTHS[g])
    x = lambda v: v * sign
    b["Thigh"] = ("Hips", (x(3.4), 11.5, 0.8), (x(3.4), 8.4, -2.4))
    b["Shin"] = ("Thigh", (x(3.4), 8.4, -2.4), (x(3.4), 3.8, 1.0))
    b["Tarsus"] = ("Shin", (x(3.4), 3.8, 1.0), (x(3.4), 1.0, -1.9))
    b["Foot"] = ("Tarsus", (x(3.4), 1.0, -1.9), (x(3.4), 0.7, -4.4))
    b["Toes"] = ("Foot", (x(3.4), 0.7, -4.4), (x(3.4), 0.45, -6.0))
    b["Hallux"] = ("Foot", (x(3.4), 1.0, -1.9), (x(3.4), 0.6, 0.1))
    b["Trouser"] = ("Thigh", (x(3.2), 11.1, 1.2), (x(3.5), 6.4, 2.0))
    for plume, (ya, yb) in (("Crest", ((x(0.8), 20.5, -8.8), (x(1.6), 21.2, -4.8))),):
        b[plume + "A"] = ("Head", ya, yb)
        b[plume + "B"] = (plume + "A", yb, (x(2.1), 21.0, -1.6))
    return {tag + n: (((tag + p) if (p in b and p != "Chest" and p != "Head" and p != "Hips") else p), h, t) for n, (p, h, t) in b.items()}


for _sign, _tag in ((-1, "Left"), (1, "Right")):
    BONES.update(_side(_sign, _tag))
# the legs hang from Hips, the wings from Chest, the plumes from Head: fix the parents the prefix rule above turned into "<tag>Hips"
for _n, (_p, _h, _t) in list(BONES.items()):
    if _p in ("LeftHips", "RightHips", "LeftChest", "RightChest", "LeftHead", "RightHead"):
        BONES[_n] = (_p.replace("Left", "").replace("Right", ""), _h, _t)

LEG_BONES = ("Thigh", "Shin", "Tarsus", "Foot", "Toes", "Hallux", "Trouser")


def joints():
    """The bones the game poses: every bone but the root and the eyes' (posed by hand)."""
    return [n for n in BONES if n not in ("Root", "Eyes")]


