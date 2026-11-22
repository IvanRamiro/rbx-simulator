"""The Demonic sword's blade (run inside Blender, headless): a shinogi-zukuri section swept down the studied outline
(sword_demonic_profile.py), at any density.

Section (one side shown, the other mirrored, across the blade from the spine u=0 to the edge u=1):
  back corner -> back flat (mune) -> flat of the upper plane (shinogi-ji) -> fuller wall -> fuller floor -> wall -> flat -> the ridge
  (shinogi) -> the face (hira), convex in six facets -> the edge bevel (ha) -> the edge.
In the scooped stretch behind the point the back's flat widens into a sloped swedge and its corner sharpens to a false edge.
Along its length the fuller (bohi) rises out of the forte and runs out before the point's yokote line, where the thickness drops
faster so the point's facets read as their own plane.

blade(m, lod, mats, uvmode): adds the solid to Mesh m. Returns the helpers the engraving needs (surface(), floor()).
"""
import math

import numpy as np

import sword_demonic_kit as KT
import sword_demonic_profile as P

smooth = KT.smoothstep
COVE_S = P.FINAL["cove_s"]
BOHI0, BOHI1 = P.S_BOHI
US = 0.40               # the ridge's place across the blade (fraction from the spine)
MUNE = 0.034            # the back flat's width, studs
BEVEL = 0.105           # the edge bevel's width, studs


def stations(lod):
    if lod == "hi":
        base = np.linspace(0.0, P.L, 300)
        extra = [BOHI0 - 0.03, BOHI0, BOHI0 + 0.03, BOHI0 + 0.07, BOHI0 + 0.12, BOHI0 + 0.16, BOHI1 - 0.16, BOHI1 - 0.12, BOHI1 - 0.07, BOHI1 - 0.03, BOHI1, BOHI1 + 0.03, COVE_S, COVE_S - 0.25, COVE_S + 0.45, P.S_YOKOTE, P.L - 0.02]
        return np.unique(np.round(np.concatenate([base, extra, np.linspace(4.2, P.L, 60)]), 5))
    mid = list(np.arange(1.0, BOHI1 - 0.2, 0.25))
    return np.array(sorted(set([0.0, 0.3, BOHI0 - 0.02, BOHI0 + 0.06, BOHI0 + 0.16] + mid + [BOHI1 - 0.16, BOHI1 - 0.04, BOHI1 + 0.04, 3.8, 3.95, 4.1, 4.25, 4.4, 4.55, 4.68, 4.8, 4.9, 4.96, P.L])))


def groove_ramp(s):
    """Depth: the fuller's ends are cut square, a chisel's end, not run out to a point (a pointed lozenge with a line in it reads as
    something else)."""
    return smooth(BOHI0, BOHI0 + 0.16, s) * (1.0 - smooth(BOHI1 - 0.16, BOHI1, s))


def groove_width(s):
    return smooth(BOHI0 - 0.02, BOHI0 + 0.05, s) * (1.0 - smooth(BOHI1 - 0.05, BOHI1 + 0.02, s))


PATCH = (0.86, 3.44)     # where the engraved fuller floor (a separate dense patch) lies
PATCH_SINK = 0.022       # how much deeper the main groove is under it, so the patch's engraving has room


def patch_mask(s):
    return smooth(PATCH[0], PATCH[0] + 0.10, s) * (1.0 - smooth(PATCH[1] - 0.10, PATCH[1], s))


