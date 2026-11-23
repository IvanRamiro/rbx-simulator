"""nightfall_kit: the geometry kit of Nightfall Citadel, the Demonic territory (2026-11-23). Plain Python, no Blender.

Built on hq_kit's containers (Geo = indexed faces, Piece = material suffix -> Geo) and windrift_kit's WP (a Piece that also carries collision boxes, marks, lights, floors and the
QA's z-fighting resolver) and on nothing of either territory's architecture: Dawnspire's marble, gold, dougong and tiered pagoda roofs and Windrift's leaning timber, verdigris
sawtooth tiles and rope are not here. Nightfall's shape language is its own:
  * heavy BATTERED black stone (every wall slopes in toward its top, string courses and corner quoins stand proud of it), crenellated tops, hard facets, no curves;
  * roofs of STANDING SEAMS: straight near-black slopes with ribs running eave to ridge, a crimson fascia along every eave and rake, a sawtooth crest of iron spikes on the ridge and
    two upswept iron horns at its ends, gable faces of plain stone; hip roofs end in one iron spike;
  * iron: spiked caps, braziers on tripods, chains, studded doors, bars; crimson cloth banners; Ember (Neon) only in small flames and cages.
Everything is authored in ROBLOX STUDS: x right, y up, z back (a piece's FRONT is -Z), the piece's origin at its floor line (y = 0 is the floor or the ground it stands on; feet sink below).
A piece has at most four material suffixes (Stone, Tile, Iron, Crimson, Ember, Timber: choose four).
"""
import math
import random

import hq_kit as K
from hq_kit import vadd, vsub, vmul, vnorm, vlen, vcross, vdot, lerp, TAU
from windrift_kit import WP as _WP, hex8, beam, post, cyl, obox, tri_prism, axes_of

S_STONE, S_TILE, S_IRON, S_CRIMSON, S_EMBER, S_TIMBER = "Stone", "Tile", "Iron", "Crimson", "Ember", "Timber"


class NP(_WP):
    """A WP that also keeps turned collision boxes (rcol: centre x, z, size x, z, y0, y1, yaw, name) in its frame, and the spots of its effects (emitters)."""

    def __init__(self):
        super().__init__()
        self.rcol = []
        self.emit = []             # (kind, (x, y, z)) in the piece frame: Flame, Embers, Ash, Glow

    def rblock(self, name, cx, cz, sx, sz, y0, y1, yaw):
        self.rcol.append((cx, cz, sx, sz, y0, y1, yaw, name))

    def absorb(self, other, t=(0.0, 0.0, 0.0), yaw=0.0, s=1.0):
        super().absorb(other, t=t, yaw=yaw, s=s)
        c, sn = math.cos(yaw), math.sin(yaw)
        for (cx, cz, sx, sz, y0, y1, ry, n) in getattr(other, "rcol", []):
            self.rcol.append((cx * c + cz * sn + t[0], -cx * sn + cz * c + t[2], sx, sz, y0 + t[1], y1 + t[1], ry + yaw, n))
        for (k, p) in getattr(other, "emit", []):
            self.emit.append((k, (p[0] * c + p[2] * sn + t[0], p[1] + t[1], -p[0] * sn + p[2] * c + t[2])))
        return self


def jit(a, b):
    s = math.sin(a[0] * 12.9898 + a[1] * 78.233 + a[2] * 37.719 + b[0] * 4.1414 + b[1] * 9.1317 + b[2] * 2.7183) * 43758.5453
    return (s - math.floor(s)) * 2 - 1


# ======================================================================================================================
# solids
# ======================================================================================================================
def frust(g, x0, x1, z0, z1, y0, y1, ix0=0.0, ix1=None, iz0=None, iz1=None):
    """A frustum: the rectangle x0..x1, z0..z1 at y0, its top at y1 drawn in by ix0 (left), ix1 (right), iz0 (front), iz1 (back); a batter."""
    ix1 = ix0 if ix1 is None else ix1
    iz0 = ix0 if iz0 is None else iz0
    iz1 = iz0 if iz1 is None else iz1
    hex8(g, [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
             (x0 + ix0, y1, z0 + iz0), (x1 - ix1, y1, z0 + iz0), (x1 - ix1, y1, z1 - iz1), (x0 + ix0, y1, z1 - iz1)])


