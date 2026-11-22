"""The Demonic sword's materials (run inside Blender, headless): procedural shaders for the high-detail source, baked to the game
mesh's four maps (color from Base Color, roughness, metalness, the tangent normal from the geometry and bump).

    blade       blackened, blued steel (fine grain running along it), the edge bevel and the false edge mirror-polished, a hard
                temper line (hamon) of leaning flame tongues rising out of the polished edge into the dark; the fuller's floor
                a deeper blue, the back a matte black. Reads the primary UV (u across from the spine, v along) and the "Aux" UV
                (per-face: a polished facet flag, a zone) that the blade builder writes
    iron        dark forged iron: hammer marks, the edges worn bright
    bronze      blackened bronze: dark in the hollows and the engraving, a warm metal on the raised faces
    skin        black lacquered ray skin: small pale nodules
    silk        blood-red braided cord: a chevron of fine ridges along each ribbon

Metal is baked as metal: base colours of bare metal are bright (sRGB 180 and over) where polished; the dark blued steel and the
blackened bronze are oxide on metal, so they are dark colours with a lower, but not zero, metalness.
"""
import math

import bpy

import secret_kit as SK
import weapon_kit as WK

Hm = SK.Hm
TAU = math.tau


def srgb(r, g, b):
    return SK.srgb(r, g, b)


def vec(g, x=0.0, y=0.0, z=0.0):
    c = g.n("ShaderNodeCombineXYZ")
    for i, val in enumerate((x, y, z)):
        if isinstance(val, (int, float)):
            c.inputs[i].default_value = val
        else:
            g.link(val, c.inputs[i])
    return c.outputs[0]


def uvmap(g, name="Param"):
    """A UV layer by name. The hi-detail pieces' own layer is called "Param" (never "UVMap": in a bake the game mesh's layer of that
    name is what a shader finds, and the temper line would be drawn from the game UVs)."""
    return g.n("ShaderNodeUVMap", uv_map=name).outputs["UV"]


def noise(g, vector, scale, detail=3.0, rough=0.5):
    n = g.n("ShaderNodeTexNoise", **{"Scale": scale, "Detail": detail, "Roughness": rough})
    g.link(vector, n.inputs["Vector"])
    return n.outputs["Fac"]


def smooth(g, x, a, b):
    return SK.smooth(g, x, a, b)


