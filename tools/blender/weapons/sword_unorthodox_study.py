"""The Unorthodox sword's design study (run inside Blender, headless): the research board and the silhouette sheet.

    blender -b --factory-startup --python tools/blender/weapons/sword_unorthodox_study.py -- board|silhouettes|all

Everything is drawn flat in plan (looking down on the flat the player sees: the point toward the top, +X to the right, studs),
from outlines described by numbers, so a form can be judged and compared before any 3D is built. The reference forms on the
board are the author's own line drawings of real blade types (proportions approximate, drawn to show the principle), never
a copy of any museum piece or any game's weapon.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import sword_unorthodox_draw as D  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "renders", "faction_weapons_v2", "Unorthodox")

BG = (0.07, 0.075, 0.09)
INK = (0.92, 0.93, 0.95)
DIM = (0.55, 0.58, 0.64)
TEAL = (0.35, 0.72, 0.68)
COPPER = (0.9, 0.55, 0.32)


# ---------- outlines ----------
def curve(pts, n=160, smooth=9):
    """Piecewise-linear [(u, value)] resampled to n points on u 0..1 and smoothed."""
    us = np.linspace(0, 1, n)
    xs, ys = zip(*pts)
    v = np.interp(us, xs, ys)
    k = np.ones(smooth) / smooth
    pad = np.concatenate([np.full(smooth, v[0]), v, np.full(smooth, v[-1])])
    return np.convolve(pad, k, mode="same")[smooth:-smooth]


def blade(L, heading_deg, we, ws, z0=-1.0, x0=0.0, n=160, tip_round=0.0):
    """A blade outline in plan: centreline from (x0, z0) heading `heading_deg`(u) from -Z toward +X, the edge side toward -X
    (`we`(u) wide) and the spine side toward +X (`ws`(u) wide). Returns (outline polygon, centreline, tip point, edge pts, spine pts)."""
    th = np.radians(curve(heading_deg, n))
    ds = L / (n - 1)
    x = x0 + np.concatenate([[0], np.cumsum(np.sin(th[:-1]) * ds)])
    z = z0 + np.concatenate([[0], np.cumsum(-np.cos(th[:-1]) * ds)])
    tx, tz = np.sin(th), -np.cos(th)
    nx_e, nz_e = tz, -tx          # edge side (toward -X for a blade heading -Z)
    wedge, wspine = curve(we, n, 5), curve(ws, n, 5)
    edge = np.stack([x + nx_e * wedge, z + nz_e * wedge], 1)
    spine = np.stack([x - nx_e * wspine, z - nz_e * wspine], 1)
    poly = [tuple(p) for p in edge] + [tuple(p) for p in spine[::-1]]
    return poly, np.stack([x, z], 1), (x[-1], z[-1]), edge, spine


def stroke(points, widths, closed=False):
    """A polygon round a polyline [(x, z)] with a width at each point (list or one number); round ends are not added."""
    p = np.array(points, dtype=float)
    w = np.full(len(p), widths, dtype=float) if np.isscalar(widths) else np.array(widths, dtype=float)
    t = np.gradient(p, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    n = np.stack([-t[:, 1], t[:, 0]], 1)
    a, b = p + n * (w[:, None] / 2), p - n * (w[:, None] / 2)
    return [tuple(q) for q in a] + [tuple(q) for q in b[::-1]]


def bez(p0, p1, p2, p3=None, n=24):
    """A quadratic (3 points) or cubic (4) Bezier as points."""
    t = np.linspace(0, 1, n)[:, None]
    a, b, c = np.array(p0, float), np.array(p1, float), np.array(p2, float)
    if p3 is None:
        return [tuple(q) for q in (1 - t) ** 2 * a + 2 * (1 - t) * t * b + t ** 2 * c]
    d = np.array(p3, float)
    return [tuple(q) for q in (1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t ** 2 * c + t ** 3 * d]


def ring(cx, cz, ro, ri, n=40):
    """An annulus as two loops (even-odd fills the ring)."""
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return [[(cx + ro * math.cos(t), cz + ro * math.sin(t)) for t in a], [(cx + ri * math.cos(t), cz + ri * math.sin(t)) for t in a]]


def disc(cx, cz, r, n=32):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return [(cx + r * math.cos(t), cz + r * math.sin(t)) for t in a]


def grip(z0=-0.78, z1=0.86, w=0.30, swell=0.04):
    zs = np.linspace(z0, z1, 12)
    half = [w / 2 + swell * math.sin(math.pi * (z - z0) / (z1 - z0)) for z in zs]
    return [(h, z) for h, z in zip(half, zs)] + [(-h, z) for h, z in zip(half[::-1], zs[::-1])]


# ---------- the candidates ----------
def c1_talon():
    """Recurved: the blade bows out to +X, swells into a belly on the edge side, then turns back and ends in a clipped talon
    whose point is aimed back across the axis. The guard is one swept arm on the edge side, its end turned the other way."""
    b, cl, tip, edge, spine = blade(4.55, [(0, 5), (0.3, 13), (0.55, 5), (0.75, -14), (0.9, -34), (1, -52)],
                                    [(0, .13), (.25, .17), (.5, .25), (.72, .38), (.88, .30), (.96, .12), (1, 0)],
                                    [(0, .11), (.5, .10), (.75, .09), (.9, .06), (1, 0)])
    arm = stroke(bez((0.0, -0.95), (-0.55, -0.95), (-0.9, -1.15), (-0.92, -1.7)), np.linspace(0.2, 0.09, 24))
    seat = stroke([(0.22, -0.92), (-0.4, -0.92)], 0.30)
    return dict(name="TALON", polys=[b, arm, seat, grip(), disc(0, 1.02, 0.17)], tip=tip,
                note="S curve, belly, point turned back. One swept guard arm (edge side)", verdict='KEPT: the S curve and the turned-back point read at 60 px. The thin claw guard is the weak part: round 2.')


def c2_kora():
    """Forward-weighted cleaver: a slim forte widening to a broad rounded 'ear' end that leans forward; a ring on one side."""
    b, cl, tip, edge, spine = blade(4.3, [(0, 3), (0.5, 7), (1, 20)],
                                    [(0, .12), (.3, .15), (.6, .33), (.8, .52), (.93, .44), (.985, .2), (1, 0)],
                                    [(0, .10), (.6, .10), (.85, .08), (.97, .04), (1, 0)])
    seat = stroke([(0.2, -0.92), (-0.45, -0.92)], 0.28)
    return dict(name="KORA EAR", polys=[b, seat, ring(-0.72, -1.02, 0.34, 0.2), grip(), disc(0, 1.02, 0.17)], tip=tip,
                note="forward-heavy broad end, one side ring", verdict='REJECTED: the ring reads as a key, the blade as a machete.')


def c3_yatagan():
    """Double curve: leans toward the edge first, then swings out in a belly; ears on the pommel, no guard."""
    b, cl, tip, edge, spine = blade(4.5, [(0, -10), (0.25, -14), (0.5, -2), (0.75, 18), (1, 32)],
                                    [(0, .12), (.3, .16), (.6, .24), (.85, .27), (.96, .12), (1, 0)],
                                    [(0, .10), (.6, .10), (.9, .06), (1, 0)])
    ears = stroke([(-0.5, 1.0), (-0.2, 0.82), (0.2, 0.82), (0.5, 1.0)], [0.12, 0.2, 0.2, 0.12])
    return dict(name="YATAGAN", polys=[b, grip(0.0 - 0.7, 0.8), ears, stroke([(0, -0.85), (0.3, -0.9)], 0.3)], tip=tip,
                note="double curve, eared pommel, no guard", verdict='REJECTED: elegant, but the ears read as a stand and there is no one-sided idea.')


def c4_sickle():
    """A deep crescent that turns back toward the wielder; a shell-like plate on one side."""
    b, cl, tip, edge, spine = blade(4.1, [(0, 8), (0.4, 30), (0.75, 62), (1, 96)],
                                    [(0, .13), (.4, .20), (.8, .22), (.95, .1), (1, 0)], [(0, .10), (.5, .10), (.9, .05), (1, 0)])
    plate = [(0.0, -0.85), (-0.55, -0.9), (-0.95, -1.2), (-0.85, -1.6), (-0.4, -1.45), (0.0, -1.15)]
    return dict(name="SICKLE", polys=[b, plate, grip(), disc(0, 1.02, 0.17)], tip=tip, note="deep crescent, shell guard", verdict='REJECTED: a scythe with a plate: a prop.')


def c5_stepped():
    """A straight blade with a stepped swelling and a notch cut into the back near the point; one long forward quillon."""
    b, cl, tip, edge, spine = blade(4.4, [(0, 3), (1, 5)],
                                    [(0, .12), (.5, .14), (.53, .28), (.93, .26), (.985, .1), (1, 0)],
                                    [(0, .10), (.78, .10), (.81, .01), (.9, .01), (.95, .06), (1, 0)])
    arm = stroke([(0.0, -0.95), (-0.6, -0.95), (-0.7, -1.9)], 0.18)
    return dict(name="STEPPED", polys=[b, arm, stroke([(0.2, -0.92), (-0.4, -0.92)], 0.3), grip(), disc(0, 1.02, 0.17)], tip=tip,
                note="straight, stepped belly, notched back, forward quillon", verdict='REJECTED: reads as a bayonet; the step is a flaw, not an idea.')


def c6_falcata():
    """Forward-curving blade (the curve toward the edge) with a hooked hand guard running from the guard to the pommel on one side."""
    b, cl, tip, edge, spine = blade(4.5, [(0, -2), (0.4, -10), (0.7, -24), (1, -44)],
                                    [(0, .12), (.4, .20), (.7, .32), (.9, .24), (1, 0)], [(0, .10), (.6, .10), (.9, .06), (1, 0)])
    bow = stroke(bez((0.08, 0.95), (-0.75, 0.6), (-0.75, -0.6), (-0.1, -0.95)), 0.14)
    return dict(name="FALCATA", polys=[b, bow, grip(), stroke([(0.2, -0.92), (-0.2, -0.92)], 0.3)], tip=tip,
                note="forward curve, knuckle bow on one side", verdict="REJECTED: bows to the other side (breaks the hand placement's convention), the loop reads as a duelling guard.")


def c7_talon_sweep():
    """The same talon blade; the guard arm sweeps back along the grip as a hand guard instead of forward."""
    b, cl, tip, edge, spine = blade(4.55, [(0, 5), (0.3, 13), (0.55, 5), (0.75, -14), (0.9, -34), (1, -52)],
                                    [(0, .13), (.25, .17), (.5, .25), (.72, .38), (.88, .30), (.96, .12), (1, 0)],
                                    [(0, .11), (.5, .10), (.75, .09), (.9, .06), (1, 0)])
    arm = stroke(bez((0.0, -0.95), (-0.7, -0.95), (-0.8, -0.1), (-0.55, 0.55)), np.linspace(0.2, 0.1, 24))
    return dict(name="TALON SWEEP", polys=[b, arm, stroke([(0.22, -0.92), (-0.4, -0.92)], 0.30), grip(), disc(0, 1.02, 0.17)], tip=tip,
                note="the talon, hand guard swept back", verdict='REJECTED: a guard swept back reads as a cutlass hilt: generic.')


def c8_plain():
    """The control: a plain curved sabre with two straight quillons."""
    b, cl, tip, edge, spine = blade(4.4, [(0, 3), (0.6, 11), (1, 22)],
                                    [(0, .13), (.5, .17), (.9, .15), (1, 0)], [(0, .10), (.8, .10), (1, 0)])
    return dict(name="CONTROL", polys=[b, stroke([(0.5, -0.92), (-0.5, -0.92)], 0.14), grip(), disc(0, 1.02, 0.17)], tip=tip,
                note="plain sabre, symmetric quillons: the thing to beat", verdict='THE CONTROL: the thing to beat.')


def ref_orthodox():
    b, cl, tip, edge, spine = blade(4.1, [(0, 0), (1, 0)], [(0, .12), (.9, .12), (1, 0)], [(0, .12), (.9, .12), (1, 0)])
    return dict(name="ORTHODOX DIR", polys=[b, stroke([(0.6, -0.92), (-0.6, -0.92)], 0.12), grip(), disc(0, 1.02, 0.17)], tip=tip,
                note="straight, slender, symmetric")


def ref_demonic():
    b, cl, tip, edge, spine = blade(4.3, [(0, 2), (1, 16)], [(0, .30), (.5, .36), (.9, .3), (1, 0)], [(0, .26), (.9, .24), (1, 0)])
    return dict(name="DEMONIC DIR", polys=[b, stroke([(0.8, -0.92), (-0.8, -0.92)], 0.34), grip(), disc(0, 1.02, 0.2)], tip=tip,
                note="massive, broad, dark")



# ---------- round 2: the talon blade refined, six guards ----------
def talon_blade(hook=-44, belly=0.42, L=4.7):
    return blade(L, [(0, 5), (0.3, 12), (0.55, 6), (0.76, -12), (0.9, -30), (1, hook)],
                 [(0, .13), (.22, .17), (.5, .26), (.74, belly), (.89, belly * 0.78), (.965, .13), (1, 0)],
                 [(0, .11), (.5, .10), (.76, .09), (.9, .055), (1, 0)])


def _r2(name, guard_polys, note, verdict="", **kw):
    b, cl, tip, edge, spine = talon_blade(**kw)
    seat = stroke([(0.24, -0.93), (-0.42, -0.93)], 0.30)
    return dict(name=name, polys=[b, seat, grip(), disc(0, 1.02, 0.17)] + guard_polys, tip=tip, note=note, verdict=verdict)


def r2_claw():
    arm = stroke(bez((-0.2, -0.95), (-0.75, -0.95), (-1.0, -1.2), (-0.98, -1.85)), np.linspace(0.24, 0.07, 24))
    return _r2("A CLAW", [arm], "tapering claw: in plan it reads as a TUSK", "REJECTED: a bare horn, and tusks are the Demonic family's language.")


def r2_knob():
    arm = stroke(bez((-0.2, -0.95), (-0.8, -0.95), (-1.02, -1.15), (-1.0, -1.8)), np.linspace(0.2, 0.17, 24))
    return _r2("B KNOB ARM", [arm, disc(-1.0, -1.88, 0.16)], "bar arm with a blunt finial: hardware, not a horn", "REJECTED: the ball makes it a hanger hook.")


def r2_loop():
    loop = ring(-0.78, -1.3, 0.34, 0.2, 48)
    web = stroke([(-0.3, -0.95), (-0.55, -1.05)], 0.22)
    return _r2("C SIDE LOOP", [loop, web], "closed side ring: man-made, a hoop", "REJECTED: fights the ring pommel and reads as a key.")


def r2_hook():
    arm = stroke(bez((-0.2, -0.95), (-1.0, -0.95), (-1.05, -1.9), (-0.55, -1.75)), np.linspace(0.2, 0.12, 24))
    return _r2("D RETURN HOOK", [arm], "bar out, forward, then back toward the blade: a catch with a slot", "CHOSEN: it answers the blade (the point turns one way, the arm the other). In 3D: stout hex bar, dark steel, brass bands, copper inlay.")


def r2_plate():
    plate = [(-0.2, -0.78), (-0.9, -0.98), (-1.12, -1.35), (-0.8, -1.55), (-0.45, -1.2), (-0.2, -1.12)]
    return _r2("E PLATE WING", [plate], "flat wing plate", "REJECTED: wings and plates are what the realm weapons and the first attempt already did.")


def r2_short():
    arm = stroke(bez((-0.2, -0.95), (-0.65, -0.95), (-0.86, -1.1), (-0.86, -1.45)), np.linspace(0.22, 0.14, 24))
    return _r2("F SHORT BAR", [arm, disc(-0.86, -1.5, 0.13)], "short bar and finial: quiet", "REJECTED: too quiet beside the blade; nothing for the eye to answer.")


ROUND2 = [r2_claw, r2_knob, r2_loop, r2_hook, r2_plate, r2_short]


def round2(chosen=3, path=None):
    cells = [f() for f in ROUND2]
    cw, ch = 280, 600
    cv = D.canvas(len(cells) * cw + 4, ch + 380)
    D.text(cv, 12, 8, "ROUND 2: THE TALON BLADE KEPT, SIX GUARDS ON ONE SIDE ONLY (PLAN VIEW, POINT UP)", INK, 2)
    for i, c in enumerate(cells):
        draw_cell(cv, c, i * cw, 28, cw, ch, 78, (0.04, 0.04, 0.05), (0.80, 0.82, 0.85), mark=(i == chosen), lscale=2)
        y_ = D.wrap(cv, i * cw + 6, 28 + ch + 4, c["note"], cw - 10, (0.78, 0.8, 0.85), 1, 10)
        D.wrap(cv, i * cw + 6, y_ + 3, c.get("verdict", ""), cw - 10, TEAL if c["verdict"].startswith(("KEPT", "CHOSEN")) else COPPER, 1, 10)
    y0 = 28 + ch + 110
    x = 8
    for c in cells:
        draw_cell(cv, c, x, y0, 50, 190, 25, (0.0, 0.0, 0.0), (1, 1, 1), hand=False, label=False)
        draw_cell(cv, c, x + 52, y0 + 66, 30, 124, 14, (0.0, 0.0, 0.0), (1, 1, 1), hand=False, label=False)
        D.text(cv, x, y0 + 194, c["name"][:10], DIM, 1)
        x += 100
    return D.save(cv, path or os.path.join(OUT, "02_silhouette_round2.png"))


CANDIDATES = [c1_talon, c2_kora, c3_yatagan, c4_sickle, c5_stepped, c6_falcata, c7_talon_sweep, c8_plain]
REFS = [ref_orthodox, ref_demonic]


# ---------- drawing ----------
def to_px(poly, scale, ox, oy):
    if isinstance(poly[0][0], (tuple, list)):
        return [[(ox + x * scale, oy + z * scale) for x, z in lp] for lp in poly]
    return [(ox + x * scale, oy + z * scale) for x, z in poly]


def draw_cell(cv, cand, x0, y0, w, h, scale, fg, bg_cell, hand=True, label=True, mark=False, lscale=1):
    """One silhouette cell. The origin (the grip's centre) sits 62% down the cell, so the point has the room."""
    cv[y0:y0 + h, x0:x0 + w] = bg_cell
    saved = cv.copy() if False else None
    ox, oy = x0 + w * 0.5, y0 + h * 0.78
    if hand:
        D.fill(cv, to_px([(-0.29, -0.4), (0.29, -0.4), (0.29, 0.4), (-0.29, 0.4)], scale, ox, oy), tuple(c * 0.35 + bg_cell[0] * 0.65 for c in fg))
    for p in cand["polys"]:
        D.fill(cv, to_px(p, scale, ox, oy), fg)
    if label:
        D.text(cv, x0 + 5, y0 + 4, cand["name"], DIM if bg_cell[0] < 0.5 else (0.3, 0.3, 0.3), lscale)
    if mark:
        D.rect(cv, x0 + 1, y0 + 1, x0 + w - 2, y0 + h - 2, TEAL, 3)


def silhouettes(chosen=0, path=None):
    cells = [f() for f in CANDIDATES]
    refs = [f() for f in REFS]
    cw, ch = 215, 640
    n = len(cells)
    W = n * cw + 20 + 2 * 100
    H = ch + 280 + 130
    cv = D.canvas(max(W, n * cw), H)
    D.text(cv, 12, 8, "UNORTHODOX SECRET SWORD: SILHOUETTE STUDY, 8 CANDIDATES (PLAN VIEW, THE FLAT THE PLAYER SEES, POINT UP)", INK, 2)
    for i, c in enumerate(cells):
        draw_cell(cv, c, i * cw, 28, cw, ch, 86, (0.04, 0.04, 0.05), (0.80, 0.82, 0.85), mark=(i == chosen), lscale=2)
        D.text(cv, i * cw + 6, 28 + ch - 16, str(i + 1), (0.3, 0.3, 0.3), 2)
        # the note under each cell
        y_ = D.wrap(cv, i * cw + 6, 28 + ch + 4, c["note"], cw - 10, (0.78, 0.8, 0.85), 1, 10)
        D.wrap(cv, i * cw + 6, y_ + 3, c.get("verdict", ""), cw - 10, TEAL if c["verdict"].startswith(("KEPT", "CHOSEN")) else COPPER, 1, 10)
    # the thumbnail row: black on white at 100 px tall, three scales (the player sees them small), the two other factions' directions at the end
    y0 = 28 + ch + 96
    D.text(cv, 12, y0 - 2, "AT THUMBNAIL SIZE (BLACK ON WHITE, 60 AND 100 PX TALL) NEXT TO THE OTHER TWO FACTIONS' DIRECTIONS", INK, 2)
    x = 8
    for c in cells + refs:
        tw = 52
        draw_cell(cv, c, x, y0 + 14, tw, 200, 26, (0.0, 0.0, 0.0), (1, 1, 1), hand=False, label=False)
        draw_cell(cv, c, x + tw + 2, y0 + 14 + 70, 34, 130, 16, (0.0, 0.0, 0.0), (1, 1, 1), hand=False, label=False)
        D.text(cv, x, y0 + 14 + 204, c["name"][:9], DIM, 1)
        x += tw + 2 + 34 + 12 if True else 0
    return D.save(cv, path or os.path.join(OUT, "01_silhouette_sheet.png"))


# ---------- the research board ----------
def board(path=None):
    """Real blade forms drawn in plan as line studies, each with the principle taken."""
    refs = []

    def add(name, polys, note, took):
        refs.append((name, polys, note, took))

    b, *_ = blade(4.3, [(0, 0), (1, -28)], [(0, .1), (.35, .15), (.65, .27), (.9, .2), (1, 0)], [(0, .08), (.9, .06), (1, 0)])
    add("KOPIS (GREEK)", [b, stroke([(0, -0.85), (0.1, -0.9)], 0.25), grip(-0.7, 0.7, 0.26)], "single edge, forward-curving, weight swells toward the point",
        "TOOK: the belly. A blade that gets heavier toward the end looks like it wants to fall")
    b, *_ = blade(4.2, [(0, -4), (1, -36)], [(0, .1), (.45, .18), (.75, .28), (.92, .18), (1, 0)], [(0, .08), (.9, .05), (1, 0)])
    add("FALCATA (IBERIA)", [b, stroke(bez((0.0, 0.8), (-0.55, 0.5), (-0.55, -0.5), (-0.05, -0.85)), 0.1), grip(-0.7, 0.7, 0.24)],
        "forward curve; the hilt curls round the hand on ONE side, a closed one-sided hand guard",
        "TOOK: guard on one side only, part of the hilt line")
    b, *_ = blade(4.0, [(0, 4), (0.5, 38), (1, 80)], [(0, .12), (.6, .16), (1, 0)], [(0, .08), (.9, .05), (1, 0)])
    add("KHOPESH (EGYPT)", [b, grip(-0.7, 0.7, 0.24)], "a sickle that is a sword: edge on the outer curve, the tip comes back toward the hand",
        "TOOK: a point that turns back. NOT the sickle depth")
    b, *_ = blade(4.3, [(0, 4), (0.5, 12), (1, 30)], [(0, .1), (.5, .12), (.75, .16), (1, 0)], [(0, .08), (.7, .08), (.8, .22), (.9, .1), (1, 0)])
    add("KILIJ (OTTOMAN)", [b, stroke([(0.35, -0.9), (-0.35, -0.9)], 0.1), grip(-0.7, 0.7, 0.24)], "the 'yelman': the last third widens and the back is sharpened, a clipped heavy point",
        "TOOK: a clipped point, widening ahead of the hand")
    b, *_ = blade(4.2, [(0, -12), (0.3, -12), (0.6, 8), (1, 28)], [(0, .1), (.5, .18), (.85, .2), (1, 0)], [(0, .08), (.9, .05), (1, 0)])
    add("YATAGAN (OTTOMAN)", [b, grip(-0.7, 0.7, 0.22), stroke([(-0.45, 0.98), (-0.15, 0.78), (0.15, 0.78), (0.45, 0.98)], [0.1, 0.16, 0.16, 0.1])],
        "a double curve; no guard at all: two flared 'ears' on the pommel lock the hand",
        "TOOK: the double (S) curve. A guard is not a must")
    b, *_ = blade(4.3, [(0, 2), (0.5, 8), (1, 18)], [(0, .1), (.35, .14), (.65, .3), (.85, .45), (.95, .32), (1, 0)], [(0, .08), (.8, .08), (1, 0)])
    add("KORA (NEPAL)", [b, stroke([(0.3, -0.9), (-0.3, -0.9)], 0.12), grip(-0.7, 0.7, 0.24)], "a slim forte opening into a broad forward belly: the weight is far ahead of the hand",
        "TOOK: forward weight and an 'ear' of metal at the end")
    b, *_ = blade(4.3, [(0, 0), (0.5, 3), (1, 6)], [(0, .12), (1, .1)], [(0, .11), (1, .1)])
    b, *_ = blade(4.3, [(0, 0), (1, 12)], [(0, .1), (.88, .12), (.96, .07), (1, 0)], [(0, .1), (.88, .08), (.96, .03), (1, 0)])
    add("KATANA/TACHI (JAPAN)", [b, disc(0, -0.92, 0.38, 28), grip(-0.8, 0.8, 0.22)], "one smith's whole craft: forged grain, a temper line, a big clean point (the kissaki)",
        "TOOK: forged grain, hardened-edge line, layered fittings (collar, spacer, guard)")
    b, *_ = blade(3.6, [(0, 0), (1, 0)], [(0, .12), (.9, .12), (1, 0)], [(0, .12), (.9, .12), (1, 0)])
    add("HWANDUDAEDO (KOREA)", [b, grip(-0.6, 0.6, 0.18), ring(0, 0.92, 0.36, 0.22)], "a heavy ring where the pommel would be, from the tombs of Silla and Gaya; bronze, gilded",
        "TOOK: a real ring pommel (Korean, not the Han dao's)")
    rod = stroke([(0.0, -0.8), (0.0, -3.4)], 0.09)
    hook = stroke(bez((0.0, -1.1), (-0.5, -1.1), (-0.55, -1.7), (-0.3, -2.3)), 0.08)
    add("JITTE (JAPAN)", [rod, hook, grip(-0.5, 0.5, 0.2)], "an iron police rod with ONE hook on one side to catch a blade",
        "TOOK: a one-sided catching arm as a working part")
    cw, ch = 300, 250
    cols, rows = 5, 2
    W, H = cols * cw + 20, rows * (ch + 120) + 230
    cv = D.canvas(W, H)
    D.text(cv, 12, 10, "RESEARCH BOARD: UNCONVENTIONAL REAL BLADE FORMS AND WHAT WAS TAKEN AS PRINCIPLE", INK, 3)
    D.text(cv, 12, 40, "STYLE RULE: KOREAN + JAPANESE + ORIGINAL. NO DAO/JIAN FITTINGS, NO RUYI, DRAGON, TAIJI, KNOTS OR LETTERING.", DIM, 2)
    D.text(cv, 12, 56, "NO EXISTING SWORD IS COPIED: THESE ARE THE AUTHOR'S OWN LINE STUDIES OF THE TYPES. PLAN VIEW, POINT UP.", DIM, 2)
    for i, (name, polys, note, took) in enumerate(refs[:10]):
        r, c = divmod(i, cols)
        x0, y0 = 10 + c * cw, 86 + r * (ch + 130)
        cv[y0:y0 + ch, x0:x0 + cw - 10] = (0.8, 0.82, 0.85)
        D.text(cv, x0 + 6, y0 + 5, name, (0.25, 0.25, 0.28), 2)
        ox, oy = x0 + (cw - 10) * 0.5, y0 + ch * 0.80
        for p in polys:
            D.fill(cv, to_px(p, 34, ox, oy), (0.04, 0.04, 0.05))
        yy = D.wrap(cv, x0 + 4, y0 + ch + 6, note, cw - 18, (0.82, 0.84, 0.88), 1, 10)
        D.wrap(cv, x0 + 4, yy + 2, took, cw - 18, TEAL, 1, 10)
    y = 86 + 2 * (ch + 130) - 6
    D.text(cv, 12, y, "WHAT THE DESIGN TOOK (PRINCIPLES, NOT SHAPES): FORWARD WEIGHT AND A SWELLING BELLY (KOPIS, KORA, KILIJ). A POINT THAT TURNS BACK (KHOPESH, YATAGAN).", INK, 1)
    D.text(cv, 12, y + 12, "A GUARD ON ONE SIDE ONLY, FORMED AS A WORKING CATCH (FALCATA HILT, JITTE). A REAL KOREAN RING POMMEL. LAYERED FITTINGS, FORGED GRAIN AND A TEMPER LINE (TACHI).", INK, 1)
    D.text(cv, 12, y + 24, "HOW MASTER SMITHS HANDLED IT: THICKNESS TAPERS FROM FOOT TO POINT; THE EDGE IS HONED BRIGHT AND SET OFF BY A DARK, GRAINED BODY; FITTINGS ARE COPPER, BRONZE AND BRASS", INK, 1)
    D.text(cv, 12, y + 36, "PATINATED ON PURPOSE (VERDIGRIS IN THE HOLLOWS); GRIPS ARE WRAPPED TIGHT OVER A CORE. NOTHING HERE IS COPIED FROM A MUSEUM PIECE OR ANOTHER GAME'S WEAPON.", INK, 1)
    return D.save(cv, path or os.path.join(OUT, "00_research_board.png"))


if __name__ == "__main__":
    stage = (sys.argv[sys.argv.index("--") + 1:] or ["all"])[0] if "--" in sys.argv else "all"
    if stage in ("board", "all"):
        print(board())
    if stage in ("silhouettes", "all"):
        print(silhouettes())
    if stage in ("round2", "all"):
        print(round2())
