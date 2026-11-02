"""The Eclipse Exorcist's seal cord (run inside Blender; a rigid Waist accessory on
WaistCenterAttachment), worn over the robe.

The rope that binds the seal: a braided crimson cord of two twisted strands round the waist, tied
off-centre on the wearer's left in a heavy wrapped knot with one loop flaring up, its two ends
hanging in silver-capped crimson tassels. Below the knot hangs the eclipse seal: an eight-pointed
silver star round a black eclipse disc, and under it a red ofuda tag written in black sigils. On the
left hip two white shide papers zigzag down from the cord; across the front a silver chain sags
from the knot to the right hip, a small seal-kunai hanging from its lowest link.

Built twice (see ee_kit): pieces(res="hi") for the bake, pieces(res="low") for the game mesh.
"""
import math

from mathutils import Vector

import ee_kit as K

V = Vector
TAU = K.TAU

RES = {
    "hi": {"cord_step": 0.02, "cord_sides": 12, "fibre": 1.0, "link": (24, 8), "tassel": 40, "detail": True},
    "low": {"cord_step": 0.12, "cord_sides": 5, "fibre": 0.0, "link": (6, 4), "tassel": 8, "detail": False},
}
CORD_Z = 0.32
CORD_AB = (1.16, 0.71)        # the cord's centre line round the robe (the stole lies at 0.62)
STRAND = 0.05                 # each strand's radius
TWIST_R = 0.042               # how far each strand winds from the centre line
TWISTS = 2.3                  # twists per stud
KNOT_T = 0.06                 # where round the waist the knot sits: just left of centre, clear of the stole
SEAL = 1.5                    # the seal's scale (1: a 0.46-stud star)


def ring_point(t, z=CORD_Z):
    x, y, nrm = K.se(t, CORD_AB[0], CORD_AB[1], 4.0)
    return V((x, y, z)), nrm


def strands(m, path, r, mat, closed=False, radius=STRAND, twist_r=TWIST_R):
    """Two strands wound round each other along `path`: the braid."""
    fr = K.frames(path)
    along = [0.0]
    for a, b in zip(path, path[1:]):
        along.append(along[-1] + (b - a).length)
    for s in range(2):
        curve = []
        for c, (t, side, up), d in zip(path, fr, along):
            ang = TAU * TWISTS * d + math.pi * s
            curve.append(c + (side * math.cos(ang) + up * math.sin(ang)) * twist_r)
        K.tube(m, curve, lambda k, n: radius, r["cord_sides"], mat, cap=not closed, twist=0.35 if r["fibre"] else 0.0, uv_v=3.0)


KNOT_HALF = 0.16              # half the knot's wrapping, along the cord


def waist_cord(r):
    """The cord round the waist: from inside the knot's wrapping all the way round and back into it
    (cut by length along the cord: near the front a small turn of angle covers a long way)."""
    m = K.Mesh()
    n = 2000
    ring = [ring_point(KNOT_T + TAU * k / n)[0] for k in range(n + 1)]
    along = [0.0]
    for a, b in zip(ring, ring[1:]):
        along.append(along[-1] + (b - a).length)
    total = along[-1]
    gap = KNOT_HALF * 0.75
    pts = [p for p, d in zip(ring, along) if gap <= d <= total - gap]
    path = K.resample(pts, r["cord_step"])
    strands(m, path, r, 0)
    return m


def knot_centre():
    p, nrm = ring_point(KNOT_T)
    return p + nrm * 0.04, nrm


