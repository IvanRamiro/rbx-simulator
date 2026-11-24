-- The weekly rivalry's tally across every server (GameConfig.Renown.War; the rules are shared/StandingRules). One DataStore key a week, "W<week number>":
--   { [faction] = { Renown, Members } }      the renown the faction's members earned that week, and how many of them earned any
-- A server adds what its players earn to a pending tally, and every FlushEvery seconds writes it into the week's record with UpdateAsync (adding, so servers
-- never overwrite one another) and reads back everyone's total; last week's record is read the same way for the Victory share. In Studio the store's name starts with the
-- StudioTestSave name (or "Studio"), so a Play never touches the real tally; with no store reachable there, it is kept in memory for the session.
--
--   FactionWar.add(week, faction, renown, newMember)   a player of `faction` earned `renown` (newMember: their first renown of the week)
--   FactionWar.totals(week)                            { [faction] = { Renown, Members } } as last known, this server's pending included
--   FactionWar.ready(week)                             whether that week's record has been read from the store at least once
--   FactionWar.start()                                 begins the flush loop (StandingService calls it once)
local DataStoreService = game:GetService("DataStoreService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local GoalRules = require(ReplicatedStorage:WaitForChild("GoalRules"))

local CONFIG = GameConfig.Renown.War
local FactionWar = {}

local MAX = 1e9
local prefix = ""
if RunService:IsStudio() then
    local name = ServerStorage:GetAttribute("StudioTestSave")
    prefix = (if typeof(name) == "string" and name ~= "" then name elseif name then "StudioTestSave" else "Studio") .. "_"
end

local store
do
    local ok, result = pcall(DataStoreService.GetDataStore, DataStoreService, prefix .. CONFIG.Store)
    store = if ok then result else nil
end
local storeOff = store == nil
local memory = {} -- [key] = record, when there is no store (Studio only)

local pending = {}  -- [week] = { [faction] = { Renown, Members } }
local known = {}    -- [week] = { [faction] = { Renown, Members } } as last read from the store (not pending)
local readWeeks = {} -- [week] = true once read

local function key(week)
    return CONFIG.KeyPrefix .. week
end

local function whole(value)
    return if typeof(value) == "number" and value == value and value >= 0 and value <= MAX then math.floor(value) else 0
end

-- a stored record reduced to the factions there are, with whole numbers
local function clean(raw)
    local out = {}
    for _, faction in GameConfig.Faction.Order do
        local entry = typeof(raw) == "table" and raw[faction] or nil
        out[faction] = { Renown = whole(entry and entry.Renown), Members = whole(entry and entry.Members) }
    end
    return out
end

function FactionWar.add(week, faction, renown, newMember)
    if not table.find(GameConfig.Faction.Order, faction) or typeof(week) ~= "number" then
        return
    end
    local tally = pending[week]
    if not tally then
        tally = {}
        pending[week] = tally
    end
    local entry = tally[faction]
    if not entry then
        entry = { Renown = 0, Members = 0 }
        tally[faction] = entry
    end
    entry.Renown += whole(renown)
    if newMember then
        entry.Members += 1
    end
end

function FactionWar.totals(week)
    local out = clean(known[week])
    local tally = pending[week]
    if tally then
        for faction, entry in tally do
            out[faction].Renown += entry.Renown
            out[faction].Members += entry.Members
        end
    end
    return out
end

function FactionWar.ready(week)
    return readWeeks[week] == true
end

-- writes the week's pending tally into its record and reads the record back; false when the store did not answer (the tally stays pending)
local function flush(week)
    local tally = pending[week]
    local snapshot = {}
    if tally then
        for faction, entry in tally do
            snapshot[faction] = { Renown = entry.Renown, Members = entry.Members }
        end
    end
    local has = next(snapshot) ~= nil
    local record
    if storeOff then
        if not RunService:IsStudio() then
            return false
        end
        local merged = clean(memory[key(week)])
        for faction, entry in snapshot do
            merged[faction].Renown += entry.Renown
            merged[faction].Members += entry.Members
        end
        memory[key(week)] = merged
        record = merged
    else
        local ok, result = pcall(function()
            return store:UpdateAsync(key(week), function(old)
                local merged = clean(old)
                for faction, entry in snapshot do
                    merged[faction].Renown += entry.Renown
                    merged[faction].Members += entry.Members
                end
                return merged
            end)
        end)
        if not ok then
            if string.find(tostring(result), "StudioAccessToApisNotAllowed", 1, true) or string.find(tostring(result), "publish", 1, true) then
                storeOff = true -- (not reachable from here: Studio keeps it in memory from the next flush)
            end
            return false
        end
        record = clean(result)
    end
    if has then
        -- what was written is in the record now: take it off the pending tally (anything added during the call stays)
        for faction, entry in snapshot do
            local now = pending[week][faction]
            now.Renown -= entry.Renown
            now.Members -= entry.Members
        end
    end
    known[week] = record
    readWeeks[week] = true
    return true
end

-- last week's record is read only (nothing is added to a finished week)
local function readOnly(week)
    if storeOff then
        known[week] = clean(memory[key(week)])
        readWeeks[week] = true
        return
    end
    local ok, result = pcall(function()
        return store:GetAsync(key(week))
    end)
    if ok then
        known[week] = clean(result)
        readWeeks[week] = true
    end
end

local started = false
function FactionWar.start()
    if started then
        return
    end
    started = true
    -- what this server's players earned in the last FlushEvery seconds goes into the record when the server closes (it was lost, while each member's own WeekRenown was saved)
    game:BindToClose(function()
        local week = GoalRules.weekKey()
        pcall(flush, week)
        if pending[week - 1] and next(pending[week - 1]) ~= nil then
            pcall(flush, week - 1)
        end
    end)
    task.spawn(function()
        local count = 0
        while true do
            local week = GoalRules.weekKey()
            local ok, err = pcall(function()
                flush(week)
                if pending[week - 1] and next(pending[week - 1]) ~= nil then
                    flush(week - 1) -- (what was earned just before the week turned)
                end
                if count % 4 == 0 or not readWeeks[week - 1] then -- (a finished week does not change: read it now and then)
                    readOnly(week - 1)
                end
            end)
            if not ok then
                warn("FactionWar: a flush failed: " .. tostring(err))
            end
            count += 1
            task.wait(CONFIG.FlushEvery)
        end
    end)
end

return FactionWar
