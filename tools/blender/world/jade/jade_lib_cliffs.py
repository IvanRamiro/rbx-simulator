"""jade_lib_cliffs: Jade Grove's waterfall cliffs and rock walls (2026-11-22). The water itself is WorldBuilder.buildWaterfall (and a Glass ribbon for the stream); these are the stone
the water falls over, with mossy ledges, a notch for the lip, pool rims and the hollow behind the High Falls.

  JG_Cliff_Grotto_G1    the High Falls' face, 34 wide and 14.5 high: strata ledges, a notched lip at the top centre, and below it an arched hollow
                        (the spirit grotto) with a floor, a back wall, glowing crystals; marks: Lip (the notch's lip), CurtainBase (the fall's foot)
  JG_Cliff_Cascade_C1   three stepped ledges, each 2.4 lower than the last, with rock cheeks: a cascade 14 wide; marks Lip1..Lip3
  JG_Cliff_RimLip_R1    the chute where the stream leaves the island: two cheek walls and a worn lip slab; mark Lip
  JG_Cliff_PoolRim_P1/P2 rim stones round a pool (an open arc)
  JG_Cliff_Wall_W1/W2   a mossy strata wall for the gorge's sides (16 wide, 9 and 6 high)

Frame: the origin on the ground at the foot of the face, the face looking toward -z (water falls toward -z), the rock running back along +z.
Every ledge top is a whole or half stud (the numeric check lists them).
"""
import math
import random

import jade_lib_core as C
import jade_lib_structures as S

TAU = C.TAU


def strata_mat(seed, top_moss=True):
    def choose(n, ctr):
        if n[1] > 0.7 and C.fbm3(ctr[0] * 0.25 + seed, ctr[1] * 0.25, ctr[2] * 0.25, seed, 2) > -0.1:
            return "Moss"
        if n[1] > 0.7:
            return "RockPale"
        return "RockDark" if ctr[1] < 1.2 else "Rock"
    return choose


def layers(P, x0, x1, z_front, depth, h0, h1, n, seed, protrude=1.2, mat=None):
    """A stack of n strata slabs from h0 to h1 between x0 and x1, each with its own front protrusion and a slight overhang."""
    rnd = random.Random(seed)
    hh = (h1 - h0) / n
    for k in range(n):
        pz = z_front - rnd.uniform(0.0, protrude)
        dx = rnd.uniform(-0.5, 0.5)
        w = (x1 - x0) + rnd.uniform(-0.6, 0.6)
        P.put(C.chunk(((x0 + x1) / 2 + dx, h0 + hh * (k + 0.5), pz + (depth + (z_front - pz)) / 2), (w, hh + 0.35, depth + (z_front - pz)), seed + k * 3, 0.05, yaw=rnd.uniform(-0.03, 0.03)), mat or strata_mat(seed + k))


