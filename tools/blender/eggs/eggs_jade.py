"""Jade Grove's eggs, second generation (see egg_forge.py).

Jade Spirit Egg, "the vine and the stone": a block of nephrite worked by hand into broad soft
planes, each tilted its own way so it catches the light on its own, marbled with pale veins and
patches of mutton-fat white. Two gnarled vines climb it in opposite spirals, knotted at their nodes
where leaves break out in threes. Where they cross at the front one passes over the other, and there
they hold a large emerald cut as a single leaf, tilted, with Qi running down its midrib and veins.

Bloomwood Egg, "mended with gold": polished rose quartz, cracked and repaired the way a precious bowl
is, with seams of raised gold. A plum branch of gold wire crosses the crown and flowers. Three gold
leaves in relief round a glowing heart on its front. Two lotuses in full bloom at its feet, on a
collar of broad leaves.

Ancient Grove Egg, "the egg that became a tree": a wooden egg in carved planks, grooved and grained,
mossed low down. A bonsai has taken root in its crown: the trunk twists up out of the top, roots pour
down over the planks and grip them, and three flat pads of foliage stand out from the branches. A
Qi spiral carved into the front glows from inside the cut.
"""
import math

import numpy as np

import egg_forge as F
import egg_hi as Hm
import egg_kit as K

V = F.V
W = K.W
TAU = F.TAU


def leaf_triplet(hi, p, along, out, size, mat=0, spread=0.7):
    """Three leaves breaking out of a node: the middle one longest."""
    along, out = V(along).normalized(), V(out).normalized()
    side = along.cross(out).normalized()
    for k, (ang, scale) in enumerate(((-spread, 0.8), (0.0, 1.0), (spread, 0.8))):
        d = (along * math.cos(ang) + side * math.sin(ang) + out * 0.5).normalized()
        n = (out - d * out.dot(d)).normalized()
        # each starts a little way out along itself: sharing one base point, their first faces overlap
        Hm.leaf(hi, p + d * 0.03 + out * (k * 0.006), d, n, size * scale, size * scale * 0.3, mat=mat, fold=0.28, curl=0.28, twist=0.25 * (k - 1), steps=9, across=4, shape=0.72)


def surface_path(points, off, lift=None):
    """(s, v) waypoints laid on the shell, `off` above it."""
    out = []
    for i, (s, v) in enumerate(points):
        o = off(i / (len(points) - 1)) if callable(off) else off
        out.append(F.on(s % 1.0, v, o))
    return out


# ---------- Jade Spirit Egg ----------
JS_GEM = "2cff8a"
JS_AT = (0.5, 0.5)


def jade_spirit_paint():
    f = F.Field()
    P = f.P
    warp = np.stack([F.fbm(P, 1.7, 3, seed=s) for s in (61, 62, 63)], -1) * 0.14
    f1, edge, cid = F.voronoi(P + warp * 0.5, 2.5, seed=66, jitter=1.0, stretch=(1.0, 0.72, 1.0))
    bevel = F.sstep(0.0, 0.09, edge)
    t1, t2, t3 = np.sin(cid * 917.3), np.cos(cid * 371.1), np.sin(cid * 113.7)
    tilt = 0.038 * (t1 * P[..., 0] + t2 * P[..., 2] + t3 * (P[..., 1] - 1.3) * 0.5)
    seam = 1 - F.sstep(0.0, 0.011, edge)
    height = (tilt + 0.022) * bevel - 0.012 * seam + 0.0012 * F.fbm(P, 22.0, 2, seed=64)
    cloud = F.fbm(P + warp, 1.5, 5, 0.55, seed=67)
    tone = np.clip(0.45 + cloud * 0.8 + (cid - 0.5) * 0.5, 0, 1)
    col = F.ramp(tone, [(0.0, "04301c"), (0.3, "0a5a33"), (0.6, "128550"), (0.85, "35b07a"), (1.0, "6fd3a2")])
    # veins, thin and pale, branching through it
    veins = 1 - F.sstep(0.0, 0.016, F.ridged(P + warp * 1.5, 1.8, 4, 0.55, seed=68))
    col = F.mix(col, np.array((0.72, 0.93, 0.78)), veins * 0.34)
    # mutton-fat patches: milky white jade
    fat = F.sstep(0.2, 0.55, F.fbm(P + warp, 1.1, 4, seed=69))
    col = F.mix(col, np.array((0.83, 0.93, 0.8)), fat * 0.5)
    # each plane brighter in its middle, as light sits inside polished stone
    col = col * (0.72 + 0.34 * bevel)[..., None]
    col = F.mix(col, np.array((0.5, 1.0, 0.72)), seam * 0.75)
    col = col + np.array((0.0, 0.14, 0.08)) * (np.clip(F.blur(seam, 8) * 1.6, 0, 1) * (1 - seam))[..., None]
    rough = np.clip(0.2 + 0.12 * (1 - bevel) + 0.08 * fat, 0, 1)
    return f, np.clip(col, 0, 1), rough, np.zeros(f.S.shape), height


