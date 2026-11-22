"""Dawnspire's territory (2026-11-22): every piece, placement, collision box, marker, waterfall, light and plant of the Orthodox side's extension, in the hall's
PAD FRAME (origin at the Orthodox pad's centre lifted 0.5, +z away from the plaza, +x outward; y = Y over the plaza - 16.5 for ground, - 16 for a floor mesh
that lies 0.5 over its terrace's terrain). Plain Python: dawnspire_run.py makes the Blender scenes, renders, QA and FBX files; dawnspire_lua.py writes
src/worldbuild/Placements/MurimDawnspire.lua; dawnspire_verify.py checks the numbers; murim_dawnspire_terrain.py is the ground it stands on.

Terraces (terrain level Y over the plaza -> floor y in this frame): garden 25 -> 9, residence 43 -> 27, tea 16 -> 0, yard 20 -> 4, exhibition 25 -> 9.
"""
import json
import math
import os

import dawnspire_kit as D
import murim_dawnspire_terrain as T
from hq_kit import Piece

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
VEG_JSON = os.path.join(REPO, "assets", "world", "MurimCrossing", "Dawnspire", "veg_pieces.json")


def G(Y):
    """Frame y of the ground of a terrace at terrain level Y."""
    return Y - 16.5


def Fl(Y):
    """Frame y of a floor mesh on a terrace at level Y (0.5 over its terrain)."""
    return Y - 16.0


Y_GARDEN, Y_RES, Y_TEA, Y_YARD, Y_EXH = T.Y_GARDEN, T.Y_RESIDENCE, T.Y_TEA, T.Y_YARD, T.Y_EXHIBIT
PI = math.pi
FACE = {"S": 0.0, "E": -PI / 2, "N": PI, "W": PI / 2}      # a piece facing -z turned to face: south (-z), east (+x), north (+z), west (-x)

# ======================================================================================================================
# the pieces: name -> (family, builder). The FBX files: Buildings, Courts, Props.
# ======================================================================================================================
FILES = {"Buildings": "Dawnspire_Buildings", "Courts": "Dawnspire_Courts", "Props": "Dawnspire_Props"}
BUILDERS = {
    # buildings
    ("Buildings", "House"): D.house, ("Buildings", "Wing"): D.wing, ("Buildings", "Tower"): D.tower,
    ("Buildings", "TeaPavilion"): D.tea_pavilion, ("Buildings", "RoundPavilion"): D.round_pavilion, ("Buildings", "YardGate"): D.yard_gate,
    ("Buildings", "ExhibitionHall"): D.exhibition_hall, ("Buildings", "Corridor"): D.corridor,
    # courts: walls, screens, floors, stage, pond, bridges, stairs, rails, causeway
    ("Courts", "WallPlain12"): lambda: D.wall_plain(L=12.0), ("Courts", "WallPlain6"): lambda: D.wall_plain(L=6.0),
    ("Courts", "WallWindow12"): D.wall_window, ("Courts", "WallMoon12"): D.wall_moon, ("Courts", "WallGate24"): D.wall_gate,
    ("Courts", "ScreenClouds"): lambda: D.screen_wall(kind="clouds"), ("Courts", "ScreenWaves"): lambda: D.screen_wall(kind="waves"),
    ("Courts", "FloorYard"): lambda: D.floor_slab(x0=-28.0, x1=28.0, z0=-30.25, z1=30.25, ring=(0.0, 0.0, 9.0)),
    ("Courts", "FloorTea"): lambda: D.floor_slab(x0=-18.0, x1=18.0, z0=-15.0, z1=15.0, ring=None),
    ("Courts", "FloorForecourt"): lambda: D.floor_slab(x0=-26.0, x1=26.0, z0=-12.5, z1=12.5, ring=None),
    ("Courts", "FloorResidence"): lambda: D.floor_slab(x0=-30.0, x1=30.0, z0=-14.0, z1=18.5, ring=(0.0, 3.0, 6.0)),
    ("Courts", "Stage"): lambda: D.stage(W=16.0, D=16.0), ("Courts", "TeaPond"): D.tea_pond,
    ("Courts", "BridgeFront"): lambda: D.arch_bridge(L=28.0, rise=6), ("Courts", "BridgeGarden"): lambda: D.arch_bridge(L=24.0, rise=6),
    ("Courts", "RearStair"): D.rear_stair, ("Courts", "Stair4"): lambda: D.stair_block(n=4, width=12.0), ("Courts", "Stair5"): lambda: D.stair_block(n=5, width=12.0),
    ("Courts", "Rail8"): D.rail8, ("Courts", "Landing"): D.landing, ("Courts", "Causeway"): D.causeway,
    # props
    ("Props", "LanternPillar"): D.lantern_pillar, ("Props", "LanternLow"): D.lantern_low, ("Props", "Burner"): D.burner, ("Props", "Bench"): D.bench,
    ("Props", "TeaTable"): D.tea_table, ("Props", "Rack"): D.weapon_rack, ("Props", "Post"): D.training_post, ("Props", "PlumPosts"): D.plum_posts,
    ("Props", "Weights"): D.stone_weights, ("Props", "ExhBay"): D.exh_bay, ("Props", "RegentPlinth"): D.regent_plinth,
}
# pieces authored in the pad frame (origin = the frame's), placed at 0
UNIQUE_AT_ORIGIN = {("Courts", "Causeway")}


def key(family, name):
    return "Dawnspire_%s_%s" % (family, name)


# ======================================================================================================================
# collision boxes, per piece, in the piece's own frame: (x0, x1, y0, y1, z0, z1)
# ======================================================================================================================
def _col(x, z, hw, y0, y1, hd=None):
    hd = hw if hd is None else hd
    return (x - hw, x + hw, y0, y1, z - hd, z + hd)


def _ring_points(n, R, rot):
    return [(R * math.sin(rot + 2 * PI * i / n), -R * math.cos(rot + 2 * PI * i / n)) for i in range(n)]


