"""Nightfall Citadel's land: the Demonic side's terrain override of Murim Crossing (2026-11-23). Plain Python (no Blender).

murim_layout.py calls this module from its ground / surface / bottom / placed functions (as it calls Dawnspire's murim_dawnspire_terrain.py and Windrift's
murim_windrift_terrain.py). Everything here is declared in THE DEMONIC PAD'S FRAME: origin at the pad's centre (island-local x -126.83, z 162.33), +z away from the
plaza (up the mountain: the bearing of the pad's stairway, -38 degrees from the island's +z), +x across it (the direction Placements/MurimCrossing.lua calls toward the
island's middle, island-local (0.788, 0.616)), y over the plaza's ground (the pad is 16). The pad frame is the island frame turned by the pad's FrontYaw (-0.6632).

The terrain changes ONLY inside REGION (the pad's rear two thirds and the mountain foot behind it) and never inside what it must leave alone: the Windrift region
(the Unorthodox pad's own override), the first foundation's hidden paths, lookouts and ravines (PROTECTED), the stairway and the gate in front of the pad. `override`
returns its input unchanged everywhere else, and NIGHTFALL_TERRAIN=0 (the environment) makes that true everywhere, so the previous data can be rebuilt in every
byte to prove it (tools/blender/world/nightfall_terrain_diff.py).

What it makes (levels are heights over the plaza; every floor mesh lies 0.5 over its terrain):
    the Upper Ward   a terrace at 40 over the pad's rear and the foothill behind it (x -46..24, z 56..126): the Black Keep, the Armory and the court. Its front edge
                     is a 24-stud cliff over the pad (the Great Stair, a solid stone ramp that stands on the pad, climbs it); its left edge a 18-stud cliff over the
                     shelf; its right edge the fissure's near rim
    the Fissure      a slot of open sky (x 24..42, z 66..132) cut through the mountain beside the Upper Ward: crimson light in it, a chain bridge across it
    the Bridgehead   a raised shelf at 48 on the Upper Ward's right (x 12..24), up eight steps from the court: the chain bridge starts here
    the Residence    the ledge at 48 across the fissure (x 42..62, z 82..114): the Lord's tower
The lower ward is the pad itself (flat 16, unchanged): the curtain wall and gatehouse, the arena, the training grounds, the Ember Court and the foot of the stairs
stand on it. Stairs are solid stone ramps standing on the ground (their blocks reach down into it), so the terrain under them is not changed; only the stair
corridors that meet a terrace edge are paved (Slate).
Reach (Placements/MurimCrossing.lua, 340 from the plaza's middle): every walkable point is within it (the farthest is the Upper Ward's back-left corner, about 335).
"""
import math
import os

import blossom_layout as BL

ENABLED = os.environ.get("NIGHTFALL_TERRAIN", "1") != "0"
smoothstep, lerp, fbm = BL.smoothstep, BL.lerp, BL.fbm

# ---------- the pad's frame ----------
PAD_S = 206.0
PAD_ANGLE = math.radians(-38.0)
PAD_C = (PAD_S * math.sin(PAD_ANGLE), PAD_S * math.cos(PAD_ANGLE))    # island-local (-126.83, 162.33)
PAD_YAW = PAD_ANGLE                                                      # CFrame.Angles(0, FrontYaw, 0) of the pad's frame (-0.6632)
_C, _S = math.cos(PAD_YAW), math.sin(PAD_YAW)
Y_PAD = 16.0
FLOOR = 0.5                 # a floor mesh lies this far over its terrain


def to_local(x, z):
    """Pad frame (x, z) -> island-local (X, Z)."""
    return PAD_C[0] + x * _C + z * _S, PAD_C[1] - x * _S + z * _C


def to_pad(lx, lz):
    dx, dz = lx - PAD_C[0], lz - PAD_C[1]
    return dx * _C - dz * _S, dx * _S + dz * _C


# ---------- levels ----------
Y_UPPER, Y_BRIDGEHEAD, Y_RESIDENCE = 40.0, 48.0, 48.0

# ---------- terraces: flat rectangles (x0, x1, z0, z1) at a level, rounded corners; skirt = how far outside the flat the ground blends back (3: a cliff) ----------
# prio: where two terraces overlap the higher prio wins (the bridgehead stands on the Upper Ward's right side)
TERRACES = {
    "Upper":      dict(x0=-46.0, x1=24.0, z0=56.0, z1=126.0, y=Y_UPPER, r=5.0, skirt=3.0, mat="Slate", prio=0),
    "Bridgehead": dict(x0=12.0, x1=24.0, z0=90.0, z1=112.0, y=Y_BRIDGEHEAD, r=2.0, skirt=2.0, mat="Slate", prio=1),
    "Residence":  dict(x0=42.0, x1=62.0, z0=82.0, z1=114.0, y=Y_RESIDENCE, r=4.0, skirt=3.0, mat="Slate", prio=0),
}

# ---------- open-sky cuts: rectangles (pad frame) in which every column whose centre lies inside is removed ----------
# The Fissure: a slot through the mountain between the Upper Ward and the Residence ledge. The chain bridge crosses it along z 101 (deck 48 over a 4-stud-column world:
# the bridge's corridor, 2.5 studs each side and up to 4.6 over the deck, must hold no column: the cut is the corridor plus the 2.9 a turned column's cell reaches).
CUTS = [dict(name="Fissure", x0=24.0, x1=42.0, z0=66.0, z1=132.0)]

# ---------- paved places (terrain Slate under stair feet and walks near the pad's rim, where the pad's ground is not Slate or Asphalt) ----------
PAVED_STRIPS = [((-40.0, 12.0), (-40.0, 58.0), 4.5)]       # ((x, z), (x, z), half width): the Postern stair

