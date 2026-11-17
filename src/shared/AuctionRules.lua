-- The Auction House's rules (GameConfig.AuctionHouse), shared so the server's checks and the client's window never disagree on a
-- fee, a floor or a raise. Items are tables: a pet { PetId, Level, Size, Mutation, Worth } or a weapon { WeaponId, Element, Name }.
--
--   AuctionRules.Config                     GameConfig.AuctionHouse
--   AuctionRules.isPaidPet(petId)           whether this kind of pet comes from a Robux egg (an Exclusive egg's pool): always paid
--   AuctionRules.isPaid(kind, item)         whether this item is a paid item: a pet marked Paid (hatched from a paid egg: EggInventory)
--                                           or of an Exclusive egg's kind (the rule for saves from before the mark); never a weapon
--   AuctionRules.value(kind, item)          its sell value (what Buy & Sell pays for it)
--   AuctionRules.rarity(kind, item)         a pet's rarity, or "Weapon"
--   AuctionRules.rarityRank(rarity)         1 (Common) .. 8 (Divine); a weapon 0: for sorting by rarity
--   AuctionRules.priceCap(kind, item)       the highest bid allowed (a big or mutated pet's is higher: SizeCap, PetRules.Mutations' Cap)
--   AuctionRules.startRange(kind, item)     the lowest and highest starting bid
--   AuctionRules.listingFee(startBid)       what listing costs (kept even if nothing sells)
--   AuctionRules.saleTax(price)             what is taken from the seller's price
--   AuctionRules.minRaise(current)          how much a bid must beat the top bid by
--   AuctionRules.minBid(listing)            the least the next bid may be ({ StartBid, High = { Amount } | nil })
--   AuctionRules.isDuration(hours)          one of the durations a seller can pick
--   AuctionRules.canUse(rankName, ageDays)  ok, or false and why (in plain words)
--   AuctionRules.canOwn(rankName, kind, item)  ok, or false and why: the bidder could hatch this pet or buy this weapon
--   AuctionRules.itemName(kind, item)       what to call it
--   AuctionRules.whole(n)                   n as a whole number of stones if it is one in range, else nil
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))

local CONFIG = GameConfig.AuctionHouse

local AuctionRules = {}
AuctionRules.Config = CONFIG

local RARITIES = { "Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythical", "Secret", "Divine" }
AuctionRules.Rarities = RARITIES

-- every kind of pet an Exclusive (Robux) egg can hatch is a paid item, wherever a copy came from (the save doesn't know)
local paidPets = {}
for _, egg in GameConfig.Eggs do
    if egg.Exclusive then
        for _, entry in egg.Pool do
            paidPets[entry.PetId] = true
        end
    end
end

function AuctionRules.isPaidPet(petId)
    return paidPets[petId] == true
end

function AuctionRules.isPaid(kind, item)
    return kind == "Pet" and typeof(item) == "table" and (item.Paid == true or AuctionRules.isPaidPet(item.PetId))
end

function AuctionRules.value(kind, item)
    if typeof(item) ~= "table" then
        return 0
    end
    if kind == "Pet" then
        return Shop.petValue(item.PetId, PetRules.worth(item))
    elseif kind == "Weapon" then
        return Shop.weaponRefund(item.WeaponId, item.Element)
    end
    return 0
end

function AuctionRules.rarity(kind, item)
    if kind == "Pet" then
        local pet = typeof(item) == "table" and GameConfig.Pets[item.PetId]
        return pet and pet.Rarity or "Common"
    end
    return "Weapon"
end

function AuctionRules.rarityRank(rarity)
    return table.find(RARITIES, rarity) or 0
end

-- (a Colossal or a Void is far rarer than its sell value says: its cap rises by its size's and its mutation's multiplier, 2026-11-17)
function AuctionRules.priceCap(kind, item)
    local multiple = CONFIG.PriceCap[AuctionRules.rarity(kind, item)] or CONFIG.PriceCap.Common
    if kind == "Pet" and typeof(item) == "table" then
        multiple *= (CONFIG.SizeCap[PetRules.size(item)] or 1) * PetRules.mutationInfo(item).Cap
    end
    return math.max(10, math.floor(AuctionRules.value(kind, item) * multiple))
end

function AuctionRules.startRange(kind, item)
    local value = math.max(1, AuctionRules.value(kind, item))
    local low = math.max(1, math.ceil(value * CONFIG.StartFloor))
    local high = math.min(AuctionRules.priceCap(kind, item), math.max(low, math.floor(value * CONFIG.StartCeiling)))
    return low, high
end

function AuctionRules.listingFee(startBid)
    return math.max(CONFIG.ListingFee.Min, math.floor(startBid * CONFIG.ListingFee.Share + 0.5))
end

function AuctionRules.saleTax(price)
    return math.floor(price * CONFIG.SaleTax)
end

function AuctionRules.minRaise(current)
    return math.max(1, math.ceil(current * CONFIG.MinRaise))
end

function AuctionRules.minBid(listing)
    if listing.High then
        return listing.High.Amount + AuctionRules.minRaise(listing.High.Amount)
    end
    return listing.StartBid
end

function AuctionRules.isDuration(hours)
    return typeof(hours) == "number" and table.find(CONFIG.Hours, hours) ~= nil
end

-- a whole number of stones, from 1 to the wallet's most
function AuctionRules.whole(n)
    if typeof(n) ~= "number" or n ~= n or n ~= math.floor(n) or n < 1 or n > GameConfig.SpiritStones.Max then
        return nil
    end
    return n
end

function AuctionRules.canUse(rankName, ageDays)
    if not Ranks.isAtLeast(rankName, CONFIG.MinRank) then
        return false, "Reach " .. Ranks.getRankById(CONFIG.MinRank).Name .. " to trade at the Auction House."
    end
    -- (not in Studio: a Local Server test's players are brand-new accounts, age 0; live servers always check it)
    if typeof(ageDays) == "number" and ageDays < CONFIG.MinAccountAgeDays and not RunService:IsStudio() then
        return false, "Your Roblox account must be " .. CONFIG.MinAccountAgeDays .. " days old to trade at the Auction House."
    end
    return true
end

-- the same rule as everywhere else: a pet the player's rank could hatch, a weapon of their realm or below
function AuctionRules.canOwn(rankName, kind, item)
    if kind == "Pet" then
        local need = Shop.petEggRank(item.PetId)
        if need and not Ranks.isAtLeast(rankName, need) then
            return false, "You need " .. Ranks.getRankById(need).Name .. " to own this pet."
        end
        return true
    end
    local weapon = Shop.weapon(item.WeaponId)
    local rank = Ranks.getRank(rankName)
    local realm = rank and Shop.realmIndex(rank.Realm) or 1
    if weapon and weapon.Tier > realm then
        return false, "Reach the " .. weapon.Realm .. " to use this weapon."
    end
    return true
end

function AuctionRules.itemName(kind, item)
    if kind == "Pet" then
        return if GameConfig.Pets[item.PetId] then PetRules.displayName(item.PetId, item.Mutation) else "Pet"
    end
    if typeof(item.Name) == "string" and item.Name ~= "" then
        return item.Name
    end
    local weapon = Shop.weapon(item.WeaponId)
    return weapon and weapon.Name or "Weapon"
end

return AuctionRules
