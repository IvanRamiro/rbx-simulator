"""Yggdrasil's World Tree, at the island's centre.

An ancient ash: a trunk of seven buttress flutes that spiral as they rise, Qi glowing in the
grooves between them; three great roots arching over the Root Court and four sinking into the
mound; six limbs that part at the top of the trunk and spread into a crown of cloud pads in tiers
(the island's spirit-pine language, at the scale of the world), golden seed-lanterns hanging under
the pads on threads of light, and aerial roots trailing from the limbs.

Authored in island-local Roblox studs (ground ~0 = world Y 200), exported with Yggdrasil's island
meshes and seated at the island centre.
"""
import math
import random

from mathutils import Vector

import worldlib as W

TAU = 2 * math.pi
FLUTES = 7
FLUTE_BEARING = 38.0             # a flute (and its root) points this way at the ground
TRUNK_BASE, TRUNK_TOP = -8.0, 112.0
LONG_ROOTS = (0, 2, 4)           # the flutes whose roots arch over the Root Court
# The trunk (and its veins) squashed toward its foot so its top ends inside the six limbs: built to
# TRUNK_TOP, its rim and cap showed between them as a cut stub (the owner, 2026-11-11: "a problem in
# trunk"). The placed meshes in the game were scaled the same way in Studio (124 -> 106 studs tall).
TRUNK_SQUASH = 106 / 124


def squashed(y):
    return TRUNK_BASE + (y - TRUNK_BASE) * TRUNK_SQUASH


# ---------- trunk ----------
def _t(y):
    return (y - TRUNK_BASE) / (TRUNK_TOP - TRUNK_BASE)


def core_radius(y):
    t = _t(y)
    return 18.5 + 9.5 * (1 - W.smoothstep(0.0, 0.45, t)) + 5.0 * W.smoothstep(0.72, 1.0, t)


def flute_depth(y):
    return 4.0 + 15.0 * (1 - W.smoothstep(0.0, 0.32, _t(y))) ** 1.4


def twist(y):
    """How far the flutes have turned (radians) at height y: a third of a turn over the trunk."""
    return TAU / 3 * W.smoothstep(4.0, TRUNK_TOP + 20, y) * ((y - 4.0) / (TRUNK_TOP - 4.0) if y > 4.0 else 0.0) ** 0.25


def flute_angle(k, y):
    return math.radians(FLUTE_BEARING) + TAU * k / FLUTES + twist(y)


def ridge(phi):
    """0 in a groove, 1 on a flute's crest."""
    c = math.cos(FLUTES * phi)
    return ((c + 1) / 2) ** 1.8


def trunk_r(theta, y):
    phi = theta - math.radians(FLUTE_BEARING) - twist(y)
    burl = 1.2 * W.fbm(math.cos(theta) * 3 + y / 9, math.sin(theta) * 3 - y / 9, seed=301, octaves=3)
    return core_radius(y) + flute_depth(y) * ridge(phi) + burl


def trunk(coll, mat, bands):
    seg = 84
    ys = [TRUNK_BASE + i * 2.5 for i in range(9)] + [TRUNK_BASE + 22.5 + i * 4.5 for i in range(21)]
    ys = [y for y in ys if y <= TRUNK_TOP] + [TRUNK_TOP]
    v0, v1 = bands["BARK"]
    verts, faces, uvs = [], [], []
    for y in ys:
        for i in range(seg):
            th = TAU * i / seg
            r = trunk_r(th, y)
            verts.append(W.rb(math.cos(th) * r, squashed(y), math.sin(th) * r))
    for k in range(len(ys) - 1):
        for i in range(seg):
            j = (i + 1) % seg
            a, b, c, d = k * seg + i, k * seg + j, (k + 1) * seg + j, (k + 1) * seg + i
            faces.append([a, d, c, b])
            # u follows the spiral so the bark's fissures run with the flutes
            ua = 6 * (i / seg - twist(ys[k]) / TAU)
            ub = 6 * ((i + 1) / seg - twist(ys[k]) / TAU)
            uc = 6 * ((i + 1) / seg - twist(ys[k + 1]) / TAU)
            ud = 6 * (i / seg - twist(ys[k + 1]) / TAU)
            va = v0 + (v1 - v0) * (ys[k] - TRUNK_BASE) / (TRUNK_TOP - TRUNK_BASE)
            vb = v0 + (v1 - v0) * (ys[k + 1] - TRUNK_BASE) / (TRUNK_TOP - TRUNK_BASE)
            uvs.append([(ua, va), (ud, vb), (uc, vb), (ub, va)])
    top = len(verts)
    verts.append(W.rb(0, squashed(TRUNK_TOP + 4), 0))
    base = (len(ys) - 1) * seg
    for i in range(seg):
        faces.append([base + i, base + (i + 1) % seg, top])
        uvs.append([(0.5, v1)] * 3)
    return W.mesh_object("YG_Trunk", verts, faces, coll, uvs=uvs, material=mat)


