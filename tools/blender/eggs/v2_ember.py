"""Ember Peak's eggs, second generation (see egg_forge.py).

Inferno Egg, "breaking open": black obsidian shattered from one point. Fractures radiate from the right
shoulder the way glass breaks from an impact: long crooked cracks, and only a few cross cracks, so the
pieces are long shards. Lava is white-hot at the break and thins with distance to a dull thread, leaving the
far side clean black glass. At the centre five shards have blown clear: each is the real piece that fits
the hole it left, thick, burning on its underside, and the hole is molten.

Magma Heart Egg, "the heart in the stone": no spikes. The egg keeps its egg shape, cut into broad planes of
crimson garnet that brighten toward a molten heart set in its front: a domed stone in a black iron setting,
fire turning inside it. Arteries of lava branch out from it across the planes. A squat cut crystal sits low
on the crown, flat tabular shards of garnet lie against the shoulders, and black crust still clings to the
lower part, torn where the stone broke through.

Phoenix Ash Egg, "folded wings": the bird has not hatched, it is wrapped round itself. Rows of
overlapping crimson feather-scales in real relief, smaller toward the crown; two wings of layered
flame feathers (coverts, secondaries, primaries) sweep from the back and open around the egg; a crest
of long plumes streams back off the crown, and a gold flame burns on its breast.
"""
import math

import bmesh
import numpy as np

import egg_forge as F
import egg_hi as Hm
import egg_kit as K
import v2_origin as O

V = F.V
W = K.W
TAU = F.TAU


def on_path(points, off=0.0):
    return [F.on(s % 1.0, v, off) for s, v in points]


# ---------- Inferno Egg ----------
IN_LAVA = "ff4a12"
IN_HOT = "ffa21e"
IN_BREACH = (0.7, 0.73)
IN_SEED = 217
IN_SECTORS = 8
IN_KNOTS = (0.0, 0.3, 0.62, 1.0, 1.42, 1.86, 2.3, 2.72, math.pi)
IN_BLOWN = (0, 1, 3, 4, 6)      # the sectors whose innermost shard has blown clear


def to_shell(q, off=0.0):
    ss = (math.atan2(q.x, q.z) / TAU + 0.5) % 1.0
    vv = math.acos(max(-1, min(1, 1 - 2 * max(0.001, min(F.H - 0.001, q.y)) / F.H))) / math.pi
    return F.on(ss, vv, off), F.normal(ss, vv)


IN_CENTRE = V((0, F.H / 2, 0))


def in_layout():
    """The shatter, all from one seed: long crooked cracks leaving the point of impact, and a few cross
    cracks between them, so the pieces are long shards, not tiles. Paint, Neon and blown plates all read
    this one description, so they line up."""
    import random
    rnd = random.Random(IN_SEED)
    base = [TAU * i / IN_SECTORS + rnd.uniform(-0.2, 0.2) for i in range(IN_SECTORS)]
    wander = [[0.0 if k == 0 else rnd.uniform(-0.2, 0.2) for k in range(len(IN_KNOTS))] for _ in range(IN_SECTORS)]
    cross = []
    for i in range(IN_SECTORS):
        row = [(0.56 + rnd.uniform(-0.1, 0.1), rnd.uniform(-0.08, 0.08))]
        # further out they thin, and some are left out, so a shard can run a long way
        for th in (1.08, 1.62, 2.2, 2.7):
            if rnd.random() < 0.62:
                row.append((th + rnd.uniform(-0.2, 0.2), rnd.uniform(-0.22, 0.22)))
        cross.append(row)
    return base, wander, cross


def in_dir(th, ph):
    d0 = (F.on(*IN_BREACH) - IN_CENTRE).normalized()
    e1, e2 = O.frame(d0)
    return d0 * math.cos(th) + (e1 * math.cos(ph) + e2 * math.sin(ph)) * math.sin(th)


def in_point(th, ph):
    """Where the ray from the egg's middle in that direction meets the shell."""
    d = in_dir(th, ph)
    r = 1.2
    for _ in range(8):
        p, _n = to_shell(IN_CENTRE + d * r)
        r = (p - IN_CENTRE).length
    return p


def in_phi(i, th, base, wander):
    return base[i] + float(np.interp(th, IN_KNOTS, wander[i]))


def in_cell(i, band, base, wander, cross):
    """The corners of one shard, going round it, and a point in its middle."""
    n = (i + 1) % IN_SECTORS
    off = TAU if n == 0 else 0.0
    def edge_th(b, right):
        if b >= len(cross[i]):
            return math.pi - 0.01
        th, tilt = cross[i][b]
        return th + (tilt if right else -tilt)
    lo_l, lo_r = (0.0, 0.0) if band == 0 else (edge_th(band - 1, False), edge_th(band - 1, True))
    hi_l, hi_r = edge_th(band, False), edge_th(band, True)
    pts = []
    knots = lambda a, b: [a] + [k for k in IN_KNOTS if a < k < b] + [b]
    for th in knots(max(lo_l, 0.0), hi_l):
        pts.append(in_point(th, in_phi(i, th, base, wander)))
    for th in reversed(knots(max(lo_r, 0.0), hi_r)):
        pts.append(in_point(th, in_phi(n, th, base, wander) + off))
    if band == 0:
        pts = pts[:-1]
    midth = (lo_l + hi_l + lo_r + hi_r) / 4
    midph = (in_phi(i, midth, base, wander) + in_phi(n, midth, base, wander) + off) / 2
    return in_point(midth, midph), pts


