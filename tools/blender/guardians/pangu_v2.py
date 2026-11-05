"""Pangu the World-Splitter, rebuilt with a real skeleton (the owner, 2026-11-04: "all the boss in the game is actually stiff
specially the tiangou and pangu ... please put rig, skeleton and more weight paint"). The same titan of dark stone at the same
size, so the fight's ranges hold: one continuous skin over about 40 bones, instead of 11 rigid segments.

Bound with the arms spread (shoulders deform best from there); his standing pose, the axe on the right shoulder and the left arm
free at his side, is a pose the game holds. The axe rides its own bone. He holds no egg: no guardian does (the owner, 2026-11-02:
"Remove all the eggs that boss holding or covering"), only the three stands behind him. The legs are solved, not keyed by
eye, so a planted foot truly stays planted and the stride is measured.

Authored in Roblox studs: facing -Z, feet on the ground at y = 0, left is -X.

    import pangu_v2 as P
    P.build_form()             # the skin, beard, axe and hangings in clay, and the skeleton
    P.bind()                   # weights, cleaned to 4 influences a vertex
    P.review_form(path)        # clay from six sides, in the pose he stands in
    P.stress(path)             # the skeleton bent to its limits
    P.render_clip(folder)      # walk, run and axe cleave, frames for a video
"""
import json
import math
import os

import bpy
from mathutils import Matrix, Vector

import egg_kit as K
import guardian_kit as G
import tiangou_v2 as T

W = K.W
V = Vector
NAME = "Pangu"
RIG = "PanguRig"

# ---------- the skeleton: bone: (parent, head, tail), Roblox studs ----------
_B = {
    "Root": (None, (0, 0, 0), (0, 0, -3)),
    "Hips": ("Root", (0, 18.2, 0.2), (0, 21.0, 0.2)),
    "Spine": ("Hips", (0, 21.0, 0.2), (0, 24.6, 0.1)),
    "Chest": ("Spine", (0, 24.6, 0.1), (0, 31.2, -0.1)),
    "Neck": ("Chest", (0, 31.2, -0.1), (0, 33.2, -0.6)),
    "Head": ("Neck", (0, 33.2, -0.6), (0, 38.2, -0.8)),
    "Jaw": ("Head", (0, 33.9, -1.0), (0, 32.6, -3.0)),
    "Eyes": ("Head", (0, 35.35, -2.3), (0, 35.35, -3.3)),    # both eyes: slid into their sockets to blink and to glare
    "Beard1": ("Jaw", (0, 32.8, -2.9), (0, 30.9, -3.3)),
    "Beard2": ("Beard1", (0, 30.9, -3.3), (0, 28.9, -3.5)),
    "LoinFront1": ("Hips", (0, 19.2, -3.7), (0, 14.8, -4.4)),
    "LoinFront2": ("LoinFront1", (0, 14.8, -4.4), (0, 10.2, -4.2)),
    "LoinBack1": ("Hips", (0, 19.2, 3.9), (0, 14.8, 4.7)),
    "LoinBack2": ("LoinBack1", (0, 14.8, 4.7), (0, 10.4, 4.6)),
    "MantleMid1": ("Chest", (0, 31.4, 3.0), (0, 24.6, 5.6)),
    "MantleMid2": ("MantleMid1", (0, 24.6, 5.6), (0, 17.0, 6.2)),
}
FIST = (20.0, 20.5, -0.4)      # where the right hand grips the haft, as bound


def _side(sign, tag):
    x = lambda v: v * sign
    b = {
        "Clavicle": ("Chest", (x(1.8), 30.2, 0.0), (x(8.0), 31.0, 0.2)),
        "UpperArm": ("Clavicle", (x(8.0), 31.0, 0.2), (x(13.8), 26.0, 0.5)),
        "Forearm": ("UpperArm", (x(13.8), 26.0, 0.5), (x(18.6), 21.8, -0.2)),
        "Hand": ("Forearm", (x(18.6), 21.8, -0.2), (x(20.5), 20.1, -0.4)),
        "Fingers": ("Hand", (x(20.5), 20.1, -0.4), (x(22.2), 18.6, -0.5)),
        "Thumb": ("Hand", (x(19.0), 21.1, -2.2), (x(19.3), 18.9, -3.7)),
        "Thigh": ("Hips", (x(4.2), 17.4, 0.2), (x(4.5), 9.6, -0.5)),
        "Shin": ("Thigh", (x(4.5), 9.6, -0.5), (x(4.7), 2.2, 0.2)),
        "Foot": ("Shin", (x(4.7), 2.2, 0.2), (x(4.8), 0.9, -2.8)),
        "Toe": ("Foot", (x(4.8), 0.9, -2.8), (x(4.8), 0.7, -5.2)),
        "Mantle1": ("Chest", (x(5.2), 31.0, 3.0), (x(7.0), 25.0, 5.2)),
        "Mantle2": ("Mantle1", (x(7.0), 25.0, 5.2), (x(7.8), 18.6, 5.8)),
    }
    return {tag + name: (((tag + p) if p in b else p), h, t) for name, (p, h, t) in b.items()}


_B.update(_side(-1, "Left"))
_B.update(_side(1, "Right"))
_B["Axe"] = ("RightHand", FIST, (FIST[0], FIST[1], FIST[2] - 3.0))           # along the haft, toward the blade
BONES = _B


_HAFT_BIND = V((0, 0, -1))
_EDGE_BIND = V((BONES["RightFingers"][2][0] - BONES["RightHand"][1][0], BONES["RightFingers"][2][1] - BONES["RightHand"][1][1], 0)).normalized()


def _clay(name="PanguClay", rgb=(0.40, 0.40, 0.44)):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    return m


# ---------- the form: groups of soft forms ----------
limb = T._limb


def _palm_bind(sign):
    """The open palm's face as bound, square to the hand: down and inward, so the arm dropping to his side turns it to the thigh."""
    tag = "Left" if sign < 0 else "Right"
    d = (V(BONES[tag + "Fingers"][2]) - V(BONES[tag + "Hand"][1])).normalized()
    n = V((-sign * 0.66, -0.75, 0))
    return (n - d * n.dot(d)).normalized()


def _hand(sign, open_palm):
    """The hand at the end of the spread arm. Left: open and heavy, the fingers curled toward the palm, the thumb forward as he stands. Right: a fist round the haft."""
    wrist, tip = V(BONES[("Left" if sign < 0 else "Right") + "Hand"][1]), V(BONES[("Left" if sign < 0 else "Right") + "Fingers"][2])
    d = (tip - wrist).normalized()
    up = _palm_bind(sign)
    across = d.cross(up).normalized()
    at = lambda a, b, c: tuple(wrist + d * a + up * b + across * c)
    if not open_palm:
        # a real grip: the palm behind the haft, four fingers wrapped round it, the thumb closing over them toward the blade
        F, H, D = V(FIST), _HAFT_BIND, _EDGE_BIND
        B = D.cross(H).normalized()                    # the back of the hand
        round_haft = lambda deg, along, r=1.2: tuple(F + H * along + (D * math.cos(math.radians(deg)) + B * math.sin(math.radians(deg))) * r)
        palm = F - D * 1.05 + B * 0.7
        lobes = [(tuple(palm), (1.35, 1.35, 2.45), None), (tuple(wrist), (1.25, 1.25, 1.4), None),
                 (tuple(F + B * 1.05 + D * 0.35), (1.0, 1.0, 2.35), None)]    # the knuckles' ridge
        for along in (-1.68, -0.56, 0.56, 1.68):
            pts = [round_haft(a, along) for a in (75, 35, -10, -60, -110, -150)]
            rad = [(q, q, q) for q in (0.66, 0.64, 0.6, 0.56, 0.52, 0.44)]
            lobes += limb(pts, rad)
        pts = [round_haft(a, 2.75, 1.25) for a in (-185, -140, -95, -50)]
        lobes += limb(pts, [(q, q, q) for q in (0.8, 0.72, 0.62, 0.48)])
        return lobes
    # the palm: a broad, flat slab as wide as the fist, past a wrist narrower than it. Fingers as thick as the fist's, a groove between them
    lobes = []
    for c in (-1.6, -0.8, 0.0, 0.8, 1.6):
        lobes += limb([at(0.7, 0, c), at(2.5, 0, c)], [(0.8, 0.8, 0.8), (0.8, 0.8, 0.8)])     # solid, with no creases for the bake to catch on
    for c in (-1.5, -0.75, 0.0, 0.75, 1.5):
        lobes += limb([at(-0.5, 0, c * 0.3), at(0.9, 0, c)], [(1.0, 1.0, 1.0), (0.82, 0.82, 0.82)])    # the wrist fans out into the palm
    for k, c in enumerate((-1.65, -0.55, 0.55, 1.65)):
        length = (1.5, 1.7, 1.6, 1.3)[k]
        pts = [at(2.8, 0.0, c), at(2.8 + length * 0.8, 0.45, c * 1.03), at(2.8 + length * 1.45, 1.25, c * 1.05), at(2.8 + length * 1.8, 2.15, c * 1.05)]
        lobes += limb(pts, [(q, q, q) for q in (0.64, 0.6, 0.54, 0.42)])
    pts = [at(0.8, 0.25, -1.75), at(1.5, 0.75, -2.75), at(2.2, 1.3, -3.2), at(2.7, 1.85, -3.3)]    # the thumb, standing off the palm
    lobes += limb(pts, [(q, q, q) for q in (0.86, 0.68, 0.58, 0.44)])
    return lobes


def _groups():
    groups = []
    # the pelvis and belly, a heavy wedge rising into the chest
    groups.append((1.0, [
        ((0, 18.3, 0.2), (5.0, 2.6, 3.4), None), ((-3.6, 17.2, 0.2), (2.5, 2.4, 2.8), None), ((3.6, 17.2, 0.2), (2.5, 2.4, 2.8), None),
        ((-3.2, 16.6, 1.8), (2.7, 2.4, 2.3), None), ((3.2, 16.6, 1.8), (2.7, 2.4, 2.3), None),          # the glutes
        ((0, 20.8, 0.1), (5.0, 2.4, 3.3), None), ((0, 22.8, -0.5), (5.2, 2.8, 3.3), None),               # a heavy belly, no waist
    ]))
    # the chest: a broad barrel, slab pectorals, a wide back
    groups.append((0.8, [
        ((0, 26.2, 0.1), (6.8, 4.2, 3.9), None), ((-3.55, 28.9, -3.0), (3.2, 1.4, 0.72), None), ((3.55, 28.9, -3.0), (3.2, 1.4, 0.72), None),
        ((-3.6, 28.0, 2.4), (3.3, 3.0, 1.7), None), ((3.6, 28.0, 2.4), (3.3, 3.0, 1.7), None),            # the shoulder blades, no dome
        ((0, 24.8, 2.0), (5.8, 3.2, 2.0), None), ((0, 30.6, 0.4), (4.4, 2.1, 2.5), None),                  # the back, the trapezius
    ] + limb([(0, 30.4, 0.1), (0, 33.6, -0.5)], [(3.0, 2.0, 2.8), (2.25, 1.6, 2.2)])))
    # the head: a heavy brow over a deep-set stare, cheekbones, a square jaw; horns are in their own group
    groups.append((0.42, [
        ((0, 35.1, -0.3), (2.5, 2.9, 2.7), None),
        ((-1.5, 34.5, -2.0), (0.9, 0.8, 0.8), None), ((1.5, 34.5, -2.0), (0.9, 0.8, 0.8), None),
        ((0, 33.4, -1.6), (1.95, 1.25, 1.85), None), ((0, 34.75, -3.0), (0.5, 1.0, 0.55), None),
    ] + limb([(-2.45, 36.75, -1.75), (-0.3, 35.75, -3.05)], [(0.7, 0.55, 0.7), (0.5, 0.48, 0.5)])
      + limb([(2.45, 36.75, -1.75), (0.3, 35.75, -3.05)], [(0.7, 0.55, 0.7), (0.5, 0.48, 0.5)])))
    for sign in (-1, 1):
        x = lambda v: v * sign
        tag = "Left" if sign < 0 else "Right"
        base = V((x(2.0), 37.1, -0.6))
        horn = [base, base + V((x(1.8), 1.6, 0.6)), base + V((x(3.4), 3.8, 1.8)), base + V((x(3.6), 6.2, 1.2)), base + V((x(2.8), 7.6, -0.4))]
        groups.append((0.1, limb([tuple(p) for p in horn], [(r, r, r) for r in (1.3, 1.1, 0.85, 0.5, 0.12)])))
        s, e, w = (V(BONES[tag + n][1]) for n in ("UpperArm", "Forearm", "Hand"))
        # the arm: a great round deltoid, biceps and triceps, a forearm thick below the elbow
        groups.append((0.8, [(tuple(s + V((x(0.1), -0.1, 0))), (3.3, 3.0, 3.1), None), (tuple(V(BONES[tag + "Clavicle"][1]).lerp(s, 0.55)), (2.8, 1.7, 2.2), None)]
                       + limb([tuple(s), tuple(e)], [(2.5, 2.5, 2.5), (1.85, 1.85, 1.85)])
                       + [(tuple(s.lerp(e, 0.45) + V((0, 0, -0.6))), (2.2, 2.2, 1.9), None), (tuple(s.lerp(e, 0.5) + V((0, 0, 0.7))), (2.0, 2.0, 1.75), None)]
                       + limb([tuple(e), tuple(w)], [(1.95, 1.95, 1.95), (1.1, 1.1, 1.1) if sign < 0 else (1.4, 1.4, 1.4)])     # the open hand shows its wrist
                       + [(tuple(e.lerp(w, 0.3)), (2.15, 2.15, 1.9), None)]))
        groups.append((0.14, _hand(sign, open_palm=sign < 0)))
        h, kn, an = (V(BONES[tag + n][1]) for n in ("Thigh", "Shin", "Foot"))
        # the leg: a pillar. A thick thigh, a knee block, a calf high behind, a heavy foot
        groups.append((0.75, limb([tuple(h + V((0, 0.5, 0))), tuple(kn)], [(3.0, 3.0, 3.0), (2.0, 2.0, 2.0)])
                       + [(tuple(h.lerp(kn, 0.42) + V((0, 0, -0.8))), (2.45, 3.2, 2.2), None), (tuple(h.lerp(kn, 0.45) + V((0, 0, 0.8))), (2.2, 3.0, 1.9), None)]
                       + [(tuple(kn + V((0, 0, -0.4))), (2.0, 1.5, 1.85), None)]
                       + limb([tuple(kn), tuple(an)], [(1.95, 1.95, 1.95), (1.45, 1.45, 1.45)])
                       + [(tuple(kn.lerp(an, 0.3) + V((0, 0, 0.9))), (1.85, 2.7, 1.7), None)]))
        groups.append((0.35, [
            (tuple(an + V((0, -0.2, 0.2))), (1.5, 1.2, 1.6), None),
            ((x(4.7), 1.1, 1.1), (1.65, 1.1, 1.7), None),            # the heel
            ((x(4.8), 1.1, -1.8), (2.0, 1.1, 2.5), None),            # the arch
            ((x(4.8), 0.72, -4.0), (2.15, 0.68, 1.5), None),         # the ball
            ((x(4.8), 0.56, -5.4), (1.95, 0.52, 0.9), None),         # the toes' block
        ]))
    return groups


