"""Economy re-simulation, 2026-11-24: how long the climb to the top rank (Eternal Origin, rank 60) takes now.

    python3 -I -B tools/economy/resim.py                 the full report (40 runs a scenario, about 30 s)
    python3 -I -B tools/economy/resim.py --runs 100      a tighter median
    python3 -I -B tools/economy/resim.py --quick         8 runs, to check the script

Writes tools/economy/output/resim_2026-11-24.md and .csv, and prints the same text.
The project vault's note "Economy Resimulation 2026-11-24" has the result and the verdict.

HOW IT RELATES TO THE EARLIER SIMULATOR. tools/balance/progression_sim.py (the 2026-11-16 one, behind "Balance Analysis
2026-11-16") already reads every number from the Luau files and mirrors QiService, QiReward, RewardService, SpinService, PetRules,
the egg stands, the guardians, the tribulations and the timed boost. It was checked again on 2026-11-24 against the code now:
the rank thresholds, the realm Qi multipliers, the pets and eggs, the Qi passes, the timed boost, the daily reward, the Spin Wheel,
the stand rule, the fusion and Codex numbers are IDENTICAL to what it ran on (compared with git: only the Cinder Roc's
AwakenTime and body radius, in the Guardians table, changed). So this script imports that simulator and does not copy its
formulas. It adds the things the code now has that it did not model, each one switchable (FEATURES, and the profile keys):

  titles   TitleRules.BONUSES: the worn realm title gives +1 .. +6 % Qi (Realm1 .. Realm12). PassRules.qiMultiplier multiplies it
           into every Qi source (meditation, egg bursts, offline, daily, spins, relics). One title is worn at a time. A player who
           leaves the title on "Auto" wears Developer / Content Creator / VIP / Beta Tester before any realm title (TitleRules.autoPick),
           so only a player who chooses the realm title gets the Qi (assumed: efficient players and payers do, casual players don't).
  bloom    WeatherConfig QiBloom: +10 % (added in the pets bracket, meditation only) while it lasts, in 6/102 of the weather spells.
           Taken as its expected value (+0.59 points); it is always tiny.
  gift     BetaGift: while GameConfig.Beta.Active is true every account may take ONE free Exclusive beast (Eclipse Dreadwing
           300 %, Crysalith 180 %, Nine-Tail Moonfox 120 %), Normal size, level 1, no mutation. Modelled as the Dreadwing (the best
           choice) in the pet list at the start. Gone when the beta is switched off, so every table is given without and with it.
  rivals   (section G only) other players going for the same full-paying egg stand: the stand serves one egg per EggTheft.RespawnTime
           to the whole server, so a player gets one in 1 + rivals. An upper bound, not a measurement of any real server.
  station  the Training Ground (+50 % while meditating on the Blossom Sanctuary's kerb) needs a trip from the Hatching Sanctum;
           progression_sim's default (--station none) assumes none. Here the trip is charged (progression_sim.STATIONS "sanctuary").

NOT modelled (other players apart from section G), because the code makes it no gate or no Qi (checked): the three faction trials (a member at the Immortal realm may
run one, 90-300 s, for a bound sword worth 1.1 x the Immortal sword; no Qi, no rank gate), combat forms (FormRules keeps every form's
damage per second within 2 % of the weapon's, so a theft takes the same time), quests (Spirit Stones only; they now wait for the
player to talk to Seren the Guide), the Hall of Records (a display), the Auction House (stones between players), the Wandering
Merchant, pens, weather other than the Bloom, day and night.

CALENDAR CONVENTION (the same as progression_sim): a player plays one session of H hours a day, starting the day with the offline Qi
for the time away (20 % of it, up to 8 h), the daily reward (stones, free timed-boost minutes), and 3 Spin Wheel spins. "Days" =
whole days before the finishing one + the share of the finishing day's session used. So 5.0 days at 4 h/day is about 26 h of play.
"""

import argparse
import copy
import csv
import math
import os
import random
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "balance"))
import progression_sim as ps  # noqa: E402

OUT = os.path.join(HERE, "output")
NAME = "resim_2026-11-24"

