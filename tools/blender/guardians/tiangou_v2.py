"""Tiangou the Moon-Eater, rebuilt with a real skeleton (the owner, 2026-11-04: "all the boss in the game is actually
stiff ... please put rig, skeleton and more weight paint"). The character is the same: the heavenly hound of the eclipse
myth, a lean sighthound with a coat of night sky, white fire and the eclipse it made above its shoulders. What changes
is its construction: one continuous skin over about 40 bones.

Authored in Roblox studs: standing, facing -Z, its paws on the ground at y = 0, the same size as before, so the fight's
ranges still hold (its nose about 22 studs ahead of its origin, its shoulder 14 up).

    import tiangou_v2 as T
    T.build_form()        # the skin as plain clay, and the skeleton
    T.bind()              # weights, cleaned to 4 influences a vertex
    T.review_form(path)   # clay from six sides
    T.stress(path)        # the skeleton bent to its limits, to judge the weights
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

import egg_hi as Hm
import egg_kit as K
import guardian_kit as G

W = K.W
V = Vector

TAU = 2 * math.pi

CORONA = "dcefff"        # the eclipse's white fire (meant to bloom white)

DISC = "05070c"          # the swallowed moon: dark Neon renders as a flat black disc

EYE = "ff9a00"           # gold eyes against the midnight coat

PUPIL = "0a0400"         # round pupils, black

ECLIPSE = V((0.0, 27.5, -3.5))       # the eclipse's centre, its face toward -Z

ECLIPSE_R = 6.0

ECLIPSE_TILT = V((0.0, 0.12, -1.0)).normalized()   # its normal: leaning back a little

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

soften = G.soften

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
NAME = "Tiangou"

# bone: (parent, head, tail), Roblox studs. Left is -X. Names follow the game's joints where they can.
_B = {
    "Root": (None, (0, 0, 0), (0, 0, -3)),
    "Hips": ("Root", (0, 15.0, 8.6), (0, 15.2, 3.6)),
    "Spine": ("Hips", (0, 15.2, 3.6), (0, 15.5, -1.6)),
    "Chest": ("Spine", (0, 15.5, -1.6), (0, 16.2, -7.6)),
    "Neck1": ("Chest", (0, 16.2, -7.6), (0, 18.8, -10.8)),
    "Neck2": ("Neck1", (0, 18.8, -10.8), (0, 21.2, -13.6)),
    "Head": ("Neck2", (0, 21.2, -13.6), (0, 21.0, -21.8)),
    "Jaw": ("Head", (0, 20.8, -15.4), (0, 20.55, -20.9)),
    "Eyes": ("Head", (0, 22.55, -16.5), (0, 22.55, -17.5)),   # both eyes: slid into their sockets to blink and to narrow
    "Tail1": ("Hips", (0, 15.6, 10.8), (0, 16.3, 13.6)),
    "Tail2": ("Tail1", (0, 16.3, 13.6), (0, 17.6, 16.2)),
    "Tail3": ("Tail2", (0, 17.6, 16.2), (0, 19.5, 18.4)),
    "Tail4": ("Tail3", (0, 19.5, 18.4), (0, 21.9, 19.9)),
    "Tail5": ("Tail4", (0, 21.9, 19.9), (0, 24.4, 20.7)),
}


def _side(sign, tag):
    """A side's bones. sign: -1 left, +1 right."""
    x = lambda v: v * sign
    b = {
        "Ear": ("Head", (x(1.2), 23.0, -14.5), (x(1.8), 26.6, -13.9)),
        # the foreleg: the shoulder blade slides on the ribs; the arm runs back to the elbow; the forearm straight down
        "FrontBlade": ("Chest", (x(2.1), 16.3, -4.2), (x(2.9), 12.3, -7.0)),
        "FrontUpper": ("FrontBlade", (x(2.9), 12.3, -7.0), (x(3.0), 8.7, -4.8)),
        "FrontLower": ("FrontUpper", (x(3.0), 8.7, -4.8), (x(3.1), 2.3, -5.3)),
        "FrontPaw": ("FrontLower", (x(3.1), 2.3, -5.3), (x(3.1), 0.45, -7.5)),
        # the hind leg: the thigh runs forward to the stifle, the shin back to the hock, then the long rear pastern
        "BackUpper": ("Hips", (x(2.6), 14.1, 9.0), (x(3.1), 8.9, 5.5)),
        "BackLower": ("BackUpper", (x(3.1), 8.9, 5.5), (x(3.3), 5.4, 10.8)),
        "BackMeta": ("BackLower", (x(3.3), 5.4, 10.8), (x(3.3), 1.5, 10.0)),
        "BackPaw": ("BackMeta", (x(3.3), 1.5, 10.0), (x(3.3), 0.45, 7.7)),
    }
    return {tag + name: (((tag + p) if p in b else p), h, t) for name, (p, h, t) in b.items()}


_B.update(_side(-1, "Left"))
_B.update(_side(1, "Right"))
BONES = _B


def _clay():
    m = bpy.data.materials.get("TiangouClay") or bpy.data.materials.new("TiangouClay")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.42, 0.43, 0.46, 1)
    b.inputs["Roughness"].default_value = 0.65
    return m


def _limb(points, radii, per=None):
    """A limb: one continuous tapered form per span, its cross-section going between the points' radii (x, y, z)."""
    return [("seg", tuple(points[i]), tuple(points[i + 1]), tuple(radii[i]), tuple(radii[i + 1])) for i in range(len(points) - 1)]


def _paw(x, y, z, reach, sign):
    """A paw: a pad and four toes, the middle two longest, each its own soft form."""
    lobes = [((x, y + 0.14, z), (0.66, 0.46, 0.78), None)]
    for k, (dx, length) in enumerate(((-0.46, 0.62), (-0.16, 0.86), (0.16, 0.86), (0.46, 0.62))):
        lobes.append(((x + dx * sign, 0.34, z - reach * length), (0.25, 0.3, 0.42), None))
    return lobes


