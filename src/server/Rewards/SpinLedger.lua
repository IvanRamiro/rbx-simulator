-- A player's Spin Wheel day (SpinService), saved in PlayerData as
--   Spin = { Day = <the UTC day>, Used = <free and won spins taken that day>, Extra = <spins won that day>,
--            Bought = <spins bought with Robux, not yet used>, Pending = <a spin still turning> }
-- A record of an earlier day means today's spins are all left (its extras are gone with it). Bought spins (ProductService,
-- save schema 21) never run out: a spin takes today's free and won ones first (Used), and only then a bought one. Pending is the reward a spin
-- rolled, saved the moment it is rolled and paid when the wheel stops: a player who leaves while it turns is paid on their
-- next join, so leaving can't lose it, and nothing can pay it twice.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local SpinRules = require(ReplicatedStorage:WaitForChild("SpinRules"))

local SpinLedger = {}

local config = GameConfig.SpinWheel
local MAX_USED = 1000

local state = {}

local function whole(value, most)
    return if typeof(value) == "number" and value == value and value >= 0 then math.min(math.floor(value), most) else 0
end

local function sanitizePending(raw)
    if typeof(raw) ~= "table" then
        return nil
    end
    local index = whole(raw.Segment, SpinRules.Count)
    if index < 1 then
        return nil
    end
    local pending = { Segment = index, Day = whole(raw.Day, 1e7) }
    if typeof(raw.Stones) == "number" then
        pending.Stones = whole(raw.Stones, GameConfig.SpiritStones.Max)
    end
    if typeof(raw.EggId) == "string" and GameConfig.Eggs[raw.EggId] then
        pending.EggId = raw.EggId
    end
    if raw.Paid == true then -- (rolled on a spin bought with Robux: its egg is a paid one, EggInventory; save schema 24)
        pending.Paid = true
    end
    return pending
end

function SpinLedger.sanitize(raw)
    raw = if typeof(raw) == "table" then raw else {}
    return {
        Day = whole(raw.Day, 1e7),
        Used = whole(raw.Used, MAX_USED),
        Extra = whole(raw.Extra, config.MaxExtra),
        Bought = whole(raw.Bought, config.MaxBought),
        Pending = sanitizePending(raw.Pending),
    }
end

function SpinLedger.setupPlayer(player, progress)
    state[player] = SpinLedger.sanitize(progress and progress.Spin)
end

function SpinLedger.isSetUp(player)
    return state[player] ~= nil
end

-- The player's record for today (an earlier day's is started over first); nil until they're set up.
function SpinLedger.today(player)
    local data = state[player]
    if not data then
        return nil
    end
    local today = SpinRules.today()
    if data.Day ~= today then
        data.Day, data.Used, data.Extra = today, 0, 0
    end
    return data
end

function SpinLedger.spinsLeft(player)
    local data = SpinLedger.today(player)
    return if data then SpinRules.spinsLeft(data) else 0
end

-- Takes one spin: today's free or won one if any is left, else a bought one. Returns true and whether it was a bought (Robux)
-- spin; false when none is left.
function SpinLedger.take(player)
    local data = SpinLedger.today(player)
    if not data then
        return false, false
    end
    if SpinRules.freeLeft(data) > 0 then
        data.Used += 1
        return true, false
    elseif data.Bought > 0 then
        data.Bought -= 1
        return true, true
    end
    return false, false
end

-- Whether `count` more bought spins fit under GameConfig.SpinWheel.MaxBought.
function SpinLedger.canAddBought(player, count)
    local data = state[player]
    return data ~= nil and data.Bought + count <= config.MaxBought
end

-- Adds bought spins (a negative count takes them back, never below none). Returns whether it was done.
function SpinLedger.addBought(player, count)
    local data = state[player]
    if not data or (count > 0 and not SpinLedger.canAddBought(player, count)) then
        return false
    end
    data.Bought = math.max(0, data.Bought + count)
    SpinLedger.publish(player)
    return true
end

-- The player's attributes: "SpinsLeft" (every spin they can take now) and "SpinsBought" (the bought ones among them).
function SpinLedger.publish(player)
    if state[player] then
        player:SetAttribute("SpinsLeft", SpinLedger.spinsLeft(player))
        player:SetAttribute("SpinsBought", state[player].Bought)
    end
end

-- A copy for saving (nil until the player is set up).
function SpinLedger.exportData(player)
    local data = state[player]
    if not data then
        return nil
    end
    return { Day = data.Day, Used = data.Used, Extra = data.Extra, Bought = data.Bought, Pending = data.Pending and table.clone(data.Pending) }
end

function SpinLedger.removePlayer(player)
    state[player] = nil
end

return SpinLedger
