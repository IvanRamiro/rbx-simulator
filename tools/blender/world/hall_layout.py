"""The Hall of Records' layout (the owner, 2026-11-16: 22 Worked Builds/Hall of Records Directive.md; plan in the vault: Hall of Records
Plan 2026-11-16). Pure Python (no bpy): hub_ground.py writes it into Placements/Yggdrasil.lua (HallOfRecords), hall_records.py builds
the pieces to the same numbers, and WorldBuilder.buildHallOfRecords places them, their board faces and, before the owner's import,
a blockout of plain parts.

Frames, all in Roblox studs (Y up):
- the hub's island frame: the hall's centre CENTRE (where the owner stood), turned by YAW so its +Z points at the World Tree;
- the hall's frame: origin on the ground at the court's middle, +Z toward the tree; a station's angle runs from +Z toward +X;
- each piece's own frame: origin at the ground under its base centre, its front +Z (toward the court's middle, but the entrance,
  whose front faces out toward the tree).
"""
import math

OWNER_SPOT = (-151.6, 92.9)   # island-local (the hub's centre is world (0, 200, 0), no turns): where the owner stood, 2026-11-16
# The court's middle: on the old south-west avenue's line, 11 studs from the owner's spot (still on the court), so it fits r 38
# between the pens at bearings 120 and 180 (45 studs to their plots) and the Ring Road (46) (the owner, 2026-11-17: "The hall of
# records is way too crowded, I need you to expand it")
CENTRE = (math.cos(math.radians(151.0)) * 170.0, math.sin(math.radians(151.0)) * 170.0)
COURT_MESH_R = 27.0           # the court as modelled and imported (hall_records.court, HallOfRecords.fbx)
COURT_R = 38.0                # the court as placed: the mesh scaled in X and Z (COURT_SCALE), its height as modelled
COURT_SCALE = COURT_R / COURT_MESH_R
TREE_RING_OUT = 104.0         # hub_ground.RING[1]: where the hall's front flag path starts
RING_ROAD_IN = 216.0          # hub_ground.RING_ROAD[0]: where its back path ends
BACK_EXIT = 152.0             # the back path leaves the court here (degrees), between the hourglass and the stele, toward the Ring Road
                              # by the Beginner Isle's bridge: the south-west avenue's old way from the Tree Ring to the Ring Road


def yaw():
    """The yaw that turns the hall's +Z toward the World Tree (Roblox CFrame.Angles(0, yaw, 0))."""
    return math.atan2(-CENTRE[0], -CENTRE[1])


# (piece, angle in degrees from +Z toward +X, radius, faces_in): faces_in turns the piece's front toward the middle; the entrance
# faces out (its name plaque greets players coming from the tree).
STATIONS = [   # (spread out 2026-11-17: each board 8-10 studs clear of the next, the book 20 studs clear all round)
    ("HR_Trilithon", 0.0, COURT_R - 1.5, False),
    ("HR_Lectern", 0.0, 2.0, False),          # the Chronicle, in the middle: read facing into the court
    ("HR_Stele", 180.0, 29.0, True),          # Highest Cultivation, across from the entrance
    ("HR_Hourglass", 130.0, 28.5, True),      # Longest Cultivators
    ("HR_WantedBoard", -130.0, 28.5, True),   # Greatest Thieves
    ("HR_FirstsWall", 78.0, 30.5, True),      # Hall of Firsts
    ("HR_Showcase", -80.0, 29.5, True),       # Rarest Beasts
    ("HR_BannerPole", 34.0, 33.0, True),
    ("HR_BannerPole", -34.0, 33.0, True),
    ("HR_Court", 0.0, 0.0, False),
]


def stations():
    """[(piece, x, z, yaw)] in the hall's frame."""
    out = []
    for piece, deg, r, faces_in in STATIONS:
        a = math.radians(deg)
        x, z = math.sin(a) * r, math.cos(a) * r
        y = a + math.pi if faces_in else 0.0
        out.append((piece, x, z, math.atan2(math.sin(y), math.cos(y))))
    return out


def _to_island(x, z):
    a = yaw()
    return (CENTRE[0] + x * math.cos(a) + z * math.sin(a), CENTRE[1] - x * math.sin(a) + z * math.cos(a))


