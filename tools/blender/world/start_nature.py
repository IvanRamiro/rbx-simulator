"""Starting Island nature: spirit pines with cloud-pad canopies, plum-blossom trees, mossy
boulders and flower clumps, plus their placement (hero pieces and a seeded scatter that keeps
paths, landmarks and the rim clear). Uses the prop atlas from start_props."""
import bpy, bmesh, math, random
import worldlib as W
import start_island as S
import start_props as P

TAU = 2 * math.pi


# ---------- trees ----------
def cloud_pad(mb, centre, r, thick, seed, band):
    """A flattened, scalloped canopy pad (Huangshan pine foliage layer)."""
    rnd = random.Random(seed)
    ph = rnd.uniform(0, TAU)
    lobes = rnd.choice((5, 6, 7))
    rmod = lambda th, k: 1 + 0.13 * math.sin(lobes * th + ph) * (1 if k in (1, 2, 3) else 0.5)
    mb.lathe([(r * 0.55, thick * 1.0, 1.0), (r * 0.9, thick * 0.75, 0.92), (r, thick * 0.25, 0.75), (r * 0.92, -thick * 0.2, 0.5),
              (r * 0.5, -thick * 0.45, 0.32)], 14, band, centre=centre, rmod=rmod, phase=ph, cap_top=True, cap_bottom=True, u_repeat=0.0)


def spirit_pine(name, coll, mat, bands, seed):
    rnd = random.Random(seed)
    mb = W.MeshBuilder()
    lean = rnd.uniform(0, TAU)
    lx, lz = math.cos(lean), math.sin(lean)
    height = rnd.uniform(13, 16)
    trunk = [(0, -1.2, 0)]
    for k, t in enumerate((0.28, 0.55, 0.8, 1.0)):
        wig = rnd.uniform(-1.0, 1.0)
        trunk.append((lx * t * 3.2 + -lz * wig, height * t, lz * t * 3.2 + lx * wig))
    curve = W.mb_tube(mb, trunk, lambda t: 1.15 - 0.8 * t, 7, bands[P.BARK], per=5)
    # branches from the upper trunk, each ending in a pad; the crown pad caps the trunk
    pads = [(curve[-1], rnd.uniform(3.6, 4.4))]
    used = []
    for b in range(rnd.choice((3, 4))):
        idx = int(len(curve) * rnd.uniform(0.5, 0.85))
        base = curve[idx]
        ang = rnd.uniform(0, TAU)
        while any(abs((ang - u + math.pi) % TAU - math.pi) < 1.2 for u in used):
            ang = rnd.uniform(0, TAU)
        used.append(ang)
        reach = rnd.uniform(3.5, 5.5)
        ax, az = math.cos(ang), math.sin(ang)
        mid = (base.x + ax * reach * 0.5, base.y - 0.6, base.z + az * reach * 0.5)
        end = (base.x + ax * reach, base.y + 0.7, base.z + az * reach)
        W.mb_tube(mb, [tuple(base), mid, end], lambda t: 0.45 - 0.25 * t, 5, bands[P.BARK], per=4)
        pads.append((W.Vector(end), rnd.uniform(2.6, 3.4)))
    for k, (c, r) in enumerate(pads):
        cloud_pad(mb, (c.x, c.y + 0.6, c.z), r, 1.0, seed * 7 + k, bands[P.PINE])
    return mb.object(name, coll, mat)


def blossom_tree(name, coll, mat, bands, seed):
    rnd = random.Random(seed)
    mb = W.MeshBuilder()
    fork = (rnd.uniform(-0.6, 0.6), rnd.uniform(3.6, 4.4), rnd.uniform(-0.6, 0.6))
    W.mb_tube(mb, [(0, -1.0, 0), (0.3, 1.8, -0.2), fork], lambda t: 0.95 - 0.35 * t, 7, bands[P.BARK], per=4)
    puffs = []
    for b in range(3):
        ang = TAU * b / 3 + rnd.uniform(-0.4, 0.4)
        ax, az = math.cos(ang), math.sin(ang)
        reach = rnd.uniform(2.6, 3.6)
        mid = (fork[0] + ax * reach * 0.6, fork[1] + 1.6, fork[2] + az * reach * 0.6)
        end = (fork[0] + ax * reach, fork[1] + rnd.uniform(3.0, 4.2), fork[2] + az * reach)
        W.mb_tube(mb, [fork, mid, end], lambda t: 0.55 - 0.35 * t, 5, bands[P.BARK], per=4)
        puffs.append((end, rnd.uniform(1.7, 2.2)))
        puffs.append(((mid[0] + ax * 0.6, mid[1] + 0.9, mid[2] + az * 0.6), rnd.uniform(1.2, 1.6)))
        side = ang + rnd.choice((-1, 1)) * 0.7
        puffs.append(((end[0] + math.cos(side) * 1.6, end[1] - 0.8, end[2] + math.sin(side) * 1.6), rnd.uniform(1.0, 1.3)))
    puffs.append(((fork[0], fork[1] + 4.6, fork[2]), rnd.uniform(1.8, 2.3)))
    for k, (c, r) in enumerate(puffs):
        prnd = random.Random(seed * 13 + k)
        wob = lambda th, kk, a=prnd.uniform(0, TAU): 1 + 0.1 * math.sin(3 * th + a + kk)
        # shaded toward the deep end of the blossom strip so crowns read pink, not white
        mb.lathe([(0.0, r * 0.95, 0.62), (r * 0.62, r * 0.75, 0.52), (r * 0.98, r * 0.15, 0.36), (r * 0.8, -r * 0.45, 0.14),
                  (0.0, -r * 0.7, 0.04)], 9, bands[P.BLOSSOM], centre=c, rmod=wob, phase=prnd.uniform(0, TAU),
                 cap_top=False, u_repeat=1.0)
    return mb.object(name, coll, mat)


