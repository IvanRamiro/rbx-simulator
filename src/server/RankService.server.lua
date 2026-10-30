local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local PlayerData = require(script.Parent:WaitForChild("PlayerData"))

local function tryRankUp(player)
    if player.Parent ~= Players then
        return
    end

    local leaderstats = player:FindFirstChild("leaderstats")
    local qi = leaderstats and leaderstats:FindFirstChild("Qi")
    local rank = leaderstats and leaderstats:FindFirstChild("Rank")
    if not (qi and rank) then
        return
    end

    local nextRank = Ranks.getNextRank(rank.Value)
    if not nextRank then
        return
    end

    if qi.Value < nextRank.QiRequired then
        return
    end

    rank.Value = nextRank.Name
    PlayerData.saveSoon(player)
end

RemoteEvents.RankUpEvent.OnServerEvent:Connect(tryRankUp)
