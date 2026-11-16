-- The Spin Wheel's rules (GameConfig.SpinWheel), shared so the wheel shows exactly what the server pays:
--   SpinRules.Segments              the segments, clockwise from the top (GameConfig.SpinWheel.Segments)
--   SpinRules.today()               the day a spin counts for: the daily reward's UTC day (RewardRules.today)
--   SpinRules.secondsToReset(now)   seconds until the next day's spins (now: the server's time, os.time() or GetServerTimeNow)
--   SpinRules.spinsLeft(record)     what a player's record { Day, Used, Extra, Bought } leaves: today's free and won spins
--                                    left, plus the bought ones (which never run out)
--   SpinRules.freeLeft(record)      today's free and won spins left alone (a spin takes these before a bought one)
--   SpinRules.roll(random)          a segment's index, by weight (random: a Random; the server's own)
--   SpinRules.stones(index, rankName, player)  what a Stones segment pays a player of this rank (with their passes' daily-stones
--                                    bonus: VIP's +50%, the owner 2026-11-17; player nil: without it)
--   SpinRules.bestEgg(rankName)     the best ordinary (non-Robux) egg this rank can take (the Egg segment's egg)
--   SpinRules.describe(index, rankName, player)  { Kind, Stones, Minutes, EggId, Short, Long, Icon key } of a segment for this rank
--   SpinRules.angleOf(index)        the segment's centre, degrees clockwise from the top
--   SpinRules.restricted(player)    whether paid random items are restricted where the player is (SpinService sets the player's
--                                    "RandomItemsRestricted" from PolicyService): there the jackpot pays stones, not an egg
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RewardRules = require(ReplicatedStorage:WaitForChild("RewardRules"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))

local config = GameConfig.SpinWheel

local SpinRules = {}

SpinRules.Segments = config.Segments
SpinRules.Count = #config.Segments
SpinRules.Step = 360 / #config.Segments

local totalWeight = 0
for _, segment in config.Segments do
    assert(segment.Weight > 0, "SpinWheel: every segment needs a weight")
    totalWeight += segment.Weight
end
SpinRules.TotalWeight = totalWeight

function SpinRules.today()
    return RewardRules.today()
end

function SpinRules.secondsToReset(now)
    now = now or os.time()
    return math.max(0, (math.floor(now / 86400) + 1) * 86400 - now)
end

-- A day record from an earlier day leaves today's full spins (its extras are gone with it); bought spins stay.
function SpinRules.freeLeft(record)
    if not record or record.Day ~= SpinRules.today() then
        return config.DailySpins
    end
    return math.max(0, config.DailySpins + (record.Extra or 0) - (record.Used or 0))
end

function SpinRules.spinsLeft(record)
    return SpinRules.freeLeft(record) + (if record then record.Bought or 0 else 0)
end

function SpinRules.roll(random)
    local pick = (random or Random.new()):NextNumber() * totalWeight
    for index, segment in config.Segments do
        pick -= segment.Weight
        if pick < 0 then
            return index
        end
    end
    return #config.Segments
end

-- the player's rank's index, or the first
local function rankIndex(rankName)
    return Ranks.getIndex(rankName) or 1
end

function SpinRules.stones(index, rankName, player)
    local segment = config.Segments[index]
    if not (segment and segment.Share) then
        return 0
    end
    local rank = GameConfig.Ranks[rankIndex(rankName)]
    local stones = Shop.roundNice(Shop.rankValue(rank.Id) * segment.Share)
    return if player then PassRules.dailyStones(player, stones) else stones
end

-- the largest stones segment's pay: what a full egg slot pays instead
function SpinRules.fallbackStones(rankName, player)
    local best, bestShare = nil, 0
    for index, segment in config.Segments do
        if segment.Share and segment.Share > bestShare then
            best, bestShare = index, segment.Share
        end
    end
    return SpinRules.stones(best, rankName, player)
end

-- the ordinary eggs (not the Robux one), each with its rank's place
local marketEggs = {}
for eggId, egg in GameConfig.Eggs do
    local rank = not egg.Exclusive and Ranks.getRankById(egg.RequiredRank)
    if rank then
        table.insert(marketEggs, { Id = eggId, Index = Ranks.getIndex(rank.Name) or 1 })
    end
end
table.sort(marketEggs, function(a, b)
    return a.Index > b.Index or (a.Index == b.Index and a.Id < b.Id)
end)

function SpinRules.bestEgg(rankName)
    local index = rankIndex(rankName)
    for _, entry in marketEggs do
        if entry.Index <= index then
            return entry.Id
        end
    end
    return marketEggs[#marketEggs].Id
end

-- Where Roblox restricts paid random items (PolicyService: some countries treat paying for a random prize like gambling), the
-- jackpot's Exclusive Egg, an egg otherwise sold for Robux, is swapped for the largest stones prize (the owner, 2026-11-17).
function SpinRules.restricted(player)
    return player ~= nil and player:GetAttribute("RandomItemsRestricted") == true
end

-- What a segment gives a player of this rank, in words: Short for the wheel, Long for the message.
function SpinRules.describe(index, rankName, player)
    local segment = config.Segments[index]
    if not segment then
        return nil
    end
    local info = { Kind = segment.Kind, Index = index }
    if segment.Kind == "Stones" then
        info.Stones = SpinRules.stones(index, rankName, player)
        info.Short = NumberFormat.compact(info.Stones) .. " STONES"
        info.Long = NumberFormat.compact(info.Stones) .. " Spirit Stones"
        info.Icon = "Stones"
    elseif segment.Kind == "Qi" then
        info.Minutes = segment.Minutes
        info.Short = segment.Minutes .. " MIN QI"
        info.Long = segment.Minutes .. " minutes of Qi"
        info.Icon = "Qi"
    elseif segment.Kind == "Egg" then
        info.EggId = SpinRules.bestEgg(rankName)
        local egg = GameConfig.Eggs[info.EggId]
        info.Short = "EGG"
        info.Long = (if string.find(egg.DisplayName, "^[AEIOUaeiou]") then "an " else "a ") .. egg.DisplayName
        info.Icon = "Egg"
    elseif segment.Kind == "Spin" then
        info.Short = "EXTRA SPIN"
        info.Long = "1 more spin"
        info.Icon = "Spin"
    elseif segment.Kind == "Jackpot" and SpinRules.restricted(player) then
        info.Kind = "Stones"
        info.Stones = SpinRules.fallbackStones(rankName, player)
        info.Short = NumberFormat.compact(info.Stones) .. " STONES"
        info.Long = NumberFormat.compact(info.Stones) .. " Spirit Stones"
        info.Icon = "Stones"
    elseif segment.Kind == "Jackpot" then
        info.EggId = GameConfig.ExclusiveEgg.EggId
        info.Short = "JACKPOT"
        info.Long = "an Exclusive Egg"
        info.Icon = "Egg"
    end
    info.Chance = segment.Weight / totalWeight
    return info
end

function SpinRules.angleOf(index)
    return (index - 1) * SpinRules.Step
end

return SpinRules