def in_segments():
    """Every crack as a list of (a, b, how far from the break it is, 0..pi)."""
    base, wander, cross = in_layout()
    out = []
    for i in range(IN_SECTORS):
        n = (i + 1) % IN_SECTORS
        off = TAU if n == 0 else 0.0
        # the long cracks, broken at the knots so they run in straight crooked lengths
        for a, b in zip(IN_KNOTS, IN_KNOTS[1:]):
            for q in range(3):
                t0, t1 = a + (b - a) * q / 3, a + (b - a) * (q + 1) / 3
                out.append((in_point(t0, in_phi(i, t0, base, wander)), in_point(t1, in_phi(i, t1, base, wander)), (t0 + t1) / 2))
        for th, tilt in cross[i]:
            left = in_phi(i, th - tilt, base, wander)
            right = in_phi(n, th + tilt, base, wander) + off
            for q in range(6):
                f0, f1 = q / 6, (q + 1) / 6
                t0, t1 = th - tilt + 2 * tilt * f0, th - tilt + 2 * tilt * f1
                out.append((in_point(t0, left + (right - left) * f0), in_point(t1, left + (right - left) * f1), (t0 + t1) / 2))
    return out


def inferno_paint():
    f = F.Field()
    P = f.P
    base, wander, cross = in_layout()
    d0 = (F.on(*IN_BREACH) - IN_CENTRE).normalized()
    e1, e2 = O.frame(d0)
    rel = P - np.array(IN_CENTRE)
    rel = rel / np.maximum(np.sqrt((rel ** 2).sum(-1)), 1e-6)[..., None]
    th = np.arccos(np.clip((rel * np.array(d0)).sum(-1), -1, 1))
    ph = np.arctan2((rel * np.array(e2)).sum(-1), (rel * np.array(e1)).sum(-1))
    # which sector: the long cracks' angles at this distance from the break
    bounds = np.stack([base[i] + np.interp(th, IN_KNOTS, wander[i]) for i in range(IN_SECTORS)], -1)
    b0 = bounds[..., 0]
    relph = (ph - b0) % TAU
    relb = (bounds - b0[..., None]) % TAU
    sector = (relph[..., None] >= relb).sum(-1) - 1
    # which band across that sector
    nxt = np.take_along_axis(relb, ((sector + 1) % IN_SECTORS)[..., None], -1)[..., 0]
    nxt = np.where(nxt <= 0, TAU, nxt)
    cur = np.take_along_axis(relb, sector[..., None], -1)[..., 0]
    frac = np.clip((relph - cur) / np.maximum(nxt - cur, 1e-6), 0, 1)
    band = np.zeros(th.shape, dtype=int)
    for i in range(IN_SECTORS):
        m = sector == i
        for c_th, tilt in cross[i]:
            band = np.where(m & (th > c_th + tilt * (2 * frac - 1)), band + 1, band)
    ids = sector * 10 + band
    # distance to the nearest crack, and how far from the break that crack is
    seam_d = np.full(th.shape, 9.0)
    for a, b, t in in_segments():
        a, b = np.array(a), np.array(b)
        ab = b - a
        tt = np.clip(((P - a) * ab).sum(-1) / max(ab.dot(ab), 1e-9), 0, 1)
        seam_d = np.minimum(seam_d, np.sqrt(((P - a - ab * tt[..., None]) ** 2).sum(-1)))
    # energy dies with distance from the break: wide and white-hot near it, a dull thread far away
    reach = np.exp(-((th / 1.75) ** 2))
    wob = F.fbm(P, 3.4, 2, seed=231)
    width = np.maximum(0.009 + 0.05 * reach + 0.006 * wob, 0.006)
    seam = 1 - F.sstep(width * 0.7, width, seam_d)
    per = (np.sin(ids * 91.7) * 43758.5) % 1.0
    t1, t2, t3 = np.sin(ids * 917.3), np.cos(ids * 371.1), np.sin(ids * 113.7)
    tilt = 0.05 * (t1 * P[..., 0] + t2 * P[..., 2] + t3 * (P[..., 1] - 1.3) * 0.5)
    bevel = F.sstep(width, width + 0.014, seam_d)
    grain = F.fbm(P, 16.0, 3, seed=232)
    height = (tilt + 0.04) * bevel + 0.0025 * grain
    col = F.ramp(np.clip(0.3 + 0.5 * per + 0.25 * grain, 0, 1), [(0.0, "040303"), (0.5, "0c0a09"), (1.0, "1c1716")])
    band_h = np.exp(-((np.maximum(seam_d - width, 0) / (0.02 + 0.11 * reach)) ** 1.2)) * (0.3 + 0.7 * reach)
    col = col + F.ramp(band_h, [(0.0, "000000"), (0.4, "2a0602"), (0.8, "8c1a05"), (1.0, "e8420c")])
    t = np.clip(seam_d / width + (1 - reach) * 0.55, 0, 1)
    lava = F.ramp(t, [(0.0, "fff2a8"), (0.3, "ffc23a"), (0.6, "ff7a14"), (0.85, "c82604"), (1.0, "5a0e03")])
    col = F.mix(col, lava, seam)
    height = height - 0.05 * seam
    hole = np.isin(ids, np.array([k * 10 for k in IN_BLOWN]))
    _, skin_edge, skin = F.voronoi(P, 9.0, seed=235)
    crust = (skin > 0.72) * F.sstep(0.02, 0.1, skin_edge)
    pool = F.ramp(np.clip(0.5 + F.fbm(P, 5.0, 3, seed=236) * 0.9, 0, 1), [(0.0, "ff5a10"), (0.5, "ffa21e"), (1.0, "fff0a0")])
    pool = F.mix(pool, np.array((0.16, 0.05, 0.02)), crust)
    col = np.where(hole[..., None], pool, col)
    height = np.where(hole, -0.09 + 0.006 * crust, height)
    rough = np.clip(0.12 + 0.08 * (grain * 0.5 + 0.5) + 0.3 * seam, 0, 1)
    rough = np.where(hole, 0.45, rough)
    return f, np.clip(col, 0, 1), rough, np.zeros(f.S.shape), height


