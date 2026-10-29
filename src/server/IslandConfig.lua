
-- Settings for the starting floating island, all in one place.
-- The island is built when the server starts (see IslandService), so changes
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

    -- Note: these recolour ALL terrain of that material in the place
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

    -- Beginner Qi Egg stand (the pet chances and cooldown are in GameConfig.BeginnerEgg)
    BeginnerEgg = {
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

return IslandConfig
