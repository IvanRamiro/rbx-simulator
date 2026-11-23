"""Nightfall Citadel's territory (2026-11-23): every piece, placement, collision box, marker, light, effect and plant of the Demonic pad's compound, in the pad's FRAME (origin at
the Demonic pad's centre, island-local x -126.83, z 162.33, lifted 0.5; turned by the pad's FrontYaw -0.6632; +z up the mountain away from the plaza, +x across the stairway toward the
island's middle; y = Y over the plaza - 16.5 for the ground itself, - 16 for a floor mesh that lies 0.5 over its terrain). Plain Python: nightfall_run.py makes the Blender scenes,
renders, QA and FBX files; nightfall_lua.py writes the Placements Lua; nightfall_verify.py checks the numbers; murim_nightfall_terrain.py is the ground it stands on.

Levels (terrain Y over the plaza -> ground y in this frame): the pad (the lower ward) 16 -> -0.5, the Upper Ward 40 -> 23.5, the bridgehead and the Residence ledge 48 -> 31.5.
"""
import json
import math
import os

import murim_nightfall_terrain as T
import nightfall_arch as A

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
VEG_JSON = os.path.join(REPO, "assets", "world", "MurimCrossing", "Nightfall", "veg_pieces.json")

Y0 = 16.5                      # frame y = Y - Y0 for the ground
PI = math.pi
TAU = 2 * PI


def G(Y):
    """Frame y of the ground of a terrace at terrain level Y."""
    return Y - Y0


def Fl(Y):
    """Frame y of a floor mesh on a terrace at level Y (0.5 over its terrain)."""
    return Y - 16.0


# the Roblox look of each architecture material suffix (no texture anywhere): Material enum name, colour, extras
ARCH_LOOKS = {
    "Stone": {"Material": "Basalt", "Color": [38, 36, 46]},
    "Tile": {"Material": "Slate", "Color": [26, 24, 32]},
    "Iron": {"Material": "Metal", "Color": [78, 76, 92]},
    "Crimson": {"Material": "Fabric", "Color": [158, 24, 36], "CastShadow": False},
    "Ember": {"Material": "Neon", "Color": [255, 90, 42], "CastShadow": False},
    "Timber": {"Material": "Wood", "Color": [52, 40, 36]},
}

FILES = {"Buildings": "Nightfall_Buildings", "Courts": "Nightfall_Courts", "Props": "Nightfall_Props"}


def key(family, name):
    return "Nightfall_%s_%s" % (family, name)


def family_of(k):
    return k.split("_")[1]


BUILDERS = {}


def _register():
    for n, f in getattr(A, "BUILDING_BUILDERS", {}).items():
        BUILDERS[("Buildings", n)] = f
    for n, f in getattr(A, "COURT_BUILDERS", {}).items():
        BUILDERS[("Courts", n)] = f
    for n, f in getattr(A, "PROP_BUILDERS", {}).items():
        BUILDERS[("Props", n)] = f


_register()
_VEG = None


def veg():
    global _VEG
    if _VEG is None:
        _VEG = json.load(open(VEG_JSON)) if os.path.exists(VEG_JSON) else {"pieces": {}, "looks": {}, "frame": ""}
    return _VEG


