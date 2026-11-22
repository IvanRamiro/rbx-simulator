"""The Unorthodox faction's secret weapon (run inside Blender, headless): the Stormhook Spear, id SecretUnorthodox.

    blender -b --factory-startup --python tools/blender/weapons/secret_unorthodox.py -- clay|export|review|all

Idea: a weapon that follows no rule. Lopsided on purpose, patched and weathered, sharp where it counts.
- The head is a crescent hook-blade of teal-green steel (flowing forge-wave pattern, a polished edge) that bows out to one side
  and curls back until its point returns toward the shaft's line; its cutting edge is the inside of the curve and runs with a
  copper-orange line of light (the "Glow" piece, Neon, saturated orange). A smaller counter-hook leaves the same socket on the
  other side, lower, and curls forward the other way. The bay between them is open.
- The socket is teal steel bound in copper: three raised copper bands, a copper wire spiralled between them, rivets.
- The shaft is weathered wood stained forest-teal. Hemp rope is wound round the grip, tied behind the socket (it holds the
  streamer, its ends hang), and turned loosely near the butt. Three copper rings sit on the shaft, slightly tilted, one of them
  split, worn green in the hollows. A copper cap closes the butt.
- A patchwork cloth streamer, stitched from linen, forest teal, rust, faded indigo and ochre, flies back from the tie in a wave,
  its end torn into a fork.

Parts and contacts (studs from the grip, point toward -Z; the hand closes on z -0.4..0.4, on the rope wrap):
  shaft       z 3.50 to -3.95, runs up inside the socket (overlap);
  socket      z -2.95 to -4.12, the shaft goes in; both hooks' roots go into its mouth (overlap);
  main hook   root z -3.80 (inside the socket) to the point at (0.16, -6.52); counter-hook root z -3.85 to (-0.30, -5.62);
  rope        grip wrap z -0.90 to 0.80 (sunk into the wood), tie z -2.92 to -2.66, loose turns z 2.55 to 2.75;
  rings       three bands sunk into the wood, tilted; streamer rooted under the tie; butt cap z 3.38 to 3.88.

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
WEAPON_ID = "SecretUnorthodox"
COMPARE = ("Spear6", 2.6)
GLOW = "ff7418"             # saturated copper-orange
BUTT, SHAFT_END = 3.50, -3.95
HILT, POINT = -4.12, (0.384, -6.74)
SHAFT_R = 0.135


# ---------- materials ----------
def smooth(g, x, a, b):
    return g.bw(g.ramp(x, [(a, (0, 0, 0)), (b, (1, 1, 1))]))


def mat_teal_steel(name="StTealSteel"):
    """Teal-green steel with a flowing forge-wave pattern (rings round the crescent's centre, distorted), a darker hammered
    back and a bright polished edge. UV u runs round the blade's section: the spine faces are u 0..0.125 and 0.875..1,
    the edge bevels 0.375..0.625."""
    g = Hm._Graph(name)
    mp = g.n("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (-1.0, -5.2, 0.0)       # the crescent's centre, in Blender axes
    g.link(g.coords(), mp.inputs["Vector"])
    wave = g.n("ShaderNodeTexWave", wave_type="RINGS", rings_direction="Z", **{"Scale": 2.0, "Distortion": 9.0, "Detail": 4.0, "Detail Scale": 2.2, "Detail Roughness": 0.7})
    g.link(mp.outputs[0], wave.inputs["Vector"])
    fine = WK._noise(g, 38.0, 4.0)
    u, _ = _u(g)
    edge = g.bw(g.ramp(u, [(0.34, (0, 0, 0)), (0.4, (1, 1, 1)), (0.6, (1, 1, 1)), (0.66, (0, 0, 0))]))
    back = g.math("MAXIMUM", g.math("LESS_THAN", u, 0.15), g.math("GREATER_THAN", u, 0.85))
    pat = g.math("ADD", g.math("MULTIPLY", wave.outputs["Fac"], 0.55), g.math("MULTIPLY", fine, 0.45))
    col = g.ramp(pat, [(0.25, (0.045, 0.16, 0.145)), (0.5, (0.09, 0.28, 0.25)), (0.78, (0.2, 0.45, 0.4))])
    col = g.mix(g.math("MULTIPLY", back, 0.5), col, (0.02, 0.07, 0.07))
    col = g.mix(edge, col, (0.62, 0.86, 0.78))
    col = g.ao(col, 0.04, 0.5)
    rough = g.math("ADD", g.math("MULTIPLY", g.math("SUBTRACT", 1.0, edge), 0.16), g.math("ADD", 0.14, g.math("MULTIPLY", fine, 0.12)))
    metal = g.math("ADD", g.math("MULTIPLY", g.math("SUBTRACT", 1.0, edge), -0.1), 0.92)
    return g.finish(col, rough, metal, g.bump(g.math("ADD", pat, fine), 0.1, 0.003))


def _u(g):
    u, v, _ = g.sep(g.coords("UV"))
    return u, v


def mat_copper(name="StCopper"):
    """Worn copper: warm metal on the raised parts, verdigris settled in the hollows (ambient occlusion turned to patina)."""
    g = Hm._Graph(name)
    co = g.coords()
    n = WK._noise(g, 16.0, 5.0)
    col = g.ramp(n, [(0.3, (0.5, 0.2, 0.09)), (0.7, (0.82, 0.42, 0.24))])
    ao = g.n("ShaderNodeAmbientOcclusion", samples=16, only_local=True)
    ao.inputs["Distance"].default_value = 0.06
    patina = g.math("MINIMUM", g.math("MULTIPLY", g.math("POWER", g.math("SUBTRACT", 1.0, ao.outputs["AO"], clamp=True), 0.7), 1.6), 1.0)
    patina = g.math("MULTIPLY", patina, g.math("ADD", 0.5, n))
    col = g.mix(g.math("MINIMUM", patina, 1.0), col, (0.1, 0.36, 0.28))
    metal = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.math("MINIMUM", patina, 1.0)), 0.85)
    rough = g.math("ADD", 0.32, g.math("MULTIPLY", patina, 0.4))
    return g.finish(col, rough, metal, g.bump(n, 0.12, 0.004))


def mat_wood(name="StWood"):
    """Weathered wood stained forest-teal, grain running along the shaft (Blender Y)."""
    g = Hm._Graph(name)
    mp = g.n("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (30.0, 1.5, 30.0)
    g.link(g.coords(), mp.inputs["Vector"])
    grain = WK._noise(g, 1.0, 5.0, 0.4, coords=mp.outputs[0])
    blot = WK._noise(g, 3.0, 3.0)
    col = g.ramp(g.math("ADD", g.math("MULTIPLY", grain, 0.7), g.math("MULTIPLY", blot, 0.3)), [(0.3, (0.04, 0.075, 0.07)), (0.7, (0.12, 0.2, 0.17))])
    col = g.ao(col, 0.05, 0.4)
    return g.finish(col, 0.62, 0.0, g.bump(grain, 0.3, 0.004))


def mat_patch(name="StPatchwork"):
    """Patchwork: cloth patches, each its own colour, with a fine weave, stitched along their seams (UV u across the strip,
    v along it in studs)."""
    g = Hm._Graph(name)
    u, v = _u(g)
    wob = WK._noise(g, 2.2, 3.0)
    pv = g.math("ADD", g.math("MULTIPLY", v, 1.8), g.math("MULTIPLY", g.math("SUBTRACT", wob, 0.5), 1.1))     # a patch every 0.55 stud, uneven
    pu = g.math("ADD", g.math("MULTIPLY", u, 2.0), g.math("MULTIPLY", g.math("SUBTRACT", WK._noise(g, 3.1, 2.0), 0.5), 0.9))
    cell = g.math("ADD", g.math("FLOOR", pv), g.math("MULTIPLY", g.math("FLOOR", pu), 3.0))
    rnd = g.math("FRACT", g.math("MULTIPLY", g.math("SINE", g.math("MULTIPLY", cell, 12.9898)), 43758.5453))
    pal = g.ramp(rnd, [(0.0, (0.55, 0.46, 0.3)), (0.17, (0.04, 0.2, 0.17)), (0.34, (0.4, 0.12, 0.05)), (0.5, (0.07, 0.13, 0.24)),
                       (0.67, (0.55, 0.36, 0.08)), (0.84, (0.62, 0.58, 0.46))], interp="CONSTANT")
    cx, cy, _ = g.sep(g.coords())
    weave = g.math("MULTIPLY", g.math("ADD", g.math("ADD", g.math("SINE", g.math("MULTIPLY", cx, 380.0)), g.math("SINE", g.math("MULTIPLY", cy, 380.0))), 2.0), 0.25)
    col = g.mix(g.math("MULTIPLY", weave, 0.6), pal, (0.0, 0.0, 0.0))     # the weave: dark where the threads dip
    near_v = g.math("GREATER_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", g.math("FRACT", pv), 0.5)), 0.47)
    near_u = g.math("GREATER_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", g.math("FRACT", pu), 0.5)), 0.475)
    dash_v = g.math("LESS_THAN", g.math("FRACT", g.math("MULTIPLY", u, 22.0)), 0.55)
    dash_u = g.math("LESS_THAN", g.math("FRACT", g.math("MULTIPLY", v, 40.0)), 0.55)
    stitch = g.math("MAXIMUM", g.math("MULTIPLY", near_v, dash_v), g.math("MULTIPLY", near_u, dash_u))
    col = g.mix(g.math("MULTIPLY", stitch, 0.9), col, (0.1, 0.065, 0.04))
    dirt = WK._noise(g, 6.0, 4.0)
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, dirt), 0.55), col, (0.05, 0.04, 0.03))
    col = g.ao(col, 0.04, 0.5)
    return g.finish(col, 0.88, 0.0, g.bump(weave, 0.5, 0.003))


# ---------- the head ----------
# centre-line (x, z) and half-width of each hook, from its root in the socket to its point; the spine is the outside of
# the curve, the edge the inside
MAIN = [((0.00, -3.80), 0.13), ((0.18, -4.12), 0.17), ((0.55, -4.55), 0.20), ((0.95, -5.05), 0.20), ((1.10, -5.65), 0.16), ((0.92, -6.12), 0.10), ((0.62, -6.46), 0.045), ((0.30, -6.62), 0.004)]
COUNTER = [((-0.02, -3.85), 0.10), ((-0.22, -4.12), 0.12), ((-0.52, -4.45), 0.12), ((-0.68, -4.90), 0.09), ((-0.56, -5.30), 0.05), ((-0.34, -5.52), 0.004)]
XS, ZS, HS = 1.28, 1.04, 1.1          # the sketch's sweep widened, a touch longer, its blades a little broader
MAIN = [((x * XS, -3.8 + (z + 3.8) * ZS), h * HS) for (x, z), h in MAIN]
COUNTER = [((x * XS, -3.8 + (z + 3.8) * ZS), h * HS) for (x, z), h in COUNTER]
HOOK_PROFILE = [(1.0, 0.0), (0.85, 0.75), (0.2, 1.0), (-0.55, 0.35), (-1.0, 0.0), (-0.55, -0.35), (0.2, -1.0), (0.85, -0.75)]


def densify(spec, per=8):
    """Catmull-Rom through a hook's centre-line, with its half-width interpolated alongside."""
    pts = W.catmull([(x, 0.0, z) for (x, z), _ in spec], per)
    hs = []
    n = len(pts)
    for i in range(n):
        f = i / (n - 1) * (len(spec) - 1)
        k = min(int(f), len(spec) - 2)
        hs.append(spec[k][1] + (spec[k + 1][1] - spec[k][1]) * (f - k))
    return [V(p) for p in pts], hs


def hook(steel, spec, spine_side, thick):
    pts, hs = densify(spec)
    prof = HOOK_PROFILE if spine_side > 0 else [(-a, b) for a, b in HOOK_PROFILE]
    n = len(pts)
    SK.sweep(steel, pts, prof, lambda t: (max(hs[min(n - 1, int(round(t * (n - 1))))], 0.003), thick * (1 - 0.75 * t) + 0.004), uv_scale=0.5)
    return pts, hs


def edge_line(glow, pts, hs, spine_side, t0, t1, radius):
    """The glowing line along a hook's cutting edge (the inner side), a hair beyond the steel."""
    n = len(pts)
    out = []
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        t = (b - a).normalized()
        side = t.cross(V((0, 1, 0)))                 # +X when travelling forward: the outside of the main hook
        out.append(pts[i] - side * (spine_side * hs[i] * 0.985))
    i0, i1 = int(t0 * (n - 1)), int(t1 * (n - 1))
    seg = out[i0:i1 + 1:2]
    m = len(seg)
    SK.sweep(glow, seg, [(1, 0), (0, 1), (-1, 0), (0, -1)], lambda t: (radius * min(1.0, t / 0.08 + 0.2, (1 - t) / 0.1 + 0.2), radius * 1.1 * min(1.0, t / 0.08 + 0.2, (1 - t) / 0.1 + 0.2)), uv_scale=1.0)


def head(steel, glow):
    mp, mh = hook(steel, MAIN, 1, 0.085)
    cp, ch = hook(steel, COUNTER, -1, 0.06)
    edge_line(glow, mp, mh, 1, 0.1, 0.97, 0.026)
    edge_line(glow, cp, ch, -1, 0.1, 0.95, 0.02)


# ---------- the socket ----------
SOCK_Z0, SOCK_Z1 = -2.95, -4.12


def sock_r(z):
    f = (z - SOCK_Z0) / (SOCK_Z1 - SOCK_Z0)
    return 0.235 - 0.05 * f


def socket(steel, copper):
    path = [V((0, 0, SOCK_Z0 + (SOCK_Z1 - SOCK_Z0) * i / 10)) for i in range(11)]
    SK.sweep(steel, path, SK.lens_profile(8), lambda t: (sock_r(SOCK_Z0 + (SOCK_Z1 - SOCK_Z0) * t),) * 2, uv_scale=1.0)
    for z in (-3.05, -3.52, -4.04):
        r = sock_r(z) + 0.022
        SK.sweep(copper, [V((0, 0, z + 0.06)), V((0, 0, z)), V((0, 0, z - 0.06))], SK.lens_profile(8, flat=0.35), lambda t, r=r: (r, r), uv_scale=1.0)
        for k in range(5):
            a = TAU * k / 5 + z * 3
            WK.sphere(copper, (math.cos(a) * (r + 0.004), math.sin(a) * (r + 0.004), z), 0.026, sides=8)
    # the copper wire spiralled between the bands
    m = 90
    pts = []
    for i in range(m + 1):
        f = i / m
        z = -3.17 + (-3.9 + 3.17) * f
        r = sock_r(z) + 0.012
        a = TAU * 5.0 * f
        pts.append(V((r * math.cos(a), r * math.sin(a), z)))
    Hm.htube(copper, pts, lambda t: 0.012, sides=5, per=1, uv_scale=6.0, tip=True, wobble=0.0)


# ---------- the shaft, rope, rings, butt ----------
def shaft(wood, copper):
    Hm.htube(wood, [V((0, 0, BUTT)), V((0, 0, 0)), V((0, 0, SHAFT_END + 0.15))], lambda t: SHAFT_R, sides=14, per=40, uv_scale=1.0, tip=False, wobble=0.0)
    # the copper cap on the butt, with a short point
    SK.sweep(copper, [V((0, 0, BUTT - 0.12)), V((0, 0, BUTT + 0.05)), V((0, 0, BUTT + 0.2)), V((0, 0, BUTT + 0.38))], SK.lens_profile(8),
             lambda t: (0.152 * (1 - t ** 3) * (1 - 0.15 * t) + 0.01,) * 2, uv_scale=1.0)


def rope_wrap(hi, z0, z1, turns, phase=0.0, radius=SHAFT_R + 0.03, tube=0.04, hand=1, ends_loose=False):
    m = max(40, int(turns * 22))
    pts = []
    for i in range(m + 1):
        f = i / m
        a = phase + hand * TAU * turns * f
        pts.append(V((radius * math.cos(a), radius * math.sin(a), z0 + (z1 - z0) * f)))
    Hm.htube(hi, pts, lambda t: tube, sides=6, per=1, uv_scale=6.0, tip=True, wobble=0.0)
    return pts


def rope_tail(hi, start, drop, sway, tube=0.034):
    """A rope end hanging from `start`: down by `drop` (Roblox -Y), swaying by `sway` (a vector), thinning to a frayed tip."""
    s = V(start)
    pts = [s, s + V((0, -drop * 0.25, 0)) + sway * 0.25, s + V((0, -drop * 0.6, 0)) + sway * 0.7, s + V((0, -drop, 0)) + sway]
    Hm.htube(hi, pts, lambda t: tube * (1 - 0.45 * t), sides=6, per=5, uv_scale=6.0, tip=True, wobble=0.0)


def rope(hi):
    rope_wrap(hi, -0.90, 0.80, 19.0, 0.3)
    # a second layer of cross turns over the middle of the grip, binding it
    rope_wrap(hi, -0.55, 0.45, 6.0, 1.1, radius=SHAFT_R + 0.062, tube=0.03, hand=-1)
    # the tie behind the socket: tight turns, ends hanging
    pts = rope_wrap(hi, -2.92, -2.66, 3.4, 0.2, tube=0.045)
    rope_tail(hi, pts[-1], 0.55, V((0.08, 0, 0.18)))
    rope_tail(hi, pts[0], 0.4, V((-0.1, 0, -0.1)))
    # loose turns near the butt, one end hanging with a knot
    pts = rope_wrap(hi, 2.55, 2.75, 2.6, 2.0, radius=SHAFT_R + 0.033, tube=0.04)
    rope_tail(hi, pts[-1], 0.7, V((0.0, 0, 0.3)), tube=0.036)
    WK.sphere(hi, pts[-1] + V((0.0, -0.58, 0.25)), 0.05, sides=8)


def rings(copper):
    """Three copper rings, loose and a little tilted, sunk into the wood so they touch it; one is split."""
    for z, tilt_x, tilt_y, arc in ((-1.62, 0.12, 0.05, TAU), (-1.2, -0.08, 0.14, TAU), (1.95, 0.1, -0.12, TAU * 0.9)):
        nrm = V((tilt_y, tilt_x, -1.0)).normalized()
        SK.torus(copper, (0, 0, z), nrm, SHAFT_R + 0.03, 0.046, n=28, sides=8, arc=arc, start=0.5)


# ---------- the streamer ----------
def streamer(cloth_hi):
    path = [V((-0.16, 0.02, -2.8)), V((-0.55, 0.1, -2.3)), V((-0.92, 0.04, -1.7)), V((-1.18, -0.06, -0.95)), V((-1.1, 0.06, -0.15)), V((-0.84, 0.16, 0.55)),
            V((-0.62, 0.06, 1.2)), V((-0.5, -0.04, 1.6))]
    pts = W.catmull([tuple(p) for p in path], 6)

    def width(f):
        return 0.40 + 0.16 * math.sin(math.pi * min(1, f * 1.6)) - 0.12 * f

    def rag(f, k):
        return (f > 0.86 and k in (1, 2)) or (f > 0.93 and k == 3 and int(f * 97) % 2 == 0)
    SK.cloth(cloth_hi, pts, width, mat=0, across=4, wave=0.08, wave_turns=2.4, rag=rag, flutter=0.03, seed=3, uv_len=1.0)


# ---------- the weapon ----------
def build():
    SK.fresh()
    root = W.collection("SecretUnorthodoxHi")
    W.clear_collection(root)
    steel, glow, socket_steel, copper, wood, ropehi, clothhi = (Hm.Hi() for _ in range(7))
    head(steel, glow)
    socket(socket_steel, copper)
    shaft(wood, copper)
    rope(ropehi)
    rings(copper)
    streamer(clothhi)
    objs = []

    def piece(name, hi, mats, **props):
        o = hi.object(name, root, mats, smooth=props.pop("smooth", True))
        for k, v in props.items():
            o[k] = v
        objs.append(o)
        return o
    steel_mat = mat_teal_steel()
    piece("SH_Head", steel, [steel_mat], target=1100)
    piece("SH_Socket", socket_steel, [steel_mat], target=240)
    piece("SH_Copper", copper, [mat_copper()], target=700)
    piece("SH_Shaft", wood, [mat_wood()], target=240)
    piece("SH_Rope", ropehi, [WK.mat_cord("StHemp", (0.32, 0.24, 0.12), (0.78, 0.66, 0.42))], target=900)
    cloth_o = piece("SH_Streamer", clothhi, [mat_patch()], smooth=True)
    SK.thicken(cloth_o, 0.012)
    cloth_o["target"] = 420
    glow_obj = glow.object("SH_Glow", root, [WK.K.glow_material(GLOW)], smooth=True)
    return objs, {GLOW: ("Glow", [glow_obj])}, root


def hilt_tip():
    return (0.0, 0.0, HILT), (POINT[0], 0.0, POINT[1])


# close-ups: the head from above and in 3/4, the socket and streamer tie, the butt
CLOSE = (("top", (0.15, 0.0, -5.0), 4.0), ("front34", (0.1, 0.0, -4.8), 4.4), ("back34", (-0.3, 0.0, -3.0), 3.6), ("edge_r", (0.0, 0.0, -4.6), 4.4))


def export():
    objs, glow, root = build()
    hilt, tip = hilt_tip()
    return objs, glow, root, SK.export(WEAPON_ID, "Spear", "secret_unorthodox.py", objs, glow, root, hilt, tip, budget=3900)


if __name__ == "__main__":
    stage = (sys.argv[sys.argv.index("--") + 1:] or ["all"])[0] if "--" in sys.argv else "all"
    import secret_review as R
    R.run(sys.modules[__name__], stage)
