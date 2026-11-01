"""Jade Grove meshes, batch 1: the island atlas, the faceted jade underside (crystal clusters,
moss curtains, hanging vines), the Elder Jade Tree (root-pillar hollow, buttress roots, branches,
canopy, standing pads and its Qinggong climb) and the Grove Gate.

Island-specific pieces are authored in island-local Roblox studs and exported with an anchor at
the island centre; kit pieces (tree shelf, gate) are authored around their own origin.
"""
import bpy, math, os, random
import worldlib as W
import jade_island as J
import layout as L

TAU = 2 * math.pi


# ---------- atlas ----------
def _n(u, v, f, seed):
    a = u * TAU
    return W.fbm(math.cos(a) * f + 3, math.sin(a) * f + v * f * 2, seed=seed, octaves=3)


def _ramp(lo, hi, v, n, k=0.04):
    return tuple(max(0.0, min(1.0, lo[i] + (hi[i] - lo[i]) * v + k * n)) for i in range(3))


def strata(u, v):
    # v: 0 = deep underside, 1 = cliff top; dark green-grey stone with pale jade veins
    n = _n(u, v, 3, 61)
    if v > 0.9:  # the cliff top under the grass lip: dark moss, so it never reads as a pale ledge
        return _ramp((0.14, 0.22, 0.1), (0.2, 0.3, 0.14), (v - 0.9) * 10, n, 0.04)
    c = _ramp((0.12, 0.16, 0.15), (0.34, 0.42, 0.37), v, n, 0.05)
    vein = max(0.0, 1 - abs(_n(u, v * 0.5, 3, 62)) * 14)
    return tuple(min(1.0, c[i] + vein * (0.14, 0.26, 0.18)[i]) for i in range(3))


def jade(u, v):
    n = _n(u, v, 4, 63)
    cloud = max(0.0, _n(u, v, 9, 64))
    c = _ramp((0.06, 0.36, 0.26), (0.52, 0.9, 0.7), v, n, 0.06)
    return tuple(min(1.0, c[i] + 0.15 * cloud) for i in range(3))


def moss(u, v):
    return _ramp((0.12, 0.26, 0.1), (0.38, 0.6, 0.24), v, _n(u, v, 8, 65), 0.06)


def bark(u, v):
    fissure = abs(math.sin(u * TAU * 9 + 2.5 * _n(u, v * 0.2, 2, 66)))
    lichen = max(0.0, _n(u, v, 5, 67) - 0.35) * 1.2
    c = _ramp((0.2, 0.17, 0.14), (0.44, 0.39, 0.32), v * (0.55 + 0.45 * fissure), _n(u, v, 6, 68), 0.04)
    return tuple(c[i] * (1 - lichen) + (0.36, 0.44, 0.32)[i] * lichen for i in range(3))


def leaf(u, v):
    n = _n(u, v, 7, 69)
    return _ramp((0.08, 0.26, 0.14), (0.42, 0.66, 0.3), v, n, 0.06)


def stone(u, v):
    n = _n(u, v, 6, 70)
    grain = _n(u, v, 17, 75)
    c = _ramp((0.28, 0.29, 0.26), (0.55, 0.55, 0.5), v, n + 0.6 * grain, 0.07)
    if _n(u, v, 12, 71) > 0.55:  # sparse moss flecks
        return (0.3, 0.46, 0.22)
    return c


def gold(u, v):
    return _ramp((0.5, 0.36, 0.12), (0.95, 0.8, 0.42), v, _n(u, v, 7, 72), 0.04)


def bamboo(u, v):
    node = abs(math.sin(v * math.pi * 6)) < 0.08
    c = _ramp((0.3, 0.42, 0.14), (0.66, 0.78, 0.36), u, _n(u, v, 5, 73), 0.03)
    return tuple(x * 0.7 for x in c) if node else c


FLOWER_COLOURS = [(0.97, 0.95, 0.9), (0.95, 0.58, 0.72), (0.7, 0.58, 0.92), (0.98, 0.84, 0.36), (0.3, 0.56, 0.26)]


def flowers(u, v):
    c = FLOWER_COLOURS[min(4, int(u * 5))]
    return tuple(c[i] * (0.7 + 0.3 * v) for i in range(3))


