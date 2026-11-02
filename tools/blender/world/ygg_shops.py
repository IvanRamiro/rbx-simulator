"""Yggdrasil's two shop buildings, each on its plot (ygg_island.PLOTS), on the prop atlas
(start_props.STRIPS) and under the same tiled roof as the Ascension Stele (ygg_props.tiled_roof).

- The Blacksmith, the Dragon-Kiln Forge: a smoke-dark timber and stone smithy whose forge is a
  dragon's head bursting from the back wall, the fire and a burning pearl between its open jaws,
  its eyes alight, its horns and whiskers bronze. Its body coils up the round chimney behind and
  out through the roof, the tail curling over the chimney's mouth. Before it, an anvil with a
  half-forged blade glowing on it, a quench trough, bellows and a coal bin; along the left wall a
  rack of swords and spears.
- Buy & Sell, the Jade Scale: a merchant's hall behind an open forecourt where a great bronze
  balance scale stands, glowing Spirit Stones heaped in one pan and a spirit egg in the other (pets
  traded for stones). Under the roof, a counter topped with jade before a wall of drawers, red paper
  lanterns at the eave's corners, banners on the pillars, crates and sacks.

Each is authored round its plot's centre on the ground, its open front toward +Z (the lane). SIGNS
gives each name board's face, PROMPTS where each shop's prompt stands, and FX where the game adds
its fire, smoke and lights (ygg_props.write_placements writes them into the placements).

    import ygg_shops; objs = ygg_shops.build(); ygg_shops.export(objs)   # assets/world/Yggdrasil/Yggdrasil_Shops.fbx
"""
import math

import worldlib as W
import start_props as P
import ygg_props as YP

TAU = 2 * math.pi
FLOOR = 1.1          # the halls' floor, over the plot's ground

# the Blacksmith: the dragon's open jaws (the forge mouth) and its chimney
JAW_TOP, JAW_LOW = FLOOR + 5.3, FLOOR + 2.4
CHIMNEY = (0.0, -10.0)
CHIMNEY_TOP = 30.0
# Buy & Sell: the hall's front, and the scale in the forecourt
HALL_FRONT = 2.6
SCALE = (0.0, 8.6)
BEAM_Y = FLOOR + 13.5
PAN_X, PAN_Y = 7.0, FLOOR + 6.2
LANTERN_X = (-11.0, 11.0)

SIGNS = {            # the name board over each entrance: face centre (x, y, z) and size
    "Blacksmith": ((0.0, 14.4, 13.36), (9.0, 1.6)),
    "BuySell": ((0.0, 12.75, HALL_FRONT + 0.76), (8.0, 1.4)),
}
PROMPTS = {          # where each shop's prompt stands: at the anvil, at the foot of the scale
    "Blacksmith": (0.0, FLOOR + 2.6, 2.4),
    "BuySell": (0.0, FLOOR + 2.4, SCALE[1] + 3.2),
}
FX = {               # where the game adds each shop's effects: (kind, (x, y, z))
    "Blacksmith": [("Forge", (0.0, FLOOR + 3.4, -6.4)), ("Smoke", (CHIMNEY[0], CHIMNEY_TOP + 0.8, CHIMNEY[1]))],
    "BuySell": [("Stones", (-PAN_X, PAN_Y + 1.2, SCALE[1]))] + [("Lantern", (x, 11.1, HALL_FRONT + 1.2)) for x in LANTERN_X],
}


# ---------- shared pieces ----------
def pillar(mb, bands, x, z, top, r=0.85, band=P.LACQUER):
    """An octagonal pillar on a bronze base, under a bronze capital."""
    c = (x, 0, z)
    mb.lathe([(r, top - 0.4, 0.9), (r, FLOOR + 0.9, 0.6)], 8, bands[band], centre=c, phase=TAU / 16, cap_top=False)
    mb.lathe([(r + 0.15, FLOOR + 0.9, 0.9), (r + 0.35, FLOOR + 0.6, 0.8), (r + 0.35, FLOOR, 0.6)], 8, bands[P.BRONZE], centre=c,
             phase=TAU / 16, cap_top=True)
    mb.lathe([(r + 0.3, top, 1.0), (r + 0.3, top - 0.4, 0.8), (r + 0.05, top - 0.6, 0.6)], 8, bands[P.BRONZE], centre=c,
             phase=TAU / 16, cap_top=True)


def name_board(mb, bands, sign):
    """A dark board in a bronze frame, its face toward +Z (the name is written on it in the game)."""
    (x, y, z), (w, h) = sign
    mb.box((x, y, z - 0.2), (w + 0.6, h + 0.6, 0.4), bands[P.BRONZE], u=0.5, top_shade=1.0, side_shade=0.8)
    P.oriented(mb, [(x - w / 2, y - h / 2, z + 0.01), (x + w / 2, y - h / 2, z + 0.01), (x + w / 2, y + h / 2, z + 0.01),
                    (x - w / 2, y + h / 2, z + 0.01)], (0, 0, 1), bands[P.DARK], 0.5, [0.3] * 4)


