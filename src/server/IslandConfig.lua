local IslandConfig = {
    ModelName = "StartingIsland",
    Seed = 2026,
    Center = Vector3.new(0, 200, 0),

    Radius = 90,
    GrassDepth = 6,
    SoilDepth = 8,
    UndersideDepth = 55,
    UndersideLayers = 8,

    Materials = {
        Surface = Enum.Material.Grass,
        Soil = Enum.Material.Ground,
        Underside = { Enum.Material.Rock, Enum.Material.Slate },
    },

    TerrainColors = {
        [Enum.Material.Grass] = Color3.fromRGB(92, 156, 94),
        [Enum.Material.Ground] = Color3.fromRGB(112, 92, 72),
        [Enum.Material.Rock] = Color3.fromRGB(98, 104, 120),
        [Enum.Material.Slate] = Color3.fromRGB(80, 86, 104),
    },

    Hills = { Count = 4, MinRadius = 10, MaxRadius = 16 },

    Platform = {
        Diameter = 40,
        BaseMaterial = Enum.Material.Slate,
        BaseColor = Color3.fromRGB(70, 78, 95),
        FloorMaterial = Enum.Material.Marble,
        FloorColor = Color3.fromRGB(225, 228, 235),
        RingColor = Color3.fromRGB(120, 220, 255),
        LanternCount = 4,
        LanternColor = Color3.fromRGB(170, 235, 255),
    },

    EggStands = {
        { EggId = "BeginnerQiEgg", ModelName = "BeginnerQiEgg", Distance = 55, AngleDegrees = 210, ClearRadius = 16, PromptDistance = 10,
            GlowColor = Color3.fromRGB(120, 220, 255), EggColor = Color3.fromRGB(240, 248, 255) },
        { EggId = "SpiritBreezeEgg", ModelName = "SpiritBreezeEgg", Distance = 55, AngleDegrees = 175, ClearRadius = 16, PromptDistance = 10,
            GlowColor = Color3.fromRGB(150, 255, 220), EggColor = Color3.fromRGB(230, 255, 245) },
        { EggId = "ElementalCoreEgg", ModelName = "ElementalCoreEgg", Distance = 55, AngleDegrees = 245, ClearRadius = 16, PromptDistance = 10,
            GlowColor = Color3.fromRGB(180, 140, 255), EggColor = Color3.fromRGB(230, 220, 255) },
    },

    TrainingStation = {
        ModelName = "QiSpring",
        Distance = 52,
        AngleDegrees = 30,
        ClearRadius = 18,
        WaterColor = Color3.fromRGB(110, 225, 255),
        GlowColor = Color3.fromRGB(150, 240, 255),
    },

    RelicColor = Color3.fromRGB(170, 235, 255),
    Relics = {
        { Id = "IslandRoot", Offset = Vector3.new(14, -78, 0) },
    },

    DecorationClearRadius = 30,
    EdgeMargin = 8,
    DecorationSpacing = 9,

    Trees = {
        Count = 8,
        MinHeight = 8,
        MaxHeight = 13,
        TrunkColor = Color3.fromRGB(105, 78, 60),
        CanopyMaterial = Enum.Material.Grass,
        CanopyColors = {
            Color3.fromRGB(90, 170, 120),
            Color3.fromRGB(240, 185, 205),
            Color3.fromRGB(120, 200, 190),
        },
    },

    Rocks = {
        Count = 10,
        Material = Enum.Material.Rock,
        Color = Color3.fromRGB(110, 115, 130),
    },

    Crystals = {
        Count = 5,
        Colors = {
            Color3.fromRGB(120, 220, 255),
            Color3.fromRGB(170, 140, 255),
            Color3.fromRGB(200, 245, 255),
        },
        LightRange = 10,
    },

    FloatingFragments = {
        Count = 10,
        MinDistance = 12,
        MaxDistance = 45,
        MinHeight = -35,
        MaxHeight = 20,
        RockColor = Color3.fromRGB(98, 104, 120),
        GrassColor = Color3.fromRGB(92, 156, 94),
    },

    Safety = {
        FallResetDepth = 90,
        CheckInterval = 0.25,
    },

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

IslandConfig.OuterIslands = {
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
        EggStands = {
        { EggId = "JadeSpiritEgg", ModelName = "JadeSpiritEgg", Distance = 24, AngleDegrees = 330, ClearRadius = 10, PromptDistance = 10,
            GlowColor = Color3.fromRGB(90, 230, 150), EggColor = Color3.fromRGB(190, 255, 210) },
        { EggId = "BloomwoodEgg", ModelName = "BloomwoodEgg", Distance = 24, AngleDegrees = 30, ClearRadius = 10, PromptDistance = 10,
            GlowColor = Color3.fromRGB(255, 170, 230), EggColor = Color3.fromRGB(255, 225, 245) },
        { EggId = "AncientGroveEgg", ModelName = "AncientGroveEgg", Distance = 26, AngleDegrees = 75, ClearRadius = 10, PromptDistance = 10,
            GlowColor = Color3.fromRGB(200, 255, 120), EggColor = Color3.fromRGB(225, 245, 200) },
        },
        RelicColor = Color3.fromRGB(110, 240, 160),
        Relics = {
            { Id = "GroveHeart", AngleDegrees = 0, Distance = 0 },
            { Id = "JadeSeed", AngleDegrees = 120, Distance = 30 },
            { Id = "WhisperingSpring", AngleDegrees = 250, Distance = 28 },
        },
    },

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
            GrassColor = Color3.fromRGB(85, 70, 70),
        },
        EggStands = {
        { EggId = "InfernoEgg", ModelName = "InfernoEgg", Distance = 22, AngleDegrees = 220, ClearRadius = 10, PromptDistance = 10,
            GlowColor = Color3.fromRGB(255, 110, 40), EggColor = Color3.fromRGB(255, 190, 120) },
        { EggId = "MagmaHeartEgg", ModelName = "MagmaHeartEgg", Distance = 22, AngleDegrees = 160, ClearRadius = 10, PromptDistance = 10,
            GlowColor = Color3.fromRGB(255, 170, 60), EggColor = Color3.fromRGB(255, 215, 150) },
        { EggId = "PhoenixAshEgg", ModelName = "PhoenixAshEgg", Distance = 22, AngleDegrees = 280, ClearRadius = 10, PromptDistance = 10,
            GlowColor = Color3.fromRGB(255, 80, 120), EggColor = Color3.fromRGB(255, 180, 190) },
        },
        RelicColor = Color3.fromRGB(255, 140, 60),
        Relics = {
            { Id = "EmberHeart", AngleDegrees = 0, Distance = 0 },
            { Id = "AshenSigil", AngleDegrees = 90, Distance = 26 },
            { Id = "CalderaCrown", Offset = Vector3.new(0, 24, 0) },
        },
    },

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
        EggStands = {
        { EggId = "CelestialEgg", ModelName = "CelestialEgg", Distance = 19, AngleDegrees = 0, ClearRadius = 8, PromptDistance = 10,
            GlowColor = Color3.fromRGB(150, 200, 255), EggColor = Color3.fromRGB(240, 245, 255) },
        { EggId = "AstralSanctumEgg", ModelName = "AstralSanctumEgg", Distance = 18, AngleDegrees = 60, ClearRadius = 8, PromptDistance = 10,
            GlowColor = Color3.fromRGB(190, 150, 255), EggColor = Color3.fromRGB(235, 225, 255) },
        { EggId = "HeavenlyThroneEgg", ModelName = "HeavenlyThroneEgg", Distance = 18, AngleDegrees = 300, ClearRadius = 8, PromptDistance = 10,
            GlowColor = Color3.fromRGB(255, 215, 120), EggColor = Color3.fromRGB(255, 248, 225) },
        },
        RelicColor = Color3.fromRGB(205, 185, 255),
        Relics = {
            { Id = "MoonMirror", AngleDegrees = 0, Distance = 0 },
            { Id = "StarWell", AngleDegrees = 180, Distance = 20 },
        },
    },

    {
        ModelName = "OriginAbyss",
        Seed = 71,
        Center = Vector3.new(-420, 150, -430),
        Radius = 42,
        GrassDepth = 5,
        SoilDepth = 6,
        UndersideDepth = 45,
        UndersideLayers = 7,
        Materials = {
            Surface = Enum.Material.Slate,
            Soil = Enum.Material.CrackedLava,
            Underside = { Enum.Material.Basalt, Enum.Material.Rock },
        },
        TerrainColors = {
            [Enum.Material.Slate] = Color3.fromRGB(48, 38, 66),
            [Enum.Material.CrackedLava] = Color3.fromRGB(150, 70, 255),
        },
        Hills = { Count = 3, MinRadius = 8, MaxRadius = 13 },
        DecorationClearRadius = 6,
        EdgeMargin = 6,
        DecorationSpacing = 8,
        Rocks = { Count = 10, Material = Enum.Material.Basalt, Color = Color3.fromRGB(40, 34, 55) },
        Crystals = {
            Count = 8,
            Colors = { Color3.fromRGB(170, 90, 255), Color3.fromRGB(255, 90, 210), Color3.fromRGB(120, 70, 255) },
            LightRange = 14,
        },
        LavaPools = { Count = 3, MinDiameter = 5, MaxDiameter = 8, Color = Color3.fromRGB(140, 60, 255) },
        FloatingFragments = {
            Count = 9,
            MinDistance = 10,
            MaxDistance = 32,
            MinHeight = -25,
            MaxHeight = 22,
            RockColor = Color3.fromRGB(45, 40, 60),
            GrassColor = Color3.fromRGB(70, 50, 100),
        },
        EggStands = {
        { EggId = "ForbiddenOriginEgg", ModelName = "ForbiddenOriginEgg", Distance = 22, AngleDegrees = 30, ClearRadius = 10, PromptDistance = 10,
            GlowColor = Color3.fromRGB(180, 90, 255), EggColor = Color3.fromRGB(70, 50, 110) },
        { EggId = "VoidRiftEgg", ModelName = "VoidRiftEgg", Distance = 22, AngleDegrees = 150, ClearRadius = 10, PromptDistance = 10,
            GlowColor = Color3.fromRGB(120, 70, 255), EggColor = Color3.fromRGB(50, 40, 90) },
        { EggId = "PrimordialAbyssEgg", ModelName = "PrimordialAbyssEgg", Distance = 22, AngleDegrees = 270, ClearRadius = 10, PromptDistance = 10,
            GlowColor = Color3.fromRGB(255, 90, 200), EggColor = Color3.fromRGB(80, 40, 90) },
        },
        RelicColor = Color3.fromRGB(190, 120, 255),
        Relics = {
            { Id = "OriginAltar", AngleDegrees = 0, Distance = 0 },
            { Id = "VoidShard", Offset = Vector3.new(0, 28, 0) },
        },
    },
}

do
    local ReplicatedStorage = game:GetService("ReplicatedStorage")
    local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

    local standCount = {}
    for _, island in { IslandConfig, table.unpack(IslandConfig.OuterIslands) } do
        for _, stand in island.EggStands or {} do
            assert(GameConfig.Eggs[stand.EggId], "IslandConfig has an egg stand with an unknown EggId: " .. tostring(stand.EggId))
            standCount[stand.EggId] = (standCount[stand.EggId] or 0) + 1
        end
    end
    for eggId in GameConfig.Eggs do
        assert(standCount[eggId] == 1, "Egg " .. eggId .. " must stand on exactly one island in IslandConfig")
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
