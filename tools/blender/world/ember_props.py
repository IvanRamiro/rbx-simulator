"""Ember Peak set pieces, batch 2. Uses the Ember Peak atlas from ember_meshes.

- The Ember Forge ruins: hearth, coals, ruined walls with a furnace chimney, anvils.
- The Ash Plain: the Ashen Sigil monolith and its glowing sigil, petrified trees.
- The Phoenix Altar, at the Cinder Arena's back: a hex-basalt pad under each cinnabar-topped column
  egg pedestal; braziers and basalt columns ring the arena's edge.
- Island dressing: fire crystals, ember vents, basalt clusters, obsidian shards.
"""
import bpy, math, random
import worldlib as W
import ember_island as E
import ember_meshes as EM
import start_props as SP

TAU = 2 * math.pi
oriented = SP.oriented
column = EM.column
ground = EM.ground


# ---------- the Ember Forge (Ember Heart) ----------
FX, FZ, FR = E.FORGE
FORGE_FLOOR = 2.0


def forge_hearth(coll, mat, bands):
    """The round hearth the Ember Heart hovers over: an iron-banded basin of ember stone."""
    mb = W.MeshBuilder()
    mb.lathe([(2.6, 3.0, 0.7), (3.3, 3.2, 0.95), (3.6, 2.9, 0.85), (3.7, 1.2, 0.6), (4.2, 0.4, 0.5), (4.2, -1.0, 0.3)], 12,
             bands[EM.EMBERSTONE], cap_top=False, u_repeat=2.0)
    mb.lathe([(3.72, 2.6, 0.9), (3.78, 2.0, 0.7)], 12, bands[EM.IRON], cap_top=False, u_repeat=1.0)
    mb.lathe([(3.72, 1.5, 0.9), (3.78, 0.9, 0.7)], 12, bands[EM.IRON], cap_top=False, u_repeat=1.0)
    mb.lathe([(2.6, 2.2, 0.4), (0.0, 2.2, 0.3)], 12, bands[EM.SOOT], cap_top=False, u_repeat=0.0)
    return mb.object("EP_ForgeHearth", coll, mat)


def forge_coals(coll, mat, bands):
    mb = W.MeshBuilder()
    rnd = random.Random(31)
    for k in range(11):
        a, d = rnd.uniform(0, TAU), rnd.uniform(0, 1.9)
        SP.pebble(mb, (math.cos(a) * d, 2.2, math.sin(a) * d), 0.6, 0.5, 0.5 + 0.3 * rnd.random(), rnd.uniform(0, TAU), k,
                  bands[EM.GLOW], sink=0.3)
    return mb.object("EP_ForgeCoals", coll, mat)


def forge_walls(coll, mat, bands):
    """A ruined ring of stacked basalt blocks around the forge floor, open to the south-west
    path, with a squat furnace chimney on the north side (island-local, placed at the forge)."""
    mb = W.MeshBuilder()
    rnd = random.Random(41)
    open_a = math.atan2(E.PATHS[2][-1][1] - FZ, E.PATHS[2][-1][0] - FX)
    for k in range(28):
        a = TAU * k / 28
        if abs((a - open_a + math.pi) % TAU - math.pi) < 0.55:
            continue
        x, z = FX + math.cos(a) * (FR - 1.5), FZ + math.sin(a) * (FR - 1.5)
        courses = rnd.choice((1, 2, 2, 3, 4)) if abs((a + math.pi / 2 + math.pi) % TAU - math.pi) > 0.7 else 5
        for c in range(courses):
            rnd.uniform(-0.06, 0.06)            # an unused draw, kept so the stones after it stay as exported
            mb.box((x, FORGE_FLOOR + 0.55 + c * 1.1, z), (3.3 - c * 0.15, 1.05, 1.6), bands[EM.BASALT if c % 2 else EM.SOOT],
                   yaw=math.pi / 2 - a, u=rnd.random(), top_shade=0.8, side_shade=0.55)
    # the furnace chimney on the north side (toward -Z), a tapering stack with an iron collar
    cx, cz = FX, FZ - (FR - 1.5)
    mb.lathe([(1.6, 13.0, 0.7), (1.9, 12.6, 0.8), (2.3, 9.0, 0.6), (3.0, 5.0, 0.55), (3.4, FORGE_FLOOR - 1, 0.4)], 8,
             bands[EM.SOOT], centre=(cx, 0, cz), cap_top=True, u_repeat=1.0)
    mb.lathe([(2.4, 9.6, 0.9), (2.45, 8.8, 0.7)], 8, bands[EM.IRON], centre=(cx, 0, cz), cap_top=False, u_repeat=1.0)
    return mb.object("EP_ForgeWalls", coll, mat)


