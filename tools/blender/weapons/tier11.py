"""The Primordial Realm's weapons (run inside Blender): the eleventh realm's, whose aura is ancient
glyphs and vast layered energy. Their Qi is violet.

- Sword11, the Chaos Origin Sword: a great broad blade hewn from primordial obsidian, its edges rough
  as if not yet finished being made, violet fire running in its veins and great glyphs of light on
  its faces. An ammonite, the oldest shell, coils round its foot as the guard; its grip is bound
  in hide, and a rough stone is its pommel.
- Spear11, the Primeval Dragon Spear: the head is the skull of a dragon from before the world, its
  long spiralled horn the point, violet light in its eye sockets, great horns sweeping back from
  its crown; its spine runs down the dark ancient wood of the shaft, vertebra by vertebra.

    import tier11 as T
    T.build("Sword11"); T.export("Sword11")
"""
import math
import random

from mathutils import Vector

import weapon_kit as WK

Hm, W = WK.Hm, WK.W
V = Vector
TAU = WK.TAU
GLOW = "643cff"          # violet, the Divine Realm and above


def obsidian():
    return Hm.mat_obsidian("WpnPrimordialObsidian", vein=(0.45, 0.2, 1.0), vein_hot=(0.75, 0.6, 1.0), heat=(0.3, 0.1, 0.6), heat_reach=0.03)


def bone():
    return WK.mat_plain("WpnAncientBone", (0.42, 0.36, 0.27), (0.78, 0.72, 0.6), rough=0.6, scale=9.0, bump=0.12)


# ---------- Sword11: the Chaos Origin Sword ----------
FOOT, TIP, SHELL = -1.0, -4.9, -0.86


def _roughness():
    rnd = random.Random(11)
    return [(rnd.uniform(0.05, 0.85), rnd.uniform(0.015, 0.04), rnd.uniform(0.03, 0.07)) for _ in range(14)]


ROUGH = _roughness()


def half_width(t):
    w = 0.43 * (1 - 0.18 * t)
    for c, depth, width in ROUGH:   # hewn, not finished: the edges bitten here and there
        w -= depth * max(0.0, 1 - abs(t - c) / width) ** 1.5
    if t > 0.8:   # a broad chisel point
        w *= math.sqrt(max(0.0, 1 - ((t - 0.8) / 0.2) ** 1.6))
    return max(0.0, w)


def chaos_blade(stone, glow):
    surface = WK.blade(stone, FOOT, TIP, half_width, lambda t: 0.08 * (1 - 0.5 * t) + 0.01, rib=0.15, n=110)
    for side in (1, -1):
        def place(i, u, v, side=side):
            t = 0.08 + 0.15 * i + 0.11 * v
            return surface(t, (u - 0.5) * 0.42, side, 0.005)
        WK.runes(glow, place, 5, seed=110 + (side > 0), tube=0.017)


def ammonite(shell):
    """The shell coiling round the blade's foot, across it, two and a half turns, its tube swelling."""
    pts = []
    for k in range(80):
        f = k / 79
        a = 2.5 * TAU * f
        r = 0.08 + 0.36 * f ** 1.2
        pts.append(V((r * math.cos(a), r * math.sin(a), SHELL)))
    Hm.htube(shell, pts, lambda t: 0.03 + 0.12 * t ** 1.1, sides=14, per=2, uv_scale=6.0, tip=False, wobble=0.0)


