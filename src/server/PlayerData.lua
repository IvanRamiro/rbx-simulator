
-- Saves and loads each player's progress with DataStoreService (server only).
--
-- One saved record per player, key "Player_<UserId>":
-- {
--     SchemaVersion = 5,
--     Session = { Id = "...", Time = os.time() } or nil, -- which server is using this data
--     Progress = {
--         Qi = 1234,
--         RankId = "QiCondenser",
--         Pets = { { InstanceId = "...", PetId = "AquaWisp" }, ... },
--         EquippedPetIds = { "...", ... },
--         AuraPetInstanceId = "..." or nil,
--         Relics = { "GroveHeart", ... }, -- Spirit Relics found
--     } or nil, -- nil until the first save, which means "new player"
-- }
--
-- Only progress is saved. Cultivation, characters, auras, cooldowns and UI
-- are never saved, so every session starts with cultivation off.

local DataStoreService = game:GetService("DataStoreService")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local Discoveries = require(script.Parent:WaitForChild("Discoveries"))
local PetInventory = require(script.Parent:WaitForChild("PetInventory"))

local DATASTORE_NAME = "PlayerProgress"
local SCHEMA_VERSION = 5

local LOAD_ATTEMPTS = 4 -- The last attempt takes over data another server still claims
local LOAD_RETRY_DELAY = 5 -- Seconds between load attempts
local FINAL_SAVE_ATTEMPTS = 3
local SESSION_LOCK_TIMEOUT = 300 -- A claim older than this many seconds counts as abandoned
local MIN_SECONDS_BETWEEN_SAVES = 10 -- For quick saves after important changes
local WRITE_COOLDOWN = 6 -- Roblox allows one write per key about every 6 seconds
local MAX_QI = 1e15 -- Loaded Qi is clamped between 0 and this

local PlayerData = {}
PlayerData.AUTOSAVE_INTERVAL = 60

-- MIGRATIONS[n] upgrades saved Progress from schema version n to n + 1.
-- Anything a migration doesn't recognise is cleaned up by sanitizeProgress.
local MIGRATIONS = {}

-- Version 1 -> 2: the cultivation ranks and starter pets were replaced with
-- the ones from the design guide.
-- Each old rank becomes the highest new rank needing no more Qi than it did,
-- so nobody is placed above what they earned (Qi is kept, so players can rank
-- straight back up). Each old pet becomes the new pet of the same rarity;
-- instance IDs are kept, so equipped pets and the aura pet stay selected.
local V1_RANKS = {
    Mortal = "QiInitiate", -- Needed 0 Qi; Qi Initiate needs 0
    QiSensing = "QiInitiate", -- Needed 250 Qi; Qi Gatherer needs 300
    QiGathering = "QiGatherer", -- Needed 750 Qi; Qi Gatherer needs 300
    FlowingMeridians = "QiAdept", -- Needed 2000 Qi; Qi Adept needs 2000
    AwakenedAura = "QiAwakener", -- Needed 5000 Qi; Qi Awakener needs 4000
}
local V1_PETS = {
    EmberWisp = "AquaWisp", -- Common
    MoonKoi = "EmberWyrm", -- Uncommon
    JadeTortoise = "VoltFox", -- Rare
}

MIGRATIONS[1] = function(progress)
    progress.RankId = V1_RANKS[progress.RankId] or progress.RankId

    if typeof(progress.Pets) == "table" then
        for _, pet in progress.Pets do
            if typeof(pet) == "table" and V1_PETS[pet.PetId] then
                pet.PetId = V1_PETS[pet.PetId]
            end
        end
    end

    return progress
end

-- Version 2 -> 3: Spirit Relics were added; older saves haven't found any
MIGRATIONS[2] = function(progress)
    progress.Relics = progress.Relics or {}
    return progress
end

-- Version 3 -> 4: new pets (Jade Spirit and Inferno eggs). Nothing to change;
-- the version bump stops older servers, which don't know these pets, from
-- loading (and dropping them from) newer saves.
MIGRATIONS[3] = function(progress)
    return progress
end

-- Version 4 -> 5: new pets (Lunar Hopper and Astral Whale). Like version 4,
-- the bump only stops older servers from dropping them.
MIGRATIONS[4] = function(progress)
    return progress
end

local store = nil
local storeOk, storeResult = pcall(function()
    return DataStoreService:GetDataStore(DATASTORE_NAME)
end)
if storeOk then
    store = storeResult
