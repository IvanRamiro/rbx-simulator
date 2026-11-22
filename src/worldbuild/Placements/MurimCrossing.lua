-- Written by tools/blender/world/murim_layout.py (Murim Crossing, 2026-11-22). Do not edit by hand.
-- Island-local Roblox studs (local -Z faces the hub, +X is the Orthodox side), every Y 0 = the island's ground (world Y 200). Read by
-- CrossingBuilder (the court, the gate, the banners, the representatives, the zones) and, later, by each headquarters' build.
-- Yaw: CFrame.Angles(0, Yaw, 0) in the island's frame turns a model's front (-Z) the way it says. Pads: Front is the unit vector toward
-- the Court (a headquarters' main hall faces it), Gate the pad's entrance where its arm arrives, FlatRadius how far from Centre the
-- ground is exactly level; the pad's own materials are Limestone/Grass (Orthodox), LeafyGrass/Mud/Ground/Rock (Unorthodox) and
-- Slate/Asphalt (Demonic): never lay a floor on Grass (its blades come up through it) and keep Basalt/CrackedLava (they bump) to
-- ground nothing is built on.
return {
    Reach = 306,
    Court = { Centre = Vector3.new(0.00, 0.00, 0.00), Radius = 46.0, OathStone = Vector3.new(0.00, 0.00, 0.00), OathYaw = 0.0000 },
    Gate = { Position = Vector3.new(0.00, 0.00, -64.00), Yaw = 0.0000 }, -- the island's own gate, across the end of the bridge
    Arrival = Vector3.new(0.00, 0, -88.00), -- where the bridge's last deck node lands
    Spur = { FromZ = -84.0, ToZ = -38.0, Half = 26.0 },
    Checkpoint = { Position = Vector3.new(0.00, 0.00, -24.00), Yaw = 3.1416 }, -- where a fall from the island returns to: the Court, facing the oath stone
    Order = { "Orthodox", "Unorthodox", "Demonic" },
    Arms = {
        Orthodox = { Axis = Vector3.new(0.8660, 0, -0.5000), Half = 13.0, From = 46.0, To = 137.0, GateAt = 64.0, IdentityTo = 106.0, Centreline = { Vector3.new(39.84, 0.00, -23.00), Vector3.new(91.80, 0.00, -53.00), Vector3.new(118.65, 0.00, -68.50) } },
        Unorthodox = { Axis = Vector3.new(0.0000, 0, 1.0000), Half = 13.0, From = 46.0, To = 137.0, GateAt = 64.0, IdentityTo = 106.0, Centreline = { Vector3.new(0.00, 0.00, 46.00), Vector3.new(0.00, 0.00, 106.00), Vector3.new(0.00, 0.00, 137.00) } },
        Demonic = { Axis = Vector3.new(-0.8660, 0, -0.5000), Half = 13.0, From = 46.0, To = 137.0, GateAt = 64.0, IdentityTo = 106.0, Centreline = { Vector3.new(-39.84, 0.00, -23.00), Vector3.new(-91.80, 0.00, -53.00), Vector3.new(-118.65, 0.00, -68.50) } },
    },
    Reps = { -- each faction's representative stands in the Court in front of its arm, facing the oath stone
        Orthodox = { Position = Vector3.new(29.44, 0.00, -17.00), Yaw = 2.0944 },
        Unorthodox = { Position = Vector3.new(0.00, 0.00, 34.00), Yaw = 0.0000 },
        Demonic = { Position = Vector3.new(-29.44, 0.00, -17.00), Yaw = -2.0944 },
    },
    Banners = { -- a tall pole between the oath stone and each representative
        Orthodox = { Position = Vector3.new(20.78, 0.00, -12.00), Yaw = 2.0944 },
        Unorthodox = { Position = Vector3.new(0.00, 0.00, 24.00), Yaw = 0.0000 },
        Demonic = { Position = Vector3.new(-20.78, 0.00, -12.00), Yaw = -2.0944 },
    },
    Pads = {
        Orthodox = {
            Centre = Vector3.new(177.54, 0.00, -102.50), FlatRadius = 70.0, EdgeRadius = 88.0,
            Front = Vector3.new(-0.8660, 0, 0.5000), FrontYaw = 2.0944,
            Gate = { Position = Vector3.new(118.65, 0.00, -68.50), Yaw = -1.0472 },
            MainHall = { Position = Vector3.new(189.66, 0.00, -109.50), Yaw = 2.0944 },
            Vault = { Position = Vector3.new(184.98, 0.00, -157.61), Yaw = 2.0944 },
            Checkpoint = { Position = Vector3.new(118.65, 0.00, -68.50), Yaw = -1.0472 },
            TrialGates = { Vector3.new(123.84, 0.00, -71.50), Vector3.new(133.80, 0.00, -77.25), Vector3.new(143.76, 0.00, -83.00), Vector3.new(153.72, 0.00, -88.75), Vector3.new(163.68, 0.00, -94.50) },
        },
        Unorthodox = {
            Centre = Vector3.new(0.00, 0.00, 205.00), FlatRadius = 70.0, EdgeRadius = 94.0,
            Front = Vector3.new(-0.0000, 0, -1.0000), FrontYaw = 0.0000,
            Gate = { Position = Vector3.new(0.00, 0.00, 137.00), Yaw = -3.1416 },
            MainHall = { Position = Vector3.new(0.00, 0.00, 219.00), Yaw = 0.0000 },
            Vault = { Position = Vector3.new(44.00, 0.00, 239.00), Yaw = 0.0000 },
            Checkpoint = { Position = Vector3.new(0.00, 0.00, 137.00), Yaw = -3.1416 },
            TrialTokenSpots = { Vector3.new(27.00, 0.00, 251.77), Vector3.new(54.00, 0.00, 205.00), Vector3.new(27.00, 0.00, 158.23), Vector3.new(-27.00, 0.00, 158.23), Vector3.new(-54.00, 0.00, 205.00), Vector3.new(-27.00, 0.00, 251.77) },
        },
        Demonic = {
            Centre = Vector3.new(-177.54, 0.00, -102.50), FlatRadius = 70.0, EdgeRadius = 92.0,
            Front = Vector3.new(0.8660, 0, 0.5000), FrontYaw = -2.0944,
            Gate = { Position = Vector3.new(-118.65, 0.00, -68.50), Yaw = 1.0472 },
            MainHall = { Position = Vector3.new(-189.66, 0.00, -109.50), Yaw = -2.0944 },
            Vault = { Position = Vector3.new(-228.98, 0.00, -81.39), Yaw = -2.0944 },
            Checkpoint = { Position = Vector3.new(-118.65, 0.00, -68.50), Yaw = 1.0472 },
            TrialArena = Vector3.new(-174.07, 0.00, -100.50),
            TrialWaves = { Vector3.new(-187.07, 0.00, -77.98), Vector3.new(-148.07, 0.00, -100.50), Vector3.new(-187.07, 0.00, -123.02) },
        },
    },
}
