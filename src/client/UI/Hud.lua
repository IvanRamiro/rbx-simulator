-- The HUD's regions, laid out from the owner's reference (2026-11-04). Every controller puts its pieces
-- into a region, in its LayoutOrder, instead of placing them by pixel, so they line up and never overlap:
--   Status    top left, one column: the player's profile, then the Rail
--   Rail      the menu down the left: Shop, Pets, Codex, Robes, Quests, Titles, Settings (on a phone, icons in a row under the profile)
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
local ContextActionService = game:GetService("ContextActionService")
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

-- Notifications (Toast) get a screen of their own too, over the windows: a shop's refusal mustn't hide behind the shop
local oldNotice = playerGui:FindFirstChild("HudNotice")
if oldNotice then
    oldNotice:Destroy()
end
local noticeGui = Instance.new("ScreenGui")
noticeGui.Name = "HudNotice"
noticeGui.ResetOnSpawn = false
noticeGui.DisplayOrder = 25
noticeGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
noticeGui.Parent = playerGui

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
-- where the notification shows: top centre, hanging just under whatever the Banner holds (it follows the Banner's foot)
Hud.Notice = region("Notice", Vector2.new(0.5, 0), UDim2.new(0.5, 0, 0, M), Enum.FillDirection.Vertical,
    Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Top, 6, noticeGui)
-- Under the Banner; but where an open window would be covered (its title, its tabs), it moves down to sit just over the
-- window's foot instead (a short screen: a purchase's message hid the Blacksmith's title, a new player's run, 2026-11-11).
local openWindowFrame = nil -- set by Hud.window: the frame of the window that is open, if any
local function placeNotice()
    local banner = Hud.Banner
    local scale = HudMetrics.scale()
    local notice = Hud.Notice
    -- what it holds may keep a margin round itself for its glow (its "Bleed", in its own units): the region rises by that much,
    -- so the notification's visible edge, not its margin, is what sits on the line (the profile's and the QUEST panel's top)
    local bleed = (notice:GetAttribute("Bleed") or 0) * scale
    local foot = (if banner.AbsoluteSize.Y > 1 then banner.AbsolutePosition.Y + banner.AbsoluteSize.Y + 6 * scale else M) - bleed
    local frame = openWindowFrame
    if frame and frame.Visible and notice.AbsoluteSize.Y > 1 and foot + notice.AbsoluteSize.Y > frame.AbsolutePosition.Y then
        local bottom = frame.AbsolutePosition.Y + frame.AbsoluteSize.Y - 12 * scale -- over the window's lowest part
        notice.AnchorPoint = Vector2.new(0.5, 1)
        notice.Position = UDim2.new(0.5, 0, 0, bottom)
        return
    end
    notice.AnchorPoint = Vector2.new(0.5, 0)
    notice.Position = UDim2.new(0.5, 0, 0, foot)
end
Hud.Banner:GetPropertyChangedSignal("AbsoluteSize"):Connect(placeNotice)
Hud.Banner:GetPropertyChangedSignal("AbsolutePosition"):Connect(placeNotice)
Hud.Notice:GetPropertyChangedSignal("AbsoluteSize"):Connect(placeNotice)
Hud.Notice:GetAttributeChangedSignal("Bleed"):Connect(placeNotice)
Hud.Quest = region("Quest", Vector2.new(1, 0), UDim2.new(1, -M, 0, M), Enum.FillDirection.Vertical,
    Enum.HorizontalAlignment.Right, Enum.VerticalAlignment.Top, 6)
-- The row beside Roblox's own buttons: the counters and the round buttons share one middle line (placeTopRow, under the
-- compact screens' code), whatever their own heights.
Hud.Currency = region("Currency", Vector2.new(0.5, 0.5), UDim2.new(0.5, 0, 0, 0), Enum.FillDirection.Horizontal,
    Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center, 8, topGui)
Hud.TopRight = region("TopRight", Vector2.new(1, 0.5), UDim2.new(1, -M, 0, 0), Enum.FillDirection.Horizontal,
    Enum.HorizontalAlignment.Right, Enum.VerticalAlignment.Center, 8, topGui)

