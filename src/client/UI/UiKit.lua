-- Builds the interface's pieces in the UiTheme look (the cultivator's System), so every HUD and
-- window shares one style:
--   panel(props)                a System window: glass, a glowing edge, corner ticks
--                               (Brackets = false: no ticks)
--   content(panel, x, y)        a padded frame inside a panel, for its content
--   header(parent, text, props) a bracketed header: a line, [ TEXT ], a line
--   glow(label, color)          a soft glow round a label's letters
--   icon(image, size, tone)     an outlined box with its icon (UiTheme.Icons; "Accent", "Danger",
--                               "Highlight")
--   label(props)                text in a theme font (Font = a UiTheme.Fonts name)
--   button(props)               an action: "Accent" (primary), "Highlight" (a breakthrough),
--                               "Quiet", "Danger"; it glows on hover and sinks when pressed
--   keycap(key)                 a keyboard key's hint (hidden on touch screens)
--   bar(props)                  a progress bar; setBar(bar, fraction) eases it
--   list(parent, props)         a UIListLayout
-- props: any Instance properties to set, plus the extras named per builder.
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local UiTheme = require(script.Parent:WaitForChild("UiTheme"))

local C = UiTheme.Colors
local UiKit = {}

local EASE = TweenInfo.new(0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)

local function apply(instance, props)
    for key, value in props or {} do
        instance[key] = value
    end
    return instance
end

local function corner(parent, radius)
    local c = Instance.new("UICorner")
    c.CornerRadius = UDim.new(0, radius or UiTheme.Corner)
    c.Parent = parent
    return c
end
UiKit.corner = corner

local function stroke(parent, color, transparency, thickness)
    local s = Instance.new("UIStroke")
    s.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
    s.Color = color
    s.Transparency = transparency or 0
    s.Thickness = thickness or 1
    s.Parent = parent
    return s
end
UiKit.stroke = stroke

function UiKit.padding(parent, x, y)
    local p = Instance.new("UIPadding")
    p.PaddingLeft, p.PaddingRight = UDim.new(0, x), UDim.new(0, x)
    p.PaddingTop, p.PaddingBottom = UDim.new(0, y or x), UDim.new(0, y or x)
    p.Parent = parent
    return p
end

function UiKit.list(parent, props)
    local layout = Instance.new("UIListLayout")
    layout.SortOrder = Enum.SortOrder.LayoutOrder
    apply(layout, props)
    layout.Parent = parent
    return layout
end

-- bright ticks on a window's four corners, over its edge
function UiKit.brackets(frame, color, length)
    length = length or 12
    color = color or C.Edge
    for _, spot in { Vector2.new(0, 0), Vector2.new(1, 0), Vector2.new(0, 1), Vector2.new(1, 1) } do
        for _, horizontal in { true, false } do
            local arm = Instance.new("Frame")
            arm.Name = "Tick"
            arm.BorderSizePixel = 0
            arm.BackgroundColor3 = color
            arm.AnchorPoint = spot
            arm.Size = if horizontal then UDim2.fromOffset(length, 2) else UDim2.fromOffset(2, length)
            arm.Position = UDim2.new(spot.X, if spot.X == 0 then -1 else 1, spot.Y, if spot.Y == 0 then -1 else 1)
            arm.ZIndex = frame.ZIndex + 2
            arm.Parent = frame
        end
    end
end

function UiKit.panel(props)
    local frame = Instance.new("Frame")
    frame.BackgroundColor3 = C.Panel
    frame.BackgroundTransparency = UiTheme.PanelTransparency
    frame.BorderSizePixel = 0
    local copy = table.clone(props or {})
    local brackets = copy.Brackets ~= false
    copy.Brackets = nil
    apply(frame, copy)
    corner(frame)
    stroke(frame, C.Edge, 0.25)
    -- the glow: a soft wide rim just inside the edge
    local rim = Instance.new("Frame")
    rim.Name = "Glow"
    rim.BackgroundTransparency = 1
    rim.AnchorPoint = Vector2.new(0.5, 0.5)
    rim.Position = UDim2.fromScale(0.5, 0.5)
    rim.Size = UDim2.new(1, -4, 1, -4)
    rim.Parent = frame
    corner(rim)
    stroke(rim, C.Edge, 0.72, 5)
    local glass = Instance.new("UIGradient") -- deeper at the bottom, as light through glass
    glass.Rotation = 90
    glass.Transparency = NumberSequence.new(0, 0.12)
    glass.Parent = frame
    if brackets then
        UiKit.brackets(frame)
    end
    return frame
