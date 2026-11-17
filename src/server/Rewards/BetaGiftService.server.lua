-- The beta gift (shared/BetaGift): while the beta runs, every Roblox account may take ONE Exclusive beast of its choice, free, once
-- ever. Who has taken theirs is kept in its own DataStore (BetaGift.Store, key "U_<UserId>"), not in the save, so no save schema
-- changes and the record holds across servers and rejoins.
--
-- A claim, step by step, so nothing is lost or given twice across a crash or two servers:
--   0. checks: one of the three beasts, the beta on, this server holds the player's save, room in their pets (refused here, before
--      anything is written, if they hold MaxOwnedPets).
--   1. reserve: their save is written first (PlayerData.saveConfirmed), then UpdateAsync writes { Status = "pending", PetId, At,
--      Had } only if the key is empty (Had: how many of that beast they held, which is now also what the save holds). A second
--      claim, from any server, finds the key taken and is refused.
--   2. give: PetInventory.grantPet (Normal size, Level 1, no mutation: as the Merchant gives a beast), then publish.
--   3. save: PlayerData.saveConfirmed (as the Auction House does: it also proves this server still holds the session).
--   4. done: UpdateAsync turns the record to { Status = "done", DoneAt, InstanceId }.
-- Recovery: a record found "pending" on joining (a crash or a lost connection between 1 and 4) is finished there, before the player
-- can do anything: if their save holds more of that beast than Had, the save has the gift and the record is only marked done;
-- otherwise the gift is given again (steps 2 to 4). A failed save in step 3 is retried in the background, then the next autosave or
-- the save on leaving writes the beast and the next join marks it done. A reservation whose beast couldn't be given (they filled
-- their pets in the same moment, or left) is taken back, so they can choose again.
-- Every call checks the request budget first (keeping RESERVE a minute for the saves) and tries again with a growing wait.
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local BetaGift = require(ReplicatedStorage:WaitForChild("BetaGift"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))

local serverRoot = script.Parent.Parent
local PlayerData = require(serverRoot:WaitForChild("Data"):WaitForChild("PlayerData"))
local PetInventory = require(serverRoot:WaitForChild("Pets"):WaitForChild("PetInventory"))

local Event = RemoteEvents.BetaGiftEvent

