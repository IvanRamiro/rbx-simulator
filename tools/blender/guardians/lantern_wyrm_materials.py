"""The Lantern Wyrm's materials: procedural Cycles shaders baked into the four maps (colour, normal, roughness, metalness) of each game piece
(run inside Blender). No letters, no symbols: scales, scutes, horn, a membrane, a gold cup.

Palette: scales of near-black blue-violet with an oil-slick iridescence (each scale takes a teal, blue or violet gleam along its rear
edge and a roughness and metalness of its own: the sheen shifts scale to scale and along the body, shown in the maps and not in a shader),
pale cream ventral scutes (broad belly plates, a snake's: not bone), a smoky translucent violet frill with darker ribs, horns of smoked
violet-black warming to amber at the tips, a lantern of amber gold. The cold dark body against the one WARM gold light is the
creature's identity: no white and gold marble (Dawnspire), no timber and verdigris (Windrift), no black and crimson (Nightfall), no
charcoal and ember orange (the Roc), no indigo and violet-white void veins (the old Pangu).
"""
import bpy

import egg_hi as Hm

NIGHT = (0.004, 0.005, 0.016)          # the scales' ground, linear
INDIGO = (0.010, 0.012, 0.045)
TEAL = (0.010, 0.230, 0.200)           # the oil-slick's gleams
BLUE = (0.020, 0.090, 0.380)
VIOLET = (0.170, 0.035, 0.330)
CREAM = (0.560, 0.470, 0.300)          # the belly's scutes
CREAM_SHADE = (0.200, 0.140, 0.095)
AMBER = (1.0, 0.45, 0.04)
GOLD = (0.80, 0.50, 0.06)
LAMP_HEX, EYE_HEX, RING_HEX = "ffb21a", "ffdf80", "3ad6ff"
UVS = 56.0 / 2048.0                    # uv per stud on the body's map


def _smooth(g, x, lo, hi):
    t = g.math("DIVIDE", g.math("SUBTRACT", x, lo), hi - lo, clamp=True)
    return g.math("MULTIPLY", g.math("MULTIPLY", t, t), g.math("SUBTRACT", 3.0, g.math("MULTIPLY", t, 2.0)))


def _attr(g, name):
    a = g.n("ShaderNodeAttribute", attribute_name=name, attribute_type="GEOMETRY")
    return a.outputs["Fac"]


def _vmul(g, vec, scale):
    n = g.n("ShaderNodeMapping")
    n.inputs["Scale"].default_value = scale
    g.link(vec, n.inputs["Vector"])
    return n.outputs["Vector"]


def _scales(g, vec, ground, bias_hue):
    """Overlapping scales on `vec` (coordinates already scaled so one cell is one scale): returns (colour, dome height 0..1, rear-edge sheen 0..1,
    per-scale random 0..1)."""
    edge = g.n("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE", Scale=1.0)
    g.link(vec, edge.inputs["Vector"])
    cell = g.n("ShaderNodeTexVoronoi", feature="F1", Scale=1.0)
    g.link(vec, cell.inputs["Vector"])
    sep_pos = g.sep(cell.outputs["Position"])
    sep_here = g.sep(vec)
    rnd = g.bw(cell.outputs["Color"])
    # the sheen sits on the scale's rear (free) edge: how far this point is behind its cell's middle along the body
    rear = _smooth(g, g.math("SUBTRACT", sep_pos[1], sep_here[1]), -0.05, 0.42)
    dome = _smooth(g, edge.outputs["Distance"], 0.0, 0.30)
    hue = g.math("ADD", g.math("MULTIPLY", rnd, 0.62), g.math("MULTIPLY", bias_hue, 0.55))
    gleam = g.ramp(g.math("MINIMUM", hue, 1.0), [(0.0, VIOLET), (0.35, BLUE), (0.7, TEAL), (1.0, (0.12, 0.34, 0.16))])
    shade = g.math("MULTIPLY", g.math("ADD", g.math("MULTIPLY", rear, 0.70), 0.06), g.math("ADD", g.math("MULTIPLY", dome, 0.6), 0.4))
    col = g.mix(g.math("MINIMUM", shade, 1.0), ground, gleam)
    return col, dome, rear, rnd


