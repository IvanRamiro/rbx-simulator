"""The Bamboo Mantis Sage, Jade Grove's guardian (run inside Blender). The idea: a hermit sage who
became the grove. A towering praying mantis whose body is living jade bamboo: every segment of it
a bamboo culm with the pale waxy node rings of bamboo, the abdomen's segments its nodes. Great
bamboo leaves fold over its back like a sage's robe, a mala of jade beads hangs round its neck
with a gold-tasselled guru bead, a crest of leaves rises from its crown like a topknot, and its
scythe forearms, edged with jade Qi, are folded in prayer round the egg it guards. Its compound
eyes are faceted jade with a glowing amber pupil that seems to follow you.

About 36 studs tall to the antennae, its legs spread 28 studs wide. Built from rigid segments the
game turns with Motor6D joints: Body (thorax and abdomen), Mantle (the leaf robe), Neck (the long
prothorax), Head, an Upper and a Blade per forearm, an Upper and a Lower per walking leg. The
glowing pieces (the pupils, the blades' edges) are Neon pieces riding their segment.

Authored in Roblox studs, standing, facing -Z, its feet on the ground at y = 0.

    import mantis_sage as M
    M.build()                     # the high-detail segments, in collection MantisSageHi
    M.bake(names)                 # bake those segments (a few per call: the connection drops on long runs)
    M.export()                    # assets/guardians/MantisSage.fbx and its pieces report
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
NAME = "MantisSage"
PUPIL = "ff9000"         # the amber pupils (deep: Neon blooms paler ones to white)
EDGE = "00c86e"          # the jade Qi of the blades' edges
NODE = 2.6               # studs between bamboo nodes, on every culm (the bamboo shader draws them)

# segment: (parent, pivot): where it turns on its parent (Roblox studs)
PIVOTS = {
    "Body": (None, (0.0, 12.6, 3.0)),
    "Mantle": ("Body", (0.0, 16.8, 3.5)),
    "Neck": ("Body", (0.0, 13.6, 1.0)),
    "Head": ("Neck", (0.0, 26.8, -7.0)),
    "LeftArmUpper": ("Neck", (-1.9, 23.0, -4.6)),
    "LeftArmBlade": ("LeftArmUpper", (-2.1, 15.5, -10.0)),
    "RightArmUpper": ("Neck", (1.9, 23.0, -4.6)),
    "RightArmBlade": ("RightArmUpper", (2.1, 15.5, -10.0)),
    "MidLeftUpper": ("Body", (-2.0, 12.6, 1.8)),
    "MidLeftLower": ("MidLeftUpper", (-9.5, 16.2, -1.6)),
    "MidRightUpper": ("Body", (2.0, 12.6, 1.8)),
    "MidRightLower": ("MidRightUpper", (9.5, 16.2, -1.6)),
    "HindLeftUpper": ("Body", (-2.0, 12.3, 5.6)),
    "HindLeftLower": ("HindLeftUpper", (-10.6, 15.8, 10.4)),
    "HindRightUpper": ("Body", (2.0, 12.3, 5.6)),
    "HindRightLower": ("HindRightUpper", (10.6, 15.8, 10.4)),
}


# ---------- materials ----------
def mat_bamboo(name="MantisBamboo", base=(0.08, 0.27, 0.09), light=(0.4, 0.58, 0.18), aged=(0.62, 0.55, 0.24)):
    """Living jade bamboo: fine fibres running along the culm (UV v, in studs), broad paler and
    darker streaks, patches aged toward straw, and at every node (every NODE studs) the pale waxy
    ring of bamboo over a dark seam."""
    g = Hm._Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    fibres_at = g.n("ShaderNodeCombineXYZ")
    g.link(g.math("MULTIPLY", u, 40.0), fibres_at.inputs["X"])
    g.link(g.math("MULTIPLY", v, 0.5), fibres_at.inputs["Y"])
    fibres = g.n("ShaderNodeTexNoise", **{"Scale": 3.0, "Detail": 6.0, "Roughness": 0.6})
    g.link(fibres_at.outputs[0], fibres.inputs["Vector"])
    co = g.coords()
    broad = g.n("ShaderNodeTexNoise", **{"Scale": 0.22, "Detail": 3.0})
    g.link(co, broad.inputs["Vector"])
    col = g.ramp(broad.outputs["Fac"], [(0.3, base), (0.7, light)])
    col = g.mix(g.math("MULTIPLY", fibres.outputs["Fac"], 0.35), col, tuple(c * 0.7 for c in base))
    patch = g.n("ShaderNodeTexNoise", **{"Scale": 0.45, "Detail": 4.0})
    g.link(co, patch.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", patch.outputs["Fac"], 0.58, clamp=True), 2.6), col, aged)
    # the nodes: distance (studs) to the nearest node along the culm
    f = g.math("FRACT", g.math("DIVIDE", v, NODE))
    d = g.math("MULTIPLY", g.math("MINIMUM", f, g.math("SUBTRACT", 1.0, f)), NODE)
    ring = g.math("SUBTRACT", 1.0, g.math("DIVIDE", d, 0.3), clamp=True)
    col = g.mix(g.math("MULTIPLY", ring, 0.55), col, (0.7, 0.76, 0.52))
    seam = g.math("LESS_THAN", d, 0.05)
    col = g.mix(g.math("MULTIPLY", seam, 0.7), col, tuple(c * 0.35 for c in base))
    col = g.ao(col, 0.15, 0.4)
    height = g.math("ADD", g.math("MULTIPLY", fibres.outputs["Fac"], 0.6), g.math("MULTIPLY", ring, 0.8))
    return g.finish(col, 0.38, 0.0, g.bump(height, 0.3, 0.02))


def mat_bamboo_leaf(name="MantisLeaf", stem=(0.05, 0.2, 0.07), mid=(0.14, 0.42, 0.13), tip=(0.3, 0.55, 0.18)):
    """A bamboo leaf: parallel veins along it (UV u across, v along), a pale midrib, deep green at
    the stem to fresher green, the tip and rim touched with straw."""
    g = Hm._Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    col = g.ramp(v, [(0.0, stem), (0.5, mid), (0.88, tip), (1.0, (0.55, 0.52, 0.2))])
    du = g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5))
    midrib = g.math("LESS_THAN", du, 0.03)
    veins = g.math("LESS_THAN", g.math("FRACT", g.math("MULTIPLY", u, 16.0)), 0.12)
    col = g.mix(g.math("MAXIMUM", g.math("MULTIPLY", midrib, 0.65), g.math("MULTIPLY", veins, 0.22)), col, (0.45, 0.68, 0.3))
    rim = g.math("GREATER_THAN", du, 0.44)
    col = g.mix(g.math("MULTIPLY", rim, 0.4), col, (0.5, 0.48, 0.2))
    col = g.ao(col, 0.08, 0.45)
    nrm = g.bump(g.math("SUBTRACT", 1.0, g.math("MAXIMUM", midrib, g.math("MULTIPLY", veins, 0.5))), 0.25, 0.008)
    return g.finish(col, 0.45, 0.0, nrm)


def mat_eye(name="MantisEye"):
    """A compound eye: a dome of hexagonal-ish facets (Voronoi), each its own jade with a golden
    sheen toward the top, dark seams between them, glossy."""
    g = Hm._Graph(name)
    co = g.coords()
    cells = g.n("ShaderNodeTexVoronoi", **{"Scale": 9.0})
    g.link(co, cells.inputs["Vector"])
    tone = g.ramp(cells.outputs["Color"], [(0.0, (0.02, 0.16, 0.08)), (0.5, (0.06, 0.34, 0.16)), (1.0, (0.4, 0.42, 0.1))])
    edge = g.n("ShaderNodeTexVoronoi", **{"Scale": 9.0, "feature": "DISTANCE_TO_EDGE"})
    g.link(co, edge.inputs["Vector"])
    seam = g.math("LESS_THAN", edge.outputs["Distance"], 0.06)
    col = g.mix(g.math("MULTIPLY", seam, 0.8), tone, (0.01, 0.05, 0.02))
    up = g.sep(co)[2]
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", up, 0.2, clamp=True), 0.15), col, (0.75, 0.62, 0.16))
    nrm = g.bump(edge.outputs["Distance"], 0.45, 0.02)
    return g.finish(col, 0.12, 0.0, nrm)


# ---------- shapes ----------
cone = G.cone


def resample(pts, step=0.22):
    """Points along a smooth curve through `pts`, about `step` studs apart, ends included."""
    dense = [V(p) for p in W.catmull([tuple(p) for p in pts], 16)]
    at = [0.0]
    for a, b in zip(dense, dense[1:]):
        at.append(at[-1] + (b - a).length)
    count = max(2, round(at[-1] / step) + 1)
    out, j = [], 0
    for i in range(count):
        s = at[-1] * i / (count - 1)
        while j < len(dense) - 2 and at[j + 1] < s:
            j += 1
        span = at[j + 1] - at[j]
        out.append(dense[j].lerp(dense[j + 1], 0 if span <= 0 else (s - at[j]) / span))
    return out


def culm(hi, pts, r0, r1, sides=14, swell=None, mat=0, offset=0.0):
    """A bamboo culm through `pts`, its radius r0 to r1 (or swell(t) scaling it), pinched just
    before each node and ringed at it. UV v runs along it in studs, so the shader's nodes sit on
    the geometry's."""
    curve = resample(pts)
    length = sum((b - a).length for a, b in zip(curve, curve[1:]))

    def radius(t):
        s = t * length + offset
        f = (s / NODE) % 1.0
        d = min(f, 1 - f) * NODE
        base = (r0 + (r1 - r0) * t) * (swell(t) if swell else 1.0)
        return base * (1 + 0.1 * math.exp(-(d / 0.22) ** 2) - 0.035 * math.exp(-(d / 0.7) ** 2))

    Hm.htube(hi, curve, radius, sides=sides, per=1, mat=mat, uv_scale=1.0, tip=False, wobble=0.0)
    return curve