else
    warn("PlayerData: DataStores are unavailable: " .. tostring(storeResult))
end

local startingRank = Ranks.getRank(GameConfig.StartingRank)

-- profiles[player] = {
--     key, sessionId,
--     status = "Loading" | "Loaded" | "Failed",
--     progress, isNew,  -- validated loaded data, for the gameplay scripts
--     canSave,          -- false until loaded, and forever if loading failed
--     isSaving, isReleasing, quickSaveScheduled, lastSaveTime,
--     loaded = BindableEvent, -- fires once when loading finishes
-- }
local profiles = {}

-- Validation ---------------------------------------------------------------

-- Turns loaded (possibly old or damaged) progress into safe, valid progress.
-- Anything invalid is dropped or replaced with a safe value.
local function sanitizeProgress(raw)
    local progress = {
        Qi = GameConfig.StartingQi,
        RankId = startingRank.Id,
        Pets = {},
        EquippedPetIds = {},
        AuraPetInstanceId = nil,
        Relics = {},
    }

    if typeof(raw) ~= "table" then
        return progress
    end

    -- Qi: a whole number from 0 to MAX_QI (raw.Qi == raw.Qi rules out NaN)
    if typeof(raw.Qi) == "number" and raw.Qi == raw.Qi then
        progress.Qi = math.clamp(math.floor(raw.Qi), 0, MAX_QI)
    end

    -- Rank: must be a known rank, and the player must have enough Qi for it
    local rankIndex = 1
    for index, rank in GameConfig.Ranks do
        if rank.Id == raw.RankId then
            rankIndex = index
        end
    end
    while rankIndex > 1 and GameConfig.Ranks[rankIndex].QiRequired > progress.Qi do
        rankIndex -= 1
    end
    progress.RankId = GameConfig.Ranks[rankIndex].Id

    -- Pets: known catalogue pets only, no duplicate instance IDs, within the limit
    local ownedIds = {}
    if typeof(raw.Pets) == "table" then
        for _, pet in raw.Pets do
            if #progress.Pets >= GameConfig.MaxOwnedPets then
                break
            end

            local isValid = typeof(pet) == "table"
                and typeof(pet.InstanceId) == "string"
                and #pet.InstanceId > 0
                and #pet.InstanceId <= 64
                and typeof(pet.PetId) == "string"
                and GameConfig.Pets[pet.PetId] ~= nil

            if isValid and not ownedIds[pet.InstanceId] then
                ownedIds[pet.InstanceId] = true
                table.insert(progress.Pets, { InstanceId = pet.InstanceId, PetId = pet.PetId })
            end
        end
    end

    -- Equipped: owned pets only, no duplicates, at most MaxEquippedPets
    if typeof(raw.EquippedPetIds) == "table" then
        for _, instanceId in raw.EquippedPetIds do
            if #progress.EquippedPetIds >= GameConfig.MaxEquippedPets then
                break
            end

            if typeof(instanceId) == "string" and ownedIds[instanceId] and not table.find(progress.EquippedPetIds, instanceId) then
                table.insert(progress.EquippedPetIds, instanceId)
            end
        end
    end

    -- Aura pet: must be one of the equipped pets
    if typeof(raw.AuraPetInstanceId) == "string" and table.find(progress.EquippedPetIds, raw.AuraPetInstanceId) then
        progress.AuraPetInstanceId = raw.AuraPetInstanceId
    end

    -- Relics: known relic Ids only, each once
    if typeof(raw.Relics) == "table" then
        for _, relicId in raw.Relics do
            if typeof(relicId) == "string" and Discoveries.getRelic(relicId) and not table.find(progress.Relics, relicId) then
                table.insert(progress.Relics, relicId)
            end
        end
    end

    return progress
end

local function migrate(progress, fromVersion)
    for version = fromVersion, SCHEMA_VERSION - 1 do
        local upgrade = MIGRATIONS[version]
        if upgrade then
            progress = upgrade(progress)
        end
    end

    return progress
end