class Plan:
    def __init__(self):
        self.pieces = {}
        self.placements = []
        self.colliders = []          # dicts: name, x0..z1 (pad frame), optional yaw / rotated / cx, cz, sx, sz
        self.lights = []
        self.effects = []            # dicts: kind, pos
        self.veg = []
        self.spots = {}

    def piece(self, family, name):
        k = key(family, name)
        if k not in self.pieces:
            p = BUILDERS[(family, name)]()
            p.finish()
            self.pieces[k] = p
        return k

    def put(self, family, name, x, y, z, yaw=0.0, role="decor", light=False, fx=False, collide=True, **extra):
        k = self.piece(family, name)
        d = dict(piece=k, family=family, name=name, x=x, y=y, z=z, yaw=yaw, scale=1.0, role=role)
        if light:
            d["light"] = True
        if fx:
            d["fx"] = True
        d.update(extra)
        self.placements.append(d)
        pc = self.pieces[k]
        c, s = math.cos(yaw), math.sin(yaw)
        if collide:
            right = abs(round(yaw / (PI / 2)) * (PI / 2) - yaw) < 1e-6
            for (x0, x1, y0, y1, z0, z1, nm) in pc.col:
                if right:
                    pts = [(px * c + pz * s, -px * s + pz * c) for px in (x0, x1) for pz in (z0, z1)]
                    self.colliders.append(dict(name=nm, x0=x + min(p[0] for p in pts), x1=x + max(p[0] for p in pts), y0=y + y0, y1=y + y1,
                                               z0=z + min(p[1] for p in pts), z1=z + max(p[1] for p in pts)))
                else:                                           # a box turned by an odd yaw: centre, size and yaw
                    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
                    wx, wz = cx * c + cz * s + x, -cx * s + cz * c + z
                    self.colliders.append(dict(name=nm, x0=wx - (x1 - x0) / 2, x1=wx + (x1 - x0) / 2, y0=y + y0, y1=y + y1, z0=wz - (z1 - z0) / 2, z1=wz + (z1 - z0) / 2,
                                               yaw=yaw, rotated=True, cx=wx, cz=wz, sx=x1 - x0, sz=z1 - z0))
            for (cx, cz, sx, sz, y0, y1, ry, nm) in getattr(pc, "rcol", []):
                wx, wz = cx * c + cz * s + x, -cx * s + cz * c + z
                self.colliders.append(dict(name=nm, x0=wx - sx / 2, x1=wx + sx / 2, y0=y + y0, y1=y + y1, z0=wz - sz / 2, z1=wz + sz / 2, yaw=ry + yaw, rotated=True, cx=wx, cz=wz, sx=sx, sz=sz))
        if light:
            for (lx, ly, lz) in pc.lights[:1]:
                self.lights.append(dict(pos=(x + lx * c + lz * s, y + ly, z - lx * s + lz * c), note="%s (%s)" % (name, role)))
        if fx:
            for (kind, (ex, ey, ez)) in pc.emit:
                self.effects.append(dict(kind=kind, pos=(x + ex * c + ez * s, y + ey, z - ex * s + ez * c), note=name))
        return d

    def box(self, name, x0, x1, y0, y1, z0, z1):
        self.colliders.append(dict(name=name, x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z1))

    def abox(self, name, cx, cz, sx, sz, y0, y1, yaw):
        """A collider box turned by yaw about its centre."""
        self.colliders.append(dict(name=name, x0=cx - sx / 2, x1=cx + sx / 2, y0=y0, y1=y1, z0=cz - sz / 2, z1=cz + sz / 2, yaw=yaw, rotated=True, cx=cx, cz=cz, sx=sx, sz=sz))

    def vegp(self, name, x, z, y=None, yaw=0.0, scale=1.0, folder="Vegetation"):
        """A tree, rock or plant of the vegetation library at ground y (default: the terrain's own, frame y): its colliders (rotated by yaw) join the colliders."""
        k = "Nightfall_%s" % name
        meta = veg()["pieces"][k]
        if y is None:
            h = cell_height(x, z)
            y = (h if h is not None else 16.0) - Y0
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


GR = G(T.Y_PAD)                 # the pad's terrain: -0.5
GU = G(T.Y_UPPER)               # the Upper Ward's terrain: 23.5
GB = G(T.Y_BRIDGEHEAD)          # the bridgehead's and the Residence ledge's: 31.5

# the places everything is anchored to (pad frame)
GATE_Z = -34.0                  # the curtain wall's line
ARENA = (0.0, -8.0)
RING = (-34.0, -12.0)
COURT = (38.0, -8.0)            # the Ember Court
KEEP = (-9.0, 106.0)
ARMORY = (-37.0, 82.0)
BRIDGE = (33.0, 101.0)
RES = (54.5, 101.0)
STAIR_X = 0.0
POSTERN_X = -40.0
BH_X = 18.0                     # the bridgehead stair
ARENA_R_IN = 12.0

NPC_R = 6.2


ARMORY_PLINTH = (8.4, 0.0, 0.4)      # the Talon's plinth in the armory's own frame (the right end of the hall)


def local_to_world(pl, m):
    c, s = math.cos(pl["yaw"]), math.sin(pl["yaw"])
    return (pl["x"] + m[0] * c + m[2] * s, pl["y"] + m[1], pl["z"] - m[0] * s + m[2] * c)


def arm_mark(pl, key):
    return A.armory_marks()[key]


