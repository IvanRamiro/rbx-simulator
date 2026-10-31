-- Grants each player the Qinggong level of their rank: run speed (Humanoid.WalkSpeed) and the
-- number of mid-air leaps (the "QinggongAirLeaps" attribute the client controller reads).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local PlayerData = require(script.Parent:WaitForChild("PlayerData"))

local function applyLevel(player, rankValue)
    local level = Ranks.getQinggong(rankValue.Value)
    player:SetAttribute("QinggongAirLeaps", level.AirLeaps)

    local humanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
    if humanoid then
        humanoid.WalkSpeed = level.RunSpeed
    end
end

local function setupPlayer(player)
    local first = Ranks.getQinggong("")
    player:SetAttribute("QinggongAirLeaps", first.AirLeaps)

    if not PlayerData.waitForData(player) then
        return
    end
    local leaderstats = player:WaitForChild("leaderstats", 30)
    local rankValue = leaderstats and leaderstats:WaitForChild("Rank", 30)
    if not rankValue then
        return
    end

    applyLevel(player, rankValue)
    rankValue.Changed:Connect(function()
        applyLevel(player, rankValue)
    end)
    player.CharacterAdded:Connect(function(character)
        character:WaitForChild("Humanoid")
        applyLevel(player, rankValue)
    end)
end

Players.PlayerAdded:Connect(setupPlayer)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
