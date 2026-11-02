"""Shared building blocks for the guardians (run inside Blender): shapes authored in Roblox studs
(x right, y up, the guardian's front toward -Z, its feet on the ground at y = 0), the bake of each
segment onto its own game mesh, and the FBX with its pieces report.

A guardian is built from rigid segments that the game turns with Motor6D joints; each segment's
high-detail objects are baked onto one game mesh (egg_bake.py), its glowing parts are separate
Neon pieces named <Guardian>_<Segment>_Glow_<hex>.
"""
import json
import math
import os

import bmesh
import bpy
from mathutils import Euler, Vector
from mathutils.bvhtree import BVHTree

import egg_bake as B
import egg_hi as Hm
import egg_kit as K

W = K.W
V = Vector
TAU = 2 * math.pi
OUT_DIR = os.path.join(W.REPO, "assets", "guardians")


# ---------- shapes ----------
def blob(name, coll, mat, lobes, voxel=0.12, smooth=0.6, rough=0.05, chisel="LionChisel"):
    """A solid mass: ellipsoid lobes [(centre, radii, rotation degrees or None)], merged by a voxel
    remesh, smoothed, and roughened by a Voronoi displacement (`chisel` names its texture)."""
    bm = bmesh.new()
    for centre, radii, rot in lobes:
        made = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        r = Euler([math.radians(a) for a in (rot or (0, 0, 0))]).to_matrix()
        for v in made["verts"]:
            p = V((v.co.x * radii[0], v.co.y * radii[1], v.co.z * radii[2]))
            p = r @ p
            v.co = W.rb(centre[0] + p.x, centre[1] + p.y, centre[2] + p.z)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    tex = bpy.data.textures.get(chisel) or bpy.data.textures.new(chisel, "VORONOI")
    tex.noise_scale = 0.9
    Hm.apply_modifiers(o, [("REMESH", {"mode": "VOXEL", "voxel_size": voxel}),
                           ("SMOOTH", {"factor": smooth, "iterations": 6}),
                           ("DISPLACE", {"texture": tex, "strength": rough, "mid_level": 0.5, "texture_coords": "GLOBAL"})])
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def capsule_lobes(a, b, r0, r1, n=5):
    """Ellipsoid lobes along a limb from a to b, its radius going from r0 to r1."""
    a, b = V(a), V(b)
    out = []
    for i in range(n):
        t = i / (n - 1)
        c = a.lerp(b, t)
        r = r0 + (r1 - r0) * t
        out.append((tuple(c), (r, r * 1.25, r), None))
    return out


def surface_down(obj, x, z, from_y=40.0):
    """Where a ray straight down at (x, z) meets obj, and the surface normal there (Roblox space)."""
    tree = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    hit, normal, _, _ = tree.ray_cast(W.rb(x, from_y, z), V((0, 0, -1)))
    if hit is None:
        return None, None
    return V(K.rb_inv(*hit)), V(K.rb_inv(*normal))


def surface_along(obj, near, normal, reach=6.0):
    """Where the line through `near` along `normal` leaves obj's surface outward (Roblox space): cast
    back toward obj from `reach` out."""
    tree = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    start = V(near) + V(normal) * reach
    hit, _, _, _ = tree.ray_cast(W.rb(*start), W.rb(*(-V(normal))))
    assert hit is not None, "no surface behind the point"
    return V(K.rb_inv(*hit))


def frame(normal):
    n = V(normal).normalized()
    ref = V((0, 1, 0)) if abs(n.y) < 0.9 else V((1, 0, 0))
    s = n.cross(ref).normalized()
    return n, s, n.cross(s).normalized()


def curl(hi, centre, normal, radius, turns=1.6, thick=0.22, spin=1, phase=0.0):
    """A carved spiral curl lying on a surface: a tube winding in from `radius`, standing proud."""
    n, s, t = frame(normal)
    c = V(centre)
    pts = []
    steps = 28
    for i in range(steps + 1):
        k = i / steps
        a = phase + spin * TAU * turns * k
        r = radius * (1 - 0.82 * k)
        pts.append(c + (s * math.cos(a) + t * math.sin(a)) * r + n * thick * 0.6 * (1 - 0.4 * k))
    Hm.htube(hi, pts, lambda k: thick * (1 - 0.55 * k), sides=7, per=1, uv_scale=3.0, tip=True, wobble=0.0)
    sphere(hi, pts[0], thick, nu=8, nv=6)                  # the outer end rounded off, not an open tube


