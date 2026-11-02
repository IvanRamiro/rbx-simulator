"""Jade Grove set pieces and forest, batch 2: the Bloom Glade shrine (flagstone floor, standing
stones, golden-root egg pedestals), the Whispering Hollow (spring water, rim stones, whisper
stones), jade lanterns, and the forest: ancient trees, bamboo, ferns, glowing mushrooms, jade
outcrops, ruin pillars and fallen logs. Uses the Jade Grove atlas from jade_meshes.
"""
import bpy, math, random
import worldlib as W
import jade_island as J
import jade_meshes as JM
import start_props as SP

TAU = 2 * math.pi
oriented = SP.oriented


def ground(x, z):
    return J.height(x, z)[0]


# ---------- Bloom Glade ----------
PEDESTAL_TOP = 3.35  # the jade seat's top, where the egg rests


def egg_pedestal(coll, mat, bands):
    """Golden roots rising from a mossy stone base to cradle the egg on a jade seat."""
    mb = W.MeshBuilder()
    mb.lathe([(3.6, 1.0, 0.95), (3.8, 0.85, 0.8), (3.8, 0.6, 0.6), (4.6, 0.6, 0.9), (4.8, 0.45, 0.7), (4.8, -1.2, 0.45)],
             28, bands[JM.STONE], cap_top=True, u_repeat=2.0)
    mb.lathe([(0.0, 3.3, 1.0), (1.3, 3.25, 0.9), (1.6, 2.9, 0.7), (1.0, 1.0, 0.5)], 6, bands[JM.JADE], cap_top=False, u_repeat=1.0)
    rnd = random.Random(4)
    for k in range(5):  # low golden roots twisting up around the seat (the egg has its own roots)
        a = TAU * k / 5 + 0.2
        pts = [(math.cos(a) * 3.4, 0.8, math.sin(a) * 3.4), (math.cos(a + 0.5) * 2.4, 1.6, math.sin(a + 0.5) * 2.4),
               (math.cos(a + 1.0) * 1.75, 2.7 + rnd.uniform(-0.1, 0.2), math.sin(a + 1.0) * 1.75),
               (math.cos(a + 1.5) * 1.55, 3.7 + rnd.uniform(0, 0.3), math.sin(a + 1.5) * 1.55)]
        W.mb_tube(mb, pts, lambda t: 0.34 - 0.24 * t, 6, bands[JM.GOLD], per=4)
    return mb.object("JG_EggPedestal", coll, mat)


def egg_glow_ring(coll, mat, bands):
    mb = W.MeshBuilder()
    mb.lathe([(3.95, 0.64, 1.0), (4.4, 0.64, 1.0)], 40, bands[JM.GLOW], cap_top=False, u_repeat=0.0)
    return mb.object("JG_EggGlowRing", coll, mat)


def glade_floor(coll, mat, bands):
    """Irregular mossy flagstones in rings, about 12 studs across the radius, with moss joints."""
    mb = W.MeshBuilder()
    rnd = random.Random(19)
    mb.lathe([(12.6, -0.12, 0.6), (12.8, -0.6, 0.4)], 32, bands[JM.MOSS], cap_top=True, u_repeat=0.0)
    for r0, r1, n in ((0.0, 3.2, 1), (3.2, 7.0, 8), (7.0, 12.4, 13)):
        off = rnd.uniform(0, TAU)
        for k in range(n):
            if n == 1:
                poly = [(math.cos(TAU * i / 7) * (r1 - 0.12), math.sin(TAU * i / 7) * (r1 - 0.12)) for i in range(7)]
            else:
                a0, a1 = off + TAU * k / n, off + TAU * (k + 1) / n
                poly = [(math.cos(a0) * r0, math.sin(a0) * r0), (math.cos(a1) * r0, math.sin(a1) * r0),
                        (math.cos(a1) * r1, math.sin(a1) * r1), (math.cos(a0) * r1, math.sin(a0) * r1)]
                poly = SP.inset(poly, 0.16)
            SP.slab_tile(mb, poly, 0.0, -0.12, bands[JM.STONE], rnd.random(), 0.75 + 0.25 * rnd.random())
    return mb.object("JG_GladeFloor", coll, mat)