def anvil(coll, mat, bands):
    mb = W.MeshBuilder()
    I = bands[EM.IRON]
    mb.box((0, 0.5, 0), (1.6, 1.0, 1.2), bands[EM.BASALT], u=0.3, top_shade=0.8, side_shade=0.6)
    mb.box((0, 1.4, 0), (0.9, 0.8, 0.7), I, u=0.6, top_shade=0.8, side_shade=0.6)
    mb.box((0, 2.05, 0), (2.4, 0.5, 0.9), I, u=0.4, top_shade=1.0, side_shade=0.7)
    oriented(mb, [(1.2, 2.3, 0.3), (2.2, 2.05, 0.0), (1.2, 2.3, -0.3)], (0, 1, 0), I, 0.4, [0.95] * 3)
    oriented(mb, [(1.2, 1.8, 0.3), (1.2, 1.8, -0.3), (2.2, 2.05, 0.0)], (0, -1, 0), I, 0.4, [0.5] * 3)
    return mb.object("EP_Anvil", coll, mat)


# ---------- the Ash Plain (Ashen Sigil) ----------
AX, AZ, AR = E.ASH


def sigil_monolith(coll, mat, bands):
    """A cracked obsidian slab, 12 studs tall, its carved sigil facing +Z (origin at ground centre)."""
    mb = W.MeshBuilder()
    t = 0.75
    poly = [(-1.6, -1.5), (1.6, -1.5), (1.45, 9.6), (0.6, 12.2), (-0.4, 11.6), (-1.5, 10.0)]
    oriented(mb, [(x, y, t) for x, y in poly], (0, 0, 1), bands[EM.OBSIDIAN], 0.5, [0.85] * len(poly))
    oriented(mb, [(x, y, -t) for x, y in poly], (0, 0, -1), bands[EM.OBSIDIAN], 0.5, [0.6] * len(poly))
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        oriented(mb, [(a[0], a[1], t), (b[0], b[1], t), (b[0], b[1], -t), (a[0], a[1], -t)], (b[1] - a[1], -(b[0] - a[0]), 0),
                 bands[EM.OBSIDIAN], 0.5, [0.5] * 4)
    mb.box((0, -0.6, 0), (4.4, 1.6, 3.0), bands[EM.BASALT], u=0.2, top_shade=0.8, side_shade=0.5)
    return mb.object("EP_SigilMonolith", coll, mat)


def sigil_glow(coll, mat, bands):
    """The carved sigil (Neon in Roblox): a ring, a flame-like spine and three bars."""
    mb = W.MeshBuilder()
    z = 0.8
    G = bands[EM.GLOW]
    for i in range(16):
        a0, a1 = TAU * i / 16, TAU * (i + 1) / 16
        p = lambda r, a: (math.cos(a) * r, 6.2 + math.sin(a) * r, z)
        oriented(mb, [p(1.0, a0), p(1.18, a0), p(1.18, a1), p(1.0, a1)], (0, 0, 1), G, 0.5, [1.0] * 4)
    for x0, y0, x1, y1, w in ((0, 3.4, 0, 9.4, 0.09), (-0.8, 7.9, 0.8, 7.9, 0.08), (-0.6, 4.6, 0.6, 4.6, 0.08),
                              (-0.9, 6.2, 0.9, 6.2, 0.07), (0, 9.4, 0.45, 10.1, 0.07), (0, 9.4, -0.45, 10.1, 0.07)):
        dx, dy = x1 - x0, y1 - y0
        L_ = math.hypot(dx, dy)
        nx, ny = -dy / L_ * w, dx / L_ * w
        oriented(mb, [(x0 - nx, y0 - ny, z), (x1 - nx, y1 - ny, z), (x1 + nx, y1 + ny, z), (x0 + nx, y0 + ny, z)], (0, 0, 1), G, 0.5, [1.0] * 4)
    return mb.object("EP_SigilGlow", coll, mat)