def veins(coll):
    """Qi in the grooves: a broken ribbon up each groove, lying just proud of the bark."""
    verts, faces = [], []
    rnd = random.Random(7)
    for k in range(FLUTES):
        y = 5.0 + rnd.uniform(0, 3)
        top = rnd.uniform(84, 104)
        prev = None
        while y < top:
            # a groove sits half a flute away from a crest
            th = flute_angle(k + 0.5, y) + 0.05 * math.sin(y / 7 + k)
            r = trunk_r(th, y) + 0.3
            width = (0.55 + 0.35 * (0.5 + 0.5 * math.sin(y / 11 + k * 2))) * (1.6 - 0.8 * _t(y))
            centre = Vector((math.cos(th) * r, math.sin(th) * r))
            side = Vector((-math.sin(th), math.cos(th))) * width
            live = W.noise2(k * 3.1, y / 9, seed=17) > 0.18
            pair = (len(verts), len(verts) + 1)
            verts.append(W.rb(centre.x - side.x, squashed(y), centre.y - side.y))
            verts.append(W.rb(centre.x + side.x, squashed(y), centre.y + side.y))
            if prev and live:
                faces.append([prev[0], pair[0], pair[1], prev[1]])
            prev = pair
            y += 2.0
    return W.mesh_object("YG_TrunkVeins", verts, faces, coll, smooth=False)


# ---------- roots on the mound ----------
def root_points(k):
    """A root's centre line out of flute k's foot (Roblox studs)."""
    b = math.radians(FLUTE_BEARING) + TAU * k / FLUTES
    drift = 0.1 * (1 if k % 2 else -1)
    def at(r, y, curl=0.0):
        a = b + drift * curl
        return (math.cos(a) * r, y, math.sin(a) * r)
    if k in LONG_ROOTS:
        # out of the buttress, up over the Root Court (its underside about 12 studs over the path),
        # and down into the meadow beyond
        return [at(14, 14, 0), at(30, 9, 0), at(44, 6, 0.2), at(56, 9, 0.5), at(67, 14.5, 0.8), at(77, 18.5, 1.0), at(87, 17.5, 1.1),
                at(98, 11, 1.1), at(109, 3, 0.9), at(119, -5, 0.7)]
    return [at(14, 13, 0), at(30, 8, 0), at(44, 4.5, 0.2), at(55, 2.5, 0.6), at(65, 0.5, 0.9), at(74, -4, 1.0)]


def mound_roots(coll, mat, bands):
    objs = []
    for k in range(FLUTES):
        pts = root_points(k)
        long = k in LONG_ROOTS
        r0, r1 = (11.0, 3.5) if long else (11.5, 3.0)
        objs.append(W.tube("YG_MoundRoot%d" % k, coll, [W.rb(*p) for p in pts],
                           lambda t, r0=r0, r1=r1: r0 + (r1 - r0) * t ** 0.7, 14, mat, bands["ROOT"],
                           per=8, uv_repeat=2.0, wobble=0.18, seed=k * 7 + 3))
    return objs


# ---------- limbs and crown ----------
def limb_plan():
    """Each limb: bearing, reach, height and forks. Seeded, so it never changes."""
    rnd = random.Random(1909)
    limbs = []
    for k in range(6):
        b = math.radians(FLUTE_BEARING + 30 + 60 * k + rnd.uniform(-8, 8))
        limbs.append({"bearing": b, "reach": rnd.uniform(78, 92), "end_y": rnd.uniform(128, 138),
                      "forks": [rnd.uniform(-0.42, -0.26), rnd.uniform(0.26, 0.42)]})
    return limbs


