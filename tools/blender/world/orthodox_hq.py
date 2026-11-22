"""Dawnspire Hall, the Orthodox faction's headquarters (2026-11-22). Plain Python (no Blender): builds every piece, the placements, the collision
boxes and the markers from hq_kit. orthodox_hq_run.py turns them into Blender objects, renders, checks, exports and writes the Luau data.

Authoring frame (the PAD'S frame): origin at the pad's centre, y = 0 is the court's floor (0.5 over the pad's ground), front is -Z (toward the
plaza's stairway, whose top is at z = -54), x across. Placed with CFrame.new(pad centre + (0, 0.5, 0)) * Angles(0, FrontYaw, 0) every position
below is a pad-frame position. Unique masses (court, woldae, hall, roofs, rock, ...) are authored in this frame (their origin IS the pad frame's);
instanced pieces (tower, gate pavilion, lantern, banner, flag, spire, basin) have their own origin (y = 0 at their floor) and are placed.

Plan (studs): court x -24..24, z -54..-28 at y 0; tier A (top y 3) x +-34, z -28..38; tier B (y 6) x +-30, z -21..36; tier C (y 9, the hall terrace and the
inner court) x +-26, z -14..34; the hall: columns at x -20..20 every 8 and z -12 (porch), -4, 4, 12; a five-tier stack above; two towers on rock mounds
at (+-40, 6, 0); gate pavilions at (+-25, 1, -42) and (0, 10, 29); the ceremonial stair x +-8 (six steps and the tiers' own edges, every riser 1 stud).
"""
import math

import hq_kit as K
from hq_kit import Piece, Style, box, hexa, prism, lathe, lerp

ST = Style()

# ----- the plan's numbers (all pad-frame studs) -----
COURT = dict(x=24.0, z0=-54.0, z1=-28.0)
TIERS = {  # name: (half width x, z0, z1, y0 (the neck's foot), y1 (the top))
    "A": (42.0, -28.0, 38.0, 0.0, 3.0),
    "B": (38.0, -21.0, 36.0, 3.0, 6.0),
    "C": (34.0, -14.0, 34.0, 6.0, 9.0),
}
FLOOR = 9.0
COL_X = [-28.0, -20.0, -12.0, -4.0, 4.0, 12.0, 20.0, 28.0]
COL_Z = [-12.0, -4.0, 4.0, 12.0]
COL_H = 10.0            # shaft height above the foot (the foot is 1 stud; shaft y 10..20)
COL_TOP = FLOOR + 1.0 + COL_H
BEAM = 1.5
HB1 = 2.2               # the hall's bracket height
HALL_A, HALL_D = 28.0, 12.0
WALL_Z_FRONT, WALL_Z_REAR = -4.0, 12.0
STAIR_HALF = 8.0
TOWER_AT = (45.0, 6.0, 0.0)
PAVILION_FRONT = (25.0, 1.0, -42.0)
PAVILION_REAR = (0.0, 10.0, 29.0)

# the stack above the hall (column-line half sizes, storey heights, roof rises): T2 .. T5
STACK = [
    dict(a=21, d=9, wall=4.2, hb=1.7, o=5.0, rise=4.2, nbx=6, nbz=2, layers=1, mids=0, pitch=1.8, rafters=False, detail=1, br_detail=0, lat_cols=2, lat_rows=2),
    dict(a=16.5, d=7, wall=3.8, hb=1.5, o=4.5, rise=3.8, nbx=6, nbz=2, layers=1, mids=0, pitch=2.1, rafters=False, detail=0, br_detail=0, windows=False),
    dict(a=12, d=5.5, wall=3.4, hb=1.3, o=4.0, rise=3.4, nbx=4, nbz=2, layers=1, mids=0, pitch=2.0, windows=False, rafters=False, detail=0, br_detail=0),
    dict(a=8, d=4, wall=3.2, hb=1.1, o=3.5, rise=4.5, nbx=2, nbz=2, layers=1, mids=0, ridge=2.0, pitch=2.0, windows=False, rafters=False, detail=0, br_detail=0),
]
TOWER = [
    dict(a=6, d=6, wall=7.0, hb=1.6, o=4.0, rise=4.2, nbx=2, nbz=2, layers=1, mids=0, pitch=2.3, rafters=False, detail=0, plinth=0.8, lat_cols=2, lat_rows=2, discs=False,
         br_detail=0),
    dict(a=4.2, d=4.2, wall=5.0, hb=1.3, o=3.4, rise=3.6, nbx=2, nbz=2, layers=1, mids=0, pitch=2.5, rafters=False, detail=0, windows=False,
         br_detail=0, col_seg=6, discs=False),
    dict(a=3.0, d=3.0, wall=4.2, hb=1.1, o=3.0, rise=5.2, nbx=2, nbz=2, layers=1, mids=0, pitch=2.6, rafters=False, detail=0, windows=False, finial=3.6,
         br_detail=0, col_seg=6, discs=False),
]
PAVILION = [
    dict(a=5, d=5, wall=6.5, hb=1.6, o=3.6, rise=3.4, nbx=2, nbz=2, layers=1, mids=0, pitch=2.3, rafters=False, detail=0, windows=False, discs=False,
         open=("N", "E", "S", "W"), col_detail=0, col_seg=6, br_detail=0),
    dict(a=2.2, d=2.2, wall=2.6, hb=0.9, o=2.6, rise=3.6, nbx=1, nbz=1, layers=1, mids=0, pitch=2.0, rafters=False, detail=0, windows=False, finial=3.0,
         br_detail=0, col_seg=6),
]

LANTERN_SPOTS = [  # (x, y, z, yaw, light)
    (-19.5, 0.0, -52.0, 0.0, True), (19.5, 0.0, -52.0, 0.0, True),
    (-14.0, 0.0, -41.0, 0.0, False), (14.0, 0.0, -41.0, 0.0, False),
    (-11.2, 3.0, -25.4, 0.0, False), (11.2, 3.0, -25.4, 0.0, False),
    (-11.2, 6.0, -18.4, 0.0, False), (11.2, 6.0, -18.4, 0.0, False),
    (-8.0, 9.0, -8.5, 0.0, True), (8.0, 9.0, -8.5, 0.0, True),
    (-13.0, 9.0, 15.5, math.pi, False), (13.0, 9.0, 15.5, math.pi, False),
]


