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

-- ---------- the profile (top of the Status region): portrait, name, rank, realm, progress ----------
local FULL_SIZE, MINIMIZED_SIZE = UDim2.fromOffset(270, 88), UDim2.fromOffset(84, 88)
local statusFrame = UiKit.panel({ Name = "StatusWindow", Size = FULL_SIZE, LayoutOrder = 1, Parent = Hud.Status })

-- the portrait: tapping it folds the rest away (the owner's minimize, saved in their settings)
local portrait = Instance.new("ImageButton")
portrait.Name = "Portrait"
portrait.AnchorPoint = Vector2.new(0, 0.5)
portrait.Position = UDim2.new(0, 10, 0.5, 0)
portrait.Size = UDim2.fromOffset(64, 64)
portrait.BackgroundColor3 = C.Well
portrait.AutoButtonColor = false
portrait.ZIndex = 2
portrait.Parent = statusFrame
UiKit.corner(portrait, 32)
UiKit.stroke(portrait, C.Edge, 0, 2)
task.spawn(function()
    local ok, image = pcall(function()
        return Players:GetUserThumbnailAsync(player.UserId, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size150x150)
    end)
    if ok then
        portrait.Image = image
    end
end)

local details = Instance.new("Frame")
details.Name = "Details"
details.BackgroundTransparency = 1
details.Position = UDim2.fromOffset(84, 6)
details.Size = UDim2.new(1, -94, 1, -12)
details.Parent = statusFrame
UiKit.label({
    Name = "NameLabel", Font = "Strong", TextSize = 13, Text = player.DisplayName, TextTruncate = Enum.TextTruncate.AtEnd,
    Size = UDim2.new(1, -66, 0, 16), Parent = details,
})
local powerTag = UiKit.label({
    Name = "Power", Font = "Strong", TextSize = 12, TextColor3 = C.Highlight, AnchorPoint = Vector2.new(1, 0),
    Position = UDim2.new(1, 0, 0, 0), Size = UDim2.fromOffset(64, 16), TextXAlignment = Enum.TextXAlignment.Right, Text = "", Parent = details,
})
local rankLabel = UiKit.label({
    Name = "RankLabel", Font = "Title", TextSize = 15, TextColor3 = C.Highlight, Position = UDim2.fromOffset(0, 16),
    Size = UDim2.new(1, 0, 0, 18), TextTruncate = Enum.TextTruncate.AtEnd, Parent = details,
})
local realmLabel = UiKit.label({
    Name = "RealmLabel", Font = "Strong", TextSize = 11, TextColor3 = C.Muted, Position = UDim2.fromOffset(0, 34),
    Size = UDim2.new(1, 0, 0, 14), TextTruncate = Enum.TextTruncate.AtEnd, Parent = details,
})
local progressBar = UiKit.bar({ Name = "Progress", Position = UDim2.new(0, 0, 1, -18), Size = UDim2.new(1, 0, 0, 18), Parent = details })
local nextRankLabel = UiKit.label({
    Name = "NextRankLabel", Font = "Strong", TextSize = 11, Size = UDim2.fromScale(1, 1), Text = "", ZIndex = 3,
    TextXAlignment = Enum.TextXAlignment.Center, TextTruncate = Enum.TextTruncate.AtEnd, TextStrokeTransparency = 0.5, Parent = progressBar,
})

local function fitStatus()
    local minimized = player:GetAttribute("SettingStatusMinimized") == true
    statusFrame.Size = if minimized then MINIMIZED_SIZE else FULL_SIZE
    details.Visible = not minimized
end
portrait.Activated:Connect(function()
    -- the attribute changes at once, so it answers without waiting for the server's copy
    local minimized = player:GetAttribute("SettingStatusMinimized") ~= true
    player:SetAttribute("SettingStatusMinimized", minimized)
    RemoteEvents.SettingsEvent:FireServer("StatusMinimized", minimized)
end)
player:GetAttributeChangedSignal("SettingStatusMinimized"):Connect(fitStatus)
fitStatus()

-- the Qi, first of the currencies
local _, qiLabel = Hud.chip("QiCounter", UiTheme.Icons.Qi, 0)

-- ---------- the dock: the breakthrough (when it's ready), the station's bonus, Cultivate ----------
local rankUpButton = UiKit.button({
    Name = "RankUpButton", Tone = "Highlight", Font = "Title", TextSize = 17, Text = "BREAK THROUGH",
    Size = UDim2.fromOffset(Hud.DockWidth(), 40), AutomaticSize = Enum.AutomaticSize.X, LayoutOrder = 20, Visible = false,
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
    Size = UDim2.fromOffset(Hud.DockWidth(), if Hud.isCompact() then 38 else 50), LayoutOrder = 30, Parent = Hud.Dock,
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
        nextRankLabel.Text = "The highest rank"
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
        then "Ready to break through"
        else NumberFormat.compact(nextRank.QiRequired - qiValue.Value) .. " Qi to " .. target
    nextRankLabel.TextColor3 = if canRankUp then C.Highlight else C.Text
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
