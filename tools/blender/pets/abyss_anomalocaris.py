"""The Abyss Anomalocaris (Legendary, Primordial seas; Primordial Abyss Egg): "The first hunter of the first sea. The sea is long gone; it hasn't noticed."

A new creature, the Primordial Abyss Egg's own. A Cambrian hunter that swims through the air as it once swam through the first ocean: a low oval head shield, a flattened
trunk of nine segments fringed with nine pairs of shingled flaps that ripple in a wave from front to back, a tail fan of three pairs of long blades raised in a V, and two great
ringed arms under its head, curled like fern fronds, each segment armed with a pair of curved spines. Its eyes are its own: two large kidney-shaped compound eyes on short thick
stalks at the back corners of the shield, faceted all over, black-violet. It is made of the egg's primordial stone (dark slate, warped strata, thin ochre seams), paler
beneath, and the only light on it is a thin line of magenta along the outer edge of every flap and tail blade.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/abyss_anomalocaris.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre. It always hovers. The maps go to assets/pets/PrimordialAbyssEgg/.

What touches what: the shield lies on the head, its underside sunk into it; the eye stalks and the mouth cone are fused into the skin; each flap's root and each tail blade's
root are sunk into the trunk; the arms' roots are sunk into the underside of the head; each spine's root is sunk into its arm segment.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "AbyssAnomalocaris"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "PrimordialAbyssEgg")

# ---------- colours: the egg's primordial stone ----------
SLATE, DEEP, STRATA, ASH = rgb(52, 48, 60), rgb(26, 24, 34), rgb(78, 70, 84), rgb(112, 104, 112)
OCHRE, RUST, BELLY, BONE = rgb(196, 138, 66), rgb(132, 82, 44), rgb(150, 132, 112), rgb(226, 214, 190)
EYE_BLACK, EYE_VIOLET, MAGENTA = rgb(10, 8, 18), rgb(70, 40, 110), rgb(222, 52, 178)

# ---------- the frame of it ----------
SPINE = catmull([V(0, -0.60, 0.0), V(0, -0.50, 0.012), V(0, -0.38, 0.022), V(0, -0.24, 0.026), V(0, -0.08, 0.022), V(0, 0.10, 0.014), V(0, 0.28, 0.006), V(0, 0.44, 0.0),
                 V(0, 0.555, -0.002)], 12)
P_W = ((0, 0.03), (0.04, 0.085), (0.1, 0.125), (0.2, 0.145), (0.32, 0.15), (0.45, 0.148), (0.6, 0.13), (0.75, 0.098), (0.88, 0.064), (1, 0.04))
P_T = ((0, 0.016), (0.06, 0.04), (0.16, 0.056), (0.32, 0.066), (0.5, 0.062), (0.7, 0.05), (0.88, 0.036), (1, 0.027))
P_B = ((0, 0.016), (0.06, 0.032), (0.16, 0.044), (0.32, 0.05), (0.5, 0.048), (0.7, 0.04), (0.88, 0.029), (1, 0.023))
SPINE_LEN = sum((SPINE[i + 1] - SPINE[i]).length for i in range(len(SPINE) - 1))

FLAPS = 9
FLAP_Y = np.linspace(-0.27, 0.41, FLAPS)
FLAP_REACH = (0.13, 0.17, 0.205, 0.228, 0.236, 0.226, 0.2, 0.165, 0.128)
FLAP_CHORD = (0.122, 0.138, 0.148, 0.152, 0.152, 0.148, 0.138, 0.126, 0.112)
FLAP_PITCH = 0.016         # each flap rises from its front edge to its back, so it rests over the next flap and never touches it
FLAP_ARCH = 0.024          # level at the root, curving a little down to the tip
FLAP_SWEEP = 0.105         # how far back its tip is carried

FAN_BASE = V(0, 0.565, 0.0)
FAN = ((14, 26, 0.3, 0.088), (32, 19, 0.27, 0.08), (50, 12, 0.22, 0.068))     # (out from the axis, up, length, width), degrees and metres

ARM = [V(0.03, -0.548, -0.008), V(0.046, -0.635, -0.028), V(0.056, -0.73, -0.052), V(0.058, -0.79, -0.092), V(0.054, -0.812, -0.142), V(0.046, -0.788, -0.182),
       V(0.038, -0.748, -0.194), V(0.033, -0.716, -0.18), V(0.031, -0.701, -0.157), V(0.032, -0.706, -0.139)]
ARM_SEGMENTS = 11

STALK = [V(0.09, -0.392, 0.036), V(0.14, -0.4, 0.054), V(0.166, -0.404, 0.064)]
EYE_SIZE = (0.036, 0.062, 0.045)      # out along the stalk, fore and aft, up and down: a kidney, long front to back

MOUTH_C, MOUTH_R = V(0, -0.455, -0.026), 0.034


def prof(knots, f):
    a = np.array(knots)
    return np.interp(f, a[:, 0], a[:, 1])


def spine_at(f):
    k = float(np.clip(f, 0, 1)) * (len(SPINE) - 1)
    i = min(int(k), len(SPINE) - 2)
    return SPINE[i].lerp(SPINE[i + 1], k - i)


def spine_f(y):
    """Fraction along the spine at this y (the spine runs straight down -Y to +Y)."""
    ys = np.array([p.y for p in SPINE])
    return np.interp(y, ys, np.linspace(0, 1, len(SPINE)))


def merged(objs, name, coll):
    bm = bmesh.new()
    for o in objs:
        bm.from_mesh(o.data)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


# ---------- the trunk ----------
def trunk_rings(nt, rows):
    out = []
    a = np.linspace(-math.pi, math.pi, nt, endpoint=False)
    cs, sn = np.cos(a), np.sin(a)
    for i in range(rows):
        f = i / (rows - 1)
        p = spine_at(f)
        w, t, b = float(prof(P_W, f)), float(prof(P_T, f)), float(prof(P_B, f))
        x = w * np.sign(cs) * np.abs(cs) ** 0.55          # flattened, its sides full: the flaps grow from them
        z = np.where(sn > 0, t * np.abs(sn) ** 0.9, -b * np.abs(sn) ** 0.7)
        ring = np.stack((x, np.zeros_like(x), z), 1) + np.array(tuple(p))[None, :]
        out.append(ring)
    return out


def rings_mesh(name, coll, front, rings, back):
    m = Mesh()
    bm = m.bm
    a = bm.verts.new(front)
    grid = [[bm.verts.new(tuple(p)) for p in ring] for ring in rings]
    b = bm.verts.new(back)
    nt = len(rings[0])
    for j in range(nt):
        j2 = (j + 1) % nt
        bm.faces.new((a, grid[0][j2], grid[0][j]))
        for i in range(len(grid) - 1):
            bm.faces.new((grid[i][j], grid[i][j2], grid[i + 1][j2], grid[i + 1][j]))
        bm.faces.new((grid[-1][j], grid[-1][j2], b))
    return m.finish(name, coll)


def stalk_path(side, per=6):
    return catmull([mir(p, side) for p in STALK], per)


def stalk_radius(f):
    return 0.031 - 0.006 * f


def eye_centre(side):
    path = stalk_path(side)
    d = (path[-1] - path[-2]).normalized()
    return path[-1] + d * (EYE_SIZE[0] * 0.55), d


def build_skin(name, coll):
    """Trunk, the tail's knob, the eye stalks and the mouth cone, fused into one smooth skin."""
    rings = trunk_rings(96, 150)
    loft = rings_mesh(name + "Loft", coll, tuple(SPINE[0] - V(0, 0.004, 0)), rings, tuple(SPINE[-1] + V(0, 0.004, 0)))
    m = Mesh()
    m.ball(FAN_BASE + V(0, -0.012, 0.004), (0.036, 0.034, 0.028), 32, 20)        # the knob the tail blades grow from
    for side in (1, -1):
        m.tube(stalk_path(side), stalk_radius, sides=24)
    # the mouth cone: a thick ring of plates under the head, its middle dark and deep
    ring = [MOUTH_C + V(math.cos(TAU * k / 48) * MOUTH_R, math.sin(TAU * k / 48) * MOUTH_R * 1.08, 0) for k in range(49)]
    m.tube(ring, lambda f: 0.0105, sides=14, plane=V(0, 0, 1), caps=False)
    extra = m.finish(name + "Extra", coll, recalc=False)
    o = merged((loft, extra), name, coll)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0036, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def shape_skin(o):
    """The trunk's forms that a loft can't give: the grooves between segments, the setal ridges along the back, the plates of the mouth cone."""
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    top = smooth(-0.1, 0.5, Nn[:, 2])
    # the grooves, midway between the flaps, across the back and round the sides
    groove = np.zeros_like(y)
    for k in range(FLAPS - 1):
        gy = (FLAP_Y[k] + FLAP_Y[k + 1]) / 2
        groove = np.maximum(groove, 1 - smooth(0.0, 0.0085, np.abs(y - gy)))
    trunk = smooth(-0.33, -0.3, y) * (1 - smooth(0.5, 0.53, y))
    # the setal blades: fine ridges running along the back in two bands either side of the midline
    band = smooth(0.02, 0.035, np.abs(x)) * (1 - smooth(0.085, 0.1, np.abs(x)))
    ridges = (0.5 + 0.5 * np.cos(np.abs(x) * TAU / 0.0085)) * band * top
    # the mouth cone's plates: radial grooves round the ring
    mr = np.sqrt((x - MOUTH_C.x) ** 2 + ((y - MOUTH_C.y) / 1.08) ** 2)
    ma = np.arctan2(y - MOUTH_C.y, x - MOUTH_C.x)
    cone = (1 - smooth(MOUTH_R + 0.012, MOUTH_R + 0.02, mr)) * smooth(0.0, -0.02, z - MOUTH_C.z) * smooth(0.0, 0.4, -Nn[:, 2])
    plates = (1 - smooth(0.0, 0.3, np.abs(np.sin(ma * 7)))) * cone
    pit = (1 - smooth(MOUTH_R * 0.55, MOUTH_R * 0.8, mr)) * cone
    d = -0.0032 * groove * trunk + 0.0007 * ridges * trunk - 0.0016 * plates - 0.012 * pit
    set_verts(o, P + Nn * d[:, None])
    return {"groove": groove * trunk, "ridges": ridges * trunk, "cone": cone, "plates": plates, "pit": pit}


