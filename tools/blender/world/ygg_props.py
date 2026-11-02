"""Yggdrasil's kit and placements.

New pieces, on the Starting Island's prop atlas (start_props.STRIPS):
- YG_SpawnDais / YG_SpawnDaisGlow: a player's spawn slot, a two-tier stone seat with a jade inlay
  and a ring that lights for the player it belongs to; their name is cut into the stone behind it.
- YG_PlotStake: a talisman stake. Stakes and red cords mark out each plot kept for a building.
- YG_PlotBoard: the roofed notice board at a plot's front, naming what will stand there.

Everything else Yggdrasil places is the Starting Island's kit, stored in Studio under
WorldKit.Yggdrasil (SI_* names), including its Qi Spring, carried onto this rim by
ygg_island.SPRING_* .
"""
import math
import os
import random

import worldlib as W
import ygg_island as Y
import ygg_meshes as G
import start_island as S
import start_props as P

TAU = 2 * math.pi

# ---------- kit ----------
DAIS_TOP = 1.0
SLOT_STONE = (0.0, -11.0)              # the name stone stands behind the dais (local x, z; the dais faces +Z)
SLOT_PANEL = ((0.0, 2.15), (3.3, 2.0))  # its face: centre (x, y) and size, on its +Z side
STONE_FRONT = 0.48


def spawn_dais(coll, mat, bands):
    mb = W.MeshBuilder()
    mb.lathe([(7.0, DAIS_TOP, 0.95), (7.3, 0.9, 0.8), (7.3, 0.62, 0.6), (8.9, 0.55, 0.9), (9.3, 0.35, 0.7), (9.4, -1.0, 0.4)],
             64, bands[P.PALE], cap_top=False, u_repeat=3.0)
    # the jade inlay round the seat, and the seat inside it
    mb.lathe([(4.6, DAIS_TOP - 0.02, 0.9), (6.95, DAIS_TOP - 0.02, 0.8)], 64, bands[P.JADE], cap_top=False, u_repeat=2.0)
    mb.lathe([(0.0, DAIS_TOP, 0.9), (3.6, DAIS_TOP, 0.85)], 48, bands[P.PALE], cap_top=False, u_repeat=1.0)
    # six leaf-shaped steps on the lower tier, one for each slot round the World Tree
    for k in range(6):
        a = TAU * k / 6 + TAU / 12
        tip, root, w = 9.0, 7.4, 0.75
        pts = [(math.cos(a) * root - math.sin(a) * w, math.sin(a) * root + math.cos(a) * w),
               (math.cos(a) * tip, math.sin(a) * tip),
               (math.cos(a) * root + math.sin(a) * w, math.sin(a) * root - math.cos(a) * w)]
        P.slab_tile(mb, pts, 0.68, 0.5, bands[P.JADE], 0.5, 0.9)
    # the name stone: a low tablet with a rounded top, its face toward the dais
    sx, sz = SLOT_STONE
    poly = [(-2.1, -0.4), (2.1, -0.4), (2.1, 3.2)]
    for i in range(1, 10):
        a = math.pi * i / 10
        poly.append((math.cos(a) * 2.1, 3.2 + math.sin(a) * 0.9))
    poly.append((-2.1, 3.2))
    t = STONE_FRONT
    P.oriented(mb, [(sx + x, y, sz + t) for x, y in poly], (0, 0, 1), bands[P.PALE], 0.5, [0.9] * len(poly))
    P.oriented(mb, [(sx + x, y, sz - t) for x, y in poly], (0, 0, -1), bands[P.PALE], 0.5, [0.75] * len(poly))
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        P.oriented(mb, [(sx + a[0], a[1], sz + t), (sx + b[0], b[1], sz + t), (sx + b[0], b[1], sz - t), (sx + a[0], a[1], sz - t)],
                   (b[1] - a[1], -(b[0] - a[0]), 0), bands[P.PALE], 0.5, [0.7] * 4)
    (px, py), (pw, ph) = SLOT_PANEL
    panel = [(px - pw / 2 - 0.2, py - ph / 2 - 0.2), (px + pw / 2 + 0.2, py - ph / 2 - 0.2),
             (px + pw / 2 + 0.2, py + ph / 2 + 0.2), (px - pw / 2 - 0.2, py + ph / 2 + 0.2)]
    P.oriented(mb, [(sx + x, y, sz + t + 0.02) for x, y in panel], (0, 0, 1), bands[P.DARK], 0.5, [0.5] * 4)
    mb.box((sx, -0.1, sz), (5.0, 0.6, 1.6), bands[P.DARK], u=0.4, top_shade=0.8, side_shade=0.55)
    return mb.object("YG_SpawnDais", coll, mat)


