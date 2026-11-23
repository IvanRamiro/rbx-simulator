-- Data integrity of GameConfig and the tables built from it: the checks that used to be done by hand before a release (egg pools add up,
-- every pet has lore, every faction is complete). A failure here means a config edit left the game inconsistent.
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local Ranks = require("@shared/Ranks")
local Shop = require("@shared/Shop")
local CodexRules = require("@shared/CodexRules")
local PetLore = require("@shared/PetLore")
local PetMaps = require("@shared/PetMaps")
local WeaponMaps = require("@shared/WeaponMaps")
local AuctionRules = require("@shared/AuctionRules")
local FactionRules = require("@shared/FactionRules")

local function count(map)
    local n = 0
    for _ in map do
        n += 1
    end
    return n
end

-- ---------- eggs and pets ----------
t.test("every egg's pool adds up to 100 percent", function()
    for eggId, egg in GameConfig.Eggs do
        local total = 0
        for _, entry in egg.Pool do
            t.ok(entry.HatchChance > 0, eggId .. " has a pet with no chance")
            total += entry.HatchChance
        end
        t.near(total, 100, 1e-6, eggId .. " pool total")
    end
end)

t.test("every egg's pets exist, and its required rank is a rank", function()
    for eggId, egg in GameConfig.Eggs do
        t.ok(#egg.Pool > 0, eggId .. " hatches nothing")
        t.ok(Ranks.getRankById(egg.RequiredRank) ~= nil, eggId .. " requires an unknown rank " .. tostring(egg.RequiredRank))
        local seen = {}
        for _, entry in egg.Pool do
            t.ok(GameConfig.Pets[entry.PetId] ~= nil, eggId .. " hatches an unknown pet " .. tostring(entry.PetId))
            t.falsy(seen[entry.PetId], eggId .. " lists " .. entry.PetId .. " twice")
            seen[entry.PetId] = true
        end
    end
end)

t.test("every pet can be had: hatched, a starter, a creator's or a dev test pet", function()
    local reachable = {}
    for _, egg in GameConfig.Eggs do
        for _, entry in egg.Pool do
            reachable[entry.PetId] = true
        end
    end
    for _, list in { GameConfig.StarterPetIds, GameConfig.DevTestPetIds, GameConfig.CreatorPets.PetIds } do
        for _, id in list do
            t.ok(GameConfig.Pets[id] ~= nil, "a pet list names an unknown pet " .. tostring(id))
            reachable[id] = true
        end
    end
    for petId in GameConfig.Pets do
        t.ok(reachable[petId], petId .. " is in Pets but no egg hatches it and no list grants it")
    end
end)

t.test("every pet has a known rarity, a positive Qi bonus and a name", function()
    for petId, pet in GameConfig.Pets do
        t.ok(GameConfig.PetRarityColors[pet.Rarity] ~= nil, petId .. " has an unknown rarity " .. tostring(pet.Rarity))
        t.ok(table.find(AuctionRules.Rarities, pet.Rarity) ~= nil, petId .. "'s rarity is missing from the Auction House's list")
        t.ok(type(pet.QiBonus) == "number" and pet.QiBonus > 0, petId .. " QiBonus")
        t.ok(type(pet.DisplayName) == "string" and #pet.DisplayName > 0, petId .. " DisplayName")
    end
end)

t.test("every hatchable pet has lore, and the texture map table names only real pets", function()
    for _, petId in CodexRules.Pets do
        t.ok(PetLore[petId] ~= nil, petId .. " has no lore")
    end
    for petId in PetMaps do
        t.ok(GameConfig.Pets[petId] ~= nil, "PetMaps names an unknown pet " .. petId)
    end
    for petId in PetLore do
        t.ok(GameConfig.Pets[petId] ~= nil, "PetLore names an unknown pet " .. petId)
    end
end)

t.test("the Codex counts exactly the beasts the eggs can hatch", function()
    local hatchable = {}
    for _, egg in GameConfig.Eggs do
        for _, entry in egg.Pool do
            hatchable[entry.PetId] = true
        end
    end
    t.eq(CodexRules.Total, count(hatchable))
    t.eq(#CodexRules.Pets, CodexRules.Total)
end)

-- ---------- guardians ----------
t.test("a guardian guards real eggs, and no egg has two guardians", function()
    local guardedBy = {}
    for guardianId, guardian in GameConfig.Guardians do
        t.ok(#guardian.Eggs > 0, guardianId .. " guards nothing")
        for _, eggId in guardian.Eggs do
            t.ok(GameConfig.Eggs[eggId] ~= nil, guardianId .. " guards an unknown egg " .. tostring(eggId))
            t.falsy(guardedBy[eggId], eggId .. " is guarded by " .. tostring(guardedBy[eggId]) .. " and " .. guardianId)
            guardedBy[eggId] = guardianId
        end
        t.ok(guardian.MaxHealth > 0, guardianId .. " MaxHealth")
    end
end)

-- ---------- weapons ----------
t.test("twelve weapon tiers with prices and damage that rise", function()
    local tiers = GameConfig.WeaponTiers
    t.eq(#tiers, 12)
    for i = 2, #tiers do
        t.ok(tiers[i].Price > tiers[i - 1].Price, "tier " .. i .. " price")
        t.ok(tiers[i].Damage > tiers[i - 1].Damage, "tier " .. i .. " damage")
    end
end)

t.test("every weapon has its texture maps, and Shop knows every weapon", function()
    for i = 1, 12 do
        t.ok(WeaponMaps["Sword" .. i] ~= nil, "no maps for Sword" .. i)
        t.ok(WeaponMaps["Spear" .. i] ~= nil, "no maps for Spear" .. i)
        t.ok(Shop.weapon("Sword" .. i) ~= nil, "Shop does not know Sword" .. i)
        t.ok(Shop.weapon("Spear" .. i) ~= nil, "Shop does not know Spear" .. i)
    end
    for weaponId in WeaponMaps do
        t.ok(Shop.weapon(weaponId) ~= nil, "WeaponMaps has maps for a weapon Shop does not know: " .. weaponId)
    end
end)

-- ---------- factions ----------
t.test("three factions, each complete", function()
    local factions = GameConfig.Faction.Factions
    t.eq(count(factions), 3)
    t.eq(#GameConfig.Faction.Order, 3)
    t.eq(#FactionRules.Order, 3)
    local hqs, weapons = {}, {}
    for _, id in GameConfig.Faction.Order do
        local f = factions[id]
        t.ok(f ~= nil, "Faction.Order names " .. id .. " but it is not defined")
        t.ok(FactionRules.isFaction(id))
        for _, field in { "DisplayName", "Short", "Hq", "Master", "Motto", "OutfitId", "TitleId" } do
            t.ok(type(f[field]) == "string" and #f[field] > 0, id .. "." .. field)
        end
        t.ok(f.Color ~= nil and f.Deep ~= nil, id .. " colours")
        t.ok(f.Trial and #f.Trial.Name > 0 and #f.Trial.Text > 0, id .. " trial")
        t.eq(#f.Pages, 3, id .. " pages")
        for _, page in f.Pages do
            t.ok(#page.Title > 0 and #page.Text > 0, id .. " has an empty page")
        end
        t.falsy(hqs[f.Hq], "two factions share a headquarters name")
        hqs[f.Hq] = true
        -- the secret weapon: bound, registered, mapped, and belonging to this faction only
        t.ok(f.Weapon and f.Weapon.Id and #f.Weapon.Name > 0, id .. " weapon")
        t.falsy(weapons[f.Weapon.Id], "two factions share a weapon")
        weapons[f.Weapon.Id] = true
        t.ok(Shop.weapon(f.Weapon.Id) ~= nil, f.Weapon.Id .. " is not registered in Shop")
        t.ok(Shop.isBound(f.Weapon.Id), f.Weapon.Id .. " must be bound (never sold, forged or auctioned)")
        t.ok(WeaponMaps[f.Weapon.Id] ~= nil, f.Weapon.Id .. " has no texture maps")
        t.eq(FactionRules.weaponFaction(f.Weapon.Id), id)
        t.eq(GameConfig.Outfits[f.OutfitId].Faction, id, id .. "'s outfit belongs to another faction")
    end
end)

-- ---------- rewards, wheel, auction, merchant ----------
t.test("the daily reward is a full week of paying days", function()
    local days = GameConfig.Rewards.Daily
    t.eq(#days, 7)
    for i, day in days do
        t.ok(day.Stones > 0, "day " .. i .. " pays no stones")
    end
end)

t.test("the spin wheel has weighted segments and spins to give", function()
    local wheel = GameConfig.SpinWheel
    t.ok(#wheel.Segments >= 2)
    t.ok(wheel.DailySpins >= 1)
    for i, segment in wheel.Segments do
        t.ok(segment.Weight > 0, "segment " .. i .. " weight")
    end
end)

t.test("the Auction House's durations, caps and fees make sense", function()
    local config = GameConfig.AuctionHouse
    t.ok(#config.Hours >= 1)
    for _, rarity in AuctionRules.Rarities do
        t.ok(config.PriceCap[rarity] ~= nil, "no price cap for " .. rarity)
    end
    t.ok(Ranks.getRankById(config.MinRank) ~= nil, "AuctionHouse.MinRank must be a rank id")
    t.ok(config.StartFloor > 0 and config.StartFloor < config.StartCeiling, "start floor below start ceiling")
    t.ok(config.SaleTax >= 0 and config.SaleTax < 1)
end)

t.test("developer test grants are off (they would hand every new Studio save free pets)", function()
    t.eq(GameConfig.GrantDevTestPets, false)
end)

t.test("a new player has not met the Guide: the quests and the tutorial wait for them to talk to her", function()
    t.eq(GameConfig.Settings.GuideMet, false, "GuideMet must start false")
    t.eq(GameConfig.Settings.TutorialDone, false)
    for key, default in GameConfig.Settings do
        t.ok(type(default) == "number" or type(default) == "boolean", "setting " .. key .. " has no usable default")
    end
end)

t.finish("config")
