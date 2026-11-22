"""Murim Crossing (the owner's faction map, 2026-11-22): one source for the island's shape, its terrain, its anchors and the plan sketch.
Plain Python (no Blender needed). Phase M1, the foundation: the ground, the court, three arms and three empty headquarters pads.

    python3 tools/blender/world/murim_layout.py            # check the layout, print its numbers
    python3 tools/blender/world/murim_layout.py --write    # also write src/worldbuild/Terrain/MurimCrossing.lua,
                                                           # src/worldbuild/Placements/MurimCrossing.lua and
                                                           # renders/murim_foundation/plan_topdown.png (local only)

Coordinates are Roblox studs. The island's own frame ("local") has its origin at the Court's middle, local -Z pointing back at the hub
(the side the bridge arrives on) and local +X toward the east-south-east. WorldBuilder.islandFrame turns local into world by the
island's Turns (not a whole number of quarter turns, so the terrain grid is written already turned: BakedTurn), as the Blossom
Sanctuary's. Where the island stands and its Turns are in layout.py (ISLANDS, ARRIVALS, ROUTES: the one source for every island and
bridge); this file reads them.

The shape (a trefoil, the owner's brief): a round neutral Court of Banners at the middle (radius COURT_R), an entry spur toward the hub
that carries the bridge in, and three arms at 120 degrees, each a causeway ARM_HALF * 2 wide leading to a headquarters plateau (a flat
building pad with its own slopes and cliff edge). The bridge arrives between two arms, facing the Court, with the third arm straight
ahead: Orthodox on the left (toward the Blossom Sanctuary), Demonic on the right, Unorthodox ahead, the one in the middle of the
other two, as in the old tales. Each plateau keeps its own outline from afar (round and ordered; lopsided and ragged; a crown of fangs)
and its own hanging underside (pale limestone; rock and earth; black slate), so the three read apart before anyone reaches them.
Terrain colours are global to the place, so the materials are ones whose colours are already set (WorldBuilder.MaterialColors).
"""
import json
import math
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

import blossom_layout as BL          # its noise, its footprint (the clearance check) and the shared sketch writer
import layout as LAYOUT              # where every island stands

ISLAND = "MurimCrossing"
CENTRE = tuple(float(v) for v in LAYOUT.ISLANDS[ISLAND]["centre"])
TURNS = LAYOUT.ISLANDS[ISLAND]["turns"]
YAW = -TURNS * math.pi / 2           # the island's turn about its centre (WorldBuilder.islandFrame: CFrame.Angles(0, -Turns * pi / 2, 0))
CELL = 4
ARRIVAL = LAYOUT.ARRIVALS[ISLAND]    # where the bridge's last deck node lands (local)

# ---------- the shape ----------
COURT_R = 46.0        # the Court of Banners
ARM_HALF = 13.0       # an arm is 26 studs wide, edge to edge (about 20 of them level: its edge slopes 3 studs)
PAD_D = 205.0         # a pad's middle, from the Court's
PAD_FLAT = 70.0       # every pad is level out to this radius from its middle (asserted below)
PAD_LIP = 12.0        # the slope from the level pad down to its cliff edge
PAD_DROP = 4.0
COURT_LIP = 8.0
COURT_DROP = 3.0
ARM_LIP = 3.0
ARM_DROP = 3.0
SPUR_HALF = 26.0      # the entry spur that carries the bridge in (the bridge's deck is 40 wide)
SPUR_FROM, SPUR_TO = -84.0, -38.0   # local Z: it starts under the bridge's abutment (8 long past the last node, ending at ABUTMENT_END)
ABUTMENT_END = -80.0  # the abutment's top is the bridge's end level (Y 200); the ground under it is 0.6 lower, so no two tops share a plane
GATE_Z = -64.0        # the island's own gate, on the spur
IDENTITY = 60.0       # how far down an arm its faction's mark runs (its gate stands 18 studs in)