# which of the additions this script makes are switched on (the ablation turns them on one at a time)
FEATURES = {"title": True, "bloom": True}
BLOOM_EXPECTED_POINTS = 0.0   # filled by read_extras()
TITLE_QI = {}                 # realm number -> percent


def read_extras():
    """Title Qi percentages and the Qi Bloom's expected bonus, read from TitleRules.lua and WeatherConfig.lua."""
    global BLOOM_EXPECTED_POINTS
    with open(os.path.join(ROOT, "src/shared/TitleRules.lua"), encoding="utf-8") as handle:
        text = handle.read()
    for realm, pct in re.findall(r'Realm(\d+) = \{ "Qi", (\d+) \}', text):
        TITLE_QI[int(realm)] = int(pct)
    assert len(TITLE_QI) == 12, TITLE_QI
    with open(os.path.join(ROOT, "src/shared/WeatherConfig.lua"), encoding="utf-8") as handle:
        weather = handle.read()
    states = weather[weather.index("WeatherConfig.States"):]
    weights = {name: float(w) for name, w in re.findall(r"\n    (\w+) = \{[^\n]*?Weight = ([0-9.]+)", states)}
    weights.update({name: float(w) for name, w in re.findall(r"\n    (\w+) = \{\s*\n\s*Weight = ([0-9.]+)", states)})
    bloom_pct = float(re.search(r"QiBloom = \{\s*Weight = [0-9.]+, Repeat = false, QiBonusPercent = ([0-9.]+)", states).group(1))
    BLOOM_EXPECTED_POINTS = bloom_pct * weights["QiBloom"] / sum(weights.values())


class Player(ps.Player):
    """progression_sim's player, plus the title Qi bonus, the Qi Bloom and the beta gift."""

    def __init__(self, rules, profile, rng, calendar_hours=None):
        self._title_ok = profile.get("title", False)
        super().__init__(rules, profile, rng, calendar_hours)
        if profile.get("behaviour"):   # a variant of the style's assumptions (BEHAVIOUR entries added below)
            self.b = ps.BEHAVIOUR[profile["behaviour"]]
        if profile.get("gift"):
            self.add_pet("EclipseDreadwing", "Normal")   # BetaGiftService: grantPet, Normal size, level 1, no mutation
            self.refresh()

    def steal(self, plan, gid):
        """progression_sim's theft, but with `rivals` other players of the same realm after the same full-paying egg: its stand brings
        the egg back every RespawnTime (EggTheft) for everyone, so this player gets one egg in 1 + rivals (round robin: an upper
        bound on the wait, the real wait depends on who is near the island). A lesser, capped egg is nobody's first choice and is left alone."""
        rivals = self.p.get("rivals", 0)
        egg_id, slot = plan[1], plan[2]
        uncapped = self.R.ranks[self.R.egg_rank(egg_id)]["QiMultiplier"] >= self.R.best_egg_mult(self.idx)
        before = self.thefts
        super().steal(plan, gid)
        if rivals and uncapped and self.thefts > before:
            egg, ready_at = self.stands[gid][slot]
            self.stands[gid][slot] = (egg, ready_at + self.R.cfg["EggTheft"]["RespawnTime"] * rivals)

    @property
    def base_pass(self):
        """PassRules.qiMultiplier without the timed boost: tier x VIP x the worn title's Qi bonus."""
        title = 1.0
        if FEATURES["title"] and self._title_ok:
            title = 1 + TITLE_QI[self.R.realm_of[self.idx]] / 100
        return self._base * title

    @base_pass.setter
    def base_pass(self, value):
        self._base = value

    def meditate_rate(self, spring=True):  # QiService.awardCultivationQi
        bonus = self.pet_pct + self.codex_pct + (self.R.cfg["TrainingStation"]["QiBonusPercent"] if spring else 0)
        if FEATURES["bloom"]:
            bonus += BLOOM_EXPECTED_POINTS
        return math.floor(self.R.cfg["CultivationQiReward"] * self.realm_mult() * self.pass_mult * (100 + bonus) / 100)


ps.Player = Player  # progression_sim.run builds its players by this name