def in_plate_material():
    """UV v says where: 1 is the plate's outer face (black glass), 0 its broken edge (burning)."""
    g = Hm._Graph("IN_Plate")
    _, v, _ = g.sep(g.coords("UV"))
    grain = g.n("ShaderNodeTexNoise", **{"Scale": 22.0, "Detail": 3.0})
    g.link(g.coords(), grain.inputs["Vector"])
    black = g.ramp(grain.outputs["Fac"], [(0.35, (0.002, 0.0015, 0.0015)), (0.65, (0.012, 0.009, 0.008))])
    edge = g.ramp(v, [(0.0, (1.0, 0.42, 0.06)), (0.5, (0.72, 0.09, 0.01)), (0.98, (0.12, 0.02, 0.006))])
    col = g.mix(g.math("GREATER_THAN", v, 0.99), edge, black)
    return g.finish(col, 0.15, 0.0, g.bump(grain.outputs["Fac"], 0.08, 0.003))


def in_blown_plates(coll):
    base, wander, cross = in_layout()
    hi, under = Hm.Hi(), Hm.Hi()
    # how far each has gone: the first barely lifted, the last well clear, each turning as it goes
    flight = ((0.22, 0.12, 0.1), (0.42, -0.2, 0.16), (0.62, 0.24, -0.2), (0.86, -0.3, 0.3), (1.12, 0.34, 0.36))
    for k, i in enumerate(IN_BLOWN):
        site, corners = in_cell(i, 0, base, wander, cross)
        n = to_shell(site)[1]
        lift, ax, ay = flight[k]
        e1, e2 = O.frame(n)
        axis = (e1 * ax + e2 * ay)

        def place(p):
            d = p - site
            c, s_ = math.cos(axis.length), math.sin(axis.length)
            u = axis.normalized()
            d = d * c + u.cross(d) * s_ + u * u.dot(d) * (1 - c)
            return site + d * 0.94 + n * lift + V((0, 0.16 * lift, 0))
        m = len(corners)
        outer = [hi.v(place(p)) for p in corners]
        mids = [hi.v(place(to_shell(site.lerp(p, 0.55))[0])) for p in corners]
        top = hi.v(place(site))
        inner = [hi.v(place(p - to_shell(p)[1] * 0.11)) for p in corners]
        for a in range(m):
            b = (a + 1) % m
            hi.f([outer[a], outer[b], mids[b], mids[a]], [(0, 1), (1, 1), (1, 1), (0, 1)])
            hi.f([mids[a], mids[b], top], [(0, 1), (1, 1), (0.5, 1)])
            hi.f([inner[a], inner[b], outer[b], outer[a]], [(0, 0), (1, 0), (1, 0.95), (0, 0.95)])
        ring = [under.v(place(p - to_shell(p)[1] * 0.11 - n * 0.002)) for p in corners]
        low = under.v(place(site - n * 0.11 - n * 0.002))
        for a in range(m):
            under.f([ring[(a + 1) % m], ring[a], low], [(0, 0), (1, 0), (0, 1)])
    o = hi.object("IN_Plates", coll, [in_plate_material()], smooth=False)
    F.fix_normals(o)
    o["w"] = 1.0
    u = F.fix_normals(under.object("IN_Under", coll, [K.glow_material(IN_LAVA)], smooth=False, weld=0))
    return o, u


def in_threads(coll):
    """Neon in the hot part of each crack, seated in the channel: it fades out with distance."""
    hi = Hm.Hi()
    for a, b, th in in_segments():
        if th > 1.75 or th < 0.56:
            continue            # none inside the open hole: there's nothing there for a crack to run through
        pts = []
        for t in range(3):
            q, n = to_shell(a.lerp(b, t / 2))
            pts.append((q + n * -0.016, n))
        F.prism(hi, pts, 0.008 + 0.024 * math.exp(-((th / 1.1) ** 2)), height=lambda w: w * 0.5)
    return hi.object("IN_LavaThreads", coll, [K.glow_material(IN_HOT)], smooth=False, weld=0)


def inferno_clay():
    coll = W.collection("InfernoEggHi")
    f, col, rough, metal, height = inferno_paint()
    shell = F.shell_mesh("IN_Shell", coll, 256, 160, height)
    o, u = in_blown_plates(coll)
    t = in_threads(coll)
    return {x.name: F.tris(x) for x in (shell, o, u, t)}