# ---------- the shield ----------
SHIELD_Y = (-0.585, -0.335)       # from just behind the nose to the eyes


def shield_xy(u, v):
    """Its outline follows the head's own width, a little inside it, rounded off at both ends."""
    Y = 2 * v - 1
    y = SHIELD_Y[0] + (SHIELD_Y[1] - SHIELD_Y[0]) * v
    w = float(prof(P_W, spine_f(y))) * 0.86 * max(0.24, math.sqrt(max(0.0, 1 - abs(Y) ** 3.2)))      # (its ends short edges, never points)
    return w * (2 * u - 1), y


def build_shield(name, coll, tree, nu=48, nv=52):
    """A plate laid over the head, following it: sunk a millimetre at its underside, its top a low dome with a shallow keel, so its edge stands as a clean step."""
    def point(u, v):
        x, y = shield_xy(u, v)
        hit = tree.ray_cast(V(x, y, 0.5), V(0, 0, -1), 1.0)[0]
        z = hit.z if hit else 0.03
        r2 = (2 * u - 1) ** 2 + (2 * v - 1) ** 2
        r2 = min(1.0, r2 / 2 + max(abs(2 * u - 1), abs(2 * v - 1)) ** 2 / 2)
        keel = 0.0022 * math.exp(-((2 * u - 1) / 0.12) ** 2) * (1 - r2)
        return (x, y, z + 0.0008 + 0.0045 * (1 - r2) + keel)       # its underside 2 mm into the head, well clear of the skin's own faces

    def thick(u, v):
        r = max(abs(2 * u - 1), abs(2 * v - 1))
        return 0.0058 - 0.0018 * r ** 4
    m = Mesh()
    m.sheet(point, thick, nu, nv)
    o = m.finish(name, coll)
    return o


# ---------- the flaps ----------
def flap_root(k, side):
    y = float(FLAP_Y[k])
    f = float(spine_f(y))
    w = float(prof(P_W, f))
    c = spine_at(f)
    return V(side * w * 0.78, y, c.z - 0.006), w


