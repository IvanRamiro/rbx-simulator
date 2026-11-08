-- The HUD's regions, laid out from the owner's reference (2026-11-04). Every controller puts its pieces
-- into a region, in its LayoutOrder, instead of placing them by pixel, so they line up and never overlap:
--   Status    top left, one column: the player's profile, then the Rail
--   Rail      the menu down the left: Pets, Codex, Robes, Quests, Settings (on a phone, icons in a row under the profile)
--   Currency  top centre, in the row beside Roblox's own buttons: Qi, Spirit Stones, Relics, sharing one slim strip
--   TopRight  top right, in that row: small round buttons (Rewards)
--   Quest     right, under them: the current quest (QuestController)
--   Banner    top centre, under the currencies: the guardian's bar and messages (Toast)
--   Dock      bottom centre, bottom up: Cultivate, the breakthrough, the Qinggong strip
-- The touch actions stand beside Roblox's jump button, bottom right (TouchActions). Roblox's chat stays where Roblox
-- puts it, at the top. Windows (the pets list, the altar, the shops): Hud.window, one open at a time.
-- Each region scales with the screen (HudScale, HudMetrics), and text stays readable at any scale. Hud.isCompact() is true on a
-- short screen (a phone in landscape): pieces change their layout on it, following Hud.CompactChanged. The first script to require this builds it.
local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))
local UiFx = require(script.Parent:WaitForChild("UiFx"))
local UiKit = require(script.Parent:WaitForChild("UiKit"))
local UiTheme = require(script.Parent:WaitForChild("UiTheme"))
local applyHudScale = require(script.Parent:WaitForChild("HudScale"))
local HudMetrics = require(script.Parent:WaitForChild("HudMetrics"))

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

-- The row beside Roblox's own buttons: a screen of its own, since the Hud's starts below them
local oldTop = playerGui:FindFirstChild("HudTop")
if oldTop then
    oldTop:Destroy()
end
local topGui = Instance.new("ScreenGui")
topGui.Name = "HudTop"
topGui.ResetOnSpawn = false
topGui.ScreenInsets = Enum.ScreenInsets.DeviceSafeInsets
topGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
topGui.Parent = playerGui

-- Windows get their own screen, drawn over the HUD and over the touch controls (Strike, Dash ...),
-- which on a phone sit where a window opens
local oldWindows = playerGui:FindFirstChild("HudWindows")
if oldWindows then
    oldWindows:Destroy()
end
local windowGui = Instance.new("ScreenGui")
windowGui.Name = "HudWindows"
windowGui.ResetOnSpawn = false
windowGui.DisplayOrder = 20
windowGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
windowGui.Parent = playerGui

local function region(name, anchor, position, direction, horizontal, vertical, gap, parent)
    local frame = Instance.new("Frame")
    frame.Name = name
    frame.BackgroundTransparency = 1
    frame.AnchorPoint = anchor
    frame.Position = position
    frame.AutomaticSize = Enum.AutomaticSize.XY
    frame.Size = UDim2.new()
    frame.Parent = parent or gui
    UiKit.list(frame, {
        FillDirection = direction, HorizontalAlignment = horizontal, VerticalAlignment = vertical,
        Padding = UDim.new(0, gap),
    })
    applyHudScale(frame)
    return frame
end

Hud.Status = region("Status", Vector2.new(0, 0), UDim2.fromOffset(M, M), Enum.FillDirection.Vertical,
    Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Top, 8)
Hud.Dock = region("Dock", Vector2.new(0.5, 1), UDim2.new(0.5, 0, 1, -M), Enum.FillDirection.Vertical,
    Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Bottom, 8)
Hud.Banner = region("Banner", Vector2.new(0.5, 0), UDim2.new(0.5, 0, 0, M), Enum.FillDirection.Vertical,
    Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Top, 6)
Hud.Quest = region("Quest", Vector2.new(1, 0), UDim2.new(1, -M, 0, M), Enum.FillDirection.Vertical,
    Enum.HorizontalAlignment.Right, Enum.VerticalAlignment.Top, 6)
Hud.Currency = region("Currency", Vector2.new(0.5, 0), UDim2.new(0.5, 0, 0, 8), Enum.FillDirection.Horizontal,
    Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center, 8, topGui)
Hud.TopRight = region("TopRight", Vector2.new(1, 0), UDim2.new(1, -M, 0, 6), Enum.FillDirection.Horizontal,
    Enum.HorizontalAlignment.Right, Enum.VerticalAlignment.Center, 8, topGui)

