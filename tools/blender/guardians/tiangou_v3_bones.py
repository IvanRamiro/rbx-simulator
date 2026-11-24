"""Tiangou the Moon-Eater, rebuilt (v3): the skeleton table. bone: (parent, head, tail) in Roblox studs (x right, y up, the hound facing -Z,
the ground at y = 0, left is -X). No Blender in here, so the motion code and the checks can share it.

70 bones: Root; the spine (Hips, SpineA, SpineB, Chest); a neck of three; the head with its jaw and eyes; two ears of two; a tail of six; the
eclipse (a stalk of two bones to a floating ring, and eight streamers of two bones round it); a ruff of fire (a centre mane, a collar each
side, a chest tuft); four legs (front: scapula, upper arm, forearm, pastern, toes; back: thigh, shin, metatarsus, toes) each with a feather of
fire that hangs from it. The bind is the awake stand, bound straight and mirror-symmetric about x = 0.
"""
import math

BONES = {}


def _add(name, parent, head, tail):
    BONES[name] = (parent, tuple(round(c, 4) for c in head), tuple(round(c, 4) for c in tail))


# ---- the spine and neck: a strong back, a neck raised and carried forward, a head about 8 long
_add("Root", None, (0, 0, 0), (0, 0, -3))
_add("Hips", "Root", (0, 12.0, 5.6), (0, 12.4, 2.2))
_add("SpineA", "Hips", (0, 12.4, 2.2), (0, 12.6, -0.9))
_add("SpineB", "SpineA", (0, 12.6, -0.9), (0, 12.7, -3.8))
_add("Chest", "SpineB", (0, 12.7, -3.8), (0, 12.6, -7.0))
_add("Neck1", "Chest", (0, 12.9, -7.2), (0, 14.3, -9.1))
_add("Neck2", "Neck1", (0, 14.3, -9.1), (0, 15.5, -11.6))
_add("Neck3", "Neck2", (0, 15.5, -11.6), (0, 16.5, -14.0))
_add("Head", "Neck3", (0, 16.5, -14.0), (0, 15.0, -21.5))
_add("Jaw", "Head", (0, 15.5, -16.4), (0, 13.9, -21.0))
_add("Eyes", "Head", (0, 17.1, -17.4), (0, 17.1, -18.4))

# ---- ears: tall and pointed, a root and a tip each
for _s, _t in ((-1, "Left"), (1, "Right")):
    _add(_t + "EarA", "Head", (_s * 1.35, 18.0, -15.0), (_s * 1.8, 20.1, -15.4))
    _add(_t + "EarB", _t + "EarA", (_s * 1.8, 20.1, -15.4), (_s * 2.55, 21.6, -16.7))

# ---- the tail: a root on the croup and six bones that droop and sweep back
_tail = [(0, 12.4, 7.4), (0, 12.0, 9.8), (0, 11.3, 12.2), (0, 10.4, 14.5), (0, 9.4, 16.6), (0, 8.2, 18.4), (0, 6.9, 20.0)]
for _i in range(6):
    _add("Tail%d" % (_i + 1), "Hips" if _i == 0 else "Tail%d" % _i, _tail[_i], _tail[_i + 1])

# ---- the eclipse: a stalk of fire rising behind the shoulders to a ring that floats upright (its face toward -Z), and eight streamers
ECLIPSE = (0.0, 22.2, -1.9)
ECLIPSE_R = 6.3
_add("Stalk1", "Chest", (0, 13.4, -5.6), (0, 15.6, -4.0))
_add("Stalk2", "Stalk1", (0, 15.6, -4.0), (0, 17.9, -2.6))
_add("EclipseRing", "Stalk2", (ECLIPSE[0], ECLIPSE[1], ECLIPSE[2]), (ECLIPSE[0], ECLIPSE[1], ECLIPSE[2] + 1.0))
STREAMS = 8


def stream_dir(i):
    """Streamer i's outward direction in the ring's plane (0 straight up, going round to the viewer's left and back to the right), swept a little back."""
    a = 2 * math.pi * i / STREAMS + math.pi / STREAMS * 0.0
    return (math.sin(a), math.cos(a))


for _i in range(STREAMS):
    _dx, _dy = stream_dir(_i)
    _root = (ECLIPSE[0] + _dx * ECLIPSE_R, ECLIPSE[1] + _dy * ECLIPSE_R, ECLIPSE[2])
    _mid = (_root[0] + _dx * 4.6, _root[1] + _dy * 4.6, _root[2] + 0.8)
    _end = (_root[0] + _dx * 9.4, _root[1] + _dy * 9.4, _root[2] + 1.6)
    _add("Stream%dA" % (_i + 1), "EclipseRing", _root, _mid)
    _add("Stream%dB" % (_i + 1), "Stream%dA" % (_i + 1), _mid, _end)