def section(s, sink=False):
    """The top half's points for stations s (N,): u (N, 13) and h (N, 13), plus W, xs, and the flags per segment. `sink`: the groove is
    deeper under the engraved patch (the high-detail source only)."""
    s = np.asarray(s, dtype=np.float64)
    W = np.maximum(P.width(s), 1e-4)
    T = P.thickness(s)
    sw = smooth(COVE_S - 0.25, COVE_S + 0.45, s)
    mu = np.minimum((MUNE + 0.15 * sw) / W, 0.30)
    hback = T * 0.60 * (1 - sw) + 0.012 * sw
    hback = np.minimum(hback, T * 0.9)
    ramp = groove_ramp(s)
    c = (mu + US) / 2
    gh = 0.40 * (US - mu) * groove_width(s)
    gw = 2 * gh
    d = 0.56 * T * ramp + (PATCH_SINK * patch_mask(s) if sink else 0.0)
    bw = np.minimum(BEVEL, 0.22 * W)
    ub = 1.0 - bw / W
    he = np.minimum(0.006, 0.4 * T + 0.0004)
    hbev = 0.20 * T
    f = np.array([0.2, 0.4, 0.6, 0.8])
    N = len(s)
    u = np.zeros((N, 13))
    h = np.zeros((N, 13))
    u[:, 0], h[:, 0] = 0.0, hback
    u[:, 1], h[:, 1] = mu, T
    u[:, 2], h[:, 2] = c - gh, T
    u[:, 3], h[:, 3] = c - gh + 0.16 * gw, T - d
    u[:, 4], h[:, 4] = c + gh - 0.16 * gw, T - d
    u[:, 5], h[:, 5] = c + gh, T
    u[:, 6], h[:, 6] = US, T
    for k in range(4):
        uu = US + f[k] * (ub - US)
        u[:, 7 + k] = uu
        h[:, 7 + k] = hbev + (T - hbev) * (1 - f[k] ** 1.35)
    u[:, 11], h[:, 11] = ub, hbev
    u[:, 12], h[:, 12] = 1.0, he
    return dict(u=u, h=h, W=W, xs=P.x_spine(s), T=T, sw=sw, ramp=ramp)


def ring_points(s, sec, keep):
    """3D ring points (N, R, 3) for stations s: [back middle, top 0..12, bottom 12..0] restricted to the top indices `keep`."""
    N = len(s)
    u, h, W, xs = sec["u"][:, keep], sec["h"][:, keep], sec["W"][:, None], sec["xs"][:, None]
    x = xs - W * u
    z = np.broadcast_to((P.Z0 - s)[:, None], x.shape)
    top = np.stack([x, h, z], axis=-1)
    bot = np.stack([x, -h, z], axis=-1)[:, ::-1]
    back = np.stack([xs[:, 0], np.zeros(N), P.Z0 - s], axis=-1)[:, None, :]
    return np.concatenate([back, top, bot], axis=1)