-- The menu down the left, under the profile
local rail = Instance.new("Frame")
rail.Name = "Rail"
rail.BackgroundTransparency = 1
rail.AutomaticSize = Enum.AutomaticSize.XY
rail.Size = UDim2.new()
rail.LayoutOrder = 20
rail.Parent = Hud.Status
-- square tiles, two to a row (the owner, 2026-11-13: "Cultivation Bold", the top games' icon tiles in our colours)
local railGrid = Instance.new("UIGridLayout")
railGrid.SortOrder = Enum.SortOrder.LayoutOrder
railGrid.FillDirection = Enum.FillDirection.Horizontal
railGrid.CellPadding = UDim2.fromOffset(8, 8)
railGrid.Parent = rail
Hud.Rail = rail
local RAIL_TILE = 70 -- a tile's side (a phone's row of tiles: 54 by 52, see layoutRail)

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
HudMetrics.Changed:Connect(checkCompact)
checkCompact()

-- the top row's line: the round buttons (Hud.topButton) hang TOP_ROW_TOP under the screen's top edge, and the counters centre
-- on their middle (the counters' strip and a round button are different heights: on a phone, their tops at the same offset
-- left two middles 4 px apart)
local TOP_ROW_TOP = 6
local TOP_BUTTON = { [true] = 56, [false] = 46 } -- a round button's side; 56 on a phone is 45 pixels at its 0.8 scale
local function placeTopRow()
    local middle = TOP_ROW_TOP + TOP_BUTTON[compact == true] * HudMetrics.scale() / 2
    Hud.Currency.Position = UDim2.new(0.5, 0, 0, middle)
    Hud.TopRight.Position = UDim2.new(1, -M, 0, middle)
end
HudMetrics.Changed:Connect(placeTopRow)
Hud.CompactChanged:Connect(placeTopRow)
placeTopRow()

HudMetrics.keepReadable(gui)
HudMetrics.keepReadable(topGui)
HudMetrics.keepReadable(windowGui, HudMetrics.windowScale) -- (a window is drawn at its own scale: Hud.window)

-- On a phone the menu runs along under the profile as icons alone: the thumbstick has the screen's lower left. A tile made
-- with KeepWord (the Shop) keeps its word there, in gold, and its icon moves up over it, as on the desktop's tiles.
local PHONE_TILE = 56 -- 56 at a phone's scale (0.8) is 45 pixels: a thumb's 44 (UI overhaul 2026-11-15; the audit of 2026-11-11 found 35)
local WORD_HEIGHT, WORD_INSET, ICON_TOP = 13, 4, 6 -- a tile's word: its height and its inset from the foot; the icon's from the top
local function layoutRail(isCompact)
    local tile = if isCompact then PHONE_TILE else RAIL_TILE
    railGrid.CellSize = UDim2.fromOffset(tile, tile)
    railGrid.FillDirectionMaxCells = if isCompact then 0 else 2
    for _, button in rail:GetChildren() do
        if button:IsA("TextButton") then
            local keepWord = button:GetAttribute("KeepWord") == true
            local worded = not isCompact or keepWord
            local word = button:FindFirstChild("Word")
            if word then
                word.Visible = worded
                word.TextColor3 = if isCompact and keepWord then UiTheme.Colors.Highlight else UiTheme.Colors.Text
            end
            local icon = button:FindFirstChild("Icon")
            if icon then
                icon.AnchorPoint = Vector2.new(0.5, 0.5)
                if worded then -- over its word, in the room the word leaves (a phone's smaller tile: a closer top, 3 over the word)
                    local top = if isCompact then 4 else ICON_TOP
                    local side = if isCompact then tile - top - WORD_HEIGHT - WORD_INSET - 3 else 42
                    icon.Size = UDim2.fromOffset(side, side)
                    icon.Position = UDim2.new(0.5, 0, 0, top + side / 2)
                else -- alone on a phone's tile, in its middle
                    icon.Size = UDim2.fromOffset(38, 38)
                    icon.Position = UDim2.fromScale(0.5, 0.5)
                end
            end
        end
    end
end
Hud.CompactChanged:Connect(layoutRail)

-- The three counters share one slim strip, side by side
local strip = UiKit.panel({ -- (bold, the owner 2026-11-13: bigger icons and numbers, outlined, as the top games show their money)
    Name = "Counters", AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 42), Brackets = false, Parent = Hud.Currency,
})
strip:FindFirstChildOfClass("UIStroke").Thickness = 2
local stripRow = Instance.new("Frame")
stripRow.Name = "Row"
stripRow.BackgroundTransparency = 1
stripRow.AutomaticSize = Enum.AutomaticSize.X
stripRow.Size = UDim2.fromScale(0, 1)
stripRow.Parent = strip
UiKit.padding(stripRow, 12, 0)
UiKit.list(stripRow, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 14), VerticalAlignment = Enum.VerticalAlignment.Center })

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
    icon.Size = UDim2.fromOffset(30, 30)
    icon.Parent = row
    local picture = Instance.new("ImageLabel")
    picture.Name = "Image"
    picture.BackgroundTransparency = 1
    picture.Image = image
    picture.Size = UDim2.fromScale(1, 1)
    picture.Parent = icon
    local value = UiKit.label({
        Name = "Value", Font = "Heavy", TextSize = 21, AutomaticSize = Enum.AutomaticSize.X,
        Size = UDim2.fromOffset(0, 26), LayoutOrder = 2, Parent = row,
    })
    UiKit.outline(value, 2)
    return chip, UiFx.counter(value, opts.Format, {
        Color = opts.Color, FloatIn = chip, Icon = icon:FindFirstChild("Image"), FloatFormat = opts.FloatFormat,
    })
