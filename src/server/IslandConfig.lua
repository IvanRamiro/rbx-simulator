
-- Settings for the floating islands, all in one place: the starting island
-- (the top-level settings) and the outer sky islands (OuterIslands below).
-- Islands are built when the server starts (see IslandService), so changes
-- here show up the next time you press Play.

local IslandConfig = {
    ModelName = "StartingIsland",
    Seed = 2026, -- Change for a different layout; the same seed always gives the same island
    Center = Vector3.new(0, 200, 0), -- Centre of the grass surface

    -- Island body (made of terrain)
    Radius = 90,
    GrassDepth = 6,
    SoilDepth = 8,
    UndersideDepth = 55, -- How far the rocky underside hangs below the soil
    UndersideLayers = 8,

    -- Terrain materials for the top, the soil under it and the rocky underside
    -- (alternating layers). Hills use the top material.
    Materials = {
        Surface = Enum.Material.Grass,
        Soil = Enum.Material.Ground,
        Underside = { Enum.Material.Rock, Enum.Material.Slate },
    },

    -- Note: these recolour ALL terrain of that material in the place, so
    -- each island uses its own materials for its own colours
    TerrainColors = {
        [Enum.Material.Grass] = Color3.fromRGB(92, 156, 94),
        [Enum.Material.Ground] = Color3.fromRGB(112, 92, 72),
        [Enum.Material.Rock] = Color3.fromRGB(98, 104, 120),
        [Enum.Material.Slate] = Color3.fromRGB(80, 86, 104),
    },

    -- Gentle grassy bumps on the surface
    Hills = { Count = 4, MinRadius = 10, MaxRadius = 16 },

    -- Central cultivation platform (players spawn here)
    Platform = {
        Diameter = 40,
        BaseMaterial = Enum.Material.Slate,
        BaseColor = Color3.fromRGB(70, 78, 95),
        FloorMaterial = Enum.Material.Marble,
        FloorColor = Color3.fromRGB(225, 228, 235),
        RingColor = Color3.fromRGB(120, 220, 255), -- Glowing Qi circle
        LanternCount = 4,
        LanternColor = Color3.fromRGB(170, 235, 255),
    },

    -- Pet egg stand. EggId picks the egg from GameConfig.Eggs, which has its
    -- pets, chances, cooldown and required rank.
    EggStand = {
        EggId = "BeginnerQiEgg",
        ModelName = "BeginnerQiEgg",
        Distance = 55, -- Studs from the island centre
        AngleDegrees = 210, -- Direction from the centre (0 = towards +X)
        ClearRadius = 16, -- Hills and decorations stay this far away
        PromptDistance = 10,
        GlowColor = Color3.fromRGB(170, 140, 255),
        EggColor = Color3.fromRGB(255, 240, 210),
    },

    -- Qi Spring training station (its Qi bonus and radius are in GameConfig.TrainingStation)
    TrainingStation = {
        ModelName = "QiSpring",
        Distance = 52, -- Studs from the island centre
        AngleDegrees = 30, -- Direction from the centre (0 = towards +X), across from the egg
        ClearRadius = 18, -- Hills and decorations stay this far away
        WaterColor = Color3.fromRGB(110, 225, 255),
        GlowColor = Color3.fromRGB(150, 240, 255),
    },

    -- Spirit Relics on this island (rewards and names are in GameConfig.Relics).
    -- A relic either stands on the ground at AngleDegrees / Distance from the
    -- island centre, or floats at Offset from the centre of the grass surface.
    RelicColor = Color3.fromRGB(170, 235, 255),
    Relics = {
        { Id = "IslandRoot", Offset = Vector3.new(14, -78, 0) }, -- Hidden under the island
    },

    -- Decorations are placed between the platform and the island edge
    DecorationClearRadius = 30, -- Keep this area around the centre empty
    EdgeMargin = 8, -- Keep this far from the island edge
    DecorationSpacing = 9, -- Minimum distance between decorations

    Trees = {
        Count = 8,
        MinHeight = 8,
        MaxHeight = 13,
        TrunkColor = Color3.fromRGB(105, 78, 60),
        CanopyMaterial = Enum.Material.Grass,
        CanopyColors = {
            Color3.fromRGB(90, 170, 120), -- Jade
            Color3.fromRGB(240, 185, 205), -- Blossom
            Color3.fromRGB(120, 200, 190), -- Pale teal
        },
    },

    Rocks = {
        Count = 10,
        Material = Enum.Material.Rock,
        Color = Color3.fromRGB(110, 115, 130),
    },

    Crystals = {
        Count = 5, -- Clusters of 3 glowing crystals
        Colors = {
            Color3.fromRGB(120, 220, 255), -- Cyan
            Color3.fromRGB(170, 140, 255), -- Violet
            Color3.fromRGB(200, 245, 255), -- Pale blue
        },
        LightRange = 10,
    },

    FloatingFragments = {
        Count = 10,
        MinDistance = 12, -- Studs beyond the island edge
        MaxDistance = 45,
        MinHeight = -35, -- Relative to the grass surface
        MaxHeight = 20,
        RockColor = Color3.fromRGB(98, 104, 120),
        GrassColor = Color3.fromRGB(92, 156, 94),
    },

    -- Players who fall this far below the grass surface are returned to the platform
    Safety = {
        FallResetDepth = 90,
        CheckInterval = 0.25, -- Seconds between checks
    },

    -- Applied while the game runs; set Enabled = false to keep the place's own lighting
    Lighting = {
        Enabled = true,
        ClockTime = 14.5,
        Brightness = 2.2,
        Ambient = Color3.fromRGB(60, 70, 90),
        OutdoorAmbient = Color3.fromRGB(130, 140, 165),
        Atmosphere = {
            Density = 0.32,
            Offset = 0.2,
            Color = Color3.fromRGB(199, 220, 240),
            Decay = Color3.fromRGB(106, 132, 170),
            Glare = 0.15,
            Haze = 1.2,
        },
    },
}

