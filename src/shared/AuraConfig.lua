-- The owner's AuraConfig (pasted 2026-11-03): each realm's name and colours.
-- RealmAura (src/client/Auras) builds every realm's aura from it, in the game and the test range;
-- AuraController matches a rank's realm to its tier by Name.
-- The colours are the owner's set of 2026-11-11 (no two realms alike: "Don't repeat same color to
-- aura"). Palette: Hot as a particle is born, Main, Deep as it fades; Glow scales the base aura's
-- brightness (pale and gold colours bloom to white sooner). Color runs Hot to Main (Eternal: its
-- three hues). (The pasted rates, sizes, speeds, light emission and beam colours were never read:
-- RealmAura sets those per layer. Removed 2026-11-15.)
local AuraConfig = {}

AuraConfig.Tiers = {
    [1] = { -- Qi Awakening (x1)
        Name = "Qi Awakening",
        Color = ColorSequence.new(Color3.fromRGB(175, 255, 175), Color3.fromRGB(40, 215, 95)), -- jade green
        Palette = { Hot = Color3.fromRGB(175, 255, 175), Main = Color3.fromRGB(40, 215, 95), Deep = Color3.fromRGB(10, 105, 45), Glow = 1 },
    },
    [2] = { -- Qi Foundation (x1)
        Name = "Qi Foundation",
        Color = ColorSequence.new(Color3.fromRGB(150, 255, 240), Color3.fromRGB(20, 200, 180)), -- teal
        Palette = { Hot = Color3.fromRGB(150, 255, 240), Main = Color3.fromRGB(20, 200, 180), Deep = Color3.fromRGB(0, 95, 100), Glow = 1 },
    },
    [3] = { -- Spirit Core (x1)
        Name = "Spirit Core",
        Color = ColorSequence.new(Color3.fromRGB(255, 235, 140), Color3.fromRGB(255, 185, 20)), -- gold
        Palette = { Hot = Color3.fromRGB(255, 235, 140), Main = Color3.fromRGB(255, 185, 20), Deep = Color3.fromRGB(165, 95, 0), Glow = 0.8 },
    },
    [4] = { -- Spirit Soul (x2)
        Name = "Spirit Soul",
        Color = ColorSequence.new(Color3.fromRGB(165, 195, 255), Color3.fromRGB(60, 100, 255)), -- royal blue
        Palette = { Hot = Color3.fromRGB(165, 195, 255), Main = Color3.fromRGB(60, 100, 255), Deep = Color3.fromRGB(20, 25, 140), Glow = 1 },
    },
    [5] = { -- Ascendant Realm (x4)
        Name = "Ascendant Realm",
        Color = ColorSequence.new(Color3.fromRGB(255, 190, 110), Color3.fromRGB(255, 125, 40)), -- solar orange
        Palette = { Hot = Color3.fromRGB(255, 190, 110), Main = Color3.fromRGB(255, 125, 40), Deep = Color3.fromRGB(190, 45, 10), Glow = 1 },
    },
    [6] = { -- Immortal Realm (x8)
        Name = "Immortal Realm",
        Color = ColorSequence.new(Color3.fromRGB(255, 255, 255), Color3.fromRGB(210, 222, 245)), -- silver-white
        Palette = { Hot = Color3.fromRGB(255, 255, 255), Main = Color3.fromRGB(210, 222, 245), Deep = Color3.fromRGB(110, 125, 165), Glow = 0.5 },
    },
    [7] = { -- Divine Realm (x16)
        Name = "Divine Realm",
        Color = ColorSequence.new(Color3.fromRGB(255, 110, 90), Color3.fromRGB(225, 20, 45)), -- crimson
        Palette = { Hot = Color3.fromRGB(255, 110, 90), Main = Color3.fromRGB(225, 20, 45), Deep = Color3.fromRGB(115, 0, 20), Glow = 1 },
    },
    [8] = { -- Cosmic Realm (x32)
        Name = "Cosmic Realm",
        Color = ColorSequence.new(Color3.fromRGB(215, 170, 255), Color3.fromRGB(145, 60, 235)), -- violet
        Palette = { Hot = Color3.fromRGB(215, 170, 255), Main = Color3.fromRGB(145, 60, 235), Deep = Color3.fromRGB(55, 15, 115), Glow = 1 },
    },
    [9] = { -- Void Realm (x64)
        Name = "Void Realm",
        Color = ColorSequence.new(Color3.fromRGB(150, 210, 255), Color3.fromRGB(120, 200, 240)), -- black core, ice-blue rim
        Palette = { Hot = Color3.fromRGB(150, 210, 255), Main = Color3.fromRGB(120, 200, 240), Deep = Color3.fromRGB(6, 8, 20), Glow = 0.6 },
    },
    [10] = { -- Heavenly Dao (x128)
        Name = "Heavenly Dao",
        Color = ColorSequence.new(Color3.fromRGB(255, 195, 228), Color3.fromRGB(255, 85, 170)), -- rose pink
        Palette = { Hot = Color3.fromRGB(255, 195, 228), Main = Color3.fromRGB(255, 85, 170), Deep = Color3.fromRGB(145, 20, 90), Glow = 0.8 },
    },
    [11] = { -- Primordial Realm (x256)
        Name = "Primordial Realm",
        Color = ColorSequence.new(Color3.fromRGB(255, 140, 30), Color3.fromRGB(185, 35, 5)), -- lava: amber to dark ember
        Palette = { Hot = Color3.fromRGB(255, 140, 30), Main = Color3.fromRGB(185, 35, 5), Deep = Color3.fromRGB(55, 5, 0), Glow = 0.75 },
    },
    [12] = { -- Eternal Transcendence (x512)
        Name = "Eternal Transcendence",
        Color = ColorSequence.new({
            ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 215, 90)),
            ColorSequenceKeypoint.new(0.5, Color3.fromRGB(90, 215, 255)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(215, 70, 255)),
        }), -- prismatic: gold, cyan, magenta
        Palette = { Hot = Color3.fromRGB(255, 215, 90), Main = Color3.fromRGB(90, 215, 255), Deep = Color3.fromRGB(215, 70, 255), Glow = 0.45 },
    }
}

return AuraConfig
