-- The guardian bounty (GameConfig.Bounty; the rules are shared/BountyRules, the saved state ConquestBook). A conquest is a fight that brought a guardian down to Weakened
-- with the player having dealt ConquestShare of it (Guardian:weaken fires Quests.Moment "Conquer", player, guardianId). Counted here, and paid at once:
--   the tier stones of each guardian's ladder when a count reaches a tier (once; "Paid" in the save says how many tiers are paid, so a payment that the wallet could not
--   take yet is made the next time the board is touched or the player joins), and the day's bounty on the first conquest of the guardian marked for the day.
--   a ladder's last tier also fires Quests.Moment "Master" (TitleService gives the guardian's conquest title).
-- Every guardian model carries the attribute "Bounty" (true on the marked one), so its health bar can say so.
--   BountyEvent, client to server: "Get" (send the state again)
--   BountyEvent, server to client: "State", { Counts, Paid, DayPaid, Marked, Day } | "Conquered", guardianId, count, bountyStones, tierStones, tiersReached
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local BountyRules = require(ReplicatedStorage:WaitForChild("BountyRules"))
local GoalRules = require(ReplicatedStorage:WaitForChild("GoalRules"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local Server = script.Parent.Parent
local Analytics = require(Server:WaitForChild("Analytics"):WaitForChild("Analytics"))
local PlayerData = require(Server:WaitForChild("Data"):WaitForChild("PlayerData"))
local Quests = require(Server:WaitForChild("Quests"):WaitForChild("Quests"))
local Wallet = require(Server:WaitForChild("Shop"):WaitForChild("Wallet"))
local ConquestBook = require(script.Parent:WaitForChild("ConquestBook"))

local THROTTLE = 0.5
local MARK_EVERY = 20 -- seconds between looks at which guardian is marked (a new day, a guardian that streamed in late)

local ready = {}      -- [player] = true once their board is loaded
local lastRequest = {}
local lastCount = {}  -- [player] = { [guardianId] = os.clock() of the conquest last counted }
local busy = {}       -- [player] = true while a payment is made

local function snapshot(data)
    return { Counts = data.Counts, Paid = data.Paid, DayPaid = data.DayPaid, Day = data.Day, Marked = BountyRules.marked(GoalRules.dayKey()) }
end

local function push(player)
    local data = ConquestBook.get(player)
    if data and ready[player] and player.Parent == Players then
        RemoteEvents.BountyEvent:FireClient(player, "State", snapshot(data))
    end
end

-- pays every tier reached and not yet paid, lowest first: the stones paid in total, and the guardian ids whose ladder is now complete
local function settle(player, data)
    local stones, finished = 0, {}
    if Wallet.exportData(player) == nil then
        return 0, finished -- (their wallet isn't set up yet: nothing is marked paid until it can take it)
    end
    local realm = Shop.playerRealmIndex(player)
    for _, owed in BountyRules.owed(data) do
        local id, tier = owed[1], owed[2]
        local amount = BountyRules.tierStones(tier, realm)
        if Wallet.add(player, amount, "BountyTier", id .. tier) then
            data.Paid[id] = tier
            stones += amount
            if tier == #BountyRules.tiers then
                table.insert(finished, id)
            end
        else
            break
        end
    end
    return stones, finished
end

local function conquered(player, guardianId)
    if not ready[player] or busy[player] or typeof(guardianId) ~= "string" or not table.find(BountyRules.order, guardianId) then
        return
    end
    local data = ConquestBook.get(player)
    if not data then
        return
    end
    local times = lastCount[player]
    if not times then
        times = {}
        lastCount[player] = times
    end
    local now = os.clock()
    if times[guardianId] and now - times[guardianId] < GameConfig.Bounty.Cooldown then
        return -- (the same fight counted twice: a guardian that healed and was weakened again at once)
    end
    times[guardianId] = now
    busy[player] = true
    data.Counts[guardianId] = math.min((data.Counts[guardianId] or 0) + 1, 1e6)
    -- the day's bounty: the marked guardian's first conquest today
    local bounty = 0
    if guardianId == BountyRules.marked(GoalRules.dayKey()) and not data.DayPaid and Wallet.exportData(player) ~= nil then
        local amount = BountyRules.dailyStones(Shop.playerRealmIndex(player))
        if Wallet.add(player, amount, "Bounty", guardianId) then
            data.DayPaid = true
            bounty = amount
        end
    end
    local tierStones, finished = settle(player, data)
    busy[player] = nil
    PlayerData.saveSoon(player)
    Analytics.event(player, "GuardianConquered", data.Counts[guardianId], guardianId)
    for _, id in finished do
        Quests.Moment:Fire(player, "Master", id)
    end
    RemoteEvents.BountyEvent:FireClient(player, "Conquered", guardianId, data.Counts[guardianId], bounty, tierStones, BountyRules.reached(data.Counts[guardianId]))
    push(player)
end

Quests.Moment.Event:Connect(function(player, kind, guardianId)
    if kind == "Conquer" and typeof(player) == "Instance" and player:IsA("Player") then
        local ok, err = pcall(conquered, player, guardianId)
        if not ok then
            busy[player] = nil
            warn("ConquestService: a conquest by " .. player.Name .. " failed: " .. tostring(err))
        end
    end
end)

RemoteEvents.BountyEvent.OnServerEvent:Connect(function(player, action)
    if not ready[player] or os.clock() - (lastRequest[player] or 0) < THROTTLE then
        return
    end
    lastRequest[player] = os.clock()
    if action == "Get" then
        push(player)
    end
end)

local function setupPlayer(player)
    local progress = PlayerData.waitForData(player)
    if not progress or player.Parent ~= Players then
        return
    end
    ConquestBook.setupPlayer(player, progress)
    ready[player] = true
    -- tiers reached earlier that could not be paid then (the wallet was not up): now
    local data = ConquestBook.get(player)
    local stones = settle(player, data)
    if stones > 0 then
        PlayerData.saveSoon(player)
    end
    -- every finished ladder's title (giving one twice does nothing, so a title lost to an earlier hiccup is given back here)
    for _, id in BountyRules.order do
        if data.Paid[id] == #BountyRules.tiers then
            Quests.Moment:Fire(player, "Master", id)
        end
    end
    push(player)
end

Players.PlayerAdded:Connect(setupPlayer)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
Players.PlayerRemoving:Connect(function(player)
    ready[player], lastRequest[player], lastCount[player], busy[player] = nil, nil, nil, nil
end)

-- the marked guardian wears a BOUNTY on its health bar (model attribute), and a new day reaches players already online
local folder = workspace:WaitForChild("Guardians")
local markedDay
while true do
    local marked = BountyRules.marked(GoalRules.dayKey())
    for _, model in folder:GetChildren() do
        local id = model:GetAttribute("GuardianId")
        if id ~= nil then
            local want = id == marked
            if model:GetAttribute("Bounty") ~= want then
                model:SetAttribute("Bounty", want)
            end
        end
    end
    if markedDay ~= marked then
        if markedDay ~= nil then
            for player in ready do
                pcall(push, player)
            end
        end
        markedDay = marked
    end
    task.wait(MARK_EVERY)
end
