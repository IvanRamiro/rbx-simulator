"""The Ascendant Realm's weapons (run inside Blender): the fifth realm's, whose aura is golden energy,
glowing trails and Qinggong. Their Qi is the realm's gold.

- Sword5, the Skyrise Sword: a swallow diving. Its body, dark blue enamel with eyes of gold light,
  is the guard, its swept golden wings the quillons; the blade is its flight, pale gold steel rising
  in a gentle sweep with a line of golden cloud light up its middle; its forked tail is the pommel.
- Spear5, the Cloudspine Spear: a leaf blade of pale gold steel rising out of a collar of golden
  cloud scrolls, curling like the ruyi; cloud curls run down the top of the sky-blue lacquered shaft
  like a spine, and scrolls crown the butt.

    import tier05 as T
    T.build("Sword5"); T.export("Sword5")
"""
import math

from mathutils import Vector

import weapon_kit as WK

Hm, W = WK.Hm, WK.W
V = Vector
TAU = WK.TAU
GLOW = "ffaa1e"          # the Ascendant Realm's gold (GameConfig.SwordFlight.RealmGlow)


def pale_gold_steel():
    return WK.mat_plain("WpnPaleGoldSteel", (0.56, 0.5, 0.36), (0.88, 0.82, 0.64), rough=0.2, metal=0.85, scale=16.0, bump=0.03)


def gold():
    return Hm.mat_gold("WpnGold")


def scroll(hi, centre, out, axis, size, turns=1.7, tube=0.05, mat=0):
    """A ruyi cloud curl: a spiral in the plane of `out` and `axis`, starting near the centre side and
    winding inward."""
    c, o, a = V(centre), V(out).normalized(), V(axis).normalized()
    pts = []
    for k in range(25):
        f = k / 24
        th = math.pi + turns * math.pi * f
        rho = size * (1 - 0.7 * f)
        pts.append(c + o * (rho * math.cos(th)) + a * (rho * math.sin(th)))
    Hm.htube(hi, pts, lambda t: tube * (1 - 0.55 * t), sides=8, per=2, mat=mat, uv_scale=3.0, tip=True, wobble=0.0)


# ---------- Sword5: the Skyrise Sword ----------
FOOT, TIP = -1.05, -4.6


def skyrise_blade(steel, glow):
    def half_width(t):
        return 0.18 * (1 - 0.25 * t) * math.sqrt(max(0.0, 1 - max(0.0, (t - 0.86) / 0.14) ** 2))

    surface = WK.blade(steel, FOOT, TIP, half_width, lambda t: 0.05 * (1 - 0.5 * t) + 0.008, sway=lambda t: 0.12 * t * t, rib=0.3)
    WK.ribbon(glow, surface, 0.04, 0.62, lambda t: 0.035 * math.sin(t * 22) * (1 - t), lambda t: 0.018 * (1 - 0.4 * t), n=90)


