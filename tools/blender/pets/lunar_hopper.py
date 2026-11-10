"""The Lunar Hopper (Rare, Moonlight; Beginner Qi Egg): "It leaps only under moonlight, and each leap lands a little further from the ground than it
should."

Recreated (November 10, 2026; the old model was a faceted low-poly lavender rabbit with tall cyan ears): the jade rabbit of the moon (the owner's choice),
the moon-elixir rabbit of the old tales, in a design language of its own: a mochi dumpling that keeps the moon's medicine. Round and soft, sat up on its
big flat hind feet: a plump pear of a body, a big round head with full round cheeks, a fluffy ruff at its chest; long soft lop
ears that rise from its crown and hang down beside its cheeks, their tips dipped in moonlight; big moonstone eyes; a silver crescent inlaid on its brow;
a cotton tail. In its front paws, held slanting across its chest, a little jade pestle for pounding the elixir. Its fur is pearl white with a cool blue
moonlit sheen, faint pale craters dappled over its haunches like the moon's own face.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/lunar_hopper.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre, its feet on the ground (z = 0). +X is its left. The maps go to assets/pets/BeginnerQiEgg/.

What touches what: head, body, arms, feet, ruff and tail are one fused skin; each ear is its own blade, its root buried in its crown; the eyes sit in their sockets under their lids; the pestle (its own
piece) is gripped by both front paws; the crescent (a glow piece) is half sunk into its brow.
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
PET = "LunarHopper"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "BeginnerQiEgg")

# ---------- colours: pearl fur, moonlight and jade ----------
PEARL, PEARL_WARM = rgb(244, 242, 250), rgb(250, 247, 244)
SHEEN, LAVENDER = rgb(196, 212, 246), rgb(168, 166, 210)
CRATER = rgb(214, 222, 244)
MOONTIP, MOONTIP_DEEP = rgb(196, 222, 255), rgb(120, 168, 248)     # its ear tips, dipped in moonlight
EAR_IN, BLUSH, NOSE = rgb(238, 200, 218), rgb(246, 190, 206), rgb(232, 140, 168)
MOUTH = rgb(120, 70, 96)
PAD = rgb(226, 170, 190)
LASH = rgb(52, 46, 84)
JADE, JADE_DEEP, JADE_LIGHT = rgb(150, 214, 182), rgb(52, 140, 104), rgb(218, 246, 230)     # pale celadon jade (deep green, it read as a bottle)
GLINT_HEX = "f4f8ff"
MOON_HEX = "8fbcff"          # its crescent: moon blue, as its ear tips (pale, it vanished against its white fur)

# ---------- the frame of it ----------
HEAD = V(0, -0.07, 0.39)
HEAD_R = (0.125, 0.11, 0.105)                        # big and round
EYE_R = 0.036
EYE_C = V(0.06, -0.142, 0.415)
EYE_AXIS = V(0.45, -0.87, 0.12).normalized()         # big and set forward: a sweet, open look
LID_UP, LID_LOW = (52.0, 118.0, 0.0026), (-44.0, -126.0, 0.0022)     # wide open (lower over the eye it read as grumpy); the lower lid's edge just above its skin (deeper, it hid inside the socket, touching nothing)
LID_TILT = 6.0
BLINK_U, BLINK_L = 66.0, 22.0
IRIS, PUPIL = 0.92, 0.42
# its body, sat up: a plump pear
BELLY = (V(0, 0.02, 0.13), (0.12, 0.13, 0.13))
BACK = (V(0, 0.05, 0.19), (0.112, 0.12, 0.12))
CHEST = (V(0, -0.03, 0.25), (0.095, 0.09, 0.1))
RUFF = (V(0, -0.06, 0.305), (0.096, 0.08, 0.055))
HAUNCH = (V(0.08, 0.06, 0.1), (0.085, 0.11, 0.095))
TAIL_C, TAIL_R = V(0, 0.165, 0.11), 0.05
# a lop ear (left): from its crown, up and out over, then hanging down beside its cheek
EAR = [V(0.05, -0.05, 0.462), V(0.098, -0.05, 0.502), V(0.143, -0.055, 0.492), V(0.166, -0.065, 0.43), V(0.172, -0.075, 0.355), V(0.165, -0.085, 0.272)]     # (arched high off its head it read as headphones)
EAR_PATH = catmull(EAR, 12)
EAR_W = ((0, 0.03), (0.15, 0.04), (0.45, 0.05), (0.75, 0.048), (0.92, 0.035), (1, 0.012))     # half-widths, crown to tip
EAR_CUP = 0.22                                       # how far its ear's edges curl in toward its head (further, they touched its cheeks and fused)
EAR_TIP = 0.72                                       # where the moonlight painted on its ear tips starts (a glowing sheath there read as a bandage)
# a front leg (left): shoulder, elbow, wrist, the paw gripping the pestle
ARM = [V(0.058, -0.075, 0.262), V(0.074, -0.118, 0.212), V(0.044, -0.16, 0.214), V(0.022, -0.173, 0.218)]     # forearms clear of its chest and ruff (fused to them, raising them tore)
ARM_R = [0.028, 0.023, 0.019, 0.017]
# a hind foot (left): the heel under the haunch, long and flat to the toes
FOOT = [V(0.095, 0.1, 0.027), V(0.09, 0.02, 0.025), V(0.084, -0.088, 0.022)]     # big, long rabbit's feet
PESTLE_TOP, PESTLE_END = V(0.03, -0.178, 0.282), V(-0.034, -0.19, 0.14)     # held slanting across its chest (upright, it read as a bottle)
CRESCENT = (V(0, -0.14, 0.476), 0.0165)              # on its brow, clear of its lids: centre, radius


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def path_tan(path, f, reach=0.02):
    return (path_at(path, min(1.0, f + reach)) - path_at(path, max(0.0, f - reach))).normalized()


def arm_radius(f):
    return float(np.interp(f, np.linspace(0, 1, len(ARM_R)), ARM_R))


# ---------- the ears ----------
def ear_frame(side, u):
    """Along its ear: the tangent, the 'out' (away from its head) and the width across."""
    c = mir(path_at(EAR_PATH, u), side)
    t = mir(path_tan(EAR_PATH, u), side)
    d = c - (HEAD + V(0, 0, 0.02))
    n = (d - t * t.dot(d)).normalized()
    b = t.cross(n).normalized()
    return c, t, n, b


def ear_point(side, grow=0.0):
    def point(u, v):
        c, t, n, b = ear_frame(side, u)
        s = v * 2 - 1
        w = prof(EAR_W, u) + grow
        cup = EAR_CUP * w * (1 - s * s)              # cupped: its edges curl in toward its head
        return tuple(c + b * (s * w) + n * cup)
    return point


def ear_thick(grow=0.0):
    def thick(u, v):
        s = v * 2 - 1
        return (0.016 * (1 - 0.4 * u)) * math.sqrt(max(0.0, 1 - s * s)) ** 0.5 + 0.005 + 2 * grow     # (a rim one voxel thin could tear in the re-mesh)
    return thick


def build_ear(side, name, coll, low=False):
    """One lop ear: its own blade, its root buried in its crown (fused into the skin, the game mesh's re-mesh broke its thin rims)."""
    m = Mesh()
    nu, nv = (16, 6) if low else (48, 14)
    m.sheet(ear_point(side), ear_thick(), nu, nv)
    return m.finish(name, coll)


def paint_ear(o, side):
    """Soft pink on its inner face, pearl on its back, both going to moonlight blue toward the tip."""
    Pv = verts(o)
    f, _ = nearest_on([mir(q, side) for q in EAR_PATH], Pv)
    inner = np.zeros(len(Pv))
    for i in range(len(Pv)):
        c, t, nn, b = ear_frame(side, float(f[i]))
        off = Vector(Pv[i]) - c
        we = prof(EAR_W, float(f[i]))
        sx = off.dot(b) / we
        inner[i] = smooth(0.0005, -0.0015, off.dot(nn) - EAR_CUP * we * (1 - min(1.0, sx * sx)))
    strands = fbm(Pv * np.array([1.0, 1.0, 3.0]), 90.0, 3, 9)
    back = mix(np.broadcast_to(PEARL, (len(Pv), 3)), SHEEN, 0.35)      # its back in the moon's cool light
    col = mix(back, EAR_IN, inner * smooth(0.06, 0.2, f) * 0.85)
    tips = smooth(EAR_TIP, EAR_TIP + 0.08, f)
    col = mix(col, mix(MOONTIP, MOONTIP_DEEP, smooth(0.8, 1.0, f)), tips * 0.95)
    col = col * (0.96 + 0.06 * strands)[:, None]
    paint(o, np.clip(col, 0, 1), 0.78 - 0.3 * tips, np.zeros(len(Pv)))


# ---------- the skin ----------
def build_skin():
    core = Mesh()
    for c, r in (BELLY, BACK, CHEST):
        core.ball(c, r)
    for side in (1, -1):
        core.ball(mir(HAUNCH[0], side), HAUNCH[1])
        core.tube(catmull([mir(p, side) for p in FOOT], 8), lambda f: 0.031 - 0.004 * f, sides=24, flat=1.35, plane=V(1, 0, 0))   # wide, flat feet
        core.ball(mir(FOOT[-1] + V(0, -0.006, 0.0), side), (0.037, 0.03, 0.022), 24, 14)       # one soft round toe-front (little toe balls went blocky in the game mesh)
    core.ball(TAIL_C, (TAIL_R,) * 3, 32, 20)
    # the cotton tail: a cloud of little puffs
    for k in range(10):
        a, e = k * 2.39996, math.asin(-1 + 2 * (k + 0.5) / 10)
        d = V(math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e))
        if d.y < -0.3:
            continue
        core.ball(TAIL_C + d * (TAIL_R * 0.78), (0.028,) * 3, 14, 9)
    # the ruff at its chest: a soft bib of fluff, its lower edge in big round scallops (small beads of it read as a necklace)
    core.ball(RUFF[0] + V(0, -0.012, -0.012), (0.088, 0.066, 0.06))
    for k in range(5):
        a = math.radians(-64 + 32 * k)
        core.ball(RUFF[0] + V(math.sin(a) * 0.066, -math.cos(a) * 0.052 - 0.004, -0.03 + 0.008 * abs(k - 2)), (0.034, 0.03, 0.032), 20, 12)     # (lower, it swallowed its paws)
    c = core.finish(N + "CoreHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.005, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 24})])     # (less, its back read lumpy)
    fine = Mesh()
    fine.ball(HEAD, HEAD_R, 48, 32)
    fine.ball(V(0, -0.14, 0.33), (0.036, 0.03, 0.026))                    # a little chin
    for side in (1, -1):
        fine.ball(mir(V(0.068, -0.128, 0.362), side), (0.066, 0.058, 0.056))    # full, round cheeks
        fine.ball(mir(V(0.02, -0.162, 0.362), side), (0.025, 0.022, 0.021))     # the whisker pads (bigger, they read as a moustache)
        fine.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.008, (EYE_R * 1.08,) * 3, 28, 18)     # the socket
        fine.ball(mir(EAR[0] + V(0.006, 0.002, 0.008), side), (0.024, 0.022, 0.016), 20, 12)     # the soft base its ear springs from
        fine.tube(catmull([mir(p, side) for p in ARM], 8), arm_radius, sides=20)
        fine.ball(mir(ARM[-1], side), (0.019, 0.018, 0.019), 18, 12)              # the paw
        # (no tufts at its cheeks: beside its hanging ears they read as spikes)
    th = fine.finish(N + "FineHi", HI)
    bm = bmesh.new()
    bm.from_mesh(c.data)
    bm.from_mesh(th.data)
    bm.to_mesh(c.data)
    bm.free()
    bpy.data.objects.remove(th, do_unlink=True)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0026, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 5})])
    P = verts(c)
    P[:, 2] = np.maximum(P[:, 2], 0.0)                                    # its feet flat on the ground
    set_verts(c, P)
    c.name = N + "SkinHi"
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    return c


