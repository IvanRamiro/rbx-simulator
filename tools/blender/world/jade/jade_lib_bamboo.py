"""jade_lib_bamboo: Jade Grove's bamboo, vines and moss curtains (2026-11-22).

  JG_Bamboo_Grove_G1 / G2   a tall green culm grove: arching jointed culms, leaf plumes at the tips and at the upper joints
  JG_Bamboo_Clump_K1 / K2   a short dense clump: many culms splayed from one root-knot, fanned leaf sprays
  JG_Bamboo_Shoots_S1       young shoots: pale sheathed stems pushing out of a moss mat
  JG_Bamboo_Arch_H1         two bundles of culms leaning over a path to meet above it (a green tunnel for the hidden paths)
  JG_Vine_Curtain_V1 / V2   hanging vines with leaf pairs from an anchoring stub (for branches, ledges and ruins)
  JG_Moss_Curtain_M1 / M2   a thick draped moss sheet with a ragged hem (for cliff ledges and eaves)

Culms are single lofts whose rings sit at the joints (a swollen node band, then a long straight internode), so a 30-stud culm costs about 200
triangles; joint bands take their own material. Colliders: a small cylinder at each grove's middle (the leaves never collide).
"""
import math
import random

import jade_lib_core as C

TAU = C.TAU


def culm(base, height, lean, arch, radius, seed, sides=5, gap=3.4, taper=0.38):
    """One jointed culm: rises from `base`, leaning toward (lx, lz) by `lean` studs at the top and arching a further `arch` at the very tip.
    Returns (shell, node centres, tip position, tip direction)."""
    rnd = random.Random(seed)
    lx, lz = lean
    la = math.hypot(lx, lz)

    def axis(h):
        t = h / height
        bend = (t ** 1.6) * 1.0
        return (base[0] + lx * t + (lx / (la + 1e-9)) * arch * t ** 3.2, base[1] + h - arch * 0.18 * t ** 3.2, base[2] + lz * t + (lz / (la + 1e-9)) * arch * t ** 3.2)
    n_seg = max(2, int(height / gap))
    stations = [(-0.4, False)]
    for k in range(n_seg):
        h = 1.2 + k * (height - 1.8) / max(1, n_seg - 1)
        if h > height - 0.5:
            break
        stations += [(h - 0.13, True), (h + 0.13, True)]
    stations.append((height, False))
    rings, nodes = [], []
    prev = None
    nrm = None
    for i, (h, is_node) in enumerate(stations):
        c = axis(max(h, 0.0))
        ahead = axis(min(height, max(h, 0.0) + 0.3))
        behind = axis(max(0.0, max(h, 0.0) - 0.3))
        T = C.vnorm(C.vsub(ahead, behind))
        ref = (0.0, 1.0, 0.0) if abs(T[1]) < 0.95 else (1.0, 0.0, 0.0)
        N = C.vnorm(C.vsub(ref, C.vmul(T, C.vdot(T, ref))))
        B = C.vcross(T, N)
        t = max(h, 0.0) / height
        r = radius * (1.0 - taper * t) * (1.3 if is_node else 1.0) * (1.0 + 0.5 * math.exp(-max(h, 0.0) / 0.7))
        if i == len(stations) - 1:
            r *= 0.55
        ring = []
        for k in range(sides):
            a = TAU * k / sides + 0.3
            ring.append((c[0] + (N[0] * math.cos(a) + B[0] * math.sin(a)) * r, c[1] + (N[1] * math.cos(a) + B[1] * math.sin(a)) * r,
                         c[2] + (N[2] * math.cos(a) + B[2] * math.sin(a)) * r))
        rings.append(ring)
    centres = []
    for i, (h, is_node) in enumerate(stations):
        if is_node and (i == 0 or not stations[i - 1][1] or stations[i - 1][0] != h - 0.26 + 0.0):
            pass
    for i in range(0, len(stations) - 1):
        if stations[i][1] and stations[i + 1][1] and abs(stations[i + 1][0] - stations[i][0] - 0.26) < 1e-6:
            centres.append(axis(stations[i][0] + 0.13))
    g = C.loft(rings, True, True)
    tip = axis(height)
    tdir = C.vnorm(C.vsub(tip, axis(height - 1.0)))
    return g, centres, tip, tdir, axis


