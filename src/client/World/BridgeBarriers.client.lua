-- The Qi barriers across the start of each island bridge (tagged GameConfig.BridgeBarrierTag, with
-- the RankId that opens them). A barrier is solid until this player reaches its rank; from then on
-- it lets them through (collision off for this player only) and glows fainter, an open seal.
-- WorldService still returns anyone below the rank who gets onto the bridge some other way.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))

local player = Players.LocalPlayer
local OPEN_TRANSPARENCY = 0.75

local barriers = {} -- [part] = { Index = required rank index, Transparency = as built }

local function playerIndex()
    local leaderstats = player:FindFirstChild("leaderstats")
    local rank = leaderstats and leaderstats:FindFirstChild("Rank")
    return rank and Ranks.getIndex(rank.Value) or 0
end

local function refresh(part, entry)
    local open = playerIndex() >= entry.Index
    part.CanCollide = not open
    part.Transparency = open and OPEN_TRANSPARENCY or entry.Transparency
end

local function refreshAll()
    for part, entry in barriers do
        refresh(part, entry)
    end
end

local function add(part)
    local rank = Ranks.getRankById(part:GetAttribute("RankId"))
    if not (rank and part:IsA("BasePart")) then
        return
    end
    local entry = { Index = Ranks.getIndex(rank.Name), Transparency = part.Transparency }
    barriers[part] = entry
    refresh(part, entry)
end

CollectionService:GetInstanceAddedSignal(GameConfig.BridgeBarrierTag):Connect(add)
CollectionService:GetInstanceRemovedSignal(GameConfig.BridgeBarrierTag):Connect(function(part)
    barriers[part] = nil
end)
for _, part in CollectionService:GetTagged(GameConfig.BridgeBarrierTag) do
    add(part)
end

local leaderstats = player:WaitForChild("leaderstats")
local rank = leaderstats:WaitForChild("Rank")
rank.Changed:Connect(refreshAll)
refreshAll()