def petrified_tree(coll, mat, bands, name, seed):
    """A tree turned to stone by the ash: twisted trunk, stubby broken limbs, no leaves."""
    rnd = random.Random(seed)
    mb = W.MeshBuilder()
    h = rnd.uniform(8, 12)
    lean = rnd.uniform(0, TAU)
    lx, lz = math.cos(lean), math.sin(lean)
    trunk = [(0, -1, 0), (lx * 0.6, h * 0.4, lz * 0.6), (lx * 1.4 + rnd.uniform(-0.5, 0.5), h * 0.75, lz * 1.4), (lx * 1.8, h, lz * 1.8)]
    curve = W.mb_tube(mb, trunk, lambda t: 1.1 - 0.75 * t, 7, bands[EM.PETRIFIED], per=4)
    for k in range(rnd.choice((3, 4))):
        base = curve[int(len(curve) * rnd.uniform(0.35, 0.85))]
        a = rnd.uniform(0, TAU)
        reach = rnd.uniform(2.0, 4.0)
        end = (base.x + math.cos(a) * reach, base.y + rnd.uniform(0.6, 2.4), base.z + math.sin(a) * reach)
        W.mb_tube(mb, [tuple(base), ((base.x + end[0]) / 2, base.y + 0.3, (base.z + end[2]) / 2), end],
                  lambda t: 0.45 - 0.3 * t, 5, bands[EM.PETRIFIED], per=3)
    return mb.object(name, coll, mat)


# ---------- the Phoenix Altar (egg shrine) ----------
PAD_R = 4.6   # each egg pedestal's hex-basalt pad
ALTAR_FLOOR = 1.5  # tile tops sit just above the voxel ground of the flat terrace at +1
PEDESTAL_TOPS = (2.8, 4.0, 5.2)   # the three egg columns rise like steps, the rarest egg highest


def altar_floor(coll, mat, bands):
    """A pad of tight hexagonal basalt tops under each egg pedestal (island-local, placed at the origin)."""
    mb = W.MeshBuilder()
    rnd = random.Random(51)
    for _, qx, qz, _, _ in egg_layout():
        for x, z in EM.hex_cells(lambda th: PAD_R, 3.1):
            column(mb, qx + x, qz + z, 1.5, ALTAR_FLOOR - 2.5, ALTAR_FLOOR + rnd.uniform(-0.06, 0.12), bands[EM.BASALT],
                   int(1000 + (qx + x) * 7 + (qz + z) * 13), tilt=0.0, bottom=False)
    return mb.object("EP_AltarFloor", coll, mat)


def egg_pedestal(coll, mat, bands):
    """A single thick basalt column with a cinnabar-lacquered top plate and a gold rim; the egg
    rests on top. Height is set per stand by placement (the top is 4.0 at scale 1)."""
    mb = W.MeshBuilder()
    column(mb, 0, 0, 2.3, -1.5, 3.6, bands[EM.BASALT], 1100, tilt=0.0)
    mb.lathe([(1.9, 4.0, 1.0), (2.15, 3.95, 0.9), (2.2, 3.6, 0.7)], 6, bands[EM.CINNABAR], phase=TAU / 12, cap_top=True, u_repeat=0.0)
    mb.lathe([(2.2, 3.62, 1.0), (2.45, 3.55, 0.9), (2.45, 3.4, 0.7)], 6, bands[EM.GOLD], phase=TAU / 12, cap_top=False, u_repeat=0.0)
    return mb.object("EP_EggPedestal", coll, mat)


def egg_glow_ring(coll, mat, bands):
    mb = W.MeshBuilder()
    mb.lathe([(2.6, 0.06, 1.0), (3.1, 0.06, 1.0)], 6, bands[EM.GLOW], phase=TAU / 12, cap_top=False, u_repeat=0.0)
    return mb.object("EP_EggGlowRing", coll, mat)


def brazier(coll, mat, bands):
    """An iron tripod brazier (fire is EP_BrazierFire)."""
    mb = W.MeshBuilder()
    for k in range(3):
        a = TAU * k / 3
        W.mb_tube(mb, [(math.cos(a) * 1.3, -0.5, math.sin(a) * 1.3), (math.cos(a) * 0.9, 1.8, math.sin(a) * 0.9),
                       (math.cos(a) * 0.95, 3.4, math.sin(a) * 0.95)], lambda t: 0.16, 5, bands[EM.IRON], per=3)
    mb.lathe([(0.8, 4.2, 0.5), (1.6, 4.3, 0.95), (1.75, 4.0, 0.85), (1.2, 3.3, 0.6), (0.5, 3.1, 0.4)], 8, bands[EM.IRON],
             cap_top=True, u_repeat=1.0)
    return mb.object("EP_Brazier", coll, mat)


