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
import jade_lib_island as I
import jade_lib_craft as K
import jade_lib_bamboo as BB
import jade_lib_structures as S

TAU = C.TAU


def strata_mat(seed):
    return K.face_mat(seed)


def three_tone(seed, mouth_z=2.0, height=20.0, half=17.0):
    """The tall faces' material choice with three suffixes only (each material is a MeshPart in the game): moss on up-facing shelves in soft patches, dark in the cracks, the undersides,
    the wet foot and the cave, and water-stained streaks that run down from the brow (a stripe one or two columns wide, each its own length). No bands, no per-face checker: the strata
    are told by the geometry and the sun. The block's two end walls (seen from the pools) are weathered rock with moss and stains, not the dark of a back."""
    def choose(n, ctr):
        side = abs(ctr[0]) > half - 0.8 and abs(n[0]) > 0.6
        if ctr[2] > mouth_z and not side:
            return "RockDark"
        if n[1] > 0.5:
            return "Moss" if C.fbm3(ctr[0] * 0.12 + seed, ctr[1] * 0.12, ctr[2] * 0.12, seed, 2) > -0.2 else "Rock"
        if n[1] < -0.3 or (abs(n[0]) > 0.6 and n[1] < 0.2 and not side):
            return "RockDark"
        if ctr[1] < 1.3:
            return "RockDark"
        if side:
            if C.fbm3(ctr[2] * 0.25 + seed, ctr[1] * 0.2, 1.0, seed, 2) > 0.28:
                return "Moss"
            return "RockDark" if C.fbm3(ctr[2] * 0.5 + seed, ctr[1] * 0.14, 3.0, seed + 2, 2) > 0.3 else "Rock"
        # a stain: where the column's noise is high, dark from the brow down to a length of its own
        col = C.fbm2(ctr[0] * 0.62 + seed * 0.1, 0.4, seed + 3, 2)
        if col > 0.22:
            length = height * (0.18 + 0.7 * (0.5 + 0.5 * C.fbm2(ctr[0] * 0.9 + 11.0, 2.0, seed + 5, 2)))
            if ctr[1] > height - length:
                return "RockDark"
        return "Rock"
    return choose


def worn_block(P, c, size, yaw, seed, mat="Rock", tilt=None, moss=True):
    """One carved block, a little chipped (a jittered chunk with a chamfered corner)."""
    def m(n, ctr):
        if moss and n[1] > 0.7 and C.fbm3(ctr[0] * 0.8 + seed, ctr[1], ctr[2] * 0.8, seed, 2) > 0.0:
            return "Moss"
        return mat
    P.put(C.chunk(c, size, seed, 0.05, yaw=yaw, tilt=tilt, chip=0.18), m)


# the High Falls' face: 34 wide, as tall as the plateau (I.FALLS_H), 14 deep so the plateau's cliff foot (9 behind the foot line) and its slope are inside the rock; the cave is open air
FACE_D = 14.0
MOUTH_D = 8.0                              # how far the arched pocket runs back from the face


