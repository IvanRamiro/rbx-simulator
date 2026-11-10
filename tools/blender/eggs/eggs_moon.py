"""Moonlit Isle's eggs, second generation (see egg_forge.py).

Celestial Egg, "the star chart": black-blue lacquer, real constellations inlaid in gold wire with
small stars at their joints, a drift of mother-of-pearl where the Milky Way runs across it. Behind it
stands a great silver crescent, thick at its foot and tapering to two horns above the shoulders, the
egg resting in its curve; from one horn a pearl hangs on a thread of silver.

Astral Sanctum Egg, "the astrolabe": just an egg, and the instrument is written on it. Moonstone with its blue
sheen, a brass dial engraved on its face and back, raised gold bands of a sky map running round the shell, marked
in degrees, a line of violet light along the ecliptic, and five small planets inlaid along it, one ringed.

Heavenly Throne Egg, "the seat of heaven": just an egg, and the sky is on it. Pearl rising through pale blue, three
banks of cloud sculpted round its lower half, each rimmed in gold, and long gold rays falling from a sun on the
crown, its edge lit.
"""
import math

import numpy as np

import egg_forge as F
import egg_hi as Hm
import egg_kit as K
import eggs_origin as O

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
AS_DIAL = "8a5cff"
AS_C = V((0, F.H / 2, 0))


def as_dial(f, s0, v0):
    """Engraved lines on a plane at (s0, v0): circles, degree ticks, an off-centre star ring and pointers
    that sweep toward it. An instrument's face."""
    x, y, front = f.plane(s0, v0)
    r = np.hypot(x, y)
    ang = np.arctan2(y, x)
    m = np.zeros(x.shape)
    for R, w in ((0.14, 0.008), (0.27, 0.006), (0.56, 0.009), (0.72, 0.012)):
        m = np.maximum(m, 1 - F.sstep(w * 0.7, w, np.abs(r - R)))
    # degree ticks between the outer circles, every third one long
    t = (ang / TAU * 72) % 1.0
    tick = (np.abs(t - 0.5) < 0.08) * (r > 0.585) * (r < 0.72)
    t3 = (ang / TAU * 24) % 1.0
    tick3 = (np.abs(t3 - 0.5) < 0.05) * (r > 0.56) * (r < 0.72)
    m = np.maximum.reduce([m, tick * 1.0, tick3 * 1.0])
    # the off-centre ring and its curved pointers
    r2 = np.hypot(x, y - 0.14)
    m = np.maximum(m, 1 - F.sstep(0.005, 0.008, np.abs(r2 - 0.33)))
    for k in range(7):
        a = TAU * k / 7 + 0.3
        pts = []
        for i in range(13):
            q = i / 12
            ra = a + 0.75 * q
            rr = 0.14 + (0.5 - 0.14) * q
            pts.append((math.cos(ra) * rr, math.sin(ra) * rr))
        d, along = F.seg_dist(x, y, pts)
        m = np.maximum(m, 1 - F.sstep(0.0, 0.009 * (1.2 - along) + 0.002, d))
    return m * (front > 0.25)


AS_TILT = V((math.sin(math.radians(32)), math.cos(math.radians(32)), 0.18)).normalized()
AS_DIALS = ((0.5, 0.52), (0.0, 0.52))
# the planets, by their angle round the ecliptic: (angle degrees, radius, base colour, highlight)
AS_PLANETS = ((14, 0.085, "e8dfd0", "fff8ea"), (72, 0.07, "a81c14", "ff6a4a"), (148, 0.115, "c8922e", "ffe08a"), (205, 0.1, "1c46b4", "78b4ff"), (292, 0.065, "8a93a8", "e4e9f4"))


def as_ring_point(axis, deg):
    """A point on the egg at this angle round a great circle with this axis, seen from the middle."""
    ref = V((0, 0, 1)) if abs(V(axis).z) < 0.9 else V((1, 0, 0))
    e1 = V(axis).cross(ref).normalized()
    e2 = V(axis).cross(e1)
    a = math.radians(deg)
    d = e1 * math.cos(a) + e2 * math.sin(a)
    r = 1.2
    for _ in range(8):
        q = AS_C + d * r
        ss = (math.atan2(q.x, q.z) / TAU + 0.5) % 1.0
        vv = math.acos(max(-1, min(1, 1 - 2 * max(0.001, min(F.H - 0.001, q.y)) / F.H))) / math.pi
        p = F.on(ss, vv)
        r = (p - AS_C).length
    return p, F.normal(ss, vv)


