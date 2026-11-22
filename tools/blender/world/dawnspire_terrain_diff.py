"""Proof that Dawnspire's terrain change touches only the Orthodox side (2026-11-22): compares the terrain data murim_layout writes now with the data it
wrote before (git HEAD's src/worldbuild/Terrain/MurimCrossing.lua), cell by cell, in all four arrays (heights, surface material, underside depth, underside
material), and lists where every difference is. Plain Python.

    python3 tools/blender/world/dawnspire_terrain_diff.py            # writes renders/dawnspire/terrain_diff.txt
"""
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

import murim_layout as M  # noqa: E402
import murim_dawnspire_terrain as DT  # noqa: E402


def decode(text, off, conv):
    out = []
    for tok in text.split(","):
        if tok.startswith("~"):
            out += [off] * int(tok[1:])
        elif tok:
            out.append(conv(tok))
    return out


def grids(lua):
    g = {}
    for key, off, conv in (("Heights", None, float), ("MaterialIndex", 0, int), ("Bottoms", None, float), ("UndersideIndex", 0, int)):
        m = re.search(r"\b" + key + r' = "([^"]*)"', lua)
        g[key] = decode(m.group(1), off, conv)
    for key in ("Origin", "Size", "Cell"):
        pass
    g["Size"] = int(re.search(r"Size = (\d+)", lua).group(1))
    o = re.search(r"Origin = Vector2\.new\(([-\d.]+), ([-\d.]+)\)", lua)
    g["Origin"] = (float(o.group(1)), float(o.group(2)))
    return g


def main():
    old_lua = subprocess.run(["git", "show", "HEAD:src/worldbuild/Terrain/MurimCrossing.lua"], cwd=REPO, capture_output=True, text=True, check=True).stdout
    new_lua = open(os.path.join(REPO, "src", "worldbuild", "Terrain", "MurimCrossing.lua")).read()
    a, b = grids(old_lua), grids(new_lua)
    lines = []
    say = lambda s="": (lines.append(s), print(s))
    say("Terrain diff: git HEAD's src/worldbuild/Terrain/MurimCrossing.lua against the file now (the arrays are run-length strings, decoded here)")
    say("grid %dx%d, origin %s: same shape: %s" % (a["Size"], a["Size"], a["Origin"], (a["Size"], a["Origin"]) == (b["Size"], b["Origin"])))
    n = a["Size"]
    ox, oz = a["Origin"]
    changed = []
    for key in ("Heights", "MaterialIndex", "Bottoms", "UndersideIndex"):
        assert len(a[key]) == len(b[key]) == n * n, key
    for k in range(n * n):
        if any(a[key][k] != b[key][k] for key in ("Heights", "MaterialIndex", "Bottoms", "UndersideIndex")):
            changed.append(k)
    say("cells that differ in any of the four arrays: %d of %d" % (len(changed), n * n))
    inside = outside = 0
    bad = []
    xs, zs = [], []
    for k in changed:
        i, j = k % n, k // n
        wx, wz = ox + (i + 0.5) * M.CELL, oz + (j + 0.5) * M.CELL
        lx, lz = M.to_local(wx, wz)
        px, pz = DT.to_pad(lx, lz)
        xs.append(px)
        zs.append(pz)
        in_box = DT.in_region_box(px, pz)
        in_hall = lx >= 60.0 and any(r[0] <= px <= r[1] and r[2] <= pz <= r[3] for r in DT.HALL_PAVE)
        ok = in_hall or (in_box and lx >= DT.REGION_MIN_LOCAL_X)
        if ok:
            inside += 1
        else:
            outside += 1
            bad.append((round(lx, 1), round(lz, 1)))
    say("inside the Orthodox region (%s; plus the hall's repaved footprint): %d" % (DT.region_text(), inside))
    say("OUTSIDE it: %d %s" % (outside, bad[:6]))
    if xs:
        say("changed cells span pad frame x %.0f..%.0f, z %.0f..%.0f" % (min(xs), max(xs), min(zs), max(zs)))
    # named parts that must be byte-identical
    def untouched(label, pred):
        total = diff = 0
        for k in range(n * n):
            i, j = k % n, k // n
            lx, lz = M.to_local(ox + (i + 0.5) * M.CELL, oz + (j + 0.5) * M.CELL)
            if pred(lx, lz):
                total += 1
                if k in changed_set:
                    diff += 1
        say("%-52s %6d cells, %d changed" % (label, total, diff))
        return diff
    changed_set = set(changed)
    bad_parts = 0
    bad_parts += untouched("the plaza (radius 90 from its middle)", lambda x, z: math.hypot(x, z) <= 90.0)
    bad_parts += untouched("the bridge's spur and its abutment (z < -50)", lambda x, z: z < -50.0)
    def hall(x, z):
        px, pz = DT.to_pad(x, z)
        return x >= 60.0 and any(r[0] <= px <= r[1] and r[2] <= pz <= r[3] for r in DT.HALL_PAVE)
    bad_parts += untouched("the Unorthodox side (local x -78..78, z > 40, off the hall's pad)", lambda x, z: -78.0 <= x <= 78.0 and z > 40.0 and not hall(x, z))
    bad_parts += untouched("the Demonic side (local x < -78)", lambda x, z: x < -78.0)
    bad_parts += untouched("the Unorthodox pad, its stair and the hidden paths (x < 92)", lambda x, z: x < 60.0)
    say("")
    say("RESULT: %s" % ("every difference lies inside the Orthodox region; the plaza, the spur and bridge end, the Unorthodox and Demonic sides are identical" if outside == 0 and bad_parts == 0 else "FAILED"))
    os.makedirs(os.path.join(REPO, "renders", "dawnspire"), exist_ok=True)
    open(os.path.join(REPO, "renders", "dawnspire", "terrain_diff.txt"), "w").write("\n".join(lines) + "\n")
    return 0 if outside == 0 and bad_parts == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