# ---------- the pestle, the crescent and the ear tips ----------
def pestle_radius(f):
    """f 0 at its top, 1 at its pounding end: a rounded grip end, a handle, a carved ring, swelling to a long round head."""
    grip = 0.0115 * math.sqrt(max(0.0, 1 - ((f - 0.045) / 0.045) ** 2)) if f < 0.09 else 0.0
    handle = 0.0095 + 0.0015 * math.sin(math.pi * min(1.0, f / 0.55))
    ring = 0.0016 * math.exp(-((f - 0.5) / 0.014) ** 2)
    t = (f - 0.79) / 0.21
    head = 0.019 * math.sqrt(max(0.0, 1 - t * t)) if f > 0.58 else 0.0       # a long, round-ended head (a ball read as a rattle, a flat end as a bottle)
    return max(grip, handle + ring, head, 0.0012)


def build_pestle(name, coll, sides=28, per=60):
    m = Mesh()
    pts = [PESTLE_TOP.lerp(PESTLE_END, k / per) for k in range(per + 1)]
    m.tube(pts, pestle_radius, sides=sides)
    return m.finish(name, coll)


def paint_pestle(o):
    P = verts(o)
    f, _ = nearest_on([PESTLE_TOP, PESTLE_END], P)
    vein = fbm(P * np.array([1.0, 1.0, 0.4]), 60.0, 4, 41)
    col = mix(np.broadcast_to(JADE, (len(P), 3)), JADE_DEEP, smooth(0.55, 0.85, vein) * 0.55)          # celadon, clouded deeper in its veins
    col = mix(col, JADE_LIGHT, smooth(0.6, 0.9, fbm(P, 110.0, 3, 43)) * 0.5)
    ring = np.exp(-((f - 0.5) / 0.02) ** 2)
    col = mix(col, JADE_DEEP, ring * 0.8)                                                         # a carved ring, deeper jade
    paint(o, np.clip(col, 0, 1), 0.18 + 0.12 * ring, np.zeros(len(P)))


