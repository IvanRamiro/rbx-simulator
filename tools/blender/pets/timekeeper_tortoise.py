"""The Timekeeper Tortoise (Legendary, Time; Astral Sanctum Egg, also in the Heavenly Throne Egg): "Its shell is a calendar for an age nobody remembers. It is
never late, because it decides when things happen."

A sundial tortoise (the owner's choice, 2026-11-09), in a design language of its own: an ancient sundial grown into a living shell. A giant land tortoise,
its high dome a weathered stone of scutes with deep growth rings; on its crown a dial of bronze inlaid in the stone, a ring with hour lines fanning out
from a tall bronze gnomon blade, and numerals of an age nobody remembers (bars and dots) round it; the bronze gone green with verdigris in its grooves; a
thin line of gold light along the gnomon's edge. A wrinkled old sage of a face: long flowing white brows (which move: its expression), a hooked beak of dark horn, small dark eyes under heavy lids that blink slowly. Armoured forelegs of big overlapping scales, columnar hind legs,
blunt nails; a short tail tucked under.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/timekeeper_tortoise.py -- [clay|paint|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. all: also the game mesh, bake, rig, the file and the FBX.
Faces -Y, Z up, 1 unit = 1 metre. +X is its left. Stands on the ground (its feet at z = 0). The maps go to assets/pets/AstralSanctumEgg/.

What touches what: the shell (carapace, bridges and plastron) is one solid piece; the neck and head, each leg and the tail are skin, each rooted inside the
shell; the eyes sit in the head with their lids round them; the brows root in the brow ridge; the nails root in the feet; the
gnomon stands sunk into the crown of the shell, its gold edge lying along its sloped edge.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector  # noqa: F401  (Matrix and Vector: the game stage)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "TimekeeperTortoise"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "AstralSanctumEgg")

# ---------- colours ----------
STONE, STONE_DEEP, STONE_PALE, SEAM = rgb(186, 160, 118), rgb(138, 112, 80), rgb(214, 196, 160), rgb(70, 54, 38)
LICHEN = rgb(150, 160, 128)
BRONZE, BRONZE_DARK, VERDIGRIS = rgb(176, 124, 58), rgb(110, 72, 34), rgb(86, 160, 138)
SKIN, SKIN_DEEP, SKIN_PALE = rgb(92, 86, 74), rgb(58, 54, 46), rgb(132, 124, 104)
HORN, HORN_EDGE = rgb(58, 48, 38), rgb(126, 108, 82)
HAIR = rgb(238, 236, 228)
NAIL = rgb(70, 60, 48)
GOLD_HEX = "ffcf6e"

# ---------- the frame of it (its left; mirrored) ----------
SHELL_C = V(0, 0.03, 0.0)       # the shell's middle, seen from above
SHELL_A, SHELL_B = 0.42, 0.5    # its half-width and half-length at the rim
SHELL_TOP = 0.65
NECK = [V(0, -0.36, 0.3), V(0, -0.47, 0.35), V(0, -0.56, 0.4), V(0, -0.62, 0.425)]
HEAD_C, HEAD_R = V(0, -0.67, 0.437), (0.058, 0.086, 0.047)
SNOUT = [V(0, -0.728, 0.43), V(0, -0.752, 0.418), V(0, -0.762, 0.402)]
EYE_C, EYE_R = V(0.046, -0.69, 0.452), 0.0165
EYE_AXIS = V(0.82, -0.5, 0.25).normalized()
LID_UP, LID_LOW = (2.0, 120.0, 0.0018), (-30.0, -128.0, 0.0018)      # the upper lid low and heavy over the eye: an old one's
FORE = [V(0.19, -0.29, 0.29), V(0.29, -0.36, 0.21), V(0.31, -0.38, 0.12), V(0.305, -0.39, 0.05)]      # inside the shell, the elbow under the rim, the wrist, the foot
HIND = [V(0.19, 0.3, 0.27), V(0.29, 0.36, 0.2), V(0.3, 0.38, 0.11), V(0.295, 0.39, 0.05)]
FORE_R = [0.07, 0.074, 0.068, 0.07]
HIND_R = [0.076, 0.08, 0.074, 0.074]
TAIL = [V(0, 0.42, 0.24), V(0, 0.52, 0.18), V(0, 0.585, 0.12)]
GNOMON = (V(0, -0.14, 0.0), V(0, 0.2, 0.0), 0.3)          # its base runs front to back along the crown; its tall end at the back, this much above the shell
DIAL_S = 0.42                                             # where on the dome (0 the crown, 1 the rim) the dial's bronze ring lies


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def path_at(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def make_tags(bm, ints=(), floats=()):
    for key in ints:
        bm.verts.layers.int.new(key)
    for key in floats:
        bm.verts.layers.float.new(key)


def tag_new(bm, before, **values):
    for key, value in values.items():
        layer = bm.verts.layers.float[key] if isinstance(value, float) else bm.verts.layers.int[key]
        for v in bm.verts:
            if v not in before:
                v[layer] = value


def read_tag(o, key):
    a = o.data.attributes[key]
    out = np.zeros(len(o.data.vertices), dtype=float if a.data_type == "FLOAT" else int)
    a.data.foreach_get("value", out)
    return out


# ---------- the shell ----------
def rim_z(t):
    """The rim's height round it: t = 0 its front. Raised over the neck and over the tail, low along its sides."""
    front = math.cos(t) ** 2 * (math.cos(t) > 0) * 1.0
    back = math.cos(t) ** 2 * (math.cos(t) < 0) * 1.0
    return 0.215 + 0.1 * front ** 3 + 0.075 * back ** 3