def _sockets(points, d):
    """Deep sockets cut under the brow: his eyes look out of shadow."""
    import numpy as np
    for side in (-1, 1):
        q = (points - np.array((side * 1.08, 35.28, -3.0))) / np.array((0.9, 0.46, 0.62))
        hole = (np.linalg.norm(q, axis=1) - 1.0) * 0.5
        d = np.maximum(d, -hole)
    return d


def _rough_lobes(groups):
    out = []
    for _, lobes in groups:
        for lobe in lobes:
            if lobe[0] == "seg":
                _, a, b, ra, rb = lobe
                for k in range(5):
                    t = k / 4
                    out.append((tuple(V(a).lerp(V(b), t)), tuple(ra[n] + (rb[n] - ra[n]) * t for n in range(3)), None))
            else:
                out.append(lobe)
    return out


def _beard_groups():
    """His beard hangs clear of his chest, its own mass, or it would melt into it: broad from jaw to jaw, three bound braids."""
    groups = [(0.5, [((0, 32.2, -2.5), (1.95, 1.05, 0.95), None), ((-1.75, 33.1, -1.7), (0.7, 1.4, 0.8), None), ((1.75, 33.1, -1.7), (0.7, 1.4, 0.8), None),
                     ((0, 31.0, -2.95), (1.5, 1.25, 0.8), None)])]
    for k, xx in enumerate((-0.75, 0.0, 0.75)):
        top = V((xx, 30.2, -3.1))
        groups.append((0.2, limb([tuple(top), tuple(top + V((xx * 0.15, -1.1, -0.2))), tuple(top + V((xx * 0.25, -2.2, -0.15)))],
                                 [(0.62, 0.62, 0.62), (0.48, 0.48, 0.48), (0.22, 0.22, 0.22)])))
    return groups


def _axe(coll):
    """The world-splitting axe, as bound and as held: the haft runs through the right fist, across the palm, the thumb toward
    the blade; the edge points the way the knuckles do, as on any axe or hammer. The grip never changes: it rides the hand."""
    import bmesh
    F = V(FIST)
    H, E = _HAFT_BIND, _EDGE_BIND
    S = H.cross(E).normalized()
    head = F + H * 12.2
    pt = lambda a, b: head + H * a + E * b
    # a battle-axe's crescent: a narrow neck at the haft, the throat curving out to two swept horns, one long curve of edge
    neck = [(-1.5, 0.55), (0.0, 0.5), (1.5, 0.55), (1.75, 1.3), (2.4, 2.3), (3.6, 3.3), (5.4, 4.0)]
    edge = [(5.4 * (1 - 2 * i / 20), 4.0 + 2.5 * (1 - (1 - 2 * i / 20) ** 2) ** 0.8) for i in range(21)]
    outline = neck + edge[1:-1] + [(-5.4, 4.0), (-3.6, 3.3), (-2.4, 2.3), (-1.75, 1.3)]
    thick = lambda b: 0.5 * max(0.12, 1 - max(0.0, b - 2.2) / 3.8)
    bm = bmesh.new()
    front = [bm.verts.new(W.rb(*(pt(a, b) + S * thick(b)))) for a, b in outline]
    back = [bm.verts.new(W.rb(*(pt(a, b) - S * thick(b)))) for a, b in outline]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], back[i], back[j], front[j]))
    # the haft and the socket, as simple tubes
    for a, b, r in ((-3.4, 15.5, 0.55), (10.0, 14.4, 1.0)):
        ring = 10
        bottom, top = [], []
        for k in range(ring):
            q = 2 * math.pi * k / ring
            off = S * math.cos(q) * r + E * math.sin(q) * r
            bottom.append(bm.verts.new(W.rb(*(F + H * a + off))))
            top.append(bm.verts.new(W.rb(*(F + H * b + off))))
        bm.faces.new(bottom)
        bm.faces.new(list(reversed(top)))
        for k in range(ring):
            m = (k + 1) % ring
            bm.faces.new((bottom[k], bottom[m], top[m], top[k]))
    me = bpy.data.meshes.new("PG2_Axe")
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("PG2_Axe", me)
    coll.objects.link(o)
    me.materials.append(_clay("PanguClayDark", (0.2, 0.2, 0.24)))
    return o


