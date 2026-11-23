-- The Spin Wheel in the hub (GameConfig.SpinWheel, shared/SpinRules; the wheel: SpinWheelBuilder). The server decides everything:
-- it rolls the segment, saves the spin as taken with its reward pending (SpinLedger), tells every client to turn the world wheel
-- onto that segment, and pays the reward when the wheel stops (or, if the player left meanwhile, when they next join).
-- One wheel for the whole server: while it turns, other spins wait.
--
-- SpinEvent, client to server: "Spin".
-- Server to client: "Open" (the wheel's prompt was used), "Refused" text, "Spun" { Segment, SpinsLeft } (the spinner),
--   "Turn" { From, To, Start, Seconds, Segment, UserId } (everyone: the world wheel's turn), "Won" { Segment, Kind, Text, Late }
--   (the spinner, once paid), "Jackpot" name (everyone), "Bought" { Spins } (the buyer, from ProductService, once a purchase of
--   spins is saved).
-- Spins bought with Robux (GameConfig.SpinWheel.SpinProducts) are paid by ProductService into SpinLedger; a spin takes them only
-- after the day's free and won ones (SpinLedger.take).
-- Attributes: the player's "SpinsLeft" (bought ones included) and "SpinsBought" (SpinLedger.publish); the wheel model's "Rest"
-- (degrees it rests at) and "TurningUntil" (server time).
local Players = game:GetService("Players")
local PolicyService = game:GetService("PolicyService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local SpinRules = require(ReplicatedStorage:WaitForChild("SpinRules"))
local Server = script.Parent.Parent
local Analytics = require(Server:WaitForChild("Analytics"):WaitForChild("Analytics"))
local EggInventory = require(Server:WaitForChild("Pets"):WaitForChild("EggInventory"))
local MovementGuard = require(Server:WaitForChild("Security"):WaitForChild("MovementGuard"))
local PlayerData = require(Server:WaitForChild("Data"):WaitForChild("PlayerData"))
local QiReward = require(Server:WaitForChild("Cultivation"):WaitForChild("QiReward"))
local Wallet = require(Server:WaitForChild("Shop"):WaitForChild("Wallet"))
local WorldConfig = require(Server:WaitForChild("World"):WaitForChild("WorldConfig"))
local SpinLedger = require(script.Parent:WaitForChild("SpinLedger"))

local config = GameConfig.SpinWheel
local THROTTLE = 1
local SETTLE = 0.6 -- seconds the wheel's overshoot settles after its turn

local random = Random.new()
local ready = {}
local lastRequest = {}
local wheel = nil -- the wheel's model, once it's found
local turningUntil = 0 -- os.clock() the wheel is free again

local function publish(player)
    SpinLedger.publish(player)
end

local function refuse(player, text)
    RemoteEvents.SpinEvent:FireClient(player, "Refused", text)
end

local function untilReset()
    local seconds = SpinRules.secondsToReset(os.time())
    local hours, minutes = math.floor(seconds / 3600), math.ceil(seconds % 3600 / 60)
    if minutes == 60 then
        hours, minutes = hours + 1, 0
    end
    return if hours > 0 then hours .. "h " .. minutes .. "m" else math.max(1, minutes) .. "m"
end

local function promptPart()
    return wheel and wheel:FindFirstChild("Prompt")
end

local function nearWheel(player)
    local spot = promptPart()
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    return spot ~= nil and root ~= nil and not MovementGuard.isSuspect(player)
        and (root.Position - spot.Position).Magnitude <= config.Reach
end

-- what a player's own parts are set up for paying
local function canPay(player)
    return SpinLedger.isSetUp(player) and Wallet.exportData(player) ~= nil and EggInventory.exportData(player) ~= nil
        and (PlayerData.getStats(player)) ~= nil
end

-- Pays a pending spin's reward, once: it is cleared before anything is given.
local function settle(player, late)
    local data = SpinLedger.today(player)
    local pending = data and data.Pending
    if not (pending and canPay(player)) then
        return
    end
    data.Pending = nil
    local index = pending.Segment
    local segment = SpinRules.Segments[index]
    local rankName = Ranks.getPlayerRankName(player)
    -- (the kind decided when it was rolled: a restricted player's jackpot is stones; older pending prizes carry no Kind)
    local text, kind, big = nil, pending.Kind or segment.Kind, false
    if kind == "Jackpot" and pending.Kind == nil and SpinRules.restricted(player) then
        kind = "Stones" -- (a prize saved before its kind was kept: never a paid random item for a restricted player)
        pending.Stones = pending.Stones or SpinRules.fallbackStones(rankName, player)
    end
    local function payStones(amount)
        Wallet.add(player, amount, "Spin", "Segment" .. index)
        return NumberFormat.compact(amount) .. " Spirit Stones"
    end
    if kind == "Stones" then
        text = payStones(pending.Stones or SpinRules.stones(index, rankName, player))
        big = (segment.Share or 1) >= 1
    elseif kind == "Qi" then
        local qi = QiReward.grantMinutes(player, segment.Minutes)
        text = NumberFormat.compact(qi) .. " Qi (" .. segment.Minutes .. " minutes of cultivating)"
        big = segment.Minutes >= 15
    elseif kind == "Egg" or kind == "Jackpot" then
        local eggId = pending.EggId or (if kind == "Jackpot" then GameConfig.ExclusiveEgg.EggId else SpinRules.bestEgg(rankName))
        player:SetAttribute("FreeEggAt", workspace:GetServerTimeNow()) -- (the Store's thanks for a bought egg stays quiet: StoreController)
        if EggInventory.grant(player, eggId, pending.Paid == true) then
            local name = GameConfig.Eggs[eggId].DisplayName
            text = (if string.find(name, "^[AEIOUaeiou]") then "an " else "a ") .. name .. "! Hatch it at the Hatching Sanctum."
        else -- (holding the most of that egg)
            kind = "Stones"
            text = payStones(SpinRules.fallbackStones(rankName, player)) .. " (your eggs of that kind are full)"
        end
        big = true
    elseif kind == "Spin" then
        if pending.Day == SpinRules.today() then -- (won just before the reset: the new day has its own spins)
            data.Extra = math.min(config.MaxExtra, data.Extra + 1)
        end
        text = "1 more spin today!"
    end
    publish(player)
    PlayerData.saveSoon(player)
    Analytics.event(player, "WheelSpin", index, kind)
    RemoteEvents.SpinEvent:FireClient(player, "Won", { Segment = index, Kind = kind, Text = text, Big = big, Late = late == true,
        Jackpot = segment.Kind == "Jackpot" and kind ~= "Stones" })
    if segment.Kind == "Jackpot" and kind ~= "Stones" then
        RemoteEvents.SpinEvent:FireAllClients("Jackpot", player.DisplayName)
    end
end

local actions = {}

function actions.Spin(player)
    local data = SpinLedger.today(player)
    if not (data and canPay(player)) then
        return
    end
    if data.Pending then
        refuse(player, "Your spin is still turning.")
        return
    end
    if SpinRules.spinsLeft(data) <= 0 then
        refuse(player, "No spins left. New free spins in " .. untilReset()
            .. (if SpinRules.restricted(player) then "." else ", or buy more at the wheel."))
        return
    end
    if not nearWheel(player) then
        refuse(player, "Walk up to the Spin Wheel to spin.")
        return
    end
    if os.clock() < turningUntil then
        refuse(player, "The wheel is turning. Try again in a moment.")
        return
    end

    local index = SpinRules.roll(random)
    local info = SpinRules.describe(index, Ranks.getPlayerRankName(player), player)
    local _, bought = SpinLedger.take(player) -- (a free or won spin first, then a bought one)
    -- an egg won on a spin bought with Robux is a paid egg: the pet it hatches is a paid item (EggInventory, the Auction House's policy)
    data.Pending = { Segment = index, Day = data.Day, Kind = info.Kind, Stones = info.Stones, EggId = info.EggId,
        Paid = if bought then true else nil }
    publish(player)
    PlayerData.saveSoon(player)

    -- the turn: from where the wheel rests, 4 to 6 whole turns and on to the segment, landing a little off its middle
    local from = (wheel:GetAttribute("Rest") or 0) % 360
    local offset = random:NextNumber(-0.32, 0.32) * SpinRules.Step
    local onto = (-SpinRules.angleOf(index) + offset - from) % 360
    local to = from + random:NextInteger(4, 6) * 360 + onto
    local start = workspace:GetServerTimeNow()
    turningUntil = os.clock() + config.Seconds + SETTLE + 0.4
    wheel:SetAttribute("Rest", to % 360)
    wheel:SetAttribute("TurningUntil", start + config.Seconds + SETTLE)
    RemoteEvents.SpinEvent:FireAllClients("Turn", { From = from, To = to, Start = start, Seconds = config.Seconds, Segment = index,
        UserId = player.UserId })
    RemoteEvents.SpinEvent:FireClient(player, "Spun", { Segment = index, SpinsLeft = SpinRules.spinsLeft(data) })
    task.delay(config.Seconds, settle, player)
end

RemoteEvents.SpinEvent.OnServerEvent:Connect(function(player, action)
    local handler = typeof(action) == "string" and actions[action]
    if not (handler and ready[player]) or os.clock() - (lastRequest[player] or 0) < THROTTLE then
        return
    end
    lastRequest[player] = os.clock()
    handler(player)
end)

-- the wheel's prompt opens the spin window
task.spawn(function()
    local island = workspace:WaitForChild(WorldConfig.FolderName):WaitForChild(WorldConfig.StartIsland)
    wheel = island:WaitForChild("SpinWheel", 30)
    local prompt = wheel and wheel:FindFirstChild("Prompt") and wheel.Prompt:FindFirstChildOfClass("ProximityPrompt")
    if not prompt then
        warn("SpinService: " .. WorldConfig.StartIsland .. " has no SpinWheel with a prompt (SpinWheelBuilder)")
        wheel = nil
        return
    end
    wheel:SetAttribute("Rest", random:NextInteger(0, SpinRules.Count - 1) * SpinRules.Step)
    wheel:SetAttribute("TurningUntil", 0)
    prompt.Triggered:Connect(function(player)
        if ready[player] then
            RemoteEvents.SpinEvent:FireClient(player, "Open")
        end
    end)
end)

-- Whether paid random items are restricted where the player is (SpinRules.restricted). Asked before they can spin; if Roblox can't
-- answer after a few tries, the safe answer: restricted (the jackpot then pays stones, and the wheel offers no spins for Robux).
local function checkPolicy(player)
    for try = 1, 3 do
        local ok, info = pcall(PolicyService.GetPolicyInfoForPlayerAsync, PolicyService, player)
        if ok and typeof(info) == "table" then
            player:SetAttribute("RandomItemsRestricted", info.ArePaidRandomItemsRestricted == true)
            return
        end
        if player.Parent ~= Players then
            return
        end
        task.wait(try)
    end
    player:SetAttribute("RandomItemsRestricted", true)
end

local function setupPlayer(player)
    local policyChecked = false
    task.spawn(function()
        checkPolicy(player)
        policyChecked = true
    end)
    local progress, isNewPlayer = PlayerData.waitForData(player)
    if not progress or player.Parent ~= Players then
        return
    end
    SpinLedger.setupPlayer(player, if isNewPlayer then nil else progress)
    publish(player)
    -- paying needs the player's wallet, eggs and Qi (their services set them up alongside this one)
    local deadline = os.clock() + 20
    while not (canPay(player) and policyChecked) and player.Parent == Players and os.clock() < deadline do
        task.wait(0.2)
    end
    if player.Parent ~= Players then
        return
    end
    ready[player] = true
    settle(player, true) -- a spin that was still turning when they last left
end

Players.PlayerAdded:Connect(setupPlayer)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
Players.PlayerRemoving:Connect(function(player)
    ready[player], lastRequest[player] = nil, nil
end)

-- a new UTC day reaches players already online
while true do
    task.wait(15)
    -- (each player under pcall: one error used to be able to stop this loop for the whole server; bug audit, 2026-11-24)
    for player in ready do
        local ok, err = pcall(publish, player)
        if not ok then
            warn("SpinService: publish for " .. player.Name .. " failed: " .. tostring(err))
        end
    end
end