def bridge_boxes(L, rise, w=8.0, spring=5.0, thick=1.3):
    tread = 1.5
    run = rise * tread
    flat = L - 2 * run
    out = []
    for k in range(1, rise + 1):
        out.append((-L / 2 + (k - 1) * tread, -L / 2 + k * tread, k - 1.0, float(k), -w / 2, w / 2))
        out.append((L / 2 - k * tread, L / 2 - (k - 1) * tread, k - 1.0, float(k), -w / 2, w / 2))
        for z0, z1 in ((-w / 2 - 0.8, -w / 2), (w / 2, w / 2 + 0.8)):
            out.append((-L / 2 + (k - 1) * tread, -L / 2 + k * tread, k, k + 1.9, z0, z1))
            out.append((L / 2 - k * tread, L / 2 - (k - 1) * tread, k, k + 1.9, z0, z1))
    out.append((-flat / 2, flat / 2, rise - thick, float(rise), -w / 2, w / 2))
    for z0, z1 in ((-w / 2 - 0.8, -w / 2), (w / 2, w / 2 + 0.8)):
        out.append((-flat / 2, flat / 2, rise, rise + 1.9, z0, z1))
    return out


def stair_boxes(n, width, y0=0.0, z0=0.0, tread=1.5):
    out = []
    for k in range(1, n + 1):
        za, zb = z0 + (k - 1) * tread, z0 + k * tread
        out.append((-width / 2, width / 2, y0 + k - 1.0, y0 + k, za, zb))
        out.append((width / 2, width / 2 + 0.8, y0 + k - 1.0, y0 + k + 1.7, za, zb))
        out.append((-width / 2 - 0.8, -width / 2, y0 + k - 1.0, y0 + k + 1.7, za, zb))
    return out


def moon_boxes(L=12.0, H=7.6, r=3.1):
    cy = 0.25 + r
    out = []
    edges = [0.55, 1.5, 2.6, 3.8, 5.0, 6.0, H]
    out.append((-r - 0.7, r + 0.7, 0.0, 0.55, -0.55, 0.55))
    for ya, yb in zip(edges, edges[1:]):
        ext = max(abs(ya - cy), abs(yb - cy))
        gap = math.sqrt(r * r - ext * ext) if ext < r else 0.0
        if gap <= 0.3:
            out.append((-L / 2, L / 2, ya, yb, -0.55, 0.55))
        else:
            out.append((-L / 2, -gap, ya, yb, -0.55, 0.55))
            out.append((gap, L / 2, ya, yb, -0.55, 0.55))
    return out