ORDER = ["Orthodox", "Unorthodox", "Demonic"]
ANGLE = {"Orthodox": 120.0, "Unorthodox": 0.0, "Demonic": 240.0}    # degrees from local +Z (straight ahead) toward local +X
MATERIALS = ["Limestone", "Grass", "Pavement", "Ground", "Mud", "LeafyGrass", "Rock", "Slate", "Asphalt", "Basalt", "CrackedLava"]
MI = {m: i + 1 for i, m in enumerate(MATERIALS)}
# what each hanging underside is made of: (rock, the strata bands). The Court, the arms and the spur hang plain rock.
UNDERSIDE = {None: ("Rock", "Ground"), "Orthodox": ("Limestone", "Rock"), "Unorthodox": ("Rock", "Ground"), "Demonic": ("Slate", "Basalt")}
DEEPEST = 100.0       # the underside never reaches the fall line (110 under the island's ground)


def direction(f):
    a = math.radians(ANGLE[f])
    return math.sin(a), math.cos(a)


def pad_centre(f):
    dx, dz = direction(f)
    return dx * PAD_D, dz * PAD_D


def to_world(x, z):
    c, s = math.cos(YAW), math.sin(YAW)
    return CENTRE[0] + x * c + z * s, CENTRE[2] - x * s + z * c


def to_local(wx, wz):
    dx, dz = wx - CENTRE[0], wz - CENTRE[2]
    c, s = math.cos(YAW), math.sin(YAW)
    return dx * c - dz * s, dx * s + dz * c


vnoise, fbm, smoothstep, lerp = BL.vnoise, BL.fbm, BL.smoothstep, BL.lerp


def pad_polar(f, x, z):
    """(rho, phi) round a pad's middle: phi 0 points away from the Court (the pad's back), +-pi toward it (where its arm arrives)."""
    px, pz = pad_centre(f)
    dx, dz = direction(f)
    ox, oz = x - px, z - pz
    along = ox * dx + oz * dz
    across = ox * dz - oz * dx
    return math.hypot(ox, oz), math.atan2(across, along)


def pad_edge(f, phi):
    """The radius of a pad's outline at bearing phi: each faction's own shape."""
    if f == "Orthodox":      # round and ordered: a circle that hardly wavers
        return 88.0 + 1.6 * (fbm(math.cos(phi) * 2.0 + 11, math.sin(phi) * 2.0, 5) - 0.5)
    if f == "Unorthodox":    # lopsided and rough, like a bank worn by the river: about 83 to 108
        return 94.0 + 14.0 * (fbm(math.cos(phi) * 2.4 + 7, math.sin(phi) * 2.4 + 3, 9, 3) - 0.5) + 4.0 * math.cos(2.0 * (phi - 0.6))
    # Demonic: a crown of nine fangs (sharp tips, rounded valleys), smooth where the arm comes in
    u = (phi / (2 * math.pi)) * 9.0
    tri = 1.0 - abs(2.0 * (u - math.floor(u)) - 1.0)
    tooth = 84.0 + 17.0 * tri ** 1.6
    return lerp(tooth, 86.0, smoothstep(2.35, 2.85, abs(phi)))


def comp_fields(x, z):
    """Inside distance (studs, > 0 inside) of each part of the island: court, spur, the arms, the pads. Hard maxima: the lips are
    laid component by component so that a causeway stays level where it meets the Court or a pad."""
    out = {"court": COURT_R - math.hypot(x, z) + 2.4 * (fbm(x / 22.0, z / 22.0, 31) - 0.5)}
    if SPUR_FROM <= z <= SPUR_TO + 8:
        out["spur"] = SPUR_HALF - abs(x)
    else:
        out["spur"] = -1.0
    for f in ORDER:
        dx, dz = direction(f)
        t = x * dx + z * dz
        lat = abs(x * dz - z * dx)
        out["arm_" + f] = (ARM_HALF - lat + 0.8 * (fbm(x / 14.0, z / 14.0, 41) - 0.5)) if -2.0 <= t <= PAD_D else -1.0
        rho, phi = pad_polar(f, x, z)
        out["pad_" + f] = pad_edge(f, phi) - rho + 1.4 * (fbm(x / 18.0, z / 18.0, 51) - 0.5)
    return out


def lip_height(c, e):
    """Height over the island's ground (Y 200) of a column e studs inside its component."""
    if e <= 0:
        return None
    if c == "court":
        return -COURT_DROP * (1.0 - smoothstep(0.0, COURT_LIP, e))
    if c == "spur":
        return -ARM_DROP * (1.0 - smoothstep(0.0, ARM_LIP, e))
    if c.startswith("arm_"):
        return -ARM_DROP * (1.0 - smoothstep(0.0, ARM_LIP, e))
    return -PAD_DROP * (1.0 - smoothstep(0.0, PAD_LIP, e))


