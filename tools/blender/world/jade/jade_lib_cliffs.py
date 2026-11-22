"""jade_lib_cliffs: Jade Grove's waterfall cliffs and rock walls (2026-11-22, second pass: real rock faces). The water itself is WorldBuilder.buildWaterfall (and a Glass
ribbon for the stream); these are the stone the water falls over.

  JG_Cliff_Grotto_G1    the High Falls' face, 34 wide and 14.5 high: irregular strata that step in and out (hard brows, soft recessed layers, an undercut foot), vertical joint cracks,
                        moss shelves on every ledge, broken blocks at the foot, roots hooking over the brow, hanging moss, a notch in the top edge for the lip, and below it a real cave
                        mouth: an arched pocket 9.2 wide whose carved lip is laid in worn voussoir stones (some chipped, some fallen), a floor, crystals and jade veins inside
  JG_Cliff_Cascade_C1   three stepped ledges, each 2.4 lower than the last, irregular outlines with moss shelves and boulders on their edges, rock-face cheeks
  JG_Cliff_RimLip_R1    the chute where the stream leaves the island: a worn lip with a carved groove and rock-face cheeks
  JG_Cliff_PoolRim_P1/P2 irregular rim stones round a pool (an open arc), mossy, with larger boulders at the ends
  JG_Cliff_Wall_W1/W2   a rock-face wall for the gorge's sides (16 and 12 wide)

Frame: origin on the ground at the foot of the face, the face looking toward -z (water falls toward -z), the rock running back along +z. Colliders and marks are the first pass's
(the stated collision proxies): the faces are visual, the boxes carry the walking.
"""
import math
import random

import jade_lib_core as C
import jade_lib_craft as K
import jade_lib_bamboo as BB
import jade_lib_structures as S

TAU = C.TAU


def strata_mat(seed):
    return K.face_mat(seed)


def worn_block(P, c, size, yaw, seed, mat="Stone", tilt=None, moss=True):
    """One carved block, a little chipped (a jittered chunk with a chamfered corner)."""
    def m(n, ctr):
        if moss and n[1] > 0.7 and C.fbm3(ctr[0] * 0.8 + seed, ctr[1], ctr[2] * 0.8, seed, 2) > 0.0:
            return "Moss"
        return mat
    P.put(C.chunk(c, size, seed, 0.05, yaw=yaw, tilt=tilt, chip=0.18), m)


