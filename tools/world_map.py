"""Draws a top view of the whole world (north up, east right) from the project's own data:

    python3 tools/world_map.py [out.png]       (default: renders/world_map/world_map.png, local only)

Every island's footprint is read from its terrain grid (src/worldbuild/Terrain/<Island>.lua: height and material of each 4-stud cell),
coloured with the game's terrain colours (WorldBuilder.MaterialColors) and hill-shaded; the bridges come from tools/blender/world/layout.py;
Murim Crossing's plaza, stairways and three headquarters pads from src/worldbuild/Placements/MurimCrossing.lua; a few hub landmarks from
Placements/Yggdrasil.lua. The picture is an SVG over a raster of the terrain, turned into a PNG by headless Chrome (no other dependency).
No Pillow or matplotlib needed: the raster is written with zlib.
"""
import base64
import math
import os
import re
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender", "world"))
import layout as L  # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "renders", "world_map", "world_map.png")
ISLANDS = ["Yggdrasil", "BeginnerIsle", "JadeGrove", "EmberPeak", "MoonlitIsle", "OriginAbyss", "BlossomSanctuary", "MurimCrossing"]
PX = 3  # raster pixels per 4-stud cell


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf8") as f:
        return f.read()


# ---------- terrain colours ----------
def material_colours():
    text = read("src/worldbuild/WorldBuilder.lua")
    block = text[text.index("WorldBuilder.MaterialColors = {"):]
    block = block[:block.index("\n}")]
    return {m.group(1): (int(m.group(2)), int(m.group(3)), int(m.group(4)))
            for m in re.finditer(r"^\s*([A-Za-z]+) = Color3\.fromRGB\((\d+), (\d+), (\d+)\)", block, re.M)}


FALLBACK = {"Limestone": (214, 208, 196), "Pavement": (160, 164, 176), "Slate": (60, 62, 74), "Asphalt": (44, 40, 44), "Basalt": (34, 32, 38),
            "CrackedLava": (214, 86, 30), "Sand": (206, 182, 128), "Snow": (236, 242, 250), "Salt": (226, 224, 214), "Concrete": (150, 150, 152),
            "Glacier": (150, 200, 226)}


# ---------- terrain files ----------
def expand(text, off):
    out = []
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        if token.startswith("~"):
            out.extend([off] * int(token[1:]))
        elif token == "false":
            out.append(False)
        else:
            out.append(float(token))
    return out


def grid_values(text, key, off):
    m = re.search(r"\b" + key + r' = "([^"]*)"', text)
    if m:
        return expand(m.group(1), off)
    m = re.search(r"\b" + key + r" = \{(.*?)\n    \},", text, re.S)
    return expand(m.group(1).replace("\n", " "), off) if m else None


def parse_terrain(island):
    t = read("src/worldbuild/Terrain/%s.lua" % island)
    vec3 = re.search(r"Centre = Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", t)
    vec2 = re.search(r"Origin = Vector2\.new\(([-\d.]+), ([-\d.]+)\)", t)
    d = {
        "centre": (float(vec3.group(1)), float(vec3.group(3))),
        "origin": (float(vec2.group(1)), float(vec2.group(2))),
        "turns": float(re.search(r"Turns = ([-\d.]+)", t).group(1)),
        "baked": "BakedTurn = true" in t,
        "cell": int(re.search(r"Cell = (\d+)", t).group(1)),
        "size": int(re.search(r"Size = (\d+)", t).group(1)),
        "materials": re.findall(r'"([A-Za-z]+)"', re.search(r"Materials = \{([^}]*)\}", t).group(1)),
    }
    d["heights"] = grid_values(t, "Heights", False)
    d["index"] = grid_values(t, "MaterialIndex", 0)
    return d