-- Reads the player's current progress from the gameplay systems. Returns nil
-- if they aren't fully set up, so partial or default data is never saved.
local function captureProgress(player)
    local leaderstats = player:FindFirstChild("leaderstats")
    local qi = leaderstats and leaderstats:FindFirstChild("Qi")
    local rankValue = leaderstats and leaderstats:FindFirstChild("Rank")
    local pets = PetInventory.exportData(player)
    local relics = Discoveries.exportData(player)
    if not (qi and rankValue and pets and relics) then
        return nil
    end

    local rank = Ranks.getRank(rankValue.Value) or startingRank

    return {
        Qi = qi.Value,
        RankId = rank.Id,
        Pets = pets.Pets,
        EquippedPetIds = pets.EquippedPetIds,
        AuraPetInstanceId = pets.AuraPetInstanceId,
        Relics = relics,
    }
end

-- DataStore access ---------------------------------------------------------

-- Errors that retrying won't fix (mostly Studio setup problems)
local function isPermanentError(message)
    message = tostring(message)
    return string.find(message, "StudioAccessToApisNotAllowed") ~= nil
        or string.find(message, "publish") ~= nil
        or string.find(message, "unavailable") ~= nil
end

-- Runs inside UpdateAsync while loading. Claims the record for this session
-- unless another server is still actively using it.
-- Returns "Loaded" plus the record to write, or "Locked" / "Corrupt" / "TooNew".
local function claimSession(stored, sessionId, takeOver)
    stored = if stored == nil then {} else stored

    if typeof(stored) ~= "table" or (stored.Progress ~= nil and typeof(stored.Progress) ~= "table") then
        return "Corrupt", nil
    end

    -- Saved by a newer version of the game; this server can't safely use it
    if typeof(stored.SchemaVersion) == "number" and stored.SchemaVersion > SCHEMA_VERSION then
        return "TooNew", nil
    end

    local session = stored.Session
    local isClaimedByOther = typeof(session) == "table"
        and session.Id ~= sessionId
        and typeof(session.Time) == "number"
        and os.time() - session.Time < SESSION_LOCK_TIMEOUT
    if isClaimedByOther and not takeOver then
        return "Locked", nil
    end

    stored.Session = { Id = sessionId, Time = os.time() }
    return "Loaded", stored
end

-- Writes progress with UpdateAsync. The write only happens while this
-- session still owns the record; if another server has taken over, its data
-- is newer, so it's left alone and this session stops saving.
-- progress = nil keeps the stored progress (used to just release the claim).
local function writeRecord(profile, progress, releaseClaim)
    local accepted = false

    local ok, err = pcall(function()
        store:UpdateAsync(profile.key, function(stored)
            accepted = false
            if typeof(stored) ~= "table" or typeof(stored.Session) ~= "table" or stored.Session.Id ~= profile.sessionId then
                return nil -- Cancel the write
            end

            accepted = true
            return {
                SchemaVersion = if progress then SCHEMA_VERSION else stored.SchemaVersion,
                Session = if releaseClaim then nil else { Id = profile.sessionId, Time = os.time() },
                Progress = progress or stored.Progress,
            }
        end)
    end)

    if not ok then
        warn("PlayerData: save failed for " .. profile.key .. ": " .. tostring(err))
        return false
    end

    if not accepted then
        warn("PlayerData: " .. profile.key .. " is now used by another server; this server stopped saving it")
        profile.canSave = false
        return false
    end

    return true
end

local function loadProfile(player, profile)
    local result, record = "Error", nil

    for attempt = 1, LOAD_ATTEMPTS do
        local takeOver = attempt == LOAD_ATTEMPTS
        local ok, err = pcall(function()
            if not store then
                error("DataStores are unavailable")
            end

            store:UpdateAsync(profile.key, function(stored)
                result, record = claimSession(stored, profile.sessionId, takeOver)
                return if result == "Loaded" then record else nil
            end)
        end)

        if not ok then
            result = "Error"
            warn("PlayerData: load failed for " .. profile.key .. ": " .. tostring(err))
        end

        local shouldRetry = (result == "Locked" or result == "Error")
            and not (not ok and isPermanentError(err))
            and player.Parent == Players
            and attempt < LOAD_ATTEMPTS
        if not shouldRetry then
            break
        end

        task.wait(LOAD_RETRY_DELAY)
    end

    if result == "Loaded" then
        local version = if typeof(record.SchemaVersion) == "number" then record.SchemaVersion else SCHEMA_VERSION
        profile.isNew = record.Progress == nil
        profile.progress = sanitizeProgress(if record.Progress then migrate(record.Progress, version) else nil)
        profile.canSave = true
        profile.status = "Loaded"
    elseif RunService:IsStudio() then
        -- Usually Studio without API access or an unpublished place. Play with
        -- fresh data but never save it, so nothing real can be overwritten.
        warn("PlayerData: couldn't load data (" .. result .. "). This Studio session will NOT be saved.")
        profile.isNew = true
        profile.progress = sanitizeProgress(nil)
        profile.status = "Loaded"
    else
        profile.status = "Failed"
        if player.Parent == Players then
            player:Kick("Your saved progress couldn't be loaded. Please rejoin in a moment.")
        end
    end

    profile.lastSaveTime = os.clock()
    profile.loaded:Fire()
