"""How long the climb to the top rank (Eternal Origin) takes, for free and paying players.

    python3 -I tools/balance/progression_sim.py              the game as it is
    python3 -I tools/balance/progression_sim.py --proposal   with the tuning proposed in PROPOSAL below
    python3 -I tools/balance/progression_sim.py --both       both, and the before/after table
    python3 -I -B tools/balance/progression_sim.py --root <folder> --name before   an older version's files (src/... under it)
    python3 -I -B tools/balance/progression_sim.py --compare before current        compare.md from two runs
    python3 -I -B tools/balance/progression_sim.py --proposal --stands code   a variant of PROPOSAL (try other numbers)
    options: --runs N (Monte Carlo runs per profile, default 30), --seed S, --mults 2,5,12,... (realms 4-12, to try others)

Writes tools/balance/output/<current|proposal|proposal_config_only>.md and .csv (and compare.md with --both).
The results in the vault note "Balance Analysis 2026-11-16": the game before the 2026-11-16 balance (git ed75c91's GameConfig,
PetRules, Bridges and EggStands, run with --root) against the game now (current), 30 runs each.

Every game number is read from the Luau files (luau_table.py parses them; nothing is copied by hand):
  src/shared/GameConfig.lua   ranks, realm multipliers, pets, eggs, passes, guardians, weapons, combat, Qinggong, stones,
                              relics, quests, daily rewards, offline Qi, Spin Wheel, Codex, fusion, Tribulation, Qi Spring
  src/shared/PetRules.lua     hatch sizes (Qi and value per size)
  src/worldbuild/Placements/Bridges.lua   bridge paths (how far an egg is carried) and the rank each bridge opens at
The formulas mirror the code, with the source named at each one:
  meditation   QiService.awardCultivationQi: floor(10 * realmMult * passMult * (100 + pets% + codex% + spring%) / 100) per second
  egg burst    QiReward.grantEggBurst / grantAtRate: 300 s at the cultivating rate, no Qi Spring, realm multiplier capped
               at the egg's realm unless it is the best egg the player can take
  offline      RewardService.grantOffline: 0.2 of the time away (at most 8 h) at grantAtRate
  relic        DiscoveryService: QiReward * passMult (no realm multiplier, no pets)
  passMult     PassRules.qiMultiplier: the highest Qi Boost tier owned (never stacked) * VIP 1.1
  pets         PetInventory.getQiBonusPercent: sum over equipped pets of PetRules.qiBonus (base * (1 + 0.1 (level-1)) * size Qi)
               + Codex milestones' QiPercent; 3 slots, 6 with the +3 Pet Slots pass
  ranks        RankService: Qi is never spent; a new realm needs its Heavenly Tribulation survived

What is NOT in the code, and so is an assumption (BEHAVIOUR and the theft-cycle timings below): how well a player fights,
how often a carried egg is knocked away, how long walking to the altar takes, how often a tribulation is failed, and how
a casual player splits their time. They are the levers of uncertainty; the report states them.
"""

import argparse
import copy
import csv
import math
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from luau_table import read_table  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


# ------------------------------------------------------------------------------------------------ reading the game
def load_game():
    def read(path, marker):
        with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
            return read_table(handle.read(), marker)

    game = {
        "cfg": read("src/shared/GameConfig.lua", "local GameConfig ="),
        "sizes": read("src/shared/PetRules.lua", "PetRules.Sizes ="),
        "bridges": read("src/worldbuild/Placements/Bridges.lua", "return")["Bridges"],
    }
    # the egg stands' respawn rule (EggStands.respawn): "own" since 2026-11-16 (a stand brings back its own egg), before it the
    # lowest-or-random rule
    stands_path = os.path.join(ROOT, "src/server/Guardians/EggStands.lua")
    if os.path.exists(stands_path):
        with open(stands_path, encoding="utf-8") as handle:
            if "slot.home" in handle.read():
                game["cfg"]["__stand_rule"] = "own"
    return game


def vec(value):
    """A parsed Vector3.new(x, y, z) as (x, z)."""
    assert value[0] == "call" and value[1] == "Vector3.new", value
    return value[2][0], value[2][2]


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def round_nice(n):  # Shop.roundNice
    if n < 100:
        return max(1, math.floor(n + 0.5))
    unit = 10 ** (math.floor(math.log10(n)) - 1)
    return math.floor(n / unit + 0.5) * unit


