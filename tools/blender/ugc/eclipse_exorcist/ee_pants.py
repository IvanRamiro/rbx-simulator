"""The Eclipse Exorcist's hakama (run inside Blender; layered clothing, Pants on WaistCenterAttachment).

Wide pleated hakama of charcoal silk, pinstriped in black, flaring to mid-shin, where kyahan
wrappings bind each shin in black bandage, cross-tied with the crimson cord of the waist rope; split
-toed tabi boots of black lacquered leather below. Each leg's inner side is flattened where the
blocky legs meet.

Built twice (see ee_kit): pieces(res="hi") for the bake, pieces(res="low") for the game mesh.
"""
import math

from mathutils import Vector

import ee_kit as K

V = Vector
TAU = K.TAU

RES = {
    "hi": {"folds": 1.0, "leg": (96, 0.04), "hip": (96, 0.05), "wrap": (64, 0.02), "boot": (56, 0.03), "cord": 0.02},
    "low": {"folds": 0.6, "leg": (18, 0.32), "hip": (16, 0.4), "wrap": (14, 0.28), "boot": (14, 0.12), "cord": 0.12},
}
LEG_X = 0.5            # the blocky leg box is x 0..1: its centre
HIP_TOP, HAKAMA_HEM = 0.42, -1.3
WRAP_TOP, WRAP_BOTTOM = -1.18, -1.7
BOOT_TOP, SOLE = -1.66, -2.02


def leg_section(t, side, outer_a, inner_a, b):
    """A leg's cross-section: wide on the outside, flattened on the inside (where the legs meet)."""
    outward = math.sin(t) * side > 0
    a = outer_a if outward else inner_a
    p = 4.0 if outward else 7.0
    return K.se(t, a, b, p)


def hakama_leg(r, side):
    """One wide hakama leg from the hip to its flared hem at mid-shin; deep pleats at the front, two
    at the back, soft folds deepening downward."""
    m = K.Mesh()
    n, step = r["leg"]
    cx = LEG_X * side
    zs = K.levels(0.05, HAKAMA_HEM, step)
    pts, uvs = [], []
    total = len(zs) - 1
    for j, z in enumerate(zs):
        v = j / total
        outer = 0.6 + 0.12 * v ** 1.3
        inner = 0.545          # reaches just past the centre line: the legs' cloth meets there
        b = 0.6 + 0.1 * v ** 1.2
        row, uvrow = [], []
        for i in range(n + 1):
            t = TAU * i / n
            x, y, nrm = leg_section(t, side, outer, inner, b)
            front = max(0.0, -math.cos(t))
            back = max(0.0, math.cos(t))
            # pleats: sharp at the front (five), softer at the back (two)
            pleat = 0.035 * (abs(math.sin(t * 5 * 2.5)) - 0.5) * front ** 0.5 + 0.03 * (abs(math.sin(t * 2 * 2.5)) - 0.5) * back
            d = pleat * (0.5 + 0.5 * v) * r["folds"] + K.folds(t, v, 51 + side, 6, lambda vv: 0.025 * r["folds"] * vv)
            # the hem rises a little at the back
            zz = z + (0.08 * back * v ** 4)
            row.append(V((cx + x, y, zz)) + nrm * d)
            uvrow.append((i / n * 3.0, (0.05 - z) * 0.8))
        pts.append(row[:-1])
        uvs.append(uvrow)
    m.grid(pts, uvs, 0, closed=True, outward=lambda j, i, c: V((c.x - cx, c.y, 0.0)))
    return m


def hip(r):
    """The hakama's waist: a band round the hips (under the robe and the cord), joining the legs."""
    m = K.Mesh()
    n, step = r["hip"]
    pts, uvs = [], []
    for z in K.levels(HIP_TOP, -0.1, step):
        row, uvrow = [], []
        for i in range(n + 1):
            t = TAU * i / n
            x, y, nrm = K.se(t, 1.04, 0.545, 5.0)
            row.append(V((x, y, z)))
            uvrow.append((i / n * 3.4, (HIP_TOP - z) * 0.8))
        pts.append(row[:-1])
        uvs.append(uvrow)
    m.grid(pts, uvs, 0, closed=True, outward=lambda j, i, c: V((c.x, c.y, 0.0)))
    return m


