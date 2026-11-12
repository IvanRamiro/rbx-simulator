"""The hub rebuilt as a celestial crystal city (the owner, 2026-11-12: "NOT INSPIRED BY CHINESE CULTURE ... RECREATE ALL THE ASSETS
IN THE MAIN HUB, NO CHINESE"): white veined marble, lapis, polished gold and glowing sky-blue crystal round the World Tree.

One atlas for the whole hub (HUB_STRIPS), every piece authored in Roblox studs at its own origin on y = 0, its front toward +Z.
Glow pieces (HB_*Glow, HB_*Crystal) take Neon in the game; glass pieces (HB_*Glass) see-through Glass.

- HB_HatchSanctum (+ HB_HatchGlass, HB_HatchCrystal, HB_HatchRunes): where eggs are hatched. A round marble dais of three steps;
  eight fluted marble columns with gold capitals carry a ring beam and a dome of gold ribs glazed with sky-blue crystal; a
  crystal floats over the apex. At the middle a gold cradle of six crystal claws holds the egg (the game's "Cradle" marker),
  a ring of runes turning round it.
- HB_CrystalLamp (+ HB_CrystalLampGlow): the city's street lamp: a marble foot, a slim gold post, a crescent arm and a faceted
  crystal floating in it.
- HB_PlazaConcept: a piece of the new ground for review: concentric marble paving, a lapis band, gold lines and a glowing rune
  path leading off it.
"""
import math

import worldlib as W

TAU = 2 * math.pi


# ---------- the atlas ----------
def _vein(u, v, seed):
    a = math.sin(u * 23.0 + seed + math.sin(v * 9.0 + seed * 2) * 2.2) + 0.5 * math.sin(u * 61.0 - v * 17.0 + seed)
    return max(0.0, 1.0 - abs(a) * 3.5)


def marble(u, v):
    base = 0.86 + 0.1 * v
    vein = _vein(u, v, 1.3) * 0.18
    return (base - vein * 0.9, base - vein * 0.85, base + 0.02 - vein * 0.6)


def marble_shade(u, v):
    base = 0.58 + 0.16 * v
    vein = _vein(u, v, 4.1) * 0.12
    return (base - vein, base + 0.01 - vein, base + 0.07 - vein * 0.7)


def lapis(u, v):
    fleck = 0.12 if (math.sin(u * 410.0) * math.sin(u * 173.0 + 1.1) > 0.92) else 0.0
    return (0.07 + 0.08 * v + fleck, 0.13 + 0.12 * v + fleck * 0.8, 0.36 + 0.22 * v + fleck * 0.3)


def gold(u, v):
    return (0.62 + 0.36 * v, 0.44 + 0.3 * v, 0.14 + 0.16 * v)


def crystal(u, v):
    """Deep sapphire at the bottom of the strip to bright sky-blue at the top (faces pick their depth by shade)."""
    return (0.1 + 0.45 * v * v, 0.32 + 0.55 * v, 0.85 + 0.15 * v)


def glow(u, v):
    return (0.75 + 0.25 * v, 0.95, 1.0)


def slate(u, v):
    return (0.18 + 0.12 * v, 0.2 + 0.13 * v, 0.27 + 0.15 * v)


def steel(u, v):
    return (0.55 + 0.25 * v, 0.57 + 0.25 * v, 0.6 + 0.25 * v)


# (since the finish pass, hub_finish.py, the strips only sort faces into materials: each becomes its own mesh and Roblox material)
HUB_STRIPS = [(64, marble), (64, marble_shade), (64, lapis), (64, gold), (64, crystal), (32, glow), (64, slate), (64, marble), (32, steel)]
MARBLE, SHADE, LAPIS, GOLD, CRYSTAL, GLOW, SLATE, MARBLE2, STEEL = range(9)


# ---------- shared shapes ----------
def ring(mb, r0, r1, y, band, seg=64, shade=0.85, centre=(0.0, 0.0), down=False):
    cx, cz = centre
    for k in range(seg):
        a0, a1 = TAU * k / seg, TAU * (k + 1) / seg
        pts = [(cx + math.cos(a0) * r1, y, cz + math.sin(a0) * r1), (cx + math.cos(a1) * r1, y, cz + math.sin(a1) * r1),
               (cx + math.cos(a1) * r0, y, cz + math.sin(a1) * r0), (cx + math.cos(a0) * r0, y, cz + math.sin(a0) * r0)]
        W_oriented(mb, pts, (0, -1 if down else 1, 0), band, shade)


def W_oriented(mb, pts, want, band, shade=0.8, u=0.5):
    nx = ny = nz = 0.0
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    if nx * want[0] + ny * want[1] + nz * want[2] < 0:
        pts = pts[::-1]
    v0, v1 = band
    mb.face(list(pts), [(u, v0 + (v1 - v0) * shade)] * len(pts))


def drum(mb, r, y0, y1, band, seg=64, top=True, centre=(0.0, 0.0), shade=(0.9, 0.62)):
    """A round tier: its wall and (top) its top."""
    mb.lathe([(r, y1, shade[0]), (r, y0, shade[1])], seg, band, centre=(centre[0], 0, centre[1]), cap_top=top)


