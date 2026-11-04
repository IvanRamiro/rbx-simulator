"""Yggdrasil's three shop buildings, each on its plot (ygg_island.PLOTS), on the prop atlas
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
- The Marketplace, the Coin-Tree Market: a three-tier pagoda of jade-glazed tiles at the back of a
  courtyard, striped stalls of goods down both sides, an arched gate on the lane, strings of red lanterns
  overhead, and at the centre a bronze money tree hung with glowing coins. Its own FBX, since the other
  two were imported first (build_market, export_market).

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
    "Marketplace": ((0.0, 11.9, 15.72), (11.0, 1.7)),
}
PROMPTS = {          # where each shop's prompt stands: at the anvil, at the foot of the scale
    "Blacksmith": (0.0, FLOOR + 2.6, 2.4),
    "BuySell": (0.0, FLOOR + 2.4, SCALE[1] + 3.2),
    # the Marketplace has no prompt yet: what it sells isn't decided
}
# the Coin-Tree Market
TOWER_Z = -9.0
TREE = (0.0, 3.6)
GATE_Z = 15.0
STALL_Z = (1.0, 6.2, 11.4)
FX = {               # where the game adds each shop's effects: (kind, (x, y, z))
    "Marketplace": [("Coins", (TREE[0], FLOOR + 9.0, TREE[1])), ("Lantern", (-9.0, 9.4, 8.0)), ("Lantern", (9.0, 9.4, 8.0))],
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


# ---------- the Marketplace ----------
def market_tier(mb, bands, glazed, half, depth, y0, y1, eave, ridge, roof_half, roof_depth, lift, lattice):
    """One storey of the pagoda over the one below: paper walls in a lacquer frame, under a glazed roof."""
    z = TOWER_Z
    # a hair inside the frame and the frieze above, so their faces don't fight
    mb.box((0, (y0 + y1) / 2 - 0.05, z), (2 * half - 0.06, y1 - y0 - 0.1, 2 * depth - 0.06), bands[P.PAPER], u=0.5, top_shade=0.95, side_shade=0.92)
    for sx in (-1, 1):
        for sz in (-1, 1):
            mb.box((sx * half, (y0 + y1) / 2, z + sz * depth), (0.7, y1 - y0, 0.7), bands[P.LACQUER], u=0.5, top_shade=0.9, side_shade=0.75)
    mb.box((0, y1 - 0.2, z + depth), (2 * half, 0.5, 0.45), bands[P.LACQUER], u=0.5, top_shade=0.9, side_shade=0.75)
    mb.box((0, y0 + 0.2, z + depth), (2 * half, 0.5, 0.45), bands[P.LACQUER], u=0.5, top_shade=0.9, side_shade=0.75)
    for k in range(1, lattice):   # the lattice over the paper, front and back
        x = -half + 2 * half * k / lattice
        for sz in (-1, 1):
            mb.box((x, (y0 + y1) / 2, z + sz * (depth + 0.05)), (0.22, y1 - y0, 0.2), bands[P.WOOD], u=0.4, top_shade=0.7, side_shade=0.6)
    roof = (eave, ridge, roof_half, roof_depth, z, lift)
    YP.tiled_roof(mb, glazed, eave, ridge, roof_half, roof_depth, z, lift=lift, cols=int(roof_half * 2), rows=5)
    YP.roof_walls(mb, bands[P.LACQUER], bands[P.WOOD], roof, half, z + depth, z - depth, y1 - 0.1)


def market_goods(mb, bands, sx, z, kind):
    """What one stall sells, set out on its counter (at x = sx * 12.7) and on the shelf behind."""
    top = FLOOR + 2.7
    x = sx * 12.7
    if kind == "Fruit":       # baskets heaped with spirit peaches
        for dz in (-1.4, 0.0, 1.4):
            mb.lathe([(0.7, top + 0.6, 0.9), (0.55, top, 0.6)], 8, bands[P.WOOD], centre=(x, 0, z + dz), cap_top=True)
            for ox, oz in ((-0.25, 0), (0.25, 0.1), (0, -0.28)):
                mb.lathe([(0.0, top + 1.2, 1.0), (0.3, top + 0.95, 0.95), (0.28, top + 0.7, 0.8), (0.0, top + 0.55, 0.7)], 6, bands[P.BLOSSOM],
                         centre=(x + ox, 0, z + dz + oz), cap_top=False)
    elif kind == "Jars":      # glazed jars of elixir, stoppered in red
        for dz, band in ((-1.5, P.JADE), (-0.5, P.BRONZE), (0.5, P.JADE), (1.5, P.BRONZE)):
            mb.lathe([(0.24, top + 1.15, 0.9), (0.28, top + 0.95, 0.8), (0.5, top + 0.65, 0.95), (0.42, top + 0.1, 0.65), (0.3, top, 0.55)], 8, bands[band],
                     centre=(x, 0, z + dz), cap_top=False)
            mb.lathe([(0.0, top + 1.35, 1.0), (0.2, top + 1.25, 0.9), (0.2, top + 1.1, 0.8)], 6, bands[P.LACQUER], centre=(x, 0, z + dz), cap_top=False)
    elif kind == "Cloth":     # folded bolts of silk, stacked in colours
        for dz, a, b in ((-1.3, P.LACQUER, P.PAPER), (0.0, P.JADE, P.LACQUER), (1.3, P.PAPER, P.JADE)):
            for level, band in enumerate((a, b, a)):
                mb.box((x, top + 0.2 + 0.4 * level, z + dz), (1.3, 0.36, 1.1), bands[band], u=0.5, top_shade=1.0, side_shade=0.75)
    elif kind == "Gourds":    # spirit gourds, tied at the waist
        for dz in (-1.4, -0.45, 0.5, 1.45):
            mb.lathe([(0.03, top + 1.3, 0.8), (0.22, top + 1.15, 0.95), (0.3, top + 0.9, 0.9), (0.15, top + 0.72, 0.7), (0.46, top + 0.4, 0.95), (0.3, top, 0.6)], 8,
                     bands[P.JADE], centre=(x, 0, z + dz), cap_top=False)
    elif kind == "Scrolls":   # scrolls standing in brushpots
        for dz in (-1.2, 0.2, 1.4):
            mb.lathe([(0.55, top + 0.9, 0.85), (0.5, top, 0.6)], 8, bands[P.BRONZE], centre=(x, 0, z + dz), cap_top=True)
            for ox, oz, h in ((-0.2, 0.1, 1.9), (0.2, -0.1, 2.2), (0.0, 0.25, 1.7)):
                mb.lathe([(0.14, top + h, 1.0), (0.14, top + 0.8, 0.85)], 6, bands[P.PAPER], centre=(x + ox, 0, z + dz + oz), cap_top=True)
    elif kind == "Crystals":  # uncut spirit stones on a cloth
        mb.box((x, top + 0.05, z), (1.6, 0.12, 3.8), bands[P.LACQUER], u=0.5, top_shade=0.95, side_shade=0.7)
        for k, (ox, dz, r, h) in enumerate(((0, -1.2, 0.34, 1.4), (0.3, -0.3, 0.26, 1.0), (-0.3, 0.2, 0.3, 1.2), (0.25, 1.0, 0.36, 1.5), (-0.25, 1.5, 0.22, 0.8))):
            y = top + 0.1
            mb.lathe([(0.02, y + h, 1.0), (r, y + h * 0.6, 0.95), (r * 0.8, y, 0.75)], 6, bands[P.JADE], centre=(x + ox, 0, z + dz), phase=0.6 * k, cap_top=False)
    # the shelf on the back wall, with crates and jars on it
    back = sx * 17.9
    mb.box((back, FLOOR + 3.6, z), (1.0, 0.2, 4.4), bands[P.WOOD], u=0.4, top_shade=0.9, side_shade=0.65)
    for dz, band in ((-1.4, P.WOOD), (0.1, P.BRONZE), (1.4, P.WOOD)):
        mb.box((back, FLOOR + 4.15, z + dz), (0.8, 0.9, 1.0), bands[band], u=0.6, top_shade=0.9, side_shade=0.7)


def market_stall(mb, bands, sx, z, stripe, kind, last):
    """One stall, open to the courtyard, under a striped awning sloping down toward it. Stalls share
    their posts with their neighbours: only the last in a row adds the one at its far end."""
    half = 2.6
    mb.box((sx * 18.5, FLOOR + 4.6, z), (0.5, 9.2, 2 * half), bands[P.WOOD], u=0.3, top_shade=0.7, side_shade=0.55)
    for dz in (-half, half) if last else (-half,):
        mb.box((sx * 11.4, FLOOR + 3.0, z + dz), (0.45, 6.0, 0.45), bands[P.LACQUER], u=0.5, top_shade=0.9, side_shade=0.75)
    # the counter
    mb.box((sx * 12.7, FLOOR + 1.25, z), (1.9, 2.5, 4.5), bands[P.WOOD], u=0.35, top_shade=0.7, side_shade=0.55)
    mb.box((sx * 12.7, FLOOR + 2.58, z), (2.2, 0.2, 4.8), bands[P.PALE], u=0.5, top_shade=1.0, side_shade=0.75)
    market_goods(mb, bands, sx, z, kind)
    # the awning: five stripes, a valance along its front edge
    high, low = FLOOR + 9.6, FLOOR + 6.3
    n = 5
    for k in range(n):
        band = bands[stripe] if k % 2 == 0 else bands[P.PAPER]
        z0, z1 = z - half + 2 * half * k / n, z - half + 2 * half * (k + 1) / n
        outer, inner = sx * 18.9, sx * 10.6
        quad = [(outer, high, z0), (outer, high, z1), (inner, low, z1), (inner, low, z0)]
        P.oriented(mb, quad, (sx * 0.3, 1, 0), band, 0.5, [0.98, 0.98, 0.85, 0.85])
        under = [(outer, high - 0.15, z0), (outer, high - 0.15, z1), (inner, low - 0.15, z1), (inner, low - 0.15, z0)]
        P.oriented(mb, under, (0, -1, 0), band, 0.5, [0.5] * 4)
        P.oriented(mb, [(inner, low, z0), (inner, low, z1), (inner, low - 0.8, z1), (inner, low - 0.8, z0)], (-sx, 0, 0), band, 0.5, [0.8] * 4)
    # a little banner hung from the awning's edge
    mb.box((sx * 10.5, low - 1.7, z), (0.1, 1.8, 1.1), bands[stripe], u=0.5, top_shade=0.95, side_shade=0.95)


def market(coll, mat, bands):
    mb = W.MeshBuilder()
    base(mb, bands, 38.4, 31)
    glazed = dict(bands)                 # the pagoda's and the gate's tiles are glazed jade
    glazed[P.DARK] = bands[P.JADE]

    # the courtyard's paving: a jade round in a bronze ring under the tree, pale flags to the gate
    tx, tz = TREE
    mb.lathe([(0.0, FLOOR + 0.06, 0.9), (6.2, FLOOR + 0.06, 0.8)], 24, bands[P.JADE], centre=(tx, 0, tz), cap_top=False)
    mb.lathe([(6.2, FLOOR + 0.1, 0.9), (6.9, FLOOR + 0.1, 0.8), (6.9, FLOOR, 0.6)], 24, bands[P.BRONZE], centre=(tx, 0, tz), cap_top=False)

    # the pagoda's ground floor: open at the front, its back and sides closed, a long counter inside
    z, depth = TOWER_Z, 6.0
    for x in (-7.2, -2.6, 2.6, 7.2):
        pillar(mb, bands, x, z + depth, 11.6, r=0.75)
    for x in (-7.2, 7.2):
        pillar(mb, bands, x, z - depth, 11.6, r=0.75)
    mb.box((0, 12.0, z + depth), (15.4, 0.9, 1.1), bands[P.LACQUER], u=0.5, top_shade=0.85, side_shade=0.7)
    mb.box((0, FLOOR + 5.3, z - depth), (14.6, 10.6, 0.5), bands[P.WOOD], u=0.3, top_shade=0.6, side_shade=0.5)
    for sx in (-1, 1):
        mb.box((sx * 7.2, FLOOR + 5.3, z), (0.4, 10.6, 2 * depth), bands[P.PAPER], u=0.5, top_shade=0.95, side_shade=0.9)
        for dz in (-3, 0, 3):
            mb.box((sx * 7.4, FLOOR + 5.3, z + dz), (0.2, 10.6, 0.3), bands[P.WOOD], u=0.4, top_shade=0.7, side_shade=0.6)
    mb.box((0, FLOOR + 1.5, z + 1.6), (11.0, 3.0, 2.2), bands[P.WOOD], u=0.35, top_shade=0.7, side_shade=0.55)
    mb.box((0, FLOOR + 3.1, z + 1.6), (11.6, 0.26, 2.6), bands[P.JADE], u=0.5, top_shade=1.0, side_shade=0.8)
    for row in range(3):                 # shelves of goods on the back wall
        y = FLOOR + 3.2 + 2.4 * row
        mb.box((0, y, z - depth + 0.6), (13.4, 0.2, 0.9), bands[P.BARK], u=0.5, top_shade=0.85, side_shade=0.65)
        for k in range(7):
            band = (P.JADE, P.BRONZE, P.LACQUER, P.PAPER)[(k + row) % 4]
            mb.box((-5.7 + 1.9 * k, y + 0.6, z - depth + 0.6), (1.1, 1.0, 0.7), bands[band], u=0.5, top_shade=0.95, side_shade=0.72)
    roof = (12.3, 18.2, 10.6, 8.8, z, 1.8)
    YP.tiled_roof(mb, glazed, *roof[:5], lift=roof[5], cols=21, rows=6)
    YP.roof_walls(mb, bands[P.LACQUER], bands[P.WOOD], roof, 7.2, z + depth, z - depth, 12.3)

    market_tier(mb, bands, glazed, 5.2, 3.9, 14.6, 21.2, 21.0, 25.8, 8.0, 6.4, 1.5, 6)
    market_tier(mb, bands, glazed, 3.4, 2.5, 23.6, 28.8, 28.6, 32.4, 5.6, 4.6, 1.2, 4)
    # the finial: bronze rings and a jade pearl
    mb.lathe([(0.75, 33.2, 0.9), (0.5, 33.0, 0.8), (0.5, 32.2, 0.6)], 8, bands[P.BRONZE], centre=(0, 0, z), cap_top=True)
    mb.lathe([(0.22, 35.6, 0.95), (0.22, 33.2, 0.7)], 6, bands[P.BRONZE], centre=(0, 0, z), cap_top=True)
    for y, r in ((34.0, 0.55), (34.7, 0.42)):
        mb.lathe([(r, y + 0.12, 0.95), (r, y - 0.12, 0.7)], 8, bands[P.BRONZE], centre=(0, 0, z), cap_top=True, cap_bottom=True)
    mb.lathe([(0.0, 36.5, 1.0), (0.42, 36.2, 0.95), (0.55, 35.85, 0.85), (0.3, 35.5, 0.7), (0.0, 35.45, 0.6)], 10, bands[P.JADE], centre=(0, 0, z), cap_top=False)

    # the stalls down both sides of the courtyard
    goods = {-1: ("Fruit", "Cloth", "Scrolls"), 1: ("Jars", "Crystals", "Gourds")}
    stripes = {-1: (P.LACQUER, P.JADE, P.LACQUER), 1: (P.JADE, P.LACQUER, P.JADE)}
    for sx in (-1, 1):
        for k, sz in enumerate(STALL_Z):
            market_stall(mb, bands, sx, sz, stripes[sx][k], goods[sx][k], k == len(STALL_Z) - 1)

    # the stalls' outer walls, seen from the rest of the island: timber frames over a stone course, a
    # lattice window to each stall, a banner between
    for sx in (-1, 1):
        wall = sx * 18.85
        mb.box((wall, FLOOR + 0.9, 6.2), (0.3, 1.8, 15.8), bands[P.PALE], u=0.4, top_shade=0.9, side_shade=0.68)
        mb.box((wall, FLOOR + 8.6, 6.2), (0.3, 0.5, 15.8), bands[P.BARK], u=0.5, top_shade=0.8, side_shade=0.7)
        for z_post in (-1.5, 3.6, 8.8, 13.9):
            mb.box((wall, FLOOR + 4.7, z_post), (0.35, 8.2, 0.55), bands[P.BARK], u=0.5, top_shade=0.8, side_shade=0.7)
        for sz in STALL_Z:
            mb.box((wall, FLOOR + 5.0, sz), (0.2, 3.6, 3.0), bands[P.PAPER], u=0.5, top_shade=0.95, side_shade=0.92)
            for dz in (-1.5, -0.5, 0.5, 1.5):
                mb.box((wall + sx * 0.08, FLOOR + 5.0, sz + dz), (0.14, 3.7, 0.16), bands[P.WOOD], u=0.4, top_shade=0.7, side_shade=0.6)
            for dy in (-1.8, 0.0, 1.8):
                # a little proud of the uprights, so the crossings don't fight
                mb.box((wall + sx * 0.1, FLOOR + 5.0 + dy, sz), (0.14, 0.16, 3.1), bands[P.WOOD], u=0.4, top_shade=0.7, side_shade=0.6)

    # the yard behind each side of the pagoda: a low wall, stacked crates, barrels and sacks
    for sx in (-1, 1):
        mb.box((sx * 15.0, FLOOR + 1.0, -15.1), (8.4, 2.0, 0.6), bands[P.PALE], u=0.4, top_shade=0.95, side_shade=0.68)
        mb.box((sx * 19.0, FLOOR + 1.0, -8.0), (0.6, 2.0, 13.6), bands[P.PALE], u=0.4, top_shade=0.95, side_shade=0.68)
        mb.box((sx * 15.0, FLOOR + 2.1, -15.1), (8.8, 0.25, 0.9), bands[P.DARK], u=0.5, top_shade=0.95, side_shade=0.7)
        mb.box((sx * 19.0, FLOOR + 2.13, -8.2), (0.9, 0.25, 14.2), bands[P.DARK], u=0.5, top_shade=0.95, side_shade=0.7)
        for x, y, z_, size in ((16.4, 0.9, -12.8, 1.8), (14.4, 0.8, -13.2, 1.6), (15.6, 2.6, -13.0, 1.5), (16.8, 0.8, -10.4, 1.6)):
            mb.box((sx * x, FLOOR + y, z_), (size, size, size), bands[P.WOOD], u=0.6, top_shade=0.85, side_shade=0.65)
        for x, z_ in ((12.8, -8.6), (14.6, -7.8), (13.6, -6.2)):
            mb.lathe([(0.75, FLOOR + 2.3, 0.9), (0.95, FLOOR + 1.2, 0.8), (0.75, FLOOR, 0.6)], 8, bands[P.WOOD], centre=(sx * x, 0, z_), cap_top=True)
            mb.lathe([(0.98, FLOOR + 1.45, 0.9), (0.98, FLOOR + 1.1, 0.75)], 8, bands[P.BRONZE], centre=(sx * x, 0, z_), cap_top=False)
        for x, z_ in ((16.6, -5.2), (15.2, -4.0)):
            mb.lathe([(0.0, FLOOR + 1.9, 0.9), (0.7, FLOOR + 1.6, 0.85), (0.95, FLOOR + 0.8, 0.75), (0.8, FLOOR, 0.6)], 8, bands[P.PAPER],
                     centre=(sx * x, 0, z_), cap_top=False, cap_bottom=True)

    # the bronze money tree: a stone plinth, a gnarled trunk and limbs reaching out from it
    y0 = FLOOR
    mb.lathe([(2.2, y0 + 1.6, 0.95), (2.7, y0 + 1.2, 0.8), (3.2, y0 + 0.6, 0.75), (3.7, y0 + 0.6, 0.85), (3.7, y0, 0.6)], 12, bands[P.PALE], centre=(tx, 0, tz), cap_top=True)
    tube(mb, [(tx + 0.1, y0 + 1.4, tz), (tx - 0.4, y0 + 4.0, tz + 0.2), (tx + 0.3, y0 + 7.0, tz - 0.2), (tx, y0 + 9.5, tz)],
         lambda t: 0.95 - 0.55 * t, 8, bands[P.BRONZE], per=4)
    for ox, oz, sign in ((-1.0, 0.0, 1), (0.8, 0.5, 1), (0.0, -1.0, 1), (0.9, -0.7, 1)):   # roots over the plinth
        tube(mb, [(tx + ox * 0.3, y0 + 2.6, tz + oz * 0.3), (tx + ox * 1.2, y0 + 1.7, tz + oz * 1.2), (tx + ox * 2.0, y0 + 1.5, tz + oz * 2.0)],
             lambda t: 0.42 - 0.3 * t, 5, bands[P.BRONZE], per=3)
    for tip in tree_limbs():
        (px, py, pz), (qx, qy, qz), (rx, ry, rz) = tip
        tube(mb, [(px, py, pz), (qx, qy, qz), (rx, ry, rz)], lambda t: 0.3 - 0.2 * t, 5, bands[P.BRONZE], per=3)
    for (cx, cy, cz) in tree_coins():    # the cords the coins hang from
        mb.box((cx, cy + 0.85, cz), (0.05, 0.75, 0.05), bands[P.LACQUER], u=0.5)

    # the gate on the lane: two lacquer pillars, a beam, the name board and a glazed roof
    for x in (-9.5, 9.5):
        pillar(mb, bands, x, GATE_Z, 13.2, r=0.72)
        mb.lathe([(1.4, FLOOR + 1.0, 0.9), (1.6, FLOOR + 0.5, 0.8), (1.6, FLOOR, 0.6)], 8, bands[P.PALE], centre=(x, 0, GATE_Z), phase=TAU / 16, cap_top=True)
    mb.box((0, 13.7, GATE_Z), (21.6, 0.8, 1.0), bands[P.LACQUER], u=0.5, top_shade=0.85, side_shade=0.7)
    mb.box((0, 10.1, GATE_Z), (19.0, 0.5, 0.7), bands[P.LACQUER], u=0.5, top_shade=0.85, side_shade=0.7)
    (sx_, sy_, sz_), (sw, sh) = SIGNS["Marketplace"]
    name_board(mb, bands, ((sx_, sy_, sz_), (sw, sh)))
    YP.tiled_roof(mb, glazed, 14.2, 16.6, 12.4, 2.4, GATE_Z, lift=1.1, cols=24, rows=3)

    # the strings the lanterns hang from
    for sx in (-1, 1):
        ends = [(sx * 9.5, 12.8, GATE_Z - 0.6), (sx * 9.0, 10.4, 8.0), (sx * 8.0, 11.6, -2.8)]
        tube(mb, ends, lambda t: 0.05, 4, bands[P.DARK], per=6)
    return mb.object("YG_Market", coll, mat)


def tree_limbs():
    """The money tree's limbs: (start, middle, tip), climbing and spreading in a ring."""
    tx, tz = TREE
    limbs = []
    for k in range(8):
        a = TAU * k / 8 + 0.3
        c, s_ = math.cos(a), math.sin(a)
        low = k % 2 == 0
        y = FLOOR + (6.8 if low else 8.2)
        reach = 4.6 if low else 3.6
        rise = 1.6 if low else 2.4
        limbs.append(((tx, y, tz), (tx + c * reach * 0.55, y + rise * 0.8, tz + s_ * reach * 0.55), (tx + c * reach, y + rise, tz + s_ * reach)))
    return limbs


