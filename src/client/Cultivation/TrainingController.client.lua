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

-- ---------- the STATUS window (the Status region): Qi, name, rank, realm, progress ----------
local statusFrame = UiKit.panel({ Name = "StatusWindow", Size = UDim2.fromOffset(310, 178), LayoutOrder = 1, Parent = Hud.Status })
local status = UiKit.content(statusFrame, 14, 10)
UiKit.header(status, "STATUS", { TextSize = 13 })

local qiIcon = UiKit.icon(UiTheme.Icons.Qi, 34, "Accent")
qiIcon.Position = UDim2.fromOffset(0, 30)
qiIcon.Parent = status
UiKit.label({
    Name = "QiCaption", Font = "Strong", TextSize = 10, TextColor3 = C.Muted, Text = "QI",
    Position = UDim2.fromOffset(44, 28), Size = UDim2.fromOffset(40, 12), Parent = status,
})
local qiLabel = UiKit.label({
    Name = "QiLabel", Font = "Number", TextSize = 26, TextColor3 = C.AccentBright,
    Position = UDim2.fromOffset(44, 38), Size = UDim2.new(1, -120, 0, 28), Text = "...", Parent = status,
})
local powerTag = UiKit.label({
    Name = "Power", Font = "Strong", TextSize = 12, TextColor3 = C.Highlight, AnchorPoint = Vector2.new(1, 0),
    Position = UDim2.new(1, 0, 0, 44), Size = UDim2.fromOffset(80, 16), TextXAlignment = Enum.TextXAlignment.Right,
    Text = "", Parent = status,
})

-- the System's fields: a muted key, its value
local function field(key, y, color)
    UiKit.label({
        Name = key .. "Key", Font = "Strong", TextSize = 11, TextColor3 = C.Muted, Text = key,
        Position = UDim2.fromOffset(0, y), Size = UDim2.fromOffset(58, 16), Parent = status,
    })
    return UiKit.label({
        Name = key .. "Value", Font = "Strong", TextSize = 13, TextColor3 = color or C.Text, Text = "",
        Position = UDim2.fromOffset(60, y), Size = UDim2.new(1, -60, 0, 16), TextTruncate = Enum.TextTruncate.AtEnd,
        Parent = status,
    })
end
field("NAME", 74).Text = player.DisplayName
local rankLabel = field("RANK", 92, C.Highlight)
local realmLabel = field("REALM", 110)

-- On a short screen (a phone in landscape) the window slims down to Qi, rank and progress: NAME
-- and REALM go, and RANK moves up into NAME's place.
local FULL_HEIGHT, COMPACT_HEIGHT = 178, 140
local function fitStatus(compact)
    statusFrame.Size = UDim2.fromOffset(310, if compact then COMPACT_HEIGHT else FULL_HEIGHT)
    for _, key in { "NAME", "REALM" } do
        status[key .. "Key"].Visible = not compact
        status[key .. "Value"].Visible = not compact
    end
    status.RANKKey.Position = UDim2.fromOffset(0, if compact then 74 else 92)
    status.RANKValue.Position = UDim2.fromOffset(60, if compact then 74 else 92)
end
Hud.CompactChanged:Connect(fitStatus)
fitStatus(Hud.isCompact())

local progressBar = UiKit.bar({ Name = "Progress", Position = UDim2.new(0, 0, 1, -22), Size = UDim2.new(1, 0, 0, 6), Parent = status })
local nextRankLabel = UiKit.label({
    Name = "NextRankLabel", TextSize = 11, TextColor3 = C.Muted, AnchorPoint = Vector2.new(0, 1),
    Position = UDim2.new(0, 0, 1, 0), Size = UDim2.new(1, 0, 0, 14), Text = "", TextTruncate = Enum.TextTruncate.AtEnd,
    Parent = status,
})

-- ---------- the dock: the breakthrough (when it's ready), the station's bonus, Cultivate ----------
local rankUpButton = UiKit.button({
    Name = "RankUpButton", Tone = "Highlight", Font = "Title", TextSize = 17, Text = "BREAK THROUGH",
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
    Name = "StationLabel", Font = "Strong", TextSize = 13, TextColor3 = C.AccentBright,
    BackgroundTransparency = 0.15, BackgroundColor3 = C.AccentDeep, AutomaticSize = Enum.AutomaticSize.X,
    Size = UDim2.fromOffset(0, 24), TextXAlignment = Enum.TextXAlignment.Center, LayoutOrder = 25, Visible = false,
    Text = GameConfig.TrainingStation.DisplayName .. "  +" .. GameConfig.TrainingStation.QiBonusPercent .. "% Qi",
    Parent = Hud.Dock,
})
UiKit.corner(stationLabel)
UiKit.padding(stationLabel, 10, 0)

local cultivateButton = UiKit.button({
    Name = "CultivateButton", Tone = "Accent", Font = "Title", TextSize = 18, Text = "CULTIVATE",
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
    cultivateButton:SetAttribute("Tone", if isCultivating() then "Quiet" else "Accent")
    cultivateButton.Text = if isCultivating() then "STOP CULTIVATING" else "CULTIVATE"
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

    if input.KeyCode == GameConfig.CultivationKeybind or input.KeyCode == Enum.KeyCode.ButtonL1 then
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
    nextRankLabel.TextColor3 = if canRankUp then C.Highlight else C.Muted
    rankUpButton.Visible = canRankUp
    rankUpButton.Text = "BREAK THROUGH: " .. string.upper(target)
end

local function requestRankUp()
    local nextRank = Ranks.getNextRank(rankValue.Value)
    if nextRank and qiValue.Value >= nextRank.QiRequired then
        RemoteEvents.RankUpEvent:FireServer()
    end
end

rankUpButton.Activated:Connect(requestRankUp)
UserInputService.InputBegan:Connect(function(input, gameProcessedEvent)
    if not gameProcessedEvent and input.KeyCode == Enum.KeyCode.ButtonR1 then
        requestRankUp()
    end
end)

qiValue.Changed:Connect(function()
    updateQiLabel()
    updateRankDisplay()
end)
rankValue.Changed:Connect(updateRankDisplay)

updateQiLabel()
updateRankDisplay()
