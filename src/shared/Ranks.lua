local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local Ranks = {}

function Ranks.getIndex(rankName)
    for index, rank in GameConfig.Ranks do
        if rank.Name == rankName then
            return index
        end
    end

    return nil
end

function Ranks.getRank(rankName)
    local index = Ranks.getIndex(rankName)
    return if index then GameConfig.Ranks[index] else nil
end

function Ranks.getRankById(rankId)
    for _, rank in GameConfig.Ranks do
        if rank.Id == rankId then
            return rank
        end
    end

    return nil
end

function Ranks.getNextRank(rankName)
    local index = Ranks.getIndex(rankName)
    if not index then
        return nil
    end

    return GameConfig.Ranks[index + 1]
end

-- The Qinggong level a rank has reached, and the next level (nil at the top).
function Ranks.getQinggong(rankName)
    local rankIndex = Ranks.getIndex(rankName) or 0
    local current = GameConfig.Qinggong.Levels[1]

    for _, level in GameConfig.Qinggong.Levels do
        local levelRank = Ranks.getRankById(level.RankId)
        if Ranks.getIndex(levelRank.Name) <= rankIndex then
            current = level
        else
            return current, level
        end
    end

    return current, nil
end

function Ranks.getQiMultiplier(rankName)
    local rank = Ranks.getRank(rankName)
    return if rank and rank.QiMultiplier then rank.QiMultiplier else 1
end

function Ranks.isAtLeast(rankName, rankId)
    local index = Ranks.getIndex(rankName)
    local required = Ranks.getRankById(rankId)
    return index ~= nil and required ~= nil and index >= Ranks.getIndex(required.Name)
end

assert(
    Ranks.getIndex(GameConfig.StartingRank) == 1,
    "GameConfig.StartingRank must be the first entry in GameConfig.Ranks"
)

local seenRankIds = {}
local seenRankNames = {}
for _, rank in GameConfig.Ranks do
    assert(typeof(rank.Id) == "string" and not seenRankIds[rank.Id], "Every rank needs a unique Id: " .. rank.Name)
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

local previousQinggongLevel = nil
for _, level in GameConfig.Qinggong.Levels do
    local levelRank = Ranks.getRankById(level.RankId)
    assert(levelRank, "GameConfig.Qinggong.Levels has an unknown RankId: " .. tostring(level.RankId))
    if previousQinggongLevel then
        assert(
            Ranks.getIndex(levelRank.Name) > Ranks.getIndex(Ranks.getRankById(previousQinggongLevel.RankId).Name)
                and level.AirLeaps > previousQinggongLevel.AirLeaps,
            "GameConfig.Qinggong.Levels must go from lower to higher ranks and air leaps"
        )
    else
        assert(Ranks.getIndex(levelRank.Name) == 1, "GameConfig.Qinggong.Levels must start at the first rank")
    end
    previousQinggongLevel = level
end

for index = 2, #GameConfig.Ranks do
    assert(
        GameConfig.Ranks[index].QiRequired > GameConfig.Ranks[index - 1].QiRequired,
        "GameConfig.Ranks must be ordered from lowest to highest QiRequired"
    )
end

return Ranks
