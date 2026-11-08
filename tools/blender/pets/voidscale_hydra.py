"""The Voidscale Hydra (Mythical, Void; Void Rift Egg, also in the Primordial Abyss Egg): "Cut one head and the void grows two in its place. Between its scales there is simply nothing."

A new creature. Not a serpent: a low, sprawling reptile on four splayed legs with three-clawed feet, a heavy tail curling to one side, and three necks rising from its
shoulders. The two outer necks are long and end in big viper heads, triangular, heavy-browed; the middle neck is shorter and forks into two small young heads, the two the void
grew where one was cut. Its scales are separate plates of polished black void glass, and between them there is simply nothing: a starry deep-blue void shows through every gap,
each plate's edge catching a thin bright-blue rim. Its eyes are glowing pale-blue slits under the brows, no eyeballs, no lids; each mouth hides a forked tongue of blue light.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/voidscale_hydra.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre, its feet on z = 0. +X is its left. The maps go to assets/pets/VoidRiftEgg/.

What touches what: legs, necks, heads, feet and claws are fused into one skin with the body; the eye slits lie on the heads; the tongues are hidden inside the heads at rest.
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
PET = "VoidscaleHydra"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "VoidRiftEgg")

# ---------- colours: the Void Rift Egg's black glass and blue void ----------
GLASS, GLASS_SHEEN, SCUTE = rgb(12, 12, 22), rgb(38, 36, 70), rgb(30, 27, 50)
VOID_DEEP, VOID_BLUE, RIM, STARLIGHT = rgb(8, 14, 52), rgb(24, 56, 170), rgb(70, 150, 255), rgb(225, 235, 255)
CLAW = rgb(176, 196, 230)

# ---------- the frame of it ----------
SPINE = catmull([V(0, -0.31, 0.2), V(0, -0.18, 0.205), V(0, 0.0, 0.2), V(0, 0.18, 0.19), V(0, 0.33, 0.165), V(0.01, 0.48, 0.13), V(0.045, 0.64, 0.095), V(0.1, 0.8, 0.07),
                 V(0.165, 0.93, 0.055), V(0.215, 1.03, 0.045)], 12)
P_W = ((0, 0.08), (0.04, 0.15), (0.12, 0.18), (0.25, 0.185), (0.38, 0.162), (0.48, 0.112), (0.6, 0.074), (0.75, 0.047), (0.9, 0.026), (1, 0.009))
P_T = ((0, 0.06), (0.06, 0.1), (0.2, 0.112), (0.38, 0.1), (0.5, 0.076), (0.65, 0.05), (0.8, 0.032), (1, 0.009))
P_B = ((0, 0.06), (0.06, 0.086), (0.2, 0.096), (0.38, 0.09), (0.5, 0.068), (0.65, 0.045), (0.8, 0.03), (1, 0.009))

LEGS = {      # shoulder or hip, elbow or knee, wrist or ankle, sole; for the left side (+X)
    "F": [V(0.13, -0.17, 0.17), V(0.26, -0.19, 0.165), V(0.295, -0.22, 0.055), V(0.3, -0.245, 0.017)],
    "B": [V(0.13, 0.26, 0.16), V(0.27, 0.235, 0.155), V(0.3, 0.285, 0.055), V(0.305, 0.27, 0.017)],
}
FOOT = (0.048, 0.062, 0.017)

NECKS = {     # each from its root in the shoulders up to where its head begins
    "L": [V(0.09, -0.25, 0.24), V(0.15, -0.36, 0.32), V(0.2, -0.43, 0.41), V(0.24, -0.49, 0.46), V(0.27, -0.55, 0.48)],
    "R": [V(-0.09, -0.25, 0.24), V(-0.16, -0.37, 0.3), V(-0.215, -0.46, 0.38), V(-0.25, -0.53, 0.42), V(-0.275, -0.59, 0.43)],
    "M": [V(0, -0.28, 0.25), V(0, -0.37, 0.32), V(0, -0.42, 0.36)],
}
FORKS = {     # the two young necks, from the fork at the middle neck's end
    "ML": [V(0, -0.42, 0.36), V(0.052, -0.47, 0.405), V(0.085, -0.525, 0.425)],
    "MR": [V(0, -0.42, 0.36), V(-0.055, -0.48, 0.395), V(-0.088, -0.54, 0.4)],
}
HEAD_SIZE = {"L": 1.0, "R": 1.0, "ML": 0.64, "MR": 0.64}
HEAD_LEN = 0.2
NECK_R = {"L": (0.07, 0.046), "R": (0.07, 0.046), "M": (0.066, 0.052), "ML": (0.032, 0.028), "MR": (0.032, 0.028)}
# the head's loft, from the back of the skull (0) to the tip of the snout (1): half-width, height above its axis, depth below it
H_W = ((0, 0.04), (0.12, 0.062), (0.3, 0.07), (0.5, 0.058), (0.72, 0.042), (0.9, 0.028), (1, 0.012))
H_T = ((0, 0.036), (0.15, 0.04), (0.4, 0.038), (0.7, 0.028), (0.9, 0.02), (1, 0.008))
H_B = ((0, 0.036), (0.15, 0.036), (0.4, 0.03), (0.7, 0.022), (0.9, 0.016), (1, 0.007))


def prof(knots, f):
    a = np.array(knots)
    return np.interp(f, a[:, 0], a[:, 1])


def spine_at(f):
    k = float(np.clip(f, 0, 1)) * (len(SPINE) - 1)
    i = min(int(k), len(SPINE) - 2)
    return SPINE[i].lerp(SPINE[i + 1], k - i)


def path_of(key, per=8):
    pts = NECKS.get(key) or FORKS.get(key)
    return catmull(pts, per)


def head_frame(key):
    """The head's frame: where it starts (the neck's end), forward (the neck's last run, turned toward the front and a little down), its left, its up."""
    pts = NECKS.get(key) or FORKS.get(key)
    e = pts[-1]
    t = (pts[-1] - pts[-2]).normalized()
    d = (t * 0.45 + V(0, -1, -0.3).normalized() * 0.55).normalized()
    left = V(0, 0, 1).cross(d).normalized()       # +X-ish when it faces -Y
    up = d.cross(left).normalized()
    return e, d, left, up


def oriented_ball(m, c, axes, radii, seg=40, rings=26):
    """An ellipsoid with these radii along these axes (left, forward, up)."""
    rot = Matrix((tuple(axes[0]), tuple(axes[1]), tuple(axes[2]))).transposed().to_4x4()
    bmesh.ops.create_uvsphere(m.bm, u_segments=seg, v_segments=rings, radius=1.0, matrix=Matrix.Translation(c) @ rot @ Matrix.Diagonal((radii[0], radii[1], radii[2], 1)))


def head_at(key, f_fwd, f_left, f_up):
    e, d, left, up = head_frame(key)
    S = HEAD_SIZE[key]
    return e + (d * f_fwd + left * f_left + up * f_up) * S


def build_head(m, key):
    """A viper's head, lofted along its own axis: flat on top, widest at the cheeks behind the eyes so it is a triangle from above, narrowing to a blunt snout; a ledge of brow over each eye."""
    e, d, left, up = head_frame(key)
    S = HEAD_SIZE[key]
    L = HEAD_LEN * S
    nt, rows = 40, 34
    a = np.linspace(-math.pi, math.pi, nt, endpoint=False)
    cs, sn = np.cos(a), np.sin(a)
    grid = []
    for i in range(rows):
        f = i / (rows - 1)
        w, t, b = float(prof(H_W, f)) * S, float(prof(H_T, f)) * S, float(prof(H_B, f)) * S
        # the brow: a ledge standing above the top's edges, from the cheeks to the front of the eye
        brow = 0.009 * S * math.exp(-((f - 0.42) / 0.17) ** 2)
        x = w * np.sign(cs) * np.abs(cs) ** 0.6
        z = np.where(sn > 0, t * np.abs(sn) ** 0.45 + brow * np.exp(-((np.abs(cs) - 0.72) / 0.16) ** 2), -b * np.abs(sn) ** 0.7)
        c = e - d * (0.02 * S) + d * (L * f)
        grid.append([m.bm.verts.new(c + left * float(xx) + up * float(zz)) for xx, zz in zip(x, z)])
    back = m.bm.verts.new(e - d * (0.03 * S))
    tip = m.bm.verts.new(e - d * (0.02 * S) + d * (L + 0.006 * S))
    for j in range(nt):
        j2 = (j + 1) % nt
        m.bm.faces.new((back, grid[0][j2], grid[0][j]))
        for i in range(rows - 1):
            m.bm.faces.new((grid[i][j], grid[i][j2], grid[i + 1][j2], grid[i + 1][j]))
        m.bm.faces.new((grid[-1][j], grid[-1][j2], tip))


def build_skin(name, coll):
    """Body and tail, legs and feet, necks and heads, all fused into one skin."""
    # the body and tail: a loft round the spine
    rows, nt = 170, 72
    a = np.linspace(-math.pi, math.pi, nt, endpoint=False)
    cs, sn = np.cos(a), np.sin(a)
    m = Mesh()
    bm = m.bm
    grid = []
    for i in range(rows):
        f = i / (rows - 1)
        p = spine_at(f)
        w, t, b = float(prof(P_W, f)), float(prof(P_T, f)), float(prof(P_B, f))
        x = w * np.sign(cs) * np.abs(cs) ** 0.8
        z = np.where(sn > 0, t * np.abs(sn) ** 0.9, -b * np.abs(sn) ** 0.8)
        # the tail is round: let its rings follow the spine's turn as well as its rise
        tan = (spine_at(min(1.0, f + 0.01)) - spine_at(max(0.0, f - 0.01))).normalized()
        side = V(0, 0, 1).cross(tan).normalized()
        grid.append([bm.verts.new(p - side * float(xx) + V(0, 0, float(zz))) for xx, zz in zip(x, z)])
    front = bm.verts.new(spine_at(0) - V(0, 0.02, 0))
    back = bm.verts.new(spine_at(1) + (spine_at(1) - spine_at(0.99)).normalized() * 0.006)
    for j in range(nt):
        j2 = (j + 1) % nt
        bm.faces.new((front, grid[0][j2], grid[0][j]))
        for i in range(rows - 1):
            bm.faces.new((grid[i][j], grid[i][j2], grid[i + 1][j2], grid[i + 1][j]))
        bm.faces.new((grid[-1][j], grid[-1][j2], back))
    # legs: a heavy upper limb sprawled out to the elbow or knee, the lower limb down to a splayed foot of three long toes, each ending in a claw
    for side in (1, -1):
        for leg in ("F", "B"):
            pts = [mir(p, side) for p in LEGS[leg]]
            path = catmull(pts, 8)
            m.tube(path, lambda f: 0.052 - 0.022 * f + 0.006 * math.exp(-((f - 0.4) / 0.1) ** 2), sides=24)
            mid = pts[0].lerp(pts[1], 0.45)
            out = (pts[1] - pts[0]).normalized()
            oriented_ball(m, mid + V(0, 0, 0.006), (out, V(0, 1, 0).cross(out).normalized() if abs(out.y) < 0.9 else V(1, 0, 0), V(0, 0, 1)), (0.075, 0.05, 0.05), 32, 20)   # the muscle of the upper limb
            sole = pts[-1]
            m.ball(sole + V(0, -0.006, 0.002), (0.038, 0.042, 0.016), 32, 18)
            for spread in (-0.5, 0.0, 0.5):
                d = V(math.sin(spread) * side, -math.cos(spread), 0).normalized()
                base = sole + V(0, -0.006, 0.006)
                toe = [base, base + d * 0.035 + V(0, 0, 0.006), base + d * 0.062 + V(0, 0, 0.003)]
                m.tube(catmull(toe, 4), lambda f: 0.0125 - 0.003 * f, sides=14)
                tip = toe[-1]
                claw = [tip + d * (0.024 * t) + V(0, 0, -0.012 * t * t + 0.003 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 7)]
                m.tube(claw, lambda f: 0.0085 * (1 - f) ** 0.9 + 0.0011, sides=12)
    # necks, the fork and the heads
    for key in ("L", "R", "M", "ML", "MR"):
        r0, r1 = NECK_R[key]
        m.tube(path_of(key), lambda f, r0=r0, r1=r1: r0 + (r1 - r0) * f, sides=28)
    m.ball(NECKS["M"][-1], (0.06, 0.058, 0.056), 32, 20)          # the knot where the middle neck forks
    for key in HEAD_SIZE:
        build_head(m, key)
    o = m.finish(name, coll)         # (every part's faces turned outward before the remesh reads them)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.003, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- the scales: which part each point of the skin belongs to, and where it lies on that part ----------
def part_paths():
    """(name, path, scale cell size in metres, cells round it, radius at its start and end) for every part the scales follow."""
    out = [("Body", SPINE, 0.034, 32, None)]
    for key in ("L", "R", "M", "ML", "MR"):
        r0, r1 = NECK_R[key]
        out.append(("Neck" + key, path_of(key, 6), 0.024 * (0.72 if key in FORKS else 1.0), 18 if key not in FORKS else 12, (r0, r1)))
    for side, tag in ((1, "L"), (-1, "R")):
        for leg in ("F", "B"):
            out.append(("Leg" + leg + tag, catmull([mir(p, side) for p in LEGS[leg]], 6), 0.02, 12, (0.05, 0.03)))
    for key in HEAD_SIZE:
        e, d, left, up = head_frame(key)
        S = HEAD_SIZE[key]
        out.append(("Head" + key, [e - d * (0.02 * S) + d * (HEAD_LEN * S * t) for t in np.linspace(0, 1, 12)], 0.03 * S, 10 if S > 0.8 else 8, None))
    return out


def frames_of(path):
    fr = []
    for i in range(len(path)):
        tan = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = V(0, 0, 1).cross(tan)
        side = side.normalized() if side.length > 1e-6 else V(1, 0, 0)
        fr.append((tan, side, tan.cross(side).normalized()))
    return fr


def scale_coords(P):
    """Per vertex: its part, the distance along it, the angle round it (0..1), and that part's cell size and count round."""
    parts = part_paths()
    best = np.full(len(P), 1e9)
    which = np.zeros(len(P), dtype=np.int64)
    along = np.zeros(len(P))
    for k, (name, path, cell, around, radii) in enumerate(parts):
        f, d = nearest_on(path, P)
        if radii is not None:       # a thin part claims only what lies near its own surface
            r = radii[0] + (radii[1] - radii[0]) * f
            d = d / np.maximum(r, 1e-3) * 0.06
        elif name.startswith("Head"):
            d = d * 0.8
        better = d < best
        best = np.where(better, d, best)
        which = np.where(better, k, which)
        along = np.where(better, f, along)
    # every point inside a head's own shape is the head's, however near its neck runs
    names = [p[0] for p in parts]
    for key in HEAD_SIZE:
        e, d, left, up = head_frame(key)
        S = HEAD_SIZE[key]
        L = HEAD_LEN * S
        rel = P - np.array(tuple(e - d * (0.02 * S)))
        f = rel @ np.array(tuple(d)) / L
        lat = np.abs(rel @ np.array(tuple(left)))
        ver = rel @ np.array(tuple(up))
        fc = np.clip(f, 0, 1)
        w = np.array([float(prof(H_W, x)) for x in fc]) * S
        t = np.array([float(prof(H_T, x)) for x in fc]) * S
        b = np.array([float(prof(H_B, x)) for x in fc]) * S
        inside = (f > -0.04) & (f < 1.08) & (lat < w * 1.25 + 0.006) & (ver < t * 1.5 + 0.014) & (ver > -b * 1.4 - 0.006)
        k = names.index("Head" + key)
        which = np.where(inside, k, which)
        along = np.where(inside, np.clip(f, 0, 1) * (len(parts[k][1]) - 1) / (len(parts[k][1]) - 1), along)
    s_m = np.zeros(len(P))
    theta = np.zeros(len(P))
    radius = np.full(len(P), 0.05)
    cells = np.zeros(len(P))
    counts = np.zeros(len(P))
    for k, (name, path, cell, around, radii) in enumerate(parts):
        mine = which == k
        if not mine.any():
            continue
        length = sum((path[i + 1] - path[i]).length for i in range(len(path) - 1))
        fr = frames_of(path)
        idx = np.clip(np.round(along[mine] * (len(path) - 1)).astype(np.int64), 0, len(path) - 1)
        pts = np.array([tuple(path[i]) for i in idx])
        sides = np.array([tuple(fr[i][1]) for i in idx])
        ups = np.array([tuple(fr[i][2]) for i in idx])
        rel = P[mine] - pts
        theta[mine] = (np.arctan2((rel * ups).sum(1), (rel * sides).sum(1)) / TAU) % 1.0
        radius[mine] = np.hypot((rel * ups).sum(1), (rel * sides).sum(1))
        s_m[mine] = along[mine] * length
        cells[mine] = cell
        counts[mine] = around
    return which, names, s_m, theta, cells, counts, radius


def scale_field(P, Nn):
    """Per vertex: plate (1 on a plate, 0 in a gap), rim (the plate's bright edge), its row's random, and whether it is belly scute."""
    which, names, s_m, theta, cells, counts, radius = scale_coords(P)
    U = s_m / cells
    Vv = theta * counts
    row = np.floor(U)
    fu = U - row
    # diamonds, edge to edge, like a snake's: each point belongs to its nearest scale centre, measured so a centre's neighbours in its own row and in the
    # rows either side are equally far; the void is where the two nearest are nearly equal, a thin even line round every plate
    d1 = np.full(len(P), 9.0)
    d2 = np.full(len(P), 9.0)
    col_best = np.zeros(len(P))
    row_best = np.zeros(len(P))
    for dr in (-1, 0, 1):
        r = row + dr
        shift = 0.5 * (r % 2)
        c0 = np.floor(Vv - shift)
        for dc in (-1, 0, 1):
            c = c0 + dc
            cu, cv = r + 0.5, c + 0.5 + shift
            d = 0.5 * np.abs(U - cu) + np.abs(Vv - cv)
            nearer = d < d1
            d2 = np.where(nearer, d1, np.minimum(d2, d))
            row_best = np.where(nearer, r, row_best)
            col_best = np.where(nearer, c, col_best)
            d1 = np.where(nearer, d, d1)
    edge = d2 - d1
    # the void line about 3 mm wide everywhere, whatever the plate's size: a unit of `edge` is one plate's width round the part
    across = np.maximum(TAU * radius / counts, 0.004)
    g = np.clip(0.0016 / across, 0.05, 0.3)
    plate = smooth(g, g * 1.6, edge)
    rim = (1 - smooth(g * 1.6, g * 1.6 + 0.0022 / across, edge)) * plate      # a rim about 2 mm wide inside each plate's edge
    row, col = row_best, col_best
    # beneath the body and the necks: broad scutes across, in rows
    is_body_or_neck = np.array([names[w].startswith(("Body", "Neck")) for w in which])
    belly = is_body_or_neck & (Nn[:, 2] < -0.45)
    scute = 1 - smooth(0.38, 0.47, np.abs(fu - 0.5))
    plate = np.where(belly, scute, plate)
    rim = np.where(belly, smooth(0.3, 0.38, np.abs(fu - 0.5)) * scute * 0.6, rim)
    rnd = hash01(row.astype(np.int64), col.astype(np.int64), which.astype(np.int64), 7)
    return plate, rim, rnd, belly, which, names


CLAWS = []


def claw_paths():
    if not CLAWS:
        for side in (1, -1):
            for leg in ("F", "B"):
                sole = mir(LEGS[leg][-1], side)
                for spread in (-0.5, 0.0, 0.5):
                    d = V(math.sin(spread) * side, -math.cos(spread), 0).normalized()
                    tip = sole + V(0, -0.006, 0.006) + d * 0.062 + V(0, 0, 0.003)
                    CLAWS.append([tip + d * (0.024 * t) + V(0, 0, -0.012 * t * t + 0.003 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 7)])
    return CLAWS


def mouth_lines():
    """Each head's mouth: a line along each side, from the snout's tip back to the corner of the jaw, just below its axis."""
    lines = []
    for key in HEAD_SIZE:
        e, d, left, up = head_frame(key)
        S = HEAD_SIZE[key]
        for side in (1, -1):
            pts = []
            for f in np.linspace(0.42, 0.99, 12):
                w = float(prof(H_W, f)) * S
                c = e - d * (0.02 * S) + d * (HEAD_LEN * S * f)
                pts.append(c + left * (side * w * 0.97) + up * (-0.005 * S))
            lines.append(pts)
    return lines


def eye_spots():
    """(head, side, centre, along) of every eye: on the head's side under the brow, a little behind the middle."""
    out = []
    for key in HEAD_SIZE:
        e, d, left, up = head_frame(key)
        S = HEAD_SIZE[key]
        f = 0.44
        w, t = float(prof(H_W, f)) * S, float(prof(H_T, f)) * S
        c = e - d * (0.02 * S) + d * (HEAD_LEN * S * f)
        for side in (1, -1):
            out.append((key, side, c + left * (side * w * 0.9) + up * (t * 0.32), d))
    return out


def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    plate, rim, rnd, belly, which, names = scale_field(P, Nn)
    # the void between the plates: deep blue with a scatter of stars
    cloud = fbm(P, 9.0, 4, 3)
    void = mix(VOID_DEEP, VOID_BLUE, smooth(0.35, 0.8, cloud))
    # a few stars, single specks, only in the void
    twinkle = np.random.default_rng(41).random(len(P))
    stars = (twinkle > 0.975) * (1 - plate)
    void = mix(void, STARLIGHT, stars * 0.9)
    glass = mix(GLASS, GLASS_SHEEN, smooth(0.45, 0.85, fbm(P, 14.0, 3, 5)) * (0.3 + 0.35 * rnd))      # each plate its own depth of sheen
    glass = np.where(belly[:, None], mix(SCUTE, GLASS_SHEEN, 0.25 * rnd), glass)
    col = mix(void, glass, plate)
    col = mix(col, RIM, rim * np.where(belly, 0.45, 0.75))
    rough = 0.65 - 0.53 * plate + 0.1 * rim
    # the claws: pale glass
    claw = np.zeros(len(P))
    for path in claw_paths():
        _, d = nearest_on(path, P)
        claw = np.maximum(claw, 1 - smooth(0.007, 0.011, d))
    col = mix(col, CLAW, claw)
    rough = rough * (1 - claw) + 0.18 * claw
    # the mouths: a thin line of void along each jaw
    mouth = np.zeros(len(P))
    for line in mouth_lines():
        _, d = nearest_on(catmull(line, 3), P)
        mouth = np.maximum(mouth, 1 - smooth(0.0012, 0.0032, d))
    col = mix(col, VOID_DEEP * 0.5, mouth)
    # under each eye a shallow socket of void, so the slit sits in shadow
    socket = np.zeros(len(P))
    for key, side, c, d in eye_spots():
        socket = np.maximum(socket, 1 - smooth(0.012 * HEAD_SIZE[key], 0.022 * HEAD_SIZE[key], np.linalg.norm(P - np.array(tuple(c)), axis=1)))
    col = mix(col, VOID_DEEP, socket * 0.8)
    # relief: each plate a low dome, the gaps sunk, the mouth a groove, the sockets a hollow
    relief = 0.0016 * plate - 0.0012 * (1 - plate) - 0.002 * mouth - 0.003 * socket
    set_verts(o, P + Nn * relief[:, None])
    paint(o, col, rough)


# ---------- the light: eye slits and forked tongues, one Neon piece per head ----------
LIGHT_HEX = "5aa0ff"


def slit(m, tree, c, d, side_axis, size):
    """An eye: a thin almond of light lying on the head's surface, long along the head."""
    hit = tree.ray_cast(c + side_axis * 0.05, -side_axis, 0.1)
    loc, nrm = (hit[0], hit[1]) if hit[0] else (c, side_axis)
    along = (d - nrm * d.dot(nrm)).normalized()
    across = nrm.cross(along).normalized()
    n = 9
    top, bot = [], []
    for k in range(n):
        t = k / (n - 1)
        x = (t - 0.5) * 0.034 * size
        w = 0.0042 * size * math.sin(math.pi * t) ** 0.8 + 0.0004
        bend = -0.002 * size * math.sin(math.pi * t)
        p = loc + nrm * 0.0016 + along * x + across * bend      # 1.6 mm off the skin: clear of it, yet touching it for QA's contact test
        top.append(m.bm.verts.new(p + across * w))
        bot.append(m.bm.verts.new(p - across * w))
    flip = (along.cross(-across)).dot(nrm) < 0         # every face of the slit turned the same way, toward the outside
    for k in range(n - 1):
        q = [top[k], top[k + 1], bot[k + 1], bot[k]]
        m.bm.faces.new(list(reversed(q)) if flip else q)


def tongue_path(key):
    e, d, left, up = head_frame(key)
    S = HEAD_SIZE[key]
    L = HEAD_LEN * S
    base = e - d * (0.02 * S) + d * (0.12 * L) - up * (0.004 * S)
    stem = [base + d * (0.68 * L * t) for t in np.linspace(0, 1, 6)]
    end = stem[-1]
    forks = [[end - d * (0.01 * L) + d * (0.14 * L * t) + left * (side * (0.012 * L + 0.05 * L * t ** 0.9)) for t in np.linspace(0, 1, 5)] for side in (1, -1)]
    return stem, forks


def build_lights(tree, coll, low=False):
    out, owners = {}, {}
    for key in HEAD_SIZE:
        m = Mesh()
        owner = []
        e, d, left, up = head_frame(key)
        S = HEAD_SIZE[key]
        for k2, side, c, dd in eye_spots():
            if k2 != key:
                continue
            before = len(m.bm.verts)
            slit(m, tree, c, d, left * side, S)
            m.bm.verts.ensure_lookup_table()
            owner += ["Head" + key] * (len(m.bm.verts) - before)
        slits = m.finish(N + "Slits" + key, coll, smooth_shade=False, recalc=False)
        stem, forks = tongue_path(key)
        mt = Mesh()
        mt.tube(stem, lambda t: 0.0042 * S, sides=6 if low else 10)
        for fork in forks:
            mt.tube(fork, lambda t: 0.0036 * S * (1 - 0.7 * t), sides=6 if low else 10)
        tongue = mt.finish(N + "Tongue" + key, coll, smooth_shade=False)
        owner += ["Tongue" + key] * len(tongue.data.vertices)
        bm = bmesh.new()
        bm.from_mesh(slits.data)
        bm.from_mesh(tongue.data)
        me = bpy.data.meshes.new(N + "Light" + key + "_Glow_" + LIGHT_HEX)
        bm.to_mesh(me)
        bm.free()
        for o in (slits, tongue):
            bpy.data.objects.remove(o, do_unlink=True)
        o = bpy.data.objects.new(me.name, me)
        coll.objects.link(o)
        out["Light" + key] = o
        owners["Light" + key] = owner
    return out, owners


def show_glows(glows):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        h = LIGHT_HEX
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 2.0
        o.data.materials.append(mat)
        o.visible_shadow = False


def build_hi(clay=False):
    pieces, data = {}, {}
    skin = build_skin(N + "SkinHi", HI)
    data["SkinBase"] = bpy.data.objects.new(N + "SkinBase", skin.data.copy())
    HI.objects.link(data["SkinBase"])
    data["SkinBase"].hide_render = True
    pieces["Skin"] = skin
    glows, data["light_owners"] = build_lights(tree_of(skin), HI)
    if not clay:
        paint_skin(skin)
    return pieces, glows, data


VIEWS = [(0, -1, 0.15), (0.62, -0.72, 0.35), (1, 0, 0.12), (0, 1, 0.25), (-0.62, 0.62, 0.45), (-0.62, -0.72, 0.3), (0, -0.02, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, -0.05, 0.24)
FACE_AT = (0, -0.6, 0.44)
EXTRA = [(0, -1, 0.1, 1.0, FACE_AT), (0.75, -0.6, 0.2, 0.8, (0.28, -0.63, 0.48)), (1, -0.15, 0.08, 0.65, (0.29, -0.64, 0.48)), (0.2, -0.95, 0.35, 0.55, (0.0, -0.58, 0.42)),
         (0.35, -0.5, 0.75, 0.6, (0.28, -0.63, 0.5)), (1, 0.2, 0.2, 1.0, (0.29, -0.02, 0.08)), (0.3, 0.9, 0.45, 1.4, (0.1, 0.6, 0.1))]


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
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=3.0, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
def build_low(data):
    skin = decimated(data["SkinBase"], N + "SkinLow", 7600)
    bm = bmesh.new()
    bm.from_mesh(skin.data)
    seen, stray = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        island, stack = [], [v]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            island.append(x)
            stack += [e.other_vert(x) for e in x.link_edges]
        if len(island) < 20:
            stray += island
    bmesh.ops.delete(bm, geom=stray, context="VERTS")
    bm.to_mesh(skin.data)
    bm.free()
    print("SKIN stray specks removed", len(stray), "verts", flush=True)
    skin.data.polygons.foreach_set("use_smooth", [True] * len(skin.data.polygons))
    print("SKIN decimated gap", round(surface_gap(skin, tree_of(data["SkinBase"])), 4), flush=True)
    lows = {"Skin": skin}
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
BODY_CHAIN = ["Chest", "Body", "Hips", "Tail1", "Tail2", "Tail3", "Tail4", "Tail5"]
BODY_F = (0.04, 0.17, 0.36, 0.47, 0.59, 0.71, 0.83, 0.94)
NECK_F = (0.0, 0.3, 0.6, 0.86)
LEG_F = (0.0, 0.34, 0.67)


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def neck_bones(key):
    if key in ("L", "R"):
        return ["Neck%s%d" % (key, k + 1) for k in range(4)], NECK_F
    if key == "M":
        return ["NeckM1", "NeckM2"], (0.0, 0.55)
    return ["Fork%s1" % key[1], "Fork%s2" % key[1]], (0.0, 0.5)


def skeleton():
    bones = [("Root", V(0, 0, 0), None), ("Body", spine_at(BODY_F[1]), "Root"), ("Chest", spine_at(BODY_F[0]), "Body"), ("Hips", spine_at(BODY_F[2]), "Body")]
    parent = "Hips"
    for name, f in zip(BODY_CHAIN[3:], BODY_F[3:]):
        bones.append((name, spine_at(f), parent))
        parent = name
    for side, tag in ((1, "L"), (-1, "R")):
        for leg, root in (("F", "Chest"), ("B", "Hips")):
            pts = [mir(p, side) for p in LEGS[leg]]
            bones += [("Upper%s%s" % (leg, tag), pts[0], root), ("Lower%s%s" % (leg, tag), pts[1], "Upper%s%s" % (leg, tag)), ("Foot%s%s" % (leg, tag), pts[2], "Lower%s%s" % (leg, tag))]
    for key in ("L", "R", "M"):
        names, fs = neck_bones(key)
        path = path_of(key)
        par = "Chest"
        for name, f in zip(names, fs):
            bones.append((name, path_at(path, f), par))
            par = name
        if key != "M":
            e, d, left, up = head_frame(key)
            bones += [("Head" + key, e.copy(), par), ("Tongue" + key, tongue_path(key)[0][0], "Head" + key)]
    for key in ("ML", "MR"):
        names, fs = neck_bones(key)
        path = path_of(key)
        par = "NeckM2"
        for name, f in zip(names, fs):
            bones.append((name, path_at(path, f), par))
            par = name
        e, d, left, up = head_frame(key)
        bones += [("Head" + key, e.copy(), par), ("Tongue" + key, tongue_path(key)[0][0], "Head" + key)]
    return armature(bones)


def torso_inside(P):
    """Per vertex: how far out of the torso's own outline it lies (1 on its surface), and where along the spine."""
    f, _ = nearest_on(SPINE, P)
    out = np.zeros(len(P))
    for i in range(len(P)):
        c = spine_at(float(f[i]))
        tan = (spine_at(min(1.0, f[i] + 0.01)) - spine_at(max(0.0, f[i] - 0.01))).normalized()
        side = V(0, 0, 1).cross(tan).normalized()
        rel = Vector(P[i]) - c
        w, t, b = float(prof(P_W, f[i])), float(prof(P_T, f[i])), float(prof(P_B, f[i]))
        z = rel.z
        out[i] = math.hypot(rel.dot(side) / w, z / (t if z > 0 else b))
    return out, f


def part_weight(name, f):
    if name.startswith("Leg"):
        leg, tag = name[3], name[4]
        return chain_weight(["Upper%s%s" % (leg, tag), "Lower%s%s" % (leg, tag), "Foot%s%s" % (leg, tag)], LEG_F, f)
    if name.startswith("Neck"):
        bones, fs = neck_bones(name[4:])
        return chain_weight(bones, fs, f)
    key = name[4:]
    bones, fs = neck_bones(key)
    share = float(smooth(0.0, 0.12, f))
    return {"Head" + key: share, bones[-1]: 1 - share} if share < 1 else {"Head" + key: 1.0}


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


def skin_weights(o):
    P = verts(o)
    which, names, s_m, theta, cells, counts, radius = scale_coords(P)
    parts = part_paths()
    lengths = [sum((p[1][i + 1] - p[1][i]).length for i in range(len(p[1]) - 1)) for p in parts]
    rn, fs = torso_inside(P)
    fork_paths = {k: path_of(k, 8) for k in ("ML", "MR")}
    _, d_ml = nearest_on(fork_paths["ML"], P)
    _, d_mr = nearest_on(fork_paths["MR"], P)
    fork_at = NECKS["M"][-1]
    m_out = (NECKS["M"][-1] - NECKS["M"][-2]).normalized()
    neck_paths = {k: path_of(k, 8) for k in ("L", "M", "R")}
    neck_f, neck_d = {}, {}
    for k, path in neck_paths.items():
        neck_f[k], neck_d[k] = nearest_on(path, P)
    out = []
    for i in range(len(P)):
        name = names[which[i]]
        f = s_m[i] / lengths[which[i]]
        body = chain_weight(BODY_CHAIN, BODY_F, float(fs[i]))
        if name == "Body":
            out.append(body)
            continue
        past_fork = name in ("NeckM", "HeadML", "HeadMR") and (Vector(P[i]) - fork_at).dot(m_out) > -0.005 and min(d_ml[i], d_mr[i]) < 0.06
        if name in ("NeckML", "NeckMR") or (name == "NeckM" and past_fork):
            # between the two young necks: both share the crotch, so it follows each of them
            fl = float(nearest_on(fork_paths["ML"], P[i:i + 1])[0][0])
            fr = float(nearest_on(fork_paths["MR"], P[i:i + 1])[0][0])
            t = float(smooth(-0.025, 0.025, d_ml[i] - d_mr[i]))
            w = blend(part_weight("NeckML", fl), part_weight("NeckMR", fr), t)
            near_fork = 1 - float(smooth(0.035, 0.07, (Vector(P[i]) - fork_at).length))
            w = blend(w, {"NeckM2": 1.0}, near_fork)
        elif name in ("NeckL", "NeckR", "NeckM"):
            # where two necks run fused near their roots, a point nearly as close to a neighbour as to its own neck shares the two, so the web between them follows both
            order = sorted(("L", "M", "R"), key=lambda k: neck_d[k][i])
            a, b = order[0], order[1]
            t = float(smooth(-0.03, 0.0, neck_d[a][i] - neck_d[b][i])) * 0.5
            w = blend(part_weight("Neck" + a, float(neck_f[a][i])), part_weight("Neck" + b, float(neck_f[b][i])), t)
        else:
            w = part_weight(name, f)
        # a point still inside the torso's outline stays with the body; out of it, it goes over to its leg or neck
        if name.startswith(("Leg", "NeckL", "NeckR", "NeckM")) and name not in ("NeckML", "NeckMR"):
            stay = 1 - float(smooth(0.95, 1.3, rn[i]))
            w = blend(w, body, stay)
        out.append(w)
    return out


def bind_all(lows, rig, glows, owners):
    weigh(lows["Skin"], skin_weights(lows["Skin"]))
    for key, o in glows.items():
        weigh(o, [{b: 1.0} for b in owners[key]])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateVoidscaleHydra uses. +X lifts what points forward and drops what points back; +Y turns to its left
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), move)