def dome_point(s, t):
    """A point of the carapace: s from the crown (0) to the rim (1) (how far out it lies seen from above), t round it from the front. A true dome:
    its height falls with s as an ellipse's does, so its sides round off into the rim instead of standing straight up."""
    r = min(s, 1.0)
    if s > 1.0:                                       # the rim's lip, flaring a little out and down
        r = 1.0 + 0.4 * (s - 1.0)
    zr = rim_z(t)
    zz = zr + (SHELL_TOP - zr) * max(0.0, 1 - min(s, 1.0) ** 2) ** 0.62 - (0.12 * (s - 1.0) if s > 1.0 else 0.0)
    return V(SHELL_C.x + SHELL_A * r * math.sin(t), SHELL_C.y - SHELL_B * r * math.cos(t), zz)


def build_shell():
    m = Mesh()
    ns, nt = 40, 96
    rings = []
    for i in range(ns + 1):
        s = 1.08 * (0.02 + 0.98 * i / ns)
        rings.append([m.bm.verts.new(dome_point(s, TAU * k / nt)) for k in range(nt)])
    under = [m.bm.verts.new(dome_point(1.08, TAU * k / nt) * 1.0 - V(0, 0, 0.03) - (dome_point(1.08, TAU * k / nt) - SHELL_C - V(0, 0, dome_point(1.08, TAU * k / nt).z)) * 0.06) for k in range(nt)]
    for i in range(ns):
        for k in range(nt):
            k2 = (k + 1) % nt
            m.bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    for k in range(nt):
        k2 = (k + 1) % nt
        m.bm.faces.new((rings[ns][k], rings[ns][k2], under[k2], under[k]))
    m.bm.faces.new(list(reversed(under)))
    crown = m.bm.verts.new(V(SHELL_C.x, SHELL_C.y, SHELL_TOP))
    for k in range(nt):
        m.bm.faces.new((crown, rings[0][k], rings[0][(k + 1) % nt]))
    # the plastron beneath, and the bridges joining it to the carapace between the legs
    m.ball(V(0, 0.02, 0.17), (0.3, 0.4, 0.05), 48, 20)
    for side in (1, -1):
        m.ball(V(side * 0.3, 0.01, 0.2), (0.09, 0.16, 0.05), 32, 16)
    o = m.finish(N + "ShellHi", HI)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.004, "adaptivity": 0.0}), ("SMOOTH", {"factor": 0.6, "iterations": 4})])
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- the skin: neck and head, legs, tail ----------
def leg_path(knots, side, per=8):
    return catmull([mir(p, side) for p in knots], per)


def build_skin():
    m = Mesh()
    m.tube(catmull(NECK, 8), lambda f: prof(((0, 0.075), (0.4, 0.062), (1, 0.05)), f), sides=32)
    m.ball(NECK[0] + V(0, 0.02, -0.01), (0.09, 0.07, 0.07), 32, 18)               # the neck's root, deep in the shell
    m.ball(HEAD_C, HEAD_R, 40, 28)
    m.tube(catmull([HEAD_C + V(0, -0.03, -0.004)] + SNOUT, 6), lambda f: 0.032 - 0.02 * f, sides=28, flat=1.25)     # the upper beak, hooking down at its tip
    m.tube(catmull([V(0, -0.64, 0.408), V(0, -0.7, 0.402), V(0, -0.745, 0.404)], 6), lambda f: 0.032 - 0.016 * f, sides=24, flat=1.25)     # the lower jaw
    for side in (1, -1):
        m.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.004, (EYE_R * 1.15,) * 3, 24, 16)      # the eye's socket
        m.tube(catmull([mir(p, side) for p in (V(0.022, -0.69, 0.472), V(0.048, -0.682, 0.474), V(0.066, -0.66, 0.462))], 6),
               lambda f: 0.009 * math.sin(math.pi * (0.1 + 0.8 * f)) ** 0.5 + 0.003, sides=16)     # the brow ridge
        m.ball(V(side * 0.04, -0.645, 0.408), (0.024, 0.03, 0.022), 24, 14)          # the cheek
        for knots, radii in ((FORE, FORE_R), (HIND, HIND_R)):
            path = leg_path(knots, side)
            m.tube(path, lambda f, r=radii: float(np.interp(f, np.linspace(0, 1, len(r)), r)), sides=28)
            foot = mir(knots[-1], side)
            m.ball(foot + V(0, 0, -0.02), (0.075, 0.08, 0.045), 32, 18)                # the foot, a broad pad on the ground
    m.tube(catmull(TAIL, 6), lambda f: 0.042 * (1 - f) ** 0.8 + 0.006, sides=20)
    o = m.finish(N + "SkinHi", HI)
    apply_mods(o, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.003, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 6})])
    # flatten the feet's soles onto the ground
    P = verts(o)
    low = P[:, 2] < 0.004
    P[low, 2] = 0.0 + 0.0 * P[low, 2]
    P[:, 2] = np.maximum(P[:, 2], 0.0)
    set_verts(o, P)
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


# ---------- the sundial: the gnomon and its gold edge ----------
def crown_z(y):
    """The shell's height along its middle line at this y."""
    best = 0.0
    for i in range(200):
        s = i / 200
        for t in (0.0, math.pi):
            p = dome_point(s, t)
            if abs(p.y - y) < 0.006:
                best = max(best, p.z)
    return best


def gnomon_outline():
    f, b, h = GNOMON
    zf, zb = crown_z(f.y), crown_z(b.y)
    base_f, base_b = V(0, f.y, zf - 0.03), V(0, b.y, zb - 0.03)        # (sunk into the crown)
    apex = V(0, b.y - 0.02, zb + h)
    return base_f, base_b, apex


