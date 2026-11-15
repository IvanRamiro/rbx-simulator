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
--   keycapOn(button, key)       that hint inside a button's right end; keyRoom(button) is what its words must leave free
--   fitWords(text, size, room)  words at `size`, or smaller if they would not fit across `room`
--   pillShape(button, height)   a button rounded into a pill, its halo and light following
--   wordsWidth(text)            a text object's words' width in its own units
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
    corner(frame, UiTheme.Radius.Panel)
    stroke(frame, C.Edge, 0.1, UiTheme.Stroke.Window)
    -- the glow: a soft wide rim just inside the edge
    local rim = Instance.new("Frame")
    rim.Name = "Glow"
    rim.BackgroundTransparency = 1
    rim.AnchorPoint = Vector2.new(0.5, 0.5)
    rim.Position = UDim2.fromScale(0.5, 0.5)
    rim.Size = UDim2.new(1, -4, 1, -4)
    rim.Parent = frame
    corner(rim, UiTheme.Radius.Panel - 2)
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

-- A section's heading across its parent: its NAME in heavy gold capitals on the left, a gold line running from it to the
-- right edge (one heading style everywhere: a shop's sections, the titles' groups). props: Color, TextSize, and any
-- Frame properties (Position, Size, LayoutOrder ...).
function UiKit.header(parent, text, props)
    local copy = table.clone(props or {})
    local color = copy.Color or C.Edge
    local size = copy.TextSize or UiTheme.Text.Heading
    copy.Color, copy.TextSize = nil, nil
    local row = Instance.new("Frame")
    row.Name = "Header"
    row.BackgroundTransparency = 1
    row.Size = UDim2.new(1, 0, 0, size + 10)
    apply(row, copy)
    row.Parent = parent
    local word = UiKit.label({
        Name = "Text", Font = "Heavy", Text = string.upper(text), TextSize = size, TextColor3 = color,
        AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.fromScale(0, 0.5), AutomaticSize = Enum.AutomaticSize.X,
        Size = UDim2.new(0, 0, 1, 0), Parent = row,
    })
    UiKit.outline(word, 1)
    -- the line from the word to the edge, fading out; it follows the word's width
    local line = Instance.new("Frame")
    line.Name = "Rule"
    line.BorderSizePixel = 0
    line.BackgroundColor3 = C.Edge
    line.AnchorPoint = Vector2.new(1, 0.5)
    line.Position = UDim2.fromScale(1, 0.5)
    line.Parent = row
    local fade = Instance.new("UIGradient")
    fade.Transparency = NumberSequence.new(0.35, 1)
    fade.Parent = line
    local function fit()
        line.Size = UDim2.new(1, -(word.TextBounds.X + UiTheme.Space.S), 0, 1)
    end
    word:GetPropertyChangedSignal("TextBounds"):Connect(fit)
    fit()
    return row, word
end

