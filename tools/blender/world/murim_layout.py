"""Murim Crossing (the owner's faction map, 2026-11-22): one source for the island's shape, its terrain, its anchors and the plan sketch.
Plain Python (no Blender needed). Phase M1, the foundation: the ground, the plaza, three stairways and three empty headquarters pads.

    python3 tools/blender/world/murim_layout.py            # check the layout, print its numbers
    python3 tools/blender/world/murim_layout.py --write    # also write src/worldbuild/Terrain/MurimCrossing.lua,
                                                           # src/worldbuild/Placements/MurimCrossing.lua and
                                                           # renders/murim_foundation/plan_topdown.png (local only)

Coordinates are Roblox studs. The island's own frame ("local") has its origin at the Plaza's middle, local -Z pointing back at the hub (the
side the bridge arrives on), local +Z away from it, and local +X to the LEFT of someone who has just arrived and looks across the plaza.
WorldBuilder.islandFrame turns local into world by the island's Turns (not a whole number of quarter turns, so the terrain grid is written
already turned: BakedTurn), as the Blossom Sanctuary's. Where the island stands and its Turns are in layout.py (ISLANDS, ARRIVALS, ROUTES:
the one source for every island and bridge); this file reads them.

The shape (the owner's picture, 2026-11-22, used as a LAYOUT reference only): the bridge from the hub lands at the front of a large circular
PLAZA; across it, three headquarters stand side by side on raised pads, each reached by its own grand stairway rising from the plaza's far
edge: ORTHODOX on the left, UNORTHODOX in the centre (further back, higher, on the mountain), DEMONIC on the right. The side pads stand 16
studs over the plaza, the centre pad 36. Behind them rise tall rock mountains (rounded, cliff-sided mesas for the Orthodox and Unorthodox,
sharp jagged spires for the Demonic), with room for waterfalls on the first two. The Unorthodox side has hidden paths to four lookouts.
Terrain colours are global to the place, so the materials are ones whose colours are already set (WorldBuilder.MaterialColors).
"""
import json
import math
import os
import sys

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

# ---------- the plaza, the entry ----------
PLAZA_R = 76.0
PLAZA_LIP = 8.0
PLAZA_DROP = 3.0
SPUR_HALF = 26.0      # the entry spur that carries the bridge in (the bridge's deck is 40 wide)
SPUR_FROM, SPUR_TO = -120.0, -60.0   # local Z: it starts under the bridge's abutment (8 long past the last node, ending at ABUTMENT_END)
ABUTMENT_END = -116.0 # the abutment's top is the bridge's end level (Y 200); the ground under it is 0.6 lower, so no two tops share a plane
GATE_Z = -100.0       # the island's own gate, on the spur
REP_S = 54.0          # how far along its stair's axis from the plaza's middle each representative stands (on the plaza)
BANNER_S, BANNER_U = 62.0, 21.0      # a banner pole: along the stair's axis and to the side of it

ORDER = ["Orthodox", "Unorthodox", "Demonic"]
ZONE = {"Orthodox": "O", "Unorthodox": "U", "Demonic": "D"}
STEP_RISE = 1.0       # every step is a stud high
STAIR_HALF = 16.0     # a stairway is 32 studs wide, a landing 52
LANDING_HALF = 26.0
UNDER_STEP = 1.8      # the terrain under a flight lies this far under the steps' line (the steps are solid boxes that stand in it)

# the headquarters: the stair's bearing from local +Z (toward local +X), the pad's height over the plaza and its middle's distance along
# the bearing, its radius (flat out to `flat`, then a slope), and the stair's tiers as (kind, from s, to s, from h, to h). A stair ends where the
# pad's flat disc begins: pad_s - flat = the last tier's end.
SIDE_TIERS = [("flight", 72.0, 96.0, 0.0, 6.0), ("landing", 96.0, 112.0, 6.0, 6.0), ("flight", 112.0, 152.0, 6.0, 16.0)]
HQ = {
    "Orthodox": {"angle": 38.0, "pad_h": 16.0, "pad_s": 206.0, "pad_r": 62.0, "flat": 54.0, "tiers": SIDE_TIERS},
    "Unorthodox": {"angle": 0.0, "pad_h": 36.0, "pad_s": 250.0, "pad_r": 66.0, "flat": 58.0, "tiers": [
        ("flight", 72.0, 102.0, 0.0, 12.0), ("landing", 102.0, 118.0, 12.0, 12.0), ("flight", 118.0, 148.0, 12.0, 24.0),
        ("landing", 148.0, 162.0, 24.0, 24.0), ("flight", 162.0, 192.0, 24.0, 36.0)]},
    "Demonic": {"angle": -38.0, "pad_h": 16.0, "pad_s": 206.0, "pad_r": 62.0, "flat": 54.0, "tiers": SIDE_TIERS},
}
PAD_SKIRT = 12.0      # the slope from a pad's flat disc down (or up) to the ground round it

# the backdrop: zone, middle x, z, radius, height over the plaza, style. A "mesa" has a rounded top and cliff sides; a "spire" is sharp and
# jagged. Each one's footprint is ground too.
MOUNTAINS = [
    ("O", 200.0, 292.0, 78.0, 70.0, "mesa"), ("O", 284.0, 204.0, 48.0, 54.0, "mesa"), ("O", 116.0, 320.0, 56.0, 58.0, "mesa"),
    ("U", 0.0, 358.0, 88.0, 98.0, "mesa"), ("U", -102.0, 328.0, 50.0, 68.0, "mesa"), ("U", 102.0, 328.0, 50.0, 68.0, "mesa"),
    ("D", -200.0, 292.0, 68.0, 86.0, "spire"), ("D", -284.0, 206.0, 44.0, 72.0, "spire"), ("D", -116.0, 320.0, 48.0, 78.0, "spire"),
    ("D", -242.0, 324.0, 40.0, 104.0, "spire"),
]
# the massif the pads and the mountains stand on: ellipses (middle x, z, half width x, z)
MASSIF = [(0.0, 188.0, 200.0, 112.0), (0.0, 254.0, 104.0, 80.0)]
FOOTHILL = 22.0       # how far over the plaza the ground behind the pads has risen by z 230