end

-- A padded frame filling a panel, for its content: a UIPadding on the panel itself would push the
-- corner ticks inward onto the content.
function UiKit.content(panel, x, y)
    local inner = Instance.new("Frame")
    inner.Name = "Content"
    inner.BackgroundTransparency = 1
    inner.Size = UDim2.fromScale(1, 1)
    inner.Parent = panel
    UiKit.padding(inner, x, y)
    return inner
end

function UiKit.label(props)
    local label = Instance.new("TextLabel")
    label.BackgroundTransparency = 1
    label.TextColor3 = C.Text
    label.FontFace = UiTheme.Fonts.Body
    label.TextSize = 16
    label.TextXAlignment = Enum.TextXAlignment.Left
    local copy = table.clone(props or {})
    if copy.Font then
        label.FontFace = UiTheme.Fonts[copy.Font]
        copy.Font = nil
    end
    apply(label, copy)
    return label
end

-- A soft glow round a label's letters, as projected light (the header font is thin)
function UiKit.glow(label, color)
    local halo = stroke(label, color or C.Edge, 0.6, 1)
    halo.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
    return halo
end

-- A bracketed header across its parent: a fading line, [ TEXT ], a fading line. props: Color,
-- TextSize, and any Frame properties (Position, Size, LayoutOrder ...).
function UiKit.header(parent, text, props)
    local copy = table.clone(props or {})
    local color = copy.Color or C.Text
    local size = copy.TextSize or 14
    copy.Color, copy.TextSize = nil, nil
    local row = Instance.new("Frame")
    row.Name = "Header"
    row.BackgroundTransparency = 1
    row.Size = UDim2.new(1, 0, 0, size + 8)
    apply(row, copy)
    row.Parent = parent
    local word = UiKit.label({
        Name = "Text", Font = "Header", Text = "[  " .. text .. "  ]", TextSize = size, TextColor3 = color,
        AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), AutomaticSize = Enum.AutomaticSize.X,
        Size = UDim2.new(0, 0, 1, 0), TextXAlignment = Enum.TextXAlignment.Center, Parent = row,
    })
    if size >= 13 then -- on smaller letters a halo fills their gaps
        UiKit.glow(word)
    end
    -- a line each side of the word, fading out toward the edges; they follow the word's width
    local lines = {}
    for side = 0, 1 do
        local line = Instance.new("Frame")
        line.BorderSizePixel = 0
        line.BackgroundColor3 = C.Edge
        line.AnchorPoint = Vector2.new(side, 0.5)
        line.Position = UDim2.fromScale(side, 0.5)
        line.Parent = row
        local fade = Instance.new("UIGradient")
        fade.Transparency = if side == 0 then NumberSequence.new(1, 0.2) else NumberSequence.new(0.2, 1)
        fade.Parent = line
        lines[side] = line
    end
    local function fit()
        local gap = word.AbsoluteSize.X / 2 + 10
        for _, line in lines do
            line.Size = UDim2.new(0.5, -gap, 0, 1)
        end
    end
    word:GetPropertyChangedSignal("AbsoluteSize"):Connect(fit)
    fit()
    return row, word
end

local TONES = {
    Accent = { C.AccentDeep, C.Accent, C.AccentBright },
    Danger = { C.DangerDeep, C.Danger, C.Text },
    Highlight = { Color3.fromRGB(80, 60, 16), C.Highlight, C.Highlight },
}

function UiKit.icon(image, size, tone)
    local colors = TONES[tone or "Accent"]
    local box = Instance.new("Frame")
    box.Name = "Icon"
    box.Size = UDim2.fromOffset(size, size)
    box.BackgroundColor3 = colors[1]
    box.BackgroundTransparency = 0.3
    box.BorderSizePixel = 0
    corner(box, 2)
    stroke(box, colors[2], 0.1, 1)
    local picture = Instance.new("ImageLabel")
    picture.Name = "Image"
    picture.BackgroundTransparency = 1
    picture.Image = image
    picture.ImageColor3 = colors[3]
    picture.AnchorPoint = Vector2.new(0.5, 0.5)
    picture.Position = UDim2.fromScale(0.5, 0.5)
    picture.Size = UDim2.fromScale(0.7, 0.7)
    picture.Parent = box
    return box
end

