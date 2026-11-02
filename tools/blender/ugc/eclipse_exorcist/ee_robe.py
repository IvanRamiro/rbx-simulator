"""The Eclipse Exorcist's robe (run inside Blender; layered clothing, a Jacket on BodyFrontAttachment).

An exorcist who seals a blood-moon demon into silver talismans, and the robe shows what the seal
costs him:
- black silk with crimson fractures leaking through it, heaviest low on his left;
- a high standing collar masking his face to the nose, taller at the back;
- the crossed collar (left over right) banded in crimson;
- wide sleeves with crimson cuffs, the right one printed with grey storm clouds;
- a white funeral stole hung over his left shoulder only, and over his right shoulder a short black
  half-mantle lined in crimson, cut into three pointed lappets: the two shoulders never match;
- an asymmetric skirt of five panels, long on his left (ending in a pointed tail below the knee),
  cut short on his right, over a ragged crimson underskirt that shows through every slit.

Built twice from the same shapes (see ee_kit): pieces(res="hi") for the bake, pieces(res="low")
for the game mesh. Space: Blender, on the blocky body (ee_kit's header).
"""
import math

from mathutils import Vector

import ee_kit as K

V = Vector
TAU = K.TAU

# per piece: (columns round, rows every this many studs); folds scales every fold's depth
RES = {
    "hi": {"folds": 1.0, "torso": (96, 0.05), "collar": (96, 0.04), "sleeve": (80, 0.05), "skirt": (160, 0.05),
           "under": (160, 0.05), "mantle": (80, 0.04), "stole": 0.04, "band": 0.05},
    "low": {"folds": 0.6, "torso": (16, None), "collar": (20, 0.2), "sleeve": (16, 0.42), "skirt": (34, 0.3),
            "under": (22, 0.38), "mantle": (18, 0.3), "stole": 0.3, "band": 0.6},
}
THICK = 0.035

TORSO_A = 1.07
NECK = (0.69, 0.675)          # the collar's base (the head is 0.6 x 0.6; its inner face clears it)
SKIRT_TOP = 0.1
SKIRT_TOP_AB = (1.1, 0.62)
SKIRT_HEM_AB = (1.34, 0.88)
SLEEVE_X = 1.53
CUFF = 0.62                   # the crimson cuff runs from the sleeve's opening up to here


def torso_b(z):
    """The torso's half-depth: the body's 0.5 plus room, filling out over the chest to meet the
    collar (which must clear the head)."""
    return 0.575 + (NECK[1] + 0.01 - 0.575) * K.smoothstep(1.3, 1.95, z)


def skirt_ab(z, scale=1.0):
    """The skirt's half-extents at height z (it flares toward the hem)."""
    f = K.smoothstep(SKIRT_TOP, -1.7, z) ** 0.9
    a = SKIRT_TOP_AB[0] + (SKIRT_HEM_AB[0] - SKIRT_TOP_AB[0]) * f
    b = SKIRT_TOP_AB[1] + (SKIRT_HEM_AB[1] - SKIRT_TOP_AB[1]) * f
    return a * scale, b * scale


def _wrap(t):
    return t - TAU if t > math.pi else t


# ---------- pieces ----------
def torso(r):
    """The body of the robe: a rounded box from the waist to the shoulders, filling out over the
    chest, closed over the shoulders by a yoke that turns in to the collar's base."""
    m = K.Mesh()
    n, step = r["torso"]
    # the game mesh keeps only the rows the shape needs (where the chest fills out)
    zs = K.levels(1.98, -0.04, step)[::-1] if step else [-0.04, 0.6, 1.3, 1.65, 1.98]
    rings = [(z, TORSO_A, torso_b(z)) for z in zs]
    bt = torso_b(2.0)
    rings += [(2.04, TORSO_A - 0.02, bt), (2.075, TORSO_A - 0.15, bt), (2.09, NECK[0] + 0.012, NECK[1] + 0.01)]
    pts, uvs = [], []
    for z, ra, rb in rings:
        row, uvrow = [], []
        for i in range(n + 1):
            t = TAU * i / n
            x, y, nrm = K.se(t, ra, rb, 6.0)
            d = K.folds(t, 0.5, 11, 7, lambda v: 0.012 * r["folds"]) if z < 1.9 else 0.0
            row.append(V((x, y, z)) + nrm * d)
            uvrow.append((i / n * 3.4, z * 0.8))
        pts.append(row[:-1])
        uvs.append(uvrow)
    top = len(rings) - 4
    m.grid(pts, uvs, 0, closed=True, outward=lambda j, i, c: V((c.x, c.y, 0.0)) if j < top else V((0, 0, 1)))
    return m


