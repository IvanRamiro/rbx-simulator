"""Starting Island set pieces: the Qi Compass spawn plaza, stone lanterns, lotus egg pedestals,
route waystones and the Qi Spring (rim stones, water, spillway, source rock, lotus stepping stones).

Every piece is authored in Roblox studs around its own origin (ground centre) except the spring
pieces, which are authored in the Starting Island's coordinates (start_island). Yggdrasil places
them all (ygg_props.placements); the spring as one piece, moved onto its rim.
"""
import bpy, bmesh, math, os, random
import worldlib as W
import start_island as S

TAU = 2 * math.pi
NAME = "StartingIsland"


# ---------- prop atlas ----------
def _n(u, v, f, seed):
    a = u * TAU
    return W.fbm(math.cos(a) * f + 5, math.sin(a) * f + v * f * 2, seed=seed, octaves=3)


def _ramp(lo, hi, v, n, k=0.04):
    return tuple(max(0.0, min(1.0, lo[i] + (hi[i] - lo[i]) * v + k * n)) for i in range(3))


def pale(u, v):
    return _ramp((0.56, 0.53, 0.49), (0.86, 0.83, 0.77), v, _n(u, v, 7, 1))


def dark(u, v):
    return _ramp((0.22, 0.24, 0.28), (0.47, 0.49, 0.54), v, _n(u, v, 7, 2))


def jade(u, v):
    n = _n(u, v, 4, 3)
    vein = max(0.0, 1 - abs(_n(u, v * 0.5, 9, 4)) * 6)
    c = _ramp((0.2, 0.47, 0.37), (0.55, 0.84, 0.68), v, n, 0.06)
    return tuple(min(1.0, c[i] + 0.12 * vein) for i in range(3))


def bronze(u, v):
    n = _n(u, v, 8, 5)
    c = _ramp((0.45, 0.33, 0.16), (0.86, 0.69, 0.36), v, n, 0.05)
    if _n(u, v, 13, 6) > 0.45:  # verdigris flecks
        return (0.33, 0.56, 0.48)
    return c


def lacquer(u, v):
    return _ramp((0.4, 0.09, 0.07), (0.76, 0.2, 0.14), v, _n(u, v, 6, 7), 0.03)


def wood(u, v):
    grain = math.sin(u * TAU * 23 + 3 * _n(u, v, 3, 8))
    return _ramp((0.2, 0.13, 0.08), (0.43, 0.3, 0.19), v, grain, 0.03)


def water(u, v):
    return _ramp((0.08, 0.34, 0.4), (0.38, 0.78, 0.8), v, _n(u, v, 5, 9), 0.03)


def pine(u, v):
    return _ramp((0.09, 0.22, 0.15), (0.3, 0.52, 0.32), v, _n(u, v, 9, 10), 0.05)


def blossom(u, v):
    return _ramp((0.8, 0.47, 0.6), (1.0, 0.85, 0.89), v, _n(u, v, 9, 11), 0.05)


def bark(u, v):
    return _ramp((0.22, 0.18, 0.15), (0.47, 0.4, 0.34), v, _n(u, v * 0.3, 12, 12), 0.05)


FLOWER_COLOURS = [(0.95, 0.94, 0.9), (0.98, 0.82, 0.3), (0.62, 0.45, 0.85), (0.95, 0.5, 0.4), (0.3, 0.55, 0.28)]


def flowers(u, v):
    c = FLOWER_COLOURS[min(4, int(u * 5))]
    return tuple(c[i] * (0.7 + 0.3 * v) for i in range(3))


def paper(u, v):
    return _ramp((0.95, 0.72, 0.42), (1.0, 0.93, 0.76), v, _n(u, v, 5, 13), 0.02)


STRIPS = [(64, pale), (48, dark), (48, jade), (32, bronze), (32, lacquer), (32, wood), (32, water),
          (64, pine), (48, blossom), (48, bark), (32, flowers), (32, paper)]
