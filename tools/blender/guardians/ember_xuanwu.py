"""The Ember Xuanwu, Ember Peak's guardian (run inside Blender). The idea: the Black Tortoise of
the north, gone to the volcano. A colossal tortoise whose shell has become a small volcano: the
carapace is a dome of black basalt columns, stepped up into a cone whose crater cradles the egg,
and between every column the magma inside the shell shows through, glowing. Round the shell coils
its companion, a molten serpent: a body of cooled black crust broken into bands, the lava of it
glowing between them. The serpent rises from the coil over the volcano's flank and looks down at
whoever comes; the tortoise's own head is a heavy beaked skull crowned with basalt columns, its
eyes and throat alight. Slow, huge, armoured.

About 24 studs to the crater's rim and 31 to the serpent's crown, 30 studs wide across its feet
and 48 long from beak to tail. Built from rigid segments the game turns with Motor6D joints: Body
(the shell, the volcano, the serpent's coil and the body under them), Neck, Head and Jaw (the
tortoise's), SerpentNeck and SerpentHead, Tail, and an Upper and a Lower per leg. The glowing
pieces (the magma core, the serpent's lava, the eyes and throats) are Neon pieces riding their
segment.

Authored in Roblox studs, standing, facing -Z, its feet on the ground at y = 0.

    import ember_xuanwu as X
    X.build()                     # the high-detail segments, in collection EmberXuanwuHi
    X.bake(names)                 # bake those segments (a few per call: the connection drops on long runs)
    X.export()                    # assets/guardians/EmberXuanwu.fbx and its pieces report
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
NAME = "EmberXuanwu"
LAVA = "ff4600"          # the magma in the shell, the serpent's lava, the throats (deep: Neon blooms paler ones to white)
EYE = "ffa000"           # the tortoise's eyes
SERPENT_EYE = "ffc800"   # the serpent's, a hotter gold
PUPIL = "1c0700"         # the slit pupils: dark Neon renders as a flat black slit, and the rig blinks it with the iris

SHELL_C = V((0.0, 7.0, 1.5))           # the carapace: an ellipsoid's upper half, its rim at the equator
SHELL_R = V((13.5, 8.5, 16.5))
CONE = (0.0, 1.5)                      # the volcano's axis (x, z), on the shell's crown
RIM_Y, POOL_Y = 23.6, 21.2             # the crater's rim, and the magma pool in it
COLUMN_LIFT = 0.55                     # how far the dome's columns stand proud of the shell
CONE_OUT = 12.0                        # where the volcano's flank meets the dome

# segment: (parent, pivot): where it turns on its parent (Roblox studs)
PIVOTS = {
    "Body": (None, (0.0, 7.0, 1.5)),
    "Neck": ("Body", (0.0, 8.6, -12.0)),
    "Head": ("Neck", (0.0, 10.4, -18.6)),
    "Jaw": ("Head", (0.0, 9.6, -20.6)),
    "SerpentNeck": ("Body", None),      # where the serpent leaves its coil (coil_end())
    "SerpentHead": ("SerpentNeck", (-5.0, 27.2, -12.6)),
    "Tail": ("Body", (0.0, 5.6, 16.4)),
    "FrontLeftUpper": ("Body", (-8.6, 6.4, -8.6)),
    "FrontLeftLower": ("FrontLeftUpper", (-12.4, 5.2, -10.6)),
    "FrontRightUpper": ("Body", (8.6, 6.4, -8.6)),
    "FrontRightLower": ("FrontRightUpper", (12.4, 5.2, -10.6)),
    "BackLeftUpper": ("Body", (-8.6, 6.0, 10.8)),
    "BackLeftLower": ("BackLeftUpper", (-12.0, 4.8, 12.6)),
    "BackRightUpper": ("Body", (8.6, 6.0, 10.8)),
    "BackRightLower": ("BackRightUpper", (12.0, 4.8, 12.6)),
}


# ---------- materials ----------
def mat_basalt(name="XuanwuBasalt"):
    """Columnar basalt: each column its own charcoal (random per island), cross-joints cracking it
    every stud and a half along its length (UV v), grey ash settled on the upward faces, and the
    crevices between the columns heated red by the magma under them."""
    g = Hm._Graph(name)
    geo = g.n("ShaderNodeNewGeometry")
    col = g.ramp(geo.outputs["Random Per Island"], [(0.0, (0.045, 0.042, 0.04)), (0.5, (0.075, 0.068, 0.062)), (1.0, (0.11, 0.1, 0.09))])
    co = g.coords()
    grain = g.n("ShaderNodeTexNoise", **{"Scale": 3.5, "Detail": 6.0, "Roughness": 0.65})
    g.link(co, grain.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", grain.outputs["Fac"], 0.45), col, (0.16, 0.15, 0.14))
    # cross-joints: thin cracks round the column, a little uneven
    _, v, _ = g.sep(g.coords("UV"))
    wob = g.n("ShaderNodeTexNoise", **{"Scale": 1.2, "Detail": 2.0})
    g.link(co, wob.inputs["Vector"])
    f = g.math("FRACT", g.math("ADD", g.math("DIVIDE", v, 1.55), g.math("MULTIPLY", wob.outputs["Fac"], 0.5)))
    joint = g.math("LESS_THAN", g.math("MINIMUM", f, g.math("SUBTRACT", 1.0, f)), 0.035)
    col = g.mix(g.math("MULTIPLY", joint, 0.8), col, (0.02, 0.012, 0.01))
    # ash on the upward faces (Blender's z is up), in drifts
    up = g.sep(geo.outputs["Normal"])[2]
    drift = g.n("ShaderNodeTexNoise", **{"Scale": 0.7, "Detail": 4.0})
    g.link(co, drift.inputs["Vector"])
    ash = g.math("MULTIPLY", g.math("SUBTRACT", up, 0.6, clamp=True), g.math("SUBTRACT", g.math("MULTIPLY", drift.outputs["Fac"], 2.2), 0.8, clamp=True))
    col = g.mix(g.math("MINIMUM", g.math("MULTIPLY", ash, 2.0), 0.7), col, (0.3, 0.285, 0.27))
    # heat: the crevices between columns glow (ambient occlusion turned to heat), deepest near the core
    ao = g.n("ShaderNodeAmbientOcclusion", samples=16, only_local=True)
    ao.inputs["Distance"].default_value = 0.3
    hot = g.math("POWER", g.math("SUBTRACT", 1.0, ao.outputs["AO"], clamp=True), 1.3)
    col = g.mix(g.math("MINIMUM", g.math("MULTIPLY", hot, 1.2), 0.75), col, (0.42, 0.05, 0.008))
    col = g.mix(g.math("MULTIPLY", joint, g.math("MINIMUM", g.math("MULTIPLY", hot, 2.0), 0.8)), col, (1.0, 0.32, 0.02))
    height = g.math("SUBTRACT", g.math("MULTIPLY", grain.outputs["Fac"], 0.5), g.math("MULTIPLY", joint, 0.6))
    return g.finish(col, g.math("ADD", 0.72, g.math("MULTIPLY", ash, 0.2)), 0.0, g.bump(height, 0.35, 0.03))


def mat_skin(name="XuanwuSkin", dark=(0.02, 0.014, 0.011), light=(0.048, 0.031, 0.022), scale=1.6):
    """Its hide: thick domed scales (Voronoi cells, `scale` per stud) of charred umber, the seams
    between them a deep ember red, ash on the upper faces, the crevices darkened."""
    g = Hm._Graph(name)
    co = g.coords()
    cells = g.n("ShaderNodeTexVoronoi", **{"Scale": scale})
    g.link(co, cells.inputs["Vector"])
    col = g.ramp(cells.outputs["Color"], [(0.0, dark), (1.0, light)])
    mott = g.n("ShaderNodeTexNoise", **{"Scale": 4.0, "Detail": 5.0})
    g.link(co, mott.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", mott.outputs["Fac"], 0.3), col, tuple(c * 1.8 for c in light))
    edge = g.n("ShaderNodeTexVoronoi", **{"Scale": scale, "feature": "DISTANCE_TO_EDGE"})
    g.link(co, edge.inputs["Vector"])
    seam = g.math("SUBTRACT", 1.0, g.math("DIVIDE", edge.outputs["Distance"], 0.07), clamp=True)
    col = g.mix(g.math("MULTIPLY", seam, 0.6), col, (0.13, 0.02, 0.006))
    geo = g.n("ShaderNodeNewGeometry")
    up = g.sep(geo.outputs["Normal"])[2]
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", up, 0.55, clamp=True), 0.5), col, (0.15, 0.14, 0.13))
    col = g.ao(col, 0.35, 0.35)
    dome = g.math("POWER", g.math("MINIMUM", g.math("DIVIDE", edge.outputs["Distance"], 0.22), 1.0), 0.5)
    return g.finish(col, 0.66, 0.0, g.bump(g.math("ADD", dome, g.math("MULTIPLY", mott.outputs["Fac"], 0.2)), 0.5, 0.05))


def mat_crust(name="XuanwuCrust"):
    """The serpent's cooled crust: rough near-black rock, warmer where it is thin, cracked all over
    with fine glowing lava (thin ridges of a distorted noise), and the edges of every band heated
    orange where they part over the molten body."""
    g = Hm._Graph(name)
    geo = g.n("ShaderNodeNewGeometry")
    col = g.ramp(geo.outputs["Random Per Island"], [(0.0, (0.022, 0.017, 0.015)), (1.0, (0.05, 0.034, 0.027))])
    co = g.coords()
    grain = g.n("ShaderNodeTexNoise", **{"Scale": 5.0, "Detail": 7.0, "Roughness": 0.7})
    g.link(co, grain.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", grain.outputs["Fac"], 0.5), col, (0.09, 0.07, 0.06))
    vn = g.n("ShaderNodeTexNoise", **{"Scale": 1.4, "Detail": 3.0, "Roughness": 0.5, "Distortion": 0.6})
    g.link(co, vn.inputs["Vector"])
    patch = g.n("ShaderNodeTexNoise", **{"Scale": 0.9, "Detail": 2.0})      # the crust cracks only where it is thin
    g.link(co, patch.inputs["Vector"])
    thin = g.math("GREATER_THAN", patch.outputs["Fac"], 0.54)
    d = g.math("ABSOLUTE", g.math("SUBTRACT", vn.outputs["Fac"], 0.5))
    crack = g.math("MULTIPLY", g.math("LESS_THAN", d, 0.012), thin)
    core = g.math("MULTIPLY", g.math("LESS_THAN", d, 0.005), thin)
    col = g.mix(crack, col, (0.85, 0.16, 0.01))
    col = g.mix(core, col, (1.0, 0.45, 0.04))
    ao = g.n("ShaderNodeAmbientOcclusion", samples=16, only_local=True)
    ao.inputs["Distance"].default_value = 0.35
    hot = g.math("POWER", g.math("SUBTRACT", 1.0, ao.outputs["AO"], clamp=True), 0.9)
    col = g.mix(g.math("MINIMUM", g.math("MULTIPLY", hot, 1.6), 0.9), col, (0.7, 0.1, 0.01))
    height = g.math("SUBTRACT", g.math("MULTIPLY", grain.outputs["Fac"], 0.8), g.math("MULTIPLY", crack, 0.6))
    return g.finish(col, g.math("ADD", 0.78, g.math("MULTIPLY", crack, -0.3)), 0.0, g.bump(height, 0.45, 0.03))


def mat_horn(name="XuanwuHorn"):
    """The beak's horn: near-black brown, fine growth lines running round it, glossy where worn."""
    g = Hm._Graph(name)
    co = g.coords()
    lines = g.n("ShaderNodeTexWave", **{"Scale": 7.0, "Distortion": 3.0, "Detail": 4.0})
    g.link(co, lines.inputs["Vector"])
    col = g.ramp(lines.outputs["Fac"], [(0.0, (0.016, 0.011, 0.008)), (1.0, (0.03, 0.02, 0.014))])
    col = g.ao(col, 0.2, 0.5)
    return g.finish(col, 0.38, 0.0, g.bump(lines.outputs["Fac"], 0.08, 0.01))


