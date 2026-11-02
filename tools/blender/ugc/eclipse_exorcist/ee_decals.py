"""The Eclipse Exorcist's printed motifs (run inside Blender): designed shapes, not noise.

Each motif is drawn flat (in studs, u across and v up) and projected onto the high-detail cloth along
a direction, lying a hair above it, so the bake (selected to active) carries crisp edges into the
colour map and a faint relief into the normal map. Only the high-detail source has them.

- kumo: a printed storm cloud: three to five scalloped lobes on a flat base, a spiral curl in each lobe,
  a curling tail, outlined (the outline is a darker copy of the lobes, slightly larger, beneath them).
- brush: a crimson brush stroke: a tapered ribbon along a curve, split at its dry end into bristle
  tails.
- crest: the eclipse crest: a ring, eight long petals and a dark disc in its heart.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import ee_kit as K

V = Vector
TAU = K.TAU


class Flat:
    """2D shapes (u, v in studs) with a layer each (a height step above the cloth) and a material."""

    def __init__(self):
        self.polys = []          # (points [(u, v)], layer, material index)

    def poly(self, pts, layer, mat):
        self.polys.append((pts, layer, mat))

    def disc(self, c, r, layer, mat, n=20):
        self.poly([(c[0] + r * math.cos(TAU * k / n), c[1] + r * math.sin(TAU * k / n)) for k in range(n)], layer, mat)

    def ribbon(self, path, width_fn, layer, mat):
        """A band along a 2D path; width_fn(s) (s 0..1 along it) its full width there."""
        n = len(path)
        left, right = [], []
        for k, p in enumerate(path):
            a = path[max(k - 1, 0)]
            b = path[min(k + 1, n - 1)]
            d = V((b[0] - a[0], b[1] - a[1]))
            d = d.normalized() if d.length > 1e-9 else V((1, 0))
            nrm = V((-d.y, d.x))
            w = width_fn(k / (n - 1)) / 2
            left.append((p[0] + nrm.x * w, p[1] + nrm.y * w))
            right.append((p[0] - nrm.x * w, p[1] - nrm.y * w))
        for k in range(n - 1):
            self.poly([left[k], right[k], right[k + 1], left[k + 1]], layer, mat)


def spiral(c, r0, r1, turns, start, n=28, flip=1):
    return [(c[0] + (r0 + (r1 - r0) * k / n) * math.cos(start + flip * TAU * turns * k / n),
             c[1] + (r0 + (r1 - r0) * k / n) * math.sin(start + flip * TAU * turns * k / n)) for k in range(n + 1)]


def kumo(f, size, seed, fill, line, outline, flip=1):
    """A printed storm cloud `size` studs across: lobes on a flat base, a curl in each, a tail."""
    rnd = random.Random(seed)
    lobes = 3 + seed % 3
    w = size
    centres = []
    for k in range(lobes):
        u = -w / 2 + w * (k + 0.5) / lobes
        r = w / lobes * (0.62 + 0.18 * math.sin(k * 2.1 + seed)) * (1.15 if k == lobes // 2 else 1.0)
        centres.append(((u, r * 0.55 + rnd.uniform(-0.01, 0.02)), r))
    base_h = w * 0.13
    # the outline: every lobe and the base a little larger, one step down
    o = w * 0.028
    for c, r in centres:
        f.disc(c, r + o, 0, outline)
    f.poly([(-w / 2 - o, -base_h / 2 - o), (w / 2 + o, -base_h / 2 - o), (w / 2 + o, base_h / 2 + o), (-w / 2 - o, base_h / 2 + o)], 0, outline)
    for c, r in centres:
        f.disc(c, r, 1, fill)
    f.poly([(-w / 2, -base_h / 2), (w / 2, -base_h / 2), (w / 2, base_h / 2), (-w / 2, base_h / 2)], 1, fill)
    lw = w * 0.022
    for k, (c, r) in enumerate(centres):
        f.ribbon(spiral(c, r * 0.12, r * 0.72, 1.35, rnd.uniform(0, TAU), flip=1 if k % 2 else -1), lambda s: lw * (0.4 + 0.6 * s), 2, line)
    # the tail: a curl leaving the last lobe
    (cx, cy), r = centres[-1 if flip > 0 else 0]
    sgn = 1 if flip > 0 else -1
    tail = [(cx + sgn * (r * 0.9 + w * 0.3 * k / 16) + sgn * w * 0.06 * math.sin(k / 16 * math.pi),
             cy - r * 0.2 - w * 0.12 * math.sin(k / 16 * math.pi * 1.2)) for k in range(17)]
    f.ribbon(tail, lambda s: lw * 2.2 * (1 - s) + lw * 0.3, 1, fill)
    end = tail[-1]
    f.ribbon(spiral(end, w * 0.05, w * 0.012, 1.1, 0.0, flip=-sgn), lambda s: lw * 1.6 * (1 - s) + lw * 0.3, 1, fill)


def brush(f, length, width, seed, mat, bend=0.18, bristles=3):
    """A brush slash `length` long: pressed down hard at its start, sweeping in one clean arc and
    tapering to a sharp point, with a few dry bristle flicks leaving its tail; a thin echo stroke
    runs beside it."""
    rnd = random.Random(seed)
    n = 30
    path = [(length * (k / n - 0.5), bend * length * math.sin(math.pi * k / n)) for k in range(n + 1)]

    def w(s):
        return width * min(1.0, (s / 0.06)) ** 0.6 * (1 - s) ** 1.15
    f.ribbon(path, w, 0, mat)
    # dry bristle flicks off the tail
    for b in range(bristles):
        off = (b - (bristles - 1) / 2) * width * 0.34
        start = int(n * rnd.uniform(0.45, 0.6))
        reach = rnd.uniform(0.85, 1.12)
        sub = [(p[0] * reach + length * 0.02, p[1] + off * (0.3 + k / (n - start))) for k, p in enumerate(path[start:])]
        f.ribbon(sub, lambda s: width * 0.14 * (1 - s) ** 1.2 + 0.003, 0, mat)
    # the echo: a thin stroke along the inside of the arc
    echo = [(p[0] * 0.8 + length * 0.04, p[1] - width * 0.9) for p in path[3:-3]]
    f.ribbon(echo, lambda s: width * 0.22 * math.sin(math.pi * s) ** 0.7 + 0.002, 0, mat)


def crest(f, radius, ring_mat, disc_mat):
    """The eclipse crest: a ring, eight long petals between it and a dark disc."""
    n = 40
    outer, inner = radius, radius * 0.86
    for k in range(n):
        a0, a1 = TAU * k / n, TAU * (k + 1) / n
        f.poly([(outer * math.cos(a0), outer * math.sin(a0)), (outer * math.cos(a1), outer * math.sin(a1)),
                (inner * math.cos(a1), inner * math.sin(a1)), (inner * math.cos(a0), inner * math.sin(a0))], 0, ring_mat)
    for p in range(8):
        a = TAU * p / 8 + TAU / 16
        pts = []
        for k in range(13):
            s = k / 12
            r = radius * (0.3 + 0.48 * s)
            half = 0.18 * math.sin(math.pi * s) ** 0.8
            pts.append((r * math.cos(a + half), r * math.sin(a + half)))
        for k in range(12, -1, -1):
            s = k / 12
            r = radius * (0.3 + 0.48 * s)
            half = 0.18 * math.sin(math.pi * s) ** 0.8
            pts.append((r * math.cos(a - half), r * math.sin(a - half)))
        f.poly(pts, 0, ring_mat)
    f.disc((0, 0), radius * 0.3, 0, ring_mat, 28)
    f.disc((0, 0), radius * 0.22, 1, disc_mat, 28)


def project(f, name, coll, materials, bvh, centre, direction, up, rotate=0.0, lift=0.004, step=0.0025):
    """Lays the flat shapes onto the cloth: each point cast along `direction` (toward the cloth)
    from in front of `centre`, landing on the first surface hit, raised by lift + layer * step.
    Points that miss are dropped with their shape."""
    d = V(direction).normalized()
    up = V(up)
    up = (up - d * up.dot(d)).normalized()
    right = up.cross(d).normalized()
    ca, sa = math.cos(rotate), math.sin(rotate)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    kept = 0
    for pts, layer, mat in f.polys:
        verts = []
        ok = True
        for (u, v) in pts:
            uu, vv = u * ca - v * sa, u * sa + v * ca
            origin = V(centre) + right * uu + up * vv - d * 1.5
            hit, nrm, _, _ = bvh.ray_cast(origin, d, 3.0)
            if hit is None:
                ok = False
                break
            if nrm.dot(d) > 0:
                nrm = -nrm
            verts.append(hit + nrm * (lift + layer * step))
        if not ok or len(verts) < 3:
            continue
        bv = [bm.verts.new(p) for p in verts]
        try:
            face = bm.faces.new(bv)
        except ValueError:
            continue
        face.material_index = mat
        # wound to face out of the cloth (toward where it was cast from)
        if face.normal.length > 0 and face.normal.dot(-d) < 0:
            face.normal_flip()
        uv_of = dict(zip(bv, pts))         # by vertex: a flip reverses the loops
        for loop in face.loops:
            loop[uvl].uv = uv_of[loop.vert]
        kept += 1
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in materials:
        me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    o["kind"] = "decal"
    return o, kept


def cloth_bvh(objects):
    """One BVH over the given objects (world space)."""
    bm = bmesh.new()
    for o in objects:
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    bvh = BVHTree.FromBMesh(bm)
    bm.free()
    return bvh


def ink_materials():
    return [K.mat_flat("EE_CloudFill", (0.27, 0.27, 0.3), 0.55), K.mat_flat("EE_CloudLine", (0.62, 0.62, 0.66), 0.5),
            K.mat_flat("EE_CloudOutline", (0.5, 0.5, 0.54), 0.5), K.mat_flat("EE_BrushCrimson", (0.62, 0.01, 0.035), 0.42),
            K.mat_flat("EE_CrestDark", (0.02, 0.0, 0.0), 0.5), K.mat_flat("EE_InkFill", (0.33, 0.33, 0.36), 0.6),
            K.mat_flat("EE_InkLine", (0.04, 0.04, 0.05), 0.6)]