def on_ellipsoid(centre, radii, u, v):
    """A point on an ellipsoid (u round from the front -Z, v from the bottom 0 to the top 1) and its
    outward normal."""
    a, th = TAU * u, math.pi * v
    d = V((math.sin(th) * math.sin(a), -math.cos(th), -math.sin(th) * math.cos(a)))
    p = V(centre) + V((d.x * radii[0], d.y * radii[1], d.z * radii[2]))
    n = V((d.x / radii[0], d.y / radii[1], d.z / radii[2])).normalized()
    return p, n


def resample(pts, step=0.25):
    """Points along a smooth curve through `pts`, about `step` studs apart, ends included."""
    dense = [V(p) for p in W.catmull([tuple(p) for p in pts], 16)]
    at = [0.0]
    for a, b in zip(dense, dense[1:]):
        at.append(at[-1] + (b - a).length)
    count = max(2, round(at[-1] / step) + 1)
    out, j = [], 0
    for i in range(count):
        s = at[-1] * i / (count - 1)
        while j < len(dense) - 2 and at[j + 1] < s:
            j += 1
        span = at[j + 1] - at[j]
        out.append(dense[j].lerp(dense[j + 1], 0 if span <= 0 else (s - at[j]) / span))
    return out


def cone(hi, base, tip, r, sides=8):
    base, tip = V(base), V(tip)
    n, s, t = frame(tip - base)
    ring = [hi.v(base + (s * math.cos(TAU * i / sides) + t * math.sin(TAU * i / sides)) * r) for i in range(sides)]
    top = hi.v(tip)
    for i in range(sides):
        out = (s * math.cos(TAU * (i + 0.5) / sides) + t * math.sin(TAU * (i + 0.5) / sides))
        hi.facing([ring[i], ring[(i + 1) % sides], top], [(0, 0), (1, 0), (0.5, 1)], tuple(out), 0)


def sphere(hi, centre, r, nu=16, nv=10, radii=None, mat=0):
    """A sphere (or an ellipsoid with `radii`) with UVs round (u) and up (v)."""
    c = V(centre)
    rx, ry, rz = radii or (r, r, r)
    dirs = [[V((math.sin(math.pi * j / nv) * math.cos(TAU * i / nu), -math.cos(math.pi * j / nv), math.sin(math.pi * j / nv) * math.sin(TAU * i / nu)))
             for i in range(nu + 1)] for j in range(nv + 1)]
    rows = [[hi.v(c + V((d.x * rx, d.y * ry, d.z * rz))) for d in row] for row in dirs]
    for j in range(nv):
        for i in range(nu):
            out = dirs[j][i] + dirs[j][i + 1] + dirs[j + 1][i + 1] + dirs[j + 1][i]
            hi.facing([rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]],
                      [(i / nu, j / nv), ((i + 1) / nu, j / nv), ((i + 1) / nu, (j + 1) / nv), (i / nu, (j + 1) / nv)], tuple(out), mat)