def flap_point(k, side, u, v):
    """The middle surface of flap k at (u out from its root, v from its front edge to its back)."""
    root, w = flap_root(k, side)
    reach = FLAP_REACH[k] + w * 0.22
    # a lobe: broadest a third of the way out, its front edge curving back to a rounded tip, its back edge straighter
    half = 0.5 * FLAP_CHORD[k] * max(0.0, 1 - u ** 3.2) ** 0.38 * (1 + 0.12 * math.sin(math.pi * min(1.0, u * 1.3)))     # broad almost to its rounded end
    half = max(half, 0.0045)          # (never a point: its end stays a short rounded edge, no edge of zero length)
    sweep = FLAP_SWEEP * u ** 1.45 * (0.55 + 0.45 * FLAP_REACH[k] / 0.236)
    lean = 0.35 * half * u          # the front edge sweeps back more than the back edge does
    x = root.x + side * reach * u
    y = root.y + sweep + half * (2 * v - 1) + lean * (1 - v)
    z = root.z - FLAP_ARCH * (u * reach / 0.236) ** 1.7 + FLAP_PITCH * (v - 0.5) * (1 - 0.25 * u)
    return (x, y, z)


def flap_thick(u, v):
    return 0.0012 + 0.0058 * (1 - u) ** 0.8 * max(0.0, 4 * v * (1 - v)) ** 0.5 * max(0.0, 1 - u ** 6) ** 0.5      # never under 1.2 mm, so its faces can't lie on each other


def build_flaps(name, coll, ks, nu, nv):
    m = Mesh()
    meta = []
    for side, tag in ((1, "L"), (-1, "R")):
        for k in ks:
            before = len(m.bm.verts)
            m.sheet(lambda u, v, k=k, side=side: flap_point(k, side, u, v), flap_thick, nu, nv)
            m.bm.verts.ensure_lookup_table()
            meta += [(tag, k)] * (len(m.bm.verts) - before)
    o = m.finish(name, coll)
    return o, meta


# ---------- the tail fan ----------
def fan_frame(j, side):
    out, up, length, width = FAN[j]
    a, e = math.radians(out), math.radians(up)
    d = V(side * math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)).normalized()
    across = V(0, 0, 1).cross(d).normalized()           # level, square to the blade
    if across.x * side < 0:
        across = -across
    across = (across + V(0, 0, 0.35)).normalized()      # banked a little so the V opens upward
    return d, across, length, width


def fan_point(j, side, u, v):
    d, across, length, width = fan_frame(j, side)
    base = FAN_BASE + V(side * 0.012, -0.006, 0.004 + 0.009 * (2 - j))     # its root sunk into the knob, each blade a little above the next
    half = 0.5 * width * math.sin(math.pi * min(1.0, u ** 0.75 * 1.02)) ** 0.85 + 0.004 * (1 - u) + 0.0035 * u      # (its tip a short edge, never a point)
    lift = 0.035 * u ** 2 * length / 0.27                 # its tip curling up
    p = base + d * (length * u) + across * (half * (2 * v - 1)) + V(0, 0, lift)
    return tuple(p)


def fan_thick(u, v):
    return 0.0015 + 0.005 * (1 - u) ** 0.9 * max(0.0, 4 * v * (1 - v)) ** 0.5


def build_fan(name, coll, js, nu, nv):
    m = Mesh()
    meta = []
    for side, tag in ((1, "L"), (-1, "R")):
        for j in js:
            before = len(m.bm.verts)
            m.sheet(lambda u, v, j=j, side=side: fan_point(j, side, u, v), fan_thick, nu, nv)
            m.bm.verts.ensure_lookup_table()
            meta += [(tag, j)] * (len(m.bm.verts) - before)
    o = m.finish(name, coll)
    return o, meta


# ---------- the arms ----------
def arm_path(side, per=10):
    return catmull([mir(p, side) for p in ARM], per)


def arm_radius(f):
    """Thick at the root, tapering to the curled tip, pinched at every joint between its segments."""
    base = 0.0165 * (1 - f) ** 0.8 + 0.0046
    seg = f * ARM_SEGMENTS
    joint = np.exp(-((seg - np.round(seg)) / 0.12) ** 2) * (f > 0.04)
    return base * (1 - 0.17 * joint)


def arm_frames(side, path):
    """Per point: tangent, the inner side of the curl (where the spines grow: toward the curl's centre, or straight down where the arm runs straight), and the side axis."""
    n = len(path)
    out = []
    for i, p in enumerate(path):
        tan = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
        k = (path[max(i - 4, 0)] + path[min(i + 4, n - 1)]) * 0.5 - p
        k = k - tan * k.dot(tan)
        down = V(0, 0, -1) - tan * tan.z
        down = down.normalized()
        w = min(1.0, k.length / 0.004) if k.length > 1e-6 else 0.0
        inner = (down * (1 - w) + (k.normalized() * w if w > 0 else V(0, 0, 0))).normalized()
        out.append((tan, inner, tan.cross(inner).normalized()))
    return out


def spine_specs(side):
    """(base, direction, length, along) of every spine on this arm: a pair on each segment from the second to the ninth, splayed, longest mid-arm."""
    path = arm_path(side, 24)
    frames = arm_frames(side, path)
    n = len(path)
    specs = []
    for s in range(1, 9):
        f = (s + 0.5) / ARM_SEGMENTS
        i = min(n - 1, int(round(f * (n - 1))))
        tan, inner, b = frames[i]
        length = 0.016 + 0.046 * math.sin(math.pi * min(1.0, (f - 0.08) / 0.78)) ** 1.2
        for spread in (-1, 1):
            d = (inner * math.cos(math.radians(24)) + b * math.sin(math.radians(24)) * spread + tan * 0.22).normalized()
            r = float(arm_radius(f))
            base = path[i] + inner * r * 0.38 + b * spread * r * 0.42      # the pair stand apart at the root, each sunk into the arm
            specs.append((base, d, length, tan))
    return specs


def spine_path(base, d, length, tan, per):
    """A spine curving toward the arm's tip."""
    pts = []
    for k in range(per + 1):
        t = k / per
        bend = tan * (0.28 * length * t ** 2)
        pts.append(base + d * (length * t) + bend)
    return pts


