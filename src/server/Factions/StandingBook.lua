-- A player's faction standing (GameConfig.Renown, shared/StandingRules), saved in PlayerData as Standing:
--   { Renown, Paid, CacheDay, Week, WeekRenown, LastWeek, LastRenown, WarClaimed }
-- StandingService earns and pays; this only holds the state.
--   StandingBook.setupPlayer(player, progress)   the saved state, cleaned (the week rolled)
--   StandingBook.get(player)                     the live table (the week rolled first), or nil before setup
--   StandingBook.exportData(player)              a clean copy to save, or nil
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GoalRules = require(ReplicatedStorage:WaitForChild("GoalRules"))
local StandingRules = require(ReplicatedStorage:WaitForChild("StandingRules"))

local StandingBook = {}

StandingBook.sanitize = StandingRules.sanitize

local state = {} -- [player] = the saved table

function StandingBook.setupPlayer(player, progress)
    local data = StandingRules.sanitize(progress and progress.Standing)
    StandingRules.roll(data, GoalRules.weekKey())
    state[player] = data
end

function StandingBook.get(player)
    local data = state[player]
    if data then
        StandingRules.roll(data, GoalRules.weekKey())
    end
    return data
end

function StandingBook.exportData(player)
    local data = StandingBook.get(player)
    return if data then StandingRules.sanitize(data) else nil
end

function StandingBook.removePlayer(player)
    state[player] = nil
end

return StandingBook
