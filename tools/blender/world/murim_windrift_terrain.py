"""Windrift Hold's land: the Unorthodox side's terrain override of Murim Crossing (2026-11-23). Plain Python (no Blender).

murim_layout.py calls this module from its ground / surface / bottom / placed functions (as it calls Dawnspire's murim_dawnspire_terrain.py). Everything
here is declared in WINDRIFT'S PAD FRAME: origin at the Unorthodox pad's centre (island-local x 0, z 250), x = island-local x (to the LEFT of someone who has
just arrived), +z away from the plaza (up the mountain, toward the cliff), y over the plaza's ground (the pad is 36). The pad's FrontYaw is 0, so this frame
is the island frame shifted by 250 in z (Placements/MurimWindrift.lua puts the pad's centre, lifted 0.5, at its origin).

The terrain changes ONLY inside REGION (the pad and its skirt, and the cliff foot behind it) and never inside PROTECTED (the stair, the gate, the two hidden
lookouts at the front and their paths, the ravines with their rope bridges and the paths that end at them). `override` returns its input unchanged
everywhere else, and WINDRIFT_TERRAIN=0 (the environment) makes that true everywhere so the old data can be regenerated to prove it
(tools/blender/world/windrift_terrain_diff.py).

What the override makes (levels are heights over the plaza; every floor mesh lies 0.5 over its terrain):
    the Gorge        a slot of open sky cut through the pad behind its middle (x 3..16, z 8..68), ending in the cliff: the Great Falls pour into its rear end,
                     a hall straddles it, a footbridge crosses it, a stair hangs in it
    the Drip Ledge   a shelf in the gorge (24), a stair's landing under the hall
    the Eyrie        a ledge cut into the cliff to the right of the falls (58): the Elder's house; a stair climbs to it from the pad
    the Perch        a ledge cut into the cliff to the left of the falls (52): the bell perch, reached by the long bridge from the Eyrie (and by flying)
The pad itself keeps its height (36): the buildings stand on it, and under them the ground is repaved (Sandstone and Ground, never Grass).
Reach (Placements/MurimCrossing.lua, 340 from the plaza's middle): every walkable point of the new ground is within it (the farthest is the Eyrie's back
corner, 334).
"""
import math
import os

import blossom_layout as BL

ENABLED = os.environ.get("WINDRIFT_TERRAIN", "1") != "0"
smoothstep, lerp, fbm = BL.smoothstep, BL.lerp, BL.fbm

PAD_C = (0.0, 250.0)       # island-local x, z of the pad's centre
Y_PAD = 36.0
FLOOR = 0.5                # a floor mesh lies this far over its terrain

# ---------- levels ----------
Y_EYRIE, Y_PERCH, Y_DRIP = 58.0, 52.0, 24.0


def to_local(x, z):
    return PAD_C[0] + x, PAD_C[1] + z


def to_pad(lx, lz):
    return lx - PAD_C[0], lz - PAD_C[1]


# ---------- the gorge: open sky ----------
SLOT = dict(x0=3.0, x1=16.0, z0=8.0, z1=72.0, r=2.0)

# ---------- terraces: flat rectangles (x0, x1, z0, z1) at a level, rounded corners; skirt = how far outside the flat the ground blends back ----------
TERRACES = {
    "Eyrie": dict(x0=-32.5, x1=-13.0, z0=61.5, z1=76.0, y=Y_EYRIE, r=3.0, skirt=3.0, mat="Sandstone"),
    "Perch": dict(x0=16.0, x1=33.0, z0=61.5, z1=75.0, y=Y_PERCH, r=2.0, skirt=3.0, skirt_max_z=72.0, skirt_max_x=20.0, mat="Sandstone"),   # (no skirt at the corner behind the gorge's rear end, z > 72 and x < 20: the mesa's rim beside the falls stays as it was; the Perch's east and rear skirt is the old one)
    "Drip": dict(x0=3.0, x1=11.0, z0=45.0, z1=53.0, y=Y_DRIP, r=1.5, skirt=2.0, mat="Rock"),
}

# ---------- open-sky cuts: rectangles (pad frame) in which every column whose centre lies inside is removed ----------
# The Great Span (deck along z 66, x -14 .. 19) runs from the Eyrie's ledge to the Perch's across the cliff foot, and the cliff stands in its way: Studio's 4-stud voxel
# columns are filled to their height, so the corridor of the span (3 studs each side of its axis, the deck top up to 6 over it) must hold no column. A column's cell is
# 4 studs square and turned 23 degrees against this frame, so one whose centre is up to 2.9 outside the corridor can still reach into it: the cut is the corridor
# plus 2.9 each side (z 60.1 .. 71.9), from 3 studs inside the Eyrie ledge's east edge (x -16: the ledge's own columns would reach 2.6 studs into the corridor) to the Gorge (x 3, where the slot's own open sky begins).
CUTS = [dict(name="SpanCut", x0=-16.0, x1=3.0, z0=60.1, z1=71.9)]

