"""The Cinder Roc, stage 1: the reference and silhouette study (run inside Blender, headless).

    blender -b --factory-startup -P tools/blender/guardians/cinder_roc_study.py -- [out_folder]

Eight candidate bodies for the fire-bird of Ember Peak, each built as a flat proxy from the same parts the real model will use
(torso lobes, an S or straight neck, a hooked beak, five ribbons of tail, a crest, two legs, two wings with a real arm and a fan of
primaries and secondaries) and rendered as a black silhouette, in orthographic views: standing with the wings folded, from the side;
from the front with the wings spread; from above with the wings spread. The sheet is judged for the myth first (would anyone call it
just a bird?), then for the fight: the black shape must read at 60 studs, the open wing must read as a weapon, the closed wing as a
cloak, and the eye must find the head at once.

Reference read before drawing (nothing copied: each is a fact about how such birds are built):
  - the Peng of the Zhuangzi (a bird whose wings hang from the sky like clouds, a back of a thousand li): scale and awe come from
    the span against the body, so the wings stay huge against a compact trunk;
  - a harpy eagle and a golden eagle perched: the body leans 35 to 60 degrees, the thigh is a deep feathered trouser, the shank
    below it is bare and scaled, the toes grip, the hallux is the killing talon; the wing, folded, is a Z (humerus back, forearm
    forward, hand back) with the wrist standing proud over the back;
  - a grey heron's neck: an S whose lower bend sits forward of the chest and whose upper bend carries the head back over it, so
    the head can stab forward from a coiled neck: a heron's neck is also what lets a head hold still while the body moves;
  - a secretary bird and a cassowary: a bird on long digitigrade legs that kicks and stamps, a crest of quills;
  - a lappet-faced vulture and a condor: the hunch, the ruff, a head sunk between the shoulders (menace, but it reads as scavenger);
  - an arabian-night Roc and the Persian Simurgh: the span and the long trailing tail.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
for sub in ("../eggs", "../world", "."):
    sys.path.insert(0, os.path.normpath(os.path.join(HERE, sub)))
import egg_hi as Hm  # noqa: E402
import egg_kit as K  # noqa: E402

W = K.W
V = Vector
REPO = W.REPO


def rb(p):
    return W.rb(*p)


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for x in list(block):
            block.remove(x)


# ---------- parts, in Roblox studs ----------
def ell(hi, centre, radii, pitch=0.0, nu=14, nv=9):
    """An ellipsoid, its long axis -Z raised by `pitch` degrees at the front."""
    rot = Matrix.Rotation(math.radians(pitch), 3, "X")
    c = V(centre)
    rows = []
    for j in range(nv + 1):
        th = math.pi * j / nv
        row = []
        for i in range(nu):
            a = 2 * math.pi * i / nu
            d = V((math.sin(th) * math.cos(a) * radii[0], -math.cos(th) * radii[1], math.sin(th) * math.sin(a) * radii[2]))
            row.append(hi.v(c + rot @ d))
        rows.append(row)
    for j in range(nv):
        for i in range(nu):
            k = (i + 1) % nu
            hi.f([rows[j][i], rows[j][k], rows[j + 1][k], rows[j + 1][i]], [(0, 0)] * 4)


def tube(hi, pts, radii, sides=8):
    """A tapering tube through points; radii is a function of 0..1 along it or a pair."""
    fn = radii if callable(radii) else (lambda t: radii[0] + (radii[1] - radii[0]) * t)
    Hm.htube(hi, [tuple(p) for p in pts], fn, sides=sides, per=4, uv_scale=1.0, tip=True, wobble=0.0)


def ribbon(hi, pts, width, normal=(0, 1, 0), steps=12):
    """A flat strip along a curve: `width` is a function of 0..1 (half width). The face stays square to `normal` as far as it can."""
    curve = [V(p) for p in W.catmull([tuple(p) for p in pts], steps // max(1, len(pts) - 1) + 2)]
    n = V(normal)
    rows = []
    for i, c in enumerate(curve):
        t = i / (len(curve) - 1)
        tan = (curve[min(i + 1, len(curve) - 1)] - curve[max(i - 1, 0)]).normalized()
        side = tan.cross(n)
        if side.length < 1e-3:
            side = tan.cross(V((1, 0, 0)))
        side.normalize()
        w = width(t)
        rows.append((hi.v(c - side * w), hi.v(c + side * w)))
    for a, b in zip(rows, rows[1:]):
        hi.f([a[0], a[1], b[1], b[0]], [(0, 0)] * 4)
        hi.f([a[0], b[0], b[1], a[1]], [(0, 0)] * 4)       # both faces: it is a silhouette


def leaf_w(wmax, tip=0.35, root=0.25):
    """Half width: a blade that swells fast and ends in a point, `tip` the share that tapers."""
    def fn(t):
        up = min(1.0, t / max(root, 1e-3))
        down = min(1.0, (1 - t) / max(tip, 1e-3))
        return wmax * (up ** 0.6) * (down ** 0.8)
    return fn


# ---------- the wing: a real arm, then the feathers it carries ----------
def wing(hi, s, shoulder, dirs, lens, normal, back, primaries=10, secondaries=12, plen=(8.0, 11.5), slen=(5.0, 7.0), fan=70.0, width=1.15):
    """One wing (side s: +1 right, -1 left). dirs: unit directions of the upper arm, forearm and hand; normal: the wing's face; back:
    where the trailing edge points. Feathers: primaries fan from the hand, secondaries trail from the forearm, tertials from the upper arm."""
    pts = [V(shoulder)]
    for d, l in zip(dirs, lens):
        pts.append(pts[-1] + V(d).normalized() * l)
    tube(hi, pts, lambda t: 0.9 - 0.5 * t, sides=8)
    n = V(normal).normalized()

    def trail_of(d):
        b = V(back) - d * V(back).dot(d)
        return b.normalized()

    # primaries: from the hand, fanned from the hand's own direction round toward the trailing edge
    d3 = V(dirs[2]).normalized()
    t3 = trail_of(d3)
    for k in range(primaries):
        q = k / (primaries - 1)
        ang = math.radians(8 + (fan - 8) * q)
        d = (d3 * math.cos(ang) + t3 * math.sin(ang)).normalized()
        length = plen[0] + (plen[1] - plen[0]) * math.sin(math.pi * (0.15 + 0.65 * q)) ** 0.7
        root = pts[2].lerp(pts[3], 0.35 + 0.65 * (1 - q) * 0.9)
        curve = [root, root + d * length * 0.5 + n * 0.25, root + d * length + (n * 0.5 - d3 * 0.5 * q)]
        ribbon(hi, curve, leaf_w(width * (1.0 - 0.25 * q), 0.28, 0.2), n)
    # secondaries: along the forearm, trailing
    d2 = V(dirs[1]).normalized()
    t2 = trail_of(d2)
    for k in range(secondaries):
        q = k / (secondaries - 1)
        root = pts[1].lerp(pts[2], q)
        d = (t2 * math.cos(math.radians(14)) - d2 * math.sin(math.radians(14)) * (1 - q * 0.4) * -1).normalized()
        d = (t2 + d2 * (0.30 - 0.1 * q)).normalized()
        length = slen[0] + (slen[1] - slen[0]) * (1 - 0.5 * q)
        curve = [root, root + d * length * 0.5 + n * 0.15, root + d * length + n * 0.3]
        ribbon(hi, curve, leaf_w(width * 1.15, 0.3, 0.2), n)
    d1 = V(dirs[0]).normalized()
    t1 = trail_of(d1)
    for k in range(4):
        q = k / 3
        root = pts[0].lerp(pts[1], 0.2 + 0.7 * q)
        d = (t1 + d1 * 0.08).normalized()
        length = 6.4 - 0.9 * q
        curve = [root, root + d * length * 0.5 + n * 0.1, root + d * length + n * 0.2]
        ribbon(hi, curve, leaf_w(width * 1.2, 0.3, 0.2), n)
    return pts


SPREAD = lambda s: dict(dirs=[(s * 0.96, 0.10, 0.26), (s * 0.97, 0.06, -0.22), (s * 0.95, 0.14, 0.28)], normal=(0, 1, 0), back=(0, -0.08, 1))
HALF = lambda s: dict(dirs=[(s * 0.80, 0.05, 0.55), (s * 0.60, 0.45, -0.60), (s * 0.70, 0.15, 0.65)], normal=(s * 0.3, 0.9, 0.1), back=(0, -0.3, 1))
FOLDED = lambda s: dict(dirs=[(s * 0.30, 0.10, 0.95), (s * 0.12, 0.34, -0.93), (s * 0.10, -0.12, 0.98)], normal=(s, 0.1, 0), back=(0, -1, 0.12))
CLOAK = lambda s: dict(dirs=[(s * 0.35, -0.30, 0.88), (s * 0.20, -0.45, -0.87), (s * 0.15, -0.55, 0.82)], normal=(s, 0.1, 0), back=(0, -1, 0.3))
DROOP = lambda s: dict(dirs=[(s * 0.85, -0.45, 0.28), (s * 0.55, -0.82, -0.15), (s * 0.35, -0.92, 0.18)], normal=(s * 0.6, 0.5, 0), back=(0, -0.6, 0.8))
RAISED = lambda s: dict(dirs=[(s * 0.55, 0.78, 0.30), (s * 0.55, 0.80, -0.20), (s * 0.55, 0.78, 0.30)], normal=(s * 0.8, 0.0, 0.2), back=(0, 0.2, 1))


# ---------- a candidate ----------
def build(c, pose="folded"):
    """c: dict of the candidate's numbers. Returns the object (one mesh: it is only a shadow)."""
    hi = Hm.Hi()
    p = c["pitch"]
    hip = c["hip"]
    rot = Matrix.Rotation(math.radians(p), 3, "X")
    axis = rot @ V((0, 0, -1))
    up = rot @ V((0, 1, 0))
    centre = V((0, hip + c["lift"], c.get("shift", 0.0)))
    L, R, H = c["torso"]
    for off, sc in ((-0.46, (0.62, 0.70, 0.26)), (-0.28, (0.86, 0.90, 0.32)), (-0.04, (1.0, 1.0, 0.36)), (0.20, (0.98, 1.0, 0.34)), (0.40, (0.80, 0.86, 0.24))):
        ell(hi, centre + axis * (off * L), (R * sc[0], H * sc[1], L * sc[2]), p)
    shoulder = centre + axis * (0.30 * L) + up * (0.45 * H)
    # the neck
    neck = [shoulder + V(q) for q in c["neck"]]
    tube(hi, neck, lambda t: c["neck_r"][0] + (c["neck_r"][1] - c["neck_r"][0]) * t, sides=9)
    head = neck[-1] + V(c.get("head_off", (0, 0.2, -0.8)))
    ell(hi, head, (c["head"][0], c["head"][1], c["head"][2]), c.get("head_pitch", -12))
    # the beak: a hooked blade
    bl, hook = c["beak"]
    bd = (rot @ V((0, 0, 1))) * 0 + V((0, -0.22, -1)).normalized()
    b0 = head + V((0, -0.1, -c["head"][2] * 0.7))
    tube(hi, [b0, b0 + bd * bl * 0.5, b0 + bd * bl * 0.95 + V((0, -hook * 0.3, 0)), b0 + bd * bl + V((0, -hook, 0.2))], lambda t: c["head"][1] * 0.62 * (1 - 0.9 * t), sides=7)
    # the crest
    for k, (dy, dz, ln, wd) in enumerate(c["crest"]):
        root = head + V((0, c["head"][1] * 0.8, 0.2))
        end = root + V((dy * 0.25 * (k % 3 - 1), dy, dz)).normalized() * ln
        mid = root.lerp(end, 0.5) + V((0, 0.5, 0))
        ribbon(hi, [root, mid, end + V((0, -ln * 0.12, 0.4))], leaf_w(wd, 0.5, 0.3), (1, 0, 0))
    # the tail: ribbons that trail, spread by yaw
    rump = centre - axis * (0.50 * L) + V((0, 0.0, 0))
    for yaw, lift, ln, wd in c["tail"]:
        d = V((math.sin(math.radians(yaw)), -lift, 1)).normalized()
        end = rump + d * ln
        end.y = max(0.3, end.y + c.get("tail_fall", 0.0))
        mid = rump.lerp(end, 0.5) + V((0, 0.5, 0))
        ribbon(hi, [rump, mid, end], leaf_w(wd, 0.55, 0.12), (0, 1, 0) if abs(yaw) < 1 else (math.sin(math.radians(yaw)), 1, 0))
    # the legs: a feathered trouser, a shank, the foot
    for s in (-1, 1):
        hipj = V((s * c["leg_x"], hip, 0.6))
        knee = hipj + V((0, -c["leg"][0] * 0.78, -c["leg"][0] * 0.62))
        ankle = knee + V((0, -c["leg"][1] * 0.85, c["leg"][1] * 0.52))
        ball = V((s * c["leg_x"], 0.9, ankle.z - c["leg"][2] * 0.55))
        ball.y = 0.9
        ankle.y = max(ankle.y, ball.y + c["leg"][2] * 0.82)
        ell(hi, hipj.lerp(knee, 0.5), (1.9, 3.2, 2.5), 0)
        tube(hi, [knee, ankle], (0.8, 0.55), sides=7)
        tube(hi, [ankle, ball], (0.5, 0.42), sides=7)
        for dx in (-0.9, 0.0, 0.9):
            tube(hi, [ball, V((ball.x + dx, 0.45, ball.z - 3.6))], (0.32, 0.18), sides=5)
        tube(hi, [ball, V((ball.x, 0.5, ball.z + 2.4))], (0.34, 0.2), sides=5)
    # the wings
    for s in (-1, 1):
        sh = shoulder + V((s * R * 0.9, 0.0, -0.4))
        spec = {"folded": FOLDED, "spread": SPREAD, "half": HALF, "cloak": CLOAK, "droop": DROOP, "raised": RAISED}[c.get("wing_" + pose, pose)](s)
        wl = c["wing"]
        wing(hi, s, sh, spec["dirs"], wl[0], spec["normal"], spec["back"], plen=wl[1], slen=wl[2], width=wl[3])
    mat = bpy.data.materials.get("Shade") or bpy.data.materials.new("Shade")
    mat.diffuse_color = (0.02, 0.02, 0.025, 1)
    o = hi.object("Candidate", bpy.context.scene.collection, [mat], smooth=True, weld=0)
    return o


