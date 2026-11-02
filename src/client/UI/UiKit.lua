-- Builds the interface's pieces in the UiTheme look, so every HUD and window shares one style:
--   panel(props)                lacquer panel: gold hairline, a light falling from the top, lattice
--                               corner brackets (Brackets = false: none)
--   content(panel, x, y)        a padded frame inside a panel, for its content
--   seal(glyph, size, tone)     a square seal stamp with its character ("Cinnabar" or "Jade")
--   label(props)                text in a theme font (Font = a UiTheme.Fonts name)
--   button(props)               an action: "Jade" (primary), "Gold" (a breakthrough), "Quiet",
--                               "Cinnabar"; it lifts on hover and sinks when pressed
--   keycap(key)                 a keyboard key's hint (hidden on touch screens)
--   bar(props)                  a progress bar; :set(fraction) eases it
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

-- four small L-shaped gold corners just inside a frame's edge, like a lattice window's joints
function UiKit.brackets(frame, color, length, inset)
    length, inset = length or 9, inset or 4
    color = color or C.Gold
    for _, spot in { Vector2.new(0, 0), Vector2.new(1, 0), Vector2.new(0, 1), Vector2.new(1, 1) } do
        local sx, sy = if spot.X == 0 then 1 else -1, if spot.Y == 0 then 1 else -1
        for _, horizontal in { true, false } do
            local arm = Instance.new("Frame")
            arm.Name = "Bracket"
            arm.BorderSizePixel = 0
            arm.BackgroundColor3 = color
            arm.AnchorPoint = spot
            arm.Size = if horizontal then UDim2.fromOffset(length, 2) else UDim2.fromOffset(2, length)
            arm.Position = UDim2.new(spot.X, sx * inset, spot.Y, sy * inset)
            arm.ZIndex = frame.ZIndex + 2
            arm.Parent = frame
        end
    end
end

function UiKit.panel(props)
    local frame = Instance.new("Frame")
    frame.BackgroundColor3 = C.Ink
    frame.BackgroundTransparency = UiTheme.PanelTransparency
    frame.BorderSizePixel = 0
    local brackets = props and props.Brackets ~= false
    local copy = table.clone(props or {})
    copy.Brackets = nil
    apply(frame, copy)
    corner(frame)
    stroke(frame, C.Gold, 0.45)
    local light = Instance.new("UIGradient") -- a soft light from above, as on lacquer
    light.Rotation = 90
    light.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(150, 150, 150))
    light.Parent = frame
    if brackets then
        UiKit.brackets(frame)
    end
    return frame
end

-- A padded frame filling a panel, for its content: a UIPadding on the panel itself would push the
-- corner brackets inward onto the content.
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
    label.TextColor3 = C.Parchment
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

local TONES = {
    Cinnabar = { C.Cinnabar, C.Parchment },
    Jade = { C.JadeDeep, C.JadeBright },
    Gold = { C.Gold, C.Ink },
}

function UiKit.seal(glyph, size, tone)
    local colors = TONES[tone or "Cinnabar"]
    local seal = Instance.new("Frame")
    seal.Name = "Seal"
    seal.Size = UDim2.fromOffset(size, size)
    seal.BackgroundColor3 = colors[1]
    seal.BorderSizePixel = 0
    seal.Rotation = -3 -- pressed by hand, never quite square
    corner(seal, 3)
    local rim = Instance.new("Frame") -- the stamp's carved inner border
    rim.BackgroundTransparency = 1
    rim.AnchorPoint = Vector2.new(0.5, 0.5)
    rim.Position = UDim2.fromScale(0.5, 0.5)
    rim.Size = UDim2.new(1, -math.max(4, size // 8), 1, -math.max(4, size // 8))
    rim.Parent = seal
    corner(rim, 2)
    stroke(rim, colors[2], 0.35, 1)
    UiKit.label({
        Font = "Seal", Text = glyph, TextColor3 = colors[2], TextSize = math.floor(size * 0.66),
        Size = UDim2.fromScale(1, 1), TextXAlignment = Enum.TextXAlignment.Center, Parent = seal,
    })
    return seal
end

local BUTTON_TONES = {
    Jade = { back = C.JadeDeep, edge = C.Jade, text = C.Parchment },
    Gold = { back = Color3.fromRGB(92, 70, 30), edge = C.Gold, text = C.Parchment },
    Quiet = { back = C.InkRaised, edge = C.GoldDim, text = C.Parchment },
    Cinnabar = { back = C.CinnabarDeep, edge = C.Cinnabar, text = C.Parchment },
}

-- props.Tone picks the colours; button:SetAttribute("Tone", name) changes them later
function UiKit.button(props)
    local copy = table.clone(props or {})
    local toneName = copy.Tone or "Quiet"
    copy.Tone = nil
    local button = Instance.new("TextButton")
    button.AutoButtonColor = false
    button.BorderSizePixel = 0
    button.FontFace = UiTheme.Fonts.Strong
    button.TextSize = 16
    if copy.Font then
        button.FontFace = UiTheme.Fonts[copy.Font]
        copy.Font = nil
    end
    corner(button)
    local edge = stroke(button, C.Gold, 0.15)
    local sheen = Instance.new("UIGradient")
    sheen.Rotation = 90
    sheen.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(175, 175, 175))
    sheen.Parent = button
    local scale = Instance.new("UIScale")
    scale.Parent = button

    local hovered = false
    local function paint()
        local tone = BUTTON_TONES[button:GetAttribute("Tone")] or BUTTON_TONES.Quiet
        local lift = if hovered and button.Active then 0.12 else 0
        button.BackgroundColor3 = tone.back:Lerp(tone.edge, lift)
        button.TextColor3 = tone.text
        edge.Color = tone.edge
        edge.Transparency = if button.Active then 0.1 else 0.6
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
        Name = "Keycap", Font = "Strong", Text = key, TextSize = 13, TextColor3 = C.Parchment,
        TextXAlignment = Enum.TextXAlignment.Center, BackgroundTransparency = 0.2,
        BackgroundColor3 = C.InkDeep, Size = UDim2.fromOffset(24, 22),
    })
    corner(cap, 3)
    stroke(cap, C.Parchment, 0.5)
    cap.Visible = not UserInputService.TouchEnabled or UserInputService.KeyboardEnabled
    return cap
end

-- props.Fill: the fill colour (default jade). Returns the bar; bar:SetAttribute("Fraction", t) or
-- UiKit.setBar(bar, t) eases the fill there.
function UiKit.bar(props)
    local copy = table.clone(props or {})
    local fillColor = copy.Fill or C.Jade
    copy.Fill = nil
    local track = Instance.new("Frame")
    track.Name = "Bar"
    track.BackgroundColor3 = C.InkDeep
    track.BackgroundTransparency = 0.15
    track.BorderSizePixel = 0
    track.ClipsDescendants = true
    corner(track, 2)
    stroke(track, C.GoldDim, 0.3)
    local fill = Instance.new("Frame")
    fill.Name = "Fill"
    fill.BorderSizePixel = 0
    fill.BackgroundColor3 = fillColor
    fill.Size = UDim2.fromScale(0, 1)
    fill.Parent = track
    corner(fill, 2)
    local sheen = Instance.new("UIGradient") -- brighter at the leading edge: Qi flowing in
    sheen.Color = ColorSequence.new(Color3.fromRGB(150, 150, 150), Color3.new(1, 1, 1))
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