def eye(iris, pupil, lids, centre, normal, forward, length, height, tilt=0.25, bulge=0.12, lid=0.32, droop=0.35, lower=0.16,
        slit=0.2, pupil_height=0.8, lid_mat=0):
    """An expressive eye, not a ball: an almond iris with sharp corners (a lens, `length` and
    `height` its half sizes) bulging a little from `centre` toward `normal`, its front corner (toward
    `forward`, the snout) lowered by `tilt`; a slit pupil standing just proud of it (`slit` its
    width, `pupil_height` its share of the iris's height); a heavy upper lid whose line drops
    toward the front corner by `droop` (a scowl), and a thinner lower lid.
    iris and pupil are Hi meshes for Neon pieces (the rig narrows, blinks and recolours them; a dark
    Neon pupil renders as a flat black slit), lids a Hi for the head's own mesh."""
    n = V(normal).normalized()
    s = V(forward) - n * V(forward).dot(n)
    s.normalize()
    t = n.cross(s)
    if t.y < 0:
        t = -t
    c = V(centre)
    R = (length ** 2 + height ** 2) / (2 * height)

    def lens(x):
        return max(0.0, math.sqrt(max(0.0, R * R - x * x)) - (R - height))

    def at(x, y, up):
        return c + s * x + t * (y - tilt * height * x / length) + n * up

    m, rings = 16, 5
    xs = [length * math.cos(math.pi * i / m) for i in range(m + 1)]
    outline = [(x, lens(x)) for x in xs] + [(x, -lens(x)) for x in reversed(xs[1:-1])]
    grid = [[iris.v(at(x * k / rings, y * k / rings, bulge * (1 - (k / rings) ** 2))) for x, y in outline] for k in range(1, rings + 1)]
    mid = iris.v(at(0, 0, bulge))
    count = len(outline)
    for j in range(count):
        jj = (j + 1) % count
        iris.facing([mid, grid[0][j], grid[0][jj]], [(0.5, 0.5), (0, 0), (1, 0)], tuple(n))
        for k in range(rings - 1):
            iris.facing([grid[k][j], grid[k + 1][j], grid[k + 1][jj], grid[k][jj]], [(0, 0), (0, 1), (1, 1), (1, 0)], tuple(n))
    # the slit: a vertical lens just proud of the iris's crown
    ph, pw = height * pupil_height, length * slit
    pR = (ph ** 2 + pw ** 2) / (2 * pw)
    plens = lambda y: max(0.0, math.sqrt(max(0.0, pR * pR - y * y)) - (pR - pw))
    ys = [ph * math.cos(math.pi * i / 12) for i in range(13)]
    rim = [(plens(y), y) for y in ys] + [(-plens(y), y) for y in reversed(ys[1:-1])]
    ring = [pupil.v(c + s * x + t * y + n * (bulge * (1 - 0.6 * (y / height) ** 2) + 0.03)) for x, y in rim]
    centre_p = pupil.v(c + n * (bulge + 0.04))
    for j in range(len(ring)):
        pupil.facing([centre_p, ring[j], ring[(j + 1) % len(ring)]], [(0.5, 0.5), (0, 0), (1, 0)], tuple(n))
    # the lids: tubes along the iris's edges, the upper one heavy and dropping toward the front
    ur, lr = lid * height, lower * height
    upper = []
    for i in range(13):
        x = length * 1.18 * (1 - 2 * i / 12)
        f = max(-1.0, min(1.0, x / length))
        y = lens(min(abs(x), length)) + ur * 0.4 - droop * height * (0.5 + 0.5 * f)
        upper.append(at(x, y, bulge * 0.5 + ur * 0.3))
    Hm.htube(lids, upper, lambda q: ur * (0.45 + 0.55 * math.sin(math.pi * q) ** 0.6), sides=10, per=3, mat=lid_mat, uv_scale=1.0, tip=False,
             wobble=0.0)
    for end in (upper[0], upper[-1]):                     # rounded ends, not open tubes
        sphere(lids, end, ur * 0.45, nu=10, nv=6, mat=lid_mat)
    under = []
    for i in range(11):
        x = length * 1.08 * (1 - 2 * i / 10)
        y = -lens(min(abs(x), length)) - lr * 0.35
        under.append(at(x, y, bulge * 0.4 + lr * 0.2))
    Hm.htube(lids, under, lambda q: lr * (0.4 + 0.6 * math.sin(math.pi * q) ** 0.6), sides=8, per=3, mat=lid_mat, uv_scale=1.0, tip=False,
             wobble=0.0)
    for end in (under[0], under[-1]):
        sphere(lids, end, lr * 0.4, nu=8, nv=6, mat=lid_mat)


def wisp(hi, base, direction, up, length, radius, rnd, sides=6):
    """A wisp (of fire, of void): a tapered tongue that leaves `base` along `direction`, sways, and
    curls toward `up` at its tip. UV v runs 0 at its root to 1 at its tip."""
    d = V(direction).normalized()
    u = V(up) - d * V(up).dot(d)
    u = u.normalized() if u.length > 1e-4 else frame(d)[1]
    side = d.cross(u)
    sway = rnd.uniform(-1, 1)
    pts = [V(base), V(base) + d * length * 0.35 + side * length * 0.09 * sway,
           V(base) + d * length * 0.7 - side * length * 0.06 * sway + u * length * 0.12,
           V(base) + d * length * 0.95 + u * length * 0.32]
    Hm.htube(hi, pts, lambda q: radius * (1.0 + 0.25 * math.sin(math.pi * min(1.0, q * 2.5))) * (1 - q) ** 0.85, sides=sides, per=3,
             uv_scale=1.0 / length, tip=True, wobble=0.0)