def _groups():
    """The body as groups of soft forms: (how softly the group's forms melt together, its forms)."""
    groups = []
    # the torso: a deep keeled ribcage rising to a tucked loin, one long sweep, not rings
    groups.append((1.15, [
        ((0, 13.5, -3.6), (2.9, 4.5, 5.6), (-8, 0, 0)),          # the ribcage
        ((0, 11.6, -5.8), (1.9, 2.5, 2.8), None),                 # the breast, the keel
        ((0, 16.5, -5.2), (1.9, 1.5, 3.0), None),                 # the withers
        ((0, 15.3, 3.2), (2.0, 1.9, 4.6), (4, 0, 0)),             # the loin
        ((0, 15.0, 8.6), (2.5, 2.25, 2.9), (10, 0, 0)),           # the croup, falling to the tail
    ]))
    # the neck: wide into the shoulders and fine under the skull, one arch
    groups.append((1.6, _limb([(0, 16.1, -6.6), (0, 18.0, -9.5), (0, 20.2, -12.2), (0, 21.5, -13.9)],
                              [(2.4, 2.9, 2.7), (1.75, 2.05, 2.0), (1.3, 1.5, 1.45), (1.15, 1.25, 1.2)])))
    # the head: a narrow wedge. Skull, brow, cheek, a long muzzle
    groups.append((0.42, [
        ((0, 22.2, -15.1), (1.5, 1.35, 1.85), None),
        ((0, 22.75, -16.2), (1.05, 0.72, 1.2), None),             # the brow
        ((-1.08, 21.5, -15.6), (0.55, 0.85, 1.1), None), ((1.08, 21.5, -15.6), (0.55, 0.85, 1.1), None),   # the cheeks
    ] + _limb([(0, 21.95, -16.7), (0, 21.55, -18.8), (0, 21.2, -21.0)], [(0.98, 0.88, 1.3), (0.68, 0.6, 1.3), (0.46, 0.42, 0.62)], per=3)))
    for sign in (-1, 1):
        x = lambda v: v * sign
        # the ear: broad at its root, pointed, leaning back
        groups.append((0.1, _limb([(x(1.2), 23.0, -14.5), (x(1.55), 24.4, -14.3), (x(1.8), 26.2, -13.9)],
                                  [(0.72, 0.8, 0.3), (0.52, 1.0, 0.25), (0.08, 0.5, 0.09)], per=3)))
        # the foreleg: a flat shoulder blade lying on the ribs, the arm back to the elbow, a clean straight forearm
        groups.append((0.9, [((x(2.2), 14.3, -4.9), (0.7, 2.8, 1.9), (0, 0, x(-7)))]
                       + _limb([(x(2.6), 12.3, -6.5), (x(2.95), 8.7, -4.8)], [(0.9, 1.9, 1.7), (0.76, 1.05, 1.0)])
                       + _limb([(x(2.95), 8.7, -4.8), (x(3.0), 5.4, -5.05), (x(3.05), 2.5, -5.25)], [(0.72, 0.95, 0.92), (0.46, 0.9, 0.58), (0.4, 0.55, 0.48)])
                       + _limb([(x(3.05), 2.5, -5.25), (x(3.08), 1.2, -5.8)], [(0.4, 0.55, 0.48), (0.48, 0.6, 0.62)], per=2)
                       + _paw(x(3.08), 0.5, -6.2, 1.35, sign)))
        # the hind leg: a broad flat thigh, a long shin, the hock's point, a long upright pastern
        groups.append((1.0, [((x(1.85), 13.4, 8.3), (0.9, 2.8, 2.7), (12, 0, 0))]
                       + _limb([(x(2.4), 11.8, 7.6), (x(3.0), 9.2, 5.9)], [(0.9, 2.0, 2.0), (0.8, 1.15, 1.2)])
                       + _limb([(x(3.0), 9.2, 5.9), (x(3.15), 7.0, 8.4), (x(3.25), 5.4, 10.7)], [(0.78, 1.05, 1.1), (0.52, 0.7, 0.85), (0.36, 0.5, 0.56)])
                       + _limb([(x(3.25), 5.4, 10.7), (x(3.25), 3.4, 10.3), (x(3.25), 1.6, 9.95)], [(0.36, 0.5, 0.56), (0.34, 0.9, 0.42), (0.38, 0.55, 0.46)])
                       + _paw(x(3.25), 0.5, 9.3, 1.3, sign)))
    # the tail: slender, rising in one curve (its plume of white fire comes later)
    pts = [_B["Tail1"][1], _B["Tail2"][1], _B["Tail3"][1], _B["Tail4"][1], _B["Tail5"][1], _B["Tail5"][2]]
    rad = [(1.05, 1.1, 1.1), (0.78, 0.82, 0.82), (0.6, 0.64, 0.64), (0.46, 0.48, 0.48), (0.3, 0.32, 0.32), (0.06, 0.08, 0.08)]
    groups.append((0.32, _limb(pts, rad)))
    return groups


def _form_lobes():
    """The forms as plain ellipsoids, only to give the first rough mesh something to wrap."""
    out = []
    for _, lobes in _groups():
        for lobe in lobes:
            if lobe[0] == "seg":
                _, a, b, ra, rb = lobe
                for k in range(5):
                    t = k / 4
                    out.append((tuple(V(a).lerp(V(b), t)), tuple(ra[n] + (rb[n] - ra[n]) * t for n in range(3)), None))
            else:
                out.append(lobe)
    return out


def _smin(a, b, k):
    """A smooth minimum that can't inflate beyond k / 4, however many forms are folded in."""
    import numpy as np
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def _form_distance(points, lobe):
    import numpy as np
    if lobe[0] == "seg":
        _, a, b, ra, rb = lobe
        a, b, ra, rb = (np.array(v, dtype=np.float64) for v in (a, b, ra, rb))
        ab = b - a
        t = np.clip(((points - a) @ ab) / max(ab @ ab, 1e-9), 0.0, 1.0)[:, None]
        q = points - (a + ab * t)
        rr = ra + (rb - ra) * t
    else:
        c, r, rot = lobe
        q = points - np.array(c, dtype=np.float64)
        if rot:
            # into the form's frame (rot is degrees about X, Y, Z in Roblox axes)
            m = np.array(Matrix.Rotation(math.radians(rot[0]), 3, "X") @ Matrix.Rotation(math.radians(rot[1]), 3, "Y") @ Matrix.Rotation(math.radians(rot[2]), 3, "Z"))
            q = q @ m
        rr = np.array(r, dtype=np.float64)
    k0 = np.linalg.norm(q / rr, axis=1)
    k1 = np.linalg.norm(q / (rr * rr), axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)


def _sdf(points, groups, between=1.25):
    """How far points are outside the smooth union of the groups' forms (negative inside): each group's forms melt
    together by its softness, then the groups melt into each other."""
    total = None
    for softness, lobes in groups:
        group = None
        for lobe in lobes:
            d = _form_distance(points, lobe)
            group = d if group is None else _smin(group, d, softness)
        total = group if total is None else _smin(total, group, between)
    return total


def _mouth_line(z):
    """The height of the line between the upper and lower jaw, along the muzzle."""
    t = (z + 16.4) / -5.0
    return 21.32 - 0.36 * t


def _mouth_cut(points, d):
    """The skin stops at the mouth: everything below the line, ahead of the mouth's corner, belongs to the jaw."""
    import numpy as np
    w = np.maximum(points[:, 1] - _mouth_line(points[:, 2]), points[:, 2] + 16.4)   # negative inside the wedge
    return np.maximum(d, -w)


def _jaw_cut(points, d):
    """The jaw's top: flat, just under the mouth's line."""
    import numpy as np
    return np.maximum(d, points[:, 1] - (_mouth_line(points[:, 2]) - 0.06))