def grotto(name="JG_Cliff_Grotto_G1", seed=801):
    rnd = random.Random(seed)
    P = C.Piece(name)
    H, D = 14.5, 9.0
    AW, AH, JH = 4.6, 5.6, 3.4          # the mouth: half width, crown height, where the jambs end and the arch starts
    face = K.rock_face(34.0, H, D, seed, layers=5, soft_every=3, overhang=2.2, undercut=1.1, cracks=6, rough=0.3, step=1.15, fine=(-5.8, 5.8), end_curl=3.0, end_drop=0.22,
                       arch=(0.0, AW, JH, AH), notch=(0.0, 2.4, 1.0), mouth_depth=8.0)
    P.put(face, strata_mat(seed))
    # colliders: the first pass's proxies (wings, the mass over the mouth, the floor, the back wall, the jambs)
    for sx in (-1, 1):
        x0, x1 = (AW + 0.8) * sx, 17.0 * sx
        lo, hi = min(x0, x1), max(x0, x1)
        P.box(((lo + hi) / 2, H / 2, D / 2 - 0.2), (hi - lo - 0.6, H, D - 1.0))
    P.box((0.0, AH + (H - 1.4 - AH) / 2, D / 2 - 0.2), (AW * 2 + 2.0, H - 1.4 - AH, D - 1.0))
    # the floor of the hollow (top y = 0.6), the back wall
    P.put(C.chunk((0.0, 0.1, 3.8), (AW * 2 + 0.4, 1.0, D - 1.4), seed + 50, 0.01), lambda n, c: "Moss" if n[1] > 0.8 and C.fbm3(c[0] * 0.3, 0, c[2] * 0.3, seed, 2) > 0.1 else "Rock")
    P.box((0.0, 0.1, 3.0), (AW * 2 + 0.4, 1.0, D + 1.0))
    P.put(C.chunk((0.0, AH / 2 + 0.3, D - 0.4), (AW * 2 + 1.0, AH, 1.6), seed + 58, 0.03), "RockDark")
    P.box((0.0, AH / 2 + 0.5, D - 0.2), (AW * 2 + 1.6, AH, 1.6))
    for sx in (-1, 1):
        P.box((sx * (AW + 0.5), AH / 2, D / 2 + 0.2), (1.2, AH, D - 0.6))
        # the pocket's side walls are the face's own; a stone course along the foot of each wall inside
        P.put(C.chunk((sx * (AW - 0.4), 0.9, 4.2), (0.9, 1.0, 6.4), seed + 61 + sx, 0.06), "RockDark")
    # the carved lip: voussoirs laid along the arch (a few chipped or missing), jamb courses below, a worn keystone
    skip = {2, 8}
    nv = 13
    for k in range(nv):
        if k in skip:
            continue
        a = math.pi * (k + 0.5) / nv
        r = AW + 0.55
        cx, cy = math.cos(a) * r, JH + math.sin(a) * (AH - JH) * (r / AW)
        tang = math.atan2(-math.sin(a) * (AH - JH), -math.cos(a) * AW)
        worn_block(P, (cx, cy, -0.5 - 0.05 * (k % 3)), (1.25 + 0.2 * rnd.random(), 0.95 + 0.03 * (k % 4), 1.9), 0.0, seed + 100 + k, "Stone", tilt=((0, 0, 1), math.pi / 2 - a + rnd.uniform(-0.1, 0.1)))
    for sx in (-1, 1):
        for row in range(4):
            y = 0.5 + row * 0.85
            if (row, sx) == (2, 1):
                continue
            worn_block(P, (sx * (AW + 0.5 + 0.12 * (row % 2)), y, -0.4), (1.0 + 0.25 * (row % 2), 0.82, 1.8), 0.0, seed + 140 + row * 2 + sx, "Stone" if row % 2 else "StoneDark")
    worn_block(P, (0.0, AH + 0.75, -0.6), (1.5, 1.2, 2.0), 0.0, seed + 160, "Stone")       # the keystone
    # a fallen voussoir and two chips on the floor of the mouth's apron
    worn_block(P, (-2.2, 0.4, -0.3), (1.2, 0.8, 1.1), 0.6, seed + 161, "Stone", tilt=((1, 0, 0), 0.3))
    worn_block(P, (1.7, 0.3, -0.2), (0.8, 0.6, 0.8), 1.0, seed + 162, "StoneDark")
    # inside: crystals growing from the floor with glowing tips, veins of jade on the back wall (small Neon accents)
    for k in range(7):
        x = rnd.uniform(-AW + 0.8, AW - 0.8)
        z = rnd.uniform(D - 3.6, D - 1.6)
        hgt = rnd.uniform(0.8, 1.9)
        tilt = ((rnd.uniform(-1, 1), 0, rnd.uniform(-1, 1)), rnd.uniform(0.05, 0.3))
        P.put(C.chunk((x, 0.5 + hgt / 2 - 0.1, z), (0.45, hgt, 0.45), seed + 70 + k, 0.08, taper=0.5, tilt=tilt), "JadeGlass")
        P.put(C.ellipsoid((x, 0.5 + hgt - 0.3, z), (0.2, 0.2, 0.2), 5, 3), "GlowTeal")
    for k, y in enumerate((1.6, 2.6, 3.5)):
        P.put(C.chunk((-AW + 1.2 + k * 3.0, y, D - 1.0), (1.8, 0.2, 0.7), seed + 80 + k, 0.05, tilt=((0, 0, 1), 0.5 - 0.4 * k)), "Jade")
    # the foot: broken blocks, roots over the brow, hanging moss at both shoulders
    K.foot_blocks(P, rnd, 34.0, -0.6, 6, seed + 200, 2.0, avoid=(-5.6, 5.6), seg=7, rings=4)
    K.root_hooks(P, rnd, 34.0, H - 0.5, -1.4, 3, seed + 300, avoid=(-4.5, 4.5))
    for k, x in enumerate((-9.5, 11.0)):
        m = BB.moss_curtain("c", seed + 400 + k, 5.0, 7.0, 5, 3)
        P.add_piece(m, t=(x, H - 1.2, -0.6))
    P.marks["Lip"] = ((0.0, H - 0.9, -1.4), 0.0)
    P.marks["CurtainBase"] = ((0.0, 0.0, -1.2), 0.0)
    P.marks["GrottoFloor"] = ((0.0, 0.6, 3.0), 0.0)
    return P


