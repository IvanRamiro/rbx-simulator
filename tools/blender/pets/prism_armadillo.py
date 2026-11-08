"""The Prism Armadillo (Rare, Crystals; Bloomwood Egg): "When it curls up, its plates split light into every colour. It curls up often, mostly to show off."

An armadillo that can roll right up into a ball. Its armour is crystal: a shield over the shoulders, four bands that slide over each other, a shield over the hips, each plate faceted like cut quartz, the bands' back edges in small prism points;
under it, soft dusty-rose skin. A long snout with a pink nose, tall cupped ears, stubby legs with big digging claws, a ringed tail. Down its back a row of small prisms glows, each slowly changing colour. Its face is like no other pet's:
small bead eyes under an overhanging crystal brow, with no upper lids; soft cheek pads slide up from below to squint, and all the way to blink.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/prism_armadillo.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, claws on z = 0. The maps go to assets/pets/BloomwoodEgg/.

What touches what: the head's back is sunk into the body under the shield; ears and the head shield are sunk into the head; eyes half sunk in it; the cheek pads lie on it, below the eyes; each band's front edge lies under the band before it,
with a gap; the bands' inner faces lie over the body with a gap; legs are sunk into the body; claws into the paws; the tail's root into the rump, under the pelvic shield; each crest prism stands sunk into its plate.
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
STAGE = ARGS[0] if ARGS else "all"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "PrismArmadillo"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "BloomwoodEgg")

# ---------- colours ----------
SKIN, SKIN_D, BELLY, PINK = rgb(196, 150, 160), rgb(140, 100, 116), rgb(238, 210, 206), rgb(244, 150, 170)
QUARTZ, QUARTZ_D, ICE, LILAC = rgb(232, 228, 248), rgb(160, 150, 200), rgb(196, 236, 248), rgb(200, 176, 240)
CLAW, BEAD = rgb(70, 56, 72), rgb(18, 12, 22)

# ---------- the frame of it ----------
TORSO = catmull([V(0, -0.3, 0.25), V(0, -0.1, 0.275), V(0, 0.12, 0.275), V(0, 0.3, 0.235)], 12)
TORSO_W = ((0, 0.13), (0.15, 0.18), (0.5, 0.2), (0.85, 0.18), (1, 0.12))
TORSO_T = ((0, 0.12), (0.15, 0.15), (0.5, 0.165), (0.85, 0.15), (1, 0.1))
TORSO_B = ((0, 0.1), (0.15, 0.12), (0.5, 0.13), (0.85, 0.12), (1, 0.09))
# the armour, front to back: (name, y front, y back, rows of facets)
PLATES = (("Shield", -0.275, -0.065, 5), ("Band1", -0.085, -0.025, 1), ("Band2", -0.045, 0.015, 1), ("Band3", -0.005, 0.055, 1), ("Band4", 0.035, 0.095, 1), ("Pelvis", 0.075, 0.295, 5))      # (the pelvic shield stops where the torso does: past it, its rows would fold into each other)
ARC = 1.78           # radians either side of the top that the armour reaches down
TEETH = 16           # prism points along each plate's back edge
P0, NOSE = V(0, -0.28, 0.27), V(0, -0.575, 0.17)
HD = (NOSE - P0).normalized()
HUP = (V(0, 0, 1) - HD * HD.z).normalized()
H_S = (0.0, 0.12, 0.3, 0.45, 0.62, 0.85, 1.0)
H_W = (0.07, 0.1, 0.106, 0.085, 0.058, 0.042, 0.03)
H_T = (0.06, 0.09, 0.098, 0.076, 0.052, 0.038, 0.03)
H_B = (0.06, 0.08, 0.076, 0.06, 0.044, 0.034, 0.026)
TAIL = catmull([V(0, 0.27, 0.2), V(0, 0.42, 0.17), V(0, 0.58, 0.12), V(0, 0.72, 0.085)], 10)
FRONT = [V(0.12, -0.2, 0.2), V(0.15, -0.23, 0.11), V(0.15, -0.215, 0.045), V(0.15, -0.25, 0.022)]
HIND = [V(0.12, 0.2, 0.2), V(0.15, 0.16, 0.11), V(0.15, 0.22, 0.045), V(0.15, 0.19, 0.022)]
LEGS = (("FL", 1, FRONT, (0.06, 0.042, 0.032, 0.03)), ("FR", -1, FRONT, (0.06, 0.042, 0.032, 0.03)), ("BL", 1, HIND, (0.065, 0.045, 0.034, 0.032)), ("BR", -1, HIND, (0.065, 0.045, 0.034, 0.032)))
EYE_R = 0.021


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def head_axis(s):
    return P0.lerp(NOSE, s)


def hprof(s, knots):
    return float(np.interp(s, H_S, knots))


def hash_of(k):
    return math.sin(k * 12.9898) * 43758.5453 % 1.0


def torso_at(y):
    """The torso's centre-line point and its fraction along, at a given y."""
    ys = np.array([p.y for p in TORSO])
    i = int(np.clip(np.searchsorted(ys, y) - 1, 0, len(TORSO) - 2))
    t = (y - ys[i]) / max(1e-6, ys[i + 1] - ys[i])
    t = min(1.0, max(0.0, t))
    p = TORSO[i].lerp(TORSO[i + 1], t)
    f = (i + t) / (len(TORSO) - 1)
    return p, f


