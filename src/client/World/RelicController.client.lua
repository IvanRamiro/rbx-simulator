local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local applyHudScale = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudScale"))
local Toast = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Toast"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local HUD_NAME = "RelicHud"
local PANEL_COLOR = Color3.fromRGB(20, 20, 30)
local RELIC_COLOR = Color3.fromRGB(170, 235, 255)
local MESSAGE_SECONDS = 4
local FOUND_TRANSPARENCY = 0.7

local relicsById = {}
for _, relic in GameConfig.Relics do
    relicsById[relic.Id] = relic
end

local oldHud = playerGui:FindFirstChild(HUD_NAME)
if oldHud then
    oldHud:Destroy()
end

local hud = Instance.new("ScreenGui")
hud.Name = HUD_NAME
hud.ResetOnSpawn = false

local counter = Instance.new("TextLabel")
counter.Name = "RelicCounter"
counter.Position = UDim2.fromOffset(16, 64)
counter.Size = UDim2.fromOffset(150, 30)
counter.BackgroundColor3 = PANEL_COLOR
counter.BackgroundTransparency = 0.25
counter.Font = Enum.Font.GothamBold
counter.TextScaled = true
counter.TextColor3 = RELIC_COLOR
counter.Text = "Relics 0/" .. #GameConfig.Relics
counter.Parent = hud
applyHudScale(counter)

local counterCorner = Instance.new("UICorner")
counterCorner.CornerRadius = UDim.new(0, 8)
counterCorner.Parent = counter

local counterPadding = Instance.new("UIPadding")
counterPadding.PaddingTop = UDim.new(0, 4)
counterPadding.PaddingBottom = UDim.new(0, 4)
counterPadding.Parent = counter

local message = Toast.new(hud, "RelicMessage", 64, RELIC_COLOR, MESSAGE_SECONDS)

hud.Parent = playerGui

local function showMessage(text)
    message:show(text)
end

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

local function getRankName()
    return Ranks.getPlayerRankName(player)
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
    counter.Text = "Relics " .. foundCount .. "/" .. #GameConfig.Relics

    local rankName = getRankName()
    for _, model in CollectionService:GetTagged(GameConfig.RelicTag) do
        updateRelic(model, found, rankName)
    end
end

CollectionService:GetInstanceAddedSignal(GameConfig.RelicTag):Connect(function(model)
    updateRelic(model, getFoundSet(), getRankName())
end)

player:GetAttributeChangedSignal("FoundRelics"):Connect(updateAll)

task.spawn(function()
    local rankValue = player:WaitForChild("leaderstats"):WaitForChild("Rank")
    rankValue.Changed:Connect(updateAll)
    updateAll()
end)

updateAll()

RemoteEvents.RelicResultEvent.OnClientEvent:Connect(function(result)
    if typeof(result) ~= "table" then
        return
    end

    local relic = relicsById[result.RelicId]
    if not relic then
        return
    end

    if result.Reason == "Locked" then
        showMessage(relic.DisplayName .. " needs " .. tostring(result.RequiredRank) .. " to attune.")
    else
        showMessage("Attuned to " .. relic.DisplayName .. "! +" .. tostring(result.QiReward) .. " Qi")
    end
end)