# hidden paths of the Unorthodox side: each a list of (x, z, h) knots (h None: the ground's own height there, plus a stud), 3 studs half-wide;
# the lookouts they end at (x, z, radius); and two ravines cut into the hillside (middle x, z, half width x, half length z, depth), each crossed
# by a rope bridge between the two paths that end at its rims
PATHS = [
    [(-26.0, 155.0, 24.0), (-40.0, 178.0, None), (-56.0, 198.0, None), (-72.0, 214.0, None)],
    [(26.0, 155.0, 24.0), (40.0, 178.0, None), (56.0, 198.0, None), (72.0, 214.0, None)],
    [(-40.0, 308.0, None), (-50.0, 304.0, None)],
    [(-74.0, 296.0, None), (-86.0, 284.0, None), (-92.0, 270.0, None)],
    [(40.0, 308.0, None), (50.0, 304.0, None)],
    [(74.0, 296.0, None), (86.0, 284.0, None), (92.0, 270.0, None)],
]
NOOKS = [(-72.0, 214.0, 6.5), (72.0, 214.0, 6.5), (-92.0, 270.0, 6.5), (92.0, 270.0, 6.5)]
RAVINES = [(-62.0, 300.0, 10.0, 15.0, 14.0), (62.0, 300.0, 10.0, 15.0, 14.0)]
ROPE_BRIDGES = [((-51.0, 303.0), (-73.0, 297.5)), ((51.0, 303.0), (73.0, 297.5))]   # (x, z) of the two rims
PATH_HALF = 3.0

MATERIALS = ["Limestone", "Grass", "Pavement", "Ground", "Mud", "LeafyGrass", "Rock", "Slate", "Asphalt", "Basalt", "CrackedLava", "Sandstone"]
MI = {m: i + 1 for i, m in enumerate(MATERIALS)}
# what each hanging underside is made of: (rock, the strata bands). The plaza and the spur hang plain rock.
UNDERSIDE = {None: ("Rock", "Ground"), "O": ("Limestone", "Rock"), "U": ("Sandstone", "Rock"), "D": ("Slate", "Basalt")}
DEEPEST = 100.0       # the underside never reaches the fall line (110 under the island's ground)

vnoise, fbm, smoothstep, lerp = BL.vnoise, BL.fbm, BL.smoothstep, BL.lerp


def direction(f):
    a = math.radians(HQ[f]["angle"])
    return math.sin(a), math.cos(a)


def pad_centre(f):
    dx, dz = direction(f)
    return dx * HQ[f]["pad_s"], dz * HQ[f]["pad_s"]


def to_world(x, z):
    c, s = math.cos(YAW), math.sin(YAW)
    return CENTRE[0] + x * c + z * s, CENTRE[2] - x * s + z * c


def to_local(wx, wz):
    dx, dz = wx - CENTRE[0], wz - CENTRE[2]
    c, s = math.cos(YAW), math.sin(YAW)
    return dx * c - dz * s, dx * s + dz * c


def su(f, x, z):
    """(s, u) of a point for a headquarters: along its stair's axis from the plaza's middle, and across it (positive toward +X)."""
    a = math.radians(HQ[f]["angle"])
    return x * math.sin(a) + z * math.cos(a), x * math.cos(a) - z * math.sin(a)


def tiers(f):
    return HQ[f]["tiers"]


def stair_line(f, s):
    """The walking line of a stairway at distance s along its axis: 0 on the plaza, the flights' straight ramps, the landings' levels, the
    pad's height beyond the last tier."""
    t = tiers(f)
    if s <= t[0][1]:
        return 0.0
    if s >= t[-1][2]:
        return t[-1][4]
    for kind, s0, s1, h0, h1 in t:
        if s0 <= s <= s1:
            return lerp(h0, h1, (s - s0) / (s1 - s0))
    return 0.0


def stair_kind(f, s):
    for kind, s0, s1, h0, h1 in tiers(f):
        if s0 <= s <= s1:
            return kind
    return "pad" if s > tiers(f)[-1][2] else "plaza"


# ---------- the ground's height ----------
def foothill(x, z):
    """The slope behind the plaza the pads and mountains stand on: rising from nothing at z 50 to FOOTHILL by z 230."""
    return FOOTHILL * smoothstep(50.0, 230.0, z) * (0.85 + 0.3 * fbm(x / 70.0, z / 70.0, 91)) + 3.0 * (fbm(x / 26.0, z / 26.0, 93) - 0.5)


def mountain_height(x, z):
    """(the tallest mountain's height at a point (0 off all of them), its zone)."""
    best, zone = 0.0, None
    for z_, cx, cz, R, H, style in MOUNTAINS:
        warp = 0.1 * R * (fbm(x / 40.0 + 3, z / 40.0, 97) - 0.5)
        d = math.hypot(x - cx, z - cz) + warp
        t = 1.0 - d / R
        if t <= 0:
            continue
        if style == "mesa":
            v = H * smoothstep(0.10, 0.52, t) * (0.93 + 0.07 * fbm(x / 22.0, z / 22.0, 101)) + 0.12 * H * t
        else:
            ridge = 1.0 - abs(2.0 * fbm(x / 15.0, z / 15.0, 103) - 1.0)
            v = H * (t ** 1.1) * (0.7 + 0.55 * ridge)
        if v > best:
            best, zone = v, z_
    return best, zone


def massif_inside(x, z):
    """Inside distance (studs) of the ground behind the plaza: the massif's ellipses and every mountain's footprint."""
    best = -1e9
    for cx, cz, a, b in MASSIF:
        best = max(best, (1.0 - math.hypot((x - cx) / a, (z - cz) / b)) * min(a, b))
    for z_, cx, cz, R, H, style in MOUNTAINS:
        best = max(best, R * 0.98 - math.hypot(x - cx, z - cz))
    for q in ORDER:                      # every pad's flat disc and its slope are ground whatever the ellipses do
        px, pz = pad_centre(q)
        best = max(best, HQ[q]["flat"] + PAD_SKIRT * 0.75 - math.hypot(x - px, z - pz))
    return best + 7.0 * (fbm(x / 42.0, z / 42.0, 105) - 0.5)


