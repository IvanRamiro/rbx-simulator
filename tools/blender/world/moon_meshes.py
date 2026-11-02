"""Moonlit Isle meshes, batch 1.

- The island atlas.
- The marble cliff skirt (gold-trimmed under the lip) that follows the crescent's coast.
- The cloud bank cushioning the island, and the moonstone geode crystals hanging beneath it.
- The Moon Mirror: pool, rim, crescent bridge and lotus dais.
- The Star Well: ring and starfield lining.
- Kit pieces: the Crescent Arch at the arrival and moonstone spires.
"""
import bpy, math, random
import worldlib as W
import moon_island as M
import layout as L
import start_props as SP
import jade_meshes as JM

TAU = 2 * math.pi
oriented = SP.oriented


# ---------- atlas ----------
def _n(u, v, f, seed):
    a = u * TAU
    return W.fbm(math.cos(a) * f + 9, math.sin(a) * f + v * f * 2, seed=seed, octaves=3)


def _ramp(lo, hi, v, n, k=0.04):
    return tuple(max(0.0, min(1.0, lo[i] + (hi[i] - lo[i]) * v + k * n)) for i in range(3))


def marble(u, v):
    vein = max(0.0, 1 - abs(_n(u, v * 0.6, 3, 141) + 0.2 * _n(u, v, 11, 142)) * 10)
    c = _ramp((0.7, 0.71, 0.76), (0.95, 0.95, 0.98), v, _n(u, v, 5, 143), 0.03)
    return tuple(c[i] - vein * (0.18, 0.14, 0.04)[i] for i in range(3))


def moonstone(u, v):
    sheen = 0.5 + 0.5 * math.sin(u * TAU * 2 + v * 6)
    return _ramp((0.42, 0.55, 0.82), (0.86, 0.9, 1.0), v, _n(u, v, 4, 144), 0.05)[:2] + (min(1.0, 0.88 + 0.12 * sheen),)


def gold(u, v):
    return _ramp((0.62, 0.45, 0.14), (1.0, 0.86, 0.48), v, _n(u, v, 7, 145), 0.04)


def porcelain(u, v):
    glaze = v > 0.85
    return (0.25, 0.42, 0.78) if glaze else _ramp((0.86, 0.88, 0.92), (0.99, 0.99, 1.0), v, _n(u, v, 6, 146), 0.02)


def night(u, v):
    star = _n(u, v, 23, 147) > 0.6
    return (0.95, 0.95, 1.0) if star else _ramp((0.04, 0.05, 0.14), (0.12, 0.14, 0.32), v, _n(u, v, 4, 148), 0.04)


def cloud(u, v):
    return _ramp((0.62, 0.64, 0.8), (0.98, 0.98, 1.0), v, _n(u, v, 3, 149), 0.03)


def silver(u, v):
    return _ramp((0.5, 0.53, 0.6), (0.88, 0.9, 0.95), v, _n(u, v, 8, 150), 0.03)


def lunar(u, v):
    return _ramp((0.52, 0.53, 0.58), (0.8, 0.8, 0.84), v, _n(u, v, 9, 151), 0.05)


def pearl(u, v):
    return _ramp((0.82, 0.8, 0.86), (1.0, 0.98, 1.0), v, _n(u, v, 5, 152), 0.04)


def glow(u, v):
    return (0.8, 0.88, 1.0)


def starfield(u, v):
    star = _n(u, v, 31, 153) > 0.55
    return (1.0, 0.96, 0.85) if star else _ramp((0.02, 0.02, 0.07), (0.1, 0.08, 0.26), v, _n(u, v, 5, 154), 0.05)


STRIPS = [(64, marble), (64, moonstone), (48, gold), (48, porcelain), (48, night), (64, cloud), (32, silver), (48, lunar),
          (32, pearl), (16, glow), (48, starfield)]
MARBLE, MOONSTONE, GOLD, PORCELAIN, NIGHT, CLOUD, SILVER, LUNAR, PEARL, GLOW, STARFIELD = range(11)