end

-- one place for every badge (the rail's tiles, the round buttons): over the top right corner, the same overhang everywhere
-- (the Rewards button had its own, and its badge sat lower and further in than the tiles'). 4 across leaves half a tile gap
-- to the next tile; 4 up keeps a top-row badge on the screen.
local BADGE_OUT = Vector2.new(4, 4)
local function addBadge(button)
    local badge = UiKit.label({
        Name = "Badge", Font = "Strong", TextSize = 11, TextColor3 = UiTheme.Colors.Panel,
        BackgroundTransparency = 0, BackgroundColor3 = UiTheme.Colors.Accent,
        AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, BADGE_OUT.X, 0, -BADGE_OUT.Y), Size = UDim2.fromOffset(0, 18),
        AutomaticSize = Enum.AutomaticSize.X, TextXAlignment = Enum.TextXAlignment.Center, Visible = false,
        ZIndex = 5, Parent = button,
    })
    badge.FontFace = UiTheme.Fonts.Heavy
    UiKit.corner(badge, 9)
    UiKit.padding(badge, 6, 0)
    UiKit.stroke(badge, UiTheme.Colors.Outline, 0.2, 1.5)
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

-- A menu tile on the rail: its icon over its word, with an optional badge (a count, or a dot).
-- opts.KeepWord: the word stays on a phone's tile too (the Shop's, so players can always find it).
-- Returns the button and a function that sets the badge text (nil hides it).
function Hud.railButton(name, image, word, order, opts)
    local button = UiKit.button({ Name = name, Text = "", Size = UDim2.fromOffset(RAIL_TILE, RAIL_TILE), LayoutOrder = order, Tone = "Tile", Parent = Hud.Rail })
    button:SetAttribute("KeepWord", opts ~= nil and opts.KeepWord == true)
    button:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, UiTheme.Radius.Card)
    button:SetAttribute("EdgeThickness", UiTheme.Stroke.Button)
    local icon = UiKit.icon(image, 42)
    icon.BackgroundTransparency = 1 -- the tile is the frame: the picture stands on it bare
    icon:FindFirstChildOfClass("UIStroke"):Destroy()
    icon.Parent = button
    local label = UiKit.label({
        Name = "Word", Font = "Heavy", Text = string.upper(word), TextSize = 11, TextColor3 = UiTheme.Colors.Text,
        TextXAlignment = Enum.TextXAlignment.Center, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -WORD_INSET),
        Size = UDim2.new(1, -4, 0, WORD_HEIGHT), ZIndex = 4, Parent = button,
    })
    UiKit.outline(label, 1.5)
    layoutRail(compact == true)
    return button, addBadge(button)