def inferno_build():
    coll = W.collection("InfernoEggHi")
    f, col, rough, metal, height = inferno_paint()
    mat = F.shell_material("IN_Glass", col, rough, metal)
    o, u = in_blown_plates(coll)
    t = in_threads(coll)
    return F.assemble("InfernoEgg", coll, mat, height, [o], {IN_HOT: [t], IN_LAVA: [u]}, budget=2000, shell_frac=0.82, low_nu=96, low_nv=62, shell_ext=0.16, shell_ray=0.36, hard=25, ao_floor=0.8)


# ---------- Magma Heart Egg ----------
MH_VEIN = "ff3214"
MH_HEART = (0.5, 0.48)
# the arteries: (x, y) on a plane at the heart, each starting at the setting and branching outward
MH_ARTERIES = (
    ((0.28, 0.28), (0.44, 0.48), (0.42, 0.72), (0.58, 0.95)),
    ((0.44, 0.48), (0.68, 0.5), (0.86, 0.66)),
    ((-0.3, 0.26), (-0.5, 0.42), (-0.46, 0.68), (-0.62, 0.9)),
    ((-0.5, 0.42), (-0.74, 0.4), (-0.92, 0.5)),
    ((0.38, -0.08), (0.62, -0.02), (0.82, -0.14), (0.98, -0.06)),
    ((-0.38, -0.1), (-0.6, -0.04), (-0.8, -0.18), (-0.96, -0.12)),
    ((0.0, 0.38), (0.06, 0.62), (-0.04, 0.84)),
    ((0.2, -0.32), (0.3, -0.5), (0.24, -0.66)),
    ((-0.2, -0.32), (-0.34, -0.48), (-0.28, -0.62)),
)
# the shards: tabular plates lying on the shoulders, wide and low. (s, v, radius, roll)
MH_SHARDS = ((0.23, 0.66, 0.2, 0.3), (0.31, 0.74, 0.14, 1.1), (0.16, 0.74, 0.12, 2.2), (0.77, 0.66, 0.2, -0.4), (0.69, 0.75, 0.13, 0.9), (0.85, 0.73, 0.12, 1.9),
             (0.03, 0.6, 0.17, 0.7), (0.96, 0.7, 0.13, 2.6), (0.42, 0.82, 0.1, 1.5), (0.6, 0.83, 0.1, 0.2))


def magma_paint():
    f = F.Field()
    P, Vv = f.P, f.V
    warp = np.stack([F.fbm(P, 2.2, 3, seed=s) for s in (301, 302, 303)], -1) * 0.1
    # the crust's torn edge: lower at the front so the heart is clear, higher behind
    broken = 0.27 + 0.1 * np.cos(TAU * (f.S - 0.5) + math.pi) + 0.09 * F.fbm(P, 3.2, 3, seed=304) + 0.025 * F.fbm(P, 16.0, 2, seed=305)
    stone = F.sstep(broken - 0.004, broken + 0.004, Vv)
    # broad cut planes, each tilted its own way, sharp where they meet
    _, wall, cid = F.voronoi(P + warp * 0.5, 2.7, seed=306, jitter=1.0, stretch=(1.0, 0.8, 1.0))
    t1, t2, t3 = np.sin(cid * 917.3), np.cos(cid * 371.1), np.sin(cid * 113.7)
    tilt = 0.042 * (t1 * P[..., 0] + t2 * P[..., 2] + t3 * (P[..., 1] - 1.3) * 0.5)
    edge = 1 - F.sstep(0.0, 0.02, wall)
    # the stone brightens toward the heart, as if lit from inside, and each plane disagrees a little
    x, y, front = f.plane(*MH_HEART)
    d_heart = np.hypot(x, y) + (1 - np.clip(front, 0, 1)) * 1.6
    lit = np.exp(-(d_heart / 1.05) ** 2)
    tone = np.clip(0.12 + 0.72 * lit + 0.42 * (cid - 0.5) + 0.12 * F.fbm(P, 3.0, 3, seed=307), 0, 1)
    gem = F.ramp(tone, [(0.0, "1a0106"), (0.3, "4a040e"), (0.55, "8c0a18"), (0.8, "c81a1e"), (1.0, "ff5a2a")])
    gem = F.mix(gem, gem * 1.8 + 0.06, edge * 0.55)
    # the arteries, swelling toward the heart
    best = np.full(x.shape, 9.0)
    along = np.zeros(x.shape)
    for a in MH_ARTERIES:
        d, t = F.seg_dist(x, y, a)
        closer = d < best
        best = np.where(closer, d, best)
        along = np.where(closer, t, along)
    best = best + (front <= 0.05) * 9.0
    w = 0.024 * (1 - 0.62 * along) + 0.006
    art = 1 - F.sstep(w * 0.65, w, best)
    hot = F.ramp(np.clip(best / w, 0, 1), [(0.0, "fff0a0"), (0.4, "ffb02e"), (0.8, "ff5a12"), (1.0, "c81e06")])
    gem = gem + np.array((0.34, 0.05, 0.0)) * (np.exp(-(np.maximum(best - w, 0) / 0.07) ** 2) * (1 - art))[..., None]
    gem = F.mix(gem, hot, art)
    h_gem = (tilt + 0.03) * F.sstep(0.0, 0.05, wall) - 0.012 * art
    # the crust: black, in small scaled plates, pulled away at its edge
    f1, pl, pid = F.voronoi(P + warp, 6.5, seed=310, jitter=1.0, stretch=(1.0, 0.8, 1.0))
    grain = F.fbm(P, 12.0, 4, seed=311)
    crust = F.ramp(np.clip(0.3 + 0.5 * pid + 0.4 * grain, 0, 1), [(0.0, "070606"), (0.5, "151212"), (1.0, "2d2523")])
    gap = 1 - F.sstep(0.0, 0.05, pl)
    crust = F.mix(crust, F.ramp(np.clip(Vv / np.maximum(broken, 0.01), 0, 1), [(0.0, "230603"), (0.6, "6a1205"), (1.0, "e0420c")]), gap)
    h_crust = 0.075 + 0.034 * (pid - 0.5) + 0.012 * grain - 0.045 * gap
    col = F.mix(crust, gem, stone)
    height = h_gem * stone + h_crust * (1 - stone) + 0.03 * np.exp(-((Vv - broken) / 0.03) ** 2) * (1 - stone)
    col = F.mix(col, np.array((1.0, 0.36, 0.06)), np.exp(-((Vv - broken) / 0.006) ** 2) * 0.85)
    rough = F.mix(0.75 + 0.1 * grain, 0.12 + 0.2 * art, stone)
    return f, np.clip(col, 0, 1), np.clip(rough, 0, 1), np.zeros(f.S.shape), height


