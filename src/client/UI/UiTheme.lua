-- The interface's look, in one place: a cultivation sect's lacquer and seal work. Dark ink-lacquer
-- panels framed by a gold hairline, jade for Qi and for what the player can do, cinnabar seal
-- stamps for icons and warnings, parchment for text. Titles in a heavy classical serif
-- (Merriweather), numbers and body in Montserrat; seals carry a Chinese character (the CJK
-- fallback font) so each one reads as a stamp, with its English word beside it.
local UiTheme = {}

UiTheme.Colors = {
    Ink = Color3.fromRGB(15, 19, 20),          -- panels
    InkRaised = Color3.fromRGB(28, 34, 34),    -- rows, quiet buttons
    InkDeep = Color3.fromRGB(7, 9, 10),        -- bar tracks, wells
    Gold = Color3.fromRGB(214, 178, 108),      -- hairlines, titles, rank
    GoldDim = Color3.fromRGB(118, 98, 62),     -- quiet hairlines
    Jade = Color3.fromRGB(86, 206, 164),       -- Qi, primary actions, progress
    JadeBright = Color3.fromRGB(170, 246, 214),
    JadeDeep = Color3.fromRGB(22, 86, 68),
    Cinnabar = Color3.fromRGB(196, 58, 44),    -- seals, close, refusals
    CinnabarDeep = Color3.fromRGB(112, 28, 22),
    Parchment = Color3.fromRGB(240, 232, 212), -- text
    Mist = Color3.fromRGB(150, 156, 148),      -- secondary text
    Sky = Color3.fromRGB(150, 214, 255),       -- Qinggong, flight
}

local FAMILY = "rbxasset://fonts/families/"
UiTheme.Fonts = {
    Title = Font.new(FAMILY .. "Merriweather.json", Enum.FontWeight.Bold),
    Display = Font.new(FAMILY .. "Merriweather.json", Enum.FontWeight.Heavy),
    Body = Font.new(FAMILY .. "Montserrat.json", Enum.FontWeight.Medium),
    Strong = Font.new(FAMILY .. "Montserrat.json", Enum.FontWeight.Bold),
    Number = Font.new(FAMILY .. "Montserrat.json", Enum.FontWeight.ExtraBold),
    Seal = Font.new(FAMILY .. "NotoSansCJKFallback.json", Enum.FontWeight.Bold), -- one weight ships; Bold is drawn heavier, crisp
}

UiTheme.PanelTransparency = 0.1
UiTheme.Corner = 4 -- crisp lacquer edges, not bubbles
UiTheme.Margin = 16 -- from the screen's edges

-- Each HUD seal's character: what it stands for, at a glance
UiTheme.Seals = {
    Qi = "气",        -- qi
    Stones = "灵",    -- spirit (stones)
    Relics = "宝",    -- treasure
    Pets = "兽",      -- beast
    Robes = "衣",     -- robe
    Qinggong = "轻",  -- light (body)
    Hatch = "孵",     -- hatch
    Shop = "市",      -- market
    Forge = "炉",     -- furnace
    Guardian = "守",  -- guard
}

return UiTheme