def tube(mb, pts, r, band, sides=8, shade=0.85, caps=True):
    from mathutils import Vector
    P = [Vector(p) for p in pts]
    rings = []
    for i, p in enumerate(P):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        side = t.cross(Vector((0, 1, 0)))
        if side.length < 1e-4:
            side = t.cross(Vector((1, 0, 0)))
        side.normalize()
        up = side.cross(t).normalized()
        rr = r(i / (len(P) - 1)) if callable(r) else r
        rings.append([p + (side * math.cos(TAU * k / sides) + up * math.sin(TAU * k / sides)) * rr for k in range(sides)])
    v0, v1 = band
    for i in range(len(rings) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            quad = [tuple(rings[i][k]), tuple(rings[i][k2]), tuple(rings[i + 1][k2]), tuple(rings[i + 1][k])]
            mb.face(quad, [(0.5, v0 + (v1 - v0) * shade)] * 4)
    if caps:
        mb.face([tuple(q) for q in rings[0]][::-1], [(0.5, v0 + (v1 - v0) * shade)] * sides)
        mb.face([tuple(q) for q in rings[-1]], [(0.5, v0 + (v1 - v0) * shade)] * sides)


def gem(mb, centre, r, h, band, sides=6, shade=0.9, twist=0.0):
    """A faceted crystal: two pyramids base to base (a long bipyramid), its waist at centre."""
    cx, cy, cz = centre
    waist = [(cx + math.cos(TAU * k / sides + twist) * r, cy, cz + math.sin(TAU * k / sides + twist) * r) for k in range(sides)]
    top, bot = (cx, cy + h, cz), (cx, cy - h * 0.6, cz)
    v0, v1 = (band[0], band[1])
    for k in range(sides):
        a, b = waist[k], waist[(k + 1) % sides]
        for tip, sh in ((top, shade), (bot, shade * 0.7)):
            W_oriented(mb, [a, b, tip], ((a[0] + b[0]) / 2 - cx, (tip[1] - cy) * 0.3, (a[2] + b[2]) / 2 - cz), band, sh)


def shard(mb, base, direction, length, r, band, sides=6, shade=0.9, twist=0.0, foot=0.35):
    """One crystal shard: a hexagonal prism with a long faceted point, and a short point at its foot. base: where its foot's
    point meets the prism; direction: the way it grows."""
    from mathutils import Vector
    d = Vector(direction).normalized()
    side = d.cross(Vector((0, 1, 0)))
    if side.length < 1e-3:
        side = d.cross(Vector((1, 0, 0)))
    side.normalize()
    up = side.cross(d).normalized()
    b = Vector(base)
    body = length * 0.62

    def ringat(t, rr):
        return [b + d * t + (side * math.cos(TAU * k / sides + twist) + up * math.sin(TAU * k / sides + twist)) * rr for k in range(sides)]
    low, high = ringat(0.0, r), ringat(body, r * 0.92)
    tip, toe = b + d * length, b - d * (length * foot * 0.5)
    for k in range(sides):
        k2 = (k + 1) % sides
        mid = (low[k] + low[k2]) / 2 - b
        W_oriented(mb, [tuple(low[k]), tuple(low[k2]), tuple(high[k2]), tuple(high[k])], tuple(mid), band, shade * (0.8 + 0.2 * (k % 2)))
        W_oriented(mb, [tuple(high[k]), tuple(high[k2]), tuple(tip)], tuple((high[k] + high[k2]) / 2 - b), band, shade)
        W_oriented(mb, [tuple(low[k2]), tuple(low[k]), tuple(toe)], tuple((low[k] + low[k2]) / 2 - b - d), band, shade * 0.7)


# a cluster's shards: (tilt from upright in degrees, turn round it, length, radius, how far out from the middle its foot sits, hanging)
CLUSTER = [(0, 0, 1.0, 1.0, 0.0, False), (24, 15, 0.62, 0.62, 0.55, False), (32, 105, 0.5, 0.52, 0.6, False), (20, 200, 0.7, 0.66, 0.5, False),
           (38, 285, 0.42, 0.45, 0.62, False), (14, 330, 0.36, 0.4, 0.35, False), (160, 60, 0.34, 0.45, 0.4, True), (150, 230, 0.28, 0.38, 0.45, True)]


def crystal_cluster(mb, centre, size, band, turn=0.0):
    """A floating cluster: a tall main shard and smaller ones fanning out at their own angles, two hanging below; centre is the
    cluster's heart, where its gold ring mount goes (cluster_mount). size: the main shard's length."""
    from mathutils import Vector, Matrix
    c = Vector(centre)
    for tilt, spin, L, rr, out, hang in CLUSTER:
        a = math.radians(spin) + turn
        d = Matrix.Rotation(a, 3, "Y") @ Matrix.Rotation(math.radians(tilt), 3, "X") @ Vector((0, 1, 0))
        foot = c + Vector((math.sin(a) * out, 0, math.cos(a) * out)) * size * 0.14 - d * size * 0.12
        shard(mb, tuple(foot), tuple(d), size * L, size * 0.13 * rr, band, twist=spin, shade=0.75 + 0.25 * rr)


def cluster_mount(mb, centre, size, band):
    """The gold mount round a cluster's heart: a ring, a second ring tilted across it, and four little claws gripping the shards."""
    cx, cy, cz = centre
    R = size * 0.27
    for tilt in (0.0, 0.5):
        pts = []
        for i in range(29):
            a = TAU * i / 28
            x, y = math.cos(a) * R, math.sin(a) * R * math.sin(tilt)
            z = math.sin(a) * R * math.cos(tilt)
            pts.append((cx + x, cy + y, cz + z))
        tube(mb, pts, size * 0.017, band, sides=6, shade=0.95, caps=False)
    for k in range(4):
        a = TAU * k / 4 + TAU / 8
        tube(mb, [(cx + math.cos(a) * R, cy, cz + math.sin(a) * R), (cx + math.cos(a) * R * 0.75, cy + size * 0.12, cz + math.sin(a) * R * 0.75),
                  (cx + math.cos(a) * R * 0.45, cy + size * 0.18, cz + math.sin(a) * R * 0.45)], lambda f: size * (0.03 - 0.015 * f), band, sides=5, shade=1.0)


# ---------- the Hatching Sanctum ----------
DAIS = ((20.0, 0.6), (17.6, 1.2), (15.4, 1.8))    # the three steps: radius, top
COL_R, COLS, COL_TOP = 13.2, 8, 17.0               # the columns: ring radius, count, height of their capitals' top
BEAM_TOP = 18.6
DOME_H = 9.5                                      # the dome's rise over the ring beam
CRADLE_TOP = 4.4                                  # where the egg rests (the game's Cradle marker)
FLOOR = DAIS[-1][1]
# (size 5.2: the cluster stands as tall as the single crystals it replaced; at 8 it read bigger, the owner: "I didn't ask for bigger crystal")
# (four floating clusters stood round the dais until the owner, 2026-11-12: "I think the floating crystals are not necessary you can remove it")
SANCTUM_CLUSTERS = []


def column(mb, x, z, y0, y1, r=0.72):
    c = (x, 0, z)
    # the gold base: a plinth and a torus-like step
    mb.lathe([(r + 0.55, y0 + 0.5, 1.0), (r + 0.55, y0, 0.7)], 16, GOLD_BAND, centre=c, cap_top=True)
    mb.lathe([(r + 0.3, y0 + 0.9, 1.0), (r + 0.42, y0 + 0.5, 0.85)], 16, GOLD_BAND, centre=c, cap_top=True)
    # the fluted marble shaft (16 flutes, a slight taper)
    seg = 32
    rm = lambda a, k: 1.0 - 0.06 * (0.5 + 0.5 * math.cos(a * 16))
    mb.lathe([(r * 0.94, y1 - 1.2, 0.95), (r, y0 + 0.9, 0.7)], seg, MARBLE_BAND, centre=c, rmod=rm, cap_top=False)
    # the capital: a gold collar, a flaring bell of crystal-blue leaves, a square gold abacus
    mb.lathe([(r * 0.98, y1 - 0.9, 1.0), (r * 0.96, y1 - 1.2, 0.85)], 16, GOLD_BAND, centre=c, cap_top=False)
    mb.lathe([(r + 0.75, y1 - 0.35, 0.95), (r + 0.25, y1 - 0.75, 0.8), (r * 0.98, y1 - 0.9, 0.7)], 16, GOLD_BAND, centre=c, cap_top=True)
    mb.box((x, y1 - 0.18, z), (2 * r + 1.8, 0.36, 2 * r + 1.8), GOLD_BAND, u=0.5, top_shade=1.0, side_shade=0.8)


def dome_point(a, t, base, R=COL_R + 0.2, H=DOME_H):
    """A point on the dome: a, round it; t from the ring beam (0) to the apex (1)."""
    phi = t * math.pi / 2
    r = R * math.cos(phi)
    return (math.cos(a) * r, base + H * math.sin(phi), math.sin(a) * r)


def sanctum(coll, mat, bands):
    global MARBLE_BAND, GOLD_BAND
    MARBLE_BAND, GOLD_BAND = bands[MARBLE], bands[GOLD]
    mb = W.MeshBuilder()
    # the dais: three marble steps, each edged in gold
    prev = 0.0
    for r, top in DAIS:
        drum(mb, r, prev - 0.6 if prev == 0.0 else prev - 0.05, top, bands[MARBLE], shade=(0.95, 0.6))
        ring(mb, r - 0.35, r, top + 0.01, bands[GOLD], shade=0.9)
        prev = top
    # the floor: a lapis ring, gold lines, a marble field
    ring(mb, 9.0, 11.2, FLOOR + 0.02, bands[LAPIS], shade=0.8)
    ring(mb, 8.7, 9.0, FLOOR + 0.025, bands[GOLD], shade=0.95)
    ring(mb, 11.2, 11.5, FLOOR + 0.025, bands[GOLD], shade=0.95)
    for k in range(12):   # gold star points between the rings
        a = TAU * k / 12
        pts = [(math.cos(a) * 5.2, FLOOR + 0.03, math.sin(a) * 5.2), (math.cos(a + 0.09) * 8.4, FLOOR + 0.03, math.sin(a + 0.09) * 8.4),
               (math.cos(a) * 8.7, FLOOR + 0.03, math.sin(a) * 8.7), (math.cos(a - 0.09) * 8.4, FLOOR + 0.03, math.sin(a - 0.09) * 8.4)]
        W_oriented(mb, pts, (0, 1, 0), bands[GOLD], 0.9)
    # the columns and the ring beam they carry
    for k in range(COLS):
        a = TAU * (k + 0.5) / COLS
        column(mb, math.cos(a) * COL_R, math.sin(a) * COL_R, FLOOR, COL_TOP)
    mb.lathe([(COL_R + 1.7, BEAM_TOP, 0.95), (COL_R + 1.7, COL_TOP, 0.75)], 64, bands[MARBLE], cap_top=False)
    mb.lathe([(COL_R - 1.4, COL_TOP, 0.55), (COL_R - 1.4, BEAM_TOP, 0.7)], 64, bands[SHADE], cap_top=False)
    ring(mb, COL_R - 1.4, COL_R + 1.7, COL_TOP, bands[SHADE], shade=0.5, down=True)
    ring(mb, COL_R - 1.4, COL_R + 1.7, BEAM_TOP, bands[MARBLE], shade=0.95)
    for y in (COL_TOP + 0.25, BEAM_TOP - 0.25):   # gold bands round the beam's face
        mb.lathe([(COL_R + 1.78, y + 0.12, 1.0), (COL_R + 1.78, y - 0.12, 0.9)], 64, bands[GOLD], cap_top=False)
    # the dome's gold ribs, a gold ring round its foot and the apex crown
    base = BEAM_TOP
    for k in range(COLS):
        a = TAU * (k + 0.5) / COLS
        pts = [dome_point(a, t / 12, base) for t in range(13)]
        tube(mb, pts, lambda f: 0.42 - 0.14 * f, bands[GOLD], sides=6, shade=0.95, caps=False)
    mb.lathe([(COL_R + 0.5, base + 0.45, 1.0), (COL_R + 0.6, base, 0.8)], 64, bands[GOLD], cap_top=False)
    # the lantern on the apex: a gold collar, a ring of six slender gold posts round a crystal core, a little gold dome, a spire
    apex = base + DOME_H
    mb.lathe([(2.6, apex + 0.4, 1.0), (2.9, apex - 0.2, 0.85), (2.5, apex - 0.6, 0.7)], 24, bands[GOLD], cap_top=True)
    for k in range(6):
        a = TAU * k / 6
        mb.lathe([(0.16, apex + 3.6, 1.0), (0.2, apex + 0.4, 0.8)], 6, bands[GOLD], centre=(math.cos(a) * 2.1, 0, math.sin(a) * 2.1), cap_top=True)
    mb.lathe([(0.0, apex + 5.4, 1.0), (1.2, apex + 4.9, 0.95), (2.4, apex + 4.0, 0.85), (2.6, apex + 3.6, 0.75)], 24, bands[GOLD], cap_top=False)
    mb.lathe([(0.0, apex + 9.0, 1.0), (0.18, apex + 7.5, 0.95), (0.35, apex + 5.4, 0.85)], 8, bands[GOLD], cap_top=False)
    # the cradle: a stepped marble plinth, a gold bowl, six gold-set crystal claws curling up round the egg
    drum(mb, 3.4, FLOOR - 0.05, FLOOR + 0.6, bands[MARBLE], seg=32)
    ring(mb, 3.05, 3.4, FLOOR + 0.61, bands[GOLD], seg=32)
    drum(mb, 2.6, FLOOR + 0.6, FLOOR + 1.3, bands[MARBLE], seg=32)
    mb.lathe([(2.3, CRADLE_TOP - 0.2, 1.0), (2.0, CRADLE_TOP - 0.9, 0.9), (1.2, FLOOR + 1.9, 0.8), (0.7, FLOOR + 1.3, 0.7)], 24, bands[GOLD], cap_top=False)
    ring(mb, 0.0, 2.25, CRADLE_TOP - 0.3, bands[LAPIS], seg=24, shade=0.7)                       # the lapis well the egg sits in
    ring(mb, 2.0, 2.3, CRADLE_TOP - 0.19, bands[GOLD], seg=24, shade=1.0)
    for x, y, z, size in SANCTUM_CLUSTERS:
        cluster_mount(mb, (x, y, z), size, bands[GOLD])
    for k in range(6):
        a = TAU * k / 6
        ca, sa = math.cos(a), math.sin(a)
        pts = [(ca * 1.9, CRADLE_TOP - 0.6, sa * 1.9), (ca * 2.4, CRADLE_TOP + 0.6, sa * 2.4), (ca * 2.25, CRADLE_TOP + 1.9, sa * 2.25),
               (ca * 1.75, CRADLE_TOP + 2.8, sa * 1.75)]
        tube(mb, pts, lambda f: 0.28 - 0.18 * f, bands[GOLD], sides=6, shade=0.95)
    return mb.object("HB_HatchSanctum", coll, mat)


def sanctum_glass(coll, mat, bands):
    """The dome's crystal panes between the ribs (see-through in the game)."""
    mb = W.MeshBuilder()
    base = BEAM_TOP
    n_t = 8
    for k in range(COLS):
        a0, a1 = TAU * (k + 0.5) / COLS + 0.03, TAU * (k + 1.5) / COLS - 0.03
        for j in range(n_t):
            t0, t1 = j / n_t, min((j + 1) / n_t, 0.97)
            for s in range(3):
                b0, b1 = a0 + (a1 - a0) * s / 3, a0 + (a1 - a0) * (s + 1) / 3
                pts = [dome_point(b0, t0, base, COL_R), dome_point(b1, t0, base, COL_R), dome_point(b1, t1, base, COL_R), dome_point(b0, t1, base, COL_R)]
                mid = dome_point((b0 + b1) / 2, (t0 + t1) / 2, base, COL_R)
                W_oriented(mb, pts, (mid[0], mid[1] - base + 2, mid[2]), bands[CRYSTAL], 0.6 + 0.35 * j / n_t)
    return mb.object("HB_HatchGlass", coll, mat)


def sanctum_crystal(coll, mat, bands):
    """The crystal floating over the apex, and the crystals set in the claws' tips (glow)."""
    mb = W.MeshBuilder()
    apex = BEAM_TOP + DOME_H
    gem(mb, (0, apex + 2.1, 0), 1.1, 1.6, bands[GLOW], sides=6)                 # the lantern's crystal core
    # four crystal clusters floating round the dais
    for k, (x, y, z, size) in enumerate(SANCTUM_CLUSTERS):
        crystal_cluster(mb, (x, y, z), size, bands[GLOW], turn=k * 1.3)       # white with a glow (the owner, 2026-11-12)
    for k in range(6):
        a = TAU * k / 6
        gem(mb, (math.cos(a) * 1.7, CRADLE_TOP + 3.05, math.sin(a) * 1.7), 0.32, 0.6, bands[GLOW], sides=5, twist=a)
    return mb.object("HB_HatchCrystal", coll, mat)


def sanctum_runes(coll, mat, bands):
    """The ring of runes round the cradle (glow; the game turns it slowly): twelve rune plates on a thin band."""
    mb = W.MeshBuilder()
    y, R = CRADLE_TOP + 0.4, 4.3
    for k in range(48):   # the band: a thin vertical ribbon
        a0, a1 = TAU * k / 48, TAU * (k + 1) / 48
        W_oriented(mb, [(math.cos(a0) * R, y - 0.08, math.sin(a0) * R), (math.cos(a1) * R, y - 0.08, math.sin(a1) * R),
                        (math.cos(a1) * R, y + 0.08, math.sin(a1) * R), (math.cos(a0) * R, y + 0.08, math.sin(a0) * R)], (math.cos(a0), 0, math.sin(a0)), bands[GLOW], 0.9)
    for k in range(12):   # rune plates: a little diamond and a bar, alternating
        a = TAU * k / 12
        ca, sa = math.cos(a), math.sin(a)
        tx, tz = -sa, ca
        cx, cz = ca * R, sa * R
        if k % 2:
            pts = [(cx, y + 0.55, cz), (cx + tx * 0.35, y + 0.2, cz + tz * 0.35), (cx, y - 0.15, cz), (cx - tx * 0.35, y + 0.2, cz - tz * 0.35)]
        else:
            pts = [(cx - tx * 0.12, y + 0.6, cz - tz * 0.12), (cx + tx * 0.12, y + 0.6, cz + tz * 0.12), (cx + tx * 0.12, y - 0.2, cz + tz * 0.12),
                   (cx - tx * 0.12, y - 0.2, cz - tz * 0.12)]
        W_oriented(mb, pts, (ca, 0, sa), bands[GLOW], 1.0)
        W_oriented(mb, pts, (-ca, 0, -sa), bands[GLOW], 1.0)
    return mb.object("HB_HatchRunes", coll, mat)


# ---------- the lamp ----------
LAMP_Y = 9.2


def crystal_lamp(coll, mat, bands):
    """A marble foot, a slim gold post with two bands, a gold cup of four curling prongs holding the crystal, a halo ring round it."""
    mb = W.MeshBuilder()
    mb.lathe([(1.15, 0.5, 0.95), (1.3, 0.25, 0.8), (1.3, 0.0, 0.65)], 16, bands[MARBLE], cap_top=True)
    mb.lathe([(0.75, 1.0, 0.95), (0.95, 0.5, 0.8)], 16, bands[MARBLE], cap_top=True)
    mb.lathe([(0.24, LAMP_Y - 1.6, 1.0), (0.32, 1.0, 0.75)], 12, bands[GOLD], cap_top=True)
    for y in (2.4, 5.6):
        mb.lathe([(0.42, y + 0.12, 1.0), (0.42, y - 0.12, 0.85)], 12, bands[GOLD], cap_top=True)
    mb.lathe([(0.55, LAMP_Y - 1.25, 1.0), (0.3, LAMP_Y - 1.65, 0.85)], 12, bands[GOLD], cap_top=True)   # the cup's foot
    for k in range(4):
        a = TAU * k / 4 + TAU / 8
        ca, sa = math.cos(a), math.sin(a)
        pts = [(ca * 0.4, LAMP_Y - 1.3, sa * 0.4), (ca * 0.95, LAMP_Y - 0.6, sa * 0.95), (ca * 1.05, LAMP_Y + 0.4, sa * 1.05), (ca * 0.75, LAMP_Y + 1.2, sa * 0.75)]
        tube(mb, pts, lambda f: 0.12 - 0.06 * f, bands[GOLD], sides=5, shade=0.95)
    # the halo: a thin gold ring round the crystal's waist
    seg = 24
    pts = [(math.cos(TAU * i / seg) * 1.35, LAMP_Y + 0.15, math.sin(TAU * i / seg) * 1.35) for i in range(seg + 1)]
    tube(mb, pts, 0.07, bands[GOLD], sides=5, shade=1.0, caps=False)
    return mb.object("HB_CrystalLamp", coll, mat)


def crystal_lamp_glow(coll, mat, bands):
    mb = W.MeshBuilder()
    gem(mb, (0, LAMP_Y, 0), 0.62, 1.15, bands[GLOW], sides=6)
    return mb.object("HB_CrystalLampGlow", coll, mat)


# ---------- the ground, for review ----------
def plaza_concept(coll, mat, bands):
    mb = W.MeshBuilder()
    y = 0.05
    ring(mb, 21.0, 46.4, y - 0.03, bands[SHADE], seg=96, shade=0.35)              # the grout under the flagstones
    # concentric courses of marble flagstones, alternating white and veined shade
    r = 22.0
    k = 0
    while r < 46.0:
        w = 2.4
        n = max(12, int(TAU * r / 3.2))
        for i in range(n):
            a0, a1 = TAU * i / n + 0.004, TAU * (i + 1) / n - 0.004
            band = bands[MARBLE] if (i + k) % 5 else bands[MARBLE2]
            pts = [(math.cos(a0) * (r + w - 0.06), y, math.sin(a0) * (r + w - 0.06)), (math.cos(a1) * (r + w - 0.06), y, math.sin(a1) * (r + w - 0.06)),
                   (math.cos(a1) * (r + 0.06), y, math.sin(a1) * (r + 0.06)), (math.cos(a0) * (r + 0.06), y, math.sin(a0) * (r + 0.06))]
            W_oriented(mb, pts, (0, 1, 0), band, 0.6 + 0.35 * ((i * 7 + k * 3) % 5) / 4)
        r += w
        k += 1
    ring(mb, 21.4, 22.0, y + 0.01, bands[GOLD], shade=0.95)
    ring(mb, 30.5, 33.5, y + 0.012, bands[LAPIS], shade=0.75)
    ring(mb, 30.2, 30.5, y + 0.015, bands[GOLD], shade=0.95)
    ring(mb, 33.5, 33.8, y + 0.015, bands[GOLD], shade=0.95)
    ring(mb, 45.6, 46.4, y + 0.3, bands[GOLD], shade=0.9)
    mb.lathe([(46.4, y + 0.3, 0.8), (46.4, y - 0.8, 0.6)], 96, bands[SHADE], cap_top=False)
    # a path leading off it: marble slabs with a rune channel down the middle
    for i in range(14):
        z0 = 46.0 + i * 3.0
        W_oriented(mb, [(-5.0, y - 0.03, z0), (5.0, y - 0.03, z0), (5.0, y - 0.03, z0 + 3.0), (-5.0, y - 0.03, z0 + 3.0)], (0, 1, 0), bands[SHADE], 0.35)
        for side in (-1, 1):
            W_oriented(mb, [(side * 0.6, y, z0 + 0.06), (side * 5.0, y, z0 + 0.06), (side * 5.0, y, z0 + 2.94), (side * 0.6, y, z0 + 2.94)], (0, 1, 0),
                       bands[MARBLE] if i % 3 else bands[MARBLE2], 0.85)
            W_oriented(mb, [(side * 5.0, y + 0.15, z0), (side * 5.8, y + 0.15, z0), (side * 5.8, y + 0.15, z0 + 3.0), (side * 5.0, y + 0.15, z0 + 3.0)],
                       (0, 1, 0), bands[GOLD], 0.85)
        W_oriented(mb, [(-0.6, y - 0.02, z0), (0.6, y - 0.02, z0), (0.6, y - 0.02, z0 + 3.0), (-0.6, y - 0.02, z0 + 3.0)], (0, 1, 0), bands[LAPIS], 0.6)
    return mb.object("HB_PlazaConcept", coll, mat)


def plaza_concept_glow(coll, mat, bands):
    """The rune path's glowing glyphs, and a rune ring in the lapis band."""
    mb = W.MeshBuilder()
    for i in range(14):
        zc = 47.5 + i * 3.0
        W_oriented(mb, [(0, 0.06, zc - 0.9), (0.4, 0.06, zc), (0, 0.06, zc + 0.9), (-0.4, 0.06, zc)], (0, 1, 0), bands[GLOW], 1.0)
    for k in range(36):
        a = TAU * k / 36
        ca, sa = math.cos(a), math.sin(a)
        tx, tz = -sa, ca
        cx, cz = ca * 32.0, sa * 32.0
        if k % 3 == 0:
            pts = [(cx + ca * 0.9, 0.075, cz + sa * 0.9), (cx + tx * 0.6, 0.075, cz + tz * 0.6), (cx - ca * 0.9, 0.075, cz - sa * 0.9), (cx - tx * 0.6, 0.075, cz - tz * 0.6)]
        else:
            pts = [(cx + tx * 0.18 + ca * 0.8, 0.075, cz + tz * 0.18 + sa * 0.8), (cx - tx * 0.18 + ca * 0.8, 0.075, cz - tz * 0.18 + sa * 0.8),
                   (cx - tx * 0.18 - ca * 0.8, 0.075, cz - tz * 0.18 - sa * 0.8), (cx + tx * 0.18 - ca * 0.8, 0.075, cz + tz * 0.18 - sa * 0.8)]
        W_oriented(mb, pts, (0, 1, 0), bands[GLOW], 1.0)
    return mb.object("HB_PlazaConceptGlow", coll, mat)


CONCEPT = [sanctum, sanctum_glass, sanctum_crystal, sanctum_runes, crystal_lamp, crystal_lamp_glow, plaza_concept, plaza_concept_glow]


def build(pieces=CONCEPT):
    img, bands = W.atlas_image("Hub_CelestialAtlas", 512, HUB_STRIPS)
    mat = W.textured_material("Hub_CelestialMat", img)
    coll = W.collection("Hub_Celestial")
    W.clear_collection(coll)
    global MARBLE_BAND, GOLD_BAND
    MARBLE_BAND, GOLD_BAND = bands[MARBLE], bands[GOLD]
    return [fn(coll, mat, bands) for fn in pieces], img


# ---------- shared building helpers ----------
def slab_box(mb, bands, centre, size, band=MARBLE, trim=GOLD, trim_h=0.25):
    """A marble block with a gold band round its top edge."""
    x, y, z = centre
    sx, sy, sz = size
    mb.box((x, y, z), size, bands[band], u=0.5, top_shade=0.95, side_shade=0.7)
    # (its top a hair under the marble's: level with it, the two surfaces fought and rendered black)
    mb.box((x, y + sy / 2 - trim_h / 2 - 0.03, z), (sx + 0.14, trim_h, sz + 0.14), bands[trim], u=0.5, top_shade=1.0, side_shade=0.85)


def panel(mb, bands, centre, size, facing_z=1):
    """A sign's lapis face in a gold frame (the game writes the name on it), facing +Z (or -Z)."""
    x, y, z = centre
    w, h = size
    mb.box((x, y, z - facing_z * 0.2), (w + 0.8, h + 0.7, 0.4), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.85)
    W_oriented(mb, [(x - w / 2, y - h / 2, z + facing_z * 0.01), (x + w / 2, y - h / 2, z + facing_z * 0.01), (x + w / 2, y + h / 2, z + facing_z * 0.01),
                    (x - w / 2, y + h / 2, z + facing_z * 0.01)], (0, 0, facing_z), bands[LAPIS], 0.6)


def egg_shape(mb, centre, r, band, seg=16, shade=(1.0, 0.7)):
    """An egg standing on end."""
    cx, cy, cz = centre
    prof = []
    for i in range(9):
        t = i / 8                                      # 0 top .. 1 bottom
        a = math.pi * t
        rr = r * math.sin(a) * (0.82 + 0.18 * t)
        y = cy + r * 1.3 * math.cos(a) * (1.0 if a < math.pi / 2 else 0.85)
        prof.append((max(rr, 0.0), y, shade[0] + (shade[1] - shade[0]) * t))
    mb.lathe(prof, seg, band, centre=(cx, 0, cz), cap_top=False)


# ---------- the Marketplace: a crescent arcade of marble, stalls under floating crystal canopies, a crystal egg at its heart ----------
MK_R, MK_COLS, MK_TOP = 15.0, 9, 12.0
MK_ARC = (200.0, 340.0)                                 # the arcade's sweep, behind (degrees round its centre; 270 straight back)
MK_STALLS = (214.0, 242.0, 270.0, 298.0, 326.0)
MK_EGG_Y = 7.0
MK_SIGN = ((0.0, MK_TOP + 1.05, -MK_R + 1.95), (6.5, 1.4))   # (9 wide, its ends sank behind the curved beam: "arketplac", seen in Studio)
MK_PROMPT = (0.0, 1.8, 5.2)


def _arc_xz(a, r):
    return (math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r)


def market(coll, mat, bands):
    global MARBLE_BAND, GOLD_BAND
    MARBLE_BAND, GOLD_BAND = bands[MARBLE], bands[GOLD]
    mb = W.MeshBuilder()
    # the floor: a round marble terrace, two steps, gold edged, a lapis ring
    drum(mb, 19.0, -0.6, 0.45, bands[MARBLE], shade=(0.95, 0.6))
    ring(mb, 18.65, 19.0, 0.46, bands[GOLD])
    drum(mb, 17.2, 0.4, 0.9, bands[MARBLE], shade=(0.95, 0.62))
    ring(mb, 16.85, 17.2, 0.91, bands[GOLD])
    ring(mb, 6.2, 7.6, 0.92, bands[LAPIS], shade=0.8)
    ring(mb, 7.6, 7.85, 0.925, bands[GOLD])
    # the arcade's columns and its curved entablature
    a0, a1 = MK_ARC
    for i in range(MK_COLS):
        a = a0 + (a1 - a0) * i / (MK_COLS - 1)
        x, z = _arc_xz(a, MK_R)
        column(mb, x, z, 0.9, MK_TOP, r=0.6)
    seg = 40
    for k in range(seg):
        b0, b1 = a0 - 3 + (a1 - a0 + 6) * k / seg, a0 - 3 + (a1 - a0 + 6) * (k + 1) / seg
        for (r_in, r_out, y0, y1, band) in ((MK_R - 1.3, MK_R + 1.3, MK_TOP, MK_TOP + 2.0, MARBLE), (MK_R - 1.45, MK_R + 1.45, MK_TOP + 2.0, MK_TOP + 2.35, GOLD)):
            p = [_arc_xz(b0, r_out), _arc_xz(b1, r_out), _arc_xz(b1, r_in), _arc_xz(b0, r_in)]
            W_oriented(mb, [(p[0][0], y1, p[0][1]), (p[1][0], y1, p[1][1]), (p[2][0], y1, p[2][1]), (p[3][0], y1, p[3][1])], (0, 1, 0), bands[band], 0.95)
            W_oriented(mb, [(p[0][0], y0, p[0][1]), (p[1][0], y0, p[1][1]), (p[1][0], y1, p[1][1]), (p[0][0], y1, p[0][1])],
                       (p[0][0] + p[1][0], 0, p[0][1] + p[1][1]), bands[band], 0.75)
            W_oriented(mb, [(p[3][0], y0, p[3][1]), (p[2][0], y0, p[2][1]), (p[2][0], y1, p[2][1]), (p[3][0], y1, p[3][1])],
                       (-(p[2][0] + p[3][0]), 0, -(p[2][1] + p[3][1])), bands[band], 0.8)
            W_oriented(mb, [(p[0][0], y0, p[0][1]), (p[1][0], y0, p[1][1]), (p[2][0], y0, p[2][1]), (p[3][0], y0, p[3][1])], (0, -1, 0), bands[SHADE], 0.5)
    # the entablature's two ends, capped
    for b in (a0 - 3, a1 + 3):
        for (r_in, r_out, y0, y1, band) in ((MK_R - 1.3, MK_R + 1.3, MK_TOP, MK_TOP + 2.0, MARBLE), (MK_R - 1.45, MK_R + 1.45, MK_TOP + 2.0, MK_TOP + 2.35, GOLD)):
            p0, p1 = _arc_xz(b, r_in), _arc_xz(b, r_out)
            t = math.radians(b)
            out = (-math.sin(t), 0, math.cos(t)) if b > 270 else (math.sin(t), 0, -math.cos(t))
            W_oriented(mb, [(p0[0], y0, p0[1]), (p1[0], y0, p1[1]), (p1[0], y1, p1[1]), (p0[0], y1, p0[1])], out, bands[band], 0.8)
    # a gold crest along the top, with little crystal finials at the ends and the middle (the finials glow: market_glow)
    for a in (a0 - 3, 270.0, a1 + 3):
        x, z = _arc_xz(a, MK_R)
        mb.lathe([(0.0, MK_TOP + 3.6, 1.0), (0.45, MK_TOP + 3.0, 0.9), (0.5, MK_TOP + 2.35, 0.8)], 8, bands[GOLD], centre=(x, 0, z), cap_top=False)
    # the stalls: a marble counter with a gold top, a lapis front panel, goods on it, and a gold mount for its canopy above
    for i, a in enumerate(MK_STALLS):
        x, z = _arc_xz(a, MK_R - 4.2)
        yaw = math.atan2(-x, -z)
        mb.box((x, 1.9, z), (5.2, 2.0, 1.8), bands[MARBLE], yaw=yaw, u=0.5, top_shade=0.95, side_shade=0.7)
        mb.box((x, 2.97, z), (5.5, 0.18, 2.1), bands[GOLD], yaw=yaw, u=0.5, top_shade=1.0, side_shade=0.85)
        fx, fz = math.sin(yaw), math.cos(yaw)
        mb.box((x + fx * 0.92, 1.9, z + fz * 0.92), (4.4, 1.3, 0.05), bands[LAPIS], yaw=yaw, u=0.5, top_shade=0.7, side_shade=0.7)
        # goods: eggs on little gold stands, a box of stones
        for j, s in enumerate((-1.6, 0.0, 1.6)):
            ex, ez = x + math.cos(yaw) * s, z - math.sin(yaw) * s
            if i % 2 == 0 or j != 1:
                mb.lathe([(0.35, 3.25, 1.0), (0.25, 3.06, 0.8)], 8, bands[GOLD], centre=(ex, 0, ez), cap_top=True)
                egg_shape(mb, (ex, 3.75, ez), 0.42, bands[(LAPIS, MARBLE2, CRYSTAL)[(i + j) % 3]], seg=10)
            else:
                mb.box((ex, 3.35, ez), (1.1, 0.5, 0.8), bands[SLATE], yaw=yaw, u=0.5, top_shade=0.8, side_shade=0.6)
        # the canopy's mount: a slim gold post behind the counter rising to a ring
        px, pz = _arc_xz(a, MK_R - 2.6)
        mb.lathe([(0.12, 8.0, 1.0), (0.16, 0.9, 0.8)], 6, bands[GOLD], centre=(px, 0, pz), cap_top=True)
    # the heart: a round plinth of three tiers, a gold ring stand and (market_glow) a great crystal egg floating in it
    drum(mb, 4.2, 0.9, 1.6, bands[MARBLE], seg=32)
    ring(mb, 3.85, 4.2, 1.61, bands[GOLD], seg=32)
    drum(mb, 3.2, 1.6, 2.4, bands[MARBLE], seg=32)
    drum(mb, 2.2, 2.4, 3.0, bands[LAPIS], seg=32, shade=(0.8, 0.6))
    pts = [(3.4 * math.sin(TAU * i / 40), MK_EGG_Y + 3.4 * math.cos(TAU * i / 40), 0.0) for i in range(41)]
    tube(mb, pts, 0.18, bands[GOLD], sides=6, shade=1.0, caps=False)              # a gold ring standing round the egg
    tube(mb, [(0.0, 3.0, 0.0), (0.0, MK_EGG_Y - 3.4, 0.0)], 0.22, bands[GOLD], sides=6, shade=0.95)
    panel(mb, bands, *MK_SIGN)
    return mb.object("HB_Market", coll, mat)


def market_canopies(coll, mat, bands):
    """The stalls' floating crystal canopies: a flat hexagonal pane each, tilted toward the plaza (glass)."""
    mb = W.MeshBuilder()
    for a in MK_STALLS:
        x, z = _arc_xz(a, MK_R - 3.8)
        out = math.atan2(-x, -z)
        tilt = 0.18
        pts = []
        for k in range(6):
            b = TAU * k / 6
            px, pz = math.cos(b) * 3.4, math.sin(b) * 3.4
            # tilt toward the centre: lower on the side facing it
            toward = px * math.sin(out) + pz * math.cos(out)
            pts.append((x + px, 8.6 - toward * tilt, z + pz))
        top = [(p[0], p[1] + 0.12, p[2]) for p in pts]
        W_oriented(mb, top, (0, 1, 0), bands[CRYSTAL], 0.9)
        W_oriented(mb, pts, (0, -1, 0), bands[CRYSTAL], 0.6)
        for k in range(6):
            k2 = (k + 1) % 6
            W_oriented(mb, [pts[k], pts[k2], top[k2], top[k]], (pts[k][0] + pts[k2][0] - 2 * x, 0, pts[k][2] + pts[k2][2] - 2 * z), bands[CRYSTAL], 0.8)
    return mb.object("HB_MarketCanopy", coll, mat)


def market_glow(coll, mat, bands):
    """The great crystal egg at the market's heart and the crests' crystal finials."""
    mb = W.MeshBuilder()
    egg_shape(mb, (0.0, MK_EGG_Y, 0.0), 2.3, bands[GLOW], seg=20, shade=(1.0, 0.85))
    a0, a1 = MK_ARC
    for a in (a0 - 3, 270.0, a1 + 3):
        x, z = _arc_xz(a, MK_R)
        gem(mb, (x, MK_TOP + 4.4, z), 0.4, 0.8, bands[GLOW], sides=6)
    return mb.object("HB_MarketGlow", coll, mat)


# ---------- the Blacksmith: the Celestial Forge ----------
# (rejected: a flat-roofed marble hall with a slate chimney, "The blacksmith is terrible", "That looks generic"; a floating
# star-and-swords forge was drafted next and dropped unshown, a toy, not a building.)
# A working forge hall: a barrel vault roofed in lapis on gold ribs, open in front under a great arch and between its piers
# along both sides (a forge needs air); at its far end the hearth glows under a marble hood, and behind it the furnace tower
# rises to a gold crown holding the forge's fire crystal, seen across the hub. On the floor the anvil, a quench trough, a
# grindstone, racks of steel blades; the name hangs on chains under the front arch.
BS_FLOOR = 1.0
BS_SPRING, BS_RIN, BS_ROUT = 7.0, 7.4, 8.4                # the vault: where it springs, its inner and outer radius
BS_FRONT, BS_BACK = 6.0, -12.0                           # the hall's open front and its back wall's inner face
BS_PIERS = (-0.4, -6.0)                                  # the side piers' z (the front arch's pilasters and the back wall frame them)
BS_TOWER = (0.0, -17.0)
BS_CROWN = 25.0
BS_SIGN = ((0.0, 11.3, BS_FRONT - 0.3), (8.5, 1.5))
BS_PROMPT = (0.0, 2.6, 4.2)
BS_CORE = (0.0, 3.4, -9.6)                               # the Forge effect: in the hearth's mouth, sparks thrown toward the anvil
BS_SMOKE = (0.0, BS_CROWN + 5.0, BS_TOWER[1])


def blade(mb, bands, base, d, sd, t, length, w, th=0.18, band=None):
    """A blade of diamond section from base along d, its flat across sd, tapering to a point."""
    band = bands[STEEL] if band is None else band
    rings = []
    for f, ww in ((0.0, w), (0.78, w * 0.86)):
        c = base + d * length * f
        rings.append([c + sd * ww / 2, c + t * th / 2, c - sd * ww / 2, c - t * th / 2])
    tip = base + d * length
    for k in range(4):
        k2 = (k + 1) % 4
        a, b = rings[0][k], rings[0][k2]
        mid = (a + b) / 2 - base
        W_oriented(mb, [tuple(a), tuple(b), tuple(rings[1][k2]), tuple(rings[1][k])], tuple(mid), band, 0.9)
        W_oriented(mb, [tuple(rings[1][k]), tuple(rings[1][k2]), tuple(tip)], tuple(mid), band, 0.9)
    W_oriented(mb, [tuple(q) for q in rings[0]], tuple(-d), band, 0.8)


def weapon_rack(mb, bands, x, z, facing):
    """A gold-framed rack against the back wall: three swords and two spears standing in it, points up."""
    from mathutils import Vector
    y0 = BS_FLOOR
    sd = Vector((1, 0, 0))
    t = Vector((0, 0, facing))
    up = Vector((0, 1, 0))
    mb.box((x, y0 + 0.3, z), (3.6, 0.6, 1.0), bands[MARBLE], u=0.5, top_shade=0.95, side_shade=0.7)
    for dx in (-1.75, 1.75):
        mb.box((x + dx, y0 + 2.6, z), (0.2, 4.6, 0.2), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.85)
    for yy in (y0 + 1.9, y0 + 4.6):
        mb.box((x, yy, z), (3.7, 0.18, 0.24), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.85)
    for k, dx in enumerate((-1.2, -0.6, 0.0, 0.6, 1.2)):
        p = Vector((x + dx, y0 + 0.6, z))
        if k % 2 == 0:   # a sword: lapis grip, gold guard, steel blade
            tube(mb, [tuple(p), tuple(p + up * 0.9)], 0.07, bands[LAPIS], sides=6, shade=0.8)
            mb.box(tuple(p + up * 0.95), (0.55, 0.1, 0.14), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.85)
            blade(mb, bands, p + up * 1.0, up, sd, t, 3.6, 0.22)
        else:            # a spear: a gold-shod shaft, a leaf head
            tube(mb, [tuple(p), tuple(p + up * 4.4)], 0.06, bands[SLATE], sides=6, shade=0.8)
            tube(mb, [tuple(p + up * 4.3), tuple(p + up * 4.6)], 0.09, bands[GOLD], sides=6, shade=1.0)
            blade(mb, bands, p + up * 4.6, up, sd, t, 1.1, 0.3)


def prism(mb, poly, z0, z1, band, shade=0.85):
    """A convex polygon in the x-y plane, extruded from z0 to z1 (caps and sides)."""
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    W_oriented(mb, [(x, y, z1) for x, y in poly], (0, 0, 1), band, shade)
    W_oriented(mb, [(x, y, z0) for x, y in poly], (0, 0, -1), band, shade * 0.8)
    for i in range(len(poly)):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % len(poly)]
        mx, my = (ax + bx) / 2 - cx, (ay + by) / 2 - cy
        W_oriented(mb, [(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)], (mx, my, 0), band, shade * (0.75 + 0.25 * max(0.0, my) / (abs(mx) + abs(my) + 1e-6)))


