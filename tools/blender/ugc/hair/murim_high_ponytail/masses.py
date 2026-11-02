"""The Murim High Ponytail, redesigned by form (run inside Blender).

The owner's directive (2026-11-02): build it as a hair artist does, in stages, by intentional
primary masses rather than dozens of generated spikes. Stage 1 is the cap; stage 2 the primary
masses, each a sculpted shell with its own shape, flow and taper (hair_kit.mass):

- the crown: one rounded volume swept from behind the bangs up and back into the high tie;
- the bangs: parted in the middle, each half one curved mass whose lower edge comes to three
  lobes of different lengths (the middle lock longest, between the eyes);
- the upper sides: each flows back and down from under the crown, wrapping the side of the head
  to the jaw in two lobes;
- the framing locks: one a side, rounded and tapering, from the temple down beside the face onto
  the chest;
- the rear: the hair below the tie, a layered foundation hanging to the upper back in four lobes;
- the ponytail: five separate tapered clumps that rise out of the tie, broad, then fall down the
  back in an S, the middle one longest and the outer ones flaring.

Secondary locks, the ornament and the ribbons come only after the owner approves these forms in
clay. Space and the head as in hair_kit.
"""
import math

from mathutils import Vector

import hair_kit as H

K = H.K
V = Vector
TAU = H.TAU
DEG = math.pi / 180
C = H.HEAD_C
TIE = V((0.0, 0.3, 3.4))
COLLECTION = "MURIM_HAIR_REDESIGN"

# the hairline (elevation per azimuth from the front, degrees): a slight peak at the parting, the
# temples drawn back a little, a sideburn, round the back to the nape
HAIRLINE = H.table([(0, 37), (8, 39), (25, 38), (42, 30), (55, 18), (65, -2), (80, -20), (100, -26), (130, -36),
                    (160, -43), (180, -45)])

# game-mesh resolution: (columns, rows) per mass, segments for the ponytail clumps
RES = {"low": {"cap": (16, 7), "crown": (11, 7), "bangs": (8, 6), "side": (9, 9), "rear": (13, 7), "clump": (6, 0.34)},
       "hi": {"cap": (96, 24), "crown": (60, 40), "bangs": (44, 36), "side": (48, 50), "rear": (64, 40), "clump": (20, 0.03)}}


def hairline(a):
    return HAIRLINE(abs(((a / DEG + 180) % 360) - 180)) * DEG


def cap(r, tree):
    """Stage 1: the fitted cap, the foundation everything lies on: just off the head, thin."""
    cols, rows = r["cap"]
    return H.scalp(tree, cols, rows, hairline, lambda a, t: 0.045, None, 0)   # clears the head's rounded corners


def crown(r):
    """The crown: one rounded volume from under the bangs' roots (they lie over its front) up over
    the top and back into the tie, its underside resting on the head."""
    cols, rows = r["crown"]
    paths = []
    for i in range(cols):
        c = -1 + 2 * i / (cols - 1)
        # on the cap, building outward from it: its underside rests on the head
        paths.append([(0.5 * c, -0.12, 3.18), (0.62 * c, 0.02, 3.27), (0.52 * c, 0.16, 3.31),
                      (0.18 * c, 0.28, 3.37), TIE + V((0.04 * c, 0.02, -0.02))])
    m = K.Mesh()
    H.mass(m, paths, rows, lambda s, t: H.lens(s, t, 0.17, root=0.18, tip=0.85))
    return m


def bangs(r):
    """The bangs: two curved masses parted in the middle, falling over the forehead and curving out
    toward the temples; each lower edge comes to three lobes (the middle lock longest)."""
    cols, rows = r["bangs"]
    m = K.Mesh()
    for side in (1, -1):
        paths = []
        for i in range(cols):
            c = i / (cols - 1)
            tipz = H.lobes(c, [(0.04, 2.6), (0.5, 2.7), (0.96, 2.84)], 0.85)
            # up over the brow with volume, then down, curving out toward the temple
            paths.append([(side * (0.03 + 0.36 * c), -0.02, 3.33), (side * (0.06 + 0.5 * c), -0.66, 3.25 - 0.05 * c),
                          (side * (0.12 + 0.53 * c), -0.81, 2.96 - 0.08 * c),
                          (side * (0.18 + 0.53 * c + 0.08 * (1 - c)), -0.77, tipz)])
        H.mass(m, paths, rows, lambda s, t: H.lens(s, t, 0.1, root=0.15, tip=0.7))
    return m


