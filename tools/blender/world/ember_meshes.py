"""Ember Peak meshes, batch 1.

- The island atlas.
- The underside: hanging hexagonal basalt columns, with a magma core glowing through the gaps.
- The crater crown, the lava lake with crust plates, and the Caldera pillar.
- The lava river.
- Kit pieces: the basalt steps up the volcano and the Ember Gate (with its brazier fires).

Island-specific pieces are authored in island-local Roblox studs (anchor at the island centre);
kit pieces are authored around their own origin.
"""
import bpy, math, os, random
import worldlib as W
import ember_island as E
import layout as L
import start_props as SP

TAU = 2 * math.pi
oriented = SP.oriented


# ---------- atlas ----------
def _n(u, v, f, seed):
    a = u * TAU
    return W.fbm(math.cos(a) * f + 7, math.sin(a) * f + v * f * 2, seed=seed, octaves=3)


def _ramp(lo, hi, v, n, k=0.04):
    return tuple(max(0.0, min(1.0, lo[i] + (hi[i] - lo[i]) * v + k * n)) for i in range(3))


def basalt(u, v):
    # vertical fracture lines along each column face, weathered lighter toward the tops
    fracture = abs(math.sin(u * TAU * 11 + 2.0 * _n(u, v * 0.3, 2, 101))) ** 0.25
    # cool near-black stone, so warm firelight never turns it brown
    c = _ramp((0.06, 0.065, 0.08), (0.22, 0.23, 0.27), v, _n(u, v, 6, 102), 0.04)
    return tuple(x * (0.7 + 0.3 * fracture) for x in c)


def obsidian(u, v):
    sheen = max(0.0, 1 - abs(v - 0.8) * 9) * 0.25
    c = _ramp((0.03, 0.02, 0.05), (0.18, 0.13, 0.25), v, _n(u, v, 5, 103), 0.03)
    return tuple(min(1.0, x + sheen) for x in c)


def magma(u, v):
    return _ramp((0.32, 0.03, 0.02), (1.0, 0.72, 0.25), v, _n(u, v, 7, 104), 0.08)


def ash(u, v):
    return _ramp((0.2, 0.19, 0.19), (0.45, 0.43, 0.42), v, _n(u, v, 9, 105), 0.05)


def iron(u, v):
    if _n(u, v, 13, 106) > 0.42:  # rust
        return (0.42, 0.2, 0.1)
    return _ramp((0.1, 0.09, 0.09), (0.38, 0.33, 0.3), v, _n(u, v, 8, 107), 0.04)


def cinnabar(u, v):
    return _ramp((0.42, 0.05, 0.03), (0.8, 0.18, 0.1), v, _n(u, v, 6, 108), 0.03)


def emberstone(u, v):
    return _ramp((0.24, 0.11, 0.07), (0.52, 0.3, 0.2), v, _n(u, v, 7, 109), 0.05)


def petrified(u, v):
    rings = abs(math.sin(v * 50 + 4 * _n(u, v, 3, 110)))
    return _ramp((0.3, 0.3, 0.3), (0.58, 0.57, 0.55), v * (0.7 + 0.3 * rings), _n(u, v, 9, 111), 0.04)  # grey stone, not wood


def gold(u, v):
    return _ramp((0.5, 0.34, 0.1), (0.95, 0.78, 0.38), v, _n(u, v, 7, 112), 0.04)


def glow(u, v):
    return (1.0, 0.62, 0.28)


def soot(u, v):
    return _ramp((0.04, 0.035, 0.035), (0.18, 0.15, 0.14), v, _n(u, v, 9, 113), 0.03)


def crystal(u, v):
    return _ramp((0.55, 0.08, 0.04), (1.0, 0.62, 0.36), v, _n(u, v, 5, 114), 0.06)


STRIPS = [(96, basalt), (32, obsidian), (64, magma), (32, ash), (48, iron), (32, cinnabar), (48, emberstone),
          (48, petrified), (32, gold), (16, glow), (32, soot), (32, crystal)]
