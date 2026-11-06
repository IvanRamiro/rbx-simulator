"""The Lantern Warden (Epic, Light; Bloomwood Egg): "A keeper of lost paths that carries a light nobody lit. Follow it and you arrive, though not always where you meant."

A stooped wayfarer spirit: three tiers of old straw rain-cape, gone to moss at the shoulders, a tilted conical hat with blossom growing on it, two thin legs with root toes. A gnarled crook grows out of its back, arches over the hat, and hangs a
bronze paper lantern in front of its face. Its face is like no other pet's: a pale carved mask with two upward crescents cut right through, and behind them, small ember pupils that slide about, seen only through the slits. It blinks by drawing them back into the dark.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/lantern_warden.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, toes on z = 0. The maps go to assets/pets/BloomwoodEgg/.

What touches what: the mantle's top is buried in the hood, each tier's top inside the tier above; the hood sits on the core; the mask is sunk in the hood's front, the hat on the hood's crown; sleeves come out through the middle tier; legs are sunk in the core's underside and hidden by the low tier;
the crook's root is buried in the back of the mantle; the chain's first link hangs through the crook's tip and the lantern's ring through the last link.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.geometry import delaunay_2d_cdt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "all"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "LanternWarden"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "BloomwoodEgg")

# ---------- colours ----------
STRAW, STRAW_D, STRAW_PALE = rgb(170, 134, 74), rgb(92, 70, 40), rgb(214, 186, 124)
MOSS, MOSS_D = rgb(86, 116, 56), rgb(44, 64, 36)
BARK, BARK_D = rgb(74, 54, 42), rgb(36, 26, 22)
IVORY, IVORY_D = rgb(236, 226, 204), rgb(186, 170, 142)
CLOTH, CLOTH_D = rgb(46, 52, 48), rgb(22, 24, 24)
BRONZE, VERDIGRIS = rgb(126, 88, 48), rgb(84, 142, 118)
BLOSSOM, BLOSSOM_D, EMBER, ROUGE = rgb(255, 128, 186), rgb(214, 62, 130), rgb(255, 176, 60), rgb(206, 84, 84)

# ---------- the frame of it ----------
def lean(z):
    """It stoops: the higher, the further forward."""
    return -0.13 * (z - 0.6)


TIERS = {   # z top, z hem, radius top, radius hem, teeth, turn of the teeth, depth of the teeth
    "Mantle": (1.40, 1.10, 0.09, 0.31, 20, 0.0, 0.07),
    "Mid": (1.20, 0.85, 0.20, 0.36, 24, 0.5, 0.075),
    "Low": (0.98, 0.56, 0.25, 0.40, 28, 0.25, 0.08),
}
FLAT_Y = 0.86
HOOD = V(0, lean(1.45) + 0.02, 1.45)
MASK_Y, MASK_Z, MASK_W, MASK_H = HOOD.y - 0.105, 1.455, 0.122, 0.158
HAT_C = V(0, HOOD.y + 0.03, 1.575)
HAT_UP = V(0, 0.24, 0.97).normalized()
HAT_R, HAT_H = 0.44, 0.33
TIP_X, TIP_Y = 0.40, -0.56      # out to its left: from in front the lantern must never hide the face
CROOK = catmull([V(0, 0.16, 1.14), V(0, 0.42, 1.36), V(0.02, 0.53, 1.7), V(0.01, 0.38, 2.06), V(0.1, -0.06, 2.25), V(0.27, -0.42, 2.13), V(TIP_X - 0.01, TIP_Y, 1.97), V(TIP_X, TIP_Y, 1.87)], 8)
LANTERN_AT = V(TIP_X, TIP_Y, 1.50)
LANTERN_R, LANTERN_H = 0.1, 0.25
LEG = [V(0.085, 0.0, 0.72), V(0.105, -0.13, 0.47), V(0.105, 0.06, 0.215), V(0.105, -0.03, 0.04)]
LEG_R = (0.05, 0.034, 0.023, 0.026)
ARM = [V(0.15, -0.06, 1.2), V(0.205, -0.25, 1.05), V(0.115, -0.42, 1.03), V(0.07, -0.47, 1.03)]
ARM_R = (0.05, 0.052, 0.062, 0.03)


def along_radii(radii, f):
    return float(np.interp(f, np.linspace(0, 1, len(radii)), radii))


def hash_of(k):
    return math.sin(k * 12.9898) * 43758.5453 % 1.0


def from_arrays(name, coll, verts_np, faces):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts_np.tolist(), [], faces)
    me.update()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


# ---------- the cape: three tiers, each a thin closed shell with a toothed hem ----------
def tier_surface(key, cols, rows, inset=0.0):
    z0, z1, r0, r1, teeth, turn, depth = TIERS[key]
    a = TAU * (np.arange(cols) / cols + turn / teeth)
    # each tooth is two columns' worth at the least: a tip and a notch
    phase = np.arange(cols) / cols * teeth
    tri = np.abs(((phase + 0.5) % 1.0) * 2 - 1)            # 0 at a notch, 1 at a tip
    long = 0.62 + 0.76 * (np.sin(np.floor(phase) * 12.9898 + z0 * 50) * 43758.5453 % 1.0)      # (hand-laid: no two the same)
    u = (np.arange(rows + 1) / rows)[:, None]
    z = z0 + (z1 - z0) * u - depth * (tri * long - 0.5) * u ** 4
    r = r0 + (r1 - r0) * u ** 0.8 - inset
    ya = np.cos(a)[None, :]
    x = r * np.sin(a)[None, :]
    y = r * -ya * FLAT_Y + (-0.13 * (z - 0.6))
    return np.stack((x, y, z), axis=2), u[:, 0], a


def build_tier(key, name, coll, cols, rows):
    """Outer surface, inner surface, joined all round the hem and the top."""
    outer, us, a = tier_surface(key, cols, rows)
    inner, _, _ = tier_surface(key, cols, rows, inset=0.012)
    v = np.concatenate((outer.reshape(-1, 3), inner.reshape(-1, 3)))
    W = rows + 1
    n = W * cols

    def oid(i, j):
        return i * cols + (j % cols)
    faces = []
    for i in range(rows):
        for j in range(cols):
            faces.append((oid(i, j), oid(i, j + 1), oid(i + 1, j + 1), oid(i + 1, j)))
            faces.append((n + oid(i, j), n + oid(i + 1, j), n + oid(i + 1, j + 1), n + oid(i, j + 1)))
    for j in range(cols):
        faces.append((oid(rows, j), oid(rows, j + 1), n + oid(rows, j + 1), n + oid(rows, j)))
        faces.append((oid(0, j), n + oid(0, j), n + oid(0, j + 1), oid(0, j + 1)))
    o = from_arrays(name, coll, v, faces)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- the hat ----------
def hat_frame():
    side = V(1, 0, 0)
    fwd = HAT_UP.cross(side).normalized()
    if fwd.y > 0:
        fwd = -fwd
    return side, fwd


def build_hat(name, coll, cols, rows, under, frayed=True):
    """A shallow cone, slightly concave, its rim frayed. Top surface and a dark underside, closed."""
    side, fwd = hat_frame()
    S_, F_, U_, C_ = (np.array(tuple(q)) for q in (side, fwd, HAT_UP, HAT_C))
    a = TAU * np.arange(cols) / cols
    fray = 1 + 0.014 * np.sin(a * 37 + np.sin(a * 11) * 2) + 0.009 * np.sin(a * 91) if frayed else np.ones(cols)
    pts = []
    for i in range(1, rows + 1):
        t = i / rows
        h = HAT_H * (1 - t) ** 1.28
        r = HAT_R * t * (1 + (fray - 1) * t ** 6)
        pts.append(C_ + (np.outer(np.cos(a) * r, S_) + np.outer(np.sin(a) * r, F_)) + U_ * h)
    for i in range(1, under + 1):
        t = 1 - i / (under + 1) * 0.86
        h = 0.085 * (1 - t) ** 1.0 + 0.004 * (1 - (1 - t))
        r = HAT_R * t * (1 + (fray - 1) * t ** 6) - 0.002
        pts.append(C_ + (np.outer(np.cos(a) * r, S_) + np.outer(np.sin(a) * r, F_)) + U_ * (h - 0.012))
    grid = np.array(pts)
    total = len(pts)
    v = grid.reshape(-1, 3)
    faces = []
    for i in range(total - 1):
        for j in range(cols):
            j2 = (j + 1) % cols
            faces.append((i * cols + j, (i + 1) * cols + j, (i + 1) * cols + j2, i * cols + j2))
    tip = len(v)
    bottom = tip + 1
    v = np.concatenate((v, [C_ + U_ * (HAT_H + 0.002)], [C_ + U_ * (0.085 * 0.86 - 0.012 + 0.012)]))
    for j in range(cols):
        j2 = (j + 1) % cols
        faces.append((tip, j, j2))
        faces.append((bottom, (total - 1) * cols + j2, (total - 1) * cols + j))
    o = from_arrays(name, coll, v, faces)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def hat_point(a, t, lift=0.0):
    side, fwd = hat_frame()
    h = HAT_H * (1 - t) ** 1.28
    return HAT_C + side * math.cos(a) * HAT_R * t + fwd * math.sin(a) * HAT_R * t + HAT_UP * (h + lift)


# ---------- the mask: a height field with two crescents cut through it ----------
def mask_half_width(z):
    q = (np.asarray(z) - MASK_Z) / MASK_H
    return MASK_W * np.sqrt(np.clip(1 - q ** 2, 0, 1)) * (1 - 0.2 * np.clip(-q, 0, 1) ** 1.6)


def mask_y(x, z):
    """Forward of the mask at (x, z): dome, brow, a long thin nose and the suggestion of a chin."""
    x, z = np.asarray(x, float), np.asarray(z, float)
    q, p = x / MASK_W, (z - MASK_Z) / MASK_H
    dome = 0.072 * np.clip(1 - q ** 2 - 0.5 * p ** 2, -1, 1)
    nose = 0.022 * np.exp(-(x / 0.017) ** 2) * np.exp(-((p + 0.12) / 0.34) ** 2)
    chin = 0.007 * np.exp(-((p + 0.72) / 0.14) ** 2 - (q / 0.34) ** 2)
    return MASK_Y - dome - nose - chin


EYE_X, EYE_Z, EYE_A, EYE_B = 0.056, MASK_Z + 0.022, 0.046, 0.024
EYE_DEPTH = 0.022


def crescent(side, n):
    """A closed loop in (x, z): an upward arc: flat-bottomed, like an eye closed in a smile: pointed at both ends."""
    out = []
    for k in range(n):
        th = TAU * k / n
        t = math.cos(th)
        arch = EYE_B * (1 - t * t)
        s = math.sin(th)
        h = arch * (1.0 if s >= 0 else 0.34) * (1 if s >= 0 else 1)
        z = EYE_Z + (h if s >= 0 else h) - 0.0 * s
        out.append((side * EYE_X + EYE_A * t, z))
    return out


def in_crescent(side, x, z):
    t = (np.asarray(x) - side * EYE_X) / EYE_A
    arch = EYE_B * np.clip(1 - t * t, 0, 1)
    return (np.abs(t) < 1) & (z < EYE_Z + arch) & (z > EYE_Z + 0.34 * arch)


def build_mask(name, coll, step, n_outline, n_eye, back_rings):
    """The mask's face, triangulated round the crescents so each slit is a clean edge, with a wall and a dark floor behind it, and a plain back."""
    outline = []
    for k in range(n_outline):
        th = TAU * k / n_outline
        z = MASK_Z + MASK_H * math.sin(th)
        outline.append((MASK_W * math.cos(th) * (1 - 0.2 * max(0.0, -math.sin(th)) ** 1.6), z))
    pts = list(outline)
    edges = [(k, (k + 1) % n_outline) for k in range(n_outline)]
    loops = [list(range(n_outline))]
    eye_rings = {}
    for side in (1, -1):
        ring = crescent(side, n_eye)
        start = len(pts)
        pts += ring
        edges += [(start + k, start + (k + 1) % n_eye) for k in range(n_eye)]
        eye_rings[side] = list(range(start, start + n_eye))
        loops.append(list(range(start, start + n_eye)))
    xs = np.arange(-MASK_W, MASK_W + step, step)
    zs = np.arange(MASK_Z - MASK_H, MASK_Z + MASK_H + step, step)
    keep = step * 0.62
    for j, z in enumerate(zs):
        w = float(mask_half_width(z))
        for x in xs + (0.5 * step if j % 2 else 0.0):
            if abs(x) > w - keep:
                continue
            clear = True
            for side in (1, -1):
                t = (x - side * EYE_X) / EYE_A
                if abs(t) < 1 + keep / EYE_A and EYE_Z - keep < z < EYE_Z + EYE_B * max(0.0, 1 - min(1.0, t * t)) + keep:
                    clear = False
            if clear:
                pts.append((float(x), float(z)))
    vs, es, fs, ov, oe, of = delaunay_2d_cdt([Vector(p) for p in pts], edges, loops, 2, 1e-6)
    # verts may be renumbered: find each eye's ring again by position
    vxz = np.array([(p[0], p[1]) for p in vs])
    front = np.column_stack((vxz[:, 0], mask_y(vxz[:, 0], vxz[:, 1]), vxz[:, 1]))
    bm = bmesh.new()
    fv = [bm.verts.new(tuple(p)) for p in front]
    for f in fs:
        try:
            bm.faces.new([fv[i] for i in f])
        except ValueError:
            pass
    bm.verts.ensure_lookup_table()

    def nearest(p):
        return int(np.argmin(((vxz - np.array(p)) ** 2).sum(1)))
    # the slits: a wall going straight back, and a floor
    for side in (1, -1):
        ring = [fv[nearest(p)] for p in crescent(side, n_eye)]
        depth = EYE_DEPTH * (1 + 0.0 * side)
        back = [bm.verts.new((v.co.x, v.co.y + depth, v.co.z)) for v in ring]
        for k in range(n_eye):
            k2 = (k + 1) % n_eye
            bm.faces.new((ring[k], ring[k2], back[k2], back[k]))
        hub = bm.verts.new((side * EYE_X, sum(v.co.y for v in back) / n_eye + 0.004, EYE_Z + 0.34 * EYE_B * 1.8))
        for k in range(n_eye):
            bm.faces.new((back[k], back[(k + 1) % n_eye], hub))
    # the back: a shallow cap inside the hood
    rim = sorted([v for v in fv if nearest((v.co.x, v.co.z)) < 1e9 and _on_outline(v, outline)], key=lambda v: math.atan2(v.co.z - MASK_Z, v.co.x))
    last = rim
    for r in range(1, back_rings + 1):
        k = 1 - r / (back_rings + 1)
        ring = [bm.verts.new((v.co.x * k, v.co.y + 0.05 * math.sin(r / (back_rings + 1) * math.pi / 2), MASK_Z + (v.co.z - MASK_Z) * k)) for v in rim]
        for i in range(len(rim)):
            i2 = (i + 1) % len(rim)
            bm.faces.new((last[i], last[i2], ring[i2], ring[i]))
        last = ring
    hub = bm.verts.new((0, MASK_Y + 0.05, MASK_Z))
    for i in range(len(rim)):
        bm.faces.new((last[i], last[(i + 1) % len(rim)], hub))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def _on_outline(v, outline):
    return min((v.co.x - p[0]) ** 2 + (v.co.z - p[1]) ** 2 for p in outline) < 1e-9


