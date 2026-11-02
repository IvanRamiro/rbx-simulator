"""Pangu, the World-Splitter, Origin Abyss's guardian (run inside Blender). The idea: in the myth,
Pangu hatched from the cosmic egg and split the chaos inside it into heaven and earth with his axe.
Here he is a titan of dark stone still cracked with the chaos he came from (violet void light
seeping through every fissure, a crack of it splitting his brow), a mane and a mantle of void
drifting from him like smoke, great curved horns, a carved stone beard bound in bronze, and a
bronze belt with the disc of yin and yang: the split he made. The world-splitting axe rests on his
right shoulder, its edge alight with void; in his open left palm, before his chest, he holds the
egg, the cosmic egg he was born from. The island's rift is his axe stroke.

About 36 studs to his crown, 43 to his horns' tips. Built from rigid segments the game turns with
Motor6D joints: Body (the pelvis), Chest (with the mantle), Head, an UpperArm and a Forearm per arm
(the right forearm holds the axe) and a Thigh and a Shin per leg. The glowing pieces (the void in
his cracks, his eyes and their pupils, the axe's edge) are Neon pieces riding their segment.

Authored in Roblox studs, standing, facing -Z, his feet on the ground at y = 0.

    import pangu as P
    P.build()                     # the high-detail segments, in collection PanguHi
    P.bake(names)                 # bake those segments (a few per call: the connection drops on long runs)
    P.export()                    # assets/guardians/Pangu.fbx and its pieces report
"""
import math
import random

import bpy
from mathutils import Vector

import egg_bake as B
import egg_hi as Hm
import egg_kit as K
import guardian_kit as G

W = K.W
V = Vector
TAU = 2 * math.pi
NAME = "Pangu"
VOID = "8c28ff"          # the void in his cracks and on his axe's edge (the island's void core colour)
EYE = "9a64ff"           # his eyes: starlit violet
PUPIL = "06020c"         # dark Neon renders as a flat black

LIFT = 2.5                           # everything above his hips is authored 2.5 lower and lifted in build(): longer legs
EGG_AT = V((-5.9, 23.3 + LIFT, -6.6))   # the cosmic egg's centre, on his open left palm (as built)

# segment: (parent, pivot): where it turns on its parent (Roblox studs)
AUTHORED = {   # segment: (parent, pivot) as authored (above the hips, before the lift)
    "Body": (None, (0.0, 15.5, 0.0)),
    "Chest": ("Body", (0.0, 18.6, 0.2)),
    "Head": ("Chest", (0.0, 30.2, -0.2)),
    "LeftUpperArm": ("Chest", (-7.0, 28.4, 0.2)),
    "LeftForearm": ("LeftUpperArm", (-8.6, 21.6, 1.2)),
    "RightUpperArm": ("Chest", (7.0, 28.4, 0.2)),
    "RightForearm": ("RightUpperArm", (8.8, 21.6, 1.0)),
}
LEGS = {"hip": (3.2, 15.2 + LIFT, 0.2), "knee": (3.5, 9.4, -0.5), "ankle": (3.6, 2.0, 0.3)}
PIVOTS = {name: (parent, (p[0], p[1] + LIFT, p[2])) for name, (parent, p) in AUTHORED.items()}
for _side, _s in ((-1, "Left"), (1, "Right")):
    PIVOTS[_s + "Thigh"] = ("Body", (_side * LEGS["hip"][0], LEGS["hip"][1], LEGS["hip"][2]))
    PIVOTS[_s + "Shin"] = (_s + "Thigh", (_side * LEGS["knee"][0], LEGS["knee"][1], LEGS["knee"][2]))
LIFTED = set(AUTHORED)