def zone_of(x, z):
    """O, U or D: whose side of the island a point is on (the middle band is the Unorthodox's)."""
    if x > 78 + 10 * (fbm(x / 30.0, z / 30.0, 107) - 0.5):
        return "O"
    if x < -78 + 10 * (fbm(x / 30.0, z / 30.0, 109) - 0.5):
        return "D"
    return "U"


def comp_fields(x, z):
    """Inside distance of each part of the island: the plaza, the spur, the massif, and each stair's corridor."""
    out = {"plaza": PLAZA_R - math.hypot(x, z) + 1.6 * (fbm(x / 22.0, z / 22.0, 31) - 0.5)}
    out["spur"] = (SPUR_HALF - abs(x)) if SPUR_FROM <= z <= SPUR_TO + 8 else -1.0
    out["massif"] = massif_inside(x, z)
    for f in ORDER:
        s, u = su(f, x, z)
        last = tiers(f)[-1][2]
        out["stair_" + f] = (LANDING_HALF - abs(u)) if (tiers(f)[0][1] - 14.0 <= s <= last + 2.0) else -1.0
    return out


def corridor_half(kind):
    return STAIR_HALF + 2.0 if kind == "flight" else LANDING_HALF


def base_height(x, z):
    """The ground's own height before the stairs, pads and paths: the foothill or the mountain, smoothed over a few studs."""
    total = 0.0
    for dx, dz in ((0, 0), (5, 0), (-5, 0), (0, 5), (0, -5)):
        mh, mz = mountain_height(x + dx, z + dz)
        total += max(foothill(x + dx, z + dz), mh)
    return total / 5.0


def ravine_mask(x, z):
    m = 0.0
    for cx, cz, hx, hz, depth in RAVINES:
        mx = 1.0 - smoothstep(hx - 2.0, hx + 1.0, abs(x - cx))
        mz = 1.0 - smoothstep(hz - 2.0, hz + 1.0, abs(z - cz))
        m = max(m, mx * mz)
    return m


_HEIGHTS = {}


def knot_height(knot):
    x, z, h = knot
    if h is not None:
        return h
    key = (x, z)
    if key not in _HEIGHTS:
        _HEIGHTS[key] = base_height(x, z) + 1.0
    return _HEIGHTS[key]


def path_segments():
    if "segs" not in _HEIGHTS:
        segs = []
        for knots in PATHS:
            for k0, k1 in zip(knots, knots[1:]):
                x0, z0, h0, x1, z1, h1 = k0[0], k0[1], knot_height(k0), k1[0], k1[1], knot_height(k1)
                segs.append((x0, z0, h0, x1, z1, h1, min(x0, x1) - 8, max(x0, x1) + 8, min(z0, z1) - 8, max(z0, z1) + 8))
        _HEIGHTS["segs"] = segs
    return _HEIGHTS["segs"]


def path_state(x, z):
    """(mask, height) of the hidden paths and their lookouts at a point: mask 1 on a path (or a lookout), falling to 0 over 4 studs."""
    best_mask, best_h = 0.0, 0.0
    for x0, z0, h0, x1, z1, h1, bx0, bx1, bz0, bz1 in path_segments():
        if x < bx0 or x > bx1 or z < bz0 or z > bz1:
            continue
        vx, vz = x1 - x0, z1 - z0
        L2 = vx * vx + vz * vz
        t = max(0.0, min(1.0, ((x - x0) * vx + (z - z0) * vz) / L2))
        d = math.hypot(x - (x0 + vx * t), z - (z0 + vz * t))
        m = 1.0 - smoothstep(PATH_HALF, PATH_HALF + 4.0, d)
        if m > best_mask:
            best_mask, best_h = m, lerp(h0, h1, t)
    for nx, nz, nr in NOOKS:
        if abs(x - nx) > nr + 5 or abs(z - nz) > nr + 5:
            continue
        m = 1.0 - smoothstep(nr, nr + 4.0, math.hypot(x - nx, z - nz))
        if m > best_mask:
            best_mask, best_h = m, knot_height((nx, nz, None))
    return best_mask, best_h


def ground(x, z):
    """(height over Y 200, details) of the ground at a point, or (None, None) off the island: the plaza, the foothill and mountains, then
    the stairways, the pads and the hidden paths laid over them."""
    f = comp_fields(x, z)
    if max(f.values()) <= 0:
        return None, None
    h = None
    if f["plaza"] > 0:
        h = -PLAZA_DROP * (1.0 - smoothstep(0.0, PLAZA_LIP, f["plaza"]))
    if f["spur"] > 0:
        v = -3.0 * (1.0 - smoothstep(0.0, 3.0, f["spur"]))
        h = v if h is None else max(h, v)
    mh, mz = mountain_height(x, z)
    if f["massif"] > 0:
        # the massif's very edge falls away a little (the mountains keep their height up to their cliffs)
        v = max(foothill(x, z), mh) - 2.5 * (1.0 - smoothstep(0.0, 6.0, f["massif"]))
        h = v if h is None else max(h, v)
    detail = {"fields": f, "zone": mz or zone_of(x, z), "mountain": mh}
    for q in ORDER:                      # the stairways
        s, u = su(q, x, z)
        s0 = tiers(q)[0][1]
        kind = stair_kind(q, s)
        if kind in ("flight", "landing") or (kind == "plaza" and s > s0 - 14.0):
            half = corridor_half("flight" if kind == "plaza" else kind)
            m = 1.0 - smoothstep(half, half + 8.0, abs(u))
            if kind == "plaza":
                m *= smoothstep(s0 - 14.0, s0, s)
            if m > 0:
                line = stair_line(q, s) - (UNDER_STEP if kind == "flight" else 0.0)
                h = line if h is None else lerp(h, line, m)
                detail["stair"] = (q, kind, m)
    for q in ORDER:                      # the pads
        px, pz = pad_centre(q)
        rho = math.hypot(x - px, z - pz) + 2.0 * (fbm(x / 18.0, z / 18.0, 51) - 0.5)
        flat = HQ[q]["flat"]
        m = 1.0 - smoothstep(flat, flat + PAD_SKIRT, rho)
        if m > 0:
            h = lerp(h if h is not None else foothill(x, z), HQ[q]["pad_h"], m)
            detail["pad"] = (q, rho, m)
    rm = ravine_mask(x, z)               # the ravines
    if rm > 0 and f["massif"] > 0 and h is not None:
        h -= rm * max(r[4] for r in RAVINES)
        detail["ravine"] = rm
    pm, ph = path_state(x, z)            # the hidden paths
    if pm > 0 and f["massif"] > 0:
        h = ph if h is None else lerp(h, ph, pm)
        detail["path"] = pm
    return h, detail