PUPIL_R = 0.0115
EYE_TURN = 0.1      # the pupils' pivot is this far inside the mask: about the radius of its curve, so a glance slides along behind it


def eye_frame(side):
    """Where a pupil sits behind its slit, the way it faces (out of the mask), the way it slides, and the pivot it turns on."""
    x, z = side * EYE_X, EYE_Z + 0.009
    slope = 2 * 0.072 * EYE_X / MASK_W ** 2
    n = V(side * slope, -1, 0).normalized()
    across = V(0, 0, 1).cross(n).normalized()
    surface = V(x, float(mask_y(x, z)), z)
    return surface - n * (EYE_DEPTH * 0.72), n, across, surface - n * EYE_TURN


def disc(bm, c, n, across, r_u, r_v, sides, u0=0.0, v0=0.0):
    up = V(0, 0, 1)
    hub = bm.verts.new(c + across * u0 + up * v0)
    ring = [bm.verts.new(c + across * (u0 + r_u * math.cos(TAU * k / sides)) + up * (v0 + r_v * math.sin(TAU * k / sides))) for k in range(sides)]
    fs = [bm.faces.new((hub, ring[k], ring[(k + 1) % sides])) for k in range(sides)]
    for f in fs:
        f.normal_update()
        if f.normal.dot(n) < 0:
            f.normal_flip()


