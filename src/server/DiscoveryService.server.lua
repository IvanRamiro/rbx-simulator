local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Discoveries = require(script.Parent:WaitForChild("Discoveries"))
local IslandBuilder = require(script.Parent:WaitForChild("IslandBuilder"))
local PlayerData = require(script.Parent:WaitForChild("PlayerData"))

local PROMPT_DISTANCE_TOLERANCE = 6

local function publishFound(player)
    local relicIds = Discoveries.exportData(player)
    if relicIds then
        player:SetAttribute("FoundRelics", table.concat(relicIds, ","))
    end
end

local function isAliveAndNear(player, part, maxDistance)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    if not (humanoid and rootPart) or humanoid.Health <= 0 then
        return false
    end

    return (rootPart.Position - part.Position).Magnitude <= maxDistance
end

local function onRelicTriggered(player, relicId, crystal, maxDistance)
    if player.Parent ~= Players or not Discoveries.isSetUp(player) then
        return
    end

    local relic = Discoveries.getRelic(relicId)
    if not relic or Discoveries.hasFound(player, relicId) or not isAliveAndNear(player, crystal, maxDistance) then
        return
    end

    local leaderstats = player:FindFirstChild("leaderstats")
    local qi = leaderstats and leaderstats:FindFirstChild("Qi")
    local rankValue = leaderstats and leaderstats:FindFirstChild("Rank")
    if not (qi and rankValue) then
        return
    end

    if not Ranks.isAtLeast(rankValue.Value, relic.RequiredRank) then
        RemoteEvents.RelicResultEvent:FireClient(player, {
            RelicId = relicId,
            Reason = "Locked",
            RequiredRank = Ranks.getRankById(relic.RequiredRank).Name,
        })
        return
    end

    if not Discoveries.markFound(player, relicId) then
        return
    end

    qi.Value += relic.QiReward
    publishFound(player)
    PlayerData.saveSoon(player)
    RemoteEvents.RelicResultEvent:FireClient(player, { RelicId = relicId, QiReward = relic.QiReward })
end

local connectedRelics = {}

local function connectRelic(model)
    local relicId = model:GetAttribute("RelicId")
    local crystal = model:FindFirstChild("RelicCrystal")
    local prompt = crystal and crystal:FindFirstChildOfClass("ProximityPrompt")
    if connectedRelics[model] or not (typeof(relicId) == "string" and prompt) then
        return
    end
    connectedRelics[model] = true

    local maxDistance = prompt.MaxActivationDistance + PROMPT_DISTANCE_TOLERANCE
    prompt.Triggered:Connect(function(player)
        onRelicTriggered(player, relicId, crystal, maxDistance)
    end)
end

local function setupPlayer(player)
    local progress = PlayerData.waitForData(player)
    if not progress then
        return
    end

    Discoveries.setupPlayer(player, progress.Relics)
    publishFound(player)
end

CollectionService:GetInstanceAddedSignal(IslandBuilder.RELIC_TAG):Connect(connectRelic)
for _, model in CollectionService:GetTagged(IslandBuilder.RELIC_TAG) do
    connectRelic(model)
end

Players.PlayerAdded:Connect(setupPlayer)

for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