def piece_colliders(family, name):
    """Boxes (x0, x1, y0, y1, z0, z1) in the piece's frame, with a role name; collision is only ever these (the visual meshes never collide)."""
    k = (family, name)
    c = []
    if k == ("Buildings", "House"):
        a, d, wall = 20.0, 7.0, 6.4
        top = 1.0 + wall - 1.5
        c += [(-a - 2.1, a + 2.1, -3.0, 1.0, -d - 2.3, d + 1.3), (-4.5, 4.5, -3.0, 0.3, -d - 4.0, -d - 2.3), (-4.5, 4.5, -3.0, 0.65, -d - 3.6, -d - 2.3)]
        for x in (-20, -12, -4, 4, 12, 20):
            c += [_col(x, -d, 0.85, 1.0, 1.0 + wall), _col(x, d, 0.85, 1.0, 1.0 + wall)]
        c += [_col(-20, 0, 0.85, 1.0, 1.0 + wall), _col(20, 0, 0.85, 1.0, 1.0 + wall)]
        zf = -d + 4.2
        c += [(-19.1, -3.2, 1.0, top, zf - 0.45, zf + 0.45), (3.2, 19.1, 1.0, top, zf - 0.45, zf + 0.45), (-a - 0.6, a + 0.6, 1.0, top, d - 0.45, d + 0.45)]
        c += [(sx * a - 0.45, sx * a + 0.45, 1.0, top, -d, d) for sx in (-1, 1)]
    elif k == ("Buildings", "Wing"):
        a, d, wall = 9.0, 5.0, 5.2
        top = 1.0 + wall - 1.5
        c += [(-a - 1.8, a + 1.8, -3.0, 1.0, -d - 2.2, d + 1.2)]
        for x in (-9, -3, 3, 9):
            c += [_col(x, -d, 0.85, 1.0, 1.0 + wall), _col(x, d, 0.85, 1.0, 1.0 + wall)]
        zf = -d + 2.4
        c += [(-8.1, -2.6, 1.0, top, zf - 0.45, zf + 0.45), (2.6, 8.1, 1.0, top, zf - 0.45, zf + 0.45), (-a - 0.5, a + 0.5, 1.0, top, d - 0.45, d + 0.45)]
        c += [(sx * a - 0.45, sx * a + 0.45, 1.0, top, -d, d) for sx in (-1, 1)]
    elif k == ("Buildings", "YardGate"):
        a, d, wall = 10.0, 3.0, 7.0
        c += [(-a - 1.7, a + 1.7, -3.0, 0.5, -d - 2.1, d + 1.5)]
        top = 0.5 + 1.0 + wall - 1.5
        for x in (-10.0, -4.0, 4.0, 10.0):
            c += [_col(x, -d, 0.85, 0.5, 8.5), _col(x, d, 0.85, 0.5, 8.5)]
        for x0, x1 in ((-9.1, -4.9), (4.9, 9.1)):
            c += [(x0, x1, 0.5, top, -d - 0.45, -d + 0.45), (x0, x1, 0.5, top, d - 0.45, d + 0.45)]
        c += [(sx * a - 0.45, sx * a + 0.45, 0.5, top, -d + 0.9, d - 0.9) for sx in (-1, 1)]
    elif k == ("Buildings", "Tower"):
        c += [(-8.5, 8.5, -3.0, 1.0, -8.5, 8.5)]
        for (x, z) in _ring_points(8, 7.2, -PI / 8):
            c += [_col(x, z, 0.8, 1.0, 6.6)]
        c += [(6.1, 7.2, 1.0, 3.3, -2.75, 2.75), (-7.2, -6.1, 1.0, 3.3, -2.75, 2.75)]       # the cardinal rails (the diagonal one has none)
    elif k == ("Buildings", "TeaPavilion"):
        c += [(-6.5, 6.5, -3.0, 1.0, -6.1, 6.1)]
        for (x, z) in _ring_points(6, 5.6, -PI / 6):
            c += [_col(x, z, 0.85, 1.0, 7.0)]
    elif k == ("Buildings", "RoundPavilion"):
        c += [(-6.0, 6.0, -3.0, 1.0, -6.0, 6.0)]
        sides12 = "OORRROOORRRO"
        for ci, (x, z) in enumerate(_ring_points(12, 4.7, -PI / 12)):
            if sides12[ci - 1] == "O" and sides12[ci] == "O":
                continue
            c += [_col(x, z, 0.65, 1.0, 6.4)]
        c += [(4.1, 4.9, 1.0, 3.2, -1.2, 1.2), (-4.9, -4.1, 1.0, 3.2, -1.2, 1.2)]
    elif k == ("Buildings", "ExhibitionHall"):
        e = D.EXH
        a = e["nb"] * e["bay"] / 2
        y0, wall = e["floor"], e["wall"]
        top = y0 + wall - 1.5
        c += [(-a - 2.7, a + 2.7, -3.0, y0, -e["d_col"] - 2.7, e["d_rear"] + 1.7), (-6.0, 6.0, -3.0, 1.0, -e["d_col"] - 4.4, -e["d_col"] - 2.7)]
        for i in range(e["nb"] + 1):
            c += [_col(-a + i * e["bay"], -e["d_col"], 0.85, y0, y0 + wall)]
        df = e["d_front"]
        c += [(-a - 0.4, -3.0, y0, top, -df - 0.45, -df + 0.45), (3.0, a + 0.4, y0, top, -df - 0.45, -df + 0.45), (-a - 0.9, a + 0.9, y0, top, e["d_rear"] - 0.45, e["d_rear"] + 0.45)]
        c += [(sx * (a + 0.2) - 0.45, sx * (a + 0.2) + 0.45, y0, top, -df, e["d_rear"]) for sx in (-1, 1)]
    elif k == ("Buildings", "Corridor"):
        W = 5.2
        for i in range(3):
            for z in (-W / 2, W / 2):
                c += [_col(-4.0 + i * 4.0, z, 0.55, 0.0, 4.6)]
        c += [(-4.0, 4.0, 0.0, 3.0, W / 2 - 0.3, W / 2 + 0.3), (-4.5, 4.5, -2.0, 0.0, -W / 2 - 0.7, W / 2 + 0.7)]
    elif k[0] == "Courts" and name.startswith("WallPlain") or k == ("Courts", "WallWindow12"):
        L = 6.0 if name.endswith("6") else 12.0
        c += [(-L / 2, L / 2, -1.5, 5.0, -0.65, 0.65)]
    elif k == ("Courts", "WallMoon12"):
        c += moon_boxes()
    elif k == ("Courts", "WallGate24"):
        c += [(-12.0, -4.2, -1.5, 5.0, -0.65, 0.65), (4.2, 12.0, -1.5, 5.0, -0.65, 0.65), (-4.95, -3.25, -1.5, 7.5, -0.9, 0.9), (3.25, 4.95, -1.5, 7.5, -0.9, 0.9)]
    elif name.startswith("Screen"):
        c += [(-7.9, 7.9, -1.5, 1.3, -1.6, 1.6), (-6.5, 6.5, 1.3, 7.1, -0.6, 0.6)]
    elif name.startswith("Floor"):
        pass                                    # (floors are made from the terrace's own slab below)
    elif k == ("Courts", "Stage"):
        c += [(-8.4, 8.4, -2.0, 3.0, -8.4, 8.4), (-4.0, 4.0, 0.0, 2.0, -9.75, -8.25), (-4.0, 4.0, 0.0, 1.0, -11.25, -9.75)]
        for sx in (-1, 1):
            for sz in (-1, 1):
                c += [_col(sx * 7.1, sz * 7.1, 0.5, 3.0, 5.4)]
    elif k == ("Courts", "TeaPond"):
        c += [(-7.2, 7.2, -1.5, 0.95, -4.2, 4.2)]
    elif k == ("Courts", "BridgeFront"):
        c += bridge_boxes(28.0, 6)
    elif k == ("Courts", "BridgeGarden"):
        c += bridge_boxes(24.0, 6)
    elif k == ("Courts", "RearStair"):
        c += stair_boxes(9, 16.0)
        c += [(-8.0, 8.0, 8.0, 9.0, 13.5, 19.5), (8.0, 8.8, 8.0, 10.7, 13.5, 19.5), (-8.8, -8.0, 8.0, 10.7, 13.5, 19.5)]
        c += stair_boxes(9, 16.0, y0=9.0, z0=19.5)
        for sx in (-1, 1):                                    # the rills' beds (shallow, walkable)
            xa, xb = (9.1, 11.5) if sx > 0 else (-11.5, -9.1)
            xo0, xo1 = (11.5, 12.3) if sx > 0 else (-12.3, -11.5)
            for kk in range(1, 10):
                c += [(xa, xb, kk - 1.0, kk - 0.18, (kk - 1) * 1.5, kk * 1.5), (xo0, xo1, kk - 1.0, kk + 0.5, (kk - 1) * 1.5, kk * 1.5)]
                c += [(xa, xb, 9 + kk - 1.0, 9 + kk - 0.18, 19.5 + (kk - 1) * 1.5, 19.5 + kk * 1.5), (xo0, xo1, 9 + kk - 1.0, 9 + kk + 0.5, 19.5 + (kk - 1) * 1.5, 19.5 + kk * 1.5)]
            c += [(xa, xb, 8.0, 8.82, 13.5, 19.5), (xo0, xo1, 8.0, 9.5, 13.5, 19.5)]
    elif k == ("Courts", "Stair4"):
        c += stair_boxes(4, 12.0)
    elif k == ("Courts", "Stair5"):
        c += stair_boxes(5, 12.0)
    elif k == ("Courts", "Rail8"):
        c += [(-4.55, 4.55, -1.2, 2.0, -0.55, 0.55)]
    elif k == ("Courts", "Landing"):
        c += [(-2.5, 2.5, -2.5, 0.0, -4.5, 4.5)]
    elif k == ("Courts", "Causeway"):
        c += [(-7.2, 7.2, 1.5, 9.0, 33.8, 40.8), (-36.0, -7.2, 2.0, 9.6, 38.2, 40.8), (7.2, 36.0, 2.0, 9.6, 38.2, 40.8)]
    elif k == ("Props", "LanternPillar"):
        c += [_col(0, 0, 0.7, 0.0, 4.4)]
    elif k == ("Props", "LanternLow"):
        c += [_col(0, 0, 0.7, 0.0, 2.2)]
    elif k == ("Props", "Burner"):
        c += [_col(0, 0, 1.4, 0.0, 3.4)]
    elif k == ("Props", "Bench"):
        c += [(-2.5, 2.5, 0.0, 1.4, -0.7, 0.7)]
    elif k == ("Props", "TeaTable"):
        c += [_col(0, 0, 1.75, 0.0, 1.7)] + [_col(3.0 * math.cos(2 * PI * i / 4 + PI / 4), 3.0 * math.sin(2 * PI * i / 4 + PI / 4), 0.7, 0.0, 1.0) for i in range(4)]
    elif k == ("Props", "Rack"):
        c += [(-2.7, 2.7, 0.0, 4.7, -0.7, 0.7)]
    elif k == ("Props", "Post"):
        c += [_col(0, 0, 0.85, 0.0, 5.6)]
    elif k == ("Props", "PlumPosts"):
        spots = [(0.0, 0.0, 2.8)] + [(3.4 * math.cos(a), 3.4 * math.sin(a), 2.0) for a in (0.0, PI / 2, PI, 3 * PI / 2)] + \
                [(6.0 * math.cos(a), 6.0 * math.sin(a), 1.2) for a in (PI / 4, 3 * PI / 4, 5 * PI / 4, 7 * PI / 4)]
        c += [_col(x, z, 0.5, 0.0, h) for x, z, h in spots]
    elif k == ("Props", "Weights"):
        c += [(-2.2, 2.2, 0.0, 2.2, -1.1, 1.1)]
    elif k == ("Props", "ExhBay"):
        c += [(-2.4, 2.4, 0.0, 1.0, -1.7, -0.1), (-2.4, 2.4, 1.0, 6.2, -0.55, 0.0)]
    elif k == ("Props", "RegentPlinth"):
        c += [(-9.0, 9.0, -1.0, 1.0, -2.6, 2.6), (-8.0, 8.0, 1.0, 5.4, -2.0, 2.0)]
    return c


