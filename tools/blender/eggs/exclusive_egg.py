"""The Exclusive Egg (the game's Robux egg), second generation (see egg_forge.py).

Exclusive Egg, "the celestial night": it holds three exclusive pets, the Eclipse Dreadwing (Mythic), the
Nine-Tail Moonfox (Secret) and Crysalith, the Eternal Frost (Divine), and wears one sign of each on a
shell of deep midnight-indigo lacquer with a faint pearly sheen.
- The eclipse, its focal point: a black satin disc inlaid on its front, ringed by a corona of cyan-white light
  (Neon) that is a hairline on one side and heavy on the other, as at the moment of totality, with long soft
  streamers painted out across the lit lacquer. The Dreadwing's eclipse.
- Three silver tail-ribbons sweep up round the shell in one spiral, each a fox's brush: midnight at the
  root, silver through the body, frosted white at the tip, combed into strands, the outer edge swelling into
  locks. They cross the front on the diagonal. The Moonfox's tails.
- Faceted ice crystals break through the shell in two clusters near the base (one at the front, off-centre; one
  bursting through the band at the back) and one near the crown, pale
  ice-blue with bright edges, the lacquer frosted and cracked round them; hairline cracks run from the crown
  cluster with the moonlight inside showing through. Crysalith's frost.
- The lower shell darkens to obsidian and is layered like feathers, in faint relief and sheen only.
- A silver filigree band near the base: two rails with a running wave-scroll and beads between them.
- Small raised four-point stars scattered over the upper shell.

Run headless (one stage per call, or all):
    Blender -b --factory-startup -P tools/blender/eggs/exclusive_egg.py -- clay|look|build|verify|all
Environment: EXCLUSIVE_EGG_WORK, a folder for working renders (default renders/eggs/ExclusiveEgg_work).
Writes assets/eggs/ExclusiveEgg.fbx and its four maps, tools/blender/eggs/ExclusiveEgg.blend,
assets/ui/egg_icons/ExclusiveEgg.png, assets/ui/store/ExclusiveEgg_premium_512.png and
renders/eggs/ExclusiveEgg_review.png.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import egg_bake as B  # noqa: E402
import egg_forge as F  # noqa: E402
import egg_hi as Hm  # noqa: E402
import egg_kit as K  # noqa: E402

W = K.W
V = Vector
TAU = F.TAU
EGG = "ExclusiveEgg"
REPO = K.REPO
WORK = os.environ.get("EXCLUSIVE_EGG_WORK") or os.path.join(REPO, "renders", "eggs", EGG + "_work")
BLEND = os.path.join(HERE, EGG + ".blend")
CORONA = "78d2ff"           # (120, 210, 255): a saturated cyan-white, since Neon pales light colours


def srgb(r, g, b):
    """sRGB 0-255 to linear, for shader colours."""
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))


# ---------- headless ----------
def _override(obj):
    """egg_bake's mode switches without a window (Blender -b has none)."""
    return bpy.context.temp_override(active_object=obj, object=obj, selected_objects=[obj], selected_editable_objects=[obj])


if bpy.app.background:
    B._ui_override = _override


def gpu():
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = kind
        except TypeError:
            continue
        prefs.get_devices()
        if any(d.type == kind for d in prefs.devices):
            for d in prefs.devices:
                d.use = True
            return kind
    return "CPU"


# ---------- the shell's own measures ----------
def _meridian():
    v = np.linspace(0, 1, 4001)
    p = F.shell_pos(np.full_like(v, 0.5), v)
    L = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    return v, L


VT, LT = _meridian()


def arc(v):
    """Length along the shell from the bottom up to v."""
    return np.interp(v, VT, LT)


def rad(v):
    return F.R * np.sin(np.pi * v) * (1 + 0.13 * np.cos(np.pi * v))


def frame_at(s0, v0, roll=0.0):
    """A plane against the egg at (s0, v0), as Field.plane makes it: centre, normal, x and y."""
    c, n = F.on(s0, v0), F.normal(s0, v0)
    e1 = V((0, 1, 0)).cross(n).normalized()
    e2 = n.cross(e1).normalized()
    if roll:
        ca, sa = math.cos(roll), math.sin(roll)
        e1, e2 = e1 * ca + e2 * sa, e2 * ca - e1 * sa
    return c, n, e1, e2


def project(fr, x, y):
    """The (s, v) on the shell whose plane coordinates are (x, y): straight along the plane's normal, as
    Field.plane measures the paint, so geometry and paint line up exactly."""
    c, n, e1, e2 = fr
    q = c + e1 * x + e2 * y
    s = math.atan2(q.x, q.z) / TAU + 0.5
    v = math.acos(max(-1.0, min(1.0, 1 - 2 * max(0.001, min(F.H - 0.001, q.y)) / F.H))) / math.pi

    def coords(ss, vv):
        d = F.on(ss % 1.0, vv) - c
        return d.dot(e1), d.dot(e2)
    for _ in range(6):
        a, b = coords(s, v)
        ra, rb = a - x, b - y
        if abs(ra) + abs(rb) < 1e-7:
            break
        h = 1e-5
        a1, b1 = coords(s + h, v)
        a2, b2 = coords(s, v + h)
        j = np.array([[(a1 - a) / h, (a2 - a) / h], [(b1 - b) / h, (b2 - b) / h]])
        ds, dv = np.linalg.solve(j, [-ra, -rb])
        s, v = s + ds, min(0.999, max(0.001, v + dv))
    return s % 1.0, v


def lifted(s, v, h):
    return F.on(s, v, h)


# ---------- the design ----------
BAND = (0.165, 0.245)            # v of the filigree band's lower and upper rails
ECL = dict(s=0.5, v=0.62, R=0.29, thin=0.007, thick=0.088, heavy=218)   # the corona is heaviest toward `heavy` (degrees)
# the corona's broad bulges (angle degrees, reach, width degrees), and the long soft streamers painted round
# it on the lacquer (angle degrees, length, width degrees): lopsided on purpose, an eclipse and not an iris
FLARES = ((205, 0.03, 22), (250, 0.018, 16), (40, 0.012, 14))
STREAMERS = ((196, 0.7, 10), (226, 0.5, 8), (252, 0.32, 7), (170, 0.3, 7), (24, 0.4, 7), (62, 0.24, 6), (300, 0.22, 6))
# the ribbons, one triple spiral: waypoints (s, v) from root to tip (s runs past 1), widest width, height, tip
# lift, seed. They cross the front on the diagonal, never hanging either side of the eclipse like arms.
RIBBONS = (
    ("Sweep", ((0.3, 0.265), (0.38, 0.305), (0.46, 0.358), (0.54, 0.42), (0.61, 0.5), (0.655, 0.59), (0.68, 0.68), (0.688, 0.755)), 0.36, 0.11, 0.07, 1),
    ("Climb", ((0.66, 0.265), (0.74, 0.3), (0.82, 0.35), (0.9, 0.42), (0.97, 0.5), (1.02, 0.59), (1.05, 0.68), (1.062, 0.765)), 0.36, 0.11, 0.07, 2),
    ("Curl", ((0.99, 0.265), (1.07, 0.3), (1.15, 0.352), (1.23, 0.422), (1.3, 0.5), (1.345, 0.59), (1.37, 0.68), (1.378, 0.76)), 0.34, 0.105, 0.07, 3),
)
# ice clusters breaking out of the shell: name, s, v, crystals [(azimuth degrees, lean degrees, length, radius, seed)]
CLUSTERS = (
    ("IceFront", 0.555, 0.245, ((165, 20, 0.5, 0.115, 11), (215, 36, 0.36, 0.09, 12), (110, 36, 0.3, 0.08, 13), (262, 50, 0.22, 0.064, 14), (60, 48, 0.17, 0.055, 15))),
    ("IceBack", 0.845, 0.2, ((20, 18, 0.42, 0.1, 21), (320, 38, 0.3, 0.078, 22), (85, 36, 0.24, 0.066, 23))),
    ("IceCrown", 0.625, 0.865, ((330, 24, 0.4, 0.092, 31), (20, 46, 0.27, 0.072, 32), (260, 42, 0.22, 0.062, 33), (90, 56, 0.15, 0.05, 34))),
)
CRACK_SEED = 41
STAR_SEED = 51


