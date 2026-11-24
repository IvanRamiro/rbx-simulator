"""Windrift Hold's top-down plan and cross-sections, drawn from the real terrain data (murim_layout's grid, the one that is written to
src/worldbuild/Terrain/MurimCrossing.lua) and, once windrift.py exists, its buildings, stairs, bridges, paths, spots and plants.
Picture: the pad's frame (the island's, shifted: x = island-local x, z = island-local z - 250), +z (toward the cliff and the falls) at the top, +x (the player's left)
at the left. An SVG over a raster of the terrain, turned into PNGs by headless Chrome (as tools/blender/world/world_map.py does).

    python3 tools/blender/world/windrift_plan.py            # renders/windrift/plan_topdown.png
    python3 tools/blender/world/windrift_plan.py --sections # renders/windrift/section_*.png
"""
import base64
import math
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "tools"))

import murim_layout as M  # noqa: E402
import murim_windrift_terrain as DT  # noqa: E402
import world_map as WM  # noqa: E402

OUT = os.path.join(REPO, "renders", "windrift")
X0, X1, Z0, Z1 = -75.0, 75.0, -58.0, 92.0       # the plan's window, pad frame
PX = 8                                             # screen pixels per stud
COLOURS = dict(WM.FALLBACK)
COLOURS.update(WM.material_colours())


def world_of(x, z):
    lx, lz = DT.to_local(x, z)
    return M.to_world(lx, lz)


_GRID = {}


def grid():
    if not _GRID:
        ox, oz, n, H, Mi, B, U = M.sample_grid()
        _GRID.update(ox=ox, oz=oz, n=n, H=H, M=Mi, B=B)
    return _GRID