def torso_point(y, a, extra=0.0):
    """On the torso's surface (plus extra outward), at y, at angle a from the top (positive toward +X)."""
    c, f = torso_at(y)
    w, t, b = prof(TORSO_W, f), prof(TORSO_T, f), prof(TORSO_B, f)
    s, co = math.sin(a), math.cos(a)
    x = (w + extra) * math.copysign(abs(s) ** 0.85, s)
    z = (t + extra) * math.copysign(abs(co) ** 0.85, co) if co >= 0 else -(b + extra) * abs(co) ** 0.85
    return V(c.x + x, y, c.z + z)


def rings_mesh(name, coll, top, rings, bottom):
    m = Mesh()
    bm = m.bm
    a = bm.verts.new(top)
    grid = [[bm.verts.new(tuple(p)) for p in ring] for ring in rings]
    b = bm.verts.new(bottom)
    nt = len(rings[0])
    for j in range(nt):
        j2 = (j + 1) % nt
        bm.faces.new((a, grid[0][j], grid[0][j2]))
        for i in range(len(grid) - 1):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j2], grid[i][j2]))
        bm.faces.new((grid[-1][j], b, grid[-1][j2]))
    return m.finish(name, coll)


# ---------- the body under the armour ----------
def build_torso(name, coll, nt=64, rows=60):
    rings = []
    ys = np.linspace(TORSO[0].y, TORSO[-1].y, rows)
    for y in ys:
        rings.append([tuple(torso_point(float(y), TAU * j / nt)) for j in range(nt)])
    o = rings_mesh(name, coll, tuple(TORSO[0] - V(0, 0.05, 0)), rings, tuple(TORSO[-1] + V(0, 0.04, -0.01)))
    return o


def build_body(name, coll):
    m = Mesh()
    t = build_torso(N + "Torso", coll)
    m.bm.from_mesh(t.data)
    bpy.data.objects.remove(t, do_unlink=True)
    for key, side, knots, radii in LEGS:
        m.tube(catmull([mir(p, side) for p in knots[:3]], 6), lambda f, r=radii: float(np.interp(f, (0, 0.5, 1), r[:3])), sides=18)
        m.ball(mir(knots[3], side), (radii[3] * 1.05, radii[3] * 1.4, radii[3] * 0.75), 20, 12)
    m.tube(TAIL, lambda f: 0.055 * (1 - f) ** 0.9 + 0.012, sides=20)
    # the neck, into the back of the head
    m.tube(catmull([V(0, -0.22, 0.25), V(0, -0.3, 0.26), V(0, -0.34, 0.265)], 4), lambda f: 0.09 - 0.02 * f, sides=20)
    o = m.finish(name, coll, recalc=False)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0045, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 8})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- the armour ----------
def facet(u, v):
    """A cut gem in each cell: a flat table, bevelled down to a groove at its edges. u, v in cell units."""
    fu, fv = u - np.floor(u) - 0.5, v - np.floor(v) - 0.5
    d = 1 - 2 * np.maximum(np.abs(fu), np.abs(fv))
    return np.clip(d / 0.3, 0, 1) ** 0.8


def plate_arc(name):
    """How far down each plate reaches: each one a little less than the one before, so their side ends never lie in one plane where they overlap."""
    k = [p[0] for p in PLATES].index(name)
    return ARC * (1 - 0.014 * k)


def plate_surface(spec, cols, rows, inset=0.0, teeth=TEETH):
    """A plate's outer (or, with an inset, inner) surface, rows from front to back, columns round the arc; the back edge in prism points."""
    name, y0, y1, _ = spec
    arc = plate_arc(name)
    a = np.linspace(-arc, arc, cols + 1)
    phase = (a + arc) / (2 * arc) * teeth
    tri = np.abs(((phase + 0.5) % 1.0) * 2 - 1)
    pts = []
    for i in range(rows + 1):
        g = i / rows
        row = []
        for j in range(cols + 1):
            y = y0 + (y1 - y0) * g + 0.006 * math.sin(math.pi * (phase[j] % 1.0)) * g ** 6      # (the back edge gently scalloped, one scallop to each tile)
            lift = 0.024 + 0.016 * g - inset
            if name == "Shield":
                lift = 0.03 - inset - 0.012 * (1 - g) ** 3
            if name == "Pelvis":
                lift = 0.022 + 0.01 * g - inset
            # the lower edge too: prism points along each side
            p = torso_point(min(TORSO[-1].y, max(TORSO[0].y, y)), float(a[j]), lift)
            row.append(tuple(p))
        pts.append(row)
    return np.array(pts)