end

-- A small round button in the top row, with the same badge.
function Hud.topButton(name, image, order)
    local button = UiKit.button({ Name = name, Text = "", Size = UDim2.fromOffset(42, 42), LayoutOrder = order, Tone = "Quiet", Parent = Hud.TopRight })
    -- bigger on a phone, where 42 at the phone's scale is too small for a thumb: 56 there is 45 pixels (TOP_BUTTON)
    local function sizeFor(isCompact)
        local side = TOP_BUTTON[isCompact == true]
        button.Size = UDim2.fromOffset(side, side)
    end
    Hud.CompactChanged:Connect(sizeFor)
    sizeFor(compact == true)
    button:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(1, 0)
    button:SetAttribute("NoSheen", true) -- a band of light would show this round button's square corners
    button:SetAttribute("EdgeThickness", UiTheme.Stroke.Button)
    local icon = UiKit.icon(image, 32)
    icon.BackgroundTransparency = 1
    icon:FindFirstChildOfClass("UIStroke"):Destroy()
    icon.AnchorPoint = Vector2.new(0.5, 0.5)
    icon.Position = UDim2.fromScale(0.5, 0.5)
    icon.Size = UDim2.fromScale(0.72, 0.72)
    icon.Parent = button
    return button, addBadge(button)
end

-- ---------- a controller's selection ----------
-- A gamepad moves a selection through the buttons (Roblox's own UI navigation). Its frame is the interface's gold, not
-- Roblox's default box, so it reads as part of the game (UI audit 2026-11-11: no menu supported a controller at all).
do
    local selection = Instance.new("Frame")
    selection.Name = "Selection"
    selection.BackgroundTransparency = 1
    selection.Size = UDim2.new(1, 8, 1, 8)
    selection.Position = UDim2.fromOffset(-4, -4)
    UiKit.corner(selection, UiTheme.Corner + 4)
    local ring = Instance.new("UIStroke")
    ring.Color = UiTheme.Colors.Highlight
    ring.Thickness = 2.5
    ring.Parent = selection
    playerGui.SelectionImageObject = selection
end

local function usingGamepad()
    local last = UserInputService:GetLastInputType()
    return last.Name:find("^Gamepad") ~= nil
end

-- the first button a window's selection lands on: its uppermost, then leftmost, active and shown button (its close
-- button only if it has no other)
local function firstButton(root, closeButton)
    local best, bestY, bestX = nil, math.huge, math.huge
    for _, d in root:GetDescendants() do
        if d:IsA("GuiButton") and d ~= closeButton and d.Active and d.Selectable and d.AbsoluteSize.X > 0 then
            local shown = true
            local x = d
            while x and x ~= root do
                if x:IsA("GuiObject") and not x.Visible then
                    shown = false
                    break
                end
                x = x.Parent
            end
            local p = d.AbsolutePosition
            if shown and (p.Y < bestY - 2 or (math.abs(p.Y - bestY) <= 2 and p.X < bestX)) then
                best, bestY, bestX = d, p.Y, p.X
            end
        end
    end
    return best or closeButton
end