def _settle(skin, groups, passes=7, cut=None):
    """Slides every vertex onto the smooth union's surface: the shape's own creases melt away."""
    import numpy as np
    n = len(skin.data.vertices)
    co = np.zeros(n * 3)
    skin.data.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    pts = np.stack([co[:, 0], co[:, 2], -co[:, 1]], axis=1)   # Blender to Roblox
    e = 0.02
    for _ in range(passes):
        for start in range(0, n, 6000):
            chunk = pts[start:start + 6000]
            field = (lambda q: cut(q, _sdf(q, groups))) if cut else (lambda q: _sdf(q, groups))
            d = field(chunk)
            grad = np.stack([(field(chunk + np.eye(3)[a] * e) - d) / e for a in range(3)], axis=1)
            g2 = np.maximum((grad * grad).sum(axis=1, keepdims=True), 1e-4)
            pts[start:start + 6000] = chunk - grad * np.clip(d[:, None] / g2, -0.5, 0.5)
    out = np.stack([pts[:, 0], -pts[:, 2], pts[:, 1]], axis=1)
    skin.data.vertices.foreach_set("co", out.ravel())
    skin.data.update()
    return True


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.actions, bpy.data.cameras, bpy.data.lights, bpy.data.textures, bpy.data.images):
        for x in list(block):
            block.remove(x)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    bpy.data.orphans_purge(do_recursive=True)