def build_all(with_veg=True):
    P = Plan()
    # ---------------------------------------------------------------------------------------------- the lower ward: the curtain wall, the gatehouse, the bastions
    P.put("Buildings", "Gatehouse", 0.0, GR, GATE_Z, role="gate", light=True)
    for sx in (-1, 1):
        for x, nm in ((18.0, "Curtain12"), (30.0, "Curtain12"), (39.0, "Curtain6")):
            P.put("Courts", nm, sx * x, GR, GATE_Z, role="wall")
        P.put("Buildings", "Bastion", sx * 45.0, GR, GATE_Z, role="tower", fx=True)
    for sx in (-1, 1):
        P.put("Props", "BrazierTall", sx * 6.6, GR, GATE_Z - 5.4, role="prop", fx=True)
        P.put("Props", "BannerPole", sx * 17.0, GR, GATE_Z - 8.0, role="prop")
    # ---------------------------------------------------------------------------------------------- the arena (the Trial of Strength): a round pit, three gates, eight dummy places
    P.put("Buildings", "Arena", ARENA[0], GR, ARENA[1], role="arena")
    for k in range(8):
        a = TAU * k / 8 + TAU / 16
        P.spots["ArenaDummy%d" % (k + 1)] = dict(pos=(ARENA[0] + 8.0 * math.cos(a), 0.0, ARENA[1] + 8.0 * math.sin(a)), yaw=face_yaw(-math.cos(a), -math.sin(a)), note="a place the arena sends a dummy to (the Trial of Strength)")
    P.spots["ArenaCentre"] = dict(pos=(ARENA[0], 0.0, ARENA[1]), yaw=0.0, note="the middle of the arena's pit (the fighter's place)")
    # ---------------------------------------------------------------------------------------------- the training grounds
    P.put("Buildings", "ChainRing", RING[0], GR, RING[1], role="court")
    P.put("Props", "StakeRow", -30.0, GR, RING[1] + 14.0, role="prop")
    P.put("Buildings", "RackShed", -29.0, GR, RING[1] + 22.0, role="shelter")
    P.spots["TrainingRing"] = dict(pos=(RING[0], 0.0, RING[1]), yaw=0.0, note="the middle of the chain ring (the training grounds)")
    P.spots["StakeRow"] = dict(pos=(-30.0, 0.0, RING[1] + 11.0), yaw=PI, note="in front of the training stakes")
    # ---------------------------------------------------------------------------------------------- the gathering place (10 NPC spots)
    P.put("Buildings", "EmberCourt", COURT[0], GR, COURT[1], role="court", light=True, fx=True)
    for k in range(10):
        a = TAU * k / 10 + 0.31
        x, z = COURT[0] + NPC_R * math.cos(a), COURT[1] + NPC_R * math.sin(a)
        P.spots["Npc%d" % (k + 1)] = dict(pos=(x, 0.0, z), yaw=face_yaw(COURT[0] - x, COURT[1] - z), note="an NPC's place round the Ember Court's fire (the gathering area)")
    P.spots["EmberFire"] = dict(pos=(COURT[0], 1.0, COURT[1]), yaw=0.0, note="the fire bowl's middle")
    for k in range(4):
        a = TAU * k / 4 + PI / 4
        P.put("Props", "BannerPole", COURT[0] + 12.6 * math.cos(a), GR, COURT[1] + 12.6 * math.sin(a), role="prop")
    # ---------------------------------------------------------------------------------------------- the Great Stair: two flights, a landing, the gate at its head (a solid ramp on the pad)
    P.put("Courts", "GreatFlight", STAIR_X, GR, 11.0, role="stair")
    P.put("Courts", "GreatLanding", STAIR_X, G(28.0), 29.0, role="stair")
    P.put("Courts", "GreatFlightHigh", STAIR_X, G(28.0), 35.0, role="stair")
    P.put("Buildings", "UpperGate", STAIR_X, GU, 53.0, role="gate", light=True)
    for sx in (-1, 1):
        P.put("Props", "BrazierTall", sx * 5.4, G(28.0), 32.0, role="prop", fx=True, light=(sx == 1))
        P.put("Props", "BannerPole", sx * 16.8, GU, 61.0, role="prop")
    # ---------------------------------------------------------------------------------------------- the Postern: the narrow stair on the left, from the training grounds to the Upper Ward
    P.put("Courts", "PosternFlight", POSTERN_X, GR, 13.0, role="stair")
    P.put("Courts", "PosternLanding", POSTERN_X, G(28.0), 31.0, role="stair")
    P.put("Courts", "PosternFlightHigh", POSTERN_X, G(28.0), 35.0, role="stair")
    P.put("Courts", "PosternLanding", POSTERN_X, GU, 53.0, role="stair")
    # ---------------------------------------------------------------------------------------------- the Upper Ward: the keep, the armory, the court, the rim
    P.put("Buildings", "Keep", KEEP[0], Fl(T.Y_UPPER), KEEP[1], role="hq", light=True, fx=True)
    P.put("Buildings", "Armory", ARMORY[0], Fl(T.Y_UPPER), ARMORY[1], yaw=-PI / 2, role="hall", light=True)
    for x in (-15.5, -2.5):
        P.put("Props", "BrazierTall", x, GU, KEEP[1] - 17.2, role="prop")
    for z in (ARMORY[1] - 11.0, ARMORY[1] + 11.0):
        P.put("Props", "BrazierTall", ARMORY[0] + 10.6, GU, z, role="prop")
    for x in (-30.0, -18.0):
        P.put("Courts", "Parapet12", x, GU, 57.2, role="rail")
    P.put("Courts", "Parapet12", 17.5, GU, 57.2, role="rail")
    for z in (66.0, 78.0):
        P.put("Courts", "Parapet12", 22.8, GU, z, yaw=PI / 2, role="rail")
    P.put("Courts", "Parapet12", 22.8, GU, 119.0, yaw=PI / 2, role="rail")
    # the bridgehead: six steps up from the court, the shelf, the chain bridge over the fissure to the Residence ledge
    P.put("Courts", "BridgeFlight", BH_X, GU, 75.0, role="stair")
    P.put("Courts", "BridgeTop", BH_X, GB, 87.0, role="stair")
    P.put("Courts", "ChainBridge", BRIDGE[0], Fl(T.Y_BRIDGEHEAD), BRIDGE[1], role="bridge", light=True, fx=True)
    for z in (BRIDGE[1] - 8.8, BRIDGE[1] + 8.8):
        P.put("Courts", "Parapet6", 22.8, GB, z, yaw=PI / 2, role="rail")
    # ---------------------------------------------------------------------------------------------- the Residence on its ledge
    P.put("Buildings", "Residence", RES[0], Fl(T.Y_RESIDENCE), RES[1], yaw=PI / 2, role="house", light=True)
    for z in (RES[1] - 8.0, RES[1] + 8.0):
        P.put("Props", "BrazierTall", 46.4, GB, z, role="prop")
    # ---------------------------------------------------------------------------------------------- the marks
    arm = [p for p in P.placements if p["name"] == "Armory"][0]
    for nm, key, note in (("Vault", "Vault", "in front of the faction vault's door in the armory (the vault itself is not built yet: just the place)"),
                          ("ArmoryInside", "Inside", "the middle of the armory's hall")):
        P.spots[nm] = dict(pos=local_to_world(arm, arm_mark(arm, key)), yaw=PI if nm == "Vault" else 0.0, note=note)
    plx, ply, plz = ARMORY_PLINTH
    tx, ty, tz = local_to_world(arm, (plx, 0.0, plz))
    P.put("Props", "TalonPlinth", tx, ty, tz, yaw=arm["yaw"], role="prop")
    P.spots["TalonDisplay"] = dict(pos=local_to_world(arm, (plx, 1.75, plz)), yaw=arm["yaw"], note="where the Nightfall Talon lies (a static clone of ServerStorage.Weapons.SecretDemonic: blade along the marker's x axis, flat up), on the plinth in the armory")
    P.spots["GateCourt"] = dict(pos=(0.0, 0.0, -40.0), yaw=0.0, note="the forecourt behind the island's gate, between the banner poles and the gatehouse")
    P.spots["GatePassage"] = dict(pos=(0.0, 0.0, GATE_Z), yaw=0.0, note="the middle of the gatehouse's passage")
    P.spots["HqDoor"] = dict(pos=(KEEP[0], Fl(T.Y_UPPER), KEEP[1] - 15.4), yaw=PI, note="in front of the keep's door (the headquarters)")
    P.spots["HqInside"] = dict(pos=(KEEP[0], Fl(T.Y_UPPER), KEEP[1] - 1.5), yaw=0.0, note="the middle of the keep's hall")
    P.spots["LordSpot"] = dict(pos=(RES[0] + 1.5, Fl(T.Y_RESIDENCE), RES[1]), yaw=-PI / 2, note="Lord Mu Yeong's place in his tower (the residence), facing the door")
    P.spots["GreatStairFoot"] = dict(pos=(STAIR_X, 0.0, 9.0), yaw=0.0, note="the foot of the Great Stair")
    P.spots["UpperGate"] = dict(pos=(STAIR_X, Fl(T.Y_UPPER), 59.5), yaw=0.0, note="the head of the Great Stair, past the gate")
    P.spots["UpperCourt"] = dict(pos=(-4.0, Fl(T.Y_UPPER), 72.0), yaw=0.0, note="the Upper Ward's court, between the stair, the keep and the armory")
    P.spots["PosternFoot"] = dict(pos=(POSTERN_X, 0.0, 10.5), yaw=0.0, note="the foot of the Postern, the narrow stair at the training grounds' back")
    P.spots["PosternTop"] = dict(pos=(POSTERN_X, Fl(T.Y_UPPER), 58.0), yaw=0.0, note="the head of the Postern, on the Upper Ward's left")
    P.spots["BridgeHead"] = dict(pos=(BH_X, Fl(T.Y_BRIDGEHEAD), 96.0), yaw=PI / 2, note="the bridgehead, where the chain bridge starts")
    P.spots["BridgeEnd"] = dict(pos=(45.6, Fl(T.Y_RESIDENCE), BRIDGE[1]), yaw=-PI / 2, note="the chain bridge's far end on the Residence ledge")
    P.spots["FissureView"] = dict(pos=(BRIDGE[0], Fl(T.Y_BRIDGEHEAD) + 0.5, BRIDGE[1]), yaw=0.0, note="the middle of the chain bridge: the fissure glows beneath")
    P.spots["ArmoryDoor"] = dict(pos=(ARMORY[0] + 10.5, Fl(T.Y_UPPER), ARMORY[1]), yaw=-PI / 2, note="in front of the armory's door (the weapon exhibition hall)")
    if with_veg:
        plant(P)
    _lights(P)
    return P


