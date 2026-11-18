-- The breakthrough's title card, in the game's own "Cultivation Bold" look: a small line above (the kind of step), the realm or the
-- rank in big heavy letters in the realm's colour, the rank under it for a new realm, a line of light, then what was gained in
-- plain words, and what comes next. It is drawn into the sequence's own ScreenGui (BreakthroughShow) and scales with the HUD.
--
--   Card.new(gui, info)  -> card   gui: the ScreenGui; info: BreakthroughStyles.describe
--   card.show()          comes in (a settle from large, a sweep of light through the letters, the lines one by one)
--   card.hide(seconds)   fades away (and is destroyed after)
--   card.destroy()
local TweenService = game:GetService("TweenService")

local UI = script.Parent.Parent:WaitForChild("UI")
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local applyHudScale = require(UI:WaitForChild("HudScale"))

local C = UiTheme.Colors

local Card = {}

local function tween(instance, seconds, goal, style, direction)
    local made = TweenService:Create(instance, TweenInfo.new(seconds, style or Enum.EasingStyle.Quad, direction or Enum.EasingDirection.Out), goal)
    made:Play()
    return made
end

local WIDTH = 760

function Card.new(gui, info)
    local grade, theme = info.Grade, info.Theme
    local big = grade.Name == "Realm" or grade.Name == "Apex"
    local headlineSize = if grade.Name == "Apex" then 68 elseif big then 62 elseif grade.Name == "Milestone" then 50 else 38
    local light = theme.Hot:Lerp(Color3.new(1, 1, 1), 0.45)
    local mainColor = theme.Main:Lerp(Color3.new(1, 1, 1), 0.15)
    if theme.Realm == 9 then -- the Void's own colour is a black core: its card takes the ice
        mainColor = theme.Hot
    end

    local group = Instance.new("CanvasGroup")
    group.Name = "BreakthroughCard"
    group.BackgroundTransparency = 1
    group.AnchorPoint = Vector2.new(0.5, 0.5)
    group.Position = UDim2.fromScale(0.5, if grade.Name == "Step" then 0.3 else 0.36)
    group.GroupTransparency = 1
    group.ZIndex = 20
    group.Parent = gui

    local lines = info.Lines
    local rankLine = big and info.Rank.Level == 1
    local y = 0
    local height = 0

    -- the kind of step, small, above
    local kicker = UiKit.label({
        Name = "Kicker", Font = "Heavy", TextSize = if big then 17 else 14, TextColor3 = light, Text = info.Subline,
        TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.fromOffset(WIDTH, 22), Position = UDim2.fromOffset(0, y), ZIndex = 21, Parent = group,
    })
    UiKit.outline(kicker, 1)
    y += 26

    -- the headline: a wide soft glow of the realm's colour under it, then the letters (one label sized to fit, heavy and outlined)
    local headHeight = headlineSize + 14
    local function headline(name, props)
        local label = UiKit.label({
            Name = name, Font = "Title", Text = info.Headline, TextXAlignment = Enum.TextXAlignment.Center, TextScaled = true,
            AnchorPoint = Vector2.new(0.5, 0), Size = UDim2.fromOffset(WIDTH, headHeight), Position = UDim2.fromOffset(WIDTH / 2, y), ZIndex = 21, Parent = group,
        })
        local limit = Instance.new("UITextSizeConstraint")
        limit.MaxTextSize = headlineSize
        limit.MinTextSize = 14
        limit.Parent = label
        for key, value in props do
            label[key] = value
        end
        return label
    end
    local glow = headline("Glow", { TextColor3 = mainColor, TextTransparency = 0.68, ZIndex = 21 })
    local glowStroke = Instance.new("UIStroke")
    glowStroke.Color = mainColor
    glowStroke.Thickness = 7
    glowStroke.Transparency = 0.68
    glowStroke.LineJoinMode = Enum.LineJoinMode.Round
    glowStroke.Parent = glow
    local word = headline("Word", { TextColor3 = Color3.new(1, 1, 1), ZIndex = 22 })
    local wordStroke = Instance.new("UIStroke")
    wordStroke.Color = Color3.fromRGB(14, 12, 34)
    wordStroke.Thickness = 3.5
    wordStroke.LineJoinMode = Enum.LineJoinMode.Round
    wordStroke.Parent = word
    -- the letters' colour: white at the top running into the realm's light, a band of white light sweeps through them on arrival
    local shine = Instance.new("UIGradient")
    shine.Color = ColorSequence.new({
        ColorSequenceKeypoint.new(0, Color3.new(1, 1, 1)),
        ColorSequenceKeypoint.new(0.4, light),
        ColorSequenceKeypoint.new(1, mainColor),
    })
    shine.Rotation = 90
    shine.Parent = word
    local scale = Instance.new("UIScale")
    scale.Scale = 1.35
    scale.Parent = word
    local glowScale = Instance.new("UIScale")
    glowScale.Scale = 1.35
    glowScale.Parent = glow
    y += headHeight + 2

    if rankLine then
        local rank = UiKit.label({
            Name = "Rank", Font = "Title", TextSize = if grade.Name == "Apex" then 30 else 26, TextColor3 = C.Highlight, Text = info.RankName,
            TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.fromOffset(WIDTH, 34), Position = UDim2.fromOffset(0, y), ZIndex = 21, Parent = group,
        })
        UiKit.outline(rank, 2)
        y += 36
    end

    -- a line of light, as wide as the card, fading at both ends
    local rule = Instance.new("Frame")
    rule.Name = "Rule"
    rule.BorderSizePixel = 0
    rule.BackgroundColor3 = mainColor
    rule.AnchorPoint = Vector2.new(0.5, 0)
    rule.Position = UDim2.new(0.5, 0, 0, y + 6)
    rule.Size = UDim2.fromOffset(0, 2)
    rule.ZIndex = 21
    rule.Parent = group
    local ruleFade = Instance.new("UIGradient")
    ruleFade.Transparency = NumberSequence.new({
        NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0), NumberSequenceKeypoint.new(0.75, 0), NumberSequenceKeypoint.new(1, 1),
    })
    ruleFade.Parent = rule
    y += 16

    -- what was gained, in plain words, one line after another
    local rows = {}
    for index, text in lines do
        local row = Instance.new("Frame")
        row.Name = "Gain" .. index
        row.BackgroundTransparency = 1
        row.Size = UDim2.fromOffset(WIDTH, 26)
        row.Position = UDim2.fromOffset(0, y)
        row.ZIndex = 21
        row.Parent = group
        local label = UiKit.label({
            Name = "Text", Font = "Strong", TextSize = if big then 19 else 17, TextColor3 = C.Text, Text = text,
            TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.fromScale(1, 1), ZIndex = 22, TextTransparency = 1, Parent = row,
        })
        UiKit.outline(label, 1)
        table.insert(rows, label)
        y += 28
    end
    local nextLabel = UiKit.label({
        Name = "Next", Font = "Body", TextSize = 14, TextColor3 = C.Muted, Text = info.Next, TextXAlignment = Enum.TextXAlignment.Center,
        Size = UDim2.fromOffset(WIDTH, 20), Position = UDim2.fromOffset(0, y + 4), ZIndex = 21, TextTransparency = 1, Parent = group,
    })
    UiKit.outline(nextLabel, 1)
    y += 28
    height = y
    group.Size = UDim2.fromOffset(WIDTH, height)
    applyHudScale(group)
    -- UIScale's pivot is the group's centre: keep the card centred on its anchor
    kicker.TextTransparency = 1

    local card = { group = group, gone = false }

    function card.show()
        if card.gone then
            return
        end
        tween(group, 0.35, { GroupTransparency = 0 })
        tween(scale, 0.55, { Scale = 1 }, Enum.EasingStyle.Back)
        tween(glowScale, 0.55, { Scale = 1 }, Enum.EasingStyle.Back)
        tween(kicker, 0.4, { TextTransparency = 0 })
        tween(rule, 0.6, { Size = UDim2.fromOffset(WIDTH * 0.8, 2) }, Enum.EasingStyle.Cubic)
        -- the sweep of light through the letters
        if big or grade.Name == "Milestone" then
            local sweep = Instance.new("UIGradient")
            sweep.Color = ColorSequence.new({
                ColorSequenceKeypoint.new(0, Color3.new(1, 1, 1)), ColorSequenceKeypoint.new(0.42, Color3.new(1, 1, 1)),
                ColorSequenceKeypoint.new(0.5, theme.Hot:Lerp(Color3.new(1, 1, 1), 0.2)), ColorSequenceKeypoint.new(0.58, Color3.new(1, 1, 1)),
                ColorSequenceKeypoint.new(1, Color3.new(1, 1, 1)),
            })
            sweep.Offset = Vector2.new(-1, 0)
            sweep.Parent = glow
            tween(sweep, 1.3, { Offset = Vector2.new(1, 0) }, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut)
        end
        for index, label in rows do
            task.delay(0.45 + 0.28 * (index - 1), function()
                if not card.gone and label.Parent then
                    tween(label, 0.4, { TextTransparency = 0 })
                end
            end)
        end
        task.delay(0.45 + 0.28 * #rows + 0.1, function()
            if not card.gone and nextLabel.Parent then
                tween(nextLabel, 0.5, { TextTransparency = 0 })
            end
        end)
    end

    function card.hide(seconds)
        if card.gone then
            return
        end
        card.gone = true
        seconds = seconds or 0.5
        tween(group, seconds, { GroupTransparency = 1 })
        tween(scale, seconds, { Scale = 1.06 })
        task.delay(seconds + 0.05, function()
            group:Destroy()
        end)
    end

    function card.destroy()
        card.gone = true
        group:Destroy()
    end

    return card
end

return Card