def soil(u, v):
    return _ramp((0.14, 0.1, 0.07), (0.34, 0.26, 0.18), v, _n(u, v, 9, 74), 0.04)


def glow(u, v):
    return (0.85, 1.0, 0.9)


STRIPS = [(96, strata), (48, jade), (48, moss), (64, bark), (64, leaf), (48, stone), (32, gold), (32, bamboo),
          (32, flowers), (32, soil), (16, glow)]
STRATA, JADE, MOSS, BARK, LEAF, STONE, GOLD, BAMBOO, FLOWERS, SOIL, GLOW = range(11)


def flower_u(k):
    return (k + 0.5) / 5


# ---------- shared helpers ----------
def oriented(mb, pts, want, band, u=0.5, shade=None):
    import start_props
    start_props.oriented(mb, pts, want, band, u, shade)


def ground(x, z):
    return J.height(x, z)[0]


# ---------- underside: a faceted jade mass ----------
# (radius scale relative to the rim, y) from the cliff top down to the tip
BODY = [(1.0, -3.2), (1.03, -7.0), (1.0, -14.0), (0.93, -21.0), (0.8, -32.0), (0.63, -45.0), (0.45, -58.0),
        (0.28, -70.0), (0.12, -80.0)]
TIP = (6.0, -88.0, -4.0)   # x, y, z of the lowest point
BODY_SEG = 22


def body(coll, mat, bands):
    mb = W.MeshBuilder()
    rnd = random.Random(81)
    v0, v1 = bands[STRATA]
    rings = []
    for k, (s, y) in enumerate(BODY):
        twist = rnd.uniform(-0.12, 0.12)
        ring = []
        for i in range(BODY_SEG):
            th = TAU * (i + (0.5 if k % 2 else 0.0)) / BODY_SEG + twist
            R = J.rim(th)
            # the cliff band hugs the terrain edge; facets get bolder further down
            jitter = 1 + (0.0 if k == 0 else 0.03 if k < 3 else 0.13) * (rnd.random() - 0.5) * 2
            r = (R + 1.6) * min(s, 1.0) * jitter if k < 3 else R * s * jitter
            yy = y + (0 if k < 2 else rnd.uniform(-3.0, 3.0))
            cx = TIP[0] * (1 - s); cz = TIP[2] * (1 - s)
            ring.append((cx + math.cos(th) * r, yy, cz + math.sin(th) * r))
        rings.append(ring)
    depth = lambda y: (y - TIP[1]) / (-3.2 - TIP[1])
    for k in range(len(rings) - 1):
        for i in range(BODY_SEG):
            j = (i + 1) % BODY_SEG
            a, b, c, d = rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]
            u = (i + 0.5) / BODY_SEG * 2
            for tri in ((a, b, c), (a, c, d)):  # triangles: faceted, never bent quads
                mid = [sum(p[q] for p in tri) / 3 for q in range(3)]
                oriented(mb, list(tri), (mid[0] - TIP[0] * 0.5, 0.15, mid[2] - TIP[2] * 0.5), bands[STRATA], u,
                         [0.15 + 0.8 * depth(p[1]) for p in tri])
    for i in range(BODY_SEG):
        j = (i + 1) % BODY_SEG
        oriented(mb, [rings[-1][i], rings[-1][j], TIP], (0, -1, 0), bands[STRATA], 0.5, [0.1, 0.1, 0.05])
    return mb.object("JG_Underside", coll, mat)


CRYSTAL_SITES = [(-30, -40, 24, 10), (34, -46, -30, 12), (10, -60, 34, 14), (-34, -30, -38, 9), (40, -34, 26, 10),
                 (-6, -74, -14, 15)]