def mat_blade(name="SdBlade"):
    g = Hm._Graph(name)
    u, v, _ = g.sep(uvmap(g))
    aux = g.n("ShaderNodeUVMap", uv_map="Aux").outputs["UV"]
    flag, zone, _ = g.sep(aux)
    # the temper line: flame tongues that rise from the edge into the dark, each cell its own height, leaning toward the point
    N = 9.0
    vN = g.math("MULTIPLY", v, N)
    cell = g.math("FLOOR", vN)
    wn = g.n("ShaderNodeTexWhiteNoise", noise_dimensions="1D")
    g.link(cell, wn.inputs["W"])
    hgt = wn.outputs["Value"]
    wn2 = g.n("ShaderNodeTexWhiteNoise", noise_dimensions="1D")
    g.link(g.math("ADD", cell, 31.7), wn2.inputs["W"])
    x = g.math("FRACT", vN)
    xw = g.math("POWER", x, 1.55)                                              # skews the peak toward the point
    tongue = g.math("POWER", g.math("SUBTRACT", 1.0, g.math("ABSOLUTE", g.math("SUBTRACT", g.math("MULTIPLY", xw, 2.0), 1.0))), 1.05)
    small = g.math("MULTIPLY", g.math("POWER", g.math("SINE", g.math("MULTIPLY", g.math("MULTIPLY", vN, 2.6), math.pi)), 2.0), 0.35)
    amp = g.math("ADD", 0.030, g.math("MULTIPLY", hgt, 0.15))
    hamon_u = g.math("SUBTRACT", 0.845, g.math("MULTIPLY", amp, g.math("ADD", tongue, g.math("MULTIPLY", small, wn2.outputs["Value"]))))
    below = smooth(g, g.math("SUBTRACT", u, hamon_u), -0.006, 0.006)       # 1 on the polished side of the line
    haze = g.math("MULTIPLY", smooth(g, g.math("SUBTRACT", u, hamon_u), -0.05, -0.0), g.math("SUBTRACT", 1.0, below))
    pol = g.math("MAXIMUM", g.math("GREATER_THAN", flag, 0.5), below)
    bohi = g.math("LESS_THAN", g.math("ABSOLUTE", g.math("SUBTRACT", zone, 0.25)), 0.08)
    mune = g.math("GREATER_THAN", zone, 0.4)
    # forged grain running along the blade
    grain_co = vec(g, g.math("MULTIPLY", u, 38.0), g.math("MULTIPLY", v, 4.0), 0.0)
    grain = noise(g, grain_co, 5.0, 5.0, 0.6)
    stripes = g.math("ADD", g.math("MULTIPLY", g.math("SINE", g.math("MULTIPLY", g.math("ADD", g.math("MULTIPLY", u, 70.0), g.math("MULTIPLY", grain, 3.0)), TAU)), 0.5), 0.5)
    fine = noise(g, g.coords(), 16.0, 4.0, 0.55)
    dark = g.ramp(g.math("ADD", g.math("MULTIPLY", fine, 0.72), g.math("MULTIPLY", stripes, 0.28)),
                  [(0.25, SK.srgb(34, 38, 48)), (0.55, SK.srgb(48, 55, 70)), (0.85, SK.srgb(68, 78, 100))])
    blue_floor = g.ramp(fine, [(0.3, SK.srgb(22, 28, 44)), (0.8, SK.srgb(40, 52, 80))])
    black_back = g.ramp(fine, [(0.3, SK.srgb(12, 12, 14)), (0.8, SK.srgb(24, 24, 28))])
    mirror = g.ramp(g.math("ADD", g.math("MULTIPLY", fine, 0.7), g.math("MULTIPLY", grain, 0.3)),
                    [(0.3, SK.srgb(196, 202, 212)), (0.7, SK.srgb(222, 227, 235))])
    col = g.mix(bohi, dark, blue_floor)
    col = g.mix(mune, col, black_back)
    col = g.mix(g.math("MULTIPLY", haze, 0.45), col, SK.srgb(78, 92, 122))        # the soft cloud above the line
    col = g.ao(col, 0.05, 0.55)
    col = g.mix(pol, col, mirror)
    rough_dark = g.math("ADD", 0.30, g.math("MULTIPLY", g.math("SUBTRACT", stripes, 0.5), 0.14))
    r = lerp(g, rough_dark, 0.065, pol)
    r = lerp(g, r, 0.17, g.math("MULTIPLY", bohi, g.math("SUBTRACT", 1.0, pol)))
    r = lerp(g, r, 0.55, mune)
    metal = lerp(g, 0.82, 1.0, pol)
    metal = lerp(g, metal, 0.6, mune)
    return g.finish(col, r, metal, g.bump(g.math("ADD", g.math("MULTIPLY", grain, 0.6), g.math("MULTIPLY", stripes, 0.4)), 0.10, 0.002))


def lerp(g, a, b, t):
    """a * (1 - t) + b * t, on values."""
    return g.math("ADD", g.math("MULTIPLY", a, g.math("SUBTRACT", 1.0, t)), g.math("MULTIPLY", b, t))


def pointy(g, a=0.0, b=1.0):
    """Edge wear: Cycles' pointiness, 0..1 (0.5 flat), ramped so only convex edges read."""
    geo = g.n("ShaderNodeNewGeometry")
    return g.math("DIVIDE", g.math("SUBTRACT", geo.outputs["Pointiness"], 0.5 + a), (b - a) * 0.5, clamp=True)


def mat_iron(name="SdIron", wear=True, line_col=None):
    g = Hm._Graph(name)
    co = g.coords()
    line = g.math("GREATER_THAN", g.sep(g.n("ShaderNodeUVMap", uv_map="Aux").outputs["UV"])[0], 0.35)
    n1 = noise(g, co, 22.0, 5.0, 0.6)
    hammer = g.n("ShaderNodeTexVoronoi", **{"Scale": 42.0})
    g.link(co, hammer.inputs["Vector"])
    dents = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", hammer.outputs["Distance"], 1.6), clamp=True)
    base = g.ramp(g.math("ADD", g.math("MULTIPLY", n1, 0.6), g.math("MULTIPLY", dents, 0.4)), [(0.25, SK.srgb(34, 32, 34)), (0.6, SK.srgb(52, 50, 52)), (0.9, SK.srgb(74, 72, 76))])
    base = g.ao(base, 0.05, 0.5)
    worn = g.math("MAXIMUM", pointy(g, 0.04, 0.42), line)
    col = g.mix(g.math("MULTIPLY", worn, 0.9), base, SK.srgb(*(line_col or (160, 158, 160))))
    r = g.math("SUBTRACT", g.math("ADD", 0.52, g.math("MULTIPLY", g.math("SUBTRACT", n1, 0.5), 0.2)), g.math("MULTIPLY", worn, 0.3))
    metal = g.math("ADD", 0.80, g.math("MULTIPLY", worn, 0.2))
    return g.finish(col, r, metal, g.bump(g.math("ADD", g.math("MULTIPLY", n1, 0.5), g.math("MULTIPLY", dents, 0.5)), 0.18, 0.003))