def standing_stone(coll, mat, bands, name="JG_StandingStone", height=7.0, seed=8):
    """A tall weathered slab with a chamfered crown and a jade disc set in its face (+Z)."""
    mb = W.MeshBuilder()
    rnd = random.Random(seed)
    w, t = 1.2, 0.55
    poly = [(-w, -1.0), (w, -1.0), (w * 0.92, height * 0.82), (w * 0.45, height), (-w * 0.55, height * 0.96), (-w * 0.95, height * 0.8)]
    poly = [(x + rnd.uniform(-0.08, 0.08), y) for x, y in poly]
    oriented(mb, [(x, y, t) for x, y in poly], (0, 0, 1), bands[JM.STONE], 0.4, [0.9] * len(poly))
    oriented(mb, [(x, y, -t) for x, y in poly], (0, 0, -1), bands[JM.STONE], 0.6, [0.7] * len(poly))
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        oriented(mb, [(a[0], a[1], t), (b[0], b[1], t), (b[0], b[1], -t), (a[0], a[1], -t)], (b[1] - a[1], -(b[0] - a[0]), 0),
                 bands[JM.STONE], 0.5, [0.6] * 4)
    SP.disc_z(mb, (0, height * 0.66, t + 0.03), 0.0, 0.5, 10, bands[JM.JADE])
    SP.disc_z(mb, (0, height * 0.66, t + 0.02), 0.5, 0.68, 10, bands[JM.GOLD], shade=0.8)
    return mb.object(name, coll, mat)


def whisper_stone(coll, mat, bands):
    return standing_stone(coll, mat, bands, "JG_WhisperStone", height=9.5, seed=12)


# ---------- Whispering Hollow ----------
def hollow_water(coll, mat, bands):
    mb = W.MeshBuilder()
    px, pz, pr = J.HOLLOW_POOL
    r = pr + 0.7
    for i in range(28):
        a0, a1 = TAU * i / 28, TAU * (i + 1) / 28
        oriented(mb, [(px + math.cos(a0) * r, J.POOL_WATER, pz + math.sin(a0) * r), (px + math.cos(a1) * r, J.POOL_WATER, pz + math.sin(a1) * r),
                      (px, J.POOL_WATER, pz)], (0, 1, 0), bands[JM.JADE], 0.5, [0.7, 0.7, 0.9])
    return mb.object("JG_HollowWater", coll, mat)


def hollow_rim(coll, mat, bands):
    mb = W.MeshBuilder()
    rnd = random.Random(23)
    px, pz, pr = J.HOLLOW_POOL
    n = 18
    for k in range(n):
        a = TAU * k / n + rnd.uniform(-0.08, 0.08)
        r = pr + 1.0
        x, z = px + math.cos(a) * r, pz + math.sin(a) * r
        size = 0.9 + 0.6 * rnd.random()
        SP.pebble(mb, (x, ground(x, z) - 0.2, z), size * 1.3, size, 0.6 + 0.6 * rnd.random(), math.pi / 2 - a,
                  rnd.randint(0, 1 << 20), bands[JM.STONE], sink=1.2)
    return mb.object("JG_HollowRim", coll, mat)