# ======================================================================================================================
# the plan: placements, markers, falls, lights, vegetation
# ======================================================================================================================
EDGE_RAIL = []          # (x, z, yaw, y) rails on exposed terrace edges, filled in build_all
_VEG = None


def veg():
    global _VEG
    if _VEG is None:
        _VEG = json.load(open(VEG_JSON))
    return _VEG


class Plan:
    def __init__(self):
        self.pieces = {}
        self.placements = []
        self.colliders = []          # dicts: name, x0..z1 (pad frame), optional yaw
        self.marks = {}
        self.falls = []
        self.lights = []
        self.veg = []                # dicts: piece, x, y, z, yaw, scale, folder
        self.paths = []              # walk-check paths: (label, [(x, z), ...])
        self.footprints = []         # (label, x0, x1, z0, z1) building footprints (the terrain paves them)
        self.spots = {}              # NPC places etc.

    def piece(self, family, name):
        k = key(family, name)
        if k not in self.pieces:
            p = BUILDERS[(family, name)]()
            p.finish()
            self.pieces[k] = p
        return k

    def put(self, family, name, x, y, z, yaw=0.0, role="decor", light=False, collide=True, **extra):
        k = self.piece(family, name)
        d = dict(piece=k, family=family, name=name, x=x, y=y, z=z, yaw=yaw, scale=1.0, role=role)
        if light:
            d["light"] = True
        d.update(extra)
        self.placements.append(d)
        if collide:
            c, s = math.cos(yaw), math.sin(yaw)
            sxs = extra.get("scale_x", 1.0)
            for (x0, x1, y0, y1, z0, z1) in piece_colliders(family, name):
                x0, x1 = x0 * sxs, x1 * sxs
                pts = [(px * c + pz * s, -px * s + pz * c) for px in (x0, x1) for pz in (z0, z1)]
                self.colliders.append(dict(name=name, x0=x + min(p[0] for p in pts), x1=x + max(p[0] for p in pts), y0=y + y0, y1=y + y1,
                                           z0=z + min(p[1] for p in pts), z1=z + max(p[1] for p in pts)))
        return d

    def box(self, name, x0, x1, y0, y1, z0, z1):
        self.colliders.append(dict(name=name, x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z1))

    def tree(self, name, x, z, Y, yaw=0.0, scale=1.0, folder="Vegetation"):
        """A plant or rock of the vegetation library at terrain level Y: its collision boxes (rotated by yaw) join the colliders."""
        k = "Dawnspire_%s" % name
        meta = veg()["pieces"][k]
        d = dict(piece=k, x=x, y=G(Y), z=z, yaw=yaw, scale=scale, folder=folder)
        self.veg.append(d)
        c, s = math.cos(yaw), math.sin(yaw)
        for b in meta["collision"]:
            cx, cz = (b["x0"] + b["x1"]) / 2 * scale, (b["z0"] + b["z1"]) / 2 * scale
            self.colliders.append(dict(name=name.split("_")[1], x0=x + cx * c + cz * s - (b["x1"] - b["x0"]) / 2 * scale, x1=x + cx * c + cz * s + (b["x1"] - b["x0"]) / 2 * scale,
                                       y0=G(Y) + b["y0"] * scale, y1=G(Y) + b["y1"] * scale, z0=z - cx * s + cz * c - (b["z1"] - b["z0"]) / 2 * scale,
                                       z1=z - cx * s + cz * c + (b["z1"] - b["z0"]) / 2 * scale, yaw=yaw, rotated=True, cx=x + cx * c + cz * s, cz=z - cx * s + cz * c,
                                       sx=(b["x1"] - b["x0"]) * scale, sz=(b["z1"] - b["z0"]) * scale))
        return d