def paths():
    """The hall's two flag paths, in its frame: [(start (x, z), end (x, z))]: the front one from just past the entrance to the Tree
    Ring's edge (+Z, toward the tree), the back one from the court's edge at BACK_EXIT out to the Ring Road's inner edge."""
    front = ((0.0, COURT_R + 3.0), (0.0, math.hypot(*CENTRE) - TREE_RING_OUT - 1.0))
    a = math.radians(BACK_EXIT)
    ux, uz = math.sin(a), math.cos(a)
    r = COURT_R + 1.0
    while math.hypot(*_to_island(ux * r, uz * r)) < RING_ROAD_IN - 1.0:
        r += 0.1
    back = ((ux * (COURT_R + 1.6), uz * (COURT_R + 1.6)), (ux * r, uz * r))
    return [front, back]


def flag_path():
    """The slate flags of both paths, in the hall's frame: [(x, z, yaw)], a step apart, each turned and shifted a little so they
    read laid by hand."""
    out = []
    k = 0
    for (x0, z0), (x1, z1) in paths():
        length = math.hypot(x1 - x0, z1 - z0)
        ux, uz = (x1 - x0) / length, (z1 - z0) / length
        heading = math.atan2(ux, uz)
        n = int(length / 3.1) + 1
        for j in range(n):
            t = length * j / max(n - 1, 1)
            side = 0.35 * math.sin(k * 2.1) + 0.2 * math.sin(k * 5.3)
            x, z = x0 + ux * t + uz * side, z0 + uz * t - ux * side
            out.append((round(x, 2), round(z, 2), round(heading + 0.06 * math.sin(k * 3.7) + (0.0 if k % 2 else 0.04), 4)))
            k += 1
    return out


# ---------- each piece's numbers (its own frame) ----------
# The board faces: a SurfaceGui is drawn on an invisible part at each (client/World/HallOfRecords). Centre (x, y, z), size (w, h),
# the face's normal and up (where the GUI's top is).
UP = (0.0, 1.0, 0.0)
FWD = (0.0, 0.0, 1.0)

STELE = {"plinth": [(17.0, 6.6, 0.5), (15.6, 5.6, 0.5), (14.2, 4.6, 0.5)], "slab": (13.0, 2.2, 1.5, 19.5), "taper": 0.6,
         "face": (11.0, 14.0, 9.7)}
_stele_front = -0.4 + STELE["slab"][1] / 2   # the slab stands 0.4 behind the plinth's middle
HOURGLASS = {"pillar": (1.9, 17.0, 4.7), "lintel": (11.6, 1.3, 2.0), "ledger": (7.6, 7.6, 1.3, 1.0), "glass": (8.6, 17.0),
             "face": (6.8, 6.8)}
WANTED = {"posts": (0.9, 10.6, 6.4), "board": (12.2, 7.6, 0.5, 2.4), "face": (11.2, 6.6)}
SHOWCASE = {"plinth": (17.0, 2.2, 3.6), "case": (16.0, 7.4, 2.0), "fascia": (16.4, 1.5), "face": (15.0, 6.3), "title": (14.2, 1.05)}
FIRSTS = {"mid": (10.0, 12.6, 1.6), "side": (8.0, 10.6, 1.6), "turn": 18.0, "gap": 0.5, "plinth": 0.6,
          "mid_face": (9.0, 10.8), "side_face": (7.0, 8.8)}
LECTERN = {"book": (9.0, 6.0), "front_y": 3.4, "slope": 30.0, "page": (4.1, 5.5), "cover": 0.12, "pages": 0.28}


def lectern_plane():
    """The book's frame on the lectern: (centre of its underside, normal, up-the-page), in the piece's frame. The book lies on a rest
    tilted `slope` degrees toward the reader (+Z), its front edge at front_y."""
    a = math.radians(LECTERN["slope"])
    n = (0.0, math.cos(a), math.sin(a))
    up = (0.0, math.sin(a), -math.cos(a))
    c = (0.0, LECTERN["front_y"] + LECTERN["book"][1] / 2 * math.sin(a), 0.0)
    return c, n, up
TRILITHON = {"upright": (2.6, 2.1, 13.2), "opening": 10.0, "lintel": (16.4, 2.3, 2.5), "plaque": (11.0, 1.6)}


