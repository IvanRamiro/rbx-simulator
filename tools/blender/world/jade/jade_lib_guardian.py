"""jade_lib_guardian: E, the ancient guardian tree of Jade Grove, and its shrine (2026-11-22).

It REPLACES the Elder Jade Tree on its knoll (the first foundation's JG_ElderTrunk / ElderBranches / ElderPads / ElderCanopy and the four
JG_TreeShelf pieces) and KEEPS ITS FUNCTIONS, because the Grove Heart and the Jade Seed relics and the Qinggong climb depend on them:
  - the tree's axis, its base level (the knoll's ground 5.78 less 0.5), the trunk's outer radius at every shelf height;
  - a walk-in hollow at its foot with the Grove Heart at the axis, 3.0 over the base;
  - four climbing shelves at the old positions and yaws (flat tops at the old heights), reaching the first branch deck;
  - five branch decks (flat tops, same centres and heights as the old leaf-cloud tiers) and the crown nest with the Jade Seed 3.0 over it.
All of those numbers are the old module's own (jade_meshes.py: EX/EZ, trunk_axis, trunk_radius, BRANCHES, CROWN_PAD) copied here; the numeric
check (jade_lib_verify.py) reads the old placements file and proves each one.

Frame: origin = the tree's axis at its base level (island-local (48.825, 5.278, -91.827) once placed, no turn). y up.
Pieces: JG_Tree_Guardian (trunk, root pillars, buttress roots, branches, hanging roots), JG_Tree_GuardianCrown (the decks and leaf masses),
JG_Tree_GuardianShelf (the climbing fungus shelf, placed four times),
JG_Tree_GuardianShrine (the stone dais and niche in the hollow). The landmark is allowed a larger budget than a forest tree (see the note).
"""
import math
import random

import jade_lib_core as C

TAU = C.TAU
PILLAR_RING, TRUNK_BASE = 7.0, 12.0
CROWN_PAD = 58.6
PAD_R, CROWN_R = 7.5, 8.5
BRANCHES = [(0.4, 30, 18, 8), (2.1, 34, 20, 9), (3.6, 38, 17, 10), (4.9, 42, 16, 9), (1.3, 46, 14, 9)]     # angle, height on trunk, reach, rise
SHELVES = [(13, 2.6), (22, 3.9), (30.5, 5.0), (38, 0.0)]                                                      # height, angle (the old spiral)
# island-local placement of the tree's origin
ORIGIN = (48.82504252973265, 5.277805083778704, -91.8265496573284)


def axis(h):
    """The trunk's axis at height h above the base (relative to the origin): a gentle lean and twist."""
    t = h / 60.0
    return (2.5 * math.sin(t * 2.2) * t, -1.8 * t * t)


def trunk_radius(h):
    if h <= TRUNK_BASE:
        return 9.0
    if h <= 40:
        return 9.0 - 5.0 * (h - TRUNK_BASE) / (40 - TRUNK_BASE)
    return max(1.6, 4.0 - 2.4 * (h - 40) / 18)


def branch_end(angle, h, reach, rise):
    ax, az = axis(h)
    return (ax + math.cos(angle) * reach, h + rise, az + math.sin(angle) * reach)


def deck_top(b):
    return b[1] + b[3] + 1.2


def shelf_pose(h, ang):
    """The shelf's walkable-top centre point on the trunk and its yaw, exactly the old climb_shelves()."""
    ax, az = axis(h)
    r = trunk_radius(h) + 0.3
    return (ax + math.cos(ang) * r, h, az + math.sin(ang) * r), -ang


def crown_centre():
    ax, az = axis(58)
    return (ax, CROWN_PAD, az)


# ----------------------------------------------------------------------------------------------------------------------
def _bark(seed, top=0.5):
    def choose(n, ctr):
        if n[1] > top and C.fbm3(ctr[0] * 0.12 + seed, ctr[1] * 0.12, ctr[2] * 0.12, seed, 2) > -0.1:
            return "Moss"
        if ctr[1] < 13 and n[1] > 0.1 and C.fbm3(ctr[0] * 0.2 + seed, ctr[1] * 0.2, ctr[2] * 0.2, seed + 3, 2) > 0.05:
            return "Moss"
        return "Trunk"
    return choose