-- The menu down the left, under the profile
local rail = Instance.new("Frame")
rail.Name = "Rail"
rail.BackgroundTransparency = 1
rail.AutomaticSize = Enum.AutomaticSize.XY
rail.Size = UDim2.new()
rail.LayoutOrder = 20
rail.Parent = Hud.Status
UiKit.list(rail, { FillDirection = Enum.FillDirection.Vertical, Padding = UDim.new(0, 6) })
Hud.Rail = rail

-- ---------- compact screens ----------
local compactChanged = Instance.new("BindableEvent")
Hud.CompactChanged = compactChanged.Event
local compact = nil
local function checkCompact()
    local now = HudMetrics.class() == "Phone"
    if now ~= compact then
        compact = now
        compactChanged:Fire(now)
    end
end
function Hud.isCompact()
    checkCompact()
    return compact == true
end
-- how wide the dock's bars are: narrower on a phone, where they sit over the player's character
function Hud.DockWidth()
    return if Hud.isCompact() then 190 else 240
end
HudMetrics.Changed:Connect(checkCompact)
checkCompact()

HudMetrics.keepReadable(gui)
HudMetrics.keepReadable(topGui)
HudMetrics.keepReadable(windowGui)

-- On a phone the menu runs along under the profile as icons alone: the thumbstick has the screen's lower left
local function layoutRail(isCompact)
    rail:FindFirstChildOfClass("UIListLayout").FillDirection = if isCompact then Enum.FillDirection.Horizontal else Enum.FillDirection.Vertical
    for _, button in rail:GetChildren() do
        if button:IsA("TextButton") then
            button.Size = UDim2.fromOffset(if isCompact then 44 else 150, 42)
            local word = button:FindFirstChild("Word")
            if word then
                word.Visible = not isCompact
            end
        end
    end
end
Hud.CompactChanged:Connect(layoutRail)

-- The three counters share one slim strip, side by side
local strip = UiKit.panel({
    Name = "Counters", AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 30), Brackets = false, Parent = Hud.Currency,
})
local stripRow = Instance.new("Frame")
stripRow.Name = "Row"
stripRow.BackgroundTransparency = 1
stripRow.AutomaticSize = Enum.AutomaticSize.X
stripRow.Size = UDim2.fromScale(0, 1)
stripRow.Parent = strip
UiKit.padding(stripRow, 8, 0)
UiKit.list(stripRow, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), VerticalAlignment = Enum.VerticalAlignment.Center })

-- A resource chip: its icon and a value. Returns the chip and a function that sets its number: it rolls
-- there, and what changed floats off under the chip. opts: Format (number to text), FloatFormat, Color.
function Hud.chip(name, image, order, opts)
    local chip = Instance.new("Frame")
    chip.Name = name
    chip.BackgroundTransparency = 1
    chip.AutomaticSize = Enum.AutomaticSize.X
    chip.Size = UDim2.fromScale(0, 1)
    chip.LayoutOrder = order
    chip.Parent = stripRow
    -- the row is its own frame: what's gained floats off under the chip, outside the row's order
    local row = Instance.new("Frame")
    row.Name = "Row"
    row.BackgroundTransparency = 1
    row.AutomaticSize = Enum.AutomaticSize.X
    row.Size = UDim2.fromScale(0, 1)
    row.Parent = chip
    UiKit.list(row, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 5), VerticalAlignment = Enum.VerticalAlignment.Center })
    local icon = Instance.new("Frame") -- the picture alone, no box: it stays as small as the strip
    icon.Name = "Icon"
    icon.BackgroundTransparency = 1
    icon.Size = UDim2.fromOffset(20, 20)
    icon.Parent = row
    local picture = Instance.new("ImageLabel")
    picture.Name = "Image"
    picture.BackgroundTransparency = 1
    picture.Image = image
    picture.Size = UDim2.fromScale(1, 1)
    picture.Parent = icon
    local value = UiKit.label({
        Name = "Value", Font = "Strong", TextSize = 14, AutomaticSize = Enum.AutomaticSize.X,
        Size = UDim2.fromOffset(0, 20), LayoutOrder = 2, Parent = row,
    })
    return chip, UiFx.counter(value, opts.Format, {
        Color = opts.Color, FloatIn = chip, Icon = icon:FindFirstChild("Image"), FloatFormat = opts.FloatFormat,
    })