def astral_paint():
    f = F.Field()
    P, S = f.P, f.S
    warp = np.stack([F.fbm(P, 1.3, 3, seed=s) for s in (521, 522, 523)], -1) * 0.3
    sheen = F.sstep(-0.1, 0.45, F.fbm(P + warp, 1.25, 4, 0.5, seed=524))
    hue = np.clip(F.fbm(P, 0.8, 2, seed=525) * 1.4 + 0.5, 0, 1)
    tint = F.mix(np.array((0.3, 0.46, 0.95)), np.array((0.56, 0.38, 0.95)), hue)
    col = F.mix(np.array((0.88, 0.89, 0.95)), tint, sheen * 0.78)
    fine = F.fbm(P, 30.0, 2, seed=526)
    # the dials sit on top of everything else: a clear disc of stone round each
    clear = np.ones(S.shape)
    for s0, v0 in AS_DIALS:
        x, y, front = f.plane(s0, v0)
        clear = np.minimum(clear, np.where(front > 0.2, F.sstep(0.74, 0.77, np.hypot(x, y)), 1.0))
    rel = P - np.array(AS_C)
    # raised bands round the shell: the horizon, two meridians, and the ecliptic with the light in it
    bands = np.zeros(S.shape)
    ticks = np.zeros(S.shape)
    axes = ((V((0, 1, 0)), 0.03), (V((math.sin(math.radians(58)), 0, math.cos(math.radians(58)))), 0.024), (V((math.sin(math.radians(-58)), 0, math.cos(math.radians(-58)))), 0.024), (AS_TILT, 0.036))
    for axis, w in axes:
        a = np.array(axis)
        d = np.abs((rel * a).sum(-1))
        band = 1 - F.sstep(w, w + 0.006, d)
        bands = np.maximum(bands, band)
        # degree marks across each band: from an angle round that axis
        ref = np.array((0.0, 0.0, 1.0)) if abs(axis.z) < 0.9 else np.array((1.0, 0.0, 0.0))
        e1 = np.cross(a, ref)
        e1 = e1 / np.linalg.norm(e1)
        e2 = np.cross(a, e1)
        ang = np.arctan2((rel * e2).sum(-1), (rel * e1).sum(-1))
        tk = np.abs(((ang / TAU * 36) % 1.0) - 0.5) < 0.05
        ticks = np.maximum(ticks, tk * band)
    bands = bands * clear
    ticks = ticks * clear
    gold = F.mix(np.array((0.82, 0.56, 0.18)), np.array((1.0, 0.84, 0.42)), np.clip(0.55 + fine * 0.7, 0, 1))
    col = F.mix(col, gold, bands)
    col = F.mix(col, gold * 0.42, ticks)
    height = 0.016 * F.blur(bands, 1.5) - 0.004 * ticks
    # the planets: small domed stones inlaid along the ecliptic
    stones = np.zeros(S.shape)
    for deg, R, base, light in AS_PLANETS:
        p, n = as_ring_point(AS_TILT, deg)
        d = np.sqrt(((P - np.array(p)) ** 2).sum(-1))
        m = d < R
        t = np.clip(d / R, 0, 1)
        dome = np.sqrt(np.clip(1 - t * t, 0, 1))
        stone = F.mix(F.rgb(base) * 0.5, F.rgb(light), dome ** 1.5)
        col = np.where(m[..., None], stone, col)
        rim = np.exp(-((d - R * 1.1) / 0.008) ** 2)
        col = F.mix(col, gold, rim)
        height = np.where(m, 0.016 + 0.05 * dome, height) + 0.008 * rim
        stones = np.maximum(stones, m * 1.0)
        bands = np.where(m, 0.0, np.maximum(bands, rim))
        if deg == 148:
            # the ringed one: a thin gold ellipse round it
            e1, e2 = O.frame(n)
            q = P - np.array(p)
            xx = (q * np.array(e1)).sum(-1)
            yy = (q * np.array(e2)).sum(-1)
            ca, sa = math.cos(0.45), math.sin(0.45)
            xr, yr = xx * ca + yy * sa, -xx * sa + yy * ca
            ell = np.abs(np.hypot(xr / (R * 1.75), yr / (R * 0.62)) - 1.0)
            ring = (1 - F.sstep(0.05, 0.1, ell)) * (d >= R * 0.95) * (d < R * 2.2)
            col = F.mix(col, gold, ring)
            height = height + 0.012 * ring
            bands = np.maximum(bands, ring)
    dial = np.maximum(as_dial(f, 0.5, 0.52), as_dial(f, 0.0, 0.52))
    col = F.mix(col, gold, dial)
    height = height + 0.006 * F.blur(dial, 1) + 0.0004 * fine
    rough = np.clip(0.1 + 0.2 * np.maximum(dial, bands) + 0.02 * stones, 0, 1)
    metal = 0.85 * np.maximum(dial, bands)
    return f, np.clip(col, 0, 1), rough, metal, height


