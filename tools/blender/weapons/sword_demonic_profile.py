"""The Demonic sword's blade as numbers (pure Python and numpy: no Blender needed), shared by the design study and the model so what
was judged in silhouette is what is built.

Studs, authored as the game weapon is: the grip centre at the origin, the point toward -Z, the spine toward +X. `s` is the distance
along the blade from where it starts (the guard's front, z = Z0) to the point.
"""
import math

import numpy as np

TAU = math.tau
Z0 = -1.24          # where the blade starts (the guard's front): the weapon's Hilt


def catmull(pts, per=14):
    """A smooth curve through control points [(a, b)] (Catmull-Rom, ends repeated)."""
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = (np.array(p[j], dtype=float) for j in (i - 1, i, i + 1, i + 2))
        for k in range(per):
            t = k / per
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.array(p[-2], dtype=float))
    return np.array(out)


def talon(L=5.05, spine_x=0.22, forte_edge=0.40, belly_edge=0.70, belly_s=3.6, cove_s=4.1, tip_dx=-0.30, sori=0.30, bulge=0.0,
          q=2.0, q2=2.0, flick=0.06, guard="crescent", pommel="ring", edge_mid=None, waist=None, waist_s=1.8):
    """The chosen idea as numbers: a straight spine, an edge that swells into a forward belly, then the spine scooped (a cove of
    power q) into a hooked point. tip_dx: where the point stands relative to the spine line, sori: the whole blade's bow toward +X."""
    def bow(sv):
        return sori * (sv / L) ** 1.7
    n = 18
    spine, edge = [], []
    for i in range(n + 1):
        sv = cove_s * i / n
        spine.append((sv, spine_x + bow(sv) + bulge * math.sin(math.pi * sv / cove_s)))
    xc = spine[-1][1]
    xt = spine_x + tip_dx + bow(L)
    m = 10
    for i in range(1, m + 1):
        t = i / m
        sv = cove_s + (L - cove_s) * t
        ease = min(1.0, t / 0.26)
        ease = ease * ease * (3 - 2 * ease)
        spine.append((sv, xc + (xt - xc) * (1 - (1 - t) ** q) * ease ** 0.7 + flick * t ** 6))
    # the edge: a long swell to the belly, then an arc in to the point
    k = 14
    for i in range(k + 1):
        sv = belly_s * i / k
        u = i / k
        w = forte_edge + (belly_edge - forte_edge) * (u ** 1.15 if edge_mid is None else u ** edge_mid)
        if waist is not None:       # the edge first draws in to a waist, then swells to the belly (a kopis head)
            if sv <= waist_s:
                w = forte_edge + (waist - forte_edge) * math.sin(math.pi / 2 * sv / waist_s)
            else:
                u2 = (sv - waist_s) / (belly_s - waist_s)
                w = waist + (belly_edge - waist) * (math.sin(math.pi / 2 * u2) ** 1.3)
        edge.append((sv, spine_x - w + bow(sv)))
    xb = edge[-1][1]
    for i in range(1, m + 1):
        t = i / m
        sv = belly_s + (L - belly_s) * t
        edge.append((sv, xb + (xt - xb) * (t ** q2) + flick * t ** 6))
    return dict(spine=[(0, spine_x)] + spine[1:], edge=edge, guard=guard, pommel=pommel)




# ---------- the chosen blade (the study's round 3, tuned) ----------
L = 5.00            # blade length: Hilt z = -1.24, point z = -6.24 (Sword6's point is at -4.65: 1.34 times)
FINAL = dict(L=L, spine_x=0.35, forte_edge=0.70, waist=0.58, waist_s=1.9, belly_edge=1.0, belly_s=3.9, cove_s=3.95, q=3.0,
             tip_dx=-0.70, sori=0.34, flick=0.50)
S_YOKOTE = 4.4      # where the point's facets start (the yokote line)
S_BOHI = (0.62, 3.66)   # the fuller's ends


def blade_table():
    """Dense spine and edge x(s) arrays (Catmull-Rom through talon()'s controls, resampled on a fine even grid)."""
    spec = talon(**FINAL)
    sp = catmull(spec["spine"], 16)
    ed = catmull(spec["edge"], 16)
    s = np.linspace(0.0, L, 2001)
    xs = np.interp(s, sp[:, 0], sp[:, 1])
    xe = np.interp(s, ed[:, 0], ed[:, 1])
    return s, xs, xe


_T = None


def table():
    global _T
    if _T is None:
        _T = blade_table()
    return _T


def x_spine(s):
    t = table()
    return np.interp(s, t[0], t[1])


def x_edge(s):
    t = table()
    return np.interp(s, t[0], t[2])


def width(s):
    return x_spine(s) - x_edge(s)


def thickness(s):
    """Half the blade's thickness at its ridge (the shinogi), in studs: heavy at the forte, drawn down toward the point, and
    falling faster past the yokote so the point's facets show as their own plane."""
    s = np.asarray(s, dtype=float)
    return np.interp(s, [0.0, 1.8, 3.9, S_YOKOTE, L - 0.04, L], [0.112, 0.104, 0.082, 0.056, 0.012, 0.0])


def tip_xz():
    """The point in the weapon's frame (x, z)."""
    return float(x_spine(L)), Z0 - L
