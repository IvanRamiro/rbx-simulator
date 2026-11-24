-- Gives out titles (shared/TitleRules) as a player earns them, and takes their choice of which to wear from their Titles
-- window. Earned on joining: Developer (GameConfig.Titles.DeveloperUserIds) and Beta Tester (joining while GameConfig.Beta
-- is Active; saved like any earned title, so it is given once and kept after the beta ends). Earned as they go (looked at every few seconds): the title of every realm they have
-- reached, the beast collector titles and Keeper of Secrets (their Spirit Beast Codex), Relic Seeker (every relic found).
-- Earned at the moment: a guardian's title, for carrying an egg of its home (Guardian.lua's "Secure" moment).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local TitleRules = require(ReplicatedStorage:WaitForChild("TitleRules"))
local CodexRules = require(ReplicatedStorage:WaitForChild("CodexRules"))

local serverRoot = script.Parent.Parent
local PlayerData = require(serverRoot:WaitForChild("Data"):WaitForChild("PlayerData"))
local Codex = require(serverRoot:WaitForChild("Pets"):WaitForChild("Codex"))
local Discoveries = require(serverRoot:WaitForChild("World"):WaitForChild("Discoveries"))
local Quests = require(serverRoot:WaitForChild("Quests"):WaitForChild("Quests"))
local TitleBook = require(script.Parent:WaitForChild("TitleBook"))

local CHECK_EVERY = 2
local THROTTLE = 0.2

local lastRequest = {}

local joining = {} -- [player] = the titles they qualified for as they joined (announced once, together)

-- Gives a title; tells them when it is new (their window's badge and a notice) and saves it.
local function award(player, id)
    if TitleBook.earn(player, id) then
        if joining[player] then
            table.insert(joining[player], id)
        else
            RemoteEvents.TitleEvent:FireClient(player, "Earned", id)
            TitleBook.publish(player)
        end
        PlayerData.saveSoon(player)
        return true
    end
    return false
end

-- counted over the beasts that can be hatched, as the Codex window counts them (CodexRules.Pets)
local function beastsFound(player)
    local count, secret = 0, false
    for _, petId in CodexRules.Pets do
        if Codex.isFound(player, petId) then
            count += 1
            secret = secret or GameConfig.Pets[petId].Rarity == "Secret"
        end
    end
    return count, secret
end

local function check(player)
    if not TitleBook.isSetUp(player) then
        return
    end
    -- every realm up to the one they are in (a realm's title is kept even if their Qi ever fell back below it)
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    local realmId = rank and TitleRules.RealmTitleIds[rank.Realm]
    local realm = realmId and TitleRules.ById[realmId].RealmIndex or 0
    for index = 1, realm do
        award(player, "Realm" .. index)
    end
    -- a member's faction title, for good (the pledge is read a moment after joining: FactionBook)
    local factionInfo = GameConfig.Faction.Factions[player:GetAttribute("Faction") or ""]
    if factionInfo then
        award(player, factionInfo.TitleId)
    end
    local count, secret = beastsFound(player)
    for _, entry in TitleRules.CollectorTitles do
        if count >= entry.Count then
            award(player, entry.Id)
        end
    end
    if secret then
        award(player, "SecretKeeper")
    end
    if Discoveries.isSetUp(player) then
        local all = #GameConfig.Relics > 0
        for _, relic in GameConfig.Relics do
            all = all and Discoveries.hasFound(player, relic.Id)
        end
        if all then
            award(player, "RelicSeeker")
        end
    end
end

local function setupPlayer(player)
    local progress, isNewPlayer = PlayerData.waitForData(player)
    if not progress or player.Parent ~= Players then
        return
    end
    TitleBook.setupPlayer(player, if isNewPlayer then nil else progress)
    joining[player] = {}
    local beta = GameConfig.Beta
    if beta and beta.Active == true and typeof(beta.TitleId) == "string" and TitleRules.ById[beta.TitleId] then
        award(player, beta.TitleId)
    end
    check(player)
    local found = joining[player]
    joining[player] = nil
    TitleBook.publish(player)
    if #found > 0 then
        RemoteEvents.TitleEvent:FireClient(player, "EarnedOnJoin", #found, found)
    end
end

Players.PlayerAdded:Connect(setupPlayer)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
Players.PlayerRemoving:Connect(function(player)
    lastRequest[player] = nil
    joining[player] = nil
end)

Quests.Moment.Event:Connect(function(player, kind, guardianId)
    if kind == "Secure" and typeof(guardianId) == "string" then
        local id = TitleRules.GuardianTitleIds[guardianId]
        if id then
            award(player, id)
        end
    end
end)

-- a guardian's ladder finished (ConquestService): its conquest title
Quests.Moment.Event:Connect(function(player, kind, guardianId)
    if kind == "Master" and typeof(guardianId) == "string" then
        local id = TitleRules.ConquestTitleIds[guardianId]
        if id then
            award(player, id)
        end
    end
end)

-- a faction rank reached (StandingService): its title, for a member of that faction
Quests.Moment.Event:Connect(function(player, kind, rank)
    if kind == "FactionRank" and typeof(rank) == "number" then
        local ids = TitleRules.FactionRankTitleIds[player:GetAttribute("Faction") or ""]
        local id = ids and ids[rank]
        if id then
            award(player, id)
        end
    end
end)

RemoteEvents.TitleEvent.OnServerEvent:Connect(function(player, action, choice)
    if os.clock() - (lastRequest[player] or 0) < THROTTLE then
        return
    end
    lastRequest[player] = os.clock()
    if action == "Wear" then
        if TitleBook.wear(player, choice) then
            PlayerData.saveSoon(player)
        end
        TitleBook.publish(player)
    elseif action == "Get" then
        TitleBook.publish(player)
    end
end)

task.spawn(function()
    while true do
        task.wait(CHECK_EVERY)
        for _, player in Players:GetPlayers() do
            check(player)
        end
    end
end)