-- ---------- a window's frame: one title band and one close button for every window and dialog ----------
-- The title band across a window's top: its name in Merriweather, outlined, centred over a gold rule; the close button at
-- its right. Returns the title label and the close button. Its height is UiTheme.Height.TitleBar.
function UiKit.titleBar(frame, text)
    local band = Instance.new("Frame")
    band.Name = "TitleBar"
    band.BackgroundColor3 = C.Well
    band.BackgroundTransparency = 0.45
    band.BorderSizePixel = 0
    band.Size = UDim2.new(1, 0, 0, UiTheme.Height.TitleBar)
    band.ZIndex = frame.ZIndex
    band.Parent = frame
    corner(band, UiTheme.Radius.Window)
    -- squares off the band's lower corners, so only the window's own top corners are round
    local foot = Instance.new("Frame")
    foot.Name = "Foot"
    foot.BackgroundColor3 = C.Well
    foot.BackgroundTransparency = 0.45
    foot.BorderSizePixel = 0
    foot.AnchorPoint = Vector2.new(0, 1)
    foot.Position = UDim2.fromScale(0, 1)
    foot.Size = UDim2.new(1, 0, 0, UiTheme.Radius.Window)
    foot.ZIndex = frame.ZIndex
    foot.Parent = band
    local rule = Instance.new("Frame")
    rule.Name = "Rule"
    rule.BorderSizePixel = 0
    rule.BackgroundColor3 = C.Edge
    rule.AnchorPoint = Vector2.new(0.5, 1)
    rule.Position = UDim2.fromScale(0.5, 1)
    rule.Size = UDim2.new(1, -UiTheme.Space.L * 2, 0, 1)
    rule.ZIndex = frame.ZIndex + 1
    rule.Parent = band
    local fade = Instance.new("UIGradient")
    fade.Transparency = NumberSequence.new({
        NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.1), NumberSequenceKeypoint.new(1, 1),
    })
    fade.Parent = rule
    local closeSize = UiTheme.Height.Close
    local title = UiKit.label({
        Name = "Title", Font = "Header", Text = text, TextSize = UiTheme.Text.WindowTitle, TextColor3 = C.AccentBright,
        TextXAlignment = Enum.TextXAlignment.Center, TextTruncate = Enum.TextTruncate.AtEnd,
        AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
        -- room for the close button on both sides, so the title stays centred on the window
        Size = UDim2.new(1, -(closeSize + UiTheme.Space.M * 2) * 2, 0, UiTheme.Text.WindowTitle + 6),
        ZIndex = frame.ZIndex + 1, Parent = band,
    })
    UiKit.outline(title, 2)
    local close = UiKit.closeButton(closeSize)
    close.AnchorPoint = Vector2.new(1, 0.5)
    close.Position = UDim2.new(1, -UiTheme.Space.M + 2, 0.5, 0)
    close.ZIndex = frame.ZIndex + 2
    close.Parent = band
    return title, close, band
end

-- The close button: a red square with a drawn cross (no glyph: every font draws an X differently)
function UiKit.closeButton(size)
    local button = UiKit.button({ Name = "Close", Text = "", Tone = "Danger", Size = UDim2.fromOffset(size, size) })
    for _, turn in { 45, -45 } do
        local bar = Instance.new("Frame")
        bar.Name = "Cross"
        bar.BorderSizePixel = 0
        bar.BackgroundColor3 = C.Text
        bar.AnchorPoint = Vector2.new(0.5, 0.5)
        bar.Position = UDim2.fromScale(0.5, 0.5)
        bar.Size = UDim2.new(0.46, 0, 0, 3)
        bar.Rotation = turn
        bar.ZIndex = button.ZIndex + 1
        bar.Parent = button
        corner(bar, 2)
    end
    return button
end

-- A tab: a framed tile, gold while it is the one showing. UiKit.selectTab(button, on) switches it.
function UiKit.tab(props)
    local copy = table.clone(props or {})
    copy.Font = copy.Font or "Heavy"
    copy.TextSize = copy.TextSize or 14
    copy.Tone = "Tile"
    local button = UiKit.button(copy)
    button:SetAttribute("EdgeThickness", UiTheme.Stroke.Button)
    return button
end
function UiKit.selectTab(button, on)
    button:SetAttribute("Tone", if on then "Highlight" else "Tile")
end

-- A small value pill: an icon and a number or a word, on a dark well with a fine gold edge (a balance, a timer, a count).
-- Returns the pill and its label.
function UiKit.pill(image, text, props)
    local pill = Instance.new("Frame")
    pill.Name = "Pill"
    pill.BackgroundColor3 = C.Well
    pill.BackgroundTransparency = 0.25
    pill.BorderSizePixel = 0
    pill.AutomaticSize = Enum.AutomaticSize.X
    pill.Size = UDim2.fromOffset(0, 30)
    corner(pill, 15)
    stroke(pill, C.EdgeDim, 0.2, 1.5)
    local pad = UiKit.padding(pill, 12, 0)
    pad.PaddingLeft = UDim.new(0, if image then 6 else 12)
    UiKit.list(pill, { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 6), VerticalAlignment = Enum.VerticalAlignment.Center })
    if image then
        local picture = Instance.new("ImageLabel")
        picture.Name = "Icon"
        picture.BackgroundTransparency = 1
        picture.Image = image
        picture.Size = UDim2.fromOffset(22, 22)
        picture.Parent = pill
    end
    local label = UiKit.label({
        Name = "Value", Font = "Heavy", TextSize = 14, Text = text or "", AutomaticSize = Enum.AutomaticSize.X,
        Size = UDim2.fromOffset(0, 20), LayoutOrder = 2, Parent = pill,
    })
    UiKit.outline(label, 1.5)
    apply(pill, props)
    return pill, label
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
    corner(box, UiTheme.Radius.Chip)
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
    Danger = { back = C.DangerDeep, edge = C.Danger, text = C.Text, outlined = true },
    Active = { back = Color3.fromRGB(14, 112, 118), edge = Color3.fromRGB(120, 255, 236), text = Color3.new(1, 1, 1), glow = Color3.fromRGB(70, 240, 220), outlined = true }, -- something running, right now
    Buy = { back = C.Buy, edge = C.BuyBright, text = Color3.new(1, 1, 1), glow = C.Buy, outlined = true }, -- a price (Robux or Spirit Stones)
    Tile = { back = C.Raised, edge = C.Edge, text = C.Text }, -- a rail tile or a tab: quiet, framed in gold
    Go = { back = C.Buy, edge = C.BuyBright, text = Color3.new(1, 1, 1), glow = C.Buy, outlined = true }, -- a positive action (Equip, Hatch, Claim): green
}