def colliders_from(boxes):
    return boxes


# ======================================================================================================================
def tier_block(P, x1, z0, z1, y0, y1, st=ST, foot=-8.0):
    """A woldae tier: a granite plinth (projecting 0.35), a marble neck with a gold line, a marble cornice (projecting 0.3). Symmetric about x = 0."""
    gs = P.geo(st.stone2)
    gm = P.geo(st.stone)
    gg = P.geo(st.gold)
    pl = 0.9
    box(gs, -x1 - 0.35, x1 + 0.35, min(y0, foot) if y0 == 0.0 else y0, y0 + pl, z0 - 0.35, z1 + 0.35, "TNESW")
    box(gm, -x1, x1, y0 + pl, y1 - 0.8, z0, z1, "NESW")
    box(gm, -x1 - 0.3, x1 + 0.3, y1 - 0.8, y1, z0 - 0.3, z1 + 0.3, "TBNESW")
    # a gold line on the neck's face under the cornice (three faces: front, sides, back)
    t = 0.05
    box(gg, -x1 - t, x1 + t, y1 - 1.1, y1 - 0.95, z0 - t, z0 + 0.0, "TBN")
    box(gg, -x1 - t, x1 + t, y1 - 1.1, y1 - 0.95, z1, z1 + t, "TBS")
    box(gg, -x1 - t, -x1, y1 - 1.1, y1 - 0.95, z0, z1, "TBW")
    box(gg, x1, x1 + t, y1 - 1.1, y1 - 0.95, z0, z1, "TBE")


def panels_on_neck(P, x1, z0, z1, y0, y1, step=6.0, st=ST, skip_x=0.0):
    """Recessed rectangular panels on a tier's neck (a frame of gold, 0.04 proud): front and the two sides."""
    gg = P.geo(st.gold)
    gm = P.geo(st.stone)
    ya, yb = y0 + 1.25, y1 - 1.35
    if yb - ya < 0.5:
        return
    n = int((2 * x1 - 2) // step)
    xs = [-x1 + 1.0 + (2 * x1 - 2.0) * (i + 0.5) / n for i in range(n)]
    for x in xs:
        if abs(x) < skip_x:
            continue
        w = step * 0.5
        # a slightly raised panel (marble) with a gold frame line over its top edge
        box(gm, x - w / 2, x + w / 2, ya, yb, z0 - 0.08, z0, "TBNESW" if False else "TBN")
        box(gg, x - w / 2, x + w / 2, yb - 0.06, yb, z0 - 0.11, z0 - 0.08, "TBN")
        box(gg, x - w / 2, x + w / 2, ya, ya + 0.06, z0 - 0.11, z0 - 0.08, "TBN")


def stair_stone(P, st=ST):
    """The ceremonial stair (x +-8): steps y 1, 2 (z -31..-28, on the court), 4, 5 (z -24..-21, on tier A's ledge), 7, 8 (z -17..-14, on tier B's
    ledge), a raised carved strip down the middle (x +-3) with gold edging, and cheek walls with gold caps. Every riser is 1 stud."""
    g = P.geo(st.stone)
    gg = P.geo(st.gold)
    gf = P.geo(st.goldflat)
    gs = P.geo(st.stone2)
    flights = [(0.0, [(-31.0, -29.5), (-29.5, -28.0)]), (3.0, [(-24.0, -22.5), (-22.5, -21.0)]), (6.0, [(-17.0, -15.5), (-15.5, -14.0)])]
    steps = []
    for base, treads in flights:
        for k, (z0, z1) in enumerate(treads):
            top = base + k + 1
            steps.append((base, top, z0, z1))
            box(g, -STAIR_HALF, STAIR_HALF, base, top, z0, z1, "TNESW")
            # the middle strip: a raised marble slab with a gold inlay line round it
            box(g, -3.0, 3.0, top, top + 0.06, z0 + 0.15, z1 - 0.05, "TNESW")
            box(gf, -3.2, -3.0, top, top + 0.07, z0 + 0.1, z1 - 0.02, "TNESW")
            box(gf, 3.0, 3.2, top, top + 0.07, z0 + 0.1, z1 - 0.02, "TNESW")
            # a carved panel on the riser: a gold border and three coin rings (an old motif: concentric coins, nothing figurative)
            ya, yb = top - 0.88, top - 0.14
            for (xa, xb, yy0, yy1) in ((-2.7, 2.7, yb - 0.07, yb), (-2.7, 2.7, ya, ya + 0.07), (-2.7, -2.63, ya + 0.07, yb - 0.07), (2.63, 2.7, ya + 0.07, yb - 0.07)):
                box(gg, xa, xb, yy0, yy1, z0 - 0.05, z0, "TBN")
            for xr in (-1.6, 0.0, 1.6):
                K.lathe_xy(gg, xr, (ya + yb) / 2, 0.3, 0.09, 0.05, 6, z0)
        # cheek walls: one block per flight, each side, stepped with the treads
        for sx in (-1, 1):
            for k, (z0, z1) in enumerate(treads):
                top = base + k + 1
                x0, x1 = (STAIR_HALF, STAIR_HALF + 0.8) if sx > 0 else (-STAIR_HALF - 0.8, -STAIR_HALF)
                box(g, x0, x1, base, top + 1.8, z0, z1, "TNESW")
                box(gg, x0 - 0.06, x1 + 0.06, top + 1.8, top + 2.05, z0 - 0.05, z1 + (0.05 if k == len(treads) - 1 else 0.0), "TBNESW")
    return steps


def balustrade_runs(P, st=ST):
    """Carved balustrades on the tiers' front edges (either side of the stair) and plain parapets on the sides and back (gold-capped posts)."""
    fronts = []
    for name, (x1, z0, z1, y0, y1) in TIERS.items():
        zc = z0 + 0.15
        L = {"A": 32.0, "B": 28.0, "C": 24.0}[name]
        xs = x1 - 0.8 - L                                      # the run starts 0.8 inside the tier's corner
        for sx in (1, -1):
            b = K.balustrade(st, L, h=2.6, post_every=L / round(L / 5.0), thick=0.9)
            if sx > 0:
                P.add(b, t=(xs, y1, zc))
            else:
                P.add(b, t=(-xs - L, y1, zc))
            fronts.append((name, sx, xs, xs + L, zc, y1))
        # the plain parapet: from the end of the carved run round the side and the back
        gm = P.geo(st.stone)
        gg = P.geo(st.gold)
        run_x0, run_x1 = x1 - 0.8 - 0.0, x1 - 0.8
        for sx in (1, -1):
            # the front's corner post and the side runs: x = +-(x1 - 0.8) from z0 + 0.15 to z1 - 0.15
            xx = sx * (x1 - 0.8)
            _parapet(P, xx, z0 + 0.15, xx, z1 - 0.15, y1, st)
        _parapet(P, -(x1 - 0.8), z1 - 0.15, x1 - 0.8, z1 - 0.15, y1, st, gap=({"A": 0.0, "B": 0.0, "C": 0.0}[name]))
        # the part of the front between the carved run and the corner (a short parapet), none needed: the carved run reaches the corner
    return fronts


def _parapet(P, xa, za, xb, zb, y, st, gap=0.0):
    """A plain parapet wall (marble, 1.7 high, 0.8 thick, a gold cap) from (xa, za) to (xb, zb) (axis aligned), with a post every 8."""
    gm = P.geo(st.stone)
    gg = P.geo(st.gold)
    gs = P.geo(st.stone2)
    t = 0.4
    if abs(xb - xa) > abs(zb - za):
        x0, x1 = min(xa, xb), max(xa, xb)
        box(gm, x0, x1, y, y + 1.6, za - t, za + t, "TNESW")
        box(gg, x0 - 0.05, x1 + 0.05, y + 1.6, y + 1.8, za - t - 0.08, za + t + 0.08, "TBNESW")
        n = max(1, int(round((x1 - x0) / 8.0)))
        for i in range(n + 1):
            x = lerp(x0, x1, i / n)
            box(gm, x - 0.55, x + 0.55, y, y + 2.1, za - 0.55, za + 0.55, "TNESW")
            box(gg, x - 0.42, x + 0.42, y + 2.1, y + 2.5, za - 0.42, za + 0.42, "TNESW")
    else:
        z0, z1 = min(za, zb), max(za, zb)
        box(gm, xa - t, xa + t, y, y + 1.6, z0, z1, "TNESW")
        box(gg, xa - t - 0.08, xa + t + 0.08, y + 1.6, y + 1.8, z0 - 0.05, z1 + 0.05, "TBNESW")
        n = max(1, int(round((z1 - z0) / 8.0)))
        for i in range(n + 1):
            z = lerp(z0, z1, i / n)
            box(gm, xa - 0.55, xa + 0.55, y, y + 2.1, z - 0.55, z + 0.55, "TNESW")
            box(gg, xa - 0.42, xa + 0.42, y + 2.1, y + 2.5, z - 0.42, z + 0.42, "TNESW")


# ======================================================================================================================
def build_court():
    P = Piece()
    P.add(K.paving(ST, -COURT["x"], COURT["x"], COURT["z0"], COURT["z1"], y_top=0.0, depth=6.0, slab=4.0))
    gg = P.geo(ST.goldflat)
    ga = P.geo(ST.paint)
    # the crest inlaid at (0, -41): an azure disc, a gold ring and blades (relief 0.08)
    R = 8.5
    cz = -41.0
    prism(ga, [(R * 0.7 * math.cos(K.TAU * k / 24), cz + R * 0.7 * math.sin(K.TAU * k / 24)) for k in range(24)], -0.02, 0.05, "T")
    K.crest(gg, ST, R, (0.0, 0.05, cz), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), 0.08)
    # a gold kerb line along the court's front edge and the sides
    gs = P.geo(ST.stone2)
    box(gs, -COURT["x"], COURT["x"], 0.0, 0.18, COURT["z0"], COURT["z0"] + 0.5, "TNESW")
    for sx in (-1, 1):
        box(gs, sx * COURT["x"] - (0.0 if sx < 0 else 0.5), sx * COURT["x"] + (0.5 if sx < 0 else 0.0), 0.0, 0.18, COURT["z0"] + 0.5, COURT["z1"], "TNESW")
    return P