def limb(a, b, r0, r1):
    """Lobes along a limb, close enough that the merge reads as one smooth form."""
    n = max(4, int((V(b) - V(a)).length / (0.45 * min(r0, r1))) + 1)
    return capsule_lobes(a, b, r0, r1, n=n)


def soften(o, iterations=14):
    """Extra smoothing for living forms: the ellipsoids' creases melt into one body."""
    Hm.apply_modifiers(o, [("SMOOTH", {"factor": 0.9, "iterations": iterations})])
    return o


def veins(hi, obj, starts, rnd, steps=14, step=0.7, radius=0.16, lift=0.04):
    """Glowing cracks wandering over obj's surface: from each start, a random walk kept on the
    surface (each point pulled to the nearest surface point and lifted a hair), forking now and then.
    Tubes into `hi` (a glow piece)."""
    tree = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())

    def onto(p):
        hit, normal, _, _ = tree.find_nearest(W.rb(*p))
        return V(K.rb_inv(*hit)) + V(K.rb_inv(*normal)) * lift

    def walk(p, heading, n, r):
        pts = [onto(p)]
        for _ in range(n):
            heading = (heading + V((rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6)))).normalized()
            pts.append(onto(pts[-1] + heading * step))
            if rnd.random() < 0.12 and n > 5:
                walk(pts[-1], (heading + V((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)))).normalized(), n // 2, r * 0.7)
        if len(pts) > 2:
            Hm.htube(hi, pts, lambda q: r * (1 - 0.6 * q), sides=5, per=2, uv_scale=1.0, tip=True, wobble=0.0)

    for p, heading in starts:
        walk(V(p), V(heading).normalized(), steps, radius)


# ---------- bake and export ----------
def bake_piece(guardian, piece, hi, coll, budget):
    """Bakes a piece's high-detail objects onto its game mesh <guardian>_<piece>, with its maps in
    assets/guardians/."""
    name = guardian + "_" + piece
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    low = B.make_low(name, hi, coll, budget)
    low.name = name
    saved = B.EGG_DIR
    B.EGG_DIR = OUT_DIR
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        B.bake(name, hi, low, size=1024, small=256)
    finally:
        B.EGG_DIR = saved
    return low


def centre_of(obj):
    pts = [V(K.rb_inv(*(obj.matrix_world @ v.co))) for v in obj.data.vertices]
    lo = V((min(q.x for q in pts), min(q.y for q in pts), min(q.z for q in pts)))
    hi = V((max(q.x for q in pts), max(q.y for q in pts), max(q.z for q in pts)))
    return [round(c, 4) for c in (lo + hi) / 2]


def write_fbx(guardian, parts, report):
    """One FBX of every segment's game mesh and glow piece, and the pieces' centres and pivots."""
    path = os.path.join(OUT_DIR, guardian + ".fbx")
    W.export_batch(parts, path)
    with open(os.path.join(OUT_DIR, guardian + "_pieces.json"), "w") as f:
        json.dump(report, f, indent=1, sort_keys=True)
    return path


def export(guardian, pivots, parts_map):
    """The FBX and its report from parts_map {piece: (segment, low object name)} and the guardian's
    glow pieces (<guardian>_<Segment>_Glow_<hex>)."""
    parts, report = [], {"Pieces": {}, "Pivots": {}}
    for piece, (segment, low) in sorted(parts_map.items()):
        obj = bpy.data.objects[low]
        parts.append(obj)
        report["Pieces"][piece] = {"Segment": segment, "Centre": centre_of(obj)}
    for o in bpy.data.objects:
        if o.name.startswith(guardian + "_") and "_Glow_" in o.name:
            parts.append(o)
            segment = o.name[len(guardian) + 1:].split("_Glow_")[0]
            report["Pieces"][o.name[len(guardian) + 1:]] = {"Segment": segment, "Centre": centre_of(o), "Hex": o.name.rsplit("_", 1)[1]}
    for segment, (parent, pos) in pivots.items():
        report["Pivots"][segment] = {"Parent": parent, "Position": list(pos)}
    return write_fbx(guardian, parts, report), report