def brazier_fire(coll, mat, bands):
    mb = W.MeshBuilder()
    for dx, dz, h in ((0, 0, 2.6), (0.5, 0.3, 1.8), (-0.45, -0.35, 2.0)):
        mb.lathe([(0.0, 4.2 + h, 1.0), (0.6, 4.2 + h * 0.4, 0.9), (0.75, 4.15, 0.8)], 7, bands[EM.GLOW], centre=(dx, 0, dz),
                 cap_top=False, cap_bottom=True, u_repeat=0.0)
    return mb.object("EP_BrazierFire", coll, mat)


# ---------- dressing ----------
def fire_crystal(coll, mat, bands):
    mb = W.MeshBuilder()
    rnd = random.Random(61)
    SP.pebble(mb, (0, 0.2, 0), 2.2, 1.9, 1.2, 0.0, 61, bands[EM.BASALT], sink=1.0)
    import jade_meshes as JM
    for k in range(5):
        a = rnd.uniform(0, TAU)
        d = (math.cos(a) * rnd.uniform(0.2, 0.55), 1, math.sin(a) * rnd.uniform(0.2, 0.55))
        JM.crystal_prism(mb, (math.cos(a) * 0.7, 0.6, math.sin(a) * 0.7), d, rnd.uniform(2.2, 4.6), rnd.uniform(0.35, 0.6),
                         bands[EM.CRYSTAL])
    return mb.object("EP_FireCrystal", coll, mat)


def ember_vent(coll, mat, bands):
    """A cracked cinder mound with a glowing throat (EP_VentGlow)."""
    mb = W.MeshBuilder()
    mb.lathe([(0.7, 0.9, 0.5), (1.3, 1.0, 0.8), (2.4, 0.4, 0.7), (2.9, -0.6, 0.5)], 9, bands[EM.SOOT], cap_top=False, u_repeat=1.0)
    mb.lathe([(0.7, 0.9, 0.4), (0.5, 0.2, 0.3)], 9, bands[EM.SOOT], cap_top=False, u_repeat=0.0)
    return mb.object("EP_EmberVent", coll, mat)


def vent_glow(coll, mat, bands):
    mb = W.MeshBuilder()
    mb.lathe([(0.52, 0.35, 1.0), (0.0, 0.35, 1.0)], 9, bands[EM.GLOW], cap_top=False, u_repeat=0.0)
    return mb.object("EP_VentGlow", coll, mat)


def basalt_cluster(coll, mat, bands, name, seed):
    mb = W.MeshBuilder()
    rnd = random.Random(seed)
    for k in range(rnd.randint(5, 8)):
        a, d = rnd.uniform(0, TAU), rnd.uniform(0, 3.2)
        column(mb, math.cos(a) * d, math.sin(a) * d, rnd.uniform(1.1, 1.8), -2.0, rnd.uniform(1.5, 7.5), bands[EM.BASALT],
               seed * 10 + k, tilt=rnd.uniform(0.3, 1.5))
    return mb.object(name, coll, mat)


def obsidian_shard(coll, mat, bands):
    mb = W.MeshBuilder()
    import jade_meshes as JM
    rnd = random.Random(71)
    for k in range(3):
        a = rnd.uniform(0, TAU)
        JM.crystal_prism(mb, (math.cos(a) * 0.5, -0.5, math.sin(a) * 0.5), (math.cos(a) * 0.35, 1, math.sin(a) * 0.35),
                         rnd.uniform(2.5, 4.5), rnd.uniform(0.45, 0.7), bands[EM.OBSIDIAN])
    return mb.object("EP_ObsidianShard", coll, mat)


PIECES = {
    "EP_ForgeHearth": forge_hearth, "EP_ForgeCoals": forge_coals, "EP_ForgeWalls": forge_walls, "EP_Anvil": anvil,
    "EP_SigilMonolith": sigil_monolith, "EP_SigilGlow": sigil_glow,
    "EP_PetrifiedTreeA": lambda c, m, b: petrified_tree(c, m, b, "EP_PetrifiedTreeA", 81),
    "EP_PetrifiedTreeB": lambda c, m, b: petrified_tree(c, m, b, "EP_PetrifiedTreeB", 87),
    "EP_AltarFloor": altar_floor, "EP_EggPedestal": egg_pedestal, "EP_EggGlowRing": egg_glow_ring,
    "EP_Brazier": brazier, "EP_BrazierFire": brazier_fire, "EP_FireCrystal": fire_crystal,
    "EP_EmberVent": ember_vent, "EP_VentGlow": vent_glow,
    "EP_BasaltClusterA": lambda c, m, b: basalt_cluster(c, m, b, "EP_BasaltClusterA", 91),
    "EP_BasaltClusterB": lambda c, m, b: basalt_cluster(c, m, b, "EP_BasaltClusterB", 97),
    "EP_ObsidianShard": obsidian_shard,
}