end

local function addBadge(button)
    local badge = UiKit.label({
        Name = "Badge", Font = "Strong", TextSize = 11, TextColor3 = UiTheme.Colors.Panel,
        BackgroundTransparency = 0, BackgroundColor3 = UiTheme.Colors.Accent,
        AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 6, 0, -6), Size = UDim2.fromOffset(0, 18),
        AutomaticSize = Enum.AutomaticSize.X, TextXAlignment = Enum.TextXAlignment.Center, Visible = false,
        ZIndex = 5, Parent = button,
    })
    UiKit.corner(badge, 9)
    UiKit.padding(badge, 6, 0)
    local scale = Instance.new("UIScale")
    scale.Parent = badge
    return function(text, tone)
        if text ~= nil and text ~= badge.Text then -- something new: it jumps
            scale.Scale = 1.5
            UiFx.tween(scale, 0.32, { Scale = 1 }, Enum.EasingStyle.Back)
        end
        badge.Visible = text ~= nil
        badge.Text = text or ""
        badge.BackgroundColor3 = if tone == "Highlight" then UiTheme.Colors.Highlight else UiTheme.Colors.Accent
    end
end

-- A menu button on the rail: its icon beside its word, with an optional badge (a count, or a dot).
-- Returns the button and a function that sets the badge text (nil hides it).
function Hud.railButton(name, image, word, order)
    local button = UiKit.button({ Name = name, Text = "", Size = UDim2.fromOffset(150, 42), LayoutOrder = order, Tone = "Quiet", Parent = Hud.Rail })
    local icon = UiKit.icon(image, 32)
    icon.AnchorPoint = Vector2.new(0, 0.5)
    icon.Position = UDim2.new(0, 6, 0.5, 0)
    icon.Parent = button
    UiKit.label({
        Name = "Word", Font = "Strong", Text = word, TextSize = 15, TextColor3 = UiTheme.Colors.Text,
        AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, 46, 0.5, 0), Size = UDim2.new(1, -50, 0, 18), Parent = button,
    })
    layoutRail(compact == true)
    return button, addBadge(button)
end

-- A small round button in the top row, with the same badge.
function Hud.topButton(name, image, order)
    local button = UiKit.button({ Name = name, Text = "", Size = UDim2.fromOffset(42, 42), LayoutOrder = order, Tone = "Quiet", Parent = Hud.TopRight })
    button:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(1, 0)
    button:SetAttribute("NoSheen", true) -- a band of light would show this round button's square corners
    local icon = UiKit.icon(image, 32)
    icon.BackgroundTransparency = 1
    icon:FindFirstChildOfClass("UIStroke"):Destroy()
    icon.AnchorPoint = Vector2.new(0.5, 0.5)
    icon.Position = UDim2.fromScale(0.5, 0.5)
    icon.Parent = button
    return button, addBadge(button)
end

-- ---------- windows ----------
-- A window over the HUD: a TITLE header, a close button, and its Body. One is open at
-- a time: opening one closes the other (its OnClose runs), so they never stack.
-- props: Name, Title, Size (Vector2), AnchorPoint, Position (UDim2), OnClose (function)
-- Returns { Frame, Body, open(), close(), isOpen(), setTitle(text) }.
local windows = {}
local WINDOW_MARGIN = 24
local SLIDE = TweenInfo.new(0.16, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)

