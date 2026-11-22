"""The Unorthodox sword's materials (run inside Blender): procedural shaders on the high-detail pieces, baked to the game mesh's
colour, roughness, metalness and normal maps (secret_kit.bake reads Base Color, BAKE_ROUGH, BAKE_METAL and the Normal input).

Palette (the owner's): blackened and teal-patinated steel with a bright honed edge, copper, bronze and aged brass, bone and linen cord.
Painter values are sRGB (SK.srgb turns them into linear shader colours). Metal reads as metal: metalness is high on every bare metal
and falls to near zero where verdigris or oxide sits on it; a dark patinated steel keeps its metalness (a dark mirror) while the
teal bloom on it is dielectric.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402

import secret_kit as SK  # noqa: E402

Hm, WK = SK.Hm, SK.WK
TAU = math.tau
S = SK.srgb


def _noise3(g, scale, detail=5.0, rough=0.55, dist=0.0, coords=None, w=None):
    n = g.n("ShaderNodeTexNoise", **{"Scale": scale, "Detail": detail, "Roughness": rough, "Distortion": dist})
    g.link(coords if coords is not None else g.coords(), n.inputs["Vector"])
    return n.outputs["Fac"]


def _vec(g, x, y, z):
    c = g.n("ShaderNodeCombineXYZ")
    for sock, val in zip(("X", "Y", "Z"), (x, y, z)):
        if isinstance(val, (int, float)):
            c.inputs[sock].default_value = val
        else:
            g.link(val, c.inputs[sock])
    return c.outputs["Vector"]


def _mulc(g, x, k):
    return g.math("MULTIPLY", x, float(k))


def _lerp(g, fac, a, b):
    """a + (b - a) * fac for numbers."""
    return g.math("ADD", g.math("MULTIPLY", g.math("SUBTRACT", 1.0, fac), a), g.math("MULTIPLY", fac, b))


def _stripes(g, x, count):
    return g.math("ADD", g.math("MULTIPLY", g.math("SINE", g.math("MULTIPLY", x, TAU * count)), 0.5), 0.5)


def _dark_steel(g, u, v, wig, patina_bias=0.0, grain_scale=1.0):
    """The blackened body: forged grain (hada) flowing along the blade, teal patina collecting in its valleys.
    u: the across coordinate (0 at the end of the edge bevel, 1 at the ridge), v: along the blade (studs).
    Returns (colour, patina mask, grain, metal, rough)."""
    co = _vec(g, g.math("MULTIPLY", u, 5.2 * grain_scale), g.math("ADD", g.math("MULTIPLY", v, 2.3), g.math("MULTIPLY", wig, 1.6)), 0.37)
    g1 = _noise3(g, 1.0, 5.0, 0.6, 0.9, coords=co)
    bands = _stripes(g, g.math("ADD", g.math("MULTIPLY", u, 8.0 * grain_scale), g.math("MULTIPLY", g1, 4.5)), 1.0)
    grain = g.math("ADD", g.math("MULTIPLY", g1, 0.62), g.math("MULTIPLY", bands, 0.38))
    col = g.ramp(grain, [(0.30, S(14, 20, 22)), (0.58, S(30, 42, 44)), (0.85, S(58, 76, 76))])
    blotch = _noise3(g, 2.2, 3.0, 0.5)
    valley = g.math("SUBTRACT", 1.0, grain)
    patina = SK.smooth(g, g.math("ADD", g.math("ADD", g.math("MULTIPLY", valley, 0.55), g.math("MULTIPLY", blotch, 0.5)), patina_bias), 0.64, 0.95)
    teal = g.ramp(g1, [(0.3, S(22, 78, 70)), (0.7, S(44, 112, 98))])
    col = g.mix(g.math("MULTIPLY", patina, 0.8), col, teal)
    metal = g.math("SUBTRACT", 0.92, g.math("MULTIPLY", patina, 0.62))
    rough = g.math("ADD", g.math("ADD", 0.34, g.math("MULTIPLY", grain, 0.14)), g.math("MULTIPLY", patina, 0.30))
    return col, patina, grain, metal, rough


def _wig(g, v, side_off=0.0):
    """A slow irregular wander along the blade (0..1), for the temper line."""
    return _noise3(g, 1.0, 2.0, 0.5, coords=_vec(g, g.math("MULTIPLY", v, 1.5), 0.31 + side_off, 0.5))


def mat_hira(name="UgHira"):
    """The hira: dark patinated steel with its forged grain, and the temper line (hamon) rising and falling along the polished band
    beside the edge bevel, small teeth (ashi) crossing the line. UV u: 0 where the bevel ends, 1 at the ridge; v along the blade."""
    g = Hm._Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    wig = _wig(g, v)
    fine = _noise3(g, 1.0, 2.0, 0.5, coords=_vec(g, g.math("MULTIPLY", v, 9.0), 0.71, 0.2))
    mid = _noise3(g, 1.0, 2.0, 0.5, coords=_vec(g, g.math("MULTIPLY", v, 4.0), 0.13, 0.9))
    wave1 = g.math("SINE", g.math("ADD", g.math("MULTIPLY", v, TAU / 0.60), g.math("MULTIPLY", g.math("SUBTRACT", wig, 0.5), 7.0)))
    wave2 = g.math("SINE", g.math("ADD", g.math("MULTIPLY", v, TAU / 0.21), g.math("MULTIPLY", g.math("SUBTRACT", mid, 0.5), 9.0)))
    d_h = g.math("ADD", g.math("ADD", 0.44, g.math("MULTIPLY", wave1, 0.17)), g.math("ADD", g.math("MULTIPLY", wave2, 0.07), g.math("MULTIPLY", g.math("SUBTRACT", fine, 0.5), 0.10)))
    yaki = SK.smooth(g, g.math("SUBTRACT", d_h, u), -0.025, 0.025)
    col, patina, grain, metal, rough = _dark_steel(g, u, v, wig)
    # ashi: short teeth running from the line toward the edge, and a faint halo (nioi) just beyond it
    teeth = g.math("LESS_THAN", g.math("MODULO", g.math("ADD", g.math("MULTIPLY", v, 38.0), g.math("MULTIPLY", wig, 9.0)), 1.0), 0.34)
    halo = g.math("MULTIPLY", SK.smooth(g, g.math("SUBTRACT", g.math("ADD", d_h, 0.14), u), 0.0, 0.14), g.math("SUBTRACT", 1.0, yaki))
    depth = g.math("SUBTRACT", d_h, u)                        # how far into the bright band (0 at the temper line)
    ashi = g.math("MULTIPLY", g.math("MULTIPLY", teeth, SK.smooth(g, depth, -0.01, 0.01)), g.math("SUBTRACT", 1.0, SK.smooth(g, depth, 0.03, 0.17)))
    col = g.mix(g.math("MULTIPLY", halo, 0.4), col, S(96, 116, 118))
    bright = g.ramp(fine, [(0.3, S(150, 158, 160)), (0.7, S(200, 206, 206))])
    bright = g.mix(g.math("MULTIPLY", g.math("MULTIPLY", ashi, g.math("SUBTRACT", 1.0, g.math("MULTIPLY", yaki, 0.0))), 0.5), bright, S(96, 108, 110))
    col = g.mix(yaki, col, bright)
    metal = _lerp(g, yaki, metal, 1.0)
    rough = _lerp(g, yaki, rough, g.math("ADD", 0.20, g.math("MULTIPLY", fine, 0.10)))
    col = g.ao(col, 0.03, 0.62)
    h = g.math("ADD", g.math("MULTIPLY", grain, 0.8), g.math("MULTIPLY", patina, -0.3))
    return g.finish(col, rough, metal, g.bump(h, 0.22, 0.003))


def mat_edge(name="UgEdge"):
    """The honed edge bevel: bright polished steel with fine hairline streaks along it (UV u is negative on it)."""
    g = Hm._Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    streak = _noise3(g, 1.0, 3.0, 0.6, coords=_vec(g, g.math("MULTIPLY", u, 40.0), g.math("MULTIPLY", v, 1.2), 0.3))
    col = g.ramp(streak, [(0.3, S(184, 192, 194)), (0.7, S(228, 234, 232))])
    col = g.ao(col, 0.02, 0.8)
    return g.finish(col, g.math("ADD", 0.13, g.math("MULTIPLY", streak, 0.1)), 1.0, g.bump(streak, 0.1, 0.002))


def mat_shinogi(name="UgShinogi"):
    """The ridge band and the back: the same dark steel, heavier teal, with fine brushed hairlines (kebiki) running along the blade."""
    g = Hm._Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    wig = _wig(g, v, 0.4)
    col, patina, grain, metal, rough = _dark_steel(g, u, v, wig, patina_bias=0.08, grain_scale=0.8)
    hair = _noise3(g, 1.0, 3.0, 0.65, coords=_vec(g, g.math("MULTIPLY", u, 60.0), g.math("MULTIPLY", v, 0.8), 0.5))
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", hair, 0.5), 0.5), col, S(70, 92, 90))
    col = g.ao(col, 0.03, 0.55)
    return g.finish(col, g.math("ADD", rough, g.math("MULTIPLY", hair, 0.1)), metal, g.bump(g.math("ADD", g.math("MULTIPLY", hair, 0.6), g.math("MULTIPLY", grain, 0.4)), 0.3, 0.003))


def mat_fuller(name="UgFuller"):
    """The fuller's floor: the deepest, most patinated part of the steel; dark verdigris with black pitting."""
    g = Hm._Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    wig = _wig(g, v, 0.7)
    col, patina, grain, metal, rough = _dark_steel(g, u, v, wig, patina_bias=0.18, grain_scale=1.3)
    pits = _noise3(g, 60.0, 2.0, 0.5)
    col = g.mix(g.math("MULTIPLY", SK.smooth(g, pits, 0.60, 0.78), 0.75), col, S(8, 12, 12))
    col = g.ao(col, 0.03, 0.5)
    return g.finish(col, g.math("ADD", rough, 0.1), g.math("MULTIPLY", metal, 0.85), g.bump(g.math("ADD", grain, pits), 0.35, 0.003))