def cells(d):
    """{(cellX, cellZ): (height, materialName)} in world cell coordinates (a cell = 4 studs, keyed by its corner / 4)."""
    n, cell = d["size"], d["cell"]
    out = {}
    cx, cz = d["centre"]
    turns = int(round(d["turns"])) % 4 if not d["baked"] else 0
    for idx, h in enumerate(d["heights"]):
        if h is False:
            continue
        i, j = idx % n, idx // n
        x = d["origin"][0] + (i + 0.5) * cell
        z = d["origin"][1] + (j + 0.5) * cell
        if turns:
            rx, rz = x - cx, z - cz
            for _ in range(turns):
                rx, rz = -rz, rx
            x, z = cx + rx, cz + rz
        mi = d["index"][idx] if d["index"] else 1
        name = d["materials"][int(mi) - 1] if mi and int(mi) - 1 < len(d["materials"]) else "Rock"
        out[(int(math.floor(x / cell)), int(math.floor(z / cell)))] = (h, name)
    return out


def shaded(colour, h, hn):
    """Hill shading: the light comes from the north-west; hn = the heights around (e, w, s, n)."""
    e, w, s, n = hn
    slope = ((w - e) + (n - s)) * 0.5
    k = max(0.62, min(1.4, 1.0 + 0.05 * slope))
    return tuple(max(0, min(255, int(c * k))) for c in colour)


def paint_all(keep=None):
    """{(cellX, cellZ): rgb}; keep(x_stud, z_stud) -> bool limits it to a region."""
    colours = dict(FALLBACK)
    colours.update(material_colours())
    allc = {}
    for island in ISLANDS:
        d = parse_terrain(island)
        cs = cells(d)
        for (cx, cz), (h, name) in cs.items():
            if keep and not keep(cx * 4 + 2, cz * 4 + 2):
                continue

            def hh(dx, dz):
                other = cs.get((cx + dx, cz + dz))
                return other[0] if other else h
            hn = (hh(1, 0), hh(-1, 0), hh(0, 1), hh(0, -1))
            allc[(cx, cz)] = shaded(colours.get(name, (120, 120, 126)), h, hn)
    return allc


def png_rgba(width, height, rows):
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


# ---------- placements ----------
def turn(v, turns):
    x, z = v
    a = math.radians(turns * 90)
    return (x * math.cos(a) - z * math.sin(a), x * math.sin(a) + z * math.cos(a))


def murim_world(local):
    c = L.ISLANDS["MurimCrossing"]["centre"]
    x, z = turn(local, L.ISLANDS["MurimCrossing"]["turns"])
    return (c[0] + x, c[2] + z)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def label(x, z, text, size, colour="#f4efe2", weight="600", anchor="middle", opacity=1.0):
    return ('<text x="%.1f" y="%.1f" font-size="%d" font-weight="%s" fill="%s" fill-opacity="%.2f" text-anchor="%s" '
            'paint-order="stroke" stroke="#0a0f1e" stroke-width="%.1f" stroke-linejoin="round">%s</text>'
            % (x, z, size, weight, colour, opacity, anchor, size * 0.28, esc(text)))




FACTIONS = {"Orthodox": ("#5fa8ff", "Dawnspire Hall"), "Unorthodox": ("#46c896", "Windrift Hold"), "Demonic": ("#e23430", "Nightfall Citadel")}
GOLD, CREAM = "#e9d49a", "#f4efe2"


def vec(m):
    return (float(m[0]), float(m[2]))


def lua_vectors(text):
    return [(float(a), float(c)) for a, _, c in re.findall(r"Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", text)]


def background(x0, z0, W, H, grid=True, step=200):
    parts = ['<defs><radialGradient id="sky" cx="50%%" cy="42%%" r="80%%"><stop offset="0" stop-color="#1b2748"/><stop offset="1" stop-color="#090d1a"/></radialGradient></defs>',
             '<rect x="%d" y="%d" width="%d" height="%d" fill="url(#sky)"/>' % (x0, z0, W, H)]
    if grid:
        gx = int(math.ceil(x0 / float(step))) * step
        while gx < x0 + W:
            parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#ffffff" stroke-opacity="0.07" stroke-width="2"/>' % (gx, z0, gx, z0 + H))
            parts.append(label(gx, z0 + 78, str(gx), 26, "#8fa0c8", "500", opacity=0.8))
            gx += step
        gz = int(math.ceil(z0 / float(step))) * step
        while gz < z0 + H:
            parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#ffffff" stroke-opacity="0.07" stroke-width="2"/>' % (x0, gz, x0 + W, gz))
            parts.append(label(x0 + 14, gz - 8, str(gz), 26, "#8fa0c8", "500", "start", 0.8))
            gz += step
    return parts