# ---------- stairs: straight runs (from (x, z) at level y0 to (x, z) at y1); a flight has one-stud risers and 1.5 treads ----------
UNDER_STEP = 1.8
UNDER_LANDING = 3.0         # a landing's stone stands 3 deep in the ground (the 4-stud columns beside a flight reach under its last steps)
STAIRS = {
    # up from the pad's right-rear to the Eyrie: a flight along the cliff foot, a landing, a flight turned back toward the ledge (22 one-stud risers)
    "Eyrie": dict(half=3.0, blend=3.0, runs=[((-46.5, 29.5), (-40.5, 44.5), 36.0, 47.0), ((-40.5, 44.5), (-37.7, 49.0), 47.0, 47.0),
                                              ((-37.7, 49.0), (-26.9, 61.5), 47.0, 58.0)]),
}

# ---------- the region: every cell this module may change ----------
REGION_R = 74.0                                   # the pad (flat 58) and its skirt (12) with a margin
REGION_BACK = (-66.0, 66.0, 30.0, 88.0)           # the cliff foot behind it (x0, x1, z0, z1)
REGION_MIN_Z = -50.0                              # the stair and the gate (island-local z 200) are never touched
# protected island-local places, each (kind, ...): a disc or a segment with a radius
PATH_PROTECT = 8.0                                 # the hidden paths' own width is 3 + a 4-stud blend: nothing within 8 of a path's centre line is changed
_SEGMENTS = []                                    # filled lazily from murim_layout.PATHS: ((x0, z0), (x1, z1), radius)


def _segments():
    if not _SEGMENTS:
        import murim_layout as M
        for knots in M.PATHS:
            for k0, k1 in zip(knots, knots[1:]):
                _SEGMENTS.append(((k0[0], k0[1]), (k1[0], k1[1]), PATH_PROTECT))
    return _SEGMENTS


def _seg_dist(x, z, a, b):
    vx, vz = b[0] - a[0], b[1] - a[1]
    L2 = vx * vx + vz * vz
    t = max(0.0, min(1.0, ((x - a[0]) * vx + (z - a[1]) * vz) / L2)) if L2 else 0.0
    return math.hypot(x - (a[0] + vx * t), z - (a[1] + vz * t))


def protected(lx, lz):
    """True where the first foundation's hidden paths, lookouts, ravines and rope bridges stand (they must keep working: never changed)."""
    import murim_layout as M
    for (a, b, r) in _segments():
        if _seg_dist(lx, lz, a, b) < r:
            return True
    for nx, nz, nr in M.NOOKS:
        if math.hypot(lx - nx, lz - nz) < nr + 12.0:
            return True
    for cx, cz, hx, hz, depth in M.RAVINES:
        if abs(lx - cx) <= hx + 7.0 and abs(lz - cz) <= hz + 7.0:
            return True
    return False


def in_region(x, z):
    if z < REGION_MIN_Z:
        return False
    if math.hypot(x, z) <= REGION_R:
        return True
    b = REGION_BACK
    return b[0] <= x <= b[1] and b[2] <= z <= b[3]


