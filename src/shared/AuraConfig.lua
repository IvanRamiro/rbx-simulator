-- The owner's AuraConfig (pasted 2026-11-03, unchanged): each realm's name, colours and light.
-- RealmAura (src/client/Auras) builds every realm's aura from it, in the game and the test range.
local AuraConfig = {}

AuraConfig.Tiers = {
    [1] = { -- Qi Awakening (x1)
        Name = "Qi Awakening",
        ParticleRate = 15,
        SizeRange = NumberRange.new(1.0, 1.8),
        SpeedRange = NumberRange.new(1, 3),
        Color = ColorSequence.new(Color3.fromRGB(120, 255, 120)), -- Soft Green
        LightEmission = 0.2,
        HasBeams = false,
    },
    [2] = { -- Qi Foundation (x1)
        Name = "Qi Foundation",
        ParticleRate = 20,
        SizeRange = NumberRange.new(1.2, 2.2),
        SpeedRange = NumberRange.new(1.5, 3.5),
        Color = ColorSequence.new(Color3.fromRGB(80, 220, 180)), -- Cyan-Teal
        LightEmission = 0.3,
        HasBeams = false,
    },
    [3] = { -- Spirit Core (x1)
        Name = "Spirit Core",
        ParticleRate = 30,
        SizeRange = NumberRange.new(1.5, 2.8),
        SpeedRange = NumberRange.new(2, 4),
        Color = ColorSequence.new(Color3.fromRGB(255, 215, 0)), -- Golden Core
        LightEmission = 0.6,
        HasBeams = true,
        BeamColor = Color3.fromRGB(255, 180, 50),
    },
    [4] = { -- Spirit Soul (x2)
        Name = "Spirit Soul",
        ParticleRate = 45,
        SizeRange = NumberRange.new(1.8, 3.2),
        SpeedRange = NumberRange.new(2.5, 5),
        Color = ColorSequence.new({
            ColorSequenceKeypoint.new(0, Color3.fromRGB(100, 150, 255)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 100, 255))
        }),
        LightEmission = 0.7,
        HasBeams = true,
        BeamColor = Color3.fromRGB(150, 120, 255),
    },
    [5] = { -- Ascendant Realm (x4)
        Name = "Ascendant Realm",
        ParticleRate = 60,
        SizeRange = NumberRange.new(2.2, 4.0),
        SpeedRange = NumberRange.new(3, 6),
        Color = ColorSequence.new(Color3.fromRGB(255, 140, 40)), -- Solar Flame
        LightEmission = 0.8,
        HasBeams = true,
        BeamColor = Color3.fromRGB(255, 200, 100),
    },
    [6] = { -- Immortal Realm (x8)
        Name = "Immortal Realm",
        ParticleRate = 85,
        SizeRange = NumberRange.new(2.5, 4.8),
        SpeedRange = NumberRange.new(3.5, 7),
        Color = ColorSequence.new(Color3.fromRGB(255, 255, 255)), -- Pure Celestial White/Gold
        LightEmission = 0.9,
        HasBeams = true,
        BeamColor = Color3.fromRGB(255, 240, 200),
    },
    [7] = { -- Divine Realm (x16)
        Name = "Divine Realm",
        ParticleRate = 120,
        SizeRange = NumberRange.new(3.0, 5.5),
        SpeedRange = NumberRange.new(4, 8),
        Color = ColorSequence.new({
            ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 50, 50)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(255, 215, 0))
        }),
        LightEmission = 1.0,
        HasBeams = true,
        BeamColor = Color3.fromRGB(255, 100, 50),
    },
    [8] = { -- Cosmic Realm (x32)
        Name = "Cosmic Realm",
        ParticleRate = 160,
        SizeRange = NumberRange.new(3.5, 6.5),
        SpeedRange = NumberRange.new(4.5, 9),
        Color = ColorSequence.new({
            ColorSequenceKeypoint.new(0, Color3.fromRGB(20, 10, 40)),
            ColorSequenceKeypoint.new(0.5, Color3.fromRGB(120, 40, 200)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(255, 255, 255))
        }),
        LightEmission = 0.9,
        HasBeams = true,
        BeamColor = Color3.fromRGB(140, 80, 255),
    },
    [9] = { -- Void Realm (x64)
        Name = "Void Realm",
        ParticleRate = 210,
        SizeRange = NumberRange.new(4.0, 7.5),
        SpeedRange = NumberRange.new(5, 10),
        Color = ColorSequence.new({
            ColorSequenceKeypoint.new(0, Color3.fromRGB(5, 5, 10)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(70, 130, 180))
        }),
        LightEmission = -0.5, -- Dark void absorption effect
        HasBeams = true,
        BeamColor = Color3.fromRGB(30, 30, 60),
    },
    [10] = { -- Heavenly Dao (x128)
        Name = "Heavenly Dao",
        ParticleRate = 280,
        SizeRange = NumberRange.new(4.5, 8.5),
        SpeedRange = NumberRange.new(6, 11),
        Color = ColorSequence.new(Color3.fromRGB(240, 248, 255)), -- Alice Blue / Divine Law
        LightEmission = 1.0,
        HasBeams = true,
        BeamColor = Color3.fromRGB(200, 230, 255),
    },
    [11] = { -- Primordial Realm (x256)
        Name = "Primordial Realm",
        ParticleRate = 360,
        SizeRange = NumberRange.new(5.2, 9.8),
        SpeedRange = NumberRange.new(7, 13),
        Color = ColorSequence.new({
            ColorSequenceKeypoint.new(0, Color3.fromRGB(180, 30, 30)),
            ColorSequenceKeypoint.new(0.5, Color3.fromRGB(255, 140, 0)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(255, 255, 100))
        }),
        LightEmission = 1.2,
        HasBeams = true,
        BeamColor = Color3.fromRGB(255, 120, 0),
    },
    [12] = { -- Eternal Transcendence (x512)
        Name = "Eternal Transcendence",
        ParticleRate = 500,
        SizeRange = NumberRange.new(6.0, 12.0),
        SpeedRange = NumberRange.new(8, 15),
        Color = ColorSequence.new({
            ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 255, 255)),
            ColorSequenceKeypoint.new(0.3, Color3.fromRGB(255, 215, 0)),
            ColorSequenceKeypoint.new(0.7, Color3.fromRGB(100, 200, 255)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(255, 100, 255))
        }),
        LightEmission = 1.5,
        HasBeams = true,
        BeamColor = Color3.fromRGB(255, 255, 255),
    }
}

return AuraConfig
