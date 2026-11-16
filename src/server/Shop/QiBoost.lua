-- A player's timed Qi boost (GameConfig.TimedBoost, the owner 2026-11-16: "a consumable multiplier like 2x qi multiplier per 5 mins"),
-- saved in PlayerData as Boost = { Seconds = <seconds left> } (save schema 22). Its clock runs only while the player is in the game:
-- on joining it ends Seconds from now, and leaving saves what is left. Bought minutes (ProductService) and the daily reward's
-- (RewardService) add to it, up to MaxMinutes. The player's "QiBoostEnds" attribute (a server time, workspace:GetServerTimeNow) is
-- what PassRules reads, on the server and the client alike: the boost counts while that time is ahead.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local QiBoost = {}

local MAX_SECONDS = GameConfig.TimedBoost.MaxMinutes * 60

local state = {} -- [player] = { ends = <server time it ends, 0 for none> }

local function now()
    return workspace:GetServerTimeNow()
end

function QiBoost.sanitize(raw)
    local seconds = typeof(raw) == "table" and raw.Seconds
    if typeof(seconds) ~= "number" or seconds ~= seconds or seconds <= 0 then
        seconds = 0
    end
    return { Seconds = math.min(math.floor(seconds), MAX_SECONDS) }
end

function QiBoost.publish(player)
    local data = state[player]
    if data then
        player:SetAttribute("QiBoostEnds", if data.ends > now() then data.ends else nil)
    end
end

function QiBoost.setupPlayer(player, progress)
    local seconds = QiBoost.sanitize(progress and progress.Boost).Seconds
    state[player] = { ends = if seconds > 0 then now() + seconds else 0 }
    QiBoost.publish(player)
end

function QiBoost.isSetUp(player)
    return state[player] ~= nil
end

function QiBoost.secondsLeft(player)
    local data = state[player]
    return if data then math.max(0, data.ends - now()) else 0
end

-- Whether `minutes` more fit under MaxMinutes.
function QiBoost.canAdd(player, minutes)
    return state[player] ~= nil and QiBoost.secondsLeft(player) + minutes * 60 <= MAX_SECONDS
end

-- Adds minutes of boost (a negative number takes them back, never below none). Returns whether it was done.
function QiBoost.add(player, minutes)
    local data = state[player]
    if not data or typeof(minutes) ~= "number" or minutes ~= minutes or (minutes > 0 and not QiBoost.canAdd(player, minutes)) then
        return false
    end
    local left = math.max(0, QiBoost.secondsLeft(player) + minutes * 60)
    data.ends = if left > 0 then now() + left else 0
    QiBoost.publish(player)
    return true
end

-- A copy for saving: the seconds left (nil until the player is set up).
function QiBoost.exportData(player)
    if not state[player] then
        return nil
    end
    return { Seconds = math.floor(QiBoost.secondsLeft(player)) }
end

function QiBoost.removePlayer(player)
    state[player] = nil
end

return QiBoost