# ---------- shapes ----------
def rr_inside(x, z, x0, x1, z0, z1, r):
    """Distance inside a rounded rectangle (negative outside)."""
    cx, cz, hx, hz = (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2, (z1 - z0) / 2
    qx, qz = abs(x - cx) - (hx - r), abs(z - cz) - (hz - r)
    out = math.hypot(max(qx, 0.0), max(qz, 0.0)) + min(max(qx, qz), 0.0) - r
    return -out


def stair_runs(name):
    st = STAIRS[name]
    out = []
    for (a, b, y0, y1) in st["runs"]:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 1e-6:
            continue
        out.append(dict(a=a, b=b, y0=y0, y1=y1, L=L, dx=(b[0] - a[0]) / L, dz=(b[1] - a[1]) / L, flight=abs(y1 - y0) > 1e-6, half=st["half"], stair=name,
                        blend=st.get("blend", 3.0)))
    return out


def all_runs():
    out = []
    for name in STAIRS:
        out += stair_runs(name)
    return out


def run_state(x, z, run):
    vx, vz = x - run["a"][0], z - run["a"][1]
    return vx * run["dx"] + vz * run["dz"], -vx * run["dz"] + vz * run["dx"]


def stair_line(run, s):
    return lerp(run["y0"], run["y1"], max(0.0, min(1.0, s / run["L"])))


# ---------- paved places (terrain Sandstone / Ground under buildings, courts and walks), filled by windrift.py ----------
PAVED_RECTS = []      # (x0, x1, z0, z1): under a building's footprint
PAVED_STRIPS = []     # walks: ((x, z), (x, z), half width)
COURTS = []           # (x0, x1, z0, z1): courts of worn ground


# ---------- the terrain override ----------
def override(lx, lz, h, d):
    """Called with the unchanged ground (h, details) of an island-local point; returns the ground with Windrift's gorge, ledges and stairs laid over it."""
    if not ENABLED:
        return h, d
    x, z = to_pad(lx, lz)
    if not in_region(x, z) or protected(lx, lz):
        return h, d
    wind = None
    new_h = h
    # 1. terraces: the flat rectangle exactly, the skirt a blend back to the old ground
    best = None
    for name, t in TERRACES.items():
        din = rr_inside(x, z, t["x0"], t["x1"], t["z0"], t["z1"], t["r"])
        if din >= 0.0 and (best is None or din > best[1]):
            best = (name, din, t)
    if best:
        name, din, t = best
        new_h = t["y"]
        wind = {"terrace": name, "inside": din, "mat": t["mat"], "depth": 8.0 + 2.4 * din}
    else:
        near = None
        for name, t in TERRACES.items():
            dout = -rr_inside(x, z, t["x0"], t["x1"], t["z0"], t["z1"], t["r"])
            if dout < t["skirt"] and not (z > t.get("skirt_max_z", 1e9) and x < t.get("skirt_max_x", -1e9)) and (near is None or dout < near[1]):
                near = (name, dout, t)
        if near and h is not None:
            name, dout, t = near
            m = smoothstep(0.0, t["skirt"], dout)
            new_h = lerp(t["y"], h, m)
            wind = {"terrace": name, "inside": -dout, "mat": None, "depth": 8.0, "skirt": 1.0 - m}
    # 2. stairs: the ground under a flight dips under its steps (they stand in it)
    for run in all_runs():
        s, u = run_state(x, z, run)
        gh = run["half"] + 2.0
        if -1.0 <= s <= run["L"] + 1.0:
            m = 1.0 - smoothstep(gh, gh + run["blend"], abs(u))
            if m > 0.0:
                line = stair_line(run, s) - (UNDER_STEP if run["flight"] else UNDER_LANDING)
                if new_h is None:
                    if m >= 0.5 and abs(u) <= run["half"] + 2.0:
                        new_h = line
                        wind = {"terrace": None, "inside": 4.0, "mat": "Rock" if run["flight"] else "Ground", "depth": 10.0, "stair": run["stair"]}
                else:
                    new_h = lerp(new_h, line, m)
                    if m > 0.5:
                        wind = {"terrace": None, "inside": 4.0, "mat": "Rock" if run["flight"] else "Ground", "depth": 10.0, "stair": run["stair"]}
    # 2b. the cuts (open sky across the Great Span's corridor)
    for c in CUTS:
        if c["x0"] <= x <= c["x1"] and c["z0"] <= z <= c["z1"]:
            return None, None
    # 3. the gorge: a slot of open sky through the pad (the falls land in it; the route zones catch a fall)
    if rr_inside(x, z, SLOT["x0"], SLOT["x1"], SLOT["z0"], SLOT["z1"], SLOT["r"]) >= 0.0:
        keep = best and best[0] == "Drip"
        if not keep:
            return None, None
    # 4. paved places on the pad (the height stays, the ground under a building is repaved)
    if wind is None and h is not None and (PAVED_RECTS or PAVED_STRIPS or COURTS):
        if _paved(x, z) is not None:
            wind = {"terrace": None, "inside": 4.0, "mat": _paved(x, z), "depth": 0.0, "pave": True}
    if wind is None or new_h is None:
        return h, d
    if d is None:
        import murim_layout as M
        d = {"fields": M.comp_fields(lx, lz), "zone": "U", "mountain": 0.0}
    else:
        d = dict(d)
    d["zone"] = "U"
    d["wind"] = wind
    return new_h, d


def _paved(x, z):
    for (x0, x1, z0, z1) in PAVED_RECTS:
        if x0 <= x <= x1 and z0 <= z <= z1:
            return "Sandstone"
    for (a, b, half) in PAVED_STRIPS:
        if _seg_dist(x, z, a, b) <= half:
            return "Ground"
    for (x0, x1, z0, z1) in COURTS:
        if x0 <= x <= x1 and z0 <= z <= z1:
            return "Ground"
    return None


# ---------- surface and underside ----------
def surface(lx, lz, slope, d, base):
    """The terrain material of a column the override touched."""
    wind = d["wind"]
    mat = wind.get("mat")
    if wind.get("pave"):
        return mat
    if "stair" in wind:
        return mat
    if mat is None:                         # a skirt or a cliff: the old material by slope
        if slope > 0.8:
            return "Rock" if fbm(lx / 9.0, lz / 9.0, 61) > 0.1 else "Sandstone"
        return base
    x, z = to_pad(lx, lz)
    if slope > 1.2:
        return "Rock"
    for (a, b, half) in PAVED_STRIPS:
        if _seg_dist(x, z, a, b) <= half:
            return "Ground"
    return mat


def bottom_depth(d):
    """How deep the underside of a column the override touched reaches (a cone of rock under every ledge), or 0."""
    wind = d.get("wind") if d else None
    if not wind:
        return 0.0
    return wind["depth"]


def region_text():
    return "pad frame: radius %.0f round the pad's centre (z >= %.0f) and x %.0f..%.0f, z %.0f..%.0f behind it, minus the protected stair, lookouts, paths and ravines" % (
        REGION_R, REGION_MIN_Z, REGION_BACK[0], REGION_BACK[1], REGION_BACK[2], REGION_BACK[3])
