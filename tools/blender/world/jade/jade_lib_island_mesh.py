"""jade_lib_island_mesh: the faceted jade-grey mass under Jade Grove's expanded ground, its hanging crystals and moss curtains (2026-11-22). It follows the NEW rim
(jade_lib_island.rim2), so it replaces the first foundation's JG_Underside, JG_UnderCrystals, JG_MossCurtains and JG_Vines, which were cut to the old rim.

Authored in island-local studs with the island's centre at the origin and y = 0 the island's base level (the builder places it at the island's frame, no turn).
Nothing here collides (the terrain shell, 14 studs deep, carries the cliffs; the mass hangs below it).
"""
import math
import random

import jade_lib_core as C
import jade_lib_island as I
import jade_lib_bamboo as B

TAU = C.TAU
BODY = [(1.0, -3.2), (1.03, -8.0), (1.0, -18.0), (0.93, -30.0), (0.8, -46.0), (0.63, -66.0), (0.45, -86.0), (0.28, -104.0), (0.12, -118.0)]   # (scale of the rim, y): as the old mass
TIP = (12.0, -130.0, -8.0)
SEG = 48


def radius_at(th, y, inset=1.0):
    """The mass's radius at bearing th and height y (the rings' own interpolation, the first rings hugging the rim)."""
    R = I.rim2(th)
    for (s0, y0), (s1, y1) in zip(BODY, BODY[1:]):
        if y1 <= y <= y0:
            t = (y0 - y) / (y0 - y1)
            s = s0 + (s1 - s0) * t
            return ((R + 1.6) * min(s, 1.0) if y > -18.0 else R * s) * inset
    return R * inset


_RINGS = []


def underside(name="JG_Isle_Underside", seed=901):
    rnd = random.Random(seed)
    P = C.Piece(name)
    rings = []
    for k, (s, y) in enumerate(BODY):
        twist = rnd.uniform(-0.1, 0.1)
        ring = []
        for i in range(SEG):
            th = TAU * (i + (0.5 if k % 2 else 0.0)) / SEG + twist
            R = I.rim2(th)
            jitter = 1 + (0.0 if k == 0 else 0.03 if k < 3 else 0.13) * (rnd.random() - 0.5) * 2
            r = (R + 1.6) * min(s, 1.0) * jitter if k < 3 else R * s * jitter
            yy = y + (0 if k < 2 else rnd.uniform(-3.0, 3.0))
            cx, cz = TIP[0] * (1 - s), TIP[2] * (1 - s)
            ring.append((cx + math.cos(th) * r, yy, cz + math.sin(th) * r))
        rings.append(ring)
    _RINGS[:] = rings
    g = C.loft(rings, True, True, True)        # the flat top (hidden inside the terrain's shell) and the tip are closed so the shell is watertight

    def mat(n, ctr):
        d = C.fbm3(ctr[0] * 0.07 + seed, ctr[1] * 0.07, ctr[2] * 0.07, seed, 2)
        if ctr[1] > -9.0 and n[1] > -0.2:
            return "Moss"
        if d > 0.28:
            return "Rock"
        return "RockDark"
    P.put(g, mat)
    # veins of jade across the mass: flat inlays laid on the middle of real facets of rings 3 and 4, a hair proud
    for k in range(18):
        ring_k = 3 + k % 2
        i = rnd.randrange(SEG)
        a, b = _RINGS[ring_k], _RINGS[ring_k + 1]
        j = (i + 1) % SEG
        pts = [a[i], a[j], b[j], b[i]]
        c = tuple(sum(p[q] for p in pts) / 4 for q in range(3))
        th = math.atan2(c[2], c[0])
        P.put(C.chunk(c, (rnd.uniform(5, 8), 1.6, 3.0), seed + k, 0.1, yaw=-th + math.pi / 2), "Jade")
    return P


def crystals(name="JG_Isle_Crystals", seed=911):
    """Hanging jade crystals: clusters rooted on real facets of rings 2 and 3, hanging down."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    if not _RINGS:
        underside()
    for k in range(22):
        ring_k = 2 + k % 2
        i = rnd.randrange(SEG)
        a, b = _RINGS[ring_k], _RINGS[ring_k + 1]
        j = (i + 1) % SEG
        pts = [a[i], a[j], b[j], b[i]]
        base = tuple(sum(p[q] for p in pts) / 4 for q in range(3))
        th = math.atan2(base[2], base[0])
        for j2 in range(3 + k % 2):
            L = rnd.uniform(5.0, 11.0)
            tilt = ((-math.sin(th), 0, math.cos(th)), rnd.uniform(-0.3, 0.3))
            P.put(C.chunk((base[0] + rnd.uniform(-1.0, 1.0), base[1] - L / 2 + 0.6, base[2] + rnd.uniform(-1.0, 1.0)), (1.6, L, 1.6), seed + k * 7 + j2 + 13, 0.08, tilt=tilt), "JadeGlass")
    return P


def curtains(name="JG_Isle_Curtains", seed=921):
    rnd = random.Random(seed)
    P = C.Piece(name)
    n = 16
    for k in range(n):
        th = TAU * k / n + rnd.uniform(-0.08, 0.08)
        R = I.rim2(th)
        r = R + 1.2
        m = B.moss_curtain("c", seed + k, rnd.uniform(6.0, 10.0), rnd.uniform(9.0, 16.0), 5, 3)
        P.add_piece(m, t=(math.cos(th) * r, -2.4, math.sin(th) * r), yaw=-th + math.pi / 2 + math.pi)
    return P


def build_all():
    u = underside()
    return {"JG_Isle_Underside": u, "JG_Isle_Crystals": crystals(), "JG_Isle_Curtains": curtains()}


if __name__ == "__main__":
    for n, p in build_all().items():
        lo, hi = p.bounds()
        print("%-22s %5d tris  box %s -> %s  %s" % (n, p.tris(), tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi), p.stats()))