def ground_h(x, z):
    h, d = ground(x, z)
    return 0.0 if h is None else h


# ---------- surface materials ----------
def surface(x, z, slope, d):
    """The terrain material at a column: by what it is (path, pad, stair, plaza) or by whose side of the island it is and how steep."""
    n = fbm(x / 11.0, z / 11.0, 71)
    n2 = fbm(x / 6.0, z / 6.0, 73)
    f = d["fields"]
    zone = d["zone"]
    if d.get("path", 0) > 0.5:
        return "Mud" if n > 0.7 else "Ground"
    if "pad" in d and d["pad"][2] > 0.5:
        q, rho, m = d["pad"]
        flat = HQ[q]["flat"]
        if q == "Orthodox":
            return "Limestone" if rho < flat - 8 else ("Grass" if rho < flat + 4 else "Rock")
        if q == "Unorthodox":
            if rho >= flat + 3:
                return "Sandstone" if n > 0.5 else "LeafyGrass"
            return "Mud" if n > 0.78 else ("Ground" if n > 0.64 else "LeafyGrass")
        if n2 > 0.66 and rho > flat + 2:
            return "CrackedLava"
        return "Asphalt" if n > 0.62 else "Slate"
    if "stair" in d and d["stair"][2] > 0.5:
        q, kind, m = d["stair"]
        if kind == "landing":
            return {"Orthodox": "Pavement", "Unorthodox": "Ground", "Demonic": "Slate"}[q]
        return {"Orthodox": "Limestone", "Unorthodox": "Rock", "Demonic": "Slate"}[q]
    if f["plaza"] > 0:
        r = math.hypot(x, z)
        if f["plaza"] < 2.0:
            return "Rock"
        for q in ("Unorthodox", "Demonic"):     # a wedge of each of these factions' own ground in front of its stairs
            s, u = su(q, x, z)
            if s > 40 and abs(u) < 30 and r > 38:
                if q == "Unorthodox":
                    return "Mud" if n > 0.74 else "Ground"
                return "Asphalt" if n > 0.66 else "Slate"
        if r < 12.0 or 30.0 <= r < 33.0 or 52.0 <= r < 54.0:
            return "Limestone"
        return "Pavement"
    if f["spur"] > 0 and f["massif"] <= 0:
        return "Rock" if f["spur"] < 2.0 else ("Pavement" if abs(x) > 19.0 else "Limestone")
    if zone == "O":                              # the massif and the mountains
        if slope > 0.85:
            return "Limestone" if n > 0.35 else "Rock"
        return "Grass"
    if zone == "U":
        if slope > 0.8:
            return "Sandstone" if n > 0.3 else "Rock"
        return "LeafyGrass" if n > 0.28 else "Ground"
    if slope > 1.5 and n2 > 0.72:
        return "CrackedLava"                     # the jagged ridges glow in their cracks (nothing is built on them)
    if slope > 0.7:
        return "Basalt"
    return "Asphalt" if n > 0.64 else "Slate"


def bottom(x, z, d):
    """How deep the rock underside reaches at this column (negative, over Y 200): a bowl under the plaza, a keel under the spur, a cone
    under the massif and under every mountain, ridged by noise; never past DEEPEST."""
    f = d["fields"]
    depth = 6.0
    r = math.hypot(x, z)
    if f["plaza"] > -6:
        depth = max(depth, 6.0 + 66.0 * max(0.0, 1.0 - (r / (PLAZA_R + 6)) ** 1.7))
    if f["spur"] > -1:
        depth = max(depth, 6.0 + 9.0 * max(0.0, 1.0 - (x / SPUR_HALF) ** 2))
    for cx, cz, a, b in MASSIF:
        q = math.hypot((x - cx) / a, (z - cz) / b)
        if q < 1.08:
            depth = max(depth, 8.0 + 78.0 * max(0.0, 1.0 - (q / 1.08) ** 1.25))
    for z_, cx, cz, R, H, style in MOUNTAINS:
        q = math.hypot(x - cx, z - cz) / R
        if q < 1.0:
            depth = max(depth, 8.0 + 70.0 * (1.0 - q ** 1.2))
    e = max(0.0, max(f.values()))
    depth += 9.0 * (fbm(x / 30.0, z / 30.0, 81) - 0.45) * smoothstep(0, 28, e)
    return -max(6.0, min(DEEPEST, depth))


def underside_owner(d):
    f = d["fields"]
    if f["massif"] > 0 or f["stair_Orthodox"] > 0 or f["stair_Unorthodox"] > 0 or f["stair_Demonic"] > 0:
        return d["zone"]
    return None


# ---------- the grid ----------
_CACHE = {}


def grid():
    corners = [(-380.0, -140.0), (380.0, -140.0), (-380.0, 520.0), (380.0, 520.0)]
    pts = [to_world(x, z) for x, z in corners]
    xs, zs = [p[0] for p in pts], [p[1] for p in pts]
    ox = math.floor(min(xs) / CELL) * CELL - CELL
    oz = math.floor(min(zs) / CELL) * CELL - CELL
    n = int(math.ceil(max(max(xs) - ox, max(zs) - oz) / CELL)) + 2
    return ox, oz, n


