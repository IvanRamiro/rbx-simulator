-- The owner's AuraConfig (pasted 2026-11-03): each realm's name, colours and light.
-- RealmAura (src/client/Auras) builds every realm's aura from it, in the game and the test range.
-- The colours are the owner's set of 2026-11-11 (no two realms alike: "Don't repeat same color to
-- aura"). Palette: Hot as a particle is born, Main, Deep as it fades; Glow scales the base aura's
-- brightness (pale and gold colours bloom to white sooner). Color runs Hot to Main (Eternal: its
-- three hues), BeamColor sits between them.
local AuraConfig = {}

AuraConfig.Tiers = {
    [1] = { -- Qi Awakening (x1)
        Name = "Qi Awakening",
        ParticleRate = 15,
        SizeRange = NumberRange.new(1.0, 1.8),
        SpeedRange = NumberRange.new(1, 3),
        Color = ColorSequence.new(Color3.fromRGB(175, 255, 175), Color3.fromRGB(40, 215, 95)), -- jade green
        LightEmission = 0.2,
        HasBeams = false,
        BeamColor = Color3.fromRGB(94, 231, 127),
        Palette = { Hot = Color3.fromRGB(175, 255, 175), Main = Color3.fromRGB(40, 215, 95), Deep = Color3.fromRGB(10, 105, 45), Glow = 1 },
    },
    [2] = { -- Qi Foundation (x1)
        Name = "Qi Foundation",
        ParticleRate = 20,
        SizeRange = NumberRange.new(1.2, 2.2),
        SpeedRange = NumberRange.new(1.5, 3.5),
        Color = ColorSequence.new(Color3.fromRGB(150, 255, 240), Color3.fromRGB(20, 200, 180)), -- teal
        LightEmission = 0.3,
        HasBeams = false,
        BeamColor = Color3.fromRGB(72, 222, 204),
        Palette = { Hot = Color3.fromRGB(150, 255, 240), Main = Color3.fromRGB(20, 200, 180), Deep = Color3.fromRGB(0, 95, 100), Glow = 1 },
    },
    [3] = { -- Spirit Core (x1)
        Name = "Spirit Core",
        ParticleRate = 30,
        SizeRange = NumberRange.new(1.5, 2.8),
        SpeedRange = NumberRange.new(2, 4),
        Color = ColorSequence.new(Color3.fromRGB(255, 235, 140), Color3.fromRGB(255, 185, 20)), -- gold
        LightEmission = 0.6,
        HasBeams = true,
        BeamColor = Color3.fromRGB(255, 205, 68),
        Palette = { Hot = Color3.fromRGB(255, 235, 140), Main = Color3.fromRGB(255, 185, 20), Deep = Color3.fromRGB(165, 95, 0), Glow = 0.8 },
    },
    [4] = { -- Spirit Soul (x2)
        Name = "Spirit Soul",
        ParticleRate = 45,
        SizeRange = NumberRange.new(1.8, 3.2),
        SpeedRange = NumberRange.new(2.5, 5),
        Color = ColorSequence.new(Color3.fromRGB(165, 195, 255), Color3.fromRGB(60, 100, 255)), -- royal blue
        LightEmission = 0.7,
        HasBeams = true,
        BeamColor = Color3.fromRGB(102, 138, 255),
        Palette = { Hot = Color3.fromRGB(165, 195, 255), Main = Color3.fromRGB(60, 100, 255), Deep = Color3.fromRGB(20, 25, 140), Glow = 1 },
    },
    [5] = { -- Ascendant Realm (x4)
        Name = "Ascendant Realm",
        ParticleRate = 60,
        SizeRange = NumberRange.new(2.2, 4.0),
        SpeedRange = NumberRange.new(3, 6),
        Color = ColorSequence.new(Color3.fromRGB(255, 190, 110), Color3.fromRGB(255, 125, 40)), -- solar orange
        LightEmission = 0.8,
        HasBeams = true,
        BeamColor = Color3.fromRGB(255, 151, 68),
        Palette = { Hot = Color3.fromRGB(255, 190, 110), Main = Color3.fromRGB(255, 125, 40), Deep = Color3.fromRGB(190, 45, 10), Glow = 1 },
    },
    [6] = { -- Immortal Realm (x8)
        Name = "Immortal Realm",
        ParticleRate = 85,
        SizeRange = NumberRange.new(2.5, 4.8),
        SpeedRange = NumberRange.new(3.5, 7),
        Color = ColorSequence.new(Color3.fromRGB(255, 255, 255), Color3.fromRGB(210, 222, 245)), -- silver-white
        LightEmission = 0.9,
        HasBeams = true,
        BeamColor = Color3.fromRGB(228, 235, 249),
        Palette = { Hot = Color3.fromRGB(255, 255, 255), Main = Color3.fromRGB(210, 222, 245), Deep = Color3.fromRGB(110, 125, 165), Glow = 0.5 },
    },
    [7] = { -- Divine Realm (x16)
        Name = "Divine Realm",
        ParticleRate = 120,
        SizeRange = NumberRange.new(3.0, 5.5),
        SpeedRange = NumberRange.new(4, 8),
        Color = ColorSequence.new(Color3.fromRGB(255, 110, 90), Color3.fromRGB(225, 20, 45)), -- crimson
        LightEmission = 1.0,
        HasBeams = true,
        BeamColor = Color3.fromRGB(237, 56, 63),
        Palette = { Hot = Color3.fromRGB(255, 110, 90), Main = Color3.fromRGB(225, 20, 45), Deep = Color3.fromRGB(115, 0, 20), Glow = 1 },
    },
    [8] = { -- Cosmic Realm (x32)
        Name = "Cosmic Realm",
        ParticleRate = 160,
        SizeRange = NumberRange.new(3.5, 6.5),
        SpeedRange = NumberRange.new(4.5, 9),
        Color = ColorSequence.new(Color3.fromRGB(215, 170, 255), Color3.fromRGB(145, 60, 235)), -- violet
        LightEmission = 0.9,
        HasBeams = true,
        BeamColor = Color3.fromRGB(173, 104, 243),
        Palette = { Hot = Color3.fromRGB(215, 170, 255), Main = Color3.fromRGB(145, 60, 235), Deep = Color3.fromRGB(55, 15, 115), Glow = 1 },
    },
    [9] = { -- Void Realm (x64)
        Name = "Void Realm",
        ParticleRate = 210,
        SizeRange = NumberRange.new(4.0, 7.5),
        SpeedRange = NumberRange.new(5, 10),
        Color = ColorSequence.new(Color3.fromRGB(150, 210, 255), Color3.fromRGB(120, 200, 240)), -- black core, ice-blue rim
        LightEmission = -0.5, -- Dark void absorption effect
        HasBeams = true,
        BeamColor = Color3.fromRGB(132, 204, 246),
        Palette = { Hot = Color3.fromRGB(150, 210, 255), Main = Color3.fromRGB(120, 200, 240), Deep = Color3.fromRGB(6, 8, 20), Glow = 0.6 },
    },
    [10] = { -- Heavenly Dao (x128)
        Name = "Heavenly Dao",
        ParticleRate = 280,
        SizeRange = NumberRange.new(4.5, 8.5),
        SpeedRange = NumberRange.new(6, 11),
        Color = ColorSequence.new(Color3.fromRGB(255, 195, 228), Color3.fromRGB(255, 85, 170)), -- rose pink
        LightEmission = 1.0,
        HasBeams = true,
        BeamColor = Color3.fromRGB(255, 129, 193),
        Palette = { Hot = Color3.fromRGB(255, 195, 228), Main = Color3.fromRGB(255, 85, 170), Deep = Color3.fromRGB(145, 20, 90), Glow = 0.8 },
    },
    [11] = { -- Primordial Realm (x256)
        Name = "Primordial Realm",
        ParticleRate = 360,
        SizeRange = NumberRange.new(5.2, 9.8),
        SpeedRange = NumberRange.new(7, 13),
        Color = ColorSequence.new(Color3.fromRGB(255, 140, 30), Color3.fromRGB(185, 35, 5)), -- lava: amber to dark ember
        LightEmission = 1.2,
        HasBeams = true,
        BeamColor = Color3.fromRGB(213, 77, 15),
        Palette = { Hot = Color3.fromRGB(255, 140, 30), Main = Color3.fromRGB(185, 35, 5), Deep = Color3.fromRGB(55, 5, 0), Glow = 0.75 },
    },
    [12] = { -- Eternal Transcendence (x512)
        Name = "Eternal Transcendence",
        ParticleRate = 500,
        SizeRange = NumberRange.new(6.0, 12.0),
        SpeedRange = NumberRange.new(8, 15),
        Color = ColorSequence.new({
            ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 215, 90)),
            ColorSequenceKeypoint.new(0.5, Color3.fromRGB(90, 215, 255)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(215, 70, 255)),
        }), -- prismatic: gold, cyan, magenta
        LightEmission = 1.5,
        HasBeams = true,
        BeamColor = Color3.fromRGB(190, 235, 255),
        Palette = { Hot = Color3.fromRGB(255, 215, 90), Main = Color3.fromRGB(90, 215, 255), Deep = Color3.fromRGB(215, 70, 255), Glow = 0.45 },
    }
}

return AuraConfig
