"""Dawnspire's terrace system: the Orthodox side's extension of Murim Crossing's terrain (2026-11-22). Plain Python (no Blender).

murim_layout.py calls this module from its ground / surface / bottom / placed functions. Everything here is declared in the HALL'S PAD FRAME (the
frame Placements/MurimOrthodox.lua and Placements/MurimDawnspire.lua use): origin at the Orthodox pad's centre, +z away from the plaza (up the
mountain, behind the hall), +x toward the island's outer edge (the player's left on arrival), y over the plaza's ground. The terrain changes ONLY
inside the region listed in REGION (island-local x of at least 92, so the Unorthodox side, the plaza, the Demonic side and the bridge are
untouched); `override` returns its input unchanged everywhere else, which DAWNSPIRE_TERRAIN=0 (the environment) makes true everywhere so the
old data can be regenerated to prove it (tools/blender/world/dawnspire_terrain_diff.py).

The terrace system (levels are heights over the plaza; every floor mesh lies 0.5 over its terrace's terrain, as the hall's court does):
    pad            16    the hall's court and flat disc (unchanged)
    garden         25    the rear garden behind the hall, level with the hall's inner court (floor 25.5): the cherry court, the pavilion, two ravine edges
    residence      43    the Master's courtyard house, up a gorge stair from the garden (two flights, a landing at 34)
    tea terrace    16    the NPC gathering area on its own shelf east of the front court, reached by an arched bridge over a gap
    training yard  20    the martial yard, up a stair from the tea terrace
    exhibition     25    the weapon exhibition hall's terrace, up a stair from the training yard, joined to the garden by an arched bridge over the ravine
The land that did not exist (the east shelves) is new rock, each terrace hanging in its own cone of limestone (`bottom`).
"""
import math
import os

import blossom_layout as BL

ENABLED = os.environ.get("DAWNSPIRE_TERRAIN", "1") != "0"
smoothstep, lerp, fbm = BL.smoothstep, BL.lerp, BL.fbm

# ---------- the pad's frame ----------
PAD_S = 206.0
PAD_ANGLE = math.radians(38.0)
PAD_C = (PAD_S * math.sin(PAD_ANGLE), PAD_S * math.cos(PAD_ANGLE))    # island-local (126.83, 162.33)
PAD_YAW = PAD_ANGLE                                                      # CFrame.Angles(0, FrontYaw, 0) of the pad's frame (0.6632)
_C, _S = math.cos(PAD_YAW), math.sin(PAD_YAW)


def to_local(x, z):
    """Pad frame (x, z) -> island-local (X, Z)."""
    return PAD_C[0] + x * _C + z * _S, PAD_C[1] - x * _S + z * _C


def to_pad(lx, lz):
    dx, dz = lx - PAD_C[0], lz - PAD_C[1]
    return dx * _C - dz * _S, dx * _S + dz * _C


# ---------- levels ----------
Y_PAD, Y_GARDEN, Y_RESIDENCE, Y_TEA, Y_YARD, Y_EXHIBIT = 16.0, 25.0, 43.0, 16.0, 20.0, 25.0
FLOOR = 0.5                 # a floor mesh lies this far over its terrace's terrain

# ---------- terraces: flat rectangles (x0, x1, z0, z1) at a level, with rounded corners ----------
# skirt: how far outside the flat rectangle the terrain blends back to what was there (nothing where there was only sky: a cliff)
TERRACES = {
    "Garden":    dict(x0=-36.0, x1=36.0, z0=38.6, z1=96.0, y=Y_GARDEN, r=6.0, skirt=6.0, mat="Limestone"),
    "GardenTab": dict(x0=30.0, x1=39.0, z0=63.0, z1=73.0, y=Y_GARDEN, r=1.0, skirt=2.0, mat="Pavement"),     # where the bridge to the exhibition terrace starts
    "Residence": dict(x0=-32.0, x1=32.0, z0=129.0, z1=182.0, y=Y_RESIDENCE, r=5.0, skirt=9.0, mat="Limestone"),
    "Tea":       dict(x0=62.0, x1=104.0, z0=-62.0, z1=-24.0, y=Y_TEA, r=6.0, skirt=2.0, mat="Limestone"),
    "CourtTab":  dict(x0=24.0, x1=37.0, z0=-56.0, z1=-46.0, y=Y_PAD, r=2.0, skirt=2.0, mat="Pavement"),      # the bridge's near landing, on the court's side (level with the pad)
    "Yard":      dict(x0=62.0, x1=126.0, z0=-24.0, z1=44.5, y=Y_YARD, r=5.0, skirt=2.0, mat="Limestone"),
    "Exhibit":   dict(x0=62.0, x1=122.0, z0=52.0, z1=100.0, y=Y_EXHIBIT, r=5.0, skirt=4.0, mat="Limestone"),
}
# the ravine east of the garden, between it and the east terraces: a channel (x0, x1, z0, z1) of open sky cut through the ground (where there is any)
RAVINES = [dict(name="EastRavine", x0=44.0, x1=55.0, z0=46.0, z1=108.0)]

