"""Eternal Transcendence's weapons (run inside Blender): the last realm's, whose aura is cosmic
rings, shifting colours and an effect of its own. Their light is three colours, gold, violet and
azure, where every other weapon's is one.

- Sword12, the Eternity Sword: a broad radiant blade of white gold, threads of gold, violet and
  azure light running down it side by side. Its guard is the sign of the endless, a figure eight of
  gold with a loop of violet light inside it; three rings of light orbit the blade, each its own
  colour and tilt, smaller toward the point, a bead of light on each; a ringed star is its pommel.
- Spear12, the Eternal Sun Spear: the head is a flame of white gold rising from a sun. The sun is a
  gold disc behind the head, its face ringed, flames of gold curling out round it, a ring of
  azure light at its rim and a ring of violet orbiting it aslant. The shaft is white gold lacquer.

    import tier12 as T
    T.build("Sword12"); T.export("Sword12")
"""
import math

from mathutils import Vector

import weapon_kit as WK

Hm, W = WK.Hm, WK.W
V = Vector
TAU = WK.TAU
GOLD, VIOLET, AZURE = "ffaa1e", "643cff", "28a0ff"


def radiant_steel():
    return WK.mat_plain("WpnRadiantSteel", (0.7, 0.64, 0.5), (0.96, 0.92, 0.82), rough=0.16, metal=0.85, scale=16.0, bump=0.02)


def gold():
    return Hm.mat_gold("WpnGold")


# ---------- Sword12: the Eternity Sword ----------
FOOT, TIP, GUARD = -1.0, -4.95, -0.85


def eternity_blade(steel, glows):
    def half_width(t):
        return 0.26 * (1 - 0.2 * t) * math.sqrt(max(0.0, 1 - max(0.0, (t - 0.86) / 0.14) ** 2))

    surface = WK.blade(steel, FOOT, TIP, half_width, lambda t: 0.05 * (1 - 0.5 * t) + 0.008, rib=0.25)
    for hexstr, offset in ((VIOLET, -0.06), (GOLD, 0.0), (AZURE, 0.06)):
        WK.ribbon(glows[hexstr], surface, 0.02, 0.85, lambda t, o=offset: o * (1 - 0.6 * t), lambda t: 0.012 * (1 - 0.5 * t), n=80)
    for hexstr, t, r, tilt in ((GOLD, 0.25, 0.5, (0.3, 0.2, 1)), (VIOLET, 0.5, 0.42, (-0.35, 0.15, 1)), (AZURE, 0.75, 0.32, (0.2, -0.4, 1))):
        centre = V((0, 0, FOOT + (TIP - FOOT) * t))
        WK.ring(glows[hexstr], centre, tilt, r, 0.022, n=56, sides=6)
        n = V(tilt).normalized()
        side = n.cross(V((0, 1, 0))).normalized()
        WK.sphere(glows[hexstr], centre + side * r, 0.05, sides=8)          # a bead of light travelling the ring


def lemniscate(scale, z):
    pts = []
    for k in range(97):
        a = TAU * k / 96
        d = 1 + math.sin(a) ** 2
        pts.append(V((scale * math.cos(a) / d, scale * math.sin(a) * math.cos(a) / d * 1.3, z)))
    return pts


