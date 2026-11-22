"""The review stages for the Demonic sword (run inside Blender, headless): everything the owner's process asks to see, written to
renders/faction_weapons_v2/Demonic/ (local, never committed).

    clay        the high-detail source in neutral grey from six views, and close-ups of guard, grip, pommel
    game        the game mesh dressed in its four baked maps: six views under neutral light and under a dark dramatic light (the
                VFX-off test: no glow anywhere), close-ups of guard, grip and pommel, the point, the fuller's engraving
    sections    the blade's cross-section at four stations
    silhouette  the black silhouette at thumbnail size, from the flat, the edge and three-quarters
    hand        the R15 right hand and lower arm at true size round the grip, from the flat and the edge, with the numbers
    compare     the sword and Sword6 side by side at one scale, both in the same hand
    maps        the four maps large, and at thumbnail size on a dark ground (for the stranger's look)
    qa          the asset gate, profile roblox, and the maps' statistics
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import secret_kit as SK  # noqa: E402
import secret_lab as L  # noqa: E402
import secret_review as R  # noqa: E402
import sword_demonic_lab as LAB  # noqa: E402
import sword_demonic_text as T  # noqa: E402

V = SK.V
REVIEW = LAB.REVIEW
WID = "SecretDemonic"
OUT = SK.OUT_DIR
ASSETS = os.path.join(SK.REPO, "assets", "weapons")

# the weapon spans z -6.25 .. +2.8 (Blender y +6.25 .. -2.8): its middle for the full views
MID = V((0.0, 1.8, 0.0))
FULL = 10.2


def _save(tiles, cols, name, bg=(0.07, 0.075, 0.09, 1.0)):
    return L.save_png(L.sheet(tiles, cols, bg=bg), os.path.join(REVIEW, name))


def _label(img_arr, items):
    h, w = img_arr.shape[:2]
    return T.over(img_arr, T.layer(w, h, items))


def clay(objs, tag="10_clay"):
    LAB.set_mode("clay")
    L.lab()
    with L.clay(objs):
        tiles = [L.shoot(objs, v, size=(300, 700), samples=32, ortho=v in ("top", "bottom", "edge_r", "edge_l"), centre=MID, span=FULL)
                 for v in ("top", "bottom", "edge_r", "edge_l", "front34", "back34")]
        p1 = _save(tiles, 6, tag + "_six_views.png")
        close = []
        for v, c, span, ortho in (("front34", (0.0, 1.0, 0.0), 3.2, False), ("top", (0.0, 1.1, 0.0), 3.2, True), ("back34", (0.0, 1.0, 0.0), 3.2, False),
                                  ("front34", (0.0, -1.2, 0.0), 3.0, False), ("top", (0.0, -1.2, 0.0), 3.0, True), ("edge_r", (0.0, -1.2, 0.0), 3.0, True)):
            close.append(L.shoot(objs, v, size=(480, 480), samples=32, ortho=ortho, centre=V(c), span=span))
        p2 = _save(close, 3, tag + "_closeups.png")
    print("clay:", p1, p2)


def load(folder=None):
    SK.fresh()
    body, glows = R.load_game(WID, folder or OUT)
    return [body] + glows


def game(mine, mode, tag):
    LAB.set_mode(mode)
    L.lab()
    tiles = [L.shoot(mine, v, size=(300, 700), samples=64, ortho=v in ("top", "bottom", "edge_r", "edge_l"), centre=MID, span=FULL)
             for v in ("top", "bottom", "edge_r", "edge_l", "front34", "back34")]
    p1 = _save(tiles, 6, "%s_%s_six_views.png" % (tag, mode))
    return p1


def closeups(mine, mode, tag):
    LAB.set_mode(mode)
    L.lab()
    rows = []
    # guard, from the flat and three-quarters; grip and pommel and the cord; the point; the fuller and its engraving
    specs = (("front34", (0.0, 1.15, 0.0), 3.3, False), ("top", (0.0, 1.0, 0.0), 3.0, True), ("back34", (0.0, 0.5, 0.0), 3.4, False),
             ("top", (0.0, -1.2, 0.0), 3.6, True), ("front34", (0.0, -1.3, 0.0), 3.6, False), ("edge_r", (0.0, -1.2, 0.0), 3.6, True),
             ("front34", (0.35, 5.7, 0.0), 1.9, False), ("top", (0.25, 4.7, 0.0), 2.6, True), ("top", (-0.05, 3.0, 0.0), 2.0, True))
    for v, c, span, ortho in specs:
        rows.append(L.shoot(mine, v, size=(460, 460), samples=64, ortho=ortho, centre=V(c), span=span))
    return _save(rows, 3, "%s_%s_closeups.png" % (tag, mode))


def silhouettes(mine):
    """Black on white, thumbnail size: what the shape says before any paint."""
    out = []
    for view, size in (("top", (140, 420)), ("edge_r", (140, 420)), ("front34", (140, 420)), ("top", (70, 210)), ("edge_r", (70, 210)), ("front34", (70, 210))):
        tile = R.silhouette_tiles(mine, (view,), size=size, ortho=(view != "front34"))[0]
        out.append(tile)
    # the silhouette tiles are framed on the object itself: lay them on one sheet
    p = _save(out, 6, "30_silhouette_black.png", bg=(0.5, 0.5, 0.5, 1.0))
    return p


def vfx_off(mine):
    ps = []
    for mode in ("neutral", "dramatic"):
        LAB.set_mode(mode)
        L.lab()
        tiles = [L.shoot(mine, v, size=(380, 820), samples=96, ortho=ortho, centre=MID, span=FULL) for v, ortho in (("top", True), ("front34", False), ("back34", False))]
        ps.append(_save(tiles, 3, "31_vfx_off_%s.png" % mode))
    return ps


def hand(mine, name="40_hand_test"):
    """The weapon in a true R15 hand: a stand-in for the hand and forearm blocks, the numbers beside the pictures."""
    LAB.set_mode("neutral")
    L.lab()
    scene = bpy.context.scene
    hand_objs = LAB.r15_hand(scene.collection)
    body = mine[0]
    pts = np.array([[(body.matrix_world @ v.co).x, (body.matrix_world @ v.co).z, -(body.matrix_world @ v.co).y] for v in body.data.vertices])   # Roblox space
    boxes = LAB.hand_boxes()
    d = LAB.min_distance(pts, boxes)
    inside_grip = (np.abs(pts[:, 2]) < 0.5)
    rep = {}
    rep["guard_to_hand_min"] = round(float(d[pts[:, 2] < -0.5].min()), 3)
    rep["pommel_ring_cord_to_hand_min"] = round(float(d[pts[:, 2] > 0.7].min()), 3)
    rep["points_of_pommel_ring_cord_inside_hand_or_forearm"] = int((d[pts[:, 2] > 0.7] < 0).sum())
    rep["grip_between"] = [round(float(pts[inside_grip][:, 2].min()), 3), round(float(pts[inside_grip][:, 2].max()), 3)]
    print("hand test:", rep)
    held = [L.shoot(mine + hand_objs, v, size=(560, 640), samples=48, centre=V((0.0, -0.4, 0.0)), span=4.6, ortho=ortho)
            for v, ortho in (("top", True), ("edge_r", True), ("front34", False), ("back34", False))]
    p = _save(held, 4, name + ".png")
    for o in hand_objs:
        L.set_visible([o], False)
    return rep


def compare(mine):
    """Next to Sword6 (the Immortal realm sword) at one scale, both in a hand."""
    LAB.set_mode("neutral")
    L.lab()
    scene = bpy.context.scene
    hand_objs = LAB.r15_hand(scene.collection, alpha=0.3)
    obody, oglows = R.load_game("Sword6", ASSETS, (3.2, 0, 0))
    others = [obody] + oglows
    for o in hand_objs:
        h2 = o.copy()
        scene.collection.objects.link(h2)
        h2.location = h2.location + V((3.2, 0, 0))
        others.append(h2)
    both = mine + hand_objs + others
    tiles = [L.shoot(both, "top", size=(620, 760), samples=48, ortho=True, centre=V((1.6, 1.8, 0.0)), span=10.4),
             L.shoot(both, "front34", size=(620, 760), samples=48, centre=V((1.6, 1.8, 0.0)), span=10.4)]
    p = _save(tiles, 2, "41_vs_Sword6.png")
    return p


def sections():
    """The blade's cross-section at four stations, drawn from the section function (the same numbers the mesh is built from)."""
    import sword_demonic_blade as BL
    import sword_demonic_profile as P
    stations = (0.5, 2.0, 3.8, 4.7)
    W_, H_ = 360, 300
    tiles = []
    labels = []
    for k, s in enumerate(stations):
        sec = BL.section(np.array([s]), sink=False)
        u, h, Wd = sec["u"][0], sec["h"][0], float(sec["W"][0])
        pts = [(Wd * (1 - x), y) for x, y in zip(u, h)]          # across measured from the edge so the spine is at the right
        pts = [(Wd * x, y) for x, y in zip(u, h)]
        top = [(x, y) for x, y in pts]
        poly = top + [(x, -y) for x, y in top[::-1]]
        tile = np.ones((H_, W_, 4), dtype=np.float32) * np.array([0.95, 0.95, 0.96, 1.0], dtype=np.float32)
        scale = 300.0 / 1.1
        yy = np.arange(H_)[:, None] + 0.5
        xx = np.arange(W_)[None, :] + 0.5
        inside = np.zeros((H_, W_), dtype=bool)
        px = [30 + x * scale for x, _ in poly]
        py = [H_ / 2 - y * scale * 2.2 for _, y in poly]
        n = len(poly)
        for i in range(n):
            x0, y0, x1, y1 = px[i], py[i], px[(i + 1) % n], py[(i + 1) % n]
            if y0 == y1:
                continue
            cross = ((y0 <= yy) & (yy < y1)) | ((y1 <= yy) & (yy < y0))
            xi = x0 + (yy - y0) * (x1 - x0) / (y1 - y0)
            inside ^= cross & (xx < xi)
        tile[inside] = np.array([0.1, 0.11, 0.14, 1.0], dtype=np.float32)
        tiles.append(tile)
        labels.append((10 + k * (W_ + 6), 6, "s = %.1f   width %.2f   thick %.3f (drawn 2.2x taller)" % (s, Wd, 2 * float(sec["T"][0])), 13, (0.1, 0.1, 0.12)))
    sheet = L.sheet(tiles, 2, pad=6, bg=(0.85, 0.85, 0.87, 1.0))
    # labels placed per tile
    items = []
    for k, s in enumerate(stations):
        r, c = divmod(k, 2)
        x0 = 6 + c * (W_ + 6)
        y0 = 6 + r * (H_ + 6)
        items.append((x0 + 8, y0 + 6, "s = %.1f studs from the hilt (thickness drawn 2.2 times too tall; the back is on the left, the edge on the right)" % s, 13, (0.1, 0.1, 0.12)))
    sheet = _label(sheet, items)
    return L.save_png(sheet, os.path.join(REVIEW, "24_blade_sections.png"))


