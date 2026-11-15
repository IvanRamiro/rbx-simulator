-- A player's Spin Wheel day (SpinService), saved in PlayerData as
--   Spin = { Day = <the UTC day>, Used = <spins taken that day>, Extra = <spins won that day>, Pending = <a spin still turning> }
-- A record of an earlier day means today's spins are all left (its extras are gone with it). Pending is the reward a spin
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
    return pending
end

function SpinLedger.sanitize(raw)
    raw = if typeof(raw) == "table" then raw else {}
    return {
        Day = whole(raw.Day, 1e7),
        Used = whole(raw.Used, MAX_USED),
        Extra = whole(raw.Extra, config.MaxExtra),
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

-- A copy for saving (nil until the player is set up).
function SpinLedger.exportData(player)
    local data = state[player]
    if not data then
        return nil
    end
    return { Day = data.Day, Used = data.Used, Extra = data.Extra, Pending = data.Pending and table.clone(data.Pending) }
end

function SpinLedger.removePlayer(player)
    state[player] = nil
end

return SpinLedger
