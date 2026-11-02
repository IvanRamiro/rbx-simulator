"""Spirit Core's weapons (run inside Blender): the third realm's, whose aura is swirling rings of
energy. Their Qi is the realm's jade.

- Sword3, the Coreflame Sword: a straight blade of dark steel forged round a spirit core. The core,
  a sphere of jade light, is the guard, three bronze rings orbiting it like an armillary and a
  fourth ring of light swinging wide; up the blade from it runs a channel of jade flame. A ring and
  a smaller core make the pommel.
- Spear3, the Ember Fang Spear: the head is the curved fang of a fire beast, ivory, embers glowing
  in its cracks, a smaller fang flaring either side of its root like the beast's jaw. Three bronze claws rise from the socket and cradle a burning spirit core under the
  fang's root, a ring of light circling it. The shaft is black-red lacquer banded in bronze.

    import tier03 as T
    T.build("Sword3"); T.export("Sword3")
"""
import math

from mathutils import Vector

import weapon_kit as WK

Hm, W = WK.Hm, WK.W
V = Vector
TAU = WK.TAU
GLOW = "14d296"          # Spirit Core's jade (GameConfig.SwordFlight.RealmGlow)
EMBER = "ff6414"


def dark_gold():
    return WK.mat_plain("WpnDarkGold", (0.22, 0.13, 0.04), (0.46, 0.3, 0.1), rough=0.32, metal=0.6, scale=18.0)


# ---------- Sword3: the Coreflame Sword ----------
FOOT, TIP, CORE = -1.0, -4.5, -0.85


def coreflame_blade(steel, glow):
    def half_width(t):
        return 0.2 * (1 - 0.15 * t) * math.sqrt(max(0.0, 1 - max(0.0, (t - 0.86) / 0.14) ** 2))

    surface = WK.blade(steel, FOOT, TIP, half_width, lambda t: 0.055 * (1 - 0.5 * t) + 0.01, rib=0.3)
    # the channel of jade flame: licking up from the core, swaying, narrowing
    WK.ribbon(glow, surface, 0.0, 0.68, lambda t: 0.025 * math.sin(t * 26), lambda t: 0.065 * (1 - t / 0.7) ** 0.6 * (0.75 + 0.25 * math.sin(t * 41)),
              n=90)


def armillary(gold, glow):
    WK.sphere(glow, (0, 0, CORE), 0.17)
    for normal in ((0, 0, 1), (1, 0, 0.55), (-1, 0, 0.55)):
        WK.ring(gold, (0, 0, CORE), normal, 0.36, 0.034)
    WK.ring(glow, (0, 0, CORE), (0.35, 1, 0.2), 0.55, 0.014, n=64, sides=6)     # the ring of light swinging wide
    for sx in (-1, 1):   # the blade's foot clasped where it leaves the rings
        WK.blob(gold, (sx * 0.05, 0, CORE - 0.3), (sx * 0.24, 0, CORE - 0.22), 0.05, sides=8)