def materials():
    return {"basalt": mat_basalt(), "skin": mat_skin(), "scute": mat_skin("XuanwuScute", (0.03, 0.023, 0.019), (0.07, 0.052, 0.04), 0.75),
            "crust": mat_crust(),
            "obsidian": Hm.mat_obsidian("XuanwuObsidian", heat_reach=0.04), "horn": mat_horn()}


# ---------- shapes ----------
cone, sphere, frame = G.cone, G.sphere, G.frame


def shell_y(x, z):
    """The carapace's height over (x, z), or None beyond its rim."""
    k = 1 - ((x - SHELL_C.x) / SHELL_R.x) ** 2 - ((z - SHELL_C.z) / SHELL_R.z) ** 2
    return SHELL_C.y + SHELL_R.y * math.sqrt(k) if k > 0 else None


def shell_normal(p):
    d = V(p) - SHELL_C
    return V((d.x / SHELL_R.x ** 2, d.y / SHELL_R.y ** 2, d.z / SHELL_R.z ** 2)).normalized()


def shell_point(u, v, lift=0.0):
    p, n = G.on_ellipsoid(SHELL_C, SHELL_R, u, v)
    return p + n * lift, n


def column(hi, base, axis, length, radius, phase, chamfer=0.14, mat=0):
    """A basalt column: a hexagonal prism from `base` along `axis`, its top edge chamfered. UV v runs
    along it in studs (the shader's cross-joints); its base is left open, sunk in what it stands on."""
    n, s, t = frame(axis)
    top = V(base) + n * length
    dirs = [s * math.cos(phase + TAU * k / 6) + t * math.sin(phase + TAU * k / 6) for k in range(6)]
    low = [hi.v(V(base) + d * radius) for d in dirs]
    high = [hi.v(top - n * chamfer + d * radius) for d in dirs]
    inner = [hi.v(top + d * (radius - chamfer)) for d in dirs]
    edge = length - chamfer
    for k in range(6):
        j = (k + 1) % 6
        out = (dirs[k] + dirs[j]).normalized()
        hi.facing([low[k], low[j], high[j], high[k]], [(k / 6, 0), ((k + 1) / 6, 0), ((k + 1) / 6, edge), (k / 6, edge)], tuple(out), mat)
        hi.facing([high[k], high[j], inner[j], inner[k]], [(k / 6, edge), ((k + 1) / 6, edge), ((k + 1) / 6, length), (k / 6, length)],
                  tuple(out + n), mat)
    hi.facing(inner, [(0.5 + 0.3 * math.cos(TAU * k / 6), length + 0.3 * math.sin(TAU * k / 6)) for k in range(6)], tuple(n), mat)