def ledge(P, top, z0, run, width, seed, rnd):
    """A cascade ledge: an irregular slab whose top is exactly flat at `top`, edge boulders and a moss shelf along its lip."""
    n = 14
    poly = []
    for i in range(n):
        a = TAU * i / n
        rr = 1.0 + 0.12 * math.sin(3 * a + seed) + 0.07 * rnd.uniform(-1, 1)
        poly.append((math.cos(a) * (width / 2 + 0.4) * rr, math.sin(a) * (run / 2 + 0.9) * rr))
    g = C.prism(poly, -0.5 - 0.1 * (seed % 5), top, (0.0, 0.0, z0 + run / 2 + 0.6))

    def m(n_, ctr):
        if n_[1] > 0.9:
            return "Moss" if C.fbm3(ctr[0] * 0.4 + seed, 0, ctr[2] * 0.4, seed, 2) > 0.0 else "RockPale"
        return "RockDark" if ctr[1] < top * 0.4 else "Rock"
    P.put(g, m)
    P.box((0.0, top / 2 - 0.5, z0 + run / 2 + 0.6), (width - 0.8, top, run + 0.6))
    # boulders on the lip and the sides, a moss mantle on the biggest
    for k in range(4):
        x = rnd.uniform(-width / 2 + 0.6, width / 2 - 0.6)
        r = rnd.uniform(0.5, 0.95)
        zc = z0 + (0.5 if k % 2 else run + 0.9)
        P.put(C.ellipsoid((x, top - r * 0.1, zc), (r, r * 0.7, r), 7, 4, 0.28, seed + k, flat=-r * 0.4), lambda n_, c: "Moss" if n_[1] > 0.55 else "Rock")


def cascade(name="JG_Cliff_Cascade_C1", seed=813, steps=3, drop=2.4, run=5.0, width=12.0):
    rnd = random.Random(seed)
    P = C.Piece(name)
    for k in range(steps):
        top = drop * (k + 1)
        z0 = k * run
        ledge(P, top, z0, run, width, seed + k * 11, rnd)
        P.marks["Lip%d" % (k + 1)] = ((0.0, top, z0), 0.0)
    # cheeks: rock faces on both sides, one long face each side that steps up with the ledges
    total = steps * run + 1.2
    for sx in (-1, 1):
        Hc = drop * steps + 1.6
        face = K.rock_face(total, Hc, 2.6, seed + 20 + sx, layers=4, soft_every=3, overhang=0.6, undercut=0.3, cracks=2, rough=0.2, step=1.7)
        P.put(face, strata_mat(seed + sx), t=(sx * (width / 2 + 0.9), 0.0, total / 2 - 0.5), yaw=(math.pi / 2 if sx > 0 else -math.pi / 2))
        for k in range(steps):
            top = drop * (k + 1)
            P.box((sx * (width / 2 + 0.9), top / 2, k * run + run / 2 + 0.6), (1.8, top + 0.6, run + 0.4))
    return P


def rim_lip(name="JG_Cliff_RimLip_R1", seed=821):
    rnd = random.Random(seed)
    P = C.Piece(name)
    poly = [(-2.6, 0.0), (-2.0, -1.0), (0.0, -1.3), (2.0, -1.0), (2.6, 0.0), (3.0, 4.5), (2.0, 8.4), (-2.0, 8.4), (-3.0, 4.5)]
    g = C.prism([(x, z) for x, z in poly], -1.2, 0.05, (0.0, 0.0, 0.0))
    P.put(g, lambda n, c: ("RockPale" if C.fbm3(c[0] * 0.4, 0, c[2] * 0.4, seed, 2) > 0.2 else "Rock") if n[1] > 0.8 else "RockDark")
    # the carved groove: a shallow channel worn along the lip (a darker, lower strip), and two rounded worn stones in it
    P.put(C.chunk((0.0, -0.02, 1.0), (2.0, 0.16, 5.0), seed + 1, 0.02), "RockDark")
    for k in range(2):
        P.put(C.ellipsoid((rnd.uniform(-0.5, 0.5), 0.05, 1.8 + k * 1.8), (0.5, 0.22, 0.45), 7, 4, 0.1, seed + k), "RockPale")
    for sx in (-1, 1):
        face = K.rock_face(8.6, 4.0, 2.2, seed + 5 + sx, layers=3, soft_every=3, overhang=0.5, undercut=0.2, cracks=1, rough=0.2, step=1.0)
        P.put(face, strata_mat(seed + sx), t=(sx * 2.9, -0.2, 4.2), yaw=(math.pi / 2 if sx > 0 else -math.pi / 2))
        P.put(C.chunk((sx * 4.0, 3.5, 4.2), (2.4, 0.7, 7.8), seed + 6 + sx, 0.08), "Moss")
        P.box((sx * 3.8, 1.2, 3.0), (2.2, 3.2, 8.2))
    for k, (x, z, r) in enumerate(((-3.6, 7.6, 0.9), (3.8, 7.9, 0.8), (-4.6, 1.2, 0.8), (4.7, 1.5, 0.9))):      # broken blocks fallen at the foot of the cheeks
        P.put(C.ellipsoid((x, 0.2, z), (r, r * 0.8, r * 0.9), 7, 4, 0.3, seed + 20 + k), lambda n_, c: "Moss" if n_[1] > 0.6 else "Rock")
    P.box((0.0, -0.4, 3.2), (5.4, 1.2, 7.6))
    P.marks["Lip"] = ((0.0, 0.3, 0.2), 0.0)
    return P