def swallow(body, glow):
    """The swallow: head toward the blade, body over the grip's top, eyes alight; returns its swept
    wings' feathers (for weapon_kit.leaves)."""
    Hm.htube(body, [V((0, 0, -1.05)), V((0, 0.02, -0.92)), V((0, 0.03, -0.72)), V((0, 0.0, -0.58))],
             lambda t: 0.09 + 0.1 * math.sin(math.pi * min(1.0, t * 1.3)) ** 0.8, sides=14, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    for sx in (-1, 1):
        WK.sphere(glow, (sx * 0.1, 0.06, -0.98), 0.026, sides=8)
    specs = []
    for sx in (-1, 1):
        for k, (dx, dz, length) in enumerate(((1.0, 0.55, 1.2), (1.0, 0.85, 1.0), (0.8, 1.1, 0.8), (0.6, 1.3, 0.6))):
            specs.append(dict(base=V((sx * 0.09, 0.03, -0.9 + 0.05 * k)), direction=V((sx * dx, 0.05, dz)), normal=V((0, 1, 0)),
                              length=length, width=0.085, fold=0.12, curl=0.12, twist=0.1 * sx, mat=0, steps=16, shape=0.45))
    return specs


def skyrise_hilt(grip, cord, metal):
    Hm.htube(grip, [V((0, 0, -0.6)), V((0, 0, 0.1)), V((0, 0, 0.78))], lambda t: 0.1, sides=14, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    for hand in (1, -1):
        WK.helix(cord, -0.56, 0.74, 0.108, 4.5, 0.017, hand=hand)
    Hm.htube(metal, [V((0, 0, 0.74)), V((0, 0, 0.82)), V((0, 0, 0.9))], lambda t: 0.12 * (1 - 0.3 * t), sides=14, per=3, uv_scale=3.0,
             tip=False, wobble=0.0)
    for sx in (-1, 1):   # the forked tail
        Hm.htube(metal, [V((0, 0, 0.86)), V((sx * 0.1, 0, 1.12)), V((sx * 0.22, 0, 1.4)), V((sx * 0.3, 0, 1.62))],
                 lambda t: 0.055 * (1 - t) ** 0.8 + 0.004, sides=8, per=6, uv_scale=3.0, tip=True, wobble=0.0)


def build_sword5():
    root = W.collection("Sword5Hi")
    W.clear_collection(root)
    steel, body, grip, cord, metal, glow = (Hm.Hi() for _ in range(6))
    skyrise_blade(steel, glow)
    wing_specs = swallow(body, glow)
    skyrise_hilt(grip, cord, metal)
    gold_mat = gold()
    hi = [steel.object("SR_Blade", root, [pale_gold_steel()]),
          body.object("SR_Swallow", root, [WK.mat_plain("WpnNavyEnamel", (0.015, 0.025, 0.07), (0.05, 0.08, 0.2), rough=0.18, scale=6.0)]),
          WK.leaves(root, "SR_Wings", [gold_mat], wing_specs, 0.03),
          metal.object("SR_Tail", root, [gold_mat]),
          grip.object("SR_Grip", root, [WK.mat_plain("WpnLeatherDark", (0.04, 0.03, 0.03), (0.12, 0.09, 0.07), rough=0.7)]),
          cord.object("SR_Cord", root, [WK.mat_cord("WpnCordNavy", (0.02, 0.03, 0.1), (0.1, 0.16, 0.38))])]
    hi[0]["keep"] = True
    return hi, {GLOW: ("Glow", [glow.object("SR_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- Spear5: the Cloudspine Spear ----------
BUTT, SOCKET, HEAD_FOOT, POINT = 3.45, -3.2, -3.55, -6.15


def cloud_head(steel, metal, glow):
    def half_width(t):
        return 0.25 * math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.6 * (1 - 0.1 * t)

    surface = WK.blade(steel, HEAD_FOOT, POINT, half_width, lambda t: 0.05 * (1 - 0.6 * t) + 0.008, rib=0.35)
    WK.ribbon(glow, surface, 0.03, 0.75, lambda t: 0.05 * math.sin(t * 20) * (1 - t), lambda t: 0.02 * (1 - 0.5 * t), n=80)
    Hm.htube(metal, [V((0, 0, SOCKET + 0.05)), V((0, 0, -3.35)), V((0, 0, HEAD_FOOT - 0.03))], lambda t: 0.13 + 0.05 * math.sin(math.pi * t),
             sides=16, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    # the collar of cloud scrolls: four great curls and four small, round the socket
    for k in range(8):
        a = TAU * k / 8
        out = V((math.cos(a), math.sin(a), 0))
        big = k % 2 == 0
        scroll(metal, out * (0.5 if big else 0.36) + V((0, 0, -3.48 if big else -3.32)), out, (0, 0, -1), 0.3 if big else 0.19,
               tube=0.075 if big else 0.055)


def spine(metal):
    for k in range(7):   # cloud curls running down the shaft's top, alternating
        z = -2.85 + 0.42 * k
        scroll(metal, (0, 0.24, z), (0, 1, 0), (0, 0, -1 if k % 2 else 1), 0.13, turns=1.5, tube=0.045)


def build_spear5():
    root = W.collection("Spear5Hi")
    W.clear_collection(root)
    shaft, steel, metal, cord, glow = (Hm.Hi() for _ in range(5))
    Hm.htube(shaft, [V((0, 0, BUTT)), V((0, 0, 0)), V((0, 0, SOCKET))], lambda t: 0.135 - 0.01 * t, sides=16, per=40, uv_scale=1.0,
             tip=False, wobble=0.0)
    for z in (-1.2, 1.0):
        Hm.htube(metal, [V((0, 0, z - 0.04)), V((0, 0, z + 0.04))], lambda t: 0.15, sides=16, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    for hand in (1, -1):
        WK.helix(cord, -0.55, 0.55, 0.145, 4, 0.019, hand=hand)
    Hm.htube(metal, [V((0, 0, BUTT - 0.1)), V((0, 0, BUTT + 0.2)), V((0, 0, BUTT + 0.4))], lambda t: 0.14 * (1 - t) ** 0.6 + 0.004,
             sides=14, per=6, uv_scale=3.0, tip=True, wobble=0.0)
    for sx in (-1, 1):
        scroll(metal, (sx * 0.24, 0, BUTT + 0.1), (sx, 0, 0), (0, 0, 1), 0.12, tube=0.04)
    cloud_head(steel, metal, glow)
    spine(metal)
    hi = [shaft.object("CS_Shaft", root, [WK.mat_plain("WpnSkyLacquer", (0.08, 0.18, 0.36), (0.22, 0.42, 0.66), rough=0.28, scale=3.0)]),
          steel.object("CS_Blade", root, [pale_gold_steel()]),
          metal.object("CS_Gold", root, [gold()]),
          cord.object("CS_Cord", root, [WK.mat_cord("WpnCordNavy", (0.02, 0.03, 0.1), (0.1, 0.16, 0.38))])]
    return hi, {GLOW: ("Glow", [glow.object("CS_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- both ----------
WEAPONS = {
    "Sword5": dict(kind="Sword", build=build_sword5, hilt=(0.0, 0.0, FOOT), tip=(0.0, 0.0, TIP), budget=9000),
    "Spear5": dict(kind="Spear", build=build_spear5, hilt=(0.0, 0.0, HEAD_FOOT), tip=(0.0, 0.0, POINT), budget=9000),
}


def build(weapon_id):
    return WEAPONS[weapon_id]["build"]()


def export(weapon_id):
    spec = WEAPONS[weapon_id]
    hi, glow, root = spec["build"]()
    return WK.export(weapon_id, spec["kind"], "tier05.py", hi, glow, root, spec["hilt"], spec["tip"], budget=spec["budget"])
