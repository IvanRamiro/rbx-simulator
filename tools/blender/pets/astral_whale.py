"""The Astral Whale (Mythical, Cosmic; Beginner Qi Egg): "It swims the gap between stars and sings too low for mortals to hear. Cultivators who sleep
near one wake with stronger Qi."

Recreated (November 10, 2026; the old model was a faceted blue block whale with crystal fins and star diamonds): the starsong humpback (the owner's
choice), in a design language of its own: a whale that is the twilight sky, and an instrument. A humpback calf, after the real animal's anatomy: a big
soft head with knobbly tubercles along the rostrum and chin, a deep lower jaw pleated from chin to navel, a full chest, a small dorsal fin on a hump and
the knuckles of its back running down to a tall, thin tail stock; long wing-like flippers (a third of its length, as a humpback's), knobbed along their
leading edge; wide flukes with a notch and a scalloped trailing edge. Its skin is the sky at dusk from the zenith down: night indigo on its back with a
few faint stars, dusk violet on its flanks, a band of rose at its horizon, pearl beneath. The grooves of its throat hold golden strings that light up as
it sings; the knobs along its flippers shine as small pale stars.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/astral_whale.py -- [clay|paint|rig|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. rig: through the bake and the rig, with the limbs' signs measured.
all: also the poses, the file and the FBX. Faces -Y, Z up, 1 unit = 1 metre. It swims in the air: its lowest point (a flipper tip) is about
z = 0.05. +X is its left. The maps go to assets/pets/BeginnerQiEgg/.

What touches what: head, body, hump, dorsal fin, knuckles and tail stock are one fused skin; each flipper is its own blade, its root buried in the
flank; the flukes are one blade, their root buried in the tail stock's end; the eyes sit in their sockets under their lids; the golden strings lie
in the throat grooves and the star knobs sit on the flippers' leading edges (glow pieces).
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector  # noqa: F401  (the game stage)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "AstralWhale"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "BeginnerQiEgg")

# ---------- colours: the sky at dusk, from the zenith down ----------
NIGHT, NIGHT_DEEP = rgb(54, 42, 112), rgb(30, 24, 70)        # (violet in it: the game's blue sky pushes cool colours to navy, measured on the Volt Fox)
DUSK = rgb(104, 82, 168)
ROSE = rgb(214, 150, 184)
HORIZON = rgb(250, 214, 170)
PEARL = rgb(236, 232, 244)
LASH = rgb(16, 14, 36)
STRING_HEX = "ffc45c"           # its golden strings (Neon: a saturated gold, a pale one blooms white)
STAR_HEX = "a9c8ff"             # the star knobs on its flippers
GLINT_HEX = "f4f6ff"

# ---------- the body: a lofted calf ----------
SPINE = catmull([V(0, -0.44, 0.276), V(0, -0.3, 0.29), V(0, -0.1, 0.3), V(0, 0.1, 0.306), V(0, 0.26, 0.31), V(0, 0.4, 0.312)], 16)
# half-width, height above the spine, depth below it; along the spine (0 at its rostrum, 1 at the end of its tail stock)
# (a calf: short and plump, its head big and soft; the first, longer body read as a torpedo, its rostrum tip a separate ball as a clown's nose)
# (its rostrum slopes down to a rounded tip, as a humpback's: rising fast, its front read as a blunt loaf, a sperm whale's)
BODY_W = ((0, 0.014), (0.03, 0.048), (0.08, 0.084), (0.15, 0.118), (0.24, 0.146), (0.35, 0.168), (0.48, 0.165), (0.62, 0.14), (0.75, 0.096), (0.88, 0.052),
          (0.97, 0.022), (1, 0.012))
BODY_HT = ((0, 0.01), (0.04, 0.028), (0.1, 0.052), (0.18, 0.078), (0.26, 0.102), (0.35, 0.13), (0.48, 0.142), (0.62, 0.13), (0.75, 0.106),
           (0.88, 0.078), (0.97, 0.042), (1, 0.02))
BODY_HB = ((0, 0.014), (0.04, 0.048), (0.1, 0.084), (0.18, 0.114), (0.26, 0.138), (0.35, 0.158), (0.48, 0.155), (0.62, 0.13), (0.75, 0.09),
           (0.88, 0.052), (0.97, 0.024), (1, 0.012))     # (its tail stock tapers to a point inside its flukes: blunt, it ended in a stub)
NAVEL_Y = 0.0                    # where its throat pleats end
EYE_R = 0.035
EYE_C = V(0.13, -0.222, 0.282)
EYE_AXIS = V(0.84, -0.5, 0.14).normalized()     # (a little forward: its face reads from the front three-quarter)
LID_UP, LID_LOW = (44.0, 118.0, 0.0024), (-44.0, -126.0, 0.002)
LID_TILT = 6.0
BLINK_U, BLINK_L = 66.0, 30.0    # (they add past the 88 degrees between the lids' edges: the lids meet)
IRIS, PUPIL = 0.88, 0.36
# its flippers (left): root in the flank, out, back and a little down: a third of its length
PEC_ROOT = V(0.12, -0.12, 0.212)
PEC_DIR = V(0.86, 0.34, -0.37).normalized()
PEC_LEN = 0.34
PEC_W = ((0, 0.066), (0.15, 0.08), (0.45, 0.074), (0.75, 0.058), (0.92, 0.036), (1, 0.012))     # chord, root to tip
PEC_KNOBS = 8                     # tubercles along its leading edge
# its flukes: from the tail stock's end, swept back, a notch in the middle
FLUKE_ROOT = V(0, 0.352, 0.311)
FLUKE_SPAN = 0.22
DORSAL = [V(0, 0.13, 0.415), V(0, 0.19, 0.438), V(0, 0.236, 0.472)]


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def spine_f(y):
    """Where along the spine a point at this y is (its spine runs straight down the y axis, near enough)."""
    return np.clip((np.asarray(y) - SPINE[0].y) / (SPINE[-1].y - SPINE[0].y), 0, 1)


# ---------- the skin ----------
def loft_body(m, rings=96, sides=56):
    bm = m.bm
    ring_verts = []
    for i in range(rings + 1):
        f = i / rings
        p = path_at(SPINE, f)
        w, ht, hb = prof(BODY_W, f), prof(BODY_HT, f), prof(BODY_HB, f)
        ring = []
        for k in range(sides):
            t = TAU * k / sides
            s, c = math.sin(t), math.cos(t)
            x = w * math.copysign(abs(c) ** 0.88, c)
            z = (ht if s > 0 else hb) * math.copysign(abs(s) ** 0.92, s)
            ring.append(bm.verts.new(p + V(x, 0, z)))
        ring_verts.append(ring)
    for i in range(rings):
        for k in range(sides):
            k2 = (k + 1) % sides
            bm.faces.new((ring_verts[i][k], ring_verts[i][k2], ring_verts[i + 1][k2], ring_verts[i + 1][k]))
    bm.faces.new(list(reversed(ring_verts[0])))
    bm.faces.new(ring_verts[-1])


def surface_points(tree, pts, dirn, sink):
    """Each point dropped onto the skin along dirn, then sunk a little under it."""
    out = []
    for p in pts:
        loc, nrm, _, _ = tree.ray_cast(p - dirn * 0.5, dirn, 1.0)
        if loc:
            out.append((loc - nrm * sink, nrm))
    return out


def build_skin():
    base = Mesh()
    loft_body(base)
    for side in (1, -1):
        base.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.007, (EYE_R * 1.1,) * 3, 28, 18)    # the socket
    base.ball(V(0, 0.16, 0.405), (0.032, 0.07, 0.03), 28, 18)                  # the hump its dorsal fin sits on
    base.tube(catmull(DORSAL, 8), lambda f: 0.034 * (1 - f) ** 0.9 + 0.007, sides=20, flat=0.45)     # the dorsal fin, thin sideways (at 0.32 its tip folded in the game mesh)
    o = base.finish(N + "BaseHi", HI)
    tree = tree_of(o)
    bumps = Mesh()
    # tubercles: rows along the top of its rostrum, a cluster on its chin
    top = [V(x, y, 0.6) for y in np.arange(-0.415, -0.28, 0.036) for x in (-0.07, -0.035, 0.0, 0.035, 0.07) if not (x == 0 and y > -0.32)]
    for p, nrm in surface_points(tree, top, V(0, 0, -1), 0.004):
        bumps.ball(p, (0.0085, 0.0085, 0.0085), 14, 9)
    chin = [V(x, y, -0.2) for y in (-0.41, -0.385, -0.36) for x in (-0.03, 0.0, 0.03)]
    for p, nrm in surface_points(tree, chin, V(0, 0, 1), 0.004):
        bumps.ball(p, (0.008, 0.008, 0.008), 14, 9)
    # the splash guard: a low ridge in front of its blowholes (a ball set in the loft by hand remeshed to a crater ring)
    for p, nrm in surface_points(tree, [V(0, -0.262, 0.7)], V(0, 0, -1), 0.007):
        bumps.ball(p, (0.02, 0.03, 0.012), 24, 14)
    # the knuckles of its back, from its dorsal fin to its tail stock
    back = [V(0, y, 0.7) for y in (0.27, 0.3, 0.33, 0.36)]
    for p, nrm in surface_points(tree, back, V(0, 0, -1), 0.005):
        bumps.ball(p, (0.012, 0.012, 0.009), 14, 9)
    b = bumps.finish(N + "BumpsHi", HI)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.from_mesh(b.data)
    bm.to_mesh(o.data)
    bm.free()
    bpy.data.objects.remove(b, do_unlink=True)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0032, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    o.name = N + "SkinHi"
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- the flippers ----------
def pec_frame(side):
    root, d = mir(PEC_ROOT, side), mir(PEC_DIR, side)
    c = V(0, 0, 1).cross(d).normalized()                  # across its chord, front to back
    if c.y < 0:
        c = -c
    up = d.cross(c).normalized()
    if up.z < 0:
        up = -up
    return root, d, c, up


def knob_us():
    return [0.14 + 0.8 * k / (PEC_KNOBS - 1) for k in range(PEC_KNOBS)]


def pec_edge(side, u):
    """Its leading edge at u: scalloped, a knob at each tubercle (a humpback's flipper, from the front)."""
    root, d, c, up = pec_frame(side)
    w = prof(PEC_W, u)
    bump = sum(0.0065 * math.exp(-((u - k) / 0.034) ** 2) for k in knob_us()) * (1 - 0.4 * u)
    bow = 0.022 * math.sin(math.pi * u)                    # its span bows back a little, as a wing
    return root + d * (u * PEC_LEN) - c * (w * 0.32 + bump - bow) + V(0, 0, -0.03 * u * u)


def pec_point(side):
    root, d, c, up = pec_frame(side)

    def point(u, v):
        w = prof(PEC_W, u)
        le = pec_edge(side, u)
        te = root + d * (u * PEC_LEN) + c * (w * 0.68 + 0.022 * math.sin(math.pi * u)) + V(0, 0, -0.03 * u * u)
        p = le.lerp(te, v)
        return tuple(p + up * (0.006 * math.sin(math.pi * v) * (1 - u)))      # a gentle camber
    return point


def pec_thick(u, v):
    return (0.024 * (1 - u) ** 0.8 + 0.006) * (0.22 + 0.78 * min(1.0, 2.6 * math.sqrt(max(v, 0.0)) * (1 - v)))


def build_pec(side, name, coll, low=False):
    m = Mesh()
    nu, nv = (36, 8) if low else (90, 24)          # (the game blade keeps four segments a knob: its scallops survive)
    m.sheet(pec_point(side), pec_thick, nu, nv)
    return m.finish(name, coll)


# ---------- the flukes ----------
def fluke_point():
    """One blade from tip to tip (two halves met face to face down its middle: hidden back-to-back faces and a crease). u: 0 at its right tip, 1 at
    its left; v: 0 at its leading edge, 1 at its trailing edge."""
    def point(uu, v):
        s = uu * 2 - 1
        u = abs(s)
        x = FLUKE_SPAN * s
        le_y = FLUKE_ROOT.y + 0.125 * u ** 1.5
        chord = (0.062 + 0.042 * smooth(0.0, 0.25, u)) * (1 - u ** 2.3) + 0.004
        chord += 0.0045 * math.sin(u * math.pi * 9) * (u > 0.08) * (1 - u)            # its scalloped trailing edge
        y = le_y + chord * v
        z = FLUKE_ROOT.z + 0.012 * u * u
        return (x, y, z)
    return point


def fluke_thick(uu, v):
    u = abs(uu * 2 - 1)
    return (0.022 * (1 - u) + 0.005) * (0.22 + 0.78 * min(1.0, 2.6 * math.sqrt(max(v, 0.0)) * (1 - v)))


def build_flukes(name, coll, low=False):
    m = Mesh()
    nu, nv = (60, 7) if low else (160, 22)          # (enough along its span for the scallops of its trailing edge)
    m.sheet(fluke_point(), fluke_thick, nu, nv)
    return m.finish(name, coll)


# ---------- its glow pieces ----------
def string_paths(tree):
    """Its golden strings: the pleats of its throat, from its chin back to its navel, fanning out (a humpback's ventral grooves)."""
    paths = []
    for k in range(-5, 6):
        x_end = k * 0.024
        pts = []
        for s in np.linspace(0.0, 1.0, 26):
            y = -0.395 + (NAVEL_Y + 0.395) * s
            x = x_end * (0.25 + 0.75 * smooth(0.0, 0.55, s))
            hit = surface_points(tree, [V(x, y, -0.3)], V(0, 0, 1), -0.0012)
            if hit:
                pts.append(hit[0][0])
        if len(pts) > 4:
            paths.append((k, pts))
    return paths


def build_strings(tree, name_a, name_b, coll, low=False):
    a, b = Mesh(), Mesh()
    for k, pts in string_paths(tree):
        (a if k % 2 == 0 else b).tube(pts, lambda f: 0.0024 * (1 - 0.5 * f) + 0.0008, sides=5 if low else 8)
    return a.finish(name_a, coll), b.finish(name_b, coll)


def build_stars(name, coll, low=False):
    m = Mesh()
    for side in (1, -1):
        root, d, c, up = pec_frame(side)
        for k, u in enumerate(knob_us()):
            r = 0.0078 * (1 - 0.35 * u)
            m.ball(pec_edge(side, u) + c * 0.003, (r, r, r * 0.9), 10 if low else 18, 7 if low else 12)
    return m.finish(name, coll)


# ---------- paint: the sky at dusk ----------
SPINE_Y = np.array([p.y for p in SPINE])
SPINE_Z = np.array([p.z for p in SPINE])
MOUTH_Y = (-0.437, -0.238)       # its mouth runs from the tip of its rostrum to just under its eye


def mouth_line(Pv, e):
    """Its mouth: a gentle line along its jaw, held at a height on its body (points set by hand missed the skin), arching up toward its eye."""
    y = Pv[:, 1]
    em = -0.22 + 0.2 * smooth(-0.32, MOUTH_Y[1], y)
    inside = smooth(MOUTH_Y[0] - 0.004, MOUTH_Y[0] + 0.01, y) * smooth(MOUTH_Y[1] + 0.004, MOUTH_Y[1] - 0.008, y)
    return (1 - smooth(0.022, 0.05, np.abs(e - em))) * inside      # (thinner, it broke into dashes at the skin's vertex spacing)
BLOWHOLES = (V(0.012, -0.236, 0.0), V(-0.012, -0.236, 0.0))


def elevation(P):
    """Per point: how far up the body it is: -1 under its belly, 0 at its widest, 1 along its back."""
    f = spine_f(P[:, 1])
    cz = np.interp(P[:, 1], SPINE_Y, SPINE_Z)
    ht = np.interp(f, [k[0] for k in BODY_HT], [k[1] for k in BODY_HT])
    hb = np.interp(f, [k[0] for k in BODY_HB], [k[1] for k in BODY_HB])
    dz = P[:, 2] - cz
    return np.clip(np.where(dz > 0, dz / np.maximum(ht, 1e-3), dz / np.maximum(hb, 1e-3)), -1.2, 1.2)


def sky(e, specks):
    """The sky at dusk from the zenith down, by elevation: night, dusk violet, a band of rose, a thin gold horizon, pearl."""
    col = mix(np.broadcast_to(PEARL, (len(e), 3)), HORIZON, smooth(-0.62, -0.5, e) * (1 - smooth(-0.46, -0.4, e)) * 0.85)
    col = mix(col, ROSE, smooth(-0.5, -0.36, e))
    col = mix(col, DUSK, smooth(-0.34, -0.08, e))
    col = mix(col, NIGHT, smooth(0.12, 0.5, e))         # (dusk given its flanks: night from its widest up read as all night)
    col = mix(col, NIGHT_DEEP, smooth(0.45, 0.95, e) * 0.7)
    # a few faint stars across the night of its back: small, sparse, never lines
    col = mix(col, mix(PEARL, HORIZON, 0.25), specks * smooth(0.15, 0.45, e))
    return col


def star_specks(P, density, size, seed):
    """Sparse soft points scattered over the surface: 0..1."""
    q = P / size
    i = np.floor(q).astype(np.int64)
    out = np.zeros(len(P))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = i + np.array((dx, dy, dz))
                keep = hash01(c[:, 0], c[:, 1], c[:, 2], seed) < density
                jitter = np.stack([hash01(c[:, 0], c[:, 1], c[:, 2], seed + k) for k in (1, 2, 3)], 1)
                centre = (c + 0.2 + 0.6 * jitter) * size
                r = 0.18 * size * (0.5 + hash01(c[:, 0], c[:, 1], c[:, 2], seed + 4))
                d = np.linalg.norm(P - centre, axis=1)
                out = np.maximum(out, keep * (1 - smooth(r * 0.4, r, d)))
    return out


def paint_skin(o, tree):
    Pv = verts(o)
    Nn = normals(o)
    n = len(Pv)
    e = elevation(Pv)
    specks = star_specks(Pv, 0.12, 0.022, 7)
    col = sky(e, specks)
    soft = fbm(Pv, 30.0, 3, 11)
    col = col * (0.96 + 0.07 * soft)[:, None]
    # its throat grooves: the strings' lines pressed into the pearl of its throat, a soft violet shade in each
    groove = np.zeros(n)
    for k, pts in string_paths(tree):
        f, d = nearest_on(pts, Pv)
        groove = np.maximum(groove, (1 - smooth(0.0022, 0.0055, d)) * smooth(0.0, 0.08, f) * smooth(1.0, 0.85, f))
    col = mix(col, mix(PEARL, DUSK, 0.45), groove * 0.7)
    # its mouth: a gentle line from the tip of its rostrum, arching back toward its eye
    mouth = mouth_line(Pv, e)
    col = mix(col, NIGHT_DEEP * 0.7, mouth * 0.9)
    # its blowholes: two soft slits behind the splash guard
    blow = np.zeros(n)
    for b in BLOWHOLES:
        q = (Pv[:, 0] - b.x) / 0.0045, (Pv[:, 1] - b.y) / 0.014
        blow = np.maximum(blow, (1 - smooth(0.7, 1.0, np.hypot(*q))) * smooth(0.3, 0.7, Nn[:, 2]))
    col = mix(col, NIGHT_DEEP * 0.5, blow)
    relief = -0.0016 * groove - 0.0016 * mouth - 0.002 * blow + (soft - 0.5) * 0.0004      # (the mouth pressed in: shading carries it too)
    set_verts(o, Pv + Nn * relief[:, None])
    paint(o, np.clip(col, 0, 1), 0.5 + 0.06 * (e < -0.4) + 0.2 * mouth + 0.2 * blow, np.zeros(n))      # (at 0.36 the studio light left a hard white sheet on its back)


def paint_blade_sky(o, top_dir, root, tip_dir, length, under_pearl=1.0):
    """A fin: night at its root fading through dusk to rose and pearl at its tip on top; pearl beneath."""
    Pv = verts(o)
    Nn = normals(o)
    along = np.clip(((Pv - np.array(tuple(root))) @ np.array(tuple(tip_dir))) / length, 0, 1)
    topness = smooth(-0.3, 0.3, Nn @ np.array(tuple(top_dir)))
    top = mix(np.broadcast_to(NIGHT, (len(Pv), 3)), DUSK, smooth(0.15, 0.55, along))
    top = mix(top, ROSE, smooth(0.6, 0.85, along))
    top = mix(top, PEARL, smooth(0.85, 1.0, along))
    col = mix(np.broadcast_to(PEARL, (len(Pv), 3)) * 0.98, top, topness * under_pearl + (1 - under_pearl))
    return Pv, Nn, col


def paint_pec(o, side):
    root, d, c, up = pec_frame(side)
    Pv, Nn, col = paint_blade_sky(o, up, root, d, PEC_LEN)
    soft = fbm(Pv, 40.0, 3, 13 + side)
    paint(o, np.clip(col * (0.97 + 0.06 * soft)[:, None], 0, 1), np.full(len(Pv), 0.5), np.zeros(len(Pv)))


def paint_flukes(o):
    Pv, Nn, col = paint_blade_sky(o, V(0, 0, 1), FLUKE_ROOT, V(1, 0, 0), FLUKE_SPAN)
    # (both halves: its span runs out either way from the middle)
    along = np.clip(np.abs(Pv[:, 0]) / FLUKE_SPAN, 0, 1)
    topness = smooth(-0.3, 0.3, Nn[:, 2])
    top = mix(np.broadcast_to(NIGHT, (len(Pv), 3)), DUSK, smooth(0.2, 0.7, along))
    top = mix(top, ROSE, smooth(0.75, 1.0, along) * 0.6)
    # beneath, pearl edged with night along its scalloped trailing edge (a humpback's flukes are each marked their own way)
    trail = smooth(0.6, 1.0, (Pv[:, 1] - FLUKE_ROOT.y - 0.125 * along ** 1.5) / np.maximum(0.03, (0.062 + 0.042 * smooth(0.0, 0.25, along)) * (1 - along ** 2.3) + 0.004))
    under = mix(np.broadcast_to(PEARL, (len(Pv), 3)), DUSK, trail * 0.8)
    col = mix(under, top, topness)
    paint(o, np.clip(col, 0, 1), np.full(len(Pv), 0.5), np.zeros(len(Pv)))


def eye_paint(o, fr):
    """A dusk eye: deep indigo going to violet, ringed in horizon gold, a big soft pupil."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(18, 16, 40), (len(px), 3)).copy()
    iris = mix(rgb(44, 36, 120), rgb(140, 110, 220), smooth(0.35, 0.78, r / IRIS))
    iris = mix(iris, rgb(255, 196, 110), smooth(0.8, 0.95, r / IRIS))
    azi = np.arctan2(py, px)
    iris = iris * (0.9 + 0.1 * np.sin(azi * 22 + np.sin(azi * 4) * 1.4))[:, None]
    iris = mix(iris, iris * 0.6, smooth(-0.1, 0.9, py / IRIS) * 0.45)
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS, r))
    col = mix(col, rgb(10, 8, 26), 1 - smooth(PUPIL - 0.02, PUPIL + 0.02, r))
    paint(o, col, np.full(len(px), 0.05), np.zeros(len(px)))


def show_glows(glows):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 3.0
        o.data.materials.clear()
        o.data.materials.append(mat)
        o.visible_shadow = False


def build_hi(clay=False):
    pieces, data = {}, {}
    skin = build_skin()
    pieces["Skin"] = skin
    data["tree"] = tree_of(skin)
    for side, tag in ((1, "L"), (-1, "R")):
        pieces["Pec" + tag] = build_pec(side, N + "Pec" + tag + "Hi", HI)
    pieces["Flukes"] = build_flukes(N + "FlukesHi", HI)
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, NIGHT, LASH)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, DUSK, LASH, lower_share=0.7)
    sa, sb = build_strings(data["tree"], N + "StringsA_Glow_" + STRING_HEX, N + "StringsB_Glow_" + STRING_HEX, HI)
    if not clay:
        paint_skin(skin, data["tree"])
        for side, tag in ((1, "L"), (-1, "R")):
            paint_pec(pieces["Pec" + tag], side)
        paint_flukes(pieces["Flukes"])
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 24, 0.0074, 12), (20, -18, 0.0033, 8))),
             "StringsA": sa, "StringsB": sb, "Stars": build_stars(N + "Stars_Glow_" + STAR_HEX, HI)}
    return pieces, frames, glows, data




# ---------- the game mesh ----------
SKIN_QUADS = 3600
SCALES = {"EyeL": 2.2, "EyeR": 2.2, "LidUL": 1.3, "LidUR": 1.3, "LidLL": 1.3, "LidLR": 1.3, "PecL": 1.0, "PecR": 1.0, "Flukes": 1.0}


def fold_edges(bm, limit):
    return [e for e in bm.edges if len(e.link_faces) == 2 and e.link_faces[0].normal.angle(e.link_faces[1].normal) > limit]


def unfold(low, tree, limit=math.radians(100), rounds=12):
    """Where the re-topology left faces folded over one another (seen at its brow and its fin's base: the folds overlapped in the UV map), relax the
    vertices round each fold and set them back on the high skin, until none is left. Returns the folds found at first and at the end."""
    bm = bmesh.new()
    bm.from_mesh(low.data)
    first = len(fold_edges(bm, limit))
    for _ in range(rounds):
        bm.normal_update()
        bad = fold_edges(bm, limit)
        if not bad:
            break
        near = set()
        for e in bad:
            for v in e.verts:
                near.add(v)
                for e2 in v.link_edges:
                    near.add(e2.other_vert(v))
        near = list(near)
        bmesh.ops.smooth_vert(bm, verts=near, factor=0.6, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        for v in near:
            hit = tree.find_nearest(v.co)
            if hit[0] is not None:
                v.co = hit[0]
    bm.normal_update()
    last = len(fold_edges(bm, limit))
    bm.to_mesh(low.data)
    bm.free()
    low.data.update()
    return first, last


def build_low(pieces, frames):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    print("FOLDS in the skin, before and after", unfold(lows["Skin"], tree_of(pieces["Skin"])), flush=True)
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Pec" + tag] = build_pec(side, N + "Pec" + tag + "Low", GAME, low=True)
    lows["Flukes"] = build_flukes(N + "FlukesLow", GAME, low=True)
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 24, 16)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
SPINE_BONES = (("Head", V(0, -0.27, 0.29), "Chest"), ("Chest", V(0, -0.15, 0.295), "Body"), ("Body", V(0, -0.02, 0.3), "Root"),
               ("Spine1", V(0, 0.1, 0.306), "Body"), ("Spine2", V(0, 0.21, 0.31), "Spine1"), ("Tail", V(0, 0.29, 0.311), "Spine2"),
               ("Fluke", V(0, 0.35, 0.311), "Tail"))
CHAIN = [name for name, _, _ in SPINE_BONES]
CHAIN_Y = (-0.25, -0.13, -0.01, 0.12, 0.22, 0.31, 0.37)      # (y where each takes over, head to flukes)


def pec_names(tag):
    return ["Pec" + tag + "1", "Pec" + tag + "2"]


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None)]
    for name in ("Body", "Chest", "Head", "Spine1", "Spine2", "Tail", "Fluke"):
        at, parent = next((a, p) for n, a, p in SPINE_BONES if n == name)
        bones.append((name, at.copy(), parent))
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head")]
        root, d, c, up = pec_frame(side)
        one, two = pec_names(tag)
        bones += [(one, root.copy(), "Chest"), (two, root + d * (0.5 * PEC_LEN), one)]
    return armature(bones)


def pec_u(side, P_):
    root, d, c, up = pec_frame(side)
    return np.clip(((P_ - np.array(tuple(root))) @ np.array(tuple(d))) / PEC_LEN, 0, 1)


def body_weights(P_):
    out = []
    near = {}
    for side, tag in ((1, "L"), (-1, "R")):
        near[tag] = np.linalg.norm((P_ - np.array(tuple(mir(PEC_ROOT, side)))) / np.array((0.05, 0.06, 0.04)), axis=1)
    for i in range(len(P_)):
        w = chain_weight(CHAIN, CHAIN_Y, float(P_[i, 1]))
        # the flank round a flipper's root goes a little way with it, so the joint never opens as it flaps
        for side, tag in ((1, "L"), (-1, "R")):
            if P_[i, 0] * side > 0.05 and near[tag][i] < 1.0:
                w = blend(w, {pec_names(tag)[0]: 1.0}, 0.45 * float(smooth(1.0, 0.4, near[tag][i])))
        out.append(w)
    return out


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


def pec_weights(side, tag, P_):
    u = pec_u(side, P_)
    return [chain_weight(pec_names(tag), (0.3, 0.72), float(x)) for x in u]


def bind_all(lows, rig, glows):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    for side, tag in ((1, "L"), (-1, "R")):
        weigh(lows["Pec" + tag], pec_weights(side, tag, verts(lows["Pec" + tag])))
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    rigid(lows["Flukes"], "Fluke")
    for key in ("StringsA", "StringsB"):
        weigh(glows[key], body_weights(verts(glows[key])))
    P = verts(glows["Stars"])
    weigh(glows["Stars"], [pec_weights(1 if p[0] > 0 else -1, "L" if p[0] > 0 else "R", p[None, :])[0] for p in P])
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


def part_flush(body, gap=0.0015, rounds=6):
    """Where an eye or a lid slides in under the brow, the skin can run within a millimetre of it and parallel: it would shimmer. Each such skin face is
    moved off the eye or lid, keeping its side of it, to a clean gap (after the bake: a millimetre or two does not move the paint). Looked for both
    ways, from the eye's or lid's faces and from the skin's, as QA looks. Returns how many skin vertices moved."""
    from mathutils.bvhtree import BVHTree
    from mathutils.geometry import intersect_point_tri
    me = body.data
    names = {g.index: g.name for g in body.vertex_groups}
    moved = set()
    for _ in range(rounds):
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        dl = bm.verts.layers.deform.active

        def eye_part(f):
            best = {}
            for v in f.verts:
                for gi, w in v[dl].items():
                    best[names[gi]] = best.get(names[gi], 0) + w
            top = max(best, key=best.get)
            return top.startswith("Eye") or top.startswith("Lid")
        part = [eye_part(f) for f in bm.faces]
        tree = BVHTree.FromBMesh(bm)
        push = {}

        def check(src, dst, skin, eye):
            if abs(src.normal.dot(dst.normal)) < 0.99:
                return False
            n = eye.normal
            sdist = (skin.calc_center_median() - eye.calc_center_median()).dot(n)
            target = gap if sdist >= 0 else -gap
            if abs(sdist) >= gap:
                return False
            for v in skin.verts:
                step = n * (target - sdist)
                if v.index not in push or step.length > push[v.index].length:
                    push[v.index] = step
            return True
        for f in bm.faces:
            cen = f.calc_center_median()
            for p in [cen] + [cen.lerp(v.co, 0.6) for v in f.verts]:
                for _, _, j, _ in tree.find_nearest_range(p, gap):
                    if j is None or j == f.index or part[j] == part[f.index] or set(f.verts) & set(bm.faces[j].verts):
                        continue
                    g = bm.faces[j]
                    q = p - g.normal * g.normal.dot(p - g.verts[0].co)
                    if intersect_point_tri(q, *[v.co for v in g.verts[:3]]):
                        skin, eye = (g, f) if part[f.index] else (f, g)
                        check(f, g, skin, eye)
        if not push:
            bm.free()
            break
        bm.verts.ensure_lookup_table()
        for i, dv in push.items():
            bm.verts[i].co += dv
        moved |= set(push)
        bm.to_mesh(me)
        bm.free()
    me.update()
    return len(moved)


# poses in the game's axes (turns x, y, z: +x lifts what points forward; +y turns to its left); the same numbers as PetRig's AWH tables
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def probe(rig, body, bones=("Head", "Chest", "Spine1", "Spine2", "Tail", "Fluke", "PecL1", "PecL2")):
    """Each limb's signs, measured on the mesh: where the skin it carries goes (model axes, mm) under +0.4 rad about each game axis."""
    groups = {g.name: g.index for g in body.vertex_groups}
    dg = bpy.context.evaluated_depsgraph_get()

    def centre(idx):
        bpy.context.view_layer.update()
        dg2 = bpy.context.evaluated_depsgraph_get()
        me = body.evaluated_get(dg2).to_mesh()
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        body.evaluated_get(dg2).to_mesh_clear()
        return co.reshape(-1, 3)[idx].mean(axis=0)
    for bone in bones:
        gi = groups[bone]
        idx = [v.index for v in body.data.vertices if any(g.group == gi and g.weight > 0.6 for g in v.groups)]
        if not idx:
            print("PROBE", bone, "no skin", flush=True)
            continue
        pose(rig, {})
        c0 = centre(idx)
        row = []
        for k, axis in enumerate("xyz"):
            turn = [0.0, 0.0, 0.0]
            turn[k] = 0.4
            pose(rig, spec({bone: tuple(turn)}))
            d = (centre(idx) - c0) * 1000
            row.append("%s+ (%d,%d,%d)" % (axis, round(d[0]), round(d[1]), round(d[2])))
        print("PROBE", bone, len(idx), "verts", " ".join(row), flush=True)
    pose(rig, {})


def uv_clashes(body, size=1024):
    """Which faces share texels: per clash, the two faces' centres and their main bones."""
    me = body.data
    uv = me.uv_layers.active.data
    names = {g.index: g.name for g in body.vertex_groups}
    owner = np.full((size, size), -1, dtype=np.int32)
    pairs = {}
    for p in me.polygons:
        loops = list(p.loop_indices)
        a, b, c = [np.array(uv[i].uv) * size for i in loops[:3]]
        low = np.clip(np.floor(np.minimum(np.minimum(a, b), c)).astype(int), 0, size - 1)
        high = np.clip(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int), 0, size - 1)
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-9:
            continue
        ys, xs = np.mgrid[low[1]:high[1] + 1, low[0]:high[0] + 1]
        qx, qy = xs + 0.5, ys + 0.5
        w0 = ((b[1] - c[1]) * (qx - c[0]) + (c[0] - b[0]) * (qy - c[1])) / d
        w1 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / d
        inside = (w0 >= 0) & (w1 >= 0) & (w0 + w1 <= 1)
        here = owner[ys[inside], xs[inside]]
        for o in set(here[here >= 0].tolist()):
            pairs[(o, p.index)] = pairs.get((o, p.index), 0) + int((here == o).sum())
        owner[ys[inside], xs[inside]] = p.index

    def bone_of(fi):
        best = {}
        for vi in me.polygons[fi].vertices:
            for g in me.vertices[vi].groups:
                best[names[g.group]] = best.get(names[g.group], 0) + g.weight
        return max(best, key=best.get)
    for (a, b), n in sorted(pairs.items(), key=lambda kv: -kv[1])[:8]:
        ca, cb = me.polygons[a].center, me.polygons[b].center
        print("UV CLASH", n, "texels", tuple(round(v, 3) for v in ca), bone_of(a), "|", tuple(round(v, 3) for v in cb), bone_of(b), flush=True)



VIEWS = [(0, -1, 0.2), (0.62, -0.72, 0.35), (1, 0, 0.12), (0, 1, 0.3), (-0.6, 0.6, 0.45), (-0.62, -0.72, 0.3), (0, -0.05, 1), (0.5, -0.5, -0.5)]
VIEW_AT = (0, -0.02, 0.28)
FACE_AT = (0.06, -0.3, 0.29)
EXTRA = [(0.9, -0.45, 0.1, 1.1, FACE_AT), (0.2, -0.95, 0.15, 1.0, FACE_AT), (0.3, -0.4, -0.85, 1.2, (0, -0.22, 0.2)), (0.85, -0.4, 0.45, 1.0, (0.3, -0.05, 0.17)),
         (0.3, 0.9, 0.4, 1.0, (0, 0.42, 0.31))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, "glow", {k: len(o.data.polygons) for k, o in glows.items()}, flush=True)
    stage_setup((0.3, 0.32, 0.42, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
        dark = bpy.data.materials.new("clay_eye")
        g = next(n for n in dark.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.05, 0.06, 0.12, 1)
        g.inputs["Roughness"].default_value = 0.15
    else:
        mat = hi_material(ao_distance=0.03, ao_share=0.35)
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(dark if STAGE == "clay" and key.startswith("Eye") else mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=2.7, size=640)
    print("DONE", flush=True)


def is_head(poly):
    return poly.center.y < -0.2


if __name__ == "__main__" and STAGE in ("all", "rig"):
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.03, ao_share=0.35)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.42, 1))
    lows = build_low(pieces, frames)
    print("SURFACE GAP skin", round(surface_gap(lows["Skin"], data["tree"]), 4), flush=True)
    # its face given more of the atlas
    unwrap(lows, [(is_head, 1.6), (None, 1.0)], SCALES, margin=0.01, angle=42)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.24, 0.2, 0.42, 1), far=("Skin",), reach=(0.004, 0.01), far_reach=(0.008, 0.02))
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for o in glows.values():
        bpy.data.objects.remove(o, do_unlink=True)          # first, so the game's pieces take their exact names
    low_tree = tree_of(lows["Skin"])
    sa, sb = build_strings(low_tree, N + "StringsA_Glow_" + STRING_HEX, N + "StringsB_Glow_" + STRING_HEX, GAME, low=True)
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 24, 0.0074, 10), (20, -18, 0.0033, 6))),
             "StringsA": sa, "StringsB": sb, "Stars": build_stars(N + "Stars_Glow_" + STAR_HEX, GAME, low=True)}
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames)
    body = bind_all(lows, rig, glows)
    print("SKIN MOVED OFF EYES AND LIDS", part_flush(body), "verts", flush=True)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for o in [body] + list(glows.values()) for v in o.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", body.name, uv_overlap_texels(body.data, 1024), flush=True)
    uv_clashes(body)
    zs = [(o.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    print("Z range", round(min(zs), 4), round(max(zs), 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name in ("Root", "Body", "Head", "Fluke", "PecL1"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    vs = [v.co for v in glows["Glints"].data.vertices]
    mid = Vector(((min(v.x for v in vs) + max(v.x for v in vs)) / 2, (min(v.y for v in vs) + max(v.y for v in vs)) / 2, (min(v.z for v in vs) + max(v.z for v in vs)) / 2))
    print("GLINTS box centre game axes", (round(-mid.x, 4), round(mid.z, 4), round(mid.y, 4)), flush=True)
    probe(rig, body)
    if STAGE == "rig":
        print("DONE", flush=True)
        raise SystemExit(0)


# its stances, in game axes, signs measured on the mesh (probe): +x lifts its head; -x raises its spine, tail and flukes (they point back); its
# left flipper flaps down with +z and sweeps back with +y. Left values; the right mirrors y and z.
def sym(table):
    out = {}
    for name, v in table.items():
        out[name] = v
        if name.startswith("PecL"):
            out["PecR" + name[4:]] = (v[0], -v[1], -v[2]) + tuple(v[3:])
    return out


SWIM_UP = sym({"Head": (0.06, 0, 0), "Spine1": (-0.08, 0, 0), "Spine2": (-0.14, 0, 0), "Tail": (-0.2, 0, 0), "Fluke": (-0.3, 0, 0)})
SWIM_DOWN = sym({"Head": (-0.06, 0, 0), "Spine1": (0.08, 0, 0), "Spine2": (0.14, 0, 0), "Tail": (0.22, 0, 0), "Fluke": (0.35, 0, 0)})
FLAP_UP = sym({"PecL1": (0, 0, -0.5), "PecL2": (0, 0, -0.25)})
FLAP_DOWN = sym({"PecL1": (0, 0, 0.42), "PecL2": (0, 0, 0.2)})
GLIDE = sym({"PecL1": (0, 0.45, -0.1), "PecL2": (0, 0.15, 0)})
TURN = sym({"Head": (0, 0.2, 0), "Chest": (0, 0.12, 0), "Spine1": (0, -0.12, 0), "Spine2": (0, -0.16, 0), "Tail": (0, -0.18, 0), "Fluke": (0, -0.15, 0)})
SING = sym({"Head": (0.26, 0, 0), "Chest": (0.08, 0, 0), "Spine1": (-0.1, 0, 0), "Spine2": (-0.14, 0, 0), "Tail": (-0.16, 0, 0), "Fluke": (-0.22, 0, 0),
            "PecL1": (0, -0.35, -0.3), "PecL2": (0, -0.1, -0.15)})


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    return {"Blink": lids(BLINK_U, BLINK_L), "Wide": lids(-12, -6), "SwimUp": spec(SWIM_UP), "SwimDown": spec(SWIM_DOWN), "FlapUp": spec(FLAP_UP),
            "FlapDown": spec(FLAP_DOWN), "Glide": spec(GLIDE), "Turn": spec(TURN), "Sing": {**spec(SING), **lids(-10, -5)},
            "Look": spec({"Head": (0.1, 0.3, 0.1)})}


if __name__ == "__main__" and STAGE == "all":
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=2.7, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    side = (1, -0.05, 0.12, 2.6, VIEW_AT)
    face = (0.75, -0.6, 0.15, 1.1, FACE_AT)
    wide = (0.62, -0.72, 0.35, 2.7, VIEW_AT)
    front = (0.15, -1, 0.25, 2.6, VIEW_AT)
    for name, view in (("Blink", face), ("Wide", face), ("SwimUp", side), ("SwimDown", side), ("FlapUp", front), ("FlapDown", front), ("Glide", wide),
                       ("Turn", (0, -0.05, 1, 2.7, VIEW_AT)), ("Sing", side), ("Look", face)):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.3, 2.6, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)