def mat_inlay(name="UgInlay"):
    """Copper wire inlay set in the drift lines."""
    g = Hm._Graph(name)
    n = _noise3(g, 40.0, 3.0)
    col = g.ramp(n, [(0.3, S(196, 112, 74)), (0.7, S(240, 156, 106))])
    return g.finish(col, g.math("ADD", 0.26, g.math("MULTIPLY", n, 0.12)), 1.0)


def _verdigris(g, col, metal, rough, distance=0.05, reach=1.5):
    """Verdigris settled in the hollows: ambient occlusion turned to patina (teal, dielectric, rougher)."""
    ao = g.n("ShaderNodeAmbientOcclusion", samples=16, only_local=True)
    ao.inputs["Distance"].default_value = distance
    hollow = g.math("MINIMUM", g.math("MULTIPLY", g.math("POWER", g.math("SUBTRACT", 1.0, ao.outputs["AO"], clamp=True), 0.7), reach), 1.0)
    n = _noise3(g, 7.0, 4.0)
    hollow = g.math("MINIMUM", g.math("MULTIPLY", hollow, g.math("ADD", 0.6, g.math("MULTIPLY", n, 0.8))), 1.0)
    teal = g.ramp(n, [(0.3, S(34, 108, 94)), (0.7, S(64, 150, 128))])
    col = g.mix(hollow, col, teal)
    metal = g.math("MULTIPLY", metal, g.math("SUBTRACT", 1.0, g.math("MULTIPLY", hollow, 0.95)))
    rough = g.math("ADD", rough, g.math("MULTIPLY", hollow, 0.35))
    return col, metal, rough, hollow