def knot(r):
    """The knot: a thick wrapping round the cord where its ends cross, three turns standing out, and
    one loop flaring up and out to the wearer's right."""
    m = K.Mesh()
    c, nrm = knot_centre()
    along = (ring_point(KNOT_T + 0.01)[0] - ring_point(KNOT_T - 0.01)[0]).normalized()
    up = V((0, 0, 1))
    # the wrapping: a short barrel along the cord, its turns as ridges
    n_al, n_round = (40, 24) if r["detail"] else (6, 10)
    pts, uvs = [], []
    for j in range(n_al + 1):
        s = j / n_al - 0.5
        rad = 0.135 * (1 - (2 * s) ** 6 * 0.35)
        if r["detail"]:
            rad += 0.012 * abs(math.sin(s * math.pi * 3))
        row = []
        side = along.cross(up).normalized()
        for i in range(n_round):
            a = TAU * i / n_round
            row.append(c + along * (s * KNOT_HALF * 2) + (up * math.cos(a) + side * math.sin(a)) * rad)
        pts.append(row)
        uvs.append([(i / n_round, s * 2) for i in range(n_round + 1)])
    rows = m.grid(pts, uvs, 0, closed=True, outward=lambda j, i, cc: cc - (c + along * ((j / n_al - 0.5) * KNOT_HALF * 2)))
    for end, sgn in ((rows[0], -1), (rows[-1], 1)):
        cc = m.v(c + along * (KNOT_HALF * sgn))
        for i in range(n_round):
            m.face([end[i], end[(i + 1) % n_round], cc], [(0, 0), (1, 0), (0.5, 0.5)], 0, along * sgn)
    # the loop: out of the knot's top, up and over to the wearer's right, back into its side
    side = along
    loop = [c + up * 0.08, c + up * 0.24 - side * 0.06 + nrm * 0.04, c + up * 0.3 - side * 0.24 + nrm * 0.06,
            c + up * 0.18 - side * 0.36 + nrm * 0.05, c + up * 0.02 - side * 0.26 + nrm * 0.03, c - side * 0.1]
    strands(m, K.resample(loop, r["cord_step"] * 0.7), r, 0, radius=0.042, twist_r=0.034)
    return m


def hanging_ends(r):
    """The cord's two ends hanging from the knot, the longer swinging out to the left; returns the
    mesh and where each tassel hangs (its top, its axis)."""
    m = K.Mesh()
    c, nrm = knot_centre()
    along = (ring_point(KNOT_T + 0.01)[0] - ring_point(KNOT_T - 0.01)[0]).normalized()
    ends = []
    # one each side of the seal, which hangs in front between them
    for length, swing, lean in ((0.86, 0.24, 0.03), (0.62, -0.22, 0.02)):
        path = [c - V((0, 0, 0.06)), c + along * (swing * 0.3) + nrm * lean - V((0, 0, length * 0.4)),
                c + along * swing + nrm * (lean * 1.6) - V((0, 0, length))]
        path = K.resample(path, r["cord_step"])
        strands(m, path, r, 0, radius=0.04, twist_r=0.032)
        ends.append((path[-1], (path[-1] - path[-2]).normalized()))
    return m, ends


def tassel(r, top, axis):
    """A silver cap and a crimson tassel flaring below it: many fine threads (or a ridged cone)."""
    cap, threads = K.Mesh(), K.Mesh()
    axis = axis.normalized()
    side = axis.cross(V((1, 0, 0)) if abs(axis.x) < 0.9 else V((0, 1, 0))).normalized()
    other = axis.cross(side)
    # the cap: a short silver collar
    n = 16 if r["detail"] else 8
    ring_pts = []
    for z, rad in ((-0.02, 0.06), (0.06, 0.078), (0.1, 0.07)):
        ring_pts.append([top + axis * z + (side * math.cos(TAU * i / n) + other * math.sin(TAU * i / n)) * rad for i in range(n)])
    rows = cap.grid(ring_pts, [[(i / n, k) for i in range(n + 1)] for k in range(3)], 0, closed=True,
                    outward=lambda j, i, cc: cc - (top + axis * 0.05))
    for end, d, sgn in ((rows[0], -0.02, -1), (rows[-1], 0.1, 1)):
        cc = cap.v(top + axis * d)
        for i in range(n):
            cap.face([end[i], end[(i + 1) % n], cc], [(0, 0), (1, 0), (0.5, 0.5)], 0, axis * sgn)
    # the tassel: a flaring cone of threads
    base = top + axis * 0.1
    length = 0.42
    if r["detail"]:
        for k in range(r["tassel"]):
            a = TAU * k / r["tassel"]
            spread = 0.05 + 0.035 * ((k * 7) % 5) / 5
            d0 = side * math.cos(a) + other * math.sin(a)
            curve = [base + d0 * 0.045, base + axis * length * 0.5 + d0 * (0.05 + spread), base + axis * length * (0.95 + 0.08 * ((k * 3) % 4) / 4) + d0 * (0.06 + spread * 1.3)]
            K.tube(threads, K.resample(curve, 0.03), lambda kk, nn: 0.009 * (1 - kk / max(1, nn - 1) * 0.6), 5, 0, cap=True, uv_v=6.0)
    else:
        nn = r["tassel"]
        pts = []
        for z, rad in ((0.0, 0.055), (0.5, 0.095), (1.0, 0.12)):
            pts.append([base + axis * (length * z) + (side * math.cos(TAU * i / nn) + other * math.sin(TAU * i / nn)) * rad for i in range(nn)])
        rows = threads.grid(pts, [[(i / nn, z) for i in range(nn + 1)] for z in range(3)], 0, closed=True,
                            outward=lambda j, i, cc: cc - (base + axis * (length * j / 2)))
        for end, z, sgn in ((rows[0], 0.0, -1), (rows[-1], 1.0, 1)):
            cc = threads.v(base + axis * (length * z))
            for i in range(nn):
                threads.face([end[i], end[(i + 1) % nn], cc], [(0, 0), (1, 0), (0.5, 0.5)], 0, axis * sgn)
    return cap, threads