def sides(r):
    """The upper sides, swept back: from under the crown each flows back and down over the side of
    the head, cut high at the temple (the face's side stays open) and sloping down toward the back,
    where it meets the rear; its lower edge in two lobes pointing back and down."""
    cols, rows = r["side"]
    m = K.Mesh()
    for side in (1, -1):
        paths = []
        for i in range(cols):
            c = i / (cols - 1)
            y = -0.3 + 0.7 * c
            drop = 2.5 - 0.5 * c                                   # the lower edge slopes down toward the back
            tipz = H.lobes(c, [(0.3, drop - 0.06), (0.78, drop - 0.08)], 0.7)
            sweep = 0.12 + 0.1 * c                                 # the ends swept back
            bulge = 0.84 + 0.04 * math.sin(math.pi * c)
            paths.append([(side * 0.55, y - 0.02, 3.14 - 0.05 * c), (side * 0.8, y, 2.95 - 0.04 * c),
                          (side * bulge, y + sweep * 0.5, (2.95 + tipz) / 2), (side * 0.82, y + sweep, tipz)])
        H.mass(m, paths, rows, lambda s, t: H.lens(s, t, 0.13, root=0.12, tip=0.72))
    return m


def framing(r):
    """The framing locks: one a side, from the temple over the front corner of the head and down
    beside the face, in front of the shoulder onto the chest: rounded, broad at the top, tapering
    to a point; the left a little longer."""
    sides_, step = r["clump"]
    m = K.Mesh()
    for side, tipz in ((1, 1.08), (-1, 1.2)):
        pts = [V((side * 0.36, -0.4, 3.16)), V((side * 0.66, -0.62, 3.0)), V((side * 0.76, -0.7, 2.6)),
               V((side * 0.75, -0.68, 2.1)), V((side * 0.7, -0.64, 1.6)), V((side * 0.72, -0.6, tipz))]
        path = K.resample(pts, step * 0.8)

        def width(k, nn):
            u = k / (nn - 1)
            return 0.17 * (0.7 + 0.3 * math.sin(min(u / 0.25, 1.0) * math.pi / 2)) * (1 - H.smoothstep(0.35, 1.0, u)) ** 1.1 if k < nn - 1 else 0.0

        def depth(k, nn):
            return width(k, nn) * 0.55
        H.lock(m, path, width, depth, sides_, V((1, 0, 0)), 0, None, uv_norm=True)
    return m


def rear(r, tree):
    """The rear: the hair below the tie, from the back of the head down over it in a full curve,
    hanging to the upper back in four lobes."""
    cols, rows = r["rear"]
    paths = []
    for i in range(cols):
        c = i / (cols - 1)
        a = (105 + 150 * c) * DEG
        root, n0 = H.on_head(tree, a, 38 * DEG)     # high, under the tie: no gap below the crown
        mid, n1 = H.on_head(tree, a, -12 * DEG)
        low, n2 = H.on_head(tree, a, -44 * DEG)
        tipz = H.lobes(c, [(0.1, 1.74), (0.37, 1.6), (0.63, 1.62), (0.9, 1.76)], 1.1)
        out = V((low.x, low.y, 0)).normalized()
        paths.append([root + n0 * 0.02, mid + n1 * 0.15, low + n2 * 0.14, V((low.x, low.y, tipz)) + out * 0.2])
    m = K.Mesh()
    H.mass(m, paths, rows, lambda s, t: H.lens(s, t, 0.11, root=0.15, tip=0.75))
    return m


