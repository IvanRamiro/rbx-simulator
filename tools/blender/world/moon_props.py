"""Moonlit Isle set pieces, batch 2. Uses the Moonlit Isle atlas from moon_meshes.

- The Celestial Pavilion: a stepped marble platform, eight porcelain pillars with gold crescent
  finials, and a floating golden armillary.
- Porcelain egg pedestals with blue glaze bands and gold bands at the lip and foot.
- Island dressing: star lanterns hovering over the frost, glowing frost lilies, moonstone shards
  and lunar rocks.
"""
import bpy, math, random
import worldlib as W
import moon_island as M
import moon_meshes as MM
import start_props as SP
import jade_meshes as JM

TAU = 2 * math.pi
oriented = SP.oriented
ground = MM.ground

PX, PZ, PR = M.PAVILION
PLATFORM_TOP = 2.6 + 1.2   # the pavilion floor, two steps above the terrace


def pavilion(coll, mat, bands):
    """The platform, pillars and finials (island-local, placed at the island origin)."""
    mb = W.MeshBuilder()
    top = PLATFORM_TOP
    mb.lathe([(8.2, top, 0.95), (8.5, top - 0.15, 0.85), (8.5, top - 0.6, 0.7), (9.4, top - 0.6, 0.9), (9.6, top - 0.75, 0.75),
              (9.6, 1.6, 0.5)], 32, bands[MM.MARBLE], centre=(PX, 0, PZ), cap_top=True, u_repeat=3.0)
    for i in range(32):  # gold inlay ring on the floor
        a0, a1 = TAU * i / 32, TAU * (i + 1) / 32
        p = lambda r, a: (PX + math.cos(a) * r, top + 0.02, PZ + math.sin(a) * r)
        oriented(mb, [p(6.4, a0), p(6.8, a0), p(6.8, a1), p(6.4, a1)], (0, 1, 0), bands[MM.GOLD], 0.5, [1.0] * 4)
    for k in range(8):
        a = TAU * (k + 0.5) / 8
        x, z = PX + math.cos(a) * 7.4, PZ + math.sin(a) * 7.4
        mb.lathe([(0.55, top + 9.0, 0.9), (0.42, top + 8.6, 0.85), (0.36, top + 0.6, 0.6), (0.6, top + 0.3, 0.7), (0.62, top, 0.6)], 8,
                 bands[MM.PORCELAIN], centre=(x, 0, z), cap_top=True, u_repeat=1.0)
        # gold crescent finial on each pillar, opening outward
        for j in range(10):
            t0, t1 = j / 10, (j + 1) / 10
            def pt(t, rr):
                ang = math.pi * (0.15 + 0.7 * t)
                return (x + math.cos(a) * math.cos(ang) * rr, top + 9.0 + math.sin(ang) * rr, z + math.sin(a) * math.cos(ang) * rr)
            w0 = 0.15 + 0.35 * math.sin(math.pi * t0)
            w1 = 0.15 + 0.35 * math.sin(math.pi * t1)
            quad = [pt(t0, 1.0), pt(t1, 1.0), pt(t1, 1.0 + w1), pt(t0, 1.0 + w0)]
            oriented(mb, quad, (-math.sin(a), 0, math.cos(a)), bands[MM.GOLD], 0.5, [1.0] * 4)
            oriented(mb, quad, (math.sin(a), 0, -math.cos(a)), bands[MM.GOLD], 0.5, [0.85] * 4)
    return mb.object("MI_Pavilion", coll, mat)


ARMILLARY_Y = PLATFORM_TOP + 13.0


def armillary(coll, mat, bands):
    """Three interlocking gold rings floating over the pavilion (no collision)."""
    mb = W.MeshBuilder()
    for k, (tilt, spin, r) in enumerate(((0.0, 0.0, 4.2), (1.15, 0.6, 3.9), (1.15, 2.2, 3.6))):
        seg = 40
        for i in range(seg):
            a0, a1 = TAU * i / seg, TAU * (i + 1) / seg
            ring = []
            for a in (a0, a1):
                for dr in (-0.18, 0.18):
                    x, y, z = math.cos(a) * (r + dr), 0.0, math.sin(a) * (r + dr)
                    # tilt about X, then spin about Y
                    y, z = y * math.cos(tilt) - z * math.sin(tilt), y * math.sin(tilt) + z * math.cos(tilt)
                    x, z = x * math.cos(spin) + z * math.sin(spin), -x * math.sin(spin) + z * math.cos(spin)
                    ring.append((PX + x, ARMILLARY_Y + y, PZ + z))
            (a_in, a_out, b_in, b_out) = ring
            for side in (1, -1):
                n = (math.sin(spin) * math.sin(tilt) * side, math.cos(tilt) * side, math.cos(spin) * math.sin(tilt) * side)
                oriented(mb, [a_in, a_out, b_out, b_in], n, bands[MM.GOLD], 0.5, [1.0 if side > 0 else 0.8] * 4)
    mb.lathe([(0.0, ARMILLARY_Y + 0.9, 1.0), (0.7, ARMILLARY_Y + 0.4, 0.9), (0.9, ARMILLARY_Y, 0.8), (0.7, ARMILLARY_Y - 0.4, 0.7),
              (0.0, ARMILLARY_Y - 0.9, 0.6)], 10, bands[MM.MOONSTONE], centre=(PX, 0, PZ), cap_top=False, u_repeat=1.0)
    return mb.object("MI_Armillary", coll, mat)


