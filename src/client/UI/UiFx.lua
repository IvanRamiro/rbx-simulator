-- What makes the interface feel alive (the owner: "more interactive or more appealing in the eye of
-- players"), none of it changing the layout:
--   sweep(frame)                 a band of light crossing it
--   ripple(frame, x, y)          a ring of light spreading from a touch
--   flash(panel)                 its edge lights up and settles (something changed here)
--   scan(panel)                  a line of light running down it, as a projected window unfolds
--   edgeLight(panel)             light travelling slowly round its edge, for as long as it exists
--   attention(button)            it breathes and a band of light crosses it, while it waits to be taken
--   typeIn(label, seconds)       its text writes itself on
--   pop(guiObject, size)         its size jumps and settles (an icon that just gained something)
--   counter(label, format, opts) a number that rolls to its new value and floats the difference off
--   stagger(root)                the rows of its lists settle in one after another
-- Everything runs on TweenService or one shared Heartbeat that only runs while a number is rolling, so
-- a resting interface costs nothing.
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local UiTheme = require(script.Parent:WaitForChild("UiTheme"))

local C = UiTheme.Colors
local UiFx = {}

local function tween(instance, seconds, goal, style, direction, repeats, reverses, delay)
    local t = TweenService:Create(instance, TweenInfo.new(seconds, style or Enum.EasingStyle.Quad, direction or Enum.EasingDirection.Out,
        repeats or 0, reverses or false, delay or 0), goal)
    t:Play()
    return t
end
UiFx.tween = tween

-- A clipped layer over a frame for light to move in: a frame can't clip its own badges and ticks away.
-- Not on a frame sized by its contents: a child sized by its parent would stretch it (the quest panel ran
-- to the bottom of the screen), so light skips those.
local function lit(frame)
    return frame.AutomaticSize == Enum.AutomaticSize.None and not frame:GetAttribute("NoSheen")
end

local function lightLayer(frame)
    local layer = frame:FindFirstChild("LightLayer")
    if not layer then
        -- a rounded button's light has to stay inside its curves: only a CanvasGroup clips to them
        local round = frame:GetAttribute("RoundLight")
        layer = Instance.new(if round then "CanvasGroup" else "Frame")
        if round then
            local curve = Instance.new("UICorner")
            curve.CornerRadius = UDim.new(0, round)
            curve.Parent = layer
        end
        layer.Name = "LightLayer"
        layer.BackgroundTransparency = 1
        layer.BorderSizePixel = 0
        layer.ClipsDescendants = true
        layer.Size = UDim2.fromScale(1, 1)
        layer.ZIndex = frame.ZIndex + 1
        layer.Parent = frame
    end
    return layer
end

function UiFx.sweep(frame, color, seconds)
    if not lit(frame) then
        return
    end
    local layer = lightLayer(frame)
    local band = layer:FindFirstChild("Band")
    if not band then
        band = Instance.new("Frame")
        band.Name = "Band"
        band.BorderSizePixel = 0
        band.Size = UDim2.new(0.45, 0, 1, 0)
        band.ZIndex = layer.ZIndex
        local fade = Instance.new("UIGradient")
        fade.Rotation = 12
        fade.Transparency = NumberSequence.new({
            NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.62), NumberSequenceKeypoint.new(1, 1),
        })
        fade.Parent = band
        band.Parent = layer
    end
    band.BackgroundColor3 = color or C.AccentBright
    band.Position = UDim2.fromScale(-0.5, 0)
    tween(band, seconds or 0.5, { Position = UDim2.fromScale(1.05, 0) }, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut)
end

function UiFx.ripple(frame, x, y, color)
    if not lit(frame) then
        return
    end
    local layer = lightLayer(frame)
    local ring = Instance.new("Frame")
    ring.Name = "Ripple"
    ring.AnchorPoint = Vector2.new(0.5, 0.5)
    ring.BackgroundColor3 = color or C.AccentBright
    ring.BackgroundTransparency = 0.7
    ring.BorderSizePixel = 0
    ring.Position = UDim2.fromOffset(x - layer.AbsolutePosition.X, y - layer.AbsolutePosition.Y)
    ring.Size = UDim2.fromOffset(4, 4)
    ring.ZIndex = layer.ZIndex
    local round = Instance.new("UICorner")
    round.CornerRadius = UDim.new(1, 0)
    round.Parent = ring
    ring.Parent = layer
    local reach = math.max(layer.AbsoluteSize.X, layer.AbsoluteSize.Y) * 2.2
    tween(ring, 0.38, { Size = UDim2.fromOffset(reach, reach), BackgroundTransparency = 1 })
    task.delay(0.4, function()
        ring:Destroy()
    end)