def island_field(x, z):
    return max(comp_fields(x, z).values())


# ---------- the ground ----------
def ground(x, z):
    """(height over Y 200, surface material, underside owner, fields) or (None, None, None, None) off the island."""
    fields = comp_fields(x, z)
    h = None
    for c, e in fields.items():
        v = lip_height(c, e)
        if v is not None and (h is None or v > h):
            h = v
    if h is None:
        return None, None, None, None
    if z < ABUTMENT_END + 1.0 and fields["spur"] > 0:
        h = min(h, -0.6)
    return h, surface(x, z, fields), underside_owner(fields), fields


def underside_owner(fields):
    for f in ORDER:
        if fields["pad_" + f] > 0:
            return f
    return None


def wedge_weight(f, x, z, inner, outer):
    """How far into a faction's mouth in the Court a point is (0 outside, 1 well inside), with a ragged edge."""
    r = math.hypot(x, z)
    if r < inner or r > outer + 1:
        return 0.0
    dx, dz = direction(f)
    ang = math.degrees(math.atan2(x * dz - z * dx, x * dx + z * dz))     # 0 on the arm's axis
    half = 23.0 + 9.0 * (fbm(x / 9.0, z / 9.0, 61) - 0.5)
    return 1.0 - smoothstep(half - 5, half, abs(ang))


def surface(x, z, fields):
    r = math.hypot(x, z)
    n = fbm(x / 11.0, z / 11.0, 71)       # patches of a second material
    n2 = fbm(x / 6.0, z / 6.0, 73)
    # a pad
    for f in ORDER:
        e = fields["pad_" + f]
        if e > 0:
            rho, phi = pad_polar(f, x, z)
            if f == "Orthodox":
                if e < 3.0:
                    return "Rock"
                return "Limestone" if rho < 63.0 else "Grass"
            if f == "Unorthodox":
                if e < 4.0:
                    return "Rock"
                if rho >= 62.0:
                    return "Ground" if n > 0.66 else ("Rock" if e < PAD_LIP * 0.6 else "LeafyGrass")
                px, pz = pad_centre(f)
                dx, dz = direction(f)
                across = abs((x - px) * dz - (z - pz) * dx)
                along = (x - px) * dx + (z - pz) * dz
                if across < 3.2 and along < 0:       # the dirt road from the arm to the middle
                    return "Ground"
                if n > 0.78:
                    return "Mud"
                return "Ground" if n > 0.67 else "LeafyGrass"
            # Demonic
            if e < 6.0 and n2 > 0.64:
                return "CrackedLava"                 # glowing seams along the fangs (nothing is built out there)
            if e < PAD_LIP:
                return "Basalt" if e < 9.0 else "Slate"
            return "Asphalt" if n > 0.62 else "Slate"
    # the Court
    if fields["court"] > 0:
        if fields["court"] < 2.0:
            return "Rock"
        for f in ("Unorthodox", "Demonic"):
            w = wedge_weight(f, x, z, 29.0, COURT_R)
            if w > 0.5:
                if f == "Unorthodox":
                    return "Mud" if n > 0.72 else "Ground"
                return "Asphalt" if n > 0.66 else "Slate"
        if r < 11.0 or 28.0 <= r < 31.0:
            return "Pavement"
        return "Limestone"
    # the spur
    if fields["spur"] > 0:
        if fields["spur"] < 2.0:
            return "Rock"
        return "Pavement" if abs(x) > 19.0 else "Limestone"
    # the arms
    for f in ORDER:
        e = fields["arm_" + f]
        if e > 0:
            dx, dz = direction(f)
            lat = abs(x * dz - z * dx)
            if e < 2.0:
                return "Rock"
            if f == "Orthodox":
                return "Limestone" if lat < 9.0 else "Grass"
            if f == "Unorthodox":
                if lat < 9.0:
                    return "Mud" if n > 0.74 else "Ground"
                return "LeafyGrass"
            return "Slate" if lat < 9.0 else "Asphalt"
    return "Rock"