def build_woldae():
    P = Piece()
    for name, (x1, z0, z1, y0, y1) in TIERS.items():
        tier_block(P, x1, z0, z1, y0, y1)
        panels_on_neck(P, x1, z0, z1, y0, y1, skip_x=STAIR_HALF + 1.5)
    stair_stone(P)
    return P


def build_balustrades():
    P = Piece()
    balustrade_runs(P)
    return P


# ======================================================================================================================
def build_hall():
    """The ground floor of the hall: columns (porch, wall line, inner, rear), walls with the central doorway, lattice doors and windows, beams,
    bracket sets on every side, the doors' leaves swung open, the ceiling's coffers. Returns (Piece, info)."""
    P = Piece()
    st = ST
    gw = P.geo(st.wall)
    gp = P.geo(st.paint)
    gg = P.geo(st.gold)
    ytop = COL_TOP
    # columns
    for z in COL_Z:
        for x in COL_X:
            det = 2 if z == -12.0 else 0
            seg = 12 if z == -12.0 else 8
            P.add(K.pillar(st, COL_H, foot=True, seg=seg, detail=det), t=(x, FLOOR, z))
    # beams: porch row (front), the rear row, the sides, cross beams from the porch to the wall line
    def beams(x0, x1, z, depth=0.62):
        box(gp, x0, x1, ytop - BEAM, ytop - BEAM + 0.7, z - depth, z + depth, "TBNESW")
        box(gp, x0, x1, ytop - BEAM + 0.7, ytop, z - depth + 0.1, z + depth - 0.1, "TBNESW")
    beams(-27.38, 27.38, -12.0)
    beams(-27.38, 27.38, 12.0)
    for x in (-28.0, 28.0):
        for (za, zb) in ((-11.38, 11.38),):
            box(gp, x - 0.62, x + 0.62, ytop - BEAM, ytop - BEAM + 0.7, za, zb, "TBNESW")
            box(gp, x - 0.52, x + 0.52, ytop - BEAM + 0.7, ytop, za, zb, "TBNESW")
    for x in COL_X:     # tie beams across the porch and over the hall
        for (za, zb) in ((-11.4, -4.6), (-3.4, 3.4), (4.6, 11.4)):
            if x in (-28.0, 28.0):
                continue
            box(gp, x - 0.45, x + 0.45, ytop - BEAM + 0.1, ytop - 0.1, za, zb, "TBNESW")
    # gold on the upper beam's ends at each column
    for z in (-12.0, 12.0):
        for x in COL_X:
            box(gg, x - 0.95, x + 0.95, ytop - 0.55, ytop - 0.05, z - 0.66 if z < 0 else z + 0.46, z - 0.46 if z < 0 else z + 0.66, "TBNESW")
    # ---- walls
    def wall_run(x0, x1, z, y0, y1, openings=(), t=0.9):
        """Plaster wall along x with openings [(xa, xb, ya, yb)]."""
        cur = x0
        for (xa, xb, ya, yb) in sorted(openings):
            if xa > cur:
                box(gw, cur, xa, y0, y1, z - t / 2, z + t / 2, "TBNESW")
            box(gw, xa, xb, y0, ya, z - t / 2, z + t / 2, "TNESW") if ya > y0 else None
            box(gw, xa, xb, yb, y1, z - t / 2, z + t / 2, "TBNESW") if yb < y1 else None
            cur = xb
        if cur < x1:
            box(gw, cur, x1, y0, y1, z - t / 2, z + t / 2, "TBNESW")
    wall_top = ytop - BEAM
    door_x = 3.15
    # front wall z = -4: the central doorway, lattice doors in bays 2 and 4 (closed), windows in bays 1 and 5
    wall_run(-28.0, 28.0, WALL_Z_FRONT, FLOOR, wall_top, openings=[(-door_x, door_x, FLOOR, wall_top),
                                                                    (-11.1, -4.9, FLOOR, wall_top), (4.9, 11.1, FLOOR, wall_top),
                                                                    (-19.1, -12.9, FLOOR, wall_top), (12.9, 19.1, FLOOR, wall_top),
                                                                    (-27.1, -20.9, FLOOR + 3.0, wall_top - 1.0), (20.9, 27.1, FLOOR + 3.0, wall_top - 1.0)])
    # the lattice doors (bays at x +-8 and +-16: full-height lattice screens) and windows (the end bays)
    scr = K.lattice(st, 6.2, wall_top - FLOOR, nx=4, ny=6, frame=0.3, bar=0.12, pattern="grid")
    for x in (-16.0, -8.0, 8.0, 16.0):
        P.add(scr, t=(x, FLOOR, WALL_Z_FRONT - 0.05))
    win = K.lattice(st, 6.2, 5.0, nx=4, ny=3, frame=0.25, bar=0.12)
    for x in (-24.0, 24.0):
        P.add(win, t=(x, FLOOR + 3.0, WALL_Z_FRONT - 0.05))
    # the main door's leaves thrown fully open against the wall's inner face (each 3.15 wide, hinged at the jambs)
    leaf = K.door_leaf(st, 3.15, wall_top - FLOOR - 0.2)
    P.add(leaf, t=(-door_x, FLOOR, -3.325), yaw=math.pi)
    P.add(leaf, t=(door_x, FLOOR, -3.325), yaw=math.pi, mx=True)
    # the lintel transom over the doorway: a lattice band
    # rear wall z = 12: bays 2 and 4 are open doorways (x +-4.85..11.15), the middle bay holds the sealed vault, bays 1 and 5 windows
    wall_run(-28.0, 28.0, WALL_Z_REAR, FLOOR, wall_top, openings=[(-11.15, -4.85, FLOOR, wall_top), (4.85, 11.15, FLOOR, wall_top),
                                                                    (-19.1, -12.9, FLOOR + 3.0, wall_top - 1.0), (12.9, 19.1, FLOOR + 3.0, wall_top - 1.0),
                                                                    (-27.1, -20.9, FLOOR + 3.0, wall_top - 1.0), (20.9, 27.1, FLOOR + 3.0, wall_top - 1.0)])
    for x in (-24.0, -16.0, 16.0, 24.0):
        P.add(win, t=(x, FLOOR + 3.0, WALL_Z_REAR - 0.05))
    # side walls x = +-20 from z -4 to 12: two bays, each a window
    for sx in (-1, 1):
        xw = sx * 28.0
        yaw = -math.pi / 2 if sx > 0 else math.pi / 2
        # the wall as a face piece: along z from -4 to 12 (two bays of 8)
        for zc in (0.0, 8.0):
            lo, hi = zc - 4 + 0.95, zc + 4 - 0.95
            box(gw, xw - 0.45, xw + 0.45, FLOOR, FLOOR + 3.0, lo, hi, "TNESW")
            box(gw, xw - 0.45, xw + 0.45, wall_top - 1.0, wall_top, lo, hi, "TBNESW")
            box(gw, xw - 0.45, xw + 0.45, FLOOR + 3.0, wall_top - 1.0, lo, lo + 0.5, "TBNESW")
            box(gw, xw - 0.45, xw + 0.45, FLOOR + 3.0, wall_top - 1.0, hi - 0.5, hi, "TBNESW")
            P.add(K.lattice(st, hi - lo - 1.0, 5.0, nx=3, ny=3, frame=0.25, bar=0.12), t=(xw, FLOOR + 3.0, (lo + hi) / 2), yaw=yaw)
    # ---- brackets: heads of 1.7 wide, middle sets 1.0 wide, arms never overlapping their neighbours
    ytop_b = ytop
    head3 = K.bracket_set(st, layers=3, w=1.7, h=HB1, reach=1.3, detail=2)
    mid2 = K.bracket_set(st, layers=2, w=1.3, h=HB1, reach=1.9, detail=1)
    head2 = K.bracket_set(st, layers=1, w=1.7, h=HB1, reach=1.9, detail=0)
    mid1 = K.bracket_set(st, layers=1, w=1.2, h=HB1, reach=1.9, detail=0)
    # front (N face, z = -12): a three-layer head on every column, two two-layer sets in each bay (spacing 8 / 3)
    for i in range(8):
        P.add(head3, t=(-28.0 + 8.0 * i, ytop_b, -12.0))
    for i in range(7):
        P.add(mid2, t=(-28.0 + 8.0 * i + 4.0, ytop_b, -12.0))
    # rear (S face, z = 12): a head on every column, one set per bay
    for i in range(8):
        P.add(head2, t=(-28.0 + 8.0 * i, ytop_b, 12.0), yaw=math.pi)
    for i in range(7):
        P.add(mid1, t=(-24.0 + 8.0 * i, ytop_b, 12.0), yaw=math.pi)
    # sides (x = +-28): a head on the middle columns (z -4, 4) and a set in each of the three bays between z -12 and 12
    for sx in (-1, 1):
        yaw = -math.pi / 2 if sx > 0 else math.pi / 2
        for z in (-4.0, 4.0):
            P.add(head2, t=(sx * 28.0, ytop_b, z), yaw=yaw)
        for z in (-8.0, 0.0, 8.0):
            P.add(mid1, t=(sx * 28.0, ytop_b, z), yaw=yaw)
    # ---- the ceiling: coffers (a flat azure ceiling with gold ribs) over the hall
    zc0, zc1 = WALL_Z_FRONT + 0.45, WALL_Z_REAR - 0.45
    cy = ytop - BEAM - 0.05
    box(gp, -27.55, 27.55, cy, cy + 0.2, zc0, zc1, "B")
    for x in range(-24, 25, 8):
        box(gg, x - 0.18, x + 0.18, cy - 0.06, cy, zc0, zc1, "BNESW")
    for z in (0.0, 8.0):
        box(gg, -27.55, 27.55, cy - 0.06, cy, z - 0.18, z + 0.18, "BNESW")
    return P