def build_skeleton(coll):
    data = bpy.data.armatures.new("TiangouRig")
    arm = bpy.data.objects.new("TiangouRig", data)
    coll.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    made = {}
    for name, (parent, head, tail) in BONES.items():
        b = data.edit_bones.new(name)
        b.head, b.tail = W.rb(*head), W.rb(*tail)
        made[name] = b
    for name, (parent, head, tail) in BONES.items():
        if parent:
            made[name].parent = made[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    for b in data.bones:
        b.use_deform = b.name != "Root"
    return arm


def build_form(voxel=0.14):
    clear()
    coll = bpy.data.collections.new("TiangouV2")
    bpy.context.scene.collection.children.link(coll)
    groups = _groups()
    skin = G.blob("TG2_Skin", coll, _clay(), _form_lobes(), voxel=voxel, smooth=0.75, rough=0.0, chisel="TiangouV2Fur")
    _settle(skin, groups, cut=_mouth_cut)
    G.soften(skin, 8)                # evens out the vertices the settling crowded together
    _settle(skin, groups, passes=2, cut=_mouth_cut)
    arm = build_skeleton(coll)
    return skin, arm


def to_game_mesh(tris=18000):
    """Reduces the skin to the game's budget (Roblox allows 20,000 a mesh), keeping the silhouette."""
    skin = bpy.data.objects["TG2_Skin"]
    now = sum(len(p.vertices) - 2 for p in skin.data.polygons)
    if now > tris:
        m = skin.modifiers.new("Reduce", "DECIMATE")
        m.ratio = tris / now
        bpy.context.view_layer.objects.active = skin
        bpy.ops.object.select_all(action="DESELECT")
        skin.select_set(True)
        bpy.ops.object.modifier_apply(modifier=m.name)
    for p in skin.data.polygons:
        p.use_smooth = True
    return sum(len(p.vertices) - 2 for p in skin.data.polygons)


# how far each bone's own influence reaches round it, in studs: a thin limb's bone mustn't pull on its neighbours
_REACH = {"Hips": 3.6, "Spine": 3.6, "Chest": 4.4, "Neck1": 3.0, "Neck2": 2.2, "Head": 2.2, "Jaw": 1.2}


def _bone_segments():
    import numpy as np
    names, a, b = [], [], []
    for name, (parent, head, tail) in BONES.items():
        if name == "Root":
            continue
        names.append(name)
        a.append(head)
        b.append(tail)
    return names, np.array(a, dtype=np.float64), np.array(b, dtype=np.float64)


def bind(falloff=1.7, influences=4, object_name="TG2_Skin"):
    """Paints the weights from each vertex's distance to the bones, the falloff soft enough for a joint to bend as flesh
    and not as a hinge. Whole regions that must stay rigid (the skull's top against the ears and the jaw, each side's limbs
    against the other side's) are kept apart by which bones may reach them. Cleaned to 4 influences, normalized."""
    import numpy as np
    skin = bpy.data.objects[object_name]
    arm = bpy.data.objects["TiangouRig"]
    n = len(skin.data.vertices)
    co = np.zeros(n * 3)
    skin.data.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    pts = np.stack([co[:, 0], co[:, 2], -co[:, 1]], axis=1)
    names, a, b = _bone_segments()
    ab = b - a
    t = np.clip(np.einsum("ijk,jk->ij", pts[:, None, :] - a[None, :, :], ab) / np.maximum((ab * ab).sum(axis=1), 1e-9), 0, 1)
    d = np.linalg.norm(pts[:, None, :] - (a[None] + t[..., None] * ab[None]), axis=2)
    for j, name in enumerate(names):
        # a vertex on one side of the body belongs to that side's limbs only
        if name.startswith("Left"):
            d[pts[:, 0] > 0.15, j] = 1e6
        elif name.startswith("Right"):
            d[pts[:, 0] < -0.15, j] = 1e6
        if name.endswith("Ear"):
            d[(pts[:, 1] < 23.15) | (np.abs(pts[:, 0]) < 0.55) | (pts[:, 2] < -15.5), j] = 1e6   # the ear, not the eye below it
    # legs below the belly belong only to their leg, the tail only to the tail past its root
    limb = np.array([("Front" in nm or "Back" in nm) for nm in names])
    core = np.array([nm in ("Hips", "Spine", "Chest", "Neck1") for nm in names])
    # below the belly, out on a leg, the trunk lets go; the keel between the legs stays the trunk's. Soft edges: a hard cut tears
    out_on_leg = (pts[:, 1] < 7.5) & (np.abs(pts[:, 0]) > 1.6)
    d[np.ix_(out_on_leg, core)] = 1e6
    keel = np.abs(pts[:, 0]) < 1.5
    d[np.ix_(keel & (pts[:, 2] < 2.5), limb)] += 2.5      # the ribs don't follow a leg's swing
    tail = np.array([nm.startswith("Tail") for nm in names])
    d[np.ix_(pts[:, 2] < 9.5, tail)] = 1e6
    head = np.array([nm in ("Head", "Jaw", "LeftEar", "RightEar") for nm in names])
    d[np.ix_(pts[:, 2] > -11.5, head)] = 1e6
    # the mass over a joint stays with the trunk: only what's below it swings with the limb, so a thigh doesn't fold into a ball
    for j, name in enumerate(names):
        if name.endswith("BackUpper"):
            d[:, j] += np.maximum(pts[:, 1] - 12.6, 0.0) * 1.5
        elif name.endswith("FrontUpper"):
            d[:, j] += np.maximum(pts[:, 1] - 11.6, 0.0) * 1.5
        elif name.endswith("FrontBlade"):
            d[:, j] += np.abs(pts[:, 0]) < 1.2
    for j, name in enumerate(names):
        if name in ("Jaw", "Eyes"):
            d[:, j] = 1e6                 # their own pieces, rigid
    near = d.min(axis=1, keepdims=True)
    w = np.exp(-((d - near) / falloff) ** 2 * 2.2)
    w[d >= 1e5] = 0
    order = np.argsort(-w, axis=1)[:, :influences]
    keep = np.zeros_like(w)
    rows = np.arange(n)[:, None]
    keep[rows, order] = w[rows, order]
    keep[keep < 0.02] = 0
    keep /= keep.sum(axis=1, keepdims=True)
    skin.vertex_groups.clear()
    groups = {nm: skin.vertex_groups.new(name=nm) for nm in names}
    for j, nm in enumerate(names):
        idx = np.nonzero(keep[:, j])[0]
        vg = groups[nm]
        for i in idx.tolist():
            vg.add([i], float(keep[i, j]), "REPLACE")
    for mod in list(skin.modifiers):
        if mod.type == "ARMATURE":
            skin.modifiers.remove(mod)
    md = skin.modifiers.new("Armature", "ARMATURE")
    md.object = arm
    skin.parent = arm
    return {"verts": n, "max influences": int((keep > 0).sum(axis=1).max()), "unweighted": int((keep.sum(axis=1) < 0.99).sum())}


def rb_rot(x=0, y=0, z=0):
    """A rotation given in Roblox axes (degrees, as CFrame.Angles), in Blender's axes."""
    C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    m = Matrix.Rotation(math.radians(x), 3, "X") @ Matrix.Rotation(math.radians(y), 3, "Y") @ Matrix.Rotation(math.radians(z), 3, "Z")
    return C @ m @ C.transposed()


def set_pose(pose, root_shift=(0, 0, 0)):
    """pose: {bone: (pitch, yaw, roll)} in the guardian's own axes, each on top of its parent, as the game's joints work.
    root_shift: studs, Roblox axes, on Hips."""
    arm = bpy.data.objects["TiangouRig"]
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    world = {}
    def walk(pb, parent_world):
        rest = pb.bone.matrix_local.to_3x3()
        t = rb_rot(*pose.get(pb.name, (0, 0, 0)))
        w = parent_world @ t
        world[pb.name] = w
        # the bone's channel, in its own axes: rest^-1 * (parent's posed)^-1 ... as the delta from rest
        pb.rotation_quaternion = (rest.inverted() @ t @ rest).to_quaternion()
        for c in pb.children:
            walk(c, w)
    walk(arm.pose.bones["Root"], Matrix.Identity(3))
    hips = arm.pose.bones["Hips"]
    rest = hips.bone.matrix_local.to_3x3()
    C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    hips.location = rest.inverted() @ (C @ V(root_shift))
    bpy.context.view_layer.update()


def _leg(tag, pitch_upper, pitch_lower, pitch_paw=0, meta=None):
    out = {}
    if tag.endswith("Front"):
        side = tag[:-5]
        out[side + "FrontUpper"] = (pitch_upper, 0, 0)
        out[side + "FrontLower"] = (pitch_lower, 0, 0)
        out[side + "FrontPaw"] = (pitch_paw, 0, 0)
    else:
        side = tag[:-4]
        out[side + "BackUpper"] = (pitch_upper, 0, 0)
        out[side + "BackLower"] = (pitch_lower, 0, 0)
        out[side + "BackMeta"] = (meta or 0, 0, 0)
        out[side + "BackPaw"] = (pitch_paw, 0, 0)
    return out


STRESS = {
    "rest": ({}, (0, 0, 0)),
    "gather": ({"Hips": (14, 0, 0), "Spine": (-12, 0, 0), "Chest": (-12, 0, 0), "Neck1": (10, 0, 0), "Tail1": (-20, 0, 0), "Tail2": (-16, 0, 0), "Tail3": (-12, 0, 0),
                **_leg("LeftFront", -52, 62, -25), **_leg("RightFront", -46, 58, -25), **_leg("LeftBack", 58, -55, 25, 25), **_leg("RightBack", 50, -50, 20, 20)}, (0, -2.4, 0)),
    "stretch": ({"Hips": (-10, 0, 0), "Spine": (9, 0, 0), "Chest": (9, 0, 0), "Neck1": (-12, 0, 0), "Tail1": (14, 0, 0), "Tail2": (8, 0, 0),
                 **_leg("LeftFront", 62, 12, 25), **_leg("RightFront", 56, 16, 25), **_leg("LeftBack", -52, 20, -20, -10), **_leg("RightBack", -46, 16, -20, -8)}, (0, 0.6, 0)),
    "howl": ({"Hips": (-12, 0, 0), "Spine": (10, 0, 0), "Chest": (12, 0, 0), "Neck1": (30, 0, 0), "Neck2": (24, 0, 0), "Head": (16, 0, 0), "Jaw": (-40, 0, 0),
              "LeftEar": (-30, 0, 0), "RightEar": (-30, 0, 0), "Tail1": (-18, 0, 0)}, (0, -1.4, 0.6)),
    "turn": ({"Hips": (0, -9, 0), "Spine": (0, 16, 0), "Chest": (0, 18, 0), "Neck1": (0, 22, 0), "Neck2": (0, 22, 0), "Head": (0, 18, 0),
              "Tail1": (0, -24, 0), "Tail2": (0, -28, 0), "Tail3": (0, -30, 0), "Tail4": (0, -24, 0)}, (0, 0, 0)),
    "crouch": ({"Neck1": (-22, 0, 0), "Neck2": (-14, 0, 0), "Head": (10, 0, 0), "LeftEar": (-46, 0, 0), "RightEar": (-46, 0, 0), "Tail1": (-30, 0, 0), "Tail2": (-16, 0, 0),
                **_leg("LeftFront", 28, 42, -26), **_leg("RightFront", 28, 42, -26), **_leg("LeftBack", 44, -66, 28, 12), **_leg("RightBack", 44, -66, 28, 12)}, (0, -4.0, 0)),
}


def stress(path, yaw=-90, pitch=4, size=420, columns=3, distance=66):
    """The skeleton bent to its limits, in clay: creases, collapse and pinching show here, not in a pretty render."""
    scene, cam = _review_scene(size)
    bpy.data.objects["TiangouRig"].hide_render = True
    tmp = path + ".tile.png"
    tiles = []
    for name, (pose, shift) in STRESS.items():
        set_pose(pose, shift)
        tiles.append(_shot(scene, cam, yaw, pitch, distance, W.rb(0, 12.5, 0), size, tmp))
    set_pose({})
    _sheet(tiles, columns, path, size)
    import os
    if os.path.exists(tmp):
        os.remove(tmp)
    return path


# ---------- the gallop ----------
# A sighthound's double-suspension gallop: phases are shares of one stride, per leg, each leg's phase 0 at its touchdown.
# (phase, upper, lower, paw[, meta]) in degrees: + swings a limb's far end forward and up.
GALLOP_FRONT = [(0.0, 30, 6, -28), (0.12, 2, 2, -4), (0.26, -34, 10, 24), (0.42, -44, 56, -18), (0.62, -8, 70, -30), (0.84, 38, 30, -24), (1.0, 30, 6, -28)]
GALLOP_BACK = [(0.0, 34, -20, -6, 14), (0.14, 6, -12, 2, 8), (0.3, -34, 6, 22, -6), (0.46, -42, -28, 8, 20), (0.7, 6, -60, -14, 32), (0.9, 40, -42, -16, 26), (1.0, 34, -20, -6, 14)]
LEAD = {"LeftBack": 0.0, "RightBack": 0.09, "LeftFront": 0.47, "RightFront": 0.56}


def _curve(keys, phase, column):
    """A closed smooth curve through the keys (Catmull-Rom): motion in arcs, no stop at each key."""
    phase %= 1.0
    n = len(keys) - 1
    for i in range(n):
        if phase <= keys[i + 1][0]:
            break
    t0, t1 = keys[i][0], keys[i + 1][0]
    u = (phase - t0) / max(t1 - t0, 1e-6)
    p1, p2 = keys[i][column], keys[i + 1][column]
    p0, p3 = keys[(i - 1) % n][column], keys[(i + 2) % n][column]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u)


