-- The HUD's regions, laid out from the owner's reference (2026-11-04). Every controller puts its pieces
-- into a region, in its LayoutOrder, instead of placing them by pixel, so they line up and never overlap:
--   Status    top left, one column: the player's profile, then the Rail
--   Rail      the menu down the left: Shop, Pets, Codex, Robes, Quests, Titles, Settings, Feedback (on a phone, icons in a row under the profile),
--             under its MENU toggle, which slides it away and back (M, a gamepad's d-pad left; saved in the player's settings)
--   Currency  top centre, in the row beside Roblox's own buttons: Qi, Spirit Stones, Relics, sharing one slim strip
--   TopRight  top right, in that row: small round buttons (Rewards)
--   Quest     right, under them: the current quest (QuestController), the air leaps under it (QinggongController)
--   Banner    top centre, under the currencies: messages (Toast) and the TAKE AN EGG panel
--   Dock      bottom centre, bottom up: the inventory bar (the weapon's slot), what rises over it (the breakthrough ...)
-- The touch actions stand beside Roblox's jump button, bottom right (TouchActions). Roblox's chat stays where Roblox
-- puts it, at the top. Windows (the pets list, the altar, the shops): Hud.window, one open at a time.
-- Each region scales with the screen (HudScale, HudMetrics), and text stays readable at any scale. Hud.isCompact() is true on a
-- short screen (a phone in landscape): pieces change their layout on it, following Hud.CompactChanged. The first script to require this builds it.
local GuiService = game:GetService("GuiService")
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
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
-- where the notification shows: top centre, hanging just under whatever the Banner holds (layoutTop places it)
Hud.Notice = region("Notice", Vector2.new(0.5, 0), UDim2.new(0.5, 0, 0, M), Enum.FillDirection.Vertical,
    Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Top, 6, noticeGui)
Hud.Quest = region("Quest", Vector2.new(1, 0), UDim2.new(1, -M, 0, M), Enum.FillDirection.Vertical,
    Enum.HorizontalAlignment.Right, Enum.VerticalAlignment.Top, 6)

-- ---------- the top centre: one stack ----------
-- The Banner's pieces (the Lightning Trial, the egg panel, the tutorial, the Merchant's line) and the notification under them
-- are one stack at the top centre, between the left column (the profile, the menu) and the right one (the quest panel, the air
-- leaps), and each hangs only as low as it stays clear of them and of the inventory bar. On a phone the menu's row runs under
-- the profile into the middle of the screen: the tutorial, the Merchant's line and a notification piled down over its tiles
-- and the player (phone pass, 2026-11-16). What doesn't fit waits its turn and comes back when there is room: the Banner's
-- later pieces first; and while a notification shows (a few seconds; a tap puts it away), the pieces it needs the room of.
-- A piece with a LayoutOrder under 0 (the Lightning Trial, the egg panel: the moment's own) never waits.
-- Where an open window would be covered (its title, its tabs), the notification sits just over the window's foot instead
-- (a short screen: a purchase's message hid the Blacksmith's title, a new player's run, 2026-11-11).
local STACK_GAP = 6 -- the Banner's own gap
local SIDE_GAP = 8 -- kept from the side pieces
local openWindowFrame = nil -- set by Hud.window: the frame of the window that is open, if any
local bannerWaiting = Instance.new("Frame") -- where a Banner piece waits: hidden, at the HUD's scale so it measures the same
bannerWaiting.Name = "BannerWaiting"
bannerWaiting.BackgroundTransparency = 1
bannerWaiting.Visible = false
bannerWaiting.Parent = gui
applyHudScale(bannerWaiting)
local bannerPieces = setmetatable({}, { __mode = "k" })

-- The width the top centre has between the side columns, in the HUD's units (its scale applies after), up to `nominal`.
-- The notification and the tutorial are sized by it (UI audit 2026-11-11: a fixed 420 overlapped both columns on a tablet).
function Hud.centreRoom(nominal)
    local view, scale = HudMetrics.viewport(), HudMetrics.scale()
    local profile = Hud.Status:FindFirstChild("StatusWindow")
    local left = if Hud.Status.Visible and profile and profile.Visible then M + profile.AbsoluteSize.X else 0 -- (at rest)
    local quest = Hud.Quest
    local right = if quest.Visible and quest.AbsoluteSize.X > 1 then M + quest.AbsoluteSize.X else 0
    local side = math.max(left, right) + (SIDE_GAP + 2) * scale
    return math.min((view.X - 2 * side) / scale, nominal)
end

-- the boxes the stack keeps clear of, in pixels, where they rest (the side columns slide in when the game starts)
local function sideBoxes()
    local boxes = {}
    local width, height = gui.AbsoluteSize.X, gui.AbsoluteSize.Y
    local function add(piece, shift)
        if piece:IsA("GuiObject") and piece.Visible and piece.AbsoluteSize.X > 1 and piece.AbsoluteSize.Y > 1 then
            local at = piece.AbsolutePosition - shift
            table.insert(boxes, { at, at + piece.AbsoluteSize })
        end
    end
    local status, quest, dock = Hud.Status, Hud.Quest, Hud.Dock
    if status.Visible then
        local shift = Vector2.new(status.AbsolutePosition.X - M, 0)
        for _, piece in status:GetChildren() do
            add(piece, shift)
        end
    end
    if quest.Visible then
        local shift = Vector2.new(quest.AbsolutePosition.X + quest.AbsoluteSize.X - (width - M), 0)
        for _, piece in quest:GetChildren() do
            add(piece, shift)
        end
    end
    if dock.Visible then
        add(dock, Vector2.new(0, dock.AbsolutePosition.Y + dock.AbsoluteSize.Y - (height - M)))
    end
    return boxes
end

-- the lowest a piece spanning x0 to x1, hanging from y, may reach and stay clear of the boxes
local function floorUnder(x0, x1, y, boxes)
    local floor = gui.AbsoluteSize.Y
    local gap = SIDE_GAP * HudMetrics.scale()
    for _, box in boxes do
        if x0 < box[2].X + gap and x1 > box[1].X - gap and box[2].Y > y then
            floor = math.min(floor, box[1].Y - gap)
        end
    end
    return floor
end

local laidOut = true
local function layoutTop()
    laidOut = true
    local scale = HudMetrics.scale()
    local boxes = sideBoxes()
    local centre = gui.AbsoluteSize.X / 2
    local function fits(size, y)
        return y + size.Y <= floorUnder(centre - size.X / 2, centre + size.X / 2, y, boxes)
    end
    local pieces = {}
    for piece in bannerPieces do
        if (piece.Parent == Hud.Banner or piece.Parent == bannerWaiting) and piece.Visible then
            table.insert(pieces, piece)
        end
    end
    table.sort(pieces, function(a, b)
        return a.LayoutOrder < b.LayoutOrder
    end)
    -- the Banner's pieces, in order, while they fit (the first always shows)
    local top = Hud.Banner.AbsolutePosition.Y
    local kept, feet = {}, {}
    for _, piece in pieces do
        local y = if #kept == 0 then top else feet[#kept] + STACK_GAP * scale
        if #kept > 0 and piece.LayoutOrder >= 0 and not fits(piece.AbsoluteSize, y) then
            break
        end
        table.insert(kept, piece)
        table.insert(feet, y + piece.AbsoluteSize.Y)
    end
    -- the notification under them: while it shows and doesn't fit, the latest that may wait makes room
    local notice = Hud.Notice
    local bleed = (notice:GetAttribute("Bleed") or 0) * scale
    local size = notice.AbsoluteSize - Vector2.new(2, 2) * bleed -- (its visible window, without the margin for its glow)
    local function noticeTop()
        return if #kept > 0 then feet[#kept] + STACK_GAP * scale else top
    end
    if notice.AbsoluteSize.Y > 1 then
        while #kept > 0 and kept[#kept].LayoutOrder >= 0 and not fits(size, noticeTop()) do
            table.remove(kept)
            table.remove(feet)
        end
    end
    local keep = {}
    for _, piece in kept do
        keep[piece] = true
    end
    for piece in bannerPieces do
        if piece.Parent == Hud.Banner or piece.Parent == bannerWaiting then
            local home = if keep[piece] or not piece.Visible then Hud.Banner else bannerWaiting
            if piece.Parent ~= home then
                piece.Parent = home
            end
        end
    end
    -- what it holds may keep a margin round itself for its glow (its "Bleed", in its own units): the region rises by that much,
    -- so the notification's visible edge, not its margin, is what sits on the line (the profile's and the QUEST panel's top)
    local foot = noticeTop() - bleed
    local frame = openWindowFrame
    if frame and frame.Visible and notice.AbsoluteSize.Y > 1 and foot + notice.AbsoluteSize.Y > frame.AbsolutePosition.Y then
        local bottom = frame.AbsolutePosition.Y + frame.AbsoluteSize.Y - 12 * scale -- over the window's lowest part
        -- ... or over its title band, whichever hides fewer of the window's buttons (2026-11-24: on a phone a window fills the screen and its main button, the beta gift's
        -- GREAT!, sits at its foot: the notice lay over it for the few seconds it shows). Ties keep the foot.
        local across = notice.AbsoluteSize
        local left = gui.AbsoluteSize.X / 2 - across.X / 2
        local titleTop = frame.AbsolutePosition.Y + 4 * scale
        local function covered(top)
            local n = 0
            for _, d in frame:GetDescendants() do
                if d:IsA("GuiButton") and d.Visible and d.Active and d.AbsoluteSize.X > 1 then
                    local at, size = d.AbsolutePosition, d.AbsoluteSize
                    if at.X < left + across.X and at.X + size.X > left and at.Y < top + across.Y and at.Y + size.Y > top
                        and at.Y + size.Y > frame.AbsolutePosition.Y and at.Y < frame.AbsolutePosition.Y + frame.AbsoluteSize.Y then
                        n += 1
                    end
                end
            end
            return n
        end
        if covered(titleTop) < covered(bottom - across.Y) then
            notice.AnchorPoint = Vector2.new(0.5, 0)
            notice.Position = UDim2.new(0.5, 0, 0, titleTop)
            return
        end
        notice.AnchorPoint = Vector2.new(0.5, 1)
        notice.Position = UDim2.new(0.5, 0, 0, bottom)
        return
    end
    notice.AnchorPoint = Vector2.new(0.5, 0)
    notice.Position = UDim2.new(0.5, 0, 0, foot)
end
local function placeNotice() -- (once a frame at most, whatever asked)
    if laidOut then
        laidOut = false
        task.defer(layoutTop)
    end
end
local function addBannerPiece(piece)
    if bannerPieces[piece] or not piece:IsA("GuiObject") then
        return
    end
    bannerPieces[piece] = true
    for _, property in { "Visible", "AbsoluteSize", "LayoutOrder" } do
        piece:GetPropertyChangedSignal(property):Connect(placeNotice)
    end
    placeNotice()
end
Hud.Banner.ChildAdded:Connect(addBannerPiece)
Hud.Banner.ChildRemoved:Connect(placeNotice)
for _, piece in { Hud.Banner, Hud.Notice, Hud.Status, Hud.Quest, Hud.Dock } do
    piece:GetPropertyChangedSignal("AbsoluteSize"):Connect(placeNotice)
    piece:GetPropertyChangedSignal("Visible"):Connect(placeNotice)
end
Hud.Status:GetPropertyChangedSignal("AbsolutePosition"):Connect(placeNotice)
Hud.Quest:GetPropertyChangedSignal("AbsolutePosition"):Connect(placeNotice)
Hud.Notice:GetAttributeChangedSignal("Bleed"):Connect(placeNotice)
HudMetrics.Changed:Connect(placeNotice)

-- ---------- the right column's foot ----------
-- The quest panel and the air leaps under it go down the right side only as far as they stay clear of the touch buttons
-- round the jump button (TouchActions) and of the jump button itself: on a phone the quest panel, unfolded for a new quest,
-- pushed the air leaps onto the lotus and Dash buttons (phone pass, 2026-11-16). A piece that would reach them waits (the air
-- leaps, while the panel is unfolded) and comes back when there is room; the first piece always shows.
local columnWaiting = Instance.new("Frame")
columnWaiting.Name = "QuestWaiting"
columnWaiting.BackgroundTransparency = 1
columnWaiting.Visible = false
columnWaiting.Parent = gui
applyHudScale(columnWaiting)
local columnPieces = setmetatable({}, { __mode = "k" })
local touchWatched = setmetatable({}, { __mode = "k" })
local columnLaid = true

-- the lowest the right column may reach (pixels, the HUD's): over the touch buttons and the jump button that stand under it
local function columnFloor(widest)
    local scale = HudMetrics.scale()
    local right = gui.AbsoluteSize.X - M -- the column's right edge at rest
    local floor = gui.AbsoluteSize.Y
    -- the buttons it keeps clear of: the touch actions shown, and Roblox's jump button
    local blockers = {}
    local touchGui = playerGui:FindFirstChild("TouchActions")
    if touchGui and touchGui.Enabled then
        for _, button in touchGui:GetChildren() do
            if button:IsA("GuiButton") and button.Visible then
                table.insert(blockers, button)
            end
        end
    end
    local roblox = playerGui:FindFirstChild("TouchGui")
    local jump = roblox and roblox.Enabled and roblox:FindFirstChild("JumpButton", true)
    if jump and jump:IsA("GuiObject") and jump.Visible then
        table.insert(blockers, jump)
    end
    for _, button in blockers do
        local at, size = button.AbsolutePosition, button.AbsoluteSize
        if at.X < right + SIDE_GAP * scale and at.X + size.X > right - widest - SIDE_GAP * scale then
            floor = math.min(floor, at.Y - SIDE_GAP * scale)
        end
    end
    return floor
end
function Hud.rightColumnFloor()
    return columnFloor(Hud.rightColumnWidth() * HudMetrics.scale())
end

local function layoutColumn()
    columnLaid = true
    local scale = HudMetrics.scale()
    local quest = Hud.Quest
    local pieces = {}
    for piece in columnPieces do
        if (piece.Parent == quest or piece.Parent == columnWaiting) and piece.Visible then
            table.insert(pieces, piece)
        end
    end
    table.sort(pieces, function(a, b)
        return a.LayoutOrder < b.LayoutOrder
    end)
    local widest = 0
    for _, piece in pieces do
        widest = math.max(widest, piece.AbsoluteSize.X)
    end
    local floor = columnFloor(widest)
    local y = quest.AbsolutePosition.Y
    local keep = {}
    for index, piece in pieces do
        local top = if index == 1 then y else y + STACK_GAP * scale
        if index > 1 and top + piece.AbsoluteSize.Y > floor then
            break
        end
        keep[piece] = true
        y = top + piece.AbsoluteSize.Y
    end
    for piece in columnPieces do
        if piece.Parent == quest or piece.Parent == columnWaiting then
            local home = if keep[piece] or not piece.Visible then quest else columnWaiting
            if piece.Parent ~= home then
                piece.Parent = home
            end
        end
    end
end
local function placeColumn()
    if columnLaid then
        columnLaid = false
        task.defer(layoutColumn)
    end
end
Hud.Quest.ChildAdded:Connect(function(piece)
    if piece:IsA("GuiObject") and not columnPieces[piece] then
        columnPieces[piece] = true
        for _, property in { "Visible", "AbsoluteSize", "LayoutOrder" } do
            piece:GetPropertyChangedSignal(property):Connect(placeColumn)
        end
    end
    placeColumn()
end)
Hud.Quest.ChildRemoved:Connect(placeColumn)
Hud.Quest:GetPropertyChangedSignal("AbsoluteSize"):Connect(placeColumn)
HudMetrics.Changed:Connect(placeColumn)
-- the touch buttons come and go (Strike near a guardian, Dash on landing ...): each one shown or hidden lays the column out again
local function watchTouch(touchGui)
    if touchWatched[touchGui] or not touchGui:IsA("ScreenGui") then
        return
    end
    touchWatched[touchGui] = true
    local function watch(button)
        if button:IsA("GuiObject") then
            button:GetPropertyChangedSignal("Visible"):Connect(placeColumn)
            button:GetPropertyChangedSignal("AbsolutePosition"):Connect(placeColumn)
        end
    end
    for _, button in touchGui:GetDescendants() do
        watch(button)
    end
    touchGui.DescendantAdded:Connect(watch)
    placeColumn()
end
playerGui.ChildAdded:Connect(function(child)
    if child.Name == "TouchActions" or child.Name == "TouchGui" then
        watchTouch(child)
    end
end)
for _, name in { "TouchActions", "TouchGui" } do
    local child = playerGui:FindFirstChild(name)
    if child then
        watchTouch(child)
    end
end
-- The row beside Roblox's own buttons: the counters and the round buttons share one middle line (placeTopRow, under the
-- compact screens' code), whatever their own heights.
Hud.Currency = region("Currency", Vector2.new(0.5, 0.5), UDim2.new(0.5, 0, 0, 0), Enum.FillDirection.Horizontal,
    Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center, 8, topGui)
Hud.TopRight = region("TopRight", Vector2.new(1, 0.5), UDim2.new(1, -M, 0, 0), Enum.FillDirection.Horizontal,
    Enum.HorizontalAlignment.Right, Enum.VerticalAlignment.Center, 8, topGui)

-- The menu down the left, under the profile: its toggle (Hud's "the menu's toggle", below), then the Rail in a holder it slides
-- out of. On a big screen the toggle is a bar over the tiles; on a phone, a tile at the start of their row.
local menu = Instance.new("Frame")
menu.Name = "Menu"
menu.BackgroundTransparency = 1
menu.AutomaticSize = Enum.AutomaticSize.XY
menu.Size = UDim2.new()
menu.LayoutOrder = 20
menu.Parent = Hud.Status
local menuList = UiKit.list(menu, { Padding = UDim.new(0, 8) })
local railHolder = Instance.new("Frame") -- sized to the Rail (placeRail): the Rail slides off the screen's edge inside it
railHolder.Name = "RailHolder"
railHolder.BackgroundTransparency = 1
railHolder.LayoutOrder = 2
railHolder.Parent = menu
local rail = Instance.new("Frame")
rail.Name = "Rail"
rail.BackgroundTransparency = 1
rail.AutomaticSize = Enum.AutomaticSize.XY
rail.Size = UDim2.new()
rail.Parent = railHolder
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
-- The counters keep to the room the row leaves them, between Roblox's own buttons (GuiService.TopbarInset: where the row's
-- room for a game starts) and the round buttons at the right: centred on the screen if they fit there, moved over if not, and
-- on a screen too narrow for them they shrink, never under MIN_COUNTERS of their size, instead of running under either.
local TOP_GAP = 8
local MIN_COUNTERS = 0.8
local countersFit = Instance.new("UIScale") -- on the strip, inside the region's own scale
countersFit.Name = "Fit"
local function placeTopRow()
    -- the row stays inside Roblox's top bar, whatever the screen: on a big screen the HUD's scale (1.28 on an iPad) made the
    -- round buttons taller than the bar, and their badges ran off the top of the screen. So the row's own scale stops where its
    -- buttons fill the bar less TOP_ROW_TOP above and below.
    local bar = GuiService:GetGuiInset().Y
    local most = if bar > 0 then (bar - 2 * TOP_ROW_TOP) / TOP_BUTTON[compact == true] else math.huge
    local scale = math.min(HudMetrics.scale(), most)
    for _, region in { Hud.Currency, Hud.TopRight } do
        local regionScale = region:FindFirstChildOfClass("UIScale")
        if regionScale and math.abs(regionScale.Scale - scale) > 0.001 then
            regionScale.Scale = scale
        end
    end
    local middle = TOP_ROW_TOP + TOP_BUTTON[compact == true] * scale / 2
    Hud.TopRight.Position = UDim2.new(1, -M, 0, middle)
    local strip = Hud.Currency:FindFirstChild("Counters")
    local view = topGui.AbsoluteSize.X
    if not (strip and view > 0) then
        Hud.Currency.Position = UDim2.new(0.5, 0, 0, middle)
        return
    end
    countersFit.Parent = strip
    local left = GuiService.TopbarInset.Min.X + TOP_GAP * scale
    local topRight = Hud.TopRight
    local right = (if topRight.AbsoluteSize.X > 1 then view - M - topRight.AbsoluteSize.X else view - M) - TOP_GAP * scale
    local width = strip.AbsoluteSize.X / countersFit.Scale
    if width <= 0 then
        return
    end
    local fit = math.clamp((right - left) / width, MIN_COUNTERS, 1)
    if math.abs(fit - countersFit.Scale) > 0.005 then
        countersFit.Scale = fit
    end
    width *= fit
    local centre = math.clamp(view / 2, left + width / 2, math.max(left + width / 2, right - width / 2))
    Hud.Currency.Position = UDim2.new(0, math.round(centre), 0, middle)
end
local topRowQueued = false
local function queueTopRow()
    if not topRowQueued then
        topRowQueued = true
        task.defer(function()
            topRowQueued = false
            placeTopRow()
        end)
    end
end
HudMetrics.Changed:Connect(queueTopRow)
Hud.CompactChanged:Connect(queueTopRow)
Hud.Currency:GetPropertyChangedSignal("AbsoluteSize"):Connect(queueTopRow)
Hud.TopRight:GetPropertyChangedSignal("AbsoluteSize"):Connect(queueTopRow)
GuiService:GetPropertyChangedSignal("TopbarInset"):Connect(queueTopRow)
topGui:GetPropertyChangedSignal("AbsoluteSize"):Connect(queueTopRow)
placeTopRow()

HudMetrics.keepReadable(gui)
HudMetrics.keepReadable(topGui)
HudMetrics.keepReadable(windowGui, HudMetrics.windowScale) -- (a window is drawn at its own scale: Hud.window)
HudMetrics.keepReadable(noticeGui) -- (the notification: its kind's word was drawn 8.9 px on a phone)

-- On a phone the menu runs along under the profile as icons alone: the thumbstick has the screen's lower left. A tile made
-- with KeepWord (the Shop) keeps its word there, in gold, and its icon moves up over it, as on the desktop's tiles.
local PHONE_TILE = 56 -- 56 at a phone's scale (0.8) is 45 pixels: a thumb's 44 (UI overhaul 2026-11-15; the audit of 2026-11-11 found 35)
local WORD_HEIGHT, WORD_INSET, ICON_TOP = 14, 4, 6 -- (14: a phone draws the word at 14, to stay 11 px on the screen) -- a tile's word: its height and its inset from the foot; the icon's from the top
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
local placeMenu -- (the menu's toggle, below: it follows the Rail's layout)
local watchBadge -- (and every tile's badge, for its dot)

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
    local setBadge = addBadge(button)
    if watchBadge then
        watchBadge(button)
    end
    if placeMenu then
        placeMenu()
    end
    return button, setBadge
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
-- While one is open the quest panel, the inventory bar and the top centre's pieces step aside, so nothing shows through or
-- round it, and the
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
    Hud.Banner.Visible = not open -- (its pieces showed round a window's edge: the Merchant's line beside the Hatching Sanctum)
    -- on a phone no window clears the left column (the profile and the menu): each lay over part of the menu's tiles (the
    -- Hatching Sanctum's, beside the altar, over three of them). There the column steps aside too while one is open.
    Hud.Status.Visible = not (open and Hud.isCompact())
end
Hud.CompactChanged:Connect(stepAside)
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
    local wanted = props.Size -- (what it asks for; win.resize changes it: a window with a longer page than its first, the Rewards' goals)
    local function fitToScreen()
        local view, scale = HudMetrics.viewport(), windowScale()
        local room = (view.Y - GuiService:GetGuiInset().Y - WINDOW_MARGIN) / scale
        local across = (view.X - WINDOW_MARGIN) / scale
        frame.Size = UDim2.fromOffset(math.min(wanted.X, across), math.min(wanted.Y, room))
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
    -- asks for another height (as tall as the screen allows), e.g. when a taller page is shown; the width stays
    function win.resize(height)
        wanted = Vector2.new(props.Size.X, height)
        place()
    end
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

-- ---------- the inventory bar ----------
-- The bottom of the screen's main piece (the owner, 2026-11-16: "remove the cultivation bar and replace it with the box for
-- inventory weapon"): a row of item slots at the bottom centre, as other Roblox games' hotbars. Each slot is a raised tile with its
-- number's key in its top left corner and its item's name under it; the item in hand lights the slot (the Active tone) and a small
-- EQUIPPED mark sits on its foot (on its top edge it covered the key). Slot 1 holds the weapon (CombatController); more slots can be added later, each with its own
-- number key. Cultivating has no button here: E (or the touch screens' lotus button, TouchActions) starts and stops it.
--   Hud.Inventory.addSlot(index, opts) -> slot     opts.OnPress (the slot pressed), opts.Name
--     slot.Button, slot.Holder (where the item's picture goes), slot.setItem(name, picture), slot.setEquipped(on),
--     slot.setEmpty(word, hint)   no item: a quiet slot with `word` in it and `hint` under it
local SLOT = 64          -- a slot's side: 51 px at a phone's 0.8, a thumb's 44 and more
local SLOT_GAP = 10
local NAME_HEIGHT, NAME_GAP = 15, 9 -- the item's name under its slot (the gap: room for the EQUIPPED mark over the slot's foot)
local inventory = Instance.new("Frame")
inventory.Name = "Inventory"
inventory.BackgroundTransparency = 1
inventory.AutomaticSize = Enum.AutomaticSize.X
inventory.Size = UDim2.fromOffset(0, SLOT + NAME_GAP + NAME_HEIGHT)
inventory.LayoutOrder = 30
inventory.Parent = Hud.Dock
UiKit.list(inventory, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, SLOT_GAP), HorizontalAlignment = Enum.HorizontalAlignment.Center })
Hud.Inventory = {}

function Hud.Inventory.addSlot(index, opts)
    opts = opts or {}
    local holder = Instance.new("Frame")
    holder.Name = opts.Name or ("Slot" .. index)
    holder.BackgroundTransparency = 1
    holder.Size = UDim2.fromOffset(SLOT, SLOT + NAME_GAP + NAME_HEIGHT)
    holder.LayoutOrder = index
    holder.Parent = inventory
    local button = UiKit.button({ Name = "Button", Text = "", Tone = "Tile", Size = UDim2.fromOffset(SLOT, SLOT), Parent = holder })
    button:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, UiTheme.Radius.Card)
    button:SetAttribute("EdgeThickness", UiTheme.Stroke.Button)
    local picture = Instance.new("Frame") -- the item's picture (a ViewportFrame or an image), inset from the tile's edge
    picture.Name = "Item"
    picture.BackgroundTransparency = 1
    picture.AnchorPoint = Vector2.new(0.5, 0.5)
    picture.Position = UDim2.fromScale(0.5, 0.5)
    picture.Size = UDim2.new(1, -4, 1, -4)
    picture.ZIndex = 3
    picture.Parent = button
    local empty = UiKit.boldLabel({ -- what an empty slot says inside itself
        Name = "Empty", TextSize = 11, TextColor3 = UiTheme.Colors.Muted, TextXAlignment = Enum.TextXAlignment.Center, TextWrapped = true,
        Size = UDim2.fromScale(1, 1), ZIndex = 4, Visible = false, Parent = button,
    })
    -- its number's key, in its top left corner (keyboards only: UiKit.keycap hides itself on a touch screen)
    local key = UiKit.keycap(tostring(index))
    key.AnchorPoint = Vector2.new(0, 0)
    key.Position = UDim2.fromOffset(-4, -4)
    key.Size = UDim2.fromOffset(20, 20)
    key.TextSize = 12
    key.ZIndex = 6
    key.Parent = button
    local name = UiKit.boldLabel({ -- wider than the slot, centred under it: a hint for an empty slot is a few words
        Name = "ItemName", TextSize = 11, TextXAlignment = Enum.TextXAlignment.Center, AnchorPoint = Vector2.new(0.5, 1),
        Position = UDim2.fromScale(0.5, 1), Size = UDim2.new(1, 96, 0, NAME_HEIGHT), TextTruncate = Enum.TextTruncate.AtEnd, Parent = holder,
    })
    -- EQUIPPED, on the slot's foot while the item is in hand
    local mark = UiKit.tag("Equipped", Color3.fromRGB(120, 255, 236))
    mark.Name = "EquippedMark"
    mark.AnchorPoint = Vector2.new(0.5, 0.5)
    mark.Position = UDim2.fromScale(0.5, 1)
    mark.BackgroundColor3 = Color3.fromRGB(14, 112, 118)
    mark.BackgroundTransparency = 0
    mark.TextColor3 = Color3.new(1, 1, 1)
    mark.ZIndex = 7
    mark.Visible = false
    mark.Parent = button
    local slot = { Button = button, Holder = picture }
    function slot.setItem(text, item)
        empty.Visible = false
        picture:ClearAllChildren()
        if item then
            item.AnchorPoint = Vector2.new(0.5, 0.5)
            item.Position = UDim2.fromScale(0.5, 0.5)
            item.Size = UDim2.fromScale(1, 1)
            item.ZIndex = 3
            item.Parent = picture
        end
        name.Text = text or ""
        name.TextColor3 = UiTheme.Colors.Text
        button:SetAttribute("Tone", if mark.Visible then "Active" else "Tile")
    end
    function slot.setEmpty(word, hint)
        picture:ClearAllChildren()
        empty.Text = word or ""
        empty.Visible = true
        name.Text = hint or ""
        name.TextColor3 = UiTheme.Colors.Highlight
        mark.Visible = false
        button:SetAttribute("Tone", "Quiet")
    end
    function slot.setEquipped(on)
        mark.Visible = on
        if not empty.Visible then
            button:SetAttribute("Tone", if on then "Active" else "Tile")
        end
    end
    if opts.OnPress then
        button.Activated:Connect(opts.OnPress)
    end
    return slot
end

-- ---------- what rises over the inventory bar ----------
-- The buttons and labels stacked over the bar (the breakthrough, the station's bonus, "cultivating") are laid out here, all on the
-- bar's centre line (the screen's), so the column keeps one middle whoever adds to it, with one gap between rows. Each in its own
-- row, bottom up in their order; but where that column would rise into the menu's row (a phone's short screen), the buttons share
-- one row instead, their group still on that line (an OwnRow piece keeps its own row).
--   Hud.Inventory.addPill(object, order, opts)
--     opts.Width(height)   its natural width (its words and margins), in the HUD's units
--     opts.MinWidth        never narrower than this
--     opts.Height          a fixed height (a label); a button takes PILL_HEIGHT and a pill's shape
--     opts.OwnRow          never shares a row
--   Hud.Inventory.layoutPills()  lays them out again (a controller's words changed size)
local PILL_GAP = 8 -- the Dock region's own gap
local PILL_HEIGHT = { [true] = 56, [false] = 48 } -- a button pill: 56 on a phone is 45 pixels at its 0.8
local PILL_ROOM = 420 -- the column's frame: as wide as its widest row may be
local pills = {}
local pillHolder = Instance.new("Frame")
pillHolder.Name = "Pills"
pillHolder.BackgroundTransparency = 1
pillHolder.LayoutOrder = 20
pillHolder.Visible = false
pillHolder.Parent = Hud.Dock
local pillWaiting = Instance.new("Frame") -- where a line waits while there is no room for it (hidden)
pillWaiting.Name = "PillsWaiting"
pillWaiting.BackgroundTransparency = 1
pillWaiting.Visible = false
pillWaiting.Parent = Hud.Dock

-- whether a column of `height` and `width` (the HUD's units) over the bar would reach into the menu's row, on the screen as it is
local function columnMeetsRail(height, width)
    local rail, room = Hud.Rail, Hud.Dock.Parent
    if not (Hud.Status.Visible and rail.Parent.Visible and rail.AbsoluteSize.Y > 1 and room:IsA("GuiBase2d")) then
        return false
    end
    local scale = HudMetrics.scale()
    -- where the column will stand once the Dock is at rest (it may still be arriving): the Dock hangs M over the screen's foot
    local foot = room.AbsolutePosition.Y + room.AbsoluteSize.Y - M
    local top = foot - (inventory.Size.Y.Offset + PILL_GAP + height) * scale
    local centre = room.AbsolutePosition.X + room.AbsoluteSize.X / 2
    local left, right = centre - width / 2 * scale, centre + width / 2 * scale
    -- the menu's place at rest: the Status region's offset from its home is the arrival still under way
    local shift = Hud.Status.AbsolutePosition.X - (room.AbsolutePosition.X + M)
    local railLeft = rail.AbsolutePosition.X - shift
    local railRight, railBottom = railLeft + rail.AbsoluteSize.X, rail.AbsolutePosition.Y + rail.AbsoluteSize.Y
    return top < railBottom + PILL_GAP * scale and left < railRight and right > railLeft
end

local function layoutPills()
    local buttonHeight = PILL_HEIGHT[compact == true]
    local shown = {}
    for _, pill in pills do
        if pill.object.Visible then
            pill.h = pill.opts.Height or buttonHeight
            pill.w = math.max(pill.opts.MinWidth or 0, pill.opts.Width(pill.h))
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
    local function measure(rows)
        local height, widest = -PILL_GAP, 0
        for _, row in rows do
            local rowHeight, rowWidth = 0, -PILL_GAP
            for _, pill in row do
                rowHeight = math.max(rowHeight, pill.h)
                rowWidth += pill.w + PILL_GAP
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
    if #rows > 1 and columnMeetsRail(height, widest) then
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
    -- and if even that reaches the menu's row (a short phone: the breakthrough over the "cultivating" line), the lines (a
    -- label's row) wait and the buttons keep their place; they come back when there is room (phone pass, 2026-11-16)
    local waiting = {}
    while #rows > 1 and columnMeetsRail(height, select(2, measure(rows))) do
        local lineRow = nil
        for index = #rows, 1, -1 do
            if rows[index][1].opts.Height then
                lineRow = index
                break
            end
        end
        if not lineRow then
            break
        end
        for _, pill in table.remove(rows, lineRow) do
            waiting[pill] = true
        end
        height = measure(rows)
    end
    for _, pill in shown do
        local home = if waiting[pill] then pillWaiting else pillHolder
        if pill.object.Parent ~= home then
            pill.object.Parent = home
        end
    end
    local centre = PILL_ROOM / 2
    local y = 0
    for _, row in rows do
        local rowHeight, rowWidth = 0, -PILL_GAP
        for _, pill in row do
            rowHeight = math.max(rowHeight, pill.h)
            rowWidth += pill.w + PILL_GAP
        end
        local x = centre - rowWidth / 2
        for _, pill in row do
            local object = pill.object
            object.AnchorPoint = Vector2.new(0.5, 0.5)
            object.Position = UDim2.fromOffset(x + pill.w / 2, y + rowHeight / 2)
            object.Size = UDim2.fromOffset(pill.w, pill.h)
            if not pill.opts.Height then
                UiKit.pillShape(object, pill.h)
            end
            x += pill.w + PILL_GAP
        end
        y += rowHeight + PILL_GAP
    end
    pillHolder.Size = UDim2.fromOffset(PILL_ROOM, height)
end

function Hud.Inventory.addPill(object, order, opts)
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
Hud.Inventory.layoutPills = layoutPills
Hud.Inventory.pillHeight = function()
    return PILL_HEIGHT[compact == true]
end
HudMetrics.Changed:Connect(function()
    task.defer(layoutPills)
end)
Hud.CompactChanged:Connect(function()
    task.defer(layoutPills)
end)
Hud.Rail:GetPropertyChangedSignal("AbsoluteSize"):Connect(function()
    task.defer(layoutPills)
end)
Hud.Status:GetPropertyChangedSignal("Visible"):Connect(function()
    task.defer(layoutPills)
end)

-- ---------- the right column's width ----------
-- The quest panel and the air leaps under it (QinggongController) read as one column: one width, one right edge.
local RIGHT_COLUMN = { [true] = 236, [false] = 280 }
function Hud.rightColumnWidth()
    return RIGHT_COLUMN[compact == true]
end

-- ---------- the menu's toggle ----------
-- The owner, 2026-11-16: "Toggleable UI for all the Icons in the left side". The toggle slides every tile of the menu off the
-- screen's left edge and back: on a big screen it is a slim MENU bar over the tiles (its key, M, hinted at its right end), on a
-- phone a tile at the start of their row (a thumb's 45 px, as theirs). Its chevron points the way the tiles will go. While they
-- are away, a dot on the toggle says one of them has a badge (a new pet, a reward to claim ...), and it jumps when one arrives.
-- M, or a gamepad's d-pad left, does the same. The choice is the player's setting MenuHidden (server/Data/Settings): kept for the
-- session and the next. While the tiles are away the menu takes no room: the top centre, the inventory bar's lines and the
-- notifications keep clear of the toggle alone.
local MENU_BAR = 34 -- the bar's height on a big screen (43.5 px on an iPad, at its 1.28: a thumb's)
local MENU_KEYS = { [Enum.KeyCode.M] = true, [Enum.KeyCode.DPadLeft] = true }
local SLIDE_OUT = TweenInfo.new(0.24, Enum.EasingStyle.Quint, Enum.EasingDirection.In)
local SLIDE_IN = TweenInfo.new(0.34, Enum.EasingStyle.Quint, Enum.EasingDirection.Out)
local localPlayer = Players.LocalPlayer
local menuToggle = UiKit.button({
    Name = "MenuToggle", Text = "", Tone = "Tile", LayoutOrder = 1, ZIndex = 3, Size = UDim2.fromOffset(2 * RAIL_TILE + 8, MENU_BAR),
    Parent = menu,
})
menuToggle:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, UiTheme.Radius.Card)
menuToggle:SetAttribute("EdgeThickness", UiTheme.Stroke.Button)
-- the chevron: two bars meeting in a point ("<" while the tiles show), in an unturned frame it turns round
local chevron = Instance.new("Frame")
chevron.Name = "Chevron"
chevron.BackgroundTransparency = 1
chevron.AnchorPoint = Vector2.new(0.5, 0.5)
chevron.Size = UDim2.fromOffset(16, 16)
chevron.ZIndex = 4
chevron.Parent = menuToggle
local chevronScale = Instance.new("UIScale")
chevronScale.Parent = chevron
for _, arm in { { -3.5, -45 }, { 3.5, 45 } } do
    local bar = Instance.new("Frame")
    bar.Name = "Arm"
    bar.BorderSizePixel = 0
    bar.BackgroundColor3 = UiTheme.Colors.Highlight
    bar.AnchorPoint = Vector2.new(0.5, 0.5)
    bar.Position = UDim2.new(0.5, 0, 0.5, arm[1])
    bar.Size = UDim2.fromOffset(11, 3.5)
    bar.Rotation = arm[2]
    bar.ZIndex = 4
    bar.Parent = chevron
    UiKit.corner(bar, 2)
end
local menuWord = UiKit.label({
    Name = "Word", Font = "Heavy", Text = "MENU", TextSize = 12, TextColor3 = UiTheme.Colors.Text, AnchorPoint = Vector2.new(0.5, 0.5),
    Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.new(1, -64, 1, 0), TextXAlignment = Enum.TextXAlignment.Center, ZIndex = 4,
    Parent = menuToggle,
})
UiKit.outline(menuWord, 1.5)
local menuKey = UiKit.keycapOn(menuToggle, "M")
menuKey.ZIndex = 4
-- the dot: where the tiles' badges sit (BADGE_OUT), in the badges' own colours
local dot = Instance.new("Frame")
dot.Name = "BadgeDot"
dot.BorderSizePixel = 0
dot.AnchorPoint = Vector2.new(1, 0)
dot.Position = UDim2.new(1, BADGE_OUT.X, 0, -BADGE_OUT.Y)
dot.Size = UDim2.fromOffset(16, 16)
dot.BackgroundColor3 = UiTheme.Colors.Accent
dot.Visible = false
dot.ZIndex = 5
dot.Parent = menuToggle
UiKit.corner(dot, 8)
UiKit.stroke(dot, UiTheme.Colors.Outline, 0.2, 1.5)
local dotScale = Instance.new("UIScale")
dotScale.Parent = dot

local menuHidden = false
local menuTween = nil

-- the tiles' size, in the HUD's units, as layoutRail lays them out
local function railSize()
    local count = 0
    for _, button in rail:GetChildren() do
        if button:IsA("GuiButton") and button.Visible then
            count += 1
        end
    end
    local gap = railGrid.CellPadding.X.Offset
    if count == 0 then
        return Vector2.zero
    elseif compact then
        return Vector2.new(count * PHONE_TILE + (count - 1) * gap, PHONE_TILE)
    end
    local rows, columns = math.ceil(count / 2), math.min(count, 2)
    return Vector2.new(columns * RAIL_TILE + (columns - 1) * gap, rows * RAIL_TILE + (rows - 1) * gap)
end
-- how far left the tiles go to be off the screen (generous: past the toggle and the screen's margin too)
local function awayOffset()
    return UDim2.fromOffset(-(railSize().X + PHONE_TILE + 2 * M + 24), 0)
end

function placeMenu()
    local size = railSize()
    railHolder.Size = UDim2.fromOffset(size.X, size.Y)
    if compact then -- a tile at the start of the row: the chevron alone, larger
        menuList.FillDirection = Enum.FillDirection.Horizontal
        menuToggle.Size = UDim2.fromOffset(PHONE_TILE, PHONE_TILE)
        chevron.Position = UDim2.fromScale(0.5, 0.5)
        chevronScale.Scale = 1.4
        menuWord.Visible = false
        menuKey.Parent = nil
    else -- a bar over the tiles, as wide as their two columns: the chevron, MENU, and the key
        menuList.FillDirection = Enum.FillDirection.Vertical
        menuToggle.Size = UDim2.fromOffset(2 * RAIL_TILE + railGrid.CellPadding.X.Offset, MENU_BAR)
        chevron.Position = UDim2.new(0, 18, 0.5, 0)
        chevronScale.Scale = 1
        menuWord.Visible = true
        menuKey.Parent = menuToggle
    end
    if menuHidden and not menuTween then
        rail.Position = awayOffset()
    end
end
Hud.CompactChanged:Connect(function()
    task.defer(placeMenu)
end)
-- (and follows the tiles: a controller may show its tile a while after making it)
rail:GetPropertyChangedSignal("AbsoluteSize"):Connect(function()
    task.defer(placeMenu)
end)

-- the dot shows while the tiles are away and one of them has a badge; it jumps when a badge arrives or changes
local function refreshDot(arrived)
    local any, color = false, UiTheme.Colors.Accent
    for _, button in rail:GetChildren() do
        local badge = button:IsA("GuiButton") and button.Visible and button:FindFirstChild("Badge")
        if badge and badge.Visible then
            any = true
            if badge.BackgroundColor3 == UiTheme.Colors.Highlight then
                color = UiTheme.Colors.Highlight
            end
        end
    end
    local show = menuHidden and any
    dot.BackgroundColor3 = color
    if show and (arrived or not dot.Visible) then
        dotScale.Scale = 1.7
        UiFx.tween(dotScale, 0.36, { Scale = 1 }, Enum.EasingStyle.Back)
    end
    dot.Visible = show
end
function watchBadge(button)
    local badge = button:FindFirstChild("Badge")
    if not badge then
        return
    end
    badge:GetPropertyChangedSignal("Visible"):Connect(function()
        refreshDot(badge.Visible)
    end)
    badge:GetPropertyChangedSignal("Text"):Connect(function()
        refreshDot(badge.Visible)
    end)
    badge:GetPropertyChangedSignal("BackgroundColor3"):Connect(function()
        refreshDot(false)
    end)
end
for _, button in rail:GetChildren() do -- (any made before this ran)
    if button:IsA("GuiButton") then
        watchBadge(button)
    end
end

-- shows or hides the tiles: sliding (animate) or at once (the saved choice arriving as the game starts)
local function setMenuHidden(hidden, animate)
    if hidden == menuHidden and animate then
        return
    end
    menuHidden = hidden
    if menuTween then
        menuTween:Cancel()
        menuTween = nil
    end
    UiFx.tween(chevron, if animate then 0.28 else 0, { Rotation = if hidden then 180 else 0 }, Enum.EasingStyle.Quad)
    menuToggle:SetAttribute("Hidden", hidden)
    if hidden then
        local away = awayOffset()
        if animate and railHolder.Visible then
            menuTween = TweenService:Create(rail, SLIDE_OUT, { Position = away })
            menuTween.Completed:Connect(function(state)
                if state == Enum.PlaybackState.Completed and menuHidden then
                    railHolder.Visible = false
                    menuTween = nil
                end
            end)
            menuTween:Play()
        else
            rail.Position = away
            railHolder.Visible = false
        end
    else
        railHolder.Visible = true
        if animate then
            menuTween = TweenService:Create(rail, SLIDE_IN, { Position = UDim2.new() })
            menuTween.Completed:Connect(function(state)
                if state == Enum.PlaybackState.Completed then
                    menuTween = nil
                end
            end)
            menuTween:Play()
        else
            rail.Position = UDim2.new()
        end
    end
    refreshDot(false)
end

local function toggleMenu()
    local hidden = not menuHidden
    setMenuHidden(hidden, true)
    Sfx.play(if hidden then "Close" else "Open")
    -- the attribute at once (it answers without waiting for the server's copy), and saved with the player's settings
    localPlayer:SetAttribute("SettingMenuHidden", hidden)
    -- (required here, not at the top: the HUD is built before the server's remotes exist, and must not wait for them)
    local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
    RemoteEvents.SettingsEvent:FireServer("MenuHidden", hidden)
end
Hud.toggleMenu = toggleMenu

menuToggle.Activated:Connect(toggleMenu)
UserInputService.InputBegan:Connect(function(input, processed)
    if processed or not MENU_KEYS[input.KeyCode] then
        return
    end
    -- (the d-pad moves a gamepad's selection while one is on a button: it is the menu's key only when nothing is selected)
    if input.KeyCode == Enum.KeyCode.DPadLeft and GuiService.SelectedObject ~= nil then
        return
    end
    toggleMenu()
end)
local menuStarted = os.clock()
localPlayer:GetAttributeChangedSignal("SettingMenuHidden"):Connect(function()
    -- (the saved choice arrives a moment after joining, while the HUD is still arriving: it takes its place without a slide)
    setMenuHidden(localPlayer:GetAttribute("SettingMenuHidden") == true, os.clock() - menuStarted > 3)
end)
placeMenu()
setMenuHidden(localPlayer:GetAttribute("SettingMenuHidden") == true, false)

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
    placeNotice()
    placeColumn()
end)

return Hud
