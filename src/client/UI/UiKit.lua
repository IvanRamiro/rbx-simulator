-- Builds the interface's pieces in the UiTheme look, so every HUD and window shares one style:
--   panel(props)                a rounded window in a colour: props.Hue, a UiTheme.Hues name
--   content(panel, x, y)        a padded frame inside a panel, for its content
--   header(parent, text, props) a title across its parent: a line, TEXT, a line
--   icon(image, size, tone)     a box with its icon (UiTheme.Icons; "Accent", "Danger", "Highlight")
--   label(props)                text in a theme font (Font = a UiTheme.Fonts name)
--   button(props)               an action: Tone = "Accent", "Go", "Highlight", "Quiet", "Danger" or a
--                               UiTheme.Hues name; it brightens on hover and sinks when pressed
--   touchButton(button, text, hue)  a round on-screen button for touch players
--   keycap(key)                 a keyboard key's hint (hidden on touch screens)
--   bar(props)                  a progress bar; setBar(bar, fraction) eases it
--   list(parent, props)         a UIListLayout
--   scroll(props)               a scrolling list (its children laid out down it)
--   card(props)                 a row in a window: a lighter tint of the window's colour; Stripe = a
--                               colour down its left side (a rarity, an element)
--   tag(text, color)            a small filled word: a rarity, a state ("EQUIPPED")
--   textbox(props)              a text field
--   empty(parent, text)         the muted line a list shows when it has nothing
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

-- a top-to-bottom gradient: the instance's own colour is white, so this is its colour
local function fillGradient(instance, top, bottom)
    instance.BackgroundColor3 = Color3.new(1, 1, 1)
    local gradient = Instance.new("UIGradient")
    gradient.Color = ColorSequence.new(top, bottom)
    gradient.Rotation = 90
    gradient.Parent = instance
    return gradient
end

function UiKit.panel(props)
    local frame = Instance.new("Frame")
    frame.BackgroundTransparency = UiTheme.PanelTransparency
    frame.BorderSizePixel = 0
    local copy = table.clone(props or {})
    local hue = UiTheme.Hues[copy.Hue or "Violet"]
    copy.Hue = nil
    apply(frame, copy)
    corner(frame)
    stroke(frame, hue.Edge, 0.05, 2)
    fillGradient(frame, hue.Top, hue.Bottom)
    return frame
end

-- A padded frame filling a panel, for its content
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
    label.TextStrokeColor3 = C.TextShadow
    label.TextStrokeTransparency = 0.55
    local copy = table.clone(props or {})
    if copy.Font then
        label.FontFace = UiTheme.Fonts[copy.Font]
        copy.Font = nil
    end
    apply(label, copy)
    return label
end

-- A title across its parent: a fading line, TEXT, a fading line. props: Color, TextSize, and any Frame
-- properties (Position, Size, LayoutOrder ...).
function UiKit.header(parent, text, props)
    local copy = table.clone(props or {})
    local color = copy.Color or C.Text
    local size = (copy.TextSize or 14) + 3 -- the chunky font reads better a little larger
    copy.Color, copy.TextSize = nil, nil
    local row = Instance.new("Frame")
    row.Name = "Header"
    row.BackgroundTransparency = 1
    row.Size = UDim2.new(1, 0, 0, size + 5)
    apply(row, copy)
    row.Parent = parent
    local word = UiKit.label({
        Name = "Text", Font = "Header", Text = text, TextSize = size, TextColor3 = color,
        AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), AutomaticSize = Enum.AutomaticSize.X,
        Size = UDim2.new(0, 0, 1, 0), TextXAlignment = Enum.TextXAlignment.Center, Parent = row,
    })
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
        fade.Transparency = if side == 0 then NumberSequence.new(1, 0.35) else NumberSequence.new(0.35, 1)
        fade.Parent = line
        lines[side] = line
    end
    local function fit()
        local gap = word.AbsoluteSize.X / 2 + 10
        for _, line in lines do
            line.Size = UDim2.new(0.5, -gap, 0, 2)
        end
    end
    word:GetPropertyChangedSignal("AbsoluteSize"):Connect(fit)
    fit()
    return row, word
end

-- an icon's box: a light tint of whatever it sits on, or a warning or reward colour
local TONES = {
    Accent = { back = Color3.new(1, 1, 1), clear = 0.8 },
    Danger = { back = C.Danger, clear = 0.1 },
    Highlight = { back = C.Highlight, clear = 0.15 },
}