# the ponytail's clumps: (place across -1..1, depth back, length: its tip's height, width)
CLUMPS = [(-0.9, 0.0, 1.12, 0.22), (-0.45, 0.06, 0.78, 0.26), (0.0, 0.1, 0.52, 0.28), (0.45, 0.06, 0.74, 0.26), (0.9, 0.0, 1.06, 0.22)]


def ponytail(r):
    """The ponytail: five separate tapered clumps out of the tie, rising first (the high tail's
    lift), broad at the top where they touch, then falling down the back in an S, spreading and
    parting as they go, the middle one longest."""
    sides, step = r["clump"]
    m = K.Mesh()
    for f, back, tipz, w in CLUMPS:
        pts = [TIE + V((0.03 * f, 0.0, -0.02)), TIE + V((0.1 * f, 0.24 + back * 0.3, 0.07)), V((0.22 * f, 0.66 + back, 3.42)),
               V((0.34 * f, 0.98 + back, 3.12)), V((0.42 * f + 0.04, 1.1 + back, 2.5)), V((0.5 * f - 0.03, 1.05 + back, 1.85)),
               V((0.62 * f + 0.02, 0.98 + back, tipz + 0.35)), V((0.7 * f + 0.06 * f, 0.94 + back, tipz))]
        path = K.resample(pts, step)
        n = len(path)

        def width(k, nn, w=w):
            u = k / (nn - 1)
            grow = 0.45 + 0.55 * math.sin(min(u / 0.2, 1.0) * math.pi / 2)
            return w * grow * (1 - H.smoothstep(0.45, 1.0, u)) ** 1.1 if k < nn - 1 else 0.0

        def depth(k, nn, w=w):
            return width(k, nn, w) * 0.62
        H.lock(m, path, width, depth, sides, V((1, 0, 0)), 0, None, uv_norm=True)
    return m


def build(tree, res="low", clay=None):
    """Stages 1 and 2 into the MURIM_HAIR_REDESIGN collection: the cap and the primary masses, each
    its own object (MHR_<Mass>_<res>). Returns the objects."""
    r = RES[res]
    coll = K.collection(COLLECTION)
    for o in list(coll.objects):
        if o.name.endswith("_" + res):
            bpy_remove(o)
    mat = clay or K.mat_flat("MHR_Clay", (0.24, 0.24, 0.25), 0.6)
    out = []
    for name, mesh in (("Cap", cap(r, tree)), ("Crown", crown(r)), ("Bangs", bangs(r)), ("Sides", sides(r)),
                       ("Framing", framing(r)), ("Rear", rear(r, tree)), ("Ponytail", ponytail(r))):
        o = mesh.object("MHR_%s_%s" % (name, res), coll, [mat])
        if name == "Cap":
            K.solidify(o, 0.015)
        out.append(o)
    return out


def bpy_remove(o):
    import bpy
    me = o.data
    bpy.data.objects.remove(o, do_unlink=True)
    if me.users == 0:
        bpy.data.meshes.remove(me)


def inspect(objects, tree):
    """What the inspection checks, per object: triangles, open edges, inside-out pieces, and
    vertices inside the head (clipping)."""
    import bmesh
    report = {}
    for o in objects:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        tris = sum(len(f.verts) - 2 for f in bm.faces)
        open_edges = sum(1 for e in bm.edges if not e.is_manifold)
        vol = sum(f.verts[0].co.dot(f.verts[i].co.cross(f.verts[i + 1].co)) / 6 for f in bm.faces for i in range(1, len(f.verts) - 1))
        inside = 0
        points = [v.co for v in bm.verts] + [f.calc_center_median() for f in bm.faces]   # faces too: a flat face can cut a curve
        for co in points:
            p = o.matrix_world @ co
            loc, nrm, _, d = tree.find_nearest(p)
            if (p - loc).dot(nrm) < -0.002:
                inside += 1
        bm.free()
        report[o.name] = {"tris": tris, "open_edges": open_edges, "volume": round(vol, 4), "points_in_head": inside}
    return report