def sample_grid():
    if "grid" in _CACHE:
        return _CACHE["grid"]
    ox, oz, n = grid()
    H, D, X = [], [], []
    for j in range(n):
        for i in range(n):
            wx, wz = ox + (i + 0.5) * CELL, oz + (j + 0.5) * CELL
            x, z = to_local(wx, wz)
            h, d = ground(x, z)
            H.append(h); D.append(d); X.append((x, z))
    M, B, U = [], [], []
    for j in range(n):
        for i in range(n):
            k = j * n + i
            if H[k] is None:
                M.append(0); B.append(None); U.append(0)
                continue
            slope = 0.0
            if 0 < i < n - 1 and 0 < j < n - 1:
                nb = [H[k + 1], H[k - 1], H[k + n], H[k - n]]
                nb = [v if v is not None else H[k] - 20.0 for v in nb]    # beside the outline the ground drops away: steep
                slope = max(abs(nb[0] - nb[1]), abs(nb[2] - nb[3])) / (2 * CELL)
            x, z = X[k]
            m = surface(x, z, slope, D[k])
            M.append(MI[m]); B.append(bottom(x, z, D[k]))
            rock, strata = UNDERSIDE[underside_owner(D[k])]
            U.append(MI[rock] * 100 + MI[strata])
    _CACHE["grid"] = (ox, oz, n, H, M, B, U)
    return _CACHE["grid"]


# ---------- anchors (everything a headquarters phase builds on) ----------
def axis_point(f, s, u=0.0):
    """Local x, z of the point s along a stair's axis and u across it (toward +X)."""
    a = math.radians(HQ[f]["angle"])
    return s * math.sin(a) + u * math.cos(a), s * math.cos(a) - u * math.sin(a)


def pad_point(f, along, across=0.0):
    """A point on a pad: `along` studs from its middle toward its back (away from the plaza), `across` studs to its right when looking out
    from the plaza."""
    px, pz = pad_centre(f)
    a = math.radians(HQ[f]["angle"])
    dx, dz = math.sin(a), math.cos(a)
    return px + dx * along + dz * across, pz + dz * along - dx * across


def yaw_facing(vx, vz):
    """Y rotation (CFrame.Angles(0, yaw, 0)) that turns a model's front (-Z) toward the horizontal direction (vx, vz)."""
    return math.atan2(-vx, -vz)


def anchors():
    a = {"Plaza": {"Centre": (0.0, 0.0), "Radius": PLAZA_R, "OathStone": (0.0, 0.0), "OathYaw": 0.0},
         "Gate": {"Position": (0.0, GATE_Z), "Yaw": 0.0}, "Arrival": ARRIVAL, "Spur": (SPUR_FROM, SPUR_TO, SPUR_HALF),
         "Checkpoint": {"Position": (0.0, -30.0), "Yaw": math.pi}, "Stairs": {}, "Pads": {}, "Reps": {}, "Banners": {}}
    for f in ORDER:
        dx, dz = direction(f)
        info = HQ[f]
        yaw_to_plaza = yaw_facing(-dx, -dz)       # facing back down the stairs
        yaw_out = yaw_facing(dx, dz)              # facing up them
        px, pz = pad_centre(f)
        last = tiers(f)[-1]
        a["Stairs"][f] = {"Axis": (dx, dz), "Tiers": tiers(f), "Width": 2 * STAIR_HALF, "LandingWidth": 2 * LANDING_HALF,
                          "Top": axis_point(f, last[2]), "TopHeight": last[4], "Yaw": yaw_out}
        pad = {"Centre": (px, pz), "Height": info["pad_h"], "FlatRadius": info["flat"], "EdgeRadius": info["flat"] + PAD_SKIRT,
               "Front": (-dx, -dz), "FrontYaw": yaw_to_plaza,
               "Gate": {"Position": axis_point(f, last[2] + 6.0), "Yaw": yaw_out},
               "MainHall": {"Position": pad_point(f, 16.0), "Yaw": yaw_to_plaza},
               "Vault": {"Position": pad_point(f, 22.0, 38.0), "Yaw": yaw_to_plaza},
               "Checkpoint": {"Position": axis_point(f, last[2] + 6.0), "Yaw": yaw_out}}
        if f == "Orthodox":      # five gates up the ceremonial stair, from the plaza's edge to the pad
            pad["Trial"] = {"Gates": [axis_point(f, s) for s in (84.0, 104.0, 124.0, 138.0, 150.0)]}
        elif f == "Unorthodox":  # places a token may be hidden: the four lookouts and two nooks on the pad's rim
            pad["Trial"] = {"TokenSpots": [(n[0], n[1]) for n in NOOKS] + [pad_point(f, 52.0, 24.0), pad_point(f, 52.0, -24.0)]}
        else:                    # the arena's middle and the three places each wave comes from
            pad["Trial"] = {"Arena": pad_point(f, -2.0), "Waves": [pad_point(f, -2.0 + 26.0 * math.cos(math.radians(90 + 120 * k)), 26.0 * math.sin(math.radians(90 + 120 * k))) for k in range(3)]}
        a["Pads"][f] = pad
        a["Reps"][f] = {"Position": axis_point(f, REP_S), "Yaw": yaw_to_plaza}
        a["Banners"][f] = {"Position": axis_point(f, BANNER_S, BANNER_U), "Yaw": 0.0}
    return a


# ---------- placed things: trees and so on, each at the ground's own height ----------
def free_spot(x, z, pad_margin):
    """The ground (height, details) at a point if something may stand there: off the plaza, the spur, every stair, pad and path."""
    h, d = ground(x, z)
    if h is None:
        return None
    f = d["fields"]
    if f["plaza"] > -6 or f["spur"] > 0:
        return None
    for q in ORDER:
        s, u = su(q, x, z)
        if tiers(q)[0][1] - 20 <= s <= tiers(q)[-1][2] + 6 and abs(u) < LANDING_HALF + 8:
            return None
        px, pz = pad_centre(q)
        if math.hypot(x - px, z - pz) < HQ[q]["flat"] + pad_margin:
            return None
    if path_state(x, z)[0] > 0.02:
        return None
    for nx, nz, nr in NOOKS:
        if math.hypot(x - nx, z - nz) < nr + 8:
            return None
    return h, d


