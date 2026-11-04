"""Moonlit Isle's eggs, second generation (see egg_forge.py).

Celestial Egg, "the star chart": black-blue lacquer, real constellations inlaid in gold wire with
small stars at their joints, a drift of mother-of-pearl where the Milky Way runs across it. Behind it
stands a great silver crescent, thick at its foot and tapering to two horns above the shoulders, the
egg resting in its curve; from one horn a pearl hangs on a thread of silver.

Astral Sanctum Egg, "the shrine": the egg as a building. A stepped plinth; six tall pointed windows
set deep in moonstone walls, each with gold frame and tracery and violet light behind it; slim columns
with capitals between them; a cornice; a ribbed gold dome on a drum, and a spire with an orb and a
crescent at its point.

Heavenly Throne Egg, "the enthroned": pearl with a soft fire in it, belted with a rail of gold and a
row of small pearls. A coronet with eight points and four arches rising to an orb. It sits on a wide
cushion of cloud, and behind it a pointed mandorla of gold, its rim a ring of flames, the sun's disc
at its head.
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
AS_LOW, AS_HIGH = 0.26, 0.6      # the windows' sills and points, in v
AS_WIDTH = 0.042                 # half a window's width, in s at its widest


def as_window_half(v):
    """A window's half width at height v: straight sides, then a pointed Gothic head."""
    spring = AS_LOW + (AS_HIGH - AS_LOW) * 0.62
    if v <= spring:
        return AS_WIDTH
    t = (v - spring) / (AS_HIGH - spring)
    return AS_WIDTH * max(0.0, 1 - t ** 1.6) ** 0.7


def astral_paint():
    f = F.Field()
    P, S, Vv = f.P, f.S, f.V
    # moonstone: milky white with a blue and lilac sheen drifting in it
    warp = np.stack([F.fbm(P, 1.5, 3, seed=s) for s in (521, 522, 523)], -1) * 0.25
    sheen = np.clip(F.fbm(P + warp, 1.8, 5, 0.55, seed=524) * 1.3 + 0.5, 0, 1)
    hue = np.clip(F.fbm(P, 1.1, 2, seed=525) * 1.4 + 0.5, 0, 1)
    tint = F.mix(np.array((0.56, 0.68, 0.98)), np.array((0.74, 0.6, 0.96)), hue)
    col = F.mix(np.array((0.86, 0.88, 0.94)), tint, sheen * 0.8)
    # ashlar courses: stone blocks, thin joints, each block very slightly its own tone
    rows = 15
    yy = Vv * rows
    row = np.floor(yy)
    xs = S * (32 - 0) + 0.5 * (row % 2)
    cell = np.floor(xs)
    joint = np.minimum(np.abs(yy - row - 0.5) * -1 + 0.5, np.abs(xs - cell - 0.5) * -1 + 0.5)
    joint_m = 1 - F.sstep(0.0, 0.05, joint)
    per = (np.sin((cell + row * 13.0) * 37.7) * 43758.5) % 1.0
    col = col * (0.93 + 0.1 * per)[..., None]
    col = F.mix(col, col * 0.6, joint_m * 0.65)
    height = -0.004 * joint_m + 0.002 * (per - 0.5)
    # the windows: cut deep into the wall, reveals darkened, sills lit violet from inside
    win = np.zeros(S.shape)
    glowing = np.zeros(S.shape)
    half = np.vectorize(as_window_half)
    vs = np.linspace(0, 1, 512)
    table = np.array([as_window_half(v) for v in vs])
    for k in range(AS_WINDOWS):
        c = k / AS_WINDOWS
        ds = np.abs((S - c + 0.5) % 1.0 - 0.5)
        hw = np.interp(Vv, vs, table)
        inside = (ds < hw) * (Vv > AS_LOW) * (Vv < AS_HIGH)
        # a soft measure of how far in: for the reveal
        depth = np.clip((hw - ds) / 0.012, 0, 1) * np.clip((Vv - AS_LOW) / 0.012, 0, 1) * inside
        win = np.maximum(win, depth)
        glowing = np.maximum(glowing, np.exp(-(np.maximum(ds - hw, 0) / 0.02) ** 2) * np.exp(-(np.maximum(AS_LOW - Vv, 0) / 0.04) ** 2) * np.exp(-(np.maximum(Vv - AS_HIGH, 0) / 0.03) ** 2))
    col = F.mix(col, np.array((0.1, 0.05, 0.28)), win)
    col = col + np.array((0.08, 0.03, 0.2)) * (glowing * (1 - win))[..., None]
    height = height * (1 - win) - 0.11 * win
    rough = np.clip(0.2 + 0.2 * joint_m + 0.1 * win, 0, 1)
    return f, np.clip(col, 0, 1), rough, np.zeros(S.shape), height