def crescent_path(tree, n=24):
    """Its brow mark: a crescent moon opening up and to its right, laid on its brow and sunk half its thickness in."""
    c, r = CRESCENT
    out = []
    for k in range(n + 1):
        a = math.radians(70 + 230 * k / n)           # a long sweep round, horns up and to one side (a short lower arc, horns up, read as a smile)
        p = c + V(math.cos(a) * r, 0, math.sin(a) * r)
        hit = tree.ray_cast(p + V(0, -0.05, 0.02), (V(0, 1, -0.4)).normalized(), 0.2)
        out.append(hit[0] if hit[0] is not None else p)
    return out


def build_crescent(tree, name, coll, low=False):
    m = Mesh()
    m.tube(crescent_path(tree, 14 if low else 32), lambda f: 0.0062 * math.sin(math.pi * min(1.0, 0.03 + f * 0.94)) ** 1.1 + 0.0011, sides=8 if low else 16)
    return m.finish(name, coll)


# ---------- paint ----------
def paint_skin(o):
    """Pearl fur, cool blue moonlight on its back and crown, soft lavender in its folds; faint pale craters on its haunches; a whiter muzzle and
    belly; soft pink inside its ears, their tips dipped in moonlight blue; pink at its nose and on the pads of its feet; a hint of blush on its cheeks."""
    Pv = verts(o)
    Nn = normals(o)
    x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
    n = len(Pv)
    # the fur: fine strands running down and back
    strands = fbm(Pv * np.array([3.0, 3.0, 0.6]), 90.0, 3, 5)
    clumps = fbm(Pv, 30.0, 3, 6)
    col = mix(np.broadcast_to(PEARL, (n, 3)), PEARL_WARM, smooth(0.4, 0.7, clumps) * 0.6)
    # moonlight from above and behind: a cool sheen on its back, crown and the tops of its ears
    moon = np.clip(Nn @ np.array(tuple(V(0.0, 0.45, 0.89).normalized())), 0, 1)
    col = mix(col, SHEEN, smooth(0.35, 0.95, moon) * 0.55)
    col = mix(col, LAVENDER, smooth(0.1, -0.7, Nn[:, 2]) * 0.3)
    col = col * (0.95 + 0.07 * strands)[:, None]
    # pale craters dappled over its haunches and back, like the face of the moon
    d1, d2, own = cells_of(Pv, 22.0, 3)
    hz = np.zeros(n)
    for side in (1, -1):
        hz = np.maximum(hz, 1 - smooth(0.08, 0.12, np.linalg.norm((Pv - np.array(tuple(mir(HAUNCH[0], side)))) / np.array((1.0, 0.9, 1.0)), axis=1)))
    crater = (1 - smooth(0.16, 0.24, d1)) * (own > 0.45) * hz * smooth(-0.2, 0.3, Nn[:, 1] * 0 + 1)
    rim = smooth(0.16, 0.2, d1) * (1 - smooth(0.2, 0.25, d1)) * (own > 0.45) * hz
    col = mix(col, CRATER, crater * 0.7)
    col = mix(col, LAVENDER, rim * 0.35)
    # a whiter muzzle, chin and belly
    head = 1 - smooth(0.12, 0.16, np.linalg.norm((Pv - np.array(tuple(HEAD))) / np.array((1.0, 0.95, 1.0)), axis=1))
    muzzle = (1 - smooth(0.03, 0.06, np.linalg.norm((Pv - np.array((0, -0.165, 0.35))) / np.array((1.4, 1.0, 1.0)), axis=1)))
    belly = smooth(0.2, -0.6, Nn[:, 1]) * smooth(0.28, 0.08, z) * (1 - head)
    col = mix(col, PEARL_WARM * 1.01, np.clip(muzzle + belly * 0.6, 0, 1))
    # blush on its cheeks; its nose; its mouth, a little 'y' under the nose
    blush = np.zeros(n)
    for side in (1, -1):
        blush = np.maximum(blush, 1 - smooth(0.006, 0.026, np.linalg.norm(Pv - np.array((side * 0.085, -0.168, 0.37)), axis=1)))
    col = mix(col, BLUSH, blush * 0.55)
    nose = 1 - smooth(0.0, 1.0, np.linalg.norm((Pv - np.array((0, -0.188, 0.381))) / np.array((0.011, 0.012, 0.008)), axis=1))
    col = mix(col, NOSE, smooth(0.0, 0.3, nose))
    lx, lz = x, z - 0.372
    philtrum = (1 - smooth(0.0011, 0.0024, np.abs(lx))) * (lz < -0.001) * (lz > -0.012)
    smile = np.zeros(n)
    for side in (1, -1):                              # each side a small arc from the foot of the line, curving up and out
        rr = np.hypot(lx - side * 0.0105, lz + 0.0015)
        smile = np.maximum(smile, (1 - smooth(0.0011, 0.0024, np.abs(rr - 0.0105))) * (lz < -0.0045))
    mouth = np.clip(philtrum + smile, 0, 1) * (y < -0.15) * smooth(-0.2, 0.3, -Nn[:, 1])
    col = mix(col, MOUTH, mouth * 0.85)
    pads = smooth(0.012, 0.0, z) * (np.abs(x) > 0.05) * smooth(0.05, -0.02, y)
    col = mix(col, PAD, pads * 0.7)
    # three toe grooves on top of each foot's front
    toes = np.zeros(n)
    for side in (1, -1):
        fx = (x - side * FOOT[-1].x) * side
        front = smooth(-0.072, -0.088, y) * smooth(0.014, 0.028, z) * smooth(0.055, 0.042, z) * (np.abs(fx) < 0.026)      # (longer, they read as stripes)
        g = np.minimum(np.abs(fx), np.abs(np.abs(fx) - 0.012))                   # to the nearest of three grooves: four toes
        toes = np.maximum(toes, front * (1 - smooth(0.0012, 0.003, g)))
    col = mix(col, LAVENDER, toes * 0.6)
    relief = (strands - 0.5) * 0.0005 + (clumps - 0.5) * 0.0006 - mouth * 0.0008 - crater * 0.0008 - toes * 0.0012      # (stronger, its fur read lumpy)
    set_verts(o, Pv + Nn * relief[:, None])
    paint(o, np.clip(col, 0, 1), 0.78 - 0.1 * moon - 0.25 * smooth(0.0, 0.3, nose), np.zeros(n))


