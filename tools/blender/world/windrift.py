"""Windrift Hold's territory (2026-11-23): every piece, placement, collision box, marker, waterfall, light and plant of the Unorthodox pad's compound, in the pad's
FRAME (origin at the Unorthodox pad's centre, island-local x 0, z 250, lifted 0.5; +z up the mountain toward the cliff and the falls, +x the player's left; y =
Y over the plaza - 36 for a floor mesh that lies 0.5 over its terrain, - 36.5 for the ground itself). Plain Python: windrift_run.py makes the Blender scenes, renders, QA
and FBX files; windrift_lua.py writes src/worldbuild/Placements/MurimWindrift.lua; windrift_verify.py checks the numbers; murim_windrift_terrain.py is the ground it stands on.

Levels (terrain Y over the plaza -> floor y in this frame): the pad 36 -> 0, the Eyrie 58 -> 22, the Perch 52 -> 16, the Drip ledge 24 -> -12.
"""
import json
import math
import os

import murim_windrift_terrain as T
import windrift_arch as A

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
VEG_JSON = os.path.join(REPO, "assets", "world", "MurimCrossing", "Windrift", "veg_pieces.json")

Y0 = 36.5                      # frame y = Y - Y0 for the ground
PI = math.pi


def G(Y):
    """Frame y of the ground of a terrace at terrain level Y."""
    return Y - 36.5


def Fl(Y):
    """Frame y of a floor mesh on a terrace at level Y (0.5 over its terrain)."""
    return Y - 36.0


# the Roblox look of each architecture material suffix (no texture anywhere): Material enum name, colour, extras
ARCH_LOOKS = {
    "Stone": {"Material": "Slate", "Color": [62, 82, 74]},
    "Tile": {"Material": "Slate", "Color": [28, 84, 68]},
    "Timber": {"Material": "Wood", "Color": [88, 66, 46]},
    "Plank": {"Material": "WoodPlanks", "Color": [128, 102, 72]},
    "Bronze": {"Material": "CorrodedMetal", "Color": [150, 112, 66]},
    "Cloth": {"Material": "Fabric", "Color": [58, 118, 98], "CastShadow": False},
    "Rope": {"Material": "Fabric", "Color": [158, 134, 98], "CastShadow": False},
    "Lamp": {"Material": "Neon", "Color": [255, 196, 112], "CastShadow": False},
    "Bamboo": {"Material": "Wood", "Color": [150, 154, 84]},
    "Water": {"Material": "Glass", "Color": [92, 170, 160], "Transparency": 0.5, "CastShadow": False},
}

# the FBX files: family -> file name
FILES = {"Buildings": "Windrift_Buildings", "Courts": "Windrift_Courts", "Props": "Windrift_Props"}
FAMILY = {}            # piece key -> family (set by Plan.piece)


def key(family, name):
    return "Windrift_%s_%s" % (family, name)


def family_of(k):
    return k.split("_")[1]


def veg_meta():
    return json.load(open(VEG_JSON))


# ======================================================================================================================
# the pieces
# ======================================================================================================================
BUILDERS = {}
for _n, _f in A.BUILDING_BUILDERS.items():
    BUILDERS[("Buildings", _n)] = _f
for _n, _f in A.COURT_BUILDERS.items():
    BUILDERS[("Courts", _n)] = _f