def tree_coins():
    """Where each coin hangs: below each limb's tip and halfway along it."""
    spots = []
    for k, (_, mid, tip) in enumerate(tree_limbs()):
        spots.append((tip[0], tip[1] - 1.1, tip[2]))
        spots.append((mid[0], mid[1] - 1.4 - 0.3 * (k % 2), mid[2]))
    return spots


def market_coins(coll, mat, bands):
    """The money tree's spirit coins, each turned its own way, and the pearl at its crown."""
    mb = W.MeshBuilder()
    for k, (cx, cy, cz) in enumerate(tree_coins()):
        coin(mb, bands[P.PAPER], (cx, cy, cz), 0.48, 0.13, 1 if k % 2 == 0 else -1, depth=0.09, n=8)
    tx, tz = TREE
    y = FLOOR + 10.0
    mb.lathe([(0.0, y + 1.5, 1.0), (0.6, y + 1.15, 1.0), (0.8, y + 0.7, 1.0), (0.55, y + 0.2, 1.0), (0.0, y, 1.0)], 10, bands[P.PAPER], centre=(tx, 0, tz), cap_top=False)
    return mb.object("YG_MarketCoins", coll, mat)


def market_lanterns(coll, mat, bands):
    """Red paper lanterns along the two strings, and a pair at the gate."""
    mb = W.MeshBuilder()
    spots = [(sx * 9.5, 12.4 - 1.4 * (1 - abs(2 * t - 1)), GATE_Z - 0.6 + (-2.8 - GATE_Z + 0.6) * t) for sx in (-1, 1) for t in (0.18, 0.42, 0.66, 0.88)]
    spots = [(x * (1 - 0.16 * ((GATE_Z - 0.6 - z) / (GATE_Z + 2.2))), y, z) for x, y, z in spots]
    for x, y, z in spots + [(-7.2, 12.0, GATE_Z + 0.3), (7.2, 12.0, GATE_Z + 0.3)]:
        mb.lathe([(0.0, y, 1.0), (0.42, y - 0.15, 1.0), (0.58, y - 0.55, 1.0), (0.46, y - 0.95, 1.0), (0.0, y - 1.1, 1.0)], 8, bands[P.PAPER], centre=(x, 0, z), cap_top=False)
    return mb.object("YG_MarketLanterns", coll, mat)


