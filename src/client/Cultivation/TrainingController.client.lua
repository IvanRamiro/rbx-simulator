local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))

local player = Players.LocalPlayer
local C = UiTheme.Colors

local keyName = GameConfig.CultivationKeybind.Name
local lastToggleRequestTime = 0

-- ---------- the cultivator's plaque (Status): Qi, rank, progress to the next ----------
local plaqueFrame = UiKit.panel({ Name = "QiPlaque", Size = UDim2.fromOffset(310, 108), LayoutOrder = 1, Parent = Hud.Status })
local plaque = UiKit.content(plaqueFrame, 16, 12)

local qiSeal = UiKit.seal(UiTheme.Seals.Qi, 38, "Jade")
qiSeal.Parent = plaque

local qiLabel = UiKit.label({
    Name = "QiLabel", Font = "Number", TextSize = 30, TextColor3 = C.JadeBright,
    Position = UDim2.fromOffset(48, -3), Size = UDim2.new(1, -48, 0, 32), Text = "...", Parent = plaque,
})
local powerTag = UiKit.label({
    Name = "Power", Font = "Strong", TextSize = 12, TextColor3 = C.Gold, AnchorPoint = Vector2.new(1, 0),
    Position = UDim2.new(1, 0, 0, 4), Size = UDim2.fromOffset(70, 16), TextXAlignment = Enum.TextXAlignment.Right,
    Text = "", Parent = plaque,
})
local rankLabel = UiKit.label({
    Name = "RankLabel", Font = "Title", TextSize = 15, TextColor3 = C.Gold,
    Position = UDim2.fromOffset(48, 28), Size = UDim2.new(1, -48, 0, 18), Text = "", TextTruncate = Enum.TextTruncate.AtEnd,
    Parent = plaque,
})
local realmLabel = UiKit.label({
    Name = "RealmLabel", TextSize = 12, TextColor3 = C.Mist,
    Position = UDim2.fromOffset(48, 46), Size = UDim2.new(1, -48, 0, 14), Text = "", TextTruncate = Enum.TextTruncate.AtEnd,
    Parent = plaque,
})
local progressBar = UiKit.bar({ Name = "Progress", Position = UDim2.new(0, 0, 1, -22), Size = UDim2.new(1, 0, 0, 6), Parent = plaque })
local nextRankLabel = UiKit.label({
    Name = "NextRankLabel", TextSize = 12, TextColor3 = C.Mist, AnchorPoint = Vector2.new(0, 1),
    Position = UDim2.new(0, 0, 1, 0), Size = UDim2.new(1, 0, 0, 14), Text = "", TextTruncate = Enum.TextTruncate.AtEnd,
    Parent = plaque,
})