def bottom(x, z, fields):
    """How deep the rock underside reaches at this column (negative, over Y 200): a cone under each pad, a bowl under the Court, a
    keel under each arm and the spur, ridged by noise; never past DEEPEST."""
    d = 6.0
    r = math.hypot(x, z)
    if fields["court"] > -6:
        d = max(d, 6.0 + 62.0 * max(0.0, 1.0 - (r / (COURT_R + 4)) ** 1.7))
    if fields["spur"] > -1:
        d = max(d, 6.0 + 9.0 * max(0.0, 1.0 - (x / SPUR_HALF) ** 2))
    for f in ORDER:
        if fields["arm_" + f] > -1:
            dx, dz = direction(f)
            lat = abs(x * dz - z * dx)
            d = max(d, 7.0 + 16.0 * max(0.0, 1.0 - (lat / ARM_HALF) ** 2))
        rho, phi = pad_polar(f, x, z)
        edge = pad_edge(f, phi)
        if rho < edge + 4:
            d = max(d, 8.0 + 84.0 * max(0.0, 1.0 - (rho / (edge + 4)) ** 1.35))
    e = max(0.0, max(fields.values()))
    d += 9.0 * (fbm(x / 30.0, z / 30.0, 81) - 0.45) * smoothstep(0, 28, e)
    return -max(6.0, min(DEEPEST, d))


# ---------- the grid ----------
def grid():
    pts = []
    reach = PAD_D + 110.0
    for k in range(72):
        a = 2 * math.pi * k / 72
        pts.append(to_world(math.cos(a) * reach, math.sin(a) * reach))
    xs, zs = [p[0] for p in pts], [p[1] for p in pts]
    ox = math.floor(min(xs) / CELL) * CELL - CELL
    oz = math.floor(min(zs) / CELL) * CELL - CELL
    n = int(math.ceil(max(max(xs) - ox, max(zs) - oz) / CELL)) + 2
    return ox, oz, n


def sample_grid():
    ox, oz, n = grid()
    H, M, B, U, S = [], [], [], [], []
    for j in range(n):
        for i in range(n):
            wx, wz = ox + (i + 0.5) * CELL, oz + (j + 0.5) * CELL
            x, z = to_local(wx, wz)
            h, m, owner, fields = ground(x, z)
            if h is None:
                H.append(None); M.append(0); B.append(None); U.append(0); S.append(0)
                continue
            H.append(h); M.append(MI[m]); B.append(bottom(x, z, fields))
            rock, strata = UNDERSIDE[owner]
            U.append(MI[rock]); S.append(MI[strata])
    return ox, oz, n, H, M, B, U, S


# ---------- anchors (everything a headquarters phase builds on) ----------
def arm_point(f, t, lateral=0.0):
    dx, dz = direction(f)
    return dx * t + dz * lateral, dz * t - dx * lateral


def pad_point(f, along, across=0.0):
    """A point on a pad: `along` studs from its middle toward its back (away from the Court), `across` studs to its right when
    looking out from the Court."""
    px, pz = pad_centre(f)
    dx, dz = direction(f)
    return px + dx * along + dz * across, pz + dz * along - dx * across


def yaw_facing(vx, vz):
    """Y rotation (CFrame.Angles(0, yaw, 0)) that turns a model's front (-Z) toward the horizontal direction (vx, vz)."""
    return math.atan2(-vx, -vz)


