"""The Heavenly Dao's weapons (run inside Blender): the tenth realm's, whose aura is celestial
symbols, radiant rings and divine lightning. Their Qi is violet.

- Sword10, the Dao Heart Sword: the blade is split down its ridge into white jade and black jade,
  yin and yang, a line of light where they meet, a dot of each in the other at its foot. Its guard
  is a taiji disc rimmed in gold, the eight trigrams floating round it in light; its grip is bound
  in a white cord and a black, and a pearl of light ringed in gold is its pommel.
- Spear10, the Heaven Pillar Spear: a pillar that holds up heaven. The shaft is white marble, a gold
  cloud coiling up it; under the head a cloud board crosses it, as on a heaven-pillar; the head is
  a four-sided spike of white jade inscribed with glowing glyphs, a radiant ring round its foot.

    import tier10 as T
    T.build("Sword10"); T.export("Sword10")
"""
import math

from mathutils import Vector

import weapon_kit as WK

Hm, W = WK.Hm, WK.W
V = Vector
TAU = WK.TAU
GLOW = "643cff"          # violet, the Divine Realm and above

TRIGRAMS = [(1, 1, 1), (0, 1, 1), (1, 0, 1), (0, 0, 1), (1, 1, 0), (0, 1, 0), (1, 0, 0), (0, 0, 0)]   # lines, inner to outer (1 solid)


def gold():
    return Hm.mat_gold("WpnGold")


def black_jade():
    return WK.mat_plain("WpnBlackJade", (0.015, 0.02, 0.025), (0.07, 0.09, 0.09), rough=0.18, scale=4.0)


# ---------- Sword10: the Dao Heart Sword ----------
FOOT, TIP, TAIJI = -1.0, -4.8, -0.85
R = 0.42


def half_width(t):
    return 0.21 * (1 - 0.2 * t) * math.sqrt(max(0.0, 1 - max(0.0, (t - 0.87) / 0.13) ** 2))


def thickness(t):
    return 0.05 * (1 - 0.5 * t) + 0.008


def yin_yang_blade(white, black, glow):
    """Each half of the blade its own surface, meeting on the ridge."""
    n = 80
    for hi, sx in ((white, 1), (black, -1)):
        rings = []
        for k in range(n + 1):
            t = k / n
            z = FOOT + (TIP - FOOT) * t
            w, th = half_width(t), thickness(t)
            pts = [(0, th * 1.25), (0.45 * w, th * 0.85), (0.8 * w, th * 0.4), (w, 0), (0.8 * w, -th * 0.4), (0.45 * w, -th * 0.85), (0, -th * 1.25)]
            rings.append((V((sx * w / 3, 0, z)), [V((sx * x, y, z)) for x, y in pts]))
        WK.loft(hi, rings, cap_end=False, uv_scale=1.0)
    for side in (1, -1):
        pts = [V((0, side * (thickness(t) * 1.25 + 0.004), FOOT + (TIP - FOOT) * t)) for t in (0.0, 0.25, 0.5, 0.75, 0.95)]
        Hm.htube(glow, pts, lambda t: 0.014 * (1 - 0.6 * t), sides=5, per=8, uv_scale=3.0, tip=True, wobble=0.0)
        t = 0.06
        z = FOOT + (TIP - FOOT) * t
        WK.disc(black, (0.09, side * (thickness(t) * 0.9 + 0.006), z), (0, side, 0), 0.035)
        WK.disc(white, (-0.09, side * (thickness(t) * 0.9 + 0.006), z), (0, side, 0), 0.035)