def build_vault_door():
    """The sealed vault door in the hall's rear wall (middle bay): a marble portal frame, two azure leaves bound with gold bars and studs, a gold lock
    plate with a small azure glow. Origin: the door's floor centre on the wall's inner face (z = 11.55); it faces -z."""
    P = Piece()
    st = ST
    gm = P.geo(st.stone)
    gg = P.geo(st.gold)
    ga = P.geo(st.paint)
    gl = P.geo(st.glow)
    h = COL_TOP - BEAM - FLOOR - 0.6
    w = 6.0
    # the frame: two jambs, a lintel with a gold cap
    box(gm, -w / 2 - 1.0, -w / 2, 0.0, h + 0.8, -1.2, 0.0, "TNESW")
    box(gm, w / 2, w / 2 + 1.0, 0.0, h + 0.8, -1.2, 0.0, "TNESW")
    box(gm, -w / 2 - 1.2, w / 2 + 1.2, h, h + 0.9, -1.4, 0.0, "TBNESW")
    box(gg, -w / 2 - 1.3, w / 2 + 1.3, h + 0.9, h + 1.1, -1.5, 0.05, "TBNESW")
    # the leaves, shut: two doors side by side, a hair apart, set 0.3 in front of the wall
    for sx in (-1, 1):
        leaf = K.door_leaf(st, w / 2 - 0.05, h - 0.15, thick=0.5, studs=(2, 6))
        # the leaf runs +x from its hinge: the left leaf hinges at -w/2, the right leaf (mirrored) at +w/2
        if sx < 0:
            P.add(leaf, t=(-w / 2, 0.0, -0.35))
        else:
            P.add(leaf, t=(w / 2, 0.0, -0.35), mx=True)
    # iron bars across both leaves
    for y in (h * 0.28, h * 0.72):
        box(gg, -w / 2 + 0.1, w / 2 - 0.1, y - 0.2, y + 0.2, -0.78, -0.5, "TBNESW")
    # the lock plate and its glow (a small saturated azure accent)
    lathe_plate = P.geo(st.gold)
    K.lathe_xy(lathe_plate, 0.0, h * 0.5, 0.75, 0.3, 0.08, 12, -0.58)
    K.lathe_xy(gl, 0.0, h * 0.5, 0.45, 0.14, 0.04, 12, -0.66)
    return P