def mh_heart_material():
    """Fire turning inside a domed stone: hot at the middle, a slow swirl of molten bands, dark garnet at
    its rim."""
    g = Hm._Graph("MH_HeartStone")
    co = g.coords()
    wave = g.n("ShaderNodeTexNoise", **{"Scale": 3.0, "Detail": 5.0, "Roughness": 0.5, "Distortion": 2.2})
    g.link(co, wave.inputs["Vector"])
    geo = g.n("ShaderNodeNewGeometry")
    c, n = F.on(*MH_HEART), F.normal(*MH_HEART)
    facing = g.n("ShaderNodeVectorMath", operation="DOT_PRODUCT")
    g.link(geo.outputs["Normal"], facing.inputs[0])
    facing.inputs[1].default_value = tuple(W.rb(*n))
    # a ruby lit from inside: dark at its rim, deep red, then orange and one small hot point, the fire
    # only turning a little across those bands
    centre = g.math("MAXIMUM", facing.outputs["Value"], 0.0)
    v = g.math("ADD", g.math("POWER", centre, 2.2), g.math("MULTIPLY", g.math("SUBTRACT", wave.outputs["Fac"], 0.5), 0.34))
    col = g.ramp(v, [(0.0, (0.03, 0.0, 0.003)), (0.3, (0.2, 0.002, 0.006)), (0.58, (0.62, 0.012, 0.01)), (0.78, (1.0, 0.1, 0.01)), (0.92, (1.0, 0.42, 0.04)), (1.0, (1.0, 0.86, 0.36))])
    return g.finish(col, 0.09, 0.0)


def iron_material(name):
    g = Hm._Graph(name)
    n = g.n("ShaderNodeTexNoise", **{"Scale": 30.0, "Detail": 4.0})
    g.link(g.coords(), n.inputs["Vector"])
    col = g.ramp(n.outputs["Fac"], [(0.35, (0.03, 0.028, 0.03)), (0.65, (0.075, 0.07, 0.072))])
    col = g.ao(col, 0.05, 0.45)
    return g.finish(col, g.math("ADD", 0.34, g.math("MULTIPLY", n.outputs["Fac"], 0.24)), 0.65, g.bump(n.outputs["Fac"], 0.2, 0.004))


def mh_pieces(coll):
    garnet = F.gem_material("MH_Garnet", (0.06, 0.0, 0.006), (0.5, 0.004, 0.018), (1.0, 0.14, 0.09), pane_weight=0.12, panes=9.0)
    iron = iron_material("MH_Iron")
    c, n = F.on(*MH_HEART), F.normal(*MH_HEART)
    e1, e2 = O.frame(n)
    # the heart: a smooth dome, set in iron with six low claws
    h = Hm.Hi()
    rows = []
    R, dome = 0.34, 0.2
    for j in range(13):
        th = (math.pi / 2) * j / 12
        rows.append([h.v(c + n * (0.05 + dome * math.sin(th)) + (e1 * math.cos(TAU * k / 40) + e2 * math.sin(TAU * k / 40) * 1.08) * R * math.cos(th)) for k in range(40)])
    for j in range(12):
        for k in range(40):
            q = (k + 1) % 40
            h.f([rows[j][k], rows[j][q], rows[j + 1][q], rows[j + 1][k]], [(0, 0), (1, 0), (1, 1), (0, 1)])
    heart = F.fix_normals(h.object("MH_Heart", coll, [mh_heart_material()]))
    heart["w"] = 2.5
    s = Hm.Hi()
    O.disc_steps(s, c, n, [(0.3, -0.34), (0.42, -0.34), (0.42, 0.015), (0.385, 0.06), (0.355, 0.06), (0.34, 0.03)], sides=48)
    for k in range(6):
        a = TAU * (k + 0.5) / 6
        d = e1 * math.cos(a) + e2 * math.sin(a) * 1.08
        pts = [(c + d * (0.42 - 0.13 * t / 8) + n * (0.09 + 0.08 * math.sin(math.pi * t / 8 * 0.7)), (n + d * 0.3).normalized()) for t in range(9)]
        F.bar(s, pts, lambda t: 0.075 * (1 - 0.55 * t), 0.03, foot=0.03)
    # the crown's setting
    top = V((0, F.H, 0))
    up = V((0, 1, 0))
    O.disc_steps(s, top - up * 0.1, up, [(0.2, -0.06), (0.36, -0.03), (0.39, 0.05), (0.34, 0.12), (0.29, 0.12), (0.27, 0.08)], sides=40)
    setting = s.object("MH_Iron", coll, [iron], smooth=False)
    F.fix_normals(setting)
    for p in setting.data.polygons:
        p.use_smooth = False
    setting["w"] = 1.6
    # the crown: wide and low, a table-cut stone, never a point
    g = Hm.Hi()
    F.cut_gem(g, top + up * 0.03, up, (0, 0, 1), 0.28, 0.2, sides=8, base=0.12)
    for k, (s_, v_, r, roll) in enumerate(MH_SHARDS):
        p, nn = F.on(s_, v_, 0.008), F.normal(s_, v_)
        u = V((math.sin(roll), math.cos(roll), 0.2 * math.sin(roll * 2)))
        F.cut_gem(g, p, nn, u, r, r * 0.42, sides=5 + (k % 2), base=0.05, squash=0.72)
    gems = F.fix_normals(g.object("MH_Shards", coll, [garnet], smooth=False))
    gems["w"] = 3.0
    return [heart, setting, gems]


