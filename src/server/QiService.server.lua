
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local IslandConfig = require(script.Parent:WaitForChild("IslandConfig"))
local PetInventory = require(script.Parent:WaitForChild("PetInventory"))
local PlayerData = require(script.Parent:WaitForChild("PlayerData"))

-- How far above or below the spring's water a player can be and still count
-- as inside it (cultivating players levitate a little)
local STATION_HEIGHT_TOLERANCE = 12

-- Players who are currently cultivating: cultivatingPlayers[player] = true
local cultivatingPlayers = {}

-- Last time each player started or stopped cultivating, keyed by Player
local lastToggleTime = {}

local function getQiValue(player)
    local leaderstats = player:FindFirstChild("leaderstats")
    return leaderstats and leaderstats:FindFirstChild("Qi")
end

local function hasAliveCharacter(player)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    return humanoid ~= nil and humanoid.Health > 0
end

-- Centre of the Qi Spring's water, once IslandService has built it
local stationCenter = nil

-- The only place cultivation state changes. The "IsCultivating" attribute
-- replicates to every client, which use it for the UI, levitation and aura.
local function setCultivating(player, isCultivating)
    cultivatingPlayers[player] = if isCultivating then true else nil
    player:SetAttribute("IsCultivating", isCultivating)
    if not isCultivating then
        player:SetAttribute("AtTrainingStation", false)
    end
end

-- Uses the server's own view of the character's position
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
    -- Every new character starts out not cultivating
    setCultivating(player, false)

    local humanoid = character:WaitForChild("Humanoid")
    humanoid.Died:Connect(function()
        setCultivating(player, false)
    end)
end

-- This is the only place player stats are created. Other scripts (like
-- RankService) find these values instead of creating their own. Nothing is
-- created until saved data has loaded, so defaults never replace real progress.
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

    -- Parent last so clients see the finished folder all at once
    leaderstats.Parent = player

    player:SetAttribute("IsCultivating", false)

    -- Taking off ends meditation
    player:GetAttributeChangedSignal("IsFlying"):Connect(function()
        if player:GetAttribute("IsFlying") == true and cultivatingPlayers[player] then
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

-- The client only sends true (start) or false (stop). It never sends
-- amounts or timing; the server decides both.
local function onCultivationRequest(player, wantsToCultivate)
    if player.Parent ~= Players or typeof(wantsToCultivate) ~= "boolean" then
        return
    end

    if wantsToCultivate == (cultivatingPlayers[player] == true) then
        return -- Already in the requested state
    end

    -- Stopping is always allowed. Starting needs a living character and is
    -- rate-limited so players can't spam start/stop.
    if wantsToCultivate then
        local lastTime = lastToggleTime[player]
        if lastTime and os.clock() - lastTime < GameConfig.CultivationToggleCooldown then
            return
        end

        if not (getQiValue(player) and hasAliveCharacter(player)) then
            return
        end

        -- Cultivating needs the player to land first (see FlightService)
        if player:GetAttribute("IsFlying") == true then
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

    -- The "AtTrainingStation" attribute is only for the client's HUD
    local atStation = isAtTrainingStation(player)
    if player:GetAttribute("AtTrainingStation") ~= atStation then
        player:SetAttribute("AtTrainingStation", atStation)
    end

    -- Reward = base reward plus the pets' and Qi Spring's bonus percent, rounded down.
    -- Example: base 10 with +35% from pets and +50% from the spring = floor(10 * 185 / 100) = 18 Qi
    local bonusPercent = PetInventory.getQiBonusPercent(player)
    if atStation then
        bonusPercent += GameConfig.TrainingStation.QiBonusPercent
    end
    qi.Value += math.floor(GameConfig.CultivationQiReward * (100 + bonusPercent) / 100)
end

Players.PlayerAdded:Connect(setupPlayer)

Players.PlayerRemoving:Connect(function(player)
    cultivatingPlayers[player] = nil
    lastToggleTime[player] = nil
end)

RemoteEvents.CultivationEvent.OnServerEvent:Connect(onCultivationRequest)

-- Handle players who joined before this script finished loading
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end

-- The island is built by IslandService, which may still be running
task.spawn(function()
    local island = workspace:WaitForChild(IslandConfig.ModelName)
    local station = island:WaitForChild(IslandConfig.TrainingStation.ModelName)
    stationCenter = station:WaitForChild("SpringWater").Position
end)

-- One loop rewards every cultivating player, so there is never more than one
-- loop and toggling can't earn rewards faster than CultivationInterval.
while true do
    task.wait(GameConfig.CultivationInterval)

    for player in cultivatingPlayers do
        awardCultivationQi(player)
    end
end