def mat_body(name="LWBody"):
    """The body's skin on its own UVs (isotropic, 56 px a stud): scales pointing back, a darker dorsal stripe with a keel, cream scutes on the belly."""
    g = Hm._Graph(name)
    uv = g.coords("UV")
    along = _attr(g, "Along")              # -1 at the head .. 1 at the tail tip
    belly = _attr(g, "BellyMask")
    dorsal = _attr(g, "DorsalMask")
    vec = _vmul(g, uv, (1.0 / (0.52 * UVS), 1.0 / (0.80 * UVS), 1.0))
    ground = g.mix(g.math("MULTIPLY", along, 0.5), INDIGO, NIGHT)
    hue_bias = g.math("ADD", g.math("MULTIPLY", along, 0.5), 0.5)          # violet toward the head, teal toward the tail
    col, dome, rear, rnd = _scales(g, vec, ground, hue_bias)
    # a darker stripe along the spine, the gleam kept low there
    col = g.mix(g.math("MULTIPLY", dorsal, 0.55), col, NIGHT)
    # the belly: broad scutes across it, cream with a shaded edge, lit by a slow warm-to-cool drift
    band = g.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y", **{"Scale": 0.314 / (0.9 * UVS), "Distortion": 0.4, "Detail": 0.0})
    g.link(uv, band.inputs["Vector"])
    scute_edge = g.math("SUBTRACT", 1.0, _smooth(g, band.outputs["Fac"], 0.0, 0.18))
    fine = g.n("ShaderNodeTexNoise", **{"Scale": 40.0, "Detail": 4.0, "Roughness": 0.6})
    g.link(uv, fine.inputs["Vector"])
    cream = g.mix(g.math("MULTIPLY", fine.outputs["Fac"], 0.5), CREAM, (0.62, 0.50, 0.32))
    cream = g.mix(g.math("MULTIPLY", scute_edge, 0.7), cream, CREAM_SHADE)
    mask = _smooth(g, belly, 0.45, 0.62)
    col = g.mix(mask, col, cream)
    col = g.ao(col, 0.4, 0.55)
    # roughness: glossy scales with a rougher belly; sheen areas smoother. Metalness: a little where the oil-slick sheen is strongest
    rough_v = g.math("ADD", g.math("SUBTRACT", 0.52, g.math("MULTIPLY", rear, 0.26)), g.math("MULTIPLY", mask, 0.14))
    metal = g.math("MULTIPLY", g.math("MULTIPLY", rear, 0.40), g.math("SUBTRACT", 1.0, mask))
    height = g.math("ADD", g.math("MULTIPLY", dome, 0.55), g.math("MULTIPLY", g.math("MULTIPLY", scute_edge, -0.7), mask))
    height = g.math("ADD", height, g.math("MULTIPLY", g.math("MULTIPLY", dome, 1.0), g.math("SUBTRACT", 1.0, mask)))
    return g.finish(col, rough_v, metal, g.bump(height, 0.9, 0.035))


def mat_head(name="LWHead"):
    """The head and the jaw: finer scales on object coordinates, the brow and crown glinting violet and teal, the jaw's underside and the
    lips pale, the nostrils dark."""
    g = Hm._Graph(name)
    co = g.coords()                         # Blender object coordinates: x right, y = -Roblox z (the front +), z = Roblox y
    x, fwd, h = g.sep(co)
    vec = _vmul(g, co, (2.6, 2.6, 2.6))
    low = _smooth(g, g.math("SUBTRACT", 2.0, h), 0.15, 0.7)             # the jaw's underside (below the spine's level)
    ground = g.mix(0.35, INDIGO, NIGHT)
    crown = _smooth(g, g.math("SUBTRACT", h, 2.9), 0.0, 0.8)           # brow and crown
    col, dome, rear, rnd = _scales(g, vec, ground, g.math("ADD", crown, 0.15))
    col = g.mix(g.math("MULTIPLY", low, 0.85), col, CREAM_SHADE)
    col = g.mix(g.math("MULTIPLY", _smooth(g, g.math("SUBTRACT", 2.0, h), 0.5, 1.1), 0.55), col, CREAM)
    col = g.ao(col, 0.25, 0.4)
    rough = g.math("SUBTRACT", 0.5, g.math("MULTIPLY", rear, 0.25))
    metal = g.math("MULTIPLY", rear, 0.4)
    return g.finish(col, rough, metal, g.bump(g.math("MULTIPLY", dome, 1.0), 0.8, 0.02))


