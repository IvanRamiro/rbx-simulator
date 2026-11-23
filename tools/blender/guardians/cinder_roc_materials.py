"""The Cinder Roc's materials: procedural Cycles shaders that are baked into the four maps (colour, normal, roughness, metalness) of
each game piece (run inside Blender). No letters, no symbols: plumage, basalt, horn, scales, ember.

Palette: charcoal plumage lit from underneath by a deep ember-orange (hue about 25 degrees: orange, never the crimson of the Demonic
territory, the azure and gold of the Orthodox one or the teal of the Unorthodox one), cracked basalt armour with thin molten cracks,
obsidian-black horn and talons, an amber fire in the eyes (a separate Neon piece).
"""
import bpy

import egg_hi as Hm

EMBER = (0.92, 0.17, 0.018)        # the underfeather glow, linear
EMBER_HOT = (1.0, 0.42, 0.045)     # where it burns hottest
AMBER = (1.0, 0.62, 0.12)          # a flame's tip
CHARCOAL = (0.006, 0.006, 0.008)
SLATE = (0.020, 0.021, 0.028)


def _ao(g, distance=0.5):
    a = g.n("ShaderNodeAmbientOcclusion", samples=16, only_local=True)
    a.inputs["Distance"].default_value = distance
    return g.math("POWER", g.math("SUBTRACT", 1.0, a.outputs["AO"], clamp=True), 1.4)


def _smooth(g, x, lo, hi):
    """smoothstep(lo, hi, x) as nodes."""
    t = g.math("DIVIDE", g.math("SUBTRACT", x, lo), hi - lo, clamp=True)
    return g.math("MULTIPLY", g.math("MULTIPLY", t, t), g.math("SUBTRACT", 3.0, g.math("MULTIPLY", t, 2.0)))


def mat_plumage(name="CinderPlumage", glow=1.0, edge=1.0):
    """A flight or contour feather (UV: u across, v along): charcoal with a slate sheen along the rachis and fine barbs, the root and
    the trailing edge burning ember, the deep gaps between overlapping feathers glowing."""
    g = Hm._Graph(name)
    uv = g.coords("UV")
    u, v, _ = g.sep(uv)
    co = g.coords()
    n1 = g.n("ShaderNodeTexNoise", **{"Scale": 2.2, "Detail": 3.0, "Roughness": 0.6})
    g.link(co, n1.inputs["Vector"])
    col = g.ramp(n1.outputs["Fac"], [(0.32, CHARCOAL), (0.72, SLATE)])
    barbs = g.n("ShaderNodeTexWave", **{"Scale": 70.0, "Distortion": 1.6, "Detail": 2.0, "Detail Scale": 1.5})
    g.link(uv, barbs.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", barbs.outputs["Fac"], 0.85), col, (0.055, 0.058, 0.078))
    # the rachis: a lighter shaft along the feather
    shaft = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.30)), 22.0), clamp=True)
    col = g.mix(g.math("MULTIPLY", shaft, 0.5), col, (0.08, 0.08, 0.1))
    # ember: the root, the trailing edge, the leading edge, the deep gaps
    root = g.math("SUBTRACT", 1.0, _smooth(g, v, 0.02, 0.30))
    trail = g.math("MULTIPLY", _smooth(g, u, 0.9, 1.0), _smooth(g, v, 0.45, 0.9))
    tip = g.math("MULTIPLY", _smooth(g, v, 0.93, 1.0), 0.35)
    fire = g.math("ADD", g.math("MULTIPLY", root, 0.8 * glow), g.math("ADD", g.math("MULTIPLY", trail, 0.6 * edge), tip))
    fire = g.math("ADD", fire, g.math("MULTIPLY", _ao(g, 0.45), 0.55 * glow))
    fire = g.math("MINIMUM", fire, 1.0)
    # the fire is dim at its rim and white-orange at its core
    col = g.mix(g.math("MULTIPLY", fire, 0.92), col, EMBER)
    col = g.mix(g.math("MULTIPLY", _smooth(g, fire, 0.65, 1.0), 0.8), col, EMBER_HOT)
    rough = g.math("ADD", 0.38, g.math("MULTIPLY", n1.outputs["Fac"], 0.25))
    height = g.math("ADD", g.math("MULTIPLY", barbs.outputs["Fac"], 0.5), g.math("MULTIPLY", shaft, 0.9))
    return g.finish(col, rough, 0.0, g.bump(height, 0.35, 0.02))


