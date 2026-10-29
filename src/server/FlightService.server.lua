-- Decides who may fly and how fast. Flight unlocks at a cultivation rank and
-- gets faster as players rank up (GameConfig.Flight.SpeedLevels). The client
-- only asks to take off or land; the server checks the rank and sets two
-- replicated attributes that the client's FlightController follows:
--   FlightSpeed  studs per second (0 = flight is still locked)
--   IsFlying     whether the player is flying right now
-- The flying movement itself runs on the player's client, like walking does,
-- because Roblox gives each player control of their own character's physics.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local PlayerData = require(script.Parent:WaitForChild("PlayerData"))

-- Last time each player took off or landed, keyed by Player
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

-- The client only sends true (take off) or false (land)
local function onFlightRequest(player, wantsToFly)
    if player.Parent ~= Players or typeof(wantsToFly) ~= "boolean" then
        return
    end

    if wantsToFly == (player:GetAttribute("IsFlying") == true) then
        return -- Already in the requested state
    end

    -- Landing is always allowed. Taking off needs flight unlocked and a
    -- living character, and is rate-limited.
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
    -- Every new character starts on the ground
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

    -- The rank lives in leaderstats, which QiService creates once data has loaded
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

-- Handle players who joined before this script finished loading
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