PEDESTAL_TOP = 4.2


def egg_pedestal(coll, mat, bands):
    """A porcelain column with blue glaze bands and a wide dish, gold bands round its lip and foot
    (the egg rests at 4.2). Its gold wings and orbiting ring are gone: they were sized round the old
    egg family, and the ring cut through the new, wider Moonlit eggs."""
    mb = W.MeshBuilder()
    top = PEDESTAL_TOP
    mb.lathe([(1.95, top, 1.0), (2.1, top - 0.05, 0.95), (2.1, top - 0.25, 0.9), (1.9, top - 0.35, 0.85), (1.2, top - 0.9, 0.8),
              (0.9, 1.4, 0.7), (1.5, 0.8, 0.85), (1.9, 0.0, 0.6), (1.9, -0.4, 0.4)], 32, bands[MM.PORCELAIN], cap_top=True, u_repeat=2.0)
    for y in (1.2, 2.4):
        mb.lathe([(0.97, y + 0.18, 1.0), (0.97, y - 0.18, 1.0)], 16, bands[MM.NIGHT], cap_top=False, u_repeat=1.0)
    mb.lathe([(2.12, top - 0.07, 1.0), (2.12, top - 0.23, 0.85)], 32, bands[MM.GOLD], cap_top=False, u_repeat=2.0)   # the lip's band
    mb.lathe([(1.92, 0.12, 1.0), (1.92, -0.06, 0.8)], 32, bands[MM.GOLD], cap_top=False, u_repeat=2.0)               # the foot's band
    return mb.object("MI_EggPedestal", coll, mat)


def egg_glow_ring(coll, mat, bands):
    mb = W.MeshBuilder()
    mb.lathe([(2.1, 0.04, 1.0), (2.5, 0.04, 1.0)], 32, bands[MM.GLOW], cap_top=False, u_repeat=0.0)
    return mb.object("MI_EggGlowRing", coll, mat)


def star_lantern(coll, mat, bands):
    """A porcelain lantern hovering over the frost (origin at ground; the lantern floats 3.2 up)."""
    mb = W.MeshBuilder()
    y = 3.2
    mb.lathe([(0.0, y + 1.7, 1.0), (0.4, y + 1.6, 0.95), (1.0, y + 1.15, 0.9), (0.95, y + 0.95, 0.7), (0.5, y + 0.9, 0.6)], 8,
             bands[MM.PORCELAIN], cap_top=False, cap_bottom=True, u_repeat=0.0)
    for k in range(4):
        a = TAU * k / 4 + TAU / 8
        mb.box((math.cos(a) * 0.62, y + 0.45, math.sin(a) * 0.62), (0.14, 0.9, 0.14), bands[MM.GOLD], yaw=-a, u=0.5, top_shade=1.0, side_shade=0.8)
    mb.lathe([(0.5, y, 0.9), (0.75, y - 0.1, 0.8), (0.5, y - 0.35, 0.6)], 8, bands[MM.PORCELAIN], cap_top=True, cap_bottom=True, u_repeat=0.0)
    return mb.object("MI_StarLantern", coll, mat)


def star_lantern_core(coll, mat, bands):
    mb = W.MeshBuilder()
    y = 3.2
    mb.lathe([(0.0, y + 0.85, 1.0), (0.45, y + 0.45, 1.0), (0.0, y + 0.05, 1.0)], 8, bands[MM.GLOW], cap_top=False, u_repeat=0.0)
    return mb.object("MI_StarLanternCore", coll, mat)