def box(g, x0, x1, y0, y1, z0, z1):
    K.box(g, x0, x1, y0, y1, z0, z1)


def pyramid(g, cx, cz, y0, hx, hz, h, lean=(0.0, 0.0)):
    """A square pyramid (closed): base 2hx by 2hz at y0, the apex h up (and `lean` = (dx, dz) off the middle)."""
    b = [g.vert((cx - hx, y0, cz - hz)), g.vert((cx + hx, y0, cz - hz)), g.vert((cx + hx, y0, cz + hz)), g.vert((cx - hx, y0, cz + hz))]
    t = g.vert((cx + lean[0], y0 + h, cz + lean[1]))
    g.face(b[0], b[1], b[2], b[3])
    for i in range(4):
        g.face(b[i], t, b[(i + 1) % 4])
    # (faces of the base ring run the other way round the apex: orient() sorts the sign out)


def cone(g, cx, y0, cz, r, h, seg=6, phase=0.0, lean=(0.0, 0.0)):
    """A cone (closed): a seg-sided base of radius r at y0, the apex h up."""
    ring = [g.vert((cx + r * math.cos(phase + TAU * k / seg), y0, cz + r * math.sin(phase + TAU * k / seg))) for k in range(seg)]
    t = g.vert((cx + lean[0], y0 + h, cz + lean[1]))
    c = g.vert((cx, y0, cz))
    for k in range(seg):
        j = (k + 1) % seg
        g.face(c, ring[k], ring[j])
        g.face(ring[k], t, ring[j])


def pprism(g, cx, cz, y0, y1, r, seg=8, r_top=None, phase=0.0, caps=True):
    """A regular n-gon prism or frustum (radius r at y0, r_top at y1) about the vertical axis through (cx, cz); caps are fans from their middle."""
    r_top = r if r_top is None else r_top
    rb = [g.vert((cx + r * math.cos(phase + TAU * k / seg), y0, cz + r * math.sin(phase + TAU * k / seg))) for k in range(seg)]
    rt = [g.vert((cx + r_top * math.cos(phase + TAU * k / seg), y1, cz + r_top * math.sin(phase + TAU * k / seg))) for k in range(seg)]
    for k in range(seg):
        j = (k + 1) % seg
        g.face(rb[k], rt[k], rt[j], rb[j])
    if caps:
        cb, ct = g.vert((cx, y0, cz)), g.vert((cx, y1, cz))
        for k in range(seg):
            j = (k + 1) % seg
            g.face(cb, rb[k], rb[j])
            g.face(ct, rt[j], rt[k])


def ring_slab(g, cx, cz, r_in, r_out, y0, y1, a0, a1, r_in_top=None, r_out_top=None):
    """A block of a ring wall between two angles (a0 to a1, radians from +x toward +z): inner radius r_in (vertical unless r_in_top), outer r_out at y0 and r_out_top at y1."""
    r_in_top = r_in if r_in_top is None else r_in_top
    r_out_top = r_out if r_out_top is None else r_out_top

    def pt(r, a, y):
        return (cx + r * math.cos(a), y, cz + r * math.sin(a))
    hex8(g, [pt(r_in, a0, y0), pt(r_out, a0, y0), pt(r_out, a1, y0), pt(r_in, a1, y0),
             pt(r_in_top, a0, y1), pt(r_out_top, a0, y1), pt(r_out_top, a1, y1), pt(r_in_top, a1, y1)])