# ======================================================================================================================
def build_interior():
    """The hall's floor details and the Master's dais: gold inlay lines, a one-stud dais (x +-3, z 2..7), steps, the crest in the floor."""
    P = Piece()
    st = ST
    gm = P.geo(st.stone)
    gg = P.geo(st.goldflat)
    gs = P.geo(st.stone2)
    ga = P.geo(st.paint)
    # the dais (top y 10) with a granite kerb and a front step... a one-stud rise
    box(gm, -3.0, 3.0, FLOOR, FLOOR + 1.0, 2.0, 7.0, "TNESW")
    box(gs, -3.2, 3.2, FLOOR, FLOOR + 0.12, 1.8, 7.2, "TNESW")
    box(gg, -2.6, 2.6, FLOOR + 1.0, FLOOR + 1.05, 2.4, 6.6, "TNESW")
    # the path of gold inlay down the hall's middle from the doorway to the dais
    box(gg, -0.18, 0.18, FLOOR, FLOOR + 0.04, -3.5, 1.8, "TNESW")
    for x in (-3.0, 3.0):
        box(gg, x - 0.1, x + 0.1, FLOOR, FLOOR + 0.04, -3.5, 1.8, "TNESW")
    # the crest on the dais front? (a floor medallion before it)
    K.crest(gg, st, 1.6, (0.0, FLOOR + 0.05, 0.2), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), 0.04)
    return P


# ======================================================================================================================
def build_roof1():
    """The hall's lowest roof: eave tip rectangle 26 x 18 at y 21.2 rising to the second storey's column line (14 x 8)."""
    ye = COL_TOP + HB1 * 0.55 - 0.0
    ye = COL_TOP + 1.2
    P = K.roof(ST, 34.0, 18.0, 21.0, 9.0, ye, ye + 5.2, detail=2, pitch=2.1)
    return P, ye, ye + 5.2