# ---------- materials ----------
def mat_stone(name="PanguStone"):
    """The titan's stone: dark slate with a violet cast, cut by fracture lines (Voronoi edges),
    void light glowing faintly in its deepest crevices (ambient occlusion turned to violet), dust
    settled on its upper faces."""
    g = Hm._Graph(name)
    co = g.coords()
    big = g.n("ShaderNodeTexNoise", **{"Scale": 0.45, "Detail": 5.0, "Roughness": 0.6})
    g.link(co, big.inputs["Vector"])
    col = g.ramp(big.outputs["Fac"], [(0.3, (0.035, 0.03, 0.045)), (0.7, (0.1, 0.09, 0.12))])
    cells = g.n("ShaderNodeTexVoronoi", **{"Scale": 0.9, "feature": "DISTANCE_TO_EDGE"})
    g.link(co, cells.inputs["Vector"])
    crack = g.math("LESS_THAN", cells.outputs["Distance"], 0.03)
    col = g.mix(g.math("MULTIPLY", crack, 0.85), col, (0.012, 0.008, 0.02))
    fine = g.n("ShaderNodeTexNoise", **{"Scale": 9.0, "Detail": 3.0})
    g.link(co, fine.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", fine.outputs["Fac"], 0.3), col, (0.16, 0.15, 0.18))
    geo = g.n("ShaderNodeNewGeometry")
    up = g.sep(geo.outputs["Normal"])[2]
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", up, 0.55, clamp=True), 0.6), col, (0.2, 0.19, 0.21))
    ao = g.n("ShaderNodeAmbientOcclusion", samples=16, only_local=True)
    ao.inputs["Distance"].default_value = 0.35
    deep = g.math("POWER", g.math("SUBTRACT", 1.0, ao.outputs["AO"], clamp=True), 1.2)
    col = g.mix(g.math("MINIMUM", g.math("MULTIPLY", deep, 1.3), 0.8), col, (0.22, 0.05, 0.42))
    height = g.math("SUBTRACT", g.math("MULTIPLY", big.outputs["Fac"], 0.6), g.math("MULTIPLY", crack, 0.5))
    return g.finish(col, 0.74, 0.0, g.bump(g.math("ADD", height, g.math("MULTIPLY", fine.outputs["Fac"], 0.3)), 0.4, 0.04))


def mat_void(name="PanguVoid"):
    """Chaos as smoke: near black at a wisp's root, deep violet along it, a bright violet tip (UV v)."""
    g = Hm._Graph(name)
    _, v, _ = g.sep(g.coords("UV"))
    col = g.ramp(v, [(0.0, (0.012, 0.004, 0.03)), (0.55, (0.12, 0.025, 0.3)), (1.0, (0.42, 0.14, 0.95))])
    return g.finish(col, 0.55, 0.0)


def mat_horn(name="PanguHorn"):
    """Horn: near-black, ridged with growth lines, a violet sheen at the ridges."""
    g = Hm._Graph(name)
    co = g.coords()
    lines = g.n("ShaderNodeTexWave", **{"Scale": 2.5, "Distortion": 2.0, "Detail": 3.0})
    g.link(co, lines.inputs["Vector"])
    col = g.ramp(lines.outputs["Fac"], [(0.0, (0.01, 0.008, 0.014)), (0.8, (0.05, 0.04, 0.07)), (1.0, (0.12, 0.07, 0.2))])
    col = g.ao(col, 0.2, 0.5)
    return g.finish(col, 0.42, 0.0, g.bump(lines.outputs["Fac"], 0.3, 0.02))


def mat_plain(name, color, rough, metal=0.0):
    g = Hm._Graph(name)
    co = g.coords()
    n = g.n("ShaderNodeTexNoise", **{"Scale": 5.0, "Detail": 4.0})
    g.link(co, n.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", n.outputs["Fac"], 0.3), color, tuple(min(1.0, c * 1.7) for c in color))
    col = g.ao(col, 0.15, 0.45)
    return g.finish(col, rough, metal, g.bump(n.outputs["Fac"], 0.2, 0.01))


def materials():
    return {"stone": mat_stone(), "void": mat_void(), "horn": mat_horn(), "bronze": Hm.mat_bronze("PanguBronze"),
            "cloth": mat_plain("PanguCloth", (0.03, 0.014, 0.06), 0.8), "haft": mat_plain("PanguHaft", (0.05, 0.03, 0.022), 0.6),
            "yang": mat_plain("PanguYang", (0.62, 0.6, 0.56), 0.35), "yin": mat_plain("PanguYin", (0.012, 0.01, 0.016), 0.3),
            "blade": mat_plain("PanguBlade", (0.022, 0.019, 0.03), 0.5)}


# ---------- shapes ----------
cone, sphere, frame, wisp, limb, soften = G.cone, G.sphere, G.frame, G.wisp, G.limb, G.soften


def keep(o):
    o["keep"] = True
    return o


def stone_blob(name, coll, M, lobes, voxel=0.12, smooth=14):
    return soften(G.blob(name, coll, M["stone"], lobes, voxel=voxel, smooth=0.7, rough=0.06, chisel="PanguChisel"), smooth)


def band(hi, centre, axis, radius, thick=0.25, mat=0):
    """A bronze band round a limb."""
    n, s, t = frame(axis)
    ring = [V(centre) + (s * math.cos(TAU * i / 24) + t * math.sin(TAU * i / 24)) * radius for i in range(24)]
    Hm.htube(hi, ring + ring[:2], lambda q: thick, sides=6, per=1, mat=mat, uv_scale=2.0, tip=False, wobble=0.0)


def vein_starts(rnd, centre, spread, count):
    return [(V(centre) + V((rnd.uniform(-1, 1) * spread[0], rnd.uniform(-1, 1) * spread[1], rnd.uniform(-1, 1) * spread[2])),
             V((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 0.3)))) for _ in range(count)]


# ---------- the segments ----------
def body(coll, M):
    flesh = stone_blob("PG_Body", coll, M, [((0, 15.8, 0.2), (3.9, 2.4, 2.8), None), ((-2.8, 14.8, 0.2), (2.0, 2.2, 2.3), None),
                                             ((2.8, 14.8, 0.2), (2.0, 2.2, 2.3), None), ((0, 17.4, 0.2), (3.6, 1.4, 2.7), None),
                                             ((-3.2, 13.0, 0.2), (1.9, 1.6, 2.1), None), ((3.2, 13.0, 0.2), (1.9, 1.6, 2.1), None)])
    bronze, disc, cloth, glow = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    # the belt, and before it the disc of yin and yang
    ring = [V((3.95 * math.sin(TAU * i / 40), 17.2, 0.2 - 2.95 * math.cos(TAU * i / 40))) for i in range(40)]
    Hm.htube(bronze, ring + ring[:2], lambda q: 0.55, sides=8, per=1, uv_scale=2.0, tip=False, wobble=0.0)
    c, r = V((0, 16.9, -3.45)), 1.55
    Hm.htube(bronze, [c + V((r * math.cos(TAU * i / 32), r * math.sin(TAU * i / 32), 0)) for i in range(34)], lambda q: 0.22, sides=8, per=1,
             uv_scale=2.0, tip=False, wobble=0.0)
    rings, wedges = 10, 48

    def yang(x, y):
        """The taiji: the lower small circle is yang, the upper yin, and of the rest the right half."""
        up, down = math.hypot(x, y - r / 2) < r / 2, math.hypot(x, y + r / 2) < r / 2
        return down or (x > 0 and not up)

    pts = [[disc.v(c + V((r * k / rings * math.cos(TAU * i / wedges), r * k / rings * math.sin(TAU * i / wedges), -0.1))) for i in range(wedges)]
           for k in range(rings + 1)]
    for k in range(rings):
        for i in range(wedges):
            j = (i + 1) % wedges
            rr, am = r * (k + 0.5) / rings, TAU * (i + 0.5) / wedges
            mat = 0 if yang(rr * math.cos(am), rr * math.sin(am)) else 1
            disc.facing([pts[k][i], pts[k + 1][i], pts[k + 1][j], pts[k][j]], [(0, 0), (1, 0), (1, 1), (0, 1)], (0, 0, -1), mat)
    for dy, mat in ((r / 2, 0), (-r / 2, 1)):          # each lobe holds a dot of the other
        sphere(disc, c + V((0, dy, -0.16)), 0.22, nu=10, nv=6, radii=(0.22, 0.22, 0.06), mat=mat)
    # his loincloth, front and back: hangings of chaos-dark cloth
    for z, sign in ((-3.0, -1), (3.1, 1)):
        for x, length, width in ((0, 10.5, 2.2), (-1.9, 8.0, 1.5), (1.9, 8.3, 1.5)):       # torn into strips
            Hm.leaf(cloth, (x, 16.4, z), (x * 0.03, -1, sign * 0.1), (0, 0, sign), length, width, mat=0, fold=0.08, curl=0.04,
                    twist=x * 0.04, steps=12, across=3, shape=0.85)
    G.veins(glow, flesh, vein_starts(random.Random(3), (0, 15.5, 0.2), (3.5, 1.5, 2.5), 5), random.Random(4), steps=8, radius=0.14)
    d = disc.object("PG_BodyDisc", coll, [M["yang"], M["yin"]])
    cl = cloth.object("PG_BodyCloth", coll, [M["cloth"]])
    Hm.solidify(cl, 0.12)
    cl["sheet"] = True
    return [flesh, keep(bronze.object("PG_BodyBronze", coll, [M["bronze"]])), keep(d), cl], \
        {VOID: [glow.object("PG_BodyVoid", coll, [K.glow_material(VOID)], smooth=True)]}


def chest(coll, M):
    lobes = [((0, 20.0, 0.2), (3.3, 2.6, 2.5), None), ((0, 23.8, 0.0), (5.4, 3.6, 3.4), None),
             ((-2.6, 25.4, -1.8), (2.6, 2.0, 1.6), None), ((2.6, 25.4, -1.8), (2.6, 2.0, 1.6), None),
             ((-5.6, 27.6, 0.2), (2.6, 2.2, 2.4), None), ((5.6, 27.6, 0.2), (2.6, 2.2, 2.4), None),
             ((0, 28.6, 0.2), (2.4, 1.8, 2.0), None), ((0, 24.5, 1.6), (4.6, 4.0, 2.5), None), ((0, 21.8, -1.1), (2.8, 2.0, 1.5), None)]
    flesh = stone_blob("PG_Chest", coll, M, lobes, voxel=0.13, smooth=18)
    mantle, glow = Hm.Hi(), Hm.Hi()
    rnd = random.Random(11)
    # the mantle: chaos drifting from his shoulders and down his back like smoke
    for layer, (y0, z0, count, lengths, width) in enumerate(((28.6, 1.6, 26, (10.0, 15.0), (0.7, 1.0)), (27.0, 2.6, 22, (8.0, 12.0), (0.55, 0.8)))):
        for k in range(count):
            q = k / (count - 1)
            x = -6.6 + 13.2 * q + rnd.uniform(-0.3, 0.3)
            base = V((x, y0 - 1.4 * abs(x) / 6.6 + rnd.uniform(-0.3, 0.3), z0 + 0.5 * abs(x) / 6.6))
            d = V((x * 0.03, -1, 0.16 + rnd.uniform(0, 0.12)))                  # draped down his back, a little away from it
            wisp(mantle, base, d, V((x * 0.05, 0.1, 1)), rnd.uniform(*lengths), rnd.uniform(*width), rnd, sides=7)
    for k in range(10):                                   # and up off his shoulders
        side = -1 if k % 2 else 1
        base = V((side * rnd.uniform(4.5, 7.5), 29.6, rnd.uniform(-0.5, 1.5)))
        wisp(mantle, base, V((side * 0.3, 1, 0.5)), V((0, 0.3, 1)), rnd.uniform(2.5, 4.5), 0.35, rnd, sides=5)
    G.veins(glow, flesh, vein_starts(random.Random(5), (0, 24, -1), (4.5, 3.5, 2.5), 9), random.Random(6), steps=12, radius=0.17)
    return [flesh, keep(mantle.object("PG_ChestMantle", coll, [M["void"]]))], \
        {VOID: [glow.object("PG_ChestVoid", coll, [K.glow_material(VOID)], smooth=True)]}


def head(coll, M):
    skull = stone_blob("PG_Head", coll, M, [
        ((0, 32.6, -0.3), (2.5, 2.9, 2.7), None), ((0, 33.55, -2.35), (2.4, 0.7, 0.9), None),            # the skull, the heavy brow
        ((-1.5, 32.0, -2.0), (0.9, 0.8, 0.8), None), ((1.5, 32.0, -2.0), (0.9, 0.8, 0.8), None),          # cheekbones
        ((0, 30.8, -1.5), (1.9, 1.3, 1.8), None), ((0, 32.4, -2.9), (0.45, 0.9, 0.5), None),              # the jaw, the nose
        ((0, 30.0, 0.0), (1.6, 1.4, 1.6), None)], voxel=0.07, smooth=8)
    eyes, pupils, lids, horns, bronze, beard, mane, glow = (Hm.Hi() for _ in range(8))
    for side in (-1, 1):
        normal = V((side * 0.4, 0.04, -0.92)).normalized()
        seat = G.surface_along(skull, V((side * 0.95, 32.85, -2.4)), normal)
        # a titan's stare: deep under the brow, the lids heavy and level, stern rather than wild
        G.eye(eyes, pupils, lids, seat, normal, (-side * 0.6, 0, -1), 0.56, 0.27, tilt=0.12, bulge=0.1, lid=0.5, droop=0.42, lower=0.22,
              slit=0.3, pupil_height=0.5)
        base = V((side * 2.0, 34.6, -0.6))
        pts = [base, base + V((side * 1.8, 1.6, 0.6)), base + V((side * 3.4, 3.8, 1.8)), base + V((side * 3.6, 6.2, 1.2)),
               base + V((side * 2.8, 7.6, -0.4))]
        Hm.htube(horns, pts, lambda q: 0.85 * (1 - 0.88 * q), sides=12, per=6, uv_scale=1.0, tip=True, wobble=0.0)
        band(bronze, base + V((side * 1.0, 0.8, 0.3)), V((side * 1.8, 1.6, 0.6)), 0.82, 0.16)
    # the crack of chaos splitting his brow
    brow = [V((0, 35.2, -2.1)), V((0.12, 34.5, -2.55)), V((-0.08, 33.9, -2.8))]
    Hm.htube(glow, brow, lambda q: 0.13 * (1 - 0.5 * q), sides=6, per=4, uv_scale=1.0, tip=True, wobble=0.0)
    # the beard: five stone braids, bound in bronze
    rnd = random.Random(13)
    # the beard: broad from jaw to jaw beneath the mouth, sideburns up to the ears, tapering below the chin
    beard_mass = soften(G.blob("PG_HeadBeardMass", coll, M["stone"], [
        ((0, 29.7, -2.2), (2.1, 1.0, 1.05), None), ((-1.75, 30.6, -1.4), (0.75, 1.5, 0.9), None), ((1.75, 30.6, -1.4), (0.75, 1.5, 0.9), None),
        ((0, 28.5, -2.5), (1.6, 1.3, 0.95), None), ((0, 27.4, -2.65), (1.1, 1.1, 0.8), None)], voxel=0.07, smooth=0.7, rough=0.05,
        chisel="PanguChisel"), 6)
    for side in (-1, 1):                                          # a moustache sweeping down into it
        Hm.htube(beard, [(side * 0.2, 31.4, -3.2), (side * 0.9, 31.0, -3.15), (side * 1.4, 30.3, -2.9), (side * 1.55, 29.5, -2.55)],
                 lambda q: 0.32 * (1 - 0.65 * q), sides=8, per=4, uv_scale=1.0, tip=True, wobble=0.3, seed=7 + side)
    # his mouth: a seam of the chaos inside him
    Hm.htube(glow, [V((-0.75, 30.95, -3.0)), V((0, 30.85, -3.2)), V((0.75, 30.95, -3.0))], lambda q: 0.08, sides=6, per=4, uv_scale=1.0,
             tip=True, wobble=0.0)
    for k, x in enumerate((-0.75, 0.0, 0.75)):                    # three braided ends, bound in bronze
        top = V((x, 27.4, -2.8))
        pts = [top, top + V((x * 0.15, -1.2, -0.15)), top + V((x * 0.25, -2.4, 0.05))]
        Hm.htube(beard, pts, lambda q: 0.4 * (1 - 0.55 * q), sides=8, per=4, uv_scale=1.0, tip=True, wobble=0.4, seed=k)
        band(bronze, top + V((x * 0.1, -0.7, -0.08)), V((0, -1, 0.05)), 0.4, 0.11)
    # the mane: chaos drifting up and back off his head
    for k in range(22):
        a = math.pi * (0.1 + 0.8 * k / 21)
        base = V((2.2 * math.cos(a), 33.4 + 1.6 * math.sin(a), 1.2 + 0.4 * math.sin(a)))
        wisp(mane, base, V((math.cos(a) * 0.4, 0.5, 1)), V((0, 1, 0.2)), rnd.uniform(3.5, 6.0), rnd.uniform(0.35, 0.5), rnd, sides=6)
    return [skull, keep(lids.object("PG_HeadLids", coll, [M["stone"]])), keep(horns.object("PG_HeadHorns", coll, [M["horn"]])),
            keep(bronze.object("PG_HeadBronze", coll, [M["bronze"]])), keep(beard.object("PG_HeadBeard", coll, [M["stone"]])), beard_mass,
            keep(mane.object("PG_HeadMane", coll, [M["void"]]))], \
        {EYE: [eyes.object("PG_Eyes", coll, [K.glow_material(EYE)], smooth=True)],
         PUPIL: [pupils.object("PG_Pupils", coll, [K.glow_material(PUPIL)], smooth=True)],
         VOID: [glow.object("PG_HeadVoid", coll, [K.glow_material(VOID)], smooth=True)]}


def upper_arm(coll, M, side):
    name = ("Left" if side < 0 else "Right") + "UpperArm"
    sh = V(AUTHORED[name][1])                       # authored positions: build() lifts the arm with the rest
    el = V(AUTHORED[("Left" if side < 0 else "Right") + "Forearm"][1])
    flesh = stone_blob("PG_" + name, coll, M,
                       limb(sh + V((-side * 0.3, 0.6, 0)), el, 2.0, 1.55) + [(tuple(sh + V((side * 0.4, -0.6, 0))), (2.3, 2.1, 2.3), None)])
    bronze, glow = Hm.Hi(), Hm.Hi()
    band(bronze, sh.lerp(el, 0.62), el - sh, 1.75, 0.22)
    G.veins(glow, flesh, vein_starts(random.Random(7 + side), sh.lerp(el, 0.4), (1.2, 2.5, 1.2), 3), random.Random(8 + side), steps=8, radius=0.13)
    return [flesh, keep(bronze.object("PG_" + name + "Bronze", coll, [M["bronze"]]))], \
        {VOID: [glow.object("PG_" + name + "Void", coll, [K.glow_material(VOID)], smooth=True)]}


def left_forearm(coll, M):
    el, wr = V((-8.6, 21.6, 1.2)), V((-6.5, 21.0, -4.8))
    palm = V((-5.9, 20.95, -6.5))
    lobes = limb(el, wr, 1.6, 1.2) + [(tuple(palm), (1.5, 0.6, 1.6), None)]
    # fingers curling up round the egg, the thumb on the near side
    tips = []
    for k in range(4):
        a = math.radians(-60 + 40 * k)
        root = palm + V((math.sin(a) * 1.2, 0.2, -math.cos(a) * 1.25))
        mid = root + V((math.sin(a) * 0.9, 0.9, -math.cos(a) * 0.9))
        tip = mid + V((-math.sin(a) * 0.15, 0.9, math.cos(a) * 0.3))
        lobes += limb(root, mid, 0.42, 0.38) + limb(mid, tip, 0.38, 0.3)
        tips.append(tip)
    thumb_root = palm + V((1.3, 0.25, 0.5))
    lobes += limb(thumb_root, thumb_root + V((0.6, 1.1, -0.6)), 0.45, 0.36)
    flesh = stone_blob("PG_LeftForearm", coll, M, lobes, voxel=0.08, smooth=8)
    bronze, glow = Hm.Hi(), Hm.Hi()
    for q in (0.25, 0.55):
        band(bronze, el.lerp(wr, q), wr - el, 1.5 - 0.25 * q, 0.22)
    G.veins(glow, flesh, vein_starts(random.Random(21), el.lerp(wr, 0.5), (1.0, 1.0, 2.0), 3), random.Random(22), steps=7, radius=0.12)
    return [flesh, keep(bronze.object("PG_LeftForearmBronze", coll, [M["bronze"]]))], \
        {VOID: [glow.object("PG_LeftForearmVoid", coll, [K.glow_material(VOID)], smooth=True)]}


# the axe: its haft runs from the pommel, below his fist, up over his right shoulder; its head
# rests behind the shoulder, the edge turned up and forward so the swing brings it down in front
FIST = V((7.3, 24.6, -4.4))
SHOULDER_TOP = V((7.2, 30.8, 0.4))
HAFT = (SHOULDER_TOP - FIST).normalized()
EDGE_DIR = V((0, HAFT.z, -HAFT.y)).normalized() if V((0, HAFT.z, -HAFT.y)).y > 0 else -V((0, HAFT.z, -HAFT.y)).normalized()
AXE_HEAD = FIST + HAFT * 12.2


def right_forearm(coll, M):
    el = V((8.8, 21.6, 1.0))
    wr = FIST + V((0.2, -1.0, 0.9))
    lobes = limb(el, wr, 1.6, 1.25) + [(tuple(FIST), (1.25, 1.35, 1.25), None)]
    flesh = stone_blob("PG_RightForearm", coll, M, lobes, voxel=0.08, smooth=8)
    bronze, haft, blade, glow = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    for q in (0.3, 0.6):
        band(bronze, el.lerp(wr, q), wr - el, 1.5 - 0.2 * q, 0.22)
    pommel = FIST - HAFT * 5.0
    top = FIST + HAFT * 14.5
    Hm.htube(haft, [pommel, FIST, top], lambda q: 0.48, sides=10, per=2, uv_scale=1.0, tip=False, wobble=0.0)
    for at in (pommel, pommel + HAFT * 0.4, FIST + HAFT * 3.0, AXE_HEAD - HAFT * 2.2, top):
        band(bronze, at, HAFT, 0.55, 0.16)
    sphere(bronze, pommel - HAFT * 0.3, 0.75, nu=12, nv=8)
    # the head: a great bearded crescent of black stone, thick at its socket, thinning to its edge
    s = HAFT.cross(EDGE_DIR).normalized()
    pt = lambda a, b: AXE_HEAD + HAFT * a + EDGE_DIR * b
    outline = [(-2.6, 0.55), (-1.3, 0.5), (0.0, 0.5), (1.3, 0.5), (2.6, 0.55), (3.2, 1.6), (3.9, 3.7)]
    edge = [(3.9 * (1 - 2 * i / 16), 3.7 + 1.7 * (1 - (1 - 2 * i / 16) ** 2)) for i in range(17)]
    outline += edge[1:-1] + [(-3.9, 3.7), (-3.2, 1.6)]
    centre = pt(0, 2.4)
    thick = lambda b: 0.42 * max(0.15, 1 - max(0.0, b - 2.6) / 2.6)
    rim_f = [blade.v(pt(a, b) + s * thick(b)) for a, b in outline]
    rim_b = [blade.v(pt(a, b) - s * thick(b)) for a, b in outline]
    cf, cb = blade.v(centre + s * 0.45), blade.v(centre - s * 0.45)
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        blade.facing([cf, rim_f[i], rim_f[j]], [(0.5, 0.5), (0, 0), (1, 0)], tuple(s))
        blade.facing([cb, rim_b[j], rim_b[i]], [(0.5, 0.5), (0, 0), (1, 0)], tuple(-s))
        a0, b0 = outline[i]
        a1, b1 = outline[j]
        mid_out = (pt((a0 + a1) / 2, (b0 + b1) / 2) - centre).normalized()
        blade.facing([rim_f[i], rim_b[i], rim_b[j], rim_f[j]], [(0, 0), (0, 1), (1, 1), (1, 0)], tuple(mid_out))
    # its socket on the haft, and a spike behind
    Hm.htube(bronze, [AXE_HEAD - HAFT * 2.0, AXE_HEAD + HAFT * 2.0], lambda q: 0.85, sides=10, per=2, uv_scale=1.0, tip=False, wobble=0.0)
    cone(blade, AXE_HEAD - EDGE_DIR * 0.6, AXE_HEAD - EDGE_DIR * 2.8 + HAFT * 0.4, 0.5, sides=8)
    # the void along its edge
    Hm.htube(glow, [pt(a, b + 0.05) for a, b in edge], lambda q: 0.14, sides=6, per=2, uv_scale=1.0, tip=False, wobble=0.0)
    G.veins(glow, flesh, vein_starts(random.Random(31), el.lerp(wr, 0.5), (1.0, 1.0, 1.5), 3), random.Random(32), steps=7, radius=0.12)
    return [flesh, keep(bronze.object("PG_RightForearmBronze", coll, [M["bronze"]])), keep(haft.object("PG_RightForearmHaft", coll, [M["haft"]])),
            keep(blade.object("PG_RightForearmBlade", coll, [M["stone"]], smooth=False))], \
        {VOID: [glow.object("PG_RightForearmVoid", coll, [K.glow_material(VOID)], smooth=True)]}


def thigh(coll, M, side):
    hip, knee = (V((side * p[0], p[1], p[2])) for p in (LEGS["hip"], LEGS["knee"]))
    name = ("Left" if side < 0 else "Right") + "Thigh"
    flesh = stone_blob("PG_" + name, coll, M, limb(hip + V((0, 0.6, 0)), knee, 2.25, 1.55) +
                       [(tuple(hip.lerp(knee, 0.4) + V((0, 0, -0.7))), (1.85, 2.9, 1.6), None)])
    glow = Hm.Hi()
    G.veins(glow, flesh, vein_starts(random.Random(41 + side), hip.lerp(knee, 0.5), (1.5, 2.5, 1.5), 3), random.Random(42 + side), steps=8,
            radius=0.14)
    return [flesh], {VOID: [glow.object("PG_" + name + "Void", coll, [K.glow_material(VOID)], smooth=True)]}


def shin(coll, M, side):
    knee, ankle = (V((side * p[0], p[1], p[2])) for p in (LEGS["knee"], LEGS["ankle"]))
    name = ("Left" if side < 0 else "Right") + "Shin"
    lobes = limb(knee, ankle, 1.55, 1.05) + [(tuple(knee.lerp(ankle, 0.3) + V((0, 0, 0.75))), (1.35, 2.4, 1.3), None)]   # the calf
    lobes += [(tuple(ankle + V((0, -1.1, 0.5))), (1.3, 0.9, 1.4), None), (tuple(ankle + V((0, -1.2, -1.9))), (1.6, 0.8, 1.7), None)]
    flesh = stone_blob("PG_" + name, coll, M, lobes, voxel=0.1, smooth=10)
    bronze, glow = Hm.Hi(), Hm.Hi()
    for q in (0.55, 0.8):
        band(bronze, knee.lerp(ankle, q), ankle - knee, 1.3 - 0.25 * q, 0.2)
    G.veins(glow, flesh, vein_starts(random.Random(51 + side), knee.lerp(ankle, 0.4), (1.2, 2.0, 1.2), 2), random.Random(52 + side), steps=7,
            radius=0.12)
    return [flesh, keep(bronze.object("PG_" + name + "Bronze", coll, [M["bronze"]]))], \
        {VOID: [glow.object("PG_" + name + "Void", coll, [K.glow_material(VOID)], smooth=True)]}


def segments():
    return {"Body": body, "Chest": chest, "Head": head,
            "LeftUpperArm": lambda c, M: upper_arm(c, M, -1), "RightUpperArm": lambda c, M: upper_arm(c, M, 1),
            "LeftForearm": left_forearm, "RightForearm": right_forearm,
            "LeftThigh": lambda c, M: thigh(c, M, -1), "RightThigh": lambda c, M: thigh(c, M, 1),
            "LeftShin": lambda c, M: shin(c, M, -1), "RightShin": lambda c, M: shin(c, M, 1)}


BUDGET = {"Body": 8000, "Chest": 16000, "Head": 16000, "LeftUpperArm": 5000, "RightUpperArm": 5000, "LeftForearm": 6000,
          "RightForearm": 8000, "LeftThigh": 5000, "RightThigh": 5000, "LeftShin": 5000, "RightShin": 5000}


def build(only=None):
    M = materials()
    root = W.collection(NAME + "Hi")
    out = {}
    for name, fn in segments().items():
        if only and name not in only:
            continue
        coll = W.collection(NAME + "_" + name, root)
        W.clear_collection(coll)
        hi, glow = fn(coll, M)
        for hexstr, objs in glow.items():
            assert len(objs) == 1, "one glow piece per colour per segment"
            objs[0].name = NAME + "_" + name + "_Glow_" + hexstr
        if name in LIFTED:
            for o in list(hi) + [o for objs in glow.values() for o in objs]:
                o.data.transform(__import__("mathutils").Matrix.Translation(W.rb(0, LIFT, 0)))
        out[name] = (hi, glow, coll)
    return out


def bake(names):
    """Bakes these segments' game meshes (built already); records them for export()."""
    parts = bpy.app.driver_namespace.setdefault("pangu_parts", {})
    for name in names:
        coll = bpy.data.collections[NAME + "_" + name]
        hi = [o for o in coll.objects if o.name.startswith("PG_") and o.type == "MESH"]
        low = G.bake_piece(NAME, name, hi, coll, BUDGET.get(name, 5000))
        parts[name] = (name, low.name)
    return {n: B.tris(bpy.data.objects[parts[n][1]]) for n in names}


def export():
    return G.export(NAME, PIVOTS, bpy.app.driver_namespace["pangu_parts"])