-- ---------- windows ----------
-- A window over the HUD: a TITLE header, a close button, and its Body. One is open at
-- a time: opening one closes the other (its OnClose runs), so they never stack.
-- props: Name, Title, Size (Vector2), OnClose (function); Side = true keeps the AnchorPoint and Position given (the
-- Hatching Altar's, which stands beside the altar it belongs to). Every other window opens in the same place: the middle
-- of the room beside the left column (the profile and the menu), or of the screen on a phone.
-- While one is open the quest panel and the Cultivation dock step aside, so nothing shows through or round it, and the
-- menu button that opened it (win.link(button)) stays lit.
-- Returns { Frame, Body, open(), close(), isOpen(), setTitle(text), link(button) }.
local windows = {}
local LEFT_COLUMN = 270 -- the profile's width: the menu sits under it
local CLOSE_ACTION = "HudCloseWindow"
local function openWindow()
    for _, win in windows do
        if win.isOpen() then
            return win
        end
    end
    return nil
end
-- gamepad B closes the open window (bound only while one is open, over the dash B otherwise gives)
local function bindClose()
    if openWindow() then
        ContextActionService:BindActionAtPriority(CLOSE_ACTION, function(_, state)
            local win = openWindow()
            if state == Enum.UserInputState.Begin and win then
                win.close()
                return Enum.ContextActionResult.Sink
            end
            return Enum.ContextActionResult.Pass
        end, false, Enum.ContextActionPriority.High.Value, Enum.KeyCode.ButtonB)
    else
        ContextActionService:UnbindAction(CLOSE_ACTION)
    end
end

-- Closes whatever window is open; true if one was.
function Hud.closeWindows()
    local win = openWindow()
    if win then
        win.close()
    end
    return win ~= nil
end

local function stepAside()
    local open = false
    for _, win in windows do
        open = open or win.isOpen()
    end
    Hud.Quest.Visible = not open
    Hud.Dock.Visible = not open
end
local WINDOW_MARGIN = 24
local switching = false -- a window opening closes the one before it: that close is silent (the opening has its own sound)
local SLIDE = TweenInfo.new(0.16, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local PAD = UiTheme.Pad.Window

-- A window's own scale: the HUD's, but never under 1 on a phone. The HUD shrinks there to leave the playfield clear; a window
-- is what the player is looking at, so its words stay readable and its buttons stay a thumb's size (44 px).
local windowScale = HudMetrics.windowScale
Hud.windowScale = windowScale

-- Every window shares one frame: a title band (its name centred, the close button at its right, a gold rule under it), and
-- its Body, padded the same on every side.
function Hud.window(props)
    local frame = UiKit.panel({
        Name = props.Name, Size = UDim2.fromOffset(props.Size.X, props.Size.Y), AnchorPoint = props.AnchorPoint,
        Position = props.Position, Visible = false, ZIndex = 10, Parent = windowGui,
    })
    frame.BackgroundTransparency = 0 -- near solid, all the way down: the HUD under a window mustn't read through it
    frame:FindFirstChildOfClass("UIGradient").Transparency = NumberSequence.new(0)
    frame:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, UiTheme.Radius.Window)
    frame.Glow:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, UiTheme.Radius.Window - 2)
    frame.Active = true -- clicks on it stay on it: they mustn't swing the player's weapon behind it
    local hudScale = Instance.new("UIScale")
    hudScale.Scale = windowScale()
    hudScale.Parent = frame
    -- on a small screen it keeps its scale, so its text stays readable, and gets shorter: its lists scroll
    local function fitToScreen()
        local view, scale = HudMetrics.viewport(), windowScale()
        local room = (view.Y - GuiService:GetGuiInset().Y - WINDOW_MARGIN) / scale
        local across = (view.X - WINDOW_MARGIN) / scale
        frame.Size = UDim2.fromOffset(math.min(props.Size.X, across), math.min(props.Size.Y, room))
    end
    -- where it rests: the middle of the screen; moved right only as far as it takes to clear the left column (the profile
    -- and the menu), and only if it then still fits on the screen. (Centring it in the room beside the column put every
    -- window visibly right of the middle: the owner, "the position of UI are off".)
    local home = props.Position
    local function place()
        fitToScreen()
        if props.Side then
            return
        end
        local view, scale = HudMetrics.viewport(), windowScale()
        local width = frame.Size.X.Offset * scale
        local centre = view.X / 2
        if not Hud.isCompact() then
            local clear = (M + LEFT_COLUMN + M) * scale + width / 2 -- the leftmost centre that clears the column
            local farthest = view.X - M * scale - width / 2 -- the rightmost centre that stays on the screen
            if clear > centre and clear <= farthest then
                centre = clear
            end
        end
        frame.AnchorPoint = Vector2.new(0.5, 0.5)
        home = UDim2.new(0, centre, 0.5, 0)
        if frame.Visible then
            frame.Position = home
        end
    end
    HudMetrics.Changed:Connect(place)
    place()
    local title, closeButton = UiKit.titleBar(frame, props.Title)
    local top = UiTheme.Height.TitleBar + UiTheme.Space.M
    local body = Instance.new("Frame")
    body.Name = "Body"
    body.BackgroundTransparency = 1
    body.Position = UDim2.fromOffset(PAD, top)
    body.Size = UDim2.new(1, -PAD * 2, 1, -(top + PAD))
    body.Parent = frame

    local win = { Frame = frame, Body = body }
    local opened = false
    local linked = nil -- the menu button that opens it
    local shown = 0 -- which opening or closing is the latest: a quick reopen cancels a closing
    -- its rest scale is the screen's, read each time: the screen may change while it is open
    local restScale = windowScale
    HudMetrics.Changed:Connect(function()
        hudScale.Scale = restScale()
    end)
    UiFx.edgeLight(frame)
    function win.isOpen()
        return opened
    end
    function win.close()
        if not opened then
            return
        end
        opened = false
        if not switching then
            Sfx.play("Close")
        end
        if linked then
            linked:SetAttribute("Tone", linked:GetAttribute("RestTone") or "Quiet")
        end
        if openWindowFrame == frame then
            openWindowFrame = nil
            task.defer(placeNotice)
        end
        stepAside()
        task.defer(bindClose)
        -- a controller's selection inside it goes back to the button that opened it
        local selected = GuiService.SelectedObject
        if selected and selected:IsDescendantOf(frame) then
            GuiService.SelectedObject = if usingGamepad() and linked and linked.Visible then linked else nil
        end
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
        switching = true
        for _, other in windows do
            if other ~= win then
                other.close()
            end
        end
        switching = false
        if not opened then
            opened = true
            if linked then
                linked:SetAttribute("Tone", "Accent")
            end
            openWindowFrame = frame
            task.delay(0.3, placeNotice) -- once it has risen into place
            stepAside()
            task.defer(bindClose)
            -- with a controller, the selection moves into it (once whoever opened it has filled it)
            task.delay(0.3, function()
                if opened and usingGamepad() then
                    GuiService.SelectedObject = firstButton(frame, closeButton)
                end
            end)
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
    function win.link(button)
        linked = button
        -- the tone it goes back to when the window closes: its own (a rail tile's is Tile)
        button:SetAttribute("RestTone", button:GetAttribute("RestTone") or button:GetAttribute("Tone") or "Quiet")
        button:SetAttribute("Tone", if opened then "Accent" else button:GetAttribute("RestTone"))
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
-- Height is the plate's: the dock's frame is exactly the plate (the emblem, shorter, centres on it), so the gap over it is
-- the Dock's own gap, like the gaps between the pills over it (the frame was 3 taller than the plate at each end: the gap
-- over the plate read 3 wider than the one between the pills).
local DOCK_SIZES = {
    -- (a phone: its button 56 tall, 45 pixels at the phone's scale; it was 38, 30 pixels)
    [true] = { Width = 330, Height = 102, Emblem = 88, Button = 56, TextSize = 12, Top = 5, Bar = 26, BarHeight = 9, Bottom = -6 },
    [false] = { Width = 380, Height = 102, Emblem = 100, Button = 48, TextSize = 13, Top = 7, Bar = 28, BarHeight = 13, Bottom = -8 },
}
local CONTENT_RIGHT = 10 -- the plate's rows (title, stamina bar, Cultivate) all end this far from its right edge

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

-- Where the Cultivate button sits across the dock: its centre's offset from the dock's left edge, and its width. The pills
-- stacked over the dock (the breakthrough, DRAW / SHEATHE) centre on this same line, so the column reads as one; centred on
-- the whole dock they sat over the emblem's side, and the three rows had three different middles (owner's screenshot,
-- 2026-11-15).
-- The plate's rows share this one span too (contentSpan): their left and right ends line up.
local function contentSpan(size)
    local plateLeft = math.floor(size.Emblem * 0.45)
    local contentLeft = size.Emblem - plateLeft + 8
    return plateLeft, contentLeft, size.Width - plateLeft - contentLeft - CONTENT_RIGHT