class Rules:
    """The game's rules, derived from the parsed config the way the Luau modules derive them."""

    def __init__(self, game):
        cfg = self.cfg = game["cfg"]
        self.sizes = game["sizes"]
        self.size_order = sorted(self.sizes, key=lambda name: self.sizes[name]["Order"])
        self.ranks = cfg["Ranks"]
        self.rank_index = {rank["Id"]: i for i, rank in enumerate(self.ranks)}  # 0-based here
        self.realms = []
        for rank in self.ranks:
            if rank["Realm"] not in self.realms:
                self.realms.append(rank["Realm"])
        self.realm_of = [self.realms.index(rank["Realm"]) + 1 for rank in self.ranks]  # 1-based realm number per rank
        self.ranks_per_realm = len(self.ranks) / len(self.realms)
        self.pets = cfg["Pets"]
        self.eggs = cfg["Eggs"]
        self.passes = {p["Id"]: p for p in cfg["GamePasses"]}
        self.weapons = cfg["WeaponTiers"]
        stones = self.stones_cfg = cfg["SpiritStones"]

        # Shop.petRealm: the earliest realm of an egg holding the pet (Exclusive egg included, as Shop does)
        self.pet_realm = {}
        for egg in self.eggs.values():
            realm = self.realm_of[self.rank_index[egg["RequiredRank"]]]
            for entry in egg["Pool"]:
                self.pet_realm[entry["PetId"]] = min(self.pet_realm.get(entry["PetId"], realm), realm)
        # the Codex counts every beast an egg holds (CodexRules)
        self.codex_total = len(self.pet_realm)
        self.codex = cfg["Codex"]["Milestones"]

        # guardians: where they stand (their quest's Way), their island's bridge (nearest bridge end), unlock rank
        ways = {}
        for quest in cfg["Quests"]:
            way = quest.get("Way")
            if way and isinstance(way, list) and isinstance(way[0], str):
                ways.setdefault(way[0], (way[1], way[2]))
        self.altar = (cfg["HatchingAltar"]["Centre"][2][0], cfg["HatchingAltar"]["Centre"][2][2])
        self.guardians = {}
        for gid, g in cfg["Guardians"].items():
            spot = None
            for label, xy in ways.items():
                name = label[4:] if label.startswith("the ") else label
                if name in g["DisplayName"] or g.get("Called") == name:
                    spot = xy
            assert spot, "no quest Way for guardian " + gid
            best = None
            for bid, bridge in self.bridges_of(game):
                nodes = [vec(n["Position"]) for n in bridge["Nodes"]]
                far = min(dist(nodes[0], spot), dist(nodes[-1], spot))
                if best is None or far < best[0]:
                    length = sum(dist(nodes[i], nodes[i + 1]) for i in range(len(nodes) - 1))
                    hub_end = nodes[0] if dist(nodes[0], self.altar) < dist(nodes[-1], self.altar) else nodes[-1]
                    best = (far, length, hub_end, bridge["RankId"], bid)
            far, length, hub_end, unlock, bid = best
            self.guardians[gid] = {
                "id": gid, "hp": g["MaxHealth"], "eggs": g["Eggs"], "element": g.get("Element"),
                "awaken": g.get("AwakenTime", 1.6),
                "unlock": self.rank_index[unlock], "bridge": bid,
                # the egg goes home on foot: island leg + bridge; the hub is the safe zone (secured on setting foot on it)
                "carry": far + length,
                "out": dist(self.altar, spot),            # straight line (sword flight) from the altar
                "hub_walk": dist(self.altar, hub_end),    # from the bridge's hub end back to the Hatching Sanctum
                "run_out": dist(self.altar, hub_end) + length + far,
            }
        self.qinggong = cfg["Qinggong"]["Levels"]
        self.flight_rank = self.rank_index[cfg["SwordFlight"]["UnlockRank"]]
        self.relics = [dict(r, idx=self.rank_index[r["RequiredRank"]]) for r in cfg["Relics"]]

    @staticmethod
    def bridges_of(game):
        return game["bridges"].items()

    # Shop.rankValue (rank index 0-based)
    def rank_value(self, idx):
        return self.weapons[0]["Price"] * self.stones_cfg["RealmFactor"] ** (idx / self.ranks_per_realm)

    def egg_rank(self, egg_id):
        return self.rank_index[self.eggs[egg_id]["RequiredRank"]]

    def market_price(self, egg_id):  # Shop.marketEggPrice
        return round_nice(self.rank_value(self.egg_rank(egg_id)) * self.stones_cfg["MarketEggShare"])

    def egg_stones(self, egg_id):  # Shop.eggStones
        idx = self.egg_rank(egg_id)
        share = self.stones_cfg["EggShare"] * self.stones_cfg["EggShareFalloff"] ** (self.realm_of[idx] - 1)
        return round_nice(max(self.stones_cfg["MinReward"], self.rank_value(idx) * share))

    def relic_stones(self, relic):  # Shop.relicStones
        return round_nice(max(self.stones_cfg["MinReward"], self.rank_value(relic["idx"]) * self.stones_cfg["RelicShare"]))

    def pet_value(self, pet_id, worth):  # Shop.petValue
        pet = self.pets[pet_id]
        realm = pet.get("ValueRealm") or self.pet_realm.get(pet_id, 1)
        base = math.floor(self.stones_cfg["PetValue"][pet["Rarity"]] * self.stones_cfg["RealmFactor"] ** (realm - 1))
        return math.floor(base * worth + 1e-6)

    def qi_bonus(self, pet_id, level, size):  # PetRules.qiBonus
        fusion = self.cfg["PetFusion"]
        return round(self.pets[pet_id]["QiBonus"] * (1 + fusion["QiPerLevel"] * (level - 1)) * self.sizes[size]["Qi"])

    RARITY = {"Common": 1, "Uncommon": 2, "Rare": 3, "Epic": 4, "Legendary": 5, "Mythical": 6, "Secret": 7, "Divine": 8}

    def lucky_pool(self, pool, luck):  # PassRules.luckyPool
        out = [(e["PetId"], e["HatchChance"]) for e in pool]
        if luck <= 1:
            return out
        rank = lambda pid: self.RARITY[self.pets[pid]["Rarity"]]
        lowest = min(rank(pid) for pid, _ in out)
        threshold = max(lowest + 1, self.RARITY["Rare"])
        rare = sum(c for pid, c in out if rank(pid) >= threshold)
        common = sum(c for pid, c in out if rank(pid) < threshold)
        if rare <= 0 or common <= 0:
            return out
        boost = max(1, min(luck, (100 - self.cfg["LuckFloor"]) / rare))
        scale = (100 - rare * boost) / common
        return [(pid, c * (boost if rank(pid) >= threshold else scale)) for pid, c in out]

    def qinggong_at(self, idx):  # Ranks.getQinggong
        current = self.qinggong[0]
        for level in self.qinggong:
            if self.rank_index[level["RankId"]] <= idx:
                current = level
        return current

    def best_egg_mult(self, idx):  # QiReward.bestEggMultiplier
        best = 1
        for g in self.cfg["Guardians"].values():
            for egg_id in g["Eggs"]:
                e_idx = self.egg_rank(egg_id)
                if e_idx <= idx:
                    best = max(best, self.ranks[e_idx]["QiMultiplier"])
        return best

    def market_eggs_for(self, idx):  # the best Marketplace egg this rank can take (SpinRules.bestEgg; Exclusive excluded)
        options = [(self.egg_rank(e), e) for e, egg in self.eggs.items() if not egg.get("Exclusive") and self.egg_rank(e) <= idx]
        return max(options)[1]