def blacksmith(coll, mat, bands):
    global MARBLE_BAND, GOLD_BAND
    MARBLE_BAND, GOLD_BAND = bands[MARBLE], bands[GOLD]
    mb = W.MeshBuilder()
    F = BS_FLOOR
    # the podium: two marble tiers, gold edged, under the hall and the tower
    slab_box(mb, bands, (0, -0.1, -6.5), (24.0, 1.1, 33.0))
    slab_box(mb, bands, (0, 0.7, -6.5), (22.0, 0.6, 31.0))
    # the hall's floor: a lapis runner up the middle between gold lines
    mb.box((0, F + 0.02, (BS_FRONT + BS_BACK) / 2), (4.0, 0.04, BS_FRONT - BS_BACK), bands[LAPIS], u=0.5, top_shade=0.8, side_shade=0.6)
    for x in (-2.15, 2.15):
        mb.box((x, F + 0.03, (BS_FRONT + BS_BACK) / 2), (0.3, 0.06, BS_FRONT - BS_BACK), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.85)
    # the side piers (gold base and capital) and the beam along each side carrying the vault
    xs = (BS_RIN + BS_ROUT) / 2
    for side in (-1, 1):
        x = side * xs
        for z in BS_PIERS:
            mb.box((x, F + 0.35, z), (1.9, 0.7, 2.1), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.8)
            mb.box((x, F + (BS_SPRING - 1.0 - F) / 2 + 0.35, z), (1.4, BS_SPRING - 1.0 - F - 0.7, 1.6), bands[MARBLE], u=0.5, top_shade=0.95, side_shade=0.72)
            mb.box((x, BS_SPRING - 1.25, z), (1.9, 0.5, 2.1), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.8)
            # a buttress leaning on the pier outside, its back sloping from the pier's capital down to a gold-capped foot
            xi, xo = x + side * 0.7, x + side * 2.6
            prism(mb, [(xi, F), (xo, F), (xo, F + 1.3), (xi, BS_SPRING - 1.5)], z - 0.6, z + 0.6, bands[MARBLE])
            mb.box(((xi + xo) / 2 + side * 0.55, F + 0.15, z), (abs(xo - xi) - 0.9, 0.3, 1.4), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.85)
        mb.box((x, BS_SPRING - 0.5, (BS_FRONT + BS_BACK) / 2 - 0.4), (1.5, 1.0, BS_FRONT - BS_BACK + 0.8), bands[MARBLE], u=0.5, top_shade=0.95, side_shade=0.72)
    # the back wall, up to the vault's springing, and the half-moon of wall under the vault
    mb.box((0, (F + BS_SPRING) / 2, BS_BACK - 0.5), (2 * BS_ROUT, BS_SPRING - F, 1.0), bands[MARBLE], u=0.5, top_shade=0.95, side_shade=0.72)
    seg = 28
    for k in range(seg):
        a0, a1 = math.pi * k / seg, math.pi * (k + 1) / seg
        for zz, want in ((BS_BACK, 1), (BS_BACK - 1.0, -1)):
            W_oriented(mb, [(0.0, BS_SPRING, zz), (math.cos(a0) * BS_RIN, BS_SPRING + math.sin(a0) * BS_RIN, zz),
                            (math.cos(a1) * BS_RIN, BS_SPRING + math.sin(a1) * BS_RIN, zz)], (0, 0, want), bands[MARBLE], 0.8)
    # the vault: lapis outside, marble soffit inside, its front edge a marble band, gold ribs over each pier and round the arch
    z0, z1 = BS_BACK - 1.0, BS_FRONT
    for k in range(seg):
        a0, a1 = math.pi * k / seg, math.pi * (k + 1) / seg
        c0, s0, c1, s1 = math.cos(a0), math.sin(a0), math.cos(a1), math.sin(a1)
        o = lambda c, s_, z: (c * BS_ROUT, BS_SPRING + s_ * BS_ROUT, z)
        n = lambda c, s_, z: (c * BS_RIN, BS_SPRING + s_ * BS_RIN, z)
        W_oriented(mb, [o(c0, s0, z0), o(c1, s1, z0), o(c1, s1, z1), o(c0, s0, z1)], ((c0 + c1), (s0 + s1), 0), bands[LAPIS], 0.6 + 0.35 * (s0 + s1) / 2)
        W_oriented(mb, [n(c0, s0, z0), n(c1, s1, z0), n(c1, s1, z1), n(c0, s0, z1)], (-(c0 + c1), -(s0 + s1), 0), bands[MARBLE], 0.75)
        W_oriented(mb, [n(c0, s0, z1), n(c1, s1, z1), o(c1, s1, z1), o(c0, s0, z1)], (0, 0, 1), bands[MARBLE], 0.9)
    arc = lambda r, z, n_=33: [(math.cos(math.pi * i / (n_ - 1)) * r, BS_SPRING + math.sin(math.pi * i / (n_ - 1)) * r, z) for i in range(n_)]
    for z in BS_PIERS[1:] + (BS_BACK - 0.6,):
        tube(mb, arc(BS_ROUT + 0.15, z), 0.38, bands[GOLD], sides=8, shade=1.0, caps=False)
        tube(mb, arc(BS_RIN - 0.12, z), 0.22, bands[GOLD], sides=6, shade=0.95, caps=False)
    tube(mb, arc(BS_ROUT + 0.2, BS_FRONT - 0.35), 0.45, bands[GOLD], sides=8, shade=1.0, caps=False)
    tube(mb, arc(BS_RIN + 0.05, BS_FRONT + 0.12), 0.2, bands[GOLD], sides=6, shade=1.0, caps=False)
    tube(mb, [(0, BS_SPRING + BS_ROUT + 0.5, BS_BACK - 1.0), (0, BS_SPRING + BS_ROUT + 0.5, BS_FRONT - 0.3)], 0.32, bands[GOLD], sides=8, shade=1.0)
    # the front arch's feet: marble pilasters with gold capitals, and a keystone over the crown
    for side in (-1, 1):
        x = side * xs
        mb.box((x, F + 0.35, BS_FRONT + 0.3), (2.0, 0.7, 1.0), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.8)
        mb.box((x, (F + BS_SPRING) / 2 + 0.1, BS_FRONT + 0.3), (1.6, BS_SPRING - F - 0.9, 0.8), bands[MARBLE], u=0.5, top_shade=0.95, side_shade=0.75)
        mb.box((x, BS_SPRING - 0.3, BS_FRONT + 0.3), (2.0, 0.6, 1.0), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.8)
    ky = BS_SPRING + BS_RIN
    prism(mb, [(-0.55, ky - 0.4), (0.55, ky - 0.4), (0.85, ky + 1.5), (-0.85, ky + 1.5)], BS_FRONT - 0.5, BS_FRONT + 0.75, bands[MARBLE], 0.95)
    mb.box((0, ky + 1.62, BS_FRONT + 0.12), (1.9, 0.25, 1.4), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.85)
    # the hearth at the far end: a slate firebox, its mouth an arch of gold (the fire: blacksmith_core), under a tapering hood
    hz = BS_BACK + 1.3
    mb.box((0, F + 2.6, hz), (6.4, 5.2, 2.6), bands[SLATE], u=0.5, top_shade=0.8, side_shade=0.6)
    mb.box((0, F + 5.35, hz + 0.1), (7.0, 0.5, 3.0), bands[MARBLE], u=0.5, top_shade=0.95, side_shade=0.75)
    mb.box((0, F + 5.05, hz + 0.15), (7.2, 0.2, 3.1), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.85)
    pts = [(math.cos(math.pi * i / 16) * 1.9, F + 2.2 + math.sin(math.pi * i / 16) * 1.9, hz + 1.35) for i in range(17)]
    tube(mb, pts, 0.26, bands[GOLD], sides=6, shade=1.0)
    for x in (-1.9, 1.9):
        tube(mb, [(x, F + 0.1, hz + 1.35), (x, F + 2.2, hz + 1.35)], 0.26, bands[GOLD], sides=6, shade=1.0)
    mb.lathe([(1.6, BS_SPRING + BS_RIN - 0.6, 0.9), (3.8, F + 5.6, 0.7)], 4, bands[MARBLE], centre=(0, 0, hz - 0.2), phase=math.pi / 4, cap_top=False)
    # the furnace tower behind: a square marble base, an octagonal shaft banded in gold, a gold crown (its fire: blacksmith_core)
    tx, tz = BS_TOWER
    mb.lathe([(6.4, 14.0, 0.95), (6.4, F, 0.7)], 4, bands[MARBLE], centre=(tx, 0, tz), phase=math.pi / 4, cap_top=True)
    mb.lathe([(6.75, 14.4, 1.0), (6.75, 13.8, 0.85)], 4, bands[GOLD], centre=(tx, 0, tz), phase=math.pi / 4, cap_top=True)
    mb.lathe([(2.6, BS_CROWN, 0.9), (3.3, 14.4, 0.7)], 8, bands[MARBLE], centre=(tx, 0, tz), phase=math.pi / 8, cap_top=False)
    for y in (18.0, 21.8):
        mb.lathe([(3.25 - (y - 14.4) * 0.065, y + 0.3, 1.0), (3.32 - (y - 14.4) * 0.065, y - 0.3, 0.85)], 8, bands[GOLD], centre=(tx, 0, tz), phase=math.pi / 8, cap_top=False)
    mb.lathe([(3.6, BS_CROWN + 1.3, 1.0), (3.3, BS_CROWN + 0.6, 0.9), (2.5, BS_CROWN - 0.3, 0.8)], 8, bands[GOLD], centre=(tx, 0, tz), phase=math.pi / 8, cap_top=False)
    for k in range(4):    # the crown's four prongs curling in round the fire crystal
        a = TAU * k / 4 + TAU / 8
        tube(mb, [(tx + math.cos(a) * 3.4, BS_CROWN + 1.2, tz + math.sin(a) * 3.4), (tx + math.cos(a) * 3.0, BS_CROWN + 3.4, tz + math.sin(a) * 3.0),
                  (tx + math.cos(a) * 1.7, BS_CROWN + 5.0, tz + math.sin(a) * 1.7)], lambda f: 0.32 - 0.2 * f, bands[GOLD], sides=6, shade=1.0)
    # the anvil on a marble block
    az = 0.6
    slab_box(mb, bands, (0, F + 0.35, az), (3.2, 0.7, 2.2))
    mb.box((0, F + 1.0, az), (2.6, 0.6, 1.7), bands[SLATE], u=0.5, top_shade=0.8, side_shade=0.6)
    mb.box((0, F + 1.75, az), (1.2, 0.9, 1.0), bands[SLATE], u=0.5, top_shade=0.8, side_shade=0.6)
    mb.box((0, F + 2.55, az), (3.0, 0.7, 1.3), bands[SLATE], u=0.5, top_shade=0.85, side_shade=0.65)
    tube(mb, [(1.5, F + 2.6, az), (2.4, F + 2.68, az), (3.3, F + 2.85, az)], lambda f: 0.48 - 0.42 * f, bands[SLATE], sides=8, shade=0.8)
    mb.box((-1.75, F + 2.65, az), (0.5, 0.5, 0.9), bands[SLATE], u=0.5, top_shade=0.8, side_shade=0.6)
    mb.box((-0.9, F + 3.15, az - 0.2), (0.5, 0.5, 1.1), bands[STEEL], u=0.5, top_shade=1.0, side_shade=0.8)
    tube(mb, [(-0.9, F + 3.12, az + 0.3), (-1.05, F + 3.05, az + 1.4), (-1.15, F + 2.95, az + 2.1)], 0.12, bands[LAPIS], sides=6, shade=0.85)
    # the quench trough and the grindstone, either side of the hall
    slab_box(mb, bands, (-4.6, F + 0.6, -4.0), (1.8, 1.2, 4.2))
    mb.box((-4.6, F + 1.08, -4.0), (1.3, 0.04, 3.7), bands[CRYSTAL], u=0.5, top_shade=0.9, side_shade=0.8)
    for dz in (-0.9, 0.9):
        mb.box((4.6, F + 1.2, -4.0 + dz), (0.5, 2.4, 0.5), bands[MARBLE], u=0.5, top_shade=0.95, side_shade=0.72)
    tube(mb, [(4.6, F + 2.1, -4.0 - 0.55), (4.6, F + 2.1, -4.0 + 0.55)], 1.45, bands[SLATE], sides=20, shade=0.8)
    tube(mb, [(4.6, F + 2.1, -4.0 - 1.3), (4.6, F + 2.1, -4.0 + 1.3)], 0.12, bands[GOLD], sides=6, shade=1.0)
    # weapon racks against the back wall, either side of the hearth
    for x in (-5.3, 5.3):
        weapon_rack(mb, bands, x, BS_BACK + 0.5, 1)
    # the name board, hung on gold chains under the front arch
    (sx, sy, sz_), (sw, sh) = BS_SIGN
    for x in (-3.4, 3.4):
        top = BS_SPRING + math.sqrt(BS_RIN ** 2 - x * x)
        tube(mb, [(x, top + 0.2, sz_ - 0.2), (x, sy + sh / 2 + 0.3, sz_ - 0.2)], 0.07, bands[GOLD], sides=4, shade=1.0)
    panel(mb, bands, *BS_SIGN)
    return mb.object("HB_Blacksmith", coll, mat)