def _lights(P):
    """At most eight PointLights: one per lit place, at the position the piece names for it (its own frame, moved by its placement); colour by place."""
    assert len(P.lights) <= 8, "at most eight PointLights in the whole territory (%d)" % len(P.lights)
    for l in P.lights:
        inside = l["note"].startswith(("Keep", "Armory", "Residence"))
        l.setdefault("color", (255, 138, 78) if inside else (255, 70, 52))
        l.setdefault("range", 26 if inside else 32)
        l.setdefault("brightness", 0.85 if inside else 0.9)
    P.effects.append(dict(kind="Ash", pos=(0.0, 14.0, 0.0), note="drifting ash over the lower ward"))
    for e in P.effects:
        e["rate"] = {"Flame": 6, "Embers": 4, "Ash": 3}[e["kind"]]
    assert len(P.effects) <= 12


def _hash(i, a, seed):
    import blossom_layout as BL
    return BL._hash(i, a, seed)


# the walking lanes (pad frame): strips (a, b, half width) no tree, rock or shrub may stand in
LANES = [((0.0, -52.0), (0.0, -24.0), 5.0), ((0.0, -26.0), (38.0, -26.0), 4.5), ((0.0, -26.0), (-34.0, -24.0), 4.5), ((-34.0, -26.0), (-34.0, -4.0), 3.8), ((-20.0, -26.0), (-20.0, 6.0), 5.0),
         ((-20.0, 6.0), (0.0, 10.0), 5.0), ((0.0, 8.0), (0.0, 60.0), 10.5), ((0.0, 58.0), (-9.0, 92.0), 5.5), ((0.0, 66.0), (-29.0, 82.0), 4.5), ((-4.0, 70.0), (18.0, 76.0), 4.5),
         ((18.0, 70.0), (18.0, 101.0), 6.0), ((18.0, 101.0), (58.0, 101.0), 5.0), ((-34.0, -2.0), (-38.5, -1.0), 3.5), ((-38.5, -1.0), (-40.0, 14.0), 3.5), ((-40.0, 12.0), (-40.0, 62.0), 5.0),
         ((-40.0, 60.0), (-30.0, 64.0), 4.5), ((-9.0, 92.0), (-9.0, 106.0), 6.0), ((38.0, -30.0), (38.0, -14.0), 5.0), ((-34.0, -2.0), (-24.0, 5.0), 4.0)]
