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
            TrialTokenSpots = { Vector3.new(-72.00, 26.00, 214.00), Vector3.new(72.00, 26.00, 214.00), Vector3.new(-96.00, 50.00, 262.00), Vector3.new(96.00, 50.00, 262.00), Vector3.new(24.00, 36.00, 302.00), Vector3.new(-24.00, 36.00, 302.00) },
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
        Vector3.new(-72.00, 26.00, 214.00), Vector3.new(72.00, 26.00, 214.00), Vector3.new(-96.00, 50.00, 262.00), Vector3.new(96.00, 50.00, 262.00),
    },
    Paths = { -- those paths, as knots
        { Vector3.new(-26.00, 24.00, 155.00), Vector3.new(-40.00, 25.00, 178.00), Vector3.new(-56.00, 26.00, 198.00), Vector3.new(-72.00, 26.00, 214.00) },
        { Vector3.new(26.00, 24.00, 155.00), Vector3.new(40.00, 25.00, 178.00), Vector3.new(56.00, 26.00, 198.00), Vector3.new(72.00, 26.00, 214.00) },
        { Vector3.new(-44.00, 36.00, 306.00), Vector3.new(-72.00, 42.00, 296.00), Vector3.new(-88.00, 47.00, 280.00), Vector3.new(-96.00, 50.00, 262.00) },
        { Vector3.new(44.00, 36.00, 306.00), Vector3.new(72.00, 42.00, 296.00), Vector3.new(88.00, 47.00, 280.00), Vector3.new(96.00, 50.00, 262.00) },
    },
    Dress = { -- trees and rocks, each at the ground's own height: position, yaw
        TreesO = { { Vector3.new(166.92, 71.66, 282.62), 4.664 }, { Vector3.new(288.54, 56.43, 186.23), 5.190 }, { Vector3.new(246.76, 21.83, 218.50), 5.862 }, { Vector3.new(306.53, 55.92, 210.31), 0.185 }, { Vector3.new(181.89, 20.66, 204.52), 4.613 }, { Vector3.new(157.14, 22.77, 249.11), 1.412 }, { Vector3.new(268.42, 54.79, 217.92), 3.666 }, { Vector3.new(249.77, 17.62, 181.35), 2.365 }, { Vector3.new(134.62, 60.95, 317.51), 3.810 }, { Vector3.new(184.90, 72.57, 274.34), 3.096 }, { Vector3.new(195.46, 72.60, 309.52), 4.500 }, { Vector3.new(197.35, 22.75, 228.27), 3.410 }, { Vector3.new(180.48, 73.65, 296.25), 5.459 }, { Vector3.new(114.71, 21.97, 252.17), 2.333 }, { Vector3.new(132.63, 22.21, 255.63), 2.617 }, { Vector3.new(166.76, 72.16, 308.13), 0.471 }, { Vector3.new(187.76, 18.66, 188.61), 5.203 }, { Vector3.new(225.29, 72.61, 310.71), 2.194 }, { Vector3.new(154.58, 23.54, 232.11), 5.672 }, { Vector3.new(210.44, 74.42, 301.52), 2.121 }, { Vector3.new(83.05, 20.52, 235.59), 1.514 }, { Vector3.new(264.96, 21.78, 313.85), 4.178 }, { Vector3.new(148.41, 40.02, 304.99), 4.324 }, { Vector3.new(288.04, 55.21, 224.01), 4.372 } },
        TreesU = { { Vector3.new(-112.54, 72.44, 338.03), 4.697 }, { Vector3.new(0.85, 103.13, 390.79), 5.492 }, { Vector3.new(-25.13, 101.28, 338.22), 4.746 }, { Vector3.new(-27.41, 102.16, 350.36), 2.524 }, { Vector3.new(-60.52, 15.50, 167.48), 0.521 }, { Vector3.new(60.92, 20.83, 397.47), 5.561 }, { Vector3.new(77.49, 21.16, 370.48), 0.872 }, { Vector3.new(-47.79, 16.06, 170.55), 4.630 }, { Vector3.new(-62.99, 21.80, 322.89), 0.640 }, { Vector3.new(107.64, 72.06, 331.89), 2.631 }, { Vector3.new(63.86, 18.31, 183.48), 5.342 }, { Vector3.new(-62.30, 20.92, 398.58), 1.103 }, { Vector3.new(-6.42, 106.40, 367.18), 5.871 }, { Vector3.new(-41.11, 19.02, 193.15), 3.140 }, { Vector3.new(123.51, 70.26, 334.14), 1.985 }, { Vector3.new(-101.82, 21.00, 369.26), 5.851 }, { Vector3.new(-100.67, 71.07, 305.66), 3.311 }, { Vector3.new(-69.55, 16.02, 175.69), 3.824 }, { Vector3.new(-54.50, 17.21, 181.55), 0.044 }, { Vector3.new(10.39, 105.74, 346.77), 5.278 }, { Vector3.new(35.50, 102.41, 345.36), 4.231 }, { Vector3.new(67.35, 21.25, 381.44), 2.888 }, { Vector3.new(-17.13, 104.62, 356.70), 1.927 }, { Vector3.new(62.13, 15.89, 167.70), 0.459 }, { Vector3.new(45.44, 9.76, 131.07), 0.346 }, { Vector3.new(-14.65, 101.03, 324.07), 2.255 }, { Vector3.new(-74.84, 22.12, 265.67), 4.511 }, { Vector3.new(71.12, 21.30, 247.93), 5.679 }, { Vector3.new(91.98, 72.91, 331.61), 3.127 }, { Vector3.new(-102.66, 72.74, 320.57), 1.862 }, { Vector3.new(62.24, 11.52, 140.13), 4.396 }, { Vector3.new(-43.01, 7.09, 118.11), 4.071 } },
        RocksD = { { Vector3.new(-172.77, 15.17, 129.59), 4.233 }, { Vector3.new(-78.13, 16.00, 150.21), 0.224 }, { Vector3.new(-167.86, 24.13, 246.04), 3.267 }, { Vector3.new(-129.78, 20.90, 225.14), 6.157 }, { Vector3.new(-148.43, 22.95, 262.13), 0.578 }, { Vector3.new(-301.41, 21.52, 238.23), 2.637 }, { Vector3.new(-222.27, 25.96, 251.44), 1.696 }, { Vector3.new(-171.15, 20.84, 205.52), 1.407 }, { Vector3.new(-137.78, 42.49, 317.53), 5.551 }, { Vector3.new(-86.16, 21.94, 249.71), 2.507 }, { Vector3.new(-262.12, 23.18, 229.09), 5.639 }, { Vector3.new(-173.53, 16.00, 181.11), 3.115 }, { Vector3.new(-152.73, 23.62, 299.43), 1.984 }, { Vector3.new(-187.80, 52.58, 322.31), 2.804 }, { Vector3.new(-274.48, 21.67, 246.28), 0.067 }, { Vector3.new(-250.18, 24.00, 284.86), 0.364 }, { Vector3.new(-218.09, 70.26, 289.18), 5.639 }, { Vector3.new(-322.39, 21.43, 210.90), 2.865 }, { Vector3.new(-259.13, 18.49, 177.45), 1.278 }, { Vector3.new(-188.46, 21.78, 215.11), 3.001 } },
    },
    Falls = { -- where a waterfall pours off a mesa's rim: the lip and the point behind it
        { Zone = "O", Lip = Vector3.new(160.82, 65.54, 269.38), From = Vector3.new(167.58, 72.25, 273.28) },
        { Zone = "O", Lip = Vector3.new(97.37, 52.20, 293.39), From = Vector3.new(100.58, 59.55, 297.98) },
        { Zone = "U", Lip = Vector3.new(0.00, 82.66, 315.76), From = Vector3.new(0.00, 103.75, 324.56) },
    },
    Moon = { Position = Vector3.new(-230.00, 330.00, 640.00), Radius = 70.0 }, -- behind and over the Demonic mountains
}