function Hud.window(props)
    local frame = UiKit.panel({
        Name = props.Name, Size = UDim2.fromOffset(props.Size.X, props.Size.Y), AnchorPoint = props.AnchorPoint,
        Position = props.Position, Visible = false, ZIndex = 10, Parent = windowGui,
    })
    frame.BackgroundTransparency = 0 -- near solid, all the way down: the HUD under a window mustn't read through it
    frame:FindFirstChildOfClass("UIGradient").Transparency = NumberSequence.new(0)
    frame.Active = true -- clicks on it stay on it: they mustn't swing the player's weapon behind it
    applyHudScale(frame)
    -- on a small screen it stays at the HUD's scale, so its text stays readable, and gets shorter: its lists scroll
    local function fitToScreen()
        local view, scale = HudMetrics.viewport(), HudMetrics.scale()
        local room = (view.Y - GuiService:GetGuiInset().Y - WINDOW_MARGIN) / scale
        local across = (view.X - WINDOW_MARGIN) / scale
        frame.Size = UDim2.fromOffset(math.min(props.Size.X, across), math.min(props.Size.Y, room))
    end
    HudMetrics.Changed:Connect(fitToScreen)
    fitToScreen()
    local inner = UiKit.content(frame, 14, 10)
    local _, title = UiKit.header(inner, props.Title, { TextSize = 14 })
    local closeButton = UiKit.button({
        Name = "Close", Tone = "Danger", Font = "Strong", Text = "X", TextSize = 14, AnchorPoint = Vector2.new(1, 0),
        Position = UDim2.new(1, 4, 0, -4), Size = if UserInputService.TouchEnabled then UDim2.fromOffset(38, 38) else UDim2.fromOffset(28, 28),
        Parent = inner,
    })
    local body = Instance.new("Frame")
    body.Name = "Body"
    body.BackgroundTransparency = 1
    body.Position = UDim2.fromOffset(0, 34)
    body.Size = UDim2.new(1, 0, 1, -34)
    body.Parent = inner

    local win = { Frame = frame, Body = body }
    local home = props.Position
    local opened = false
    local shown = 0 -- which opening or closing is the latest: a quick reopen cancels a closing
    local hudScale = frame:FindFirstChildOfClass("UIScale")
    -- its rest scale is the screen's (HudScale), read each time: the screen may change while it is open
    local restScale = HudMetrics.scale
    UiFx.edgeLight(frame)
    function win.isOpen()
        return opened
    end
    function win.close()
        if not opened then
            return
        end
        opened = false
        shown += 1
        local this = shown
        UiFx.tween(hudScale, 0.09, { Scale = restScale() * 0.95 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
        task.delay(0.09, function()
            if shown == this then
                frame.Visible = false
                hudScale.Scale = restScale()
            end
        end)
        if props.OnClose then
            props.OnClose()
        end
    end
    function win.open()
        for _, other in windows do
            if other ~= win then
                other.close()
            end
        end
        if not opened then
            opened = true
            shown += 1
            local this = shown
            task.delay(0.25, function() -- (the screen changed while it unfolded: the tween ended on the old scale)
                if shown == this then
                    hudScale.Scale = restScale()
                end
            end)
            Sfx.play("Open")
            frame.Position = home + UDim2.fromOffset(0, 14) -- it rises into place, unfolding
            frame.Visible = true
            hudScale.Scale = restScale() * 0.93
            UiFx.tween(hudScale, 0.24, { Scale = restScale() }, Enum.EasingStyle.Back)
            TweenService:Create(frame, SLIDE, { Position = home }):Play()
            UiFx.flash(frame)
            UiFx.scan(frame)
            task.defer(UiFx.stagger, body) -- once whoever opened it has filled its list
        end
    end
    function win.setTitle(text)
        title.Text = text
    end
    closeButton.Activated:Connect(win.close)
    table.insert(windows, win)
    return win
end

-- ---------- the Cultivation dock ----------
-- The bottom of the screen's main piece (the owner's reference, 2026-11-04): one plate, a cultivator in the
-- lotus in the circle on its left, the air leaps and stamina bar above the Cultivate button. Hud builds the
-- frame; QinggongController fills Top and Bar, TrainingController puts its button in Action.
-- Two sizes, and it follows the screen: the screen's size may not be known yet when this first runs.
local DOCK_SIZES = {
    [true] = { Width = 310, Height = 90, Emblem = 80, Button = 38, TextSize = 12, Top = 4, Bar = 24, BarHeight = 10, Bottom = -6 },
    [false] = { Width = 380, Height = 108, Emblem = 100, Button = 48, TextSize = 13, Top = 7, Bar = 28, BarHeight = 13, Bottom = -8 },
}

local dock = Instance.new("Frame")
dock.Name = "CultivationDock"
dock.BackgroundTransparency = 1
dock.LayoutOrder = 30
dock.Parent = Hud.Dock

local plate = UiKit.panel({
    Name = "Plate", Brackets = false, ZIndex = 2, Parent = dock,
})
plate.BackgroundTransparency = 0.04
plate:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, 12)
plate.Glow:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, 11)
UiFx.edgeLight(plate, 9)