def build_stack(y0):
    pcs, info = K.tiers_block(ST, y0, STACK)
    return pcs, info


def build_tower():
    """One tower: origin at its floor centre; the granite plinth ring below; three tiers; a gold finial."""
    pcs, info = K.tiers_block(ST, 0.0, TOWER)
    P = Piece()
    for p in pcs:
        P.add(p)
    return P, info


def build_pavilion(closed_back=False):
    """A gate pavilion, origin at its floor centre: a 12 x 12 granite plinth (1 stud, the step up), four-sided open kiosk with a marble rail, a hip roof and a
    small upper roof with a finial."""
    P = Piece()
    st = ST
    gs = P.geo(st.stone2)
    gm = P.geo(st.stone)
    box(gs, -6.0, 6.0, -7.0, -0.2, -6.0, 6.0, "NESW")
    box(gm, -6.0, 6.0, -0.2, 0.0, -6.0, 6.0, "TNESW")
    pcs, info = K.tiers_block(st, 0.0, PAVILION)
    for p in pcs:
        P.add(p)
    # rails between the columns on the E and W faces, and the outer bays of N and S (the middle bay stays open: a way through)
    for sx in (-1, 1):
        P.add(K.balustrade(st, 10.0, h=2.2, post_every=5.0, thick=0.7), t=(sx * 5.0, 0.0, -5.0), yaw=-math.pi / 2)
    return P, info


def build_lantern():
    return K.lantern(ST, h=9.0)


def build_banner():
    return K.banner(ST, 7.5, 11.0)


def build_flag():
    """A tall flag: a gold pole (origin at its foot) with a finial, a crossbar near the top and a hanging banner."""
    P = Piece()
    st = ST
    gg = P.geo(st.gold)
    lathe(gg, [(0.0, 0.0), (0.7, 0.0), (0.7, 0.6), (0.3, 0.9), (0.3, 25.0), (0.5, 25.2), (0.0, 26.5)], 8, caps=False)
    b = K.banner(st, 5.0, 14.0, two_sided=True)
    P.add(b, t=(0.0, 24.0, -0.55))
    return P


def build_spire():
    return K.spire(ST, base_y=0.0, crystal_h=15.0, ring_r=9.0)


def build_basin():
    """A stone basin (a trough 6 x 3.2, 0.9 high) with a still pool: marble rim, granite foot, water surface."""
    P = Piece()
    st = ST
    gm = P.geo(st.stone)
    gs = P.geo(st.stone2)
    gw = P.geo(st.water)
    x0, x1, z0, z1 = -3.0, 3.0, -1.6, 1.6
    box(gs, x0 - 0.2, x1 + 0.2, 0.0, 0.3, z0 - 0.2, z1 + 0.2, "TNESW")
    t = 0.45
    box(gm, x0, x1, 0.3, 1.0, z0, z0 + t, "TBNESW")
    box(gm, x0, x1, 0.3, 1.0, z1 - t, z1, "TBNESW")
    box(gm, x0, x0 + t, 0.3, 1.0, z0 + t, z1 - t, "TNESW")
    box(gm, x1 - t, x1, 0.3, 1.0, z0 + t, z1 - t, "TNESW")
    box(gw, x0 + t, x1 - t, 0.3, 0.8, z0 + t, z1 - t, "TNESW")
    return P


def mound_ring(cx, cz, rx, rz, n=18, seed=2):
    ring = []
    for k in range(n):
        a = K.TAU * k / n
        j = 1.0 + 0.1 * (K._noise(k, 1, 1, seed) - 0.5) * 2
        ring.append((cx + rx * j * math.cos(a), cz + rz * j * math.sin(a)))
    return ring


def build_rock():
    """The rock under the towers (a mound with a ring of craggy blocks) and two garden rocks at the court's sides: the right side built, then
    mirrored (exact symmetry)."""
    half = Piece()
    half.add(K.rock_mound(ST, mound_ring(TOWER_AT[0], 0.0, 9.5, 14.5, 24, 3), -8.0, TOWER_AT[1], levels=5, seed=3, jitter=0.8, inset=1.2, ledge=0.5, top_flat=0.0))
    half.add(K.rock_blocks(ST, TOWER_AT[0] + 0.5, 0.0, 9.0, 14.0, -8.0, TOWER_AT[1] - 1.0, n=12, seed=11, size=(4.0, 7.0)))
    half.add(K.rock_blocks(ST, TOWER_AT[0] + 0.5, 0.0, 6.5, 10.5, -8.0, TOWER_AT[1] - 0.2, n=9, seed=13, size=(3.5, 6.0), start=0.3))
    half.add(K.rock_mound(ST, mound_ring(48.0, -31.0, 5.5, 5.5, 14, 5), -8.0, 3.2, levels=4, seed=5, jitter=0.6, inset=1.4, ledge=0.4, top_flat=0.4))
    half.add(K.rock_blocks(ST, 48.0, -31.0, 5.0, 5.0, -8.0, 2.4, n=8, seed=17, size=(3.0, 5.0)))
    half.add(K.rock_mound(ST, mound_ring(48.0, 25.0, 7.0, 10.0, 16, 7), -8.0, 5.0, levels=4, seed=7, jitter=0.7, inset=1.6, ledge=0.5, top_flat=0.5))
    half.add(K.rock_blocks(ST, 48.0, 25.0, 6.5, 9.5, -8.0, 4.0, n=10, seed=19, size=(3.5, 6.0)))
    P = Piece()
    P.add(half)
    P.add(half.mirrored())
    return P


# ======================================================================================================================
# assembling everything: pieces, placements, collision boxes, markers
# ======================================================================================================================
def _box_c(x0, x1, y0, y1, z0, z1, name):
    return dict(name=name, x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z1)


