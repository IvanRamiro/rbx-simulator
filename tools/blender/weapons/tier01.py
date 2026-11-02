"""Qi Awakening's weapons (run inside Blender): the first realm's, sold from the start. Their Qi is
the realm's: a faint, pale azure.

- Sword1, the Reedwhisper Sword: a sword grown from a river reed. Its blade is one long reed leaf of
  celadon steel, curving like a leaf in the wind, its parallel veins running down it and a thread
  of Qi along its midrib; at its foot the reed's leaf-sheaths peel away round the grip. The grip is
  a reed flute: Qi glows in its finger holes and in its open end, and the reed's feathery seed
  plume hangs from it.
- Spear1, the Bamboo Thorn Spear: a green bamboo culm, its nodes ringed, cut on the bias into a
  point; Qi glows inside the hollow the cut lays open. At the head's node the shoot's papery
  sheaths peel back, and two curved bamboo thorns flare out as its lugs. Its grip is bound in
  cord, and three bamboo leaves hang from its butt.

    import tier01 as T
    T.build("Sword1")            # the high-detail weapon, to look at
    T.export("Sword1")           # bake and write assets/weapons/Sword1.fbx and its placements
"""
import math
import random

from mathutils import Vector

import weapon_kit as WK

Hm, W = WK.Hm, WK.W
V = Vector
TAU = WK.TAU
GLOW = "3caaff"          # Qi Awakening's pale azure (paler blooms white in Neon)


# ---------- Sword1: the Reedwhisper Sword ----------
BLADE_FOOT, BLADE_TIP = -0.85, -4.35
GRIP_TOP, GRIP_END = -0.62, 1.32
GRIP_R = 0.125
HOLES = (-0.3, 0.0, 0.7, 1.0)


def leaf_blade(t):
    """The reed leaf's half-width, its sideways sway, its thickness and its twist (radians) at t (0
    foot, 1 point)."""
    w = 0.29 * math.sin(math.pi * (0.16 + 0.84 * t)) ** 0.55 * (1 - 0.12 * t)
    return max(0.0, w), 0.3 * t * t, 0.07 * (1 - 0.55 * t) + 0.008, 0.55 * t ** 1.5


def turned(cx, x, y, twist):
    """A point of the leaf's section, the section turned about its midrib by `twist`."""
    return cx + x * math.cos(twist) - y * math.sin(twist), x * math.sin(twist) + y * math.cos(twist)


def reed_blade(hi):
    rings = []
    n, m = 90, 24
    for k in range(n + 1):
        t = k / n
        z = BLADE_FOOT + (BLADE_TIP - BLADE_FOOT) * t
        w, cx, th, tw = leaf_blade(t)
        pts = []
        for i in range(m):
            a = TAU * i / m
            c, s = math.cos(a), math.sin(a)
            rib = 0.4 * th * math.exp(-(c / 0.13) ** 2)    # the raised midrib
            x, y = turned(cx, w * c, math.copysign(th * abs(s) ** 0.85 + rib * abs(s), s), tw)
            pts.append(V((x, y, z)))
        rings.append((V((cx, 0, z)), pts))
    WK.loft(hi, rings, cap_end=False, uv_scale=1.0)


def midrib_glow(hi):
    """A thread of Qi along the midrib, both faces."""
    for side in (1, -1):
        pts = []
        for k in range(31):
            t = 0.04 + 0.68 * k / 30
            z = BLADE_FOOT + (BLADE_TIP - BLADE_FOOT) * t
            _, cx, th, tw = leaf_blade(t)
            x, y = turned(cx, 0.0, side * (th * 1.4 + 0.002), tw)
            pts.append(V((x, y, z)))
        Hm.htube(hi, pts, lambda t: 0.016 * (1 - 0.6 * t), sides=6, per=1, uv_scale=3.0, tip=True, wobble=0.0)