# ---------- lanterns ----------
def jade_lantern(coll, mat, bands):
    mb = W.MeshBuilder()
    S, Jd = bands[JM.STONE], bands[JM.JADE]
    mb.lathe([(0.75, 1.35, 0.9), (0.95, 1.15, 0.8), (1.15, 0.6, 0.7), (1.3, 0.4, 0.6), (1.3, -0.8, 0.4)], 6, S, cap_top=True, u_repeat=0.0)
    mb.lathe([(0.42, 3.95, 0.85), (0.36, 1.35, 0.6)], 6, S, cap_top=False, u_repeat=0.0)
    mb.lathe([(0.95, 4.35, 0.95), (1.2, 4.3, 0.85), (1.25, 4.15, 0.7), (1.05, 3.95, 0.55), (0.42, 3.9, 0.5)], 6, S, cap_top=True, u_repeat=0.0)
    for k in range(6):
        a = TAU * k / 6
        mb.box((math.cos(a) * 0.86, 5.1, math.sin(a) * 0.86), (0.26, 1.5, 0.26), S, yaw=-a, u=0.4, top_shade=0.9, side_shade=0.7)
    mb.lathe([(0.22, 6.95, 0.95), (0.55, 6.7, 0.9), (1.25, 6.25, 0.82), (1.75, 6.05, 0.78), (1.88, 6.14, 0.75),
              (1.82, 5.92, 0.5), (0.95, 5.85, 0.35)], 6, Jd, cap_top=True, cap_bottom=True, u_repeat=0.0)
    mb.lathe([(0.12, 7.75, 1.0), (0.3, 7.42, 0.9), (0.2, 7.18, 0.7), (0.28, 6.95, 0.6)], 6, bands[JM.GOLD], cap_top=True, u_repeat=0.0)
    return mb.object("JG_JadeLantern", coll, mat)


def jade_lantern_light(coll, mat, bands):
    mb = W.MeshBuilder()
    mb.lathe([(0.62, 5.78, 1.0), (0.62, 4.38, 0.85)], 6, bands[JM.GLOW], cap_top=True, cap_bottom=True, u_repeat=0.0)
    return mb.object("JG_JadeLanternLight", coll, mat)


# ---------- forest ----------
def ancient_tree(coll, mat, bands, name, seed):
    """A smaller cousin of the Elder Tree: leaning trunk, three or four branches, cloud-tier canopy."""
    rnd = random.Random(seed)
    mb = W.MeshBuilder()
    h = rnd.uniform(18, 23)
    lean = rnd.uniform(0, TAU)
    lx, lz = math.cos(lean), math.sin(lean)
    trunk = [(0, -1.5, 0), (lx * 0.8, h * 0.35, lz * 0.8), (lx * 2.0 + rnd.uniform(-1, 1), h * 0.7, lz * 2.0), (lx * 2.6, h, lz * 2.6)]
    curve = W.mb_tube(mb, trunk, lambda t: 2.4 - 1.6 * t, 9, bands[JM.BARK], per=5)
    for k in range(3):  # flared roots
        a = TAU * k / 3 + rnd.uniform(-0.3, 0.3)
        W.mb_tube(mb, [(math.cos(a) * 1.0, 2.2, math.sin(a) * 1.0), (math.cos(a) * 3.0, 0.4, math.sin(a) * 3.0),
                       (math.cos(a) * 4.4, -1.0, math.sin(a) * 4.4)], lambda t: 1.3 - 0.8 * t, 6, bands[JM.BARK], per=3)
    tiers = [(curve[-1], rnd.uniform(5.0, 6.0))]
    for k in range(rnd.choice((3, 4))):
        idx = int(len(curve) * rnd.uniform(0.45, 0.85))
        base = curve[idx]
        a = lean + TAU * k / 4 + rnd.uniform(-0.4, 0.4)
        reach = rnd.uniform(5, 8)
        end = (base.x + math.cos(a) * reach, base.y + rnd.uniform(1.0, 3.0), base.z + math.sin(a) * reach)
        mid = ((base.x + end[0]) / 2, base.y + 0.3, (base.z + end[2]) / 2)
        W.mb_tube(mb, [tuple(base), mid, end], lambda t: 0.8 - 0.5 * t, 6, bands[JM.BARK], per=4)
        tiers.append((W.Vector(end), rnd.uniform(3.6, 4.8)))
    for k, (c, r) in enumerate(tiers):
        JM.cloud_tier(mb, (c.x, c.y + 1.0, c.z), r, bands[JM.LEAF], seed * 31 + k)
    return mb.object(name, coll, mat)