def pool_rim(name, seed, R, count, arc, seg=8):
    rnd = random.Random(seed)
    P = C.Piece(name)
    a0 = rnd.uniform(0, TAU)
    for k in range(count):
        a = a0 + arc * k / (count - 1) - arc / 2
        end = k in (0, count - 1)
        size = rnd.uniform(1.5, 2.6) * (1.35 if end else 1.0)
        hgt = rnd.uniform(0.7, 1.3) * (1.4 if end else 1.0)
        x, z = math.cos(a) * R, math.sin(a) * R
        g = C.ellipsoid((0, 0, 0), (size * 0.62, hgt * 0.7, size * 0.8), seg, 5, 0.32, seed + k * 3, flat=-hgt * 0.25)
        P.put(g, lambda n, c: "Moss" if n[1] > 0.55 and C.fbm3(c[0] * 0.7, c[1], c[2] * 0.7, seed, 2) > -0.15 else ("RockDark" if c[1] < 0.15 else "Rock"), t=(x, hgt * 0.35, z), yaw=-a + math.pi / 2)
        if k % 3 == 1:       # a flat capping slab on every third stone
            P.put(C.chunk((x, hgt * 0.95, z), (size * 0.9, 0.22, size * 0.7), seed + 40 + k, 0.1, yaw=-a + math.pi / 2), lambda n, c: "Moss" if n[1] > 0.8 else "RockPale")
    return P


def wall(name, seed, W=16.0, H=9.0, n=4):
    rnd = random.Random(seed)
    P = C.Piece(name)
    face = K.rock_face(W, H, 4.0, seed, layers=n + 1, soft_every=3, overhang=1.0, undercut=0.7, cracks=3, rough=0.22, step=1.0, end_curl=2.2, end_drop=0.18)
    P.put(face, strata_mat(seed))
    K.foot_blocks(P, rnd, W, -0.5, 5 if W > 14 else 3, seed + 20, 1.8, seg=7, rings=4)
    K.root_hooks(P, rnd, W, H - 0.4, -1.0, 2, seed + 30)
    m = BB.moss_curtain("c", seed + 40, W * 0.3, H * 0.55, 5, 3)
    P.add_piece(m, t=(rnd.uniform(-W * 0.2, W * 0.2), H - 0.6, -0.1))
    P.box((0.0, H / 2, 1.8), (W - 0.8, H, 3.6))
    return P


def build_all():
    out = {}
    out["JG_Cliff_Grotto_G1"] = grotto()
    out["JG_Cliff_Cascade_C1"] = cascade()
    out["JG_Cliff_RimLip_R1"] = rim_lip()
    out["JG_Cliff_PoolRim_P1"] = pool_rim("JG_Cliff_PoolRim_P1", 831, 8.6, 11, math.radians(230), seg=7)
    out["JG_Cliff_PoolRim_P2"] = pool_rim("JG_Cliff_PoolRim_P2", 841, 5.8, 8, math.radians(200), seg=10)
    out["JG_Cliff_Wall_W1"] = wall("JG_Cliff_Wall_W1", 851, 16.0, 9.0, 4)
    out["JG_Cliff_Wall_W2"] = wall("JG_Cliff_Wall_W2", 861, 12.0, 6.0, 3)
    return out


if __name__ == "__main__":
    for n, p in build_all().items():
        lo, hi = p.bounds()
        print("%-26s %5d tris  box %s -> %s  marks %s" % (n, p.tris(), tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi), {k: tuple(round(c, 1) for c in v[0]) for k, v in p.marks.items()}))