# ---------- stairs: straight runs between terraces ----------
# each run: from (x, z) at level y0 to (x, z) at y1 (a flight: 1-stud risers, 1.5 treads) or a landing (y0 == y1); half = half width of the steps
STAIRS = {
    "Rear": dict(half=8.0, runs=[((0.0, 96.0), (0.0, 109.5), 25.0, 34.0), ((0.0, 109.5), (0.0, 115.5), 34.0, 34.0), ((0.0, 115.5), (0.0, 129.0), 34.0, 43.0)]),
    "TeaToYard": dict(half=6.0, blend=3.0, runs=[((94.0, -30.0), (94.0, -24.0), 16.0, 20.0)]),
    "YardToExhibit": dict(half=6.0, blend=3.0, runs=[((94.0, 44.5), (94.0, 52.0), 20.0, 25.0)]),
}
UNDER_STEP = 1.8            # terrain under a flight lies this far under its steps (they stand in it, as the plaza stairways')
GORGE = 18.0                # the rear stair's corridor: ground follows the steps this far from the axis, then the mesa's own height blends back over 8

# ---------- bridges (decks are meshes; the terrain beneath them is whatever is there: air or a ravine) ----------
BRIDGES = {
    "Front": dict(a=(36.5, -51.0), b=(64.5, -51.0), y=16.0, rise=6.0),       # court to the tea terrace, over the gap east of the hall's front court (south of the gate pavilion)
    "Garden": dict(a=(38.0, 68.0), b=(62.0, 68.0), y=25.0, rise=6.0),         # garden to the exhibition terrace, over the ravine
}

# ---------- ground the hall's builder repaves (Grass -> Pavement), so a terrain rebuild keeps it ----------
HALL_PAVE = [(-58.0, 58.0, -56.0, 42.0), (-22.0, 22.0, -112.0, -56.0)]    # (x0, x1, z0, z1) pad frame: the hall's footprint, the top of its stair

# ---------- paved areas (terrain Pavement under walks, floors and building footprints) ----------
PAVED_RECTS = []            # filled by dawnspire.py (building footprints): (x0, x1, z0, z1)
PAVED_STRIPS = []           # walks: ((x, z), (x, z), half width)
LAWNS = [("Garden", (0.0, 70.0), (30.0, 22.0))]    # (terrace, centre, half sizes): an ellipse of Grass inside a terrace

# ---------- the region: every cell this module may change ----------
REGION_PAD = (-52.0, 135.0, -75.0, 192.0)        # a bounding box in the pad frame
REGION_MIN_LOCAL_X = 92.0                        # and island-local x at least this (the Orthodox side: x > 78 is its zone)


def in_region_box(x, z):
    return REGION_PAD[0] <= x <= REGION_PAD[1] and REGION_PAD[2] <= z <= REGION_PAD[3]


