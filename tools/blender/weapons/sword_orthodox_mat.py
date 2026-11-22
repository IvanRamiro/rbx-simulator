"""The Orthodox sword's materials (run inside Blender): procedural shaders on the HIGH-detail parts, baked to the game mesh's colour,
roughness, metalness and normal maps. Every colour is given the way a painter reads it (sRGB 0-255) and converted. No glyphs and no
shapes that could be read as anatomy: grain, a temper line, fine dots, weave.

    steel      folded-steel grain (itame, the layers following the blade), a wavy temper line (hamon) with its haze (nioi), mirror-polished
               edge bevels and ridge, a gold line inlaid in each groove
    silver     white silver, polished, with a faint stone grain (ishime)
    gilt       gold with a fish-roe (nanako) texture of fine dots
    rayskin    white ray-skin, round pebbles and a scatter of larger ones
    silk       deep azure silk, a twill weave; cords; jade; gold thread
"""
import math

import secret_kit as SK
import sword_orthodox_parts as P
import weapon_kit as WK

Hm = WK.Hm
TAU = math.tau
srgb = SK.srgb


def _uv(g):
    u, v, _ = g.sep(g.coords("UV"))
    return u, v


def _smooth(g, x, a, b):
    return SK.smooth(g, x, a, b)


def _band(g, x, a0, a1, b0, b1):
    """1 between a1 and b0, easing in over a0-a1 and out over b0-b1."""
    return g.math("MULTIPLY", _smooth(g, x, a0, a1), g.math("SUBTRACT", 1.0, _smooth(g, x, b0, b1)))


def mat_steel(name="OrSteel"):
    g = Hm._Graph(name)
    u, v = _uv(g)
    d = g.math("MULTIPLY", g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5)), 2.0)          # 0 ridge .. 0.66 shinogi .. 1 edge
    L = g.math("MULTIPLY", v, 2.0)                                                       # studs from the grip, along the blade
    s = g.math("DIVIDE", g.math("SUBTRACT", L, -P.Z_HILT), P.BLADE_LEN)                    # 0 at the collar, 1 at the point
    n1 = WK._noise(g, 2.2, 3.0, coords=g.coords())
    n2 = WK._noise(g, 7.0, 4.0, coords=g.coords())
    # --- zones
    bevel = _smooth(g, d, 0.722, 0.748)
    ridge = g.math("SUBTRACT", 1.0, _smooth(g, d, 0.105, 0.125))
    root = _smooth(g, s, 0.0, -0.02)                                                     # 1 where the blade is the root inside the bell (s < 0)
    polished = g.math("MULTIPLY", g.math("MAXIMUM", bevel, ridge), g.math("SUBTRACT", 1.0, root))
    inlay = g.math("MULTIPLY", _band(g, d, 0.196, 0.204, 0.246, 0.254), g.math("SUBTRACT", 1.0, _smooth(g, s, 0.6, 0.625)))
    # --- the temper line: a notare wave with a finer ripple, and the haze (nioi) beyond it
    wave = g.math("ADD", g.math("ADD", 0.60, g.math("MULTIPLY", g.math("SINE", g.math("ADD", g.math("MULTIPLY", L, 9.6), g.math("MULTIPLY", n1, 3.0))), 0.026)),
                  g.math("MULTIPLY", g.math("SINE", g.math("ADD", g.math("MULTIPLY", L, 41.0), g.math("MULTIPLY", n2, 4.0))), 0.011))
    haze = _smooth(g, g.math("SUBTRACT", d, wave), -0.008, 0.012)
    cloud = g.math("ADD", g.math("MULTIPLY", n2, 0.5), 0.5)
    # --- the layered grain: lines along the blade, bent by slow noise, fine layers inside the broad ones
    big = g.math("ADD", g.math("MULTIPLY", d, 11.0), g.math("ADD", g.math("MULTIPLY", n1, 3.4), g.math("MULTIPLY", g.math("SINE", g.math("MULTIPLY", L, 2.4)), 0.7)))
    fine = g.math("ADD", g.math("MULTIPLY", d, 30.0), g.math("MULTIPLY", n2, 3.0))
    lines_big = g.math("ABSOLUTE", g.math("SINE", g.math("MULTIPLY", big, math.pi)))
    lines_fine = g.math("ABSOLUTE", g.math("SINE", g.math("MULTIPLY", fine, math.pi)))
    dark = g.math("ADD", g.math("MULTIPLY", _smooth(g, lines_big, 0.55, 0.95), 0.55), g.math("MULTIPLY", _smooth(g, lines_fine, 0.6, 0.97), 0.3))
    dark = g.math("MINIMUM", dark, 1.0)
    grain_col = g.ramp(dark, [(0.0, srgb(158, 170, 194)), (0.5, srgb(112, 126, 152)), (1.0, srgb(62, 74, 100))])
    nioi_col = g.mix(g.math("MULTIPLY", cloud, 0.5), srgb(232, 238, 247), srgb(204, 214, 232))
    col = g.mix(g.math("MULTIPLY", haze, g.math("SUBTRACT", 1.0, polished)), grain_col, nioi_col)
    mirror = srgb(238, 242, 248)
    col = g.mix(polished, col, mirror)
    col = g.mix(root, col, srgb(104, 110, 124))
    col = g.mix(inlay, col, srgb(226, 178, 80))
    col = g.ao(col, 0.025, 0.55)
    unpol = g.math("SUBTRACT", 1.0, polished)
    rough = g.math("ADD", g.math("MULTIPLY", unpol, g.math("ADD", 0.40, g.math("MULTIPLY", dark, 0.16))), 0.07)
    rough = g.math("SUBTRACT", rough, g.math("MULTIPLY", haze, g.math("MULTIPLY", unpol, 0.1)))
    rough = g.math("ADD", g.math("MULTIPLY", rough, g.math("SUBTRACT", 1.0, inlay)), g.math("MULTIPLY", inlay, 0.3))
    metal = g.math("SUBTRACT", 0.88, g.math("MULTIPLY", unpol, g.math("MULTIPLY", dark, 0.12)))
    metal = g.math("SUBTRACT", metal, g.math("MULTIPLY", inlay, 0.1))
    height = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, dark), unpol)
    return g.finish(col, rough, metal, g.bump(height, 0.4, 0.0016))