def wslab(g, a, b, y0, y1, tb, tt, off=0.0):
    """A battered wall slab along a -> b (x, z each): thickness tb at y0 and tt at y1, centred on the line (shifted by `off` along its left normal)."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx, nz = -uz, ux
    ax, az = a[0] + nx * off, a[1] + nz * off
    bx, bz = b[0] + nx * off, b[1] + nz * off
    hex8(g, [(ax - nx * tb / 2, y0, az - nz * tb / 2), (ax + nx * tb / 2, y0, az + nz * tb / 2), (bx + nx * tb / 2, y0, bz + nz * tb / 2), (bx - nx * tb / 2, y0, bz - nz * tb / 2),
             (ax - nx * tt / 2, y1, az - nz * tt / 2), (ax + nx * tt / 2, y1, az + nz * tt / 2), (bx + nx * tt / 2, y1, bz + nz * tt / 2), (bx - nx * tt / 2, y1, bz - nz * tt / 2)])


# ======================================================================================================================
# masonry
# ======================================================================================================================
def bmass(P, x0, x1, z0, z1, y0, y1, batter, bands=(), band_out=0.22, band_h=0.42, quoins=True, suffix=S_STONE, seed=1, sides="NESW", footing=0.0):
    """A battered stone mass: the rectangle x0..x1, z0..z1 at y0 narrowing by `batter` on every side to y1, with string courses (bands: heights over y0, each a slab standing
    band_out proud of the wall) and corner quoins (a stack of blocks at each corner, alternately long on one face and the other). `footing`: sinks the foot that much below y0
    (a plinth the ground hides). Returns the inset at height y."""
    g = P.geo(suffix)
    h = y1 - y0
    frust(g, x0, x1, z0, z1, y0 - footing, y1, batter * (h + footing) / h)

    def inset(y):
        return batter * (y - y0) / h
    for yb in bands:
        yy = y0 + yb
        i0, i1 = inset(yy), inset(yy + band_h)
        frust(g, x0 + i0 - band_out, x1 - i0 + band_out, z0 + i0 - band_out, z1 - i0 + band_out, yy, yy + band_h, band_out + (i1 - i0))
    if quoins:
        rng = random.Random(seed)
        yq = y0 + 0.6
        k = 0
        while yq < y1 - 1.0:
            qh = 0.9 + 0.5 * rng.random()
            i0 = inset(yq)
            for cx_, cz_, sx, sz in ((x0, z0, 1, 1), (x1, z0, -1, 1), (x1, z1, -1, -1), (x0, z1, 1, -1)):
                long_x = (k % 2 == 0) == ((sx * sz) > 0)
                lx, lz = (2.0, 1.1) if long_x else (1.1, 2.0)
                # the block lies on the corner, standing 0.14 proud of both faces
                xa = cx_ + sx * (i0 - 0.14)
                za = cz_ + sz * (i0 - 0.14)
                xb = xa + sx * lx
                zb = za + sz * lz
                box(g, min(xa, xb), max(xa, xb), yq, yq + qh, min(za, zb), max(za, zb))
            yq += qh + 0.04
            k += 1
    return inset


def merlons(P, a, b, y, h=1.5, w=1.35, gap=1.05, thick=1.5, off=0.0, suffix=S_STONE, tip=0.2, skip=()):
    """A row of merlons along a -> b (x, z each) standing on a wall top at y: each a block w long and `thick` through, its top drawn in by `tip` on every side (a hard facet),
    with a gap between. Returns the merlons' centres (for spikes)."""
    g = P.geo(suffix)
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx, nz = -uz, ux
    n = max(1, int(round((L + gap) / (w + gap))))
    pitch = L / n
    out = []
    for i in range(n):
        if i in skip:
            continue
        s0 = pitch * i + (pitch - w) / 2
        s1 = s0 + w
        pts = []
        for s, hh in ((s0, 0.0), (s1, 0.0)):
            pass
        ax, az = a[0] + ux * s0 + nx * off, a[1] + uz * s0 + nz * off
        bx, bz = a[0] + ux * s1 + nx * off, a[1] + uz * s1 + nz * off
        t = thick / 2
        bot = [(ax - nx * t, y - 0.04, az - nz * t), (ax + nx * t, y - 0.04, az + nz * t), (bx + nx * t, y - 0.04, bz + nz * t), (bx - nx * t, y - 0.04, bz - nz * t)]
        tt = [(ax + ux * tip - nx * (t - tip), y + h, az + uz * tip - nz * (t - tip)), (ax + ux * tip + nx * (t - tip), y + h, az + uz * tip + nz * (t - tip)),
              (bx - ux * tip + nx * (t - tip), y + h, bz - uz * tip + nz * (t - tip)), (bx - ux * tip - nx * (t - tip), y + h, bz - uz * tip - nz * (t - tip))]
        hex8(g, bot + tt)
        out.append(((ax + bx) / 2, y + h, (az + bz) / 2))
    return out


