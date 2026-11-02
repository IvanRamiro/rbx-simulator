-- The HUD's one screen and its regions. Every controller puts its pieces into a region, in its
-- LayoutOrder, instead of placing them by pixel, so they line up and never overlap:
--   Status   top left: the cultivator's plaque (Qi, rank, progress), then the resource chips
--   Rail     left, centred: the menu seals (Pets, Robes ...)
--   Dock     bottom centre, bottom up: Cultivate, the breakthrough, the Qinggong strip
--   Banner   top centre: messages (Toast)
-- Windows (the pets list, the altar, the shops) open in their own ScreenGuis.
-- Each region scales with the screen (HudScale). The first script to require this builds it.
local Players = game:GetService("Players")

local UiKit = require(script.Parent:WaitForChild("UiKit"))
local UiTheme = require(script.Parent:WaitForChild("UiTheme"))
local applyHudScale = require(script.Parent:WaitForChild("HudScale"))

local playerGui = Players.LocalPlayer:WaitForChild("PlayerGui")
local M = UiTheme.Margin

local Hud = {}

local old = playerGui:FindFirstChild("Hud")
if old then
    old:Destroy()
end
local gui = Instance.new("ScreenGui")
gui.Name = "Hud"
gui.ResetOnSpawn = false
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
gui.Parent = playerGui
Hud.Gui = gui

local function region(name, anchor, position, direction, horizontal, vertical, gap)
    local frame = Instance.new("Frame")
    frame.Name = name
    frame.BackgroundTransparency = 1
    frame.AnchorPoint = anchor
    frame.Position = position
    frame.AutomaticSize = Enum.AutomaticSize.XY
    frame.Size = UDim2.new()
    frame.Parent = gui
    UiKit.list(frame, {
        FillDirection = direction, HorizontalAlignment = horizontal, VerticalAlignment = vertical,
        Padding = UDim.new(0, gap),
    })
    applyHudScale(frame)
    return frame
end

Hud.Status = region("Status", Vector2.new(0, 0), UDim2.fromOffset(M, M), Enum.FillDirection.Vertical,
    Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Top, 8)
Hud.Rail = region("Rail", Vector2.new(0, 0.5), UDim2.new(0, M, 0.5, 0), Enum.FillDirection.Vertical,
    Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center, 10)
Hud.Dock = region("Dock", Vector2.new(0.5, 1), UDim2.new(0.5, 0, 1, -M), Enum.FillDirection.Vertical,
    Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Bottom, 8)
Hud.Banner = region("Banner", Vector2.new(0.5, 0), UDim2.new(0.5, 0, 0, M), Enum.FillDirection.Vertical,
    Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Top, 6)

-- A row in the Status region for the small resource chips (Spirit Stones, Relics ...)
local chips = Instance.new("Frame")
chips.Name = "Chips"
chips.BackgroundTransparency = 1
chips.AutomaticSize = Enum.AutomaticSize.XY
chips.Size = UDim2.new()
chips.LayoutOrder = 10
chips.Parent = Hud.Status
UiKit.list(chips, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), VerticalAlignment = Enum.VerticalAlignment.Center })
Hud.Chips = chips

-- A resource chip: its seal and a value. Returns the chip and its value label.
function Hud.chip(name, glyph, order)
    local chip = UiKit.panel({
        Name = name, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 34),
        LayoutOrder = order, Brackets = false, Parent = chips,
    })
    UiKit.padding(chip, 5, 5)
    UiKit.list(chip, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), VerticalAlignment = Enum.VerticalAlignment.Center })
    UiKit.seal(glyph, 24).Parent = chip
    local value = UiKit.label({
        Name = "Value", Font = "Strong", TextSize = 16, AutomaticSize = Enum.AutomaticSize.X,
        Size = UDim2.fromOffset(0, 24), LayoutOrder = 2, Parent = chip,
    })
    local pad = Instance.new("UIPadding")
    pad.PaddingRight = UDim.new(0, 6)
    pad.Parent = value
    return chip, value
end

-- A menu seal on the rail: the seal over its word, with an optional badge (a count, or a dot).
-- Returns the button and a function that sets the badge text (nil hides it).
function Hud.railButton(name, glyph, word, order)
    local button = UiKit.button({
        Name = name, Text = "", Size = UDim2.fromOffset(64, 70), LayoutOrder = order, Tone = "Quiet",
        Parent = Hud.Rail,
    })
    local seal = UiKit.seal(glyph, 34)
    seal.AnchorPoint = Vector2.new(0.5, 0)
    seal.Position = UDim2.new(0.5, 0, 0, 8)
    seal.Parent = button
    UiKit.label({
        Name = "Word", Font = "Strong", Text = word, TextSize = 12, TextColor3 = UiTheme.Colors.Parchment,
        AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -5), Size = UDim2.new(1, 0, 0, 14),
        TextXAlignment = Enum.TextXAlignment.Center, Parent = button,
    })
    local badge = UiKit.label({
        Name = "Badge", Font = "Strong", TextSize = 11, TextColor3 = UiTheme.Colors.Ink,
        BackgroundTransparency = 0, BackgroundColor3 = UiTheme.Colors.Jade,
        AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 6, 0, -6), Size = UDim2.fromOffset(0, 18),
        AutomaticSize = Enum.AutomaticSize.X, TextXAlignment = Enum.TextXAlignment.Center, Visible = false,
        ZIndex = 5, Parent = button,
    })
    UiKit.corner(badge, 9)
    UiKit.padding(badge, 6, 0)
    local function setBadge(text, tone)
        badge.Visible = text ~= nil
        badge.Text = text or ""
        badge.BackgroundColor3 = if tone == "Gold" then UiTheme.Colors.Gold else UiTheme.Colors.Jade
    end
    return button, setBadge
end

return Hud