function UiKit.icon(image, size, tone)
    local colors = TONES[tone or "Accent"]
    local box = Instance.new("Frame")
    box.Name = "Icon"
    box.Size = UDim2.fromOffset(size, size)
    box.BackgroundColor3 = colors.back
    box.BackgroundTransparency = colors.clear
    box.BorderSizePixel = 0
    corner(box, 8)
    stroke(box, C.Edge, 0.45, 1)
    local picture = Instance.new("ImageLabel")
    picture.Name = "Image"
    picture.BackgroundTransparency = 1
    picture.Image = image
    picture.ImageColor3 = C.Text
    picture.AnchorPoint = Vector2.new(0.5, 0.5)
    picture.Position = UDim2.fromScale(0.5, 0.5)
    picture.Size = UDim2.fromScale(0.76, 0.76)
    picture.Parent = box
    return box
end

local BUTTON_TONES = {
    Accent = { back = Color3.fromRGB(30, 140, 245), edge = Color3.fromRGB(180, 230, 255), clear = 0 },
    Go = { back = Color3.fromRGB(30, 190, 105), edge = Color3.fromRGB(200, 255, 205), clear = 0 },
    Highlight = { back = Color3.fromRGB(245, 160, 20), edge = Color3.fromRGB(255, 238, 160), clear = 0 },
    Quiet = { back = Color3.new(1, 1, 1), edge = Color3.new(1, 1, 1), clear = 0.78 },
    Danger = { back = Color3.fromRGB(235, 45, 95), edge = Color3.fromRGB(255, 190, 210), clear = 0 },
}
for name, hue in UiTheme.Hues do
    BUTTON_TONES[name] = { back = hue.Top, edge = hue.Edge, clear = 0 }
end

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
    button.TextStrokeColor3 = C.TextShadow
    button.TextStrokeTransparency = 0.55
    corner(button, 10)
    local edge = stroke(button, C.Edge, 0.1, 2)
    local gloss = Instance.new("UIGradient") -- lit from above. It tints the button's words too: keep it light
    gloss.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(226, 226, 226))
    gloss.Rotation = 90
    gloss.Parent = button
    local scale = Instance.new("UIScale")
    scale.Parent = button

    local hovered = false
    local function paint()
        local tone = BUTTON_TONES[button:GetAttribute("Tone")] or BUTTON_TONES.Quiet
        local lit = hovered and button.Active
        button.BackgroundColor3 = if lit then tone.back:Lerp(Color3.new(1, 1, 1), 0.2) else tone.back
        button.BackgroundTransparency = if button.Active then tone.clear else math.max(tone.clear, 0.45)
        button.TextColor3 = C.Text
        edge.Color = tone.edge
        edge.Transparency = if button.Active then 0.1 else 0.6
        edge.Thickness = if lit then 3 else 2
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

-- A round on-screen button for touch players (Strike, Dash ...), in a UiTheme.Hues colour.
function UiKit.touchButton(button, text, hueName)
    local hue = UiTheme.Hues[hueName or "Blue"]
    button.BackgroundTransparency = 0.05
    button.BorderSizePixel = 0
    button.FontFace = UiTheme.Fonts.Title
    button.TextScaled = true
    button.TextColor3 = C.Text
    button.TextStrokeColor3 = C.TextShadow
    button.TextStrokeTransparency = 0.55
    button.Text = text
    corner(button, 999)
    stroke(button, hue.Edge, 0.05, 3)
    fillGradient(button, hue.Top, hue.Bottom)
    UiKit.padding(button, 10, 10)
end

function UiKit.keycap(key)
    local cap = UiKit.label({
        Name = "Keycap", Font = "Strong", Text = key, TextSize = 13, TextColor3 = C.Text,
        TextXAlignment = Enum.TextXAlignment.Center, BackgroundTransparency = 0.35,
        BackgroundColor3 = C.Well, Size = UDim2.fromOffset(24, 22),
    })
    corner(cap, 6)
    stroke(cap, C.Edge, 0.5)
    cap.Visible = not UserInputService.TouchEnabled or UserInputService.KeyboardEnabled
    return cap
end

