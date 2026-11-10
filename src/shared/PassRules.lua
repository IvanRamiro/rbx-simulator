-- The Store's game passes (GameConfig.GamePasses) and what owning each one does, shared so the server's effects and the
-- client's windows never disagree. The server alone decides who owns what (server/Shop/GamePassService) and sets the
-- player's "Pass_<Id>" attributes; everything here only reads them.
--
--   PassRules.List / PassRules.ById    the passes, in the Store's order
--   PassRules.owns(player, id)         whether they own it
--   PassRules.qiMultiplier(player)     every pass's Qi multiplier, multiplied together (1 with none)
--   PassRules.luck(player)             how many times likelier their rare hatches are (1 with no luck)
--   PassRules.maxEquipped(player)      how many beasts they can equip; PassRules.MostEquipped: the most anyone can
--   PassRules.dailyStones(player, n)   a daily reward's Spirit Stones with their passes' bonus
--   PassRules.luckyPool(pool, luck)    an egg's pool with luck applied: a new list of { PetId, HatchChance }, adding to 100
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local PassRules = {}

PassRules.List = GameConfig.GamePasses
PassRules.ById = {}
local extraSlots = 0
for _, pass in PassRules.List do
    PassRules.ById[pass.Id] = pass
    extraSlots += pass.ExtraSlots or 0
end
PassRules.MostEquipped = GameConfig.MaxEquippedPets + extraSlots

PassRules.RarityOrder = { Common = 1, Uncommon = 2, Rare = 3, Epic = 4, Legendary = 5, Mythical = 6, Secret = 7 }

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

function PassRules.qiMultiplier(player)
    return product(player, "QiMultiplier", 1)
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