# ---------- rocks and flowers ----------
def mossy_rock(name, coll, mat, bands, seed, size):
    rnd = random.Random(seed)
    blobs = [((0, size * 0.35, 0), (size, size * 0.7, size * 0.85))]
    for _ in range(rnd.choice((1, 2))):
        a = rnd.uniform(0, TAU)
        blobs.append(((math.cos(a) * size * 0.7, size * 0.2, math.sin(a) * size * 0.7), (size * 0.6, size * 0.5, size * 0.55)))
    o = P.hull_rock(name, coll, mat, bands[P.DARK], blobs, seed)
    # moss on the upward faces
    me = o.data
    uv = me.uv_layers.active
    m0, m1 = bands[P.PINE]
    for poly in me.polygons:
        if poly.normal.z > 0.55:
            for li in poly.loop_indices:
                uv.data[li].uv = (uv.data[li].uv[0], m0 + (m1 - m0) * (0.45 + 0.4 * poly.normal.z))
    # sink the base a little so it sits in the ground
    for v in me.vertices:
        v.co.z -= size * 0.15
    return o


def flower_clump(name, coll, mat, bands, seed, colours):
    rnd = random.Random(seed)
    mb = W.MeshBuilder()
    leaf = bands[P.FLOWERS]
    for k in range(7):
        a, d = rnd.uniform(0, TAU), rnd.uniform(0, 0.9)
        x, z = math.cos(a) * d, math.sin(a) * d
        h = rnd.uniform(0.6, 1.15)
        # leaf blade (two-sided)
        la = rnd.uniform(0, TAU)
        tip = (x + math.cos(la) * 0.5, h * 0.7, z + math.sin(la) * 0.5)
        b0 = (x + math.sin(la) * 0.12, 0, z - math.cos(la) * 0.12)
        b1 = (x - math.sin(la) * 0.12, 0, z + math.cos(la) * 0.12)
        for tri in ([b0, b1, tip], [b1, b0, tip]):
            mb.face(tri, [(P.flower_u(4), leaf[0] + (leaf[1] - leaf[0]) * s) for s in (0.5, 0.5, 0.9)])
        # flower head: small octahedron
        u = P.flower_u(rnd.choice(colours))
        r = rnd.uniform(0.17, 0.26)
        c = (x, h, z)
        tops = [(c[0], c[1] + r, c[2]), (c[0], c[1] - r * 0.6, c[2])]
        ring = [(c[0] + math.cos(TAU * i / 4 + a) * r, c[1], c[2] + math.sin(TAU * i / 4 + a) * r) for i in range(4)]
        for i in range(4):
            j = (i + 1) % 4
            P.oriented(mb, [ring[i], ring[j], tops[0]], (ring[i][0] + ring[j][0] - 2 * c[0], 1, ring[i][2] + ring[j][2] - 2 * c[2]),
                       leaf, u, [0.85, 0.85, 1.0])
            P.oriented(mb, [ring[j], ring[i], tops[1]], (ring[i][0] + ring[j][0] - 2 * c[0], -1, ring[i][2] + ring[j][2] - 2 * c[2]),
                       leaf, u, [0.6, 0.6, 0.5])
    return mb.object(name, coll, mat)


VARIANTS = {
    "SI_SpiritPineA": lambda c, m, b: spirit_pine("SI_SpiritPineA", c, m, b, 3),
    "SI_SpiritPineB": lambda c, m, b: spirit_pine("SI_SpiritPineB", c, m, b, 11),
    "SI_BlossomTreeA": lambda c, m, b: blossom_tree("SI_BlossomTreeA", c, m, b, 5),
    "SI_BlossomTreeB": lambda c, m, b: blossom_tree("SI_BlossomTreeB", c, m, b, 17),
    "SI_MossRockA": lambda c, m, b: mossy_rock("SI_MossRockA", c, m, b, 23, 2.4),
    "SI_MossRockB": lambda c, m, b: mossy_rock("SI_MossRockB", c, m, b, 29, 1.6),
    "SI_FlowersWhite": lambda c, m, b: flower_clump("SI_FlowersWhite", c, m, b, 31, (0, 0, 1)),
    "SI_FlowersWarm": lambda c, m, b: flower_clump("SI_FlowersWarm", c, m, b, 37, (1, 3, 3)),
    "SI_FlowersViolet": lambda c, m, b: flower_clump("SI_FlowersViolet", c, m, b, 41, (2, 2, 0)),
}