LEVELS = (GR, GU, GB)
_VEGSEQ = [0]


def _lane_dist(x, z):
    import murim_nightfall_terrain as T_
    best = 1e9
    for (a, b, w) in LANES:
        best = min(best, T_._seg_dist(x, z, a, b) - w)
    return best


def _ground(x, z, r):
    """The ground y (frame) under a piece with footprint radius r if the terrain is one flat level there (the middle and eight points on 0.8 r), else None."""
    h0 = cell_height(x, z)
    if h0 is None:
        return None
    for k in range(8):
        a = TAU * k / 8
        h = cell_height(x + 0.8 * r * math.cos(a), z + 0.8 * r * math.sin(a))
        if h is None or abs(h - h0) > 0.3:
            return None
    return h0 - Y0


def _clear(P, x, z, r, solid, y):
    """Clear of the architecture's colliders (grown by half the piece's radius plus a stud when it is solid) and of the library's own pieces."""
    grow = (0.5 * r + 0.8) if solid else 0.3
    for c in P.colliders:
        if c["y1"] - c["y0"] < 0.6 or c["y1"] < y - 0.2 or c["y0"] > y + 8.0:
            continue
        if c.get("rotated"):
            cx, cz = c["cx"], c["cz"]
            if math.hypot(x - cx, z - cz) <= grow + max(c["sx"], c["sz"]) / 2 + 0.2:
                if _in_rot(c, x, z, grow):
                    return False
        elif c["x0"] - grow <= x <= c["x1"] + grow and c["z0"] - grow <= z <= c["z1"] + grow:
            return False
    for v in P.veg:
        meta = veg()["pieces"][v["piece"]]
        if meta["keepout"] > 0 or solid:
            need = max(meta["keepout"], 0.0) + 0.45 * (r + meta["radius"]) if solid and meta["keepout"] > 0 else 0.4 * (r + meta["radius"])
            if math.hypot(x - v["x"], z - v["z"]) < need:
                return False
    return True