def build_pupils(name, coll, sides):
    """Small discs just behind the slits. The mask hides what isn't in line with one, so they only ever show through it."""
    m = Mesh()
    for side in (1, -1):
        c, n, across, _ = eye_frame(side)
        disc(m.bm, c, n, across, PUPIL_R, PUPIL_R, sides)
    return m.finish(name, coll, recalc=False)


def build_glints(coll, sides):
    m = Mesh()
    for side in (1, -1):
        c, n, across, _ = eye_frame(side)
        disc(m.bm, c + n * 0.0016, n, across, 0.0036, 0.0036, sides, -0.003, 0.0035)
    return m.finish(N + "Glints_Glow_ffe6b0", coll, smooth_shade=False, recalc=False)


# ---------- the body under it all ----------
def build_core(name, coll, sides, voxel=None):
    m = Mesh()
    path = catmull([V(0, lean(0.63), 0.63), V(0, lean(0.7), 0.7), V(0, lean(0.9), 0.9), V(0, lean(1.2), 1.2), V(0, lean(1.4), 1.4)], 5)
    m.tube(path, lambda f: float(np.interp(f, (0, 0.14, 0.3, 1), (0.31, 0.3, 0.24, 0.08))), sides=sides, flat=1.0, plane=V(1, 0, 0))
    m.ball(HOOD + V(0, 0.005, 0.03), (0.135, 0.128, 0.19), sides * 2, sides)      # (its crown rises into the hat, and carries it)
    o = m.finish(name, coll, recalc=False)
    if voxel:
        apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": voxel, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 10})])
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- legs with root toes ----------
TOES = ((0.0, -1.0, 0.13), (0.62, -0.78, 0.115), (-0.62, -0.78, 0.115), (0.0, 1.0, 0.085))


def toe_path(side, tx, ty, length):
    a = mir(LEG[3], side)
    d = V(tx * side, ty, 0).normalized()
    return catmull([a + d * 0.018 + V(0, 0, 0.004 + 0.004 * abs(tx)), a + d * length * 0.5 + V(0, 0, 0.0), a + d * length + V(tx * side * 0.012, 0, -0.034)], 4)


def toe_radius(f):
    return 0.024 - 0.018 * f


def build_legs_hi(name, coll):
    m = Mesh()
    for side in (1, -1):
        path = catmull([mir(p, side) for p in LEG], 14)
        m.tube(path, lambda f: along_radii(LEG_R, f), sides=20)
        m.ball(mir(LEG[1], side), (0.038, 0.04, 0.04), 16, 12)
        m.ball(mir(LEG[2], side), (0.029, 0.03, 0.032), 16, 12)
        m.ball(mir(LEG[3], side), (0.032, 0.036, 0.024), 16, 12)
        for tx, ty, length in TOES:
            m.tube(toe_path(side, tx, ty, length), toe_radius, sides=12)
        # cloth wrappings round the shin
        for f, r in ((0.5, 0.008), (0.545, 0.008), (0.59, 0.007), (0.635, 0.007)):
            c = path[int(f * (len(path) - 1))]
            tan = (path[int(f * (len(path) - 1)) + 1] - c).normalized()
            q = Vector((0, 0, 1)).rotation_difference(tan)
            for k in range(1):
                bmesh.ops.create_cone(m.bm, cap_ends=True, segments=20, radius1=along_radii(LEG_R, f) + r, radius2=along_radii(LEG_R, f) + r, depth=0.02, matrix=Matrix.Translation(c) @ q.to_matrix().to_4x4())
    o = m.finish(name, coll, recalc=False)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0032, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.5, "iterations": 2})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def build_legs_low():
    m = Mesh()
    meta = []
    for side, tag in ((1, "L"), (-1, "R")):
        path = catmull([mir(p, side) for p in LEG], 3)
        m.tube(path, lambda f: along_radii(LEG_R, f) * 1.04, sides=7)
        n = len(path)
        for i in range(n):
            meta += [(tag, i / (n - 1))] * 7
    return m.finish(N + "LegsLow", GAME), meta


def build_toes_low():
    m = Mesh()
    meta = []
    for side, tag in ((1, "L"), (-1, "R")):
        for tx, ty, length in TOES:
            path = resample(toe_path(side, tx, ty, length), 4)
            m.tube(path, toe_radius, sides=5)
            meta += [tag] * (4 * 5)
    return m.finish(N + "ToesLow", GAME), meta


def resample(path, n):
    a = [Vector(p) for p in path]
    out = []
    for k in range(n):
        f = k / (n - 1) * (len(a) - 1)
        i = min(int(f), len(a) - 2)
        out.append(a[i].lerp(a[i + 1], f - i))
    return out


# ---------- arms ----------
FINGERS = ((-0.016, 0.052), (0.0, 0.058), (0.016, 0.05))


def hand_frame(side):
    wrist, tip = mir(ARM[2], side), mir(ARM[3], side)
    d = (tip - wrist).normalized()
    across = V(0, 0, 1).cross(d).normalized()
    return tip, d, across


def finger_path(side, off, length):
    c, d, across = hand_frame(side)
    start = c + V(0, 0, off) + d * 0.012
    return catmull([start, start + d * length * 0.55 + V(0, 0, 0), start + d * length + V(0, 0, -0.016)], 4)


def thumb_path(side):
    c, d, across = hand_frame(side)
    start = c + across * (0.016 * side * -1) + V(0, 0, 0.02)
    return catmull([start, start + d * 0.02 + across * (-side * 0.012) + V(0, 0, 0.012), start + d * 0.038 + across * (-side * 0.012) + V(0, 0, 0.014)], 4)


def build_arms_hi(name, coll):
    m = Mesh()
    for side in (1, -1):
        path = catmull([mir(p, side) for p in ARM[:3]], 12)
        m.tube(path, lambda f: 0.046 + 0.022 * f ** 2, sides=20, caps=True)
        # the wrist in the cuff, a long thin palm, three fingers and a thumb
        wrist, tip = mir(ARM[2], side), mir(ARM[3], side)
        m.tube([wrist - (tip - wrist).normalized() * 0.03, wrist, tip], lambda f: 0.02, sides=12)
        c, d, across = hand_frame(side)
        m.ball(c, (0.024, 0.028, 0.03), 18, 12)
        for off, length in FINGERS:
            m.tube(finger_path(side, off, length), lambda f: 0.0095 - 0.004 * f, sides=10)
        m.tube(thumb_path(side), lambda f: 0.0095 - 0.003 * f, sides=10)
    o = m.finish(name, coll, recalc=False)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0026, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.5, "iterations": 2})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def build_arms_low():
    m = Mesh()
    meta = []
    for side, tag in ((1, "L"), (-1, "R")):
        path = catmull([mir(p, side) for p in ARM[:3]], 3)
        m.tube(path, lambda f: 0.048 + 0.022 * f ** 2, sides=7)
        n = len(path)
        for i in range(n):
            meta += [(tag, i / (n - 1))] * 7
    return m.finish(N + "ArmsLow", GAME), meta


def build_hands_low():
    m = Mesh()
    meta = []
    for side, tag in ((1, "L"), (-1, "R")):
        wrist, tip = mir(ARM[2], side), mir(ARM[3], side)
        m.tube([wrist - (tip - wrist).normalized() * 0.03, tip], lambda f: 0.021, sides=5)
        meta += [tag] * 10
        c, d, across = hand_frame(side)
        m.ball(c, (0.026, 0.03, 0.032), 6, 4)
        meta += [tag] * (6 * 3 + 2)
        for off, length in FINGERS:
            m.tube(resample(finger_path(side, off, length), 3), lambda f: 0.0105 - 0.004 * f, sides=4)
            meta += [tag] * 12
        m.tube(resample(thumb_path(side), 3), lambda f: 0.0105 - 0.003 * f, sides=4)
        meta += [tag] * 12
    return m.finish(N + "HandsLow", GAME), meta


# ---------- the crook ----------
def crook_radius(f):
    return float(np.interp(f, (0, 0.2, 0.7, 1), (0.05, 0.038, 0.026, 0.017)))