def tongue_out(keys, k=1.0):
    out = {}
    for key in keys:
        e, d, left, up = head_frame(key)
        L = HEAD_LEN * HEAD_SIZE[key]
        out["Tongue" + key] = ((0, 0, 1), 0, tuple(d * (0.42 * L * k)))
    return out


def pose_library():
    return {
        "Rear": {"Chest": game_turn(0.25, 0, 0), "NeckL1": game_turn(0.35, 0, 0), "NeckR1": game_turn(0.35, 0, 0), "NeckM1": game_turn(0.3, 0, 0), "NeckL3": game_turn(-0.2, 0, 0), "NeckR3": game_turn(-0.2, 0, 0)},
        "Sway": {"NeckL1": game_turn(0, 0.35, 0), "NeckL2": game_turn(0, 0.25, 0), "NeckR1": game_turn(0, -0.3, 0), "NeckR2": game_turn(0, -0.2, 0), "ForkL1": game_turn(0.2, 0.3, 0), "ForkR1": game_turn(-0.15, -0.3, 0)},
        "Look": {"HeadL": game_turn(0.2, 0.5, 0), "HeadR": game_turn(-0.15, -0.5, 0), "HeadML": game_turn(0, -0.6, 0), "HeadMR": game_turn(0, 0.6, 0)},
        "Tongues": tongue_out(HEAD_SIZE),
        "Stride": {"UpperFL": game_turn(0, 0.45, 0), "LowerFL": game_turn(0.3, 0, 0), "UpperFR": game_turn(0, 0.45, 0), "UpperBL": game_turn(0, -0.4, 0), "UpperBR": game_turn(0, -0.4, 0), "Body": game_turn(0, 0.1, 0.05)},
        "TailCurl": {"Tail%d" % k: game_turn(0, 0.22, 0) for k in range(1, 6)},
        "Strike": {"Chest": game_turn(-0.1, 0, 0), "NeckL1": game_turn(-0.3, 0, 0), "NeckL3": game_turn(0.4, 0, 0), "NeckR1": game_turn(-0.3, 0, 0), "NeckR3": game_turn(0.4, 0, 0), "HeadL": game_turn(-0.3, 0, 0), "HeadR": game_turn(-0.3, 0, 0), **tongue_out(("L", "R"))},
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
    unwrap(lows, [(None, 1.0)], {}, shape="CONCAVE", angle=50, margin=0.004)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.03, 0.04, 0.12, 1), far=("Skin",), reach=(0.006, 0.016), far_reach=(0.007, 0.02))
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for o in glows.values():
        HI.objects.unlink(o)
        GAME.objects.link(o)
    triangulate(glows)
    rig = skeleton()
    body = bind_all(lows, rig, glows, data["light_owners"])
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(body.matrix_world @ v.co).z for v in body.data.vertices]
    lo, hi = min(zs), max(zs)
    print("Z range", round(lo, 4), round(hi, 4), "SOLE metres below the box middle", round((hi + lo) / 2 - lo, 4), flush=True)
    for key in HEAD_SIZE:
        e, d, left, up = head_frame(key)
        print("HEAD", key, "forward in the game's axes", (round(-d.x, 4), round(d.z, 4), round(d.y, 4)), "tongue reach", round(0.42 * HEAD_LEN * HEAD_SIZE[key], 4), flush=True)
    pose(rig, {})
    bpy.context.scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=3.0, size=640)
    lib = pose_library()
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    wide = (0.6, -0.7, 0.4, 2.8, VIEW_AT)
    face = (0.35, -0.9, 0.3, 1.2, FACE_AT)
    for name, view in (("Rear", wide), ("Sway", (0, -0.2, 1, 2.6, VIEW_AT)), ("Look", face), ("Tongues", face), ("Stride", (0, -0.1, 1, 2.6, VIEW_AT)), ("TailCurl", (0, 0.1, 1, 3.0, (0.1, 0.4, 0))), ("Strike", (1, -0.2, 0.2, 2.6, VIEW_AT))):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.35, 2.8, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)