def js_vines(coll):
    bark = Hm.mat_bark("JS_Bark", moss=0.5)
    leaf = Hm.mat_leaf("JS_Leaf", base=(0.02, 0.2, 0.05), mid=(0.08, 0.46, 0.1), tip=(0.32, 0.72, 0.16), rib=(0.55, 0.85, 0.3))
    hi, leaves = Hm.Hi(), Hm.Hi()
    crossings = (0.08, 0.45, 0.82)
    for r in range(2):
        s0, ds = (-0.1075, 1.35) if r == 0 else (1.1075, -1.35)
        route, offs = [], []
        for i in range(25):
            t = i / 24
            vv = 0.025 + 0.9 * t ** 0.9 + 0.012 * math.sin(t * 17 + r * 2)
            route.append((s0 + ds * t, min(vv, 0.96)))
            # who passes over whom, turn about at each crossing
            over = 0.0
            for k, c in enumerate(crossings):
                if (k % 2 == 1) == (r == 1):
                    over += 0.075 * math.exp(-((t - c) / 0.035) ** 2)
            offs.append(0.03 + over + 0.012 * math.sin(t * 31 + r))
        pts = [F.on(a % 1.0, b, o) for (a, b), o in zip(route, offs)]
        pts = [V((p.x, max(p.y, 0.125), p.z)) for p in pts]      # the vine's underside stays above the ground
        curve = Hm.htube(hi, pts, lambda t: 0.1 * (1 - 0.78 * t ** 0.85) + 0.012, sides=10, per=4, knots=12, seed=70 + r)
        for t, flip in ((0.14, 1), (0.28, -1), (0.56, 1), (0.68, -1), (0.8, 1), (0.92, -1), (1.0, 1)):
            i = min(len(curve) - 1, int(t * (len(curve) - 1)))
            p = curve[i]
            along = (curve[i] - curve[max(0, i - 3)]).normalized()
            out = V((p.x, 0.14, p.z)).normalized()
            stem = p + out * 0.04
            sign = flip if r == 0 else -flip
            leaf_triplet(leaves, stem, along + along.cross(out) * sign * 0.8, out, 0.46 * (1.12 - 0.42 * t))
    o = hi.object("JS_Vines", coll, [bark])
    o["w"] = 1.0
    l = leaves.object("JS_Leaves", coll, [leaf])
    Hm.solidify(l, 0.014)
    l["w"] = 1.6
    return o, l


def js_gem(coll):
    """An emerald cut as one leaf: a pointed outline, a ridge down its midrib, a facet between each
    pair of side veins. Tilted, so it hangs from the crossing like a real leaf."""
    c, n = F.on(JS_AT[0], JS_AT[1], 0.11), F.normal(*JS_AT)
    roll = math.radians(-34)
    e1 = V((0, 1, 0)).cross(n).normalized()
    e2 = n.cross(e1).normalized()
    across, up = e1 * math.cos(roll) + e2 * math.sin(roll), e2 * math.cos(roll) - e1 * math.sin(roll)
    L, Wd, rows = 0.44, 0.215, 7
    hi = Hm.Hi()
    uv = [(0, 0), (1, 0), (1, 1), (0, 1)]

    def outline(t):
        return Wd * (math.sin(math.pi * t ** 0.72) ** 0.82) + 0.006

    mid, left, right, back_l, back_r = [], [], [], [], []
    for i in range(rows + 1):
        t = i / rows
        y = -L + 2 * L * t
        w = outline(t)
        centre = c + up * y
        # side points run a little ahead of the midrib: leaf veins sweep toward the tip
        mid.append(hi.v(centre + n * (0.1 * math.sin(math.pi * t) ** 0.6 + 0.012)))
        left.append(hi.v(c + up * (y + 0.05 * math.sin(math.pi * t)) - across * w + n * 0.01))
        right.append(hi.v(c + up * (y + 0.05 * math.sin(math.pi * t)) + across * w + n * 0.01))
        back_l.append(hi.v(c + up * y - across * w * 0.9 - n * 0.12))
        back_r.append(hi.v(c + up * y + across * w * 0.9 - n * 0.12))
    for i in range(rows):
        hi.f([mid[i], left[i], left[i + 1]], uv[:3])
        hi.f([mid[i], left[i + 1], mid[i + 1]], uv[:3])
        hi.f([mid[i], mid[i + 1], right[i + 1]], uv[:3])
        hi.f([mid[i], right[i + 1], right[i]], uv[:3])
        hi.f([left[i], back_l[i], back_l[i + 1], left[i + 1]], uv)
        hi.f([right[i], right[i + 1], back_r[i + 1], back_r[i]], uv)
    gem = F.fix_normals(hi.object("JS_Gem", coll, [F.gem_material("JS_GemMat", (0.0, 0.16, 0.06), (0.01, 0.66, 0.24), (0.5, 1.0, 0.62), pane_weight=0.1, panes=6.0, axis=tuple(W.rb(*n)))], smooth=False))
    gem["w"] = 3.0
    glow = Hm.Hi()
    spine = [(c + up * (-L * 0.92 + 2 * L * 0.92 * t / 20) + n * (0.1 * math.sin(math.pi * (0.04 + 0.92 * t / 20)) ** 0.6 + 0.016), n) for t in range(21)]
    F.prism(glow, spine, lambda t: 0.02 * (1 - 0.65 * t), height=lambda w: w * 0.35)
    # paired side veins from the midrib out across each facet
    for i in range(1, rows):
        t = i / rows
        y = -L + 2 * L * t
        w = outline(t) * 0.8
        for sign in (-1, 1):
            start = c + up * y + n * (0.1 * math.sin(math.pi * t) ** 0.6 + 0.016)
            end = c + up * (y + 0.05 * math.sin(math.pi * t) * 0.8 + 0.03) + across * sign * w + n * 0.03
            line = [(start.lerp(end, q / 6), n) for q in range(7)]
            F.prism(glow, line, lambda q: 0.012 * (1 - q), height=lambda v: v * 0.35)
    return gem, glow.object("JS_Midrib", coll, [K.glow_material(JS_GEM)], smooth=False, weld=0)


