-- Notifications: one window at the top of the screen (Hud.Notice: under the currencies and whatever the Banner holds,
-- between the profile and the QUEST panel, drawn over any open window), shared by the whole game (the owner's pick, 2026-11-11: "Gilded Scroll").
--
--   local message = Toast.new(name, nil, seconds)   a sender: its messages stay `seconds` on the screen
--   message:show(text, kind, color)                  kind: "Success", "Warning", "Error", "Info" (default) or "Reward"
--                                                    color: the message's own colour, where it means something (a title's)
--   Toast.showing()                                  whether a notification is on the screen
--
-- Each kind has its colour, its seal and its word, so what happened reads before the sentence does.
-- One at a time, everywhere: a new notification takes the place of the one showing. One that arrives while the last has
-- been up for less than HOLD seconds waits its turn (at most QUEUE_MAX wait), so a burst is read one by one instead of
-- flickering past. The same message again doesn't show twice: the one showing counts (x2, x3) and stays a while longer.
-- It pops in, fades out, and a click or a tap puts it away.
local TweenService = game:GetService("TweenService")

local Hud = require(script.Parent:WaitForChild("Hud"))
local UiFx = require(script.Parent:WaitForChild("UiFx"))
local UiKit = require(script.Parent:WaitForChild("UiKit"))
local UiTheme = require(script.Parent:WaitForChild("UiTheme"))

local C = UiTheme.Colors

local Toast = {}
Toast.__index = Toast

