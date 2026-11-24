-- The CARRYING card (UI brief 2026-11-24, design/features/hud): while the player carries a stolen egg, a card at the top of the
-- right column (Hud.Quest, over the quest tracker) says what they hold, how far home is with a bar of how much of the way they
-- have come, and that the guardian is after them. Until now nothing on the HUD showed the most tense moment of the game.
-- Client only and cosmetic: it reads the player's "CarryingEgg" attribute and the guardian model's attributes (Egg, TargetId,
-- SafeZone, State) the server already sets; the server alone decides everything about the egg.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local REFRESH = 0.25 -- seconds between looks at the distance

local card = UiKit.panel({
    Name = "CarryCard", Size = UDim2.fromOffset(270, 0), AutomaticSize = Enum.AutomaticSize.Y, LayoutOrder = -20,
    Visible = false, Brackets = false, Parent = Hud.Quest,
})
card:FindFirstChildOfClass("UIStroke").Color = C.Danger
local inner = Instance.new("Frame")
inner.Name = "Inner"
inner.BackgroundTransparency = 1
inner.AutomaticSize = Enum.AutomaticSize.Y
inner.Size = UDim2.new(1, 0, 0, 0)
inner.Parent = card
UiKit.padding(inner, UiTheme.Pad.Card, UiTheme.Pad.Card)
UiKit.list(inner, { Padding = UDim.new(0, 6) })

-- the egg: its picture on a red tile, CARRYING over its name
local top = Instance.new("Frame")
top.Name = "Top"
top.BackgroundTransparency = 1
top.Size = UDim2.new(1, 0, 0, 46)
top.LayoutOrder = 1
top.Parent = inner
local picture = UiKit.icon(UiTheme.Icons.Hatch, 46, "Danger")
-- a light violet tile: the dark eggs (the Forbidden Origin's) vanish on the dark red
picture.BackgroundColor3 = Color3.fromRGB(86, 66, 178)
picture.BackgroundTransparency = 0
picture.Parent = top
local word = UiKit.boldLabel({
    Name = "Word", TextSize = 11, Text = "CARRYING", TextColor3 = C.Danger, Position = UDim2.fromOffset(56, 4), Size = UDim2.new(1, -56, 0, 14), Parent = top,
})
local _ = word
local eggName = UiKit.label({
    Name = "EggName", Font = "Title", TextSize = 16, TextColor3 = C.Text, Position = UDim2.fromOffset(56, 20), Size = UDim2.new(1, -56, 0, 22),
    TextTruncate = Enum.TextTruncate.AtEnd, Parent = top,
})

-- home and how far: "HOME · Yggdrasil" with the distance at the right, and a bar of the way come
local homeRow = Instance.new("Frame")
homeRow.Name = "Home"
homeRow.BackgroundTransparency = 1
homeRow.Size = UDim2.new(1, 0, 0, 16)
homeRow.LayoutOrder = 2
homeRow.Parent = inner
local homeName = UiKit.label({
    Name = "HomeName", Font = "Strong", TextSize = 12, TextColor3 = C.Muted, Size = UDim2.new(0.6, 0, 1, 0), Parent = homeRow,
})
local homeDistance = UiKit.label({
    Name = "Distance", Font = "Strong", TextSize = 12, TextColor3 = C.Sky, AnchorPoint = Vector2.new(1, 0), Position = UDim2.fromScale(1, 0),
    Size = UDim2.new(0.4, 0, 1, 0), TextXAlignment = Enum.TextXAlignment.Right, Parent = homeRow,
})
local track = Instance.new("Frame")
track.Name = "Track"
track.BackgroundColor3 = C.Well
track.BorderSizePixel = 0
track.Size = UDim2.new(1, 0, 0, 8)
track.LayoutOrder = 3
track.Parent = inner
UiKit.corner(track, 4)
local fill = Instance.new("Frame")
fill.Name = "Fill"
fill.BackgroundColor3 = C.Buy
fill.BorderSizePixel = 0
fill.Size = UDim2.fromScale(0, 1)
fill.Parent = track
UiKit.corner(fill, 4)

-- the chase: shown only while a guardian is after them
local chase = Instance.new("Frame")
chase.Name = "Chase"
chase.BackgroundColor3 = C.DangerDeep
chase.BackgroundTransparency = 0.1
chase.BorderSizePixel = 0
chase.Size = UDim2.new(1, 0, 0, 24)
chase.LayoutOrder = 4
chase.Visible = false
chase.Parent = inner
UiKit.corner(chase, 8)
local chaseText = UiKit.label({
    Name = "Text", Font = "Strong", TextSize = 12, TextColor3 = C.Text, Position = UDim2.fromOffset(10, 0), Size = UDim2.new(1, -20, 1, 0),
    TextTruncate = Enum.TextTruncate.AtEnd, Parent = chase,
})

-- the guardian whose egg this player carries, if it is still after them
local function chasingGuardian()
    for _, model in CollectionService:GetTagged(GameConfig.GuardianTag) do
        if model:GetAttribute("Egg") == "Carried" and model:GetAttribute("TargetId") == player.UserId then
            return model
        end
    end
    return nil
end

local function sentenceStart(text)
    return string.upper(string.sub(text, 1, 1)) .. string.sub(text, 2)
end

local startDistance = nil -- how far home was when this carry began (the bar's whole length)

local function refresh()
    local eggId = player:GetAttribute("CarryingEgg")
    if typeof(eggId) ~= "string" or eggId == "" then
        card.Visible = false
        startDistance = nil
        return
    end
    local config = GameConfig.Eggs[eggId]
    eggName.Text = if config then config.DisplayName else "an egg"
    picture:FindFirstChild("Image").Image = UiTheme.EggIcons[eggId] or UiTheme.Icons.Hatch
    local model = chasingGuardian()
    local safe = if model then model:GetAttribute("SafeZone") else nil
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    local haveHome = model ~= nil and typeof(safe) == "Vector3" and root ~= nil
    homeRow.Visible = haveHome
    track.Visible = haveHome
    chase.Visible = false
    if haveHome then
        local guardian = GameConfig.Guardians[model:GetAttribute("GuardianId")] or {}
        local zone = guardian.SafeZone and guardian.SafeZone.Name or "home"
        local distance = (Vector3.new(root.Position.X, 0, root.Position.Z) - Vector3.new(safe.X, 0, safe.Z)).Magnitude
        startDistance = math.max(startDistance or 0, distance)
        homeName.Text = "HOME · " .. zone
        homeDistance.Text = math.floor(distance + 0.5) .. " studs"
        fill.Size = UDim2.fromScale(math.clamp(1 - distance / math.max(startDistance, 1), 0, 1), 1)
        if model:GetAttribute("State") == "Enraged" then
            local called = guardian.Called or ("The " .. (guardian.DisplayName or "guardian"))
            chaseText.Text = sentenceStart(called) .. " is chasing you"
            chase.Visible = true
        end
    end
    card.Visible = true
end

player:GetAttributeChangedSignal("CarryingEgg"):Connect(refresh)
task.spawn(function()
    while true do
        if player:GetAttribute("CarryingEgg") ~= nil then
            refresh()
        end
        task.wait(REFRESH)
    end
end)
refresh()