def build_arms(name, coll, sides, per, spine_sides, spine_per):
    m = Mesh()
    meta = []
    for side, tag in ((1, "L"), (-1, "R")):
        path = arm_path(side, per)
        n = len(path)
        before = len(m.bm.verts)
        m.tube(path, lambda f: float(arm_radius(f)), sides=sides)
        m.bm.verts.ensure_lookup_table()
        count = len(m.bm.verts) - before
        meta += [(tag, i / (n - 1)) for i in range(n) for _ in range(sides)][:count]
        for base, d, length, tan in spine_specs(side):
            before = len(m.bm.verts)
            m.tube(spine_path(base, d, length, tan, spine_per), lambda t, L=length: max(0.0006, (0.0034 + 0.06 * L) * (1 - t) ** 1.05), sides=spine_sides, flat=0.55, plane=tan)
            m.bm.verts.ensure_lookup_table()
            f_at = float(nearest_on(path, np.array([tuple(base)]))[0][0])
            meta += [(tag, f_at)] * (len(m.bm.verts) - before)
    o = m.finish(name, coll)
    return o, meta


# ---------- the eyes ----------
def eye_frame(side):
    c, d = eye_centre(side)
    fore = V(0, -1, 0)
    fore = (fore - d * fore.dot(d)).normalized()
    up = d.cross(fore).normalized()
    if up.z < 0:
        up = -up
    return c, d, fore, up


def build_eyes(name, coll, seg, rings):
    """Each a kidney: long fore and aft, its inner side dished round the stalk, faceted all over."""
    m = Mesh()
    for side in (1, -1):
        c, d, fore, up = eye_frame(side)
        q = Matrix((tuple(d), tuple(fore), tuple(up))).transposed().to_4x4()
        mat = Matrix.Translation(c) @ q @ Matrix.Diagonal((EYE_SIZE[0], EYE_SIZE[1], EYE_SIZE[2], 1))
        bmesh.ops.create_uvsphere(m.bm, u_segments=seg, v_segments=rings, radius=1.0, matrix=mat)
    o = m.finish(name, coll)
    P = verts(o)
    for side in (1, -1):
        c, d, fore, up = eye_frame(side)
        rel = P - np.array(tuple(c))
        mine = (rel[:, 0] * side > -0.05)
        a = rel @ np.array(tuple(d)) / EYE_SIZE[0]
        b = rel @ np.array(tuple(fore)) / EYE_SIZE[1]
        dish = np.exp(-(b / 0.45) ** 2) * smooth(0.2, -0.9, a) * 0.011      # the kidney's hollow, where the stalk goes in
        P[mine] -= (np.array(tuple(d))[None, :] * dish[:, None])[mine]
    set_verts(o, P)
    return o


def facets(o):
    """Per vertex of the eyes: distance to the nearest facet's centre (hexagonal, about 4 mm across), and that facet's own random."""
    P = verts(o)
    out_d, out_h = np.zeros(len(P)), np.zeros(len(P))
    for side in (1, -1):
        c, d, fore, up = eye_frame(side)
        rel = P - np.array(tuple(c))
        mine = rel[:, 0] * side > -0.05
        dirs = rel / np.maximum(np.linalg.norm(rel, axis=1)[:, None], 1e-9)
        # a facet grid on the eye's surface, by angle round the stalk axis and along it
        lon = np.arctan2(dirs @ np.array(tuple(up)), dirs @ np.array(tuple(fore)))
        lat = np.arcsin(np.clip(dirs @ np.array(tuple(d)), -1, 1))
        cell = 0.11
        qx = lon / cell
        qy = lat / (cell * 0.866)
        row = np.round(qy)
        col = np.round(qx - 0.5 * (row % 2))
        best = np.full(len(P), 9.0)
        bh = np.zeros(len(P))
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                r = row + dr
                cc = col + dc
                cx = (cc + 0.5 * (r % 2)) * cell
                cy = r * cell * 0.866
                dd = np.sqrt((lon - cx) ** 2 * np.cos(lat) ** 2 + (lat - cy) ** 2)
                h = hash01(cc.astype(np.int64), r.astype(np.int64), np.zeros_like(r, dtype=np.int64), 17 + side)
                better = dd < best
                best = np.where(better, dd, best)
                bh = np.where(better, h, bh)
        out_d[mine] = best[mine] / cell
        out_h[mine] = bh[mine]
    return out_d, out_h


def shape_eyes(o):
    d, h = facets(o)
    P = verts(o)
    Nn = normals(o)
    set_verts(o, P + Nn * (0.0012 * (1 - smooth(0.0, 0.62, d)) - 0.0004)[:, None])     # each facet a little dome
    return d, h


# ---------- the whole, high-detail ----------
def build_hi(clay=False):
    pieces, data = {}, {}
    skin = build_skin(N + "SkinHi", HI)
    data["SkinBase"] = bpy.data.objects.new(N + "SkinBase", skin.data.copy())
    HI.objects.link(data["SkinBase"])
    data["SkinBase"].hide_render = True
    data["skin_fields"] = shape_skin(skin)
    pieces["Skin"] = skin
    pieces["Shield"] = build_shield(N + "ShieldHi", HI, tree_of(data["SkinBase"]))
    odd, even = range(0, FLAPS, 2), range(1, FLAPS, 2)
    pieces["FlapsA"], data["FlapsA"] = build_flaps(N + "FlapsAHi", HI, odd, 40, 22)
    pieces["FlapsB"], data["FlapsB"] = build_flaps(N + "FlapsBHi", HI, even, 40, 22)
    pieces["FanA"], data["FanA"] = build_fan(N + "FanAHi", HI, (0, 2), 40, 16)
    pieces["FanB"], data["FanB"] = build_fan(N + "FanBHi", HI, (1,), 40, 16)
    pieces["Arms"], data["Arms"] = build_arms(N + "ArmsHi", HI, 28, 22, 12, 10)
    eyes = build_eyes(N + "EyesHi", HI, 96, 64)
    data["eye_facets"] = shape_eyes(eyes)
    pieces["Eyes"] = eyes
    remember_sheet_grid(40, 22)
    remember_sheet_grid(40, 16)
    glows, data["glow_owners"] = build_glows()
    if not clay:
        paint_all(pieces, data)
    return pieces, glows, data


def strata(P, f=9.0, seed=0):
    """The egg's stone: warped layers, as a value 0..1 across them."""
    warp = fbm(P * 1.0, 3.0, 3, seed) - 0.5
    layer = P[:, 2] * 1.0 + P[:, 1] * 0.35 + warp * 0.09
    return 0.5 + 0.5 * np.sin(layer * TAU * f)


