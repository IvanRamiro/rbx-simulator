"""Moonlit Isle's eggs, second generation (see egg_forge.py).

Celestial Egg, "the star chart": black-blue lacquer, real constellations inlaid in gold wire with
small stars at their joints, a drift of mother-of-pearl where the Milky Way runs across it. Behind it
stands a great silver crescent, thick at its foot and tapering to two horns above the shoulders, the
egg resting in its curve; from one horn a pearl hangs on a thread of silver.

Astral Sanctum Egg, "the egg is the shrine": it stays an egg. Six slim pointed windows are set deep into
smooth moonstone, the blue sheen drifting across it, with violet light behind fine gold tracery and slim
pilasters between them. Above a scalloped cornice the whole crown of the egg IS the gold dome, ribbed and
following the shell's own curve, with a slender spire at the very top carrying an orb and a flame-shaped tip.
No plinth, no onion, no symbol from any real faith, and nothing that hides the shape.

Heavenly Throne Egg, "the enthroned": pearl with a soft fire in it, belted with gold and small pearls. A
small coronet sits on its crown. It rests on a three-tier cushion of carved cloud, each tier scalloped and
edged in gold. Behind it, open air: a slim oval mandorla of gold, with a sunburst of broad wavy rays rising
from its upper half. No backing plate, so the egg is what you see.
"""
import math

import numpy as np

import egg_forge as F
import egg_hi as Hm
import egg_kit as K

V = F.V
W = K.W
TAU = F.TAU


def lay_on(s0, v0, off=0.0):
    """A function from plane coordinates at (s0, v0) to a point and normal on the shell."""
    c, n = F.on(s0, v0), F.normal(s0, v0)
    e1 = V((0, 1, 0)).cross(n).normalized()
    e2 = n.cross(e1).normalized()

    def fn(x, y, o=off):
        q = c + e1 * x + e2 * y
        ss = (math.atan2(q.x, q.z) / TAU + 0.5) % 1.0
        vv = math.acos(max(-1, min(1, 1 - 2 * max(0.001, min(F.H - 0.001, q.y)) / F.H))) / math.pi
        return F.on(ss, vv, o), F.normal(ss, vv)
    return fn


def sphere(hi, c, r, mat=0, rings=10, sides=16):
    """A UV sphere: for pearls and orbs."""
    c = V(c)
    grid = []
    for j in range(rings + 1):
        th = math.pi * j / rings
        grid.append([hi.v(c + V((math.sin(th) * math.cos(TAU * k / sides), math.cos(th), math.sin(th) * math.sin(TAU * k / sides))) * r) for k in range(sides)])
    for j in range(rings):
        for k in range(sides):
            n = (k + 1) % sides
            hi.f([grid[j][k], grid[j][n], grid[j + 1][n], grid[j + 1][k]], [(0, 0), (1, 0), (1, 1), (0, 1)], mat)


def lathe(hi, profile, sides=48, mat=0, centre=(0, 0, 0), ribs=0, rib_depth=0.0):
    """A body of revolution round the y axis through `profile` [(radius, y)]; ribs > 0 scallops it
    into that many lobes, as a melon dome is."""
    c = V(centre)
    rows = []
    for r, y in profile:
        row = []
        for k in range(sides):
            a = TAU * k / sides
            rr = r * (1 + rib_depth * (abs(math.cos(a * ribs / 2)) ** 0.6 - 0.65)) if ribs else r
            row.append(hi.v(c + V((math.sin(a) * rr, y, math.cos(a) * rr))))
        rows.append(row)
    for j in range(len(rows) - 1):
        for k in range(sides):
            n = (k + 1) % sides
            hi.f([rows[j][k], rows[j][n], rows[j + 1][n], rows[j + 1][k]], [(k / sides, j), ((k + 1) / sides, j), ((k + 1) / sides, j + 1), (k / sides, j + 1)], mat)


# ---------- Celestial Egg ----------
CE_STAR = "ffc23a"
# constellations: (s, v, roll, [(x, y)...], [(a, b)...]) drawn on a plane on the egg
CE_SKIES = (
    (0.5, 0.52, 0.0, ((-0.42, 0.32), (-0.2, 0.42), (0.02, 0.26), (0.26, 0.34), (0.36, 0.06), (0.14, -0.14), (-0.1, -0.02), (0.3, -0.38)), ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 2), (5, 6), (4, 7))),
    (0.19, 0.42, 0.3, ((-0.3, 0.3), (-0.08, 0.14), (0.14, 0.2), (0.32, -0.04), (0.04, -0.2), (-0.22, -0.32)), ((0, 1), (1, 2), (2, 3), (3, 4), (4, 1), (4, 5))),
    (0.81, 0.46, -0.2, ((-0.34, -0.12), (-0.14, 0.12), (0.1, 0.02), (0.28, 0.28), (0.34, -0.24), (0.1, -0.34)), ((0, 1), (1, 2), (2, 3), (2, 4), (4, 5), (5, 2))),
    (0.0, 0.5, 0.1, ((-0.28, 0.36), (0.0, 0.2), (0.26, 0.32), (0.08, -0.08), (-0.2, -0.24), (0.3, -0.3)), ((0, 1), (1, 2), (1, 3), (3, 4), (3, 5))),
)


