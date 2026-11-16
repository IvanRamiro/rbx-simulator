-- The Hall of Records' stores (shared/RecordsConfig), shared by every server:
--   ladders   one OrderedDataStore each (UserId -> a whole number): RecordStores.ladder(name)
--   records   the DataStore RecordsConfig.RecordStore (keys "Firsts" and "Rarest"): RecordStores.records
--   feed      the MemoryStore SortedMap RecordsConfig.FeedMap (the Chronicle's feats, each expiring): RecordStores.feed
-- In Studio every name starts with the StudioTestSave name (or "Studio"), as the Auction House's do, so a test never touches real
-- records. Each call checks the request budget first (keeping RESERVE a minute for the player saves) and makes one attempt:
-- RecordsService decides when to try again. A store that can never answer here (an unpublished place, Studio without API access)
-- is marked off, and RecordStores.available says so.
local DataStoreService = game:GetService("DataStoreService")
local MemoryStoreService = game:GetService("MemoryStoreService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local RecordsConfig = require(ReplicatedStorage:WaitForChild("RecordsConfig"))

local RecordStores = {}

local RESERVE = 10

local prefix = ""
if RunService:IsStudio() then
    local name = ServerStorage:GetAttribute("StudioTestSave")
    prefix = (if typeof(name) == "string" and name ~= "" then name elseif name then "StudioTestSave" else "Studio") .. "_"
end
RecordStores.prefix = prefix

local off = {} -- [kind] = true once a store can never answer here ("data", "memory")
local warned = {}
local function warnOnce(key, message)
    if not warned[key] then
        warned[key] = true
        warn("RecordStores: " .. message)
    end
end

local function isPermanent(err)
    local message = tostring(err)
    return string.find(message, "StudioAccessToApisNotAllowed", 1, true) ~= nil or string.find(message, "publish", 1, true) ~= nil
end

function RecordStores.available(kind)
    return not off[kind]
end

local function hasBudget(requestType)
    local ok, budget = pcall(DataStoreService.GetRequestBudgetForRequestType, DataStoreService, requestType)
    return not ok or budget > RESERVE
end

-- one attempt: ok, result | false, err ("budget" when there was none to spare)
local function call(kind, requestType, fn)
    if off[kind] then
        return false, "off"
    end
    if requestType and not hasBudget(requestType) then
        return false, "budget"
    end
    local ok, result = pcall(fn)
    if not ok then
        if isPermanent(result) then
            off[kind] = true
        end
        warnOnce(kind .. tostring(result):sub(1, 60), tostring(result))
    end
    return ok, result
end

local function open(kind, getter)
    local ok, store = pcall(getter)
    if not ok then
        warnOnce("open" .. kind, "can't open a store: " .. tostring(store))
        if isPermanent(store) then
            off[kind] = true
        end
        return nil
    end
    return store
end

-- ---------- the ladders ----------
local ladders = {}
function RecordStores.ladder(name)
    if ladders[name] then
        return ladders[name]
    end
    local store = open("data", function()
        return DataStoreService:GetOrderedDataStore(prefix .. name)
    end)
    local s = {}
    function s.set(userId, value)
        if not store then
            return false, "no store"
        end
        return call("data", Enum.DataStoreRequestType.SetIncrementSortedAsync, function()
            store:SetAsync(tostring(userId), math.max(0, math.floor(value)))
        end)
    end
    -- ok, { { UserId, Value }, ... } best first
    function s.top(count)
        if not store then
            return false, "no store"
        end
        local ok, page = call("data", Enum.DataStoreRequestType.GetSortedAsync, function()
            return store:GetSortedAsync(false, count):GetCurrentPage()
        end)
        if not ok then
            return false, page
        end
        local out = {}
        for _, entry in page do
            local userId = tonumber(entry.key)
            if userId and typeof(entry.value) == "number" and entry.value > 0 then
                table.insert(out, { UserId = userId, Value = entry.value })
            end
        end
        return true, out
    end
    ladders[name] = s
    return s
end

-- ---------- the records (Firsts, Rarest) ----------
local recordStore = open("data", function()
    return DataStoreService:GetDataStore(prefix .. RecordsConfig.RecordStore)
end)
RecordStores.records = {}
function RecordStores.records.get(key)
    if not recordStore then
        return false, "no store"
    end
    return call("data", Enum.DataStoreRequestType.GetAsync, function()
        return (recordStore:GetAsync(key))
    end)
end
-- transform(stored) -> the value to store or nil (cancel); ok, err
function RecordStores.records.update(key, transform)
    if not recordStore then
        return false, "no store"
    end
    return call("data", Enum.DataStoreRequestType.UpdateAsync, function()
        recordStore:UpdateAsync(key, function(stored)
            return transform(stored)
        end)
    end)
end

-- ---------- the Chronicle's feed ----------
local feedMap = open("memory", function()
    return MemoryStoreService:GetSortedMap(prefix .. RecordsConfig.FeedMap)
end)
RecordStores.feed = {}
function RecordStores.feed.add(key, value)
    if not feedMap then
        return false, "no store"
    end
    return call("memory", nil, function()
        feedMap:SetAsync(key, value, RecordsConfig.Feed.Keep)
    end)
end
-- ok, { value, ... } newest first
function RecordStores.feed.latest(count)
    if not feedMap then
        return false, "no store"
    end
    local ok, items = call("memory", nil, function()
        return feedMap:GetRangeAsync(Enum.SortDirection.Descending, count)
    end)
    if not ok then
        return false, items
    end
    local out = {}
    for _, item in items do
        table.insert(out, item.value)
    end
    return true, out
end

return RecordStores