def collar(r):
    """The high collar: from the yoke round the lower head, up to the bridge of the nose at the front
    and taller at the back, flaring slightly; the left side laps over the right at the front, its
    edge standing proud."""
    m = K.Mesh()
    n, step = r["collar"]
    rows = max(3, int(round(0.62 / step)))
    pts, uvs = [], []
    for j in range(rows + 1):
        v = j / rows
        row, uvrow = [], []
        for i in range(n + 1):
            t = TAU * i / n
            back = (1 - math.cos(t)) / 2
            top = 2.6 + 0.38 * back ** 1.1
            z = 2.07 + (top - 2.07) * v
            flare = 0.035 * v ** 2 * (0.4 + 0.6 * back)
            x, y, nrm = K.se(t, NECK[0] + flare, NECK[1] + flare, 3.2)
            tw = _wrap(t)
            lap = 0.024 * K.smoothstep(-0.14, -0.04, tw) * (1 - K.smoothstep(0.3, 0.44, tw))
            row.append(V((x, y, z)) + nrm * lap)
            uvrow.append((i / n * 3.0, z * 0.8))
        pts.append(row[:-1])
        uvs.append(uvrow)
    m.grid(pts, uvs, 0, closed=True, outward=lambda j, i, c: V((c.x, c.y, 0.0)))
    return m


def sleeve(r, side):
    """A wide sleeve round the arm, flaring toward the cuff, its back hanging lower (the pocket of a
    kimono sleeve), closed over the top of the arm; the lowest rows are the crimson cuff."""
    m = K.Mesh()
    n, step = r["sleeve"]
    cx = SLEEVE_X * side
    zs = sorted(set(K.levels(2.04, 0.42, step) + [CUFF]), reverse=True)
    pts, uvs, mats = [], [], []
    for z in zs:
        v = (2.04 - z) / (2.04 - 0.42)
        a = 0.56 + 0.17 * v ** 1.4
        b = 0.57 + 0.24 * v ** 1.3
        row, uvrow = [], []
        for i in range(n + 1):
            t = TAU * i / n
            x, y, nrm = K.se(t, a, b, 5.0)
            back = max(0.0, -math.cos(t))                  # 1 at the back (+Y)
            droop = 0.32 * back ** 1.5 * v ** 3
            d = K.folds(t, v, 5 + side, 5, lambda vv: 0.035 * r["folds"] * vv)
            row.append(V((cx + x, y, z - droop)) + nrm * d)
            uvrow.append((i / n * 3.0, (2.04 - z) * 0.8))
        pts.append(row[:-1])
        uvs.append(uvrow)
        mats.append(2 if z < CUFF - 1e-6 else 0)
    cap = []
    for rise, shrink in ((0.04, 0.55), (0.02, 0.9)):
        cap.append([V((cx + K.se(TAU * i / n, 0.56 * shrink, 0.57 * shrink, 5.0)[0],
                       K.se(TAU * i / n, 0.56 * shrink, 0.57 * shrink, 5.0)[1], 2.04 + rise)) for i in range(n)])
    allpts = cap + pts
    nc = len(cap)
    alluv = [[(i / n * 3.0, -0.1 * (nc - k)) for i in range(n + 1)] for k in range(nc)] + uvs
    rows = [[m.v(p) for p in row] for row in allpts]
    for j in range(len(rows) - 1):
        mat = mats[j - nc + 1] if j >= nc else 0        # a band takes the material of its lower row
        for i in range(n):
            i2 = (i + 1) % n
            q = [rows[j][i], rows[j][i2], rows[j + 1][i2], rows[j + 1][i]]
            uv = [alluv[j][i], alluv[j][i + 1], alluv[j + 1][i + 1], alluv[j + 1][i]]
            c = (allpts[j][i] + allpts[j + 1][i2]) / 2
            m.face(q, uv, mat, V((c.x - cx, c.y, 0.0)) if j >= nc else V((0, 0, 1)))
    top = m.v(V((cx, 0, 2.088)))
    for i in range(n):
        m.face([rows[0][i], rows[0][(i + 1) % n], top], [(0, 0), (1, 0), (0.5, 0.5)], 0, V((0, 0, 1)))
    return m