def wall_line(P, family, y, x0, x1, z, pieces, yaw=0.0):
    """Walls of the listed (name, length) in a row from x0 along x at depth z (or along z for yaw +-pi/2)."""
    cur = x0
    for name, L in pieces:
        cx = cur + L / 2
        P.put(family, name, cx, y, z, yaw=yaw, role="wall")
        cur += L
    return cur


def build_all():
    P = Plan()
    TY, FY = G, Fl
    # ------------------------------------------------------------------------------------------------ the garden (terrain 25)
    y = FY(Y_GARDEN)
    P.put("Courts", "Causeway", 0.0, 0.0, 0.0, role="unique")
    for (name, cx) in (("WallPlain12", -30.0), ("WallPlain12", -18.0), ("WallGate24", 0.0), ("WallPlain12", 18.0), ("WallPlain12", 30.0)):
        P.put("Courts", name, cx, y, 56.0, role="wall")
    P.put("Props", "LanternPillar", -6.6, y, 54.2, light=True)
    P.put("Props", "LanternPillar", 6.6, y, 54.2)
    P.put("Buildings", "RoundPavilion", 23.0, y - 0.5, 87.0, yaw=0.0, role="pavilion", light=False)       # (0.5 down: its podium is one step over the garden's ground)
    P.put("Courts", "RearStair", 0.0, y - 0.5, 96.0, role="stair")           # (its first step is one stud over the garden's ground)
    P.box("StairApron", -8.0, 8.0, y - 3.0, y, 92.5, 96.0)                     # (an invisible apron, level with the floors, so the foot is one clean step)
    P.put("Props", "LanternLow", -11.0, y, 93.5)
    P.put("Props", "LanternLow", 11.0, y, 93.5)
    # the garden bridge to the exhibition terrace, and its landings
    P.put("Courts", "BridgeGarden", 50.0, y, 68.0, role="bridge")
    P.put("Courts", "Landing", 36.5, y, 68.0, role="landing", collide=True)
    P.put("Courts", "Landing", 63.5, y, 68.0, role="landing")
    # ------------------------------------------------------------------------------------------------ the residence (terrain 43)
    y = FY(Y_RES)
    P.put("Courts", "FloorResidence", 0.0, y, 143.0, role="floor")
    P.box("FloorResidence", -30.0, 30.0, y - 3.0, y, 129.0, 161.5)
    P.put("Buildings", "House", 0.0, y, 172.0, role="house")
    P.put("Buildings", "Wing", -24.0, y, 145.0, yaw=FACE["E"], role="wing")
    P.put("Buildings", "Wing", 24.0, y, 145.0, yaw=FACE["W"], role="wing")
    for (name, cx) in (("WallWindow12", -24.0), ("WallPlain12", -12.0), ("WallMoon12", 0.0), ("WallPlain12", 12.0), ("WallWindow12", 24.0)):
        P.put("Courts", name, cx, y, 131.0, role="wall")
    for sx in (-1, 1):
        for zc in (137.0, 149.0, 161.0):
            P.put("Courts", "WallPlain12", sx * 31.6, y, zc, yaw=FACE["E"] if sx < 0 else FACE["W"], role="wall")
    P.put("Courts", "ScreenClouds", 0.0, y, 138.0, role="screen")
    P.put("Props", "LanternLow", -5.4, y, 132.9, light=True)
    P.put("Props", "LanternLow", 5.4, y, 132.9)
    # ------------------------------------------------------------------------------------------------ the tea terrace (terrain 16)
    y = FY(Y_TEA)
    P.put("Courts", "FloorTea", 83.0, y, -43.0, role="floor")
    P.box("FloorTea", 65.0, 101.0, y - 3.0, y, -58.0, -28.0)
    P.put("Buildings", "TeaPavilion", 88.0, y, -43.0, role="pavilion", light=True)
    for cx in (74.0, 82.0):
        P.put("Buildings", "Corridor", cx, y, -29.0, role="corridor")
    P.put("Courts", "TeaPond", 78.0, y, -57.0, role="pond")
    P.put("Props", "TeaTable", 99.0, y, -44.0, role="table")
    P.put("Props", "TeaTable", 74.0, y, -39.0, role="table")
    for (x, z, yaw) in ((82.0, -59.0, 0.0), (92.0, -59.0, 0.0), (64.5, -34.0, FACE["E"]), (100.5, -36.0, FACE["W"])):
        P.put("Props", "Bench", x, y, z, yaw=yaw)
    P.put("Props", "LanternPillar", 70.5, y, -55.5, light=True)
    P.put("Props", "LanternPillar", 70.5, y, -46.5)
    P.put("Courts", "Landing", 67.0, y, -51.0, role="landing")           # the bridge's tea end
    P.put("Courts", "BridgeFront", 50.5, y, -51.0, role="bridge")
    P.put("Courts", "Landing", 34.0, y, -51.0, role="landing")           # the court's side
    P.put("Courts", "Stair4", 94.0, y, -30.0, yaw=0.0, role="stair")
    # ------------------------------------------------------------------------------------------------ the training yard (terrain 20)
    y = FY(Y_YARD)
    P.put("Courts", "FloorYard", 94.0, y, 14.25, role="floor")
    P.box("FloorYard", 66.0, 122.0, y - 3.0, y, -16.0, 44.5)
    P.box("YardForecourt", 84.0, 104.0, y - 3.0, y, -24.0, -15.5)
    P.put("Buildings", "YardGate", 94.0, G(Y_YARD), -16.0, role="gate", light=True)
    # south wall (the gate leaves 66..84 and 104..122), west and east walls, north wall (the tower stands in it)
    wall_line(P, "Courts", y, 66.0, 84.0, -16.0, [("WallPlain12", 12.0), ("WallPlain6", 6.0)])
    wall_line(P, "Courts", y, 104.0, 122.0, -16.0, [("WallPlain12", 12.0), ("WallPlain6", 6.0)])
    for xw, face in ((64.5, "E"), (123.5, "W")):
        for i, (name_, zc) in enumerate((("WallPlain12", -10.0), ("WallPlain12", 2.0), ("WallPlain12", 14.0), ("WallPlain12", 26.0), ("WallPlain12", 38.0), ("WallPlain6", 44.0))):
            P.put("Courts", name_, xw, y, zc, yaw=FACE[face], role="wall")
    wall_line(P, "Courts", y, 66.0, 83.0, 44.0, [("WallPlain12", 12.0), ("WallPlain6", 5.0)])
    wall_line(P, "Courts", y, 105.0, 122.0, 44.0, [("WallPlain6", 5.0), ("WallPlain12", 12.0)])
    P.put("Buildings", "Tower", 94.0, y - 1.0, 32.0, role="tower")
    P.put("Courts", "Stage", 113.5, y, 22.0, role="stage")
    for i, zc in enumerate((-4.0, 5.0, 14.0, 23.0, 32.0)):
        P.put("Props", "Rack", 67.4, y, zc, yaw=FACE["E"], role="rack")
    for (x, z) in ((78.0, -6.0), (78.0, 4.0), (78.0, 14.0), (86.0, -6.0), (86.0, 4.0), (86.0, 14.0)):
        P.put("Props", "Post", x, y, z, role="post")
    P.put("Props", "PlumPosts", 108.0, y, 0.0, role="plum")
    for (x, z, yaw) in ((111.0, -11.0, 0.0), (117.0, -11.0, 0.0), (111.0, -6.0, 0.0), (117.0, -6.0, 0.0)):
        P.put("Props", "Weights", x, y, z, yaw=yaw, role="weights")
    P.put("Props", "LanternPillar", 83.0, y, -18.5)
    P.put("Props", "LanternPillar", 105.0, y, -18.5)
    P.put("Courts", "Stair5", 94.0, y, 44.5, role="stair")
    # ------------------------------------------------------------------------------------------------ the exhibition terrace (terrain 25)
    y = FY(Y_EXH)
    P.put("Courts", "FloorForecourt", 92.0, y, 64.5, role="floor")
    P.box("FloorForecourt", 66.0, 118.0, y - 3.0, y, 52.0, 77.0)
    P.put("Buildings", "ExhibitionHall", 92.0, y, 88.0, role="hall")
    for i, dx in enumerate((-15.0, -9.0, -3.0, 3.0, 9.0, 15.0)):
        P.put("Props", "ExhBay", 92.0 + dx, y + 2.0, 96.55, role="bay")
    P.put("Props", "RegentPlinth", 92.0, y + 2.0, 89.3, role="regent")
    P.put("Courts", "ScreenWaves", 72.0, y, 59.0, yaw=FACE["W"], role="screen")
    P.put("Props", "LanternPillar", 84.0, y, 73.5)
    P.put("Props", "LanternPillar", 100.0, y, 73.5, light=True)
    P.put("Props", "Burner", 92.0, y, 66.0)
    # ------------------------------------------------------------------------------------------------ rails on the exposed edges
    def rails(x0, z0, x1, z1, Y, n=None):
        L = math.hypot(x1 - x0, z1 - z0)
        n = n or max(1, int(round(L / 8.0)))
        yaw = 0.0 if abs(z1 - z0) < 1e-6 else FACE["E"]
        for i in range(n):
            t = (i + 0.5) / n
            Lm = L / n
            P.put("Courts", "Rail8", x0 + (x1 - x0) * t, G(Y) + 0.0, z0 + (z1 - z0) * t, yaw=yaw, role="rail", scale_x=Lm / 8.0)
    rails(35.4, 41.5, 35.4, 62.0, Y_GARDEN)
    rails(35.4, 74.0, 35.4, 95.0, Y_GARDEN)
    rails(62.6, -61.4, 103.4, -61.4, Y_TEA)
    rails(103.4, -61.4, 103.4, -24.6, Y_TEA)
    rails(121.4, 52.6, 121.4, 99.0, Y_EXH)
    # ------------------------------------------------------------------------------------------------ markers
    s = P.spots
    s["MasterSpot"] = dict(pos=(0.0, FY(Y_RES) + 1.0, 169.0), yaw=0.0, note="the Faction Master's standing place in her house, facing the door (Master Hwa Rin's home)")
    s["MasterGarden"] = dict(pos=(0.0, FY(Y_RES), 150.0), yaw=PI, note="where the Master receives in the court when the weather is fair")
    s["RegentDisplay"] = dict(pos=(92.0, FY(Y_EXH) + 2.0 + 1.0 + 2.1, 89.3), yaw=0.0,
                              note="the Dawnspire Regent lies along x here (a static clone of ServerStorage.Weapons.SecretOrthodox: its blade along the marker's x axis, the point toward +x, the flat up)")
    s["ExhibitDoor"] = dict(pos=(92.0, FY(Y_EXH) + 2.0, 83.5), yaw=0.0, note="the exhibition hall's doorway")
    s["TeaTable1"] = dict(pos=(99.0, FY(Y_TEA), -44.0), yaw=0.0, note="the tea table's middle")
    npc = [("NpcTea1", 99.0 + 3.0 * math.cos(math.radians(45)), -44.0 + 3.0 * math.sin(math.radians(45))), ("NpcTea2", 99.0 - 3.0 * math.cos(math.radians(45)), -44.0 + 3.0 * math.sin(math.radians(45))),
           ("NpcTea3", 99.0 + 3.0 * math.cos(math.radians(45)), -44.0 - 3.0 * math.sin(math.radians(45))), ("NpcTea4", 99.0 - 3.0 * math.cos(math.radians(45)), -44.0 - 3.0 * math.sin(math.radians(45))),
           ("NpcPavilion1", 86.0, -40.0), ("NpcPavilion2", 90.0, -46.5), ("NpcCorridor1", 74.0, -29.0), ("NpcCorridor2", 82.0, -29.0), ("NpcPond", 78.0, -51.0), ("NpcStairFoot", 94.0, -34.0)]
    for n, x, z in npc:
        s[n] = dict(pos=(x, FY(Y_TEA), z), yaw=math.atan2(-(94.0 - x), -(-44.0 - z)) if False else 0.0, note="an NPC's place on the tea terrace (the gathering area)")
    s["GardenBench"] = dict(pos=(23.0, FY(Y_GARDEN) + 1.0, 87.0), yaw=0.0, note="the garden pavilion's middle")
    s["YardCentre"] = dict(pos=(94.0, FY(Y_YARD), 14.5), yaw=0.0, note="the training yard's middle (a place for trainees)")
    s["StageTop"] = dict(pos=(113.5, FY(Y_YARD) + 3.0, 22.0), yaw=0.0, note="the top of the stage")
    # ------------------------------------------------------------------------------------------------ waterfalls (lip, the point behind it; drop = how far it falls)
    P.falls = [
        dict(zone="TeaPond", lip=(78.0, FY(Y_TEA) + 0.4, -62.6), frm=(78.0, FY(Y_TEA) + 0.4, -59.5), note="the tea pond's overflow, off the terrace's south edge into the void"),
        dict(zone="GardenEdge", lip=(36.7, FY(Y_GARDEN) + 0.4, 90.0), frm=(33.0, FY(Y_GARDEN) + 0.4, 90.0), note="a pool's overflow off the garden's east edge into the ravine"),
        dict(zone="ExhibitEdge", lip=(61.6, FY(Y_EXH) + 0.4, 95.0), frm=(65.0, FY(Y_EXH) + 0.4, 95.0), note="a brook off the exhibition terrace's west edge into the ravine"),
    ]
    # ------------------------------------------------------------------------------------------------ vegetation (the library's own pieces; each at its terrace's level)
    plant(P)
    LIGHT_OFFSET = {"LanternPillar": (0.0, 5.2, 0.0), "LanternLow": (0.0, 2.1, 0.0), "TeaPavilion": (0.0, 5.5, 0.0), "YardGate": (0.0, 7.5, -4.0)}
    for p in P.placements:
        if p.get("light"):
            o = LIGHT_OFFSET[p["name"]]
            warm = p["name"] in ("TeaPavilion", "LanternLow")
            P.lights.append(dict(pos=(p["x"] + o[0], p["y"] + o[1], p["z"] + o[2]), color=(255, 226, 176) if warm else (150, 205, 255), range=24, brightness=0.9,
                                 note="%s (%s)" % (p["name"], p["role"])))
    assert len(P.lights) <= 6, "at most six PointLights in the whole territory"
    return P