def mat_silver(name="OrSilver", rough=0.2):
    """White silver, polished, a stone-grain (ishime) in it; where recesses gather, a cooler shade."""
    g = Hm._Graph(name)
    co = g.coords()
    n = WK._noise(g, 34.0, 5.0, coords=co)
    n2 = WK._noise(g, 4.0, 3.0, coords=co)
    col = g.ramp(g.math("ADD", g.math("MULTIPLY", n, 0.6), g.math("MULTIPLY", n2, 0.4)), [(0.3, srgb(196, 203, 216)), (0.65, srgb(222, 227, 236)), (0.9, srgb(240, 243, 248))])
    col = g.ao(col, 0.05, 0.45)
    return g.finish(col, g.math("ADD", rough, g.math("MULTIPLY", g.math("SUBTRACT", n, 0.5), 0.12)), 0.72, g.bump(n, 0.12, 0.002))


def _nanako(g, scale, size):
    """Fish-roe: a field of small round raised dots (Voronoi cells, each a dot): returns dots 0..1."""
    vo = g.n("ShaderNodeTexVoronoi", **{"Scale": scale})
    g.link(g.coords(), vo.inputs["Vector"])
    return g.math("SUBTRACT", 1.0, _smooth(g, vo.outputs["Distance"], size * 0.5, size))


def mat_gilt(name="OrGilt", rough=0.26, dots=True, scale=110.0, deep=False):
    """Gilt silver: warm gold, a fine nanako (small round dots), a deeper gold in the recesses. deep: the lining of the bell, a little darker."""
    g = Hm._Graph(name)
    co = g.coords()
    n = WK._noise(g, 14.0, 3.0, coords=co)
    top = srgb(206, 154, 58) if deep else srgb(236, 190, 92)
    low = srgb(142, 94, 30) if deep else srgb(176, 124, 44)
    d = _nanako(g, scale, 0.62) if dots else n
    tone = g.math("ADD", g.math("ADD", 0.5, g.math("MULTIPLY", d, 0.22)), g.math("MULTIPLY", g.math("SUBTRACT", n, 0.5), 0.2))
    col = g.ramp(tone, [(0.0, low), (0.6, top), (1.0, srgb(252, 218, 136))])
    col = g.ao(col, 0.05, 0.4)
    return g.finish(col, g.math("ADD", rough, g.math("MULTIPLY", g.math("SUBTRACT", 1.0, d), 0.08)), 0.62, g.bump(d, 0.3, 0.0018))


