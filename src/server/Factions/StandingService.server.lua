-- Faction standing and the weekly rivalry (GameConfig.Renown; the rules are shared/StandingRules, the saved state StandingBook, the cross-server tally FactionWar).
-- A member of a faction (the "Faction" attribute, FactionBook) earns renown for it from what the server itself sees:
--   a goal claimed (Quests.Moment "GoalClaimed", GoalService), a guardian conquest ("Conquer", Guardian:weaken through ConquestService), an egg carried home ("Secure"),
--   and the daily cache (below).
-- Renown climbs the ranks: each pays its stones once (a rank the wallet could not pay yet is paid at the next touch or join) and, from the second, fires
-- Quests.Moment "FactionRank" (TitleService gives the rank's title). The daily cache is the faction's stipend, claimed once a UTC day, bigger with rank. The weekly
-- rivalry (FactionWar) adds every server's renown; the week after, a member of the winning faction who earned MinRenown of that week may take the Victory share.
--   StandingEvent, client to server: "Get" | "Cache" | "Victory"
--   StandingEvent, server to client: "State", { Faction, Renown, Rank, Paid, CacheReady, Week, WeekRenown, Totals = { [faction] = { Renown, Members } },
--                                    Last = { Week, Totals, Winner, Mine, Ready, Claimed } } | "Paid", kind ("Cache" | "Victory" | "Rank"), stones, extra
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local GoalRules = require(ReplicatedStorage:WaitForChild("GoalRules"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local StandingRules = require(ReplicatedStorage:WaitForChild("StandingRules"))
local Server = script.Parent.Parent
local Analytics = require(Server:WaitForChild("Analytics"):WaitForChild("Analytics"))
local PlayerData = require(Server:WaitForChild("Data"):WaitForChild("PlayerData"))
local Quests = require(Server:WaitForChild("Quests"):WaitForChild("Quests"))
local QiBoost = require(Server:WaitForChild("Shop"):WaitForChild("QiBoost"))
local Wallet = require(Server:WaitForChild("Shop"):WaitForChild("Wallet"))
local StandingBook = require(script.Parent:WaitForChild("StandingBook"))
local FactionWar = require(script.Parent:WaitForChild("FactionWar"))

local CONFIG = GameConfig.Renown
local THROTTLE = 0.5
local PUSH_EVERY = 1

local ready = {}       -- [player] = true once their standing is loaded
local lastRequest = {}
local busy = {}
local pushAt, pending = {}, {}

local function factionOf(player)
    local id = player:GetAttribute("Faction")
    return if typeof(id) == "string" and CONFIG.RankNames[id] then id else nil
end

local function stateOf(player, data)
    local faction = factionOf(player)
    local week = GoalRules.weekKey()
    local lastTotals = FactionWar.totals(week - 1)
    return {
        Faction = faction, Renown = data.Renown, Rank = StandingRules.rankOf(data.Renown), Paid = data.Paid,
        CacheReady = data.CacheDay ~= GoalRules.dayKey(), Week = week, WeekRenown = data.WeekRenown, Totals = FactionWar.totals(week),
        Last = {
            Week = week - 1, Totals = lastTotals, Winner = StandingRules.winner(lastTotals), Mine = if data.LastWeek == week - 1 then data.LastRenown else 0,
            Ready = FactionWar.ready(week - 1), Claimed = data.WarClaimed == week - 1,
        },
    }
end

local function push(player)
    local data = StandingBook.get(player)
    if not (data and ready[player]) or player.Parent ~= Players or not factionOf(player) then
        return
    end
    pushAt[player] = os.clock()
    pending[player] = nil
    RemoteEvents.StandingEvent:FireClient(player, "State", stateOf(player, data))
end

local function schedule(player)
    if not ready[player] or pending[player] then
        return
    end
    local wait = PUSH_EVERY - (os.clock() - (pushAt[player] or -math.huge))
    if wait <= 0 then
        push(player)
    else
        pending[player] = true
        task.delay(wait, push, player)
    end
end

-- pays the ranks reached and not yet paid (lowest first); the stones paid in all, and the ranks reached that carry a title
local function settle(player, data)
    local stones, titled = 0, {}
    if Wallet.exportData(player) == nil then
        return 0, titled
    end
    local realm = Shop.playerRealmIndex(player)
    for _, rank in StandingRules.owed(data) do
        local amount = StandingRules.rankStones(rank, realm)
        if amount == 0 or Wallet.add(player, amount, "FactionRank", rank) then
            data.Paid = rank
            stones += amount
            if rank >= 2 then
                table.insert(titled, rank)
            end
        else
            break
        end
    end
    return stones, titled
end

local function announce(player, stones, titled)
    for _, rank in titled do
        Quests.Moment:Fire(player, "FactionRank", rank)
    end
    if stones > 0 then
        RemoteEvents.StandingEvent:FireClient(player, "Paid", "Rank", stones, StandingRules.rankOf(StandingBook.get(player).Renown))
    end
end

local function earn(player, source)
    local faction = factionOf(player)
    local data = ready[player] and faction and StandingBook.get(player)
    local amount = CONFIG.Sources[source]
    if not data or not amount then
        return
    end
    local week = GoalRules.weekKey()
    local first = StandingRules.earn(data, week, amount)
    FactionWar.add(week, faction, amount, first)
    local stones, titled = settle(player, data)
    PlayerData.saveSoon(player)
    Analytics.event(player, "Renown", amount, source)
    announce(player, stones, titled)
    schedule(player)
end

Quests.Moment.Event:Connect(function(player, kind)
    if typeof(player) ~= "Instance" or not player:IsA("Player") then
        return
    end
    if kind == "GoalClaimed" then
        earn(player, "Goal")
    elseif kind == "Conquer" then
        earn(player, "Conquest")
    elseif kind == "Secure" then
        earn(player, "Secure")
    end
end)

local function claimCache(player)
    local faction = factionOf(player)
    local data = ready[player] and faction and StandingBook.get(player)
    if not data or busy[player] or data.CacheDay == GoalRules.dayKey() or Wallet.exportData(player) == nil then
        return
    end
    busy[player] = true
    local amount = StandingRules.cacheStones(StandingRules.rankOf(data.Renown), Shop.playerRealmIndex(player))
    if Wallet.add(player, amount, "FactionCache", faction) then
        data.CacheDay = GoalRules.dayKey()
        busy[player] = nil
        PlayerData.saveSoon(player)
        RemoteEvents.StandingEvent:FireClient(player, "Paid", "Cache", amount, CONFIG.Sources.Cache)
        earn(player, "Cache")
        return
    end
    busy[player] = nil
end

local function claimVictory(player)
    local faction = factionOf(player)
    local data = ready[player] and faction and StandingBook.get(player)
    local week = GoalRules.weekKey()
    if not data or busy[player] or data.WarClaimed == week - 1 or data.LastWeek ~= week - 1 or data.LastRenown < CONFIG.War.MinRenown
        or not FactionWar.ready(week - 1) or StandingRules.winner(FactionWar.totals(week - 1)) ~= faction
        or Wallet.exportData(player) == nil or not QiBoost.isSetUp(player) then
        return
    end
    busy[player] = true
    local realm = Shop.playerRealmIndex(player)
    local amount = StandingRules.warStones(realm)
    if Wallet.add(player, amount, "FactionVictory", week - 1) then
        data.WarClaimed = week - 1
        local room = math.floor((GameConfig.TimedBoost.MaxMinutes * 60 - QiBoost.secondsLeft(player)) / 60)
        local minutes = math.max(0, math.min(CONFIG.War.BoostMinutes, room))
        if minutes > 0 then
            QiBoost.add(player, minutes)
        end
        PlayerData.saveSoon(player)
        Analytics.event(player, "FactionVictory", 1, faction)
        RemoteEvents.StandingEvent:FireClient(player, "Paid", "Victory", amount, minutes)
    end
    busy[player] = nil
    push(player)
end

RemoteEvents.StandingEvent.OnServerEvent:Connect(function(player, action)
    if not ready[player] or os.clock() - (lastRequest[player] or 0) < THROTTLE then
        return
    end
    lastRequest[player] = os.clock()
    if action == "Get" then
        push(player)
    elseif action == "Cache" then
        claimCache(player)
        push(player)
    elseif action == "Victory" then
        claimVictory(player)
    end
end)

local function setupPlayer(player)
    local progress = PlayerData.waitForData(player)
    if not progress or player.Parent ~= Players then
        return
    end
    StandingBook.setupPlayer(player, progress)
    ready[player] = true
    -- ranks reached earlier that could not be paid then (the wallet was not up): now (and their titles)
    local data = StandingBook.get(player)
    local stones, titled = settle(player, data)
    if stones > 0 then
        PlayerData.saveSoon(player)
    end
    for rank = 2, StandingRules.rankOf(data.Renown) do
        if data.Paid >= rank then
            table.insert(titled, rank) -- (giving a title twice does nothing: one lost to an earlier hiccup is given back)
        end
    end
    local faction
    local t = os.clock()
    while not faction and os.clock() - t < 90 and player.Parent == Players do
        faction = factionOf(player)
        if not faction then
            task.wait(2)
        end
    end
    if faction then
        for _, rank in titled do
            Quests.Moment:Fire(player, "FactionRank", rank)
        end
    end
    push(player)
end

Players.PlayerAdded:Connect(setupPlayer)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
Players.PlayerRemoving:Connect(function(player)
    ready[player], lastRequest[player], busy[player], pushAt[player], pending[player] = nil, nil, nil, nil, nil
end)

FactionWar.start()
-- a new day or week reaches players already online, and what the other servers earned comes with it
while true do
    task.wait(30)
    for player in ready do
        local ok, err = pcall(push, player)
        if not ok then
            warn("StandingService: push for " .. player.Name .. " failed: " .. tostring(err))
        end
    end
end
