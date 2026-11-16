-- The Auction House's transaction tests (vault: Auction House Design 2026-11-16). Runs src/server/Auction/AuctionCore against
-- fake stores that behave like DataStore UpdateAsync (atomic per key, copies in and out), fake players with a memory and a
-- persisted save (saveConfirmed copies one to the other), a fake clock, and a tiny scheduler so two bidders can race.
-- A "crash" throws at a named journal step: the server dies there, every player on it reloads from their persisted save, the
-- stores keep what they had, and recovery runs as a new server would.
--
-- Used two ways, with no Roblox service needed:
--   luau tools/roblox/auction_harness/run_cli.luau                (the Luau CLI: AuctionCore required by path)
--   in Studio: put it in as a ModuleScript (a temporary file in src/server/Auction syncs it) and call it with the live AuctionCore
-- Returns run(Core, log) -> passed, failed, lines.
local CONFIG = {
    SnipeWindow = 60, SnipeExtend = 60, MaxExtension = 1800, MinRaise = 0.05, SaleTax = 0.1,
}

local function deepCopy(value)
    if type(value) ~= "table" then
        return value
    end
    local out = {}
    for k, v in value do
        out[k] = deepCopy(v)
    end
    return out
end

local RULES = {
    minBid = function(listing)
        if listing.High then
            return listing.High.Amount + math.max(1, math.ceil(listing.High.Amount * CONFIG.MinRaise))
        end
        return listing.StartBid
    end,
    saleTax = function(price)
        return math.floor(price * CONFIG.SaleTax)
    end,
}

-- ---------- the scheduler ----------
local function newScheduler()
    local S = { tasks = {}, crashed = nil }
    function S.spawn(fn, ...)
        local args = table.pack(...)
        table.insert(S.tasks, coroutine.create(function()
            fn(table.unpack(args, 1, args.n))
        end))
    end
    function S.yield()
        if coroutine.isyieldable() then
            coroutine.yield()
        end
    end
    -- runs every task to its end, in turns; a CRASH kills them all (the server died)
    function S.run()
        local rounds = 0
        while #S.tasks > 0 do
            rounds += 1
            assert(rounds < 100000, "scheduler: tasks never finished")
            for i = #S.tasks, 1, -1 do
                local co = S.tasks[i]
                local ok, err = coroutine.resume(co)
                if not ok then
                    if type(err) == "string" and string.find(err, "CRASH:", 1, true) then
                        S.crashed = string.match(err, "CRASH:([%w%.]+)")
                        S.tasks = {}
                        return S.crashed
                    end
                    error(err, 0)
                end
                if coroutine.status(co) == "dead" then
                    table.remove(S.tasks, i)
                end
            end
        end
        return nil
    end
    return S
end

