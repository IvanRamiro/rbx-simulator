"""The Void Realm's weapons (run inside Blender): the ninth realm's, whose aura is dark energy,
torn space and trails like a step through it. Their Qi is violet.

- Sword9, the Voidsilence Sword: a blade that is a cut in space. Black void glass, broken into
  segments that float apart, each a little turned, violet light leaking through the gaps; shards of
  the same glass orbit its guard round a ring of light; a black sphere ringed in light is its
  pommel.
- Spear9, the Abyss Fang Spear: a curved black fang-blade, its back serrated, comes through a portal
  at the socket, rings of light round a vortex spiralling into it, shards drifting about it. The
  shaft is black lacquer, lines of light running down it.

    import tier09 as T
    T.build("Sword9"); T.export("Sword9")
"""
import math

from mathutils import Vector

import weapon_kit as WK

Hm, W = WK.Hm, WK.W
V = Vector
TAU = WK.TAU
GLOW = "643cff"          # violet, the Divine Realm and above


def void_glass():
    return Hm.mat_voidglass("WpnVoidGlass")


# ---------- Sword9: the Voidsilence Sword ----------
FOOT, TIP, GUARD = -1.0, -4.75, -0.85
SEGMENTS = [(0.0, 0.22, 0.0, 0.0), (0.28, 0.48, 0.08, 0.22), (0.54, 0.74, -0.07, -0.3), (0.8, 1.0, 0.06, 0.35)]   # t0, t1, shift, turn


def void_half_width(t):
    return 0.21 * (1 - 0.2 * t) * math.sqrt(max(0.0, 1 - max(0.0, (t - 0.85) / 0.15) ** 2))


def thickness(t):
    return 0.05 * (1 - 0.5 * t) + 0.008


def segmented_blade(glass, glow):
    """Each segment a blade of its own over its stretch, shifted and turned a little; in each gap a
    thin sheet of light, the size of the blade there."""
    span = TIP - FOOT
    for t0, t1, shift, turn in SEGMENTS:
        WK.blade(glass, FOOT + span * t0, FOOT + span * t1, lambda u, t0=t0, t1=t1: void_half_width(t0 + (t1 - t0) * u),
                 lambda u, t0=t0, t1=t1: thickness(t0 + (t1 - t0) * u), sway=lambda u, s=shift: s, twist=lambda u, a=turn: a,
                 n=30, rib=0.2, cap_start=True, cap_end=t1 < 1.0)
    for (_, a1, s0, r0), (b0, _, s1, r1) in zip(SEGMENTS, SEGMENTS[1:]):
        t = (a1 + b0) / 2
        z = FOOT + span * t
        w, th = void_half_width(t) * 1.08, thickness(t) * 0.6
        pts = [V(((s0 + s1) / 2 + w * math.cos(TAU * i / 16), th * math.sin(TAU * i / 16), z)) for i in range(16)]
        WK.loft(glow, [(V(((s0 + s1) / 2, 0, z + 0.012)), [p + V((0, 0, 0.012)) for p in pts]), (V(((s0 + s1) / 2, 0, z - 0.012)),
                                                                                                 [p + V((0, 0, -0.012)) for p in pts])])


def shards(glass, glow):
    WK.ring(glow, (0, 0, GUARD), (0, 0, 1), 0.36, 0.016, n=64, sides=6)
    for k in range(6):
        a = TAU * k / 6
        c, s = math.cos(a), math.sin(a)
        r = 0.48 if k % 2 == 0 else 0.42
        WK.crystal(glass, (r * c * 0.75, r * s * 0.75, GUARD + 0.08 * (1 if k % 2 else -1)), (r * c * 1.6, r * s * 1.6, GUARD - 0.12), 0.1, sides=5,
                   waist=0.4, phase=a)
    rings = [(V((0, 0, z)), [V((r * math.cos(TAU * i / 20), r * math.sin(TAU * i / 20), z)) for i in range(20)])
             for z, r in ((GUARD - 0.12, 0.12), (GUARD, 0.17), (GUARD + 0.1, 0.12))]
    WK.loft(glass, rings, uv_scale=3.0)