end

local function edgeOf(panel)
    return panel:FindFirstChildOfClass("UIStroke")
end

function UiFx.flash(panel, color)
    local edge = edgeOf(panel)
    if not edge then
        return
    end
    local thickness, shade, transparency = edge:GetAttribute("RestThickness") or edge.Thickness, edge:GetAttribute("RestColor") or edge.Color, edge:GetAttribute("RestTransparency") or edge.Transparency
    edge:SetAttribute("RestThickness", thickness)
    edge:SetAttribute("RestColor", shade)
    edge:SetAttribute("RestTransparency", transparency)
    edge.Thickness = thickness + 2
    edge.Color = color or C.AccentBright
    edge.Transparency = 0
    tween(edge, 0.55, { Thickness = thickness, Color = shade, Transparency = transparency })
end

function UiFx.scan(panel, color)
    if not lit(panel) then
        return
    end
    local layer = lightLayer(panel)
    local line = Instance.new("Frame")
    line.Name = "Scan"
    line.BackgroundColor3 = color or C.AccentBright
    line.BackgroundTransparency = 0.15
    line.BorderSizePixel = 0
    line.Size = UDim2.new(1, 0, 0, 2)
    line.ZIndex = panel.ZIndex + 5
    local trail = Instance.new("Frame") -- the glow it leaves just behind it
    trail.BackgroundColor3 = color or C.Accent
    trail.BorderSizePixel = 0
    trail.AnchorPoint = Vector2.new(0, 1)
    trail.Size = UDim2.new(1, 0, 0, 46)
    trail.ZIndex = line.ZIndex
    local fade = Instance.new("UIGradient")
    fade.Rotation = 90
    fade.Transparency = NumberSequence.new(1, 0.72)
    fade.Parent = trail
    trail.Parent = line
    line.Parent = layer
    tween(line, 0.36, { Position = UDim2.new(0, 0, 1, 0) }, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
    task.delay(0.26, function()
        tween(line, 0.12, { BackgroundTransparency = 1 })
        tween(trail, 0.12, { BackgroundTransparency = 1 })
    end)
    task.delay(0.4, function()
        line:Destroy()
    end)
end

-- light travelling round a panel's edge: a gradient on the stroke, slowly turning
function UiFx.edgeLight(panel, seconds)
    local edge = edgeOf(panel)
    if not edge or edge:FindFirstChild("EdgeLight") then
        return
    end
    local light = Instance.new("UIGradient")
    light.Name = "EdgeLight"
    light.Color = ColorSequence.new({
        ColorSequenceKeypoint.new(0, C.EdgeDim), ColorSequenceKeypoint.new(0.42, C.Edge),
        ColorSequenceKeypoint.new(0.5, Color3.new(1, 1, 1)), ColorSequenceKeypoint.new(0.58, C.Edge),
        ColorSequenceKeypoint.new(1, C.EdgeDim),
    })
    light.Parent = edge
    tween(light, seconds or 7, { Rotation = 360 }, Enum.EasingStyle.Linear, Enum.EasingDirection.InOut, -1)
end

-- while it is showing, it breathes and a band of light crosses it every few seconds
function UiFx.attention(button, color)
    local edge = edgeOf(button)
    if edge then
        tween(edge, 0.8, { Thickness = 3 }, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true)
    end
    task.spawn(function()
        while button.Parent do
            if button.Visible then
                UiFx.sweep(button, color or C.Highlight, 0.7)
            end
            task.wait(2.4)
        end
    end)
end

function UiFx.typeIn(label, seconds)
    label.MaxVisibleGraphemes = 0
    local length = utf8.len(label.ContentText) or #label.ContentText
    tween(label, seconds or math.clamp(length * 0.012, 0.15, 0.55), { MaxVisibleGraphemes = length }, Enum.EasingStyle.Linear)
    task.delay((seconds or 0.55) + 0.05, function()
        if label.Parent then
            label.MaxVisibleGraphemes = -1
        end
    end)
end

-- a jump and a settle, by size: a UIScale here would shift whatever it is laid out beside
function UiFx.pop(frame, grow, seconds)
    local rest = frame:GetAttribute("RestSize") or frame.Size
    frame:SetAttribute("RestSize", rest)
    grow = grow or 1.3
    frame.Size = UDim2.new(rest.X.Scale * grow, rest.X.Offset * grow, rest.Y.Scale * grow, rest.Y.Offset * grow)
    tween(frame, seconds or 0.35, { Size = rest }, Enum.EasingStyle.Back)
end

-- ---------- numbers ----------
local rolling = {}
local rollConnection

local function roll()
    local now = os.clock()
    for counter in rolling do
        local t = math.min(1, (now - counter.startedAt) / counter.time)
        local eased = 1 - (1 - t) * (1 - t)
        counter.shown = counter.from + (counter.to - counter.from) * eased
        counter.label.Text = counter.format(if t >= 1 then counter.to else math.round(counter.shown))
        if t >= 1 then
            rolling[counter] = nil
        end
    end
    if next(rolling) == nil then
        rollConnection:Disconnect()
        rollConnection = nil
    end
end

local function floater(counter, amount)
    local holder = counter.floatIn
    local gain = amount > 0
    local text = Instance.new("TextLabel")
    text.Name = "Floater"
    text.BackgroundTransparency = 1
    text.AnchorPoint = Vector2.new(0.5, 0)
    text.AutomaticSize = Enum.AutomaticSize.XY
    text.FontFace = UiTheme.Fonts.Number
    text.Position = UDim2.new(0.5, 0, 1, 2)
    text.Size = UDim2.new()
    text.Text = (if gain then "+" else "-") .. (counter.floatFormat or counter.format)(math.abs(amount))
    text.TextColor3 = if gain then counter.color else C.Danger
    text.TextSize = 15
    text.TextStrokeColor3 = Color3.fromRGB(4, 12, 28)
    text.TextStrokeTransparency = 0.3
    text.ZIndex = 20
    text.Parent = holder
    tween(text, 0.9, { Position = UDim2.new(0.5, 0, 1, 26), TextTransparency = 1, TextStrokeTransparency = 1 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
    task.delay(0.95, function()
        text:Destroy()
    end)
end

-- Returns set(number). opts: Color (of a gain), FloatIn (the frame a difference floats down from), Icon
-- (pops on a gain), FloatFormat (the difference, if not as `format`). The first value, and whatever arrives while a save loads
-- (QUIET_SECONDS), just appears: nobody gained their whole save.
local QUIET_SECONDS = 4
local FLOAT_GAP = 0.9 -- a stream of small gains floats as one number at most this often

function UiFx.counter(label, format, opts)
    opts = opts or {}
    local counter = {
        label = label, format = format, floatFormat = opts.FloatFormat, color = opts.Color or C.AccentBright, floatIn = opts.FloatIn, shown = nil, to = nil,
        pending = 0, lastFloat = 0, quietUntil = os.clock() + QUIET_SECONDS, time = 0.45,
    }
    return function(value)
        if counter.to == nil or os.clock() < counter.quietUntil then
            counter.to, counter.shown = value, value
            rolling[counter] = nil
            label.Text = format(value)
            return
        end
        local change = value - counter.to
        if change == 0 then
            return
        end
        counter.from = counter.shown or counter.to
        counter.to = value
        counter.startedAt = os.clock()
        rolling[counter] = true
        if not rollConnection then
            rollConnection = RunService.Heartbeat:Connect(roll)
        end
        if counter.floatIn then
            counter.pending += change
            local now = os.clock()
            if now - counter.lastFloat >= FLOAT_GAP then
                counter.lastFloat = now
                floater(counter, counter.pending)
                counter.pending = 0
                if opts.Icon then
                    UiFx.pop(opts.Icon, 1.28)
                end
            end
        end
    end
end

-- The rows of a window's lists settle in, one after another. They're laid out by a list, so only their
-- scale can move; the scale is removed afterwards.
local STAGGER_ROWS = 9

function UiFx.stagger(root)
    for _, scroll in root:GetDescendants() do
        if scroll:IsA("ScrollingFrame") then
            local rows = {}
            for _, row in scroll:GetChildren() do
                if row:IsA("GuiObject") and row.Visible then
                    table.insert(rows, row)
                end
            end
            table.sort(rows, function(a, b)
                return a.LayoutOrder < b.LayoutOrder
            end)
            for index = 1, math.min(#rows, STAGGER_ROWS) do
                local row = rows[index]
                if not row:FindFirstChild("SettleScale") then
                    local scale = Instance.new("UIScale")
                    scale.Name = "SettleScale"
                    scale.Scale = 0.94
                    scale.Parent = row
                    local t = tween(scale, 0.26, { Scale = 1 }, Enum.EasingStyle.Back, Enum.EasingDirection.Out, 0, false, (index - 1) * 0.022)
                    t.Completed:Once(function()
                        scale:Destroy()
                    end)
                end
            end
        end
    end
end

return UiFx