def disc(mb, centre, r, y, band, seg=32, shade=1.0):
    cx, cz = centre
    for k in range(seg):
        a0, a1 = TAU * k / seg, TAU * (k + 1) / seg
        W_oriented(mb, [(cx, y, cz), (cx + math.cos(a0) * r, y, cz + math.sin(a0) * r), (cx + math.cos(a1) * r, y, cz + math.sin(a1) * r)], (0, 1, 0), band, shade)


def blacksmith_core(coll, mat, bands):
    """The fire: the hearth's mouth, the fire crystal in the tower's crown, the blade glowing on the anvil (Neon orange)."""
    mb = W.MeshBuilder()
    F = BS_FLOOR
    hz = BS_BACK + 1.3 + 1.32
    for k in range(16):
        t0, t1 = math.pi * k / 16, math.pi * (k + 1) / 16
        W_oriented(mb, [(0, F + 2.2, hz), (math.cos(t0) * 1.75, F + 2.2 + math.sin(t0) * 1.75, hz), (math.cos(t1) * 1.75, F + 2.2 + math.sin(t1) * 1.75, hz)],
                   (0, 0, 1), bands[GLOW], 1.0)
    W_oriented(mb, [(-1.75, F + 0.1, hz), (1.75, F + 0.1, hz), (1.75, F + 2.2, hz), (-1.75, F + 2.2, hz)], (0, 0, 1), bands[GLOW], 1.0)
    tx, tz = BS_TOWER
    crystal_cluster(mb, (tx, BS_CROWN + 2.6, tz), 4.2, bands[GLOW], turn=0.4)
    # the furnace's vents: a narrow glowing slit on four faces of the tower's shaft, under the crown
    for k in range(4):
        a = TAU * k / 4 + TAU / 16 + TAU / 8   # (the middle of an octagon face)
        r = 2.95 - 0.02
        c, s_ = math.cos(a), math.sin(a)
        sx, sz = -s_ * 0.22, c * 0.22
        x0, z0 = tx + c * (r + 0.02), tz + s_ * (r + 0.02)
        W_oriented(mb, [(x0 - sx, 19.2, z0 - sz), (x0 + sx, 19.2, z0 + sz), (x0 + sx, 21.2, z0 + sz), (x0 - sx, 21.2, z0 - sz)], (c, 0, s_), bands[GLOW], 1.0)
    mb.box((0.5, F + 2.95, 0.6), (2.0, 0.1, 0.3), bands[GLOW], u=0.5, top_shade=1.0, side_shade=1.0)
    return mb.object("HB_BlacksmithCore", coll, mat)