def mh_veins(coll):
    hi = Hm.Hi()
    fn = O.lay_on(*MH_HEART)
    for a in MH_ARTERIES:
        fine = W.catmull([(x, y, 0.0) for x, y in a], 7)
        pts = [fn(p[0], p[1], -0.002) for p in fine]
        F.prism(hi, pts, lambda t: 0.024 * (1 - 0.72 * t) + 0.004, height=lambda w: w * 0.4)
    return hi.object("MH_Veins", coll, [K.glow_material(MH_VEIN)], smooth=False, weld=0)


def magma_clay():
    coll = W.collection("MagmaHeartEggHi")
    f, col, rough, metal, height = magma_paint()
    shell = F.shell_mesh("MH_Shell", coll, 192, 120, height)
    pieces = mh_pieces(coll)
    v = mh_veins(coll)
    return {o.name: F.tris(o) for o in [shell, v] + pieces}


def magma_build():
    coll = W.collection("MagmaHeartEggHi")
    f, col, rough, metal, height = magma_paint()
    mat = F.shell_material("MH_Shell", col, rough, metal)
    pieces = mh_pieces(coll)
    v = mh_veins(coll)
    return F.assemble("MagmaHeartEgg", coll, mat, height, pieces, {MH_VEIN: [v]}, budget=4500, shell_frac=0.74, low_nu=84, low_nv=56, hard=25, shell_ext=0.1, shell_ray=0.24, ao_floor=0.62)


# ---------- Phoenix Ash Egg ----------
PH_FLAME = "ff5a14"
PH_HOT = "ffa21e"
PH_AT = (0.5, 0.5)


def ph_flame_outline():
    """The flame on the breast as one closed outline in the plane: a central tongue and two side
    tongues curling away from it, rising from a point at the bottom."""
    centre = [(0.0, -0.36), (0.1, -0.28), (0.15, -0.15), (0.11, -0.02), (0.16, 0.04), (0.19, -0.04), (0.25, 0.05), (0.27, 0.19), (0.22, 0.3), (0.2, 0.2), (0.14, 0.12), (0.1, 0.2), (0.07, 0.32),
              (0.03, 0.45), (0.0, 0.58), (-0.03, 0.45), (-0.07, 0.32), (-0.1, 0.2), (-0.14, 0.12), (-0.2, 0.2), (-0.22, 0.3), (-0.27, 0.19), (-0.25, 0.05), (-0.19, -0.04), (-0.16, 0.04), (-0.11, -0.02), (-0.15, -0.15), (-0.1, -0.28)]
    return centre


