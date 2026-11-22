"""jade_lib_oldmap: the island as it is today, read without Blender (2026-11-22).

`jade_island.py` (the first foundation's layout) is Jade Grove's own and stays the source of every position the game depends on. It imports
`worldlib` lazily inside its height functions, and worldlib needs Blender; here a stand-in `worldlib` (the same value noise, copied constant for
constant) is put in `sys.modules` first, so plain Python can sample the very same ground. `reproduces_terrain()` proves the stand-in: the old
terrain file is rebuilt from it and compared byte for byte with src/worldbuild/Terrain/JadeGrove.lua.
"""
import math
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
WORLD = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))


def _hash(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def noise2(x, y, seed=0):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _hash(ix, iy, seed), _hash(ix + 1, iy, seed)
    c, d = _hash(ix, iy + 1, seed), _hash(ix + 1, iy + 1, seed)
    return (a + (b - a) * sx) + ((c + (d - c) * sx) - (a + (b - a) * sx)) * sy


def fbm(x, y, seed=0, octaves=4, lac=2.0, gain=0.5):
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        total += amp * (noise2(x * freq, y * freq, seed + o * 17) * 2 - 1)
        norm += amp
        amp *= gain
        freq *= lac
    return total / norm


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))) if e1 != e0 else (1.0 if x >= e1 else 0.0)
    return t * t * (3 - 2 * t)


def gauss(dx, dz, r):
    return math.exp(-(dx * dx + dz * dz) / (2 * r * r))


def load():
    """The old jade_island module, its worldlib import served by the stand-in."""
    stub = types.ModuleType("worldlib")
    stub.fbm, stub.smoothstep, stub.gauss, stub.noise2 = fbm, smoothstep, gauss, noise2
    stub.REPO = REPO
    sys.modules["worldlib"] = stub
    sys.path.insert(0, WORLD)
    import jade_island
    return jade_island


OLD = load()


def export_old_text():
    """The old terrain file's text, regenerated from the old functions (worldlib.export_heightfield's logic, copied)."""
    J = OLD
    centre, cell, half = J.CENTRE, 4, 176
    materials = J.MATERIALS
    priority = [("Mud", 2)]
    corner_x = math.floor((centre[0] - half) / cell) * cell
    corner_z = math.floor((centre[2] - half) / cell) * cell
    n = int(math.ceil((centre[0] + half - corner_x) / cell))
    n = max(n, int(math.ceil((centre[2] + half - corner_z) / cell)))
    heights, mats = [], []
    for j in range(n):
        for i in range(n):
            x = corner_x - centre[0] + (i + 0.5) * cell
            z = corner_z - centre[2] + (j + 0.5) * cell
            h, m = J.height(x, z)
            if h is not None and priority:
                counts = {}
                for sx in (-0.33, 0, 0.33):
                    for sz in (-0.33, 0, 0.33):
                        _, sm = J.height(x + sx * cell, z + sz * cell)
                        if sm:
                            counts[sm] = counts.get(sm, 0) + 1
                for name, need in priority:
                    if counts.get(name, 0) >= need:
                        m = name
                        break
            if h is None:
                heights.append("false")
                mats.append("0")
            else:
                heights.append("%.2f" % h)
                mats.append(str(materials.index(m) + 1))
    lines = [
        "-- Written by tools/blender/world (%s). Do not edit by hand." % J.NAME,
        "return {",
        '    Island = "%s",' % J.NAME,
        "    Centre = Vector3.new(%g, %g, %g)," % tuple(centre),
        "    Turns = %s, -- quarter turns about the centre, each adding 90 degrees of bearing" % ("%g" % J.TURNS),
        "    Origin = Vector2.new(%g, %g), -- world X/Z of the grid's first corner" % (corner_x, corner_z),
        "    Cell = %d," % cell,
        "    Size = %d," % n,
        "    Materials = { %s }," % ", ".join('"%s"' % m for m in materials),
    ]

    def chunked(name, vals):
        out = ["    %s = {" % name]
        for k in range(0, len(vals), n):
            out.append("        " + ", ".join(vals[k:k + n]) + ",")
        out.append("    },")
        return out
    lines += chunked("Heights", heights) + chunked("MaterialIndex", mats)
    lines += ["}", ""]
    return "\n".join(lines), n, heights, mats, (corner_x, corner_z)


def reproduces_terrain():
    text, n, heights, mats, origin = export_old_text()
    path = os.path.join(REPO, "src", "worldbuild", "Terrain", "JadeGrove.lua")
    with open(path) as f:
        have = f.read()
    # (the old file's first line is a comment with an older wording; everything from the second line on is data and is compared byte for byte)
    return text.split("\n", 1)[1] == have.split("\n", 1)[1], len(text), len(have)


if __name__ == "__main__":
    ok, a, b = reproduces_terrain()
    print("old terrain file reproduced byte for byte:", ok, a, b)
