-- The daily and weekly goals (GameConfig.Goals; the rules and the picks are shared/GoalRules, the progress is GoalBook). The server counts what really happens and
-- pays; a client only asks to claim and shows what it is told:
--   counted here   every landing strike on a guardian (Combat.Hit), every egg carried home (Quests.Moment "Secure")
--   counted by     QiService (Cultivate), PetService (Hatch), SpinService (Spin), CombatService (Combo), each through GoalBook.count
--   GoalEvent, client to server: "Get" (send the state again) | "Claim", scope ("Daily" or "Weekly"), goal id
--   GoalEvent, server to client: "State", { Day, Week, DayProgress, DayClaimed, DayBonus, WeekProgress, WeekClaimed, WeekBonus } | "Claimed", scope, goal id, stones,
--                                bonus stones, bonus minutes of 2x Qi
--   attribute "GoalsReady": how many finished goals wait to be claimed (the Rewards button's dot)
-- A claim pays the goal's stones; the claim that finishes the scope's last goal also pays the scope's bonus (stones and minutes of the timed boost, only what fits
-- under TimedBoost.MaxMinutes, as the login reward's). Nothing is marked paid until the wallet has taken it.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local GoalRules = require(ReplicatedStorage:WaitForChild("GoalRules"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local Server = script.Parent.Parent
local Analytics = require(Server:WaitForChild("Analytics"):WaitForChild("Analytics"))
local Combat = require(Server:WaitForChild("Combat"):WaitForChild("Combat"))
local PlayerData = require(Server:WaitForChild("Data"):WaitForChild("PlayerData"))
local Quests = require(Server:WaitForChild("Quests"):WaitForChild("Quests"))
local QiBoost = require(Server:WaitForChild("Shop"):WaitForChild("QiBoost"))
local Wallet = require(Server:WaitForChild("Shop"):WaitForChild("Wallet"))
local GoalBook = require(script.Parent:WaitForChild("GoalBook"))

local THROTTLE = 0.4
local PUSH_EVERY = 1 -- seconds: a burst of strikes is one message, not forty

local ready = {}        -- [player] = true once their goals are loaded
local lastRequest = {}
local busy = {}         -- [player] = true while a claim is paid
local pushAt = {}       -- [player] = os.clock() of the last State sent
local pending = {}      -- [player] = true while a State is waiting its turn

local function snapshot(data)
    return {
        Day = data.Day, Week = data.Week,
        DayProgress = data.DayProgress, DayClaimed = data.DayClaimed, DayBonus = data.DayBonus,
        WeekProgress = data.WeekProgress, WeekClaimed = data.WeekClaimed, WeekBonus = data.WeekBonus,
    }
end

local function claimable(player, data)
    local n = 0
    for _, scope in { "Daily", "Weekly" } do
        local progress, claimed = GoalBook.scopeOf(data, scope)
        local key = if scope == "Weekly" then data.Week else data.Day
        for _, goal in GoalRules.pick(scope, player.UserId, key) do
            if (progress[goal.Id] or 0) >= goal.Target and not claimed[goal.Id] then
                n += 1
            end
        end
    end
    return n
end

local function push(player)
    local data = GoalBook.get(player)
    if not (data and ready[player]) or player.Parent ~= Players then
        return
    end
    pushAt[player] = os.clock()
    pending[player] = nil
    player:SetAttribute("GoalsReady", claimable(player, data))
    RemoteEvents.GoalEvent:FireClient(player, "State", snapshot(data))
end

-- sends at once if the last send was a while ago, else after PUSH_EVERY (the latest state wins)
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

GoalBook.Changed.Event:Connect(schedule)

local function claim(player, scope, goalId)
    if (scope ~= "Daily" and scope ~= "Weekly") or typeof(goalId) ~= "string" or #goalId > 40 or busy[player] then
        return
    end
    local data = GoalBook.get(player)
    if not data or Wallet.exportData(player) == nil or not QiBoost.isSetUp(player) then
        return -- (their wallet or boost isn't set up yet: marking a claim paid now would lose it)
    end
    local progress, claimed, bonusFlag = GoalBook.scopeOf(data, scope)
    local key = if scope == "Weekly" then data.Week else data.Day
    local picks = GoalRules.pick(scope, player.UserId, key)
    local goal
    for _, g in picks do
        if g.Id == goalId then
            goal = g
        end
    end
    if not goal or claimed[goalId] or (progress[goalId] or 0) < goal.Target then
        return
    end
    busy[player] = true
    local realm = Shop.playerRealmIndex(player)
    local stones = GoalRules.stones(scope, realm)
    if not Wallet.add(player, stones, "Goal", goalId) then
        busy[player] = nil
        return
    end
    claimed[goalId] = true
    -- the scope's last goal: its bonus too
    local bonusStones, bonusMinutes = 0, 0
    local all = true
    for _, g in picks do
        all = all and claimed[g.Id] == true
    end
    if all and not data[bonusFlag] then
        local stonesBonus, minutes = GoalRules.bonus(scope, realm)
        if Wallet.add(player, stonesBonus, "GoalBonus", scope) then
            data[bonusFlag] = true
            bonusStones = stonesBonus
            local room = math.floor((GameConfig.TimedBoost.MaxMinutes * 60 - QiBoost.secondsLeft(player)) / 60)
            minutes = math.max(0, math.min(minutes, room))
            if minutes > 0 and QiBoost.add(player, minutes) then
                bonusMinutes = minutes
            end
        end
    end
    busy[player] = nil
    PlayerData.saveSoon(player)
    Analytics.event(player, "GoalClaimed", 1, goalId)
    if bonusStones > 0 then
        Analytics.event(player, "GoalBonus", 1, scope)
    end
    RemoteEvents.GoalEvent:FireClient(player, "Claimed", scope, goalId, stones, bonusStones, bonusMinutes)
    push(player)
end

RemoteEvents.GoalEvent.OnServerEvent:Connect(function(player, action, scope, goalId)
    if not ready[player] or os.clock() - (lastRequest[player] or 0) < THROTTLE then
        return
    end
    lastRequest[player] = os.clock()
    if action == "Get" then
        push(player)
    elseif action == "Claim" then
        claim(player, scope, goalId)
    end
end)

-- what the server itself sees (the other kinds are counted where they happen)
Combat.Hit.Event:Connect(function(player, target)
    if typeof(player) == "Instance" and player:IsA("Player") and typeof(target) == "Instance"
        and CollectionService:HasTag(target, GameConfig.GuardianTag) then
        GoalBook.count(player, "GuardianHit", 1)
    end
end)

Quests.Moment.Event:Connect(function(player, kind)
    if kind == "Secure" then
        GoalBook.count(player, "Secure", 1)
    end
end)

local function setupPlayer(player)
    local progress = PlayerData.waitForData(player)
    if not progress or player.Parent ~= Players then
        return
    end
    GoalBook.setupPlayer(player, progress)
    ready[player] = true
    push(player)
end

Players.PlayerAdded:Connect(setupPlayer)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
Players.PlayerRemoving:Connect(function(player)
    ready[player], lastRequest[player], busy[player], pushAt[player], pending[player] = nil, nil, nil, nil, nil
end)

-- a new day or week reaches players already online
while true do
    task.wait(60)
    for player in ready do
        local ok, err = pcall(push, player)
        if not ok then
            warn("GoalService: push for " .. player.Name .. " failed: " .. tostring(err))
        end
    end
end
