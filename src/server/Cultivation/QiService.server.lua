local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local WorldConfig = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("WorldConfig"))
local PetInventory = require(script.Parent.Parent:WaitForChild("Pets"):WaitForChild("PetInventory"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))

local STATION_HEIGHT_TOLERANCE = 12

local cultivatingPlayers = {}

local lastToggleTime = {}

local function getQiValue(player)
    return (PlayerData.getStats(player))
end

local function hasAliveCharacter(player)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    return humanoid ~= nil and humanoid.Health > 0
end

local stationCenter = nil

-- where each player began cultivating: walking or teleporting off ends it, on the server's own word
local cultivatingFrom = {}
local STILL_RADIUS = 8

local function setCultivating(player, isCultivating)
    cultivatingPlayers[player] = if isCultivating then true else nil
    local rootPart = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    cultivatingFrom[player] = if isCultivating and rootPart then rootPart.Position else nil
    player:SetAttribute("IsCultivating", isCultivating)
    if not isCultivating then
        player:SetAttribute("AtTrainingStation", false)
    end
end

local function isAtTrainingStation(player)
    local character = player.Character
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    if not (stationCenter and rootPart) then
        return false
    end

    local offset = rootPart.Position - stationCenter
    local horizontalDistance = Vector3.new(offset.X, 0, offset.Z).Magnitude
    return horizontalDistance <= GameConfig.TrainingStation.Radius and math.abs(offset.Y) <= STATION_HEIGHT_TOLERANCE
end

local function onCharacterAdded(player, character)
    setCultivating(player, false)

    local humanoid = character:WaitForChild("Humanoid")
    humanoid.Died:Connect(function()
        setCultivating(player, false)
    end)
end

local function setupPlayer(player)
    local progress = PlayerData.waitForData(player)
    if not progress or player:FindFirstChild("leaderstats") then
        return
    end

    local leaderstats = Instance.new("Folder")
    leaderstats.Name = "leaderstats"

    local qi = Instance.new("IntValue")
    qi.Name = "Qi"
    qi.Value = progress.Qi
    qi.Parent = leaderstats

    local rank = Instance.new("StringValue")
    rank.Name = "Rank"
    rank.Value = Ranks.getRankById(progress.RankId).Name
    rank.Parent = leaderstats

    leaderstats.Parent = player

    player:SetAttribute("IsCultivating", false)

    player:GetAttributeChangedSignal("IsFlying"):Connect(function()
        if player:GetAttribute("IsFlying") == true and cultivatingPlayers[player] then
            setCultivating(player, false)
        end
    end)
    player:GetAttributeChangedSignal("InTribulation"):Connect(function() -- a tribulation stops meditation: they must move
        if player:GetAttribute("InTribulation") == true and cultivatingPlayers[player] then
            setCultivating(player, false)
        end
    end)

    player.CharacterAdded:Connect(function(character)
        onCharacterAdded(player, character)
    end)
    if player.Character then
        task.spawn(onCharacterAdded, player, player.Character)
    end
end

local function onCultivationRequest(player, wantsToCultivate)
    if player.Parent ~= Players or typeof(wantsToCultivate) ~= "boolean" then
        return
    end

    if wantsToCultivate == (cultivatingPlayers[player] == true) then
        return
    end

    if wantsToCultivate then
        local lastTime = lastToggleTime[player]
        if lastTime and os.clock() - lastTime < GameConfig.CultivationToggleCooldown then
            return
        end

        if not (getQiValue(player) and hasAliveCharacter(player)) then
            return
        end

        if player:GetAttribute("IsFlying") == true or player:GetAttribute("CarryingEgg") ~= nil
            or player:GetAttribute("InTribulation") == true then -- facing the heavens is no time to meditate
            return
        end
    end

    lastToggleTime[player] = os.clock()
    setCultivating(player, wantsToCultivate)
end

local function awardCultivationQi(player)
    local qi = getQiValue(player)
    if not (qi and hasAliveCharacter(player)) then
        setCultivating(player, false)
        return
    end
    local from = cultivatingFrom[player]
    local rootPart = player.Character:FindFirstChild("HumanoidRootPart")
    if (from and rootPart and (rootPart.Position - from).Magnitude > STILL_RADIUS) or player:GetAttribute("CarryingEgg") ~= nil then
        setCultivating(player, false)
        return
    end

    local atStation = isAtTrainingStation(player)
    if player:GetAttribute("AtTrainingStation") ~= atStation then
        player:SetAttribute("AtTrainingStation", atStation)
    end

    local bonusPercent = PetInventory.getQiBonusPercent(player)
    if atStation then
        bonusPercent += GameConfig.TrainingStation.QiBonusPercent
    end
    local _, rankValue = PlayerData.getStats(player)
    local multiplier = Ranks.getQiMultiplier(rankValue and rankValue.Value) * PassRules.qiMultiplier(player)
    qi.Value += math.floor(GameConfig.CultivationQiReward * multiplier * (100 + bonusPercent) / 100)
end

Players.PlayerAdded:Connect(setupPlayer)

Players.PlayerRemoving:Connect(function(player)
    cultivatingPlayers[player] = nil
    cultivatingFrom[player] = nil
    lastToggleTime[player] = nil
end)

RemoteEvents.CultivationEvent.OnServerEvent:Connect(onCultivationRequest)

for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end

task.spawn(function()
    local island = workspace:WaitForChild(WorldConfig.FolderName):WaitForChild(WorldConfig.StartIsland)
    local station = island:WaitForChild("QiSpring")
    stationCenter = station:WaitForChild("SpringWater").Position
end)

while true do
    task.wait(GameConfig.CultivationInterval)

    for player in cultivatingPlayers do
        awardCultivationQi(player)
    end
end