def build_gnomon(name, coll, thick=0.014):
    """A plate of bronze: a right triangle standing along its spine, its long edge sloping up from the front to the tall back edge; bevelled."""
    base_f, base_b, apex = gnomon_outline()
    m = Mesh()
    nu, nv = 30, 30

    def point(u, v):
        # u along the base, front to back; v from the base up toward the sloped edge; the front tip a small edge, never a point
        uu = 0.04 + 0.96 * u
        p0 = base_f.lerp(base_b, uu)
        top = base_f.lerp(apex, uu)
        return tuple(p0.lerp(top, v))
    m.sheet(point, lambda u, v: thick * (0.4 + 0.6 * math.sqrt(max(0.0, 1 - (2 * v - 1) ** 8))), nu, nv)
    return m.finish(name, coll)


def build_gnomon_edge(name, coll, sides=10, per=12):
    base_f, base_b, apex = gnomon_outline()
    m = Mesh()
    a = base_f.lerp(apex, 0.06)
    pts = [a.lerp(apex, k / per) for k in range(per + 1)]
    m.tube(pts, lambda f: 0.0042, sides=sides)
    return m.finish(name, coll)


# ---------- the face: eyes, lids, brows, the chin tuft; nails ----------
def eye_frames():
    return {tag: EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=-6.0) for side, tag in ((1, "L"), (-1, "R"))}


def strand_paths(side):
    """The long white brow over each eye: wisps from the brow ridge, sweeping back and out and drooping."""
    out = []
    for k in range(10):
        f = (k % 5) / 4
        layer = k // 5                                   # two layers, the lower one shorter and drooping more; spaced wider than a strand is thick (closer, they z-fought)
        root = mir(V(0.016 + 0.052 * f + 0.006 * layer, -0.692 + 0.032 * f, 0.477 - 0.009 * f - 0.011 * layer), side)
        d = mir(V(0.55 + 0.2 * f, 0.75, 0.2 - 0.2 * layer), side).normalized()
        length = (0.09 + 0.04 * math.sin(math.pi * (0.3 + 0.7 * f))) * (1 - 0.25 * layer)
        pts = [root - d * 0.006]
        for j in range(1, 7):
            q = j / 6
            pts.append(root + d * (length * q) + mir(V(0.004 * f * q, 0, -(0.05 + 0.05 * layer) * q * q), side))      # flowing back and out, drooping at their ends
        out.append(pts)
    return out


def build_hair(name, coll, sides=6, per=4):
    m = Mesh()
    make_tags(m.bm, ints=("kind",))
    for side, kind in ((1, 0), (-1, 1)):
        for path in strand_paths(side):
            before = set(m.bm.verts)
            m.tube(catmull(path, per), lambda f: 0.0032 * (1 - f) ** 0.9 + 0.0006, sides=sides)
            tag_new(m.bm, before, kind=kind)
    return m.finish(name, coll)


def nail_list():
    """Each nail: (foot key, root, tip). Five blunt nails on a forefoot, four on a hind foot, round its front edge."""
    out = []
    for side, tag in ((1, "L"), (-1, "R")):
        for key, knots, count in (("F", FORE, 5), ("B", HIND, 4)):
            foot = mir(knots[-1], side) + V(0, 0, -0.02)
            for k in range(count):
                a = (k - (count - 1) / 2) * 0.38 + side * 0.15
                d = V(math.sin(a), -math.cos(a), 0)
                root = foot + d * 0.06 + V(0, 0, 0.01)
                tip = root + d * 0.016 + V(0, 0, -0.01)
                out.append((key + tag, root - d * 0.01, tip))
    return out


def build_nails(name, coll, sides=8, per=3):
    m = Mesh()
    make_tags(m.bm, ints=("foot",))
    keys = {"FL": 0, "FR": 1, "BL": 2, "BR": 3}
    for key, root, tip in nail_list():
        before = set(m.bm.verts)
        m.tube([root.lerp(tip, k / per) for k in range(per + 1)], lambda f: 0.0085 * (1 - f) ** 0.6 + 0.0025, sides=sides)
        tag_new(m.bm, before, foot=keys[key])
    return m.finish(name, coll)


# ---------- painting ----------
def cells2(p, centres):
    """Nearest and second-nearest centre (2D), and which."""
    d = np.linalg.norm(p[:, None, :] - centres[None, :, :], axis=2)
    order = np.argsort(d, axis=1)
    i1 = order[:, 0]
    d1 = d[np.arange(len(p)), i1]
    d2 = d[np.arange(len(p)), order[:, 1]]
    return d1, d2, i1


SCUTES = np.array([(0, -0.72), (0, -0.36), (0, 0.0), (0, 0.36), (0, 0.72),
                   (0.56, -0.55), (0.6, -0.18), (0.6, 0.18), (0.56, 0.55), (-0.56, -0.55), (-0.6, -0.18), (-0.6, 0.18), (-0.56, 0.55)])


def shell_coords(P):
    """Each point: where it lies on the dome seen from above (unit disc), how far out (0 crown, 1 rim) and round (0 front)."""
    u = (P[:, 0] - SHELL_C.x) / SHELL_A
    v = (P[:, 1] - SHELL_C.y) / SHELL_B
    r = np.hypot(u, v)
    t = np.arctan2(u, -v) % TAU
    return u, v, r, t


def dome_s(r):
    """The dome's s from how far out a point lies seen from above (they are the same)."""
    return np.clip(r, 0, 1.2)


def numeral_mask(t, rad, hours=12):
    """Numerals of bars and dots, one per hour round the dial, just outside its ring: hour k has (k // 5) bars and (k % 5) dots."""
    out = np.zeros(len(t))
    for k in range(hours):
        a0 = TAU * (k + 0.5) / hours
        da = ((t - a0 + math.pi) % TAU) - math.pi
        local_x = da * rad                  # across, in dial units (a ring's radius is 1)
        local_y = rad - 1.1                 # out from just beyond the ring (it was once set inside the ring and masked away: no numerals showed)
        n = k + 1
        bars, dots = n // 5, n % 5
        for b in range(bars):
            y0 = 0.03 + 0.07 * b
            out = np.maximum(out, (np.abs(local_x) < 0.13) * (np.abs(local_y - y0) < 0.018))
        for d in range(dots):
            x0 = (d - (dots - 1) / 2) * 0.075
            y0 = 0.03 + 0.07 * bars + 0.01
            out = np.maximum(out, (np.hypot(local_x - x0, local_y - y0) < 0.026) * 1.0)
    return out


