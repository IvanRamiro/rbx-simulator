"""The Murim High Ponytail (run inside Blender; a rigid hair accessory on HairAttachment).

From the owner's "Murim Hair" concept sheet (its front, side and back views), made exactly as drawn
and pushed further: wild, layered black wuxia hair with real volume. A full centre-parted fringe of
pointed locks falls over the forehead to the eyes; heavy side hair frames the face, two long locks
on each side hanging in front of the shoulders onto the chest. The top and back are swept up in
messy clumps to a high tie at the back of the crown, a spray of spikes bursting up out of it. From
the tie the tail falls long and wide down the back in layered spiky locks, its ends shading to a
deep red-brown. At the tie: a silver clasp, a pointed crown at its front set with a red gem and a
diamond clasp at its back, over a crimson ribbon bow whose long tails hang down the tail, one
streaming out to the side.

Built twice (see hair_kit): pieces("hi") for the bake, pieces("low") for the game mesh, whose
clumps are diamond-sectioned locks (they read as anime hair clumps) within the 4,000-triangle
budget.
"""
import math
import random

from mathutils import Vector

import hair_kit as H

K = H.K
V = Vector
TAU = H.TAU
ITEM = "MurimHighPonytail"
C = H.HEAD_C
TIE = V((0.0, 0.3, 3.38))          # the high tie at the back of the crown
TAIL_DIR = V((0.0, 0.92, 0.39)).normalized()   # the tail leaves the tie back and a little up

RES = {
    "hi": {"cap": (96, 24), "rib_step": 0.03, "rib_cols": 6, "ring": (40, 10)},
    "low": {"cap": (12, 3), "rib_step": 0.24, "rib_cols": 1, "ring": (10, 3)},
}

DEG = math.pi / 180
HAIRLINE = H.table([(0, 40), (40, 32), (60, 0), (90, -24), (130, -38), (180, -44)])


def hairline(a):
    return HAIRLINE(abs(((a / DEG + 180) % 360) - 180)) * DEG


class Hair:
    """Builds the strands of one version (hi or low)."""

    def __init__(self, res):
        self.r = RES[res]
        self.hi = res == "hi"
        self.seed = 0

    def strand(self, mesh, pts, width, thick, step=0.24, **kw):
        """A blade lock (hair_kit.strand); the game mesh's segments `step` long."""
        self.seed += 1
        H.strand(mesh, pts, width, thick, 0.03 if self.hi else step, self.hi, 0, seed=self.seed, **kw)


def fringe(h, m, rnd):
    """The bangs, in two layers: from the parting on top, over the front edge and down the forehead
    to the eyes, the middle locks longest, each curving a little and its tip lifting off the face."""
    for i in range(8):   # the back layer: broader, a little shorter
        f = -1 + 2 * (i + 0.5) / 8
        pts = [(0.08 * f, 0.02, 3.1), (0.45 * f, -0.56, 3.3), (0.62 * f, -0.72, 3.08),
               (0.66 * f, -0.7, 2.8 + 0.06 * abs(f) + rnd.uniform(-0.03, 0.03))]
        h.strand(m, pts, 0.17, 0.04, 0.22, curl=0.03, flick=0.02)
    for i in range(9):   # the front layer: finer, longer, curving
        f = -1 + 2 * i / 8
        tipz = 2.62 + 0.13 * abs(f) ** 1.5 + (0.05 if 0.35 < abs(f) < 0.7 else 0.0) + rnd.uniform(-0.03, 0.03)
        pts = [(0.06 * f, -0.06, 3.1), (0.42 * f, -0.62, 3.28 - 0.05 * abs(f)), (0.58 * f + 0.05 * f, -0.78, 3.0 - 0.06 * abs(f)),
               (0.64 * f + 0.1 * f + rnd.uniform(-0.03, 0.03), -0.74, tipz)]
        h.strand(m, pts, 0.13 - 0.02 * abs(f), 0.032, 0.2, curl=0.04, flick=0.035)