def anchors():
    a = {"Court": {"Centre": (0.0, 0.0), "Radius": COURT_R, "OathStone": (0.0, 0.0), "OathYaw": 0.0},
         "Gate": {"Position": (0.0, GATE_Z), "Yaw": 0.0}, "Arrival": ARRIVAL, "Spur": (SPUR_FROM, SPUR_TO, SPUR_HALF),
         "Checkpoint": {"Position": (0.0, -24.0), "Yaw": math.pi}, "Arms": {}, "Pads": {}, "Reps": {}, "Banners": {}}
    for f in ORDER:
        dx, dz = direction(f)
        yaw_to_court = yaw_facing(-dx, -dz)
        yaw_out = yaw_facing(dx, dz)
        px, pz = pad_centre(f)
        a["Arms"][f] = {"Axis": (dx, dz), "Half": ARM_HALF, "From": COURT_R, "To": PAD_D - PAD_FLAT + 2.0,
                        "Centreline": [arm_point(f, t) for t in (COURT_R, COURT_R + IDENTITY, PAD_D - PAD_FLAT + 2.0)],
                        "GateAt": COURT_R + 18.0, "IdentityTo": COURT_R + IDENTITY}
        # a pad: its middle, its flat radius, its outline, which way it faces (toward the Court), the gate where its arm arrives,
        # the main hall's spot (toward its back, facing the Court), the representative's spot (at the Court, in front of the
        # arm), the vault's, and the trial's points
        gate = pad_point(f, -PAD_FLAT + 2.0)
        pad = {"Centre": (px, pz), "FlatRadius": PAD_FLAT, "EdgeRadius": {"Orthodox": 88.0, "Unorthodox": 94.0, "Demonic": 92.0}[f], "Front": (-dx, -dz), "FrontYaw": yaw_to_court,
               "Gate": {"Position": gate, "Yaw": yaw_out},
               "MainHall": {"Position": pad_point(f, 14.0), "Yaw": yaw_to_court},
               "Vault": {"Position": pad_point(f, 34.0, 44.0), "Yaw": yaw_to_court},
               "Checkpoint": {"Position": gate, "Yaw": yaw_out}}
        if f == "Orthodox":      # five gates up the ceremonial stair, from the pad's front to the hall
            pad["Trial"] = {"Gates": [pad_point(f, -62.0 + k * 11.5) for k in range(5)]}
        elif f == "Unorthodox":  # places a token may be hidden: a ring round the hold (the trial picks three)
            pad["Trial"] = {"TokenSpots": [pad_point(f, 54.0 * math.cos(math.radians(30 + 60 * k)), 54.0 * math.sin(math.radians(30 + 60 * k))) for k in range(6)]}
        else:                    # the arena's middle and the three places each wave comes from
            pad["Trial"] = {"Arena": pad_point(f, -4.0), "Waves": [pad_point(f, -4.0 + 26.0 * math.cos(math.radians(90 + 120 * k)), 26.0 * math.sin(math.radians(90 + 120 * k))) for k in range(3)]}
        a["Pads"][f] = pad
        a["Reps"][f] = {"Position": arm_point(f, 34.0), "Yaw": yaw_to_court}
        a["Banners"][f] = {"Position": arm_point(f, 24.0), "Yaw": yaw_to_court}
    return a


# ---------- checks ----------
def boundary_world(H, n, ox, oz):
    """World X/Z of every ground cell that has a neighbour with none."""
    out = []
    for j in range(1, n - 1):
        for i in range(1, n - 1):
            k = j * n + i
            if H[k] is None:
                continue
            if H[k + 1] is None or H[k - 1] is None or H[k + n] is None or H[k - n] is None:
                out.append((ox + (i + 0.5) * CELL, oz + (j + 0.5) * CELL))
    return out


def blossom_boundary():
    ox, oz, n, H, M, Wt, B = BL.sample_grid()
    return boundary_world(H, n, ox, oz)


