"""Jade Grove eggs (after the 15-egg concept sheet), built the way the sculpted pets are: high-detail
pieces with procedural shaders (egg_hi.py), baked onto a game mesh with colour, normal,
roughness and metalness maps (egg_bake.py). Glowing parts stay separate (Neon in the game).

- Jade Spirit Egg: large cut facets of jade, Qi glowing in the seams between them, caged by thick
  knotted bark branches that sprout twigs and clusters of leaves; two of them frame a bark-bound
  bezel round a glowing jade-leaf gem in the front.
- Bloomwood Egg: facets of blossom-pink crystal veined with gold, gold filigree branching over
  the crown, two rows of broad leaves cupping the lower half, an emblem of three leaves in relief
  with a gold rim round a glowing heart, and a lotus in bloom either side of the base.
- Ancient Grove Egg: carved wood in upright planks with real grooves, pale heartwood showing
  through cracks that split the crown; a mossy trunk behind it whose roots grip the egg and whose
  branches spread into lumpy crowns of leaves; a spiral of Qi glowing on its front.

    import eggs_jade as J
    J.build()           # the high-detail eggs, in collections JadeSpiritEgg, BloomwoodEgg, ...
    J.export_all()      # bake and export: assets/eggs/<EggId>.fbx plus its maps
"""
import math
import random

import bpy

import egg_bake as B
import egg_hi as Hm
import egg_kit as K

W = K.W
V = K.V
TAU = K.TAU
H, R = K.H, K.R


def on(u, v, off=0.0):
    return K.egg_point(u, v, offset=off)[0]


def normal_at(u, v):
    return K.egg_point(u, v)[1]


def surface_path(points, off, per=4):
    """A smooth path over the egg through (u, v) points, `off` above the shell."""
    return [V(p) for p in W.catmull([tuple(on(u, v, off)) for u, v in points], per)]


def gnarled(base, taper=0.5):
    return lambda t: base * (1 - taper * t)


def uv_of(p):
    """The (u, v) of the shell point nearest to p (by direction from the axis and height)."""
    y = max(0.0, min(H, p.y))
    return (math.atan2(p.x, p.z) / TAU) % 1.0, math.acos(max(-1.0, min(1.0, 1 - 2 * y / H))) / math.pi


def cluster(hi, at, out, count, size, seed, mat, spread=0.9, droop=0.15):
    """A cluster of leaves fanning out from `at` round the direction `out`."""
    rnd = random.Random(seed)
    out = V(out).normalized()
    ref = V((0, 1, 0)) if abs(out.y) < 0.9 else V((1, 0, 0))
    s = out.cross(ref).normalized()
    t = out.cross(s).normalized()
    for k in range(count):
        a = TAU * k / count + rnd.uniform(-0.3, 0.3)
        d = (out + (s * math.cos(a) + t * math.sin(a)) * spread + V((0, -droop, 0))).normalized()
        nrm = (V((0, 1, 0)) - d * d.y).normalized() if abs(d.y) < 0.95 else s
        Hm.leaf(hi, at, d, nrm, size * rnd.uniform(0.8, 1.15), size * rnd.uniform(0.3, 0.38), mat,
                fold=0.18, curl=rnd.uniform(-0.25, 0.1), twist=rnd.uniform(-0.5, 0.5), steps=6, across=2)


# ---------- Jade Spirit Egg ----------
JS_SEAM = "17c25e"     # Qi glowing in the seams between the jade facets
JS_GEM = "2cff8a"      # the jade-leaf gem in the front


def vesica(cu, cv, hu, hv, n=20):
    """A pointed oval (a leaf outline, pointed top and bottom) round (cu, cv) in (u, v)."""
    half = n // 2
    right = [(cu + hu * (1 - t * t), cv + hv * t) for t in (1 - 2 * i / half for i in range(half))]
    left = [(cu - hu * (1 - t * t), cv + hv * t) for t in (-1 + 2 * i / half for i in range(half))]
    return right + left


