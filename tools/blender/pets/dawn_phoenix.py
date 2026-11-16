"""The Dawn Phoenix, The First Light (Mythical; Inferno Egg, Ember Peak): the model, built to the owner's directive (22 Worked Builds/Dawn Phoenix
Directive.md, November 16, 2026).

An ancient firebird of the first sunrise: noble, graceful, proud. A distinctive phoenix skull (a long face, a raised forehead, hard brows, a refined back
of the skull) with a powerful hooked beak in two parts and intelligent golden eyes; a long, graceful neck in an S, clad in layered feathers; a deep,
forward breast of cream and ivory feathers; a lean, streamlined body; two enormous wings, held slightly extended, built as a bird's are (shoulder,
upper arm, forearm, wrist and hand, ten primaries, twelve secondaries, tertials, the alula, and four layers of coverts); strong legs with three toes
forward and one back, each toe jointed and ending in a hooked bronze talon; a long, flowing tail fanned from the rump; and a crest of flame-shaped
feathers sweeping back from the crown. It is physical, not fire: its fire is in its shapes and its colours, the sky going from night to sunrise.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/dawn_phoenix.py -- [stage]

Stages (the directive's section 11): blockout | anatomy | wings | feathers | materials | final (= all). Each later stage builds on the earlier ones.
blockout, anatomy and wings each save their stage file (tools/blender/pets/InfernoEgg/Dawn_Phoenix_<Stage>.blend); final builds the game meshes (at most
20,000 triangles), bakes the painted detail into one set of maps, checks it, renders the QA set (renders/pets/InfernoEgg/DawnPhoenix_final/), writes
Dawn_Phoenix_Final.blend and the FBX (assets/pets/InfernoEgg/DawnPhoenix_Model/). Stage renders go to renders/pets/InfernoEgg/DawnPhoenix_stages/.
Faces -Y, Z up, 1 unit = 1 metre, +X is its left. The game files sit on the ground: its talons' lowest point is at z = 0.

How it is made: the skin is sculpted as one volume (overlapping forms fused by a voxel remesh and smoothed, as a sculpt base is) and retopologised
to even quads; the beak is lofted from a ridged cross-section; every feather is its own blade, laid by script (the repetitive geometry the directive
allows) row by row along the bones of the wing, the neck and the body, each lying over the root of the next.
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
from pet_kit import (EyeFrame, Mesh, V, apply_mods, build_eye, build_lid, catmull, eye_coords, hi_material, low_eye, low_lid, mir, mix,
                     nearest_on, normals, paint, rgb, set_verts, shots, smooth, stage_setup, tree_of, verts, TAU)

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "materials"
if STAGE == "all":
    STAGE = "final"
PET, EGG = "DawnPhoenix", "InfernoEgg"
N = PET + "_"
ORDER = ("blockout", "anatomy", "wings", "feathers", "materials", "final")
LEVEL = ORDER.index(STAGE)
ROOT = pet_kit.ROOT
STAGE_DIR = os.path.join(ROOT, "renders/pets", EGG, PET + "_stages", STAGE)
FINAL_DIR = os.path.join(ROOT, "renders/pets", EGG, PET + "_final")
BLEND_DIR = os.path.join(ROOT, "tools/blender/pets", EGG)
OUT_DIR = os.path.join(ROOT, "assets/pets", EGG, PET + "_Model")      # its own folder: the live pet's files are not touched before approval
os.makedirs(STAGE_DIR, exist_ok=True)
HI, GAME = pet_kit.start(PET, EGG)
pet_kit.OUT, pet_kit.TOOLS = OUT_DIR, BLEND_DIR

# ---------- colours: from the last of the night to the sunrise (the directive's palette) ----------
DEEP_CRIMSON = rgb(104, 12, 30)
CRIMSON = rgb(152, 20, 34)
BURNT = rgb(204, 82, 20)          # burnt orange
AMBER = rgb(226, 132, 28)         # warm amber
GOLDEN = rgb(242, 182, 52)        # golden yellow
PALE_GOLD = rgb(240, 210, 124)
CREAM = rgb(246, 232, 200)
IVORY = rgb(250, 243, 226)
CHAMPAGNE = rgb(236, 214, 164)
PEACH = rgb(250, 184, 140)
PALE_YELLOW = rgb(252, 236, 160)
BRONZE = rgb(72, 46, 28)          # legs: dark bronze
TALON = rgb(44, 30, 22)
LASH = rgb(96, 24, 18)

# ---------- the frame of it (metres; built in the air, the ground set at the end) ----------
CHEST = V(0, -0.065, 0.625)
BELLY = V(0, 0.05, 0.535)
RUMP = V(0, 0.175, 0.47)
SPINE = catmull([V(0, 0.245, 0.445), RUMP, BELLY, CHEST, V(0, -0.09, 0.69)], 8)
SPINE_R = ((0, 0.03), (0.18, 0.055), (0.45, 0.088), (0.75, 0.1), (1.0, 0.08))
NECK = catmull([V(0, -0.085, 0.69), V(0, -0.155, 0.77), V(0, -0.188, 0.85), V(0, -0.172, 0.93), V(0, -0.162, 0.995), V(0, -0.18, 1.04)], 8)
NECK_R = ((0, 0.072), (0.22, 0.052), (0.55, 0.04), (0.85, 0.036), (1.0, 0.037))
HEAD_C = V(0, -0.2, 1.07)
EYE_R = 0.0146
EYE_C = V(0.0275, -0.24, 1.078)
EYE_AXIS = V(0.44, -0.89, 0.07).normalized()
LID_UP, LID_LOW = (21.0, 116.0, 0.0016), (-33.0, -124.0, 0.0014)     # open, calm and intelligent: neither a stare nor a scowl
LID_TILT = 6.0
IRIS, PUPIL = 0.86, 0.3
BEAK_ROOT = V(0, -0.252, 1.062)
# the wing (left; the right mirrors x): shoulder, elbow (back), wrist (forward), the end of the hand: held slightly extended, a little raised
DIHEDRAL = math.radians(40)        # the wings raised in a broad V...
PITCH_ROOT, PITCH_TIP = math.radians(34), math.radians(-24)
# ...and twisted along its length as a bird's is: a plane that holds the fore-aft line is edge-on from the front and the back whatever its V. The inner
# wing is pitched trailing edge up (its upper side shows from the front), the hand turned the other way (its primaries face a camera behind and
# above: the player's), so the wing reads as a broad shape from every side.
ARM = [V(0.07, -0.005, 0.67), V(0.215, 0.07, 0.775), V(0.395, -0.02, 0.92), V(0.52, 0.012, 1.012)]
ARM_PATH = catmull(ARM, 12)
ARM_F = (0.0, 1 / 3, 2 / 3, 1.0)
# the leg (left): hip, hock (the drumstick, feathered, runs down and back to it), foot (the bare scaly tarsus runs down and forward)
LEG = [V(0.055, 0.075, 0.5), V(0.062, 0.115, 0.405), V(0.064, 0.055, 0.318)]
TAIL_ROOT = RUMP + V(0, 0.07, -0.02)
TAIL_DIR = V(0, 0.78, -0.62).normalized()


def along(path, f):
    k = f * (len(path) - 1)
    i = min(int(k), len(path) - 2)
    return path[i].lerp(path[i + 1], k - i)


def path_tan(path, f, reach=0.02):
    return (along(path, min(1.0, f + reach)) - along(path, max(0.0, f - reach))).normalized()


def prof(knots, f):
    a = np.array(knots)
    return float(np.interp(f, a[:, 0], a[:, 1]))


def arm_radius(f):
    return 0.04 - 0.024 * f


def hashf(a, b=0, c=0):
    """A repeatable 0..1 for a feather (its index, its side, its row)."""
    return pet_kit.hash01(int(a * 1000), int(b * 1000), int(c * 1000))


# ---------- feathers ----------
class Plume:
    """One feather standing free of the skin (flight, tail and crest feathers). root, direction, its face (which way its upper side looks); length and
    half-width; lift raises it over its neighbour as it goes out; tilt turns it like a slat of a blind; cup bows it across; droop bends it down along;
    curl sweeps its tip sideways; hook bends its tip toward its face. shape: "flight" (a broad root, the widest a fifth out, a long taper to a rounded
    point), "lance" (a flame-shaped feather: widest a third out, its edges waved, drawn to a long point) or "round" (a covert: a broad rounded end)."""

    def __init__(self, root, direction, length, width, face, lift=0.0, tilt=0.0, cup=0.005, droop=0.0, curl=0.0, hook=0.0, shape="flight", group=0,
                 f=0.0, sunk=0.01, wave=0.0, seed=0, taper=0.45):
        self.root, self.d, self.length, self.width = root.copy(), direction.normalized(), length, width
        up = face - self.d * self.d.dot(face)
        self.up = up.normalized()
        self.side = self.up.cross(self.d).normalized()
        self.lift, self.tilt, self.cup, self.droop, self.curl, self.hook, self.shape = lift, tilt, cup, droop, curl, hook, shape
        self.group, self.f, self.sunk, self.wave, self.seed, self.taper = group, f, sunk, wave, seed, taper

    def half(self, u):
        if self.shape == "flight":
            grow = 0.66 + 0.34 * min(1.0, u / 0.2) ** 0.6
            t0 = self.taper
            fall = 1.0 if u < t0 else max(0.05, ((1 - u) / (1 - t0)) ** (0.62 if t0 < 0.6 else 0.45))
            return self.width * grow * fall
        if self.shape == "lance":
            grow = (u / 0.32) ** 0.5 if u < 0.32 else 1.0
            fall = 1.0 if u < 0.32 else max(0.04, ((1 - u) / 0.68) ** 0.9)
            waves = 1 + self.wave * math.sin(u * 3 * math.pi + self.seed) * min(1.0, u * 2)
            return self.width * max(0.04, 0.4 + 0.6 * grow) * fall * waves
        if self.shape == "blunt":     # a secondary: broad all the way, its end cut round and a little asymmetric
            grow = 0.66 + 0.34 * min(1.0, u / 0.18) ** 0.6
            end = 1.0 if u < 0.78 else max(0.08, math.sqrt(max(0.0, 1 - ((u - 0.78) / 0.22) ** 2)))
            return self.width * grow * end
        return self.width * min(1.0, math.sin(math.pi * min(1.0, 0.1 + 0.9 * u) ** 0.42) + 0.05) ** 0.55 * (0.55 + 0.45 * min(1.0, u * 3.5))

    def point(self, u, v):
        w = 2 * v - 1
        half = self.half(u)
        L = self.length
        rise = self.lift * (0.6 + 0.4 * min(1.0, u * 3.0) ** 0.8) - self.sunk * max(0.0, 1 - u * 5)
        sweep = self.curl * L * u ** 2.2
        bend = self.hook * L * u ** 3 - self.droop * L * u * u
        return (self.root + self.d * L * u + self.side * (half * w + sweep) +
                self.up * (rise + bend + half * w * self.tilt + self.cup * (1 - w * w) * min(1.0, u * 4)))


class LongFeather:
    """A long tail feather along a curve: a broad base, an elongated body, a tapered tip; it twists a little as it flows."""

    def __init__(self, path, widths, face, twist=0.0, group=0, f=0.0, cup=0.007):
        self.path, self.widths, self.face, self.twist, self.group, self.f, self.cup = path, widths, face, twist, group, f, cup
        self.length = sum((path[i + 1] - path[i]).length for i in range(len(path) - 1))
        self.up = face
        self.shape = "long"
        # a frame carried along the curve with no turn of its own (parallel transport): measured against one fixed "up", the side flipped where the
        # tip curled toward that up, and the end folded over into a flat hook
        self.samples = 96
        sides = []
        t0 = path_tan(path, 0.0, 0.012)
        side = t0.cross(face).normalized()
        for i in range(self.samples + 1):
            t = path_tan(path, i / self.samples, 0.012)
            side = (side - t * t.dot(side)).normalized()
            sides.append(side.copy())
        self.sides = sides

    def half(self, u):
        return prof(self.widths, u)

    def point(self, u, v):
        w = 2 * v - 1
        t = path_tan(self.path, u, 0.012)
        k = u * self.samples
        i = min(int(k), self.samples - 1)
        side = self.sides[i].lerp(self.sides[i + 1], k - i)
        side = (side - t * t.dot(side)).normalized()
        up = side.cross(t).normalized()
        a = self.twist * u * u
        side, up = side * math.cos(a) + up * math.sin(a), up * math.cos(a) - side * math.sin(a)
        return along(self.path, u) + side * self.half(u) * w + up * self.cup * (1 - w * w) * min(1.0, u * 8)


class SkinFeather:
    """A contour feather lying on the skin: laid in the skin's tangent plane, then each point pressed back onto the surface and lifted off it, so it
    hugs the body; its root sunk in, its free end raised over the root of the feather it lies on."""

    def __init__(self, tree, root, direction, length, width, lift=0.0028, shape="round", group=0, f=0.0, seed=0):
        hit = tree.find_nearest(root)
        self.tree, self.root, self.n = tree, hit[0], hit[1]
        d = direction - self.n * self.n.dot(direction)
        self.d = d.normalized()
        self.up = self.n
        self.side = self.n.cross(self.d).normalized()
        self.length, self.width, self.lift, self.shape, self.group, self.f, self.seed = length, width, lift, shape, group, f, seed

    def half(self, u):
        if self.shape == "lance":
            grow = (u / 0.35) ** 0.5 if u < 0.35 else 1.0
            fall = 1.0 if u < 0.35 else max(0.05, ((1 - u) / 0.65) ** 0.8)
            return self.width * max(0.05, 0.45 + 0.55 * grow) * fall
        return self.width * min(1.0, math.sin(math.pi * min(1.0, 0.1 + 0.9 * u) ** 0.42) + 0.05) ** 0.55 * (0.55 + 0.45 * min(1.0, u * 3.5))

    def point(self, u, v):
        w = 2 * v - 1
        q = self.root + self.d * self.length * u + self.side * self.half(u) * w
        hit = self.tree.find_nearest(q)
        if hit[0] is None:
            return q
        rise = -0.0025 + (self.lift + 0.0025) * min(1.0, u / 0.3) ** 0.7 + 0.0008 * (1 - w * w)
        return hit[0] + hit[1] * rise


def feather_thick(u, v):
    return 0.0042 * (1 - u) + 0.0018


def crest_thick(u, v):
    return 0.0028 * (1 - u) + 0.0014


def skin_feather_thick(u, v):
    return 0.0016


def build_plumes(plumes, name, coll, nu, nv, thick=feather_thick):
    """One mesh of many feathers (closed blades). Per vertex: which feather, how far along, across, and whether it is the upper face."""
    m = Mesh()
    idx, uu, vv, top = [], [], [], []
    for k, p in enumerate(plumes):
        m.sheet(p.point, thick, nu, nv)
        for i in range(nu + 1):
            for j in range(nv + 1):
                for t in (1, 0):
                    idx.append(k)
                    uu.append(i / nu)
                    vv.append(j / nv)
                    top.append(t)
    o = m.finish(name, coll)
    return o, np.array(idx), np.array(uu), np.array(vv), np.array(top)


def build_low_plumes(plumes, name, coll, nu, nv, thick=feather_thick, res=None):
    """The game mesh's feathers: an upper and a lower face, not joined at the edge (joined, the shading rounds over the edge and the bake's rays
    bend off the feather: streaks along every one, seen on the Nebula Owl)."""
    m = Mesh()
    bm = m.bm
    idx, uu, vv, top = [], [], [], []
    for k, p in enumerate(plumes):
        if res:
            nu, nv = res(p)
        upper, lower = [], []
        for i in range(nu + 1):
            ru, rl = [], []
            u = i / nu
            for j in range(nv + 1):
                v = j / nv
                q = Vector(p.point(u, v))
                du = Vector(p.point(min(u + 1 / nu, 1), v)) - Vector(p.point(max(u - 1 / nu, 0), v))
                dv = Vector(p.point(u, min(v + 1 / nv, 1))) - Vector(p.point(u, max(v - 1 / nv, 0)))
                nrm = du.cross(dv)
                nrm = nrm.normalized() if nrm.length > 1e-9 else p.up
                t = thick(u, v) / 2
                ru.append(bm.verts.new(q + nrm * t))
                rl.append(bm.verts.new(q - nrm * t))
                idx += [k, k]
                uu += [u, u]
                vv += [v, v]
                top += [1, 0]
            upper.append(ru)
            lower.append(rl)
        for i in range(nu):
            for j in range(nv):
                bm.faces.new((upper[i][j], upper[i + 1][j], upper[i + 1][j + 1], upper[i][j + 1]))
                bm.faces.new((lower[i][j + 1], lower[i + 1][j + 1], lower[i + 1][j], lower[i][j]))
    o = m.finish(name, coll, recalc=False)
    return o, np.array(idx), np.array(uu), np.array(vv), np.array(top)


# ---------- the wings ----------
GROUPS = {"primary": 0, "secondary": 1, "tertial": 2, "greater": 3, "median": 4, "lesser": 5, "marginal": 6, "pcovert": 7, "alula": 8, "under": 9}


def wing_plumes(side):
    """The left wing (side 1) or the right (-1), built as a bird's, every row overlapping like shingles so the wing is one broad, layered surface:
    ten primaries off the hand (only the outer four parted into fingers at their tips, the eighth and ninth longest: a pointed wing), twelve
    secondaries in one continuous trailing edge, three tertials, then the greater coverts, the primary coverts and the alula over their roots, the
    median and lesser coverts over those, and small marginal coverts closing the leading edge; under the arm a row of underwing coverts. In each
    row every feather lies a little over the next (a steady lift), never tilted against its neighbour (alternate tilts read as a louvre)."""
    out = []
    OUT = V(side * math.cos(DIHEDRAL), 0, math.sin(DIHEDRAL))
    NRM0 = V(-side * math.sin(DIHEDRAL), 0, math.cos(DIHEDRAL))
    pf = [0.0]

    def frame(f):
        p = PITCH_ROOT + (PITCH_TIP - PITCH_ROOT) * float(smooth(0.35, 0.97, f))
        back = (V(0, 1, 0) * math.cos(p) + NRM0 * math.sin(p)).normalized()
        nrm = (NRM0 * math.cos(p) - V(0, 1, 0) * math.sin(p)).normalized()
        return back, nrm

    def on_arm(f):
        pf[0] = f
        return mir(along(ARM_PATH, f), side)

    def d(deg, n=0.0):        # deg: 0 straight out along the wing, 90 straight back; n: out of the wing's plane (at the feather's own place: on_arm first)
        back, nrm = frame(pf[0])
        a = math.radians(deg)
        return (OUT * math.cos(a) + back * math.sin(a) + nrm * n).normalized()

    def face_at(f):
        return (frame(f)[1] + V(0, 0.08, 0)).normalized()

    BACK = V(0, 1, 0)
    G = GROUPS
    p_len = (0.37, 0.43, 0.475, 0.495, 0.485, 0.455, 0.425, 0.4, 0.38, 0.36)        # outermost (p10) first
    p_deg = (3, 10, 17, 24, 29, 34, 39, 44, 49, 54)
    p_half = (0.036, 0.039, 0.042, 0.045, 0.05, 0.052, 0.053, 0.054, 0.055, 0.056)
    for k in range(10):
        f = 1.0 - k * 0.03
        fingered = k < 4
        out.append(Plume(on_arm(f), d(p_deg[k], 0.02), p_len[k], p_half[k], face_at(f), lift=0.0016 * k, tilt=0.0, cup=0.005, droop=0.0,
                         curl=0.0, hook=0.06 if fingered else 0.04, shape="flight", group=G["primary"], f=f, seed=k,
                         taper=(0.5 if fingered else 0.68)))
    for k in range(12):
        f = 0.665 - k * 0.046
        out.append(Plume(on_arm(f), d(82 + k * 1.4, -0.02), 0.29 - k * 0.004 + 0.004 * (hashf(k, 3) - 0.5), 0.058, face_at(f),
                         lift=0.016 + 0.0016 * k, tilt=0.0, cup=0.006, droop=0.03, shape="blunt", group=G["secondary"], f=f, seed=k))
    for k in range(3):
        f = 0.12 - k * 0.042
        out.append(Plume(on_arm(f) + V(0, 0.006, 0.002), d(94 + k * 5, -0.04), 0.25 - 0.02 * k, 0.054, face_at(f), lift=0.036 + 0.0016 * k,
                         tilt=0.0, cup=0.006, droop=0.03, shape="blunt", group=G["tertial"], f=f, seed=k))
    for k in range(14):
        f = 0.7 - k * 0.05
        out.append(Plume(on_arm(f) + BACK * 0.006, d(70 + k * 1.6, 0.0), 0.15 - 0.001 * k, 0.05, face_at(f), lift=0.03 + 0.0015 * k, tilt=0.0,
                         cup=0.006, droop=0.02, shape="round", group=G["greater"], f=f, seed=k))
    for k in range(7):
        f = 0.995 - k * 0.042
        out.append(Plume(on_arm(f) + BACK * 0.004, d(12 + k * 7.5, 0.0), 0.17 - 0.007 * k, 0.042, face_at(f), lift=0.03 + 0.0015 * k, tilt=0.0,
                         cup=0.005, droop=0.02, shape="flight", group=G["pcovert"], f=f, seed=k, taper=0.7))
    for k in range(3):
        f = 0.76 - k * 0.02
        out.append(Plume(on_arm(f) - BACK * 0.01 + frame(f)[1] * 0.004, d(-14 + k * 9, 0.04), 0.1 - 0.012 * k, 0.018, face_at(f), lift=0.046 + 0.0015 * k,
                         tilt=0.0, cup=0.004, droop=0.01, shape="lance", group=G["alula"], f=f, seed=k))
    for k in range(12):
        f = 0.93 - k * 0.075
        out.append(Plume(on_arm(f), d(62 + k * 1.2, 0.0), 0.105, 0.044, face_at(f), lift=0.048 + 0.0015 * k, tilt=0.0, cup=0.005, droop=0.015,
                         shape="round", group=G["median"], f=f, seed=k))
    for k in range(14):
        f = 0.95 - k * 0.07
        out.append(Plume(on_arm(f) - BACK * arm_radius(f) * 0.6, d(50, 0.0), 0.08, 0.036, face_at(f), lift=0.068 + 0.0014 * k, tilt=0.0, cup=0.004,
                         droop=0.01, shape="round", group=G["lesser"], f=f, seed=k))
    for k in range(10):
        f = 0.92 - k * 0.095
        out.append(Plume(on_arm(f) - BACK * arm_radius(f) * 0.95, d(36, 0.0), 0.055, 0.026, face_at(f), lift=0.064 + 0.0014 * k, tilt=0.0, cup=0.003,
                         droop=0.006, shape="round", group=G["marginal"], f=f, seed=k))
    for k in range(9):
        f = 0.85 - k * 0.09
        out.append(Plume(on_arm(f) + BACK * 0.004, d(72, -0.05), 0.12, 0.036, -face_at(f), lift=0.004 + 0.0014 * k, tilt=0.0, cup=0.004, droop=-0.01,
                         shape="round", group=G["under"], f=f, seed=k))
    return out


# ---------- the tail ----------
def tail_feathers():
    """The tail: two long, flowing central feathers, then four pairs fanning out shorter, each with a broad base, a long body and a tapered tip, its
    own curve. Outer ones lie under, the middle pair on top."""
    out = []
    fan_face = V(0, 0.62, 0.78).normalized()
    spec = [(0.0, 1.12, 0.044, 0.0, 0), (0.0, 1.0, 0.04, 0.0, 1)]      # the central pair: (angle, length, width, phase, which)
    for k, (a, length, width) in enumerate(((9, 0.78, 0.038), (17, 0.62, 0.036), (26, 0.5, 0.034), (35, 0.4, 0.032))):
        for s in (1, -1):
            spec.append((s * a, length, width, 0.0, 2 + 2 * k + (0 if s > 0 else 1)))
    for a, length, width, _, which in spec:
        r = math.radians(a)
        side_off = 0.018 if which == 0 else (-0.018 if which == 1 else 0.0)
        base_dir = (TAIL_DIR * math.cos(r) + V(1, 0, 0) * math.sin(r)).normalized()
        rank = 0 if which < 2 else (which - 2) // 2 + 1
        root = TAIL_ROOT + V(math.sin(r) * 0.03 + side_off, -0.004 * rank, 0.008 * (4 - rank) * 0.5 - 0.004 - (0.005 if which == 1 else 0.0))
        # its flow: down and back, then lifting at its end; the central pair in a long S
        pts = []
        for i in range(9):
            t = i / 8
            sway = (0.05 if which == 0 else 0.035 if which == 1 else 0.02 * math.copysign(1, a)) * math.sin(t * math.pi * 1.2) * length      # (the central pair sway together: apart, they closed into a loop seen from behind)
            lift = (0.3 if which < 2 else 0.22) * length * t ** 2.2 - 0.06 * length * math.sin(math.pi * t)
            pts.append(root + base_dir * length * t + V(sway, 0, lift))
        path = catmull(pts, 6)
        widths = ((0, width * 0.62), (0.12, width), (0.55, width * 0.92), (0.82, width * 0.6), (0.95, width * 0.28), (1.0, width * 0.08))
        out.append(LongFeather(path, widths, fan_face, twist=0.25 * (1 if a >= 0 else -1) * (1 if which >= 2 else 0.4), group=which,
                               f=a / 35 if which >= 2 else (0.02 if which == 0 else -0.02)))
    return out


def tail_coverts():
    """Upper tail coverts over the tail's root, so the feathers grow out of the body and not out of a seam."""
    out = []
    for k, a in enumerate((-30, -15, 0, 15, 30)):
        r = math.radians(a)
        dirn = (TAIL_DIR * math.cos(r) + V(1, 0, 0) * math.sin(r)).normalized()
        out.append(Plume(TAIL_ROOT + V(math.sin(r) * 0.02, -0.045, 0.03), dirn, 0.2 - 0.02 * abs(math.sin(r)), 0.034, V(0, 0.62, 0.78),
                         lift=0.012 + 0.004 * (2 - abs(k - 2)), cup=0.005, droop=0.02, shape="flight", group=k, f=a / 30, sunk=0.02))
    return out


