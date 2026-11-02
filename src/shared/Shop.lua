-- What the Blacksmith sells and what Buy & Sell pays, from GameConfig.WeaponKinds, WeaponTiers and
-- SpiritStones. Shared, so the server's checks and the client's windows never disagree on a price.
--
--   Shop.weapons              every weapon, by tier then kind: { Id, Kind, Tier, Name, Realm, Price, Damage }
--   Shop.weapon(id)           one of them, or nil
--   Shop.realmIndex(realm)    a realm's place in the ranks (1 = Qi Awakening), or nil
--   Shop.playerRealmIndex(player)
--   Shop.weaponRefund(id, element)  what a weapon sells back for (a forged one returns part of its forging too)
--   Shop.forgePrice(id)       what forging a weapon with an element costs (GameConfig.Forge)
--   Shop.element(name)        an element's GameConfig.Forge entry, or nil
--   Shop.petValue(petId)      what a pet sells for
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

Shop.weapons = {}
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
        table.insert(Shop.weapons, weapon)
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

-- a pet's egg realm: the earliest realm whose egg can hatch it
local petRealm = {}
for _, egg in GameConfig.Eggs do
    local rank = Ranks.getRankById(egg.RequiredRank)
    local realm = rank and Shop.realmIndex(rank.Realm) or 1
    for _, entry in egg.Pool do
        petRealm[entry.PetId] = math.min(petRealm[entry.PetId] or realm, realm)
    end
end

function Shop.petValue(petId)
    local pet = GameConfig.Pets[petId]
    if not pet then
        return 0
    end
    local rules = GameConfig.SpiritStones
    return math.floor((rules.PetValue[pet.Rarity] or 0) * rules.RealmFactor ^ ((petRealm[petId] or 1) - 1))
end

return Shop