def wrap(r, side):
    """The kyahan: a close wrapping round the shin, under the hakama's hem; the bandage's turns
    stand out as low ridges (the high-detail source only)."""
    m = K.Mesh()
    n, step = r["wrap"]
    cx = LEG_X * side
    zs = K.levels(WRAP_TOP, WRAP_BOTTOM, step)
    hi = step < 0.1
    pts, uvs = [], []
    for z in zs:
        row, uvrow = [], []
        for i in range(n + 1):
            t = TAU * i / n
            x, y, nrm = K.se(t, 0.535, 0.535, 6.0)
            ridge = 0.0
            if hi:
                # a bandage wound in a spiral: each turn's edge raised
                ph = ((z - WRAP_BOTTOM) / 0.11 + t / TAU) % 1.0
                ridge = 0.012 * (1 - min(1.0, ph / 0.12)) + 0.006 * math.sin(ph * math.pi)
            row.append(V((cx + x * 1.0, y, z)) + nrm * ridge)
            uvrow.append((i / n * 2.2, (WRAP_TOP - z) * 2.0))
        pts.append(row[:-1])
        uvs.append(uvrow)
    m.grid(pts, uvs, 0, closed=True, outward=lambda j, i, c: V((c.x - cx, c.y, 0.0)))
    return m


def cross_cord(r, side):
    """The crimson cord tied crosswise up the front of the wrapping, knotted at the top."""
    m = K.Mesh()
    cx = LEG_X * side
    zs = [WRAP_BOTTOM + 0.06 + k * 0.12 for k in range(5)]
    path = []
    for k, z in enumerate(zs):
        sx = 0.32 if k % 2 == 0 else -0.32
        path.append(V((cx + sx, -0.56, z)))
    path = K.resample(path, r["cord"])
    for p in path:
        # lie on the wrapping's front, curving round its corners
        p.y = -0.56 + 0.06 * (abs(p.x - cx) / 0.34) ** 4
    sides = 6 if r["cord"] < 0.1 else 4
    K.tube(m, path, lambda k, nn: 0.022, sides, 0, cap=True, uv_v=4.0)
    knot = [V((cx - 0.08, -0.6, WRAP_TOP + 0.01)), V((cx, -0.62, WRAP_TOP + 0.04)), V((cx + 0.08, -0.6, WRAP_TOP + 0.01))]
    K.tube(m, K.resample(knot, r["cord"] / 2), lambda k, nn: 0.034, sides, 0, cap=True, uv_v=4.0)
    return m


def boot(r, side):
    """A split-toed tabi boot of lacquered leather round the blocky foot: a thick sole, the split
    between the big toe and the rest (a groove down the front), a seam up the back."""
    m = K.Mesh()
    n, step = r["boot"]
    cx = LEG_X * side
    zs = K.levels(BOOT_TOP, SOLE, step)
    hi = step < 0.1
    pts, uvs = [], []
    for z in zs:
        row, uvrow = [], []
        for i in range(n + 1):
            t = TAU * i / n
            sole = z < -1.95
            a = 0.545 + (0.012 if sole else 0.0)
            x, y, nrm = K.se(t, a, 0.56 + (0.015 if sole else 0.0), 6.0)
            groove = 0.0
            if hi:
                # the split toe: a groove down the front, a third of the way in from the inner side
                gx = cx - side * 0.17
                groove = -0.025 * max(0.0, 1 - abs((cx + x) - gx) / 0.03) * (1.0 if y < -0.45 else 0.0)
            row.append(V((cx + x, y, z)) + nrm * groove)
            uvrow.append((i / n * 3.0, (BOOT_TOP - z) * 2.0))
        pts.append(row[:-1])
        uvs.append(uvrow)
    m.grid(pts, uvs, 0, closed=True, outward=lambda j, i, c: V((c.x - cx, c.y, 0.0)))
    # the sole: closed underneath
    bottom = [m.v(p) for p in pts[-1]]
    c = m.v(V((cx, 0, SOLE)))
    for i in range(n):
        m.face([bottom[i], bottom[(i + 1) % n], c], [(0, 0), (1, 0), (0.5, 0.5)], 0, V((0, 0, -1)))
    return m


def pieces(res, coll, M):
    r = RES[res]
    out = []

    def shell(mesh, name, mats, thick, kind):
        o = mesh.object(name, coll, mats)
        if thick:
            K.solidify(o, thick)
        o["kind"] = kind
        out.append(o)
        return o

    cloth = [M["hakama"], M["hakama_in"]]
    shell(hip(r), "EE_Pants_Hip_" + res, cloth, 0.03, "cloth")
    for side, nm in ((1, "Left"), (-1, "Right")):
        shell(hakama_leg(r, side), "EE_Pants_Leg" + nm + "_" + res, cloth, 0.035, "cloth")
        shell(wrap(r, side), "EE_Pants_Wrap" + nm + "_" + res, [M["wrap"], M["wrap"]], 0.03, "cloth")
        shell(cross_cord(r, side), "EE_Pants_Cord" + nm + "_" + res, [M["cord"]], 0, "cord")
        shell(boot(r, side), "EE_Pants_Boot" + nm + "_" + res, [M["boot"], M["boot"]], 0.04, "cloth")
    return out


def materials():
    return {"hakama": K.mat_hakama(), "hakama_in": K.mat_flat("EE_HakamaInside", (0.02, 0.02, 0.022), 0.7),
            "wrap": K.mat_wrap(), "cord": K.mat_cord(), "boot": K.mat_lacquer()}