def shell_fields(P, Nn):
    """The shell's carving, per point: the seams between scutes, growth rings, and the dial: its ring, hour lines and numerals."""
    u, v, r, t = shell_coords(P)
    s = dome_s(r)
    top = Nn[:, 2] > -0.2
    marginal = s > 0.86
    d1, d2, own = cells2(np.stack([u, v], 1), SCUTES)
    seam = (1 - smooth(0.0, 0.05, d2 - d1)) * (~marginal) * top
    # the marginals: a row of plates round the rim, each its own
    mk = np.floor(t / (TAU / 24)).astype(int)
    mf = t / (TAU / 24) - mk
    mseam = marginal * ((1 - smooth(0.0, 0.08, mf)) + (1 - smooth(0.0, 0.08, 1 - mf))) + (1 - smooth(0.0, 0.015, np.abs(s - 0.86)))
    seam = np.clip(np.maximum(seam, mseam * top), 0, 1)
    edge_d = np.where(marginal, np.minimum(np.minimum(mf, 1 - mf) * 0.5, np.abs(s - 0.86) * 2 + 0.0), d2 - d1)      # how far in from its scute's edge
    growth = (0.5 + 0.5 * np.sin(edge_d * 95)) * smooth(0.0, 0.03, edge_d) * (1 - smooth(0.12, 0.2, edge_d))      # growth rings following its outline, an old one's
    # the dial: a bronze ring round the crown, hour lines fanning from the gnomon's foot to it, numerals outside it
    rad = s / DIAL_S                                       # 1 at the ring
    ring = (1 - smooth(0.025, 0.05, np.abs(rad - 1.0))) * top
    hour = np.zeros(len(P))
    for k in range(12):
        a = TAU * k / 12
        da = np.abs(((t - a + math.pi) % TAU) - math.pi)
        hour = np.maximum(hour, (1 - smooth(0.012, 0.024, da * np.maximum(rad, 0.15) * 0.55)) * smooth(0.18, 0.25, rad) * (rad < 1.0))
    hour *= top
    nums = numeral_mask(t, rad) * top * (rad > 1.0)
    dome = smooth(0.0, 0.16, edge_d)                     # each scute a little domed
    return seam, growth, ring, hour, nums, own, s, dome


def carve_shell(o):
    P, Nn = verts(o), normals(o)
    seam, growth, ring, hour, nums, own, s, dome = shell_fields(P, Nn)
    d = -0.007 * seam + 0.005 * dome - 0.0012 * growth * (1 - seam) - 0.0018 * hour - 0.0018 * nums + 0.0018 * ring
    set_verts(o, P + Nn * d[:, None])


def paint_shell(o):
    P, Nn = verts(o), normals(o)
    seam, growth, ring, hour, nums, own, s, dome = shell_fields(P, Nn)
    shade = hash01(own.astype(np.int64), np.zeros(len(P), dtype=np.int64), np.zeros(len(P), dtype=np.int64), 4)
    col = mix(np.broadcast_to(STONE, (len(P), 3)), STONE_DEEP, 0.3 * shade + 0.35 * growth)
    col = mix(col, STONE_PALE, smooth(0.45, 0.85, fbm(P, 9.0, 4, 2)) * 0.35)
    col = mix(col, STONE_DEEP * 0.75, smooth(0.55, 0.85, fbm(P, 40.0, 3, 7)) * 0.3)          # weathered: pitted, stained
    col = mix(col, STONE_PALE * 1.05, dome * smooth(0.6, 0.9, fbm(P, 18.0, 2, 3)) * 0.3)      # each scute's middle worn paler
    col = mix(col, SEAM * 1.3, (1 - smooth(0.0, 0.05, np.abs(s - 1.0))) * 0.5)                # grime at the rim
    col = mix(col, LICHEN, smooth(0.62, 0.8, fbm(P, 14.0, 3, 6)) * 0.45 * (1 - smooth(0.0, 0.5, s)))      # lichen on its old crown
    col = mix(col, SEAM, seam * 0.85)
    under = smooth(-0.1, -0.6, Nn[:, 2])
    col = mix(col, rgb(196, 176, 130), under * 0.6)                   # the plastron, paler
    bronze = np.clip(np.maximum.reduce([ring, hour, nums]), 0, 1)
    patina = smooth(0.55, 0.75, fbm(P, 22.0, 3, 9))
    metal_col = mix(mix(np.broadcast_to(BRONZE, (len(P), 3)), BRONZE_DARK, 0.3 * shade), VERDIGRIS, patina * 0.75)
    col = mix(col, metal_col, bronze)
    rough = 0.75 - 0.35 * bronze * (1 - patina * 0.6)
    paint(o, np.clip(col, 0, 1), rough, bronze * (1 - patina) * 0.85)