-- Outer sky islands, reached by flying. They use the same settings as the
-- starting island; leave out a decoration (Trees, Rocks, ...) to skip it.
-- Only the starting island has a platform and training station.
IslandConfig.OuterIslands = {
    -- A forest island to the east
    {
        ModelName = "JadeGrove",
        Seed = 31,
        Center = Vector3.new(250, 225, -140),
        Radius = 46,
        GrassDepth = 5,
        SoilDepth = 6,
        UndersideDepth = 35,
        UndersideLayers = 6,
        Materials = {
            Surface = Enum.Material.LeafyGrass,
            Soil = Enum.Material.Mud,
            Underside = { Enum.Material.Rock, Enum.Material.Slate },
        },
        TerrainColors = {
            [Enum.Material.LeafyGrass] = Color3.fromRGB(70, 150, 95),
            [Enum.Material.Mud] = Color3.fromRGB(90, 70, 55),
        },
        Hills = { Count = 3, MinRadius = 8, MaxRadius = 12 },
        DecorationClearRadius = 6,
        EdgeMargin = 6,
        DecorationSpacing = 8,
        Trees = {
            Count = 12,
            MinHeight = 9,
            MaxHeight = 15,
            TrunkColor = Color3.fromRGB(95, 70, 55),
            CanopyMaterial = Enum.Material.LeafyGrass,
            CanopyColors = {
                Color3.fromRGB(60, 160, 100),
                Color3.fromRGB(90, 190, 120),
                Color3.fromRGB(45, 130, 90),
            },
        },
        Rocks = { Count = 4, Material = Enum.Material.Slate, Color = Color3.fromRGB(95, 110, 105) },
        Crystals = {
            Count = 3,
            Colors = { Color3.fromRGB(90, 230, 150), Color3.fromRGB(170, 255, 200) },
            LightRange = 10,
        },
        FloatingFragments = {
            Count = 5,
            MinDistance = 8,
            MaxDistance = 25,
            MinHeight = -20,
            MaxHeight = 15,
            RockColor = Color3.fromRGB(95, 105, 110),
            GrassColor = Color3.fromRGB(70, 150, 95),
        },
        EggStand = {
            EggId = "JadeSpiritEgg",
            ModelName = "JadeSpiritEgg",
            Distance = 24,
            AngleDegrees = 330,
            ClearRadius = 10,
            PromptDistance = 10,
            GlowColor = Color3.fromRGB(90, 230, 150),
            EggColor = Color3.fromRGB(190, 255, 210),
        },
        RelicColor = Color3.fromRGB(110, 240, 160),
        Relics = {
            { Id = "GroveHeart", AngleDegrees = 0, Distance = 0 },
            { Id = "JadeSeed", AngleDegrees = 120, Distance = 30 },
            { Id = "WhisperingSpring", AngleDegrees = 250, Distance = 28 },
        },
    },

    -- A volcanic island to the south-west, with lava pools
    {
        ModelName = "EmberPeak",
        Seed = 47,
        Center = Vector3.new(-230, 255, 170),
        Radius = 40,
        GrassDepth = 5,
        SoilDepth = 6,
        UndersideDepth = 40,
        UndersideLayers = 6,
        Materials = {
            Surface = Enum.Material.Basalt,
            Soil = Enum.Material.CrackedLava,
            Underside = { Enum.Material.Basalt, Enum.Material.Rock },
        },
        TerrainColors = {
            [Enum.Material.Basalt] = Color3.fromRGB(60, 55, 62),
            [Enum.Material.CrackedLava] = Color3.fromRGB(230, 95, 35),
        },
        Hills = { Count = 4, MinRadius = 8, MaxRadius = 14 },
        DecorationClearRadius = 6,
        EdgeMargin = 6,
        DecorationSpacing = 8,
        Rocks = { Count = 9, Material = Enum.Material.Basalt, Color = Color3.fromRGB(55, 50, 58) },
        Crystals = {
            Count = 4,
            Colors = { Color3.fromRGB(255, 120, 40), Color3.fromRGB(255, 70, 40) },
            LightRange = 10,
        },
        LavaPools = { Count = 4, MinDiameter = 5, MaxDiameter = 9, Color = Color3.fromRGB(255, 110, 30) },
        FloatingFragments = {
            Count = 4,
            MinDistance = 8,
            MaxDistance = 22,
            MinHeight = -20,
            MaxHeight = 12,
            RockColor = Color3.fromRGB(60, 55, 62),
            GrassColor = Color3.fromRGB(85, 70, 70), -- Ash
        },
        EggStand = {
            EggId = "InfernoEgg",
            ModelName = "InfernoEgg",
            Distance = 22,
            AngleDegrees = 220,
            ClearRadius = 10,
            PromptDistance = 10,
            GlowColor = Color3.fromRGB(255, 110, 40),
            EggColor = Color3.fromRGB(255, 190, 120),
        },
        RelicColor = Color3.fromRGB(255, 140, 60),
        Relics = {
            { Id = "EmberHeart", AngleDegrees = 0, Distance = 0 },
            { Id = "AshenSigil", AngleDegrees = 90, Distance = 26 },
            { Id = "CalderaCrown", Offset = Vector3.new(0, 24, 0) }, -- Floating high above the peak
        },
    },

    -- A pale celestial island, the highest and furthest
    {
        ModelName = "MoonlitIsle",
        Seed = 53,
        Center = Vector3.new(40, 320, 300),
        Radius = 32,
        GrassDepth = 4,
        SoilDepth = 5,
        UndersideDepth = 30,
        UndersideLayers = 5,
        Materials = {
            Surface = Enum.Material.Salt,
            Soil = Enum.Material.Limestone,
            Underside = { Enum.Material.Slate, Enum.Material.Rock },
        },
        TerrainColors = {
            [Enum.Material.Salt] = Color3.fromRGB(230, 232, 245),
            [Enum.Material.Limestone] = Color3.fromRGB(200, 200, 215),
        },
        Hills = { Count = 2, MinRadius = 6, MaxRadius = 10 },
        DecorationClearRadius = 6,
        EdgeMargin = 5,
        DecorationSpacing = 8,
        Trees = {
            Count = 4,
            MinHeight = 7,
            MaxHeight = 11,
            TrunkColor = Color3.fromRGB(200, 195, 215),
            CanopyMaterial = Enum.Material.SmoothPlastic,
            CanopyColors = { Color3.fromRGB(210, 190, 255), Color3.fromRGB(235, 225, 255) },
        },
        Rocks = { Count = 3, Material = Enum.Material.Marble, Color = Color3.fromRGB(220, 222, 235) },
        Crystals = {
            Count = 6,
            Colors = { Color3.fromRGB(190, 160, 255), Color3.fromRGB(150, 220, 255) },
            LightRange = 12,
        },
        FloatingFragments = {
            Count = 6,
            MinDistance = 6,
            MaxDistance = 24,
            MinHeight = -15,
            MaxHeight = 20,
            RockColor = Color3.fromRGB(180, 182, 200),
            GrassColor = Color3.fromRGB(230, 232, 245),
        },
        RelicColor = Color3.fromRGB(205, 185, 255),
        Relics = {
            { Id = "MoonMirror", AngleDegrees = 0, Distance = 0 },
            { Id = "StarWell", AngleDegrees = 180, Distance = 20 },
        },
    },
}

-- Catch config mistakes as soon as the game starts: every relic in
-- GameConfig.Relics must be placed on exactly one island, and every egg
-- stand must use an egg from GameConfig.Eggs
do
    local ReplicatedStorage = game:GetService("ReplicatedStorage")
    local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

    for _, island in { IslandConfig, table.unpack(IslandConfig.OuterIslands) } do
        if island.EggStand then
            assert(GameConfig.Eggs[island.EggStand.EggId], "IslandConfig has an egg stand with an unknown EggId: " .. tostring(island.EggStand.EggId))
        end
    end

    local placed = {}
    for _, island in { IslandConfig, table.unpack(IslandConfig.OuterIslands) } do
        for _, relic in island.Relics or {} do
            assert(not placed[relic.Id], "Relic " .. relic.Id .. " is placed more than once in IslandConfig")
            placed[relic.Id] = true
        end
    end
    for _, relic in GameConfig.Relics do
        assert(placed[relic.Id], "Relic " .. relic.Id .. " isn't placed on any island in IslandConfig")
        placed[relic.Id] = nil
    end
    assert(next(placed) == nil, "IslandConfig places a relic that isn't in GameConfig.Relics: " .. tostring(next(placed)))
end

return IslandConfig