BASALT, OBSIDIAN, MAGMA, ASH, IRON, CINNABAR, EMBERSTONE, PETRIFIED, GOLD, GLOW, SOOT, CRYSTAL = range(12)


def ground(x, z):
    return E.height(x, z)[0]


# ---------- the basalt column, the island's building block ----------
def column(mb, cx, cz, r, y_bottom, y_top, band, seed, top=True, bottom=True, tilt=0.0, bottom_band=None):
    """A hexagonal basalt column. The top (and bottom) cap can be tilted a little, like a
    broken column end. `tilt` is the cap's slope in studs across the column."""
    rnd = random.Random(seed)
    yaw = rnd.uniform(0, TAU / 6)
    ta, ba = rnd.uniform(0, TAU), rnd.uniform(0, TAU)
    corners = [(cx + math.cos(yaw + TAU * k / 6) * r, cz + math.sin(yaw + TAU * k / 6) * r) for k in range(6)]
    tops = [(x, y_top + tilt * 0.5 * math.cos(math.atan2(z - cz, x - cx) - ta), z) for x, z in corners]
    bots = [(x, y_bottom + tilt * 0.5 * math.cos(math.atan2(z - cz, x - cx) - ba), z) for x, z in corners]
    u0 = rnd.random()
    v0, v1 = band
    # a chamfer ring just below the top edge gives each column a lit, broken-edge rim
    bevel = min(0.35, r * 0.12)
    inner = [(cx + (x - cx) * 0.86, y, cz + (z - cz) * 0.86) for x, y, z in tops]
    shoulder = [(x, y - bevel, z) for x, y, z in tops]
    for k in range(6):
        j = (k + 1) % 6
        out = ((corners[k][0] + corners[j][0]) / 2 - cx, 0, (corners[k][1] + corners[j][1]) / 2 - cz)
        # u runs across each face so the atlas's vertical fractures show on every side
        ua, ub = u0 + k / 6, u0 + (k + 1) / 6
        mb.face([shoulder[k], shoulder[j], bots[j], bots[k]],
                [(ua, v0 + (v1 - v0) * 0.9), (ub, v0 + (v1 - v0) * 0.9), (ub, v0 + (v1 - v0) * 0.2), (ua, v0 + (v1 - v0) * 0.2)])
        _fix_last(mb, out)
        if top:
            mb.face([inner[k], inner[j], shoulder[j], shoulder[k]], [(ua, v1)] * 4)
            _fix_last(mb, (out[0], 1.2, out[2]))
    if top:
        oriented(mb, inner, (0, 1, 0), band, u0, [0.97] * 6)
    if bottom:
        oriented(mb, bots, (0, -1, 0), bottom_band or band, u0, [0.5 if bottom_band else 0.1] * 6)


def _fix_last(mb, want):
    """Flip the most recently added face if its normal points away from `want`."""
    face = mb.faces[-1]
    pts = [mb.verts[i] for i in face]
    n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
    w = W.rb(*want)
    if n.dot(w) < 0:
        face.reverse()
        mb.uvs[-1].reverse()


def hex_cells(radius_fn, spacing):
    """Centres of a hexagonal grid inside the outline radius_fn(theta)."""
    out = []
    rows = int(120 / (spacing * 0.866)) + 2
    for j in range(-rows, rows + 1):
        for i in range(-rows, rows + 1):
            x = (i + (0.5 if j % 2 else 0.0)) * spacing
            z = j * spacing * 0.866
            r = math.hypot(x, z)
            if r <= radius_fn(math.atan2(z, x)):
                out.append((x, z))
    return out


# ---------- underside ----------
UNDER_TOP = -3.0
UNDER_R, UNDER_SPACING = 4.6, 10.0


