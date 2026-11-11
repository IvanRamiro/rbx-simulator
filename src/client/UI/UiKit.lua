-- Builds the interface's pieces in the UiTheme look, so every HUD and window shares one style:
--   panel(props)                a window: deep glass, gold trim, a small ornament on each corner
--                               (Brackets = false: none)
--   content(panel, x, y)        a padded frame inside a panel, for its content
--   header(parent, text, props) a bracketed header: a line, [ TEXT ], a line
--   icon(image, size, tone)     a box holding a full-colour icon (UiTheme.Icons; "Accent" or "Danger")
--   label(props)                text in a theme font (Font = a UiTheme.Fonts name)
--   button(props)               an action: "Primary" (the one main action, with a halo), "Accent",
--                               "Highlight" (a breakthrough, with a halo), "Quiet", "Danger"; on hover
--                               it lifts and light crosses it, pressed it sinks with a ripple
--   keycap(key)                 a keyboard key's hint (hidden on touch screens)
--   bar(props)                  a progress bar; setBar(bar, fraction) eases it
--   list(parent, props)         a UIListLayout
--   scroll(props)               a scrolling list (a thin glowing bar; its children laid out down it)
--   card(props)                 a row in a window: raised glass, a quiet edge; Stripe = a colour
--                               down its left side (a rarity, an element)
--   tag(text, color)            a small outlined word: a rarity, a state ("EQUIPPED")
--   textbox(props)              a text field in the interface's style
--   empty(parent, text)         the muted line a list shows when it has nothing
-- props: any Instance properties to set, plus the extras named per builder.
local ContentProvider = game:GetService("ContentProvider")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local UiFx = require(script.Parent:WaitForChild("UiFx"))
local UiTheme = require(script.Parent:WaitForChild("UiTheme"))

local C = UiTheme.Colors
local UiKit = {}

local EASE = TweenInfo.new(0.1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local BOUNCE = TweenInfo.new(0.22, Enum.EasingStyle.Back, Enum.EasingDirection.Out)

-- fetched as soon as the game starts, so a phone never shows an empty icon box for long
task.spawn(function()
    local images = {}
    for _, id in UiTheme.Icons do
        local picture = Instance.new("ImageLabel")
        picture.Image = id
        table.insert(images, picture)
    end
    pcall(function()
        ContentProvider:PreloadAsync(images)
    end)
end)

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

-- a small gold ornament on a window's four corners, over its edge: one drawing, turned for each
local ORNAMENT_SIZE = 34
function UiKit.brackets(frame)
    for _, corner_ in { { 0, 0, 0 }, { 1, 0, 90 }, { 1, 1, 180 }, { 0, 1, 270 } } do
        local piece = Instance.new("ImageLabel")
        piece.Name = "Ornament"
        piece.BackgroundTransparency = 1
        piece.Image = UiTheme.Ornaments.Corner
        piece.AnchorPoint = Vector2.new(corner_[1], corner_[2])
        piece.Position = UDim2.new(corner_[1], if corner_[1] == 0 then -3 else 3, corner_[2], if corner_[2] == 0 then -3 else 3)
        piece.Size = UDim2.fromOffset(ORNAMENT_SIZE, ORNAMENT_SIZE)
        piece.Rotation = corner_[3]
        piece.ZIndex = frame.ZIndex + 2
        piece.Parent = frame
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
    stroke(frame, C.Edge, 0.1)
    -- the glow: a soft wide rim just inside the edge
    local rim = Instance.new("Frame")
    rim.Name = "Glow"
    rim.BackgroundTransparency = 1
    rim.AnchorPoint = Vector2.new(0.5, 0.5)
    rim.Position = UDim2.fromScale(0.5, 0.5)
    rim.Size = UDim2.new(1, -4, 1, -4)
    rim.Parent = frame
    corner(rim)
    stroke(rim, C.Edge, 0.9, 4)
    local glass = Instance.new("UIGradient") -- deeper at the bottom, as light through glass
    glass.Rotation = 90
    glass.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(120, 118, 160))
    glass.Transparency = NumberSequence.new(0, 0.12)
    glass.Parent = frame
    -- a thread of light along the top, as a projected window's upper edge
    local top = Instance.new("Frame")
    top.Name = "TopLight"
    top.BackgroundColor3 = C.AccentBright
    top.BorderSizePixel = 0
    top.AnchorPoint = Vector2.new(0.5, 0)
    top.Position = UDim2.new(0.5, 0, 0, 1)
    top.Size = UDim2.new(1, -8, 0, 1)
    local thread = Instance.new("UIGradient")
    thread.Transparency = NumberSequence.new({
        NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.45), NumberSequenceKeypoint.new(1, 1),
    })
    thread.Parent = top
    top.Parent = frame
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

