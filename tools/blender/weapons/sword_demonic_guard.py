"""The Demonic sword's guard and its blade collar (run inside Blender, headless).

The guard is one heavy slab of dark iron that sweeps forward from its middle in a single bold curve, so the two arms cradle the
blade's root and the collar standing out of it. Seen from the flat it is a crescent: its middle is deep (0.48 along the weapon) and
thick (0.30), its arms narrow and thin toward blunt, square-cut, chamfered ends (a rounded dome with a band round it reads as anatomy). Each face carries a plate of blackened bronze, inset from the
iron rim, engraved with long smoke lines that stream outward from the root and end in small curls.

    core(m, lod, mat)       the iron slab
    plates(m, lod, mat)     the two engraved bronze face plates
    habaki(m, lod, mat)     the collar round the blade's root, in front of the slab

Studs in the weapon's frame; the slab's front face at the middle is the blade's Hilt (z = -1.20).
"""
import math

import numpy as np

import sword_demonic_kit as KT
import sword_demonic_profile as P

smooth = KT.smoothstep
ZC = -0.98          # the middle of the slab along the weapon
A = 1.30            # the arms' reach on each side
SWEEP = 0.78        # how far the ends stand forward of the middle
PW = 2.2            # the sweep's curve (a power of the distance out)
HW0, HWT = 0.26, 0.14      # half the slab's width (along the weapon) at its middle and its ends
TG0, TGT = 0.170, 0.100    # half its thickness
RP = 3.4            # the section's squareness (a superellipse exponent: 2 is round, large is a box)
R_END = 0.05        # the arm ends are cut square and chamfered over this much (a rounded dome with a band round it reads as something else)
PLATE_H = 0.022     # the plate's height over the iron
PLATE_INSET = 0.78  # the plate's share of the slab's width
PLATE_A = A - 0.12  # the plate's reach
ENGRAVE = 0.019     # the engraving's depth