def taiji(white, black, metal, glow):
    """The taiji disc across the blade, sampled on a polar grid, each cell yin or yang."""
    rings_n, segs = 22, 72
    z0, z1 = TAIJI - 0.035, TAIJI + 0.035

    def yang(x, y):
        if math.hypot(x, y - R / 2) < R / 8:
            return False
        if math.hypot(x, y + R / 2) < R / 8:
            return True
        if math.hypot(x, y + R / 2) < R / 2:
            return False
        return x > 0 or math.hypot(x, y - R / 2) < R / 2

    for i in range(rings_n):
        r0, r1 = R * i / rings_n, R * (i + 1) / rings_n
        for j in range(segs):
            a0, a1 = TAU * j / segs, TAU * (j + 1) / segs
            rm, am = (r0 + r1) / 2, (a0 + a1) / 2
            hi = white if yang(rm * math.cos(am), rm * math.sin(am)) else black
            for z, face in ((z0, -1), (z1, 1)):
                pts = [V((r * math.cos(a), r * math.sin(a), z)) for r, a in ((r0, a0), (r1, a0), (r1, a1), (r0, a1))]
                hi.facing([hi.v(p) for p in pts], [(0, 0), (1, 0), (1, 1), (0, 1)], (0, 0, face))
    WK.ring(metal, (0, 0, TAIJI), (0, 0, 1), R + 0.02, 0.04, n=64)
    # the eight trigrams floating round it
    for k, lines in enumerate(TRIGRAMS):
        a = TAU * k / 8 + TAU / 16
        c, s = math.cos(a), math.sin(a)
        tangent = V((-s, c, 0))
        for li, solid in enumerate(lines):
            centre = V(((R + 0.16 + 0.065 * li) * c, (R + 0.16 + 0.065 * li) * s, TAIJI))
            spans = [(-0.08, 0.08)] if solid else [(-0.08, -0.018), (0.018, 0.08)]
            for u0, u1 in spans:
                Hm.htube(glow, [centre + tangent * u0, centre + tangent * u1], lambda t: 0.016, sides=5, per=1, uv_scale=3.0, tip=False, wobble=0.0)


