"""jade_lib_bridges: Jade Grove's three forest bridges (2026-11-22). Small crossings of a gorge or a rift, nothing like the 40-stud island bridges (those stay).

  JG_Bridge_LogSpan_B1   a felled log laid across a cleft: its top hewn flat, a rope rail on one side, a bank stone at each end     span 26.0, deck 3.1 wide
  JG_Bridge_RopeSpan_B2  a rope-and-plank bridge: 34 planks, two hand ropes and ties; with JG_Bridge_RopePost_B2P (a carved post, four of them)  span 34.0, deck 4.0
  JG_Bridge_RootSpan_B3  a living-root bridge: five roots woven across the gorge under a moss deck, rail roots rising at the sides, root mounds at both ends   span 30.0, deck 3.8

Frame: the deck's walking surface is y = 0, the span runs along +x from x = 0 (the first bank's edge) to x = span; the centre line is z = 0. Both ends rest 2 studs
on the banks, which the terrain levels to the deck (rise 0 at each end). Colliders: one deck box per bridge (top exactly y = 0) and rail boxes.
"""
import math
import random

import jade_lib_core as C
import jade_lib_structures as S

TAU = C.TAU
SPANS = {"B1": 26.0, "B2": 34.0, "B3": 30.0}
DECK_W = {"B1": 3.1, "B2": 4.0, "B3": 3.8}


def log_span(name="JG_Bridge_LogSpan_B1", seed=701):
    rnd = random.Random(seed)
    P = C.Piece(name)
    L = SPANS["B1"]
    x0, x1 = -2.0, L + 2.0
    rings = []
    stations = [x0 + (x1 - x0) * k / 10.0 for k in range(11)]
    for k, x in enumerate(stations):
        t = k / 10.0
        R = 2.45 - 0.35 * t + 0.1 * math.sin(k * 1.7)
        cy = -1.45
        ring = []
        for i in range(12):
            a = TAU * i / 12
            y = cy + math.sin(a) * R * (1 + 0.04 * C.noise3(k, i, seed, seed))
            z = math.cos(a) * R * (1 + 0.05 * C.noise3(i, k, seed, seed + 1))
            ring.append((x, min(y, 0.0), z))
        rings.append(ring)
    log = C.loft(rings, True, True)

    def mat(n, ctr):
        if n[1] > 0.95:
            return "Moss" if C.fbm3(ctr[0] * 0.25 + seed, 0.0, ctr[2] * 0.4, seed, 2) > 0.1 else "Timber"
        if abs(n[0]) > 0.8:
            return "Timber"
        return "Trunk"
    P.put(log, mat)
    # snapped branch stubs, a root flare at the thick end, a few knots
    for k, (x, a, ln) in enumerate(((4.0, -0.9, 1.5), (11.0, 2.4, 1.2), (17.5, -2.2, 1.0), (22.0, 0.8, 1.2))):
        z = math.cos(a) * 2.2
        P.put(C.tube([(x, -1.45 + math.sin(a) * 2.0, z), (x + 0.2, -1.45 + math.sin(a) * (2.0 + ln), z + math.cos(a) * ln)], 0.32, 0.26, 5, per=1), "Trunk")
    for k in range(4):
        a = TAU * k / 4 + 0.4
        P.put(C.tube([(x0 + 0.8, -1.2, math.sin(a) * 1.4), (x0 - 0.8, -1.7, math.sin(a) * 2.6), (x0 - 2.4, -2.4, math.sin(a) * 3.0)], 0.5, 0.4, 6, per=2), "Root")
    # a rope rail on the -z side: three short posts and a sagging cord
    zr = -1.45
    for k, x in enumerate((1.0, L / 2, L - 1.0)):
        P.put(C.tube([(x, -0.4, zr), (x, 2.6, zr)], 0.16, 0.13, 5, per=1), "Timber")
        P.box((x, 1.3, zr), (0.34, 2.6, 0.34))
    P.put(C.tube([(1.0, 2.4, zr), (L * 0.25, 1.9, zr), (L / 2, 2.2, zr), (L * 0.75, 1.9, zr), (L - 1.0, 2.4, zr)], 0.07, None, 4, per=3), "Cord")
    # bank stones where it rests
    for sx, x in ((-1, -1.3), (1, L + 1.3)):
        P.put(C.chunk((x, -0.6, 0.0), (3.4, 1.4, 4.6), seed + sx, 0.06), S.moss_top(seed + sx, -0.2))
    P.box((L / 2, -0.5, 0.0), (L + 3.0, 1.0, 2.8))
    return P