def jade_spirit_clay():
    coll = W.collection("JadeSpiritEggHi")
    shell = F.shell_mesh("JS_Shell", coll, 96, 64)
    v, l = js_vines(coll)
    g, m = js_gem(coll)
    return {o.name: F.tris(o) for o in (shell, v, l, g, m)}


def jade_spirit_build():
    coll = W.collection("JadeSpiritEggHi")
    f, col, rough, metal, height = jade_spirit_paint()
    mat = F.shell_material("JS_Stone", col, rough, metal)
    v, l = js_vines(coll)
    g, m = js_gem(coll)
    return F.assemble("JadeSpiritEgg", coll, mat, height, [v, l, g], {JS_GEM: [m]}, budget=8500, shell_frac=0.6, low_nu=72, low_nv=46)


# ---------- Bloomwood Egg ----------
BW_HEART = "ff2e9a"
BW_AT = (0.5, 0.47)


def bw_leaf_shape(x, y, ang, length, width):
    """Distance-like measure for one leaf in the plane, growing out of the origin at `ang`: < 0
    inside, plus its position along (0..1) and across (signed)."""
    ca, sa = math.cos(ang), math.sin(ang)
    a = x * ca + y * sa
    b = -x * sa + y * ca
    t = a / length
    half = width * np.sin(np.pi * np.clip(t, 0, 1) ** 0.75) ** 0.85
    return np.abs(b) - half, np.clip(t, -0.2, 1.2), b


def bloomwood_paint():
    f = F.Field()
    P, Vv = f.P, f.V
    warp = np.stack([F.fbm(P, 1.5, 3, seed=s) for s in (81, 82, 83)], -1) * 0.18
    # rose quartz: milky clouds drifting in it, deepest low down, nearly white at the crown
    cloud = F.fbm(P + warp, 1.7, 5, 0.55, seed=84)
    col = F.ramp(np.clip(Vv * 0.8 + cloud * 0.45 + 0.08, 0, 1), [(0.0, "a82e68"), (0.25, "d14f8e"), (0.5, "ec7fb0"), (0.75, "f8aecd"), (1.0, "ffe4ef")])
    # inclusions: white needles frozen in the stone, seen a little below the surface
    silk = 1 - F.sstep(0.0, 0.05, F.ridged(P * np.array((1.0, 0.45, 1.0)) + warp, 4.0, 3, seed=85))
    col = F.mix(col, np.array((1.0, 0.92, 0.95)), silk * 0.2)
    height = 0.0005 * F.fbm(P, 30.0, 2, seed=86)
    # the mend: fracture lines filled with raised gold, thick and thin as a brush lays them
    lines = F.ridged(P + warp * 0.7, 1.15, 3, 0.45, seed=87)
    width = 0.008 + 0.012 * np.clip(F.fbm(P, 2.6, 2, seed=88) + 0.45, 0, 1)
    gold = 1 - F.sstep(width * 0.75, width * 1.1, lines)
    gold = gold * F.sstep(-0.1, 0.1, F.fbm(P, 0.9, 2, seed=89) + 0.12)     # some cracks stop, not all join up
    # the emblem: three leaves in relief round a heart
    x, y, front = f.plane(*BW_AT)
    fill = np.zeros(x.shape)
    rim = np.zeros(x.shape)
    vein = np.zeros(x.shape)
    for ang, length, wid in ((math.pi / 2, 0.62, 0.2), (math.pi / 2 + 1.0, 0.54, 0.17), (math.pi / 2 - 1.0, 0.54, 0.17)):
        d, t, b = bw_leaf_shape(x, y, ang, length, wid)
        inside = (t > 0) & (t < 1)
        fill = np.maximum(fill, (d < 0) * inside * (1.0 - F.sstep(-0.03, 0.0, d) * 0))
        rim = np.maximum(rim, (np.abs(d) < 0.013) * inside)
        v = (np.abs(b) < 0.006 + 0.004 * (1 - t)) | ((np.abs(((t - np.abs(b) * 1.8) * 6.0) % 1.0 - 0.5) < 0.05) & (d < -0.012))
        vein = np.maximum(vein, v * (d < 0) * inside)
    fill = fill * (front > 0.2)
    rim = rim * (front > 0.2)
    vein = vein * (front > 0.2)
    col = F.mix(col, F.ramp(np.clip(np.hypot(x, y) / 0.62, 0, 1), [(0.0, "ffd0e8"), (0.5, "c43f86"), (1.0, "8a1c58")]), fill)
    gold_all = np.maximum.reduce([gold * (1 - fill), rim, vein * 0.9])
    gold_all = F.blur(gold_all, 1) if False else gold_all
    gold_col = F.mix(np.array((0.8, 0.54, 0.16)), np.array((1.0, 0.84, 0.42)), np.clip(0.5 + F.fbm(P, 22.0, 2, seed=90) * 0.8, 0, 1))
    col = F.mix(col, gold_col, gold_all)
    height = height + 0.02 * F.blur(fill, 2) + 0.012 * F.blur(gold_all, 1.2)
    rough = 0.1 + 0.2 * gold_all + 0.08 * fill
    metal = 0.85 * gold_all
    return f, np.clip(col, 0, 1), rough, metal, height


