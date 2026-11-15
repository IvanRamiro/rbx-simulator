-- The first-time tutorial (the owner, 2026-11-16: "we will just add a tutorial for the game, so player will press letter E to
-- cultivate"): a short card at the top centre (Hud.Banner) that teaches cultivating, then hands the player to the quests.
--   1. "Press E to cultivate" (a touch screen: "Tap the lotus button", the small round button by jump). Done when they sit down.
--   2. "Qi is coming in!": what Qi is for, and that the quest panel (top right) says what to do next. GOT IT ends it.
-- It shows once: only to a player on the first quest who hasn't seen it, and SKIP or the end saves that (the TutorialDone setting,
-- server/Data/Settings). A player who is past the first quest never sees it.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local UiFx = require(UI:WaitForChild("UiFx"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local KEY = GameConfig.CultivationKeybind.Name

-- wait for the saved settings and the quest step (the server sets both once the save has loaded)
while player:GetAttribute("SettingTutorialDone") == nil or player:GetAttribute("QuestStep") == nil do
    task.wait(0.5)
    if not player.Parent then
        return
    end
end

local function finish()
    player:SetAttribute("SettingTutorialDone", true) -- (at once, so it answers before the server's copy comes back)
    RemoteEvents.SettingsEvent:FireServer("TutorialDone", true)
end

if player:GetAttribute("SettingTutorialDone") == true then
    return
end
if player:GetAttribute("QuestStep") ~= 1 then -- already past the first quest: an old save, nothing to teach
    finish()
    return
end

-- ---------- the card ----------
local WIDTH, PAD = 360, UiTheme.Pad.Card
local card = UiKit.panel({ Name = "Tutorial", Brackets = false, Size = UDim2.fromOffset(WIDTH, 0), LayoutOrder = 5, Parent = Hud.Banner })
local inner = Instance.new("Frame")
inner.Name = "Inner"
inner.BackgroundTransparency = 1
inner.AutomaticSize = Enum.AutomaticSize.Y
inner.Size = UDim2.new(1, 0, 0, 0)
inner.Parent = card
UiKit.padding(inner, PAD, PAD)
UiKit.list(inner, { Padding = UDim.new(0, 6) })
local function fitHeight() -- as tall as what it holds (the quest panel's way: its own AutomaticSize would count the glow's margin)
    local drawn = card.AbsoluteSize.X
    local ratio = if drawn > 0 then card.Size.X.Offset / drawn else 1
    card.Size = UDim2.fromOffset(WIDTH, math.ceil(inner.AbsoluteSize.Y * ratio))
end
inner:GetPropertyChangedSignal("AbsoluteSize"):Connect(fitHeight)

-- the header: HOW TO PLAY, the step, SKIP
local header = Instance.new("Frame")
header.Name = "Header"
header.BackgroundTransparency = 1
header.Size = UDim2.new(1, 0, 0, 22)
header.LayoutOrder = 1
header.Parent = inner
UiKit.boldLabel({ Name = "Word", TextSize = 13, Text = "HOW TO PLAY", TextColor3 = C.Edge, Size = UDim2.new(0.5, 0, 1, 0), Parent = header })
local stepLabel = UiKit.boldLabel({
    Name = "Step", TextSize = 11, TextColor3 = C.Muted, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -78, 0.5, 0),
    Size = UDim2.fromOffset(40, 14), TextXAlignment = Enum.TextXAlignment.Right, Parent = header,
})
local skip = UiKit.button({
    Name = "Skip", TextSize = 12, Text = "SKIP", Tone = "Quiet", AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.fromScale(1, 0.5),
    Size = UDim2.fromOffset(64, 30), Parent = header,
})
-- a thumb's room round SKIP on a phone (it is 30 tall: 24 pixels there), as the quest panel's fold does
local skipHit = Instance.new("TextButton")
skipHit.Name = "Hit"
skipHit.Text = ""
skipHit.BackgroundTransparency = 1
skipHit.AnchorPoint = Vector2.new(0.5, 0.5)
skipHit.Position = UDim2.fromScale(0.5, 0.5)
skipHit.Size = UDim2.new(1, 12, 0, 56)
skipHit.ZIndex = skip.ZIndex + 3
skipHit.Parent = skip

-- the step's line: big words, with the key (or the lotus button's picture) in it
local line = Instance.new("Frame")
line.Name = "Line"
line.BackgroundTransparency = 1
line.Size = UDim2.new(1, 0, 0, 30)
line.LayoutOrder = 2
line.Parent = inner
UiKit.list(line, { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 7) })
local body = UiKit.label({
    Name = "Body", Font = "Strong", TextSize = 13, TextColor3 = C.Text, TextWrapped = true, AutomaticSize = Enum.AutomaticSize.Y,
    Size = UDim2.new(1, 0, 0, 0), LayoutOrder = 3, Parent = inner,
})
local actions = Instance.new("Frame")
actions.Name = "Actions"
actions.BackgroundTransparency = 1
actions.Size = UDim2.new(1, 0, 0, UiTheme.Height.ButtonSmall)
actions.LayoutOrder = 4
actions.Visible = false
actions.Parent = inner
local gotIt = UiKit.button({
    Name = "GotIt", Text = "GOT IT", Tone = "Primary", AnchorPoint = Vector2.new(1, 0), Position = UDim2.fromScale(1, 0),
    Size = UDim2.fromOffset(120, UiTheme.Height.ButtonSmall), Parent = actions,
})