-- ---------- a world: stores, clock, players ----------
local function newWorld()
    local W = { clock = 1000000, seq = 0, players = {}, crashAt = nil, crashes = 0, sched = newScheduler(), notified = {} }

    local function store(name)
        local data = {}
        local s = { data = data, name = name, faults = {} }
        function s.get(key)
            W.sched.yield()
            return true, deepCopy(data[key])
        end
        -- fault "before": fails without writing; "after": writes, then reports a failure (a commit the caller can't see)
        function s.update(key, transform)
            W.sched.yield()
            local fault = s.faults[key]
            if fault == "before" then
                s.faults[key] = nil
                return false, "fault"
            end
            local new = transform(deepCopy(data[key]))
            if new ~= nil then
                data[key] = deepCopy(new)
            end
            if fault == "after" then
                s.faults[key] = nil
                return false, "fault"
            end
            return true
        end
        return s
    end
    W.listings = store("listings")
    W.mail = store("mail")
    W.indexData = {}
    W.index = {
        put = function(summary)
            W.indexData[summary.Id] = { End = summary.End, Summary = deepCopy(summary) }
        end,
        remove = function(id)
            W.indexData[id] = nil
        end,
        due = function(before, n)
            local ids = {}
            for id, entry in W.indexData do
                if entry.End <= before then
                    table.insert(ids, id)
                end
            end
            table.sort(ids)
            while #ids > n do
                table.remove(ids)
            end
            return ids
        end,
    }
    function W.deps()
        return {
            now = function()
                return W.clock
            end,
            guid = function()
                W.seq += 1
                return string.format("ID%04d", W.seq)
            end,
            listings = W.listings, mail = W.mail, index = W.index, rules = RULES, config = CONFIG,
            notify = function(userId)
                W.notified[userId] = (W.notified[userId] or 0) + 1
            end,
            step = function(name)
                W.lastStep = name
                if W.crashAt == name then
                    W.crashAt = nil
                    W.crashes += 1
                    error("CRASH:" .. name, 0)
                end
            end,
        }
    end

    -- a player: persisted = what their save holds; the live table = what this server holds in memory
    function W.player(userId, name, stones, pets, weapons)
        local saved = {
            stones = stones, pets = pets or {}, weapons = weapons or {},
            ledger = { Out = {}, Bids = {}, Claimed = {}, Mine = {}, Watch = {} },
        }
        local slot = { saved = saved, userId = userId, name = name, paidOk = true, maxPets = 50, maxWeapons = 30, sessionLost = false }
        W.players[userId] = slot
        W.load(userId)
        return slot
    end

    -- (re)loads a player on a "new server": their memory from their persisted save, nothing pending
    function W.load(userId)
        local slot = W.players[userId]
        local mem = deepCopy(slot.saved)
        local p = { userId = userId, name = slot.name, pending = {}, ledger = mem.ledger, mem = mem }
        p.paidOk = slot.paidOk
        function p.takeItem(kind, instanceId)
            local list = if kind == "Pet" then mem.pets else mem.weapons
            for i, item in list do
                if item.InstanceId == instanceId then
                    if item.Locked or item.Equipped then
                        return nil
                    end
                    table.remove(list, i)
                    return deepCopy(item)
                end
            end
            return nil
        end
        function p.restoreItem(kind, item)
            local list = if kind == "Pet" then mem.pets else mem.weapons
            if #list >= (if kind == "Pet" then slot.maxPets else slot.maxWeapons) then
                return false
            end
            local copy = deepCopy(item)
            copy.Locked, copy.Equipped = nil, nil
            table.insert(list, copy)
            return true
        end
        function p.spend(n)
            if mem.stones < n then
                return false
            end
            mem.stones -= n
            return true
        end
        function p.add(n)
            mem.stones += n
        end
        function p.saveConfirmed()
            W.sched.yield()
            if slot.sessionLost then
                return false
            end
            slot.saved = deepCopy(mem)
            return true
        end
        function p.saveSoon()
            slot.dirty = true
        end
        slot.p = p
        return p
    end

    -- the autosave: what a later, ordinary save would write
    function W.autosave()
        for _, slot in W.players do
            if not slot.sessionLost then
                slot.saved = deepCopy(slot.p.mem)
            end
        end
    end

    -- the server died: every player's memory is lost; they come back on a new server
    function W.crashServer()
        for userId in W.players do
            W.load(userId)
        end
    end

    -- everything a running game does in time: each player's journal pumped and mail claimed, the sweeper, an autosave; repeated
    function W.quiesce(core, rounds)
        for _ = 1, rounds or 4 do
            for _, slot in W.players do
                if not slot.sessionLost then
                    W.sched.spawn(function()
                        core:pump(slot.p)
                        core:claim(slot.p)
                    end)
                end
            end
            W.sched.spawn(function()
                core:sweep(50)
            end)
            if W.sched.run() then
                W.crashServer()
            end
            W.autosave()
        end
    end

    function W.run(fn, ...)
        W.sched.spawn(fn, ...)
        local crashed = W.sched.run()
        if crashed then
            W.crashServer()
        end
        return crashed
    end

    -- every stone and every item, wherever it is: memory wallets and inventories, journals, listings, outboxes, mailboxes
    function W.census()
        local stones, items = 0, {}
        local claimed = {}
        local function item(id, where)
            items[id] = items[id] or {}
            table.insert(items[id], where)
        end
        for userId, slot in W.players do
            local mem = slot.p.mem
            stones += mem.stones
            for _, pet in mem.pets do
                item(pet.InstanceId, "inv:" .. userId)
            end
            for _, weapon in mem.weapons do
                item(weapon.InstanceId, "inv:" .. userId)
            end
            for _, entry in mem.ledger.Out do
                item(entry.Item.InstanceId, "out:" .. userId)
                stones += entry.Fee -- (paid, and kept: counted as spent below)
            end
            for _, entry in mem.ledger.Bids do
                stones += entry.Amount
            end
            for mailId in mem.ledger.Claimed do
                claimed[mailId] = true
            end
        end
        local fees, taxes = 0, 0
        local mails = {}
        for id, record in W.listings.data do
            if record.Seller then
                fees += record.Fee or 0
                if record.State == "Active" then
                    if record.Item then
                        item(record.Item.InstanceId, "listing:" .. id)
                    end
                    if record.High then
                        stones += record.High.Amount
                    end
                end
                if record.Result then
                    taxes += record.Result.Tax
                end
                for mailId, entry in record.Outbox or {} do
                    mails[mailId] = entry.Mail
                end
            end
        end
        for key, box in W.mail.data do
            for mailId, mail in box.Items or {} do
                mails[mailId] = mail
            end
            for mailId in box.Done or {} do
                mails[mailId] = nil
                claimed[mailId] = true
            end
        end
        for mailId, mail in mails do
            if not claimed[mailId] then
                stones += mail.Stones or 0
                if mail.Item then
                    item(mail.Item.InstanceId, "mail:" .. mailId)
                end
            end
        end
        -- the fees counted in a journal were also taken from the wallet: count each once
        local journalFees = 0
        for _, slot in W.players do
            for _, entry in slot.p.mem.ledger.Out do
                journalFees += entry.Fee
            end
        end
        return { stones = stones - journalFees, fees = fees + journalFees, taxes = taxes, items = items }
    end

    -- nothing left in flight: journals empty, outboxes empty, mailboxes claimed
    function W.idle()
        for _, slot in W.players do
            local l = slot.p.mem.ledger
            if next(l.Out) or next(l.Bids) or next(l.Claimed) then
                return false, "journal of " .. slot.userId
            end
        end
        for id, record in W.listings.data do
            if next(record.Outbox or {}) then
                return false, "outbox of " .. id
            end
        end
        for key, box in W.mail.data do
            if next(box.Items or {}) then
                return false, "mailbox " .. key
            end
        end
        return true
    end

    return W
end

-- ---------- the cases ----------
return function(Core, log)
    log = log or print
    local passed, failed, lines = 0, 0, {}
    local function say(text)
        table.insert(lines, text)
        log(text)
    end
    local function check(cond, what)
        if cond then
            passed += 1
        else
            failed += 1
            say("  FAIL: " .. what)
        end
        return cond
    end
    local function pet(id, petId)
        return { InstanceId = id, PetId = petId or "VoltFox", Level = 1, Size = "Normal", Worth = 1 }
    end
    local function spec(instanceId, startBid, hours)
        return { Kind = "Pet", InstanceId = instanceId, StartBid = startBid or 100, Hours = hours or 1, Fee = 2, Paid = false,
            Rarity = "Epic", Value = 50, Cap = 100000, Show = nil, SellerName = "Seller" }
    end
    -- conservation: every stone and item is where it should be, each item exactly once
    local function conserved(W, total, ids, label)
        local c = W.census()
        local ok = check(c.stones + c.fees + c.taxes == total,
            label .. ": stones conserved (" .. c.stones .. " + fees " .. c.fees .. " + tax " .. c.taxes .. " vs " .. total .. ")")
        for _, id in ids do
            local where = c.items[id] or {}
            ok = check(#where == 1, label .. ": item " .. id .. " exactly once (" .. table.concat(where, ", ") .. ")") and ok
        end
        return ok, c
    end
    local function holder(W, id)
        local where = W.census().items[id]
        return where and where[1]
    end

    -- 1. list, bid, outbid and refund, anti-snipe, end with a winner
    do
        say("case: list, bid, outbid, refund, anti-snipe, winner")
        local W = newWorld()
        local core = Core.new(W.deps())
        local S = W.player(1, "Seller", 1000, { pet("P1") })
        local A = W.player(2, "Ann", 1000)
        local B = W.player(3, "Bo", 1000)
        local listingId
        W.run(function()
            local ok, id, status = core:list(S.p, spec("P1", 100, 1))
            check(ok and status == "Live", "listed live")
            listingId = id
        end)
        check(W.listings.data[listingId] and W.listings.data[listingId].State == "Active", "record Active")
        check(S.p.mem.stones == 998, "fee taken (998)")
        check(#S.p.mem.pets == 0, "pet out of the seller's inventory")
        W.run(function()
            local _, outcome = core:bid(A.p, listingId, 100)
            check(outcome == "Accepted", "Ann's bid accepted")
        end)
        check(A.p.mem.stones == 900, "Ann's 100 in escrow")
        W.run(function()
            local _, outcome, why = core:bid(A.p, listingId, 120)
            check(outcome == "Refused" and why == "Top", "Ann can't raise her own top bid")
        end)
        check(A.p.mem.stones == 900, "Ann's refused raise refunded")
        W.run(function()
            local _, outcome, why = core:bid(B.p, listingId, 104)
            check(outcome == "Refused" and why == "Low", "Bo under the minimum raise refused (" .. tostring(why) .. ")")
        end)
        check(B.p.mem.stones == 1000, "Bo's refused bid refunded")
        -- anti-snipe: 30 s before the end
        local record = W.listings.data[listingId]
        W.clock = record.Ends - 30
        W.run(function()
            local _, outcome = core:bid(B.p, listingId, 105)
            check(outcome == "Accepted", "Bo outbids at 105")
        end)
        record = W.listings.data[listingId]
        check(record.Ends == W.clock + 60, "anti-snipe moved the end to 60 s after the bid")
        W.quiesce(core)
        check(A.p.mem.stones == 1000, "Ann refunded through her mailbox (" .. A.p.mem.stones .. ")")
        -- the end
        W.clock = record.Ends + 5
        W.quiesce(core)
        record = W.listings.data[listingId]
        check(record.State == "Sold", "sold")
        check(holder(W, "P1") == "inv:3", "Bo has the pet")
        check(S.p.mem.stones == 998 + 105 - 10, "seller paid 105 less 10 tax (" .. S.p.mem.stones .. ")")
        check(B.p.mem.stones == 895, "Bo paid 105")
        check(W.idle(), "nothing left in flight")
        conserved(W, 3000, { "P1" }, "winner")
    end

    -- 2. end with no bids; cancel; duplicate list; own listing; insufficient stones; anti-snipe cap
    do
        say("case: no bids, cancel, duplicate list, own listing, insufficient stones")
        local W = newWorld()
        local core = Core.new(W.deps())
        local S = W.player(1, "Seller", 50, { pet("P1"), pet("P2"), pet("P3") })
        local A = W.player(2, "Ann", 10)
        local first, second
        W.run(function()
            local _, id = core:list(S.p, spec("P1", 100, 1))
            first = id
            local ok, why = core:list(S.p, spec("P1", 100, 1))
            check(not ok and why == "Gone", "the same pet can't be listed twice")
            local _, id2 = core:list(S.p, spec("P2", 100, 4))
            second = id2
        end)
        W.run(function()
            local _, outcome, why = core:bid(S.p, first, 40)
            check(outcome == "Refused" and why == "Own", "no bidding on your own listing (" .. tostring(why) .. ")")
            local ok, why2 = core:bid(A.p, first, 100)
            check(not ok and why2 == "Stones", "not enough stones")
        end)
        check(S.p.mem.stones == 46, "seller's refused own bid refunded (46)")
        W.run(function()
            local ok = core:cancel(S.p, second)
            check(ok, "cancel with no bids")
            local ok2, why = core:cancel(A.p, first)
            check(not ok2 and why == "NotYours", "only the seller cancels")
        end)
        W.quiesce(core)
        check(holder(W, "P2") == "inv:1", "cancelled pet back with the seller")
        W.clock += 3600 + 10
        W.quiesce(core)
        check(W.listings.data[first].State == "Unsold", "no bids: unsold")
        check(holder(W, "P1") == "inv:1", "unsold pet back with the seller")
        check(S.p.mem.stones == 46, "fees kept (46)")
        check(W.idle(), "nothing left in flight")
        conserved(W, 60, { "P1", "P2", "P3" }, "unsold")
        -- a listing with a bid can't be cancelled
        local third
        W.run(function()
            local _, id = core:list(S.p, spec("P3", 5, 1))
            third = id
        end)
        A.p.mem.stones = 10
        A.saved.stones = 10
        W.run(function()
            core:bid(A.p, third, 5)
            local ok, why = core:cancel(S.p, third)
            check(not ok and why == "HasBids", "no cancel once bid on")
        end)
    end

    -- 3. a concurrent bid race: two bidders, the same amount, at the same moment
    do
        say("case: concurrent bid race")
        local W = newWorld()
        local core = Core.new(W.deps())
        local S = W.player(1, "Seller", 0, { pet("P1") })
        S.p.mem.stones = 10
        S.saved.stones = 10
        local A = W.player(2, "Ann", 500)
        local B = W.player(3, "Bo", 500)
        local id
        W.run(function()
            local _, lid = core:list(S.p, spec("P1", 100, 1))
            id = lid
        end)
        local outcomes = {}
        W.sched.spawn(function()
            local _, o, why = core:bid(A.p, id, 100)
            outcomes.A = o .. ":" .. tostring(why)
        end)
        W.sched.spawn(function()
            local _, o, why = core:bid(B.p, id, 100)
            outcomes.B = o .. ":" .. tostring(why)
        end)
        W.sched.run()
        local accepted = (if string.find(outcomes.A, "Accepted") then 1 else 0) + (if string.find(outcomes.B, "Accepted") then 1 else 0)
        check(accepted == 1, "exactly one of two equal racing bids accepted (" .. outcomes.A .. ", " .. outcomes.B .. ")")
        check(A.p.mem.stones + B.p.mem.stones == 900, "the loser's stones came back at once")
        W.quiesce(core)
        conserved(W, 1010, { "P1" }, "race")
        -- and two different amounts racing: the higher stands, the lower is refunded or outbid
        local C = W.player(4, "Cy", 1000)
        local D = W.player(5, "Di", 1000)
        W.sched.spawn(function()
            core:bid(C.p, id, 300)
        end)
        W.sched.spawn(function()
            core:bid(D.p, id, 400)
        end)
        W.sched.run()
        W.quiesce(core)
        local record = W.listings.data[id]
        check(record.High.Amount == 400 and record.High.UserId == 5, "the highest racing bid holds the top (" .. record.High.Amount .. ")")
        check(C.p.mem.stones == 1000, "the other racer has all his stones back")
        conserved(W, 3010, { "P1" }, "race 2")
    end

    -- 4. a crash at every journal step: nothing duplicated, nothing lost, and everything finishes
    local STEPS = { "list.journaled", "list.saved", "list.created", "list.indexed", "bid.journaled", "bid.saved", "bid.applied",
        "bid.settled", "flush.delivered", "flush.cleared", "cancel.closed", "settle.closed", "claim.granted", "claim.saved", "claim.crossed" }
    for _, crashStep in STEPS do
        local W = newWorld()
        local core = Core.new(W.deps())
        local S = W.player(1, "Seller", 100, { pet("P1"), pet("P2"), pet("P3") })
        local A = W.player(2, "Ann", 1000)
        local B = W.player(3, "Bo", 1000)
        W.crashAt = crashStep
        local ids = {}
        local function act(fn)
            local crashed = W.run(fn)
            return crashed
        end
        -- the whole life of three listings: two bids and an outbid, a cancel, an unsold one; then the end
        act(function()
            local _, id = core:list(S.p, spec("P1", 100, 1))
            ids.sold = id
        end)
        W.quiesce(core, 2)
        act(function()
            local _, id = core:list(S.p, spec("P2", 100, 1))
            ids.cancel = id
        end)
        W.quiesce(core, 2)
        act(function()
            local _, id = core:list(S.p, spec("P3", 100, 1))
            ids.unsold = id
        end)
        W.quiesce(core, 2)
        -- (a crash may have left a listing only journaled: the quiesce made it, or its id is unknown here; find them by item)
        local function listingOf(instanceId)
            for id, record in W.listings.data do
                if record.Item and record.Item.InstanceId == instanceId and record.State == "Active" then
                    return id
                end
            end
            return nil
        end
        ids.sold, ids.cancel, ids.unsold = listingOf("P1"), listingOf("P2"), listingOf("P3")
        if ids.sold then
            act(function()
                core:bid(A.p, ids.sold, 100)
            end)
            W.quiesce(core, 2)
            act(function()
                core:bid(B.p, ids.sold, 150)
            end)
            W.quiesce(core, 2)
        end
        if ids.cancel then
            act(function()
                core:cancel(S.p, ids.cancel)
            end)
            W.quiesce(core, 2)
        end
        W.clock += 3600 + 100
        W.quiesce(core, 6)
        local label = "crash at " .. crashStep
        local idle, what = W.idle()
        check(W.crashes == 1, label .. ": the crash happened")
        check(idle, label .. ": everything finished (" .. tostring(what) .. ")")
        local _, c = conserved(W, 2100, { "P1", "P2", "P3" }, label)
        -- (whatever the crash cut short, the result is one the rules allow: each pet with its seller or the winner)
        if ids.sold and W.listings.data[ids.sold].State == "Sold" then
            local result = W.listings.data[ids.sold].Result
            check(c.items.P1 and c.items.P1[1] == "inv:" .. result.Winner, label .. ": the winner has the sold pet")
        end
        say(string.format("  %-16s idle=%s stones %d+%d+%d items P1=%s P2=%s P3=%s", crashStep, tostring(idle), c.stones, c.fees, c.taxes,
            tostring(c.items.P1 and c.items.P1[1]), tostring(c.items.P2 and c.items.P2[1]), tostring(c.items.P3 and c.items.P3[1])))
    end

    -- 5. ambiguous store failures: a write that lands but reports failure, and one that fails outright
    do
        say("case: ambiguous and failed writes")
        local W = newWorld()
        local core = Core.new(W.deps())
        local S = W.player(1, "Seller", 100, { pet("P1") })
        local A = W.player(2, "Ann", 1000)
        local id
        W.run(function()
            local _, lid = core:list(S.p, spec("P1", 100, 1))
            id = lid
        end)
        W.listings.faults[id] = "after" -- the bid lands, but the caller hears a failure
        W.run(function()
            local _, outcome = core:bid(A.p, id, 100)
            check(outcome == "Pending", "an unseen commit leaves the bid pending")
        end)
        check(next(A.p.mem.ledger.Bids) ~= nil, "the bid stays in the journal")
        W.quiesce(core, 2)
        check(next(A.p.mem.ledger.Bids) == nil and W.listings.data[id].High.UserId == 2, "the pump finds it accepted")
        check(A.p.mem.stones == 900, "and no refund was given (" .. A.p.mem.stones .. ")")
        local B = W.player(3, "Bo", 1000)
        W.listings.faults[id] = "before"
        W.run(function()
            local _, outcome = core:bid(B.p, id, 200)
            check(outcome == "Pending", "a failed write leaves the bid pending")
        end)
        W.quiesce(core, 3)
        check(W.listings.data[id].High.UserId == 3, "the pump puts it on the listing once the store answers")
        conserved(W, 2100, { "P1" }, "ambiguous")
        -- a session taken by another server: the save fails, nothing leaves this server
        local C = W.player(4, "Cy", 1000)
        C.sessionLost = true
        W.run(function()
            local _, outcome = core:bid(C.p, id, 400)
            check(outcome == "Pending", "with the session gone, the bid waits")
        end)
        check(W.listings.data[id].High.UserId == 3, "and never reached the listing")
        C.sessionLost = false
        W.load(4) -- the other server has the save: the bid was never written
        check(C.p.mem.stones == 1000, "the other server's save still has all of Cy's stones")
        -- the same for a listing: a seller whose session moved can't put an item up from the old server
        S.p.mem.pets = { pet("P9") }
        S.saved.pets = { pet("P9") }
        S.sessionLost = true
        W.run(function()
            local _, _, status = core:list(S.p, spec("P9", 100, 1))
            check(status == "Pending", "with the session gone, the listing waits")
        end)
        local made = false
        for _, record in W.listings.data do
            if record.Item and record.Item.InstanceId == "P9" then
                made = true
            end
        end
        check(not made, "and no listing was made from the old server")
        S.sessionLost = false
        W.load(1)
        check(#S.p.mem.pets == 1, "the other server's save still has the pet")
    end

    -- 6. a crashed bid racing its own recovery: the recovery voids it before the old server's write lands
    do
        say("case: a recovered bid voided before a late write")
        local W = newWorld()
        local core = Core.new(W.deps())
        local S = W.player(1, "Seller", 100, { pet("P1") })
        local A = W.player(2, "Ann", 1000)
        local id
        W.run(function()
            local _, lid = core:list(S.p, spec("P1", 100, 1))
            id = lid
        end)
        W.crashAt = "bid.saved"
        W.run(function()
            core:bid(A.p, id, 100)
        end)
        -- the new server: Ann's save holds the bid; the old server's write never happened. Recovery resolves it.
        local bidId = next(A.p.mem.ledger.Bids)
        check(bidId ~= nil, "the journaled bid survived the crash")
        -- void it as a recovery would if the listing had ended meanwhile
        W.clock += 3600 + 10
        W.run(function()
            core:pump(A.p)
        end)
        check(W.listings.data[id].Voided[bidId] == true, "the late bid is voided on the listing")
        check(A.p.mem.stones == 1000, "and its stones came back")
        -- the old server's write arriving now can't take it, even on a listing where the same bid would be valid
        local late = core:refusal(W.listings.data[id], 2, 100, true, W.clock)
        check(late ~= nil, "a late write is refused")
        local W2 = newWorld()
        local core2 = Core.new(W2.deps())
        local S2 = W2.player(1, "Seller", 100, { pet("Q1") })
        local A2 = W2.player(2, "Ann", 1000)
        local id2
        W2.run(function()
            local _, lid = core2:list(S2.p, spec("Q1", 100, 1))
            id2 = lid
        end)
        W2.crashAt = "bid.saved"
        W2.run(function()
            core2:bid(A2.p, id2, 100)
        end)
        local oldMemory = deepCopy(A2.saved) -- what the crashed server still held
        local bid2 = next(A2.p.mem.ledger.Bids)
        W2.listings.data[id2].Voided = { [bid2] = true } -- as a recovery that saw it refused would leave it
        local late2 = { userId = 2, name = "Ann", pending = {}, ledger = oldMemory.ledger, paidOk = true,
            add = function() end, saveSoon = function() end, spend = function()
                return true
            end }
        W2.run(function()
            local outcome = core2:applyBid(late2, bid2)
            check(outcome == "Refused", "a voided bid is never accepted later, though the listing would take it (" .. tostring(outcome) .. ")")
        end)
        check(W2.listings.data[id2].High == nil, "the listing has no top bid from it")
        W.quiesce(core)
        conserved(W, 1100, { "P1" }, "void")
    end

    -- 7. the mailbox: one delivery per id, one gift per mail
    do
        say("case: mailbox idempotency")
        local W = newWorld()
        local core = Core.new(W.deps())
        local A = W.player(2, "Ann", 0)
        local mail = { Why = "Sold", Stones = 50, At = 1 }
        W.run(function()
            check(core:deliver(2, "PX", mail), "delivered")
            check(core:deliver(2, "PX", mail), "delivered again: no change")
            core:claim(A.p)
            core:claim(A.p)
        end)
        check(A.p.mem.stones == 50, "given once (" .. A.p.mem.stones .. ")")
        W.run(function()
            core:deliver(2, "PX", mail) -- a late copy, after the claim
            core:claim(A.p)
        end)
        check(A.p.mem.stones == 50, "a late copy of a claimed mail gives nothing")
        -- a crash between the save and the crossing off
        W.crashAt = "claim.saved"
        W.run(function()
            core:deliver(2, "PY", { Why = "Outbid", Stones = 7, At = 2 })
            core:claim(A.p)
        end)
        check(A.p.mem.stones == 57, "the saved gift survived the crash (" .. A.p.mem.stones .. ")")
        W.run(function()
            core:claim(A.p)
        end)
        check(A.p.mem.stones == 57, "and isn't given again on the next claim")
        check(W.idle(), "the mail is crossed off")
        -- a full inventory leaves the item waiting
        A.maxPets = 0
        W.load(2)
        A.maxPets = 0
        W.run(function()
            core:deliver(2, "IZ", { Why = "Won", Kind = "Pet", Item = pet("PZ"), At = 3 })
            local given, waiting = core:claim(A.p)
            check(#given == 0 and waiting == 1, "no room: the pet waits in the mailbox")
        end)
        A.maxPets = 50
        W.run(function()
            local given = core:claim(A.p)
            check(#given == 1, "with room it arrives")
        end)
        check(holder(W, "PZ") == "inv:2", "the pet is Ann's")
    end

    -- 8. the paid-item rule: a player whose region doesn't allow trading paid items can't bid on one
    do
        say("case: paid-item policy")
        local W = newWorld()
        local core = Core.new(W.deps())
        local S = W.player(1, "Seller", 100, { pet("PM", "NineTailMoonfox") })
        local A = W.player(2, "Ann", 5000)
        A.paidOk = false
        W.load(2)
        local id
        W.run(function()
            local s = spec("PM", 100, 1)
            s.Paid = true
            local _, lid = core:list(S.p, s)
            id = lid
        end)
        W.run(function()
            local _, outcome, why = core:bid(A.p, id, 100)
            check(outcome == "Refused" and why == "Paid", "a paid item is refused where trading them isn't allowed")
        end)
        check(A.p.mem.stones == 5000, "and the stones came back")
        A.paidOk = true
        W.load(2)
        W.run(function()
            local _, outcome = core:bid(A.p, id, 100)
            check(outcome == "Accepted", "allowed elsewhere")
        end)
    end

    say(string.format("AUCTION HARNESS: %d passed, %d failed", passed, failed))
    return passed, failed, lines
end