def spawn_dais_glow(coll, mat, bands):
    mb = W.MeshBuilder()
    mb.lathe([(3.65, DAIS_TOP + 0.01, 1.0), (4.55, DAIS_TOP + 0.01, 1.0)], 64, bands[P.PAPER], cap_top=False, u_repeat=0.0)
    return mb.object("YG_SpawnDaisGlow", coll, mat)


STAKE_HEIGHT = 5.4
CORD_HEIGHT = 4.7     # where the cords tie on


def plot_stake(coll, mat, bands):
    mb = W.MeshBuilder()
    mb.box((0, STAKE_HEIGHT / 2 - 0.8, 0), (0.62, STAKE_HEIGHT + 1.6, 0.62), bands[P.WOOD], u=0.3, top_shade=0.8, side_shade=0.75)
    # bronze cap and the collar the cords tie to
    mb.lathe([(0.0, STAKE_HEIGHT + 0.75, 1.0), (0.5, STAKE_HEIGHT + 0.1, 0.85), (0.5, STAKE_HEIGHT - 0.1, 0.6)], 4,
             bands[P.BRONZE], phase=TAU / 8, cap_top=False, cap_bottom=True)
    mb.box((0, CORD_HEIGHT, 0), (0.78, 0.28, 0.78), bands[P.BRONZE], u=0.6, top_shade=0.9, side_shade=0.7)
    # a paper talisman on a peg, a red seal on it
    mb.box((0, 3.4, 0.44), (0.12, 0.12, 0.3), bands[P.WOOD], u=0.6)
    mb.box((0, 2.45, 0.6), (0.62, 1.9, 0.04), bands[P.PAPER], u=0.5, top_shade=0.9, side_shade=0.95)
    mb.box((0, 2.75, 0.63), (0.32, 0.32, 0.02), bands[P.LACQUER], u=0.5, top_shade=0.9, side_shade=0.9)
    mb.box((0, 2.15, 0.63), (0.08, 0.6, 0.02), bands[P.LACQUER], u=0.5, top_shade=0.9, side_shade=0.9)
    return mb.object("YG_PlotStake", coll, mat)


BOARD_PANEL = ((0.0, 4.0), (5.2, 2.9))   # the board's face: centre (x, y) and size, on its +Z side
BOARD_FRONT = 0.2


def plot_board(coll, mat, bands):
    mb = W.MeshBuilder()
    for x in (-3.3, 3.3):
        mb.box((x, 3.0, 0), (0.6, 7.2, 0.6), bands[P.WOOD], u=0.3, top_shade=0.8, side_shade=0.75)
        mb.box((x, 0.15, 0), (1.1, 0.5, 1.1), bands[P.DARK], u=0.4, top_shade=0.85, side_shade=0.6)
    (bx, by), (bw, bh) = BOARD_PANEL
    mb.box((bx, by, 0), (bw + 0.6, bh + 0.6, 2 * BOARD_FRONT), bands[P.WOOD], u=0.7, top_shade=0.75, side_shade=0.6)
    P.oriented(mb, [(bx - bw / 2, by - bh / 2, BOARD_FRONT + 0.01), (bx + bw / 2, by - bh / 2, BOARD_FRONT + 0.01),
                    (bx + bw / 2, by + bh / 2, BOARD_FRONT + 0.01), (bx - bw / 2, by + bh / 2, BOARD_FRONT + 0.01)],
               (0, 0, 1), bands[P.DARK], 0.5, [0.45] * 4)
    # a little gabled roof, lacquered, with a bronze ridge
    eave, ridge, half, depth = 6.25, 7.15, 4.3, 1.25
    for side in (1, -1):
        P.oriented(mb, [(-half, eave, side * depth), (half, eave, side * depth), (half, ridge, 0), (-half, ridge, 0)],
                   (0, depth, side * (ridge - eave)), bands[P.LACQUER], 0.5, [0.8, 0.8, 1.0, 1.0])
        P.oriented(mb, [(-half, eave, side * depth), (-half, eave - 0.18, side * depth), (half, eave - 0.18, side * depth), (half, eave, side * depth)],
                   (0, 0, side), bands[P.LACQUER], 0.5, [0.6] * 4)
    for x in (-half, half):
        sgn = 1 if x > 0 else -1
        P.oriented(mb, [(x, eave, depth), (x, ridge, 0), (x, eave, -depth)], (sgn, 0, 0), bands[P.LACQUER], 0.5, [0.55] * 3)
    mb.box((0, ridge + 0.08, 0), (2 * half + 0.3, 0.2, 0.28), bands[P.BRONZE], u=0.5, top_shade=1.0, side_shade=0.8)
    return mb.object("YG_PlotBoard", coll, mat)