def celestial_paint():
    f = F.Field()
    P = f.P
    warp = np.stack([F.fbm(P, 1.3, 3, seed=s) for s in (501, 502, 503)], -1) * 0.2
    # the lacquer: near black, with a blue depth rising toward the crown
    col = F.ramp(np.clip(f.V * 1.1 + F.fbm(P, 1.2, 3, seed=504) * 0.2, 0, 1), [(0.0, "02030a"), (0.45, "050a1f"), (0.8, "0a1638"), (1.0, "132353")])
    # the Milky Way: a band across the egg, tilted, made of mother-of-pearl flakes that change colour
    band = np.exp(-(((P[..., 1] - 1.35 - 0.55 * P[..., 0]) / 0.5) ** 2))
    cloud = np.clip(F.fbm(P + warp, 2.2, 5, 0.55, seed=505) * 1.6 + 0.3, 0, 1)
    _, shard_edge, shard = F.voronoi(P, 24.0, seed=506, jitter=1.0)
    flake = (shard > 0.45) * F.sstep(0.0, 0.03, shard_edge)
    shimmer = F.ramp((shard * 3.7 + P[..., 0] * 0.5) % 1.0, [(0.0, "6a8cff"), (0.25, "78e0d8"), (0.5, "f0a8e0"), (0.75, "9a78ff"), (1.0, "6a8cff")])
    amount = band * cloud
    col = F.mix(col, shimmer * 0.5, np.clip(amount * flake * 0.9, 0, 1))
    col = F.mix(col, np.array((0.2, 0.26, 0.55)), np.clip(amount * 0.42, 0, 1))
    # stars: a fine dust, a few brighter
    f1, _, cid = F.voronoi(P, 30.0, seed=507)
    col = F.mix(col, np.array((0.85, 0.9, 1.0)), (1 - F.sstep(0.02, 0.07, f1)) * (cid > 0.55))
    f2, _, cid2 = F.voronoi(P, 12.0, seed=508)
    col = F.mix(col, np.array((1.0, 0.97, 0.86)), (1 - F.sstep(0.02, 0.06, f2)) * (cid2 > 0.72))
    height = np.zeros(f.S.shape)
    # the wire: raised gold
    wire = np.zeros(f.S.shape)
    for s0, v0, roll, stars, lines in CE_SKIES:
        x, y, front = f.plane(s0, v0, roll=roll)
        for a, b in lines:
            d, _ = F.seg_dist(x, y, [stars[a], stars[b]])
            wire = np.maximum(wire, (1 - F.sstep(0.005, 0.009, d)) * (front > 0.25))
    gold = F.mix(np.array((0.82, 0.58, 0.2)), np.array((1.0, 0.86, 0.46)), np.clip(0.5 + F.fbm(P, 24.0, 2, seed=509) * 0.8, 0, 1))
    col = F.mix(col, gold, wire)
    height = height + 0.007 * F.blur(wire, 1) + 0.0006 * F.fbm(P, 40.0, 2, seed=510)
    rough = np.clip(0.07 + 0.2 * wire + 0.12 * np.clip(amount * flake, 0, 1), 0, 1)
    metal = 0.85 * wire
    return f, np.clip(col, 0, 1), rough, metal, height


def ce_stars(coll):
    """Each star a small four-pointed Neon spark, big at a constellation's main joints."""
    hi = Hm.Hi()
    for s0, v0, roll, stars, lines in CE_SKIES:
        fn = lay_on(s0, v0)
        cr, sr = math.cos(roll), math.sin(roll)
        degree = {}
        for a, b in lines:
            degree[a] = degree.get(a, 0) + 1
            degree[b] = degree.get(b, 0) + 1
        for k, (x, y) in enumerate(stars):
            size = 0.05 if degree.get(k, 0) >= 3 else 0.036
            X, Y = x * cr - y * sr, x * sr + y * cr
            p, n = fn(X, Y, 0.012)
            e1 = V((0, 1, 0)).cross(n).normalized()
            e2 = n.cross(e1).normalized()
            pts = []
            for q in range(8):
                r = size if q % 2 == 0 else size * 0.32
                a = TAU * q / 8
                pts.append(hi.v(p + (e1 * math.cos(a) + e2 * math.sin(a)) * r))
            top = hi.v(p + n * 0.02)
            for q in range(8):
                hi.f([pts[q], pts[(q + 1) % 8], top], [(0, 0), (1, 0), (0, 1)])
    return F.fix_normals(hi.object("CE_Stars", coll, [K.glow_material(CE_STAR)], smooth=False, weld=0))


