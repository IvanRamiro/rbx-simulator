"""The Ember Wyrm (Uncommon, Fire; Beginner Qi Egg and Inferno Egg): "A little salamander born in the coals of an old campfire, held together by one
stubborn, molten heart. It sleeps in the warm ash of old campfires."

Recreated (November 9, 2026; the old model was a chain of floating lava beads): a campfire salamander (the owner's choice), in a design language of its
own: a campfire that went for a walk. A chubby baby wyrm built like a fire salamander, low and round: a big flat round head with a wide, contented smile
and big sleepy ember eyes set high on it; a soft, fat body on four stubby legs splayed out to the sides, round pads on its little fingers; a thick tail
tapering to a tip that burns like a small campfire. Its skin is charcoal crust, cracked all over with glowing seams of magma, warm ember-orange beneath;
down its back a crest of little flames flickers; its cheeks glow like coals.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/ember_wyrm.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre, its pads on the ground (z = 0). +X is its left. The maps go to assets/pets/BeginnerQiEgg/.

What touches what: head, body, legs, fingers and tail are one fused skin; the eyes sit in their sockets under their lids; the flames of its crest
(glow pieces) root in the ridge of its back, its campfire (glow pieces) in the tip of its tail.
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
PET = "EmberWyrm"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "BeginnerQiEgg")

# ---------- colours: charcoal, coal-glow and flame ----------
CHAR, CHAR_LIGHT, ASH = rgb(34, 28, 30), rgb(70, 58, 56), rgb(120, 108, 104)
EMBER, EMBER_DEEP, EMBER_HOT, MAGMA = rgb(255, 128, 40), rgb(196, 62, 22), rgb(255, 196, 90), rgb(255, 92, 20)
MOUTH = rgb(70, 20, 14)
LASH = rgb(16, 10, 10)
GLINT_HEX = "fff4e0"
FLAME_HEX, CORE_HEX = "ff7a1e", "ffd04a"

# ---------- the frame of it ----------
# low and chubby, its belly near the ground (higher on longer legs it read as a lanky lizard)
SPINE = [V(0, 0.22, 0.125), V(0, 0.11, 0.138), V(0, 0.0, 0.142), V(0, -0.09, 0.14), V(0, -0.17, 0.148)]
BODY_PATH = catmull(SPINE, 10)
BODY_W = ((0, 0.095), (0.3, 0.135), (0.6, 0.142), (0.85, 0.13), (1, 0.11))      # half-widths, hips to shoulders: wide and soft
BODY_H = ((0, 0.07), (0.3, 0.088), (0.6, 0.095), (0.85, 0.09), (1, 0.08))      # half-heights: a low, round body
HEAD = V(0, -0.29, 0.162)
HEAD_R = (0.135, 0.125, 0.086)                                                       # big, flat and round
EYE_R = 0.034
EYE_C = V(0.076, -0.322, 0.222)
EYE_AXIS = V(0.55, -0.62, 0.56).normalized()        # set high on its head, looking up and out as a salamander's do
LID_UP, LID_LOW = (22.0, 118.0, 0.0026), (-50.0, -126.0, 0.0022)      # sleepy: its upper lid low over its eye
LID_TILT = -4.0
BLINK_U, BLINK_L = 70.0, 24.0
IRIS, PUPIL = 0.9, 0.36
TAIL = catmull([V(0, 0.2, 0.13), V(0, 0.32, 0.116), V(0, 0.44, 0.096), V(0.03, 0.54, 0.086), V(0.056, 0.62, 0.092), V(0.05, 0.68, 0.116)], 10)
TAIL_R = ((0, 0.09), (0.3, 0.075), (0.6, 0.056), (0.85, 0.043), (1, 0.037))      # thick and short: a baby's
# legs (left): shoulder or hip, elbow or knee, wrist or ankle, the palm; splayed out to the sides
FRONT = [V(0.085, -0.09, 0.118), V(0.165, -0.1, 0.098), V(0.188, -0.122, 0.04), V(0.198, -0.14, 0.018)]
HIND = [V(0.085, 0.14, 0.115), V(0.17, 0.155, 0.096), V(0.192, 0.18, 0.04), V(0.202, 0.2, 0.018)]
LEG_R = [0.06, 0.05, 0.04, 0.032]                    # stubby
LEGS = (("FL", 1, FRONT, 4), ("FR", -1, FRONT, 4), ("BL", 1, HIND, 5), ("BR", -1, HIND, 5))
# the crest of little flames down its back (fractions along BODY_PATH from the hips, then down the tail), and its campfire
CREST = [(0.95, 0.085), (0.8, 0.115), (0.64, 0.12), (0.48, 0.11), (0.32, 0.095), (0.16, 0.08), (0.02, 0.068)]
TAIL_CREST = [(0.2, 0.058), (0.38, 0.05), (0.55, 0.042)]
CAMPFIRE = TAIL[-1]


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def path_tan(path, f, reach=0.03):
    return (path_at(path, min(1.0, f + reach)) - path_at(path, max(0.0, f - reach))).normalized()


def leg_path(knots, side, per=8):
    return catmull([mir(p, side) for p in knots], per)


def leg_radius(f):
    return float(np.interp(f, np.linspace(0, 1, len(LEG_R)), LEG_R))


def path_frames(path):
    out = []
    for i in range(len(path)):
        tan = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = V(1, 0, 0) - tan * tan.x
        side = side.normalized() if side.length > 1e-5 else V(1, 0, 0)
        out.append((tan, side, tan.cross(side).normalized()))
    return out


def loft(m, path, w_fn, h_fn, drop_fn=None, nt=48):
    fr = path_frames(path)
    rings = []
    for i, p in enumerate(path):
        f = i / (len(path) - 1)
        tan, side, up = fr[i]
        w, h = w_fn(f), h_fn(f)
        c = p - V(0, 0, drop_fn(f) if drop_fn else 0.0)
        rings.append([m.bm.verts.new(c + side * (w * math.cos(TAU * k / nt)) + up * (h * math.sin(TAU * k / nt))) for k in range(nt)])
    for i in range(len(rings) - 1):
        for k in range(nt):
            k2 = (k + 1) % nt
            m.bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    m.bm.faces.new(rings[0])
    m.bm.faces.new(list(reversed(rings[-1])))


def fingers(knots, side, count):
    """Its little fingers, splayed in a fan forward and out from the palm, each ending in a round pad."""
    palm = mir(knots[3], side)
    out = []
    spread = math.radians(110 if count == 5 else 95)
    base = math.radians(-20)
    for k in range(count):
        a = base + spread * (k / (count - 1) - 0.5)
        d = V(side * math.sin(a + math.radians(35)), -math.cos(a + math.radians(35)), 0).normalized()
        length = 0.045 + 0.012 * math.sin(math.pi * k / (count - 1))
        tip = palm + d * length + V(0, 0, -0.008)
        out.append((palm + d * 0.012, tip))
    return out


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    loft(core, BODY_PATH, lambda f: prof(BODY_W, f), lambda f: prof(BODY_H, f), lambda f: 0.01 * math.sin(math.pi * f))
    core.tube(TAIL, lambda f: prof(TAIL_R, f), sides=36, flat=1.15)
    core.ball(TAIL[-1], (0.032, 0.03, 0.028), 20, 12)
    core.ball(V(0, -0.19, 0.15), (0.112, 0.09, 0.08))                    # the neck, hardly there: the head sits on the shoulders
    for side in (1, -1):
        core.ball(V(side * 0.085, -0.09, 0.12), (0.065, 0.07, 0.065))     # the shoulder
        core.ball(V(side * 0.085, 0.14, 0.118), (0.07, 0.08, 0.068))     # the haunch
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.005, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 10})])
    fine = Mesh()
    fine.ball(HEAD, HEAD_R, 44, 30)                                       # the big round head, one smooth shape to its blunt snout (a ball for a snout read as a frog's)
    fine.ball(HEAD + V(0, 0.01, -0.03), (0.122, 0.105, 0.05))             # a full chin
    for side in (1, -1):
        fine.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.006, (EYE_R * 1.1,) * 3, 28, 18)     # the socket, a bump on top of its head
        fine.ball(mir(EYE_C, side) + V(0, 0.004, 0.012), (0.036, 0.034, 0.02))                   # the brow over it: the lids' hidden edges stay under it (higher, it came down over the eye; where skin and lid lie flush, part_flush parts them)
        fine.ball(V(side * 0.095, -0.315, 0.138), (0.045, 0.05, 0.04))                           # the round cheek
    for key, side, knots, count in LEGS:
        fine.tube(leg_path(knots, side), leg_radius, sides=24, flat=0.95)
        fine.ball(mir(knots[1], side), (0.046, 0.046, 0.044), 20, 12)                            # the elbow or knee
        fine.ball(mir(knots[3], side) + V(0, 0, 0.002), (0.034, 0.036, 0.018), 20, 12)            # the palm
        for a, b in fingers(knots, side, count):
            fine.tube([a, b], lambda f: 0.011 - 0.002 * f, sides=14)
            fine.ball(b, (0.0125, 0.0125, 0.0105), 14, 8)                                         # the round pad on its fingertip
    th = fine.finish(N + "FineHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0028, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    P = verts(c)
    P[:, 2] = np.maximum(P[:, 2], 0.0)                                    # its pads flat on the ground
    set_verts(c, P)
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


# ---------- flames ----------
def flame_path(base, height, lean, phase=0.0, sway=0.12):
    """A tongue of flame rising from base, leaning back, waving like a real one in an S."""
    pts = []
    for j in range(9):
        t = j / 8
        w = math.sin(math.pi * (1.6 * t + phase)) * sway * height * t
        pts.append(base + V(0, lean * height * t * t, height * t) + V(0, w, 0) + V(w * 0.3, 0, 0))
    return pts


def flame_tube(m, base, height, width, lean, phase, core=False, sides=16, per=4):
    path = catmull(flame_path(base, height, lean, phase), per)

    def r(f):
        return width * (math.sin(math.pi * min(1.0, 0.08 + f * 0.92)) ** 0.55) * (1 - f) ** 0.45 * (0.42 if core else 1.0) + (0.0006 if core else 0.0016)
    m.tube(path, r, sides=sides, flat=0.62)


def crest_roots(tree):
    """Where each flame of its crest roots on the ridge of its back and tail."""
    out = []
    for f, h in CREST:
        c = path_at(BODY_PATH, f)
        hit = tree.ray_cast(c + V(0, 0, 0.3), V(0, 0, -1), 0.6)
        out.append((hit[0] - V(0, 0, 0.006), h, "body", f))
    for f, h in TAIL_CREST:
        c = path_at(TAIL, f)
        hit = tree.ray_cast(c + V(0, 0, 0.3), V(0, 0, -1), 0.6)
        out.append((hit[0] - V(0, 0, 0.006), h, "tail", f))
    return out


def build_flames(roots, name_outer, name_core, coll, low=False):
    """The crest and the campfire: an orange outer flame round a yellow core, each its own glow piece. Returns both and, per vertex, which flame."""
    outer, inner = Mesh(), Mesh()
    which_o, which_i = [], []
    sides, per = (6, 1) if low else (16, 4)
    for k, (base, h, part, f) in enumerate(roots):
        before = len(outer.bm.verts)
        flame_tube(outer, base, h, h * 0.32, 0.45, k * 0.37, sides=sides, per=per)
        which_o += [k] * (len(outer.bm.verts) - before)
        before = len(inner.bm.verts)
        flame_tube(inner, base - V(0, 0, 0.004), h * 0.62, h * 0.32, 0.45, k * 0.37, core=True, sides=sides, per=per)     # rooted deeper, and following its flame's lean and wave (level with its root, or waving its own way, it poked out flush and z-fought)
        which_i += [k] * (len(inner.bm.verts) - before)
    # its campfire: five tongues round the tip of its tail, the middle one tallest, leaning up and back
    k0 = len(roots)
    tan = (TAIL[-1] - TAIL[-4]).normalized()
    for j, (a, h, w) in enumerate(((0, 0.21, 0.058), (72, 0.17, 0.046), (144, 0.15, 0.042), (216, 0.16, 0.044), (288, 0.18, 0.048))):
        off = V(math.cos(math.radians(a)), math.sin(math.radians(a)), 0) * (0.0 if j == 0 else 0.026)     # spread round it (close in, one tongue hid the rest)
        base = CAMPFIRE + off + V(0, 0, 0.01) + tan * 0.01
        before = len(outer.bm.verts)
        flame_tube(outer, base, h, w, 0.25, 0.2 * j, sides=sides, per=per)
        which_o += [k0] * (len(outer.bm.verts) - before)
        before = len(inner.bm.verts)
        flame_tube(inner, base - V(0, 0, 0.004), h * 0.6, w * 0.85, 0.25, 0.2 * j, core=True, sides=sides, per=per)
        which_i += [k0] * (len(inner.bm.verts) - before)
    return outer.finish(name_outer, coll), inner.finish(name_core, coll), np.array(which_o), np.array(which_i)


# ---------- paint ----------
def cells(P, f, seed=0):
    """Distance to the nearest and second-nearest cell point, and the nearest cell's own random number and centre."""
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    d2 = np.full(len(P), 1e9)
    own = np.zeros(len(P))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                d = np.sqrt((q[:, 0] - c[:, 0] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 1)) ** 2 + (q[:, 1] - c[:, 1] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 2)) ** 2
                            + (q[:, 2] - c[:, 2] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + 3)) ** 2)
                nearer = d < d1
                d2 = np.where(nearer, d1, np.minimum(d2, d))
                own = np.where(nearer, hash01(c[:, 0], c[:, 1], c[:, 2], seed + 4), own)
                d1 = np.where(nearer, d, d1)
    return d1, d2, own