def seam_lines(P, seed=0):
    """Thin ochre seams through the stone: a few hairline cracks, broken, wandering across it."""
    warp = fbm(P, 3.0, 3, seed + 5) - 0.5
    a = P[:, 0] * 2.3 + P[:, 1] * 1.4 + warp * 0.5
    d = np.abs(((a * 4.0) % 1.0) - 0.5)
    broken = smooth(0.5, 0.64, fbm(P, 9.0, 2, seed + 9))
    return (1 - smooth(0.0, 0.012, d)) * broken


def stone(P, seed=0):
    s = strata(P, 9.0, seed)
    col = mix(DEEP, SLATE, smooth(0.15, 0.75, s))
    col = mix(col, STRATA, smooth(0.7, 0.95, s) * 0.55)
    grain = fbm(P, 60.0, 3, seed + 3)
    col = col * (0.88 + 0.24 * grain)[:, None]
    return col


def paint_skin(o, fields):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    top = smooth(-0.35, 0.35, Nn[:, 2])
    col = stone(P, 1)
    belly = mix(stone(P, 21), mix(BELLY, ASH, 0.4), 0.42)        # the same stone, paler beneath
    col = mix(belly, col, top)
    # each segment's back edge rimmed ochre, the grooves deep
    rim = np.zeros_like(y)
    for k in range(FLAPS - 1):
        gy = (FLAP_Y[k] + FLAP_Y[k + 1]) / 2
        rim = np.maximum(rim, (1 - smooth(0.0, 0.0045, np.abs(y - (gy - 0.0115)))))
    trunk = smooth(-0.33, -0.3, y) * (1 - smooth(0.5, 0.53, y))
    col = mix(col, mix(OCHRE, RUST, 0.35), rim * trunk * top * 0.8)
    col = mix(col, DEEP * 0.6, fields["groove"] * 0.85)
    col = mix(col, OCHRE, seam_lines(P, 2) * top * 0.7)
    col = mix(col, ASH, fields["ridges"] * 0.25)
    # the mouth cone: pale plates, a dark pit
    col = mix(col, mix(BONE, OCHRE, 0.35), fields["cone"] * (0.4 + 0.6 * fields["plates"]))
    col = mix(col, EYE_BLACK, fields["pit"])
    rough = 0.62 - 0.12 * top * smooth(0.6, 0.9, strata(P, 9.0, 1))
    paint(o, col, rough)


def paint_shield(o):
    P = verts(o)
    Nn = normals(o)
    x, y = P[:, 0], P[:, 1]
    # growth lines round the plate, like an old shell's
    w = np.maximum(np.array([prof(P_W, spine_f(v)) for v in y]) * 0.86, 1e-3)
    r = np.sqrt((x / w) ** 2 + ((y - (SHIELD_Y[0] + SHIELD_Y[1]) / 2) / ((SHIELD_Y[1] - SHIELD_Y[0]) / 2)) ** 2)
    rings = 0.5 + 0.5 * np.sin(r * 26 + (fbm(P, 5.0, 3, 31) - 0.5) * 9)
    col = stone(P, 32)
    col = mix(col, STRATA, smooth(0.75, 1.0, rings) * 0.22 * smooth(0.25, 0.6, r))
    col = col * (0.9 + 0.2 * fbm(P, 50.0, 3, 33))[:, None]
    col = mix(col, OCHRE, smooth(0.9, 0.95, r) * (1 - smooth(0.97, 1.02, r)) * 0.7)       # its rim, a fine ochre line like the egg's seams
    col = mix(col, OCHRE, seam_lines(P, 4) * 0.5)
    col = mix(col, mix(BELLY, ASH, 0.5), smooth(0.2, -0.4, Nn[:, 2]))
    paint(o, col, 0.48 - 0.1 * smooth(0.5, 0.9, rings))


def paint_sheets(o, meta, point, kind):
    """Flaps and tail blades: stone on top, going darker to the edge, with fine veins out from the root and an ochre band inside the edge (the magenta line is a glow piece). Pale beneath."""
    P = verts(o)
    Nn = normals(o)
    col = np.zeros((len(P), 3))
    uv = sheet_uv(o, meta, point)
    u, v = uv[:, 0], uv[:, 1]
    edge = np.minimum(np.minimum(v, 1 - v) * 2.2, 1 - u)
    veins = (1 - smooth(0.0, 0.18, np.abs(np.sin((v - 0.5) * (14 if kind == "flap" else 9) + u * 1.5)))) * smooth(0.08, 0.25, u) * smooth(0.0, 0.1, edge)
    top_col = stone(P, 7 if kind == "flap" else 9)
    top_col = mix(top_col, DEEP, smooth(0.25, 0.0, edge) * 0.6)
    top_col = mix(top_col, ASH, veins * 0.35)
    band = smooth(0.05, 0.075, edge) * (1 - smooth(0.085, 0.11, edge))
    top_col = mix(top_col, OCHRE, band * 0.85)
    under = mix(stone(P, 8), mix(BELLY, ASH, 0.4), 0.42 + 0.2 * veins)
    top = smooth(-0.2, 0.2, Nn[:, 2]) if kind == "flap" else np.ones(len(P))      # a tail blade is seen from above on both faces: stone on both
    col = mix(under, top_col, top)
    paint(o, col, 0.55 - 0.1 * band)


def sheet_uv(o, meta, point):
    """Per vertex of a set of sheets: its (u, v) on the sheet it belongs to, found by its index in the grid (Mesh.sheet lays rows out in order)."""
    count = len(o.data.vertices)
    out = np.zeros((count, 2))
    i = 0
    while i < count:
        key = meta[i]
        j = i
        while j < count and meta[j] == key:
            j += 1
        n = j - i                      # (nu + 1) * (nv + 1) * 2 per sheet
        out[i:j] = SHEET_UV[n]
        i = j
    return out


SHEET_UV = {}


def remember_sheet_grid(nu, nv):
    g = np.array([(a / nu, b / nv) for a in range(nu + 1) for b in range(nv + 1) for _ in range(2)])
    SHEET_UV[len(g)] = g