def phoenix_paint():
    f = F.Field()
    P, S, Vv = f.P, f.S, f.V
    # the scales: rows that get smaller toward the crown, each overlapping the row above it
    rows = 26.0
    t = (Vv ** 0.92) * rows
    row = np.floor(t)
    girth = np.maximum(np.sin(np.pi * np.clip(Vv, 0.02, 0.98)), 0.1)
    # scales per row: fewer near the poles, always a whole number so the row closes on itself
    count = np.maximum(np.round(30.0 * girth), 6.0)
    xs = S * count + 0.5 * (row % 2)
    cell = np.floor(xs)
    fx = xs - cell - 0.5                    # -0.5..0.5 across one scale
    fy = t - row                            # 0 at the scale's tip (below), 1 at its root
    # a pointed rounded tip: the scale's outline, with a ridge down its centre
    outline = np.abs(fx) * 2.0 - np.clip(fy * 1.6, 0, 1) ** 0.65
    body = 1 - F.sstep(-0.1, 0.02, outline)
    # height: rises toward its tip, so each lies over the row below
    h = (1 - fy) * 0.016 * body
    rib = 1 - F.sstep(0.0, 0.05, np.abs(fx))
    barb = 0.5 + 0.5 * np.sin((fy * 16.0 - np.abs(fx) * 26.0) * TAU * 0.5)
    h = h + 0.003 * rib * body + 0.0012 * barb * body
    height = h - 0.012 * (1 - body)
    # colour: crimson deep at the root of each scale, burning orange to pale gold toward its tip
    per = (np.sin((cell + row * 7.3) * 91.7) * 43758.5) % 1.0
    tipwards = np.clip((1 - fy) * 1.15 + (per - 0.5) * 0.25, 0, 1)
    col = F.ramp(tipwards, [(0.0, "3c0507"), (0.35, "7c0a0e"), (0.65, "bf1b10"), (0.88, "f0561a"), (1.0, "ffb54a")])
    col = col * (0.82 + 0.25 * rib[..., None])
    col = F.mix(np.array((0.05, 0.005, 0.005)), col, body)
    # ash: the lower scales burned darker, a soft smoke rising from the base
    ash = F.sstep(0.42, 0.05, Vv + F.fbm(P, 2.6, 3, seed=401) * 0.1)
    col = F.mix(col, col * np.array((0.3, 0.26, 0.26)), ash * 0.75)
    # the flame on the breast, raised in gold round a burning middle
    x, y, front = f.plane(*PH_AT)
    fl = ph_flame_outline()
    d, _ = F.seg_dist(x, y, fl, closed=True)
    # inside test: even-odd over the outline
    inside = np.zeros(x.shape, dtype=bool)
    pts = fl + fl[:1]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        crossing = ((ay > y) != (by > y)) & (x < (bx - ax) * (y - ay) / (by - ay + 1e-9) + ax)
        inside ^= crossing
    inside = inside & (front > 0.3)
    rim = (1 - F.sstep(0.012, 0.024, d)) * (front > 0.3)
    fill = inside * 1.0
    inner = F.ramp(np.clip((y + 0.36) / 0.9, 0, 1), [(0.0, "ffe89a"), (0.4, "ffae2e"), (0.8, "f05012"), (1.0, "9c1408")])
    col = F.mix(col, inner, fill)
    gold = F.mix(np.array((0.85, 0.58, 0.18)), np.array((1.0, 0.86, 0.44)), np.clip(0.5 + F.fbm(P, 20.0, 2, seed=402) * 0.7, 0, 1))
    col = F.mix(col, gold, rim)
    height = height * (1 - fill) * (1 - rim) + 0.012 * F.blur(fill, 2) + 0.024 * F.blur(rim, 1)
    rough = np.clip(0.34 - 0.08 * rib + 0.14 * ash + 0.0 * fill, 0.1, 1)
    metal = 0.85 * rim
    return f, np.clip(col, 0, 1), rough, metal, height


def ph_wrap(L, forward):
    """How much a feather must bend toward the egg to follow its curve for its length: a circle of
    the egg's radius falls away from its tangent by L^2 / 2R. `forward` says how much of the feather
    runs round the egg (those rising above the shoulder stay straighter)."""
    return -(L / (2 * F.R)) * 0.95 * forward


