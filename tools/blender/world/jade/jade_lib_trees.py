"""jade_lib_trees: Jade Grove's tree species (2026-11-22). Each is its own construction with its own growth rule, not one generator re-seeded:

  A  JG_Tree_Aspire    tall and elegant: a slender silver trunk under a high, narrowing stack of ruffled leaf tiers (a spire of layered leaf)
  B  JG_Tree_Buttress  wide and ancient: a massive fluted trunk standing on seven exposed buttress fins, four limbs, a broad cumulus crown
  C  JG_Tree_Spiral    twisted, bamboo-inspired: three jointed culms wound round one another, each flaring into a fan of arching blades
  D  JG_Tree_Mistbough small understorey tree: twin leaning stems and a swept-back crown of pale new growth
  F  JG_Tree_Veil      a weeping tree: a low dome of leaf and long hanging veils (for the pools and the streams)
  E  JG_Tree_Guardian  the ancient guardian (jade_lib_guardian.py)

Variants (…_A1, _A2 …) differ in their construction parameters (tier count, lean, root layout), not only in a seed. Trunk bases sit at y = 0 with
the roots buried a little below. Colliders: one trunk cylinder per tree (the leaves never collide).
"""
import math
import random

from jade_lib_core import *  # noqa: F401,F403
import jade_lib_core as C

TAU = C.TAU


def _tier_mat(c, R, seed, top=0.5, pale=0.22):
    """Up-facing faces mid green, the underside and the hanging points deep jade, and broad soft patches of mist-pale new growth on the upper rim
    (low-frequency noise, so the patches read as light falling on new leaf and never as a checker)."""
    def choose(n, ctr):
        dx, dz = ctr[0] - c[0], ctr[2] - c[2]
        rr = math.hypot(dx, dz) / max(R, 0.1)
        if n[1] > top:
            patch = C.fbm3(ctr[0] * 0.09 + seed, ctr[1] * 0.09, ctr[2] * 0.09, seed, 2)
            if rr > 0.45 and patch > 0.30 - pale * 0.5:
                return "LeafPale" if n[1] > 0.74 else "LeafMid"
            return "LeafMid"
        if n[1] > -0.1 and ctr[1] > c[1] - 0.25 * R:
            return "LeafMid"
        return "LeafDeep"
    return choose


def _trunk_path(h0, h1, lean, n=6, sway=0.5, seed=0, phase=0.0):
    pts = []
    for k in range(n):
        t = k / float(n - 1)
        y = h0 + (h1 - h0) * t
        x = lean[0] * t * t + sway * math.sin(t * math.pi * 1.4 + phase) * t
        z = lean[1] * t * t + sway * 0.7 * math.cos(t * math.pi * 1.2 + phase) * t
        pts.append((x, y, z))
    return pts


def _root_fins(P, r0, n, reach, height, seed, mat="Root", fin=0.28, base_y=0.0):
    rnd = random.Random(seed)
    for i in range(n):
        a = TAU * i / n + rnd.uniform(-0.25, 0.25)
        ca, sa = math.cos(a), math.sin(a)
        rr = reach * rnd.uniform(0.8, 1.15)
        hh = height * rnd.uniform(0.8, 1.1)
        path = [(ca * r0 * 0.75, hh, sa * r0 * 0.75), (ca * (r0 + rr * 0.35), hh * 0.46 + 0.4, sa * (r0 + rr * 0.35)),
                (ca * (r0 + rr * 0.72), 0.55, sa * (r0 + rr * 0.72)), (ca * (r0 + rr), -0.35, sa * (r0 + rr))]
        g = C.tube(path, lambda t, hh=hh: max(0.4, hh * 0.5 * (1 - t) ** 1.1 + 0.34), lambda t: fin * (1.0 - 0.5 * t) + 0.18, 6, per=3, wob=0.1, seed=seed + i)
        P.put(g, mat)