-- ---------- the dock: the breakthrough (when it's ready), the station's bonus, Cultivate ----------
local rankUpButton = UiKit.button({
    Name = "RankUpButton", Tone = "Gold", Font = "Title", TextSize = 17, Text = "Break Through",
    Size = UDim2.fromOffset(240, 40), AutomaticSize = Enum.AutomaticSize.X, LayoutOrder = 20, Visible = false,
    Parent = Hud.Dock,
})
UiKit.padding(rankUpButton, 16, 0)
-- a breakthrough waiting to be taken breathes, so it is seen
local glow = rankUpButton:FindFirstChildOfClass("UIStroke")
task.spawn(function()
    while true do
        local t = os.clock()
        if rankUpButton.Visible then
            glow.Thickness = 1.5 + math.sin(t * 4) * 1
        end
        task.wait(1 / 30)
    end
end)

local stationLabel = UiKit.label({
    Name = "StationLabel", Font = "Strong", TextSize = 13, TextColor3 = C.JadeBright,
    BackgroundTransparency = 0.15, BackgroundColor3 = C.JadeDeep, AutomaticSize = Enum.AutomaticSize.X,
    Size = UDim2.fromOffset(0, 24), TextXAlignment = Enum.TextXAlignment.Center, LayoutOrder = 25, Visible = false,
    Text = GameConfig.TrainingStation.DisplayName .. "  +" .. GameConfig.TrainingStation.QiBonusPercent .. "% Qi",
    Parent = Hud.Dock,
})
UiKit.corner(stationLabel)
UiKit.padding(stationLabel, 10, 0)

local cultivateButton = UiKit.button({
    Name = "CultivateButton", Tone = "Jade", Font = "Title", TextSize = 19, Text = "Cultivate",
    Size = UDim2.fromOffset(240, 50), LayoutOrder = 30, Parent = Hud.Dock,
})
local cultivateKey = UiKit.keycap(keyName)
cultivateKey.AnchorPoint = Vector2.new(1, 0.5)
cultivateKey.Position = UDim2.new(1, -12, 0.5, 0)
cultivateKey.Parent = cultivateButton

local function isCultivating()
    return player:GetAttribute("IsCultivating") == true
end

local function updateCultivateButton()
    -- while cultivating it turns quiet and says how to stop: the aura itself is the feedback
    cultivateButton:SetAttribute("Tone", if isCultivating() then "Quiet" else "Jade")
    cultivateButton.Text = if isCultivating() then "Stop Cultivating" else "Cultivate"
end

local function requestToggleCultivation()
    local now = os.clock()
    if now - lastToggleRequestTime < GameConfig.CultivationToggleCooldown then
        return
    end
    lastToggleRequestTime = now

    RemoteEvents.CultivationEvent:FireServer(not isCultivating())
end

cultivateButton.Activated:Connect(requestToggleCultivation)

UserInputService.InputBegan:Connect(function(input, gameProcessedEvent)
    if gameProcessedEvent then
        return
    end

    if input.KeyCode == GameConfig.CultivationKeybind then
        requestToggleCultivation()
    end
end)

player:GetAttributeChangedSignal("IsCultivating"):Connect(updateCultivateButton)
updateCultivateButton()

local function updateStationLabel()
    stationLabel.Visible = player:GetAttribute("AtTrainingStation") == true
end

player:GetAttributeChangedSignal("AtTrainingStation"):Connect(updateStationLabel)
updateStationLabel()

local leaderstats = player:WaitForChild("leaderstats")
local qiValue = leaderstats:WaitForChild("Qi")
local rankValue = leaderstats:WaitForChild("Rank")

local function updateQiLabel()
    qiLabel.Text = NumberFormat.compact(qiValue.Value)
end

local function updateRankDisplay()
    local rank = Ranks.getRank(rankValue.Value)
    powerTag.Text = if rank and rank.QiMultiplier > 1 then "Qi ×" .. rank.QiMultiplier else ""
    rankLabel.Text = if rank then rank.Name else tostring(rankValue.Value)
    realmLabel.Text = if rank then rank.Realm .. "  ·  " .. rank.Level .. " / 5" else ""

    local nextRank = Ranks.getNextRank(rankValue.Value)
    if not nextRank then
        nextRankLabel.Text = "The highest rank: nothing above you"
        UiKit.setBar(progressBar, 1)
        rankUpButton.Visible = false
        return
    end

    -- the bar runs from this rank's Qi to the next one's
    local from = if rank then rank.QiRequired else 0
    local canRankUp = qiValue.Value >= nextRank.QiRequired
    UiKit.setBar(progressBar, (qiValue.Value - from) / math.max(1, nextRank.QiRequired - from))
    local target = if rank and nextRank.Realm ~= rank.Realm then nextRank.Realm else nextRank.Name
    nextRankLabel.Text = if canRankUp
        then target .. ": ready to break through"
        else target .. " at " .. NumberFormat.compact(nextRank.QiRequired) .. "  ·  " .. NumberFormat.compact(nextRank.QiRequired - qiValue.Value) .. " to go"
    nextRankLabel.TextColor3 = if canRankUp then C.Gold else C.Mist
    rankUpButton.Visible = canRankUp
    rankUpButton.Text = "Break Through: " .. target
end

local function requestRankUp()
    local nextRank = Ranks.getNextRank(rankValue.Value)
    if nextRank and qiValue.Value >= nextRank.QiRequired then
        RemoteEvents.RankUpEvent:FireServer()
    end
end

rankUpButton.Activated:Connect(requestRankUp)

qiValue.Changed:Connect(function()
    updateQiLabel()
    updateRankDisplay()
end)
rankValue.Changed:Connect(updateRankDisplay)

updateQiLabel()
updateRankDisplay()