def under_columns(coll, mat, bands):
    """Basalt organ pipes hanging under the island: long at the centre, short at the rim, with
    magma-lit broken ends. Narrow gaps between them show the magma core."""
    mb = W.MeshBuilder()
    rnd = random.Random(201)
    v0, v1 = bands[BASALT]
    for n, (x, z) in enumerate(hex_cells(lambda th: E.rim(th) + 1.5, UNDER_SPACING)):
        R = E.rim(math.atan2(z, x))
        t = min(1.0, math.hypot(x, z) / R)
        length = 16 + 66 * (1 - t ** 1.5) + rnd.uniform(-8, 8)
        column(mb, x, z, UNDER_R, UNDER_TOP - length, UNDER_TOP, bands[BASALT], 300 + n, top=False,
               tilt=rnd.uniform(1.0, 4.0), bottom_band=bands[MAGMA] if rnd.random() < 0.35 else None)
    return mb.object("EP_UnderColumns", coll, mat)


def magma_core(coll, mat, bands):
    """The glowing heart the columns hang around (Neon in Roblox, no collision)."""
    mb = W.MeshBuilder()
    rings = []
    for s, y in ((0.86, -4.0), (0.8, -20.0), (0.62, -40.0), (0.4, -58.0), (0.18, -72.0)):
        rings.append([(math.cos(TAU * i / 20) * E.rim(TAU * i / 20) * s, y, math.sin(TAU * i / 20) * E.rim(TAU * i / 20) * s)
                      for i in range(20)])
    for k in range(len(rings) - 1):
        for i in range(20):
            j = (i + 1) % 20
            a = TAU * (i + 0.5) / 20
            oriented(mb, [rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]], (math.cos(a), -0.3, math.sin(a)),
                     bands[GLOW], 0.5, [1.0] * 4)
    for i in range(20):
        oriented(mb, [rings[-1][i], rings[-1][(i + 1) % 20], (0, -78.0, 0)], (0, -1, 0), bands[GLOW], 0.5, [1.0] * 3)
    return mb.object("EP_MagmaCore", coll, mat)


# ---------- the volcano: crater crown, lava lake, Caldera pillar, river ----------
VX, VZ = E.VOLCANO[0], E.VOLCANO[1]
STEP_ARRIVAL = 0.35   # bearing (radians from the volcano axis) where the basalt steps reach the rim


def crater_crown(coll, mat, bands):
    mb = W.MeshBuilder()
    rnd = random.Random(211)
    notch = math.atan2(E.RIVER[0][1] - VZ, E.RIVER[0][0] - VX)
    for k in range(20):
        a = TAU * k / 20 + rnd.uniform(-0.08, 0.08)
        gap = lambda b: abs((a - b + math.pi) % TAU - math.pi)
        if gap(notch) < 0.45 or gap(STEP_ARRIVAL) < 0.22:
            continue
        rr = E.RIM_R + rnd.uniform(-0.5, 2.5)
        x, z = VX + math.cos(a) * rr, VZ + math.sin(a) * rr
        g = ground(x, z)
        column(mb, x, z, rnd.uniform(1.5, 2.4), g - 4, g + rnd.uniform(1.5, 5.5), bands[BASALT], 600 + k,
               tilt=rnd.uniform(0.5, 2.5))
    return mb.object("EP_CraterCrown", coll, mat)


def lake_outline(offset=0.8, seg=40):
    """Points around the caldera where the floor rises to the lava surface (plus an offset)."""
    out = []
    for i in range(seg):
        a = TAU * i / seg
        lo, hi = 0.0, E.RIM_R
        for _ in range(30):
            mid = (lo + hi) / 2
            if ground(VX + math.cos(a) * mid, VZ + math.sin(a) * mid) < E.LAVA_LAKE:
                lo = mid
            else:
                hi = mid
        r = lo + offset
        out.append((VX + math.cos(a) * r, VZ + math.sin(a) * r))
    return out


LAKE_SURFACE = E.LAVA_LAKE + 0.4  # a little above the level, so voxel smoothing never hides it