# ---- the ruff: a mane down the neck's top, a collar of fire behind each cheek, a tuft on the chest
_add("RuffTopA", "Neck1", (0, 14.7, -8.4), (0, 15.6, -6.1))
_add("RuffTopB", "RuffTopA", (0, 15.8, -6.1), (0, 15.6, -3.2))
for _s, _t in ((-1, "Left"), (1, "Right")):
    _add(_t + "Ruff1", "Neck2", (_s * 1.6, 15.5, -12.0), (_s * 3.0, 14.4, -10.2))
    _add(_t + "Ruff2", _t + "Ruff1", (_s * 3.0, 14.9, -10.2), (_s * 3.6, 12.6, -8.4))
_add("ChestTuftA", "Chest", (0, 10.4, -10.2), (0, 8.4, -11.2))
_add("ChestTuftB", "ChestTuftA", (0, 8.4, -11.2), (0, 6.0, -10.8))

# ---- the legs: the front ones a shoulder blade, an upper arm that runs down and back, a forearm that runs down and forward, a pastern and toes;
# the back ones a thigh that runs down and forward, a shin that runs down and back to the hock, a metatarsus and toes.
for _s, _t in ((-1, "Left"), (1, "Right")):
    _x = _s * 2.6
    _add("Front%sScapula" % _t, "Chest", (_x, 13.0, -6.6), (_x, 10.4, -9.4))
    _add("Front%sUpper" % _t, "Front%sScapula" % _t, (_x, 10.4, -9.4), (_x, 7.0, -7.0))
    _add("Front%sLower" % _t, "Front%sUpper" % _t, (_x, 7.0, -7.0), (_x, 2.5, -8.2))
    _add("Front%sPaw" % _t, "Front%sLower" % _t, (_x, 2.5, -8.2), (_x, 0.9, -9.4))
    _add("Front%sToes" % _t, "Front%sPaw" % _t, (_x, 0.9, -9.4), (_x, 0.35, -11.7))
    _add("Front%sFeather" % _t, "Front%sLower" % _t, (_x, 6.6, -6.9), (_x, 3.4, -6.4))
    _x = _s * 2.55
    _add("Back%sThigh" % _t, "Hips", (_x, 11.6, 4.6), (_x, 7.2, 2.2))
    _add("Back%sShin" % _t, "Back%sThigh" % _t, (_x, 7.2, 2.2), (_x, 3.6, 5.6))
    _add("Back%sMeta" % _t, "Back%sShin" % _t, (_x, 3.6, 5.6), (_x, 0.9, 4.9))
    _add("Back%sToes" % _t, "Back%sMeta" % _t, (_x, 0.9, 4.9), (_x, 0.35, 2.6))
    _add("Back%sFeather" % _t, "Back%sThigh" % _t, (_x + _s * 0.4, 8.6, 4.8), (_x + _s * 0.4, 4.6, 7.0))

NECK = ["Neck1", "Neck2", "Neck3"]
SPINE = ["Hips", "SpineA", "SpineB", "Chest"]
TAIL = ["Tail%d" % i for i in range(1, 7)]
LEGS = {
    "FrontLeft": ("Scapula", "Upper", "Lower", "Paw", "Toes"), "FrontRight": ("Scapula", "Upper", "Lower", "Paw", "Toes"),
    "BackLeft": ("Thigh", "Shin", "Meta", "Toes"), "BackRight": ("Thigh", "Shin", "Meta", "Toes"),
}


def leg_names(leg):
    return [leg + p for p in LEGS[leg]]


def joints():
    """The bones the game poses: every bone but the root and the eyes (those are set by hand)."""
    return [n for n in BONES if n not in ("Root", "Eyes")]


def children_of():
    out = {}
    for n, (p, h, t) in BONES.items():
        out.setdefault(p, []).append(n)
    return out


def checks():
    """Symmetry of the bind about x = 0 (left is -X), every bone's head on its parent's tail or inside it, and the length of each chain."""
    worst = 0.0
    for n, (p, h, t) in BONES.items():
        for tag_a, tag_b in (("Left", "Right"), ("Front%s" % "Left", "Front%s" % "Right"), ("Back%s" % "Left", "Back%s" % "Right")):
            if tag_a in n:
                m = n.replace(tag_a, tag_b)
                ph, pt = BONES[m][1], BONES[m][2]
                worst = max(worst, abs(h[0] + ph[0]), abs(h[1] - ph[1]), abs(h[2] - ph[2]), abs(t[0] + pt[0]), abs(t[1] - pt[1]), abs(t[2] - pt[2]))
                break
    count = len(BONES)
    return {"bones": count, "mirror error (studs)": round(worst, 5)}
