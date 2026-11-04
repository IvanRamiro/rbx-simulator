-- The interface's look, in one place: the cultivator's System, a holographic status interface
-- that the Heavenly Dao shows only to them (the owner: "make it more like a game system status from
-- solo leveling"; an original take on that genre, nothing copied). Translucent deep-blue windows
-- with a glowing cyan edge and corner ticks, bracketed headers ("STATUS", "NOTIFICATION"), crisp
-- white sans-serif text, and outlined icon boxes. English only: no Chinese text anywhere (the
-- owner: players might not play a game with text they can't read).
local UiTheme = {}

UiTheme.Colors = {
    Panel = Color3.fromRGB(6, 16, 34),         -- window glass
    Raised = Color3.fromRGB(14, 34, 64),       -- rows, quiet buttons
    Well = Color3.fromRGB(2, 7, 16),           -- bar tracks, wells
    Edge = Color3.fromRGB(96, 196, 255),       -- the glowing frame
    EdgeDim = Color3.fromRGB(46, 102, 150),    -- quiet frames, separators
    Accent = Color3.fromRGB(88, 200, 255),     -- Qi, primary actions, progress
    AccentBright = Color3.fromRGB(205, 240, 255),
    AccentDeep = Color3.fromRGB(16, 64, 112),
    Highlight = Color3.fromRGB(255, 214, 102), -- a breakthrough, a reward, the rank
    Danger = Color3.fromRGB(255, 76, 92),      -- guardians, refusals, close
    DangerDeep = Color3.fromRGB(96, 18, 32),
    Text = Color3.fromRGB(236, 246, 255),
    Muted = Color3.fromRGB(132, 166, 198),
    Sky = Color3.fromRGB(150, 226, 255),       -- Qinggong
}

local FAMILY = "rbxasset://fonts/families/"
UiTheme.Fonts = {
    Header = Font.new(FAMILY .. "Michroma.json"),                               -- wide, technical: STATUS
    Title = Font.new(FAMILY .. "Montserrat.json", Enum.FontWeight.Bold),
    Body = Font.new(FAMILY .. "Montserrat.json", Enum.FontWeight.Medium),
    Strong = Font.new(FAMILY .. "Montserrat.json", Enum.FontWeight.SemiBold),
    Number = Font.new(FAMILY .. "Montserrat.json", Enum.FontWeight.ExtraBold),
}

UiTheme.PanelTransparency = 0.3 -- glass: the world shows through
UiTheme.Corner = 2 -- sharp, like a projected window
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