def paint_skin(o):
    """Charcoal crust, ashy where it faces up, cracked with fine glowing seams; rows of ember spots down its flanks as a fire salamander's; a warm
    ember belly; coal-glow cheeks, glowing pads, its tail heating toward its campfire."""
    Pv = verts(o)
    Nn = normals(o)
    x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
    head = 1 - smooth(0.13, 0.17, np.linalg.norm((Pv - np.array(tuple(HEAD))) / np.array((1.0, 1.1, 1.3)), axis=1))
    crust = fbm(Pv, 60.0, 4, 3)
    col = mix(np.broadcast_to(CHAR, (len(Pv), 3)), CHAR_LIGHT, smooth(0.45, 0.75, crust) * 0.7)
    col = mix(col, ASH, smooth(0.4, 1.0, Nn[:, 2]) * smooth(0.55, 0.8, crust) * 0.45)
    # the fine glowing cracks, where its crust has split over the fire inside it
    warp = np.stack([fbm(Pv, 14.0, 2, 31), fbm(Pv, 14.0, 2, 32), fbm(Pv, 14.0, 2, 33)], axis=1) - 0.5
    d1, d2, _ = cells(Pv + warp * 0.03, 26.0, 7)
    crack = (1 - smooth(0.015, 0.065, d2 - d1)) * (0.55 + 0.45 * smooth(0.2, -0.6, Nn[:, 2]))      # (thinner than the mesh can hold, they broke into dashes)
    # the ember spots: round, in rows down its back and flanks and over its head (none on the belly)
    e1, e2, own = cells(Pv * np.array([1.0, 0.75, 1.0]), 16.0, 11)
    spot = (1 - smooth(0.2, 0.3, e1 + 0.08 * (own - 0.5))) * (own > 0.35) * smooth(-0.05, 0.3, Nn[:, 2])     # (one on its chin read as a fang)
    # the belly: warm ember, banded softly
    under = smooth(-0.15, -0.65, Nn[:, 2]) * (1 - head * 0.3)
    bands = smooth(0.75, 0.95, 0.5 + 0.5 * np.cos(TAU * y * 30))
    belly = mix(np.broadcast_to(EMBER_DEEP, (len(Pv), 3)), EMBER, smooth(0.3, 0.9, under))
    belly = mix(belly, EMBER_HOT, bands * 0.25 * (1 - head))      # (a band crossing the curve of its chin read as a fang)
    col = mix(col, belly, under)
    col = mix(col, mix(EMBER, EMBER_HOT, smooth(0.0, 0.15, -(e1 - 0.2))), spot * (1 - under) * 0.95)
    crack = crack * (1 - under * head)                      # none under its chin (one there read as a fang under its smile)
    col = mix(col, mix(MAGMA, EMBER_HOT, smooth(0.6, 1.0, crack)), crack * (1 - spot) * 0.85)
    # cheeks glowing like coals; pads on its fingers; its tail heating toward the fire at its tip
    cheeks = np.zeros(len(Pv))
    for side in (1, -1):
        c = np.array(tuple(V(side * 0.112, -0.335, 0.13)))
        cheeks = np.maximum(cheeks, 1 - smooth(0.012, 0.03, np.linalg.norm(Pv - c, axis=1)))
    col = mix(col, mix(EMBER, EMBER_HOT, cheeks), cheeks * 0.9)
    pads = (z < 0.016).astype(float) * smooth(0.0, 0.012, 0.016 - z)
    col = mix(col, EMBER, pads * 0.8)
    tf, td = nearest_on(TAIL, Pv)
    heat = smooth(0.7, 1.0, tf) * (1 - smooth(0.05, 0.07, td))
    col = mix(col, mix(EMBER_DEEP, EMBER_HOT, smooth(0.85, 1.0, tf)), heat * 0.9)
    # its wide, contented smile
    lx, ly, lz = x, y - HEAD.y, z - HEAD.z
    smile_z = -0.022 + 0.6 * lx ** 2
    mouth = (1 - smooth(0.0012, 0.003, np.abs(lz - smile_z))) * (np.abs(lx) < 0.11) * (ly < -0.04) * smooth(-0.2, 0.3, -Nn[:, 1])
    col = mix(col, MOUTH, mouth * 0.9)
    nost = np.zeros(len(Pv))
    for side in (1, -1):
        c = np.array(tuple(HEAD + V(side * 0.022, -0.118, 0.022)))
        nost = np.maximum(nost, 1 - smooth(0.0035, 0.006, np.linalg.norm(Pv - c, axis=1)))
    col = mix(col, MAGMA * 0.6, nost)
    relief = (crust - 0.5) * 0.0018 - crack * 0.0012 - mouth * 0.0012 + spot * 0.0004
    set_verts(o, Pv + Nn * relief[:, None])
    glow = np.clip(crack * (1 - spot) + spot + cheeks + heat * 0.5, 0, 1)
    paint(o, np.clip(col, 0, 1), 0.82 - 0.35 * glow - 0.2 * under, np.zeros(len(Pv)))