def grotto(name="JG_Cliff_Grotto_G1", seed=801):
    """The High Falls' face. Polish pass 2026-11-23: it stands 29.5 high (it was 14.5), the notch in its brow is as wide as the basin (26), the same arched mouth and carved lip as before,
    three materials (Rock, RockDark, Moss): the jade crystals of the cave are their own small piece (JG_Cliff_GrottoCrystals_K1)."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    H, D = I.FALLS_H, FACE_D
    MD = MOUTH_D
    AW, AH, JH = 5.4, 7.6, 4.4          # the mouth: half width, crown height, where the jambs end and the arch starts (it was 4.6, 5.6, 3.4 under a 14.5 face)
    face = K.rock_face(I.FACE_W, H, D, seed, layers=11, soft_every=3, overhang=1.5, undercut=1.1, cracks=12, rough=0.42, step=1.25, fine=(-6.6, 6.6), end_curl=4.5, end_drop=0.16, relief=2.0, bow=3.4, skyline=1.4,
                       arch=(0.0, AW, JH, AH), notch=(0.0, 13.0, 1.2), mouth_depth=MD)
    P.put(face, three_tone(seed, 2.0, H, I.FACE_W / 2.0))
    # colliders: the first pass's proxies (wings, the mass over the mouth, the floor, the back wall, the jambs)
    # (the face curves toward the viewer by 3.4 at its ends: each wing is two boxes, the outer one standing further forward)
    for sx in (-1, 1):
        for xa, xb, zf in ((AW + 0.8, 10.8, 0.3), (10.8, 17.0, -1.6)):
            x0, x1 = xa * sx, xb * sx
            lo, hi = min(x0, x1), max(x0, x1)
            P.box(((lo + hi) / 2, H / 2, (zf + D - 0.7) / 2), (hi - lo - 0.6, H, D - 0.7 - zf))
    P.box((0.0, AH + (H - 1.4 - AH) / 2, D / 2 - 0.2), (AW * 2 + 2.0, H - 1.4 - AH, D - 1.0))
    # the floor of the hollow (top y = 0.6), the back wall
    P.put(C.chunk((0.0, 0.1, 3.8), (AW * 2 + 0.4, 1.0, MD - 0.4), seed + 50, 0.01), lambda n, c: "Moss" if n[1] > 0.8 and C.fbm3(c[0] * 0.3, 0, c[2] * 0.3, seed, 2) > 0.1 else "Rock")
    P.box((0.0, 0.1, 3.0), (AW * 2 + 0.4, 1.0, MD + 2.0))
    P.put(C.chunk((0.0, AH / 2 + 0.3, MD + 0.6), (AW * 2 + 1.0, AH, 1.6), seed + 58, 0.03), "RockDark")
    P.box((0.0, AH / 2 + 0.5, MD + 0.8), (AW * 2 + 1.6, AH, 1.6))
    for sx in (-1, 1):
        P.box((sx * (AW + 0.5), AH / 2, MD / 2 + 0.7), (1.2, AH, MD + 0.4))
        # the pocket's side walls are the face's own; a stone course along the foot of each wall inside
        P.put(C.chunk((sx * (AW - 0.4), 0.9, 4.2), (0.9, 1.0, 6.4), seed + 61 + sx, 0.06), "RockDark")
    # the carved lip: voussoirs laid along the arch (a few chipped or missing), jamb courses below, a worn keystone
    skip = {2, 9}
    nv = 15
    for k in range(nv):
        if k in skip:
            continue
        a = math.pi * (k + 0.5) / nv
        r = AW + 0.55
        cx, cy = math.cos(a) * r, JH + math.sin(a) * (AH - JH) * (r / AW)
        worn_block(P, (cx, cy, -0.5 - 0.05 * (k % 3)), (1.4 + 0.2 * rnd.random(), 1.05 + 0.03 * (k % 4), 1.9), 0.0, seed + 100 + k, "Rock", tilt=((0, 0, 1), math.pi / 2 - a + rnd.uniform(-0.1, 0.1)))
    for sx in (-1, 1):
        for row in range(5):
            y = 0.5 + row * 0.9
            if (row, sx) == (2, 1):
                continue
            worn_block(P, (sx * (AW + 0.5 + 0.12 * (row % 2)), y, -0.4), (1.0 + 0.25 * (row % 2), 0.82, 1.8), 0.0, seed + 140 + row * 2 + sx, "Rock" if row % 2 else "RockDark")
    worn_block(P, (0.0, AH + 0.85, -0.6), (1.7, 1.3, 2.0), 0.0, seed + 160, "Rock")       # the keystone
    # a fallen voussoir and two chips on the floor of the mouth's apron
    worn_block(P, (-2.2, 0.4, -0.3), (1.2, 0.8, 1.1), 0.6, seed + 161, "Rock", tilt=((1, 0, 0), 0.3))
    worn_block(P, (1.7, 0.3, -0.2), (0.8, 0.6, 0.8), 1.0, seed + 162, "RockDark")
    # the foot: broken blocks, roots over the brow, hanging moss at both shoulders (outside the water: the lip's curtains are 25 wide)
    K.foot_blocks(P, rnd, I.FACE_W, -0.6, 7, seed + 200, 2.0, avoid=(-5.6, 5.6), seg=7, rings=4)
    K.root_hooks(P, rnd, I.FACE_W, H - 0.5, -1.4, 3, seed + 300, avoid=(-13.5, 13.5))
    for k, x in enumerate((-15.6, 15.4)):
        m = BB.moss_curtain("c", seed + 400 + k, 4.4, 7.0, 5, 3)
        P.add_piece(m, t=(x, H - 1.6, -0.6))
    P.marks["Lip"] = ((0.0, H - 1.1, I.LIP_Z), 0.0)
    P.marks["CurtainBase"] = ((0.0, 0.0, -1.2), 0.0)
    P.marks["GrottoFloor"] = ((0.0, 0.6, 3.0), 0.0)
    P.merge({"RockPale": "Rock", "Stone": "Rock", "StoneDark": "RockDark", "MossDeep": "Moss", "Root": "Moss"})
    return P


def grotto_crystals(name="JG_Cliff_GrottoCrystals_K1", seed=803):
    """The cave's jade crystals on a low rock bed, in the High Falls' face frame (placed at the same position and yaw as JG_Cliff_Grotto_G1): translucent crystals with small glowing
    tips, as in phase A, now a piece of their own so the face stays at three materials."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    AW = 5.4
    bed_z = MOUTH_D - 2.6
    P.put(C.chunk((0.0, 0.62, bed_z), (AW * 2 - 1.0, 0.7, 3.4), seed, 0.1, chip=0.1), "RockDark")
    for k in range(7):
        x = rnd.uniform(-AW + 0.8, AW - 0.8)
        z = bed_z + rnd.uniform(-1.2, 1.2)
        hgt = rnd.uniform(0.8, 1.9)
        tilt = ((rnd.uniform(-1, 1), 0, rnd.uniform(-1, 1)), rnd.uniform(0.05, 0.3))
        P.put(C.chunk((x, 0.6 + hgt / 2 - 0.05, z), (0.45, hgt, 0.45), seed + 70 + k, 0.08, taper=0.5, tilt=tilt), "JadeGlass")
        P.put(C.ellipsoid((x, 0.6 + hgt - 0.22, z), (0.2, 0.2, 0.2), 5, 3), "GlowTeal")
    return P