def paint_arms(o, meta):
    P = verts(o)
    f = np.array([m[1] for m in meta])
    seg = f * ARM_SEGMENTS
    joint = np.exp(-((seg - np.round(seg)) / 0.055) ** 2) * (f > 0.04)
    # spines: every vertex further than the arm's own radius from its centre line
    dist = np.zeros(len(P))
    for side, tag in ((1, "L"), (-1, "R")):
        mine = np.array([m[0] == tag for m in meta])
        _, d = nearest_on(arm_path(side, 24), P[mine])
        dist[mine] = d
    radius = np.array([float(arm_radius(x)) for x in f])
    spine = smooth(1.15, 1.6, dist / radius)
    col = mix(DEEP, SLATE, 0.35 + 0.3 * fbm(P, 40.0, 3, 41))
    col = mix(col, mix(OCHRE, RUST, 0.45), joint * 0.75)
    tip = smooth(1.6, 4.0, dist / radius)
    spine_col = mix(BONE, mix(BONE, RUST, 0.6), tip)
    col = mix(col, spine_col, spine)
    paint(o, col, 0.5 - 0.15 * spine)


def paint_eyes(o, fac):
    d, h = fac
    col = mix(EYE_BLACK, EYE_VIOLET, smooth(0.35, 0.62, d) * 0.85)          # each facet dark, its rim violet
    col = mix(col, rgb(120, 70, 170), (h > 0.92) * (1 - smooth(0.0, 0.4, d)) * 0.4)     # a few facets catching more light
    paint(o, col, np.full(len(d), 0.12))


def paint_all(pieces, data):
    paint_skin(pieces["Skin"], data["skin_fields"])
    paint_shield(pieces["Shield"])
    for key in ("FlapsA", "FlapsB"):
        paint_sheets(pieces[key], data[key], None, "flap")
    for key in ("FanA", "FanB"):
        paint_sheets(pieces[key], data[key], None, "fan")
    paint_arms(pieces["Arms"], data["Arms"])
    paint_eyes(pieces["Eyes"], data["eye_facets"])


# ---------- the glow pieces: a thin magenta line along every flap's and tail blade's outer edge ----------
GLOW_HEX = "e040b8"
GLOW_W = 0.009


def sheet_normal(point, u, v, eps=1e-3):
    p = Vector(point(u, v))
    du = Vector(point(min(1.0, u + eps), v)) - Vector(point(max(0.0, u - eps), v))
    dv = Vector(point(u, min(1.0, v + eps))) - Vector(point(u, max(0.0, v - eps)))
    n = du.cross(dv)
    return p, (n.normalized() if n.length > 1e-12 else V(0, 0, 1))


GLOW_LIFT = 0.0024          # above the sheet's face: clear of it for any renderer


def rounded_outline(segments, radius):
    """A path in (u, v) through these corner points, each inner corner rounded by an arc of this radius (in u, v units): no fold for the strip's inner edge."""
    pts = []
    for i in range(len(segments) - 1):
        a, b = np.array(segments[i]), np.array(segments[i + 1])
        n = max(2, int(np.linalg.norm(b - a) / 0.03))
        for t in np.linspace(0, 1, n, endpoint=False):
            pts.append(a + (b - a) * t)
    pts.append(np.array(segments[-1]))
    pts = np.array(pts)
    # round the corners: a few passes of a moving average, ends held
    for _ in range(int(radius * 120)):
        pts[1:-1] = (pts[:-2] + pts[1:-1] * 2 + pts[2:]) / 4
    return [tuple(p) for p in pts]


def edge_strip(m, point, thick, outline):
    """A strip lying on a sheet's upper face just inside its edge: outline in (u, v), its inner edge GLOW_W in toward the sheet's middle line at that
    point's own place along it (pulled back from the end), every face turned up."""
    rows = []
    for i, (u, v) in enumerate(outline):
        p, n = sheet_normal(point, u, v)
        if n.z < 0:
            n = -n
        prev = Vector(point(*outline[max(0, i - 1)]))
        nxt = Vector(point(*outline[min(len(outline) - 1, i + 1)]))
        tan = (nxt - prev).normalized()
        inward = n.cross(tan).normalized()
        if inward.dot(Vector(point(min(u, 0.9) * 0.95, 0.5)) - p) < 0:
            inward = -inward
        lift = n * (thick(u, v) / 2 + GLOW_LIFT)
        rows.append((p + lift, p + inward * GLOW_W + lift, n))
    verts = [(m.bm.verts.new(a), m.bm.verts.new(b)) for a, b, _ in rows]
    for i in range(len(rows) - 1):
        q = [verts[i][0], verts[i + 1][0], verts[i + 1][1], verts[i][1]]
        face_n = (rows[i + 1][0] - rows[i][0]).cross(rows[i][1] - rows[i][0])
        if face_n.dot(rows[i][2]) < 0:
            q.reverse()
        m.bm.faces.new(q)


def flap_outline(k):
    """Round the flap's visible edge: out along its back edge from halfway, round its end, and back along the front edge to near its root."""
    return rounded_outline([(0.6, 0.995), (0.985, 0.995), (0.985, 0.12)], 0.12)


def fan_outlines():
    """Each long edge of a tail blade, stopping where the blade grows too narrow to hold two lines side by side (its tip is under 3 cm wide past u = 0.86)."""
    return [rounded_outline([(0.14, 0.99), (0.86, 0.99)], 0.0), rounded_outline([(0.14, 0.01), (0.86, 0.01)], 0.0)]


def build_glows():
    glows, owners = {}, {}
    for side, tag in ((1, "L"), (-1, "R")):
        m = Mesh()
        owner = []
        for k in range(FLAPS):
            before = len(m.bm.verts)
            edge_strip(m, lambda u, v, k=k, side=side: flap_point(k, side, u, v), flap_thick, flap_outline(k))
            m.bm.verts.ensure_lookup_table()
            owner += [("Flap", tag, k)] * (len(m.bm.verts) - before)
        for j in range(len(FAN)):
            before = len(m.bm.verts)
            for outline in fan_outlines():
                edge_strip(m, lambda u, v, j=j, side=side: fan_point(j, side, u, v), fan_thick, outline)
            m.bm.verts.ensure_lookup_table()
            owner += [("Fan", tag, j)] * (len(m.bm.verts) - before)
        glows["Edges" + tag] = m.finish(N + "Edges" + tag + "_Glow_" + GLOW_HEX, HI, smooth_shade=False, recalc=False)
        owners["Edges" + tag] = owner
    return glows, owners