def build():
    img = bpy.data.images["EmberPeak_Atlas"]
    _, bands = W.atlas_image("EmberPeak_Atlas", 512, EM.STRIPS)
    mat = W.textured_material("EmberPeak_Mat", img)
    root = W.collection(E.NAME)
    coll = W.collection("EP_Props", root)
    W.clear_collection(coll)
    return [fn(coll, mat, bands) for fn in PIECES.values()], img


# ---------- placement ----------
EGG_IDS = ["InfernoEgg", "MagmaHeartEgg", "PhoenixAshEgg"]


def face_yaw(fx, fz):
    return math.atan2(fx, fz)


def egg_layout():
    """The three pedestals in their arc at the arena's back, each facing the lair; the rarest (the
    tallest) in the middle."""
    out = []
    order = (0, 2, 1)   # Inferno, Phoenix Ash, Magma Heart round the arc: Phoenix Ash's tallest column in the middle
    for k, bearing in enumerate(E.EGG_BEARINGS):
        i = order[k]
        x, z = E._polar(bearing, E.EGG_RING)
        out.append((EGG_IDS[i], x, z, face_yaw(E.LAIR[0] - x, E.LAIR[1] - z), PEDESTAL_TOPS[i]))
    return out


SPOKE_BEARINGS = [E.ARRIVAL_BEARING] + [E._bearing_of(p[-1]) for p in E.PATHS[2:]]


def arena_ring():
    """Round the arena, between the paths, just outside its glowing border: braziers and basalt
    column clusters alternating (props ring the middle; nothing stands in it)."""
    out = []
    for k in range(16):
        bearing = 11.25 + 22.5 * k
        if any(abs((bearing - b + 180) % 360 - 180) < 13 for b in SPOKE_BEARINGS):
            continue
        x, z = E._polar(bearing, E.ARENA_EDGE + 3.5)
        out.append(("EP_Brazier" if k % 2 == 0 else "Cluster", x, z, face_yaw(-x, -z)))
    return out


def keepouts():
    return [(FX, FZ, FR + 4), (AX, AZ, 10), (E.ARENA[0], E.ARENA[1], E.RING_R + 5), (E.LANDING[0], E.LANDING[1], 12),
            (E.GATE[0], E.GATE[1], 12), (E.VOLCANO[0], E.VOLCANO[1], E.VOLCANO[2] - 4)]


def scatter(rnd, count, gap, path_clear, rim_clear, taken, accept=None, tries=5000):
    out = []
    zones = keepouts()
    for _ in range(tries):
        if len(out) >= count:
            break
        x, z = rnd.uniform(-E.BASE_R - 15, E.BASE_R + 15), rnd.uniform(-E.BASE_R - 15, E.BASE_R + 15)
        if math.hypot(x, z) > E.rim(math.atan2(z, x)) - rim_clear:
            continue
        if E.path_distance(x, z) < path_clear or E.river_distance(x, z) < E.RIVER_HALF + 3:
            continue
        if any(math.hypot(x - zx, z - zz) < zr for zx, zz, zr in zones):
            continue
        if any(math.hypot(x - tx, z - tz) < max(gap, tg) for tx, tz, tg in taken):
            continue
        if accept and not accept(x, z, rnd):
            continue
        out.append((x, z))
        taken.append((x, z, gap))
    return out