def build_crook_hi(name, coll):
    m = Mesh()
    m.tube(CROOK, crook_radius, sides=24)
    n = len(CROOK)
    # knots, and two short snapped twigs
    for k, f in enumerate((0.14, 0.3, 0.46, 0.62, 0.76)):
        c = CROOK[int(f * (n - 1))]
        r = crook_radius(f) * 1.32
        m.ball(c + V(0.008 * math.sin(k * 3), 0, 0.006 * math.cos(k * 2)), (r, r, r), 16, 12)
    for f, d, length in ((0.24, V(0.5, 0.7, 0.2), 0.1), (0.5, V(-0.5, 0.1, 0.8), 0.09), (0.67, V(0.6, -0.2, 0.6), 0.075)):
        c = CROOK[int(f * (n - 1))]
        d = d.normalized()
        m.tube(catmull([c, c + d * length * 0.5 + V(0, 0, 0.006), c + d * length], 3), lambda g: crook_radius(f) * 0.55 * (1 - 0.65 * g), sides=10)
    o = m.finish(name, coll, recalc=False)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0035, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.7, "iterations": 3})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def build_crook_low():
    m = Mesh()
    path = resample(CROOK, 26)
    m.tube(path, lambda f: crook_radius(f) * 1.1, sides=8)
    meta = []
    for i in range(26):
        meta += [i / 25] * 8
    for f, d, length in ((0.24, V(0.5, 0.7, 0.2), 0.1), (0.5, V(-0.5, 0.1, 0.8), 0.09), (0.67, V(0.6, -0.2, 0.6), 0.075)):
        c = CROOK[int(f * (len(CROOK) - 1))]
        d = d.normalized()
        m.tube([c, c + d * length * 0.5 + V(0, 0, 0.006), c + d * length], lambda g: crook_radius(f) * 0.6 * (1 - 0.65 * g), sides=4)
        meta += [f] * 12
    return m.finish(N + "CrookLow", GAME), meta


# ---------- the chain and the lantern ----------
LINKS = [V(TIP_X, TIP_Y, 1.845), V(TIP_X, TIP_Y, 1.78), V(TIP_X, TIP_Y, 1.715)]


def torus(m, c, r_big, r_small, major, minor, flat_y=False):
    bm = m.bm
    rows = []
    for i in range(major):
        a = TAU * i / major
        ring = []
        for j in range(minor):
            b = TAU * j / minor
            rad = r_big * 1.0 + r_small * math.cos(b)
            z_stretch = 1.45
            x, z = rad * math.cos(a), rad * math.sin(a) * z_stretch
            y = r_small * math.sin(b)
            p = V(y, x, z) if flat_y else V(x, y, z)
            ring.append(bm.verts.new(c + p))
        rows.append(ring)
    for i in range(major):
        i2 = (i + 1) % major
        for j in range(minor):
            j2 = (j + 1) % minor
            bm.faces.new((rows[i][j], rows[i2][j], rows[i2][j2], rows[i][j2]))


def build_chain(name, coll, major, minor):
    m = Mesh()
    for k, c in enumerate(LINKS):
        torus(m, c, 0.023, 0.0055, major, minor, flat_y=bool(k % 2))
    return m.finish(name, coll)


def hex_ring(z_rel, r, sides=6):
    return [LANTERN_AT + V(r * math.cos(TAU * k / sides + math.pi / 6), r * math.sin(TAU * k / sides + math.pi / 6), z_rel) for k in range(sides)]


def lantern_r(z_rel):
    """A paper lantern's belly: wider in the middle of its height."""
    q = z_rel / (LANTERN_H / 2)
    return LANTERN_R * (0.72 + 0.28 * math.cos(q * math.pi / 2))