# ======================================================================================================================
# A: Aspire
# ======================================================================================================================
def tree_aspire(name, seed=1, height=46.0, tiers=6, lean=(1.2, 0.5), rmax=8.4, first=0.38):
    rnd = random.Random(seed)
    P = C.Piece(name)
    top = height
    # the silver trunk: slender, a gentle S, flared at the foot, running up through the crown to a leader
    path = _trunk_path(-0.6, top, lean, 7, 0.45, seed, seed)

    def rad(t):
        h = t * (top + 0.6)
        return 1.2 * (1 - t) ** 0.7 * (1 + 0.95 * math.exp(-h / 1.5)) + 0.24
    P.put(C.tube(path, rad, rad, 9, per=3, wob=0.05, seed=seed), "TrunkPale")
    _root_fins(P, 1.0, 4, 2.3, 1.9, seed, "TrunkPale", 0.2)

    def axis_at(y):
        best = min(range(len(path) - 1), key=lambda i: abs(path[i][1] - y) + abs(path[i + 1][1] - y))
        a, b = path[best], path[best + 1]
        t = C.clamp((y - a[1]) / max(b[1] - a[1], 1e-6))
        return C.vlerp(a, b, t)
    for k in range(tiers):
        t = k / float(max(1, tiers - 1))
        y = top * first + (top * 0.93 - top * first) * (t ** 0.85)
        R = rmax * (1 - t * 0.8) * rnd.uniform(0.92, 1.06)
        ax = axis_at(y)
        c = (ax[0] + rnd.uniform(-0.5, 0.5), y, ax[2] + rnd.uniform(-0.5, 0.5))
        g = C.leaf_tier((0, 0, 0), R, R * 0.36 + 0.3, seg=16, lobes=rnd.choice((4, 5, 6)), ruffle=0.2, droop=0.62, seed=seed * 31 + k, flat=0.0, under=0.3, tip_len=(0.6, 1.25), bump=0.2)
        tl = (C.vnorm((rnd.uniform(-1, 1), 0.0, rnd.uniform(-1, 1))), rnd.uniform(0.07, 0.16))
        P.put(g, _tier_mat(c, R, seed + k), t=c, yaw=rnd.uniform(0, TAU), tilt=tl)
        if k < tiers - 2:
            R2 = R * 0.62
            g2 = C.leaf_tier((0, 0, 0), R2, R2 * 0.3 + 0.2, seg=12, lobes=4, ruffle=0.16, droop=0.7, seed=seed * 37 + k, flat=0.0, under=0.3, tip_len=(0.6, 1.2))
            c2 = (ax[0] + rnd.uniform(-0.4, 0.4), y - R * 0.34 - 1.0, ax[2] + rnd.uniform(-0.4, 0.4))
            P.put(g2, _tier_mat(c2, R2, seed + k + 5), t=c2, yaw=rnd.uniform(0, TAU), tilt=(tl[0], tl[1] * 0.8))
        if R > 2.4:
            for j in range(2):
                a = rnd.uniform(0, TAU)
                s0 = (ax[0], y - 1.4, ax[2])
                e = (c[0] + math.cos(a) * R * 0.5, y - 0.5 - R * 0.12, c[2] + math.sin(a) * R * 0.5)
                m = (C.lerp(s0[0], e[0], 0.5), y - 1.5 - R * 0.14, C.lerp(s0[2], e[2], 0.5))
                P.put(C.tube([s0, m, e], lambda t: 0.3 - 0.12 * t, None, 5, per=2), "TrunkPale")
    tip = axis_at(top)
    P.put(C.tube([(tip[0], top - 0.5, tip[2]), (tip[0] + 0.1, top + 2.4, tip[2] + 0.05)], lambda t: 0.26 - 0.18 * t, None, 5, per=2), "TrunkPale")
    P.cyl((0, 3.0, 0), 2.0, 6.0)
    return P