# ---------- the crest ----------
def crest_plumes():
    """Flame-shaped feathers from the crown and the back of the skull, sweeping back along the line of flight, each its own length and curve: short at
    the forehead, longest from the crown, two at the sides of the back of the skull. Their edges are waved like a flame's, but they are feathers."""
    out = []
    rows = [  # (root from HEAD_C, direction, length, half-width, curl, hook, wave, splay)
        ((0, -0.03, 0.046), (0, 0.75, 0.85), 0.1, 0.015, 0.1, 0.0, 0.12, 0.0),
        ((0, -0.012, 0.052), (0, 0.85, 0.7), 0.165, 0.019, 0.12, 0.0, 0.16, 0.0),
        ((0, 0.008, 0.052), (0, 0.92, 0.55), 0.245, 0.022, 0.14, 0.0, 0.18, 0.0),
        ((0, 0.028, 0.046), (0, 0.97, 0.38), 0.275, 0.023, 0.16, 0.0, 0.18, 0.0),
        ((0, 0.044, 0.034), (0, 1.0, 0.2), 0.21, 0.02, 0.14, 0.0, 0.15, 0.0),
        ((0, 0.056, 0.02), (0, 1.0, 0.08), 0.15, 0.017, 0.12, 0.0, 0.14, 0.0),
    ]
    for k, (r, dirn, length, width, curl, hook, wave, splay) in enumerate(rows):
        face = V(1, 0, 0) if splay == 0 else V(1, -abs(splay), 0).normalized()
        fan = (0.0, -0.14, 0.12, -0.07, 0.16, -0.18)[k]        # each a little to one side: a flame seen from the front, not a spike
        x_off = 0.0035 * (1 if fan > 0 else -1 if fan < 0 else 0)
        dvec = V(fan, dirn[1], dirn[2])
        face = V(1, 0, 0) - dvec.normalized() * dvec.normalized().x
        out.append(Plume(HEAD_C + V(*r) + V(x_off, 0, 0), dvec, length, width, face, lift=0.0, tilt=0.0, cup=0.003, droop=0.0, curl=curl,
                         hook=hook, shape="lance", group=k, f=float(k), sunk=0.012, wave=wave, seed=k * 1.7))
    return out