def blade(m, lod="hi", mat=0, uvmode="shader", cap=None):
    s = stations(lod)
    sec = section(s, sink=(lod == "hi"))
    keep = list(range(13)) if lod == "hi" else [0, 1, 2, 3, 4, 5, 6, 9, 11, 12]
    Pts = ring_points(s, sec, keep)
    N, R, _ = Pts.shape
    nk = len(keep)
    # the surface's UVs
    if uvmode == "shader":
        u = sec["u"][:, keep]
        uu = np.concatenate([np.zeros((N, 1)), u, u[:, ::-1]], axis=1)
        vv = np.broadcast_to((s / P.L)[:, None], (N, R))
        UV = np.stack([uu, vv], axis=-1)
    else:     # the belt: the ring unrolled, per station 0..1 round it, along the length
        seg = np.linalg.norm(np.diff(Pts, axis=1), axis=-1)
        seg = np.concatenate([np.zeros((N, 1)), seg], axis=1)
        cum = np.cumsum(seg, axis=1)
        per = cum[:, -1:] + np.linalg.norm(Pts[:, 0] - Pts[:, -1], axis=-1)[:, None] * 0.0
        # the ring closes at the back middle: the last point's neighbour is the first
        close = np.linalg.norm(Pts[:, -1] - Pts[:, 0], axis=-1)[:, None]
        per = cum[:, -1:] + close
        uu = cum / np.maximum(per, 1e-9)
        vv = np.broadcast_to((s / P.L)[:, None], (N, R))
        UV = np.stack([uu, vv], axis=-1)
    # the faces' flags: (polished facet, zone) per segment of the ring
    # segments: 0: back-mid -> top0 (back), then top k -> k+1, then edge top -> edge bottom, then bottom, then bottom0 -> back-mid
    def zone_of(a, b):
        """zone for the top segment between kept top indices a and b: 0 face, 1 fuller, 2 back"""
        if (a, b) == (0, 1):
            return 2
        if a in (2, 3, 4) or (a == 3) or (b in (3, 4, 5) and a in (2, 3, 4)):
            return 1
        return 0
    aux = np.zeros((N - 1, R, 2))
    top_seg = []
    for i in range(nk - 1):
        a, b = keep[i], keep[i + 1]
        z = 1 if (a in (2, 3, 4) and b in (3, 4, 5)) else (2 if a == 0 else 0)
        pol = 1.0 if a == 11 or b == 12 and a >= 9 else 0.0
        top_seg.append((z, pol, a))
    # ring segment j goes from point j to point j+1 (wrapping at R)
    segs = []
    segs.append((2, 0.0, 'back'))                     # back-mid -> top0
    for z, pol, a in top_seg:
        segs.append((z, pol, a))
    segs.append((0, 1.0, 'edge'))                     # the edge's thin flat
    for z, pol, a in reversed(top_seg):
        segs.append((z, pol, a))
    segs.append((2, 0.0, 'back'))                     # bottom0 -> back-mid
    assert len(segs) == R, (len(segs), R)
    for j, (z, pol, a) in enumerate(segs):
        aux[:, j, 0] = pol
        aux[:, j, 1] = z / 4.0
    # the sharp false edge of the cove: the back's facet is a polished bevel there
    swm = 0.5 * (sec["sw"][:-1] + sec["sw"][1:])
    for j in (1, R - 1):
        pass
    back_top_j = 1
    back_bot_j = R - 2
    aux_top_back = np.where(swm > 0.5, 1.0, 0.0)
    aux[:, back_top_j, 0] = aux_top_back
    aux[:, back_bot_j, 0] = aux_top_back
    # the quads are between ring points j, j+1; the ring closes on a repeated first column, so that the UVs of the closing quad do not
    # run back across the whole belt (u = 1 there, not 0)
    Pts2 = np.concatenate([Pts, Pts[:, :1]], axis=1)
    UV2 = np.concatenate([UV, UV[:, :1]], axis=1)
    if uvmode != "shader":
        UV2[:, -1, 0] = 1.0
    idx = m.grid(Pts2, UV2, mat=mat, aux=aux)
    if cap is None:
        cap = (lod == "hi")        # the game mesh's root stays open: it is buried in the guard and its collar
    if cap:
        # the root: a fan to the ring's middle (inside the guard)
        ring = idx[0][:-1]
        centre = Pts[0].mean(axis=0)
        m.fan(ring, centre, mat=mat, uv_centre=UV[0].mean(axis=0), flip=True)
    return dict(s=s, sec=sec, keep=keep, Pts=Pts)


# ---------- the surface, for the engraving ----------
def top_profile(s):
    """u, h of the top half at stations s (any shape) for the full 13-point section."""
    sec = section(np.atleast_1d(s).astype(float))
    return sec


