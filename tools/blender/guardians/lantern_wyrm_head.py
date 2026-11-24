"""The Lantern Wyrm's head and what rides on it (run inside Blender): a long deep dragon's head (a heavy brow with a broad eminence between
the horns, deep cheeks, a long slightly down-sloped muzzle, nostrils, short fangs), its lower jaw, two swept-back antler horns with tines,
almond eyes (an iris with a slit cut through it, so the pupil is the dark head behind it: no separate pupil piece), the lantern's stalk
and its gold cup, and two pairs of barbels. Roblox studs, the head along -Z from the neck's top at z = -22, the spine at y = 2.6.
"""
import math

import bpy
import egg_hi as Hm
import guardian_kit as G
import tiangou_v2 as T
from mathutils import Vector

import lantern_wyrm_bones as B

V = Vector
TAU = 2 * math.pi
limb = T._limb
Z0 = B.HEAD_BASE          # -22
Y = B.Y0


def _lobes_of(groups):
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


def skull_groups():
    g = []
    cr = [((0, Y + 0.35, Z0 - 2.3), (1.6, 1.4, 2.4), None),                                 # the cranium
          ((-0.95, Y + 1.0, Z0 - 3.0), (0.62, 0.36, 1.5), (0, 8, 0)), ((0.95, Y + 1.0, Z0 - 3.0), (0.62, 0.36, 1.5), (0, -8, 0)),       # the heavy brow ridges
          ((0, Y + 1.35, Z0 - 2.9), (0.7, 0.5, 1.1), None),                                  # the broad eminence between the horns
          ((-1.3, Y - 0.15, Z0 - 3.0), (0.75, 0.85, 1.4), None), ((1.3, Y - 0.15, Z0 - 3.0), (0.75, 0.85, 1.4), None),                   # the cheeks
          ((-0.5, Y + 0.12, Z0 - 8.2), (0.22, 0.2, 0.32), None), ((0.5, Y + 0.12, Z0 - 8.2), (0.22, 0.2, 0.32), None),
          ((0, Y + 0.2, Z0 - 0.9), (1.75, 1.5, 1.3), None)]                   # the nostrils' bulges
    g.append((0.45, cr + limb([(0, Y - 0.05, Z0 - 3.9), (0, Y - 0.15, Z0 - 6.0), (0, Y - 0.35, Z0 - 8.1), (0, Y - 0.6, Z0 - 8.9)],
                                [(1.1, 0.95, 1.2), (0.85, 0.76, 1.1), (0.64, 0.55, 0.9), (0.4, 0.38, 0.5)])))
    return g


def jaw_groups():
    return [(0.35, limb([(0, Y - 0.75, Z0 - 2.4), (0, Y - 0.85, Z0 - 5.0), (0, Y - 1.0, Z0 - 7.6), (0, Y - 1.05, Z0 - 8.6)],
                        [(0.9, 0.62, 1.0), (0.86, 0.55, 1.1), (0.62, 0.45, 0.85), (0.36, 0.3, 0.4)]))]


def build_skull(coll, mat, voxel=0.085):
    groups = skull_groups()
    o = G.blob("LW_Skull", coll, mat, _lobes_of(groups), voxel=voxel, smooth=0.7, rough=0.0, chisel="LWChisel")
    T._settle(o, groups, passes=3)
    G.soften(o, 4)
    T._settle(o, groups, passes=2)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def build_jaw(coll, mat, voxel=0.07):
    groups = jaw_groups()
    o = G.blob("LW_Jaw", coll, mat, _lobes_of(groups), voxel=voxel, smooth=0.7, rough=0.0, chisel="LWChisel")
    T._settle(o, groups, passes=3)
    G.soften(o, 3)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def horns():
    """Two antler horns swept back over the neck, each with a forward tine and a rear tine."""
    hi = Hm.Hi()
    for s in (-1, 1):
        beam = [(s * 0.85, Y + 1.0, Z0 - 2.4), (s * 1.25, Y + 2.1, Z0 - 0.9), (s * 1.95, Y + 3.1, Z0 + 1.3), (s * 2.8, Y + 3.7, Z0 + 3.9), (s * 3.7, Y + 3.7, Z0 + 6.4)]
        Hm.htube(hi, beam, lambda t: 0.44 * (1 - t) ** 0.8 + 0.05, sides=8, per=5, uv_scale=1.0, tip=True, wobble=0.0)
        Hm.htube(hi, [beam[1], (s * 1.5, Y + 2.9, Z0 - 1.3), (s * 1.65, Y + 3.9, Z0 - 2.1)], lambda t: 0.22 * (1 - t) ** 0.8 + 0.04, sides=6, per=4, uv_scale=1.0, tip=True, wobble=0.0)
        Hm.htube(hi, [beam[2], (s * 2.5, Y + 4.1, Z0 + 1.4), (s * 3.0, Y + 5.2, Z0 + 2.3)], lambda t: 0.22 * (1 - t) ** 0.8 + 0.04, sides=6, per=4, uv_scale=1.0, tip=True, wobble=0.0)
    return hi


