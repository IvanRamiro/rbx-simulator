"""Spirit Soul's weapons (run inside Blender): the fourth realm's, whose aura is floating runes and
a translucent spirit silhouette. Their Qi is the realm's jade.

- Sword4, the Soulmirror Sword: a slim blade of black mirror steel, runes of jade light running
  down its middle, and beside each edge a line of light echoing it: the soul's silhouette of the
  blade. Its guard is a round bronze mirror, polished on the blade's side and cast with rings on
  the grip's, a ring of soul light round its face; a small mirror is its pommel.
- Spear4, the Moonpiercer Spear: a long needle of moon silver pierces a crescent moon. The crescent
  is set on the socket, opening forward round the needle, runes cut into it and moonlight along its
  inner edge. The shaft is deep indigo lacquer banded in silver.

    import tier04 as T
    T.build("Sword4"); T.export("Sword4")
"""
import math

from mathutils import Vector

import weapon_kit as WK

Hm, W = WK.Hm, WK.W
V = Vector
TAU = WK.TAU
GLOW = "14d296"          # Spirit Soul's jade (GameConfig.SwordFlight.RealmGlow)


def disc(hi, z0, z1, radius, n=48, mat=0):
    """A round plate across the blade's axis, from z0 to z1."""
    rings = [(V((0, 0, z)), [V((radius * math.cos(TAU * i / n), radius * math.sin(TAU * i / n), z)) for i in range(n)]) for z in (z0, z1)]
    WK.loft(hi, rings, mat=mat, uv_scale=3.0)


# ---------- Sword4: the Soulmirror Sword ----------
FOOT, TIP, MIRROR = -0.95, -4.6, -0.86


def soul_blade(steel, glow):
    def half_width(t):
        return 0.17 * (1 - 0.2 * t) * math.sqrt(max(0.0, 1 - max(0.0, (t - 0.88) / 0.12) ** 2))

    surface = WK.blade(steel, FOOT, TIP, half_width, lambda t: 0.045 * (1 - 0.45 * t) + 0.008, rib=0.25)
    # runes down the middle, both faces
    for side in (1, -1):
        def place(i, u, v, side=side):
            t = 0.08 + 0.12 * i + 0.08 * v
            return surface(t, (u - 0.5) * 0.12, side, 0.004)
        WK.runes(glow, place, 6, seed=4 + (side > 0), tube=0.011)
    # the soul's echo of each edge: a line of light just outside it, meeting beyond the point
    for sx in (-1, 1):
        pts = []
        for k in range(41):
            t = 0.03 + 0.97 * k / 40
            z = FOOT + (TIP - FOOT) * t
            pts.append(V((sx * (half_width(t) + 0.12 * (1 - 0.5 * t) * (1 + 0.3 * math.sin(t * 17 + sx))), 0, z - 0.08 * t)))
        pts.append(V((0, 0, TIP - 0.24)))
        Hm.htube(glow, pts, lambda t: 0.014 * (1 - 0.4 * t), sides=6, per=2, uv_scale=3.0, tip=True, wobble=0.0)


def mirror_guard(bronze, polished, glow):
    disc(bronze, MIRROR + 0.04, MIRROR + 0.1, 0.44)
    disc(polished, MIRROR - 0.005, MIRROR + 0.045, 0.4)
    WK.ring(bronze, (0, 0, MIRROR + 0.02), (0, 0, 1), 0.43, 0.03)
    for r in (0.34, 0.22):   # the cast rings on its back
        WK.ring(bronze, (0, 0, MIRROR + 0.1), (0, 0, 1), r, 0.016)
    for k in range(8):       # and the ring of bosses between them
        a = TAU * k / 8
        WK.sphere(bronze, (0.28 * math.cos(a), 0.28 * math.sin(a), MIRROR + 0.1), 0.028, sides=8)
    WK.ring(glow, (0, 0, MIRROR - 0.01), (0, 0, 1), 0.37, 0.012, n=64, sides=6)


