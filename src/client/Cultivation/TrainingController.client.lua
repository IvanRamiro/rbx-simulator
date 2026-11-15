-- The Status region of the HUD (portrait, name, rank, realm, progress), the Qi counter with its income while cultivating,
-- and the cultivate toggle (GameConfig.CultivationKeybind, a gamepad's L1, or the button), with the Qi Spring's bonus line.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local UiFx = require(UI:WaitForChild("UiFx"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors

local keyName = GameConfig.CultivationKeybind.Name
local lastToggleRequestTime = 0

-- ---------- the profile (top of the Status region): portrait, name, rank, realm, progress ----------
-- The portrait sits PAD in from the frame's left as from its top and foot (it was 10 in, 12 down); the details' rows stack with
-- one gap between them, centred down the frame, and end PAD from its right (the bar's gap above it was three times the others).
local HEIGHT, PORTRAIT, PAD = 88, 64, UiTheme.Pad.Card
local DETAILS_LEFT = PAD + PORTRAIT + UiTheme.Space.S
local ROW_GAP = 3
local FULL_SIZE, MINIMIZED_SIZE = UDim2.fromOffset(270, HEIGHT), UDim2.fromOffset(PAD + PORTRAIT + PAD, HEIGHT)
local statusFrame = UiKit.panel({ Name = "StatusWindow", Size = FULL_SIZE, LayoutOrder = 1, Parent = Hud.Status })
UiFx.edgeLight(statusFrame, 11)

-- the portrait: tapping it folds the rest away (the owner's minimize, saved in their settings)
local portrait = Instance.new("ImageButton")
portrait.Name = "Portrait"
portrait.AnchorPoint = Vector2.new(0, 0.5)
portrait.Position = UDim2.new(0, PAD, 0.5, 0)
portrait.Size = UDim2.fromOffset(PORTRAIT, PORTRAIT)
portrait.BackgroundColor3 = C.Well
portrait.AutoButtonColor = false
portrait.ZIndex = 2
portrait.Parent = statusFrame
UiKit.corner(portrait, PORTRAIT // 2)
UiKit.stroke(portrait, C.Highlight, 0, 3)
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
details.Position = UDim2.fromOffset(DETAILS_LEFT, 0)
details.Size = UDim2.new(1, -(DETAILS_LEFT + PAD), 1, 0)
details.Parent = statusFrame
UiKit.list(details, { Padding = UDim.new(0, ROW_GAP), VerticalAlignment = Enum.VerticalAlignment.Center })
local nameRow = Instance.new("Frame") -- the name, and the Qi multiplier at the row's right end
nameRow.Name = "NameRow"
nameRow.BackgroundTransparency = 1
nameRow.Size = UDim2.new(1, 0, 0, 16)
nameRow.LayoutOrder = 1
nameRow.Parent = details
UiKit.boldLabel({
    Name = "NameLabel", TextSize = 13, Text = player.DisplayName, TextTruncate = Enum.TextTruncate.AtEnd,
    Size = UDim2.new(1, -66, 1, 0), Parent = nameRow,
})
local powerTag = UiKit.boldLabel({
    Name = "Power", TextSize = 12, TextColor3 = C.Highlight, AnchorPoint = Vector2.new(1, 0),
    Position = UDim2.fromScale(1, 0), Size = UDim2.new(0, 64, 1, 0), TextXAlignment = Enum.TextXAlignment.Right, Text = "", Parent = nameRow,
})
local rankLabel = UiKit.label({
    Name = "RankLabel", Font = "Title", TextSize = 15, TextColor3 = C.Highlight, LayoutOrder = 2,
    Size = UDim2.new(1, 0, 0, 18), TextTruncate = Enum.TextTruncate.AtEnd, Parent = details,
})
local realmLabel = UiKit.label({
    Name = "RealmLabel", Font = "Strong", TextSize = 11, TextColor3 = C.Muted, LayoutOrder = 3,
    Size = UDim2.new(1, 0, 0, 14), TextTruncate = Enum.TextTruncate.AtEnd, Parent = details,
})
local progressBar = UiKit.bar({ Name = "Progress", LayoutOrder = 4, Size = UDim2.new(1, 0, 0, 18), Parent = details })
local nextRankLabel = UiKit.label({
    Name = "NextRankLabel", Font = "Heavy", TextSize = 11, Size = UDim2.fromScale(1, 1), Text = "", ZIndex = 3,
    TextXAlignment = Enum.TextXAlignment.Center, TextTruncate = Enum.TextTruncate.AtEnd, Parent = progressBar,
})
UiKit.outline(nextRankLabel, 1.5)
progressBar:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, 9)
progressBar.Fill:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(0, 9)

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
local qiChip, setQi = Hud.chip("QiCounter", UiTheme.Icons.Qi, 0, { Format = NumberFormat.compact, Color = C.Sky })
-- beside it while cultivating, how fast Qi is coming in (measured here, over the last few seconds of cultivating: the top games
-- show income per second beside the money, the owner's reference 2026-11-13)
local qiRate = UiKit.label({
    Name = "Rate", Font = "Heavy", TextSize = 14, TextColor3 = C.Highlight, Text = "", AutomaticSize = Enum.AutomaticSize.X,
    Size = UDim2.fromOffset(0, 20), LayoutOrder = 3, Visible = false, Parent = qiChip:FindFirstChild("Row"),
})
UiKit.outline(qiRate, 1.5)
local RATE_WINDOW = 3 -- seconds of gains averaged

-- ---------- the dock: the breakthrough (when it's ready), the station's bonus, Cultivate ----------
-- a pill over the dock (Hud.CultivationDock.addPill): on the Cultivate button's centre line and at its height, as wide as
-- Cultivate, wider only when its words need it (then it grows evenly about the same centre)
local rankUpButton = UiKit.button({
    Name = "RankUpButton", Tone = "Highlight", Font = "Heavy", TextSize = 17, Text = "BREAK THROUGH", Visible = false,
})
local RANK_UP_MARGIN = 24 -- each side of its words
Hud.CultivationDock.addPill(rankUpButton, 20, {
    MatchAction = true,
    Width = function()
        return UiKit.wordsWidth(rankUpButton) + RANK_UP_MARGIN * 2
    end,
})
-- a breakthrough waiting to be taken breathes, so it is seen
UiFx.attention(rankUpButton)

local STATION_HEIGHT, STATION_MARGIN = 28, 14
local stationLabel = UiKit.label({
    Name = "StationLabel", Font = "Heavy", TextSize = 13, TextColor3 = C.AccentBright,
    BackgroundTransparency = 0.15, BackgroundColor3 = C.AccentDeep, TextXAlignment = Enum.TextXAlignment.Center, Visible = false,
    Text = GameConfig.TrainingStation.DisplayName .. "  +" .. GameConfig.TrainingStation.QiBonusPercent .. "% Qi",
})
UiKit.corner(stationLabel, STATION_HEIGHT // 2)
UiKit.stroke(stationLabel, C.Edge, 0.3, 1.5)
Hud.CultivationDock.addPill(stationLabel, 25, {
    Height = STATION_HEIGHT, OwnRow = true,
    Width = function()
        return UiKit.wordsWidth(stationLabel) + STATION_MARGIN * 2
    end,
})

local cultivateButton = UiKit.button({
    Name = "CultivateButton", Tone = "Primary", Font = "Heavy", Text = "CULTIVATE", -- (the dock's buttons share one face)
    Size = UDim2.fromScale(1, 1), Parent = Hud.CultivationDock.Action,
})
-- a pill, and light that keeps to its curves; the dock's size can change once the screen's is known
local function shapeCultivateButton(size)
    UiKit.pillShape(cultivateButton, size.Button)
end
Hud.CultivationDock.Resized:Connect(shapeCultivateButton)
shapeCultivateButton(Hud.CultivationDock.Size)
UiKit.keycapOn(cultivateButton, keyName)

local function isCultivating()
    return player:GetAttribute("IsCultivating") == true
end

-- the game's one main action catches the eye now and then, while it isn't being done
task.spawn(function()
    while cultivateButton.Parent do
        task.wait(5)
        if not isCultivating() and cultivateButton.Visible then
            UiFx.sweep(cultivateButton, Color3.new(1, 1, 1), 0.7)
        end
    end
end)

-- While cultivating there is no mistaking it: the button turns from gold to living jade and a band of light keeps crossing it, the
-- emblem's ring turns, its well glows the same colour and the figure brightens. Pressing it again stops, and it says so.
local ACTIVE_GLOW = Color3.fromRGB(120, 255, 236)
local dock = Hud.CultivationDock
local well = Hud.CultivationEmblemWell
local WELL_AT_REST, FIGURE_AT_REST = well.BackgroundColor3, dock.Emblem.ImageColor3
local RING_TURN = 40 -- degrees a second
local turning = nil
local sweeping = 0 -- the active look's sweep loop: a new one stops any still waiting from before

-- its words, centred on the button, leave the key's hint its room at each end (they ran into the E on a phone, cultivating)
local CULTIVATE_MARGIN = UiTheme.Space.M
local function shapeCultivateText()
    local size = dock.Size
    local _, width = dock.actionSpan(size)
    local room = width - 2 * math.max(UiKit.keyRoom(cultivateButton), CULTIVATE_MARGIN)
    UiKit.fitWords(cultivateButton, if isCultivating() then size.TextSize + 3 else size.TextSize + 7, room)
end

local function updateCultivateButton()
    local active = isCultivating()
    cultivateButton:SetAttribute("Tone", if active then "Active" else "Primary")
    cultivateButton.Text = if active then "CULTIVATING - STOP" else "CULTIVATE"
    shapeCultivateText()
    well.BackgroundColor3 = if active then ACTIVE_GLOW else WELL_AT_REST
    dock.Emblem.ImageColor3 = if active then Color3.new(1, 1, 1) else FIGURE_AT_REST
    if active and not turning then
        turning = RunService.RenderStepped:Connect(function(dt)
            dock.Ring.Rotation = (dock.Ring.Rotation + RING_TURN * dt) % 360
        end)
        sweeping += 1
        local mine = sweeping
        task.spawn(function()
            while mine == sweeping and isCultivating() and cultivateButton.Parent do
                UiFx.sweep(cultivateButton, Color3.new(1, 1, 1), 0.9)
                task.wait(1.4)
            end
        end)
    elseif not active and turning then
        turning:Disconnect()
        turning = nil
        dock.Ring.Rotation = 0
    end
end
dock.Resized:Connect(shapeCultivateText)

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

local rateSamples = {} -- { time, gain } of each rise in Qi while cultivating, newest last
local lastQi = qiValue.Value

local function showRate()
    local now = os.clock()
    while rateSamples[1] and now - rateSamples[1][1] > RATE_WINDOW do
        table.remove(rateSamples, 1)
    end
    -- the gains after the first, over the time from the first to now: right from the second tick, and falling once they stop
    local count = #rateSamples
    local gained = 0
    for i = 2, count do
        gained += rateSamples[i][2]
    end
    local span = if count >= 2 then now - rateSamples[1][1] else 0
    local cultivating = player:GetAttribute("IsCultivating") == true
    qiRate.Visible = cultivating and span > 0 and gained > 0
    if qiRate.Visible then
        qiRate.Text = "+" .. NumberFormat.compact(math.floor(gained / span + 0.5)) .. "/s"
    end
end

local function updateQiLabel()
    local gain = qiValue.Value - lastQi
    lastQi = qiValue.Value
    if gain > 0 and player:GetAttribute("IsCultivating") == true then
        table.insert(rateSamples, { os.clock(), gain })
        Sfx.play("QiTick") -- (a twinkle now and then, not every tick: its Gap)
    end
    setQi(qiValue.Value)
    showRate()
end
player:GetAttributeChangedSignal("IsCultivating"):Connect(function()
    rateSamples = {}
    showRate()
end)
task.spawn(function() -- the rate falls away when the gains stop
    while true do
        task.wait(1)
        if qiRate.Visible or #rateSamples > 0 then
            showRate()
        end
    end
end)

local wasReady = nil -- (nil until the first update: joining with a breakthrough ready says nothing)
local rankChangedAt = -math.huge
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
    nextRankLabel.TextColor3 = C.Text -- white either way: gold words would vanish on the gold bar
    UiKit.setBarColor(progressBar, if canRankUp then C.Highlight else C.Accent)
    -- into a new realm, the Heavenly Tribulation stands in the way (server/Cultivation/Tribulation): hidden while it lasts,
    -- and after a fall, the time until they may face it again
    local newRealm = rank ~= nil and nextRank.Realm ~= rank.Realm
    local recovering = math.ceil((player:GetAttribute("TribulationRetryAt") or 0) - workspace:GetServerTimeNow())
    rankUpButton.Visible = canRankUp and player:GetAttribute("InTribulation") ~= true
    if rankUpButton.Visible and wasReady == false and os.clock() - rankChangedAt > 4 then
        Sfx.play("BreakthroughReady") -- the moment it can be done (not on joining, nor straight after a breakthrough's own sound)
    end
    wasReady = rankUpButton.Visible
    if newRealm and recovering > 0 then
        rankUpButton.Text = "RECOVERING FROM THE TRIBULATION: " .. recovering .. " s"
        rankUpButton:SetAttribute("Tone", "Quiet")
    else
        rankUpButton.Text = if newRealm then "FACE THE TRIBULATION: " .. string.upper(target) else "BREAK THROUGH: " .. string.upper(target)
        rankUpButton:SetAttribute("Tone", "Highlight")
    end
end

local function requestRankUp()
    local nextRank = Ranks.getNextRank(rankValue.Value)
    local recovering = (player:GetAttribute("TribulationRetryAt") or 0) > workspace:GetServerTimeNow()
    if nextRank and qiValue.Value >= nextRank.QiRequired and player:GetAttribute("InTribulation") ~= true and not recovering then
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
rankValue.Changed:Connect(function()
    rankChangedAt = os.clock()
    updateRankDisplay()
end)
player:GetAttributeChangedSignal("InTribulation"):Connect(updateRankDisplay)
-- the countdown after a fall, each second until it's over
task.spawn(function()
    while true do
        task.wait(1)
        if (player:GetAttribute("TribulationRetryAt") or 0) > workspace:GetServerTimeNow() - 1 then
            updateRankDisplay()
        end
    end
end)

updateQiLabel()
updateRankDisplay()
