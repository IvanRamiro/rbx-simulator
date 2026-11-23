-- AuctionRules (fees, caps, minimum bids), Merchant (the hourly timetable and each visit's deals) and Shop.roundNice.
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local AuctionRules = require("@shared/AuctionRules")
local Merchant = require("@shared/Merchant")
local Ranks = require("@shared/Ranks")
local Shop = require("@shared/Shop")

local A = GameConfig.AuctionHouse
local M = GameConfig.WanderingMerchant
local pet = { PetId = "VoltFox" }

-- ---------- the Auction House ----------
t.test("fees: the listing fee has a floor, the sale tax rounds down", function()
    t.eq(AuctionRules.listingFee(1), A.ListingFee.Min, "a tiny listing still pays the least fee")
    t.ok(AuctionRules.listingFee(1000000) >= A.ListingFee.Min)
    t.eq(AuctionRules.listingFee(1000000), math.floor(1000000 * A.ListingFee.Share + 0.5))
    t.eq(AuctionRules.saleTax(1000), math.floor(1000 * A.SaleTax))
    t.eq(AuctionRules.saleTax(0), 0)
    t.ok(AuctionRules.saleTax(777) <= 777 * A.SaleTax, "tax never rounds up")
end)

t.test("bids: the next bid is the high bid plus the minimum raise, never less than 1 above", function()
    t.eq(AuctionRules.minRaise(0), 1)
    t.eq(AuctionRules.minRaise(10), math.max(1, math.ceil(10 * A.MinRaise)))
    t.eq(AuctionRules.minBid({ StartBid = 50 }), 50, "no bid yet: the start bid")
    t.eq(AuctionRules.minBid({ StartBid = 50, High = { Amount = 200 } }), 200 + AuctionRules.minRaise(200))
    for amount = 1, 400, 7 do
        t.ok(AuctionRules.minBid({ StartBid = 1, High = { Amount = amount } }) > amount, "a raise is always a raise")
    end
end)

t.test("durations and whole numbers of stones are validated", function()
    for _, hours in A.Hours do
        t.ok(AuctionRules.isDuration(hours))
    end
    t.falsy(AuctionRules.isDuration(0))
    t.falsy(AuctionRules.isDuration("12"))
    t.falsy(AuctionRules.isDuration(nil))
    t.falsy(AuctionRules.isDuration(A.Hours[1] + 0.5))
    t.eq(AuctionRules.whole(5), 5)
    t.eq(AuctionRules.whole(1), 1)
    t.eq(AuctionRules.whole(GameConfig.SpiritStones.Max), GameConfig.SpiritStones.Max)
    for _, bad in { 0, -3, 1.5, 0 / 0, math.huge, GameConfig.SpiritStones.Max + 1, "7", true } do
        t.eq(AuctionRules.whole(bad), nil, "whole(" .. tostring(bad) .. ")")
    end
end)

t.test("rarity ranks follow the ladder", function()
    t.eq(AuctionRules.rarityRank("Common"), 1)
    t.eq(AuctionRules.rarityRank("Divine"), #AuctionRules.Rarities)
    t.eq(AuctionRules.rarityRank("Nonsense"), 0)
    for i = 2, #AuctionRules.Rarities do
        t.ok(AuctionRules.rarityRank(AuctionRules.Rarities[i]) > AuctionRules.rarityRank(AuctionRules.Rarities[i - 1]))
    end
end)

t.test("start range and price cap: floor at least 1, floor <= ceiling <= cap, a rarer or bigger pet caps higher", function()
    local low, high = AuctionRules.startRange("Pet", pet)
    t.ok(low >= 1 and low <= high, "start range")
    t.ok(high <= AuctionRules.priceCap("Pet", pet))
    t.ok(AuctionRules.priceCap("Pet", pet) >= 10, "a cap is at least 10")
    local giant = { PetId = "VoltFox", Size = "Giant", Mutation = "Void" }
    t.ok(AuctionRules.priceCap("Pet", giant) > AuctionRules.priceCap("Pet", pet), "a Giant Void caps above a plain one")
    t.eq(AuctionRules.value("Pet", nil), 0)
    t.eq(AuctionRules.value("Nothing", {}), 0)
    t.eq(AuctionRules.rarity("Pet", { PetId = "NoSuchPet" }), "Common", "an unknown pet is Common")
    t.eq(AuctionRules.rarity("Weapon", {}), "Weapon")
end)

t.test("paid (Robux) pets are the Exclusive egg's, wherever the copy came from", function()
    local exclusiveEgg = GameConfig.Eggs[GameConfig.ExclusiveEgg.EggId]
    t.ok(exclusiveEgg ~= nil)
    for _, entry in exclusiveEgg.Pool do
        t.ok(AuctionRules.isPaidPet(entry.PetId), entry.PetId .. " should be a paid pet")
        t.ok(AuctionRules.isPaid("Pet", { PetId = entry.PetId }))
    end
    t.falsy(AuctionRules.isPaidPet("VoltFox"))
    t.ok(AuctionRules.isPaid("Pet", { PetId = "VoltFox", Paid = true }), "a record flagged Paid is paid")
    t.falsy(AuctionRules.isPaid("Weapon", { PetId = exclusiveEgg.Pool[1].PetId }), "only pets can be paid items")
end)

t.test("who may trade: the minimum rank and account age (live servers only)", function()
    local minRank = Ranks.getRankById(A.MinRank)
    local below = Ranks.getRank(GameConfig.Ranks[Ranks.getIndex(minRank.Name) - 1].Name)
    local ok1 = AuctionRules.canUse(below.Name, 1000)
    t.falsy(ok1, "a rank below the minimum may not trade")
    local ok2, why = AuctionRules.canUse(minRank.Name, A.MinAccountAgeDays - 1)
    t.falsy(ok2, "too young an account")
    t.ok(type(why) == "string" and #why > 0, "refusals say why")
    t.ok(AuctionRules.canUse(minRank.Name, A.MinAccountAgeDays))
    t.ok(AuctionRules.canUse(minRank.Name, nil), "an unknown age is not checked here")
end)

-- ---------- the Wandering Merchant ----------
t.test("the timetable: he comes every hour and stays ten minutes", function()
    t.ok(M.Stay < M.Every)
    t.eq(Merchant.visitIndex(0), 0)
    t.eq(Merchant.visitIndex(M.Every - 1), 0)
    t.eq(Merchant.visitIndex(M.Every * 3 + 5), 3)
    t.ok(Merchant.isOpen(0))
    t.ok(Merchant.isOpen(M.Stay - 1))
    t.falsy(Merchant.isOpen(M.Stay))
    t.falsy(Merchant.isOpen(M.Every - 1))
    t.ok(Merchant.isOpen(M.Every), "the next visit opens on the hour")
    t.eq(Merchant.leavesAt(0), M.Stay)
    t.eq(Merchant.leavesAt(M.Every * 2 + 30), M.Every * 2 + M.Stay)
    t.eq(Merchant.nextArrival(0), M.Every)
    t.eq(Merchant.nextArrival(M.Every + 1), M.Every * 2)
    t.eq(Merchant.isOpen(M.Every * 7.5 + 0.9), Merchant.isOpen(math.floor(M.Every * 7.5)), "fractions of a second do not matter")
end)

t.test("every visit has 3 or 4 different deals, the same each time it is asked, and one a brand-new player can buy", function()
    local firstRank = GameConfig.Ranks[1].Id
    for visit = 1, 300 do
        local deals = Merchant.dealsFor(visit)
        t.ok(#deals >= M.Deals.Min and #deals <= M.Deals.Max, "visit " .. visit .. " has " .. #deals .. " deals")
        local seen, beginner = {}, false
        for _, deal in deals do
            t.falsy(seen[deal.Id], "visit " .. visit .. " offers " .. tostring(deal.Id) .. " twice")
            seen[deal.Id] = true
            t.ok(Merchant.isOffered(visit, deal.Id))
            beginner = beginner or deal.RequiredRank == firstRank
        end
        t.ok(beginner, "visit " .. visit .. " has nothing a new player can buy")
        local again = Merchant.dealsFor(visit)
        t.eq(#again, #deals)
        for i, deal in deals do
            t.eq(again[i].Id, deal.Id)
        end
    end
end)

-- ---------- Shop.roundNice ----------
t.test("roundNice keeps two significant figures (and at least 1)", function()
    local cases = { { 0.2, 1 }, { 0, 1 }, { 7.4, 7 }, { 7.5, 8 }, { 99.4, 99 }, { 100, 100 }, { 1234, 1200 }, { 1250, 1300 }, { 98765, 99000 }, { 999999, 1000000 } }
    for _, case in cases do
        t.eq(Shop.roundNice(case[1]), case[2], "roundNice(" .. case[1] .. ")")
    end
end)

t.finish("market")