def build_plate(spec, name, coll, cols, rows, thick=0.014):
    outer = plate_surface(spec, cols, rows)
    inner = plate_surface(spec, cols, rows, inset=thick)
    R, C = outer.shape[0], outer.shape[1]
    v = np.concatenate((outer.reshape(-1, 3), inner.reshape(-1, 3)))
    n = R * C

    def at(i, j):
        return i * C + j
    faces = []
    for i in range(R - 1):
        for j in range(C - 1):
            faces.append((at(i, j), at(i + 1, j), at(i + 1, j + 1), at(i, j + 1)))
            faces.append((n + at(i, j), n + at(i, j + 1), n + at(i + 1, j + 1), n + at(i + 1, j)))
    for j in range(C - 1):
        faces.append((at(0, j), at(0, j + 1), n + at(0, j + 1), n + at(0, j)))
        faces.append((at(R - 1, j), n + at(R - 1, j), n + at(R - 1, j + 1), at(R - 1, j + 1)))
    for i in range(R - 1):
        faces.append((at(i, 0), n + at(i, 0), n + at(i + 1, 0), at(i + 1, 0)))
        faces.append((at(i, C - 1), at(i + 1, C - 1), n + at(i + 1, C - 1), n + at(i, C - 1)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(v.tolist(), [], faces)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def plate_coords(spec, P):
    """Per point: across the arc (radians from the top) and back along the plate (0 front, 1 back)."""
    name, y0, y1, _ = spec
    g = (P[:, 1] - y0) / (y1 - y0)
    c = np.array([tuple(torso_at(float(y))[0]) for y in np.clip(P[:, 1], TORSO[0].y, TORSO[-1].y)])
    a = np.arctan2(P[:, 0] - c[:, 0], P[:, 2] - c[:, 2])
    return a, g


def facet_plate(o, spec):
    """Cut the plate's top into crystal facets: pyramids in a staggered grid, sharp at their ridges."""
    P = verts(o)
    Nn = normals(o)
    a, g = plate_coords(spec, P)
    rows = spec[3]
    u = a / (2 * ARC) * TEETH * 0.5 * (1.0 if rows > 1 else 1.0)
    v = g * rows * 1.0 + (np.floor(u) % 2) * 0.5 * (rows > 1)
    fct = facet(u, v)
    out = (Nn * (P - np.array([tuple(torso_at(float(y))[0]) for y in np.clip(P[:, 1], TORSO[0].y, TORSO[-1].y)]))).sum(1) > 0
    set_verts(o, P + Nn * (0.004 * fct * out)[:, None])
    return fct


# ---------- the head ----------
def head_rings(nt, rows):
    a = np.linspace(-math.pi, math.pi, nt, endpoint=False)
    X, U_ = np.array((1.0, 0, 0)), np.array(tuple(HUP))
    cs, sn = np.cos(a), np.sin(a)
    out = []
    for i in range(rows):
        s = i / (rows - 1)
        w, t, b = hprof(s, H_W), hprof(s, H_T), hprof(s, H_B)
        c = np.array(tuple(head_axis(s)))
        x = w * np.sign(cs) * np.abs(cs) ** 0.9
        y = np.where(sn > 0, t, b) * np.sign(sn) * np.abs(sn) ** 0.9
        out.append(c + x[:, None] * X + y[:, None] * U_)
    return out


def eye_at(side):
    return head_axis(0.42) + HUP * 0.036 + V(side * 0.066, 0, 0)      # (a bead set deep: about a third of it shows)


def eye_out(side):
    return V(side * 0.82, -0.42, 0.32).normalized()


def cheek_frame(side):
    """The pad's centre, lying on the skin below the eye, and its axes: along the head, up its face, out of the skin."""
    out = eye_out(side)
    along = (HD - out * HD.dot(out)).normalized()
    up = out.cross(along).normalized()
    if up.z < 0:
        up = -up
    centre = eye_at(side) - up * 0.026 + out * 0.015      # 3 cm from the eye's centre: further than the eye and the pad's own thickness, so as it turns up over the eye it can't pass into it
    return centre, along, up, out


CHEEK_BLINK, CHEEK_SQUINT = 1.15, 0.5      # radians the pad turns up round the eye: closed, and a pleased half-close


def cheek_hinge(side):
    """The pad turns on the eye's centre about the head's long axis: a positive turn carries it from below the eye up over its front."""
    c, along, up, out = cheek_frame(side)
    return along      # (measured: about -along the pad sinks into the head)


data_store = {}


def build_head(name, coll):
    rings = head_rings(64, 70)
    o = rings_mesh(name, coll, tuple(P0 - HD * 0.03), rings, tuple(NOSE + HD * 0.01))
    m = Mesh()
    m.bm.from_mesh(o.data)
    bpy.data.objects.remove(o, do_unlink=True)
    # the nose: a soft pink pad on the snout's tip
    m.ball(NOSE + HD * 0.004 + HUP * 0.004, (0.03, 0.016, 0.022), 20, 12)
    o = m.finish(name, coll, recalc=False)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.003, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    # the eye sockets, a little hollow; a brow ridge over each; the crown cut into gem facets from the brows back to the ears
    P = verts(o)
    Nn = normals(o)
    d0 = P - np.array(tuple(P0))
    s = d0 @ np.array(tuple(HD)) / (NOSE - P0).length
    up = d0 @ np.array(tuple(HUP))
    for side in (1, -1):
        e = np.array(tuple(eye_at(side)))
        d = np.linalg.norm(P - e, axis=1)
        P = P - Nn * (0.007 * np.exp(-(d / 0.028) ** 2))[:, None]
        brow = np.exp(-((np.linalg.norm((P - (e + np.array((side * -0.008, 0.004, 0.03)))) / np.array((0.03, 0.03, 0.012)), axis=1)) ** 2))
        P = P + Nn * (0.0045 * brow)[:, None]
    crown = smooth(-0.02, 0.03, up - 0.35 * np.interp(s, H_S, H_T)) * smooth(0.02, 0.08, s) * (1 - smooth(0.46, 0.52, s))
    u = P[:, 0] / 0.042 + 0.5
    v = s * 6 + (np.floor(u) % 2) * 0.5
    P = P + Nn * (0.0022 * facet(u, v) * crown + 0.002 * crown)[:, None]
    set_verts(o, P)
    data_store["crown"] = (u, v)
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def unused_head_shield_point(u, v):
    """The crystal shield on the head: u from the back of the skull to over the eyes, v across."""
    s = 0.04 + 0.42 * u
    c = head_axis(s)
    w = hprof(s, H_W) * (0.8 + 0.12 * math.sin(math.pi * u))
    t = hprof(s, H_T)
    x = (2 * v - 1) * w
    q = x / max(w, 1e-4)
    z = t * math.sqrt(max(0.0, 1 - 0.55 * q * q)) + 0.012
    brow = 0.018 * math.exp(-((u - 0.92) / 0.1) ** 2)      # its front edge stands out over the eyes
    return c + V(x * 1.12, 0, 0) + HUP * (z + brow) - HD * 0.012 * (u > 0.9) * 0


def build_head_shield(name, coll, nu, nv):
    m = Mesh()
    m.sheet(head_shield_point, lambda u, v: 0.012, nu, nv)
    return m.finish(name, coll)


def ear_point(side):
    root = V(side * 0.07, -0.33, 0.31)
    up = V(side * 0.35, 0.15, 0.92).normalized()
    face = V(side * 0.4, -0.9, 0.0)
    face = (face - up * face.dot(up)).normalized()
    across = up.cross(face).normalized()

    def point(u, v):
        w = 2 * v - 1
        half = 0.048 * math.sin(math.pi * min(1.0, 0.12 + u * 0.95)) ** 0.8 + 0.002
        return root + up * 0.13 * u + across * half * w - face * (0.016 * (1 - w * w) - 0.006)
    return point


def build_eyes(name, coll, seg, rings):
    m = Mesh()
    for side in (1, -1):
        m.ball(eye_at(side), (EYE_R, EYE_R, EYE_R), seg, rings)
    return m.finish(name, coll)


def build_cheeks(name, coll, seg, rings):
    """Soft pads lying flat on the skin below each eye, like a lower lid: thin out of the skin, long along the head."""
    m = Mesh()
    for side in (1, -1):
        c, along, up, out = cheek_frame(side)
        M = Matrix.Translation(c) @ Matrix((tuple(along) + (0,), tuple(up) + (0,), tuple(out) + (0,), (0, 0, 0, 1))).transposed() @ Matrix.Diagonal((0.037, 0.021, 0.0085, 1))
        bmesh.ops.create_uvsphere(m.bm, u_segments=seg, v_segments=rings, radius=1.0, matrix=M)
    return m.finish(name, coll)


# ---------- legs, claws, the tail's crystal rings, the crest prisms ----------
def build_claws(name, coll, sides, per, low=False):
    m = Mesh()
    which = []
    for index, (key, side, knots, _) in enumerate(LEGS):
        paw = mir(knots[3], side)
        fore = key[0] == "F"
        count = 3 if fore else 4
        length = 0.07 if fore else 0.035
        for k in range(count):
            x = (k - (count - 1) / 2) * 0.017
            start = paw + V(x, -0.03, 0.004)
            path = catmull([start, start + V(x * 0.3, -length * 0.55, -0.002), start + V(x * 0.5, -length, -0.02)], per)
            before = len(m.bm.verts)
            m.tube(path, lambda f: 0.0085 * (1 - 0.85 * f) + 0.0008, sides=sides)
            which += [key] * (len(m.bm.verts) - before)
    return m.finish(name, coll), which


CRESTS = (("Shield", -0.17, 1.15), ("Band1", -0.055, 0.85), ("Band2", -0.015, 0.85), ("Band3", 0.025, 0.85), ("Band4", 0.065, 0.85), ("Pelvis", 0.18, 1.05))
HUES = ("ff7ab4", "ffc864", "8cf0a0", "78c8ff", "a08cff", "f08cff")


def build_crest(k, coll, sides=6):
    """A small hexagonal prism standing on the plate's crest, leaning back, pointed."""
    plate, y, size = CRESTS[k]
    base = torso_point(y, 0.0, 0.03 + 0.012)
    up = V(0, 0.32, 1).normalized()
    m = Mesh()
    bm = m.bm
    r = 0.017 * size
    h = 0.05 * size
    q = Vector((0, 0, 1)).rotation_difference(up).to_matrix()
    bottom = [bm.verts.new(base - up * 0.02 + q @ V(r * math.cos(TAU * j / sides), r * math.sin(TAU * j / sides), 0)) for j in range(sides)]
    top = [bm.verts.new(base + up * h + q @ V(r * math.cos(TAU * j / sides), r * math.sin(TAU * j / sides), 0)) for j in range(sides)]
    tip = bm.verts.new(base + up * (h + 0.032 * size))
    for j in range(sides):
        j2 = (j + 1) % sides
        bm.faces.new((bottom[j], bottom[j2], top[j2], top[j]))
        bm.faces.new((top[j], top[j2], tip))
    bm.faces.new(list(reversed(bottom)))
    return m.finish(N + "Crest%d_Glow_%s" % (k + 1, HUES[k]), coll, smooth_shade=False)


def build_hi(clay=False):
    pieces, data = {}, {}
    pieces["Skin"] = build_body(N + "SkinHi", HI)
    pieces["Head"] = build_head(N + "HeadHi", HI)
    for key in ("Skin", "Head"):
        data[key + "Base"] = bpy.data.objects.new(N + key + "Base", pieces[key].data.copy())
        HI.objects.link(data[key + "Base"])
        data[key + "Base"].hide_render = True
    pieces["Legs"] = pieces["Skin"]
    for spec in PLATES:
        o = build_plate(spec, N + spec[0] + "Hi", HI, 240, 30 * spec[3] + 10)
        data[spec[0] + "Facets"] = facet_plate(o, spec)
        pieces[spec[0]] = o
    pieces["Eyes"] = build_eyes(N + "EyesHi", HI, 48, 32)
    pieces["Cheeks"] = build_cheeks(N + "CheeksHi", HI, 40, 24)
    pieces["Claws"], _ = build_claws(N + "ClawsHi", HI, 12, 8)
    for side, tag in ((1, "L"), (-1, "R")):
        m = Mesh()
        m.sheet(ear_point(side), lambda u, v: 0.009 * (1 - u) + 0.003, 40, 24)
        pieces["Ear" + tag] = m.finish(N + "Ear" + tag + "Hi", HI)
    glows = {"Crest%d" % (k + 1): build_crest(k, HI) for k in range(len(CRESTS))}
    if not clay:
        paint_all(pieces, data)
    return pieces, glows, data


def worley2(P, f, seed=0):
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    d2 = np.full(len(P), 1e9)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                d = np.sqrt(sum((q[:, k] - c[:, k] - hash01(c[:, 0], c[:, 1], c[:, 2], seed + k + 1)) ** 2 for k in range(3)))
                d2 = np.where(d < d1, d1, np.minimum(d2, d))
                d1 = np.minimum(d1, d)
    return d1, d2


def spectrum(h):
    """A soft rainbow: h in 0..1 round the hues."""
    h = np.asarray(h)[:, None] if np.ndim(h) else np.array([[h]])
    k = (np.array((0.0, 1 / 3, 2 / 3))[None, :] + h) % 1.0
    return 0.5 + 0.5 * np.cos(TAU * k)


def quartz(P, Nn, table, cell_u, cell_v, under):
    """Cut crystal: each tile its own faint tint, its table bright, a spectral sheen along its bevel (the light split), a glint across it, darker in the grooves."""
    tile = np.floor(cell_u) * 7.13 + np.floor(cell_v) * 3.71
    tint = np.sin(tile * 12.9898) * 43758.5453 % 1.0
    tints = np.stack([LILAC, ICE, rgb(248, 206, 230), rgb(214, 244, 222)])
    base = tints[(tint * 4).astype(int) % 4]
    col = mix(QUARTZ, base, 0.45)
    col = mix(col, QUARTZ_D, (1 - smooth(0.0, 0.25, table)) * 0.75)            # down into the grooves
    bevel = smooth(0.0, 0.35, table) * (1 - smooth(0.6, 1.0, table))
    sheen = spectrum(Nn @ np.array((0.6, 0.3, 0.7)) * 1.6 + tint)
    col = mix(col, mix(col, sheen, 0.55), bevel * 0.7)
    fu, fv = cell_u - np.floor(cell_u) - 0.5, cell_v - np.floor(cell_v) - 0.5
    glint = np.exp(-((fu + fv - 0.15) / 0.07) ** 2) * smooth(0.6, 1.0, table)
    col = mix(col, rgb(255, 255, 255), glint * 0.7)
    col = np.where(under[:, None], mix(SKIN_D, QUARTZ_D, 0.4), col)
    rough = np.where(under, 0.7, 0.24 - 0.12 * glint)
    return col, rough


def paint_plate(o, spec):
    P = verts(o)
    Nn = normals(o)
    a, g = plate_coords(spec, P)
    rows = spec[3]
    u = a / (2 * ARC) * TEETH * 0.5
    v = g * rows + (np.floor(u) % 2) * 0.5 * (rows > 1)
    table = facet(u, v)
    c = np.array([tuple(torso_at(float(y))[0]) for y in np.clip(P[:, 1], TORSO[0].y, TORSO[-1].y)])
    under = (Nn * (P - c)).sum(1) < 0
    col, rough = quartz(P, Nn, table, u, v, under)
    paint(o, col, rough)


def pebbles(P, f, seed):
    d1, d2 = worley2(P, f, seed)
    return 1 - smooth(0.0, 0.1, d2 - d1)


def paint_skin(o):
    P = verts(o)
    Nn = normals(o)
    peb = pebbles(P, 70.0, 3)
    col = mix(SKIN, SKIN_D, peb * 0.45)
    belly = smooth(0.0, -0.7, Nn[:, 2]) * smooth(0.22, 0.1, P[:, 2]) * (np.abs(P[:, 1]) < 0.28)
    col = mix(col, BELLY, belly * 0.7)
    feet = smooth(0.06, 0.02, P[:, 2])
    col = mix(col, SKIN_D, feet * 0.6)
    # the tail: rings of small crystal tiles
    f, d = nearest_on(TAIL, P)
    on_tail = (d < 0.07) & (P[:, 1] > 0.3)
    a = np.arctan2(P[:, 0], P[:, 2] - 0.1)
    u, v = a / math.pi * 5, f * 9
    tcol, trough = quartz(P, Nn, facet(u, v), u, v, np.zeros(len(P), bool))
    col = np.where(on_tail[:, None], mix(tcol, SKIN, 0.2), col)
    rough = np.where(on_tail, trough, 0.82)
    set_verts(o, P + Nn * np.where(on_tail, 0.0025 * facet(u, v), 0.0012 * peb)[:, None])
    paint(o, col, rough)


def paint_head(o):
    P = verts(o)
    Nn = normals(o)
    d0 = P - np.array(tuple(P0))
    s = d0 @ np.array(tuple(HD)) / (NOSE - P0).length
    up = d0 @ np.array(tuple(HUP))
    peb = pebbles(P, 90.0, 5)
    col = mix(SKIN, SKIN_D, peb * 0.35)
    col = mix(col, mix(SKIN, PINK, 0.35), smooth(0.6, 0.95, s))
    col = mix(col, BELLY, smooth(0.0, -0.6, up / 0.05) * 0.5)
    crown = smooth(-0.02, 0.03, up - 0.35 * np.interp(s, H_S, H_T)) * smooth(0.02, 0.08, s) * (1 - smooth(0.46, 0.52, s))
    u, v = data_store["crown"]
    if len(u) != len(P):
        u = P[:, 0] / 0.042 + 0.5
        v = s * 6 + (np.floor(u) % 2) * 0.5
    qcol, qrough = quartz(P, Nn, facet(u, v), u, v, np.zeros(len(P), bool))
    col = mix(col, qcol, crown)
    nose = np.linalg.norm(P - np.array(tuple(NOSE + HD * 0.004 + HUP * 0.004)), axis=1) < 0.034
    col = np.where((nose & (s > 0.93))[:, None], mix(PINK, SKIN_D, 0.25), col)
    # a dark rim round each eye, and the mouth's small line
    for side in (1, -1):
        d = np.linalg.norm(P - np.array(tuple(eye_at(side))), axis=1)
        col = mix(col, mix(SKIN_D, BEAD, 0.4), np.exp(-((d - EYE_R * 1.05) / 0.004) ** 2) * 0.6)
    mouth = np.exp(-((up + 0.62 * np.interp(s, H_S, H_B)) / 0.004) ** 2) * smooth(0.55, 0.65, s) * (1 - smooth(0.95, 1.0, s))
    col = mix(col, SKIN_D, mouth * 0.8)
    rough = 0.82 * (1 - crown) + qrough * crown
    paint(o, col, rough)


def paint_eyes(o):
    P = verts(o)
    Nn = normals(o)
    col = np.tile(BEAD, (len(P), 1))
    col = mix(col, rgb(70, 40, 96), smooth(0.2, 0.9, Nn @ np.array((0, -0.4, 0.9))) * 0.35)
    paint(o, col, 0.06)


def paint_all(pieces, data):
    paint_skin(pieces["Skin"])
    paint_head(pieces["Head"])
    for spec in PLATES:
        paint_plate(pieces[spec[0]], spec)
    paint_eyes(pieces["Eyes"])
    plain(pieces["Cheeks"], mix(SKIN, BELLY, 0.18), 0.8)
    P = verts(pieces["Claws"])
    paint(pieces["Claws"], mix(CLAW, rgb(150, 120, 160), smooth(0.0, 0.05, P[:, 2])), 0.3)
    for side, tag in ((1, "L"), (-1, "R")):
        o = pieces["Ear" + tag]
        P, Nn = verts(o), normals(o)
        face = np.array(tuple(V(side * 0.4, -0.9, 0.0).normalized()))
        inner = smooth(-0.05, 0.3, Nn @ face)
        paint(o, mix(SKIN_D, PINK, inner * 0.8), 0.75)


def show_glows(glows):
    for k, o in enumerate(glows.values()):
        m = bpy.data.materials.new(o.name)
        g = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        hexa = HUES[k]
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (int(hexa[0:2], 16) / 255, int(hexa[2:4], 16) / 255, int(hexa[4:6], 16) / 255, 1)
        g.inputs["Emission Strength"].default_value = 1.4
        o.data.materials.append(m)
        o.visible_shadow = False


VIEWS = [(0, -1, 0.1), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.62, 0.62, 0.4), (-0.62, -0.72, 0.28), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, 0.02, 0.2)
FACE_AT = (0, -0.45, 0.27)
EXTRA = [(0, -1, 0.05, 0.75, FACE_AT), (0.62, -0.78, 0.12, 0.75, FACE_AT), (1, -0.05, 0.05, 0.85, FACE_AT), (0.3, -0.85, 0.45, 0.85, FACE_AT), (0.4, -0.9, 0.1, 0.36, (0.07, -0.42, 0.32)), (0.8, 0.3, 0.6, 1.4, (0, 0.05, 0.3)), (0.75, -0.55, -0.1, 1.1, (0.1, -0.1, 0.06))]


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
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=2.8, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
TEXELS = {"Head": 2.0, "Eyes": 1.6, "Cheeks": 1.4, "Claws": 0.9, "EarL": 1.2, "EarR": 1.2, "Shield": 1.4, "Band1": 1.4, "Band2": 1.4, "Band3": 1.4, "Band4": 1.4, "Pelvis": 1.4}
LOW_PLATE = {"Shield": (16, 10), "Band1": (16, 2), "Band2": (16, 2), "Band3": (16, 2), "Band4": (16, 2), "Pelvis": (16, 10)}
META = {}


def build_low(data):
    skin = decimated(data["SkinBase"], N + "SkinLow", 2600)
    head = decimated(data["HeadBase"], N + "HeadLow", 1100)
    for o in (skin, head):
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    print("SKIN decimated gap", round(surface_gap(skin, tree_of(data["SkinBase"])), 4), "HEAD gap", round(surface_gap(head, tree_of(data["HeadBase"])), 4), flush=True)
    lows = {"Skin": skin, "Head": head}
    for spec in PLATES:
        cols, rows = LOW_PLATE[spec[0]]
        lows[spec[0]] = build_plate(spec, N + spec[0] + "Low", GAME, cols, rows)
    lows["Eyes"] = build_eyes(N + "EyesLow", GAME, 12, 8)
    lows["Cheeks"] = build_cheeks(N + "CheeksLow", GAME, 10, 6)
    lows["Claws"], META["Claws"] = build_claws(N + "ClawsLow", GAME, 4, 2, low=True)
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Ear" + tag] = low_sheet(ear_point(side), lambda u, v: 0.009 * (1 - u) + 0.003, 5, 3, N + "Ear" + tag + "Low")
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
# the spine bends at the plates' joins; each plate rides one bone, rigid, and so does the skin under it, so nothing can push through the armour as it rolls up
JOINTS = (("Front", -0.06), ("Mid", 0.02), ("Back", 0.06), ("Pelvis", 0.1))
PLATE_BONE = {"Shield": "Front", "Band1": "Body", "Band2": "Body", "Band3": "Mid", "Band4": "Back", "Pelvis": "Pelvis"}
TAIL_F = (0.0, 0.35, 0.7)
TAIL_BONES = ("Tail1", "Tail2", "Tail3")


def path_at(path, f):
    return path[min(len(path) - 1, int(round(f * (len(path) - 1))))].copy()


def skeleton():
    # the hinges sit just under the armour's crest: there the plates hardly part as it rolls up, and lower down they slide over each other, the front one outside
    hinge_z = 0.4
    bones = [("Root", V(0, 0, 0), None), ("Body", V(0, -0.02, 0.26), "Root"), ("Front", V(0, -0.06, hinge_z), "Body"), ("Neck", V(0, -0.24, 0.255), "Front"), ("Head", V(0, -0.3, 0.26), "Neck"),
             ("Mid", V(0, 0.02, hinge_z), "Body"), ("Back", V(0, 0.06, hinge_z), "Mid"), ("Pelvis", V(0, 0.1, hinge_z), "Back")]
    parent = "Pelvis"
    for name, f in zip(TAIL_BONES, TAIL_F):
        bones.append((name, path_at(TAIL, f), parent))
        parent = name
    for side, tag in ((1, "L"), (-1, "R")):
        bones += [("Ear" + tag, V(side * 0.07, -0.33, 0.33), "Head"), ("Cheek" + tag, eye_at(side), "Head")]
    for key, side, knots, _ in LEGS:
        top = "Front" if key[0] == "F" else "Pelvis"
        bones += [("Leg" + key + "1", mir(knots[0], side), top), ("Leg" + key + "2", mir(knots[1], side), "Leg" + key + "1"), ("Paw" + key, mir(knots[2], side), "Leg" + key + "2")]
    return armature(bones)


def spine_weight(y):
    """Along the body: each plate's stretch to its plate's bone, shading across the short join under each overlap."""
    cuts = ((-0.07, "Front", "Body"), (0.015, "Body", "Mid"), (0.055, "Mid", "Back"), (0.095, "Back", "Pelvis"))
    if y < -0.235:
        t = float(smooth(-0.27, -0.235, y))
        return {"Neck": 1 - t, "Front": t}
    for k, (cut, a, b) in enumerate(cuts):
        if y < cut - 0.012:
            return {a: 1.0}
        if y < cut + 0.012:
            t = float(smooth(cut - 0.012, cut + 0.012, y))
            return {a: 1 - t, b: t}
    return {"Pelvis": 1.0}


def leg_share(key, side, p):
    """How much of a leg this point is, and how far down it: by distance to the leg's line."""
    _, _, knots, radii = next(l for l in LEGS if l[0] == key)
    path = catmull([mir(q, side) for q in knots[:3]], 6) + [mir(knots[3], side)]
    f, d = nearest_on(path, np.array([tuple(p)]))
    return float(f[0]), float(d[0])


def skin_weights(o):
    P = verts(o)
    tf, td = nearest_on(TAIL, P)
    out = []
    for i, p in enumerate(P):
        w = spine_weight(float(p[1]))
        # the tail
        if p[1] > 0.29 and td[i] < 0.075:
            t = float(smooth(0.29, 0.34, p[1]))
            tw = chain_weight(TAIL_BONES, TAIL_F, float(tf[i]))
            w = {k: v * (1 - t) for k, v in w.items()}
            for k, v in tw.items():
                w[k] = w.get(k, 0) + v * t
        # the legs: below the body's underside, and near a leg's line
        if p[2] < 0.205:
            best = None
            for key, side, knots, radii in LEGS:
                if (p[0] * side) <= 0.02:
                    continue
                f, d = leg_share(key, side, p)
                if d < 0.085 and (best is None or d < best[1]):
                    best = (key, d, f)
            if best:
                key, d, f = best
                t = float(smooth(0.205, 0.15, p[2]))
                if f < 0.42:
                    lw = {"Leg%s1" % key: 1.0}
                elif f < 0.55:
                    s_ = float(smooth(0.42, 0.55, f))
                    lw = {"Leg%s1" % key: 1 - s_, "Leg%s2" % key: s_}
                elif f < 0.8:
                    lw = {"Leg%s2" % key: 1.0}
                else:
                    s_ = float(smooth(0.8, 0.9, f))
                    lw = {"Leg%s2" % key: 1 - s_, "Paw%s" % key: s_}
                w = {k: v * (1 - t) for k, v in w.items()}
                for k, v in lw.items():
                    w[k] = w.get(k, 0) + v * t
        total = sum(w.values())
        w = {k: v / total for k, v in w.items() if v > 0.005}
        # keep the three strongest
        top = sorted(w.items(), key=lambda kv: -kv[1])[:3]
        total = sum(v for _, v in top)
        out.append({k: v / total for k, v in top})
    weigh(o, out)


def bind_all(lows, rig, glows):
    skin_weights(lows["Skin"])
    for key in ("Head", "Eyes"):
        rigid(lows[key], "Head")
    weigh(lows["Cheeks"], [{"CheekL" if p[0] > 0 else "CheekR": 1.0} for p in verts(lows["Cheeks"])])
    for tag in ("L", "R"):
        rigid(lows["Ear" + tag], "Ear" + tag)
    for spec in PLATES:
        rigid(lows[spec[0]], PLATE_BONE[spec[0]])
    weigh(lows["Claws"], [{"Paw" + k: 1.0} for k in META["Claws"]])
    for k, (plate, _, _) in enumerate(CRESTS):
        rigid(glows["Crest%d" % (k + 1)], PLATE_BONE[plate])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animatePrismArmadillo uses. +X: what points forward lifts (a head), what points back drops (a tail), a hanging limb's far end swings forward
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), move)


