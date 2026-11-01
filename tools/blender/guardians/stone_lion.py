"""The Stone Lion, the Starting Island's guardian (run inside Blender): a colossal temple guardian
lion awakened, about 28 studs tall. An original design: weathered pale granite, moss on its back,
a mane of spiral curls round its neck and over its head, spiral brows over glowing cyan eyes, a
broad muzzle with fangs, curled tufts at its elbows, a plume of curls for a tail, and a carved
stone collar hung with a glowing jade orb of Qi and two gold tassels. In game it pins its egg
under its right front paw.

Built from rigid stone segments, so the game animates it with Motor6D joints and nothing
stretches: Body, Head, Jaw, Tail, and for each leg an Upper and a Lower segment. The carved curls
of the body, head and tail are pieces of their own riding their segment (BodyCurls, HeadCurls,
TailCurls): baked with the stone mass they were decimated into lumps to fit one mesh's budget. Each segment is a
union of ellipsoid lobes (voxel remeshed, smoothed, roughened like chiselled stone) with carved
curls on it, baked onto its own game mesh (egg_bake.py). The glowing parts (eyes, the collar's
orb) are separate Neon pieces riding their segment.

Authored in Roblox studs, standing, facing -Z, its paws on the ground at y = 0. PIVOTS (where
each segment turns on its parent) are written with the export for the game to build its joints.

    import stone_lion as L
    L.build()        # the high-detail segments, in collection StoneLionHi
    L.export()       # bake each segment; write assets/guardians/StoneLion.fbx, its maps, pivots
"""
import json
import math
import os
import random

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
NAME = "StoneLion"
OUT_DIR = os.path.join(W.REPO, "assets", "guardians")
EYE = "39d8ff"           # the eyes' Qi
ORB = "2fe6c8"           # the collar's jade orb

# segment: (parent, pivot): where it turns on its parent (Roblox studs)
# Proportioned like a temple guardian lion, not a dog: an enormous head (a third of its length),
# a deep chest and short body, pillar-thick legs on great paws.
PIVOTS = {
    "Body": (None, (0.0, 14.0, 0.0)),
    "Head": ("Body", (0.0, 22.0, -10.0)),
    "Jaw": ("Head", (0.0, 22.8, -14.5)),
    "Tail": ("Body", (0.0, 16.0, 9.5)),
    "FrontLeftUpper": ("Body", (-4.4, 15.0, -6.5)),
    "FrontLeftLower": ("FrontLeftUpper", (-4.6, 8.5, -7.0)),
    "FrontRightUpper": ("Body", (4.4, 15.0, -6.5)),
    "FrontRightLower": ("FrontRightUpper", (4.6, 8.5, -7.0)),
    "BackLeftUpper": ("Body", (-4.3, 14.0, 6.4)),
    "BackLeftLower": ("BackLeftUpper", (-4.5, 4.6, 9.6)),
    "BackRightUpper": ("Body", (4.3, 14.0, 6.4)),
    "BackRightLower": ("BackRightUpper", (4.5, 4.6, 9.6)),
}


# ---------- shapes ----------
def blob(name, coll, mat, lobes, voxel=0.12, smooth=0.6, rough=0.05):
    """A stone mass: ellipsoid lobes [(centre, radii, rotation degrees or None)], merged by a voxel
    remesh, smoothed, and roughened like chiselled stone."""
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
    tex = bpy.data.textures.get("LionChisel") or bpy.data.textures.new("LionChisel", "VORONOI")
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


def on_ellipsoid(centre, radii, u, v):
    """A point on an ellipsoid (u round from the front -Z, v from the bottom 0 to the top 1) and its
    outward normal."""
    a, th = TAU * u, math.pi * v
    d = V((math.sin(th) * math.sin(a), -math.cos(th), -math.sin(th) * math.cos(a)))
    p = V(centre) + V((d.x * radii[0], d.y * radii[1], d.z * radii[2]))
    n = V((d.x / radii[0], d.y / radii[1], d.z / radii[2])).normalized()
    return p, n


def cone(hi, base, tip, r, sides=8):
    base, tip = V(base), V(tip)
    n, s, t = frame(tip - base)
    ring = [hi.v(base + (s * math.cos(TAU * i / sides) + t * math.sin(TAU * i / sides)) * r) for i in range(sides)]
    top = hi.v(tip)
    for i in range(sides):
        out = (s * math.cos(TAU * (i + 0.5) / sides) + t * math.sin(TAU * (i + 0.5) / sides))
        hi.facing([ring[i], ring[(i + 1) % sides], top], [(0, 0), (1, 0), (0.5, 1)], tuple(out), 0)