def plant(P):
    t = P.tree
    GY, EY, TY_, YY, RY = Y_GARDEN, Y_EXH, Y_TEA, Y_YARD, Y_RES
    # the hall's own tree spots (the first foundation's borrowed Blossom Sanctuary trees are gone): beside the front court
    t("Trees_PlinthTreeA", -36.0, -36.0, 16.0, 0.4)
    t("Trees_PlinthTreeB", 36.0, -36.0, 16.0, 3.4)
    # the rear garden: an arch of blossom over the walk, the tiered tree, the silk-bound elder, two weepers in basins before the cross wall
    t("Trees_ArchTreeA", 0.0, 72.0, GY, 0.0)
    t("Trees_TierTreeA", -22.0, 82.0, GY, 0.5)
    t("Trees_BoundTreeA", 21.0, 63.0, GY, 0.8)
    t("Trees_BasinTreeA", -11.0, 47.0, GY, 0.2)
    t("Plants_LotusBasin", -9.0, 61.0, GY, 0.0, folder="Plants")
    t("Plants_LotusBasin", 9.0, 61.0, GY, 0.0, folder="Plants")
    for (x, z) in ((-15.5, 94.5), (15.5, 94.5)):
        t("Plants_AzaleaHedge6", x, z, GY, 0.0, folder="Plants")
    t("Plants_PeonyBed", -10.0, 77.0, GY, 0.0, folder="Plants")
    t("Plants_GravelRakeRect", 15.0, 49.0, GY, 0.0, folder="Plants")
    t("Plants_GravelRakeRound", -16.0, 49.5, GY, 0.0, folder="Plants")
    for i, (x, z, nm) in enumerate(((5.0, 80.0, "A"), (8.5, 83.0, "B"), (12.5, 85.5, "C"), (16.0, 86.5, "A"))):
        t("Rocks_SteppingStone" + nm, x, z, GY, 0.6 * i, folder="Rocks")
    # the Master's court
    t("Trees_PlinthTreeA", -13.0, 150.0, RY, 0.0)
    t("Rocks_ScholarB", -22.0, 135.0, RY, 0.3, folder="Rocks")
    t("Plants_LotusBasin", 0.0, 149.0, RY, 0.0, folder="Plants")
    t("Plants_AzaleaHedge6", 16.0, 138.0, RY, 0.0, folder="Plants")
    t("Plants_GravelRakeRect", 20.0, 147.0, RY, 0.0, folder="Plants")
    # the tea terrace
    t("Trees_TierTreeA", 98.0, -56.0, TY_, 0.7)
    t("Rocks_ScholarA", 68.0, -57.0, TY_, 1.0, folder="Rocks")
    t("Plants_AzaleaHedge6", 100.0, -34.0, TY_, 0.0, folder="Plants")
    t("Plants_PeonyBed", 76.0, -36.0, TY_, 0.0, folder="Plants")
    t("Plants_PetalDriftB", 92.0, -50.0, TY_, 0.0, folder="Plants")
    # the training yard (austere: one tree, one stone, raked gravel)
    t("Rocks_ScholarE", 122.0, 10.0, YY, 3.1, folder="Rocks")
    t("Plants_DwarfPine", 70.0, 40.0, YY, 0.0, folder="Plants")
    # the exhibition terrace
    t("Trees_ArchTreeB", 94.0, 58.0, EY, 0.0)
    t("Trees_TierTreeB", 110.0, 62.0, EY, 0.4)
    t("Rocks_ScholarB", 118.0, 80.0, EY, 0.2, folder="Rocks")
    t("Plants_WhiteIris", 118.0, 58.0, EY, 0.0, folder="Plants")
    t("Plants_PetalDriftC", 104.0, 58.0, EY, 0.0, folder="Plants")