KIT = [spawn_dais, spawn_dais_glow, plot_stake, plot_board]


# ---------- the Ascension Stele (the leaderboard) ----------
# An honour board like a memorial archway's: a dark slate board in a bronze frame on a stepped
# plinth, between two lacquered pillars under a tiled roof whose corners sweep up, a pearl of Qi
# on its ridge. Built on the Leaderboard plot: origin at the plot's centre on the ground, the board
# facing +Z (the Qi Compass). The board's face (STELE_PANEL) and the title plaque (STELE_TITLE)
# carry the names in the game.
STELE_PANEL = ((0.0, 8.6), (15.6, 9.6))     # the board's face: centre (x, y) and size, at z = STELE_FRONT
STELE_TITLE = ((0.0, 15.7), (6.2, 1.1))
STELE_FRONT = 0.2
BOARD_Z = -0.3                               # the board's and the pillars' centre line
PILLAR_X = 10.4
EAVE, RIDGE, ROOF_HALF, ROOF_DEPTH = 18.4, 22.4, 14.6, 4.6


def _roof(mb, bands):
    """Two tiled slopes from the ridge to the eaves, each corner sweeping up, with a lacquered
    soffit underneath and a thin edge all round."""
    cols, rows = 24, 6

    def point(i, j, side, drop=0.0):
        x = -ROOF_HALF + 2 * ROOF_HALF * i / cols
        t = j / rows
        lift = 1.5 * (abs(x) / ROOF_HALF) ** 4 * t ** 1.5
        y = RIDGE - (RIDGE - EAVE) * t ** 0.8 + lift - drop
        return (x, y, BOARD_Z + side * ROOF_DEPTH * t)
    for side in (1, -1):
        for i in range(cols):
            for j in range(rows):
                top = [point(i, j, side), point(i + 1, j, side), point(i + 1, j + 1, side), point(i, j + 1, side)]
                # tile channels running down the slope, lighter toward the ridge
                shade = 0.55 + 0.14 * (i % 2) + 0.2 * (1 - j / rows)
                P.oriented(mb, top, (0, 1, side * 0.6), bands[P.DARK], 0.5, [shade] * 4)
                under = [point(i, j, side, 0.4), point(i + 1, j, side, 0.4), point(i + 1, j + 1, side, 0.4), point(i, j + 1, side, 0.4)]
                P.oriented(mb, under, (0, -1, 0), bands[P.LACQUER], 0.5, [0.45] * 4)
        for i in range(cols):   # the eave's edge
            a, b = point(i, rows, side), point(i + 1, rows, side)
            P.oriented(mb, [a, b, point(i + 1, rows, side, 0.4), point(i, rows, side, 0.4)], (0, 0, side), bands[P.LACQUER], 0.5, [0.7] * 4)
        for i, sx in ((0, -1), (cols, 1)):   # the gable ends
            for j in range(rows):
                P.oriented(mb, [point(i, j, side), point(i, j + 1, side), point(i, j + 1, side, 0.4), point(i, j, side, 0.4)],
                           (sx, 0, 0), bands[P.LACQUER], 0.5, [0.6] * 4)
    mb.box((0, RIDGE + 0.15, BOARD_Z), (2 * ROOF_HALF - 1.0, 0.4, 0.6), bands[P.BRONZE], u=0.5, top_shade=1.0, side_shade=0.8)
    for sx in (-1, 1):   # the ridge's upturned ends
        mb.box((sx * (ROOF_HALF - 0.9), RIDGE + 0.7, BOARD_Z), (0.5, 1.1, 0.5), bands[P.BRONZE], u=0.5, top_shade=1.0, side_shade=0.8)
        mb.box((sx * (ROOF_HALF - 0.6), RIDGE + 1.2, BOARD_Z), (0.9, 0.35, 0.5), bands[P.BRONZE], u=0.5, top_shade=1.0, side_shade=0.8)
    # a bronze lotus cup on the ridge holding the pearl of Qi (stele_glow)
    mb.lathe([(0.55, RIDGE + 1.45, 1.0), (0.8, RIDGE + 1.3, 0.9), (0.32, RIDGE + 0.75, 0.7), (0.45, RIDGE + 0.35, 0.6)], 10,
             bands[P.BRONZE], centre=(0, 0, BOARD_Z), cap_top=True)