def blacksmith_crystal(coll, mat, bands):
    """The white crystal set in the front arch's keystone."""
    mb = W.MeshBuilder()
    gem(mb, (0.0, BS_SPRING + BS_RIN + 2.45, BS_FRONT + 0.12), 0.5, 1.1, bands[GLOW], sides=6)
    return mb.object("HB_BlacksmithCrystal", coll, mat)


# ---------- Buy & Sell: a gilded round vault with a great vault door, a giant scale floating over it ----------
BV_C, BV_R, BV_H = (0.0, -6.0), 10.0, 12.0
BV_SCALE_Y, BV_PAN_X, BV_PAN_Y = 22.0, 12.5, 11.5
BV_SIGN = ((0.0, BV_H + 1.2, BV_C[1] + BV_R + 0.6), (8.0, 1.4))
BV_PROMPT = (0.0, 2.2, 10.6)


def buy_sell(coll, mat, bands):
    global MARBLE_BAND, GOLD_BAND
    MARBLE_BAND, GOLD_BAND = bands[MARBLE], bands[GOLD]
    mb = W.MeshBuilder()
    cx, cz = BV_C
    # the platform: a round marble base under the vault and a forecourt step
    drum(mb, 18.0, -0.6, 0.5, bands[MARBLE], centre=(0.0, -2.0), shade=(0.95, 0.6))
    ring(mb, 17.65, 18.0, 0.51, bands[GOLD], centre=(0.0, -2.0))
    ring(mb, 12.5, 14.0, 0.52, bands[LAPIS], centre=(0.0, -2.0), shade=0.8)
    # the vault: a marble drum banded in gold, a shallow dome, a gold finial
    drum(mb, BV_R, 0.5, BV_H, bands[MARBLE], centre=BV_C, top=False, shade=(0.95, 0.68))
    for y in (1.2, BV_H - 0.6, 6.0):
        mb.lathe([(BV_R + 0.12, y + 0.25, 1.0), (BV_R + 0.12, y - 0.25, 0.85)], 48, bands[GOLD], centre=(cx, 0, cz), cap_top=False)
    prof = [(0.0, BV_H + 4.2, 1.0)] + [(BV_R * math.sin(math.pi / 2 * t / 6), BV_H + 4.2 * math.cos(math.pi / 2 * t / 6), 0.95 - 0.2 * t / 6) for t in range(1, 7)]
    mb.lathe(prof, 48, bands[MARBLE], centre=(cx, 0, cz), cap_top=False)
    mb.lathe([(0.0, BV_H + 6.4, 1.0), (0.5, BV_H + 5.6, 0.95), (0.9, BV_H + 4.6, 0.85), (1.3, BV_H + 4.1, 0.8)], 12, bands[GOLD], centre=(cx, 0, cz), cap_top=False)
    # the vault door on its front: a marble frame, a gold door of rings, bolts round it and a spoked wheel
    dz = cz + BV_R + 0.05
    dy = 5.6
    for (r0, r1, band, z, sh) in ((5.4, 6.4, MARBLE, 0.25, 0.9), (0.0, 5.4, GOLD, 0.35, 0.85), (3.6, 4.0, GOLD, 0.55, 1.0), (1.2, 1.6, GOLD, 0.6, 1.0)):
        for k in range(32):
            a0, a1 = TAU * k / 32, TAU * (k + 1) / 32
            W_oriented(mb, [(math.cos(a0) * r1, dy + math.sin(a0) * r1, dz + z), (math.cos(a1) * r1, dy + math.sin(a1) * r1, dz + z),
                            (math.cos(a1) * r0, dy + math.sin(a1) * r0, dz + z), (math.cos(a0) * r0, dy + math.sin(a0) * r0, dz + z)], (0, 0, 1), bands[band], sh)
    for k in range(32):   # the door's rim, standing out
        a0, a1 = TAU * k / 32, TAU * (k + 1) / 32
        W_oriented(mb, [(math.cos(a0) * 5.4, dy + math.sin(a0) * 5.4, dz + 0.35), (math.cos(a1) * 5.4, dy + math.sin(a1) * 5.4, dz + 0.35),
                        (math.cos(a1) * 5.4, dy + math.sin(a1) * 5.4, dz - 0.4), (math.cos(a0) * 5.4, dy + math.sin(a0) * 5.4, dz - 0.4)],
                   (math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 0), bands[GOLD], 0.8)
    for k in range(8):    # bolts
        a = TAU * k / 8
        mb.box((math.cos(a) * 4.7, dy + math.sin(a) * 4.7, dz + 0.55), (0.45, 0.45, 0.4), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.8)
    for k in range(6):    # the wheel's spokes, standing off the door
        a = TAU * k / 6
        tube(mb, [(0.0, dy, dz + 1.1), (math.cos(a) * 2.6, dy + math.sin(a) * 2.6, dz + 1.1)], 0.16, bands[GOLD], sides=6, shade=1.0)
    pts = [(math.cos(TAU * i / 24) * 2.6, dy + math.sin(TAU * i / 24) * 2.6, dz + 1.1) for i in range(25)]
    tube(mb, pts, 0.18, bands[GOLD], sides=6, shade=1.0, caps=False)
    tube(mb, [(0.0, dy, dz + 0.4), (0.0, dy, dz + 1.3)], 0.5, bands[GOLD], sides=8, shade=0.9)
    # the counter in the forecourt
    slab_box(mb, bands, (0.0, 1.6, 9.0), (9.0, 2.2, 1.8))
    mb.box((0.0, 1.6, 9.92), (7.8, 1.4, 0.05), bands[LAPIS], u=0.5, top_shade=0.7, side_shade=0.7)
    # the floating scale over the door: a gold beam, chains, and two pans (one heaped with Spirit Stones, one holding an egg)
    sz = dz + 1.5
    tube(mb, [(-BV_PAN_X, BV_SCALE_Y, sz), (0.0, BV_SCALE_Y + 0.4, sz), (BV_PAN_X, BV_SCALE_Y, sz)], 0.32, bands[GOLD], sides=8, shade=1.0)
    for sx in (-1, 1):
        x = sx * BV_PAN_X
        mb.lathe([(0.0, BV_SCALE_Y + 0.9, 1.0), (0.45, BV_SCALE_Y + 0.4, 0.95), (0.45, BV_SCALE_Y - 0.4, 0.8), (0.0, BV_SCALE_Y - 0.8, 0.7)], 8, bands[GOLD], centre=(x, 0, sz))
        for k in range(3):    # chains
            a = TAU * k / 3 + 0.5
            tube(mb, [(x, BV_SCALE_Y - 0.6, sz), (x + math.cos(a) * 2.6, BV_PAN_Y + 0.5, sz + math.sin(a) * 2.6)], 0.07, bands[GOLD], sides=4, shade=1.0)
        mb.lathe([(2.9, BV_PAN_Y + 0.5, 1.0), (2.6, BV_PAN_Y, 0.9), (1.6, BV_PAN_Y - 0.6, 0.8), (0.0, BV_PAN_Y - 0.7, 0.7)], 20, bands[GOLD], centre=(x, 0, sz), cap_top=False)
        ring(mb, 0.0, 2.75, BV_PAN_Y + 0.35, bands[LAPIS], seg=20, centre=(x, sz), shade=0.7)
    egg_shape(mb, (BV_PAN_X, BV_PAN_Y + 1.7, sz), 1.25, bands[MARBLE2], seg=16)
    panel(mb, bands, *BV_SIGN)
    return mb.object("HB_BuySell", coll, mat)