def scatter(zone, count, spacing, seed, region, max_slope, pad_margin):
    """Up to `count` places on `zone`'s ground inside region (x0, x1, z0, z1), at least `spacing` apart, on gentle ground: (x, z, h, yaw)."""
    x0, x1, z0, z1 = region
    out = []
    for tries in range(1, 6000):
        if len(out) >= count:
            break
        x = x0 + (x1 - x0) * BL._hash(tries, 3, seed)
        z = z0 + (z1 - z0) * BL._hash(tries, 5, seed + 1)
        got = free_spot(x, z, pad_margin)
        if not got or got[1]["zone"] != zone:
            continue
        h = got[0]
        if math.hypot(ground_h(x + 3, z) - ground_h(x - 3, z), ground_h(x, z + 3) - ground_h(x, z - 3)) / 6.0 > max_slope:
            continue
        if min([math.hypot(x - o[0], z - o[1]) for o in out] or [1e9]) < spacing:
            continue
        out.append((x, z, h, BL._hash(tries, 7, seed + 2) * 6.283))
    return out


def placed():
    """Everything the builder places that depends on the ground's height."""
    if "placed" in _CACHE:
        return _CACHE["placed"]
    trees_o = scatter("O", 24, 15.0, 211, (50.0, 330.0, 20.0, 330.0), 0.55, 4.0)
    trees_u = scatter("U", 32, 12.0, 223, (-125.0, 125.0, 30.0, 400.0), 0.65, 4.0)
    rocks_d = scatter("D", 20, 18.0, 233, (-330.0, -60.0, 40.0, 340.0), 0.9, -10.0)
    falls = []
    # waterfalls: where a mesa's rim faces the plaza: (zone, mesa index, bearing from its middle) -> lip and the point behind it
    for zone, idx, bearing in (("O", 0, -150.0), ("O", 2, -125.0), ("U", 3, -90.0)):
        z_, cx, cz, R, H, style = MOUNTAINS[idx]
        ang = math.radians(bearing)
        rr = 0.58
        while rr > 0.36:
            lx, lz = cx + math.cos(ang) * R * rr, cz + math.sin(ang) * R * rr
            if ground_h(lx, lz) > H * 0.82:
                break
            rr -= 0.02
        bx, bz = cx + math.cos(ang) * R * (rr - 0.1), cz + math.sin(ang) * R * (rr - 0.1)
        falls.append({"Zone": zone, "Lip": (lx, lz, ground_h(lx, lz)), "From": (bx, bz, ground_h(bx, bz))})
    _CACHE["placed"] = {"TreesO": trees_o, "TreesU": trees_u, "RocksD": rocks_d, "Falls": falls}
    return _CACHE["placed"]


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
    ox, oz, n, H, M, B, U = sample_grid()
    cells = sum(1 for v in H if v is not None)
    mine = boundary_world(H, n, ox, oz)
    clear = {}
    for name, info in LAYOUT.ISLANDS.items():
        if name == ISLAND:
            continue
        cx, _, cz = info["centre"]
        r = 248.0 if name == "Yggdrasil" else float(info["radius"])
        clear[name] = round(min(math.hypot(wx - cx, wz - cz) for wx, wz in mine) - r)
    bb = blossom_boundary()
    clear["BlossomSanctuary"] = round(min(math.hypot(wx - bx, wz - bz) for wx, wz in mine[::2] for bx, bz in bb[::2]))
    lows = [b for b in B if b is not None]
    highs = [h for h in H if h is not None]
    start, end = LAYOUT.BRIDGES["MurimRoute"]["start"], LAYOUT.BRIDGES["MurimRoute"]["end"]
    level = {}
    for q in ORDER:                      # how level each pad's flat disc is (sampled)
        px, pz = pad_centre(q)
        worst = 0.0
        for k in range(0, 360, 10):
            for rr in (0.0, 20.0, 40.0, HQ[q]["flat"] - 2.0):
                worst = max(worst, abs(ground_h(px + math.cos(math.radians(k)) * rr, pz + math.sin(math.radians(k)) * rr) - HQ[q]["pad_h"]))
        level[q] = round(worst, 2)
    voxels = sum(max(1, int(math.ceil((h - b) / 4.0))) for h, b in zip(H, B) if h is not None)
    walk = max([math.hypot(*pad_centre(q)) + HQ[q]["flat"] for q in ORDER] + [math.hypot(nx, nz) for nx, nz, nr in NOOKS])
    return {
        "grid": {"origin": (ox, oz), "size": n, "cells": cells},
        "area_sq_studs": cells * CELL * CELL, "blossom_sq_studs": 175728, "origin_abyss_disc_sq_studs": round(math.pi * 165 ** 2),
        "highest_ground_over_plaza": round(max(highs), 1), "deepest_underside": round(min(lows), 1), "voxels": voxels,
        "turns": TURNS, "yaw_deg": round(math.degrees(YAW), 2), "centre": CENTRE, "hub_to_centre": round(math.hypot(CENTRE[0], CENTRE[2])),
        "bridge": {"start": start, "end": end, "flat_length": round(LAYOUT.flat(start, end)), "nodes": len(LAYOUT.bridge_nodes("MurimRoute")) - 1},
        "clearance_to_islands_ground_to_ground": clear, "pads_level_worst_deviation": level, "walkable_reach_from_plaza": round(walk),
    }


# ---------- writing ----------
def encode(values, off, fmt):
    """A run-length string for the data module: values joined by commas, `~N` for N entries of `off` (the grid is mostly sky)."""
    out, run = [], 0
    for v in values:
        if v == off:
            run += 1
            continue
        if run:
            out.append("~%d" % run)
            run = 0
        out.append(fmt % v)
    if run:
        out.append("~%d" % run)
    return ",".join(out)


