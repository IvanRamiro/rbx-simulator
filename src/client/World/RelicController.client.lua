local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Hud = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Hud"))
local UiTheme = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiTheme"))
local Toast = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Toast"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer

local RELIC_COLOR = Color3.fromRGB(170, 235, 255)
local MESSAGE_SECONDS = 4
local FOUND_TRANSPARENCY = 0.7

local relicsById = {}
for _, relic in GameConfig.Relics do
    relicsById[relic.Id] = relic
end

local _, counter = Hud.chip("RelicCounter", UiTheme.Icons.Relics, 2)
counter.Text = "0 / " .. #GameConfig.Relics .. " Relics"

local message = Toast.new(nil, "RelicMessage", nil, RELIC_COLOR, MESSAGE_SECONDS)

local function getFoundSet()
    local found = {}
    local value = player:GetAttribute("FoundRelics")
    if typeof(value) == "string" and value ~= "" then
        for _, relicId in string.split(value, ",") do
            found[relicId] = true
        end
    end
    return found
end

local function updateRelic(model, found, rankName)
    local relic = relicsById[model:GetAttribute("RelicId")]
    local crystal = model:FindFirstChild("RelicCrystal")
    if not (relic and crystal) then
        return
    end

    local isFound = found[relic.Id] == true
    crystal.Transparency = if isFound then FOUND_TRANSPARENCY else 0

    local light = crystal:FindFirstChildOfClass("PointLight")
    if light then
        light.Enabled = not isFound
    end
    local sparkles = crystal:FindFirstChildOfClass("ParticleEmitter")
    if sparkles then
        sparkles.Enabled = not isFound
    end

    local prompt = crystal:FindFirstChildOfClass("ProximityPrompt")
    if prompt then
        prompt.Enabled = not isFound
        prompt.ActionText = if Ranks.isAtLeast(rankName, relic.RequiredRank)
            then "Attune (+" .. relic.QiReward .. " Qi)"
            else "Needs " .. Ranks.getRankById(relic.RequiredRank).Name
    end
end

local function updateAll()
    local found = getFoundSet()
    local foundCount = 0
    for _ in found do
        foundCount += 1
    end
    counter.Text = foundCount .. " / " .. #GameConfig.Relics .. " Relics"

    local rankName = Ranks.getPlayerRankName(player)
    for _, model in CollectionService:GetTagged(GameConfig.RelicTag) do
        updateRelic(model, found, rankName)
    end
end

CollectionService:GetInstanceAddedSignal(GameConfig.RelicTag):Connect(function(model)
    updateRelic(model, getFoundSet(), Ranks.getPlayerRankName(player))
end)

player:GetAttributeChangedSignal("FoundRelics"):Connect(updateAll)

updateAll()
task.spawn(function()
    local rankValue = player:WaitForChild("leaderstats"):WaitForChild("Rank")
    rankValue.Changed:Connect(updateAll)
    updateAll() -- now with the player's rank
end)

RemoteEvents.RelicResultEvent.OnClientEvent:Connect(function(result)
    if typeof(result) ~= "table" then
        return
    end

    local relic = relicsById[result.RelicId]
    if not relic then
        return
    end

    if result.Reason == "Locked" then
        Sfx.play("Error")
        message:show(relic.DisplayName .. " needs " .. tostring(result.RequiredRank) .. " to attune.")
    else
        local stones = if typeof(result.Stones) == "number" and result.Stones > 0 then ", +" .. result.Stones .. " Spirit Stones" else ""
        local info = typeof(result.Element) == "string" and GameConfig.Forge.Elements[result.Element]
        local element = if info then ". " .. info.DisplayName .. " unlocked at the Blacksmith's forge" else ""
        Sfx.play("Attune")
        message:show("Attuned to " .. relic.DisplayName .. "! +" .. tostring(result.QiReward) .. " Qi" .. stones .. element)
    end
end)