# ---------- feathers lying on the skin ----------
def neck_feathers(tree):
    """Rows of narrow feathers down the neck, each row over the root of the next, pointing down the neck toward the body."""
    out = []
    rows = 8
    for r in range(rows):
        f = 0.94 - r * 0.106
        c = along(NECK, f)
        t = path_tan(NECK, f, 0.05)
        ref = V(1, 0, 0)
        b = t.cross(ref).normalized()
        n_around = 8
        for k in range(n_around):
            a = TAU * (k + 0.5 * (r % 2)) / n_around
            radial = (ref * math.cos(a) + b * math.sin(a)).normalized()
            root = c + radial * 0.12
            hit = tree.ray_cast(root, -radial, 0.2)[0]
            if hit is None:
                continue
            length = 0.078 + 0.022 * (1 - f)
            out.append(SkinFeather(tree, hit, -t, length, 0.0135 + 0.007 * (1 - f), lift=0.0042, shape="lance", group=r, f=f, seed=k))
    return out


def chest_feathers(tree):
    """Rows of round-ended breast feathers over the chest and down to the belly, each row lying over the next."""
    out = []
    for r in range(6):
        z = 0.712 - r * 0.036
        n_across = 5 + (r % 2)
        for k in range(n_across):
            x = (k - (n_across - 1) / 2) * 0.035
            probe = V(x, -0.4, z)
            hit = tree.ray_cast(probe, V(0, 1, 0), 0.6)[0]
            if hit is None or hit.y > 0.02:
                continue
            down = V(0, 0.25, -1)
            out.append(SkinFeather(tree, hit, down, 0.07 + 0.004 * r, 0.0195, lift=0.0024, shape="round", group=r, f=z, seed=k))
    return out


def body_feathers(tree):
    """The mantle over the back and the flank feathers, pointing back along the body; and the feathered thighs ("trousers") down to the hock."""
    out = []
    for r in range(5):
        f = 0.92 - r * 0.13
        c = along(SPINE, f)
        t = path_tan(SPINE, f, 0.05)
        for k in range(7):
            a = math.radians(-80 + k * (160 / 6) + (13 if r % 2 else 0))
            radial = V(math.sin(a), math.cos(a) * 0.8, math.cos(a) * 0.6).normalized()
            hit = tree.ray_cast(c + radial * 0.3, -radial, 0.4)[0]
            if hit is None:
                continue
            out.append(SkinFeather(tree, hit, -t, 0.078, 0.02, lift=0.0031, shape="round", group=r, f=f, seed=k))
    for side in (1, -1):
        hip, hock = mir(LEG[0], side), mir(LEG[1], side)
        dirn = (hock - hip).normalized()
        for r in range(3):
            for k in range(4):
                a = math.radians(-70 + k * 46 + (20 if r % 2 else 0))
                c = hip.lerp(hock, 0.15 + 0.22 * r)
                ref = V(side, 0, 0)
                b = dirn.cross(ref).normalized()
                radial = (ref * math.cos(a) + b * math.sin(a)).normalized()
                hit = tree.ray_cast(c + radial * 0.15, -radial, 0.25)[0]
                if hit is None:
                    continue
                out.append(SkinFeather(tree, hit, dirn, 0.05, 0.014, lift=0.0026, shape="lance", group=10 + r, f=r, seed=k))
    return out


# ---------- the skin: one sculpted volume ----------
def build_skin(blockout=False):
    core = Mesh()
    core.tube(SPINE, lambda f: prof(SPINE_R, f), sides=32)
    core.tube(NECK, lambda f: prof(NECK_R, f), sides=28)
    core.ball(CHEST + V(0, -0.016, 0.0), (0.1, 0.106, 0.118))              # the breast: deep, forward
    core.ball(V(0, -0.075, 0.6), (0.06, 0.07, 0.1))                        # the keel under it
    core.ball(V(0, 0.01, 0.665), (0.108, 0.095, 0.08))                     # the back and the shoulders the wings come off
    core.ball(BELLY, (0.074, 0.11, 0.074))                                 # a compact abdomen
    core.ball(RUMP, (0.05, 0.08, 0.045))                                   # the rump the tail grows from
    for side in (1, -1):
        core.ball(mir(V(0.05, 0.085, 0.5), side), (0.04, 0.05, 0.045))     # the hip
        core.tube(catmull([mir(LEG[0], side), mir(LEG[1], side)], 4), lambda f: 0.036 - 0.018 * f, sides=18)      # the feathered drumstick
    core.ball(HEAD_C, (0.041, 0.06, 0.045))                                  # the skull: narrow and long
    core.ball(HEAD_C + V(0, 0.036, 0.004), (0.038, 0.045, 0.042))           # the back of the skull
    if not blockout:
        core.ball(HEAD_C + V(0, -0.03, 0.02), (0.027, 0.036, 0.017))        # the raised forehead, sloping down into the beak
        core.ball(BEAK_ROOT + V(0, 0.018, 0.002), (0.02, 0.016, 0.02))       # the cere the beak grows from
        for side in (1, -1):
            core.ball(mir(EYE_C, side) - mir(EYE_AXIS, side) * 0.003, (EYE_R * 1.1,) * 3, 28, 18)      # the socket
            core.ball(mir(EYE_C + V(0.002, -0.004, 0.0128), side), (0.0185, 0.027, 0.0095))          # the hard brow ridge, overhanging it
    c = core.finish(N + "SkinHi", HI)
    apply_mods(c, [("REMESH", {"mode": "VOXEL", "voxel_size": 0.0055, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 10}),
                   ("REMESH", {"mode": "VOXEL", "voxel_size": 0.0024, "adaptivity": 0.0}), ("SMOOTH", {"factor": 1.0, "iterations": 4})])
    c.data.polygons.foreach_set("use_smooth", [True] * len(c.data.polygons))
    base = bpy.data.objects.new(N + "SkinBase", c.data.copy())
    HI.objects.link(base)
    base.hide_render = True
    return c, base


# ---------- the beak: lofted from a ridged section, in two parts ----------
def beak_paths():
    upper = catmull([BEAK_ROOT + V(0, 0.018, 0.006), BEAK_ROOT + V(0, -0.01, 0.005), BEAK_ROOT + V(0, -0.028, 0.0), BEAK_ROOT + V(0, -0.04, -0.012),
                     BEAK_ROOT + V(0, -0.044, -0.026), BEAK_ROOT + V(0, -0.038, -0.036)], 6)
    lower = catmull([BEAK_ROOT + V(0, 0.014, -0.018), BEAK_ROOT + V(0, -0.008, -0.021), BEAK_ROOT + V(0, -0.02, -0.023), BEAK_ROOT + V(0, -0.027, -0.0235)], 6)     # tucked under the hook (head-on, a longer one read as a lip)
    return upper, lower