def grotto(name="JG_Cliff_Grotto_G1", seed=801):
    rnd = random.Random(seed)
    P = C.Piece(name)
    H, D = 14.5, 9.0
    AW, AH = 4.6, 5.6              # the arch: half width and height
    # the wings, left and right of the arch, full height
    for sx in (-1, 1):
        x0, x1 = (AW + 0.8) * sx, 17.0 * sx
        lo, hi = min(x0, x1), max(x0, x1)
        layers(P, lo, hi, 0.0, D, 0.0, H, 5, seed + sx * 11, 1.5)
        P.box(((lo + hi) / 2, H / 2, D / 2 - 0.2), (hi - lo - 0.6, H, D - 1.0))
    # the mass over the arch and a notch in its top for the lip
    layers(P, -AW - 1.2, AW + 1.2, 0.0, D, AH, H - 0.9, 3, seed + 31, 0.8)
    P.put(C.chunk((-3.1, H - 0.45, D / 2 - 0.4), (3.6, 1.0, D - 0.8), seed + 40, 0.03), strata_mat(seed + 40))
    P.put(C.chunk((3.1, H - 0.45, D / 2 - 0.4), (3.6, 1.0, D - 0.8), seed + 41, 0.03), strata_mat(seed + 41))
    # the lip: a worn slab a little lower than the shoulders, its front edge beyond the face
    P.put(C.chunk((0.0, H - 1.05, D / 2 - 0.2), (5.0, 0.7, D + 0.6), seed + 42, 0.015), lambda n, c: "RockPale" if n[1] > 0.7 else "Rock")
    P.box((0.0, AH + (H - 1.4 - AH) / 2, D / 2 - 0.2), (AW * 2 + 2.0, H - 1.4 - AH, D - 1.0))
    # a brow over the wings, leaning out
    for sx in (-1, 1):
        P.put(C.chunk((sx * 11.0, H + 0.2, -0.6 + 3.0), (11.5, 0.9, 8.0), seed + 43 + sx, 0.04, tilt=((1, 0, 0), 0.0)), strata_mat(seed + 44))
    # the grotto: an arched opening 9.2 wide and 5.6 high into a hollow 8 deep: floor (top 0.6), back wall, ceiling dome
    P.put(C.chunk((0.0, 0.1, 3.8), (AW * 2 + 0.4, 1.0, D - 1.4), seed + 50, 0.01), lambda n, c: "Moss" if n[1] > 0.8 and C.fbm3(c[0] * 0.3, 0, c[2] * 0.3, seed, 2) > 0.1 else "Rock")
    P.box((0.0, 0.1, 3.0), (AW * 2 + 0.4, 1.0, D + 1.0))
    P.put(C.chunk((0.0, AH - 0.3, 3.8), (AW * 2 + 0.6, 0.8, D - 1.4), seed + 51, 0.03), "RockDark")
    # the arch's two jambs and a keystone lintel
    for sx in (-1, 1):
        P.put(C.chunk((sx * (AW + 0.4), AH / 2 + 0.3, 0.1), (1.2, AH + 0.2, 1.6), seed + 52 + sx, 0.04), strata_mat(seed + 53))
        P.put(C.chunk((sx * (AW - 0.2), AH - 0.9, 0.2), (1.6, 1.4, 1.6), seed + 54 + sx, 0.05, tilt=((0, 0, 1), -sx * 0.4)), strata_mat(seed + 55))
    P.put(C.chunk((0.0, AH + 0.2, 0.2), (AW * 2 + 1.0, 1.0, 1.6), seed + 56, 0.03), strata_mat(seed + 57))
    P.put(C.chunk((0.0, AH / 2, D - 0.6), (AW * 2 + 1.6, AH, 1.4), seed + 58, 0.03), "RockDark")       # the back wall
    P.box((0.0, AH / 2 + 0.5, D - 0.2), (AW * 2 + 1.6, AH, 1.6))
    for sx in (-1, 1):
        P.put(C.chunk((sx * (AW + 0.5), AH / 2, D / 2 + 0.2), (1.0, AH, D - 0.6), seed + 59 + sx, 0.03), "RockDark")
        P.box((sx * (AW + 0.5), AH / 2, D / 2 + 0.2), (1.2, AH, D - 0.6))
    # crystals and veins inside: jade prisms growing from the floor and the back wall, glowing tips (small Neon accents)
    for k in range(7):
        x = rnd.uniform(-AW + 0.8, AW - 0.8)
        z = rnd.uniform(D - 3.6, D - 1.6)
        hgt = rnd.uniform(0.8, 1.9)
        tilt = ((rnd.uniform(-1, 1), 0, rnd.uniform(-1, 1)), rnd.uniform(0.05, 0.3))
        P.put(C.chunk((x, 0.5 + hgt / 2 - 0.1, z), (0.45, hgt, 0.45), seed + 70 + k, 0.08, taper=0.5, tilt=tilt), "JadeGlass")
        P.put(C.ellipsoid((x, 0.5 + hgt - 0.3, z), (0.2, 0.2, 0.2), 5, 3), "GlowTeal")
    for k, y in enumerate((1.6, 2.6, 3.5)):
        P.put(C.chunk((-AW + 1.2 + k * 3.0, y, D - 1.2), (1.8, 0.2, 0.4), seed + 80 + k, 0.05, tilt=((0, 0, 1), 0.5 - 0.4 * k)), "Jade")
    # moss hanging from the lintel, ledge lips
    for k in range(5):
        x = -AW + 1.0 + k * (2 * AW - 2.0) / 4
        P.put(C.chunk((x, AH - 0.2, 1.0), (1.2, 0.5 + 0.3 * (k % 2), 0.4), seed + 90 + k, 0.1), "MossDeep")
    P.marks["Lip"] = ((0.0, H - 0.7, -0.5), 0.0)
    P.marks["CurtainBase"] = ((0.0, 0.0, -1.2), 0.0)
    P.marks["GrottoFloor"] = ((0.0, 0.6, 3.0), 0.0)
    return P