# ======================================================================================================================
# B: Buttress
# ======================================================================================================================
def tree_buttress(name, seed=2, fins=7, trunk_r=4.3, limbs=4, spread=1.0, hang=True):
    rnd = random.Random(seed)
    P = C.Piece(name)
    TH = 13.0
    # the fluted trunk: five lobes in section, swelling at the base, a waist, then the crown fork
    rings = []
    for k in range(10):
        t = k / 9.0
        y = -0.6 + (TH + 0.6) * t
        r = trunk_r * (1.18 - 0.4 * t + 0.2 * math.sin(t * math.pi * 2.0)) * (1 + 0.55 * math.exp(-y / 1.2))
        ring = []
        for i in range(14):
            a = TAU * i / 14
            w = 1.0 + 0.1 * math.sin(5 * a + seed) + 0.05 * C.noise3(a * 2 + seed, y * 0.4, 0.5, seed) + 0.07 * math.sin(3 * a + t * 3)
            ring.append((math.cos(a) * r * w + 0.3 * math.sin(t * 3.1) * t, y, math.sin(a) * r * w))
        rings.append(ring)
    trunk = C.loft(rings, True, True)

    def trunk_mat(n, ctr):
        if ctr[1] < 7.5 and n[1] > 0.0 and C.fbm3(ctr[0] * 0.16 + seed, ctr[1] * 0.16, ctr[2] * 0.16, seed, 2) > 0.12:
            return "Moss"
        return "Trunk"
    P.put(trunk, trunk_mat)
    # the exposed buttress fins, tall at the trunk, running out and down into the ground; mossy along their tops
    rnd2 = random.Random(seed + 5)
    for i in range(fins):
        a = TAU * i / fins + rnd2.uniform(-0.28, 0.28)
        ca, sa = math.cos(a), math.sin(a)
        reach = rnd2.uniform(11.0, 17.0)
        hh = rnd2.uniform(7.5, 10.5)
        r0 = trunk_r * 0.78
        path = [(ca * r0, hh, sa * r0), (ca * (r0 + reach * 0.28), hh * 0.52 + 0.9, sa * (r0 + reach * 0.28) + rnd2.uniform(-0.6, 0.6)),
                (ca * (r0 + reach * 0.62), 1.2, sa * (r0 + reach * 0.62) + rnd2.uniform(-0.8, 0.8)), (ca * (r0 + reach), -0.5, sa * (r0 + reach))]
        g = C.tube(path, lambda t, hh=hh: max(0.42, hh * 0.5 * (1 - t) ** 2.1 + 0.4), lambda t: 0.95 * (1 - 0.62 * t) + 0.2, 6, per=3, wob=0.08, seed=seed + i)

        def fin_mat(n, ctr, o=rnd2.random()):
            if n[1] > 0.5 and C.fbm3(ctr[0] * 0.14 + o * 9, ctr[1] * 0.14, ctr[2] * 0.14, seed + 3, 2) > -0.05:
                return "Moss"
            return "Root"
        P.put(g, fin_mat)
    # four limbs sweeping out of the fork, each carrying a pad of leaf; one big dome over the middle
    crown_y = TH - 0.5
    tips = []
    for i in range(limbs):
        a = TAU * i / limbs + rnd.uniform(-0.35, 0.35) + 0.5
        reach = rnd.uniform(10.0, 14.0) * spread
        rise = rnd.uniform(7.0, 11.0)
        ca, sa = math.cos(a), math.sin(a)
        s0 = (ca * 1.0, crown_y, sa * 1.0)
        m = (ca * reach * 0.48, crown_y + rise * 0.7, sa * reach * 0.48)
        e = (ca * reach, crown_y + rise, sa * reach)
        P.put(C.tube([s0, m, e], lambda t: 2.5 - 1.55 * t, None, 7, per=3, wob=0.05, seed=seed + i * 3), "Trunk")
        tips.append((e, a))
        # a secondary twig up inside the pad
        P.put(C.tube([e, (e[0] + ca * 2.5, e[1] + 3.5, e[2] + sa * 2.5)], lambda t: 0.9 - 0.5 * t, None, 5, per=2), "Trunk")
    for k, (e, a) in enumerate(tips):
        R = rnd.uniform(8.6, 10.4) * spread
        g = C.leaf_tier((0, 0, 0), R, R * 0.6, seg=16, lobes=rnd.choice((5, 6, 7)), ruffle=0.2, droop=0.46, seed=seed * 17 + k, flat=0.0, under=0.4, bump=0.22)
        c = (e[0], e[1] + 1.8, e[2])
        P.put(g, _tier_mat(c, R, seed + k, 0.45, 0.2), t=c, yaw=rnd.uniform(0, TAU))
        g2 = C.leaf_tier((0, 0, 0), R * 0.62, R * 0.4, seg=14, lobes=5, ruffle=0.2, droop=0.4, seed=seed * 19 + k, flat=0.0, under=0.3, bump=0.2)
        c2 = (e[0] - math.cos(a) * 2.5 * 0, e[1] + 5.3 + rnd.uniform(0, 1.2), e[2] - math.sin(a) * 0)
        P.put(g2, _tier_mat(c2, R * 0.62, seed + k + 9, 0.45, 0.3), t=c2, yaw=rnd.uniform(0, TAU))
    g = C.leaf_tier((0, 0, 0), 11.0 * spread, 7.0, seg=18, lobes=6, ruffle=0.18, droop=0.4, seed=seed * 23, flat=0.1, under=0.45, bump=0.22)
    c = (0.0, crown_y + 12.2, 0.0)
    P.put(g, _tier_mat(c, 11.0 * spread, seed + 20, 0.45, 0.22), t=c)
    # the trunk climbs on inside the middle dome
    P.put(C.tube([(0, crown_y - 1, 0), (0.2, crown_y + 6, 0), (0, crown_y + 11, 0)], lambda t: 2.4 - 1.6 * t, None, 8, per=3), "Trunk")
    P.cyl((0, 5.0, 0), trunk_r * 1.55, 10.0)
    return P