def lava_lake(coll, mat, bands):
    mb = W.MeshBuilder()
    ring = lake_outline(offset=1.6)
    y = LAKE_SURFACE
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]
        oriented(mb, [(a[0], y, a[1]), (b[0], y, b[1]), (VX, y, VZ)], (0, 1, 0), bands[GLOW], 0.5, [1.0] * 3)
    return mb.object("EP_LavaLake", coll, mat)


def lava_crust(coll, mat, bands):
    """Cooling crust plates drifting on the lake (dark, slightly above the lava)."""
    mb = W.MeshBuilder()
    rnd = random.Random(221)
    for k in range(9):
        a, d = rnd.uniform(0, TAU), rnd.uniform(3.5, 7.0)
        cx, cz = VX + math.cos(a) * d, VZ + math.sin(a) * d
        size = rnd.uniform(0.9, 1.8)
        poly = [(cx + math.cos(TAU * i / 6 + a) * size * rnd.uniform(0.7, 1.2), cz + math.sin(TAU * i / 6 + a) * size * rnd.uniform(0.7, 1.2))
                for i in range(6)]
        SP.slab_tile(mb, poly, E.LAVA_LAKE + 0.18, E.LAVA_LAKE - 0.3, bands[SOOT], rnd.random(), 0.7)
    return mb.object("EP_LavaCrust", coll, mat)


PILLAR_TOP = E.LAVA_LAKE + 5.0  # the Caldera pillar's standing top


def caldera_pillar(coll, mat, bands):
    mb = W.MeshBuilder()
    column(mb, VX, VZ, 2.4, E.CRATER_FLOOR - 2, PILLAR_TOP, bands[BASALT], 700, tilt=0.0)
    for k, (a, h, r) in enumerate(((0.6, -2.0, 1.1), (2.4, -3.3, 1.0), (4.3, -1.2, 0.9))):
        x, z = VX + math.cos(a) * 3.2, VZ + math.sin(a) * 3.2
        column(mb, x, z, r, E.CRATER_FLOOR - 2, PILLAR_TOP + h, bands[BASALT], 710 + k, tilt=1.2)
    return mb.object("EP_CalderaPillar", coll, mat)


def river_samples(step=2.0):
    pts = []
    for a, b in zip(E.RIVER, E.RIVER[1:]):
        L_ = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L_ / step))
        for i in range(n):
            t = i / n
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    pts.append(E.RIVER[-1])
    return pts


def lava_river(coll, mat, bands):
    """A glowing ribbon down the river channel, riding just above the carved bed."""
    mb = W.MeshBuilder()
    pts = river_samples()
    half = E.RIVER_HALF * 0.85
    prev = None
    for k, (x, z) in enumerate(pts):
        q = pts[min(k + 1, len(pts) - 1)]; o = pts[max(k - 1, 0)]
        dx, dz = q[0] - o[0], q[1] - o[1]
        Ln = math.hypot(dx, dz) or 1
        ax, az = -dz / Ln * half, dx / Ln * half
        y = max(ground(x + ax * f, z + az * f) for f in (-1, -0.5, 0, 0.5, 1)) + 0.9
        if k == 0:
            y = max(y, E.LAVA_LAKE)
        cur = ((x - ax, y, z - az), (x + ax, y, z + az))
        if prev:
            oriented(mb, [prev[0], prev[1], cur[1], cur[0]], (0, 1, 0), bands[GLOW], 0.5, [1.0] * 4)
        prev = cur
    return mb.object("EP_LavaRiver", coll, mat)


# ---------- kit ----------
def basalt_step(coll, mat, bands):
    """One Qinggong step up the volcano: a column whose top is the origin, 16 studs tall."""
    mb = W.MeshBuilder()
    column(mb, 0, 0, 2.7, -16.0, 0.0, bands[BASALT], 800, tilt=0.0)
    return mb.object("EP_BasaltStep", coll, mat)