def base(mb, bands, width, depth):
    """A stone platform with a step along its front."""
    mb.box((0, 0.3, 0), (width, 1.6, depth), bands[P.PALE], u=0.3, top_shade=0.9, side_shade=0.65)
    mb.box((0, 0.35, depth / 2 + 0.8), (width * 0.55, 0.9, 1.6), bands[P.PALE], u=0.6, top_shade=0.95, side_shade=0.7)


def loft(mb, band, rings, n=16):
    """A rounded form lofted through cross-sections in the XY plane, listed back to front:
    (x, y, z, half width, half height, squareness: 2 is an ellipse, higher is boxier). Its top is
    lit and its underside shaded; the front section is capped."""
    loops = []
    for (cx, cy, cz, hw, hh, p) in rings:
        loop = []
        for i in range(n):
            c, s = math.cos(TAU * i / n), math.sin(TAU * i / n)
            loop.append((cx + hw * math.copysign(abs(c) ** (2 / p), c), cy + hh * math.copysign(abs(s) ** (2 / p), s), cz))
        loops.append(loop)
    for k in range(len(loops) - 1):
        ca, cb = rings[k][:3], rings[k + 1][:3]
        for i in range(n):
            j = (i + 1) % n
            quad = [loops[k][i], loops[k][j], loops[k + 1][j], loops[k + 1][i]]
            out = [sum(q[d] for q in quad) / 4 - (ca[d] + cb[d]) / 2 for d in range(3)]
            out[2] = 0.0
            shade = 0.5 + 0.45 * (0.5 + 0.5 * math.sin(TAU * (i + 0.5) / n))
            P.oriented(mb, quad, out, band, 0.5, [shade] * 4)
    P.oriented(mb, loops[-1], (0, 0, 1 if rings[-1][2] > rings[-2][2] else -1), band, 0.5, [0.8] * n)


def cone(mb, band, base_centre, r, h, seg=6, phase=0.0):
    """A cone from a base ring to a point h above it (h < 0 points it down)."""
    x, y, z = base_centre
    if h > 0:
        mb.lathe([(0.02, y + h, 1.0), (r, y, 0.7)], seg, band, centre=(x, 0, z), phase=phase, cap_top=False)
    else:
        mb.lathe([(r, y, 1.0), (0.02, y + h, 0.8)], seg, band, centre=(x, 0, z), phase=phase, cap_top=True)


def tube(mb, points, radius_fn, sides, band, per=6):
    """worldlib.mb_tube, kept off the band's top edge (its tip samples there, which bleeds into the
    next strip of the atlas)."""
    v0, v1 = band
    return W.mb_tube(mb, points, radius_fn, sides, (v0, v1 - 0.15 * (v1 - v0)), per=per)