def sides(h, m, rnd):
    """The side hair: a curtain of locks over each side of the head, flicking out at the jaw, and
    three long locks a side falling in front of the shoulders onto the chest."""
    for s in (1, -1):
        for j in range(5):
            y = -0.36 + 0.2 * j
            pts = [(0.3 * s, y, 3.08), (0.8 * s, y - 0.04, 2.95), (0.88 * s, y - 0.06, 2.45),
                   (0.94 * s + rnd.uniform(0.0, 0.06) * s, y - 0.03, 2.0 - 0.04 * j + rnd.uniform(-0.05, 0.05))]
            h.strand(m, pts, 0.17, 0.04, 0.26, curl=0.05, flick=0.07)
        for j, (tipz, x, w) in enumerate(((1.08, 0.68, 0.13), (1.34, 0.8, 0.1), (1.55, 0.6, 0.07))):
            pts = [(0.28 * s, -0.34 + 0.08 * j, 3.08), (0.72 * s, -0.63 + 0.04 * j, 2.92), (0.77 * s, -0.69 + 0.04 * j, 2.4),
                   (x * s, -0.65 + 0.03 * j, 1.85), (x * s + 0.05 * s, -0.6 + 0.03 * j, tipz)]
            h.strand(m, pts, w, 0.035, 0.3, curl=0.07, flick=0.04, swell=0.25, root=0.8)


def crown_hair(h, m, rnd, tree):
    """The top, sides and back swept up to the tie, each lock lifting off the head on its way, its
    end flicking past the tie (the messy volume on top)."""
    for k in range(15):
        a = 40 + 280 * k / 14
        el = 34 - 10 * math.sin(math.radians(a - 40) * 180 / 280 * 0.9)
        p, n = H.on_head(tree, a * DEG, el * DEG)
        root = p - n * 0.03
        mid = (root + TIE) / 2
        mid = mid + (mid - C).normalized() * 0.2 + V((0, 0, 0.04))
        end = TIE + (TIE - C).normalized() * 0.08 + V((rnd.uniform(-0.14, 0.14), rnd.uniform(-0.05, 0.14), rnd.uniform(0.04, 0.18)))
        h.strand(m, [root, mid, end], 0.2, 0.045, 0.25, curl=0.03, flick=0.06, swell=0.4, root=0.85)


def back_hair(h, m, rnd, tree):
    """The hair below the tie at the back and sides, left loose: it hangs in layered locks to the
    shoulders and upper back, behind and beside the tail."""
    for k in range(11):
        a = 100 + 160 * k / 10
        el = -6 + 6 * math.cos(math.radians(a - 180))
        p, n = H.on_head(tree, a * DEG, el * DEG)
        out = V((p.x, p.y, 0)).normalized()
        tipz = 1.62 + 0.4 * abs(a - 180) / 80 + rnd.uniform(-0.06, 0.06)
        root = p - n * 0.04 + V((0, 0, 0.22))
        bulge = p + out * 0.26 + V((0, 0, -0.05))
        tip = V((p.x * 1.25 + rnd.uniform(-0.05, 0.05), p.y * 1.2 + 0.15, tipz))
        h.strand(m, [root, bulge, tip], 0.2, 0.045, 0.26, curl=0.06, flick=0.08)


def spray(h, m, rnd):
    """The spikes bursting up out of the tie, curling back."""
    for k in range(9):
        a = TAU * k / 9 + rnd.uniform(-0.2, 0.2)
        d = V((0.6 * math.sin(a), 0.4 * math.cos(a) + 0.2, 1.0)).normalized()
        L = rnd.uniform(0.45, 0.7)
        tip = TIE + d * L + V((0, 0.16, -0.08))
        h.strand(m, [TIE - V((0, 0, 0.05)), TIE + d * (L * 0.55), tip], 0.11, 0.03, 0.2, curl=0.05, flick=0.04,
                 up=lambda p: (p - TIE).normalized() if (p - TIE).length > 1e-4 else V((0, 0, 1)), swell=0.3, root=0.9)


def tail(h, m, rnd):
    """The tail: out of the tie and down the back, fanning wide in three layers of long locks that
    swing in S-curves, their tips flicking out; the middle longest."""
    def outward(p):
        core = V((0.0, 1.0, p.z))
        o = p - core
        o = V((o.x, max(o.y, 0.0) + 0.35, 0.0))
        return o.normalized()
    for layer, n in ((0, 8), (1, 7), (2, 5)):
        for i in range(n):
            f = -1 + 2 * (i + (0.5 if layer == 1 else 0.0)) / max(1, n - (0 if layer == 1 else 1))
            f = max(-1.0, min(1.0, f))
            back = 0.1 * layer
            flick = rnd.uniform(-0.06, 0.06) + 0.12 * f
            tipz = 0.48 + 0.55 * f * f + 0.22 * layer + rnd.uniform(-0.1, 0.1)
            pts = [TIE + V((0.05 * f, 0.02, 0.0)), TIE + TAIL_DIR * 0.45 + V((0.16 * f, back * 0.5, 0.04)),
                   (0.34 * f, 0.98 + back, 3.0), (0.5 * f, 1.02 + back, 2.3), (0.62 * f + flick * 0.5, 0.98 + back, 1.55),
                   (0.7 * f + flick, 0.94 + back + rnd.uniform(-0.04, 0.06), tipz)]
            h.strand(m, pts, 0.24 - 0.03 * layer, 0.05, 0.46, up=outward, curl=0.1, flick=0.1, swell=0.35, root=0.6)


