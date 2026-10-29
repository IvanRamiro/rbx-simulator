
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local PlayerData = require(script.Parent:WaitForChild("PlayerData"))

-- The client only asks to rank up and never says which rank it wants.
-- The server moves the player up exactly one rank, and only if they have
-- enough Qi, so ranks can't be skipped or claimed early.
local function tryRankUp(player)
    -- Ignore requests from players who are leaving
    if player.Parent ~= Players then
        return
    end

    -- leaderstats is created by QiService; skip players it hasn't set up yet
    local leaderstats = player:FindFirstChild("leaderstats")
    local qi = leaderstats and leaderstats:FindFirstChild("Qi")
    local rank = leaderstats and leaderstats:FindFirstChild("Rank")
    if not (qi and rank) then
        return
    end

    local nextRank = Ranks.getNextRank(rank.Value)
    if not nextRank then
        return -- Already at the highest rank
    end

    if qi.Value < nextRank.QiRequired then
        return
    end

    rank.Value = nextRank.Name
    PlayerData.saveSoon(player)
end

RemoteEvents.RankUpEvent.OnServerEvent:Connect(tryRankUp)