def frost_lilies(coll, mat, bands):
    """A clump of pale lilies (their glowing hearts are MI_LilyGlow)."""
    rnd = random.Random(501)
    mb = W.MeshBuilder()
    for k in range(5):
        a, d = rnd.uniform(0, TAU), rnd.uniform(0, 1.1)
        x, z = math.cos(a) * d, math.sin(a) * d
        h = rnd.uniform(0.8, 1.5)
        W.mb_tube(mb, [(x, -0.2, z), (x, h * 0.5, z), (x + 0.1, h, z)], lambda t: 0.06, 4, bands[MM.SILVER], per=2)
        for p in range(5):
            pa = TAU * p / 5 + rnd.uniform(0, 0.3)
            tip = (x + math.cos(pa) * 0.55, h + 0.35, z + math.sin(pa) * 0.55)
            l = (x + math.cos(pa + 0.4) * 0.2, h + 0.05, z + math.sin(pa + 0.4) * 0.2)
            r = (x + math.cos(pa - 0.4) * 0.2, h + 0.05, z + math.sin(pa - 0.4) * 0.2)
            for tri in ([l, r, tip], [r, l, tip]):
                mb.face(tri, [(0.5, bands[MM.PEARL][1])] * 3)
    return mb.object("MI_FrostLilies", coll, mat)


def lily_glow(coll, mat, bands):
    rnd = random.Random(501)
    mb = W.MeshBuilder()
    for k in range(5):
        a, d = rnd.uniform(0, TAU), rnd.uniform(0, 1.1)
        x, z = math.cos(a) * d, math.sin(a) * d
        h = rnd.uniform(0.8, 1.5)
        rnd.random()  # keep in step with frost_lilies' petal jitter draws
        for _ in range(4):
            rnd.uniform(0, 0.3)
        mb.lathe([(0.0, h + 0.3, 1.0), (0.16, h + 0.15, 1.0), (0.0, h, 1.0)], 6, bands[MM.GLOW], centre=(x, 0, z), cap_top=False, u_repeat=0.0)
    return mb.object("MI_LilyGlow", coll, mat)


def moonstone_shards(coll, mat, bands):
    mb = W.MeshBuilder()
    rnd = random.Random(511)
    SP.pebble(mb, (0, 0, 0), 1.6, 1.4, 0.8, 0.0, 511, bands[MM.LUNAR], sink=0.8)
    for k in range(4):
        a = rnd.uniform(0, TAU)
        JM.crystal_prism(mb, (math.cos(a) * 0.5, 0.3, math.sin(a) * 0.5), (math.cos(a) * 0.35, 1, math.sin(a) * 0.35),
                         rnd.uniform(1.8, 3.6), rnd.uniform(0.3, 0.5), bands[MM.MOONSTONE], k)
    return mb.object("MI_MoonstoneShards", coll, mat)


def lunar_rock(coll, mat, bands):
    o = SP.hull_rock("MI_LunarRock", coll, mat, bands[MM.LUNAR], [((0, 0.5, 0), (2.2, 1.2, 1.8)), ((1.1, 0.3, 0.6), (1.2, 0.9, 1.1))], 521)
    return o


PIECES = {
    "MI_Pavilion": pavilion, "MI_Armillary": armillary, "MI_EggPedestal": egg_pedestal, "MI_EggGlowRing": egg_glow_ring,
    "MI_StarLantern": star_lantern, "MI_StarLanternCore": star_lantern_core, "MI_FrostLilies": frost_lilies,
    "MI_LilyGlow": lily_glow, "MI_MoonstoneShards": moonstone_shards, "MI_LunarRock": lunar_rock,
}


def build():
    img = bpy.data.images["MoonlitIsle_Atlas"]
    _, bands = W.atlas_image("MoonlitIsle_Atlas", 512, MM.STRIPS)
    mat = W.textured_material("MoonlitIsle_Mat", img)
    root = W.collection(M.NAME)
    coll = W.collection("MI_Props", root)
    W.clear_collection(coll)
    return [fn(coll, mat, bands) for fn in PIECES.values()], img


# ---------- placement ----------
EGG_IDS = ["CelestialEgg", "AstralSanctumEgg", "HeavenlyThroneEgg"]


def face_yaw(fx, fz):
    return math.atan2(fx, fz)


def egg_layout():
    """Three pedestals across the pavilion's far half, facing the path in."""
    entrance = M.PATHS[2][-1]
    toward = math.atan2(entrance[1] - PZ, entrance[0] - PX)
    out = []
    for k, eid in enumerate(EGG_IDS):
        a = toward + math.pi + (k - 1) * 1.3   # about 6 studs apart, so the wings never overlap
        x, z = PX + math.cos(a) * 5.0, PZ + math.sin(a) * 5.0
        out.append((eid, x, z, face_yaw(entrance[0] - x, entrance[1] - z)))
    return out


def scatter(rnd, count, gap, taken, edge_min=3.0, tries=4000):
    out = []
    zones = [(M.MIRROR[0], M.MIRROR[1], M.MIRROR[2] + 2), (PX, PZ, PR + 2), (M.WELL[0], M.WELL[1], M.WELL[2] + 4),
             (M.LANDING[0], M.LANDING[1], M.LANDING[2] + 4),
             (M.ARRIVAL[0], M.ARRIVAL[1], 9)]   # where the bridge from the Starting Island lands
    for _ in range(tries):
        if len(out) >= count:
            break
        x, z = rnd.uniform(-65, 65), rnd.uniform(-60, 70)
        if M.edge_distance(x, z) < edge_min or M.path_distance(x, z) < 3:
            continue
        if any(math.hypot(x - a, z - b) < r for a, b, r in zones):
            continue
        if any(math.hypot(x - tx, z - tz) < max(gap, tg) for tx, tz, tg in taken):
            continue
        out.append((x, z))
        taken.append((x, z, gap))
    return out