# ---------- shapes ----------
def rr_inside(x, z, x0, x1, z0, z1, r):
    """Distance inside a rounded rectangle (negative outside)."""
    cx, cz, hx, hz = (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2, (z1 - z0) / 2
    qx, qz = abs(x - cx) - (hx - r), abs(z - cz) - (hz - r)
    out = math.hypot(max(qx, 0.0), max(qz, 0.0)) + min(max(qx, qz), 0.0) - r
    return -out


def stair_runs(name):
    """The stair's runs as dicts with unit direction, length, from/to levels."""
    st = STAIRS[name]
    out = []
    for (a, b, y0, y1) in st["runs"]:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        out.append(dict(a=a, b=b, y0=y0, y1=y1, L=L, dx=(b[0] - a[0]) / L, dz=(b[1] - a[1]) / L, flight=abs(y1 - y0) > 1e-6, half=st["half"], stair=name))
    return out


def all_runs():
    out = []
    for name in STAIRS:
        out += stair_runs(name)
    return out


def run_state(x, z, run):
    """(s along the run, u across it) of a point."""
    vx, vz = x - run["a"][0], z - run["a"][1]
    return vx * run["dx"] + vz * run["dz"], -vx * run["dz"] + vz * run["dx"]


def stair_line(run, s):
    return lerp(run["y0"], run["y1"], max(0.0, min(1.0, s / run["L"])))


# ---------- the terrain override ----------
def override(lx, lz, h, d):
    """Called with the unchanged ground (h, details) of an island-local point; returns the ground with Dawnspire's terraces, stairs and ravine laid
    over it (h may become a height where there was sky). Outside REGION it returns its arguments."""
    if not ENABLED or lx < REGION_MIN_LOCAL_X:
        return h, d
    x, z = to_pad(lx, lz)
    if not in_region_box(x, z):
        return h, d
    dawn = None
    new_h = h
    # 1. terraces: the flat rectangle exactly, the skirt a blend back to the old ground (a cliff where there was none)
    best = None
    for name, t in TERRACES.items():
        din = rr_inside(x, z, t["x0"], t["x1"], t["z0"], t["z1"], t["r"])
        if din >= 0.0:
            if best is None or din > best[1]:
                best = (name, din, t)
    if best:
        name, din, t = best
        new_h = t["y"]
        dawn = {"terrace": name, "inside": din, "mat": t["mat"], "depth": 8.0 + 2.4 * din}
    else:
        near = None
        for name, t in TERRACES.items():
            dout = -rr_inside(x, z, t["x0"], t["x1"], t["z0"], t["z1"], t["r"])
            if dout < t["skirt"] and (near is None or dout < near[1]):
                near = (name, dout, t)
        if near and h is not None:
            name, dout, t = near
            m = smoothstep(0.0, t["skirt"], dout)
            new_h = lerp(t["y"], h, m)
            dawn = {"terrace": name, "inside": -dout, "mat": None, "depth": 8.0, "skirt": 1.0 - m}
    # 2. stairs: the ground under a flight, flights' own corridor (the rear stair's is a gorge in the mesa)
    for run in all_runs():
        s, u = run_state(x, z, run)
        gh = GORGE if run["stair"] == "Rear" else run["half"] + 2.0
        if -1.0 <= s <= run["L"] + 1.0:
            m = 1.0 - smoothstep(gh, gh + STAIRS[run["stair"]].get("blend", 8.0), abs(u))
            if m > 0.0:
                line = stair_line(run, s) - (UNDER_STEP if run["flight"] else 0.0)
                if new_h is None:
                    if m >= 0.5 and abs(u) <= run["half"] + 2.0:
                        new_h = line
                        dawn = {"terrace": None, "inside": 4.0, "mat": "Limestone" if run["flight"] else "Pavement", "depth": 10.0, "stair": run["stair"]}
                else:
                    new_h = lerp(new_h, line, m)
                    if m > 0.5:
                        dawn = {"terrace": None, "inside": 4.0, "mat": "Limestone" if run["flight"] else "Pavement", "depth": 10.0, "stair": run["stair"]}
    # 3. the ravine: a channel of open sky cut through the ground between the garden and the east terraces (nothing to land on: a fall is caught by the
    #    route zones, which reach 100 studs under)
    for rv in RAVINES:
        if rr_inside(x, z, rv["x0"], rv["x1"], rv["z0"], rv["z1"], 2.0) >= 0.0:
            return None, None
    if dawn is None:
        return h, d
    if new_h is None:
        return h, d
    if d is None:
        import murim_layout as M
        d = {"fields": M.comp_fields(lx, lz), "zone": "O", "mountain": 0.0}
    else:
        d = dict(d)
    d["zone"] = "O"
    d["dawn"] = dawn
    return new_h, d


# ---------- surface and underside ----------
def surface(lx, lz, slope, d, base):
    """The terrain material of a column the override touched."""
    x, z = to_pad(lx, lz)
    dawn = d["dawn"]
    mat = dawn.get("mat")
    if "stair" in dawn:
        return mat
    if mat is None:                         # a skirt or a cliff: the old material by slope
        if slope > 0.8:
            return "Rock" if fbm(lx / 9.0, lz / 9.0, 61) > 0.1 else "Limestone"
        return base
    # inside a terrace: paved places first, then a steep place is rock, then lawn, then the terrace's own
    for (x0, x1, z0, z1) in PAVED_RECTS:
        if x0 <= x <= x1 and z0 <= z <= z1:
            return "Pavement"
    if slope > 1.2:
        return "Rock"
    for (a, b, half) in PAVED_STRIPS:
        vx, vz = b[0] - a[0], b[1] - a[1]
        L2 = vx * vx + vz * vz
        t = max(0.0, min(1.0, ((x - a[0]) * vx + (z - a[1]) * vz) / L2)) if L2 else 0.0
        if math.hypot(x - (a[0] + vx * t), z - (a[1] + vz * t)) <= half:
            return "Pavement"
    for (terr, c, hs) in LAWNS:
        if dawn.get("terrace") == terr and ((x - c[0]) / hs[0]) ** 2 + ((z - c[1]) / hs[1]) ** 2 <= 1.0 and dawn["inside"] > 3.0:
            return "Grass"
    return mat


def hall_pave(lx, lz, base):
    """The hall's footprint and the top of its stair were Grass: the builder repaves them (OrthodoxBuilder.paveGround); the data does it too."""
    if not ENABLED or base != "Grass" or lx < 60.0:          # (the hall's pad reaches a little into the middle band: x 73 and up)
        return base
    x, z = to_pad(lx, lz)
    for (x0, x1, z0, z1) in HALL_PAVE:
        if x0 <= x <= x1 and z0 <= z <= z1:
            return "Pavement"
    return base


def bottom_depth(d):
    """How deep the underside of a terrace column reaches (a cone of rock under every terrace), or 0."""
    dawn = d.get("dawn") if d else None
    if not dawn:
        return 0.0
    return dawn["depth"]


def region_text():
    return "pad frame x %.0f..%.0f, z %.0f..%.0f, island-local x >= %.0f" % (REGION_PAD + (REGION_MIN_LOCAL_X,))