def fangs(upper=True):
    hi = Hm.Hi()
    for s in (-1, 1):
        if upper:
            for z, l in ((Z0 - 7.7, 0.62), (Z0 - 5.9, 0.46)):
                G.cone(hi, (s * 0.62, Y - 0.35, z), (s * 0.6, Y - 0.35 - l, z - 0.1), 0.15, sides=6)
        else:
            for z, l in ((Z0 - 7.2, 0.5), (Z0 - 5.2, 0.4)):
                G.cone(hi, (s * 0.55, Y - 0.62, z), (s * 0.56, Y - 0.62 + l, z - 0.1), 0.13, sides=6)
    return hi


def stalk_and_cup():
    """The lantern's stalk through the Lure joints and the gold cup that holds the lamp."""
    hi = Hm.Hi()
    pts = [(0, Y + 0.85, Z0 - 2.7)] + [B.BONES["Lure1"][1], B.BONES["Lure1"][2], B.BONES["Lure2"][2], B.BONES["Lure3"][2]]
    Hm.htube(hi, pts, lambda t: 0.34 - 0.2 * t, sides=8, per=8, uv_scale=1.0, tip=False, wobble=0.0)
    lamp = V(B.LAMP)
    top = V(B.BONES["Lure3"][2])
    d = (lamp - top).normalized() if (lamp - top).length > 1e-3 else V((0, -1, 0))
    # a cup under the lamp: a short flared collar, open toward the lamp
    base = top + V((0, 0.0, -0.1))
    n, s, t = G.frame(V((0, -0.3, -1)))
    ring_a = [hi.v(base + (s * math.cos(TAU * i / 10) + t * math.sin(TAU * i / 10)) * 0.2) for i in range(10)]
    ring_b = [hi.v(base + V((0, -0.35, -0.55)) + (s * math.cos(TAU * i / 10) + t * math.sin(TAU * i / 10)) * 0.62) for i in range(10)]
    for i in range(10):
        j = (i + 1) % 10
        out = (s * math.cos(TAU * (i + .5) / 10) + t * math.sin(TAU * (i + .5) / 10))
        hi.facing([ring_a[i], ring_a[j], ring_b[j], ring_b[i]], [(i / 10, 0), ((i + 1) / 10, 0), ((i + 1) / 10, 1), (i / 10, 1)], tuple(out + V((0, 0, -0.5))))
    return hi


def barbels():
    """The long whisker-barbels and the short beard, tubes along the bones' bind line, thick at the root and fine at the tip."""
    hi = Hm.Hi()
    for tag in ("Left", "Right"):
        for chain, r0 in (("BarbelA", 0.2), ("BarbelB", 0.14)):
            names = [n for n in B.BARBELS[tag] if n.startswith(tag + chain)]
            pts = [B.BONES[names[0]][1]] + [B.BONES[n][2] for n in names]
            Hm.htube(hi, pts, lambda t, r0=r0: r0 * (1 - 0.8 * t) + 0.02, sides=5, per=3, uv_scale=0.5, tip=True, wobble=0.0)
    return hi


