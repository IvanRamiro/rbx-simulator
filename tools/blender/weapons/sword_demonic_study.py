"""The Demonic sword's design study (run inside Blender, headless):

    blender -b --factory-startup --python tools/blender/weapons/sword_demonic_study.py -- silhouettes|research|all

silhouettes: eight candidate outlines of the whole sword, drawn flat black on white from the flat the player sees (point up),
             as a big sheet and again at thumbnail size, next to grey outlines of the other two factions' directions and
             Sword6 at the same scale, with the chosen one marked;
research:    the research board: what the real swords measure (the Met's open-access records, numbers only: the museum's
             image server refuses automated downloads, so no photographs are used) and the principles taken from them, drawn
             as schematic profiles.

Everything goes to renders/faction_weapons_v2/Demonic/ (local, never committed). Studs, authored as the game weapon is:
the grip centre at the origin, the point toward -Z (drawn up), the spine toward +X.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import sword_demonic_text as T  # noqa: E402
from sword_demonic_profile import catmull, talon  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REVIEW = os.environ.get("SD_REVIEW") or os.path.join(REPO, "renders", "faction_weapons_v2", "Demonic")
TAU = math.tau


# ---------- 2D drawing ----------
def fill(mask, poly, scale, origin, ss=1):
    """Even-odd fills polygon `poly` ([(x, z)] studs; z up in the image is -z) into boolean `mask` (H, W)."""
    h, w = mask.shape
    pts = np.array(poly, dtype=float)
    px = origin[0] + pts[:, 0] * scale
    py = origin[1] + pts[:, 1] * scale          # image y grows downward = +z grows downward: the point (-z) is up
    ys = (np.arange(h) + 0.5)[:, None]
    xs = (np.arange(w) + 0.5)[None, :]
    inside = np.zeros((h, w), dtype=bool)
    n = len(pts)
    for i in range(n):
        x0, y0, x1, y1 = px[i], py[i], px[(i + 1) % n], py[(i + 1) % n]
        if y0 == y1:
            continue
        cross = ((y0 <= ys) & (ys < y1)) | ((y1 <= ys) & (ys < y0))
        xi = x0 + (ys - y0) * (x1 - x0) / (y1 - y0)
        inside ^= cross & (xs < xi)
    mask |= inside
    return mask


def band(path, widths):
    """A polygon round an open path [(x, z)]: half-widths per point; returns the outline."""
    path = np.array(path, dtype=float)
    n = len(path)
    t = np.gradient(path, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    nrm = np.stack([-t[:, 1], t[:, 0]], axis=1)
    w = np.array(widths, dtype=float)[:, None]
    return list(path + nrm * w) + list((path - nrm * w)[::-1])


def circle(cx, cz, r, n=40):
    return [(cx + r * math.cos(TAU * i / n), cz + r * math.sin(TAU * i / n)) for i in range(n)]


def ring(cx, cz, r_out, r_in, n=44):
    """Outline of a ring as one polygon (even-odd fills the hole)."""
    return circle(cx, cz, r_out, n) + circle(cx, cz, r_in, n)[::-1] + [circle(cx, cz, r_out, n)[0]]


# ---------- the parts ----------
from sword_demonic_profile import Z0  # where the blade starts (the guard's front)


def blade_pts(spine, edge, per=12):
    """A blade outline from explicit controls: spine and edge are [(s, x)] (s studs along from the blade's start, x across, + toward
    the spine), both ending at the point; Catmull-Rom between them. Returns [(x, z)] spine first, then the edge back."""
    sp = catmull(spine, per)
    ed = catmull(edge, per)
    return [(x, Z0 - s) for s, x in sp] + [(x, Z0 - s) for s, x in ed[::-1]]


def crescent(zc=-0.95, reach=0.98, sweep=0.55, thick=0.2, power=2.2, tip=0.45, n=28):
    """A slab guard seen from the flat: two arms from the middle that sweep forward (toward the point) in one curve, thick in the
    middle and tapering to a blunt end (tip: the end's thickness as a share of the middle's)."""
    out = []
    for side in (-1, 1):
        xs = np.linspace(0.0, reach, n)
        path = [(side * x, zc - sweep * (x / reach) ** power) for x in xs]
        wid = [thick * (1 - (1 - tip) * (x / reach) ** 2.2) for x in xs]
        out.append(band(path, wid))
    out.append(band([(0, zc + 0.02), (0, zc - 0.02)], [thick * 1.1, thick * 1.1]))
    return out


def guard_polys(kind):
    out = []
    zc = -0.95
    if kind == "crescent":
        out += crescent()
    elif kind == "crescent_big":
        out += crescent(zc=-0.97, reach=1.30, sweep=0.78, thick=0.27, tip=0.5)
    elif kind == "crescent_thin":
        out += crescent(thick=0.12, tip=0.2, sweep=0.7, power=1.8)
    elif kind == "crescent_short":
        out += crescent(reach=0.8, sweep=0.38, thick=0.22, tip=0.6)
    elif kind == "bar":             # a plain heavy bar with chamfered ends
        out.append([(-0.9, zc + 0.1), (-0.8, zc - 0.17), (0.8, zc - 0.17), (0.9, zc + 0.1), (0.8, zc + 0.17), (-0.8, zc + 0.17)])
    elif kind == "disc":            # a round tsuba
        out.append(circle(0, zc, 0.62, 50))
    elif kind == "droop":           # quillons sloping toward the point (claymore line)
        for side in (-1, 1):
            out.append(band([(side * x, zc - 0.5 * (x / 0.95) ** 1.2) for x in np.linspace(0, 0.98, 22)], [0.1 * (1 - 0.6 * x) + 0.03 for x in np.linspace(0, 0.98, 22)]))
        out.append(circle(0, zc, 0.2, 20))
    elif kind == "notch":           # a thick slab whose front face carries one deep notch round the blade root
        out.append([(-0.95, zc + 0.2), (-0.95, zc - 0.22), (-0.42, zc - 0.22), (-0.3, zc - 0.5), (0.3, zc - 0.5), (0.42, zc - 0.22), (0.95, zc - 0.22), (0.95, zc + 0.2)])
    return out


def grip_polys(pommel):
    out = [[(-0.14, -0.72), (0.14, -0.72), (0.16, 0.0), (0.14, 0.88), (-0.14, 0.88), (-0.16, 0.0)]]
    if pommel == "ring":
        out.append([(-0.2, 0.88), (0.2, 0.88), (0.17, 1.08), (-0.17, 1.08)])
        out.append(ring(0, 1.34, 0.3, 0.17))
    elif pommel == "cap":
        out.append(band([(0, 0.88), (0, 1.2)], [0.2, 0.17]))
    elif pommel == "disc":
        out.append(circle(0, 1.05, 0.26, 30))
    return out


CANDIDATES = {
    # a long, near-parallel blade, a big point, a round plate guard: a katana made bigger
    "A": dict(spine=[(0, .20), (1.5, .24), (3.0, .30), (4.3, .38), (4.85, .44), (5.05, .48)],
              edge=[(0, -.36), (1.5, -.40), (3.0, -.38), (4.3, -.26), (4.85, .0), (5.05, .48)], guard="disc", pommel="cap"),
    # a straight falchion: a broad belly and a blunt point
    "B": dict(spine=[(0, .30), (2.0, .30), (4.0, .34), (4.8, .30), (5.05, .05)],
              edge=[(0, -.50), (2.0, -.55), (4.0, -.62), (4.8, -.34), (5.05, .05)], guard="bar", pommel="disc"),
    # a kilij: curved, the back stepping out into a false edge toward the point
    "C": dict(spine=[(0, .20), (2.2, .24), (3.3, .32), (3.45, .48), (4.2, .56), (4.8, .5), (5.05, .45)],
              edge=[(0, -.34), (2.0, -.34), (3.6, -.22), (4.4, -.05), (4.85, .28), (5.05, .45)], guard="droop", pommel="cap"),
    # broad and straight-backed, the belly forward, the spine scooped away into a hooked point
    "D": dict(spine=[(0, .22), (1.0, .25), (2.0, .30), (3.0, .38), (3.8, .46), (4.2, .43), (4.55, .30), (4.85, .13), (5.05, .10)],
              edge=[(0, -.42), (1.0, -.46), (2.0, -.54), (3.0, -.62), (3.7, -.64), (4.3, -.56), (4.75, -.36), (5.05, .10)], guard="crescent", pommel="ring"),
    # straight, stepped at the root and clipped at the point: a messer
    "E": dict(spine=[(0, .22), (0.7, .22), (0.85, .36), (3.8, .42), (4.5, .34), (5.05, .0)],
              edge=[(0, -.46), (3.0, -.52), (4.2, -.46), (4.8, -.26), (5.05, .0)], guard="notch", pommel="disc"),
    # an S line: a waist, a belly, the point turned back
    "F": dict(spine=[(0, .2), (1.2, .08), (2.4, .1), (3.4, .28), (4.2, .52), (4.7, .5), (5.05, .38)],
              edge=[(0, -.18), (1.2, -.3), (2.4, -.28), (3.4, -.08), (4.2, .2), (4.7, .3), (5.05, .38)], guard="droop", pommel="cap"),
    # a strong bow and a deep scoop: a hooked beak
    "G": dict(spine=[(0, .24), (1.5, .36), (3.0, .68), (4.0, .98), (4.5, 1.05), (4.85, 1.0), (5.05, .96)],
              edge=[(0, -.30), (1.5, -.18), (3.0, .12), (4.0, .52), (4.6, .78), (4.9, .9), (5.05, .96)], guard="notch", pommel="ring"),
    # a straight slab with a long flat point: a cleaver
    "H": dict(spine=[(0, .30), (2.5, .32), (4.9, .32), (5.05, 0.1)],
              edge=[(0, -.5), (2.5, -.52), (4.9, -.5), (5.05, 0.1)], guard="bar", pommel="cap"),
}


def _final_spec():
    import sword_demonic_profile as PF
    return talon(**PF.FINAL, guard="crescent_big", pommel="ring")


def sword(kind):
    """A candidate's polygons: blade, guard parts, grip parts."""
    if kind == "I":
        s = talon(forte_edge=0.70, waist=0.58, waist_s=1.9, belly_edge=1.0, belly_s=3.85, cove_s=4.2, q=2.2, tip_dx=-0.25, sori=0.4, spine_x=0.3,
                  flick=0.14, guard="crescent_short", pommel="ring")
    elif kind == "J":
        s = _final_spec()
    else:
        s = CANDIDATES[kind] if isinstance(kind, str) else kind
    polys = [blade_pts(s["spine"], s["edge"])]
    polys += guard_polys(s["guard"])
    polys += grip_polys(s["pommel"])
    return polys