def _culm_mat(centres):
    def choose(n, ctr):
        for c in centres:
            if abs(ctr[1] - c[1]) < 0.34 and math.hypot(ctr[0] - c[0], ctr[2] - c[2]) < 1.1:
                return "CulmNode"
        return "Culm"
    return choose


def plume(P, at, direction, rnd, n=5, L=(3.2, 4.6), w=0.36, droop=0.45):
    d0 = C.vnorm(direction)
    for b in range(n):
        a = TAU * b / n + rnd.uniform(-0.3, 0.3)
        d = (d0[0] * 0.6 + math.cos(a) * 0.9, d0[1] * 0.6 + rnd.uniform(0.0, 0.6), d0[2] * 0.6 + math.sin(a) * 0.9)
        P.put(C.blade(at, d, rnd.uniform(*L), w * rnd.uniform(0.9, 1.2), droop=droop * rnd.uniform(0.8, 1.2), thick=0.05, segs=2, mid=0.45), "LeafMid" if b % 3 else "LeafPale")


def grove(name, seed, n=9, h=(26.0, 36.0), r=4.4, rad=0.58, lean_out=2.6, gap=3.4, tufts=True):
    rnd = random.Random(seed)
    P = C.Piece(name)
    bases = []
    for i in range(n):
        a = TAU * i / n + rnd.uniform(-0.4, 0.4)
        d = r * (0.15 + 0.85 * math.sqrt(rnd.random()))
        base = (math.cos(a) * d, -0.4, math.sin(a) * d)
        bases.append(base)
        H = rnd.uniform(*h)
        lean = (math.cos(a) * lean_out * rnd.uniform(0.5, 1.3), math.sin(a) * lean_out * rnd.uniform(0.5, 1.3))
        g, centres, tip, tdir, axis = culm(base, H, lean, rnd.uniform(2.0, 4.2), rad * rnd.uniform(0.85, 1.15), seed * 7 + i, 5, gap)
        P.put(g, _culm_mat(centres))
        plume(P, tip, tdir, rnd, 6, (4.4, 6.2), 0.5)
        if tufts:
            at = axis(H * 0.8)
            plume(P, at, (math.cos(a), 0.5, math.sin(a)), rnd, 3, (3.2, 4.4), 0.42)
    # low roots running out from the culms' feet
    for k, b in enumerate(bases[:4]):
        a = math.atan2(b[2], b[0]) + 0.3 * (k - 1.5)
        P.put(C.tube([(b[0], 0.5, b[2]), (b[0] + math.cos(a) * 1.4, 0.1, b[2] + math.sin(a) * 1.4), (b[0] + math.cos(a) * 2.6, -0.35, b[2] + math.sin(a) * 2.6)], 0.3, 0.26, 5, per=2), "Root")
    P.cyl((0, 3.0, 0), r * 1.3, 6.0)
    return P


def clump(name, seed, n=14, h=(8.0, 15.0), splay=0.5, rad=0.4):
    rnd = random.Random(seed)
    P = C.Piece(name)
    bases = []
    for i in range(n):
        a = TAU * i / n + rnd.uniform(-0.25, 0.25)
        d = rnd.uniform(0.2, 1.6)
        base = (math.cos(a) * d, -0.3, math.sin(a) * d)
        bases.append(base)
        H = rnd.uniform(*h)
        lean = (math.cos(a) * H * splay * rnd.uniform(0.4, 1.1), math.sin(a) * H * splay * rnd.uniform(0.4, 1.1))
        g, centres, tip, tdir, axis = culm(base, H, lean, rnd.uniform(0.8, 2.0), rad * rnd.uniform(0.85, 1.2), seed * 9 + i, 5, 2.6, 0.32)
        P.put(g, _culm_mat(centres))
        plume(P, tip, tdir, rnd, 4, (3.4, 4.8), 0.46, 0.5)
    for k, b in enumerate(bases[:5]):
        a = math.atan2(b[2], b[0]) + 0.3 * (k - 2)
        P.put(C.tube([(b[0], 0.4, b[2]), (b[0] + math.cos(a) * 1.2, 0.0, b[2] + math.sin(a) * 1.2), (b[0] + math.cos(a) * 2.2, -0.3, b[2] + math.sin(a) * 2.2)], 0.26, 0.22, 5, per=2), "Root")
    P.cyl((0, 2.0, 0), 2.6, 4.0)
    return P


