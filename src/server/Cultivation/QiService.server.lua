-- Cultivating: CultivationEvent starts and stops it, and every CultivationInterval the server pays each cultivating player
-- their Qi (the rank's multiplier, Qi passes, their pets' bonus and the Training Ground's). Moving, or carrying an egg, stops it.
-- It also sets whether they sit on the Blossom Sanctuary's Training Ground (the AtTrainingStation attribute): inside its kerb's
-- outline (Placements.BlossomSanctuary.TrainingGround, island-local) and within its Height of the lawn.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local WeatherConfig = require(ReplicatedStorage:WaitForChild("WeatherConfig"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local WorldConfig = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("WorldConfig"))
local PetInventory = require(script.Parent.Parent:WaitForChild("Pets"):WaitForChild("PetInventory"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))

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

-- the Training Ground, once its island is found: { frame (island-local to world), outline (Vector2s), floor, height, min, max }
local trainingGround = nil

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

-- even-odd: is (x, z) inside the closed outline?
local function insideOutline(outline, x, z)
    local inside = false
    local count = #outline
    local j = count
    for i = 1, count do
        local a, b = outline[i], outline[j]
        if (a.Y > z) ~= (b.Y > z) and x < (b.X - a.X) * (z - a.Y) / (b.Y - a.Y) + a.X then
            inside = not inside
        end
        j = i
    end
    return inside
end

local function isAtTrainingStation(player)
    local character = player.Character
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    local zone = trainingGround
    if not (zone and rootPart) then
        return false
    end
    local at = zone.frame:PointToObjectSpace(rootPart.Position)
    if math.abs(at.Y - zone.floor) > zone.height or at.X < zone.min.X or at.X > zone.max.X or at.Z < zone.min.Y or at.Z > zone.max.Y then
        return false
    end
    return insideOutline(zone.outline, at.X, at.Z)
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
    -- a Qi Bloom (the weather, WeatherService's published state) adds its share too
    if ReplicatedStorage:GetAttribute("Weather") == "QiBloom" then
        bonusPercent += WeatherConfig.States.QiBloom.QiBonusPercent
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
    -- (only where the island is built: without it there is no Training Ground bonus)
    local name = GameConfig.TrainingStation.Island
    local island = workspace:WaitForChild(WorldConfig.FolderName):WaitForChild(name, 30)
    local build = ServerStorage:FindFirstChild("WorldBuild")
    local module = build and build:FindFirstChild("Placements") and build.Placements:FindFirstChild(name)
    if not (island and module) then
        warn("QiService: no " .. name .. " (or its placements): no Training Ground bonus")
        return
    end
    local rules = require(module).TrainingGround
    local min, max = Vector2.new(math.huge, math.huge), Vector2.new(-math.huge, -math.huge)
    for _, point in rules.Outline do
        min, max = min:Min(point), max:Max(point)
    end
    trainingGround = { frame = WorldConfig.frame(name), outline = rules.Outline, floor = rules.Floor, height = rules.Height, min = min, max = max }
end)

while true do
    task.wait(GameConfig.CultivationInterval)

    -- (each player under pcall: one error used to be able to stop this loop for the whole server; bug audit, 2026-11-24)
    for player in cultivatingPlayers do
        local ok, err = pcall(awardCultivationQi, player)
        if not ok then
            warn("QiService: cultivation Qi for " .. player.Name .. " failed: " .. tostring(err))
        end
    end
end