local KINDS = {
    Success = { Word = "SUCCESS", Color = Color3.fromRGB(111, 212, 154) },
    Warning = { Word = "WARNING", Color = Color3.fromRGB(255, 182, 72) },
    Error = { Word = "ERROR", Color = Color3.fromRGB(255, 98, 116) },
    Info = { Word = "NOTICE", Color = Color3.fromRGB(143, 200, 255) },
    Reward = { Word = "REWARD", Color = C.Highlight },
}
local SEAL_INK = Color3.fromRGB(20, 18, 48) -- a seal's mark, dark on its colour
local IN = TweenInfo.new(0.22, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
local OUT = TweenInfo.new(0.18, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
local HOLD = 1.6      -- seconds a notification is up before the next may take its place
local QUEUE_MAX = 4   -- the most waiting: past that the oldest waiting is dropped
local SEAL = 34
local function width() -- fits between the profile and the QUEST panel
    return if Hud.isCompact() then 334 else 420
end

-- ---------- the window ----------
-- a CanvasGroup fades the whole window at once; its padding keeps the glow inside it
local group = Instance.new("CanvasGroup")
group.Name = "Notification"
group.BackgroundTransparency = 1
group.AutomaticSize = Enum.AutomaticSize.Y
group.Size = UDim2.fromOffset(width() + 6, 0)
group.LayoutOrder = 1
group.Visible = false
group.Parent = Hud.Notice
UiKit.padding(group, 3, 3)
Hud.CompactChanged:Connect(function()
    group.Size = UDim2.fromOffset(width() + 6, 0)
end)

local window = UiKit.panel({ Name = "Window", Brackets = false, AutomaticSize = Enum.AutomaticSize.Y, Size = UDim2.new(1, 0, 0, 0), Parent = group })
window.Active = true -- it takes the click that puts it away
local edge = window:FindFirstChildOfClass("UIStroke")
local pop = Instance.new("UIScale")
pop.Parent = window

-- the seal: a disc in the kind's colour with its mark
local seal = Instance.new("Frame")
seal.Name = "Seal"
seal.AnchorPoint = Vector2.new(0, 0.5)
seal.Position = UDim2.new(0, 12, 0.5, 0)
seal.Size = UDim2.fromOffset(SEAL, SEAL)
seal.BorderSizePixel = 0
seal.Parent = window
UiKit.corner(seal, 999)

local function stroke(parent, wide, tall, x, y, turn)
    local line = Instance.new("Frame")
    line.AnchorPoint = Vector2.new(0.5, 0.5)
    line.Position = UDim2.fromOffset(x, y)
    line.Size = UDim2.fromOffset(wide, tall)
    line.Rotation = turn
    line.BackgroundColor3 = SEAL_INK
    line.BorderSizePixel = 0
    line.Parent = parent
    UiKit.corner(line, 2)
    return line
end
local function mark(name)
    local frame = Instance.new("Frame")
    frame.Name = name
    frame.BackgroundTransparency = 1
    frame.Size = UDim2.fromScale(1, 1)
    frame.Visible = false
    frame.Parent = seal
    return frame
end
local function letter(name, text)
    local frame = mark(name)
    local glyph = Instance.new("TextLabel")
    glyph.BackgroundTransparency = 1
    glyph.Size = UDim2.fromScale(1, 1)
    glyph.FontFace = UiTheme.Fonts.Number
    glyph.TextSize = 22
    glyph.TextColor3 = SEAL_INK
    glyph.Text = text
    glyph.Parent = frame
    return frame
end
local marks = {}
marks.Success = mark("Check") -- a tick: a short stroke down, a long stroke up
stroke(marks.Success, 4, 10, 12, 20, -45)
stroke(marks.Success, 4, 17, 20, 17, 45)
marks.Error = mark("Cross")
stroke(marks.Error, 4, 19, 17, 17, 45)
stroke(marks.Error, 4, 19, 17, 17, -45)
marks.Warning = letter("Bang", "!")
marks.Info = letter("Note", "i")
marks.Reward = mark("Gift") -- the gold ingot, on a dark disc ringed in gold
do
    local image = Instance.new("ImageLabel")
    image.BackgroundTransparency = 1
    image.AnchorPoint = Vector2.new(0.5, 0.5)
    image.Position = UDim2.fromScale(0.5, 0.5)
    image.Size = UDim2.fromScale(0.78, 0.78)
    image.Image = UiTheme.Icons.Rewards
    image.Parent = marks.Reward
end
local sealEdge = UiKit.stroke(seal, C.Highlight, 0, 1.5)

local inner = Instance.new("Frame")
inner.Name = "Inner"
inner.BackgroundTransparency = 1
inner.AutomaticSize = Enum.AutomaticSize.Y
inner.Size = UDim2.new(1, 0, 0, 0)
inner.Parent = window
local innerPad = Instance.new("UIPadding")
innerPad.PaddingLeft = UDim.new(0, 12 + SEAL + 12)
innerPad.PaddingRight = UDim.new(0, 14)
innerPad.PaddingTop = UDim.new(0, 9)
innerPad.PaddingBottom = UDim.new(0, 10)
innerPad.Parent = inner
UiKit.list(inner, { Padding = UDim.new(0, 2) })
local word = UiKit.label({
    Name = "Kind", Font = "Number", TextSize = 11, Size = UDim2.new(1, 0, 0, 13), LayoutOrder = 1, Parent = inner,
})
local label = UiKit.label({
    Name = "Message", Font = "Strong", TextSize = 15, TextWrapped = true, AutomaticSize = Enum.AutomaticSize.Y,
    Size = UDim2.new(1, 0, 0, 0), LayoutOrder = 2, Parent = inner,
})
local count = UiKit.label({
    Name = "Count", Font = "Number", TextSize = 15, TextXAlignment = Enum.TextXAlignment.Right, AnchorPoint = Vector2.new(1, 0),
    Position = UDim2.new(1, -14, 0, 7), Size = UDim2.fromOffset(40, 16), Visible = false, Parent = window,
})

-- ---------- one at a time ----------
local current = nil -- { text, kind, color, seconds, count, at }
local waiting = {}
local token = 0     -- the showing, or the leaving, now under way

local function leave()
    token += 1
    local this = token
    current = nil
    TweenService:Create(group, OUT, { GroupTransparency = 1 }):Play()
    TweenService:Create(pop, OUT, { Scale = 0.96 }):Play()
    task.delay(OUT.Time, function()
        if token == this then
            group.Visible = false
        end
    end)
end

local present

-- its time on the screen starts (again): it leaves when that is up, unless something else has happened since
local function arm(entry)
    token += 1
    local this = token
    entry.at = os.clock()
    task.delay(HOLD, function()
        if token == this and waiting[1] then
            present(table.remove(waiting, 1))
        end
    end)
    task.delay(entry.seconds, function()
        if token == this then
            if waiting[1] then
                present(table.remove(waiting, 1))
            else
                leave()
            end
        end
    end)
end

function present(entry)
    local kind = KINDS[entry.kind]
    current = entry
    for name, frame in marks do
        frame.Visible = name == entry.kind
    end
    seal.BackgroundColor3 = if entry.kind == "Reward" then C.Well else kind.Color
    sealEdge.Transparency = if entry.kind == "Reward" then 0 else 1
    edge.Color = kind.Color:Lerp(C.Edge, 0.35)
    word.Text = kind.Word
    word.TextColor3 = kind.Color
    label.Text = entry.text
    label.TextColor3 = entry.color or C.Text
    count.Visible = false
    count.TextColor3 = kind.Color
    innerPad.PaddingRight = UDim.new(0, 14)
    UiFx.typeIn(label, 0.22)
    if not group.Visible then
        group.GroupTransparency = 1
        group.Visible = true
    end
    pop.Scale = 0.9
    TweenService:Create(group, TweenInfo.new(0.14), { GroupTransparency = 0 }):Play()
    TweenService:Create(pop, IN, { Scale = 1 }):Play()
    arm(entry)
end

-- a click or a tap puts it away (the next one waiting takes its place)
window.InputBegan:Connect(function(input)
    if input.UserInputType ~= Enum.UserInputType.MouseButton1 and input.UserInputType ~= Enum.UserInputType.Touch then
        return
    end
    if not current then
        return
    end
    if waiting[1] then
        present(table.remove(waiting, 1))
    else
        leave()
    end
end)

function Toast.new(_name, _color, seconds)
    return setmetatable({ seconds = seconds or 4 }, Toast)
end

function Toast:show(text, kind, color)
    if typeof(kind) == "Color3" then -- (the old order: a colour, no kind)
        kind, color = "Info", kind
    end
    kind = if KINDS[kind] then kind else "Info"
    text = tostring(text or "")
    if text == "" then
        return
    end
    -- the same again: counted on the one showing, never shown or queued twice
    if current and current.text == text and current.kind == kind then
        current.count += 1
        count.Text = "x" .. current.count
        count.Visible = true
        innerPad.PaddingRight = UDim.new(0, 56)
        arm(current)
        return
    end
    for _, entry in waiting do
        if entry.text == text and entry.kind == kind then
            return
        end
    end
    local entry = { text = text, kind = kind, color = color, seconds = self.seconds, count = 1, at = 0 }
    if current and os.clock() - current.at < HOLD then
        table.insert(waiting, entry)
        while #waiting > QUEUE_MAX do
            table.remove(waiting, 1)
        end
        return
    end
    present(entry)
end

function Toast.showing()
    return current ~= nil
end

return Toast
