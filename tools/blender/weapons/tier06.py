"""The Immortal Realm's weapons (run inside Blender): the sixth realm's, whose aura is layered halos
and luminous wings. Their Qi is the realm's gold.

- Sword6, the Lotusfall Sword: a sword growing out of a lotus. Its blade is one long petal of pearl,
  a line of golden light down its midrib; at its foot a lotus opens round it, an inner cup of
  petals clasping the blade and an outer ring falling open, round a golden seed pod. A halo of
  light stands behind the flower, golden rays round it; the grip is white silk bound in gold, and a
  lotus bud is its pommel.
- Spear6, the Crane Feather Spear: the head is a single great feather of an immortal crane, white
  turning gold toward its tip, its quill a line of golden light; at the socket a halo of light and
  two small wings of light flare back. The shaft is white lacquer banded in gold.

    import tier06 as T
    T.build("Sword6"); T.export("Sword6")
"""
import math

from mathutils import Vector

import weapon_kit as WK

Hm, W = WK.Hm, WK.W
V = Vector
TAU = WK.TAU
GLOW = "ffaa1e"          # the Immortal Realm's gold (GameConfig.SwordFlight.RealmGlow)


def gold():
    return Hm.mat_gold("WpnGold")


# ---------- Sword6: the Lotusfall Sword ----------
FOOT, TIP, FLOWER = -1.0, -4.65, -0.85


def petal_blade(pearl, glow):
    def half_width(t):
        return 0.24 * math.sin(math.pi * (0.1 + 0.9 * t)) ** 0.45 * (1 - 0.2 * t)

    surface = WK.blade(pearl, FOOT, TIP, half_width, lambda t: 0.05 * (1 - 0.5 * t) + 0.008, rib=0.3)
    WK.ribbon(glow, surface, 0.02, 0.8, lambda t: 0.0, lambda t: 0.016 * (1 - 0.6 * t), n=70)


def lotus():
    """The flower: an inner cup of petals clasping the blade, an outer ring falling open."""
    specs = []
    for k in range(8):
        a = TAU * k / 8 + TAU / 16
        c, s = math.cos(a), math.sin(a)
        specs.append(dict(base=V((0.1 * c, 0.1 * s, FLOWER)), direction=V((0.32 * c, 0.32 * s, -1.0)), normal=V((c, s, 0.0)),
                          length=0.55, width=0.17, fold=0.1, curl=0.25, twist=0.0, cup=0.35, mat=0, steps=12))
    for k in range(10):
        a = TAU * k / 10
        c, s = math.cos(a), math.sin(a)
        specs.append(dict(base=V((0.14 * c, 0.14 * s, FLOWER + 0.06)), direction=V((1.0 * c, 1.0 * s, -0.35)), normal=V((0.3 * c, 0.3 * s, -1.0)),
                          length=0.62, width=0.2, fold=0.08, curl=-0.35, twist=0.0, cup=0.3, mat=0, steps=12))
    return specs


def halo(metal, glow):
    z = FLOWER + 0.22
    WK.ring(glow, (0, 0, z), (0, 0, 1), 0.62, 0.022, n=72, sides=6)
    WK.ring(metal, (0, 0, z + 0.02), (0, 0, 1), 0.52, 0.02, n=64)
    for k in range(16):   # the rays
        a = TAU * k / 16
        c, s = math.cos(a), math.sin(a)
        length = 0.2 if k % 2 == 0 else 0.12
        Hm.htube(metal, [V((0.66 * c, 0.66 * s, z)), V(((0.66 + length) * c, (0.66 + length) * s, z))], lambda t: 0.025 * (1 - t) + 0.004,
                 sides=6, per=2, uv_scale=3.0, tip=True, wobble=0.0)
    for k in range(4):    # the stays holding it to the flower
        a = TAU * k / 4 + TAU / 8
        c, s = math.cos(a), math.sin(a)
        Hm.htube(metal, [V((0.12 * c, 0.12 * s, FLOWER + 0.08)), V((0.35 * c, 0.35 * s, z + 0.02)), V((0.52 * c, 0.52 * s, z + 0.02))],
                 lambda t: 0.018, sides=6, per=4, uv_scale=3.0, tip=False, wobble=0.0)


