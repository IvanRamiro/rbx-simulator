-- How the Spirit Relics look on this screen: found or unfound, locked below their rank, an unfound one turning and bobbing.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

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
local GLOW_FOUND_TRANSPARENCY = 0.6 -- a found relic's small glows dim too (the modelled relics' Glow pieces)
local DRIFT_RANGE = 160 -- studs from the camera within which a relic slowly turns and bobs
local TURN_SPEED = 0.35 -- radians a second
local BOB = 0.25 -- studs up and down

local relicsById = {}
for _, relic in GameConfig.Relics do
    relicsById[relic.Id] = relic
end

local _, setFound = Hud.chip("RelicCounter", UiTheme.Icons.Relics, 2, {
    Format = function(found)
        return found .. " / " .. #GameConfig.Relics
    end,
    FloatFormat = tostring, Color = UiTheme.Colors.Highlight,
})
setFound(0)

local message = Toast.new("RelicMessage", RELIC_COLOR, MESSAGE_SECONDS)

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
    for _, piece in model:GetChildren() do
        if piece:IsA("BasePart") and piece:GetAttribute("RelicGlow") then
            piece.Transparency = if isFound then GLOW_FOUND_TRANSPARENCY else 0
        end
    end
    model:SetAttribute("Found", isFound)

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
    setFound(foundCount)

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
        message:show(relic.DisplayName .. " needs " .. tostring(result.RequiredRank) .. " to attune.", "Warning")
    else
        local stones = if typeof(result.Stones) == "number" and result.Stones > 0 then ", +" .. result.Stones .. " Spirit Stones" else ""
        local info = typeof(result.Element) == "string" and GameConfig.Forge.Elements[result.Element]
        local element = if info then ". " .. info.DisplayName .. " unlocked at the Blacksmith's forge" else ""
        Sfx.play("Attune")
        message:show("Attuned to " .. relic.DisplayName .. "! +" .. tostring(result.QiReward) .. " Qi" .. stones .. element, "Reward")
    end
end)

-- An unfound relic slowly turns and bobs where it floats (only on this screen: the server's relic stays still, and its prompt's reach is
-- measured from there). A found one rests.
local rest = {}
RunService.Heartbeat:Connect(function()
    local camera = workspace.CurrentCamera
    if not camera then
        return
    end
    local t = os.clock()
    for _, model in CollectionService:GetTagged(GameConfig.RelicTag) do
        local point = model:GetAttribute("RelicPoint")
        if typeof(point) ~= "Vector3" or not model.PrimaryPart then
            continue
        end
        rest[model] = rest[model] or model:GetPivot()
        if model:GetAttribute("Found") or (camera.CFrame.Position - point).Magnitude > DRIFT_RANGE then
            continue
        end
        local phase = point.X * 0.37 + point.Z * 0.21 -- each relic on its own beat
        local turn = CFrame.new(point) * CFrame.Angles(0, t * TURN_SPEED + phase, 0) * CFrame.new(-point)
        model:PivotTo(CFrame.new(0, BOB * math.sin(t * 1.3 + phase), 0) * turn * rest[model])
    end
end)
CollectionService:GetInstanceRemovedSignal(GameConfig.RelicTag):Connect(function(model)
    rest[model] = nil
end)