# Two extra play styles for the sensitivity block (assumptions, like every entry of progression_sim.BEHAVIOUR: nothing in the code says
# how well a player fights or how often a tribulation is failed).
ps.BEHAVIOUR["mid"] = dict(ps.BEHAVIOUR["efficient"], hit_share=0.6, chase=1.5, fail=0.10, overhead=25, relic_seconds=100,
                           tribulation_fail=(0.15, 0.04))                     # between efficient and casual, but always stealing
ps.BEHAVIOUR["hardtrib"] = dict(ps.BEHAVIOUR["efficient"], tribulation_fail=(0.30, 0.05))   # efficient, but fails tribulations 3-4x as often


# ------------------------------------------------------------------------------------------------ scenarios
# (key, label, hours a day, profile). Keys of a profile: style (BEHAVIOUR in progression_sim: efficient / casual), tier (Qi pass),
# vip, boost_minutes (timed boost bought a play day), title (wears the realm title), gift (takes the beta beast).
def scenarios(gift):
    g = {"gift": gift}
    return [
        ("free4", "Free, efficient, 4 h/day", 4, dict(style="efficient", title=True, **g)),
        ("free1e", "Free, efficient, 1 h/day (reference)", 1, dict(style="efficient", title=True, **g)),
        ("casual1", "Free, casual, 1 h/day", 1, dict(style="casual", **g)),
        ("casual4", "Free, casual, 4 h/day (reference)", 4, dict(style="casual", **g)),
        ("pass2", "2x pass + VIP, 4 h/day", 4, dict(style="efficient", title=True, tier=2, vip=True, **g)),
        ("payer0", "4x pass + VIP, 4 h/day", 4, dict(style="efficient", title=True, tier=4, vip=True, **g)),
        ("payer30", "4x + VIP + 30 min of boost a day, 4 h/day (the old note's payer)", 4,
         dict(style="efficient", title=True, tier=4, vip=True, boost_minutes=30, **g)),
        ("payer60", "4x + VIP + 1 h of boost a day, 4 h/day", 4,
         dict(style="efficient", title=True, tier=4, vip=True, boost_minutes=60, **g)),
        ("payer240", "4x + VIP + boost for all play time (4 h a day), 4 h/day", 4,
         dict(style="efficient", title=True, tier=4, vip=True, boost_minutes=240, **g)),
        ("payer1", "4x + VIP + 30 min of boost a day, 1 h/day", 1,
         dict(style="efficient", title=True, tier=4, vip=True, boost_minutes=30, **g)),
    ]


def run_calendar(rules, profile, seed, hours, limit_days=900):
    """progression_sim.run's calendar loop, also recording the day each realm is entered."""
    rng = random.Random(seed)
    player = Player(rules, profile, rng, hours)
    session = hours * 3600
    entered = {1: 0.0}
    day = 0
    start = 0.0

    def stamp():
        for realm in player.realm_entered:
            if realm not in entered:
                entered[realm] = day + min(1.0, max(0.0, (player.t - start) / session))

    while not player.done() and day < limit_days:
        player.session_start(0 if day == 0 else 86400 - session, day)
        start = player.t
        end = start + session
        while not player.done() and player.t < end:
            player.break_through()
            stamp()
            player.shop()
            if player.done():
                break
            player.act(end - player.t)
        if player.done():
            stamp()
            return player, day + (player.t - start) / session, entered
        day += 1
    return player, float("inf"), entered


def evaluate(rules, rows, runs, seed):
    out = {}
    realm_count = len(rules.realms)
    for key, label, hours, profile in rows:
        totals, plays, per_realm, bought = [], [], [], []
        for r in range(runs):
            player, days, entered = run_calendar(rules, profile, seed + r, hours)
            totals.append(days)
            plays.append(player.t / 3600)
            per_realm.append([entered.get(k, float("inf")) for k in range(2, realm_count + 1)])
            bought.append(player.boost_bought)
        med = statistics.median
        ordered = sorted(totals)
        out[key] = {
            "label": label, "hours": hours, "profile": profile,
            "days": med(totals), "p10": ordered[int(runs * 0.1)], "p90": ordered[min(runs - 1, int(runs * 0.9))],
            "play_h": med(plays),
            "reach": [med(x[i] for x in per_realm) for i in range(realm_count - 1)],   # day each realm 2..12 is entered
        }
    return out


