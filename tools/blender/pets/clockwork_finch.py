"""The Qi Clockwork Finch (Uncommon, Magical machinery; Ancient Grove Egg): "Built by a forgotten artisan and wound with pure Qi. It still sings the hour
of a city that no longer exists."

A new creature, in a design language of its own: a cloisonne automaton. A songbird built the way the old singing-bird boxes were, of fitted shells and
plates, every one of them gilt wire bent into cells and filled with fired enamel, in a goldfinch's colours: a coral mask round its beak, ivory cheeks, a
lapis cap, a turquoise back and an ivory-buff breast, each scaled in little feather-shaped cells; lapis-black wing and tail feathers, each a plate of its
own with a gold shaft and ivory tip spots, a bar of real gold across each wing. A gilt finch's beak in two halves; onyx bead eyes in gold bezels, with
brass shutter lids; a brass collar at its neck, toothed like a gear, Qi light seeping from the seam; thin brass legs with pin joints and curled toes. On
its back, its winding key: an old jade bi disc on a brass stem, slowly turning, Qi glowing in its hole.

    Blender -b --factory-startup --python-exit-code 1 -P tools/blender/pets/clockwork_finch.py -- [clay|paint|rig|all] [review dir]

clay: form review in neutral clay. paint: the painted high-detail model. rig: the game mesh and skeleton, posed and checked. all: also the unwrap,
bake, the file and the FBX. Faces -Y, Z up, 1 unit = 1 metre. +X is its left. It hovers: its middle about 0.45 m up. The maps go to
assets/pets/AncientGroveEgg/.

What touches what: every piece is rigid on its own bone, as an automaton's are. The body shell is one piece; the head shell sits on the collar, its
lower part inside it; the collar is half sunk in the body; the beak halves are set in the head's front; the eyes in their bezels, sunk in the head, the
shutter lids round them; each wing's covert plate is rooted in the body's shoulder, its feathers rooted under the covert; the tail feathers rooted in
the body's rump; the key's stem rooted in the back, the disc on the stem's end; the legs rooted under the belly; the seam light lies in the collar's
seam, the key light in the disc's hole.
"""
import math
import os
import re
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector  # noqa: F401
from mathutils.bvhtree import BVHTree  # noqa: F401

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pet_kit
from pet_kit import *  # noqa: F401,F403

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STAGE = ARGS[0] if ARGS else "paint"
REVIEW = ARGS[1] if len(ARGS) > 1 else "/tmp"
PET = "QiClockworkFinch"
N = PET + "_"
HI, GAME = pet_kit.start(PET, "AncientGroveEgg")

# ---------- colours: fired enamel in gilt wire, brass, onyx and old jade ----------
GOLD, GOLD_DEEP = rgb(236, 192, 96), rgb(170, 122, 48)            # gilt wire and gold leaf (metal)
BRASS = rgb(212, 166, 84)                                          # brass parts (metal)
LAPIS, LAPIS_DEEP = rgb(34, 58, 150), rgb(20, 26, 70)
TURQ, TURQ_DEEP = rgb(40, 182, 172), rgb(22, 120, 128)
CORAL, CORAL_DEEP = rgb(226, 74, 58), rgb(170, 40, 40)
IVORY, BUFF = rgb(246, 240, 226), rgb(240, 208, 168)
ONYX = rgb(14, 12, 18)
JADE, JADE_DEEP, JADE_LIGHT = rgb(120, 196, 156), rgb(50, 128, 98), rgb(196, 236, 210)
QI_HEX, GLINT_HEX = "1cf58f", "ffffff"

# ---------- the frame of it ----------
BODY_C, BODY_R = V(0, 0.03, 0.42), (0.1, 0.142, 0.108)            # an egg along its length, a little nose-up
BODY_PITCH = math.radians(12)
BODY_PEAR = 0.14                                                   # fuller at the breast
NECK = V(0, -0.088, 0.488)                                         # the collar's middle: where the head turns
NECK_AXIS = V(0, -0.45, 0.89).normalized()                         # the collar's axis, up through the neck
COLLAR_R, COLLAR_TUBE = 0.052, 0.011
HEAD_C, HEAD_R = V(0, -0.128, 0.545), 0.084                       # a big round finch's head
BEAK_ROOT, BEAK_DIR = V(0, -0.196, 0.534), V(0, -1, -0.12).normalized()
BEAK_LEN, BEAK_R = 0.058, 0.027
EYE_R = 0.021
EYE_C = V(0.052, -0.176, 0.556)
EYE_AXIS = V(0.62, -0.76, 0.16).normalized()
LID_UP, LID_LOW = (54.0, 124.0, 0.0022), (-50.0, -126.0, 0.002)   # brass shutters, wide open
LID_TILT = -4.0
BLINK_U, BLINK_L = 78.0, 34.0                                       # (the two add past the 104 degrees between the edges)
SHOULDER = V(0.078, -0.03, 0.48)                                   # (left) a wing's root
WING_SPAN = V(1.0, 0.12, 0.62).normalized()                        # its half-spread wing reaches out and up in a V (level, they read as rotor blades)
WRIST = SHOULDER + WING_SPAN * 0.13
PRIMARIES = 7
TAIL_ROOT, TAIL_DIR = V(0, 0.16, 0.392), V(0, 1, -0.32).normalized()
TAIL_FEATHERS = 5
KEY_ROOT, KEY_DIR = V(0, 0.1, 0.505), V(0, 0.8, 0.6).normalized()        # (rising up its back, it read as an antenna on its head)
KEY_STEM, KEY_DISC_R, KEY_HOLE_R, KEY_THICK = 0.07, 0.046, 0.015, 0.012
LEG = [V(0.034, 0.03, 0.34), V(0.04, 0.012, 0.282), V(0.04, -0.008, 0.262)]     # (left) hip in the belly, ankle, foot


def arc_lengths(path):
    a = np.array([tuple(p) for p in path])
    return np.concatenate([[0], np.cumsum(np.linalg.norm(a[1:] - a[:-1], axis=1))])


def ell_dist(P, c, r):
    return np.linalg.norm((P - np.array(tuple(c))) / np.array(r), axis=1)


def basis(axis):
    """Two directions square to an axis (the first as level as it can be)."""
    a = axis.normalized()
    s = a.cross(V(0, 0, 1))
    if s.length < 1e-4:
        s = a.cross(V(0, 1, 0))
    s.normalize()
    return s, a.cross(s).normalized()


BODY_M = Matrix.Rotation(BODY_PITCH, 3, "X")                       # its body's own frame: y along it, nose up


def body_local(P):
    return (P - np.array(tuple(BODY_C))) @ np.array(BODY_M)


# ---------- shells ----------
def body_shell(seg=640, rings=480, coll=None, name="BodyHi"):
    m = Mesh()
    m.ball(V(0, 0, 0), BODY_R, seg, rings)
    o = m.finish(N + name, coll or HI)
    P = verts(o)
    k = 1 + BODY_PEAR * np.clip(-P[:, 1] / BODY_R[1], -1, 1)          # fuller toward its breast
    P[:, 0] *= k
    P[:, 2] *= 1 + 0.6 * BODY_PEAR * np.clip(-P[:, 1] / BODY_R[1], -1, 1)
    P = P @ np.array(BODY_M).T + np.array(tuple(BODY_C))
    set_verts(o, P)
    o.data.update()
    return o


def head_shell(seg=512, rings=384, coll=None, name="HeadHi"):
    m = Mesh()
    m.ball(HEAD_C, (HEAD_R, HEAD_R * 0.98, HEAD_R * 0.96), seg, rings)
    o = m.finish(N + name, coll or HI)
    P, Nn = verts(o), normals(o)
    # soft cheeks below the eyes, and a little brow over them
    h = np.zeros(len(P))
    for side in (1, -1):
        h += 0.008 * np.exp(-np.sum(((P - np.array((side * 0.055, -0.15, 0.52))) / np.array((0.03, 0.03, 0.025))) ** 2, axis=1))
    set_verts(o, P + Nn * h[:, None])
    return o


def revolve(m, centre, axis, profile, nt):
    """A solid turned round an axis: profile is (along, radius) from one pole round to the other (radius 0 at both ends)."""
    s, t = basis(axis)
    rings, poles = [], []
    for i, (a, r) in enumerate(profile):
        c = centre + axis * a
        if r < 1e-6:
            poles.append((i, m.bm.verts.new(c)))
            rings.append(None)
        else:
            rings.append([m.bm.verts.new(c + (s * math.cos(TAU * k / nt) + t * math.sin(TAU * k / nt)) * r) for k in range(nt)])
    for i in range(len(profile) - 1):
        a, b = rings[i], rings[i + 1]
        if a is None:
            pole = dict(poles)[i]
            for k in range(nt):
                m.bm.faces.new((pole, b[(k + 1) % nt], b[k]))
        elif b is None:
            pole = dict(poles)[i + 1]
            for k in range(nt):
                m.bm.faces.new((a[k], a[(k + 1) % nt], pole))
        else:
            for k in range(nt):
                m.bm.faces.new((a[k], a[(k + 1) % nt], b[(k + 1) % nt], b[k]))