def loft_beak(path, width, height, sides, lower=False):
    """A beak along its path: each section an arch with a ridge along its top (the culmen) and a cutting edge along its sides, closed underneath;
    widest at the root, tapering, the upper one hooking down at its tip."""
    m = Mesh()
    bm = m.bm
    rings = []
    n = len(path)
    for i, p in enumerate(path):
        f = i / (n - 1)
        t = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
        side = V(1, 0, 0)
        up = t.cross(side).normalized()
        if up.z < 0:
            up = -up
        w = width(f)
        h = height(f)
        ring = []
        for k in range(sides):
            a = TAU * k / sides
            ca, sa = math.cos(a), math.sin(a)
            if (ca > 0) != lower:             # the ridge side: narrowing to the culmen
                x = w * sa * (1 - 0.42 * abs(ca) ** 1.4)
                z = h * ca * (1 if not lower else -1) * (1 if not lower else 1)
            else:                              # the mouth side: a flatter edge
                x = w * sa
                z = h * 0.42 * ca * (1 if not lower else -1)
            z = z if not lower else -z
            ring.append(bm.verts.new(p + side * x + up * (z if not lower else -z)))
        rings.append(ring)
    for i in range(n - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    return m


def build_beak(name, coll, sides, lower=False):
    up, low = beak_paths()
    if lower:
        m = loft_beak(low, lambda f: 0.0128 * (1 - f) ** 0.8 + 0.0015, lambda f: 0.0055 * (1 - f) ** 0.6 + 0.0014, sides, lower=True)
    else:
        m = loft_beak(up, lambda f: 0.0172 * (1 - f) ** 0.72 + 0.0007, lambda f: 0.023 * (1 - f) ** 0.58 + 0.0008, sides)
    return m.finish(name, coll)


# ---------- legs, toes and talons ----------
def toe_paths(side):
    """Three toes forward, spread, a little curled as if about to grip; one back. Each with its joints."""
    foot = mir(LEG[2], side)
    out = []
    for deg, length, curl in ((24, 0.062, 0.5), (0, 0.072, 0.55), (-24, 0.058, 0.5), (180, 0.04, 0.6)):
        a = math.radians(deg)
        fwd = V(side * math.sin(a), -math.cos(a), 0)
        dirn = (fwd * 0.9 + V(0, 0, -0.42)).normalized()
        p = foot + dirn * 0.005
        pts = [p.copy()]
        for j in range(4):
            seg = length / 4
            p = p + dirn * seg
            pts.append(p.copy())
            dirn = (dirn * math.cos(curl * 0.5) + V(0, 0, -1) * math.sin(curl * 0.5)).normalized()
        out.append((catmull(pts, 3), length))
    return out


def joint_radius(f, base, joints=3):
    """A toe's thickness along it: tapering, swelling a little at each knuckle."""
    knuckle = 0.12 * max(0.0, math.cos(f * joints * math.pi * 2)) ** 6
    return base * (1 - 0.45 * f) * (1 + knuckle)


def build_legs(name, coll, sides, tsides, step=1):
    """The bare legs: the scaly tarsus from the hock (a knob at the joint) down to the foot, flattened front to back as a bird's is; and the toes."""
    m = Mesh()
    bm = m.bm
    bm.verts.layers.int.new("side")
    bm.verts.layers.int.new("part")
    bm.verts.layers.float.new("along")
    sl, pl, al = bm.verts.layers.int["side"], bm.verts.layers.int["part"], bm.verts.layers.float["along"]
    for side in (1, -1):
        hock, foot = mir(LEG[1], side), mir(LEG[2], side)
        path = catmull([hock + V(0, 0.01, 0.012), hock, hock.lerp(foot, 0.5) + V(0, -0.004, 0), foot], 5)[::step]
        before = set(bm.verts)
        m.tube(path, lambda f: (0.0115 - 0.003 * f) * (1 + 0.28 * max(0.0, 1 - f * 6)), sides=sides, flat=0.82, plane=V(1, 0, 0))
        new = [v for v in bm.verts if v not in before]
        fr, _ = nearest_on(path, np.array([tuple(v.co) for v in new]))
        for v, ff in zip(new, fr):
            v[sl], v[pl], v[al] = side, 0, float(ff)
        for toe, length in toe_paths(side):
            toe = toe[::step] + ([toe[-1]] if (len(toe) - 1) % step else [])
            before = set(bm.verts)
            m.tube(toe, lambda f: joint_radius(f, 0.0068), sides=tsides)
            new = [v for v in bm.verts if v not in before]
            fr, _ = nearest_on(toe, np.array([tuple(v.co) for v in new]))
            for v, ff in zip(new, fr):
                v[sl], v[pl], v[al] = side, 1, float(ff)
    return m.finish(name, coll)


def build_talons(name, coll, sides, rings=7):
    """A hooked claw at the end of each toe: thick at its base, curving down and in, drawn to a sharp point."""
    m = Mesh()
    bm = m.bm
    bm.verts.layers.int.new("side")
    sl = bm.verts.layers.int["side"]
    for side in (1, -1):
        for toe, length in toe_paths(side):
            tip = toe[-1]
            dirn = (toe[-1] - toe[-3]).normalized()
            down = V(0, 0, -1)
            pts = []
            for i in range(rings):
                t = i / (rings - 1)
                a = t * 1.25
                d = (dirn * math.cos(a) + down * math.sin(a)).normalized()
                pts.append(tip - dirn * 0.004 + (dirn * math.sin(a) + down * (1 - math.cos(a))) * 0.022 * (0.9 if length < 0.05 else 1.0))
            before = set(bm.verts)
            m.tube(pts, lambda f: 0.0058 * (1 - f) ** 0.9 + 0.0006, sides=sides, flat=0.75, plane=V(side, 0, 0))
            for v in set(bm.verts) - before:
                v[sl] = side
    return m.finish(name, coll)


def build_arms(name, coll, sides, step):
    """The wing's arm: shoulder, upper arm, forearm, wrist and hand, its leading edge rounded and its trailing side drawn thin, as the skin of a
    wing is; the coverts hide most of it."""
    m = Mesh()
    bm = m.bm
    bm.verts.layers.int.new("side")
    bm.verts.layers.float.new("along")
    sl, al = bm.verts.layers.int["side"], bm.verts.layers.float["along"]
    for side in (1, -1):
        path = [mir(p, side) for p in ARM_PATH[::step]] + ([mir(ARM_PATH[-1], side)] if (len(ARM_PATH) - 1) % step else [])
        before = set(bm.verts)
        m.tube(path, lambda f: arm_radius(f) * (1 + 0.15 * max(0.0, 1 - abs(f - 2 / 3) * 12)), sides=sides, flat=0.48, plane=V(0, 0, 1))
        new = [v for v in bm.verts if v not in before]
        fr, _ = nearest_on(path, np.array([tuple(v.co) for v in new]))
        for v, ff in zip(new, fr):
            v[sl], v[al] = side, float(ff)
    return m.finish(name, coll)


def read_attr(o, key, kind=int):
    a = o.data.attributes[key]
    out = np.zeros(len(o.data.vertices), dtype=kind)
    a.data.foreach_get("value", out)
    return out


# ---------- paint ----------
def scallops(x, y, seed=0):
    """Overlapping round feather ends in offset rows (y up toward the head). Per point: how far across the feather shown there (0 middle, 1 free
    edge) and that feather's own small change of shade."""
    best_e = np.full(len(x), 9.0)
    best_v = np.zeros(len(x))
    shown = np.zeros(len(x), dtype=bool)
    R = 0.66
    base = np.floor(y)
    for dr in (1, 0, -1):
        row = base + dr
        off = (row % 2) * 0.5
        col = np.floor(x - off) + 0.5 + off
        for dc in (0, -1, 1):
            cx = col + dc
            cy = row + 0.62
            e = np.hypot((x - cx) * 1.05, (y - cy)) / R
            take = (~shown) & (e < 1.0) & (y < cy + 0.2)
            best_e = np.where(take, e, best_e)
            best_v = np.where(take, (np.sin(cx * 12.9898 + row * 78.233 + seed) * 43758.5453) % 1.0, best_v)
            shown |= take
    return np.where(shown, best_e, 1.0), best_v


def region_colours(Pv, Nn):
    """The colour of the creature at each point of its skin, by region (the directive's distribution): head warm golden orange, its crown going to
    crimson; neck rich orange; chest cream and ivory; body deep amber and burnt orange, its back the darkest."""
    n = len(Pv)
    hz = Pv - np.array(tuple(HEAD_C))
    head = 1 - smooth(0.05, 0.075, np.linalg.norm(hz / np.array((1.0, 0.75, 1.0)), axis=1))
    nf, nd = nearest_on(NECK, Pv)
    neck = (1 - smooth(0.06, 0.09, nd)) * smooth(0.06, 0.18, nf) * (1 - head)
    back = smooth(-0.3, 0.7, Nn[:, 1] * 0.8 + Nn[:, 2] * 0.45)
    front = smooth(-0.1, 0.7, -Nn[:, 1] * 0.85 - Nn[:, 2] * 0.25)
    z = Pv[:, 2]
    body = mix(np.broadcast_to(AMBER, (n, 3)), BURNT, smooth(0.2, 0.7, back))
    body = mix(body, mix(BURNT, CRIMSON, 0.45), smooth(0.7, 1.0, back) * 0.7)
    chest = mix(mix(np.broadcast_to(mix(CREAM, CHAMPAGNE, 0.55), (n, 3)), mix(CHAMPAGNE, PEACH, 0.25), smooth(0.68, 0.55, z)), mix(PALE_GOLD, AMBER, 0.3), smooth(0.56, 0.47, z))
    chest = mix(chest, CREAM, smooth(0.6, 0.66, z) * (1 - smooth(0.68, 0.72, z)) * 0.5)
    window = (1 - neck) * smooth(0.45, 0.53, z) * (1 - smooth(0.74, 0.8, z))
    cream = smooth(0.35, 1.0, front) ** 1.4 * window
    col = mix(body, mix(mix(AMBER, GOLDEN, 0.5), PALE_GOLD, smooth(0.3, 0.7, front)), smooth(0.1, 0.55, front) * window)   # amber warming to gold...
    col = mix(col, chest, cream)                                                                                            # ...to cream at its heart
    col = col * (0.8 + 0.2 * smooth(-0.1, 0.85, front))[:, None] * (1 - 0.0 * window[:, None])     # the breast's form: its sides in shade
    neck_col = mix(mix(np.broadcast_to(BURNT, (n, 3)), AMBER, 0.55), GOLDEN, smooth(0.3, 0.9, -Nn[:, 1]) * 0.55)
    neck_col = mix(neck_col, mix(CREAM, CHAMPAGNE, 0.5), smooth(0.8, 0.12, nf) * smooth(0.25, 0.85, -Nn[:, 1]) * 0.8)     # the throat pale, running down into the breast
    col = mix(col, neck_col, neck)
    head_col = mix(mix(np.broadcast_to(GOLDEN, (n, 3)), AMBER, 0.45), CRIMSON, smooth(1.085, 1.115, z) * 0.75)
    head_col = mix(head_col, GOLDEN, smooth(0.3, 0.9, -hz[:, 1] / 0.06) * 0.35)          # the face a little brighter toward the beak
    col = mix(col, head_col, head)
    return col, head, neck, front


def paint_skin(o):
    Pv = verts(o)
    Nn = normals(o)
    x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
    n = len(Pv)
    col, head, neck, front = region_colours(Pv, Nn)
    hz = Pv - np.array(tuple(HEAD_C))
    # round each eye, a ring of pale gold bare skin; a darker crimson line sweeping back from it (the noble mask of its face)
    ring = np.zeros(n)
    stripe = np.zeros(n)
    for side in (1, -1):
        e = np.array(tuple(mir(EYE_C, side)))
        rel = Pv - e
        dist = np.linalg.norm(rel, axis=1)
        ring = np.maximum(ring, (1 - smooth(EYE_R * 1.08, EYE_R * 1.32, dist)) * smooth(EYE_R * 0.95, EYE_R * 1.02, dist))
        bd = np.array((side * 0.38, 0.92, 0.04))
        bd = bd / np.linalg.norm(bd)
        t = (rel * bd).sum(1)
        off = np.linalg.norm(rel - t[:, None] * bd, axis=1)
        lt = np.clip((t - 0.012) / 0.07, 0, 1)
        width = 0.0042 * (1 - lt) ** 0.7 + 0.0008
        on = (t > 0.012) & (t < 0.082)
        stripe = np.maximum(stripe, np.where(on, 1 - smooth(width * 0.6, width, off), 0.0) * smooth(0.012, 0.02, t))
    col = mix(col, mix(AMBER, BURNT, 0.4), ring * 0.8)
    # feather scallops where feathers are not modelled (the skin under and between them)
    f, _ = nearest_on(SPINE, Pv)
    e1, v1 = scallops(np.arctan2(x, -y) / TAU * 28, f * 24, 3)
    nf, _ = nearest_on(NECK, Pv)
    e2, v2 = scallops(np.arctan2(x, -y) / TAU * 24, nf * 30, 5)
    e3, v3 = scallops(np.arctan2(hz[:, 0], hz[:, 1]) / TAU * 30, (hz[:, 2] + 0.1) * 300, 7)
    use_neck = smooth(0.3, 0.7, neck)
    e = e1 * (1 - use_neck) + e2 * use_neck
    vary = v1 * (1 - use_neck) + v2 * use_neck
    e = e * (1 - head) + e3 * head
    vary = vary * (1 - head) + v3 * head
    bare = np.clip(np.maximum(head * smooth(0.0, 0.5, -hz[:, 1] / 0.045), ring * 2), 0, 1)
    col = col * (0.96 + 0.07 * (vary[:, None] - 0.5))
    col = mix(col, col * 0.9, (1 - smooth(0.0, 0.55, e)) * 0.25 * (1 - bare))
    col = mix(col, mix(col, PALE_GOLD, 0.5), smooth(0.74, 0.97, e) * (0.2 + 0.25 * front) * (1 - bare))
    relief = (smooth(0.0, 1.0, e) * 0.0008 - 0.0004) * (1 - bare)
    set_verts(o, Pv + Nn * relief[:, None])
    rough = 0.62 - 0.12 * front - 0.2 * ring
    paint(o, np.clip(col, 0, 1), rough, np.zeros(n))


def root_shade(uu, depth=0.22):
    """Toward its root a feather sits in the shade of the one over it: what a bake's occlusion gives, painted in."""
    return (1 - depth) + depth * smooth(0.0, 0.35, uu)


def vane(uu, w, shaft=True):
    """A feather's surface: fine barbs running out from its middle at a slant; on flight and tail feathers a faint shaft that fades out well before
    the tip (a strong line to the end with a spot at its tip reads as something else at thumbnail size: never)."""
    barbs = 0.5 + 0.5 * np.sin((uu * 1.0 + w * 0.32) * 95)
    out = 0.95 + 0.06 * barbs
    if shaft:
        s = (1 - smooth(0.04, 0.09, w)) * (1 - smooth(0.45, 0.7, uu)) * smooth(0.0, 0.08, uu)
        out = out * (1 + 0.1 * s)
    return out


def colour_wing(idx, uu, vv, top, plumes, P=None):
    n = len(idx)
    g = np.array([plumes[int(i)].group for i in idx])
    seed = np.array([plumes[int(i)].seed for i in idx], dtype=float)
    w = np.abs(2 * vv - 1)
    G = GROUPS
    # primaries: burnt orange roots going to deep crimson toward their ends, the outer ones the darkest; a few edged pale gold at the tip
    prim = mix(mix(np.broadcast_to(AMBER, (n, 3)), BURNT, smooth(0.0, 0.35, uu)), CRIMSON, smooth(0.42, 0.85, uu))
    prim = mix(prim, DEEP_CRIMSON, smooth(0.75, 1.0, uu) * smooth(6.0, 0.0, seed))
    tipped = (seed % 3 == 1)
    prim = mix(prim, PALE_GOLD, smooth(0.9, 0.99, uu) * tipped * 0.8)
    # secondaries and tertials: burnt orange to golden amber, tipped pale gold
    sec = mix(mix(np.broadcast_to(BURNT, (n, 3)), AMBER, smooth(0.1, 0.6, uu)), GOLDEN, smooth(0.6, 0.9, uu))
    sec = mix(sec, PALE_GOLD, smooth(0.9, 1.0, uu) * 0.85)
    # coverts: golden amber in the greater and median rows; the lesser and marginal coverts along the leading edge crimson to burnt orange
    greater = mix(mix(np.broadcast_to(AMBER, (n, 3)), GOLDEN, smooth(0.2, 0.9, uu)), PALE_GOLD, smooth(0.85, 1.0, uu) * 0.7)
    fpos = np.array([plumes[int(i)].f for i in idx])
    greater = mix(greater, mix(BURNT, AMBER, smooth(0.3, 1.0, uu)), smooth(0.45, 0.05, fpos) * 0.55)      # toward the body, deeper: no flat yellow block
    lesser = mix(np.broadcast_to(CRIMSON, (n, 3)), BURNT, smooth(0.2, 1.0, uu))
    under = mix(np.broadcast_to(PEACH, (n, 3)), CREAM, smooth(0.0, 1.0, uu))
    col = np.where((g == G["primary"])[:, None], prim, sec)
    col = np.where(np.isin(g, (G["greater"], G["median"], G["pcovert"]))[:, None], greater, col)
    col = np.where(np.isin(g, (G["lesser"], G["marginal"], G["alula"]))[:, None], lesser, col)
    col = np.where((g == G["under"])[:, None], under, col)
    # each feather's underside light and warm (peach to pale gold, the primaries' ends still crimson): seen from below, one clean warm surface
    under_all = mix(mix(np.broadcast_to(PEACH, (n, 3)), PALE_GOLD, smooth(0.2, 0.9, uu)), col, 0.22)
    under_all = mix(under_all, CRIMSON, (smooth(0.6, 0.95, uu) * (g == G["primary"]) * 0.45))
    col = np.where(top[:, None] > 0, col, under_all)
    flight = np.isin(g, (G["primary"], G["secondary"], G["tertial"]))
    col = col * np.where(flight, vane(uu, w, True), vane(uu, w, False))[:, None]
    col = col * (1 + 0.08 * smooth(0.75, 1.0, w))[:, None]
    jit = np.array([0.94 + 0.12 * hashf(s, k) for s, k in zip(seed, g)])
    col = col * jit[:, None]
    return np.clip(col, 0, 1), np.where(top > 0, 0.46, 0.54).astype(float)


def colour_tail(idx, uu, vv, top, feathers, P=None):
    """Deep crimson at the root, warm orange, golden amber, and pale gold to pale yellow at the tips."""
    n = len(idx)
    g = np.array([feathers[int(i)].group for i in idx])
    w = np.abs(2 * vv - 1)
    col = mix(np.broadcast_to(CRIMSON, (n, 3)), BURNT, smooth(0.05, 0.3, uu))
    col = mix(col, AMBER, smooth(0.3, 0.58, uu))
    col = mix(col, GOLDEN, smooth(0.55, 0.8, uu))
    col = mix(col, PALE_GOLD, smooth(0.78, 0.92, uu))
    col = mix(col, PALE_YELLOW, smooth(0.9, 1.0, uu))
    edge = smooth(0.7, 1.0, w) * smooth(0.2, 0.6, uu) * (1 - smooth(0.85, 0.95, uu))
    col = mix(col, CRIMSON, edge * 0.35)          # a darker margin along each vane, so each feather reads on its own
    col = np.where(top[:, None] > 0, col, mix(col, PEACH, 0.3))
    col = col * vane(uu, w, True)[:, None]
    jit = np.array([0.95 + 0.1 * hashf(k, 7) for k in g])
    col = col * jit[:, None]
    return np.clip(col, 0, 1), np.where(top > 0, 0.44, 0.52).astype(float)


def colour_crest(idx, uu, vv, top, plumes, P=None):
    """Warm golden orange at the root, going to crimson toward the ends; the long middle ones edged pale gold."""
    n = len(idx)
    k = idx
    w = np.abs(2 * vv - 1)
    col = mix(mix(np.broadcast_to(GOLDEN, (n, 3)), AMBER, smooth(0.0, 0.3, uu)), BURNT, smooth(0.3, 0.55, uu))
    col = mix(col, CRIMSON, smooth(0.5, 0.85, uu))
    col = mix(col, DEEP_CRIMSON, smooth(0.85, 1.0, uu) * 0.6)
    col = mix(col, PALE_GOLD, smooth(0.78, 1.0, w) * smooth(0.15, 0.4, uu) * np.isin(k, (2, 3, 4)) * 0.6)
    col = col * vane(uu, w, False)[:, None]
    return np.clip(col, 0, 1), np.full(n, 0.45)


def colour_skin_feathers(idx, uu, vv, top, feathers, P=None):
    """Feathers lying on the skin take the skin's colour where they lie, their free ends edged a little lighter (the neck's layers golden, the
    breast's champagne)."""
    n = len(idx)
    Pv = P
    Nn = np.array([tuple(feathers[int(i)].n) for i in idx])
    col, head, neck, front = region_colours(Pv, Nn)
    w = np.abs(2 * vv - 1)
    edge = smooth(0.6, 0.98, uu) * 0.7 + smooth(0.7, 1.0, w) * smooth(0.25, 0.8, uu) * 0.3
    light = np.where(neck > 0.4, 1.0, 0.0)
    col = mix(col, mix(col, GOLDEN, 0.6), edge * light * 0.55)
    col = mix(col, mix(col, mix(PALE_GOLD, CREAM, front), 0.5), edge * (1 - light) * 0.45)       # each row's free edge lighter: the gradient runs through the rows
    col = col * vane(uu, w, False)[:, None]
    jit = np.array([0.95 + 0.1 * hashf(i, 11) for i in idx])
    col = col * jit[:, None]
    return np.clip(col, 0, 1), np.full(n, 0.55)


def paint_by(o, colour, meta, plumes):
    """Paints a high-detail feather mesh by its colour function (per vertex)."""
    idx, uu, vv, top = meta
    col, rough = colour(idx, uu, vv, top, plumes, verts(o))
    col = col * np.where(top > 0, root_shade(uu, 0.08 if colour is colour_skin_feathers else 0.22), 1.0)[:, None]
    paint(o, col, rough, np.zeros(len(idx)))


def paint_beak(o, lower):
    Pv = verts(o)
    up, low = beak_paths()
    f, _ = nearest_on(low if lower else up, Pv)
    col = mix(np.broadcast_to(AMBER, (len(Pv), 3)), mix(GOLDEN, CHAMPAGNE, 0.35), smooth(0.08, 0.4, f))
    if not lower:      # its ridge darker than its sides: head-on it reads as a hooked beak, not a long pale nose
        nrm = normals(o)
        col = mix(col, mix(AMBER, BRONZE, 0.35), smooth(0.55, 0.95, nrm[:, 2]) * smooth(0.1, 0.3, f) * 0.7)
    col = mix(col, mix(BRONZE, AMBER, 0.45), smooth(0.8, 1.0, f) * (0.3 if lower else 0.5))
    paint(o, col, np.full(len(Pv), 0.3), np.zeros(len(Pv)))


def paint_legs(o):
    part = read_attr(o, "part")
    along_ = read_attr(o, "along", float)
    n = len(along_)
    Pv = verts(o)
    scutes = 0.5 + 0.5 * np.sin(along_ * np.where(part == 0, 70, 40) * TAU)
    col = mix(np.broadcast_to(BRONZE, (n, 3)), rgb(110, 74, 44), 0.35 * scutes[:, None].ravel())
    set_verts(o, Pv + normals(o) * ((scutes - 0.5) * 0.0005)[:, None])
    paint(o, np.clip(col, 0, 1), np.full(n, 0.42), np.zeros(n))


def paint_talons(o):
    n = len(o.data.vertices)
    paint(o, np.broadcast_to(TALON, (n, 3)), np.full(n, 0.28), np.zeros(n))


def paint_arms(o):
    Pv = verts(o)
    Nn = normals(o)
    n = len(Pv)
    col = mix(np.broadcast_to(CRIMSON, (n, 3)), PEACH, smooth(0.1, -0.6, Nn[:, 2]))
    paint(o, col, np.full(n, 0.58), np.zeros(n))


def eye_paint(o, fr):
    """Golden eyes: a bright amber iris going to golden orange at its rim with a fine darker ring, fine rays, a round dark pupil; the brow's shadow
    over its top. Intelligent, not fierce: no white showing."""
    px, py, a = eye_coords(o, fr)
    front = a > 0
    r = np.where(front, np.hypot(px, py), 3.0)
    n = len(px)
    col = np.broadcast_to(rgb(46, 22, 10), (n, 3)).copy()
    t = r / IRIS
    iris = mix(rgb(250, 176, 40), rgb(226, 112, 16), smooth(0.35, 0.85, t))
    iris = mix(iris, rgb(96, 34, 10), smooth(0.84, 1.0, t))
    azi = np.arctan2(py, px)
    iris = iris * (0.94 + 0.06 * np.sin(azi * 26 + np.sin(azi * 5) * 1.3))[:, None]
    iris = mix(iris, iris * 0.6, smooth(-0.2, 0.7, py / IRIS) * 0.5)
    col = mix(col, iris, 1 - smooth(IRIS - 0.03, IRIS, r))
    col = mix(col, rgb(14, 6, 4), 1 - smooth(PUPIL - 0.03, PUPIL + 0.02, r))
    # a soft highlight painted in (no glowing pieces: the directive's renders allow no effects)
    hl = 1 - smooth(0.07, 0.11, np.hypot(px + 0.32, py - 0.34))
    col = mix(col, rgb(255, 246, 225), hl * 0.9 * front)
    paint(o, col, np.full(n, 0.04), np.zeros(n))


# ---------- building it ----------
def blockout():
    """The primary forms: head, neck, chest, torso, hips, legs, wings (their arm and their long feathers as plain blades) and the tail."""
    pieces = {}
    pieces["Skin"], _ = build_skin(blockout=True)
    pieces["Arms"] = build_arms(N + "ArmBlock", HI, 12, 2)
    for side, tag in ((1, "L"), (-1, "R")):
        wing = [p for p in wing_plumes(side) if p.group in (0, 1, 2)]
        pieces["Wing" + tag], *_ = build_plumes(wing, N + "WingBlock" + tag, HI, 8, 2)
    pieces["Tail"], *_ = build_plumes(tail_feathers(), N + "TailBlock", HI, 40, 3)
    pieces["Legs"] = build_legs(N + "LegBlock", HI, 10, 6)
    pieces["Crest"], *_ = build_plumes(crest_plumes()[1:5], N + "CrestBlock", HI, 10, 3)
    return pieces


def build_hi(level):
    pieces, frames, data = {}, {}, {}
    pieces["Skin"], data["SkinBase"] = build_skin()
    tree = tree_of(data["SkinBase"])
    data["tree"] = tree
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, mix(GOLDEN, AMBER, 0.55), LASH, line_w=1.5)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, mix(GOLDEN, AMBER, 0.3), LASH, lower_share=0.25, line_w=1.4)
    pieces["BeakUpper"] = build_beak(N + "BeakUpperHi", HI, 24)
    pieces["BeakLower"] = build_beak(N + "BeakLowerHi", HI, 20, lower=True)
    pieces["Legs"] = build_legs(N + "LegsHi", HI, 16, 10)
    pieces["Talons"] = build_talons(N + "TalonsHi", HI, 10)
    data["Tail"] = tail_feathers() + tail_coverts()
    pieces["Tail"], *data["TailMeta"] = build_plumes(data["Tail"], N + "TailHi", HI, 60, 10)
    data["Crest"] = crest_plumes()
    pieces["Crest"], *data["CrestMeta"] = build_plumes(data["Crest"], N + "CrestHi", HI, 36, 10, thick=crest_thick)
    pieces["Arms"] = build_arms(N + "ArmsHi", HI, 20, 1)
    if level >= ORDER.index("wings"):
        for side, tag in ((1, "L"), (-1, "R")):
            data["Wing" + tag] = wing_plumes(side)
            pieces["Wing" + tag], *data["Wing" + tag + "Meta"] = build_plumes(data["Wing" + tag], N + "Wing" + tag + "Hi", HI, 30, 8)
    if level >= ORDER.index("feathers"):
        for key, maker in (("NeckFeathers", neck_feathers), ("ChestFeathers", chest_feathers), ("BodyFeathers", body_feathers)):
            data[key] = maker(tree)
            pieces[key], *data[key + "Meta"] = build_plumes(data[key], N + key + "Hi", HI, 10, 6, thick=skin_feather_thick)
    if level >= ORDER.index("materials"):
        paint_skin(pieces["Skin"])
        for tag, fr in frames.items():
            eye_paint(pieces["Eye" + tag], fr)
        paint_beak(pieces["BeakUpper"], False)
        paint_beak(pieces["BeakLower"], True)
        paint_legs(pieces["Legs"])
        paint_talons(pieces["Talons"])
        paint_arms(pieces["Arms"])
        for tag in ("L", "R"):
            paint_by(pieces["Wing" + tag], colour_wing, data["Wing" + tag + "Meta"], data["Wing" + tag])
        paint_by(pieces["Tail"], colour_tail, data["TailMeta"], data["Tail"])
        paint_by(pieces["Crest"], colour_crest, data["CrestMeta"], data["Crest"])
        for key in ("NeckFeathers", "ChestFeathers", "BodyFeathers"):
            paint_by(pieces[key], colour_skin_feathers, data[key + "Meta"], data[key])
    return pieces, frames, data