def ground(x, z):
    return M.height(x, z)[0]


# ---------- the crescent's coast ----------
def coast(offset=1.6, step_deg=3.0):
    """The coastline as a closed loop (x, z): the outer arc of the full-moon disc between the horn
    tips, then the inner arc of the bite back again, pushed `offset` studs outward."""
    bx, bz, br = M.BODY
    cx, cz, cr = M.BITE
    pts = []
    # outer shore: body circle points that are outside the bite
    a = 0.0
    outer = []
    while a < 360:
        t = math.radians(a)
        x, z = bx + math.cos(t) * (br + offset), bz + math.sin(t) * (br + offset)
        if math.hypot(x - cx, z - cz) > cr - offset:
            outer.append((a, x, z))
        a += step_deg
    # order the outer arc from one horn tip around the south to the other
    outer.sort(key=lambda p: (p[0] - 300) % 360)
    pts += [(x, z) for _, x, z in outer]
    # inner shore: bite circle points inside the body, walked back from east horn to west horn
    inner = []
    a = 0.0
    while a < 360:
        t = math.radians(a)
        x, z = cx + math.cos(t) * (cr - offset), cz + math.sin(t) * (cr - offset)
        if math.hypot(x - bx, z - bz) < br + offset:
            inner.append((a, x, z))
        a += step_deg
    inner.sort(key=lambda p: (p[0] - 0) % 360)
    pts += [(x, z) for _, x, z in inner]
    return pts


SKIRT_TOP, SKIRT_BOTTOM = -2.3, -38.0
# the cliff steps inward as it falls: (depth below the island, inset from the coast); deeper since
# the island doubled (2026-11-02)
SKIRT_RINGS = [(SKIRT_TOP, 0.0), (SKIRT_TOP - 0.7, 0.1), (-15.0, 4.0), (-26.0, 7.5), (SKIRT_BOTTOM, 15.0)]


def inward(x, z):
    """Unit direction into the land at a coast point (the edge distance's gradient)."""
    e = 0.5
    gx = M.edge_distance(x + e, z) - M.edge_distance(x - e, z)
    gz = M.edge_distance(x, z + e) - M.edge_distance(x, z - e)
    L_ = math.hypot(gx, gz) or 1
    return gx / L_, gz / L_


def cliff_skirt(coll, mat, bands):
    """Marble cliffs following the coast, stepping inward as they fall, with a gold band just
    under the lip. Each column of the cliff is jittered so the faces break up into facets."""
    mb = W.MeshBuilder()
    loop = coast()
    n = len(loop)
    rnd = random.Random(321)
    rings = []
    for i, (x, z) in enumerate(loop):
        ix, iz = inward(x, z)
        jit = [0.0, 0.0] + [rnd.uniform(-1.0, 1.0) for _ in SKIRT_RINGS[2:]]
        rings.append([(x + ix * (inset + j), y, z + iz * (inset + j)) for (y, inset), j in zip(SKIRT_RINGS, jit)])
    for i in range(n):
        j = (i + 1) % n
        if math.hypot(loop[j][0] - loop[i][0], loop[j][1] - loop[i][1]) > 12:
            continue  # the step between the two arcs at a horn tip
        ix, iz = inward((loop[i][0] + loop[j][0]) / 2, (loop[i][1] + loop[j][1]) / 2)
        u0, u1 = i / n * 6, (i + 1) / n * 6
        for k in range(len(SKIRT_RINGS) - 1):
            band = bands[GOLD] if k == 0 else bands[MARBLE]
            v0, v1 = band
            st = 0.95 if k == 0 else 0.9 - 0.18 * k
            sb = 0.75 if k == 0 else 0.9 - 0.18 * (k + 1)
            pts = [rings[i][k], rings[j][k], rings[j][k + 1], rings[i][k + 1]]
            mb.face(pts, [(u0, v0 + (v1 - v0) * st), (u1, v0 + (v1 - v0) * st), (u1, v0 + (v1 - v0) * sb), (u0, v0 + (v1 - v0) * sb)])
            face = mb.faces[-1]
            P = [mb.verts[q] for q in face]
            if (P[1] - P[0]).cross(P[2] - P[0]).dot(W.rb(-ix, 0, -iz)) < 0:
                face.reverse(); mb.uvs[-1].reverse()
    return mb.object("MI_CliffSkirt", coll, mat)


