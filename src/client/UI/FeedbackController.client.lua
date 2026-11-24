-- The Feedback window (the Feedback tile on the HUD's menu, for the public beta): the player picks what it is about (Bug,
-- Idea, Other), writes what happened or what they'd like, and sends it. Sent with it, to help fix what they found: their
-- device (touch, gamepad or keyboard), their screen size, the phone tier (Quality.Low) and this game's last few error lines
-- on their device. The server (server/Feedback/FeedbackService) checks it all, adds where they are in the game, keeps it
-- and answers; it also decides the limits (GameConfig.Feedback), which this window only mirrors.
-- On a phone the menu is one row of tiles under the profile: on the narrowest phones one more tile would run into the quest
-- column at the right, so there the tile steps out of the row; the Settings window's FEEDBACK row (SettingsController, through
-- this script's "Open" event) opens the window on every screen.
local LogService = game:GetService("LogService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextService = game:GetService("TextService")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Hud = require(script.Parent:WaitForChild("Hud"))
local HudMetrics = require(script.Parent:WaitForChild("HudMetrics"))
local Toast = require(script.Parent:WaitForChild("Toast"))
local UiKit = require(script.Parent:WaitForChild("UiKit"))
local UiTheme = require(script.Parent:WaitForChild("UiTheme"))
local Quality = require(script.Parent.Parent:WaitForChild("Performance"):WaitForChild("Quality"))

local C = UiTheme.Colors
local RULES = GameConfig.Feedback
local ERROR_LINES = 5     -- the last error lines sent along
local ERROR_LENGTH = 200  -- each cut to this many characters
local ANSWER_WAIT = 20    -- seconds to wait for the server's answer before letting them try again
local KIND_ROW = UiTheme.Height.Tab
local FOOT = UiTheme.Height.ButtonLarge
local GAP = UiTheme.Space.S
local SEND_WIDTH = 150

local camera = workspace.CurrentCamera

-- ---------- the last error lines on this device ----------
local errors = {}
local function keepError(message, messageType)
    if messageType ~= Enum.MessageType.MessageError or typeof(message) ~= "string" then
        return
    end
    local cut = utf8.len(message) and utf8.offset(message, ERROR_LENGTH + 1) -- (at a whole character)
    table.insert(errors, if cut then string.sub(message, 1, cut - 1) else string.sub(message, 1, ERROR_LENGTH))
    while #errors > ERROR_LINES do
        table.remove(errors, 1)
    end
end
pcall(function()
    for _, entry in LogService:GetLogHistory() do
        keepError(entry.message, entry.messageType)
    end
end)
LogService.MessageOut:Connect(keepError)

local function deviceKind()
    local last = UserInputService:GetLastInputType()
    if last.Name:find("^Gamepad") then
        return "Gamepad"
    elseif UiKit.usingTouch() then
        return "Touch"
    end
    return "Keyboard"
end

-- ---------- the window ----------
local toggleButton = Hud.railButton("FeedbackButton", "", "Feedback", 7)
-- its icon, drawn: a speech bubble in the menu icons' colours (cream, a dark outline, brown marks), so it needs no picture
do
    local icon = toggleButton:FindFirstChild("Icon")
    local picture = icon and icon:FindFirstChild("Image")
    if picture then
        picture:Destroy()
    end
    local CREAM, SHADE, INK, OUTLINE = Color3.fromRGB(252, 240, 206), Color3.fromRGB(240, 212, 150), Color3.fromRGB(150, 98, 52), C.Outline
    local function shape(name, position, size, z, parent)
        local f = Instance.new("Frame")
        f.Name = name
        f.BorderSizePixel = 0
        f.BackgroundColor3 = Color3.new(1, 1, 1)
        f.AnchorPoint = Vector2.new(0.5, 0.5)
        f.Position = position
        f.Size = size
        f.ZIndex = z
        f.Parent = parent or icon
        local fill = Instance.new("UIGradient")
        fill.Rotation = 90
        fill.Color = ColorSequence.new(CREAM, SHADE)
        fill.Parent = f
        return f
    end
    local tail = shape("Tail", UDim2.fromScale(0.32, 0.7), UDim2.fromScale(0.22, 0.22), 3)
    tail.Rotation = 45
    UiKit.stroke(tail, OUTLINE, 0, 2)
    local bubble = shape("Bubble", UDim2.fromScale(0.5, 0.42), UDim2.fromScale(0.88, 0.62), 4)
    UiKit.corner(bubble, 999).CornerRadius = UDim.new(0.32, 0)
    UiKit.stroke(bubble, OUTLINE, 0, 2)
    local joint = shape("Joint", UDim2.fromScale(0.32, 0.715), UDim2.fromScale(0.17, 0.06), 5) -- hides the bubble's outline over the tail
    joint:FindFirstChildOfClass("UIGradient").Color = ColorSequence.new(SHADE)
    for index = -1, 1 do
        local dot = Instance.new("Frame")
        dot.Name = "Dot"
        dot.BorderSizePixel = 0
        dot.BackgroundColor3 = INK
        dot.AnchorPoint = Vector2.new(0.5, 0.5)
        dot.Position = UDim2.fromScale(0.5 + index * 0.22, 0.42)
        dot.Size = UDim2.fromScale(0.13, 0.13)
        dot.SizeConstraint = Enum.SizeConstraint.RelativeYY
        dot.ZIndex = 6
        dot.Parent = icon
        UiKit.corner(dot, 999)
    end
end

local box -- (the text box, below)
local window = Hud.window({ Name = "FeedbackWindow", Title = "FEEDBACK", Size = Vector2.new(460, 380),
    AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
    OnClose = function()
        if box then
            box:ReleaseFocus() -- (what they wrote stays for next time, until it is sent)
        end
    end })
local body = window.Body

-- what it is about: three chips across the top
local kinds = Instance.new("Frame")
kinds.Name = "Kinds"
kinds.BackgroundTransparency = 1
kinds.Size = UDim2.new(1, 0, 0, KIND_ROW)
kinds.Parent = body
UiKit.list(kinds, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, GAP) })
local chosen = nil
local chips = {}
local WORDS = { Bug = "BUG", Idea = "IDEA", Other = "OTHER" }