def crystal_prism(mb, base, direction, length, radius, band, seed):
    """A hexagonal crystal with a pointed tip, growing from `base` along `direction`."""
    d = W.Vector(direction).normalized()
    ref = W.Vector((0, 1, 0)) if abs(d.y) < 0.9 else W.Vector((1, 0, 0))
    a = d.cross(ref).normalized(); b = d.cross(a)
    base = W.Vector(base)
    shoulder = base + d * length * 0.78
    tip = base + d * length
    ring0 = [tuple(base + (a * math.cos(TAU * k / 6) + b * math.sin(TAU * k / 6)) * radius) for k in range(6)]
    ring1 = [tuple(shoulder + (a * math.cos(TAU * k / 6) + b * math.sin(TAU * k / 6)) * radius * 0.92) for k in range(6)]
    for k in range(6):
        j = (k + 1) % 6
        out = tuple((a * math.cos(TAU * (k + 0.5) / 6) + b * math.sin(TAU * (k + 0.5) / 6)))
        oriented(mb, [ring0[k], ring0[j], ring1[j], ring1[k]], out, band, (k + 0.5) / 6, [0.35, 0.35, 0.8, 0.8])
        oriented(mb, [ring1[k], ring1[j], tuple(tip)], tuple(W.Vector(out) + d), band, (k + 0.5) / 6, [0.8, 0.8, 1.0])


def under_crystals(coll, mat, bands):
    mb = W.MeshBuilder()
    for n, (x, y, z, size) in enumerate(CRYSTAL_SITES):
        rnd = random.Random(90 + n)
        out = W.Vector((x, 0, z)).normalized()
        for k in range(rnd.randint(3, 5)):
            d = (out * rnd.uniform(0.2, 0.7) + W.Vector((rnd.uniform(-0.3, 0.3), -1, rnd.uniform(-0.3, 0.3))))
            length = size * rnd.uniform(0.55, 1.0)
            radius = size * rnd.uniform(0.1, 0.17)
            base = (x + rnd.uniform(-2, 2), y + 3, z + rnd.uniform(-2, 2))
            crystal_prism(mb, base, tuple(d), length, radius, bands[JADE], n * 10 + k)
    return mb.object("JG_UnderCrystals", coll, mat)


def moss_curtains(coll, mat, bands):
    """Ragged moss hanging from the cliff top, following the outline just outside the cliff face."""
    mb = W.MeshBuilder()
    rnd = random.Random(77)
    v0, v1 = bands[MOSS]
    for start in range(0, 360, 26):
        if rnd.random() < 0.35:
            continue
        span = rnd.uniform(8, 16)
        cols = []
        steps = 7
        for s in range(steps + 1):
            th = math.radians(start + span * s / steps)
            R = J.rim(th) + 2.0
            drop = rnd.uniform(6, 14) * (0.6 + 0.4 * math.sin(math.pi * s / steps))
            cols.append(((math.cos(th) * R, -2.6, math.sin(th) * R), (math.cos(th) * (R - 0.4), -2.6 - drop, math.sin(th) * (R - 0.4)), th))
        for s in range(steps):
            (t0, b0, th0), (t1, b1, th1) = cols[s], cols[s + 1]
            out = (math.cos((th0 + th1) / 2), 0, math.sin((th0 + th1) / 2))
            oriented(mb, [t0, t1, b1, b0], out, bands[MOSS], rnd.random(), [0.85, 0.85, 0.3, 0.3])
    return mb.object("JG_MossCurtains", coll, mat)


def vines(coll, mat, bands):
    mb = W.MeshBuilder()
    rnd = random.Random(55)
    for k in range(16):
        th = TAU * k / 16 + rnd.uniform(-0.12, 0.12)
        R = J.rim(th) + 1.4
        x, z = math.cos(th) * R, math.sin(th) * R
        length = rnd.uniform(10, 26)
        sway = rnd.uniform(-2, 2)
        pts = [(x, -2.4, z), (x * 1.01 + sway * 0.4, -2.4 - length * 0.4, z * 1.01), (x * 1.02 + sway, -2.4 - length, z * 1.02)]
        curve = W.mb_tube(mb, pts, lambda t: 0.28 - 0.12 * t, 4, bands[LEAF], per=4)
        for i in range(2, len(curve), 2):  # leaf pairs along the vine
            c = curve[i]
            for side in (-1, 1):
                a = th + side * 1.2 + rnd.uniform(-0.3, 0.3)
                tip = (c.x + math.cos(a) * 0.9, c.y - 0.3, c.z + math.sin(a) * 0.9)
                p0 = (c.x, c.y + 0.25, c.z); p1 = (c.x, c.y - 0.25, c.z)
                for tri in ([p0, p1, tip], [p1, p0, tip]):
                    mb.face(tri, [(rnd.random(), bands[LEAF][0] + (bands[LEAF][1] - bands[LEAF][0]) * s) for s in (0.7, 0.5, 0.95)])
    return mb.object("JG_Vines", coll, mat)