def _lappets(t):
    """How far each of the half-mantle's three pointed lappets drops at angle t round the arm (at the
    front, the outside and the back)."""
    d = 0.0
    for centre in (0.25, 1.5 * math.pi, math.pi - 0.15):
        delta = abs(((t - centre + math.pi) % TAU) - math.pi)
        d = max(d, max(0.0, 1 - delta / 0.62) ** 1.4)
    return d


MANTLE_GAP = 0.45     # the mantle is open on the arm's inner side (against the torso), this wide


def mantle(r):
    """The half-mantle over the right shoulder: a short shoulder cape round the top of the arm, over
    the sleeve, dropping in three pointed lappets (front, outside, back); it runs on over the shoulder
    toward the collar. Open on the arm's inner side, where it meets the torso."""
    m = K.Mesh()
    n, step = r["mantle"]
    cx = -SLEEVE_X
    t0, t1 = math.pi / 2 + MANTLE_GAP / 2, math.pi / 2 + TAU - MANTLE_GAP / 2
    nv = max(3, int(round(0.85 / step)))
    pts, uvs = [], []
    # the shoulder: from the collar's side out over the arm (the first rows), then down round it
    for j in range(nv + 1):
        v = j / nv
        row, uvrow = [], []
        for i in range(n + 1):
            t = t0 + (t1 - t0) * i / n
            hem = 1.46 - 0.24 * _lappets(t)
            z = 2.19 + (hem - 2.19) * v ** 1.1
            a = 0.62 + 0.1 * v
            b = 0.66 + 0.12 * v
            x, y, nrm = K.se(t, a, b, 4.0)
            # the top row arches over the arm; its inner end runs up to the collar
            if v == 0:
                x, y = x * 0.82, y * 0.82
            d = K.folds(t, v, 41, 6, lambda vv: 0.03 * r["folds"] * vv)
            row.append(V((cx + x, y, z)) + nrm * d)
            uvrow.append(((t - t0) * 0.7, v * 0.9))
        pts.append(row)
        uvs.append(uvrow)
    m.grid(pts, uvs, 0, outward=lambda j, i, c: V((c.x - cx, c.y, 0.3)))
    # the yoke strip over the shoulder: from the mantle's crown in to the collar's side
    pts2 = []
    for xx in (-1.06, -0.9, -0.74):
        pts2.append([V((xx, -0.6, 2.13)), V((xx, 0.0, 2.17)), V((xx, 0.6, 2.13))])
    m.grid(pts2, [[(k * 0.5, j * 0.4) for k in range(3)] for j in range(3)], 0, outward=lambda j, i, c: V((0, 0, 1)))
    return m


# the skirt's panels: (name, t0, t1, hem(u) (u 0..1 across the panel), scale, fold seed)
def _tail(u, lo, hi, peak=0.5):
    """A hem that drops to a point at `peak` across the panel."""
    d = 1 - abs(u - peak) / max(peak, 1 - peak)
    return lo + (hi - lo) * d ** 1.6