def flyaways(h, m, rnd):
    """Thin loose strands breaking the silhouette: out of the tail's sides, over the sides of the
    head, and two springing up off the crown."""
    for s in (1, -1):
        h.strand(m, [(0.3 * s, 1.1, 2.7), (0.7 * s, 1.12, 2.25), (0.95 * s, 1.0, 1.85), (1.02 * s, 0.9, 1.7)], 0.04, 0.012, 0.25,
                 curl=0.04, flick=0.04, up=lambda p: V((p.x, 0.4, 0)).normalized(), swell=0.2, root=1.0)
        h.strand(m, [(0.5 * s, 1.05, 1.8), (0.82 * s, 1.0, 1.3), (0.9 * s, 0.9, 1.05)], 0.035, 0.012, 0.25,
                 curl=0.05, up=lambda p: V((p.x, 0.4, 0)).normalized(), swell=0.2, root=1.0)
        h.strand(m, [(0.5 * s, -0.3, 3.1), (0.95 * s, -0.4, 2.95), (1.05 * s, -0.45, 2.6)], 0.035, 0.012, 0.25,
                 curl=0.03, flick=0.05, swell=0.2, root=1.0)
    for s in (1, -1):
        h.strand(m, [(0.05 * s, -0.1, 3.1), (0.1 * s, -0.25, 3.45), (0.22 * s, -0.42, 3.55), (0.3 * s, -0.5, 3.48)], 0.035, 0.012, 0.2,
                 curl=0.02, swell=0.2, root=1.0)


def plate(m, centre, xaxis, yaxis, normal, outline, th):
    """A flat plate `th` thick (a closed solid) with the given outline (x, y in its plane, any
    simple polygon, concave too): its faces properly triangulated, its rim facing out."""
    from mathutils.geometry import tessellate_polygon
    area2 = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(outline, outline[1:] + outline[:1]))
    if area2 < 0:
        outline = outline[::-1]   # counter-clockwise in (x, y): the rim's outward side is (dy, -dx)
    front = [m.v(centre + xaxis * x + yaxis * y + normal * th) for x, y in outline]
    backv = [m.v(centre + xaxis * x + yaxis * y - normal * th) for x, y in outline]
    for a, b, c in tessellate_polygon([[V((x, y, 0)) for x, y in outline]]):
        m.face([front[a], front[b], front[c]], [outline[a], outline[b], outline[c]], 0, normal)
        m.face([backv[a], backv[b], backv[c]], [outline[a], outline[b], outline[c]], 0, -normal)
    n = len(outline)
    for i in range(n):
        i2 = (i + 1) % n
        (x0, y0), (x1, y1) = outline[i], outline[i2]
        out = xaxis * (y1 - y0) - yaxis * (x1 - x0)
        m.face([front[i], backv[i], backv[i2], front[i2]], [(0, 0), (0, 1), (1, 1), (1, 0)], 0, out)


CROWN_FACE = V((0, -0.75, 0.66)).normalized()
CROWN_AT = TIE + V((0, -0.14, 0.05))
CROWN_UP = V((0, 0.66, 0.75)).normalized()   # up the crown's face


def clasp(h, m):
    """The silver clasp at the tie: a band round it; at its front a pointed crown, its tallest point
    over the red gem; at its back a diamond clasp over the ribbon's knot."""
    seg, sides_ = h.r["ring"]
    side = TAIL_DIR.cross(V((0, 0, 1))).normalized()
    nrm = side.cross(TAIL_DIR).normalized()
    K.torus(m, TIE + TAIL_DIR * 0.02, side, nrm, 0.135, 0.125, 0.03, seg, sides_, 0)
    outline = [(-0.13, 0.0), (-0.15, 0.1), (-0.09, 0.07), (-0.05, 0.15), (0.0, 0.25), (0.05, 0.15), (0.09, 0.07),
               (0.15, 0.1), (0.13, 0.0), (0.0, -0.04)]
    plate(m, CROWN_AT, V((1, 0, 0)), CROWN_UP, CROWN_FACE, outline, 0.025)
    dia = [(0.0, 0.11), (0.08, 0.0), (0.0, -0.13), (-0.08, 0.0)]
    plate(m, TIE + V((0, 0.17, 0.0)), V((-1, 0, 0)), V((0, -0.2, 1)).normalized(), V((0, 1, 0.2)).normalized(), dia, 0.025)