def stele(coll, mat, bands):
    mb = W.MeshBuilder()
    # the stepped plinth (its front steps lead up to the board)
    mb.box((0, 0.3, 0), (26, 1.6, 10), bands[P.PALE], u=0.3, top_shade=0.9, side_shade=0.65)
    mb.box((0, 1.4, 0), (23, 0.6, 8), bands[P.PALE], u=0.5, top_shade=0.95, side_shade=0.7)
    mb.box((0, 2.0, BOARD_Z), (20, 0.6, 6.4), bands[P.PALE], u=0.7, top_shade=1.0, side_shade=0.75)
    # the board, its bronze sill and frame, and the face the names are written on
    (px, py), (pw, ph) = STELE_PANEL
    mb.box((0, 2.65, BOARD_Z), (17.6, 0.7, 1.4), bands[P.BRONZE], u=0.5, top_shade=0.9, side_shade=0.75)
    mb.box((0, py, BOARD_Z), (pw + 1.4, ph + 1.6, 2 * (STELE_FRONT - BOARD_Z) - 0.02), bands[P.DARK], u=0.3, top_shade=0.5, side_shade=0.45)
    mb.box((0, py + ph / 2 + 0.95, BOARD_Z), (pw + 2.2, 0.5, 1.3), bands[P.BRONZE], u=0.5, top_shade=1.0, side_shade=0.8)
    for sx in (-1, 1):
        mb.box((sx * (pw / 2 + 0.85), py, BOARD_Z), (0.5, ph + 1.6, 1.3), bands[P.BRONZE], u=0.5, top_shade=1.0, side_shade=0.8)
    P.oriented(mb, [(px - pw / 2, py - ph / 2, STELE_FRONT + 0.01), (px + pw / 2, py - ph / 2, STELE_FRONT + 0.01),
                    (px + pw / 2, py + ph / 2, STELE_FRONT + 0.01), (px - pw / 2, py + ph / 2, STELE_FRONT + 0.01)],
               (0, 0, 1), bands[P.DARK], 0.5, [0.25] * 4)
    # the title plaque over the board
    (tx, ty), (tw, th) = STELE_TITLE
    mb.box((tx, ty, 0.0), (tw + 0.8, th + 0.6, 0.5), bands[P.BRONZE], u=0.5, top_shade=1.0, side_shade=0.8)
    P.oriented(mb, [(tx - tw / 2, ty - th / 2, 0.26), (tx + tw / 2, ty - th / 2, 0.26), (tx + tw / 2, ty + th / 2, 0.26), (tx - tw / 2, ty + th / 2, 0.26)],
               (0, 0, 1), bands[P.DARK], 0.5, [0.3] * 4)
    # the pillars: lacquered octagons on bronze bases, under bronze capitals, and the beam they carry
    for sx in (-1, 1):
        c = (sx * PILLAR_X, 0, BOARD_Z)
        mb.lathe([(0.85, 17.0, 0.9), (0.85, 3.2, 0.6)], 8, bands[P.LACQUER], centre=c, phase=TAU / 16, cap_top=False, u_repeat=1.0)
        mb.lathe([(1.0, 3.2, 0.9), (1.2, 2.9, 0.8), (1.2, 2.3, 0.6)], 8, bands[P.BRONZE], centre=c, phase=TAU / 16, cap_top=True)
        mb.lathe([(1.15, 17.4, 1.0), (1.15, 16.9, 0.8), (0.9, 16.7, 0.6)], 8, bands[P.BRONZE], centre=c, phase=TAU / 16, cap_top=True)
    mb.box((0, 17.9, BOARD_Z), (2 * PILLAR_X + 3.2, 1.0, 1.5), bands[P.LACQUER], u=0.5, top_shade=0.85, side_shade=0.7)
    _roof(mb, bands)
    return mb.object("YG_Stele", coll, mat)