def as_gold(coll, gold):
    hi = Hm.Hi()
    # frames and tracery for each window
    for k in range(AS_WINDOWS):
        c = k / AS_WINDOWS
        steps = 28
        left, right = [], []
        for i in range(steps + 1):
            v = AS_LOW + (AS_HIGH - AS_LOW) * i / steps
            w = as_window_half(v)
            left.append((c - w, v))
            right.append((c + w, v))
        path = left + right[::-1][1:] + [left[0]]
        pts = [(F.on(a % 1.0, b, 0.012), F.normal(a % 1.0, b)) for a, b in path]
        F.bar(hi, pts, 0.032, 0.03, foot=0.04)
        # a mullion up the middle, two crossbars, and a pointed trefoil in the head
        F.bar(hi, F.along_shell((c, AS_LOW), (c, AS_HIGH - 0.015), -0.05, steps=10), 0.016, 0.02, foot=0.03)
        for v in (AS_LOW + 0.09, AS_LOW + 0.18):
            F.bar(hi, F.along_shell((c - AS_WIDTH, v), (c + AS_WIDTH, v), -0.05, steps=6), 0.012, 0.016, foot=0.03)
        spring = AS_LOW + (AS_HIGH - AS_LOW) * 0.62
        F.bar(hi, F.along_shell((c - AS_WIDTH, spring), (c, AS_HIGH - 0.03), -0.05, steps=6), 0.011, 0.015, foot=0.03)
        F.bar(hi, F.along_shell((c + AS_WIDTH, spring), (c, AS_HIGH - 0.03), -0.05, steps=6), 0.011, 0.015, foot=0.03)
        # the sill stands proud
        F.bar(hi, F.along_shell((c - AS_WIDTH * 1.5, AS_LOW - 0.012), (c + AS_WIDTH * 1.5, AS_LOW - 0.012), 0.02, steps=8), 0.05, 0.04, foot=0.03)
        # the column between this window and the next: a shaft, a capital and a base
        cc = c + 0.5 / AS_WINDOWS
        col_low, col_high = 0.17, 0.66
        p0, p1 = F.on(cc % 1.0, col_low, 0.035), F.on(cc % 1.0, col_high, 0.035)
        Hm.htube(hi, [F.on(cc % 1.0, col_low + (col_high - col_low) * t / 8, 0.035) for t in range(9)], lambda t: 0.032 * (1 - 0.12 * t), sides=10, per=3, wobble=0, tip=False)
        for v, wid in ((col_low + 0.005, 0.1), (col_high, 0.12)):
            F.bar(hi, F.along_shell((cc - 0.018, v), (cc + 0.018, v), 0.018, steps=4), 0.05, 0.06, foot=0.02)
    # the cornice over the arches and the string course under them
    F.bar(hi, F.along_shell((0, 0.675), (1, 0.675), 0.012, steps=72)[:-1], 0.05, 0.05, closed=True)
    F.bar(hi, F.along_shell((0, 0.655), (1, 0.655), 0.012, steps=72)[:-1], 0.024, 0.028, closed=True)
    F.bar(hi, F.along_shell((0, 0.205), (1, 0.205), 0.012, steps=64)[:-1], 0.05, 0.035, closed=True)
    o = hi.object("AS_Frames", coll, [gold], smooth=False)
    F.fix_normals(o)
    for p in o.data.polygons:
        p.use_smooth = False
    o["w"] = 1.0
    return o


