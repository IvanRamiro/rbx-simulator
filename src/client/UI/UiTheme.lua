-- The interface's look, in one place: bright and colourful (the owner, 2026-11-04: "use a colorful
-- UI/UX, because I don't think the player will enjoy looking at the current design"). Rounded panels
-- filled with a saturated gradient, a light edge, a chunky friendly font, and each part of the game
-- in its own colour (UiTheme.Hues), so a player knows where they are at a glance. English only: no
-- Chinese text anywhere (the owner: players might not play a game with text they can't read).
local UiTheme = {}

UiTheme.Colors = {
    Panel = Color3.fromRGB(58, 32, 130),       -- the deep colour dark text and badges use
    Well = Color3.fromRGB(26, 14, 66),         -- bar tracks, wells, text fields
    Edge = Color3.fromRGB(255, 255, 255),      -- light edges
    EdgeDim = Color3.fromRGB(190, 170, 245),   -- quiet edges, separators
    Accent = Color3.fromRGB(64, 200, 255),     -- Qi, progress
    AccentBright = Color3.fromRGB(190, 240, 255),
    Highlight = Color3.fromRGB(255, 214, 70),  -- a breakthrough, a reward, the rank
    Danger = Color3.fromRGB(255, 84, 120),     -- guardians, refusals
    Text = Color3.fromRGB(255, 255, 255),
    Muted = Color3.fromRGB(232, 226, 255),
    Sky = Color3.fromRGB(120, 235, 255),       -- Qinggong
    TextShadow = Color3.fromRGB(20, 10, 50),   -- the dark line round every word, for any background
}

-- Each part of the game's colour: its gradient, top and bottom, and its light edge
UiTheme.Hues = {
    Violet = { Top = Color3.fromRGB(122, 72, 235), Bottom = Color3.fromRGB(66, 34, 160), Edge = Color3.fromRGB(210, 185, 255) },
    Blue = { Top = Color3.fromRGB(46, 130, 245), Bottom = Color3.fromRGB(24, 62, 170), Edge = Color3.fromRGB(160, 215, 255) },
    Teal = { Top = Color3.fromRGB(18, 178, 170), Bottom = Color3.fromRGB(8, 88, 118), Edge = Color3.fromRGB(160, 250, 235) },
    Green = { Top = Color3.fromRGB(46, 190, 104), Bottom = Color3.fromRGB(12, 106, 86), Edge = Color3.fromRGB(190, 255, 195) },
    Gold = { Top = Color3.fromRGB(236, 148, 24), Bottom = Color3.fromRGB(170, 70, 18), Edge = Color3.fromRGB(255, 232, 140) },
    Orange = { Top = Color3.fromRGB(245, 108, 44), Bottom = Color3.fromRGB(176, 44, 44), Edge = Color3.fromRGB(255, 212, 160) },
    Rose = { Top = Color3.fromRGB(240, 66, 150), Bottom = Color3.fromRGB(140, 24, 120), Edge = Color3.fromRGB(255, 185, 225) },
    Crimson = { Top = Color3.fromRGB(226, 52, 66), Bottom = Color3.fromRGB(120, 18, 62), Edge = Color3.fromRGB(255, 175, 175) },
}

local FAMILY = "rbxasset://fonts/families/"
UiTheme.Fonts = {
    Header = Font.new(FAMILY .. "FredokaOne.json"),                           -- STATUS, window titles
    Title = Font.new(FAMILY .. "FredokaOne.json"),
    Body = Font.new(FAMILY .. "Nunito.json", Enum.FontWeight.Bold),
    Strong = Font.new(FAMILY .. "Nunito.json", Enum.FontWeight.ExtraBold),
    Number = Font.new(FAMILY .. "FredokaOne.json"),
}

UiTheme.PanelTransparency = 0.06
UiTheme.Corner = 12
UiTheme.Margin = 16 -- from the screen's edges

-- The icons: original line drawings (tools/ui/draw_icons.py, assets/ui/icons; ids in icons.json),
-- white so the theme tints them. No text in any language on an icon.
UiTheme.Icons = {
    Qi = "rbxassetid://101372292588368", -- a rising spiral of energy
    Stones = "rbxassetid://126443684238250",    -- a faceted crystal
    Relics = "rbxassetid://86125750007333",     -- an ancient disc on its cord
    Pets = "rbxassetid://71615077567902", -- a spirit fox
    Robes = "rbxassetid://85355853714545", -- a crossed-collar robe
    Qinggong = "rbxassetid://106266801510792", -- a diving swallow
    Guardian = "rbxassetid://132576192303921",  -- a shield with a beast's eye
    Hatch = "rbxassetid://83100764073187",      -- a cracked egg
    Shop = "rbxassetid://80005118445258", -- the Jade Scale
    Forge = "rbxassetid://84883537666325",      -- hammer and anvil
    Settings = "rbxassetid://102443682370509", -- a lotus dial
    Rewards = "rbxassetid://96373560583865", -- a gold ingot
}

return UiTheme