def endless_guard(metal, glows):
    Hm.htube(metal, lemniscate(0.75, GUARD), lambda t: 0.06, sides=10, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(glows[VIOLET], lemniscate(0.58, GUARD), lambda t: 0.018, sides=6, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(metal, [V((0, 0, GUARD - 0.12)), V((0, 0, GUARD)), V((0, 0, GUARD + 0.12))], lambda t: 0.1 + 0.05 * math.sin(math.pi * t),
             sides=16, per=4, uv_scale=3.0, tip=False, wobble=0.0)


def star_pommel(metal, glows):
    Hm.htube(metal, [V((0, 0, GUARD + 0.1)), V((0, 0, 0.1)), V((0, 0, 0.82))], lambda t: 0.1, sides=14, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    WK.helix(metal, GUARD + 0.14, 0.78, 0.108, 6, 0.016)
    WK.sphere(glows[GOLD], (0, 0, 0.98), 0.09)
    for k in range(6):
        a = TAU * k / 6
        Hm.htube(metal, [V((0.06 * math.cos(a), 0.06 * math.sin(a), 0.98)), V((0.24 * math.cos(a), 0.24 * math.sin(a), 0.98))],
                 lambda t: 0.035 * (1 - t) + 0.004, sides=6, per=2, uv_scale=3.0, tip=True, wobble=0.0)
    WK.ring(glows[AZURE], (0, 0, 0.98), (0.4, 1, 0.3), 0.2, 0.012, n=40, sides=5)


def build_sword12():
    root = W.collection("Sword12Hi")
    W.clear_collection(root)
    steel, metal = Hm.Hi(), Hm.Hi()
    glows = {h: Hm.Hi() for h in (GOLD, VIOLET, AZURE)}
    eternity_blade(steel, glows)
    endless_guard(metal, glows)
    star_pommel(metal, glows)
    hi = [steel.object("ET_Blade", root, [radiant_steel()]),
          metal.object("ET_Gold", root, [gold()])]
    hi[0]["keep"] = True
    names = {GOLD: "Glow", VIOLET: "GlowViolet", AZURE: "GlowAzure"}
    return hi, {h: (names[h], [g.object("ET_" + names[h], root, [WK.K.glow_material(h)], smooth=True)]) for h, g in glows.items()}, root


# ---------- Spear12: the Eternal Sun Spear ----------
BUTT, SOCKET, SUN, FLAME_FOOT, POINT = 3.45, -3.1, -3.4, -3.55, -6.3


def flame_head(steel, glows):
    sway = lambda t: 0.06 * math.sin(t * 9) * t
    half = lambda t: 0.27 * math.sin(math.pi * (0.1 + 0.9 * t)) ** 0.7 * (1 - 0.2 * t) * (1 + 0.12 * math.sin(t * 18))
    surface = WK.blade(steel, FLAME_FOOT, POINT, half, lambda t: 0.05 * (1 - 0.6 * t) + 0.008, sway=sway, rib=0.3)
    WK.ribbon(glows[GOLD], surface, 0.03, 0.85, lambda t: 0.0, lambda t: 0.016 * (1 - 0.5 * t), n=80)


def sun(metal, glows):
    rings = [(V((0, 0, z)), [V((r * math.cos(TAU * i / 48), r * math.sin(TAU * i / 48), z)) for i in range(48)])
             for z, r in ((SUN - 0.05, 0.42), (SUN + 0.05, 0.42))]
    WK.loft(metal, rings, uv_scale=3.0)
    for r in (0.3, 0.18):
        WK.ring(metal, (0, 0, SUN - 0.05), (0, 0, 1), r, 0.022)
    for k in range(16):   # the flames curling out round it
        a = TAU * k / 16
        c, s = math.cos(a), math.sin(a)
        tc, ts = -s, c
        long_ = k % 2 == 0
        reach = 0.95 if long_ else 0.72
        pts = [V((0.4 * c, 0.4 * s, SUN)), V((0.6 * c + 0.08 * tc, 0.6 * s + 0.08 * ts, SUN + 0.02)),
               V(((reach - 0.1) * c - 0.04 * tc, (reach - 0.1) * s - 0.04 * ts, SUN + 0.05)), V((reach * c + 0.06 * tc, reach * s + 0.06 * ts, SUN + 0.1))]
        Hm.htube(metal, pts, lambda t, w=(0.07 if long_ else 0.05): w * (1 - t) ** 0.8 + 0.004, sides=8, per=4, uv_scale=3.0, tip=True, wobble=0.0)
    WK.ring(glows[AZURE], (0, 0, SUN - 0.06), (0, 0, 1), 0.43, 0.018, n=64, sides=6)
    WK.ring(glows[VIOLET], (0, 0, SUN), (0.5, 0.2, 1), 1.0, 0.016, n=80, sides=6)
    WK.sphere(glows[GOLD], (0, 0, SUN - 0.07), 0.1)


def build_spear12():
    root = W.collection("Spear12Hi")
    W.clear_collection(root)
    shaft, steel, metal = Hm.Hi(), Hm.Hi(), Hm.Hi()
    glows = {h: Hm.Hi() for h in (GOLD, VIOLET, AZURE)}
    Hm.htube(shaft, [V((0, 0, BUTT)), V((0, 0, 0)), V((0, 0, SOCKET))], lambda t: 0.135 - 0.01 * t, sides=16, per=40, uv_scale=1.0,
             tip=False, wobble=0.0)
    for z in (-2.3, -1.5, 1.5, 2.3):
        Hm.htube(metal, [V((0, 0, z - 0.035)), V((0, 0, z + 0.035))], lambda t: 0.15, sides=16, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(metal, [V((0, 0, SOCKET + 0.05)), V((0, 0, SUN)), V((0, 0, FLAME_FOOT - 0.03))], lambda t: 0.13 + 0.03 * math.sin(math.pi * t),
             sides=16, per=4, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(metal, [V((0, 0, BUTT - 0.08)), V((0, 0, BUTT + 0.18)), V((0, 0, BUTT + 0.36))], lambda t: 0.14 * (1 - t) ** 0.6 + 0.004,
             sides=14, per=6, uv_scale=3.0, tip=True, wobble=0.0)
    WK.helix(metal, -0.5, 0.5, 0.145, 6, 0.019)
    flame_head(steel, glows)
    sun(metal, glows)
    hi = [shaft.object("ES_Shaft", root, [WK.mat_plain("WpnWhiteGoldLacquer", (0.74, 0.66, 0.48), (0.94, 0.88, 0.72), rough=0.25, scale=3.0)]),
          steel.object("ES_Flame", root, [radiant_steel()]),
          metal.object("ES_Gold", root, [gold()])]
    names = {GOLD: "Glow", VIOLET: "GlowViolet", AZURE: "GlowAzure"}
    return hi, {h: (names[h], [g.object("ES_" + names[h], root, [WK.K.glow_material(h)], smooth=True)]) for h, g in glows.items()}, root


# ---------- both ----------
WEAPONS = {
    "Sword12": dict(kind="Sword", build=build_sword12, hilt=(0.0, 0.0, FOOT), tip=(0.0, 0.0, TIP), budget=10000),
    "Spear12": dict(kind="Spear", build=build_spear12, hilt=(0.0, 0.0, FLAME_FOOT), tip=(0.0, 0.0, POINT), budget=10000),
}


def build(weapon_id):
    return WEAPONS[weapon_id]["build"]()


def export(weapon_id):
    spec = WEAPONS[weapon_id]
    hi, glow, root = spec["build"]()
    return WK.export(weapon_id, spec["kind"], "tier12.py", hi, glow, root, spec["hilt"], spec["tip"], budget=spec["budget"])
