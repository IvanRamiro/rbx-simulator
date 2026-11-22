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


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "plan"
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "renders", "jade_grove_library", "plan_draft.png")
    if what == "plan":
        cells = plan(out)
        print("cells", len(cells), "area", len(cells) * 16, "ratio", round(len(cells) * 16 / 73664.0, 3))