# ---------- placement ----------
HERO = [  # (variant, x, z, yaw, scale)
    ("SI_SpiritPineA", -55.0, 20.0, 0.6, 1.25),     # crowning the lookout hill
    ("SI_BlossomTreeA", 29.0, -44.0, 1.1, 1.1),     # framing the Qi Spring's source rock
    ("SI_BlossomTreeB", 56.0, -30.0, 2.4, 1.0),     # far bank of the spring
    ("SI_BlossomTreeA", -50.0, 72.0, 4.0, 1.05),    # west end of the egg garden
    ("SI_BlossomTreeB", -16.0, 48.0, 0.3, 0.95),    # east end of the egg garden
]


def keepouts():
    """(x, z, radius) discs nothing is scattered into."""
    zones = [(0, 0, 28), (S.SPRING[0], S.SPRING[1], 25), (S.EGG_GARDEN[0], S.EGG_GARDEN[1], 22)]
    for eid, x, z, _ in P.egg_layout()[0]:
        zones.append((x, z, 7))
    for route, x, z, _ in P.waystone_layout():
        zones.append((x, z, 13))  # keep the stele and its inscription in clear view
    for name, x, z, *_ in HERO:
        zones.append((x, z, 9))
    for ex, ez in S.EXITS.values():
        zones.append((ex, ez, 12))
    return zones


def scatter(rnd, count, min_gap, path_clear, rim_clear, taken, accept=None, tries=4000):
    out = []
    zones = keepouts()
    for _ in range(tries):
        if len(out) >= count:
            break
        x, z = rnd.uniform(-100, 100), rnd.uniform(-100, 100)
        r = math.hypot(x, z)
        if r > S.rim(math.atan2(z, x)) - rim_clear:
            continue
        if S.path_distance(x, z) < path_clear or S.pool_distance(x, z) < 3:
            continue
        if any(math.hypot(x - zx, z - zz) < zr for zx, zz, zr in zones):
            continue
        if any(math.hypot(x - tx, z - tz) < max(min_gap, tg) for tx, tz, tg in taken):
            continue
        if accept and not accept(x, z, rnd):
            continue
        out.append((x, z))
        taken.append((x, z, min_gap))
    return out


def near_hill(x, z):
    return math.hypot(x - S.HILL[0], z - S.HILL[1]) < 30


def placements():
    rnd = random.Random(2026)
    items = []
    taken = [(x, z, 9) for _, x, z, *_ in HERO]
    for name, x, z, yaw, scale in HERO:
        items.append((name, x, z, yaw, scale, 0.6))
    trees = scatter(rnd, 16, 15, 6, 8, taken)
    for x, z in trees:
        r = math.hypot(x, z)
        pine = near_hill(x, z) or r > 58
        name = ("SI_SpiritPineA" if rnd.random() < 0.5 else "SI_SpiritPineB") if pine else \
               ("SI_BlossomTreeA" if rnd.random() < 0.5 else "SI_BlossomTreeB")
        items.append((name, x, z, rnd.uniform(0, TAU), rnd.uniform(0.85, 1.15), 0.6))
    rocks = scatter(rnd, 16, 8, 3, 2, taken, accept=lambda x, z, rr: near_hill(x, z) or math.hypot(x, z) > 62 or rr.random() < 0.3)
    for x, z in rocks:
        items.append(("SI_MossRockA" if rnd.random() < 0.45 else "SI_MossRockB", x, z, rnd.uniform(0, TAU), rnd.uniform(0.8, 1.3), 0.0))
    flowers = scatter(rnd, 46, 5, 2.4, 3, taken)
    for x, z in flowers:
        name = rnd.choice(("SI_FlowersWhite", "SI_FlowersWarm", "SI_FlowersViolet"))
        items.append((name, x, z, rnd.uniform(0, TAU), rnd.uniform(0.9, 1.25), 0.05))
    return items


def build():
    img = bpy.data.images["StartingIsland_PropAtlas"]
    _, bands = W.atlas_image("StartingIsland_PropAtlas", 512, P.STRIPS)
    mat = W.textured_material("StartingIsland_PropMat", img)
    root = W.collection("StartingIsland")
    coll = W.collection("SI_Nature", root)
    W.clear_collection(coll)
    return [fn(coll, mat, bands) for fn in VARIANTS.values()], img
