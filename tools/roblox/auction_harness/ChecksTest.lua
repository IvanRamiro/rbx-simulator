-- The Auction House's request checks (server/Auction/AuctionChecks, shared/AuctionRules) against the game's real config: who may
-- trade, what can go up, the paid-item rule, floors, caps and fees. Run in Studio (Edit is enough: nothing here touches a store):
-- require it as a ModuleScript and call it with the two live modules. Returns passed, failed, lines.
return function(AuctionChecks, AuctionRules, GameConfig)
    local passed, failed, lines = 0, 0, {}
    local function check(cond, what)
        if cond then
            passed += 1
        else
            failed += 1
            table.insert(lines, "FAIL: " .. what)
        end
    end
    local RANK_OK, RANK_LOW = "Core Initiate", "Qi Awakener"
    local function pet(petId, extra)
        local p = { InstanceId = "X", PetId = petId, Level = 1, Size = "Normal", Worth = 1, Locked = false, Equipped = false, InPen = false }
        for k, v in extra or {} do
            p[k] = v
        end
        return p
    end
    local function listFacts(extra)
        local f = { kind = "Pet", pet = pet("VoltFox"), petCount = 3, paidOk = true, rankName = RANK_OK, ageDays = 400,
            activeListings = 0, startBid = nil, hours = 4, stones = 10000 }
        for k, v in extra or {} do
            f[k] = v
        end
        if f.startBid == nil then
            f.startBid = (AuctionRules.startRange(f.kind, if f.kind == "Pet" then f.pet else f.weapon))
        end
        return f
    end

    -- the paid items: exactly the Exclusive Egg's beasts
    for _, petId in { "NineTailMoonfox", "Crysalith", "EclipseDreadwing" } do
        check(AuctionRules.isPaidPet(petId), petId .. " is a paid item")
    end
    check(not AuctionRules.isPaidPet("VoltFox"), "an egg-stand beast is not a paid item")
    check(AuctionRules.isPaid("Pet", pet("VoltFox", { Paid = true })), "a pet marked Paid (from a paid egg) is a paid item")
    check(not AuctionRules.isPaid("Pet", pet("VoltFox")), "an unmarked egg-stand beast is not")
    local okPaid, whyPaid = AuctionChecks.list(listFacts({ pet = pet("VoltFox", { Paid = true }), paidOk = false }))
    check(not okPaid and string.find(whyPaid, "Robux") ~= nil, "POLICY: a pet from a bought spin's egg can't be listed where paid trading isn't allowed")
    check(AuctionChecks.list(listFacts({ pet = pet("VoltFox", { Paid = true }), paidOk = true })) == true, "POLICY: allowed elsewhere")
    check(AuctionChecks.list(listFacts({ pet = pet("VoltFox"), paidOk = false })) == true, "an unpaid pet trades everywhere")
    check(not AuctionRules.isPaid("Weapon", { WeaponId = "Sword1" }), "weapons are never paid items")

    -- who may trade
    check(AuctionChecks.list(listFacts()) == true, "a free Epic pet can be listed")
    local ok, why = AuctionChecks.list(listFacts({ rankName = RANK_LOW }))
    check(not ok and string.find(why, "Core Initiate") ~= nil, "below Core Initiate: refused (" .. tostring(why) .. ")")
    ok, why = AuctionChecks.list(listFacts({ ageDays = 1 }))
    if game:GetService("RunService"):IsStudio() then
        check(ok, "a 1-day-old account: allowed in Studio only (Local Server test players are age 0)")
    else
        check(not ok and string.find(why, "days old") ~= nil, "a 1-day-old account: refused")
    end

    -- what can go up
    for flag, word in { Locked = "Unlock", Equipped = "Unequip", InPen = "pen" } do
        ok, why = AuctionChecks.list(listFacts({ pet = pet("VoltFox", { [flag] = true }) }))
        check(not ok and string.find(why, word) ~= nil, flag .. " pet refused (" .. tostring(why) .. ")")
    end
    ok, why = AuctionChecks.list(listFacts({ petCount = 1 }))
    check(not ok and string.find(why, "last pet") ~= nil, "the last pet refused")
    ok, why = AuctionChecks.list(listFacts({ isCreatorPet = true }))
    check(not ok and string.find(why, "comes back") ~= nil, "a creator's always-held pet refused")
    ok, why = AuctionChecks.list(listFacts({ pet = pet("NineTailMoonfox"), paidOk = false }))
    check(not ok and string.find(why, "Exclusive Egg") ~= nil, "POLICY: an Exclusive Egg beast (old save, no mark) can't be listed where trading paid items isn't allowed")
    check(AuctionChecks.list(listFacts({ pet = pet("NineTailMoonfox"), paidOk = true })) == true, "POLICY: allowed elsewhere")
    ok, why = AuctionChecks.list(listFacts({ kind = "Weapon", pet = nil, weapon = { InstanceId = "W1", WeaponId = "Sword1" }, equippedWeapon = "W1" }))
    check(not ok and string.find(why, "Unequip") ~= nil, "the equipped weapon refused")
    check(AuctionChecks.list(listFacts({ kind = "Weapon", pet = nil, weapon = { InstanceId = "W2", WeaponId = "Sword1" }, equippedWeapon = "W1" })) == true,
        "a spare weapon can be listed")
    ok, why = AuctionChecks.list(listFacts({ kind = "Weapon", pet = nil, weapon = nil }))
    check(not ok, "no weapon at all (a Qi Palm player): refused, nothing breaks")
    ok, why = AuctionChecks.list(listFacts({ activeListings = GameConfig.AuctionHouse.MaxListings }))
    check(not ok and string.find(why, "at once") ~= nil, "the listings cap")
    ok, why = AuctionChecks.list(listFacts({ hours = 3 }))
    check(not ok, "a duration that isn't offered")

    -- floors, ceilings, fees
    local volt = pet("VoltFox")
    local value = AuctionRules.value("Pet", volt)
    local low, high = AuctionRules.startRange("Pet", volt)
    check(low == math.max(1, value), "the floor is the sell value (" .. low .. " = " .. value .. ")")
    check(high <= AuctionRules.priceCap("Pet", volt), "the ceiling is under the price cap")
    ok = AuctionChecks.list(listFacts({ startBid = low - 1 }))
    check(not ok, "under the floor: refused")
    ok = AuctionChecks.list(listFacts({ startBid = high + 1 }))
    check(not ok, "over the ceiling: refused")
    ok = AuctionChecks.list(listFacts({ startBid = low + 0.5 }))
    check(not ok, "a fraction of a stone: refused")
    ok, why = AuctionChecks.list(listFacts({ stones = 0 }))
    check(not ok and string.find(why, "fee") ~= nil, "can't pay the fee: refused")
    check(AuctionRules.listingFee(100) == 2 and AuctionRules.listingFee(10000) == 200, "fee 2% (at least 2)")
    check(AuctionRules.saleTax(1000) == 100, "tax 10%")
    check(AuctionRules.minBid({ StartBid = 50 }) == 50, "first bid: the starting bid")
    check(AuctionRules.minBid({ StartBid = 50, High = { Amount = 100 } }) == 105, "then 5% more")
    check(AuctionRules.minBid({ StartBid = 1, High = { Amount = 3 } }) == 4, "at least 1 more")
    check(AuctionRules.priceCap("Pet", pet("AquaWisp")) < AuctionRules.priceCap("Pet", pet("OriginSerpent")), "rarer beasts may fetch more")

    -- bids
    local now = os.time()
    local record = { State = "Active", Ends = now + 600, Seller = 1, Kind = "Pet", Item = pet("VoltFox"), StartBid = 50, Cap = 5000, Paid = false }
    local function bidFacts(extra)
        local f = { rankName = RANK_OK, ageDays = 400, paidOk = true, userId = 2, record = record, amount = 50, stones = 1000, bidOn = 0,
            watching = false, now = now }
        for k, v in extra or {} do
            f[k] = v
        end
        return f
    end
    check(AuctionChecks.bid(bidFacts()) == true, "a fair bid passes")
    ok, why = AuctionChecks.bid(bidFacts({ userId = 1 }))
    check(not ok and string.find(why, "own") ~= nil, "own listing refused")
    ok = AuctionChecks.bid(bidFacts({ amount = 49 }))
    check(not ok, "under the minimum refused")
    ok = AuctionChecks.bid(bidFacts({ amount = 5001 }))
    check(not ok, "over the cap refused")
    ok, why = AuctionChecks.bid(bidFacts({ stones = 10 }))
    check(not ok and string.find(why, "need") ~= nil, "not enough stones refused")
    ok = AuctionChecks.bid(bidFacts({ now = now + 601 }))
    check(not ok, "an ended auction refused")
    ok = AuctionChecks.bid(bidFacts({ bidOn = GameConfig.AuctionHouse.MaxBidOn }))
    check(not ok, "the bid-on cap")
    check(AuctionChecks.bid(bidFacts({ bidOn = GameConfig.AuctionHouse.MaxBidOn, watching = true })) == true, "but raising where already bidding is fine")
    local paidRecord = table.clone(record)
    paidRecord.Paid, paidRecord.Item = true, pet("Crysalith")
    ok, why = AuctionChecks.bid(bidFacts({ record = paidRecord, paidOk = false }))
    check(not ok and string.find(why, "Exclusive Egg") ~= nil, "POLICY: can't bid on a paid pet where trading paid items isn't allowed")
    local markedRecord = table.clone(record)
    markedRecord.Paid, markedRecord.Item = true, pet("VoltFox", { Paid = true })
    ok = AuctionChecks.bid(bidFacts({ record = markedRecord, paidOk = false }))
    check(not ok, "POLICY: can't bid on a bought-spin pet where paid trading isn't allowed")
    check(AuctionChecks.bid(bidFacts({ record = markedRecord, paidOk = true })) == true, "POLICY: allowed elsewhere")
    local bigWeapon = table.clone(record)
    bigWeapon.Kind, bigWeapon.Item = "Weapon", { InstanceId = "W", WeaponId = "Sword12" }
    ok, why = AuctionChecks.bid(bidFacts({ record = bigWeapon }))
    check(not ok and string.find(why, "Reach") ~= nil, "a weapon above the bidder's realm refused (" .. tostring(why) .. ")")

    table.insert(lines, string.format("CHECKS: %d passed, %d failed", passed, failed))
    return passed, failed, lines
end