def mat_bronze(name="UgBronze", dark=False, nanako=False):
    """Cast bronze: a warm brown-gold metal, verdigris in every hollow, a hammered skin."""
    g = Hm._Graph(name)
    n = _noise3(g, 16.0, 4.0)
    lo, hi_ = (S(104, 82, 50), S(158, 124, 72)) if not dark else (S(76, 60, 38), S(120, 94, 56))
    col = g.ramp(n, [(0.3, lo), (0.7, hi_)])
    wear = SK.smooth(g, _noise3(g, 5.0, 3.0), 0.6, 0.8)
    col = g.mix(g.math("MULTIPLY", wear, 0.5), col, S(214, 172, 104) if not dark else S(176, 136, 84))
    col, metal, rough, hollow = _verdigris(g, col, 1.0, g.math("ADD", 0.32, g.math("MULTIPLY", n, 0.10)), 0.05, 1.7)
    bump = g.math("ADD", n, g.math("MULTIPLY", hollow, -0.5))
    if nanako:
        vo = g.n("ShaderNodeTexVoronoi", **{"Scale": 70.0})
        g.link(g.coords(), vo.inputs["Vector"])
        dots = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", vo.outputs["Distance"], 1.6), clamp=True)
        bump = g.math("ADD", bump, g.math("MULTIPLY", dots, 1.2))
    col = g.ao(col, 0.04, 0.5)
    return g.finish(col, rough, metal, g.bump(bump, 0.35, 0.004))


