"""The Orthodox sword's research board and blade drawings (run inside Blender, headless):

    blender -b --factory-startup --python tools/blender/weapons/sword_orthodox_research.py

Writes renders/faction_weapons_v2/Orthodox/research_board.png (what real master-made swords teach, and what was taken from each as a
principle), blade_sections.png (the blade's real cross-sections, from the same functions that build it, beside the classic sections) and
proportions.png (the numbers). Local review images only, never committed.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sword_orthodox_board as BD  # noqa: E402
import sword_orthodox_parts as P  # noqa: E402

REPO = P.W.REPO
REVIEW = os.path.join(REPO, "renders", "faction_weapons_v2", "Orthodox")
BG = (0.07, 0.075, 0.09, 1.0)
INK = (0.9, 0.92, 0.95, 1.0)
DIM = (0.62, 0.66, 0.72, 1.0)
GOLD = (0.93, 0.74, 0.34, 1.0)
STEEL = (0.62, 0.68, 0.78, 1.0)
AZURE = (0.25, 0.5, 0.95, 1.0)


def wrap(cv, text, x, y, width, size=14, color=INK, gap=4):
    """Word-wrapped text; returns the y below it."""
    line = ""
    per = int(width / (size * 0.47))
    for w in text.split():
        if len(line) + 1 + len(w) > per:
            cv.text(line, x, y, size, color)
            y += size + gap
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        cv.text(line, x, y, size, color)
        y += size + gap
    return y


def section_poly(pts, cx, cy, sc):
    return [(cx + x * sc, cy - y * sc) for x, y in pts]


def classic_sections():
    """(name, polygon in unit half-width/half-thickness units, note)."""
    return [
        ("hira-zukuri: flat sides, no ridge", [(-1, 0), (-0.45, 0.9), (1.0, 0.9), (1.0, -0.9), (-0.45, -0.9)], "single edge, a plain wedge"),
        ("shinogi-zukuri: the katana", [(-1, 0), (-0.3, 0.95), (0.9, 0.9), (1.0, 0.75), (1.0, -0.75), (0.9, -0.9), (-0.3, -0.95)],
         "a ridge (shinogi) keeps a thin edge strong"),
        ("diamond / lenticular (ken, moroha)", [(-1, 0), (0, 1.0), (1, 0), (0, -1.0)], "double edge, a ridge down the middle"),
        ("hexagonal (medieval European)", [(-1, 0), (-0.45, 0.95), (0.45, 0.95), (1, 0), (0.45, -0.95), (-0.45, -0.95)], "two flats and a crisp ridge on each face"),
    ]


def draw_section(cv, sec, cx, cy, sc, colours=None, width=2.0):
    pts = [(x, y) for x, y, _ in sec]
    poly = section_poly(pts, cx, cy, sc)
    cv.polygon(poly, (0.16, 0.18, 0.23, 1.0))
    n = len(sec)
    plane_col = colours or {0: (0.95, 0.97, 1.0, 1), 1: STEEL, 2: GOLD, 3: (0.85, 0.9, 1.0, 1)}
    for i in range(n):
        j = (i + 1) % n
        p = sec[i][2] if sec[i][2] == sec[j][2] else max(sec[i][2], sec[j][2])
        cv.line(poly[i], poly[j], plane_col.get(p, STEEL), width)


def blade_sections(path):
    cv = BD.Canvas(2400, 1180, bg=BG)
    cv.text("The blade's cross-sections: what the classic sections teach, and the section this blade is built from", 24, 14, 24, INK)
    cv.text("Classic sections, one scale (schematic)", 24, 60, 17, GOLD)
    x = 190
    for name, pts, note in classic_sections():
        cv.polygon(section_poly(pts, x, 210, 120), (0.16, 0.18, 0.23, 1))
        cv.polyline(section_poly(pts, x, 210, 120), STEEL, 2.0, closed=True)
        wrap(cv, name, x - 170, 320, 340, 14, INK)
        wrap(cv, note, x - 170, 362, 340, 13, DIM)
        x += 560
    cv.text("This blade (true proportions, magnified: blade 0.47 studs wide at the collar, 0.16 thick)", 24, 460, 17, GOLD)
    stations = (("at the collar (s = 0)", 0.0, 1600.0), ("half way (s = 0.5)", 0.5, 1800.0), ("in the point, near the yokote (s = 0.86)", 0.86, 2000.0))
    cx = 380
    for label, s, sc in stations:
        sec = P.blade_section(s, True)
        draw_section(cv, sec, cx, 800, sc)
        cv.text(label, cx - 250, 960, 15, INK)
        a, h = P.blade_a(s), P.blade_h(s)
        cv.text("half-width %.3f   half-thickness %.3f" % (a, h), cx - 250, 985, 13, DIM)
        cx += 800
    key = [(STEEL, "main flat (hira): the layered grain shows here, satin"), ((0.95, 0.97, 1.0, 1), "ridge band: a narrow mirror, the pronounced ridge"),
           (GOLD, "twin grooves (soe-hi) beside the ridge, a gold line inlaid in each floor"), ((0.85, 0.9, 1.0, 1), "edge bevel: mirror-polished; the break before it is the shinogi")]
    y = 1040
    for col, t in key:
        cv.rect(30, y + 3, 26, 8, col)
        cv.text(t, 66, y, 14, INK)
        y += 28
    cv.text("In the point the shinogi swings in to meet the ridge: the yokote line, the sharp-cornered 'kissaki' of a Japanese blade", 1300, 1040, 14, DIM)
    return cv.save(path)


def taper_chart(cv, x0, y0, w, h):
    cv.rect(x0, y0, w, h, (0.1, 0.11, 0.14, 1))
    cv.text("Distal taper: half-width and half-thickness, collar to point", x0 + 10, y0 + 8, 15, GOLD)
    n = 80
    for series, col, scale in ((lambda s: P.blade_a(s), STEEL, 1.0), (lambda s: P.blade_h(s) * 3.0, AZURE, 1.0)):
        pts = [(x0 + 40 + (w - 70) * i / n, y0 + h - 40 - (h - 90) * series(i / n * 0.998) / 0.25) for i in range(n + 1)]
        cv.polyline(pts, col, 3.0)
    cv.text("half-width (0.235 to 0 at the point)", x0 + 330, y0 + 70, 13, STEEL)
    cv.text("half-thickness x3 (0.078 to 0.01)", x0 + 330, y0 + 92, 13, AZURE)
    yo = x0 + 40 + (w - 70) * 0.88
    cv.line((yo, y0 + 30), (yo, y0 + h - 30), GOLD, 1.5)
    cv.text("yokote", yo - 20, y0 + h - 28, 13, GOLD)


def research(path):
    cv = BD.Canvas(2400, 1040, bg=BG)
    cv.text("ORTHODOX FACTION SWORD: research board", 24, 14, 30, INK)
    cv.text("what real master-made swords teach, and what was taken as principle (nothing copied; no Chinese fittings, no lettering)", 24, 52, 16, DIM)
    col = [24, 820, 1616]
    # --- column 1: the Japanese blade and its polish
    y = 100
    cv.text("1  THE BLADE (Japanese nihonto)", col[0], y, 20, GOLD)
    y += 32
    for t in ("Shinogi-zukuri: a raised ridge line, the shinogi, separates the flat of the blade (hira, ji) from the edge section; it lets the edge stay thin and the blade stay stiff. Taken: a pronounced ridge and a visible break line before the edge bevel.",
              "Yokote: the line across the blade where the point (kissaki) begins. Taken: the point is its own form: the break line swings in to meet the ridge, a crisp arrowhead, not a rounded tip.",
              "Distal taper: width and thickness draw in from the collar to the point (the blade is thickest at the habaki). Taken: both tapers, plus a long convex run into a precise point.",
              "Hamon, the temper line, and the polish: hadori whitens the temper line; the fine haze beside it is nioi (the coarse form is nie); the layered steel grain (jihada: itame, masame, mokume) shows in the polished flats. Taken: a wavy white temper line over a visible layered grain, a mirror on the bevels.",
              "Double edge: the ken and moroha-zukuri are straight, double-edged, ridged down the middle. Taken: a symmetric diamond-ridge section."):
        y = wrap(cv, t, col[0], y, 740, 14, INK, 5) + 8
    y += 6
    cv.text("2  THE FITTINGS (Japanese koshirae)", col[0], y, 20, GOLD)
    y += 32
    for t in ("Habaki: the metal collar on the blade's foot. Tsuba: the guard plate, often pierced (sukashi: ji-sukashi, mon-sukashi, kage-sukashi). Seppa: thin spacer washers each side of the tsuba. Fuchi and kashira: collar and cap of the handle, made as a matched pair.",
              "Tsuka: a wooden core covered in ray-skin (same), wrapped in silk (tsuka-ito) in a diamond pattern (tsukamaki), menuki ornaments under the wrap.",
              "Taken: a tall gilt collar; a guard whose beauty is its pierced construction; a ray-skin grip under a diamond silk wrap; a matched fuchi and kashira in silver with gilt bands; nanako (fish-roe dots) on the gilt."):
        y = wrap(cv, t, col[0], y, 740, 14, INK, 5) + 8
    # --- column 2: Korean
    y = 100
    cv.text("3  KOREAN SWORDS AND THE NORIGAE", col[1], y, 20, GOLD)
    y += 32
    for t in ("Hwando: a Korean single-edged sword carried into the 19th century; its name comes from the ring (hwan) of its pommel. A Late Joseon ceremonial sabre is made of copper, brass, wood, ray-skin, lacquer, silk, gold and steel; its handle is wrapped in silk over ray-skin with a hole for a long tassel (Met, Atarn). Taken: a ring pommel the cord hangs from.",
              "Norigae: a Korean ornament in four parts: the ttidon (hook or loop it hangs from), the paemul (the main ornament: gold, silver, jade, stones), the maedeup (decorative knots) and the sul (silk tassels). A large main ornament gets small knots; a small one a large knot (V&A, Korea JoongAng Daily, Korea Times). Taken: a hitch on the ring, a braided cord, a maedeup knot, a jade pendant in a gold frame and a silk tassel.",
              "Ancient Korean gold-work (Silla and Gaya): gilt-bronze fittings, filigree and granulation, set stones; ring-pommel swords with openwork inside the ring (general knowledge, not read in this session). Taken as principle: gold worked in fine dots and thin wire, never in blobs.",
              "NOT taken: jian-style fittings, ruyi clouds, dragon pillars, taiji, Chinese knots, any lettering (and no Buddhist letters on the blade, the usual place for them)."):
        y = wrap(cv, t, col[1], y, 740, 14, INK, 5) + 8
    y += 6
    cv.text("4  WHAT THE STUDY DECIDED (see the silhouette sheets)", col[1], y, 20, GOLD)
    y += 32
    for t in ("A plate guard is a BAR from the side: five of eight plate candidates read as a European cross with a ring. Only a guard with height has a silhouette of its own: a faceted bell with its mouth to the hand and a pavilion's upswept eaves. Eight tall windows cut through its wall give the openwork; a gilt rib on every arris and a gilt border on every window give the finish; the blade's root, an unpolished tang, shows through them.",
              "The pommel is a ring, not the brief's lotus bud: Sword6 (the Immortal sword) already ends in a lotus bud and grows from a lotus."):
        y = wrap(cv, t, col[1], y, 740, 14, INK, 5) + 8
    # --- column 3: principles and sources
    y = 100
    cv.text("5  PRINCIPLES TAKEN", col[2], y, 20, GOLD)
    y += 32
    for t in ("Authority from proportion: a blade 4.0 studs long (tip at -5.75, 24% past Sword6's -4.65), 0.47 wide, drawn in to a needle. Nothing else on the blade competes with it.",
              "Every ornament is a construction, never an add-on: the ribs are the arrises, the windows are the bell's wall, the diamond wrap is the grip's binding, the cord is the ring's.",
              "Restraint in colour: white silver, gold, deep azure silk, pale jade. One accent hue.",
              "Gold only where a smith would put it (collar, ribs, window borders, brim, bands, ring, inlay in the grooves): never as the main metal."):
        y = wrap(cv, t, col[2], y, 740, 14, INK, 5) + 8
    y += 6
    cv.text("6  SOURCES (web search results; full-page fetches mostly timed out)", col[2], y, 20, GOLD)
    y += 32
    for t in ("Kyoto National Museum, sword guide (kyohaku.go.jp/eng/learn/assets/guides/2025-2_sword_guide_en.pdf): hira-ji, shinogi, hamon.",
              "Glossary of Japanese swords, Japanese sword polishing, Japanese sword mountings (Wikipedia): habaki, seppa, tsuba, same, menuki, kashira, hadori, nioi, nie.",
              "Hanbon Forge, 'Shinogi-Zukuri blade' (hanbonforge.com/blog/shinogi-zukuri-blade): the ridge, the yokote.",
              "Metropolitan Museum: Korean sword and scabbard records; daisho mountings (metmuseum.org/art/collection/search/24629, 638292). Atarn: Korean ceremonial sabre.",
              "V&A: samjak norigae (collections.vam.ac.uk/item/O22440, O34813). Korea JoongAng Daily: norigae. Korea Times: maedeup. Brooklyn Museum: samjak norigae.",
              "Not verified here: real kasane and nagasa figures (the search did not return them), so this blade's numbers are designed, not copied."):
        y = wrap(cv, t, col[2], y, 740, 13, DIM, 4) + 6
    # --- bottom: the taper chart and the silhouette of the chosen hilt
    taper_chart(cv, 24, 640, 760, 340)
    cv.text("7  THE DESIGN IN ONE LINE", col[1], 640, 20, GOLD)
    wrap(cv, "A long straight double-edged blade of layered steel, mirror-polished on the ridge and bevels, rising out of a hollow faceted gilt-and-silver bell with eight windows and swept-up eaves; a long white ray-skin grip under a deep azure silk diamond wrap; a silver kashira with a gilt hwan ring; a silk cord, a knot, a jade pendant and a tassel.", col[1], 680, 1500, 16, INK, 6)
    return cv.save(path)


def proportions(path):
    cv = BD.Canvas(1700, 760, bg=BG)
    cv.text("Proportions (studs, from the grip, the point toward -Z)", 24, 14, 24, INK)
    rows = [("tip", P.Z_TIP), ("yokote (the point begins)", P.Z_YOKOTE), ("blade shows from (Hilt)", P.Z_HILT), ("collar", "%.2f to %.2f" % (P.Z_COLLAR0, P.Z_COLLAR1)),
            ("bell: neck / rim / brim", "%.2f / %.2f / %.3f" % (P.Z_NECK, P.Z_RIM, P.Z_BRIM)), ("fuchi", "%.2f to %.2f" % (P.Z_FUCHI0, P.Z_FUCHI1)),
            ("grip (the hand closes on -0.5 to 0.5)", "%.2f to %.2f" % (P.Z_GRIP0, P.Z_GRIP1)), ("kashira", "%.2f to %.2f" % (P.Z_KASHIRA0, P.Z_KASHIRA1)),
            ("ring pommel: centre / radius", "%.2f / %.2f" % (P.Z_RING, P.RING_R)), ("knot / pendant / tassel", "%.2f / %.2f to %.2f / %.2f" % (P.Z_KNOT, P.Z_JADE0, P.Z_JADE1, P.Z_TASSEL0)),
            ("blade: half-width, half-thickness at the collar", "%.3f, %.3f" % (P.BLADE_A0, P.BLADE_H0)), ("bell: radius at the neck, rim, brim (corner)", "0.28, %.2f, 0.90" % P.flare_R(1.0)),
            ("overall, tip to tassel", "about %.2f" % (3.55 + abs(P.Z_TIP)))]
    y = 70
    for a, b in rows:
        cv.text(a, 40, y, 17, DIM)
        cv.text(str(b), 700, y, 17, INK)
        y += 36
    cv.text("Sword6: tip -4.65, blade from -1.00. Hand: R15 right hand 1.0 x 1.0 x 0.32, lower arm 1.0 x 1.0 x 1.08, turned 80 degrees (CombatFx.GRIP_TURN).", 40, y + 20, 15, DIM)
    return cv.save(path)


def run():
    os.makedirs(REVIEW, exist_ok=True)
    print(blade_sections(os.path.join(REVIEW, "blade_sections.png")))
    print(research(os.path.join(REVIEW, "research_board.png")))
    print(proportions(os.path.join(REVIEW, "proportions.png")))


if __name__ == "__main__":
    run()