def cells(spacing):
    out = []
    n = int(140 / spacing) + 1
    for j in range(-n, n + 1):
        for i in range(-n, n + 1):
            x = (i + (0.5 if j % 2 else 0)) * spacing
            z = j * spacing * 0.866
            if M.edge_distance(x, z) > -1.0:
                out.append((x, z))
    return out


def _puff(mb, bands, centre, r, rnd):
    x, y, z = centre
    ph = rnd.uniform(0, TAU)
    mb.lathe([(0.0, y + r * 0.55, 0.95), (r * 0.7, y + r * 0.42, 0.88), (r, y, 0.7), (r * 0.82, y - r * 0.38, 0.45), (0.0, y - r * 0.5, 0.3)],
             8, bands[CLOUD], centre=(x, 0, z), rmod=lambda th, k, ph=ph: 1 + 0.12 * math.sin(3 * th + ph + k), phase=ph,
             cap_top=False, u_repeat=1.0)


def cloud_bank(coll, mat, bands):
    """Clouds the island rests in: a belt hugging the cliff at mid-height, and a softer layer
    beneath the island."""
    mb = W.MeshBuilder()
    rnd = random.Random(301)
    loop = coast(offset=1.0)
    for i in range(0, len(loop), 3):
        x, z = loop[i]
        ix, iz = inward(x, z)
        r = rnd.uniform(7.0, 11.0)
        _puff(mb, bands, (x - ix * r * 0.35, rnd.uniform(-22, -13), z - iz * r * 0.35), r, rnd)
    for x, z in cells(16.0):
        e = M.edge_distance(x, z)
        depth = min(1.0, max(0.0, e) / 30)
        r = rnd.uniform(9.5, 13.0)
        _puff(mb, bands, (x, SKIRT_BOTTOM + 4 - depth * rnd.uniform(3, 8), z), r, rnd)
    return mb.object("MI_CloudBank", coll, mat, smooth=True)


def geode_sites():
    rnd = random.Random(311)
    out = []
    for deg in (100, 125, 150, 172, 70, 48, 90, 20, 200, -20, -160, 135, 60):
        x, z = M.band_point(deg, rnd.uniform(0.4, 0.75))
        out.append((x, z, rnd.uniform(15, 24)))
    return out


def geode(coll, mat, bands, glow_only=False):
    """Moonstone crystals hanging under the cloud bank; every third one glows (separate mesh)."""
    mb = W.MeshBuilder()
    for n, (x, z, size) in enumerate(geode_sites()):
        rnd = random.Random(400 + n)
        for k in range(rnd.randint(4, 6)):
            glows = (k % 3 == 0)
            if glows != glow_only:
                continue
            d = (rnd.uniform(-0.35, 0.35), -1, rnd.uniform(-0.35, 0.35))
            JM.crystal_prism(mb, (x + rnd.uniform(-4, 4), SKIRT_BOTTOM - 6, z + rnd.uniform(-4, 4)), d,
                             size * rnd.uniform(0.5, 1.0), size * rnd.uniform(0.09, 0.14),
                             bands[GLOW] if glow_only else bands[MOONSTONE], n * 10 + k)
    return mb.object("MI_GeodeGlow" if glow_only else "MI_Geode", coll, mat)


def geode_crystals(coll, mat, bands):
    return geode(coll, mat, bands)


def geode_glow(coll, mat, bands):
    return geode(coll, mat, bands, glow_only=True)