def cell(x, z):
    """(height, material name, bottom) of the terrain cell under a pad-frame point, or None."""
    g = grid()
    wx, wz = world_of(x, z)
    i, j = int((wx - g["ox"]) // M.CELL), int((wz - g["oz"]) // M.CELL)
    if not (0 <= i < g["n"] and 0 <= j < g["n"]):
        return None
    k = j * g["n"] + i
    if g["H"][k] is None:
        return None
    return g["H"][k], M.MATERIALS[g["M"][k] - 1], g["B"][k]


def height(x, z):
    c = cell(x, z)
    return None if c is None else c[0]


def png_image():
    w, h = int((X1 - X0)), int((Z1 - Z0))
    rows = []
    for j in range(h):
        z = Z1 - j - 0.5
        row = bytearray()
        for i in range(w):
            x = X1 - i - 0.5
            c = cell(x, z)
            if c is None:
                row += bytes((16, 22, 40, 255))
                continue
            hgt, mat, _ = c
            base = COLOURS.get(mat, (120, 120, 126))
            hl = height(x + 1.5, z)
            hr = height(x - 1.5, z)
            hu = height(x, z + 1.5)
            hd = height(x, z - 1.5)
            sl = (((hl if hl is not None else hgt) - (hr if hr is not None else hgt)) + ((hu if hu is not None else hgt) - (hd if hd is not None else hgt))) * 0.09
            k = max(0.55, min(1.45, 1.0 + sl + (hgt - 25.0) * 0.004))
            col = [min(255, int(v * k)) for v in base]
            for q in (hl, hr, hu, hd):
                pass
            # contour every 5 studs
            a = height(x + 1.0, z)
            b = height(x, z + 1.0)
            if a is not None and b is not None and (int(hgt // 5) != int(a // 5) or int(hgt // 5) != int(b // 5)):
                col = [int(v * 0.55) for v in col]
            row += bytes(col + [255])
        rows.append(row)
    return WM.png_rgba(w, h, rows), w, h


def sx(x):
    return (X1 - x) * PX


def sz(z):
    return (Z1 - z) * PX


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def text(x, z, s, size=14, fill="#f4efe2", anchor="middle", weight="600"):
    return ('<text x="%.1f" y="%.1f" font-size="%d" font-weight="%s" fill="%s" text-anchor="%s" paint-order="stroke" stroke="#0a0f1e" stroke-width="%.1f" '
            'stroke-linejoin="round">%s</text>' % (sx(x), sz(z), size, weight, fill, anchor, size * 0.28, esc(s)))


def rect(x0, x1, z0, z1, stroke="#ffffff", fill="none", sw=2, dash="", op=1.0, r=0):
    return ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="%s" fill-opacity="%.2f" stroke="%s" stroke-width="%.1f" %s/>'
            % (sx(x1), sz(z1), (x1 - x0) * PX, (z1 - z0) * PX, r * PX, fill, op if fill != "none" else 0, stroke, sw, ('stroke-dasharray="%s"' % dash) if dash else ""))


def line(a, b, stroke="#ffffff", sw=3, dash="", op=1.0):
    return ('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f" stroke-opacity="%.2f" %s/>'
            % (sx(a[0]), sz(a[1]), sx(b[0]), sz(b[1]), stroke, sw, op, ('stroke-dasharray="%s"' % dash) if dash else ""))


def circle(x, z, r, fill="#ffffff", stroke="#0a0f1e", sw=2, op=1.0):
    return '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" fill-opacity="%.2f" stroke="%s" stroke-width="%.1f"/>' % (sx(x), sz(z), r * PX, fill, op, stroke, sw)


def render_svg(body, path, W, H):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="Helvetica Neue, Arial, sans-serif">%s</svg>'
           % (W, H, W, H, body))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    work = tempfile.mkdtemp()
    p = os.path.join(work, "plan.svg")
    open(p, "w", encoding="utf8").write(svg)
    subprocess.run([WM.CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--user-data-dir=" + os.path.join(work, "profile"),
                    "--window-size=%d,%d" % (W, H), "--force-device-scale-factor=1", "--screenshot=" + path, "file://" + p], check=True, capture_output=True, timeout=240)
    print("wrote", path, "(%d x %d)" % (W, H))


def plan(extra=None, path=None):
    png, w, h = png_image()
    W, H = int((X1 - X0) * PX), int((Z1 - Z0) * PX)
    parts = ['<rect width="%d" height="%d" fill="#0b1226"/>' % (W, H),
             '<image x="0" y="0" width="%d" height="%d" style="image-rendering:pixelated" href="data:image/png;base64,%s"/>' % (W, H, base64.b64encode(png).decode())]
    for gx in range(int(X0 // 20) * 20, int(X1) + 1, 20):
        parts.append(line((gx, Z0), (gx, Z1), "#ffffff", 1, "", 0.12))
        parts.append(text(gx, Z0 + 3, str(gx), 11, "#cfd8f0", "middle", "500"))
    for gz in range(int(Z0 // 20) * 20, int(Z1) + 1, 20):
        parts.append(line((X0, gz), (X1, gz), "#ffffff", 1, "", 0.12))
        parts.append(text(X1 - 2, gz + 1, str(gz), 11, "#cfd8f0", "end", "500"))
    parts.append(circle(0, 0, 58, "none", "#46c896", 1.5, 0))
    s_ = DT.SLOT
    parts.append(rect(s_["x0"], s_["x1"], s_["z0"], s_["z1"], "#7ad7ff", "#0b1226", 2, "4 3", 0.55, s_["r"]))
    parts.append(text((s_["x0"] + s_["x1"]) / 2, s_["z0"] - 3, "the gorge (open sky)", 11, "#bfeaff", "middle", "700"))
    for name, t in DT.TERRACES.items():
        parts.append(rect(t["x0"], t["x1"], t["z0"], t["z1"], "#ffd76a", "none", 3, "", 1.0, t["r"]))
        parts.append(text((t["x0"] + t["x1"]) / 2, t["z1"] - 3, "%s  Y %g" % (name, t["y"]), 12, "#ffe9a8", "middle", "800"))
    for name, st in DT.STAIRS.items():
        for run in DT.stair_runs(name):
            (ax, az), (bx, bz) = run["a"], run["b"]
            parts.append(line((ax, az), (bx, bz), "#ff9a5a" if run["flight"] else "#ffd0a8", st["half"] * 2 * PX, "", 0.7))
    if extra:
        parts += extra(sx, sz)
    parts.append(text(X1 - 2, Z1 - 6, "WINDRIFT HOLD PLAN (pad frame: z up the cliff, x = the player's left; contours every 5 studs)", 13, "#ffffff", "end", "800"))
    render_svg("\n".join(parts), path or os.path.join(OUT, "plan_topdown.png"), W, H)


def section(name, a, b, solids=None, y_lo=-6.0, y_hi=100.0, path=None):
    """Terrain height along the line a -> b (pad frame), with building boxes: solids = [(label, s0, s1, y0, y1, colour)]."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    W, H = int(L * 7) + 120, int((y_hi - y_lo) * 7) + 80
    sxs = lambda s: 60 + s * 7
    sys_ = lambda y: H - 40 - (y - y_lo) * 7
    parts = ['<rect width="%d" height="%d" fill="#0b1226"/>' % (W, H)]
    for y in range(int(y_lo // 10) * 10, int(y_hi) + 1, 10):
        parts.append('<line x1="60" y1="%.1f" x2="%d" y2="%.1f" stroke="#ffffff" stroke-opacity="0.14"/>' % (sys_(y), W - 20, sys_(y)))
        parts.append('<text x="52" y="%.1f" font-size="11" fill="#cfd8f0" text-anchor="end">%d</text>' % (sys_(y) + 4, y))
    pts = []
    n = int(L * 1.0)
    for i in range(n + 1):
        s = i * L / n
        x, z = a[0] + (b[0] - a[0]) * s / L, a[1] + (b[1] - a[1]) * s / L
        c = cell(x, z)
        pts.append((s, c[0] if c else None, c[1] if c else None))
    poly, prev = [], None
    for s, h, m in pts:
        if h is None:
            if poly:
                parts.append('<polygon points="%s %.1f,%.1f %.1f,%.1f" fill="#8e96a8" stroke="#dfe6f5" stroke-width="1.5"/>' % (
                    " ".join(poly), sxs(prev), sys_(y_lo), sxs(first), sys_(y_lo)))
                poly = []
            continue
        if not poly:
            first = s
        poly.append("%.1f,%.1f" % (sxs(s), sys_(h)))
        prev = s
    if poly:
        parts.append('<polygon points="%s %.1f,%.1f %.1f,%.1f" fill="#8e96a8" stroke="#dfe6f5" stroke-width="1.5"/>' % (" ".join(poly), sxs(prev), sys_(y_lo), sxs(first), sys_(y_lo)))
    for (label, s0, s1, y0, y1, col) in solids or []:
        parts.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" fill-opacity="0.55" stroke="%s"/>' % (sxs(s0), sys_(y1), (s1 - s0) * 7, (y1 - y0) * 7, col, col))
        parts.append('<text x="%.1f" y="%.1f" font-size="10" fill="#fff" text-anchor="middle">%s</text>' % (sxs((s0 + s1) / 2), sys_(y1) - 3, esc(label)))
    parts.append('<text x="60" y="22" font-size="15" font-weight="700" fill="#fff">%s</text>' % esc(name))
    render_svg("\n".join(parts), path or os.path.join(OUT, "section_%s.png" % name.split()[0].lower()), W, H)




if __name__ == "__main__":
    extra = None
    try:
        import windrift as D
        extra = D.plan_overlay
    except ImportError:
        pass
    plan(extra)