-- what happened: high in the window, so a phone's on-screen keyboard doesn't cover it. A text box doesn't scroll, so it sits in
-- a scrolling well, as tall as the well at least and growing with what is written; the well follows the end while they type.
local well = Instance.new("ScrollingFrame")
well.Name = "Writing"
well.BackgroundColor3 = C.Well
well.BackgroundTransparency = 0.25
well.BorderSizePixel = 0
well.ScrollBarThickness = 4
well.ScrollBarImageColor3 = C.Edge
well.ScrollBarImageTransparency = 0.3
well.ScrollingDirection = Enum.ScrollingDirection.Y
well.CanvasSize = UDim2.new()
well.AutomaticCanvasSize = Enum.AutomaticSize.Y
well.Position = UDim2.fromOffset(0, KIND_ROW + GAP)
well.Size = UDim2.new(1, 0, 1, -(KIND_ROW + GAP + GAP + FOOT))
well.Parent = body
UiKit.corner(well, UiTheme.Radius.Button)
local wellEdge = UiKit.stroke(well, C.EdgeDim, 0.2, 1.5)
-- the page in the well: as tall as the well at least, and as tall as what is written (measured by TextService: a text box's
-- own bounds, and an auto-sized label's, stop at their parent's size)
local page = Instance.new("Frame")
page.Name = "Page"
page.BackgroundTransparency = 1
page.Parent = well
box = UiKit.textbox({
    Name = "FeedbackText", Text = "", PlaceholderText = "Tell us what happened or what you'd like…",
    MultiLine = true, TextWrapped = true, TextYAlignment = Enum.TextYAlignment.Top, TextSize = 15,
    BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Parent = page,
})
box:FindFirstChildOfClass("UIStroke").Enabled = false -- (the well has the edge)
local boxPad = box:FindFirstChildOfClass("UIPadding")
boxPad.PaddingTop = UDim.new(0, 10)
boxPad.PaddingBottom = UDim.new(0, 10)
local BOX_SIDES = boxPad.PaddingLeft.Offset + boxPad.PaddingRight.Offset
local BOX_ENDS = boxPad.PaddingTop.Offset + boxPad.PaddingBottom.Offset
local textHeight = 0
-- at least as tall as the well (a tap anywhere in it types): the window's height less its title, padding and other rows
local function fitBox()
    local wellHeight = window.Frame.Size.Y.Offset - (UiTheme.Height.TitleBar + UiTheme.Space.M + UiTheme.Pad.Window)
        - (KIND_ROW + GAP + GAP + FOOT)
    page.Size = UDim2.new(1, -well.ScrollBarThickness - 2, 0, math.max(40, wellHeight, textHeight))