def raster_image(allc, px):
    xs = [k[0] for k in allc]
    zs = [k[1] for k in allc]
    cx0, cx1, cz0, cz1 = min(xs), max(xs), min(zs), max(zs)
    ncols, nrows = cx1 - cx0 + 1, cz1 - cz0 + 1
    rows = []
    for rz in range(nrows * px):
        row = bytearray()
        cz = cz0 + rz // px
        for rx in range(ncols * px):
            c = allc.get((cx0 + rx // px, cz))
            row += bytes(c + (255,)) if c else b"\x00\x00\x00\x00"
        rows.append(row)
    png = png_rgba(ncols * px, nrows * px, rows)
    return '<image x="%d" y="%d" width="%d" height="%d" href="data:image/png;base64,%s"/>' % (
        cx0 * 4, cz0 * 4, ncols * 4, nrows * 4, base64.b64encode(png).decode()), (cx0 * 4, (cx1 + 1) * 4, cz0 * 4, (cz1 + 1) * 4)


def bridge_lines():
    out = []
    for b in L.BRIDGES.values():
        (sx, _, sz), (ex, _, ez) = b["start"], b["end"]
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#2a2216" stroke-width="46"/>' % (sx, sz, ex, ez))
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="36"/>' % (sx, sz, ex, ez, GOLD))
    return out


# ---------- the whole world ----------
def world_map():
    allc = paint_all()
    img, (bx0, bx1, bz0, bz1) = raster_image(allc, PX)
    M = 100
    x0, x1, z0, z1 = bx0 - M, bx1 + M, bz0 - M - 80, bz1 + M + 40
    W, H = x1 - x0, z1 - z0
    parts = background(x0, z0, W, H)
    parts.append(img)
    parts += bridge_lines()
    # the Blossom Sanctuary's stepping stones: a dotted line from the hub's south-east verge
    d = math.hypot(452.0, 380.0)
    ux, uz = 452.0 / d, 380.0 / d
    parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="18" stroke-dasharray="8 22" stroke-linecap="round"/>'
                 % (245 * ux, 245 * uz, 392 * ux, 392 * uz, GOLD))
    # Murim Crossing: the plaza, the stairways, the three pads
    P = read("src/worldbuild/Placements/MurimCrossing.lua")
    parts.append('<circle cx="%.1f" cy="%.1f" r="76" fill="none" stroke="#ffffff" stroke-opacity="0.6" stroke-width="4" stroke-dasharray="14 10"/>' % murim_world((0, 0)))
    for name, (colour, hq) in FACTIONS.items():
        m = re.search(name + r" = \{\s*Centre = Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\), Height = ([\d.]+), FlatRadius = ([\d.]+)", P)
        local = (float(m.group(1)), float(m.group(3)))
        fr = float(m.group(5))
        ang = math.atan2(local[1], local[0])
        a = murim_world((76 * math.cos(ang), 76 * math.sin(ang)))
        b = murim_world((local[0] - fr * math.cos(ang), local[1] - fr * math.sin(ang)))
        parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="20" stroke-opacity="0.9"/>' % (a + b + (colour,)))
        px, pz = murim_world(local)
        parts.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" fill-opacity="0.28" stroke="%s" stroke-width="5"/>' % (px, pz, fr, colour, colour))
    # labels for the three headquarters, set outside the island on leader lines
    callouts = {"Orthodox": (110, 905), "Unorthodox": (-244, 985), "Demonic": (-560, 905)}
    for name, (colour, hq) in FACTIONS.items():
        m = re.search(name + r" = \{\s*Centre = Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", P)
        px, pz = murim_world((float(m.group(1)), float(m.group(3))))
        lx, lz = callouts[name]
        parts.append('<line x1="%.1f" y1="%.1f" x2="%d" y2="%d" stroke="%s" stroke-width="3" stroke-opacity="0.8"/>' % (px, pz, lx, lz - 34, colour))
        parts.append(label(lx, lz, hq, 30, colour, "800"))
        parts.append(label(lx, lz + 28, name + " faction", 20, CREAM, "500"))
    # hub landmarks
    hub = [(0, 0, "World Tree", "#9ee6ff", -14), (0, -178, "Hatching Sanctum", CREAM, -14), (0, -120, "Wandering Merchant", CREAM, -14),
           (235, -194, "Blacksmith", CREAM, -14), (304, -142, "Auction House", CREAM, -14), (289, -54, "Buy & Sell", CREAM, -14),
           (254, -15, "Spin Wheel", CREAM, 30), (-149, 82, "Hall of Records", CREAM, -14), (0, 176, "Arrival Plaza", CREAM, -14)]
    for x, z, text, colour, dy in hub:
        parts.append('<circle cx="%d" cy="%d" r="7" fill="#ffd76a" stroke="#0a0f1e" stroke-width="3"/>' % (x, z))
        parts.append(label(x, z + dy, text, 22, colour, "600"))
    for sx, sz in [(60, 103.92), (-60, 103.92), (-120, 0), (-60, -103.92), (60, -103.92), (120, 0)]:
        parts.append('<circle cx="%.1f" cy="%.1f" r="14" fill="none" stroke="#ffd76a" stroke-width="4"/>' % (sx, sz))
    parts.append(label(0, 50, "6 beast pens", 20, "#ffd76a", "500"))
    names = {
        "Yggdrasil": ((-380, 215), "YGGDRASIL", "the hub"),
        "BeginnerIsle": ((-480, -150), "BEGINNER ISLE", "open from the start - Stone Lion"),
        "JadeGrove": ((-420, -635), "JADE GROVE", "gate: Qi Gatherer - Bamboo Mantis Sage"),
        "EmberPeak": ((-128, -880), "EMBER PEAK", "gate: Qi Awakener - Ember Xuanwu"),
        "MoonlitIsle": ((192, -985), "MOONLIT ISLE", "gate: Soul Awakening - Tiangou"),
        "OriginAbyss": ((560, -1070), "ORIGIN ABYSS", "gate: Divine Initiate - Pangu"),
        "BlossomSanctuary": ((490, 700), "BLOSSOM SANCTUARY", "Training Ground +50% Qi - stepping stones, open to all"),
        "MurimCrossing": ((-215, 410), "MURIM CROSSING", "open to all"),
    }
    for key, ((x, z), title, sub) in names.items():
        anchor = "end" if key == "MurimCrossing" else "middle"
        parts.append(label(x, z, title, 40, "#ffffff", "800", anchor))
        parts.append(label(x, z + 30, sub, 22, "#c9d6f2", "500", anchor))
    parts.append(label(-215, 464, "join a faction from Qi Foundation", 22, "#c9d6f2", "500", "end"))
    for name in L.BRIDGES:
        b = L.BRIDGES[name]
        mx, mz = b["start"][0] * 0.82 + b["end"][0] * 0.18, b["start"][2] * 0.82 + b["end"][2] * 0.18
        parts.append('<circle cx="%.1f" cy="%.1f" r="9" fill="#ffd76a" stroke="#0a0f1e" stroke-width="3"/>' % (mx, mz))
    # title, compass, scale, legend (the bottom right and left corners: nothing else is there)
    parts.append(label(x0 + 60, z0 + 130, "STEAL A SPIRIT EGG - WORLD MAP", 52, "#ffffff", "800", "start"))
    parts.append(label(x0 + 60, z0 + 172, "top view from the project's terrain and layout data - north is up, east is right", 24, "#9fb0d6", "500", "start"))
    cxp, czp = -520, -820
    parts.append('<circle cx="%d" cy="%d" r="52" fill="none" stroke="#c9d6f2" stroke-width="3"/><path d="M %d %d L %d %d L %d %d Z" fill="#ffffff"/>'
                 % (cxp, czp, cxp, czp - 52, cxp - 14, czp + 4, cxp + 14, czp + 4))
    parts.append(label(cxp, czp - 64, "N", 30, "#ffffff", "800"))
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#ffffff" stroke-width="8"/>' % (x1 - 360, z1 - 130, x1 - 160, z1 - 130))
    parts.append(label(x1 - 260, z1 - 146, "200 studs", 26, "#ffffff", "600"))
    lg, lz = 230, 790
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="18"/>' % (lg, lz, lg + 90, lz, GOLD))
    parts.append(label(lg + 110, lz + 8, "bridge (40 studs wide), gold dot = gate", 22, CREAM, "500", "start"))
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="12" stroke-dasharray="6 16" stroke-linecap="round"/>' % (lg, lz + 44, lg + 90, lz + 44, GOLD))
    parts.append(label(lg + 110, lz + 52, "stepping stones", 24, CREAM, "500", "start"))
    return W, H, x0, z0, "\n".join(parts), 2600


# ---------- Murim Crossing, close up, the way a player sees it from the bridge: the hub behind, the headquarters ahead ----------
def murim_detail():
    cx, cz = L.ISLANDS["MurimCrossing"]["centre"][0], L.ISLANDS["MurimCrossing"]["centre"][2]
    a = math.radians(L.ISLANDS["MurimCrossing"]["turns"] * 90)
    ca, sa = math.cos(a), math.sin(a)
    # screen = rotate the world so island-local -Z (the hub) points down and local +X (the player's left) points left
    mat = (-ca, sa, -sa, -ca)  # a b c d of an SVG matrix
    e = -mat[0] * cx - mat[2] * cz
    f = -mat[1] * cx - mat[3] * cz

    def scr(local):  # island-local (x, z) -> screen
        return (-local[0], -local[1])

    def keep(x, z):
        lx = (x - cx) * ca + (z - cz) * sa
        lz = -(x - cx) * sa + (z - cz) * ca
        return -330 < lx < 330 and -190 < lz < 420
    allc = paint_all(keep)
    img, _ = raster_image(allc, 8)
    x0, x1, z0, z1 = -300, 300, -420, 290
    W, H = x1 - x0, z1 - z0
    parts = background(x0, z0, W, H, grid=False)
    parts.append('<g transform="matrix(%.6f %.6f %.6f %.6f %.3f %.3f)">%s' % (mat[0], mat[1], mat[2], mat[3], e, f, img))
    parts.append("".join(bridge_lines()) + "</g>")
    P = read("src/worldbuild/Placements/MurimCrossing.lua")
    # plaza ring and the oath stone
    parts.append('<circle cx="0" cy="0" r="76" fill="none" stroke="#ffffff" stroke-opacity="0.7" stroke-width="2.5" stroke-dasharray="9 7"/>')
    parts.append('<circle cx="0" cy="0" r="5" fill="#ffd76a" stroke="#0a0f1e" stroke-width="2"/>')
    parts.append(label(0, -12, "oath stone", 11, CREAM, "600"))
    parts.append(label(0, 100, "PLAZA (radius 76)", 12, "#c9d6f2", "600"))
    parts.append(label(-30, 168, "bridge from the hub", 13, GOLD, "600", "end"))
    parts.append(label(-30, 184, "(245 studs, open to all)", 11, GOLD, "500", "end"))
    parts.append('<line x1="0" y1="118" x2="0" y2="205" stroke="%s" stroke-width="22" stroke-opacity="0.9"/>' % GOLD)
    parts.append(label(36, 124, "island gate", 11, CREAM, "600", "start"))
    pad_labels = []
    for name, (colour, hq) in FACTIONS.items():
        m = re.search(name + r" = \{\s*Centre = Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\), Height = ([\d.]+), FlatRadius = ([\d.]+), EdgeRadius = ([\d.]+)", P)
        c = (float(m.group(1)), float(m.group(3)))
        h, fr, er = float(m.group(4)), float(m.group(5)), float(m.group(6))
        sx, sz = scr(c)
        ang = math.atan2(c[1], c[0])
        a0 = scr((76 * math.cos(ang), 76 * math.sin(ang)))
        a1 = scr((c[0] - fr * math.cos(ang), c[1] - fr * math.sin(ang)))
        parts.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-opacity="0.45" stroke-width="2" stroke-dasharray="5 5"/>' % (sx, sz, er, colour))
        parts.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" fill-opacity="0.22" stroke="%s" stroke-width="3"/>' % (sx, sz, fr, colour, colour))
        parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="16" stroke-opacity="0.75"/>' % (a0 + a1 + (colour,)))
        pad_labels.append(label(sx, sz + 4, hq, 17, colour, "800"))
        pad_labels.append(label(sx, sz + 19, "%s pad, +%d studs" % (name, h), 11, CREAM, "500"))
        # main hall and vault spots, the representative, the banner pole
        pads_block = P[P.index("    Pads = {"):]
        mh = re.search(name + r" = \{\s*Centre.*?MainHall = \{ Position = Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\).*?Vault = \{ Position = Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", pads_block, re.S)
        if mh:
            hx, hz = scr((float(mh.group(1)), float(mh.group(3))))
            vx, vz = scr((float(mh.group(4)), float(mh.group(6))))
            parts.append('<rect x="%.1f" y="%.1f" width="12" height="12" fill="%s" stroke="#0a0f1e" stroke-width="2"/>' % (hx - 6, hz - 6, colour))
            parts.append('<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="#ffd76a" stroke="#0a0f1e" stroke-width="2"/>'
                         % (vx, vz - 7, vx + 7, vz, vx, vz + 7, vx - 7, vz))
        rep = re.search(r"Reps = \{.*?" + name + r" = \{ Position = Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", P, re.S)
        if rep:
            rx, rz = scr((float(rep.group(1)), float(rep.group(3))))
            parts.append('<circle cx="%.1f" cy="%.1f" r="5" fill="%s" stroke="#fff" stroke-width="2"/>' % (rx, rz, colour))
    parts.extend(pad_labels)
    # the Orthodox trial gates (five, up its stair), the Unorthodox hidden paths, nooks, rope bridges
    tg = re.search(r"Orthodox = \{.*?TrialGates = \{(.*?)\},\n", P, re.S)
    if tg:
        pts = [scr(v) for v in lua_vectors(tg.group(1))]
        for i, (x, z) in enumerate(pts):
            parts.append('<circle cx="%.1f" cy="%.1f" r="4.5" fill="none" stroke="#ffffff" stroke-width="2"/>' % (x, z))
    paths = re.search(r"Paths = \{(.*?)\n    \},", P, re.S)
    if paths:
        for line in re.findall(r"\{ (Vector3.*?) \}", paths.group(1)):
            pts = [scr(v) for v in lua_vectors(line)]
            parts.append('<polyline points="%s" fill="none" stroke="#46c896" stroke-width="3" stroke-dasharray="6 4"/>' % " ".join("%.1f,%.1f" % q for q in pts))
    nooks = re.search(r"Nooks = \{(.*?)\n    \},", P, re.S)
    for v in lua_vectors(nooks.group(1)):
        x, z = scr(v)
        parts.append('<circle cx="%.1f" cy="%.1f" r="6" fill="#46c896" stroke="#0a0f1e" stroke-width="2"/>' % (x, z))
    for m in re.finditer(r"From = Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\), To = Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", P):
        p0, p1 = scr((float(m.group(1)), float(m.group(3)))), scr((float(m.group(4)), float(m.group(6))))
        parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#e9c27a" stroke-width="4"/>' % (p0 + p1))
    for m in re.finditer(r"Lip = Vector3\.new\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", P):
        x, z = scr((float(m.group(1)), float(m.group(3))))
        parts.append('<circle cx="%.1f" cy="%.1f" r="5" fill="#8fd8ff" stroke="#0a0f1e" stroke-width="2"/>' % (x, z))
    # legend and title
    parts.append(label(x0 + 14, z0 + 30, "MURIM CROSSING - top view, from the bridge", 20, "#ffffff", "800", "start"))
    parts.append(label(x0 + 14, z0 + 50, "the hub is behind you (bottom), the three headquarters are ahead (top); Orthodox is on your left", 12, "#9fb0d6", "500", "start"))
    ly = z1 - 92
    items = [('<rect x="%d" y="%d" width="12" height="12" fill="#ffffff" stroke="#0a0f1e" stroke-width="2"/>' % (x0 + 16, ly - 10), "main hall site"),
             ('<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="#ffd76a" stroke="#0a0f1e" stroke-width="2"/>' % (x0 + 22, ly + 8, x0 + 29, ly + 15, x0 + 22, ly + 22, x0 + 15, ly + 15), "faction vault site"),
             ('<circle cx="%d" cy="%d" r="5" fill="#ffffff"/>' % (x0 + 22, ly + 38), "faction representative"),
             ('<circle cx="%d" cy="%d" r="4.5" fill="none" stroke="#ffffff" stroke-width="2"/>' % (x0 + 22, ly + 58), "Orthodox trial gates (5, up the stairway)")]
    for k, (shape, text) in enumerate(items):
        parts.append(shape)
        parts.append(label(x0 + 38, ly + 3 + k * 20 if k == 0 else ly + 18 + (k - 1) * 20 + 4, text, 12, CREAM, "500", "start"))
    lx = x1 - 250
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#46c896" stroke-width="3" stroke-dasharray="6 4"/>' % (lx, ly, lx + 30, ly))
    parts.append(label(lx + 40, ly + 4, "Unorthodox hidden paths", 12, CREAM, "500", "start"))
    parts.append('<circle cx="%d" cy="%d" r="6" fill="#46c896" stroke="#0a0f1e" stroke-width="2"/>' % (lx + 15, ly + 20))
    parts.append(label(lx + 40, ly + 24, "hidden lookouts (4)", 12, CREAM, "500", "start"))
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#e9c27a" stroke-width="4"/>' % (lx, ly + 40, lx + 30, ly + 40))
    parts.append(label(lx + 40, ly + 44, "rope bridges (2)", 12, CREAM, "500", "start"))
    parts.append('<circle cx="%d" cy="%d" r="5" fill="#8fd8ff" stroke="#0a0f1e" stroke-width="2"/>' % (lx + 15, ly + 60))
    parts.append(label(lx + 40, ly + 64, "waterfall lips (3)", 12, CREAM, "500", "start"))
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#ffffff" stroke-width="3"/>' % (x1 - 120, z0 + 40, x1 - 20, z0 + 40))
    parts.append(label(x1 - 70, z0 + 32, "100 studs", 12, "#ffffff", "600"))
    return W, H, x0, z0, "\n".join(parts), 2200


def render(path, W, H, x0, z0, body, width):
    height = int(width * H / W)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="%d %d %d %d" '
           'font-family="Helvetica Neue, Arial, sans-serif">%s</svg>' % (width, height, x0, z0, W, H, body))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    work = tempfile.mkdtemp()
    svg_path = os.path.join(work, "map.svg")
    with open(svg_path, "w", encoding="utf8") as f:
        f.write(svg)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--user-data-dir=" + os.path.join(work, "profile"),
                    "--window-size=%d,%d" % (width, height), "--force-device-scale-factor=1", "--screenshot=" + path, "file://" + svg_path],
                   check=True, capture_output=True, timeout=180)
    print("wrote", path, "(%d x %d)" % (width, height))


def main():
    render(OUT, *world_map())
    render(os.path.join(os.path.dirname(OUT), "murim_crossing_top_view.png"), *murim_detail())


if __name__ == "__main__":
    main()
