"""The Lantern Wyrm's space curves (no Blender needed: mathutils only): a smooth path through control points with an arc-length table,
read back by distance. The wyrm's pose is authored as curves (where its spine lies) and solved into bone turns (lantern_wyrm_motion.py);
its walk reads the path its root took (the same class, built from the recorded positions), so the body follows the head.
"""
import math

from mathutils import Vector

V = Vector


class Curve:
    """A Catmull-Rom path through `pts` (studs), sampled densely, with the distance along it at every sample."""

    def __init__(self, pts, per=24, closed=False):
        pts = [V(p) for p in pts]
        self.control = pts
        ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
        dense = []
        for i in range(1, len(ext) - 2):
            p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
            for s in range(per):
                t = s / per
                t2, t3 = t * t, t * t * t
                dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
        dense.append(pts[-1])
        self.p = dense
        self.s = [0.0]
        for a, b in zip(dense, dense[1:]):
            self.s.append(self.s[-1] + (b - a).length)
        self.length = self.s[-1]

    def at(self, s):
        """The point `s` studs along the path (beyond the ends it carries straight on)."""
        if s <= 0:
            return self.p[0] + (self.p[0] - self.p[min(3, len(self.p) - 1)]).normalized() * (-s)
        if s >= self.length:
            return self.p[-1] + (self.p[-1] - self.p[-4]).normalized() * (s - self.length)
        lo, hi = 0, len(self.s) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self.s[mid] <= s:
                lo = mid
            else:
                hi = mid
        u = (s - self.s[lo]) / max(self.s[hi] - self.s[lo], 1e-9)
        return self.p[lo].lerp(self.p[hi], u)

    def tangent(self, s, h=0.4):
        return (self.at(s + h) - self.at(s - h)).normalized()


def march(curve, lengths, start=0.0):
    """Joint positions of a chain of bones of the given lengths laid along the curve: each joint is the next point of the curve exactly
    `length` (a straight chord) from the one before. Returns len(lengths) + 1 points, the first at `start` studs along the curve."""
    out = [curve.at(start)]
    s = start
    for ell in lengths:
        a = out[-1]
        lo, hi = s, s + ell * 1.6 + 0.5
        for _ in range(40):                       # the chord of length `ell`: bisection on the arc length
            mid = (lo + hi) / 2
            if (curve.at(mid) - a).length < ell:
                lo = mid
            else:
                hi = mid
        s = (lo + hi) / 2
        out.append(curve.at(s))
    return out


def frames(points, up=(0, 1, 0), start_up=None):
    """A parallel-transported (dir, up) for each segment of a polyline: no flips however it climbs and turns. `up` seeds the first."""
    out = []
    u = V(start_up if start_up is not None else up)
    prev = None
    for a, b in zip(points, points[1:]):
        d = (b - a).normalized()
        if prev is None:
            u = (u - d * u.dot(d))
            if u.length < 1e-4:
                u = V((1, 0, 0)) - d * d.x
        else:
            axis = prev.cross(d)
            if axis.length > 1e-6:
                ang = math.acos(max(-1.0, min(1.0, prev.dot(d))))
                from mathutils import Matrix
                u = Matrix.Rotation(ang, 3, axis.normalized()) @ u
            u = u - d * u.dot(d)
        u = u.normalized()
        out.append((d, u))
        prev = d
    return out