def stele_glow(coll, mat, bands):
    """The pearl of Qi on the ridge and a fine line just inside the board's frame."""
    mb = W.MeshBuilder()
    r = 0.9
    profile = [(r * math.sin(math.pi * k / 8), RIDGE + 2.1 + r * math.cos(math.pi * k / 8), 1.0) for k in range(9)]
    mb.lathe(profile, 12, bands[P.PAPER], centre=(0, 0, BOARD_Z), cap_top=False)
    (px, py), (pw, ph) = STELE_PANEL
    z, w = STELE_FRONT + 0.03, 0.14
    hx, hy = pw / 2 - 0.25, ph / 2 - 0.25
    for (ax, ay), (bx, by) in (((-hx, -hy), (hx, -hy)), ((hx, -hy), (hx, hy)), ((hx, hy), (-hx, hy)), ((-hx, hy), (-hx, -hy))):
        nx, ny = (0, w) if ay == by else (w, 0)
        P.oriented(mb, [(px + ax - nx, py + ay - ny, z), (px + bx - nx, py + by - ny, z), (px + bx + nx, py + by + ny, z), (px + ax + nx, py + ay + ny, z)],
                   (0, 0, 1), bands[P.PAPER], 0.5, [1.0] * 4)
    return mb.object("YG_SteleGlow", coll, mat)


def build_stele():
    img, bands = W.atlas_image("StartingIsland_PropAtlas", 512, P.STRIPS)
    mat = W.textured_material("StartingIsland_PropMat", img)
    coll = W.collection("YG_Stele", W.collection(Y.NAME))
    W.clear_collection(coll)
    return [stele(coll, mat, bands), stele_glow(coll, mat, bands)]


def export_stele(objs):
    """assets/world/Yggdrasil/Yggdrasil_Stele.fbx (WB.storeKit("Yggdrasil", <import>, "YG_SteleAnchor"))."""
    path = W.REPO + "/assets/world/Yggdrasil/Yggdrasil_Stele.fbx"
    W.export_batch(objs, path, image=atlas_image(), anchor_name="YG_SteleAnchor")
    return path


def atlas_image():
    import bpy
    return bpy.data.images["StartingIsland_PropAtlas"]


def build():
    img, bands = W.atlas_image("StartingIsland_PropAtlas", 512, P.STRIPS)
    mat = W.textured_material("StartingIsland_PropMat", img)
    coll = W.collection("YG_Kit", W.collection(Y.NAME))
    W.clear_collection(coll)
    return [fn(coll, mat, bands) for fn in KIT]


# ---------- placements ----------
def ground(x, z):
    return Y.height(x, z)[0]


def face_yaw(fx, fz):
    """Yaw that turns a piece's local +Z toward (fx, fz)."""
    return math.atan2(fx, fz)


EGG_IDS = ["BeginnerQiEgg", "SpiritBreezeEgg", "ElementalCoreEgg"]


def egg_layout():
    """The three pedestals on an arc across the garden's east side, facing the paths in, 10 studs
    apart as on the Starting Island (their auras were tuned to that spacing)."""
    cx, cz, _ = Y.EGG_GARDEN
    out = []
    for eid, rel in zip(EGG_IDS, (-42, 0, 42)):
        a = math.radians(rel)
        x, z = cx + math.cos(a) * 14, cz + math.sin(a) * 14
        out.append((eid, x, z, face_yaw(cx - 6 - x, cz - z)))
    return out


def waystone_layout():
    out = []
    for route, (ex, ez) in list(Y.EXITS.items()) + [("RootPath", Y.ROOT_EXIT)]:
        L = math.hypot(ex, ez)
        dx, dz = ex / L, ez / L
        side = 7.5 if route == "RootPath" else 28.0   # beside the bridge's 40-stud deck
        x, z = ex - dx * 10 - dz * side, ez - dz * 10 + dx * side
        out.append((route, x, z, face_yaw(-dx, -dz)))
    return out