def mat_copper(name="UgCopper"):
    """Worked copper: the warm red-orange of the metal, a light verdigris in the creases."""
    g = Hm._Graph(name)
    n = _noise3(g, 20.0, 4.0)
    col = g.ramp(n, [(0.3, S(196, 108, 72)), (0.7, S(240, 150, 104))])
    col, metal, rough, hollow = _verdigris(g, col, 1.0, g.math("ADD", 0.30, g.math("MULTIPLY", n, 0.15)), 0.04, 1.1)
    col = g.ao(col, 0.03, 0.55)
    return g.finish(col, rough, metal, g.bump(n, 0.15, 0.003))


def mat_brass(name="UgBrass", nanako=True):
    """Aged brass: a dull yellow, darkened and greened in the recesses, with a nanako (fish-roe) ground of tiny punched dots."""
    g = Hm._Graph(name)
    n = _noise3(g, 18.0, 4.0)
    col = g.ramp(n, [(0.3, S(150, 126, 64)), (0.7, S(206, 178, 102))])
    col, metal, rough, hollow = _verdigris(g, col, 0.95, g.math("ADD", 0.42, g.math("MULTIPLY", n, 0.15)), 0.04, 1.3)
    bump = n
    if nanako:
        vo = g.n("ShaderNodeTexVoronoi", **{"Scale": 80.0})
        g.link(g.coords(), vo.inputs["Vector"])
        bump = g.math("ADD", n, g.math("MULTIPLY", g.math("SUBTRACT", 1.0, g.math("MULTIPLY", vo.outputs["Distance"], 1.6), clamp=True), 1.5))
    col = g.ao(col, 0.03, 0.5)
    return g.finish(col, rough, metal, g.bump(bump, 0.3, 0.004))


def mat_leather(name="UgLeather"):
    """Blackened leather with a faint green dye: pores, creases, worn paler at the raised ridges."""
    g = Hm._Graph(name)
    pores = _noise3(g, 90.0, 2.0, 0.5)
    crease = _noise3(g, 6.0, 4.0, 0.6)
    col = g.ramp(g.math("ADD", g.math("MULTIPLY", pores, 0.4), g.math("MULTIPLY", crease, 0.6)), [(0.2, S(24, 26, 22)), (0.6, S(44, 46, 36)), (0.9, S(72, 70, 54))])
    col = g.mix(g.math("MULTIPLY", SK.smooth(g, crease, 0.62, 0.8), 0.25), col, S(30, 46, 40))
    col = g.ao(col, 0.04, 0.4)
    return g.finish(col, g.math("ADD", 0.5, g.math("MULTIPLY", pores, 0.2)), 0.0, g.bump(g.math("ADD", pores, g.math("MULTIPLY", crease, 0.5)), 0.45, 0.003))