end
local measuring = 0
local function measureText()
    measuring += 1
    local this = measuring
    task.spawn(function()
        -- in the window's own units (it is drawn at a scale): the well's width there is the window's less its padding
        local scale = well.AbsoluteSize.X / math.max(1, window.Frame.Size.X.Offset - UiTheme.Pad.Window * 2)
        if scale <= 0 or page.AbsoluteSize.X <= 0 then
            return
        end
        local params = Instance.new("GetTextBoundsParams")
        params.Text = box.Text .. " " -- (a space: a last empty line counts too)
        params.Font = box.FontFace
        params.Size = box.TextSize
        params.Width = page.AbsoluteSize.X / scale - BOX_SIDES
        local ok, bounds = pcall(TextService.GetTextBoundsAsync, TextService, params)
        if ok and this == measuring then
            textHeight = math.ceil(bounds.Y) + BOX_ENDS
            fitBox()
        end
    end)
end
window.Frame:GetPropertyChangedSignal("Size"):Connect(function()
    fitBox()
    measureText()
end)
fitBox()
box.Focused:Connect(function()
    wellEdge.Color = C.Edge
end)
box.FocusLost:Connect(function()
    wellEdge.Color = C.EdgeDim
end)
-- while they type at the end, the well keeps the end in sight
local function followEnd()
    if box:IsFocused() and (box.CursorPosition == -1 or box.CursorPosition > #box.Text) then
        well.CanvasPosition = Vector2.new(0, math.max(0, well.AbsoluteCanvasSize.Y - well.AbsoluteWindowSize.Y))
    end
end
well:GetPropertyChangedSignal("AbsoluteCanvasSize"):Connect(followEnd)
-- the foot: at the left the count of characters over a line of help, SEND at the right
local COUNT_HEIGHT = 16
local counter = UiKit.label({
    Name = "Counter", Font = "Strong", TextSize = 12, TextColor3 = C.Muted, Text = "0 / " .. RULES.MaxLength,
    Position = UDim2.new(0, 0, 1, -FOOT), Size = UDim2.new(1, -(SEND_WIDTH + GAP), 0, COUNT_HEIGHT), Parent = body,
})
local hint = UiKit.label({
    Name = "Hint", Font = "Strong", TextSize = 12, TextColor3 = C.Muted, TextWrapped = true,
    TextYAlignment = Enum.TextYAlignment.Center, AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, 0, 1, 0),
    Size = UDim2.new(1, -(SEND_WIDTH + GAP), 0, FOOT - COUNT_HEIGHT), Parent = body,
})
local send = UiKit.button({
    Name = "Send", Text = "SEND", TextSize = UiTheme.Text.ButtonLarge, Tone = "Primary", AnchorPoint = Vector2.new(1, 1),
    Position = UDim2.new(1, 0, 1, 0), Size = UDim2.fromOffset(SEND_WIDTH, FOOT), Parent = body,
})

local sending = false
local function length(text)
    return utf8.len(text) or #text
end
local function trimmed()
    return (string.gsub(string.gsub(box.Text, "^%s+", ""), "%s+$", ""))
end

local function refresh()
    local count = length(trimmed())
    counter.Text = count .. " / " .. RULES.MaxLength
    counter.TextColor3 = if count > 0 and count < RULES.MinLength then C.Danger else C.Muted
    local ready = chosen ~= nil and count >= RULES.MinLength and count <= RULES.MaxLength and not sending
    if sending then
        hint.Text = "Sending…"
    elseif not chosen then
        hint.Text = "Pick one: Bug, Idea or Other."
    elseif count < RULES.MinLength then
        hint.Text = "Write at least " .. RULES.MinLength .. " characters."
    else
        hint.Text = "Your device and screen size are sent too, to help us fix things."
    end
    send.Active = ready
    send:SetAttribute("Tone", if ready then "Primary" else "Quiet")
    send.Text = if sending then "SENDING" else "SEND"
end