def gallop_pose(phase):
    """One moment of the stride. Spine: gathered as the hinds come under, thrown open as the fronts reach."""
    wave = math.cos(2 * math.pi * (phase - 0.02))             # 1: gathered, -1: stretched
    pose = {
        "Hips": (7 * wave, 1.5 * math.sin(2 * math.pi * phase), 0),
        "Spine": (-7 * wave, 0, 0),
        "Chest": (-6 * wave, -1.5 * math.sin(2 * math.pi * phase), 0),
        # the neck reaches forward, low and long, nodding against the spine; the head stays level, eyes on the prey
        "Neck1": (-5 * wave - 30, 0, 0),
        "Neck2": (4 * wave - 14, 0, 0),
        "Head": (6 * wave + 34, 0, 0),
        "Tail1": (-14 - 14 * math.cos(2 * math.pi * (phase - 0.14)), 0, 0),
        "Tail2": (-10 - 14 * math.cos(2 * math.pi * (phase - 0.24)), 0, 0),
        "Tail3": (-8 - 12 * math.cos(2 * math.pi * (phase - 0.34)), 0, 0),
        "Tail4": (-6 - 10 * math.cos(2 * math.pi * (phase - 0.44)), 0, 0),
        "Tail5": (-4 - 8 * math.cos(2 * math.pi * (phase - 0.54)), 0, 0),
        "LeftEar": (46 - 6 * math.cos(2 * math.pi * (phase - 0.2)), 0, 0),
        "RightEar": (46 - 6 * math.cos(2 * math.pi * (phase - 0.2)), 0, 0),
    }
    for leg, lead in LEAD.items():
        p = phase - lead
        if leg.endswith("Front"):
            side = leg[:-5]
            pose[side + "FrontUpper"] = (_curve(GALLOP_FRONT, p, 1), 0, 0)
            pose[side + "FrontLower"] = (_curve(GALLOP_FRONT, p, 2), 0, 0)
            pose[side + "FrontPaw"] = (_curve(GALLOP_FRONT, p, 3), 0, 0)
            pose[side + "FrontBlade"] = (0.28 * _curve(GALLOP_FRONT, p, 1), 0, 0)
        else:
            side = leg[:-4]
            pose[side + "BackUpper"] = (_curve(GALLOP_BACK, p, 1), 0, 0)
            pose[side + "BackLower"] = (_curve(GALLOP_BACK, p, 2), 0, 0)
            pose[side + "BackPaw"] = (_curve(GALLOP_BACK, p, 3), 0, 0)
            pose[side + "BackMeta"] = (_curve(GALLOP_BACK, p, 4), 0, 0)
    return pose


def _lowest_paw():
    arm = bpy.data.objects["TiangouRig"]
    low = 1e9
    for name in ("LeftFrontPaw", "RightFrontPaw", "LeftBackPaw", "RightBackPaw"):
        pb = arm.pose.bones[name]
        low = min(low, (arm.matrix_world @ pb.head).z - 0.55, (arm.matrix_world @ pb.tail).z - 0.45)
    return low


def gallop_heights(frames=48):
    """How high the body rides at each moment, so the lowest paw meets the ground and it flies between: smoothed so the
    body's path is one easy wave, never touching through the floor."""
    heights = []
    for f in range(frames):
        set_pose(gallop_pose(f / frames))
        heights.append(-_lowest_paw())
    # the ride: smoothed, then lifted to keep every paw at or above the ground
    smooth = heights[:]
    for _ in range(6):
        smooth = [(smooth[i - 1] + 2 * smooth[i] + smooth[(i + 1) % frames]) / 4 for i in range(frames)]
    lift = max(h - s for h, s in zip(heights, smooth))
    return [s + lift for s in smooth]


def render_gallop(folder, frames=48, size=540, fps=30, yaw=-90, distance=78):
    """Frames of one stride from the side, on a striped floor running past, to make a video."""
    import os
    scene, cam = _review_scene(size)
    bpy.data.objects["TiangouRig"].hide_render = True
    os.makedirs(folder, exist_ok=True)
    floor = bpy.data.objects.get("TG2Floor")
    if not floor:
        mats = []
        for name, rgb in (("A", (0.46, 0.48, 0.52)), ("B", (0.4, 0.42, 0.46))):
            m = bpy.data.materials.new("TG2Floor" + name)
            m.diffuse_color = (*rgb, 1)
            mats.append(m)
        me = bpy.data.meshes.new("TG2Floor")
        vs, fs, idx = [], [], []
        for k in range(-20, 21):
            y0, y1 = k * 8.0, (k + 1) * 8.0
            b = len(vs)
            vs += [(-60, y0, 0), (60, y0, 0), (60, y1, 0), (-60, y1, 0)]
            fs.append((b, b + 1, b + 2, b + 3))
            idx.append(k % 2)
        me.from_pydata(vs, [], fs)
        for m in mats:
            me.materials.append(m)
        for p, i in zip(me.polygons, idx):
            p.material_index = i
        floor = bpy.data.objects.new("TG2Floor", me)
        scene.collection.objects.link(floor)
    heights = gallop_heights(frames)
    # the world runs past at the speed its stance feet travel: about 44 studs a stride for a hound this size
    stride = 44.0
    for f in range(frames):
        set_pose(gallop_pose(f / frames), (0, heights[f], 0))
        floor.location.y = (-stride * f / frames) % 16.0
        y, p = math.radians(yaw), math.radians(4)
        c = W.rb(0, 12.0, -1.0)
        cam.location = c + V((math.sin(y) * math.cos(p), math.cos(y) * math.cos(p), math.sin(p))) * distance
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(folder, "f%03d.png" % f)
        bpy.ops.render.render(write_still=True)
    set_pose({})
    return {"frames": frames, "ride": [round(min(heights), 2), round(max(heights), 2)]}


# ---------- the finished character ----------
PIECES = {"Skin": 18000, "Jaw": 1800, "Fire": 16000, "Moon": 2200}
OUT = G.OUT_DIR