-- A header across its parent: a fading line, TEXT, a fading line. props: Color,
-- TextSize, and any Frame properties (Position, Size, LayoutOrder ...).
function UiKit.header(parent, text, props)
    local copy = table.clone(props or {})
    local color = copy.Color or C.AccentBright
    local size = copy.TextSize or 14
    copy.Color, copy.TextSize = nil, nil
    local row = Instance.new("Frame")
    row.Name = "Header"
    row.BackgroundTransparency = 1
    row.Size = UDim2.new(1, 0, 0, size + 8)
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
    picture.ImageColor3 = Color3.new(1, 1, 1) -- full colour, as drawn
    picture.AnchorPoint = Vector2.new(0.5, 0.5)
    picture.Position = UDim2.fromScale(0.5, 0.5)
    picture.Size = UDim2.fromScale(0.86, 0.86)
    picture.Parent = box
    return box
end

local BUTTON_TONES = {
    Primary = { back = C.AccentFill, edge = C.AccentBright, text = Color3.fromRGB(48, 28, 6), glow = C.Accent }, -- the one main action on screen
    Accent = { back = Color3.fromRGB(58, 50, 122), edge = C.Accent, text = C.Text },
    Highlight = { back = C.Highlight, edge = Color3.new(1, 1, 1), text = Color3.fromRGB(48, 28, 6), glow = C.Highlight },
    Quiet = { back = C.Raised, edge = C.EdgeDim, text = C.Text },
    Danger = { back = C.DangerDeep, edge = C.Danger, text = C.Text },
    Active = { back = Color3.fromRGB(14, 112, 118), edge = Color3.fromRGB(120, 255, 236), text = Color3.new(1, 1, 1), glow = Color3.fromRGB(70, 240, 220) }, -- something running, right now
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
    glass.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(226, 214, 200))
    glass.Transparency = NumberSequence.new(0, 0.06)
    glass.Parent = button
    local scale = Instance.new("UIScale")
    scale.Parent = button
    local canHover = UserInputService.MouseEnabled -- a touch never leaves, so a phone gets no hover state

    -- a halo just outside a primary button, and a line of light along its top
    local halo = Instance.new("Frame")
    halo.Name = "Halo"
    halo.BackgroundTransparency = 1
    halo.AnchorPoint = Vector2.new(0.5, 0.5)
    halo.Position = UDim2.fromScale(0.5, 0.5)
    halo.Size = UDim2.new(1, 7, 1, 7)
    halo.ZIndex = button.ZIndex
    corner(halo, UiTheme.Corner + 3)
    local haloEdge = stroke(halo, C.Accent, 0.65, 3)
    halo.Parent = button
    local gloss = Instance.new("Frame")
    gloss.Name = "Gloss"
    gloss.BackgroundColor3 = Color3.new(1, 1, 1)
    gloss.BackgroundTransparency = 0.72
    gloss.BorderSizePixel = 0
    gloss.Position = UDim2.fromOffset(2, 1)
    gloss.Size = UDim2.new(1, -4, 0, 1)
    gloss.Parent = button

    local hovered = false
    local function iconGrow(size)
        local picture = button:FindFirstChild("Icon") and button.Icon:FindFirstChild("Image")
        if picture then
            TweenService:Create(picture, BOUNCE, { Size = UDim2.fromScale(size, size) }):Play()
        end
    end
    local function paint()
        local toneName = button:GetAttribute("Tone")
        local tone = BUTTON_TONES[toneName] or BUTTON_TONES.Quiet
        local lit = hovered and button.Active
        -- a button that can't be pressed must not look as if it can: it sinks into the panel, its words go quiet. A state
        -- shown on a button (the Active tone: OWNED, WIELDING, ON) keeps its colours, since it says something true
        local disabled = not button.Active and toneName ~= "Active"
        button.BackgroundColor3 = if lit then tone.back:Lerp(tone.edge, 0.25) else tone.back
        button.BackgroundTransparency = if disabled then 0.55 elseif tone.glow then 0 else 0.08
        button.TextColor3 = if disabled then C.Muted else tone.text
        halo.Visible = tone.glow ~= nil and button.Active and button.AutomaticSize == Enum.AutomaticSize.None
        gloss.Visible = tone.glow ~= nil and not disabled
        if tone.glow then
            haloEdge.Color = tone.glow
        end
        edge.Color = tone.edge
        edge.Transparency = if button.Active then 0.05 else 0.6
        if not edge:GetAttribute("Breathes") then -- a breathing edge (UiFx.attention) is its tween's: writing here fought it
            edge.Thickness = if lit then 2 else 1
        end
    end
    button:SetAttribute("Tone", toneName)
    button:GetAttributeChangedSignal("Tone"):Connect(paint)
    button:GetPropertyChangedSignal("Active"):Connect(function()
        paint()
        if not button.Active then -- disabled under the pointer: it drops its hover size with its hover colours
            TweenService:Create(scale, EASE, { Scale = 1 }):Play()
            iconGrow(0.86)
        elseif hovered then
            TweenService:Create(scale, BOUNCE, { Scale = 1.035 }):Play()
        end
    end)
    button.MouseEnter:Connect(function()
        if not canHover then
            return
        end
        hovered = true
        paint()
        if button.Active then
            TweenService:Create(scale, BOUNCE, { Scale = 1.035 }):Play()
            iconGrow(1.02)
            UiFx.sweep(button, (BUTTON_TONES[button:GetAttribute("Tone")] or BUTTON_TONES.Quiet).edge:Lerp(Color3.new(1, 1, 1), 0.4))
        end
    end)
    button.MouseLeave:Connect(function()
        if not canHover then
            return
        end
        hovered = false
        paint()
        TweenService:Create(scale, EASE, { Scale = 1 }):Play()
        iconGrow(0.86)
    end)
    button.InputBegan:Connect(function(input)
        if button.Active and (input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch) then
            TweenService:Create(scale, EASE, { Scale = 0.94 }):Play()
            UiFx.ripple(button, input.Position.X, input.Position.Y, (BUTTON_TONES[button:GetAttribute("Tone")] or BUTTON_TONES.Quiet).edge)
        end
    end)
    button.InputEnded:Connect(function(input)
        if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then
            TweenService:Create(scale, BOUNCE, { Scale = if hovered and button.Active then 1.035 else 1 }):Play()
        end
    end)
    apply(button, copy)
    paint()
    return button