def buy_sell_glow(coll, mat, bands):
    """The beam's floating crystal pivot and the Spirit Stones heaped in the left pan."""
    mb = W.MeshBuilder()
    sz = BV_C[1] + BV_R + 1.55
    crystal_cluster(mb, (0.0, BV_SCALE_Y + 2.2, sz), 3.2, bands[GLOW], turn=0.3)
    for k, (dx, dz, r) in enumerate(((0, 0, 0.75), (1.0, 0.6, 0.55), (-0.9, 0.7, 0.6), (0.6, -0.9, 0.5), (-0.7, -0.7, 0.5), (1.5, -0.3, 0.4), (-1.6, 0.0, 0.42))):
        gem(mb, (-BV_PAN_X + dx, BV_PAN_Y + 0.6 + r * 0.7, sz + dz), r, r * 1.6, bands[GLOW], sides=6, twist=k)
    return mb.object("HB_BuySellStones", coll, mat)


# ---------- the Qi Spring: a celestial fountain whose water is full of Qi (+50% cultivation inside its rune ring) ----------
# (the owner, 2026-11-12: "We can still add a qi spring that give 50% bonus but a better one")
# A round marble basin of shallow water you can walk into, its floor a glowing lotus seen through the water; a two-tier fountain
# in the middle, water sheeting off each gold-rimmed tier, a crystal lotus on top; eight meditation seats round the pool; a ring of
# runes on the platform marks the bonus's edge (GameConfig.TrainingStation.Radius from the water's centre). The overflow leaves
# by a spout at the back into a channel to the island's edge (hub_ground.spring_channel) and falls as a waterfall.
QS_PLAT_R, QS_PLAT_TOP = 11.2, 0.3
QS_POOL_R, QS_CURB_R, QS_CURB_TOP = 7.0, 7.8, 0.95
QS_FLOOR, QS_WATER = 0.35, 0.8
QS_ZONE_R = 10.0                                         # = GameConfig.TrainingStation.Radius
QS_LOW, QS_HIGH = 4.75, 7.3                              # the two tiers' lips
QS_SEATS = 8