# ---------- the Elder Jade Tree ----------
EX, EZ = J.ELDER[0], J.ELDER[1]
PILLAR_RING, PILLAR_R, TRUNK_BASE = 6.0, 3.3, 12.0


def elder_base():
    return ground(EX, EZ) - 0.5


def trunk_radius(h):
    """Trunk radius at height h above the tree's base."""
    if h <= TRUNK_BASE:
        return 9.0
    if h <= 40:
        return 9.0 - 5.0 * (h - TRUNK_BASE) / (40 - TRUNK_BASE)
    return max(1.6, 4.0 - 2.4 * (h - 40) / 18)


def trunk_axis(h):
    """Gentle lean and twist of the trunk axis."""
    t = h / 60
    return (EX + 2.5 * math.sin(t * 2.2) * t, EZ - 1.8 * t * t)


def elder_trunk(coll, mat, bands):
    mb = W.MeshBuilder()
    rnd = random.Random(13)
    y0 = elder_base()
    B = bands[BARK]
    # three root pillars around a walk-in hollow (entrances west, south-east, north-east)
    for k, ang in enumerate((0.0, TAU / 3, 2 * TAU / 3)):
        cx, cz = EX + math.cos(ang) * PILLAR_RING, EZ + math.sin(ang) * PILLAR_RING
        foot = (EX + math.cos(ang) * (PILLAR_RING + 4.5), y0 - 2.0, EZ + math.sin(ang) * (PILLAR_RING + 4.5))
        W.mb_tube(mb, [foot, (cx, y0 + 4, cz), (cx * 0.9 + EX * 0.1, y0 + TRUNK_BASE + 1.5, cz * 0.9 + EZ * 0.1)],
                  lambda t: 4.6 - 1.0 * t, 10, B, per=4)
    # the trunk: a lofted, slightly lumpy column from the pillar tops to the crown
    rings, heights = [], [TRUNK_BASE + 0.5 + 3.4 * k for k in range(14)] + [58.0]
    for h in heights:
        ax, az = trunk_axis(h)
        r = trunk_radius(h)
        rings.append([(ax + math.cos(TAU * i / 14) * r * (1 + 0.07 * math.sin(i * 2.3 + h * 0.2)), y0 + h,
                       az + math.sin(TAU * i / 14) * r * (1 + 0.07 * math.sin(i * 2.3 + h * 0.2))) for i in range(14)])
    for k in range(len(rings) - 1):
        for i in range(14):
            j = (i + 1) % 14
            out = (math.cos(TAU * (i + 0.5) / 14), 0, math.sin(TAU * (i + 0.5) / 14))
            oriented(mb, [rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]], out, B, (i + 0.5) / 14 * 2,
                     [0.5 + 0.4 * (k / len(rings))] * 4)
    # the hollow's ceiling (the underside of the trunk, seen from inside)
    ax, az = trunk_axis(heights[0])
    for i in range(14):
        oriented(mb, [rings[0][i], rings[0][(i + 1) % 14], (ax, y0 + heights[0] + 1.2, az)], (0, -1, 0), bands[SOIL], 0.5,
                 [0.3, 0.3, 0.1])
    top = rings[-1]
    ax, az = trunk_axis(58)
    for i in range(14):
        oriented(mb, [top[i], top[(i + 1) % 14], (ax, y0 + 58.6, az)], (0, 1, 0), B, 0.5, [0.8] * 3)
    # buttress roots: two arch high enough to walk under (west path, east path), the rest hug the ground
    for k, (ang, reach, arch, thick) in enumerate(((math.pi - 0.5, 20, 9.0, 2.6), (0.25, 17, 1.6, 3.4), (1.0, 15, 1.2, 3.6),
                                                  (1.9, 16, 1.4, 3.4), (2.6, 14, 1.0, 3.2), (-0.8, 16, 1.5, 3.6),
                                                  (-1.7, 15, 1.2, 3.4), (-2.6, 14, 1.0, 3.0))):
        sx, sz = EX + math.cos(ang) * 8.0, EZ + math.sin(ang) * 8.0
        ex_, ez_ = EX + math.cos(ang) * reach, EZ + math.sin(ang) * reach
        mx, mz = sx * 0.55 + ex_ * 0.45, sz * 0.55 + ez_ * 0.45
        pts = [(sx, y0 + 5 + arch * 0.5, sz), (mx, y0 + arch + 1.5, mz), (ex_, ground(ex_, ez_) - 2.0, ez_)]
        W.mb_tube(mb, pts, lambda t, th=thick: th - (th - 0.9) * t, 9, B, per=5)
    return mb.object("JG_ElderTrunk", coll, mat)