def flute(hi, rim, glow):
    """The grip: a reed flute with a node, finger holes glowing with Qi, cord at both ends, and its
    open end alight."""
    node_t = (0.35 - GRIP_TOP) / (GRIP_END - GRIP_TOP)
    Hm.htube(hi, [V((0, 0, GRIP_TOP)), V((0, 0, 0.35)), V((0, 0, GRIP_END))],
             lambda t: GRIP_R + 0.02 * math.exp(-((t - node_t) / 0.025) ** 2), sides=18, per=40, uv_scale=1.0, tip=False, wobble=0.0)
    Hm.htube(hi, [V((0.16 * math.cos(TAU * i / 32), 0.16 * math.sin(TAU * i / 32), -0.72)) for i in range(33)],
             lambda t: 0.04, sides=8, per=1, uv_scale=2.0, tip=False, wobble=0.0)          # the reed's node under the sheaths
    for z in HOLES:
        ring = [V((0.045 * math.cos(TAU * i / 20), GRIP_R + 0.004, z + 0.045 * math.sin(TAU * i / 20))) for i in range(21)]
        Hm.htube(rim, ring, lambda t: 0.013, sides=6, per=1, uv_scale=3.0, tip=False, wobble=0.0)
        WK.disc(glow, (0, GRIP_R + 0.003, z), (0, 1, 0), 0.036)
    for z0, z1 in ((GRIP_TOP + 0.02, GRIP_TOP + 0.2), (GRIP_END - 0.2, GRIP_END - 0.02)):
        WK.helix(rim, z0, z1, GRIP_R + 0.012, 5, 0.014)
    # the open end: the reed's wall round a hollow full of Qi
    m = 24
    outer = [hi.v(V((GRIP_R * math.cos(TAU * i / m), GRIP_R * math.sin(TAU * i / m), GRIP_END))) for i in range(m)]
    inner = [hi.v(V((0.085 * math.cos(TAU * i / m), 0.085 * math.sin(TAU * i / m), GRIP_END))) for i in range(m)]
    for i in range(m):
        j = (i + 1) % m
        hi.facing([outer[i], outer[j], inner[j], inner[i]], [(0, 0), (1, 0), (1, 1), (0, 1)], (0, 0, 1))
    WK.disc(glow, (0, 0, GRIP_END - 0.01), (0, 0, 1), 0.086)


def sheaths():
    """The reed's leaf-sheaths peeling away round the blade's foot."""
    return [
        dict(base=V((-0.1, 0.0, -0.62)), direction=V((-0.25, 0.0, -1.0)), normal=V((-1.0, 0.2, 0.0)), length=1.05, width=0.16,
             fold=0.2, curl=0.25, twist=0.4, cup=0.3, mat=0, steps=14),
        dict(base=V((0.1, 0.02, -0.55)), direction=V((0.3, 0.1, 1.0)), normal=V((1.0, 0.3, 0.0)), length=0.8, width=0.14,
             fold=0.2, curl=0.35, twist=-0.5, cup=0.3, mat=0, steps=12),
        dict(base=V((0.09, -0.03, -0.7)), direction=V((0.35, 0.0, -1.0)), normal=V((1.0, 0.0, 0.0)), length=0.55, width=0.1,
             fold=0.2, curl=0.4, twist=0.3, cup=0.2, mat=0, steps=10),
    ]


def plume():
    """The reed's seed plume: a soft tassel of feathery strands hanging from the flute's end,
    drooping and gathered, not fanned."""
    rnd = random.Random(7)
    specs = []
    for k in range(28):
        a = TAU * k / 28 + rnd.uniform(-0.1, 0.1)
        spread = rnd.uniform(0.12, 0.3)
        direction = V((spread * math.cos(a), -0.75 + 0.2 * spread * math.sin(a), 0.6)).normalized()
        specs.append(dict(base=V((0.025 * math.cos(a), -0.06 + 0.025 * math.sin(a), GRIP_END + 0.18)), direction=direction,
                          normal=V((math.cos(a), 0.0, math.sin(a))), length=rnd.uniform(0.75, 1.05), width=rnd.uniform(0.045, 0.07),
                          fold=0.35, curl=-0.25, twist=rnd.uniform(-0.8, 0.8), mat=0, steps=12, across=2, shape=0.5))
    return specs


def build_sword1():
    root = W.collection("Sword1Hi")
    W.clear_collection(root)
    blade, reed, rim, glow, stalk = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    reed_blade(blade)
    flute(reed, rim, glow)
    midrib_glow(glow)
    Hm.htube(stalk, [V((0, 0, GRIP_END - 0.05)), V((0, -0.03, GRIP_END + 0.1)), V((0, -0.06, GRIP_END + 0.2))], lambda t: 0.03 * (1 - 0.5 * t),
             sides=8, per=4, uv_scale=3.0, tip=True, wobble=0.0)
    reed_mat = WK.mat_reed()
    hi = [blade.object("RW_Blade", root, [WK.mat_celadon_steel()], smooth=True),
          reed.object("RW_Flute", root, [reed_mat]),
          rim.object("RW_Cord", root, [WK.mat_cord("WpnCordBrown", (0.1, 0.05, 0.02), (0.3, 0.17, 0.07))]),
          stalk.object("RW_Stalk", root, [reed_mat]),
          WK.leaves(root, "RW_Sheaths", [WK.mat_reed("WpnReedSheath", (0.36, 0.34, 0.12), (0.66, 0.62, 0.3))], sheaths(), 0.018),
          WK.leaves(root, "RW_Plume", [WK.mat_plain("WpnPlume", (0.42, 0.34, 0.3), (0.78, 0.7, 0.6), rough=0.85, scale=30.0)], plume(), 0.008)]
    hi[0]["keep"] = True
    return hi, {GLOW: ("Glow", [glow.object("RW_Glow", root, [WK.K.glow_material(GLOW)], smooth=False)])}, root