# ---------- the Blacksmith ----------
def dragon_head(mb, bands):
    """The dragon's head of pale carved stone bursting from the dark back wall (its forge): skull and upper jaw, the open lower jaw, the
    cheeks closing the mouth's corners, brows, horns, mane, teeth, nostrils and long whiskers."""
    F = FLOOR
    loft(mb, bands[P.PALE], [
        (0, F + 8.4, -13.0, 5.0, 3.6, 2.6),     # out of the wall
        (0, F + 8.9, -8.6, 4.8, 3.4, 2.6),     # the skull, widest at the brows
        (0, F + 8.1, -6.4, 3.8, 2.6, 2.8),
        (0, F + 7.0, -4.2, 2.9, 1.7, 3.0),     # the upper jaw
        (0, F + 6.7, -2.6, 2.7, 1.45, 3.0),    # the snout, flaring at the nose
        (0, F + 6.6, -1.7, 2.2, 1.1, 2.8),
    ])
    loft(mb, bands[P.PALE], [
        (0, F + 1.6, -13.0, 4.3, 1.5, 3.0),
        (0, F + 1.5, -7.6, 3.9, 1.3, 3.0),
        (0, F + 1.4, -4.4, 2.9, 1.0, 3.0),     # the lower jaw, open on the floor
        (0, F + 1.4, -2.4, 2.4, 0.95, 3.0),
        (0, F + 1.5, -1.9, 2.0, 0.75, 2.8),
    ])
    for sx in (-1, 1):
        # the cheeks close the mouth's corners, jaw to jaw
        mb.box((sx * 3.3, (JAW_LOW + JAW_TOP) / 2, -9.0), (1.1, JAW_TOP - JAW_LOW + 0.8, 4.4), bands[P.PALE], u=0.4,
               top_shade=0.7, side_shade=0.55)
        # the brow over a deep eye socket
        tube(mb, [(sx * 1.4, F + 9.6, -4.9), (sx * 2.9, F + 11.0, -6.6), (sx * 4.3, F + 11.0, -8.8), (sx * 5.0, F + 10.0, -10.6)],
                  lambda t: 0.75 - 0.35 * t, 7, bands[P.BRONZE], per=4)
        mb.box((sx * 3.35, F + 9.55, -6.4), (1.3, 0.8, 1.1), bands[P.DARK], yaw=sx * 0.5, u=0.3, top_shade=0.5, side_shade=0.4)
        # the great horns sweeping back and up, the lesser ones behind
        tube(mb, [(sx * 3.0, F + 11.4, -8.4), (sx * 4.6, F + 13.4, -9.8), (sx * 5.6, F + 15.6, -11.2), (sx * 6.9, F + 17.0, -11.0),
                       (sx * 7.8, F + 17.6, -10.0)], lambda t: 0.85 - 0.75 * t, 8, bands[P.BRONZE], per=5)
        tube(mb, [(sx * 3.4, F + 12.0, -10.0), (sx * 4.6, F + 12.6, -11.6), (sx * 5.0, F + 13.8, -12.2)],
                  lambda t: 0.45 - 0.35 * t, 6, bands[P.BRONZE], per=4)
        # the mane fanning from the jaw's hinge
        for k, (y, z) in enumerate(((F + 2.8, -10.6), (F + 1.6, -9.4), (F + 4.2, -11.4))):
            tube(mb, [(sx * 4.6, y, z), (sx * 6.0, y + 0.3, z - 0.8), (sx * 7.0, y + 1.0 + 0.4 * k, z - 2.2)],
                      lambda t: 0.6 - 0.5 * t, 6, bands[P.BRONZE], per=4)
        # the long whiskers, from the nose curling out and up
        tube(mb, [(sx * 1.7, F + 6.4, -1.6), (sx * 3.4, F + 5.6, -0.6), (sx * 5.4, F + 5.8, -0.4), (sx * 7.0, F + 7.2, -1.4),
                       (sx * 7.4, F + 9.0, -2.8), (sx * 6.6, F + 10.0, -3.6)], lambda t: 0.22 - 0.16 * t, 5, bands[P.BRONZE], per=5)
        mb.box((sx * 1.0, F + 7.55, -1.85), (0.7, 0.35, 0.5), bands[P.DARK], yaw=sx * 0.3, u=0.2, top_shade=0.3, side_shade=0.3)   # a nostril
    for k in range(4):   # the mane down the crown
        cone(mb, bands[P.BRONZE], (0, F + 11.9 - 0.25 * k, -6.8 - 1.4 * k), 0.55, 1.6 - 0.15 * k, seg=5)
    # teeth round the front of both jaws, fangs at the corners, and molars further in
    for k in range(7):
        a = math.pi * (k + 0.5) / 7
        x, z = math.cos(a) * 2.0, -2.8 - 0.5 * (1 - math.sin(a))
        fang = k in (0, 6)
        cone(mb, bands[P.PALE], (x, JAW_TOP + 0.2, z), 0.3 if fang else 0.22, -1.3 if fang else -0.7, seg=5)
        cone(mb, bands[P.PALE], (x * 0.95, JAW_LOW - 0.1, z + 0.3), 0.22, 1.0 if fang else 0.6, seg=5)
    for sx in (-1, 1):
        for z in (-4.0, -5.4):
            cone(mb, bands[P.PALE], (sx * 2.6, JAW_TOP + 0.25, z), 0.22, -0.7, seg=5)
            cone(mb, bands[P.PALE], (sx * 2.5, JAW_LOW - 0.1, z), 0.2, 0.55, seg=5)


def dragon_body(mb, bands):
    """The round chimney rising from the skull, the dragon's body coiling up it and out through the
    roof, its tail curled over the mouth, and spines along its back."""
    cx, cz = CHIMNEY
    mb.lathe([(1.7, CHIMNEY_TOP, 0.75), (1.9, CHIMNEY_TOP - 6, 0.65), (2.2, FLOOR + 11, 0.55)], 8, bands[P.DARK], centre=(cx, 0, cz),
             cap_top=False, phase=TAU / 16)
    mb.lathe([(1.25, CHIMNEY_TOP + 0.6, 0.3), (2.3, CHIMNEY_TOP + 0.6, 1.0), (2.3, CHIMNEY_TOP - 0.2, 0.8), (1.9, CHIMNEY_TOP - 0.5, 0.6)],
             8, bands[P.BRONZE], centre=(cx, 0, cz), cap_top=True, phase=TAU / 16)
    # the neck out of the back of the skull, then two and a half turns round the chimney
    pts = [(1.2, FLOOR + 11.0, -8.6), (2.6, FLOOR + 12.4, -9.0)]
    turns, y0, y1, steps = 2.4, FLOOR + 13.8, CHIMNEY_TOP - 1.0, 30
    for i in range(steps + 1):
        t = i / steps
        a = TAU * turns * t
        r = 2.6 + 0.6 * (1 - t)
        pts.append((cx + math.cos(a) * r, y0 + (y1 - y0) * t, cz + math.sin(a) * r))
    pts += [(cx + 0.9, CHIMNEY_TOP + 1.8, cz + 1.4), (cx - 0.6, CHIMNEY_TOP + 3.0, cz + 0.5), (cx - 1.3, CHIMNEY_TOP + 2.4, cz - 0.9)]
    curve = tube(mb, pts, lambda t: 1.4 * (1 - t) ** 0.6 + 0.12, 9, bands[P.BRONZE], per=2)
    n = len(curve)
    for i in range(6, n - 6, 4):
        x, y, z = curve[i]
        f = 1 - i / n
        cone(mb, bands[P.DARK], (x, y + 0.9 * f + 0.3, z), 0.35 * f + 0.12, 1.1 * f + 0.3, seg=4)