def _in_rot(c, x, z, grow):
    cs, sn = math.cos(c["yaw"]), math.sin(c["yaw"])
    dx, dz = x - c["cx"], z - c["cz"]
    u, v = dx * cs - dz * sn, dx * sn + dz * cs
    return abs(u) <= c["sx"] / 2 + grow and abs(v) <= c["sz"] / 2 + grow


def _try(P, name, x, z, yaw=0.0, scale=1.0, folder="Vegetation", spread=9.0, lane=True, tries=36):
    """Places a piece of the library at (x, z) or, if that is taken, at the nearest free spot on a widening spiral within `spread`; returns the placement or None."""
    k = "Nightfall_%s" % name
    meta = veg()["pieces"][k]
    r = meta["radius"] * scale
    solid = bool(meta["collision"]) or name.startswith(("Trees", "Rocks_Basalt", "Rocks_Split", "Rocks_Ember", "Rocks_Crag", "Rocks_Obs"))
    walk = meta.get("walkable")
    for t in range(tries):
        ang = t * 2.399963
        rad = spread * math.sqrt(t / float(tries - 1)) if t else 0.0
        px, pz = x + rad * math.cos(ang), z + rad * math.sin(ang)
        if lane and not walk and _lane_dist(px, pz) < (0.55 * r if solid else 0.3):
            continue
        y = _ground(px, pz, min(r, 6.0) * (0.8 if solid else 0.45))
        if y is None or not _clear(P, px, pz, r, solid, y):
            continue
        sy = y - 0.1 if walk else y
        return P.vegp(name, px, pz, y=sy, yaw=yaw, scale=scale, folder=folder)
    return None