def mat_bronze(name="SdBronze"):
    g = Hm._Graph(name)
    co = g.coords()
    line = g.math("GREATER_THAN", g.sep(g.n("ShaderNodeUVMap", uv_map="Aux").outputs["UV"])[0], 0.35)       # the engraved lines, polished
    n1 = noise(g, co, 18.0, 5.0, 0.55)
    base = g.ramp(n1, [(0.25, SK.srgb(22, 17, 14)), (0.65, SK.srgb(38, 29, 22)), (0.95, SK.srgb(60, 44, 30))])
    ao = g.n("ShaderNodeAmbientOcclusion", samples=16, only_local=True)
    ao.inputs["Distance"].default_value = 0.035
    hollow = g.math("SUBTRACT", 1.0, ao.outputs["AO"], clamp=True)
    col = g.mix(g.math("MINIMUM", g.math("MULTIPLY", hollow, 1.9), 1.0), base, SK.srgb(14, 11, 9))       # blackened in the hollows
    worn = g.math("MAXIMUM", pointy(g, 0.03, 0.40), line)
    col = g.mix(g.math("MULTIPLY", worn, 0.9), col, SK.srgb(190, 140, 78))                               # polished bright on the edges and in the lines
    r = g.math("SUBTRACT", g.math("ADD", 0.36, g.math("MULTIPLY", hollow, 0.3)), g.math("MULTIPLY", worn, 0.22))
    metal = g.math("SUBTRACT", g.math("ADD", 0.80, g.math("MULTIPLY", worn, 0.2)), g.math("MULTIPLY", hollow, 0.25))
    return g.finish(col, r, metal, g.bump(n1, 0.10, 0.002))


def mat_skin(name="SdSkin"):
    """Black lacquered ray skin: a field of small pale nodules."""
    g = Hm._Graph(name)
    co = g.coords()
    vo = g.n("ShaderNodeTexVoronoi", **{"Scale": 120.0})
    g.link(co, vo.inputs["Vector"])
    node = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", vo.outputs["Distance"], 2.6), clamp=True)
    col = g.mix(g.math("MULTIPLY", g.math("MULTIPLY", node, node), 0.7), SK.srgb(14, 14, 17), SK.srgb(92, 92, 98))
    col = g.ao(col, 0.03, 0.5)
    return g.finish(col, g.math("SUBTRACT", 0.42, g.math("MULTIPLY", node, 0.2)), 0.0, g.bump(node, 0.35, 0.002))


def mat_silk(name="SdSilk", dark=(64, 3, 9), light=(122, 11, 20), uv="Param"):
    """A braided red cord: fine herringbone ridges along each flat ribbon (UV u across it, v along)."""
    g = Hm._Graph(name)
    u, v, _ = g.sep(uvmap(g, uv))
    chev = g.math("ADD", g.math("MULTIPLY", v, 34.0), g.math("MULTIPLY", g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5)), 8.0))
    ridge = g.math("ADD", g.math("MULTIPLY", g.math("SINE", g.math("MULTIPLY", chev, TAU)), 0.5), 0.5)
    fibre = noise(g, g.coords(), 60.0, 3.0, 0.5)
    col = g.ramp(g.math("ADD", g.math("MULTIPLY", ridge, 0.7), g.math("MULTIPLY", fibre, 0.3)), [(0.1, SK.srgb(*dark)), (0.9, SK.srgb(*light))])
    col = g.ao(col, 0.03, 0.4)
    return g.finish(col, g.math("ADD", 0.62, g.math("MULTIPLY", g.math("SUBTRACT", ridge, 0.5), 0.12)), 0.0, g.bump(ridge, 0.5, 0.0025))


def mat_cord(name="SdCord"):
    return mat_silk(name, (56, 2, 8), (112, 10, 18), uv="UVMap")


def mat_rag(name="SdRag"):
    """Ragged red cloth / fray: darker, rougher."""
    g = Hm._Graph(name)
    n = noise(g, g.coords(), 40.0, 4.0, 0.55)
    col = g.ramp(n, [(0.25, SK.srgb(58, 3, 8)), (0.75, SK.srgb(112, 10, 18))])
    col = g.ao(col, 0.03, 0.4)
    return g.finish(col, 0.78, 0.0, g.bump(n, 0.4, 0.002))
