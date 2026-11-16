-- The Auction House's stores, shared by every server (vault: Auction House Design 2026-11-16):
--   listings  DataStore "AuctionListings", one key per listing (UpdateAsync: the single source of truth, never deleted)
--   mail      DataStore "AuctionMail", one key per player ("M_<userId>")
--   index     OrderedDataStore "AuctionEnds" (listing id -> its end: what to settle next, durable) and MemoryStore SortedMap
--             "AuctionBrowse" (listing id -> a summary, sorted by end: browsing; may lag, never trusted for money)
--   notify    MessagingService topic "AuctionMail": "this player has mail"
-- In Studio every name starts with the StudioTestSave name (or "Studio"), so a test never touches real auctions.
-- Each call checks the request budget first (keeping RESERVE for the player saves) and retries with backoff; a call that still
-- fails returns false, and the caller says the Auction House is busy.
local DataStoreService = game:GetService("DataStoreService")
local MemoryStoreService = game:GetService("MemoryStoreService")
local MessagingService = game:GetService("MessagingService")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local AuctionStores = {}

local RESERVE = 10                  -- requests a minute left for PlayerData's saves
local TRIES = 3
local BACKOFF = { 1, 2, 4 }
local BUDGET_WAIT = 3               -- seconds to wait for budget before giving up
local BROWSE_MAX = 1000             -- listings one browse refresh reads at most (5 MemoryStore pages)
local MAX_TTL = 45 * 86400          -- MemoryStore's longest expiration

local prefix = ""
if RunService:IsStudio() then
    local name = ServerStorage:GetAttribute("StudioTestSave")
    prefix = (if typeof(name) == "string" and name ~= "" then name elseif name then "StudioTestSave" else "Studio") .. "_"
end
AuctionStores.prefix = prefix

local function warnOnce(key, message)
    AuctionStores.warned = AuctionStores.warned or {}
    if not AuctionStores.warned[key] then
        AuctionStores.warned[key] = true
        warn("AuctionStores: " .. message)
    end
end

local function open(kind, name)
    local ok, store = pcall(function()
        if kind == "ordered" then
            return DataStoreService:GetOrderedDataStore(prefix .. name)
        elseif kind == "sorted" then
            return MemoryStoreService:GetSortedMap(prefix .. name)
        end
        return DataStoreService:GetDataStore(prefix .. name)
    end)
    if not ok then
        warnOnce(name, "can't open " .. name .. ": " .. tostring(store))
        return nil
    end
    return store
end

local listingStore = open("data", "AuctionListings")
local mailStore = open("data", "AuctionMail")
local endStore = open("ordered", "AuctionEnds")
local browseMap = open("sorted", "AuctionBrowse")
local MAIL_TOPIC = prefix .. "AuctionMail"

local function hasBudget(requestType)
    local deadline = os.clock() + BUDGET_WAIT
    while true do
        local ok, budget = pcall(DataStoreService.GetRequestBudgetForRequestType, DataStoreService, requestType)
        if not ok or budget > RESERVE then
            return true
        end
        if os.clock() > deadline then
            return false
        end
        task.wait(0.5)
    end
end
AuctionStores.hasBudget = hasBudget

local function attempt(requestType, fn)
    for try = 1, TRIES do
        if requestType and not hasBudget(requestType) then
            return false, "budget"
        end
        local ok, result = pcall(fn)
        if ok then
            return true, result
        end
        if try == TRIES then
            warnOnce(tostring(result):sub(1, 40), "request failed: " .. tostring(result))
            return false, result
        end
        task.wait(BACKOFF[try])
    end
    return false, "unreachable"
end

-- a DataStore as AuctionCore wants it: get(key) -> ok, value; update(key, transform) -> ok, err
local function dataStore(store)
    local s = {}
    function s.get(key)
        if not store then
            return false, nil
        end
        return attempt(Enum.DataStoreRequestType.GetAsync, function()
            return (store:GetAsync(key))
        end)
    end
    function s.update(key, transform)
        if not store then
            return false, "no store"
        end
        local ok, err = attempt(Enum.DataStoreRequestType.UpdateAsync, function()
            store:UpdateAsync(key, function(old)
                return transform(old)
            end)
        end)
        return ok, if ok then nil else err
    end
    return s
end

AuctionStores.listings = dataStore(listingStore)
AuctionStores.mail = dataStore(mailStore)