def flare(theta):
    """How far the corona reaches past the disc at angle theta (radians, numpy or float): thin on one side,
    heavier opposite, with broad uneven bulges."""
    heavy = math.radians(ECL["heavy"])
    out = ECL["thin"] + (ECL["thick"] - ECL["thin"]) * (0.5 + 0.5 * np.cos(theta - heavy)) ** 1.5
    for deg, reach, width in FLARES:
        d = (theta - math.radians(deg) + np.pi) % TAU - np.pi
        out = out + reach * np.exp(-np.abs(d) / math.radians(width))
    return out


def ribbon_path(points, n=150):
    """A smooth line through (s, v) waypoints, as [(point, normal)] evenly spaced along it."""
    pts = np.array(points, dtype=np.float64)
    pad = np.vstack([pts[0] * 2 - pts[1], pts, pts[-1] * 2 - pts[-2]])
    dense = []
    for i in range(1, len(pad) - 2):
        p0, p1, p2, p3 = pad[i - 1], pad[i], pad[i + 1], pad[i + 2]
        for t in np.linspace(0, 1, 24, endpoint=False):
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    dense.append(pts[-1])
    dense = np.array(dense)
    xyz = np.array([tuple(F.on(s % 1.0, v)) for s, v in dense])
    L = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(xyz, axis=0), axis=1))])
    want = np.linspace(0, L[-1], n)
    s = np.interp(want, L, dense[:, 0])
    v = np.interp(want, L, dense[:, 1])
    return [(F.on(a % 1.0, b), F.normal(a % 1.0, b)) for a, b in zip(s, v)], L[-1]


def brush_width(t, wmax):
    """A fox's brush: slim at the root, full through the middle, drawn to a soft point."""
    body = (0.2 + 0.8 * F.sstep(0.0, 0.58, t)) * (1 - F.sstep(0.6, 1.0, t) ** 1.6)
    return wmax * body + 0.003


def brush_locks(t, seed=0):
    """The outer edge only, swelling into a few soft locks toward the tip (1 = none)."""
    out = 1.0
    for k, at in enumerate((0.5, 0.66, 0.8)):
        out += (0.16 - 0.03 * k) * math.exp(-((t - at - 0.02 * seed) / 0.045) ** 2)
    return out


def brush_height(t, hmax):
    return hmax * (0.5 + 0.5 * F.sstep(0.0, 0.45, t)) * (1 - 0.45 * F.sstep(0.75, 1.0, t))


def brush(hi, path, width, height, lift, locks=None, sides=16, sink=0.02, mat=0):
    """A closed, raised brush lying along a path of (point, normal) pairs: domed on top, its feet sunk into
    the shell, the tip lifted clear of it. UVs: u across the top (0..1), v from root (0) to tip (1)."""
    n = len(path)
    rings = []
    for i, (p, nrm) in enumerate(path):
        a = path[max(i - 1, 0)][0]
        b = path[min(i + 1, n - 1)][0]
        tng = (b - a).normalized()
        side = tng.cross(nrm).normalized()
        up = side.cross(tng).normalized()
        t = i / (n - 1)
        w, h, lf = width(t) / 2, height(t), lift(t)
        ring = []
        for j in range(sides + 1):
            th = TAU * (j % sides) / sides          # the last column repeats the first exactly, so the seam welds shut
            x, sy = math.cos(th), math.sin(th)
            y = (h + 0.005) * max(sy, 0.0) ** 0.55 - 0.005 if sy >= 0 else -sink * (-sy)
            wx = w * (locks(t) if (locks and x > 0) else 1.0)
            ring.append((hi.v(p + side * (wx * x) + up * (y + lf)), ((1 - x) / 2, t)))
        rings.append(ring)
    for i in range(n - 1):
        for j in range(sides):
            a0, a1 = rings[i][j], rings[i][j + 1]
            b0, b1 = rings[i + 1][j], rings[i + 1][j + 1]
            hi.f([a0[0], a1[0], b1[0], b0[0]], [a0[1], a1[1], b1[1], b0[1]], mat)
    for ring, (p, nrm), tip in ((rings[0], path[0], False), (rings[-1], path[-1], True)):
        t = 1.0 if tip else 0.0
        a = path[-2][0] if tip else path[1][0]
        tng = (p - a).normalized()
        cap = hi.v(p + tng * (width(t) * 0.35) + nrm * (lift(t) + height(t) * 0.3))
        for j in range(sides):
            hi.f([ring[j][0], ring[j + 1][0], cap], [ring[j][1], ring[j + 1][1], (0.5, t)], mat)


def eclipse_disc(hi, mat=0, sides=72):
    """The black disc: a low puck that follows the shell, its rim rounded, sunk at its foot."""
    fr = frame_at(ECL["s"], ECL["v"])
    R = ECL["R"]
    prof = [(0.0, 0.02), (0.4, 0.0198), (0.75, 0.019), (0.92, 0.0175), (0.985, 0.0145), (1.0, 0.009), (1.0, -0.02), (0.9, -0.03)]
    rows = []
    for r, h in prof:
        row = []
        for k in range(sides):
            a = TAU * k / sides
            s, v = project(fr, r * R * math.cos(a), r * R * math.sin(a)) if r > 0 else (ECL["s"], ECL["v"])
            row.append(hi.v(lifted(s, v, h)))
        rows.append(row)
    top = hi.v(lifted(ECL["s"], ECL["v"], prof[0][1]))
    bot = hi.v(lifted(ECL["s"], ECL["v"], -0.03))
    uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for k in range(sides):
        m = (k + 1) % sides
        hi.f([top, rows[1][m], rows[1][k]], uv[:3], mat)
        for j in range(1, len(rows) - 1):
            hi.f([rows[j][k], rows[j][m], rows[j + 1][m], rows[j + 1][k]], uv, mat)
        hi.f([bot, rows[-1][k], rows[-1][m]], uv[:3], mat)


def corona(hi, steps=120, mat=0):
    """The corona: a thin ring of light hugging the disc's rim, heavier on one side, with broad uneven bulges.
    A closed loop of section swept round, lying on the shell over the disc's edge."""
    fr = frame_at(ECL["s"], ECL["v"])
    R = ECL["R"]
    rows = []
    for k in range(steps):
        a = TAU * k / steps
        ro = R + float(flare(a))
        sec = [(R * 0.975, 0.026), (R + 0.004, 0.029), ((R + ro) / 2 + 0.003, 0.022), (ro - 0.003, 0.01), (ro, -0.006), (R * 0.975, -0.02)]
        row = []
        for r, h in sec:
            s, v = project(fr, r * math.cos(a), r * math.sin(a))
            row.append(hi.v(lifted(s, v, h)))
        rows.append(row)
    m = len(rows[0])
    for k in range(steps):
        n = (k + 1) % steps
        for j in range(m):
            q = (j + 1) % m
            hi.f([rows[k][j], rows[k][q], rows[n][q], rows[n][j]], [(j / m, k / steps), ((j + 1) / m, k / steps), ((j + 1) / m, (k + 1) / steps), (j / m, (k + 1) / steps)], mat)