# ---------- review: views, clay, silhouette ----------
VIEW_AT = (0, 0.22, 0.72)
FACE_AT = (0, -0.23, 1.065)
VIEWS = [(0, -1, 0.1), (0.62, -0.72, 0.25), (1, 0, 0.06), (0, 1, 0.2), (-0.6, 0.6, 0.4), (-0.62, -0.72, 0.22), (0, -0.05, 1), (0.35, -0.5, -0.75)]
FACE_VIEWS = [(0, -1, 0.05, 0.36, FACE_AT), (0.7, -0.7, 0.12, 0.4, FACE_AT), (1, -0.05, 0.08, 0.4, FACE_AT), (0.45, -0.88, 0.1, 0.16, tuple(EYE_C))]
FAR_VIEWS = [(0.25, 0.95, 0.4, 13.0, VIEW_AT), (0.6, -0.75, 0.55, 15.0, VIEW_AT)]     # what a player sees, a few studs off
SIL_VIEWS = [(0, -1, 0.08), (1, 0, 0.04), (0.62, -0.72, 0.25), (0, 1, 0.25), (0, -0.05, 1), (0.6, 0.6, 0.3)]
DIST = 4.4


def clay_materials(pieces):
    mat = bpy.data.materials.new("clay")
    g = next(nd for nd in mat.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
    g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
    g.inputs["Roughness"].default_value = 0.6
    dark = bpy.data.materials.new("clay_eye")
    g = next(nd for nd in dark.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
    g.inputs["Base Color"].default_value = (0.32, 0.18, 0.04, 1)
    g.inputs["Roughness"].default_value = 0.12
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(dark if key.startswith("Eye") else mat)


def silhouette(objs, prefix):
    black = bpy.data.materials.new("silhouette")
    g = next(nd for nd in black.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
    g.inputs["Base Color"].default_value = (0, 0, 0, 1)
    g.inputs["Roughness"].default_value = 1.0
    g.inputs["Specular IOR Level"].default_value = 0.0
    keep = {}
    for o in objs:
        keep[o.name] = list(o.data.materials)
        o.data.materials.clear()
        o.data.materials.append(black)
    world = bpy.context.scene.world.node_tree.nodes["Background"]
    old = tuple(world.inputs[0].default_value), world.inputs[1].default_value
    world.inputs[0].default_value = (1, 1, 1, 1)
    world.inputs[1].default_value = 1.0
    lights = [o for o in bpy.context.scene.objects if o.type == "LIGHT"]
    for o in lights:
        o.hide_render = True
    shots(prefix, SIL_VIEWS, target=VIEW_AT, dist=DIST, size=420)
    for o in lights:
        o.hide_render = False
    world.inputs[0].default_value, world.inputs[1].default_value = old
    for o in objs:
        o.data.materials.clear()
        for m in keep[o.name]:
            o.data.materials.append(m)


def save_stage(name):
    """A stage file: the scene alone, written with no path from this machine in it."""
    os.makedirs(BLEND_DIR, exist_ok=True)
    path = os.path.join(BLEND_DIR, name)
    scene = bpy.context.scene
    scene.render.filepath = "//" + "_" * 1020
    scene.render.filepath = "//"
    for img in bpy.data.images:
        if img.filepath_raw and not img.filepath_raw.startswith("//"):
            img.filepath_raw = bpy.path.relpath(img.filepath_raw, start=BLEND_DIR)
        for packed in img.packed_files:
            packed.filepath = img.filepath_raw
    if os.path.exists(path):
        os.remove(path)
    bpy.data.libraries.write(path, {scene}, path_remap="RELATIVE_ALL", compress=True)
    print("STAGE FILE", path, os.path.getsize(path) // 1024, "KB", flush=True)
    return path


if __name__ == "__main__" and STAGE == "blockout":
    pieces = blockout()
    stage_setup((0.42, 0.45, 0.5, 1))
    clay_materials(pieces)
    silhouette(list(pieces.values()), os.path.join(STAGE_DIR, "sil"))
    shots(os.path.join(STAGE_DIR, STAGE), VIEWS[:6], target=VIEW_AT, dist=DIST, size=480)
    save_stage("Dawn_Phoenix_Blockout.blend")
    print("DONE", flush=True)

if __name__ == "__main__" and STAGE in ("anatomy", "wings", "feathers", "materials"):
    pieces, frames, data = build_hi(LEVEL)
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.42, 0.45, 0.5, 1))
    if STAGE == "materials":
        mat = hi_material(ao_distance=0.025, ao_share=0.35)
        for o in pieces.values():
            o.data.materials.clear()
            o.data.materials.append(mat)
    else:
        clay_materials(pieces)
        silhouette(list(pieces.values()), os.path.join(STAGE_DIR, "sil"))
    shots(os.path.join(STAGE_DIR, STAGE), VIEWS + FACE_VIEWS + FAR_VIEWS, target=VIEW_AT, dist=DIST, size=600)
    if STAGE == "anatomy":
        save_stage("Dawn_Phoenix_Anatomy.blend")
    elif STAGE == "wings":
        save_stage("Dawn_Phoenix_Wings.blend")
    print("DONE", flush=True)


# ---------- the game model (stage 7: optimisation) ----------
SKIN_QUADS = (3500, 3700, 3300, 3900)
SKIN_TRIS = 4000          # after the reduction that spares the head (the head is then subdivided once more)
TRI_LIMIT = 20000
TEXELS = {"Skin": 1.3, "EyeL": 6.0, "EyeR": 6.0, "LidUL": 3.0, "LidUR": 3.0, "LidLL": 3.0, "LidLR": 3.0, "BeakUpper": 3.2, "BeakLower": 2.6,
          "Crest": 1.6, "WingL": 0.62, "WingR": 0.62, "ArmL": 0.4, "ArmR": 0.4, "Tail": 0.62, "Legs": 1.2, "Talons": 1.2, "NeckFeathers": 1.3,
          "ChestFeathers": 1.2, "BodyFeathers": 0.85}


def truest(base, name, targets, limit=0.012):
    """QuadriFlow can wreck a small form and leave the mesh checks green: try several, measure each against the sculpt, keep the truest."""
    tree = tree_of(base)
    best, best_gap = None, 1e9
    for quads in targets:
        o = pet_kit.retopo_skin(base, N + "Try", quads)
        gap = pet_kit.surface_gap(o, tree)
        print("TRY", name, quads, len(o.data.polygons), "gap", round(gap, 4), flush=True)
        if gap < best_gap:
            if best:
                bpy.data.objects.remove(best, do_unlink=True)
            best, best_gap = o, gap
        else:
            bpy.data.objects.remove(o, do_unlink=True)
        if gap < 0.004:
            break
    assert best_gap < 0.01, name + ": every re-mesh strayed from the sculpt"
    best.name = N + name + "Low"
    for v in best.data.vertices:
        v.co = v.co.lerp(tree.find_nearest(v.co)[0], 0.85)
    return best


def skin_low(base):
    """Even quads over the whole skin, then reduced where the body is broad and plain, the head spared: the face, brows and beak root keep their
    detail (a uniform re-mesh gave the head a tenth of the triangles and melted its brows)."""
    o = truest(base, "Skin", SKIN_QUADS)
    P = verts(o)
    hz = np.linalg.norm((P - np.array(tuple(HEAD_C))) / np.array((1.0, 0.85, 1.0)), axis=1)
    keep = np.clip(1 - smooth(0.065, 0.1, hz), 0, 1)
    nf, nd = nearest_on(NECK, P)
    keep = np.maximum(keep, 0.45 * (1 - smooth(0.06, 0.09, nd)) * smooth(0.5, 0.9, nf))
    g = o.vertex_groups.new(name="keep")
    for i, w in enumerate(keep):
        g.add([i], float(w), "REPLACE")
    before = len(o.data.polygons)
    head_before = int((hz < 0.08).sum())
    pet_kit.apply_mods(o, [("DECIMATE", {"decimate_type": "COLLAPSE", "ratio": SKIN_TRIS / before, "vertex_group": "keep",
                                         "invert_vertex_group": True, "vertex_group_factor": 4.0, "use_collapse_triangulate": True})])
    o.vertex_groups.clear()
    P = verts(o)
    hz = np.linalg.norm((P - np.array(tuple(HEAD_C))) / np.array((1.0, 0.85, 1.0)), axis=1)
    print("SKIN REDUCED", before, "->", len(o.data.polygons), "head verts", head_before, "->", int((hz < 0.08).sum()), flush=True)
    # the head once more finely: its faces split, the new points laid back on the sculpt
    tree = tree_of(base)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    def in_head(v):
        q = v.co - HEAD_C
        return math.sqrt(q.x ** 2 + (q.y / 0.85) ** 2 + q.z ** 2) < 0.074
    edges = [e for e in bm.edges if in_head(e.verts[0]) and in_head(e.verts[1])]
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    for v in bm.verts:
        if in_head(v):
            v.co = v.co.lerp(tree.find_nearest(v.co)[0], 0.9)
    bm.to_mesh(o.data)
    bm.free()
    print("HEAD SUBDIVIDED: skin", len(o.data.polygons), flush=True)
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def paint_uv(o, meta, colour, plumes, images, pad=2.5):
    """A feather mesh's colour and roughness written straight into its own UV islands from each feather's own place (which feather, how far along
    and across, upper or lower face), and its normals flat: exact, where a ray bake through layers of thin feathers caught the wrong one (black
    and torn patches, seen on the first build)."""
    idx, uu, vv, top = meta
    P = verts(o)
    color, normal, rough = images
    W, H = color.size
    uv = o.data.uv_layers.active.data
    xs_all, ys_all, fi, a_i, b_i, c_i, w0s, w1s, inside = [], [], [], [], [], [], [], [], []
    for poly in o.data.polygons:
        loops = list(poly.loop_indices)
        vs = list(poly.vertices)
        A, B, C = [np.array(uv[l].uv) * (W, H) for l in loops[:3]]
        lo = np.floor(np.minimum(np.minimum(A, B), C) - pad).astype(int)
        hi = np.ceil(np.maximum(np.maximum(A, B), C) + pad).astype(int)
        lo, hi = np.clip(lo, 0, (W - 1, H - 1)), np.clip(hi, 0, (W - 1, H - 1))
        d = (B[1] - C[1]) * (A[0] - C[0]) + (C[0] - B[0]) * (A[1] - C[1])
        if abs(d) < 1e-9:
            continue
        ys, xs = np.mgrid[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
        qx, qy = xs.ravel() + 0.5, ys.ravel() + 0.5
        w0 = ((B[1] - C[1]) * (qx - C[0]) + (C[0] - B[0]) * (qy - C[1])) / d
        w1 = ((C[1] - A[1]) * (qx - C[0]) + (A[0] - C[0]) * (qy - C[1])) / d
        w2 = 1 - w0 - w1
        size = max(np.linalg.norm(B - A), np.linalg.norm(C - B), np.linalg.norm(A - C), 1.0)
        near = (w0 > -pad / size) & (w1 > -pad / size) & (w2 > -pad / size)
        if not near.any():
            continue
        xs_all.append(xs.ravel()[near]); ys_all.append(ys.ravel()[near])
        w0s.append(w0[near]); w1s.append(w1[near])
        inside.append(((w0 >= 0) & (w1 >= 0) & (w2 >= 0))[near])
        a_i.append(np.full(near.sum(), vs[0])); b_i.append(np.full(near.sum(), vs[1])); c_i.append(np.full(near.sum(), vs[2]))
    xs, ys = np.concatenate(xs_all), np.concatenate(ys_all)
    w0, w1 = np.clip(np.concatenate(w0s), 0, 1), np.clip(np.concatenate(w1s), 0, 1)
    tot = np.maximum(w0 + w1, 1.0)
    w0, w1 = w0 / tot, w1 / tot
    w2 = 1 - w0 - w1
    ia, ib, ic = np.concatenate(a_i), np.concatenate(b_i), np.concatenate(c_i)
    ins = np.concatenate(inside)
    su = uu[ia] * w0 + uu[ib] * w1 + uu[ic] * w2
    sv = vv[ia] * w0 + vv[ib] * w1 + vv[ic] * w2
    sp = P[ia] * w0[:, None] + P[ib] * w1[:, None] + P[ic] * w2[:, None]
    col, rgh = colour(idx[ia], su, sv, top[ia], plumes, sp)
    col = col * np.where(top[ia] > 0, root_shade(su, 0.08 if colour is colour_skin_feathers else 0.22), 1.0)[:, None]
    order = np.argsort(ins, kind="stable")          # the texels just outside an island first, so those inside win
    xs, ys, col, rgh = xs[order], ys[order], col[order], np.asarray(rgh)[order]
    px = np.empty(W * H * 4, dtype=np.float32)
    color.pixels.foreach_get(px)
    px = px.reshape(H, W, 4)
    px[ys, xs, :3] = to_srgb(col)
    color.pixels.foreach_set(px.ravel())
    for img, value in ((rough, None), (normal, (0.5, 0.5, 1.0))):
        w2_, h2_ = img.size
        q = np.empty(w2_ * h2_ * 4, dtype=np.float32)
        img.pixels.foreach_get(q)
        q = q.reshape(h2_, w2_, 4)
        sx, sy = (xs * w2_ // W), (ys * h2_ // H)
        q[sy, sx, :3] = np.stack([rgh] * 3, axis=1) if value is None else value
        img.pixels.foreach_set(q.ravel())
    return int(ins.sum())


def join_meshes(objs, name):
    bm = bmesh.new()
    for o in objs:
        bm.from_mesh(o.data)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    o = bpy.data.objects.new(name, me)
    GAME.objects.link(o)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    return o


def low_beak(lower):
    up, low = beak_paths()
    path = (low if lower else up)[::2]
    path = path if path[-1] == (low if lower else up)[-1] else path + [(low if lower else up)[-1]]
    if lower:
        m = loft_beak(path, lambda f: 0.0128 * (1 - f) ** 0.8 + 0.0015, lambda f: 0.0055 * (1 - f) ** 0.6 + 0.0014, 8, lower=True)
    else:
        m = loft_beak(path, lambda f: 0.0172 * (1 - f) ** 0.72 + 0.0007, lambda f: 0.023 * (1 - f) ** 0.58 + 0.0008, 10)
    return m.finish(N + ("BeakLower" if lower else "BeakUpper") + "Low", GAME)


def build_low(pieces, frames, data):
    lows = {"Skin": skin_low(data["SkinBase"])}
    for tag in ("L", "R"):
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 18, 12)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
        lows["Wing" + tag], *meta = build_low_plumes(data["Wing" + tag], N + "Wing" + tag + "Low", GAME, 4, 1,
                                                     res=lambda p: (7, 2) if p.group <= 2 else (4, 1))
        data["Wing" + tag + "LowMeta"] = meta
    lows["BeakUpper"] = low_beak(False)
    lows["BeakLower"] = low_beak(True)
    lows["Crest"], *data["CrestLowMeta"] = build_low_plumes(data["Crest"], N + "CrestLow", GAME, 11, 2, thick=crest_thick)
    lows["Tail"], *data["TailLowMeta"] = build_low_plumes(data["Tail"], N + "TailLow", GAME, 5, 1,
                                                          res=lambda p: (14, 2) if isinstance(p, LongFeather) else (5, 1))
    arms = build_arms(N + "ArmsLow", GAME, 10, 3)
    side = read_attr(arms, "side")
    for tag, sgn in (("L", 1), ("R", -1)):
        o = bpy.data.objects.new(N + "Arm" + tag + "Low", arms.data.copy())
        GAME.objects.link(o)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.verts[i] for i in range(len(side)) if side[i] != sgn], context="VERTS")
        bm.to_mesh(o.data)
        bm.free()
        lows["Arm" + tag] = o
    bpy.data.objects.remove(arms, do_unlink=True)
    lows["Legs"] = build_legs(N + "LegsLow", GAME, 8, 6, step=2)
    lows["Talons"] = build_talons(N + "TalonsLow", GAME, 6, rings=5)
    for key in ("NeckFeathers", "ChestFeathers", "BodyFeathers"):
        lows[key], *data[key + "LowMeta"] = build_low_plumes(data[key], N + key + "Low", GAME, 4 if key == "BodyFeathers" else 6, 1,
                                                             thick=skin_feather_thick)     # (the neck's and breast's seen close: a smoother outline)
    pet_kit.triangulate(lows)
    for o in lows.values():
        for a in list(o.data.attributes):
            if a.name in ("side", "part", "along") and not a.is_internal:
                o.data.attributes.remove(o.data.attributes[a.name])
    return lows


TURNED = ("WingL", "WingR", "Tail", "Crest", "Legs", "Talons")           # free feathers (and toes): turned about their roots
LIFTED = ("NeckFeathers", "ChestFeathers", "BodyFeathers")                # feathers lying on the skin: lifted whole (turned, their far ends dug in)


def separate_coplanar(lows, metas, eps=0.0011, turn=3.2, push=0.0013, rounds=16):
    """The QA's z-fight test run over the game pieces, and mended: where two sheets of different feathers (or pieces) face the same way within a
    millimetre and overlap, the one lying on top is turned a few degrees about its own root, lifting the overlap and leaving the two no longer
    parallel (lifting it whole only pushed it into the next one up). A whole feather turns, both its faces, so it keeps its shape."""
    from mathutils.bvhtree import BVHTree
    keys = list(lows.keys())
    for rnd in range(rounds):
        verts_all, tris_all, owner = [], [], []
        groups = {}
        for oi, key in enumerate(keys):
            o = lows[key]
            me = o.data
            nv = len(me.vertices)
            if key in metas:
                gid = np.asarray(metas[key][0])
                uu = np.asarray(metas[key][1])
            else:
                bm = bmesh.new()
                bm.from_mesh(me)
                gid = np.full(nv, -1)
                g = 0
                for v in bm.verts:
                    if gid[v.index] >= 0:
                        continue
                    stack = [v]
                    gid[v.index] = g
                    while stack:
                        w = stack.pop()
                        for e in w.link_edges:
                            x = e.other_vert(w)
                            if gid[x.index] < 0:
                                gid[x.index] = g
                                stack.append(x)
                    g += 1
                bm.free()
                uu = None
            co = np.empty(nv * 3)
            me.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            for g in np.unique(gid):
                sel = np.where(gid == g)[0]
                if uu is not None:
                    root_sel = sel[uu[sel] <= uu[sel].min() + 1e-6]
                    root = Vector(co[root_sel].mean(0))
                else:
                    root = Vector(co[sel].mean(0))
                groups[(oi, int(g))] = (sel, root)
            base = len(verts_all)
            verts_all += [Vector(c) for c in co]
            for poly in me.polygons:
                vs = list(poly.vertices)
                tris_all.append([base + vs[0], base + vs[1], base + vs[2]])
                owner.append((oi, int(gid[vs[0]]), poly.normal.copy()))
        bvh = BVHTree.FromPolygons(verts_all, tris_all, epsilon=0.0)
        tri_sets = [set(t) for t in tris_all]
        fix = {}
        for ti, t in enumerate(tris_all):
            a, b, c = (verts_all[i] for i in t)
            n = owner[ti][2]
            cen = (a + b + c) / 3
            for p in (cen, cen.lerp(a, .6), cen.lerp(b, .6), cen.lerp(c, .6)):
                for _, _, tj, _ in bvh.find_nearest_range(p, eps):
                    if tj is None or tj == ti or tri_sets[ti] & tri_sets[tj] or owner[tj][:2] == owner[ti][:2]:
                        continue
                    n2 = owner[tj][2]
                    if n.dot(n2) < 0.999:
                        continue
                    a2 = verts_all[tris_all[tj][0]]
                    mine, other = (owner[ti], owner[tj]) if (p - a2).dot(n2) >= 0 else (owner[tj], owner[ti])
                    sign = 1.0
                    if keys[mine[0]] not in TURNED + LIFTED:      # the skin, eyes, lids and beak are never moved: the other goes down instead
                        if keys[other[0]] not in TURNED + LIFTED:
                            continue
                        mine, sign = other, -1.0
                    key = mine[:2]
                    if key not in fix:
                        fix[key] = (mine[2] * sign, p.copy())
        print("SEPARATE round", rnd, "feathers turned", len(fix), flush=True)
        if not fix:
            return
        for (oi, g), (n, contact) in fix.items():
            sel, root = groups[(oi, g)]
            if keys[oi] in LIFTED:
                me = lows[keys[oi]].data
                for vi in sel:
                    me.vertices[int(vi)].co += n * push
                me.update()
                continue
            r = contact - root
            r = r - n * n.dot(r)
            if r.length < 1e-5:
                r = n.orthogonal()
            axis = r.normalized().cross(n).normalized()
            rot = Matrix.Rotation(math.radians(-turn), 3, axis)
            if (rot @ r).dot(n) < 0:
                rot = Matrix.Rotation(math.radians(turn), 3, axis)
            me = lows[keys[oi]].data
            for vi in sel:
                v = me.vertices[int(vi)]
                v.co = root + rot @ (v.co - root)
            me.update()


def tris_of(o):
    dg = bpy.context.evaluated_depsgraph_get()
    me = o.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    o.evaluated_get(dg).to_mesh_clear()
    return n


def split_skin(skin):
    """The one baked skin into the hierarchy's pieces: Head, Neck and Body. The cut follows the base of the skull and the base of the neck, where the
    neck's feathers lie over it."""
    P = np.array([tuple(p.center) for p in skin.data.polygons])
    hz = P - np.array(tuple(HEAD_C))
    head = np.linalg.norm(hz / np.array((1.0, 0.85, 1.0)), axis=1) < 0.075
    head |= (P[:, 2] > 1.035) & (P[:, 1] < -0.11)
    nf, nd = nearest_on(NECK, P)
    neck = (~head) & (nf > 0.08) & (nd < 0.1) & (P[:, 2] > 0.66)
    out = {}
    for name, keep in (("Head", head), ("Neck", neck), ("Body", ~head & ~neck)):
        o = bpy.data.objects.new(N + name, skin.data.copy())
        GAME.objects.link(o)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[i] for i in range(len(keep)) if not keep[i]], context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bm.to_mesh(o.data)
        bm.free()
        out[name] = o
    bpy.data.objects.remove(skin, do_unlink=True)
    return out


