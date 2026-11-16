"""The Hall of Records' meshes (2026-11-16, the owner's directive: 22 Worked Builds/Hall of Records Directive.md; the plan: the vault's
Hall of Records Plan 2026-11-16). One idea, the Record Stones: an old stone circle where the world keeps its records, under the World
Tree, in a material language of its own on the hub (not the celestial city's marble, gold, lapis and crystal):
- near-black basalt, cut in clean chamfered blocks (Basalt);
- weathered bronze bands, caps, frames and fittings (Bronze), green patina in the stele's medallion (Patina);
- a dark slate court laid in rings like a great dial, bronze inlay rings and dial lines, slate flags for its paths (Flagstone);
- deep wine cloth banners and the Chronicle's leather cover (Banner), its parchment pages (Parchment);
- the notice board's timber (Timber), the hourglass's glass and amber sand (SandGlass, Sand).

Every piece is authored in Roblox studs (worldlib.rb: Y up, front +Z) at its own origin, the ground under its base centre, to the
numbers in hall_layout.py (the same numbers the placements and the board faces use). Split by material into <Piece>__<Material>
objects (blossom_assets.make_object: closed, triangulated past quads, box-projected UVs one tile per 8 studs). No textures: Studio
sets each part's Roblox material and colour from the suffix (WorldBuilder.MaterialLooks). Blocks reach 0.3 below the ground so the
terrain never shows a gap under them.

    blender -b --factory-startup -P tools/blender/world/hall_records_run.py -- <stage> [pieces]
"""
import math

from mathutils import Vector

import blossom_assets as A
import hall_layout as L

Geo = A.Geo
TAU = 2 * math.pi
SINK = -0.3

A.COLOURS.update({
    "Basalt": (66, 63, 66), "Bronze": (150, 100, 56), "Patina": (92, 136, 116), "Flagstone": (78, 76, 80),
    "Banner": (112, 30, 44), "Parchment": (226, 208, 170), "SandGlass": (226, 220, 204), "Sand": (222, 170, 92),
})
SHADING = {"Basalt": (40.0, True), "Flagstone": (40.0, True), "Bronze": (50.0, True), "Patina": (50.0, True), "Banner": (40.0, True),
           "Parchment": (40.0, True), "Timber": (40.0, True), "SandGlass": (70.0, False), "Sand": (70.0, False)}


# ---------- shapes ----------
def cbox(g, c, s, ch=0.12, yaw=0.0, taper=0.0, pitch=0.0):
    """A closed box with every edge chamfered by `ch` (6 faces, 12 chamfers, 8 corner facets: 44 triangles). c: centre, s: size
    (x, y, z); taper narrows its width (x) by that much at the top, its faces staying upright front and back (a board on its front
    stays flat); pitch tilts it about its own x before the yaw."""
    hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2
    ch = min(ch, hx * 0.45, hy * 0.45, hz * 0.45)
    ids = {}
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                pts = {"A": (sx * hx, sy * (hy - ch), sz * (hz - ch)), "B": (sx * (hx - ch), sy * hy, sz * (hz - ch)),
                       "C": (sx * (hx - ch), sy * (hy - ch), sz * hz)}
                for k, p in pts.items():
                    t = 1.0 - taper / max(s[0], 1e-6) * (p[1] + hy) / (2 * hy) if taper else 1.0
                    q = Vector((p[0] * t, p[1], p[2]))
                    if pitch:
                        q = A.rot_x(q, pitch)
                    ids[(k, sx, sy, sz)] = g.vert(A.rot_y(q, yaw) + Vector(c))
    cyc = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    for s1 in (-1, 1):
        g.face(*[ids[("A", s1, a, b)] for a, b in cyc])
        g.face(*[ids[("B", a, s1, b)] for a, b in cyc])
        g.face(*[ids[("C", a, b, s1)] for a, b in cyc])
    for a in (-1, 1):
        for b in (-1, 1):
            g.face(ids[("B", -1, a, b)], ids[("B", 1, a, b)], ids[("C", 1, a, b)], ids[("C", -1, a, b)])
            g.face(ids[("A", a, -1, b)], ids[("A", a, 1, b)], ids[("C", a, 1, b)], ids[("C", a, -1, b)])
            g.face(ids[("A", a, b, -1)], ids[("A", a, b, 1)], ids[("B", a, b, 1)], ids[("B", a, b, -1)])
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                g.face(ids[("A", sx, sy, sz)], ids[("B", sx, sy, sz)], ids[("C", sx, sy, sz)])
    return g


