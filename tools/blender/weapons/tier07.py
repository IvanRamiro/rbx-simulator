"""The Divine Realm's weapons (run inside Blender): the seventh realm's, whose aura is violet
lightning, floating sigils and fields of power. Their Qi is violet (GameConfig.SwordFlight.DefaultGlow).

- Sword7, the Thunderjudge Sword: a bolt of lightning caught in a judge's seal. The blade is the
  bolt, dark iron zigzagging to its point, violet lightning crackling down it. The guard is the
  seal, a bronze block whose face is stamped with glowing script, a sigil ring floating round the
  blade before it; a thunder drum studded in bronze is the pommel.
- Spear7, the Thunderhowl Spear: the blade bursts from the open jaws of a roaring bronze
  thunder-beast, horned and maned, its eyes alight: a forked bolt of dark iron, lightning crackling
  down it, two small forks leaping from its root. The shaft is midnight lacquer bound in violet.

    import tier07 as T
    T.build("Sword7"); T.export("Sword7")
"""
import math

from mathutils import Vector

import weapon_kit as WK

Hm, W = WK.Hm, WK.W
V = Vector
TAU = WK.TAU
GLOW = "643cff"          # the violet of the Divine Realm and above (bluer than 8246ff, which Neon turns pink)


def tri(x):
    """A triangle wave through 0 at x = 0, between -1 and 1."""
    return 1 - 4 * abs(((x + 0.25) % 1.0) - 0.5)


def dark_iron():
    return WK.mat_plain("WpnDarkIron", (0.09, 0.09, 0.12), (0.28, 0.28, 0.33), rough=0.3, metal=0.85, scale=18.0)


def seal_block(hi, z0, z1, half, chamfer):
    rings = []
    for z in (z0, z1):
        pts = [(half, half - chamfer), (half - chamfer, half), (-half + chamfer, half), (-half, half - chamfer), (-half, -half + chamfer),
               (-half + chamfer, -half), (half - chamfer, -half), (half, -half + chamfer)]
        rings.append((V((0, 0, z)), [V((x, y, z)) for x, y in pts]))
    WK.loft(hi, rings, uv_scale=3.0)


# ---------- Sword7: the Thunderjudge Sword ----------
FOOT, TIP, SEAL = -1.12, -4.75, -0.92


def bolt_blade(iron, glow):
    def half_width(t):
        return 0.19 * (1 - 0.25 * t) * math.sqrt(max(0.0, 1 - max(0.0, (t - 0.88) / 0.12) ** 2))

    sway = lambda t: 0.15 * tri(t * 3.0) * min(1.0, t * 6)
    surface = WK.blade(iron, FOOT, TIP, half_width, lambda t: 0.05 * (1 - 0.5 * t) + 0.008, sway=sway, rib=0.25)
    WK.ribbon(glow, surface, 0.02, 0.95, lambda t: 0.05 * tri(t * 14), lambda t: 0.013 * (1 - 0.5 * t), n=140)


def seal(bronze, glow):
    seal_block(bronze, SEAL - 0.2, SEAL + 0.2, 0.3, 0.06)
    WK.ring(bronze, (0, 0, SEAL), (0, 0, 1), 0.33, 0.03)

    def place(i, u, v):   # four glyphs stamped in the face toward the blade
        gx, gy = i % 2, i // 2
        return V(((gx - 0.5) * 0.26 + (u - 0.5) * 0.2, (gy - 0.5) * 0.26 + (v - 0.5) * 0.2, SEAL - 0.205))
    WK.runes(glow, place, 4, seed=70, tube=0.012)
    WK.ring(glow, (0, 0, SEAL - 0.5), (0, 0, 1), 0.46, 0.014, n=64, sides=6)       # the sigil ring floating before it
    for k in range(8):
        a = TAU * k / 8
        p = V((0.46 * math.cos(a), 0.46 * math.sin(a), SEAL - 0.5))
        Hm.htube(glow, [p, p * 1.18 + V((0, 0, SEAL - 0.5)) * -0.18], lambda t: 0.012, sides=5, per=1, uv_scale=3.0, tip=False, wobble=0.0)


