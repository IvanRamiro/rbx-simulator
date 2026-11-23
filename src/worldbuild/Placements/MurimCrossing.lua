-- Written by tools/blender/world/murim_layout.py (Murim Crossing, 2026-11-22). Do not edit by hand.
-- Island-local Roblox studs (local -Z faces the hub, +X is the LEFT of whoever has just arrived: the Orthodox side), Y 0 = the plaza's ground
-- (world Y 200). Read by CrossingBuilder (the plaza, the gate, the stairs, the banners, the representatives, the zones, the dressing) and,
-- later, by each headquarters' build. Yaw: CFrame.Angles(0, Yaw, 0) in the island's frame turns a model's front (-Z) the way it says.
-- Pads: Height is the pad's level over the plaza, Front the unit vector toward the plaza (a headquarters' main hall faces it), Gate the pad's
-- entrance just past the stair's top, FlatRadius how far from Centre the ground is exactly level; the pad's own materials are
-- Limestone/Grass (Orthodox), LeafyGrass/Mud/Ground/Sandstone (Unorthodox) and Slate/Asphalt (Demonic): never lay a floor on Grass (its blades
-- come up through it) and keep Basalt/CrackedLava (they bump) to ground nothing is built on.
return {
    Reach = 340, -- how far from the plaza's middle the walkable ground runs (the mountains behind it are scenery)
    Plaza = { Centre = Vector3.new(0.00, 0.00, 0.00), Radius = 76.0, OathStone = Vector3.new(0.00, 0.00, 0.00), OathYaw = 0.0000 },
    Gate = { Position = Vector3.new(0.00, 0.00, -100.00), Yaw = 0.0000 }, -- the island's own gate, across the end of the bridge
    Arrival = Vector3.new(0.00, 0.00, -124.00), -- where the bridge's last deck node lands
    Spur = { FromZ = -120.0, ToZ = -60.0, Half = 26.0 },
    Checkpoint = { Position = Vector3.new(0.00, 0.00, -30.00), Yaw = 3.1416 }, -- where a fall from the island returns to: the plaza, facing the oath stone
    Order = { "Orthodox", "Unorthodox", "Demonic" },
    StepRise = 1.0, StairHalf = 16.0, LandingHalf = 26.0, UnderStep = 1.8,
    Stairs = { -- each headquarters' stairway: its axis (a unit vector from the plaza's middle), its tiers as { Kind, S0, S1, H0, H1 } (S along the axis)
        Orthodox = { Axis = Vector3.new(0.6157, 0, 0.7880), Yaw = -2.4784, Width = 32.0, LandingWidth = 52.0, Top = Vector3.new(93.58, 16.00, 119.78), Tiers = { { "flight", 72.0, 96.0, 0.0, 6.0 }, { "landing", 96.0, 112.0, 6.0, 6.0 }, { "flight", 112.0, 152.0, 6.0, 16.0 } } },
        Unorthodox = { Axis = Vector3.new(0.0000, 0, 1.0000), Yaw = -3.1416, Width = 32.0, LandingWidth = 52.0, Top = Vector3.new(0.00, 36.00, 192.00), Tiers = { { "flight", 72.0, 102.0, 0.0, 12.0 }, { "landing", 102.0, 118.0, 12.0, 12.0 }, { "flight", 118.0, 148.0, 12.0, 24.0 }, { "landing", 148.0, 162.0, 24.0, 24.0 }, { "flight", 162.0, 192.0, 24.0, 36.0 } } },
        Demonic = { Axis = Vector3.new(-0.6157, 0, 0.7880), Yaw = 2.4784, Width = 32.0, LandingWidth = 52.0, Top = Vector3.new(-93.58, 16.00, 119.78), Tiers = { { "flight", 72.0, 96.0, 0.0, 6.0 }, { "landing", 96.0, 112.0, 6.0, 6.0 }, { "flight", 112.0, 152.0, 6.0, 16.0 } } },
    },
    Reps = { -- each faction's representative stands on the plaza in front of its stairs, facing the oath stone
        Orthodox = { Position = Vector3.new(33.25, 0.00, 42.55), Yaw = 0.6632 },
        Unorthodox = { Position = Vector3.new(0.00, 0.00, 54.00), Yaw = 0.0000 },
        Demonic = { Position = Vector3.new(-33.25, 0.00, 42.55), Yaw = -0.6632 },
    },
    Banners = { -- a tall pole at the foot of each stairway
        Orthodox = { Position = Vector3.new(54.72, 0.00, 35.93), Yaw = 0.0000 },
        Unorthodox = { Position = Vector3.new(21.00, 0.00, 62.00), Yaw = 0.0000 },
        Demonic = { Position = Vector3.new(-21.62, 0.00, 61.79), Yaw = 0.0000 },
    },
    Pads = {
        Orthodox = {
            Centre = Vector3.new(126.83, 16.00, 162.33), Height = 16.0, FlatRadius = 54.0, EdgeRadius = 66.0,
            Front = Vector3.new(-0.6157, 0, -0.7880), FrontYaw = 0.6632,
            Gate = { Position = Vector3.new(97.27, 16.00, 124.51), Yaw = -2.4784 },
            MainHall = { Position = Vector3.new(136.68, 16.00, 174.94), Yaw = 0.6632 },
            Vault = { Position = Vector3.new(170.32, 16.00, 156.27), Yaw = 0.6632 },
            Checkpoint = { Position = Vector3.new(97.27, 16.00, 124.51), Yaw = -2.4784 },
            TrialGates = { Vector3.new(51.72, 1.20, 66.19), Vector3.new(64.03, 6.00, 81.95), Vector3.new(76.34, 7.20, 97.71), Vector3.new(84.96, 10.70, 108.75), Vector3.new(92.35, 15.87, 118.20) },
        },
        Unorthodox = {
            Centre = Vector3.new(0.00, 36.00, 250.00), Height = 36.0, FlatRadius = 58.0, EdgeRadius = 70.0,
            Front = Vector3.new(-0.0000, 0, -1.0000), FrontYaw = 0.0000,
            Gate = { Position = Vector3.new(0.00, 36.00, 198.00), Yaw = -3.1416 },
            MainHall = { Position = Vector3.new(0.00, 36.00, 266.00), Yaw = 0.0000 },
            Vault = { Position = Vector3.new(38.00, 36.00, 272.00), Yaw = 0.0000 },
            Checkpoint = { Position = Vector3.new(0.00, 36.00, 198.00), Yaw = -3.1416 },
            TrialTokenSpots = { Vector3.new(-72.00, 21.62, 214.00), Vector3.new(72.00, 21.98, 214.00), Vector3.new(-92.00, 22.36, 270.00), Vector3.new(92.00, 23.30, 270.00), Vector3.new(24.00, 36.00, 302.00), Vector3.new(-24.00, 36.00, 302.00) },
        },
        Demonic = {
            Centre = Vector3.new(-126.83, 16.00, 162.33), Height = 16.0, FlatRadius = 54.0, EdgeRadius = 66.0,
            Front = Vector3.new(0.6157, 0, -0.7880), FrontYaw = -0.6632,
            Gate = { Position = Vector3.new(-97.27, 16.00, 124.51), Yaw = 2.4784 },
            MainHall = { Position = Vector3.new(-136.68, 16.00, 174.94), Yaw = -0.6632 },
            Vault = { Position = Vector3.new(-110.43, 16.00, 203.06), Yaw = -0.6632 },
            Checkpoint = { Position = Vector3.new(-97.27, 16.00, 124.51), Yaw = 2.4784 },
            TrialArena = Vector3.new(-125.59, 16.00, 160.75),
            TrialWaves = { Vector3.new(-105.11, 16.00, 176.76), Vector3.new(-121.98, 16.00, 135.01), Vector3.new(-149.70, 16.00, 170.49) },
        },
    },
    Nooks = { -- the Unorthodox side's hidden lookouts, each at the end of a hidden path
        Vector3.new(-72.00, 21.62, 214.00), Vector3.new(72.00, 21.98, 214.00), Vector3.new(-92.00, 22.36, 270.00), Vector3.new(92.00, 23.30, 270.00),
    },
    Paths = { -- those paths, as knots
        { Vector3.new(-26.00, 24.00, 155.00), Vector3.new(-40.00, 18.16, 178.00), Vector3.new(-56.00, 20.24, 198.00), Vector3.new(-72.00, 21.62, 214.00) },
        { Vector3.new(26.00, 24.00, 155.00), Vector3.new(40.00, 17.35, 178.00), Vector3.new(56.00, 20.82, 198.00), Vector3.new(72.00, 21.98, 214.00) },
        { Vector3.new(-40.00, 32.70, 308.00), Vector3.new(-50.00, 22.57, 304.00) },
        { Vector3.new(-74.00, 22.29, 296.00), Vector3.new(-86.00, 22.60, 284.00), Vector3.new(-92.00, 22.36, 270.00) },
        { Vector3.new(40.00, 38.34, 308.00), Vector3.new(50.00, 23.01, 304.00) },
        { Vector3.new(74.00, 23.22, 296.00), Vector3.new(86.00, 22.66, 284.00), Vector3.new(92.00, 23.30, 270.00) },
    },
    RopeBridges = { -- rope and timber bridges across the Unorthodox side's ravines: the two rims
        { From = Vector3.new(-51.00, 22.49, 303.00), To = Vector3.new(-73.00, 22.23, 297.50) },
        { From = Vector3.new(51.00, 23.08, 303.00), To = Vector3.new(73.00, 23.31, 297.50) },
    },
    Dress = { -- trees and rocks, each at the ground's own height: position, yaw
        TreesO = {  },
        TreesU = {  },
        RocksD = { { Vector3.new(-172.77, 15.17, 129.59), 4.233 }, { Vector3.new(-78.13, 16.00, 150.21), 0.224 }, { Vector3.new(-167.86, 24.13, 246.04), 3.267 }, { Vector3.new(-129.78, 20.90, 225.14), 6.157 }, { Vector3.new(-94.46, 21.90, 251.44), 2.738 }, { Vector3.new(-148.43, 22.95, 262.13), 0.578 }, { Vector3.new(-301.41, 21.52, 238.23), 2.637 }, { Vector3.new(-222.27, 25.96, 251.44), 1.696 }, { Vector3.new(-171.15, 20.84, 205.52), 1.407 }, { Vector3.new(-137.78, 42.49, 317.53), 5.551 }, { Vector3.new(-262.12, 23.18, 229.09), 5.639 }, { Vector3.new(-173.53, 16.00, 181.11), 3.115 }, { Vector3.new(-152.73, 23.62, 299.43), 1.984 }, { Vector3.new(-187.80, 52.58, 322.31), 2.804 }, { Vector3.new(-274.48, 21.67, 246.28), 0.067 }, { Vector3.new(-250.18, 24.00, 284.86), 0.364 }, { Vector3.new(-218.09, 70.26, 289.18), 5.639 }, { Vector3.new(-322.39, 21.43, 210.90), 2.865 }, { Vector3.new(-259.13, 18.49, 177.45), 1.278 }, { Vector3.new(-188.46, 21.78, 215.11), 3.001 } },
    },
    Falls = { -- where a waterfall pours off a mesa's rim: the lip and the point behind it
    },
    Moon = { Position = Vector3.new(-230.00, 330.00, 640.00), Radius = 70.0 }, -- behind and over the Demonic mountains
}