BRANCHES = [  # angle, height on trunk, reach, rise
    (0.4, 30, 18, 8), (2.1, 34, 20, 9), (3.6, 38, 17, 10), (4.9, 42, 16, 9), (1.3, 46, 14, 9),
]


def branch_end(angle, height, reach, rise):
    ax, az = trunk_axis(height)
    return (ax + math.cos(angle) * reach, elder_base() + height + rise, az + math.sin(angle) * reach)


def elder_branches(coll, mat, bands):
    mb = W.MeshBuilder()
    y0 = elder_base()
    for ang, h, reach, rise in BRANCHES:
        ax, az = trunk_axis(h)
        r0 = trunk_radius(h) * 0.8
        start = (ax + math.cos(ang) * r0 * 0.5, y0 + h, az + math.sin(ang) * r0 * 0.5)
        mid = (ax + math.cos(ang) * reach * 0.55, y0 + h + rise * 0.3, az + math.sin(ang) * reach * 0.55)
        W.mb_tube(mb, [start, mid, branch_end(ang, h, reach, rise)], lambda t: 2.4 - 1.5 * t, 8, bands[BARK], per=5)
    return mb.object("JG_ElderBranches", coll, mat)


def pad_disc(mb, centre, r, band, seed, thick=1.0):
    rnd = random.Random(seed)
    ph = rnd.uniform(0, TAU)
    mb.lathe([(r * 0.6, thick, 1.0), (r, thick * 0.4, 0.85), (r * 0.95, -thick * 0.3, 0.55), (r * 0.5, -thick * 0.8, 0.35)],
             12, band, centre=centre, rmod=lambda th, k: 1 + 0.1 * math.sin(5 * th + ph), phase=ph, cap_top=True,
             cap_bottom=True, u_repeat=0.0)


CROWN_PAD = 58.6  # height of the crown nest's floor above the tree base


PAD_R, CROWN_R = 7.5, 8.5


def cloud_tier(mb, centre, r, band, seed):
    """A broad, flat-topped leaf cloud: the walkable canopy tiers of the Elder Tree."""
    rnd = random.Random(seed)
    ph = rnd.uniform(0, TAU)
    lobes = rnd.choice((5, 6, 7))
    mb.lathe([(r * 0.7, 0.0, 1.0), (r * 0.95, -0.4, 0.92), (r, -1.3, 0.7), (r * 0.88, -2.4, 0.42), (r * 0.5, -3.0, 0.25)],
             16, band, centre=centre, rmod=lambda th, k: 1 + 0.11 * math.sin(lobes * th + ph) * (1 if k else 0.6),
             phase=ph, cap_top=True, cap_bottom=True, u_repeat=1.0)


def elder_pads(coll, mat, bands):
    """Standing platforms (flat tops at the listed heights): a leaf-cloud tier on every branch end
    and the crown nest on top of the trunk."""
    mb = W.MeshBuilder()
    for k, b in enumerate(BRANCHES):
        x, y, z = branch_end(*b)
        cloud_tier(mb, (x, y + 1.2, z), PAD_R, bands[LEAF], 300 + k)
    ax, az = trunk_axis(58)
    cloud_tier(mb, (ax, elder_base() + CROWN_PAD, az), CROWN_R, bands[LEAF], 399)
    return mb.object("JG_ElderPads", coll, mat)