def cyl(g, c, r, h, seg=16, axis="y", r_top=None):
    """A closed cylinder (or frustum) centred on c, along y, x or z."""
    sub = Geo()
    rt = r if r_top is None else r_top
    A.lathe(sub, [(0.0, h / 2), (rt, h / 2), (r, -h / 2), (0.0, -h / 2)], seg)
    if axis == "x":
        sub.transform(lambda p: Vector((p.y, -p.x, p.z)))
    elif axis == "z":
        sub.transform(lambda p: Vector((p.x, p.z, -p.y)))
    sub.transform(lambda p: p + Vector(c))
    g.add(sub)
    return g


def torus_xy(g, c, R, r, seg=32, tube=8):
    """A ring standing in the XY plane (facing +Z), centre c, ring radius R, tube radius r."""
    rings = []
    for k in range(seg):
        a = TAU * k / seg
        ring = []
        for j in range(tube):
            b = TAU * j / tube
            rr = R + r * math.cos(b)
            ring.append(g.vert((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr, c[2] + r * math.sin(b))))
        rings.append(ring)
    for k in range(seg):
        a, b = rings[k], rings[(k + 1) % seg]
        for j in range(tube):
            jj = (j + 1) % tube
            g.face(a[j], a[jj], b[jj], b[j])
    return g


def prism(g, outline, y0, y1):
    """A closed vertical prism over a convex outline [(x, z)] from y0 to y1."""
    top = [g.vert((x, y1, z)) for x, z in outline]
    bot = [g.vert((x, y0, z)) for x, z in outline]
    g.face(*top)
    g.face(*bot[::-1])
    n = len(outline)
    for k in range(n):
        j = (k + 1) % n
        g.face(bot[k], bot[j], top[j], top[k])
    return g


def frame_bars(g, cx, cy, z0, w, h, bar, depth, yaw=0.0, centre_xz=(0.0, 0.0)):
    """Four bars round a w x h rectangle (inner size) in a vertical plane facing +Z, from z0 forward by depth."""
    ox, oz = centre_xz
    for bx, by, bw, bh in ((cx, cy + h / 2 + bar / 2, w + 2 * bar, bar), (cx, cy - h / 2 - bar / 2, w + 2 * bar, bar),
                           (cx - w / 2 - bar / 2, cy, bar, h + 0.02), (cx + w / 2 + bar / 2, cy, bar, h + 0.02)):
        p = A.rot_y(Vector((bx, 0.0, z0 + depth / 2)), yaw)
        cbox(g, (ox + p.x, by, oz + p.z), (bw, bh, depth), ch=0.04, yaw=yaw)
    return g


def corner_guards(g, cx, cz, w_at, d, heights, yaw=0.0, arm=0.7, tall=0.9, t=0.09):
    """The hall's mark: bronze corner brackets binding a stone block, an L of two plates round each vertical edge at each height.
    w_at(y) is the block's width there (a tapering block); d its depth; (cx, cz) its centre, turned by yaw."""
    for y in heights:
        w = w_at(y)
        for sx in (-1, 1):
            for sz in (-1, 1):
                for c, size in (((sx * (w / 2 - arm / 2 + t / 2), y, sz * (d / 2 + t / 2 - 0.02)), (arm, tall, t)),
                                ((sx * (w / 2 + t / 2 - 0.02), y, sz * (d / 2 - arm / 2 + t / 2)), (t, tall, arm))):
                    p = A.rot_y(Vector(c), yaw)
                    cbox(g, (cx + p.x, p.y, cz + p.z), size, ch=0.025, yaw=yaw)
    return g