# ------------------------------------------------------------------------------------------------ assumptions
# Profiles. luck/slots/vip/tier are the passes (GameConfig.GamePasses); exclusive = Exclusive Eggs bought at the start.
PROFILES = [
    {"key": "free_casual", "label": "Free, casual", "style": "casual"},
    {"key": "free_efficient", "label": "Free, efficient (with the free boosts)", "style": "efficient"},
    {"key": "free_fast", "label": "Free, fast (sensitivity: a strong player)", "style": "fast"},
    {"key": "pass2", "label": "2x pass only", "style": "efficient", "tier": 2},
    {"key": "pass4", "label": "4x pass only", "style": "efficient", "tier": 4},
    {"key": "pass4_vip", "label": "4x + VIP", "style": "efficient", "tier": 4, "vip": True},
    # the paying player (the owner's target): 4x pass + VIP + 30 minutes of timed boost a play day (one 15-minute pack twice,
    # or half the 60-minute pack)
    {"key": "payer", "label": "PAYING PLAYER: 4x + VIP + 30 min of timed boost a day", "style": "efficient", "tier": 4,
     "vip": True, "boost_minutes": 30},
    {"key": "payer_heavy", "label": "4x + VIP + 4 h of timed boost a day (all play time)", "style": "efficient", "tier": 4,
     "vip": True, "boost_minutes": 240},
    {"key": "pass2_vip_light", "label": "2x + VIP + 15 min of timed boost a day", "style": "efficient", "tier": 2, "vip": True,
     "boost_minutes": 15},
    {"key": "whale", "label": "All passes (4x, VIP, Luck, +3 slots) + 4 h boost + 5 Exclusive Eggs", "style": "efficient",
     "tier": 4, "vip": True, "luck": True, "slots": True, "boost_minutes": 240, "exclusive": 5},
    {"key": "owns16", "label": "Owner of the retired 16x pass (counts as the cap)", "style": "efficient", "tier": 16},
    {"key": "free_idle", "label": "Free, idle in the Qi Spring only", "style": "idle"},
]

# How each style plays (not in the code: estimates, see the module docstring).
BEHAVIOUR = {
    "efficient": {
        "hit_share": 0.75,       # share of the sword's cooldown-limited strikes that land (dodging the guardian's attacks)
        "chase": 1.3,            # carrying home takes this many times the straight run (dashes help; knock-backs hurt)
        "fail": 0.05,            # share of thefts where the egg goes back to its stand (knocked away and not recovered)
        "overhead": 15,          # seconds a theft: menus, equipping, the hatch prompt
        "tribulation_fail": (0.08, 0.025),   # first new realm's failure chance, and its rise per realm
        "fuse": True, "forge": True, "market": "eager", "theft_share": None,
        "relic_seconds": 60,
    },
    "fast": {  # a sensitivity check: every strike lands, no knock-backs, no menus, few failures
        "hit_share": 1.0, "chase": 1.0, "fail": 0.02, "overhead": 5, "tribulation_fail": (0.03, 0.01),
        "fuse": True, "forge": True, "market": "eager", "theft_share": None, "relic_seconds": 45,
    },
    "casual": {
        "hit_share": 0.5, "chase": 1.8, "fail": 0.15, "overhead": 40,
        "tribulation_fail": (0.2, 0.05),
        "fuse": False, "forge": False, "market": "lazy",
        "theft_share": 0.4,      # of play time spent on thefts; the rest meditating
        "spring_share": 0.7,     # of meditation time spent in the Qi Spring
        "relic_seconds": 150,
    },
    "idle": {
        "hit_share": 0, "chase": 0, "fail": 0, "overhead": 0, "tribulation_fail": (0.08, 0.025),
        "fuse": False, "forge": False, "market": "lazy", "theft_share": 0.0, "spring_share": 1.0, "relic_seconds": None,
    },
}
SESSION_OVERHEAD = 120   # seconds per play session: joining, loading, walking out
PLAY_DAY_HOURS = 4       # in the play-hours runs, a day's boosts (bought and daily-reward ones) come every this many hours of play
DAILY_HOURS = (2, 4, 8)


# ------------------------------------------------------------------------------------------------ the proposal
# Each entry changes the parsed config before the run. See the vault note "Balance Analysis 2026-11-16" for why.
PROPOSAL = {
    # 1. GameConfig.Ranks QiMultiplier per realm (realm number: multiplier). Now 1, 1, 1, 2, 4, 8 ... 512 (doubling from Spirit
    #    Soul); proposed: Spirit Soul stays x2, then about 2.3x a realm, rounded to numbers a player reads easily
    "multipliers": {1: 1, 2: 1, 3: 1, 4: 2, 5: 5, 6: 12, 7: 30, 8: 70, 9: 160, 10: 400, 11: 900, 12: 2000},
    # 2. EggStands.respawn: a stand brings back its own egg (the one it was built with) instead of the lowest-or-random rule,
    #    so eggs the player can't take yet never fill an island's stands ("code" keeps the game's rule)
    "stand_rule": "own",
    # 3. the owner's set (2026-11-16): permanent Qi passes capped at 4x, and a timed 2x boost bought in packs
    "max_tier": 4,
    "timed_boost": {"Multiplier": 2, "MaxMinutes": 24 * 60},
    # 4. free timed boost minutes on the daily reward's seven days
    "daily_boost_minutes": [5, 5, 10, 10, 15, 15, 30],
}


def apply_proposal(cfg, proposal=None):
    proposal = proposal or PROPOSAL
    multipliers = proposal["multipliers"]
    seen = []
    for rank in cfg["Ranks"]:
        if rank["Realm"] not in seen:
            seen.append(rank["Realm"])
        rank["QiMultiplier"] = multipliers[len(seen)]
    cfg["__stand_rule"] = None if proposal.get("stand_rule") == "code" else proposal.get("stand_rule")
    if proposal.get("max_tier"):
        cfg["MaxQiTier"] = proposal["max_tier"]
    if proposal.get("timed_boost"):
        cfg["TimedBoost"] = dict(proposal["timed_boost"])
    for day, minutes in enumerate(proposal.get("daily_boost_minutes") or []):
        if minutes:
            cfg["Rewards"]["Daily"][day]["BoostMinutes"] = minutes
    return cfg