PALE, DARK, JADE, BRONZE, LACQUER, WOOD, WATER, PINE, BLOSSOM, BARK, FLOWERS, PAPER = range(12)


def flower_u(k):
    return (k + 0.5) / 5


# ---------- geometry helpers ----------
def xf(p, yaw=0.0, origin=(0, 0, 0)):
    """Local -> parent: yaw about +Y (Roblox convention), then translate."""
    x, y, z = p
    cs, sn = math.cos(yaw), math.sin(yaw)
    return (origin[0] + x * cs + z * sn, origin[1] + y, origin[2] - x * sn + z * cs)


def newell(pts):
    nx = ny = nz = 0.0
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return nx, ny, nz


def oriented(mb, pts, want, band, u=0.5, shade=None):
    """Adds a face, flipping it if needed so its normal points along `want`."""
    n = newell(pts)
    if n[0] * want[0] + n[1] * want[1] + n[2] * want[2] < 0:
        pts = pts[::-1]
        shade = shade[::-1] if shade else None
    v0, v1 = band
    shade = shade or [0.8] * len(pts)
    mb.face(list(pts), [(u, v0 + (v1 - v0) * s) for s in shade])


def inset(poly, d):
    """Inset a convex 2D polygon (list of (x, z)) by distance d."""
    cx = sum(p[0] for p in poly) / len(poly); cz = sum(p[1] for p in poly) / len(poly)
    lines = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        ex, ez = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ez)
        nx, nz = -ez / L, ex / L
        if (cx - a[0]) * nx + (cz - a[1]) * nz < 0:
            nx, nz = -nx, -nz
        lines.append(((a[0] + nx * d, a[1] + nz * d), (ex, ez)))
    out = []
    for i in range(len(lines)):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        den = d1[0] * d2[1] - d1[1] * d2[0]
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out


def slab_tile(mb, poly, y_top, y_bot, band, u, shade):
    """A flat tile: top face plus vertical sides (convex 2D outline)."""
    cx = sum(p[0] for p in poly) / len(poly); cz = sum(p[1] for p in poly) / len(poly)
    oriented(mb, [(x, y_top, z) for x, z in poly], (0, 1, 0), band, u, [shade] * len(poly))
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        mx, mz = (a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2 - cz
        oriented(mb, [(a[0], y_top, a[1]), (b[0], y_top, b[1]), (b[0], y_bot, b[1]), (a[0], y_bot, a[1])],
                 (mx, 0, mz), band, u, [shade * 0.75, shade * 0.75, shade * 0.5, shade * 0.5])


def disc_z(mb, centre, r0, r1, seg, band, yaw=0.0, shade=1.0, u=0.5):
    """A flat disc (r0 = 0) or annulus in a vertical plane facing local +Z."""
    ox, oy, oz = centre
    want = xf((0, 0, 1), yaw)
    for i in range(seg):
        a0, a1 = TAU * i / seg, TAU * (i + 1) / seg
        p = lambda r, a: xf((math.cos(a) * r, math.sin(a) * r, 0), yaw, centre)
        if r0 == 0:
            oriented(mb, [p(r1, a0), p(r1, a1), (ox, oy, oz)], want, band, u, [shade] * 3)
        else:
            oriented(mb, [p(r0, a0), p(r1, a0), p(r1, a1), p(r0, a1)], want, band, u, [shade] * 4)


def pebble(mb, centre, rx, rz, h, yaw, seed, band, sink=0.8, u=None):
    """A smooth river stone: squashed dome with a buried base."""
    rnd = random.Random(seed)
    seg = 8
    profile = [(0.55, h * 0.92, 1.0), (0.92, h * 0.55, 0.85), (1.0, h * 0.15, 0.65), (0.82, -sink, 0.4)]
    phase = rnd.uniform(0, TAU)
    rings = []
    for s, y, sh in profile:
        ring = []
        for i in range(seg):
            th = phase + TAU * i / seg
            w = 1 + 0.16 * (rnd.random() - 0.5) * 2
            ring.append(xf((math.cos(th) * rx * s * w, y, math.sin(th) * rz * s * w), yaw, centre))
        rings.append(ring)
    u = rnd.random() if u is None else u
    apex = (centre[0], centre[1] + h, centre[2])
    for i in range(seg):
        j = (i + 1) % seg
        oriented(mb, [rings[0][j], rings[0][i], apex], (0, 1, 0), band, u, [1.0, 1.0, 1.0])
    for k in range(len(rings) - 1):
        for i in range(seg):
            j = (i + 1) % seg
            mid = [(rings[k][i][q] + rings[k][j][q]) / 2 - centre[q] for q in range(3)]
            oriented(mb, [rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]], (mid[0], 0, mid[2]), band, u,
                     [profile[k][2], profile[k][2], profile[k + 1][2], profile[k + 1][2]])