PANELS = [
    ("FrontRight", -1.52, 0.1, lambda u: -0.98 - 0.22 * u, 0.97, 21),
    ("FrontLeft", -0.32, 0.56, lambda u: -1.22 - 0.26 * u, 1.0, 22),
    ("LeftTail", 0.62, 1.52, lambda u: _tail(u, -1.42, -1.84, 0.42), 1.0, 23),
    ("BackLeft", 1.64, 3.06, lambda u: -1.5 + 0.24 * u, 1.0, 24),
    ("BackRight", 3.22, 4.62, lambda u: -1.22 + 0.2 * u, 1.0, 25),
]


def skirt_panel(r, spec):
    """One panel of the skirt hanging from the waist, flaring, soft folds deepening to its hem."""
    name, t0, t1, hem, scale, seed = spec
    around, step = r["skirt"]
    m = K.Mesh()
    nu = max(3, int(round((t1 - t0) / TAU * around)))
    lowest = min(hem(k / 8) for k in range(9))
    nv = max(3, int(round((SKIRT_TOP - lowest) / step)))
    pts, uvs = [], []
    for j in range(nv + 1):
        v = j / nv
        row, uvrow = [], []
        for i in range(nu + 1):
            u = i / nu
            t = t0 + (t1 - t0) * u
            z = SKIRT_TOP + (hem(u) - SKIRT_TOP) * v
            a, b = skirt_ab(z, scale)
            x, y, nrm = K.se(t, a, b, 4.0)
            d = K.folds(t, v, seed, 10, lambda vv: 0.06 * r["folds"] * (0.2 + 0.8 * vv))
            row.append(V((x, y, z)) + nrm * d)
            uvrow.append((u * (t1 - t0) * 1.4, (SKIRT_TOP - z) * 0.8))
        pts.append(row)
        uvs.append(uvrow)
    m.grid(pts, uvs, 0, outward=lambda j, i, c: V((c.x, c.y, 0.0)))
    return m


def underskirt_hem(t):
    """The underskirt's ragged hem: longer on the left, torn into points all round."""
    base = -1.28 - 0.22 * (math.sin(t) + 1) / 2
    k = (t / TAU * 11) % 1.0
    tooth = 1 - abs(k - 0.5) * 2
    return base - 0.17 * tooth ** 1.3


def underskirt(r):
    """The crimson underskirt: a full ring under the panels, a touch narrower, its hem ragged."""
    m = K.Mesh()
    n, step = r["under"]
    nv = max(3, int(round(1.6 / step)))
    pts, uvs = [], []
    for j in range(nv + 1):
        v = j / nv
        row, uvrow = [], []
        for i in range(n + 1):
            t = TAU * i / n
            z = (SKIRT_TOP - 0.06) + (underskirt_hem(t) - (SKIRT_TOP - 0.06)) * v
            a, b = skirt_ab(z, 0.93)
            x, y, nrm = K.se(t, a, b, 4.0)
            d = K.folds(t, v, 31, 12, lambda vv: 0.04 * r["folds"] * vv)
            row.append(V((x, y, z)) + nrm * d)
            uvrow.append((i / n * 4.0, (SKIRT_TOP - z) * 0.8))
        pts.append(row[:-1])
        uvs.append(uvrow)
    m.grid(pts, uvs, 0, closed=True, outward=lambda j, i, c: V((c.x, c.y, 0.0)))
    return m


def lapel_band(r):
    """The crossed collar's crimson band: from under the collar on the wearer's left, diagonally
    down across the chest to the right hip (left over right), lying on the torso's front."""
    m = K.Mesh()
    start, end = V((0.34, 0, 2.06)), V((-0.78, 0, 0.12))
    steps = max(2, int(round((start - end).length / r["band"])))
    width = 0.2
    dirn = (end - start).normalized()
    across = V((-dirn.z, 0, dirn.x))
    pts, uvs = [], []
    for k in range(steps + 1):
        c = start + (end - start) * (k / steps)
        row, uvrow = [], []
        for s in (-0.5, 0.0, 0.5):
            p = c + across * (s * width)
            p.y = -(torso_b(p.z) + 0.03)
            row.append(p)
            uvrow.append((s + 0.5, (start - c).length))
        pts.append(row)
        uvs.append(uvrow)
    m.grid(pts, uvs, 0, outward=lambda j, i, c: V((0, -1, 0)))
    return m