def elder_canopy(coll, mat, bands):
    """Leaf masses (no collision): clusters around each branch end and a ring around the crown nest."""
    mb = W.MeshBuilder()
    rnd = random.Random(31)
    clusters = []
    for b in BRANCHES:  # masses hanging under and beside each tier, never above its walkable top
        x, y, z = branch_end(*b)
        for k in range(4):
            a = b[0] + rnd.uniform(-1.6, 1.6)
            d = rnd.uniform(4.0, 7.5)
            clusters.append(((x + math.cos(a) * d, y + rnd.uniform(-3.5, -1.0), z + math.sin(a) * d), rnd.uniform(3.4, 4.8)))
    ax, az = trunk_axis(58)
    for k in range(8):
        a = TAU * k / 8 + rnd.uniform(-0.2, 0.2)
        clusters.append(((ax + math.cos(a) * 8.0, elder_base() + CROWN_PAD - rnd.uniform(2.0, 4.0), az + math.sin(a) * 8.0),
                         rnd.uniform(3.6, 4.8)))
    for n, (c, r) in enumerate(clusters):
        prnd = random.Random(500 + n)
        ph = prnd.uniform(0, TAU)
        mb.lathe([(0.0, r * 0.8, 0.95), (r * 0.7, r * 0.6, 0.85), (r, 0.0, 0.62), (r * 0.8, -r * 0.42, 0.35), (0.0, -r * 0.55, 0.2)],
                 9, bands[LEAF], centre=c, rmod=lambda th, k, ph=ph: 1 + 0.12 * math.sin(3 * th + ph + k), phase=ph,
                 cap_top=False, u_repeat=1.0)
    return mb.object("JG_ElderCanopy", coll, mat)


def climb_shelves():
    """Bracket-fungus shelves spiralling up the trunk from the knoll to the first branch pad
    (island-local positions of each shelf's walkable top centre, and its yaw)."""
    out = []
    y0 = elder_base()
    for k, (h, ang) in enumerate(((13, 2.6), (22, 3.9), (30.5, 5.0), (38, 0.0))):
        ax, az = trunk_axis(h)
        r = trunk_radius(h) + 0.3
        out.append(((ax + math.cos(ang) * r, y0 + h, az + math.sin(ang) * r), -ang))
    return out


def tree_shelf(coll, mat, bands, name="JG_TreeShelf"):
    """A jade-edged bracket fungus, flat top at the origin, opening toward +X."""
    mb = W.MeshBuilder()
    seg = 16
    top, rim_, low = [], [], []
    for i in range(seg):
        a = math.pi * i / (seg - 1) - math.pi / 2
        x, z = math.cos(a) * 5.5, math.sin(a) * 4.5
        top.append((x, 0.0, z)); rim_.append((x * 1.06, -0.6, z * 1.06)); low.append((x * 0.5 - 0.6, -2.4, z * 0.5))
    centre, back = (0.3, 0.0, 0.0), (-1.4, -2.8, 0.0)
    for i in range(seg - 1):
        oriented(mb, [top[i], top[i + 1], centre], (0, 1, 0), bands[MOSS], 0.4, [0.9] * 3)
        oriented(mb, [top[i], top[i + 1], rim_[i + 1], rim_[i]], (top[i][0], 0.2, top[i][2]), bands[JADE], 0.5, [0.9, 0.9, 0.7, 0.7])
        oriented(mb, [rim_[i], rim_[i + 1], low[i + 1], low[i]], (top[i][0], -0.5, top[i][2]), bands[STONE], 0.5, [0.6, 0.6, 0.3, 0.3])
        oriented(mb, [low[i], low[i + 1], back], (0, -1, 0), bands[STONE], 0.5, [0.25] * 3)
    oriented(mb, [top[0], top[-1], centre], (0, 1, 0), bands[MOSS], 0.4, [0.9] * 3)
    return mb.object(name, coll, mat)


# ---------- kit: the Grove Gate ----------
GATE_HOLE, GATE_HALF_W, GATE_H, GATE_T = 5.2, 8.0, 12.0, 0.8
GATE_CY = 5.0


def _rect_hit(dx, dy):
    """Distance along (dx, dy) from the hole centre to the gate panel's rectangle boundary."""
    ts = []
    if dx > 1e-6: ts.append(GATE_HALF_W / dx)
    if dx < -1e-6: ts.append(-GATE_HALF_W / dx)
    if dy > 1e-6: ts.append((GATE_H - GATE_CY) / dy)
    if dy < -1e-6: ts.append(-GATE_CY / dy)
    return min(ts)