def stats(o):
    xs = [rb_back(o.matrix_world @ v.co) for v in o.data.vertices]
    lo = V((min(p.x for p in xs), min(p.y for p in xs), min(p.z for p in xs)))
    hi = V((max(p.x for p in xs), max(p.y for p in xs), max(p.z for p in xs)))
    return lo, hi


def rb_back(p):
    return V((p.x, p.z, -p.y))


# the eight, each a different answer to "what is a fire-bird that is not just a bird"
CANDIDATES = {
    "A Heron-Eagle": dict(pitch=24, hip=12.2, lift=1.6, torso=(7.6, 4.2, 4.5), neck=[(0, 0, 0), (0, 1.8, -2.6), (0, 4.0, -2.4), (0, 5.8, -3.6)], neck_r=(1.9, 1.0),
                          head=(1.35, 1.35, 1.9), beak=(4.6, 1.5), crest=[(0.9, 1.0, 6.0, 0.55), (1.0, 0.8, 7.4, 0.6), (0.7, 1.0, 5.4, 0.5), (1.0, 0.9, 6.8, 0.55), (0.8, 1.0, 5.0, 0.45)],
                          tail=[(-24, 0.35, 15, 0.8), (-12, 0.42, 17.5, 0.9), (0, 0.5, 19.5, 1.0), (12, 0.42, 17.5, 0.9), (24, 0.35, 15, 0.8)], tail_fall=-3.0,
                          leg=(5.0, 6.6, 4.0), leg_x=2.9, wing=([5.3, 6.0, 4.0], (9.0, 12.5), (5.4, 7.6), 1.25)),
    "B Strider": dict(pitch=8, hip=15.0, lift=1.4, torso=(7.0, 3.4, 3.6), neck=[(0, 0, 0), (0, 1.2, -2.0), (0, 2.6, -2.8)], neck_r=(1.5, 0.9),
                      head=(1.1, 1.1, 1.6), beak=(3.0, 1.0), crest=[(1.0, 1.0, 5.0, 0.2)] * 7, tail=[(-6, 0.1, 12, 0.7), (0, 0.15, 17, 0.8), (6, 0.1, 12, 0.7)], tail_fall=-8,
                      leg=(7.2, 8.4, 5.5), leg_x=2.4, wing=([5.0, 5.8, 3.8], (8.4, 11.5), (5.0, 7.0), 1.1)),
    "C Mantler": dict(pitch=52, hip=11.4, lift=2.4, torso=(7.0, 4.6, 5.0), neck=[(0, 0, 0), (0, 1.6, -0.8), (0, 3.0, -1.8)], neck_r=(2.6, 1.8),
                      head=(1.6, 1.5, 2.0), beak=(4.0, 1.7), crest=[(1.0, 0.9, 3.0, 0.9)] * 3, tail=[(-14, 0.2, 9, 1.4), (0, 0.3, 11, 1.5), (14, 0.2, 9, 1.4)], tail_fall=-2,
                      leg=(4.6, 6.0, 3.6), leg_x=2.8, wing=([5.6, 6.2, 4.2], (9.4, 13.0), (5.6, 7.8), 1.3), wing_folded="half"),
    "D Cassowary": dict(pitch=-6, hip=11.0, lift=1.6, torso=(8.4, 3.8, 4.0), neck=[(0, 0, 0), (0, 0.4, -2.6), (0, -0.4, -5.2)], neck_r=(1.8, 1.0),
                        head=(1.2, 1.3, 2.0), beak=(3.8, 1.1), crest=[(1.0, 0.6, 5.6, 0.8)] * 2 + [(1.0, 0.6, 4.2, 0.8)] * 2, tail=[(-8, 0.1, 6, 1.5), (0, 0.1, 8, 1.6), (8, 0.1, 6, 1.5)], tail_fall=-5,
                        leg=(5.2, 6.6, 4.4), leg_x=2.8, wing=([5.0, 5.8, 3.8], (8.4, 11.5), (5.0, 7.0), 1.1)),
    "E Peng Colossus": dict(pitch=62, hip=11.0, lift=3.0, torso=(7.2, 3.8, 4.2), neck=[(0, 0, 0), (0, 3.2, -0.4), (0, 6.2, -0.8), (0, 9.0, -1.6)], neck_r=(1.7, 0.95),
                            head=(1.2, 1.3, 1.8), beak=(3.8, 1.2), crest=[(1.0, 0.6, 9.0, 0.5)] * 3, tail=[(0, 0.5, 26, 1.3)], tail_fall=-4,
                            leg=(4.8, 6.2, 3.8), leg_x=2.6, wing=([5.6, 6.2, 4.2], (9.4, 13.0), (5.6, 7.8), 1.3)),
    "F Hunch": dict(pitch=14, hip=11.6, lift=1.8, torso=(7.8, 4.6, 5.0), neck=[(0, 0, 0), (0, 0.6, -2.4), (0, 0.0, -4.4)], neck_r=(2.6, 1.3),
                    head=(1.4, 1.4, 2.0), beak=(4.4, 1.6), crest=[], tail=[(-10, 0.2, 7, 1.3), (0, 0.25, 8.5, 1.4), (10, 0.2, 7, 1.3)], tail_fall=-3,
                    leg=(4.6, 5.6, 3.6), leg_x=3.0, wing=([5.0, 5.8, 3.8], (8.4, 11.5), (5.0, 7.0), 1.1), wing_folded="droop"),
    "G Swan-Phoenix": dict(pitch=34, hip=12.2, lift=1.4, torso=(6.4, 3.6, 3.8), neck=[(0, 0, 0), (0, 2.6, -1.4), (0, 5.8, -1.6), (0, 8.4, -3.2), (0, 8.8, -5.2)], neck_r=(1.5, 0.8),
                           head=(0.9, 0.9, 1.4), beak=(2.8, 0.6), crest=[(1.0, 0.5, 3.6, 0.3)] * 3, tail=[(-18, 0.12, 22, 1.6), (-9, 0.1, 26, 1.8), (0, 0.1, 30, 2.0), (9, 0.1, 26, 1.8), (18, 0.12, 22, 1.6)], tail_fall=-8,
                           leg=(4.4, 5.8, 3.4), leg_x=2.2, wing=([5.0, 5.8, 3.8], (8.4, 11.5), (5.0, 7.0), 1.1)),
    "H Horned Owl-Roc": dict(pitch=48, hip=11.2, lift=2.2, torso=(6.6, 5.0, 5.0), neck=[(0, 0, 0), (0, 1.4, -0.6)], neck_r=(3.0, 2.6),
                             head=(2.4, 2.1, 2.4), beak=(2.2, 1.0), crest=[(1.0, 0.1, 3.8, 0.7), (1.0, 0.1, 3.8, 0.7)], tail=[(-6, 0.3, 8, 1.4), (0, 0.3, 9, 1.5), (6, 0.3, 8, 1.4)], tail_fall=-2,
                             leg=(4.0, 5.2, 3.2), leg_x=2.8, wing=([5.4, 6.0, 4.0], (9.0, 12.5), (5.4, 7.6), 1.25)),
}