HIERARCHY = {   # name in the game: (its piece, its parent)
    "Body": ("Body", "Root"), "Neck": ("Neck", "Body"), "Head": ("Head", "Neck"), "BeakUpper": ("BeakUpper", "Head"), "BeakLower": ("BeakLower", "Head"),
    "EyeL": ("EyeL", "Head"), "EyeR": ("EyeR", "Head"), "LidUpperL": ("LidUL", "Head"), "LidUpperR": ("LidUR", "Head"), "LidLowerL": ("LidLL", "Head"),
    "LidLowerR": ("LidLR", "Head"), "Crest": ("Crest", "Head"), "NeckFeathers": ("NeckFeathers", "Neck"), "Chest": ("ChestFeathers", "Body"),
    "BodyFeathers": ("BodyFeathers", "Body"), "LeftWing": ("ArmL", "Body"), "RightWing": ("ArmR", "Body"), "LeftWingFeathers": ("WingL", "LeftWing"),
    "RightWingFeathers": ("WingR", "RightWing"), "Legs": ("Legs", "Body"), "Talons": ("Talons", "Legs"), "TailFeathers": ("Tail", "Body"),
}


def assemble(lows, skin_parts):
    """Ground it (its lowest talon at z = 0), name every piece, and hang them in the hierarchy under a Root empty at the origin. Every transform is
    the identity: nothing to apply."""
    pieces = dict(lows)
    pieces.update(skin_parts)
    zmin = min(min(v.co.z for v in o.data.vertices) for o in pieces.values())
    for o in pieces.values():
        o.data.transform(Matrix.Translation((0, 0, -zmin)))
        o.data.update()
    root = bpy.data.objects.new(N + "Root", None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.2
    GAME.objects.link(root)
    named = {"Root": root}
    for game_name, (key, _) in HIERARCHY.items():
        o = pieces[key]
        o.name = N + game_name
        o.data.name = N + game_name
        named[game_name] = o
    for game_name, (_, parent) in HIERARCHY.items():
        named[game_name].parent = named[parent]
    return named, zmin


def set_ortho(cam, on, scale=2.6):
    cam.data.type = "ORTHO" if on else "PERSP"
    cam.data.ortho_scale = scale


def wing_pose_rig(named, data, zmin):
    """A wing-only skeleton for the QA renders of the wings extended and folded (not exported: the creature's real rig comes after approval).
    The arm follows its bones by where it lies along them; each feather follows the bone at its root, the hand's feathers taking the hand."""
    arm = bpy.data.armatures.new("QA_WingPose")
    rig = bpy.data.objects.new("QA_WingPose", arm)
    GAME.objects.link(rig)
    pet_kit.select_only([rig])
    bpy.ops.object.mode_set(mode="EDIT")
    lift = V(0, 0, -zmin)
    for tag, side in (("L", 1), ("R", -1)):
        prev = None
        for k, f in enumerate(ARM_F):
            b = arm.edit_bones.new("Wing%s%d" % (tag, k + 1))
            b.head = mir(along(ARM_PATH, f), side) + lift
            b.tail = b.head + V(0, 0, 0.04)
            if prev:
                b.parent = prev
            prev = b
    bpy.ops.object.mode_set(mode="OBJECT")
    names = lambda tag: ["Wing%s%d" % (tag, k + 1) for k in range(4)]
    from pet_kit import chain_weight
    for tag, side, arm_key, wing_key in (("L", 1, "LeftWing", "LeftWingFeathers"), ("R", -1, "RightWing", "RightWingFeathers")):
        o = named[arm_key]
        P = verts(o) - np.array((0, 0, -zmin))
        f, _ = nearest_on([mir(p, side) for p in ARM_PATH], P)
        pet_kit.weigh(o, [chain_weight(names(tag), ARM_F, float(x)) for x in f])
        o = named[wing_key]
        P = verts(o) - np.array((0, 0, -zmin))
        f, _ = nearest_on([mir(p, side) for p in ARM_PATH], P)
        pet_kit.weigh(o, [chain_weight(names(tag), ARM_F, float(x)) for x in f])
        for o in (named[arm_key], named[wing_key]):
            md = o.modifiers.new("QA_WingPose", "ARMATURE")
            md.object = rig
    return rig


def combo(first, then):
    """Two turns (axis, degrees) in the model's axes, the first applied first, as one (axis, degrees, move) for pet_kit.pose."""
    r = Matrix.Rotation(math.radians(then[1]), 3, Vector(then[0])) @ Matrix.Rotation(math.radians(first[1]), 3, Vector(first[0]))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (0, 0, 0))