def as_plinth(coll):
    """The stepped base the shrine stands on: moonstone treads with gold risers."""
    stone = Hm.mat_moonstone("AS_Stone")
    hi = Hm.Hi()
    y = 0.0
    rings = []
    for (r0, r1, h) in ((1.32, 1.28, 0.09), (1.14, 1.1, 0.09), (0.96, 0.92, 0.09)):
        rings += [(r0, y), (r1, y + h), (r1 - 0.14, y + h)]
        y += h
    profile = [(0.0, 0.0)] + rings
    lathe(hi, profile, sides=48)
    o = hi.object("AS_Plinth", coll, [stone], smooth=False)
    F.fix_normals(o)
    o["w"] = 1.2
    return o


def as_dome(coll, gold):
    hi = Hm.Hi()
    # the drum and the melon dome, seated over the crown
    base_v = 0.7
    y0 = F.on(0.0, base_v).y
    r0 = V((F.on(0.0, base_v).x, 0, F.on(0.0, base_v).z)).length
    prof = [(r0 + 0.05, y0 - 0.04), (r0 + 0.05, y0 + 0.02), (r0 - 0.03, y0 + 0.06), (r0 - 0.03, y0 + 0.14), (r0 + 0.02, y0 + 0.18)]
    lathe(hi, prof, sides=48)
    dome = []
    R = r0 + 0.02
    H_d = 1.05
    for i in range(18):
        t = i / 17
        # an onion: swelling out a little, then drawing up to a point
        rr = R * (1.0 + 0.1 * math.sin(math.pi * min(1.0, t * 2.2))) * (1 - t ** 1.5)
        dome.append((max(rr, 0.015), y0 + 0.18 + H_d * t))
    lathe(hi, dome, sides=48, ribs=12, rib_depth=0.09)
    top = y0 + 0.18 + H_d
    # the finial: a stem, an orb, a thinner stem and a crescent
    lathe(hi, [(0.06, top - 0.12), (0.03, top - 0.04), (0.022, top + 0.1)], sides=12)
    o = hi.object("AS_Dome", coll, [gold])
    F.fix_normals(o)
    o["w"] = 1.1
    s = Hm.Hi()
    sphere(s, (0, top + 0.17, 0), 0.085, rings=10, sides=16)
    orb = s.object("AS_Orb", coll, [gold])
    orb["w"] = 2.0
    # the crescent at its point
    c = Hm.Hi()
    cy = top + 0.42
    rows = []
    for i in range(25):
        t = i / 24
        a = math.radians(-40 + 260 * t)
        w = 0.05 * math.sin(math.pi * t) ** 0.8 + 0.003
        rows.append((c.v((math.cos(a) * (0.13 + w), cy + math.sin(a) * (0.13 + w), 0.012)), c.v((math.cos(a) * (0.13), cy + math.sin(a) * 0.13, 0.012)),
                     c.v((math.cos(a) * 0.13, cy + math.sin(a) * 0.13, -0.012)), c.v((math.cos(a) * (0.13 + w), cy + math.sin(a) * (0.13 + w), -0.012))))
    for i in range(24):
        for k in range(4):
            n = (k + 1) % 4
            c.f([rows[i][k], rows[i][n], rows[i + 1][n], rows[i + 1][k]], [(0, 0), (1, 0), (1, 1), (0, 1)])
    lathe(c, [(0.02, top + 0.22), (0.014, top + 0.3)], sides=8)
    cres = F.fix_normals(c.object("AS_Crescent", coll, [gold], smooth=False))
    cres["w"] = 2.0
    return o, orb, cres


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
            grid.append([hi.v(F.on((c + w * (-1 + 2 * j / 3)) % 1.0, v, -0.085)) for j in range(4)])
        for i in range(rows):
            for j in range(3):
                hi.f([grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]], [(0, 0), (1, 0), (1, 1), (0, 1)])
    return F.fix_normals(hi.object("AS_Panes", coll, [K.glow_material(AS_LIGHT)], smooth=False, weld=0))


def astral_all(coll):
    gold = Hm.mat_gold("AS_Gold")
    fr = as_gold(coll, gold)
    pl = as_plinth(coll)
    d, orb, cres = as_dome(coll, gold)
    return [fr, pl, d, orb, cres]