-- props.Tone picks the colours; button:SetAttribute("Tone", name) changes them later
function UiKit.button(props)
    local copy = table.clone(props or {})
    local toneName = copy.Tone or "Quiet"
    copy.Tone = nil
    local button = Instance.new("TextButton")
    button.AutoButtonColor = false
    button.BorderSizePixel = 0
    button.FontFace = UiTheme.Fonts.Heavy -- every button's words in the heavy face (Cultivation Bold)
    button.TextSize = UiTheme.Text.Button
    button.TextStrokeColor3 = C.Outline
    if copy.Font then
        button.FontFace = UiTheme.Fonts[copy.Font]
        copy.Font = nil
    end
    corner(button, UiTheme.Radius.Button)
    local edge = stroke(button, C.Edge, 0.15, UiTheme.Stroke.Button)
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
        -- white words on a bright fill carry a dark edge, as the bold look's outlined words do
        button.TextStrokeTransparency = if tone.outlined and not disabled then 0.45 else 1
        halo.Visible = tone.glow ~= nil and button.Active and button.AutomaticSize == Enum.AutomaticSize.None
        gloss.Visible = tone.glow ~= nil and not disabled
        if tone.glow then
            haloEdge.Color = tone.glow
        end
        edge.Color = tone.edge
        edge.Transparency = if button.Active then 0.05 else 0.6
        if not edge:GetAttribute("Breathes") then -- a breathing edge (UiFx.attention) is its tween's: writing here fought it
            edge.Thickness = (button:GetAttribute("EdgeThickness") or UiTheme.Stroke.Button) + (if lit then 1 else 0)
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
    button.BackgroundColor3 = C.Panel
    button.BackgroundTransparency = 0.12
    button.BorderSizePixel = 0
    button.FontFace = UiTheme.Fonts.Heavy -- the bold look: heavy words, a dark edge, a gold ring
    button.TextScaled = true
    button.TextColor3 = C.Text
    button.TextStrokeColor3 = C.Outline
    button.TextStrokeTransparency = 0.3
    button.Text = string.upper(text)
    corner(button, 999)
    stroke(button, C.Edge, 0.05, 2.5)
    local size = Instance.new("UITextSizeConstraint")
    size.MaxTextSize = 15
    size.MinTextSize = 10
    size.Parent = button
    UiKit.padding(button, 8, 8)
end

local KEYCAP_SIZE = Vector2.new(24, 22)
local KEYCAP_INSET = UiTheme.Space.L -- from the button's right end, on every button that carries one

function UiKit.keycap(key)
    local cap = UiKit.label({
        Name = "Keycap", Font = "Strong", Text = key, TextSize = 13, TextColor3 = C.AccentBright,
        TextXAlignment = Enum.TextXAlignment.Center, BackgroundTransparency = 0.3,
        BackgroundColor3 = C.Well, Size = UDim2.fromOffset(KEYCAP_SIZE.X, KEYCAP_SIZE.Y),
    })
    corner(cap, 2)
    stroke(cap, C.Accent, 0.35)
    cap.Visible = not UserInputService.TouchEnabled or UserInputService.KeyboardEnabled
    return cap
end