def ice_cluster(hi, s0, v0, crystals, mat=0, lift=0.55):
    c, n = F.on(s0, v0), F.normal(s0, v0)
    e1 = V((0, 1, 0)).cross(n).normalized()
    e2 = n.cross(e1).normalized()
    up = V((0, 1, 0))
    for az, lean, length, radius, seed in crystals:
        a = math.radians(az)
        out = e1 * math.cos(a) + e2 * math.sin(a)
        d = (n * math.cos(math.radians(lean)) + out * math.sin(math.radians(lean)) + up * lift).normalized()
        base = c + out * radius * 0.9 - n * 0.035
        F.crystal(hi, base, d, length, radius, sides=6, tip=0.3, seed=seed, mat=mat, taper=0.86)


def mat_ribbon(name="EX_Ribbon"):
    """A fox's brush in silver: deep midnight at the root, silver through the body, frosted white at the
    tip, combed into strands whose darker streaks run up into the silver."""
    g = Hm._Graph(name)
    u, t, _ = g.sep(g.coords("UV"))
    rnd = g.n("ShaderNodeObjectInfo").outputs["Random"]
    vec = g.n("ShaderNodeCombineXYZ")
    g.link(g.math("MULTIPLY", u, 1.0), vec.inputs[0])
    g.link(g.math("MULTIPLY", t, 5.0), vec.inputs[1])
    g.link(g.math("MULTIPLY", rnd, 9.0), vec.inputs[2])
    strands = g.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", **{"Scale": 6.0, "Distortion": 2.5, "Detail": 3.0, "Detail Scale": 1.4})
    g.link(vec.outputs[0], strands.inputs["Vector"])
    jag = g.n("ShaderNodeTexNoise", **{"Scale": 3.0, "Detail": 3.0})
    g.link(vec.outputs[0], jag.inputs["Vector"])
    tt = g.math("ADD", t, g.math("MULTIPLY", g.math("SUBTRACT", jag.outputs["Fac"], 0.5), 0.16))
    col = g.ramp(tt, [(0.0, srgb(18, 20, 58)), (0.17, srgb(30, 36, 96)), (0.34, srgb(132, 146, 204)), (0.46, srgb(206, 215, 240)),
                      (0.6, srgb(226, 232, 248)), (0.72, srgb(250, 252, 255)), (1.0, srgb(255, 255, 255))])
    fine = g.ramp(strands.outputs["Fac"], [(0.2, (0.0, 0.0, 0.0)), (0.8, (1.0, 1.0, 1.0))])
    dark = g.mix(1.0, col, (0.7, 0.72, 0.8), "MULTIPLY")
    col = g.mix(g.bw(fine), dark, col)
    # the edges a little darker, so each ribbon keeps its outline against the next
    edge = g.math("POWER", g.math("ABSOLUTE", g.math("SUBTRACT", g.math("MULTIPLY", u, 2.0), 1.0)), 3.0)
    col = g.mix(g.math("MULTIPLY", edge, 0.35), col, (0.08, 0.1, 0.22))
    col = g.ao(col, 0.05, 0.6)
    rough = g.math("ADD", 0.2, g.math("MULTIPLY", g.bw(g.ramp(t, [(0.62, (0, 0, 0)), (0.82, (1, 1, 1))])), 0.24))
    metal = g.bw(g.ramp(t, [(0.0, (0.15, 0.15, 0.15)), (0.38, (0.6, 0.6, 0.6)), (0.6, (0.5, 0.5, 0.5)), (0.76, (0.0, 0.0, 0.0))]))
    return g.finish(col, rough, metal, g.bump(g.bw(fine), 0.35, 0.004))


def mat_ice(name="EX_Ice"):
    """Ice crystal: each facet its own pale ice-blue, the edges bright."""
    g = Hm._Graph(name)
    geo = g.n("ShaderNodeNewGeometry")
    tn = geo.outputs["True Normal"]
    tone = g.n("ShaderNodeTexNoise", **{"Scale": 6.0, "Detail": 0.0})
    g.link(tn, tone.inputs["Vector"])
    col = g.ramp(tone.outputs["Fac"], [(0.3, srgb(96, 150, 210)), (0.5, srgb(160, 206, 240)), (0.7, srgb(214, 238, 255))])
    bev = g.n("ShaderNodeBevel", samples=8)
    bev.inputs["Radius"].default_value = 0.01
    dot = g.n("ShaderNodeVectorMath", operation="DOT_PRODUCT")
    g.link(bev.outputs["Normal"], dot.inputs[0])
    g.link(tn, dot.inputs[1])
    edge = g.math("MINIMUM", g.math("MULTIPLY", g.math("SUBTRACT", 1.0, dot.outputs["Value"]), 9.0), 1.0)
    col = g.mix(edge, col, srgb(245, 252, 255))
    return g.finish(col, 0.08, 0.0)


def mat_eclipse(name="EX_Eclipse"):
    """The eclipse's disc: black glass with the faintest violet drifting in it."""
    g = Hm._Graph(name)
    co = g.coords()
    nz = g.n("ShaderNodeTexNoise", **{"Scale": 9.0, "Detail": 3.0})
    g.link(co, nz.inputs["Vector"])
    col = g.ramp(nz.outputs["Fac"], [(0.35, srgb(5, 5, 12)), (0.7, srgb(14, 11, 32))])
    return g.finish(col, 0.32, 0.0)


# ---------- the shell, painted ----------
def star_sites():
    """Small stars, scattered where nothing else is: away from the eclipse, the ribbons, the ice, each
    other."""
    rnd = np.random.default_rng(STAR_SEED)
    avoid = []
    for _, pts, wmax, _, _, _ in RIBBONS:
        path, _ = ribbon_path(pts, 60)
        avoid += [(p, wmax / 2 + 0.05) for p, _ in path]
    avoid.append((F.on(ECL["s"], ECL["v"]), ECL["R"] + 0.3))
    for _, s0, v0, _ in CLUSTERS:
        avoid.append((F.on(s0, v0), 0.3))
    sites = []
    tries = 0
    while len(sites) < 20 and tries < 4000:
        tries += 1
        s, v = rnd.uniform(0, 1), rnd.uniform(0.47, 0.93)
        p = F.on(s, v)
        if any((p - q).length < r for q, r in avoid):
            continue
        if any((p - F.on(a, b)).length < 0.36 for a, b, _, _ in sites):
            continue
        sites.append((s, v, rnd.uniform(0.06, 0.08) if len(sites) < 5 else rnd.uniform(0.022, 0.042), rnd.uniform(-0.4, 0.4)))
    return sites