def write_terrain(path):
    ox, oz, n, H, M, B, U = sample_grid()

    def chunk(name, text, comment=None):
        out = []
        if comment:
            out += ["    -- " + c for c in comment]
        out.append('    %s = "%s",' % (name, text))
        return out
    lines = [
        "-- Written by tools/blender/world/murim_layout.py (Murim Crossing, 2026-11-22). Do not edit by hand.",
        "-- The arrays are run-length strings (WorldBuilder.terrainData expands them): values joined by commas, ~N for N empty columns.",
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
    lines += chunk("Heights", encode(H, None, "%.1f"))
    lines += chunk("MaterialIndex", encode(M, 0, "%d"))
    lines += chunk("Bottoms", encode([None if v is None else round(v) for v in B], None, "%d"),
                   ["how deep the rock underside reaches under each column (over Centre.Y)"])
    lines += chunk("UndersideIndex", encode(U, 0, "%d"),
                   ["what the underside is made of: rock * 100 + the strata bands' material (Materials indices): pale limestone under the Orthodox side,",
                    "sandstone and rock under the Unorthodox, black slate and basalt under the Demonic"])
    lines += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return n, sum(1 for h in H if h is not None)


def v3(x, y, z):
    return "Vector3.new(%.2f, %.2f, %.2f)" % (x, y, z)


def p3(p, y):
    return v3(p[0], y, p[1])


def pg(p):
    return v3(p[0], ground_h(p[0], p[1]), p[1])


def write_placements(path):
    a = anchors()
    pl = placed()
    L = ["-- Written by tools/blender/world/murim_layout.py (Murim Crossing, 2026-11-22). Do not edit by hand.",
         "-- Island-local Roblox studs (local -Z faces the hub, +X is the LEFT of whoever has just arrived: the Orthodox side), Y 0 = the plaza's ground",
         "-- (world Y 200). Read by CrossingBuilder (the plaza, the gate, the stairs, the banners, the representatives, the zones, the dressing) and,",
         "-- later, by each headquarters' build. Yaw: CFrame.Angles(0, Yaw, 0) in the island's frame turns a model's front (-Z) the way it says.",
         "-- Pads: Height is the pad's level over the plaza, Front the unit vector toward the plaza (a headquarters' main hall faces it), Gate the pad's",
         "-- entrance just past the stair's top, FlatRadius how far from Centre the ground is exactly level; the pad's own materials are",
         "-- Limestone/Grass (Orthodox), LeafyGrass/Mud/Ground/Sandstone (Unorthodox) and Slate/Asphalt (Demonic): never lay a floor on Grass (its blades",
         "-- come up through it) and keep Basalt/CrackedLava (they bump) to ground nothing is built on.",
         "return {",
         "    Reach = 340, -- how far from the plaza's middle the walkable ground runs (the mountains behind it are scenery)",
         "    Plaza = { Centre = %s, Radius = %.1f, OathStone = %s, OathYaw = %.4f }," % (p3(a["Plaza"]["Centre"], 0), PLAZA_R, p3(a["Plaza"]["OathStone"], 0), a["Plaza"]["OathYaw"]),
         "    Gate = { Position = %s, Yaw = %.4f }, -- the island's own gate, across the end of the bridge" % (p3(a["Gate"]["Position"], 0), a["Gate"]["Yaw"]),
         "    Arrival = %s, -- where the bridge's last deck node lands" % v3(ARRIVAL[0], 0, ARRIVAL[2]),
         "    Spur = { FromZ = %.1f, ToZ = %.1f, Half = %.1f }," % (SPUR_FROM, SPUR_TO, SPUR_HALF),
         "    Checkpoint = { Position = %s, Yaw = %.4f }, -- where a fall from the island returns to: the plaza, facing the oath stone" % (p3(a["Checkpoint"]["Position"], 0), a["Checkpoint"]["Yaw"]),
         "    Order = { \"Orthodox\", \"Unorthodox\", \"Demonic\" },",
         "    StepRise = %.1f, StairHalf = %.1f, LandingHalf = %.1f, UnderStep = %.1f," % (STEP_RISE, STAIR_HALF, LANDING_HALF, UNDER_STEP)]
    L.append("    Stairs = { -- each headquarters' stairway: its axis (a unit vector from the plaza's middle), its tiers as { Kind, S0, S1, H0, H1 } (S along the axis)")
    for f in ORDER:
        st = a["Stairs"][f]
        tiers_lua = ", ".join('{ "%s", %.1f, %.1f, %.1f, %.1f }' % t for t in st["Tiers"])
        L.append("        %s = { Axis = Vector3.new(%.4f, 0, %.4f), Yaw = %.4f, Width = %.1f, LandingWidth = %.1f, Top = %s, Tiers = { %s } }," % (
            f, st["Axis"][0], st["Axis"][1], st["Yaw"], st["Width"], st["LandingWidth"], p3(st["Top"], st["TopHeight"]), tiers_lua))
    L.append("    },")
    L.append("    Reps = { -- each faction's representative stands on the plaza in front of its stairs, facing the oath stone")
    for f in ORDER:
        L.append("        %s = { Position = %s, Yaw = %.4f }," % (f, p3(a["Reps"][f]["Position"], 0), a["Reps"][f]["Yaw"]))
    L.append("    },")
    L.append("    Banners = { -- a tall pole at the foot of each stairway")
    for f in ORDER:
        L.append("        %s = { Position = %s, Yaw = %.4f }," % (f, p3(a["Banners"][f]["Position"], 0), a["Banners"][f]["Yaw"]))
    L.append("    },")
    L.append("    Pads = {")
    for f in ORDER:
        p = a["Pads"][f]
        h = p["Height"]
        L.append("        %s = {" % f)
        L.append("            Centre = %s, Height = %.1f, FlatRadius = %.1f, EdgeRadius = %.1f," % (p3(p["Centre"], h), h, p["FlatRadius"], p["EdgeRadius"]))
        L.append("            Front = Vector3.new(%.4f, 0, %.4f), FrontYaw = %.4f," % (p["Front"][0], p["Front"][1], p["FrontYaw"]))
        for key in ("Gate", "MainHall", "Vault", "Checkpoint"):
            L.append("            %s = { Position = %s, Yaw = %.4f }," % (key, pg(p[key]["Position"]), p[key]["Yaw"]))
        for key, val in p["Trial"].items():
            if isinstance(val, list):
                L.append("            Trial%s = { %s }," % (key, ", ".join(pg(q) for q in val)))
            else:
                L.append("            Trial%s = %s," % (key, pg(val)))
        L.append("        },")
    L.append("    },")
    L.append("    Nooks = { -- the Unorthodox side's hidden lookouts, each at the end of a hidden path")
    L.append("        " + ", ".join(v3(n[0], knot_height((n[0], n[1], None)), n[1]) for n in NOOKS) + ",")
    L.append("    },")
    L.append("    Paths = { -- those paths, as knots")
    for knots in PATHS:
        L.append("        { " + ", ".join(v3(k[0], knot_height(k), k[1]) for k in knots) + " },")
    L.append("    },")
    L.append("    RopeBridges = { -- rope and timber bridges across the Unorthodox side's ravines: the two rims")
    for a_, b_ in ROPE_BRIDGES:
        L.append("        { From = %s, To = %s }," % (v3(a_[0], knot_height((a_[0], a_[1], None)), a_[1]), v3(b_[0], knot_height((b_[0], b_[1], None)), b_[1])))
    L.append("    },")
    L.append("    Dress = { -- trees and rocks, each at the ground's own height: position, yaw")
    for key in ("TreesO", "TreesU", "RocksD"):
        L.append("        %s = { %s }," % (key, ", ".join("{ %s, %.3f }" % (v3(x, h, z), yaw) for x, z, h, yaw in pl[key])))
    L.append("    },")
    L.append("    Falls = { -- where a waterfall pours off a mesa's rim: the lip and the point behind it")
    for fl in pl["Falls"]:
        L.append('        { Zone = "%s", Lip = %s, From = %s },' % (fl["Zone"], v3(fl["Lip"][0], fl["Lip"][2], fl["Lip"][1]), v3(fl["From"][0], fl["From"][2], fl["From"][1])))
    L.append("    },")
    # the blood moon: far behind the Demonic side, high, tied to the island (a part in its model; it lights nothing)
    L.append("    Moon = { Position = Vector3.new(-230.00, 330.00, 640.00), Radius = 70.0 }, -- behind and over the Demonic mountains")
    L += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(L))
    return 1


