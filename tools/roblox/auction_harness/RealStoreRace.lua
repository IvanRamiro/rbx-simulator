-- The Auction House against the REAL stores (DataStore UpdateAsync, the mailbox, the indexes), in a Studio Play server with
-- ServerStorage's StudioTestSave set (AuctionStores prefixes every store with it, so no real auction is touched). Fake players
-- (no save of theirs is touched either): a listing, two bidders racing in two threads, the end, the claims. Returns passed,
-- failed, lines. Call: require(this)(AuctionCore, AuctionStores, AuctionRules, config)
return function(AuctionCore, AuctionStores, AuctionRules, config)
    local HttpService = game:GetService("HttpService")
    local passed, failed, lines = 0, 0, {}
    local function check(cond, what)
        if cond then
            passed += 1
        else
            failed += 1
        end
        table.insert(lines, (if cond then "ok: " else "FAIL: ") .. what)
    end
    check(AuctionStores.prefix ~= "", "the stores are a test's (prefix " .. AuctionStores.prefix .. ")")
    if AuctionStores.prefix == "" then
        return passed, failed, lines
    end
    local clock = os.time()
    local core = AuctionCore.new({
        now = function()
            return clock
        end,
        guid = function()
            return HttpService:GenerateGUID(false)
        end,
        listings = AuctionStores.listings, mail = AuctionStores.mail, index = AuctionStores.index, notify = function() end,
        rules = { minBid = AuctionRules.minBid, saleTax = AuctionRules.saleTax }, config = config,
    })
    local base = -math.random(100000, 999999) -- fake user ids, never a real account
    local function fake(n, stones, items)
        local mem = { stones = stones, items = items or {} }
        local p = { userId = base - n, name = "Tester" .. n, paidOk = true, pending = {}, mem = mem,
            ledger = { Out = {}, Bids = {}, Claimed = {}, Mine = {}, Watch = {} } }
        function p.takeItem(_, id)
            for i, item in mem.items do
                if item.InstanceId == id then
                    return table.remove(mem.items, i)
                end
            end
            return nil
        end
        function p.restoreItem(_, item)
            table.insert(mem.items, item)
            return true
        end
        function p.spend(amount)
            if mem.stones < amount then
                return false
            end
            mem.stones -= amount
            return true
        end
        function p.add(amount)
            mem.stones += amount
        end
        function p.saveConfirmed()
            task.wait(0.2)
            return true
        end
        function p.saveSoon() end
        return p
    end
    local seller = fake(1, 100, { { InstanceId = "RS-" .. HttpService:GenerateGUID(false), PetId = "VoltFox", Level = 1, Size = "Normal", Worth = 1 } })
    local a, b = fake(2, 1000), fake(3, 1000)
    local item = seller.mem.items[1].InstanceId
    local ok, id, status = core:list(seller, { Kind = "Pet", InstanceId = item, StartBid = 100, Hours = 1, Fee = 2, Paid = false,
        Rarity = "Epic", Value = 50, Cap = 100000, SellerName = "Tester1" })
    check(ok and status == "Live", "listed on the real store (" .. tostring(status) .. ")")
    local got, record = AuctionStores.listings.get(id)
    check(got and record and record.State == "Active", "its record reads back Active")
    -- the race: two threads, the same amount, at once
    local outcomes, done = {}, 0
    for _, p in { a, b } do
        task.spawn(function()
            local _, outcome = core:bid(p, id, 100)
            outcomes[p.userId] = outcome
            done += 1
        end)
    end
    local deadline = os.clock() + 60
    while done < 2 and os.clock() < deadline do
        task.wait(0.1)
    end
    local accepted = (if outcomes[a.userId] == "Accepted" then 1 else 0) + (if outcomes[b.userId] == "Accepted" then 1 else 0)
    check(accepted == 1, "exactly one of two racing equal bids taken (" .. tostring(outcomes[a.userId]) .. ", " .. tostring(outcomes[b.userId]) .. ")")
    check(a.mem.stones + b.mem.stones == 1900, "the other's stones came straight back (" .. (a.mem.stones + b.mem.stones) .. ")")
    -- the loser outbids the winner: the winner's refund goes through the real mailbox
    local winner, loser = if outcomes[a.userId] == "Accepted" then a else b, if outcomes[a.userId] == "Accepted" then b else a
    local _, outcome = core:bid(loser, id, 200)
    check(outcome == "Accepted", "an outbid")
    core:claim(winner)
    check(winner.mem.stones == 1000, "the outbid refund arrived by mail (" .. winner.mem.stones .. ")")
    core:claim(winner)
    check(winner.mem.stones == 1000, "and a second claim gives nothing")
    -- the end
    clock += 3600 + 10
    core:settle(id)
    core:claim(loser)
    core:claim(seller)
    check(#loser.mem.items == 1, "the winner has the pet")
    check(seller.mem.stones == 98 + 180, "the seller got 200 less the 10% fee (" .. seller.mem.stones .. ")")
    got, record = AuctionStores.listings.get(id)
    check(got and record.State == "Sold" and next(record.Outbox or {}) == nil, "the record is Sold with an empty outbox")
    return passed, failed, lines
end