# ---------- the pieces ----------
def stele():
    """Highest Cultivation: the tallest record stone, a basalt slab on a three-step plinth, its board framed in bronze, a bronze band
    and cap, and a bronze ring holding a patina disc at its crown (the circle's sign: a ring, open and plain)."""
    s = L.STELE
    basalt, bronze, patina = Geo(), Geo(), Geo()
    y = SINK
    tops = (0.5, 1.0, 1.5)
    for (w, d, _), top in zip(s["plinth"], tops):
        cbox(basalt, (0.0, (y + top) / 2, 0.0), (w, top - y, d), ch=0.14)
        y = top - 0.05
    sw, sd, sy0, sh = s["slab"]
    z = -0.4
    cbox(basalt, (0.0, sy0 - 0.05 + (sh + 0.05) / 2, z), (sw, sh + 0.05, sd), ch=0.18, taper=s["taper"])
    fw, fh, fy = s["face"]
    front = z + sd / 2
    frame_bars(bronze, 0.0, fy, front - 0.03, fw, fh, 0.36, 0.17)
    # a band near the top, wrapping the slab (its taper is small there)
    top_w = sw - s["taper"] * (17.9 - sy0) / sh
    cbox(bronze, (0.0, 17.9, z), (top_w + 0.24, 0.55, sd + 0.24), ch=0.06)
    cap_w = sw - s["taper"] + 0.5
    cap_y = sy0 + sh
    cbox(bronze, (0.0, cap_y + 0.4, z), (cap_w, 0.85, sd + 0.6), ch=0.12)
    cbox(basalt, (0.0, cap_y + 1.15, z), (cap_w - 2.6, 0.75, sd - 0.2), ch=0.12)    # the crown's upper tier
    cbox(bronze, (0.0, cap_y + 1.6, z), (cap_w - 2.2, 0.25, sd + 0.05), ch=0.06)
    cbox(bronze, (0.0, cap_y + 1.95, z), (1.0, 0.6, 0.8), ch=0.1)
    ring_c = (0.0, cap_y + 2.2 + 1.75, z)
    corner_guards(bronze, 0.0, z, lambda y: sw - s["taper"] * (y - sy0) / sh, sd, (2.15, cap_y - 0.75))
    torus_xy(bronze, ring_c, 1.75, 0.3, seg=36, tube=10)
    cyl(patina, ring_c, 1.5, 0.22, seg=28, axis="z")
    return {"Basalt": basalt, "Bronze": bronze, "Patina": patina}, {}


def hourglass():
    """Longest Cultivators: two basalt pillars and a lintel framing a great bronze-and-glass hourglass, its sand mostly run through,
    over a ledger slab on a sill between the pillars."""
    h = L.HOURGLASS
    basalt, bronze, glass, sand = Geo(), Geo(), Geo(), Geo()
    pw, ph, px = h["pillar"]
    for sx in (-1, 1):
        cbox(basalt, (sx * px, (SINK + ph) / 2, 0.0), (pw, ph - SINK, pw), ch=0.16)
        for cy in (0.9, ph - 0.7):
            cbox(bronze, (sx * px, cy, 0.0), (pw + 0.3, 0.5, pw + 0.3), ch=0.08)
    lw, lh, ld = h["lintel"]
    cbox(basalt, (0.0, ph - 0.05 + lh / 2, 0.0), (lw, lh + 0.05, ld), ch=0.16)
    gw, gh, gd, gy = h["ledger"]
    inner = px - pw / 2
    cbox(basalt, (0.0, (SINK + gy) / 2 + 0.02, 0.0), (2 * inner + 0.1, gy - SINK + 0.04, gd + 0.3), ch=0.1)
    cbox(basalt, (0.0, gy + gh / 2, 0.0), (2 * inner + 0.1, gh, gd), ch=0.1)
    fw, fh = h["face"]
    frame_bars(bronze, 0.0, gy + gh / 2, gd / 2 - 0.03, fw, fh, 0.22, 0.12)
    # the hourglass, from the ledger's top to the lintel
    y0, y1 = gy + gh, ph
    R = 2.3
    cyl(bronze, (0.0, y0 + 0.23, 0.0), R, 0.5, seg=28)
    cyl(bronze, (0.0, y1 - 0.23, 0.0), R, 0.5, seg=28)
    for k in range(3):
        a = TAU * k / 3 + math.pi / 2
        cyl(bronze, (math.cos(a) * (R - 0.32), (y0 + y1) / 2, math.sin(a) * (R - 0.32)), 0.16, y1 - y0 - 0.9, seg=10)
    g0, g1 = y0 + 0.46, y1 - 0.46
    mid = (g0 + g1) / 2
    span = (g1 - g0) / 2
    prof = [(0.0, g1), (1.25, g1)]
    for t in (0.92, 0.75, 0.55, 0.35, 0.18, 0.06):
        prof.append((0.22 + 1.5 * math.sin(math.pi * 0.5 * t) ** 0.7, mid + span * t))
    prof.append((0.2, mid))
    for t in (0.06, 0.18, 0.35, 0.55, 0.75, 0.92):
        prof.append((0.22 + 1.5 * math.sin(math.pi * 0.5 * t) ** 0.7, mid - span * t))
    prof += [(1.25, g0), (0.0, g0)]
    A.lathe(glass, prof, 28)
    # the sand: a mound in the lower bulb, a little left in the upper, a thin stream between
    lo = [(0.0, mid - span * 0.38), (0.55, mid - span * 0.48), (1.15, mid - span * 0.66), (1.5, mid - span * 0.82),
          (1.2, g0 + 0.06), (0.0, g0 + 0.06)]
    A.lathe(sand, lo, 24)
    up = [(0.0, mid + span * 0.34), (0.9, mid + span * 0.34), (0.5, mid + span * 0.2), (0.16, mid + span * 0.06), (0.0, mid + span * 0.04)]
    A.lathe(sand, up, 24)
    cyl(sand, (0.0, mid - span * 0.17, 0.0), 0.05, span * 0.44, seg=6)
    return {"Basalt": basalt, "Bronze": bronze, "SandGlass": glass, "Sand": sand}, {}


