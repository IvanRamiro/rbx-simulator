"""The Murim High Ponytail, third design, from scratch (run inside Blender), under the owner's
Universal 3D Modeling Directive.

Why the owner's "Murim Hair" sheet works:
- Silhouette: a tall, wild mane. From the front it flares past the head at the temples and
  cheeks, then narrows to the jaw like a V, long locks running on onto the chest. From the side and
  back, the high tie lifts above the crown and the tail sweeps out behind as a long, wide comet.
- Hierarchy: the face framing (bangs, side curtains) carries the front; the tie (silver clasp,
  crimson ribbon) is the focal point; the tail carries the back and side.
- Flow: one logic everywhere. The bangs fall forward and out, the sides fall, the top sweeps up and
  back into the tie, the tail flows back then down in a wave, every tip flicking slightly out.

Method (hair: layered sculptural masses, then tapered locks):
1. Primary forms (this module's stage 1): smooth volumes that fix silhouette and proportion: the
   mane over the head, the bangs, the two side curtains, the two long chest locks, the tie and the
   comet-shaped tail. Reviewed in clay from six views; the owner approves before stage 2.
2. Secondary forms: tapered locks, each designed individually, laid along the volumes' flow.
3. Tertiary: strand grooves (in the bake), the silver clasp and the ribbon.

Budget: Roblox's rigid hair accessory, at most 4,000 triangles, one watertight mesh, within the
Classic hair box round HairAttachment (hair_kit).
"""
import math

from mathutils import Vector

import hair_kit as H

K = H.K
V = Vector
DEG = math.pi / 180
C = H.HEAD_C
TIE = V((0.0, 0.32, 3.4))          # the high tie, at the top of the back of the crown
COLLECTION = "MURIM_HAIR_V3"

# where the hair starts round the face: across the brow, the temples, a sideburn, round to the nape
HAIRLINE = H.table([(0, 36), (35, 32), (50, 22), (62, -4), (72, -24), (100, -28), (135, -38), (180, -45)])


def hairline(a):
    return HAIRLINE(abs(((a / DEG + 180) % 360) - 180)) * DEG


def mane(tree, cols=32, rows=12, uv_v=0.6):
    """The mane: the volume over the head, rising toward the tie, flaring at the temples and over
    the sides, full at the back, thin at the face's hairline (the bangs cover the brow)."""
    def offset(a, t):
        side = math.sin(a) ** 2                                          # 1 at the sides
        back = 0.5 - 0.5 * math.cos(a)                                   # 1 at the back
        body = math.sin(math.pi * min(t / 0.85, 1.0)) ** 0.7              # 0 at the crown and the hairline
        crown = (1 - t) ** 2 * back                                      # lifting toward the tie
        edge = 1 - H.smoothstep(0.86, 1.0, t)
        return 0.03 + (0.1 + 0.12 * side + 0.08 * back) * body * edge + 0.1 * crown
    # its v runs 0..uv_v from the crown: hair's body tone (and the highlight band's ring), not its roots
    m = H.scalp(tree, cols, rows, hairline, offset, None, 0, uv_u=8.0, uv_v=uv_v)
    return m


# the bangs' major lobes, per side from the parting outward: (control points with x for the wearer's
# left, width, thickness). Inner: falls between the eyes; middle: to the eye; outer: curves out to
# the temple. Each its own length and curve.
BANG_LOBES = [
    ([(0.04, -0.2, 3.3), (0.12, -0.66, 3.28), (0.17, -0.77, 3.0), (0.21, -0.74, 2.56)], 0.27, 0.075),
    ([(0.12, -0.17, 3.31), (0.34, -0.64, 3.27), (0.45, -0.76, 3.0), (0.52, -0.72, 2.69)], 0.29, 0.075),
    ([(0.2, -0.14, 3.3), (0.52, -0.58, 3.23), (0.67, -0.69, 2.98), (0.78, -0.62, 2.76)], 0.27, 0.07),
]


def bangs():
    """The bangs: centre-parted, each half a fan of three major lobes over the forehead."""
    m = K.Mesh()
    for side in (1, -1):
        for pts, w, th in BANG_LOBES:
            H.clump(m, [V((x * side, y, z)) for x, y, z in pts], w, th, 0.03, 16, 0, None, swell=0.35, root=0.85)
    return m