def crack_lines():
    """Hairline cracks running out from the crown's ice: (polyline in plane coordinates, width)."""
    rnd = np.random.default_rng(CRACK_SEED)
    lines = []
    for a0, length in ((-40, 0.42), (35, 0.36), (110, 0.3), (190, 0.4), (250, 0.26)):
        a = math.radians(a0)
        pts = [(math.cos(a) * 0.11, math.sin(a) * 0.11)]
        step = length / 7
        for i in range(7):
            a += rnd.uniform(-0.5, 0.5)
            x, y = pts[-1]
            pts.append((x + math.cos(a) * step, y + math.sin(a) * step))
            if i == 2:
                b = a + rnd.choice((-1, 1)) * rnd.uniform(0.6, 1.0)
                q = [pts[-1]]
                for _ in range(3):
                    b += rnd.uniform(-0.4, 0.4)
                    q.append((q[-1][0] + math.cos(b) * step * 0.8, q[-1][1] + math.sin(b) * step * 0.8))
                lines.append((q, 0.6))
        lines.append((pts, 1.0))
    return lines


def paint():
    f = F.Field()
    P, S, Vv = f.P, f.S, f.V
    Y = arc(Vv)
    warp = np.stack([F.fbm(P, 1.2, 3, seed=s) for s in (901, 902, 903)], -1) * 0.25
    # the lacquer: deep midnight-indigo, darkest at the foot, lifting toward the crown
    col = F.ramp(np.clip(Vv * 1.04 + F.fbm(P + warp, 1.0, 3, seed=904) * 0.1, 0, 1),
                 [(0.0, "07071a"), (0.3, "100f38"), (0.55, "17164c"), (0.8, "201e66"), (1.0, "2a2780")])
    # a faint pearly sheen drifting through it
    sheen = F.sstep(0.05, 0.6, F.fbm(P + warp, 1.4, 4, 0.5, seed=905))
    tint = F.ramp(np.clip(F.fbm(P, 0.9, 2, seed=906) * 1.6 + 0.5, 0, 1), [(0.0, "5a4fd0"), (0.3, "3a8ac8"), (0.55, "4f6fd8"), (0.8, "9060cc"), (1.0, "5a4fd0")])
    col = F.mix(col, tint, sheen * 0.3)
    height = 0.0004 * F.fbm(P, 30.0, 2, seed=907)
    rough = np.full(S.shape, 0.09)
    metal = np.zeros(S.shape)

    # obsidian feathers on the lower shell: layered rows, in relief and sheen only
    y_lo = arc(BAND[1]) + 0.02
    y_hi = arc(0.47)
    row_h = 0.15
    j0 = np.floor((Y - y_lo) / row_h)
    best_frac = np.zeros(S.shape)
    best_cx = np.zeros(S.shape)
    for dj in (0, -1):
        j = j0 + dj
        base = y_lo + j * row_h
        circ = TAU * np.maximum(rad(np.interp(base + row_h / 2, LT, VT)), 0.2)
        count = np.maximum(np.round(circ / 0.14), 6)
        u = S * count + 0.5 * (j % 2)
        cx = (u - np.floor(u)) - 0.5
        edge = base + 0.06 * (np.abs(cx) * 2) ** 1.6
        frac = (Y - edge) / row_h
        take = (frac >= 0) & (frac < 1.2)
        better = take & ((best_frac == 0) | (frac < best_frac))
        best_frac = np.where(better, frac, best_frac)
        best_cx = np.where(better, cx, best_cx)
    weight = F.sstep(y_lo - 0.02, y_lo + 0.12, Y) * (1 - F.sstep(y_hi - 0.35, y_hi, Y)) * (best_frac > 0)
    shingle = np.clip(1 - best_frac, 0, 1) ** 1.5
    barbs = 0.5 + 0.5 * np.sin(TAU * (np.abs(best_cx) * 7 + best_frac * 3.2))
    rim = 1 - F.sstep(0.0, 0.06, best_frac)
    col = F.mix(col, np.array((0.025, 0.022, 0.06)), weight * 0.55)
    col = F.mix(col, np.array((0.16, 0.13, 0.3)), weight * rim * 0.35)
    height = height + weight * (0.0025 * shingle + 0.0002 * barbs)
    rough = rough + weight * (0.08 + 0.06 * barbs)
    # obsidian below the band too
    below = 1 - F.sstep(arc(BAND[0]) - 0.04, arc(BAND[0]), Y)
    col = F.mix(col, np.array((0.02, 0.018, 0.05)), below * 0.5)

    # the silver filigree band: two rails, a running wave-scroll and beads between
    silver = F.mix(np.array((0.72, 0.75, 0.84)), np.array((0.93, 0.95, 1.0)), np.clip(0.5 + F.fbm(P, 20.0, 2, seed=908) * 0.8, 0, 1))
    ya, yb = arc(BAND[0]), arc(BAND[1])
    wire = np.zeros(S.shape)
    rails = (1 - F.sstep(0.011, 0.015, np.abs(Y - ya))) + (1 - F.sstep(0.011, 0.015, np.abs(Y - yb)))
    rails = np.clip(rails, 0, 1)
    band_rows = np.unique(np.where((Y > ya - 0.03) & (Y < yb + 0.03))[0])
    r0, r1 = band_rows.min(), band_rows.max() + 1
    mid = (ya + yb) / 2
    hb = (yb - ya) / 2 - 0.02
    count = 22
    circ = TAU * float(rad(np.interp(mid, LT, VT)))
    p = circ / count
    x = ((S[r0:r1] * count) % 1.0) * p
    y = Y[r0:r1] - mid
    rho0 = hb * 0.82
    cxs = 0.56 * p
    pts = [(0.0, -rho0 * 0.86), (cxs * 0.5, -rho0 * 0.95), (cxs, -rho0)]
    for i in range(1, 41):
        th = -math.pi / 2 + 2.25 * math.pi * i / 40
        r = rho0 * (1 - 0.8 * i / 40)
        pts.append((cxs + r * math.cos(th), r * math.sin(th)))
    d, along = F.seg_dist(x, y, pts)
    d2, _ = F.seg_dist(x - p, y, pts[:3])          # the next cell's lead-in reaching back
    d = np.minimum(d, d2)
    scroll = 1 - F.sstep(0.005, 0.0085, d)
    bead = 1 - F.sstep(0.008, 0.011, np.hypot(x - 0.16 * p, y - rho0 * 0.55))
    wire[r0:r1] = np.maximum(scroll, bead)
    wire = np.clip(np.maximum(wire, rails), 0, 1)
    col = F.mix(col, silver, wire)
    height = height + 0.011 * F.blur(rails, 1) + 0.008 * F.blur(wire * (1 - rails), 1)
    rough = np.where(wire > 0.5, 0.26, rough)
    metal = np.maximum(metal, wire * 1.0)

    # the eclipse's light on the lacquer round it: a soft glow off the corona, and long thin streamers
    x, y, front = f.plane(ECL["s"], ECL["v"])
    face = front > 0.3
    r = np.hypot(x, y)
    ang = np.arctan2(y, x)
    edge = ECL["R"] + flare(ang)
    out = np.clip(r - edge, 0, None)
    glow = np.array(srgb(120, 210, 255)) ** (1 / 2.2)
    white = np.array((0.9, 0.97, 1.0))
    light = np.exp(-out / 0.045) * 0.55 + np.exp(-out / 0.16) * 0.18
    wisp = np.zeros(S.shape)
    for deg, length, width in STREAMERS:
        d = np.abs((ang - math.radians(deg) + np.pi) % TAU - np.pi)
        spread = math.radians(width) * np.clip(ECL["R"] / np.maximum(r, 1e-3), 0.35, 1.0)
        along = np.clip(out / length, 0, 1)
        wisp = np.maximum(wisp, np.exp(-(d / spread) ** 2) * (1 - along) ** 1.6 * (out > 0))
    light = np.clip(light + wisp * 0.75, 0, 1) * face * (r > ECL["R"])
    col = F.mix(col, glow, np.clip(light, 0, 0.85))
    col = F.mix(col, white, np.clip(wisp * face * (r > ECL["R"]) * (1 - np.clip(out / 0.12, 0, 1)) * 0.4, 0, 1))
    under = (r < ECL["R"] * 1.02) * face
    col = F.mix(col, np.array((0.02, 0.02, 0.05)), under)

    # frost round the ice where it broke through, and short radial cracks
    for name, s0, v0, crystals in CLUSTERS:
        x, y, front = f.plane(s0, v0)
        r = np.hypot(x, y)
        nz = F.fbm(P, 18.0, 3, seed=hash(name) % 997)
        frost = np.clip(1 - F.sstep(0.08, 0.2 + 0.05 * nz, r), 0, 1) * (front > 0.3)
        speck = F.sstep(0.1, 0.4, F.fbm(P, 40.0, 2, seed=hash(name) % 991 + 1))
        col = F.mix(col, np.array((0.62, 0.78, 0.92)), frost * (0.35 + 0.4 * speck))
        rough = rough + frost * 0.2
        ang = np.arctan2(y, x)
        rays = (np.abs(np.sin(ang * 5 + nz * 1.5)) < 0.06) * (r > 0.08) * (r < 0.26) * (front > 0.3)
        col = F.mix(col, np.array((0.8, 0.92, 1.0)), rays * 0.7 * (1 - F.sstep(0.12, 0.26, r)))
        height = height - 0.002 * rays

    # hairline cracks from the crown's ice, moonlight showing through
    name, s0, v0, _ = CLUSTERS[2]
    x, y, front = f.plane(s0, v0)
    core = np.zeros(S.shape)
    halo = np.zeros(S.shape)
    box = (np.abs(x) < 0.65) & (np.abs(y) < 0.65) & (front > 0.2)
    for pts, w in crack_lines():
        d, along = F.seg_dist(x[box], y[box], pts)
        c = (1 - F.sstep(0.0, 0.0045 * w * (1.2 - along) + 0.0012, d))
        h = np.exp(-d / 0.02) * (1 - along) ** 1.3 * w
        core[box] = np.maximum(core[box], c)
        halo[box] = np.maximum(halo[box], h)
    col = F.mix(col, glow * 0.8, np.clip(halo * 0.45, 0, 1))
    col = F.mix(col, np.array((0.86, 0.96, 1.0)), core)
    height = height - 0.0025 * core

    # small raised stars
    starm = np.zeros(S.shape)
    starh = np.zeros(S.shape)
    for s0, v0, size, roll in star_sites():
        x, y, front = f.plane(s0, v0, roll=roll)
        box = (np.abs(x) < size * 1.3) & (np.abs(y) < size * 1.3) & (front > 0.5)
        q = np.sqrt(np.abs(x[box]) / size) + np.sqrt(np.abs(y[box]) / size)
        m = 1 - F.sstep(0.85, 1.0, q)
        starm[box] = np.maximum(starm[box], m)
        starh[box] = np.maximum(starh[box], np.clip(1 - q, 0, 1))
    col = F.mix(col, np.array((0.9, 0.93, 1.0)), starm)
    height = height + 0.007 * starh
    rough = np.where(starm > 0.5, 0.2, rough)
    metal = np.maximum(metal, starm * 0.6)
    return f, np.clip(col, 0, 1), np.clip(rough, 0, 1), np.clip(metal, 0, 1), height