def soul_hilt(bronze, polished, grip, cord):
    Hm.htube(grip, [V((0, 0, -0.76)), V((0, 0, 0.0)), V((0, 0, 0.78))], lambda t: 0.1, sides=14, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    for hand in (1, -1):
        WK.helix(cord, -0.72, 0.74, 0.11, 4.5, 0.017, hand=hand)
    disc(bronze, 0.8, 0.86, 0.17)
    disc(polished, 0.86, 0.89, 0.15)
    WK.blob(bronze, (0, 0, 0.88), (0, 0, 0.98), 0.06, sides=10)


def build_sword4():
    root = W.collection("Sword4Hi")
    W.clear_collection(root)
    steel, bronze, polished, grip, cord, glow = (Hm.Hi() for _ in range(6))
    soul_blade(steel, glow)
    mirror_guard(bronze, polished, glow)
    soul_hilt(bronze, polished, grip, cord)
    hi = [steel.object("SM_Blade", root, [WK.mat_plain("WpnMirrorSteel", (0.015, 0.02, 0.025), (0.07, 0.08, 0.09), rough=0.08, metal=0.9,
                                                       scale=12.0, bump=0.02)]),
          bronze.object("SM_Bronze", root, [Hm.mat_bronze("WpnBronze")]),
          polished.object("SM_Mirror", root, [WK.mat_plain("WpnPolishedBronze", (0.55, 0.42, 0.24), (0.82, 0.68, 0.42), rough=0.1, metal=0.9,
                                                           bump=0.01)]),
          grip.object("SM_Grip", root, [WK.mat_plain("WpnLeatherDark", (0.04, 0.03, 0.03), (0.12, 0.09, 0.07), rough=0.7)]),
          cord.object("SM_Cord", root, [WK.mat_cord("WpnCordJade", (0.02, 0.1, 0.07), (0.08, 0.32, 0.22))])]
    hi[0]["keep"] = True
    return hi, {GLOW: ("Glow", [glow.object("SM_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- Spear4: the Moonpiercer Spear ----------
BUTT, SOCKET, NEEDLE_FOOT, POINT = 3.45, -3.2, -3.35, -6.1
MOON_C, MOON_R, MOON_W, HORNS = -4.12, 0.8, 0.22, math.radians(140)


def needle(silver):
    WK.blade(silver, NEEDLE_FOOT, POINT, lambda t: 0.075 * (1 - t) ** 0.8 + 0.004, lambda t: 0.06 * (1 - t) ** 0.8 + 0.004, n=60, m=8, rib=0.0)


def crescent(silver, glow):
    """The crescent: a band round MOON_C, its back on the socket, its horns reaching forward."""
    n, th = 60, 0.04
    rows = []
    for k in range(n + 1):
        phi = -HORNS + 2 * HORNS * k / n
        d = V((math.sin(phi), 0, math.cos(phi)))
        w = MOON_W * math.cos(phi * (math.pi / 2) / HORNS) ** 0.8 + 0.004
        c = V((0, 0, MOON_C))
        o, i = c + d * MOON_R, c + d * (MOON_R - w)
        rows.append((o, i, d))
    for k in range(n):
        (o0, i0, d0), (o1, i1, d1) = rows[k], rows[k + 1]
        up, dn = V((0, th, 0)), V((0, -th, 0))
        ids = lambda pts: [silver.v(p) for p in pts]
        silver.facing(ids([o0 + up, o1 + up, i1 + up * 0.7, i0 + up * 0.7]), [(0, 0), (1, 0), (1, 1), (0, 1)], (0, 1, 0))
        silver.facing(ids([o0 + dn, o1 + dn, i1 + dn * 0.7, i0 + dn * 0.7]), [(0, 0), (1, 0), (1, 1), (0, 1)], (0, -1, 0))
        silver.facing(ids([o0 + up, o1 + up, o1 + dn, o0 + dn]), [(0, 0), (1, 0), (1, 1), (0, 1)], tuple((d0 + d1) / 2))
        silver.facing(ids([i0 + up * 0.7, i1 + up * 0.7, i1 + dn * 0.7, i0 + dn * 0.7]), [(0, 0), (1, 0), (1, 1), (0, 1)], tuple(-(d0 + d1) / 2))
    # moonlight along the inner edge, and runes cut into both faces
    inner = [rows[k][1] for k in range(4, n - 3)]
    Hm.htube(glow, inner, lambda t: 0.013, sides=6, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    for side in (1, -1):
        def place(i, u, v, side=side):
            phi = -HORNS * 0.75 + (2 * HORNS * 0.75) * (i + 0.15 + 0.7 * u) / 5
            d = V((math.sin(phi), 0, math.cos(phi)))
            w = MOON_W * math.cos(phi * (math.pi / 2) / HORNS) ** 0.8
            return V((0, 0, MOON_C)) + d * (MOON_R - w * (0.25 + 0.5 * v)) + V((0, side * (th + 0.004), 0))
        WK.runes(glow, place, 5, seed=40 + (side > 0), tube=0.011)


def build_spear4():
    root = W.collection("Spear4Hi")
    W.clear_collection(root)
    shaft, silver, glow, cord = (Hm.Hi() for _ in range(4))
    Hm.htube(shaft, [V((0, 0, BUTT)), V((0, 0, 0)), V((0, 0, SOCKET))], lambda t: 0.135 - 0.01 * t, sides=16, per=40, uv_scale=1.0,
             tip=False, wobble=0.0)
    for z in (-2.4, -1.6, 1.6, 2.4):
        Hm.htube(silver, [V((0, 0, z - 0.035)), V((0, 0, z + 0.035))], lambda t: 0.15, sides=16, per=2, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(silver, [V((0, 0, SOCKET + 0.05)), V((0, 0, -3.3)), V((0, 0, NEEDLE_FOOT - 0.05))], lambda t: 0.13 + 0.04 * math.sin(math.pi * t),
             sides=16, per=6, uv_scale=3.0, tip=False, wobble=0.0)
    Hm.htube(silver, [V((0, 0, BUTT - 0.08)), V((0, 0, BUTT + 0.15)), V((0, 0, BUTT + 0.32))], lambda t: 0.15 * (1 - t) ** 0.6 + 0.004,
             sides=14, per=6, uv_scale=3.0, tip=True, wobble=0.0)
    WK.sphere(silver, (0, 0, BUTT + 0.05), 0.17)
    for hand in (1, -1):
        WK.helix(cord, -0.5, 0.5, 0.145, 4, 0.019, hand=hand)
    needle(silver)
    crescent(silver, glow)
    hi = [shaft.object("MP_Shaft", root, [WK.mat_plain("WpnIndigoLacquer", (0.02, 0.025, 0.07), (0.07, 0.09, 0.2), rough=0.28, scale=3.0)]),
          silver.object("MP_Silver", root, [Hm.mat_moonsilver("WpnMoonSilver")]),
          cord.object("MP_Cord", root, [WK.mat_cord("WpnCordSilver", (0.25, 0.27, 0.32), (0.7, 0.73, 0.8))])]
    return hi, {GLOW: ("Glow", [glow.object("MP_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)])}, root


# ---------- both ----------
WEAPONS = {
    "Sword4": dict(kind="Sword", build=build_sword4, hilt=(0.0, 0.0, FOOT), tip=(0.0, 0.0, TIP), budget=9000),
    "Spear4": dict(kind="Spear", build=build_spear4, hilt=(0.0, 0.0, NEEDLE_FOOT), tip=(0.0, 0.0, POINT), budget=9000),
}


def build(weapon_id):
    return WEAPONS[weapon_id]["build"]()


def export(weapon_id):
    spec = WEAPONS[weapon_id]
    hi, glow, root = spec["build"]()
    return WK.export(weapon_id, spec["kind"], "tier04.py", hi, glow, root, spec["hilt"], spec["tip"], budget=spec["budget"])