def spikes(P, pts, h=1.1, r=0.22, suffix=S_IRON, lift=-0.05):
    """An iron spike (a four-sided pyramid) on each point."""
    g = P.geo(suffix)
    for (x, y, z) in pts:
        pyramid(g, x, z, y + lift, r, r, h + 0.05)


# ======================================================================================================================
# roofs
# ======================================================================================================================
def slab(g, E0, E1, R1, R0, th):
    """A roof slab: the quad E0 E1 (eave edge) R1 R0 (ridge edge) as its top, th thick under it along the quad's normal."""
    n = vnorm(vcross(vsub(E1, E0), vsub(R0, E0)))
    if n[1] < 0:
        n = vmul(n, -1.0)
    d = vmul(n, -th)
    hex8(g, [vadd(E0, d), vadd(E1, d), vadd(R1, d), vadd(R0, d), E0, E1, R1, R0])
    return n


def ribs(P, E0, E1, R1, R0, n, gap=2.4, w=0.3, h=0.3, suffix=S_TILE):
    """Standing seams: a thin rib every `gap` studs along the eave edge, running from the eave up to the ridge on the slope's surface (they stand h proud of it)."""
    g = P.geo(suffix)
    L = vlen(vsub(E1, E0))
    cnt = max(1, int(L / gap))
    for i in range(cnt + 1):
        s = (i + 0.5) / (cnt + 1) if cnt > 0 else 0.5
        a = vadd(vmul(E0, 1 - s), vmul(E1, s))
        b = vadd(vmul(R0, 1 - s), vmul(R1, s))
        a2 = vadd(vadd(a, vmul(vsub(b, a), 0.04)), vmul(n, -0.05))
        b2 = vadd(vadd(b, vmul(vsub(a, b), 0.03)), vmul(n, -0.05))
        d = vsub(b2, a2)
        # a rib: a box along the slope, its section w x (h + 0.05) with its base 0.05 in the slab
        u = vnorm(d)
        side = vnorm(vcross(u, n))
        up = n
        ctr = vadd(vmul(vadd(a2, b2), 0.5), vmul(up, (h + 0.05) / 2))
        obox(g, ctr, u, up, side, vlen(d) / 2, (h + 0.05) / 2, w / 2)


def fascia(P, a, b, w=0.5, h=0.9, up=(0.0, 1.0, 0.0), suffix=S_CRIMSON):
    beam(P.geo(suffix), a, b, w, h, up=up)