def cells_of(P, f, seed=0):
    """Distance to the nearest cell point and that cell's own random number."""
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


def eye_paint(o, fr):
    """A moonstone eye: deep indigo going to a silver-blue rim, a soft shimmer of moonlight across it, a big round pupil."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    col = np.broadcast_to(rgb(24, 22, 48), (len(px), 3)).copy()
    iris = mix(rgb(70, 64, 150), rgb(170, 196, 240), smooth(0.35, 0.9, r / IRIS))
    azi = np.arctan2(py, px)
    iris = iris * (0.9 + 0.1 * np.sin(azi * 30 + np.sin(azi * 4) * 1.2))[:, None]
    shimmer = smooth(0.0, 0.6, -py / IRIS) * smooth(0.95, 0.5, r / IRIS)
    iris = mix(iris, rgb(205, 222, 255), shimmer * 0.35)
    iris = mix(iris, iris * 0.55, smooth(-0.1, 0.9, py / IRIS) * 0.5)
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS, r))
    col = mix(col, rgb(40, 34, 90), smooth(IRIS - 0.12, IRIS - 0.02, r) * (1 - smooth(IRIS - 0.02, IRIS, r)))
    col = mix(col, rgb(10, 8, 24), 1 - smooth(PUPIL - 0.02, PUPIL + 0.02, r))
    paint(o, col, np.full(len(px), 0.05), np.zeros(len(px)))


def show_glows(glows):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 2.0
        o.data.materials.clear()
        o.data.materials.append(mat)
        o.visible_shadow = False


def build_hi(clay=False):
    pieces, data = {}, {}
    skin = build_skin()
    pieces["Skin"] = skin
    tree = tree_of(skin)
    data["tree"] = tree
    pieces["Pestle"] = build_pestle(N + "PestleHi", HI)
    for side, tag in ((1, "L"), (-1, "R")):
        pieces["Ear" + tag] = build_ear(side, N + "Ear" + tag + "Hi", HI)
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, PEARL, LASH)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, PEARL, LASH, lower_share=0.7)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-26, 26, 0.009, 14), (22, -20, 0.004, 8))),
             "Crescent": build_crescent(tree, N + "Crescent_Glow_" + MOON_HEX, HI)}
    if not clay:
        paint_skin(skin)
        paint_pestle(pieces["Pestle"])
        paint_ear(pieces["EarL"], 1)
        paint_ear(pieces["EarR"], -1)
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    return pieces, frames, glows, data


VIEWS = [(0, -1, 0.25), (0.62, -0.72, 0.35), (1, 0, 0.15), (0, 1, 0.3), (-0.6, 0.6, 0.45), (-0.62, -0.72, 0.3), (0, -0.05, 1), (0.5, -0.5, -0.4)]
VIEW_AT = (0, -0.02, 0.25)
FACE_AT = (0, -0.12, 0.39)
EXTRA = [(0, -1, 0.1, 0.8, FACE_AT), (0.75, -0.6, 0.25, 0.8, FACE_AT), (1, -0.1, 0.1, 0.9, FACE_AT), (0.4, -0.85, 0.3, 0.32, tuple(EYE_C)),
         (0.3, -0.9, 0.1, 0.6, (0, -0.16, 0.22)), (0.6, 0.6, 0.3, 0.8, (0, 0.1, 0.12))]

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
        g.inputs["Base Color"].default_value = (0.05, 0.04, 0.1, 1)
        g.inputs["Roughness"].default_value = 0.15
    else:
        mat = hi_material(ao_distance=0.02, ao_share=0.35)
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(dark if STAGE == "clay" and key.startswith("Eye") else mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=1.9, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SKIN_QUADS = 3300                  # (about 9.4k tris in all: a Rare pet that sits close to the camera)
SCALES = {"EyeL": 2.4, "EyeR": 2.4, "LidUL": 1.4, "LidUR": 1.4, "LidLL": 1.4, "LidLR": 1.4, "Pestle": 1.6, "EarL": 1.2, "EarR": 1.2}


def build_low(pieces, frames):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS), "Pestle": build_pestle(N + "PestleLow", GAME, sides=10, per=16),
            "EarL": build_ear(1, N + "EarLLow", GAME, low=True), "EarR": build_ear(-1, N + "EarRLow", GAME, low=True)}
    P = verts(lows["Skin"])
    P[:, 2] = np.maximum(P[:, 2], 0.0)                    # its soles on the ground (the re-topology lays them a few millimetres under)
    set_verts(lows["Skin"], P)
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 24, 16)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
TRUNK_HEADS = (("Hips", V(0, 0.06, 0.11), "Root"), ("Body", V(0, 0.02, 0.19), "Hips"), ("Chest", V(0, -0.03, 0.26), "Body"), ("Neck", V(0, -0.06, 0.31), "Chest"),
               ("Head", V(0, -0.07, 0.35), "Neck"))
TRUNK = catmull([V(0, 0.09, 0.05)] + [at for _, at, _ in TRUNK_HEADS] + [HEAD + V(0, 0, 0.06)], 8)
EAR_F = (0.0, 0.42)                                  # where each ear bone starts, along the ear
ARM_NAMES = {"L": ["ArmL1", "ArmL2", "PawL"], "R": ["ArmR1", "ArmR2", "PawR"]}
LEG_NAMES = {"L": ["LegL1", "LegL2", "FootL"], "R": ["LegR1", "LegR2", "FootR"]}
HIP_JOINT = V(0.07, 0.07, 0.12)                       # (left) where its hind leg turns, inside the haunch


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None)]
    for name, at, parent in TRUNK_HEADS:
        bones.append((name, at.copy(), parent))
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head")]
        bones += [("Ear%s1" % tag, mir(path_at(EAR_PATH, EAR_F[0]), side), "Head"), ("Ear%s2" % tag, mir(path_at(EAR_PATH, EAR_F[1]), side), "Ear%s1" % tag)]
        parent = "Chest"
        for k, name in enumerate(ARM_NAMES[tag]):
            bones.append((name, mir(ARM[k], side), parent))
            parent = name
        bones += [("Leg%s1" % tag, mir(HIP_JOINT, side), "Hips"), ("Leg%s2" % tag, mir(FOOT[0], side), "Leg%s1" % tag), ("Foot" + tag, mir(FOOT[1], side), "Leg%s2" % tag)]
    bones.append(("Pestle", ARM[-1].copy(), "PawL"))
    bones.append(("Tail", TAIL_C + V(0, -0.03, 0), "Hips"))
    return armature(bones)


def trunk_knots():
    pts = np.array([tuple(at) for _, at, _ in TRUNK_HEADS])
    f, _ = nearest_on(TRUNK, pts)
    mids = [(f[k] + f[k + 1]) / 2 for k in range(len(f) - 1)]
    return [n for n, _, _ in TRUNK_HEADS], tuple(mids) + (f[-1] + 0.05,)


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


HEAD_ZONE = (HEAD + V(0, -0.02, 0.0), (0.15, 0.14, 0.105))          # its head with its cheeks and muzzle (deeper, it took its ruff along when it turned)


def body_weights(P_):
    names, knots = trunk_knots()
    f_tr, _ = nearest_on(TRUNK, P_)
    hz = np.linalg.norm((P_ - np.array(tuple(HEAD_ZONE[0]))) / np.array(HEAD_ZONE[1]), axis=1)
    arms, feet = {}, {}
    for side, tag in ((1, "L"), (-1, "R")):
        arms[tag] = nearest_on(catmull([mir(p, side) for p in ARM], 8), P_)
        feet[tag] = nearest_on(catmull([mir(p, side) for p in FOOT], 8), P_)
    out = []
    for i in range(len(P_)):
        x, y, z = P_[i]
        tag = "L" if x > 0 else "R"
        side = 1 if x > 0 else -1
        w = chain_weight(names, knots, float(f_tr[i]))
        # the head, cheeks and muzzle
        if hz[i] < 1.12:
            w = blend(w, {"Head": 1.0}, float(smooth(1.12, 0.88, hz[i])))
        # a front leg, down to the paw
        fa, da = arms[tag][0][i], arms[tag][1][i]
        reach = arm_radius(float(fa)) + 0.011
        if da < reach * 1.5 and x * side > -0.012 and hz[i] > 0.95:      # (across the middle too: its paws meet there)
            share = (1 - float(smooth(reach, reach * 1.5, da))) * float(smooth(0.05, 0.22, fa))
            w = blend(w, chain_weight(ARM_NAMES[tag], (0.45, 0.86, 1.2), float(fa)), share)
        # a hind leg: the haunch, the heel and the long foot
        hp = (Vector(P_[i]) - mir(HAUNCH[0], side))
        hh = math.sqrt((hp.x / 0.1) ** 2 + (hp.y / 0.125) ** 2 + (hp.z / 0.11) ** 2)
        if hh < 1.15 and x * side > 0.02:
            w = blend(w, {"Leg%s1" % tag: 1.0}, float(smooth(1.15, 0.85, hh)) * float(smooth(0.02, 0.06, x * side)))
        ff, df = feet[tag][0][i], feet[tag][1][i]
        if df < 0.05 and z < 0.06:
            share = 1 - float(smooth(0.035, 0.05, df))
            foot = blend({"Leg%s2" % tag: 1.0}, {"Foot" + tag: 1.0}, float(smooth(0.3, 0.55, ff)))
            w = blend(w, foot, share * float(smooth(0.06, 0.035, z)))
        # the cotton tail
        td = (Vector(P_[i]) - TAIL_C).length
        if td < 0.09 and y > 0.12:
            w = blend(w, {"Tail": 1.0}, float(smooth(0.09, 0.06, td)) * float(smooth(0.12, 0.15, y)))
        out.append(w)
    return out


def bind_all(lows, rig, glows):
    weigh(lows["Skin"], body_weights(verts(lows["Skin"])))
    rigid(lows["Pestle"], "Pestle")
    for side, tag in ((1, "L"), (-1, "R")):
        f, _ = nearest_on([mir(q, side) for q in EAR_PATH], verts(lows["Ear" + tag]))
        weigh(lows["Ear" + tag], [chain_weight(["Ear%s1" % tag, "Ear%s2" % tag], (EAR_F[1], 1.2), float(t)) for t in f])
    for tag in ("L", "R"):
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    rigid(glows["Crescent"], "Head")
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


# poses in the game's axes (turns x, y, z: +x lifts what points forward; +y turns to its left); the same numbers as PetRig's LH tables
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def probe(rig, body, bones=("EarL1", "EarL2", "ArmL1", "ArmL2", "PawL", "LegL1", "LegL2", "FootL", "Tail", "Head")):
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


def is_head(poly):
    c = np.array(tuple(poly.center))
    return bool(np.linalg.norm((c - np.array(tuple(HEAD_ZONE[0]))) / np.array(HEAD_ZONE[1])) < 1.0)


GROUND_PARTS = {"Feet": ("FootL", "FootR", "LegL2", "LegR2"), "Belly": ("Body", "Hips"), "Tail": ("Tail",), "Ears": ("EarL2", "EarR2"), "Paws": ("PawL", "PawR")}

if __name__ == "__main__" and STAGE in ("all", "rig"):
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.02, ao_share=0.35)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.42, 1))
    lows = build_low(pieces, frames)
    # its face given more of the atlas; its ears projected apart (thin, against its head they'd fold); its feet apart
    unwrap(lows, [(is_head, 1.8), (lambda p: p.center.z < 0.05, 1.0), (None, 1.0)], SCALES, margin=0.012, angle=42)
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.9, 0.9, 0.95, 1), far=("Skin",), reach=(0.004, 0.01), far_reach=(0.008, 0.02))
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    tree = data["tree"]
    for o in glows.values():
        bpy.data.objects.remove(o, do_unlink=True)          # first, so the game's pieces take their exact names
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-26, 26, 0.009, 10), (22, -20, 0.004, 6))),
             "Crescent": build_crescent(tree, N + "Crescent_Glow_" + MOON_HEX, GAME, low=True)}
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
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    uv_clashes(body)
    zs = [(o.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    # (the game's box counts the RootPart, a 0.05 m cube at the origin: its bottom is 0.025 m under the feet, measured in Play on the Volt Fox)
    bottom = min(lo, -0.025)
    print("Z range", round(lo, 4), round(hi, 4), "SOLE from the box middle (the RootPart counted) down to the ground", round((hi + bottom) / 2 - lo, 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name in ("Head", "Pestle", "Hips", "Tail"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    vs = [v.co for v in glows["Glints"].data.vertices]
    mid = Vector(((min(v.x for v in vs) + max(v.x for v in vs)) / 2, (min(v.y for v in vs) + max(v.y for v in vs)) / 2, (min(v.z for v in vs) + max(v.z for v in vs)) / 2))
    print("GLINTS box centre game axes", (round(-mid.x, 4), round(mid.z, 4), round(mid.y, 4)), flush=True)
    probe(rig, body)
    if STAGE == "rig":
        print("DONE", flush=True)
        raise SystemExit(0)


# its stances, in game axes, signs measured on the mesh (probe): +x raises its arms, lifts its toes, tips its head back; -x lifts its tail; an ear
# root swings back with +y on the left, lifts with -z on the left; an ear tip trails back and down with -x. Left values; the right mirrors y and z.
def sym(table):
    out = {}
    for name, v in table.items():
        if name.endswith("L1") or name.endswith("L2") or name.endswith("L") and name[:-1] in ("Paw", "Foot", "Eye"):
            out[name] = v
            r = name[:-2] + "R" + name[-1] if name[-1] in "12" else name[:-1] + "R"
            out[r] = (v[0], -v[1], -v[2]) + tuple(v[3:])
        else:
            out[name] = v
    return out


CROUCH = sym({"Body": (-0.2, 0, 0), "Chest": (-0.08, 0, 0), "Head": (0.12, 0, 0), "EarL1": (0, 0.25, 0), "EarL2": (-0.2, 0, 0), "ArmL1": (-0.2, 0, 0)})
LEAP = sym({"Body": (-0.3, 0, 0), "Chest": (-0.1, 0, 0), "Head": (0.3, 0, 0), "EarL1": (0, 0.35, -0.2), "EarL2": (-0.45, 0, 0), "LegL1": (-0.15, 0, 0),
            "FootL": (-0.3, 0, 0), "ArmL1": (0.2, 0, 0), "Tail": (-0.25, 0, 0)})      # (its legs swung further, its feet pulled its belly into a point)
LOAF = sym({"Body": (-0.14, 0, 0), "Chest": (-0.05, 0, 0), "Head": (-0.2, 0, 0), "EarL1": (0, 0.45, 0.12), "EarL2": (-0.3, 0, 0), "ArmL1": (-0.25, 0, 0)})
POUND_UP = sym({"ArmL1": (0.5, 0, 0), "ArmL2": (0.25, 0, 0), "Body": (0.12, 0, 0), "Head": (0.18, 0, 0), "EarL1": (0, 0.2, -0.15)})
POUND_DOWN = sym({"ArmL1": (-0.25, 0, 0), "ArmL2": (-0.2, 0, 0), "Body": (-0.15, 0, 0), "Head": (-0.12, 0, 0), "EarL2": (0.25, 0, 0)})
HOVER = sym({"LegL1": (-0.12, 0, 0), "FootL": (-0.3, 0, 0), "EarL1": (0, 0.3, 0), "EarL2": (-0.3, 0, 0), "Tail": (-0.2, 0, 0)})


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    return {"Blink": lids(BLINK_U, BLINK_L), "Wide": lids(-12, -6), "Crouch": spec(CROUCH), "Leap": spec(LEAP), "Loaf": {**spec(LOAF), **lids(BLINK_U, BLINK_L)},
            "PoundUp": spec(POUND_UP), "PoundDown": spec(POUND_DOWN), "Hover": spec(HOVER),
            "Look": spec({"Neck": (0.05, 0.3, 0), "Head": (0.1, 0.35, 0.12)}), "EarFlick": spec({"EarL1": (0, 0, -0.45), "EarL2": (0.3, 0, -0.2)}),
            "Wiggle": spec({"Tail": (0, 0.45, 0)})}


if __name__ == "__main__" and STAGE == "all":
    pose(rig, {})
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=1.9, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    for name in ("Crouch", "Loaf", "PoundUp", "PoundDown"):
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, GROUND_PARTS), flush=True)
    pose(rig, {})
    print("GROUND rest", lowest_of(body, GROUND_PARTS), flush=True)
    side = (1, -0.05, 0.12, 1.9, VIEW_AT)
    face = (0.25, -0.95, 0.15, 0.8, FACE_AT)
    wide = (0.62, -0.72, 0.35, 1.9, VIEW_AT)
    for name, view in (("Blink", face), ("Wide", face), ("Crouch", side), ("Leap", side), ("Loaf", wide), ("PoundUp", wide), ("PoundDown", wide), ("Hover", side),
                       ("Look", face), ("EarFlick", wide), ("Wiggle", (0.6, 0.7, 0.3, 1.9, VIEW_AT))):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.35, 1.9, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)
