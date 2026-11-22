"""jade_lib_plan: draws Jade Grove's plan and cross-sections from the project's own data (2026-11-22). Plain Python; the picture is an SVG over a raster
of the terrain, turned into a PNG by headless Chrome (the way tools/world_map.py does it: no other dependency).

    python3 jade_lib_plan.py plan [out.png]        the whole island from above, north up, east right (island-local studs), old rim dashed
    python3 jade_lib_plan.py section <name> [out]  a cross-section along a named line (see SECTIONS)

Colours are the game's terrain colours (WorldBuilder.MaterialColors), hill-shaded; water, paths, bridges, falls, hidden places and the protected
discs are drawn over them.
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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jade_lib_island as I  # noqa: E402
import jade_lib_oldmap as O  # noqa: E402

REPO = O.REPO
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
COLOURS = {"LeafyGrass": (64, 116, 58), "Mud": (86, 68, 50), "Sandstone": (98, 124, 108)}
GOLD, CREAM = "#e9d49a", "#f4efe2"


def png_rgba(width, height, rows):
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def label(x, z, text, size, colour=CREAM, weight="600", anchor="middle", opacity=1.0):
    return ('<text x="%.1f" y="%.1f" font-size="%.1f" font-weight="%s" fill="%s" fill-opacity="%.2f" text-anchor="%s" paint-order="stroke" stroke="#0a0f1e" '
            'stroke-width="%.1f" stroke-linejoin="round">%s</text>' % (x, z, size, weight, colour, opacity, anchor, size * 0.28, esc(text)))


def fast_cells(half=I.HALF, cell=I.CELL, sample=None):
    """{(i, j): (height, material)} for cell centres over island-local x, z in -half..half, one sample per cell."""
    sample = sample or I.height
    out = {}
    n = int(2 * half / cell)
    for j in range(n):
        for i in range(n):
            x = -half + (i + 0.5) * cell
            z = -half + (j + 0.5) * cell
            h, m = sample(x, z)
            if h is not None:
                out[(i, j)] = (h, m)
    return out, n


def shade(colour, hn):
    e, w, s, n = hn
    slope = ((w - e) + (n - s)) * 0.5
    k = max(0.62, min(1.5, 1.0 + 0.09 * slope))
    return tuple(max(0, min(255, int(c * k))) for c in colour)


def raster(cells, n, px=4, water=None, extra=None):
    rows = []
    for rj in range(n * px):
        j = rj // px
        row = bytearray()
        for ri in range(n * px):
            i = ri // px
            c = cells.get((i, j))
            if c is None:
                row += b"\x00\x00\x00\x00"
                continue
            h, m = c

            def hh(di, dj):
                o = cells.get((i + di, j + dj))
                return o[0] if o else h
            rgb = shade(COLOURS.get(m, (120, 120, 126)), (hh(1, 0), hh(-1, 0), hh(0, 1), hh(0, -1)))
            # height tint: low ground (gorges, ponds) bluer, the plateau paler
            if water and water(i * 4 - I.HALF + 2, j * 4 - I.HALF + 2):
                rgb = (60, 140, 160)
            row += bytes(rgb + (255,))
        rows.append(row)
    return png_rgba(n * px, n * px, rows)


def render_svg(path, svg, w, h, width):
    work = tempfile.mkdtemp()
    sp = os.path.join(work, "plan.svg")
    with open(sp, "w", encoding="utf8") as f:
        f.write(svg)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    height = int(width * h / w)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--user-data-dir=" + os.path.join(work, "profile"),
                    "--window-size=%d,%d" % (width, height), "--force-device-scale-factor=1", "--screenshot=" + path, "file://" + sp], check=True, capture_output=True, timeout=240)
    print("wrote", path, "(%d x %d)" % (width, height))


def polyline(pts, colour, width, dash=None, opacity=1.0, cap="round"):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return '<polyline points="%s" fill="none" stroke="%s" stroke-width="%.1f"%s stroke-opacity="%.2f" stroke-linecap="%s" stroke-linejoin="round"/>' % (
        " ".join("%.1f,%.1f" % p for p in pts), colour, width, d, opacity, cap)


def plan(out, overlay=None, title="JADE GROVE - plan from the data", width=2400, sites=None):
    cells, n = fast_cells()
    png = raster(cells, n, 4, water=overlay.get("water") if overlay else None)
    H = I.HALF
    W = 2 * H
    parts = ['<defs><radialGradient id="sky" cx="50%%" cy="45%%" r="80%%"><stop offset="0" stop-color="#1b2748"/><stop offset="1" stop-color="#090d1a"/></radialGradient></defs>',
             '<rect x="%d" y="%d" width="%d" height="%d" fill="url(#sky)"/>' % (-H - 20, -H - 70, W + 40, W + 90)]
    # grid lines every 50 studs
    for g in range(-200, 201, 50):
        parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#ffffff" stroke-opacity="0.07" stroke-width="0.6"/>' % (g, -H, g, H))
        parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#ffffff" stroke-opacity="0.07" stroke-width="0.6"/>' % (-H, g, H, g))
        parts.append(label(g, -H + 8, str(g), 5.5, "#8fa0c8", "500", opacity=0.8))
        parts.append(label(-H + 4, g + 2, str(g), 5.5, "#8fa0c8", "500", "start", 0.8))
    parts.append('<image x="%d" y="%d" width="%d" height="%d" href="data:image/png;base64,%s"/>' % (-H, -H, W, W, base64.b64encode(png).decode()))
    # the old rim (dashed) and the protected discs
    old = [(math.cos(a) * OLD_R(a), math.sin(a) * OLD_R(a)) for a in [math.radians(d) for d in range(0, 361, 3)]]
    parts.append(polyline(old, "#ffffff", 0.8, "3 3", 0.6))
    for (cx, cz, r) in I.PROTECT:
        parts.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="#ffd76a" stroke-opacity="0.35" stroke-width="0.7" stroke-dasharray="2 2"/>' % (cx, cz, r))
    if overlay:
        parts.extend(overlay["svg"])
    parts.append(label(-H + 8, -H - 40, title, 11, "#ffffff", "800", "start"))
    parts.append(label(-H + 8, -H - 26, "north up, east right; island-local studs, the arena's centre at 0,0; dashed white = the old rim; dotted gold = ground that does not change", 6, "#9fb0d6", "500", "start"))
    render_svg(out, '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="%d %d %d %d" font-family="Helvetica Neue, Arial, sans-serif">%s</svg>'
               % (width, int(width * (W + 90) / (W + 40)), -H - 20, -H - 70, W + 40, W + 90, "\n".join(parts)), W + 40, W + 90, width)
    return cells


def OLD_R(a):
    return I.OLD.rim(a)


def overlay_for(pl):
    """SVG overlay for a finished Plan: the forest, the structures, ways, water, bridges, falls, lights and the hidden places."""
    import jade_lib_forest as F
    svg = []
    # water
    def water(i, j):
        return False
    for st in pl.water["streams"]:
        svg.append(polyline([(p[0], p[1]) for p in st["pts"]], "#5fd0ff", st["width"] * 0.9, None, 0.85))
    for d in pl.water["discs"]:
        svg.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#5fd0ff" fill-opacity="0.8" stroke="#bff0ff" stroke-width="0.8"/>' % (d["x"], d["z"], d["r"]))
    # rift
    svg.append(polyline(I.RIFT, "#0a0f1e", 26, None, 0.35, "butt"))
    # trails and hidden ways
    for name, line in pl.paths["Trails"].items():
        svg.append(polyline(line, "#c8a070", 3.0, None, 0.9))
    for name, line in pl.paths["Hidden"].items():
        svg.append(polyline(line, "#ffe8b0", 1.6, "1 4", 0.9))
    # the forest
    colours = {"Tree": "#0d3b2a", "Bamboo": "#d8e66a", "Rock": "#b9bcc0", "Plant": "#ff9ec0", "Mush": "#6af0d0", "Log": "#7a5a3c", "Moss": "#4f8a3c", "Vine": "#2f7d4a"}
    for piece, lst in pl.place.items():
        kind = piece.split("_")[1]
        col = colours.get(kind)
        if not col:
            continue
        r = {"Tree": 3.0, "Bamboo": 2.2, "Rock": 1.8, "Plant": 0.9, "Mush": 0.9, "Log": 1.2, "Moss": 0.7, "Vine": 1.0}[kind]
        if piece == "JG_Tree_Guardian":
            r = 9
        for e in lst:
            svg.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" fill-opacity="0.78"/>' % (e["x"], e["z"], r, col))
    # structures
    for piece, lst in pl.place.items():
        kind = piece.split("_")[1]
        if kind in ("Shrine", "Lookout", "Hidden", "Hermitage", "Gate", "Cliff"):
            for e in lst:
                svg.append('<rect x="%.1f" y="%.1f" width="9" height="9" fill="#ffd76a" stroke="#0a0f1e" stroke-width="1.2"/>' % (e["x"] - 4.5, e["z"] - 4.5))
    # bridges
    for name, b in pl.bridges.items():
        svg.append(polyline([b["A"], b["B"]], "#e9c27a", 4.2, None, 1.0, "butt"))
    # falls and lights
    for f in pl.falls:
        svg.append('<circle cx="%.1f" cy="%.1f" r="3.2" fill="#ffffff" stroke="#2a8fd0" stroke-width="1.4"/>' % (f["lip"][0], f["lip"][2]))
    for l in pl.lights:
        svg.append('<circle cx="%.1f" cy="%.1f" r="2.4" fill="#fff08a" stroke="#0a0f1e" stroke-width="0.8"/>' % (l["x"], l["z"]))
    # hidden places and labels
    for name, (x, y, z, note) in pl.spots.items():
        svg.append('<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="#ff5a5a" stroke="#fff" stroke-width="1"/>' % (x, z - 6, x + 6, z, x, z + 6, x - 6, z))
        svg.append(label(x, z - 9, name, 6.2, "#ffffff", "700"))
    for name, (x, z, t) in {"ARENA": (0, -2, "MANTIS ARENA"), "GATE": (I.GATE[0], I.GATE[1] - 6, "Grove Gate"), "GLADE": (I.GLADE[0], I.GLADE[1] - 20, "Bloom Glade"),
                           "HERM": (I.HERMITAGE[0], I.HERMITAGE[1] - 16, "Hermitage"), "HOLLOW": (I.HOLLOW[0] - 4, I.HOLLOW[1] - 20, "Hollow"), "ELDER": (I.ELDER[0], I.ELDER[1] - 26, "Guardian Tree"),
                           "RUINS": (I.RUINS[0], I.RUINS[1] + 24, "Ruin Court"), "PLATEAU": (I.PLATEAU_C[0] - 10, I.PLATEAU_C[1] - 6, "MISTFALL HEIGHTS"), "POND": (I.POND[0] + 16, I.POND[1] - 14, "Spirit Pond"),
                           "RIFT": (-108, 114, "Rift of Roots"), "VAL": (I.W_VALLEY[0] - 6, I.W_VALLEY[1] + 40, "Western Valley"), "GLEN": (I.GLEN[0] + 26, I.GLEN[1] - 14, "Northern Glen"),
                           "GORGE": (-134, 8, "Mosswater Gorge")}.items():
        svg.append(label(x, z, t, 7.5 if name in ("ARENA", "PLATEAU") else 6.4, "#ffffff", "800"))
    # legend
    lx, lz = 100, -214
    items = [("#0d3b2a", "trees"), ("#d8e66a", "bamboo"), ("#b9bcc0", "rocks"), ("#ff9ec0", "flowers and ferns"), ("#6af0d0", "glow-cap fungi")]
    for k, (c, t) in enumerate(items):
        svg.append('<circle cx="%d" cy="%d" r="3" fill="%s"/>' % (lx, lz + k * 10, c))
        svg.append(label(lx + 8, lz + 2 + k * 10, t, 6, "#f4efe2", "500", "start"))
    return {"svg": svg, "water": None}


def section(out, pl, line, title, marks=(), ys=3.0, width=2200):
    """A cross-section along line = ((x0, z0), (x1, z1)): the ground, the water, the structures' colliders crossing it, the bridges' decks. Height exaggerated by `ys`."""
    (x0, z0), (x1, z1) = line
    L = math.hypot(x1 - x0, z1 - z0)
    n = int(L)
    ux, uz = (x1 - x0) / L, (z1 - z0) / L
    pts = []
    for k in range(n + 1):
        x, z = x0 + ux * k, z0 + uz * k
        g = I.ground(x, z)
        pts.append((k, g))
    lo = min(g for _, g in pts if g is not None) - 4
    hi = max(g for _, g in pts if g is not None) + 22
    parts = ['<rect x="-20" y="%.1f" width="%d" height="%.1f" fill="#101a30"/>' % (-hi * ys - 10, n + 40, (hi - lo) * ys + 60)]
    poly = [(k, -g * ys) for k, g in pts if g is not None]
    parts.append('<polygon points="%s %d,%.1f %d,%.1f" fill="#3f7a3a" stroke="#9fd48a" stroke-width="0.8"/>' % (" ".join("%.1f,%.1f" % p for p in poly), poly[-1][0], -lo * ys, poly[0][0], -lo * ys))
    # colliders crossing the line (their footprint's centre within 6 studs of it)
    for c in pl.colliders:
        dx, dz = c["x"] - x0, c["z"] - z0
        along = dx * ux + dz * uz
        across = -dx * uz + dz * ux
        half = max(c["sx"], c["sz"]) / 2
        if 0 <= along <= L and abs(across) < half:
            parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#e9c27a" fill-opacity="0.55" stroke="#ffd76a" stroke-width="0.5"/>' % (
                along - (c["sx"] if c["kind"] == "cyl" else half * 2) / 2, -(c["y"] + c["sy"] / 2) * ys, half * 2 if c["kind"] != "cyl" else c["sx"], c["sy"] * ys))
    for d in pl.water["discs"]:
        dx, dz = d["x"] - x0, d["z"] - z0
        along, across = dx * ux + dz * uz, -dx * uz + dz * ux
        if abs(across) < d["r"] and 0 <= along <= L:
            h = math.sqrt(d["r"] ** 2 - across ** 2)
            parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#5fd0ff" fill-opacity="0.8"/>' % (along - h, -d["y"] * ys, 2 * h, 3 * ys))
    for name, at, hgt in marks:
        parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#fff" stroke-width="0.6" stroke-dasharray="2 2"/>' % (at, -hgt * ys, at, -hgt * ys - 14))
        parts.append(label(at, -hgt * ys - 18, name, 7, "#ffffff", "700"))
    parts.append(label(0, -hi * ys + 6, title + "  (height x%g, distance in studs; yellow = collision parts)" % ys, 8, "#ffffff", "800", "start"))
    parts.append('<line x1="0" y1="%.1f" x2="50" y2="%.1f" stroke="#fff" stroke-width="2"/>' % (-lo * ys + 16, -lo * ys + 16))
    parts.append(label(25, -lo * ys + 28, "50 studs", 7, "#fff"))
    vb = (-20, -hi * ys - 10, n + 40, (hi - lo) * ys + 60)
    render_svg(out, '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="%.1f %.1f %.1f %.1f" font-family="Helvetica Neue, Arial, sans-serif">%s</svg>' % (
        width, int(width * vb[3] / vb[2]), vb[0], vb[1], vb[2], vb[3], "\n".join(parts)), vb[2], vb[3], width)


def tint(cells):
    return cells


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "plan"
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "renders", "jade_grove_library", "plan_draft.png")
    if what == "final":
        import jade_lib_forest as F
        pl = F.build()
        cells = plan(out, overlay_for(pl), "JADE GROVE - the expanded island (plan from the data)")
        print("cells", len(cells), "area", len(cells) * 16, "ratio", round(len(cells) * 16 / 73664.0, 3))
    elif what == "sections":
        import jade_lib_forest as F
        pl = F.build()
        A = (I.PLATEAU_C[0] - I.DIR_F[0] * 36, I.PLATEAU_C[1] - I.DIR_F[1] * 36)
        B = (I.PLATEAU_C[0] + I.DIR_F[0] * 100, I.PLATEAU_C[1] + I.DIR_F[1] * 100)
        section(os.path.join(os.path.dirname(out), "section_high_falls.png"), pl, (A, B), "Cross-section: Mistfall Heights, the High Falls and grotto, the Spirit Pond", [
            ("spring", 0, 14), ("falls lip", 36 * 0.8 + 36, 15), ("grotto cliff foot", 36 + 34, 0), ("Spirit Pond", 36 + 34 + 9, 0)])
        b = pl.bridges["RootBridge"]
        mx, mz = (b["A"][0] + b["B"][0]) / 2, (b["A"][1] + b["B"][1]) / 2
        d = (b["B"][0] - b["A"][0], b["B"][1] - b["A"][1])
        Ld = math.hypot(*d)
        d = (d[0] / Ld, d[1] / Ld)
        section(os.path.join(os.path.dirname(out), "section_root_bridge.png"), pl, ((mx - d[0] * 40, mz - d[1] * 40), (mx + d[0] * 40, mz + d[1] * 40)),
                "Cross-section: the Mosswater Gorge and the living-root bridge (span 30)", [("root bridge deck", 40, b["level"])], ys=5.0, width=1800)
    elif what == "plan":
        cells = plan(out)
        print("cells", len(cells), "area", len(cells) * 16, "ratio", round(len(cells) * 16 / 73664.0, 3))