def _stole_depth(z):
    """How far from the body's centre plane the stole lies at height z: on the torso above the
    waist, on the flaring skirt below it."""
    if z > SKIRT_TOP:
        return torso_b(z) + 0.045
    return skirt_ab(z)[1] + 0.03 * K.smoothstep(SKIRT_TOP, -0.4, z) + 0.06


def stole_path():
    """The stole's centre line, from its end at the back to its hanging end at the front: up the
    back, round the shoulder's edge and over the left shoulder outside the collar, and down the
    front over the skirt."""
    back = [(0.62, -0.04), (0.62, 1.2), (0.66, 1.75)]
    front = [(0.62, 1.2), (0.6, 0.2), (0.64, -0.6), (0.68, -1.22)]
    over = [V((0.72, 0.74, 1.97)), V((0.79, 0.67, 2.12)), V((0.87, 0.42, 2.16)), V((0.92, 0.14, 2.175)),
            V((0.92, -0.14, 2.175)), V((0.87, -0.42, 2.16)), V((0.79, -0.67, 2.12)), V((0.72, -0.74, 1.97)),
            V((0.66, -_stole_depth(1.75), 1.75))]
    pts = [V((x, _stole_depth(z), z)) for x, z in back] + over
    pts += [V((x, -_stole_depth(z), z)) for x, z in front]
    return pts


def stole_length():
    path = K.resample(stole_path(), 0.04)
    return sum((b - a).length for a, b in zip(path, path[1:]))


def stole(r):
    """The funeral stole: a band 0.4 wide along stole_path, lying on the body, its hanging end cut
    to a swallowtail. UVs: u across 0..1, v along in studs from the back end."""
    m = K.Mesh()
    path = K.resample(stole_path(), r["stole"])
    width = 0.4
    pts, uvs = [], []
    along = 0.0
    total = sum((b - a).length for a, b in zip(path, path[1:]))
    for k, c in enumerate(path):
        if k:
            along += (path[k] - path[k - 1]).length
        t = (path[min(k + 1, len(path) - 1)] - path[max(k - 1, 0)]).normalized()
        out = V((0, c.y, 0)) if abs(c.y) > 0.3 else V((0, 0, 1))
        across = t.cross(out).normalized()
        if across.x < 0:
            across = -across
        tail = K.smoothstep(total - 0.32, total, along)
        row, uvrow = [], []
        for s in ((-0.5, -0.25, 0.0, 0.25, 0.5) if r["stole"] < 0.1 else (-0.5, 0.0, 0.5)):
            p = c + across * (s * width) + V((0, 0, 0.22 * tail * (1 - abs(s) * 2)))
            row.append(p)
            uvrow.append((s + 0.5, along))
        pts.append(row)
        uvs.append(uvrow)
    m.grid(pts, uvs, 0, outward=lambda j, i, cc: V((0, cc.y, 0)) if abs(cc.y) > 0.3 else V((0, 0, 1)))
    return m


def clasp(r):
    """A silver clasp on the collar's front, where the left side laps over: a four-pointed star."""
    m = K.Mesh()
    t = 0.3
    x, y, nrm = K.se(t, NECK[0] + 0.03, NECK[1] + 0.03, 3.2)
    c = V((x, y, 2.33)) + nrm * 0.02
    up = V((0, 0, 1))
    side = nrm.cross(up).normalized()
    size, depth = 0.13, 0.045
    tips = [c + up * size, c + side * size * 0.7, c - up * size, c - side * size * 0.7]
    inner = [c + (up + side).normalized() * size * 0.22, c + (side - up).normalized() * size * 0.22,
             c + (-up - side).normalized() * size * 0.22, c + (up - side).normalized() * size * 0.22]
    ridge = m.v(c + nrm * depth)
    ring = []
    for k in range(4):
        ring.append(m.v(tips[k]))
        ring.append(m.v(inner[k]))
    for k in range(8):
        m.face([ring[k], ring[(k + 1) % 8], ridge], [(0, 0), (1, 0), (0.5, 1)], 0, nrm)
    back = m.v(c - nrm * 0.01)
    for k in range(8):
        m.face([ring[(k + 1) % 8], ring[k], back], [(0, 0), (1, 0), (0.5, 1)], 0, -nrm)
    return m, c, nrm