def limb_points(limb):
    b, reach, ey = limb["bearing"], limb["reach"], limb["end_y"]
    def at(r, y):
        return (math.cos(b) * r, y, math.sin(b) * r)
    return [at(4, 76), at(14, 96), at(reach * 0.32, 110), at(reach * 0.55, ey - 10), at(reach * 0.8, ey - 3), at(reach, ey)]


def fork_points(limb, side):
    """A branch leaving the limb about halfway and climbing to an upper tier."""
    base = limb_points(limb)[3]
    b = limb["bearing"] + limb["forks"][side]
    r0 = math.hypot(base[0], base[2])
    return [base, (math.cos(b) * (r0 + 12), base[1] + 14, math.sin(b) * (r0 + 12)),
            (math.cos(b) * (r0 + 26), limb["end_y"] + 30, math.sin(b) * (r0 + 26))]


CENTRAL = [(0.9, 24, 180), (3.9, 20, 184)]   # the two limbs that carry the crown's top: bearing (rad), reach, top


def central_points(bearing, reach, top):
    def at(r, y):
        return (math.cos(bearing) * r, y, math.sin(bearing) * r)
    return [at(0, 96), at(reach * 0.4, 125), at(reach * 0.8, 150), at(reach, top)]


def limbs(coll, mat, bands):
    plans = []
    for limb in limb_plan():
        plans.append((limb_points(limb), 14.0, 4.0))
        for side in (0, 1):
            plans.append((fork_points(limb, side), 5.5, 2.2))
    for bearing, reach, top in CENTRAL:
        plans.append((central_points(bearing, reach, top), 10.0, 3.5))
    objs = []
    for idx, (pts, r0, r1) in enumerate(plans):
        sides = 16 if r0 > 8 else 10
        objs.append(W.tube("YG_Limb%d" % idx, coll, [W.rb(*p) for p in pts],
                           lambda t, r0=r0, r1=r1: r0 + (r1 - r0) * t ** 0.8, sides, mat, bands["BARK"],
                           per=8, uv_repeat=3.0 if r0 > 8 else 1.5, wobble=0.12, seed=idx * 11 + 5))
    return objs


def pad_plan():
    """(centre, radius, thickness, golden) for every cloud pad of the crown."""
    rnd = random.Random(4242)
    pads = []
    for limb in limb_plan():
        end = limb_points(limb)[-1]
        b = limb["bearing"]
        # a broad pad over the limb's tip and a smaller one off to one side
        pads.append(((end[0] + math.cos(b) * 4, end[1] + 2, end[2] + math.sin(b) * 4), rnd.uniform(31, 36), 7.5, False))
        side = b + rnd.choice((-1, 1)) * rnd.uniform(0.4, 0.5)
        r = math.hypot(end[0], end[2]) + rnd.uniform(-2, 8)
        pads.append(((math.cos(side) * r, end[1] - rnd.uniform(2, 5), math.sin(side) * r), rnd.uniform(17, 21), 6.0, False))
        for s in (0, 1):
            tip = fork_points(limb, s)[-1]
            pads.append(((tip[0], tip[1] + 2, tip[2]), rnd.uniform(23, 27), 7.0, s == 1))
    for bearing, reach, top in CENTRAL:
        tip = central_points(bearing, reach, top)[-1]
        pads.append(((tip[0], tip[1] + 2, tip[2]), rnd.uniform(27, 31), 8.0, True))
    pads.append(((0, 200, 0), 20.0, 7.0, True))
    return pads