def as_glow(coll):
    """Violet light inlaid along the middle of the ecliptic band, broken where a dial or planet sits, and
    the small stone at each dial's centre."""
    hi = Hm.Hi()
    run = []

    def flush():
        if len(run) > 2:
            F.prism(hi, list(run), lambda t: 0.024 * min(1.0, min(t, 1 - t) / 0.06 + 0.2), height=lambda w: w * 0.4)
        run.clear()
    hold = [F.on(a, b) for a, b in AS_DIALS]
    planets = [as_ring_point(AS_TILT, d[0])[0] for d in AS_PLANETS]
    radii = [d[1] for d in AS_PLANETS]
    for k in range(361):
        p, n = as_ring_point(AS_TILT, k)
        blocked = any((p - h).length < 0.8 for h in hold) or any((p - q).length < r * 1.3 for q, r in zip(planets, radii))
        if blocked:
            flush()
        else:
            run.append((p + n * 0.012, n))
    flush()
    light = hi.object("AS_Light", coll, [K.glow_material(AS_LIGHT)], smooth=False, weld=0)
    gem = Hm.Hi()
    for s0, v0 in AS_DIALS:
        F.cut_gem(gem, F.on(s0, v0, 0.0), F.normal(s0, v0), (0, 1, 0), 0.07, 0.03, sides=6, base=0.02)
    g = F.fix_normals(gem.object("AS_DialGems", coll, [K.glow_material(AS_DIAL)], smooth=False, weld=0))
    return light, g


def astral_clay():
    coll = W.collection("AstralSanctumEggHi")
    f, col, rough, metal, height = astral_paint()
    shell = F.shell_mesh("AS_Shell", coll, 192, 120, height)
    a, b = as_glow(coll)
    return {o.name: F.tris(o) for o in (shell, a, b)}


def astral_build():
    coll = W.collection("AstralSanctumEggHi")
    f, col, rough, metal, height = astral_paint()
    mat = F.shell_material("AS_Moonstone", col, rough, metal)
    a, b = as_glow(coll)
    return F.assemble("AstralSanctumEgg", coll, mat, height, [], {AS_LIGHT: [a], AS_DIAL: [b]}, shell_frac=0.998, low_nu=96, low_nv=62, ao_floor=0.85)


# ---------- Heavenly Throne Egg ----------
HT_HALO = "ffa31a"
HT_BANKS = ((0.34, 7, 0.05, 0.4), (0.24, 9, 0.042, 1.9), (0.145, 11, 0.034, 3.1))     # cloud banks: v, lobes, lift, phase