def shoots(name, seed, n=8):
    """Young bamboo sprouts: thin pale stems bending a little, dry brown sheath flaps standing out at the joints, each stem opening at the top
    into narrow unfurling leaves; they push through a mat of moss. (No smooth rounded tips: every stem ends in leaf.)"""
    rnd = random.Random(seed)
    P = C.Piece(name)
    for i in range(n):
        a = TAU * i / n + rnd.uniform(-0.3, 0.3)
        d = rnd.uniform(0.5, 2.8)
        x, z = math.cos(a) * d, math.sin(a) * d
        H = rnd.uniform(2.6, 6.6)
        lean = (rnd.uniform(-0.9, 0.9), rnd.uniform(-0.9, 0.9))
        g, centres, tip, tdir, axis = culm((x, -0.2, z), H, lean, rnd.uniform(0.4, 1.0), 0.17 * rnd.uniform(0.9, 1.2), seed * 3 + i, 5, 1.5, 0.2)
        P.put(g, lambda n_, c_, cs=centres: "CulmNode" if any(abs(c_[1] - c[1]) < 0.3 and math.hypot(c_[0] - c[0], c_[2] - c[2]) < 0.8 for c in cs) else "CulmPale")
        # dry sheath flaps at the joints
        for k, c in enumerate(centres):
            if k % 2 == 0:
                sa = a + rnd.uniform(-1.2, 1.2)
                P.put(C.blade(c, (math.cos(sa), 0.55, math.sin(sa)), rnd.uniform(0.9, 1.5), 0.34, droop=0.35, thick=0.05, segs=2, mid=0.4), "Timber")
        for b in range(3):
            ba = TAU * b / 3 + rnd.uniform(-0.3, 0.3)
            P.put(C.blade(tip, (math.cos(ba) * 0.6, 1.0, math.sin(ba) * 0.6), rnd.uniform(2.0, 3.0), 0.3, droop=0.4, thick=0.04, segs=2, mid=0.45), "LeafPale")
    P.put(C.ellipsoid((0, -0.05, 0), (3.6, 0.45, 3.2), 12, 4, 0.16, seed, flat=-0.25), lambda nrm, ctr: "MossDeep" if nrm[1] < 0.5 else "Moss")
    P.cyl((0, 0.3, 0), 3.0, 0.6)
    return P


def arch(name, seed, span=5.6, height=9.2, bundles=3):
    """Two bundles of culms rising either side of a path and leaning in to meet over it. Origin at the path's middle; the path runs along z."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    for side in (-1, 1):
        for i in range(bundles):
            z = (i - (bundles - 1) / 2) * 2.3 + rnd.uniform(-0.3, 0.3)
            base = (side * (span / 2 + rnd.uniform(-0.2, 0.5)), -0.4, z)
            H = height + rnd.uniform(1.0, 3.2)
            g, centres, tip, tdir, axis = culm(base, H, (-side * (span / 2 + rnd.uniform(0.2, 1.2)), rnd.uniform(-0.6, 0.6)), rnd.uniform(1.4, 2.6), 0.46 * rnd.uniform(0.9, 1.1), seed * 5 + i + side * 11, 5, 3.0, 0.3)
            P.put(g, _culm_mat(centres))
            plume(P, tip, tdir, rnd, 4, (2.8, 3.8), 0.34)
            plume(P, axis(H * 0.7), (-side, 0.5, 0.0), rnd, 2, (2.2, 3.0), 0.3)
    # the arch is open: nothing at the path
    return P


def vine_curtain(name, seed, strands=7, width=7.0, drop=(7.0, 13.0), leafy=True):
    """Hanging vines: a stub of branch at the top, thin cords with leaf pairs every few studs. Origin: the stub's centre, vines hang toward -y."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    P.put(C.tube([(-width / 2 - 0.4, 0.0, 0.0), (0.0, 0.25, 0.1), (width / 2 + 0.4, 0.0, -0.05)], 0.34, 0.3, 6, per=3), "Trunk")
    for s in range(strands):
        x = -width / 2 + width * (s + rnd.uniform(0.1, 0.9)) / strands
        L = rnd.uniform(*drop)
        sway = rnd.uniform(-0.7, 0.7)
        pts = [(x, 0.0, 0.0), (x + sway * 0.3, -L * 0.33, 0.2 * sway), (x - sway * 0.4, -L * 0.66, -0.2 * sway), (x + sway * 0.2, -L, 0.1)]
        P.put(C.tube(pts, lambda t: 0.1 - 0.04 * t, None, 4, per=2), "MossDeep")
        if leafy:
            for k in range(3):
                t = 0.3 + 0.24 * k
                y = -L * t
                for sg in (-1, 1):
                    P.put(C.blade((x + sway * 0.2 * t, y, 0.0), (sg * 0.8, -0.35, rnd.uniform(-0.3, 0.3)), rnd.uniform(1.0, 1.6), 0.42, droop=0.5, thick=0.05, segs=2, mid=0.45), "LeafMid" if (s + k) % 2 else "Fern")
    return P


