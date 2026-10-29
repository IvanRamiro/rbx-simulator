-- Spirit Relics: hold the prompt at a relic to attune to it once, for a
-- one-time Qi reward (GameConfig.Relics). The relics are built by
-- IslandService and tagged, so this script finds them wherever they are.
--
-- The client never says which relic or how much Qi: the server uses the
-- relic whose prompt fired, checks the player is really there and has the
-- rank for it, and only rewards each relic once per player.
-- Found relics are shared with the player's client through the replicated
-- "FoundRelics" attribute (e.g. "GroveHeart,EmberHeart"), so it can dim them.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Discoveries = require(script.Parent:WaitForChild("Discoveries"))
local IslandBuilder = require(script.Parent:WaitForChild("IslandBuilder"))
local PlayerData = require(script.Parent:WaitForChild("PlayerData"))

-- Extra distance allowed beyond the prompt's range, for network delay
local PROMPT_DISTANCE_TOLERANCE = 6

local function publishFound(player)
    local relicIds = Discoveries.exportData(player)
    if relicIds then
        player:SetAttribute("FoundRelics", table.concat(relicIds, ","))
    end
end

-- Uses the server's own view of the character's position
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
    -- Triggered fires on the server, after the player has held the prompt
    prompt.Triggered:Connect(function(player)
        onRelicTriggered(player, relicId, crystal, maxDistance)
    end)
end

-- Waits for saved data, then shares the player's found relics with their client
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

-- Handle players who joined before this script finished loading
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