def blacksmith(coll, mat, bands):
    mb = W.MeshBuilder()
    base(mb, bands, 35, 29)
    # back and side walls of dark stone banded with pale courses; buttresses behind
    mb.box((0, FLOOR + 7, -13.4), (34, 14, 1.6), bands[P.DARK], u=0.2, top_shade=0.6, side_shade=0.5)
    mb.box((0, FLOOR + 0.6, -13.2), (34.4, 1.2, 2.2), bands[P.PALE], u=0.4, top_shade=0.8, side_shade=0.65)
    for y in (FLOOR + 4.8, FLOOR + 9.6):
        mb.box((0, y, -13.4), (34.2, 0.35, 1.8), bands[P.PALE], u=0.6, top_shade=0.8, side_shade=0.6)
    for x in (-11.5, 11.5):
        mb.box((x, FLOOR + 5.5, -14.6), (2.2, 11, 2.0), bands[P.PALE], u=0.3, top_shade=0.85, side_shade=0.6)
        mb.box((x, FLOOR + 11.4, -14.3), (1.8, 1.0, 1.4), bands[P.PALE], u=0.5, top_shade=0.9, side_shade=0.65)
    for sx in (-1, 1):
        mb.box((sx * 16.7, FLOOR + 6.5, -5.4), (1.4, 13, 15.0), bands[P.DARK], u=0.25, top_shade=0.6, side_shade=0.5)
        mb.box((sx * 16.7, FLOOR + 0.6, -5.4), (2.0, 1.2, 15.2), bands[P.PALE], u=0.45, top_shade=0.8, side_shade=0.65)
        mb.box((sx * 16.7, FLOOR + 6.0, 2.1), (1.8, 12.0, 1.2), bands[P.PALE], u=0.4, top_shade=0.85, side_shade=0.65)
    # smoke-dark timber: four pillars, the beams they carry, bronze brackets
    for x in (-16.2, -6.5, 6.5, 16.2):
        pillar(mb, bands, x, 12.6, 15.6, r=0.95, band=P.BARK)
    for z in (12.6, -13.0):
        mb.box((0, 16.1, z), (34.6, 1.0, 1.3), bands[P.BARK], u=0.5, top_shade=0.85, side_shade=0.7)
    for sx in (-1, 1):
        mb.box((sx * 16.4, 16.1, -0.2), (1.0, 1.0, 26.6), bands[P.BARK], u=0.5, top_shade=0.85, side_shade=0.7)
        mb.box((sx * 11.4, 15.3, 12.6), (5.6, 0.5, 0.7), bands[P.BRONZE], u=0.5)
    name_board(mb, bands, SIGNS["Blacksmith"])
    roof = (16.8, 24.5, 19.6, 16.6, -0.4, 2.2)
    YP.tiled_roof(mb, bands, *roof[:5], lift=roof[5], cols=28, rows=7)
    YP.roof_walls(mb, bands[P.BARK], bands[P.DARK], roof, 16.4, 12.6, -13.0, 16.6)

    dragon_head(mb, bands)
    dragon_body(mb, bands)

    # the anvil on its stump, the quench trough, the bellows piped to the kiln, the coal bin
    mb.lathe([(1.25, FLOOR + 2.0, 0.85), (1.35, FLOOR + 0.3, 0.6), (1.6, FLOOR, 0.5)], 10, bands[P.WOOD], centre=(0, 0, 0.5), cap_top=True)
    mb.box((0, FLOOR + 2.3, 0.5), (1.4, 0.6, 1.0), bands[P.DARK], u=0.5, top_shade=0.9, side_shade=0.6)
    mb.box((0.2, FLOOR + 2.85, 0.5), (2.8, 0.5, 1.3), bands[P.DARK], u=0.5, top_shade=1.0, side_shade=0.6)
    mb.box((2.2, FLOOR + 2.95, 0.5), (1.4, 0.3, 0.7), bands[P.DARK], u=0.5, top_shade=1.0, side_shade=0.6)
    mb.box((8.5, FLOOR + 0.9, -2.5), (5.2, 1.8, 2.4), bands[P.PALE], u=0.6, top_shade=0.8, side_shade=0.6)
    P.oriented(mb, [(6.2, FLOOR + 1.81, -1.6), (10.8, FLOOR + 1.81, -1.6), (10.8, FLOOR + 1.81, -3.4), (6.2, FLOOR + 1.81, -3.4)],
               (0, 1, 0), bands[P.WATER], 0.5, [0.7] * 4)
    mb.box((-7.4, FLOOR + 1.0, -8.4), (2.8, 2.0, 3.6), bands[P.WOOD], u=0.4, top_shade=0.8, side_shade=0.6)
    mb.box((-7.4, FLOOR + 2.4, -8.4), (2.4, 0.9, 3.2), bands[P.LACQUER], u=0.4, top_shade=0.6, side_shade=0.45)
    mb.box((-7.4, FLOOR + 3.05, -8.4), (2.8, 0.45, 3.6), bands[P.WOOD], u=0.4, top_shade=0.8, side_shade=0.6)
    tube(mb, [(-6.0, FLOOR + 2.2, -8.4), (-5.4, FLOOR + 2.0, -8.6), (-4.6, FLOOR + 2.6, -9.2)], lambda t: 0.25, 6, bands[P.BRONZE], per=3)
    mb.box((-9.6, FLOOR + 0.7, -2.4), (3.2, 1.4, 2.4), bands[P.WOOD], u=0.6, top_shade=0.7, side_shade=0.55)

    # a rack of swords and spears along the left wall
    rx = -15.4
    for z in (-11.2, -2.2):
        mb.box((rx, FLOOR + 3.5, z), (0.6, 7, 0.6), bands[P.WOOD], u=0.3, top_shade=0.8, side_shade=0.7)
    for y in (FLOOR + 1.6, FLOOR + 6.2):
        mb.box((rx, y, -6.7), (0.7, 0.4, 9.4), bands[P.WOOD], u=0.3, top_shade=0.8, side_shade=0.7)
    for k, z in enumerate((-10.0, -8.4, -6.8, -5.2, -3.6)):
        if k % 2 == 0:   # a sword, point down, hung by its guard
            mb.box((rx + 0.5, FLOOR + 3.6, z), (0.12, 4.2, 0.5), bands[P.PALE], u=0.8, top_shade=1.0, side_shade=0.9)
            mb.box((rx + 0.5, FLOOR + 5.85, z), (0.3, 0.3, 1.3), bands[P.BRONZE], u=0.5, top_shade=1.0, side_shade=0.8)
            mb.box((rx + 0.5, FLOOR + 6.6, z), (0.25, 1.3, 0.25), bands[P.LACQUER], u=0.5)
        else:            # a spear, leaning up the rack
            mb.box((rx + 0.5, FLOOR + 4.6, z), (0.22, 9.0, 0.22), bands[P.WOOD], u=0.5, top_shade=0.9, side_shade=0.8)
            mb.box((rx + 0.5, FLOOR + 9.7, z), (0.12, 1.4, 0.45), bands[P.PALE], u=0.8, top_shade=1.0, side_shade=0.9)
            mb.box((rx + 0.5, FLOOR + 8.9, z), (0.4, 0.3, 0.4), bands[P.BRONZE], u=0.5)
    # tongs and hammers hung on the back wall
    for k, x in enumerate((-13.6, -12.4, 12.4, 13.6)):
        mb.box((x, FLOOR + 6.4, -12.45), (0.25, 3.2, 0.25), bands[P.WOOD], u=0.5)
        mb.box((x, FLOOR + 8.1, -12.45), (1.0 if k % 2 else 0.4, 0.5, 0.5), bands[P.DARK], u=0.5)
    return mb.object("YG_Blacksmith", coll, mat)


