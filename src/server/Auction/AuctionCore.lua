-- The Auction House's transactions: listing, bidding, cancelling, settling, delivering and claiming (the vault note
-- "Auction House Design 2026-11-16" has the reasoning and every crash point). It touches no Roblox service itself: the stores,
-- the clock and the player are passed in, so tools/roblox/auction_harness runs it with fake stores and crashes.
--
-- THE RULE: nothing leaves this server (a listing, a bid, a claim) until a save holding its journal entry has been written
-- (p.saveConfirmed, which also proves this server still holds the player's session). Every outside step is idempotent:
--   a listing is created only if absent (records are never deleted: a closed one is a small tombstone);
--   a bid is accepted once (Accepted[bidId]) or voided once (Voided[bidId]), whichever lands first;
--   a mail is delivered once per mail id (Items or Done), and given once (the save's Claimed, then the mailbox's Done).
--
--   local core = AuctionCore.new(deps)
--   deps.now()                 unix seconds
--   deps.guid()                a new unique id
--   deps.listings, deps.mail   { get(key) -> ok, value; update(key, transform) -> ok, err } (transform(old) -> new, or nil to keep;
--                              it may be called more than once and must not yield)
--   deps.index                 { put(summary), remove(id), due(before, count) -> ids } (best effort: never trusted for money)
--   deps.notify(userId)        the receiver has mail
--   deps.rules                 { minBid(listing), saleTax(price) }
--   deps.config                GameConfig.AuctionHouse
--   deps.step(name)            a test hook at every journal step (a harness makes one throw, to crash the server there)
--
-- A player (built by AuctionService, or by the harness) is a table:
--   userId, name, paidOk (may trade paid items), ledger (AuctionLedger's live table: Out, Bids, Claimed, Mine, Watch), pending = {}
--   takeItem(kind, instanceId) -> record | nil     restoreItem(kind, record) -> true | false (no room)
--   spend(n, why) -> bool      add(n, why)      saveConfirmed() -> bool      saveSoon()
local AuctionCore = {}
AuctionCore.__index = AuctionCore

local GRACE = 2                  -- seconds past the end before settling (servers' clocks differ a little)
local DONE_KEEP = 60 * 86400     -- seconds a mailbox remembers a delivered mail id
local DONE_MOST = 2000           -- and at most this many
local LAST_SHOWN = 5             -- bids a listing keeps for its detail page

function AuctionCore.new(deps)
    return setmetatable({ deps = deps }, AuctionCore)
end

local function step(self, name)
    if self.deps.step then
        self.deps.step(name)
    end
end

local function count(map)
    local n = 0
    for _ in map or {} do
        n += 1
    end
    return n
end
AuctionCore.count = count

local function addPointer(list, id)
    if not table.find(list, id) then
        table.insert(list, id)
    end
end

local function removePointer(list, id)
    local at = table.find(list, id)
    if at then
        table.remove(list, at)
    end
end
AuctionCore.removePointer = removePointer

-- ---------- the player's journal: an entry may be acted on only once a save holds it ----------
function AuctionCore.mark(p, id)
    p.pending[id] = true
end

function AuctionCore.isConfirmed(p, id)
    return not p.pending[id]
end

-- Writes the save; true if it landed. Only the entries marked before the write are known to be in it.
function AuctionCore.confirm(p)
    local marked = {}
    for id in p.pending do
        table.insert(marked, id)
    end
    if not p.saveConfirmed() then
        return false
    end
    for _, id in marked do
        p.pending[id] = nil
    end
    return true
end

-- ---------- what a listing shows when browsed (MemoryStore) ----------
function AuctionCore.summary(record)
    local item = record.Item or {}
    return {
        Id = record.Id, K = record.Kind, P = item.PetId, W = item.WeaponId, R = record.Rarity, S = item.Size, Lv = item.Level,
        E = item.Element, N = record.Show and record.Show.Name, Sn = record.SellerName, Su = record.Seller,
        Pr = if record.High then record.High.Amount else record.StartBid, St = record.StartBid, B = record.Bids or 0,
        End = record.Ends, Hb = record.High and record.High.UserId, Paid = record.Paid == true, Cr = record.Created,
        State = record.State,
    }
end

-- What another player may see of a listing (its detail page): nothing of the escrow's bookkeeping.
function AuctionCore.public(record)
    local shown = AuctionCore.summary(record)
    shown.Last = record.Last
    shown.Cap = record.Cap
    shown.Value = record.Value
    shown.Result = record.Result
    shown.FirstEnd = record.FirstEnds
    return shown
end

local function isClosed(record)
    return record.State ~= "Active"
end

-- ---------- listing ----------
-- spec: { Kind, InstanceId, StartBid, Hours, Fee, Paid, Rarity, Value, Cap, Show, SellerName } (AuctionService has checked it all)
-- Returns ok, why | listingId, status ("Live" or "Pending": the listing appears once its save lands).
function AuctionCore:list(p, spec)
    local item = p.takeItem(spec.Kind, spec.InstanceId)
    if not item then
        return false, "Gone"
    end
    if not p.spend(spec.Fee, "AuctionFee") then
        p.restoreItem(spec.Kind, item)
        return false, "Stones"
    end
    local id = self.deps.guid()
    p.ledger.Out[id] = {
        Kind = spec.Kind, Item = item, StartBid = spec.StartBid, Hours = spec.Hours, Fee = spec.Fee, Paid = spec.Paid == true,
        Rarity = spec.Rarity, Value = spec.Value, Cap = spec.Cap, Show = spec.Show, SellerName = spec.SellerName, At = self.deps.now(),
    }
    AuctionCore.mark(p, id)
    step(self, "list.journaled")
    if not AuctionCore.confirm(p) then
        return true, id, "Pending"
    end
    step(self, "list.saved")
    local status = self:createListing(p, id)
    return true, id, if status == "Live" then "Live" else "Pending"
end

-- Makes the listing an Out entry stands for, if it isn't made yet. "Live" once the record exists (the entry is then dropped),
-- "Pending" if the store couldn't be reached (the pump tries again).
function AuctionCore:createListing(p, id)
    local entry = p.ledger.Out[id]
    if not entry or not AuctionCore.isConfirmed(p, id) then
        return "Pending"
    end
    local now = self.deps.now()
    local record
    local ok = self.deps.listings.update(id, function(old)
        record = nil
        -- (a stub, written by a bid's recovery that found no record: never one with a seller)
        if old ~= nil and not (old.State == "Void" and old.Seller == nil) then
            record = old
            return nil
        end
        local ends = now + entry.Hours * 3600
        record = {
            V = 1, Id = id, State = "Active", Seller = p.userId, SellerName = entry.SellerName, Kind = entry.Kind,
            Item = entry.Item, Show = entry.Show, Paid = entry.Paid, Rarity = entry.Rarity, Value = entry.Value, Cap = entry.Cap,
            StartBid = entry.StartBid, Fee = entry.Fee, Created = now, Ends = ends, FirstEnds = ends, High = nil, Bids = 0,
            Last = {}, Accepted = {}, Voided = if old then old.Voided else {}, Outbox = {},
        }
        return record
    end)
    if not ok or not record then
        return "Pending"
    end
    step(self, "list.created")
    if p.ledger.Out[id] then
        p.ledger.Out[id] = nil
        addPointer(p.ledger.Mine, id)
        p.saveSoon()
    end
    if record.State == "Active" then
        self.deps.index.put(AuctionCore.summary(record))
    end
    step(self, "list.indexed")
    return "Live"
end

-- ---------- bidding ----------
local REFUSALS = { Ended = true, Own = true, Top = true, Paid = true, Low = true, Cap = true, Missing = true }
AuctionCore.Refusals = REFUSALS

-- Why a bid can't be taken right now, or nil.
function AuctionCore:refusal(record, userId, amount, paidOk, now)
    if not record or record.State == "Void" then
        return "Missing"
    end
    if record.State ~= "Active" or now >= record.Ends then
        return "Ended"
    end
    if record.Seller == userId then
        return "Own"
    end
    if record.High and record.High.UserId == userId then
        return "Top"
    end
    if record.Paid and not paidOk then
        return "Paid"
    end
    if amount < self.deps.rules.minBid(record) then
        return "Low"
    end
    if amount > record.Cap then
        return "Cap"
    end
    return nil
end

-- Returns ok, why | outcome ("Accepted", "Refused" + why, or "Pending": it is settled once its save lands), the listing.
function AuctionCore:bid(p, listingId, amount)
    if not p.spend(amount, "AuctionBid") then
        return false, "Stones"
    end
    local id = self.deps.guid()
    p.ledger.Bids[id] = { L = listingId, Amount = amount, At = self.deps.now() }
    AuctionCore.mark(p, id)
    step(self, "bid.journaled")
    if not AuctionCore.confirm(p) then
        return true, "Pending"
    end
    step(self, "bid.saved")
    return true, self:applyBid(p, id)
end

-- Puts a journaled bid on its listing, or voids it there and gives the stones back. Returns "Accepted", "Refused" and why,
-- "Pending" (couldn't reach the store: the pump tries again) or "Done" (already settled).
function AuctionCore:applyBid(p, id)
    local entry = p.ledger.Bids[id]
    if not entry then
        return "Done"
    end
    if not AuctionCore.isConfirmed(p, id) then
        return "Pending"
    end
    local now = self.deps.now()
    local config = self.deps.config
    local outcome, why, record
    local ok = self.deps.listings.update(entry.L, function(old)
        outcome, why, record = nil, nil, old
        if old == nil then
            -- no such listing (never in normal play): a stub, so nothing can ever take this bid later
            outcome, why = "Refused", "Missing"
            return { V = 1, Id = entry.L, State = "Void", Voided = { [id] = true } }
        end
        old.Accepted = old.Accepted or {}
        old.Voided = old.Voided or {}
        if old.Accepted[id] then
            outcome = "Accepted"
            return nil
        end
        if old.Voided[id] then
            outcome, why = "Refused", "Ended"
            return nil
        end
        local reason = self:refusal(old, p.userId, entry.Amount, p.paidOk, now)
        if reason then
            old.Voided[id] = true
            outcome, why = "Refused", reason
            return old
        end
        local previous = old.High
        old.High = { UserId = p.userId, Name = p.name, Amount = entry.Amount, BidId = id, At = now }
        old.Accepted[id] = true
        old.Bids = (old.Bids or 0) + 1
        old.Last = old.Last or {}
        table.insert(old.Last, 1, { Name = p.name, Amount = entry.Amount, At = now })
        while #old.Last > LAST_SHOWN do
            table.remove(old.Last)
        end
        old.Outbox = old.Outbox or {}
        if previous then
            old.Outbox["R" .. previous.BidId] = { To = previous.UserId, Mail = {
                Why = "Outbid", L = old.Id, Stones = previous.Amount, Name = old.Show and old.Show.Name, Kind = old.Kind,
                PetId = old.Item and old.Item.PetId, WeaponId = old.Item and old.Item.WeaponId, At = now,
            } }
        end
        -- anti-snipe: a bid in the last SnipeWindow seconds moves the end to SnipeExtend after it, up to MaxExtension past the first
        if old.Ends - now < config.SnipeWindow then
            old.Ends = math.min(math.max(old.Ends, now + config.SnipeExtend), old.FirstEnds + config.MaxExtension)
        end
        outcome = "Accepted"
        return old
    end)
    if not ok or not outcome then
        return "Pending"
    end
    step(self, "bid.applied")
    if not p.ledger.Bids[id] then
        return "Done" -- (settled meanwhile by another call: never twice)
    end
    p.ledger.Bids[id] = nil
    if outcome == "Accepted" then
        addPointer(p.ledger.Watch, entry.L)
    else
        p.add(entry.Amount, "AuctionRefund") -- the bid and its stones come back together, in one step
    end
    p.saveSoon()
    step(self, "bid.settled")
    if outcome == "Accepted" and record then
        self.deps.index.put(AuctionCore.summary(record))
        self:flush(entry.L, record)
    end
    return outcome, why, record
end

-- ---------- cancelling ----------
-- Only the seller, only with no bids. The item comes back through the mailbox. Returns ok, why.
function AuctionCore:cancel(p, listingId)
    local now = self.deps.now()
    local why, record
    local ok = self.deps.listings.update(listingId, function(old)
        why, record = nil, old
        if old == nil or old.Seller ~= p.userId then
            why = "NotYours"
            return nil
        end
        if old.State ~= "Active" or now >= old.Ends then
            why = "Ended"
            return nil
        end
        if old.High then
            why = "HasBids"
            return nil
        end
        old.State = "Cancelled"
        old.Closed = now
        old.Outbox = old.Outbox or {}
        old.Outbox["I" .. listingId] = { To = old.Seller, Mail = {
            Why = "Returned", Reason = "Cancelled", L = listingId, Kind = old.Kind, Item = old.Item, Name = old.Show and old.Show.Name, At = now,
        } }
        return old
    end)
    if not ok then
        return false, "Busy"
    end
    if why then
        return false, why
    end
    step(self, "cancel.closed")
    self:flush(listingId, record)
    return true
end

-- ---------- settling: the end of an auction ----------
-- Closes an Active listing whose end has passed: the item to the top bidder and the price, less the tax, to the seller; with no
-- bids, the item back to the seller. Then delivers. Returns the record as it now stands (or nil if it couldn't be read).
function AuctionCore:settle(listingId)
    local now = self.deps.now()
    local record
    local ok = self.deps.listings.update(listingId, function(old)
        record = old
        if old == nil or old.State ~= "Active" or now < old.Ends + GRACE then
            return nil
        end
        local high = old.High
        old.Outbox = old.Outbox or {}
        local name = old.Show and old.Show.Name
        old.Outbox["I" .. listingId] = { To = if high then high.UserId else old.Seller, Mail = {
            Why = if high then "Won" else "Returned", Reason = if high then nil else "Unsold", L = listingId, Kind = old.Kind,
            Item = old.Item, Name = name, Price = high and high.Amount, At = now,
        } }
        if high then
            local tax = self.deps.rules.saleTax(high.Amount)
            old.Outbox["P" .. listingId] = { To = old.Seller, Mail = {
                Why = "Sold", L = listingId, Stones = high.Amount - tax, Price = high.Amount, Tax = tax, Kind = old.Kind,
                PetId = old.Item and old.Item.PetId, WeaponId = old.Item and old.Item.WeaponId, Name = name, Buyer = high.Name, At = now,
            } }
            old.Result = { Price = high.Amount, Tax = tax, Winner = high.UserId, WinnerName = high.Name }
            old.State = "Sold"
        else
            old.State = "Unsold"
        end
        old.Closed = now
        return old
    end)
    if not ok then
        return nil
    end
    step(self, "settle.closed")
    if record then
        self:flush(listingId, record)
    end
    return record
end

-- Hands a listing's outbox to the mailboxes, then crosses off what was delivered; a closed listing with nothing left to send
-- leaves the indexes. Its record stays for good, small (Accepted and Voided answer a crashed bid's recovery; the item is kept only
-- so My Auctions can still show what was sold).
function AuctionCore:flush(listingId, record)
    if not record then
        local ok, value = self.deps.listings.get(listingId)
        if not ok then
            return false
        end
        record = value
    end
    if not record then
        return true
    end
    local delivered, left = {}, 0
    for mailId, entry in record.Outbox or {} do
        if self:deliver(entry.To, mailId, entry.Mail) then
            delivered[mailId] = true
            self.deps.notify(entry.To)
        else
            left += 1
        end
        step(self, "flush.delivered")
    end
    if next(delivered) then
        local ok = self.deps.listings.update(listingId, function(old)
            if old == nil then
                return nil
            end
            for mailId in delivered do
                if old.Outbox then
                    old.Outbox[mailId] = nil
                end
            end
            record = old
            return old
        end)
        if not ok then
            return false
        end
        step(self, "flush.cleared")
    end
    if isClosed(record) and left == 0 and next(record.Outbox or {}) == nil then
        self.deps.index.remove(listingId)
    end
    return left == 0
end

-- One mail into a mailbox, once ever for its id. True when it is there (or was delivered and claimed before).
function AuctionCore:deliver(userId, mailId, mail)
    local now = self.deps.now()
    return self.deps.mail.update("M_" .. userId, function(old)
        old = old or {}
        old.Items = old.Items or {}
        old.Done = old.Done or {}
        if old.Items[mailId] or old.Done[mailId] then
            return nil
        end
        old.Items[mailId] = mail
        -- forget delivered ids after DONE_KEEP (a listing's outbox is emptied within minutes, so no copy can come that late)
        local done = {}
        for id, at in old.Done do
            if now - at > DONE_KEEP then
                old.Done[id] = nil
            else
                table.insert(done, { id, at })
            end
        end
        if #done > DONE_MOST then
            table.sort(done, function(a, b)
                return a[2] < b[2]
            end)
            for i = 1, #done - DONE_MOST do
                old.Done[done[i][1]] = nil
            end
        end
        return old
    end)
end

-- Finishes whatever an earlier visit to the store left undone for this listing: settles it if it has ended, delivers its
-- outbox. Returns the record (or nil).
function AuctionCore:touch(listingId, record)
    if not record then
        local ok, value = self.deps.listings.get(listingId)
        if not ok then
            return nil
        end
        record = value
    end
    if not record then
        return nil
    end
    if record.State == "Active" and self.deps.now() >= record.Ends + GRACE then
        return self:settle(listingId) or record
    end
    if next(record.Outbox or {}) then
        self:flush(listingId, record)
    elseif isClosed(record) then
        self.deps.index.remove(listingId)
    end
    return record
end

-- The ended listings the index knows of, settled. A listing whose end the anti-snipe rule moved gets its index entry put right.
function AuctionCore:sweep(count)
    local now = self.deps.now()
    local ids = self.deps.index.due(now - GRACE, count or 20) or {}
    local settled = 0
    for _, listingId in ids do
        local record = self:touch(listingId)
        if record and record.State == "Active" then
            self.deps.index.put(AuctionCore.summary(record))
        elseif record then
            settled += 1
        end
    end
    return settled, #ids
end

-- ---------- claiming the mailbox ----------
-- Gives the player their mail: items (when there's room) and stones, each with its Claimed entry, in one step; then a save;
-- only then the mailbox crosses them off. Returns the mails given now, and how many wait for room (nil if unreadable).
function AuctionCore:claim(p)
    local key = "M_" .. p.userId
    local ok, box = self.deps.mail.get(key)
    if not ok then
        return nil
    end
    box = box or {}
    local items = box.Items or {}
    local now = self.deps.now()
    local changed = false
    -- a Claimed entry whose mail the mailbox no longer holds: crossed off already
    for mailId in p.ledger.Claimed do
        if not items[mailId] and AuctionCore.isConfirmed(p, "C" .. mailId) then
            p.ledger.Claimed[mailId] = nil
            changed = true
        end
    end
    local order = {}
    for mailId, mail in items do
        table.insert(order, { id = mailId, mail = mail })
    end
    table.sort(order, function(a, b)
        return (a.mail.At or 0) < (b.mail.At or 0) or ((a.mail.At or 0) == (b.mail.At or 0) and a.id < b.id)
    end)
    local given, waiting = {}, 0
    for _, entry in order do
        if not p.ledger.Claimed[entry.id] then
            local mail = entry.mail
            local room = true
            if mail.Item then
                room = p.restoreItem(mail.Kind, mail.Item)
            end
            if room then
                if mail.Stones and mail.Stones > 0 then
                    p.add(mail.Stones, "Auction" .. tostring(mail.Why))
                end
                p.ledger.Claimed[entry.id] = now
                AuctionCore.mark(p, "C" .. entry.id)
                table.insert(given, mail)
            else
                waiting += 1
            end
        end
    end
    if #given > 0 then
        step(self, "claim.granted")
    end
    local toCross = {}
    local function collect()
        table.clear(toCross)
        for mailId in p.ledger.Claimed do
            if items[mailId] and AuctionCore.isConfirmed(p, "C" .. mailId) then
                toCross[mailId] = true
            end
        end
    end
    if #given > 0 then
        if not AuctionCore.confirm(p) then
            return given, waiting -- given in memory; crossed off once a save holds them
        end
        step(self, "claim.saved")
    end
    collect()
    if next(toCross) then
        local crossed = self.deps.mail.update(key, function(old)
            if old == nil or old.Items == nil then
                return nil
            end
            old.Done = old.Done or {}
            for mailId in toCross do
                if old.Items[mailId] then
                    old.Items[mailId] = nil
                    old.Done[mailId] = now
                end
            end
            return old
        end)
        step(self, "claim.crossed")
        if crossed then
            for mailId in toCross do
                p.ledger.Claimed[mailId] = nil
            end
            changed = true
        end
    end
    if changed then
        p.saveSoon()
    end
    return given, waiting
end

-- Everything the journal still holds, finished: called on joining, after each action and every so often. Never acts on an entry
-- no save holds yet.
function AuctionCore:pump(p)
    if next(p.pending) and not AuctionCore.confirm(p) then
        return false
    end
    for id in table.clone(p.ledger.Out) do
        self:createListing(p, id)
    end
    for id in table.clone(p.ledger.Bids) do
        self:applyBid(p, id)
    end
    return true
end

return AuctionCore