def cap(hi, centre, r, mat=0):
    G.sphere(hi, centre, r, nu=12, nv=8, mat=mat)


def blade(hi, glow, pts, depth, thick, inward):
    """A scythe: a lens-section blade along `pts` (its back), its cutting edge toward `inward`,
    `depth` and `thick` functions of t; the edge's jade Qi is a thin glowing tube in `glow`."""
    curve = resample(pts, 0.18)
    n = len(curve)
    fr = Hm.frames(curve)
    rings, edge = [], []
    sides = 16
    for i, c in enumerate(curve):
        t = i / (n - 1)
        tan = fr[i][0]
        d_in = (V(inward) - tan * V(inward).dot(tan)).normalized()
        side = tan.cross(d_in).normalized()
        d, th = depth(t), thick(t)
        centre = c + d_in * d * 0.5
        ring = []
        for k in range(sides + 1):
            a = TAU * k / sides
            ring.append(hi.v(centre + d_in * (d * 0.5) * math.cos(a) + side * th * math.sin(a) * (0.35 + 0.65 * abs(math.sin(a)))))
        rings.append(ring)
        edge.append(centre + d_in * (d * 0.5 + 0.02))
    for i in range(n - 1):
        for k in range(sides):
            hi.f([rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k]],
                 [(k / sides, i * 0.18), ((k + 1) / sides, i * 0.18), ((k + 1) / sides, (i + 1) * 0.18), (k / sides, (i + 1) * 0.18)], 0)
    tip = hi.v(curve[-1] + fr[-1][0] * 0.25)
    for k in range(sides):
        hi.f([rings[-1][k], rings[-1][k + 1], tip], [(k / sides, 0), ((k + 1) / sides, 0), ((k + 0.5) / sides, 0.1)], 0)
    Hm.htube(glow, edge[2:-2], lambda t: 0.18 * (1 - 0.5 * t), sides=6, per=1, uv_scale=1.0, tip=True, wobble=0.0)
    return edge


