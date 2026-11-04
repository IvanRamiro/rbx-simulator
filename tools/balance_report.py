"""Prints how long cultivation progression takes with the numbers in GameConfig.lua.

    python3 tools/balance_report.py

Reads the ranks, pet bonuses, Qi Spring bonus, relic rewards, egg chances and Qinggong levels
straight from src/shared/GameConfig.lua, so it always matches the game.
Times are minutes of cultivating alone. Securing a guardian's egg also pays a burst worth
EggTheft.SecureQiMinutes of cultivating, so real players who fight go faster than this.

The "typical" player follows the pets they would usually own by then (see
TYPICAL_PETS), always cultivating in the Qi Spring. From Spirit Soul on, each
realm's QiMultiplier multiplies every reward.
"""

import os
import re

CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "shared", "GameConfig.lua")

# Pets a typical player has equipped in each realm (see the docstring)
TYPICAL_PETS = {
    "Qi Awakening": ["AquaWisp"],
    "Qi Foundation": ["AquaWisp", "EmberWyrm", "LunarHopper"],
    "Spirit Core": ["GoldenKirin", "VoltFox", "EmberWyrm"],
    "Spirit Soul": ["ThunderclawDrake", "LanternWarden", "GoldenManeLion"],
    "Ascendant Realm": ["NebulaOwl", "CelestialSnowLeopard", "NinefoldSpiritSerpent"],
    "Immortal Realm": ["CometStag", "EclipseCat", "CelestialSnowLeopard"],
    "Divine Realm": ["TimekeeperTortoise", "CometStag", "EclipseCat"],
    "Cosmic Realm": ["RuneSphinx", "TimekeeperTortoise", "DreadfangCerberus"],
    "Void Realm": ["RuneSphinx", "CelestialPearlDragon", "TimekeeperTortoise"],
    "Heavenly Dao": ["HeavenbreakerApe", "RuneSphinx", "CelestialPearlDragon"],
    "Primordial Realm": ["HeavenbreakerApe", "RuneSphinx", "GalaxyManta"],
    "Eternal Transcendence": ["HeavenbreakerApe", "ThousandYearDreamEater", "GalaxyManta"],
}


def read_config():
    text = open(CONFIG).read()

    number = lambda pattern: float(re.search(pattern, text).group(1))
    config = {
        "base_reward": number(r"CultivationQiReward = ([\d.]+)"),
        "interval": number(r"CultivationInterval = ([\d.]+)"),
        "spring_bonus": number(r"TrainingStation = \{[^}]*QiBonusPercent = ([\d.]+)"),
    }

    config["ranks"] = [
        {"id": m[0], "name": m[1], "realm": m[2], "level": int(m[3]), "qi": int(m[4]), "multiplier": float(m[5])}
        for m in re.findall(
            r'\{ Id = "(\w+)", Name = "([^"]+)", Realm = "([^"]+)", Level = (\d), QiRequired = (\d+), '
            r'AuraTier = \d, QiMultiplier = ([\d.]+)',
            text,
        )
    ]
    config["pets"] = {
        m[0]: {"name": m[1], "rarity": m[2], "bonus": int(m[3])}
        for m in re.findall(r'(\w+) = \{ DisplayName = "([^"]+)", Rarity = "(\w+)",[^\n]*QiBonusPercent = (\d+)', text)
    }
    config["eggs"] = [
        {
            "name": m[0],
            "rank": m[1],
            "cooldown": float(m[2]),
            "pool": [(p[0], float(p[1])) for p in re.findall(r'PetId = "(\w+)", Weight = ([\d.]+)', m[3])],
        }
        for m in re.findall(
            r'DisplayName = "([^"]+)",\s*RequiredRank = "(\w+)",\s*Cooldown = ([\d.]+),\s*Pool = \{(.*?)\n            \},',
            text,
            re.S,
        )
    ]
    config["relics"] = [
        (m[0], int(m[1]), m[2])
        for m in re.findall(r'DisplayName = "([^"]+)", QiReward = (\d+), RequiredRank = "(\w+)"', text)
    ]
    qinggong = re.search(r"Qinggong = \{.*?Levels = \{(.*?)\n        \},", text, re.S).group(1)
    config["qinggong"] = [(m[0], int(m[1]), int(m[2]))
                          for m in re.findall(r'RankId = "(\w+)", AirLeaps = (\d+), RunSpeed = (\d+)', qinggong)]
    return config