# ---------- Spear1: the Bamboo Thorn Spear ----------
BUTT, HEAD_FOOT, POINT = 3.45, -3.6, -5.2
NODES = (-2.4, -1.35, 0.75, 1.8, 2.85)
CULM_R = 0.15


def culm_radius(z):
    t = (BUTT - z) / (BUTT - HEAD_FOOT)
    r = CULM_R - 0.015 * t
    for zn in NODES + (HEAD_FOOT,):
        r += 0.02 * math.exp(-((z - zn) / 0.035) ** 2) - 0.006 * math.exp(-((z - zn - 0.14) / 0.08) ** 2)
    return r


def culm(hi):
    Hm.htube(hi, [V((0, 0, BUTT)), V((0, 0, 0)), V((0, 0, HEAD_FOOT))],
             lambda t: culm_radius(BUTT + (HEAD_FOOT - BUTT) * t), sides=16, per=160, uv_scale=0.5, tip=False, wobble=0.0)


def cut_z(a):
    """Where the bias cut crosses the culm's wall at angle a round it: the point is underneath (-Y), so
    the cut, and the Qi in the hollow, face up toward the camera."""
    return -3.75 - 1.45 * ((1 - math.sin(a)) / 2) ** 1.8


def bias_head(hi, cut, glow):
    """The head: the culm's wall from its last node up to the bias cut, the cut face showing the
    wall's thickness, and Qi lighting the hollow inside."""
    m, steps = 32, 30
    r_out = culm_radius(HEAD_FOOT)
    outer, inner = [], []
    for s in range(steps + 1):
        f = s / steps
        ro = r_out * (1 - 0.12 * f)
        ri = ro - 0.03
        o_row, i_row = [], []
        for i in range(m):
            a = TAU * i / m
            z = HEAD_FOOT + f * (cut_z(a) - HEAD_FOOT)
            o_row.append(hi.v(V((ro * math.cos(a), ro * math.sin(a), z))))
            i_row.append(glow.v(V((ri * math.cos(a), ri * math.sin(a), z))))
        outer.append(o_row)
        inner.append(i_row)
    for s in range(steps):
        for i in range(m):
            j = (i + 1) % m
            a = TAU * (i + 0.5) / m
            uv = [(i / m, s / steps), ((i + 1) / m, s / steps), ((i + 1) / m, (s + 1) / steps), (i / m, (s + 1) / steps)]
            hi.facing([outer[s][i], outer[s][j], outer[s + 1][j], outer[s + 1][i]], uv, (math.cos(a), math.sin(a), 0))
            glow.facing([inner[s][i], inner[s][j], inner[s + 1][j], inner[s + 1][i]], uv, (-math.cos(a), -math.sin(a), 0))
    # the cut face: from the outer wall to the inner, along the cut
    for i in range(m):
        j = (i + 1) % m
        a0, a1 = TAU * i / m, TAU * j / m
        ro, ri = r_out * 0.88, r_out * 0.88 - 0.03
        q = [cut.v(V((ro * math.cos(a0), ro * math.sin(a0), cut_z(a0)))), cut.v(V((ro * math.cos(a1), ro * math.sin(a1), cut_z(a1)))),
             cut.v(V((ri * math.cos(a1), ri * math.sin(a1), cut_z(a1)))), cut.v(V((ri * math.cos(a0), ri * math.sin(a0), cut_z(a0))))]
        cut.facing(q, [(0, 0), (1, 0), (1, 1), (0, 1)], (0, 1, -0.7))
    WK.disc(glow, (0, 0, HEAD_FOOT + 0.02), (0, 0, -1), r_out - 0.03)    # the node's wall closing the hollow