def roof_gable(P, x0, x1, zf, zb, y_e, y_r, over=1.8, rake=1.4, th=0.6, rib_gap=2.4, horns=True, teeth=True, z_r=None, seed=1, gable_fill=True, fill_t=0.7, wall_y=None):
    """A hard gable roof over x0..x1 with its eaves at z = zf (front) and zb (back) at height y_e and its ridge at z_r (the middle) at y_r: two straight slopes (near-black
    Tile) with standing seams, a crimson fascia along every eave and rake, an iron ridge with a sawtooth crest of spikes and two upswept horns at the ends, stone gable faces.
    Returns the ridge ends."""
    z_r = (zf + zb) / 2 if z_r is None else z_r
    xa, xb = x0 - rake, x1 + rake
    gt = P.geo(S_TILE)
    sf = (zf - z_r, y_e - y_r)
    sb = (zb - z_r, y_e - y_r)
    Lf, Lb = math.hypot(*sf), math.hypot(*sb)
    F = [(xa, y_r + sf[1] * (1 + over / Lf), z_r + sf[0] * (1 + over / Lf)), (xb, y_r + sf[1] * (1 + over / Lf), z_r + sf[0] * (1 + over / Lf))]
    Bk = [(xa, y_r + sb[1] * (1 + over / Lb), z_r + sb[0] * (1 + over / Lb)), (xb, y_r + sb[1] * (1 + over / Lb), z_r + sb[0] * (1 + over / Lb))]
    R = [(xa, y_r, z_r), (xb, y_r, z_r)]
    nf = slab(gt, F[0], F[1], R[1], R[0], th)
    nb = slab(gt, Bk[1], Bk[0], R[0], R[1], th)
    if rib_gap:
        ribs(P, F[0], F[1], R[1], R[0], nf, gap=rib_gap)
        ribs(P, Bk[1], Bk[0], R[0], R[1], nb, gap=rib_gap)
    # crimson fascia: along both eaves, and up the rake of each end
    fascia(P, (F[0][0], F[0][1] - 0.05, F[0][2]), (F[1][0], F[1][1] - 0.05, F[1][2]), 0.55, 0.95)
    fascia(P, (Bk[0][0], Bk[0][1] - 0.05, Bk[0][2]), (Bk[1][0], Bk[1][1] - 0.05, Bk[1][2]), 0.55, 0.95)
    for xx in (xa, xb):
        fascia(P, (xx, F[0][1] - 0.05, F[0][2]), (xx, y_r, z_r), 0.5, 0.8, up=(1.0, 0.0, 0.0))
        fascia(P, (xx, Bk[0][1] - 0.05, Bk[0][2]), (xx, y_r, z_r), 0.5, 0.8, up=(1.0, 0.0, 0.0))
    gi = P.geo(S_IRON)
    beam(gi, (xa - 0.2, y_r + 0.1, z_r), (xb + 0.2, y_r + 0.1, z_r), 0.7, 0.7)
    if teeth:
        n = max(2, int((xb - xa) / 2.6))
        for i in range(n + 1):
            x = lerp(xa + 1.0, xb - 1.0, i / n)
            pyramid(gi, x, z_r, y_r + 0.4, 0.34, 0.34, 1.15 + 0.35 * (i % 2))
    if horns:
        for (xx, sg) in ((xa, -1.0), (xb, 1.0)):
            a = (xx - sg * 0.1, y_r + 0.2, z_r)
            tri_prism(gi, (a[0], a[1], a[2] - 0.5), (a[0], a[1], a[2] + 0.5), (a[0] + sg * 1.4, a[1] + 3.4, a[2]), 0.55, (1.0, 0.0, 0.0))
    if gable_fill:
        gs = P.geo(S_STONE)
        wy = y_e if wall_y is None else wall_y
        for xx in (x0, x1):
            sgn = -1.0 if xx == x0 else 1.0
            tri_prism(gs, (xx, wy, zf), (xx, wy, zb), (xx, y_r - 0.05, z_r), fill_t, (1.0, 0.0, 0.0))
    return dict(R0=R[0], R1=R[1], F=F, B=Bk)