def bamboo_clump(coll, mat, bands, name="JG_BambooClump", seed=5):
    rnd = random.Random(seed)
    mb = W.MeshBuilder()
    for k in range(9):
        a, d = rnd.uniform(0, TAU), rnd.uniform(0, 1.8)
        x, z = math.cos(a) * d, math.sin(a) * d
        h = rnd.uniform(11, 16)
        tilt = rnd.uniform(0, TAU)
        tx, tz = math.cos(tilt) * h * 0.08, math.sin(tilt) * h * 0.08
        top = (x + tx, h, z + tz)
        W.mb_tube(mb, [(x, -0.8, z), (x + tx * 0.4, h * 0.5, z + tz * 0.4), top], lambda t: 0.3 - 0.1 * t, 5, bands[JM.BAMBOO], per=3)
        for s in range(5):  # leaf sprays near the top
            la = rnd.uniform(0, TAU)
            yy = h * rnd.uniform(0.62, 0.98)
            c = (x + tx * yy / h, yy, z + tz * yy / h)
            tip = (c[0] + math.cos(la) * 1.8, yy - 0.6, c[2] + math.sin(la) * 1.8)
            side = (math.cos(la + 1.57) * 0.25, 0, math.sin(la + 1.57) * 0.25)
            p0 = (c[0] + side[0], yy, c[2] + side[2]); p1 = (c[0] - side[0], yy, c[2] - side[2])
            v0, v1 = bands[JM.LEAF]
            for tri in ([p0, p1, tip], [p1, p0, tip]):
                mb.face(tri, [(rnd.random(), v0 + (v1 - v0) * s_) for s_ in (0.6, 0.6, 0.9)])
    return mb.object(name, coll, mat)


def fern(coll, mat, bands, name="JG_Fern", seed=9):
    rnd = random.Random(seed)
    mb = W.MeshBuilder()
    v0, v1 = bands[JM.LEAF]
    for k in range(8):
        a = TAU * k / 8 + rnd.uniform(-0.2, 0.2)
        length = rnd.uniform(2.0, 3.0)
        dx, dz = math.cos(a), math.sin(a)
        prev = (0.0, 0.1, 0.0)
        for s in range(1, 5):
            t = s / 4
            cur = (dx * length * t, 0.1 + 1.6 * t - 1.3 * t * t, dz * length * t)
            w = 0.55 * (1 - t * 0.7)
            sx, sz = -dz * w, dx * w
            for side in (1, -1):
                tip = ((prev[0] + cur[0]) / 2 + sx * side, (prev[1] + cur[1]) / 2 - 0.1, (prev[2] + cur[2]) / 2 + sz * side)
                for tri in ([prev, cur, tip], [cur, prev, tip]):
                    mb.face(tri, [(rnd.random() * 0.5, v0 + (v1 - v0) * s_) for s_ in (0.55, 0.7, 0.95)])
            prev = cur
    return mb.object(name, coll, mat)


def mushrooms(coll, mat, bands):
    """Stems (JG_Mushrooms) and caps (JG_MushroomCaps, made Neon in Roblox) built from one layout."""
    rnd = random.Random(14)
    stems, caps = W.MeshBuilder(), W.MeshBuilder()
    for k in range(5):
        a, d = rnd.uniform(0, TAU), rnd.uniform(0, 1.4)
        x, z = math.cos(a) * d, math.sin(a) * d
        h = rnd.uniform(0.6, 1.6)
        r = rnd.uniform(0.35, 0.7)
        stems.lathe([(r * 0.3, h, 0.9), (r * 0.25, -0.3, 0.6)], 6, bands[JM.STONE], centre=(x, 0, z), cap_top=False, u_repeat=0.0)
        caps.lathe([(0.0, h + r * 0.6, 1.0), (r * 0.7, h + r * 0.45, 0.95), (r, h + 0.05, 0.85), (r * 0.5, h - 0.05, 0.6)], 8,
                   bands[JM.GLOW], centre=(x, 0, z), cap_top=False, cap_bottom=True, u_repeat=0.0)
    return [stems.object("JG_Mushrooms", coll, mat), caps.object("JG_MushroomCaps", coll, mat)]