-- the emblem: a round well of silver (the owner), the figure in deep gold on it, the gold ring round it
local emblem = Instance.new("Frame")
emblem.Name = "Emblem"
emblem.AnchorPoint = Vector2.new(0, 0.5)
emblem.Position = UDim2.new(0, 0, 0.5, 0)
emblem.BackgroundTransparency = 1
emblem.ZIndex = 3
emblem.Parent = dock
local well = Instance.new("Frame")
well.Name = "Well"
well.AnchorPoint = Vector2.new(0.5, 0.5)
well.Position = UDim2.fromScale(0.5, 0.5)
well.Size = UDim2.fromScale(0.8, 0.8)
well.BackgroundColor3 = Color3.fromRGB(236, 239, 245)
well.BorderSizePixel = 0
well.Parent = emblem
UiKit.corner(well, 999)
local wellDepth = Instance.new("UIGradient")
wellDepth.Rotation = 90
wellDepth.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(176, 180, 190))
wellDepth.Parent = well
local emblemIcon = Instance.new("ImageLabel")
emblemIcon.Name = "Icon"
emblemIcon.BackgroundTransparency = 1
emblemIcon.Image = UiTheme.Ornaments.LotusSit -- a cultivator in the lotus (the owner)
emblemIcon.ImageColor3 = Color3.fromRGB(240, 205, 110) -- the drawing is pale gold: this deepens it, to stand out on silver
emblemIcon.AnchorPoint = Vector2.new(0.5, 0.5)
emblemIcon.Position = UDim2.fromScale(0.5, 0.5)
emblemIcon.Size = UDim2.fromScale(0.68, 0.68)
emblemIcon.Parent = emblem
Hud.CultivationEmblemWell = well
local ring = Instance.new("ImageLabel")
ring.Name = "Ring"
ring.BackgroundTransparency = 1
ring.Image = UiTheme.Ornaments.EmblemRing
ring.Size = UDim2.fromScale(1, 1)
ring.Parent = emblem

local top = Instance.new("Frame")
top.Name = "Top"
top.BackgroundTransparency = 1
top.Parent = plate
local barSlot = Instance.new("Frame")
barSlot.Name = "BarSlot"
barSlot.BackgroundTransparency = 1
barSlot.Parent = plate
local action = Instance.new("Frame")
action.Name = "Action"
action.BackgroundTransparency = 1
action.AnchorPoint = Vector2.new(0, 1)
action.Parent = plate

local dockResized = Instance.new("BindableEvent")
Hud.CultivationDock = { Top = top, Bar = barSlot, Action = action, Emblem = emblemIcon, Ring = ring, Resized = dockResized.Event, Size = nil }

local function layoutDock(compact)
    local size = DOCK_SIZES[compact]
    local plateLeft = math.floor(size.Emblem * 0.45)
    local contentLeft = size.Emblem - plateLeft + 8
    dock.Size = UDim2.fromOffset(size.Width, size.Height)
    plate.Position = UDim2.fromOffset(plateLeft, 3)
    plate.Size = UDim2.new(1, -plateLeft, 1, -6)
    emblem.Size = UDim2.fromOffset(size.Emblem, size.Emblem)
    top.Position = UDim2.fromOffset(contentLeft, size.Top)
    top.Size = UDim2.new(1, -contentLeft - 14, 0, 18)
    barSlot.Position = UDim2.fromOffset(contentLeft, size.Bar)
    barSlot.Size = UDim2.new(1, -contentLeft - 22, 0, size.BarHeight)
    action.Position = UDim2.new(0, contentLeft, 1, size.Bottom)
    action.Size = UDim2.new(1, -contentLeft - 10, 0, size.Button)
    Hud.CultivationDock.Size = size
    dockResized:Fire(size, compact)
end
Hud.CompactChanged:Connect(layoutDock)
layoutDock(Hud.isCompact())

-- ---------- the first moment ----------
-- The HUD arrives from the screen's edges, once, instead of being there already.
local function arrive(frame, from, delay)
    local home = frame.Position
    frame.Position = home + from
    UiFx.tween(frame, 0.55, { Position = home }, Enum.EasingStyle.Quint, Enum.EasingDirection.Out, 0, false, delay)
end
arrive(Hud.Status, UDim2.fromOffset(-300, 0), 0.5)
arrive(Hud.Currency, UDim2.fromOffset(0, -70), 0.58)
arrive(Hud.TopRight, UDim2.fromOffset(0, -70), 0.62)
arrive(Hud.Quest, UDim2.fromOffset(340, 0), 0.66)
arrive(Hud.Dock, UDim2.fromOffset(0, 260), 0.72)

return Hud