# ======================================================================================================================
# terrain pavement: the ground under every building, floor and walk is Pavement (bladeless and level), never Grass
# ======================================================================================================================
WALKS = [((0.0, 40.0), (0.0, 96.0), 3.4), ((4.0, 79.0), (17.0, 87.0), 2.0), ((94.0, 52.0), (94.0, 76.0), 3.6), ((62.0, 68.0), (88.0, 68.0), 2.6),
         ((62.0, -51.0), (88.0, -51.0), 2.6), ((88.0, -51.0), (88.0, -44.0), 2.6), ((94.0, -34.0), (94.0, -30.0), 3.6), ((0.0, 129.0), (0.0, 160.0), 3.4), ((24.0, -51.0), (64.5, -51.0), 4.5), ((38.0, 68.0), (62.0, 68.0), 4.5)]
PAVE_ROLES = ("house", "wing", "hall", "gate", "tower", "pavilion", "corridor", "stage", "pond", "floor", "landing", "wall", "stair", "screen", "bridge")


def register_pavement():
    P = build_all()
    rects = []
    for p in P.placements:
        if p["role"] not in PAVE_ROLES or p["piece"].endswith("Causeway"):
            continue
        (lx, _, lz), (hx, _, hz) = P.pieces[p["piece"]].bounds()
        c, s = math.cos(p["yaw"]), math.sin(p["yaw"])
        pts = [(p["x"] + x * c + z * s, p["z"] - x * s + z * c) for x in (lx, hx) for z in (lz, hz)]
        m = 1.2
        rects.append((min(q[0] for q in pts) - m, max(q[0] for q in pts) + m, min(q[1] for q in pts) - m, max(q[1] for q in pts) + m))
    T.PAVED_RECTS[:] = rects
    T.PAVED_STRIPS[:] = [(a, b, w) for (a, b, w) in WALKS]
    return len(rects)