# ---------- the pieces ----------
def pieces(coll):
    """Ribbons, ice and the eclipse's disc (baked), and the corona (Neon)."""
    rib_mat = mat_ribbon()
    ice_mat = mat_ice()
    ecl_mat = mat_eclipse()
    out = []
    for name, pts, wmax, hmax, lift_max, seed in RIBBONS:
        hi = Hm.Hi()
        path, length = ribbon_path(pts, 170)
        brush(hi, path, lambda t, w=wmax: brush_width(t, w), lambda t, h=hmax: brush_height(t, h), lambda t, lm=lift_max: lm * F.sstep(0.8, 1.0, t) ** 1.5,
              lambda t, sd=seed: brush_locks(t, sd))
        o = F.fix_normals(hi.object("EX_Ribbon" + name, coll, [rib_mat]))
        o["w"] = 1.0
        out.append(o)
    hi = Hm.Hi()
    for name, s0, v0, crystals in CLUSTERS:
        ice_cluster(hi, s0, v0, crystals, lift=0.45 if v0 < 0.5 else 0.4)
    ice = hi.object("EX_Ice", coll, [ice_mat], smooth=False, weld=0)
    bm = bmesh.new()
    bm.from_mesh(ice.data)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])     # the crystals' hexagonal feet
    bm.to_mesh(ice.data)
    bm.free()
    F.fix_normals(ice)
    ice["keep"] = True
    out.append(ice)
    hi = Hm.Hi()
    eclipse_disc(hi)
    disc = F.fix_normals(hi.object("EX_EclipseDisc", coll, [ecl_mat]))
    disc["w"] = 1.4
    out.append(disc)
    hi = Hm.Hi()
    corona(hi)
    glow = F.fix_normals(hi.object("EX_Corona", coll, [K.glow_material(CORONA)], smooth=False, weld=1e-6))
    return out, glow


# ---------- assembling (egg_forge.assemble, with the shell's seam welded so the body is watertight) ----------
def weld(obj, dist=1e-6):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def assemble(coll, shell_mat, height, parts, glow, budget=5600, shell_frac=0.64, low_nu=72, low_nv=44):
    hi_shell = F.shell_mesh(EGG + "_ShellHi", coll, 1024, 640, height, shell_mat)
    low_h = F.blur(height, height.shape[1] / 128)
    low_shell = F.shell_mesh(EGG + "_ShellLow", coll, low_nu, low_nv, low_h, None, (0.004, 0.004, 0.996, shell_frac - 0.006))
    weld(low_shell)
    kept = sum(F.tris(o) for o in parts if o.get("keep"))
    total = sum(F.tris(o) * o.get("w", 1.0) for o in parts if not o.get("keep")) or 1
    k = (budget - kept) / total
    lp = [F.decimated(o, 1.0 if o.get("keep") else min(1.0, k * o.get("w", 1.0)), coll) for o in parts]
    low_att = K.join(lp, EGG + "_AttLow", coll)
    for c in lp:
        me = c.data
        bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.meshes.remove(me)
    for p in low_att.data.polygons:
        p.use_smooth = True
    F.fix_normals(low_att)
    F.harden(low_att, 50)
    F.unwrap_into(low_att, (0.004, shell_frac + 0.006, 0.996, 0.996), angle=50)
    pairs = [(low_shell, [hi_shell], 0.08, 0.2), (low_att, list(parts), 0.05, 0.16)]
    mat, log = F.bake(EGG, pairs, [glow], samples=16, ao_floor=0.55, ao_reach=0.3)
    # the Neon piece: its own clean UVs (Studio ignores them, but every mesh should have them, inside 0..1)
    F.unwrap_into(glow, (0.0, 0.0, 1.0, 1.0), angle=60)
    parts_out, tris = F.export(EGG, [low_shell, low_att], {CORONA: [glow]}, coll)
    return parts_out, tris, log, hi_shell