def void_hilt(glass, grip, cord, glow):
    Hm.htube(grip, [V((0, 0, GUARD + 0.08)), V((0, 0, 0.1)), V((0, 0, 0.8))], lambda t: 0.1, sides=14, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    for hand in (1, -1):
        WK.helix(cord, GUARD + 0.12, 0.76, 0.108, 4.5, 0.017, hand=hand)
    WK.sphere(glass, (0, 0, 0.98), 0.17)
    WK.ring(glow, (0, 0, 0.98), (0.3, 1, 0.2), 0.26, 0.014, n=48, sides=6)


def build_sword9():
    root = W.collection("Sword9Hi")
    W.clear_collection(root)
    glass, grip, cord, glow = (Hm.Hi() for _ in range(4))
    segmented_blade(glass, glow)
    shards(glass, glow)
    void_hilt(glass, grip, cord, glow)
    hi = [glass.object("VS_Glass", root, [void_glass()]),
          grip.object("VS_Grip", root, [WK.mat_plain("WpnLeatherDark", (0.04, 0.03, 0.03), (0.12, 0.09, 0.07), rough=0.7)]),
          cord.object("VS_Cord", root, [WK.mat_cord("WpnCordViolet", (0.06, 0.03, 0.14), (0.24, 0.14, 0.5))])]
    hi[0]["keep"] = True
    return hi, {GLOW: ("Glow", [glow.object("VS_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- Spear9: the Abyss Fang Spear ----------
BUTT, SOCKET, PORTAL, POINT = 3.45, -3.2, -3.55, -6.3


def fang_blade(glass, glow):
    sway = lambda t: 0.4 * t * t
    half = lambda t: 0.2 * (1 - 0.35 * t) * math.sqrt(max(0.0, 1 - max(0.0, (t - 0.8) / 0.2) ** 2))
    surface = WK.blade(glass, PORTAL + 0.25, POINT, half, lambda t: 0.05 * (1 - 0.5 * t) + 0.008, sway=sway, rib=0.2)
    # the cutting edge (inside the curve) lit; teeth along the back (outside it)
    WK.ribbon(glow, surface, 0.04, 0.95, lambda t: -0.8 * half(t), lambda t: 0.014, n=90)
    span = POINT - (PORTAL + 0.25)
    for k in range(7):
        t = 0.1 + 0.1 * k
        z = PORTAL + 0.25 + span * t
        x = sway(t) + half(t) * 0.95
        Hm.htube(glass, [V((x - 0.03, 0, z + 0.06)), V((x + 0.09, 0, z + 0.02)), V((x + 0.14, 0, z + 0.1))],
                 lambda u: 0.035 * (1 - u) + 0.003, sides=6, per=3, uv_scale=3.0, tip=True, wobble=0.0)


def portal(metal, glow, glass):
    for r, z in ((0.64, PORTAL), (0.5, PORTAL - 0.04)):
        WK.ring(glow if r > 0.55 else metal, (0, 0, z), (0, 0.15, 1), r, 0.026 if r > 0.55 else 0.04, n=64, sides=6 if r > 0.55 else 8)
    for arm in range(3):   # the vortex spiralling in
        pts = []
        for k in range(18):
            f = k / 17
            a = TAU * arm / 3 + 2.4 * f
            r = 0.46 * (1 - f) + 0.05
            pts.append(V((r * math.cos(a), r * math.sin(a), PORTAL + 0.02 * f)))
        Hm.htube(glow, pts, lambda t: 0.014 * (1 - 0.6 * t), sides=5, per=2, uv_scale=3.0, tip=True, wobble=0.0)
    for k in range(4):
        a = TAU * k / 4 + 0.4
        c, s = math.cos(a), math.sin(a)
        WK.crystal(glass, (0.78 * c, 0.78 * s, PORTAL + 0.12), (0.94 * c, 0.94 * s, PORTAL - 0.16), 0.07, sides=5, waist=0.4, phase=a)


def build_spear9():
    root = W.collection("Spear9Hi")
    W.clear_collection(root)
    shaft, glass, metal, cord, glow = (Hm.Hi() for _ in range(5))
    Hm.htube(shaft, [V((0, 0, BUTT)), V((0, 0, 0)), V((0, 0, SOCKET))], lambda t: 0.135 - 0.01 * t, sides=16, per=40, uv_scale=1.0,
             tip=False, wobble=0.0)
    for k in range(3):   # lines of light down the shaft
        a = TAU * k / 3
        Hm.htube(glow, [V((0.138 * math.cos(a), 0.138 * math.sin(a), z)) for z in (-2.9, -1.6, -0.7)], lambda t: 0.012, sides=5, per=4,
                 uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(metal, [V((0, 0, SOCKET + 0.05)), V((0, 0, -3.38)), V((0, 0, PORTAL + 0.3))], lambda t: 0.12 + 0.04 * math.sin(math.pi * t),
             sides=16, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(metal, [V((0, 0, BUTT - 0.08)), V((0, 0, BUTT + 0.18)), V((0, 0, BUTT + 0.36))], lambda t: 0.14 * (1 - t) ** 0.6 + 0.004,
             sides=14, per=6, uv_scale=3.0, tip=True, wobble=0.0)
    for hand in (1, -1):
        WK.helix(cord, -0.5, 0.5, 0.145, 4, 0.019, hand=hand)
    fang_blade(glass, glow)
    portal(metal, glow, glass)
    hi = [shaft.object("AF_Shaft", root, [WK.mat_plain("WpnBlackLacquer", (0.01, 0.01, 0.015), (0.05, 0.045, 0.07), rough=0.25, scale=3.0)]),
          glass.object("AF_Glass", root, [void_glass()]),
          metal.object("AF_Metal", root, [WK.mat_plain("WpnBlackSteel", (0.03, 0.03, 0.04), (0.12, 0.11, 0.15), rough=0.3, metal=0.85)]),
          cord.object("AF_Cord", root, [WK.mat_cord("WpnCordViolet", (0.06, 0.03, 0.14), (0.24, 0.14, 0.5))])]
    hi[1]["keep"] = True
    return hi, {GLOW: ("Glow", [glow.object("AF_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- both ----------
WEAPONS = {
    "Sword9": dict(kind="Sword", build=build_sword9, hilt=(0.0, 0.0, FOOT), tip=(0.06, 0.0, TIP), budget=9000),
    "Spear9": dict(kind="Spear", build=build_spear9, hilt=(0.0, 0.0, PORTAL), tip=(0.4, 0.0, POINT), budget=9000),
}


def build(weapon_id):
    return WEAPONS[weapon_id]["build"]()


def export(weapon_id):
    spec = WEAPONS[weapon_id]
    hi, glow, root = spec["build"]()
    return WK.export(weapon_id, spec["kind"], "tier09.py", hi, glow, root, spec["hilt"], spec["tip"], budget=spec["budget"])