def _weight_setup(obj, weights, names):
    """Writes weights (verts x bones) as cleaned vertex groups and the armature modifier."""
    import numpy as np
    arm = bpy.data.objects["TiangouRig"]
    keep = weights.copy()
    order = np.argsort(-keep, axis=1)[:, :4]
    trimmed = np.zeros_like(keep)
    rows = np.arange(len(keep))[:, None]
    trimmed[rows, order] = keep[rows, order]
    trimmed[trimmed < 0.02] = 0
    trimmed /= np.maximum(trimmed.sum(axis=1, keepdims=True), 1e-6)
    obj.vertex_groups.clear()
    for j, nm in enumerate(names):
        idx = np.nonzero(trimmed[:, j])[0]
        if len(idx):
            vg = obj.vertex_groups.new(name=nm)
            for i in idx.tolist():
                vg.add([i], float(trimmed[i, j]), "REPLACE")
    for mod in list(obj.modifiers):
        if mod.type == "ARMATURE":
            obj.modifiers.remove(mod)
    md = obj.modifiers.new("Armature", "ARMATURE")
    md.object = arm
    obj.parent = arm


def bind_rigid(obj, bone):
    """A piece that rides one bone whole: the eclipse, the eyes, the jaw."""
    arm = bpy.data.objects["TiangouRig"]
    obj.vertex_groups.clear()
    vg = obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    for mod in list(obj.modifiers):
        if mod.type == "ARMATURE":
            obj.modifiers.remove(mod)
    md = obj.modifiers.new("Armature", "ARMATURE")
    md.object = arm
    obj.parent = arm