def grove_gate(coll, mat, bands):
    """A moon gate: a stone panel with a round opening ringed in jade, flanking walls and a tiled
    cap. Origin at the ground centre of the opening; the gate faces +Z / -Z."""
    mb = W.MeshBuilder()
    seg = 32
    P, D = bands[STONE], bands[STRATA]
    for side in (1, -1):
        z = side * GATE_T
        for i in range(seg):
            a0, a1 = TAU * i / seg, TAU * (i + 1) / seg
            pts = []
            for a in (a0, a1):
                dx, dy = math.cos(a), math.sin(a)
                hx, hy = dx * GATE_HOLE, max(-GATE_CY, dy * GATE_HOLE)
                t = _rect_hit(dx, dy)
                pts.append(((hx, GATE_CY + hy), (dx * t, GATE_CY + dy * t)))
            (h0, r0), (h1, r1) = pts
            quad = [(h0[0], h0[1], z), (h1[0], h1[1], z), (r1[0], r1[1], z), (r0[0], r0[1], z)]
            if abs(r0[1] - h0[1]) + abs(r1[1] - h1[1]) + abs(r0[0] - h0[0]) + abs(r1[0] - h1[0]) > 1e-3:
                oriented(mb, quad, (0, 0, side), P, 0.3 + 0.4 * (i / seg), [0.85] * 4)
        # jade ring band around the opening, standing proud of the panel
        for i in range(seg):
            a0, a1 = TAU * i / seg, TAU * (i + 1) / seg
            if math.sin(a0) * GATE_HOLE < -GATE_CY + 0.01 and math.sin(a1) * GATE_HOLE < -GATE_CY + 0.01:
                continue
            ring = [(math.cos(a) * r, GATE_CY + max(-GATE_CY, math.sin(a) * r), z + side * 0.18) for a, r in
                    ((a0, GATE_HOLE), (a0, GATE_HOLE + 0.8), (a1, GATE_HOLE + 0.8), (a1, GATE_HOLE))]
            oriented(mb, ring, (0, 0, side), bands[JADE], (i + 0.5) / seg, [0.95] * 4)
    # the opening's inner surface
    for i in range(seg):
        a0, a1 = TAU * i / seg, TAU * (i + 1) / seg
        p = lambda a, z: (math.cos(a) * GATE_HOLE, GATE_CY + max(-GATE_CY, math.sin(a) * GATE_HOLE), z)
        q = [p(a0, GATE_T), p(a1, GATE_T), p(a1, -GATE_T), p(a0, -GATE_T)]
        am = (a0 + a1) / 2
        oriented(mb, q, (-math.cos(am), -math.sin(am), 0), P, 0.5, [0.55] * 4)
    # panel edges
    for x in (-GATE_HALF_W, GATE_HALF_W):
        oriented(mb, [(x, 0, GATE_T), (x, GATE_H, GATE_T), (x, GATE_H, -GATE_T), (x, 0, -GATE_T)], (x, 0, 0), P, 0.5, [0.6] * 4)
    # flanking walls, the cap and its tiled roof
    for sx in (-1, 1):
        mb.box((sx * 11.5, 4.0, 0), (7.0, 8.0 + 2, 2 * GATE_T * 0.9), P, u=0.6, top_shade=0.8, side_shade=0.7)
        mb.box((sx * 11.5, 9.4, 0), (7.6, 0.8, 2.6), D, u=0.4, top_shade=0.7, side_shade=0.5)
    mb.box((0, GATE_H + 0.4, 0), (2 * GATE_HALF_W + 1.4, 0.8, 3.0), D, u=0.4, top_shade=0.7, side_shade=0.5)
    ridge = [(-GATE_HALF_W - 0.7, GATE_H + 0.8), (GATE_HALF_W + 0.7, GATE_H + 0.8)]
    for side in (1, -1):
        oriented(mb, [(ridge[0][0], ridge[0][1], side * 1.5), (ridge[1][0], ridge[1][1], side * 1.5),
                      (ridge[1][0] - 0.6, GATE_H + 2.4, 0), (ridge[0][0] + 0.6, GATE_H + 2.4, 0)], (0, 1, side), D, 0.3, [0.6, 0.6, 0.85, 0.85])
    for sx in (-1, 1):
        x = sx * (GATE_HALF_W + 0.7)
        oriented(mb, [(x, GATE_H + 0.8, 1.5), (x - sx * 0.6, GATE_H + 2.4, 0), (x, GATE_H + 0.8, -1.5)], (sx, 0, 0), D, 0.3, [0.6] * 3)
    # a jade emblem disc over the opening
    import start_props as SP
    SP.disc_z(mb, (0, GATE_H - 1.2, GATE_T + 0.05), 0.0, 0.7, 12, bands[JADE])
    SP.disc_z(mb, (0, GATE_H - 1.2, -GATE_T - 0.05), 0.0, 0.7, 12, bands[JADE], yaw=math.pi)
    return mb.object("JG_GroveGate", coll, mat)