def build_tree(name="JG_Tree_Guardian", seed=7):
    rnd = random.Random(seed)
    P = C.Piece(name)
    # ---- the three root pillars round the hollow, each a swelling column that leans into the trunk's underside ----
    for k in range(3):
        a = TAU * k / 3
        ca, sa = math.cos(a), math.sin(a)
        foot = (ca * (PILLAR_RING + 4.0), -2.0, sa * (PILLAR_RING + 4.0))
        mid = (ca * (PILLAR_RING + 0.2), 4.5, sa * (PILLAR_RING + 0.2))
        top = (ca * (PILLAR_RING - 1.4), TRUNK_BASE + 2.0, sa * (PILLAR_RING - 1.4))
        g = C.tube([foot, mid, top], lambda t: 3.8 - 0.5 * t, lambda t: 3.8 - 0.5 * t, 11, per=4, wob=0.07, seed=seed + k)
        P.put(g, _bark(seed + k, 0.4))
    # ---- the fused trunk above: five flutes in section, a lumpy waist, narrowing to the crown; its underside is the hollow's domed ceiling ----
    rings = []
    heights = [10.2, 11.3, 12.4] + [TRUNK_BASE + 0.5 + 3.4 * k for k in range(1, 14)] + [58.0]
    for hi, h in enumerate(heights):
        ax, az = axis(max(h, 12.5))
        r = trunk_radius(max(h, 12.5))
        shrink = 1.0
        if h < 12.4:
            shrink = {10.2: 0.2, 11.3: 0.62}.get(h, 0.0)
        ring = []
        for i in range(15):
            a = TAU * i / 15
            flute = 1.0 + 0.055 * math.sin(5 * a + h * 0.08) + 0.04 * C.noise3(a * 1.3 + seed, h * 0.13, 0.5, seed) + 0.03 * math.sin(3 * a - h * 0.05)
            rr = r * flute * shrink if h >= 12.4 else (PILLAR_RING - 0.3) * 0.0 + r * flute * shrink
            ring.append((ax + math.cos(a) * rr, h, az + math.sin(a) * rr))
        rings.append(ring)
    trunk = C.loft(rings, True, True)
    P.put(trunk, _bark(seed + 9, 0.55))
    # ---- buttress roots: two arch high enough to walk under, the rest hug the ground ----
    for k, (ang, reach, arch, thick) in enumerate(((math.pi - 0.5, 21, 9.0, 2.6), (0.25, 18, 1.8, 3.2), (1.0, 17, 1.4, 3.4), (1.9, 17, 1.5, 3.2),
                                                  (2.6, 16, 1.2, 3.0), (-0.8, 17, 1.6, 3.4), (-1.7, 16, 1.4, 3.2), (-2.6, 15, 1.2, 3.0))):
        sx, sz = math.cos(ang) * 8.6, math.sin(ang) * 8.6
        ex, ez = math.cos(ang) * reach, math.sin(ang) * reach
        mx, mz = sx * 0.55 + ex * 0.45, sz * 0.55 + ez * 0.45
        pts = [(sx, 5 + arch * 0.5, sz), (mx, arch + 1.5, mz), (ex, -0.6, ez)]
        g = C.tube(pts, lambda t, th=thick: th - (th - 0.9) * t, lambda t, th=thick: th * 0.9 - (th * 0.9 - 0.8) * t, 8, per=4, wob=0.06, seed=seed + 20 + k)

        def root_mat(n, ctr, o=rnd.random()):
            return "Moss" if n[1] > 0.45 and C.fbm3(ctr[0] * 0.14 + o * 9, ctr[1] * 0.14, ctr[2] * 0.14, seed + 5, 2) > -0.15 else "Root"
        P.put(g, root_mat)
    # ---- the five branches that carry the decks ----
    for k, b in enumerate(BRANCHES):
        ang, h, reach, rise = b
        ax, az = axis(h)
        r0 = trunk_radius(h) * 0.8
        start = (ax + math.cos(ang) * r0 * 0.5, h, az + math.sin(ang) * r0 * 0.5)
        mid = (ax + math.cos(ang) * reach * 0.55, h + rise * 0.3, az + math.sin(ang) * reach * 0.55)
        end = branch_end(*b)
        P.put(C.tube([start, mid, (end[0], end[1] - 0.6, end[2])], lambda t: 3.0 - 1.9 * t, None, 9, per=4, wob=0.05, seed=seed + 40 + k), _bark(seed + 40 + k, 0.5))
    # the crown nest is carried on the trunk's own top: a last stubby fork
    cx, cy, cz = crown_centre()
    P.put(C.tube([(cx, cy - 4.0, cz), (cx, cy - 0.5, cz)], lambda t: 1.9 - 0.4 * t, None, 8, per=2), "Trunk")
    # ---- colliders: pillars, the trunk's column, in studs (cylinders; decor never collides, these do) ----
    for k in range(3):
        a = TAU * k / 3
        P.cyl((math.cos(a) * PILLAR_RING, 7.0, math.sin(a) * PILLAR_RING), 6.8, 14.0)
    for (h0, h1) in ((12.0, 26.0), (26.0, 40.0), (40.0, 58.0)):
        hm = (h0 + h1) / 2
        ax, az = axis(hm)
        P.cyl((ax, hm, az), 2 * trunk_radius(h0 + (h1 - h0) * 0.7) - 1.0, h1 - h0)
    hang_from_trunk(P)
    return P