def ce_crescent(coll):
    moon = Hm.mat_moonsilver("CE_Moon")
    hi = Hm.Hi()
    z0 = -0.78
    cy_out, r_out = 1.56, 1.56
    cy_in, r_in = 1.9, 1.3
    # sweep round from horn to horn: the band between the outer circle and the inner one
    steps = 96
    across = 8
    rows = []
    start, end = math.radians(138), math.radians(402)
    for i in range(steps + 1):
        a = start + (end - start) * i / steps
        ox, oy = math.cos(a) * r_out, cy_out + math.sin(a) * r_out
        # where the ray from the outer point toward the inner circle's centre meets it
        dx, dy = -ox, cy_in - oy
        L = math.hypot(dx, dy)
        dx, dy = dx / L, dy / L
        depth = max(0.0, L - r_in)
        # taper to clean horn tips
        t = i / steps
        fade = min(1.0, min(t, 1 - t) / 0.12)
        depth = depth * fade ** 0.7 + 0.004
        row = []
        for j in range(across + 1):
            k = j / across
            x, y = ox + dx * depth * k, oy + dy * depth * k
            lens = math.sin(math.pi * k) ** 0.55 * (0.13 + 0.42 * depth)
            row.append((hi.v((x, y, z0 + lens)), hi.v((x, y, z0 - lens))))
        rows.append(row)
    for i in range(steps):
        for j in range(across):
            for side in (0, 1):
                q = [rows[i][j][side], rows[i][j + 1][side], rows[i + 1][j + 1][side], rows[i + 1][j][side]]
                hi.f(q, [(0, 0), (1, 0), (1, 1), (0, 1)])
    o = hi.object("CE_Crescent", coll, [moon])
    F.fix_normals(o)
    o["w"] = 1.5
    # the pearl on its thread, from the horn on the viewer's right
    # the horn's tip: where the band has thinned, a little inward
    wire = Hm.Hi()
    top = V((math.cos(math.radians(30)) * r_out * 0.965, cy_out + math.sin(math.radians(30)) * r_out * 0.965, z0))
    drop = top + V((0.04, -0.52, 0.0))
    Hm.htube(wire, [top, top.lerp(drop, 0.5) + V((0.015, 0, 0)), drop], lambda t: 0.012, sides=6, per=6, wobble=0, tip=False)
    w = wire.object("CE_Thread", coll, [moon])
    w["w"] = 2.0
    p = Hm.Hi()
    sphere(p, drop + V((0, -0.11, 0)), 0.125, rings=12, sides=20)
    pearl = p.object("CE_Pearl", coll, [Hm.mat_pearl("CE_PearlMat")])
    pearl["w"] = 2.0
    return o, w, pearl


def celestial_clay():
    coll = W.collection("CelestialEggHi")
    shell = F.shell_mesh("CE_Shell", coll, 96, 64)
    s = ce_stars(coll)
    c, w, p = ce_crescent(coll)
    return {o.name: F.tris(o) for o in (shell, s, c, w, p)}


def celestial_build():
    coll = W.collection("CelestialEggHi")
    f, col, rough, metal, height = celestial_paint()
    mat = F.shell_material("CE_Lacquer", col, rough, metal)
    s = ce_stars(coll)
    c, w, p = ce_crescent(coll)
    return F.assemble("CelestialEgg", coll, mat, height, [c, w, p], {CE_STAR: [s]}, budget=5500, shell_frac=0.74, low_nu=72, low_nv=48)


# ---------- Astral Sanctum Egg ----------
AS_LIGHT = "643cff"
AS_WINDOWS = 6
AS_LOW, AS_HIGH = 0.24, 0.6      # the windows' sills and points, in v
AS_WIDTH = 0.034                 # half a window's width, in s at its widest
AS_DOME = 0.69                   # where the gold crown starts, in v
AS_RIBS = 12


def as_window_half(v):
    """A window's half width at height v: straight sides, then a pointed Gothic head."""
    spring = AS_LOW + (AS_HIGH - AS_LOW) * 0.64
    if v <= spring:
        return AS_WIDTH
    t = (v - spring) / (AS_HIGH - spring)
    return AS_WIDTH * max(0.0, 1 - t ** 1.6) ** 0.7