def report():
    ox, oz, n, H, M, B, U, S = sample_grid()
    cells = sum(1 for v in H if v is not None)
    area = cells * CELL * CELL
    mine = boundary_world(H, n, ox, oz)
    clear = {}
    for name, info in LAYOUT.ISLANDS.items():
        if name == ISLAND:
            continue
        cx, _, cz = info["centre"]
        if name == "Yggdrasil":
            r = 248.0
        else:
            r = float(info["radius"])
        clear[name] = round(min(math.hypot(wx - cx, wz - cz) for wx, wz in mine) - r)
    bb = blossom_boundary()
    best = 1e9
    for wx, wz in mine:
        for bx, bz in bb:
            d = math.hypot(wx - bx, wz - bz)
            if d < best:
                best = d
    clear["BlossomSanctuary"] = round(best)
    hubx, hubz = 0.0, 0.0
    # the flat pads: every pad is level out to PAD_FLAT, every arm to ARM_HALF - ARM_LIP, the Court to COURT_R - COURT_LIP
    worst_pad = {}
    for f in ORDER:
        worst = 1e9
        for k in range(360):
            phi = math.radians(k)
            worst = min(worst, pad_edge(f, phi) - PAD_LIP - 1.4)
        worst_pad[f] = round(worst, 1)
    lows = [b for b in B if b is not None]
    start, end = LAYOUT.BRIDGES["MurimRoute"]["start"], LAYOUT.BRIDGES["MurimRoute"]["end"]
    return {
        "grid": {"origin": (ox, oz), "size": n, "cells": cells},
        "area_sq_studs": area, "origin_abyss_disc_sq_studs": round(math.pi * 165 ** 2), "blossom_sq_studs": 175728,
        "deepest_underside": min(lows), "turns": TURNS, "yaw_deg": round(math.degrees(YAW), 2),
        "centre": CENTRE, "hub_to_centre": round(math.hypot(CENTRE[0], CENTRE[2])),
        "bridge": {"start": start, "end": end, "flat_length": round(LAYOUT.flat(start, end)), "nodes": len(LAYOUT.bridge_nodes("MurimRoute")) - 1},
        "clearance_to_islands_ground_to_ground": clear, "flat_radius_guaranteed_by_outline": worst_pad,
        "reach": round(max(math.hypot(*[v for v in to_local(wx, wz)]) for wx, wz in mine)),
    }


# ---------- writing ----------
def lua_num(v):
    return "false" if v is None else ("%.2f" % v)


def write_terrain(path):
    ox, oz, n, H, M, B, U, S = sample_grid()
    lines = [
        "-- Written by tools/blender/world/murim_layout.py (Murim Crossing, 2026-11-22). Do not edit by hand.",
        "return {",
        '    Island = "%s",' % ISLAND,
        "    Centre = Vector3.new(%g, %g, %g)," % CENTRE,
        "    Turns = %.5f, -- quarter turns about the centre, each adding 90 degrees of bearing" % TURNS,
        "    BakedTurn = true, -- the grid below is already turned",
        "    Origin = Vector2.new(%g, %g), -- world X/Z of the grid's first corner" % (ox, oz),
        "    Cell = %d," % CELL,
        "    Size = %d," % n,
        "    Materials = { %s }," % ", ".join('"%s"' % m for m in MATERIALS),
    ]

    def chunked(name, vals):
        out = ["    %s = {" % name]
        for k in range(0, len(vals), n):
            out.append("        " + ", ".join(vals[k:k + n]) + ",")
        out.append("    },")
        return out
    lines += chunked("Heights", [lua_num(v) for v in H])
    lines += chunked("MaterialIndex", [str(v) for v in M])
    lines.append("    -- how deep the rock underside reaches under each column (over Centre.Y), and what it is made of (a Materials index, and the")
    lines.append("    -- strata bands' one): pale limestone under the Orthodox pad, rock and earth under the Unorthodox, black slate under the Demonic")
    lines += chunked("Bottoms", [lua_num(v) for v in B])
    lines += chunked("UndersideIndex", [str(v) for v in U])
    lines += chunked("StrataIndex", [str(v) for v in S])
    lines += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return n, sum(1 for h in H if h is not None)


def v2(p, y=0.0):
    return "Vector3.new(%.2f, %.2f, %.2f)" % (p[0], y, p[1])