def bead(r, c, nrm, hi):
    """The crimson bead in the clasp's heart."""
    m = K.Mesh()
    rows, n = (6, 10) if hi else (3, 6)
    centre = c + nrm * 0.05
    rad = 0.045
    up = V((0, 0, 1))
    side = nrm.cross(up).normalized()
    pts, uvs = [], []
    for j in range(rows + 1):
        th = math.pi * j / rows
        pts.append([centre + (nrm * math.cos(th) + (side * math.cos(TAU * i / n) + up * math.sin(TAU * i / n)) * math.sin(th)) * rad
                    for i in range(n)])
        uvs.append([(i / n, j / rows) for i in range(n + 1)])
    m.grid(pts, uvs, 0, closed=True, outward=lambda j, i, cc: cc - centre)
    return m


def pieces(res, coll, M):
    """The robe's pieces as closed shells: [object] (obj["kind"]: 'cloth', 'band' or 'metal')."""
    r = RES[res]
    out = []

    def shell(mesh, name, mats, thick, kind):
        o = mesh.object(name, coll, mats)
        K.solidify(o, thick)
        o["kind"] = kind
        out.append(o)
        return o

    silk = [M["silk"], M["lining"]]
    shell(torso(r), "EE_Robe_Torso_" + res, silk, THICK, "cloth")
    shell(collar(r), "EE_Robe_Collar_" + res, silk, 0.05, "cloth")
    for side, nm in ((1, "Left"), (-1, "Right")):
        shell(sleeve(r, side), "EE_Robe_Sleeve" + nm + "_" + res, [M["silk"], M["lining"], M["cuff"], M["lining"]], THICK, "cloth")
    shell(mantle(r), "EE_Robe_Mantle_" + res, silk, THICK, "cloth")
    for spec in PANELS:
        shell(skirt_panel(r, spec), "EE_Robe_Skirt" + spec[0] + "_" + res, silk, THICK, "cloth")
    shell(underskirt(r), "EE_Robe_Underskirt_" + res, [M["under"], M["lining"]], 0.03, "cloth")
    shell(lapel_band(r), "EE_Robe_Lapel_" + res, [M["trim"], M["trim"]], 0.025, "band")
    shell(stole(r), "EE_Robe_Stole_" + res, [M["stole"], M["stole"]], 0.03, "band")
    cm, c, nrm = clasp(r)
    o = cm.object("EE_Robe_Clasp_" + res, coll, [M["silver"]], smooth=False)
    o["kind"] = "metal"
    out.append(o)
    bo = bead(r, c, nrm, res == "hi").object("EE_Robe_Bead_" + res, coll, [M["bead"]])
    bo["kind"] = "metal"
    out.append(bo)
    return out


def materials():
    # the stole's seal stamp sits 0.62 studs from its hanging end (UV v runs from the back end)
    K.STOLE_STAMP_V = stole_length() - 0.62
    return {
        "silk": K.mat_eclipse_silk(), "lining": K.mat_lining(), "under": K.mat_underskirt(),
        "stole": K.mat_stole(), "trim": K.mat_trim(), "cuff": K.mat_lining("EE_CrimsonCuff", (0.36, 0.0, 0.025), (0.62, 0.02, 0.05)),
        "silver": K.mat_silver(), "bead": K.mat_flat("EE_Bead", (0.55, 0.0, 0.03), 0.2, 0.0),
    }


