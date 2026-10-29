-- Spirit Relics on this client: a "Relics 3/9" counter, a message when you
-- attune to one, and dimming the relics you've already found (only for you).
-- The server decides everything (see DiscoveryService); this script only shows it.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local applyHudScale = require(script.Parent:WaitForChild("HudScale"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local HUD_NAME = "RelicHud"
local PANEL_COLOR = Color3.fromRGB(20, 20, 30)
local RELIC_COLOR = Color3.fromRGB(170, 235, 255)
local MESSAGE_SECONDS = 4
local FOUND_TRANSPARENCY = 0.7 -- How faded a relic you've found looks

local relicsById = {}
for _, relic in GameConfig.Relics do
    relicsById[relic.Id] = relic
end

-- Build the HUD ------------------------------------------------------------

local oldHud = playerGui:FindFirstChild(HUD_NAME)
if oldHud then
    oldHud:Destroy()
end

local hud = Instance.new("ScreenGui")
hud.Name = HUD_NAME
hud.ResetOnSpawn = false

-- Top left, below Roblox's own menu buttons
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

-- Messages appear just below the pet hatch messages at the top centre
local message = Instance.new("TextLabel")
message.Name = "RelicMessage"
message.AnchorPoint = Vector2.new(0.5, 0)
message.Position = UDim2.new(0.5, 0, 0, 64)
message.Size = UDim2.fromOffset(380, 44)
message.BackgroundColor3 = PANEL_COLOR
message.BackgroundTransparency = 0.25
message.Font = Enum.Font.GothamBold
message.TextScaled = true
message.TextColor3 = RELIC_COLOR
message.Visible = false
message.Parent = hud
applyHudScale(message)

local messageCorner = Instance.new("UICorner")
messageCorner.CornerRadius = UDim.new(0, 10)
messageCorner.Parent = message

local messagePadding = Instance.new("UIPadding")
messagePadding.PaddingLeft = UDim.new(0, 10)
messagePadding.PaddingRight = UDim.new(0, 10)
messagePadding.PaddingTop = UDim.new(0, 6)
messagePadding.PaddingBottom = UDim.new(0, 6)
messagePadding.Parent = message

hud.Parent = playerGui

local messageCount = 0

local function showMessage(text)
    messageCount += 1
    local thisMessage = messageCount
    message.Text = text
    message.Visible = true

    task.delay(MESSAGE_SECONDS, function()
        if messageCount == thisMessage then
            message.Visible = false
        end
    end)
end

-- Relics in the world -----------------------------------------------------------

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
    local leaderstats = player:FindFirstChild("leaderstats")
    local rankValue = leaderstats and leaderstats:FindFirstChild("Rank")
    return if rankValue then rankValue.Value else ""
end

-- Dims a found relic and hides its prompt, or shows which rank a locked one
-- needs. Changes made here are only seen by this player.
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

-- Relics stream in as you fly closer, so style each one when it arrives
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

-- Messages from the server -------------------------------------------------------

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
