-- What the Blacksmith sells and what Buy & Sell pays, from GameConfig.WeaponKinds, WeaponTiers and
-- SpiritStones. Shared, so the server's checks and the client's windows never disagree on a price.
--
--   Shop.weapon(id)           a weapon ("Sword<tier>" or "Spear<tier>"): { Id, Kind, Tier, Name, Realm, Price, Damage }, or nil
--   Shop.realmIndex(realm)    a realm's place in the ranks (1 = Qi Awakening), or nil
--   Shop.playerRealmIndex(player)
--   Shop.weaponRefund(id, element)  what a weapon sells back for (a forged one returns part of its forging too)
--   Shop.forgePrice(id)       what forging a weapon with an element costs (GameConfig.Forge)
--   Shop.element(name)        an element's GameConfig.Forge entry, or nil
--   Shop.petValue(petId, level)  what a pet sells for: a fused pet is worth every copy it took in
--   Shop.petEggRank(petId)    the rank of the earliest egg that hatches it (what a player needs to hatch it), or nil
--   Shop.rankValue(rankId)    the rewards' ladder: a weapon's price at its realm's first rank, between
--   Shop.eggStones(eggId)     what securing this egg pays
--   Shop.marketEggPrice(eggId)  what the Marketplace asks for this egg
--   Shop.relicStones(relic)   what a relic's first attunement pays
--   Shop.roundNice(n)         two significant figures (a price worth reading)
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))

local Shop = {}

local realms = {}
for _, rank in GameConfig.Ranks do
    if not table.find(realms, rank.Realm) then
        table.insert(realms, rank.Realm)
    end
end

function Shop.realmIndex(realm)
    return table.find(realms, realm)
end

function Shop.playerRealmIndex(player)
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    return rank and Shop.realmIndex(rank.Realm) or 1
end

local byId = {}
for tier, info in GameConfig.WeaponTiers do
    assert(Shop.realmIndex(info.Realm) == tier, "WeaponTiers[" .. tier .. "] is not the realm in that place: " .. info.Realm)
    for _, kind in { "Sword", "Spear" } do
        local weapon = {
            Id = kind .. tier,
            Kind = kind,
            Tier = tier,
            Name = info[kind],
            Realm = info.Realm,
            Price = info.Price,
            Damage = info.Damage * GameConfig.WeaponKinds[kind].DamageScale,
        }
        byId[weapon.Id] = weapon
    end
end

function Shop.weapon(id)
    return if typeof(id) == "string" then byId[id] else nil
end

function Shop.forgePrice(id)
    local weapon = byId[id]
    local forge = GameConfig.Forge
    return weapon and math.max(forge.MinPrice, math.floor(weapon.Price * forge.PriceShare)) or 0
end

function Shop.element(name)
    return if typeof(name) == "string" then GameConfig.Forge.Elements[name] else nil
end

function Shop.weaponRefund(id, element)
    local weapon = byId[id]
    if not weapon then
        return 0
    end
    local paid = weapon.Price + (if Shop.element(element) then Shop.forgePrice(id) else 0)
    return math.floor(paid * GameConfig.SpiritStones.WeaponRefund)
end

-- a pet's egg realm: the earliest realm whose egg can hatch it; and that earliest egg's required rank
local petRealm = {}
local petRank = {} -- [petId] = { Id, Index }
for _, egg in GameConfig.Eggs do
    local rank = Ranks.getRankById(egg.RequiredRank)
    local realm = rank and Shop.realmIndex(rank.Realm) or 1
    local index = rank and Ranks.getIndex(rank.Name) or 1
    for _, entry in egg.Pool do
        petRealm[entry.PetId] = math.min(petRealm[entry.PetId] or realm, realm)
        if not petRank[entry.PetId] or index < petRank[entry.PetId].Index then
            petRank[entry.PetId] = { Id = egg.RequiredRank, Index = index }
        end
    end
end

-- the rank a player needs to hatch this pet from any egg (the earliest egg whose pool holds it), or nil if none can
function Shop.petEggRank(petId)
    local entry = petRank[petId]
    return entry and entry.Id
end

function Shop.petValue(petId, level)
    local pet = GameConfig.Pets[petId]
    if not pet then
        return 0
    end
    local rules = GameConfig.SpiritStones
    -- (a pet's ValueRealm, when set, replaces its egg's realm)
    return math.floor((rules.PetValue[pet.Rarity] or 0) * rules.RealmFactor ^ ((pet.ValueRealm or petRealm[petId] or 1) - 1)) * (level or 1)
end

function Shop.roundNice(n)
    if n < 100 then
        return math.max(1, math.floor(n + 0.5))
    end
    local unit = 10 ^ (math.floor(math.log10(n)) - 1)
    return math.floor(n / unit + 0.5) * unit
end

-- rises by the realm's price step over each realm's ranks, so rewards keep pace with prices
local RANKS_PER_REALM = #GameConfig.Ranks / #realms
function Shop.rankValue(rankId)
    local rank = Ranks.getRankById(rankId)
    local index = rank and Ranks.getIndex(rank.Name) or 1
    return GameConfig.WeaponTiers[1].Price * GameConfig.SpiritStones.RealmFactor ^ ((index - 1) / RANKS_PER_REALM)
end

function Shop.marketEggPrice(eggId)
    local egg = GameConfig.Eggs[eggId]
    return if egg then Shop.roundNice(Shop.rankValue(egg.RequiredRank) * GameConfig.SpiritStones.MarketEggShare) else 0
end

function Shop.eggStones(eggId)
    local egg = GameConfig.Eggs[eggId]
    local rules = GameConfig.SpiritStones
    if not egg then
        return 0
    end
    local rank = Ranks.getRankById(egg.RequiredRank)
    local realm = rank and Shop.realmIndex(rank.Realm) or 1
    local share = rules.EggShare * (rules.EggShareFalloff or 1) ^ (realm - 1)
    return Shop.roundNice(math.max(rules.MinReward, Shop.rankValue(egg.RequiredRank) * share))
end

function Shop.relicStones(relic)
    local rules = GameConfig.SpiritStones
    return Shop.roundNice(math.max(rules.MinReward, Shop.rankValue(relic.RequiredRank) * rules.RelicShare))
end

return Shop