for _n, _f in A.PROP_BUILDERS.items():
    BUILDERS[("Props", _n)] = _f
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
        self.colliders = []          # dicts: name, x0..z1 (pad frame), optional yaw / rotated / cx, cz, sx, sz
        self.falls = []
        self.lights = []
        self.veg = []
        self.walks = []              # (label, [(x, z), ...]) walk-check paths
        self.spots = {}
        self.zones = dict(routes=[], checks=[])

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
            right = abs(round(yaw / (PI / 2)) * (PI / 2) - yaw) < 1e-6
            for (x0, x1, y0, y1, z0, z1, nm) in self.pieces[k].col:
                if right:
                    pts = [(px * c + pz * s, -px * s + pz * c) for px in (x0, x1) for pz in (z0, z1)]
                    self.colliders.append(dict(name=nm, x0=x + min(p[0] for p in pts), x1=x + max(p[0] for p in pts), y0=y + y0, y1=y + y1,
                                               z0=z + min(p[1] for p in pts), z1=z + max(p[1] for p in pts)))
                else:                                           # a box turned by an odd yaw: centre, size and yaw
                    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
                    wx, wz = cx * c + cz * s + x, -cx * s + cz * c + z
                    self.colliders.append(dict(name=nm, x0=wx - (x1 - x0) / 2, x1=wx + (x1 - x0) / 2, y0=y + y0, y1=y + y1, z0=wz - (z1 - z0) / 2, z1=wz + (z1 - z0) / 2,
                                               yaw=yaw, rotated=True, cx=wx, cz=wz, sx=x1 - x0, sz=z1 - z0))
        return d

    def box(self, name, x0, x1, y0, y1, z0, z1):
        self.colliders.append(dict(name=name, x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z1))

    def abox(self, name, cx, cz, sx, sz, y0, y1, yaw):
        """A collider box turned by yaw about its centre (a gap filler on a diagonal stair)."""
        self.colliders.append(dict(name=name, x0=cx - sx / 2, x1=cx + sx / 2, y0=y0, y1=y1, z0=cz - sz / 2, z1=cz + sz / 2, yaw=yaw, rotated=True, cx=cx, cz=cz, sx=sx, sz=sz))

    def vegp(self, name, x, z, y=None, yaw=0.0, scale=1.0, folder="Vegetation"):
        """A tree, rock or plant of the vegetation library at ground y (default: the terrain's own, frame y): its colliders (rotated by yaw) join the colliders."""
        k = "Windrift_%s" % name
        meta = veg()["pieces"][k]
        if y is None:
            h = cell_height(x, z)
            y = (h if h is not None else 36.0) - Y0
        d = dict(piece=k, x=x, y=y, z=z, yaw=yaw, scale=scale, folder=folder)
        self.veg.append(d)
        c, s = math.cos(yaw), math.sin(yaw)
        for b in meta["collision"]:
            cx, cz = (b["x0"] + b["x1"]) / 2 * scale, (b["z0"] + b["z1"]) / 2 * scale
            wx, wz = x + cx * c + cz * s, z - cx * s + cz * c
            sx, sz = (b["x1"] - b["x0"]) * scale, (b["z1"] - b["z0"]) * scale
            self.colliders.append(dict(name=name.split("_")[1], x0=wx - sx / 2, x1=wx + sx / 2, y0=y + b["y0"] * scale, y1=y + b["y1"] * scale, z0=wz - sz / 2, z1=wz + sz / 2,
                                       yaw=yaw, rotated=True, cx=wx, cz=wz, sx=sx, sz=sz))
        return d