# ---------- the Moon Mirror ----------
MX, MZ, MR = M.MIRROR
POOL_Y = 1.45
DAIS_TOP = 2.4


def mirror_pool(coll, mat, bands):
    mb = W.MeshBuilder()
    r = M.MIRROR_POOL_R
    for i in range(40):
        a0, a1 = TAU * i / 40, TAU * (i + 1) / 40
        oriented(mb, [(MX + math.cos(a0) * r, POOL_Y, MZ + math.sin(a0) * r), (MX + math.cos(a1) * r, POOL_Y, MZ + math.sin(a1) * r),
                      (MX, POOL_Y, MZ)], (0, 1, 0), bands[NIGHT], 0.5, [0.6] * 3)
    return mb.object("MI_MirrorPool", coll, mat)


def mirror_rim(coll, mat, bands):
    """A marble rim around the pool with a gold inlay ring, the crescent bridge from the east bank
    toward the centre, and the moonstone lotus dais where the Moon Mirror relic hovers."""
    mb = W.MeshBuilder()
    r = M.MIRROR_POOL_R
    mb.lathe([(r, POOL_Y + 0.5, 0.9), (r + 1.4, POOL_Y + 0.5, 1.0), (r + 1.7, POOL_Y + 0.2, 0.8), (r + 1.7, POOL_Y - 1.4, 0.4)],
             48, bands[MARBLE], centre=(MX, 0, MZ), cap_top=False, u_repeat=3.0)
    mb.lathe([(r, POOL_Y + 0.5, 0.6), (r, POOL_Y - 0.6, 0.3)], 48, bands[MARBLE], centre=(MX, 0, MZ), cap_top=False, u_repeat=3.0)
    for i in range(48):  # gold inlay ring on the rim's top
        a0, a1 = TAU * i / 48, TAU * (i + 1) / 48
        p = lambda rr, a: (MX + math.cos(a) * rr, POOL_Y + 0.52, MZ + math.sin(a) * rr)
        oriented(mb, [p(r + 0.55, a0), p(r + 0.85, a0), p(r + 0.85, a1), p(r + 0.55, a1)], (0, 1, 0), bands[GOLD], 0.5, [1.0] * 4)
    # crescent bridge: an arc of marble slabs curving in from the bank toward the east
    toward = math.atan2(M.JUNCTION[1] - MZ, M.JUNCTION[0] - MX)
    for k in range(7):
        t = k / 6
        rr = r - 0.6 - t * (r - 3.4)
        a = toward + 0.9 * math.sin(t * math.pi * 0.9)
        cxk, czk = MX + math.cos(a) * rr, MZ + math.sin(a) * rr
        mb.box((cxk, POOL_Y + 0.45, czk), (2.2, 0.35, 1.5), bands[MARBLE], yaw=math.pi / 2 - a, u=0.3 + 0.1 * k, top_shade=0.95, side_shade=0.7)
    # the lotus dais
    petals = lambda th, k: 1 - (0.18 if k in (2, 3) else 0.0) * (1 - abs(math.cos(4 * th)) ** 0.5)
    mb.lathe([(1.6, DAIS_TOP, 0.95), (2.6, DAIS_TOP - 0.05, 1.0), (3.1, DAIS_TOP + 0.4, 0.95), (2.9, DAIS_TOP - 0.4, 0.7),
              (2.2, POOL_Y - 1.0, 0.4)], 40, bands[MOONSTONE], centre=(MX, 0, MZ), rmod=petals, cap_top=True, u_repeat=1.0)
    return mb.object("MI_MirrorRim", coll, mat)


# ---------- the Star Well ----------
WX, WZ, WR = M.WELL