def sphere(hi, centre, r, nu=16, nv=10):
    c = V(centre)
    dirs = [[V((math.sin(math.pi * j / nv) * math.cos(TAU * i / nu), -math.cos(math.pi * j / nv), math.sin(math.pi * j / nv) * math.sin(TAU * i / nu)))
             for i in range(nu + 1)] for j in range(nv + 1)]
    rows = [[hi.v(c + d * r) for d in row] for row in dirs]
    for j in range(nv):
        for i in range(nu):
            out = dirs[j][i] + dirs[j][i + 1] + dirs[j + 1][i + 1] + dirs[j + 1][i]
            hi.facing([rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]], [(0, 0), (1, 0), (1, 1), (0, 1)], tuple(out), 0)


# ---------- materials ----------
def mat_granite(name="LionGranite"):
    """Weathered pale granite: warm grey flecked dark and light, darker in the crevices, moss settled
    on the upward faces."""
    g = Hm._Graph(name)
    co = g.coords()
    big = g.n("ShaderNodeTexNoise", **{"Scale": 0.35, "Detail": 4.0, "Roughness": 0.55})
    g.link(co, big.inputs["Vector"])
    col = g.ramp(big.outputs["Fac"], [(0.3, (0.36, 0.34, 0.31)), (0.55, (0.5, 0.48, 0.44)), (0.75, (0.6, 0.58, 0.54))])
    fleck = g.n("ShaderNodeTexNoise", **{"Scale": 14.0, "Detail": 2.0})
    g.link(co, fleck.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", g.math("GREATER_THAN", fleck.outputs["Fac"], 0.66), 0.5), col, (0.16, 0.15, 0.14))
    col = g.mix(g.math("MULTIPLY", g.math("LESS_THAN", fleck.outputs["Fac"], 0.3), 0.25), col, (0.78, 0.76, 0.72))
    geo = g.n("ShaderNodeNewGeometry")
    up = g.sep(geo.outputs["Normal"])[2]
    mossn = g.n("ShaderNodeTexNoise", **{"Scale": 0.6, "Detail": 5.0})
    g.link(co, mossn.inputs["Vector"])
    moss = g.math("MULTIPLY", g.math("SUBTRACT", up, 0.55, clamp=True), g.math("SUBTRACT", g.math("MULTIPLY", mossn.outputs["Fac"], 2.4), 1.0, clamp=True))
    col = g.mix(g.math("MINIMUM", g.math("MULTIPLY", moss, 2.2), 0.85), col, (0.17, 0.3, 0.09))
    col = g.ao(col, 0.6, 0.35)
    return g.finish(col, 0.82, 0.0, g.bump(g.math("ADD", big.outputs["Fac"], g.math("MULTIPLY", fleck.outputs["Fac"], 0.3)), 0.25, 0.05))


# ---------- the segments ----------
def body(coll, M):
    lobes = [((0, 15.5, -5.0), (6.4, 6.8, 6.2), None), ((0, 14.0, 1.5), (5.4, 5.4, 5.6), None), ((0, 14.5, 6.0), (5.4, 5.6, 4.6), None),
             ((-4.2, 16.0, -5.5), (3.2, 4.5, 4.0), None), ((4.2, 16.0, -5.5), (3.2, 4.5, 4.0), None),
             ((-4.0, 13.5, 6.4), (3.2, 4.6, 4.0), None), ((4.0, 13.5, 6.4), (3.2, 4.6, 4.0), None),
             ((0, 20.0, -8.0), (5.0, 5.5, 5.0), None), ((0, 21.0, -8.0), (7.4, 7.0, 5.6), None)]
    stone = blob("SL_Body", coll, M["granite"], lobes, voxel=0.16, rough=0.07)
    carved, gold, glow = Hm.Hi(), Hm.Hi(), Hm.Hi()
    # the mane round the neck: rows of spiral curls on the ruff, each curling its own way
    ruff = ((0, 21.0, -8.0), (7.7, 7.3, 5.9))
    rnd = random.Random(7)
    for row, (v, count) in enumerate(((0.36, 16), (0.47, 19), (0.58, 19), (0.69, 17), (0.8, 13), (0.9, 8))):
        for k in range(count):
            u = (k + 0.5 * (row % 2)) / count
            if 0.4 < u < 0.6 and v < 0.75:
                continue                          # the back of the neck runs smooth into the spine
            p, n = on_ellipsoid(ruff[0], ruff[1], u, v)
            curl(carved, p - n * 0.15, n, 1.0 + rnd.uniform(-0.1, 0.14), thick=0.28, spin=1 if (k + row) % 2 else -1, phase=rnd.uniform(0, TAU))
    # a ridge of curls down the spine, and a great spiral relief on each shoulder and haunch, as
    # guardian lions are carved (a plain body reads as a dog)
    for k in range(7):
        z = -1.0 + 1.6 * k
        p, n = surface_down(stone, 0.0, z)                         # measured on the carved back, not guessed
        if p:
            curl(carved, p - n * 0.12, n, 0.95, thick=0.28, spin=1 if k % 2 else -1, phase=k)
    for side in (-1, 1):
        for centre, r in (((side * 7.25, 16.6, -5.5), 2.3), ((side * 7.05, 13.6, 6.4), 2.1)):
            curl(carved, centre, (side, 0.15, 0), r, turns=2.3, thick=0.34, spin=side)
    # the collar: a carved band round the neck, the jade orb at its front, two gold tassels hanging
    collar = []
    for i in range(48):
        a = TAU * i / 48
        collar.append(V((5.7 * math.sin(a), 17.4 + 1.1 * math.cos(a), -8.4 - 5.3 * math.cos(a))))
    Hm.htube(carved, collar + collar[:2], lambda t: 0.5, sides=10, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    orb = V((0, 16.0, -14.2))
    ring = [orb + V((1.15 * math.sin(TAU * i / 24), 1.15 * math.cos(TAU * i / 24), 0.25)) for i in range(24)]
    Hm.htube(gold, ring + ring[:2], lambda t: 0.2, sides=8, per=1, uv_scale=3.0, tip=False, wobble=0.0)
    sphere(glow, orb + V((0, 0, -0.15)), 1.0)
    for side in (-1, 1):
        top = V((side * 3.2, 16.6, -12.6))
        Hm.htube(gold, [top, top + V((side * 0.3, -1.4, -0.5)), top + V((side * 0.4, -3.0, -0.3))], lambda t: 0.22 * (1 - 0.3 * t), sides=8,
                 per=4, uv_scale=3.0, tip=False, wobble=0.0)
        for j in range(7):
            a = TAU * j / 7
            base = top + V((side * 0.4, -3.0, -0.3)) + V((0.18 * math.cos(a), 0, 0.18 * math.sin(a)))
            Hm.htube(gold, [base, base + V((0.1 * math.cos(a), -1.3, 0.1 * math.sin(a)))], lambda t: 0.09, sides=5, per=3, uv_scale=3.0, tip=True,
                     wobble=0.0)
    return [stone, carved.object("SL_BodyCurls", coll, [M["granite"]]), gold.object("SL_BodyGold", coll, [M["gold"]])], \
        {ORB: [glow.object("SL_Orb", coll, [K.glow_material(ORB)], smooth=True)]}


def head(coll, M):
    lobes = [((0, 26.0, -13.0), (5.8, 5.0, 5.0), None), ((-3.5, 24.0, -15.5), (3.0, 2.6, 2.8), None), ((3.5, 24.0, -15.5), (3.0, 2.6, 2.8), None),
             ((0, 23.5, -18.0), (3.6, 2.4, 2.8), None), ((0, 25.0, -20.6), (1.9, 1.2, 1.1), None),
             ((-2.6, 28.2, -16.8), (2.1, 1.0, 1.6), (0, 0, -12)), ((2.6, 28.2, -16.8), (2.1, 1.0, 1.6), (0, 0, 12)),
             ((0, 27.4, -10.4), (6.2, 5.8, 4.0), None), ((-5.2, 28.4, -12.4), (1.3, 1.9, 0.8), (0, 0, 25)), ((5.2, 28.4, -12.4), (1.3, 1.9, 0.8), (0, 0, -25))]
    stone = blob("SL_Head", coll, M["granite"], lobes, voxel=0.12, rough=0.05)
    carved, glow = Hm.Hi(), Hm.Hi()
    rnd = random.Random(11)
    # curls over the crown and back of the head
    mane = ((0, 27.4, -10.4), (6.5, 6.1, 4.3))
    for row, (v, count) in enumerate(((0.45, 14), (0.58, 14), (0.7, 12), (0.82, 9), (0.93, 5))):
        for k in range(count):
            u = 0.22 + 0.56 * (k + 0.5 * (row % 2)) / count       # from the sides round the back
            p, n = on_ellipsoid(mane[0], mane[1], u, v)
            curl(carved, p - n * 0.1, n, 0.95 + rnd.uniform(-0.08, 0.12), thick=0.27, spin=1 if (k + row) % 2 else -1, phase=rnd.uniform(0, TAU))
    # spiral brows above the eyes, and curled whisker bosses on the muzzle
    for side in (-1, 1):
        curl(carved, (side * 2.6, 29.0, -17.2), (side * 0.2, 0.8, -0.6), 1.2, turns=1.8, thick=0.32, spin=side)
        curl(carved, (side * 2.2, 23.3, -20.3), (side * 0.5, -0.1, -0.85), 0.8, turns=1.6, thick=0.24, spin=-side)
        sphere(glow, (side * 2.4, 26.8, -18.0), 1.25)            # the eyes, bulging, alight with Qi
    # the upper fangs
    for side in (-1, 1):
        cone(carved, (side * 1.8, 22.6, -20.2), (side * 1.7, 20.9, -20.6), 0.42)
        cone(carved, (side * 0.8, 22.5, -20.7), (side * 0.8, 21.6, -20.9), 0.26)
    return [stone, carved.object("SL_HeadCurls", coll, [M["granite"]])], {EYE: [glow.object("SL_Eyes", coll, [K.glow_material(EYE)], smooth=True)]}


def jaw(coll, M):
    lobes = [((0, 21.8, -18.0), (3.3, 1.1, 3.0), None), ((0, 21.6, -16.0), (3.4, 1.2, 2.0), None)]
    stone = blob("SL_Jaw", coll, M["granite"], lobes, voxel=0.1, rough=0.04)
    carved = Hm.Hi()
    for side in (-1, 1):
        cone(carved, (side * 2.0, 22.4, -20.1), (side * 1.9, 23.6, -20.4), 0.36)
    # a beard of curls under the chin
    for k, (x, y, z) in enumerate(((-1.6, 20.8, -19.0), (0.0, 20.4, -19.6), (1.6, 20.8, -19.0), (-0.8, 19.6, -18.8), (0.8, 19.6, -18.8))):
        curl(carved, (x, y, z), (x * 0.3, -0.5, -0.8), 0.78, turns=1.5, thick=0.24, spin=1 if k % 2 else -1)
    return [stone, carved.object("SL_JawCurls", coll, [M["granite"]])], {}


def tail(coll, M):
    """A tail that flares up like flame: a stout stem, then five tongues of carved curls fanning
    upward, each ending in a spiral."""
    lobes = [((0, 17.4, 10.6), (1.6, 2.0, 1.6), (35, 0, 0)), ((0, 19.0, 11.4), (1.5, 1.6, 1.4), (20, 0, 0))]
    stone = blob("SL_Tail", coll, M["granite"], lobes, voxel=0.12, rough=0.05)
    carved = Hm.Hi()
    base = V((0, 19.6, 11.6))
    for k, (a, height, lean) in enumerate(((-0.55, 6.0, 1.4), (-0.27, 7.5, 1.0), (0.0, 8.3, 0.6), (0.27, 7.5, 1.0), (0.55, 6.0, 1.4))):
        tip = base + V((math.sin(a) * 4.2, height, lean + 0.8))
        mid = base + V((math.sin(a) * 1.8, height * 0.55, lean * 0.4 + 1.2))
        Hm.htube(carved, [base, mid, tip], lambda t: 1.35 * (1 - 0.65 * t), sides=10, per=8, uv_scale=3.0, tip=False, wobble=0.0)
        side = 1 if a >= 0 else -1
        curl(carved, tip + V((0, 0.2, 0)), (math.sin(a), 0.2, 0.6), 1.1, turns=1.7, thick=0.32, spin=side if k != 2 else 1)
    return [stone, carved.object("SL_TailCurls", coll, [M["granite"]])], {}


def paw(centre, front):
    """Lobes for a paw at `centre`, its toes toward `front` (-1 for -Z)."""
    c = V(centre)
    out = [(tuple(c), (2.8, 1.5, 3.3), None)]
    for i, dx in enumerate((-1.6, -0.55, 0.55, 1.6)):
        out.append((tuple(c + V((dx, -0.2, front * (2.9 - 0.3 * abs(dx))))), (0.95, 1.0, 1.05), None))
    return out


def leg(coll, M, name, side, front):
    sx = side
    carved = Hm.Hi()
    if front and name.endswith("Upper"):
        lobes = capsule_lobes((sx * 4.4, 15.0, -6.5), (sx * 4.6, 8.6, -7.0), 3.3, 2.8)
        # a curled tuft at the back of the elbow
        for k in range(3):
            curl(carved, (sx * (4.6 + 0.8 * (k - 1)), 9.8 - 0.4 * abs(k - 1), -4.1), (sx * 0.3 * (k - 1), -0.2, 1), 0.85, thick=0.27,
                 spin=1 if k % 2 else -1)
    elif front:
        lobes = capsule_lobes((sx * 4.6, 8.6, -7.0), (sx * 4.6, 2.6, -7.6), 2.8, 2.5) + paw((sx * 4.6, 1.5, -9.2), -1)
    elif name.endswith("Upper"):
        lobes = [((sx * 4.5, 11.0, 7.4), (3.4, 4.6, 4.0), None), ((sx * 4.5, 6.6, 9.0), (2.3, 3.2, 2.4), (-15, 0, 0))]
        for k in range(3):
            curl(carved, (sx * (4.5 + 0.8 * (k - 1)), 10.6 - 0.4 * abs(k - 1), 11.2), (sx * 0.3 * (k - 1), 0.1, 1), 0.85, thick=0.27,
                 spin=1 if k % 2 else -1)
    else:
        lobes = capsule_lobes((sx * 4.5, 4.6, 9.6), (sx * 4.5, 2.4, 8.8), 2.0, 1.9) + paw((sx * 4.5, 1.4, 7.4), -1)
    stone = blob("SL_" + name, coll, M["granite"], lobes, voxel=0.12, rough=0.05)
    out = [stone]
    if carved.faces:
        out.append(carved.object("SL_" + name + "Curls", coll, [M["granite"]]))
    return out, {}


def segments():
    out = {"Body": body, "Head": head, "Jaw": jaw, "Tail": tail}
    for side, s in ((-1, "Left"), (1, "Right")):
        for front, f in ((True, "Front"), (False, "Back")):
            for part in ("Upper", "Lower"):
                name = f + s + part
                out[name] = (lambda n, sd, fr: lambda c, M: leg(c, M, n, sd, fr))(name, side, front)
    return out


BUDGET = {"Body": 12000, "Head": 12000, "Jaw": 5000, "Tail": 5000, "BodyCurls": 19000, "HeadCurls": 15000, "TailCurls": 12000}
OWN_CURLS = ("Body", "Head", "Tail")     # segments whose curls are a piece of their own


def build(only=None):
    M = {"granite": mat_granite(), "gold": Hm.mat_gold()}
    root = W.collection(NAME + "Hi")
    out = {}
    for name, fn in segments().items():
        if only and name not in only:
            continue
        coll = W.collection(NAME + "_" + name, root)
        W.clear_collection(coll)
        hi, glow = fn(coll, M)
        out[name] = (hi, glow, coll)
    return out


def pieces(name, hi):
    """A segment's game pieces: [(piece, hi objects)]. Curls and gold are kept whole (the stone mass
    is decimated around them), or, on the curl-covered segments, the curls are a piece of their own."""
    curls = [o for o in hi if o.name.endswith("Curls")]
    rest = [o for o in hi if o not in curls]
    for o in rest:
        o["keep"] = o.name.endswith("Gold")
    if name in OWN_CURLS:
        for o in curls:
            o["keep"] = False
        return [(name, rest), (name + "Curls", curls)]
    for o in curls:
        o["keep"] = True
    return [(name, rest + curls)]


def bake_segment(name, hi, coll):
    piece = NAME + "_" + name
    old = bpy.data.objects.get(piece)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    low = B.make_low(piece, hi, coll, BUDGET.get(name, 5000))
    low.name = piece
    saved = B.EGG_DIR
    B.EGG_DIR = OUT_DIR
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        B.bake(piece, hi, low, size=1024, small=256)
    finally:
        B.EGG_DIR = saved
    return low


def centre_of(obj):
    pts = [V(K.rb_inv(*(obj.matrix_world @ v.co))) for v in obj.data.vertices]
    lo = V((min(q.x for q in pts), min(q.y for q in pts), min(q.z for q in pts)))
    hi = V((max(q.x for q in pts), max(q.y for q in pts), max(q.z for q in pts)))
    return [round(c, 4) for c in (lo + hi) / 2]


def write_fbx(parts, report):
    """One FBX of every segment's game mesh and glow piece, and the pieces' centres and pivots."""
    path = os.path.join(OUT_DIR, NAME + ".fbx")
    W.export_batch(parts, path)
    with open(os.path.join(OUT_DIR, NAME + "_pieces.json"), "w") as f:
        json.dump(report, f, indent=1, sort_keys=True)
    return path
