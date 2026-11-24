"""Tiangou v3's materials: procedural Cycles shaders baked into the four maps (colour, normal, roughness, metalness) of each game piece
(run inside Blender). No letters, no symbols: a coat that is the midnight sky (deep blue, faint constellations drawn as sparse points and
the outlines of a few star-cells, silvered where the moon would fall: on top and at the rim), fur streaks along the body, dark paw pads,
a dark mouth; white fire (pale blue-white, a warm cream core at its root, cooler toward its tip), ivory fangs and claws, a black nose.

Colours are linear. The eclipse disc and its corona are Neon pieces whose colour the game sets (Placements.Glow).
"""
import bpy

import egg_hi as Hm

SKY = (0.006, 0.014, 0.060)             # the coat's ground: deep midnight blue
SKY2 = (0.016, 0.030, 0.120)            # lifted toward indigo by a slow noise
SILVER = (0.30, 0.42, 0.68)          # where the moon falls
STAR = (0.80, 0.90, 1.00)
PAD = (0.012, 0.012, 0.022)
GUM = (0.14, 0.018, 0.030)
TONGUE = (0.38, 0.050, 0.075)
IVORY = (0.62, 0.58, 0.46)
FIRE_ROOT = (1.00, 0.84, 0.52)          # the warm core
FIRE_MID = (0.60, 0.76, 1.00)
FIRE_TIP = (0.42, 0.62, 1.0)
EYE_HEX, PUPIL_HEX = "ffb21e", "0a0408"
ECLIPSE_HEX, CORONA_HEX, CORE_HEX = "05070c", "dcefff", "ffe9a8"


def _smooth(g, x, lo, hi):
    t = g.math("DIVIDE", g.math("SUBTRACT", x, lo), hi - lo, clamp=True)
    return g.math("MULTIPLY", g.math("MULTIPLY", t, t), g.math("SUBTRACT", 3.0, g.math("MULTIPLY", t, 2.0)))


def _vmul(g, vec, scale):
    n = g.n("ShaderNodeMapping")
    n.inputs["Scale"].default_value = scale
    g.link(vec, n.inputs["Vector"])
    return n.outputs["Vector"]


