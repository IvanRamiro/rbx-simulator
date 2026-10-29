
-- Helpers for looking up the cultivation ranks defined in GameConfig.Ranks.
-- Used by the server (to validate rank-ups) and the client (to display them).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local Ranks = {}

-- Returns the position of a rank in GameConfig.Ranks, or nil if it doesn't exist
function Ranks.getIndex(rankName)
    for index, rank in GameConfig.Ranks do
        if rank.Name == rankName then
            return index
        end
    end

    return nil
end

-- Returns the rank's full definition from GameConfig.Ranks, or nil if it doesn't exist
function Ranks.getRank(rankName)
    local index = Ranks.getIndex(rankName)
    return if index then GameConfig.Ranks[index] else nil
end

-- Finds a rank by its stable Id (used in saved data), or nil if it doesn't exist
function Ranks.getRankById(rankId)
    for _, rank in GameConfig.Ranks do
        if rank.Id == rankId then
            return rank
        end
    end

    return nil
end

-- Returns the rank after rankName, or nil if rankName is the highest (or unknown)
function Ranks.getNextRank(rankName)
    local index = Ranks.getIndex(rankName)
    if not index then
        return nil
    end

    return GameConfig.Ranks[index + 1]
end

-- Flight speed for a rank (from GameConfig.Flight.SpeedLevels): returns the
-- speed (0 while flight is still locked) and the next speed level to reach,
-- as { RankId, Speed }, or nil when the fastest level is reached
function Ranks.getFlightSpeed(rankName)
    local rankIndex = Ranks.getIndex(rankName) or 0
    local speed = 0

    for _, level in GameConfig.Flight.SpeedLevels do
        local levelRank = Ranks.getRankById(level.RankId)
        if Ranks.getIndex(levelRank.Name) <= rankIndex then
            speed = level.Speed
        else
            return speed, level
        end
    end

    return speed, nil
end

-- Cultivation power for a rank: every Qi reward is multiplied by this
-- (1 for unknown ranks)
function Ranks.getQiMultiplier(rankName)
    local rank = Ranks.getRank(rankName)
    return if rank and rank.QiMultiplier then rank.QiMultiplier else 1
end

-- Whether rankName is rankId's rank or higher (false for unknown ranks)
function Ranks.isAtLeast(rankName, rankId)
    local index = Ranks.getIndex(rankName)
    local required = Ranks.getRankById(rankId)
    return index ~= nil and required ~= nil and index >= Ranks.getIndex(required.Name)
end

-- Catch config mistakes as soon as the game starts
assert(
    Ranks.getIndex(GameConfig.StartingRank) == 1,
    "GameConfig.StartingRank must be the first entry in GameConfig.Ranks"
)

local seenRankIds = {}
local seenRankNames = {}
for _, rank in GameConfig.Ranks do
    assert(typeof(rank.Id) == "string" and not seenRankIds[rank.Id], "Every rank needs a unique Id: " .. rank.Name)
    -- leaderstats shows the Name, and the game looks ranks up by it
    assert(not seenRankNames[rank.Name], "Every rank needs a unique Name: " .. rank.Name)
    assert(typeof(rank.Realm) == "string", "Every rank needs a Realm: " .. rank.Name)
    assert(table.find({ 1, 2, 3, 4, 5 }, rank.Level), "Rank Level must be 1 to 5: " .. rank.Name)
    assert(typeof(rank.QiMultiplier) == "number" and rank.QiMultiplier >= 1, "Rank QiMultiplier must be 1 or more: " .. rank.Name)
    seenRankIds[rank.Id] = true
    seenRankNames[rank.Name] = true
end

local seenRelicIds = {}
for _, relic in GameConfig.Relics do
    assert(typeof(relic.Id) == "string" and not seenRelicIds[relic.Id], "Every relic needs a unique Id: " .. tostring(relic.Id))
    assert(Ranks.getRankById(relic.RequiredRank), "Relic " .. relic.Id .. " has an unknown RequiredRank")
    seenRelicIds[relic.Id] = true
end

local previousFlightLevel = nil
for _, level in GameConfig.Flight.SpeedLevels do
    local levelRank = Ranks.getRankById(level.RankId)
    assert(levelRank, "GameConfig.Flight.SpeedLevels has an unknown RankId: " .. tostring(level.RankId))
    if previousFlightLevel then
        assert(
            Ranks.getIndex(levelRank.Name) > Ranks.getIndex(Ranks.getRankById(previousFlightLevel.RankId).Name)
                and level.Speed > previousFlightLevel.Speed,
            "GameConfig.Flight.SpeedLevels must go from lower to higher ranks and speeds"
        )
    end
    previousFlightLevel = level
end

for index = 2, #GameConfig.Ranks do
    assert(
        GameConfig.Ranks[index].QiRequired > GameConfig.Ranks[index - 1].QiRequired,
        "GameConfig.Ranks must be ordered from lowest to highest QiRequired"
    )
end

return Ranks