GATE_HALF = 5.0  # half the gap between the gate's column bundles


def ember_gate(coll, mat, bands):
    """Twin bundles of basalt columns either side of the path, iron braziers on top and a cracked
    obsidian lintel with a cinnabar plaque. Origin at ground centre; the path runs along Z."""
    mb = W.MeshBuilder()
    for side in (-1, 1):
        bx = side * (GATE_HALF + 2.2)
        for k, (dx, dz, r, h) in enumerate(((0, 0, 1.9, 13.0), (side * 1.9, 1.3, 1.4, 10.5), (side * 1.5, -1.6, 1.3, 9.0))):
            column(mb, bx + dx, dz, r, -2.0, h, bands[BASALT], 900 + k + (10 if side > 0 else 0), tilt=0.6 if k else 0.0)
        # brazier bowl on the tallest column
        mb.lathe([(1.0, 14.9, 0.4), (1.9, 15.0, 0.9), (2.1, 14.6, 0.8), (1.6, 13.6, 0.6), (0.9, 13.0, 0.4)], 10,
                 bands[IRON], centre=(bx, 0, 0), cap_top=True, u_repeat=1.0)
    # obsidian lintel resting on the two tallest columns, with a cinnabar plaque
    mb.box((0, 13.4, 0), (2 * (GATE_HALF + 2.2) + 2.6, 1.0, 2.0), bands[OBSIDIAN], u=0.5, top_shade=0.9, side_shade=0.6)
    for side in (1, -1):
        mb.box((0, 12.2, side * 0.95), (3.2, 1.6, 0.2), bands[CINNABAR], u=0.5, top_shade=0.9, side_shade=0.8)
    return mb.object("EP_EmberGate", coll, mat)


def gate_fire(coll, mat, bands):
    """The braziers' flames (Neon in Roblox, with a light)."""
    mb = W.MeshBuilder()
    for side in (-1, 1):
        bx = side * (GATE_HALF + 2.2)
        for k, (dx, dz, h) in enumerate(((0, 0, 3.2), (0.6, 0.3, 2.2), (-0.5, -0.4, 2.5))):
            mb.lathe([(0.0, 14.9 + h, 1.0), (0.7, 14.9 + h * 0.4, 0.9), (0.9, 14.8, 0.8)], 7, bands[GLOW],
                     centre=(bx + dx, 0, dz), cap_top=False, cap_bottom=True, u_repeat=0.0)
    return mb.object("EP_GateFire", coll, mat)


# ---------- placements ----------
def step_positions():
    """Basalt steps from the spur at the volcano's east foot up to the crater rim: each top rises
    about 6 studs over about 8 horizontally (two air leaps clear it easily; Ember Peak needs three)."""
    start = E.PATHS[4][-1]
    a0 = math.atan2(start[1] - VZ, start[0] - VX)
    out = []
    tops = [12.0, 18.0, 24.0, 30.0, 36.0, 41.0]
    for k, top in enumerate(tops):
        frac = k / (len(tops) - 1)
        a = a0 + (STEP_ARRIVAL - a0) * frac
        # radius where the flank is about 3 studs below the step top, so each column stands proud
        lo, hi = E.RIM_R + 0.5, E.VOLCANO[2]
        for _ in range(30):
            mid = (lo + hi) / 2
            if ground(VX + math.cos(a) * mid, VZ + math.sin(a) * mid) > top - 3:
                lo = mid
            else:
                hi = mid
        out.append(((VX + math.cos(a) * lo, top, VZ + math.sin(a) * lo), k * 0.7))
    return out


def gate_frame():
    """Ember Gate position and yaw: across the path between the landing and the junction."""
    gx, gz = 38.0, -33.0
    a, b = E.PATHS[0][1], E.PATHS[0][2]
    return (gx, ground(gx, gz) - 0.3, gz), math.atan2(b[0] - a[0], b[1] - a[1])