# ------------------------------------------------------------------------------------------------ the player
class Player:
    @property
    def t(self):
        return self._t

    @t.setter
    def t(self, value):
        spent = value - getattr(self, "_t", 0.0)
        self._t = value
        if spent > 0 and getattr(self, "boost_left", 0) > 0:
            self.boost_used += min(spent, self.boost_left)
            self.boost_left = max(0.0, self.boost_left - spent)

    @property
    def pass_mult(self):
        """PassRules.qiMultiplier: the Qi pass tier (capped at MaxQiTier) x VIP x the timed boost while it runs."""
        return self.base_pass * (self.boost_mult if self.boost_left > 0 else 1)

    def add_boost(self, minutes):
        cap = self.R.cfg.get("TimedBoost", {}).get("MaxMinutes", 24 * 60) * 60
        self.boost_left = min(cap, self.boost_left + minutes * 60)

    def __init__(self, rules, profile, rng, calendar_hours=None):
        self.R = rules
        self.p = profile
        self.b = BEHAVIOUR[profile["style"]]
        self.rng = rng
        self.calendar_hours = calendar_hours
        cfg = rules.cfg
        self.qi = cfg["StartingQi"]
        self.idx = 0
        self.stones = 0
        self.t = 0.0             # play seconds
        self.pets = []           # dicts: id, level, size, worth
        self.codex = set()
        self.claimed = set()
        self.codex_pct = 0
        self.weapons = set()     # sword tiers owned: new players start with the Qi Palm (no starter weapon since 2026-11-16)
        self.forged = set()
        self.elements = set()
        self.relics_done = set()
        self.secured_guardians = set()
        self.quests_paid = set()
        self.realm_entered = {1: 0.0}
        self.rank_reached = {0: 0.0}
        # each island's three stands, built with one of each of its eggs (WorldBuilder.buildEggStands): (egg, ready at)
        self.stands = {gid: [(egg, 0.0) for egg in g["eggs"]] for gid, g in rules.guardians.items()}
        self.slots = cfg["MaxEquippedPets"] + (self.R.passes["PetSlots"]["ExtraSlots"] if profile.get("slots") else 0)
        self.luck = self.R.passes["Luck"]["Luck"] if profile.get("luck") else 1
        tier = min(profile.get("tier", 1), cfg.get("MaxQiTier", 16))  # PassRules.qiTier: a tier above the cap counts as the cap
        self.base_pass = tier * (self.R.passes["VIP"]["QiMultiplier"] if profile.get("vip") else 1)
        boost = cfg.get("TimedBoost")
        self.boost_mult = boost["Multiplier"] if boost else 1  # (none in a game without timed boosts)
        self.boost_left = 0.0
        self.boost_used = 0.0
        self.boost_bought = 0
        self.daily_stones_mult = self.R.passes["VIP"]["DailyStones"] if profile.get("vip") else 1
        self.thefts = 0
        self.hatches = 0
        self.theft_seconds = 0.0
        for pet_id in cfg["StarterPetIds"]:
            self.add_pet(pet_id, "Normal")
        for _ in range(profile.get("exclusive", 0)):
            self.hatch("ExclusiveEgg", luck_applies=False)
        # quest stones (GameConfig.Quests): Rank and Secure ones when reached (break_through, steal), Visit ones when the
        # island opens (its guardian's unlock rank), the rest in the first minutes
        island_unlock = {g["Island"]: rules.guardians[gid]["unlock"] for gid, g in cfg["Guardians"].items()}
        self.visit_quests = []
        for quest in cfg["Quests"]:
            if quest["Kind"] == "Visit":
                self.visit_quests.append((island_unlock[quest["Goal"]], quest["Reward"]))
            elif quest["Kind"] not in ("Rank", "Secure"):
                self.stones += quest["Reward"]
        self.refresh()

    # -- pets
    def add_pet(self, pet_id, size):
        self.pets.append({"id": pet_id, "level": 1, "size": size, "worth": self.R.sizes[size]["Value"]})
        self.codex.add(pet_id)

    def roll_size(self):
        roll = self.rng.random() * 100
        for name in self.R.size_order:
            roll -= self.R.sizes[name]["Chance"]
            if roll < 0:
                return name
        return "Normal"

    def hatch(self, egg_id, luck_applies=True):
        pool = self.R.lucky_pool(self.R.eggs[egg_id]["Pool"], self.luck if luck_applies else 1)
        roll = self.rng.random() * sum(c for _, c in pool)
        pet_id = pool[-1][0]
        for pid, chance in pool:
            roll -= chance
            if roll < 0:
                pet_id = pid
                break
        self.add_pet(pet_id, self.roll_size())
        self.hatches += 1

    def bonus_of(self, pet):
        return self.R.qi_bonus(pet["id"], pet["level"], pet["size"])

    def refresh(self):
        """Fuse, equip the best, sell spares, claim Codex milestones."""
        R = self.R
        if self.b["fuse"]:
            by_kind = {}
            for pet in self.pets:
                by_kind.setdefault(pet["id"], []).append(pet)
            for copies in by_kind.values():
                if len(copies) < 2:
                    continue
                copies.sort(key=lambda p: (-R.sizes[p["size"]]["Order"], -p["level"]))
                target = copies[0]
                for material in sorted(copies[1:], key=lambda p: (p["level"], R.sizes[p["size"]]["Order"])):
                    if target["level"] + material["level"] <= R.cfg["PetFusion"]["MaxLevel"]:
                        target["level"] += material["level"]
                        target["worth"] += material["worth"]
                        if R.sizes[material["size"]]["Order"] > R.sizes[target["size"]]["Order"]:
                            target["size"] = material["size"]
                        self.pets.remove(material)
        self.pets.sort(key=self.bonus_of, reverse=True)
        self.pet_pct = sum(self.bonus_of(p) for p in self.pets[: self.slots])
        keep = self.slots + 3 if self.b["fuse"] else None
        if keep is not None and len(self.pets) > keep:
            for pet in self.pets[keep:]:
                self.stones += R.pet_value(pet["id"], pet["worth"])
            del self.pets[keep:]
        elif len(self.pets) > R.cfg["MaxOwnedPets"] - 5:
            for pet in self.pets[35:]:
                self.stones += R.pet_value(pet["id"], pet["worth"])
            del self.pets[35:]
        found = len(self.codex)
        for i, milestone in enumerate(R.codex):
            need = milestone.get("Count", R.codex_total)
            if i not in self.claimed and found >= need:
                self.claimed.add(i)
                self.codex_pct += milestone["QiPercent"]
                self.stones += math.floor(milestone["WeaponShare"] * R.weapons[R.realm_of[self.idx] - 1]["Price"])

    # -- Qi rates
    def realm_mult(self):
        return self.R.ranks[self.idx]["QiMultiplier"]

    def meditate_rate(self, spring=True):  # QiService.awardCultivationQi, per second
        bonus = self.pet_pct + self.codex_pct + (self.R.cfg["TrainingStation"]["QiBonusPercent"] if spring else 0)
        return math.floor(self.R.cfg["CultivationQiReward"] * self.realm_mult() * self.pass_mult * (100 + bonus) / 100)

    def at_rate(self, seconds, cap=None, no_boost=False):  # QiReward.grantAtRate (offline Qi leaves the timed boost out)
        mult = min(self.realm_mult(), cap if cap is not None else math.inf) * (self.base_pass if no_boost else self.pass_mult)
        per_second = self.R.cfg["CultivationQiReward"] / self.R.cfg["CultivationInterval"] * mult * (100 + self.pet_pct + self.codex_pct) / 100
        return math.floor(per_second * seconds)

    def burst(self, egg_id):  # QiReward.grantEggBurst
        e_idx = self.R.egg_rank(egg_id)
        cap = self.R.ranks[e_idx]["QiMultiplier"]
        if cap >= self.R.best_egg_mult(self.idx):
            cap = None
        return self.at_rate(self.R.cfg["EggTheft"]["SecureQiMinutes"] * 60, cap)

    # -- a theft
    def strike(self):
        if self.weapons:
            tier = max(self.weapons)
            damage = self.R.weapons[tier - 1]["Damage"] * (1 + self.R.cfg["Forge"]["DamageBonus"] if tier in self.forged else 1)
            cooldown = self.R.cfg["WeaponKinds"]["Sword"]["Cooldown"]
        else:  # the Qi Palm (Combat.Palm)
            damage = self.R.cfg["Combat"]["Palm"]["Damage"]
            cooldown = self.R.cfg["Combat"]["Palm"]["Cooldown"]
        power = 1 + self.idx * self.R.cfg["Combat"]["RankPowerStep"]  # Combat.powerOf
        crit = self.R.cfg["Combat"]["Crit"]
        damage *= power * (1 + crit["Chance"] * (crit["Multiplier"] - 1))
        return damage / cooldown * self.b["hit_share"]

    def cycle_seconds(self, gid):
        """A theft's play seconds at this guardian, the stands' waiting aside (assumptions: BEHAVIOUR)."""
        g = self.R.guardians[gid]
        q = self.R.qinggong_at(self.idx)
        run = q["RunSpeed"]
        fly = q["FlightSpeed"] if self.idx >= self.R.flight_rank else 0
        out = g["out"] / fly if fly else g["run_out"] * 1.1 / run          # sword flight there, else run the bridge
        fight = 0.9 * g["hp"] / self.strike() + g["awaken"]                 # weaken it below WeakenedAt (0.1)
        carry = g["carry"] / (run * 1.1) * self.b["chase"]                  # on foot (FlightService: no flight with an egg)
        home = g["hub_walk"] / run + self.R.cfg["HatchingAltar"]["Stage"]   # to the Hatching Sanctum, and the hatch
        return out, out + fight + 3 + carry + home + self.b["overhead"]

    def potential(self, gid):
        """Qi per second of thefts here if its best takeable egg were on a stand: what a player chooses an island by."""
        g = self.R.guardians[gid]
        if self.idx < g["unlock"]:
            return 0
        takeable = [e for e in g["eggs"] if self.R.egg_rank(e) <= self.idx]
        if not takeable:
            return 0
        return max(self.burst(e) for e in takeable) / self.cycle_seconds(gid)[1]

    def theft_plan(self, gid):
        """(seconds, egg_id, stand, qi) for the best-paying takeable egg on this guardian's stands (waiting for a stand that
        is respawning if none is up), or None."""
        g = self.R.guardians[gid]
        if self.idx < g["unlock"]:
            return None
        out, cycle = self.cycle_seconds(gid)
        takeable = [e for e in g["eggs"] if self.R.egg_rank(e) <= self.idx]
        top = max(self.burst(e) for e in takeable)
        best = None
        for slot, (egg_id, ready_at) in enumerate(self.stands[gid]):
            if self.R.egg_rank(egg_id) > self.idx:
                continue
            value = self.burst(egg_id)
            # taking a lesser egg also re-rolls its stand: worth half the chance that the best egg comes back on it
            reroll = 0.0
            if value < top:
                chance = self.respawn_chances(gid, slot)
                reroll = 0.5 * top * sum(c for e, c in chance.items() if self.burst(e) == top)
            wait = max(0.0, ready_at - (self.t + out))
            key = ((value + reroll) / (cycle + wait), -wait)
            if best is None or key > best[0]:
                best = (key, egg_id, wait, slot, value, value + reroll)
        if not best:
            return None
        # (seconds, egg, stand, Qi it pays, what it is worth to the player with the re-roll)
        return cycle + best[2], best[1], best[3], best[4], best[5]

    def respawn_chances(self, gid, slot):
        eggs = self.R.guardians[gid]["eggs"]
        if self.R.cfg.get("__stand_rule") == "own":
            return {eggs[slot]: 1.0}
        lowest_shown = any(other == eggs[0] for i, (other, _) in enumerate(self.stands[gid]) if i != slot)
        if not lowest_shown:
            return {eggs[0]: 1.0}
        return {e: 1 / len(eggs) for e in eggs}

    def respawn_egg(self, gid, slot):  # EggStands.respawn: the lowest egg unless another stand shows it, else a random one
        eggs = self.R.guardians[gid]["eggs"]
        if self.R.cfg.get("__stand_rule") == "own":
            return eggs[slot]  # the proposed fix: each stand brings back its own egg
        lowest_shown = any(other == eggs[0] for i, (other, _) in enumerate(self.stands[gid]) if i != slot)
        return self.rng.choice(eggs) if lowest_shown else eggs[0]

    def steal(self, plan, gid):
        seconds, egg_id, slot = plan[0], plan[1], plan[2]
        self.t += seconds
        self.theft_seconds += seconds
        if self.rng.random() < self.b["fail"]:
            return
        self.thefts += 1
        self.qi += self.burst(egg_id)
        self.stones += self.R.egg_stones(egg_id)
        self.stands[gid][slot] = (None, 0)
        self.stands[gid][slot] = (self.respawn_egg(gid, slot), self.t + self.R.cfg["EggTheft"]["RespawnTime"])
        element = self.R.guardians[gid]["element"]
        if element:
            self.elements.add(element)
        if gid not in self.secured_guardians:
            self.secured_guardians.add(gid)
            for quest in self.R.cfg["Quests"]:
                if quest["Kind"] == "Secure" and quest["Goal"] == gid:
                    self.stones += quest["Reward"]
        self.hatch(egg_id)
        self.refresh()

    # -- the rest of the loop
    def shop(self):
        R = self.R
        tier = R.realm_of[self.idx]
        price = R.weapons[tier - 1]["Price"]
        if tier not in self.weapons and self.stones >= price:
            self.stones -= price
            self.weapons.add(tier)
        if self.b["forge"] and self.elements and tier in self.weapons and tier not in self.forged:
            cost = max(R.cfg["Forge"]["MinPrice"], math.floor(price * R.cfg["Forge"]["PriceShare"]))
            if self.stones >= cost:
                self.stones -= cost
                self.forged.add(tier)
        if tier not in self.weapons:
            return  # saving for this realm's weapon
        egg = R.market_eggs_for(self.idx)
        egg_price = R.market_price(egg)
        reserve = egg_price * (3 if self.b["market"] == "lazy" else 1)
        bought = 0
        while self.stones >= reserve and self.stones >= egg_price and bought < 30:
            self.stones -= egg_price
            self.hatch(egg)
            self.t += 8
            bought += 1
            if self.b["market"] == "lazy":
                break
        if bought:
            self.refresh()

    def relics(self):
        if self.b["relic_seconds"] is None:
            return
        for relic in self.R.relics:
            if relic["Id"] not in self.relics_done and self.idx >= relic["idx"]:
                self.relics_done.add(relic["Id"])
                self.t += self.b["relic_seconds"]
                self.qi += math.floor(relic["QiReward"] * self.pass_mult)  # DiscoveryService
                self.stones += self.R.relic_stones(relic)
                if relic.get("Element"):
                    self.elements.add(relic["Element"])

    def break_through(self):
        R = self.R
        while self.idx + 1 < len(R.ranks) and self.qi >= R.ranks[self.idx + 1]["QiRequired"]:
            nxt = self.idx + 1
            new_realm = R.realm_of[nxt] != R.realm_of[self.idx]
            self.t += 3
            if new_realm:
                trib = R.cfg["Tribulation"]
                k = R.realm_of[nxt] - 2
                attempt = trib["Gather"] + math.ceil(trib["Bolts"][k] / trib["Together"][k]) * trib["Gap"][k] + trib["Warn"][k] + 2
                base, step = self.b["tribulation_fail"]
                fail = min(0.85, base + step * k)
                self.t += attempt
                while self.rng.random() < fail:
                    # a failed try, then RetryAfter seconds: spent meditating (Qi still comes in), then another try
                    self.meditate(R.cfg["Tribulation"]["RetryAfter"], spring=False)
                    self.t += attempt
            self.idx = nxt
            self.rank_reached[nxt] = self.t
            if new_realm:
                self.realm_entered[R.realm_of[nxt]] = self.t
            for quest in R.cfg["Quests"]:
                if quest["Kind"] == "Rank" and quest["Goal"] == R.ranks[nxt]["Id"]:
                    self.stones += quest["Reward"]
            self.stones += sum(reward for unlock, reward in self.visit_quests if unlock == nxt)
            self.relics()
            self.refresh()

    def meditate(self, seconds, spring=True):
        self.qi += self.meditate_rate(spring) * int(seconds)
        self.t += seconds
        self.med_seconds = getattr(self, "med_seconds", 0.0) + seconds

    def seconds_to_next(self, rate):
        if self.idx + 1 >= len(self.R.ranks):
            return 0
        need = self.R.ranks[self.idx + 1]["QiRequired"] - self.qi
        return max(1, math.ceil(need / max(rate, 1)))

    def act(self, budget):
        """One action, at most `budget` play seconds where possible."""
        style = self.p["style"]
        med_rate = self.meditate_rate(True)
        if style in ("efficient", "fast"):
            # the island whose best egg pays the most Qi a second; there it takes the best egg showing (a lesser one when the
            # best isn't up: that also re-rolls the stand, and brings a pet and stones). Thefts are worth it a little under
            # meditation's rate for the pets and stones.
            choices = [(self.potential(gid), gid) for gid in self.R.guardians]
            rate, gid = max(choices)
            plan = self.theft_plan(gid) if rate >= 0.8 * med_rate else None
            # ...unless what is actually showing pays much less than meditating (stands holding only eggs it can't take
            # or capped ones): then it meditates
            if plan and plan[4] / plan[0] >= 0.6 * med_rate:
                self.steal(plan, gid)
                return
            self.meditate(min(budget, 60, self.seconds_to_next(med_rate)))
            return
        if style == "casual" and self.theft_seconds < self.b["theft_share"] * self.t:
            # a casual player goes to the newest island they can, not the best-paying one
            open_ids = [gid for gid, g in self.R.guardians.items() if self.idx >= g["unlock"]]
            gid = max(open_ids, key=lambda x: self.R.guardians[x]["unlock"])
            plan = self.theft_plan(gid)
            if plan:
                self.steal(plan, gid)
                return
        spring = self.rng.random() < self.b["spring_share"]
        self.meditate(min(budget, 120, self.seconds_to_next(self.meditate_rate(spring))), spring)

    def session_start(self, away_seconds, day):
        R = self.R
        cfg = R.cfg["Rewards"]
        if away_seconds >= cfg["Offline"]["MinMinutes"] * 60:
            self.qi += self.at_rate(cfg["Offline"]["Share"] * min(away_seconds, cfg["Offline"]["MaxHours"] * 3600), no_boost=True)
        self.day_boosts(day)
        daily = cfg["Daily"][day % len(cfg["Daily"])]
        realm = R.realm_of[self.idx]
        stones = max(5, round_nice(daily["Stones"] * R.stones_cfg["RealmFactor"] ** (realm - 1)))
        self.stones += math.floor(stones * self.daily_stones_mult + 0.5)
        if daily.get("QiMinutes"):
            self.qi += self.at_rate(daily["QiMinutes"] * 60)
        if daily.get("BoostMinutes") and self.boost_mult > 1:
            self.add_boost(daily["BoostMinutes"])
        spins = R.cfg["SpinWheel"]["DailySpins"]
        segments = R.cfg["SpinWheel"]["Segments"]
        total = sum(s["Weight"] for s in segments)
        while spins > 0:
            spins -= 1
            pick = self.rng.random() * total
            for seg in segments:
                pick -= seg["Weight"]
                if pick < 0:
                    break
            if seg["Kind"] == "Stones":
                self.stones += math.floor(round_nice(R.rank_value(self.idx) * seg["Share"]) * self.daily_stones_mult + 0.5)
            elif seg["Kind"] == "Qi":
                self.qi += self.at_rate(seg["Minutes"] * 60)
            elif seg["Kind"] == "Egg":
                self.hatch(R.market_eggs_for(self.idx))
            elif seg["Kind"] == "Spin":
                spins += 1
            elif seg["Kind"] == "Boost" and self.boost_mult > 1:
                self.add_boost(seg["Minutes"])
            elif seg["Kind"] == "Jackpot":
                self.hatch("ExclusiveEgg", luck_applies=False)
        self.t += SESSION_OVERHEAD
        self.refresh()

    def day_boosts(self, day):
        """The timed boost minutes the profile buys each play day (none in a game without timed boosts)."""
        if self.boost_mult > 1 and self.p.get("boost_minutes"):
            self.add_boost(self.p["boost_minutes"])
            self.boost_bought += self.p["boost_minutes"]

    def done(self):
        return self.idx + 1 >= len(self.R.ranks)