def ph_feathers(coll):
    feather = Hm.mat_feather("PH_Feather", base=(0.22, 0.004, 0.008), mid=(0.8, 0.022, 0.012), tip=(1.0, 0.2, 0.018))
    dark = Hm.mat_feather("PH_Covert", base=(0.12, 0.003, 0.006), mid=(0.42, 0.012, 0.012), tip=(0.95, 0.12, 0.016))
    wing, covert, crest = Hm.Hi(), Hm.Hi(), Hm.Hi()
    for side in (-1, 1):
        s0 = 0.5 + side * 0.34
        root = F.on(s0, 0.72)
        n = F.normal(s0, 0.72)
        toward = (F.on(0.5 + side * 0.29, 0.72) - root).normalized()
        up = n.cross(toward).normalized()
        if up.y < 0:
            up = -up
        # primaries: the long outer fan, wrapping round the egg with their tips lifting off it; the
        # uppermost rise above the shoulder and break the silhouette
        count = 12
        for k in range(count):
            t = k / (count - 1)
            a = math.radians(82 - 150 * t)
            L = 0.95 + 0.85 * math.sin(math.pi * (0.2 + 0.7 * t))
            forward = min(1.0, max(0.0, (math.radians(82) - a) / math.radians(42)))
            d = (toward * math.cos(a) + up * math.sin(a) + n * 0.12).normalized()
            b = root + d * 0.02 + n * (0.05 + 0.009 * k) + up * (0.15 - 0.42 * t)
            Hm.leaf(wing, b, d, n, L, 0.15 * (0.85 + 0.25 * math.sin(math.pi * t)), fold=0.16, curl=ph_wrap(L, forward) + 0.05, twist=-0.12 * side + 0.11 * ((k % 3) - 1), steps=14, across=4, shape=0.5)
        # secondaries: shorter, lying over the primaries' roots
        count = 9
        for k in range(count):
            t = k / (count - 1)
            a = math.radians(58 - 120 * t)
            L = 0.8 + 0.25 * math.sin(math.pi * t)
            forward = min(1.0, max(0.0, (math.radians(70) - a) / math.radians(40)))
            d = (toward * math.cos(a) + up * math.sin(a) + n * 0.1).normalized()
            b = root + d * 0.01 + n * (0.16 + 0.009 * k) + up * (0.12 - 0.3 * t)
            Hm.leaf(wing, b, d, n, L, 0.135, fold=0.14, curl=ph_wrap(L, forward) + 0.05, twist=-0.08 * side + 0.11 * ((k % 3) - 1), steps=11, across=4, shape=0.5)
        # coverts: a whole rosette of short feathers, overlapping all the way round the shoulder, so
        # the wing's root is feathered from behind as well as from in front
        for ring_, (count, reach, r0, phase) in enumerate(((13, 0.52, 0.2, 0.0), (9, 0.36, 0.27, 0.5), (5, 0.22, 0.32, 0.25))):
            for k in range(count):
                a = TAU * (k + phase) / count
                d = (toward * math.cos(a) + up * math.sin(a) + n * (0.12 + 0.1 * ring_)).normalized()
                b = root + d * 0.05 + n * (r0 + 0.008 * (k % 4))
                Hm.leaf(covert, b, d, n, reach, reach * 0.32, fold=0.12, curl=-0.14, twist=0.16 * ((k % 3) - 1), steps=8, across=4, shape=0.48)
    # the crest: a fan of plumes rising off the crown, broad enough to read from the front and
    # sweeping back at their tips
    for k, (x, L) in enumerate(((-0.42, 0.85), (-0.21, 1.2), (0.0, 1.45), (0.21, 1.2), (0.42, 0.85))):
        base = V((x * 0.22, F.H - 0.07, 0.0 + abs(x) * 0.02)) + V((0, 0, -0.004 * k))
        d = V((x * 0.95, 1.0, -0.2)).normalized()
        n = V((-x * 0.3, 0.2, 1.0))
        Hm.leaf(crest, base, d, n, L, 0.17 * (1.0 - abs(x) * 0.4), fold=0.2, curl=-0.3, twist=x * 0.6, steps=14, across=4, shape=0.56)
    for k, (x, L) in enumerate(((-0.3, 0.62), (0.0, 0.75), (0.3, 0.62))):
        base = V((x * 0.2, F.H - 0.03, 0.05))
        d = V((x * 1.0, 1.0, 0.1)).normalized()
        Hm.leaf(crest, base, d, (0, 0.1, 1.0), L, 0.11, fold=0.2, curl=-0.15, steps=10, across=4, shape=0.56)
    # the shoulders: a soft mound of down the feathers grow from, closing the gap to the shell
    mounds = []
    for side in (-1, 1):
        s0 = 0.5 + side * 0.34
        root, n = F.on(s0, 0.72), F.normal(s0, 0.72)
        mounds += [(root + n * 0.03, 0.22, (1.0, 1.0, 1.0))]
    g = Hm._Graph("PH_Down")
    grain = g.n("ShaderNodeTexNoise", **{"Scale": 40.0, "Detail": 4.0})
    g.link(g.coords(), grain.inputs["Vector"])
    down = g.finish(g.ramp(grain.outputs["Fac"], [(0.35, (0.1, 0.004, 0.006)), (0.65, (0.34, 0.016, 0.012))]), 0.7, 0.0, g.bump(grain.outputs["Fac"], 0.5, 0.01))
    mound = F.lobes("PH_Shoulders", coll, down, mounds, voxel=0.03)
    mound["w"] = 0.35
    a = wing.object("PH_Wings", coll, [feather])
    Hm.solidify(a, 0.012)
    a["w"] = 1.5
    b = covert.object("PH_Coverts", coll, [dark])
    Hm.solidify(b, 0.012)
    b["w"] = 1.0
    c = crest.object("PH_Crest", coll, [feather])
    Hm.solidify(c, 0.012)
    c["w"] = 1.4
    return a, b, c, mound


def ph_flame_glow(coll):
    hi = Hm.Hi()
    c, n = F.on(*PH_AT), F.normal(*PH_AT)
    e1 = V((0, 1, 0)).cross(n).normalized()
    e2 = n.cross(e1).normalized()

    def lay(x, y, off):
        q = c + e1 * x + e2 * y
        ss = (math.atan2(q.x, q.z) / TAU + 0.5) % 1.0
        vv = math.acos(max(-1, min(1, 1 - 2 * q.y / F.H))) / math.pi
        return F.on(ss, vv, off), F.normal(ss, vv)
    # the heart of the flame: a small tongue of fire inside the gold
    tongue = [(0.0, -0.22), (0.05, -0.16), (0.075, -0.05), (0.04, 0.07), (0.018, 0.2), (0.0, 0.32), (-0.018, 0.2), (-0.04, 0.07), (-0.075, -0.05), (-0.05, -0.16)]
    rim = [hi.v(lay(x, y, 0.016)[0]) for x, y in tongue]
    top = hi.v(lay(0, 0.0, 0.05)[0])
    for k in range(len(tongue)):
        hi.f([rim[k], rim[(k + 1) % len(tongue)], top], [(0, 0), (1, 0), (0, 1)])
    return F.fix_normals(hi.object("PH_Flame", coll, [K.glow_material(PH_HOT)], smooth=False, weld=0))


def phoenix_clay():
    coll = W.collection("PhoenixAshEggHi")
    shell = F.shell_mesh("PH_Shell", coll, 96, 64)
    a, b, c, m = ph_feathers(coll)
    g = ph_flame_glow(coll)
    return {o.name: F.tris(o) for o in (shell, a, b, c, m, g)}


def phoenix_build():
    coll = W.collection("PhoenixAshEggHi")
    f, col, rough, metal, height = phoenix_paint()
    mat = F.shell_material("PH_Scales", col, rough, metal)
    a, b, c, m = ph_feathers(coll)
    g = ph_flame_glow(coll)
    return F.assemble("PhoenixAshEgg", coll, mat, height, [a, b, c, m], {PH_HOT: [g]}, budget=10500, shell_frac=0.56, low_nu=56, low_nv=36, ao_floor=0.6)