def paint_gnomon(o):
    P, Nn = verts(o), normals(o)
    base_f, base_b, apex = gnomon_outline()
    up = (P[:, 2] - np.interp(P[:, 1], [base_f.y, base_b.y], [base_f.z, base_b.z])) / max(1e-6, apex.z - base_b.z)      # 0 at its foot, 1 at its tip
    edge_wear = 1 - smooth(0.0, 0.25, np.abs(Nn[:, 0]))               # the bevelled edges, rubbed bright
    col = mix(np.broadcast_to(BRONZE, (len(P), 3)), BRONZE_DARK, 0.3 + 0.2 * fbm(P, 16.0, 3, 12))
    col = mix(col, rgb(214, 170, 96), edge_wear * 0.6)
    # an engraved line of numerals along its face, a little below its sloped edge; verdigris in the engraving and rising from its foot
    slope = np.interp(P[:, 1], [base_f.y, base_b.y], [base_f.z, apex.z])
    band = (np.abs(P[:, 2] - (slope - 0.04)) < 0.007) * (np.sin(P[:, 1] * 260) > 0.2) * (P[:, 1] > base_f.y + 0.05)
    patina = np.clip(band + (1 - smooth(0.0, 0.25, up)) * smooth(0.35, 0.65, fbm(P, 30.0, 3, 12)), 0, 1)
    col = mix(col, VERDIGRIS, patina * 0.8)
    paint(o, np.clip(col, 0, 1), 0.38 + 0.3 * patina, (1 - patina) * 0.9)


def paint_skin(o):
    P, Nn = verts(o), normals(o)
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    # leathery and scaled: small scales over its neck and legs; big overlapping plates down the front of its forelegs
    d1, d2, _ = cells_3d(P, 70.0, 3)
    scale = smooth(0.0, 0.12, d2 - d1)
    col = mix(np.broadcast_to(SKIN, (len(P), 3)), SKIN_DEEP, (1 - scale) * 0.6)
    col = mix(col, SKIN_PALE, smooth(0.4, 0.9, fbm(P, 12.0, 3, 4)) * 0.25)
    fore = np.zeros(len(P))
    for side in (1, -1):
        f, dd = nearest_on(leg_path(FORE, side), P)
        fore = np.maximum(fore, (dd < 0.08) * smooth(0.25, 0.4, f) * smooth(-0.2, -0.7, Nn[:, 1]) * (x * side > 0))
    b1, b2, bown = cells_3d(P, 30.0, 8)
    plate = smooth(0.0, 0.1, b2 - b1)
    col = mix(col, mix(np.broadcast_to(rgb(120, 110, 90), (len(P), 3)), rgb(150, 140, 112), bown * 0.6), fore * plate * 0.8)      # (a 1-D weight: an (N, 1) one broadcast to N x N and took all the memory)
    col = mix(col, SKIN_DEEP * 0.7, fore * (1 - plate) * 0.7)
    # the neck's wrinkles: rings of fold
    fn, dn = nearest_on(catmull(NECK, 8), P)
    on_neck = (dn < 0.09) & (fn < 0.95)
    wrinkle = 0.5 + 0.5 * np.sin(fn * 60 + 4 * np.sin(np.arctan2(x, z - 0.35) * 3))
    col = mix(col, SKIN_DEEP, on_neck * smooth(0.6, 0.95, wrinkle) * 0.55)
    # its head: the beak of dark horn, its edge paler; the mouth line
    hd = np.linalg.norm((P - np.array(tuple(HEAD_C + V(0, -0.05, -0.02)))) / np.array((0.04, 0.03, 0.035)), axis=1)
    beak = (y < -0.7) * smooth(1.6, 1.0, hd)
    col = mix(col, HORN, beak * 0.9)
    mouth = (np.abs(z - np.interp(y, [-0.74, -0.7, -0.64], [0.41, 0.413, 0.418])) < 0.003) * (y < -0.63) * (np.abs(x) < 0.05)
    col = mix(col, SKIN_DEEP * 0.4, mouth)
    # the soles, worn pale
    col = mix(col, rgb(120, 112, 96), smooth(0.03, 0.0, z) * 0.6)
    paint(o, np.clip(col, 0, 1), 0.62 - 0.1 * (1 - scale), np.zeros(len(P)))


def cells_3d(P, f, seed=0):
    q = P * f
    base = np.floor(q).astype(np.int64)
    d1 = np.full(len(P), 1e9)
    d2 = np.full(len(P), 1e9)
    own = np.zeros(len(P))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                off = np.stack([hash01(c[:, 0], c[:, 1], c[:, 2], seed + k) for k in (1, 2, 3)], 1)
                d = np.linalg.norm(q - c - off, axis=1)
                nearer = d < d1
                d2 = np.where(nearer, d1, np.minimum(d2, d))
                own = np.where(nearer, hash01(c[:, 0], c[:, 1], c[:, 2], seed + 4), own)
                d1 = np.where(nearer, d, d1)
    return d1, d2, own


def knap_skin(o):
    """The scales raised a little, the neck's folds pressed in."""
    P, Nn = verts(o), normals(o)
    d1, d2, _ = cells_3d(P, 70.0, 3)
    scale = smooth(0.0, 0.12, d2 - d1)
    fn, dn = nearest_on(catmull(NECK, 8), P)
    wrinkle = 0.5 + 0.5 * np.sin(fn * 60 + 4 * np.sin(np.arctan2(P[:, 0], P[:, 2] - 0.35) * 3))
    on_neck = (dn < 0.09) & (fn < 0.95)
    b1, b2, _ = cells_3d(P, 30.0, 8)
    plate = smooth(0.0, 0.1, b2 - b1)
    legs = np.zeros(len(P))
    for side in (1, -1):
        for knots in (FORE, HIND):
            f, dd = nearest_on(leg_path(knots, side), P)
            legs = np.maximum(legs, (dd < 0.1) * smooth(0.3, 0.45, f))
    d = 0.0012 * scale - 0.0035 * on_neck * smooth(0.6, 0.95, wrinkle) + 0.004 * plate * legs
    set_verts(o, P + Nn * d[:, None])