def wing_pose(rig, kind):
    """extended: spread to the full span and lifted; folded: elbow and wrist drawn in and the hand laid back along the body."""
    spec = {}
    for tag, s in (("L", 1), ("R", -1)):
        if kind == "extended":       # spread level and wide: the full span
            spec["Wing%s1" % tag] = ((0, 1, 0), s * 30, (0, 0, 0))
            spec["Wing%s2" % tag] = ((0, 0, 1), -s * 14, (0, 0, 0))
            spec["Wing%s3" % tag] = ((0, 0, 1), -s * 10, (0, 0, 0))
        elif kind == "folded":       # half closed: lowered, the elbow drawn back and the hand dropped and turned back along the body
            spec["Wing%s1" % tag] = combo(((0, 1, 0), s * 50), ((0, 0, 1), s * 10))
            spec["Wing%s2" % tag] = ((0, 0, 1), s * 42, (0, 0, 0))
            spec["Wing%s3" % tag] = combo(((0, 1, 0), s * 40), ((0, 0, 1), s * 62))
    pet_kit.pose(rig, spec)


def qa_lighting(dark=(0.085, 0.085, 0.095, 1)):
    w = bpy.context.scene.world.node_tree.nodes["Background"]
    w.inputs[0].default_value = dark
    w.inputs[1].default_value = 1.0