def rope_post(name="JG_Bridge_RopePost_B2P", seed=711):
    """A carved post: a squared timber 7 high on a stone footing, a spiral groove, a notched top, a cross-bar and an iron-free rope loop for the ropes."""
    P = C.Piece(name)
    P.put(C.lathe([(0.0, -0.4), (1.1, -0.4), (1.0, 0.5), (0.0, 0.5)], 8), S.moss_top(seed))
    P.put(C.chunk((0, 3.6, 0), (0.9, 7.2, 0.9), seed, 0.03, taper=0.06), "Timber")
    pts = [(math.cos(a) * 0.5, 1.2 + a * 0.45, math.sin(a) * 0.5) for a in [t * 0.5 for t in range(0, 11)]]
    P.put(C.tube(pts, 0.09, 0.07, 4, per=1), "PlankDark")
    P.put(C.chunk((0, 7.4, 0), (1.15, 0.5, 1.15), seed + 1, 0.04), "Timber")
    P.put(C.chunk((0, 6.4, 0), (0.45, 0.4, 1.9), seed + 2, 0.02), "Timber")
    P.put(C.tube([(0.0, 6.1, 0.35), (0.0, 6.0, 0.95), (0.0, 5.4, 0.95), (0.0, 5.3, 0.35)], 0.07, None, 4, per=2), "Cord")
    P.box((0, 3.5, 0), (1.0, 7.0, 1.0))
    return P


def rope_span(name="JG_Bridge_RopeSpan_B2", seed=721):
    rnd = random.Random(seed)
    P = C.Piece(name)
    L, W = SPANS["B2"], DECK_W["B2"]
    n = 34
    plank_len = L / n
    for k in range(n):
        x = (k + 0.5) * plank_len
        sag = -0.55 * math.sin(math.pi * x / L) * 0.0
        P.put(C.box((x, -0.16, 0.0), (plank_len - 0.1, 0.32, W - 0.1 + rnd.uniform(-0.1, 0.1)), jit=True), "Plank" if k % 3 else "PlankDark")
    # two stringer ropes under the planks hold them together
    for sz in (-1, 1):
        P.put(C.tube([(-0.4, -0.36, sz * (W / 2 - 0.35)), (L + 0.4, -0.36, sz * (W / 2 - 0.35))], 0.17, None, 5, per=1), "Cord")
    # two hand ropes at 3.3 above the deck, sagging 0.5 between the posts; ties every 3.4
    for sz in (-1, 1):
        z = sz * (W / 2 + 0.1)
        pts = [(-0.4, 3.3, z), (L * 0.25, 3.0, z), (L * 0.5, 2.8, z), (L * 0.75, 3.0, z), (L + 0.4, 3.3, z)]
        P.put(C.tube(pts, 0.09, None, 5, per=5), "Cord")
        P.put(C.tube([(-0.3, 0.1, z), (L * 0.5, -0.1, z), (L + 0.3, 0.1, z)], 0.08, None, 4, per=6), "Cord")
        for k in range(1, 10):
            x = L * k / 10.0
            ty = 3.3 - 0.5 * math.sin(math.pi * x / L)
            P.put(C.tube([(x, ty, z), (x, 0.0, z)], 0.04, None, 3, per=1), "Cord")
    # the invisible rails (colliders) keep walkers on the deck
    for sz in (-1, 1):
        P.box((L / 2, 1.3, sz * (W / 2 + 0.1)), (L, 2.6, 0.3))
    P.box((L / 2, -0.5, 0.0), (L, 1.0, W - 0.3))
    return P