def write_placements(path):
    a = anchors()
    L = ["-- Written by tools/blender/world/murim_layout.py (Murim Crossing, 2026-11-22). Do not edit by hand.",
         "-- Island-local Roblox studs (local -Z faces the hub, +X is the Orthodox side), every Y 0 = the island's ground (world Y 200). Read by",
         "-- CrossingBuilder (the court, the gate, the banners, the representatives, the zones) and, later, by each headquarters' build.",
         "-- Yaw: CFrame.Angles(0, Yaw, 0) in the island's frame turns a model's front (-Z) the way it says. Pads: Front is the unit vector toward",
         "-- the Court (a headquarters' main hall faces it), Gate the pad's entrance where its arm arrives, FlatRadius how far from Centre the",
         "-- ground is exactly level; the pad's own materials are Limestone/Grass (Orthodox), LeafyGrass/Mud/Ground/Rock (Unorthodox) and",
         "-- Slate/Asphalt (Demonic): never lay a floor on Grass (its blades come up through it) and keep Basalt/CrackedLava (they bump) to",
         "-- ground nothing is built on.",
         "return {",
         "    Reach = %d," % round(report()["reach"] + 6),
         "    Court = { Centre = %s, Radius = %.1f, OathStone = %s, OathYaw = %.4f }," % (v2(a["Court"]["Centre"]), COURT_R, v2(a["Court"]["OathStone"]), a["Court"]["OathYaw"]),
         "    Gate = { Position = %s, Yaw = %.4f }, -- the island's own gate, across the end of the bridge" % (v2(a["Gate"]["Position"]), a["Gate"]["Yaw"]),
         "    Arrival = %s, -- where the bridge's last deck node lands" % ("Vector3.new(%.2f, 0, %.2f)" % (ARRIVAL[0], ARRIVAL[2])),
         "    Spur = { FromZ = %.1f, ToZ = %.1f, Half = %.1f }," % (SPUR_FROM, SPUR_TO, SPUR_HALF),
         "    Checkpoint = { Position = %s, Yaw = %.4f }, -- where a fall from the island returns to: the Court, facing the oath stone" % (v2(a["Checkpoint"]["Position"]), a["Checkpoint"]["Yaw"]),
         "    Order = { \"Orthodox\", \"Unorthodox\", \"Demonic\" },"]
    L.append("    Arms = {")
    for f in ORDER:
        arm = a["Arms"][f]
        L.append("        %s = { Axis = Vector3.new(%.4f, 0, %.4f), Half = %.1f, From = %.1f, To = %.1f, GateAt = %.1f, IdentityTo = %.1f, Centreline = { %s } }," % (
            f, arm["Axis"][0], arm["Axis"][1], arm["Half"], arm["From"], arm["To"], arm["GateAt"], arm["IdentityTo"], ", ".join(v2(p) for p in arm["Centreline"])))
    L.append("    },")
    L.append("    Reps = { -- each faction's representative stands in the Court in front of its arm, facing the oath stone")
    for f in ORDER:
        L.append("        %s = { Position = %s, Yaw = %.4f }," % (f, v2(a["Reps"][f]["Position"]), a["Reps"][f]["Yaw"]))
    L.append("    },")
    L.append("    Banners = { -- a tall pole between the oath stone and each representative")
    for f in ORDER:
        L.append("        %s = { Position = %s, Yaw = %.4f }," % (f, v2(a["Banners"][f]["Position"]), a["Banners"][f]["Yaw"]))
    L.append("    },")
    L.append("    Pads = {")
    for f in ORDER:
        p = a["Pads"][f]
        L.append("        %s = {" % f)
        L.append("            Centre = %s, FlatRadius = %.1f, EdgeRadius = %.1f," % (v2(p["Centre"]), p["FlatRadius"], p["EdgeRadius"]))
        L.append("            Front = Vector3.new(%.4f, 0, %.4f), FrontYaw = %.4f," % (p["Front"][0], p["Front"][1], p["FrontYaw"]))
        for key in ("Gate", "MainHall", "Vault", "Checkpoint"):
            L.append("            %s = { Position = %s, Yaw = %.4f }," % (key, v2(p[key]["Position"]), p[key]["Yaw"]))
        t = p["Trial"]
        for key, val in t.items():
            if isinstance(val, list):
                L.append("            Trial%s = { %s }," % (key, ", ".join(v2(q) for q in val)))
            else:
                L.append("            Trial%s = %s," % (key, v2(val)))
        L.append("        },")
    L.append("    },")
    L += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(L))
    return 1


# ---------- the sketch ----------
COL = {"Limestone": (214, 214, 226), "Grass": (104, 160, 86), "Pavement": (176, 180, 198), "Ground": (128, 100, 74), "Mud": (86, 68, 50),
       "LeafyGrass": (70, 122, 62), "Rock": (120, 122, 130), "Slate": (60, 58, 72), "Asphalt": (70, 64, 64), "Basalt": (44, 40, 42),
       "CrackedLava": (255, 110, 40)}