GLOW_RIM = 7.0              # a column within this many studs of the fissure hangs in cracked lava (the fissure's walls glow below the top layers)

# ---------- the region: every cell this module may change ----------
REGION_R = 62.0                                   # the pad's flat disc (54) and the first stretch of its skirt
REGION_MIN_Z = -50.0                              # the stairway and the gate (z -54 and in front) are never touched
REGION_BOX = (-64.0, 70.0, 30.0, 136.0)           # the mountain foot behind the pad (x0, x1, z0, z1)


def in_region(x, z):
    if z < REGION_MIN_Z:
        return False
    if math.hypot(x, z) <= REGION_R:
        return True
    b = REGION_BOX
    return b[0] <= x <= b[1] and b[2] <= z <= b[3]


def protected(lx, lz):
    """True where another territory's own ground or the first foundation's hidden paths stand: Windrift's region (never changed by this module), the Unorthodox side's
    paths, lookouts and ravines."""
    import murim_layout as M
    import murim_windrift_terrain as WT
    x, z = WT.to_pad(lx, lz)
    if WT.in_region(x, z):
        return True
    return WT.protected(lx, lz)


# ---------- shapes ----------
def rr_inside(x, z, x0, x1, z0, z1, r):
    """Distance inside a rounded rectangle (negative outside)."""
    cx, cz, hx, hz = (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2, (z1 - z0) / 2
    qx, qz = abs(x - cx) - (hx - r), abs(z - cz) - (hz - r)
    out = math.hypot(max(qx, 0.0), max(qz, 0.0)) + min(max(qx, qz), 0.0) - r
    return -out


def _seg_dist(x, z, a, b):
    vx, vz = b[0] - a[0], b[1] - a[1]
    L2 = vx * vx + vz * vz
    t = max(0.0, min(1.0, ((x - a[0]) * vx + (z - a[1]) * vz) / L2)) if L2 else 0.0
    return math.hypot(x - (a[0] + vx * t), z - (a[1] + vz * t))


def cut_distance(x, z):
    """Distance outside the nearest cut rectangle (0 inside)."""
    best = 1e9
    for c in CUTS:
        dx = max(c["x0"] - x, 0.0, x - c["x1"])
        dz = max(c["z0"] - z, 0.0, z - c["z1"])
        best = min(best, math.hypot(dx, dz))
    return best


# ---------- the terrain override ----------
def override(lx, lz, h, d):
    """Called with the unchanged ground (h, details) of an island-local point; returns the ground with the Citadel's terraces and fissure laid over it."""
    if not ENABLED:
        return h, d
    x, z = to_pad(lx, lz)
    if not in_region(x, z) or protected(lx, lz):
        return h, d
    night = None
    new_h = h
    # 1. terraces: the flat rectangle exactly, the skirt a blend back to the old ground
    best = None
    for name, t in TERRACES.items():
        din = rr_inside(x, z, t["x0"], t["x1"], t["z0"], t["z1"], t["r"])
        if din >= 0.0 and (best is None or (t["prio"], din) > (best[2]["prio"], best[1])):
            best = (name, din, t)
    if best:
        name, din, t = best
        new_h = t["y"]
        night = {"terrace": name, "inside": din, "mat": t["mat"], "depth": 8.0 + 2.4 * din}
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
            night = {"terrace": name, "inside": -dout, "mat": None, "depth": 8.0, "skirt": 1.0 - m}
    # 2. the cuts (open sky): the fissure
    for c in CUTS:
        if c["x0"] <= x <= c["x1"] and c["z0"] <= z <= c["z1"]:
            return None, None
    # 3. paved strips (the stair corridors near the pad's rim)
    if night is None and h is not None:
        for (a, b, half) in PAVED_STRIPS:
            if _seg_dist(x, z, a, b) <= half:
                night = {"terrace": None, "inside": 4.0, "mat": "Slate", "depth": 0.0, "pave": True}
                break
    if night is None or new_h is None:
        return h, d
    if d is None:
        import murim_layout as M
        d = {"fields": M.comp_fields(lx, lz), "zone": "D", "mountain": 0.0}
    else:
        d = dict(d)
    d["zone"] = "D"
    d["night"] = night
    night["rim"] = cut_distance(x, z)
    return new_h, d


# ---------- surface and underside ----------
def surface(lx, lz, slope, d, base):
    """The terrain material of a column the override touched: Slate on every terrace and walk, a basalt cliff with cracked-lava veins on a skirt."""
    night = d["night"]
    mat = night.get("mat")
    if night.get("pave") or mat is not None:
        return mat
    n = fbm(lx / 7.0, lz / 7.0, 83)
    if slope > 0.8:
        if night["rim"] < 8.0 and n > 0.52:
            return "CrackedLava"         # the cliffs beside the fissure glow in their cracks (nothing is built on them)
        return "Basalt" if n > 0.3 else "Slate"
    return "Slate" if base in ("Slate", "Asphalt") else base


def bottom_depth(d):
    """How deep the underside of a column the override touched reaches (a cone of rock under every terrace), or 0."""
    night = d.get("night") if d else None
    if not night:
        return 0.0
    return night["depth"]


def region_text():
    return "pad frame: radius %.0f round the pad's centre (z >= %.0f) and x %.0f..%.0f, z %.0f..%.0f behind it, minus Windrift's region and the protected paths, lookouts and ravines" % (
        REGION_R, REGION_MIN_Z, REGION_BOX[0], REGION_BOX[1], REGION_BOX[2], REGION_BOX[3])