def build_all():
    pieces = {}
    place = []
    coll = []
    marks = {}

    def add_piece(name, piece):
        piece.finish()
        pieces["Orthodox_" + name] = piece
        return piece

    def put(name, x, y, z, yaw=0.0, scale=1.0, role=None, **extra):
        d = dict(piece="Orthodox_" + name, x=x, y=y, z=z, yaw=yaw, scale=scale, role=role or "decor")
        d.update(extra)
        place.append(d)

    # ---- unique masses (origin: the pad frame's)
    add_piece("Court", build_court())
    add_piece("Woldae", build_woldae())
    add_piece("Balustrades", build_balustrades())
    add_piece("HallBody", build_hall())
    add_piece("HallInterior", build_interior())
    roof1, ye1, yt1 = build_roof1()
    add_piece("HallRoof1", roof1)
    pcs, info = build_stack(yt1)
    for i, p in enumerate(pcs):
        add_piece("HallTier%d" % (i + 2), p)
    add_piece("Rock", build_rock())
    add_piece("VaultDoor", build_vault_door())
    # ---- instanced
    tower, tinfo = build_tower()
    add_piece("Tower", tower)
    pav, pinfo = build_pavilion()
    add_piece("GatePavilion", pav)
    add_piece("Lantern", build_lantern())
    add_piece("Banner", build_banner())
    add_piece("Flag", build_flag())
    spire = build_spire()
    add_piece("Spire", spire)
    add_piece("Basin", build_basin())
    # ---- placements
    for name in ("Court", "Woldae", "Balustrades", "HallBody", "HallInterior", "HallRoof1", "Rock"):
        put(name, 0.0, 0.0, 0.0, role="unique")
    for i in range(len(pcs)):
        put("HallTier%d" % (i + 2), 0.0, 0.0, 0.0, role="unique")
    put("VaultDoor", 0.0, FLOOR, WALL_Z_REAR - 0.45, role="vault")
    for sx in (-1, 1):
        put("Tower", sx * TOWER_AT[0], TOWER_AT[1] + 0.8, TOWER_AT[2], role="tower")
        put("GatePavilion", sx * PAVILION_FRONT[0], PAVILION_FRONT[1], PAVILION_FRONT[2], role="pavilion")
        put("Flag", sx * 40.0, 3.0, -26.5, role="flag")
        put("Banner", sx * 17.0, ye1 - 0.4, -18.9, role="banner")
    put("GatePavilion", PAVILION_REAR[0], PAVILION_REAR[1], PAVILION_REAR[2], yaw=math.pi, role="pavilion")
    put("Banner", 0.0, COL_TOP - BEAM + 0.1, WALL_Z_REAR + 1.4, yaw=math.pi, role="banner", rear=True)
    apex = info[-1]["top"] + 0.7
    put("Spire", 0.0, apex, 0.0, role="spire")
    for (x, y, z, yaw, light) in LANTERN_SPOTS:
        put("Lantern", x, y, z, yaw=yaw, role="lantern", light=light)
    for sx in (-1, 1):
        put("Basin", sx * 16.0, 3.0, -24.2, role="basin")
        put("Basin", sx * 37.5, -0.4, -19.0, role="basin")
    # ---- collision boxes
    C = coll.append
    C(_box_c(-COURT["x"], COURT["x"], -6.0, 0.0, COURT["z0"], COURT["z1"], "Court"))
    ys = {"A": -8.0, "B": 3.0, "C": 6.0}
    for name, (x1, z0, z1, y0, y1) in TIERS.items():
        C(_box_c(-x1 - 0.3, x1 + 0.3, ys[name], y1, z0 - 0.3, z1 + 0.3, "Tier" + name))
    flights = [(0.0, [(-31.0, -29.5), (-29.5, -28.0)]), (3.0, [(-24.0, -22.5), (-22.5, -21.0)]), (6.0, [(-17.0, -15.5), (-15.5, -14.0)])]
    stair_steps = []
    for base, treads in flights:
        for k, (z0, z1) in enumerate(treads):
            top = base + k + 1
            C(_box_c(-STAIR_HALF, STAIR_HALF, base, top, z0, z1, "Step"))
            stair_steps.append((top, z0, z1))
            for sx in (-1, 1):
                x0, x1 = (STAIR_HALF, STAIR_HALF + 0.8) if sx > 0 else (-STAIR_HALF - 0.8, -STAIR_HALF)
                C(_box_c(x0, x1, base, top + 1.8, z0, z1, "StairWall"))
    # the hall: walls, columns, the dais
    wt = COL_TOP - BEAM
    C(_box_c(-29.0, -3.15, FLOOR, wt, WALL_Z_FRONT - 0.45, WALL_Z_FRONT + 0.45, "WallFront"))
    C(_box_c(3.15, 29.0, FLOOR, wt, WALL_Z_FRONT - 0.45, WALL_Z_FRONT + 0.45, "WallFront"))
    C(_box_c(-29.0, -11.15, FLOOR, wt, WALL_Z_REAR - 0.45, WALL_Z_REAR + 0.45, "WallRear"))
    C(_box_c(-4.85, 4.85, FLOOR, wt, WALL_Z_REAR - 0.45, WALL_Z_REAR + 0.45, "WallRear"))
    C(_box_c(11.15, 29.0, FLOOR, wt, WALL_Z_REAR - 0.45, WALL_Z_REAR + 0.45, "WallRear"))
    for sx in (-1, 1):
        C(_box_c(sx * 28.0 - 0.45, sx * 28.0 + 0.45, FLOOR, wt, WALL_Z_FRONT - 0.45, WALL_Z_REAR + 0.45, "WallSide"))
    for z in COL_Z:
        for x in COL_X:
            C(_box_c(x - 0.85, x + 0.85, FLOOR, COL_TOP, z - 0.85, z + 0.85, "Column"))
    C(_box_c(-3.0, 3.0, FLOOR, FLOOR + 1.0, 2.0, 7.0, "Dais"))
    # the balustrades on the tiers (a rail you cannot walk through; the stair's gap stays open)
    for name, (x1, z0, z1, y0, y1) in TIERS.items():
        L = {"A": 32.0, "B": 28.0, "C": 24.0}[name]
        xs = x1 - 0.8 - L
        zc = z0 + 0.15
        for sx in (-1, 1):
            xa, xb = (xs, xs + L) if sx > 0 else (-xs - L, -xs)
            C(_box_c(xa, xb, y1, y1 + 2.6, zc - 0.45, zc + 0.45, "Balustrade"))
            xx = sx * (x1 - 0.8)
            C(_box_c(xx - 0.4, xx + 0.4, y1, y1 + 1.8, z0 + 0.15, z1 - 0.15, "Parapet"))
        C(_box_c(-(x1 - 0.8), x1 - 0.8, y1, y1 + 1.8, z1 - 0.15 - 0.4, z1 - 0.15 + 0.4, "Parapet"))
    # rock mounds and towers (not enterable)
    for sx in (-1, 1):
        C(_box_c(*sorted((sx * 38.0, sx * 54.0)), -8.0, TOWER_AT[1], -13.0, 13.0, "Mound"))
        C(_box_c(*sorted((sx * 38.5, sx * 51.5)), TOWER_AT[1], TOWER_AT[1] + 9.0, -6.5, 6.5, "TowerBody"))
        C(_box_c(*sorted((sx * 43.0, sx * 53.0)), -8.0, 3.2, -36.0, -26.0, "GardenRock"))
        C(_box_c(*sorted((sx * 42.0, sx * 54.0)), -8.0, 5.0, 15.0, 35.0, "GardenRock"))
        # gate pavilions (front): plinth, columns, rails on the E/W faces
        px, py, pz = sx * PAVILION_FRONT[0], PAVILION_FRONT[1], PAVILION_FRONT[2]
        C(_box_c(px - 6.0, px + 6.0, -6.0, py, pz - 6.0, pz + 6.0, "PavilionPlinth"))
        for dx in (-5.0, 0.0, 5.0):
            for dz in (-5.0, 5.0):
                C(_box_c(px + dx - 0.7, px + dx + 0.7, py, py + 7.5, pz + dz - 0.7, pz + dz + 0.7, "PavilionColumn"))
        for dx in (-5.0, 5.0):
            C(_box_c(px + dx - 0.35, px + dx + 0.35, py, py + 2.2, pz - 5.0, pz + 5.0, "PavilionRail"))
            C(_box_c(px + dx - 0.7, px + dx + 0.7, py, py + 7.5, pz - 0.7, pz + 0.7, "PavilionColumn"))
        C(_box_c(*sorted((sx * 15.2, sx * 16.8)), 3.0, 4.0, -25.8, -22.6, "Basin"))
        C(_box_c(*sorted((sx * 34.2, sx * 40.8)), -0.4, 0.6, -20.8, -17.2, "Basin"))
    rx, ry, rz = PAVILION_REAR
    C(_box_c(rx - 6.0, rx + 6.0, 3.0, ry, rz - 6.0, rz + 6.0, "PavilionPlinth"))
    for dx in (-5.0, 0.0, 5.0):
        for dz in (-5.0, 5.0):
            C(_box_c(rx + dx - 0.7, rx + dx + 0.7, ry, ry + 7.5, rz + dz - 0.7, rz + dz + 0.7, "PavilionColumn"))
    for dx in (-5.0, 5.0):
        C(_box_c(rx + dx - 0.35, rx + dx + 0.35, ry, ry + 2.2, rz - 5.0, rz + 5.0, "PavilionRail"))
        C(_box_c(rx + dx - 0.7, rx + dx + 0.7, ry, ry + 7.5, rz - 0.7, rz + 0.7, "PavilionColumn"))
    for (x, y, z, yaw, light) in LANTERN_SPOTS:
        C(_box_c(x - 0.9, x + 0.9, y, y + 4.0, z - 0.9, z + 0.9, "Lantern"))
    # ---- markers
    marks["VaultSpot"] = dict(pos=(0.0, FLOOR, WALL_Z_REAR - 2.6), yaw=0.0, note="clear floor before the sealed vault door (the model tagged FactionVault goes here: 6 wide, 3 deep, 8 high)")
    marks["MasterSpot"] = dict(pos=(0.0, FLOOR + 1.0, 4.5), yaw=0.0, note="the Master's standing place on the one-stud dais, facing the main door")
    marks["CourtCentre"] = dict(pos=(0.0, 0.0, -41.0), yaw=0.0, note="the crest inlaid in the front court")
    marks["HallDoor"] = dict(pos=(0.0, FLOOR, WALL_Z_FRONT), yaw=0.0, note="the open main door (6.3 wide, 9.5 high)")
    marks["InnerCourt"] = dict(pos=(0.0, FLOOR, 22.0), yaw=0.0, note="the inner court behind the hall")
    marks["StairTop"] = dict(pos=(0.0, 0.0, -52.0), yaw=0.0, note="where the plaza stairway meets the court (pad ground is 0.5 lower)")
    marks["SpireGlow"] = dict(pos=(0.0, apex + 1.2 + 15.0 * 0.52, 0.0), yaw=0.0, note="the crystal's middle (the halo rings centre on it)")
    falls = [dict(lip=(sx * 16.0, 5.0, -21.5), frm=(sx * 16.0, 5.4, -19.5), zone="stair") for sx in (-1, 1)]
    falls += [dict(lip=(sx * 38.5, 6.0, -11.6), frm=(sx * 38.5, 6.2, -8.6), zone="mound") for sx in (-1, 1)]
    trees = [(sx * 36.0, -0.3, -36.0) for sx in (-1, 1)] + [(sx * 38.0, -0.3, -24.5) for sx in (-1, 1)] + [(sx * 19.0, 9.0, 27.0) for sx in (-1, 1)]
    return dict(pieces=pieces, placements=place, colliders=coll, marks=marks, falls=falls, trees=trees, stack=info, roof1=(ye1, yt1), tower=tinfo,
                pavilion=pinfo, apex=apex)


def stats(data):
    pieces = data["pieces"]
    count = {}
    for p in data["placements"]:
        count[p["piece"]] = count.get(p["piece"], 0) + 1
    rows = []
    total = 0
    for name, piece in sorted(pieces.items()):
        n = count.get(name, 0)
        t = piece.tris()
        rows.append((name, t, n, t * n, piece.stats()))
        total += t * n
    return rows, total


if __name__ == "__main__":
    d = build_all()
    rows, total = stats(d)
    for name, t, n, tn, per in rows:
        print("%-24s %6d tris x %2d = %6d   %s" % (name, t, n, tn, per))
    print("TOTAL as placed", total)
    print("colliders", len(d["colliders"]))