def jade_outcrop(coll, mat, bands):
    o_rock = SP.hull_rock("JG_OutcropRock_tmp", coll, mat, bands[JM.STRATA], [((0, 0.6, 0), (2.6, 1.4, 2.2)), ((1.4, 0.3, 0.8), (1.6, 1.0, 1.4))], 33)
    mb = W.MeshBuilder()
    rnd = random.Random(35)
    for k in range(5):
        a = rnd.uniform(0, TAU)
        d = (math.cos(a) * rnd.uniform(0.2, 0.5), 1, math.sin(a) * rnd.uniform(0.2, 0.5))
        JM.crystal_prism(mb, (math.cos(a) * 0.8, 0.8, math.sin(a) * 0.8), d, rnd.uniform(2.5, 5.0), rnd.uniform(0.4, 0.7),
                         bands[JM.JADE], k)
    crystals = mb.object("JG_OutcropCrystals_tmp", coll, mat)
    return _join("JG_JadeOutcrop", [o_rock, crystals])


def ruin_pillar(coll, mat, bands):
    mb = W.MeshBuilder()
    rnd = random.Random(41)
    S = bands[JM.STONE]
    mb.lathe([(1.6, 0.5, 0.85), (1.8, 0.2, 0.7), (1.8, -0.8, 0.5)], 8, S, cap_top=True, u_repeat=0.0)
    broken = lambda th, k: 1.0
    mb.lathe([(1.0, 5.4, 0.8), (1.0, 0.5, 0.6)], 8, S, cap_top=False, u_repeat=1.0)
    # jagged broken top
    top = [(math.cos(TAU * i / 8) * 1.0, 5.4 + rnd.uniform(-0.6, 0.9), math.sin(TAU * i / 8) * 1.0) for i in range(8)]
    for i in range(8):
        oriented(mb, [top[i], top[(i + 1) % 8], (0.1, 5.6, 0.0)], (0, 1, 0), S, 0.5, [0.7] * 3)
    # its fallen drum lying beside it, half sunk
    mb.box((2.9, 0.15, 0.6), (3.2, 1.7, 1.8), S, yaw=0.5, u=0.6, top_shade=0.8, side_shade=0.6)
    mb.box((2.9, 1.05, 0.6), (3.4, 0.25, 2.0), bands[JM.MOSS], yaw=0.5, u=0.3, top_shade=0.9, side_shade=0.7)
    return mb.object("JG_RuinPillar", coll, mat)


def fallen_log(coll, mat, bands):
    mb = W.MeshBuilder()
    W.mb_tube(mb, [(-5.5, 0.3, 0), (0, 0.9, 0.4), (5.5, 0.5, -0.2)], lambda t: 1.1 - 0.25 * t, 8, bands[JM.BARK], per=4)
    for k in range(5):  # moss pads along the top
        x = -4 + k * 2
        mb.lathe([(0.7, 0.0, 1.0), (0.9, -0.2, 0.8)], 7, bands[JM.MOSS], centre=(x, 1.75 + 0.1 * math.sin(k), 0.2),
                 cap_top=True, u_repeat=0.0)
    return mb.object("JG_FallenLog", coll, mat)