def thorns(hi):
    """Two curved thorns flaring from the head's node as lugs, and two small ones behind."""
    for sx in (-1, 1):
        WK.blob(hi, (sx * 0.1, 0, HEAD_FOOT + 0.04), (sx * 0.2, 0, HEAD_FOOT - 0.08), 0.07)
        Hm.htube(hi, [V((sx * 0.12, 0, HEAD_FOOT + 0.02)), V((sx * 0.42, 0.0, HEAD_FOOT - 0.06)), V((sx * 0.72, 0.0, HEAD_FOOT - 0.32)),
                      V((sx * 0.84, 0.0, HEAD_FOOT - 0.66)), V((sx * 0.8, 0.0, HEAD_FOOT - 0.92))],
                 lambda t: 0.095 * (1 - t) ** 0.85 + 0.004, sides=12, per=6, uv_scale=3.0, tip=True, wobble=0.0)
        Hm.htube(hi, [V((sx * 0.1, 0, NODES[0])), V((sx * 0.22, 0.0, NODES[0] + 0.1)), V((sx * 0.28, 0.0, NODES[0] + 0.28))],
                 lambda t: 0.04 * (1 - t) ** 0.9 + 0.003, sides=8, per=5, uv_scale=3.0, tip=True, wobble=0.0)


def head_sheaths():
    specs = []
    for k in range(4):
        a = TAU / 8 + TAU * k / 4
        c, s = math.cos(a), math.sin(a)
        specs.append(dict(base=V((0.13 * c, 0.13 * s, HEAD_FOOT + 0.05)), direction=V((0.22 * c, 0.22 * s, 1.0)), normal=V((c, s, 0.0)),
                          length=0.72, width=0.17, fold=0.05, curl=0.5, twist=0.2 * (1 if k % 2 else -1), cup=0.35, mat=0, steps=14))
    return specs


def butt_leaves():
    specs = []
    for k, (dx, length) in enumerate(((-0.45, 0.62), (0.0, 0.7), (0.45, 0.58))):
        specs.append(dict(base=V((0.0, -0.3, BUTT + 0.36)), direction=V((dx, -1.0, 0.35)), normal=V((0.0, 0.2, 1.0)), length=length,
                          width=0.11, fold=0.25, curl=0.2, twist=0.3 * (k - 1), mat=0, steps=12))
    return specs


def build_spear1():
    root = W.collection("Spear1Hi")
    W.clear_collection(root)
    body, cut, glow, thorn, cord = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    culm(body)
    bias_head(body, cut, glow)
    thorns(thorn)
    WK.disc(cut, (0, 0, BUTT + 0.001), (0, 0, 1), culm_radius(BUTT))
    WK.helix(cord, -0.55, 0.55, CULM_R + 0.012, 14, 0.016)
    WK.helix(cord, HEAD_FOOT + 0.62, HEAD_FOOT + 0.86, CULM_R + 0.008, 5, 0.018)       # the head's binding, behind the sheaths
    WK.helix(cord, BUTT - 0.4, BUTT - 0.12, CULM_R + 0.01, 5, 0.016)
    Hm.htube(cord, [V((0, 0.05, BUTT - 0.25)), V((0, -0.12, BUTT + 0.05)), V((0, -0.28, BUTT + 0.3)), V((0, -0.3, BUTT + 0.38))],
             lambda t: 0.018, sides=6, per=6, uv_scale=6.0, tip=False, wobble=0.0)
    hi = [body.object("BT_Culm", root, [WK.mat_bamboo()]),
          cut.object("BT_Cut", root, [WK.mat_plain("WpnBambooCut", (0.62, 0.56, 0.34), (0.86, 0.8, 0.56), rough=0.6)], smooth=False),
          thorn.object("BT_Thorns", root, [WK.mat_plain("WpnThorn", (0.07, 0.04, 0.02), (0.28, 0.17, 0.08), rough=0.35)]),
          cord.object("BT_Cord", root, [WK.mat_cord("WpnCordRed", (0.18, 0.04, 0.03), (0.45, 0.12, 0.07))]),
          WK.leaves(root, "BT_Sheaths", [WK.mat_sheath()], head_sheaths(), 0.02),
          WK.leaves(root, "BT_Leaves", [Hm.mat_leaf("WpnBambooLeaf")], butt_leaves(), 0.012)]
    return hi, {GLOW: ("Glow", [glow.object("BT_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- both ----------
WEAPONS = {
    "Sword1": dict(kind="Sword", build=build_sword1, hilt=(0.0, 0.0, -0.95), tip=(0.3, 0.0, BLADE_TIP), budget=10000),
    "Spear1": dict(kind="Spear", build=build_spear1, hilt=(0.0, 0.0, HEAD_FOOT), tip=(0.0, -0.12, POINT), budget=10000),
}


def build(weapon_id):
    return WEAPONS[weapon_id]["build"]()


def export(weapon_id):
    spec = WEAPONS[weapon_id]
    hi, glow, root = spec["build"]()
    return WK.export(weapon_id, spec["kind"], "tier01.py", hi, glow, root, spec["hilt"], spec["tip"], budget=spec["budget"])
