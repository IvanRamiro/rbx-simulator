"""Qi Foundation's weapons (run inside Blender): the second realm's. Its Qi is a bright azure.

- Sword2, the Jadevein Sword: a blade split from foundation rock along a vein of jade. Its back is
  dark slate, cleaved rough and chipped; its cutting edge is the jade vein itself, celadon, its
  very edge alight with Qi, and finer veins of light branch from it across the stone. Its guard is
  a dressed cornerstone banded in bronze, a jade cabochon set in each face; its grip is bound in
  blue cord, and a second, smaller cornerstone, turned on its point, is its pommel.
- Spear2, the Jade Crane Spear: its head is a crane striking. The bronze beak is the point; the
  head is white jade under a red crown, its eyes alight; the neck, black jade, curves down into
  the bronze socket, and the crane's wings, half spread, sweep out and back as the lugs, their
  primaries black, two quills on each alight. The shaft is dark teal lacquer bound in blue cord, and
  the butt is a bronze crane's foot.

    import tier02 as T
    T.build("Sword2"); T.export("Sword2")
"""
import math
import random

from mathutils import Vector

import weapon_kit as WK

Hm, W = WK.Hm, WK.W
V = Vector
TAU = WK.TAU
GLOW = "288cff"          # Qi Foundation's bright azure (GameConfig.SwordFlight.RealmGlow)


# ---------- Sword2: the Jadevein Sword ----------
FOOT, TIP = -0.95, -4.45
EDGE, VEIN = 0.3, 0.11   # the cutting edge and where the jade meets the stone (x)
BACK = -0.31


def _chips():
    rnd = random.Random(11)
    return [(rnd.uniform(0.05, 0.8), rnd.uniform(0.03, 0.07), rnd.uniform(0.025, 0.06)) for _ in range(9)]


CHIPS = _chips()


def section(t):
    """The blade at t (0 foot, 1 point): back (x), jade boundary (x), edge (x), thickness."""
    xb, xj, xe = BACK, VEIN, EDGE
    for c, depth, width in CHIPS:   # the cleaved back's chips
        xb += depth * max(0.0, 1 - abs(t - c) / width) ** 1.5
    th = 0.12 * (1 - 0.35 * t)
    if t > 0.84:   # the back slopes down to meet the edge in a clipped point
        f = min(1.0, (t - 0.84) / 0.16)
        xb = xb + (0.27 - xb) * f ** 1.3
        xe = xe - 0.03 * f
        th *= (1 - f) ** 0.6
    xj = max(xj, xb + 0.01)
    xe = max(xe, xj)
    return xb, xj, xe, th


def stone_y(x, xb, xj, th):
    """The height of the stone flat at x (it falls from the back's bevel to the jade)."""
    thj = th * 0.55
    f = min(1.0, max(0.0, (x - (xb + 0.03)) / max(1e-4, xj - xb - 0.03)))
    return th + (thj - th) * f


def blade(stone, jade):
    n = 100
    s_rings, j_rings = [], []
    for k in range(n + 1):
        t = k / n
        z = FOOT + (TIP - FOOT) * t
        xb, xj, xe, th = section(t)
        thj = th * 0.55
        s_pts = [(xb, -th * 0.85), (xb, th * 0.85), (xb + 0.03, th), (xj, thj), (xj, -thj), (xb + 0.03, -th)]
        mid = xj + 0.6 * (xe - xj)
        j_pts = [(xj - 0.01, thj), (mid, thj * 0.45), (xe, 0.006), (xe, -0.006), (mid, -thj * 0.45), (xj - 0.01, -thj)]
        s_rings.append((V(((xb + xj) / 2, 0, z)), [V((x, y, z)) for x, y in s_pts]))
        j_rings.append((V(((xj + xe) / 2, 0, z)), [V((x, y, z)) for x, y in j_pts]))
    WK.loft(stone, s_rings, cap_end=False, uv_scale=1.5)
    WK.loft(jade, j_rings, cap_end=False, uv_scale=1.5)


def edge_glow(glow):
    """The jade's very edge, alight."""
    rings = []
    for k in range(97):
        t = 0.02 + 0.96 * k / 96
        z = FOOT + (TIP - FOOT) * t
        xb, xj, xe, th = section(t)
        thj = th * 0.55
        mid = xj + 0.6 * (xe - xj)

        def jade_y(x):
            return thj * 0.45 + (0.006 - thj * 0.45) * (x - mid) / max(1e-4, xe - mid)
        x0 = max(mid, xe - 0.05)
        rings.append((V((xe - 0.02, 0, z)), [V((x0, jade_y(x0) + 0.003, z)), V((xe + 0.006, 0.0, z)), V((x0, -jade_y(x0) - 0.003, z))]))
    WK.loft(glow, rings, cap_start=False, cap_end=False)