-- props.Fill: the fill colour (default a sweep of colours). UiKit.setBar(bar, t) eases the fill there.
function UiKit.bar(props)
    local copy = table.clone(props or {})
    local fillColor = copy.Fill
    copy.Fill = nil
    local track = Instance.new("Frame")
    track.Name = "Bar"
    track.BackgroundColor3 = C.Well
    track.BackgroundTransparency = 0.25
    track.BorderSizePixel = 0
    track.ClipsDescendants = true
    corner(track, 4)
    local fill = Instance.new("Frame")
    fill.Name = "Fill"
    fill.BorderSizePixel = 0
    fill.BackgroundColor3 = fillColor or Color3.new(1, 1, 1)
    fill.Size = UDim2.fromScale(0, 1)
    fill.Parent = track
    corner(fill, 4)
    local sweep = Instance.new("UIGradient") -- it tints whatever fill colour is set: brightest at the leading edge
    sweep.Color = if fillColor then ColorSequence.new(Color3.fromRGB(170, 170, 170), Color3.new(1, 1, 1))
        else ColorSequence.new({
            ColorSequenceKeypoint.new(0, C.Accent),
            ColorSequenceKeypoint.new(0.55, Color3.fromRGB(150, 110, 255)),
            ColorSequenceKeypoint.new(1, Color3.fromRGB(255, 110, 190)),
        })
    sweep.Parent = fill
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

function UiKit.scroll(props)
    local scroll = Instance.new("ScrollingFrame")
    scroll.BackgroundTransparency = 1
    scroll.BorderSizePixel = 0
    scroll.ScrollBarThickness = 5
    scroll.ScrollBarImageColor3 = C.Edge
    scroll.ScrollBarImageTransparency = 0.35
    scroll.CanvasSize = UDim2.new()
    scroll.AutomaticCanvasSize = Enum.AutomaticSize.Y
    scroll.ScrollingDirection = Enum.ScrollingDirection.Y
    apply(scroll, props)
    local pad = Instance.new("UIPadding") -- room for the bar, and for each card's edge
    pad.PaddingRight = UDim.new(0, 8)
    pad.PaddingTop, pad.PaddingBottom, pad.PaddingLeft = UDim.new(0, 2), UDim.new(0, 2), UDim.new(0, 2)
    pad.Parent = scroll
    UiKit.list(scroll, { Padding = UDim.new(0, 6) })
    return scroll
end

function UiKit.card(props)
    local copy = table.clone(props or {})
    local stripeColor = copy.Stripe
    copy.Stripe = nil
    local card = Instance.new("Frame")
    card.BackgroundColor3 = Color3.new(1, 1, 1)
    card.BackgroundTransparency = 0.84
    card.BorderSizePixel = 0
    corner(card, 10)
    stroke(card, C.Edge, 0.65)
    if stripeColor then
        local stripe = Instance.new("Frame")
        stripe.Name = "Stripe"
        stripe.BorderSizePixel = 0
        stripe.BackgroundColor3 = stripeColor
        stripe.Position = UDim2.fromOffset(3, 6)
        stripe.Size = UDim2.new(0, 4, 1, -12)
        stripe.Parent = card
        corner(stripe, 2)
    end
    apply(card, copy)
    return card
end

function UiKit.tag(text, color)
    color = color or C.Accent
    local tag = UiKit.label({
        Name = "Tag", Font = "Strong", Text = string.upper(text), TextSize = 10, TextColor3 = C.Text,
        BackgroundColor3 = color, BackgroundTransparency = 0.1, AutomaticSize = Enum.AutomaticSize.X,
        Size = UDim2.fromOffset(0, 16), TextXAlignment = Enum.TextXAlignment.Center,
    })
    corner(tag, 6)
    UiKit.padding(tag, 6, 0)
    return tag
end

function UiKit.textbox(props)
    local box = Instance.new("TextBox")
    box.BackgroundColor3 = C.Well
    box.BackgroundTransparency = 0.25
    box.BorderSizePixel = 0
    box.ClearTextOnFocus = false
    box.FontFace = UiTheme.Fonts.Strong
    box.TextSize = 15
    box.TextColor3 = C.Text
    box.PlaceholderColor3 = C.Muted
    box.TextXAlignment = Enum.TextXAlignment.Left
    corner(box, 10)
    local edge = stroke(box, C.EdgeDim, 0.3)
    box.Focused:Connect(function()
        edge.Color = C.Edge
    end)
    box.FocusLost:Connect(function()
        edge.Color = C.EdgeDim
    end)
    UiKit.padding(box, 10, 0)
    apply(box, props)
    return box
end

function UiKit.empty(parent, text)
    return UiKit.label({
        Name = "Empty", Text = text, TextSize = 14, TextColor3 = C.Muted, TextWrapped = true,
        TextXAlignment = Enum.TextXAlignment.Center, AutomaticSize = Enum.AutomaticSize.Y,
        Size = UDim2.new(1, 0, 0, 0), Parent = parent,
    })
end

return UiKit
