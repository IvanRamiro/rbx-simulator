"""The Unorthodox sword's blade (run inside Blender): its plan, its cross-section and both meshes made from them.

The blade is one surface described by numbers, so the high-detail mesh and the game mesh agree to a few thousandths of a stud:

- PLAN (in the X-Z plane, studs): a centre-line from the guard that bows out to +X, comes back through a recurve and ends in a
  clipped point turned toward -X; the edge is the -X side, wide in a forward belly (the weight sits far ahead of the hand, as in
  the kora and the kilij's yelman), the back is the +X side, narrow and thick.
- SECTION: a Japanese shinogi-zukuri section: a polished edge bevel, a gently convex hira, a ridge (shinogi), a shinogi-ji band
  with a long fuller cut into it, a flat rounded back (mune). Thickness tapers toward the point (distal taper).
- ENGRAVING as geometry: three drift lines cut into the hira of the belly, each a shallow groove that follows the blade's own
  curve and tapers to nothing at both ends (their floors are a separate material: copper inlay).

Per face material indexes: 0 the hira (dark patinated steel with the temper line), 1 the polished edge bevel, 2 the shinogi-ji and
back, 3 the fuller floor, 4 the inlay in the drift lines. UVs of the high-detail blade are for its shaders: u = distance from the
edge along the surface (studs), v = distance along the blade (studs), +50 on the underside so the two faces differ.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

V = Vector

FOOT_Z = -0.70          # the blade's foot (inside the guard)
ARC = 5.05              # length along the curve, foot to point
HEADING = [(0, 5), (0.28, 13), (0.50, 8), (0.72, -6), (0.88, -22), (1, -38)]       # degrees from -Z toward +X, by u
WE = [(0, .13), (.20, .16), (.45, .25), (.72, .44), (.86, .40), (.94, .27), (.985, .10), (1, .007)]   # edge-side half width
WS = [(0, .11), (.50, .10), (.76, .09), (.90, .055), (1, .005)]                          # back-side half width
THICK = [(0, 0.088), (.5, 0.070), (.8, 0.052), (1, 0.026)]                              # half thickness at the ridge
SHINOGI = 0.62          # the ridge sits this fraction of the width back from the edge
BEVEL = 0.058           # edge bevel width (studs)
FULLER = (0.05, 0.60)   # the fuller's run (u)
LINES = [(0.30, 0.46, 0.94), (0.55, 0.40, 0.90), (0.80, 0.34, 0.86)]   # drift lines: fraction hamon->ridge, u start, u end


def _smooth(vals, k):
    if k < 2:
        return vals
    pad = np.concatenate([np.full(k, vals[0]), vals, np.full(k, vals[-1])])
    return np.convolve(pad, np.ones(k) / k, mode="same")[k:-k]


class Blade:
    """The plan sampled finely; stations are picked from it by arc length."""

    def __init__(self, n=2400):
        self.n = n
        us = np.linspace(0, 1, n)
        self.u = us

        def table(pts, k):
            xs, ys = zip(*pts)
            return _smooth(np.interp(us, xs, ys), k)
        self.heading = np.radians(table(HEADING, n // 40))
        self.we = np.maximum(table(WE, n // 120), 0.0)
        self.ws = np.maximum(table(WS, n // 120), 0.0)
        self.h = table(THICK, n // 60)
        ds = ARC / (n - 1)
        self.x = np.concatenate([[0], np.cumsum(np.sin(self.heading[:-1]) * ds)])
        self.z = FOOT_Z + np.concatenate([[0], np.cumsum(-np.cos(self.heading[:-1]) * ds)])
        self.s = us * ARC
        self.tx, self.tz = np.sin(self.heading), -np.cos(self.heading)
        self.nx, self.nz = self.tz, -self.tx          # toward the edge (-X for a blade heading -Z)

    def at(self, arr, u):
        return float(np.interp(u, self.u, arr))

    def width(self, u):
        return self.at(self.we, u) + self.at(self.ws, u)

    def tip(self):
        return (float(self.x[-1]), float(self.z[-1]))

    def point(self, u, a, y):
        """The point at station u, `a` across from the centre-line toward the edge, y up (Roblox space)."""
        return V((self.at(self.x, u) + self.at(self.nx, u) * a, y, self.at(self.z, u) + self.at(self.nz, u) * a))

    def stations(self, count, curve_bias=2.5):
        """u values, denser where the plan turns."""
        k = np.abs(np.gradient(self.heading))
        k = k / max(k.max(), 1e-9)
        w = 1.0 + curve_bias * _smooth(k, 40)
        cum = np.concatenate([[0], np.cumsum(0.5 * (w[1:] + w[:-1]))])
        cum /= cum[-1]
        return [float(np.interp(i / (count - 1), cum, self.u)) for i in range(count)]


# ---------- the section ----------
def ridge_frac(u):
    return SHINOGI


def section_top(b, u, fine=True):
    """The top half of the section at station u as [(a, y, x, kind)], from the edge over the ridge to the back. x is the shader's
    across coordinate: 0 where the edge bevel ends, 1 at the ridge (negative on the bevel, above 1 on the shinogi-ji and the back).
    kind: 0 hira, 1 edge bevel, 2 shinogi-ji / back, 3 fuller floor, 4 drift-line floor."""
    we, ws, h = b.at(b.we, u), b.at(b.ws, u), b.at(b.h, u)
    w = we + ws
    bw = min(BEVEL, 0.45 * w)
    d_s = SHINOGI * w                    # ridge distance from the edge
    d_b = bw
    yb = 0.36 * h
    pts = []

    def add(d, y, kind):
        pts.append((we - d, y, (d - d_b) / (d_s - d_b), kind))
    add(0.0, 0.0015, 1)
    add(d_b * 0.55, yb * 0.55, 1)
    add(d_b, yb, 1)
    n_h = 96 if fine else 1       # the same count at every station: the quads join point to point
    lines = []
    for f, u0, u1 in LINES:
        if u0 < u < u1 and fine:
            t = (u - u0) / (u1 - u0)
            wid = 0.0125 * math.sin(math.pi * t) ** 0.6
            d_h = d_b + 0.07 + 0.45 * (d_s - d_b - 0.07)       # the lines run in the upper part of the hira
            centre = d_b + 0.03 + f * (d_s - d_b - 0.06) + 0.012 * math.sin(7.0 * u + f * 9)
            lines.append((centre, wid, 0.0095 * math.sin(math.pi * t) ** 0.5))
    for i in range(1, n_h + 1):
        s = i / n_h
        d = d_b + (d_s - d_b) * s
        y = yb + (h - yb) * (s ** 0.6) - 0.0
        kind = 0
        for centre, wid, dep in lines:
            q = abs(d - centre)
            if q < wid:
                y -= dep * (0.5 + 0.5 * math.cos(math.pi * q / wid))
                if q < wid * 0.55:
                    kind = 4
        add(d, y, kind)
    # the ridge, slightly rounded
    add(d_s + 0.004, h * 0.995, 2)
    # the shinogi-ji with the fuller
    d_back = w - 0.03
    n_j = 30 if fine else 1
    f0, f1 = FULLER
    run = 0.0
    if f0 < u < f1 and fine:
        t = (u - f0) / (f1 - f0)
        run = math.sin(math.pi * min(1.0, t * 1.0)) ** 0.5 if 0 < t < 1 else 0.0
        run = min(1.0, run * 1.6)
    for i in range(1, n_j + 1):
        s = i / n_j
        d = d_s + 0.004 + (d_back - d_s - 0.004) * s
        y = h * (0.995 - 0.075 * s)
        kind = 2
        if fine and run > 0:
            c = 0.5
            half = 0.30
            q = abs(s - c)
            if q < half:
                depth = 0.016 * run * (0.5 + 0.5 * math.cos(math.pi * q / half))
                y -= depth
                if q < half * 0.7:
                    kind = 3
        add(d, y, kind)
    # the rounded back
    add(w - 0.012, h * 0.62, 2)
    add(w - 0.001, h * 0.30, 2)
    return pts, w


def section_loop(b, u, fine=True):
    """The whole section as [(a, y, dist, kind, top)] round the blade, starting at the edge (top side), over the back, and
    returning along the underside; no point is repeated."""
    top, w = section_top(b, u, fine)
    we = b.at(b.we, u)
    back_mid = (we - w - 0.004, 0.0, (w + 0.002 - min(BEVEL, 0.45 * w)) / (SHINOGI * w - min(BEVEL, 0.45 * w)), 2)
    loop = [(a, y, d, k, True) for a, y, d, k in top]
    loop.append((*back_mid, True))
    loop += [(a, -y, d, k, False) for a, y, d, k in top[::-1]]
    return loop, w


# ---------- meshes ----------
def build_hi(hi, b, count=300):
    """The high-detail blade into `hi` (an egg_hi.Hi). Returns the station rows (for inlay placement)."""
    us = b.stations(count)
    rows = []
    for u in us:
        loop, w = section_loop(b, u, True)
        ids, uvx, tops = [], [], []
        for a, y, d, k, top in loop:
            ids.append(hi.v(b.point(u, a, y)))
            uvx.append(d)
            tops.append(top)
        rows.append((u, ids, [l[3] for l in loop], uvx, tops, [l[:2] for l in loop]))
    return _quads(hi, b, rows, us)


def build_low(hi, b, count=72):
    """The game mesh's blade: seven points a section, flat shading across the facets (sharp edges are set by the caller). Its UVs are the
    blade seen from above (top faces) and from below (bottom faces, set aside), so each face of the blade is a blade-shaped island that keeps
    the blade's own curve (an unwrap that joined the two faces at the edge made a lens with a line down it); the back is a strip."""
    us = b.stations(count, 3.0)
    rows = []
    for u in us:
        we, ws, h = b.at(b.we, u), b.at(b.ws, u), b.at(b.h, u)
        w = we + ws
        bw = min(BEVEL, 0.45 * w)
        d_s = SHINOGI * w
        top = [(we, 0.0015, 0.0, 1), (we - bw, 0.36 * h, bw, 1), (we - d_s, h, d_s, 0), (-ws + 0.012, h * 0.915, w - 0.012, 2)]
        loop = [(a, y, d, k, True) for a, y, d, k in top]
        loop += [(-ws, h * 0.45, w, 2, True)]
        loop += [(-ws, -h * 0.45, w, 2, False)]
        loop += [(a, -y, d, k, False) for a, y, d, k in top[::-1][:-1]]
        ids = [hi.v(b.point(u, a, y)) for a, y, d, k, t in loop]
        rows.append((u, ids, [l[3] for l in loop], [l[2] for l in loop], [l[4] for l in loop], [l[:2] for l in loop]))
    return _quads(hi, b, rows, us, plan_uv=True)