def wanted_board():
    """Greatest Thieves: a timber notice board on two posts set in basalt footings, a rail over it, bronze caps and bolts."""
    w = L.WANTED
    timber, bronze, basalt = Geo(), Geo(), Geo()
    pw, ph, px = w["posts"]
    for sx in (-1, 1):
        cbox(timber, (sx * px, (SINK - 0.2 + ph) / 2, 0.0), (pw, ph - SINK + 0.2, pw), ch=0.08)
        cbox(basalt, (sx * px, (SINK + 0.55) / 2, 0.0), (1.7, 0.55 - SINK, 1.7), ch=0.14)
        cbox(bronze, (sx * px, ph + 0.64, 0.0), (pw + 0.25, 0.22, pw + 0.25), ch=0.05)
    bw, bh, bd, by = w["board"]
    planks = 6
    ph_ = bh / planks
    for k in range(planks):
        cy = by + ph_ * (k + 0.5)
        cbox(timber, (0.0, cy, 0.0), (2 * px, ph_ - 0.05, bd), ch=0.05)
    # battens behind the planks, holding them to the posts
    for cy in (by + 0.9, by + bh - 0.9):
        cbox(timber, (0.0, cy, -bd / 2 - 0.15), (2 * px, 0.6, 0.32), ch=0.05)
    # the rail over the board, on the posts' tops
    cbox(timber, (0.0, ph + 0.27, 0.0), (2 * px + 1.6, 0.55, 1.1), ch=0.08)
    for sx in (-1, 1):
        for cy in (by + 0.32, by + bh - 0.32):
            cyl(bronze, (sx * (bw / 2 - 0.32), cy, bd / 2 + 0.04), 0.13, 0.12, seg=8, axis="z")
    return {"Timber": timber, "Bronze": bronze, "Basalt": basalt}, {}