def star_well(coll, mat, bands):
    """A marble ring with a gold lip around the shaft; the shaft is lined with a starfield."""
    mb = W.MeshBuilder()
    g = ground(WX + WR, WZ)
    inner, outer = M.WELL_SHAFT_R + 0.2, M.WELL_SHAFT_R + 1.9
    top = g + 1.5
    mb.lathe([(inner, top, 0.95), (outer, top, 0.95), (outer + 0.3, top - 0.3, 0.8), (outer + 0.3, g - 1.5, 0.4)], 24,
             bands[MARBLE], centre=(WX, 0, WZ), cap_top=False, u_repeat=2.0)
    for i in range(24):
        a0, a1 = TAU * i / 24, TAU * (i + 1) / 24
        p = lambda rr, a, y: (WX + math.cos(a) * rr, y, WZ + math.sin(a) * rr)
        oriented(mb, [p(inner, a0, top + 0.02), p(inner + 0.5, a0, top + 0.02), p(inner + 0.5, a1, top + 0.02), p(inner, a1, top + 0.02)],
                 (0, 1, 0), bands[GOLD], 0.5, [1.0] * 4)
    # the shaft's starfield lining, facing inward
    for k in range(6):
        y0, y1 = top - k * (top - M.WELL_FLOOR) / 6, top - (k + 1) * (top - M.WELL_FLOOR) / 6
        for i in range(18):
            a0, a1 = TAU * i / 18, TAU * (i + 1) / 18
            r = M.WELL_SHAFT_R - 0.05
            q = [(WX + math.cos(a0) * r, y0, WZ + math.sin(a0) * r), (WX + math.cos(a1) * r, y0, WZ + math.sin(a1) * r),
                 (WX + math.cos(a1) * r, y1, WZ + math.sin(a1) * r), (WX + math.cos(a0) * r, y1, WZ + math.sin(a0) * r)]
            am = (a0 + a1) / 2
            oriented(mb, q, (-math.cos(am), 0, -math.sin(am)), bands[STARFIELD], (i + 0.5) / 18 * 3, [0.9 - 0.12 * k] * 4)
    return mb.object("MI_StarWell", coll, mat)


# ---------- kit ----------
def moonstone_spire(coll, mat, bands):
    """A tall moonstone obelisk on a gold-collared marble footing (origin at ground centre)."""
    mb = W.MeshBuilder()
    mb.lathe([(1.4, 0.8, 0.9), (1.7, 0.6, 0.85), (1.9, 0.0, 0.7), (1.9, -1.2, 0.4)], 6, bands[MARBLE], cap_top=True, u_repeat=0.0)
    mb.lathe([(1.12, 1.25, 1.0), (1.2, 0.8, 0.8)], 6, bands[GOLD], cap_top=False, u_repeat=0.0)
    JM.crystal_prism(mb, (0, 0.8, 0), (0, 1, 0), 13.0, 1.05, bands[MOONSTONE], 5)
    return mb.object("MI_MoonstoneSpire", coll, mat)


def crescent_slab(mb, bands, r_out, r_in, offset, thick, seg=24):
    """A flat crescent: the disc of radius r_out minus a disc of radius r_in shifted by offset
    along -Z. Top at y=0. Built as a strip between the two arcs."""
    def outer(t):
        a = math.radians(200 + 140 * t)  # from one horn round the back to the other (+Z side is the back)
        return (math.cos(a) * r_out, -math.sin(a) * r_out)
    pts_o, pts_i = [], []
    for k in range(seg + 1):
        t = k / seg
        ox, oz = outer(t)
        pts_o.append((ox, oz))
        # matching point on the inner arc: scaled toward the bite centre
        cx, cz = 0.0, -offset
        dx, dz = ox - cx, oz - cz
        L_ = math.hypot(dx, dz)
        w = math.sin(math.pi * t) ** 0.8  # thickest in the middle, horns taper to points
        pts_i.append((ox - dx / L_ * (r_out - r_in) * w * 0 + (cx + dx / L_ * r_in - ox) * w, oz + (cz + dz / L_ * r_in - oz) * w))
    for k in range(seg):
        a, b, c, d = pts_o[k], pts_o[k + 1], pts_i[k + 1], pts_i[k]
        oriented(mb, [(a[0], 0, a[1]), (b[0], 0, b[1]), (c[0], 0, c[1]), (d[0], 0, d[1])], (0, 1, 0), bands[MARBLE], 0.4, [0.95] * 4)
        for p, q in ((a, b), (c, d)):
            mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            oriented(mb, [(p[0], 0, p[1]), (q[0], 0, q[1]), (q[0], -thick, q[1]), (p[0], -thick, p[1])], (mid[0], 0, mid[1] + offset * 0.5),
                     bands[GOLD] if p is a else bands[MARBLE], 0.4, [0.8, 0.8, 0.5, 0.5])
        oriented(mb, [(a[0], -thick, a[1]), (b[0], -thick, b[1]), (c[0], -thick, c[1]), (d[0], -thick, d[1])], (0, -1, 0), bands[LUNAR], 0.4, [0.3] * 4)