def bw_petal(name):
    """Clear pink, not dusty: saturated from root to a pale tip, the veins only a little deeper."""
    g = Hm._Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    col = g.ramp(v, [(0.0, (0.72, 0.02, 0.26)), (0.3, (0.95, 0.14, 0.42)), (0.7, (1.0, 0.42, 0.66)), (1.0, (1.0, 0.82, 0.9))])
    w = g.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", **{"Scale": 9.0, "Distortion": 1.5, "Detail": 2.0})
    mp = g.n("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 0.15, 1.0)
    g.link(g.coords("UV"), mp.inputs["Vector"])
    g.link(mp.outputs[0], w.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", g.math("SUBTRACT", w.outputs["Fac"], 0.6, clamp=True), 0.4), col, (0.82, 0.08, 0.36))
    return g.finish(col, 0.38, 0.0, g.bump(w.outputs["Fac"], 0.15, 0.004))


def bw_blossom(hi, gold_hi, p, n, size, mat=0):
    """A plum blossom: five rounded notched petals round gold stamens."""
    n = V(n).normalized()
    e1 = n.cross(V((0, 1, 0)) if abs(n.y) < 0.9 else V((1, 0, 0))).normalized()
    e2 = n.cross(e1)
    for k in range(5):
        a = TAU * k / 5 + 0.3
        d = e1 * math.cos(a) + e2 * math.sin(a)
        Hm.leaf(hi, p + d * size * 0.16 + n * (size * 0.05 + 0.006 * k), (d + n * 0.5).normalized(), n, size, size * 0.44, mat=mat, fold=0.05, curl=-0.1, steps=7, across=4, shape=0.42, notch=0.5, cup=0.25)
    for k in range(5):
        a = TAU * (k + 0.5) / 5
        q = p + (e1 * math.cos(a) + e2 * math.sin(a)) * size * 0.2 + n * size * 0.28
        Hm.htube(gold_hi, [p + n * size * 0.05, p.lerp(q, 0.6) + n * 0.005, q], lambda t: size * 0.03 * (1 - 0.4 * t), sides=5, per=2, wobble=0)
    # the short stem that carries the flower, down into the shell
    Hm.htube(gold_hi, [p - n * 0.06, p + n * size * 0.08], lambda t: size * 0.06, sides=6, per=2, wobble=0, tip=False)


def bw_branch(coll, gold, petal_mat):
    gold_hi, petals = Hm.Hi(), Hm.Hi()
    # the bough crosses the crown from the back and comes down the front-right shoulder
    trunk = [(0.1, 0.52), (0.13, 0.64), (0.2, 0.74), (0.32, 0.82), (0.47, 0.86), (0.6, 0.8), (0.7, 0.73), (0.74, 0.66), (0.79, 0.62), (0.77, 0.57), (0.8, 0.53)]
    curve = surface_path(trunk, 0.02)
    Hm.htube(gold_hi, curve, lambda t: 0.04 * min(1.0, t * 7.0) ** 0.8 * (1 - 0.86 * t) + 0.004, sides=7, per=5, knots=7, seed=91, wobble=0.5, tip=True)
    twigs = (((0.2, 0.74), (0.24, 0.66), (0.33, 0.62), (0.38, 0.65)), ((0.32, 0.82), (0.26, 0.91), (0.14, 0.92), (0.05, 0.86)),
             ((0.47, 0.86), (0.54, 0.94), (0.72, 0.93), (0.82, 0.86)), ((0.6, 0.8), (0.55, 0.72), (0.56, 0.66)),
             ((0.7, 0.72), (0.8, 0.72), (0.9, 0.67), (0.95, 0.6)), ((0.13, 0.64), (0.04, 0.62), (0.97, 0.66)))
    blossoms = [(0.38, 0.655, 0.2), (0.3, 0.63, 0.15), (0.05, 0.86, 0.19), (0.17, 0.925, 0.15), (0.82, 0.86, 0.21), (0.66, 0.935, 0.16), (0.56, 0.66, 0.17),
                (0.95, 0.6, 0.2), (0.86, 0.695, 0.14), (0.97, 0.66, 0.17), (0.79, 0.535, 0.21), (0.75, 0.6, 0.13)]
    for tw in twigs:
        Hm.htube(gold_hi, surface_path(tw, 0.016), lambda t: 0.018 * (1 - 0.6 * t) + 0.004, sides=6, per=5, seed=92, wobble=0.3)
    for s_, v_, size in blossoms:
        bw_blossom(petals, gold_hi, F.on(s_ % 1.0, v_, 0.018), F.normal(s_ % 1.0, v_), size)
    g = gold_hi.object("BW_Filigree", coll, [gold])
    p = petals.object("BW_Blossoms", coll, [petal_mat])
    Hm.solidify(p, 0.01)
    p["w"] = 1.3
    return g, p


def bw_lotus(hi, c, axis, scale, mat=0):
    """A lotus in full bloom: three whorls of cupped petals, the inner ones nearly closed."""
    axis = V(axis).normalized()
    e1 = axis.cross(V((1, 0, 0)) if abs(axis.x) < 0.9 else V((0, 0, 1))).normalized()
    e2 = axis.cross(e1)
    for ring, (count, tilt, length, phase) in enumerate(((9, 0.28, 0.44, 0.0), (8, 0.72, 0.4, 0.5), (6, 1.15, 0.3, 0.2))):
        for k in range(count):
            a = TAU * (k + phase) / count
            r = e1 * math.cos(a) + e2 * math.sin(a)
            d = (r * math.cos(tilt) + axis * math.sin(tilt)).normalized()
            Hm.leaf(hi, c + r * scale * (0.07 * (3 - ring) + 0.012 * (k % 2)) + axis * scale * (0.035 * ring + 0.006 * (k % 3)), d, axis, length * scale, length * scale * 0.42, mat=mat, fold=0.14, curl=0.42, steps=9, across=4, shape=0.58, cup=0.3)


def bw_base(coll, gold):
    petal = bw_petal("BW_Petal")
    lf = Hm.mat_leaf("BW_Leaf", base=(0.02, 0.17, 0.08), mid=(0.05, 0.4, 0.2), tip=(0.28, 0.66, 0.26), rib=(0.85, 0.78, 0.4))
    leaves, lotus = Hm.Hi(), Hm.Hi()
    # a collar of broad leaves cupping the base, each lifted from under the egg
    for k in range(9):
        a = TAU * (k + 0.5) / 9
        out = V((math.sin(a), 0, math.cos(a)))
        base = out * 0.34 + V((0, 0.055, 0))
        d = (out + V((0, 0.95, 0))).normalized()
        n = (V((0, 1, 0)) - d * d.y + out * -0.5).normalized()
        Hm.leaf(leaves, base, d, n, 0.95, 0.3, fold=0.2, curl=-0.2, twist=0.15 * (1 if k % 2 else -1), steps=12, across=6, shape=0.62, cup=0.12)
    l = leaves.object("BW_Collar", coll, [lf])
    Hm.solidify(l, 0.016)
    l["w"] = 3.0
    for side in (-1, 1):
        a = side * 0.72
        c = V((math.sin(a) * 1.02, 0.25, math.cos(a) * 1.02))
        bw_lotus(lotus, c, (math.sin(a) * 0.42, 1.0, math.cos(a) * 0.42), 1.0)
    o = lotus.object("BW_Lotus", coll, [petal])
    Hm.solidify(o, 0.012)
    o["w"] = 1.5
    gh = Hm.Hi()
    for side in (-1, 1):
        a = side * 0.72
        c = V((math.sin(a) * 1.02, 0.31, math.cos(a) * 1.02))
        F.rivet(gh, c + V((0, 0.05, 0)), (math.sin(a) * 0.42, 1.0, math.cos(a) * 0.42), 0.09, rings=4, sides=12)
    pod = gh.object("BW_Pods", coll, [gold])
    pod["w"] = 2.0
    return l, o, pod


def bw_heart(coll):
    c, n = F.on(BW_AT[0], BW_AT[1], 0.018), F.normal(*BW_AT)
    hi = Hm.Hi()
    F.cut_gem(hi, c, n, (0, 1, 0), 0.098, 0.075, sides=6, base=0.03)
    gem = F.fix_normals(hi.object("BW_Heart", coll, [F.gem_material("BW_HeartMat", (0.3, 0.0, 0.16), (1.0, 0.1, 0.5), (1.0, 0.72, 0.88), pane_weight=0.1, panes=20.0, axis=tuple(W.rb(*n)))], smooth=False))
    gem["w"] = 3.0
    e1 = V((0, 1, 0)).cross(n).normalized()
    e2 = n.cross(e1).normalized()
    glow = Hm.Hi()
    pts = [(c + (e1 * math.cos(TAU * k / 36) + e2 * math.sin(TAU * k / 36)) * 0.115 + n * 0.006, n) for k in range(36)]
    F.prism(glow, pts, 0.016, height=lambda w: w * 0.3, closed=True)
    ring = glow.object("BW_HeartRing", coll, [K.glow_material(BW_HEART)], smooth=False, weld=0)
    return gem, ring


def bw_all(coll):
    gold = Hm.mat_gold("BW_Gold")
    petal = bw_petal("BW_BlossomPetal")
    g, p = bw_branch(coll, gold, petal)
    l, o, pod = bw_base(coll, gold)
    gem, ring = bw_heart(coll)
    return [g, p, l, o, pod, gem], ring


def bloomwood_clay():
    coll = W.collection("BloomwoodEggHi")
    shell = F.shell_mesh("BW_Shell", coll, 96, 64)
    pieces, h = bw_all(coll)
    return {o.name: F.tris(o) for o in [shell, h] + pieces}


def bloomwood_build():
    coll = W.collection("BloomwoodEggHi")
    f, col, rough, metal, height = bloomwood_paint()
    mat = F.shell_material("BW_Quartz", col, rough, metal)
    pieces, h = bw_all(coll)
    return F.assemble("BloomwoodEgg", coll, mat, height, pieces, {BW_HEART: [h]}, budget=10500, shell_frac=0.56, low_nu=56, low_nv=36, ao_floor=0.66)


# ---------- Ancient Grove Egg ----------
AG_QI = "5cff2e"
AG_AT = (0.5, 0.46)


def ag_spiral(size=0.4, turns=2.2, steps=90):
    out = []
    for i in range(steps):
        t = i / (steps - 1)
        a = -math.pi / 2 + turns * TAU * t
        r = size * (1 - t) ** 0.8 + 0.018
        out.append((math.cos(a) * r, math.sin(a) * r))
    return out


def ancient_grove_paint():
    f = F.Field()
    P, S, Vv = f.P, f.S, f.V
    warp = F.fbm(P * np.array((1.0, 0.25, 1.0)), 2.2, 3, seed=101)
    count = 15
    xs = S * count + warp * 0.18
    idx = np.floor(xs)
    across = xs - idx                      # 0..1 across one plank
    per = (np.sin(idx * 127.1) * 43758.5453) % 1.0
    # grain: long lines running up each plank, bending round the occasional knot
    q = np.stack([across * 3.2 + idx * 1.7, f.Y * 0.8, idx * 0.9], -1)
    bend = F.fbm(q * np.array((1.0, 2.2, 1.0)), 1.0, 3, seed=102)
    grain = 0.5 + 0.5 * np.sin((across * 11.0 + idx * 3.0 + bend * 7.5) * TAU * 0.5)
    fine = F.fbm(np.stack([across * 22.0, f.Y * 2.0, idx * 1.3], -1), 1.0, 3, seed=103)
    groove = 1 - F.sstep(0.0, 0.07, np.minimum(across, 1 - across))
    height = -0.04 * groove + 0.016 * (per - 0.5) * (1 - groove) + 0.007 * grain + 0.004 * fine
    tone = np.clip(0.2 + 0.55 * per + 0.3 * grain * 0.6 + fine * 0.2, 0, 1)
    col = F.ramp(tone, [(0.0, "2a1709"), (0.3, "4d2e15"), (0.6, "6f4822"), (0.85, "946a38"), (1.0, "b88d58")])
    col = col * (1 - 0.72 * groove)[..., None]
    # wear on the planks' shoulders
    shoulder = F.sstep(0.07, 0.12, np.minimum(across, 1 - across)) * (1 - F.sstep(0.12, 0.2, np.minimum(across, 1 - across)))
    col = F.mix(col, np.array((0.72, 0.55, 0.34)), shoulder * 0.35)
    # moss: gathers low and in the grooves, broken up
    patches = F.fbm(P, 2.8, 4, 0.55, seed=104)
    moss = np.clip(F.sstep(0.62, 0.05, Vv) * 1.1 + groove * 0.45 * F.sstep(0.75, 0.2, Vv), 0, 1) * F.sstep(-0.12, 0.25, patches)
    tuft = F.fbm(P, 34.0, 3, seed=105)
    col = F.mix(col, F.ramp(np.clip(tuft + 0.5, 0, 1), [(0.0, "26400f"), (0.5, "4f7a1c"), (1.0, "8fb53a")]), moss)
    height = height + moss * (0.014 + 0.01 * tuft)
    # the spiral carved into the front: a deep clean cut with a chamfer
    x, y, front = f.plane(*AG_AT)
    d, along = F.seg_dist(x, y, ag_spiral())
    cut = (1 - F.sstep(0.022, 0.05, d)) * (front > 0.2)
    col = F.mix(col, np.array((0.12, 0.08, 0.03)), cut * 0.85)
    glow_spill = np.clip(np.exp(-(d / 0.09) ** 2), 0, 1) * (front > 0.2) * (1 - cut)
    col = col + np.array((0.08, 0.2, 0.02)) * glow_spill[..., None]
    moss = moss * (1 - cut)
    height = height * (1 - cut) - 0.03 * F.blur(cut, 1.5)
    rough = np.clip(0.72 - 0.15 * grain + 0.2 * moss, 0, 1)
    return f, np.clip(col, 0, 1), rough, np.zeros(S.shape), height


def ag_tree(coll):
    bark = Hm.mat_bark("AG_Bark", moss=0.9, base=(0.09, 0.055, 0.03), ridge=(0.42, 0.3, 0.16))
    hi = Hm.Hi()
    # the roots: pouring over the crown, each finding its own way down between the planks
    routes = (((0.52, 0.97), (0.47, 0.84), (0.34, 0.72), (0.32, 0.62), (0.22, 0.5), (0.21, 0.38)),
              ((0.72, 0.97), (0.74, 0.85), (0.68, 0.76), (0.76, 0.64), (0.75, 0.52), (0.8, 0.42), (0.78, 0.32)),
              ((0.9, 0.97), (0.94, 0.86), (0.04, 0.76), (0.02, 0.62), (0.1, 0.5)),
              ((0.2, 0.97), (0.14, 0.85), (0.24, 0.8), (0.14, 0.68), (0.12, 0.6)),
              ((0.62, 0.95), (0.6, 0.84), (0.63, 0.74), (0.58, 0.68)),
              ((0.4, 0.95), (0.42, 0.86), (0.38, 0.8)))
    for k, route in enumerate(routes):
        big = 0.1 if k < 3 else 0.065
        pts = surface_path(route, lambda t: 0.04 * (1 - 0.6 * t))
        Hm.htube(hi, pts, lambda t: big * (1 - 0.85 * t ** 0.85) + 0.006, sides=9, per=5, knots=5, seed=110 + k)
    # the trunk: flares out of the roots, twists, thins
    top = F.H
    trunk = [(0.0, top - 0.1, 0.0), (0.03, top + 0.08, -0.02), (0.14, top + 0.34, 0.02), (0.1, top + 0.6, 0.1), (-0.06, top + 0.82, 0.08), (-0.1, top + 1.03, 0.02)]
    Hm.htube(hi, trunk, lambda t: 0.25 * (1 - 0.62 * t) ** 1.2 * (1 + 0.5 * (1 - min(1.0, t * 5)) ** 2), sides=14, per=8, knots=9, seed=117, tip=True)
    branches = (((0.12, top + 0.42, 0.04), (0.42, top + 0.5, 0.02), (0.68, top + 0.47, 0.1), (0.88, top + 0.6, 0.12)),
                ((0.0, top + 0.72, 0.09), (-0.3, top + 0.76, 0.14), (-0.56, top + 0.76, 0.16), (-0.78, top + 0.88, 0.14)),
                ((-0.09, top + 0.95, 0.04), (-0.02, top + 1.18, 0.02), (0.12, top + 1.4, 0.0)),
                ((0.32, top + 0.48, 0.03), (0.42, top + 0.62, -0.1), (0.46, top + 0.74, -0.2)))
    for k, b in enumerate(branches):
        Hm.htube(hi, b, lambda t: 0.08 * (1 - 0.6 * t), sides=9, per=6, knots=3, seed=120 + k)
    o = hi.object("AG_Tree", coll, [bark])
    o["w"] = 1.2
    return o


def ag_foliage():
    """Clumps of pine-like leaves: bright sprays on top, deep green beneath and between, every spray
    its own green, needles drawn across each."""
    g = Hm._Graph("AG_Foliage")
    co = g.coords()
    geo = g.n("ShaderNodeNewGeometry")
    up = g.sep(geo.outputs["Normal"])[2]
    cell = g.n("ShaderNodeTexVoronoi", **{"Scale": 15.0})
    g.link(co, cell.inputs["Vector"])
    edge = g.n("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE", **{"Scale": 15.0})
    g.link(co, edge.inputs["Vector"])
    fine = g.n("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE", **{"Scale": 54.0})
    g.link(co, fine.inputs["Vector"])
    col = g.ramp(g.bw(cell.outputs["Color"]), [(0.0, (0.035, 0.2, 0.035)), (0.45, (0.08, 0.36, 0.05)), (0.8, (0.2, 0.54, 0.07)), (1.0, (0.42, 0.68, 0.12))])
    gap = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", edge.outputs["Distance"], 8.0), clamp=True)
    col = g.mix(g.math("MULTIPLY", gap, 0.85), col, (0.006, 0.05, 0.015))
    needle = g.math("SUBTRACT", 1.0, g.math("MULTIPLY", fine.outputs["Distance"], 12.0), clamp=True)
    col = g.mix(g.math("MULTIPLY", needle, 0.45), col, (0.01, 0.1, 0.02))
    # undersides sink into shade
    shade = g.math("MULTIPLY", g.math("SUBTRACT", 0.2, up, clamp=True), 1.3)
    col = g.mix(g.math("MINIMUM", shade, 1.0), col, (0.004, 0.035, 0.012))
    nrm = g.bump(g.math("ADD", edge.outputs["Distance"], g.math("MULTIPLY", fine.outputs["Distance"], 0.5)), 0.9, 0.018)
    return g.finish(col, 0.62, 0.0, nrm)


def ag_pads(coll):
    foliage = ag_foliage()
    pads = ((0.92, F.H + 0.6, 0.12, 0.56, 0.2), (-0.84, F.H + 0.88, 0.14, 0.52, 0.19), (0.12, F.H + 1.4, 0.0, 0.62, 0.22), (0.48, F.H + 0.84, -0.26, 0.34, 0.15))
    import random
    rnd = random.Random(131)
    out = []
    for i, (x, y, z, rad, thick) in enumerate(pads):
        lobes = []
        # flat beneath, domed above: the look of cloud pruning
        for k in range(int(40 * rad / 0.5)):
            a = rnd.uniform(0, TAU)
            r = rad * math.sqrt(rnd.uniform(0, 1))
            lift = thick * 0.8 * (1 - (r / rad) ** 2)
            lobes.append(((x + math.cos(a) * r, y + lift, z + math.sin(a) * r), rnd.uniform(0.075, 0.125)))
        o = Hm.foliage("AG_Pad%d" % i, coll, foliage, lobes, voxel=0.02, roughness=0.075)
        # cut flat below
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(o.data)
        for v in bm.verts:
            zz = v.co.z
            floor = y - 0.05
            if zz < floor:
                v.co.z = floor + (zz - floor) * 0.15
        # only the main mass stays: clumps that came apart would hang in the air
        seen, islands = set(), []
        for v in bm.verts:
            if v in seen:
                continue
            stack, part = [v], []
            seen.add(v)
            while stack:
                q = stack.pop()
                part.append(q)
                for e in q.link_edges:
                    w = e.other_vert(q)
                    if w not in seen:
                        seen.add(w)
                        stack.append(w)
            islands.append(part)
        islands.sort(key=len, reverse=True)
        for part in islands[1:]:
            bmesh.ops.delete(bm, geom=part, context="VERTS")
        bm.to_mesh(o.data)
        bm.free()
        o["w"] = 1.0
        out.append(o)
    return out


def ag_spiral_glow(coll):
    hi = Hm.Hi()
    s0, v0 = AG_AT
    c, n = F.on(s0, v0), F.normal(s0, v0)
    e1 = V((0, 1, 0)).cross(n).normalized()
    e2 = n.cross(e1).normalized()
    pts = []
    for x, y in ag_spiral()[::1]:
        q = c + e1 * x + e2 * y
        ss = (math.atan2(q.x, q.z) / TAU + 0.5) % 1.0
        vv = math.acos(max(-1, min(1, 1 - 2 * q.y / F.H))) / math.pi
        pts.append((F.on(ss, vv, -0.018), F.normal(ss, vv)))
    F.prism(hi, pts, lambda t: 0.032 * (1 - 0.5 * t), height=lambda w: w * 0.28)
    return hi.object("AG_Spiral", coll, [K.glow_material(AG_QI)], smooth=False, weld=0)


def ancient_grove_clay():
    coll = W.collection("AncientGroveEggHi")
    shell = F.shell_mesh("AG_Shell", coll, 96, 64)
    tree = ag_tree(coll)
    pads = ag_pads(coll)
    g = ag_spiral_glow(coll)
    return {o.name: F.tris(o) for o in [shell, tree, g] + pads}


def ancient_grove_build():
    coll = W.collection("AncientGroveEggHi")
    f, col, rough, metal, height = ancient_grove_paint()
    mat = F.shell_material("AG_Planks", col, rough, metal)
    tree = ag_tree(coll)
    pads = ag_pads(coll)
    g = ag_spiral_glow(coll)
    return F.assemble("AncientGroveEgg", coll, mat, height, [tree] + pads, {AG_QI: [g]}, budget=8800, shell_frac=0.56, low_nu=60, low_nv=38)