def ball(k=1.0):
    """Rolled right up: the front and back of the shell meet round it, the head and tail tucked inside, the legs folded in."""
    out = {"Front": game_turn(-0.46 * k, 0, 0), "Neck": game_turn(-1.25 * k, 0, 0), "Head": game_turn(-1.1 * k, 0, 0),
           "Mid": game_turn(0.3 * k, 0, 0), "Back": game_turn(0.3 * k, 0, 0), "Pelvis": game_turn(0.48 * k, 0, 0),
           "Tail1": game_turn(0.9 * k, 0, 0), "Tail2": game_turn(0.8 * k, 0, 0), "Tail3": game_turn(0.7 * k, 0, 0),
           "Body": game_turn(0, 0, 0, (0, 0, -0.03 * k)), "EarL": game_turn(0.7 * k, 0, 0), "EarR": game_turn(0.7 * k, 0, 0)}
    for key in ("FL", "FR"):
        out["Leg%s1" % key] = game_turn(-0.9 * k, 0, 0)
        out["Leg%s2" % key] = game_turn(1.4 * k, 0, 0)
    for key in ("BL", "BR"):
        out["Leg%s1" % key] = game_turn(0.9 * k, 0, 0)
        out["Leg%s2" % key] = game_turn(-1.2 * k, 0, 0)
    return out