def coreflame_hilt(gold, grip, cord, glow):
    Hm.htube(grip, [V((0, 0, -0.66)), V((0, 0, 0.0)), V((0, 0, 0.75))], lambda t: 0.105, sides=14, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    for hand in (1, -1):
        WK.helix(cord, -0.62, 0.72, 0.114, 4.5, 0.018, hand=hand)
    for z in (-0.68, 0.77):
        Hm.htube(gold, [V((0, 0, z - 0.04)), V((0, 0, z + 0.04))], lambda t: 0.13, sides=16, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    WK.ring(gold, (0, 0, 0.98), (1, 0, 0), 0.16, 0.03)
    WK.ring(gold, (0, 0, 0.98), (0, 1, 0), 0.16, 0.03)
    WK.sphere(glow, (0, 0, 0.98), 0.075)


def build_sword3():
    root = W.collection("Sword3Hi")
    W.clear_collection(root)
    steel, gold, grip, cord, glow = (Hm.Hi() for _ in range(5))
    coreflame_blade(steel, glow)
    armillary(gold, glow)
    coreflame_hilt(gold, grip, cord, glow)
    hi = [steel.object("CF_Blade", root, [WK.mat_plain("WpnDarkSteel", (0.12, 0.14, 0.15), (0.3, 0.34, 0.35), rough=0.28, metal=0.8, scale=20.0)]),
          gold.object("CF_Rings", root, [dark_gold()]),
          grip.object("CF_Grip", root, [WK.mat_plain("WpnLeatherDark", (0.04, 0.03, 0.03), (0.12, 0.09, 0.07), rough=0.7)]),
          cord.object("CF_Cord", root, [WK.mat_cord("WpnCordJade", (0.02, 0.1, 0.07), (0.08, 0.32, 0.22))])]
    hi[0]["keep"] = True
    return hi, {GLOW: ("Glow", [glow.object("CF_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- Spear3: the Ember Fang Spear ----------
BUTT, SOCKET, CORE_Z, FANG_ROOT = 3.4, -3.2, -3.62, -3.74
FANG = [(0, 0.0, FANG_ROOT), (0, 0.04, -4.5), (0, 0.18, -5.3), (0, 0.42, -6.05)]
SIDE_FANGS = [[(sx * 0.16, -0.04, FANG_ROOT + 0.02), (sx * 0.34, 0.0, -4.05), (sx * 0.42, 0.1, -4.45)] for sx in (-1, 1)]


def fang_radius(t):
    return 0.27 * (1 - t) ** 0.85 + 0.004


def fang(bone, ember):
    """The great fang, and a smaller one either side of its root, like a beast's jaw."""
    for pts in SIDE_FANGS:
        Hm.htube(bone, [V(p) for p in pts], lambda t: 0.11 * (1 - t) ** 0.85 + 0.003, sides=12, per=6, uv_scale=2.0, tip=True, wobble=0.0)
    curve = Hm.htube(bone, [V(p) for p in FANG], fang_radius, sides=18, per=12, uv_scale=2.0, tip=True, wobble=0.0)
    frames = Hm.frames(curve)
    n = len(curve)
    for k, (t0, t1, a0) in enumerate(((0.05, 0.55, 0.3), (0.12, 0.7, 2.2), (0.2, 0.5, 3.9), (0.08, 0.42, 5.1))):
        pts = []
        for j in range(14):
            f = j / 13
            t = t0 + (t1 - t0) * f
            i = min(n - 1, int(t * (n - 1)))
            _, s, b = frames[i]
            a = a0 + 0.35 * math.sin(f * 11 + k) + 0.25 * f
            pts.append(curve[i] + (s * math.cos(a) + b * math.sin(a)) * fang_radius(i / (n - 1)) * 1.02)
        Hm.htube(ember, pts, lambda t: 0.022 * (1 - 0.7 * t), sides=5, per=1, uv_scale=3.0, tip=True, wobble=0.0)


def claws(gold, glow):
    Hm.htube(gold, [V((0, 0, SOCKET)), V((0, 0, -3.35)), V((0, 0, -3.48))], lambda t: 0.15 + 0.05 * math.sin(math.pi * t),
             sides=18, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    for k in range(3):
        a = TAU * k / 3 + TAU / 12
        c, s = math.cos(a), math.sin(a)
        Hm.htube(gold, [V((0.15 * c, 0.15 * s, -3.42)), V((0.34 * c, 0.34 * s, -3.62)), V((0.32 * c, 0.32 * s, -3.92)),
                        V((0.2 * c, 0.2 * s, -4.1))], lambda t: 0.075 * (1 - t) ** 0.7 + 0.004, sides=10, per=6, uv_scale=3.0, tip=True,
                 wobble=0.0)
    WK.sphere(glow, (0, 0, CORE_Z), 0.13)
    WK.ring(glow, (0, 0, CORE_Z), (0.3, 1, 0.25), 0.4, 0.013, n=56, sides=6)


def build_spear3():
    root = W.collection("Spear3Hi")
    W.clear_collection(root)
    shaft, gold, cord, bone, glow, ember = (Hm.Hi() for _ in range(6))
    Hm.htube(shaft, [V((0, 0, BUTT)), V((0, 0, 0)), V((0, 0, SOCKET))], lambda t: 0.14 - 0.01 * t, sides=16, per=40, uv_scale=1.0,
             tip=False, wobble=0.0)
    for z in (-2.2, -1.0, 1.0, 2.2):
        Hm.htube(gold, [V((0, 0, z - 0.05)), V((0, 0, z + 0.05))], lambda t: 0.155, sides=16, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(gold, [V((0, 0, BUTT - 0.12)), V((0, 0, BUTT + 0.2)), V((0, 0, BUTT + 0.45))], lambda t: 0.15 * (1 - t) ** 0.6 + 0.004,
             sides=14, per=6, uv_scale=3.0, tip=True, wobble=0.0)
    for hand in (1, -1):
        WK.helix(cord, -0.5, 0.5, 0.15, 4, 0.02, hand=hand)
    claws(gold, glow)
    fang(bone, ember)
    hi = [shaft.object("EF_Shaft", root, [WK.mat_plain("WpnBlackRedLacquer", (0.025, 0.007, 0.006), (0.11, 0.025, 0.018), rough=0.3, scale=3.0)]),
          gold.object("EF_Bronze", root, [dark_gold()]),
          cord.object("EF_Cord", root, [WK.mat_cord("WpnCordEmber", (0.12, 0.03, 0.01), (0.42, 0.12, 0.04))]),
          bone.object("EF_Fang", root, [WK.mat_plain("WpnIvory", (0.56, 0.48, 0.36), (0.9, 0.84, 0.7), rough=0.45, scale=6.0)])]
    hi[3]["keep"] = True
    return hi, {GLOW: ("Glow", [glow.object("EF_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)]),
                EMBER: ("Ember", [ember.object("EF_Ember", root, [WK.K.glow_material(EMBER)], smooth=True)])}, root


# ---------- both ----------
WEAPONS = {
    "Sword3": dict(kind="Sword", build=build_sword3, hilt=(0.0, 0.0, FOOT), tip=(0.0, 0.0, TIP), budget=9000),
    "Spear3": dict(kind="Spear", build=build_spear3, hilt=(0.0, 0.0, FANG_ROOT), tip=(0.0, 0.46, -6.4), budget=9000),
}


def build(weapon_id):
    return WEAPONS[weapon_id]["build"]()


def export(weapon_id):
    spec = WEAPONS[weapon_id]
    hi, glow, root = spec["build"]()
    return WK.export(weapon_id, spec["kind"], "tier03.py", hi, glow, root, spec["hilt"], spec["tip"], budget=spec["budget"])