def _join(name, objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name; o.data.name = name
    return o


PIECES = {
    "JG_EggPedestal": egg_pedestal, "JG_EggGlowRing": egg_glow_ring, "JG_GladeFloor": glade_floor,
    "JG_StandingStone": standing_stone, "JG_WhisperStone": whisper_stone, "JG_HollowWater": hollow_water,
    "JG_HollowRim": hollow_rim, "JG_JadeLantern": jade_lantern, "JG_JadeLanternLight": jade_lantern_light,
    "JG_AncientTreeA": lambda c, m, b: ancient_tree(c, m, b, "JG_AncientTreeA", 61),
    "JG_AncientTreeB": lambda c, m, b: ancient_tree(c, m, b, "JG_AncientTreeB", 73),
    "JG_BambooClump": bamboo_clump, "JG_Fern": fern, "JG_JadeOutcrop": jade_outcrop, "JG_RuinPillar": ruin_pillar,
    "JG_FallenLog": fallen_log,
}


def build():
    img = bpy.data.images["JadeGrove_Atlas"]
    _, bands = W.atlas_image("JadeGrove_Atlas", 512, JM.STRIPS)
    mat = W.textured_material("JadeGrove_Mat", img)
    root = W.collection(J.NAME)
    coll = W.collection("JG_Props", root)
    W.clear_collection(coll)
    objs = []
    for name, fn in PIECES.items():
        out = fn(coll, mat, bands)
        objs.extend(out if isinstance(out, list) else [out])
    objs.extend(mushrooms(coll, mat, bands))
    return objs, img


# ---------- placement ----------
EGG_IDS = ["JadeSpiritEgg", "BloomwoodEgg", "AncientGroveEgg"]


def face_yaw(fx, fz):
    return math.atan2(fx, fz)


def arena_eggs():
    """The three egg stands in their arc behind the Mantis Sage's lair, each facing the lair."""
    eggs = []
    for eid, bearing in zip(EGG_IDS, J.EGG_BEARINGS):
        x, z = J._polar(bearing, J.EGG_RING)
        eggs.append((eid, x, z, face_yaw(J.LAIR[0] - x, J.LAIR[1] - z)))
    return eggs


def glade_stones():
    """The Bloom Glade's ring of standing stones, its opening toward the arena."""
    gx, gz, gr = J.GLADE
    opening = math.atan2(J.ARENA[1] - gz, J.ARENA[0] - gx)
    stones = []
    for k in range(7):
        a = opening + math.radians(30 + k * (300 / 6))
        x, z = gx + math.cos(a) * 15.5, gz + math.sin(a) * 15.5
        stones.append((x, z, face_yaw(gx - x, gz - z)))
    return stones


SPOKE_BEARINGS = [J.ARRIVAL_BEARING, 150, -62, -148, 100]   # where paths leave the arena's ring


def arena_ring():
    """Round the arena, between the paths: jade lanterns and standing stones alternating, just outside
    its flagstones (props ring the middle; nothing stands in it)."""
    out = []
    for k in range(16):
        bearing = 11.25 + 22.5 * k
        if any(abs((bearing - b + 180) % 360 - 180) < 13 for b in SPOKE_BEARINGS):
            continue
        x, z = J._polar(bearing, J.ARENA_EDGE + 3)
        out.append(("JG_JadeLantern" if k % 2 == 0 else "JG_StandingStone", x, z, face_yaw(-x, -z)))
    return out


def ruin_court():
    """Broken pillars round the Ruin Court."""
    rx, rz, rr = J.RUINS
    rnd = random.Random(31)
    out = []
    for k in range(7):
        a = math.radians(k * 360 / 7 + rnd.uniform(-10, 10))
        out.append((rx + math.cos(a) * (rr - 3), rz + math.sin(a) * (rr - 3), rnd.uniform(0, TAU)))
    return out


def whisper_layout():
    px, pz, pr = J.HOLLOW_POOL
    out = []
    for deg in (20, 140, 260):
        a = math.radians(deg)
        x, z = px + math.cos(a) * (pr + 4.5), pz + math.sin(a) * (pr + 4.5)
        out.append((x, z, face_yaw(px - x, pz - z)))
    return out


def flank(end, prev, spread):
    """Two points either side of a path's end, `spread` studs from its centre line."""
    dx, dz = end[0] - prev[0], end[1] - prev[1]
    L = math.hypot(dx, dz)
    px, pz = -dz / L, dx / L
    return [(end[0] + px * spread, end[1] + pz * spread), (end[0] - px * spread, end[1] - pz * spread)]


def keepouts():
    zones = [(J.GLADE[0], J.GLADE[1], 20), (J.ELDER[0], J.ELDER[1], 26), (J.HOLLOW[0], J.HOLLOW[1], 16),
             (J.LANDING[0], J.LANDING[1], 14), (J.GATE[0], J.GATE[1], 14), (J.ARRIVAL[0], J.ARRIVAL[1], 12),
             (J.ARENA[0], J.ARENA[1], J.RING_R + 5), (J.RUINS[0], J.RUINS[1], J.RUINS[2] + 2)]
    return zones


def scatter(rnd, count, gap, path_clear, rim_clear, taken, zones, inside=None, tries=5000):
    out = []
    for _ in range(tries):
        if len(out) >= count:
            break
        x, z = rnd.uniform(-J.BASE_R - 15, J.BASE_R + 15), rnd.uniform(-J.BASE_R - 15, J.BASE_R + 15)
        if math.hypot(x, z) > J.rim(math.atan2(z, x)) - rim_clear:
            continue
        if J.path_distance(x, z) < path_clear or J.pool_distance(x, z) < 2.5:
            continue
        if inside is None and any(math.hypot(x - zx, z - zz) < zr for zx, zz, zr in zones):
            continue
        if inside is not None and not inside(x, z):
            continue
        if any(math.hypot(x - tx, z - tz) < max(gap, tg) for tx, tz, tg in taken):
            continue
        out.append((x, z))
        taken.append((x, z, gap))
    return out


def placements():
    """Kit entries (name, x, y, z, yaw, scale), the egg stands and the rest of Placements."""
    rnd = random.Random(2027)
    items = []
    eggs = arena_eggs()
    gx, gz = J.GLADE[0], J.GLADE[1]
    items.append(("JG_GladeFloor", gx, 1.02, gz, 0.0, 1.0))  # the glade terrace is flat at +1
    for x, z, yaw in glade_stones():
        items.append(("JG_StandingStone", x, ground(x, z), z, yaw, rnd.uniform(0.9, 1.1)))
    for name, x, z, yaw in arena_ring():
        y = ground(x, z)
        items.append((name, x, y, z, yaw, 1.0 if name == "JG_JadeLantern" else rnd.uniform(0.95, 1.1)))
        if name == "JG_JadeLantern":
            items.append(("JG_JadeLanternLight", x, y, z, yaw, 1.0))
    for x, z, yaw in ruin_court():
        items.append(("JG_RuinPillar", x, ground(x, z), z, yaw, rnd.uniform(0.9, 1.25)))
    for x, z, yaw in whisper_layout():
        items.append(("JG_WhisperStone", x, ground(x, z), z, yaw, 1.0))
    items.append(("JG_HollowWater", 0, 0, 0, 0.0, 1.0))
    items.append(("JG_HollowRim", 0, 0, 0, 0.0, 1.0))
    lanterns = flank(J.PATHS[2][-1], J.PATHS[2][-2], 5.0) + flank(J.PATHS[4][-1], J.PATHS[4][-2], 4.0) + \
        flank(J.PATHS[3][-1], J.PATHS[3][-2], 4.5) + flank(J.PATHS[5][-1], J.PATHS[5][-2], 4.5)
    yaw = JM.gate_yaw()
    fwd, right = (math.sin(yaw), math.cos(yaw)), (math.cos(yaw), -math.sin(yaw))
    for side in (1, -1):  # just inside the Grove Gate, either side of the path
        lanterns.append((J.GATE[0] + fwd[0] * 4.5 + right[0] * 5.0 * side, J.GATE[1] + fwd[1] * 4.5 + right[1] * 5.0 * side))
    for x, z in lanterns:
        y = ground(x, z)
        yaw = face_yaw(-x, -z)
        items.append(("JG_JadeLantern", x, y, z, yaw, 1.0))
        items.append(("JG_JadeLanternLight", x, y, z, yaw, 1.0))
    zones = keepouts()
    taken = [(x, z, 3) for _, x, _, z, *_ in items]
    # the forest ringing the arena: four times the ground of the old island, so about three times the trees
    for x, z in scatter(rnd, 46, 17, 6, 8, taken, zones):
        items.append((rnd.choice(("JG_AncientTreeA", "JG_AncientTreeB")), x, ground(x, z) - 0.4, z, rnd.uniform(0, TAU), rnd.uniform(0.85, 1.25)))
    for x, z in scatter(rnd, 28, 11, 4, 6, taken, zones):
        items.append(("JG_BambooClump", x, ground(x, z), z, rnd.uniform(0, TAU), rnd.uniform(0.85, 1.15)))
    for x, z in scatter(rnd, 20, 12, 3, 4, taken, zones):
        items.append(("JG_JadeOutcrop", x, ground(x, z) - 0.3, z, rnd.uniform(0, TAU), rnd.uniform(0.9, 1.4)))
    for x, z in scatter(rnd, 10, 14, 4, 6, taken, zones):
        items.append(("JG_RuinPillar", x, ground(x, z), z, rnd.uniform(0, TAU), rnd.uniform(0.9, 1.2)))
    for x, z in scatter(rnd, 12, 14, 4, 6, taken, zones):
        items.append(("JG_FallenLog", x, ground(x, z) - 0.6, z, rnd.uniform(0, TAU), rnd.uniform(0.9, 1.2)))
    # ferns and mushrooms everywhere outside the arena, including the hollow and the Elder Tree knoll (but not paths)
    small_ok = lambda x, z: all(math.hypot(x - zx, z - zz) > zr for zx, zz, zr in
                                ((J.GLADE[0], J.GLADE[1], 14), (J.LANDING[0], J.LANDING[1], 12), (J.GATE[0], J.GATE[1], 10),
                                 (J.ARENA[0], J.ARENA[1], J.RING_R + 3), (J.RUINS[0], J.RUINS[1], J.RUINS[2] - 2)))
    for x, z in scatter(rnd, 40, 7, 2.6, 4, taken, zones, inside=small_ok):
        y = ground(x, z)
        yaw = rnd.uniform(0, TAU)
        items.append(("JG_Mushrooms", x, y, z, yaw, 1.0))
        items.append(("JG_MushroomCaps", x, y, z, yaw, 1.0))
    for x, z in scatter(rnd, 130, 5, 2.6, 3, taken, zones, inside=small_ok):
        items.append(("JG_Fern", x, ground(x, z) - 0.1, z, rnd.uniform(0, TAU), rnd.uniform(0.9, 1.4)))
    return items, eggs


def write_placements(path=W.REPO + "/src/worldbuild/Placements/JadeGrove.lua"):
    kit = {"JG_TreeShelf": [(p, y, 1.0) for p, y in JM.climb_shelves()],
           "JG_GroveGate": [((J.GATE[0], ground(*J.GATE) - 0.3, J.GATE[1]), JM.gate_yaw(), 1.0)]}
    items, eggs = placements()
    for name, x, y, z, yaw, scale in items:
        kit.setdefault(name, []).append(((x, y, z), yaw, scale))
    lines = ["-- Generated by tools/blender/world/jade_props.py. Do not edit by hand.",
             "-- Island-local Roblox studs. Kit entries place each piece's authored origin.", "return {", "    Kit = {"]
    for name in sorted(kit):
        lines.append("        %s = {" % name)
        for (x, y, z), yaw, scale in kit[name]:
            extra = ", Scale = %.3f" % scale if abs(scale - 1) > 1e-6 else ""
            lines.append("            { Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f%s }," % (x, y, z, yaw, extra))
        lines.append("        },")
    lines.append("    },")
    lines.append('    EggStandPieces = { Pedestal = "JG_EggPedestal", GlowRing = "JG_EggGlowRing" },')
    lines.append("    EggStands = {")
    for eid, x, z, yaw in eggs:
        lines.append('        { EggId = "%s", Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f, EggRest = %.2f },'
                     % (eid, x, ground(x, z), z, yaw, PEDESTAL_TOP))
    lines.append("    },")
    lx, lz = J.LANDING[0], J.LANDING[1]
    lines.append("    Checkpoint = Vector3.new(%.2f, %.2f, %.2f)," % (lx, ground(lx, lz) + 0.5, lz))
    lines.append("    Relics = {")
    for rid, (x, y, z) in JM.relic_positions().items():
        lines.append('        %s = Vector3.new(%.2f, %.2f, %.2f),' % (rid, x, y, z))
    lines.append("    },")
    lines += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def export():
    objs, img = build()
    out = W.REPO + "/assets/world/JadeGrove/"
    W.export_batch(objs, out + "JadeGrove_Props.fbx", anchor_name="JG_PropsAnchor")
    write_placements()
    return objs