def eyes(skull):
    """Almond eyes: the iris (Neon, a slit cut through it), the lids (for the head). Returns (iris Hi, lids Hi)."""
    iris, pupil, lids = Hm.Hi(), Hm.Hi(), Hm.Hi()
    for side in (-1, 1):
        normal = V((side * 0.80, 0.18, -0.57)).normalized()
        near = V((side * 0.9, Y + 0.55, Z0 - 3.6))
        seat = G.surface_along(skull, near, normal, reach=5.0)
        G.eye(iris, pupil, lids, seat, normal, (-side * 0.5, -0.12, -1), 0.95, 0.54, tilt=0.35, bulge=0.15, lid=0.55, droop=0.5, lower=0.2, slit=0.2, pupil_height=0.82)
    return iris, lids


def _rb(p):
    return V((p[0], p[2], -p[1]))


def cut_slits(iris):
    """Takes the pupils' slits out of the irises: removes each iris face whose middle lies in the slit's lens (the slit is 0.2 of the iris's
    length wide and 0.82 of its height tall, as G.eye drew it)."""
    keep = []
    # find each eye's centre as the iris's apex: the iris Hi holds two eyes; split by the sign of x
    for side in (-1, 1):
        idx = [i for i, f in enumerate(iris.faces) if (sum(iris.verts[v][0] for v in f) / len(f)) * side > 0]
        pts = [_rb(iris.verts[v]) for i in idx for v in iris.faces[i]]
        c = sum(pts, V()) / len(pts)
        # the iris's frame: the normal runs out from the head; the slit's long axis runs up the iris
        keep.append((side, idx, c))
    drop = set()
    for side, idx, c in keep:
        n = V((side * 0.80, 0.18, -0.57)).normalized()
        up = V((0, 1, 0)) - n * n.y
        up.normalize()
        fw = up.cross(n)
        for i in idx:
            f = iris.faces[i]
            m = sum((_rb(iris.verts[v]) for v in f), V()) / len(f)
            d = m - c
            x, yy = abs(d.dot(fw)), d.dot(up)
            half_w, half_h = 0.95 * 0.2, 0.54 * 0.82
            if half_h > abs(yy) and x < half_w * (1 - (yy / half_h) ** 2) ** 0.7 + 0.02:
                drop.add(i)
    faces = [f for i, f in enumerate(iris.faces) if i not in drop]
    uvs = [u for i, u in enumerate(iris.uvs) if i not in drop]
    mats = [m for i, m in enumerate(iris.mats) if i not in drop]
    used = sorted({v for f in faces for v in f})
    remap = {old: new for new, old in enumerate(used)}
    iris.verts = [iris.verts[i] for i in used]
    iris.faces = [[remap[v] for v in f] for f in faces]
    iris.uvs, iris.mats = uvs, mats
    return len(drop)


def lamp():
    """The lantern's lamp: a faceted amber gem hanging in its cup (a Neon piece): a long eight-sided jewel with a girdle and two tiers of facets."""
    hi = Hm.Hi()
    c = V(B.LAMP)
    n = 8
    rings = [(-1.05, 0.0), (-0.55, 0.55), (0.0, 0.78), (0.6, 0.6), (1.1, 0.0)]
    pos, rows = {}, []
    for k, (h, r) in enumerate(rings):
        if r == 0.0:
            p = c + V((0, h * 0.9, 0))
            i = hi.v(p)
            pos[i] = p
            rows.append([i])
        else:
            off = 0.5 * (k % 2)
            row = []
            for j in range(n):
                p = c + V((r * math.cos(TAU * (j + off) / n), h * 0.9, r * math.sin(TAU * (j + off) / n)))
                i = hi.v(p)
                pos[i] = p
                row.append(i)
            rows.append(row)

    def face(ids, uv):
        mid = sum((pos[i] for i in ids), V()) / len(ids) - c
        hi.facing(ids, uv, tuple(mid))
    for a_, b_ in zip(rows, rows[1:]):
        if len(a_) == 1:
            for i in range(n):
                face([a_[0], b_[(i + 1) % n], b_[i]], [(0.5, 0), (1, 1), (0, 1)])
        elif len(b_) == 1:
            for i in range(n):
                face([a_[i], a_[(i + 1) % n], b_[0]], [(0, 0), (1, 0), (0.5, 1)])
        else:
            for i in range(n):
                j = (i + 1) % n
                face([a_[i], a_[j], b_[j], b_[i]], [(0, 0), (1, 0), (1, 1), (0, 1)])
    return hi