def firsts_slabs():
    """The Firsts wall's three slabs: [(name, centre x, z, yaw, (w, h, d))], the middle one at the origin, the sides turned in."""
    mw, mh, md = FIRSTS["mid"]
    sw, sh, sd = FIRSTS["side"]
    t = math.radians(FIRSTS["turn"])
    off = mw / 2 + FIRSTS["gap"] + sw / 2 * math.cos(t)
    fwd = sw / 2 * math.sin(t)
    return [("Left", -off, fwd, t, FIRSTS["side"]), ("Mid", 0.0, 0.0, 0.0, FIRSTS["mid"]), ("Right", off, fwd, -t, FIRSTS["side"])]


def _turn(p, yaw):
    """Turns a point (x, y, z) about the vertical by yaw (Roblox: +yaw turns +Z toward +X)."""
    c, s = math.cos(yaw), math.sin(yaw)
    return (p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c)


def faces():
    """{piece: [(board, centre, (w, h), normal, up)]} in each piece's own frame."""
    out = {}
    w, h, cy = STELE["face"]
    out["HR_Stele"] = [("Qi", (0.0, cy, _stele_front + 0.06), (w, h), FWD, UP)]
    lw, lh, ld, ly = HOURGLASS["ledger"]
    fw, fh = HOURGLASS["face"]
    out["HR_Hourglass"] = [("PlayTime", (0.0, ly + lh / 2, ld / 2 + 0.06), (fw, fh), FWD, UP)]
    bw, bh, bd, by = WANTED["board"]
    fw, fh = WANTED["face"]
    out["HR_WantedBoard"] = [("Thieves", (0.0, by + bh / 2, bd / 2 + 0.07), (fw, fh), FWD, UP)]
    pw, ph, pd = SHOWCASE["plinth"]
    cw, ch, cd = SHOWCASE["case"]
    fw, fh = SHOWCASE["face"]
    tw, th = SHOWCASE["title"]
    fz, fy = SHOWCASE["fascia"]
    out["HR_Showcase"] = [("Rarest", (0.0, ph + ch / 2, -cd / 2 + 0.55), (fw, fh), FWD, UP),
                          ("RarestTitle", (0.0, ph + ch + fy / 2, cd / 2 + 0.09), (tw, th), FWD, UP)]
    out["HR_FirstsWall"] = []
    for name, x, z, yw, (sw, sh, sd) in firsts_slabs():
        board = {"Left": "FirstsGuardian", "Mid": "FirstsRealm", "Right": "FirstsBeast"}[name]
        fw, fh = FIRSTS["mid_face"] if name == "Mid" else FIRSTS["side_face"]
        local = (0.0, FIRSTS["plinth"] + sh / 2 - 0.1, sd / 2 + 0.06)
        c = _turn(local, yw)
        out["HR_FirstsWall"].append((board, (x + c[0], c[1], z + c[2]), (fw, fh), _turn(FWD, yw), UP))
    pw, ph = LECTERN["page"]
    c, n, up = lectern_plane()
    lift = LECTERN["cover"] + LECTERN["pages"] + 0.03   # just over the pages' top
    out["HR_Lectern"] = [(board, (sx * (pw / 2 + 0.15), c[1] + n[1] * lift, c[2] + n[2] * lift), (pw, ph), n, up)
                         for board, sx in (("FeedLeft", -1.0), ("FeedRight", 1.0))]
    uw, ud, uh = TRILITHON["upright"]
    lw, lh, ld = TRILITHON["lintel"]
    pw, ph = TRILITHON["plaque"]
    out["HR_Trilithon"] = [("HallTitle", (0.0, uh + lh / 2, ld / 2 + 0.16), (pw, ph), FWD, UP)]
    return out