def boost_cost(minutes_a_day):
    """Robux a day for that many minutes of timed boost, from the cheapest packs (GameConfig.TimedBoost.Products)."""
    if minutes_a_day <= 0:
        return 0
    best = None
    for hours in range(0, 6):
        for q in range(0, 6):
            for f in range(0, 13):
                if hours * 60 + q * 15 + f * 5 >= minutes_a_day:
                    cost = hours * PACKS[60] + q * PACKS[15] + f * PACKS[5]
                    best = cost if best is None else min(best, cost)
    return best


PACKS = {}


# ------------------------------------------------------------------------------------------------ report
def fmt(x):
    return "never" if x == float("inf") else ("%.1f" % x if x >= 10 else "%.2f" % x)


def days_table(rules, results, title):
    lines = ["### " + title, "",
             "Day on which each realm is entered (median), and the day the top rank (Eternal Origin) is reached. Play hours: all play, not counting time away.", "",
             "| Scenario | h/day | " + " | ".join("R%d" % k for k in range(2, len(rules.realms) + 1)) + " | **Top rank (days)** | p10-p90 | Play hours |",
             "|---|---|" + "---|" * (len(rules.realms) - 1) + "---|---|---|"]
    for res in results.values():
        lines.append("| %s | %d | %s | **%s** | %s-%s | %.1f |" % (
            res["label"], res["hours"], " | ".join(fmt(x) for x in res["reach"]), fmt(res["days"]),
            fmt(res["p10"]), fmt(res["p90"]), res["play_h"]))
    return lines


def play_hours(rules, rows, runs, seed):
    """Play hours spent in each realm, no offline Qi / daily reward / spins counted (the old note's "hours in each realm" table)."""
    out = {}
    for key, label, hours, profile in rows:
        per, totals = [], []
        for r in range(runs):
            player, _ = ps.run(rules, profile, seed + r)
            realms = sorted(player.realm_entered)
            entered = [player.realm_entered[k] for k in realms] + [player.t]
            per.append([(entered[i + 1] - entered[i]) / 3600 for i in range(len(realms))])
            totals.append(player.t / 3600)
        n = min(len(x) for x in per)
        out[key] = {"label": label, "realm_h": [statistics.median(x[i] for x in per) for i in range(n)],
                    "total": statistics.median(totals)}
    return out


def realm_table(rules, played, keys, title):
    names = [("%d %s" % (i + 1, r)) for i, r in enumerate(rules.realms)]
    lines = ["### " + title, "",
             "Play hours spent inside each realm (median; offline Qi, the daily reward and spins are NOT counted, so these are the realms' own weights).", "",
             "| Realm | " + " | ".join(played[k]["label"] for k in keys) + " |", "|---|" + "---|" * len(keys)]
    for i, name in enumerate(names):
        lines.append("| %s | %s |" % (name, " | ".join("%.2f" % played[k]["realm_h"][i] for k in keys)))
    lines.append("| **Total play hours** | %s |" % " | ".join("**%.1f**" % played[k]["total"] for k in keys))
    flags = []
    for k in keys:
        h = played[k]["realm_h"]
        late = statistics.median(h[3:])
        jump = max(range(1, len(h)), key=lambda i: h[i] / max(h[i - 1], 0.05))
        flags.append("longest R%d = %.1fx the median of R4-R12; biggest step up R%d (%.1fx the realm before)" % (
            h.index(max(h)) + 1, max(h) / late, jump + 1, h[jump] / max(h[jump - 1], 0.05)))
    lines.append("| *shape* | %s |" % " | ".join(flags))
    return lines