def plant(P):
    """The vegetation library's pieces (agent B's: upright and angular, the faction's own), each at its ground on a free flat spot clear of every lane and collider. The mix follows the
    library's plan (16 trees, 24 rocks and paths, 60 plants) where the ground allows; a piece with no free place near its mark is left out."""
    if not veg()["pieces"]:
        return
    tp = lambda n, x, z, yaw=0.0, spread=9.0, folder="Vegetation": _try(P, n, x, z, yaw=yaw, spread=spread, folder=folder)
    # ---- trees: the landmark, then the families along the walls, rims and corners
    tp("Trees_GiantBlackthorn", 24.0, 34.0, spread=4.0)
    for (n, x, z) in (("Trees_AshthornA1", -47.0, -20.0), ("Trees_AshthornA1", 46.0, -24.0), ("Trees_AshthornA2", -49.0, 4.0), ("Trees_AshthornA2", 49.0, 10.0),
                      ("Trees_IronpineB1", -40.0, 110.0), ("Trees_IronpineB1", 20.0, 62.0), ("Trees_IronpineB2", 58.0, 87.0),
                      ("Trees_ShardtreeC1", 21.0, 108.0), ("Trees_ShardtreeC1", 57.0, 111.0), ("Trees_ShardtreeC2", 23.0, 104.0), ("Trees_ShardtreeC2", 53.0, 88.0),
                      ("Trees_CinderstumpD1", 40.0, 14.0), ("Trees_CinderstumpD1", -22.0, 30.0), ("Trees_CinderstumpD2", -28.0, -42.0), ("Trees_CinderstumpD2", 28.0, -42.0)):
        tp(n, x, z, yaw=_hash(int(x * 3), int(z * 3), 5) * TAU)
    # ---- rocks and the paths
    for (n, x, z, yw) in (("Rocks_BasaltColumns", -47.0, -4.0, 0.0), ("Rocks_BasaltColumns", 44.0, 24.0, 0.0), ("Rocks_BasaltPalisade", -34.0, 123.0, 0.0), ("Rocks_BasaltPalisade", 6.0, 122.0, 0.0),
                          ("Rocks_ObsidianShards", 21.0, 94.0, 0.0), ("Rocks_ObsidianShards", -18.0, 62.0, 0.0), ("Rocks_ObsidianShards", 52.0, 110.0, 0.0),
                          ("Rocks_SplitObelisk", -23.0, -42.0, 0.0), ("Rocks_SplitObelisk", 23.0, -42.0, PI), ("Rocks_EmberCone", -42.0, 120.0, 0.0), ("Rocks_EmberCone", 14.0, 66.0, 0.0),
                          ("Rocks_EmberFangs", 47.0, 96.0, 0.0), ("Rocks_EmberFangs", -14.0, 58.0, 0.0), ("Rocks_CragSpires", -40.0, 90.0, 0.0), ("Rocks_CragSpires", 52.0, 84.0, 0.0),
                          ("Rocks_ShardScatter", -16.0, -22.0, 0.0), ("Rocks_ShardScatter", 24.0, -20.0, 0.0), ("Rocks_ShardScatter", 36.0, 50.0, 0.0)):
        tp(n, x, z, yaw=yw, folder="Rocks")
    tp("Rocks_HexStepsA", 0.0, -41.0, spread=0.5, folder="Paths")
    for z in (64.0, 72.6, 81.2):
        _try(P, "Rocks_BasaltPave", -5.5, z, spread=0.4, folder="Paths", lane=False)
    # ---- plants: ash grass over the open ground, lilies at the gates and stair feet, thorns under the walls, spearleaf and ember crust at the rims
    areas = {"lower": (-52.0, 52.0, -46.0, 50.0), "upper": (-44.0, 22.0, 58.0, 124.0), "shelf": (12.0, 23.0, 91.0, 112.0), "ledge": (43.0, 61.0, 83.0, 113.0)}

    def scatter(name, count, area, seed, spread=0.0, folder="Vegetation"):
        x0, x1, z0, z1 = areas[area]
        placed = 0
        for t in range(count * 14):
            if placed >= count:
                break
            x = x0 + (x1 - x0) * _hash(t, 3, seed)
            z = z0 + (z1 - z0) * _hash(t, 5, seed + 1)
            if _try(P, name, x, z, yaw=_hash(t, 7, seed + 2) * TAU, spread=0.0, folder=folder, tries=1):
                placed += 1
    for name, n_l, n_u, n_s, n_r, seed in (("Plants_AshGrassA", 5, 3, 0, 1, 301), ("Plants_AshGrassB", 4, 2, 0, 1, 303), ("Plants_SpiderLilyA", 3, 2, 0, 0, 307), ("Plants_SpiderLilyB", 3, 1, 1, 0, 311),
                                           ("Plants_Thornbrake", 2, 1, 0, 1, 313), ("Plants_ThornClimber", 0, 0, 0, 0, 317), ("Plants_Spearleaf", 2, 2, 0, 1, 319), ("Plants_Thornrose", 2, 1, 0, 1, 323),
                                           ("Plants_Cinderbush", 2, 1, 1, 1, 329), ("Plants_Ashcap", 1, 1, 0, 1, 331), ("Plants_EmberCrust", 2, 0, 1, 0, 337), ("Plants_AshDrift", 3, 1, 0, 1, 347)):
        for area, cnt in (("lower", n_l), ("upper", n_u), ("shelf", n_s), ("ledge", n_r)):
            if cnt:
                scatter(name, cnt, area, seed + {'lower': 0, 'upper': 2, 'shelf': 4, 'ledge': 6}[area], folder="Paths" if name.startswith(("Plants_AshDrift", "Plants_EmberCrust")) else "Vegetation")