def show_glows(glows):
    for o in glows.values():
        m = bpy.data.materials.new(o.name)
        g = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        h = GLOW_HEX
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 2.0
        o.data.materials.append(m)
        o.visible_shadow = False


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.32), (1, 0, 0.1), (0, 1, 0.22), (-0.62, 0.62, 0.42), (-0.62, -0.72, 0.3), (0, -0.02, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, -0.02, -0.02)
FACE_AT = (0, -0.55, -0.04)
EXTRA = [(0, -1, 0.15, 1.1, FACE_AT), (0.7, -0.7, 0.2, 1.1, FACE_AT), (1, -0.1, 0.05, 1.1, FACE_AT), (0.3, -0.5, -0.8, 1.0, (0, -0.55, -0.08)), (0.55, -0.6, 0.55, 0.7, (0.18, -0.42, 0.07)),
         (0.2, 0.9, 0.4, 1.3, (0, 0.6, 0.05)), (1, 0.2, 0.6, 1.4, (0.15, 0.05, 0))]


if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
    else:
        mat = hi_material(ao_distance=0.03, ao_share=0.4)
    for o in set(pieces.values()):
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=3.4, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
TEXELS = {"Shield": 1.3, "FlapsA": 1.0, "FlapsB": 1.0, "FanA": 1.0, "FanB": 1.0, "Arms": 1.5, "Eyes": 2.0}
META = {}


def build_low(data):
    skin = decimated(data["SkinBase"], N + "SkinLow", 3600)
    skin.data.polygons.foreach_set("use_smooth", [True] * len(skin.data.polygons))
    print("SKIN decimated gap", round(surface_gap(skin, tree_of(data["SkinBase"])), 4), flush=True)
    lows = {"Skin": skin}
    lows["Shield"] = build_shield(N + "ShieldLow", GAME, tree_of(data["SkinBase"]), 10, 12)
    odd, even = range(0, FLAPS, 2), range(1, FLAPS, 2)
    lows["FlapsA"], META["FlapsA"] = build_flaps(N + "FlapsALow", GAME, odd, 7, 4)
    lows["FlapsB"], META["FlapsB"] = build_flaps(N + "FlapsBLow", GAME, even, 7, 4)
    lows["FanA"], META["FanA"] = build_fan(N + "FanALow", GAME, (0, 2), 7, 3)
    lows["FanB"], META["FanB"] = build_fan(N + "FanBLow", GAME, (1,), 7, 3)
    lows["Arms"], META["Arms"] = build_arms(N + "ArmsLow", GAME, 8, 3, 4, 2)
    lows["Eyes"] = build_eyes(N + "EyesLow", GAME, 18, 12)
    triangulate(lows)
    return lows


# Seen in the game's light (2026-11-08) the stone read almost black, its strata and shingles lost: the baked colour map's darks are lifted
# (each channel to the power COLOUR_LIFT, so the slate goes from 20% to about 31% and the ochre hardly moves).
COLOUR_LIFT = 0.72


def lift_colour_map():
    img = next(i for i in bpy.data.images if i.filepath_raw.endswith(PET + "_color.png"))
    px = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(-1, 4)
    px[:, :3] = np.clip(px[:, :3], 0, 1) ** COLOUR_LIFT
    img.pixels.foreach_set(px.ravel())
    img.save()
    img.pack()


# ---------- the skeleton ----------
TRUNK = ["Head", "Seg1", "Seg2", "Body", "Seg4", "Seg5", "Seg6", "Seg7", "Seg8", "Seg9", "Tail"]
HEAD_Y = -0.47
ARM_F = (0.0, 0.17, 0.34, 0.51, 0.68, 0.84)


def trunk_y():
    return [HEAD_Y] + [float(y) for y in FLAP_Y] + [FAN_BASE.y]


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def skeleton():
    ys = trunk_y()
    at = {name: spine_at(float(spine_f(y))) for name, y in zip(TRUNK, ys)}
    bones = [("Root", V(0, 0, 0), None), ("Body", at["Body"], "Root")]
    bones += [("Seg2", at["Seg2"], "Body"), ("Seg1", at["Seg1"], "Seg2"), ("Head", at["Head"], "Seg1")]
    parent = "Body"
    for name in TRUNK[4:]:
        bones.append((name, at[name] if name != "Tail" else FAN_BASE.copy(), parent))
        parent = name
    for side, tag in ((1, "L"), (-1, "R")):
        for k in range(FLAPS):
            root, _ = flap_root(k, side)
            bones.append(("Flap%s%d" % (tag, k + 1), root, TRUNK[k + 1]))
        for j in range(len(FAN)):
            d, _, _, _ = fan_frame(j, side)
            bones.append(("Fan%s%d" % (tag, j + 1), FAN_BASE + V(side * 0.012, -0.006, 0.004 + 0.009 * (2 - j)), "Tail"))
        path = arm_path(side, 24)
        parent = "Head"
        for k, f in enumerate(ARM_F):
            bones.append(("Arm%s%d" % (tag, k + 1), path_at(path, f), parent))
            parent = "Arm%s%d" % (tag, k + 1)
        bones.append(("Stalk" + tag, stalk_path(side)[0].copy(), "Head"))
        bones.append(("Eye" + tag, eye_centre(side)[0], "Stalk" + tag))
    return armature(bones)


def flap_bone_weight(tag, y):
    """A flap's every point follows the flap bones by how far along the body it lies, so where two flaps overlap they move as one and never cut each other."""
    names = ["Flap%s%d" % (tag, k + 1) for k in range(FLAPS)]
    ys = list(FLAP_Y)
    if y <= ys[0]:
        return {names[0]: 1.0}
    if y >= ys[-1]:
        return {names[-1]: 1.0}
    for k in range(FLAPS - 1):
        if y <= ys[k + 1]:
            t = (y - ys[k]) / (ys[k + 1] - ys[k])
            t = t * t * (3 - 2 * t)
            return {names[k]: 1 - t, names[k + 1]: t}