end

-- Public API ---------------------------------------------------------------

-- Starts loading a player's data (only once). Called when they join.
function PlayerData.startLoading(player)
    if profiles[player] then
        return profiles[player]
    end

    if player.Parent ~= Players then
        return nil
    end

    local profile = {
        key = "Player_" .. player.UserId,
        sessionId = HttpService:GenerateGUID(false),
        status = "Loading",
        progress = nil,
        isNew = false,
        canSave = false,
        isSaving = false,
        isReleasing = false,
        quickSaveScheduled = false,
        lastSaveTime = 0,
        loaded = Instance.new("BindableEvent"),
    }
    profiles[player] = profile

    task.spawn(loadProfile, player, profile)
    return profile
end

-- Waits until the player's data has loaded. Returns the validated progress
-- and whether they are a brand-new player, or nil if it couldn't be loaded
-- or the player left. Gameplay scripts must not set the player up until then.
function PlayerData.waitForData(player)
    local profile = PlayerData.startLoading(player)
    if not profile then
        return nil
    end

    if profile.status == "Loading" then
        profile.loaded.Event:Wait()
    end

    if profile.status ~= "Loaded" or player.Parent ~= Players then
        return nil
    end

    return profile.progress, profile.isNew
end

-- Saves the player's current progress. Skips if a save is already running
-- (the next autosave catches up), so saves for one player never overlap.
function PlayerData.save(player)
    local profile = profiles[player]
    if not profile or not profile.canSave or profile.isReleasing or profile.isSaving then
        return
    end

    if os.clock() - profile.lastSaveTime < WRITE_COOLDOWN then
        return -- Saved moments ago; the next autosave will catch up
    end

    local progress = captureProgress(player)
    if not progress then
        return
    end

    profile.isSaving = true
    writeRecord(profile, progress, false)
    profile.lastSaveTime = os.clock()
    profile.isSaving = false
end

-- Call after important progress (rank-ups, new pets). Saves soon, but never
-- more often than MIN_SECONDS_BETWEEN_SAVES, and only one is ever queued.
function PlayerData.saveSoon(player)
    local profile = profiles[player]
    if not profile or profile.quickSaveScheduled then
        return
    end

    profile.quickSaveScheduled = true
    local delay = math.max(0, profile.lastSaveTime + MIN_SECONDS_BETWEEN_SAVES - os.clock())

    task.delay(delay, function()
        profile.quickSaveScheduled = false
        PlayerData.save(player)
    end)
end

-- Final save when a player leaves (or the server closes). Releases this
-- session's claim so their next server can load the data straight away.
function PlayerData.release(player)
    local profile = profiles[player]
    if profile and profile.isReleasing then
        return
    end

    -- Take the final snapshot right away, before other scripts clean up
    local finalProgress = if profile and profile.status == "Loaded" then captureProgress(player) else nil

    -- Pet and relic data are removed here (not in their services) so they're always captured first
    PetInventory.removePlayer(player)
    Discoveries.removePlayer(player)

    if not profile then
        return
    end
    profile.isReleasing = true

    if profile.status == "Loading" then
        profile.loaded.Event:Wait()
    end

    if profile.canSave then
        while profile.isSaving do
            task.wait(0.1)
        end

        profile.isSaving = true
        for _ = 1, FINAL_SAVE_ATTEMPTS do
            if writeRecord(profile, finalProgress, true) or not profile.canSave then
                break
            end
            task.wait(2)
        end
        profile.isSaving = false
    end

    profiles[player] = nil
    profile.loaded:Destroy()
end

-- For BindToClose: saves everyone and waits (up to about 25 seconds)
-- until every final save has finished
function PlayerData.releaseAll()
    for _, player in Players:GetPlayers() do
        task.spawn(PlayerData.release, player)
    end

    local deadline = os.clock() + 25
    while next(profiles) ~= nil and os.clock() < deadline do
        task.wait(0.5)
    end
end

return PlayerData
