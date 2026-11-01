local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local applyHudScale = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudScale"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local HUD_NAME = "QiHud"
local READY_COLOR = Color3.fromRGB(70, 160, 110)
local CULTIVATING_COLOR = Color3.fromRGB(120, 90, 190)
local COOLDOWN_COLOR = Color3.fromRGB(90, 90, 90)
local RANK_UP_READY_COLOR = Color3.fromRGB(200, 155, 50)

local keyName = GameConfig.CultivationKeybind.Name
local lastToggleRequestTime = 0

local oldHud = playerGui:FindFirstChild(HUD_NAME)
if oldHud then
    oldHud:Destroy()
end

local hud = Instance.new("ScreenGui")
hud.Name = HUD_NAME
hud.ResetOnSpawn = false

local panel = Instance.new("Frame")
panel.Name = "Panel"
panel.AnchorPoint = Vector2.new(0.5, 1)
panel.Position = UDim2.new(0.5, 0, 1, -24)
panel.Size = UDim2.fromOffset(260, 200)
panel.BackgroundColor3 = Color3.fromRGB(20, 20, 30)
panel.BackgroundTransparency = 0.25
panel.Parent = hud
applyHudScale(panel)

local panelCorner = Instance.new("UICorner")
panelCorner.CornerRadius = UDim.new(0, 12)
panelCorner.Parent = panel

local qiLabel = Instance.new("TextLabel")
qiLabel.Name = "QiLabel"
qiLabel.Position = UDim2.fromOffset(10, 8)
qiLabel.Size = UDim2.new(1, -20, 0, 36)
qiLabel.BackgroundTransparency = 1
qiLabel.Font = Enum.Font.GothamBold
qiLabel.TextScaled = true
qiLabel.TextColor3 = Color3.fromRGB(150, 230, 255)
qiLabel.Text = "Qi: ..."
qiLabel.Parent = panel

local rankLabel = Instance.new("TextLabel")
rankLabel.Name = "RankLabel"
rankLabel.Position = UDim2.fromOffset(10, 46)
rankLabel.Size = UDim2.new(1, -20, 0, 24)
rankLabel.BackgroundTransparency = 1
rankLabel.Font = Enum.Font.GothamBold
rankLabel.TextScaled = true
rankLabel.TextColor3 = Color3.fromRGB(255, 215, 120)
rankLabel.Text = "Rank: ..."
rankLabel.Parent = panel

local nextRankLabel = Instance.new("TextLabel")
nextRankLabel.Name = "NextRankLabel"
nextRankLabel.Position = UDim2.fromOffset(10, 72)
nextRankLabel.Size = UDim2.new(1, -20, 0, 18)
nextRankLabel.BackgroundTransparency = 1
nextRankLabel.Font = Enum.Font.Gotham
nextRankLabel.TextScaled = true
nextRankLabel.TextColor3 = Color3.fromRGB(200, 200, 210)
nextRankLabel.Text = ""
nextRankLabel.Parent = panel

local cultivateButton = Instance.new("TextButton")
cultivateButton.Name = "CultivateButton"
cultivateButton.Position = UDim2.fromOffset(10, 98)
cultivateButton.Size = UDim2.new(1, -20, 0, 48)
cultivateButton.BackgroundColor3 = READY_COLOR
cultivateButton.AutoButtonColor = true
cultivateButton.Font = Enum.Font.GothamBold
cultivateButton.TextScaled = true
cultivateButton.TextColor3 = Color3.new(1, 1, 1)
cultivateButton.Text = "Cultivate [" .. keyName .. "]"
cultivateButton.Parent = panel

local cultivateCorner = Instance.new("UICorner")
cultivateCorner.CornerRadius = UDim.new(0, 10)
cultivateCorner.Parent = cultivateButton

local rankUpButton = Instance.new("TextButton")
rankUpButton.Name = "RankUpButton"
rankUpButton.Position = UDim2.fromOffset(10, 154)
rankUpButton.Size = UDim2.new(1, -20, 0, 36)
rankUpButton.BackgroundColor3 = COOLDOWN_COLOR
rankUpButton.AutoButtonColor = false
rankUpButton.Font = Enum.Font.GothamBold
rankUpButton.TextScaled = true
rankUpButton.TextColor3 = Color3.new(1, 1, 1)
rankUpButton.Text = "Rank Up"
rankUpButton.Parent = panel

local rankUpCorner = Instance.new("UICorner")
rankUpCorner.CornerRadius = UDim.new(0, 10)
rankUpCorner.Parent = rankUpButton

local stationLabel = Instance.new("TextLabel")
stationLabel.Name = "StationLabel"
stationLabel.AnchorPoint = Vector2.new(0.5, 1)
stationLabel.Position = UDim2.new(0.5, 0, 0, -6)
stationLabel.Size = UDim2.new(1, 0, 0, 26)
stationLabel.BackgroundColor3 = Color3.fromRGB(20, 20, 30)
stationLabel.BackgroundTransparency = 0.25
stationLabel.Font = Enum.Font.GothamBold
stationLabel.TextScaled = true
stationLabel.TextColor3 = Color3.fromRGB(150, 240, 255)
stationLabel.Text = GameConfig.TrainingStation.DisplayName .. ": +" .. GameConfig.TrainingStation.QiBonusPercent .. "% Qi"
stationLabel.Visible = false
stationLabel.Parent = panel

local stationCorner = Instance.new("UICorner")
stationCorner.CornerRadius = UDim.new(0, 8)
stationCorner.Parent = stationLabel

hud.Parent = playerGui

local function isCultivating()
    return player:GetAttribute("IsCultivating") == true
end

local function updateCultivateButton()
    if isCultivating() then
        cultivateButton.BackgroundColor3 = CULTIVATING_COLOR
        cultivateButton.Text = "Cultivating... Stop [" .. keyName .. "]"
    else
        cultivateButton.BackgroundColor3 = READY_COLOR
        cultivateButton.Text = "Cultivate [" .. keyName .. "]"
    end
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
    qiLabel.Text = "Qi: " .. NumberFormat.compact(qiValue.Value)
end

local function updateRankDisplay()
    local rank = Ranks.getRank(rankValue.Value)
    local power = if rank and rank.QiMultiplier > 1 then "  |  Qi x" .. rank.QiMultiplier else ""
    rankLabel.Text = if rank
        then rank.Name .. "  |  " .. rank.Realm .. " " .. rank.Level .. "/5" .. power
        else "Rank: " .. rankValue.Value

    local nextRank = Ranks.getNextRank(rankValue.Value)
    if not nextRank then
        nextRankLabel.Text = "Highest rank reached"
        rankUpButton.Visible = false
        return
    end

    if rank and nextRank.Realm ~= rank.Realm then
        nextRankLabel.Text = "Next realm: " .. nextRank.Realm .. " at " .. NumberFormat.compact(nextRank.QiRequired) .. " Qi"
    else
        nextRankLabel.Text = "Next: " .. nextRank.Name .. " at " .. NumberFormat.compact(nextRank.QiRequired) .. " Qi"
    end
    rankUpButton.Visible = true

    local canRankUp = qiValue.Value >= nextRank.QiRequired
    local qiNeeded = nextRank.QiRequired - qiValue.Value

    rankUpButton.BackgroundColor3 = if canRankUp then RANK_UP_READY_COLOR else COOLDOWN_COLOR
    rankUpButton.AutoButtonColor = canRankUp
    rankUpButton.Text = if canRankUp then "Rank Up!" else "Rank Up (" .. NumberFormat.compact(qiNeeded) .. " more Qi)"
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