# ======================================================================================================================
# C: Spiral
# ======================================================================================================================
def tree_spiral(name, seed=3, culms=3, height=32.0, turns=1.15, spread=3.4, seg_len=3.0):
    rnd = random.Random(seed)
    P = C.Piece(name)
    for c_i in range(culms):
        phi0 = TAU * c_i / culms + rnd.uniform(-0.2, 0.2)
        hc = height * rnd.uniform(0.88, 1.08)
        # sample at node rings and between them
        n_seg = int(hc / seg_len)
        heights = [-0.5 - 0.07 * c_i]
        for s in range(n_seg + 1):
            hn = 1.4 + s * seg_len
            if hn > hc:
                break
            heights += [hn - 0.24, hn + 0.24, hn + seg_len * 0.55]
        heights = [h for h in heights if h <= hc]
        heights.append(hc)
        rings, node_rows = [], []
        for hi, h in enumerate(heights):
            t = max(0.0, h) / hc
            phi = phi0 + TAU * turns * t
            rho = 0.55 + spread * t ** 1.5
            cx, cz = math.cos(phi) * rho, math.sin(phi) * rho
            base = 0.62 * (1 - 0.5 * t) + 0.2
            is_node = any(abs(h - (1.4 + s * seg_len - 0.24)) < 0.01 or abs(h - (1.4 + s * seg_len + 0.24)) < 0.01 for s in range(n_seg + 2))
            r = base * (1.42 if is_node else 1.0) * (1 + 0.5 * math.exp(-max(h, 0) / 1.0))
            ring = [(cx + math.cos(TAU * k / 6) * r, h, cz + math.sin(TAU * k / 6) * r) for k in range(6)]
            rings.append(ring)
            node_rows.append(is_node)
        g = C.loft(rings, True, True)
        node_y = [1.4 + s * seg_len for s in range(n_seg + 2)]

        def culm_mat(n, ctr, node_y=node_y):
            return "CulmNode" if any(abs(ctr[1] - y) < 0.3 for y in node_y) else "Culm"
        P.put(g, culm_mat)
        # the fan: a plume of arching blades from the top, plus a lower tuft from the last two joints
        phi = phi0 + TAU * turns
        top = (math.cos(phi) * (0.55 + spread), hc, math.sin(phi) * (0.55 + spread))
        out = (math.cos(phi), 0.0, math.sin(phi))
        nb = 10 if culms <= 3 else 8
        for b in range(nb):
            a = TAU * b / nb + rnd.uniform(-0.2, 0.2)
            lift = rnd.uniform(0.4, 1.2)
            d = (math.cos(a) * 0.9 + out[0] * 0.3, lift, math.sin(a) * 0.9 + out[2] * 0.3)
            L = rnd.uniform(6.4, 8.2)
            P.put(C.blade(top, d, L, rnd.uniform(0.9, 1.2), droop=rnd.uniform(0.3, 0.55), thick=0.09, segs=3, mid=0.42, trough=0.2), "LeafMid" if b % 3 else "LeafPale")
        for b in range(3):
            a = TAU * b / 3 + rnd.uniform(0, 1)
            h0 = hc - seg_len * 1.1
            ph0 = phi0 + TAU * turns * (h0 / hc)
            bp = (math.cos(ph0) * (0.55 + spread * (h0 / hc) ** 1.5), h0, math.sin(ph0) * (0.55 + spread * (h0 / hc) ** 1.5))
            P.put(C.blade(bp, (math.cos(a), 0.55, math.sin(a)), rnd.uniform(3.4, 4.6), 0.55, droop=0.4, thick=0.07, segs=2), "LeafMid")
    # the root bulb: the three culms rise out of a knot of low roots
    for b in range(5):
        a = TAU * b / 5 + 0.3
        P.put(C.tube([(math.cos(a) * 0.9, 1.4, math.sin(a) * 0.9), (math.cos(a) * 2.2, 0.6, math.sin(a) * 2.2), (math.cos(a) * 3.4, -0.25, math.sin(a) * 3.4)],
                     lambda t: 0.62 - 0.28 * t, 0.5, 6, per=3), "Root")
    P.cyl((0, 3.0, 0), 3.2, 6.0)
    return P