# ----------------------------------------------------------------------------------------------------------------------
def deck(c, R, seed, sink=0.0):
    """A walkable leaf deck: a perfectly flat top disc (0.72 R across) at y = 0 and a ruffled rim, a fringe of hanging leaf points and a dished
    underside. One closed shell, y = 0 the walking surface."""
    rnd = random.Random(seed)
    seg = 18
    ph, ph2 = rnd.uniform(0, TAU), rnd.uniform(0, TAU)
    lobes = rnd.choice((5, 6, 7))
    jit = [rnd.uniform(-1, 1) for _ in range(seg)]
    tipk = [rnd.uniform(0.55, 1.0) if i % 2 == 0 else rnd.uniform(0.0, 0.2) for i in range(seg)]
    prof = [(0.0, -3.0), (0.45, -3.2), (0.9, -2.2), (1.0, -1.1), (0.92, -0.36), (0.74, 0.0), (0.0, 0.0)]
    rings = []
    for k, (r, y) in enumerate(prof):
        ring = []
        for i in range(seg):
            th = TAU * i / seg
            w = 1.0 + 0.17 * math.sin(lobes * th + ph) + 0.08 * math.sin((2 * lobes + 1) * th + ph2) + 0.06 * jit[i] if 0 < k < 5 else 1.0
            rr = r * R * w
            yy = y
            if k == 2:
                yy = y - 3.6 * tipk[i]
            if k == 5:
                w = 1.0   # the flat top is an exact disc
                rr = r * R
            ring.append((c[0] + math.cos(th) * rr, c[1] + yy, c[2] + math.sin(th) * rr))
        rings.append(ring)
    return C.loft(rings, True, True)


def _deck_mat(c, R, seed):
    def choose(n, ctr):
        if n[1] > 0.93 and abs(ctr[1] - c[1]) < 0.05:
            return "Moss"                                   # the walkable top is moss
        if n[1] > 0.4:
            p = C.fbm3(ctr[0] * 0.1 + seed, ctr[1] * 0.1, ctr[2] * 0.1, seed, 2)
            return "LeafPale" if p > 0.3 else "LeafMid"
        if n[1] > -0.1:
            return "LeafMid"
        return "LeafDeep"
    return choose


def build_crown(name="JG_Tree_GuardianCrown", seed=8):
    rnd = random.Random(seed)
    P = C.Piece(name)
    decks = []
    for k, b in enumerate(BRANCHES):
        e = branch_end(*b)
        decks.append(((e[0], deck_top(b), e[2]), PAD_R, b))
    decks.append((crown_centre(), CROWN_R, None))
    for k, (c, R, b) in enumerate(decks):
        P.put(deck(c, R, seed * 11 + k), _deck_mat(c, R, seed + k))
        # a walkable deck collides as a cylinder: top at the deck's top, 1.2 thick, a little wider than its flat top
        P.cyl((c[0], c[1] - 0.6, c[2]), 2 * R * 0.76, 1.2)
        # leaf masses hang under and beside the deck, never above its walkable top
        for j in range(5):
            a = TAU * j / 5 + rnd.uniform(-0.5, 0.5) + k
            d = rnd.uniform(0.7, 1.05) * R
            Rj = rnd.uniform(3.4, 4.8)
            cj = (c[0] + math.cos(a) * d, c[1] - rnd.uniform(1.6, 3.4), c[2] + math.sin(a) * d)
            g = C.leaf_tier((0, 0, 0), Rj, Rj * 0.4, seg=10, lobes=rnd.choice((3, 4)), ruffle=0.2, droop=0.6, seed=seed * 7 + k * 5 + j, flat=0.2, under=0.4, bump=0.18)
            P.put(g, _deck_mat(cj, Rj, seed + j + k * 3), t=(cj[0], min(cj[1], c[1] - 1.4), cj[2]), yaw=rnd.uniform(0, TAU))
    cx, cy, cz = crown_centre()
    # three slender limbs rise from the crown nest's rim to carry the high canopy (outside the standing area, nothing at the axis: the Jade Seed
    # floats there)
    for k in range(3):
        a = TAU * k / 3 + 0.5
        ca, sa = math.cos(a), math.sin(a)
        pts = [(cx + ca * 6.6, cy - 3.0, cz + sa * 6.6), (cx + ca * 8.6, cy + 3.5, cz + sa * 8.6), (cx + ca * 6.4, cy + 9.5, cz + sa * 6.4), (cx + ca * 3.0, cy + 12.8, cz + sa * 3.0)]
        P.put(C.tube(pts, lambda t: 1.35 - 0.65 * t, None, 8, per=3, wob=0.05, seed=seed + 60 + k), "Trunk")
    # the high canopy: broad leaf domes well above the crown nest, so the tree has a crown from far off and nobody's view is shut
    cc = crown_centre()
    for j, (dx, dz, dy, R) in enumerate(((0.0, 0.0, 12.5, 13.0), (-10.5, 4.0, 7.0, 8.4), (9.0, -6.0, 9.0, 8.8), (3.0, 11.0, 6.4, 7.6))):
        g = C.leaf_tier((0, 0, 0), R, R * 0.52, seg=18, lobes=rnd.choice((5, 6, 7)), ruffle=0.2, droop=0.4, seed=seed * 19 + j, flat=0.0, under=0.5, bump=0.22)
        c = (cc[0] + dx, cc[1] + dy, cc[2] + dz)
        P.put(g, _deck_mat(c, R, seed + 40 + j), t=c, yaw=rnd.uniform(0, TAU))
    hang_from_decks(P)
    return P