# ======================================================================================================================
# statistics and the plan drawing
# ======================================================================================================================
def stats(P):
    count = {}
    for p in P.placements:
        count[p["piece"]] = count.get(p["piece"], 0) + 1
    rows, total = [], 0
    for name, piece in sorted(P.pieces.items()):
        n = count.get(name, 0)
        t = piece.tris()
        rows.append((name, t, n, t * n, piece.stats()))
        total += t * n
    vm = veg()["pieces"]
    vtotal, vparts = 0, 0
    for v in P.veg:
        vtotal += vm[v["piece"]]["tris"]
        vparts += len(vm[v["piece"]]["materials"])
    return rows, total, vtotal, vparts


def plan_overlay(sx, sz):
    """SVG layers for dawnspire_plan.plan(): the buildings (footprints), pieces' centres, spots, plants, falls."""
    import dawnspire_plan as PL
    P = build_all()
    out = []
    for p in P.placements:
        col = {"house": "#ffd2a0", "wing": "#ffd2a0", "tower": "#c8b6ff", "pavilion": "#ffe08a", "hall": "#ffb3a0", "gate": "#c8b6ff", "corridor": "#ffe08a",
               "stage": "#c8b6ff", "bridge": "#f2e6c8", "stair": "#ff9a5a", "wall": "#ffffff", "floor": None, "rail": "#ddd", "screen": "#9fe8ff"}.get(p["role"])
        if col is None:
            continue
        pcs = P.pieces[p["piece"]]
        (lx, ly, lz), (hx, hy, hz) = pcs.bounds()
        c, s = math.cos(p["yaw"]), math.sin(p["yaw"])
        pts = [(p["x"] + x * c + z * s, p["z"] - x * s + z * c) for x in (lx, hx) for z in (lz, hz)]
        x0, x1 = min(q[0] for q in pts), max(q[0] for q in pts)
        z0, z1 = min(q[1] for q in pts), max(q[1] for q in pts)
        if p["role"] in ("rail", "wall"):
            out.append(PL.line((x0, (z0 + z1) / 2), (x1, (z0 + z1) / 2), col, 3, "", 0.9) if (x1 - x0) > (z1 - z0) else PL.line(((x0 + x1) / 2, z0), ((x0 + x1) / 2, z1), col, 3, "", 0.9))
        else:
            out.append(PL.rect(x0, x1, z0, z1, col, col, 2, "", 0.22))
    for v in P.veg:
        meta = veg()["pieces"][v["piece"]]
        colr = "#ffb5d0" if "Trees" in v["piece"] else ("#a8c8a0" if "Plants" in v["piece"] else "#e8e0d0")
        out.append(PL.circle(v["x"], v["z"], max(0.8, meta["radius"] * 0.55), colr, "#0a0f1e", 1.5, 0.85))
    for n, sp in P.spots.items():
        out.append(PL.circle(sp["pos"][0], sp["pos"][2], 1.0, "#7dffb0" if "Npc" in n else "#ffffff", "#0a0f1e", 1.5, 1.0))
    for f in P.falls:
        out.append(PL.circle(f["lip"][0], f["lip"][2], 1.4, "#7ad7ff", "#0a0f1e", 1.5, 1.0))
    for p in P.placements:
        if p.get("light"):
            out.append(PL.circle(p["x"], p["z"], 1.1, "#ffe66d", "#0a0f1e", 1.5, 1.0))
    return out


if __name__ == "__main__":
    P = build_all()
    rows, total, vt, vp = stats(P)
    for name, t, n, tn, per in rows:
        print("%-34s %6d tris x %2d = %6d   %s" % (name, t, n, tn, per))
    print("buildings, courts and props as placed:", total)
    print("vegetation as placed:", vt, "triangles in", len(P.veg), "pieces (%d material meshes)" % vp)
    print("TOTAL as placed:", total + vt)
    print("colliders", len(P.colliders), "placements", len(P.placements), "lights", len(P.lights))