def drum_hilt(bronze, grip, cord, glow):
    Hm.htube(grip, [V((0, 0, SEAL + 0.2)), V((0, 0, 0.2)), V((0, 0, 0.82))], lambda t: 0.105, sides=14, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    for hand in (1, -1):
        WK.helix(cord, SEAL + 0.24, 0.78, 0.114, 4.5, 0.018, hand=hand)
    rings = [(V((0, 0, z)), [V((r * math.cos(TAU * i / 24), r * math.sin(TAU * i / 24), z)) for i in range(24)])
             for z, r in ((0.82, 0.16), (0.88, 0.22), (1.06, 0.22), (1.12, 0.16))]
    WK.loft(bronze, rings, uv_scale=3.0)
    for z in (0.9, 1.04):
        for k in range(12):
            a = TAU * k / 12
            WK.sphere(bronze, (0.225 * math.cos(a), 0.225 * math.sin(a), z), 0.022, sides=6)
    WK.ring(glow, (0, 0, 1.125), (0, 0, 1), 0.1, 0.014, n=32, sides=5)


def build_sword7():
    root = W.collection("Sword7Hi")
    W.clear_collection(root)
    iron, bronze, grip, cord, glow = (Hm.Hi() for _ in range(5))
    bolt_blade(iron, glow)
    seal(bronze, glow)
    drum_hilt(bronze, grip, cord, glow)
    hi = [iron.object("TJ_Blade", root, [dark_iron()]),
          bronze.object("TJ_Bronze", root, [Hm.mat_bronze("WpnBronze")]),
          grip.object("TJ_Grip", root, [WK.mat_plain("WpnLeatherDark", (0.04, 0.03, 0.03), (0.12, 0.09, 0.07), rough=0.7)]),
          cord.object("TJ_Cord", root, [WK.mat_cord("WpnCordViolet", (0.06, 0.03, 0.14), (0.24, 0.14, 0.5))])]
    hi[0]["keep"] = True
    return hi, {GLOW: ("Glow", [glow.object("TJ_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- Spear7: the Thunderhowl Spear ----------
BUTT, SOCKET, MOUTH, POINT = 3.45, -3.1, -3.85, -6.4


def section(c, hw, hh, p=2.6, n=16):
    return [V((c.x + hw * math.copysign(abs(math.cos(TAU * i / n)) ** (2 / p), math.cos(TAU * i / n)),
               c.y + hh * math.copysign(abs(math.sin(TAU * i / n)) ** (2 / p), math.sin(TAU * i / n)), c.z)) for i in range(n)]


def beast(bronze, glow):
    """The thunder-beast's head round the socket, roaring forward: skull and upper jaw, lower jaw,
    horns, a mane of spikes behind, teeth and eyes."""
    upper = [(0.0, 0.06, SOCKET, 0.28, 0.24), (0.0, 0.13, -3.35, 0.4, 0.32), (0.0, 0.14, -3.6, 0.32, 0.22), (0.0, 0.13, MOUTH, 0.23, 0.13),
             (0.0, 0.12, MOUTH - 0.1, 0.17, 0.09)]
    WK.loft(bronze, [(V((x, y, z)), section(V((x, y, z)), hw, hh)) for x, y, z, hw, hh in upper], uv_scale=3.0)
    lower = [(0.0, -0.14, -3.3, 0.27, 0.11), (0.0, -0.22, -3.6, 0.23, 0.1), (0.0, -0.26, MOUTH - 0.04, 0.17, 0.07)]
    WK.loft(bronze, [(V((x, y, z)), section(V((x, y, z)), hw, hh, 3.0)) for x, y, z, hw, hh in lower], uv_scale=3.0)
    for sx in (-1, 1):
        Hm.htube(bronze, [V((sx * 0.2, 0.36, -3.4)), V((sx * 0.4, 0.62, -3.2)), V((sx * 0.48, 0.78, -2.85)), V((sx * 0.42, 0.82, -2.55))],
                 lambda t: 0.09 * (1 - t) ** 0.8 + 0.004, sides=8, per=5, uv_scale=3.0, tip=True, wobble=0.0)          # horns
        WK.sphere(glow, (sx * 0.25, 0.25, -3.55), 0.05, sides=8)                                                  # eyes
        for z in (-3.62, -3.76):
            WK.blob(bronze, (sx * 0.17, 0.04, z), (sx * 0.17, -0.09, z), 0.03, sides=6)                          # fangs
    for k in range(9):   # the mane: spikes fanning back round the neck
        a = math.pi * (k / 8) - 0.05
        c, s = math.cos(a), math.sin(a)
        Hm.htube(bronze, [V((0.28 * c, 0.06 + 0.24 * s, SOCKET - 0.1)), V((0.5 * c, 0.06 + 0.44 * s, SOCKET + 0.15)),
                          V((0.62 * c, 0.06 + 0.56 * s, SOCKET + 0.5))], lambda t: 0.07 * (1 - t) + 0.003, sides=6, per=4, uv_scale=3.0,
                 tip=True, wobble=0.0)


def bolt_head(iron, glow):
    sway = lambda t: 0.12 * tri(t * 2.0) * min(1.0, t * 5)
    surface = WK.blade(iron, MOUTH + 0.1, POINT, lambda t: 0.23 * (1 - 0.3 * t) * math.sqrt(max(0.0, 1 - max(0.0, (t - 0.82) / 0.18) ** 2)),
                       lambda t: 0.05 * (1 - 0.5 * t) + 0.008, sway=sway, rib=0.25)
    WK.ribbon(glow, surface, 0.02, 0.92, lambda t: 0.045 * tri(t * 11), lambda t: 0.013, n=110)
    for sx in (-1, 1):   # two small forks leaping from its root
        pts = [V((sx * 0.1, 0, -4.05)), V((sx * 0.3, 0, -4.2)), V((sx * 0.24, 0, -4.38)), V((sx * 0.42, 0, -4.6))]
        Hm.htube(iron, pts, lambda t: 0.05 * (1 - t) + 0.004, sides=8, per=1, uv_scale=3.0, tip=True, wobble=0.0)
        Hm.htube(glow, [p + V((0, 0.045, 0)) for p in pts], lambda t: 0.012, sides=5, per=1, uv_scale=3.0, tip=True, wobble=0.0)


def build_spear7():
    root = W.collection("Spear7Hi")
    W.clear_collection(root)
    shaft, iron, bronze, cord, glow = (Hm.Hi() for _ in range(5))
    Hm.htube(shaft, [V((0, 0, BUTT)), V((0, 0, 0)), V((0, 0, SOCKET))], lambda t: 0.135 - 0.01 * t, sides=16, per=40, uv_scale=1.0,
             tip=False, wobble=0.0)
    for z in (-2.2, 1.6, 2.4):
        Hm.htube(bronze, [V((0, 0, z - 0.04)), V((0, 0, z + 0.04))], lambda t: 0.15, sides=16, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(bronze, [V((0, 0, BUTT - 0.1)), V((0, 0, BUTT + 0.2)), V((0, 0, BUTT + 0.42))], lambda t: 0.15 * (1 - t) ** 0.6 + 0.004,
             sides=14, per=6, uv_scale=3.0, tip=True, wobble=0.0)
    for hand in (1, -1):
        WK.helix(cord, -0.55, 0.55, 0.145, 4, 0.019, hand=hand)
    beast(bronze, glow)
    bolt_head(iron, glow)
    hi = [shaft.object("TH_Shaft", root, [WK.mat_plain("WpnMidnightLacquer", (0.015, 0.015, 0.04), (0.06, 0.06, 0.14), rough=0.28, scale=3.0)]),
          iron.object("TH_Blade", root, [dark_iron()]),
          bronze.object("TH_Beast", root, [Hm.mat_bronze("WpnBronze")]),
          cord.object("TH_Cord", root, [WK.mat_cord("WpnCordViolet", (0.06, 0.03, 0.14), (0.24, 0.14, 0.5))])]
    return hi, {GLOW: ("Glow", [glow.object("TH_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- both ----------
WEAPONS = {
    "Sword7": dict(kind="Sword", build=build_sword7, hilt=(0.0, 0.0, FOOT), tip=(0.0, 0.0, TIP), budget=10000),
    "Spear7": dict(kind="Spear", build=build_spear7, hilt=(0.0, 0.0, MOUTH), tip=(0.0, 0.0, POINT), budget=10000),
}


def build(weapon_id):
    return WEAPONS[weapon_id]["build"]()


def export(weapon_id):
    spec = WEAPONS[weapon_id]
    hi, glow, root = spec["build"]()
    return WK.export(weapon_id, spec["kind"], "tier07.py", hi, glow, root, spec["hilt"], spec["tip"], budget=spec["budget"])