def kit_entries():
    rnd = random.Random(2029)
    kit = {}

    def add(name, x, y, z, yaw=0.0, scale=1.0):
        kit.setdefault(name, []).append(((x, y, z), yaw, scale))
    add("MI_Pavilion", 0, 0, 0)
    add("MI_Armillary", 0, 0, 0)
    taken = [(M.ARRIVAL[0], M.ARRIVAL[1], 14)]   # where the bridge from the Starting Island lands, 20 studs wide
    # star lanterns along the paths
    for line in M.PATHS:
        for (ax, az), (bx, bz) in zip(line, line[1:]):
            L_ = math.hypot(bx - ax, bz - az)
            for k in range(1, int(L_ // 12) + 1):
                t = k * 12 / L_
                px, pz = ax + (bx - ax) * t, az + (bz - az) * t
                nx, nz = -(bz - az) / L_ * 4.0, (bx - ax) / L_ * 4.0
                side = 1 if k % 2 else -1
                x, z = px + nx * side, pz + nz * side
                if M.edge_distance(x, z) > 3:
                    add("MI_StarLantern", x, ground(x, z), z, rnd.uniform(0, TAU))
                    add("MI_StarLanternCore", x, ground(x, z), z)
                    taken.append((x, z, 4))
    # a ring of star lanterns around the Moon Mirror, leaving the bridge's bank clear
    mx, mz, mr = M.MIRROR
    bridge = math.atan2(M.JUNCTION[1] - mz, M.JUNCTION[0] - mx)
    for k in range(6):
        a = bridge + TAU * (k + 0.5) / 6
        x, z = mx + math.cos(a) * (mr + 0.5), mz + math.sin(a) * (mr + 0.5)
        if M.edge_distance(x, z) > 3:
            add("MI_StarLantern", x, ground(x, z), z, a)
            add("MI_StarLanternCore", x, ground(x, z), z)
            taken.append((x, z, 4))
    for x, z in scatter(rnd, 16, 6, taken):
        y = ground(x, z) - 0.1
        yaw = rnd.uniform(0, TAU)
        add("MI_FrostLilies", x, y, z, yaw)
        add("MI_LilyGlow", x, y, z, yaw)
    for x, z in scatter(rnd, 9, 9, taken):
        add("MI_MoonstoneShards", x, ground(x, z) - 0.2, z, rnd.uniform(0, TAU), rnd.uniform(0.8, 1.3))
    for x, z in scatter(rnd, 8, 9, taken, edge_min=2.0):
        add("MI_LunarRock", x, ground(x, z) - 0.4, z, rnd.uniform(0, TAU), rnd.uniform(0.8, 1.4))
    # more spires along both horns
    for deg in (192, 200, 345, 352, 18):
        for frac in (0.5,):
            x, z = M.band_point(deg, frac)
            if M.edge_distance(x, z) > 1.8 and all(math.hypot(x - tx, z - tz) > max(6, tg) for tx, tz, tg in taken):
                add("MI_MoonstoneSpire", x, ground(x, z) - 0.2, z, rnd.uniform(0, TAU), rnd.uniform(0.7, 1.0))
                taken.append((x, z, 6))
    return kit


def write_all():
    lines = ['    EggStandPieces = { Pedestal = "MI_EggPedestal", GlowRing = "MI_EggGlowRing" },', "    EggStands = {"]
    for eid, x, z, yaw in egg_layout():
        lines.append('        { EggId = "%s", Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f, EggRest = %.2f },'
                     % (eid, x, PLATFORM_TOP, z, yaw, PEDESTAL_TOP))
    lines.append("    },")
    MM.write_placements(extra_kit=kit_entries(), extra_lines=lines)


def export_pedestal():
    """Only the egg pedestal, for a small import (WorldBuilder.storeKit replaces just that template)."""
    objs, img = build()
    pedestal = [o for o in objs if o.name == "MI_EggPedestal"]
    W.export_batch(pedestal, W.REPO + "/assets/world/MoonlitIsle/MI_EggPedestal.fbx", anchor_name="MI_PropsAnchor")
    return pedestal


def export():
    objs, img = build()
    W.export_batch(objs, W.REPO + "/assets/world/MoonlitIsle/MoonlitIsle_Props.fbx", anchor_name="MI_PropsAnchor")
    write_all()
    return objs