# ---------- placements ----------
def gate_yaw():
    """Turn the gate so its opening faces the arriving player (along the arrival -> gate line)."""
    dx, dz = J.GATE[0] - J.LANDING[0], J.GATE[1] - J.LANDING[1]
    return math.atan2(dx, dz)


ISLAND_PIECES = [body, under_crystals, moss_curtains, vines, elder_trunk, elder_branches, elder_pads, elder_canopy]
KIT_PIECES = [tree_shelf, grove_gate]


def build():
    img, bands = W.atlas_image("JadeGrove_Atlas", 512, STRIPS)
    mat = W.textured_material("JadeGrove_Mat", img)
    root = W.collection(J.NAME)
    island = W.collection("JG_Island", root)
    kit = W.collection("JG_Kit", root)
    W.clear_collection(island); W.clear_collection(kit)
    return [f(island, mat, bands) for f in ISLAND_PIECES], [f(kit, mat, bands) for f in KIT_PIECES], img


def relic_positions():
    """Island-local positions of the three Jade Grove relics."""
    y0 = elder_base()
    ax, az = trunk_axis(58)
    px, pz, pr = J.HOLLOW_POOL
    return {
        "GroveHeart": (EX, y0 + 3.0, EZ),                                # inside the Elder Tree's hollow
        "JadeSeed": (ax, y0 + CROWN_PAD + 3.0, az),                       # in the crown nest
        "WhisperingSpring": (px - pr - 2.5, J.POOL_WATER + 3.0, pz + 2.0),  # on the hollow's spring bank
    }


def write_placements(path=W.REPO + "/src/worldbuild/Placements/JadeGrove.lua"):
    kit = {"JG_TreeShelf": [(pos, yaw, 1.0) for pos, yaw in climb_shelves()],
           "JG_GroveGate": [((J.GATE[0], ground(*J.GATE) - 0.3, J.GATE[1]), gate_yaw(), 1.0)]}
    lines = ["-- Generated by tools/blender/world/jade_meshes.py. Do not edit by hand.",
             "-- Island-local Roblox studs. Kit entries place each piece's authored origin.", "return {", "    Kit = {"]
    for name in sorted(kit):
        lines.append("        %s = {" % name)
        for (x, y, z), yaw, scale in kit[name]:
            lines.append("            { Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f }," % (x, y, z, yaw))
        lines.append("        },")
    lines.append("    },")
    lx, lz = J.LANDING[0], J.LANDING[1]
    lines.append("    Checkpoint = Vector3.new(%.2f, %.2f, %.2f)," % (lx, ground(lx, lz) + 0.5, lz))
    lines.append("    Relics = {")
    for rid, (x, y, z) in relic_positions().items():
        lines.append('        %s = Vector3.new(%.2f, %.2f, %.2f),' % (rid, x, y, z))
    lines.append("    },")
    lines += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def export():
    island, kit, img = build()
    out = W.REPO + "/assets/world/JadeGrove/"
    W.export_batch(island, out + "JadeGrove_Island.fbx", image=img, anchor_name="JG_Anchor")
    W.export_batch(kit, out + "JadeGrove_Kit.fbx", anchor_name="JG_KitAnchor")
    write_placements()
    return island + kit