def astral_clay():
    coll = W.collection("AstralSanctumEggHi")
    shell = F.shell_mesh("AS_Shell", coll, 96, 64)
    pieces = astral_all(coll)
    g = as_light(coll)
    return {o.name: F.tris(o) for o in [shell, g] + pieces}


def astral_build():
    coll = W.collection("AstralSanctumEggHi")
    f, col, rough, metal, height = astral_paint()
    mat = F.shell_material("AS_Wall", col, rough, metal)
    pieces = astral_all(coll)
    g = as_light(coll)
    return F.assemble("AstralSanctumEgg", coll, mat, height, pieces, {AS_LIGHT: [g]}, budget=7800, shell_frac=0.6, low_nu=72, low_nv=48, hard=35, shell_ext=0.14, shell_ray=0.3)


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
        h = 0.36 if tall else 0.22
        side = V((0, 1, 0)).cross(out).normalized()
        w = 0.1 if tall else 0.07
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
    top_y = y0 + 0.92
    for k in range(4):
        a = TAU * k / 4
        out = V((math.sin(a), 0, math.cos(a)))
        pts = [out * (r0 + 0.02) + V((0, y0 + 0.3, 0)), out * (r0 + 0.02) * 0.92 + V((0, y0 + 0.52, 0)), out * r0 * 0.62 + V((0, y0 + 0.76, 0)), out * r0 * 0.22 + V((0, y0 + 0.88, 0)), V((0, top_y, 0))]
        Hm.htube(hi, pts, lambda t: 0.036 * (1 - 0.2 * t), sides=8, per=6, wobble=0, tip=False)
    lathe(hi, [(0.05, top_y - 0.06), (0.11, top_y - 0.01), (0.06, top_y + 0.03), (0.04, top_y + 0.05)], sides=20)
    o = hi.object("HT_Coronet", coll, [gold])
    F.fix_normals(o)
    o["w"] = 1.1
    s = Hm.Hi()
    sphere(s, (0, top_y + 0.13, 0), 0.1, rings=12, sides=18)
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
        sphere(p, V((math.sin(a) * (r0 + 0.02), y0 + 0.385, math.cos(a) * (r0 + 0.02))), 0.055, rings=5, sides=8)
    beads = p.object("HT_Pearls", coll, [Hm.mat_pearl("HT_PearlMat")])
    beads["w"] = 4.0
    return rails, beads


def ht_cushion(coll):
    spheres = []
    # a wide flat bed: broad billows in the middle, smaller ones crowding its edge, all melted together
    for ring, (count, R, r, y, sy) in enumerate(((10, 0.74, 0.44, 0.3, 0.62), (14, 1.2, 0.3, 0.23, 0.72))):
        for k in range(count):
            a = TAU * (k + 0.37 * ring) / count
            wob = math.sin(k * 2.3 + ring)
            spheres.append((V((math.sin(a) * R * (1 + 0.04 * wob), y + 0.02 * wob, math.cos(a) * R * (1 + 0.04 * wob))), r * (0.92 + 0.14 * wob), (1.0, sy, 1.0)))
    bed = F.lobes("HT_Cloud", coll, Hm.mat_cloud("HT_CloudMat"), spheres, voxel=0.024, smooth=10)
    bed["w"] = 0.6
    return bed