def mat_ember(name="CinderEmber", root=(0.16, 0.025, 0.012)):
    """The crest and the burning ribbons of the tail: dark at the root, ember through the middle, amber at the tip."""
    g = Hm._Graph(name)
    uv = g.coords("UV")
    u, v, _ = g.sep(uv)
    barbs = g.n("ShaderNodeTexWave", **{"Scale": 46.0, "Distortion": 2.0, "Detail": 2.0})
    g.link(uv, barbs.inputs["Vector"])
    col = g.ramp(v, [(0.0, root), (0.18, (0.5, 0.08, 0.012)), (0.5, EMBER), (0.8, EMBER_HOT), (1.0, AMBER)])
    col = g.mix(g.math("MULTIPLY", barbs.outputs["Fac"], 0.35), col, (1.0, 0.5, 0.08))
    mid = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.45)), 9.0), clamp=True)
    col = g.mix(g.math("MULTIPLY", g.math("MULTIPLY", mid, g.math("SUBTRACT", 1.0, v)), 0.5), col, CHARCOAL)
    height = g.math("ADD", g.math("MULTIPLY", barbs.outputs["Fac"], 0.6), g.math("MULTIPLY", mid, 0.6))
    return g.finish(col, 0.5, 0.0, g.bump(height, 0.3, 0.02))