def eye_paint(o, fr):
    """An old tortoise's eye: near-black and glossy, a thin ring of amber round its pupil."""
    px, py, a = eye_coords(o, fr)
    r = np.where(a > 0, np.hypot(px, py), 3.0)
    col = mix(rgb(90, 58, 22), rgb(16, 12, 8), smooth(0.55, 0.85, r))
    col = mix(col, rgb(8, 6, 4), 1 - smooth(0.32, 0.4, r))
    paint(o, np.clip(col, 0, 1), np.full(len(px), 0.05), np.zeros(len(px)))


def paint_hair(o):
    P = verts(o)
    n = len(P)
    col = mix(np.broadcast_to(HAIR, (n, 3)), rgb(206, 202, 192), 0.3 * (0.5 + 0.5 * np.sin(P[:, 0] * 900 + P[:, 2] * 400)))
    paint(o, col, np.full(n, 0.6), np.zeros(n))


def show_glows(glows):
    for o in glows.values():
        mat = bpy.data.materials.new(o.name)
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        h = o.name[-6:]
        c = rgb(int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16))
        g.inputs["Base Color"].default_value = (0, 0, 0, 1)
        g.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1)
        g.inputs["Emission Strength"].default_value = 2.5
        o.data.materials.append(mat)
        o.visible_shadow = False


# ---------- the whole, high-detail ----------
def build_hi(clay=False):
    pieces, data = {}, {}
    pieces["Shell"] = build_shell()
    pieces["Skin"] = build_skin()
    frames = eye_frames()
    for tag, fr in frames.items():
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, SKIN, SKIN_DEEP * 0.5)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, SKIN, SKIN_DEEP * 0.6, lower_share=0.8)
    pieces["Gnomon"] = build_gnomon(N + "GnomonHi", HI)
    pieces["Hair"] = build_hair(N + "HairHi", HI)
    pieces["Nails"] = build_nails(N + "NailsHi", HI)
    glows = {"Edge": build_gnomon_edge(N + "Edge_Glow_" + GOLD_HEX, HI),
             "Glints": glints(frames, HI, "Glints_Glow_ffffff", spots=((-24, 22, 0.0042, 10), (20, -16, 0.002, 6)))}
    if not clay:
        carve_shell(pieces["Shell"])
        paint_shell(pieces["Shell"])
        knap_skin(pieces["Skin"])
        paint_skin(pieces["Skin"])
        paint_gnomon(pieces["Gnomon"])
        paint_hair(pieces["Hair"])
        plain(pieces["Nails"], NAIL, 0.5)
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
    return pieces, frames, glows, data


VIEWS = [(0, -1, 0.12), (0.62, -0.72, 0.28), (1, 0, 0.08), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.25, -0.3, -0.9)]
VIEW_AT = (0, -0.05, 0.4)
FACE_AT = (0, -0.68, 0.44)
EXTRA = [(0, -1, 0.1, 0.45, FACE_AT), (0.62, -0.75, 0.2, 0.45, FACE_AT), (1, -0.15, 0.1, 0.45, FACE_AT), (0.2, 0.0, 1, 1.2, (0, 0.03, 0.75)),
         (0.7, -0.5, 0.3, 0.5, (0.3, -0.38, 0.08)), (0.9, 0.2, 0.5, 1.0, (0, 0.05, 0.85))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows, data = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
    else:
        mat = hi_material(ao_distance=0.05, ao_share=0.4)
        b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        attr = mat.node_tree.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "metal"
        mat.node_tree.links.new(attr.outputs["Fac"], b.inputs["Metallic"])      # (review only: the bake stage leaves the metal to its own pass)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    shots(os.path.join(REVIEW, STAGE), VIEWS + EXTRA, target=VIEW_AT, dist=3.2, size=640)
    print("DONE", flush=True)


# ---------- the game mesh ----------
SHELL_QUADS, SKIN_QUADS = 2200, 3000
SCALES = {"Shell": 1.35, "EyeL": 2.0, "EyeR": 2.0, "LidUL": 1.0, "LidUR": 1.0, "LidLL": 1.0, "LidLR": 1.0, "Gnomon": 1.3, "Hair": 0.5, "Nails": 0.6}


def build_low(pieces, frames):
    lows = {"Skin": retopo_skin(pieces["Skin"], N + "SkinLow", SKIN_QUADS), "Shell": retopo_skin(pieces["Shell"], N + "ShellLow", SHELL_QUADS)}
    P = verts(lows["Skin"])
    P[:, 2] = np.maximum(P[:, 2], 0.0)                 # the soles on the ground: the re-mesh rounded them a few millimetres under it
    set_verts(lows["Skin"], P)
    for tag, fr in frames.items():
        lows["Eye" + tag] = low_eye(fr, N + "Eye" + tag + "Low", 20, 12)
        lows["LidU" + tag] = low_lid(fr, True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(fr, False, N + "LidL" + tag + "Low")
    m = Mesh()
    base_f, base_b, apex = gnomon_outline()
    m.sheet(lambda u, v: tuple(base_f.lerp(base_b, 0.04 + 0.96 * u).lerp(base_f.lerp(apex, 0.04 + 0.96 * u), v)), lambda u, v: 0.014 * (0.4 + 0.6 * math.sqrt(max(0.0, 1 - (2 * v - 1) ** 8))), 6, 6)
    lows["Gnomon"] = m.finish(N + "GnomonLow", GAME)
    lows["Hair"] = build_hair(N + "HairLow", GAME, sides=4, per=1)
    lows["Nails"] = build_nails(N + "NailsLow", GAME, sides=5, per=1)
    for o in lows.values():
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    triangulate(lows)
    return lows


def shell_uv(o, density):
    """The shell's own UVs: the projection's charts as seams, a cut round the plastron's edge, then an angle-based unwrap, which can't fold a chart over
    itself (projected straight down, the plastron and the overhang above it, one chart, landed on each other)."""
    select_only([o])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(40), island_margin=0.004, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.seams_from_islands()
    bpy.ops.object.mode_set(mode="OBJECT")
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for e in bm.edges:
        faces = e.link_faces
        mid = (e.verts[0].co + e.verts[1].co) / 2
        if len(faces) == 2 and all(f.normal.z < -0.4 for f in faces) and 0.16 < mid.z < 0.205:
            e.seam = True
    bm.to_mesh(o.data)
    bm.free()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.003)
    bpy.ops.object.mode_set(mode="OBJECT")
    scale_uv_to(o, list(o.data.polygons), density)


# ---------- the skeleton ----------
BODY_AT = V(0, 0.03, 0.36)
NECK_HEADS = (("Neck1", NECK[0].copy(), "Body"), ("Neck2", path_at(catmull(NECK, 8), 0.45), "Neck1"), ("Head", path_at(catmull(NECK, 8), 0.92), "Neck2"))
JAW_AT = V(0, -0.635, 0.41)
TAIL_AT = TAIL[0].copy()
LEGS = (("FL", 1, FORE), ("FR", -1, FORE), ("BL", 1, HIND), ("BR", -1, HIND))
BROW_AT = V(0.04, -0.686, 0.474)


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None), ("Body", BODY_AT.copy(), "Root")]
    bones += list(NECK_HEADS)
    bones.append(("Jaw", JAW_AT.copy(), "Head"))
    for tag, fr in frames.items():
        bones += [("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head")]
    for side, tag in ((1, "L"), (-1, "R")):
        bones.append(("Brow" + tag, mir(BROW_AT, side), "Head"))
    bones.append(("Tail", TAIL_AT, "Body"))
    for key, side, knots in LEGS:
        bones += [("Leg%s1" % key, mir(knots[0], side), "Body"), ("Leg%s2" % key, mir(knots[1], side), "Leg%s1" % key), ("Foot" + key, mir(knots[2], side), "Leg%s2" % key)]
    return armature(bones)