def astral_paint():
    f = F.Field()
    P, S, Vv = f.P, f.S, f.V
    # moonstone: milky white, with the blue sheen that gives it its name drifting across in soft clouds
    warp = np.stack([F.fbm(P, 1.3, 3, seed=s) for s in (521, 522, 523)], -1) * 0.3
    sheen = F.sstep(-0.05, 0.42, F.fbm(P + warp, 1.25, 4, 0.5, seed=524))
    hue = np.clip(F.fbm(P, 0.8, 2, seed=525) * 1.4 + 0.5, 0, 1)
    tint = F.mix(np.array((0.34, 0.56, 1.0)), np.array((0.62, 0.48, 1.0)), hue)
    col = F.mix(np.array((0.93, 0.93, 0.96)), tint, sheen * 0.82)
    wisp = 1 - F.sstep(0.0, 0.05, F.ridged(P + warp, 2.4, 3, seed=526))
    col = F.mix(col, np.array((1.0, 1.0, 1.0)), wisp * 0.25)
    height = np.zeros(S.shape)
    # the windows, cut deep; the reveal's stone is lit violet from inside
    win = np.zeros(S.shape)
    glowing = np.zeros(S.shape)
    vs = np.linspace(0, 1, 512)
    table = np.array([as_window_half(v) for v in vs])
    hw = np.interp(Vv, vs, table)
    for k in range(AS_WINDOWS):
        c = k / AS_WINDOWS
        ds = np.abs((S - c + 0.5) % 1.0 - 0.5)
        inside = (ds < hw) * (Vv > AS_LOW) * (Vv < AS_HIGH)
        depth = np.clip((hw - ds) / 0.01, 0, 1) * np.clip((Vv - AS_LOW) / 0.01, 0, 1) * inside
        win = np.maximum(win, depth)
        glowing = np.maximum(glowing, np.exp(-(np.maximum(ds - hw, 0) / 0.016) ** 2) * np.exp(-(np.maximum(AS_LOW - Vv, 0) / 0.03) ** 2) * np.exp(-(np.maximum(Vv - AS_HIGH, 0) / 0.025) ** 2))
    col = F.mix(col, np.array((0.14, 0.06, 0.34)), win)
    col = col + np.array((0.05, 0.015, 0.16)) * (glowing * (1 - win))[..., None]
    height = height - 0.09 * win
    # the crown is the dome: gold, ribbed, its lower edge scalloped into one scallop per rib
    xs = S * AS_RIBS
    fx = xs - np.floor(xs) - 0.5
    edge = AS_DOME + 0.017 * np.cos(fx * 2 * np.pi)
    dome = F.sstep(edge - 0.0025, edge + 0.0025, Vv)
    rib = np.abs(fx) * 2                                    # 0 mid-lobe, 1 on a rib line
    lobe = np.cos(fx * np.pi) ** 0.7
    fade = np.clip((0.985 - Vv) / 0.06, 0, 1)
    height = height * (1 - dome) + dome * (0.045 + 0.034 * lobe * fade)
    gold = F.mix(np.array((0.82, 0.56, 0.18)), np.array((1.0, 0.84, 0.42)), np.clip(0.55 + F.fbm(P, 20.0, 2, seed=527) * 0.7, 0, 1))
    groove = (1 - F.sstep(0.0, 0.1, 1 - rib)) * fade
    gold = gold * (1 - 0.55 * groove)[..., None]
    col = F.mix(col, gold, dome)
    # a row of small gold studs on the stone, just under the cornice
    star = np.zeros(S.shape)
    n = 24
    sx = (S * n) % 1.0 - 0.5
    sy = (Vv - 0.645) * 4.2 / (6.0 * 0.72 / n)
    r = np.hypot(sx, sy)
    star = (r < 0.15) * 1.0                # small round studs: a four-pointed star this small reads as a cross
    col = F.mix(col, gold, star * (1 - dome))
    height = height - 0.004 * star * (1 - dome)
    rough = np.clip(0.11 + 0.1 * win + 0.2 * dome, 0, 1)
    metal = np.maximum(0.82 * dome * (1 - 0.3 * groove), 0.82 * star * (1 - dome))
    return f, np.clip(col, 0, 1), rough, metal, height