def gem(h, m):
    """The red gem set in the crown."""
    c = CROWN_AT + CROWN_FACE * 0.03 + CROWN_UP * 0.08
    K.cylinder(m, c, CROWN_FACE, CROWN_UP, V((1, 0, 0)), 0.035, 0.03, 24 if h.hi else 6, 0)


def ribbons(h, m):
    """The crimson ribbon: a bow of two loops at the tie, two long tails down the middle of the tail
    (forked ends), and one streaming out to the wearer's left."""
    r = h.r

    def strip(pts, width, notch, wide):
        path = K.resample([V(p) for p in pts], r["rib_step"])
        H.ribbon(m, path, lambda k, n: width, wide, 0, notch=notch, cols=r["rib_cols"])
    for s in (1, -1):   # the bow's loops, out to each side of the knot and back
        k = TIE + V((0, 0.16, -0.02))
        pts = [k, k + V((0.12 * s, 0.05, 0.1)), k + V((0.26 * s, 0.06, 0.06)), k + V((0.24 * s, 0.07, -0.06)), k + V((0.08 * s, 0.04, -0.05))]
        strip(pts, 0.11, 0.0, lambda kk: V((0, 0.3, 1)))
    for s, end in ((1, 1.25), (-1, 0.95)):   # the tails, facing back, turning a little
        pts = [TIE + V((0.05 * s, 0.17, -0.06)), (0.08 * s, 0.6, 3.22), (0.1 * s, 1.27, 2.75), (0.15 * s, 1.33, 2.2),
               (0.06 * s, 1.29, 1.6), (0.16 * s, 1.22, end)]

        def wide(kk, s=s):
            a = 0.15 * math.sin(kk * 0.6 + s)
            return V((math.cos(a), math.sin(a), 0))
        strip(pts, 0.12, 0.08, wide)
    # streaming back and down past the tail's left side, its face to the side
    pts = [TIE + V((0.12, 0.14, -0.02)), (0.3, 0.6, 3.25), (0.58, 1.1, 3.0), (0.74, 1.42, 2.62), (0.8, 1.6, 2.15), (0.84, 1.68, 1.75)]

    def flutter(kk):
        a = 0.5 * math.sin(kk * 0.9)
        return V((0.15 * math.sin(a), math.cos(a) * 0.5, math.cos(a)))
    strip(pts, 0.11, 0.07, flutter)


def pieces(res, coll, M, tree):
    h = Hair(res)
    rnd = random.Random(11)
    out = []

    def shell(mesh, name, mats, thick, kind):
        o = mesh.object(name + "_" + res, coll, mats)
        if thick:
            K.solidify(o, thick)
        o["kind"] = kind
        out.append(o)
        return o

    cols, rows = h.r["cap"]
    shell(H.scalp(tree, cols, rows, hairline, lambda a, t: 0.03, None, 0), "MHP_Cap", [M["hair"], M["inside"]], 0.025, "hair")
    m = K.Mesh()
    fringe(h, m, rnd)
    shell(m, "MHP_Fringe", [M["hair"]], 0, "hair")
    m = K.Mesh()
    sides(h, m, rnd)
    shell(m, "MHP_Sides", [M["hair"]], 0, "hair")
    m = K.Mesh()
    crown_hair(h, m, rnd, tree)
    back_hair(h, m, rnd, tree)
    spray(h, m, rnd)
    shell(m, "MHP_Crown", [M["hair"]], 0, "hair")
    m = K.Mesh()
    tail(h, m, rnd)
    shell(m, "MHP_Tail", [M["tail"]], 0, "hair")
    m = K.Mesh()
    flyaways(h, m, rnd)
    shell(m, "MHP_Flyaways", [M["hair"]], 0, "hair")
    m = K.Mesh()
    clasp(h, m)
    shell(m, "MHP_Clasp", [M["silver"]], 0, "metal")
    m = K.Mesh()
    gem(h, m)
    shell(m, "MHP_Gem", [M["gem"]], 0, "metal")
    m = K.Mesh()
    ribbons(h, m)
    shell(m, "MHP_Ribbons", [M["silk"], M["silk"]], 0.012, "cloth")
    return out


def materials():
    return {"hair": H.mat_anime_hair("MHP_Hair"),
            "tail": H.mat_anime_hair("MHP_TailHair", tip=(0.085, 0.016, 0.016), tip_from=0.5),
            "inside": H.mat_flat("MHP_HairInside", (0.004, 0.003, 0.004)),
            "silver": H.mat_silver("MHP_Silver"), "silk": H.mat_silk("MHP_Silk"),
            "gem": K.mat_flat("MHP_Gem", (0.5, 0.0, 0.03), 0.1)}