def smooth_weights(obj, factor=0.5, repeat=5):
    """Blurs the painted weights along the surface: no vertex jumps from one bone to another, so the skin can't tear."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    bpy.ops.object.vertex_group_smooth(group_select_mode="ALL", factor=factor, repeat=repeat, expand=0.0)
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
    bpy.ops.object.vertex_group_clean(group_select_mode="ALL", limit=0.015, keep_single=True)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def bind_fire(obj, falloff=1.2):
    """White fire rides whatever it grows from, a little softer than the skin."""
    import numpy as np
    n = len(obj.data.vertices)
    co = np.zeros(n * 3)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    pts = np.stack([co[:, 0], co[:, 2], -co[:, 1]], axis=1)
    names, a, b = _bone_segments()
    ab = b - a
    t = np.clip(np.einsum("ijk,jk->ij", pts[:, None, :] - a[None, :, :], ab) / np.maximum((ab * ab).sum(axis=1), 1e-9), 0, 1)
    d = np.linalg.norm(pts[:, None, :] - (a[None] + t[..., None] * ab[None]), axis=2)
    for j, name in enumerate(names):
        if name.startswith("Left"):
            d[pts[:, 0] > 0.3, j] = 1e6
        elif name.startswith("Right"):
            d[pts[:, 0] < -0.3, j] = 1e6
        if name in ("Jaw", "Eyes"):
            d[:, j] = 1e6
    near = d.min(axis=1, keepdims=True)
    w = np.exp(-((d - near) / falloff) ** 2 * 2.2)
    w[d >= 1e5] = 0
    _weight_setup(obj, w, names)


def _keep(obj):
    obj["keep"] = True
    return obj


def build_final(voxel=0.13):
    """The high-detail pieces, ready to bake: {piece: [objects]}, and the glow pieces {name: (object, hex)}."""
    clear()
    coll = bpy.data.collections.new("TiangouV2")
    bpy.context.scene.collection.children.link(coll)
    M = materials()
    groups = _groups()

    # the skin, in the night-sky coat
    skin = G.blob("TG2_SkinHi", coll, M["coat"], _form_lobes(), voxel=voxel, smooth=0.75, rough=0.0, chisel="TiangouV2Fur")
    _settle(skin, groups, cut=_mouth_cut)
    G.soften(skin, 8)
    _settle(skin, groups, passes=2, cut=_mouth_cut)
    for p in skin.data.polygons:
        p.use_smooth = True

    glow, pupils, lids, nose, teeth, cheeks, claws, ruff, plume, feather = (Hm.Hi() for _ in range(10))
    rnd = random.Random(3)
    for side in (-1, 1):
        normal = V((side * 0.72, 0.2, -0.66)).normalized()
        seat = G.surface_along(skin, V((side * 0.75, 22.62, -16.5)), normal)
        G.eye(glow, pupils, lids, seat, normal, (0, -0.1, -1), 0.62, 0.34, tilt=0.22, bulge=0.1, lid=0.4, droop=0.36, lower=0.18, slit=0.26, pupil_height=0.48)
        # a flicker of white fire in each ear
        base = V((side * 1.22, 23.5, -14.75))
        for k in range(2):
            G.wisp(cheeks, base + V((side * 0.14 * k, 0.2, 0)), V((side * 0.15, 1, 0.1)), V((0, 0, -1)), 1.9 - 0.5 * k, 0.15, rnd, sides=5)
        # flames trailing from the cheeks
        for k in range(4):
            G.wisp(cheeks, (side * 1.5, 21.75 - 0.32 * k, -14.9 + 0.4 * k), (side * 0.5, 0.05, 1), (0, 1, 0.3), 2.5 - 0.3 * k, 0.24, rnd)
        cone(teeth, (side * 0.4, _mouth_line(-20.5) + 0.1, -20.5), (side * 0.38, _mouth_line(-20.5) - 0.62, -20.6), 0.13, sides=6)   # the upper fangs
        cone(teeth, (side * 0.46, _mouth_line(-19.5) + 0.1, -19.5), (side * 0.44, _mouth_line(-19.5) - 0.32, -19.55), 0.08, sides=6)
        # claws, silver, past the toes
        for (x, z, reach) in ((3.05, -6.2, 1.35), (3.25, 9.3, 1.3)):
            for dx, length in ((-0.46, 0.62), (-0.16, 0.86), (0.16, 0.86), (0.46, 0.62)):
                tip_z = z - reach * length - 0.28
                cone(claws, (side * x + dx * side, 0.34, tip_z), (side * x + dx * side * 1.12, 0.05, tip_z - 0.42), 0.1, sides=6)
        # white fire feathering the back of the forearm and the hock
        for k in range(3):
            q = 0.18 + 0.2 * k
            front = V((side * 2.97, 8.7, -4.75)).lerp(V((side * 3.03, 2.6, -5.1)), q)
            G.wisp(feather, front + V((0, 0, 0.3)), V((side * 0.15, -0.72, 0.7)), V((0, 0.2, 1)), 3.1 - 0.5 * k, 0.26, rnd, sides=6)
            hock = V((side * 3.2, 7.2, 8.1)).lerp(V((side * 3.25, 5.0, 10.9)), q)
            G.wisp(feather, hock + V((0, 0.1, 0.15)), V((side * 0.15, -0.5, 0.86)), V((0, 0.3, 1)), 3.0 - 0.45 * k, 0.26, rnd, sides=6)
    nose_at = G.surface_along(skin, V((0, 21.32, -20.9)), V((0, 0.15, -1)).normalized())
    sphere(nose, nose_at + V((0, 0.02, 0.12)), 0.3, nu=12, nv=8, radii=(0.34, 0.25, 0.24))

    # the ruff of white fire down the neck
    rnd = random.Random(5)
    axis = (V((0, 21.0, -13.4)) - V((0, 16.2, -7.4))).normalized()
    # the tongues grow from the skin itself and lie back along the neck, overlapping like a mane
    for q, count, length in ((0.0, 22, 4.6), (0.2, 20, 4.2), (0.42, 17, 3.6), (0.64, 13, 3.0), (0.84, 10, 2.3)):
        c = V((0, 16.2, -7.4)).lerp(V((0, 21.0, -13.4)), q)
        n, a1, a2 = frame(axis)
        for k in range(count):
            ang = 2 * math.pi * (k + rnd.uniform(-0.3, 0.3)) / count
            out = a1 * math.cos(ang) + a2 * math.sin(ang)
            root = G.surface_along(skin, c, out, reach=8.0) - out * 0.12
            d = (-axis * rnd.uniform(0.9, 1.1) + out * rnd.uniform(0.42, 0.7) + V((0, -0.12, 0))).normalized()
            up = out + V((rnd.uniform(-0.3, 0.3), 0.2, 0))
            G.wisp(ruff, root, d, up, length * rnd.uniform(0.7, 1.25), 0.3 * rnd.uniform(0.85, 1.2), rnd, sides=6)
    # the plume along the tail, fuller toward the tip
    rnd = random.Random(23)
    pts = [V(BONES["Tail%d" % k][1]) for k in range(1, 6)] + [V(BONES["Tail5"][2])]
    for i in range(2, 11):
        u = i / 10 * 5
        j = min(int(u), 4)
        c = pts[j].lerp(pts[j + 1], u - j)
        d = (pts[j + 1] - pts[j]).normalized()
        flame_ring(plume, c, d, 0.75 - 0.05 * i, 7 + i // 2, 2.3 + 0.17 * i, rnd, lean=0.6, width=0.3)

    def obj(hi, name, mat, smooth=True, keep=True):
        o = hi.object(name, coll, [mat], smooth=smooth)
        if keep:
            o["keep"] = True
        return o

    # the jaw: its own piece, with its teeth and a tongue
    jaw_groups = [(0.5, _limb([(0, 20.9, -15.6), (0, 20.75, -18.0), (0, 20.58, -20.7)], [(0.95, 0.5, 0.9), (0.66, 0.38, 1.0), (0.42, 0.27, 0.45)]))]
    jaw_lobes = [((0, 20.9 - 0.033 * k, -15.6 - 0.51 * k), (0.95 - 0.053 * k, 0.5 - 0.023 * k, 0.8), None) for k in range(11)]
    jaw = G.blob("TG2_JawHi", coll, M["coat"], jaw_lobes, voxel=0.07, smooth=0.75, rough=0.0, chisel="TiangouV2Fur")
    _settle(jaw, jaw_groups, cut=_jaw_cut)
    G.soften(jaw, 4)
    _settle(jaw, jaw_groups, passes=2, cut=_jaw_cut)
    jaw["keep"] = False
    jaw_teeth = Hm.Hi()
    for side in (-1, 1):
        cone(jaw_teeth, (side * 0.32, _mouth_line(-20.2) - 0.12, -20.2), (side * 0.3, _mouth_line(-20.2) + 0.4, -20.3), 0.11, sides=6)
    tongue = Hm.Hi()
    Hm.htube(tongue, [(0, _mouth_line(-16.8) - 0.02, -16.8), (0, _mouth_line(-18.5) - 0.0, -18.5), (0, _mouth_line(-20.0) - 0.05, -20.0)],
             lambda q: 0.34 * (1 - 0.5 * q), sides=8, per=4, uv_scale=1.0, tip=True, wobble=0.0)
    tongue_mat = mat_plain("TiangouTongue", (0.28, 0.05, 0.09), 0.4)

    # the eclipse and its fire
    parts, eclipse_glow = body(coll, M)
    flesh, moon, streams = parts
    me = flesh.data
    bpy.data.objects.remove(flesh, do_unlink=True)
    bpy.data.meshes.remove(me)

    pieces = {
        "Skin": [skin, obj(lids, "TG2_Lids", M["coat"]), obj(nose, "TG2_Nose", M["nose"]), obj(teeth, "TG2_Teeth", M["ivory"]), obj(claws, "TG2_Claws", M["silver"])],
        "Jaw": [jaw, obj(jaw_teeth, "TG2_JawTeeth", M["ivory"]), obj(tongue, "TG2_Tongue", tongue_mat)],
        "Fire": [obj(ruff, "TG2_Ruff", M["flame"]), obj(plume, "TG2_Plume", M["flame"]), obj(feather, "TG2_Feather", M["flame"]), obj(cheeks, "TG2_Cheeks", M["flame"])],
        "Moon": [moon, streams],
    }
    glows = {
        "Eyes": (glow.object("TG2_Eyes", coll, [K.glow_material(EYE)], smooth=True), EYE),
        "Pupils": (pupils.object("TG2_Pupils", coll, [K.glow_material(PUPIL)], smooth=True), PUPIL),
        "Eclipse": (eclipse_glow[DISC][0], DISC),
        "Corona": (eclipse_glow[CORONA][0], CORONA),
    }
    build_skeleton(coll)
    return pieces, glows


def look(path, shots=None, size=520, columns=3, samples=32):
    """Colour renders under moonlit light, to judge the materials before and after the bake."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.resolution_x = scene.render.resolution_y = size
    world = bpy.data.worlds.get("TG2World") or bpy.data.worlds.new("TG2World")
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.5, 0.55, 0.65, 1)
    bg.inputs[1].default_value = 1.0
    scene.world = world
    if not bpy.data.objects.get("TG2Sun"):
        d = bpy.data.lights.new("TG2Sun", "SUN")
        d.energy = 2.5
        o = bpy.data.objects.new("TG2Sun", d)
        o.rotation_euler = (math.radians(50), 0, math.radians(30))
        scene.collection.objects.link(o)
    cam = bpy.data.objects.get("TG2Cam")
    if not cam:
        data = bpy.data.cameras.new("TG2Cam")
        data.lens = 70
        cam = bpy.data.objects.new("TG2Cam", data)
        scene.collection.objects.link(cam)
    scene.camera = cam
    arm = bpy.data.objects.get("TiangouRig")
    if arm:
        arm.hide_render = True
    shots = shots or [(-90, 4, 66, (0, 14.5, 0)), (-35, 12, 66, (0, 14.5, 0)), (150, 10, 66, (0, 14.5, 0)), (-60, 6, 20, (0, 21.5, -17)), (-5, 4, 20, (0, 21.5, -17)), (-75, -14, 14, (0, 21.3, -19))]
    tmp = path + ".tile.png"
    tiles = [_shot(scene, cam, y, p, d, W.rb(*c), size, tmp) for y, p, d, c in shots]
    _sheet(tiles, columns, path, size)
    import os
    if os.path.exists(tmp):
        os.remove(tmp)
    return path


