"""The Demonic faction's secret weapon (run inside Blender, headless): the Bloodmoon Saber, id SecretDemonic.

    blender -b --factory-startup --python tools/blender/weapons/secret_demonic.py -- clay|export|review|all

Idea: overwhelming and feared. A black saber that bites out of a beast's jaws, a ridge of hooked spines down its back and an
ember burning in its steel.
- The blade is curved, single-edged black iron: it bows toward +X, the spine on the inside of the curve and the edge on the outside,
  a clip point at the tip. Crimson veins run through the iron (painted into the colour map); an ember-orange bar of light (the
  "Glow" piece, Neon, saturated orange-red) lies in the fuller beside the spine. Nine jagged spines, hooked back toward the hilt
  and uneven in size, serrate the back.
- The guard is a beast's head biting the blade's root: an iron skull block, a snout whose upper jaw rests on the blade and whose
  lower jaw lies under it (the blade is clamped between them), two long steel fangs hanging from the upper jaw and two shorter
  ones rising from the lower, small teeth along both gums, a crimson mouth, a crest of three spines, swept cheek spines and two
  curved steel tusks sweeping out and forward as the cross-guard. An animal, not a skull: a muzzle, lips, a mouth, no eyes and no
  sockets anywhere.
- The grip is iron wrapped in ragged crimson cloth, and three torn rags hang from the pommel's ring; the pommel is a short iron
  cap with three claws.

Parts and contacts (studs from the grip, point toward -Z; the hand closes on z -0.4..0.4):
  head        skull block z -0.60 to -1.15, upper jaw z -1.05 to -1.64 (its underside 0.008 below the blade's top: it presses on it),
              lower jaw z -1.10 to -1.45 (likewise from below), tusks rooted inside the skull;
  blade       from z -0.95 (inside the skull) along its curve to the tip at (0.52, -5.25), runs through the jaws;
  grip        z -0.75 (inside the skull) to 0.86, cloth wound on it;
  pommel      z 0.82 to 1.12, ring at 1.17, rags tied to the ring.
The head's rear face (z -0.60) stands clear of the fist (-0.40) and the pommel (0.82) of its back (0.40).

Authored in the realm weapons' convention (see weapon_kit.py).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import secret_kit as SK  # noqa: E402

WK, Hm, W = SK.WK, SK.Hm, SK.W
V = Vector
TAU = SK.TAU
WEAPON_ID = "SecretDemonic"
COMPARE = ("Sword6", 2.4)
GLOW = "ff4010"             # saturated ember orange-red
UP = V((0, 1, 0))

# ---------- the blade's curve ----------
Z0, LEN, BEND = -0.95, 4.45, 0.0365       # root z, length along z, how far it bows: x = BEND * s^2
CLIP = 3.2                                # where the clip point starts cutting the spine back


def c0(s):
    return V((BEND * s * s, 0.0, Z0 - s))


def side0(s):
    t = V((2 * BEND * s, 0.0, -1.0)).normalized()
    return t.cross(UP).normalized()       # +X: toward the spine, the inside of the curve


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def hu(s):
    """Half-width of the unclipped blade."""
    return 0.225 - 0.055 * smoothstep(0.0, 3.1, s)


def hw(s):
    """Half-width with the clip point: the spine is cut back toward the edge over the last stretch."""
    if s <= CLIP:
        return hu(s)
    f = (s - CLIP) / (LEN - CLIP)
    return hu(s) * max(0.0, 1 - f ** 1.25)


def centre(s):
    return c0(s) - side0(s) * (hu(s) - hw(s))


def spine(s):
    return centre(s) + side0(s) * hw(s)


def edge(s):
    return centre(s) - side0(s) * hw(s)


def half_thick(s):
    return 0.075 * (1 - 0.34 * s / LEN) + 0.004


BLADE_PROFILE = [(-1.0, 0.0), (-0.55, 0.55), (0.55, 0.85), (1.0, 0.6), (1.0, -0.6), (0.55, -0.85), (-0.55, -0.55)]
TIP_POINT = edge(LEN)


# ---------- materials ----------
def _u(g):
    u, v, _ = g.sep(g.coords("UV"))
    return u, v


def smooth(g, x, a, b):
    return SK.smooth(g, x, a, b)


def _veins(g, density=1.0):
    """Thin crimson veins branching through the iron (a distorted noise's ridge lines, in patches). Returns (vein, core)."""
    co = g.coords()
    vn = g.n("ShaderNodeTexNoise", **{"Scale": 3.4 * density, "Detail": 4.0, "Roughness": 0.5, "Distortion": 0.7})
    g.link(co, vn.inputs["Vector"])
    patch = WK._noise(g, 1.7, 2.0)
    d = g.math("ABSOLUTE", g.math("SUBTRACT", vn.outputs["Fac"], 0.5))
    on = g.math("GREATER_THAN", patch, 0.42)
    return g.math("MULTIPLY", g.math("LESS_THAN", d, 0.012), on), g.math("MULTIPLY", g.math("LESS_THAN", d, 0.0045), on)


def mat_saber_iron(name="BmSaberIron"):
    """Black iron: hammer-scale mottling, a dark steel polish on the edge bevel, crimson veins through it. UV u runs round the
    blade's section: the edge faces are u 0..0.29 (points 0 to 2 of 7) and 0.86..1, the spine 0.43..0.57."""
    g = Hm._Graph(name)
    u, _ = _u(g)
    mott = WK._noise(g, 14.0, 6.0)
    fine = WK._noise(g, 60.0, 3.0)
    base = g.ramp(g.math("ADD", g.math("MULTIPLY", mott, 0.7), g.math("MULTIPLY", fine, 0.3)), [(0.3, (0.012, 0.012, 0.015)), (0.7, (0.045, 0.042, 0.05))])
    bevel = g.math("MAXIMUM", g.math("LESS_THAN", u, 0.145), g.math("GREATER_THAN", u, 0.857))
    polish = g.mix(g.math("MULTIPLY", bevel, 0.9), base, (0.3, 0.3, 0.33))
    vein, core = _veins(g)
    col = g.mix(vein, polish, (0.5, 0.025, 0.03))
    col = g.mix(core, col, (0.95, 0.2, 0.06))
    col = g.ao(col, 0.04, 0.5)
    rough = g.math("ADD", g.math("ADD", 0.34, g.math("MULTIPLY", mott, 0.2)), g.math("MULTIPLY", bevel, -0.18))
    return g.finish(col, rough, 0.9, g.bump(g.math("ADD", mott, g.math("MULTIPLY", fine, 0.4)), 0.12, 0.003))


def mat_beast_iron(name="BmBeastIron"):
    """The head's, spines' and pommel's iron: the same black, crimson veins, and the mouth lined in crimson: wherever a surface
    faces the gap between the jaws (its normal turned toward the blade's plane) it is crimson."""
    g = Hm._Graph(name)
    mott = WK._noise(g, 12.0, 6.0)
    fine = WK._noise(g, 55.0, 3.0)
    base = g.ramp(g.math("ADD", g.math("MULTIPLY", mott, 0.7), g.math("MULTIPLY", fine, 0.3)), [(0.3, (0.012, 0.011, 0.014)), (0.7, (0.05, 0.045, 0.052))])
    vein, core = _veins(g, 0.8)
    col = g.mix(vein, base, (0.5, 0.025, 0.03))
    col = g.mix(core, col, (0.95, 0.2, 0.06))
    geo = g.n("ShaderNodeNewGeometry")
    nx, _, nz = g.sep(geo.outputs["Normal"])
    cx, cy, cz = g.sep(g.coords())              # Blender x and z are the radial plane, y the weapon's axis (forward = +y)
    inward = g.math("ADD", g.math("MULTIPLY", nx, g.math("MULTIPLY", cx, 0.69)), g.math("MULTIPLY", nz, g.math("MULTIPLY", cz, 1.6)))   # negative where the surface faces the axis (the cup is squashed: x / 1.45, z / 0.62)
    in_cup = g.math("MULTIPLY", g.math("GREATER_THAN", cy, 0.55), g.math("LESS_THAN", cy, 1.75))
    mouth = g.math("MULTIPLY", smooth(g, g.math("MULTIPLY", inward, -1.0), 0.02, 0.12), in_cup)
    lining = g.ramp(mott, [(0.3, (0.22, 0.01, 0.02)), (0.7, (0.5, 0.04, 0.04))])
    col = g.mix(mouth, col, lining)
    col = g.ao(col, 0.04, 0.5)
    rough = g.math("ADD", 0.38, g.math("MULTIPLY", mott, 0.2))
    return g.finish(col, rough, g.math("MULTIPLY", g.math("SUBTRACT", 1.0, mouth), 0.88), g.bump(g.math("ADD", mott, g.math("MULTIPLY", fine, 0.4)), 0.14, 0.003))


def mat_fang(name="BmFang", root_heat=True):
    """Steel fangs and tusks: pale steel, a heat of crimson at the root (fangs: by distance from the blade's plane), polished."""
    g = Hm._Graph(name)
    n = WK._noise(g, 20.0, 4.0)
    col = g.ramp(n, [(0.3, (0.5, 0.52, 0.55)), (0.7, (0.72, 0.74, 0.77))])
    if root_heat:
        yb = g.sep(g.coords())[1]
        root = g.math("SUBTRACT", 1.0, smooth(g, yb, 1.72, 1.84))
        col = g.mix(g.math("MULTIPLY", root, 0.85), col, (0.6, 0.04, 0.03))
    col = g.ao(col, 0.03, 0.5)
    return g.finish(col, g.math("ADD", 0.2, g.math("MULTIPLY", n, 0.1)), 0.88, g.bump(n, 0.08, 0.003))


def mat_cloth(name="BmCrimsonCloth", dark=(0.16, 0.008, 0.012), light=(0.62, 0.05, 0.05)):
    """Ragged crimson cloth: a coarse weave, dirty and sun-bleached in patches, scorched dark at the torn edges."""
    g = Hm._Graph(name)
    u, v = _u(g)
    cx, cy, cz = g.sep(g.coords())
    weave = g.math("MULTIPLY", g.math("ADD", g.math("ADD", g.math("SINE", g.math("MULTIPLY", cx, 300.0)), g.math("SINE", g.math("MULTIPLY", cy, 300.0))), 2.0), 0.25)
    patch = WK._noise(g, 4.0, 5.0)
    col = g.ramp(g.math("ADD", g.math("MULTIPLY", patch, 0.8), g.math("MULTIPLY", weave, 0.3)), [(0.25, dark), (0.6, (0.38, 0.025, 0.03)), (0.9, light)])
    edge = g.math("MAXIMUM", smooth(g, g.math("SUBTRACT", 0.12, u), 0.0, 0.12), smooth(g, g.math("SUBTRACT", u, 0.88), 0.0, 0.12))
    col = g.mix(g.math("MULTIPLY", edge, 0.7), col, (0.03, 0.01, 0.01))
    col = g.ao(col, 0.04, 0.5)
    return g.finish(col, 0.88, 0.0, g.bump(weave, 0.6, 0.003))


# ---------- the blade ----------
def blade(iron, spikes, glow):
    n = 90
    path = [centre(LEN * i / n) for i in range(n + 1)]
    SK.sweep(iron, path, BLADE_PROFILE, lambda t: (max(hw(LEN * t), 0.004), half_thick(LEN * t)), uv_scale=0.25)
    # the ember bar in the fuller, beside the spine, a hair proud of both faces, pointed at both ends
    s0, s1, m = 0.5, 3.45, 44
    gp, gs = [], []
    for i in range(m + 1):
        f = i / m
        s = s0 + (s1 - s0) * f
        end = min(1.0, f / 0.07, (1 - f) / 0.14)
        gp.append(centre(s) + side0(s) * (0.4 * hw(s)))
        gs.append((0.042 * (1 - 0.4 * f) * (0.25 + 0.75 * end), (half_thick(s) * 0.88 + 0.011) * (0.2 + 0.8 * end)))
    SK.sweep(glow, gp, SK.hex_profile(0.62), lambda t: gs[min(m, int(round(t * m)))], uv_scale=1.0)
    # the serrated back: nine hooked spines, uneven, leaning toward the hilt
    stations = [(1.25, 0.19), (1.6, 0.13), (1.98, 0.22), (2.35, 0.12), (2.75, 0.2), (3.1, 0.1), (3.45, 0.17), (3.78, 0.09), (4.05, 0.1)]
    for s, ln in stations:
        sd = side0(s)
        base = spine(s) - sd * 0.05
        lean = math.radians(38 + 8 * math.sin(s * 5))
        d = sd * math.cos(lean) + V((0, 0, 1)) * math.sin(lean)
        mid = base + d * ln * 0.55 + V((0, 0, 0.012))
        tip = base + d * ln + V((0, 0, 0.07 * ln / 0.2))
        wdt = 0.04 + 0.35 * ln * 0.25
        SK.sweep(spikes, [base, mid, tip], [(1, 0), (0, 1), (-1, 0), (0, -1)], lambda t, wdt=wdt: (wdt * (1 - t) ** 0.85 + 0.003, 0.046 * (1 - t) ** 0.8 + 0.003), uv_scale=2.0)


# ---------- the beast's head ----------
# The head is turned so the player sees it in profile from above, the way the sword's flat is seen: its forward is -Z, its
# dorsal (up) side is +X, so the jaws open sideways round the blade (upper jaw on the spine side, lower jaw on the edge side)
# and its width is along Y. hp(f, u, w): f forward from the head's back, u toward its dorsal side, w sideways.
HEAD_BACK = -0.58


def hp(f, u, w=0.0):
    return V((u, w, HEAD_BACK - f))


# The maw: a wide, flat cup round the blade's root, open toward the tip, lined in crimson, two rows of fangs on its rim, the upper
# row hanging over the blade's top flat and the lower row rising under its bottom flat, their tips a hair clear of the steel. From
# above it is a gaping toothed mouth biting the blade, from the side a jaw: nothing in it can be read as a face.
FS = 0.78                              # the cup's length scale
SX, SY = 1.45, 0.62                    # wide along the blade's width, flat along its thickness
BACK = [(0.01, 0.0), (0.15, 0.0), (0.26, 0.14), (0.38, 0.4), (0.44, 0.56), (0.36, 0.56), (0.31, 0.42), (0.01, 0.36)]      # the skull: a full ring
FRONT = [(0.335, 0.36), (0.46, 0.75), (0.5, 1.1), (0.52, 1.36), (0.54, 1.44), (0.47, 1.4), (0.45, 1.1), (0.41, 0.75), (0.34, 0.46)]    # one jaw's shell


def head(iron, fang, tusk):
    SK.revolve(iron, [(r, HEAD_BACK - f * FS) for r, f in BACK], n=32, sx=SX, sy=SY)
    front = [(r, HEAD_BACK - f * FS) for r, f in FRONT]
    for lo, hi_ in ((math.radians(12), math.radians(168)), (math.radians(192), math.radians(348))):     # the upper jaw and the lower
        SK.revolve(iron, front, n=22, sx=SX, sy=SY, a0=lo, a1=hi_)
    rim_z = HEAD_BACK - 1.4 * FS
    lip = 0.5
    # the fangs on the rim: an upper row above the blade, a lower row below it, alternating long and short; and a tusk-tooth at each corner
    spots = [(a, 1) for a in (28, 48, 68, 90, 112, 132, 152)] + [(a, -1) for a in (208, 230, 252, 270, 288, 310, 332)]
    for k, (deg, sgn) in enumerate(spots):
        a = math.radians(deg)
        big = k % 2 == 0
        ln = (0.52 if sgn > 0 else 0.4) * (1.0 if big else 0.68) * (0.9 + 0.2 * ((k * 5) % 4) / 3)
        if deg in (68, 90, 112, 252, 270, 288):
            ln *= 1.32                                    # the canines, longest at the middle of each jaw
        base = V((lip * SX * math.cos(a), lip * SY * math.sin(a), rim_z + 0.04))
        tip = V((base.x * 0.86, sgn * 0.1, rim_z - ln))
        SK.spike(fang, base, tip, 0.056 if big else 0.04, sides=6, curve=(0.0, -sgn * 0.05, 0.03), belly=0.12)
    # a crest of three spines down the cup's top, and swept spines at its corners, leaning back toward the grip
    for f, h in ((0.45, 0.3), (0.75, 0.24), (1.05, 0.18)):
        z0 = HEAD_BACK - f * FS
        SK.spike(iron, V((0, 0.2, z0)), V((0, 0.2 + h, z0 + 0.14 + 0.35 * h)), 0.06, sides=4, curve=(0, 0.03, 0.03))
    for sx in (1, -1):
        for f, ln in ((0.55, 0.36), (0.95, 0.28)):
            z0 = HEAD_BACK - f * FS
            SK.spike(iron, V((sx * 0.62, 0.0, z0)), V((sx * (0.62 + 0.3 * ln / 0.36 + 0.2), 0.04, z0 + 0.28 * ln / 0.36)), 0.055, sides=4, curve=(sx * 0.02, 0.02, 0.0))
    # the tusks: from the cup's corners out along the blade's width and forward, the cross-guard
    for sx in (1, -1):
        path = [V((sx * 0.62, 0.0, HEAD_BACK - 0.34)), V((sx * 0.95, 0.0, HEAD_BACK - 0.34)), V((sx * 1.2, 0.04, HEAD_BACK - 0.5)), V((sx * 1.32, 0.08, HEAD_BACK - 0.85)), V((sx * 1.24, 0.12, HEAD_BACK - 1.2))]
        pts = W.catmull([tuple(p) for p in path], 6)
        SK.sweep(tusk, [V(p) for p in pts], SK.lens_profile(7), lambda t: (0.09 * (1 - t) ** 0.7 + 0.003, 0.082 * (1 - t) ** 0.7 + 0.003), uv_scale=1.0)


# ---------- the grip, pommel and cloth ----------
GRIP_Z0, GRIP_Z1 = -0.75, 0.86


def grip(core, cloth, iron):
    n = 24
    path = [V((0, 0, GRIP_Z0 + (GRIP_Z1 - GRIP_Z0) * i / n)) for i in range(n + 1)]
    SK.sweep(core, path, SK.lens_profile(8), lambda t: (0.104 + 0.01 * math.sin(math.pi * t),) * 2, uv_scale=1.0)
    # cloth wound on: two layers of torn strips crossing, thicker at the ends
    z0, z1 = -0.62, 0.8
    for hand, rad, turns, ph in ((1, 0.112, 5.2, 0.2), (-1, 0.122, 4.6, 1.6)):
        m = 120
        pts = []
        for i in range(m + 1):
            f = i / m
            a = ph + hand * TAU * turns * f
            r = rad + 0.012 * math.sin(math.pi * f) + 0.004 * math.sin(f * 40)
            pts.append(V((r * math.cos(a), r * math.sin(a), z0 + (z1 - z0) * f)))

        def radial(i, p):
            return V((p[i].x, p[i].y, 0.0))
        SK.sweep(cloth, pts, [(1, 1), (1, -1), (-1, -1), (-1, 1)], lambda t: (0.085 * (0.9 + 0.2 * math.sin(t * 17)), 0.009), up=radial, uv_scale=2.0)
    # an iron collar at the head's back and one under the pommel
    SK.sweep(iron, [V((0, 0, -0.66)), V((0, 0, -0.6)), V((0, 0, -0.54))], SK.bar_profile(), lambda t: (0.15, 0.15), uv_scale=1.0)
    SK.sweep(iron, [V((0, 0, 0.78)), V((0, 0, 0.84)), V((0, 0, 0.9))], SK.bar_profile(), lambda t: (0.14, 0.14), uv_scale=1.0)


def pommel(iron):
    SK.sweep(iron, [V((0, 0, 0.86)), V((0, 0, 0.98)), V((0, 0, 1.1))], SK.lens_profile(8, 0.2), lambda t: (0.15 * (1 - t ** 2) + 0.03,) * 2, uv_scale=1.0)
    for k in range(3):                      # three short claws curling back round the cap
        a = TAU * k / 3 + 0.5
        c, s = math.cos(a), math.sin(a)
        SK.spike(iron, V((0.12 * c, 0.12 * s, 0.93)), V((0.2 * c, 0.2 * s, 1.17)), 0.04, sides=4, curve=(0.05 * c, 0.05 * s, 0.02))
    SK.torus(iron, (0, 0, 1.17), (1, 0, 0), 0.06, 0.018, n=24, sides=6)


def rags(cloth_hi):
    """Three torn rags tied to the pommel's ring, hanging and trailing back."""
    specs = [((0.0, 0.0, 1.17), [(0.02, -0.25, 0.28), (0.1, -0.7, 0.45), (0.0, -1.15, 0.5)], 0.18, 1),
             ((0.0, 0.0, 1.17), [(-0.08, -0.2, 0.34), (-0.2, -0.55, 0.6), (-0.1, -0.85, 0.8)], 0.14, 2),
             ((0.0, 0.0, 1.17), [(0.1, -0.1, 0.4), (0.3, -0.35, 0.7), (0.34, -0.7, 0.85)], 0.12, 3)]
    for root, offs, wd, seed in specs:
        r = V(root)
        pts = [r] + [r + V(o) for o in offs]
        curve = W.catmull([tuple(p) for p in pts], 6)

        def width(f, wd=wd):
            return wd * (1.0 - 0.3 * f)

        def rag(f, k, seed=seed):
            # torn teeth along the last stretch: alternate rows lose an edge column, so every piece stays joined
            row = int(f * 40) + seed
            return (f > 0.78 and k == 2 and row % 2 == 0) or (f > 0.9 and k == 0 and row % 2 == 1)
        SK.cloth(cloth_hi, curve, width, mat=0, up=(1, 0, 0), across=3, wave=0.05, wave_turns=2.0, rag=rag, flutter=0.04, seed=seed, uv_len=1.0)


# ---------- the weapon ----------
def build():
    SK.fresh()
    root = W.collection("SecretDemonicHi")
    W.clear_collection(root)
    ironhi, spikes, glow, headhi, fanghi, tuskhi, core, clothhi, rag_hi = (Hm.Hi() for _ in range(9))
    blade(ironhi, spikes, glow)
    head(headhi, fanghi, tuskhi)
    grip(core, clothhi, headhi)
    pommel(headhi)
    rags(rag_hi)
    objs = []

    def piece(name, hi, mats, **props):
        o = hi.object(name, root, mats, smooth=props.pop("smooth", True))
        for k, v in props.items():
            o[k] = v
        objs.append(o)
        return o
    beast = mat_beast_iron()
    piece("BM_Blade", ironhi, [mat_saber_iron()], target=1050)
    piece("BM_Spikes", spikes, [beast], target=330)
    piece("BM_Head", headhi, [beast], target=1050)
    piece("BM_Fangs", fanghi, [mat_fang()], target=380)
    piece("BM_Tusks", tuskhi, [mat_fang("BmTusk", root_heat=False)], target=220)
    piece("BM_Core", core, [beast], target=100)
    piece("BM_Wrap", clothhi, [mat_cloth()], target=380)
    r = piece("BM_Rags", rag_hi, [mat_cloth("BmRagCloth", (0.12, 0.006, 0.01), (0.5, 0.04, 0.04))])
    SK.thicken(r, 0.012)
    r["target"] = 260
    glow_obj = glow.object("BM_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)
    return objs, {GLOW: ("Glow", [glow_obj])}, root


def hilt_tip():
    return (0.0, 0.0, HEAD_BACK - 1.4 * FS - 0.52), (TIP_POINT.x, 0.0, TIP_POINT.z)


CLOSE = (("front34", (0.0, 0.1, -1.2), 3.0), ("top", (0.0, 0.0, -1.2), 3.0), ("edge_r", (0.0, 0.1, -1.2), 3.0), ("back34", (0.0, 0.0, 0.5), 3.2))


def export():
    objs, glow, root = build()
    hilt, tip = hilt_tip()
    return objs, glow, root, SK.export(WEAPON_ID, "Sword", "secret_demonic.py", objs, glow, root, hilt, tip, budget=3900)


if __name__ == "__main__":
    stage = (sys.argv[sys.argv.index("--") + 1:] or ["all"])[0] if "--" in sys.argv else "all"
    import secret_review as R
    R.run(sys.modules[__name__], stage)