def roof_hip(P, cx, cz, hx, hz, y_e, y_r, over=1.4, th=0.55, rib_gap=2.4, ridge=0.0, spike=3.2, seed=1, trim=True):
    """A hard hip roof over a rectangle (half sizes hx, hz about cx, cz): four straight slopes meeting along a ridge of half length `ridge` (0 = a point), standing seams,
    a crimson fascia on the eaves, iron hip caps and one iron spike at the top."""
    gt, gi = P.geo(S_TILE), P.geo(S_IRON)
    k = (hz + over) / hz
    ye = y_e - (y_r - y_e) * (over / max(hz, 0.5))
    sx, sz = hx + over, hz + over
    E = [(cx - sx, ye, cz - sz), (cx + sx, ye, cz - sz), (cx + sx, ye, cz + sz), (cx - sx, ye, cz + sz)]
    r = ridge
    Rp = [(cx - r, y_r, cz), (cx + r, y_r, cz)]
    if r < 0.05:
        Rp = [(cx - 0.02, y_r, cz - 0.02), (cx + 0.02, y_r, cz + 0.02)]
    planes = [(E[0], E[1], Rp[1], Rp[0]), (E[2], E[3], Rp[0], Rp[1]), (E[1], E[2], Rp[1], Rp[1]), (E[3], E[0], Rp[0], Rp[0])]
    for i, (e0, e1, r1, r0) in enumerate(planes):
        if i >= 2 and vlen(vsub(r1, r0)) < 1e-6:
            r1 = (r1[0] + 0.02 * (1 if i == 2 else -1), r1[1], r1[2] + 0.02)
        n = slab(gt, e0, e1, r1, r0, th)
        if rib_gap and vlen(vsub(e1, e0)) > 5:
            ribs(P, e0, e1, r1, r0, n, gap=rib_gap)
    if trim:
        for a, b in ((E[0], E[1]), (E[1], E[2]), (E[2], E[3]), (E[3], E[0])):
            fascia(P, (a[0], a[1] - 0.05, a[2]), (b[0], b[1] - 0.05, b[2]), 0.55, 0.95)
    for e, rr in ((E[0], Rp[0]), (E[1], Rp[1]), (E[2], Rp[1]), (E[3], Rp[0])):
        beam(gi, (e[0], e[1] + 0.05, e[2]), (rr[0], rr[1] + 0.06, rr[2]), 0.42, 0.42)
    if spike:
        pyramid(gi, cx, cz, y_r - 0.1, 0.42, 0.42, spike)
    return dict(E=E, R=Rp)


# ======================================================================================================================
# iron: braziers, chains, bars, banners
# ======================================================================================================================
def brazier(P, x, y, z, bowl=1.5, stand=3.0, ember=True, legs=3, spike_legs=True, light=True):
    """An iron fire bowl on a spiked tripod: three splayed legs, a ring band, a faceted bowl, a crown of four spikes round the rim and (Ember) a small cone of flame. y = the
    ground. Registers a flame emitter and returns the light spot."""
    gi = P.geo(S_IRON)
    for k in range(legs):
        a = TAU * k / legs + 0.4
        foot = (x + math.cos(a) * bowl * 0.95, y - 0.05, z + math.sin(a) * bowl * 0.95)
        top = (x + math.cos(a) * bowl * 0.45, y + stand, z + math.sin(a) * bowl * 0.45)
        cyl(gi, foot, top, 0.2, 0.15, seg=4, caps=True, phase=0.3)
        if spike_legs:
            pyramid(gi, foot[0], foot[2], y - 0.35, 0.16, 0.16, 0.5)
    pprism(gi, x, z, y + stand - 0.1, y + stand + 0.55, bowl * 0.55, seg=8, r_top=bowl * 1.0, caps=True)
    pprism(gi, x, z, y + stand + 0.5, y + stand + 0.95, bowl * 1.0, seg=8, r_top=bowl * 0.9, caps=False)
    for k in range(4):
        a = TAU * k / 4 + math.pi / 4
        px, pz = x + math.cos(a) * bowl * 0.95, z + math.sin(a) * bowl * 0.95
        cone(gi, px, y + stand + 0.85, pz, 0.15, 0.8, seg=4)
    if ember:
        ge = P.geo(S_EMBER)
        cone(ge, x, y + stand + 0.45, z, bowl * 0.55, bowl * 1.4, seg=5, phase=0.2, lean=(0.1, 0.0))
    if light:
        P.lights.append((x, y + stand + 1.8, z))
    P.emit.append(("Flame", (x, y + stand + 1.0, z)))
    return (x, y + stand + 1.8, z)