def mat_coat(name="TG3Coat"):
    """The hound's coat on Blender object coordinates (x right, y toward the nose, z up): midnight blue with fur streaks along y, silvered on top
    and where the surface turns toward the moon, stars, the outlines of a few star-cells, dark pads under the paws, a dark mouth."""
    g = Hm._Graph(name)
    co = g.coords()
    x, y, z = g.sep(co)
    geo = g.n("ShaderNodeNewGeometry")
    nx, ny, nz = g.sep(geo.outputs["Normal"])
    # fur: streaks stretched along the body, over a slow patchiness
    fur = g.n("ShaderNodeTexNoise", **{"Scale": 1.0, "Detail": 6.0, "Roughness": 0.55})
    g.link(_vmul(g, co, (5.5, 1.3, 5.5)), fur.inputs["Vector"])
    slow = g.n("ShaderNodeTexNoise", **{"Scale": 0.55, "Detail": 3.0})
    g.link(co, slow.inputs["Vector"])
    ground = g.mix(g.math("MULTIPLY", slow.outputs["Fac"], 1.6), SKY, SKY2)
    col = g.mix(g.math("MULTIPLY", fur.outputs["Fac"], 0.55), ground, (0.002, 0.005, 0.026))
    # moonlight: the top of the body, the crown, the top of each limb and the brow; broken by the fur
    top = _smooth(g, g.math("ADD", nz, g.math("MULTIPLY", g.math("SUBTRACT", fur.outputs["Fac"], 0.5), 0.55)), 0.15, 0.80)
    rim = _smooth(g, g.math("ADD", ny, g.math("MULTIPLY", nz, 0.5)), 0.55, 1.0)         # facing forward and up: the chest, the brow
    silver = g.math("MINIMUM", g.math("ADD", top, g.math("MULTIPLY", rim, 0.55)), 1.0)
    col = g.mix(g.math("MULTIPLY", silver, 0.85), col, SILVER)
    # stars: the points of a coarse cell lattice, most cells empty; and a finer, dimmer one
    cell = g.n("ShaderNodeTexVoronoi", feature="F1", Scale=0.85)
    g.link(co, cell.inputs["Vector"])
    rnd = g.bw(cell.outputs["Color"])
    star = g.math("MULTIPLY", _smooth(g, g.math("SUBTRACT", 0.24, cell.outputs["Distance"]), 0.0, 0.14), _smooth(g, rnd, 0.38, 0.46))
    cell2 = g.n("ShaderNodeTexVoronoi", feature="F1", Scale=3.1)
    g.link(co, cell2.inputs["Vector"])
    rnd2 = g.bw(cell2.outputs["Color"])
    star2 = g.math("MULTIPLY", g.math("MULTIPLY", _smooth(g, g.math("SUBTRACT", 0.09, cell2.outputs["Distance"]), 0.0, 0.07), _smooth(g, rnd2, 0.80, 0.86)), 0.7)
    # the outline of a few star-cells: the lines of a constellation
    edge = g.n("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE", Scale=0.85)
    g.link(co, edge.inputs["Vector"])
    line = g.math("MULTIPLY", _smooth(g, g.math("SUBTRACT", 0.065, edge.outputs["Distance"]), 0.0, 0.05), _smooth(g, rnd, 0.76, 0.8))
    sky_mask = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", silver, 0.8))                  # stars show on the dark coat, not on the silvered top
    glint = g.math("MULTIPLY", g.math("MINIMUM", g.math("MULTIPLY", star2, 0.8), 1.0), sky_mask)
    col = g.mix(glint, col, STAR)
    # dark pads under the paws (the low part of each limb, facing down)
    pad = g.math("MULTIPLY", _smooth(g, g.math("SUBTRACT", -0.35, nz), 0.0, 0.3), _smooth(g, g.math("SUBTRACT", 1.45, z), 0.0, 0.6))
    col = g.mix(pad, col, PAD)
    # the mouth: the roof (faces down, just under the muzzle's line) and the floor (faces up, on the jaw), forward of the cheek
    ahead = g.math("MULTIPLY", _smooth(g, y, 16.3, 16.8), g.math("MULTIPLY", _smooth(g, g.math("SUBTRACT", 1.4, g.math("ABSOLUTE", x)), 0.0, 0.25), _smooth(g, g.math("SUBTRACT", 21.9, y), 0.0, 0.2)))
    roof = g.math("MULTIPLY", g.math("MULTIPLY", _smooth(g, g.math("SUBTRACT", -0.78, nz), 0.0, 0.12), _smooth(g, z, 14.2, 14.45)), _smooth(g, g.math("SUBTRACT", 14.8, z), 0.0, 0.15))
    floor = g.math("MULTIPLY", g.math("MULTIPLY", _smooth(g, g.math("SUBTRACT", nz, 0.78), 0.0, 0.12), _smooth(g, z, 13.9, 14.1)), _smooth(g, g.math("SUBTRACT", 15.0, z), 0.0, 0.15))
    inside = g.math("MULTIPLY", g.math("MAXIMUM", roof, floor), ahead)
    mouth = g.mix(g.math("MULTIPLY", floor, 1.0), GUM, TONGUE)
    col = g.mix(inside, col, mouth)
    # fur: fine strands (darker between them), the ears' inner faces pale with a flicker, the lip line under the flew
    fine = g.n("ShaderNodeTexNoise", **{"Scale": 1.0, "Detail": 3.0, "Roughness": 0.6})
    g.link(_vmul(g, co, (26.0, 4.0, 26.0)), fine.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", _smooth(g, g.math("SUBTRACT", 0.55, fine.outputs["Fac"]), 0.0, 0.3), 0.55), col, (0.0, 0.0, 0.01))
    ear = g.math("MULTIPLY", g.math("MULTIPLY", _smooth(g, z, 18.6, 19.1), _smooth(g, ny, 0.15, 0.5)), _smooth(g, g.math("ABSOLUTE", x), 0.9, 1.3))
    col = g.mix(g.math("MULTIPLY", ear, 0.9), col, (0.40, 0.55, 0.95))
    lip = g.math("MULTIPLY", g.math("MULTIPLY", _smooth(g, g.math("SUBTRACT", -0.2, nz), 0.0, 0.3), _smooth(g, y, 16.9, 17.4)),
                 g.math("MULTIPLY", _smooth(g, z, 14.0, 14.4), _smooth(g, g.math("SUBTRACT", 15.4, z), 0.0, 0.3)))
    col = g.mix(g.math("MULTIPLY", lip, 0.8), col, (0.004, 0.006, 0.02))
    col = g.ao(col, 0.35, 0.45)
    rough = g.math("SUBTRACT", g.math("ADD", 0.78, g.math("MULTIPLY", fur.outputs["Fac"], 0.1)), g.math("MULTIPLY", g.math("MAXIMUM", glint, inside), 0.35))
    metal = g.math("MULTIPLY", silver, 0.12)
    height = g.math("ADD", g.math("MULTIPLY", fur.outputs["Fac"], 0.6), g.math("MULTIPLY", fine.outputs["Fac"], 0.9))
    return g.finish(col, rough, metal, g.bump(height, 0.9, 0.03))


def mat_fire(name="TG3Fire"):
    """White fire on the UV of its tongues (u round, the broad faces at 0.25 and 0.75 and the edges at 0 and 0.5; v from the root, 0, to the tip, 0.8): a warm
    white core on the faces, a cool blue-white at the edges, warmer at the root, cooler toward the tip."""
    g = Hm._Graph(name)
    uv = g.coords("UV")
    u, v, _ = g.sep(uv)
    sn = g.math("SINE", g.math("MULTIPLY", u, 6.28318))
    core = g.math("MULTIPLY", sn, sn)
    t = g.math("MINIMUM", g.math("DIVIDE", v, 0.8), 1.0)
    base = g.ramp(t, [(0.0, FIRE_ROOT), (0.25, (1.0, 0.96, 0.9)), (0.65, (0.82, 0.9, 1.0)), (1.0, FIRE_MID)])
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", 1.0, core), 0.85), base, FIRE_TIP)
    return g.finish(col, 0.9, 0.0)


def mat_plain(name, color, rough, metal=0.0):
    g = Hm._Graph(name)
    return g.finish(g.mix(0.0, color, color), rough, metal)


def mat_tooth(name="TG3Tooth"):
    g = Hm._Graph(name)
    n = g.n("ShaderNodeTexNoise", **{"Scale": 20.0, "Detail": 3.0})
    g.link(g.coords(), n.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", n.outputs["Fac"], 0.5), IVORY, (0.30, 0.27, 0.20))
    return g.finish(col, 0.38, 0.0, g.bump(n.outputs["Fac"], 0.15, 0.01))


def all_materials():
    import egg_kit as K
    return {"coat": mat_coat(), "fire": mat_fire(), "tooth": mat_tooth(), "star": mat_plain("TG3Star", (0.82, 0.92, 1.0), 0.45), "nose": mat_plain("TG3Nose", (0.016, 0.017, 0.026), 0.92), "nostril": mat_plain("TG3Nostril", (0.0, 0.0, 0.0), 0.9),
            "eyes": K.glow_material(EYE_HEX), "pupils": K.glow_material(PUPIL_HEX), "eclipse": K.glow_material(ECLIPSE_HEX), "corona": K.glow_material(CORONA_HEX),
            "core": K.glow_material(CORE_HEX)}