def resample(pts, step=0.25):
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


def lava_body(crust, core, curve, radius, band=1.5, gap=0.16, seed=0, spines=None, spine_from=0.0, back=None):
    """The serpent's molten body along `curve`: bands of cooled crust, each a little swollen and
    turned its own way, the lava core (a Neon tube) glowing in the gaps between them. radius(t), t
    0..1 along it. spines: a Hi for a ridge of obsidian spines down its back (from t spine_from),
    back(point) the way its back faces there."""
    rnd = random.Random(seed)
    at = [0.0]
    for a, b in zip(curve, curve[1:]):
        at.append(at[-1] + (b - a).length)
    total = at[-1]
    fr = Hm.frames(curve)
    s = 0.0
    while s < total - 0.3:
        length = band * rnd.uniform(0.6, 1.4)
        e = min(total, s + length)
        i0 = next(i for i, a in enumerate(at) if a >= s)
        i1 = max(i0 + 2, next((i for i, a in enumerate(at) if a >= e), len(at) - 1))
        seg = curve[i0:i1 + 1:2] if (i1 - i0) % 2 == 0 else curve[i0:i1:2] + [curve[i1]]     # rings about half a stud apart
        r0 = radius(s / total)
        swell = rnd.uniform(1.0, 1.08)
        Hm.htube(crust, seg, lambda t, r0=r0, swell=swell: r0 * swell * (0.9 + 0.1 * math.sin(math.pi * t)), sides=10, per=1,
                 uv_scale=1.0, tip=False, seed=rnd.randint(0, 999), wobble=0.5)
        if spines is not None and s / total >= spine_from:
            m = seg[len(seg) // 2]
            k = min(range(len(curve)), key=lambda q: (curve[q] - m).length)
            t_ = fr[k][0]
            up = back(curve[k])
            up = (up - t_ * up.dot(t_)).normalized()
            r = radius(at[k] / total)
            base = m + up * r * 0.8
            cone(spines, base, base + up * (0.5 + 0.6 * r) - t_ * 0.35 * r, 0.22 * r, sides=6)
        s = e + gap * rnd.uniform(0.55, 1.35)
    Hm.htube(core, curve[::3] + ([curve[-1]] if (len(curve) - 1) % 3 else []), lambda t: radius(t) * 0.8, sides=8, per=1, uv_scale=1.0,
             tip=False, wobble=0.0)


DOME_SPACING = 1.95


def to_shell(p):
    """The shell's surface point straight out from its centre through p, kept above its rim."""
    d = V(p) - SHELL_C
    d.y = max(d.y, 0.0)
    k = math.sqrt((d.x / SHELL_R.x) ** 2 + (d.y / SHELL_R.y) ** 2 + (d.z / SHELL_R.z) ** 2)
    return SHELL_C + d / k


def dome_spots(spacing, cx, cz, seed=3, rounds=24):
    """Points spread evenly over the dome outside the volcano, `spacing` apart: thrown at random,
    then pushed apart over the surface until they settle. [(point, normal)]."""
    rnd = random.Random(seed)
    pts = []
    for _ in range(9000):
        u, v = rnd.random(), 0.5 + 0.5 * rnd.random()
        p, _ = shell_point(u, v)
        if math.hypot(p.x - cx, p.z - cz) < CONE_OUT + 0.4:
            continue
        if all((p - q).length >= spacing * 0.8 for q in pts):
            pts.append(p)
    for _ in range(rounds):
        moved = []
        for p in pts:
            push = V((0, 0, 0))
            for q in pts:
                d = p - q
                l = d.length
                if 0 < l < spacing * 1.25:
                    push += d / l * (spacing * 1.25 - l)
            q = to_shell(p + push * 0.25)
            if math.hypot(q.x - cx, q.z - cz) < CONE_OUT + 0.4:
                r = V((q.x - cx, 0, q.z - cz)).normalized() * (CONE_OUT + 0.4)
                q = to_shell(V((cx + r.x, q.y, cz + r.z)))
            moved.append(q)
        pts = moved
    return [(p, shell_normal(p)) for p in pts]


# ---------- the serpent's coil ----------
def coil_curve():
    """The coil round the shell: from its thin tail at the back right, round the right flank, over
    the shell's front above the neck, round the left flank to the back, rising: the serpent's neck
    leaves it there, behind the volcano."""
    pts = []
    steps = 60
    for i in range(steps + 1):
        k = i / steps
        u = 0.44 - 0.84 * k            # u round from the front (-Z), 0.25 its right: from the back right round the front to the back left
        v = 0.565 + 0.13 * k ** 1.5 + 0.03 * math.sin(k * TAU * 2.5)   # climbing the dome, rising and dipping
        r = coil_radius(k)
        p, n = shell_point(u % 1.0, v, 0.0)
        pts.append(p + n * (r * 0.72 + COLUMN_LIFT + 0.2))       # lying on the columns' tops
    return pts


def coil_radius(t):
    return 0.45 + 1.45 * min(1.0, t * 1.4) ** 0.8


def coil_end():
    c = coil_curve()
    return c[-1], (c[-1] - c[-3]).normalized()


SERPENT_NECK = [None, (-10.5, 19.0, 8.0), (-11.0, 23.5, 2.5), (-9.5, 27.2, -3.5), (-7.0, 28.4, -9.0), (-5.0, 27.2, -12.6)]   # the coil's end goes first


def serpent_neck_curve():
    end, d = coil_end()
    pts = [end - d * 1.2, end] + [V(p) for p in SERPENT_NECK[1:]]
    return resample(pts, 0.25)


# ---------- the segments ----------
def body(coll, M):
    basalt, crust, spines, core = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    rnd = random.Random(23)
    coil = resample(coil_curve(), 0.25)

    coil_r = [coil_radius(i / (len(coil) - 1)) for i in range(len(coil))]

    def near_coil(p, margin):
        """Whether p is within `margin` of the coil's crust (its thickness there counted)."""
        return min((p - coil[i]).length - coil_r[i] for i in range(0, len(coil), 2)) < margin

    # the volcano: rings of upright columns, their tops on a concave flank rising from the dome to
    # the crater's rim
    cx, cz = CONE
    rings = (3.9, 5.15, 6.4, 7.65, 8.9, 10.15, 11.4)

    def cone_top(rr, x, z):
        d = (shell_y(x, z) or SHELL_C.y) + COLUMN_LIFT
        return d + (RIM_Y - d) * max(0.0, (CONE_OUT - rr) / (CONE_OUT - rings[0])) ** 1.5

    for ring, rr in enumerate(rings):
        radius = 0.72 + 0.05 * ring
        count = int(TAU * rr / (1.732 * radius * 0.96))
        for k in range(count):
            a = TAU * (k + 0.5 * (ring % 2)) / count + rnd.uniform(-0.03, 0.03)
            x, z = cx + rr * math.cos(a), cz + rr * math.sin(a)
            ground = shell_y(x, z)
            if near_coil(V((x, ground, z)), radius + 0.2):
                continue
            top = cone_top(rr, x, z) + rnd.uniform(-0.35, 0.3) - (0.8 if rnd.random() < 0.06 else 0.0)
            out = V((math.cos(a), 0, math.sin(a)))
            axis = (V((0, 1, 0)) + out * 0.05).normalized()
            base = V((x, ground - 1.0, z))
            # a flat face toward each neighbour round the ring (frame((0, 1, 0)) puts phase 0 at -Z)
            column(basalt, base, axis, top - base.y, radius * rnd.uniform(0.98, 1.04), -a - math.pi / 2 + rnd.uniform(-0.08, 0.08))
    # the dome: columns packed close along its normal, a pavement of hexagons stepped a little, the
    # rim's standing longer like the serrated edge of a tortoise's shell
    spots = dome_spots(DOME_SPACING, cx, cz)
    for p, n in spots:
        nn = DOME_SPACING
        rim = p.y < SHELL_C.y + 1.2
        lift = COLUMN_LIFT * rnd.uniform(0.55, 1.35) + (0.5 if rim else 0.0)
        if rnd.random() < 0.05:
            lift *= 0.3                                     # a broken column: the magma glows in the hole
        base = p - n * 1.0
        column(basalt, base, n, 1.0 + lift, nn * 0.585, rnd.uniform(0, TAU))
    # the magma core: a heightfield over the shell, just under the columns, rising into the cone and
    # pooling in the crater
    def core_y(rr, x, z):
        dome = (shell_y(x, z) or SHELL_C.y) - 0.3
        return max(dome, min(POOL_Y, cone_top(rr, x, z) - 1.1)) if rr <= CONE_OUT else dome
    radial, around = 26, 48
    grid = []
    for i in range(radial + 1):
        row = []
        for j in range(around):
            a = TAU * j / around
            dx, dz = math.cos(a), math.sin(a)
            # out from the cone's axis to the rim (the ellipse round the shell's equator)
            lo, hi_ = 0.0, 40.0
            for _ in range(30):
                m = (lo + hi_) / 2
                if shell_y(cx + dx * m, cz + dz * m) is None:
                    hi_ = m
                else:
                    lo = m
            rr = lo * (0.02 + 0.98 * (i / radial) ** 0.8)
            x, z = cx + dx * rr, cz + dz * rr
            row.append(core.v((x, core_y(rr, x, z), z)))
        grid.append(row)
    for i in range(radial):
        for j in range(around):
            jj = (j + 1) % around
            core.facing([grid[i][j], grid[i][jj], grid[i + 1][jj], grid[i + 1][j]], [(0, 0), (1, 0), (1, 1), (0, 1)], (0, 1, 0))
    middle = core.v((cx, POOL_Y, cz))
    for j in range(around):
        core.facing([middle, grid[0][j], grid[0][(j + 1) % around]], [(0.5, 0.5), (0, 0), (1, 0)], (0, 1, 0))
    # the crater: broken stubs of columns standing in the pool round the egg's cradle
    for k in range(9):
        a = TAU * k / 9 + rnd.uniform(-0.15, 0.15)
        rr = rnd.uniform(2.45, 2.85)
        x, z = cx + rr * math.cos(a), cz + rr * math.sin(a)
        column(basalt, V((x, POOL_Y - 0.8, z)), V((0, 1, 0)), 0.8 + rnd.uniform(0.25, 0.85), rnd.uniform(0.38, 0.5), rnd.uniform(0, TAU))
    # the serpent's coil
    lava_body(crust, core, coil, coil_radius, seed=5, spines=spines, spine_from=0.25, back=shell_normal)
    # under the shell: the tortoise's body, its plastron a broad plate of scutes
    flesh = G.blob("EX_Body", coll, M["skin"], [((0, 5.4, 1.5), (11.2, 3.2, 14.6), None), ((0, 6.2, -10.5), (6.5, 3.0, 4.5), None),
                                                ((0, 5.8, 13.0), (6.0, 2.6, 4.0), None)], voxel=0.28, smooth=0.6, rough=0.04)
    # the plastron, and the shell's underside out to its rim (seen from below: players stand at its height)
    plastron = G.blob("EX_BodyPlastron", coll, M["scute"], [((0, 4.0, 1.5), (10.4, 1.3, 13.6), None), ((0, 6.3, 1.5), (13.2, 1.9, 16.2), None)],
                      voxel=0.22, smooth=0.7, rough=0.03)
    b = basalt.object("EX_ShellColumns", coll, [M["basalt"]], smooth=False)
    b["keep"] = True
    c = crust.object("EX_BodyCoil", coll, [M["crust"]])
    c["keep"] = True
    sp = spines.object("EX_BodySpines", coll, [M["obsidian"]])
    sp["keep"] = True
    return [flesh, plastron, b, c, sp], {LAVA: [core.object("EX_BodyCore", coll, [K.glow_material(LAVA)], smooth=True)]}


def neck(coll, M):
    lobes = G.capsule_lobes((0, 8.2, -10.5), (0, 10.4, -19.2), 3.3, 2.7, n=6)
    o = G.blob("EX_Neck", coll, M["skin"], lobes, voxel=0.12, smooth=0.6, rough=0.03)
    folds = Hm.Hi()
    for k in range(5):                                  # heavy folds of hide round the neck
        z = -12.6 - 1.25 * k
        y = 8.2 + (-10.5 - z) * 0.253                  # along the neck's rise
        r = 3.15 - 0.1 * k
        ring = [V((r * math.cos(a), y + r * 0.92 * math.sin(a), z + 0.25 * math.sin(a * 3))) for a in (TAU * i / 28 for i in range(28))]
        Hm.htube(folds, ring + ring[:2], lambda t: 0.28, sides=8, per=1, uv_scale=1.0, tip=False, wobble=0.6, seed=k)
    f = folds.object("EX_NeckFolds", coll, [M["skin"]])
    f["keep"] = True
    return [o, f], {}


def head(coll, M):
    # a snapping turtle's skull, not a round one: a broad cranium tapering to a hooked beak, a heavy
    # brow shelf over each eye, heavy jowls
    skull = G.blob("EX_Head", coll, M["scute"], [
        ((0, 11.8, -21.0), (3.4, 2.4, 3.2), None)] + [
        ((0, 11.55 - 0.14 * k, -22.6 - 0.625 * k), (2.75 - 0.18 * k, 1.95 - 0.08 * k, 1.6), None) for k in range(8)] + [   # the face, a wedge
        ((-1.85, 12.95, -23.2), (1.6, 0.6, 1.7), (0, 0, -16)), ((1.85, 12.95, -23.2), (1.6, 0.6, 1.7), (0, 0, 16)),  # brow shelves
        ((-2.5, 10.6, -21.6), (1.3, 1.1, 1.6), None), ((2.5, 10.6, -21.6), (1.3, 1.1, 1.6), None),                # heavy jowls
        ((0, 11.2, -19.4), (3.1, 2.4, 1.8), None)], voxel=0.09, smooth=0.8, rough=0.03, chisel="XuanwuHide")
    basalt, glow, pupils, lids, throat = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    rnd = random.Random(31)
    # a crown of basalt columns rising from the brow and sweeping back, the volcano in small
    for row, (z, ys, count) in enumerate(((-22.6, 13.5, 3), (-21.0, 13.9, 4), (-19.4, 13.7, 3))):
        for k in range(count):
            x = (k - (count - 1) / 2) * 1.35
            base = V((x, ys - 1.0, z))
            axis = V((x * 0.12, 1.0, 0.55 + 0.1 * row))
            column(basalt, base, axis, 1.6 + 1.3 * (1 - abs(x) / 3) + rnd.uniform(-0.2, 0.3) + 0.3 * row, 0.5, rnd.uniform(0, TAU), chamfer=0.1)
    for side in (-1, 1):
        # an old, heavy-lidded glare: the upper lid slanting down toward the beak
        G.eye(glow, pupils, lids, (side * 2.2, 12.1, -23.4), (side * 0.85, 0.12, -0.5), (0, -0.05, -1), 0.95, 0.5, tilt=0.2, bulge=0.14,
              lid=0.42, droop=0.42, lower=0.22, slit=0.17)
    # the throat's fire, seen when the jaw opens
    sphere(throat, (0, 9.4, -22.4), 1.3, radii=(1.5, 0.6, 2.4))
    b = basalt.object("EX_HeadCrown", coll, [M["basalt"]], smooth=False)
    b["keep"] = True
    lid = lids.object("EX_HeadLids", coll, [M["skin"]])
    lid["keep"] = True
    # the beak's horn sheath, black and glassy, hooked over the jaw
    beak = G.blob("EX_HeadBeak", coll, M["horn"], [((0, 10.45, -27.3), (1.35, 1.3, 1.3), None), ((0, 10.1, -28.3), (0.9, 1.1, 0.95), (18, 0, 0)),
                                                    ((0, 9.3, -28.95), (0.45, 0.95, 0.45), (38, 0, 0))], voxel=0.06, smooth=0.6, rough=0.012)
    return [skull, b, lid, beak], {EYE: [glow.object("EX_Eyes", coll, [K.glow_material(EYE)], smooth=True)],
                                PUPIL: [pupils.object("EX_Pupils", coll, [K.glow_material(PUPIL)], smooth=True)],
                           LAVA: [throat.object("EX_Throat", coll, [K.glow_material(LAVA)], smooth=True)]}


def jaw(coll, M):
    o = G.blob("EX_Jaw", coll, M["scute"], [((0, 9.3, -22.0), (2.9, 1.0, 2.6), None), ((0, 9.1, -24.8), (2.1, 0.9, 2.2), None)],
               voxel=0.09, smooth=0.65, rough=0.02, chisel="XuanwuHide")
    beak = G.blob("EX_JawBeak", coll, M["horn"], [((0, 9.15, -26.7), (1.2, 0.72, 1.4), (12, 0, 0))], voxel=0.06, smooth=0.6, rough=0.012)
    return [o, beak], {}


def serpent_neck(coll, M):
    crust, core, spines = Hm.Hi(), Hm.Hi(), Hm.Hi()
    curve = serpent_neck_curve()
    lava_body(crust, core, curve, lambda t: 1.7 - 0.25 * t, band=1.6, seed=9, spines=spines, back=lambda p: V((0, 0.6, 1)))   # the outside of its arc
    c = crust.object("EX_SerpentNeck", coll, [M["crust"]])
    sp = spines.object("EX_SerpentNeckSpines", coll, [M["obsidian"]])
    sp["keep"] = True
    return [c, sp], {LAVA: [core.object("EX_SerpentNeckCore", coll, [K.glow_material(LAVA)], smooth=True)]}


def serpent_head(coll, M):
    """A dragon-serpent's head, crusted black: a long wedge of a skull, its mouth open on molten
    fire, fangs of obsidian, two swept horns and a frill of obsidian spines."""
    # long and flat, wide at the jaw's hinge, tapering to a blunt snout: lobes that overlap closely
    # so the voxel merge reads as one wedge
    head = [((-5.0, 27.55 - 0.05 * k, -13.6 - 1.05 * k), (1.85 - 0.17 * k, 1.15 - 0.08 * k, 1.25), None) for k in range(6)]
    ridges = [((-5.0 + side * 1.15, 28.25, -15.6), (0.55, 0.42, 1.5), (0, side * 8, 0)) for side in (-1, 1)]       # bony ridges over the eyes
    upper = G.blob("EX_SerpentHead", coll, M["crust"], head + ridges, voxel=0.07, smooth=0.45, rough=0.03, chisel="XuanwuCrustChisel")
    jaw_lobes = [((-5.0, 25.95 - 0.22 * k, -13.9 - 1.0 * k), (1.5 - 0.17 * k, 0.48 - 0.03 * k, 1.2), (-14, 0, 0)) for k in range(5)]
    lower = G.blob("EX_SerpentHeadJaw", coll, M["crust"], jaw_lobes, voxel=0.07, smooth=0.45, rough=0.03, chisel="XuanwuCrustChisel")
    glow, pupils, lids, mouth, obs = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    for side in (-1, 1):
        # a snake's stare, cold and sharp: a narrow almond, a thin slit, a hard ridge low over it
        G.eye(glow, pupils, lids, (-5.0 + side * 1.5, 27.95, -15.9), (side * 0.9, 0.3, -0.32), (0, -0.05, -1), 0.72, 0.36, tilt=0.28,
              bulge=0.1, lid=0.36, droop=0.36, lower=0.18, slit=0.13, pupil_height=0.9)
        Hm.htube(obs, [(-5.0 + side * 0.8, 27.9, -14.3), (-5.0 + side * 1.6, 29.6, -11.8), (-5.0 + side * 1.9, 30.0, -9.6),
                       (-5.0 + side * 1.7, 29.6, -8.2)], lambda t: 0.38 * (1 - 0.8 * t), sides=8, per=5, uv_scale=1.0, tip=True, wobble=0.0)
        for k, (z, y) in enumerate(((-18.5, 26.75), (-17.2, 26.7))):                                  # fangs, top and bottom
            cone(obs, (-5.0 + side * 0.55, y, z), (-5.0 + side * 0.5, y - 0.95 + 0.2 * k, z - 0.15), 0.16, sides=6)
        cone(obs, (-5.0 + side * 0.5, 25.85, -18.0), (-5.0 + side * 0.48, 26.55, -18.15), 0.13, sides=6)
        for k in range(4):                                                                           # the frill
            base = V((-5.0 + side * (1.3 + 0.1 * k), 27.4 - 0.35 * k, -12.9 + 0.2 * k))
            cone(obs, base, base + V((side * 1.3, 0.5 - 0.4 * k, 1.1)), 0.24, sides=6)
    sphere(mouth, (-5.0, 26.55, -15.6), 1.0, radii=(0.95, 0.42, 2.0))                              # the fire in its open mouth
    o = obs.object("EX_SerpentHeadHorns", coll, [M["obsidian"]])
    o["keep"] = True
    lid = lids.object("EX_SerpentHeadLids", coll, [M["crust"]])
    lid["keep"] = True
    return [upper, lower, o, lid], {SERPENT_EYE: [glow.object("EX_SerpentEyes", coll, [K.glow_material(SERPENT_EYE)], smooth=True)],
                                    PUPIL: [pupils.object("EX_SerpentPupils", coll, [K.glow_material(PUPIL)], smooth=True)],
                               LAVA: [mouth.object("EX_SerpentMouth", coll, [K.glow_material(LAVA)], smooth=True)]}


def tail(coll, M):
    pts = [(0, 5.6, 15.6), (0, 4.9, 18.4), (0.6, 3.6, 21.0), (1.4, 2.4, 22.6)]
    o = G.blob("EX_Tail", coll, M["skin"], G.capsule_lobes(pts[0], pts[1], 1.9, 1.5, n=4) + G.capsule_lobes(pts[1], pts[3], 1.5, 0.45, n=6),
               voxel=0.1, smooth=0.6, rough=0.03)
    basalt = Hm.Hi()
    rnd = random.Random(41)
    curve = resample(pts, 0.9)
    for k, c in enumerate(curve[1:-1]):
        t = (k + 1) / len(curve)
        column(basalt, c + V((0, 0.6, 0)), V((0, 1, 0.5)), 1.2 + 1.0 * (1 - t), 0.55 * (1 - 0.5 * t), rnd.uniform(0, TAU), chamfer=0.1)
    b = basalt.object("EX_TailColumns", coll, [M["basalt"]], smooth=False)
    b["keep"] = True
    return [o, b], {}


LEGS = {   # shoulder, elbow, foot centre (left side; the right mirrors)
    "Front": ((-8.6, 6.4, -8.6), (-12.4, 5.2, -10.6), (-12.8, 0.0, -11.6)),
    "Back": ((-8.6, 6.0, 10.8), (-12.0, 4.8, 12.6), (-12.3, 0.0, 13.4)),
}


def leg(coll, M, name, side, pair, part):
    sh, el, ft = (V((-side * p[0], p[1], p[2])) for p in LEGS[pair])
    if part == "Upper":
        o = G.blob("EX_" + name, coll, M["skin"], G.capsule_lobes(sh + (sh - el) * 0.25, el, 2.7, 2.5, n=5), voxel=0.12, smooth=0.6, rough=0.03)
        return [o], {}
    # the pillar of a leg and its foot, armoured in great scutes down its outer face, claws of obsidian
    pillar = G.capsule_lobes(el, ft + V((0, 1.4, 0)), 2.5, 2.6, n=5) + [(tuple(ft + V((0, 1.0, -0.4))), (3.0, 1.2, 3.3), None)]
    o = G.blob("EX_" + name, coll, M["skin"], pillar, voxel=0.12, smooth=0.6, rough=0.03)
    plates, claws = Hm.Hi(), Hm.Hi()
    out = V((side, 0, -0.35 if pair == "Front" else 0.35)).normalized()
    rnd = random.Random(len(name))
    for row in range(4):
        y = 4.5 - 1.15 * row
        for k in (-2, -1, 0, 1, 2):
            a = (k + 0.5 * (row % 2)) * 0.5
            d = V((out.x * math.cos(a) - out.z * math.sin(a), 0, out.x * math.sin(a) + out.z * math.cos(a)))
            c = V((el.x + (ft.x - el.x) * (1 - y / el.y), y, el.z + (ft.z - el.z) * (1 - y / el.y)))
            column(plates, c + d * 1.9, d + V((0, 0.25, 0)), 0.85 + rnd.uniform(0, 0.25), 0.68, rnd.uniform(0, TAU), chamfer=0.12)
    for k in range(4):
        a = (-0.75 + 0.5 * k)
        d = V((math.sin(a), 0, -math.cos(a)))
        base = ft + V((0, 0.55, -0.2)) + d * 2.7
        cone(claws, base, base + d * 1.25 + V((0, -0.5, 0)), 0.42, sides=7)
    p = plates.object("EX_" + name + "Scutes", coll, [M["basalt"]], smooth=False)
    p["keep"] = True
    c = claws.object("EX_" + name + "Claws", coll, [M["obsidian"]])
    c["keep"] = True
    return [o, p, c], {}


def segments():
    out = {"Body": body, "Neck": neck, "Head": head, "Jaw": jaw, "SerpentNeck": serpent_neck, "SerpentHead": serpent_head, "Tail": tail}
    for side, s in ((-1, "Left"), (1, "Right")):
        for pair in ("Front", "Back"):
            for part in ("Upper", "Lower"):
                name = pair + s + part
                out[name] = (lambda n, sd, pr, pt: lambda c, M: leg(c, M, n, sd, pr, pt))(name, side, pair, part)
    return out


# pieces baked apart from the rest of their segment's mesh: piece: (segment, its high-detail objects)
PIECES = {"Shell": ("Body", ["EX_ShellColumns"])}       # the basalt shell: ~10k triangles, kept whole, its own maps
BUDGET = {"Shell": 12000, "Body": 9000, "Head": 9000, "SerpentNeck": 7000, "SerpentHead": 7000, "Neck": 5000, "Jaw": 3000, "Tail": 4000}   # each leg piece: 4000


def pivots():
    out = dict(PIVOTS)
    end, _ = coil_end()
    out["SerpentNeck"] = ("Body", tuple(round(c, 2) for c in end))
    return out


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
        out[name] = (hi, glow, coll)
    return out


def bake(names):
    """Bakes these segments' game meshes (built already); records them for export()."""
    parts = bpy.app.driver_namespace.setdefault("xuanwu_parts", {})
    apart = {o for _, objs in PIECES.values() for o in objs}
    for name in names:
        segment, only = PIECES.get(name, (name, None))
        coll = bpy.data.collections[NAME + "_" + segment]
        hi = [o for o in coll.objects if o.name.startswith("EX_") and o.type == "MESH" and (o.name in only if only else o.name not in apart)]
        low = G.bake_piece(NAME, name, hi, coll, BUDGET.get(name, 4000))
        parts[name] = (segment, low.name)
    return {n: B.tris(bpy.data.objects[parts[n][1]]) for n in names}


def export():
    return G.export(NAME, pivots(), bpy.app.driver_namespace["xuanwu_parts"])