def _sheet(coll, name, strands, widths, rows=10, mat=None):
    """Hangings: a sheet down a few bone chains. strands: lists of points, left to right. widths: half-width at top and bottom."""
    import bmesh
    bm = bmesh.new()
    grid = []
    across = len(strands)
    for r in range(rows + 1):
        q = r / rows
        row = []
        for s, chain in enumerate(strands):
            at = q * (len(chain) - 1)
            i = min(int(at), len(chain) - 2)
            p = V(chain[i]).lerp(V(chain[i + 1]), at - i)
            row.append(p)
        pts = []
        half = widths[0] + (widths[1] - widths[0]) * q
        if across == 1:
            pts = [row[0] + V((-half, 0, 0)), row[0], row[0] + V((half, 0, 0))]
        else:
            pts = row
        grid.append([bm.verts.new(W.rb(*p)) for p in pts])
    for r in range(rows):
        for c in range(len(grid[r]) - 1):
            bm.faces.new((grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    me.materials.append(mat or _clay("PanguClayCloth", (0.24, 0.2, 0.32)))
    return o


def _clean(obj, triangulate=False):
    """What Roblox needs of a mesh: faces wound outward (it hides back faces), none collapsed, no n-gons."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.004)      # hoops' ends and sheets' seams become one surface
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4)
    # the reduction can leave crumbs: keep only real parts
    seen, parts = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        seen.add(v)
        stack = [v]
        part = []
        while stack:
            q = stack.pop()
            part.append(q)
            for e in q.link_edges:
                o = e.other_vert(q)
                if o not in seen:
                    seen.add(o)
                    stack.append(o)
        parts.append(part)
    biggest = max(len(x) for x in parts)
    crumbs = [q for x in parts if len(x) < min(8, biggest) for q in x]      # a few stray vertices, never a real piece
    if crumbs:
        bmesh.ops.delete(bm, geom=crumbs, context="VERTS")
    if triangulate:
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def _eyes(coll, skin):
    """Deep-set under the heavy brow, a titan's stare: an almond iris, a dark pupil and a heavy lid, kept stern, not wild."""
    import egg_hi as Hm
    eyes, pupils, lids = Hm.Hi(), Hm.Hi(), Hm.Hi()
    for side in (-1, 1):
        normal = V((side * 0.4, 0.04, -0.92)).normalized()
        seat = G.surface_along(skin, V((side * 1.08, 35.3, -2.5)), normal)
        G.eye(eyes, pupils, lids, seat, normal, (-side * 0.6, 0, -1), 0.6, 0.2, tilt=0.42, bulge=0.08, lid=0.72, droop=0.75, lower=0.2, slit=0.22, pupil_height=0.72)
    return (eyes.object("PG2_Eyes", coll, [_clay("PanguClayEye", (0.78, 0.62, 0.95))], smooth=True),
            pupils.object("PG2_Pupils", coll, [_clay("PanguClayPupil", (0.02, 0.01, 0.03))], smooth=True),
            lids.object("PG2_Lids", coll, [_clay()]))


def build_skeleton(coll):
    data = bpy.data.armatures.new(RIG)
    arm = bpy.data.objects.new(RIG, data)
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


def _reduce(obj, tris):
    now = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    if now > tris:
        m = obj.modifiers.new("Reduce", "DECIMATE")
        m.ratio = tris / now
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.modifier_apply(modifier=m.name)
    for p in obj.data.polygons:
        p.use_smooth = True
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def build_form(voxel=0.15, tris=19000):
    T.clear()
    coll = bpy.data.collections.new("PanguV2")
    bpy.context.scene.collection.children.link(coll)
    groups = _groups()
    skin = G.blob("PG2_Skin", coll, _clay(), _rough_lobes(groups), voxel=voxel, smooth=0.75, rough=0.0, chisel="PanguV2Chisel")
    T._settle(skin, groups, cut=_sockets)
    G.soften(skin, 6)
    T._settle(skin, groups, passes=2, cut=_sockets)
    beard_groups = _beard_groups()
    beard = G.blob("PG2_Beard", coll, _clay(), _rough_lobes(beard_groups), voxel=0.09, smooth=0.75, rough=0.0, chisel="PanguV2Chisel2")
    T._settle(beard, beard_groups)
    G.soften(beard, 4)
    counts = {"skin": _reduce(skin, tris), "beard": _reduce(beard, 1800)}
    _clean(skin)
    _clean(beard)
    _clean(_axe(coll), triangulate=True)
    _eyes(coll, skin)
    B = BONES
    chain = lambda *names: [B[names[0]][1]] + [B[n][2] for n in names]
    _sheet(coll, "PG2_Mantle", [chain("LeftMantle1", "LeftMantle2"), chain("MantleMid1", "MantleMid2"), chain("RightMantle1", "RightMantle2")], (0, 0), rows=12)
    _sheet(coll, "PG2_LoinFront", [chain("LoinFront1", "LoinFront2")], (2.3, 1.7))
    _sheet(coll, "PG2_LoinBack", [chain("LoinBack1", "LoinBack2")], (2.5, 1.9))
    build_skeleton(coll)
    return {**counts, "bones": len(BONES)}


# ---------- the weights ----------
def _points(obj):
    import numpy as np
    n = len(obj.data.vertices)
    co = np.zeros(n * 3)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    return np.stack([co[:, 0], co[:, 2], -co[:, 1]], axis=1)


def _distances(pts, names):
    import numpy as np
    a = np.array([BONES[n][1] for n in names], dtype=np.float64)
    b = np.array([BONES[n][2] for n in names], dtype=np.float64)
    ab = b - a
    t = np.clip(np.einsum("ijk,jk->ij", pts[:, None, :] - a[None, :, :], ab) / np.maximum((ab * ab).sum(axis=1), 1e-9), 0, 1)
    return np.linalg.norm(pts[:, None, :] - (a[None] + t[..., None] * ab[None]), axis=2)


def _write_weights(obj, names, d, falloff, influences=4):
    import numpy as np
    near = d.min(axis=1, keepdims=True)
    w = np.exp(-((d - near) / falloff) ** 2 * 2.2)
    w[d >= 1e5] = 0
    order = np.argsort(-w, axis=1)[:, :influences]
    keep = np.zeros_like(w)
    rows = np.arange(len(w))[:, None]
    keep[rows, order] = w[rows, order]
    keep[keep < 0.02] = 0
    keep /= np.maximum(keep.sum(axis=1, keepdims=True), 1e-9)
    obj.vertex_groups.clear()
    for j, nm in enumerate(names):
        idx = np.nonzero(keep[:, j])[0]
        if len(idx):
            vg = obj.vertex_groups.new(name=nm)
            for i in idx.tolist():
                vg.add([i], float(keep[i, j]), "REPLACE")
    _attach(obj)
    return {"verts": len(w), "max influences": int((keep > 0).sum(axis=1).max()), "unweighted": int((keep.sum(axis=1) < 0.99).sum())}


def _attach(obj):
    for mod in list(obj.modifiers):
        if mod.type == "ARMATURE":
            obj.modifiers.remove(mod)
    md = obj.modifiers.new("Armature", "ARMATURE")
    md.object = bpy.data.objects[RIG]
    obj.parent = bpy.data.objects[RIG]


def bind_rigid(obj, bone):
    obj.vertex_groups.clear()
    vg = obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    _attach(obj)


def bind_skin(falloff=1.9):
    """Weights by each vertex's distance to the bones, with each bone allowed only its own region: a titan of stone bends at
    his joints, and his fingers must not drag his thigh."""
    import numpy as np
    skin = bpy.data.objects["PG2_Skin"]
    pts = _points(skin)
    names = [n for n in BONES if n != "Root"]
    d = _distances(pts, names)
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    ax = np.abs(x)
    allow = {
        "Hips": (y > 14.2) & (ax < 8.0),
        "Spine": (y > 18.6) & (y < 27.2) & (ax < 8.8),
        "Chest": (y > 22.8) & (ax < 11.8),
        "Neck": (y > 29.8) & (y < 36) & (ax < 4.6),
        "Head": (y > 31.8),
        "Jaw": (y < 34.4) & (y > 31.2) & (z < -0.5) & (ax < 3),
    }
    limits = {"Clavicle": (ax > 1.4) & (y > 26.4), "UpperArm": (ax > 5.0) & (y > 21), "Forearm": ax > 12.4, "Hand": ax > 17.8, "Fingers": ax > 19.8,
              "Thumb": (ax > 18.6) & (ax < 20.7) & (z < -1.9), "Thigh": y < 20.5, "Shin": y < 12.4, "Foot": y < 4.2, "Toe": (y < 1.9) & (z < -2.6)}
    never = ("Eyes", "Beard1", "Beard2", "Axe", "LoinFront1", "LoinFront2", "LoinBack1", "LoinBack2", "MantleMid1", "MantleMid2")
    for j, nm in enumerate(names):
        if nm in never or "Mantle" in nm or nm in ("RightFingers", "RightThumb"):     # the fist stays closed on the haft
            d[:, j] = 1e6
            continue
        if nm.startswith("Left"):
            d[x > 0.1, j] = 1e6
        elif nm.startswith("Right"):
            d[x < -0.1, j] = 1e6
        base = nm.replace("Left", "").replace("Right", "")
        if nm in allow:
            d[~allow[nm], j] = 1e6
        elif base in limits:
            d[~limits[base], j] = 1e6
    # across the shoulder the chest hands over to the arm gradually: a hard line there tears when the arm goes up
    hand_over = np.clip((ax - 6.0) / 4.6, 0.0, 1.0)
    hand_over = hand_over * hand_over * (3 - 2 * hand_over)
    shoulder = y > 21
    for j, nm in enumerate(names):
        base = nm.replace("Left", "").replace("Right", "")
        if nm == "Chest":
            d[shoulder, j] += (hand_over * 7.0)[shoulder]
        elif base == "UpperArm":
            d[shoulder, j] += ((1 - hand_over) * 7.0)[shoulder]
    # the head's mass doesn't follow the neck past the jaw line; horns are all head
    head = names.index("Head")
    d[y > 37.0, :] = 1e6
    d[y > 37.0, head] = 0.0
    result = _write_weights(skin, names, d, falloff)
    T.smooth_weights(skin, factor=0.5, repeat=8)
    return result


def _bind_chain(obj, bones, falloff=2.2):
    pts = _points(obj)
    d = _distances(pts, bones)
    return _write_weights(obj, bones, d, falloff)


def bind():
    out = {"skin": bind_skin()}
    out["beard"] = _bind_chain(bpy.data.objects["PG2_Beard"], ["Jaw", "Beard1", "Beard2"], 1.2)
    out["mantle"] = _bind_chain(bpy.data.objects["PG2_Mantle"], ["LeftMantle1", "LeftMantle2", "MantleMid1", "MantleMid2", "RightMantle1", "RightMantle2"])
    out["loin front"] = _bind_chain(bpy.data.objects["PG2_LoinFront"], ["LoinFront1", "LoinFront2"])
    out["loin back"] = _bind_chain(bpy.data.objects["PG2_LoinBack"], ["LoinBack1", "LoinBack2"])
    bind_rigid(bpy.data.objects["PG2_Eyes"], "Eyes")
    bind_rigid(bpy.data.objects["PG2_Pupils"], "Eyes")
    bind_rigid(bpy.data.objects["PG2_Lids"], "Head")
    bind_rigid(bpy.data.objects["PG2_Axe"], "Axe")
    return out


# ---------- posing: rotations in Roblox axes, each on top of its parent, as the game's joints work ----------
def _euler(m):
    e = m.to_euler("ZYX")            # R = Rx Ry Rz, as CFrame.Angles(x, y, z)
    return (math.degrees(e.x), math.degrees(e.y), math.degrees(e.z))


def _mat(angles):
    return (Matrix.Rotation(math.radians(angles[0]), 3, "X") @ Matrix.Rotation(math.radians(angles[1]), 3, "Y") @ Matrix.Rotation(math.radians(angles[2]), 3, "Z"))


def fk(pose, shift=(0, 0, 0)):
    """Where each bone is under a pose: {bone: (world rotation, world head)}, Roblox axes."""
    out = {}

    def walk(name, parent):
        pa, head, tail = BONES[name]
        r = _mat(pose.get(name, (0, 0, 0)))
        if parent is None:
            world, at = r, V(head)
        else:
            pr, pp = out[parent]
            world = pr @ r
            at = pp + pr @ (V(head) - V(BONES[parent][1]))
            if name == "Hips":
                at = at + V(shift)
        out[name] = (world, at)
        for child, (p2, _, _) in BONES.items():
            if p2 == name:
                walk(child, name)

    walk("Root", None)
    return out


def _tail(state, name):
    r, at = state[name]
    return at + r @ (V(BONES[name][2]) - V(BONES[name][1]))


def set_pose(pose, shift=(0, 0, 0)):
    arm = bpy.data.objects[RIG]
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        rest = pb.bone.matrix_local.to_3x3()
        t = T.rb_rot(*pose.get(pb.name, (0, 0, 0)))
        pb.rotation_quaternion = (rest.inverted() @ t @ rest).to_quaternion()
        pb.location = (0, 0, 0)
    hips = arm.pose.bones["Hips"]
    C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    hips.location = hips.bone.matrix_local.to_3x3().inverted() @ (C @ V(shift))
    bpy.context.view_layer.update()


def _aim(pose, shift, bone, want):
    """Turns a bone, under its parent, so its length points along `want`."""
    state = fk(pose, shift)
    parent = BONES[bone][0]
    pr = state[parent][0]
    rest = (V(BONES[bone][2]) - V(BONES[bone][1])).normalized()
    pose[bone] = _euler(pr.inverted() @ rest.rotation_difference(V(want).normalized()).to_matrix())


def _frame(a, b):
    a = V(a).normalized()
    c = a.cross(V(b)).normalized()
    return Matrix((a, c.cross(a), c)).transposed()


def _orient(pose, shift, bone, rest_pair, want_pair):
    """Turns a bone so two rest directions become two wanted ones."""
    pr = fk(pose, shift)[BONES[bone][0]][0]
    pose[bone] = _euler(pr.inverted() @ _frame(*want_pair) @ _frame(*rest_pair).inverted())


def solve_arm(pose, shift, tag, wrist, pole):
    """Two-bone IK: the shoulder stays, the wrist reaches `wrist`, the elbow bends toward `pole`."""
    s = fk(pose, shift)[tag + "UpperArm"][1]
    l1 = (V(BONES[tag + "UpperArm"][2]) - V(BONES[tag + "UpperArm"][1])).length
    l2 = (V(BONES[tag + "Forearm"][2]) - V(BONES[tag + "Forearm"][1])).length
    to = V(wrist) - s
    dist = max(min(to.length, (l1 + l2) * 0.995), abs(l1 - l2) + 0.05)
    d = to.normalized()
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    side = (V(pole) - d * V(pole).dot(d)).normalized()
    elbow = s + d * a + side * h
    _aim(pose, shift, tag + "UpperArm", elbow - s)
    _aim(pose, shift, tag + "Forearm", (s + d * dist) - elbow)


_L_THIGH = (V(BONES["LeftThigh"][2]) - V(BONES["LeftThigh"][1]))
_L_SHIN = (V(BONES["LeftShin"][2]) - V(BONES["LeftShin"][1]))
_L1, _L2 = _L_THIGH.length, _L_SHIN.length
_THIGH_REST = math.atan2(-_L_THIGH.z, -_L_THIGH.y)
_SHIN_REST = math.atan2(-_L_SHIN.z, -_L_SHIN.y)
_ANKLE_Y = BONES["LeftShin"][2][1]
_ANKLE_Z = BONES["LeftShin"][2][2]


def leg(pose, shift, tag, ankle_y, ankle_z, roll=0.0, toe=0.0):
    """A leg solved in its side plane: pitch only, the knee forward, the sole flat unless it's rolling onto the toe."""
    state = fk(pose, shift)
    hr, hp = state["Hips"]
    hip = hp + hr @ (V(BONES[tag + "Thigh"][1]) - V(BONES["Hips"][1]))
    dy, dz = ankle_y - hip.y, ankle_z - hip.z
    dist = max(min(math.hypot(dy, dz), (_L1 + _L2) * 0.998), abs(_L1 - _L2) + 0.05)
    aim = math.atan2(-dz, -dy)
    alpha = math.acos(max(-1, min(1, (_L1 * _L1 + dist * dist - _L2 * _L2) / (2 * _L1 * dist))))
    beta = math.acos(max(-1, min(1, (_L2 * _L2 + dist * dist - _L1 * _L1) / (2 * _L2 * dist))))
    thigh_world, shin_world = aim + alpha, aim - beta
    hip_pitch = pose.get("Hips", (0, 0, 0))[0]
    thigh = math.degrees(thigh_world - _THIGH_REST) - hip_pitch
    shin = math.degrees((shin_world - _SHIN_REST) - (thigh_world - _THIGH_REST))
    pose[tag + "Thigh"] = (thigh, 0, 0)
    pose[tag + "Shin"] = (shin, 0, 0)
    pose[tag + "Foot"] = (-(hip_pitch + thigh + shin) - roll, 0, 0)
    pose[tag + "Toe"] = (toe, 0, 0)


# ---------- the pose he stands in ----------
STAND_FIST = (9.0, 27.6, -5.6)                          # his right fist before the shoulder, the haft resting on it
# the haft from the fist up to the top of the shoulder (the deltoid's crown, 34.5 up), where it rests
HAFT_STAND = (V((8.4, 34.5, 0.2)) - V(STAND_FIST)).normalized()
EDGE_STAND = V((0, HAFT_STAND.z, -HAFT_STAND.y)).normalized()   # the blade's edge up and forward
_LEFT_D = (V(BONES["LeftFingers"][2]) - V(BONES["LeftHand"][1])).normalized()
_LEFT_N = _palm_bind(-1)
_LEFT_ACROSS = _LEFT_D.cross(_LEFT_N).normalized()      # the fingers curl about this; the thumb lies on its negative side
_TWIST_SHARE = (0.5, 0.3)                               # of an arm's whole twist: the shoulder's, the elbow's; the wrist has the rest
_TWIST_MOST = 240                                       # an arm never carries more than this


def _twist(rot, axis):
    """How far a rotation turns about an axis, in degrees, from -180 to 180."""
    q = rot.to_quaternion()
    deg = math.degrees(2 * math.atan2(V((q.x, q.y, q.z)).dot(axis), q.w))
    return (deg + 180) % 360 - 180


def spread_twist(pose, shift, near=None):
    """With no twist bones, a joint asked to turn about the limb pinches its skin like a candy wrapper. So each arm's twist is shared
    along it: the bones roll about their own lengths, and the elbow, the wrist and the hand (and the axe in it) stay exactly where they are.
    `near` is each arm's twist in the pose before: the same twist can be written 360 degrees apart, and taking the other one spins the arm
    between the two poses. Returns each arm's twist, for the next pose."""
    wholes = {}
    for tag in ("Left", "Right"):
        upper_axis = (V(BONES[tag + "UpperArm"][2]) - V(BONES[tag + "UpperArm"][1])).normalized()
        fore_axis = (V(BONES[tag + "Forearm"][2]) - V(BONES[tag + "Forearm"][1])).normalized()
        for _ in range(3):      # the two axes are nearly, not quite, the same: a few passes settle it
            state = fk(pose, shift)
            collar, upper, fore, hand = (state[tag + n][0] for n in ("Clavicle", "UpperArm", "Forearm", "Hand"))
            shoulder = _twist(collar.inverted() @ upper, upper_axis)
            elbow = _twist(upper.inverted() @ fore, upper_axis)
            wrist = _twist(fore.inverted() @ hand, fore_axis)
            whole = (shoulder + elbow + wrist + 180) % 360 - 180
            ref = (near or {}).get(tag, 0)
            whole = min((c for c in (whole - 360, whole, whole + 360) if abs(c) <= _TWIST_MOST), key=lambda c: abs(c - ref))
            wholes[tag] = whole
            roll_upper = whole * _TWIST_SHARE[0] - shoulder
            roll_fore = roll_upper + whole * _TWIST_SHARE[1] - elbow
            upper2 = upper @ Matrix.Rotation(math.radians(roll_upper), 3, upper_axis)
            fore2 = fore @ Matrix.Rotation(math.radians(roll_fore), 3, fore_axis)
            pose[tag + "UpperArm"] = _euler(collar.inverted() @ upper2)
            pose[tag + "Forearm"] = _euler(upper2.inverted() @ fore2)
            pose[tag + "Hand"] = _euler(fore2.inverted() @ hand)
    return wholes


def hold_axe(pose, shift, fist, haft, edge, pole=(0.7, -1, 0.6)):
    """The hand takes the axe where it's wanted, the grip unchanged, and the arm reaches for the hand."""
    turn = _frame(haft, edge) @ _frame(_HAFT_BIND, _EDGE_BIND).inverted()
    wrist = V(fist) - turn @ (V(FIST) - V(BONES["RightHand"][1]))
    solve_arm(pose, shift, "Right", wrist, pole)
    pr = fk(pose, shift)["RightForearm"][0]
    pose["RightHand"] = _euler(pr.inverted() @ turn)
    pose.pop("Axe", None)


def free_arm(pose, shift, wrist=(-12.6, 18.6, -1.3), pole=(-0.5, 0, 1), fingers=(0.12, -1, -0.12), palm=(1, 0, 0.1)):
    """The left arm, free: it hangs by his side, the palm turned to the thigh, a little bent."""
    solve_arm(pose, shift, "Left", wrist, pole)
    _orient(pose, shift, "LeftHand", (_LEFT_D, _LEFT_N), (fingers, palm))


STAGGER = {"Left": -1.5, "Right": 1.3}     # how he stands: braced, the left foot forward, so a blow never has to slide his feet


def standing(extra=None, shift=(0, -0.7, 0), legs=True, axe=True, free=True):
    pose = dict(extra or {})
    if legs:
        for tag in ("Left", "Right"):
            leg(pose, shift, tag, _ANKLE_Y, _ANKLE_Z + STAGGER[tag])
    if axe:
        hold_axe(pose, shift, STAND_FIST, HAFT_STAND, EDGE_STAND)
    if free:
        free_arm(pose, shift)
    if axe and free:
        spread_twist(pose, shift)
    return pose


_ARMS = {}


def stand_arms():
    """The arms as he stands, each on top of its parent: held like this they move with his chest, as arms do."""
    if not _ARMS:
        pose = standing()
        for tag in ("Left", "Right"):
            for part in ("UpperArm", "Forearm", "Hand"):
                _ARMS[tag + part] = pose[tag + part]
    return dict(_ARMS)


# ---------- the gaits: a heavy walk, and the run he chases at ----------
# Each is measured: stride = the distance a planted ankle travels back under him, per share of the cycle it stays planted.
GAITS = {
    "walk": {"reach": 5.2, "stance": 0.60, "lift": 2.4, "hips": -1.25, "bob": 0.5, "lean": -3, "yaw": 6, "roll": 2.5, "speed": 12},
    "run": {"reach": 6.6, "stance": 0.40, "lift": 4.2, "hips": -1.7, "bob": 0.9, "lean": -11, "yaw": 9, "roll": 3, "speed": 28},
}


def stride_of(g):
    return 2 * g["reach"] / g["stance"]


def _ease(u):
    return u * u * (3 - 2 * u)


def _foot(g, p):
    """A foot at share p of its cycle (0: it comes down, ahead of the body): ankle height, ankle z and the sole's roll."""
    p %= 1.0
    s = g["stance"]
    if p < s:
        u = p / s
        z = _ANKLE_Z - g["reach"] + 2 * g["reach"] * u
        heel = max(0.0, (u - 0.72) / 0.28)                  # the heel lifts late, rolling onto the ball
        slap = max(0.0, 1 - u / 0.16)                       # it lands on the heel, toes up, and the sole slaps flat
        return _ANKLE_Y + 1.1 * heel * heel + 0.3 * slap * slap, z, 24 * heel * heel - 14 * slap * slap, 24 * heel * heel
    u = (p - s) / (1 - s)
    z = _ANKLE_Z + g["reach"] - 2 * g["reach"] * _ease(u)
    y = _ANKLE_Y + 1.1 * (1 - u) ** 2 + g["lift"] * math.sin(math.pi * u) ** 1.2 + 0.3 * max(0.0, (u - 0.75) / 0.25) ** 2
    roll = 24 * (1 - u) ** 2 + 26 * math.sin(math.pi * u) - 14 * max(0.0, (u - 0.75) / 0.25)
    return y, z, roll, 24 * (1 - u) ** 2


def add_turn(pose, bone, pitch):
    """A swing on top of a bone's pose, about the guardian's own side axis."""
    pose[bone] = _euler(_mat((pitch, 0, 0)) @ _mat(pose.get(bone, (0, 0, 0))))


def gait_pose(name, phase):
    """One moment of a gait, and the hips' shift. Left foot comes down at phase 0, the right at 0.5."""
    g = GAITS[name]
    a = 2 * math.pi * phase
    mid = g["stance"] / 2
    bob = -g["bob"] * math.cos(4 * math.pi * (phase - mid + 0.25)) if name == "run" else -g["bob"] * math.cos(4 * math.pi * phase)
    shift = (0.35 * math.sin(a + 0.6), g["hips"] + bob, 0)
    sway = math.sin(a + 0.4)
    pose = {
        "Hips": (g["lean"], g["yaw"] * sway, g["roll"] * math.sin(a)),
        "Spine": (g["lean"] * 0.5, -g["yaw"] * 0.7 * sway, -g["roll"] * 0.5 * math.sin(a)),
        "Chest": (g["lean"] * 0.5, -g["yaw"] * 0.9 * sway, -g["roll"] * 0.5 * math.sin(a)),
        "Neck": (-g["lean"] * 0.8, g["yaw"] * 0.4 * sway, 0),
        "Head": (-g["lean"] * 0.8 - 1.5 * math.cos(2 * a), g["yaw"] * 0.3 * sway, 0),
    }
    for tag, off in (("Left", 0.0), ("Right", 0.5)):
        y, z, roll, toe = _foot(g, phase + off)
        leg(pose, shift, tag, y, z, roll, toe)
    pose.update(stand_arms())
    # the free arm swings against its leg, its forearm lagging; the axe rocks on the shoulder; the hangings trail
    swing, bend = (17, 10) if name == "walk" else (34, 34)
    add_turn(pose, "LeftUpperArm", -swing * math.cos(a) + (2 if name == "walk" else 8))
    add_turn(pose, "LeftForearm", bend * (0.65 - 0.35 * math.cos(a - 0.7)))
    add_turn(pose, "RightUpperArm", 3 * math.sin(a))
    speed = 1.0 if name == "walk" else 1.9
    for chain, lag in (("Mantle", 0.0),):
        for tag in ("Left", "Right"):
            pose[tag + "Mantle1"] = ((8 + 5 * math.sin(a - 0.8)) * speed - 5, 0, 0)
            pose[tag + "Mantle2"] = ((5 + 5 * math.sin(a - 1.5)) * speed - 3, 0, 0)
        pose["MantleMid1"] = ((8 + 5 * math.sin(2 * a - 0.8)) * speed - 5, 0, 0)
        pose["MantleMid2"] = ((5 + 5 * math.sin(2 * a - 1.5)) * speed - 3, 0, 0)
    pose["LoinFront1"] = (-6 * speed * max(0, math.sin(a)) - 5 * speed, 0, 0)
    pose["LoinFront2"] = (-3 * speed, 0, 0)
    pose["LoinBack1"] = (5 * speed * math.sin(a - 0.6) + 6 * speed, 0, 0)
    pose["LoinBack2"] = (3 * speed * math.sin(a - 1.2) + 3 * speed, 0, 0)
    pose["Jaw"] = (0, 0, 0)
    pose["Beard1"] = (3 * math.sin(2 * a - 1.0), 0, 0)
    pose["Beard2"] = (3 * math.sin(2 * a - 1.6), 0, 0)
    return pose, shift


def measure_gait(name, frames=48):
    """How well the feet hold: while planted, how far an ankle strays from a straight line along the ground, at the gait's own speed."""
    g = GAITS[name]
    stride = stride_of(g)
    slip, height = [], []
    for tag, off in (("Left", 0.0), ("Right", 0.5)):
        planted = []
        for f in range(frames):
            phase = f / frames
            if (phase + off) % 1.0 >= g["stance"] * 0.72:
                continue
            pose, shift = gait_pose(name, phase)
            state = fk(pose, shift)
            ankle = state[tag + "Foot"][1]
            planted.append((ankle.z - stride * phase, ankle.y, (phase + off) % 1.0))
        planted.sort(key=lambda r: r[2])
        zs = [p[0] for p in planted]
        slip.append(max(zs) - min(zs))
        height.append(max(p[1] for p in planted) - min(p[1] for p in planted))
    return {"stride": round(stride, 2), "slip": [round(s, 3) for s in slip], "height drift": [round(h, 3) for h in height]}


# ---------- the axe cleave, keyed by where the fist and the blade are ----------
FREE_ARM = {0.28: (14, 18), 0.68: (46, 34), 0.90: (-30, 12), 1.20: (-18, 16)}
HANGINGS = {
    0.28: {"MantleMid1": (6, 0, 0), "LeftMantle1": (6, 0, 0), "RightMantle1": (4, 0, 0), "LoinFront1": (4, 0, 0)},
    0.68: {"MantleMid1": (-8, 0, 0), "MantleMid2": (-6, 0, 0), "LeftMantle1": (-6, 0, 0), "RightMantle1": (-6, 0, 0), "LoinFront1": (-8, 0, 0), "LoinBack1": (6, 0, 0), "Beard1": (6, 0, 0), "Beard2": (6, 0, 0)},
    0.90: {"MantleMid1": (26, 0, 0), "MantleMid2": (18, 0, 0), "LeftMantle1": (22, 0, 0), "LeftMantle2": (14, 0, 0), "RightMantle1": (24, 0, 0), "RightMantle2": (16, 0, 0),
           "LoinFront1": (18, 0, 0), "LoinFront2": (10, 0, 0), "LoinBack1": (-4, 0, 0), "Beard1": (-14, 0, 0), "Beard2": (-10, 0, 0), "Jaw": (-10, 0, 0)},
    1.20: {"MantleMid1": (-6, 0, 0), "MantleMid2": (6, 0, 0), "LeftMantle1": (-4, 0, 0), "RightMantle1": (-4, 0, 0), "LoinFront1": (4, 0, 0), "Beard1": (6, 0, 0), "Beard2": (4, 0, 0), "Jaw": (-4, 0, 0)},
}


def cleave_keys():
    """(seconds, ease into this key, body, hips' shift, fist, haft, edge). The fight's wind-up is 0.9 s: the blow lands there."""
    stand_body = {}
    high = (10.5, 42.0, 3.0)
    keys = [
        (0.0, "smooth", stand_body, (0, -0.7, 0), STAND_FIST, HAFT_STAND, EDGE_STAND),
        # the gather: he sinks, the chest winding back and the axe coming off the shoulder
        (0.28, "out", {"Hips": (0, 8, 0), "Spine": (2, 6, 0), "Chest": (4, 8, 0)}, (0, -1.5, 0), (11.0, 32.0, -4.4), (0.05, 0.9, 0.42), (0, 0.42, -0.9)),
        # the top: risen, arched back, the axe high behind him
        (0.68, "smooth", {"Hips": (6, 12, 0), "Spine": (5, 8, 0), "Chest": (9, 12, 0), "Neck": (-4, -6, 0), "Head": (-3, -6, 0)}, (0, -0.5, 0), high, (0.0, 0.5, 0.86), (0, 0.86, -0.5)),
        # the blow: the whole body drives it down, the blade in the ground before him
        (0.90, "in", {"Hips": (-16, -8, 0), "Spine": (-14, -8, 0), "Chest": (-18, -10, 0), "Neck": (12, 6, 0), "Head": (10, 6, 0)}, (0, -4.3, -1.0), (5.6, 10.6, -8.6), (-0.02, -0.35, -0.94), (0, -0.94, 0.35)),
        # it bites and he holds there
        (1.20, "out", {"Hips": (-14, -7, 0), "Spine": (-12, -7, 0), "Chest": (-15, -9, 0), "Neck": (10, 5, 0), "Head": (8, 5, 0)}, (0, -4.0, -0.9), (5.6, 10.9, -8.6), (-0.02, -0.35, -0.94), (0, -0.94, 0.35)),
        # and wrenches it back to the shoulder
        (1.95, "smooth", stand_body, (0, -0.7, 0), STAND_FIST, HAFT_STAND, EDGE_STAND),
    ]
    out = []
    for at, ease, body, shift, fist, haft, edge in keys:
        pose = dict(body)
        for tag in ("Left", "Right"):
            leg(pose, shift, tag, _ANKLE_Y, _ANKLE_Z + STAGGER[tag])
        arms = stand_arms()
        for part in ("LeftUpperArm", "LeftForearm", "LeftHand"):
            pose[part] = arms[part]
        lift, bend = FREE_ARM.get(at, (0, 0))       # thrown forward for balance as the axe goes up, and back as it comes down
        add_turn(pose, "LeftUpperArm", lift)
        add_turn(pose, "LeftForearm", bend)
        hold_axe(pose, shift, fist, V(haft).normalized(), V(edge).normalized())
        # overlap: the hangings and beard lag the body, thrown forward by the blow, then settling
        pose.update(HANGINGS.get(at, {}))
        out.append((at, ease, pose, shift))
    return out


def cleave_pose(t, keys):
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if t <= b[0]:
            u = (t - a[0]) / (b[0] - a[0])
            u = {"in": u * u * u, "out": 1 - (1 - u) ** 3, "smooth": _ease(u)}[b[1]]
            names = set(a[2]) | set(b[2])
            pose = {}
            for n in names:           # true rotation blending: a big turn takes the short way round
                qa = _mat(a[2].get(n, (0, 0, 0))).to_quaternion()
                qb = _mat(b[2].get(n, (0, 0, 0))).to_quaternion()
                pose[n] = _euler(qa.slerp(qb, u).to_matrix())
            shift = tuple(a[3][k] + (b[3][k] - a[3][k]) * u for k in range(3))
            for tag in ("Left", "Right"):      # solved every frame, not only at the keys: the feet never leave their spots
                leg(pose, shift, tag, _ANKLE_Y, _ANKLE_Z + STAGGER[tag])
            return pose, shift
    return keys[-1][2], keys[-1][3]


# ---------- review ----------
VIEWS = {"front": (0, 6), "three": (-38, 8), "left": (-90, 4), "right": (90, 4), "back": (180, 6), "top": (0, 88)}


def _hide_rig():
    bpy.data.objects[RIG].hide_render = True


def review_form(path, pose=None, shift=None, views=("front", "three", "left", "back", "right", "top"), size=460, columns=3, distance=112, centre=(0, 22, 0)):
    scene, cam = T._review_scene(size)
    _hide_rig()
    if pose is None:
        pose = standing()
        shift = (0, -0.7, 0)
    set_pose(pose, shift or (0, 0, 0))
    tmp = path + ".tile.png"
    tiles = [T._shot(scene, cam, *VIEWS[v], distance, W.rb(*centre), size, tmp) for v in views]
    T._sheet(tiles, columns, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)
    return path


def stress_poses():
    """What the fight asks of him. Each returns (name, pose, shift, yaw)."""
    out = [("bound as modelled", {}, (0, 0, 0), -30), ("standing", standing(), (0, -0.7, 0), -35)]
    # both arms overhead (the sky-splitter's top)
    s = (0, -0.4, 0)
    p = standing({"Chest": (6, 0, 0), "RightClavicle": (0, 0, 28), "LeftClavicle": (0, 0, -28)}, s, axe=False, free=False)
    solve_arm(p, s, "Right", (6.5, 46.0, 0.5), (1, 0, 0.3))
    solve_arm(p, s, "Left", (-6.5, 46.0, 0.5), (-1, 0, 0.3))
    out.append(("arms overhead", p, s, -30))
    # a deep squat, the titan's crouch before a leap
    s = (0, -6.5, 0)
    p = {"Hips": (-18, 0, 0), "Spine": (6, 0, 0), "Chest": (10, 0, 0), "Neck": (6, 0, 0)}
    for tag in ("Left", "Right"):
        leg(p, s, tag, _ANKLE_Y, _ANKLE_Z)
    hold_axe(p, s, (9.0, 21.4, -7.0), HAFT_STAND, EDGE_STAND)
    free_arm(p, s, wrist=(-9.6, 13.4, -7.6), pole=(-0.6, 0.4, 1), fingers=(0.1, -0.8, -0.6), palm=(0.8, -0.2, 0.5))
    out.append(("deep crouch", p, s, -55))
    # down on the right knee, weakened
    s = (0, -7.6, -0.5)
    p = {"Hips": (-6, 0, 0), "Spine": (-8, 0, 0), "Chest": (-12, 0, 0), "Neck": (-6, 0, 0), "Head": (-10, 0, 0)}
    leg(p, s, "Left", _ANKLE_Y, -6.5)
    leg(p, s, "Right", 2.0, 8.8)
    p["RightFoot"] = (p["RightFoot"][0] + 58, 0, 0)
    p["RightToe"] = (-48, 0, 0)
    hold_axe(p, s, (11.4, 12.2, -5.4), (0.0, 0.25, -0.97), (0, -0.97, -0.25), pole=(1, 0.2, 0.6))
    free_arm(p, s, wrist=(-5.6, 11.6, -7.6), pole=(-1, 0.3, 0.6), fingers=(0.1, -1, -0.15), palm=(0.1, -0.1, 1))      # the hand braced on the raised knee
    out.append(("on one knee", p, s, -60))
    # twisted, and the jaw open in a roar
    s = (0, -0.9, 0)
    p = standing({"Hips": (0, -14, 0), "Spine": (0, 18, 0), "Chest": (8, 22, 0), "Neck": (10, 14, 0), "Head": (12, 12, 0), "Jaw": (-16, 0, 0)}, s)
    out.append(("turned, roaring", p, s, -20))
    return out


def stress(path, size=460, columns=3, distance=112):
    scene, cam = T._review_scene(size)
    _hide_rig()
    tmp = path + ".tile.png"
    tiles = []
    for name, pose, shift, yaw in stress_poses():
        set_pose(pose, shift)
        tiles.append(T._shot(scene, cam, yaw, 6, distance, W.rb(0, 21, 0), size, tmp))
    set_pose({})
    T._sheet(tiles, columns, path, size)
    if os.path.exists(tmp):
        os.remove(tmp)
    return path


def _floor():
    scene = bpy.context.scene
    floor = bpy.data.objects.get("PG2Floor")
    if floor:
        return floor
    mats = []
    for name, rgb in (("A", (0.46, 0.48, 0.52)), ("B", (0.4, 0.42, 0.46))):
        m = bpy.data.materials.new("PG2Floor" + name)
        m.diffuse_color = (*rgb, 1)
        mats.append(m)
    me = bpy.data.meshes.new("PG2Floor")
    vs, fs, idx = [], [], []
    for k in range(-40, 41):
        y0, y1 = k * 8.0, (k + 1) * 8.0
        b = len(vs)
        vs += [(-90, y0, 0), (90, y0, 0), (90, y1, 0), (-90, y1, 0)]
        fs.append((b, b + 1, b + 2, b + 3))
        idx.append(k % 2)
    me.from_pydata(vs, [], fs)
    for m in mats:
        me.materials.append(m)
    for p, i in zip(me.polygons, idx):
        p.material_index = i
    floor = bpy.data.objects.new("PG2Floor", me)
    scene.collection.objects.link(floor)
    return floor


def _camera(cam, yaw, pitch, distance, centre):
    y, p = math.radians(yaw), math.radians(pitch)
    c = W.rb(*centre)
    cam.location = c + V((math.sin(y) * math.cos(p), math.cos(y) * math.cos(p), math.sin(p))) * distance
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()


def render_clip(folder, size=620, fps=30):
    """One video in order: the walk, then the run, each from the side and a three-quarter view, then the axe cleave."""
    scene, cam = T._review_scene(size)
    _hide_rig()
    floor = _floor()
    os.makedirs(folder, exist_ok=True)
    n = 0
    shots = [("walk", -90, 2), ("walk", -40, 1), ("run", -90, 3), ("run", -40, 2)]
    info = {}
    for name, yaw, cycles in shots:
        g = GAITS[name]
        stride = stride_of(g)
        seconds = stride / g["speed"]
        frames = max(8, round(seconds * fps))
        info[name] = {"stride": round(stride, 2), "seconds a stride": round(seconds, 2), "frames": frames}
        for f in range(frames * cycles):
            phase = (f / frames) % 1.0
            pose, shift = gait_pose(name, phase)
            set_pose(pose, shift)
            floor.location.y = (-stride * f / frames) % 16.0
            _camera(cam, yaw, 5, 118, (0, 22, 0))
            bpy.context.view_layer.update()
            scene.render.filepath = os.path.join(folder, "f%04d.png" % n)
            bpy.ops.render.render(write_still=True)
            n += 1
    floor.location.y = 0
    keys = cleave_keys()
    for yaw in (-55, -125):
        for f in range(int(keys[-1][0] * fps) + 12):
            pose, shift = cleave_pose(f / fps, keys)
            set_pose(pose, shift)
            _camera(cam, yaw, 5, 118, (0, 20, -3))
            bpy.context.view_layer.update()
            scene.render.filepath = os.path.join(folder, "f%04d.png" % n)
            bpy.ops.render.render(write_still=True)
            n += 1
    set_pose({})
    info["total frames"] = n
    return info


def report():
    data = {}
    for name in GAITS:
        data[name] = measure_gait(name)
    return json.dumps(data)


# ---------- the finished character ----------
PIECES = {"Skin": 19500, "Beard": 2000, "Axe": 4000, "Loin": 3000, "Mantle": 12000, "Mane": 4000}
OUT = G.OUT_DIR
TAU = 2 * math.pi


def _piece_axe(coll, M):
    """The axe as modelled for the clay, split by material for the bake, and its void-lit edge."""
    import egg_hi as Hm
    F, H, E = V(FIST), _HAFT_BIND, _EDGE_BIND
    S = H.cross(E).normalized()
    head = F + H * 12.2
    pt = lambda a, b: head + H * a + E * b
    neck = [(-1.5, 0.55), (0.0, 0.5), (1.5, 0.55), (1.75, 1.3), (2.4, 2.3), (3.6, 3.3), (5.4, 4.0)]
    edge = [(5.4 * (1 - 2 * i / 20), 4.0 + 2.5 * (1 - (1 - 2 * i / 20) ** 2) ** 0.8) for i in range(21)]
    outline = neck + edge[1:-1] + [(-5.4, 4.0), (-3.6, 3.3), (-2.4, 2.3), (-1.75, 1.3)]
    thick = lambda b: 0.5 * max(0.12, 1 - max(0.0, b - 2.2) / 3.8)
    blade, haft, bronze, glow = Hm.Hi(), Hm.Hi(), Hm.Hi(), Hm.Hi()
    centre = pt(0, 2.6)
    front = [blade.v(pt(a, b) + S * thick(b)) for a, b in outline]
    back = [blade.v(pt(a, b) - S * thick(b)) for a, b in outline]
    cf, cb = blade.v(centre + S * 0.5), blade.v(centre - S * 0.5)
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        blade.facing([cf, front[i], front[j]], [(0.5, 0.5), (0, 0), (1, 0)], tuple(S))
        blade.facing([cb, back[j], back[i]], [(0.5, 0.5), (0, 0), (1, 0)], tuple(-S))
        a0, b0 = outline[i]
        a1, b1 = outline[j]
        blade.facing([front[i], back[i], back[j], front[j]], [(0, 0), (0, 1), (1, 1), (1, 0)], tuple((pt((a0 + a1) / 2, (b0 + b1) / 2) - centre).normalized()))
    pommel, top = F - H * 3.4, F + H * 15.5
    Hm.htube(haft, [pommel, F, top], lambda q: 0.55, sides=10, per=2, uv_scale=1.0, tip=False, wobble=0.0)
    import pangu as O
    for at in (pommel + H * 0.3, F + H * 3.2, head - H * 2.4, top - H * 0.3):
        _band(bronze, at, H, 0.62, 0.18)
    G.sphere(bronze, pommel - H * 0.25, 0.8, nu=12, nv=8)
    Hm.htube(bronze, [head - H * 2.0, head + H * 2.2], lambda q: 1.0, sides=10, per=2, uv_scale=1.0, tip=False, wobble=0.0)
    G.cone(blade, head - E * 0.7, head - E * 3.2 + H * 0.4, 0.55, sides=8)       # a spike behind the socket
    Hm.htube(glow, [pt(a, b + 0.06) for a, b in edge], lambda q: 0.16, sides=6, per=2, uv_scale=1.0, tip=False, wobble=0.0)
    return blade.object("PG2_AxeBlade", coll, [M["blade"]], smooth=False), haft.object("PG2_AxeHaft", coll, [M["haft"]]), bronze.object("PG2_AxeBronze", coll, [M["bronze"]]), glow


def _ring(hi, pts, radius, sides=8):
    """A closed hoop: its ends meet once and are welded by _clean, so it never lies over itself."""
    import egg_hi as Hm
    Hm.htube(hi, list(pts) + [pts[0]], lambda q: radius, sides=sides, per=1, uv_scale=2.0, tip=False, wobble=0.0)


def _band(hi, centre, axis, radius, thick):
    n, s, u = G.frame(axis)
    _ring(hi, [V(centre) + (s * math.cos(TAU * i / 24) + u * math.sin(TAU * i / 24)) * radius for i in range(24)], thick, sides=6)


def _fit_uv(obj):
    """A Neon piece wears no map, but Roblox wants its UVs inside the square."""
    uv = obj.data.uv_layers.active
    if not uv:
        return
    us = [d.uv.x for d in uv.data]
    vs = [d.uv.y for d in uv.data]
    su, sv = max(max(us) - min(us), 1e-6), max(max(vs) - min(vs), 1e-6)
    u0, v0 = min(us), min(vs)
    for d in uv.data:
        d.uv = ((d.uv.x - u0) / su, (d.uv.y - v0) / sv)


def _taiji(disc, c, r):
    """The disc of yin and yang on his belt: the split he made."""
    rings, wedges = 10, 48

    def yang(x, y):
        up, down = math.hypot(x, y - r / 2) < r / 2, math.hypot(x, y + r / 2) < r / 2
        return down or (x > 0 and not up)

    pts = [[disc.v(c + V((r * k / rings * math.cos(TAU * i / wedges), r * k / rings * math.sin(TAU * i / wedges), -0.1))) for i in range(wedges)] for k in range(rings + 1)]
    for k in range(rings):
        for i in range(wedges):
            j = (i + 1) % wedges
            rr, am = r * (k + 0.5) / rings, TAU * (i + 0.5) / wedges
            disc.facing([pts[k][i], pts[k + 1][i], pts[k + 1][j], pts[k][j]], [(0, 0), (1, 0), (1, 1), (0, 1)], (0, 0, -1), 0 if yang(rr * math.cos(am), rr * math.sin(am)) else 1)
    for dy, mat in ((r / 2, 0), (-r / 2, 1)):
        G.sphere(disc, c + V((0, dy, -0.16)), 0.26, nu=10, nv=6, radii=(0.26, 0.26, 0.07), mat=mat)


def build_final(voxel=0.11):
    """The high-detail pieces, ready to bake: {piece: [objects]}, and the glow pieces {name: object}."""
    import random
    import egg_hi as Hm
    import pangu as O
    T.clear()
    coll = bpy.data.collections.new("PanguV2")
    bpy.context.scene.collection.children.link(coll)
    M = O.materials()
    groups = [g for g in _groups() if not (g[0] == 0.1)]      # the horns are their own pieces here, in horn
    skin = G.blob("PG2_SkinHi", coll, M["stone"], _rough_lobes(groups), voxel=voxel, smooth=0.75, rough=0.0, chisel="PanguV2Chisel")
    T._settle(skin, groups, cut=_sockets)
    G.soften(skin, 6)
    T._settle(skin, groups, passes=2, cut=_sockets)
    # hewn stone: broad planes broken into facets, without moving his forms
    tex = bpy.data.textures.get("PanguV2Hewn") or bpy.data.textures.new("PanguV2Hewn", "VORONOI")
    tex.noise_scale = 1.4
    Hm.apply_modifiers(skin, [("DISPLACE", {"texture": tex, "strength": 0.11, "mid_level": 0.5, "texture_coords": "GLOBAL"})])
    for p in skin.data.polygons:
        p.use_smooth = True

    eyes, pupils, lids, horns, bronze, disc, void = (Hm.Hi() for _ in range(7))
    for side in (-1, 1):
        normal = V((side * 0.4, 0.04, -0.92)).normalized()
        seat = G.surface_along(skin, V((side * 1.08, 35.3, -2.5)), normal)
        G.eye(eyes, pupils, lids, seat, normal, (-side * 0.6, 0, -1), 0.6, 0.2, tilt=0.42, bulge=0.08, lid=0.72, droop=0.75, lower=0.2, slit=0.22, pupil_height=0.72)
        base = V((side * 2.0, 37.1, -0.6))
        horn = [V((side * 0.9, 36.0, -0.6)), base, base + V((side * 1.8, 1.6, 0.6)), base + V((side * 3.4, 3.8, 1.8)), base + V((side * 3.6, 6.2, 1.2)), base + V((side * 2.8, 7.6, -0.4))]     # rooted inside the skull
        Hm.htube(horns, horn, lambda q: 1.34 * (1 - 0.9 * max(0.0, q - 0.14) / 0.86), sides=12, per=6, uv_scale=1.0, tip=True, wobble=0.0)
        _band(bronze, base + V((side * 0.9, 0.8, 0.3)), V((side * 1.8, 1.6, 0.6)), 1.22, 0.2)
        tag = "Left" if side < 0 else "Right"
        s, e, w = (V(BONES[tag + n][1]) for n in ("UpperArm", "Forearm", "Hand"))
        _band(bronze, s.lerp(e, 0.66), e - s, 2.28, 0.26)
        for q in (0.3, 0.62):
            _band(bronze, e.lerp(w, q), w - e, 2.0 - 0.45 * q if side > 0 else 2.17 - 1.02 * q, 0.26)     # the left forearm narrows to its wrist
        kn, an = V(BONES[tag + "Shin"][1]), V(BONES[tag + "Foot"][1])
        for q in (0.58, 0.82):
            _band(bronze, kn.lerp(an, q), an - kn, 1.9 - 0.45 * q, 0.24)
    # the belt, sitting on him, and the disc at its front
    ring = []
    for i in range(44):
        a = TAU * i / 44
        ring.append(G.surface_along(skin, V((0, 20.2, 0.1)), V((math.sin(a), 0, -math.cos(a))), reach=9.0))
    _ring(bronze, ring, 0.6)
    c = G.surface_along(skin, V((0, 19.9, 0.1)), V((0, 0, -1)), reach=9.0) + V((0, 0, -0.34))
    _ring(bronze, [c + V((1.75 * math.cos(TAU * i / 32), 1.75 * math.sin(TAU * i / 32), 0)) for i in range(32)], 0.24)
    _taiji(disc, c, 1.72)

    # void light in the fissures: where he is cracked, and the crack splitting his brow
    regions = [((0, 26.5, -1.5), (5.5, 3.5, 2.5), 7, 12, 0.1, 5), ((0, 26.5, 2.5), (5.5, 3.5, 1.5), 4, 12, 0.1, 6), ((0, 20.5, 0), (4.5, 2.2, 3.0), 4, 8, 0.09, 3)]
    for side in (-1, 1):
        tag = "Left" if side < 0 else "Right"
        s, e, w = (V(BONES[tag + n][1]) for n in ("UpperArm", "Forearm", "Hand"))
        h, kn, an = (V(BONES[tag + n][1]) for n in ("Thigh", "Shin", "Foot"))
        for a, b, spread, count, steps, seed in ((s, e, (1.8, 1.8, 1.8), 3, 8, 7), (e, w, (1.2, 1.2, 1.2), 3, 7, 21), (h, kn, (1.8, 2.5, 1.8), 3, 8, 41), (kn, an, (1.3, 2.0, 1.3), 2, 7, 51)):
            regions.append((tuple(a.lerp(b, 0.5)), spread, count, steps, 0.08, seed + side))
    for centre, spread, count, steps, radius, seed in regions:
        G.veins(void, skin, O.vein_starts(random.Random(seed), centre, spread, count), random.Random(seed + 1), steps=steps, radius=radius)
    Hm.htube(void, [V((0, 37.7, -2.1)), V((0.12, 37.0, -2.6)), V((-0.08, 36.4, -2.95))], lambda q: 0.11 * (1 - 0.5 * q), sides=6, per=4, uv_scale=1.0, tip=True, wobble=0.0)
    mouth = [V((-0.85, 33.02, -3.14)), V((0, 33.22, -3.52)), V((0.85, 33.02, -3.14))]             # a stern seam of chaos: the corners down
    Hm.htube(void, mouth, lambda q: 0.055, sides=6, per=4, uv_scale=1.0, tip=True, wobble=0.0)

    # the beard: a stone mass, moustache and three braids bound in bronze
    beard_groups = _beard_groups()
    beard = G.blob("PG2_BeardHi", coll, M["horn"], _rough_lobes(beard_groups), voxel=0.08, smooth=0.75, rough=0.0, chisel="PanguV2Chisel2")
    T._settle(beard, beard_groups)
    G.soften(beard, 4)
    for p in beard.data.polygons:
        p.use_smooth = True
    whisker, beard_bronze = Hm.Hi(), Hm.Hi()
    for side in (-1, 1):
        Hm.htube(whisker, [(side * 0.2, 33.95, -3.3), (side * 0.9, 33.55, -3.25), (side * 1.4, 32.85, -3.0), (side * 1.55, 32.05, -2.65)], lambda q: 0.32 * (1 - 0.65 * q), sides=8, per=4, uv_scale=1.0, tip=True, wobble=0.3, seed=7 + side)
    for xx in (-0.75, 0.0, 0.75):
        _band(beard_bronze, V((xx, 29.45, -3.25)), V((0, -1, -0.1)), 0.52, 0.12)

    # hangings of torn, chaos-dark cloth
    loin = Hm.Hi()
    for z, sign, bone_z in ((-4.0, -1, -4.2), (4.2, 1, 4.5)):
        for x, length, width in ((0, 9.5, 2.3), (-2.1, 7.4, 1.6), (2.1, 7.7, 1.6)):
            Hm.leaf(loin, (x, 18.1, z), (x * 0.03, -1, sign * 0.08), (0, 0, sign), length, width, mat=0, fold=0.08, curl=0.04, twist=x * 0.04, steps=12, across=3, shape=0.85)
    loin_o = loin.object("PG2_LoinHi", coll, [M["cloth"]])
    Hm.solidify(loin_o, 0.14)
    loin_o["keep"] = True

    # the mantle and the mane: chaos drifting from him like smoke
    rnd = random.Random(11)
    mantle, mane = Hm.Hi(), Hm.Hi()
    for layer, (y0, z0, count, lengths, width) in enumerate(((30.6, 3.1, 22, (9.0, 15.0), (0.42, 0.72)), (28.0, 4.5, 20, (7.0, 13.0), (0.36, 0.62)))):
        for k in range(count):
            q = k / (count - 1)
            x = -8.0 + 16.0 * q + rnd.uniform(-0.3, 0.3)
            b = V((x, y0 - 1.3 * abs(x) / 8.0 + rnd.uniform(-1.6, 1.6), z0 + 0.3 * abs(x) / 8.0))
            G.wisp(mantle, b, V((x * 0.03, -1, 0.22 + rnd.uniform(0, 0.1))), V((x * 0.05, 0.1, 1)), rnd.uniform(*lengths), rnd.uniform(*width), rnd, sides=7)
    for k in range(22):
        a = math.pi * (0.1 + 0.8 * k / 21)
        b = V((2.2 * math.cos(a), 35.9 + 1.6 * math.sin(a), 1.2 + 0.4 * math.sin(a)))
        G.wisp(mane, b, V((math.cos(a) * 0.4, 0.5, 1)), V((0, 1, 0.2)), rnd.uniform(3.5, 6.0), rnd.uniform(0.35, 0.5), rnd, sides=6)

    blade, haft, axe_bronze, axe_glow = _piece_axe(coll, M)

    def kept(hi, name, mat):
        o = hi.object(name, coll, mat if isinstance(mat, list) else [mat])
        o["keep"] = True
        return o

    pieces = {
        "Skin": [skin, kept(lids, "PG2_Lids", M["stone"]), kept(horns, "PG2_Horns", M["horn"]), kept(bronze, "PG2_Bronze", M["bronze"]), kept(disc, "PG2_Disc", [M["yang"], M["yin"]])],
        "Beard": [beard, kept(whisker, "PG2_Whisker", M["horn"]), kept(beard_bronze, "PG2_BeardBronze", M["bronze"])],
        "Axe": [blade, haft, axe_bronze],
        "Loin": [loin_o],
        "Mantle": [kept(mantle, "PG2_MantleHi", M["void"])],
        "Mane": [kept(mane, "PG2_ManeHi", M["void"])],
    }
    for o in pieces["Axe"]:
        o["keep"] = True
    glows = {
        "Eyes": (eyes.object("PG2_Eyes", coll, [K.glow_material(EYE_HEX)], smooth=True), EYE_HEX),
        "Pupils": (pupils.object("PG2_Pupils", coll, [K.glow_material(PUPIL_HEX)], smooth=True), PUPIL_HEX),
        "BodyVoid": (void.object("PG2_BodyVoid", coll, [K.glow_material(VOID_HEX)], smooth=True), VOID_HEX),
        "AxeVoid": (axe_glow.object("PG2_AxeVoid", coll, [K.glow_material(VOID_HEX)], smooth=True), VOID_HEX),
    }
    for o, _ in glows.values():
        _clean(o, triangulate=True)
        _fit_uv(o)
    build_skeleton(coll)
    return pieces, glows


EYE_HEX, PUPIL_HEX, VOID_HEX = "9a64ff", "06020c", "8c28ff"


def make_lows(pieces):
    import egg_bake as B
    coll = bpy.data.collections["PanguV2"]
    lows = {}
    for name, hi in pieces.items():
        low = B.make_low("PanguV2_" + name, hi, coll, PIECES[name])
        low.name = "PanguV2_" + name
        _clean(low)
        lows[name] = low
    return lows


BAKES = {"Skin": dict(size=2048, small=1024, ray=0.3, extrusion=0.14), "Beard": dict(size=512, small=256, ray=0.2, extrusion=0.08), "Axe": dict(size=1024, small=512, ray=0.12, extrusion=0.05),
         "Loin": dict(size=512, small=256, ray=0.08, extrusion=0.03), "Mantle": dict(size=1024, small=256, ray=0.08, extrusion=0.03), "Mane": dict(size=512, small=256, ray=0.08, extrusion=0.03)}


def bake_piece(name, hi, low):
    import egg_bake as B
    bpy.context.scene.cycles.device = "GPU"
    saved = B.EGG_DIR
    B.EGG_DIR = OUT
    try:
        B.bake("PanguV2_" + name, hi, low, samples=12, **BAKES[name])
    finally:
        B.EGG_DIR = saved


def bind_rigid_kept(obj, bone, also):
    """A piece riding one bone whole. The hundredth of `also` on one vertex did not save the bone from the importer (it dropped Axe
    and Eyes anyway): Placements/PanguSkinned puts them back with AddBones."""
    bind_rigid(obj, bone)
    vg = obj.vertex_groups.new(name=also)
    vg.add([0], 0.01, "REPLACE")
    obj.vertex_groups[bone].add([0], 0.99, "REPLACE")


def bind_like_skin(obj, skin):
    """Each vertex takes the weights of the nearest skin vertex: what grows from the skin moves with it."""
    from mathutils.kdtree import KDTree
    tree = KDTree(len(skin.data.vertices))
    for v in skin.data.vertices:
        tree.insert(v.co, v.index)
    tree.balance()
    names = {g.index: g.name for g in skin.vertex_groups}
    obj.vertex_groups.clear()
    made = {}
    for v in obj.data.vertices:
        _, i, _ = tree.find(v.co)
        for g in skin.data.vertices[i].groups:
            nm = names[g.group]
            if nm not in made:
                made[nm] = obj.vertex_groups.new(name=nm)
            made[nm].add([v.index], g.weight, "REPLACE")
    _attach(obj)


def rig_all():
    O = bpy.data.objects
    skin = O["PanguV2_Skin"]
    skin.name = "PG2_Skin"
    out = {"skin": bind_skin()}
    out["beard"] = _bind_chain(O["PanguV2_Beard"], ["Jaw", "Beard1", "Beard2"], 1.2)
    out["mantle"] = _bind_chain(O["PanguV2_Mantle"], ["LeftMantle1", "LeftMantle2", "MantleMid1", "MantleMid2", "RightMantle1", "RightMantle2"])
    out["loin"] = _bind_chain(O["PanguV2_Loin"], ["LoinFront1", "LoinFront2", "LoinBack1", "LoinBack2"])
    bind_rigid(O["PanguV2_Mane"], "Head")
    bind_like_skin(O["PG2_BodyVoid"], O["PG2_Skin"])
    bind_rigid_kept(O["PG2_Eyes"], "Eyes", "Head")
    bind_rigid_kept(O["PG2_Pupils"], "Eyes", "Head")
    bind_rigid_kept(O["PanguV2_Axe"], "Axe", "RightHand")
    bind_rigid_kept(O["PG2_AxeVoid"], "Axe", "RightHand")
    game = set(GAME_NAMES) | {RIG}
    for o in O:
        if o.type == "MESH" and o.name not in game:
            o.hide_render = True
            o.hide_viewport = True
    return out


GAME_NAMES = {"PG2_Skin": "Skin", "PanguV2_Beard": "Beard", "PanguV2_Axe": "Axe", "PanguV2_Loin": "Loin", "PanguV2_Mantle": "Mantle", "PanguV2_Mane": "Mane",
              "PG2_Eyes": "Eyes", "PG2_Pupils": "Pupils", "PG2_BodyVoid": "BodyVoid", "PG2_AxeVoid": "AxeVoid"}


def tally():
    return {GAME_NAMES[o.name]: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.name in GAME_NAMES}


def export():
    """assets/guardians/PanguV2.fbx: every game piece, skinned, and the skeleton, bound as modelled. The maps go in with it."""
    O = bpy.data.objects
    set_pose({})
    arm = O[RIG]
    arm.hide_render = False
    bpy.ops.object.select_all(action="DESELECT")
    for src, name in GAME_NAMES.items():
        o = O[src]
        o.hide_viewport = False
        o.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    for src, name in list(GAME_NAMES.items()):
        O[src].name = name
    path = os.path.join(OUT, "PanguV2.fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH", "ARMATURE"}, axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_UNITS", path_mode="COPY", embed_textures=True,
                             mesh_smooth_type="FACE", add_leaf_bones=False, use_armature_deform_only=True, bake_anim=False, primary_bone_axis="Y", secondary_bone_axis="X")
    return path, os.path.getsize(path) // 1024


# ---------- his moves, solved here and played by the game (PanguClips.lua) ----------
def _haft_grip(pose, shift, along):
    """The left hand joins the right on the haft, `along` studs toward the blade from the right fist."""
    state = fk(pose, shift)
    r, at = state["Axe"]
    H = r @ _HAFT_BIND
    point = at + H * along
    shoulder = state["LeftUpperArm"][1]
    reach = (point - shoulder).normalized()
    palm = reach.cross(H).normalized()              # the thumb on the blade's side, the haft against the palm
    wrist = point - reach * 2.0 - palm * 1.4
    solve_arm(pose, shift, "Left", wrist, (-1, -0.4, 0.5))
    _orient(pose, shift, "LeftHand", (_LEFT_D, _LEFT_N), (reach, palm))
    pose["LeftFingers"] = _euler(Matrix.Rotation(math.radians(62), 3, _LEFT_ACROSS))     # closed round the haft


def _key(at, ease="smooth", body=None, shift=(0, -0.7, 0), axe=None, left=None, hang=None, legs=None):
    """One key pose: `axe` (fist, haft, edge) or the arm as he stands; `left`: {"lift", "bend"}, {"grip": along} or {"wrist", ...}."""
    pose = dict(body or {})
    planted = legs is None
    if planted:
        for tag in ("Left", "Right"):
            leg(pose, shift, tag, _ANKLE_Y, _ANKLE_Z + STAGGER[tag])
    else:
        pose.update(legs)
    arms = stand_arms()
    for part in ("LeftUpperArm", "LeftForearm", "LeftHand", "RightUpperArm", "RightForearm", "RightHand"):
        pose[part] = arms[part]
    if axe:
        hold_axe(pose, shift, axe[0], V(axe[1]).normalized(), V(axe[2]).normalized())
    left = left or {}
    if "wrist" in left:
        free_arm(pose, shift, **left)
    elif "grip" in left:
        _haft_grip(pose, shift, left["grip"])
    else:
        add_turn(pose, "LeftUpperArm", left.get("lift", 0))
        add_turn(pose, "LeftForearm", left.get("bend", 0))
    pose.update(hang or {})
    spread_twist(pose, shift)
    return (at, ease, pose, shift, planted)


REST_AXE = (STAND_FIST, HAFT_STAND, EDGE_STAND)
_HANG_BLOW = {"MantleMid1": (26, 0, 0), "MantleMid2": (18, 0, 0), "LeftMantle1": (22, 0, 0), "LeftMantle2": (14, 0, 0), "RightMantle1": (24, 0, 0), "RightMantle2": (16, 0, 0),
              "LoinFront1": (18, 0, 0), "LoinFront2": (10, 0, 0), "LoinBack1": (-4, 0, 0), "Beard1": (-14, 0, 0), "Beard2": (-10, 0, 0), "Jaw": (-10, 0, 0)}


def clips():
    """Every timed move. The blow of each lands at the fight's wind-up time, when the server's hit or wave fires."""
    down = ((-0.02, -0.35, -0.94), (0, -0.94, 0.35))
    bent = {"Hips": (-16, -8, 0), "Spine": (-14, -8, 0), "Chest": (-18, -10, 0), "Neck": (12, 6, 0), "Head": (10, 6, 0)}
    bent_h = {"Hips": (-14, -7, 0), "Spine": (-12, -7, 0), "Chest": (-15, -9, 0), "Neck": (10, 5, 0), "Head": (8, 5, 0)}
    sway = HANGINGS
    out = {}
    out["AxeCleave"] = [
        _key(0.0),
        _key(0.28, "out", {"Hips": (0, 8, 0), "Spine": (2, 6, 0), "Chest": (4, 8, 0)}, (0, -1.5, 0), ((11.0, 32.0, -4.4), (0.05, 0.9, 0.42), (0, 0.42, -0.9)), {"lift": 14, "bend": 18}, sway[0.28]),
        _key(0.68, "smooth", {"Hips": (6, 12, 0), "Spine": (5, 8, 0), "Chest": (9, 12, 0), "Neck": (-4, -6, 0), "Head": (-3, -6, 0)}, (0, -0.5, 0), ((10.5, 42.0, 3.0), (0.0, 0.5, 0.86), (0, 0.86, -0.5)), {"lift": 46, "bend": 34}, sway[0.68]),
        _key(0.90, "in", bent, (0, -4.3, -1.0), ((5.6, 10.6, -8.6), *down), {"lift": -30, "bend": 12}, _HANG_BLOW),
        _key(1.20, "out", bent_h, (0, -4.0, -0.9), ((5.6, 10.9, -8.6), *down), {"lift": -18, "bend": 16}, sway[1.20]),
        _key(1.95),
    ]
    # the sky-splitter: both hands on the axe, raised high, driven straight down before him
    centre = {"Hips": (-16, 8, 0), "Spine": (-14, 8, 0), "Chest": (-18, 14, 0), "Neck": (12, -8, 0), "Head": (10, -8, 0)}
    out["SkySplitter"] = [
        _key(0.0),
        _key(0.42, "out", {"Chest": (-8, 6, 0), "Head": (-6, 0, 0)}, (0, -1.7, 0), ((7.0, 26.4, -7.4), (0, 0.8, 0.6), (0, 0.6, -0.8)), {"grip": 5.0}, sway[0.28]),
        _key(0.98, "smooth", {"Hips": (5, 0, 0), "Spine": (5, 0, 0), "Chest": (10, 0, 0), "Neck": (-5, 0, 0), "Head": (-3, 0, 0)}, (0, -0.2, 0), ((3.2, 45.0, 1.8), (0, 0.35, 0.94), (0, 0.94, -0.35)), {"grip": 5.0}, sway[0.68]),
        _key(1.20, "in", centre, (0, -4.5, -1.0), ((3.4, 10.6, -8.8), *down), {"grip": 4.8}, _HANG_BLOW),
        _key(1.55, "out", centre, (0, -4.2, -0.9), ((3.4, 11.0, -8.8), *down), {"grip": 4.8}, sway[1.20]),
        _key(2.20),
    ]
    # the chaos nova: he gathers the void to his chest, then thrusts his palm up, holding up the sky
    hold = {"wrist": (-10.0, 47.5, -1.0), "pole": (-1, 0, 0.3), "fingers": (0.1, 0.1, -1), "palm": (0, 1, 0)}
    aside = ((12.5, 25.5, -3.0), (0.05, 0.85, 0.5), (0, 0.5, -0.85))
    out["ChaosNova"] = [
        _key(0.0),
        _key(0.49, "out", {"Spine": (-6, 0, 0), "Chest": (-14, 0, 0), "Neck": (-4, 0, 0), "Head": (-8, 0, 0)}, (0, -1.8, 0), None, {"wrist": (-4.0, 26.0, -7.2), "pole": (-1, -0.6, 0.4), "fingers": (0.4, 0.2, -0.9), "palm": (0.5, 0.8, 0.3)}, sway[0.28]),
        _key(1.25, "smooth", {"Chest": (8, -6, 0), "Head": (10, 0, 0)}, (0, -0.8, 0), aside, {"wrist": (-9.0, 41.0, -3.0), "pole": (-1, -0.2, 0.5), "fingers": (0.05, 0.6, -0.8), "palm": (0, 0.8, 0.6)}, sway[0.68]),
        _key(1.45, "out", {"Spine": (6, 0, 0), "Chest": (15, -8, 0), "Neck": (8, 0, 0), "Head": (12, 0, 0), "Jaw": (-16, 0, 0)}, (0, -1.2, 0), aside, hold, _HANG_BLOW),
        _key(2.05, "smooth", {"Spine": (5, 0, 0), "Chest": (13, -7, 0), "Neck": (7, 0, 0), "Head": (10, 0, 0), "Jaw": (-12, 0, 0)}, (0, -1.1, 0), aside, hold, sway[1.20]),
        _key(2.70),
    ]
    # the titan's leap: a deep crouch, up with the knees drawn and the axe high; the land takes it from there
    tuck = {"LeftThigh": (62, 0, 0), "LeftShin": (-78, 0, 0), "LeftFoot": (16, 0, 0), "RightThigh": (30, 0, 0), "RightShin": (-96, 0, 0), "RightFoot": (40, 0, 0)}
    reach = {"LeftThigh": (30, 0, 0), "LeftShin": (-30, 0, 0), "LeftFoot": (0, 0, 0), "RightThigh": (14, 0, 0), "RightShin": (-34, 0, 0), "RightFoot": (20, 0, 0)}
    high = ((10.0, 41.0, 2.0), (0, 0.6, 0.8), (0, 0.8, -0.6))
    out["TitanLeap"] = [
        _key(0.0),
        _key(0.60, "out", {"Hips": (-20, 0, 0), "Spine": (6, 0, 0), "Chest": (8, 0, 0), "Neck": (6, 0, 0), "Head": (6, 0, 0)}, (0, -5.5, 0), ((9.0, 21.0, -7.0), HAFT_STAND, EDGE_STAND), {"lift": -14, "bend": 26}, sway[0.28]),
        _key(0.84, "in", {"Hips": (-6, 0, 0), "Chest": (4, 0, 0)}, (0, -0.4, 0), high, {"lift": 30, "bend": 18}, sway[0.68]),
        _key(1.25, "smooth", {"Hips": (-14, 0, 0), "Chest": (6, 0, 0), "Head": (8, 0, 0)}, (0, 0, 0), high, {"lift": 44, "bend": 30}, sway[0.68], tuck),
        _key(2.10, "smooth", {"Hips": (-4, 0, 0), "Chest": (2, 0, 0), "Head": (2, 0, 0)}, (0, 0, 0), high, {"lift": 26, "bend": 20}, {"MantleMid1": (-20, 0, 0), "LeftMantle1": (-16, 0, 0), "RightMantle1": (-16, 0, 0), "LoinFront1": (-10, 0, 0), "LoinBack1": (12, 0, 0)}, reach),
        _key(2.40, "smooth", {"Hips": (-4, 0, 0)}, (0, 0, 0), high, {"lift": 20, "bend": 16}, None, reach),
    ]
    out["Land"] = [
        _key(0.0, "smooth", {"Hips": (-4, 0, 0)}, (0, -0.4, 0), high, {"lift": 20, "bend": 16}),
        _key(0.12, "out", {"Hips": (-22, 0, 0), "Spine": (8, 0, 0), "Chest": (6, 0, 0), "Neck": (6, 0, 0), "Head": (6, 0, 0)}, (0, -6.2, -0.6), ((9.0, 21.0, -7.0), HAFT_STAND, EDGE_STAND), {"lift": -24, "bend": 18}, _HANG_BLOW),
        _key(0.40, "smooth", {"Hips": (-10, 0, 0), "Chest": (2, 0, 0)}, (0, -2.6, -0.3), None, {"lift": -8, "bend": 10}, sway[1.20]),
        _key(0.90),
    ]
    # each arm's twist runs on from key to key through a move, and from the leap into its landing
    for names in (("AxeCleave",), ("SkySplitter",), ("ChaosNova",), ("TitanLeap", "Land")):
        near = None
        for name in names:
            for key in out[name]:
                near = spread_twist(key[2], key[3], near)
    return out


def clip_pose(t, keys):
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if t <= b[0]:
            u = (t - a[0]) / (b[0] - a[0])
            u = {"in": u * u * u, "out": 1 - (1 - u) ** 3, "smooth": _ease(u)}[b[1]]
            pose = {}
            for n in set(a[2]) | set(b[2]):
                qa = _mat(a[2].get(n, (0, 0, 0))).to_quaternion()
                qb = _mat(b[2].get(n, (0, 0, 0))).to_quaternion()
                pose[n] = _euler(qa.slerp(qb, u).to_matrix())
            shift = tuple(a[3][k] + (b[3][k] - a[3][k]) * u for k in range(3))
            if a[4] and b[4]:          # both on the ground: the feet never leave their spots
                for tag in ("Left", "Right"):
                    leg(pose, shift, tag, _ANKLE_Y, _ANKLE_Z + STAGGER[tag])
            return pose, shift
    return keys[-1][2], keys[-1][3]


def _near(angle, ref):
    return angle + 360 * round((ref - angle) / 360)


def _continuous(e, ref):
    """The same rotation written closest to `ref`: angle tables must run smoothly, or the game's springs flail."""
    a = tuple(_near(e[k], ref[k]) for k in range(3))
    b0 = (e[0] + 180, 180 - e[1], e[2] + 180)
    b = tuple(_near(b0[k], ref[k]) for k in range(3))
    dist = lambda v: sum(abs(v[k] - ref[k]) for k in range(3))
    return a if dist(a) <= dist(b) else b


def _joints():
    return [n for n in BONES if n not in ("Root", "Eyes", "RightFingers", "RightThumb")]


def _full(pose):
    return {n: pose.get(n, (0, 0, 0)) for n in _joints()}


def state_poses():
    """The poses he holds in each state, every joint, as angles written close to how he stands."""
    s0 = (0, -0.7, 0)
    stand = standing()
    states = {"Guardian": (dict(stand, Chest=(2, 0, 0)), s0), "Returning": (dict(stand, Head=(-4, 0, 0)), s0)}
    sleep = dict(stand)
    sleep.update({"Chest": (-5, 0, 0), "Neck": (-6, 0, 0), "Head": (-20, 0, 0)})
    states["Dormant"] = (sleep, s0)
    states["Resting"] = (sleep, s0)
    s = (0, -7.6, -0.5)
    p = {"Hips": (-6, 0, 0), "Spine": (-8, 0, 0), "Chest": (-12, 0, 0), "Neck": (-6, 0, 0), "Head": (-10, 0, 0)}
    leg(p, s, "Left", _ANKLE_Y, -6.5)
    leg(p, s, "Right", 2.0, 8.8)
    p["RightFoot"] = (p["RightFoot"][0] + 58, 0, 0)
    p["RightToe"] = (-48, 0, 0)
    hold_axe(p, s, (11.4, 12.2, -5.4), (0.0, 0.25, -0.97), (0, -0.97, -0.25), pole=(1, 0.2, 0.6))
    # the left hand laid over the raised knee: the palm on the kneecap, the fingers down its front
    fingers, palm = V((0.05, -0.75, -0.66)), V((0, -0.66, 0.75))
    knee = fk(p, s)["LeftShin"][1]
    free_arm(p, s, wrist=tuple(knee - palm * 2.9 - fingers * 1.7), pole=(-1, 0.3, 0.6), fingers=tuple(fingers), palm=tuple(palm))
    spread_twist(p, s)
    states["Weakened"] = (p, s)
    s = (0, -1.5, 0)
    p = {"Hips": (-4, 0, 0), "Spine": (2, 0, 0), "Chest": (6, 0, 0), "Neck": (-2, 0, 0), "Head": (4, 0, 0), "Jaw": (-6, 0, 0)}
    for tag in ("Left", "Right"):
        leg(p, s, tag, _ANKLE_Y, _ANKLE_Z + STAGGER[tag])
    hold_axe(p, s, (11.0, 31.5, -6.5), (0.02, 0.86, 0.5), (0, 0.5, -0.86))
    free_arm(p, s, wrist=(-13.0, 21.0, -5.0), pole=(-0.6, -0.1, 1), fingers=(0.1, -0.5, -0.85), palm=(0.9, 0.3, -0.2))
    spread_twist(p, s)
    states["Enraged"] = (p, s)
    return stand, s0, states


def _vals(pose, shift, base):
    """{joint: [pitch, yaw, roll]} written close to `base`; the hips carry the shift as lift and slide."""
    out = {}
    for n in _joints():
        e = _continuous(pose.get(n, (0, 0, 0)), base.get(n, (0, 0, 0))[:3])
        out[n] = list(e)
    out["Hips"] = out["Hips"] + [shift[1], shift[2]]
    return out


def bake_clips(fps=30):
    stand, s0, _ = state_poses()
    base = {n: stand.get(n, (0, 0, 0)) for n in _joints()}
    out, worst = {}, {}
    for name, keys in clips().items():
        frames, prev = [], base
        length = keys[-1][0]
        for f in range(int(length * fps) + 1):
            pose, shift = clip_pose(min(f / fps, length), keys)
            v = _vals(pose, shift, prev)
            for n in _joints():
                d = max(abs(v[n][k] - prev[n][k]) for k in range(3))
                if f and d > worst.get(name, (0, ""))[0]:
                    worst[name] = (round(d, 1), n, f)
            prev = {n: tuple(v[n][:3]) for n in _joints()}
            frames.append(v)
        out[name] = frames
    return out, worst


def anchors():
    """Where things truly are at each blow, for the effects."""
    out = {}
    cl = clips()
    for name, at in (("AxeCleave", 0.90), ("SkySplitter", 1.20)):
        pose, shift = clip_pose(at, cl[name])
        r, a = fk(pose, shift)["Axe"]
        # the lowest point of the edge's curve, where the blade really meets the ground
        points = [a + r @ (_HAFT_BIND * (12.2 + 5.4 * i / 10) + _EDGE_BIND * (4.0 + 2.5 * (1 - (i / 10) ** 2) ** 0.8)) for i in range(-10, 11)]
        p = min(points, key=lambda q: q.y)
        out[name] = (round(p.x, 1), 0.6, round(p.z, 1))
    pose, shift = clip_pose(1.45, cl["ChaosNova"])
    p = fk(pose, shift)["LeftFingers"][1]
    out["ChaosNova"] = (round(p.x, 1), round(p.y + 0.6, 1), round(p.z, 1))
    return out


def _lua(v):
    if isinstance(v, dict):
        return "{" + ",".join(k + "=" + _lua(x) for k, x in v.items()) + "}"
    if isinstance(v, (list, tuple)):
        return "{" + ",".join(_lua(x) for x in v) + "}"
    s = "%.2f" % v
    return s.rstrip("0").rstrip(".") if "." in s else s


def write_clips(path=None):
    """src/client/Guardians/GuardianRigs/PanguClips.lua, generated: what the owner approved, as data the rig plays."""
    path = path or os.path.join(W.REPO, "src", "client", "Guardians", "GuardianRigs", "PanguClips.lua")
    stand, s0, states = state_poses()
    base = {n: stand.get(n, (0, 0, 0)) for n in _joints()}
    lines = ["-- Generated by tools/blender/guardians/pangu_v2.py (write_clips): do not edit by hand. Angles in degrees, [pitch, yaw, roll];",
             "-- the hips also carry [lift, slide]. Poses and Clips are whole poses; Gaits are changes from how he stands.", "local Clips = {}",
             "Clips.Fps = 30", "Clips.Anchors = " + _lua({k: list(v) for k, v in anchors().items()}),
             "Clips.Strides = " + _lua({n: stride_of(g) for n, g in GAITS.items()}), "Clips.Stance = " + _lua({n: g["stance"] for n, g in GAITS.items()})]
    lines.append("Clips.Poses = {")
    for name, (pose, shift) in states.items():
        lines.append(name + "=" + _lua(_vals(pose, shift, base)) + ",")
    lines.append("}")
    standv = _vals(stand, s0, base)
    lines.append("Clips.Stand = " + _lua(standv))
    lines.append("Clips.Gaits = {")
    for name in GAITS:
        table = {n: [] for n in _joints()}
        prev = base
        for f in range(24):
            pose, shift = gait_pose(name, f / 24)
            v = _vals(pose, shift, prev)
            prev = {n: tuple(v[n][:3]) for n in _joints()}
            for n in _joints():
                d = [v[n][k] - standv[n][k] for k in range(len(v[n]))]
                table[n].append(d)
        keep = {n: t for n, t in table.items() if any(abs(x) > 0.3 for row in t for x in row)}
        lines.append(name + "=" + _lua(keep) + ",")
    lines.append("}")
    baked, worst = bake_clips()
    lines.append("Clips.Moves = {")
    for name, frames in baked.items():
        moved = [n for n in _joints() if any(abs(fr[n][k] - frames[0][n][k]) > 0.2 for fr in frames for k in range(3)) or abs(frames[0][n][0] - standv[n][0]) > 0.2]
        slim = [{n: fr[n] for n in moved} for fr in frames]
        lines.append(name + "=" + _lua(slim) + ",")
    lines.append("}")
    lines.append("return Clips")
    with open(path, "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")
    return {"bytes": os.path.getsize(path), "biggest step": worst, "anchors": anchors()}
