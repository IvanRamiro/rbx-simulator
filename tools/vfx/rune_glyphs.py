"""Floating runes for the Spirit Soul aura (Realm 4, 2026-11-03): sixteen original glyphs in a 4x4
sheet, one per particle (FlipbookStartRandom picks the cell). White on transparent, a soft glow
under each stroke; the game tints them.

No text in any language (the game's fixed directive): every glyph is built from abstract marks
(rings, arcs, bars, dots, ticks, triangles), never a letter or a character.

    python3 rune_glyphs.py assets/aura/runes     (needs Pillow and numpy)

  RuneGlyphs.png  1024x1024  4x4 cells of 256
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(20261104)
SCALE = 4                      # drawn at 4x and reduced, for clean strokes
CELL = 256 * SCALE
STROKE = 9 * SCALE


def glyph(d, cx, cy, r, kind):
    """one rune of `kind` (0..15) centred on (cx, cy), radius r"""
    def ring(rr, w=STROKE):
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=255, width=w)

    def arc(rr, a0, a1, w=STROKE):
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], a0, a1, fill=255, width=w)

    def bar(x0, y0, x1, y1, w=STROKE):
        d.line([cx + x0 * r, cy + y0 * r, cx + x1 * r, cy + y1 * r], fill=255, width=w)

    def dot(x, y, s=0.09):
        d.ellipse([cx + (x - s) * r, cy + (y - s) * r, cx + (x + s) * r, cy + (y + s) * r], fill=255)

    def tri(s, up=True, w=STROKE):
        k = -1 if up else 1
        pts = [(cx, cy + k * s * r), (cx + 0.87 * s * r, cy - k * 0.5 * s * r), (cx - 0.87 * s * r, cy - k * 0.5 * s * r)]
        d.polygon(pts, outline=255, width=w)

    if kind == 0:      # a ring round a dot, ticks at the quarters
        ring(r * 0.75); dot(0, 0, 0.14)
        for a in range(4):
            t = a * math.pi / 2
            bar(math.cos(t) * 0.75, math.sin(t) * 0.75, math.cos(t) * 1.0, math.sin(t) * 1.0)
    elif kind == 1:    # a crescent over a small diamond
        arc(r * 0.8, 200, 340)
        pts = [(cx, cy + 0.05 * r), (cx + 0.25 * r, cy + 0.35 * r), (cx, cy + 0.65 * r), (cx - 0.25 * r, cy + 0.35 * r)]
        d.polygon(pts, outline=255, width=STROKE)
    elif kind == 2:    # a triangle in a ring
        ring(r * 0.9); tri(0.62)
    elif kind == 3:    # two crescents back to back
        arc(r * 0.7, 110, 250); arc(r * 0.7, -70, 70); bar(0, -0.9, 0, 0.9)
    elif kind == 4:    # a diamond with a dot at each point
        pts = [(cx, cy - 0.85 * r), (cx + 0.6 * r, cy), (cx, cy + 0.85 * r), (cx - 0.6 * r, cy)]
        d.polygon(pts, outline=255, width=STROKE)
        for x, y in ((0, -0.85), (0.6, 0), (0, 0.85), (-0.6, 0)):
            dot(x, y, 0.1)
    elif kind == 5:    # a spiral of three turns of arc
        for i, rr in enumerate((0.25, 0.5, 0.75)):
            arc(r * rr, 90 * i, 90 * i + 250)
    elif kind == 6:    # an eye: two arcs and a ring
        arc(r * 1.1, 200, 340); arc(r * 1.1, 20, 160); ring(r * 0.28)
    elif kind == 7:    # a drawn bow: an arc, its string, a shaft across with a point
        arc(r * 0.85, 120, 240); bar(-0.42, -0.74, -0.42, 0.74); bar(-0.85, 0, 0.75, 0)
        bar(0.75, 0, 0.5, -0.2); bar(0.75, 0, 0.5, 0.2)
    elif kind == 8:    # a ring cut by a bar, dots either side
        ring(r * 0.6); bar(-0.95, 0, 0.95, 0); dot(0, -0.85); dot(0, 0.85)
    elif kind == 9:    # two triangles, one inverted (offset, not a star)
        tri(0.55, True); tri(0.4, False)
    elif kind == 10:   # a column of dots between curving rails
        arc(r * 1.4, 145, 215); arc(r * 1.4, -35, 35)
        for yy in (-0.6, -0.2, 0.2, 0.6):
            dot(0, yy, 0.1)
    elif kind == 11:   # three rings in a row, the middle larger
        for x, s in ((-0.62, 0.22), (0, 0.36), (0.62, 0.22)):
            d.ellipse([cx + (x - s) * r, cy - s * r, cx + (x + s) * r, cy + s * r], outline=255, width=STROKE)
    elif kind == 12:   # a half ring over a bar, three dots under
        arc(r * 0.75, 180, 360); bar(-0.85, 0, 0.85, 0)
        for x in (-0.45, 0, 0.45):
            dot(x, 0.45)
    elif kind == 13:   # a cross of unequal arms, ringed at the crossing
        bar(0, -0.95, 0, 0.6); bar(-0.6, -0.25, 0.6, -0.25); d.ellipse([cx - 0.2 * r, cy - 0.45 * r, cx + 0.2 * r, cy - 0.05 * r], outline=255, width=STROKE)
    elif kind == 14:   # a wave over a bar, a dot beneath
        pts = [(cx + (x / 20 - 0.5) * 1.7 * r, cy - 0.45 * r + math.sin(x / 20 * math.tau) * 0.22 * r) for x in range(21)]
        d.line(pts, fill=255, width=STROKE, joint="curve")
        bar(-0.8, 0.2, 0.8, 0.2); dot(0, 0.62, 0.12)
    else:              # a ring of six dots round a smaller ring
        ring(r * 0.3)
        for k in range(6):
            t = k * math.tau / 6
            dot(math.cos(t) * 0.75, math.sin(t) * 0.75, 0.1)


sheet = Image.new("L", (CELL * 4, CELL * 4), 0)
draw = ImageDraw.Draw(sheet)
for k in range(16):
    cx, cy = (k % 4 + 0.5) * CELL, (k // 4 + 0.5) * CELL
    glyph(draw, cx, cy, CELL * 0.3, k)
# a soft glow under every stroke, so a rune reads as light, not ink
glow = sheet.filter(ImageFilter.GaussianBlur(10 * SCALE)).point(lambda v: int(min(255, v * 1.6)))
alpha = Image.fromarray(np.maximum(np.asarray(sheet), np.asarray(glow) * 0.6).astype(np.uint8))
alpha = alpha.resize((1024, 1024), Image.LANCZOS)
rgba = Image.new("RGBA", (1024, 1024), (255, 255, 255, 0))
rgba.putalpha(alpha)
rgba.save(os.path.join(OUT, "RuneGlyphs.png"))
print("written:", sorted(os.listdir(OUT)))