# ---------- printed motifs (the high-detail source only) ----------
# (kind, centre, direction (cast toward the cloth), up, rotation, size, seed, flip)
FRONT, BACK, FROM_RIGHT, FROM_LEFT = V((0, 1, 0)), V((0, -1, 0)), V((1, 0, 0)), V((-1, 0, 0))
UP = V((0, 0, 1))
MOTIFS = [
    # every motif lies on one piece only (each is baked onto the piece it lies on)
    # storm clouds on his right: the sleeve below the mantle, the back of the skirt
    ("kumo", (-2.3, 0.08, 0.95), FROM_RIGHT, UP, 0.0, 0.6, 3, -1),
    ("kumo", (-1.5, -1.6, 0.78), FRONT, UP, 0.05, 0.62, 4, -1),
    ("kumo", (-1.5, 1.6, 1.05), BACK, UP, -0.05, 0.66, 5, 1),
    ("kumo", (-0.72, 1.6, -0.6), BACK, UP, 0.04, 0.46, 6, -1),
    ("kumo", (0.7, 1.6, -1.12), BACK, UP, -0.06, 0.66, 7, 1),
    # crimson brush strokes on his left, where the seal strains
    ("brush", (0.22, -1.6, 0.8), FRONT, UP, 1.42, (0.7, 0.11), 11, 1),
    ("brush", (2.3, 0.0, 1.3), FROM_LEFT, UP, 0.45, (1.0, 0.15), 12, 1),
    ("brush", (2.3, 0.08, 0.78), FROM_LEFT, UP, -0.3, (0.7, 0.1), 13, 1),
    ("brush", (1.5, -1.6, 1.1), FRONT, UP, 0.95, (0.8, 0.12), 14, 1),
    ("brush", (2.5, -0.43, -0.68), FROM_LEFT, UP, 1.35, (0.78, 0.12), 15, 1),
    ("brush", (0.18, -1.6, -0.78), FRONT, UP, 1.15, (0.9, 0.12), 16, 1),
    ("brush", (1.55, 1.6, 1.05), BACK, UP, 0.7, (0.75, 0.12), 17, 1),
    ("brush", (0.78, 1.6, -0.5), BACK, UP, 1.2, (0.7, 0.11), 18, 1),
    # the eclipse crest between the shoulder blades
    ("crest", (0.0, 1.6, 1.38), BACK, UP, 0.0, 0.34, 0, 1),
    # ink clouds down the white stole
    ("ink", (0.66, -1.6, 1.36), FRONT, UP, 0.0, 0.2, 21, 1),
    ("ink", (0.566, -1.6, 0.42), FRONT, UP, 0.0, 0.2, 22, -1),
    ("ink", (0.665, -1.6, -0.4), FRONT, UP, 0.0, 0.2, 23, 1),
    ("ink", (0.62, 1.6, 0.8), BACK, UP, 0.0, 0.2, 24, -1),
]


def decals(hi_objects, coll):
    """The printed motifs laid onto the high-detail robe; returns (objects, report)."""
    import ee_decals as D
    bvh = D.cloth_bvh([o for o in hi_objects if o.get("kind") in ("cloth", "band")])
    mats = D.ink_materials()
    out, report = [], []
    for k, (kind, centre, d, up, rot, size, seed, flip) in enumerate(MOTIFS):
        f = D.Flat()
        if kind == "kumo":
            D.kumo(f, size, seed, 0, 1, 2, flip)
        elif kind == "ink":
            D.kumo(f, size, seed, 5, 6, 6, flip)
        elif kind == "brush":
            D.brush(f, size[0], size[1], seed, 3)
        else:
            D.crest(f, size, 3, 4)
        o, kept = D.project(f, "EE_Robe_Motif%02d_%s" % (k, kind), coll, mats, bvh, centre, d, up, rot)
        out.append(o)
        report.append((o.name, kept, len(f.polys)))
    return out, report