def wall_in(mb, r, y0, y1, band, seg=48, shade=0.75):
    """A round wall seen from inside (its faces point at the middle)."""
    for k in range(seg):
        a0, a1 = TAU * k / seg, TAU * (k + 1) / seg
        W_oriented(mb, [(math.cos(a0) * r, y1, math.sin(a0) * r), (math.cos(a1) * r, y1, math.sin(a1) * r),
                        (math.cos(a1) * r, y0, math.sin(a1) * r), (math.cos(a0) * r, y0, math.sin(a0) * r)],
                   (-math.cos((a0 + a1) / 2), 0, -math.sin((a0 + a1) / 2)), band, shade)


def qi_spring(coll, mat, bands):
    global MARBLE_BAND, GOLD_BAND
    MARBLE_BAND, GOLD_BAND = bands[MARBLE], bands[GOLD]
    mb = W.MeshBuilder()
    # the platform, gold edged
    drum(mb, QS_PLAT_R, -0.4, QS_PLAT_TOP, bands[MARBLE], shade=(0.95, 0.6))
    ring(mb, QS_PLAT_R - 0.35, QS_PLAT_R, QS_PLAT_TOP + 0.01, bands[GOLD])
    # the basin: a marble curb (a gold line along its top), its inner face, a lapis floor
    mb.lathe([(QS_CURB_R, QS_CURB_TOP, 0.9), (QS_CURB_R + 0.15, QS_PLAT_TOP, 0.65)], 64, bands[MARBLE], cap_top=False)
    ring(mb, QS_POOL_R, QS_CURB_R, QS_CURB_TOP, bands[MARBLE], shade=0.95)
    ring(mb, 7.32, 7.48, QS_CURB_TOP + 0.01, bands[GOLD])
    wall_in(mb, QS_POOL_R, QS_FLOOR, QS_CURB_TOP, bands[MARBLE], seg=64)
    ring(mb, 5.4, QS_POOL_R, QS_FLOOR, bands[LAPIS], seg=48, shade=0.7)
    # the spout at the back: a notch-lip of gold where the overflow leaves for the channel
    mb.box((0, QS_CURB_TOP - 0.25, -QS_CURB_R + 0.1), (2.2, 0.12, 1.4), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.85)
    # the fountain: a fluted column on a gold foot, the low tier, a slim stem, the high tier, a gold calyx for the crystal lotus
    mb.lathe([(1.3, QS_FLOOR + 0.5, 1.0), (1.4, QS_FLOOR, 0.8)], 24, bands[GOLD], cap_top=True)
    mb.lathe([(0.75, QS_LOW - 1.1, 0.95), (0.85, QS_FLOOR + 0.5, 0.7)], 24, bands[MARBLE], cap_top=False,
             rmod=lambda a, k: 1.0 - 0.07 * (0.5 + 0.5 * math.cos(a * 12)))
    mb.lathe([(3.3, QS_LOW, 0.95), (3.05, QS_LOW - 0.35, 0.85), (1.9, QS_LOW - 0.9, 0.7), (0.8, QS_LOW - 1.15, 0.6)], 40, bands[MARBLE], cap_top=False)
    mb.lathe([(3.4, QS_LOW + 0.12, 1.0), (3.4, QS_LOW - 0.15, 0.85)], 40, bands[GOLD], cap_top=False)
    ring(mb, 3.0, 3.4, QS_LOW + 0.12, bands[GOLD], seg=40)
    mb.lathe([(0.42, QS_HIGH - 0.8, 0.95), (0.5, QS_LOW - 0.1, 0.75)], 16, bands[MARBLE], cap_top=False)
    mb.lathe([(1.95, QS_HIGH, 0.95), (1.75, QS_HIGH - 0.3, 0.85), (0.9, QS_HIGH - 0.7, 0.7), (0.45, QS_HIGH - 0.85, 0.6)], 32, bands[MARBLE], cap_top=False)
    mb.lathe([(2.03, QS_HIGH + 0.1, 1.0), (2.03, QS_HIGH - 0.14, 0.85)], 32, bands[GOLD], cap_top=False)
    ring(mb, 1.7, 2.03, QS_HIGH + 0.1, bands[GOLD], seg=32)
    for k in range(6):   # the calyx: gold sepals cupping the lotus
        a = TAU * k / 6
        ca, sa = math.cos(a), math.sin(a)
        tube(mb, [(ca * 0.3, QS_HIGH - 0.05, sa * 0.3), (ca * 0.8, QS_HIGH + 0.5, sa * 0.8), (ca * 0.95, QS_HIGH + 1.0, sa * 0.95)],
             lambda f: 0.16 - 0.1 * f, bands[GOLD], sides=5, shade=1.0)
    # the meditation seats: low marble drums, gold rimmed, lapis cushions
    for k in range(QS_SEATS):
        a = TAU * (k + 0.5) / QS_SEATS
        c = (math.cos(a) * 9.0, math.sin(a) * 9.0)
        drum(mb, 0.95, QS_PLAT_TOP, 0.75, bands[MARBLE], seg=20, centre=c)
        ring(mb, 0.78, 0.95, 0.76, bands[GOLD], seg=20, centre=c)
        ring(mb, 0.0, 0.78, 0.77, bands[LAPIS], seg=20, centre=c, shade=0.75)
    return mb.object("HB_QiSpring", coll, mat)


def qi_spring_water(coll, mat, bands):
    """The water: the pool, each tier's surface and the sheets falling off their lips (see-through in the game)."""
    mb = W.MeshBuilder()
    ring(mb, 0.85, QS_POOL_R, QS_WATER, bands[CRYSTAL], seg=64, shade=0.85)
    ring(mb, 0.5, 3.05, QS_LOW - 0.05, bands[CRYSTAL], seg=40, shade=0.9)
    ring(mb, 0.0, 1.75, QS_HIGH - 0.06, bands[CRYSTAL], seg=32, shade=0.9)
    mb.lathe([(3.42, QS_LOW + 0.05, 0.9), (3.6, QS_LOW - 1.6, 0.85), (3.85, QS_WATER, 0.8)], 40, bands[CRYSTAL], cap_top=False)
    mb.lathe([(2.05, QS_HIGH + 0.05, 0.9), (2.15, QS_HIGH - 1.0, 0.85), (2.3, QS_LOW, 0.8)], 32, bands[CRYSTAL], cap_top=False)
    return mb.object("HB_SpringWater", coll, mat)


def qi_spring_glow(coll, mat, bands):
    """The Qi in it: a lotus glowing on the pool's floor, the crystal lotus on the fountain, the ring of runes at the bonus's edge."""
    mb = W.MeshBuilder()
    y = QS_FLOOR + 0.02
    for k in range(8):   # the floor lotus: eight petals round a disc
        a = TAU * k / 8
        ca, sa = math.cos(a), math.sin(a)
        px, pz = -sa, ca
        base, tip = 1.7, 5.1
        W_oriented(mb, [(ca * base + px * 0.75, y, sa * base + pz * 0.75), (ca * (base + tip) / 2 + px * 0.9, y, sa * (base + tip) / 2 + pz * 0.9),
                        (ca * tip, y, sa * tip), (ca * (base + tip) / 2 - px * 0.9, y, sa * (base + tip) / 2 - pz * 0.9),
                        (ca * base - px * 0.75, y, sa * base - pz * 0.75)], (0, 1, 0), bands[GLOW], 1.0)
    ring(mb, 1.45, 1.6, y, bands[GLOW], seg=32)
    for k in range(8):   # the crystal lotus on top: petals of crystal round a bud
        a = TAU * k / 8
        shard(mb, (math.cos(a) * 0.25, QS_HIGH + 0.3, math.sin(a) * 0.25), (math.cos(a) * 0.9, 1.0, math.sin(a) * 0.9), 1.3, 0.22, bands[GLOW], twist=a)
    shard(mb, (0, QS_HIGH + 0.2, 0), (0, 1, 0), 2.0, 0.32, bands[GLOW])
    # the bonus's edge: a thin ring and a glyph every 12 degrees
    ring(mb, QS_ZONE_R - 0.08, QS_ZONE_R + 0.08, QS_PLAT_TOP + 0.02, bands[GLOW], seg=96)
    for k in range(30):
        a = TAU * k / 30
        ca, sa = math.cos(a), math.sin(a)
        px, pz = -sa, ca
        r0, r1 = QS_ZONE_R + 0.3, QS_ZONE_R + 0.75
        W_oriented(mb, [(ca * r0 - px * 0.12, QS_PLAT_TOP + 0.02, sa * r0 - pz * 0.12), (ca * r0 + px * 0.12, QS_PLAT_TOP + 0.02, sa * r0 + pz * 0.12),
                        (ca * r1 + px * 0.05, QS_PLAT_TOP + 0.02, sa * r1 + pz * 0.05), (ca * r1 - px * 0.05, QS_PLAT_TOP + 0.02, sa * r1 - pz * 0.05)],
                   (0, 1, 0), bands[GLOW], 1.0)
    return mb.object("HB_SpringGlow", coll, mat)