def crescent_arch(coll, mat, bands):
    """The Crescent Arch over the arrival: two moonstone spires 10 studs apart joined by a golden
    crescent arc (origin at ground centre; the path runs along Z)."""
    mb = W.MeshBuilder()
    for side in (-1, 1):
        x = side * 5.0
        mb.lathe([(1.2, 0.8, 0.9), (1.5, 0.6, 0.85), (1.7, 0.0, 0.7), (1.7, -1.2, 0.4)], 6, bands[MARBLE], centre=(x, 0, 0), cap_top=True, u_repeat=0.0)
        JM.crystal_prism(mb, (x, 0.8, 0), (side * -0.06, 1, 0), 10.5, 0.95, bands[MOONSTONE], 7 + side)
    # golden crescent arc: a thick band along a semicircle, thinning toward its ends
    seg = 28
    for k in range(seg):
        t0, t1 = k / seg, (k + 1) / seg
        pts = []
        for t in (t0, t1):
            a = math.pi * t
            w = 0.25 + 0.9 * math.sin(math.pi * t)
            pts.append(((math.cos(a) * 5.0, 9.6 + math.sin(a) * 4.6), w))
        (p0, w0), (p1, w1) = pts
        r0 = math.hypot(p0[0], p0[1] - 9.6) or 1
        r1 = math.hypot(p1[0], p1[1] - 9.6) or 1
        o0 = (p0[0] / r0 * w0, (p0[1] - 9.6) / r0 * w0)
        o1 = (p1[0] / r1 * w1, (p1[1] - 9.6) / r1 * w1)
        quad_front = [(p0[0], p0[1], 0.35), (p1[0], p1[1], 0.35), (p1[0] + o1[0], p1[1] + o1[1], 0.35), (p0[0] + o0[0], p0[1] + o0[1], 0.35)]
        quad_back = [(x, y, -0.35) for x, y, _ in quad_front]
        oriented(mb, quad_front, (0, 0, 1), bands[GOLD], 0.5, [1.0] * 4)
        oriented(mb, quad_back, (0, 0, -1), bands[GOLD], 0.5, [0.85] * 4)
        outer = [(p0[0] + o0[0], p0[1] + o0[1], 0.35), (p1[0] + o1[0], p1[1] + o1[1], 0.35), (p1[0] + o1[0], p1[1] + o1[1], -0.35), (p0[0] + o0[0], p0[1] + o0[1], -0.35)]
        oriented(mb, outer, (o0[0] + o1[0], o0[1] + o1[1], 0), bands[GOLD], 0.5, [0.9] * 4)
        inner = [(p0[0], p0[1], 0.35), (p1[0], p1[1], 0.35), (p1[0], p1[1], -0.35), (p0[0], p0[1], -0.35)]
        oriented(mb, inner, (-(o0[0] + o1[0]), -(o0[1] + o1[1]), 0), bands[GOLD], 0.5, [0.7] * 4)
    return mb.object("MI_CrescentArch", coll, mat)