def showcase():
    """Rarest Beasts: a long basalt plinth carrying a bronze-framed case of six bays (three by two) before a basalt back, a basalt
    band over it edged in bronze for its name."""
    s = L.SHOWCASE
    basalt, bronze = Geo(), Geo()
    pw, ph, pd = s["plinth"]
    cbox(basalt, (0.0, (SINK + ph) / 2, 0.0), (pw, ph - SINK, pd), ch=0.16)
    cw, chh, cd = s["case"]
    y0, y1 = ph, ph + chh
    cbox(basalt, (0.0, (y0 + y1) / 2, -cd / 2 + 0.26), (cw - 0.1, chh + 0.05, 0.48), ch=0.08)
    # the frame: two end posts, a sill, the mullions between the six bays
    for sx in (-1, 1):
        cbox(bronze, (sx * (cw / 2 - 0.2), (y0 + y1) / 2, 0.0), (0.4, chh + 0.1, cd + 0.12), ch=0.06)
    cbox(bronze, (0.0, y0 + 0.12, 0.02), (cw - 0.3, 0.28, cd - 0.14), ch=0.05)
    fw, fh = s["face"]
    fy = y0 + chh / 2
    for sx in (-1, 1):
        cbox(bronze, (sx * fw / 6, fy, 0.22), (0.22, fh + 0.05, cd - 0.44), ch=0.04)
    cbox(bronze, (0.0, fy, 0.22), (cw - 0.42, 0.22, cd - 0.44), ch=0.04)
    ftw, fth = s["fascia"]
    cbox(basalt, (0.0, y1 + fth / 2 - 0.02, 0.0), (ftw, fth + 0.04, cd + 0.06), ch=0.08)
    for cy in (y1 + 0.06, y1 + fth - 0.06):
        cbox(bronze, (0.0, cy, 0.0), (ftw + 0.16, 0.16, cd + 0.16), ch=0.04)
    return {"Basalt": basalt, "Bronze": bronze}, {}


def firsts_wall():
    """The Hall of Firsts: three record slabs in a shallow arc on a low plinth course, each with a bronze coping and a bronze frame
    round its board."""
    f = L.FIRSTS
    basalt, bronze = Geo(), Geo()
    for name, x, z, yaw, (w, h, d) in L.firsts_slabs():
        cbox(basalt, (x, (SINK + f["plinth"]) / 2, z), (w + 0.8, f["plinth"] - SINK, d + 1.0), ch=0.12, yaw=yaw)
        cbox(basalt, (x, f["plinth"] - 0.05 + (h + 0.05) / 2, z), (w, h + 0.05, d), ch=0.16, yaw=yaw)
        top = f["plinth"] + h
        corner_guards(bronze, x, z, lambda y, w=w: w, d, (f["plinth"] + 0.75, top - 0.75), yaw=yaw, arm=0.45)
        cbox(bronze, (x, top + 0.2, z), (w + 0.4, 0.45, d + 0.4), ch=0.08, yaw=yaw)
        fw, fh = f["mid_face"] if name == "Mid" else f["side_face"]
        cy = f["plinth"] + h / 2 - 0.1
        frame_bars(bronze, 0.0, cy, d / 2 - 0.03, fw, fh, 0.2, 0.12, yaw=yaw, centre_xz=(x, z))
    return {"Basalt": basalt, "Bronze": bronze}, {}


def lectern():
    """The Chronicle: a great open book (a wine leather cover, two blocks of pages) on a tilted bronze rest, on a bronze column with
    rings, on a basalt drum."""
    basalt, bronze, cover, pages = Geo(), Geo(), Geo(), Geo()
    A.lathe(basalt, [(0.0, 0.9), (1.25, 0.9), (1.45, 0.7), (1.55, 0.2), (1.6, SINK), (0.0, SINK)], 24)
    c, n, up = L.lectern_plane()
    a = math.radians(L.LECTERN["slope"])
    A.lathe(bronze, [(0.0, c[1] - 0.2), (0.32, c[1] - 0.2), (0.4, 3.5), (0.52, 3.3), (0.38, 3.1), (0.4, 1.4), (0.55, 1.2),
                     (0.6, 0.85), (0.0, 0.85)], 20)
    bw, bd = L.LECTERN["book"]
    # the rest: a bronze board under the book, a lip at its front edge
    cbox(bronze, (c[0] - n[0] * 0.13, c[1] - n[1] * 0.13, c[2] - n[2] * 0.13), (bw + 0.5, 0.26, bd + 0.4), ch=0.06, pitch=a)
    lip = Vector((0.0, 0.23, bd / 2 + 0.1))
    lip = A.rot_x(lip, a)
    cbox(bronze, (lip.x, c[1] + lip.y, c[2] + lip.z), (bw + 0.5, 0.42, 0.2), ch=0.05, pitch=a)
    # the book: its cover, then two blocks of pages either side of the spine
    cv = L.LECTERN["cover"]
    cbox(cover, (c[0] + n[0] * (cv / 2 - 0.01), c[1] + n[1] * (cv / 2 - 0.01), c[2] + n[2] * (cv / 2 - 0.01)), (bw + 0.3, cv, bd + 0.3),
         ch=0.04, pitch=a)
    pt = L.LECTERN["pages"]
    pw, _ = L.LECTERN["page"]
    for sx in (-1, 1):
        off = cv + pt / 2 - 0.03
        cbox(pages, (sx * (pw / 2 + 0.15), c[1] + n[1] * off, c[2] + n[2] * off), (pw + 0.2, pt, bd - 0.1), ch=0.06, pitch=a)
    return {"Basalt": basalt, "Bronze": bronze, "Banner": cover, "Parchment": pages}, {}