def build_frame(name, coll, rib_sides, rows, rib_r=0.0062):
    """Six bronze ribs following the belly, a band above and below, a pagoda roof with upturned eaves, a finial and the ring it hangs by."""
    m = Mesh()
    H = LANTERN_H / 2
    for k in range(6):
        pts = []
        for i in range(rows + 1):
            z = -H + 2 * H * i / rows
            pts.append(hex_ring(z, lantern_r(z) + 0.002)[k])
        m.tube(pts, lambda f: rib_r, sides=rib_sides)
    for z, thick in ((-H, 0.009), (H, 0.009)):
        ring = hex_ring(z, lantern_r(z) + 0.004)
        for k in range(6):
            m.tube([ring[k], ring[(k + 1) % 6]], lambda f: thick, sides=rib_sides, caps=True)
    # base plate
    bm = m.bm
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=lantern_r(-H) + 0.002, radius2=lantern_r(-H) + 0.002, depth=0.012, matrix=Matrix.Translation(LANTERN_AT + V(0, 0, -H - 0.004)) @ Matrix.Rotation(math.pi / 6, 4, "Z"))
    # the roof: a loft of rings from the eaves up to the finial
    prof = ((0.0, LANTERN_R * 0.74), (0.005, LANTERN_R * 1.36), (0.012, LANTERN_R * 1.3), (0.03, LANTERN_R * 0.82), (0.052, LANTERN_R * 0.42), (0.074, LANTERN_R * 0.14))
    rings = []
    for dz, r in prof:
        ring = []
        for k, q in enumerate(hex_ring(H + dz, r)):
            ring.append(bm.verts.new(q + V(0, 0, 0.012 if dz < 0.008 and r > LANTERN_R else 0)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(6):
            k2 = (k + 1) % 6
            bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    top = LANTERN_AT + V(0, 0, H + 0.074)
    m.ball(top + V(0, 0, 0.008), (0.012, 0.012, 0.014), max(rib_sides, 6), max(rib_sides // 2, 3))
    torus(m, top + V(0, 0, 0.034), 0.016, 0.005, max(rib_sides, 6) * 2, rib_sides, flat_y=False)
    # a little tassel under it
    m.tube([LANTERN_AT + V(0, 0, -H - 0.008), LANTERN_AT + V(0, 0, -H - 0.03)], lambda f: 0.005, sides=rib_sides)
    m.ball(LANTERN_AT + V(0, 0, -H - 0.042), (0.012, 0.012, 0.016), max(rib_sides, 6), max(rib_sides // 2, 3))
    return m.finish(name, coll)


def build_panels(coll, rows):
    """Paper between the ribs: the Neon that is its light."""
    m = Mesh()
    bm = m.bm
    H = LANTERN_H / 2
    for k in range(6):
        grid = []
        for i in range(rows + 1):
            z = -H + 2 * H * i / rows
            ring = hex_ring(z, lantern_r(z))
            grid.append((bm.verts.new(ring[k]), bm.verts.new(ring[(k + 1) % 6])))
        for i in range(rows):
            bm.faces.new((grid[i][0], grid[i][1], grid[i + 1][1], grid[i + 1][0]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    o = m.finish(N + "Panels_Glow_ffc070", coll, smooth_shade=False)
    return o


# ---------- blossom on the hat and the crook ----------
HAT_FLOWERS = ((2.3, 0.86), (2.62, 0.8), (2.48, 0.9), (2.82, 0.88), (2.1, 0.76), (0.62, 0.82), (0.86, 0.88))
CROOK_FLOWERS = ((0.34, 0.5, 1), (0.37, -0.6, 1.2), (0.55, 1.2, 1), (0.59, 2.2, 0.8), (0.72, -1, 1))


FLOWER_G = []


def flower(m, c, nrm, size, petals, rows):
    """Five round petals, a little cupped."""
    bm = m.bm
    u = nrm.orthogonal().normalized()
    v = nrm.cross(u).normalized()
    hub = bm.verts.new(c - nrm * 0.014)      # (under the surface it grows from)
    FLOWER_G.append(0.0)
    for k in range(petals):
        a0 = TAU * k / petals
        grid = []
        for i in range(rows + 1):
            g = (i + 1) / (rows + 1)
            row = []
            for j in range(rows + 1):
                w = (j / rows - 0.5) * 1.05 * math.sin(math.pi * min(0.9, 0.18 + g * 0.82)) ** 0.7
                a = a0 + w
                r = size * g
                row.append(bm.verts.new(c + (u * math.cos(a) + v * math.sin(a)) * r + nrm * (0.34 * size * (g ** 2) + 0.004)))
                FLOWER_G.append(g)
            grid.append(row)
        for j in range(rows):
            bm.faces.new((hub, grid[0][j], grid[0][j + 1]))
        for i in range(rows):
            for j in range(rows):
                bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))


def build_flowers(name, coll, petals, rows):
    m = Mesh()
    which = []
    for k, (a, t) in enumerate(HAT_FLOWERS):
        before = len(m.bm.verts)
        side, fwd = hat_frame()
        c = hat_point(a, t, 0.002)
        d = hat_point(a, t + 0.04) - hat_point(a, t - 0.04)
        e = (hat_point(a + 0.1, t) - hat_point(a - 0.1, t))
        nrm = e.cross(d).normalized()
        if nrm.dot(HAT_UP) < 0:
            nrm = -nrm
        flower(m, c, nrm, 0.026 + 0.012 * hash_of(k), petals, rows)
        which += ["Hat"] * (len(m.bm.verts) - before)
    n = len(CROOK)
    for k, (f, a, s) in enumerate(CROOK_FLOWERS):
        before = len(m.bm.verts)
        i = int(f * (n - 1))
        tan = (CROOK[i + 1] - CROOK[i]).normalized()
        out = (tan.orthogonal().normalized() @ Matrix.Rotation(a, 3, tan)).normalized()
        flower(m, CROOK[i] + out * crook_radius(f), out, 0.026 * s, petals, rows)
        which += [f] * (len(m.bm.verts) - before)
    return m.finish(name, coll, recalc=False), which


def build_hi(clay=False):
    pieces, data = {}, {}
    pieces["Skin"] = build_core(N + "SkinHi", HI, 28, 0.005)
    for key, cols, rows in (("Mantle", 800, 100), ("Mid", 960, 100), ("Low", 1120, 110)):
        pieces[key] = build_tier(key, N + key + "Hi", HI, cols, rows)
    pieces["Hat"] = build_hat(N + "HatHi", HI, 1440, 110, 14)
    pieces["Mask"] = build_mask(N + "MaskHi", HI, 0.0028, 180, 72, 5)
    pieces["Pupils"] = build_pupils(N + "PupilsHi", HI, 28)
    pieces["Legs"] = build_legs_hi(N + "LegsHi", HI)
    pieces["Toes"] = pieces["Legs"]
    pieces["Arms"] = build_arms_hi(N + "ArmsHi", HI)
    pieces["Hands"] = pieces["Arms"]
    pieces["Crook"] = build_crook_hi(N + "CrookHi", HI)
    pieces["Chain"] = build_chain(N + "ChainHi", HI, 28, 12)
    pieces["Frame"] = build_frame(N + "FrameHi", HI, 12, 16)
    FLOWER_G.clear()
    pieces["Flowers"], _ = build_flowers(N + "FlowersHi", HI, 5, 5)
    data["flower_g"] = np.array(FLOWER_G)
    glows = {"Panels": build_panels(HI, 8), "Glints": build_glints(HI, 12)}
    if not clay:
        paint_all(pieces, data)
    return pieces, glows, data


def lamp(P, Nn):
    """How much of the lantern's light falls here: painted in, since it hangs close and swings little."""
    d = np.array(tuple(LANTERN_AT)) - P
    L = np.linalg.norm(d, axis=1)
    return np.clip((Nn * d).sum(1) / np.maximum(L, 1e-4), 0, 1) / (1 + (L / 0.42) ** 2)


def lit(col, P, Nn, amount=0.42):
    return mix(col, EMBER, lamp(P, Nn) * amount)


def strand_noise(P, f, seed):
    return fbm(P * np.array((1.0, 1.0, 0.1)), f, 3, seed)


def paint_tier(o, key):
    P = verts(o)
    Nn = normals(o)
    z0, z1, *_ = TIERS[key]
    u = np.clip((P[:, 2] - z0) / (z1 - z0), 0, 1.3)
    a = np.arctan2(P[:, 0], -(P[:, 1] + 0.13 * (P[:, 2] - 0.6)) / FLAT_Y)
    Q = np.column_stack((np.cos(a) * 0.32, np.sin(a) * 0.32, P[:, 2] * 0.07))
    strand = fbm(Q, 60.0, 2, 11)
    fine = fbm(Q, 190.0, 2, 17)
    col = mix(STRAW_D, STRAW, smooth(0.36, 0.62, strand * 0.5 + fine * 0.5))
    col = mix(col, STRAW_PALE, smooth(0.6, 0.76, fine) * 0.7)
    col = mix(col, STRAW_PALE, smooth(0.72, 1.05, u) * 0.3)      # the ends bleach
    patch = fbm(P, 6.0, 3, 29)
    share = {"Mantle": 0.72, "Mid": 0.5, "Low": 0.3}[key]
    moss = smooth(0.62 - 0.3 * share, 0.78 - 0.3 * share, patch + 0.12 * (fine - 0.5)) * smooth(0.95, 0.35, u)
    col = mix(col, mix(MOSS_D, MOSS, fbm(P, 120.0, 2, 5)), moss)
    col = col * (0.42 + 0.58 * smooth(0.0, 0.42, u))[:, None]      # dark up under the tier above
    inner = (Nn[:, 2] < -0.2) | (((P[:, 0] * Nn[:, 0] + (P[:, 1] - (-0.13 * (P[:, 2] - 0.6))) * Nn[:, 1]) < 0))
    col = np.where(inner[:, None], col * 0.3, col)
    col = lit(col, P, Nn, 0.3)
    set_verts(o, P + Nn * (0.0065 * (strand - 0.5) + 0.0028 * (fine - 0.5) * (1 - moss))[:, None])
    paint(o, col, 0.88)


def paint_hat(o):
    P = verts(o)
    Nn = normals(o)
    side, fwd = hat_frame()
    C, S_, F_, U_ = (np.array(tuple(q)) for q in (HAT_C, side, fwd, HAT_UP))
    d = P - C
    x, y = d @ S_, d @ F_
    a = np.arctan2(y, x)
    t = np.sqrt(x ** 2 + y ** 2) / HAT_R
    under = (Nn @ U_) < -0.1
    # straw radiating from the crown; two rows of binding thread
    ray = 0.5 + 0.5 * np.sin(a * 150 + 2.4 * np.sin(a * 9))
    ray2 = 0.5 + 0.5 * np.sin(a * 330 + 3 * np.sin(a * 17))
    n = fbm(np.column_stack((np.cos(a) * 16, np.sin(a) * 16, t * 1.2)), 2.4, 3, 3)
    col = mix(STRAW_D, STRAW, smooth(0.25, 0.75, ray * 0.45 + ray2 * 0.2 + n * 0.5))
    col = mix(col, STRAW_PALE, smooth(0.62, 0.86, n) * 0.5)
    thread = np.maximum(np.exp(-((t - 0.36) / 0.008) ** 2), np.exp(-((t - 0.68) / 0.008) ** 2)) * (0.6 + 0.4 * np.sign(np.sin(a * 60)))
    col = mix(col, rgb(52, 34, 26), thread)
    patch = fbm(P, 7.0, 3, 41)
    toward = np.exp(-(((a - 2.45 + math.pi) % TAU - math.pi) / 0.85) ** 2) + 0.5 * np.exp(-(((a - 0.74 + math.pi) % TAU - math.pi) / 0.5) ** 2)
    moss = smooth(0.55, 0.72, patch + 0.26 * toward - 0.08) * smooth(0.42, 0.72, t)
    col = mix(col, mix(MOSS_D, MOSS, fbm(P, 130.0, 2, 7)), moss)
    col = col * (0.8 + 0.2 * smooth(0.0, 0.3, t))[:, None]
    col = np.where(under[:, None], mix(STRAW_D * 0.3, EMBER, lamp(P, Nn) * 0.4), col)
    disp = 0.0028 * (ray - 0.5) + 0.0016 * (ray2 - 0.5) + 0.004 * thread * 0.5 + 0.004 * moss * (fbm(P, 90.0, 2, 9) - 0.2)
    set_verts(o, P + Nn * (disp * (~under))[:, None])
    paint(o, col, 0.86)


def paint_mask(o):
    P = verts(o)
    Nn = normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    p = (z - MASK_Z) / MASK_H
    col = np.tile(IVORY, (len(P), 1))
    col = mix(col, IVORY_D, smooth(0.42, 0.7, fbm(P, 15.0, 3, 3)) * 0.26)      # old lacquer, yellowing unevenly
    # painted, as such masks are: high smudged brows, rouge, a very small mouth that has decided something
    for side in (1, -1):
        brow = np.exp(-(((x - side * 0.05) / 0.028) ** 2 + ((z - (MASK_Z + 0.096 + 0.008 * (1 - ((x - side * 0.05) / 0.03) ** 2))) / 0.0095) ** 2))
        col = mix(col, rgb(60, 54, 60), np.clip(brow * 1.15, 0, 0.92))
        cheek = np.exp(-(((x - side * 0.068) / 0.036) ** 2 + ((z - (MASK_Z - 0.038)) / 0.03) ** 2))
        col = mix(col, ROUGE, cheek * 0.32)
        # a thin dark line round each slit
        t = (x - side * EYE_X) / EYE_A
        arch = EYE_B * np.clip(1 - t * t, 0, 1)
        top = np.abs(z - (EYE_Z + arch))
        low = np.abs(z - (EYE_Z + 0.34 * arch))
        liner = np.exp(-(np.minimum(top, low * 1.5) / 0.0028) ** 2) * (np.abs(t) < 1.14)
        col = mix(col, rgb(36, 28, 32), liner * 0.9)
    mx = x / 0.022
    mouth_line = MASK_Z - 0.098 + 0.0065 * mx ** 2
    mouth = np.exp(-((z - mouth_line) / (0.0034 * np.clip(1.2 - np.abs(mx) ** 2 * 0.8, 0.25, 1.2))) ** 2) * (np.abs(mx) < 1.0)
    col = mix(col, rgb(150, 28, 40), np.clip(mouth * 1.3, 0, 1))
    # the nostrils, the edge
    w = mask_half_width(z)
    edge = smooth(0.8, 1.0, np.abs(x) / np.maximum(w, 0.01))
    col = mix(col, IVORY_D * 0.62, edge * 0.6)
    col = lit(col, P, Nn, 0.24)
    # behind: the slits' walls and floors are the dark; the back of the mask, bark
    behind = y > mask_y(x, z) + 0.0012
    col = np.where(behind[:, None], np.tile(rgb(8, 6, 8), (len(P), 1)), col)
    rough = np.where(behind, 0.9, 0.36)
    set_verts(o, P + Nn * (0.00045 * (fbm(P, 50.0, 2, 8) - 0.5))[:, None] * (~behind)[:, None])
    paint(o, col, rough)


def paint_pupils(o):
    P = verts(o)
    col = np.zeros((len(P), 3))
    for side in (1, -1):
        c = np.array(tuple(eye_frame(side)[0]))
        r = np.linalg.norm(P - c, axis=1) / PUPIL_R
        mine = (P[:, 0] * side) > 0
        here = mix(rgb(255, 200, 96), rgb(150, 66, 16), smooth(0.34, 1.0, r))
        here = mix(rgb(16, 8, 6), here, smooth(0.16, 0.34, r))
        col = np.where(mine[:, None], here, col)
    paint(o, col, 0.2)


def paint_core(o):
    """A dark wrapped cloth, in folds running back from the mask."""
    P = verts(o)
    Nn = normals(o)
    Q = P * np.array((1.0, 0.32, 1.0))
    fold = fbm(Q, 15.0, 3, 3)
    thread = 0.5 + 0.5 * np.sin(P[:, 2] * 620) * np.sin(P[:, 0] * 620)
    col = mix(CLOTH_D, mix(CLOTH, MOSS_D, 0.55), smooth(0.3, 0.72, fold))
    col = col * (0.9 + 0.1 * thread)[:, None]
    set_verts(o, P + Nn * (0.012 * (fold - 0.5))[:, None])
    paint(o, col, 0.92)


def paint_legs(o):
    P = verts(o)
    Nn = normals(o)
    best = np.full(len(P), 9.0)
    f = np.zeros(len(P))
    for side in (1, -1):
        path = catmull([mir(q, side) for q in LEG], 14)
        ff, dd = nearest_on(path, P)
        take = dd < best
        best[take], f[take] = dd[take], ff[take]
    r = np.interp(f, np.linspace(0, 1, 4), LEG_R)
    wrap = ((f > 0.48) & (f < 0.66) & (best > r + 0.0042))
    bark = strand_noise(P * np.array((1.0, 1.0, 0.4)), 110.0, 21)
    col = mix(BARK_D, BARK, smooth(0.34, 0.66, bark))
    col = mix(col, rgb(120, 94, 66), smooth(0.68, 0.84, bark) * 0.5)
    col = np.where(wrap[:, None], mix(rgb(116, 104, 82), rgb(168, 154, 124), fbm(P, 180.0, 2, 3)), col)
    col = mix(col, MOSS, smooth(0.62, 0.74, fbm(P, 12.0, 2, 33)) * smooth(0.2, 0.0, P[:, 2]) * 0.8)
    set_verts(o, P + Nn * (0.002 * (bark - 0.5))[:, None])
    paint(o, col, 0.88)


def paint_arms(o):
    P = verts(o)
    Nn = normals(o)
    col = np.zeros((len(P), 3))
    rough = np.full(len(P), 0.86)
    best = np.full(len(P), 9.0)
    f = np.zeros(len(P))
    for side in (1, -1):
        path = catmull([mir(q, side) for q in ARM[:3]], 12)
        ff, dd = nearest_on(path, P)
        take = dd < best
        best[take], f[take] = dd[take], ff[take]
    thin = best < 0.031
    bare = np.zeros(len(P), bool)
    for side in (1, -1):
        wrist = np.array(tuple(mir(ARM[2], side)))
        tan = np.array(tuple((mir(ARM[2], side) - mir(ARM[1], side)).normalized()))
        bare |= ((P - wrist) @ tan > 0.004) & ((P[:, 0] * side) > 0)
    fold = fbm(P * np.array((1.0, 0.5, 1.0)), 44.0, 2, 7)
    sleeve = mix(CLOTH_D, mix(CLOTH, MOSS_D, 0.4), fold)
    sleeve = mix(sleeve, STRAW_D, smooth(0.86, 0.97, f) * 0.8)
    wood = mix(IVORY_D, IVORY, fbm(P, 90.0, 2, 3) * 0.7)
    col = np.where(bare[:, None], wood, sleeve)
    col = lit(col, P, Nn, 0.28)
    paint(o, col, np.where(bare, 0.5, 0.88))


def paint_crook(o):
    P = verts(o)
    Nn = normals(o)
    f, dd = nearest_on(CROOK, P)
    n = fbm(P * np.array((1.0, 1.0, 0.7)), 86.0, 3, 19)
    col = mix(BARK_D, BARK, smooth(0.28, 0.66, n))
    col = mix(col, rgb(136, 110, 82), smooth(0.68, 0.84, n) * 0.46)
    moss = smooth(0.54, 0.68, fbm(P, 16.0, 3, 45) + 0.2 * Nn[:, 2] - 0.05)
    col = mix(col, mix(MOSS_D, MOSS, fbm(P, 110.0, 2, 3)), moss)
    set_verts(o, P + Nn * (0.0028 * (n - 0.5) + 0.0016 * moss)[:, None])
    paint(o, col, 0.86)


def paint_metal(o):
    P = verts(o)
    Nn = normals(o)
    n = fbm(P, 46.0, 3, 9)
    green = smooth(0.5, 0.66, n + 0.16 * (1 - np.clip(Nn[:, 2] * 0.5 + 0.5, 0, 1)))
    col = mix(BRONZE, VERDIGRIS, green)
    paint(o, col, 0.42 + 0.46 * green, 0.92 * (1 - green))


def paint_flowers(o, g):
    n = fbm(verts(o), 90.0, 2, 7)
    col = mix(mix(GOLD_HEART, BLOSSOM_D, smooth(0.14, 0.34, g)), BLOSSOM, smooth(0.34, 0.9, g + 0.2 * (n - 0.5)))
    paint(o, col, 0.7)


GOLD_HEART = rgb(255, 214, 110)


def paint_all(pieces, data):
    for key in ("Mantle", "Mid", "Low"):
        paint_tier(pieces[key], key)
    paint_hat(pieces["Hat"])
    paint_mask(pieces["Mask"])
    paint_pupils(pieces["Pupils"])
    paint_core(pieces["Skin"])
    paint_legs(pieces["Legs"])
    paint_arms(pieces["Arms"])
    paint_crook(pieces["Crook"])
    paint_metal(pieces["Chain"])
    paint_metal(pieces["Frame"])
    paint_flowers(pieces["Flowers"], data["flower_g"])


def show_glows(glows):
    for o in glows.values():
        m = bpy.data.materials.new(o.name)
        g = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (1.0, 0.5, 0.14, 1)
        g.inputs["Emission Strength"].default_value = 1.0
        o.data.materials.append(m)
        o.visible_shadow = False


VIEWS = [(0, -1, 0.1), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.62, 0.62, 0.4), (-0.62, -0.72, 0.28), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, -0.05, 1.12)
FACE_AT = (0, -0.25, 1.48)
EXTRA = [(0, -1, 0.02, 1.5, FACE_AT), (0.62, -0.78, 0.12, 1.5, FACE_AT), (1, -0.05, 0.02, 1.8, FACE_AT), (0.3, -0.9, 0.4, 1.8, FACE_AT), (0, -1, 0.02, 0.62, (0, -0.28, 1.47)), (0.72, -0.62, 0.1, 1.1, (TIP_X, TIP_Y, 1.55)), (0.75, -0.55, -0.1, 1.6, (0.1, -0.05, 0.3)), (0.3, -0.95, 0.1, 0.7, (0.08, -0.44, 1.03))]


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
        mat = hi_material(ao_distance=0.06, ao_share=0.45)
    for o in set(pieces.values()):
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=7.4, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
TEXELS = {"Mantle": 1.15, "Mid": 1.1, "Low": 1.1, "Hat": 1.2, "Mask": 3.2, "Pupils": 3.0, "Legs": 0.95, "Toes": 0.95, "Arms": 0.7, "Hands": 1.6, "Crook": 1.0, "Chain": 0.7, "Frame": 1.3, "Flowers": 2.0}
META = {}
EYE_BLINK = 0.03      # metres back: the pupils draw away behind the mask's floor
EYE_GLANCE = 0.2      # radians: how far the pupils slide either way


def truest(base, name, targets):
    """QuadriFlow can wreck a small form and leave the mesh checks green: try several, measure each against the sculpt, keep the truest."""
    tree = tree_of(base)
    best, best_gap = None, 1e9
    for quads in targets:
        o = retopo_skin(base, N + "Try", quads)
        gap = surface_gap(o, tree)
        print("TRY", name, quads, len(o.data.polygons), "gap", round(gap, 4), flush=True)
        if gap < best_gap:
            if best:
                bpy.data.objects.remove(best, do_unlink=True)
            best, best_gap = o, gap
        else:
            bpy.data.objects.remove(o, do_unlink=True)
        if gap < 0.007:
            break
    assert best_gap < 0.016, name + ": every re-mesh strayed from the sculpt"
    best.name = N + name + "Low"
    for v in best.data.vertices:
        v.co = v.co.lerp(tree.find_nearest(v.co)[0], 0.8)
    return best


def build_low(pieces, data):
    lows = {"Skin": truest(data["CoreBase"], "Skin", (450, 520, 400, 600))}
    for key in ("Mantle", "Mid", "Low"):
        teeth = TIERS[key][4]
        lows[key] = build_tier(key, N + key + "Low", GAME, teeth * 2, 4)
    lows["Hat"] = build_hat(N + "HatLow", GAME, 28, 7, 2, frayed=False)
    lows["Mask"] = build_mask(N + "MaskLow", GAME, 0.024, 32, 14, 1)
    lows["Pupils"] = build_pupils(N + "PupilsLow", GAME, 10)
    lows["Legs"], META["Legs"] = build_legs_low()
    lows["Toes"], META["Toes"] = build_toes_low()
    lows["Arms"], META["Arms"] = build_arms_low()
    lows["Hands"], META["Hands"] = build_hands_low()
    lows["Crook"], META["Crook"] = build_crook_low()
    lows["Chain"] = build_chain(N + "ChainLow", GAME, 8, 4)
    lows["Frame"] = build_frame(N + "FrameLow", GAME, 4, 5)
    FLOWER_G.clear()
    lows["Flowers"], META["Flowers"] = build_flowers(N + "FlowersLow", GAME, 5, 1)
    triangulate(lows)
    return lows


# ---------- the skeleton ----------
CROOK_F = (0.1, 0.42, 0.72)
CROOK_BONES = ("Crook1", "Crook2", "Crook3")
SECTORS = (("F", 0.0), ("L", math.pi / 2), ("B", math.pi), ("R", -math.pi / 2))      # round the cape: a = 0 faces -Y, a = pi/2 is +X, its left


def cape_angle(P):
    return np.arctan2(P[:, 0], -(P[:, 1] + 0.13 * (P[:, 2] - 0.6)) / FLAT_Y)


def path_at(path, f):
    return path[min(len(path) - 1, int(round(f * (len(path) - 1))))].copy()


def skeleton(data):
    head_at = V(0, HOOD.y + 0.01, 1.37)
    bones = [("Root", V(0, 0, 0), None), ("Body", V(0, lean(0.8), 0.8), "Root"), ("Chest", V(0, lean(1.15), 1.15), "Body"), ("Neck", V(0, lean(1.3), 1.3), "Chest"), ("Head", head_at, "Neck"), ("Hat", HAT_C.copy(), "Head")]
    for side, tag in ((1, "L"), (-1, "R")):
        bones.append(("Eye" + tag, eye_frame(side)[3], "Head"))
    parent = "Chest"
    for name, f in zip(CROOK_BONES, CROOK_F):
        bones.append((name, path_at(CROOK, f), parent))
        parent = name
    bones += [("Chain1", V(TIP_X, TIP_Y, 1.875), "Crook3"), ("Chain2", V(TIP_X, TIP_Y, 1.812), "Chain1"), ("Lantern", V(TIP_X, TIP_Y, 1.748), "Chain2"), ("Flame", LANTERN_AT.copy(), "Lantern")]
    for key, parent in (("Mid", "Chest"), ("Low", "Body")):
        z0, _, r0, *_ = TIERS[key]
        for tag, a in SECTORS:
            bones.append((key + tag, V(math.sin(a) * r0, -math.cos(a) * r0 * FLAT_Y + lean(z0), z0), parent))
    for side, tag in ((1, "L"), (-1, "R")):
        bones += [("Arm" + tag + "1", mir(ARM[0], side), "Chest"), ("Arm" + tag + "2", mir(ARM[1], side), "Arm" + tag + "1"), ("Hand" + tag, mir(ARM[2], side), "Arm" + tag + "2")]
        bones += [("Leg" + tag + "1", mir(LEG[0], side), "Body"), ("Leg" + tag + "2", mir(LEG[1], side), "Leg" + tag + "1"), ("Leg" + tag + "3", mir(LEG[2], side), "Leg" + tag + "2"), ("Foot" + tag, mir(LEG[3], side), "Leg" + tag + "3")]
    return armature(bones)


def tier_weights(o, key, base):
    P = verts(o)
    z0, z1, *_ = TIERS[key]
    u = np.clip((P[:, 2] - z0) / (z1 - z0), 0, 1)
    g = smooth(0.1, 0.9, u)
    a = cape_angle(P)
    out = []
    for i in range(len(P)):
        shares = {}
        for tag, ak in SECTORS:
            c = max(0.0, math.cos(float(a[i]) - ak))
            if c > 0.02:
                shares[tag] = c * c
        total = sum(shares.values())
        w = {} if g[i] > 0.99 else {base: float(1 - g[i])}
        if g[i] > 0.01:
            for tag, c in shares.items():
                w[key + tag] = float(g[i]) * c / total
        out.append(w)
    return out


def trunk_weight(z):
    if z < 0.95:
        return {"Body": 1.0}
    if z < 1.12:
        t = float(smooth(0.95, 1.12, z))
        return {"Body": 1 - t, "Chest": t}
    if z < 1.24:
        return {"Chest": 1.0}
    if z < 1.33:
        t = float(smooth(1.24, 1.33, z))
        return {"Chest": 1 - t, "Neck": t}
    if z < 1.4:
        t = float(smooth(1.33, 1.4, z))
        return {"Neck": 1 - t, "Head": t}
    return {"Head": 1.0}


def limb(names, cuts, f):
    """Each name holds till its cut, and hands over across a short joint."""
    for k, cut in enumerate(cuts):
        if f < cut - 0.05:
            return {names[k]: 1.0}
        if f < cut + 0.05:
            t = float(smooth(cut - 0.05, cut + 0.05, f))
            return {names[k]: 1 - t, names[k + 1]: t}
    return {names[-1]: 1.0}


def crook_weight(f):
    return chain_weight(CROOK_BONES, CROOK_F, f)


def bind_all(lows, rig, glows, data):
    weigh(lows["Skin"], [trunk_weight(float(p[2])) for p in verts(lows["Skin"])])
    rigid(lows["Mantle"], "Chest")
    weigh(lows["Mid"], tier_weights(lows["Mid"], "Mid", "Chest"))
    weigh(lows["Low"], tier_weights(lows["Low"], "Low", "Body"))
    rigid(lows["Hat"], "Hat")
    rigid(lows["Mask"], "Head")
    weigh(lows["Pupils"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(lows["Pupils"])])
    weigh(glows["Glints"], [{"EyeL" if p[0] > 0 else "EyeR": 1.0} for p in verts(glows["Glints"])])
    weigh(lows["Legs"], [limb(("Leg%s1" % t, "Leg%s2" % t, "Leg%s3" % t, "Foot%s" % t), (1 / 3, 2 / 3, 0.97), f) for t, f in META["Legs"]])
    weigh(lows["Toes"], [{"Foot" + t: 1.0} for t in META["Toes"]])
    weigh(lows["Arms"], [limb(("Arm%s1" % t, "Arm%s2" % t, "Hand%s" % t), (0.5, 0.985), f) for t, f in META["Arms"]])
    weigh(lows["Hands"], [{"Hand" + t: 1.0} for t in META["Hands"]])
    weigh(lows["Crook"], [crook_weight(f) for f in META["Crook"]])
    weigh(lows["Flowers"], [{"Hat": 1.0} if w == "Hat" else crook_weight(w) for w in META["Flowers"]])
    chain = verts(lows["Chain"])
    weigh(lows["Chain"], [{("Chain1" if p[2] > 1.812 else ("Chain2" if p[2] > 1.748 else "Lantern")): 1.0} for p in chain])
    rigid(lows["Frame"], "Lantern")
    rigid(glows["Panels"], "Flame")
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateLanternWarden uses. +X: a hanging limb's far end swings forward, a head lifts; +Y: turns to its left; +Z rolls
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), move)


def stride(a, lift=0.0):
    """One leg's swing, positive forward: a bird's: the knee leads and the shin folds as it comes through."""
    return {"1": game_turn(a, 0, 0), "2": game_turn(-0.9 * lift, 0, 0), "3": game_turn(1.0 * lift, 0, 0), "F": game_turn(-0.5 * lift, 0, 0)}


def legs(left, right):
    out = {}
    for tag, spec in (("L", left), ("R", right)):
        s_ = stride(*spec)
        out["Leg%s1" % tag], out["Leg%s2" % tag], out["Leg%s3" % tag], out["Foot%s" % tag] = s_["1"], s_["2"], s_["3"], s_["F"]
    return out


def pose_library():
    swing = {"Chain1": game_turn(0.34, 0, 0.2), "Chain2": game_turn(0.1, 0, 0.1), "Lantern": game_turn(0.06, 0, 0.1)}
    return {
        "Blink": {"EyeL": ((0, 0, 1), 0, (0, EYE_BLINK, 0)), "EyeR": ((0, 0, 1), 0, (0, EYE_BLINK, 0))},
        "LookL": {"EyeL": game_turn(0, -EYE_GLANCE, 0), "EyeR": game_turn(0, -EYE_GLANCE, 0)},
        "LookR": {"EyeL": game_turn(0, EYE_GLANCE, 0), "EyeR": game_turn(0, EYE_GLANCE, 0)},
        "Tilt": {"Neck": game_turn(0, 0.2, 0.1), "Head": game_turn(0.08, 0.3, 0.42)},
        "Stride1": {**legs((0.55, 1.0), (-0.45, 0.0)), "Body": game_turn(0, 0.05, 0.04, (0, 0, -0.01)), **swing, "MidF": game_turn(0.1, 0, 0), "LowF": game_turn(0.2, 0, 0), "LowB": game_turn(0.1, 0, 0)},
        "Stride2": {**legs((-0.45, 0.0), (0.55, 1.0)), "Body": game_turn(0, -0.05, -0.04, (0, 0, -0.01)), "Chain1": game_turn(-0.3, 0, -0.2), "LowF": game_turn(0.2, 0, 0), "LowB": game_turn(0.1, 0, 0)},
        "Raise": {"Crook1": game_turn(0.1, 0, 0), "Crook2": game_turn(0.22, 0, 0), "Crook3": game_turn(0.26, 0, 0), "Neck": game_turn(0.24, 0, 0), "Head": game_turn(0.24, 0.2, 0.05), "ArmL1": game_turn(0.9, 0, -0.5), "ArmL2": game_turn(0.5, 0, 0), "ArmR1": game_turn(0.5, 0, 0.3), "HandL": game_turn(0.4, 0, 0)},
        "Hover": {**legs((-0.5, 0.0), (-0.32, 0.0)), "Body": game_turn(-0.16, 0, 0, (0, 0, 0.1)), "Chain1": game_turn(-0.55, 0, 0), "Chain2": game_turn(-0.2, 0, 0), "MidB": game_turn(-0.32, 0, 0), "LowB": game_turn(-0.5, 0, 0), "LowL": game_turn(0, 0, 0.3), "LowR": game_turn(0, 0, -0.3), "Hat": game_turn(0.08, 0, 0)},
        "TurnL": {"Neck": game_turn(0, 0.5, 0), "Head": game_turn(0, 0.7, 0)},
        "TurnR": {"Neck": game_turn(0, -0.5, 0), "Head": game_turn(0, -0.7, 0)},
    }


if __name__ == "__main__" and STAGE == "all":
    pieces, glows, data = build_hi()
    data["CoreBase"] = build_core(N + "CoreBase", HI, 28, 0.005)
    data["CoreBase"].hide_render = True
    mat = hi_material(ao_distance=0.06, ao_share=0.45)
    for o in set(pieces.values()):
        o.data.materials.clear()
        o.data.materials.append(mat)
    show_glows(glows)
    stage_setup((0.30, 0.33, 0.42, 1))
    lows = build_low(pieces, data)
    unwrap(lows, [(None, 0.55)], {}, shape="CONCAVE", angle=64, texels=TEXELS, margin=0.005)
    thin = {k: (0.009, 0.022) for k in ("Mantle", "Mid", "Low")}
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=True, fill=(0.2, 0.15, 0.08, 1), far=("Skin", "Legs", "Toes", "Arms", "Crook"), reach=(0.01, 0.024), far_reach=(0.016, 0.04),
             reaches={**thin, "Hat": (0.016, 0.04), "Mask": (0.03, 0.05), "Pupils": (0.004, 0.01), "Hands": (0.012, 0.03), "Frame": (0.012, 0.03), "Chain": (0.008, 0.02), "Flowers": (0.008, 0.02)})
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for o in glows.values():
        HI.objects.unlink(o)
        GAME.objects.link(o)
    triangulate(glows)
    rig = skeleton(data)
    body = bind_all(lows, rig, glows, data)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 2) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    pose(rig, {})
    bpy.context.scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=7.4, size=640)
    lib = pose_library()
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    close = (0.2, -0.97, 0.05, 1.1, FACE_AT)
    whole = (0.72, -0.62, 0.18, 7.4, VIEW_AT)
    for name, view in (("Blink", close), ("LookL", close), ("Tilt", close), ("Stride1", whole), ("Stride2", whole), ("Raise", whole), ("Hover", whole), ("TurnL", (0.7, -0.7, 0.1, 2.4, FACE_AT)), ("TurnR", (0.7, -0.7, 0.1, 2.4, FACE_AT))):
        pose(rig, lib[name])
        shots(os.path.join(REVIEW, "pose" + name), [view], target=VIEW_AT, size=540)
    pose(rig, {})
    for o in glows.values():
        o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.28, 7.4, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)