def dao_hilt(grip, white_cord, black_cord, metal, glow):
    Hm.htube(grip, [V((0, 0, TAIJI + 0.05)), V((0, 0, 0.1)), V((0, 0, 0.8))], lambda t: 0.1, sides=14, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    WK.helix(white_cord, TAIJI + 0.08, 0.76, 0.108, 5, 0.018, hand=1)
    WK.helix(black_cord, TAIJI + 0.08, 0.76, 0.108, 5, 0.018, hand=-1)
    WK.ring(metal, (0, 0, 0.98), (1, 0, 0), 0.15, 0.028)
    WK.ring(metal, (0, 0, 0.98), (0, 1, 0), 0.15, 0.028)
    WK.sphere(glow, (0, 0, 0.98), 0.08)


def build_sword10():
    root = W.collection("Sword10Hi")
    W.clear_collection(root)
    white, black, metal, grip, wcord, bcord, glow = (Hm.Hi() for _ in range(7))
    yin_yang_blade(white, black, glow)
    taiji(white, black, metal, glow)
    dao_hilt(grip, wcord, bcord, metal, glow)
    hi = [white.object("DH_White", root, [WK.mat_white_jade()], smooth=False),
          black.object("DH_Black", root, [black_jade()], smooth=False),
          metal.object("DH_Gold", root, [gold()]),
          grip.object("DH_Grip", root, [WK.mat_plain("WpnLeatherDark", (0.04, 0.03, 0.03), (0.12, 0.09, 0.07), rough=0.7)]),
          wcord.object("DH_CordWhite", root, [WK.mat_cord("WpnCordWhite", (0.6, 0.6, 0.58), (0.92, 0.92, 0.9))]),
          bcord.object("DH_CordBlack", root, [WK.mat_cord("WpnCordBlack", (0.01, 0.01, 0.012), (0.08, 0.08, 0.09))])]
    hi[0]["keep"] = hi[1]["keep"] = True
    return hi, {GLOW: ("Glow", [glow.object("DH_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- Spear10: the Heaven Pillar Spear ----------
BUTT, SOCKET, SPIKE_FOOT, POINT = 3.45, -3.0, -3.55, -6.3


def pillar(marble, metal):
    Hm.htube(marble, [V((0, 0, BUTT)), V((0, 0, 0)), V((0, 0, SOCKET))], lambda t: 0.15, sides=16, per=40, uv_scale=1.0, tip=False, wobble=0.0)
    WK.helix(metal, -2.9, 2.9, 0.165, 3.5, 0.05)       # the gold cloud coiling up it
    for z in (SOCKET, BUTT - 0.1):
        Hm.htube(marble, [V((0, 0, z - 0.06)), V((0, 0, z + 0.06))], lambda t: 0.2, sides=16, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(metal, [V((0, 0, BUTT - 0.04)), V((0, 0, BUTT + 0.2)), V((0, 0, BUTT + 0.4))], lambda t: 0.16 * (1 - t) ** 0.6 + 0.004,
             sides=14, per=6, uv_scale=3.0, tip=True, wobble=0.0)


def cloud_board(marble, metal):
    """The cloud board crossing the pillar under the head (faces toward +-Y): a long cloud, its edge
    scalloped."""
    outline = []
    for k in range(48):
        a = TAU * k / 48
        r = 1 + 0.12 * math.cos(a * 6)
        outline.append((0.95 * r * math.cos(a), -3.25 + 0.3 * r * math.sin(a)))
    WK.flat(marble, outline, 0.0, 0.13)
    edge = [V((x * 1.02, 0, z + (z + 3.25) * 0.02)) for x, z in outline]
    for side in (1, -1):
        Hm.htube(metal, [p + V((0, side * 0.066, 0)) for p in edge + edge[:3]], lambda t: 0.022, sides=6, per=1, uv_scale=3.0, tip=False,
                 wobble=0.0)


def spike(jade, glow):
    surface = WK.blade(jade, SPIKE_FOOT, POINT, lambda t: 0.26 * (1 - t) ** 0.7 + 0.004, lambda t: 0.26 * (1 - t) ** 0.7 + 0.004, n=50, m=4, rib=0.0)
    for side in (1, -1):
        def place(i, u, v, side=side):
            t = 0.08 + 0.14 * i + 0.1 * v
            return surface(t, (u - 0.5) * 0.16 * (1 - t), side, 0.004)
        WK.runes(glow, place, 5, seed=100 + (side > 0), tube=0.016)
    Hm.htube(jade, [V((0, 0, SOCKET)), V((0, 0, -3.28)), V((0, 0, SPIKE_FOOT + 0.02))], lambda t: 0.2 - 0.06 * t, sides=16, per=4, uv_scale=3.0,
             tip=False, wobble=0.0)
    WK.ring(glow, (0, 0, SPIKE_FOOT - 0.05), (0, 0, 1), 0.5, 0.02, n=64, sides=6)
    for k in range(12):   # the radiant ring's rays
        a = TAU * k / 12
        c, s = math.cos(a), math.sin(a)
        Hm.htube(glow, [V((0.55 * c, 0.55 * s, SPIKE_FOOT - 0.05)), V(((0.8 if k % 2 == 0 else 0.68) * c, (0.8 if k % 2 == 0 else 0.68) * s,
                                                                         SPIKE_FOOT - 0.05))], lambda t: 0.02 * (1 - t) + 0.003,
                 sides=5, per=1, uv_scale=3.0, tip=True, wobble=0.0)


def build_spear10():
    root = W.collection("Spear10Hi")
    W.clear_collection(root)
    marble, metal, jade, glow = (Hm.Hi() for _ in range(4))
    pillar(marble, metal)
    cloud_board(marble, metal)
    spike(jade, glow)
    hi = [marble.object("HP_Marble", root, [WK.mat_stone("WpnMarble", (0.68, 0.67, 0.64), (0.92, 0.91, 0.88))]),
          metal.object("HP_Gold", root, [gold()]),
          jade.object("HP_Jade", root, [WK.mat_white_jade()], smooth=False)]
    return hi, {GLOW: ("Glow", [glow.object("HP_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- both ----------
WEAPONS = {
    "Sword10": dict(kind="Sword", build=build_sword10, hilt=(0.0, 0.0, FOOT), tip=(0.0, 0.0, TIP), budget=10000),
    "Spear10": dict(kind="Spear", build=build_spear10, hilt=(0.0, 0.0, SPIKE_FOOT), tip=(0.0, 0.0, POINT), budget=9000),
}


def build(weapon_id):
    return WEAPONS[weapon_id]["build"]()


def export(weapon_id):
    spec = WEAPONS[weapon_id]
    hi, glow, root = spec["build"]()
    return WK.export(weapon_id, spec["kind"], "tier10.py", hi, glow, root, spec["hilt"], spec["tip"], budget=spec["budget"])