# ---------- the render: flat black on white, orthographic ----------
def scene_setup(size):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "FLAT"
    sh.color_type = "SINGLE"
    sh.single_color = (0.03, 0.03, 0.035)
    sh.background_type = "VIEWPORT"
    sh.background_color = (0.93, 0.93, 0.90)
    sh.show_shadows = False
    sh.show_cavity = False
    sc.display_settings.display_device = "sRGB"
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    cam_data = bpy.data.cameras.new("StudyCam")
    cam_data.type = "ORTHO"
    cam = bpy.data.objects.new("StudyCam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return sc, cam


def shot(sc, cam, yaw, pitch, centre, scale, tmp):
    import numpy as np
    y, p = math.radians(yaw), math.radians(pitch)
    c = V(centre)
    cam.location = c + V((math.sin(y) * math.cos(p), math.cos(y) * math.cos(p), math.sin(p))) * 200
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = scale
    bpy.context.view_layer.update()
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(tmp, check_existing=False)
    size = sc.render.resolution_x
    px = np.zeros(size * size * 4, dtype=np.float32)
    im.pixels.foreach_get(px)
    bpy.data.images.remove(im)
    return px.reshape(size, size, 4)


def sheet(tiles, columns, path):
    import numpy as np
    size = tiles[0].shape[0]
    rows = [np.concatenate(tiles[i:i + columns] + [np.ones_like(tiles[0])] * (columns - len(tiles[i:i + columns])), axis=1) for i in range(0, len(tiles), columns)]
    out = np.concatenate(rows[::-1], axis=0)
    img = bpy.data.images.new("Sheet", out.shape[1], out.shape[0])
    img.pixels.foreach_set(out.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def mark(tile, size):
    """A thin ground line and 10-stud ticks up the left edge, burned into a tile (scale: size px = 56 studs)."""
    return tile


def run(folder):
    os.makedirs(folder, exist_ok=True)
    size = 380
    sc, cam = None, None
    report = {}
    tmp = os.path.join(folder, "_tile.png")
    for name, c in CANDIDATES.items():
        clear()
        if sc is None or True:
            sc, cam = scene_setup(size)
        tiles = []
        for pose, views in (("folded", [(-90, 0, "side")]), ("spread", [(-38, 22, "three"), (-90, 82, "top")])):
            o = build(c, pose)
            lo, hi = stats(o)
            report[(name, pose)] = (round(lo.x, 1), round(hi.x, 1), round(hi.y, 1), round(lo.z, 1), round(hi.z, 1))
            for yaw, pitch, _ in views:
                centre = W.rb(0, 12, 2) if pitch < 80 else W.rb(0, 14, 2)
                scale = {"side": 46, "three": 60, "top": 62}[_]
                tiles.append(shot(sc, cam, yaw, pitch, centre, scale, tmp))
            bpy.data.objects.remove(o, do_unlink=True)
        sheet(tiles, 3, os.path.join(folder, "study_" + name.split()[0] + ".png"))
    if os.path.exists(tmp):
        os.remove(tmp)
    return report


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = argv[0] if argv else os.path.join(REPO, "renders", "cinder_roc", "study")
    for k, v in run(out).items():
        print(k, "x", v[0], v[1], "top", v[2], "z", v[3], v[4])