def slot_layout():
    """Each spawn dais: where it stands and the yaw that turns it toward the World Tree."""
    return [(x, z, face_yaw(-x, -z)) for x, z in Y.SLOTS]


def plot_layout():
    """Each plot: centre, size and the yaw that turns its local +Z out of its front."""
    out = {}
    for name, (cx, cz, w, d, facing) in Y.PLOTS.items():
        a = math.radians(facing)
        out[name] = (cx, cz, w, d, face_yaw(math.cos(a), math.sin(a)))
    return out


def lantern_spots():
    spots = []
    for b in (20, 55, 125, 160, 245, 315):           # the Root Court, clear of the paths that meet it
        spots.append(Y.polar(b, Y.COURT_R + 6))
    for b in (50, 70, 110, 130):                       # the Spawn Walk, between the daises
        spots.append(Y.polar(b, Y.SLOT_R + 6))
    cx, cz, r = Y.COMPASS
    for b in (-15, -165, 25, 155):                     # the Qi Compass, clear of its paths
        spots.append((cx + math.cos(math.radians(b)) * (r + 3.5), cz + math.sin(math.radians(b)) * (r + 3.5)))
    gx, gz, gr = Y.EGG_GARDEN
    for side in (-1, 1):                                # either side of the Egg Garden's west entrance
        spots.append((gx - gr - 2, gz + side * 7))
    for b in (180, 204):                                # the Market lane
        spots.append(Y.polar(b, Y.LANE_R - 7))
    ex, ez = 31.0, -27.0                                # the spring's path, as on the Starting Island
    for sgn in (-1, 1):
        spots.append(Y.from_start(ex + 0.647 * 4.5 * sgn, ez + 0.765 * 4.5 * sgn))
    return spots


# ---------- nature ----------
HERO = [  # (variant, x, z, yaw, scale): pines crowning the knolls, blossoms framing the arrivals
    ("SI_SpiritPineA", -118, 200, 0.6, 1.35), ("SI_SpiritPineB", -106, 214, 2.1, 1.1),
    ("SI_SpiritPineA", 122, 196, 3.9, 1.3), ("SI_SpiritPineA", -216, -66, 1.2, 1.25),
    ("SI_SpiritPineB", -78, -176, 5.0, 1.4), ("SI_SpiritPineA", -92, -164, 0.4, 1.05),
    ("SI_SpiritPineB", 172, -120, 2.8, 1.3),
    ("SI_BlossomTreeA", -42, 116, 1.1, 1.1), ("SI_BlossomTreeB", 42, 116, 2.4, 1.1),
    ("SI_BlossomTreeA", 196, -12, 4.0, 1.05), ("SI_BlossomTreeB", 192, 30, 0.3, 1.0),
]


def keepouts():
    """(x, z, radius) discs nothing is scattered into."""
    zones = [(0, 0, 96), (Y.COMPASS[0], Y.COMPASS[1], Y.COMPASS[2] + 8), (Y.EGG_GARDEN[0], Y.EGG_GARDEN[1], Y.EGG_GARDEN[2] + 4),
             (Y.LION_LAIR[0], Y.LION_LAIR[1], 26), (Y.SPRING_CENTRE[0], Y.SPRING_CENTRE[1], 32)]
    zones += [(x, z, Y.SLOT_PAD + 9) for x, z in Y.SLOTS]
    zones += [(x, z, 38) for x, z in Y.EXITS.values()] + [(Y.ROOT_EXIT[0], Y.ROOT_EXIT[1], 22)]
    zones += [(x, z, 13) for _, x, z, _ in waystone_layout()]
    zones += [(x, z, 9) for _, x, z, *_ in HERO]
    for b in G.GRIP_BEARINGS:   # where the gripping roots cross the meadow
        th = math.radians(b)
        R = Y.rim(th)
        for r in (R - 62, R - 44, R - 26, R - 10):
            zones.append((math.cos(th) * r, math.sin(th) * r, 15))
    import ygg_tree as T
    for k in T.LONG_ROOTS:      # where the long roots come down beyond the Root Court
        for p in T.root_points(k)[4:]:
            zones.append((p[0], p[2], 12))
    return zones