-- ---------- the indexes ----------
local orderedEnd = {} -- [id] = the end this server last wrote to the ordered index (only a change is written)
local localBrowse = {} -- [id] = { summary, at }: what this server put, shown at once, before the browse map catches up
local localRemoved = {} -- [id] = at: what this server took out (the map may still hold it for a moment)
local LOCAL_HOLD = 30   -- seconds this server's own change wins over the browse map's copy

AuctionStores.onIndexChanged = nil -- set by AuctionService: (id, summary or nil)

local index = {}
function index.put(summary)
    localBrowse[summary.Id] = { summary, os.clock() }
    localRemoved[summary.Id] = nil
    if AuctionStores.onIndexChanged then
        AuctionStores.onIndexChanged(summary.Id, summary)
    end
    task.spawn(function()
        if endStore and orderedEnd[summary.Id] ~= summary.End then
            local ok = attempt(Enum.DataStoreRequestType.SetIncrementSortedAsync, function()
                endStore:SetAsync(summary.Id, math.floor(summary.End))
            end)
            if ok then
                orderedEnd[summary.Id] = summary.End
            end
        end
        if browseMap then
            local ttl = math.clamp(math.floor(summary.End - os.time()) + 3600, 60, MAX_TTL)
            attempt(nil, function()
                browseMap:SetAsync(summary.Id, summary, ttl, summary.End)
            end)
        end
    end)
end

function index.remove(id)
    localBrowse[id] = nil
    localRemoved[id] = os.clock()
    if AuctionStores.onIndexChanged then
        AuctionStores.onIndexChanged(id, nil)
    end
    task.spawn(function()
        if endStore then
            local ok = attempt(Enum.DataStoreRequestType.SetIncrementSortedAsync, function()
                endStore:RemoveAsync(id)
            end)
            if ok then
                orderedEnd[id] = nil
            end
        end
        if browseMap then
            attempt(nil, function()
                browseMap:RemoveAsync(id)
            end)
        end
    end)
end

-- the listing ids whose end is at or before `before`, soonest first
function index.due(before, count)
    if not endStore then
        return {}
    end
    local ok, page = attempt(Enum.DataStoreRequestType.GetSortedAsync, function()
        return endStore:GetSortedAsync(true, math.clamp(count, 1, 100), nil, math.floor(before)):GetCurrentPage()
    end)
    local ids = {}
    if ok then
        for _, entry in page do
            table.insert(ids, entry.key)
        end
    end
    return ids
end
AuctionStores.index = index

-- Every listing the browse map holds (and this server's own changes not yet in it): ok, { summary, ... }.
function AuctionStores.browseAll()
    if not browseMap then
        return false, {}
    end
    local found, seen = {}, {}
    local lower = nil
    while #found < BROWSE_MAX do
        local ok, items = attempt(nil, function()
            return browseMap:GetRangeAsync(Enum.SortDirection.Ascending, 200, lower)
        end)
        if not ok then
            return false, found
        end
        for _, item in items do
            if typeof(item.value) == "table" and not seen[item.key] then
                seen[item.key] = true
                local mine = localBrowse[item.key]
                local removed = localRemoved[item.key]
                if not (removed and os.clock() - removed < 60) then
                    table.insert(found, if mine and os.clock() - mine[2] < LOCAL_HOLD then mine[1] else item.value)
                end
            end
        end
        if #items < 200 then
            break
        end
        local last = items[#items]
        lower = { key = last.key, sortKey = last.sortKey }
    end
    for id, mine in localBrowse do
        if not seen[id] and os.clock() - mine[2] < LOCAL_HOLD then
            table.insert(found, mine[1])
        elseif os.clock() - mine[2] >= LOCAL_HOLD then
            localBrowse[id] = nil
        end
    end
    for id, at in localRemoved do
        if os.clock() - at >= 60 then
            localRemoved[id] = nil
        end
    end
    return true, found
end

-- ---------- "you have mail" ----------
function AuctionStores.notify(userId)
    task.spawn(function()
        pcall(MessagingService.PublishAsync, MessagingService, MAIL_TOPIC, userId)
    end)
end

function AuctionStores.subscribe(callback)
    task.spawn(function()
        local ok, err = pcall(MessagingService.SubscribeAsync, MessagingService, MAIL_TOPIC, function(message)
            local userId = tonumber(message.Data)
            if userId then
                callback(userId)
            end
        end)
        if not ok then
            warnOnce("subscribe", "can't hear other servers' mail notices (claims still run every minute): " .. tostring(err))
        end
    end)
end

return AuctionStores