def moss_curtain(name, seed, w=8.0, h=6.0, cols=9, rows=4, thick=0.22):
    """A draped sheet of moss: a thick, folded slab hung from its top edge, a ragged hem, a heavier bulge where it folds. Origin: top centre."""
    rnd = random.Random(seed)
    P = C.Piece(name)
    hem = [h * (0.7 + 0.3 * rnd.random()) for _ in range(cols + 1)]
    front, back = [], []
    for j in range(rows + 1):
        rowf, rowb = [], []
        for i in range(cols + 1):
            u = i / cols
            hh = hem[i] * j / rows
            fold = 0.5 * math.sin(u * math.pi * 3.0 + seed) * (j / rows) ** 0.8 + 0.18 * rnd.uniform(-1, 1) * (j / rows)
            x = -w / 2 + w * u
            rowf.append((x, -hh, fold + thick / 2))
            rowb.append((x, -hh, fold - thick / 2))
        front.append(rowf)
        back.append(rowb)
    g = C.Geo()
    for j in range(rows):
        for i in range(cols):
            g.face(front[j][i], front[j + 1][i], front[j + 1][i + 1], front[j][i + 1])
            g.face(back[j][i], back[j][i + 1], back[j + 1][i + 1], back[j + 1][i])
    for i in range(cols):
        g.face(front[rows][i], back[rows][i], back[rows][i + 1], front[rows][i + 1])
        g.face(front[0][i], front[0][i + 1], back[0][i + 1], back[0][i])
    for j in range(rows):
        g.face(front[j][0], back[j][0], back[j + 1][0], front[j + 1][0])
        g.face(front[j][cols], front[j + 1][cols], back[j + 1][cols], back[j][cols])
    P.put(g, lambda n, c: "MossDeep" if c[1] < -h * 0.55 and n[2] < 0 else "Moss")
    return P


def build_all():
    out = {}
    out["JG_Bamboo_Grove_G1"] = grove("JG_Bamboo_Grove_G1", 101, n=8, h=(26.0, 36.0), r=4.4, lean_out=2.6)
    out["JG_Bamboo_Grove_G2"] = grove("JG_Bamboo_Grove_G2", 113, n=7, h=(20.0, 27.0), r=3.4, rad=0.52, lean_out=1.6, tufts=False)
    out["JG_Bamboo_Clump_K1"] = clump("JG_Bamboo_Clump_K1", 127, n=13, h=(8.0, 15.0), splay=0.46)
    out["JG_Bamboo_Clump_K2"] = clump("JG_Bamboo_Clump_K2", 131, n=9, h=(5.0, 9.0), splay=0.62, rad=0.34)
    out["JG_Bamboo_Shoots_S1"] = shoots("JG_Bamboo_Shoots_S1", 141)
    out["JG_Bamboo_Arch_H1"] = arch("JG_Bamboo_Arch_H1", 151)
    out["JG_Vine_Curtain_V1"] = vine_curtain("JG_Vine_Curtain_V1", 161, 7, 7.0, (7.0, 13.0))
    out["JG_Vine_Curtain_V2"] = vine_curtain("JG_Vine_Curtain_V2", 171, 5, 4.4, (5.0, 9.0), leafy=True)
    out["JG_Moss_Curtain_M1"] = moss_curtain("JG_Moss_Curtain_M1", 181, 8.0, 6.0)
    out["JG_Moss_Curtain_M2"] = moss_curtain("JG_Moss_Curtain_M2", 191, 5.0, 8.5, 7, 5)
    return out


if __name__ == "__main__":
    for n, p in build_all().items():
        lo, hi = p.bounds()
        print("%-26s %5d tris  box %s -> %s  %s" % (n, p.tris(), tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi), p.stats()))