def structure(rules):
    lines = ["### What gates a realm (read from the code)", "",
             "| Realm | First rank | Qi to start it | Realm Qi multiplier | Qi to finish it | Free meditation, no pets or passes (Qi/s) |",
             "|---|---|---|---|---|---|"]
    for i, realm in enumerate(rules.realms):
        ranks = [r for r in rules.ranks if r["Realm"] == realm]
        start = ranks[0]["QiRequired"]
        last = ranks[-1] is rules.ranks[-1]
        nxt = None if last else rules.ranks[rules.ranks.index(ranks[-1]) + 1]["QiRequired"]
        lines.append("| %d %s | %s | %s | x%s | %s | %s |" % (
            i + 1, realm, ranks[0]["Name"], "{:,}".format(start), ranks[0]["QiMultiplier"],
            "(top rank at %s)" % "{:,}".format(ranks[-1]["QiRequired"]) if last else "{:,}".format(nxt - start),
            "{:,}".format(rules.cfg["CultivationQiReward"] * ranks[0]["QiMultiplier"])))
    return lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=40, help="Monte Carlo runs per scenario (default 40)")
    parser.add_argument("--seed", type=int, default=20261124)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    runs = 8 if args.quick else args.runs
    read_extras()

    game = ps.load_game()
    PACKS.update({p["Minutes"]: p["Price"] for p in game["cfg"]["TimedBoost"]["Products"]})
    pass_price = {p["Id"]: p["Price"] for p in game["cfg"]["GamePasses"]}
    ps.STATION = "sanctuary"
    rules = ps.Rules(copy.deepcopy(game))
    assert game["cfg"]["Beta"]["Active"] in (True, False)

    lines = ["# Economy re-simulation 2026-11-24 (%d runs a scenario, seed %d)" % (runs, args.seed), ""]
    lines += ["Game read from the Luau files as of today. Beta gift active in the game now: %s. Training Ground trip charged. Title Qi bonus and "
              "Qi Bloom on (FEATURES)." % game["cfg"]["Beta"]["Active"], ""]

    FEATURES.update(title=True, bloom=True)
    no_gift = evaluate(rules, scenarios(False), runs, args.seed)
    with_gift = evaluate(rules, scenarios(True), runs, args.seed)
    lines += days_table(rules, no_gift, "A. After the beta (no free Exclusive beast): the game as it will launch") + [""]
    lines += days_table(rules, with_gift, "B. During the beta (every account took a free Dreadwing): the game as it is today") + [""]
    keys = ["free4", "casual1", "pass2", "payer30"]
    for gift, tag in ((False, "after the beta"), (True, "during the beta")):
        rows = [r for r in scenarios(gift) if r[0] in keys]
        lines += realm_table(rules, play_hours(rules, rows, runs, args.seed), keys,
                             "%s. Where the play time goes, %s" % ("C" if not gift else "D", tag)) + [""]

    # spending
    lines += ["### E. What the payers spend (Robux, from the fallback prices in GameConfig; the Store shows the live ones)", "",
              "Passes: 2x %d, 4x %d, VIP %d. Boost packs: 5 min %d, 15 min %d, 60 min %d (the cheapest packs that cover the minutes). "
              "A boost is bought every play day for the days the climb takes." % (
                  pass_price["QiSurge"], pass_price["Qi4x"], pass_price["VIP"], PACKS[5], PACKS[15], PACKS[60]), "",
              "| Scenario (after the beta) | Days | Passes | Boosts | Total R$ |", "|---|---|---|---|---|"]
    for key in ("pass2", "payer0", "payer30", "payer60", "payer240", "payer1"):
        res = no_gift[key]
        pr = res["profile"]
        passes = (pass_price["QiSurge"] if pr.get("tier") == 2 else pass_price["Qi4x"] if pr.get("tier") == 4 else 0) + (pass_price["VIP"] if pr.get("vip") else 0)
        boosts = boost_cost(pr.get("boost_minutes", 0)) * math.ceil(res["days"])
        lines.append("| %s | %s | %d | %d | %d |" % (res["label"], fmt(res["days"]), passes, boosts, passes + boosts))
    lines.append("")

    # sensitivity
    lines += ["### F. How much the answer leans on the play assumptions (days to the top rank, median, after the beta)", "",
              "| Player | 4 h/day | 1 h/day |", "|---|---|---|"]
    sens = [("Efficient (the old note's free player: 75 % of strikes land, 1.3x the straight carry, 5 % of thefts lost, tribulation failure 8 % rising 2.5 points a realm)", "efficient", "efficient"),
            ("Mid (60 % land, 1.5x carry, 10 % lost, 25 s of menus, tribulation failure 15 % rising 4 points) but always stealing", "efficient", "mid"),
            ("Efficient but fails tribulations about 3-4x as often (30 % rising 5 points: 30-80 % per realm)", "efficient", "hardtrib"),
            ("Casual (50 % land, 1.8x carry, 15 % lost, 40 s of menus, steals 40 % of the time, tribulation failure 20 % rising 5)", "casual", "casual")]
    for label, style, behaviour in sens:
        cells = []
        for hours in (4, 1):
            prof = dict(style=style, behaviour=behaviour, title=(style != "casual"))
            res = evaluate(rules, [("x", label, hours, prof)], runs, args.seed)
            cells.append(fmt(res["x"]["days"]))
        lines.append("| %s | %s | %s |" % (label, cells[0], cells[1]))
    lines.append("")

    # contention for the full-paying stand
    lines += ["### G. Other players after the same egg (days to the top rank, median, after the beta)", "",
              "Only the best egg a player can take pays their realm in full; from the Divine Realm on that is ONE stand on Pangu's island, "
              "which brings its egg back every %d s (EggTheft.RespawnTime) for the whole server. `rivals` = other players of the same realm band "
              "going for the same stand; the player gets one egg in (1 + rivals) respawns. 0 is the solo case every other table uses." % rules.cfg["EggTheft"]["RespawnTime"], "",
              "| Player | rivals 0 | 1 | 2 | 4 | 8 |", "|---|---|---|---|---|---|"]
    for label, hours, prof in [("Free, efficient, 4 h/day", 4, dict(style="efficient", title=True)),
                               ("Free, casual, 1 h/day", 1, dict(style="casual")),
                               ("4x + VIP + 30 min boost, 4 h/day", 4, dict(style="efficient", title=True, tier=4, vip=True, boost_minutes=30))]:
        cells = []
        for rivals in (0, 1, 2, 4, 8):
            res = evaluate(rules, [("x", label, hours, dict(prof, rivals=rivals))], runs, args.seed)
            cells.append(fmt(res["x"]["days"]))
        lines.append("| %s | %s |" % (label, " | ".join(cells)))
    lines.append("")

    # ablation: each addition on its own, on the three headline scenarios
    lines += ["### H. What each addition changes (days to the top rank, median)", "",
              "Row 1 is progression_sim as the old note ran it, on today's files (no Training Ground trip, no titles, no Bloom, no gift). "
              "Each row adds one thing to the row above.", "",
              "| Model | Free efficient 4 h/day | Free casual 1 h/day | 4x + VIP + 30 min boost, 4 h/day |", "|---|---|---|---|"]
    heads = [("free4", "free4"), ("casual1", "casual1"), ("payer30", "payer30")]

    def row(label, station, title, bloom, gift):
        ps.STATION = station
        FEATURES.update(title=title, bloom=bloom)
        r = ps.Rules(copy.deepcopy(game))
        rows = [s for s in scenarios(gift) if s[0] in dict(heads)]
        res = evaluate(r, rows, runs, args.seed)
        lines.append("| %s | %s | %s | %s |" % (label, fmt(res["free4"]["days"]), fmt(res["casual1"]["days"]), fmt(res["payer30"]["days"])))
        return res

    row("1. old model on today's files", "none", False, False, False)
    row("2. + the Training Ground trip charged", "sanctuary", False, False, False)
    row("3. + worn realm title's Qi (efficient and payers)", "sanctuary", True, False, False)
    row("4. + Qi Bloom", "sanctuary", True, True, False)
    row("5. + free Dreadwing from the beta gift", "sanctuary", True, True, True)
    lines.append("")
    ps.STATION = "sanctuary"
    FEATURES.update(title=True, bloom=True)

    lines += structure(rules) + [""]
    text = "\n".join(lines) + "\n"
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, NAME + ".md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    with open(os.path.join(OUT, NAME + ".csv"), "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["beta_gift", "scenario", "hours_per_day", "days_top", "p10", "p90", "play_hours"] + ["day_enter_R%d" % k for k in range(2, len(rules.realms) + 1)])
        for gift, results in ((False, no_gift), (True, with_gift)):
            for key, res in results.items():
                writer.writerow([gift, res["label"], res["hours"], round(res["days"], 2), round(res["p10"], 2), round(res["p90"], 2),
                                 round(res["play_h"], 1)] + [round(x, 2) for x in res["reach"]])
    print(text)


if __name__ == "__main__":
    main()
