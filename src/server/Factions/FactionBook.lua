-- The factions' pledges (the owner, 2026-11-22: "Once a player officially joins a faction, their choice becomes permanent ... saved
-- permanently, even after players leave and rejoin"). One record per account in its own DataStore, not in the save, so no save version
-- changes and no rolled-back or lost save can undo it:
--   key "U_<UserId>" = { Faction, Joined, Server, Trial? }      (Trial: when the faction's trial was passed, set once)
-- The pledge is written once with UpdateAsync, only if the key is empty, so a second join from any server finds it taken. Nothing here
-- (or anywhere) removes or changes a Faction: there is no leaving. (In Studio the store's name starts with the StudioTestSave name, or
-- "Studio", so a Play never touches the real pledges; with no store at all there, Studio keeps them in memory for the session.)
--
--   FactionBook.setup(player)        reads the pledge (kept trying until it answers) and publishes it
--   FactionBook.ready(player)        whether the pledge has been read
--   FactionBook.record(player)       the player's record { Faction, Joined, Trial? } or nil
--   FactionBook.factionOf(player)    their faction's id, or nil
--   FactionBook.join(player, id)     "Set" | "Taken" | "Failed", the record: the one set-once write
--   FactionBook.markTrial(player)    true once the trial passed is on the record
--   FactionBook.setTrial(player, state, endsAt)  what the clients are told (the "FactionTrial" attributes)
--   FactionBook.forget(player)
-- Player attributes: Faction, FactionReady (see shared/FactionRules).
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local FactionRules = require(ReplicatedStorage:WaitForChild("FactionRules"))

local FactionBook = {}

local RESERVE = 10     -- requests a minute left for the player saves
local READ_RETRY = 6   -- seconds between tries to read a pledge while the store doesn't answer (each try already retries three times)

local prefix = ""
if RunService:IsStudio() then
    local name = ServerStorage:GetAttribute("StudioTestSave")
    prefix = (if typeof(name) == "string" and name ~= "" then name elseif name then "StudioTestSave" else "Studio") .. "_"
end

local storeOff = false
local memory = {} -- Studio only, with no store: [key] = record
local warned = {}
local function warnOnce(key, message)
    if not warned[key] then
        warned[key] = true
        warn("FactionBook: " .. message)
    end
end

local store
do
    local ok, result = pcall(DataStoreService.GetDataStore, DataStoreService, prefix .. GameConfig.Faction.Store)
    if ok then
        store = result
    else
        storeOff = true
        warnOnce("open", "can't open the pledge store: " .. tostring(result))
    end
end

local function isPermanent(err)
    local message = tostring(err)
    return string.find(message, "StudioAccessToApisNotAllowed", 1, true) ~= nil or string.find(message, "publish", 1, true) ~= nil
end

local function inMemory()
    return storeOff and RunService:IsStudio()
end

local function hasBudget(requestType)
    local ok, budget = pcall(DataStoreService.GetRequestBudgetForRequestType, DataStoreService, requestType)
    return not ok or budget > RESERVE
end

-- runs fn up to `tries` times, waiting longer after each failure: true, result | false, err
local function attempt(requestType, fn, tries)
    local lastError = "no store"
    for try = 1, tries do
        if storeOff then
            return false, "off"
        end
        if hasBudget(requestType) then
            local ok, result = pcall(fn)
            if ok then
                return true, result
            end
            lastError = result
            if isPermanent(result) then
                storeOff = true
                warnOnce("off", "the pledge store can't be used here: " .. tostring(result))
                return false, result
            end
            warnOnce(tostring(result):sub(1, 60), tostring(result))
        else
            lastError = "budget"
        end
        if try < tries then
            task.wait(math.min(2 ^ try, 30))
        end
    end
    return false, lastError
end

local state = {} -- [player] = { ready, record }

local function validRecord(record)
    return typeof(record) == "table" and typeof(record.Faction) == "string"
end

-- puts what the player's pledge says on the player, for the other systems and the client
local function publish(player)
    local s = state[player]
    if not s then
        return
    end
    local id = if s.record and FactionRules.isFaction(s.record.Faction) then s.record.Faction else nil
    player:SetAttribute("Faction", id)
    player:SetAttribute("FactionReady", s.ready == true)
end

function FactionBook.setup(player)
    if state[player] then
        return
    end
    state[player] = { ready = false, record = nil }
    local key = FactionRules.key(player.UserId)
    while player.Parent == Players and state[player] and not state[player].ready do
        local ok, record
        if inMemory() then
            ok, record = true, memory[key]
        else
            ok, record = attempt(Enum.DataStoreRequestType.GetAsync, function()
                return (store:GetAsync(key))
            end, 3)
        end
        if ok then
            local s = state[player]
            if s then
                if record ~= nil and not validRecord(record) then
                    warn("FactionBook: " .. player.UserId .. "'s pledge is unreadable: left as it is")
                end
                s.record = if validRecord(record) then record else nil
                s.unreadable = record ~= nil and not validRecord(record)
                s.ready = true
                publish(player)
            end
            return
        end
        if storeOff and not inMemory() then
            warnOnce("noread", "no pledge can be read here: nobody can join")
        end
        task.wait(READ_RETRY)
    end
end

function FactionBook.ready(player)
    local s = state[player]
    return s ~= nil and s.ready
end

function FactionBook.record(player)
    local s = state[player]
    return s and s.record
end

function FactionBook.factionOf(player)
    local s = state[player]
    return if s and s.record and FactionRules.isFaction(s.record.Faction) then s.record.Faction else nil
end

-- whether the account has a pledge the server can't read as a faction (it must never be treated as free to join)
function FactionBook.hasUnreadable(player)
    local s = state[player]
    return s ~= nil and s.unreadable == true
end

-- The one write: sets the pledge only if the key is empty. "Set" (the record), "Taken" (the record already there, from this or
-- another server, or an earlier try of this one that landed) or "Failed".
function FactionBook.join(player, factionId)
    local s = state[player]
    if not s or not s.ready or s.record or s.unreadable or not FactionRules.isFaction(factionId) then
        return "Failed", s and s.record
    end
    local userId = player.UserId
    local key = FactionRules.key(userId)
    local fresh = { Faction = factionId, Joined = os.time(), Server = game.JobId }
    local outcome, existing
    if inMemory() then
        if memory[key] then
            outcome, existing = "Taken", memory[key]
        else
            memory[key] = fresh
            outcome = "Set"
        end
    else
        local ok = attempt(Enum.DataStoreRequestType.UpdateAsync, function()
            store:UpdateAsync(key, function(old)
                if old ~= nil then
                    outcome, existing = "Taken", old
                    return nil
                end
                outcome, existing = "Set", nil
                return fresh, { userId }
            end)
        end, 3)
        if not ok then
            return "Failed", nil
        end
    end
    if state[player] ~= s then
        return outcome, existing or fresh -- (they left while it was written: the pledge stands, the next join reads it)
    end
    if outcome == "Set" then
        s.record = fresh
    elseif validRecord(existing) then
        s.record = existing
    else
        s.unreadable = true
    end
    publish(player)
    return outcome, s.record
end

-- the trial passed, kept on the record for good (set once; the faction itself is never touched)
function FactionBook.markTrial(player)
    local s = state[player]
    if not s or not s.record or not FactionRules.isFaction(s.record.Faction) then
        return false
    end
    if s.record.Trial then
        return true
    end
    local userId = player.UserId
    local key = FactionRules.key(userId)
    local now = os.time()
    local faction = s.record.Faction
    local result
    if inMemory() then
        local record = memory[key]
        if record and record.Faction == faction then
            record.Trial = record.Trial or now
            result = record
        end
    else
        local ok = attempt(Enum.DataStoreRequestType.UpdateAsync, function()
            store:UpdateAsync(key, function(old)
                if typeof(old) ~= "table" or old.Faction ~= faction then
                    return nil
                end
                if old.Trial then
                    result = old
                    return nil
                end
                local updated = table.clone(old)
                updated.Trial = now
                result = updated
                return updated, { userId }
            end)
        end, 4)
        if not ok then
            return false
        end
    end
    if result and state[player] == s then
        s.record = result
        return true
    end
    return result ~= nil
end

-- what the clients show of the trial: "Locked" | "Open" | "Running" | "Passed" | "Done" | nil, and when a running one ends
function FactionBook.setTrial(player, trialState, endsAt)
    player:SetAttribute("FactionTrial", trialState)
    player:SetAttribute("FactionTrialEnds", endsAt)
end

-- a trial's clock running for the player (TrialService sets and clears it; FactionService publishes it)
local running = {} -- [player] = server time the run ends

function FactionBook.setRunning(player, endsAt)
    running[player] = endsAt
end

function FactionBook.runEnds(player)
    return running[player]
end

function FactionBook.forget(player)
    state[player] = nil
    running[player] = nil
end

return FactionBook