def root_span(name="JG_Bridge_RootSpan_B3", seed=747):
    rnd = random.Random(seed)
    P = C.Piece(name)
    L, W = SPANS["B3"], DECK_W["B3"]
    # five roots woven across: each runs from the first mound to the second, swinging side to side and rising and sagging in turn
    for k in range(5):
        ph = TAU * k / 5
        pts = []
        for i in range(10):
            t = i / 9.0
            x = -2.0 + (L + 4.0) * t
            env = math.sin(math.pi * t) ** 0.5
            z = 1.35 * math.sin(TAU * (t * 2.2) + ph) * env + (k - 2) * 0.42 * (1.0 - env)
            y = -0.55 - 0.13 * k * (1.0 - env) - 0.7 * math.sin(math.pi * t) * (0.4 + 0.6 * ((k + 1) % 3) / 2.0) - 0.4 * math.sin(TAU * t * 1.6 + ph) * math.sin(math.pi * t)
            pts.append((x, y, z))
        g = C.tube(pts, lambda t: 0.55 + 0.35 * (1 - math.sin(math.pi * t)) + 0.1, None, 7, per=2, wob=0.08, seed=seed + k)
        P.put(g, lambda n, c, o=k: "Moss" if n[1] > 0.6 and C.fbm3(c[0] * 0.3 + o, 0, c[2] * 0.4, seed, 2) > 0.2 else "Root")
    # the moss deck laid over the weave: a flat slab, ragged at the edges, its top at y = 0
    rings = []
    for k in range(13):
        x = L * k / 12.0
        hw = W / 2 * (1.0 + 0.05 * math.sin(k * 2.1))
        rings.append([(x, 0.0, -hw), (x, 0.0, hw), (x, -0.5, hw * 0.92), (x, -0.5, -hw * 0.92)])
    P.put(C.loft(rings, True, True), lambda n, c: "Moss" if n[1] > 0.9 else "MossDeep")
    # rail roots rising out of the mounds and arching along both sides
    for sz in (-1, 1):
        pts = [(-1.0, -0.4, sz * 2.6), (L * 0.15, 1.5, sz * 2.4), (L * 0.5, 0.9, sz * 2.3), (L * 0.85, 1.5, sz * 2.4), (L + 1.0, -0.4, sz * 2.6)]
        P.put(C.tube(pts, lambda t: 0.5 - 0.15 * math.sin(math.pi * t), 0.45, 6, per=3, wob=0.07, seed=seed + 10 + sz), "Root")
        for k in range(3):
            x = L * (k + 0.5) / 3.0
            yy = 1.0 + 0.3 * math.sin(math.pi * x / L)
            P.put(C.tube([(x, yy, sz * 2.3), (x, -0.3, sz * 1.9)], 0.22, 0.2, 5, per=1), "Root")
    # mounds of root and moss at both ends, hanging fringes underneath
    for sx, x in ((-1, -1.4), (1, L + 1.4)):
        P.put(C.ellipsoid((x, -0.9, 0.0), (2.9, 1.3, 3.4), 10, 5, 0.25, seed + sx, flat=-1.6), lambda n, c: "Moss" if n[1] > 0.35 else "Root")
    for k in range(6):
        x = L * (k + 0.5) / 6.0
        z = rnd.uniform(-1.5, 1.5)
        ln = rnd.uniform(3.0, 7.0)
        P.put(C.tube([(x, -0.9, z), (x + 0.2, -0.9 - ln * 0.5, z + 0.3), (x - 0.1, -0.9 - ln, z)], 0.14, None, 4, per=2), "Root")
    P.box((L / 2, -0.5, 0.0), (L + 2.0, 1.0, W - 0.6))
    return P


def build_all():
    out = {}
    out["JG_Bridge_LogSpan_B1"] = log_span()
    out["JG_Bridge_RopePost_B2P"] = rope_post()
    out["JG_Bridge_RopeSpan_B2"] = rope_span()
    out["JG_Bridge_RootSpan_B3"] = root_span()
    return C.apply_merges(out)


if __name__ == "__main__":
    for n, p in build_all().items():
        lo, hi = p.bounds()
        print("%-30s %5d tris  box %s -> %s" % (n, p.tris(), tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi)))