def mat_linen(name="UgLinen"):
    """Bone-coloured linen cord: a twist's diagonal ridges (UV u round, v along), loose fibres, a little grime in the twist."""
    g = Hm._Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    twist = _stripes(g, g.math("ADD", g.math("MULTIPLY", u, 2.0), g.math("MULTIPLY", v, 0.55)), 1.0)
    fib = _noise3(g, 1.0, 3.0, 0.6, coords=_vec(g, g.math("MULTIPLY", u, 60.0), g.math("MULTIPLY", v, 6.0), 0.2))
    col = g.ramp(g.math("ADD", g.math("MULTIPLY", twist, 0.55), g.math("MULTIPLY", fib, 0.45)), [(0.15, S(138, 124, 98)), (0.55, S(196, 182, 150)), (0.9, S(226, 214, 186))])
    col = g.ao(col, 0.03, 0.35)
    return g.finish(col, 0.9, 0.0, g.bump(g.math("ADD", twist, g.math("MULTIPLY", fib, 0.5)), 0.5, 0.004))


def mat_bone(name="UgBone"):
    """Polished bone: ivory yellowed at the pores, fine growth lines."""
    g = Hm._Graph(name)
    n = _noise3(g, 7.0, 4.0, 0.5, 0.4)
    lines = _stripes(g, g.math("ADD", g.sep(g.coords())[2], g.math("MULTIPLY", n, 0.3)), 22.0)
    col = g.ramp(g.math("ADD", g.math("MULTIPLY", n, 0.7), g.math("MULTIPLY", lines, 0.3)), [(0.25, S(172, 150, 112)), (0.6, S(214, 198, 164)), (0.9, S(232, 222, 196))])
    col = g.ao(col, 0.03, 0.5)
    return g.finish(col, g.math("ADD", 0.32, g.math("MULTIPLY", n, 0.12)), 0.0, g.bump(lines, 0.05, 0.002))


def mat_steel_obj(name="UgSteelObj"):
    """Forged blackened steel for the guard arm (no UVs: object coordinates): dark teal-black body, patina in the hollows, and bare bright
    steel worn onto every raised edge (pointiness of the bevelled mesh), like the blade's polished edge."""
    g = Hm._Graph(name)
    co = g.coords()
    n1 = _noise3(g, 9.0, 5.0, 0.6, 0.8)
    n2 = _noise3(g, 40.0, 3.0, 0.6)
    col = g.ramp(g.math("ADD", g.math("MULTIPLY", n1, 0.6), g.math("MULTIPLY", n2, 0.4)), [(0.3, S(14, 20, 22)), (0.55, S(30, 42, 44)), (0.85, S(60, 78, 78))])
    ao = g.n("ShaderNodeAmbientOcclusion", samples=16, only_local=True)
    ao.inputs["Distance"].default_value = 0.06
    hollow = g.math("MINIMUM", g.math("MULTIPLY", g.math("POWER", g.math("SUBTRACT", 1.0, ao.outputs["AO"], clamp=True), 0.7), 1.4), 1.0)
    patina = SK.smooth(g, g.math("ADD", g.math("MULTIPLY", hollow, 0.7), g.math("MULTIPLY", n1, 0.4)), 0.55, 0.9)
    teal = g.ramp(n2, [(0.3, S(22, 78, 70)), (0.7, S(44, 112, 98))])
    col = g.mix(g.math("MULTIPLY", patina, 0.8), col, teal)
    geo = g.n("ShaderNodeNewGeometry")
    wear = SK.smooth(g, g.math("ADD", geo.outputs["Pointiness"], g.math("MULTIPLY", g.math("SUBTRACT", n2, 0.5), 0.12)), 0.53, 0.60)
    col = g.mix(wear, col, g.ramp(n2, [(0.3, S(150, 158, 160)), (0.7, S(204, 210, 210))]))
    metal = g.math("ADD", g.math("MULTIPLY", g.math("SUBTRACT", 0.92, g.math("MULTIPLY", patina, 0.6)), g.math("SUBTRACT", 1.0, wear)), wear)
    rough = g.math("ADD", g.math("ADD", 0.34, g.math("MULTIPLY", n2, 0.12)), g.math("MULTIPLY", patina, 0.3))
    rough = g.math("MULTIPLY", rough, g.math("SUBTRACT", 1.0, g.math("MULTIPLY", wear, 0.5)))
    col = g.ao(col, 0.03, 0.6)
    return g.finish(col, rough, metal, g.bump(g.math("ADD", n1, g.math("MULTIPLY", n2, 0.3)), 0.25, 0.003))