def kit_entries():
    """Kit entries {name: [(position, yaw, scale)]} for batch 2."""
    rnd = random.Random(2028)
    kit = {}

    def add(name, x, y, z, yaw=0.0, scale=1.0):
        kit.setdefault(name, []).append(((x, y, z), yaw, scale))
    # the forge
    add("EP_ForgeHearth", FX, FORGE_FLOOR, FZ)
    add("EP_ForgeCoals", FX, FORGE_FLOOR, FZ)
    add("EP_ForgeWalls", 0, 0, 0)
    add("EP_Anvil", FX + 5.5, FORGE_FLOOR, FZ + 2.5, 0.4)
    add("EP_Anvil", FX - 4.5, FORGE_FLOOR, FZ - 4.0, 2.1, 0.85)
    # the Ash Plain: the monolith stands west of the relic, its sigil facing it
    mx, mz = AX - 4.5, AZ
    add("EP_SigilMonolith", mx, ground(mx, mz), mz, face_yaw(AX - mx, AZ - mz))
    add("EP_SigilGlow", mx, ground(mx, mz), mz, face_yaw(AX - mx, AZ - mz))
    taken = [(FX, FZ, FR + 4), (AX, AZ, 6),
             (E.ARRIVAL[0], E.ARRIVAL[1], 14)]   # where the bridge from Yggdrasil lands, 20 studs wide
    for x, z in scatter(rnd, 16, 8, 4, 6, taken, accept=lambda x, z, r: math.hypot(x - AX, z - AZ) < AR + 22):
        add(rnd.choice(("EP_PetrifiedTreeA", "EP_PetrifiedTreeB")), x, ground(x, z) - 0.4, z, rnd.uniform(0, TAU), rnd.uniform(0.85, 1.25))
    # the altar's pads under the egg pedestals, and the ring round the arena
    add("EP_AltarFloor", 0, 0, 0)
    for name, x, z, yaw in arena_ring():
        y = ground(x, z)
        if name == "EP_Brazier":
            add("EP_Brazier", x, y, z, yaw)
            add("EP_BrazierFire", x, y, z, yaw)
        else:
            add(rnd.choice(("EP_BasaltClusterA", "EP_BasaltClusterB")), x, y - 0.6, z, yaw, rnd.uniform(1.0, 1.3))
    # by the gate's inner side, either side of the path
    (gx0, _, gz0), _ = EM.gate_frame()
    inward = (E.ARENA[0] - gx0, E.ARENA[1] - gz0)
    n = math.hypot(*inward)
    fwd, side_dir = (inward[0] / n, inward[1] / n), (-inward[1] / n, inward[0] / n)
    for side in (-1, 1):
        gx, gz = gx0 + fwd[0] * 5 + side_dir[0] * 7 * side, gz0 + fwd[1] * 5 + side_dir[1] * 7 * side
        add("EP_Brazier", gx, ground(gx, gz), gz)
        add("EP_BrazierFire", gx, ground(gx, gz), gz)
    # dressing, over four times the old ground
    for x, z in scatter(rnd, 30, 12, 4, 3, taken):
        add(rnd.choice(("EP_BasaltClusterA", "EP_BasaltClusterB")), x, ground(x, z) - 0.6, z, rnd.uniform(0, TAU), rnd.uniform(0.8, 1.4))
    for x, z in scatter(rnd, 20, 10, 3, 4, taken):
        add("EP_FireCrystal", x, ground(x, z) - 0.3, z, rnd.uniform(0, TAU), rnd.uniform(0.85, 1.3))
    for x, z in scatter(rnd, 22, 10, 3, 5, taken):
        y = ground(x, z) - 0.2
        yaw = rnd.uniform(0, TAU)
        add("EP_EmberVent", x, y, z, yaw)
        add("EP_VentGlow", x, y, z, yaw)
    for x, z in scatter(rnd, 26, 8, 3, 3, taken):
        add("EP_ObsidianShard", x, ground(x, z) - 0.3, z, rnd.uniform(0, TAU), rnd.uniform(0.8, 1.3))
    return kit


def write_all():
    """Placements for both batches, plus the egg stands."""
    EM.write_placements(extra_kit=kit_entries())
    path = W.REPO + "/src/worldbuild/Placements/EmberPeak.lua"
    s = open(path).read()
    lines = ['    EggStandPieces = { Pedestal = "EP_EggPedestal", GlowRing = "EP_EggGlowRing" },', "    EggStands = {"]
    for eid, x, z, yaw, top in egg_layout():
        lines.append('        { EggId = "%s", Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f, EggRest = %.2f, Scale = %.3f },'
                     % (eid, x, ALTAR_FLOOR, z, yaw, top, top / 4.0))   # on its hex pad
    lines.append("    },")
    s = s.replace("    Checkpoint = ", "\n".join(lines) + "\n    Checkpoint = ", 1)
    open(path, "w").write(s)


def export():
    objs, img = build()
    W.export_batch(objs, W.REPO + "/assets/world/EmberPeak/EmberPeak_Props.fbx", anchor_name="EP_PropsAnchor")
    write_all()
    return objs