def chain_swag(P, a, b, sag=0.8, links=5, size=0.55, suffix=S_IRON):
    """A hanging chain: `links` boxes alternately turned a quarter along a parabola from a to b."""
    g = P.geo(suffix)
    pts = []
    for i in range(links + 1):
        t = i / links
        p = vadd(vmul(a, 1 - t), vmul(b, t))
        pts.append((p[0], p[1] - sag * 4 * t * (1 - t), p[2]))
    for i, (p0, p1) in enumerate(zip(pts, pts[1:])):
        d = vsub(p1, p0)
        u = vnorm(d)
        up = (0.0, 1.0, 0.0) if i % 2 == 0 else vnorm(vcross(u, (0.0, 1.0, 0.0)))
        if abs(vdot(up, u)) > 0.95:
            up = (1.0, 0.0, 0.0)
        side = vcross(u, up)
        c = vmul(vadd(p0, p1), 0.5)
        obox(g, c, u, vnorm(vcross(side, u)), vnorm(side), vlen(d) / 2 * 1.04, size * 0.22, size * 0.3)


def banner(P, x, y_top, z, w=2.4, h=7.0, plane="xy", suffix=S_CRIMSON, notch=True, tilt=0.0):
    """A crimson cloth banner hanging from y_top: a slab w wide, h tall, 0.16 thick, with a swallow-tail (two points) at the foot; plane xy = facing -z/+z, zy = facing x."""
    g = P.geo(suffix)
    t = 0.08
    if plane == "xy":
        pts = [(x - w / 2, y_top, z), (x + w / 2, y_top, z), (x + w / 2, y_top - h, z), (x, y_top - h + (1.1 if notch else 0.0), z), (x - w / 2, y_top - h, z)]
        nrm = (0.0, 0.0, 1.0)
    else:
        pts = [(x, y_top, z - w / 2), (x, y_top, z + w / 2), (x, y_top - h, z + w / 2), (x, y_top - h + (1.1 if notch else 0.0), z), (x, y_top - h, z - w / 2)]
        nrm = (1.0, 0.0, 0.0)
    pts = [(p[0] + nrm[0] * tilt * (p[1] - y_top), p[1], p[2] + nrm[2] * tilt * (p[1] - y_top)) for p in pts]
    # a pentagon plate: triangles (0 1 2), (0 2 3), (0 3 4) as thin prisms sharing nothing (each its own solid): use a fan of three
    for tri in ((pts[0], pts[1], pts[2]), (pts[0], pts[2], pts[3]), (pts[0], pts[3], pts[4])):
        tri_prism(g, tri[0], tri[1], tri[2], t * 2, nrm)


def iron_bars(P, x0, x1, y0, y1, z, n=7, w=0.22, spike=0.5, suffix=S_IRON):
    """Vertical iron bars between x0 and x1 at z, from y0 to y1, each with a spike on its top, joined by two cross bars."""
    g = P.geo(suffix)
    for i in range(n):
        x = lerp(x0 + w, x1 - w, i / max(1, n - 1))
        box(g, x - w / 2, x + w / 2, y0, y1, z - w / 2, z + w / 2)
        pyramid(g, x, z, y1 - 0.02, w * 0.75, w * 0.75, spike)
    for yy in (y0 + (y1 - y0) * 0.25, y0 + (y1 - y0) * 0.7):
        box(g, x0, x1, yy - 0.1, yy + 0.1, z - w * 0.7, z + w * 0.7)


def studded_door(P, x0, x1, y0, y1, z, t=0.35, suffix=S_TIMBER, iron=S_IRON):
    """A door leaf (timber) with an iron band across and a row of studs (small blocks)."""
    box(P.geo(suffix), x0, x1, y0, y1, z - t / 2, z + t / 2)
    gi = P.geo(iron)
    for yy in (y0 + (y1 - y0) * 0.22, y0 + (y1 - y0) * 0.7):
        box(gi, x0 - 0.04, x1 + 0.04, yy - 0.28, yy + 0.28, z - t / 2 - 0.07, z + t / 2 + 0.07)
    n = max(2, int((x1 - x0) / 0.9))
    for i in range(n):
        x = lerp(x0 + 0.35, x1 - 0.35, i / max(1, n - 1))
        pyramid(gi, x, z - t / 2 - 0.06, (y0 + y1) / 2 - 0.2, 0.14, 0.14, 0.2) if False else None


def seed_of(name):
    return sum((i + 1) * ord(c) for i, c in enumerate(name)) % 100003
