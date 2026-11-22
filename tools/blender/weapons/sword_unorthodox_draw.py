"""Flat 2D drawing for the Unorthodox sword's research board and silhouette study (run inside Blender, headless; numpy only).

A canvas is a float RGB array (top row first). Polygons are filled by scanline (even-odd), lines are stamped discs, text is a
5x7 pixel font (capitals, digits, a little punctuation), scaled by an integer. Written out through bpy.data.images.
"""
import math
import os

import bpy
import numpy as np

_FONT = {
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110", "D": "11100 10010 10001 10001 10001 10010 11100",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 11011 10001", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    ".": "00000 00000 00000 00000 00000 01100 01100", ",": "00000 00000 00000 00000 01100 00100 01000",
    ":": "00000 01100 01100 00000 01100 01100 00000", "-": "00000 00000 00000 11111 00000 00000 00000",
    "/": "00001 00001 00010 00100 01000 10000 10000", "(": "00010 00100 01000 01000 01000 00100 00010",
    ")": "01000 00100 00010 00010 00010 00100 01000", "+": "00000 00100 00100 11111 00100 00100 00000",
    "%": "11001 11010 00010 00100 01000 01011 10011", "'": "00100 00100 01000 00000 00000 00000 00000",
    "=": "00000 00000 11111 00000 11111 00000 00000", " ": "00000 00000 00000 00000 00000 00000 00000",
    "<": "00010 00100 01000 10000 01000 00100 00010", ">": "01000 00100 00010 00001 00010 00100 01000",
    "?": "01110 10001 00001 00010 00100 00000 00100", "*": "00000 10101 01110 11111 01110 10101 00000",
    "#": "01010 01010 11111 01010 11111 01010 01010", "&": "01100 10010 10100 01000 10101 10010 01101",
}
_GLYPHS = {k: np.array([[int(c) for c in row] for row in v.split()], dtype=bool) for k, v in _FONT.items()}


def canvas(w, h, bg=(0.07, 0.075, 0.09)):
    c = np.zeros((h, w, 3), dtype=np.float32)
    c[:] = bg
    return c


def text(cv, x, y, s, col=(0.9, 0.9, 0.92), scale=2, spacing=1):
    """Draws `s` (capitalised) with its top-left corner at (x, y); returns the x after it."""
    for ch in s.upper():
        g = _GLYPHS.get(ch)
        if g is None:
            g = _GLYPHS["?"]
        big = np.kron(g, np.ones((scale, scale), dtype=bool))
        h, w = big.shape
        y0, x0 = int(y), int(x)
        ys, xs = slice(max(0, y0), min(cv.shape[0], y0 + h)), slice(max(0, x0), min(cv.shape[1], x0 + w))
        if ys.start < ys.stop and xs.start < xs.stop:
            sub = big[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
            cv[ys, xs][sub] = col
        x += (5 + spacing) * scale
    return x


def text_width(s, scale=2, spacing=1):
    return len(s) * (5 + spacing) * scale


def wrap(cv, x, y, s, width, col=(0.8, 0.82, 0.86), scale=2, line=None):
    """Word-wrapped text in a column `width` px wide; returns the y after the last line."""
    line = line or 9 * scale
    words, cur = s.split(), ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_width(trial, scale) > width and cur:
            text(cv, x, y, cur, col, scale)
            y += line
            cur = wd
        else:
            cur = trial
    if cur:
        text(cv, x, y, cur, col, scale)
        y += line
    return y


def fill(cv, poly, col, ss=3):
    """Fills a simple polygon [(x, y)] (pixels, top row = 0), even-odd, antialiased by `ss` x `ss` supersampling of the
    covered rows. poly may hold several loops as a list of lists (holes cut out)."""
    loops = poly if isinstance(poly[0][0], (tuple, list, np.ndarray)) else [poly]
    allp = np.array([p for lp in loops for p in lp], dtype=np.float64)
    x0, y0 = max(0, int(allp[:, 0].min()) - 1), max(0, int(allp[:, 1].min()) - 1)
    x1, y1 = min(cv.shape[1], int(allp[:, 0].max()) + 2), min(cv.shape[0], int(allp[:, 1].max()) + 2)
    if x1 <= x0 or y1 <= y0:
        return
    cov = np.zeros((y1 - y0, x1 - x0), dtype=np.float32)
    for sy in range(ss):
        for sx in range(ss):
            ys = y0 + (np.arange(y1 - y0) + (sy + 0.5) / ss)
            xs = x0 + (np.arange(x1 - x0) + (sx + 0.5) / ss)
            inside = np.zeros((len(ys), len(xs)), dtype=bool)
            for lp in loops:
                n = len(lp)
                for i in range(n):
                    ax, ay = lp[i]
                    bx, by = lp[(i + 1) % n]
                    if ay == by:
                        continue
                    lo, hi = (ay, by) if ay < by else (by, ay)
                    rows = np.where((ys >= lo) & (ys < hi))[0]
                    if not len(rows):
                        continue
                    xc = ax + (ys[rows] - ay) * (bx - ax) / (by - ay)
                    inside[rows] ^= (xs[None, :] > xc[:, None])
            cov += inside
    cov /= ss * ss
    region = cv[y0:y1, x0:x1]
    a = cov[..., None]
    region[:] = region * (1 - a) + np.array(col, dtype=np.float32) * a


def line(cv, pts, col, width=1.5):
    """A polyline of stamped discs (pixels)."""
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        n = max(2, int(math.hypot(bx - ax, by - ay) * 1.5))
        for i in range(n + 1):
            t = i / n
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            r = width / 2
            xs, ys = slice(max(0, int(x - r - 1)), min(cv.shape[1], int(x + r + 2))), slice(max(0, int(y - r - 1)), min(cv.shape[0], int(y + r + 2)))
            if xs.start >= xs.stop or ys.start >= ys.stop:
                continue
            gx, gy = np.meshgrid(np.arange(xs.start, xs.stop) + 0.5, np.arange(ys.start, ys.stop) + 0.5)
            d = np.hypot(gx - x, gy - y)
            a = np.clip(r + 0.5 - d, 0, 1)[..., None]
            cv[ys, xs] = cv[ys, xs] * (1 - a) + np.array(col, dtype=np.float32) * a


def rect(cv, x0, y0, x1, y1, col, width=1.5):
    line(cv, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], col, width)


def paste(cv, tile, x, y):
    h, w = tile.shape[:2]
    cv[y:y + h, x:x + w] = tile[..., :3]


def save(cv, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    h, w = cv.shape[:2]
    img = bpy.data.images.new("UD_Out", w, h, alpha=True)
    img.colorspace_settings.name = "sRGB"
    px = np.ones((h, w, 4), dtype=np.float32)
    px[..., :3] = np.clip(cv, 0, 1)
    img.pixels.foreach_set(np.ascontiguousarray(px[::-1]).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    return path