def scatter(rnd, count, min_gap, path_clear, rim_clear, plot_clear, taken, accept=None, tries=20000):
    out = []
    zones = keepouts()
    for _ in range(tries):
        if len(out) >= count:
            break
        x, z = rnd.uniform(-270, 270), rnd.uniform(-270, 270)
        if math.hypot(x, z) > Y.rim(math.atan2(z, x)) - rim_clear:
            continue
        if Y.path_distance(x, z) < path_clear:
            continue
        if any(Y.plot_distance(x, z, p) < plot_clear for p in Y.PLOTS.values()):
            continue
        if any(math.hypot(x - zx, z - zz) < zr for zx, zz, zr in zones):
            continue
        if any(math.hypot(x - tx, z - tz) < max(min_gap, tg) for tx, tz, tg in taken):
            continue
        if accept and not accept(x, z, rnd):
            continue
        out.append((x, z))
        taken.append((x, z, min_gap))
    return out


def near_knoll(x, z):
    return any(math.hypot(x - kx, z - kz) < kr * 1.3 for kx, kz, kr, _ in Y.KNOLLS)


def nature():
    rnd = random.Random(2027)
    items = []
    taken = [(x, z, 9) for _, x, z, *_ in HERO]
    for name, x, z, yaw, scale in HERO:
        items.append((name, x, z, yaw, scale, 0.6))
    for x, z in scatter(rnd, 64, 17, 7, 10, 9, taken):
        r = math.hypot(x, z)
        pine = near_knoll(x, z) or r > 185 or rnd.random() < 0.35
        name = ("SI_SpiritPineA" if rnd.random() < 0.5 else "SI_SpiritPineB") if pine else \
               ("SI_BlossomTreeA" if rnd.random() < 0.5 else "SI_BlossomTreeB")
        items.append((name, x, z, rnd.uniform(0, TAU), rnd.uniform(0.9, 1.25) * (1.1 if pine else 1.0), 0.6))
    for x, z in scatter(rnd, 48, 9, 3.5, 2, 4, taken, accept=lambda x, z, rr: near_knoll(x, z) or math.hypot(x, z) > 200 or rr.random() < 0.3):
        items.append(("SI_MossRockA" if rnd.random() < 0.45 else "SI_MossRockB", x, z, rnd.uniform(0, TAU), rnd.uniform(0.9, 1.6), 0.0))
    for x, z in scatter(rnd, 150, 5.5, 2.8, 3, 2, taken):
        name = rnd.choice(("SI_FlowersWhite", "SI_FlowersWarm", "SI_FlowersViolet"))
        items.append((name, x, z, rnd.uniform(0, TAU), rnd.uniform(0.9, 1.3), 0.05))
    return items


def placements():
    entries = {}

    def add(name, x, y, z, yaw=0.0, scale=1.0):
        entries.setdefault(name, []).append(((x, y, z), yaw, scale))
    for pos, yaw in G.shelf_placements(16):
        add("SI_RootShelf", *pos, yaw)
    add("SI_CradleFloor", *G.CRADLE_FLOOR)
    cx, cz, _ = Y.COMPASS
    add("SI_QiCompass", cx, 0.2, cz)
    add("SI_QiCompassGlow", cx, 0.2, cz)
    for x, z in lantern_spots():
        yaw = face_yaw(-x, -z)
        add("SI_StoneLantern", x, ground(x, z), z, yaw)
        add("SI_LanternLight", x, ground(x, z), z, yaw)
    ox, oz = Y.SPRING_OFFSET
    for name in ("SI_SpringWater", "SI_SpringRim", "SI_SpringSpillway", "SI_SpringRock"):
        add(name, ox, 0, oz, Y.SPRING_YAW)
    for x, z in P.LOTUS_STONES:
        nx, nz = Y.from_start(x, z)
        add("SI_LotusStone", nx, S.POOL_WATER + 0.3, nz, P.face_yaw(x - S.POOL_A[0], z - S.POOL_A[1]) + Y.SPRING_YAW)
    for name, x, z, yaw, scale, sink in nature():
        add(name, x, ground(x, z) - sink, z, yaw, scale)
    return entries