def leaf(hi, base, direction, normal, length, width, curl=0.0, twist=0.0, fold=0.18, shape=0.9):
    Hm.leaf(hi, base, direction, normal, length, width, mat=0, fold=fold, curl=curl, twist=twist, steps=14, across=4, shape=shape)


def sheet(hi, name, coll, mat, thickness=0.08):
    o = hi.object(name, coll, [mat])
    Hm.solidify(o, thickness)
    o["sheet"] = True
    return o


# ---------- the segments ----------
def body(coll, M):
    bam = Hm.Hi()
    # the thorax, then the abdomen: a fat bamboo trunk curving down behind, its segments the nodes
    culm(bam, [(0, 13.8, 0.4), (0, 13.3, 3.6), (0, 12.6, 6.8)], 2.0, 2.1)
    culm(bam, [(0, 12.8, 6.0), (0, 13.2, 11.0), (0, 12.2, 16.5), (0, 10.3, 21.5), (0, 8.0, 25.5)], 2.3, 1.0,
         swell=lambda t: 1 + 0.32 * math.sin(math.pi * min(1, t * 1.6)))
    cap(bam, (0, 13.8, 0.4), 1.9)
    cap(bam, (0, 8.0, 25.5), 0.95)
    tuft = Hm.Hi()
    for k in range(5):
        a = (k - 2) * 0.32
        leaf(tuft, (0, 8.0, 25.4), (math.sin(a) * 0.8, -0.35, 1), (0, 1, 0.3), 4.2 - 0.35 * abs(k - 2), 0.42, curl=-0.08)
    return [bam.object("MS_Body", coll, [M["bamboo"]]), sheet(tuft, "MS_BodyTuft", coll, M["leaf"])], {}