def eye_paint(o, fr):
    """An ember eye: gold at its heart going to deep orange at its rim, flecked like a coal, a round dark pupil."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(30, 12, 6), (len(px), 3)).copy()
    iris = mix(rgb(255, 210, 90), rgb(220, 90, 20), smooth(0.4, 0.88, r / IRIS))
    azi = np.arctan2(py, px)
    iris = iris * (0.86 + 0.14 * np.sin(azi * 24 + np.sin(azi * 5) * 1.5))[:, None]
    iris = mix(iris, iris * 0.6, smooth(-0.2, 0.8, py / IRIS) * 0.45)
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS, r))
    col = mix(col, rgb(60, 18, 6), smooth(IRIS - 0.1, IRIS - 0.02, r) * (1 - smooth(IRIS - 0.02, IRIS, r)))
    col = mix(col, rgb(14, 6, 4), 1 - smooth(PUPIL - 0.02, PUPIL + 0.02, r))
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
    tree = tree_of(skin)
    data["tree"] = tree
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, CHAR_LIGHT, LASH)       # (in the dark crust's own black, closed they read as goggles)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, CHAR_LIGHT, LASH, lower_share=0.7)
    data["crest"] = crest_roots(tree)
    flames, cores, data["which_o"], data["which_i"] = build_flames(data["crest"], N + "Flames_Glow_" + FLAME_HEX, N + "Cores_Glow_" + CORE_HEX, HI)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0075, 12), (20, -18, 0.0034, 8))), "Flames": flames, "Cores": cores}
    if not clay:
        paint_skin(skin)
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    return pieces, frames, glows, data


VIEWS = [(0, -1, 0.3), (0.62, -0.72, 0.4), (1, 0, 0.15), (0, 1, 0.35), (-0.6, 0.6, 0.5), (-0.62, -0.72, 0.35), (0, -0.05, 1), (0.5, -0.4, -0.5)]
VIEW_AT = (0, 0.15, 0.12)
FACE_AT = (0, -0.33, 0.16)
EXTRA = [(0, -1, 0.15, 0.75, FACE_AT), (0.75, -0.6, 0.3, 0.75, FACE_AT), (1, -0.1, 0.1, 0.8, FACE_AT), (0.5, -0.6, 0.6, 0.32, tuple(EYE_C)),
         (0.8, 0.5, 0.4, 0.8, (0.05, 0.6, 0.15)), (1, -0.4, 0.2, 0.6, (0.19, -0.12, 0.04))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, "glow", {k: len(o.data.polygons) for k, o in glows.items()}, flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
        dark = bpy.data.materials.new("clay_eye")
        g = next(n for n in dark.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.12, 0.05, 0.02, 1)
        g.inputs["Roughness"].default_value = 0.15
    else:
        mat = hi_material(ao_distance=0.02, ao_share=0.35)
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(dark if STAGE == "clay" and key.startswith("Eye") else mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=2.4, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 3500                  # (at 3600 a sliver in the haunch crease folded one texel over its neighbour in the unwrap)
SCALES = {"EyeL": 2.4, "EyeR": 2.4, "LidUL": 1.4, "LidUR": 1.4, "LidLL": 1.4, "LidLR": 1.4}


def build_low(pieces, frames):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS)}
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 24, 16)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
TRUNK = BODY_PATH + [V(0, -0.22, 0.152), HEAD + V(0, 0.04, 0)]
TRUNK_HEADS = (("Hips", SPINE[1], "Root"), ("Body", SPINE[2], "Hips"), ("Chest", SPINE[3], "Body"), ("Neck", SPINE[4], "Chest"), ("Head", V(0, -0.22, 0.152), "Neck"))
TAIL_F = (0.0, 0.3, 0.6, 0.85)
TAIL_NAMES = ["Tail1", "Tail2", "Tail3", "Tail4"]
LEG_NAMES = {key: ["Leg%s1" % key, "Leg%s2" % key, "Hand" + key] for key, _, _, _ in LEGS}


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None)]
    for name, at, parent in TRUNK_HEADS:
        bones.append((name, at.copy(), parent))
    parent = "Hips"
    for name, f in zip(TAIL_NAMES, TAIL_F):
        bones.append((name, path_at(TAIL, f), parent))
        parent = name
    bones.append(("Campfire", CAMPFIRE.copy(), "Tail4"))
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head")]
    for key, side, knots, _ in LEGS:
        parent = "Chest" if key[0] == "F" else "Hips"
        for k, name in enumerate(LEG_NAMES[key]):
            bones.append((name, mir(knots[k], side), parent))
            parent = name
    return armature(bones)


def trunk_knots():
    pts = np.array([tuple(at) for _, at, _ in TRUNK_HEADS])
    f, _ = nearest_on(TRUNK, pts)
    mids = [(f[k] + f[k + 1]) / 2 for k in range(len(f) - 1)]
    return [n for n, _, _ in TRUNK_HEADS], tuple(mids) + (f[-1] + 0.03,)


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


HEAD_ZONE = (HEAD + V(0, -0.02, 0.0), (0.15, 0.13, 0.12))


def body_weights(P_):
    names, knots = trunk_knots()
    f_tr, _ = nearest_on(TRUNK, P_)
    hz = np.linalg.norm((P_ - np.array(tuple(HEAD_ZONE[0]))) / np.array(HEAD_ZONE[1]), axis=1)
    tf, td = nearest_on(TAIL, P_)
    legs = []
    for key, side, knots_l, count in LEGS:
        line = leg_path(knots_l, side)
        f, d = nearest_on(line, P_)
        legs.append((key, side, knots_l, f, d))
    out = []
    tail_mids = tuple((TAIL_F[k] + TAIL_F[k + 1]) / 2 for k in range(3)) + (1.1,)
    for i in range(len(P_)):
        x, y, z = P_[i]
        hand = None
        for key, side, knots_l, f, d in legs:
            if (Vector(P_[i]) - mir(knots_l[3], side)).length < 0.075 and z < 0.045:
                hand = "Hand" + key
        if hand:
            out.append({hand: 1.0})
            continue
        w = chain_weight(names, knots, float(f_tr[i]))
        if hz[i] < 1.15:
            w = blend(w, {"Head": 1.0}, float(smooth(1.15, 0.85, hz[i])))
        share = (1 - float(smooth(0.03, 0.05, td[i] - prof(TAIL_R, float(tf[i]))))) * float(smooth(0.0, 0.12, tf[i]))
        if share > 0:
            w = blend(w, chain_weight(TAIL_NAMES, tail_mids, float(tf[i])), share)
        for key, side, knots_l, f, d in legs:
            if x * side <= 0.02:
                continue
            lr = leg_radius(float(f[i])) + 0.012
            mm = float(smooth(0.06, 0.25, f[i])) * (1 - float(smooth(lr * 0.9, lr * 1.6, d[i])))
            if mm > 0:
                w = blend(w, chain_weight(LEG_NAMES[key], (0.33, 0.66, 1.2), float(f[i])), mm)
        out.append(w)
    return out


def flame_weights(o, which, roots):
    """Each crest flame with the spine (or tail) where it grows; the campfire on its own bone."""
    names, knots = trunk_knots()
    tail_mids = tuple((TAIL_F[k] + TAIL_F[k + 1]) / 2 for k in range(3)) + (1.1,)
    out = []
    per = []
    for base, h, part, f in roots:
        if part == "body":
            ft, _ = nearest_on(TRUNK, np.array([tuple(base)]))
            per.append(chain_weight(names, knots, float(ft[0])))
        else:
            per.append(chain_weight(TAIL_NAMES, tail_mids, f))
    for k in which:
        out.append({"Campfire": 1.0} if k >= len(roots) else per[int(k)])
    return out


def bind_all(lows, rig, glows, data):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    for tag in ("L", "R"):
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    weigh(glows["Flames"], flame_weights(glows["Flames"], data["low_which_o"], data["crest"]))
    weigh(glows["Cores"], flame_weights(glows["Cores"], data["low_which_i"], data["crest"]))
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
            # a sample point of src lying within gap of dst, parallel, over dst's face: the skin face goes to gap off the eye or lid face, on its side
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


# poses in the game's axes (turns x, y, z: +x lifts what points forward; +y turns to its left); the same numbers as PetRig's EW tables
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def legs4(f, b, splay=0.0):
    out = {}
    for side in "LR":
        s = 1 if side == "L" else -1
        for k in range(2):
            out["LegF%s%d" % (side, k + 1)] = (f[k], 0, s * splay * (1 - k))
            out["LegB%s%d" % (side, k + 1)] = (b[k], 0, s * splay * (1 - k))
    return out


# its stances, searched in Blender against the ground and for torn skin
NAP = {"Hips": (0, 0, 0, (0, -0.03, 0)), "Head": (0.12, 0.35, 0.1), "Neck": (0.0, 0.2, 0), "Tail1": (0, -0.35, 0), "Tail2": (0, -0.45, 0), "Tail3": (0, -0.5, 0),
       "Tail4": (0, -0.4, 0), **legs4((0.0, 0.0), (0.0, 0.0), -0.25)}      # legs splayed out flat, hands lifting off (turned the other way they sank)
STOKE = {"Tail1": (-0.3, 0, 0), "Tail2": (-0.4, 0, 0), "Tail3": (-0.4, 0, 0), "Tail4": (-0.3, 0, 0)}     # its tail swung up over its back (Bonfire)
PROUD = {"Body": (0.25, 0, 0), "Chest": (0.15, 0, 0), "Neck": (-0.05, 0, 0), "Head": (-0.2, 0, 0), "Tail1": (-0.15, 0, 0), **legs4((-0.35, 0.3), (0.0, 0.0))}


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    # its sprawling walk (measured in Blender: yaw swings a leg forward or back without changing its height, forward is -yaw on the left and +yaw on
    # the right; the sideways turn lifts the hand, -z on the left and +z on the right): the body bending side to side, a front leg and the hind leg
    # across from it reaching forward and lifted together, the other pair swung back
    walk = {"Hips": (0, -0.2, 0), "Chest": (0, 0.3, 0), "Head": (0, -0.2, 0), "Tail1": (0, -0.25, 0), "Tail2": (0, -0.2, 0),
            "LegFL1": (0, -0.45, -0.3), "LegBR1": (0, 0.45, 0.3), "LegFR1": (0, -0.35, 0), "LegBL1": (0, 0.35, 0)}
    return {"Blink": lids(BLINK_U, BLINK_L), "Wide": lids(-12, -6), "Walk": spec(walk), "Nap": spec(NAP), "Proud": spec(PROUD), "Stoke": spec({**PROUD, **STOKE}),
            "Look": spec({"Neck": (0.1, 0.35, 0), "Head": (0.2, 0.4, 0.15)}), "Wag": spec({"Tail1": (0.1, 0.4, 0), "Tail2": (0.1, 0.45, 0), "Tail3": (0, 0.5, 0), "Tail4": (0, 0.4, 0)}),
            "Fire": spec({"Campfire": (0.3, 0.3, 0.2)})}


def lowest_of(body, parts):
    groups = {g.name: g.index for g in body.vertex_groups}
    dg = bpy.context.evaluated_depsgraph_get()
    me = body.evaluated_get(dg).to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    body.evaluated_get(dg).to_mesh_clear()
    out = {}
    for name, bones in parts.items():
        idx = {groups[b] for b in bones if b in groups}
        mine = [v.index for v in body.data.vertices if any(g.group in idx and g.weight > 0.5 for g in v.groups)]
        out[name] = round(float(co[mine, 2].min()), 4) if mine else None
    return out


GROUND_PARTS = {"Hands": ("HandFL", "HandFR", "HandBL", "HandBR"), "Belly": ("Body", "Chest", "Hips"), "Head": ("Head",), "Tail": ("Tail2", "Tail3", "Tail4")}

if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.02, ao_share=0.35)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames)
    # its head given more of the atlas; its legs projected apart (with the body, the crease where a thigh meets the haunch folded one face over another)
    unwrap(lows, [(lambda p: p.center.y < -0.2, 1.8), (lambda p: abs(p.center.x) > 0.115 and p.center.z < 0.13, 1.0), (None, 1.0)], SCALES, margin=0.011, angle=42)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.14, 0.11, 0.11, 1), far=("Skin",), reach=(0.004, 0.01), far_reach=(0.008, 0.02))
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for o in glows.values():
        bpy.data.objects.remove(o, do_unlink=True)          # first, so the game's pieces take their exact names
    flames, cores, data["low_which_o"], data["low_which_i"] = build_flames(data["crest"], N + "Flames_Glow_" + FLAME_HEX, N + "Cores_Glow_" + CORE_HEX, GAME, low=True)
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 22, 0.0075, 10), (20, -18, 0.0034, 6))), "Flames": flames, "Cores": cores}
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames)
    body = bind_all(lows, rig, glows, data)
    print("SKIN MOVED OFF EYES AND LIDS", part_flush(body), "verts", flush=True)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for o in [body] + list(glows.values()) for v in o.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(o.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    # (the game's box counts the RootPart, a 0.05 m cube at the origin: its bottom is 0.025 m under the feet, measured in Play on the Volt Fox)
    bottom = min(lo, -0.025)
    print("Z range", round(lo, 4), round(hi, 4), "SOLE from the box middle (the RootPart counted) down to the ground", round((hi + bottom) / 2 - lo, 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name in ("Head", "Campfire", "Hips"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    gc = sum((Vector(v.co) for v in glows["Glints"].data.vertices), Vector()) / len(glows["Glints"].data.vertices)
    vs = [v.co for v in glows["Glints"].data.vertices]
    mid = Vector(((min(v.x for v in vs) + max(v.x for v in vs)) / 2, (min(v.y for v in vs) + max(v.y for v in vs)) / 2, (min(v.z for v in vs) + max(v.z for v in vs)) / 2))
    print("GLINTS box centre game axes", (round(-mid.x, 4), round(mid.z, 4), round(mid.y, 4)), flush=True)
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=2.4, size=640)
    lib = pose_library(frames)
    for o in [body, glows["Flames"]]:
        for name, row in pet_kit.stress_report(rig, o, lib).items():
            print("STRESS", o.name[-12:], name, row, flush=True)
    for name in ("Nap", "Proud", "Walk"):
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, GROUND_PARTS), flush=True)
    side = (1, -0.05, 0.12, 2.4, VIEW_AT)
    face = (0.25, -0.95, 0.15, 0.75, FACE_AT)
    wide = (0.62, -0.72, 0.4, 2.4, VIEW_AT)
    for name, view in (("Blink", face), ("Wide", face), ("Walk", wide), ("Nap", wide), ("Proud", side), ("Look", face), ("Wag", wide), ("Fire", wide)):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.4, 2.4, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)