def hull_rock(name, coll, mat, band, blobs, seed):
    """A scholar's rock: overlapping convex blobs (centre, radius x/y/z) merged into one mesh."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    v0, v1 = band
    lo = min(c[1] - r[1] for c, r in blobs); hi = max(c[1] + r[1] for c, r in blobs)
    for c, r in blobs:
        part = bmesh.new()
        for _ in range(26):
            th, ph = rnd.uniform(0, TAU), math.acos(rnd.uniform(-1, 1))
            k = 0.8 + 0.25 * rnd.random()
            part.verts.new(W.rb(c[0] + math.cos(th) * math.sin(ph) * r[0] * k, c[1] + math.cos(ph) * r[1] * k,
                                c[2] + math.sin(th) * math.sin(ph) * r[2] * k))
        bmesh.ops.convex_hull(part, input=part.verts)
        me = bpy.data.meshes.new("tmp"); part.to_mesh(me); part.free()
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for l in f.loops:
            co = l.vert.co
            l[uv].uv = ((math.atan2(co.y, co.x) / TAU) % 1, v0 + (v1 - v0) * (0.25 + 0.75 * (co.z - lo) / (hi - lo)))
        f.smooth = False
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    return o


# ---------- Qi Compass: the spawn plaza ----------
OCT = math.pi / 8
TRIGRAMS = {  # Earlier Heaven arrangement; lines listed bottom (nearest the centre) to top
    90: (1, 1, 1),    # south: Qian, heaven
    45: (1, 1, 0),    # south-east: Dui, lake
    0: (1, 0, 1),     # east: Li, fire
    -45: (1, 0, 0),   # north-east: Zhen, thunder
    -90: (0, 0, 0),   # north: Kun, earth
    -135: (0, 0, 1),  # north-west: Gen, mountain
    180: (0, 1, 0),   # west: Kan, water
    135: (0, 1, 1),   # south-west: Xun, wind
}
DECK_Y, GROOVE_Y = 1.0, 0.88
RINGS = [(6.1, 9.4, 1), (9.4, 12.8, 2), (12.8, 16.4, 1)]  # apothem from, to, tiles per sector


def oct_pt(apothem, angle):
    r = apothem / math.cos(OCT)
    return (math.cos(angle) * r, math.sin(angle) * r)


def qi_compass(coll, mat, bands):
    mb = W.MeshBuilder()
    rnd = random.Random(8)
    # platform body: octagonal deck with one step, skirt sinking into the ground
    c = 1 / math.cos(OCT)
    mb.lathe([(16.4 * c, GROOVE_Y, 0.8), (16.4 * c, 0.55, 0.6), (18.0 * c, 0.5, 0.85), (18.3 * c, 0.3, 0.7),
              (18.3 * c, -1.6, 0.35)], 8, bands[PALE], phase=OCT, cap_top=True, u_repeat=0.0)
    # tiles
    for s in range(8):
        phi = math.radians(s * 45)
        a0, a1 = phi - OCT, phi + OCT
        for r0, r1, n in RINGS:
            for t in range(n):
                ta, tb = t / n, (t + 1) / n
                in_a, in_b = oct_pt(r0, a0), oct_pt(r0, a1)
                out_a, out_b = oct_pt(r1, a0), oct_pt(r1, a1)
                lerp = lambda p, q, k: (p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k)
                poly = [lerp(in_a, in_b, ta), lerp(in_a, in_b, tb), lerp(out_a, out_b, tb), lerp(out_a, out_b, ta)]
                slab_tile(mb, inset(poly, 0.14), DECK_Y, GROOVE_Y, bands[PALE], rnd.random(), 0.82 + 0.18 * rnd.random())
    # trigram bars (bronze inlay standing 0.1 proud of the outer plaques)
    for deg, lines in TRIGRAMS.items():
        phi = math.radians(deg)
        yaw = math.atan2(-math.cos(phi), -math.sin(phi))
        for k, solid in enumerate(lines):
            a = 13.75 + 0.95 * k
            cx, cz = math.cos(phi) * a, math.sin(phi) * a
            length = 0.5 * 0.828 * a
            if solid:
                mb.box((cx, DECK_Y + 0.05, cz), (length, 0.1, 0.5), bands[BRONZE], yaw=yaw, u=0.3, top_shade=0.95, side_shade=0.6)
            else:
                half = (length - 0.8) / 2
                tx, tz = -math.sin(phi), math.cos(phi)
                for sgn in (-1, 1):
                    off = sgn * (half / 2 + 0.4)
                    mb.box((cx + tx * off, DECK_Y + 0.05, cz + tz * off), (half, 0.1, 0.5), bands[BRONZE], yaw=yaw, u=0.3,
                           top_shade=0.95, side_shade=0.6)
    # central dais with a jade disc and a bronze compass rose
    mb.lathe([(3.9, 1.62, 0.92), (5.0, 1.62, 0.95), (5.3, 1.5, 0.8), (5.45, 1.3, 0.65), (5.45, GROOVE_Y, 0.5)], 32,
             bands[PALE], cap_top=False, u_repeat=0.0)
    mb.lathe([(3.9, 1.7, 1.0), (3.9, 1.62, 0.5)], 32, bands[JADE], cap_top=True, u_repeat=1.0)
    star = []
    for i in range(16):
        a = TAU * i / 16
        r = (3.5 if i % 4 == 0 else 2.5) if i % 2 == 0 else 0.75
        star.append((math.cos(a) * r, math.sin(a) * r))
    for i in range(16):
        a, b = star[i], star[(i + 1) % 16]
        oriented(mb, [(a[0], 1.78, a[1]), (b[0], 1.78, b[1]), (0, 1.78, 0)], (0, 1, 0), bands[BRONZE], 0.6, [0.95] * 3)
        oriented(mb, [(a[0], 1.78, a[1]), (b[0], 1.78, b[1]), (b[0], 1.7, b[1]), (a[0], 1.7, a[1])],
                 ((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2), bands[BRONZE], 0.6, [0.6, 0.6, 0.4, 0.4])
    mb.lathe([(0.45, 1.98, 1.0), (0.7, 1.78, 0.7)], 12, bands[BRONZE], cap_top=True, u_repeat=0.0)
    return mb.object("SI_QiCompass", coll, mat)


def qi_compass_glow(coll, mat, bands):
    """Qi channels in the deck joints: inner and outer octagon rings plus eight radial lines."""
    mb = W.MeshBuilder()
    y = 0.95
    for a_in, a_out in ((5.62, 6.06), (12.7, 12.9)):
        for s in range(8):
            a0, a1 = math.radians(s * 45) - OCT, math.radians(s * 45) + OCT
            p = [oct_pt(a_in, a0), oct_pt(a_in, a1), oct_pt(a_out, a1), oct_pt(a_out, a0)]
            oriented(mb, [(x, y, z) for x, z in p], (0, 1, 0), bands[PAPER], 0.5, [1.0] * 4)
    for s in range(8):
        ang = math.radians(s * 45) + OCT
        dx, dz = math.cos(ang), math.sin(ang)
        tx, tz = -dz * 0.11, dx * 0.11
        r0, r1 = 6.06 / math.cos(OCT), 12.7 / math.cos(OCT)
        p = [(dx * r0 - tx, dz * r0 - tz), (dx * r0 + tx, dz * r0 + tz), (dx * r1 + tx, dz * r1 + tz), (dx * r1 - tx, dz * r1 - tz)]
        oriented(mb, [(x, y, z) for x, z in p], (0, 1, 0), bands[PAPER], 0.5, [1.0] * 4)
    return mb.object("SI_QiCompassGlow", coll, mat)


# ---------- stone lantern ----------
def stone_lantern(coll, mat, bands):
    mb = W.MeshBuilder()
    P, D = bands[PALE], bands[DARK]
    mb.lathe([(0.75, 1.35, 0.9), (0.95, 1.15, 0.8), (1.15, 0.6, 0.7), (1.3, 0.4, 0.6), (1.3, -0.8, 0.4)], 6, P, cap_top=True, u_repeat=0.0)
    mb.lathe([(0.42, 3.95, 0.85), (0.36, 1.35, 0.6)], 6, P, cap_top=False, u_repeat=0.0)
    mb.lathe([(0.95, 4.35, 0.95), (1.2, 4.3, 0.85), (1.25, 4.15, 0.7), (1.05, 3.95, 0.55), (0.42, 3.9, 0.5)], 6, P, cap_top=True, u_repeat=0.0)
    for k in range(6):
        a = TAU * k / 6
        mb.box((math.cos(a) * 0.86, 5.1, math.sin(a) * 0.86), (0.26, 1.5, 0.26), P, yaw=-a, u=0.4, top_shade=0.9, side_shade=0.7)
    mb.lathe([(0.22, 6.95, 0.95), (0.55, 6.7, 0.9), (1.25, 6.25, 0.82), (1.75, 6.05, 0.78), (1.88, 6.14, 0.75),
              (1.82, 5.92, 0.5), (0.95, 5.85, 0.35)], 6, D, cap_top=True, cap_bottom=True, u_repeat=0.0)
    mb.lathe([(0.12, 7.75, 1.0), (0.3, 7.42, 0.9), (0.2, 7.18, 0.7), (0.28, 6.95, 0.6)], 6, bands[BRONZE], cap_top=True, u_repeat=0.0)
    return mb.object("SI_StoneLantern", coll, mat)


def lantern_light(coll, mat, bands):
    mb = W.MeshBuilder()
    mb.lathe([(0.62, 5.78, 1.0), (0.62, 4.38, 0.85)], 6, bands[PAPER], cap_top=True, cap_bottom=True, u_repeat=0.0)
    return mb.object("SI_LanternLight", coll, mat)


# ---------- lotus egg pedestal ----------
PEDESTAL_TOP = 3.85  # where the egg rests


def egg_pedestal(coll, mat, bands):
    mb = W.MeshBuilder()
    mb.lathe([(3.6, 1.2, 0.95), (3.8, 1.05, 0.75), (3.8, 0.6, 0.6), (4.6, 0.6, 0.9), (4.8, 0.45, 0.7), (4.8, -1.2, 0.45)],
             40, bands[PALE], cap_top=True, u_repeat=2.0)
    mb.lathe([(1.1, 3.25, 0.8), (0.95, 2.8, 0.72), (0.85, 1.8, 0.6), (1.3, 1.38, 0.62), (1.55, 1.2, 0.5)], 16, bands[DARK],
             cap_top=False, u_repeat=1.0)
    amp = [0, 0, 0.05, 0.14, 0.14, 0.12, 0.06, 0]
    petals = lambda th, k: 1 - amp[k] * (1 - abs(math.cos(4 * th)) ** 0.6)
    mb.lathe([(0.0, 3.8, 0.7), (0.6, 3.8, 0.75), (1.5, 4.0, 0.8), (2.6, 4.8, 0.95), (2.9, 4.95, 1.0), (2.7, 4.3, 0.8),
              (2.0, 3.6, 0.6), (1.1, 3.22, 0.45)], 48, bands[JADE], rmod=petals, cap_top=False, u_repeat=1.0)
    amp2 = [0.16, 0.12, 0.06, 0]
    mb.lathe([(2.45, 3.95, 0.9), (2.6, 3.6, 0.72), (1.85, 3.3, 0.55), (1.1, 3.15, 0.4)], 48, bands[JADE],
             rmod=lambda th, k: 1 - amp2[k] * (1 - abs(math.cos(4 * th)) ** 0.6), phase=TAU / 16, cap_top=False, u_repeat=1.0)
    return mb.object("SI_EggPedestal", coll, mat)


def egg_glow_ring(coll, mat, bands):
    mb = W.MeshBuilder()
    mb.lathe([(3.95, 0.64, 1.0), (4.4, 0.64, 1.0)], 48, bands[PAPER], cap_top=False, u_repeat=0.0)
    return mb.object("SI_EggGlowRing", coll, mat)


# ---------- route waystone ----------
STELE_TOP = 7.6


def waystone(coll, mat, bands):
    mb = W.MeshBuilder()
    mb.box((0, -0.15, 0), (4.2, 1.7, 3.0), bands[DARK], u=0.3, top_shade=0.85, side_shade=0.6)
    mb.box((0, 1.0, 0), (3.4, 0.6, 2.4), bands[DARK], u=0.6, top_shade=0.95, side_shade=0.7)
    # arched stele, 0.76 thick
    poly = [(-1.25, 1.3), (1.25, 1.3), (1.25, STELE_TOP)]
    for i in range(1, 12):
        a = math.pi * i / 12
        poly.append((math.cos(a) * 1.25, STELE_TOP + math.sin(a) * 1.25))
    poly.append((-1.25, STELE_TOP))
    t = 0.38
    oriented(mb, [(x, y, t) for x, y in poly], (0, 0, 1), bands[PALE], 0.5, [0.95] * len(poly))
    oriented(mb, [(x, y, -t) for x, y in poly], (0, 0, -1), bands[PALE], 0.5, [0.8] * len(poly))
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        nx, ny = b[1] - a[1], -(b[0] - a[0])
        oriented(mb, [(a[0], a[1], t), (b[0], b[1], t), (b[0], b[1], -t), (a[0], a[1], -t)], (nx, ny, 0), bands[PALE], 0.5,
                 [0.75] * 4)
    # inscription panels (the destination is written here in Roblox) and a collar at the foot
    for side in (1, -1):
        z = side * (t + 0.03)
        panel = [(-0.85, 2.2), (0.85, 2.2), (0.85, 6.3), (-0.85, 6.3)]
        oriented(mb, [(x, y, z) for x, y in panel], (0, 0, side), bands[DARK], 0.5, [0.55] * 4)
        for (ax, ay), (bx, by) in zip(panel, panel[1:] + panel[:1]):
            oriented(mb, [(ax, ay, z), (bx, by, z), (bx, by, side * t), (ax, ay, side * t)], (by - ay, -(bx - ax), 0),
                     bands[DARK], 0.5, [0.4] * 4)
    mb.box((0, 1.5, 0), (2.9, 0.4, 1.15), bands[PALE], u=0.7, top_shade=0.9, side_shade=0.65)
    # bronze frame for the destination disc
    disc_z(mb, (0, STELE_TOP, t + 0.02), 0.62, 0.86, 20, bands[BRONZE], shade=0.9)
    return mb.object("SI_Waystone", coll, mat)


def waystone_glow(coll, mat, bands):
    mb = W.MeshBuilder()
    disc_z(mb, (0, STELE_TOP, 0.41), 0, 0.62, 20, bands[PAPER])
    return mb.object("SI_WaystoneGlow", coll, mat)


# ---------- Qi Spring (island-local coordinates) ----------
def pool_centre():
    return ((S.POOL_A[0] + S.POOL_B[0]) / 2, (S.POOL_A[1] + S.POOL_B[1]) / 2)


def contour(offset, seg=64):
    """Points (x, z) where the pool outline sits `offset` studs outside the water edge."""
    cx, cz = pool_centre()
    out = []
    for i in range(seg):
        a = TAU * i / seg
        lo, hi = 0.0, 30.0
        for _ in range(30):
            mid = (lo + hi) / 2
            if S.pool_distance(cx + math.cos(a) * mid, cz + math.sin(a) * mid) < offset:
                lo = mid
            else:
                hi = mid
        out.append((cx + math.cos(a) * lo, cz + math.sin(a) * lo, a))
    return out


SPILL = [(54.6, -47.5, 5.25), (59.5, -51.1, 4.3), (S.SPILL_END[0], S.SPILL_END[1], 3.3), (66.0, -55.8, 3.05)]


def spill_direction():
    cx, cz = pool_centre()
    return math.atan2(SPILL[0][1] - cz, SPILL[0][0] - cx)


def spring_water(coll, mat, bands):
    mb = W.MeshBuilder()
    cx, cz = pool_centre()
    ring = contour(0.7)
    y = S.POOL_WATER
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]
        oriented(mb, [(a[0], y, a[1]), (b[0], y, b[1]), (cx, y, cz)], (0, 1, 0), bands[WATER], 0.5, [0.85, 0.85, 1.0])
    # the stream running down the spillway trough
    for p, q in zip(SPILL, SPILL[1:]):
        dx, dz = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dz); ax, az = -dz / L * 1.5, dx / L * 1.5
        oriented(mb, [(p[0] - ax, p[2] + 0.35, p[1] - az), (p[0] + ax, p[2] + 0.35, p[1] + az),
                      (q[0] + ax, q[2] + 0.35, q[1] + az), (q[0] - ax, q[2] + 0.35, q[1] - az)], (0, 1, 0), bands[WATER], 0.5,
                 [0.9, 0.9, 0.9, 0.9])
    return mb.object("SI_SpringWater", coll, mat)


def spring_rim(coll, mat, bands):
    """River stones ringing the pool, open where the water leaves for the spillway."""
    mb = W.MeshBuilder()
    rnd = random.Random(21)
    spill = spill_direction()
    ring = contour(1.0, seg=96)
    acc, last = 0.0, None
    for x, z, a in ring:
        if last is not None:
            acc += math.hypot(x - last[0], z - last[1])
        last = (x, z)
        gap = abs((a - spill + math.pi) % TAU - math.pi)
        if acc < 2.1 or gap < 0.3:
            continue
        acc = 0.0
        ground = S.height(x, z)[0]
        size = 0.9 + 0.6 * rnd.random()
        pebble(mb, (x, ground - 0.2, z), size * 1.3, size, 0.7 + 0.6 * rnd.random(), math.pi / 2 - a, rnd.randint(0, 1 << 20),
               bands[DARK], sink=1.2)
    return mb.object("SI_SpringRim", coll, mat)


def spring_spillway(coll, mat, bands):
    """A carved stone trough carrying the spring over the cove edge, ending in a spout lip."""
    mb = W.MeshBuilder()
    prof = [(-2.6, -2.2), (-2.6, 1.0), (-1.5, 1.0), (-1.5, 0.0), (1.5, 0.0), (1.5, 1.0), (2.6, 1.0), (2.6, -2.2)]
    secs = []
    for k, p in enumerate(SPILL):
        q = SPILL[min(k + 1, len(SPILL) - 1)]; o = SPILL[max(k - 1, 0)]
        dx, dz = q[0] - o[0], q[1] - o[1]
        L = math.hypot(dx, dz); ax, az = -dz / L, dx / L
        lip = k == len(SPILL) - 1  # the spout over the cliff tapers to a thin, low-walled lip
        shape = [(a * (0.85 if lip else 1.0), (yy * 0.45 if yy > 0 else -0.5) if lip else yy) for a, yy in prof]
        secs.append([(p[0] + ax * a, p[2] + yy, p[1] + az * a) for a, yy in shape])
        secs[-1].append((ax, az))
    for k in range(len(secs) - 1):
        A, B = secs[k], secs[k + 1]
        axv = A[-1]
        for i in range(len(prof)):
            j = (i + 1) % len(prof)
            ea, ey = prof[j][0] - prof[i][0], prof[j][1] - prof[i][1]
            na, ny = -ey, ea  # profile is walked clockwise, so this points out of the stone
            want = (axv[0] * na, ny, axv[1] * na)
            sh = 0.85 if ny > 0.5 else 0.55
            oriented(mb, [A[i], A[j], B[j], B[i]], want, bands[PALE if ny > 0.5 else DARK], 0.4 + 0.2 * k / 3, [sh] * 4)
    # end caps (three rectangles each: two walls and the floor slab)
    for sec, sign in ((secs[0], -1), (secs[-1], 1)):
        p, q = SPILL[0 if sign < 0 else -1], SPILL[1 if sign < 0 else -2]
        want = ((p[0] - q[0]), 0, (p[1] - q[1]))
        for quad in ((0, 1, 2, None), (5, 6, 7, None)):
            a, b, c = sec[quad[0]], sec[quad[1]], sec[quad[2]]
            d = (a[0] + c[0] - b[0], a[1] + c[1] - b[1], a[2] + c[2] - b[2])
            oriented(mb, [a, b, c, d], want, bands[DARK], 0.5, [0.6] * 4)
        floor = [sec[0], sec[3], sec[4], sec[7]]
        oriented(mb, [floor[0], (sec[3][0], sec[3][1], sec[3][2]), sec[4], sec[7]], want, bands[DARK], 0.5, [0.6] * 4)
    return mb.object("SI_SpringSpillway", coll, mat)


SPRING_ROCK = (36.0, -47.5)


def spring_rock(coll, mat, bands):
    x, z = SPRING_ROCK
    g = S.height(x, z)[0] - 0.8
    blobs = [((x, g + 1.6, z), (3.2, 2.4, 2.8)), ((x + 0.9, g + 4.4, z - 0.4), (2.4, 2.2, 2.0)),
             ((x - 0.5, g + 7.0, z + 0.3), (1.9, 2.0, 1.7)), ((x + 0.6, g + 9.4, z - 0.2), (1.3, 1.9, 1.2)),
             ((x + 1.9, g + 6.0, z + 0.8), (1.2, 1.1, 1.0))]
    return hull_rock("SI_SpringRock", coll, mat, bands[DARK], blobs, 17)


LOTUS_STONES = [(41.2, -38.6), (45.0, -41.1), (48.7, -43.4)]


def lotus_stone(coll, mat, bands):
    mb = W.MeshBuilder()
    notch = lambda th, k: 1 - (0.25 if k < 2 and abs((th + math.pi) % TAU - math.pi) < 0.25 else 0)
    mb.lathe([(1.55, 0.0, 1.0), (1.75, -0.14, 0.82), (1.8, -0.5, 0.6), (1.2, -2.9, 0.35)], 14, bands[JADE], rmod=notch,
             cap_top=True, u_repeat=1.0)
    return mb.object("SI_LotusStone", coll, mat)


def face_yaw(fx, fz):
    """Yaw that turns a piece's local +Z toward (fx, fz)."""
    return math.atan2(fx, fz)


# ---------- build ----------
BUILDERS = [qi_compass, qi_compass_glow, stone_lantern, lantern_light, egg_pedestal, egg_glow_ring, waystone,
            waystone_glow, spring_water, spring_rim, spring_spillway, spring_rock, lotus_stone]


def build():
    img, bands = W.atlas_image("StartingIsland_PropAtlas", 512, STRIPS)
    mat = W.textured_material("StartingIsland_PropMat", img)
    root = W.collection(NAME)
    coll = W.collection("SI_Props", root)
    W.clear_collection(coll)
    objs = [b(coll, mat, bands) for b in BUILDERS]
    return objs, img