local function words(order, text, color)
    UiKit.boldLabel({
        Text = text, TextSize = 18, TextColor3 = color or C.Highlight, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, 26),
        LayoutOrder = order, Parent = line,
    })
end
local function clearLine()
    for _, child in line:GetChildren() do
        if child:IsA("GuiObject") then
            child:Destroy()
        end
    end
end

local touch = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
local step = 0
local function show(n)
    step = n
    stepLabel.Text = n .. " / 2"
    clearLine()
    if n == 1 then
        if touch then
            words(1, "Tap")
            local lotus = Instance.new("ImageLabel")
            lotus.Name = "Lotus"
            lotus.BackgroundTransparency = 1
            lotus.Image = UiTheme.Ornaments.LotusSit
            lotus.Size = UDim2.fromOffset(28, 28)
            lotus.LayoutOrder = 2
            lotus.Parent = line
            words(3, "to cultivate")
            body.Text = "Your character sits down and gathers Qi. Tap the lotus button (by the jump button) again to stand up."
        else
            words(1, "Press")
            local cap = UiKit.keycap(KEY)
            cap.Size = UDim2.fromOffset(28, 26)
            cap.TextSize = 15
            cap.Visible = true
            cap.LayoutOrder = 2
            cap.Parent = line
            words(3, "to cultivate")
            body.Text = "Your character sits down and gathers Qi. Press " .. KEY .. " again to stand up."
        end
        actions.Visible = false
    else
        words(1, "Qi is coming in!", C.Highlight)
        body.Text = "Qi makes you stronger and lets you rank up. Your quest, at the top right, shows what to do next."
        actions.Visible = true
        local tracker = Hud.Quest:FindFirstChild("QuestTracker")
        if tracker and tracker.Visible then
            UiFx.flash(tracker, C.Highlight)
        end
    end
    UiFx.flash(card, C.Highlight)
    task.defer(fitHeight)
end

local closed = false
local function close()
    if closed then
        return
    end
    closed = true
    finish()
    Sfx.play("Close")
    card:Destroy()
end
skip.Activated:Connect(close)
skipHit.Activated:Connect(close)
gotIt.Activated:Connect(close)

player:GetAttributeChangedSignal("IsCultivating"):Connect(function()
    if step == 1 and player:GetAttribute("IsCultivating") == true then
        Sfx.play("QuestComplete")
        show(2)
    end
end)
-- (the quest moving on, or the setting arriving true from elsewhere, also ends it)
player:GetAttributeChangedSignal("SettingTutorialDone"):Connect(function()
    if player:GetAttribute("SettingTutorialDone") == true and not closed then
        closed = true
        card:Destroy()
    end
end)

show(if player:GetAttribute("IsCultivating") == true then 2 else 1)