def context_polys(kind):
    """Grey outlines of the other directions: Orthodox (straight, slender, graceful), Unorthodox (curved, asymmetric, offset
    guard) and Sword6 (the Immortal realm weapon), drawn only to judge a difference of silhouette."""
    polys = []
    if kind == "orthodox":
        polys.append(blade_pts([(0, .16), (3.3, .13), (3.9, .06), (4.1, 0)], [(0, -.16), (3.3, -.13), (3.9, -.06), (4.1, 0)]))
        polys.append([(-0.8, -0.82), (-0.5, -1.2), (-0.2, -0.98), (0, -1.05), (0.2, -0.98), (0.5, -1.2), (0.8, -0.82), (0.0, -0.76)])
        polys += grip_polys("cap")
    elif kind == "unorthodox":
        polys.append(blade_pts([(0, .12), (1.5, .3), (3.0, .62), (4.0, .85), (4.5, .98)], [(0, -.2), (1.5, -.04), (3.0, .3), (4.0, .6), (4.5, .98)]))
        polys.append(band([(0.95, -0.7), (0.3, -0.95), (-0.35, -0.9)], [0.12, 0.1, 0.07]))
        polys += grip_polys("cap")
    elif kind == "sword6":
        polys.append(blade_pts([(0, .22), (1.8, .27), (3.3, .17), (3.65, 0)], [(0, -.22), (1.8, -.27), (3.3, -.17), (3.65, 0)]))
        polys.append(circle(0, -0.85, 0.5, 30))
        polys += grip_polys("cap")
    return polys


