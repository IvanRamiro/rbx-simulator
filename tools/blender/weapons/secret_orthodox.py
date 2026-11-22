"""The Orthodox faction's secret weapon (run inside Blender, headless): the Azure Oath Sword, id SecretOrthodox.

    blender -b --factory-startup --python tools/blender/weapons/secret_orthodox.py -- clay|export|review|all

Idea: the calm of a mountain sect. A straight, double-edged longsword of white-silver steel (brushed flats, a wavy temper line down
each side, polished bevels); down its middle a bar of azure light (the "Glow" piece, Neon, saturated azure: Neon whitens pale
colours) framed by two silver rails so it reads as a lit fuller. Its guard is two mountains: each side a plate cut to a skyline,
two smaller plates stacked on it (ridge behind ridge, like a tsuba), silver with snow-white summits, a sapphire (a domed rounded
rectangle, never a round or an almond) in a bezel on the middle terrace, and a thin line of the same azure light traced along
the skyline. The grip is white pebbled ray-skin wrapped in azure silk in the Japanese diamond (hishi) wrap, silver collars at both
ends. The pommel is a small silver peak with a ring under its tip; from the ring hangs a norigae (the Korean ornament): an azure
cord, a knot of three crossing cord bands, a short cord, a white jade pendant cut as a small peak, a silver cap and a short
tassel of azure and white silk.

Parts and contacts (Roblox studs from the grip, point toward -Z):
  blade       z -0.9 to -5.1, runs into the guard's centre block (overlap), habaki collar at its foot;
  guard       centre block z -0.76 to -1.10; each side three stacked plates (z -0.80 to -2.08, out to 1.14), their inner edge inside the block;
  gems        on the middle terrace, in bezels that sit on the plate;
  grip        z -0.80 (inside the block) to 0.84, fuchi collar at the block's back, kashira collar at the pommel's foot;
  pommel      z 0.80 to 1.12, the ring's front edge overlaps its tip, the cord starts inside the ring;
  norigae     cord, knot, cord, jade (a ring of cord round its neck), cap, tassel threads rooted in the cap.
The hand closes on z -0.40..0.40; the guard (-0.76) and the pommel (0.80) stand clear of it.

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
WEAPON_ID = "SecretOrthodox"
COMPARE = ("Sword6", 2.4)     # the realm weapon it is judged beside
GLOW = "1e8cff"             # saturated azure
BLADE_Z0, HILT, TIP = -0.90, -1.10, -5.10


# ---------- materials ----------
def _u(g):
    u, v, _ = g.sep(g.coords("UV"))
    return u, v


def smooth(g, x, a, b):
    return SK.smooth(g, x, a, b)


def mat_blade(name="AzBladeSteel"):
    """White-silver steel: brushed flats with a wavy temper line (hamon) running down each side, the edge side of it
    polished bright; azure light spilling onto the steel round the fuller; polished edge bevels."""
    g = Hm._Graph(name)
    mp = g.n("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (90.0, 2.5, 90.0)         # streaks run along Blender Y, the blade's length
    g.link(g.coords(), mp.inputs["Vector"])
    streak = WK._noise(g, 1.0, 3.0, coords=mp.outputs[0])
    wob = WK._noise(g, 5.0, 2.0)
    u, v = _u(g)
    top = g.math("MULTIPLY", g.math("GREATER_THAN", u, 0.2), g.math("LESS_THAN", u, 0.3))
    bot = g.math("MULTIPLY", g.math("GREATER_THAN", u, 0.7), g.math("LESS_THAN", u, 0.8))
    flat = g.math("MAXIMUM", top, bot)
    ul = g.math("MULTIPLY", g.math("SUBTRACT", u, g.math("ADD", 0.2, g.math("MULTIPLY", bot, 0.5))), 10.0)
    s = g.math("MULTIPLY", g.math("ABSOLUTE", g.math("SUBTRACT", ul, 0.5)), 2.0)      # 0 on the middle of a flat, 1 at its edge side
    line = g.math("ADD", g.math("ADD", 0.58, g.math("MULTIPLY", g.math("SINE", g.math("MULTIPLY", v, 44.0)), 0.09)),
                  g.math("MULTIPLY", g.math("SUBTRACT", wob, 0.5), 0.25))
    pol = g.math("MAXIMUM", g.math("SUBTRACT", 1.0, flat), smooth(g, g.math("SUBTRACT", s, line), -0.035, 0.035))
    brushed = g.ramp(streak, [(0.3, (0.55, 0.59, 0.66)), (0.7, (0.72, 0.76, 0.83))])
    col = g.mix(pol, brushed, (0.93, 0.95, 0.98))
    spill = g.math("MULTIPLY", g.math("MULTIPLY", smooth(g, g.math("SUBTRACT", 0.26, s), 0.0, 0.26), flat), 0.5)
    col = g.mix(spill, col, (0.35, 0.68, 1.0))
    col = g.ao(col, 0.03, 0.55)
    rough = g.math("ADD", g.math("MULTIPLY", g.math("SUBTRACT", 1.0, pol), 0.2), g.math("ADD", 0.14, g.math("MULTIPLY", streak, 0.08)))
    metal = g.math("ADD", g.math("MULTIPLY", g.math("SUBTRACT", 1.0, pol), -0.14), 0.95)
    return g.finish(col, rough, metal, g.bump(streak, 0.08, 0.002))


def mat_peak_silver(name="AzPeakSilver"):
    """The guard's and pommel's faceted silver: slightly blue and brushed low down, white at the summits (the snow line,
    by height: the guard's peaks reach Blender +Y, the weapon's front)."""
    g = Hm._Graph(name)
    co = g.coords()
    yb = g.sep(co)[1]
    snow = smooth(g, g.math("ADD", yb, g.math("MULTIPLY", g.math("SUBTRACT", WK._noise(g, 6.0, 3.0), 0.5), 0.3)), 1.3, 1.52)
    mp = g.n("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (60.0, 6.0, 60.0)
    g.link(co, mp.inputs["Vector"])
    streak = WK._noise(g, 1.0, 3.0, coords=mp.outputs[0])
    low = g.ramp(streak, [(0.3, (0.4, 0.45, 0.55)), (0.7, (0.6, 0.66, 0.76))])
    col = g.mix(snow, low, (0.95, 0.97, 1.0))
    col = g.ao(col, 0.05, 0.5)
    rough = g.math("ADD", 0.17, g.math("MULTIPLY", streak, 0.12))
    return g.finish(col, rough, 0.88, g.bump(streak, 0.06, 0.003))


def mat_sapphire(name="AzSapphire"):
    """A deep sapphire: cloudy blue depths, polished."""
    g = Hm._Graph(name)
    n = WK._noise(g, 5.0, 4.0, 1.0)
    col = g.ramp(n, [(0.25, (0.004, 0.03, 0.26)), (0.55, (0.02, 0.14, 0.6)), (0.85, (0.1, 0.4, 0.95))])
    return g.finish(g.ao(col, 0.02, 0.6), 0.07, 0.0)


def mat_rayskin(name="AzRaySkin"):
    """Ray-skin (same): a mat of round white pebbles."""
    g = Hm._Graph(name)
    vor = g.n("ShaderNodeTexVoronoi", **{"Scale": 46.0})
    g.link(g.coords(), vor.inputs["Vector"])
    d = vor.outputs["Distance"]
    col = g.ramp(d, [(0.0, (0.98, 0.97, 0.94)), (0.32, (0.92, 0.91, 0.87)), (0.5, (0.55, 0.55, 0.53))])
    col = g.ao(col, 0.03, 0.5)
    return g.finish(col, 0.42, 0.0, g.bump(g.math("SUBTRACT", 1.0, d), 0.7, 0.004))


# ---------- the blade ----------
def half_width(t):
    base = 0.212 * (1 - 0.36 * t)
    return base * (1.0 if t < 0.90 else max(0.0, (1 - t) / 0.10) ** 0.85)


def half_thick(t):
    return (0.062 * (1 - 0.42 * t) + 0.012) * (1.0 if t < 0.90 else 0.25 + 0.75 * max(0.0, (1 - t) / 0.10))


BLADE_PROFILE = [(1, 0), (0.82, 0.5), (0.5, 1), (-0.5, 1), (-0.82, 0.5), (-1, 0), (-0.82, -0.5), (-0.5, -1), (0.5, -1), (0.82, -0.5)]


def t_at(z):
    return (z - BLADE_Z0) / (TIP - BLADE_Z0)


def blade(steel, glow, trim):
    n = 84
    path = [V((0, 0, BLADE_Z0 + (TIP - BLADE_Z0) * i / n)) for i in range(n + 1)]
    SK.sweep(steel, path, BLADE_PROFILE, lambda t: (half_width(t), half_thick(t)), cap_end=True, uv_scale=0.25)
    # the azure bar: a hexagonal rod through the blade's middle, a hair proud of both flats, pointed at both ends
    t0, t1 = 0.075, 0.855
    m = 36
    gp, gs = [], []
    for i in range(m + 1):
        f = i / m
        t = t0 + (t1 - t0) * f
        z = BLADE_Z0 + (TIP - BLADE_Z0) * t
        end = min(1.0, f / 0.09, (1 - f) / 0.16)
        gp.append(V((0, 0, z)))
        gs.append((0.046 * (1 - 0.45 * t) * (0.25 + 0.75 * end), (half_thick(t) + 0.011) * (0.2 + 0.8 * end)))
    SK.sweep(glow, gp, SK.hex_profile(0.62), lambda t: gs[min(m, int(round(t * m)))], uv_scale=1.0)
    # two thin silver rails either side of the bar, top and bottom: the lit fuller's frame
    for side in (1, -1):
        for face in (1, -1):
            rp, rs = [], []
            for i in range(m + 1):
                f = i / m
                t = t0 + (t1 - t0) * f
                z = BLADE_Z0 + (TIP - BLADE_Z0) * t
                end = min(1.0, f / 0.05, (1 - f) / 0.12)
                end = 0.45 + 0.55 * end
                xo = side * (0.046 * (1 - 0.45 * t) + 0.03)
                rp.append(V((xo, face * (half_thick(t) * 0.99), z)))
                rs.append((0.011 * (0.2 + 0.8 * end), 0.0085 * (0.2 + 0.8 * end)))
            SK.sweep(trim, rp, SK.bar_profile(), lambda t, rs=rs: rs[min(m, int(round(t * m)))], uv_scale=1.0)


# ---------- the guard: two mountain peaks ----------
# the guard's right half, as a skyline (x, z): the mountain rising from the blade, its summit, a steep fall to the outer end
OUTLINE = [(0.18, -0.80), (1.14, -0.80), (1.16, -0.96), (0.99, -1.55), (0.84, -2.08), (0.66, -1.64), (0.58, -1.52), (0.40, -1.24), (0.22, -1.08), (0.18, -1.08)]
CENTRE = (0.70, -1.38)


def layer(scale, dx=0.0):
    return [(CENTRE[0] + (x - CENTRE[0]) * scale + dx, CENTRE[1] + (z - CENTRE[1]) * scale) for x, z in OUTLINE]


def guard(metal, gems):
    # the layered mountains, each side a plate cut to the skyline with two smaller plates stacked on it: ridge behind ridge
    for sx in (1, -1):
        for scale, y, half in ((1.0, 0.0, 0.065), (0.8, 0.0, 0.10), (0.52, 0.0, 0.125)):
            pts = layer(scale) if sx > 0 else [(-x, z) for x, z in layer(scale)][::-1]
            SK.plate(metal, pts, y, half)
    # the centre block the blade runs through
    SK.sweep(metal, [V((0, 0, -0.76)), V((0, 0, -0.93)), V((0, 0, -1.10))], SK.bar_profile(), lambda t: (0.30 - 0.03 * t, 0.205 - 0.02 * t), uv_scale=1.0)
    # the habaki, the collar on the blade's foot
    SK.sweep(metal, [V((0, 0, -1.08)), V((0, 0, -1.2)), V((0, 0, -1.3))], SK.lens_profile(8), lambda t: (0.236 - 0.01 * t, 0.088 - 0.008 * t), uv_scale=1.0)


def guard_light(glow):
    """Azure light traced along the middle terrace of each mountain, top and bottom: the same Neon piece as the fuller.
    One ribbon per loop, set into the terrace (a few thousandths proud), its two ends left a hair apart."""
    for sx in (1, -1):
        base = layer(0.66)
        pts = base if sx > 0 else [(-x, z) for x, z in base][::-1]
        loop = pts[1:9] if sx > 0 else pts[len(pts) - 9:len(pts) - 1]      # the skyline only, not the back edge
        for face in (1, -1):
            if face > 0:
                SK.strip(glow, loop, 0.1055, 0.096, 0.011)
            else:
                SK.strip(glow, loop, -0.096, -0.1055, 0.011)


def sapphires(gems):
    """A stone on the top and bottom of the middle ridge of each side."""
    for sx in (1, -1):
        for face in (1, -1):
            c = V((sx * 0.64, face * 0.126, -1.50))
            SK.jewel(gems, c, (0, face, 0), (sx * 0.2, 0, -1.0), 0.30, 0.17, 0.05, mat=0, bezel=1, rounded=0.45)


# ---------- the grip ----------
GRIP_Z0, GRIP_Z1 = -0.80, 0.84


def grip(skin, wrap, metal):
    n = 30
    path = [V((0, 0, GRIP_Z0 + (GRIP_Z1 - GRIP_Z0) * i / n)) for i in range(n + 1)]
    SK.sweep(skin, path, SK.lens_profile(8), lambda t: (0.104 + 0.012 * math.sin(math.pi * t), 0.097 + 0.012 * math.sin(math.pi * t)), uv_scale=1.0)
    # the hishi wrap: two flat bands crossing, wound the opposite ways
    z0, z1 = -0.66, 0.78
    turns = 6.0
    for hand, rad in ((1, 0.108), (-1, 0.116)):
        m = 150
        pts = []
        for i in range(m + 1):
            f = i / m
            a = hand * TAU * turns * f + (0.0 if hand > 0 else 0.4)
            r = rad + 0.012 * math.sin(math.pi * (z0 + (z1 - z0) * f - GRIP_Z0) / (GRIP_Z1 - GRIP_Z0))
            pts.append(V((r * math.cos(a), r * math.sin(a), z0 + (z1 - z0) * f)))

        def radial(i, p):
            return V((p[i].x, p[i].y, 0.0))
        SK.sweep(wrap, pts, [(1, 1), (1, -1), (-1, -1), (-1, 1)], lambda t: (0.056, 0.0105), up=radial, cap_start=True, cap_end=True, uv_scale=2.0)
    # silver collars: fuchi at the guard's back, kashira under the pommel
    SK.sweep(metal, [V((0, 0, -0.78)), V((0, 0, -0.72)), V((0, 0, -0.64))], SK.bar_profile(), lambda t: (0.14 - 0.01 * t, 0.134 - 0.01 * t), uv_scale=1.0)
    SK.sweep(metal, [V((0, 0, 0.76)), V((0, 0, 0.83)), V((0, 0, 0.9))], SK.bar_profile(), lambda t: (0.13 + 0.01 * t, 0.126 + 0.01 * t), uv_scale=1.0)


def pommel(metal):
    path = [V((0, 0, 0.88)), V((0, 0, 0.98)), V((0, 0, 1.08))]
    SK.sweep(metal, path, SK.hex_profile(0.3), lambda t: (0.14 * (1 - t) ** 0.8 + 0.004, 0.125 * (1 - t) ** 0.8 + 0.004), uv_scale=1.0)
    # the ring under its tip: its plane is the weapon's Y-Z plane, so a cord hangs through it
    SK.torus(metal, (0, 0, 1.135), (1, 0, 0), 0.058, 0.017, n=24, sides=6)


# ---------- the norigae ----------
KNOT = V((0.0, -0.40, 1.38))
JADE = V((0.0, -0.70, 1.40))


def norigae(cord, white, jade, metal, tassel_blue, tassel_white):
    # a cord from inside the ring down to the knot
    SK.strand(cord, [V((0, 0.0, 1.135)), V((0, -0.05, 1.25)), V((0, -0.18, 1.34)), KNOT + V((0, 0.03, 0.0))], 0.04, turns=5, sides=5, per=5)
    # the knot: a white core held by three crossing bands of azure cord
    WK.sphere(white, KNOT, 0.062, sides=12)
    for k in range(3):
        a = TAU * k / 3
        nrm = V((math.cos(a) * 0.9, 0.5, math.sin(a) * 0.9))
        SK.torus(cord, KNOT, nrm, 0.078, 0.019, n=28, sides=6)
    # a short cord to the jade, tied in a loop round its neck
    SK.strand(cord, [KNOT - V((0, 0.05, 0)), KNOT - V((0, 0.12, 0)), JADE + V((0, 0.17, 0))], 0.036, turns=3, sides=5, per=4)
    SK.torus(cord, JADE + V((0, 0.14, 0)), (0, 0, 1), 0.04, 0.014, n=18, sides=5)
    # the pendant: a small white jade peak, chamfered, with a hole through its neck
    outline = [(0.0, 1.0), (0.3, 0.52), (0.8, -0.55), (0.6, -0.9), (-0.6, -0.9), (-0.8, -0.55), (-0.3, 0.52)]
    SK.sweep(jade, [JADE + V((0, 0, 0.036)), JADE + V((0, 0, -0.036))], outline, lambda t: (0.125, 0.15), up=(0, 1, 0), uv_scale=3.0)
    # silver cap and the tassel
    cap_y = JADE.y - 0.175
    SK.sweep(metal, [V((0, cap_y + 0.045, JADE.z)), V((0, cap_y - 0.02, JADE.z)), V((0, cap_y - 0.07, JADE.z))], SK.bar_profile(), lambda t: (0.055 - 0.015 * t, 0.055 - 0.015 * t), up=(0, 0, 1), uv_scale=1.0)
    n = 10
    for k in range(n):
        a = TAU * k / n + 0.2 * (k % 3)
        hi = tassel_blue if k % 3 else tassel_white
        r0, r1 = 0.046, 0.085 + 0.012 * (k % 4)
        ln = 0.7 + 0.08 * ((k * 5) % 4) / 3
        pts = [V((r0 * math.cos(a), cap_y - 0.03, JADE.z + r0 * math.sin(a))),
               V(((r0 + r1) / 2 * math.cos(a), cap_y - 0.03 - ln * 0.5, JADE.z + (r0 + r1) / 2 * math.sin(a) + 0.01 * (k % 3))),
               V((r1 * math.cos(a), cap_y - 0.03 - ln, JADE.z + r1 * math.sin(a) + 0.03))]
        Hm.htube(hi, pts, lambda t: 0.019 * (1 - 0.55 * t), sides=4, per=3, uv_scale=4.0, tip=True, wobble=0.0)


# ---------- the weapon ----------
def build():
    SK.fresh()
    root = W.collection("SecretOrthodoxHi")
    W.clear_collection(root)
    steel, glow, trim = Hm.Hi(), Hm.Hi(), Hm.Hi()
    blade(steel, glow, trim)
    metal, gems, skin, wrap = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    guard(metal, gems)
    guard_light(glow)
    sapphires(gems)
    grip(skin, wrap, metal)
    pommel(metal)
    cord, white, jade, tblue, twhite, norimetal = (Hm.Hi() for _ in range(6))
    norigae(cord, white, jade, norimetal, tblue, twhite)
    m_steel, m_peak, m_sapph = mat_blade(), mat_peak_silver(), mat_sapphire()
    blue_cord = WK.mat_cord("AzAzureCord", (0.01, 0.12, 0.42), (0.1, 0.48, 0.95))
    white_cord = WK.mat_cord("AzWhiteSilk", (0.55, 0.57, 0.6), (0.93, 0.94, 0.96))
    objs = []

    def piece(name, hi, mats, **props):
        o = hi.object(name, root, mats, smooth=props.pop("smooth", True))
        for k, v in props.items():
            o[k] = v
        objs.append(o)
        return o
    piece("AO_Blade", steel, [m_steel], target=760)
    piece("AO_Rails", trim, [mat_peak_silver("AzRailSilver")], target=120)
    o = piece("AO_Guard", metal, [m_peak], smooth=False, planar=4.0, target=1100)
    SK.bevel(o, 0.014, 2, 40)
    piece("AO_Gems", gems, [m_sapph, m_peak], target=220)
    piece("AO_Skin", skin, [mat_rayskin()], target=160)
    piece("AO_Wrap", wrap, [blue_cord], target=520)
    piece("AO_Cord", cord, [blue_cord], target=150)
    piece("AO_Knotcore", white, [white_cord], target=80)
    piece("AO_Jade", jade, [WK.mat_white_jade("AzJade")], smooth=False, planar=3.0, target=140)
    piece("AO_TasselBlue", tblue, [blue_cord], target=170)
    piece("AO_TasselWhite", twhite, [white_cord], target=110)
    piece("AO_Cap", norimetal, [m_peak], smooth=False, planar=4.0, target=80)
    glow_obj = glow.object("AO_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)
    return objs, {GLOW: ("Glow", [glow_obj])}, root


def hilt_tip():
    return (0.0, 0.0, HILT), (0.0, 0.0, TIP)


def export():
    objs, glow, root = build()
    hilt, tip = hilt_tip()
    return objs, glow, root, SK.export(WEAPON_ID, "Sword", "secret_orthodox.py", objs, glow, root, hilt, tip, budget=3700)


if __name__ == "__main__":
    import secret_lab as L
    stage = (sys.argv[sys.argv.index("--") + 1:] or ["all"])[0] if "--" in sys.argv else "all"
    import secret_review as R
    R.run(sys.modules[__name__], stage)