def mat_horn(name="LWHorn"):
    """Antler horns and the lantern's stalk: smoked violet-black growth rings, warming to amber toward the tips (by distance from the brow)."""
    g = Hm._Graph(name)
    co = g.coords()
    rings = g.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y", **{"Scale": 0.52, "Distortion": 2.0, "Detail": 2.0})
    uv = g.coords("UV")
    g.link(uv, rings.inputs["Vector"])
    base = g.ramp(rings.outputs["Fac"], [(0.0, NIGHT), (0.6, (0.030, 0.020, 0.060)), (1.0, (0.090, 0.050, 0.100))])
    d = g.n("ShaderNodeVectorMath", operation="DISTANCE")
    d.inputs[1].default_value = (0.0, 24.0, 2.8)
    g.link(co, d.inputs[0])
    tip = _smooth(g, d.outputs["Value"], 4.6, 9.2)
    col = g.mix(g.math("MULTIPLY", tip, 0.95), base, AMBER)
    col = g.ao(col, 0.3, 0.5)
    return g.finish(col, g.math("SUBTRACT", 0.55, g.math("MULTIPLY", tip, 0.2)), g.math("MULTIPLY", tip, 0.25), g.bump(rings.outputs["Fac"], 0.3, 0.01))


def mat_whisker(name="LWWhisker"):
    """The barbels: smoky violet at the root, fading to a pale warm cream at the free end (UV v runs along each)."""
    g = Hm._Graph(name)
    uv = g.coords("UV")
    u, v, _ = g.sep(uv)
    col = g.ramp(g.math("MULTIPLY", v, 0.16), [(0.0, (0.020, 0.018, 0.050)), (0.55, (0.20, 0.17, 0.30)), (1.0, (0.60, 0.50, 0.34))])
    return g.finish(col, 0.45, 0.0)


def mat_cup(name="LWCup"):
    g = Hm._Graph(name)
    co = g.coords()
    n1 = g.n("ShaderNodeTexNoise", **{"Scale": 14.0, "Detail": 3.0})
    g.link(co, n1.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", n1.outputs["Fac"], 0.6), (0.50, 0.30, 0.04), (0.9, 0.6, 0.12))
    return g.finish(col, 0.3, 0.9, g.bump(n1.outputs["Fac"], 0.2, 0.01))


def mat_tooth(name="LWTooth"):
    g = Hm._Graph(name)
    return g.finish(g.mix(0.0, (0.62, 0.55, 0.40), (0.62, 0.55, 0.40)), 0.4, 0.0)


def mat_frill(name="LWFrill"):
    """The mane's membrane (index 0) and its ribs (index 1): a smoky violet whose fine radial veins run from each rib's root to the edge, paler and
    cooler at the free edge; ribs near-black with a faint violet sheen. UV: u across the fan (0..1 along the frill), v from the root to the edge."""
    g = Hm._Graph(name)
    uv = g.coords("UV")
    u, v, _ = g.sep(uv)
    veins = g.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", **{"Scale": 17.0, "Distortion": 3.0, "Detail": 1.0, "Detail Scale": 1.4})
    g.link(uv, veins.inputs["Vector"])
    smoke = g.n("ShaderNodeTexNoise", **{"Scale": 6.0, "Detail": 5.0, "Roughness": 0.6})
    g.link(g.coords(), smoke.inputs["Vector"])
    root = (0.030, 0.012, 0.075)
    mid = (0.080, 0.035, 0.180)
    edge = (0.170, 0.120, 0.400)
    col = g.ramp(g.math("MULTIPLY", v, 1.0), [(0.0, root), (0.45, mid), (1.0, edge)])
    col = g.mix(g.math("MULTIPLY", veins.outputs["Fac"], 0.35), col, (0.012, 0.006, 0.030))
    col = g.mix(g.math("MULTIPLY", smoke.outputs["Fac"], 0.35), col, (0.30, 0.10, 0.40))
    rib_col = g.mix(0.4, (0.006, 0.005, 0.020), (0.050, 0.030, 0.110))
    mat_index = g.n("ShaderNodeAttribute", attribute_name="RibMask", attribute_type="GEOMETRY")
    col = g.mix(mat_index.outputs["Fac"], col, rib_col)
    rough = g.math("ADD", 0.45, g.math("MULTIPLY", smoke.outputs["Fac"], 0.2))
    return g.finish(col, rough, g.math("MULTIPLY", g.math("SUBTRACT", 1.0, mat_index.outputs["Fac"]), 0.12), g.bump(g.math("ADD", veins.outputs["Fac"], mat_index.outputs["Fac"]), 0.35, 0.01))


def all_materials():
    import egg_kit as K
    return {"body": mat_body(), "head": mat_head(), "horn": mat_horn(), "whisker": mat_whisker(), "cup": mat_cup(), "tooth": mat_tooth(), "frill": mat_frill(),
            "lamp": K.glow_material(LAMP_HEX), "eyes": K.glow_material(EYE_HEX), "rings": K.glow_material(RING_HEX)}