# ======================================================================================================================
# the terrain's own pavement: the lower ward is the pad's own Slate and Asphalt (flat to 0.000), the Upper Ward and the ledges Slate: nothing to repave
# ======================================================================================================================
def register_pavement():
    return 0


LOOK_VIEWS = {
    "plaza": ((0, 10, -150), (0, 30, 60), 38),
    "aerial_front": ((0, 80, -125), (0, 22, 40), 40),
    "from_gate": ((0, 8, -60), (0, 14, 60), 34),
    "lower_ward": ((-45, 30, -62), (10, 0, -5), 40),
    "arena": ((0, 22, -34), (0, 0, -6), 34),
    "training": ((-34, 12, -36), (-34, 2, 0), 36),
    "ember_court": ((38, 14, -34), (38, 2, -8), 34),
    "great_stair": ((0, 10, 2), (0, 18, 44), 34),
    "upper_ward": ((-5, 46, 58), (-9, 30, 100), 40),
    "keep": ((-9, 34, 56), (-9, 36, 106), 34),
    "armory": ((-4, 32, 70), (-37, 30, 82), 34),
    "fissure": ((12, 44, 80), (33, 28, 101), 36),
    "residence": ((36, 44, 78), (54, 42, 101), 36),
}


def plan_overlay(sx, sz):
    import nightfall_plan as PL
    P = build_all()
    out = []
    cols = {"hq": "#ffb08a", "hall": "#ffd08a", "house": "#ffb08a", "bridge": "#f2e6c8", "stair": "#ff9a5a", "court": "#9fe8ff", "shelter": "#ffe08a", "wall": "#e8e8e8",
            "gate": "#ffd0a8", "arena": "#ff8a8a", "tower": "#cfcfcf", "rail": "#bbbbbb"}
    for p in P.placements:
        col = cols.get(p["role"])
        if col is None:
            continue
        pc = P.pieces[p["piece"]]
        rects = list(pc.floor)
        if not rects:
            continue
        for (x0, x1, z0, z1, y) in rects:
            c, s = math.cos(p["yaw"]), math.sin(p["yaw"])
            pts = [(p["x"] + x * c + z * s, p["z"] - x * s + z * c) for x in (x0, x1) for z in (z0, z1)]
            out.append(PL.rect(min(q[0] for q in pts), max(q[0] for q in pts), min(q[1] for q in pts), max(q[1] for q in pts), col, col, 2, "", 0.25))
    for n, sp in P.spots.items():
        out.append(PL.circle(sp["pos"][0], sp["pos"][2], 0.9, "#7dffb0" if n.startswith("Npc") else ("#ff7a7a" if n.startswith("ArenaDummy") else "#ffffff"), "#0a0f1e", 1.5, 1.0))
    for l in P.lights:
        out.append(PL.circle(l["pos"][0], l["pos"][2], 1.1, "#ffe66d", "#0a0f1e", 1.5, 1.0))
    for e in P.effects:
        out.append(PL.circle(e["pos"][0], e["pos"][2], 0.7, "#ff9a3c", "#0a0f1e", 1.2, 1.0))
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
    print("colliders", len(P.colliders), "placements", len(P.placements), "lights", len(P.lights), "effects", len(P.effects), "spots", len(P.spots))