def ribbon(name="JG_Cliff_Ribbon_R1", seed=871):
    """The second fall's rock: a narrow face, 15 wide and as tall as I.RIB_H (21.5), with a notch in the brow for a 5-stud ribbon of water, three materials, strata that step in and out,
    a foot of fallen blocks, roots over the brow and a moss curtain on each shoulder. Frame as the High Falls' face: origin at the foot, the water falls toward -z."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    W, H, D = I.RIB_W, I.RIB_H, 13.5
    face = K.rock_face(W, H, D, seed, layers=6, soft_every=3, overhang=1.2, undercut=0.9, cracks=4, rough=0.28, step=1.15, end_curl=2.6, end_drop=0.12, notch=(0.0, 3.4, 1.0), relief=1.4)
    P.put(face, three_tone(seed, 2.0, H, W / 2.0))
    for sx in (-1, 1):
        P.box((sx * 5.6, H / 2, D / 2 - 0.2), (3.6, H, D - 1.0))
    P.box((0.0, H / 2 - 0.5, D / 2 + 0.3), (7.6, H - 1.0, D - 1.0))
    K.foot_blocks(P, rnd, W, -0.6, 4, seed + 200, 1.8, avoid=(-2.8, 2.8), seg=7, rings=4)
    K.root_hooks(P, random.Random(seed + 5), W, H - 0.5, -1.2, 2, seed + 307, avoid=(-3.6, 3.6))
    for k, x in enumerate((-5.6, 5.5)):
        m = BB.moss_curtain("c", seed + 410 + k, 3.4, 6.0, 5, 3)
        P.add_piece(m, t=(x, H - 1.5, -0.8 - 0.1 * k))
    P.marks["Lip"] = ((0.0, H - 0.9, I.LIP_Z), 0.0)
    P.merge({"RockPale": "Rock", "Stone": "Rock", "StoneDark": "RockDark", "MossDeep": "Moss", "Root": "Moss"})
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
    out["JG_Cliff_GrottoCrystals_K1"] = grotto_crystals()
    out["JG_Cliff_Ribbon_R1"] = ribbon()
    out["JG_Cliff_Cascade_C1"] = cascade()
    out["JG_Cliff_RimLip_R1"] = rim_lip()
    out["JG_Cliff_PoolRim_P1"] = pool_rim("JG_Cliff_PoolRim_P1", 831, 8.6, 11, math.radians(230), seg=7)
    out["JG_Cliff_PoolRim_P2"] = pool_rim("JG_Cliff_PoolRim_P2", 841, 5.8, 8, math.radians(200), seg=10)
    out["JG_Cliff_Wall_W1"] = wall("JG_Cliff_Wall_W1", 851, 16.0, 9.0, 4)
    out["JG_Cliff_Wall_W2"] = wall("JG_Cliff_Wall_W2", 861, 12.0, 6.0, 3)
    return C.apply_merges(out)


if __name__ == "__main__":
    for n, p in build_all().items():
        lo, hi = p.bounds()
        print("%-26s %5d tris  box %s -> %s  marks %s" % (n, p.tris(), tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi), {k: tuple(round(c, 1) for c in v[0]) for k, v in p.marks.items()}))