def blacksmith_glow(coll, mat, bands):
    """The fire in the dragon's throat and its burning pearl, its eyes, the coals and the blade on
    the anvil."""
    mb = W.MeshBuilder()
    band = bands[P.PAPER]
    mb.box((0, (JAW_LOW + JAW_TOP) / 2 - 0.2, -8.8), (6.0, JAW_TOP - JAW_LOW + 0.4, 0.4), band)
    mb.lathe([(0.0, JAW_LOW + 2.2, 1.0), (0.85, JAW_LOW + 1.85, 1.0), (1.2, JAW_LOW + 1.1, 1.0), (0.85, JAW_LOW + 0.35, 1.0),
              (0.0, JAW_LOW, 1.0)], 10, band, centre=(0, 0, -5.4), cap_top=False)
    for sx in (-1, 1):
        mb.box((sx * 3.55, FLOOR + 9.55, -6.0), (1.1, 0.5, 0.5), band, yaw=sx * 0.5)
    for k in range(6):
        mb.box((-10.2 + 0.6 * (k % 3), FLOOR + 1.45, -2.9 + 0.5 * (k // 3)), (0.5, 0.25, 0.45), band, yaw=0.3 * k)
    mb.box((0.2, FLOOR + 3.14, 0.5), (2.4, 0.08, 0.32), band)
    return mb.object("YG_BlacksmithGlow", coll, mat)


# ---------- Buy & Sell ----------
def coin(mb, band, centre, r, hole, facing, depth=0.35, n=32):
    """A round coin with a square hole, standing in the XY plane, its face toward `facing` along z:
    a raised rim round a sunken field."""
    x0, y0, z0 = centre
    zf = z0 + facing * depth

    def ring(a, radius, square=False):
        c, s = math.cos(a), math.sin(a)
        if square:
            radius = radius / max(abs(c), abs(s))
        return x0 + c * radius, y0 + s * radius

    for i in range(n):
        a, b = TAU * i / n, TAU * (i + 1) / n
        mid = (a + b) / 2
        bands_ = [(r, zf, 0.95), (0.8 * r, zf, 0.95), (0.8 * r, zf - facing * 0.12, 0.65), (hole, zf - facing * 0.12, 0.65)]
        for (r0, zz, sh), (r1, _, _) in ((bands_[0], bands_[1]), (bands_[2], bands_[3])):
            sq = r1 == hole
            p = [ring(a, r0) + (zz,), ring(b, r0) + (zz,), ring(b, r1, sq) + (zz,), ring(a, r1, sq) + (zz,)]
            P.oriented(mb, p, (0, 0, facing), band, 0.5, [sh] * 4)
        p = [ring(a, 0.8 * r) + (zf,), ring(b, 0.8 * r) + (zf,), ring(b, 0.8 * r) + (zf - facing * 0.12,), ring(a, 0.8 * r) + (zf - facing * 0.12,)]
        P.oriented(mb, p, (-math.cos(mid), -math.sin(mid), 0), band, 0.5, [0.5] * 4)    # the rim's inner step
        p = [ring(a, r) + (zf,), ring(b, r) + (zf,), ring(b, r) + (z0,), ring(a, r) + (z0,)]
        P.oriented(mb, p, (math.cos(mid), math.sin(mid), 0), band, 0.5, [0.7] * 4)       # the edge
        zh = zf - facing * 0.12
        p = [ring(a, hole, True) + (zh,), ring(b, hole, True) + (zh,), ring(b, hole, True) + (z0,), ring(a, hole, True) + (z0,)]
        P.oriented(mb, p, (-math.cos(mid), -math.sin(mid), 0), band, 0.5, [0.35] * 4)    # the hole's sides


def buy_sell(coll, mat, bands):
    mb = W.MeshBuilder()
    base(mb, bands, 29, 25)
    hall_back = -11.6
    hall_mid = (HALL_FRONT + hall_back) / 2
    for x, z in ((-13.6, HALL_FRONT), (-5.0, HALL_FRONT), (5.0, HALL_FRONT), (13.6, HALL_FRONT), (-13.6, hall_back), (13.6, hall_back)):
        pillar(mb, bands, x, z, 13.0, r=0.8)
    for z in (HALL_FRONT, hall_back):
        mb.box((0, 13.5, z), (28.8, 0.9, 1.2), bands[P.LACQUER], u=0.5, top_shade=0.85, side_shade=0.7)
    for sx in (-1, 1):
        mb.box((sx * 13.6, 13.5, hall_mid), (0.9, 0.9, HALL_FRONT - hall_back), bands[P.LACQUER], u=0.5, top_shade=0.85, side_shade=0.7)
    name_board(mb, bands, SIGNS["BuySell"])
    roof = (13.9, 19.6, 16.6, 9.0, hall_mid, 1.8)
    YP.tiled_roof(mb, bands, *roof[:5], lift=roof[5], cols=26, rows=6)
    YP.roof_walls(mb, bands[P.LACQUER], bands[P.WOOD], roof, 13.6, HALL_FRONT, hall_back, 13.95)

    # the wall of drawers across the back: dark wood, bronze pulls, a few drawers left open
    mb.box((0, FLOOR + 6, hall_back - 0.4), (26.4, 12, 1.2), bands[P.WOOD], u=0.25, top_shade=0.6, side_shade=0.5)
    for row in range(6):
        for col in range(10):
            x, y = -11.25 + 2.5 * col, FLOOR + 1.4 + 1.65 * row
            out = 0.5 if (row * 7 + col * 3) % 11 == 0 else 0.0
            mb.box((x, y, hall_back + 0.3 + out), (2.2, 1.4, 0.3 + 2 * out), bands[P.WOOD], u=0.7, top_shade=0.9, side_shade=0.75)
            mb.box((x, y, hall_back + 0.5 + 2 * out), (0.5, 0.25, 0.2), bands[P.BRONZE], u=0.5)
    # outside, the back wall framed in dark timber over a stone course, the merchant's great bronze
    # coin at its centre
    back = hall_back - 1.05
    mb.box((0, FLOOR + 0.8, back), (26.6, 1.6, 0.4), bands[P.PALE], u=0.4, top_shade=0.85, side_shade=0.65)
    mb.box((0, FLOOR + 11.6, back), (26.6, 0.6, 0.3), bands[P.BARK], u=0.5, top_shade=0.8, side_shade=0.7)
    for x in (-8.2, -4.4, 4.4, 8.2):
        mb.box((x, FLOOR + 6.2, back), (0.6, 10.2, 0.3), bands[P.BARK], u=0.5, top_shade=0.8, side_shade=0.7)
    coin(mb, bands[P.BRONZE], (0, FLOOR + 6.4, back), 3.3, 0.9, -1)
    # paper screens closing the hall's sides
    for sx in (-1, 1):
        x = sx * 13.6
        for z in (-9.4, -5.4, -1.4):
            mb.box((x, FLOOR + 4.5, z), (0.3, 9.0, 3.6), bands[P.PAPER], u=0.5, top_shade=0.95, side_shade=0.95)
            mb.box((x, FLOOR + 4.5, z - 1.9), (0.5, 9.2, 0.3), bands[P.WOOD], u=0.4)
        mb.box((x, FLOOR + 9.1, -5.4), (0.5, 0.3, 12.0), bands[P.WOOD], u=0.4)

    # the counter: dark wood topped with jade, bronze corners, an abacus and a ledger on it
    mb.box((0, FLOOR + 1.6, -1.0), (20, 3.2, 2.6), bands[P.WOOD], u=0.35, top_shade=0.7, side_shade=0.55)
    mb.box((0, FLOOR + 3.35, -1.0), (20.6, 0.3, 3.0), bands[P.JADE], u=0.5, top_shade=1.0, side_shade=0.8)
    for x in (-9.9, 9.9):
        mb.box((x, FLOOR + 1.6, 0.35), (0.6, 3.2, 0.2), bands[P.BRONZE], u=0.5)
    for x, band in ((-6.0, P.WOOD), (6.0, P.PAPER)):
        mb.box((x, FLOOR + 3.65, -1.2), (2.4, 0.3, 1.4), bands[band], u=0.5, top_shade=0.9, side_shade=0.7)

    # the forecourt's jade paving round the scale
    sx_, sz = SCALE
    mb.lathe([(0.0, FLOOR + 0.06, 0.9), (5.2, FLOOR + 0.06, 0.8)], 24, bands[P.JADE], centre=(sx_, 0, sz), cap_top=False)
    mb.lathe([(5.2, FLOOR + 0.1, 0.9), (5.8, FLOOR + 0.1, 0.8), (5.8, FLOOR, 0.6)], 24, bands[P.BRONZE], centre=(sx_, 0, sz), cap_top=False)
    # the Jade Scale: a stepped plinth, a bronze column ringed with jade, the beam and its two pans
    mb.lathe([(1.7, FLOOR + 1.6, 0.95), (2.2, FLOOR + 1.2, 0.8), (2.6, FLOOR + 0.6, 0.75), (3.0, FLOOR + 0.6, 0.85), (3.0, FLOOR, 0.6)],
             8, bands[P.PALE], centre=(sx_, 0, sz), phase=TAU / 16, cap_top=True)
    mb.lathe([(0.65, BEAM_Y - 0.4, 0.95), (0.75, FLOOR + 6, 0.75), (0.95, FLOOR + 1.6, 0.6)], 10, bands[P.BRONZE], centre=(sx_, 0, sz),
             cap_top=False)
    for y in (FLOOR + 4.0, FLOOR + 8.5):
        mb.lathe([(1.1, y + 0.35, 1.0), (1.15, y - 0.35, 0.8)], 10, bands[P.JADE], centre=(sx_, 0, sz), cap_top=True, cap_bottom=True)
    tube(mb, [(-PAN_X - 0.6, BEAM_Y - 0.2, sz), (-PAN_X / 2, BEAM_Y + 0.25, sz), (0, BEAM_Y + 0.4, sz), (PAN_X / 2, BEAM_Y + 0.25, sz),
                   (PAN_X + 0.6, BEAM_Y - 0.2, sz)], lambda t: 0.62 - 0.2 * abs(2 * t - 1), 8, bands[P.BRONZE], per=4)
    mb.lathe([(0.0, BEAM_Y + 1.9, 1.0), (1.1, BEAM_Y + 1.2, 0.9), (1.3, BEAM_Y + 0.3, 0.8), (0.75, BEAM_Y - 0.7, 0.6), (0.0, BEAM_Y - 0.9, 0.5)],
             12, bands[P.BRONZE], centre=(sx_, 0, sz), cap_top=False)
    cone(mb, bands[P.JADE], (sx_, BEAM_Y + 1.8, sz), 0.45, 2.0, seg=6)
    for side in (-1, 1):
        px = side * PAN_X
        for k in range(3):   # three cords to each pan
            a = TAU * k / 3 + TAU / 12
            tube(mb, [(px, BEAM_Y - 0.3, sz), (px + math.cos(a) * 2.6, PAN_Y + 0.1, sz + math.sin(a) * 2.6)], lambda t: 0.08, 4,
                      bands[P.BRONZE], per=1)
        mb.lathe([(2.85, PAN_Y + 0.25, 0.95), (2.7, PAN_Y - 0.25, 0.85), (1.9, PAN_Y - 0.75, 0.7), (0.7, PAN_Y - 1.0, 0.6)], 18,
                 bands[P.BRONZE], centre=(px, 0, sz), cap_top=True, cap_bottom=True)
        mb.box((px, BEAM_Y - 0.2, sz), (0.8, 0.8, 0.8), bands[P.BRONZE], u=0.5)
    # the spirit egg in the right pan
    mb.lathe([(0.0, PAN_Y + 3.1, 1.0), (0.85, PAN_Y + 2.75, 0.95), (1.3, PAN_Y + 1.7, 0.9), (1.2, PAN_Y + 0.8, 0.8), (0.0, PAN_Y + 0.25, 0.7)],
             16, bands[P.JADE], centre=(PAN_X, 0, sz), cap_top=False)

    # banners on the hall's corner pillars, crates and sacks either side of the counter, lantern cords
    for x in (-13.6, 13.6):
        mb.box((x, FLOOR + 6.8, HALL_FRONT + 1.0), (2.0, 6.4, 0.12), bands[P.LACQUER], u=0.5, top_shade=0.9, side_shade=0.9)
        mb.box((x, FLOOR + 10.2, HALL_FRONT + 1.0), (2.4, 0.3, 0.25), bands[P.WOOD], u=0.5)
    for (x, y, z, size) in ((11.0, FLOOR + 0.9, -3.4, 1.8), (12.2, FLOOR + 0.8, -1.8, 1.6), (11.4, FLOOR + 2.6, -2.9, 1.5)):
        mb.box((x, y, z), (size, size, size), bands[P.WOOD], u=0.6, top_shade=0.85, side_shade=0.65)
    for x, z in ((-11.6, -3.2), (-10.6, -1.6), (-12.2, -1.4)):
        mb.lathe([(0.0, FLOOR + 1.9, 0.9), (0.7, FLOOR + 1.6, 0.85), (0.95, FLOOR + 0.8, 0.75), (0.8, FLOOR, 0.6)], 10, bands[P.PAPER],
                 centre=(x, 0, z), cap_top=False, cap_bottom=True)
    for x in LANTERN_X:
        mb.box((x, 13.1, HALL_FRONT + 1.2), (0.08, 2.0, 0.08), bands[P.DARK], u=0.5)
    return mb.object("YG_BuySell", coll, mat)


def buy_sell_stones(coll, mat, bands):
    """The Spirit Stones heaped in the scale's left pan: faceted crystals leaning together."""
    mb = W.MeshBuilder()
    sz = SCALE[1]
    for k, (dx, dz, s, h) in enumerate(((0, 0, 0.55, 2.2), (0.9, 0.5, 0.42, 1.5), (-0.8, 0.6, 0.45, 1.7), (0.4, -0.9, 0.4, 1.4),
                                        (-0.6, -0.7, 0.38, 1.2), (1.3, -0.3, 0.32, 1.0), (-1.4, -0.1, 0.34, 1.1))):
        y = PAN_Y + 0.2
        mb.lathe([(0.02, y + h, 1.0), (s, y + h * 0.65, 0.9), (s * 0.9, y + 0.1, 0.8), (0.02, y - 0.2, 0.7)], 6, bands[P.PAPER],
                 centre=(-PAN_X + dx, 0, sz + dz), phase=0.5 * k, cap_top=False)
    return mb.object("YG_BuySellStones", coll, mat)


def buy_sell_lanterns(coll, mat, bands):
    """Red paper lanterns hung at the front eave's corners."""
    mb = W.MeshBuilder()
    for x in LANTERN_X:
        mb.lathe([(0.0, 12.2, 1.0), (0.9, 11.9, 1.0), (1.2, 11.1, 1.0), (1.0, 10.3, 1.0), (0.0, 10.0, 1.0)], 12, bands[P.PAPER],
                 centre=(x, 0, HALL_FRONT + 1.2), cap_top=False)
    return mb.object("YG_BuySellLanterns", coll, mat)


PIECES = [blacksmith, blacksmith_glow, buy_sell, buy_sell_stones, buy_sell_lanterns]


def build():
    img, bands = W.atlas_image("StartingIsland_PropAtlas", 512, P.STRIPS)
    mat = W.textured_material("StartingIsland_PropMat", img)
    coll = W.collection("YG_Shops", W.collection("Yggdrasil"))
    W.clear_collection(coll)
    return [fn(coll, mat, bands) for fn in PIECES]


def export(objs):
    """assets/world/Yggdrasil/Yggdrasil_Shops.fbx (WB.storeKit("Yggdrasil", <import>, "YG_ShopsAnchor"))."""
    path = W.REPO + "/assets/world/Yggdrasil/Yggdrasil_Shops.fbx"
    W.export_batch(objs, path, image=YP.atlas_image(), anchor_name="YG_ShopsAnchor")
    return path