# The pre-import blockout: plain boxes per piece (centre, size, colour key), in its own frame. Only for testing the boards
# before the owner imports the hall's meshes; WorldBuilder uses the real kit as soon as it is stored.
def blockout():
    out = {}
    s = STELE
    out["HR_Stele"] = [((0.0, 0.75, 0.0), (17.0, 1.5, 6.6), "Basalt"),
                       ((0.0, 1.5 + s["slab"][3] / 2, -0.4), (s["slab"][0], s["slab"][3], s["slab"][1]), "Basalt"),
                       ((0.0, 1.5 + s["slab"][3] + 0.5, -0.4), (s["slab"][0] + 0.6, 1.0, s["slab"][1] + 0.6), "Bronze")]
    hg = HOURGLASS
    out["HR_Hourglass"] = [((-hg["pillar"][2], hg["pillar"][1] / 2, 0.0), (hg["pillar"][0], hg["pillar"][1], hg["pillar"][0]), "Basalt"),
                           ((hg["pillar"][2], hg["pillar"][1] / 2, 0.0), (hg["pillar"][0], hg["pillar"][1], hg["pillar"][0]), "Basalt"),
                           ((0.0, hg["pillar"][1] + hg["lintel"][1] / 2, 0.0), hg["lintel"], "Basalt"),
                           ((0.0, hg["ledger"][3] + hg["ledger"][1] / 2, 0.0), (hg["ledger"][0], hg["ledger"][1], hg["ledger"][2]), "Basalt"),
                           ((0.0, 12.8, 0.0), (3.6, 8.0, 3.6), "Bronze")]
    wb = WANTED
    out["HR_WantedBoard"] = [((-wb["posts"][2], wb["posts"][1] / 2, 0.0), (wb["posts"][0], wb["posts"][1], wb["posts"][0]), "Timber"),
                             ((wb["posts"][2], wb["posts"][1] / 2, 0.0), (wb["posts"][0], wb["posts"][1], wb["posts"][0]), "Timber"),
                             ((0.0, wb["board"][3] + wb["board"][1] / 2, 0.0), (wb["board"][0], wb["board"][1], wb["board"][2]), "Timber")]
    sc = SHOWCASE
    out["HR_Showcase"] = [((0.0, sc["plinth"][1] / 2, 0.0), sc["plinth"], "Basalt"),
                          ((0.0, sc["plinth"][1] + sc["case"][1] / 2, -sc["case"][2] / 2 + 0.25), (sc["case"][0], sc["case"][1], 0.5), "Basalt"),
                          ((0.0, sc["plinth"][1] + sc["case"][1] + sc["fascia"][1] / 2, 0.0), (sc["fascia"][0], sc["fascia"][1], sc["case"][2]), "Bronze")]
    out["HR_FirstsWall"] = []
    for name, x, z, yw, (w, h, d) in firsts_slabs():
        out["HR_FirstsWall"].append(((x, FIRSTS["plinth"] + h / 2, z), (w, h, d), "Basalt", yw))
    a = math.radians(LECTERN["slope"])
    out["HR_Lectern"] = [((0.0, 1.7, 0.0), (1.2, 3.4, 1.2), "Bronze"),
                         ((0.0, LECTERN["front_y"] + LECTERN["book"][1] / 2 * math.sin(a), 0.0), (LECTERN["book"][0], 0.24, LECTERN["book"][1]),
                          "Parchment", 0.0, a)]
    tr = TRILITHON
    out["HR_Trilithon"] = [((-(tr["opening"] / 2 + tr["upright"][0] / 2), tr["upright"][2] / 2, 0.0), (tr["upright"][0], tr["upright"][2], tr["upright"][1]), "Basalt"),
                           ((tr["opening"] / 2 + tr["upright"][0] / 2, tr["upright"][2] / 2, 0.0), (tr["upright"][0], tr["upright"][2], tr["upright"][1]), "Basalt"),
                           ((0.0, tr["upright"][2] + tr["lintel"][1] / 2, 0.0), (tr["lintel"][0], tr["lintel"][1], tr["lintel"][2]), "Basalt")]
    out["HR_BannerPole"] = [((0.0, 6.0, 0.0), (0.45, 12.0, 0.45), "Bronze"), ((0.0, 7.8, 0.3), (3.0, 7.0, 0.1), "Banner")]
    return out


# Warm lights on the boards at night (piece: (offset in its frame, range, brightness)); the SurfaceGuis are self-lit anyway.
LIGHTS = {"HR_Stele": ((0.0, 19.0, 3.5), 26.0, 0.9), "HR_Lectern": ((0.0, 7.5, 2.5), 14.0, 0.8),
          "HR_Trilithon": ((0.0, 12.0, 3.0), 18.0, 0.6)}