def lotus_hilt(silk, metal, bud):
    Hm.htube(metal, [V((0, 0, FLOWER - 0.05)), V((0, 0, FLOWER + 0.1)), V((0, 0, FLOWER + 0.2))], lambda t: 0.1 + 0.06 * math.sin(math.pi * t),
             sides=16, per=4, uv_scale=3.0, tip=False, wobble=0.0)      # the seed pod
    Hm.htube(silk, [V((0, 0, -0.62)), V((0, 0, 0.1)), V((0, 0, 0.8))], lambda t: 0.1, sides=14, per=6, uv_scale=6.0, tip=False, wobble=0.0)
    WK.helix(metal, -0.58, 0.76, 0.104, 9, 0.012)
    Hm.htube(metal, [V((0, 0, 0.78)), V((0, 0, 0.85))], lambda t: 0.12, sides=16, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(bud, [V((0, 0, 0.84)), V((0, 0, 1.02)), V((0, 0, 1.22))], lambda t: 0.13 * math.sin(math.pi * (0.3 + 0.7 * t)) ** 0.7 + 0.004,
             sides=14, per=6, uv_scale=3.0, tip=True, wobble=0.0)


def build_sword6():
    root = W.collection("Sword6Hi")
    W.clear_collection(root)
    pearl, metal, silk, bud, glow = (Hm.Hi() for _ in range(5))
    petal_blade(pearl, glow)
    halo(metal, glow)
    lotus_hilt(silk, metal, bud)
    petal = Hm.mat_petal("WpnLotusPetal")
    hi = [pearl.object("LF_Blade", root, [Hm.mat_pearl("WpnPearl")]),
          metal.object("LF_Gold", root, [gold()]),
          silk.object("LF_Grip", root, [WK.mat_plain("WpnWhiteSilk", (0.72, 0.7, 0.66), (0.9, 0.88, 0.84), rough=0.5, scale=40.0)]),
          bud.object("LF_Bud", root, [petal]),
          WK.leaves(root, "LF_Lotus", [petal], lotus(), 0.025)]
    hi[0]["keep"] = True
    return hi, {GLOW: ("Glow", [glow.object("LF_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- Spear6: the Crane Feather Spear ----------
BUTT, SOCKET, FEATHER_FOOT, POINT = 3.45, -3.2, -3.45, -6.3


def feather():
    """The feather's vane: one long blade either side of its quill, a little broader behind it,
    gathering to a single point."""
    return [dict(base=V((0.02, 0, FEATHER_FOOT)), direction=V((0.04, 0, -1.0)), normal=V((0, 1, 0)), length=FEATHER_FOOT - POINT, width=0.3,
                 fold=0.08, curl=0.05, twist=0.0, cup=0.12, mat=0, steps=28, across=8, shape=1.1)]


def quill(glow):
    pts = [V((0, 0.03 + 0.01 * math.sin(math.pi * f), FEATHER_FOOT + (POINT - FEATHER_FOOT) * f * 0.92)) for f in (0, 0.2, 0.4, 0.6, 0.8, 1.0)]
    Hm.htube(glow, pts, lambda t: 0.026 * (1 - 0.8 * t) + 0.004, sides=8, per=4, uv_scale=3.0, tip=True, wobble=0.0)
    WK.ring(glow, (0, 0, SOCKET - 0.18), (0, 0, 1), 0.42, 0.018, n=64, sides=6)


def light_wings():
    specs = []
    for sx in (-1, 1):
        for k, (dz, length) in enumerate(((0.35, 0.95), (0.7, 0.75), (1.0, 0.55))):
            specs.append(dict(base=V((sx * 0.12, 0.05, SOCKET - 0.22 + 0.04 * k)), direction=V((sx * 1.0, 0.25, dz)), normal=V((0, 1, -0.2)),
                              length=length, width=0.09, fold=0.1, curl=0.15, twist=0.1 * sx, mat=0, steps=10, shape=0.5))
    return specs


def build_spear6():
    root = W.collection("Spear6Hi")
    W.clear_collection(root)
    shaft, metal, cord, glow = (Hm.Hi() for _ in range(4))
    Hm.htube(shaft, [V((0, 0, BUTT)), V((0, 0, 0)), V((0, 0, SOCKET))], lambda t: 0.135 - 0.01 * t, sides=16, per=40, uv_scale=1.0,
             tip=False, wobble=0.0)
    for z in (-2.3, -1.5, 1.5, 2.3):
        Hm.htube(metal, [V((0, 0, z - 0.035)), V((0, 0, z + 0.035))], lambda t: 0.15, sides=16, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(metal, [V((0, 0, SOCKET + 0.05)), V((0, 0, -3.32)), V((0, 0, FEATHER_FOOT - 0.03))], lambda t: 0.12 + 0.05 * math.sin(math.pi * t),
             sides=16, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(metal, [V((0, 0, BUTT - 0.08)), V((0, 0, BUTT + 0.18)), V((0, 0, BUTT + 0.36))], lambda t: 0.14 * (1 - t) ** 0.6 + 0.004,
             sides=14, per=6, uv_scale=3.0, tip=True, wobble=0.0)
    for hand in (1, -1):
        WK.helix(cord, -0.5, 0.5, 0.145, 4, 0.019, hand=hand)
    quill(glow)
    hi = [shaft.object("CF6_Shaft", root, [WK.mat_plain("WpnWhiteLacquer", (0.7, 0.68, 0.62), (0.9, 0.88, 0.82), rough=0.28, scale=3.0)]),
          metal.object("CF6_Gold", root, [gold()]),
          cord.object("CF6_Cord", root, [WK.mat_cord("WpnCordGold", (0.35, 0.22, 0.05), (0.85, 0.62, 0.2))]),
          WK.leaves(root, "CF6_Feather", [Hm.mat_feather("WpnImmortalFeather", (0.88, 0.88, 0.84), (0.95, 0.9, 0.78), (0.95, 0.72, 0.28))],
                    feather(), 0.035)]
    wings = WK.leaves(root, "CF6_Wings", [WK.K.glow_material(GLOW)], light_wings(), 0.02)
    return hi, {GLOW: ("Glow", [glow.object("CF6_Glow", root, [WK.K.glow_material(GLOW)], smooth=True), wings])}, root


# ---------- both ----------
WEAPONS = {
    "Sword6": dict(kind="Sword", build=build_sword6, hilt=(0.0, 0.0, FOOT), tip=(0.0, 0.0, TIP), budget=10000),
    "Spear6": dict(kind="Spear", build=build_spear6, hilt=(0.0, 0.0, FEATHER_FOOT), tip=(0.0, 0.0, POINT), budget=9000),
}


def build(weapon_id):
    return WEAPONS[weapon_id]["build"]()


def export(weapon_id):
    spec = WEAPONS[weapon_id]
    hi, glow, root = spec["build"]()
    return WK.export(weapon_id, spec["kind"], "tier06.py", hi, glow, root, spec["hilt"], spec["tip"], budget=spec["budget"])