def as_gold(coll, gold):
    hi = Hm.Hi()
    for k in range(AS_WINDOWS):
        c = k / AS_WINDOWS
        steps = 26
        left, right = [], []
        for i in range(steps + 1):
            v = AS_LOW + (AS_HIGH - AS_LOW) * i / steps
            w = as_window_half(v)
            left.append((c - w, v))
            right.append((c + w, v))
        path = left + right[::-1][1:] + [left[0]]
        pts = [(F.on(a % 1.0, b, 0.002), F.normal(a % 1.0, b)) for a, b in path]
        F.bar(hi, pts, 0.022, 0.018, foot=0.03)
        # one mullion and a simple pointed head inside it
        F.bar(hi, F.along_shell((c, AS_LOW), (c, AS_HIGH - 0.02), -0.05, steps=10), 0.012, 0.018, foot=0.03)
        for v in (AS_LOW + 0.12,):
            F.bar(hi, F.along_shell((c - AS_WIDTH, v), (c + AS_WIDTH, v), -0.05, steps=6), 0.01, 0.015, foot=0.03)
        # a slim sill
        F.bar(hi, F.along_shell((c - AS_WIDTH * 1.35, AS_LOW - 0.008), (c + AS_WIDTH * 1.35, AS_LOW - 0.008), 0.0, steps=8), 0.028, 0.026, foot=0.03)
        # a slim pilaster between this window and the next: flat against the wall
        cc = c + 0.5 / AS_WINDOWS
        F.bar(hi, F.along_shell((cc, 0.16), (cc, AS_DOME - 0.012), 0.0, steps=16), lambda t: 0.03 * (1 - 0.2 * t), 0.022, foot=0.02)
    # the thin bands that carry them: one at the foot, and the cornice under the dome
    F.bar(hi, F.along_shell((0, 0.155), (1, 0.155), 0.0, steps=64)[:-1], 0.04, 0.03, closed=True)
    F.bar(hi, F.along_shell((0, 0.125), (1, 0.125), 0.0, steps=64)[:-1], 0.022, 0.02, closed=True)
    F.bar(hi, F.along_shell((0, AS_DOME - 0.018), (1, AS_DOME - 0.018), 0.012, steps=72)[:-1], 0.034, 0.035, closed=True)
    o = hi.object("AS_Frames", coll, [gold], smooth=False)
    F.fix_normals(o)
    for p in o.data.polygons:
        p.use_smooth = False
    o["w"] = 1.0
    return o


def as_spire(coll, gold):
    """A slender spire on the very top: stem, orb, needle, and a flame-shaped tip."""
    hi = Hm.Hi()
    t = F.H
    lathe(hi, [(0.16, t - 0.08), (0.13, t - 0.01), (0.1, t + 0.02), (0.09, t + 0.05), (0.045, t + 0.09), (0.03, t + 0.2), (0.02, t + 0.34)], sides=16)
    lathe(hi, [(0.02, t + 0.42), (0.013, t + 0.68)], sides=10)
    o = hi.object("AS_Spire", coll, [gold])
    F.fix_normals(o)
    o["w"] = 1.5
    s = Hm.Hi()
    sphere(s, (0, t + 0.38, 0), 0.065, rings=10, sides=14)
    orb = s.object("AS_Orb", coll, [gold])
    orb["w"] = 2.0
    # the tip: a slim flame shape turned on the spire. A star up here read as a cross from the front
    c = Hm.Hi()
    cy = t + 0.66
    lathe(c, [(0.008, cy), (0.042, cy + 0.05), (0.052, cy + 0.1), (0.036, cy + 0.17), (0.016, cy + 0.24), (0.002, cy + 0.31)], sides=12)
    star = F.fix_normals(c.object("AS_Tip", coll, [gold]))
    star["w"] = 2.0
    return o, orb, star


def as_light(coll):
    """Violet panes behind the tracery."""
    hi = Hm.Hi()
    for k in range(AS_WINDOWS):
        c = k / AS_WINDOWS
        rows = 22
        grid = []
        for i in range(rows + 1):
            v = AS_LOW + (AS_HIGH - AS_LOW) * i / rows
            w = max(as_window_half(v), 0.001)
            grid.append([hi.v(F.on((c + w * (-1 + 2 * j / 3)) % 1.0, v, -0.07)) for j in range(4)])
        for i in range(rows):
            for j in range(3):
                hi.f([grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]], [(0, 0), (1, 0), (1, 1), (0, 1)])
    return F.fix_normals(hi.object("AS_Panes", coll, [K.glow_material(AS_LIGHT)], smooth=False, weld=0))


def astral_all(coll):
    gold = Hm.mat_gold("AS_Gold")
    fr = as_gold(coll, gold)
    o, orb, star = as_spire(coll, gold)
    return [fr, o, orb, star]


def astral_clay():
    coll = W.collection("AstralSanctumEggHi")
    f, col, rough, metal, height = astral_paint()
    shell = F.shell_mesh("AS_Shell", coll, 256, 160, height)
    pieces = astral_all(coll)
    g = as_light(coll)
    return {o.name: F.tris(o) for o in [shell, g] + pieces}


def astral_build():
    coll = W.collection("AstralSanctumEggHi")
    f, col, rough, metal, height = astral_paint()
    mat = F.shell_material("AS_Wall", col, rough, metal)
    pieces = astral_all(coll)
    g = as_light(coll)
    return F.assemble("AstralSanctumEgg", coll, mat, height, pieces, {AS_LIGHT: [g]}, budget=5000, shell_frac=0.72, low_nu=80, low_nv=50, hard=35, shell_ext=0.12, shell_ray=0.26)