end
local function actionSpan(size)
    local plateLeft, contentLeft, width = contentSpan(size)
    return plateLeft + contentLeft + width / 2, width
end
function Hud.CultivationDock.actionSpan(size)
    return actionSpan(size or Hud.CultivationDock.Size)
end


-- ---------- the pills over the dock ----------
-- The buttons and labels stacked over the plate (the breakthrough, the station's bonus, DRAW / SHEATHE) are laid out here,
-- all on the Cultivate button's centre line (actionSpan) and at its height, so the column keeps one middle and one size
-- whoever adds to it. Each in its own row, bottom up in their order; but where that column would rise into the menu's row (a
-- phone's short screen: the breakthrough lay over the Settings tile), the buttons share one row instead, their group still
-- on that line (an OwnRow piece keeps its own row).
--   Hud.CultivationDock.addPill(object, order, opts)
--     opts.Width(actionWidth, height)  its natural width (its words and margins), in the HUD's units
--     opts.MatchAction                 alone in its row, at least as wide as Cultivate
--     opts.Height                      a fixed height (a label); a button takes the dock's button height and a pill's shape
--     opts.OwnRow                      never shares a row
--   Hud.CultivationDock.layoutPills()  lays them out again (a controller's words changed size)
local PILL_GAP = 8 -- the Dock region's own gap
local pills = {}
local pillHolder = Instance.new("Frame")
pillHolder.Name = "Pills"
pillHolder.BackgroundTransparency = 1
pillHolder.LayoutOrder = 20
pillHolder.Visible = false
pillHolder.Parent = Hud.Dock

-- whether a column of `height` (the HUD's units) over the plate would reach into the menu's row, on the screen as it is
local function columnMeetsRail(size, height, width)
    local rail, room = Hud.Rail, Hud.Dock.Parent
    if not (Hud.Status.Visible and rail.AbsoluteSize.Y > 1 and room:IsA("GuiBase2d")) then
        return false
    end
    local scale = HudMetrics.scale()
    -- where the column will stand once the Dock is at rest (it may still be arriving): the Dock hangs M over the screen's foot
    local foot = room.AbsolutePosition.Y + room.AbsoluteSize.Y - M
    local top = foot - (size.Height + PILL_GAP + height) * scale
    local dockLeft = room.AbsolutePosition.X + room.AbsoluteSize.X / 2 - size.Width * scale / 2
    local centre = actionSpan(size)
    local left, right = dockLeft + (centre - width / 2) * scale, dockLeft + (centre + width / 2) * scale
    -- the menu's place at rest: the Status region's offset from its home is the arrival still under way
    local shift = Hud.Status.AbsolutePosition.X - (room.AbsolutePosition.X + M)
    local railLeft = rail.AbsolutePosition.X - shift
    local railRight, railBottom = railLeft + rail.AbsoluteSize.X, rail.AbsolutePosition.Y + rail.AbsoluteSize.Y
    return top < railBottom + PILL_GAP * scale and left < railRight and right > railLeft
end

local function layoutPills()
    local size = Hud.CultivationDock.Size
    if not size then
        return
    end
    local centre, actionWidth = actionSpan(size)
    local shown = {}
    for _, pill in pills do
        if pill.object.Visible then
            pill.h = pill.opts.Height or size.Button
            pill.natural = pill.opts.Width(actionWidth, pill.h)
            table.insert(shown, pill)
        end
    end
    table.sort(shown, function(a, b)
        return a.order < b.order
    end)
    pillHolder.Visible = #shown > 0
    if #shown == 0 then
        return
    end
    local function widthIn(pill, alone)
        return if alone and pill.opts.MatchAction then math.max(pill.natural, actionWidth) else pill.natural
    end
    local function measure(rows)
        local height, widest = -PILL_GAP, 0
        for _, row in rows do
            local rowHeight, rowWidth = 0, -PILL_GAP
            for _, pill in row do
                rowHeight = math.max(rowHeight, pill.h)
                rowWidth += widthIn(pill, #row == 1) + PILL_GAP
            end
            height += rowHeight + PILL_GAP
            widest = math.max(widest, rowWidth)
        end
        return height, widest
    end
    local rows = {}
    for _, pill in shown do
        table.insert(rows, { pill })
    end
    local height, widest = measure(rows)
    if #rows > 1 and columnMeetsRail(size, height, widest) then
        local shared, together = {}, {}
        for _, pill in shown do
            if pill.opts.OwnRow then
                table.insert(shared, { pill })
            elseif #together == 0 then
                table.insert(together, pill)
                table.insert(shared, together)
            else
                table.insert(together, pill)
            end
        end
        rows = shared
        height = measure(rows)
    end
    local y = 0
    for _, row in rows do
        local rowHeight, rowWidth = 0, -PILL_GAP
        for _, pill in row do
            rowHeight = math.max(rowHeight, pill.h)
            rowWidth += widthIn(pill, #row == 1) + PILL_GAP
        end
        local x = centre - rowWidth / 2
        for _, pill in row do
            local width = widthIn(pill, #row == 1)
            local object = pill.object
            object.AnchorPoint = Vector2.new(0.5, 0.5)
            object.Position = UDim2.fromOffset(x + width / 2, y + rowHeight / 2)
            object.Size = UDim2.fromOffset(width, pill.h)
            if not pill.opts.Height then
                UiKit.pillShape(object, pill.h)
            end
            x += width + PILL_GAP
        end
        y += rowHeight + PILL_GAP
    end
    pillHolder.Size = UDim2.fromOffset(size.Width, height)
end

function Hud.CultivationDock.addPill(object, order, opts)
    local pill = { object = object, order = order, opts = opts }
    table.insert(pills, pill)
    object.Parent = pillHolder
    local function again()
        task.defer(layoutPills)
    end
    object:GetPropertyChangedSignal("Visible"):Connect(again)
    if object:IsA("TextButton") or object:IsA("TextLabel") then
        object:GetPropertyChangedSignal("TextBounds"):Connect(again)
    end
    layoutPills()
end
Hud.CultivationDock.layoutPills = layoutPills
HudMetrics.Changed:Connect(function()
    task.defer(layoutPills)
end)
Hud.Rail:GetPropertyChangedSignal("AbsoluteSize"):Connect(function()
    task.defer(layoutPills)
end)
Hud.Status:GetPropertyChangedSignal("Visible"):Connect(function()
    task.defer(layoutPills)
end)

local function layoutDock(compact)
    local size = DOCK_SIZES[compact]
    local plateLeft, contentLeft, contentWidth = contentSpan(size)
    dock.Size = UDim2.fromOffset(size.Width, size.Height)
    plate.Position = UDim2.fromOffset(plateLeft, 0)
    plate.Size = UDim2.new(1, -plateLeft, 1, 0)
    emblem.Size = UDim2.fromOffset(size.Emblem, size.Emblem)
    -- the title row, the stamina bar's slot (its end diamond included: QinggongController keeps it inside) and Cultivate: one span
    top.Position = UDim2.fromOffset(contentLeft, size.Top)
    top.Size = UDim2.fromOffset(contentWidth, 18)
    barSlot.Position = UDim2.fromOffset(contentLeft, size.Bar)
    barSlot.Size = UDim2.fromOffset(contentWidth, size.BarHeight)
    action.Position = UDim2.new(0, contentLeft, 1, size.Bottom)
    action.Size = UDim2.fromOffset(contentWidth, size.Button)
    Hud.CultivationDock.Size = size
    dockResized:Fire(size, compact)
    layoutPills()
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
-- once they have arrived: the screen's size may have changed while they moved (each tween ends where it was sent)
task.delay(1.4, function()
    placeTopRow()
    layoutPills()
end)

return Hud