def write_placements(path=W.REPO + "/src/worldbuild/Placements/Yggdrasil.lua"):
    entries = placements()
    pcx, pcz = P.pool_centre()
    scx, scz = Y.from_start(pcx, pcz)
    spill = Y.from_start(P.SPILL[-1][0], P.SPILL[-1][1])
    lines = ["-- Generated by tools/blender/world/ygg_props.py. Do not edit by hand.",
             "-- Island-local Roblox studs. Kit entries place each piece's authored origin; SI_* pieces are the",
             "-- Starting Island's kit (WorldKit.Yggdrasil), YG_* Yggdrasil's own.", "return {", "    Kit = {"]
    for name in sorted(entries):
        lines.append("        %s = {" % name)
        for (x, y, z), yaw, scale in entries[name]:
            extra = ", Scale = %.3f" % scale if abs(scale - 1) > 1e-6 else ""
            lines.append("            { Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f%s }," % (x, y, z, yaw, extra))
        lines.append("        },")
    lines.append("    },")
    lines.append("    EggStands = {")
    for eid, x, z, yaw in egg_layout():
        lines.append('        { EggId = "%s", Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f, EggRest = %.2f },'
                     % (eid, x, ground(x, z), z, yaw, P.PEDESTAL_TOP))
    lines.append("    },")
    lines.append("    Waystones = {")
    for route, x, z, yaw in waystone_layout():
        lines.append('        { Route = "%s", Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f },' % (route, x, ground(x, z), z, yaw))
    lines.append("    },")
    lines.append("    WaystonePanel = { Centre = Vector3.new(0, 4.25, 0.42), Size = Vector2.new(1.7, 4.1) },")
    lines.append("    -- the six spawn slots: each dais faces the World Tree (local +Z), its name stone behind it")
    lines.append("    SpawnSlots = {")
    for x, z, yaw in slot_layout():
        lines.append("        { Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f }," % (x, ground(x, z), z, yaw))
    lines.append("    },")
    lines.append("    SlotTop = %g, -- the dais's top, over its origin" % DAIS_TOP)
    (px, py), (pw, ph) = SLOT_PANEL
    lines.append("    SlotPanel = { Centre = Vector3.new(%g, %g, %.2f), Size = Vector2.new(%g, %g) },"
                 % (SLOT_STONE[0] + px, py, SLOT_STONE[1] + STONE_FRONT + 0.04, pw, ph))
    lines.append("    -- plots kept for buildings to come: centre, size (width along the front, depth) and the yaw")
    lines.append("    -- that turns local +Z out of the front, where the notice board stands")
    lines.append("    Plots = {")
    for name, (x, z, w, d, yaw) in plot_layout().items():
        lines.append("        %s = { Centre = Vector3.new(%.2f, %.2f, %.2f), Size = Vector2.new(%g, %g), Yaw = %.4f },"
                     % (name, x, 0.3, z, w, d, yaw))
    lines.append("    },")
    (bx, by), (bw, bh) = BOARD_PANEL
    lines.append("    PlotBoardPanel = { Centre = Vector3.new(%g, %g, %.2f), Size = Vector2.new(%g, %g) }," % (bx, by, BOARD_FRONT + 0.03, bw, bh))
    lines.append("    PlotCordHeight = %g," % CORD_HEIGHT)
    (sx, sy), (sw, sh) = STELE_PANEL
    (tx, ty), (tw, th) = STELE_TITLE
    lines.append("    -- the Ascension Stele (the leaderboard, on the Leaderboard plot): its board's face and title plaque")
    lines.append("    SteleBoard = { Centre = Vector3.new(%g, %g, %.2f), Size = Vector2.new(%g, %g) }," % (sx, sy, STELE_FRONT + 0.03, sw, sh))
    lines.append("    SteleTitle = { Centre = Vector3.new(%g, %g, %.2f), Size = Vector2.new(%g, %g) }," % (tx, ty, 0.29, tw, th))
    lines.append("    Spawn = Vector3.new(%.2f, %.2f, %.2f)," % (Y.COMPASS[0], 0.2 + 1.98, Y.COMPASS[1]))
    lines.append("    SpringCentre = Vector3.new(%.2f, %.2f, %.2f)," % (scx, S.POOL_WATER, scz))
    lines.append("    SpillEnd = Vector3.new(%.2f, %.2f, %.2f)," % (spill[0], P.SPILL[-1][2] + 0.35, spill[1]))
    lines.append("    Relics = { IslandRoot = Vector3.new(%.2f, %.2f, %.2f) }," % G.RELIC)
    lines += ["}", ""]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path