for order, kind in RULES.Categories do
    local chip = UiKit.tab({ Name = kind, Text = WORDS[kind] or string.upper(kind), LayoutOrder = order,
        Size = UDim2.new(1 / #RULES.Categories, -GAP * (#RULES.Categories - 1) / #RULES.Categories, 1, 0), Parent = kinds })
    chips[kind] = chip
    chip.Activated:Connect(function()
        if sending then
            return
        end
        chosen = kind
        for other, button in chips do
            UiKit.selectTab(button, other == chosen)
        end
        refresh()
    end)
end

-- never longer than the limit (a paste included): cut at a whole character
box:GetPropertyChangedSignal("Text"):Connect(function()
    local text = box.Text
    if length(text) > RULES.MaxLength then
        local cut = utf8.offset(text, RULES.MaxLength + 1)
        box.Text = if cut then string.sub(text, 1, cut - 1) else string.sub(text, 1, RULES.MaxLength)
        return
    end
    measureText()
    refresh()
    followEnd()
end)

-- on a touch screen the window rises to the top while the box is being typed in, clear of the on-screen keyboard
local raisedFrom = nil
box.Focused:Connect(function()
    if not UiKit.usingTouch() then
        return
    end
    local frame = window.Frame
    raisedFrom = frame.Position
    frame.Position = UDim2.new(raisedFrom.X.Scale, raisedFrom.X.Offset, 0, 4 + frame.AbsoluteSize.Y * (frame.AnchorPoint.Y))
end)
box.FocusLost:Connect(function()
    if raisedFrom and window.isOpen() then
        window.Frame.Position = raisedFrom
    end
    raisedFrom = nil
end)

local function clear()
    box.Text = ""
    well.CanvasPosition = Vector2.zero
    chosen = nil
    for _, button in chips do
        UiKit.selectTab(button, false)
    end
    refresh()
end

local notice = Toast.new("FeedbackMessage", nil, 4)
local asked = 0 -- which sending is the latest (an answer that arrives after giving up on it is still shown)
send.Activated:Connect(function()
    if sending or not send.Active then
        return
    end
    box:ReleaseFocus()
    sending = true
    refresh()
    asked += 1
    local this = asked
    local view = camera and camera.ViewportSize or Vector2.zero
    RemoteEvents.FeedbackEvent:FireServer("Send", {
        Category = chosen,
        Text = trimmed(),
        Device = deviceKind(),
        Screen = { math.round(view.X), math.round(view.Y) },
        QualityLow = Quality.Low == true,
        Errors = table.clone(errors),
    })
    task.delay(ANSWER_WAIT, function()
        if sending and asked == this then
            sending = false
            refresh()
            notice:show("We couldn't send your feedback right now. Please try again in a minute.", "Warning")
        end
    end)
end)

RemoteEvents.FeedbackEvent.OnClientEvent:Connect(function(kind, data)
    if kind ~= "Result" or typeof(data) ~= "table" then
        return
    end
    sending = false
    if data.Ok then
        clear()
        window.close()
        notice:show("Thanks! Your feedback was sent.", "Success")
    else
        refresh()
        notice:show(if typeof(data.Message) == "string" then data.Message else "We couldn't send your feedback. Please try again.", "Warning")
    end
end)

local function openWindow()
    refresh()
    window.open()
    task.delay(0.3, measureText) -- (once it has its size: what was kept from last time)
end
window.link(toggleButton)
toggleButton.Activated:Connect(function()
    if window.isOpen() then
        window.close()
    else
        openWindow()
    end
end)
local open = Instance.new("BindableEvent") -- (the Settings window's FEEDBACK row fires it)
open.Name = "Open"
open.Event:Connect(openWindow)
open.Parent = script
refresh()

-- ---------- room in a phone's row ----------
-- Whether the row of tiles, with this one at its end, still ends clear of the right column (the quest panel and the air
-- leaps). Measured from the other tiles at rest (the row may be sliding or still arriving), in the screen's pixels.
local function fitsRow()
    if not Hud.isCompact() then
        return true -- (two columns down the left: room for any number)
    end
    local rail, status = Hud.Rail, Hud.Status
    local screen = status.Parent
    if not (rail.Parent and screen and screen:IsA("GuiBase2d")) then
        return true
    end
    local right, width = nil, 0
    for _, tile in rail:GetChildren() do
        if tile:IsA("GuiButton") and tile ~= toggleButton and tile.Visible then
            local edge = tile.AbsolutePosition.X + tile.AbsoluteSize.X - rail.AbsolutePosition.X
            if not right or edge > right then
                right, width = edge, tile.AbsoluteSize.X
            end
        end
    end
    if not right or width <= 0 then
        return true
    end
    local scale = HudMetrics.scale()
    local grid = rail:FindFirstChildOfClass("UIGridLayout")
    local gap = (if grid then grid.CellPadding.X.Offset else UiTheme.Space.S) * scale
    -- the row's left at rest: the profile column's margin, then the rail's place in the menu (after the menu's toggle)
    local railLeft = UiTheme.Margin + (rail.Parent.AbsolutePosition.X - status.AbsolutePosition.X)
    local rowRight = railLeft + right + gap + width
    local columnLeft = screen.AbsoluteSize.X - UiTheme.Margin - Hud.rightColumnWidth() * scale
    return rowRight + gap <= columnLeft
end
local placing = false
local function placeTile()
    if placing then
        return
    end
    placing = true
    task.defer(function()
        placing = false
        local fits = fitsRow()
        if toggleButton.Visible ~= fits then
            toggleButton.Visible = fits
        end
    end)
end
Hud.CompactChanged:Connect(placeTile)
HudMetrics.Changed:Connect(placeTile)
Hud.Rail:GetPropertyChangedSignal("AbsoluteSize"):Connect(placeTile)
placeTile()