def sketch(path):
    S = 1.2
    R = PAD_D + 120
    X0, X1, Z0, Z1 = -R, R, -R - 60, R
    w, h = int((X1 - X0) * S), int((Z1 - Z0) * S)
    px = bytearray(w * h * 3)
    sky = (34, 40, 56)
    for j in range(h):
        z = Z1 - (j + 0.5) / S
        for i in range(w):
            x = X1 - (i + 0.5) / S               # seen from above: local -Z (the hub) at the bottom, +X on the left
            hh, m, owner, fields = ground(x, z)
            c = sky if hh is None else COL[m]
            if hh is not None:
                shade = 0.9 + 0.04 * hh
                c = tuple(min(255, int(v * shade)) for v in c)
            k = (j * w + i) * 3
            px[k:k + 3] = bytes(c)

    def put(x, z, c, a=1.0):
        i, j = int((X1 - x) * S), int((Z1 - z) * S)
        if 0 <= i < w and 0 <= j < h:
            k = (j * w + i) * 3
            for m in range(3):
                px[k + m] = int(px[k + m] * (1 - a) + c[m] * a)

    def disc(x, z, r, c, a=1.0):
        for dz in range(int(-r * S) - 1, int(r * S) + 2):
            for dx in range(int(-r * S) - 1, int(r * S) + 2):
                if math.hypot(dx, dz) / S <= r:
                    put(x + dx / S, z + dz / S, c, a)

    # the bridge, the gate, the anchors, the representatives
    for t in range(0, 90):
        for s in range(-20, 21, 2):
            put(s, ARRIVAL[2] - 90 + t, (236, 228, 210))
    FC = {"Orthodox": (96, 168, 255), "Unorthodox": (70, 200, 150), "Demonic": (226, 52, 48)}
    a = anchors()
    disc(0, GATE_Z, 2.0, (255, 220, 120))
    disc(0, 0, 3.0, (255, 255, 255))
    for f in ORDER:
        disc(*a["Reps"][f]["Position"], 2.2, FC[f])
        disc(*a["Banners"][f]["Position"], 1.6, FC[f])
        disc(*a["Pads"][f]["Gate"]["Position"], 2.0, (255, 220, 120))
        disc(*a["Pads"][f]["Centre"], 2.5, FC[f])
        for q in a["Pads"][f]["Trial"].values():
            for p in (q if isinstance(q, list) else [q]):
                disc(*p, 1.2, FC[f], 0.8)
    write_png(path, w, h, px)
    return w, h


write_png = BL.write_png

def verify(r):
    """The layout's rules, each printed as OK or BAD (a BAD ends the run with an error)."""
    rules = [
        ("every plateau is level to at least %d studs" % PAD_FLAT, min(r["flat_radius_guaranteed_by_outline"].values()) >= PAD_FLAT),
        ("every other island is at least 100 studs of open sky away", min(r["clearance_to_islands_ground_to_ground"].values()) >= 100),
        ("the bridge is one span of 200 to 280 studs", 200 <= r["bridge"]["flat_length"] <= 280),
        ("the underside stays above the 110-stud fall line", r["deepest_underside"] > -105),
        ("its ground is within 10% of Origin Abyss's", abs(r["area_sq_studs"] / r["origin_abyss_disc_sq_studs"] - 1.0) <= 0.10),
        ("the grid origin and the centre are whole 4-stud voxels", all(float(v) % CELL == 0 for v in (r["grid"]["origin"][0], r["grid"]["origin"][1], CENTRE[0], CENTRE[2]))),
    ]
    bad = 0
    for text, ok in rules:
        print(("OK   " if ok else "BAD  ") + text)
        bad += 0 if ok else 1
    return bad


if __name__ == "__main__":
    r = report()
    print(json.dumps(r, indent=1, default=list))
    if verify(r):
        sys.exit("layout rules broken")
    if "--write" in sys.argv:
        n, cells = write_terrain(os.path.join(REPO, "src", "worldbuild", "Terrain", ISLAND + ".lua"))
        write_placements(os.path.join(REPO, "src", "worldbuild", "Placements", ISLAND + ".lua"))
        os.makedirs(os.path.join(REPO, "renders", "murim_foundation"), exist_ok=True)
        wh = sketch(os.path.join(REPO, "renders", "murim_foundation", "plan_topdown.png"))
        print("WROTE terrain %dx%d (%d cells), sketch %s" % (n, n, cells, wh))