def mantle(coll, M):
    """The robe: great bamboo leaves folded over the back, the centre one highest, drooping at
    their tips."""
    robe = Hm.Hi()
    leaf(robe, (0, 17.5, 3.4), (0, -0.04, 1), (0, 1, 0.08), 20.5, 2.2, curl=-0.12, fold=0.24)
    for side in (-1, 1):
        leaf(robe, (side * 1.1, 17.2, 3.7), (side * 0.2, -0.07, 1), (side * 0.45, 1, 0), 19.5, 2.0, curl=-0.12, twist=side * 0.15)
        leaf(robe, (side * 2.0, 16.5, 4.2), (side * 0.36, -0.13, 1), (side * 0.85, 1, 0), 17.5, 1.8, curl=-0.1, twist=side * 0.25)
    return [sheet(robe, "MS_Mantle", coll, M["robe"], 0.12)], {}


def neck(coll, M):
    bam, beads, gold = Hm.Hi(), Hm.Hi(), Hm.Hi()
    curve = culm(bam, [(0, 13.6, 1.0), (0, 18.0, -1.5), (0, 23.0, -4.6), (0, 26.6, -6.6)], 1.55, 1.3,
                 swell=lambda t: 1 + 0.18 * math.exp(-((t - 0.72) / 0.12) ** 2))
    cap(bam, (0, 26.6, -6.6), 1.3)
    # the mala: jade beads round the neck, draping lower at the front, a guru bead and a gold tassel
    centre, axis = V((0, 20.4, -3.0)), V((0, 5.0, -3.1)).normalized()
    side = V((1, 0, 0))
    front = axis.cross(side).normalized()        # toward -Z
    if front.z > 0:
        front = -front
    count = 17
    lowest = None
    for k in range(count):
        a = TAU * k / count
        d = side * math.sin(a) + front * math.cos(a)
        droop = 1.3 * max(0.0, math.cos(a)) ** 2
        p = centre + d * 2.05 + V((0, -droop, 0))
        G.sphere(beads, p, 0.55 if k else 0.78, nu=12, nv=8)
        if k == 0:
            lowest = p
    top = lowest + V((0, -0.78, 0))
    Hm.htube(gold, [top, top + V((0, -0.5, -0.05))], lambda t: 0.16, sides=8, per=2, uv_scale=2.0, tip=False, wobble=0.0)
    for j in range(8):
        a = TAU * j / 8
        b = top + V((0, -0.5, -0.05)) + V((0.14 * math.cos(a), 0, 0.14 * math.sin(a)))
        Hm.htube(gold, [b, b + V((0.08 * math.cos(a), -1.3, 0.08 * math.sin(a)))], lambda t: 0.07, sides=5, per=3, uv_scale=2.0, tip=True, wobble=0.0)
    out = [bam.object("MS_Neck", coll, [M["bamboo"]])]
    b = beads.object("MS_NeckBeads", coll, [M["jade"]])
    b["keep"] = True
    g = gold.object("MS_NeckGold", coll, [M["gold"]])
    g["keep"] = True
    return out + [b, g], {}