# ---------- the bridge gates: where each bridge leaves the hub (the owner, 2026-11-12: the islands' own gates there were red, tiled,
# Chinese; "do 1": the hub's side in the city's style) ----------
# Two tall tapered marble pylons either side of the 40-stud deck, banded in gold, a crystal on each; a shallow marble arch on gold ribs
# springing from them; at its crown a keystone holding a crystal in the island's colour (HB_BridgeGateGlow, coloured per route) and,
# hung on gold chains under it, the island's name (WorldBuilder.dressBridge writes it). Authored on the deck at the barrier's
# foot, the opening across X, its front (+Z) toward the hub.
BG_HALF = 22.6           # the pylons' centres
BG_PYLON = 17.0          # their height
BG_RISE = 6.5            # the arch's rise over the pylons
BG_PLAQUE = ((0.0, 18.2, 1.6), (12.0, 2.0))


def _arch_point(u, r_off=0.0):
    """A point on the arch's curve, u -1..1 across, r_off outward from it (a circle through both pylon tops and the crown)."""
    span, rise = BG_HALF, BG_RISE
    R = (span * span + rise * rise) / (2 * rise)
    cy = BG_PYLON + rise - R
    a = math.asin(max(-1.0, min(1.0, u * span / R)))
    return (math.sin(a) * (R + r_off), cy + math.cos(a) * (R + r_off))


def bridge_gate(coll, mat, bands):
    global MARBLE_BAND, GOLD_BAND
    MARBLE_BAND, GOLD_BAND = bands[MARBLE], bands[GOLD]
    mb = W.MeshBuilder()
    for side in (-1, 1):
        x = side * BG_HALF
        mb.lathe([(2.3, 0.9, 0.9), (2.5, 0.0, 0.7)], 4, bands[GOLD], centre=(x, 0, 0), phase=math.pi / 4, cap_top=True)
        mb.lathe([(1.8, BG_PYLON - 1.2, 0.95), (2.15, 0.9, 0.7)], 4, bands[MARBLE], centre=(x, 0, 0), phase=math.pi / 4, cap_top=False)
        for y in (6.0, BG_PYLON - 1.2):
            mb.lathe([(2.0 - 0.02 * y, y + 0.35, 1.0), (2.05 - 0.02 * y, y - 0.35, 0.85)], 4, bands[GOLD], centre=(x, 0, 0), phase=math.pi / 4, cap_top=False)
        mb.lathe([(2.4, BG_PYLON + 0.4, 1.0), (2.2, BG_PYLON - 0.85, 0.85)], 4, bands[GOLD], centre=(x, 0, 0), phase=math.pi / 4, cap_top=True)
        # a lapis panel inset on each pylon's front and back
        for zs in (1, -1):
            W_oriented(mb, [(x - 0.85, 2.0, zs * 1.62), (x + 0.85, 2.0, zs * 1.62), (x + 0.75, 5.2, zs * 1.48), (x - 0.75, 5.2, zs * 1.48)], (0, 0.1, zs), bands[LAPIS], 0.8)
        # the finial: a gold cup on a short stem (its crystal: bridge_gate_glow)
        mb.lathe([(0.0, BG_PYLON + 2.3, 1.0), (0.75, BG_PYLON + 1.6, 0.95), (0.35, BG_PYLON + 1.0, 0.85), (0.5, BG_PYLON + 0.4, 0.8)], 8, bands[GOLD], centre=(x, 0, 0), cap_top=False)
    # the arch: a marble band 1.8 deep (radially) and 2.6 thick, gold ribs along both faces' edges
    n = 40
    for k in range(n):
        u0, u1 = -1 + 2 * k / n, -1 + 2 * (k + 1) / n
        (x0i, y0i), (x1i, y1i) = _arch_point(u0, -0.9), _arch_point(u1, -0.9)
        (x0o, y0o), (x1o, y1o) = _arch_point(u0, 0.9), _arch_point(u1, 0.9)
        for zz, want in ((1.3, 1), (-1.3, -1)):
            W_oriented(mb, [(x0i, y0i, zz), (x1i, y1i, zz), (x1o, y1o, zz), (x0o, y0o, zz)], (0, 0, want), bands[MARBLE], 0.9)
        W_oriented(mb, [(x0o, y0o, 1.3), (x1o, y1o, 1.3), (x1o, y1o, -1.3), (x0o, y0o, -1.3)], ((x0o + x1o) / 2 * 0.02, 1, 0), bands[MARBLE], 0.95)
        W_oriented(mb, [(x0i, y0i, 1.3), (x1i, y1i, 1.3), (x1i, y1i, -1.3), (x0i, y0i, -1.3)], (0, -1, 0), bands[SHADE], 0.6)
    for zz in (1.4, -1.4):
        for off in (-0.9, 0.9):
            tube(mb, [(*_arch_point(-1 + 2 * k / 32, off), zz) for k in range(33)], 0.18, bands[GOLD], sides=6, shade=1.0, caps=False)
    # the keystone, wedge-shaped, gold-capped, a gold ring round its crystal
    ky = BG_PYLON + BG_RISE
    for zz, want in ((1.55, 1), (-1.55, -1)):
        W_oriented(mb, [(-0.9, ky - 1.4, zz), (0.9, ky - 1.4, zz), (1.3, ky + 1.5, zz), (-1.3, ky + 1.5, zz)], (0, 0, want), bands[MARBLE], 0.95)
    mb.box((0, ky + 1.62, 0), (2.8, 0.25, 3.3), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.85)
    for zz in (1.62, -1.62):
        tube(mb, [(math.cos(TAU * k / 16) * 0.75, ky + math.sin(TAU * k / 16) * 0.75, zz) for k in range(17)], 0.1, bands[GOLD], sides=6, shade=1.0, caps=False)
    # the name board's chains (the board itself: a text panel the builder adds, on a gold-framed lapis panel)
    (px, py, pz), (pw, ph) = BG_PLAQUE
    for x in (-pw / 2 + 0.8, pw / 2 - 0.8):
        top = _arch_point(x / BG_HALF, -0.9)[1]
        tube(mb, [(x, top, pz - 0.2), (x, py + ph / 2 + 0.35, pz - 0.2)], 0.07, bands[GOLD], sides=4, shade=1.0)
    panel(mb, bands, *BG_PLAQUE)
    return mb.object("HB_BridgeGate", coll, mat)


def bridge_gate_glow(coll, mat, bands):
    """The keystone's crystal and the pylons' (coloured per route by the builder)."""
    mb = W.MeshBuilder()
    ky = BG_PYLON + BG_RISE
    for zz in (1.7, -1.7):
        gem(mb, (0.0, ky - 0.2, zz), 0.5, 0.8, bands[GLOW], sides=6)
    for side in (-1, 1):
        gem(mb, (side * BG_HALF, BG_PYLON + 2.6, 0.0), 0.45, 1.1, bands[GLOW], sides=6)
    return mb.object("HB_BridgeGateGlow", coll, mat)


# ---------- the Ascension Board: the leaderboard (the owner, 2026-11-12: "do 3"), facing the spawn ----------
# A round marble dais; a marble board between two pylons, its face a gold-framed lapis panel the cultivators with the most Qi are
# written on (LeaderboardService); a gold arch over it carrying a white crystal star, the board's name on a plaque beneath.
LB_HALF, LB_PYLON = 6.6, 12.4
LB_BOARD = ((0.0, 6.6, 0.56), (10.4, 8.6))
LB_TITLE = ((0.0, 12.15, 0.62), (8.2, 1.3))


def leaderboard(coll, mat, bands):
    global MARBLE_BAND, GOLD_BAND
    MARBLE_BAND, GOLD_BAND = bands[MARBLE], bands[GOLD]
    mb = W.MeshBuilder()
    drum(mb, 7.6, -0.4, 0.4, bands[MARBLE], shade=(0.95, 0.6))
    ring(mb, 7.25, 7.6, 0.41, bands[GOLD])
    drum(mb, 6.6, 0.35, 0.8, bands[MARBLE], shade=(0.95, 0.62))
    ring(mb, 6.25, 6.6, 0.81, bands[GOLD])
    # the board: a marble slab, a gold frame, the lapis face (the text: the builder's SurfaceGui)
    mb.box((0, 6.6, 0), (2 * LB_HALF - 1.2, 10.8, 0.9), bands[MARBLE], u=0.5, top_shade=0.95, side_shade=0.75)
    (bx, by, bz), (bw, bh) = LB_BOARD
    mb.box((0, by, bz - 0.12), (bw + 0.7, bh + 0.7, 0.26), bands[GOLD], u=0.5, top_shade=1.0, side_shade=0.85)
    W_oriented(mb, [(-bw / 2, by - bh / 2, bz + 0.02), (bw / 2, by - bh / 2, bz + 0.02), (bw / 2, by + bh / 2, bz + 0.02), (-bw / 2, by + bh / 2, bz + 0.02)],
               (0, 0, 1), bands[LAPIS], 0.55)
    for side in (-1, 1):
        x = side * LB_HALF
        mb.lathe([(1.25, 1.4, 0.9), (1.4, 0.8, 0.7)], 4, bands[GOLD], centre=(x, 0, 0), phase=math.pi / 4, cap_top=True)
        mb.lathe([(1.0, LB_PYLON - 0.8, 0.95), (1.2, 1.4, 0.7)], 4, bands[MARBLE], centre=(x, 0, 0), phase=math.pi / 4, cap_top=False)
        mb.lathe([(1.4, LB_PYLON + 0.2, 1.0), (1.25, LB_PYLON - 0.8, 0.85)], 4, bands[GOLD], centre=(x, 0, 0), phase=math.pi / 4, cap_top=True)
    # the arch over it: a gold band from pylon to pylon, the star's mount at its crown
    pts = [(math.cos(math.pi * k / 24) * LB_HALF, LB_PYLON + 0.2 + math.sin(math.pi * k / 24) * 3.2, 0.0) for k in range(25)]
    tube(mb, pts, 0.3, bands[GOLD], sides=8, shade=1.0, caps=False)
    tube(mb, [(math.cos(TAU * k / 16) * 0.9, LB_PYLON + 3.4 + math.sin(TAU * k / 16) * 0.9, 0.0) for k in range(17)], 0.12, bands[GOLD], sides=6, shade=1.0, caps=False)
    panel(mb, bands, *LB_TITLE)
    return mb.object("HB_Leaderboard", coll, mat)


def leaderboard_glow(coll, mat, bands):
    """The crystal star at the arch's crown: a six-pointed burst of shards round a gem."""
    mb = W.MeshBuilder()
    c = (0.0, LB_PYLON + 3.4, 0.0)
    gem(mb, c, 0.55, 0.8, bands[GLOW], sides=6)
    for k in range(6):
        a = TAU * k / 6 + math.pi / 2
        shard(mb, (c[0] + math.cos(a) * 0.35, c[1] + math.sin(a) * 0.35, 0.0), (math.cos(a), math.sin(a), 0.0), 1.1, 0.18, bands[GLOW], twist=a)
    return mb.object("HB_LeaderboardGlow", coll, mat)


BUILDINGS = [sanctum, sanctum_glass, sanctum_crystal, sanctum_runes, market, market_canopies, market_glow, blacksmith, blacksmith_core, blacksmith_crystal,
             buy_sell, buy_sell_glow, qi_spring, qi_spring_water, qi_spring_glow, bridge_gate, bridge_gate_glow, leaderboard, leaderboard_glow,
             crystal_lamp, crystal_lamp_glow]