local BUTTON_TONES = {
    Accent = { back = C.AccentDeep, edge = C.Accent, text = C.Text },
    Highlight = { back = Color3.fromRGB(70, 52, 12), edge = C.Highlight, text = C.Highlight },
    Quiet = { back = C.Raised, edge = C.EdgeDim, text = C.Text },
    Danger = { back = C.DangerDeep, edge = C.Danger, text = C.Text },
}

-- props.Tone picks the colours; button:SetAttribute("Tone", name) changes them later
function UiKit.button(props)
    local copy = table.clone(props or {})
    local toneName = copy.Tone or "Quiet"
    copy.Tone = nil
    local button = Instance.new("TextButton")
    button.AutoButtonColor = false
    button.BorderSizePixel = 0
    button.FontFace = UiTheme.Fonts.Title
    button.TextSize = 16
    if copy.Font then
        button.FontFace = UiTheme.Fonts[copy.Font]
        copy.Font = nil
    end
    corner(button)
    local edge = stroke(button, C.Edge, 0.15)
    local glass = Instance.new("UIGradient")
    glass.Rotation = 90
    glass.Transparency = NumberSequence.new(0, 0.25)
    glass.Parent = button
    local scale = Instance.new("UIScale")
    scale.Parent = button

    local hovered = false
    local function paint()
        local tone = BUTTON_TONES[button:GetAttribute("Tone")] or BUTTON_TONES.Quiet
        local lit = hovered and button.Active
        button.BackgroundColor3 = if lit then tone.back:Lerp(tone.edge, 0.25) else tone.back
        button.BackgroundTransparency = 0.18
        button.TextColor3 = tone.text
        edge.Color = tone.edge
        edge.Transparency = if button.Active then 0.05 else 0.6
        edge.Thickness = if lit then 2 else 1
    end
    button:SetAttribute("Tone", toneName)
    button:GetAttributeChangedSignal("Tone"):Connect(paint)
    button:GetPropertyChangedSignal("Active"):Connect(paint)
    button.MouseEnter:Connect(function()
        hovered = true
        paint()
    end)
    button.MouseLeave:Connect(function()
        hovered = false
        paint()
        TweenService:Create(scale, EASE, { Scale = 1 }):Play()
    end)
    button.InputBegan:Connect(function(input)
        if button.Active and (input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch) then
            TweenService:Create(scale, EASE, { Scale = 0.95 }):Play()
        end
    end)
    button.InputEnded:Connect(function(input)
        if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then
            TweenService:Create(scale, EASE, { Scale = 1 }):Play()
        end
    end)
    apply(button, copy)
    paint()
    return button
end

function UiKit.keycap(key)
    local cap = UiKit.label({
        Name = "Keycap", Font = "Strong", Text = key, TextSize = 13, TextColor3 = C.AccentBright,
        TextXAlignment = Enum.TextXAlignment.Center, BackgroundTransparency = 0.3,
        BackgroundColor3 = C.Well, Size = UDim2.fromOffset(24, 22),
    })
    corner(cap, 2)
    stroke(cap, C.Accent, 0.35)
    cap.Visible = not UserInputService.TouchEnabled or UserInputService.KeyboardEnabled
    return cap
end

-- props.Fill: the fill colour (default the accent). UiKit.setBar(bar, t) eases the fill there.
function UiKit.bar(props)
    local copy = table.clone(props or {})
    local fillColor = copy.Fill or C.Accent
    copy.Fill = nil
    local track = Instance.new("Frame")
    track.Name = "Bar"
    track.BackgroundColor3 = C.Well
    track.BackgroundTransparency = 0.2
    track.BorderSizePixel = 0
    track.ClipsDescendants = true
    corner(track, 1)
    stroke(track, C.EdgeDim, 0.2)
    local fill = Instance.new("Frame")
    fill.Name = "Fill"
    fill.BorderSizePixel = 0
    fill.BackgroundColor3 = fillColor
    fill.Size = UDim2.fromScale(0, 1)
    fill.Parent = track
    corner(fill, 1)
    local sheen = Instance.new("UIGradient") -- brightest at the leading edge (it tints whatever fill colour is set)
    sheen.Color = ColorSequence.new(Color3.fromRGB(140, 140, 140), Color3.new(1, 1, 1))
    sheen.Parent = fill
    apply(track, copy)
    return track
end

function UiKit.setBar(bar, fraction, instant)
    local fill = bar:FindFirstChild("Fill")
    local goal = UDim2.fromScale(math.clamp(fraction, 0, 1), 1)
    if instant then
        fill.Size = goal
    else
        TweenService:Create(fill, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = goal }):Play()
    end
end

return UiKit