def blend(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v * t
    return {k: v for k, v in out.items() if v > 1e-4}


def skin_weights(P):
    """The neck from the shell to the head, the head wholly the head's, the jaw under it; each leg from inside the shell to its foot; the tail."""
    neck_path = catmull(NECK, 8)
    nf, nd = nearest_on(neck_path, P)
    heads = np.array([tuple(at) for _, at, _ in NECK_HEADS])
    kf, _ = nearest_on(neck_path, heads)
    names = ["Body"] + [n for n, _, _ in NECK_HEADS]
    knots = (kf[0] * 0.5, (kf[0] + kf[1]) / 2, (kf[1] + kf[2]) / 2, kf[2] + 0.03)
    hz = np.linalg.norm((P - np.array(tuple(HEAD_C + V(0, -0.03, -0.005)))) / np.array((0.075, 0.115, 0.07)), axis=1)
    legs = []
    for key, side, knots_l in LEGS:
        path = leg_path(knots_l, side)
        lf, ld = nearest_on(path, P)
        kk, _ = nearest_on(path, np.array([tuple(mir(k, side)) for k in knots_l[:3]]))
        legs.append((key, side, lf, ld, kk))
    tf, td = nearest_on(catmull(TAIL, 6), P)
    out = []
    for i, (x, y, z) in enumerate(P):
        # which part of the skin: the nearest of neck, legs, tail
        best = ("neck", nd[i])
        for key, side, lf, ld, kk in legs:
            if ld[i] < best[1]:
                best = (key, ld[i])
        if td[i] < best[1]:
            best = ("tail", td[i])
        if best[0] == "neck":
            w = chain_weight(names, knots, float(nf[i]))
            if hz[i] < 1.2:
                w = blend(w, {"Head": 1.0}, float(smooth(1.2, 0.95, hz[i])))
            jaw = float(smooth(0.415, 0.405, z)) * float(smooth(-0.62, -0.66, y))
            if jaw > 0:
                w = blend(w, {"Jaw": 1.0}, jaw)
        elif best[0] == "tail":
            w = chain_weight(["Body", "Tail"], (0.05, 0.3), float(tf[i]))
        else:
            key, side, lf, ld, kk = next(l for l in legs if l[0] == best[0])
            mids = ((kk[0] + kk[1]) / 2, (kk[1] + kk[2]) / 2, kk[2] + 0.05)
            w = chain_weight(["Leg%s1" % key, "Leg%s2" % key, "Foot" + key], mids, float(lf[i]))
            if lf[i] < kk[0] + 0.02:
                w = blend({"Body": 1.0}, w, float(smooth(kk[0] - 0.05, kk[0] + 0.02, lf[i])))
        out.append(w)
    return out


def bind_all(lows, rig, glows):
    weigh(lows["Skin"], skin_weights(verts(lows["Skin"])))
    rigid(lows["Shell"], "Body")
    rigid(lows["Gnomon"], "Body")
    for tag in "LR":
        rigid(lows["Eye" + tag], "Head")
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    weigh(lows["Hair"], [{"BrowL" if k == 0 else "BrowR": 1.0} for k in read_tag(lows["Hair"], "kind")])
    feet = {0: "FootFL", 1: "FootFR", 2: "FootBL", 3: "FootBR"}
    weigh(lows["Nails"], [{feet[k]: 1.0} for k in read_tag(lows["Nails"], "foot")])
    rigid(glows["Edge"], "Body")
    weigh(glows["Glints"], [{"Head": 1.0} for _ in verts(glows["Glints"])])
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


# poses in the game's axes: the same numbers PetRig's animateTimekeeperTortoise uses. +X lifts what points forward; +Y turns to its left
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


# its stances in the game's axes, as searched in Blender (feet against the ground, torn skin, a head poking through its shell): the same numbers as
# PetRig's TORT_* tables. The walk: diagonal pairs; each leg swings at its shoulder, its knee lifting the foot (front legs one way, hind the other), the
# shoulder raised or lowered by the arc its swing would trace (a * sw + b * sw^2, measured), so a planted foot stays on the ground
LEADS = {"FL": 0.0, "BR": 0.0, "FR": math.pi, "BL": math.pi}
ARC = {"F": (0.0196, 0.0041), "B": (-0.01745, 0.00385)}
WALK_SWING, WALK_LIFT = 0.22, 0.6


def walk(phi):
    t = {}
    for key, off in LEADS.items():
        sw = math.sin(phi + off)
        lf = max(0.0, math.cos(phi + off))
        a1 = WALK_SWING * sw
        a2 = (1 if key[0] == "F" else -1) * WALK_LIFT * lf
        a, b = ARC[key[0]]
        t["Leg%s1" % key] = (a1, 0, 0, (0, -(a * sw + b * sw * sw), 0))
        t["Leg%s2" % key] = (a2, 0, 0)
        t["Foot" + key] = (-(a1 + a2), 0, 0)
    return t


def tucked():
    """Pulled into its shell: legs drawn up and in, folded (the forelegs across the corners of the front opening), the neck drawn back and down so its
    face peeks out of the opening between them (drawn back and up, it poked through the dome)."""
    t = {}
    for key in ("FL", "FR", "BL", "BR"):
        side = 1 if key[1] == "L" else -1
        front = key[0] == "F"
        t["Leg%s1" % key] = (0.0, 0, 0, (side * 0.05, 0.1, 0.03 if front else -0.03))
        t["Leg%s2" % key] = ((1 if front else -1) * 0.9, 0, 0)
    t.update({"Neck1": (-0.3, 0, 0, (0, -0.08, 0.22)), "Neck2": (0.3, 0, 0), "Head": (0.1, 0, 0)})
    return t


POSES = {"Walk0": walk(0.0), "Walk1": walk(math.pi / 4), "Walk2": walk(math.pi / 2), "Walk3": walk(3 * math.pi / 4), "Tuck": tucked(),
         "Plant": {"Neck1": (0.12, 0, 0), "Neck2": (0.12, 0, 0), "Head": (0.18, 0, 0), "BrowL": (-0.25, 0, 0), "BrowR": (-0.25, 0, 0)},
         "Look": {"Neck2": (0, 0.35, 0), "Head": (0.05, 0.45, 0.1)}, "Chew": {"Jaw": (-0.12, 0, 0)},
         "BrowUp": {"BrowL": (-0.3, 0, 0), "BrowR": (-0.3, 0, 0)}, "BrowDown": {"BrowL": (0.2, 0, 0), "BrowR": (0.2, 0, 0)}, "Tail": {"Tail": (0, 0.4, 0)}}


def pose_library(frames):
    out = {name: spec(table) for name, table in POSES.items()}
    for tag, fr in frames.items():
        out.setdefault("Blink", {})["LidU" + tag] = (tuple(fr.hinge), -40.0, (0, 0, 0))
        out["Blink"]["LidL" + tag] = (tuple(fr.hinge), 16.0, (0, 0, 0))
    return out


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


GROUND_PARTS = {"Feet": ("FootFL", "FootFR", "FootBL", "FootBR"), "Shell": ("Body",), "Head": ("Head", "Jaw"), "Tail": ("Tail",)}

if __name__ == "__main__" and STAGE == "all":
    pieces, frames, glows, data = build_hi()
    mat = hi_material(ao_distance=0.05, ao_share=0.4)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.4, 1))
    lows = build_low(pieces, frames)
    unwrap(lows, [(lambda p: p.center.y < -0.6, 1.8), (None, 1.0)], SCALES, margin=0.006, own_uv={"Shell": shell_uv})
    bake_all(lows, pieces, mat, size=1024, colour_size=2048, metal=True, fill=(0.6, 0.52, 0.4, 1), far=("Skin", "Shell"), reach=(0.004, 0.01), far_reach=(0.008, 0.02),
             reaches={"Hair": (0.002, 0.005), "Nails": (0.003, 0.008), "Gnomon": (0.004, 0.01)})
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for key in ("Edge", "Glints"):
        bpy.data.objects.remove(glows[key], do_unlink=True)          # first, so the game's pieces take their exact names
    glows = {"Edge": build_gnomon_edge(N + "Edge_Glow_" + GOLD_HEX, GAME, sides=6, per=4),
             "Glints": glints(frames, GAME, "Glints_Glow_ffffff", spots=((-24, 22, 0.0042, 8), (20, -16, 0.002, 5)))}
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames)
    body = bind_all(lows, rig, glows)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), "groups", len(body.vertex_groups), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for v in body.data.vertices), flush=True)
    print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(body.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    print("Z range", round(min(zs), 4), round(max(zs), 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    pose(rig, {})
    print("GROUND rest", lowest_of(body, GROUND_PARTS), flush=True)
    scene.cycles.samples = 28
    shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=3.2, size=640)
    lib = pose_library(frames)
    for name, row in pet_kit.stress_report(rig, body, lib).items():
        print("STRESS", name, row, flush=True)
    for name in lib:
        pose(rig, lib[name])
        print("GROUND", name, lowest_of(body, GROUND_PARTS), flush=True)
        shots(os.path.join(REVIEW, "pose" + name), [(0.62, -0.72, 0.3, 3.2, VIEW_AT), (1, -0.05, 0.1, 3.2, VIEW_AT)], target=VIEW_AT, size=480)
    pose(rig, {})
    for o in glows.values():
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    path = save_all((0.62, -0.72, 0.3, 3.2, VIEW_AT))      # first: the export takes the glow pieces' colours off
    print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
    print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)