def head(coll, M):
    face = G.blob("MS_Head", coll, M["face"], [
        ((0, 28.6, -8.4), (2.0, 2.3, 1.5), None), ((0, 29.9, -8.0), (2.9, 1.2, 1.45), None),
        ((0, 27.0, -8.9), (1.35, 1.1, 0.95), None), ((0, 26.1, -9.1), (0.95, 0.8, 0.7), None),
        ((0, 28.4, -6.9), (1.6, 1.8, 1.1), None)], voxel=0.07, smooth=0.7, rough=0.012, chisel="MantisSkin")
    eyes, small, glow, leaves, gold, brows = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    for side in (-1, 1):
        # tall eyes at the top corners of the triangular head
        G.sphere(eyes, (side * 2.95, 30.1, -8.0), 1.0, nu=24, nv=16, radii=(1.2, 1.9, 1.3))
        G.sphere(glow, (side * 3.0, 29.9, -9.25), 0.3, nu=14, nv=10)                   # the pupil, looking out
        # long brows like an old master's, drooping past the eyes
        leaf(brows, (side * 1.4, 31.4, -8.9), (side * 0.75, -0.7, 0.4), (side * 0.3, 0.5, -1), 5.4, 0.55, curl=0.1, twist=side * 0.3, fold=0.12)
        G.cone(small, (side * 0.5, 26.1, -9.3), (side * 0.12, 24.9, -9.7), 0.32)        # mandibles
        Hm.htube(small, [(side * 0.9, 26.4, -9.0), (side * 1.3, 25.4, -9.4), (side * 1.2, 24.6, -9.9)], lambda t: 0.14 * (1 - 0.4 * t),
                 sides=6, per=4, uv_scale=1.0, tip=True, wobble=0.0)                    # palps
        # antennae: long, fine, sweeping back over the robe
        Hm.htube(small, [(side * 0.6, 30.7, -9.0), (side * 1.0, 32.6, -9.6), (side * 2.2, 34.9, -8.5), (side * 3.8, 36.0, -5.5),
                         (side * 5.0, 35.7, -2.0)], lambda t: 0.17 * (1 - 0.55 * t), sides=6, per=6, uv_scale=1.0, tip=True, wobble=0.0)
    # the sage's beard: two long leaf strands drooping from the mouthparts
    for side in (-1, 1):
        leaf(brows, (side * 0.45, 25.4, -9.4), (side * 0.18, -1, -0.2), (0, 0.1, -1), 3.4, 0.28, curl=0.08, twist=side * 0.7, fold=0.1)
    for p in ((0, 30.65, -8.95), (-0.55, 30.35, -8.85), (0.55, 30.35, -8.85)):
        G.sphere(small, p, 0.19, nu=8, nv=6)                                             # ocelli
    # the topknot: three leaves rising from the crown, bound by a gold ring
    for k in (-1, 0, 1):
        leaf(leaves, (0, 30.9, -7.5), (k * 0.35, 1, 0.25 + 0.1 * abs(k)), (k * 0.6, 0.1, -1), 3.6 - 0.4 * abs(k), 0.4, curl=0.12)
    ring = [V((0, 31.05, -7.5)) + V((0.4 * math.cos(TAU * i / 20), 0, 0.4 * math.sin(TAU * i / 20))) for i in range(20)]
    Hm.htube(gold, ring + ring[:2], lambda t: 0.12, sides=6, per=1, uv_scale=2.0, tip=False, wobble=0.0)
    e = eyes.object("MS_HeadEyes", coll, [M["eye"]])
    s = small.object("MS_HeadSmall", coll, [M["bamboo_dark"]])
    s["keep"] = True
    g = gold.object("MS_HeadGold", coll, [M["gold"]])
    g["keep"] = True
    return [face, e, s, g, sheet(leaves, "MS_HeadCrest", coll, M["leaf"]), sheet(brows, "MS_HeadBrows", coll, M["brow"], 0.06)], \
        {PUPIL: [glow.object("MS_Pupils", coll, [K.glow_material(PUPIL)], smooth=True)]}


