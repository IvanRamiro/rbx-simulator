local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Discoveries = require(script.Parent:WaitForChild("Discoveries"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))
local Elements = require(script.Parent.Parent:WaitForChild("Shop"):WaitForChild("Elements"))
local Wallet = require(script.Parent.Parent:WaitForChild("Shop"):WaitForChild("Wallet"))
local PromptRules = require(script.Parent:WaitForChild("PromptRules"))

local function publishFound(player)
    local relicIds = Discoveries.exportData(player)
    if relicIds then
        player:SetAttribute("FoundRelics", table.concat(relicIds, ","))
    end
end

local function onRelicTriggered(player, relicId, crystal, maxDistance)
    if player.Parent ~= Players or not Discoveries.isSetUp(player) then
        return
    end

    local relic = Discoveries.getRelic(relicId)
    if not relic or Discoveries.hasFound(player, relicId) or not PromptRules.isAliveAndNear(player, crystal, maxDistance) then
        return
    end

    local qi, rankValue = PlayerData.getStats(player)
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

    local hadElement = relic.Element ~= nil and Elements.has(player, relic.Element)
    if not Discoveries.markFound(player, relicId) then
        return
    end

    -- (the Qi passes multiply it as they do every Qi reward: Qi Surge promises it, release audit 2026-11-12)
    local qiReward = math.floor(relic.QiReward * PassRules.qiMultiplier(player))
    qi.Value += qiReward
    local stones = Shop.relicStones(relic)
    Wallet.add(player, stones, "Relic", relicId)
    publishFound(player)
    PlayerData.saveSoon(player)
    -- Element: the forge element this relic unlocked, when the player didn't have it yet
    RemoteEvents.RelicResultEvent:FireClient(player, { RelicId = relicId, QiReward = qiReward, Stones = stones,
        Element = if relic.Element and not hadElement then relic.Element else nil })
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

    -- a relic set deep among roots is reached from farther (GameConfig Relics: Reach)
    local relic = Discoveries.getRelic(relicId)
    if relic and relic.Reach then
        prompt.MaxActivationDistance = relic.Reach
    end
    local maxDistance = PromptRules.maxDistance(prompt)
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

CollectionService:GetInstanceAddedSignal(GameConfig.RelicTag):Connect(connectRelic)
for _, model in CollectionService:GetTagged(GameConfig.RelicTag) do
    connectRelic(model)
end

Players.PlayerAdded:Connect(setupPlayer)

for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