def cascade(name="JG_Cliff_Cascade_C1", seed=813, steps=3, drop=2.4, run=5.0, width=12.0):
    rnd = random.Random(seed)
    P = C.Piece(name)
    for k in range(steps):
        top = drop * (k + 1)               # k = 0 is the lowest ledge (front, toward -z), the highest at the back
        z0 = k * run
        P.put(C.chunk((0.0, top / 2 - 0.4, z0 + run / 2 + 0.6), (width + rnd.uniform(-0.8, 0.8), top + 0.8, run + 1.2), seed + k, 0.03), lambda n, c, s=seed + k: "Moss" if n[1] > 0.85 and C.fbm3(c[0] * 0.4 + s, 0, c[2] * 0.4, s, 2) > 0.3 else ("RockPale" if n[1] > 0.85 else ("RockDark" if c[1] < 1.0 else "Rock")))
        P.box((0.0, top / 2 - 0.5, z0 + run / 2 + 0.6), (width - 0.8, top + 0.0, run + 0.6))
        P.marks["Lip%d" % (k + 1)] = ((0.0, top, z0), 0.0)     # the front edge of each ledge: where its water leaves it
    # cheeks: rock banks on both sides rising a stud and a half above each ledge
    for sx in (-1, 1):
        for k in range(steps):
            top = drop * (k + 1)
            P.put(C.chunk((sx * (width / 2 + 0.9), top / 2 + 0.3, k * run + run / 2 + 0.6), (2.2, top + 1.6, run + 1.0), seed + 20 + k * 2 + sx, 0.07), strata_mat(seed + k))
            P.box((sx * (width / 2 + 0.9), top / 2, k * run + run / 2 + 0.6), (1.8, top + 0.6, run + 0.4))
    return P


def rim_lip(name="JG_Cliff_RimLip_R1", seed=821):
    P = C.Piece(name)
    P.put(C.chunk((0.0, -0.4, 3.2), (6.0, 1.4, 8.0), seed, 0.03), lambda n, c: "RockPale" if n[1] > 0.8 else "Rock")
    P.put(C.chunk((0.0, 0.05, 0.4), (4.4, 0.5, 1.4), seed + 1, 0.04), "RockPale")
    for sx in (-1, 1):
        P.put(C.chunk((sx * 3.8, 1.2, 3.0), (2.4, 3.4, 8.4), seed + 2 + sx, 0.06), strata_mat(seed + 4))
        P.box((sx * 3.8, 1.2, 3.0), (2.2, 3.2, 8.2))
        P.put(C.chunk((sx * 3.6, 3.2, 3.0), (2.6, 0.7, 8.6), seed + 6 + sx, 0.08), "Moss")
    P.box((0.0, -0.4, 3.2), (5.4, 1.2, 7.6))
    P.marks["Lip"] = ((0.0, 0.3, 0.2), 0.0)
    return P


def pool_rim(name, seed, R, count, arc):
    rnd = random.Random(seed)
    P = C.Piece(name)
    a0 = rnd.uniform(0, TAU)
    for k in range(count):
        a = a0 + arc * k / (count - 1) - arc / 2
        size = rnd.uniform(1.6, 2.6)
        P.put(C.chunk((math.cos(a) * R, 0.35, math.sin(a) * R), (size, 1.0 + rnd.uniform(0, 0.5), size * 1.4), seed + k, 0.1, yaw=-a + math.pi / 2), strata_mat(seed + k))
    return P


def wall(name, seed, W=16.0, H=9.0, n=4):
    rnd = random.Random(seed)
    P = C.Piece(name)
    layers(P, -W / 2, W / 2, 0.0, 4.0, 0.0, H, n, seed, 1.1)
    # a ledge of moss and a hanging fringe
    P.put(C.chunk((rnd.uniform(-3, 3), H + 0.1, 1.6), (W * 0.7, 0.4, 3.4), seed + 40, 0.12), "Moss")
    for k in range(4):
        P.put(C.chunk((-W * 0.35 + k * W * 0.23, H * (0.45 + 0.12 * (k % 2)), 0.1), (1.6, 0.9 + 0.7 * rnd.random(), 1.4), seed + 50 + k, 0.1), "MossDeep")
    P.box((0.0, H / 2, 1.8), (W - 0.8, H, 3.6))
    return P


def build_all():
    out = {}
    out["JG_Cliff_Grotto_G1"] = grotto()
    out["JG_Cliff_Cascade_C1"] = cascade()
    out["JG_Cliff_RimLip_R1"] = rim_lip()
    out["JG_Cliff_PoolRim_P1"] = pool_rim("JG_Cliff_PoolRim_P1", 831, 8.6, 9, math.radians(230))
    out["JG_Cliff_PoolRim_P2"] = pool_rim("JG_Cliff_PoolRim_P2", 841, 5.8, 6, math.radians(200))
    out["JG_Cliff_Wall_W1"] = wall("JG_Cliff_Wall_W1", 851, 16.0, 9.0, 4)
    out["JG_Cliff_Wall_W2"] = wall("JG_Cliff_Wall_W2", 861, 12.0, 6.0, 3)
    return out


if __name__ == "__main__":
    for n, p in build_all().items():
        lo, hi = p.bounds()
        print("%-26s %5d tris  box %s -> %s  marks %s" % (n, p.tris(), tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi), {k: tuple(round(c, 1) for c in v[0]) for k, v in p.marks.items()}))