def ht_mandorla(coll, gold):
    hi = Hm.Hi()
    z0 = -1.02
    cx, cy = 0.0, 2.02
    W_, H_ = 1.4, 1.86
    n = V((0, 0, 1))

    def rim(t, scale=1.0):
        """A pointed oval (vesica): two arcs meeting at the top and bottom."""
        a = TAU * t
        x = math.sin(a)
        y = math.cos(a)
        # sharpen toward the poles
        xx = x * (abs(x) ** 0.25)
        return V((cx + xx * W_ * scale, cy + y * H_ * scale, z0))
    outline = [(rim(k / 72), n) for k in range(72)]
    F.bar(hi, outline, 0.09, 0.08, closed=True, foot=0.05)
    inner = [(rim(k / 72, 0.9), n) for k in range(72)]
    F.bar(hi, inner, 0.05, 0.05, closed=True, foot=0.04)
    # the plate between them, slightly hollow, with rays
    disc = []
    rows = 8
    rings = []
    for j in range(rows + 1):
        s = 0.9 * j / rows
        rings.append([hi.v(rim(k / 48, max(s, 0.001)) + V((0, 0, -0.02 - 0.1 * (0.9 - s)))) for k in range(48)])
    for j in range(rows):
        for k in range(48):
            q = (k + 1) % 48
            hi.f([rings[j][k], rings[j][q], rings[j + 1][q], rings[j + 1][k]], [(0, 0), (1, 0), (1, 1), (0, 1)])
    # the flames: tongues round the rim, licking outward and bending the same way, as fire in wind
    flames = 26
    for k in range(flames):
        t = (k + 0.5) / flames
        if abs(t - 0.5) < 0.06:
            continue                 # none at the foot, where it meets the cloud
        p = rim(t)
        out = (p - V((cx, cy, z0))).normalized()
        side = V((-out.y, out.x, 0))
        # bigger toward the head, each one a tongue that swells, then bends over to a point
        high = 0.5 + 0.5 * math.cos(TAU * t)
        L = (0.3 + 0.26 * high) * (1 + 0.14 * math.sin(k * 2.1))
        sway = 1 if t < 0.5 else -1
        rows_ = []
        for i in range(11):
            q = i / 10
            hw = (0.15 + 0.05 * high) * (1 - q ** 1.7) * (0.62 + 0.38 * math.sin(math.pi * min(1, q * 2.2)))
            c = p - out * 0.02 + out * L * q + side * sway * (0.18 * q * q - 0.08 * math.sin(math.pi * q))
            d = 0.04 * (1 - q)
            rows_.append([hi.v(c - side * hw), hi.v(c + V((0, 0, d))), hi.v(c + side * hw), hi.v(c - V((0, 0, d)))])
        for i in range(10):
            for r in range(4):
                nx = (r + 1) % 4
                hi.f([rows_[i][r], rows_[i][nx], rows_[i + 1][nx], rows_[i + 1][r]], [(0, 0), (1, 0), (1, 1), (0, 1)])
    # the back is not left blank: rays run out over the plate from behind the egg
    for k in range(24):
        a = TAU * (k + 0.5) / 24
        pts = []
        for i in range(9):
            q = 0.25 + 0.62 * i / 8
            pts.append((rim(a / TAU, q) + V((0, 0, -0.1 * (0.9 - q) - 0.06)), V((0, 0, -1))))
        F.bar(hi, pts, lambda t: 0.04 * (1 - 0.7 * t), 0.03, foot=0.02)
    o = hi.object("HT_Mandorla", coll, [gold], smooth=False)
    F.fix_normals(o)
    for p in o.data.polygons:
        p.use_smooth = False
    o["w"] = 1.7
    # the Neon: a line round the mandorla's inner rim
    glow = Hm.Hi()
    pts = [(rim(k / 72, 0.945) + V((0, 0, 0.06)), n) for k in range(72)]
    F.prism(glow, pts, 0.024, height=lambda w: w * 0.3, closed=True)
    g = glow.object("HT_Halo", coll, [K.glow_material(HT_FLAME)], smooth=False, weld=0)
    # a strut joining the mandorla to the egg's back
    h2 = Hm.Hi()
    a, b = F.on(0.0, 0.55, -0.02), V((0, F.on(0.0, 0.55).y, z0))
    Hm.htube(h2, [a, a.lerp(b, 0.5), b], lambda t: 0.14, sides=10, per=3, wobble=0, tip=False)
    strut = h2.object("HT_Strut", coll, [gold])
    strut["w"] = 1.0
    return o, g, strut


def heavenly_all(coll):
    gold = Hm.mat_gold("HT_Gold")
    co, orb, top = ht_coronet(coll, gold)
    rails, beads = ht_beads(coll, gold)
    bed = ht_cushion(coll)
    m, halo, strut = ht_mandorla(coll, gold)
    return [co, orb, rails, beads, bed, m, strut], halo


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
    return F.assemble("HeavenlyThroneEgg", coll, mat, height, pieces, {HT_FLAME: [g]}, budget=10000, shell_frac=0.56, low_nu=56, low_nv=36, hard=35, ao_floor=0.62, att_ext=0.09, att_ray=0.28)