# ---------- the sketch ----------
COL = {"Limestone": (214, 214, 226), "Grass": (104, 160, 86), "Pavement": (176, 180, 198), "Ground": (128, 100, 74), "Mud": (86, 68, 50),
       "LeafyGrass": (70, 122, 62), "Rock": (120, 122, 130), "Slate": (60, 58, 72), "Asphalt": (70, 64, 64), "Basalt": (44, 40, 42),
       "CrackedLava": (255, 110, 40), "Sandstone": (98, 124, 108)}


def sketch(path):
    ox, oz, n, H, M, B, U = sample_grid()
    S = 1.0
    X0, X1, Z0, Z1 = -380.0, 380.0, -150.0, 520.0
    w, h = int((X1 - X0) * S), int((Z1 - Z0) * S)
    px = bytearray(w * h * 3)
    sky = (34, 40, 56)
    for j in range(h):
        z = Z1 - (j + 0.5) / S
        for i in range(w):
            x = X1 - (i + 0.5) / S               # seen from above: local -Z (the hub) at the bottom, +X on the left
            wx, wz = to_world(x, z)
            ci, cj = int((wx - ox) // CELL), int((wz - oz) // CELL)
            c = sky
            if 0 <= ci < n and 0 <= cj < n and H[cj * n + ci] is not None:
                k = cj * n + ci
                shade = 0.62 + 0.0042 * H[k]
                c = tuple(min(255, int(v * shade)) for v in COL[MATERIALS[M[k] - 1]])
            kk = (j * w + i) * 3
            px[kk:kk + 3] = bytes(c)

    def put(x, z, c):
        i, j = int((X1 - x) * S), int((Z1 - z) * S)
        if 0 <= i < w and 0 <= j < h:
            kk = (j * w + i) * 3
            px[kk:kk + 3] = bytes(c)

    def disc(x, z, r, c):
        for dz in range(int(-r * S) - 1, int(r * S) + 2):
            for dx in range(int(-r * S) - 1, int(r * S) + 2):
                if math.hypot(dx, dz) / S <= r:
                    put(x + dx / S, z + dz / S, c)
    FC = {"Orthodox": (96, 168, 255), "Unorthodox": (70, 200, 150), "Demonic": (226, 52, 48)}
    a = anchors()
    disc(0, GATE_Z, 2.5, (255, 220, 120))
    disc(0, 0, 3.5, (255, 255, 255))
    for t in range(0, 70):
        for s_ in range(-20, 21, 2):
            put(s_, ARRIVAL[2] - 70 + t, (236, 228, 210))
    for f in ORDER:
        disc(*a["Reps"][f]["Position"], 3.0, FC[f])
        disc(*a["Banners"][f]["Position"], 2.0, FC[f])
        disc(*a["Pads"][f]["Gate"]["Position"], 2.5, (255, 220, 120))
        disc(*a["Pads"][f]["Centre"], 3.0, FC[f])
        for q in a["Pads"][f]["Trial"].values():
            for p in (q if isinstance(q, list) else [q]):
                disc(*p, 1.6, FC[f])
    for nx, nz, nr in NOOKS:
        disc(nx, nz, 3.0, (255, 255, 120))
    for fl in placed()["Falls"]:
        disc(fl["Lip"][0], fl["Lip"][1], 2.5, (120, 200, 255))
    write_png(path, w, h, px)
    return w, h


write_png = BL.write_png


def verify(r):
    """The layout's rules, each printed as OK or BAD (a BAD ends the run with an error)."""
    rules = [
        ("every pad is level over its whole flat disc (within 0.1 stud)", max(r["pads_level_worst_deviation"].values()) <= 0.1),
        ("every other island is at least 100 studs of open sky away", min(r["clearance_to_islands_ground_to_ground"].values()) >= 100),
        ("the bridge is one span of 200 to 280 studs", 200 <= r["bridge"]["flat_length"] <= 280),
        ("the underside stays above the 110-stud fall line", r["deepest_underside"] > -105),
        ("its ground is no bigger than the Blossom Sanctuary's", r["area_sq_studs"] <= r["blossom_sq_studs"]),
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