if __name__ == "__main__" and STAGE == "final":
    pieces, frames, data = build_hi(ORDER.index("materials"))
    mat = hi_material(ao_distance=0.025, ao_share=0.35)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.085, 0.085, 0.095, 1))
    lows = build_low(pieces, frames, data)
    separate_coplanar(lows, {k: data[src + "LowMeta"][:2] for k, src in (("WingL", "WingL"), ("WingR", "WingR"), ("Tail", "Tail"), ("Crest", "Crest"),
                                                                       ("NeckFeathers", "NeckFeathers"), ("ChestFeathers", "ChestFeathers"),
                                                                       ("BodyFeathers", "BodyFeathers"))})
    tris = {k: tris_of(o) for k, o in lows.items()}
    print("LOW TRIS", sum(tris.values()), tris, flush=True)
    assert sum(tris.values()) < TRI_LIMIT, "over the triangle limit"
    pet_kit.unwrap(lows, [(lambda p: p.center.z > 1.0 and p.center.y < -0.08, 4.0), (lambda p: p.center.z > 0.7 and p.center.y < -0.02, 1.8), (None, 1.3)],
                   {}, shape="CONCAVE", angle=52, texels=TEXELS, margin=0.0035)
    pieces["ArmL"] = pieces["ArmR"] = pieces.pop("Arms")       # (one high-detail piece holds both arms)
    skin_reach = (0.008, 0.02)
    feather_reach = (0.0035, 0.009)
    FEATHERS = {"WingL": (colour_wing, "WingL"), "WingR": (colour_wing, "WingR"), "Tail": (colour_tail, "Tail"), "Crest": (colour_crest, "Crest"),
                "NeckFeathers": (colour_skin_feathers, "NeckFeathers"), "ChestFeathers": (colour_skin_feathers, "ChestFeathers"),
                "BodyFeathers": (colour_skin_feathers, "BodyFeathers")}
    solid = {k: o for k, o in lows.items() if k not in FEATHERS}
    baked = pet_kit.bake_all(solid, pieces, mat, size=1024, colour_size=2048, metal=False, fill=(0.8, 0.45, 0.15, 1), far=("Skin",), reach=feather_reach,
                             far_reach=skin_reach, reaches={"Legs": (0.004, 0.01), "Talons": (0.003, 0.008), "BeakUpper": (0.003, 0.008),
                                                            "BeakLower": (0.003, 0.008), "Crest": (0.004, 0.01)})
    baked.name = N + "Plumage"
    images = [bpy.data.images[PET + "_Color"], bpy.data.images[PET + "_Normal"], bpy.data.images[PET + "_Roughness"]]
    for img in images:                  # (edited while packed, the packed copy keeps the old pixels: unpack, reload the saved bake, edit, save, pack)
        if img.packed_file:
            img.unpack(method="REMOVE")
        img.reload()
    for key, (colour, src) in FEATHERS.items():
        o = lows[key]
        o.data.materials.clear()
        o.data.materials.append(baked)
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
        print("PAINTED", key, paint_uv(o, data[src + "LowMeta"], colour, data[src], images), "texels", flush=True)
    for img in images:
        img.update()
        img.save()
        img.pack()
    print("UV OVERLAP TEXELS", {k: pet_kit.uv_overlap_texels(o.data, 1024) for k, o in lows.items() if k in ("Skin", "WingL", "Tail")}, flush=True)
    skin_parts = split_skin(lows.pop("Skin"))
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    named, zmin = assemble(lows, skin_parts)
    meshes = [o for o in named.values() if o.type == "MESH"]
    counts = {o.name: tris_of(o) for o in meshes}
    total = sum(counts.values())
    print("FINAL TRIS", total, counts, flush=True)
    assert total < TRI_LIMIT
    dims = [max((o.matrix_world @ v.co)[i] for o in meshes for v in o.data.vertices) - min((o.matrix_world @ v.co)[i] for o in meshes for v in o.data.vertices) for i in range(3)]
    print("DIMENSIONS m", [round(d, 3) for d in dims], flush=True)
    beak_tip = max((v.co for v in named["BeakUpper"].data.vertices), key=lambda c: -c.y)
    tail_base = TAIL_ROOT + V(0, 0, -zmin)
    span = dims[0]
    body_len = (beak_tip - tail_base).length
    print("BEAK TIP", tuple(round(c, 3) for c in beak_tip), "TAIL BASE", tuple(round(c, 3) for c in tail_base), "BODY LENGTH", round(body_len, 3),
          "SPAN", round(span, 3), "RATIO", round(span / body_len, 2), flush=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    # the stage file and the FBX, from the clean model (before any review pose)
    pet_kit.select_only(meshes + [named["Root"]], named["Root"])
    fbx = os.path.join(OUT_DIR, PET + ".fbx")
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={"MESH", "EMPTY"}, axis_forward="-Z", axis_up="Y",
                             apply_scale_options="FBX_SCALE_UNITS", apply_unit_scale=True, bake_space_transform=False, path_mode="COPY",
                             embed_textures=True, mesh_smooth_type="FACE", use_tspace=True, add_leaf_bones=False, bake_anim=False)
    # the exporter records where each map was copied from: keep this machine's home out of it (same length, so the binary stays valid)
    raw = open(fbx, "rb").read()
    home = os.path.expanduser("~").encode()
    if home.startswith(b"/Users/") and len(home) > 7:
        stand_in = (b"/Users/" + b"user"[:len(home) - 7].ljust(len(home) - 7, b"_"))
        raw = raw.replace(home + b"/", stand_in + b"/")
        open(fbx, "wb").write(raw)
    print("FBX", fbx, os.path.getsize(fbx) // 1024, "KB", flush=True)
    save_stage("Dawn_Phoenix_Final.blend")
    # the QA renders (section 13): neutral studio light on a dark grey ground
    os.makedirs(FINAL_DIR, exist_ok=True)
    qa_lighting()
    scene = bpy.context.scene
    scene.cycles.samples = 64
    cam = bpy.data.objects["ShowCam"]
    at = (0, 0.18, 0.72 - zmin + 0.05)
    set_ortho(cam, True, 2.3)
    shots(os.path.join(FINAL_DIR, "ortho"), [(0, -1, 0.0), (1, 0, 0.0), (0, 1, 0.0)], target=at, dist=6.0, size=1100)
    for k, name in enumerate(("01_front_ortho", "02_side_ortho", "03_rear_ortho")):
        os.replace(os.path.join(FINAL_DIR, "ortho_%d.png" % k), os.path.join(FINAL_DIR, name + ".png"))
    set_ortho(cam, False)
    shots(os.path.join(FINAL_DIR, "tq"), [(0.62, -0.72, 0.25), (-0.62, -0.72, 0.18), (0, -0.05, 1)], target=at, dist=4.6, size=1100)
    os.replace(os.path.join(FINAL_DIR, "tq_0.png"), os.path.join(FINAL_DIR, "04_three_quarter.png"))
    os.replace(os.path.join(FINAL_DIR, "tq_1.png"), os.path.join(FINAL_DIR, "04b_three_quarter_right.png"))
    os.replace(os.path.join(FINAL_DIR, "tq_2.png"), os.path.join(FINAL_DIR, "04c_top.png"))
    shots(os.path.join(FINAL_DIR, "face"), [(0.55, -0.83, 0.08, 0.5, (0, -0.23, 1.065 - zmin)), (0, -1, 0.04, 0.45, (0, -0.23, 1.065 - zmin))], target=at, size=900)
    os.replace(os.path.join(FINAL_DIR, "face_0.png"), os.path.join(FINAL_DIR, "08_head_three_quarter.png"))
    os.replace(os.path.join(FINAL_DIR, "face_1.png"), os.path.join(FINAL_DIR, "09_head_front.png"))
    # a player's view of it: from behind and above, about 25 studs off (the model's 1.7 m span is about 5.5 studs: 1 m is about 3.2 studs), and 45
    shots(os.path.join(FINAL_DIR, "far"), [(0.45, 0.8, 0.55, 7.8), (0.5, 0.8, 0.45, 14.0)], target=at, size=700)
    os.replace(os.path.join(FINAL_DIR, "far_0.png"), os.path.join(FINAL_DIR, "10_game_distance_25studs.png"))
    os.replace(os.path.join(FINAL_DIR, "far_1.png"), os.path.join(FINAL_DIR, "10b_game_distance_45studs.png"))
    rig = wing_pose_rig(named, data, zmin)
    for kind, fname, view in (("extended", "05_wings_extended", (0.1, -1, 0.35)), ("folded", "06_wings_folded", (0.62, -0.72, 0.22))):
        wing_pose(rig, kind)
        shots(os.path.join(FINAL_DIR, "pose"), [view], target=at, dist=4.6, size=1100)
        os.replace(os.path.join(FINAL_DIR, "pose_0.png"), os.path.join(FINAL_DIR, fname + ".png"))
    wing_pose(rig, "rest")
    # the beauty render: a warmer key and a soft rim, still neutral, still no effects
    for o in scene.objects:
        if o.type == "LIGHT" and o.name == "Key":
            o.data.energy = 2.6
            o.data.color = (1.0, 0.96, 0.9)
        if o.type == "LIGHT" and o.name == "Rim":
            o.data.energy = 1.6
    scene.cycles.samples = 160
    shots(os.path.join(FINAL_DIR, "beauty"), [(0.5, -0.78, 0.18)], target=at, dist=4.2, size=1400)
    os.replace(os.path.join(FINAL_DIR, "beauty_0.png"), os.path.join(FINAL_DIR, "07_beauty.png"))
    print("DONE", flush=True)