def mat_basalt(name="CinderBasalt", crack_glow=1.0):
    """Cracked basalt armour: grey columns cut by thin molten cracks, ember in the deepest gaps."""
    g = Hm._Graph(name)
    co = g.coords()
    big = g.n("ShaderNodeTexNoise", **{"Scale": 0.9, "Detail": 5.0, "Roughness": 0.65})
    g.link(co, big.inputs["Vector"])
    col = g.ramp(big.outputs["Fac"], [(0.3, (0.035, 0.033, 0.038)), (0.7, (0.12, 0.108, 0.105))])
    cells = g.n("ShaderNodeTexVoronoi", **{"Scale": 1.3, "feature": "DISTANCE_TO_EDGE"})
    g.link(co, cells.inputs["Vector"])
    crack = g.math("SUBTRACT", 1.0, _smooth(g, cells.outputs["Distance"], 0.0, 0.035))
    fine = g.n("ShaderNodeTexNoise", **{"Scale": 11.0, "Detail": 3.0})
    g.link(co, fine.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", fine.outputs["Fac"], 0.32), col, (0.19, 0.17, 0.165))
    glow = g.math("ADD", g.math("MULTIPLY", crack, crack_glow), g.math("MULTIPLY", _ao(g, 0.3), 0.55))
    col = g.mix(g.math("MINIMUM", glow, 1.0), col, EMBER)
    col = g.mix(g.math("MULTIPLY", g.math("MINIMUM", crack, 1.0), 0.9 * crack_glow), col, EMBER_HOT)
    height = g.math("SUBTRACT", g.math("MULTIPLY", big.outputs["Fac"], 0.5), g.math("MULTIPLY", crack, 0.9))
    return g.finish(col, 0.82, 0.0, g.bump(g.math("ADD", height, g.math("MULTIPLY", fine.outputs["Fac"], 0.25)), 0.5, 0.05))


def mat_horn(name="CinderHorn"):
    """Obsidian: near black, glassy, a faint ember warmth where it is thick, banded growth lines."""
    g = Hm._Graph(name)
    co = g.coords()
    lines = g.n("ShaderNodeTexWave", **{"Scale": 3.0, "Distortion": 3.0, "Detail": 3.0})
    g.link(co, lines.inputs["Vector"])
    col = g.ramp(lines.outputs["Fac"], [(0.0, (0.006, 0.006, 0.008)), (0.8, (0.022, 0.02, 0.026)), (1.0, (0.09, 0.05, 0.04))])
    col = g.mix(g.math("MULTIPLY", _ao(g, 0.4), 0.45), col, EMBER)
    return g.finish(col, 0.22, 0.0, g.bump(lines.outputs["Fac"], 0.25, 0.02))


def mat_skin(name="CinderSkin"):
    """The body under its feathers, the head, the beak and the scaled shanks of one mesh, told apart by where they are:
    charcoal down, ember in every deep fold; the beak horn-black with a warm base; the shanks scaled, an ember between the scales."""
    g = Hm._Graph(name)
    co = g.coords()
    # object coordinates are Blender's: x right, y toward the front (Roblox -z), z up (Roblox y)
    x, fwd, h = g.sep(co)
    n1 = g.n("ShaderNodeTexNoise", **{"Scale": 3.0, "Detail": 4.0, "Roughness": 0.6})
    g.link(co, n1.inputs["Vector"])
    ember_body = g.ramp(n1.outputs["Fac"], [(0.3, (0.30, 0.045, 0.008)), (0.75, EMBER)])
    body = g.mix(_smooth(g, h, 18.0, 18.8), ember_body, g.ramp(n1.outputs["Fac"], [(0.3, CHARCOAL), (0.75, SLATE)]))
    scales = g.n("ShaderNodeTexVoronoi", **{"Scale": 2.6, "feature": "DISTANCE_TO_EDGE"})
    g.link(co, scales.inputs["Vector"])
    gap = g.math("SUBTRACT", 1.0, _smooth(g, scales.outputs["Distance"], 0.0, 0.07))
    shank = g.math("SUBTRACT", 1.0, _smooth(g, h, 4.4, 6.2))                          # below the hock
    foot_mask = g.math("MULTIPLY", shank, 1.0)
    scale_col = g.mix(g.math("MULTIPLY", gap, 0.55), (0.02, 0.018, 0.022), EMBER)
    col = g.mix(foot_mask, body, scale_col)
    beak = g.math("MULTIPLY", _smooth(g, h, 16.6, 17.6), _smooth(g, fwd, 10.6, 11.8))
    beak = g.math("MULTIPLY", beak, g.math("SUBTRACT", 1.0, _smooth(g, h, 20.1, 20.6)))
    horn = g.ramp(g.math("MULTIPLY", fwd, 0.07), [(0.70, (0.2, 0.06, 0.012)), (0.80, (0.02, 0.018, 0.022)), (1.0, (0.006, 0.006, 0.008))])
    col = g.mix(beak, col, horn)
    col = g.mix(g.math("MULTIPLY", _ao(g, 0.5), 0.85), col, EMBER)
    rough = g.math("ADD", g.math("MULTIPLY", foot_mask, 0.25), 0.5)
    height = g.math("SUBTRACT", g.math("MULTIPLY", n1.outputs["Fac"], 0.4), g.math("MULTIPLY", g.math("MULTIPLY", gap, foot_mask), 0.7))
    return g.finish(col, rough, 0.0, g.bump(height, 0.4, 0.04))


def mat_arm(name="CinderArm"):
    """The bare arm of a wing under its coverts: charcoal skin, ember in the folds."""
    g = Hm._Graph(name)
    co = g.coords()
    n1 = g.n("ShaderNodeTexNoise", **{"Scale": 4.0, "Detail": 4.0, "Roughness": 0.6})
    g.link(co, n1.inputs["Vector"])
    col = g.ramp(n1.outputs["Fac"], [(0.3, CHARCOAL), (0.75, SLATE)])
    col = g.mix(g.math("MULTIPLY", _ao(g, 0.5), 0.9), col, EMBER)
    return g.finish(col, 0.55, 0.0, g.bump(n1.outputs["Fac"], 0.3, 0.03))


def mat_glow(name, hexcolor):
    """Neon pieces keep their flat colour; this is only for the Blender look."""
    import egg_kit as K
    return K.glow_material(hexcolor)


def all_materials():
    import egg_kit as K
    return {"feather": mat_plumage(), "ember": mat_ember(), "plate": mat_basalt(), "horn": mat_horn(), "skin": mat_skin(), "arm": mat_arm(),
            "tailfeather": mat_ember("CinderTail", root=(0.018, 0.018, 0.022)), "magma": K.glow_material(MAGMA_HEX), "eyes": K.glow_material(EYE_HEX)}


MAGMA_HEX, EYE_HEX, PUPIL_HEX = "ff7a14", "ffa42a", "0a0300"