def veins(glow):
    """Finer veins of light branching from the jade across the stone, both faces: each runs from the
    jade toward the back and the point, a branch leaving it halfway."""
    def point(side, t, reach, wiggle):
        xb, xj, xe, th = section(t)
        x = xj - (xj - (xb + 0.06)) * reach + 0.012 * math.sin(wiggle)
        return V((x, side * (stone_y(x, xb, xj, th) + 0.003), FOOT + (TIP - FOOT) * t))

    for side in (1, -1):
        for ts, length in ((0.12, 0.13), (0.36, 0.15), (0.58, 0.12)):
            main = [point(side, ts + length * k / 12, 0.8 * k / 12, k * 0.75 + ts * 20) for k in range(13)]
            branch = [point(side, ts + length * 0.45 + 0.09 * k / 8, 0.36 + 0.3 * k / 8, k * 0.9) for k in range(9)]
            for pts in (main, branch):
                Hm.htube(glow, pts, lambda t: 0.012 * (1 - 0.7 * t), sides=5, per=1, uv_scale=3.0, tip=True, wobble=0.0)


def chamfered(hx, hy, c):
    return [(hx, hy - c), (hx - c, hy), (-hx + c, hy), (-hx, hy - c), (-hx, -hy + c), (-hx + c, -hy), (hx - c, -hy), (hx, -hy + c)]


def guard(stone, bronze, jade):
    """A dressed cornerstone banded in bronze, a jade cabochon in each face."""
    rings = []
    for z, hx, hy in ((-1.0, 0.47, 0.22), (-0.79, 0.49, 0.235), (-0.6, 0.42, 0.2)):
        rings.append((V((0, 0, z)), [V((x, y, z)) for x, y in chamfered(hx, hy, 0.06)]))
    WK.loft(stone, rings, uv_scale=3.0)
    band = [V((x * 1.01, y * 1.06, -0.79)) for x, y in chamfered(0.49, 0.235, 0.06)]
    Hm.htube(bronze, band + band[:3], lambda t: 0.03, sides=8, per=3, uv_scale=3.0, tip=False, wobble=0.0)
    for side in (1, -1):
        WK.blob(jade, (0, side * 0.2, -0.79), (0, side * 0.3, -0.79), 0.095, sides=16)