def _quads(hi, b, rows, us, plan_uv=False):
    m = len(rows[0][1])
    flip = None
    for i in range(len(rows) - 1):
        u0, ids0, k0, ux0, t0, _ = rows[i]
        u1, ids1, k1, ux1, t1, _ = rows[i + 1]
        v0, v1 = b.at(b.s, u0), b.at(b.s, u1)
        for k in range(m):
            j = (k + 1) % m
            under = (not t0[k]) or (not t0[j])
            off = 50.0 if under else 0.0
            quad = [ids0[k], ids0[j], ids1[j], ids1[k]]
            uv = [(ux0[k], v0 + off), (ux0[j], v0 + off), (ux1[j], v1 + off), (ux1[k], v1 + off)]
            if plan_uv:
                sc = 0.11
                cs = [V(hi.verts[q]) for q in quad]                      # Blender axes: (x, -z, y)
                if t0[k] and t0[j]:                                     # the top: seen from above
                    uv = [(c.x * sc, c.y * sc) for c in cs]
                elif (not t0[k]) and (not t0[j]):                       # the underside: seen from below, set aside
                    uv = [(c.x * sc + 0.45, c.y * sc) for c in cs]
                else:                                                   # the back: a strip beside them
                    uv = [(0.82 + c.z * 0.9, c.y * sc) for c in cs]
            kind = 2 if (t0[k] != t0[j]) else k0[k]
            if flip is None and kind == 0 and t0[k] and t0[j]:
                a, bb, c = (V(hi.verts[q]) for q in quad[:3])
                flip = (bb - a).cross(c - a).z < 0        # Blender +Z is Roblox +Y: the hira faces up
            if flip:
                quad, uv = quad[::-1], uv[::-1]
            hi.f(quad, uv, kind)
    # the foot and the point are closed with fans, wound against the edges of the quads next to them (so the winding is consistent)
    for row, last in ((rows[0], False), (rows[-1], True)):
        u, ids, _, _, _, pts = row
        cx = hi.v(b.point(u, float(np.mean([p[0] for p in pts])), 0.0))
        for k in range(m):
            j = (k + 1) % m
            tri = [ids[k], ids[j], cx] if last else [ids[j], ids[k], cx]
            if flip:
                tri = tri[::-1]
            hi.f(tri, [(0, 0), (1, 0), (0.5, 1)], 2)
    return rows
