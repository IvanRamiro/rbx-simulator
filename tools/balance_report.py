"""Prints how long cultivation progression takes with the numbers in GameConfig.lua.

    python3 tools/balance_report.py

Reads the ranks, pet bonuses, Qi Spring bonus, egg chances and flight speeds
straight from src/shared/GameConfig.lua, so it always matches the game.
Times are minutes of cultivating (Qi only comes from cultivation).

The "typical" player follows the pets they would usually own by then:
an Aqua Wisp in Qi Awakening, Aqua Wisp + Ember Wyrm + Volt Fox in Qi
Foundation, and Golden Kirin + Volt Fox + Ember Wyrm in Spirit Core, always
cultivating in the Qi Spring.
"""

import os
import re

CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "shared", "GameConfig.lua")

# Pets a typical player has equipped in each realm (see the docstring)
TYPICAL_PETS = {
    "Qi Awakening": ["AquaWisp"],
    "Qi Foundation": ["AquaWisp", "EmberWyrm", "VoltFox"],
    "Spirit Core": ["GoldenKirin", "VoltFox", "EmberWyrm"],
}


def read_config():
    text = open(CONFIG).read()

    number = lambda pattern: float(re.search(pattern, text).group(1))
    config = {
        "base_reward": number(r"CultivationQiReward = ([\d.]+)"),
        "interval": number(r"CultivationInterval = ([\d.]+)"),
        "spring_bonus": number(r"TrainingStation = \{[^}]*QiBonusPercent = ([\d.]+)"),
    }
    config["egg_cooldown"] = float(re.search(r"BeginnerEgg = \{.*?Cooldown = ([\d.]+)", text, re.S).group(1))

    config["ranks"] = [
        {"id": m[0], "name": m[1], "realm": m[2], "level": int(m[3]), "qi": int(m[4])}
        for m in re.findall(
            r'\{ Id = "(\w+)", Name = "([^"]+)", Realm = "([^"]+)", Level = (\d), QiRequired = (\d+)', text
        )
    ]
    config["pets"] = {
        m[0]: {"name": m[1], "rarity": m[2], "bonus": int(m[3])}
        for m in re.findall(r'(\w+) = \{ DisplayName = "([^"]+)", Rarity = "(\w+)",[^\n]*QiBonusPercent = (\d+)', text)
    }
    pool_text = re.search(r"BeginnerEgg = \{.*?Pool = \{(.*?)\n        \},", text, re.S).group(1)
    config["egg_pool"] = [(m[0], float(m[1])) for m in re.findall(r'PetId = "(\w+)", Weight = ([\d.]+)', pool_text)]
    flight_text = re.search(r"SpeedLevels = \{(.*?)\n        \},", text, re.S).group(1)
    config["flight"] = [(m[0], int(m[1])) for m in re.findall(r'RankId = "(\w+)", Speed = (\d+)', flight_text)]
    return config


def qi_per_second(config, pet_ids, in_spring=True):
    bonus = sum(config["pets"][pet]["bonus"] for pet in pet_ids)
    if in_spring:
        bonus += config["spring_bonus"]
    # Matches QiService: floor(base * (100 + bonus) / 100) per interval
    return (config["base_reward"] * (100 + bonus) // 100) / config["interval"]


def main():
    config = read_config()
    ranks = config["ranks"]

    print("Rank progression (minutes of cultivating in the Qi Spring)")
    print(f"{'Rank':<22}{'Realm':<16}{'Qi needed':>10}{'Qi/s':>7}{'Step':>8}{'Total':>8}{'Flight':>8}")
    flight_by_rank = dict(config["flight"])
    total_seconds = 0
    flight_speed = 0
    for previous, rank in zip([None] + ranks[:-1], ranks):
        rate = qi_per_second(config, TYPICAL_PETS.get(rank["realm"], []))
        step = 0 if previous is None else (rank["qi"] - previous["qi"]) / rate
        total_seconds += step
        flight_speed = flight_by_rank.get(rank["id"], flight_speed)
        print(
            f"{rank['name']:<22}{rank['realm']:<16}{rank['qi']:>10}{rate:>7.1f}"
            f"{step / 60:>8.1f}{total_seconds / 60:>8.1f}{flight_speed or '-':>8}"
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
    total_weight = sum(weight for _, weight in config["egg_pool"])
    cooldown = config["egg_cooldown"]
    print(f"Beginner Qi Egg ({cooldown:.0f}s cooldown): chance and average time to hatch one")
    for pet_id, weight in config["egg_pool"]:
        chance = weight / total_weight
        hatches = 1 / chance
        print(
            f"  {config['pets'][pet_id]['name']:<20}{chance * 100:>6.1f}%"
            f"   1 in {hatches:>6.0f} hatches   ~{hatches * cooldown / 60:>7.1f} min"
        )


if __name__ == "__main__":
    main()