def trilithon():
    """The entrance: two tapering basalt uprights carrying a lintel (a trilithon), bronze bands round the uprights, a bronze plaque on
    the lintel's outer face for the hall's name."""
    t = L.TRILITHON
    basalt, bronze = Geo(), Geo()
    uw, ud, uh = t["upright"]
    lw, lh, ld = t["lintel"]
    ux = t["opening"] / 2 + uw / 2
    for sx in (-1, 1):
        cbox(basalt, (sx * ux, (SINK + uh) / 2, 0.0), (uw, uh - SINK, ud), ch=0.18, taper=0.3)
        for cy, k in ((1.1, 0.0), (uh - 1.4, 0.3 * (uh - 1.4 - SINK) / (uh - SINK))):
            cbox(bronze, (sx * ux, cy, 0.0), (uw - k + 0.3, 0.5, ud + 0.3), ch=0.07)
    corner_guards(bronze, 0.0, 0.0, lambda y: lw, ld, (uh + lh / 2,), arm=0.9, tall=lh - 0.5)
    cbox(basalt, (0.0, uh - 0.05 + lh / 2, 0.0), (lw, lh + 0.05, ld), ch=0.2)
    pw, ph = t["plaque"]
    cbox(bronze, (0.0, uh + lh / 2, ld / 2 + 0.06), (pw + 0.8, ph + 0.4, 0.16), ch=0.05)
    return {"Basalt": basalt, "Bronze": bronze}, {}