def qi_per_second(config, pet_ids, in_spring=True, multiplier=1):
    bonus = sum(config["pets"][pet]["bonus"] for pet in pet_ids)
    if in_spring:
        bonus += config["spring_bonus"]
    # Matches QiService: floor(base * multiplier * (100 + bonus) / 100) per interval
    return (config["base_reward"] * multiplier * (100 + bonus) // 100) / config["interval"]


def main():
    config = read_config()
    ranks = config["ranks"]

    print("Rank progression (minutes of cultivating in the Qi Spring)")
    print(f"{'Rank':<22}{'Realm':<23}{'Qi needed':>12}{'x':>5}{'Qi/s':>9}{'Step':>8}{'Total h':>9}{'Leaps':>6}{'Run':>5}")
    qinggong_by_rank = {rank_id: (leaps, run) for rank_id, leaps, run in config["qinggong"]}
    total_seconds = 0
    leaps, run = config["qinggong"][0][1:]
    for previous, rank in zip([None] + ranks[:-1], ranks):
        # Qi for this rank is earned at the previous rank's power, with its realm's pets
        earning = previous or rank
        rate = qi_per_second(config, TYPICAL_PETS.get(earning["realm"], []), multiplier=earning["multiplier"])
        step = 0 if previous is None else (rank["qi"] - previous["qi"]) / rate
        total_seconds += step
        leaps, run = qinggong_by_rank.get(rank["id"], (leaps, run))
        print(
            f"{rank['name']:<22}{rank['realm']:<23}{rank['qi']:>12}{rank['multiplier']:>5.0f}{rate:>9.1f}"
            f"{step / 60:>8.1f}{total_seconds / 3600:>9.2f}{leaps:>6}{run:>5}"
        )

    print()
    print("Qi per second with different pets (in the Qi Spring / outside it)")
    for label, pets in [
        ("No pets", []),
        ("Aqua Wisp", ["AquaWisp"]),
        ("Typical Qi Foundation", TYPICAL_PETS["Qi Foundation"]),
        ("Typical Spirit Core", TYPICAL_PETS["Spirit Core"]),
        ("Best 3 pets", sorted(config["pets"], key=lambda p: -config["pets"][p]["bonus"])[:3]),
    ]:
        print(f"  {label:<24}{qi_per_second(config, pets):>6.1f} / {qi_per_second(config, pets, False):>5.1f}")

    print()
    relic_total = sum(reward for _, reward, _ in config["relics"])
    print(f"Spirit Relics: {len(config['relics'])} relics, {relic_total} Qi in total (one-time rewards)")
    for name, reward, required in config["relics"]:
        print(f"  {name:<22}{reward:>6} Qi   needs {required}")

    for egg in config["eggs"]:
        print()
        total_weight = sum(weight for _, weight in egg["pool"])
        cooldown = egg["cooldown"]
        print(f"{egg['name']} (needs {egg['rank']}, {cooldown:.0f}s cooldown): chance and average time to hatch one")
        for pet_id, weight in egg["pool"]:
            chance = weight / total_weight
            hatches = 1 / chance
            pet = config["pets"][pet_id]
            print(
                f"  {pet['name']:<20}{pet['rarity']:<11}+{pet['bonus']:<4}{chance * 100:>6.1f}%"
                f"   1 in {hatches:>6.0f} hatches   ~{hatches * cooldown / 60:>7.1f} min"
            )


if __name__ == "__main__":
    main()