def hang_from_decks(P, seed=9):
    """Aerial roots: long cords hanging from the undersides of the decks, some reaching the ground, some stopping short."""
    rnd = random.Random(seed)
    for b in BRANCHES:
        e = branch_end(*b)
        for j in range(6):
            a = rnd.uniform(0, TAU)
            d = rnd.uniform(2.0, 7.0)
            x, z = e[0] + math.cos(a) * d, e[2] + math.sin(a) * d
            top = (x, e[1] + 0.2 - rnd.uniform(0.2, 1.4), z)          # inside the deck's body (its underside is 1.1 to 4 below the top)
            length = rnd.choice((14, 20, 28, 36, top[1] + 0.6)) if j < 5 else top[1] + 0.6
            length = min(length, top[1] + 0.6)
            sway = rnd.uniform(-1.4, 1.4)
            pts = [top, (x + sway * 0.4, top[1] - length * 0.35, z + sway * 0.2), (x + sway, top[1] - length * 0.7, z - sway * 0.3), (x + sway * 0.6, top[1] - length, z + sway * 0.4)]
            P.put(C.tube(pts, lambda t: 0.34 - 0.16 * t, None, 4, per=2), "Root")


def hang_from_trunk(P, seed=9):
    """Strands off the trunk's mid heights (they start inside the bark)."""
    rnd = random.Random(seed + 1)
    for k in range(8):
        a = TAU * k / 8 + rnd.uniform(-0.2, 0.2)
        h = rnd.uniform(15, 26)
        ax, az = axis(h)
        r = trunk_radius(h)
        top = (ax + math.cos(a) * (r - 0.6), h, az + math.sin(a) * (r - 0.6))
        out = (math.cos(a), math.sin(a))
        length = top[1] + 0.6
        pts = [top, (top[0] + out[0] * 1.6, top[1] - length * 0.4, top[2] + out[1] * 1.6), (top[0] + out[0] * 1.9, top[1] - length * 0.75, top[2] + out[1] * 1.9),
               (top[0] + out[0] * 2.2, -0.6, top[2] + out[1] * 2.2)]
        P.put(C.tube(pts, lambda t: 0.4 - 0.2 * t, None, 4, per=2), "Root")


def build_shelf(name="JG_Tree_GuardianShelf", seed=10):
    """The climbing shelf: a squarish bracket fungus whose walkable top (flat, y = 0) opens along +X from the trunk surface point (the origin); it
    reaches 1.8 into the trunk so it never floats. Collider: the box that sits inside its outline."""
    P = C.Piece(name)
    ax_x, ax_z, cx = 3.7, 4.1, 1.9
    seg = 20

    def outline(scale, k=3.0):
        pts = []
        for i in range(seg):
            a = TAU * i / seg
            ca, sa = math.cos(a), math.sin(a)
            x = ax_x * scale * math.copysign(abs(ca) ** (2.0 / k), ca)
            z = ax_z * scale * math.copysign(abs(sa) ** (2.0 / k), sa)
            pts.append((cx + x, z))
        return pts
    prof = [(0.0, -2.4, 0.0), (0.45, -2.1, 0.0), (0.88, -1.3, 0.0), (1.07, -0.5, 0.0), (1.0, -0.15, 0.0), (0.9, 0.0, 0.0)]
    rings = []
    for k, (s, y, _) in enumerate(prof):
        o = outline(s) if s > 0 else [(cx, 0.0)] * seg
        rings.append([(x, y, z) for (x, z) in o])
    # the top: a flat disc ring and its centre
    top = [(x, 0.0, z) for (x, z) in outline(0.9)]
    rings = [rings[0], rings[1], rings[2], rings[3], rings[4], top]
    g = C.loft(rings, True, True)

    def mat(n, ctr):
        if n[1] > 0.9:
            return "Moss"
        if ctr[1] > -0.9 and n[1] > -0.3:
            return "CapPale"
        return "Trunk"
    P.put(g, mat)
    P.box((cx, -0.6, 0.0), (5.8, 1.2, 6.4))
    return P