def arm_upper(coll, M, side):
    sx = side
    bam, spines = Hm.Hi(), Hm.Hi()
    pts = [(sx * 1.9, 23.0, -4.6), (sx * 2.0, 21.0, -5.8), (sx * 2.1, 18.0, -8.1), (sx * 2.1, 15.5, -10.0)]
    curve = culm(bam, pts, 1.25, 0.85, offset=0.6)
    cap(bam, pts[0], 1.2)
    cap(bam, pts[-1], 0.88)
    # the femur's spines, toward the folded blade in front
    for k in range(7):
        i = int(len(curve) * (0.38 + 0.08 * k))
        c = curve[min(i, len(curve) - 1)]
        base = c + V((-sx * 0.25, 0, -0.75))
        cone(spines, base, base + V((-sx * 0.1, 0.25, -(0.55 + 0.25 * (k % 2)))), 0.16)
    # a young leaf sprouting at the shoulder
    sprout = Hm.Hi()
    leaf(sprout, (sx * 2.6, 22.4, -4.2), (sx * 0.8, 0.7, 0.3), (sx * 0.2, 0.2, -1), 2.8, 0.36, curl=0.1)
    s = spines.object("MS_" + ("Left" if side < 0 else "Right") + "ArmSpines", coll, [M["bamboo_dark"]])
    s["keep"] = True
    name = ("Left" if side < 0 else "Right") + "ArmUpper"
    return [bam.object("MS_" + name, coll, [M["bamboo"]]), s, sheet(sprout, "MS_" + name + "Sprout", coll, M["leaf"])], {}


def arm_blade(coll, M, side):
    sx = side
    hi, glow = Hm.Hi(), Hm.Hi()
    pts = [(sx * 2.1, 15.5, -10.0), (sx * 2.2, 18.2, -11.9), (sx * 2.1, 21.2, -12.6), (sx * 1.9, 23.6, -11.9), (sx * 1.65, 24.4, -10.4),
           (sx * 1.5, 23.8, -9.5)]                    # rising before the face, the tip hooked back down
    edge = blade(hi, glow, pts, depth=lambda t: 0.7 + 1.9 * math.sin(math.pi * min(1, t * 1.25)) * (1 - 0.55 * t),
                 thick=lambda t: 0.5 * (1 - 0.6 * t), inward=(0, -0.15, 1))
    cap(hi, pts[0], 0.75)                             # the blade's root, inside the knee
    teeth = Hm.Hi()
    for k in range(4, len(edge) - 8, 5):              # a saw of small teeth along the cutting edge
        a, b = V(edge[k]), V(edge[k + 1])
        out = V((0, -0.15, 1)).normalized()           # the edge faces back, toward the femur
        cone(teeth, a, a + out * 0.45 + (b - a).normalized() * 0.2, 0.13, sides=5)
    name = ("Left" if side < 0 else "Right") + "ArmBlade"
    t = teeth.object("MS_" + name + "Teeth", coll, [M["blade"]])
    t["keep"] = True
    return [hi.object("MS_" + name, coll, [M["blade"]]), t], {EDGE: [glow.object("MS_" + name + "Edge", coll, [K.glow_material(EDGE)], smooth=True)]}