# ---------- Heavenly Throne Egg ----------
HT_FLAME = "ffa31a"
HT_BELT = 0.44


def heavenly_paint():
    f = F.Field()
    P, S, Vv = f.P, f.S, f.V
    warp = np.stack([F.fbm(P, 1.3, 3, seed=s) for s in (541, 542, 543)], -1) * 0.25
    # pearl: warm white, with the fire of nacre in soft rose, ice and pale gold
    a = np.clip(F.fbm(P + warp, 1.5, 4, seed=544) * 1.3 + 0.5, 0, 1)
    tint = F.ramp(a, [(0.0, "f4c9d8"), (0.35, "f6efe6"), (0.6, "cfe2fa"), (0.85, "fbe3b4"), (1.0, "f4c9d8")])
    col = F.mix(np.array((0.97, 0.95, 0.92)), tint, 0.75)
    # fine growth lines of nacre, round the egg
    lines = 0.5 + 0.5 * np.sin((Vv + F.fbm(P, 2.0, 2, seed=545) * 0.04) * 150.0)
    col = col * (0.965 + 0.05 * lines)[..., None]
    height = 0.0006 * lines
    # above the belt, a sun in gold: long tapered rays rising from behind the coronet's band
    rays = np.zeros(S.shape)
    count = 32
    xs = S * count
    fx = np.abs(xs - np.floor(xs) - 0.5) * 2
    big = (np.floor(xs) % 2 == 0)
    length = np.where(big, 0.34, 0.2)
    t = np.clip((0.86 - Vv) / length, 0, 1)
    ray = (fx < (1 - t) * 0.62) * (Vv < 0.86) * (Vv > 0.86 - length)
    rays = np.maximum(rays, ray * 1.0)
    # below the belt, hanging swags and tassels drawn in gold line, one for each arc
    swag = np.zeros(S.shape)
    n = 8
    xs2 = (S * n) % 1.0
    arc_v = HT_BELT - 0.02 - 0.09 * np.sin(np.pi * xs2)
    d = np.abs(Vv - arc_v)
    swag = np.maximum(swag, (1 - F.sstep(0.0028, 0.0052, d)))
    arc_v2 = HT_BELT - 0.02 - 0.055 * np.sin(np.pi * xs2)
    swag = np.maximum(swag, (1 - F.sstep(0.0018, 0.0036, np.abs(Vv - arc_v2))))
    drop = (np.abs(xs2 - 0.5) < 0.014) * (Vv < HT_BELT - 0.1) * (Vv > HT_BELT - 0.2)
    swag = np.maximum(swag, drop * 1.0)
    gold_m = np.maximum(rays, swag)
    gold = F.mix(np.array((0.84, 0.58, 0.2)), np.array((1.0, 0.86, 0.46)), np.clip(0.5 + F.fbm(P, 22.0, 2, seed=546) * 0.8, 0, 1))
    col = F.mix(col, gold, gold_m)
    height = height + 0.006 * F.blur(gold_m, 1)
    rough = np.clip(0.16 + 0.16 * gold_m, 0, 1)
    metal = 0.85 * gold_m
    return f, np.clip(col, 0, 1), rough, metal, height