def run(rules, profile, seed, calendar_hours=None, limit_hours=2000):
    rng = random.Random(seed)
    player = Player(rules, profile, rng, calendar_hours)
    limit = limit_hours * 3600
    if calendar_hours is None:
        player.t += SESSION_OVERHEAD
        next_day, day = 0.0, 0
        while not player.done() and player.t < limit:
            if player.t >= next_day:  # (no offline Qi or daily reward here: only the boosts a day brings)
                player.day_boosts(day)
                if player.boost_mult > 1:
                    daily = rules.cfg["Rewards"]["Daily"][day % len(rules.cfg["Rewards"]["Daily"])]
                    if daily.get("BoostMinutes"):
                        player.add_boost(daily["BoostMinutes"])
                day += 1
                next_day += PLAY_DAY_HOURS * 3600
            player.break_through()
            player.shop()
            if player.done():
                break
            player.act(60)
        return player, None
    day = 0
    session = calendar_hours * 3600
    while not player.done() and day < 400:
        player.session_start(0 if day == 0 else 86400 - session, day)
        end = player.t + session
        while not player.done() and player.t < end:
            player.break_through()
            player.shop()
            if player.done():
                break
            player.act(end - player.t)
        if player.done():
            into_day = session - (end - player.t)
            return player, day + into_day / session  # whole days before, and the share of the last day's session
        day += 1
    return player, float("inf")