def cell_height(x, z):
    """The terrain height (Y over the plaza) of the 4-stud cell under a pad-frame point (the voxel column's top), from the ground function, never from the written grid."""
    import murim_layout as M
    lx, lz = T.to_local(x, z)
    wx, wz = M.to_world(lx, lz)
    ox, oz, n = M.grid()
    ci, cj = int((wx - ox) // M.CELL), int((wz - oz) // M.CELL)
    cx, cz = ox + (ci + 0.5) * M.CELL, oz + (cj + 0.5) * M.CELL
    x_, z_ = M.to_local(cx, cz)
    return M.ground(x_, z_)[0]


def face_yaw(vx, vz):
    """Yaw (CFrame.Angles(0, yaw, 0)) that turns a piece's front (-Z) toward the horizontal direction (vx, vz)."""
    return math.atan2(-vx, -vz)


def run_yaw(a, b):
    """Yaw that turns a piece's +z axis along a -> b (x, z each)."""
    return math.atan2(b[0] - a[0], b[1] - a[1])


def wall_line(P, x0, z0, x1, z1, gate=None, y=G(36.0)):
    """A rough rubble wall from (x0, z0) to (x1, z1) tiled from the 12, 6 and 3 stud pieces, leaving `gate` = (distance from start, width) open."""
    L = math.hypot(x1 - x0, z1 - z0)
    ux, uz = (x1 - x0) / L, (z1 - z0) / L
    yaw = math.atan2(uz, -ux) * 0 + (0.0 if abs(uz) < 1e-6 else PI / 2)
    cur = 0.0
    segs = []
    if gate:
        segs = [(0.0, gate[0]), (gate[0] + gate[1], L)]
    else:
        segs = [(0.0, L)]
    for a, b in segs:
        pos = a
        while b - pos > 0.5:
            rem = b - pos
            for nm, ln in (("WallRough12", 12.0), ("WallRough6", 6.0), ("WallRough3", 3.2), ("WallRough2", 1.8)):
                if rem >= ln - 0.35 or ln == 1.8:
                    break
            cx = x0 + ux * (pos + ln / 2)
            cz = z0 + uz * (pos + ln / 2)
            P.put("Courts", nm, cx, y, cz, yaw=yaw, role="wall")
            pos += ln - 0.2
            if rem <= 2.2:
                break


def build_all(with_veg=True):
    P = Plan()
    Yp = G(T.Y_PAD) if False else -0.5          # the pad's terrain top, frame y
    # ---------------------------------------------------------------------------------------------- the great buildings
    P.put("Buildings", "RainHall", 9.5, 1.5, 52.0, role="hall", light=True)
    P.put("Buildings", "Hq", -20.0, 2.5, 22.0, role="hq", light=True)
    P.put("Buildings", "Gallery", 38.5, 1.5, 20.0, role="hall", light=True)
    P.put("Buildings", "Eyrie", -25.0, Fl(T.Y_EYRIE), 68.0, role="house", light=True)
    P.put("Buildings", "PerchPavilion", 27.5, Fl(T.Y_PERCH), 68.5, role="hall")
    P.put("Buildings", "DripShrine", 7.2, Fl(T.Y_DRIP), 50.2, role="hall")
    # the weapon in the Gallery's lantern room
    P.put("Props", "Cradle", 56.7, 1.5, 20.0, role="prop")
    P.spots["SaberDisplay"] = dict(pos=(56.7, 1.5 + 3.2, 20.0), yaw=0.0, note="the Crosscurrent Saber lies along x on the cradle's saddles (a static clone of ServerStorage.Weapons.SecretUnorthodox: blade along the marker's x axis, the curve and edge as the weapon's own model sits, flat up)")
    for k, x in enumerate((26.0, 30.5)):
        pass
    for k, (x, z) in enumerate(((27.0, 26.2), (33.0, 26.2), (43.5, 26.2))):
        P.put("Props", "WeaponRack", x, 1.5, z, yaw=PI, role="prop")
    # ---------------------------------------------------------------------------------------------- the gathering place (10 NPC spots)
    hx, hz = 38.0, -24.0
    P.put("Buildings", "HearthYard", hx, -0.5, hz, role="shelter", light=True)
    for k in range(10):
        a = TAU_ * k / 10 + 0.15
        x, z = hx + 4.4 * math.cos(a), hz + 4.4 * math.sin(a)
        P.spots["NpcHearth%d" % (k + 1)] = dict(pos=(x, 0.0, z), yaw=face_yaw(hx - x, hz - z), note="an NPC's place round the hearth (the gathering area)")
    P.spots["HearthFire"] = dict(pos=(hx, 0.6, hz), yaw=0.0, note="the fire ring's middle")
    # ---------------------------------------------------------------------------------------------- the training grounds
    P.put("Buildings", "StoneRing", -30.0, -0.5, -20.0, role="court")
    P.put("Buildings", "LogYard", -42.0, -0.5, -2.0, role="court")
    P.put("Buildings", "RopeCourse", -26.0, -0.5, -40.0, role="court")
    P.put("Buildings", "SwingLogs", 14.0, -0.5, -33.0, role="court")
    P.spots["TrainingRing"] = dict(pos=(-30.0, 0.8, -20.0), yaw=0.0, note="the middle of the stone sparring ring")
    P.spots["LogYard"] = dict(pos=(-42.0, 0.0, -10.5), yaw=0.0, note="the log yard's middle")
    P.spots["WireCourse"] = dict(pos=(-26.0, 0.0, -40.0), yaw=0.0, note="the wire course's start")
    # ---------------------------------------------------------------------------------------------- bridges and stairs
    P.put("Courts", "GorgeBridge", 9.25, 0.0, 14.0, role="bridge")
    P.put("Courts", "GreatSpan", 2.5, Fl(T.Y_EYRIE), 66.0, role="bridge")
    P.put("Courts", "CleftStair", 5.0, 0.0, 27.0, role="stair")
    # the Eyrie stair (terrain runs in murim_windrift_terrain.STAIRS): two flights and a landing, the Perch stair one long flight
    ey = T.STAIRS["Eyrie"]["runs"]
    P.put("Courts", "Flight11", ey[0][0][0], G(36.0), ey[0][0][1], yaw=run_yaw(ey[0][0], ey[0][1]), role="stair")
    P.put("Courts", "Landing", ey[1][0][0], G(47.0), ey[1][0][1], yaw=run_yaw(ey[1][0], ey[1][1]), role="stair")
    P.put("Courts", "Flight11", ey[2][0][0], G(47.0), ey[2][0][1], yaw=run_yaw(ey[2][0], ey[2][1]), role="stair")
    # (the landing piece is 5.0 deep, its run 5.3: an invisible fill closes the 0.3 gap to the second flight, which matters now that the ground under the landing is cut 3 studs down)
    ly = run_yaw(ey[1][0], ey[1][1])
    ldx, ldz = math.sin(ly), math.cos(ly)
    P.abox("LandingFill", ey[1][0][0] + ldx * 5.2, ey[1][0][1] + ldz * 5.2, 8.0, 0.8, G(47.0) - 3.0, G(47.0), ly)
    # ---------------------------------------------------------------------------------------------- the Moss Court (walled, hidden gate on its west side)
    wall_line(P, 18.0, -10.0, 30.0, -10.0)
    wall_line(P, 18.0, 3.0, 30.0, 3.0)
    wall_line(P, 30.0, -10.0, 30.0, 3.0)
    wall_line(P, 18.0, -10.0, 18.0, 3.0, gate=(1.6, 9.8))
    P.put("Courts", "MossGate", 18.0, -0.5, -3.5, yaw=PI / 2, role="wall")
    P.spots["MossCourt"] = dict(pos=(24.0, 0.0, -3.5), yaw=PI / 2, note="the Moss Court's middle (a hidden garden: a pond, an old tree)")
    # ---------------------------------------------------------------------------------------------- rails along the gorge, banners and lanterns
    for (x, z, yaw) in ((16.6, 27.5, PI / 2), (16.6, 35.5, PI / 2)):
        P.put("Courts", "RimRail8", x, 0.0, z, yaw=yaw, role="rail")
    P.put("Courts", "RimRail8", 7.2, 0.0, 8.4, role="rail")
    P.put("Courts", "RimRail8", 12.0, 0.0, 8.4, role="rail")
    for x in (-9.0, 9.0):
        P.put("Props", "BannerPole", x, -0.5, -42.0, role="prop")
    for (x, z, lt) in ((-6.0, -30.0, True), (6.0, -30.0, False), (-12.0, -2.0, False), (24.0, 14.0, False)):
        P.put("Props", "LanternPost", x, -0.5, z, yaw=0.0 if x < 0 else PI, role="prop", light=lt)
    for (x, z, yaw) in ((46.0, -40.0, 0.0), (-2.0, 8.0, PI / 2)):
        P.put("Props", "Bench", x, -0.5, z, yaw=yaw, role="prop")
    P.put("Props", "Waymarker", 14.0, -0.5, -44.0, yaw=0.4, role="prop")
    P.put("Props", "Waymarker", 25.0, Fl(T.Y_DRIP) - 0.5, 53.0, yaw=0.0, role="prop") if False else None
    # scaffolds on the tower, the Rain Hall's left end and the Eyrie's loft
    P.put("Props", "ScaffoldA", -35.5, 2.5, 29.0, role="prop", collide=False)
    P.put("Props", "ScaffoldB", -8.0, 1.5, 52.0, role="prop", collide=False)
    # ---------------------------------------------------------------------------------------------- other marks
    P.spots["ElderSpot"] = dict(pos=(-29.0, Fl(T.Y_EYRIE) + 0.5, 71.6), yaw=PI, note="Elder Kang Dal's place in his house (the Eyrie), facing the door")
    P.spots["ElderDeck"] = dict(pos=(-28.0, Fl(T.Y_EYRIE) + 0.5, 65.0), yaw=PI, note="where the Elder receives on his deck in fair weather")
    P.spots["HqDoor"] = dict(pos=(-21.0, 2.5, 8.8), yaw=PI, note="the Long Hold's doorway (the headquarters)")
    P.spots["HqInside"] = dict(pos=(-20.0, 2.5, 22.0), yaw=0.0, note="the middle of the Long Hold's hall")
    P.spots["FallsView"] = dict(pos=(9.5, 1.5 + 1.0, 52.0 + 8.3), yaw=0.0, note="the Rain Hall's gallery: the Great Falls are in front")
    P.spots["BellPerch"] = dict(pos=(27.5, Fl(T.Y_PERCH) + 0.5, 68.5), yaw=0.0, note="the Windbell Perch's middle (the great bell)")
    P.spots["DripLedge"] = dict(pos=(7.2, Fl(T.Y_DRIP) + 0.5, 49.0), yaw=0.0, note="the ledge in the gorge under the Rain Hall (the Drip Shrine)")
    P.spots["GateCourt"] = dict(pos=(0.0, 0.0, -40.0), yaw=0.0, note="the forecourt behind the gate, between the banner poles")
    # ---------------------------------------------------------------------------------------------- waterfalls
    P.falls = [dict(zone="GreatFalls", lip=(9.5, 67.2, 74.0), frm=(9.5, 67.2, 84.0), drop=92.0, scale=1.9, curtains=3, splash=False,
                    note="the Great Falls: off the mesa's rim into the gorge, the Rain Hall 12 studs in front of it")]
    if with_veg:
        plant(P)
    _lights(P)
    return P


TAU_ = 2 * PI


def _lights(P):
    """At most eight PointLights: one per lit place, at the position the piece names for it (its own frame, moved by its placement)."""
    P.lights = []
    for p in P.placements:
        if not p.get("light"):
            continue
        pc = P.pieces[p["piece"]]
        for (lx, ly, lz) in pc.lights[:1]:
            c, s = math.cos(p["yaw"]), math.sin(p["yaw"])
            P.lights.append(dict(pos=(p["x"] + lx * c + lz * s, p["y"] + ly, p["z"] - lx * s + lz * c), color=(255, 196, 120), range=26, brightness=0.8,
                                 note="%s (%s)" % (p["name"], p["role"])))
    assert len(P.lights) <= 8, "at most eight PointLights in the whole territory"


def _hash(i, a, seed):
    return BL_hash(i, a, seed)


def BL_hash(ix, iy, seed):
    import blossom_layout as BL
    return BL._hash(ix, iy, seed)


def _near_stairs(x, z, m):
    for name in T.STAIRS:
        for run in T.stair_runs(name):
            s, u = T.run_state(x, z, run)
            if -m <= s <= run["L"] + m and abs(u) <= run["half"] + m:
                return True
    return False


def _free(P, x, z, r, lane=True, pad_only=False):
    """True if a piece with keep-out r may stand at (x, z): not in the gorge, not on a stair, not in a collider (grown by r), not on a walk, and on ground."""
    s_ = T.SLOT
    if s_["x0"] - r - 1.5 <= x <= s_["x1"] + r + 1.5 and s_["z0"] - r - 1.5 <= z <= s_["z1"] + r + 1.5:
        return False
    lx, lz = T.to_local(x, z)
    if T.protected(lx, lz):
        return False
    if _near_stairs(x, z, 3.0 + r):
        return False
    for c in P.colliders:
        if c["x0"] - r <= x <= c["x1"] + r and c["z0"] - r <= z <= c["z1"] + r and c["y1"] - c["y0"] > 0.2:
            if c.get("name") in ("Deck", "Guard", "HallFloor", "Gallery", "Podium", "Abutment", "Landing", "Step", "Flank"):
                if c["x0"] - 0.5 <= x <= c["x1"] + 0.5 and c["z0"] - 0.5 <= z <= c["z1"] + 0.5:
                    return False
                continue
            return False
    if lane:
        for (a, b, w) in WALKS:
            if T._seg_dist(x, z, a, b) <= w + r * 0.5:
                return False
    h = cell_height(x, z)
    return h is not None


def _scatter(P, name, count, sampler, r, seed, yaw_jitter=0.3, lane=True, tries=400, scale=(1.0, 1.0)):
    placed = 0
    for t in range(tries):
        if placed >= count:
            break
        x, z = sampler(t, seed)
        if not _free(P, x, z, r, lane):
            continue
        yaw = (BL_hash(t, 11, seed + 3) - 0.5) * 2 * yaw_jitter
        sc = scale[0] + (scale[1] - scale[0]) * BL_hash(t, 13, seed + 5)
        folder = "Rocks" if name.startswith("Rocks") else "Vegetation"
        if name.startswith("Rocks_Steps") or name.startswith("Rocks_Cobble") or name.startswith("Rocks_PlankWalk"):
            folder = "Paths"
        P.vegp(name, x, z, yaw=yaw, scale=sc, folder=folder)
        placed += 1
    return placed


def _ring(r0, r1, a0=0.0, a1=TAU_):
    def f(t, seed):
        a = a0 + (a1 - a0) * BL_hash(t, 3, seed)
        r = r0 + (r1 - r0) * BL_hash(t, 5, seed + 1)
        return r * math.cos(a), r * math.sin(a)
    return f


def _box_sampler(x0, x1, z0, z1):
    def f(t, seed):
        return x0 + (x1 - x0) * BL_hash(t, 3, seed), z0 + (z1 - z0) * BL_hash(t, 5, seed + 1)
    return f


def plant(P):
    """The vegetation library's pieces (the counts are the library's own plan: 15 trees, 24 rocks and paths, 60 plants), each at its ground, all leaning with the wind (yaw about 0)."""
    t = P.vegp
    PI_ = PI
    # ---- the giant on the plateau's rim above the Eyrie, its crown streaming over the falls; a few tall pines and cedars on the rim and the shoulders
    t("Trees_GiantCedar", -34.0, 79.0, yaw=0.0)
    t("Trees_BannerPineB1", 44.0, 84.0, yaw=0.0)
    t("Trees_BannerPineB1", -58.0, 84.0, yaw=0.1)
    t("Trees_BannerPineB2", 58.0, 66.0, yaw=0.0)
    t("Trees_GaleCedarA1", 57.5, 3.0, yaw=0.1)           # the pad's rim, right and left of the gate
    t("Trees_GaleCedarA1", -55.0, -18.0, yaw=0.0)
    t("Trees_GaleCedarA2", -31.0, 74.0, yaw=0.0)          # the Eyrie ledge's far end
    t("Trees_SplitSnagE1", 60.0, -34.0, yaw=0.2)
    t("Trees_SplitSnagE1", -52.0, 36.0, yaw=-0.1)
    t("Trees_SplitSnagE2", 49.0, 44.0, yaw=0.0)
    # inside the Moss Court
    t("Trees_CliffJuniperC1", 22.0, 0.5, yaw=0.0, scale=1.0)
    t("Trees_BronzeleafD1", 25.5, -7.5, yaw=0.0)
    t("Trees_CliffJuniperC2", 28.0, -7.0, yaw=0.1)
    t("Trees_CliffJuniperC2", 52.0, -8.0, yaw=0.0)         # the hearth yard's edge
    t("Trees_BronzeleafD2", 49.0, -38.0, yaw=0.0)
    # ---- rocks and paths
    for (n, x, z, yw) in (("CragTail", -52.0, 6.0, 0.0), ("CragTail", 55.5, 4.0, 0.1), ("CragTail", 14.0, 66.0, 0.0), ("SlateSlab", -12.0, 40.0, 0.0), ("SlateSlab", 34.0, 42.0, 0.0),
                          ("StrataStack", -49.0, -34.0, 0.0), ("StrataStack", 50.0, -50.0, 0.0), ("VeinBoulderA", -50.0, 16.0, 0.3), ("VeinBoulderA", 45.0, 38.0, 0.0),
                          ("VeinBoulderB", 56.0, -16.0, 0.0), ("VeinBoulderB", -12.0, 52.0, 0.0), ("Fin", -45.0, 44.0, 0.0), ("Fin", 28.0, 46.0, 0.0),
                          ("ScreeA", -54.0, -2.0, 0.0), ("ScreeA", 58.0, 12.0, 0.0), ("ScreeB", -44.0, -46.0, 0.0), ("ScreeB", 36.0, -46.0, 0.0)):
        t("Rocks_" + n, x, z, yaw=yw, folder="Rocks")
    t("Rocks_Windgate", 52.0, -32.0, yaw=0.0, folder="Rocks")
    t("Rocks_StepsA", 0.0, -46.0, yaw=0.0, folder="Paths")
    t("Rocks_StepsA", -22.0, 13.0 - 6.0 - 4.0 - 0.0, yaw=0.0, folder="Paths") if False else None
    t("Rocks_StepsB", -22.0, -6.0, yaw=0.3, folder="Paths")
    t("Rocks_StepsB", 24.0, -14.5, yaw=0.0, folder="Paths") if False else None
    t("Rocks_StepsA", 9.5, 32.0, yaw=0.0, folder="Paths")
    t("Rocks_Cobble", 9.5, 40.4, yaw=0.0, folder="Paths")
    t("Rocks_PlankWalk", 30.0, 9.0, yaw=PI_ / 2, folder="Paths") if False else None
    t("Rocks_PlankWalk", 22.0, -3.5, yaw=PI_ / 2, folder="Paths")
    t("Rocks_StepsB", 37.0, 6.4 - 12.0, yaw=0.0, folder="Paths") if False else None
    # ---- plants: ring of grass round the pad's rim, tufts in the courts and along the rocks, flowers in the cracks of the walls
    P.vegp_set = True
    for name, n, sampler, r, seed in (
            ("Plants_GaleGrassA", 10, _ring(48.0, 58.5), 0.5, 101), ("Plants_GaleGrassB", 4, _ring(44.0, 57.0), 0.5, 103), ("Plants_Sedge", 4, _box_sampler(21.0, 29.0, -8.0, 1.5), 0.6, 107),
            ("Plants_Gorse", 3, _ring(40.0, 57.0), 1.2, 109), ("Plants_Heather", 5, _ring(38.0, 58.0), 0.6, 113), ("Plants_JuniperCreeper", 3, _ring(46.0, 58.0), 1.5, 127),
            ("Plants_Cushion", 8, _box_sampler(19.5, 29.0, -9.0, 2.0), 0.8, 131), ("Plants_Stonecrop", 8, _ring(30.0, 56.0), 0.5, 137), ("Plants_Thistle", 5, _ring(42.0, 58.0), 0.6, 139),
            ("Plants_WindStar", 5, _box_sampler(-52.0, -14.0, -48.0, -2.0), 0.6, 149), ("Plants_LichenA", 3, _ring(30.0, 56.0), 0.5, 151), ("Plants_LichenB", 2, _ring(30.0, 56.0), 0.5, 157)):
        _scatter(P, name, n, sampler, r, seed, yaw_jitter=0.25, lane=(name not in ("Plants_Sedge",)))


# ======================================================================================================================
# terrain pavement: the ground under every building, floor and walk is Sandstone or Ground, never Grass
# ======================================================================================================================
WALKS = [((0.0, -50.0), (0.0, -20.0), 4.2), ((0.0, -20.0), (-21.0, 4.0), 3.6), ((0.0, -20.0), (30.0, -22.0), 3.4), ((0.0, -20.0), (-26.0, -20.0), 3.2),
         ((0.0, -20.0), (0.5, 10.0), 3.4), ((-21.0, -4.0), (-42.0, -2.0), 3.0)]
PAVE_ROLES = ("hall", "hq", "house", "bridge", "stair", "court", "shelter", "wall")


def register_pavement():
    P = build_all(False)
    rects = []
    for p in P.placements:
        if p["role"] not in PAVE_ROLES or p["name"] in ("RimRail8",):
            continue
        pc = P.pieces[p["piece"]]
        for (x0, x1, z0, z1, y) in pc.floor:
            c, s = math.cos(p["yaw"]), math.sin(p["yaw"])
            pts = [(p["x"] + x * c + z * s, p["z"] - x * s + z * c) for x in (x0, x1) for z in (z0, z1)]
            m = 1.2
            rects.append((min(q[0] for q in pts) - m, max(q[0] for q in pts) + m, min(q[1] for q in pts) - m, max(q[1] for q in pts) + m))
    T.PAVED_RECTS[:] = rects
    T.PAVED_STRIPS[:] = [(a, b, w) for (a, b, w) in WALKS]
    T.COURTS[:] = [(18.0, 30.0, -10.0, 3.0), (-52.0, -14.0, -30.0, 2.0)]
    return len(rects)


LOOK_VIEWS = {
    "aerial_south": ((0, 120, -130), (0, 25, 30), 36),
    "aerial_back": ((0, 110, 170), (0, 20, 20), 36),
    "from_stair": ((0, 14, -96), (0, 14, 20), 32),
    "pad_wide": ((-70, 70, -50), (0, 5, 20), 40),
    "falls": ((9.5, 22, 20), (9.5, 30, 60), 34),
    "hall_gorge": ((60, 14, 30), (9.5, 4, 56), 34),
    "hq_front": ((-22, 12, -26), (-22, 10, 22), 34),
    "hearth": ((38, 14, -50), (38, 4, -24), 32),
    "training": ((-30, 14, -58), (-30, 3, -18), 34),
    "gallery": ((38, 10, -12), (40, 6, 22), 34),
    "eyrie": ((-28, 30, 20), (-28, 24, 68), 34),
    "span": ((4, 28, 30), (6, 20, 66), 34),
}


def plan_overlay(sx, sz):
    import windrift_plan as PL
    P = build_all()
    out = []
    cols = {"hq": "#ffb08a", "hall": "#ffd08a", "house": "#ffb08a", "bridge": "#f2e6c8", "stair": "#ff9a5a", "court": "#9fe8ff", "shelter": "#ffe08a", "wall": "#e8e8e8"}
    for p in P.placements:
        col = cols.get(p["role"])
        if col is None:
            continue
        pc = P.pieces[p["piece"]]
        for (x0, x1, z0, z1, y) in pc.floor:
            c, s = math.cos(p["yaw"]), math.sin(p["yaw"])
            pts = [(p["x"] + x * c + z * s, p["z"] - x * s + z * c) for x in (x0, x1) for z in (z0, z1)]
            out.append(PL.rect(min(q[0] for q in pts), max(q[0] for q in pts), min(q[1] for q in pts), max(q[1] for q in pts), col, col, 2, "", 0.25))
    for n, sp in P.spots.items():
        out.append(PL.circle(sp["pos"][0], sp["pos"][2], 0.9, "#7dffb0" if n.startswith("Npc") else "#ffffff", "#0a0f1e", 1.5, 1.0))
    for f in P.falls:
        out.append(PL.circle(f["lip"][0], f["lip"][2], 1.6, "#7ad7ff", "#0a0f1e", 1.5, 1.0))
    for l in P.lights:
        out.append(PL.circle(l["pos"][0], l["pos"][2], 1.1, "#ffe66d", "#0a0f1e", 1.5, 1.0))
    for v in P.veg:
        meta = veg()["pieces"][v["piece"]]
        colr = "#7fc17f" if "Trees" in v["piece"] else ("#c8d89a" if "Plants" in v["piece"] else "#9a9ca0")
        out.append(PL.circle(v["x"], v["z"], max(0.8, meta["radius"] * 0.55), colr, "#0a0f1e", 1.2, 0.85))
    return out


def stats(P):
    count = {}
    for p in P.placements:
        count[p["piece"]] = count.get(p["piece"], 0) + 1
    rows, total, parts = [], 0, 0
    for name, piece in sorted(P.pieces.items()):
        n = count.get(name, 0)
        t = piece.tris()
        rows.append((name, t, n, t * n, piece.stats()))
        total += t * n
        parts += len(piece.g) * n
    vm = veg()["pieces"]
    vtotal, vparts = 0, 0
    for v in P.veg:
        vtotal += vm[v["piece"]]["tris"]
        vparts += len(vm[v["piece"]]["materials"])
    return rows, total, parts, vtotal, vparts


if __name__ == "__main__":
    P = build_all()
    rows, total, parts, vt, vp = stats(P)
    for name, t, n, tn, per in rows:
        print("%-34s %6d tris x %2d = %6d   %s" % (name, t, n, tn, per))
    print("architecture, courts and props as placed:", total, "triangles,", parts, "MeshParts")
    print("vegetation as placed:", vt, "triangles in", len(P.veg), "pieces (%d MeshParts)" % vp)
    print("TOTAL as placed:", total + vt, "triangles,", parts + vp, "MeshParts")
    print("colliders", len(P.colliders), "placements", len(P.placements), "lights", len(P.lights), "spots", len(P.spots))
