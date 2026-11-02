"""Tiangou the Moon-Eater, Moonlit Isle's guardian (run inside Blender). The idea: the heavenly hound
of the eclipse myth, the dog that swallows the moon. A lean, long-legged celestial hound, its coat
the midnight sky (deep blue, faint constellations in it, silvered where the moonlight falls),
a ruff and a plume of a tail of white fire. Above its shoulders stands the eclipse it made: the
swallowed moon as a black disc ringed by a corona of white fire, framing its head from the front,
and in the last silver crescent of that moon, the egg. Its eyes are gold, and they watch you.

About 14 studs at the shoulder, 33 to the top of its eclipse, 44 from nose to tail. Built from rigid
segments the game turns with Motor6D joints: Body (with the eclipse), Neck (with the ruff), Head,
Jaw, Tail and TailTip, and an Upper and a Lower per leg. The glowing pieces (the corona, the black
disc, the eyes and their pupils) are Neon pieces riding their segment.

Authored in Roblox studs, standing, facing -Z, its paws on the ground at y = 0.

    import tiangou as T
    T.build()                     # the high-detail segments, in collection TiangouHi
    T.bake(names)                 # bake those segments (a few per call: the connection drops on long runs)
    T.export()                    # assets/guardians/Tiangou.fbx and its pieces report
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
NAME = "Tiangou"
CORONA = "dcefff"        # the eclipse's white fire (meant to bloom white)
DISC = "05070c"          # the swallowed moon: dark Neon renders as a flat black disc
EYE = "ff9a00"           # gold eyes against the midnight coat
PUPIL = "0a0400"         # round pupils, black

ECLIPSE = V((0.0, 27.5, -3.5))       # the eclipse's centre, its face toward -Z
ECLIPSE_R = 6.0
ECLIPSE_TILT = V((0.0, 0.12, -1.0)).normalized()   # its normal: leaning back a little

# segment: (parent, pivot): where it turns on its parent (Roblox studs)
PIVOTS = {
    "Body": (None, (0.0, 14.0, 1.0)),
    "Neck": ("Body", (0.0, 16.5, -8.4)),
    "Head": ("Neck", (0.0, 21.2, -13.8)),
    "Jaw": ("Head", (0.0, 21.3, -16.8)),
    "Tail": ("Body", (0.0, 15.6, 10.6)),
    "TailTip": ("Tail", (0.0, 20.5, 17.5)),
    "FrontLeftUpper": ("Body", (-3.0, 13.5, -6.5)),
    "FrontLeftLower": ("FrontLeftUpper", (-3.2, 8.5, -6.0)),
    "FrontRightUpper": ("Body", (3.0, 13.5, -6.5)),
    "FrontRightLower": ("FrontRightUpper", (3.2, 8.5, -6.0)),
    "BackLeftUpper": ("Body", (-3.0, 13.6, 8.6)),
    "BackLeftLower": ("BackLeftUpper", (-3.4, 8.5, 6.0)),
    "BackRightUpper": ("Body", (3.0, 13.6, 8.6)),
    "BackRightLower": ("BackRightUpper", (3.4, 8.5, 6.0)),
}


# ---------- materials ----------
def mat_coat(name="TiangouCoat"):
    """The night sky as fur: deep midnight blue in fine strands running back along the body,
    silvered where the moonlight falls on the upper faces, and faint stars caught in it, gathered in
    constellations (bright specks only where a broad noise allows)."""
    g = Hm._Graph(name)
    co = g.coords()
    mp = g.n("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (7.0, 0.9, 7.0)          # strands along Blender Y (the body's length)
    g.link(co, mp.inputs["Vector"])
    strands = g.n("ShaderNodeTexNoise", **{"Scale": 4.0, "Detail": 8.0, "Roughness": 0.7})
    g.link(mp.outputs[0], strands.inputs["Vector"])
    col = g.ramp(strands.outputs["Fac"], [(0.3, (0.005, 0.008, 0.03)), (0.7, (0.022, 0.034, 0.095))])
    broad = g.n("ShaderNodeTexNoise", **{"Scale": 0.35, "Detail": 3.0})
    g.link(co, broad.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", broad.outputs["Fac"], 0.35), col, (0.04, 0.03, 0.11))     # a violet drift through it
    geo = g.n("ShaderNodeNewGeometry")
    up = g.sep(geo.outputs["Normal"])[2]
    moon = g.math("MULTIPLY", g.math("SUBTRACT", up, 0.3, clamp=True), g.math("ADD", 0.4, g.math("MULTIPLY", strands.outputs["Fac"], 0.9)))
    col = g.mix(g.math("MINIMUM", moon, 0.8), col, (0.3, 0.36, 0.5))
    stars = g.n("ShaderNodeTexVoronoi", **{"Scale": 2.6})
    g.link(co, stars.inputs["Vector"])
    cluster = g.n("ShaderNodeTexNoise", **{"Scale": 0.5, "Detail": 2.0})
    g.link(co, cluster.inputs["Vector"])
    star = g.math("MULTIPLY", g.math("LESS_THAN", stars.outputs["Distance"], 0.045), g.math("GREATER_THAN", cluster.outputs["Fac"], 0.52))
    col = g.mix(star, col, (0.85, 0.9, 1.0))
    col = g.ao(col, 0.25, 0.45)
    return g.finish(col, 0.6, 0.0, g.bump(strands.outputs["Fac"], 0.35, 0.02))


def mat_flame(name="TiangouFlame"):
    """White fire: a tuft pale blue at its root, whitening to the tip (UV v along it)."""
    g = Hm._Graph(name)
    u, v, _ = g.sep(g.coords("UV"))
    col = g.ramp(v, [(0.0, (0.3, 0.42, 0.85)), (0.45, (0.72, 0.84, 1.0)), (1.0, (1.0, 1.0, 1.0))])
    du = g.math("ABSOLUTE", g.math("SUBTRACT", u, 0.5))
    col = g.mix(g.math("MULTIPLY", g.math("GREATER_THAN", du, 0.4), 0.3), col, (0.55, 0.68, 1.0))
    return g.finish(col, 0.45, 0.0)


def mat_plain(name, color, rough, metal=0.0):
    g = Hm._Graph(name)
    co = g.coords()
    n = g.n("ShaderNodeTexNoise", **{"Scale": 6.0, "Detail": 4.0})
    g.link(co, n.inputs["Vector"])
    col = g.mix(g.math("MULTIPLY", n.outputs["Fac"], 0.25), color, tuple(c * 1.6 for c in color))
    col = g.ao(col, 0.1, 0.5)
    return g.finish(col, rough, metal, g.bump(n.outputs["Fac"], 0.15, 0.01))


def materials():
    return {"coat": mat_coat(), "flame": mat_flame(), "moon": Hm.mat_moonstone("TiangouMoonstone"),
            "nose": mat_plain("TiangouNose", (0.008, 0.008, 0.012), 0.35), "ivory": mat_plain("TiangouIvory", (0.62, 0.6, 0.52), 0.4),
            "silver": Hm.mat_moonsilver("TiangouSilver")}


# ---------- shapes ----------
cone, sphere, frame = G.cone, G.sphere, G.frame


wisp = G.wisp


limb = G.limb


soften = G.soften


def ear(hi, base, tip, front, width, depth):
    """A pointed ear: a three-sided pyramid from a base triangle (two front corners, one behind) to
    the tip, its hollow (the front face) dished in a little."""
    f = V(front).normalized()
    up = (V(tip) - V(base)).normalized()
    across = up.cross(f).normalized()
    a, b = V(base) + across * width, V(base) - across * width
    c = V(base) - f * depth
    hollow = (a + b + V(tip)) / 3 - f * 0.25
    ia, ib, ic, it, ih = hi.v(a), hi.v(b), hi.v(c), hi.v(tip), hi.v(hollow)
    for tri, out in (([ia, ib, ih], f), ([ib, it, ih], f), ([it, ia, ih], f), ([ib, ic, it], -f + across), ([ic, ia, it], -f - across),
                     ([ia, ic, ib], -up)):
        hi.facing(tri, [(0, 0), (1, 0), (0.5, 1)], tuple(out))


def flame_ring(hi, centre, axis, radius, count, length, rnd, lean=0.6, width=0.3):
    """Wisps of white fire round a ring (a ruff): each from the ring outward and back along
    `axis`, curling up at the tip."""
    n, s_, t = frame(axis)
    for k in range(count):
        a = TAU * (k + rnd.uniform(-0.3, 0.3)) / count
        out = s_ * math.cos(a) + t * math.sin(a)
        base = V(centre) + out * radius
        d = (out * rnd.uniform(0.6, 1.0) + V(axis) * lean * rnd.uniform(0.7, 1.3) + V((0, rnd.uniform(0.1, 0.45), 0))).normalized()
        up = V((0, 1, 0)) + out * rnd.uniform(0.2, 0.8) + V(axis) * rnd.uniform(-0.4, 0.4)
        wisp(hi, base, d, up, length * rnd.uniform(0.65, 1.3), width * rnd.uniform(0.8, 1.25), rnd)


# ---------- the segments ----------
def body(coll, M):
    spine = [((0, 13.6 - 0.25 * k, -6.0 + 1.0 * k), (3.7 - 0.12 * k, 4.3 - 0.2 * k, 3.0), None) for k in range(7)]   # chest into the waist
    spine += [((0, 14.9 + 0.08 * k, 1.5 + 1.1 * k), (2.7 + 0.12 * k, 2.4 + 0.12 * k, 2.4), None) for k in range(7)]   # the back up to the hips
    flesh = G.blob("TG_Body", coll, M["coat"], spine + [
        ((0, 10.6, -5.6), (2.6, 2.4, 3.0), None),                                                   # the deep brisket
        ((-2.3, 14.4, -5.6), (1.6, 2.6, 2.4), None), ((2.3, 14.4, -5.6), (1.6, 2.6, 2.4), None),   # shoulders
        ((-2.1, 13.6, 8.6), (1.7, 2.6, 2.6), None), ((2.1, 13.6, 8.6), (1.7, 2.6, 2.6), None),     # haunches
        ((0, 16.0, -8.0), (2.3, 2.7, 2.5), None)], voxel=0.12, smooth=0.7, rough=0.015, chisel="TiangouFur")
    soften(flesh, 30)
    disc, corona, moon, flames = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    n, s, t = frame(ECLIPSE_TILT)        # n: the eclipse's face (toward -Z); s, t span it
    if t.y < 0:
        t = -t
    s = t.cross(n)
    at = lambda a, r, depth=0.0: ECLIPSE + (s * math.cos(a) + t * math.sin(a)) * r + n * depth
    # the swallowed moon: a black disc, both faces and its rim
    m = 48
    for side in (1, -1):
        ring = [disc.v(at(TAU * i / m, ECLIPSE_R, 0.2 * side)) for i in range(m)]
        mid = disc.v(ECLIPSE + n * 0.2 * side)
        for i in range(m):
            disc.facing([mid, ring[i], ring[(i + 1) % m]], [(0.5, 0.5), (0, 0), (1, 0)], tuple(n * side))
    rim = [(disc.v(at(TAU * i / m, ECLIPSE_R, 0.2)), disc.v(at(TAU * i / m, ECLIPSE_R, -0.2))) for i in range(m)]
    for i in range(m):
        j = (i + 1) % m
        out = s * math.cos(TAU * (i + 0.5) / m) + t * math.sin(TAU * (i + 0.5) / m)
        disc.facing([rim[i][0], rim[j][0], rim[j][1], rim[i][1]], [(0, 0), (1, 0), (1, 1), (0, 1)], tuple(out))
    # the corona: a ring of white fire, tongues of it licking outward, and a few long streamers,
    # uneven as a real corona
    ring = [at(TAU * i / 64, ECLIPSE_R + 0.25) for i in range(64)]
    Hm.htube(corona, ring + ring[:2], lambda q: 0.32, sides=8, per=1, uv_scale=1.0, tip=False, wobble=0.0)
    rnd = random.Random(17)
    for k in range(34):
        a = TAU * (k + rnd.uniform(-0.35, 0.35)) / 34
        out = s * math.cos(a) + t * math.sin(a)
        tangent = n.cross(out)
        length = rnd.uniform(0.9, 2.6)
        wisp(corona, at(a, ECLIPSE_R + 0.15, rnd.uniform(-0.3, 0.3)), out + tangent * rnd.uniform(-0.45, 0.45) + n * rnd.uniform(-0.5, 0.5),
             out + tangent * rnd.uniform(-0.6, 0.6), length, 0.3, rnd, sides=5)
    for a_deg, length in ((62, 6.5), (118, 5.2), (205, 4.2), (338, 4.6), (12, 3.6)):
        a = math.radians(a_deg)
        out = s * math.cos(a) + t * math.sin(a)
        wisp(corona, at(a, ECLIPSE_R + 0.2), out, out + n.cross(out) * 0.5, length, 0.42, rnd, sides=6)
    # the last silver crescent of the moon, at the bottom of the disc, cradling the egg
    outer, inner = ECLIPSE_R - 0.1, ECLIPSE_R - 1.7
    lift = 1.3                                   # the inner arc's centre sits higher: a crescent, thickest at the bottom
    steps = 40
    a0, a1 = math.radians(200), math.radians(340)
    front, back = [], []
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        p_out = at(a, outer)
        # the inner edge: on a circle of radius `inner` round a point `lift` above the centre, met by the same ray
        d = s * math.cos(a) + t * math.sin(a)
        c2 = ECLIPSE + t * lift
        # solve |c + d*r - c2| = inner for r
        oc = ECLIPSE - c2
        b_ = oc.dot(d)
        disc_ = b_ * b_ - (oc.dot(oc) - inner * inner)
        r_in = -b_ + math.sqrt(max(0.0, disc_))
        r_in = min(r_in, outer - 0.05)
        p_in = ECLIPSE + d * r_in
        front.append((moon.v(p_out + n * 1.9), moon.v(p_in + n * 1.9)))     # deep enough to cradle the egg before the disc
        back.append((moon.v(p_out - n * 0.1), moon.v(p_in - n * 0.1)))
    for i in range(steps):
        (fo, fi), (fo2, fi2) = front[i], front[i + 1]
        (bo, bi), (bo2, bi2) = back[i], back[i + 1]
        u0, u1 = i / steps, (i + 1) / steps
        moon.facing([fo, fo2, fi2, fi], [(u0, 0), (u1, 0), (u1, 1), (u0, 1)], tuple(n))
        moon.facing([bo, bi, bi2, bo2], [(u0, 0), (u0, 1), (u1, 1), (u1, 0)], tuple(-n))
        d = (s * math.cos(a0 + (a1 - a0) * (i + 0.5) / steps) + t * math.sin(a0 + (a1 - a0) * (i + 0.5) / steps))
        moon.facing([fo, bo, bo2, fo2], [(u0, 0), (u0, 1), (u1, 1), (u1, 0)], tuple(d))
        moon.facing([fi, fi2, bi2, bi], [(u0, 0), (u1, 0), (u1, 1), (u0, 1)], tuple(-d))
    for end in (0, steps):
        fo, fi = front[end]
        bo, bi = back[end]
        moon.f([fo, fi, bi, bo], [(0, 0), (1, 0), (1, 1), (0, 1)])
    # streams of white fire rising from its shoulders to the crescent's horns, holding the eclipse up
    for side in (-1, 1):
        horn = at(math.radians(200 if side < 0 else 340), outer - 0.6, 0.3)
        for k in range(3):
            start = V((side * (1.6 + 0.5 * k), 17.0 - 0.3 * k, -5.6 + 0.5 * k))
            wisp(flames, start, horn - start, V((side * 0.5, 0.3, -0.4)), (horn - start).length * 1.05, 0.42 - 0.08 * k, rnd, sides=7)
    m_ = moon.object("TG_BodyMoon", coll, [M["moon"]])
    m_["keep"] = True
    fl = flames.object("TG_BodyFlames", coll, [M["flame"]])
    fl["keep"] = True
    return [flesh, m_, fl], \
        {DISC: [disc.object("TG_Disc", coll, [K.glow_material(DISC)], smooth=False)],
         CORONA: [corona.object("TG_Corona", coll, [K.glow_material(CORONA)], smooth=True)]}


def neck(coll, M):
    o = soften(G.blob("TG_Neck", coll, M["coat"], limb((0, 16.2, -8.2), (0, 21.0, -13.6), 2.4, 1.75), voxel=0.1, smooth=0.7, rough=0.015,
                      chisel="TiangouFur"))
    ruff = Hm.Hi()
    rnd = random.Random(5)
    axis = V((0, 4.8, -5.4)).normalized()
    for q, count, length in ((0.05, 22, 4.4), (0.28, 20, 3.8), (0.5, 16, 3.0), (0.72, 12, 2.3)):
        c = V((0, 16.2, -8.2)).lerp(V((0, 21.0, -13.6)), q)
        flame_ring(ruff, c, -axis, 2.2 - 0.45 * q, count, length, rnd, lean=0.85, width=0.36)
    r = ruff.object("TG_NeckRuff", coll, [M["flame"]])
    r["keep"] = True                     # thin wisps: decimating them would shred them
    return [o, r], {}


def head(coll, M):
    lobes = [((0, 22.7, -15.4), (2.5, 2.3, 2.7), None), ((-1.55, 21.8, -16.5), (1.3, 1.35, 1.7), None), ((1.55, 21.8, -16.5), (1.3, 1.35, 1.7), None),
             ((-1.0, 24.0, -17.1), (1.0, 0.5, 1.2), (0, 0, -12)), ((1.0, 24.0, -17.1), (1.0, 0.5, 1.2), (0, 0, 12))]
    lobes += [((0, 22.3 - 0.12 * k, -17.6 - 0.45 * k), (1.5 - 0.075 * k, 1.4 - 0.05 * k, 1.05), None) for k in range(9)]   # the muzzle, deep, tapering
    skull = soften(G.blob("TG_Head", coll, M["coat"], lobes, voxel=0.07, smooth=0.75, rough=0.015, chisel="TiangouFur"), 8)
    glow, pupils, lids, nose, teeth, ears, cheeks = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    rnd = random.Random(3)
    for side in (-1, 1):
        normal = V((side * 0.72, 0.18, -0.67)).normalized()
        seat = G.surface_along(skull, V((side * 1.5, 23.0, -17.6)), normal)
        # a hunter's stare: a long almond under a low brow, the line dropping toward the muzzle
        G.eye(glow, pupils, lids, seat, normal, (0, -0.1, -1), 0.8, 0.44, tilt=0.22, bulge=0.13, lid=0.42, droop=0.4, lower=0.2,
              slit=0.26, pupil_height=0.48)
        # tall pointed ears, swept back, their hollows facing forward with a flicker of white fire in each
        base = V((side * 1.35, 23.9, -14.4))
        tip = base + V((side * 1.3, 4.6, 1.5))
        ear(ears, base, tip, V((side * 0.25, 0.05, -1)), 1.05, 0.55)
        for k in range(2):
            wisp(cheeks, base + V((side * (0.2 + 0.35 * k), 0.4, -0.45)), tip - base + V((0, 0, -0.6)), V((0, 0, -1)), 2.2 - 0.5 * k, 0.2, rnd, sides=5)
        # flames trailing from its cheeks
        for k in range(4):
            wisp(cheeks, (side * 2.2, 21.9 - 0.4 * k, -15.4 + 0.45 * k), (side * 0.55, 0.1, 1), (0, 1, 0.3), 3.0 - 0.4 * k, 0.32, rnd)
        cone(teeth, (side * 0.62, 21.15, -20.9), (side * 0.6, 20.25, -21.1), 0.17, sides=6)        # the upper fangs
    nose_at = G.surface_along(skull, V((0, 21.75, -21.0)), V((0, 0.15, -1)).normalized())
    sphere(nose, nose_at + V((0, 0.05, 0.12)), 0.5, nu=12, nv=8, radii=(0.62, 0.46, 0.42))
    n = nose.object("TG_HeadNose", coll, [M["nose"]])
    n["keep"] = True
    tt = teeth.object("TG_HeadTeeth", coll, [M["ivory"]])
    tt["keep"] = True
    lid = lids.object("TG_HeadLids", coll, [M["coat"]])
    lid["keep"] = True
    ch = cheeks.object("TG_HeadCheeks", coll, [M["flame"]])
    ch["keep"] = True
    e = ears.object("TG_HeadEars", coll, [M["coat"]], smooth=False)
    e["keep"] = True
    return [skull, n, tt, lid, e, ch], \
        {EYE: [glow.object("TG_Eyes", coll, [K.glow_material(EYE)], smooth=True)],
         PUPIL: [pupils.object("TG_Pupils", coll, [K.glow_material(PUPIL)], smooth=True)]}


def jaw(coll, M):
    lobes = [((0, 20.75 - 0.04 * k, -17.4 - 0.45 * k), (1.2 - 0.07 * k, 0.6, 0.9), None) for k in range(8)]
    o = soften(G.blob("TG_Jaw", coll, M["coat"], lobes, voxel=0.07, smooth=0.75, rough=0.015, chisel="TiangouFur"), 8)
    teeth = Hm.Hi()
    for side in (-1, 1):
        cone(teeth, (side * 0.55, 20.75, -20.5), (side * 0.53, 21.5, -20.65), 0.14, sides=6)
    tt = teeth.object("TG_JawTeeth", coll, [M["ivory"]])
    tt["keep"] = True
    return [o, tt], {}


def tail(coll, M):
    hi, plume = Hm.Hi(), Hm.Hi()
    curve = G.resample([(0, 15.6, 10.4), (0, 17.6, 14.0), (0, 20.5, 17.5)], 0.3)
    Hm.htube(hi, curve, lambda q: 1.25 - 0.35 * q, sides=12, per=1, uv_scale=1.0, tip=False, wobble=0.0)
    sphere(hi, curve[0], 1.25, nu=12, nv=8)
    rnd = random.Random(23)
    for i, c in enumerate(curve[2::2]):
        flame_ring(plume, c, (curve[-1] - curve[0]).normalized(), 1.0, 8, 2.8 + 0.15 * i, rnd, lean=0.55, width=0.38)
    pl = plume.object("TG_TailPlume", coll, [M["flame"]])
    pl["keep"] = True
    tb = hi.object("TG_Tail", coll, [M["coat"]])
    tb["keep"] = True                    # a plain tube, already light
    return [tb, pl], {}


def tail_tip(coll, M):
    hi, plume = Hm.Hi(), Hm.Hi()
    curve = G.resample([(0, 20.5, 17.5), (0, 23.4, 20.4), (0, 25.6, 21.6), (0, 26.4, 20.8)], 0.3)
    Hm.htube(hi, curve, lambda q: 0.9 * (1 - 0.8 * q), sides=10, per=1, uv_scale=1.0, tip=True, wobble=0.0)
    sphere(hi, curve[0], 0.9, nu=10, nv=8)
    rnd = random.Random(29)
    for i, c in enumerate(curve[1::2]):
        q = i / max(1, len(curve) // 2)
        flame_ring(plume, c, (curve[min(len(curve) - 1, (i + 1) * 2)] - c).normalized() if i * 2 + 2 < len(curve) else V((0, 0.2, -1)),
                   0.8 * (1 - 0.7 * q), 10, 3.8 * (1 - 0.25 * q), rnd, lean=0.6, width=0.4)
    pl = plume.object("TG_TailTipPlume", coll, [M["flame"]])
    pl["keep"] = True
    tb = hi.object("TG_TailTip", coll, [M["coat"]])
    tb["keep"] = True
    return [tb, pl], {}


LEGS = {   # left side: shoulder or hip, elbow or stifle, wrist or hock, paw centre
    "Front": ((-3.0, 13.5, -6.5), (-3.2, 8.5, -6.0), (-3.2, 2.2, -6.6), (-3.2, 0.65, -7.6)),
    "Back": ((-3.0, 13.6, 8.6), (-3.4, 8.5, 6.0), (-3.3, 4.0, 10.4), (-3.3, 0.65, 9.6)),
}


def leg(coll, M, name, side, pair, part):
    a, b, c, paw = (V((-side * p[0], p[1], p[2])) for p in LEGS[pair])
    feather, claws = Hm.Hi(), Hm.Hi()
    rnd = random.Random(len(name) * 7 + (1 if side > 0 else 0))
    if part == "Upper":
        if pair == "Front":
            lobes = limb(a + V((0, 1.0, 0.3)), b, 1.75, 1.0)
        else:
            lobes = limb(a + V((0, 0.8, 0)), b, 2.1, 1.05) + [(tuple(a.lerp(b, 0.35) + V((0, 0, 0.7))), (1.6, 2.3, 1.8), None)]   # the thigh
        o = soften(G.blob("TG_" + name, coll, M["coat"], lobes, voxel=0.08, smooth=0.7, rough=0.015, chisel="TiangouFur"))
        return [o], {}
    lobes = limb(b, c, 0.95, 0.6) + limb(c, paw + V((0, 0.4, 0.35)), 0.6, 0.55)
    lobes.append((tuple(paw), (0.95, 0.6, 1.3), None))
    for dx in (-0.55, -0.18, 0.18, 0.55):
        lobes.append((tuple(paw + V((dx, -0.1, -1.05 + 0.25 * abs(dx)))), (0.36, 0.42, 0.45), None))
    o = soften(G.blob("TG_" + name, coll, M["coat"], lobes, voxel=0.06, smooth=0.7, rough=0.015, chisel="TiangouFur"), 8)
    for dx in (-0.55, -0.18, 0.18, 0.55):
        base = paw + V((dx, 0.0, -1.35 + 0.25 * abs(dx)))
        cone(claws, base, base + V((dx * 0.2, -0.45, -0.55)), 0.13, sides=6)
    # white fire feathering the back of the leg (the forearm, the hock)
    for k in range(4):
        q = 0.25 + 0.17 * k
        p = (b.lerp(c, q) if pair == "Front" else c.lerp(b, q * 0.6)) + V((0, 0, 0.55))
        wisp(feather, p, V((side * 0.25, -0.2, 1)), V((0, 1, 0)), 2.0 - 0.2 * k, 0.24, rnd, sides=5)
    cl = claws.object("TG_" + name + "Claws", coll, [M["silver"]])
    cl["keep"] = True
    fe = feather.object("TG_" + name + "Feather", coll, [M["flame"]])
    fe["keep"] = True
    return [o, cl, fe], {}


def segments():
    out = {"Body": body, "Neck": neck, "Head": head, "Jaw": jaw, "Tail": tail, "TailTip": tail_tip}
    for side, s in ((-1, "Left"), (1, "Right")):
        for pair in ("Front", "Back"):
            for part in ("Upper", "Lower"):
                name = pair + s + part
                out[name] = (lambda n, sd, pr, pt: lambda c, M: leg(c, M, n, sd, pr, pt))(name, side, pair, part)
    return out


BUDGET = {"Body": 12000, "Neck": 11500, "Head": 12000, "Jaw": 3000, "Tail": 8500, "TailTip": 12500}   # each leg piece: 3500 (plumes and ruff kept whole)


def build(only=None):
    M = materials()
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


def bake(names):
    """Bakes these segments' game meshes (built already); records them for export()."""
    parts = bpy.app.driver_namespace.setdefault("tiangou_parts", {})
    for name in names:
        coll = bpy.data.collections[NAME + "_" + name]
        hi = [o for o in coll.objects if o.name.startswith("TG_") and o.type == "MESH"]
        low = G.bake_piece(NAME, name, hi, coll, BUDGET.get(name, 3500))
        parts[name] = (name, low.name)
    return {n: B.tris(bpy.data.objects[parts[n][1]]) for n in names}


def export():
    return G.export(NAME, PIVOTS, bpy.app.driver_namespace["tiangou_parts"])