ISLAND_PIECES = [under_columns, magma_core, crater_crown, lava_lake, lava_crust, caldera_pillar, lava_river]
KIT_PIECES = [basalt_step, ember_gate, gate_fire]


def build():
    img, bands = W.atlas_image("EmberPeak_Atlas", 512, STRIPS)
    mat = W.textured_material("EmberPeak_Mat", img)
    root = W.collection(E.NAME)
    island = W.collection("EP_Island", root)
    kit = W.collection("EP_Kit", root)
    W.clear_collection(island); W.clear_collection(kit)
    return [f(island, mat, bands) for f in ISLAND_PIECES], [f(kit, mat, bands) for f in KIT_PIECES], img


def relic_positions():
    """Island-local positions of the three Ember Peak relics. Batch 2 builds the Ember Forge and
    the Ashen Sigil monolith around their spots."""
    fx, fz, _ = E.FORGE
    ax, az, _ = E.ASH
    return {
        "CalderaCrown": (VX, PILLAR_TOP + 3.0, VZ),             # on the basalt pillar in the lava lake
        "EmberHeart": (fx, 2.0 + 4.0, fz),                      # in the Ember Forge's furnace
        "AshenSigil": (ax, 0.5 + 4.5, az),                      # before the Ashen Sigil monolith
    }


def lavafall_lip():
    """Where the river leaves the island, and the point it flows from (for the fall's direction)."""
    (x0, z0), (x1, z1) = E.RIVER[-2], E.RIVER[-1]
    return (x1, ground(x1, z1) + 0.35, z1), (x0, ground(x0, z0), z0)


def kit_entries():
    gate, gate_yaw = gate_frame()
    return {
        "EP_BasaltStep": [(p, y, 1.0) for p, y in step_positions()],
        "EP_EmberGate": [(gate, gate_yaw, 1.0)],
        "EP_GateFire": [(gate, gate_yaw, 1.0)],
    }


def write_placements(extra_kit=None, path=W.REPO + "/src/worldbuild/Placements/EmberPeak.lua"):
    kit = kit_entries()
    for name, entries in (extra_kit or {}).items():
        kit.setdefault(name, []).extend(entries)
    lines = ["-- Generated by tools/blender/world/ember_meshes.py. Do not edit by hand.",
             "-- Island-local Roblox studs. Kit entries place each piece's authored origin.", "return {", "    Kit = {"]
    for name in sorted(kit):
        lines.append("        %s = {" % name)
        for (x, y, z), yaw, scale in kit[name]:
            extra = ", Scale = %.3f" % scale if abs(scale - 1) > 1e-6 else ""
            lines.append("            { Position = Vector3.new(%.2f, %.2f, %.2f), Yaw = %.4f%s }," % (x, y, z, yaw, extra))
        lines.append("        },")
    lines.append("    },")
    lx, lz = E.LANDING[0], E.LANDING[1]
    lines.append("    Checkpoint = Vector3.new(%.2f, %.2f, %.2f)," % (lx, ground(lx, lz) + 0.5, lz))
    lines.append("    Relics = {")
    for rid, (x, y, z) in relic_positions().items():
        lines.append("        %s = Vector3.new(%.2f, %.2f, %.2f)," % (rid, x, y, z))
    lines.append("    },")
    lip, src = lavafall_lip()
    lines.append("    Lavafall = { Lip = Vector3.new(%.2f, %.2f, %.2f), From = Vector3.new(%.2f, %.2f, %.2f) }," % (lip + src))
    lines += ["}", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def export():
    island, kit, img = build()
    out = W.REPO + "/assets/world/EmberPeak/"
    W.export_batch(island, out + "EmberPeak_Island.fbx", image=img, anchor_name="EP_Anchor")
    W.export_batch(kit, out + "EmberPeak_Kit.fbx", anchor_name="EP_KitAnchor")
    write_placements()
    return island + kit
