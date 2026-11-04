-- The HUD's regions, laid out from the owner's reference (2026-11-04). Every controller puts its pieces
-- into a region, in its LayoutOrder, instead of placing them by pixel, so they line up and never overlap:
--   Status    top left, one column: the player's profile, then the Rail
--   Rail      the menu down the left: Pets, Robes, Quests, Settings
--   Currency  top centre, in the row beside Roblox's own buttons: Qi, Spirit Stones, Relics
--   TopRight  top right, in that row: small round buttons (Rewards)
--   Quest     right, under them: the current quest (QuestController)
--   Banner    top centre, under the currencies: the guardian's bar and messages (Toast)
--   Dock      bottom centre, bottom up: Cultivate, the breakthrough, the Qinggong strip
-- Strike, Dash and Sword stand round Roblox's jump button, bottom right. Roblox's chat stays where Roblox
-- puts it, at the top. Windows (the pets list, the altar, the shops): Hud.window, one open at a time.
-- Each region scales with the screen (HudScale). Hud.isCompact() is true on a short screen (a phone in
-- landscape). The first script to require this builds it.
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

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
local COMPACT_BELOW = 500 -- px on the screen's shorter side: phones in landscape
local compactChanged = Instance.new("BindableEvent")
Hud.CompactChanged = compactChanged.Event
local compact = nil
local function checkCompact()
    local camera = workspace.CurrentCamera
    if not camera then
        return
    end
    local now = math.min(camera.ViewportSize.X, camera.ViewportSize.Y) < COMPACT_BELOW
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
local watched
local function watchCamera()
    if watched then
        watched:Disconnect()
    end
    local camera = workspace.CurrentCamera
    watched = camera and camera:GetPropertyChangedSignal("ViewportSize"):Connect(checkCompact)
    checkCompact()
end
workspace:GetPropertyChangedSignal("CurrentCamera"):Connect(watchCamera)
watchCamera()

-- A resource chip: its icon and a value. Returns the chip and its value label.
function Hud.chip(name, image, order)
    local chip = UiKit.panel({
        Name = name, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 34),
        LayoutOrder = order, Brackets = false, Parent = Hud.Currency,
    })
    -- the row is its own frame: a list on the panel would also line up the panel's glow
    local row = Instance.new("Frame")
    row.Name = "Row"
    row.BackgroundTransparency = 1
    row.AutomaticSize = Enum.AutomaticSize.X
    row.Size = UDim2.fromScale(0, 1)
    row.Parent = chip
    UiKit.padding(row, 5, 5)
    UiKit.list(row, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), VerticalAlignment = Enum.VerticalAlignment.Center })
    UiKit.icon(image, 24).Parent = row
    local value = UiKit.label({
        Name = "Value", Font = "Strong", TextSize = 16, AutomaticSize = Enum.AutomaticSize.X,
        Size = UDim2.fromOffset(0, 24), LayoutOrder = 2, Parent = row,
    })
    local pad = Instance.new("UIPadding")
    pad.PaddingRight = UDim.new(0, 6)
    pad.Parent = value
    return chip, value
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
    return function(text, tone)
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
    return button, addBadge(button)
end

-- A small round button in the top row, with the same badge.
function Hud.topButton(name, image, order)
    local button = UiKit.button({ Name = name, Text = "", Size = UDim2.fromOffset(42, 42), LayoutOrder = order, Tone = "Quiet", Parent = Hud.TopRight })
    button:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(1, 0)
    local icon = UiKit.icon(image, 32)
    icon.BackgroundTransparency = 1
    icon:FindFirstChildOfClass("UIStroke"):Destroy()
    icon.AnchorPoint = Vector2.new(0.5, 0.5)
    icon.Position = UDim2.fromScale(0.5, 0.5)
    icon.Parent = button
    return button, addBadge(button)
end

-- ---------- windows ----------
-- A System window over the HUD: a [ TITLE ] header, a close button, and its Body. One is open at
-- a time: opening one closes the other (its OnClose runs), so they never stack.
-- props: Name, Title, Size (Vector2), AnchorPoint, Position (UDim2), OnClose (function)
-- Returns { Frame, Body, open(), close(), isOpen(), setTitle(text) }.
local windows = {}
local SLIDE = TweenInfo.new(0.16, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)

function Hud.window(props)
    local frame = UiKit.panel({
        Name = props.Name, Size = UDim2.fromOffset(props.Size.X, props.Size.Y), AnchorPoint = props.AnchorPoint,
        Position = props.Position, Visible = false, ZIndex = 10, Parent = windowGui,
    })
    frame.BackgroundTransparency = 0.06 -- near solid: the HUD under a window mustn't read through it
    frame.Active = true -- clicks on it stay on it: they mustn't swing the player's weapon behind it
    applyHudScale(frame, props.Size.Y) -- and never taller than the screen (a phone)
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
    function win.isOpen()
        return frame.Visible
    end
    function win.close()
        if not frame.Visible then
            return
        end
        frame.Visible = false
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
        if not frame.Visible then
            frame.Position = home + UDim2.fromOffset(0, 12) -- it rises into place
            frame.Visible = true
            TweenService:Create(frame, SLIDE, { Position = home }):Play()
        end
    end
    function win.setTitle(text)
        title.Text = "[  " .. text .. "  ]"
    end
    closeButton.Activated:Connect(win.close)
    table.insert(windows, win)
    return win
end

return Hud