def banner_pole():
    """A banner on a bronze pole: a basalt foot, the pole with a ball finial, a crossbar, the wine cloth (two soft folds, a
    swallowtail end) with a bronze ring and diamond worked on both faces."""
    basalt, bronze, cloth = Geo(), Geo(), Geo()
    cbox(basalt, (0.0, (SINK + 0.6) / 2, 0.0), (1.2, 0.6 - SINK, 1.2), ch=0.12)
    A.lathe(bronze, [(0.0, 12.55), (0.22, 12.45), (0.33, 12.2), (0.22, 11.95), (0.17, 11.9), (0.18, 0.7), (0.3, 0.6), (0.0, 0.55)], 14)
    cyl(bronze, (0.0, 11.4, 0.25), 0.1, 3.8, seg=10, axis="x")
    cyl(bronze, (0.0, 11.4, 0.12), 0.12, 0.3, seg=10, axis="z")
    for sx in (-1, 1):
        A.lathe(bronze, [(0.0, 11.4 + 0.16), (0.16, 11.4), (0.0, 11.4 - 0.16)], 10, centre=(sx * 1.95, 0.0, 0.25))
    # the cloth: a zig-zag section (two folds), swept down, the bottom cut to a swallowtail
    top, bottom, notch = 11.32, 3.8, 1.1
    xs = [-1.6, -0.8, 0.8, 1.6]
    zs = [0.25, 0.33, 0.33, 0.25]
    th = 0.05
    rows = 14
    front, back = [], []
    for j in range(rows + 1):
        fr, bk = [], []
        for x, z in zip(xs, zs):
            depth = notch * (1.0 - abs(x) / 1.6)
            y = top - (top - bottom - depth) * j / rows
            fr.append(cloth.vert((x, y, z + th)))
            bk.append(cloth.vert((x, y, z - th)))
        front.append(fr)
        back.append(bk)
    for j in range(rows):
        for k in range(len(xs) - 1):
            cloth.face(front[j][k], front[j][k + 1], front[j + 1][k + 1], front[j + 1][k])
            cloth.face(back[j][k + 1], back[j][k], back[j + 1][k], back[j + 1][k + 1])
    for j in range(rows):
        cloth.face(front[j][0], front[j + 1][0], back[j + 1][0], back[j][0])
        cloth.face(front[j + 1][-1], front[j][-1], back[j][-1], back[j + 1][-1])
    for k in range(len(xs) - 1):
        cloth.face(front[0][k + 1], front[0][k], back[0][k], back[0][k + 1])
        cloth.face(front[rows][k], front[rows][k + 1], back[rows][k + 1], back[rows][k])
    # the emblem on both faces of the flat middle panel
    ey = 8.9
    for sz, zz in ((1, 0.33 + th), (-1, 0.33 - th)):
        torus_xy(bronze, (0.0, ey, zz + sz * 0.02), 0.6, 0.07, seg=24, tube=6)
        dia = [(0.0, 0.38), (0.3, 0.0), (0.0, -0.38), (-0.3, 0.0)]
        g = Geo()
        fr = [g.vert((x, ey + y, zz + sz * 0.07)) for x, y in dia]
        bk = [g.vert((x, ey + y, zz - sz * 0.01)) for x, y in dia]
        g.face(*fr)
        g.face(*bk[::-1])
        for k in range(4):
            j = (k + 1) % 4
            g.face(bk[k], bk[j], fr[j], fr[k])
        bronze.add(g)
    return {"Basalt": basalt, "Bronze": bronze, "Banner": cloth}, {}


def _stone(g, a0, a1, r0, r1, y0=-0.1, y1=0.25, gap=0.05):
    """One flagstone of a ring course: the ring sector from bearing a0 to a1 (radians) and r0 to r1, its edges pulled in by `gap`,
    a closed prism with a slight chamfer on top."""
    seg = max(1, int((a1 - a0) * r1 / 1.6))
    ga0, ga1 = a0 + gap / max(r0, 0.5), a1 - gap / max(r0, 0.5)
    rr0, rr1 = r0 + gap, r1 - gap
    outer = [(math.cos(ga0 + (ga1 - ga0) * k / seg) * rr1, math.sin(ga0 + (ga1 - ga0) * k / seg) * rr1) for k in range(seg + 1)]
    inner = [(math.cos(ga1 - (ga1 - ga0) * k / seg) * rr0, math.sin(ga1 - (ga1 - ga0) * k / seg) * rr0) for k in range(seg + 1)]
    ring = outer + inner
    # the top inset by a small chamfer toward the stone's middle
    mx = sum(p[0] for p in ring) / len(ring)
    mz = sum(p[1] for p in ring) / len(ring)
    topv = [g.vert((x + (mx - x) * 0.03, y1, z + (mz - z) * 0.03)) for x, z in ring]
    midv = [g.vert((x, y1 - 0.06, z)) for x, z in ring]
    botv = [g.vert((x, y0, z)) for x, z in ring]
    n = len(ring)
    # (a sector is not convex along its outer arc: fan it from its middle)
    ctop = g.vert((mx, y1, mz))
    cbot = g.vert((mx, y0, mz))
    for k in range(n):
        j = (k + 1) % n
        g.face(ctop, topv[k], topv[j])
        g.face(cbot, botv[j], botv[k])
        g.face(topv[k], midv[k], midv[j], topv[j])
        g.face(midv[k], botv[k], botv[j], midv[j])