# ======================================================================================================================
# D: Mistbough
# ======================================================================================================================
def tree_mistbough(name, seed=4, height=11.5, lean=1.0):
    """A windswept understorey tree: a main stem and a thinner twin leaning hard to one side, the crown a swept-back run of ragged leaf clouds
    stepping down along the lean (big at the stem, smaller toward the tips), pale new growth on top."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    sgn = 1.0 if lean >= 0 else -1.0
    L = abs(lean)
    main = [(0.0, -0.5, 0.0), (0.7 * sgn * L, height * 0.3, 0.2), (2.1 * sgn * L, height * 0.62, 0.0), (4.1 * sgn * L, height * 0.86, -0.3)]
    twin = [(0.5, -0.4, 0.4), (1.0 * sgn * L, height * 0.26, 1.0), (2.2 * sgn * L, height * 0.46, 1.9)]
    P.put(C.tube(main, lambda t: 0.62 * (1 - 0.62 * t) + 0.15, None, 7, per=3, wob=0.06, seed=seed), "TrunkPale")
    P.put(C.tube(twin, lambda t: 0.42 * (1 - 0.55 * t) + 0.14, None, 6, per=3, wob=0.06, seed=seed + 1), "Trunk")
    _root_fins(P, 0.5, 3, 1.6, 1.0, seed, "Root", 0.18)
    P.put(C.tube([(1.3 * sgn * L, height * 0.45, 0.1), (3.4 * sgn * L, height * 0.5, -1.7), (5.4 * sgn * L, height * 0.46, -2.6)], lambda t: 0.3 - 0.13 * t, None, 5, per=2), "Trunk")
    clouds = [((2.1 * sgn * L, height * 0.82, 0.0), 4.6), ((4.6 * sgn * L, height * 0.93, -0.5), 3.6), ((2.6 * sgn * L, height * 0.52, 2.0), 3.0), ((5.6 * sgn * L, height * 0.58, -2.6), 2.8),
              ((0.2 * sgn, height * 0.7, -1.6), 2.5)]
    for k, (c, R) in enumerate(clouds):
        g = C.leaf_tier((0, 0, 0), R, R * 0.5, seg=14, lobes=rnd.choice((3, 4, 5)), ruffle=0.26, droop=0.55, seed=seed * 13 + k, flat=0.1, under=0.4, tip_len=(0.5, 1.1), bump=0.25)
        P.put(g, _tier_mat(c, R, seed + k, 0.4, 0.5), t=c, yaw=rnd.uniform(0, TAU), tilt=((0, 0, 1), -0.2 * sgn + rnd.uniform(-0.08, 0.08)))
    P.cyl((0.3, 2.5, 0.1), 1.7, 5.0)
    return P


# ======================================================================================================================
# F: Veil
# ======================================================================================================================
def tree_veil(name, seed=5, strands=30, crown_r=8.5, trunk_h=9.0):
    rnd = random.Random(seed)
    P = C.Piece(name)
    path = [(0.0, -0.5, 0.0), (0.5, trunk_h * 0.4, 0.2), (-0.2, trunk_h * 0.8, -0.3), (0.0, trunk_h + 1.0, 0.0)]
    P.put(C.tube(path, lambda t: 1.9 * (1 - 0.45 * t) + 0.2 + 1.2 * math.exp(-t * 14), None, 9, per=3, wob=0.07, seed=seed), "Trunk")
    _root_fins(P, 1.6, 5, 3.6, 2.6, seed, "Root", 0.3)
    # three limbs arching out, the leaf dome over them
    for i in range(3):
        a = TAU * i / 3 + 0.4
        e = (math.cos(a) * crown_r * 0.7, trunk_h + 3.4, math.sin(a) * crown_r * 0.7)
        P.put(C.tube([(0, trunk_h, 0), (math.cos(a) * crown_r * 0.35, trunk_h + 3.6, math.sin(a) * crown_r * 0.35), e], lambda t: 1.0 - 0.55 * t, None, 6, per=3), "Trunk")
    for k, (r, y, off) in enumerate(((crown_r, trunk_h + 4.2, (0, 0)), (crown_r * 0.62, trunk_h + 7.6, (0.6, -0.4)))):
        g = C.leaf_tier((0, 0, 0), r, r * 0.42, seg=18, lobes=6, ruffle=0.16, droop=0.3, seed=seed * 11 + k, flat=0.05, under=0.35, bump=0.2)
        c = (off[0], y, off[1])
        P.put(g, _tier_mat(c, r, seed + k, 0.4, 0.3), t=c, yaw=rnd.uniform(0, TAU))
    # long hanging veils from the rim: thin blades falling nearly to the ground
    for s in range(strands):
        a = TAU * s / strands + rnd.uniform(-0.1, 0.1)
        rr = crown_r * rnd.uniform(0.7, 0.86)
        base = (math.cos(a) * rr, trunk_h + 4.4 - rnd.uniform(0.0, 0.3), math.sin(a) * rr)
        L = rnd.uniform(8.0, 11.4)
        d = (math.cos(a) * 0.16, -1.0, math.sin(a) * 0.16)
        P.put(C.blade(base, d, L, rnd.uniform(0.3, 0.46), droop=0.0, thick=0.06, segs=3, mid=0.28, up=(0.0, 0.0, 1.0) if abs(math.sin(a)) < 0.7 else (1.0, 0.0, 0.0), base_w=0.5, sweep=rnd.uniform(-0.2, 0.2)), "LeafMid" if s % 3 else "LeafPale")
    P.cyl((0, 3.0, 0), 3.0, 6.0)
    return P


# ======================================================================================================================
def build_all():
    out = {}
    out["JG_Tree_Aspire_A1"] = tree_aspire("JG_Tree_Aspire_A1", seed=11, height=46, tiers=6, lean=(1.4, 0.6), rmax=7.2)
    out["JG_Tree_Aspire_A2"] = tree_aspire("JG_Tree_Aspire_A2", seed=29, height=38, tiers=5, lean=(-1.0, 1.1), rmax=6.2, first=0.36)
    out["JG_Tree_Buttress_B1"] = tree_buttress("JG_Tree_Buttress_B1", seed=31, fins=6, trunk_r=4.3, limbs=4)
    out["JG_Tree_Buttress_B2"] = tree_buttress("JG_Tree_Buttress_B2", seed=47, fins=6, trunk_r=3.7, limbs=3, spread=0.85)
    out["JG_Tree_Spiral_C1"] = tree_spiral("JG_Tree_Spiral_C1", seed=57, culms=3, height=32)
    out["JG_Tree_Spiral_C2"] = tree_spiral("JG_Tree_Spiral_C2", seed=61, culms=4, height=24, turns=0.8, spread=3.6)
    out["JG_Tree_Mistbough_D1"] = tree_mistbough("JG_Tree_Mistbough_D1", seed=71, height=11.5, lean=1.0)
    out["JG_Tree_Mistbough_D2"] = tree_mistbough("JG_Tree_Mistbough_D2", seed=83, height=9.5, lean=-0.8)
    out["JG_Tree_Veil_F1"] = tree_veil("JG_Tree_Veil_F1", seed=91)
    return C.apply_merges(out)


if __name__ == "__main__":
    for n, p in build_all().items():
        b = p.bounds()
        bad = {m: g.open_edges() for m, g in p.g.items()}
        print("%-26s %5d tris  box %s -> %s  %s" % (n, p.tris(), tuple(round(v, 1) for v in b[0]), tuple(round(v, 1) for v in b[1]), p.stats()))