def jade_spirit(coll, M):
    mb = W.MeshBuilder()
    sites = K.surface_sites(26, seed=31) + [K.egg_point(0.0, 0.0)[0]]
    K.crystal_plates(mb, (0.5, 0.5), sites, gap=0.955, lift=(0.0, 0.012), tilt=0.06, depth=0.1, seed=32, peak=0.07)
    plates = mb.object("JS_Plates", coll, M["jade"])
    plates["keep"] = True        # the cut facets are already low: decimating them breaks the cuts
    core = W.MeshBuilder()
    K.shell(core, (0.5, 0.5), nu=32, nv=20, offset=-0.05)
    seams = core.object("JS_Core", coll, K.glow_material(JS_SEAM))

    bark, leaves, glow = Hm.Hi(), Hm.Hi(), Hm.Hi()
    OFF = 0.15                           # the facets stand up to about 0.1 off the shell
    branches = []
    # the arch: two branches climbing either side of the gem, crossing over it and running on over
    # the crown and down the back
    for side in (1, -1):
        branches.append(([(-0.14 * side, 0.08), (-0.135 * side, 0.22), (-0.12 * side, 0.4), (-0.09 * side, 0.58), (-0.035 * side, 0.72),
                          (0.04 * side, 0.8), (0.14 * side, 0.86), (0.27 * side, 0.88), (0.4 * side, 0.8), (0.46 * side, 0.6)], 0.095, 3 + side))
    # four more branches winding up the sides and back, crossing into a loose cage
    for k, (u0, du, v0, v1) in enumerate(((0.2, 0.36, 0.1, 0.9), (0.8, -0.36, 0.1, 0.9), (0.4, 0.32, 0.12, 0.84), (0.6, -0.3, 0.12, 0.8))):
        branches.append(([(u0 + du * t + 0.03 * math.sin(t * 7 + k), v0 + (v1 - v0) * t) for t in (i / 7 for i in range(8))], 0.075, 10 + k))
    rnd = random.Random(33)
    for path, radius, seed in branches:
        pts = surface_path(path, OFF)
        Hm.htube(bark, pts, gnarled(radius, 0.55), sides=12, per=3, uv_scale=3.0, tip=True, knots=4, seed=seed)
        # leaves sprouting along the branch on alternate sides, lying back along it over the jade,
        # and every so often a short twig ending in a cluster
        for j in range(3, len(pts) - 2, 3):
            p = pts[j]
            u, v = uv_of(p)
            if v < 0.2 or (abs(((u + 0.5) % 1.0) - 0.5) < 0.1 and 0.26 < v < 0.66):
                continue           # nothing on the underside, nor over the gem
            nrm = normal_at(u, v)
            along = (pts[j + 1] - pts[j - 1]).normalized()
            side = along.cross(nrm).normalized() * (1 if (j // 3) % 2 else -1)
            centre_u = abs(((u + 0.5) % 1.0) - 0.5)
            if centre_u < 0.2 and (p + side * 0.3).x * p.x < p.x * p.x:
                side = -side       # by the gem, leaves grow away from it
            if (j // 3) % 3 == 2:
                d = (nrm * 0.6 + side * 0.6 + along * 0.3).normalized()
                twig = [p, p + d * 0.07, p + d * 0.13 + along * 0.03]
                Hm.htube(bark, twig, gnarled(radius * 0.38, 0.6), sides=6, per=3, uv_scale=3.0, tip=False, seed=seed + j)
                cluster(leaves, twig[-1], d + along * 0.4, 3, rnd.uniform(0.3, 0.36), seed * 7 + j, 0, spread=0.75, droop=0.05)
            else:
                d = (side * 0.8 + along * 0.45 + nrm * 0.25).normalized()
                Hm.leaf(leaves, p + nrm * radius * 0.5, d, nrm, rnd.uniform(0.3, 0.38), rnd.uniform(0.11, 0.13), 0,
                        fold=0.2, curl=rnd.uniform(-0.3, -0.12), twist=rnd.uniform(-0.4, 0.4), steps=6, across=2)
        # a cluster where the branch ends
        end_dir = (pts[-1] - pts[-4]).normalized()
        cluster(leaves, pts[-1], end_dir + normal_at(*uv_of(pts[-1])) * 0.6, 4, 0.34, seed * 13, 0, spread=0.8)
    # the bezel: bark wrapped round the gem, two arcs meeting at its points
    cu, cv = 0.0, 0.46
    outline = vesica(cu, cv, 0.09, 0.17)
    frame = [on(u, v, 0.17) for u, v in outline]
    half = len(frame) // 2
    for arc in (frame[:half + 1], frame[half:] + frame[:1]):
        Hm.htube(bark, arc, lambda t: 0.055 * (0.8 + 0.2 * math.sin(math.pi * t)), sides=10, per=3, uv_scale=3.0, tip=False, knots=2, seed=71)
    # the gem: a cut jade leaf, facets rising from its rim to a ridge along its middle
    rim = [on(cu + (u - cu) * 0.86, cv + (v - cv) * 0.86, 0.15) for u, v in outline]
    centre, cn = K.egg_point(cu, cv, offset=0.15)
    top, bottom = rim[0], rim[half]
    ridge = [bottom.lerp(top, k / 6) + cn * (0.16 * math.sin(math.pi * k / 6) + 0.02) for k in range(7)]
    idx_rim = [glow.v(p) for p in rim]
    idx_ridge = [glow.v(p) for p in ridge]

    def ridge_at(p):   # the ridge point at the same height as a rim point
        t = max(0.0, min(1.0, (p - bottom).dot((top - bottom).normalized()) / (top - bottom).length))
        return min(6, max(0, round(t * 6)))
    m = len(rim)
    for i in range(m):
        j = (i + 1) % m
        a, b = ridge_at(rim[i]), ridge_at(rim[j])
        if a == b:
            glow.facing([idx_rim[i], idx_rim[j], idx_ridge[a]], [(0, 0)] * 3, cn)
        else:
            glow.facing([idx_rim[i], idx_rim[j], idx_ridge[b], idx_ridge[a]], [(0, 0)] * 4, cn)
    # veins carved over the gem (bark), so the flat Neon in the game reads as a jade leaf: a midrib
    # over its ridge and three pairs of side veins sweeping up and out to its rim
    lift = cn * 0.02
    Hm.htube(bark, [p + lift for p in ridge], lambda t: 0.018 * (0.6 + 0.4 * math.sin(math.pi * t)), sides=6, per=3, uv_scale=3.0, tip=False)
    for t in (0.2, 0.4, 0.6):
        root = ridge[min(6, round(t * 6))] + lift
        reach = min(0.95, t + 0.22)       # each vein reaches the rim higher up than it leaves the midrib
        for edge in (rim[half - round(reach * half)], rim[(half + round(reach * half)) % m]):
            tip = edge + lift
            Hm.htube(bark, [root, root.lerp(tip, 0.5) + cn * 0.03, tip], lambda x: 0.012 * (1 - 0.5 * x), sides=5, per=3, uv_scale=3.0, tip=False)
    branches_obj = bark.object("JS_Branches", coll, [M["bark"]])
    leaves_obj = Hm.solidify(leaves.object("JS_Leaves", coll, [M["leaf"]]), 0.012)
    leaves_obj["sheet"] = True
    gem = glow.object("JS_Gem", coll, [K.glow_material(JS_GEM)], smooth=False)
    return [plates, branches_obj, leaves_obj], {JS_SEAM: [seams], JS_GEM: [gem]}


# ---------- Bloomwood Egg ----------
BW_HEART = "ff2e9a"     # the emblem's glowing heart
BW_LOTUS = "ffa51e"     # the lotus hearts


def hug_leaf(hi, cu, v_base, v_tip, half_width, off, mat, rib=0.06, steps=10, across=6):
    """A broad leaf lying on the egg and cupping it: centred on u = cu from v_base up to its point
    at v_tip, its midrib raised by `rib`, its edges curling off the shell. UVs across and along."""
    rows = []
    for i in range(steps + 1):
        t = i / steps
        v = v_base + (v_tip - v_base) * t
        w = half_width * math.sin(math.pi * min(1.0, 0.1 + 0.9 * t)) ** 0.7 * (1.2 - 0.45 * t)
        row = []
        for j in range(across + 1):
            x = -1 + 2 * j / across
            lift = off + rib * (1 - abs(x)) ** 1.5 * math.sin(math.pi * min(1.0, 0.1 + t)) + 0.05 * x * x
            row.append(hi.v(on(cu + w * x, v, lift)))
        rows.append(row)
    for i in range(steps):
        n = normal_at(cu, v_base + (v_tip - v_base) * (i + 0.5) / steps)
        for j in range(across):
            uv = [(j / across, i / steps), ((j + 1) / across, i / steps), ((j + 1) / across, (i + 1) / steps), (j / across, (i + 1) / steps)]
            hi.facing([rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]], uv, n, mat)


def relief(hi, cu, cv, hu, hv, lift, base, mat, dome=0.04, n=24, rings=4):
    """A raised pointed-oval plate on the egg (a leaf in relief): domed, with walls down to base."""
    outline = vesica(cu, cv, hu, hv, n)
    grid = [[hi.v(on(cu + (u - cu) * (1 - r / rings), cv + (v - cv) * (1 - r / rings), lift + dome * math.sin(math.pi / 2 * r / rings)))
             for u, v in outline] for r in range(rings)]
    centre_n = normal_at(cu, cv)
    c = hi.v(on(cu, cv, lift + dome))
    for r in range(rings):
        for i in range(n):
            j = (i + 1) % n
            uv = [(i / n, r / rings), ((i + 1) / n, r / rings), ((i + 1) / n, (r + 1) / rings), (i / n, (r + 1) / rings)]
            if r == rings - 1:
                hi.facing([grid[r][i], grid[r][j], c], uv[:3], centre_n, mat)
            else:
                hi.facing([grid[r][i], grid[r][j], grid[r + 1][j], grid[r + 1][i]], uv, centre_n, mat)
    bot = [hi.v(on(u, v, base)) for u, v in outline]
    for i in range(n):
        j = (i + 1) % n
        u, v = outline[i]
        out = on(u, v) - on(cu, cv)
        hi.facing([grid[0][i], grid[0][j], bot[j], bot[i]], [(0, 0), (1, 0), (1, 1), (0, 1)], tuple(out), mat)
    return outline


def lotus(hi, glow, centre, axis, size, seed, mat):
    """A lotus in bloom: three rings of cupped petals opening wider ring by ring round a heart of
    glowing seeds."""
    rnd = random.Random(seed)
    axis = V(axis).normalized()
    ref = V((0, 1, 0)) if abs(axis.y) < 0.9 else V((1, 0, 0))
    s = axis.cross(ref).normalized()
    t = axis.cross(s).normalized()
    c = V(centre)
    for ring_i, (count, open_deg, length, width, phase) in enumerate(((5, 30, 0.5, 0.2, 0.0), (8, 55, 0.72, 0.24, 0.5), (10, 78, 0.82, 0.25, 0.25))):
        for k in range(count):
            a = TAU * (k + phase) / count + rnd.uniform(-0.07, 0.07)
            radial = s * math.cos(a) + t * math.sin(a)
            op = math.radians(open_deg + rnd.uniform(-6, 6))
            d = axis * math.cos(op) + radial * math.sin(op)
            Hm.leaf(hi, c + radial * 0.04 * ring_i * size, d, axis * 0.7 - radial * 0.7, length * size, width * size, mat,
                    fold=-0.05, cup=0.35, curl=0.3 if ring_i < 2 else 0.15, steps=7, across=4, shape=0.6, notch=0.4)
    for k in range(7):
        a = TAU * k / 7
        p = c + axis * (0.24 if k == 0 else 0.2) * size + (s * math.cos(a) + t * math.sin(a)) * 0.11 * size * (0 if k == 0 else 1)
        K.gem(glow, p, axis, t, 0.13 * size, 0.13 * size, 0.09 * size, (0.5, 0.5))


def bloomwood(coll, M):
    mb = W.MeshBuilder()
    sites = K.surface_sites(40, seed=41) + [K.egg_point(0.0, 0.0)[0]]
    K.crystal_plates(mb, (0.5, 0.5), sites, gap=0.975, lift=(0.0, 0.008), tilt=0.05, depth=0.08, seed=42, peak=0.04)
    shell = mb.object("BW_Shell", coll, M["crystal"])
    shell["keep"] = True
    inner = W.MeshBuilder()
    K.shell(inner, (0.5, 0.5), nu=32, nv=20, offset=-0.04)
    under = inner.object("BW_Under", coll, M["gold"])     # gold showing in the seams between the facets
    under["keep"] = True
    gold, leaves, petals, heart = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    lotus_glow = W.MeshBuilder()
    rnd = random.Random(43)
    # gold filigree branching down over the crown from its tip
    for k in range(6):
        u0 = k / 6 + 0.04
        path = [(u0 + 0.06 * math.sin(t * 4 + k) * t, 0.99 - 0.4 * t) for t in (i / 6 for i in range(7))]
        pts = surface_path(path, 0.05)
        Hm.htube(gold, pts, lambda t: 0.024 * (1 - 0.65 * t), sides=8, per=3, uv_scale=3.0, tip=True)
        for j, sgn in ((len(pts) // 3, 1), (2 * len(pts) // 3, -1)):     # twigs curling off it
            u, v = uv_of(pts[j])
            twig = surface_path([(u, v), (u + 0.035 * sgn, v - 0.04), (u + 0.045 * sgn, v - 0.08), (u + 0.03 * sgn, v - 0.1)], 0.05, per=3)
            Hm.htube(gold, twig, lambda t: 0.015 * (1 - 0.6 * t), sides=6, per=2, uv_scale=3.0, tip=True)
    # two rows of broad leaves cupping the lower half; the front ones stand lower for the emblem
    for row, (count, off, v_lo, base_tip, phase) in enumerate(((7, 0.035, 0.08, 0.5, 0.0), (7, 0.07, 0.06, 0.38, 0.5))):
        for k in range(count):
            cu = (k + phase) / count + rnd.uniform(-0.01, 0.01)
            front = abs(((cu + 0.5) % 1.0) - 0.5)
            v_tip = base_tip - (0.14 if front < 0.12 else 0.0) + rnd.uniform(-0.03, 0.03)
            hug_leaf(leaves, cu, v_lo, v_tip, 0.085 if row == 0 else 0.075, off, 0)
    # the emblem: three leaves in relief, one inside the other, a gold rim round the outermost,
    # and a glowing heart
    cv = 0.47
    outline = relief(leaves, 0.0, cv, 0.08, 0.16, 0.06, -0.01, 0, dome=0.02)
    relief(leaves, 0.0, cv - 0.005, 0.058, 0.115, 0.1, 0.03, 0, dome=0.025)
    relief(leaves, 0.0, cv - 0.01, 0.038, 0.075, 0.15, 0.08, 0, dome=0.03)
    rim = [on(u, v, 0.075) for u, v in outline]
    half = len(rim) // 2
    for arc in (rim[:half + 1], rim[half:] + rim[:1]):
        Hm.htube(gold, arc, lambda t: 0.022, sides=8, per=3, uv_scale=3.0, tip=False)
    hp, hn = K.egg_point(0.0, cv - 0.015, offset=0.2)
    hb = W.MeshBuilder()
    K.gem(hb, hp, hn, (0, 1, 0), 0.15, 0.3, 0.12, (0.5, 0.5))
    # a lotus either side of the base, leaning out toward the front
    for side in (1, -1):
        p, n = K.egg_point(0.15 * side, 0.2, offset=0.26)
        out = V((n.x, 0, n.z)).normalized()
        lotus(petals, lotus_glow, p, out * 0.55 + V((0, 1, 0)), 0.95, seed=50 + side, mat=0)
    g = gold.object("BW_Gold", coll, [M["gold"]])
    lv = Hm.solidify(leaves.object("BW_Leaves", coll, [M["leaf"]]), 0.016)
    pt = Hm.solidify(petals.object("BW_Petals", coll, [M["petal"]]), 0.012)
    pt["sheet"] = True
    hrt = hb.object("BW_Heart", coll, K.glow_material(BW_HEART))
    lg = lotus_glow.object("BW_LotusHearts", coll, K.glow_material(BW_LOTUS))
    return [shell, under, g, lv, pt], {BW_HEART: [hrt], BW_LOTUS: [lg]}


# ---------- Ancient Grove Egg ----------
AG_SPIRAL = "5cff2e"


def plank(hi, u0, u1, v0, v1, lift, depth, seed, mat=0, nu=3, nv=8):
    """One carved plank on the egg between u0..u1 and v0..v1: its face `lift` off the shell,
    gently rounded across, its edges wavering a little like hand-carved wood, with walls down to
    `depth` under the shell. One mesh island, so it takes its own wood tone."""
    rnd = random.Random(seed)
    wob = rnd.uniform(0, TAU)

    def corner(i, j):
        u = u0 + (u1 - u0) * i / nu
        v = v0 + (v1 - v0) * j / nv
        u += 0.004 * math.sin(v * 17 + wob) * (1 if 0 < i < nu else 0.6)
        x = 2 * i / nu - 1
        return u, v, lift * (1 - 0.35 * x * x) + 0.004 * math.sin(v * 31 + wob)
    top = [[hi.v(on(*corner(i, j)[:2], corner(i, j)[2])) for i in range(nu + 1)] for j in range(nv + 1)]
    for j in range(nv):
        for i in range(nu):
            n = normal_at((u0 + u1) / 2, v0 + (v1 - v0) * (j + 0.5) / nv)
            hi.facing([top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]], [(0, 0), (1, 0), (1, 1), (0, 1)], n, mat)
    edge = [(i, 0) for i in range(nu)] + [(nu, j) for j in range(nv)] + [(i, nv) for i in range(nu, 0, -1)] + [(0, j) for j in range(nv, 0, -1)]
    cu, cv = (u0 + u1) / 2, (v0 + v1) / 2
    for k in range(len(edge)):
        (i0, j0), (i1, j1) = edge[k], edge[(k + 1) % len(edge)]
        u_a, v_a, _ = corner(i0, j0)
        u_b, v_b, _ = corner(i1, j1)
        a, b = top[j0][i0], top[j1][i1]
        a2, b2 = hi.v(on(u_a, v_a, -depth)), hi.v(on(u_b, v_b, -depth))
        out = on((u_a + u_b) / 2, (v_a + v_b) / 2) - on(cu, cv)
        hi.facing([a, b, b2, a2], [(0, 0), (1, 0), (1, 1), (0, 1)], tuple(out), mat)


def ancient_grove(coll, M):
    mb = W.MeshBuilder()
    # carved planks: fourteen upright columns round the egg, each split once or twice at its own
    # heights, under a domed cap at the crown and a disc at the base
    wood = Hm.Hi()
    rnd_p = random.Random(61)
    cols, gap = 14, 0.0045
    for i in range(cols):
        u0, u1 = i / cols + gap, (i + 1) / cols - gap
        splits = sorted(rnd_p.uniform(0.25, 0.75) for _ in range(rnd_p.choice((1, 2))))
        edges = [0.07] + splits + [0.88]
        for k in range(len(edges) - 1):
            plank(wood, u0, u1, edges[k] + 0.006, edges[k + 1] - 0.006, rnd_p.uniform(0.04, 0.065), 0.05, seed=i * 10 + k)
    for v0, v1, seed in ((0.893, 1.0, 901), (0.0, 0.064, 902)):
        rings = 4
        pts = [[on(i / 24, v0 + (v1 - v0) * j / rings, 0.05) for i in range(24)] for j in range(rings + 1)]
        idx = [[wood.v(p) for p in row] for row in pts]
        for j in range(rings):
            for i in range(24):
                n = normal_at((i + 0.5) / 24, v0 + (v1 - v0) * (j + 0.5) / rings)
                wood.facing([idx[j][i], idx[j][(i + 1) % 24], idx[j + 1][(i + 1) % 24], idx[j + 1][i]], [(0, 0), (1, 0), (1, 1), (0, 1)], n)
    planks = wood.object("AG_Planks", coll, [M["wood"]], smooth=False, weld=0)
    planks["keep"] = True
    # under the planks: dark bark in the grooves, pale heartwood toward the crown, so the seams
    # there read as the crown splitting open
    low_in, high_in = W.MeshBuilder(), W.MeshBuilder()
    K.shell(low_in, (0.5, 0.5), nu=32, nv=14, offset=-0.035, v_to=0.72)
    K.shell(high_in, (0.5, 0.5), nu=32, nv=6, offset=-0.035, v_from=0.72)
    grooves = low_in.object("AG_Grooves", coll, M["grovebark"])
    grooves["keep"] = True
    heart = high_in.object("AG_Heartwood", coll, M["heartwood"])
    heart["keep"] = True
    bark = Hm.Hi()
    rnd = random.Random(63)
    # the trunk behind the egg, and the roots it sends round the egg's base
    trunk = [V((0, 0.15, -0.66)), on(0.5, 0.24, 0.2), on(0.5, 0.4, 0.21), on(0.5, 0.56, 0.17)]
    Hm.htube(bark, trunk, lambda t: 0.22 * (1 - 0.3 * t), sides=14, per=4, uv_scale=2.5, tip=False, knots=3, seed=69)
    for k, u in enumerate((0.17, 0.3, 0.42, 0.58, 0.7, 0.83, 0.9)):
        u += rnd.uniform(-0.015, 0.015)
        path = [(u, 0.44 + rnd.uniform(-0.04, 0.04)), (u + 0.02, 0.32), (u + 0.035, 0.2), (u + 0.04, 0.1)]
        Hm.htube(bark, surface_path(path, 0.13), gnarled(0.085, 0.55), sides=10, per=3, uv_scale=2.5, tip=True, knots=2, seed=70 + k)
    # branches: from the back round the sides, breaking away up and out into crowns of leaves,
    # each forking once into a second, smaller crown
    specs = [(0.6, 0.25, 0.24, 0.58, 1, 0.8, 0.45), (0.4, 0.28, 0.79, 0.66, -1, 0.65, 0.6), (0.56, 0.42, 0.34, 0.84, 1, 0.5, 0.75),
             (0.44, 0.4, 0.69, 0.78, -1, 0.85, 0.4), (0.5, 0.55, 0.52, 0.96, 1, 0.3, 0.8)]
    crowns = []
    for k, (u0, v0, u1, v1, side, reach_out, reach_up) in enumerate(specs):
        path = [on(u0 + (u1 - u0) * t, v0 + (v1 - v0) * t, 0.12) for t in (0.0, 0.33, 0.66, 1.0)]
        tip_on, tn = K.egg_point(u1, v1, offset=0.12)
        out = V((tn.x, 0, tn.z)).normalized()
        reach = [tip_on + out * reach_out * 0.45 + V((0, reach_up * 0.6, 0)), tip_on + out * reach_out + V((0, reach_up, 0))]
        Hm.htube(bark, path + reach, gnarled(0.11, 0.6), sides=12, per=4, uv_scale=2.5, tip=False, knots=3, seed=80 + k)
        end = V(reach[-1])
        r = (0.36, 0.3, 0.32, 0.38, 0.28)[k]
        crowns.append([(tuple(end + V((dx, dy, dz)) * r), r * s_) for dx, dy, dz, s_ in
                       ((0, 0.25, 0, 0.75), (0.55, 0.05, 0.2, 0.55), (-0.5, 0.1, -0.25, 0.55), (0.1, 0.5, -0.4, 0.5), (-0.2, -0.1, 0.45, 0.5))])
        fork_from = V(reach[0])
        fork_to = fork_from + out.cross(V((0, 1, 0))).normalized() * 0.4 * side + V((0, 0.45, 0)) + out * 0.25
        Hm.htube(bark, [fork_from, (fork_from + fork_to) / 2 + V((0, 0.08, 0)), fork_to], gnarled(0.06, 0.6), sides=8, per=3,
                 uv_scale=2.5, tip=False, seed=85 + k)
        crowns.append([(tuple(fork_to + V((dx, dy, dz)) * 0.24), 0.24 * s_) for dx, dy, dz, s_ in
                       ((0, 0.3, 0, 0.75), (0.5, 0, 0.3, 0.55), (-0.45, 0.05, -0.3, 0.55))])
    crown_objs = [Hm.foliage(f"AG_Crown{k}", coll, M["foliage"], lobes, voxel=0.03, seed=k) for k, lobes in enumerate(crowns)]
    # the spiral of Qi on the front, low and to the right, its tail sweeping up
    glow = W.MeshBuilder()
    su, sv = 0.06, 0.3
    spiral = []
    for i in range(40):
        t = i / 39
        a = TAU * 2.1 * t
        r = 0.012 + 0.11 * t
        spiral.append(on(su + r * math.cos(a) * 0.55, sv + r * math.sin(a), 0.07))
    for i in range(6):
        t = (i + 1) / 6
        spiral.append(on(su + 0.08 - 0.07 * t, sv + 0.1 + 0.09 * t, 0.07))
    K.tube(glow, spiral, lambda t: 0.036 * (0.45 + 0.55 * math.sin(math.pi * min(1.0, t * 1.15))), 6, (0.5, 0.5), per=1)
    b = bark.object("AG_Tree", coll, [M["grovebark"]])
    g = glow.object("AG_Spiral", coll, K.glow_material(AG_SPIRAL))
    return [planks, grooves, heart, b] + crown_objs, {AG_SPIRAL: [g]}


EGGS = {"JadeSpiritEgg": (jade_spirit, 14000), "BloomwoodEgg": (bloomwood, 14000), "AncientGroveEgg": (ancient_grove, 15000)}


def materials():
    return {"jade": Hm.mat_jade(), "bark": Hm.mat_bark("EggBarkJade", moss=0.25), "leaf": Hm.mat_leaf(),
            "crystal": Hm.mat_crystal(), "petal": Hm.mat_petal(), "wood": Hm.mat_wood(), "heartwood": Hm.mat_heartwood(),
            "foliage": Hm.mat_foliage(), "gold": Hm.mat_gold(), "grovebark": Hm.mat_bark("EggBarkGrove", moss=0.8, base=(0.07, 0.045, 0.025), ridge=(0.34, 0.24, 0.13))}


def build(only=None):
    M = materials()
    root = W.collection("EggsHi")
    out = {}
    for egg_id, (fn, budget) in EGGS.items():
        if only and egg_id not in only:
            continue
        coll = W.collection(egg_id + "Hi", root)
        W.clear_collection(coll)
        hi, glow = fn(coll, M)
        out[egg_id] = (hi, glow, coll, budget)
    return out


def export_all(only=None):
    """Builds, bakes and exports the eggs. Returns {egg_id: (game mesh tris, exported parts)}."""
    report = {}
    for egg_id, (hi, glow, coll, budget) in build(only).items():
        low = B.make_low(egg_id, hi, coll, budget)
        B.bake(egg_id, hi, low)
        parts = B.export(egg_id, low, glow, coll)
        report[egg_id] = (B.tris(low), [p.name for p in parts])
    return report