local RESERVE = 10        -- requests a minute left for the player saves
local THROTTLE = 1.5      -- seconds between a player's requests
local READ_RETRY = 30     -- seconds between tries to read a player's claim while the store doesn't answer
local CHECK_EVERY = 20    -- seconds between checks that the beta still runs (an offer is withdrawn once it doesn't)
local ATTRIBUTE = "BetaGift"

local prefix = ""
if RunService:IsStudio() then
    local name = ServerStorage:GetAttribute("StudioTestSave")
    prefix = (if typeof(name) == "string" and name ~= "" then name elseif name then "StudioTestSave" else "Studio") .. "_"
end

local storeOff = false -- the store can never answer here (an unpublished place, Studio without API access): nothing is offered
local warned = {}
local function warnOnce(key, message)
    if not warned[key] then
        warned[key] = true
        warn("BetaGiftService: " .. message)
    end
end

local function isPermanent(err)
    local message = tostring(err)
    return string.find(message, "StudioAccessToApisNotAllowed", 1, true) ~= nil or string.find(message, "publish", 1, true) ~= nil
end

local store
do
    local ok, result = pcall(DataStoreService.GetDataStore, DataStoreService, prefix .. BetaGift.Store)
    if ok then
        store = result
    else
        storeOff = true
        warnOnce("open", "can't open the claims store: " .. tostring(result))
    end
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
                warnOnce("off", "the claims store can't be used here: " .. tostring(result))
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

local state = {} -- [player] = { status = "Checking" | "Open" | "Busy" | "Waiting" | "Claimed" | "Off", last = os.clock() }

local function setOpen(player, open)
    local s = state[player]
    if s then
        s.status = if open then "Open" else "Off"
    end
    player:SetAttribute(ATTRIBUTE, if open then "Open" else nil)
end

local function tell(player, text)
    if player.Parent == Players then
        Event:FireClient(player, "Refused", text)
    end
end

local function countOf(player, petId)
    local snapshot = PetInventory.getSnapshot(player)
    local count = 0
    for _, pet in if snapshot then snapshot.Pets else {} do
        if pet.PetId == petId then
            count += 1
        end
    end
    return count
end

local function fullText()
    return "Your pets are full (" .. GameConfig.MaxOwnedPets .. "). Sell or fuse a pet to make room, then take your gift."
end

local function readClaim(player)
    return attempt(Enum.DataStoreRequestType.GetAsync, function()
        return (store:GetAsync(BetaGift.key(player.UserId)))
    end, 3)
end

-- step 4: the record says the gift is given (kept trying in the background: until it lands, the next join finds "pending" and
-- sees the beast in the save)
local function markDone(player, record, instanceId)
    local userId = player.UserId
    task.spawn(function()
        local ok, err = attempt(Enum.DataStoreRequestType.UpdateAsync, function()
            store:UpdateAsync(BetaGift.key(userId), function(old)
                if typeof(old) ~= "table" or old.Status ~= "pending" or old.At ~= record.At then
                    return nil -- (already done, or not this claim: left as it is)
                end
                local done = table.clone(old)
                done.Status = "done"
                done.DoneAt = os.time()
                done.InstanceId = instanceId
                return done, { userId }
            end)
        end, 8)
        if not ok then
            warn("BetaGiftService: couldn't mark " .. userId .. "'s claim done (" .. tostring(err) .. "): the next join will")
        end
    end)
end

-- a reservation whose beast couldn't be given: taken back, if it is still this one and still pending
local function release(userId, record)
    attempt(Enum.DataStoreRequestType.UpdateAsync, function()
        local ok, current = pcall(store.GetAsync, store, BetaGift.key(userId))
        if ok and typeof(current) == "table" and current.Status == "pending" and current.At == record.At then
            store:RemoveAsync(BetaGift.key(userId))
        end
    end, 4)
end

-- steps 2 to 4. True once the beast is theirs.
local function give(player, record, recovered)
    local s = state[player]
    local ok, instanceId = PetInventory.grantPet(player, record.PetId)
    if not ok then
        if player.Parent == Players and PetInventory.isSetUp(player) and recovered then
            -- (a pending gift found on joining with their pets full: it waits until there is room)
            if s and s.status ~= "Waiting" then
                s.status = "Waiting"
                local name = GameConfig.Pets[record.PetId].DisplayName
                tell(player, "Your Beta gift, the " .. name .. ", is waiting. Sell or fuse a pet to make room, and it will arrive.")
            end
            return false
        end
        if not recovered then
            release(player.UserId, record)
        end
        if s then
            s.status = "Open"
        end
        if player.Parent == Players then
            player:SetAttribute(ATTRIBUTE, "Open")
            tell(player, fullText())
        end
        return false
    end
    PetInventory.publish(player)
    if s then
        s.status = "Claimed"
    end
    player:SetAttribute(ATTRIBUTE, nil)
    Event:FireClient(player, "Claimed", record.PetId, recovered == true)

    local saved = player.Parent == Players and PlayerData.canSave(player) and PlayerData.saveConfirmed(player)
    if saved then
        markDone(player, record, instanceId)
    else
        -- the next autosave or the save on leaving writes it; tried here a few more times so the record can be closed now
        task.spawn(function()
            for _ = 1, 6 do
                task.wait(15)
                if player.Parent ~= Players or not PlayerData.canSave(player) then
                    return
                end
                if PlayerData.saveConfirmed(player) then
                    markDone(player, record, instanceId)
                    return
                end
            end
        end)
    end
    return true
end

-- a "pending" record found: the gift is finished, never given twice
local function recover(player, record)
    if typeof(record.PetId) ~= "string" or not GameConfig.Pets[record.PetId] then
        warn("BetaGiftService: " .. player.UserId .. "'s pending claim names no known beast: left as it is")
        return
    end
    local had = tonumber(record.Had) or 0
    if countOf(player, record.PetId) > had then
        -- their save already holds it (the crash came after the save): only the record is closed
        local s = state[player]
        if s then
            s.status = "Claimed"
        end
        markDone(player, record, nil)
        return
    end
    if not give(player, record, true) then
        -- pets full: tried again whenever they may have made room
        task.spawn(function()
            while player.Parent == Players and state[player] and state[player].status == "Waiting" do
                task.wait(10)
                if PetInventory.isSetUp(player) and not PetInventory.isFull(player) then
                    give(player, record, true)
                end
            end
        end)
    end
end

local function claim(player, petId)
    local s = state[player]
    if not s or s.status ~= "Open" then
        return
    end
    if not BetaGift.active() then
        setOpen(player, false)
        tell(player, "The Beta gift is no longer offered.")
        return
    end
    if PetInventory.isFull(player) then
        tell(player, fullText())
        return
    end
    if not PlayerData.canSave(player) then
        tell(player, "Your progress can't be saved right now, so the gift can't be given yet. Please try again in a moment.")
        return
    end

    s.status = "Busy"
    -- the save first matches what they hold now, so Had (counted now) is also what the save holds: a recovery then reads the gift
    -- in the save exactly (a beast sold a moment ago and not yet saved would otherwise look like the gift)
    if not PlayerData.saveConfirmed(player) or player.Parent ~= Players then
        s.status = "Open"
        tell(player, "Your progress can't be saved right now, so the gift can't be given yet. Please try again in a moment.")
        return
    end
    local userId = player.UserId
    local reservation = { Status = "pending", PetId = petId, At = os.time(), Had = countOf(player, petId), Server = game.JobId }
    local outcome, existing = nil, nil
    local ok = attempt(Enum.DataStoreRequestType.UpdateAsync, function()
        store:UpdateAsync(BetaGift.key(userId), function(old)
            if old ~= nil then
                outcome, existing = "Taken", old
                return nil
            end
            outcome, existing = "Reserved", nil
            return reservation, { userId }
        end)
    end, 3)
    if player.Parent ~= Players then
        if ok and outcome == "Reserved" then
            release(userId, reservation) -- (they left while it was written: nothing was given)
        end
        return
    end
    if not ok then
        s.status = "Open"
        tell(player, "The gift couldn't be reached right now. Please try again in a moment.")
        return
    end
    if outcome == "Taken" then
        if typeof(existing) == "table" and existing.Status == "pending" then
            recover(player, existing) -- (an earlier try of this same claim landed, or one cut off by a crash)
        else
            setOpen(player, false)
            tell(player, "You already took your Beta gift.")
        end
        return
    end
    give(player, reservation, false)
end

local function setup(player)
    local progress = PlayerData.waitForData(player)
    if not progress or player.Parent ~= Players then
        return
    end
    local deadline = os.clock() + 60
    while not PetInventory.isSetUp(player) and player.Parent == Players and os.clock() < deadline do
        task.wait(0.25)
    end
    if not PetInventory.isSetUp(player) or player.Parent ~= Players then
        return
    end
    if not PlayerData.canSave(player) then
        return -- (a save that will never be written can't hold a gift: Studio without its store)
    end
    state[player] = { status = "Checking", last = 0 }
    while player.Parent == Players and not storeOff do
        local ok, record = readClaim(player)
        if ok then
            if record == nil then
                setOpen(player, BetaGift.active())
            elseif typeof(record) == "table" and record.Status == "pending" then
                recover(player, record) -- (even after the beta: it was taken while it ran)
            else
                state[player].status = "Claimed"
            end
            return
        end
        task.wait(READ_RETRY)
    end
end

Players.PlayerAdded:Connect(setup)
for _, player in Players:GetPlayers() do
    task.spawn(setup, player)
end
Players.PlayerRemoving:Connect(function(player)
    state[player] = nil
end)

Event.OnServerEvent:Connect(function(player, action, petId)
    local s = state[player]
    if not s then
        return
    end
    local now = os.clock()
    if now - s.last < THROTTLE then
        return
    end
    s.last = now
    if action == "Claim" and BetaGift.isChoice(petId) then
        claim(player, petId)
    end
end)

-- an offer is withdrawn once the beta doesn't run (GameConfig.Beta.Active)
task.spawn(function()
    while true do
        task.wait(CHECK_EVERY)
        if not BetaGift.active() then
            for player, s in state do
                if s.status == "Open" then
                    setOpen(player, false)
                end
            end
        end
    end
end)