def cloud_pad(mb, centre, r, thick, seed, band, golden):
    """A flattened, scalloped canopy pad; `golden` pads take the sun-gilded half of the strip."""
    rnd = random.Random(seed)
    ph = rnd.uniform(0, TAU)
    lobes = rnd.choice((6, 7, 8, 9))
    ph2 = rnd.uniform(0, TAU)
    rmod = lambda th, k: 1 + 0.12 * math.sin(lobes * th + ph) * (1 if k in (1, 2, 3, 4) else 0.5) + 0.05 * math.sin(2 * lobes * th + ph2)
    u = 0.75 if golden else 0.25
    rings = mb.lathe([(r * 0.5, thick * 1.0, 1.0), (r * 0.8, thick * 0.85, 0.96), (r * 0.97, thick * 0.45, 0.85),
                      (r, thick * 0.1, 0.68), (r * 0.9, -thick * 0.25, 0.48), (r * 0.55, -thick * 0.45, 0.3)],
                     30, band, centre=centre, rmod=rmod, phase=ph, cap_top=True, cap_bottom=True, u_repeat=0.0)
    # lathe faces sample the strip's middle (u 0.5); move them to this pad's half
    for uv in mb.uvs[-(30 * 5 + 60):]:
        for i, (_, v) in enumerate(uv):
            uv[i] = (u, v)
    return rings


def crown(coll, mat, bands):
    lower, upper = W.MeshBuilder(), W.MeshBuilder()
    for idx, (centre, r, thick, golden) in enumerate(pad_plan()):
        cloud_pad(lower if centre[1] < 150 else upper, centre, r, thick, 900 + idx, bands["CANOPY"], golden)
    return [lower.object("YG_CrownLower", coll, mat, smooth=True), upper.object("YG_CrownUpper", coll, mat, smooth=True)]


def lanterns(coll):
    """Seed-lanterns under the pads, each hung on a thread of light (one glowing mesh)."""
    rnd = random.Random(77)
    mb = W.MeshBuilder()
    band = (0.5, 0.5)
    for centre, r, thick, _ in pad_plan():
        for _ in range(rnd.choice((1, 2, 2, 3))):
            a, d = rnd.uniform(0, TAU), rnd.uniform(0.25, 0.7) * r
            x, z = centre[0] + math.cos(a) * d, centre[2] + math.sin(a) * d
            top = centre[1] - thick * 0.3
            drop = rnd.uniform(4, 9)
            y = top - drop
            s = rnd.uniform(0.9, 1.3)
            mb.lathe([(0.0, 1.6 * s, 1), (0.55 * s, 1.2 * s, 1), (1.05 * s, 0.1 * s, 1), (0.85 * s, -1.1 * s, 1), (0.0, -1.9 * s, 1)],
                     8, band, centre=(x, y, z), cap_top=False)
            mb.box((x, y + 1.6 * s + (drop - 1.6 * s) / 2, z), (0.14, drop - 1.6 * s, 0.14), band)
    return mb.object("YG_SeedLanterns", coll, None)


def aerial_roots(coll, mat, bands):
    """Roots trailing from the limbs' undersides, swaying a little, stopping well above the ground."""
    rnd = random.Random(31)
    mb = W.MeshBuilder()
    for limb in limb_plan():
        pts = limb_points(limb)
        for f in (0.5, 0.76):
            i = min(int(f * (len(pts) - 1)), len(pts) - 2)
            t = f * (len(pts) - 1) - i
            p = [pts[i][q] + (pts[i + 1][q] - pts[i][q]) * t for q in range(3)]
            length = rnd.uniform(30, 58)
            sway = rnd.uniform(0, TAU)
            line = [(p[0], p[1] - 4, p[2])]
            for s in range(1, 5):
                f2 = s / 4
                line.append((p[0] + math.cos(sway) * 2.5 * math.sin(f2 * 3), p[1] - 4 - length * f2, p[2] + math.sin(sway) * 2.5 * math.sin(f2 * 3)))
            W.mb_tube(mb, line, lambda t: 0.75 - 0.6 * t, 5, bands["ROOT"], per=4)
    return mb.object("YG_AerialRoots", coll, mat)


def build(coll, mat, bands):
    objs = [trunk(coll, mat, bands), veins(coll)]
    objs += mound_roots(coll, mat, bands)
    objs += limbs(coll, mat, bands)
    objs += crown(coll, mat, bands)
    objs.append(lanterns(coll))
    objs.append(aerial_roots(coll, mat, bands))
    return objs