def strip_fbx_paths(path):
    """The FBX keeps the absolute paths of its textures: change the user folder to a neutral one of the same
    length (the binary layout is unchanged), as the other assets were."""
    data = open(path, "rb").read()
    home = os.path.expanduser("~").encode()
    if home.startswith(b"/Users/") and len(home) > len(b"/Users/"):
        neutral = b"/Users/" + b"u" * (len(home) - len(b"/Users/"))
        if len(home) - len(b"/Users/") >= 4:
            neutral = b"/Users/user" + b"_" * (len(home) - len(b"/Users/user"))
        data = data.replace(home + b"/", neutral + b"/")
    open(path, "wb").write(data)
    return data.count(home + b"/")


# ---------- review ----------
VIEWS = {"front": (0, 10), "three": (38, 14), "back": (180, 10), "top": (20, 62), "left": (-90, 8), "right": (90, 8), "icon": (22, 10)}


def lab(bg=0.22):
    scene = bpy.context.scene
    world = bpy.data.worlds.get("EX_LabWorld") or bpy.data.worlds.new("EX_LabWorld")
    world.use_nodes = True
    bgn = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bgn.inputs[0].default_value = (bg, bg, bg * 1.03, 1)
    bgn.inputs[1].default_value = 1.0
    scene.world = world
    for name, loc, energy, color in (("Key", (4, -5, 6), 700, (1.0, 0.97, 0.92)), ("Rim", (-4, 6, 5), 500, (0.9, 0.95, 1.0)), ("Fill", (-5, -3, 1.5), 160, (0.85, 0.9, 1.0))):
        o = bpy.data.objects.get("EX_Lab" + name)
        if o is None:
            light = bpy.data.lights.new("EX_Lab" + name, "AREA")
            light.energy, light.color, light.size = energy, color, 4
            o = bpy.data.objects.new("EX_Lab" + name, light)
            scene.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (V((0, 0, 1.3)) - V(loc)).to_track_quat("-Z", "Y").to_euler()
    cam = bpy.data.objects.get("EX_LabCam")
    if cam is None:
        cd = bpy.data.cameras.new("EX_LabCam")
        cam = bpy.data.objects.new("EX_LabCam", cd)
        scene.collection.objects.link(cam)
    cam.data.lens = 70
    scene.camera = cam
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU"
    scene.cycles.use_denoising = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_percentage = 100
    return scene