# ------------------------------------------------------------------------------------------------ the report
def fmt_h(seconds):
    hours = seconds / 3600
    return "%.1f h" % hours if hours >= 1 else "%d min" % round(seconds / 60)


def evaluate(rules, runs, seed):
    results = {}
    for profile in PROFILES:
        play, per_realm, per_rank, thefts, hatches, pets, share = [], [], [], [], [], [], []
        for r in range(runs):
            player, _ = run(rules, profile, seed + r)
            play.append(player.t if player.done() else float("inf"))
            realms = sorted(player.realm_entered)
            entered = [player.realm_entered[k] for k in realms] + [player.t]
            per_realm.append([entered[i + 1] - entered[i] for i in range(len(realms))])
            ranks = sorted(player.rank_reached)
            per_rank.append([player.rank_reached[ranks[i + 1]] - player.rank_reached[ranks[i]] for i in range(len(ranks) - 1)])
            thefts.append(player.thefts)
            hatches.append(player.hatches)
            pets.append(player.pet_pct + player.codex_pct)
            share.append(player.theft_seconds / max(1.0, player.t))
        calendar = {}
        for hours in DAILY_HOURS:
            days = []
            for r in range(max(5, runs // 3)):
                _, d = run(rules, profile, seed + 1000 + r, calendar_hours=hours)
                days.append(d)
            calendar[hours] = statistics.median(days)
        n_realm = min(len(x) for x in per_realm)
        n_rank = min(len(x) for x in per_rank)
        results[profile["key"]] = {
            "label": profile["label"],
            "median": statistics.median(play),
            "p10": sorted(play)[max(0, int(runs * 0.1))],
            "p90": sorted(play)[min(runs - 1, int(runs * 0.9))],
            "realms": [statistics.median(x[i] for x in per_realm) for i in range(n_realm)],
            "ranks": [statistics.median(x[i] for x in per_rank) for i in range(n_rank)],
            "calendar": calendar,
            "thefts": statistics.median(thefts),
            "hatches": statistics.median(hatches),
            "bonus": statistics.median(pets),
            "theft_share": statistics.median(share),
        }
    return results


def walls(rules, ranks_seconds):
    """Ranks whose time is more than twice the one before (a wall) or under a third of it (a cliff)."""
    notes = []
    for i in range(1, len(ranks_seconds)):
        before, now = ranks_seconds[i - 1], ranks_seconds[i]
        if before > 30 and now > 2 * before and now > 600:
            notes.append("%s: %s (after %s)" % (rules.ranks[i + 1]["Name"], fmt_h(now), fmt_h(before)))
    return notes


def write_report(rules, results, name, runs):
    os.makedirs(OUT, exist_ok=True)
    lines = ["# Progression simulation: %s" % name, "",
             "Monte Carlo, %d runs per profile (median; p10-p90). Play hours exclude offline Qi, daily rewards and spins;" % runs,
             "the calendar columns include them (one session a day, offline Qi for the hours away, daily claim, 3 spins).", "",
             "| Profile | Play hours to max (p10-p90) | Days at 2 h/day | 4 h/day | 8 h/day | Thefts | Share of time stealing | Hatches | Pets+Codex % at the end |",
             "|---|---|---|---|---|---|---|---|---|"]
    for res in results.values():
        lines.append("| %s | %.1f (%.1f-%.1f) | %.1f | %.1f | %.1f | %d | %d%% | %d | %d |" % (
            res["label"], res["median"] / 3600, res["p10"] / 3600, res["p90"] / 3600,
            res["calendar"][2], res["calendar"][4], res["calendar"][8], res["thefts"], round(100 * res["theft_share"]),
            res["hatches"], res["bonus"]))
    lines += ["", "## Hours spent in each realm (play time, median)", ""]
    header = "| Realm | " + " | ".join(res["label"] for res in results.values()) + " |"
    lines += [header, "|---" * (len(results) + 1) + "|"]
    for i, realm in enumerate(rules.realms):
        cells = []
        for res in results.values():
            cells.append("%.2f" % (res["realms"][i] / 3600) if i < len(res["realms"]) else "-")
        lines.append("| %d %s | %s |" % (i + 1, realm, " | ".join(cells)))
    lines += ["", "## Walls (a rank taking over twice the one before, and over 10 minutes)", ""]
    for res in results.values():
        found = walls(rules, res["ranks"])
        lines.append("- %s: %s" % (res["label"], "; ".join(found) if found else "none"))
    lines += ["", "## Minutes per rank, free efficient and the paying player", "", "| Rank | Free efficient | Paying player |", "|---|---|---|"]
    fe, b16 = results["free_efficient"]["ranks"], results["payer"]["ranks"]
    for i in range(min(len(fe), len(b16))):
        lines.append("| %s | %.1f | %.1f |" % (rules.ranks[i + 1]["Name"], fe[i] / 60, b16[i] / 60))
    with open(os.path.join(OUT, name + ".md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    with open(os.path.join(OUT, name + ".csv"), "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["profile", "play_hours_median", "p10", "p90", "days_2h", "days_4h", "days_8h"] +
                        ["realm%d_hours" % (i + 1) for i in range(len(rules.realms))])
        for key, res in results.items():
            writer.writerow([key, round(res["median"] / 3600, 2), round(res["p10"] / 3600, 2), round(res["p90"] / 3600, 2),
                             res["calendar"][2], res["calendar"][4], res["calendar"][8]] +
                            [round(x / 3600, 3) for x in res["realms"]])
    return "\n".join(lines)


def write_compare(before, after):
    """compare.md: play hours and days to the top, per profile, from two runs' .csv files."""
    def rows(name):
        with open(os.path.join(OUT, name + ".csv"), encoding="utf-8") as handle:
            return {row["profile"]: row for row in csv.DictReader(handle)}
    labels = {p["key"]: p["label"] for p in PROFILES}
    a, b = rows(before), rows(after)
    lines = ["# Before (%s) and after (%s)" % (before, after), "",
             "| Profile | Play h before | after | Days at 2 h/day before | after | 4 h/day before | after | 8 h/day before | after |",
             "|---|---|---|---|---|---|---|---|---|"]
    for key in a:
        if key in b:
            x, y = a[key], b[key]
            values = [float(v[f]) for f in ("play_hours_median", "days_2h", "days_4h", "days_8h") for v in (x, y)]
            lines.append("| %s | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f |" % tuple([labels.get(key, key)] + values))
    text = "\n".join(lines) + "\n"
    with open(os.path.join(OUT, "compare.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", action="store_true")
    parser.add_argument("--both", action="store_true")
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20261116)
    parser.add_argument("--root", help="read the game from this folder instead (holding src/...), e.g. an older version's files")
    parser.add_argument("--name", help="the output's name instead of current")
    parser.add_argument("--mults", help="the proposal's realm 4-12 multipliers, comma-separated (default PROPOSAL's)")
    parser.add_argument("--stands", choices=["own", "code"], help="the proposal's stand rule (default PROPOSAL's)")
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"),
                        help="only write output/compare.md from two earlier runs' .csv files (e.g. before_2026-11-16 current)")
    args = parser.parse_args()
    if args.compare:
        write_compare(*args.compare)
        return
    global ROOT
    if args.root:
        ROOT = os.path.abspath(args.root)
    game = load_game()
    todo = []
    if args.both or not args.proposal:
        todo.append((args.name or "current", Rules(copy.deepcopy(game))))
    if args.both or args.proposal:
        changed = copy.deepcopy(game)
        proposal = dict(PROPOSAL)
        if args.mults:
            values = [float(v) for v in args.mults.split(",")]
            proposal["multipliers"] = {**PROPOSAL["multipliers"], **{4 + i: v for i, v in enumerate(values)}}
        if args.stands:
            proposal["stand_rule"] = args.stands
        apply_proposal(changed["cfg"], proposal)
        todo.append(("proposal" + ("_config_only" if proposal.get("stand_rule") == "code" else ""), Rules(changed)))
    all_results = {}
    for name, rules in todo:
        all_results[name] = evaluate(rules, args.runs, args.seed)
        print(write_report(rules, all_results[name], name, args.runs))
        print()
    if len(all_results) == 2:
        lines = ["# Before and after (%s)" % todo[1][0], "",
                 "| Profile | Play h now | Play h proposal | Days at 2 h/day now | proposal | Days at 4 h/day now | proposal | Days at 8 h/day now | proposal |",
                 "|---|---|---|---|---|---|---|---|---|"]
        for key in all_results["current"]:
            a, b = all_results["current"][key], all_results[todo[1][0]][key]
            lines.append("| %s | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f |" % (
                a["label"], a["median"] / 3600, b["median"] / 3600, a["calendar"][2], b["calendar"][2],
                a["calendar"][4], b["calendar"][4], a["calendar"][8], b["calendar"][8]))
        text = "\n".join(lines) + "\n"
        with open(os.path.join(OUT, "compare%s.md" % todo[1][0][len("proposal"):]), "w", encoding="utf-8") as handle:
            handle.write(text)
        print(text)


if __name__ == "__main__":
    main()