def court():
    """The court: slate flags laid in rings like a great dial (a round middle stone, courses outward), a bronze ring round the middle,
    twelve bronze dial lines across the inner courses, a bronze ring between the inner and outer courses, a bronze kerb, on a dark bed."""
    flag, bronze, bed = Geo(), Geo(), Geo()
    R = L.COURT_R
    A.lathe(bed, [(0.0, 0.14), (R - 0.4, 0.14), (R - 0.4, -0.02), (0.0, -0.02)], 96)
    A.lathe(flag, [(0.0, 0.25), (5.0, 0.25), (5.12, 0.19), (5.12, -0.1), (0.0, -0.1)], 40)
    inner = [(6.2, 9.2), (9.2, 12.2), (12.2, 15.1), (15.1, 18.0)]
    outer = [(18.5, 21.3), (21.3, 24.0), (24.0, R - 0.65)]
    dial = 12
    for r0, r1 in inner:
        per = max(1, round(TAU * (r0 + r1) / 2 / dial / 4.2))
        for d in range(dial):
            a0 = TAU * d / dial + 0.11 / r0
            a1 = TAU * (d + 1) / dial - 0.11 / r0
            for k in range(per):
                _stone(flag, a0 + (a1 - a0) * k / per, a0 + (a1 - a0) * (k + 1) / per, r0, r1)
    for i, (r0, r1) in enumerate(outer):
        n = max(12, round(TAU * (r0 + r1) / 2 / 4.4))
        ph = (0.5 if i % 2 else 0.0) * TAU / n
        for k in range(n):
            _stone(flag, ph + TAU * k / n, ph + TAU * (k + 1) / n, r0, r1)
    for r0, r1 in ((5.12, 6.2), (18.0, 18.5)):
        A.lathe_loop(bronze, [(r0, 0.27), (r1, 0.27), (r1, 0.0), (r0, 0.0)], 72)
    for d in range(dial):
        a = TAU * d / dial
        g = Geo()
        cbox(g, ((6.2 + 18.0) / 2, 0.125, 0.0), (18.0 - 6.2 + 0.1, 0.27, 0.2), ch=0.03)
        g.transform(lambda p, a=a: Vector((p.x * math.cos(a) - p.z * math.sin(a), p.y, p.x * math.sin(a) + p.z * math.cos(a))))
        bronze.add(g)
    A.lathe_loop(bronze, [(R - 0.65, 0.33), (R - 0.05, 0.33), (R, 0.28), (R, -0.15), (R - 0.65, -0.15)], 96)
    return {"Flagstone": flag, "Bronze": bronze, "Basalt": bed}, {}


def path_flag():
    """A slate flag of the hall's paths: an irregular eight-sided slab, chamfered on top, its top 0.25 over the ground."""
    out = [(-2.3, -0.9), (-1.9, -1.3), (1.6, -1.32), (2.3, -0.8), (2.25, 0.95), (1.8, 1.3), (-1.7, 1.28), (-2.28, 0.85)]
    g = Geo()
    top = [g.vert((x * 0.97, 0.25, z * 0.95)) for x, z in out]
    mid = [g.vert((x, 0.18, z)) for x, z in out]
    bot = [g.vert((x, -0.12, z)) for x, z in out]
    g.face(*top)
    g.face(*bot[::-1])
    for k in range(8):
        j = (k + 1) % 8
        g.face(top[k], mid[k], mid[j], top[j])
        g.face(mid[k], bot[k], bot[j], mid[j])
    return {"Flagstone": g}, {}


PIECES = {"HR_Stele": stele, "HR_Hourglass": hourglass, "HR_WantedBoard": wanted_board, "HR_Showcase": showcase,
          "HR_FirstsWall": firsts_wall, "HR_Lectern": lectern, "HR_Trilithon": trilithon, "HR_BannerPole": banner_pole,
          "HR_Court": court, "HR_PathFlag": path_flag}


def build_piece(piece, coll=None):
    """Builds one piece: its objects (one per material) and meta."""
    import worldlib as W
    coll = coll or W.collection(piece)
    W.clear_collection(coll)
    parts, meta = PIECES[piece]()
    objs = []
    for suffix, geo in sorted(parts.items()):
        ang, wt = SHADING.get(suffix, (60.0, True))
        objs.append(A.make_object("%s__%s" % (piece, suffix), geo, suffix, coll, ang, wt))
    return objs, meta


tris = A.tris
bbox_roblox = A.bbox_roblox
clear_scene = A.clear_scene
