-- The Auction House: the Market building on the Merchants' Terrace (its prompt's "Shop" attribute is still "Marketplace"), one
-- auction house shared by every server (vault: Auction House Design 2026-11-16; rules: shared/AuctionRules, GameConfig.AuctionHouse;
-- the transactions: AuctionCore; the stores: AuctionStores; the save's journal: AuctionLedger).
--
-- AuctionEvent, client to server (every one checked and throttled here, and the money parts again inside AuctionCore's writes):
--   "Browse" { Kind = "All"|"Pet"|"Weapon", Rarity = "All"|<rarity>, Sort = "Ending"|"Low"|"High"|"Rare"|"New", Page }
--   "Detail" listingId        "Mine"        "Sellable"        "Claim"
--   "List" { Kind, InstanceId, StartBid, Hours }     "Bid" listingId, amount     "Cancel" listingId
-- Server to client:
--   "Open" state               the prompt was used: { Can, Why, Config }
--   "Browse" { Items, Page, Pages, Total }     "Detail" listing     "Mine" { Selling, Bidding, Waiting }     "Sellable" items
--   "Result" ok, text, { Action, ListingId }   a list, bid or cancel answered
--   "Mail" { mails }           mail given: outbid refunds, wins, sales, items back (the client shows each)
--   "Busy" text                the stores are slow: try again
local Players = game:GetService("Players")
local PolicyService = game:GetService("PolicyService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")
local TextService = game:GetService("TextService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local AuctionRules = require(ReplicatedStorage:WaitForChild("AuctionRules"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Server = script.Parent.Parent
local PlayerData = require(Server:WaitForChild("Data"):WaitForChild("PlayerData"))
local PetInventory = require(Server:WaitForChild("Pets"):WaitForChild("PetInventory"))
local WeaponInventory = require(Server:WaitForChild("Shop"):WaitForChild("WeaponInventory"))
local Wallet = require(Server:WaitForChild("Shop"):WaitForChild("Wallet"))
local MovementGuard = require(Server:WaitForChild("Security"):WaitForChild("MovementGuard"))
local WorldConfig = require(Server:WaitForChild("World"):WaitForChild("WorldConfig"))
local AuctionCore = require(script.Parent:WaitForChild("AuctionCore"))
local AuctionChecks = require(script.Parent:WaitForChild("AuctionChecks"))
local AuctionLedger = require(script.Parent:WaitForChild("AuctionLedger"))
local AuctionStores = require(script.Parent:WaitForChild("AuctionStores"))

local CONFIG = AuctionRules.Config
local Event = RemoteEvents.AuctionEvent

local REQUEST_GAP = 0.4      -- seconds between any two requests
local ACT_GAP = 2            -- between two lists, bids or cancels
local ACT_PER_MINUTE = 12
local PUMP_EVERY = 15        -- seconds: each player's journal finished, if anything is in it
local CLAIM_EVERY = 60       -- their mailbox read
local SWEEP_EVERY = 30       -- the ended listings settled (with a little jitter, so servers don't all sweep at once)
local BROWSE_FRESH = 10      -- seconds a browse refresh is good for while someone has the window open
local BROWSE_IDLE = 60       -- and while nobody does
local RECORD_FRESH = 5       -- seconds a listing read is reused
local POINTER_KEEP = 86400   -- seconds a closed listing stays under My Auctions

local players = {} -- [player] = { p = the AuctionCore player, busy, lastRequest, acts = { times }, lastClaim, waiting, claimWanted }

local core = AuctionCore.new({
    now = os.time,
    guid = function()
        return HttpService:GenerateGUID(false)
    end,
    listings = AuctionStores.listings,
    mail = AuctionStores.mail,
    index = AuctionStores.index,
    notify = function(userId)
        -- (someone in this server: claimed on the next beat; anyone else hears it from MessagingService)
        local here = Players:GetPlayerByUserId(userId)
        if here and players[here] then
            players[here].claimWanted = true
        else
            AuctionStores.notify(userId)
        end
    end,
    rules = { minBid = AuctionRules.minBid, saleTax = AuctionRules.saleTax },
    config = CONFIG,
    step = nil,
})

-- ---------- each player ----------

local function rankName(player)
    return Ranks.getPlayerRankName(player)
end

local function creatorPet(player, petId)
    local creators = GameConfig.CreatorPets
    return table.find(creators.UserIds, player.UserId) ~= nil and table.find(creators.PetIds, petId) ~= nil
end

local function makeP(player, paidOk)
    local p = { userId = player.UserId, name = player.DisplayName, paidOk = paidOk, ledger = AuctionLedger.get(player), pending = {} }
    function p.takeItem(kind, instanceId)
        if kind == "Pet" then
            local snapshot = PetInventory.getSnapshot(player)
            if not snapshot or #snapshot.Pets <= 1 then
                return nil -- (never their last pet: checked again here, after any wait)
            end
            local record = PetInventory.takeRecord(player, instanceId)
            if record then
                PetInventory.publish(player)
            end
            return record
        elseif kind == "Weapon" then
            return WeaponInventory.take(player, instanceId)
        end
        return nil
    end
    function p.restoreItem(kind, record)
        if kind == "Pet" then
            local ok = PetInventory.restore(player, record)
            if ok then
                PetInventory.publish(player)
            end
            return ok
        elseif kind == "Weapon" then
            return WeaponInventory.restore(player, record)
        end
        return false
    end
    function p.spend(n, why)
        return Wallet.spend(player, n, why or "Auction", "Auction")
    end
    function p.add(n, why)
        Wallet.add(player, n, why or "Auction", "Auction")
    end
    function p.saveConfirmed()
        return player.Parent == Players and PlayerData.canSave(player) and PlayerData.saveConfirmed(player)
    end
    function p.saveSoon()
        PlayerData.saveSoon(player)
    end
    return p
end

-- One auction step at a time per player: a request that finds one running is told to wait.
local function withLock(player, fn)
    local state = players[player]
    if not state or state.busy then
        return false
    end
    state.busy = true
    local ok, err = pcall(fn, state)
    state.busy = false
    if not ok then
        warn("AuctionService: " .. tostring(err))
    end
    return true
end

-- ---------- reading listings ----------
local records = {} -- [id] = { at = os.clock(), record }

local function readRecord(id, fresh)
    local cached = records[id]
    if cached and not fresh and os.clock() - cached.at < RECORD_FRESH then
        return true, cached.record
    end
    local ok, record = AuctionStores.listings.get(id)
    if ok then
        records[id] = { at = os.clock(), record = record }
    end
    return ok, record
end

-- ---------- the browse list (one per server) ----------
local browse = { at = -math.huge, list = {}, byId = {}, refreshing = false, ok = true }
local windowOpen = {} -- [player] = true while their window is open (as far as the server knows: they browsed lately)

AuctionStores.onIndexChanged = function(id, summary)
    if summary then
        browse.byId[id] = summary
    else
        browse.byId[id] = nil
    end
    local copy = {}
    for _, entry in browse.byId do
        table.insert(copy, entry)
    end
    browse.list = copy
    records[id] = nil
end

local settling = {} -- [id] = true while this server settles it

local function settleSoon(id)
    if settling[id] then
        return
    end
    settling[id] = true
    task.spawn(function()
        pcall(function()
            core:touch(id)
        end)
        records[id] = nil
        settling[id] = nil
    end)
end

local function refreshBrowse(force)
    local fresh = if next(windowOpen) then BROWSE_FRESH else BROWSE_IDLE
    if browse.refreshing or (not force and os.clock() - browse.at < fresh) then
        return
    end
    browse.refreshing = true
    local ok, found = AuctionStores.browseAll()
    browse.refreshing = false
    browse.at = os.clock()
    browse.ok = ok
    if not ok then
        return
    end
    local byId, list = {}, {}
    local now = os.time()
    local ended = 0
    for _, summary in found do
        if summary.State == "Active" then
            byId[summary.Id] = summary
            table.insert(list, summary)
            if summary.End + 2 < now and ended < 5 then
                ended += 1
                settleSoon(summary.Id) -- (a listing the sweeper hasn't reached: settled by whoever sees it)
            end
        end
    end
    browse.byId, browse.list = byId, list
end

local SORTS = {
    Ending = function(a, b)
        return a.End < b.End
    end,
    Low = function(a, b)
        return a.Pr < b.Pr or (a.Pr == b.Pr and a.End < b.End)
    end,
    High = function(a, b)
        return a.Pr > b.Pr or (a.Pr == b.Pr and a.End < b.End)
    end,
    Rare = function(a, b)
        local ra, rb = AuctionRules.rarityRank(a.R), AuctionRules.rarityRank(b.R)
        return ra > rb or (ra == rb and (a.Pr > b.Pr or (a.Pr == b.Pr and a.End < b.End)))
    end,
    New = function(a, b)
        return (a.Cr or 0) > (b.Cr or 0)
    end,
}

local function browsePage(query)
    query = if typeof(query) == "table" then query else {}
    local kind = if query.Kind == "Pet" or query.Kind == "Weapon" then query.Kind else "All"
    local rarity = if typeof(query.Rarity) == "string" and (AuctionRules.rarityRank(query.Rarity) > 0 or query.Rarity == "Weapon")
        then query.Rarity else "All"
    local sort = if typeof(query.Sort) == "string" and SORTS[query.Sort] then query.Sort else "Ending"
    local now = os.time()
    local shown = {}
    for _, summary in browse.list do
        if summary.End > now and (kind == "All" or summary.K == kind) and (rarity == "All" or summary.R == rarity) then
            table.insert(shown, summary)
        end
    end
    table.sort(shown, SORTS[sort])
    local pages = math.max(1, math.ceil(#shown / CONFIG.PageSize))
    local page = if typeof(query.Page) == "number" and query.Page == query.Page then math.clamp(math.floor(query.Page), 1, pages) else 1
    local items = {}
    for i = (page - 1) * CONFIG.PageSize + 1, math.min(#shown, page * CONFIG.PageSize) do
        table.insert(items, shown[i])
    end
    return { Items = items, Page = page, Pages = pages, Total = #shown, Ok = browse.ok }
end

-- ---------- the player's own: what they sell and bid on ----------
local function activeListings(state)
    local count = AuctionCore.count(state.p.ledger.Out)
    for _, id in state.p.ledger.Mine do
        local cached = records[id]
        local record = cached and cached.record
        if not record or record.State == "Active" then
            count += 1
        end
    end
    return count
end

local function bidOn(state)
    local count = AuctionCore.count(state.p.ledger.Bids)
    for _, id in state.p.ledger.Watch do
        local cached = records[id]
        local record = cached and cached.record
        if not record or record.State == "Active" then
            count += 1
        end
    end
    return count
end

-- Reads each of the player's listings and bids, settles what has ended and forgets what closed long ago.
local function refreshPointers(state)
    local ledger = state.p.ledger
    local now = os.time()
    for _, list in { ledger.Mine, ledger.Watch } do
        for _, id in table.clone(list) do
            local summary = browse.byId[id]
            if not (summary and summary.End > now) or not records[id] then
                local ok, record = readRecord(id)
                if ok then
                    if record == nil or record.State == "Void" then
                        AuctionCore.removePointer(list, id)
                    elseif record.State == "Active" and now >= record.Ends + 2 then
                        settleSoon(id)
                    elseif record.State ~= "Active" then
                        if next(record.Outbox or {}) then
                            settleSoon(id)
                        elseif now - (record.Closed or now) > POINTER_KEEP then
                            AuctionCore.removePointer(list, id)
                        end
                    end
                end
            end
        end
    end
end

local function statusOf(record, userId)
    if not record then
        return nil
    end
    local mine = record.Seller == userId
    if record.State == "Active" then
        if mine then
            return if record.High then "Bid on" else "No bids yet"
        end
        return if record.High and record.High.UserId == userId then "Winning" else "Outbid"
    elseif record.State == "Sold" then
        if mine then
            return "Sold"
        end
        return if record.Result and record.Result.Winner == userId then "Won" else "Lost"
    elseif record.State == "Unsold" then
        return "No bids: back to you"
    elseif record.State == "Cancelled" then
        return "Cancelled"
    end
    return nil
end

local function mineReply(player, state)
    local ledger = state.p.ledger
    local userId = player.UserId
    local selling, bidding = {}, {}
    for _, entry in ledger.Out do
        local shown = { K = entry.Kind, P = entry.Item.PetId, W = entry.Item.WeaponId, R = entry.Rarity, S = entry.Item.Size,
            Lv = entry.Item.Level, E = entry.Item.Element, N = entry.Show and entry.Show.Name, Pr = entry.StartBid, B = 0 }
        shown.Status = "Getting ready"
        table.insert(selling, shown)
    end
    for _, entry in ledger.Bids do
        local summary = browse.byId[entry.L]
        local shown = if summary then table.clone(summary) else { Id = entry.L }
        shown.Status, shown.Yours = "Checking your bid", entry.Amount
        table.insert(bidding, shown)
    end
    for _, pair in { { ledger.Mine, selling }, { ledger.Watch, bidding } } do
        for _, id in pair[1] do
            local cached = records[id]
            local record = cached and cached.record
            local summary = browse.byId[id]
            if record and record.Seller then
                local shown = AuctionCore.summary(record)
                if summary and summary.State == "Active" and (summary.B or 0) > (shown.B or 0) then
                    shown = table.clone(summary) -- (the browse copy is newer)
                end
                if not shown.K and summary then
                    shown = table.clone(summary)
                end
                shown.Status = statusOf(record, userId)
                shown.Result = record.Result
                table.insert(pair[2], shown)
            elseif summary then
                local shown = table.clone(summary)
                shown.Status = if pair[1] == ledger.Mine then (if (summary.B or 0) > 0 then "Bid on" else "No bids yet")
                    elseif summary.Hb == userId then "Winning" else "Outbid"
                table.insert(pair[2], shown)
            end
        end
    end
    return { Selling = selling, Bidding = bidding, Waiting = state.waiting or 0 }
end

local function sellable(player, state)
    local items = {}
    local snapshot = PetInventory.getSnapshot(player)
    local weapons = WeaponInventory.snapshot(player)
    local pets = snapshot and snapshot.Pets or {}
    local full = activeListings(state) >= CONFIG.MaxListings
    for _, pet in pets do
        local why = AuctionChecks.item({ kind = "Pet", pet = pet, petCount = #pets, paidOk = state.p.paidOk,
            isCreatorPet = creatorPet(player, pet.PetId) })
        local low, high = AuctionRules.startRange("Pet", pet)
        table.insert(items, { Kind = "Pet", InstanceId = pet.InstanceId, PetId = pet.PetId, Level = PetRules.level(pet),
            Size = PetRules.size(pet), Worth = PetRules.worth(pet), Why = why, Value = AuctionRules.value("Pet", pet), Low = low,
            High = high, Rarity = AuctionRules.rarity("Pet", pet) })
    end
    for _, weapon in weapons and weapons.Weapons or {} do
        local why = AuctionChecks.item({ kind = "Weapon", weapon = weapon, equippedWeapon = weapons.Equipped })
        local low, high = AuctionRules.startRange("Weapon", weapon)
        table.insert(items, { Kind = "Weapon", InstanceId = weapon.InstanceId, WeaponId = weapon.WeaponId, Element = weapon.Element,
            Name = weapon.Name, Why = why, Value = AuctionRules.value("Weapon", weapon), Low = low, High = high, Rarity = "Weapon" })
    end
    return { Items = items, Full = full, Stones = Wallet.balance(player) }
end

local function sendMine(player, state)
    Event:FireClient(player, "Mine", mineReply(player, state))
end

local function sendSellable(player, state)
    Event:FireClient(player, "Sellable", sellable(player, state))
end

-- ---------- the mailbox ----------
local function claimNow(player, state)
    local given, waiting = core:claim(state.p)
    state.lastClaim = os.clock()
    if given == nil then
        return
    end
    state.waiting = waiting
    if #given > 0 then
        local shown = {}
        for _, mail in given do
            table.insert(shown, { Why = mail.Why, Reason = mail.Reason, Kind = mail.Kind, Stones = mail.Stones, Price = mail.Price,
                Tax = mail.Tax, Name = mail.Name, Buyer = mail.Buyer,
                PetId = mail.PetId or (mail.Item and mail.Item.PetId), WeaponId = mail.WeaponId or (mail.Item and mail.Item.WeaponId) })
        end
        Event:FireClient(player, "Mail", shown)
    end
    if #given > 0 or waiting > 0 then
        PlayerData.saveSoon(player)
    end
end

-- ---------- where the Auction House is ----------
local function prompt()
    local spot = workspace:FindFirstChild(WorldConfig.FolderName)
    spot = spot and spot:FindFirstChild(WorldConfig.StartIsland)
    spot = spot and spot:FindFirstChild("Shops")
    spot = spot and spot:FindFirstChild("Marketplace")
    return spot and spot:FindFirstChild("Prompt")
end

local function nearAuctionHouse(player)
    local spot = prompt()
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    return spot ~= nil and root ~= nil and not MovementGuard.isSuspect(player) and (root.Position - spot.Position).Magnitude <= CONFIG.Reach
end

local function openState(player)
    local can, why = AuctionRules.canUse(rankName(player), player.AccountAge)
    return { Can = can, Why = why, PaidOk = players[player] and players[player].p.paidOk, Config = {
        Hours = CONFIG.Hours, MaxListings = CONFIG.MaxListings, MaxBidOn = CONFIG.MaxBidOn, SaleTax = CONFIG.SaleTax,
        FeeShare = CONFIG.ListingFee.Share, FeeMin = CONFIG.ListingFee.Min, PageSize = CONFIG.PageSize, MinRaise = CONFIG.MinRaise,
    } }
end

-- ---------- the actions ----------
local function result(player, ok, text, extra)
    Event:FireClient(player, "Result", ok, text, extra)
end

local function filteredName(player, name)
    if typeof(name) ~= "string" or name == "" then
        return nil
    end
    local ok, filtered = pcall(function()
        return TextService:FilterStringAsync(name, player.UserId, Enum.TextFilterContext.PublicChat):GetNonChatStringForBroadcastAsync()
    end)
    return if ok and filtered == name then name else nil -- (anything changed or unchecked: shown by the weapon's own name)
end

local actions = {}

function actions.List(player, state, request)
    if typeof(request) ~= "table" then
        return
    end
    if not nearAuctionHouse(player) then
        return result(player, false, "Walk back to the Auction House.")
    end
    local kind = request.Kind
    local instanceId = request.InstanceId
    if (kind ~= "Pet" and kind ~= "Weapon") or typeof(instanceId) ~= "string" or #instanceId > 64 then
        return result(player, false, "Choose a pet or a weapon to sell.")
    end
    refreshPointers(state)
    local snapshot = PetInventory.getSnapshot(player)
    local weapons = WeaponInventory.snapshot(player)
    local facts = {
        kind = kind, rankName = rankName(player), ageDays = player.AccountAge, paidOk = state.p.paidOk,
        activeListings = activeListings(state), startBid = request.StartBid, hours = request.Hours, stones = Wallet.balance(player),
        petCount = snapshot and #snapshot.Pets or 0, equippedWeapon = weapons and weapons.Equipped,
    }
    if kind == "Pet" then
        facts.pet = PetInventory.get(player, instanceId)
        facts.isCreatorPet = facts.pet ~= nil and creatorPet(player, facts.pet.PetId)
    else
        facts.weapon = WeaponInventory.get(player, instanceId)
    end
    local ok, info = AuctionChecks.list(facts)
    if not ok then
        return result(player, false, info)
    end
    local show = nil
    if kind == "Weapon" and info.Item.Name then
        show = { Name = filteredName(player, info.Item.Name) } -- (yields: the item is checked again as it is taken)
    end
    local listed, idOrWhy, status = core:list(state.p, {
        Kind = kind, InstanceId = instanceId, StartBid = request.StartBid, Hours = request.Hours, Fee = info.Fee, Paid = info.Paid,
        Rarity = info.Rarity, Value = info.Value, Cap = info.Cap, Show = show, SellerName = player.DisplayName,
    })
    if not listed then
        return result(player, false, if idOrWhy == "Stones" then "You need more Spirit Stones for the listing fee."
            else "That item can't be put up right now.")
    end
    local name = AuctionRules.itemName(kind, info.Item)
    result(player, true, if status == "Live"
        then "Your " .. name .. " is up for auction! Listing fee: " .. NumberFormat.compact(info.Fee) .. " Spirit Stones."
        else "Your " .. name .. " is being put up. It will show in a moment.", { Action = "List", ListingId = idOrWhy })
end

function actions.Bid(player, state, listingId, amount)
    if typeof(listingId) ~= "string" or #listingId > 64 then
        return
    end
    if not nearAuctionHouse(player) then
        return result(player, false, "Walk back to the Auction House.")
    end
    local ok, record = readRecord(listingId, true)
    if not ok then
        return result(player, false, "The Auction House is busy. Try again in a moment.")
    end
    local fine, why = AuctionChecks.bid({
        rankName = rankName(player), ageDays = player.AccountAge, paidOk = state.p.paidOk, userId = player.UserId, record = record,
        amount = amount, stones = Wallet.balance(player), bidOn = bidOn(state),
        watching = table.find(state.p.ledger.Watch, listingId) ~= nil, now = os.time(),
    })
    if not fine then
        return result(player, false, why)
    end
    local placed, outcome, refusal, after = core:bid(state.p, listingId, amount)
    records[listingId] = nil
    local name = AuctionRules.itemName(record.Kind, record.Item)
    if not placed then
        return result(player, false, "You need more Spirit Stones.")
    elseif outcome == "Accepted" then
        local extended = after and after.Ends > record.Ends
        result(player, true, "You have the top bid on the " .. name .. ": " .. NumberFormat.compact(amount) .. " Spirit Stones."
            .. (if extended then " The auction now ends a minute later." else ""), { Action = "Bid", ListingId = listingId })
    elseif outcome == "Refused" then
        result(player, false, AuctionChecks.refusalText(refusal, after) .. " Your stones are back.", { Action = "Bid", ListingId = listingId })
    else
        result(player, true, "Your bid is being checked. You'll see it in a moment.", { Action = "Bid", ListingId = listingId })
    end
end

function actions.Cancel(player, state, listingId)
    if typeof(listingId) ~= "string" or not table.find(state.p.ledger.Mine, listingId) then
        return result(player, false, "That isn't one of your auctions.")
    end
    if not nearAuctionHouse(player) then
        return result(player, false, "Walk back to the Auction House.")
    end
    local ok, why = core:cancel(state.p, listingId)
    records[listingId] = nil
    if not ok then
        return result(player, false, if why == "HasBids" then "Someone has bid on it: it can't be taken back now."
            elseif why == "Ended" then "This auction has ended." elseif why == "Busy" then "The Auction House is busy. Try again in a moment."
            else "That isn't one of your auctions.")
    end
    claimNow(player, state)
    result(player, true, "Auction cancelled. Your item is back (the listing fee is kept).", { Action = "Cancel", ListingId = listingId })
end

local reads = {}

function reads.Browse(player, _, query)
    windowOpen[player] = os.clock()
    refreshBrowse(false)
    Event:FireClient(player, "Browse", browsePage(query))
end

function reads.Detail(player, state, listingId)
    if typeof(listingId) ~= "string" or #listingId > 64 then
        return
    end
    local ok, record = readRecord(listingId)
    if not ok then
        return Event:FireClient(player, "Busy", "The Auction House is busy. Try again in a moment.")
    end
    if not record or not record.Seller then
        return Event:FireClient(player, "Detail", { Id = listingId, Gone = true })
    end
    if (record.State == "Active" and os.time() >= record.Ends + 2) or next(record.Outbox or {}) then
        settleSoon(listingId)
    end
    local shown = AuctionCore.public(record)
    if not shown.K then
        local summary = browse.byId[listingId]
        shown = if summary then table.clone(summary) else shown -- (a tombstone: what the browse copy had)
        shown.Result = record.Result
        shown.State = record.State
    end
    shown.MinBid = AuctionRules.minBid(record)
    shown.Mine = record.Seller == player.UserId
    shown.Top = record.High ~= nil and record.High.UserId == player.UserId
    local can, why = AuctionRules.canUse(rankName(player), player.AccountAge)
    if can and record.Item then
        can, why = AuctionRules.canOwn(rankName(player), record.Kind, record.Item)
    end
    if can and record.Paid and not state.p.paidOk then
        can, why = false, "Beasts from the Exclusive Egg can't be traded where you live."
    end
    shown.CanBid, shown.WhyNot = can, why
    Event:FireClient(player, "Detail", shown)
end

function reads.Mine(player, state)
    refreshPointers(state)
    sendMine(player, state)
end

function reads.Sellable(player, state)
    sendSellable(player, state)
end

function reads.Claim(player, state)
    claimNow(player, state)
    sendMine(player, state)
end

Event.OnServerEvent:Connect(function(player, action, ...)
    local state = players[player]
    if not state or typeof(action) ~= "string" then
        return
    end
    local now = os.clock()
    if now - (state.lastRequest or 0) < REQUEST_GAP then
        return
    end
    state.lastRequest = now
    local args = table.pack(...)
    if actions[action] then
        -- a list, a bid or a cancel: one at a time, ACT_GAP apart, ACT_PER_MINUTE a minute
        local acts = state.acts
        while acts[1] and now - acts[1] > 60 do
            table.remove(acts, 1)
        end
        if (acts[#acts] and now - acts[#acts] < ACT_GAP) or #acts >= ACT_PER_MINUTE then
            return result(player, false, "Slow down a little, then try again.")
        end
        if not AuctionRules.canUse(rankName(player), player.AccountAge) then
            return result(player, false, (select(2, AuctionRules.canUse(rankName(player), player.AccountAge))))
        end
        table.insert(acts, now)
        local ran = withLock(player, function(s)
            actions[action](player, s, table.unpack(args, 1, args.n))
            core:pump(s.p)
        end)
        if not ran then
            return result(player, false, "One moment: your last step is still going through.")
        end
        if players[player] then
            sendMine(player, players[player])
            sendSellable(player, players[player])
        end
    elseif reads[action] then
        if action == "Claim" or action == "Mine" then
            local ran = withLock(player, function(s)
                reads[action](player, s, table.unpack(args, 1, args.n))
            end)
            if not ran and action == "Claim" then
                Event:FireClient(player, "Busy", "One moment, please.") -- (a Mine asked meanwhile: the next look answers it)
            end
        else
            task.spawn(function()
                local ok, err = pcall(reads[action], player, state, table.unpack(args, 1, args.n))
                if not ok then
                    warn("AuctionService: " .. tostring(err))
                end
            end)
        end
    end
end)

-- ---------- the prompt: the Market's, which now opens the Auction House ----------
local function watchPrompt(holder)
    local proximity = holder and holder:FindFirstChildOfClass("ProximityPrompt")
    if not proximity then
        return
    end
    -- (the place's prompt and sign are set to these too; set here as well, so an older saved place still says it)
    proximity.ObjectText = "Auction House"
    proximity.ActionText = "Open"
    local model = holder.Parent
    local sign = model and model:FindFirstChild("Sign")
    local label = sign and sign:FindFirstChild("Text", true)
    if label and label:IsA("TextLabel") then
        label.Text = "Auction House"
    end
    proximity.Triggered:Connect(function(player)
        local state = players[player]
        if not state then
            return
        end
        windowOpen[player] = os.clock()
        Event:FireClient(player, "Open", openState(player))
        task.spawn(function()
            refreshBrowse(false)
            Event:FireClient(player, "Browse", browsePage(nil))
            withLock(player, function(s)
                refreshPointers(s)
                claimNow(player, s)
                sendMine(player, s)
                sendSellable(player, s)
            end)
        end)
    end)
end

task.spawn(function()
    local island = workspace:WaitForChild(WorldConfig.FolderName):WaitForChild(WorldConfig.StartIsland)
    local shops = island:WaitForChild("Shops", 30)
    local market = shops and shops:WaitForChild("Marketplace", 30)
    local holder = market and market:WaitForChild("Prompt", 30)
    if not holder then
        warn("AuctionService: " .. WorldConfig.StartIsland .. " has no Shops.Marketplace.Prompt (WorldBuilder.buildShops)")
        return
    end
    watchPrompt(holder)
end)

-- ---------- joining and leaving ----------
local function checkPolicy(player)
    for try = 1, 3 do
        local ok, info = pcall(PolicyService.GetPolicyInfoForPlayerAsync, PolicyService, player)
        if ok and typeof(info) == "table" then
            return info.IsPaidItemTradingAllowed == true
        end
        if player.Parent ~= Players then
            return false
        end
        task.wait(try)
    end
    return false -- (no answer: paid items stay closed to them, everything else is open)
end

local function setupPlayer(player)
    local paidOk = nil
    task.spawn(function()
        paidOk = checkPolicy(player)
    end)
    local progress, isNewPlayer = PlayerData.waitForData(player)
    if not progress or player.Parent ~= Players then
        return
    end
    AuctionLedger.setupPlayer(player, if isNewPlayer then nil else progress)
    -- the parts an auction moves: set up by their own services alongside this one
    local deadline = os.clock() + 30
    while not (PetInventory.isSetUp(player) and Wallet.exportData(player) ~= nil and WeaponInventory.snapshot(player) ~= nil
        and paidOk ~= nil) and player.Parent == Players and os.clock() < deadline do
        task.wait(0.25)
    end
    if player.Parent ~= Players or not PetInventory.isSetUp(player) or Wallet.exportData(player) == nil then
        return
    end
    players[player] = { p = makeP(player, paidOk == true), acts = {}, lastClaim = -math.huge, waiting = 0 }
    -- whatever a last visit left in flight (a crash, a server shut down mid-step), finished now; then their mail
    withLock(player, function(state)
        core:pump(state.p)
        claimNow(player, state)
        refreshPointers(state)
    end)
end

Players.PlayerAdded:Connect(setupPlayer)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
Players.PlayerRemoving:Connect(function(player)
    players[player] = nil
    windowOpen[player] = nil
end)

-- ---------- mail from other servers ----------
AuctionStores.subscribe(function(userId)
    local player = Players:GetPlayerByUserId(userId)
    local state = player and players[player]
    if state then
        state.claimWanted = true
    end
end)

-- ---------- the background: journals, mailboxes, the sweeper ----------
task.spawn(function()
    local lastPump = {}
    while true do
        task.wait(2)
        local now = os.clock()
        for player, state in players do
            if windowOpen[player] and now - windowOpen[player] > 120 then
                windowOpen[player] = nil
            end
            local journal = next(state.p.ledger.Out) or next(state.p.ledger.Bids) or next(state.p.pending)
            local wantClaim = state.claimWanted or now - state.lastClaim > CLAIM_EVERY
            if (journal and now - (lastPump[player] or 0) > PUMP_EVERY) or wantClaim then
                task.spawn(withLock, player, function(s)
                    if journal then
                        lastPump[player] = os.clock()
                        core:pump(s.p)
                    end
                    if wantClaim then
                        s.claimWanted = false
                        claimNow(player, s)
                    end
                end)
            end
        end
        for player in lastPump do
            if not players[player] then
                lastPump[player] = nil
            end
        end
    end
end)

task.spawn(function()
    task.wait(math.random() * SWEEP_EVERY)
    while true do
        if next(players) then
            local ok, err = pcall(function()
                core:sweep(20)
            end)
            if not ok then
                warn("AuctionService: sweep failed: " .. tostring(err))
            end
            refreshBrowse(false)
        end
        for id, cached in records do -- (reads kept a few minutes at most: the cache never grows with every listing ever seen)
            if os.clock() - cached.at > 300 then
                records[id] = nil
            end
        end
        task.wait(SWEEP_EVERY * (0.8 + math.random() * 0.4))
    end
end)