def surface(s, u, side=1.0, lift=0.0):
    """Points on the blade's face at stations s and across fractions u (arrays of one shape), on the top (side +1) or bottom (-1),
    following the section's own facets; `lift` along y. Returns (points, normals)."""
    s = np.asarray(s, dtype=np.float64)
    u = np.asarray(u, dtype=np.float64)
    sf, uf = s.ravel(), u.ravel()
    sec = section(sf)
    h = np.zeros_like(uf)
    slope = np.zeros_like(uf)
    for i in range(len(sf)):
        uu, hh = sec["u"][i], sec["h"][i]
        # drop coincident points for interpolation
        h[i] = np.interp(uf[i], uu, hh)
        j = int(np.clip(np.searchsorted(uu, uf[i]) - 1, 0, len(uu) - 2))
        du = uu[j + 1] - uu[j]
        slope[i] = (hh[j + 1] - hh[j]) / du if du > 1e-9 else 0.0
    W = sec["W"]
    x = sec["xs"] - W * uf
    y = side * (h + lift)
    z = P.Z0 - sf
    pts = np.stack([x, y, z], axis=-1).reshape(s.shape + (3,))
    # the normal: across slope dh/dx = -slope/W; also along-length slope ignored (small)
    nx = side * slope / W * (-1.0) * -1.0
    nrm = np.stack([nx * 0 + (slope / W) * side * 1.0, np.full_like(uf, side), np.zeros_like(uf)], axis=-1)
    nrm = nrm / np.linalg.norm(nrm, axis=-1, keepdims=True)
    return pts, nrm.reshape(s.shape + (3,))


def bohi_strokes():
    """The smoke lines engraved in the fuller's floor, in (distance along the blade s, distance across from the fuller's middle):
    they drift from the forte toward the point and end in small curls. None runs down the middle."""
    spec = [
        # x0, y0, length, drift, amp, wavelength, phase, width, curl, curl_dir
        (1.04, 0.030, 2.05, 0.014, 0.030, 1.05, 0.4, (0.052, 0.008), 0.9, 1),
        (1.30, -0.066, 1.45, -0.012, 0.022, 0.78, 1.9, (0.040, 0.007), 0.8, -1),
        (1.50, 0.092, 0.95, 0.010, 0.014, 0.58, 3.4, (0.030, 0.006), 0.8, 1),
        (1.78, -0.100, 0.78, -0.008, 0.010, 0.50, 0.7, (0.024, 0.005), 0.7, -1),
    ]
    out = []
    for x0, y0, ln, dr, am, wl, ph, wd, cu, cd in spec:
        out.append(KT.tendril(x0, y0, ln, dr, am, wl, phase=ph, width=wd, curl=cu, curl_dir=cd, n=120))
    return out


ENGRAVE = 0.013


def bohi_patch(m, side=1.0, mat=0, nr=300, nc=56):
    """The fuller's engraved floor, one side: a dense patch lying at the floor's height, carved with the smoke lines."""
    s = np.linspace(PATCH[0], PATCH[1], nr)
    sec = section(s, sink=False)
    u, h, W, xs, T = sec["u"], sec["h"], sec["W"], sec["xs"], sec["T"]
    c = (u[:, 2] + u[:, 5]) / 2
    gh = (u[:, 5] - u[:, 2]) / 2
    b = np.linspace(-1.0, 1.0, nc)
    uu = c[:, None] + gh[:, None] * b[None, :]
    S = np.broadcast_to(s[:, None], (nr, nc))
    Bc = (uu - c[:, None]) * W[:, None]
    strokes = []
    for pts, ws in bohi_strokes():
        q = pts.copy()
        q[:, 1] *= side
        strokes.append((q, ws))
    field = KT.strokes_field(S, Bc, strokes) * smooth(0.04, 0.22, s - PATCH[0] + 0.04)[:, None] * (1.0 - smooth(PATCH[1] - 0.22, PATCH[1] - 0.04, s))[:, None]
    # the floor's height: the groove's floor points are the 4th/5th section points (T - d)
    floor_h = h[:, 3]
    x = xs[:, None] - W[:, None] * uu
    y = side * (floor_h[:, None] - ENGRAVE * field)
    z = np.broadcast_to((P.Z0 - s)[:, None], (nr, nc))
    pts = np.stack([x, y, z], axis=-1)
    UV = np.stack([(uu), np.broadcast_to((s / P.L)[:, None], (nr, nc))], axis=-1)
    aux = np.tile(np.array([0.0, 0.25]), (nr - 1, nc - 1, 1))
    va = np.stack([field, np.full_like(field, 0.25)], axis=-1)
    m.grid(pts, UV, mat=mat, aux=aux, flip=(side < 0), vaux=va)