def mat_rayskin(name="OrRaySkin"):
    """White ray-skin: a mat of round pebbles, a scatter of larger ones."""
    g = Hm._Graph(name)
    co = g.coords()
    vor = g.n("ShaderNodeTexVoronoi", **{"Scale": 70.0})
    g.link(co, vor.inputs["Vector"])
    big = g.n("ShaderNodeTexVoronoi", **{"Scale": 22.0})
    g.link(co, big.inputs["Vector"])
    d = vor.outputs["Distance"]
    gate = g.math("LESS_THAN", g.sep(big.outputs["Color"])[0], 0.35)
    bigd = g.math("MULTIPLY", g.math("SUBTRACT", 1.0, _smooth(g, big.outputs["Distance"], 0.16, 0.34)), gate)
    height = g.math("MAXIMUM", g.math("SUBTRACT", 1.0, _smooth(g, d, 0.18, 0.52)), g.math("MULTIPLY", bigd, 1.2))
    col = g.ramp(height, [(0.0, srgb(170, 166, 156)), (0.45, srgb(226, 222, 212)), (1.0, srgb(246, 243, 235))])
    col = g.ao(col, 0.03, 0.5)
    return g.finish(col, g.math("SUBTRACT", 0.62, g.math("MULTIPLY", height, 0.25)), 0.0, g.bump(height, 0.85, 0.004))


def mat_silk(name="OrSilk", dark=srgb(3, 14, 52), light=srgb(12, 46, 116)):
    """Silk twill: fine diagonal lines (the weave), a lustre that runs along the band. For the wrap's bands (loft UVs: u across, v along)."""
    g = Hm._Graph(name)
    u, v = _uv(g)
    tw = g.math("ADD", g.math("MULTIPLY", g.math("SINE", g.math("MULTIPLY", g.math("ADD", g.math("MULTIPLY", v, 120.0), g.math("MULTIPLY", u, 16.0)), TAU)), 0.5), 0.5)
    lustre = g.math("SINE", g.math("MULTIPLY", u, math.pi))
    col = g.ramp(g.math("ADD", g.math("MULTIPLY", tw, 0.5), g.math("MULTIPLY", lustre, 0.5)), [(0.0, dark), (1.0, light)])
    col = g.ao(col, 0.03, 0.5)
    return g.finish(col, g.math("SUBTRACT", 0.62, g.math("MULTIPLY", lustre, 0.16)), 0.0, g.bump(tw, 0.35, 0.002))


def mat_cord(name, dark, light, twist=3.0):
    """A twisted silk strand."""
    g = Hm._Graph(name)
    u, v = _uv(g)
    t = g.math("ADD", g.math("MULTIPLY", g.math("SINE", g.math("MULTIPLY", g.math("ADD", u, g.math("MULTIPLY", v, twist)), TAU * 2)), 0.5), 0.5)
    col = g.ao(g.ramp(t, [(0.0, dark), (1.0, light)]), 0.03, 0.5)
    return g.finish(col, 0.55, 0.0, g.bump(t, 0.3, 0.002))


def mat_jade(name="OrJade"):
    """Pale nephrite: milky celadon white, soft clouds of a deeper green, polished."""
    g = Hm._Graph(name)
    n = WK._noise(g, 3.5, 5.0, 1.2, coords=g.coords())
    col = g.ramp(n, [(0.3, srgb(150, 188, 166)), (0.55, srgb(196, 222, 204)), (0.85, srgb(232, 242, 232))])
    return g.finish(g.ao(col, 0.03, 0.55), 0.16, 0.0, None)