def load_px(path):
    im = bpy.data.images.load(path, check_existing=False)
    w, h = im.size
    px = np.zeros(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(px)
    bpy.data.images.remove(im)
    return px.reshape(h, w, 4)


def save_px(arr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    h, w = arr.shape[:2]
    img = bpy.data.images.new("EX_Out", w, h, alpha=True)
    img.pixels.foreach_set(np.ascontiguousarray(arr, dtype=np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    return path


def shots(views, size=420, samples=48, centre=(0, 0, 1.4), distance=7.0, transparent=False, tag="shot"):
    """Renders views of whatever is visible; returns their pixels (bottom row first, Blender's order)."""
    scene = lab()
    scene.cycles.samples = samples
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.film_transparent = transparent
    cam = scene.camera
    tiles = []
    tmp = os.path.join(WORK, "_%s.png" % tag)
    os.makedirs(WORK, exist_ok=True)
    for view in views:
        yaw, pitch = VIEWS[view] if isinstance(view, str) else view
        y, p = math.radians(yaw), math.radians(pitch)
        cam.location = V(centre) + V((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p))) * distance
        cam.rotation_euler = (V(centre) - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = tmp
        bpy.ops.render.render(write_still=True)
        tiles.append(load_px(tmp))
    os.remove(tmp)
    return tiles


def row(tiles):
    return np.concatenate(tiles, 1)


def emissive(objs, strength=3.0):
    for o in objs:
        for m in o.data.materials:
            if m and m.get("glow"):
                em = next(n for n in m.node_tree.nodes if n.type == "EMISSION")
                em.inputs["Strength"].default_value = strength


def clay_override(on):
    vl = bpy.context.view_layer
    if not on:
        vl.material_override = None
        return
    m = bpy.data.materials.get("EX_Clay") or bpy.data.materials.new("EX_Clay")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.5, 0.5, 0.52, 1)
    b.inputs["Roughness"].default_value = 0.5
    vl.material_override = m


def clay_with_normals(body, glows):
    """The game mesh in grey clay, wearing only its baked normal map: the relief exactly as the game gets it."""
    normal = next(n.image for n in body.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image and n.image.name.endswith("_Normal"))
    m = bpy.data.materials.new("EX_ClayNormal")
    m.use_nodes = True
    t = m.node_tree
    b = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.5, 0.5, 0.52, 1)
    b.inputs["Roughness"].default_value = 0.5
    tex = t.nodes.new("ShaderNodeTexImage")
    tex.image = normal
    nm = t.nodes.new("ShaderNodeNormalMap")
    t.links.new(tex.outputs["Color"], nm.inputs["Color"])
    t.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    g = bpy.data.materials.new("EX_ClayGlow")
    g.use_nodes = True
    gb = next(n for n in g.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    gb.inputs["Base Color"].default_value = (0.75, 0.75, 0.78, 1)
    saved = [(o, list(o.data.materials)) for o in [body] + list(glows)]
    body.data.materials.clear()
    body.data.materials.append(m)
    for o in glows:
        o.data.materials.clear()
        o.data.materials.append(g)

    def restore():
        for o, mats in saved:
            o.data.materials.clear()
            for x in mats:
                o.data.materials.append(x)
    return restore


# ---------- stages ----------
def fresh():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.node_groups, bpy.data.lights, bpy.data.cameras):
        for x in list(block):
            if getattr(x, "type", None) in ("RENDER_RESULT", "COMPOSITING"):
                continue
            block.remove(x)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    bpy.data.orphans_purge(do_recursive=True)


def stage_clay(with_paint=False):
    """The high-detail model: four views in clay (and in its shaders when with_paint)."""
    fresh()
    coll = W.collection(EGG + "Hi")
    f, col, rough, metal, height = paint()
    mat = F.shell_material("EX_Lacquer", col, rough, metal) if with_paint else None
    F.shell_mesh("EX_Shell", coll, 512, 320, height, mat)
    parts, glow = pieces(coll)
    emissive([glow])
    print("TRIS", {o.name: F.tris(o) for o in parts + [glow]}, flush=True)
    clay_override(True)
    a = row(shots(["front", "three", "back", "top"], 420, 32, tag="clay"))
    b = row(shots(["left", "right", (60, -8), (140, 30)], 420, 32, tag="clay2"))
    clay_override(False)
    sheet = np.concatenate([b, a], 0)
    if with_paint:
        c = row(shots(["front", "three", "back", "top"], 420, 48, tag="look"))
        d = row(shots(["left", "right", (60, -8), (140, 30)], 420, 48, tag="look2"))
        sheet = np.concatenate([d, c, sheet], 0)
    out = save_px(sheet, os.path.join(WORK, "hi_%s.png" % ("look" if with_paint else "clay")))
    print("SHEET", out, flush=True)


def stage_build():
    fresh()
    os.makedirs(WORK, exist_ok=True)
    coll = W.collection(EGG + "Hi")
    f, col, rough, metal, height = paint()
    mat = F.shell_material("EX_Lacquer", col, rough, metal)
    parts, glow = pieces(coll)
    import time
    t0 = time.time()
    out_parts, tris, log, hi_shell = assemble(coll, mat, height, parts, glow)
    print("BAKED", round(time.time() - t0, 1), "s", log, "TRIS", tris, {p.name: F.tris(p) for p in out_parts}, flush=True)
    fbx = os.path.join(F.OUT, EGG + ".fbx")
    print("FBX", fbx, "home paths left:", strip_fbx_paths(fbx), flush=True)
    # keep only the game parts for the reviews and the .blend
    keep = set(p.name for p in out_parts)
    for o in list(coll.objects):
        if o.name not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.orphans_purge(do_recursive=True)
    body = next(p for p in out_parts if p.name.endswith("_Body"))
    glows = [p for p in out_parts if "_Glow_" in p.name]
    emissive(glows)
    paint_tiles = shots(["front", "three", "back", "top"], 400, 64, tag="paint")
    restore = clay_with_normals(body, glows)
    clay_tiles = shots(["front", "three", "back", "top"], 400, 48, tag="clayn")
    restore()
    save_px(row(clay_tiles), os.path.join(WORK, "game_clay.png"))
    save_px(row(paint_tiles), os.path.join(WORK, "game_paint.png"))
    print("BLEND", save_blend(out_parts), flush=True)


def save_blend(parts):
    """The game parts with their baked maps packed, and no path from this machine in the file."""
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene
    scene.render.filepath = "//" + "_" * 1020
    scene.render.filepath = "//"
    for o in list(bpy.data.objects):
        if o not in parts:
            bpy.data.objects.remove(o, do_unlink=True)
    for w in list(bpy.data.worlds):
        bpy.data.worlds.remove(w)
    bpy.data.orphans_purge(do_recursive=True)
    for img in bpy.data.images:
        if img.source != "FILE":
            continue
        if not img.packed_file:
            img.pack()
        raw = img.filepath_raw
        if raw and not raw.startswith("//"):
            rel = bpy.path.relpath(raw, start=os.path.dirname(BLEND))
            img.filepath_raw = "//" + "_" * 1000
            img.filepath_raw = rel
        for pf in img.packed_files:
            pf.filepath = img.filepath_raw
    # written from the scene alone: no window manager, so no operator's remembered file path comes along
    if os.path.exists(BLEND):
        os.remove(BLEND)
    bpy.data.libraries.write(BLEND, {scene}, path_remap="RELATIVE_ALL", compress=True)
    return BLEND


def import_fbx(path, offset=(0, 0, 0)):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        o.location = V(o.location) + V(offset)
    return new


def neon(objs, strength=3.0):
    """Imported glow pieces shown as light, the way Studio's Neon reads."""
    import re
    for o in objs:
        m = re.search(r"_Glow_([0-9a-fA-F]{6})", o.name)
        if not m:
            continue
        o.data.materials.clear()
        o.data.materials.append(K.glow_material(m.group(1)))
        emissive([o], strength)


def stage_verify():
    """Re-imports the FBX: parts, scale, UV sets, triangles, bounds, and the QA gate (profile roblox)."""
    fresh()
    objs = import_fbx(os.path.join(F.OUT, EGG + ".fbx"))
    report = {"parts": {}}
    lo, hi = V((1e9,) * 3), V((-1e9,) * 3)
    total = 0
    for o in objs:
        if o.type != "MESH":
            continue
        t = F.tris(o)
        total += t
        for c in o.bound_box:
            w = o.matrix_world @ V(c)
            lo = V(map(min, lo, w))
            hi = V(map(max, hi, w))
        report["parts"][o.name] = {"tris": t, "uv_sets": len(o.data.uv_layers), "scale": [round(x, 5) for x in o.scale],
                                   "rotation": [round(x, 5) for x in o.rotation_euler]}
    report["tris"] = total
    report["bounds"] = [[round(x, 3) for x in lo], [round(x, 3) for x in hi]]
    maps = {}
    for key in ("color", "normal", "roughness", "metalness"):
        p = os.path.join(F.OUT, "%s_%s.png" % (EGG, key))
        im = bpy.data.images.load(p, check_existing=False)
        maps[key] = list(im.size)
        bpy.data.images.remove(im)
    report["maps"] = maps
    qa_dir = os.path.expanduser("~/.claude/plugins/marketplaces/blender-agent-skills/skills/blender-asset-qa/scripts")
    sys.path.insert(0, qa_dir)
    import qa_check
    res = qa_check.run(objects=[o.name for o in objs if o.type == "MESH"], profile="roblox")
    report["qa"] = {k: res[k] for k in ("pass", "errors", "warnings", "ground_z")}
    report["qa_objects"] = res["objects"]
    data = open(os.path.join(F.OUT, EGG + ".fbx"), "rb").read()
    report["fbx_machine_paths"] = data.count(os.path.expanduser("~").encode() + b"/") + data.count(b"/private/tmp") + data.count(b"/tmp/")
    os.makedirs(WORK, exist_ok=True)
    json.dump(report, open(os.path.join(WORK, "verify.json"), "w"), indent=1, default=str)
    print("VERIFY", json.dumps({k: v for k, v in report.items() if k != "qa_objects"}, indent=1, default=str), flush=True)
    return report


def stage_icons():
    """The in-game icon (egg_icons, as every egg), the shop card, the line-up and the review sheet."""
    import egg_icons
    gpu()
    icon = egg_icons.render(EGG, os.path.join(REPO, "assets", "ui", "egg_icons"))
    big = egg_icons.render(EGG, WORK, size=1024)
    os.replace(big, os.path.join(WORK, "icon_1024.png"))
    card = store_card(os.path.join(WORK, "icon_1024.png"), os.path.join(REPO, "assets", "ui", "store", EGG + "_premium_512.png"))
    lineup = stage_lineup()
    sheet = review_sheet(icon, card, lineup)
    print("ICON", icon, "CARD", card, "SHEET", sheet, flush=True)


LINEUP = ("CelestialEgg", "HeavenlyThroneEgg", "VoidRiftEgg")


def stage_lineup():
    fresh()
    gpu()
    xs = (-4.8, -1.6, 1.6, 4.8)
    allo = []
    for egg, x in zip((EGG,) + LINEUP, xs):
        objs = import_fbx(os.path.join(F.OUT, egg + ".fbx"), (x, 0, 0))
        neon(objs)
        allo += objs
    scene = lab(0.2)
    scene.cycles.samples = 64
    scene.render.resolution_x, scene.render.resolution_y = 1600, 520
    scene.render.film_transparent = False
    cam = scene.camera
    cam.data.lens = 70
    yaw, pitch = math.radians(14), math.radians(9)
    centre = V((0, 0, 1.5))
    d = 23.0
    cam.location = centre + V((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch))) * d
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    for name, loc in (("Key", (8, -12, 10)), ("Rim", (-8, 12, 8)), ("Fill", (-12, -6, 3))):
        o = bpy.data.objects["EX_Lab" + name]
        o.location = loc
        o.data.size = 10
        o.data.energy *= 4
        o.rotation_euler = (centre - V(loc)).to_track_quat("-Z", "Y").to_euler()
    path = os.path.join(WORK, "lineup.png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


# ---------- 2D finishing (numpy, no Pillow in Blender) ----------
def box_blur(a, r, passes=3):
    r = max(1, int(r))
    out = a
    for _ in range(passes):
        for axis in (0, 1):
            pad = [(0, 0)] * out.ndim
            pad[axis] = (r + 1, r)
            c = np.cumsum(np.pad(out, pad, mode="edge"), axis=axis)
            hi = np.take(c, np.arange(2 * r + 1, c.shape[axis]), axis=axis)
            lo = np.take(c, np.arange(0, c.shape[axis] - 2 * r - 1), axis=axis)
            out = (hi - lo) / (2 * r + 1)
    return out


def dilate(a, r):
    out = a.copy()
    for axis in (0, 1):
        src = out.copy()
        for k in range(1, r + 1):
            out = np.maximum(out, np.roll(src, k, axis=axis))
            out = np.maximum(out, np.roll(src, -k, axis=axis))
    return out


def resize(arr, w, h):
    """Through Blender's own image scaling (premultiplied, so edges don't darken)."""
    H_, W_ = arr.shape[:2]
    pre = arr.copy()
    pre[..., :3] *= pre[..., 3:4]
    img = bpy.data.images.new("EX_Scale", W_, H_, alpha=True, float_buffer=True)
    img.pixels.foreach_set(np.ascontiguousarray(pre, dtype=np.float32).ravel())
    img.scale(w, h)
    px = np.zeros(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    out = px.reshape(h, w, 4)
    a = np.clip(out[..., 3:4], 1e-6, None)
    out[..., :3] = np.where(out[..., 3:4] > 1e-5, out[..., :3] / a, 0)
    return np.clip(out, 0, 1)


def over(dst, src, x0=0, y0=0):
    """src over dst at (x0, y0) from the top-left (arrays stored top row first)."""
    h, w = src.shape[:2]
    d = dst[y0:y0 + h, x0:x0 + w]
    a = src[..., 3:4]
    out_a = a + d[..., 3:4] * (1 - a)
    rgb = (src[..., :3] * a + d[..., :3] * d[..., 3:4] * (1 - a)) / np.clip(out_a, 1e-6, None)
    dst[y0:y0 + h, x0:x0 + w, :3] = np.where(out_a > 1e-6, rgb, 0)
    dst[y0:y0 + h, x0:x0 + w, 3:4] = out_a
    return dst


def sparkle(canvas, cx, cy, r, top=(255, 255, 255), bottom=(196, 238, 255)):
    """A four-pointed sparkle (concave sides), white fading to pale cyan, onto an sRGB top-row-first canvas."""
    h, w = canvas.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    q = np.sqrt(np.abs(xx - cx) / r) + np.sqrt(np.abs(yy - cy) / r)
    a = np.clip((1.0 - q) * r / 2.0, 0, 1)
    t = np.clip((yy - (cy - r)) / (2 * r), 0, 1)[..., None]
    col = (np.array(top) * (1 - t) + np.array(bottom) * t) / 255
    layer = np.concatenate([col, a[..., None]], -1)
    return over(canvas, layer)


def store_card(render_path, out_path):
    """The shop card, in the Store art's style (tools/ui/draw_store_icons.py): the picture with a dark
    outline round it and a few sparkles, on a deep night-blue plate with a gold rim, the corners clear.
    No padlock. 512 x 512."""
    S = 1024
    pic = load_px(render_path)[::-1].astype(np.float64)      # top row first
    # (8-bit PNG pixels come in as their stored sRGB values, and go out the same way)
    pic = sparkle(pic, 812, 190, 82)
    pic = sparkle(pic, 196, 330, 52)
    pic = sparkle(pic, 842, 700, 44)
    # a dark line all round (MaxFilter 13 at 256 px, as the Store art)
    a = pic[..., 3]
    small = resize(np.dstack([np.ones((S, S, 3)), a[..., None]]), 256, 256)[..., 3]
    grown = dilate(small, 6)
    grown = box_blur(grown, 1, 1)
    grown = resize(np.dstack([np.ones((256, 256, 3)), grown[..., None]]), S, S)[..., 3]
    base = np.zeros((S, S, 4))
    base[..., :3] = np.array((12, 18, 44)) / 255
    base[..., 3] = grown
    base = over(base, pic)
    # the plate
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float64)
    r = np.hypot(xx - S / 2 + 0.5, yy - S / 2 + 0.5)
    plate = np.zeros((S, S, 4))
    rim = np.clip(S / 2 - 16 - r + 0.5, 0, 1)
    plate[..., :3] = np.array((226, 182, 92)) / 255
    plate[..., 3] = rim
    inner = np.clip(S / 2 - 44 - r + 0.5, 0, 1)
    disc = np.zeros((S, S, 4))
    disc[..., :3] = np.array((24, 25, 68)) / 255
    disc[..., 3] = inner
    plate = over(plate, disc)
    glow = box_blur((r < S / 2 - 210) * (190 / 255), 44)        # a little stronger than the pass cards': the egg is dark
    light = np.zeros((S, S, 4))
    light[..., :3] = np.array((96, 112, 206)) / 255
    light[..., 3] = glow * inner
    plate = over(plate, light)
    k = int(S * 0.74)
    picture = resize(base, k, k)
    plate = over(plate, picture, int(S * 0.13), int(S * 0.13))
    card = resize(plate, 512, 512)
    save_px(card[::-1], out_path)
    return out_path


def review_sheet(icon_path, card_path, lineup_path):
    """renders/eggs/ExclusiveEgg_review.png: clay (with the baked normals) and paint from the front, 3/4,
    back and top; the line-up beside three other eggs at the same scale; the icon at 64 and 128 px on dark
    and light, and the shop card."""
    clay = load_px(os.path.join(WORK, "game_clay.png"))[::-1]
    paint_ = load_px(os.path.join(WORK, "game_paint.png"))[::-1]
    lineup = load_px(lineup_path)[::-1]
    icon = load_px(icon_path)[::-1]
    card = load_px(card_path)[::-1]
    Wd = 1600
    strip = np.zeros((300, Wd, 4))
    strip[..., :3] = 0.08
    strip[..., 3] = 1
    strip[:, 800:, :3] = 0.62
    for size, x0, bgx in ((128, 40, 0), (64, 210, 0), (128, 840, 1), (64, 1010, 1)):
        ic = resize(icon, size, size)
        strip = over(strip, ic, x0, 150 - size // 2)
    c = resize(card, 256, 256)
    strip = over(strip, c, 330, 22)
    strip = over(strip, resize(card, 128, 128), 620, 86)
    strip = over(strip, resize(icon, 256, 256), 1130, 22)
    strip = over(strip, resize(card, 128, 128), 1420, 86)
    sheet = np.concatenate([clay, paint_, lineup, strip], 0)
    out = os.path.join(REPO, "renders", "eggs", EGG + "_review.png")
    save_px(sheet[::-1], out)
    return out


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["all"]
    stage = argv[0] if argv else "all"
    print("GPU", gpu(), flush=True)
    if stage == "clay":
        stage_clay(False)
    elif stage == "look":
        stage_clay(True)
    elif stage == "build":
        stage_build()
    elif stage == "verify":
        stage_verify()
    elif stage == "icons":
        stage_icons()
    elif stage == "all":
        stage_build()
        stage_icons()
        stage_verify()
    print("DONE", stage, flush=True)