def chaos_hilt(grip, cord, stone):
    Hm.htube(grip, [V((0, 0, SHELL + 0.12)), V((0, 0, 0.2)), V((0, 0, 0.85))], lambda t: 0.115, sides=14, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    WK.helix(cord, SHELL + 0.15, 0.8, 0.124, 7, 0.022)
    rings = []
    rnd = random.Random(3)
    for z, r in ((0.86, 0.15), (0.98, 0.24), (1.14, 0.2), (1.24, 0.08)):
        rings.append((V((0, 0, z)), [V((r * rnd.uniform(0.85, 1.1) * math.cos(TAU * i / 7), r * rnd.uniform(0.85, 1.1) * math.sin(TAU * i / 7), z))
                                     for i in range(7)]))
    WK.loft(stone, rings, uv_scale=3.0)


def build_sword11():
    root = W.collection("Sword11Hi")
    W.clear_collection(root)
    stone, shell, grip, cord, glow = (Hm.Hi() for _ in range(5))
    chaos_blade(stone, glow)
    ammonite(shell)
    chaos_hilt(grip, cord, stone)
    hi = [stone.object("CO_Obsidian", root, [obsidian()], smooth=False),
          shell.object("CO_Ammonite", root, [Hm.mat_fossil("WpnFossil")]),
          grip.object("CO_Grip", root, [WK.mat_plain("WpnHide", (0.16, 0.1, 0.06), (0.36, 0.25, 0.15), rough=0.8, scale=12.0)]),
          cord.object("CO_Cord", root, [WK.mat_cord("WpnSinew", (0.3, 0.24, 0.16), (0.6, 0.52, 0.38))])]
    hi[0]["keep"] = True
    return hi, {GLOW: ("Glow", [glow.object("CO_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- Spear11: the Primeval Dragon Spear ----------
BUTT, SOCKET, SNOUT, POINT = 3.45, -3.1, -4.0, -6.5


def section(c, hw, hh, p=2.6, n=16):
    return [V((c.x + hw * math.copysign(abs(math.cos(TAU * i / n)) ** (2 / p), math.cos(TAU * i / n)),
               c.y + hh * math.copysign(abs(math.sin(TAU * i / n)) ** (2 / p), math.sin(TAU * i / n)), c.z)) for i in range(n)]


def skull(bones, glow):
    cranium = [(0.0, 0.1, SOCKET, 0.34, 0.3), (0.0, 0.2, -3.3, 0.5, 0.4), (0.0, 0.17, -3.55, 0.4, 0.28), (0.0, 0.09, -3.8, 0.26, 0.18),
               (0.0, 0.06, SNOUT, 0.18, 0.13)]
    WK.loft(bones, [(V((x, y, z)), section(V((x, y, z)), hw, hh)) for x, y, z, hw, hh in cranium], uv_scale=3.0)
    jaw = [(0.0, -0.2, -3.25, 0.37, 0.1), (0.0, -0.22, -3.6, 0.26, 0.09), (0.0, -0.16, SNOUT + 0.06, 0.15, 0.06)]
    WK.loft(bones, [(V((x, y, z)), section(V((x, y, z)), hw, hh, 3.0)) for x, y, z, hw, hh in jaw], uv_scale=3.0)
    for sx in (-1, 1):
        WK.sphere(glow, (sx * 0.32, 0.3, -3.42), 0.075, sides=8)                                                 # the eyes' light
        WK.ring(bones, (sx * 0.32, 0.3, -3.42), (sx * 1, 0.4, 0), 0.12, 0.035, n=24)                             # the sockets' rims
        Hm.htube(bones, [V((sx * 0.32, 0.42, -3.2)), V((sx * 0.62, 0.64, -2.9)), V((sx * 0.8, 0.68, -2.4)), V((sx * 0.74, 0.52, -1.95))],
                 lambda t: 0.12 * (1 - t) ** 0.8 + 0.004, sides=10, per=6, uv_scale=3.0, tip=True, wobble=0.0)        # the great horns
        for z in (-3.5, -3.66, -3.82):
            WK.blob(bones, (sx * 0.18, -0.06, z), (sx * 0.18, -0.18, z), 0.035, sides=6)                         # teeth


def horn(bones, glow):
    """The long spiralled horn from the snout: the point."""
    curve = Hm.htube(bones, [V((0, 0.08, -3.8)), V((0, 0.1, -4.6)), V((0, 0.06, -5.6)), V((0, 0.02, POINT))],
                     lambda t: 0.16 * (1 - t) ** 0.9 + 0.003, sides=12, per=10, uv_scale=3.0, tip=True, wobble=0.0)
    frames = Hm.frames(curve)
    n = len(curve)
    for start in (0.0, math.pi):   # two spiral ridges up it, one lit
        pts = []
        for i in range(0, int(n * 0.9)):
            t = i / (n - 1)
            _, s, b = frames[i]
            a = start + 5 * TAU * t
            pts.append(curve[i] + (s * math.cos(a) + b * math.sin(a)) * (0.16 * (1 - t) ** 0.9 + 0.003) * 1.02)
        Hm.htube(glow if start == 0.0 else bones, pts, lambda t: 0.02 * (1 - 0.7 * t), sides=5, per=1, uv_scale=3.0, tip=True, wobble=0.0)


def spine(bones):
    for k in range(7):
        z = -2.7 + 0.32 * k
        Hm.htube(bones, [V((0, 0, z - 0.06)), V((0, 0, z + 0.06))], lambda t: 0.19, sides=12, per=2, uv_scale=3.0, tip=False, wobble=0.0)
        Hm.htube(bones, [V((0, 0.15, z)), V((0, 0.3, z + 0.08)), V((0, 0.36, z + 0.2))], lambda t: 0.05 * (1 - t) + 0.004, sides=6, per=3,
                 uv_scale=3.0, tip=True, wobble=0.0)


def build_spear11():
    root = W.collection("Spear11Hi")
    W.clear_collection(root)
    shaft, bones, glow = (Hm.Hi() for _ in range(3))
    Hm.htube(shaft, [V((0, 0, BUTT)), V((0, 0, 0)), V((0, 0, SOCKET))], lambda t: 0.15 - 0.01 * t, sides=16, per=40, uv_scale=1.0,
             tip=False, wobble=0.0)
    Hm.htube(bones, [V((0, 0, BUTT - 0.1)), V((0, 0, BUTT + 0.2)), V((0, 0, BUTT + 0.45))], lambda t: 0.16 * (1 - t) ** 0.6 + 0.004,
             sides=12, per=6, uv_scale=3.0, tip=True, wobble=0.0)
    skull(bones, glow)
    horn(bones, glow)
    spine(bones)
    hi = [shaft.object("PD_Shaft", root, [Hm.mat_bark("WpnAncientWood", base=(0.06, 0.04, 0.03), ridge=(0.28, 0.2, 0.12))]),
          bones.object("PD_Bone", root, [bone()])]
    return hi, {GLOW: ("Glow", [glow.object("PD_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- both ----------
WEAPONS = {
    "Sword11": dict(kind="Sword", build=build_sword11, hilt=(0.0, 0.0, FOOT), tip=(0.0, 0.0, TIP), budget=10000),
    "Spear11": dict(kind="Spear", build=build_spear11, hilt=(0.0, 0.0, SNOUT), tip=(0.0, 0.02, POINT - 0.02), budget=10000),
}


def build(weapon_id):
    return WEAPONS[weapon_id]["build"]()


def export(weapon_id):
    spec = WEAPONS[weapon_id]
    hi, glow, root = spec["build"]()
    return WK.export(weapon_id, spec["kind"], "tier11.py", hi, glow, root, spec["hilt"], spec["tip"], budget=spec["budget"])