def arm(a):
    """Path and sizes at positions a (N,) along the slab: x, z of the centre line, the in-plane normal (towards the grip), half
    width and half thickness, with the arm's rounded end."""
    a = np.asarray(a, dtype=np.float64)
    ax = np.abs(a) / A
    z = ZC - SWEEP * ax ** PW
    dzdx = -SWEEP * PW * ax ** (PW - 1) * np.sign(a) / A
    nrm = np.stack([-dzdx, np.ones_like(a)], axis=-1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    t_end = np.clip((np.abs(a) - (A - R_END)) / R_END, 0.0, 1.0)
    end = 1.0 - 0.20 * t_end * t_end * (3 - 2 * t_end)
    hw = (HW0 + (HWT - HW0) * ax ** 2.2) * end
    tg = (TG0 + (TGT - TG0) * ax ** 1.8) * end
    return a, z, nrm, hw, tg


def arc_length(a):
    """Distance along the centre line from the middle, signed like a."""
    a = np.asarray(a, dtype=np.float64)
    fine = np.linspace(0.0, A, 2001)
    ax = fine / A
    dz = SWEEP * PW * ax ** (PW - 1) / A
    seg = np.sqrt(1 + dz ** 2) * (fine[1] - fine[0])
    cum = np.concatenate([[0.0], np.cumsum(seg[:-1])])
    return np.sign(a) * np.interp(np.abs(a), fine, cum)


RIDGE = 0.040       # the keel down the middle of each face, at the slab's middle (it narrows with the arm)
RIDGE_W = 0.60      # its half width, as a share of the slab's


def super_y(c, t):
    """The slab's section height at c (-1..1 across) for half thickness t: a rounded box with a keel down its middle."""
    c = np.asarray(c, dtype=np.float64)
    base = t * np.clip(1.0 - np.abs(c) ** RP, 0.0, 1.0) ** (1.0 / RP)
    keel = RIDGE * (np.asarray(t) / TG0) * np.clip(1.0 - (np.abs(c) / RIDGE_W) ** 2, 0.0, 1.0) ** 1.4
    return base + keel


def core(m, lod="hi", mat=0, belt=False):
    """The iron slab. belt=True (the game mesh): the ring of each station laid out as a straight strip, the two flat ends as rows that
    collapse to their middle, so the slab is one rectangular UV island (a slab's two faces unwrapped by projection make a big almond with
    a bar in it, and its ends round knobs: a shape that is read as something else)."""
    na = 360 if lod == "hi" else 34
    nc = 33 if lod == "hi" else 9
    a = np.linspace(-A, A, na)
    a, z, nrm, hw, tg = arm(a)
    c = np.sin(np.linspace(-1.0, 1.0, nc) * math.pi / 2)
    N = len(a)
    xz = np.stack([a, z], axis=-1)
    top, bot = [], []
    for k in range(nc):
        pos = xz + nrm * (hw * c[k])[:, None]
        top.append(np.stack([pos[:, 0], super_y(c[k], tg), pos[:, 1]], axis=-1))
        bot.append(np.stack([pos[:, 0], -super_y(c[k], tg), pos[:, 1]], axis=-1))
    top = np.stack(top, axis=1)               # (N, nc, 3) from c = -1 to +1
    bot = np.stack(bot, axis=1)[:, 1:-1][:, ::-1]   # c = +1 .. -1 without the rim points
    ring = np.concatenate([top, bot], axis=1)
    R = ring.shape[1]
    sg = arc_length(a)
    if belt:
        ring2 = np.concatenate([ring, ring[:, :1]], axis=1)
        rows = np.concatenate([ring[0].mean(axis=0)[None, None, :].repeat(R + 1, axis=1), ring2, ring[-1].mean(axis=0)[None, None, :].repeat(R + 1, axis=1)], axis=0)
        e = 0.03
        v = np.concatenate([[0.0], e + (1 - 2 * e) * (sg - sg.min()) / (sg.max() - sg.min()), [1.0]])
        u = np.broadcast_to(np.linspace(0, 1, R + 1)[None, :], (N + 2, R + 1))
        m.grid(rows, np.stack([u, np.broadcast_to(v[:, None], (N + 2, R + 1))], axis=-1), mat=mat)
        return
    UV = np.stack(np.broadcast_arrays((np.arange(R) / R)[None, :], (sg / (2 * arc_length(np.array([A]))[0]) + 0.5)[:, None]), axis=-1)
    idx = m.grid(ring, UV, mat=mat, wrap=True)
    m.fan(idx[0], ring[0].mean(axis=0), mat=mat, flip=True)
    m.fan(idx[-1], ring[-1].mean(axis=0), mat=mat)


def plate_strokes(seed=3):
    """Engraving strokes in (distance along the arm from the middle, distance across it), for the +side arm; the -side arm is its
    mirror. Smoke lines that stream out from the root and end in small curls, and a hairline border."""
    strokes = []
    spec = [
        # x0, y0, length, drift, amp, wavelength, phase, width, curl, curl_dir
        (0.34, 0.135, 1.22, -0.060, 0.018, 0.95, 0.0, (0.040, 0.006), 0.8, 1),
        (0.30, 0.045, 1.40, -0.020, 0.020, 1.05, 1.3, (0.050, 0.006), 0.9, -1),
        (0.38, -0.050, 1.12, 0.022, 0.018, 0.90, 2.6, (0.040, 0.006), 0.8, 1),
        (0.52, -0.135, 0.88, 0.060, 0.014, 0.80, 0.9, (0.030, 0.005), 0.7, -1),
    ]
    for x0, y0, ln, dr, am, wl, ph, wd, cu, cd in spec:
        strokes.append(KT.tendril(x0 * 1.1, y0, ln * 1.32, dr, am, wl * 1.2, phase=ph, width=wd, curl=cu, curl_dir=cd, n=80))
    return strokes


def border_stroke(a_max, inset, wid=0.0075):
    """A hairline groove round the plate's edge on the +side arm's half (and across the middle), inside the rim by `inset`."""
    pts, ws = [], []
    aa = np.linspace(0.0, a_max - 0.02, 60)
    sg = arc_length(aa)
    _, z, nrm, hw, _ = arm(aa)
    for s, h in zip(sg, hw):
        pts.append((s, h * PLATE_INSET - inset))
        ws.append(wid)
    return np.array(pts), np.array(ws)


def plates(m, lod="hi", mat=1):
    """The two bronze face plates, engraved (hi) or plain (low: the engraving is baked in)."""
    na = 420 if lod == "hi" else 30
    nc = 76 if lod == "hi" else 9
    a = np.linspace(-PLATE_A, PLATE_A, na)
    a_, z, nrm, hw, tg = arm(a)
    # the plate's own end: its half width closes over the last stretch
    r_p = 0.05
    te = np.clip((np.abs(a) - (PLATE_A - r_p)) / r_p, 0.0, 1.0)
    endp = 1.0 - 0.22 * te * te * (3 - 2 * te)
    hwp = hw / np.maximum(1.0 - 0.0, 1e-9) * PLATE_INSET
    hwp = (HW0 + (HWT - HW0) * (np.abs(a) / A) ** 2.2) * PLATE_INSET * endp
    c = np.sin(np.linspace(-1.0, 1.0, nc) * math.pi / 2)
    sg = arc_length(a)
    xz = np.stack([a, z], axis=-1)
    stk = None
    for side in (1, -1):
        rows = []
        field = None
        S = np.broadcast_to(sg[:, None], (na, nc))
        Bc = (hwp[:, None] * c[None, :])
        d_edge = np.minimum((1.0 - np.abs(c)[None, :]) * hwp[:, None], (PLATE_A - np.abs(a))[:, None])
        if lod == "hi":
            strokes = []
            for sgn in (1, -1):
                for pts, ws in plate_strokes():
                    q = pts.copy()
                    q[:, 0] *= sgn
                    q[:, 1] *= sgn * side          # the mirrored arm and the underside run mirrored
                    strokes.append((q, ws))
                bp, bw = border_stroke(PLATE_A, 0.026)
                q = bp.copy()
                q[:, 0] *= sgn
                strokes.append((q, bw))
                q2 = bp.copy()
                q2[:, 0] *= sgn
                q2[:, 1] *= -1
                strokes.append((q2, bw))
            field = KT.strokes_field(S, Bc, strokes) * smooth(0.018, 0.045, d_edge)
        # the surface
        pts = np.zeros((na, nc, 3))
        cl = np.clip(c[None, :] * PLATE_INSET, -0.999, 0.999)
        ycore = super_y(cl, tg[:, None])
        yp = ycore + PLATE_H * smooth(0.0, 0.03, d_edge)
        if field is not None:
            yp = yp - ENGRAVE * field
        pos = xz[:, None, :] + nrm[:, None, :] * (hwp[:, None] * c[None, :])[..., None]
        pts[..., 0] = pos[..., 0]
        pts[..., 2] = pos[..., 1]
        pts[..., 1] = side * yp
        UV = np.stack([np.broadcast_to(np.linspace(0, 1, nc)[None, :], (na, nc)), np.broadcast_to(np.linspace(0, 1, na)[:, None], (na, nc))], axis=-1)
        va = np.stack([field if field is not None else np.zeros((na, nc)), np.zeros((na, nc))], axis=-1)
        m.grid(pts, UV, mat=mat, flip=(side < 0), vaux=va)


def habaki(m, lod="hi", mat=1, belt=False):
    """The collar: a rounded box round the blade's root, from the slab's front face forward, stepped: a heavy shoulder against the slab,
    a raised band, a long drawn-in neck, a second narrower band, and a chamfered, rounded far end."""
    nz = 90 if lod == "hi" else 16
    nc = 32 if lod == "hi" else 12
    z0, z1 = P.Z0 + 0.04, P.Z0 - 0.50
    t = np.linspace(0.0, 1.0, nz)
    z = z0 + (z1 - z0) * t
    taper = smooth(0.0, 1.0, t)
    hx = 0.405 - 0.045 * taper
    hy = 0.150 - 0.022 * taper
    band = (smooth(0.00, 0.03, t) - smooth(0.17, 0.20, t)) * 0.022          # the shoulder against the slab
    band += (smooth(0.36, 0.39, t) - smooth(0.46, 0.49, t)) * 0.016          # a raised band
    band += (smooth(0.64, 0.67, t) - smooth(0.72, 0.75, t)) * 0.012          # a narrower one
    hx, hy = hx + band, hy + band * 0.8
    close = np.sqrt(np.clip(1.0 - ((t - 0.93) / 0.07) ** 2, 0.0, 1.0)) * (t > 0.93) + 1.0 * (t <= 0.93)
    hx, hy = hx * (0.35 + 0.65 * close), hy * (0.25 + 0.75 * close)
    ang = np.linspace(0.0, math.tau, nc, endpoint=False)
    p = 4.5
    cx = np.sign(np.cos(ang)) * np.abs(np.cos(ang)) ** (2.0 / p)
    cy = np.sign(np.sin(ang)) * np.abs(np.sin(ang)) ** (2.0 / p)
    ring = np.zeros((nz, nc, 3))
    ring[..., 0] = hx[:, None] * cx[None, :]
    ring[..., 1] = hy[:, None] * cy[None, :]
    ring[..., 2] = z[:, None]
    if belt:
        ring2 = np.concatenate([ring, ring[:, :1]], axis=1)
        tip = np.array([0.0, 0.0, z1 - 0.012])
        rows = np.concatenate([ring2, tip[None, None, :].repeat(nc + 1, axis=1)], axis=0)
        u = np.broadcast_to(np.linspace(0, 1, nc + 1)[None, :], (nz + 1, nc + 1))
        v = np.concatenate([t * 0.94, [1.0]])
        m.grid(rows, np.stack([u, np.broadcast_to(v[:, None], (nz + 1, nc + 1))], axis=-1), mat=mat)
        return
    idx = m.grid(ring, None, mat=mat, wrap=True)
    m.fan(idx[-1], np.array([0.0, 0.0, z1 - 0.004]), mat=mat)