end

-- A round on-screen button for touch players (Strike, Dash ...), in the interface's colours.
function UiKit.touchButton(button, text)
    button.BackgroundColor3 = C.AccentDeep
    button.BackgroundTransparency = 0.2
    button.BorderSizePixel = 0
    button.FontFace = UiTheme.Fonts.Title
    button.TextScaled = true
    button.TextColor3 = C.Text
    button.Text = text
    corner(button, 999)
    stroke(button, C.Accent, 0.1, 2)
    UiKit.padding(button, 7, 7)
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
    -- a band of light running along what's been filled, so a bar is never quite still
    fill.ClipsDescendants = true
    local run = Instance.new("Frame")
    run.Name = "Run"
    run.BackgroundColor3 = Color3.new(1, 1, 1)
    run.BorderSizePixel = 0
    run.Position = UDim2.fromScale(-0.5, 0)
    run.Size = UDim2.fromScale(0.4, 1)
    local runFade = Instance.new("UIGradient")
    runFade.Transparency = NumberSequence.new({
        NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.55), NumberSequenceKeypoint.new(1, 1),
    })
    runFade.Parent = run
    run.Parent = fill
    TweenService:Create(run, TweenInfo.new(1.5, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, false, 1.4), { Position = UDim2.fromScale(1.1, 0) }):Play()
    apply(track, copy)
    return track