def skin_weights(o):
    P = verts(o)
    ys = trunk_y()
    knots = [float(spine_f(y)) for y in ys]
    f, _ = nearest_on(SPINE, P)
    out = [chain_weight(TRUNK, knots, float(x)) for x in f]
    for side, tag in ((1, "L"), (-1, "R")):
        path = stalk_path(side, 10)
        g, d = nearest_on(path, P)
        for i in range(len(P)):
            if P[i, 0] * side > 0.075 and d[i] < stalk_radius(min(1.0, g[i])) + 0.006 and abs(P[i, 1] + 0.4) < 0.06:
                share = float(smooth(0.15, 0.6, g[i]))
                w = {k: v * (1 - share) for k, v in out[i].items()}
                w["Stalk" + tag] = w.get("Stalk" + tag, 0) + share
                out[i] = w
    return out


def bind_all(lows, rig, glows, owners):
    weigh(lows["Skin"], skin_weights(lows["Skin"]))
    rigid(lows["Shield"], "Head")
    for key in ("FlapsA", "FlapsB"):
        P = verts(lows[key])
        weigh(lows[key], [flap_bone_weight(tag, float(p[1])) for (tag, k), p in zip(META[key], P)])
    for key in ("FanA", "FanB"):
        P = verts(lows[key])
        out = []
        for (tag, j), p in zip(META[key], P):
            root = float(smooth(0.03, 0.1, (Vector(p) - FAN_BASE).length))      # the roots, where the blades crowd together, stay with the tail
            out.append({"Fan%s%d" % (tag, j + 1): root, "Tail": 1 - root} if root < 1 else {"Fan%s%d" % (tag, j + 1): 1.0})
        weigh(lows[key], out)
    names = {tag: ["Arm%s%d" % (tag, k + 1) for k in range(len(ARM_F))] for tag in ("L", "R")}
    weigh(lows["Arms"], [chain_weight(names[tag], ARM_F, f) for tag, f in META["Arms"]])
    weigh(lows["Eyes"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(lows["Eyes"])])
    for key, o in glows.items():
        P = verts(o)
        out = []
        for (kind, tag, idx), p in zip(owners[key], P):
            if kind == "Flap":
                out.append(flap_bone_weight(tag, float(p[1])))
            else:
                root = float(smooth(0.03, 0.1, (Vector(p) - FAN_BASE).length))
                out.append({"Fan%s%d" % (tag, idx + 1): root, "Tail": 1 - root} if root < 1 else {"Fan%s%d" % (tag, idx + 1): 1.0})
        weigh(o, out)
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateAbyssAnomalocaris uses. +X: what points forward lifts, what points back drops; +Y turns to its left; +Z rolls
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), move)


def flap_wave(phase, amp):
    """The metachronal wave: each flap a little behind the one in front. Up is a turn about the long axis, opposite on the two sides."""
    out = {}
    for k in range(FLAPS):
        a = amp * math.sin(phase - k * 0.42)
        out["FlapL%d" % (k + 1)] = game_turn(0, 0, a)
        out["FlapR%d" % (k + 1)] = game_turn(0, 0, -a)
    return out


def curl(k, spread=0.0):
    """The arms: k > 0 curls them tighter, k < 0 opens them out; spread swings them apart."""
    out = {}
    for tag, sign in (("L", 1), ("R", -1)):
        for i in range(len(ARM_F)):
            out["Arm%s%d" % (tag, i + 1)] = game_turn(-k * (0.15 + 0.1 * i), sign * spread * (1 if i == 0 else 0), 0)
    return out


def pose_library():
    return {
        "WaveA": flap_wave(0.0, 0.32), "WaveB": flap_wave(1.6, 0.32),
        "ArmsOpen": curl(-1.0, 0.25), "ArmsTight": curl(0.6),
        "Lunge": {**curl(-1.2, 0.35), "Head": game_turn(0.12, 0, 0), "Seg1": game_turn(0.05, 0, 0), "Seg7": game_turn(-0.1, 0, 0), "Seg8": game_turn(-0.15, 0, 0)},
        "Bend": {name: game_turn(0, 0.12 * math.sin(i * 0.9), 0) for i, name in enumerate(TRUNK[1:])},
        "Steer": {**{"Fan%s%d" % (t, j + 1): game_turn(0.35, 0, 0) for t in "LR" for j in range(3)}, "Tail": game_turn(0, 0.3, 0)},
        "Look": {"StalkL": game_turn(0.3, 0.4, 0), "StalkR": game_turn(0.3, -0.4, 0)},
    }


if __name__ == "__main__" and STAGE == "all":
    pieces, glows, data = build_hi()
    mat = hi_material(ao_distance=0.03, ao_share=0.4)
    for o in set(pieces.values()):
        o.data.materials.clear()
        o.data.materials.append(mat)
    show_glows(glows)
    stage_setup((0.30, 0.33, 0.42, 1))
    lows = build_low(data)
    unwrap(lows, [(None, 1.0)], {}, shape="CONCAVE", angle=50, texels=TEXELS, margin=0.006)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.12, 0.11, 0.14, 1), far=("Skin",), reach=(0.004, 0.012), far_reach=(0.008, 0.022),
             reaches={"Arms": (0.005, 0.014), "Eyes": (0.004, 0.01), "Shield": (0.004, 0.01)})
    lift_colour_map()
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for o in glows.values():
        HI.objects.unlink(o)
        GAME.objects.link(o)
    triangulate(glows)
    rig = skeleton()
    body = bind_all(lows, rig, glows, data["glow_owners"])
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", tuple(round(v, 3) for v in o.dimensions), flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(body.matrix_world @ v.co).z for v in body.data.vertices]
    print("Z range", round(min(zs), 4), round(max(zs), 4), flush=True)
    for side, tag in ((1, "L"), (-1, "R")):
        c, d = eye_centre(side)
        print("EYE", tag, tuple(round(v, 4) for v in c), flush=True)
    pose(rig, {})
    bpy.context.scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=3.4, size=640)
    lib = pose_library()
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    wide = (0.55, -0.7, 0.45, 3.2, VIEW_AT)
    side_v = (1, -0.1, 0.12, 2.6, (0, -0.25, -0.05))
    for name, view in (("WaveA", wide), ("WaveB", (0.2, 0.6, 0.35, 3.0, VIEW_AT)), ("ArmsOpen", side_v), ("ArmsTight", side_v), ("Lunge", side_v), ("Bend", (0, -0.02, 1, 3.6, VIEW_AT)), ("Steer", (0.6, 0.7, 0.4, 2.0, (0, 0.6, 0.05))), ("Look", (0.4, -0.85, 0.35, 1.3, (0, -0.45, 0.03)))):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.42, 3.2, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