def build_shrine(name="JG_Tree_GuardianShrine", seed=12):
    """The hollow's shrine: a low round stone dais with two steps under the relic, a ring of jade inlay, and a little roofed stone niche on the
    hollow's back wall (a gable of stone slabs, an offering bowl with an amber ember). Origin = the axis at the base level; the dais top is 0.8."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    P.put(C.lathe([(0.0, -0.9), (3.3, -0.9), (3.3, 0.28), (3.05, 0.34), (3.0, 0.55), (2.2, 0.62), (2.0, 0.8), (0.0, 0.8)], 18, mod=lambda th, k: 1.0 + 0.035 * math.sin(5 * th + k)), "StoneDark")
    P.put(C.lathe([(2.05, 0.79), (2.05, 0.83), (1.75, 0.83), (1.75, 0.79)], 24), "Jade")
    for i in range(7):
        a = TAU * i / 7 + 0.2
        P.put(C.chunk((math.cos(a) * 3.15, 0.15, math.sin(a) * 3.15), (1.3, 0.9, 0.7), seed + i, 0.1, yaw=-a), "Stone")
    # the niche on the back wall (toward -X, where the trunk's wall is): two side slabs, a back slab, two roof slabs
    nx, nz = -3.0, -0.0
    P.put(C.chunk((nx, 1.0, nz - 1.05), (1.7, 2.0, 0.5), seed + 20, 0.05), "Stone")
    P.put(C.chunk((nx, 1.0, nz + 1.05), (1.7, 2.0, 0.5), seed + 21, 0.05), "Stone")
    P.put(C.chunk((nx - 0.75, 1.0, nz), (0.4, 2.0, 1.8), seed + 22, 0.04), "StoneDark")
    P.put(C.chunk((nx, 2.35, nz - 0.62), (2.1, 0.32, 1.5), seed + 23, 0.02, tilt=((1, 0, 0), 0.38)), "Stone")
    P.put(C.chunk((nx, 2.35, nz + 0.62), (2.1, 0.32, 1.5), seed + 24, 0.02, tilt=((1, 0, 0), -0.38)), "Stone")
    P.put(C.chunk((nx + 0.1, 2.12, nz), (2.0, 0.22, 0.34), seed + 25, 0.02), "Moss")
    P.put(C.lathe([(0.0, 0.0), (0.5, 0.0), (0.62, 0.28), (0.0, 0.28)], 10), "RockDark", t=(nx + 0.2, 0.0, nz))
    P.put(C.ellipsoid((nx + 0.2, 0.36, nz), (0.2, 0.14, 0.2), 6, 4), "GlowAmber")
    # the collider: the dais (the relic floats over it) and the niche
    P.cyl((0, -0.05, 0), 6.6, 1.7)
    P.box((nx - 0.3, 1.0, nz), (2.2, 2.0, 2.8))
    return P


def scene():
    """The assembled tree for review: (piece, position, yaw, scale)."""
    built = build_all()
    out = [(built["JG_Tree_Guardian"], (0, 0, 0), 0.0, 1.0), (built["JG_Tree_GuardianCrown"], (0, 0, 0), 0.0, 1.0),
           (built["JG_Tree_GuardianShrine"], (0, 0, 0), 0.0, 1.0)]
    for h, ang in SHELVES:
        pos, yaw = shelf_pose(h, ang)
        out.append((built["JG_Tree_GuardianShelf"], pos, yaw, 1.0))
    return out


def build_all():
    out = {}
    for p in (build_tree(), build_crown(), build_shelf(), build_shrine()):
        out[p.name] = p
    return C.apply_merges(out)


if __name__ == "__main__":
    for n, p in build_all().items():
        lo, hi = p.bounds()
        print("%-26s %5d tris  %s -> %s  %s" % (n, p.tris(), tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi), p.stats()))
        for m, g in p.g.items():
            bw = g.bad_winding()