def raster(polys, px_per_stud, size, x0=0.0, z_top=-6.7, ss=3):
    """Black-on-white silhouette (float, 0 = black) of `polys` at the given scale, supersampled."""
    w, h = size
    mask = np.zeros((h * ss, w * ss), dtype=bool)
    origin = (w * ss / 2 - x0 * px_per_stud * ss, -z_top * px_per_stud * ss)
    for p in polys:
        fill(mask, p, px_per_stud * ss, origin)
    m = mask.reshape(h, ss, w, ss).mean(axis=(1, 3))
    return 1.0 - m


def sheet_rgba(img_gray, tint=(0, 0, 0)):
    out = np.ones(img_gray.shape + (4,), dtype=np.float32)
    for c in range(3):
        out[..., c] = 1.0 - (1.0 - img_gray) * (1.0 - tint[c])
    return out


def save_png(arr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    h, w = arr.shape[:2]
    img = bpy.data.images.new("SDStudyOut", w, h, alpha=True)
    img.colorspace_settings.name = "sRGB"
    img.pixels.foreach_set(np.ascontiguousarray(arr[::-1], dtype=np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    return path


VERDICTS = {
    "A": ("Heavy nodachi", "long, near-parallel, round plate: a katana made bigger; reads generic and slender, near the other two"),
    "B": ("Falchion", "a cleaver: broad but blunt, no predatory line, reads as a tool"),
    "C": ("Kilij flare", "good belly but a plain curved sabre; close to the Unorthodox curved direction"),
    "D": ("Clip cleaver", "broad straight-backed blade, belly forward, a plain scoop at the point; a thick crescent guard: reads as an onion-shaped cleaver, the point is weak"),
    "E": ("Stepped messer", "a notch and step: busy at the guard, the point is only a clip"),
    "F": ("Double curve", "an S line: elegant, not massive; too like the Unorthodox"),
    "G": ("Hooked beak", "strong bow: reads curved-asymmetric, a hook-sabre, not a heavy cleaver"),
    "H": ("Flat slab", "a butcher's slab: all mass, no line"),
    "I": ("Heavy head, clip", "a forward-weighted head on a drawn-in neck, the back scooped to a point; strong, the point too tame, guard small"),
    "J": ("Talon head", "the same weight, the point a deep scoop ending in a hooked talon; a heavy crescent slab guard and a ring pommel: the pick"),
}


def silhouettes():
    kinds = list("ABCDEFGHIJ")
    chosen = "J"
    ppu = 40
    cw, ch = 150, 372
    cols = len(kinds)
    pad = 8
    th = int(ch * 14 / ppu)
    tw = int(cw * 14 / ppu)
    W = cols * (cw + pad) + pad
    y1 = 30
    y2 = y1 + ch + 40
    y3 = y2 + th + 50
    H = y3 + th + 40
    sheet = np.ones((H, W, 4), dtype=np.float32) * np.array([0.93, 0.93, 0.94, 1.0], dtype=np.float32)
    labels = []
    for i, k in enumerate(kinds):
        x = pad + i * (cw + pad)
        sheet[y1:y1 + ch, x:x + cw] = sheet_rgba(raster(sword(k), ppu, (cw, ch)))
        labels.append((x + 4, 6, "%d  %s" % (i + 1, VERDICTS[k][0]), 15, (0.1, 0.1, 0.12)))
        g = raster(sword(k), 14, (tw, th))
        sheet[y2:y2 + th, x + (cw - tw) // 2:x + (cw - tw) // 2 + tw] = sheet_rgba(g)
    ctx = [("orthodox", "Orthodox direction"), ("unorthodox", "Unorthodox direction"), ("sword6", "Sword6 (scale)")]
    for j, (k, name) in enumerate(ctx):
        x = pad + j * (cw + pad)
        g = raster(context_polys(k), 14, (tw, th))
        sheet[y3:y3 + th, x + (cw - tw) // 2:x + (cw - tw) // 2 + tw] = sheet_rgba(1.0 - (1.0 - g) * 0.45)
        labels.append((x + 4, y3 + th + 6, name, 13, (0.3, 0.3, 0.33)))
    # the chosen one at thumbnail size beside the other directions, all at one scale
    x = pad + 3 * (cw + pad)
    both = context_polys("orthodox") + []
    g = raster(sword(chosen), 14, (tw, th))
    sheet[y3:y3 + th, x + (cw - tw) // 2:x + (cw - tw) // 2 + tw] = sheet_rgba(g)
    labels.append((x + 4, y3 + th + 6, "chosen, same scale", 13, (0.3, 0.3, 0.33)))
    ci = kinds.index(chosen)
    x = pad + ci * (cw + pad)
    t = 4
    gold = np.array([0.85, 0.62, 0.1, 1.0], dtype=np.float32)
    sheet[y1 - 4:y1 - 4 + t, x - 3:x + cw + 3] = gold
    sheet[y1 + ch:y1 + ch + t, x - 3:x + cw + 3] = gold
    sheet[y1 - 4:y1 + ch + t, x - 3:x - 3 + t] = gold
    sheet[y1 - 4:y1 + ch + t, x + cw - 1:x + cw - 1 + t] = gold
    labels.append((x + 4, y1 + ch + 8, "CHOSEN", 18, (0.7, 0.45, 0.02)))
    labels.append((pad, y2 + th + 6, "the same ten at thumbnail scale (14 px per stud)", 13, (0.25, 0.25, 0.28)))
    lay = T.layer(W, H, labels)
    sheet = T.over(sheet, lay)
    path = save_png(sheet, os.path.join(REVIEW, "01_silhouette_study.png"))
    print("silhouette sheet:", path)
    with open(os.path.join(REVIEW, "01_silhouette_verdicts.txt"), "w") as f:
        for i, k in enumerate(kinds):
            f.write("%d %s: %s%s\n" % (i + 1, VERDICTS[k][0], VERDICTS[k][1], "  <- CHOSEN" if k == chosen else ""))


def refine2():
    """A second round: a forward-heavy head on a narrow neck, and a talon that hooks past the spine line."""
    variants = [
        ("a  kopis head, scooped", talon(forte_edge=0.40, waist=0.30, waist_s=1.9, belly_edge=0.80, belly_s=3.8, cove_s=4.2, q=2.2, tip_dx=-0.35, sori=0.3)),
        ("b  heavy head, hooked", talon(forte_edge=0.38, waist=0.30, waist_s=1.9, belly_edge=0.78, belly_s=3.9, cove_s=4.2, q=2.2, tip_dx=0.05, sori=0.5, flick=0.14)),
        ("c  talon past the back", talon(forte_edge=0.40, belly_edge=0.66, cove_s=3.9, q=2.6, tip_dx=0.18, sori=0.35, flick=0.18)),
        ("d  b, short thick crescent", talon(forte_edge=0.38, waist=0.30, waist_s=1.9, belly_edge=0.78, belly_s=3.9, cove_s=4.2, q=2.2, tip_dx=0.05, sori=0.5, flick=0.14, guard="crescent_short")),
        ("e  b, bigger head", talon(forte_edge=0.36, waist=0.26, waist_s=1.8, belly_edge=0.9, belly_s=3.9, cove_s=4.3, q=2.0, tip_dx=0.0, sori=0.5, flick=0.14)),
        ("f  e, less bow", talon(forte_edge=0.36, waist=0.26, waist_s=1.8, belly_edge=0.9, belly_s=3.9, cove_s=4.3, q=2.0, tip_dx=-0.3, sori=0.2, flick=0.1)),
        ("g  straight back head", talon(spine_x=0.2, forte_edge=0.36, waist=0.28, waist_s=1.8, belly_edge=0.84, belly_s=3.8, cove_s=4.4, q=2.4, tip_dx=-0.55, sori=0.0, flick=0.1)),
        ("h  b with the thin crescent", talon(forte_edge=0.38, waist=0.30, waist_s=1.9, belly_edge=0.78, belly_s=3.9, cove_s=4.2, q=2.2, tip_dx=0.05, sori=0.5, flick=0.14, guard="crescent_thin")),
    ]
    sheet_of(variants, "03_refine_round2.png")


def sheet_of(variants, name):
    ppu = 40
    cw, ch = 150, 372
    pad = 8
    W = len(variants) * (cw + pad) + pad
    H = ch + 70
    sheet = np.ones((H, W, 4), dtype=np.float32) * np.array([0.93, 0.93, 0.94, 1.0], dtype=np.float32)
    labels = []
    for i, (nm, spec) in enumerate(variants):
        x = pad + i * (cw + pad)
        sheet[30:30 + ch, x:x + cw] = sheet_rgba(raster(sword(spec), ppu, (cw, ch)))
        labels.append((x + 4, 6, nm, 13, (0.1, 0.1, 0.12)))
    sheet = T.over(sheet, T.layer(W, H, labels))
    print("sheet:", save_png(sheet, os.path.join(REVIEW, name)))


def refine4():
    """Round 5: the point as the weapon's signature (a deeper scoop, a talon that stands past the back) and a bigger guard."""
    base = dict(spine_x=0.35, q=2.4, flick=0.16, sori=0.34, tip_dx=-0.3, cove_s=4.25, belly_s=3.9, waist_s=1.9, forte_edge=0.70, waist=0.58,
                belly_edge=1.0, guard="crescent_big")
    variants = [
        ("a  as built", talon(**base)),
        ("b  deeper scoop", talon(**{**base, "tip_dx": -0.55, "q": 2.8, "cove_s": 4.1})),
        ("c  talon past the back", talon(**{**base, "tip_dx": 0.05, "flick": 0.34, "q": 2.2})),
        ("d  more bow, long talon", talon(**{**base, "sori": 0.62, "tip_dx": -0.05, "flick": 0.3, "cove_s": 4.1})),
        ("e  c, narrower head", talon(**{**base, "tip_dx": 0.05, "flick": 0.34, "belly_edge": 0.92, "waist": 0.54, "forte_edge": 0.66})),
        ("f  d, head forward", talon(**{**base, "sori": 0.62, "tip_dx": -0.05, "flick": 0.3, "cove_s": 4.3, "belly_s": 4.05, "waist_s": 2.1})),
        ("g  hooked, straight neck", talon(**{**base, "sori": 0.5, "tip_dx": 0.1, "flick": 0.4, "waist": 0.64, "cove_s": 4.0})),
        ("h  g, long cove", talon(**{**base, "sori": 0.5, "tip_dx": -0.2, "flick": 0.42, "waist": 0.64, "cove_s": 3.8, "q": 2.0})),
    ]
    sheet_of(variants, "05_refine_round4.png")


def refine5():
    """Round 6: the point's hook without throwing the whole blade off the axis (the tip stays within 0.7 of it)."""
    base = dict(spine_x=0.35, q=2.8, flick=0.4, sori=0.34, tip_dx=-0.55, cove_s=4.1, belly_s=3.9, waist_s=1.9, forte_edge=0.70, waist=0.58,
                belly_edge=1.0, guard="crescent_big")
    def tipx(spec):
        return spec["spine"][-1][1]
    variants = []
    for nm, kw in (("a  scoop + hook", {}), ("b  deeper, higher hook", dict(tip_dx=-0.7, flick=0.5, q=3.0, cove_s=3.95)),
                   ("c  longer scoop", dict(tip_dx=-0.5, flick=0.46, q=2.4, cove_s=3.9, belly_edge=0.96)), ("d  less bow", dict(tip_dx=-0.62, flick=0.46, sori=0.2, cove_s=4.0)),
                   ("e  head forward", dict(belly_s=4.1, cove_s=4.25, waist_s=2.2, flick=0.44)), ("f  big hook", dict(tip_dx=-0.78, flick=0.62, q=3.2, cove_s=3.9)),
                   ("g  a, thick short guard", dict(guard="crescent_short")), ("h  b, lighter forte", dict(tip_dx=-0.7, flick=0.5, q=3.0, cove_s=3.95, forte_edge=0.64, waist=0.52))):
        spec = talon(**{**base, **kw})
        variants.append(("%s (tip x %.2f)" % (nm, tipx(spec)), spec))
    sheet_of(variants, "06_refine_round5.png")


def refine3():
    """Round 4: the owner's direction asks for a much wider forte than Sword6's 0.48, so the neck is widened and the head eased."""
    base = dict(spine_x=0.26, q=2.2, flick=0.12, sori=0.4, tip_dx=-0.2, cove_s=4.2, belly_s=3.85, waist_s=1.9)
    variants = [
        ("a  forte .70 waist .58 head 1.0", talon(**{**base, "forte_edge": 0.70, "waist": 0.58, "belly_edge": 1.0})),
        ("b  forte .74 head 1.06", talon(**{**base, "forte_edge": 0.74, "waist": 0.64, "belly_edge": 1.06})),
        ("c  forte .66 head .96 deep cove", talon(**{**base, "forte_edge": 0.66, "waist": 0.54, "belly_edge": 0.96, "q": 2.6, "tip_dx": -0.4})),
        ("d  no waist, a long swell", talon(**{**base, "forte_edge": 0.70, "waist": None, "belly_edge": 1.0})),
        ("e  a, thick short crescent", talon(**{**base, "forte_edge": 0.70, "waist": 0.58, "belly_edge": 1.0, "guard": "crescent_short"})),
        ("f  a, tip hooked high", talon(**{**base, "forte_edge": 0.70, "waist": 0.58, "belly_edge": 1.0, "tip_dx": 0.0, "flick": 0.2})),
        ("g  a, head forward", talon(**{**base, "forte_edge": 0.70, "waist": 0.56, "belly_edge": 1.0, "belly_s": 4.05, "cove_s": 4.4, "q": 2.0})),
        ("h  a, less bow", talon(**{**base, "forte_edge": 0.70, "waist": 0.58, "belly_edge": 1.0, "sori": 0.2})),
    ]
    sheet_of(variants, "04_refine_round3.png")


def refine():
    """Eight tunings of the chosen idea, side by side."""
    variants = [
        ("a  first cut (as drawn)", talon()),
        ("b  slimmer forte, less belly", talon(forte_edge=0.34, belly_edge=0.58, tip_dx=-0.25)),
        ("c  straight back, deep cove", talon(spine_x=0.2, belly_edge=0.66, cove_s=3.9, q=2.6, tip_dx=-0.55, sori=0.35)),
        ("d  belly further forward", talon(belly_edge=0.66, belly_s=4.0, cove_s=4.3, q=2.2, tip_dx=-0.35, sori=0.3)),
        ("e  more bow, hooked", talon(belly_edge=0.62, sori=0.65, cove_s=4.0, q=2.4, tip_dx=-0.15, flick=0.12)),
        ("f  long cove, thin beak", talon(belly_edge=0.64, belly_s=3.4, cove_s=3.6, q=1.8, tip_dx=-0.62, sori=0.45, flick=0.1)),
        ("g  short cove, heavy beak", talon(belly_edge=0.7, belly_s=3.9, cove_s=4.5, q=2.8, tip_dx=-0.18, sori=0.3)),
        ("h  e with a thin crescent", talon(belly_edge=0.62, sori=0.65, cove_s=4.0, q=2.4, tip_dx=-0.15, flick=0.12, guard="crescent_thin")),
    ]
    ppu = 40
    cw, ch = 150, 372
    pad = 8
    W = len(variants) * (cw + pad) + pad
    H = ch + 70
    sheet = np.ones((H, W, 4), dtype=np.float32) * np.array([0.93, 0.93, 0.94, 1.0], dtype=np.float32)
    labels = []
    for i, (name, spec) in enumerate(variants):
        x = pad + i * (cw + pad)
        sheet[30:30 + ch, x:x + cw] = sheet_rgba(raster(sword(spec), ppu, (cw, ch)))
        labels.append((x + 4, 6, name, 13, (0.1, 0.1, 0.12)))
    sheet = T.over(sheet, T.layer(W, H, labels))
    print("refine sheet:", save_png(sheet, os.path.join(REVIEW, "02_refine_round1.png")))


def research():
    """The research board: numbers from the Metropolitan Museum's open-access records (the object pages' length, width, weight and
    sori; the museum's image server refuses automated downloads, so no photographs) and the principles taken from them."""
    W, H = 1900, 1180
    bg = np.array([0.10, 0.105, 0.12, 1.0], dtype=np.float32)
    sheet = np.ones((H, W, 4), dtype=np.float32) * bg
    items = []
    ink, dim, gold, red = (0.92, 0.92, 0.94), (0.62, 0.64, 0.7), (0.86, 0.66, 0.22), (0.9, 0.35, 0.3)

    def txt(x, y, s_, size=17, col=ink):
        items.append((x, y, s_, size, col))

    txt(40, 26, "DEMONIC SWORD: research board", 34, gold)
    txt(40, 76, "real master-made swords: what they measure, and the principle taken (never a copy; no Chinese design)", 18, dim)
    # column 1: the records
    txt(40, 130, "1  What the museum records say (Met open access, cm and grams)", 20, gold)
    rows = [
        "Falchion, Venice c.1490: length 91.4, 981 g: a cleaving blade that widens toward the point",
        "Kilij, Turkish 19th c.: blade 84.5, guard span 14, 1576 g with scabbard: the 'yelman' flare near the point",
        "Kilij (Iranian blade): blade 78.2, 689 g: a curved blade with a false edge on the flare",
        "Executioner's sword, Sulawesi brass: blade 45.7, width 15.2, 737 g: a head 1 : 3, all weight forward",
        "Naga two-handed sword, Assam: 117.8 long, 9.5 wide, 1.4 thick, 1.1 kg: a heavy slab one-edged blade",
        "Tachi blade, Japan 14th-15th c.: blade 89.4, edge 72.1, sori 2.7 (3 percent of the length)",
        "Claymore: blade 103.5, guard span 28.5, 2.07 kg",
        "Two-handed sword c.1400-1450: blade 109.9, guard 29.2, 2.35 kg",
        "Two-hand sword, Venice c.1570: blade 114.6, guard 45.1, 2.86 kg",
        "Korean sword 16th-19th c.: blade 68.6, 1.03 kg; tsuba 7.9 to 9.5 across, 3 thick",
        "Yatagan, Balkan 1802: blade 58.7, width 5.7, 850 g: the point leans forward",
    ]
    for i, r in enumerate(rows):
        txt(40, 168 + i * 27, r, 15, ink)
    # column 1 lower: the principles
    txt(40, 490, "2  Principles taken", 20, gold)
    pr = [
        "Forward weight: falchion, kilij and the Sulawesi head put the mass out toward the point, where a blow is fastest.",
        "   -> a drawn-in neck (0.58 wide) swelling to a head (1.00 wide) at 78 percent of the blade; the forte already 0.70.",
        "The false edge: kilij and clip-point blades sharpen the scooped back near the point.",
        "   -> the back is scooped in a cove behind the point and ground to a second, mirror-polished edge; the point is a hooked talon.",
        "Japanese blade geometry: shinogi-zukuri (a ridge, a plane above it, a face below), a bohi, a yokote where the point's facets start,",
        "   a hard temper line of leaning flame tongues (hamon) between a dark body and a mirror-polished edge bevel.",
        "Distal taper: the ridge's half thickness 0.112 at the forte, 0.082 at the head, 0.056 at the yokote, 0 at the point.",
        "A heavy guard: great swords carry a guard of 26 to 39 percent of the blade; this slab is 52 percent, stylised (a held weapon is read",
        "   from a few studs) as one thick crescent that sweeps forward and cradles the blade's collar.",
        "Tsuba and fittings are built in layers (iron core, bronze face plate, rim, washers, collar): the same here, with real steps.",
        "Korean ring pommel (hwandudaedo): one heavy ring cast with the pommel, here a flat-sided iron ring standing in the flat the player sees.",
        "Tsuka-ito wrap: flat cord crossing in diamonds over a ray-skin core, here a woven over-and-under of two sets of flat ribbons.",
        "Hairline and smoke-line engraving, inlaid bright in dark metal (zogan): lines that all flow one way, from the hand toward the point.",
    ]
    for i, r in enumerate(pr):
        txt(40, 528 + i * 25, r, 15, ink if not r.startswith("   ") else dim)
    txt(40, 868, "3  Not taken", 20, gold)
    nt = ["No Chinese forms: no dao or jian fittings, ruyi clouds, dragon pillars, taiji, knots or lettering anywhere.",
          "No beast, skull, face or eye (the first attempt's guard was thrown away four times for reading as a face), no spikes for their own sake,",
          "no glow: the geometry and the metal carry the design; a small ember accent was left out because nothing needs it."]
    for i, r in enumerate(nt):
        txt(40, 906 + i * 25, r, 15, ink)
    # column 2: bar chart, guard span as a share of the blade, with this sword's
    txt(1010, 130, "Guard span as a share of the blade (from the records)", 20, gold)
    bars = [("Kilij 14 / 84.5", 14 / 84.5), ("Korean sword (W 10.2) / 68.6", 10.2 / 68.6), ("Two-hander 1400s 29.2 / 109.9", 29.2 / 109.9), ("Claymore 28.5 / 103.5", 28.5 / 103.5),
            ("Italian two-hand 48.6 / 128.9", 48.6 / 128.9), ("Venice two-hand 45.1 / 114.6", 45.1 / 114.6), ("this sword 2.6 / 5.0", 2.6 / 5.0)]
    for i, (name, v) in enumerate(bars):
        y = 176 + i * 44
        sheet[y:y + 22, 1010:1010 + int(v * 1400)] = np.array(gold if i == len(bars) - 1 else (0.42, 0.5, 0.64), dtype=np.float32).tolist() + [1.0]
        txt(1016, y + 2, "%s = %d percent" % (name, round(v * 100)), 14, (0.05, 0.05, 0.07) if i == len(bars) - 1 else ink)
    # blade proportions
    txt(1010, 520, "Blade length to width", 20, gold)
    props = [("Naga slab 117.8 : 9.5", 9.5 / 117.8), ("Falchion-class (blade ~70 : 6.5)", 6.5 / 70), ("Sulawesi head 45.7 : 15.2", 15.2 / 45.7),
             ("this sword at the forte 5.0 : 0.70", 0.70 / 5.0), ("this sword at the head 5.0 : 1.00", 1.0 / 5.0), ("Sword6 (Immortal) 3.65 : 0.48", 0.48 / 3.65)]
    for i, (name, v) in enumerate(props):
        y = 566 + i * 44
        sheet[y:y + 22, 1010:1010 + int(v * 1400)] = np.array(gold if "this sword" in name else (0.42, 0.5, 0.64), dtype=np.float32).tolist() + [1.0]
        txt(1016, y + 2, "%s  (width is %d percent of length)" % (name, round(v * 100)), 14, (0.05, 0.05, 0.07) if "this sword" in name else ink)
    txt(1010, 866, "What the numbers say", 20, gold)
    for i, r in enumerate(["Real great swords keep the blade slim (8 percent of its length) and let a 26 to 39 percent guard and a",
                           "one-edged slab give the menace; the broad heads (Sulawesi 33 percent) are short. This sword is stylised:",
                           "a long blade with a broad head (20 percent) for Roblox's distance, kept to a clean shape rather than decoration."]):
        txt(1010, 904 + i * 25, r, 15, ink)
    txt(40, 1120, "Source: collectionapi.metmuseum.org (public-domain object records), the Korea.net and Wikipedia pages on the hwandudaedo, the Kiel sword terminology.", 13, dim)
    sheet = T.over(sheet, T.layer(W, H, items))
    print("research board:", save_png(sheet, os.path.join(REVIEW, "00_research_board.png")))


if __name__ == "__main__":
    stage = (sys.argv[sys.argv.index("--") + 1:] or ["all"])[0] if "--" in sys.argv else "all"
    if stage in ("research", "all"):
        research()
    if stage in ("silhouettes", "all"):
        silhouettes()
    if stage in ("refine",):
        refine()
    if stage in ("refine2",):
        refine2()
    if stage in ("refine3",):
        refine3()
    if stage in ("refine4",):
        refine4()
    if stage in ("refine5",):
        refine5()
