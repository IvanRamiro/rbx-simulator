"""Proof that Nightfall's terrain change touches only the Demonic pad's own region (2026-11-23): compares the terrain data murim_layout writes now with the data committed
before it (git's src/worldbuild/Terrain/MurimCrossing.lua at the given ref), cell by cell, in all four arrays (heights, surface material, underside depth, underside
material), lists where every difference is, and counts the changed cells of every part of the island that must stay as it was. Plain Python.

    python3 tools/blender/world/nightfall_terrain_diff.py [git-ref [new-terrain-file]]   # writes renders/nightfall/terrain_diff.txt (the ref defaults to 385a38f, the commit
                                                                                          # before Nightfall's terrain: the data the world was built from)
A second argument names a file to check before it is copied into src/ (the scratch file under renders/nightfall/scratch/); without it the file in src/ is read.
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
import murim_nightfall_terrain as NT  # noqa: E402
import murim_windrift_terrain as WT  # noqa: E402
import murim_dawnspire_terrain as DT  # noqa: E402

DEFAULT_REF = "385a38f"


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
    g["Size"] = int(re.search(r"Size = (\d+)", lua).group(1))
    o = re.search(r"Origin = Vector2\.new\(([-\d.]+), ([-\d.]+)\)", lua)
    g["Origin"] = (float(o.group(1)), float(o.group(2)))
    return g


def main():
    ref = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REF
    old_lua = subprocess.run(["git", "show", ref + ":src/worldbuild/Terrain/MurimCrossing.lua"], cwd=REPO, capture_output=True, text=True, check=True).stdout
    new_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "src", "worldbuild", "Terrain", "MurimCrossing.lua")
    new_lua = open(new_path).read()
    a, b = grids(old_lua), grids(new_lua)
    lines = []

    def say(s=""):
        lines.append(s)
        print(s)
    say("Terrain diff: %s's src/worldbuild/Terrain/MurimCrossing.lua against %s (the arrays are run-length strings, decoded here)" % (ref, os.path.relpath(new_path, REPO)))
    say("grid %dx%d, origin %s: same shape: %s" % (a["Size"], a["Size"], a["Origin"], (a["Size"], a["Origin"]) == (b["Size"], b["Origin"])))
    n = a["Size"]
    ox, oz = a["Origin"]
    keys = ("Heights", "MaterialIndex", "Bottoms", "UndersideIndex")
    for key in keys:
        assert len(a[key]) == len(b[key]) == n * n, key
    changed = [k for k in range(n * n) if any(a[key][k] != b[key][k] for key in keys)]
    say("cells that differ in any of the four arrays: %d of %d" % (len(changed), n * n))
    by_kind = {k: 0 for k in keys}
    for k in changed:
        for key in keys:
            if a[key][k] != b[key][k]:
                by_kind[key] += 1
    say("   by array: %s" % ", ".join("%s %d" % (k, v) for k, v in by_kind.items()))

    def local_of(k):
        i, j = k % n, k // n
        return M.to_local(ox + (i + 0.5) * M.CELL, oz + (j + 0.5) * M.CELL)

    inside = outside = 0
    bad = []
    xs, zs = [], []
    kinds = {"fissure (open sky)": 0, "terraces and their skirts (height)": 0, "repaved or re-materialled ground (same height)": 0, "other (underside only)": 0}
    for k in changed:
        lx, lz = local_of(k)
        x, z = NT.to_pad(lx, lz)
        xs.append(x)
        zs.append(z)
        if NT.in_region(x, z) and not NT.protected(lx, lz):
            inside += 1
            if b["Heights"][k] is None and a["Heights"][k] is not None:
                kinds["fissure (open sky)"] += 1
            elif a["Heights"][k] != b["Heights"][k]:
                kinds["terraces and their skirts (height)"] += 1
            elif a["Heights"][k] == b["Heights"][k] and a["Bottoms"][k] == b["Bottoms"][k] and a["UndersideIndex"][k] == b["UndersideIndex"][k]:
                kinds["repaved or re-materialled ground (same height)"] += 1
            else:
                kinds["other (underside only)"] += 1
        else:
            outside += 1
            bad.append((round(lx, 1), round(lz, 1)))
    say("inside Nightfall's region (%s): %d" % (NT.region_text(), inside))
    for kk, v in kinds.items():
        say("      %-48s %6d" % (kk, v))
    say("OUTSIDE it: %d %s" % (outside, bad[:6]))
    if xs:
        say("changed cells span pad frame x %.0f..%.0f, z %.0f..%.0f" % (min(xs), max(xs), min(zs), max(zs)))
    changed_set = set(changed)

    def untouched(label, pred):
        total = diff = 0
        for k in range(n * n):
            lx, lz = local_of(k)
            if pred(lx, lz):
                total += 1
                if k in changed_set:
                    diff += 1
        say("%-96s %6d cells, %d changed" % (label, total, diff))
        return diff
    bad_parts = 0
    pc = DT.PAD_C
    wc = WT.PAD_C
    bad_parts += untouched("the plaza (radius 90 from its middle)", lambda x, z: math.hypot(x, z) <= 90.0)
    bad_parts += untouched("the bridge's spur and its abutment (z < -50)", lambda x, z: z < -50.0)

    def stairways(x, z):
        for f in M.ORDER:
            s, u = M.su(f, x, z)
            if M.tiers(f)[0][1] - 16.0 <= s <= M.tiers(f)[-1][2] + 4.0 and abs(u) <= 40.0:
                return True
        return False
    bad_parts += untouched("all three stairways and their gates (to 4 studs past each stair's top, 40 either side of its axis)", stairways)
    bad_parts += untouched("the Orthodox side, Dawnspire's terraces included (x >= 78, or inside 72 of its pad)", lambda x, z: x >= 78.0 or math.hypot(x - pc[0], z - pc[1]) <= 72.0)
    bad_parts += untouched("the Unorthodox side, Windrift's region included (x >= -70, or inside Windrift's own region)", lambda x, z: x >= -70.0 or WT.in_region(*WT.to_pad(x, z)))

    def lookouts(x, z):
        for knots in M.PATHS:
            for k0, k1 in zip(knots, knots[1:]):
                if WT._seg_dist(x, z, (k0[0], k0[1]), (k1[0], k1[1])) < 6.5:
                    return True
        for nx, nz, nr in M.NOOKS:
            if math.hypot(x - nx, z - nz) < nr + 4.0:
                return True
        for cx, cz, hx, hz, depth in M.RAVINES:
            if abs(x - cx) <= hx + 1.0 and abs(z - cz) <= hz + 1.0:
                return True
        return False
    bad_parts += untouched("the hidden paths (6.5 either side of their centre lines), the four lookouts (to 4 over their rim), the two ravines (to 1 beyond their edge)", lookouts)
    bad_parts += untouched("everything of the island outside Nightfall's region (the rest of the Demonic side, its mountains and ravine-free ground, the backdrop)",
                           lambda x, z: not (NT.in_region(*NT.to_pad(x, z)) and not NT.protected(x, z)))
    say("")
    ok = outside == 0 and bad_parts == 0
    say("RESULT: %s" % ("every difference lies inside Nightfall's own region; the plaza, the spur, the three stairways and gates, the Orthodox side (Dawnspire), the Unorthodox side (Windrift), the hidden lookouts, paths and ravines and the rest of the island are identical" if ok else "FAILED"))
    os.makedirs(os.path.join(REPO, "renders", "nightfall"), exist_ok=True)
    open(os.path.join(REPO, "renders", "nightfall", "terrain_diff.txt"), "w").write("\n".join(lines) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