def grip(core, cord, bronze, stone, jade):
    Hm.htube(core, [V((0, 0, -0.6)), V((0, 0, 0.1)), V((0, 0, 0.8))], lambda t: 0.115, sides=14, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    for hand in (1, -1):
        WK.helix(cord, -0.55, 0.75, 0.124, 4.5, 0.02, hand=hand)
    for z in (-0.62, 0.8):
        Hm.htube(bronze, [V((0, 0, z - 0.04)), V((0, 0, z + 0.04))], lambda t: 0.14, sides=16, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    # the pommel: a small cornerstone turned on its point
    rings = []
    for z, r in ((0.82, 0.15), (1.0, 0.22), (1.2, 0.15)):
        pts = [(r * math.cos(TAU * i / 8 + TAU / 16) * (1 if i % 2 == 0 else 0.86), r * math.sin(TAU * i / 8 + TAU / 16) * (1 if i % 2 == 0 else 0.86))
               for i in range(8)]
        rings.append((V((0, 0, z)), [V((x, y, z)) for x, y in pts]))
    WK.loft(stone, rings, uv_scale=3.0)
    WK.blob(jade, (0, 0, 1.17), (0, 0, 1.26), 0.075, sides=14)


def build_sword2():
    root = W.collection("Sword2Hi")
    W.clear_collection(root)
    stone, jade, glow, core, cord, bronze, block, gem = (Hm.Hi() for _ in range(8))
    blade(stone, jade)
    edge_glow(glow)
    veins(glow)
    guard(block, bronze, gem)
    grip(core, cord, bronze, block, gem)
    jade_mat = WK.mat_celadon_jade()
    hi = [stone.object("JV_Stone", root, [WK.mat_slate()], smooth=False),
          jade.object("JV_Jade", root, [jade_mat], smooth=True),
          block.object("JV_Cornerstones", root, [WK.mat_stone()], smooth=False),
          bronze.object("JV_Bronze", root, [Hm.mat_bronze("WpnBronze")]),
          gem.object("JV_Cabochons", root, [jade_mat]),
          core.object("JV_Grip", root, [WK.mat_plain("WpnLeatherDark", (0.04, 0.03, 0.03), (0.12, 0.09, 0.07), rough=0.7)]),
          cord.object("JV_Cord", root, [WK.mat_cord("WpnCordBlue", (0.03, 0.06, 0.16), (0.12, 0.22, 0.46))])]
    for o in hi[:2]:
        o["keep"] = True
    return hi, {GLOW: ("Glow", [glow.object("JV_Glow", root, [WK.K.glow_material(GLOW)], smooth=False)])}, root


# ---------- Spear2: the Jade Crane Spear ----------
BUTT, SOCKET, NECK = 3.45, -3.0, -3.38
NECK_PTS = [(0, 0.0, NECK), (0, 0.22, -3.7), (0, 0.28, -4.05), (0, 0.12, -4.35)]
HEAD_PTS = [(0, 0.12, -4.35), (0, 0.02, -4.58), (0, -0.02, -4.8)]
BEAK_TIP = (0, -0.1, -6.0)


def crane(neck, head, beak, crest, glow):
    Hm.htube(neck, [V(p) for p in NECK_PTS], lambda t: 0.14 - 0.035 * t, sides=14, per=8, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(head, [V(p) for p in HEAD_PTS], lambda t: 0.1 + 0.11 * math.sin(math.pi * min(1.0, t * 1.1)) ** 0.8, sides=16, per=10,
             uv_scale=3.0, tip=True, wobble=0.0)
    Hm.htube(beak, [V((0, -0.01, -4.68)), V((0, -0.05, -5.3)), V(BEAK_TIP)], lambda t: 0.072 * (1 - t) ** 0.8 + 0.003, sides=12, per=8,
             uv_scale=3.0, tip=True, wobble=0.0)
    WK.blob(crest, (0, 0.15, -4.5), (0, 0.29, -4.55), 0.09, sides=14)
    for sx in (-1, 1):
        WK.blob(glow, (sx * 0.15, 0.06, -4.62), (sx * 0.205, 0.06, -4.62), 0.045, sides=10)


def wings(arm, glow):
    """The wings, half spread and swept back as the lugs: a leading edge of white jade from the
    shoulder to the wrist, a row of short coverts over it, and the flight feathers trailing back,
    longest at the tip, where the primaries are black. Two quills on each wing are alight."""
    specs = []
    for sx in (-1, 1):
        shoulder, wrist = V((sx * 0.1, 0.12, -3.5)), V((sx * 0.9, 0.32, -3.26))
        bend = V((sx * 0.5, 0.27, -3.46))
        Hm.htube(arm, [shoulder, bend, wrist], lambda t: 0.06 * (1 - 0.5 * t), sides=10, per=6, uv_scale=3.0, tip=True, wobble=0.0)
        for k in range(8):
            u = k / 7
            base = shoulder.lerp(bend, u * 2) if u < 0.5 else bend.lerp(wrist, u * 2 - 1)
            d = V((sx * (0.2 + 0.75 * u), 0.04, 1.0)).normalized()
            length = 0.5 + 0.6 * u ** 0.8
            n = V((0, 1, 0))
            specs.append(dict(base=base, direction=d, normal=n, length=length, width=0.17, fold=0.12, curl=0.12, twist=0.1 * sx,
                              mat=1 if k >= 5 else 0, steps=14))
            if k in (3, 4):
                nn = (n - d * n.dot(d)).normalized()
                pts = [base + d * length * t + nn * (0.12 * length * t * t + 0.02) for t in (0.1, 0.3, 0.5, 0.7, 0.85)]
                Hm.htube(glow, pts, lambda t: 0.013 * (1 - 0.6 * t), sides=5, per=3, uv_scale=3.0, tip=True, wobble=0.0)
        for k in range(6):   # the coverts, layered over the leading edge
            u = (k + 0.5) / 6
            base = (shoulder.lerp(bend, u * 2) if u < 0.5 else bend.lerp(wrist, u * 2 - 1)) + V((0, 0.035, -0.02))
            d = V((sx * (0.25 + 0.6 * u), 0.08, 1.0)).normalized()
            specs.append(dict(base=base, direction=d, normal=V((0, 1, 0)), length=0.34, width=0.15, fold=0.1, curl=0.1, mat=0, steps=10))
    return specs


def build_spear2():
    root = W.collection("Spear2Hi")
    W.clear_collection(root)
    shaft, bronze, cord, neck, head, beak, crest, glow, arm = (Hm.Hi() for _ in range(9))
    Hm.htube(shaft, [V((0, 0, BUTT)), V((0, 0, 0)), V((0, 0, SOCKET))], lambda t: 0.14 - 0.01 * t, sides=16, per=40, uv_scale=1.0,
             tip=False, wobble=0.0)
    for z0, z1 in ((SOCKET - 0.02, SOCKET + 0.12), (BUTT - 0.18, BUTT)):
        Hm.htube(bronze, [V((0, 0, z0)), V((0, 0, z1))], lambda t: 0.16, sides=16, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(bronze, [V((0, 0, SOCKET)), V((0, 0, -3.2)), V((0, 0, NECK - 0.03))], lambda t: 0.13 + 0.08 * math.sin(math.pi * t) ** 1.5,
             sides=18, per=8, uv_scale=3.0, tip=False, wobble=0.0)       # the socket's swelling collar
    Hm.htube(bronze, [V((0, 0, BUTT - 0.05)), V((0, 0, BUTT + 0.25)), V((0, 0, BUTT + 0.55))], lambda t: 0.13 * (1 - t) ** 0.7 + 0.004,
             sides=14, per=6, uv_scale=3.0, tip=True, wobble=0.0)        # the crane's-foot butt: a spike and three toes
    for k in range(3):
        a = TAU * k / 3 + TAU / 4
        c, s = math.cos(a), math.sin(a)
        Hm.htube(bronze, [V((0.08 * c, 0.08 * s, BUTT + 0.08)), V((0.2 * c, 0.2 * s, BUTT + 0.22)), V((0.26 * c, 0.26 * s, BUTT + 0.4))],
                 lambda t: 0.045 * (1 - t) ** 0.8 + 0.003, sides=8, per=5, uv_scale=3.0, tip=True, wobble=0.0)
    for hand in (1, -1):
        WK.helix(cord, -0.5, 0.5, 0.15, 4, 0.02, hand=hand)
    crane(neck, head, beak, crest, glow)
    white = WK.mat_white_jade()
    black = WK.mat_plain("WpnBlackJade", (0.015, 0.02, 0.025), (0.07, 0.09, 0.09), rough=0.2, scale=4.0)
    wing_specs = wings(arm, glow)
    hi = [shaft.object("JC_Shaft", root, [WK.mat_plain("WpnTealLacquer", (0.02, 0.07, 0.09), (0.06, 0.16, 0.18), rough=0.3, scale=3.0)]),
          bronze.object("JC_Bronze", root, [Hm.mat_bronze("WpnBronze")]),
          cord.object("JC_Cord", root, [WK.mat_cord("WpnCordBlue", (0.03, 0.06, 0.16), (0.12, 0.22, 0.46))]),
          neck.object("JC_Neck", root, [black]),
          head.object("JC_Head", root, [white]),
          arm.object("JC_WingEdges", root, [white]),
          beak.object("JC_Beak", root, [WK.mat_plain("WpnBeakGold", (0.3, 0.2, 0.06), (0.6, 0.44, 0.16), rough=0.3, metal=0.6)]),
          crest.object("JC_Crown", root, [WK.mat_plain("WpnCrownRed", (0.45, 0.02, 0.02), (0.75, 0.07, 0.04), rough=0.3)]),
          WK.leaves(root, "JC_Wings", [white, black], wing_specs, 0.03)]
    return hi, {GLOW: ("Glow", [glow.object("JC_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- both ----------
WEAPONS = {
    "Sword2": dict(kind="Sword", build=build_sword2, hilt=(0.0, 0.0, FOOT), tip=(0.27, 0.0, TIP), budget=7000),
    "Spear2": dict(kind="Spear", build=build_spear2, hilt=(0.0, 0.0, NECK), tip=BEAK_TIP, budget=10000),
}


def build(weapon_id):
    return WEAPONS[weapon_id]["build"]()


def export(weapon_id):
    spec = WEAPONS[weapon_id]
    hi, glow, root = spec["build"]()
    return WK.export(weapon_id, spec["kind"], "tier02.py", hi, glow, root, spec["hilt"], spec["tip"], budget=spec["budget"])