def maps_thumbs():
    """The four maps on a dark ground, big, and at thumbnail size, as a stranger sees them."""
    return R.maps_sheet(WID, OUT, os.path.join(REVIEW, "50_maps_thumbs.png"))


def qa(parts):
    res = R.qa(parts)
    stats = R.map_stats(WID, OUT)
    with open(os.path.join(REVIEW, "qa.json"), "w") as f:
        json.dump(dict(maps=stats, qa={k: res[k] for k in ("pass", "errors", "warnings")}), f, indent=1, default=str)
    return res, stats


def run(stage, hi_objs=None):
    if stage == "clay":
        clay(hi_objs)
        return
    mine = load()
    if stage in ("game", "all"):
        for mode in ("neutral", "dramatic"):
            print(game(mine, mode, "20_material"))
            print(closeups(mine, mode, "22_closeups"))
    if stage in ("silhouette", "all"):
        print(silhouettes(mine))
    if stage in ("vfxoff", "all"):
        print(vfx_off(mine))
    if stage in ("hand", "all"):
        print(hand(mine))
    if stage in ("compare", "all"):
        print(compare(mine))
    if stage in ("maps", "all"):
        print(maps_thumbs())
    if stage in ("sections", "all"):
        print(sections())
    if stage in ("qa", "all"):
        print(qa(mine))


if __name__ == "__main__":
    stage = (sys.argv[sys.argv.index("--") + 1:] or ["all"])[0] if "--" in sys.argv else "all"
    run(stage)