def make_lows(pieces):
    """The game meshes: {piece: object} (not yet baked)."""
    import egg_bake as B
    coll = bpy.data.collections["TiangouV2"]
    lows = {}
    for name, hi in pieces.items():
        low = B.make_low("TiangouV2_" + name, hi, coll, PIECES[name])
        low.name = "TiangouV2_" + name
        lows[name] = low
    return lows


def bake_piece(name, hi, low, size=2048, small=1024, ray=0.3, extrusion=0.12):
    import egg_bake as B
    bpy.context.scene.cycles.device = "GPU"
    saved = B.EGG_DIR
    B.EGG_DIR = OUT
    try:
        B.bake("TiangouV2_" + name, hi, low, size=size, small=small, samples=12, extrusion=extrusion, ray=ray)
    finally:
        B.EGG_DIR = saved


def rig_all(skin_name="TG2_Skin_game"):
    """Skins every game piece to the skeleton, then hides everything that isn't going in the game."""
    O = bpy.data.objects
    out = {}
    out["skin"] = bind(object_name=skin_name)
    smooth_weights(O[skin_name])
    bind_rigid(O["TiangouV2_Jaw"], "Jaw")
    bind_fire(O["TiangouV2_Fire"])
    bind_rigid(O["TiangouV2_Moon"], "Chest")
    for name, bone in (("TG2_Eyes", "Eyes"), ("TG2_Pupils", "Eyes"), ("TG_Disc", "Chest"), ("TG_Corona", "Chest")):
        bind_rigid(O[name], bone)
    game = {skin_name, "TiangouV2_Jaw", "TiangouV2_Fire", "TiangouV2_Moon", "TG2_Eyes", "TG2_Pupils", "TG_Disc", "TG_Corona", "TiangouRig"}
    for o in O:
        if o.type == "MESH" and o.name not in game:
            o.hide_render = True
            o.hide_viewport = True
    return out


def build_all():
    """Everything, ready to export: the pieces, their game meshes, the bakes, the skinning."""
    pieces, glows = build_final()
    lows = make_lows(pieces)
    bake_piece("Skin", pieces["Skin"], lows["Skin"])
    bake_piece("Jaw", pieces["Jaw"], lows["Jaw"], size=512, small=256, ray=0.2, extrusion=0.08)
    bake_piece("Fire", pieces["Fire"], lows["Fire"], size=1024, small=256, ray=0.08, extrusion=0.03)
    bake_piece("Moon", pieces["Moon"], lows["Moon"], size=1024, small=256, ray=0.1, extrusion=0.04)
    lows["Skin"].name = "TG2_Skin_game"
    return {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}, rig_all()


GAME_NAMES = {"TG2_Skin_game": "Skin", "TiangouV2_Jaw": "Jaw", "TiangouV2_Fire": "Fire", "TiangouV2_Moon": "Moon",
              "TG2_Eyes": "Eyes", "TG2_Pupils": "Pupils", "TG_Disc": "Eclipse", "TG_Corona": "Corona"}


def export():
    """assets/guardians/TiangouV2.fbx: every game piece, skinned, and the skeleton. The maps go in with it."""
    import os
    O = bpy.data.objects
    set_pose({})
    arm = O["TiangouRig"]
    arm.hide_render = False
    bpy.ops.object.select_all(action="DESELECT")
    objs = []
    for src, name in GAME_NAMES.items():
        o = O[src]
        o.name = name
        o.hide_viewport = False
        o.select_set(True)
        objs.append(o)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path = os.path.join(OUT, "TiangouV2.fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH", "ARMATURE"}, axis_forward="-Z", axis_up="Y",
                             apply_scale_options="FBX_SCALE_UNITS", path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE",
                             add_leaf_bones=False, use_armature_deform_only=True, bake_anim=False, primary_bone_axis="Y", secondary_bone_axis="X")
    return path, os.path.getsize(path) // 1024


def stats():
    skin = bpy.data.objects["TG2_Skin"]
    lo = V((1e9, 1e9, 1e9))
    hi = -lo
    for v in skin.data.vertices:
        p = V(K.rb_inv(*(skin.matrix_world @ v.co)))
        lo, hi = V(map(min, lo, p)), V(map(max, hi, p))
    return {"tris": sum(len(p.vertices) - 2 for p in skin.data.polygons), "min": [round(x, 2) for x in lo], "max": [round(x, 2) for x in hi], "bones": len(BONES)}


# ---------- review ----------
VIEWS = {"left": (-90, 4), "right": (90, 4), "front": (0, 6), "back": (180, 6), "three": (-38, 14), "top": (-20, 58), "low": (-140, -8)}


def _review_scene(size):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "MATERIAL"
    shading.show_shadows = True
    shading.shadow_intensity = 0.35
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.show_specular_highlight = True
    shading.background_type = "VIEWPORT"
    shading.background_color = (0.62, 0.66, 0.72)
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.film_transparent = False
    cam = bpy.data.objects.get("TG2Cam")
    if not cam:
        data = bpy.data.cameras.new("TG2Cam")
        data.lens = 70
        cam = bpy.data.objects.new("TG2Cam", data)
        scene.collection.objects.link(cam)
    scene.camera = cam
    return scene, cam


def _sheet(tiles, columns, path, size):
    import numpy as np
    rows = [np.concatenate(tiles[i:i + columns] + [np.zeros_like(tiles[0])] * (columns - len(tiles[i:i + columns])), axis=1) for i in range(0, len(tiles), columns)]
    sheet = np.concatenate(rows[::-1], axis=0)
    h, w = sheet.shape[:2]
    out = bpy.data.images.new("TG2Sheet", w, h)
    out.pixels.foreach_set(sheet.ravel())
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out)


def _shot(scene, cam, yaw_deg, pitch_deg, distance, centre, size, tmp):
    import numpy as np
    y, p = math.radians(yaw_deg), math.radians(pitch_deg)
    c = V(centre)
    # yaw 0: in front of its face (Roblox -Z is Blender +Y)
    cam.location = c + V((math.sin(y) * math.cos(p), math.cos(y) * math.cos(p), math.sin(p))) * distance
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    scene.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(tmp, check_existing=False)
    px = np.zeros(size * size * 4, dtype=np.float32)
    im.pixels.foreach_get(px)
    bpy.data.images.remove(im)
    return px.reshape(size, size, 4)


def review_form(path, views=("left", "right", "front", "back", "three", "top"), size=420, columns=3, distance=62, centre=(0, 13.5, 0)):
    scene, cam = _review_scene(size)
    arm = bpy.data.objects.get("TiangouRig")
    if arm:
        arm.hide_render = True
    tmp = path + ".tile.png"
    tiles = [_shot(scene, cam, *VIEWS[v], distance, W.rb(*centre), size, tmp) for v in views]
    _sheet(tiles, columns, path, size)
    import os
    if os.path.exists(tmp):
        os.remove(tmp)
    return path