PIECES = [blacksmith, blacksmith_glow, buy_sell, buy_sell_stones, buy_sell_lanterns]
MARKET_PIECES = [market, market_coins, market_lanterns]


def build():
    img, bands = W.atlas_image("StartingIsland_PropAtlas", 512, P.STRIPS)
    mat = W.textured_material("StartingIsland_PropMat", img)
    coll = W.collection("YG_Shops", W.collection("Yggdrasil"))
    W.clear_collection(coll)
    return [fn(coll, mat, bands) for fn in PIECES]


def build_market():
    img, bands = W.atlas_image("StartingIsland_PropAtlas", 512, P.STRIPS)
    mat = W.textured_material("StartingIsland_PropMat", img)
    coll = W.collection("YG_Market", W.collection("Yggdrasil"))
    W.clear_collection(coll)
    return [fn(coll, mat, bands) for fn in MARKET_PIECES]


def export_market(objs):
    """assets/world/Yggdrasil/Yggdrasil_Market.fbx (WB.storeKit("Yggdrasil", <import>, "YG_MarketAnchor"))."""
    path = W.REPO + "/assets/world/Yggdrasil/Yggdrasil_Market.fbx"
    W.export_batch(objs, path, image=YP.atlas_image(), anchor_name="YG_MarketAnchor")
    return path


def export(objs):
    """assets/world/Yggdrasil/Yggdrasil_Shops.fbx (WB.storeKit("Yggdrasil", <import>, "YG_ShopsAnchor"))."""
    path = W.REPO + "/assets/world/Yggdrasil/Yggdrasil_Shops.fbx"
    W.export_batch(objs, path, image=YP.atlas_image(), anchor_name="YG_ShopsAnchor")
    return path