-- A key's hint inside a button, at its right end: the same size and inset on every button that has one (Cultivate, DRAW).
-- The button's words stay centred on the whole button, so they must leave this much free at each end, or they run into the
-- key: UiKit.keyRoom(button) gives it (0 where the hint is hidden, on a touch screen).
function UiKit.keycapOn(button, key)
    local cap = UiKit.keycap(key)
    cap.AnchorPoint = Vector2.new(1, 0.5)
    cap.Position = UDim2.new(1, -KEYCAP_INSET, 0.5, 0)
    cap.Parent = button
    return cap
end
function UiKit.keyRoom(button)
    local cap = button:FindFirstChild("Keycap")
    return if cap and cap.Visible then KEYCAP_INSET + KEYCAP_SIZE.X + UiTheme.Space.S else 0
end

-- How wide a text object's words are, in its own units: TextBounds is measured on the screen, after every UIScale on it and
-- above it (the HUD's scale, a button's hover), so it is divided by them all.
function UiKit.wordsWidth(textObject)
    local scale = 1
    local x = textObject
    while x and not x:IsA("LayerCollector") do
        local uiScale = x:FindFirstChildOfClass("UIScale")
        if uiScale then
            scale *= uiScale.Scale
        end
        x = x.Parent
    end
    return textObject.TextBounds.X / math.max(scale, 0.01)
end

-- Sets a button's words to `wanted` points, or smaller if that is what it takes for them to fit across `room` (its own units):
-- the words shrink rather than run under a key's hint or off the button's ends.
function UiKit.fitWords(textObject, wanted, room)
    textObject.TextSize = wanted
    local width = UiKit.wordsWidth(textObject)
    if width > room and width > 0 then
        textObject.TextSize = math.max(1, math.floor(wanted * room / width))
    end
end

-- Rounds a button into a pill of the given height: its corners, its halo, its light layer and its line of gloss keep to the
-- curves. Every pill on the HUD (Cultivate, the breakthrough, DRAW) is shaped here, so they match.
function UiKit.pillShape(button, height)
    local half = height // 2
    button:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, half)
    local halo = button:FindFirstChild("Halo")
    if halo then
        halo:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, half + 3)
    end
    button:SetAttribute("RoundLight", half)
    local layer = button:FindFirstChild("LightLayer")
    if layer then
        layer:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, half)
    end
    local gloss = button:FindFirstChild("Gloss")
    if gloss then
        gloss.Position = UDim2.fromOffset(half, 2)
        gloss.Size = UDim2.new(1, -half * 2, 0, 1)
    end
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
    scroll.ScrollBarThickness = 4
    scroll.ScrollBarImageColor3 = C.Edge
    scroll.ScrollBarImageTransparency = 0.3
    scroll.CanvasSize = UDim2.new()
    scroll.AutomaticCanvasSize = Enum.AutomaticSize.Y
    scroll.ScrollingDirection = Enum.ScrollingDirection.Y
    apply(scroll, props)
    local pad = Instance.new("UIPadding") -- room for the bar, and for each card's edge
    pad.PaddingRight = UDim.new(0, 10)
    pad.PaddingTop, pad.PaddingBottom, pad.PaddingLeft = UDim.new(0, 2), UDim.new(0, 4), UDim.new(0, 2)
    pad.Parent = scroll
    UiKit.list(scroll, { Padding = UDim.new(0, UiTheme.Space.S) })
    return scroll
end