# ---------- placements ----------
def arch_frame():
    lx, lz, _ = M.LANDING
    a, b = M.PATHS[0][0], M.PATHS[0][1]
    x, z = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    return (x, ground(x, z) - 0.3, z), math.atan2(b[0] - a[0], b[1] - a[1])


def spire_positions():
    out = []
    for deg, frac in ((205, 0.5), (335, 0.5), (215, 0.55), (325, 0.55), (60, 0.85), (120, 0.85)):
        x, z = M.band_point(deg, frac)
        if M.edge_distance(x, z) > 2:
            out.append((x, z))
    return out


def relic_positions():
    return {
        "MoonMirror": (MX, DAIS_TOP + 3.2, MZ),
        "StarWell": (WX, ground(WX + WR, WZ) + 5.0, WZ),
    }


ISLAND_PIECES = [cliff_skirt, cloud_bank, geode_crystals, geode_glow, mirror_pool, mirror_rim, star_well]
KIT_PIECES = [moonstone_spire, crescent_arch]


def build():
    img, bands = W.atlas_image("MoonlitIsle_Atlas", 512, STRIPS)
    mat = W.textured_material("MoonlitIsle_Mat", img)
    root = W.collection(M.NAME)
    island = W.collection("MI_Island", root)
    kit = W.collection("MI_Kit", root)
    W.clear_collection(island); W.clear_collection(kit)
    return [f(island, mat, bands) for f in ISLAND_PIECES], [f(kit, mat, bands) for f in KIT_PIECES], img


def kit_entries():
    arch, arch_yaw = arch_frame()
    return {
        "MI_CrescentArch": [(arch, arch_yaw, 1.0)],
        "MI_MoonstoneSpire": [((x, ground(x, z) - 0.2, z), (k * 1.7) % TAU, 0.9 + 0.12 * (k % 3)) for k, (x, z) in enumerate(spire_positions())],
    }


def write_placements(extra_kit=None, extra_lines=(), path=W.REPO + "/src/worldbuild/Placements/MoonlitIsle.lua"):
    kit = kit_entries()
    for name, entries in (extra_kit or {}).items():
        kit.setdefault(name, []).extend(entries)
    lines = ["-- Generated by tools/blender/world/moon_meshes.py. Do not edit by hand.",
             "-- Island-local Roblox studs. Kit entries place each piece's authored origin.", "return {", "    Kit = {"]
    for name in sorted(kit):
        lines.append("        %s = {" % name)
        for (x, y, z), yaw, scale in kit[name]:
            extra = ", Scale = %.3f" % scale if abs(scale - 1) > 1e-6 else ""
            lines.append("            { Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f%s }," % (x, y, z, yaw, extra))
        lines.append("        },")
    lines.append("    },")
    lines += list(extra_lines)
    lx, lz = M.LANDING[0], M.LANDING[1]
    lines.append("    Checkpoint = Vector3.new(%.2f, %.2f, %.2f)," % (lx, ground(lx, lz) + 0.5, lz))
    lines.append("    Relics = {")
    for rid, (x, y, z) in relic_positions().items():
        lines.append("        %s = Vector3.new(%.2f, %.2f, %.2f)," % (rid, x, y, z))
    lines.append("    },")
    lines.append("    StarWell = { Mouth = Vector3.new(%.2f, %.2f, %.2f), Floor = %.2f, Radius = %.2f }," %
                 (WX, ground(WX + WR, WZ) + 1.5, WZ, M.WELL_FLOOR, M.WELL_SHAFT_R))
    lines += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def export():
    island, kit, img = build()
    out = W.REPO + "/assets/world/MoonlitIsle/"
    W.export_batch(island, out + "MoonlitIsle_Island.fbx", image=img, anchor_name="MI_Anchor")
    W.export_batch(kit, out + "MoonlitIsle_Kit.fbx", anchor_name="MI_KitAnchor")
    write_placements()
    return island + kit