def ht_coronet(coll, gold):
    hi = Hm.Hi()
    bv = 0.86
    y0 = F.on(0.0, bv).y
    r0 = V((F.on(0.0, bv).x, 0, F.on(0.0, bv).z)).length + 0.012
    # the band: a rolled rim, a flat wall, a rolled rim
    lathe(hi, [(r0 - 0.03, y0 - 0.03), (r0 + 0.04, y0 - 0.025), (r0 + 0.045, y0 + 0.0), (r0 + 0.02, y0 + 0.01), (r0 + 0.02, y0 + 0.11), (r0 + 0.05, y0 + 0.12), (r0 + 0.05, y0 + 0.15), (r0 - 0.02, y0 + 0.16)], sides=64)
    # eight points round the band: tall cross-fleury and short pearls in turn
    points = 8
    for k in range(points):
        a = TAU * k / points
        out = V((math.sin(a), 0, math.cos(a)))
        base = out * (r0 + 0.015) + V((0, y0 + 0.14, 0))
        tall = k % 2 == 0
        h = 0.26 if tall else 0.17
        side = V((0, 1, 0)).cross(out).normalized()
        w = 0.08 if tall else 0.06
        # a pointed leaf of metal: thick at the base
        rows = []
        for i in range(10):
            t = i / 9
            # never quite closing to a point: collapsed tips made faces the bake read from behind
            hw = max(0.008, w * (max(0.0, math.sin(math.pi * min(0.97, t * 0.95 + 0.06))) ** 0.8))
            th = 0.028 * (1 - 0.72 * t)
            p = base + V((0, h * t, 0)) + out * 0.05 * math.sin(math.pi * t)
            rows.append([hi.v(p - side * hw), hi.v(p + out * th), hi.v(p + side * hw), hi.v(p - out * th)])
        for i in range(9):
            for q in range(4):
                n = (q + 1) % 4
                hi.f([rows[i][q], rows[i][n], rows[i + 1][n], rows[i + 1][q]], [(0, 0), (1, 0), (1, 1), (0, 1)])
        hi.f(rows[0][::-1], [(0, 0), (1, 0), (1, 1), (0, 1)])
        hi.f(rows[-1], [(0, 0), (1, 0), (1, 1), (0, 1)])
    # four arches rising from the tall points to meet at the orb
    top_y = y0 + 0.72
    for k in range(4):
        a = TAU * k / 4
        out = V((math.sin(a), 0, math.cos(a)))
        pts = [out * (r0 + 0.02) + V((0, y0 + 0.26, 0)), out * (r0 + 0.02) * 0.9 + V((0, y0 + 0.42, 0)), out * r0 * 0.58 + V((0, y0 + 0.6, 0)), out * r0 * 0.2 + V((0, y0 + 0.69, 0)), V((0, top_y, 0))]
        Hm.htube(hi, pts, lambda t: 0.028 * (1 - 0.2 * t), sides=8, per=6, wobble=0, tip=False)
    lathe(hi, [(0.05, top_y - 0.06), (0.11, top_y - 0.01), (0.06, top_y + 0.03), (0.04, top_y + 0.05)], sides=20)
    o = hi.object("HT_Coronet", coll, [gold])
    F.fix_normals(o)
    o["w"] = 1.1
    s = Hm.Hi()
    sphere(s, (0, top_y + 0.1, 0), 0.075, rings=12, sides=18)
    orb = s.object("HT_Orb", coll, [gold])
    orb["w"] = 2.0
    return o, orb, top_y


def ht_beads(coll, gold):
    """The belt: two gold rails with a row of small pearls between them, and a pearl on each of the
    coronet's short points."""
    h = Hm.Hi()
    F.bar(h, F.along_shell((0, HT_BELT + 0.024), (1, HT_BELT + 0.024), 0.008, steps=72)[:-1], 0.024, 0.026, closed=True)
    F.bar(h, F.along_shell((0, HT_BELT - 0.024), (1, HT_BELT - 0.024), 0.008, steps=72)[:-1], 0.024, 0.026, closed=True)
    rails = h.object("HT_Rails", coll, [gold], smooth=False)
    F.fix_normals(rails)
    rails["w"] = 1.0
    p = Hm.Hi()
    count = 28
    for k in range(count):
        sphere(p, F.on(k / count, HT_BELT, 0.024), 0.055, rings=5, sides=8)
    bv = 0.86
    y0 = F.on(0.0, bv).y
    r0 = V((F.on(0.0, bv).x, 0, F.on(0.0, bv).z)).length + 0.012
    for k in range(1, 8, 2):
        a = TAU * k / 8
        sphere(p, V((math.sin(a) * (r0 + 0.02), y0 + 0.335, math.cos(a) * (r0 + 0.02))), 0.05, rings=5, sides=8)
    beads = p.object("HT_Pearls", coll, [Hm.mat_pearl("HT_PearlMat")])
    beads["w"] = 4.0
    return rails, beads


def ht_cushion(coll, gold):
    """Three tiers of carved cloud, each with a scalloped edge, soft like plaster and not a heap of
    balls, each lip traced in gold."""
    hi, trim = Hm.Hi(), Hm.Hi()
    tiers = ((1.5, 0.0, 0.22, 11, 0.0), (1.2, 0.2, 0.38, 9, 0.2), (0.92, 0.36, 0.52, 7, 0.45))
    for R, y0, y1, ribs, phase in tiers:
        h = y1 - y0
        profile = [(R * 0.62, y0), (R * 0.9, y0 + 0.005), (R * 0.98, y0 + h * 0.18), (R, y0 + h * 0.42), (R * 0.97, y0 + h * 0.7), (R * 0.88, y0 + h * 0.92), (R * 0.72, y1), (R * 0.5, y1 + 0.004)]
        sides = ribs * 12
        rows = []
        for r, y in profile:
            row = []
            for k in range(sides):
                a = TAU * k / sides + phase
                # the scallop: full at the edge, gone by the tier's flat top
                amount = max(0.0, min(1.0, (r / R - 0.5) / 0.4))
                rr = r * (1 + 0.1 * amount * (abs(math.cos((a - phase) * ribs / 2)) ** 0.55 - 0.72))
                row.append(hi.v((math.sin(a) * rr, y, math.cos(a) * rr)))
            rows.append(row)
        for j in range(len(rows) - 1):
            for k in range(sides):
                n = (k + 1) % sides
                hi.f([rows[j][k], rows[j][n], rows[j + 1][n], rows[j + 1][k]], [(0, 0), (1, 0), (1, 1), (0, 1)])
        # the gold line along this tier's widest edge
        y_line = y0 + h * 0.42
        pts = []
        for k in range(sides + 1):
            a = TAU * k / sides + phase
            rr = R * (1 + 0.1 * (abs(math.cos((a - phase) * ribs / 2)) ** 0.55 - 0.72)) * 1.012
            pts.append((math.sin(a) * rr, y_line, math.cos(a) * rr))
        Hm.htube(trim, pts, lambda t: 0.017, sides=6, per=1, wobble=0, tip=False)
    bed = hi.object("HT_Cloud", coll, [Hm.mat_cloud("HT_CloudMat")])
    F.fix_normals(bed)
    bed["w"] = 1.0
    line = trim.object("HT_Trim", coll, [gold])
    line["w"] = 2.6
    return bed, line


