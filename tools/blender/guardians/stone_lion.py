"""The Stone Lion, Yggdrasil's guardian (run inside Blender): a colossal temple guardian
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
    L.bake(names)    # bake those segments' pieces (a few per call: the connection drops on long runs)
    L.export()       # assets/guardians/StoneLion.fbx and its pieces report
"""
import math
import random

import bpy
from mathutils import Vector

import egg_bake as B
import egg_hi as Hm
import egg_kit as K
import guardian_kit as G

W = K.W
V = Vector
TAU = 2 * math.pi
NAME = "StoneLion"
OUT_DIR = G.OUT_DIR
EYE = "39d8ff"           # the eyes' Qi
PUPIL = "06101c"         # the round pupils: dark Neon renders as a flat black disc, and the rig blinks it with the iris
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


# ---------- shapes (guardian_kit) ----------
blob, capsule_lobes, surface_down, frame = G.blob, G.capsule_lobes, G.surface_down, G.frame
curl, on_ellipsoid, cone, sphere = G.curl, G.on_ellipsoid, G.cone, G.sphere


def surface_along(obj, near, normal, reach=6.0):
    """Where the line through `near` along `normal` leaves obj's surface outward (Roblox space): cast
    back toward obj from `reach` out."""
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    start = V(near) + V(normal) * reach
    hit, _, _, _ = tree.ray_cast(W.rb(*start), W.rb(*(-V(normal))))
    assert hit is not None, "no surface behind the eye"
    return V(K.rb_inv(*hit))


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
    carved, glow, pupils, lids = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
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
        # the eyes: a temple lion's, bulging and round-pupilled under carved stone lids set in a frown,
        # seated on the stone (measured, not guessed)
        normal = V((side * 0.5, 0.05, -0.87)).normalized()
        seat = surface_along(stone, V((side * 2.4, 26.8, -18.0)), normal)
        G.eye(glow, pupils, lids, seat, normal, (0, 0, -1), 1.3, 0.85, tilt=0.14, bulge=0.5, lid=0.38, droop=0.44, lower=0.22,
              slit=0.19, pupil_height=0.62)
    # the upper fangs
    for side in (-1, 1):
        cone(carved, (side * 1.8, 22.6, -20.2), (side * 1.7, 20.9, -20.6), 0.42)
        cone(carved, (side * 0.8, 22.5, -20.7), (side * 0.8, 21.6, -20.9), 0.26)
    lid = lids.object("SL_HeadLids", coll, [M["granite"]])
    lid["keep"] = True
    return [stone, lid, carved.object("SL_HeadCurls", coll, [M["granite"]])], \
        {EYE: [glow.object("SL_Eyes", coll, [K.glow_material(EYE)], smooth=True)],
         PUPIL: [pupils.object("SL_Pupils", coll, [K.glow_material(PUPIL)], smooth=True)]}


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
        for hexstr, objs in glow.items():
            assert len(objs) == 1, "one glow piece per colour per segment"
            objs[0].name = NAME + "_" + name + "_Glow_" + hexstr
        out[name] = (hi, glow, coll)
    return out


def pieces(name, hi):
    """A segment's game pieces: [(piece, hi objects)]. Curls, gold and lids are kept whole (the stone mass
    is decimated around them), or, on the curl-covered segments, the curls are a piece of their own."""
    curls = [o for o in hi if o.name.endswith("Curls")]
    rest = [o for o in hi if o not in curls]
    for o in rest:
        o["keep"] = o.name.endswith("Gold") or o.name.endswith("Lids")      # the eyes' carved lids stay whole
    if name in OWN_CURLS:
        for o in curls:
            o["keep"] = False
        return [(name, rest), (name + "Curls", curls)]
    for o in curls:
        o["keep"] = True
    return [(name, rest + curls)]


def bake_segment(name, hi, coll):
    return G.bake_piece(NAME, name, hi, coll, BUDGET.get(name, 5000))


centre_of = G.centre_of


def write_fbx(parts, report):
    """One FBX of every segment's game mesh and glow piece, and the pieces' centres and pivots."""
    return G.write_fbx(NAME, parts, report)


def bake(names):
    """Bakes these segments' game pieces (built already); records them for export()."""
    parts = bpy.app.driver_namespace.setdefault("lion_parts", {})
    for name in names:
        coll = bpy.data.collections[NAME + "_" + name]
        hi = [o for o in coll.objects if o.name.startswith("SL_") and o.type == "MESH"]
        for piece, objs in pieces(name, hi):
            low = G.bake_piece(NAME, piece, objs, coll, BUDGET.get(piece, 5000))
            parts[piece] = (name, low.name)
    return {p: B.tris(bpy.data.objects[l]) for p, (_, l) in parts.items()}


def export():
    return G.export(NAME, PIVOTS, bpy.app.driver_namespace["lion_parts"])