def heavenly_paint():
    f = F.Field()
    P, S, Vv = f.P, f.S, f.V
    warp = np.stack([F.fbm(P, 1.3, 3, seed=s) for s in (541, 542, 543)], -1) * 0.25
    # the sky: warm pearl at the crown, opening to clear pale blue low down, with nacre's soft fire through it
    a = np.clip(F.fbm(P + warp, 1.5, 4, seed=544) * 1.3 + 0.5, 0, 1)
    fire = F.ramp(a, [(0.0, "f7d3df"), (0.35, "f8f2e8"), (0.6, "d8e8fb"), (0.85, "fbe8bf"), (1.0, "f7d3df")])
    sky = F.ramp(np.clip((Vv - 0.28) / 0.6, 0, 1), [(0.0, "4f8fdc"), (0.3, "79aeea"), (0.6, "b8d6f4"), (0.85, "f1ebe6"), (1.0, "fff0d0")])
    col = F.mix(sky, fire, 0.26)
    height = np.zeros(S.shape)
    # the sun's rays: long tapered lines of gold falling from the crown, long and short in turn
    n = 28
    xs = S * n
    fx = np.abs(xs - np.floor(xs) - 0.5) * 2
    long_ = np.floor(xs) % 2 == 0
    reach = np.where(long_, 0.45, 0.26)
    t = np.clip((0.86 - Vv) / reach, 0, 1)
    rays = (fx < (1 - t) * 0.46) * (Vv < 0.87) * (Vv > 0.86 - reach)
    # the sun: a disc of gold over the crown, its edge scalloped
    edge = 0.86 + 0.012 * np.cos(S * n * TAU)
    sun = F.sstep(edge - 0.003, edge + 0.003, Vv)
    gold_m = np.maximum(rays * 1.0, sun)
    # the clouds: three banks, each overlapping the one above it, sculpted proud with a gold lip
    rim = np.zeros(S.shape)
    for bank, (v0, lobes, lift, ph) in enumerate(HT_BANKS):
        wav = np.abs(np.sin(S * lobes * np.pi + ph)) ** 0.55
        wav2 = np.abs(np.sin(S * lobes * 3.0 * np.pi + ph * 1.7)) ** 0.6
        top = v0 + 0.05 * wav + 0.022 * wav2
        inside = F.sstep(top + 0.002, top - 0.002, Vv)
        depth = np.clip((top - Vv) / 0.07, 0, 1)
        billow = np.sin(np.clip(depth, 0, 1) * np.pi * 0.5)
        tone = F.ramp(depth, [(0.0, "ffffff"), (0.55, "f4f7fc"), (1.0, "b7cdea")])
        col = F.mix(col, tone, inside)
        gold_m = gold_m * (1 - inside)
        height = height * (1 - inside) + inside * (lift * (0.55 + 0.45 * billow) + 0.008 * wav)
        rim = rim * (1 - inside)
        rim = np.maximum(rim, (1 - F.sstep(0.0018, 0.0042, np.abs(Vv - top))))
        # a gold scroll curling in each lobe, thinning as it winds to the middle
        girth = 6.2 * np.sin(np.pi * v0)
        for k in range(lobes):
            sc = ((np.pi / 2 + k * np.pi - ph) / (lobes * np.pi)) % 1.0
            vc = v0 + 0.012
            size = 0.13 - 0.018 * bank
            box = (np.abs((S - sc + 0.5) % 1.0 - 0.5) * girth < size * 1.5) & (np.abs(Vv - vc) * 4.2 < size * 1.5)
            if not box.any():
                continue
            px = ((S[box] - sc + 0.5) % 1.0 - 0.5) * girth
            py = (Vv[box] - vc) * 4.2
            flip = 1 if k % 2 else -1
            pts = []
            for i in range(30):
                t_ = i / 29
                a_ = flip * TAU * 1.7 * t_
                r_ = size * (1 - 0.84 * t_)
                pts.append((math.cos(a_) * r_, math.sin(a_) * r_))
            d_, along = F.seg_dist(px, py, pts)
            line = 1 - F.sstep(0.0, 0.009 * (1.25 - along) + 0.002, d_)
            rim[box] = np.maximum(rim[box], line)
    gold = F.mix(np.array((0.84, 0.58, 0.2)), np.array((1.0, 0.86, 0.46)), np.clip(0.5 + F.fbm(P, 22.0, 2, seed=546) * 0.8, 0, 1))
    gold_m = np.maximum(gold_m, rim)
    col = F.mix(col, gold, gold_m)
    height = height + 0.005 * F.blur(gold_m, 1) + 0.01 * sun
    rough = np.clip(0.16 + 0.16 * gold_m, 0, 1)
    metal = 0.85 * gold_m
    return f, np.clip(col, 0, 1), rough, metal, height


def ht_sun_line(coll):
    """The sun's scalloped edge, lit: a thin line of Neon inlaid along it."""
    hi = Hm.Hi()
    n = 28
    pts = []
    for k in range(n * 8):
        ss = k / (n * 8)
        vv = 0.86 + 0.012 * math.cos(ss * n * TAU)
        pts.append((F.on(ss, vv, 0.012), F.normal(ss, vv)))
    F.prism(hi, pts, 0.016, height=lambda w: w * 0.4, closed=True)
    return hi.object("HT_SunLine", coll, [K.glow_material(HT_HALO)], smooth=False, weld=0)


def heavenly_clay():
    coll = W.collection("HeavenlyThroneEggHi")
    f, col, rough, metal, height = heavenly_paint()
    shell = F.shell_mesh("HT_Shell", coll, 192, 120, height)
    g = ht_sun_line(coll)
    return {x.name: F.tris(x) for x in (shell, g)}


def heavenly_build():
    coll = W.collection("HeavenlyThroneEggHi")
    f, col, rough, metal, height = heavenly_paint()
    mat = F.shell_material("HT_Sky", col, rough, metal)
    g = ht_sun_line(coll)
    return F.assemble("HeavenlyThroneEgg", coll, mat, height, [], {HT_HALO: [g]}, shell_frac=0.998, low_nu=96, low_nv=62, ao_floor=0.85)
