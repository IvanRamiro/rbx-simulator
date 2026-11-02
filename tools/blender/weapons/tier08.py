"""The Cosmic Realm's weapons (run inside Blender): the eighth realm's, whose aura is orbiting stars
and nebulae. Their Qi is violet.

- Sword8, the Starriver Sword: a blade of night-sky glass, stars caught in it, a river of starlight
  meandering down it and stars glinting on its faces. Its guard is a spiral galaxy, two silver arms
  wheeling out from a bright core, stars strung along them; a silver star is its pommel.
- Spear8, the Comet Tail Spear: the head is a comet's nucleus, a crystal of icy light, its facet
  edges glowing; its tail streams back along the shaft as long fins of violet glass, each lit along
  its middle. The shaft is deep-space lacquer banded in silver.

    import tier08 as T
    T.build("Sword8"); T.export("Sword8")
"""
import math
import random

from mathutils import Vector

import weapon_kit as WK

Hm, W = WK.Hm, WK.W
V = Vector
TAU = WK.TAU
GLOW = "643cff"          # violet, the Divine Realm and above


def silver():
    return Hm.mat_moonsilver("WpnMoonSilver")


# ---------- Sword8: the Starriver Sword ----------
FOOT, TIP, GALAXY = -1.0, -4.7, -0.85


def star_blade(glass, glow):
    def half_width(t):
        return 0.22 * (1 - 0.15 * t) * math.sqrt(max(0.0, 1 - max(0.0, (t - 0.86) / 0.14) ** 2))

    surface = WK.blade(glass, FOOT, TIP, half_width, lambda t: 0.05 * (1 - 0.5 * t) + 0.008, rib=0.2)
    WK.ribbon(glow, surface, 0.02, 0.9, lambda t: 0.09 * math.sin(t * 8.5) * (1 - 0.6 * t), lambda t: 0.022 * (1 - 0.5 * t), n=120)
    rnd = random.Random(8)
    for side in (1, -1):
        for _ in range(12):
            t = rnd.uniform(0.05, 0.85)
            WK.sphere(glow, surface(t, rnd.uniform(-0.75, 0.75) * half_width(t), side, 0.004), rnd.uniform(0.012, 0.022), sides=6)


def galaxy(metal, glow):
    WK.sphere(glow, (0, 0, GALAXY), 0.17)
    for arm in (0, 1):
        pts = []
        for k in range(26):
            f = k / 25
            a = arm * math.pi + 1.4 * math.pi * f
            r = 0.16 + 0.62 * f
            pts.append(V((r * math.cos(a), r * math.sin(a), GALAXY + 0.04 * math.sin(f * 6))))
        Hm.htube(metal, pts, lambda t: 0.1 * (1 - t) + 0.014, sides=8, per=2, uv_scale=3.0, tip=True, wobble=0.0)
        for f in (0.35, 0.6, 0.85):
            p = pts[int(f * 25)]
            WK.sphere(glow, p + V((0, 0, -0.08)), 0.04, sides=6)
    WK.ring(metal, (0, 0, GALAXY + 0.05), (0, 0, 1), 0.2, 0.03)