function UiKit.card(props)
    local copy = table.clone(props or {})
    local stripeColor = copy.Stripe
    copy.Stripe = nil
    local card = Instance.new("Frame")
    card.BackgroundColor3 = C.Raised
    card.BackgroundTransparency = 0.15
    card.BorderSizePixel = 0
    corner(card, UiTheme.Radius.Card)
    local edge = stroke(card, C.EdgeDim, 0.3, UiTheme.Stroke.Card)
    if UserInputService.MouseEnabled then -- the row under the pointer lights up
        local restEdge, restEdgeTransparency -- (read on entering, so a card redrawn since keeps its new edge)
        local rest
        local leftAt = -1
        card.MouseEnter:Connect(function()
            if os.clock() - leftAt > EASE.Time + 0.02 then -- never read mid-tween: the last leave has settled
                rest = card.BackgroundTransparency
                restEdge, restEdgeTransparency = edge.Color, edge.Transparency
            end
            TweenService:Create(card, EASE, { BackgroundTransparency = math.max(0, rest - 0.2) }):Play()
            TweenService:Create(edge, EASE, { Color = if edge:GetAttribute("Keep") then edge.Color else C.Edge, Transparency = 0.05 }):Play()
        end)
        card.MouseLeave:Connect(function()
            leftAt = os.clock()
            TweenService:Create(card, EASE, { BackgroundTransparency = rest or card.BackgroundTransparency }):Play()
            TweenService:Create(edge, EASE, { Color = restEdge or C.EdgeDim, Transparency = restEdgeTransparency or 0.3 }):Play()
        end)
    end
    if stripeColor then -- a colour that means something (a rarity, an element): the card's edge, and a pill down its left
        edge.Color = stripeColor
        edge.Transparency = 0.35
        edge:SetAttribute("Keep", true)
        local stripe = Instance.new("Frame")
        stripe.Name = "Stripe"
        stripe.BorderSizePixel = 0
        stripe.BackgroundColor3 = stripeColor
        stripe.Position = UDim2.fromOffset(0, UiTheme.Space.M)
        stripe.Size = UDim2.new(0, 4, 1, -UiTheme.Space.M * 2)
        stripe.Parent = card
        corner(stripe, 2)
    end
    apply(card, copy)
    return card
end

-- A dark outline round a text object's words (the bold look: white or gold words, outlined, read over anything).
function UiKit.outline(textObject, thickness)
    local edge = Instance.new("UIStroke")
    edge.Name = "Outline"
    edge.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
    edge.Color = C.Outline
    edge.Thickness = thickness or 2
    edge.LineJoinMode = Enum.LineJoinMode.Round
    edge.Parent = textObject
    return edge
end

-- The bold look for a card made by UiKit.card: nearly solid, rounder, a thicker edge (in a colour: a pet's rarity). Its
-- hover still lights the edge.
function UiKit.boldCard(card, edgeColor)
    card.BackgroundTransparency = 0.1
    card:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, UiTheme.Radius.Card)
    local edge = card:FindFirstChildOfClass("UIStroke")
    edge.Thickness = UiTheme.Stroke.Card
    if edgeColor then
        edge.Color = edgeColor
        edge.Transparency = 0.2
        edge:SetAttribute("Keep", true)
    end
    local stripe = card:FindFirstChild("Stripe")
    if stripe then
        stripe:Destroy() -- the coloured edge says it now
    end
    return card
end

-- Words in the heavy face with a dark outline (the bold look).
function UiKit.boldLabel(props)
    local copy = table.clone(props)
    copy.Font = copy.Font or "Heavy"
    local label = UiKit.label(copy)
    UiKit.outline(label, if (copy.TextSize or 16) >= 18 then 2 else 1.5)
    return label
end

function UiKit.tag(text, color)
    color = color or C.Accent
    local tag = UiKit.label({
        Name = "Tag", Font = "Heavy", Text = string.upper(text), TextSize = 10, TextColor3 = color,
        BackgroundColor3 = color, BackgroundTransparency = 0.82, AutomaticSize = Enum.AutomaticSize.X,
        Size = UDim2.fromOffset(0, 18), TextXAlignment = Enum.TextXAlignment.Center,
    })
    corner(tag, UiTheme.Radius.Chip)
    stroke(tag, color, 0.35)
    UiKit.padding(tag, 6, 0).PaddingRight = UDim.new(0, 7) -- (a pixel spare: a width of half pixels read as not fitting)
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
    box.Size = UDim2.new(1, 0, 0, UiTheme.Height.Field)
    corner(box, UiTheme.Radius.Button)
    local edge = stroke(box, C.EdgeDim, 0.2, 1.5)
    box.Focused:Connect(function()
        edge.Color = C.Edge
    end)
    box.FocusLost:Connect(function()
        edge.Color = C.EdgeDim
    end)
    UiKit.padding(box, 12, 0)
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
    UiKit.outline(UiKit.label({
        Name = "Headline", Font = "Heavy", Text = headline, TextSize = 18, TextColor3 = C.AccentBright, TextWrapped = true,
        TextXAlignment = Enum.TextXAlignment.Center, AutomaticSize = Enum.AutomaticSize.Y, Size = UDim2.new(1, 0, 0, 0),
        LayoutOrder = 1, Parent = box,
    }), 1.5)
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
