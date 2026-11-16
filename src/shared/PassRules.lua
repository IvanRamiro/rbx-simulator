-- The Store's game passes (GameConfig.GamePasses) and what owning each one does, shared so the server's effects and the
-- client's windows never disagree. The server alone decides who owns what (server/Shop/GamePassService) and sets the
-- player's "Pass_<Id>" attributes; everything here only reads them.
--
--   PassRules.List / PassRules.ById    the passes, in the Store's order
--   PassRules.owns(player, id)         whether they own it
--   PassRules.ForSale                  the passes the Store shows and sells (all but the Retired ones)
--   PassRules.qiTier(player)           the highest Qi pass tier they own (2, 4; 1 with none), never over GameConfig.MaxQiTier: tiers
--                                      never stack, and a Retired 8x or 16x pass counts as the cap
--   PassRules.qiMultiplier(player, withoutTimed)  their Qi pass tier times every other pass's Qi multiplier (VIP's +10%) times the
--                                      timed boost while it runs (withoutTimed leaves it out); 1 with none
--   PassRules.boostSecondsLeft(player), boostMultiplier(player)   the timed boost: seconds left, and its multiplier now (1 when off)
--   PassRules.luck(player)             how many times likelier their rare hatches are (1 with no luck)
--   PassRules.maxEquipped(player)      how many beasts they can equip; PassRules.MostEquipped: the most anyone can
--   PassRules.dailyStones(player, n)   a daily reward's Spirit Stones with their passes' bonus
--   PassRules.luckyPool(pool, luck)    an egg's pool with luck applied: a new list of { PetId, HatchChance }, adding to 100
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local PassRules = {}

PassRules.List = GameConfig.GamePasses
PassRules.ById = {}
PassRules.ForSale = {}
local extraSlots = 0
for _, pass in PassRules.List do
    PassRules.ById[pass.Id] = pass
    extraSlots += pass.ExtraSlots or 0
    if not pass.Retired then
        table.insert(PassRules.ForSale, pass)
    end
end
PassRules.MostEquipped = GameConfig.MaxEquippedPets + extraSlots

PassRules.RarityOrder = { Common = 1, Uncommon = 2, Rare = 3, Epic = 4, Legendary = 5, Mythical = 6, Secret = 7, Divine = 8 }

function PassRules.owns(player, id)
    return player ~= nil and player:GetAttribute("Pass_" .. id) == true
end

local function product(player, field, default)
    local value = default
    for _, pass in PassRules.List do
        if pass[field] and PassRules.owns(player, pass.Id) then
            value *= pass[field]
        end
    end
    return value
end

-- (a tier over GameConfig.MaxQiTier, a Retired pass's, counts as the cap)
function PassRules.qiTier(player)
    local tier = 1
    for _, pass in PassRules.List do
        if pass.QiTier and PassRules.owns(player, pass.Id) then
            tier = math.max(tier, math.min(pass.QiTier, GameConfig.MaxQiTier or math.huge))
        end
    end
    return tier
end

-- The timed boost (GameConfig.TimedBoost): running while the player's "QiBoostEnds" attribute, a server time set by server/Shop/QiBoost,
-- is still ahead. Its clock only runs while they're in the game: QiBoost saves the seconds left and sets a new end when they rejoin.
function PassRules.boostEnds(player)
    local ends = player and player:GetAttribute("QiBoostEnds")
    return if typeof(ends) == "number" then ends else 0
end

function PassRules.boostSecondsLeft(player)
    return math.max(0, PassRules.boostEnds(player) - workspace:GetServerTimeNow())
end

function PassRules.boostMultiplier(player)
    return if PassRules.boostSecondsLeft(player) > 0 then GameConfig.TimedBoost.Multiplier else 1
end

-- withoutTimed: leave the timed boost out (offline Qi: its clock doesn't run while the player is away)
function PassRules.qiMultiplier(player, withoutTimed)
    return PassRules.qiTier(player) * product(player, "QiMultiplier", 1) * (if withoutTimed then 1 else PassRules.boostMultiplier(player))
end

function PassRules.luck(player)
    return product(player, "Luck", 1)
end

function PassRules.maxEquipped(player)
    local slots = GameConfig.MaxEquippedPets
    for _, pass in PassRules.List do
        if pass.ExtraSlots and PassRules.owns(player, pass.Id) then
            slots += pass.ExtraSlots
        end
    end
    return slots
end

function PassRules.dailyStones(player, stones)
    return math.floor(stones * product(player, "DailyStones", 1) + 0.5)
end

function PassRules.luckyPool(pool, luck)
    local out = {}
    for _, entry in pool do
        table.insert(out, { PetId = entry.PetId, HatchChance = entry.HatchChance })
    end
    if not luck or luck <= 1 then
        return out
    end
    local function rank(entry)
        local pet = GameConfig.Pets[entry.PetId]
        return PassRules.RarityOrder[pet and pet.Rarity] or 1
    end
    -- lucky: every beast of Rare or rarer that is also rarer than the egg's commonest beasts (in an egg of Legendaries, only its
    -- Mythicals and Secrets); the rest give up what they gain, each in proportion
    local lowest = math.huge
    for _, entry in out do
        lowest = math.min(lowest, rank(entry))
    end
    local threshold = math.max(lowest + 1, PassRules.RarityOrder.Rare)
    local common, rare = 0, 0
    for _, entry in out do
        if rank(entry) >= threshold then
            rare += entry.HatchChance
        else
            common += entry.HatchChance
        end
    end
    if rare <= 0 or common <= 0 then
        return out -- nothing rarer to be lucky about
    end
    -- the rarer beasts luck times likelier, unless that would leave the rest less than the floor: then as much as fits
    local boost = math.max(1, math.min(luck, (100 - GameConfig.LuckFloor) / rare))
    local commonScale = (100 - rare * boost) / common
    for _, entry in out do
        entry.HatchChance *= if rank(entry) >= threshold then boost else commonScale
    end
    return out
end

return PassRules