def star_hilt(metal, grip, cord, glow):
    Hm.htube(grip, [V((0, 0, GALAXY + 0.08)), V((0, 0, 0.1)), V((0, 0, 0.8))], lambda t: 0.1, sides=14, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    for hand in (1, -1):
        WK.helix(cord, GALAXY + 0.12, 0.76, 0.108, 4.5, 0.017, hand=hand)
    WK.sphere(metal, (0, 0, 0.92), 0.12)
    for k in range(4):   # the star's points
        a = TAU * k / 4
        Hm.htube(metal, [V((0.08 * math.cos(a), 0.08 * math.sin(a), 0.92)), V((0.3 * math.cos(a), 0.3 * math.sin(a), 0.95))],
                 lambda t: 0.05 * (1 - t) + 0.004, sides=6, per=2, uv_scale=3.0, tip=True, wobble=0.0)
    Hm.htube(metal, [V((0, 0, 0.95)), V((0, 0, 1.25))], lambda t: 0.06 * (1 - t) + 0.004, sides=6, per=2, uv_scale=3.0, tip=True, wobble=0.0)
    WK.sphere(glow, (0, 0, 1.02), 0.05, sides=8)


def build_sword8():
    root = W.collection("Sword8Hi")
    W.clear_collection(root)
    glass, metal, grip, cord, glow = (Hm.Hi() for _ in range(5))
    star_blade(glass, glow)
    galaxy(metal, glow)
    star_hilt(metal, grip, cord, glow)
    hi = [glass.object("SV_Blade", root, [Hm.mat_nightsky("WpnNightSky")]),
          metal.object("SV_Silver", root, [silver()]),
          grip.object("SV_Grip", root, [WK.mat_plain("WpnLeatherDark", (0.04, 0.03, 0.03), (0.12, 0.09, 0.07), rough=0.7)]),
          cord.object("SV_Cord", root, [WK.mat_cord("WpnCordViolet", (0.06, 0.03, 0.14), (0.24, 0.14, 0.5))])]
    hi[0]["keep"] = True
    return hi, {GLOW: ("Glow", [glow.object("SV_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- Spear8: the Comet Tail Spear ----------
BUTT, SOCKET, NUCLEUS, POINT = 3.45, -3.2, -3.5, -6.2


def comet(ice, glow):
    waist = WK.crystal(ice, (0, 0, NUCLEUS), (0, 0, POINT), 0.27, sides=6, waist=0.15)
    point = V((0, 0, POINT))
    for p in waist:   # the facet edges, lit
        Hm.htube(glow, [p * 1.02 + V((0, 0, p.z * -0.02)), p.lerp(point, 0.5), point], lambda t: 0.014 * (1 - 0.7 * t), sides=5, per=4,
                 uv_scale=3.0, tip=True, wobble=0.0)


def tail(glow):
    specs = []
    for k in range(6):
        a = TAU * k / 6 + TAU / 12
        c, s = math.cos(a), math.sin(a)
        length = 2.2 if k % 2 == 0 else 1.6
        base = V((0.14 * c, 0.14 * s, NUCLEUS + 0.05))
        d = V((0.32 * c, 0.32 * s, 1.0)).normalized()
        n = V((c, s, 0.0))
        specs.append(dict(base=base, direction=d, normal=n, length=length, width=0.15, fold=0.05, curl=-0.1, twist=0.25, cup=0.15, mat=0,
                          steps=18, shape=0.8))
        nn = (n - d * n.dot(d)).normalized()
        pts = [base + d * length * t + nn * (-0.1 * length * t * t + 0.02) for t in (0.05, 0.25, 0.45, 0.65, 0.85)]
        Hm.htube(glow, pts, lambda t: 0.014 * (1 - 0.7 * t), sides=5, per=3, uv_scale=3.0, tip=True, wobble=0.0)
    return specs


def build_spear8():
    root = W.collection("Spear8Hi")
    W.clear_collection(root)
    shaft, ice, metal, cord, glow = (Hm.Hi() for _ in range(5))
    Hm.htube(shaft, [V((0, 0, BUTT)), V((0, 0, 0)), V((0, 0, SOCKET))], lambda t: 0.135 - 0.01 * t, sides=16, per=40, uv_scale=1.0,
             tip=False, wobble=0.0)
    for z in (-2.0, 1.6, 2.4):
        Hm.htube(metal, [V((0, 0, z - 0.035)), V((0, 0, z + 0.035))], lambda t: 0.15, sides=16, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(metal, [V((0, 0, SOCKET + 0.05)), V((0, 0, -3.35)), V((0, 0, NUCLEUS - 0.02))], lambda t: 0.12 + 0.05 * math.sin(math.pi * t),
             sides=16, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(metal, [V((0, 0, BUTT - 0.08)), V((0, 0, BUTT + 0.18)), V((0, 0, BUTT + 0.36))], lambda t: 0.14 * (1 - t) ** 0.6 + 0.004,
             sides=14, per=6, uv_scale=3.0, tip=True, wobble=0.0)
    for hand in (1, -1):
        WK.helix(cord, -0.5, 0.5, 0.145, 4, 0.019, hand=hand)
    comet(ice, glow)
    tail_specs = tail(glow)
    hi = [shaft.object("CT_Shaft", root, [WK.mat_plain("WpnSpaceLacquer", (0.012, 0.01, 0.035), (0.06, 0.045, 0.14), rough=0.25, scale=3.0)]),
          ice.object("CT_Nucleus", root, [WK.mat_plain("WpnCometIce", (0.32, 0.46, 0.74), (0.74, 0.86, 1.0), rough=0.08, scale=5.0)], smooth=False),
          metal.object("CT_Silver", root, [silver()]),
          cord.object("CT_Cord", root, [WK.mat_cord("WpnCordViolet", (0.06, 0.03, 0.14), (0.24, 0.14, 0.5))]),
          WK.leaves(root, "CT_Tail", [WK.mat_plain("WpnVioletGlass", (0.16, 0.08, 0.36), (0.5, 0.36, 0.86), rough=0.1, scale=4.0)], tail_specs, 0.025)]
    return hi, {GLOW: ("Glow", [glow.object("CT_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- both ----------
WEAPONS = {
    "Sword8": dict(kind="Sword", build=build_sword8, hilt=(0.0, 0.0, FOOT), tip=(0.0, 0.0, TIP), budget=9000),
    "Spear8": dict(kind="Spear", build=build_spear8, hilt=(0.0, 0.0, NUCLEUS), tip=(0.0, 0.0, POINT), budget=9000),
}


def build(weapon_id):
    return WEAPONS[weapon_id]["build"]()


def export(weapon_id):
    spec = WEAPONS[weapon_id]
    hi, glow, root = spec["build"]()
    return WK.export(weapon_id, spec["kind"], "tier08.py", hi, glow, root, spec["hilt"], spec["tip"], budget=spec["budget"])
