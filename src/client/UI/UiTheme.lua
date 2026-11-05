-- The interface's look, in one place: the owner's reference (2026-11-04), "something like this UI but not
-- too much". Deep navy panels with a touch of indigo, fine gold trim, a small cloud-scroll ornament on the
-- corners of the main panels (tools/ui/draw_frame.py), gold for what matters. Before this it was a cyan
-- holographic System window; the owner has also said strong colours are too much, so the panels stay blue.
-- English only: no Chinese text anywhere (the owner: players might not play a game with text they can't read).
local UiTheme = {}

UiTheme.Colors = {
    Panel = Color3.fromRGB(24, 25, 68),        -- window glass, deepening toward its bottom
    Raised = Color3.fromRGB(34, 33, 84),       -- rows, quiet buttons
    Well = Color3.fromRGB(8, 9, 26),           -- bar tracks, wells
    Edge = Color3.fromRGB(226, 182, 92),       -- the gold trim
    EdgeDim = Color3.fromRGB(128, 102, 62),    -- quiet frames, separators
    Accent = Color3.fromRGB(236, 190, 90),     -- primary actions, progress
    AccentBright = Color3.fromRGB(255, 238, 196),
    AccentDeep = Color3.fromRGB(46, 42, 96),
    AccentFill = Color3.fromRGB(255, 200, 76),  -- a primary button: the one lit thing on the screen
    Highlight = Color3.fromRGB(255, 216, 104), -- a breakthrough, a reward, the rank
    Danger = Color3.fromRGB(255, 76, 92),      -- guardians, refusals, close
    DangerDeep = Color3.fromRGB(96, 18, 32),
    Text = Color3.fromRGB(246, 245, 255),
    Muted = Color3.fromRGB(172, 170, 204),
    Sky = Color3.fromRGB(150, 226, 255),       -- Qi, Qinggong
}

local FAMILY = "rbxasset://fonts/families/"
UiTheme.Fonts = {
    Header = Font.new(FAMILY .. "Merriweather.json", Enum.FontWeight.Bold),     -- a window's name
    Title = Font.new(FAMILY .. "Merriweather.json", Enum.FontWeight.Bold),      -- a rank, a quest, a button's word
    Body = Font.new(FAMILY .. "Montserrat.json", Enum.FontWeight.Medium),
    Strong = Font.new(FAMILY .. "Montserrat.json", Enum.FontWeight.SemiBold),
    Number = Font.new(FAMILY .. "Montserrat.json", Enum.FontWeight.ExtraBold),
}

UiTheme.PanelTransparency = 0.14 -- nearly solid, so gold trim has something to sit on
UiTheme.Corner = 6
UiTheme.Ornaments = {
    Corner = "rbxassetid://102166566602424",
    EmblemRing = "rbxassetid://80453677548549",
    LotusSit = "rbxassetid://107582762075601",
}
UiTheme.Margin = 16 -- from the screen's edges

-- The icons: original full-colour pictures (tools/ui/draw_icons.py, assets/ui/icons; ids in icons.json),
-- shown untinted. No text in any language on an icon.
UiTheme.Icons = {
    Qi = "rbxassetid://92441554457364", -- a flame of energy
    Stones = "rbxassetid://115509307959601",    -- a faceted crystal
    Relics = "rbxassetid://120244333350364",     -- a jade disc on its cord
    Pets = "rbxassetid://86159942849787", -- a spirit fox
    Robes = "rbxassetid://74536498666359", -- a crossed-collar robe
    Qinggong = "rbxassetid://115713809878403", -- a diving swallow
    Guardian = "rbxassetid://87780403658411",  -- a shield with a beast's eye
    Hatch = "rbxassetid://93316116947603",      -- a cracked egg
    Shop = "rbxassetid://86121773247188", -- the Jade Scale
    Forge = "rbxassetid://83033475878685",      -- hammer and anvil
    Quest = "rbxassetid://95203744242297", -- an open scroll with a seal
    Settings = "rbxassetid://92494124873013", -- a dial of lotus petals
    Rewards = "rbxassetid://119590867507093", -- a gold ingot
    Codex = "rbxassetid://77528485832233", -- an open book with a spirit's paw print
    Lock = "rbxassetid://125417292249654", -- a gold padlock
}

-- Each egg's own picture, rendered from its 3D model (tools/blender/eggs/egg_icons.py, assets/ui/egg_icons)
UiTheme.EggIcons = {
    BeginnerQiEgg = "rbxassetid://86682261572454",
    SpiritBreezeEgg = "rbxassetid://112511972816824",
    ElementalCoreEgg = "rbxassetid://135075297738440",
    JadeSpiritEgg = "rbxassetid://96694671316411",
    BloomwoodEgg = "rbxassetid://79336251483623",
    AncientGroveEgg = "rbxassetid://75738751594004",
    InfernoEgg = "rbxassetid://108740860286668",
    MagmaHeartEgg = "rbxassetid://129796553236238",
    PhoenixAshEgg = "rbxassetid://94315862454453",
    CelestialEgg = "rbxassetid://75652751925897",
    AstralSanctumEgg = "rbxassetid://87088082474707",
    HeavenlyThroneEgg = "rbxassetid://113532133031751",
    ForbiddenOriginEgg = "rbxassetid://124252731616068",
    VoidRiftEgg = "rbxassetid://83814889914054",
    PrimordialAbyssEgg = "rbxassetid://99719486622834",
}

return UiTheme