def leg(coll, M, name, side, pair, part):
    sx = side
    if pair == "Mid":
        hip, knee, ankle, foot, toe = (2.0, 12.6, 1.8), (9.5, 16.2, -1.6), (11.3, 9.0, -3.6), (12.4, 0.6, -5.2), (13.4, 0.35, -6.6)
        mid = (5.8, 15.6, -0.2)
    else:
        hip, knee, ankle, foot, toe = (2.0, 12.3, 5.6), (10.6, 15.8, 10.4), (12.4, 8.5, 13.0), (13.6, 0.6, 15.2), (14.6, 0.35, 16.6)
        mid = (6.4, 15.2, 8.0)
    m = lambda p: (sx * p[0], p[1], p[2])
    bam, dark, sprout = Hm.Hi(), Hm.Hi(), Hm.Hi()
    if part == "Upper":
        culm(bam, [m(hip), m(mid), m(knee)], 1.05, 0.8, offset=0.4)
        cap(bam, m(hip), 1.0)
        cap(bam, m(knee), 0.86)
        for k in (0, 1):
            leaf(sprout, V(m(knee)) + V((0, 0.5, 0.2 * k)), (sx * 0.4, 1, 0.3 - 0.6 * k), (sx * 0.3, 0.1, -1 + 2 * k), 2.6 - 0.4 * k, 0.33, curl=0.08)
    else:
        culm(bam, [m(knee), m(ankle), m(foot)], 0.8, 0.48, offset=1.1)
        cap(bam, m(foot), 0.5)
        Hm.htube(dark, [m(foot), m(toe)], lambda t: 0.32 * (1 - 0.3 * t), sides=8, per=3, uv_scale=1.0, tip=False, wobble=0.0)
        for dz in (-0.25, 0.25):
            t0 = V(m(toe))
            cone(dark, t0, t0 + V((sx * 0.55, -0.25, dz - 0.35)), 0.16)
    out = [bam.object("MS_" + name, coll, [M["bamboo"]])]
    if dark.faces:
        d = dark.object("MS_" + name + "Claw", coll, [M["bamboo_dark"]])
        d["keep"] = True
        out.append(d)
    if sprout.faces:
        out.append(sheet(sprout, "MS_" + name + "Sprout", coll, M["leaf"]))
    return out, {}


def segments():
    out = {"Body": body, "Mantle": mantle, "Neck": neck, "Head": head}
    for side, s in ((-1, "Left"), (1, "Right")):
        out[s + "ArmUpper"] = (lambda sd: lambda c, M: arm_upper(c, M, sd))(side)
        out[s + "ArmBlade"] = (lambda sd: lambda c, M: arm_blade(c, M, sd))(side)
        for pair in ("Mid", "Hind"):
            for part in ("Upper", "Lower"):
                name = pair + s + part
                out[name] = (lambda n, sd, pr, pt: lambda c, M: leg(c, M, n, sd, pr, pt))(name, side, pair, part)
    return out


BUDGET = {"Body": 9000, "Mantle": 6000, "Neck": 8000, "Head": 12000, "LeftArmUpper": 5000, "RightArmUpper": 5000,
          "LeftArmBlade": 4000, "RightArmBlade": 4000}       # each leg piece: 3000


def materials():
    return {"bamboo": mat_bamboo(), "bamboo_dark": mat_bamboo("MantisBambooDark", (0.2, 0.17, 0.06), (0.38, 0.3, 0.1), (0.5, 0.4, 0.16)),
            "leaf": mat_bamboo_leaf(), "robe": mat_bamboo_leaf("MantisRobe", (0.02, 0.1, 0.05), (0.05, 0.25, 0.1), (0.12, 0.38, 0.14)),
            "brow": mat_bamboo_leaf("MantisBrow", (0.3, 0.36, 0.2), (0.55, 0.58, 0.36), (0.78, 0.76, 0.56)),
            "eye": mat_eye(), "face": Hm.mat_jade("MantisFaceJade"), "jade": Hm.mat_jade("MantisJade"), "blade": Hm.mat_jade("MantisBladeJade"),
            "gold": Hm.mat_gold("MantisGold")}


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
            for o in objs:
                o.name = NAME + "_" + name + "_Glow_" + hexstr
        out[name] = (hi, glow, coll)
    return out


def bake(names):
    """Bakes these segments' game meshes (built already); records them for export()."""
    parts = bpy.app.driver_namespace.setdefault("mantis_parts", {})
    for name in names:
        coll = bpy.data.collections[NAME + "_" + name]
        hi = [o for o in coll.objects if o.name.startswith("MS_") and o.type == "MESH"]
        low = G.bake_piece(NAME, name, hi, coll, BUDGET.get(name, 3000))
        parts[name] = (name, low.name)
    return {n: B.tris(bpy.data.objects[parts[n][1]]) for n in names}


def export():
    return G.export(NAME, PIVOTS, bpy.app.driver_namespace["mantis_parts"])