end

-- A bar's colour, eased: gold when what it counts is ready to be taken (a breakthrough)
function UiKit.setBarColor(bar, color)
    TweenService:Create(bar:FindFirstChild("Fill"), TweenInfo.new(0.3), { BackgroundColor3 = color }):Play()
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
    scroll.ScrollBarThickness = 3
    scroll.ScrollBarImageColor3 = C.Edge
    scroll.ScrollBarImageTransparency = 0.3
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
    card.BackgroundColor3 = C.Raised
    card.BackgroundTransparency = 0.35
    card.BorderSizePixel = 0
    corner(card)
    local edge = stroke(card, C.EdgeDim, 0.35)
    if UserInputService.MouseEnabled then -- the row under the pointer lights up
        local rest = card.BackgroundTransparency
        card.MouseEnter:Connect(function()
            TweenService:Create(card, EASE, { BackgroundTransparency = rest - 0.2 }):Play()
            TweenService:Create(edge, EASE, { Color = C.Edge, Transparency = 0.05 }):Play()
        end)
        card.MouseLeave:Connect(function()
            TweenService:Create(card, EASE, { BackgroundTransparency = rest }):Play()
            TweenService:Create(edge, EASE, { Color = C.EdgeDim, Transparency = 0.35 }):Play()
        end)
    end
    if stripeColor then
        local stripe = Instance.new("Frame")
        stripe.Name = "Stripe"
        stripe.BorderSizePixel = 0
        stripe.BackgroundColor3 = stripeColor
        stripe.Size = UDim2.new(0, 3, 1, 0)
        stripe.Parent = card
    end
    apply(card, copy)
    return card
end

function UiKit.tag(text, color)
    color = color or C.Accent
    local tag = UiKit.label({
        Name = "Tag", Font = "Strong", Text = string.upper(text), TextSize = 10, TextColor3 = color,
        BackgroundColor3 = color, BackgroundTransparency = 0.85, AutomaticSize = Enum.AutomaticSize.X,
        Size = UDim2.fromOffset(0, 16), TextXAlignment = Enum.TextXAlignment.Center,
    })
    corner(tag, 2)
    stroke(tag, color, 0.4)
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
    corner(box)
    local edge = stroke(box, C.EdgeDim, 0.2)
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

-- An empty list's message: its first line as a headline, a short gold rule, and the rest (what to do about it) under
-- it in the quiet colour, set down a little from the top so the window doesn't read as broken.
function UiKit.empty(parent, text)
    local headline, hint = string.match(text, "^([^\n]*)\n?(.*)$")
    local box = Instance.new("Frame")
    box.Name = "Empty"
    box.BackgroundTransparency = 1
    box.AutomaticSize = Enum.AutomaticSize.Y
    box.Size = UDim2.new(1, 0, 0, 0)
    box.Parent = parent
    UiKit.padding(box, 18, 26)
    UiKit.list(box, { Padding = UDim.new(0, 8), HorizontalAlignment = Enum.HorizontalAlignment.Center })
    UiKit.label({
        Name = "Headline", Font = "Title", Text = headline, TextSize = 16, TextColor3 = C.AccentBright, TextWrapped = true,
        TextXAlignment = Enum.TextXAlignment.Center, AutomaticSize = Enum.AutomaticSize.Y, Size = UDim2.new(1, 0, 0, 0),
        LayoutOrder = 1, Parent = box,
    })
    if hint ~= "" then
        local rule = Instance.new("Frame")
        rule.Name = "Rule"
        rule.BorderSizePixel = 0
        rule.BackgroundColor3 = C.Edge
        rule.BackgroundTransparency = 0.3
        rule.Size = UDim2.fromOffset(46, 1)
        rule.LayoutOrder = 2
        rule.Parent = box
        UiKit.label({
            Name = "Hint", Text = hint, TextSize = 13, TextColor3 = C.Muted, TextWrapped = true,
            TextXAlignment = Enum.TextXAlignment.Center, AutomaticSize = Enum.AutomaticSize.Y, Size = UDim2.new(1, 0, 0, 0),
            LayoutOrder = 3, Parent = box,
        })
    end
    return box
end

return UiKit
