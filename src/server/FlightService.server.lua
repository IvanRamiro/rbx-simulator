local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local PlayerData = require(script.Parent:WaitForChild("PlayerData"))

local lastToggleTime = {}

local function setFlying(player, isFlying)
    if player:GetAttribute("IsFlying") ~= isFlying then
        player:SetAttribute("IsFlying", isFlying)
    end
end

local function hasAliveCharacter(player)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    return humanoid ~= nil and humanoid.Health > 0
end

local function updateFlightSpeed(player, rankValue)
    local speed = Ranks.getFlightSpeed(rankValue.Value)
    player:SetAttribute("FlightSpeed", speed)
    if speed <= 0 then
        setFlying(player, false)
    end
end

local function onFlightRequest(player, wantsToFly)
    if player.Parent ~= Players or typeof(wantsToFly) ~= "boolean" then
        return
    end

    if wantsToFly == (player:GetAttribute("IsFlying") == true) then
        return
    end

    if wantsToFly then
        local lastTime = lastToggleTime[player]
        if lastTime and os.clock() - lastTime < GameConfig.Flight.ToggleCooldown then
            return
        end

        local speed = player:GetAttribute("FlightSpeed")
        if not (typeof(speed) == "number" and speed > 0 and hasAliveCharacter(player)) then
            return
        end
    end

    lastToggleTime[player] = os.clock()
    setFlying(player, wantsToFly)
end

local function onCharacterAdded(player, character)
    setFlying(player, false)

    local humanoid = character:WaitForChild("Humanoid")
    humanoid.Died:Connect(function()
        setFlying(player, false)
    end)
end

local function setupPlayer(player)
    player:SetAttribute("IsFlying", false)
    player:SetAttribute("FlightSpeed", 0)

    player.CharacterAdded:Connect(function(character)
        onCharacterAdded(player, character)
    end)
    if player.Character then
        task.spawn(onCharacterAdded, player, player.Character)
    end

    if not PlayerData.waitForData(player) then
        return
    end
    local leaderstats = player:WaitForChild("leaderstats", 30)
    local rankValue = leaderstats and leaderstats:WaitForChild("Rank", 30)
    if not rankValue then
        return
    end

    updateFlightSpeed(player, rankValue)
    rankValue.Changed:Connect(function()
        updateFlightSpeed(player, rankValue)
    end)
end

RemoteEvents.FlightEvent.OnServerEvent:Connect(onFlightRequest)

Players.PlayerAdded:Connect(setupPlayer)
Players.PlayerRemoving:Connect(function(player)
    lastToggleTime[player] = nil
end)

for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