# the curtains' major lobes, per side round the head from its front corner (azimuth, degrees),
# the cheek's flare (radius), and the tip's height: the lengths step down toward the back
CURTAIN_LOBES = [(62, 0.92, 2.0), (92, 0.95, 2.06), (124, 0.9, 2.18)]


def curtains(tree):
    """The side curtains: three major lobes a side, each from under the mane down over the side of
    the head, flaring at the cheek and narrowing to its point at the jaw."""
    m = K.Mesh()
    for side in (1, -1):
        for az, flare, tipz in CURTAIN_LOBES:
            a = az * DEG
            p, n = H.on_head(tree, side * a if side > 0 else -a, 26 * DEG)
            ring = lambda r, z: V((side * math.sin(a) * r, -math.cos(a) * r, z))
            pts = [p - n * 0.02, ring(0.82, 2.86), ring(flare, 2.48), ring(0.86, tipz)]
            H.clump(m, pts, 0.46, 0.13, 0.03, 16, 0, None, swell=0.35, root=0.9)
    return m


def chest_locks(sides=16, step=0.05):
    """The long locks framing the face: one a side, out of the curtain's front at the temple, down
    past the cheek and the jaw, onto the chest in front of the shoulder; rounded, broad at the top,
    tapering to a point; the wearer's left a little longer."""
    m = K.Mesh()
    for side, tipz in ((1, 1.08), (-1, 1.2)):
        pts = [V((side * 0.42, -0.5, 3.12)), V((side * 0.66, -0.68, 2.92)), V((side * 0.74, -0.74, 2.5)),
               V((side * 0.74, -0.72, 2.0)), V((side * 0.7, -0.66, 1.55)), V((side * 0.72, -0.62, tipz))]
        path = K.resample(pts, step)

        def width(k, n):
            u = k / (n - 1)
            return 0.1 * (0.75 + 0.25 * math.sin(min(u / 0.25, 1.0) * math.pi / 2)) * (1 - H.smoothstep(0.4, 1.0, u)) ** 1.1 if k < n - 1 else 0.0

        def depth(k, n):
            return width(k, n) * 0.6
        H.lock(m, path, width, depth, sides, V((1, 0, 0)), 0, None, uv_norm=True)
    return m


def tail(sides=24, step=0.06):
    """The tie and tail: gathered tight at the tie, the hair springs up out of it, arcs back over
    and falls down the back in a long wave, widest a third of the way down, tapering to a point."""
    pts = [TIE + V((0, -0.02, -0.06)), TIE + V((0, 0.08, 0.2)), V((0.0, 0.66, 3.66)), V((0.0, 1.0, 3.42)),
           V((0.04, 1.18, 2.9)), V((0.0, 1.16, 2.25)), V((-0.06, 1.08, 1.6)), V((0.02, 1.02, 1.0)), V((0.1, 0.98, 0.5))]
    path = K.resample(pts, step)

    def width(k, n):
        u = k / (n - 1)
        prof = H.table([(0.0, 0.16), (0.06, 0.22), (0.18, 0.55), (0.36, 1.0), (0.55, 0.92), (0.75, 0.62), (0.92, 0.24), (1.0, 0.0)])
        return prof(u) / 2

    def depth(k, n):
        u = k / (n - 1)
        return width(k, n) * (0.95 if u < 0.15 else 0.6)
    m = K.Mesh()
    H.lock(m, path, width, depth, sides, V((1, 0, 0)), 0, None, uv_norm=True)
    return m


def build_primary(tree, clay=None):
    """Stage 1 into the MURIM_HAIR_V3 collection: the primary volumes, each its own object."""
    import bpy
    coll = K.collection(COLLECTION)
    for o in list(coll.objects):
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)
    mat = clay or K.mat_flat("V3_Clay", (0.22, 0.22, 0.23), 0.6)
    out = []
    for name, mesh, shell in (("Mane", mane(tree), 0.025), ("Bangs", bangs(), 0), ("Curtains", curtains(tree), 0),
                              ("ChestLocks", chest_locks(), 0), ("Tail", tail(), 0)):
        o = mesh.object("V3_%s" % name, coll, [mat])
        if shell:
            K.solidify(o, shell)
        out.append(o)
    return out
