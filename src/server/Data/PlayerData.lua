local DataStoreService = game:GetService("DataStoreService")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local Discoveries = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("Discoveries"))
local EggInventory = require(script.Parent.Parent:WaitForChild("Pets"):WaitForChild("EggInventory"))
local Elements = require(script.Parent.Parent:WaitForChild("Shop"):WaitForChild("Elements"))
local Wallet = require(script.Parent.Parent:WaitForChild("Shop"):WaitForChild("Wallet"))
local WeaponInventory = require(script.Parent.Parent:WaitForChild("Shop"):WaitForChild("WeaponInventory"))
local PetInventory = require(script.Parent.Parent:WaitForChild("Pets"):WaitForChild("PetInventory"))
local Codex = require(script.Parent.Parent:WaitForChild("Pets"):WaitForChild("Codex"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local Quests = require(script.Parent.Parent:WaitForChild("Quests"):WaitForChild("Quests"))
local Settings = require(script.Parent:WaitForChild("Settings"))
local Rewards = require(script.Parent.Parent:WaitForChild("Rewards"):WaitForChild("Rewards"))
local TitleBook = require(script.Parent.Parent:WaitForChild("Titles"):WaitForChild("TitleBook"))
local MerchantLedger = require(script.Parent.Parent:WaitForChild("Shop"):WaitForChild("MerchantLedger"))

local DATASTORE_NAME = "PlayerProgress"
local SCHEMA_VERSION = 15

-- a record another server still holds is taken over on the last attempt, about 25 s on: long
-- enough for that server's final save (with its retries) to land first
local LOAD_ATTEMPTS = 6
local LOAD_RETRY_DELAY = 5
local FINAL_SAVE_ATTEMPTS = 3
local SESSION_LOCK_TIMEOUT = 300
local MIN_SECONDS_BETWEEN_SAVES = 10
local WRITE_COOLDOWN = 6
local BUSY_RETRY = 1            -- seconds before a quick save tries again while a write is in flight
local MAX_QI = 1e15

local PlayerData = {}
PlayerData.AUTOSAVE_INTERVAL = 60

local MIGRATIONS = {}

local V1_RANKS = {
    Mortal = "QiInitiate",
    QiSensing = "QiInitiate",
    QiGathering = "QiGatherer",
    FlowingMeridians = "QiAdept",
    AwakenedAura = "QiAwakener",
}
local V1_PETS = {
    EmberWisp = "AquaWisp",
    MoonKoi = "EmberWyrm",
    JadeTortoise = "VoltFox",
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

MIGRATIONS[2] = function(progress)
    progress.Relics = progress.Relics or {}
    return progress
end

-- Upgrades from versions 3, 4 and 5 change nothing, so they have no migration: versions 4 and 5
-- added pets (the bump only stops older servers, which don't know them, from dropping them) and
-- version 6 added Eggs, which sanitizeProgress starts empty; version 7 added SpiritStones, Weapons
-- and EquippedWeapon (MIGRATIONS[6], below); version 8 added ForgeElements (the guardians' drops)
-- and a weapon's Element and Name, which start at none; version 9 added Quest (MIGRATIONS[8]);
-- version 10 added Settings and version 11 Rewards, which sanitizeProgress starts at their defaults;
-- version 12 added Codex and a pet's Level and Locked, which start empty, at 1 and unlocked (PetInventory enters owned pets in the Codex);
-- version 14 added Titles, which start with none earned (TitleService gives a returning player the ones they qualify for);
-- version 15 added Merchant (the Wandering Merchant's deals bought this visit: MerchantLedger), which starts with none.

-- A save from before weapons gets the starter weapon, once. A new player is given it by
-- WeaponInventory; nobody else is, or selling it and rejoining would mint Spirit Stones.
MIGRATIONS[6] = function(progress)
    if typeof(progress.Weapons) ~= "table" then
        local starter = { InstanceId = HttpService:GenerateGUID(false), WeaponId = GameConfig.StarterWeapon }
        progress.Weapons = { starter }
        progress.EquippedWeapon = starter.InstanceId
    end
    return progress
end

-- A save from before the first quests has played the game already: its quests start done, so a
-- returning player never sees the beginner's path (a new player starts at the first).
MIGRATIONS[8] = function(progress)
    progress.Quest = progress.Quest or Quests.DONE
    return progress
end

-- Version 13 replaced the Thunder Jelly with the Storm Bumblebee (November 9, 2026): a pet or a Codex entry of the old one
-- becomes the new one (unknown, they were dropped).
local V12_PETS = {
    ThunderJelly = "StormBumblebee",
}

MIGRATIONS[12] = function(progress)
    if typeof(progress.Pets) == "table" then
        for _, pet in progress.Pets do
            if typeof(pet) == "table" and V12_PETS[pet.PetId] then
                pet.PetId = V12_PETS[pet.PetId]
            end
        end
    end
    if typeof(progress.Codex) == "table" and typeof(progress.Codex.Found) == "table" then
        for i, petId in progress.Codex.Found do
            if V12_PETS[petId] then
                progress.Codex.Found[i] = V12_PETS[petId]
            end
        end
    end
    return progress
end

-- Playtesting in Studio: with ServerStorage's StudioTestSave attribute set, saves go to a separate store of that name, so
-- each new name starts a new player and a real save can't be touched (set to true, a store called "StudioTestSave").
-- Ignored outside Studio.
local studioTestSave = nil
if RunService:IsStudio() then
    local name = game:GetService("ServerStorage"):GetAttribute("StudioTestSave")
    studioTestSave = if typeof(name) == "string" and name ~= "" then name elseif name then "StudioTestSave" else nil
end

local store = nil
local storeOk, storeResult = pcall(function()
    return DataStoreService:GetDataStore(studioTestSave or DATASTORE_NAME)
end)
if storeOk then
    store = storeResult
else
    warn("PlayerData: DataStores are unavailable: " .. tostring(storeResult))
end

local startingRank = Ranks.getRank(GameConfig.StartingRank)

local profiles = {}

local function sanitizeProgress(raw)
    local progress = {
        Qi = GameConfig.StartingQi,
        RankId = startingRank.Id,
        Pets = {},
        EquippedPetIds = {},
        AuraPetInstanceId = nil,
        Relics = {},
        OutfitId = nil,
        Eggs = {},
        SpiritStones = 0,
        Weapons = {},
        EquippedWeapon = nil,
        Quest = 1,
        ForgeElements = {},
        Settings = Settings.sanitize(nil),
        Rewards = Rewards.sanitize(nil),
        Codex = Codex.sanitize(nil),
        Titles = TitleBook.sanitize(nil),
        Merchant = MerchantLedger.sanitize(nil),
    }

    if typeof(raw) ~= "table" then
        return progress
    end

    if typeof(raw.Qi) == "number" and raw.Qi == raw.Qi then
        progress.Qi = math.clamp(math.floor(raw.Qi), 0, MAX_QI)
    end

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
                table.insert(progress.Pets, {
                    InstanceId = pet.InstanceId, PetId = pet.PetId, Level = PetRules.level(pet), Locked = pet.Locked == true,
                })
            end
        end
    end

    if typeof(raw.EquippedPetIds) == "table" then
        for _, instanceId in raw.EquippedPetIds do
            if #progress.EquippedPetIds >= PassRules.MostEquipped then -- (the slots pass's owners: GamePassService trims the rest)
                break
            end

            if typeof(instanceId) == "string" and ownedIds[instanceId] and not table.find(progress.EquippedPetIds, instanceId) then
                table.insert(progress.EquippedPetIds, instanceId)
            end
        end
    end

    if typeof(raw.AuraPetInstanceId) == "string" and table.find(progress.EquippedPetIds, raw.AuraPetInstanceId) then
        progress.AuraPetInstanceId = raw.AuraPetInstanceId
    end

    if typeof(raw.Relics) == "table" then
        for _, relicId in raw.Relics do
            if typeof(relicId) == "string" and Discoveries.getRelic(relicId) and not table.find(progress.Relics, relicId) then
                table.insert(progress.Relics, relicId)
            end
        end
    end

    -- OutfitService checks ownership again before dressing anyone in it
    if typeof(raw.OutfitId) == "string" and GameConfig.Outfits and GameConfig.Outfits[raw.OutfitId] then
        progress.OutfitId = raw.OutfitId
    end

    progress.Eggs = EggInventory.sanitize(raw.Eggs)
    progress.SpiritStones = Wallet.sanitize(raw.SpiritStones)
    progress.Weapons, progress.EquippedWeapon = WeaponInventory.sanitize(raw.Weapons, raw.EquippedWeapon)
    progress.ForgeElements = Elements.sanitize(raw.ForgeElements)
    progress.Quest = Quests.sanitize(raw.Quest)
    progress.Settings = Settings.sanitize(raw.Settings)
    progress.Rewards = Rewards.sanitize(raw.Rewards)
    progress.Codex = Codex.sanitize(raw.Codex)
    progress.Titles = TitleBook.sanitize(raw.Titles)
    progress.Merchant = MerchantLedger.sanitize(raw.Merchant)

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

-- The player's Qi and Rank leaderstats values (nil until their data has loaded).
function PlayerData.getStats(player)
    local leaderstats = player:FindFirstChild("leaderstats")
    return leaderstats and leaderstats:FindFirstChild("Qi"), leaderstats and leaderstats:FindFirstChild("Rank")
end

local function captureProgress(player)
    local qi, rankValue = PlayerData.getStats(player)
    local pets = PetInventory.exportData(player)
    local relics = Discoveries.exportData(player)
    local eggs = EggInventory.exportData(player)
    local stones = Wallet.exportData(player)
    local weapons = WeaponInventory.exportData(player)
    local elements = Elements.exportData(player)
    local quest = Quests.exportData(player)
    local settings = Settings.exportData(player)
    local rewards = Rewards.exportData(player)
    local codex = Codex.exportData(player)
    -- (titles not set up yet: the ones loaded are kept, so a fault in them can never stop the rest from saving)
    local loaded = profiles[player] and profiles[player].progress
    local titles = TitleBook.exportData(player) or (loaded and loaded.Titles) or TitleBook.sanitize(nil)
    -- (the merchant's ledger likewise: kept as loaded until MerchantService sets it up)
    local merchant = MerchantLedger.exportData(player) or (loaded and loaded.Merchant) or MerchantLedger.sanitize(nil)
    if not (qi and rankValue and pets and relics and eggs and stones and weapons and elements and quest and settings and rewards and codex) then
        -- nothing is saved until every part is set up: say once which part is missing, or a session could go unsaved unseen
        local profile = profiles[player]
        if profile and profile.status == "Loaded" and not profile.warnedCapture then
            profile.warnedCapture = true
            local missing = {}
            for name, value in { Qi = qi, Rank = rankValue, Pets = pets, Relics = relics, Eggs = eggs, SpiritStones = stones,
                Weapons = weapons, ForgeElements = elements, Quest = quest, Settings = settings, Rewards = rewards, Codex = codex } do
                if not value then
                    table.insert(missing, name)
                end
            end
            table.sort(missing)
            warn("PlayerData: not saving " .. profile.key .. " yet: not set up: " .. table.concat(missing, ", "))
        end
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
        OutfitId = player:GetAttribute("OutfitId"),
        Eggs = eggs,
        SpiritStones = stones,
        Weapons = weapons.Weapons,
        EquippedWeapon = weapons.Equipped,
        ForgeElements = elements,
        Quest = quest,
        Settings = settings,
        Rewards = rewards,
        Codex = codex,
        Titles = titles,
        Merchant = merchant,
    }
end

local NO_STORE = "PlayerData: no DataStore" -- our own error when the store never opened (matched exactly below)

local function isPermanentError(message)
    message = tostring(message)
    return string.find(message, "StudioAccessToApisNotAllowed") ~= nil
        or string.find(message, "publish") ~= nil
        or string.find(message, NO_STORE, 1, true) ~= nil
end

local function claimSession(stored, sessionId, takeOver)
    stored = if stored == nil then {} else stored

    if typeof(stored) ~= "table" or (stored.Progress ~= nil and typeof(stored.Progress) ~= "table") then
        return "Corrupt", nil
    end

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

local function writeRecord(profile, progress, releaseClaim)
    local accepted = false

    local ok, err = pcall(function()
        store:UpdateAsync(profile.key, function(stored)
            accepted = false
            if typeof(stored) ~= "table" or typeof(stored.Session) ~= "table" or stored.Session.Id ~= profile.sessionId then
                return nil
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
                error(NO_STORE)
            end

            store:UpdateAsync(profile.key, function(stored)
                result, record = claimSession(stored, profile.sessionId, takeOver)
                return if result == "Loaded" then record else nil
            end)
        end)

        if not ok then
            result = "Error"
            warn("PlayerData: load failed for " .. profile.key .. ": " .. tostring(err))
        elseif result == "Corrupt" then
            warn("PlayerData: the saved record of " .. profile.key .. " is not readable (Corrupt): left untouched, player not loaded")
        end

        local shouldRetry = (result == "Locked" or result == "Error")
            and not (not ok and isPermanentError(err))
            and player.Parent == Players
            and attempt < LOAD_ATTEMPTS
        if not shouldRetry then
            break
        end

        task.wait(LOAD_RETRY_DELAY)
        if player.Parent ~= Players then
            break -- left during the wait: never take over a lock for a player who is gone
        end
    end

    if result == "Loaded" then
        local version = if typeof(record.SchemaVersion) == "number" then record.SchemaVersion else SCHEMA_VERSION
        profile.isNew = record.Progress == nil
        profile.progress = sanitizeProgress(if record.Progress then migrate(record.Progress, version) else nil)
        profile.canSave = true
        profile.status = "Loaded"
    elseif RunService:IsStudio() then
        warn("PlayerData: couldn't load data (" .. result .. "). This Studio session will NOT be saved.")
        profile.isNew = true
        profile.progress = sanitizeProgress(nil)
        profile.status = "Loaded"
    else
        profile.status = "Failed"
        if player.Parent == Players then
            -- a server still running an older version must not touch a newer save: this happens after a publish
            player:Kick(if result == "TooNew"
                then "This server runs an older version of the game. Your progress is safe: please rejoin in a moment."
                else "Your saved progress couldn't be loaded. Please rejoin in a moment.")
        end
    end

    profile.lastSaveTime = os.clock()
    profile.loaded:Fire()
end

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

-- Whether this server saves the player's data: it loaded from the store and no other server took it.
-- False for fresh Studio data after a failed load, which must not reach anything shared.
function PlayerData.canSave(player)
    local profile = profiles[player]
    return profile ~= nil and profile.canSave
end

function PlayerData.save(player)
    local profile = profiles[player]
    if not profile or not profile.canSave or profile.isReleasing then
        return
    end

    -- a write in flight holds an older snapshot, and one that just landed holds the cooldown: this
    -- change is saved as soon as they allow, never left for the next autosave
    if profile.isSaving or os.clock() - profile.lastSaveTime < WRITE_COOLDOWN then
        PlayerData.saveSoon(player)
        return
    end

    local progress = captureProgress(player)
    if not progress then
        return
    end

    profile.isSaving = true
    writeRecord(profile, progress, false)
    profile.lastSaveTime = os.clock()
    profile.isSaving = false
    if not profile.canSave and player.Parent == Players then
        -- another server took the save over: playing on here would never be saved
        player:Kick("Your progress continues in another server. Rejoin to keep playing.")
    end
end

function PlayerData.saveSoon(player)
    local profile = profiles[player]
    if not profile or profile.quickSaveScheduled then
        return
    end

    profile.quickSaveScheduled = true
    local delay = math.max(if profile.isSaving then BUSY_RETRY else 0, profile.lastSaveTime + MIN_SECONDS_BETWEEN_SAVES - os.clock())

    task.delay(delay, function()
        profile.quickSaveScheduled = false
        PlayerData.save(player)
    end)
end

function PlayerData.release(player)
    local profile = profiles[player]
    if profile and profile.isReleasing then
        return
    end

    local finalProgress = if profile and profile.status == "Loaded" then captureProgress(player) else nil

    PetInventory.removePlayer(player)
    Discoveries.removePlayer(player)
    EggInventory.removePlayer(player)
    Wallet.removePlayer(player)
    WeaponInventory.removePlayer(player)
    Elements.removePlayer(player)
    Quests.removePlayer(player)
    Settings.removePlayer(player)
    Rewards.removePlayer(player)
    TitleBook.removePlayer(player)
    MerchantLedger.removePlayer(player)

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