def torus(m, centre, axis, R, r, nt=64, ns=16, teeth=0, tooth=0.0):
    """A ring round an axis; teeth: bumps round its outside (a gear's)."""
    s, t = basis(axis)
    rings = []
    for k in range(nt):
        a = TAU * k / nt
        out = s * math.cos(a) + t * math.sin(a)
        bump = tooth * smooth(-0.2, 0.2, math.cos(a * teeth)) if teeth else 0.0
        rings.append([m.bm.verts.new(centre + out * (R + (r + bump * max(0.0, math.cos(TAU * j / ns))) * math.cos(TAU * j / ns)) + axis * (r * math.sin(TAU * j / ns))) for j in range(ns)])
    for k in range(nt):
        for j in range(ns):
            a, b = rings[k], rings[(k + 1) % nt]
            m.bm.faces.new((a[j], b[j], b[(j + 1) % ns], a[(j + 1) % ns]))


def build_collar(coll, nt=96, ns=16, low=False):
    m = Mesh()
    torus(m, NECK, NECK_AXIS, COLLAR_R, COLLAR_TUBE, nt if not low else 32, ns if not low else 8, teeth=0 if low else 24, tooth=0.0035)
    return m.finish(N + "Collar" + ("Low" if low else "Hi"), coll)


def build_beak(coll, nt=48, nl=24, low=False):
    """A finch's short, deep conical beak, in two halves (the lower opens). Tagged: lower."""
    s, t = V(1, 0, 0), BEAK_DIR.cross(V(1, 0, 0)).normalized()
    if t.z < 0:
        t = -t
    m = Mesh()
    lay = m.bm.verts.layers.int.new("lower")
    nt, nl = (16, 6) if low else (nt, nl)
    for half in (0, 1):
        before = set(m.bm.verts)
        rows = []
        for i in range(nl + 1):
            f = i / nl
            r = BEAK_R * (1 - f) ** 0.85 + 0.0008
            c = BEAK_ROOT + BEAK_DIR * (BEAK_LEN * f - 0.012) + t * (-0.004 * f)
            ring = []
            for k in range(nt // 2 + 1):
                a = math.pi * k / (nt // 2) + (0 if half == 0 else math.pi)       # upper half: 0..pi (up), lower: pi..2pi
                ry = r * (1.0 if half == 0 else 0.82)
                ring.append(m.bm.verts.new(c + s * (math.cos(a) * r * 0.92) + t * (math.sin(a) * ry)))
            rows.append(ring)
        for i in range(nl):
            for k in range(nt // 2):
                m.bm.faces.new((rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k]))
        # the flat cut where the two halves meet, and the root closed
        for i in range(nl):
            m.bm.faces.new((rows[i][0], rows[i + 1][0], rows[i + 1][-1], rows[i][-1]))
        m.bm.faces.new(rows[0])
        tip = m.bm.verts.new(BEAK_ROOT + BEAK_DIR * (BEAK_LEN * 1.02 - 0.012))
        for k in range(nt // 2):
            m.bm.faces.new((rows[-1][k], rows[-1][k + 1], tip))
        for v in m.bm.verts:
            if v not in before:
                v[lay] = half
    return m.finish(N + "Beak" + ("Low" if low else "Hi"), coll)


def build_bezels(coll, nt=48, ns=10, low=False):
    m = Mesh()
    for side in (1, -1):
        c = mir(EYE_C, side)
        ax = mir(EYE_AXIS, side)
        torus(m, c + ax * (EYE_R * 0.55), ax, EYE_R * 0.86, 0.0032, 20 if low else nt, 6 if low else ns)
    return m.finish(N + "Bezels" + ("Low" if low else "Hi"), coll)


# ---------- feathers: each a thin enamel plate ----------
def feather_point(root, along, side_dir, length, width, curl=0.0, cup=0.06, twist=0.0):
    nrm = along.cross(side_dir).normalized()

    def point(u, v):
        s = v * 2 - 1
        w = width * (0.42 + 0.58 * min(1.0, u / 0.3))
        if u > 0.6:
            w *= math.sqrt(max(0.0, 1 - ((u - 0.6) / 0.4) ** 2)) * 0.97 + 0.03
        w *= 0.78 if s < 0 else 1.0                                   # the leading vane narrower
        ss = s * w
        p = root + along * (u * length) + side_dir * ss
        p += nrm * (cup * width * (1 - s * s) - curl * length * u * u + twist * ss * u)
        return tuple(p)
    return point


def feather_thick(u, v):
    return 0.0036 * (1 - 0.4 * u) + 0.0012


def wing_plane(side):
    """A wing's own plane: its span, the way back across it, and its upper face."""
    sp = mir(WING_SPAN, side)
    wb = V(0, 0.62, -0.78)                 # its trailing edge back and down: the wing's face turned toward you (level, from the front it was a line)
    wb = (wb - sp * wb.dot(sp)).normalized()
    n = sp.cross(wb).normalized()
    if n.z < 0:
        n = -n
    return sp, wb, n


def in_plane(side, a):
    """A direction in the wing's plane, a radians back from its span; and the in-plane direction square to it, toward its trailing edge."""
    sp, wb, n = wing_plane(side)
    d = (sp * math.cos(a) + wb * math.sin(a)).normalized()
    sd = n.cross(d).normalized()
    if sd.dot(wb) < 0 and abs(a) < 1.2:
        sd = -sd
    elif abs(a) >= 1.2 and sd.dot(sp) > 0:
        sd = -sd
    return d, sd, n


def wing_feathers(side):
    """Each of a wing's plates: (kind, root, along, side_dir, length, width). The broad covert over the arm; the primaries fanning from the wrist, each a
    little under the one before; the secondaries along the arm, under the covert."""
    sp, wb, n = wing_plane(side)
    out = []
    d, sd, _ = in_plane(side, math.radians(12))
    out.append(("covert", mir(SHOULDER, side) + sp * 0.006 + n * 0.008, d, sd, 0.14, 0.062))      # (rooted further in, its underside grazed the shoulder)
    wrist = mir(WRIST, side)
    for k in range(PRIMARIES):
        f = k / (PRIMARIES - 1)
        d, sd, _ = in_plane(side, math.radians(-6 + 64 * f))
        out.append(("primary", wrist - d * 0.03 - n * (0.0045 * k), d, sd, 0.17 - 0.035 * f, 0.044))
    for k in range(3):                                                  # (from nearer its shoulder, they cut into its flanks on the downstroke)
        f = k / 2
        d, sd, _ = in_plane(side, math.radians(70 + 8 * f))
        out.append(("secondary", mir(SHOULDER, side).lerp(wrist, 0.45 + 0.45 * f) - n * (0.006 + 0.003 * k), d, sd, 0.11 - 0.008 * f, 0.042))
    return out


def tail_feathers():
    out = []
    for k in range(TAIL_FEATHERS):
        f = k / (TAIL_FEATHERS - 1) * 2 - 1
        a = math.radians(22 * f)
        d = (TAIL_DIR * math.cos(a) + V(1, 0, 0) * math.sin(a)).normalized()
        sd = d.cross(V(0, 0, 1)).normalized()
        if sd.x < 0:
            sd = -sd
        out.append((TAIL_ROOT + V(0.004 * f, 0, 0.003 * (1 - abs(f))) - d * 0.03, d, sd, 0.19 - 0.025 * abs(f), 0.042))
    return out


def build_plates(coll, low=False):
    """All the feather plates: tagged per vertex with group (0 covert L, 1 primaries L, 2 secondaries L, 3..5 right, 6+k tail feather k), u and v."""
    m = Mesh()
    bm = m.bm
    lay_g = bm.verts.layers.int.new("group")
    lay_u = bm.verts.layers.float.new("pu")
    lay_v = bm.verts.layers.float.new("pv")
    nu, nv = (8, 3) if low else (110, 36)          # (at 6 x 2 the game feathers read chunky up close)
    items = []
    for side in (1, -1):
        base = 0 if side > 0 else 3
        for kind, root, along, sd, length, width in wing_feathers(side):
            g = base + {"covert": 0, "primary": 1, "secondary": 2}[kind]
            curl = 0.05 if kind != "covert" else 0.02
            items.append((g, feather_point(root, along, sd, length, width, curl=curl, cup=0.08 if kind == "covert" else 0.05)))
    for k, (root, along, sd, length, width) in enumerate(tail_feathers()):
        items.append((6 + k, feather_point(root, along, sd, length, width, curl=-0.04, cup=0.05)))
    for g, point in items:
        before = set(bm.verts)
        m.sheet(point, feather_thick, nu, nv)
        new = [v for v in bm.verts if v not in before]
        idx = 0
        for i in range(nu + 1):
            for j in range(nv + 1):
                for _ in range(2):
                    v = new[idx]
                    v[lay_g], v[lay_u], v[lay_v] = g, i / nu, j / nv
                    idx += 1
    return m.finish(N + "Plates" + ("Low" if low else "Hi"), coll)


# ---------- the key ----------
def key_frame():
    s, t = basis(KEY_DIR)
    disc_c = KEY_ROOT + KEY_DIR * (KEY_STEM + KEY_DISC_R * 0.92)
    return disc_c, s, t                                                # the disc lies in the plane of the stem and s


def build_key(coll, low=False):
    """A jade bi disc on a brass stem. Tagged: part (0 stem, 1 disc)."""
    m = Mesh()
    lay = m.bm.verts.layers.int.new("part")
    before = set(m.bm.verts)
    nt = 10 if low else 32
    revolve(m, KEY_ROOT - KEY_DIR * 0.03, KEY_DIR, [(0, 0), (0, 0.0075), (KEY_STEM * 0.7, 0.0068), (KEY_STEM * 0.82, 0.0105), (KEY_STEM * 0.9, 0.0105),
                                                   (KEY_STEM + 0.03, 0.0068), (KEY_STEM + 0.034, 0)], nt)
    for v in m.bm.verts:
        if v not in before:
            v[lay] = 0
    before = set(m.bm.verts)
    c, s, t = key_frame()
    # the disc: an annulus whose axis is t (it faces sideways to the stem), its section a rounded slab
    prof = []
    n_edge = 3 if low else 8
    for k in range(n_edge + 1):
        a = -math.pi / 2 + math.pi * k / n_edge
        prof.append((KEY_THICK / 2 * math.sin(a), KEY_DISC_R - KEY_THICK / 2 + KEY_THICK / 2 * math.cos(a)))
    for k in range(n_edge + 1):
        a = math.pi / 2 + math.pi * k / n_edge
        prof.append((KEY_THICK / 2 * math.sin(a), KEY_HOLE_R + KEY_THICK / 2 + KEY_THICK / 2 * math.cos(a)))
    ns = len(prof)
    nt2 = 16 if low else 64
    a2, b2 = basis(t)
    rings = [[m.bm.verts.new(c + t * h + (a2 * math.cos(TAU * k / nt2) + b2 * math.sin(TAU * k / nt2)) * r) for (h, r) in prof] for k in range(nt2)]
    for k in range(nt2):
        A, B = rings[k], rings[(k + 1) % nt2]
        for j in range(ns):
            m.bm.faces.new((A[j], B[j], B[(j + 1) % ns], A[(j + 1) % ns]))
    for v in m.bm.verts:
        if v not in before:
            v[lay] = 1
    return m.finish(N + "Key" + ("Low" if low else "Hi"), coll)


def build_legs(coll, low=False):
    """Thin brass legs, a pin at the ankle, three toes forward and one back, curled. Tagged: side."""
    m = Mesh()
    lay = m.bm.verts.layers.int.new("side")
    sides = 6 if low else 14
    for side in (1, -1):
        before = set(m.bm.verts)
        p = [mir(q, side) for q in LEG]
        m.tube([p[0].lerp(p[1], k / 4) for k in range(5)], lambda f: 0.0068 - 0.0012 * f, sides=sides)
        m.tube([p[1].lerp(p[2], k / 3) for k in range(4)], lambda f: 0.0056, sides=sides)
        m.ball(p[1], (0.0082,) * 3, sides, max(6, sides // 2))            # the ankle's pin joint
        for a in (-25, 0, 25, 180):
            d = Matrix.Rotation(math.radians(a), 3, "Z") @ V(0, -1, 0)
            pts = [p[2], p[2] + d * 0.014 + V(0, 0, -0.004), p[2] + d * 0.022 + V(0, 0, -0.012), p[2] + d * 0.02 + V(0, 0, -0.02)]
            m.tube(catmull(pts, 2 if low else 5), lambda f: 0.0034 * (1 - 0.6 * f), sides=max(5, sides // 2))
        for v in m.bm.verts:
            if v not in before:
                v[lay] = side
    return m.finish(N + "Legs" + ("Low" if low else "Hi"), coll)


# ---------- the glowing pieces ----------
def build_seam(coll, nt=96, ns=8):
    m = Mesh()
    torus(m, NECK + NECK_AXIS * (COLLAR_TUBE * 0.15), NECK_AXIS, COLLAR_R - COLLAR_TUBE * 0.95, 0.0032, nt, ns)
    return m.finish(N + "Seam_Glow_" + QI_HEX, coll)


def build_keylight(coll, nt=32):
    c, s, t = key_frame()
    m = Mesh()
    revolve(m, c - t * 0.003, t, [(0, 0), (0, KEY_HOLE_R * 1.05), (0.006, KEY_HOLE_R * 1.05), (0.006, 0)], nt)
    return m.finish(N + "Key_Glow_" + QI_HEX, coll)


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
    pieces = {"Body": body_shell(), "Head": head_shell(), "Collar": build_collar(HI), "Beak": build_beak(HI), "Bezels": build_bezels(HI),
              "Plates": build_plates(HI), "Key": build_key(HI), "Legs": build_legs(HI)}
    frames = {}
    for side, tag in ((1, "L"), (-1, "R")):
        fr = EyeFrame(mir(EYE_C, side), mir(EYE_AXIS, side), side, EYE_R, LID_UP, LID_LOW, tilt=LID_TILT)
        frames[tag] = fr
        pieces["Eye" + tag] = build_eye(fr, tag)
        pieces["LidU" + tag] = build_lid(fr, True, "LidU" + tag, BRASS, GOLD_DEEP)
        pieces["LidL" + tag] = build_lid(fr, False, "LidL" + tag, BRASS, GOLD_DEEP, lower_share=0.4)
    glows = {"Glints": glints(frames, HI, "Glints_Glow_" + GLINT_HEX, spots=((-24, 28, 0.0068, 12), (20, -18, 0.0032, 8))),
             "Seam": build_seam(HI), "KeyLight": build_keylight(HI)}
    if not clay:
        paint_all(pieces, frames)
    return pieces, frames, glows


# ---------- painting: cloisonne ----------
WIRE = 0.0016                       # the gilt wire's width (metres)
WIRE_UP = 0.0007                    # how far it stands above the enamel


def read_attr(o, key):
    a = o.data.attributes[key]
    out = np.zeros(len(o.data.vertices), dtype=float if a.data_type == "FLOAT" else int)
    a.data.foreach_get("value", out)
    return out


def scale_cells(s, c, row, col, seed=0):
    """Overlapping feather-shaped cells (each a circle, the one nearer the head on top), on a sheet with s along it and c across: per point, how far
    inside its cell's edge it lies (metres), and its cell's centre (s, c) and own random number."""
    r0 = np.floor(s / row).astype(np.int64)
    best_row = np.full(len(s), 1 << 40, dtype=np.int64)
    d_in = np.full(len(s), -1.0)
    cs = np.zeros(len(s))
    cc = np.zeros(len(s))
    own = np.zeros(len(s))
    R = 0.62 * max(row, col)
    for dr in (-1, 0, 1, 2):
        r = r0 + dr
        shift = (r % 2) * 0.5
        c0 = np.floor(c / col - shift).astype(np.int64)
        for dc in (-1, 0, 1):
            k = c0 + dc
            ys = (r + 0.5) * row
            xs = (k + 0.5 + shift) * col
            dist = np.hypot((s - ys) * 1.0, c - xs)
            inside = dist < R
            take = inside & (r < best_row)
            best_row = np.where(take, r, best_row)
            d_in = np.where(take, R - dist, d_in)
            cs = np.where(take, ys, cs)
            cc = np.where(take, xs, cc)
            own = np.where(take, hash01(r, k, 0, seed), own)
    return np.maximum(d_in, 0.0), cs, cc, own


def enamel(o, col_fn, P, Nn, s, c, row, col, seed, rough_enamel=0.12):
    """Fills each cell with one enamel colour (chosen at the cell's centre), the gilt wire raised round it."""
    d, cs, cc, own = scale_cells(s, c, row, col, seed)
    wire = 1 - smooth(WIRE * 0.5, WIRE, d)
    base = col_fn(cs, cc, own)
    base = base * (0.94 + 0.08 * own)[:, None] * (0.9 + 0.1 * smooth(0.0, 0.005, d))[:, None]      # each cell its own firing; the enamel thinner at the wire
    gold = mix(np.broadcast_to(GOLD, (len(P), 3)), GOLD_DEEP, 0.25 * fbm(P, 300.0, 2, seed + 5))
    colour = mix(base, gold, wire)
    relief = wire * WIRE_UP + (1 - wire) * 0.00035 * smooth(0.0, 0.006, d)
    set_verts(o, P + Nn * relief[:, None])
    paint(o, np.clip(colour, 0, 1), rough_enamel + (0.3 - rough_enamel) * wire, wire)
    return wire


def paint_body(o):
    P, Nn = verts(o), normals(o)
    Q = body_local(P)
    theta = np.arctan2(Q[:, 0], Q[:, 2])
    s = Q[:, 1]

    def colours(cs, cc, own):
        th = cc / 0.1
        n = len(cs)
        back = np.abs(th) < 1.55
        col = np.where(back[:, None], np.broadcast_to(TURQ, (n, 3)), np.broadcast_to(BUFF, (n, 3)))
        col = np.where((~back & (cs < -0.03))[:, None], mix(np.broadcast_to(BUFF, (n, 3)), CORAL, 0.35), col)       # a coral blush on its breast
        col = np.where((~back & (cs > 0.04))[:, None], np.broadcast_to(IVORY, (n, 3)), col)                         # an ivory belly
        col = np.where((back & (cs > 0.085))[:, None], np.broadcast_to(IVORY, (n, 3)), col)                         # and rump
        col = np.where((back & (np.abs(th) < 0.5) & (cs < 0.085))[:, None], np.broadcast_to(TURQ_DEEP, (n, 3)), col)   # a deeper line down its spine
        return col
    enamel(o, colours, P, Nn, s, theta * 0.1, 0.026, 0.024, 11)


def paint_head(o):
    P, Nn = verts(o), normals(o)
    q = P - np.array(tuple(HEAD_C))
    fwd = np.array((0.0, -0.99, -0.12))
    fwd = fwd / np.linalg.norm(fwd)
    dirs = q / np.linalg.norm(q, axis=1)[:, None]
    ang = np.arccos(np.clip(dirs @ fwd, -1, 1))                                     # from the beak: 0 at it
    az = np.arctan2(dirs[:, 0], dirs[:, 2])                                         # round it: 0 on top

    def colours(cs, cc, own):
        a, z = cs / HEAD_R, cc / HEAD_R
        n = len(cs)
        col = np.broadcast_to(IVORY, (n, 3)).copy()                                    # its cheeks and throat
        cap = (np.abs(z) < 1.05) & (a > 0.62)
        col[cap] = LAPIS
        nape = (a > 1.85)
        col[nape] = LAPIS_DEEP
        col[a < 0.62] = CORAL                                                         # its mask round the beak
        col[(a < 0.38)] = CORAL_DEEP
        return col
    enamel(o, colours, P, Nn, ang * HEAD_R, az * np.sin(np.clip(ang, 0.25, None)) * HEAD_R, 0.016, 0.016, 23)


def paint_plates(o):
    """Each feather plate: lapis-black enamel in cells, a gold shaft and border, a bar of gold leaf across the wing's feathers, ivory spots at the tips."""
    P, Nn = verts(o), normals(o)
    g = read_attr(o, "group")
    u, v = read_attr(o, "pu"), read_attr(o, "pv")
    n = len(P)
    sv = v * 2 - 1
    kind = np.where(g >= 6, 3, g % 3)                                                 # 0 covert, 1 primary, 2 secondary, 3 tail
    length = np.select([kind == 0, kind == 1, kind == 2], [0.15, 0.15, 0.11], 0.18)
    width = np.select([kind == 0], [0.062], 0.043)
    along, across = u * length, sv * width * 0.5
    shaft = 1 - smooth(WIRE * 0.45, WIRE * 0.9, np.abs(across) + 0.0)
    shaft *= smooth(0.0, 0.05, u) * (1 - smooth(0.88, 0.97, u))
    edge = np.minimum(np.minimum((1 - np.abs(sv)) * width * 0.5, (1 - u) * length), u * length)
    border = 1 - smooth(WIRE * 0.6, WIRE * 1.2, edge)
    barbs = np.abs(((along + np.abs(across) * 0.9) / 0.022) % 1 - 0.5) * 0.022          # cells slanting out from the shaft, as barbs do
    barb = (1 - smooth(WIRE * 0.45, WIRE * 0.9, barbs)) * (np.abs(across) > 0.002)
    wire = np.clip(np.maximum.reduce([shaft, border, barb]), 0, 1)
    base = mix(np.broadcast_to(LAPIS_DEEP, (n, 3)), LAPIS, 0.35 * smooth(0.6, 0.0, u))
    base = np.where((kind == 0)[:, None], mix(np.broadcast_to(LAPIS, (n, 3)), TURQ_DEEP, 0.3 * smooth(0.0, 1.0, u)), base)
    cell = np.floor((along + np.abs(across) * 0.9) / 0.022)
    base = base * (0.92 + 0.1 * hash01(cell.astype(np.int64), (across > 0).astype(np.int64), g, 7))[:, None]
    spot = (1 - smooth(0.6, 0.85, np.hypot((u - 0.86) / 0.11, sv * 0.9))) * ((kind == 1) | (kind == 2) | (kind == 3))
    base = mix(base, IVORY, spot)
    bar = smooth(0.12, 0.14, u) * (1 - smooth(0.32, 0.34, u)) * ((kind == 1) | (kind == 0))     # the goldfinch's bar: real gold leaf
    bar = np.where(kind == 0, smooth(0.42, 0.44, u) * (1 - smooth(0.66, 0.68, u)), bar)
    metal = np.clip(np.maximum(wire, bar), 0, 1)
    gold = mix(np.broadcast_to(GOLD, (n, 3)), GOLD_DEEP, 0.2 * fbm(P, 320.0, 2, 31))
    col = mix(base, gold, metal)
    relief = wire * WIRE_UP + bar * 0.0003
    set_verts(o, P + Nn * relief[:, None])
    paint(o, np.clip(col, 0, 1), 0.12 + 0.16 * metal, metal)


def paint_metal(o, colour, rough=0.3, wear=0.25):
    P = verts(o)
    n = len(P)
    col = mix(np.broadcast_to(colour, (n, 3)), GOLD_DEEP, wear * fbm(P, 180.0, 3, 41))
    paint(o, np.clip(col, 0, 1), rough + 0.1 * fbm(P, 90.0, 2, 43), np.ones(n))


def paint_beak(o):
    P = verts(o)
    lower = read_attr(o, "lower")
    n = len(P)
    f = np.clip(((P - np.array(tuple(BEAK_ROOT))) @ np.array(tuple(BEAK_DIR))) / BEAK_LEN, 0, 1)
    col = mix(np.broadcast_to(GOLD, (n, 3)), GOLD_DEEP, 0.35 * lower + 0.2 * smooth(0.6, 1.0, f))
    ring = np.exp(-((f - 0.22) / 0.03) ** 2)                                               # an engraved ring near its root
    col = mix(col, GOLD_DEEP * 0.7, ring * 0.7)
    paint(o, np.clip(col, 0, 1), 0.22 + 0.15 * ring, np.ones(n))


def paint_key(o):
    """Brass stem; an old jade bi disc, clouded and veined, carved with the grain pattern's little raised bosses."""
    P, Nn = verts(o), normals(o)
    part = read_attr(o, "part")
    n = len(P)
    c, sx, tx = key_frame()
    a2, b2 = basis(tx)
    q = P - np.array(tuple(c))
    x, y = q @ np.array(tuple(a2)), q @ np.array(tuple(b2))
    r = np.hypot(x, y)
    face = np.abs(Nn @ np.array(tuple(tx))) > 0.7
    grain = 0.0045
    gx, gy = x / grain, (y / grain - 0.5 * (np.floor(x / grain) % 2))
    boss = 1 - smooth(0.18, 0.34, np.hypot(gx - np.round(gx), gy - np.round(gy)))
    boss = boss * face * (r > KEY_HOLE_R + 0.005) * (r < KEY_DISC_R - 0.005) * (part == 1)
    cloud = fbm(P, 70.0, 4, 51)
    jade = mix(np.broadcast_to(JADE, (n, 3)), JADE_DEEP, smooth(0.45, 0.75, cloud) * 0.6)
    jade = mix(jade, JADE_LIGHT, smooth(0.62, 0.85, fbm(P * np.array([1, 3, 1]), 110.0, 3, 53)) * 0.45)
    jade = mix(jade, rgb(150, 120, 70), smooth(0.7, 0.9, fbm(P, 40.0, 2, 57)) * 0.35)           # old: a brown flush of age at its edge
    brass = mix(np.broadcast_to(BRASS, (n, 3)), GOLD_DEEP, 0.3 * fbm(P, 200.0, 2, 59))
    col = np.where((part == 1)[:, None], jade * (0.95 + 0.1 * boss)[:, None], brass)
    set_verts(o, P + Nn * (boss * 0.0009)[:, None])
    paint(o, np.clip(col, 0, 1), np.where(part == 1, 0.2, 0.3), (part == 0).astype(float))


def eye_paint(o, fr):
    """Polished onyx: near black, a cool sheen toward its rim."""
    px, py, a = eye_coords(o, fr)
    r = np.where(a > 0, np.hypot(px, py), 2.0)
    col = mix(np.broadcast_to(ONYX, (len(px), 3)), rgb(40, 44, 60), smooth(0.4, 1.0, r) * 0.6)
    paint(o, col, np.full(len(px), 0.04), np.zeros(len(px)))


def paint_all(pieces, frames):
    paint_body(pieces["Body"])
    paint_head(pieces["Head"])
    paint_plates(pieces["Plates"])
    paint_metal(pieces["Collar"], BRASS)
    paint_metal(pieces["Bezels"], GOLD, 0.22, 0.15)
    paint_metal(pieces["Legs"], BRASS, 0.32)
    paint_beak(pieces["Beak"])
    paint_key(pieces["Key"])
    for tag, fr in frames.items():
        eye_paint(pieces["Eye" + tag], fr)
        for k in ("LidU", "LidL"):
            o = pieces[k + tag]
            a = o.data.attributes["paint"]
            cols = np.empty(len(o.data.vertices) * 4)
            a.data.foreach_get("color", cols)
            n = len(o.data.vertices)
            paint(o, cols.reshape(-1, 4)[:, :3], np.full(n, 0.28), np.ones(n))      # brass shutters


VIEWS = [(0, -1, 0.2), (0.62, -0.72, 0.3), (1, 0, 0.12), (0, 1, 0.3), (-0.6, 0.6, 0.45), (-0.62, -0.72, 0.25), (0, -0.05, 1), (0.4, -0.5, -0.6)]
VIEW_AT = (0, 0.0, 0.47)
FACE_AT = (0, -0.15, 0.54)
EXTRA = [(0.1, -1, 0.12, 0.7, FACE_AT), (0.8, -0.6, 0.25, 0.7, FACE_AT), (0.5, 0.5, 0.9, 0.7, tuple(KEY_ROOT + KEY_DIR * 0.1)),
         (1, 0.3, 0.3, 0.9, (0.2, 0.05, 0.5)), (0.4, -0.85, 0.2, 0.25, tuple(EYE_C)), (0.6, 0.8, -0.2, 0.9, (0, 0.2, 0.36))]

if __name__ == "__main__" and STAGE in ("clay", "paint"):
    pieces, frames, glows = build_hi(clay=STAGE == "clay")
    print("HI", {k: len(o.data.polygons) for k, o in pieces.items()}, flush=True)
    stage_setup((0.3, 0.32, 0.36, 1))
    show_glows(glows)
    if STAGE == "clay":
        mat = bpy.data.materials.new("clay")
        g = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.62, 0.6, 0.57, 1)
        g.inputs["Roughness"].default_value = 0.6
        dark = bpy.data.materials.new("clay_eye")
        g = next(n for n in dark.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        g.inputs["Base Color"].default_value = (0.03, 0.03, 0.04, 1)
        g.inputs["Roughness"].default_value = 0.1
    else:
        mat = hi_material(ao_distance=0.02, ao_share=0.3)
    for key, o in pieces.items():
        o.data.materials.clear()
        o.data.materials.append(dark if STAGE == "clay" and key.startswith("Eye") else mat)
    only = [int(k) for k in ARGS[ARGS.index("views") + 1].split(",")] if "views" in ARGS else None
    allv = VIEWS + EXTRA
    shots(os.path.join(REVIEW, STAGE), [allv[k] for k in only] if only else allv, target=VIEW_AT, dist=2.0, size=560)
    print("DONE", flush=True)


# ---------- the game mesh: each piece built again at a low count (nothing is re-meshed: every piece is a rigid plate) ----------
UV_ANGLE = 66
UV_SHAPE = "CONVEX"                 # (the concave packer overlapped islands on some runs: 0, then 84 texels with nothing changed)
UV_MARGIN = 0.004                   # (8 px between islands on the 2048 map: 44% of it used; projected feathers once broke into slivers and 0.016 collapsed the pack)
SCALES = {"Skin": 1.0, "Head": 1.5, "EyeL": 1.6, "EyeR": 1.6, "LidUL": 0.8, "LidUR": 0.8, "LidLL": 0.8, "LidLR": 0.8, "Plates": 1.1, "Key": 1.2,
          "Collar": 0.7, "Beak": 1.0, "Bezels": 0.6, "Legs": 0.6}


def build_low(frames):
    lows = {"Skin": body_shell(44, 30, GAME, "BodyLow"), "Head": head_shell(36, 26, GAME, "HeadLow"), "Collar": build_collar(GAME, low=True),
            "Beak": build_beak(GAME, low=True), "Bezels": build_bezels(GAME, low=True), "Plates": build_plates(GAME, low=True),
            "Key": build_key(GAME, low=True), "Legs": build_legs(GAME, low=True)}
    for side, tag in ((1, "L"), (-1, "R")):
        lows["Eye" + tag] = low_eye(frames[tag], N + "Eye" + tag + "Low", 20, 14)
        lows["LidU" + tag] = low_lid(frames[tag], True, N + "LidU" + tag + "Low")
        lows["LidL" + tag] = low_lid(frames[tag], False, N + "LidL" + tag + "Low")
    for o in lows.values():
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    triangulate(lows)
    md = lows["Plates"].modifiers.new("Rims", "EDGE_SPLIT")         # a thin plate's rims kept apart from its faces in the shading
    md.split_angle = math.radians(50)
    md.use_edge_sharp = False
    apply_mods(lows["Plates"], [])
    return lows


def flatten_normals(objs, pad=4):
    """These pieces' share of the normal map made flat: feather plates stacked millimetres apart, and a beak's two halves meeting face to face, bake
    each other's backs (black). Their wires and detail are in the colour and metal maps."""
    img = bpy.data.images[PET + "_Normal"]
    if img.packed_file:
        img.unpack(method="REMOVE")
        img.reload()
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    mask = np.zeros((h, w), dtype=bool)
    for o in objs:
        uv = o.data.uv_layers.active.data
        for p in o.data.polygons:
            loops = list(p.loop_indices)
            a, b, c = [np.array(uv[i].uv) * (w, h) for i in loops[:3]]
            lo = np.clip(np.floor(np.minimum(np.minimum(a, b), c)).astype(int) - pad, 0, (w - 1, h - 1))
            hi = np.clip(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int) + pad, 0, (w - 1, h - 1))
            d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(d) < 1e-12:
                continue
            ys, xs = np.mgrid[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
            qx, qy = xs + 0.5, ys + 0.5
            w0 = ((b[1] - c[1]) * (qx - c[0]) + (c[0] - b[0]) * (qy - c[1])) / d
            w1 = ((c[1] - a[1]) * (qx - c[0]) + (a[0] - c[0]) * (qy - c[1])) / d
            inside = (w0 >= 0) & (w1 >= 0) & (w0 + w1 <= 1)
            for p0, p1 in ((a, b), (b, c), (c, a)):
                e = p1 - p0
                t = np.clip(((qx - p0[0]) * e[0] + (qy - p0[1]) * e[1]) / max(e @ e, 1e-12), 0, 1)
                inside |= np.hypot(qx - p0[0] - e[0] * t, qy - p0[1] - e[1] * t) <= pad
            mask[ys[inside], xs[inside]] = True
    px[mask] = (0.5, 0.5, 1.0, 1.0)
    px[px[..., 2] < 0.55] = (0.5, 0.5, 1.0, 1.0)          # and the gutters, which the bake filled from those pieces' edges before (at a distance they bleed in)
    img.pixels.foreach_set(px.ravel())
    img.update()
    img.save()
    img.pack()
    return int(mask.sum())


def plates_uv(o, density):
    """Each feather plate laid out from its own grid, in true scale at this density: its top and its underside each a clean rectangle (u along it, v
    across), its thin rims folded onto the top's edge. (Projected, the plates broke into hundreds of slivers whose margins ate the atlas.)"""
    me = o.data
    uvd = me.uv_layers.active.data
    g = read_attr(o, "group")
    pu, pv = read_attr(o, "pu"), read_attr(o, "pv")
    dims = {}
    for k, (kind, root, along, sd, length, width) in enumerate(wing_feathers(1)):
        dims[{"covert": 0, "primary": 1, "secondary": 2}[kind]] = (max(dims.get({"covert": 0, "primary": 1, "secondary": 2}[kind], (0, 0))[0], length), width)
    tail_len = max(t[3] for t in tail_feathers())
    # each feather plate's normal, from its own points (top: the side its grid's normal faces)
    centre_n = {}
    for poly in me.polygons:
        gg = int(g[poly.vertices[0]])
        centre_n.setdefault(gg, Vector((0, 0, 0)))
    # place: one shelf per group, each feather instance found by its group and position along
    x = y = 0.0
    shelf_h = 0.0
    cells = {}
    for gg in sorted(set(int(v) for v in g)):
        kind = 3 if gg >= 6 else gg % 3
        length = tail_len if kind == 3 else dims[kind][0]
        width = 0.042 if kind == 3 else dims[kind][1]
        cells[gg] = (length, width)
    # a feather group holds several plates (the primaries, the secondaries): tell them apart by connected pieces
    import bmesh as _bm
    bm = _bm.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    island = [-1] * len(bm.faces)
    count = 0
    for f in bm.faces:
        if island[f.index] >= 0:
            continue
        stack = [f]
        island[f.index] = count
        while stack:
            h = stack.pop()
            for e in h.edges:
                for h2 in e.link_faces:
                    if island[h2.index] < 0:
                        island[h2.index] = count
                        stack.append(h2)
        count += 1
    # each plate's own normal: the mean of its faces' (top and bottom cancel: use the faces whose pv-gradient agrees) -> take the first face's
    plate_normal = {}
    for f in bm.faces:
        k = island[f.index]
        if k not in plate_normal and abs(f.normal.length) > 0:
            vs = f.verts
            a, b_, c = vs[0], vs[1], vs[2]
            du = Vector((pu[b_.index] - pu[a.index], pu[c.index] - pu[a.index]))
            plate_normal[k] = None
    bm.free()
    origin = {}
    pad = 0.006
    row_w = 0.0
    for poly in me.polygons:
        k = island[poly.index]
        if k in origin:
            continue
        gg = int(g[poly.vertices[0]])
        length, width = cells[gg]
        w, h = length * density, (2 * width + pad) * density
        if x + w > 1.0 and x > 0:
            x, y = 0.0, y + shelf_h + pad * density
            shelf_h = 0.0
        origin[k] = (x, y, gg)
        x += w + pad * density
        shelf_h = max(shelf_h, h)
    # which side of its plate each face is: compare its normal with its grid's (u x v) direction, found per face from its own corners
    co = np.array([tuple(v.co) for v in me.vertices])
    for poly in me.polygons:
        k = island[poly.index]
        ox, oy, gg = origin[k]
        length, width = cells[gg]
        vs = list(poly.vertices)
        U = np.array([pu[v] for v in vs])
        Vv = np.array([pv[v] for v in vs])
        # the grid's own normal here: solve for d/du and d/dv over this triangle
        P = co[vs]
        M = np.array([[U[1] - U[0], Vv[1] - Vv[0]], [U[2] - U[0], Vv[2] - Vv[0]]])
        rim = abs(np.linalg.det(M)) < 1e-9
        top = True
        if not rim:
            G = np.linalg.solve(M, np.array([P[1] - P[0], P[2] - P[0]]))
            gn = np.cross(G[0], G[1])
            top = float(np.dot(gn, np.array(tuple(poly.normal)))) >= 0
        for l, v in zip(poly.loop_indices, vs):
            fu, fv = pu[v], pv[v]                         # (a rim set in from the edge became an island of its own: the packer laid those slivers over others on some runs)
            uu = ox + fu * length * density
            vv = oy + (fv * width if top else (2 * width + pad * 0.5 - fv * width)) * density
            uvd[l].uv = (uu, vv)


def gild_rims(o, radius=2.5):
    """Every feather plate's rim painted gold (and metal) in the maps, along its UV line: a rim is the plate's edge, its gold border wire; laid on the
    very edge of its island it sampled whatever the neighbouring island had spread there (the jade of the key, at the feathers' tips)."""
    me = o.data
    uvd = me.uv_layers.active.data
    pu, pv = read_attr(o, "pu"), read_attr(o, "pv")
    segs = []
    for poly in me.polygons:
        vs = list(poly.vertices)
        U = np.array([pu[v] for v in vs])
        Vv = np.array([pv[v] for v in vs])
        M = np.array([[U[1] - U[0], Vv[1] - Vv[0]], [U[2] - U[0], Vv[2] - Vv[0]]])
        if abs(np.linalg.det(M)) < 1e-9:
            pts = [np.array(uvd[l].uv) for l in poly.loop_indices]
            for a in range(len(pts)):
                segs.append((pts[a], pts[(a + 1) % len(pts)]))
    gold = (GOLD[0], GOLD[1], GOLD[2])
    for name, value in ((PET + "_Color", gold), (PET + "_Metalness", (1.0, 1.0, 1.0)), (PET + "_Roughness", (0.3, 0.3, 0.3))):
        img = bpy.data.images[name]
        if img.packed_file:
            img.unpack(method="REMOVE")
            img.reload()
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        px = px.reshape(h, w, 4)
        r = radius * w / 2048
        for a, b in segs:
            A, B = a * (w, h), b * (w, h)
            lo = np.clip(np.floor(np.minimum(A, B) - r - 1).astype(int), 0, (w - 1, h - 1))
            hi = np.clip(np.ceil(np.maximum(A, B) + r + 1).astype(int), 0, (w - 1, h - 1))
            ys, xs = np.mgrid[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
            q = np.stack([xs + 0.5, ys + 0.5], -1)
            e = B - A
            t = np.clip(((q - A) @ e) / max(e @ e, 1e-12), 0, 1)
            d = np.linalg.norm(q - (A + t[..., None] * e), axis=-1)
            near = d <= r
            px[ys[near], xs[near], :3] = value
        img.pixels.foreach_set(px.ravel())
        img.update()
        img.save()
        img.pack()
    return len(segs)


# ---------- the skeleton: one bone per moving part ----------
WING_TAGS = ("L", "R")


def skeleton(frames):
    bones = [("Root", V(0, 0, 0), None), ("Body", BODY_C.copy(), "Root"), ("Head", NECK.copy(), "Body"), ("Jaw", BEAK_ROOT.copy(), "Head"),
             ("Key", KEY_ROOT.copy(), "Body")]
    for side, tag in ((1, "L"), (-1, "R")):
        fr = frames[tag]
        bones += [("Eye" + tag, fr.centre.copy(), "Head"), ("LidU" + tag, fr.centre.copy(), "Head"), ("LidL" + tag, fr.centre.copy(), "Head")]
        bones += [("Wing" + tag, mir(SHOULDER, side), "Body"), ("WingTip" + tag, mir(WRIST, side), "Wing" + tag), ("Leg" + tag, mir(LEG[0], side), "Body")]
    for k in range(TAIL_FEATHERS):
        bones.append(("Tail%d" % (k + 1), TAIL_ROOT.copy(), "Body"))
    return armature(bones)


def plate_bone(g):
    if g >= 6:
        return "Tail%d" % (g - 5)
    tag = "L" if g < 3 else "R"
    return ("WingTip" if g % 3 == 1 else "Wing") + tag


def bind_all(lows, rig, glows):
    rigid(lows["Skin"], "Body")
    rigid(lows["Collar"], "Body")
    rigid(lows["Head"], "Head")
    rigid(lows["Bezels"], "Head")
    weigh(lows["Beak"], [{"Jaw" if k else "Head": 1.0} for k in read_attr(lows["Beak"], "lower")])
    weigh(lows["Plates"], [{plate_bone(int(g)): 1.0} for g in read_attr(lows["Plates"], "group")])
    rigid(lows["Key"], "Key")
    weigh(lows["Legs"], [{"LegL" if k > 0 else "LegR": 1.0} for k in read_attr(lows["Legs"], "side")])
    for tag in "LR":
        rigid(lows["Eye" + tag], "Eye" + tag)
        rigid(lows["LidU" + tag], "LidU" + tag)
        rigid(lows["LidL" + tag], "LidL" + tag)
    rigid(glows["Seam"], "Body")
    rigid(glows["KeyLight"], "Key")
    weigh(glows["Glints"], [{"EyeL" if q[0] > 0 else "EyeR": 1.0} for q in verts(glows["Glints"])])
    tag_pieces(lows)
    body = join_into(lows, "Body")
    pet_kit.bind(rig, [body] + list(glows.values()))
    return body


PIECES = ("Skin", "Head", "Collar", "Beak", "Bezels", "Plates", "Key", "Legs", "EyeL", "EyeR", "LidUL", "LidUR", "LidLL", "LidLR")


def tag_pieces(lows):
    for key, o in lows.items():
        a = o.data.attributes.new("piece", "INT", "FACE")
        a.data.foreach_set("value", [PIECES.index(key)] * len(o.data.polygons))


def part_flush(body, gap=0.0015, rounds=6):
    """Where an eye or a lid slides in under the head's shell, the shell can run within a millimetre of it and parallel: it would shimmer. Each such
    shell face is moved off the eye or lid to a clean gap. Returns how many vertices moved."""
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
        for f in bm.faces:
            cen = f.calc_center_median()
            for p in [cen] + [cen.lerp(v.co, 0.6) for v in f.verts]:
                for _, _, j, _ in tree.find_nearest_range(p, gap):
                    if j is None or j == f.index or part[j] == part[f.index] or set(f.verts) & set(bm.faces[j].verts):
                        continue
                    g = bm.faces[j]
                    q = p - g.normal * g.normal.dot(p - g.verts[0].co)
                    if not intersect_point_tri(q, *[v.co for v in g.verts[:3]]):
                        continue
                    shell, eye = (g, f) if part[f.index] else (f, g)
                    if abs(shell.normal.dot(eye.normal)) < 0.99:
                        continue
                    n = eye.normal
                    sdist = (shell.calc_center_median() - eye.calc_center_median()).dot(n)
                    if abs(sdist) >= gap:
                        continue
                    target = gap if sdist >= 0 else -gap
                    for v in shell.verts:
                        step = n * (target - sdist)
                        if v.index not in push or step.length > push[v.index].length:
                            push[v.index] = step
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


# ---------- poses, in the game's axes (turns x, y, z: +x lifts what points forward; +y turns to its left), as PetRig's tables ----------
RX, RY, RZ = (-1, 0, 0), (0, 0, 1), (0, 1, 0)


def game_turn(rx, ry, rz, move=(0, 0, 0)):
    r = Matrix.Rotation(rx, 3, Vector(RX)) @ Matrix.Rotation(ry, 3, Vector(RY)) @ Matrix.Rotation(rz, 3, Vector(RZ))
    axis, angle = r.to_quaternion().to_axis_angle()
    return (tuple(axis), math.degrees(angle), (-move[0], move[2], move[1]))


def spec(table):
    return {bone: game_turn(*v[:3], v[3] if len(v) > 3 else (0, 0, 0)) for bone, v in table.items()}


def sym(table):
    out = dict(table)
    for name, v in table.items():
        m = re.match(r"^(Wing|WingTip|Eye|Leg)L$", name)
        if m and m.group(1) + "R" not in table:
            out[m.group(1) + "R"] = (v[0], -v[1], -v[2]) + tuple(v[3:])
    return out


def posed(o):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    tris = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return co.reshape(-1, 3), tris


def dominant(o):
    names = {g.index: g.name for g in o.vertex_groups}
    return [names[max(v.groups, key=lambda g: g.weight).group] if v.groups else "" for v in o.data.vertices]


def pairs(co_a, tris_a, fa, co_b, tris_b, fb):
    if not fa or not fb:
        return 0
    ta = BVHTree.FromPolygons([tuple(c) for c in co_a], [tris_a[f] for f in fa])
    tb = BVHTree.FromPolygons([tuple(c) for c in co_b], [tris_b[f] for f in fb])
    return len(ta.overlap(tb))


def probe(rig, body, bones=("Head", "Jaw", "Key", "WingL", "WingTipL", "Tail1", "Tail3", "LegL")):
    groups = {g.name: g.index for g in body.vertex_groups}
    for bone in bones:
        gi = groups[bone]
        idx = [v.index for v in body.data.vertices if any(g.group == gi and g.weight > 0.6 for g in v.groups)]
        pose(rig, {})
        c0 = posed(body)[0][idx].mean(0)
        row = []
        for k, axis in enumerate("xyz"):
            turn = [0.0, 0.0, 0.0]
            turn[k] = 0.4
            pose(rig, spec({bone: tuple(turn)}))
            d = (posed(body)[0][idx].mean(0) - c0) * 1000
            row.append("%s+ (%d,%d,%d)" % (axis, round(d[0]), round(d[1]), round(d[2])))
        print("PROBE", bone, len(idx), "verts", " ".join(row), flush=True)
    pose(rig, {})


class Checker:
    """What must never pass through what, in any pose: wing plates through body, head, key or the other wing; tail through wings; the head through the
    body or the key; the lower beak through the body."""

    def __init__(self, body):
        self.body = body
        d = dominant(body)
        fp = np.zeros(len(body.data.polygons), dtype=int)
        body.data.attributes["piece"].data.foreach_get("value", fp)
        _, tris = posed(body)

        def faces(test):
            return [i for i in range(len(tris)) if test(PIECES[fp[i]], d[tris[i][0]])]
        self.body_shell = faces(lambda p, b: p == "Skin")
        self.head = faces(lambda p, b: b == "Head" and p in ("Head", "Bezels", "Beak"))
        co0, _ = posed(body)
        n0, c0 = np.array(tuple(NECK_AXIS)), np.array(tuple(NECK))
        # the head above its collar: what shows (its lower part sits inside the collar and the body, by design)
        self.head_shown = [f for f in self.head if (co0[list(tris[f])].mean(0) - c0) @ n0 > COLLAR_TUBE * 1.2]
        self.jaw = faces(lambda p, b: b == "Jaw")
        self.key = faces(lambda p, b: p == "Key")
        self.wing = {t: faces(lambda p, b, t=t: p == "Plates" and b in ("Wing" + t, "WingTip" + t)) for t in "LR"}
        self.tail = faces(lambda p, b: p == "Plates" and b.startswith("Tail"))
        # a wing's plates away from where they root in the shoulder
        co, _ = posed(body)
        self.wing_free = {}
        for t, side in (("L", 1), ("R", -1)):
            sh = np.array(tuple(mir(SHOULDER, side)))
            self.wing_free[t] = [f for f in self.wing[t] if min(np.linalg.norm(co[v] - sh) for v in tris[f]) > 0.045]
        tr = np.array(tuple(TAIL_ROOT))
        self.tail_free = [f for f in self.tail if min(np.linalg.norm(co[v] - tr) for v in tris[f]) > 0.04]

    def run(self):
        co, tris = posed(self.body)
        w = self.wing_free["L"] + self.wing_free["R"]
        return {"wings x body": pairs(co, tris, w, co, tris, self.body_shell), "wings x head": pairs(co, tris, w, co, tris, self.head),
                "wings x key": pairs(co, tris, w, co, tris, self.key), "wing x wing": pairs(co, tris, self.wing_free["L"], co, tris, self.wing_free["R"]),
                "tail x wings": pairs(co, tris, self.tail_free, co, tris, w), "head x body": pairs(co, tris, self.head_shown, co, tris, self.body_shell),
                "head x key": pairs(co, tris, self.head, co, tris, self.key), "jaw x body": pairs(co, tris, self.jaw, co, tris, self.body_shell),
                "low z": round(float(co[:, 2].min()), 4)}


if __name__ == "__main__" and STAGE in ("rig", "all"):
    pieces, frames, glows = build_hi(clay=STAGE == "rig")
    mat = hi_material(ao_distance=0.02, ao_share=0.3)
    for o in pieces.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
    stage_setup((0.3, 0.32, 0.36, 1))
    lows = build_low(frames)
    if STAGE == "all":
        margin = float(ARGS[ARGS.index("margin") + 1]) if "margin" in ARGS else UV_MARGIN
        unwrap(lows, [(None, 1.0)], SCALES, margin=margin, angle=float(ARGS[ARGS.index("angle") + 1]) if "angle" in ARGS else UV_ANGLE, own_uv={"Plates": plates_uv}, shape=ARGS[ARGS.index("shape") + 1] if "shape" in ARGS else UV_SHAPE)
        used = sum(abs((p.loop_indices and 0) or 0) for p in [])
        objs = list(lows.values())
        area = 0.0
        for o in objs:
            uvd = o.data.uv_layers.active.data
            for p in o.data.polygons:
                L = list(p.loop_indices)
                a, b, c = [uvd[i].uv for i in L[:3]]
                area += abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) / 2
        per = {k: uv_overlap_texels(o.data, 1024) for k, o in lows.items()}
        clash = sum(per.values())
        if clash:
            print("UV OVERLAP BY PIECE", {k: v for k, v in per.items() if v}, flush=True)
        print("UV USED", round(area, 3), "OVERLAP within pieces", clash, "margin", margin, flush=True)
        assert area > 0.35, "the UV pack collapsed"
        assert clash == 0, "UV islands overlap: paint would land on two places"
        if "uvonly" in ARGS:
            raise SystemExit(0)
        pieces_for_bake = dict(pieces, Skin=pieces["Body"])
        bake_all(lows, pieces_for_bake, mat, size=1024, colour_size=2048, metal=True, fill=(0.42, 0.22, 0.05, 1), far=("Skin", "Head"),
                 reach=(0.002, 0.006), far_reach=(0.004, 0.012), reaches={"Plates": (0.004, 0.012), "Key": (0.002, 0.005), "Legs": (0.002, 0.005),
                                   **{k + t: (0.004, 0.01) for k in ("LidU", "LidL", "Eye") for t in "LR"}, "Bezels": (0.004, 0.01)}, margin_share=UV_MARGIN * 0.45)
        # (the fill: gold, the colour of every plate's border, where a ray grazing a plate's edge misses: teal, it showed as a fringe)
        # (a lid's high shell is 4.5 mm thick round the game lid's single layer: from 2 mm out, the rays started inside it and baked its inner face, black)
        print("RIMS GILDED", gild_rims(lows["Plates"]), "rim edges", flush=True)
        print("NORMALS FLATTENED (plates, beak, legs)", flatten_normals([lows["Plates"], lows["Beak"], lows["Legs"]]), "texels", flush=True)
        nimg = bpy.data.images[PET + "_Normal"]
        npx = np.array(nimg.pixels[:]).reshape(nimg.size[1], nimg.size[0], 4)
        print("NORMAL texels facing in (blue under 0.55)", int((npx[..., 2] < 0.55).sum()), flush=True)
    else:
        clay = bpy.data.materials.new("clay")
        for o in lows.values():
            o.data.materials.clear()
            o.data.materials.append(clay)
    tris = {k: sum(len(p.vertices) - 2 for p in o.data.polygons) for k, o in lows.items()}
    print("TRIS", sum(tris.values()), tris, flush=True)
    for key in list(glows):
        bpy.data.objects.remove(glows[key], do_unlink=True)
    glows = {"Glints": glints(frames, GAME, "Glints_Glow_" + GLINT_HEX, spots=((-24, 28, 0.0068, 10), (20, -18, 0.0032, 6))),
             "Seam": build_seam(GAME, 40, 4), "KeyLight": build_keylight(GAME, 12)}
    triangulate(glows)
    show_glows(glows)
    rig = skeleton(frames)
    body = bind_all(lows, rig, glows)
    print("SHELL MOVED OFF EYES AND LIDS", part_flush(body), "verts", flush=True)
    for o in list(HI.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    print("BODY tris", sum(len(p.vertices) - 2 for p in body.data.polygons), "dims", tuple(round(v, 3) for v in body.dimensions), "bones", len(rig.data.bones), flush=True)
    for o in glows.values():
        print("GLOW", o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), "tris", flush=True)
    print("MAX INFLUENCES", max(len(v.groups) for o in [body] + list(glows.values()) for v in o.data.vertices), flush=True)
    if STAGE == "all":
        print("UV OVERLAP TEXELS", uv_overlap_texels(body.data, 1024), flush=True)
    zs = [(o.matrix_world @ v.co).z for o in [body] + list(glows.values()) for v in o.data.vertices]
    print("Z range", round(min(zs), 4), round(max(zs), 4), flush=True)
    for tag, fr in frames.items():
        h = fr.hinge
        print("EYE", tag, "hinge game axes", (round(-h.x, 4), round(h.z, 4), round(h.y, 4)), flush=True)
    for name in ("Body", "Head", "Jaw", "Key", "WingL", "WingTipL", "Tail1"):
        p = rig.data.bones[name].head_local
        print("BONE", name, "game axes", (round(-p.x, 4), round(p.z, 4), round(p.y, 4)), flush=True)
    print("KEY AXIS game axes", (round(-KEY_DIR.x, 4), round(KEY_DIR.z, 4), round(KEY_DIR.y, 4)), flush=True)
    probe(rig, body)
    chk = Checker(body)
    pose(rig, {})
    print("POSE Rest", chk.run(), flush=True)


# its poses (signs measured on the mesh, probe): a left wing swings down with +z and folds back with +y, its tip likewise; the head tips back with +x,
# turns left with +y, rolls with z; the lower beak opens with -x; a tail feather fans to its right with +y and tips down with +x; a leg swings forward
# and up with +x. Left values; the right mirrors y and z.
FLAP_UP = sym({"WingL": (0, 0.0, -0.55), "WingTipL": (0, -0.08, -0.25)})
FLAP_DOWN = sym({"WingL": (0, -0.22, 0.38), "WingTipL": (0, 0.0, 0.32)})       # (swept a little forward: straight down, its inner feathers cut into its flanks)
FOLD = sym({"WingL": (0, 0.0, 0.04), "WingTipL": (0, 0.6, 0.05)})     # its tips folded back over its back (folded at its sides, the plates cut into its body)
SING = {"Head": (0.2, 0, 0), "Jaw": (-0.35, 0, 0)}          # (further back, its nape met its back)
TAIL_FAN = {"Tail1": (0, 0.35, 0), "Tail2": (0, 0.17, 0), "Tail4": (0, -0.17, 0), "Tail5": (0, -0.35, 0)}
TAIL_UP = {"Tail%d" % (k + 1): (-0.3, 0, 0) for k in range(TAIL_FEATHERS)}
RUN_DOWN = sym({"Head": (-0.35, 0, 0.15), "WingL": (0, -0.1, 0.2), "WingTipL": (0, 0.3, 0.1), "Body": (-0.1, 0, 0)})
for _k in range(TAIL_FEATHERS):
    RUN_DOWN["Tail%d" % (_k + 1)] = (0.2, 0, 0)
LOOK = {"Head": (0.05, 0.55, 0.05)}
TILT = {"Head": (0, 0, 0.35)}
LEGS_TUCK = sym({"LegL": (0.4, 0, 0)})


def pose_library(frames):
    def lids(up, low):
        out = {}
        for tag, fr in frames.items():
            out["LidU" + tag] = (tuple(fr.hinge), -up, (0, 0, 0))
            out["LidL" + tag] = (tuple(fr.hinge), low, (0, 0, 0))
        return out
    lib = {"Blink": lids(BLINK_U, BLINK_L), "FlapUp": spec(FLAP_UP), "FlapDown": spec(FLAP_DOWN), "Fold": spec(FOLD), "Sing": spec(SING),
           "TailFan": spec(TAIL_FAN), "TailUp": spec(TAIL_UP), "RunDown": spec(RUN_DOWN), "Look": spec(LOOK), "Tilt": spec(TILT), "Legs": spec(LEGS_TUCK)}
    lib["SingFan"] = {**spec({**SING, **TAIL_FAN, **FLAP_UP})}
    return lib


GAME_TABLES = {"FLAP_UP": FLAP_UP, "FLAP_DOWN": FLAP_DOWN, "FOLD": FOLD, "SING": SING, "TAIL_FAN": TAIL_FAN, "TAIL_UP": TAIL_UP, "RUN_DOWN": RUN_DOWN,
               "LOOK": LOOK, "TILT": TILT, "LEGS_TUCK": LEGS_TUCK}
TRANSITIONS = [("Rest", "FlapUp"), ("FlapUp", "FlapDown"), ("FlapDown", "Rest"), ("Rest", "Fold"), ("Fold", "FlapUp"), ("Rest", "RunDown"),
               ("RunDown", "FlapDown"), ("Rest", "SingFan"), ("Rest", "Look"), ("Rest", "Tilt")]


def mixed(a, b, w):
    out = {}
    for bone in set(a) | set(b):
        qa = Matrix.Rotation(math.radians(a[bone][1]), 3, Vector(a[bone][0])).to_quaternion() if bone in a else Matrix.Identity(3).to_quaternion()
        qb = Matrix.Rotation(math.radians(b[bone][1]), 3, Vector(b[bone][0])).to_quaternion() if bone in b else Matrix.Identity(3).to_quaternion()
        axis, angle = qa.slerp(qb, w).to_axis_angle()
        out[bone] = (tuple(axis), math.degrees(angle), (0, 0, 0))
    return out


def worse(now, rest):
    """What a pose adds over the rest pose (the head's lower part sits in the collar, the wings' roots in the shoulder, by design)."""
    return {k: v - rest[k] for k, v in now.items() if k != "low z" and v > rest[k] + 4}


POSE_VIEWS = [(0, -1, 0.15, 2.0, VIEW_AT), (0.62, -0.72, 0.3, 2.0, VIEW_AT), (1, 0.05, 0.1, 2.0, VIEW_AT), (-0.4, 0.8, 0.5, 2.0, VIEW_AT)]

if __name__ == "__main__" and STAGE in ("rig", "all"):
    rest = chk.run()
    lib = pose_library(frames)
    for name, sp in lib.items():
        pose(rig, sp)
        r = chk.run()
        print("POSE", name, worse(r, rest) or "clean", "low z", r["low z"], flush=True)
        if STAGE == "rig" and "shots" in ARGS:
            shots(os.path.join(REVIEW, "pose" + name), POSE_VIEWS, size=420)
    if "which" in ARGS:
        d_all = dominant(body)
        gp = read_attr(body, "group") if "group" in body.data.attributes else None
        for name in ("Rest", "FlapDown", "Fold", "RunDown"):
            pose(rig, lib.get(name, {}))
            co, tris = posed(body)
            w = chk.wing_free["L"]
            ta = BVHTree.FromPolygons([tuple(c) for c in co], [tris[f] for f in w])
            tb = BVHTree.FromPolygons([tuple(c) for c in co], [tris[f] for f in chk.body_shell])
            hits = ta.overlap(tb)
            where = {}
            for i, _ in hits:
                f = w[i]
                key = (d_all[tris[f][0]], int(gp[tris[f][0]]) if gp is not None else -1)
                where.setdefault(key, []).append(tuple(np.round(co[list(tris[f])].mean(0), 3)))
            print("WHICH", name, {k: (len(v), v[:2]) for k, v in where.items()}, flush=True)
        pose(rig, {})
    lib_r = dict(lib, Rest={})
    for na, nb in TRANSITIONS:
        bad = {}
        for k in range(11):
            pose(rig, mixed(lib_r[na], lib_r[nb], k / 10))
            for key, v in worse(chk.run(), rest).items():
                bad[key] = max(bad.get(key, 0), v)
        print("TRANSITION", na, "->", nb, bad or "clean", flush=True)
    for name, table in GAME_TABLES.items():
        print("TABLE", name, "{ " + ", ".join("%s = { %s }" % (b, ", ".join("%g" % x for x in v)) for b, v in sorted(table.items())) + " }", flush=True)
    pose(rig, {})
    if STAGE == "all":
        scene.cycles.samples = 28
        shots(os.path.join(REVIEW, "game"), VIEWS + EXTRA, target=VIEW_AT, dist=2.0, size=560)
        for name in ("FlapUp", "FlapDown", "Fold", "SingFan", "RunDown", "Blink"):
            pose(rig, lib[name])
            shots(os.path.join(REVIEW, "gamepose" + name), POSE_VIEWS[:2], size=420)
        pose(rig, {})
        for o in glows.values():
            if not o.data.uv_layers:
                o.data.uv_layers.new(name="UVMap")
        path = save_all((0.62, -0.72, 0.3, 2.0, VIEW_AT))
        print("BLEND", path, os.path.getsize(path) // 1024, "KB", flush=True)
        print("FBX", export_fbx(rig, body, list(glows.values())), flush=True)
    print("DONE", flush=True)
