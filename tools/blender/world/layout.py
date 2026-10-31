"""World layout for the five floating islands: one source of truth for island placement and the
Qinggong routes between them. Coordinates are Roblox studs (X east, Y up, Z south; north is -Z).

Run `python3 tools/blender/world/layout.py` to print the layout and check every route gap
against the measured Qinggong reach of its unlock rank (and the rank below it).
"""
import math

# Measured in Studio (QinggongController rules, Roblox gravity): air leaps -> (flat reach, peak height).
REACH = {1: (31, 14), 2: (50, 21), 3: (71, 28), 4: (97, 34), 5: (124, 41), 6: (153, 48), 7: (187, 55)}
LANDING_CLEARANCE = 3  # studs of peak height left over when landing on a raised stone

ISLANDS = {
    "StartingIsland": {"centre": (0, 200, 0), "radius": 95},
    "JadeGrove": {"centre": (330, 206, -70), "radius": 80},
    "EmberPeak": {"centre": (-318, 222, 262), "radius": 75},
    "MoonlitIsle": {"centre": (80, 392, -330), "radius": 60},
    "OriginAbyss": {"centre": (-560, 95, -540), "radius": 85},
}

# Each route leaves one island's rim and lands on another's. `leaps` is the air-leap count of
# the rank that unlocks the destination; every gap must be reachable with it and out of reach
# with one leap fewer. `gap` is the planned horizontal spacing between stones.
ROUTES = {
    "JadeRoute": {"from": (100, 200, -12), "to": (252, 206, -52), "leaps": 2, "gap": 40},
    "EmberRoute": {"from": (-72, 200, 72), "to": (-262, 224, 214), "leaps": 3, "gap": 57},
    "MoonlitRoute": {"from": (8, 204, -96), "to": (66, 392, -272), "leaps": 4, "climb": 27},
    "OriginRoute": {"from": (-78, 200, -70), "to": (-470, 200, -430), "leaps": 6, "gap": 132},
}


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def flat(a, b):
    return math.hypot(b[0] - a[0], b[2] - a[2])


def route_stones(name):
    """Stone positions (top centres) between a route's ends, evenly spaced."""
    r = ROUTES[name]
    a, b = r["from"], r["to"]
    if "climb" in r:
        steps = math.ceil((b[1] - a[1]) / r["climb"])
    else:
        steps = max(1, round(flat(a, b) / r["gap"]))
    return [lerp(a, b, i / steps) for i in range(1, steps)], steps


def check():
    ok = True
    for name, r in ROUTES.items():
        stones, steps = route_stones(name)
        pts = [r["from"]] + stones + [r["to"]]
        n = r["leaps"]
        for p, q in zip(pts, pts[1:]):
            d, dy = flat(p, q), q[1] - p[1]
            reach, peak = REACH[n]
            lower_reach, lower_peak = REACH[n - 1]
            can = d <= reach and dy <= peak - LANDING_CLEARANCE
            blocked = d > lower_reach or dy > lower_peak - LANDING_CLEARANCE
            if not (can and blocked):
                ok = False
            print(f"  {name}: gap {d:6.1f} rise {dy:+6.1f}  rank-ok={can}  lower-rank-blocked={blocked}")
        print(f"{name}: {steps} gaps, {len(stones)} stones")
    return ok


if __name__ == "__main__":
    for n, isl in ISLANDS.items():
        print(n, isl)
    print("ALL ROUTES OK" if check() else "SOME GAPS NEED TUNING")