def pose_library():
    up = cheek_frame(1)[2]
    cheeks = lambda a: {"CheekL": (tuple(cheek_hinge(1)), math.degrees(a), (0, 0, 0)), "CheekR": (tuple(cheek_hinge(-1)), math.degrees(a), (0, 0, 0))}
    return {
        "Squint": cheeks(CHEEK_SQUINT), "Blink": cheeks(CHEEK_BLINK),
        "Half": ball(0.5), "Ball": ball(1.0),
        "Rear": {"Front": game_turn(0.75, 0, 0), "Neck": game_turn(-0.35, 0, 0), "Head": game_turn(-0.2, 0, 0), "LegFL1": game_turn(-0.4, 0, 0), "LegFR1": game_turn(-0.4, 0, 0), "Body": game_turn(0.25, 0, 0, (0, 0, 0.04)), "Tail1": game_turn(-0.3, 0, 0)},
        "Step": {"LegFL1": game_turn(0.5, 0, 0), "LegFR1": game_turn(-0.4, 0, 0), "LegBL1": game_turn(-0.4, 0, 0), "LegBR1": game_turn(0.5, 0, 0), "LegFL2": game_turn(-0.5, 0, 0), "LegBR2": game_turn(0.5, 0, 0)},
        "Turn": {"Neck": game_turn(0, 0.45, 0), "Head": game_turn(0.1, 0.5, 0.2), "EarL": game_turn(-0.3, 0, -0.3)},
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
    unwrap(lows, [(None, 1.0)], {}, shape="CONCAVE", angle=62, texels=TEXELS, margin=0.006)
    plate_reach = {spec[0]: (0.007, 0.016) for spec in PLATES}
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.75, 0.6, 0.64, 1), far=("Skin", "Head"), reach=(0.008, 0.02), far_reach=(0.012, 0.035),
             reaches={**plate_reach, "Eyes": (0.005, 0.012), "Cheeks": (0.005, 0.012), "Claws": (0.006, 0.015)})
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for o in glows.values():
        HI.objects.unlink(o)
        GAME.objects.link(o)
    triangulate(glows)
    rig = skeleton()
    body = bind_all(lows, rig, glows)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 2) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    for side, tag in ((1, "L"), (-1, "R")):
        c, along, up, out = cheek_frame(side)
        h = cheek_hinge(side)
        print("CHEEK", tag, "hinge in the game's axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    pose(rig, {})
    bpy.context.scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=2.8, size=640)
    lib = pose_library()
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    close = (0.35, -0.92, 0.1, 0.4, (0.07, -0.42, 0.31))
    whole = (0.72, -0.62, 0.18, 2.8, VIEW_AT)
    for name, view in (("Squint", close), ("Blink", close), ("Half", whole), ("Ball", whole), ("Ball", (1, 0.05, 0.1, 1.6, (0, 0, 0.25))), ("Ball", (0, -1, 0.2, 1.6, (0, 0, 0.25))), ("Ball", (0.2, 0.3, -0.9, 1.6, (0, 0, 0.2))), ("Rear", whole), ("Step", whole), ("Turn", (0.6, -0.8, 0.2, 1.1, FACE_AT))):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name + str(abs(hash(view)) % 1000)), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.28, 2.8, VIEW_AT))
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)
