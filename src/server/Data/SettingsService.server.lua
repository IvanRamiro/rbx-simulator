-- Loads each player's settings (Settings) and takes changes from their settings window.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local PlayerData = require(script.Parent:WaitForChild("PlayerData"))
local Settings = require(script.Parent:WaitForChild("Settings"))

local THROTTLE = 0.05

local lastChange = {}

local function setupPlayer(player)
    local progress, isNewPlayer = PlayerData.waitForData(player)
    if progress and player.Parent == Players then
        Settings.setupPlayer(player, if isNewPlayer then nil else progress)
    end
end

Players.PlayerAdded:Connect(setupPlayer)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
Players.PlayerRemoving:Connect(function(player)
    lastChange[player] = nil
end)

RemoteEvents.SettingsEvent.OnServerEvent:Connect(function(player, key, value)
    if os.clock() - (lastChange[player] or 0) < THROTTLE then
        return
    end
    lastChange[player] = os.clock()
    if Settings.set(player, key, value) then
        PlayerData.saveSoon(player)
    end
end)