def seal_frame():
    """Where the eclipse seal hangs: below the knot, facing out from the waist."""
    c, nrm = knot_centre()
    centre = c + nrm * 0.16 - V((0, 0, 0.5))
    return centre, nrm


def seal_star(r):
    """The eclipse seal: an eight-pointed star of silver, its four long points and four short ones
    each ridged down the middle (a raised spine), round a ring that holds the eclipse disc; a small
    ring on its top point hangs it from the knot."""
    m = K.Mesh()
    c, nrm = seal_frame()
    up = V((0, 0, 1))
    side = nrm.cross(up).normalized()
    up = side.cross(nrm).normalized()
    pts_outline = []
    for k in range(16):
        a = TAU * k / 16 + math.pi / 2
        if k % 2 == 0:
            rad = 0.23 if (k // 2) % 2 == 0 else 0.13
            if k == 0:
                rad = 0.2
        else:
            rad = 0.095
        pts_outline.append(c + (up * math.sin(a) + side * math.cos(a)) * rad * SEAL)
    front = m.v(c + nrm * 0.07 * SEAL)
    back = m.v(c - nrm * 0.025 * SEAL)
    ring = [m.v(p) for p in pts_outline]
    for k in range(16):
        k2 = (k + 1) % 16
        m.face([ring[k], ring[k2], front], [(0, 0), (1, 0), (0.5, 1)], 0, nrm)
        m.face([ring[k2], ring[k], back], [(0, 0), (1, 0), (0.5, 1)], 0, -nrm)
    # the hanging ring on the top point
    seg, sides = r["link"]
    ring_c = c + up * 0.222 * SEAL
    K.torus(m, ring_c, up, nrm, 0.035 * SEAL, 0.035 * SEAL, 0.011 * SEAL, seg, sides, 0)
    return m


def seal_hanger(r):
    """The short cord the seal hangs by: from under the knot, through the star's ring."""
    m = K.Mesh()
    kc, knrm = knot_centre()
    c, nrm = seal_frame()
    up = V((0, 0, 1))
    side = nrm.cross(up).normalized()
    up2 = side.cross(nrm).normalized()
    ring_top = c + up2 * (0.222 + 0.035) * SEAL
    path = [kc - up * 0.1 + knrm * 0.06, (kc - up * 0.1 + ring_top) / 2 + nrm * 0.03, ring_top - up2 * 0.02]
    K.tube(m, K.resample(path, r["cord_step"] / 3), lambda kk, nn: 0.016, 6 if r["detail"] else 4, 0, cap=True, uv_v=3.0)
    return m


def eclipse_disc(r):
    """The eclipse in the seal's heart: a black disc standing proud inside a round silver bezel."""
    bezel, disc = K.Mesh(), K.Mesh()
    c, nrm = seal_frame()
    up = V((0, 0, 1))
    side = nrm.cross(up).normalized()
    up = side.cross(nrm).normalized()
    seg, sides = (40, 10) if r["detail"] else (12, 5)
    K.torus(bezel, c + nrm * 0.075 * SEAL, up, side, 0.052 * SEAL, 0.052 * SEAL, 0.012 * SEAL, seg, sides, 0)
    K.cylinder(disc, c + nrm * 0.06 * SEAL, nrm, up, side, 0.044 * SEAL, 0.05 * SEAL, 32 if r["detail"] else 10, 0)
    return bezel, disc


def ofuda(r):
    """The red ofuda tag below the seal, hung by a short cord: paper with a slight curl. UVs: u across,
    v down it (the sigils follow them)."""
    m, cordm = K.Mesh(), K.Mesh()
    c, nrm = seal_frame()
    up = V((0, 0, 1))
    side = nrm.cross(up).normalized()
    top = c - up * 0.27 * SEAL
    w, h = 0.2, 0.52
    nu, nv = (6, 16) if r["detail"] else (2, 3)
    pts, uvs = [], []
    for j in range(nv + 1):
        v = j / nv
        row, uvrow = [], []
        for i in range(nu + 1):
            u = i / nu - 0.5
            curl = 0.02 * (2 * u) ** 2 + 0.03 * v ** 2
            row.append(top + side * (u * w) - up * (v * h) + nrm * curl)
            uvrow.append((u + 0.5, v))
        pts.append(row)
        uvs.append(uvrow)
    m.grid(pts, uvs, 0, outward=lambda j, i, cc: nrm)
    K.tube(cordm, [c - up * 0.2 * SEAL, c - up * 0.235 * SEAL, top + up * 0.005], lambda kk, nn: 0.011, 6 if r["detail"] else 4, 0, cap=True)
    return m, cordm


def shide(r):
    """Two shide papers on the right hip: white strips cut and folded into a zigzag, hanging from the
    cord."""
    m = K.Mesh()
    for k, (t, length) in enumerate(((1.12, 0.6), (1.42, 0.5))):
        p, nrm = ring_point(t)
        top = p + nrm * 0.07
        up = V((0, 0, 1))
        side = nrm.cross(up).normalized()
        w = 0.11
        seg = length / 4
        for s in range(4):
            off = (s % 2) * w * 0.55 - w * 0.25
            z0, z1 = s * seg, (s + 1) * seg + 0.012
            tilt = nrm * (0.012 * s)
            quad = [top + side * (off - w / 2) - up * z0 + tilt, top + side * (off + w / 2) - up * z0 + tilt,
                    top + side * (off + w / 2) - up * z1 + tilt, top + side * (off - w / 2) - up * z1 + tilt]
            ids = [m.v(q) for q in quad]
            m.face(ids, [(0, 0), (1, 0), (1, 1), (0, 1)], 0, nrm)
    return m


def chain_path():
    """The chain's line: from the cord at the front right, sagging, to the right hip."""
    a, na = ring_point(KNOT_T - 0.2)
    b, nb = ring_point(-1.45)
    a, b = a + na * 0.07, b + nb * 0.07
    pts = []
    for k in range(41):
        s = k / 40
        # following the waist round between its ends, standing off the robe, sagging
        t = (KNOT_T - 0.2) + (-1.45 - (KNOT_T - 0.2)) * s
        p, out = ring_point(t)
        p = p + out * (0.07 + 0.1 * math.sin(math.pi * s)) - V((0, 0, 0.5 * math.sin(math.pi * s) ** 1.2))
        pts.append(p)
    return pts


def chain(r):
    """The silver chain: oval links, each turned a quarter from the last."""
    m = K.Mesh()
    path = K.resample(chain_path(), 0.075)
    seg, sides = r["link"]
    for k in range(len(path) - 1):
        c = (path[k] + path[k + 1]) / 2
        t = (path[k + 1] - path[k]).normalized()
        ref = V((0, 0, 1)) if abs(t.z) < 0.9 else V((1, 0, 0))
        s1 = t.cross(ref).normalized()
        s2 = t.cross(s1)
        side = s1 if k % 2 == 0 else s2
        K.torus(m, c, t, side, 0.055, 0.032, 0.011, seg, sides, 0)
    low = min(path, key=lambda p: p.z)
    return m, low


def kunai(r, hang):
    """The seal-kunai: a small silver throwing blade hanging point-down from the chain: a ring
    pommel, a cord-wrapped grip, a leaf blade with a raised spine."""
    m, grip = K.Mesh(), K.Mesh()
    up = V((0, 0, 1))
    # the ring
    rc = hang - up * 0.045
    seg, sides = r["link"]
    K.torus(m, rc, up, V((0, 1, 0)), 0.042, 0.042, 0.011, seg, sides, 0)
    # the grip
    g0, g1 = rc - up * 0.04, rc - up * 0.18
    K.tube(grip, [g0, (g0 + g1) / 2, g1], lambda kk, nn: 0.022, 8 if r["detail"] else 5, 0, cap=True, uv_v=12.0)
    # the blade: a leaf of four faces each side round a spine
    tip = g1 - up * 0.27
    widest = g1 - up * 0.09
    side, out = V((1, 0, 0)), V((0, -1, 0))
    outline = [g1 + side * 0.025, widest + side * 0.06, tip, widest - side * 0.06, g1 - side * 0.025]
    spine_f = [g1 + out * 0.015, widest + out * 0.02, tip]
    spine_b = [g1 - out * 0.015, widest - out * 0.02, tip]
    for sp, d in ((spine_f, out), (spine_b, -out)):
        ids = [m.v(p) for p in outline]
        sids = [m.v(p) for p in sp]
        m.face([ids[0], ids[1], sids[1], sids[0]], [(0, 0)] * 4, 0, d)
        m.face([ids[1], ids[2], sids[1]], [(0, 0)] * 3, 0, d)
        m.face([ids[2], ids[3], sids[1]], [(0, 0)] * 3, 0, d)
        m.face([ids[3], ids[4], sids[0], sids[1]], [(0, 0)] * 4, 0, d)
        m.face([ids[4], ids[0], sids[0]], [(0, 0)] * 3, 0, up)
    return m, grip


def pieces(res, coll, M):
    r = RES[res]
    out = []

    def add(mesh, name, mats, kind, smooth=True):
        o = mesh.object(name + "_" + res, coll, mats, smooth=smooth)
        o["kind"] = kind
        out.append(o)
        return o

    add(waist_cord(r), "EE_Seal_Cord", [M["cord"]], "cord")
    add(knot(r), "EE_Seal_Knot", [M["cord"]], "cord")
    ends, where = hanging_ends(r)
    add(ends, "EE_Seal_Ends", [M["cord"]], "cord")
    for k, (top, axis) in enumerate(where):
        cap, threads = tassel(r, top, axis)
        add(cap, "EE_Seal_TasselCap%d" % k, [M["silver"]], "metal")
        add(threads, "EE_Seal_Tassel%d" % k, [M["tassel"]], "cord")
    add(seal_star(r), "EE_Seal_Star", [M["silver"]], "metal", smooth=False)
    add(seal_hanger(r), "EE_Seal_Hanger", [M["cord"]], "cord")
    bezel, disc = eclipse_disc(r)
    add(bezel, "EE_Seal_Bezel", [M["silver"]], "metal")
    add(disc, "EE_Seal_Eclipse", [M["eclipse"]], "metal")
    tag, tag_cord = ofuda(r)
    o = tag.object("EE_Seal_Ofuda_" + res, coll, [M["ofuda"]])
    K.solidify(o, 0.012, lining_offset=0)
    o["kind"] = "paper"
    out.append(o)
    add(tag_cord, "EE_Seal_OfudaCord", [M["cord"]], "cord")
    sh = shide(r).object("EE_Seal_Shide_" + res, coll, [M["paper"]])
    K.solidify(sh, 0.01, lining_offset=0)
    sh["kind"] = "paper"
    out.append(sh)
    ch, low = chain(r)
    add(ch, "EE_Seal_Chain", [M["silver"]], "metal")
    blade, grip = kunai(r, low)
    add(blade, "EE_Seal_Kunai", [M["silver"]], "metal", smooth=False)
    add(grip, "EE_Seal_KunaiGrip", [M["cord_dark"]], "cord")
    return out


def materials():
    return {"cord": K.mat_cord(), "cord_dark": K.mat_cord("EE_CordDark", (0.06, 0.0, 0.01), (0.3, 0.02, 0.03)),
            "tassel": K.mat_cord("EE_Tassel", (0.45, 0.0, 0.03), (0.9, 0.08, 0.08)), "silver": K.mat_silver(),
            "eclipse": K.mat_eclipse(), "ofuda": K.mat_ofuda(), "paper": K.mat_paper()}