def ht_mandorla(coll, gold):
    hi = Hm.Hi()
    z0 = -0.98
    cx, cy = 0.0, 1.92
    W_, H_ = 1.26, 1.72
    n = V((0, 0, 1))

    def rim(t, scale=1.0):
        a = TAU * t
        x, y = math.sin(a), math.cos(a)
        xx = x * (abs(x) ** 0.18)
        return V((cx + xx * W_ * scale, cy + y * H_ * scale, z0))
    F.bar(hi, [(rim(k / 72), n) for k in range(72)], 0.05, 0.05, closed=True, foot=0.05)
    # the sunburst: broad wavy rays rising from its upper part only, long and short in turn
    rays = 21
    for k in range(rays):
        t = -0.3 + 0.6 * k / (rays - 1)
        p = rim(t)
        out = (p - V((cx, cy, z0))).normalized()
        side = V((-out.y, out.x, 0))
        long_ = k % 2 == 0
        L = (0.62 if long_ else 0.42) * (1 - 0.25 * abs(t) / 0.3)
        wavy = long_
        rows_ = []
        for i in range(13):
            q = i / 12
            hw = (0.085 if long_ else 0.072) * (1 - q ** 1.4) + 0.004
            sway = 0.055 * math.sin(q * TAU * 1.25) * (1 - 0.3 * q) if wavy else 0.0
            c = p - out * 0.02 + out * L * q + side * sway
            d = 0.024 * (1 - q) + 0.004
            rows_.append([hi.v(c - side * hw), hi.v(c + V((0, 0, d))), hi.v(c + side * hw), hi.v(c - V((0, 0, d)))])
        for i in range(12):
            for r in range(4):
                nx = (r + 1) % 4
                hi.f([rows_[i][r], rows_[i][nx], rows_[i + 1][nx], rows_[i + 1][r]], [(0, 0), (1, 0), (1, 1), (0, 1)])
        hi.f(rows_[0][::-1], [(0, 0), (1, 0), (1, 1), (0, 1)])
        hi.f(rows_[-1], [(0, 0), (1, 0), (1, 1), (0, 1)])
    o = hi.object("HT_Mandorla", coll, [gold], smooth=False)
    F.fix_normals(o)
    for p in o.data.polygons:
        p.use_smooth = False
    o["w"] = 2.2
    glow = Hm.Hi()
    pts = [(rim(k / 72, 0.97) + V((0, 0, 0.03)), n) for k in range(72)]
    F.prism(glow, pts, 0.018, height=lambda w: w * 0.3, closed=True)
    g = glow.object("HT_Halo", coll, [K.glow_material(HT_FLAME)], smooth=False, weld=0)
    return o, g


def heavenly_all(coll):
    gold = Hm.mat_gold("HT_Gold")
    co, orb, top = ht_coronet(coll, gold)
    rails, beads = ht_beads(coll, gold)
    bed, line = ht_cushion(coll, gold)
    m, halo = ht_mandorla(coll, gold)
    return [co, orb, rails, beads, bed, line, m], halo


def heavenly_clay():
    coll = W.collection("HeavenlyThroneEggHi")
    shell = F.shell_mesh("HT_Shell", coll, 96, 64)
    pieces, g = heavenly_all(coll)
    return {o.name: F.tris(o) for o in [shell, g] + pieces}


def heavenly_build():
    coll = W.collection("HeavenlyThroneEggHi")
    f, col, rough, metal, height = heavenly_paint()
    mat = F.shell_material("HT_Pearl", col, rough, metal)
    pieces, g = heavenly_all(coll)
    return F.assemble("HeavenlyThroneEgg", coll, mat, height, pieces, {HT_FLAME: [g]}, budget=9500, shell_frac=0.56, low_nu=56, low_nv=36, hard=35, ao_floor=0.66, att_ext=0.09, att_ray=0.28)
