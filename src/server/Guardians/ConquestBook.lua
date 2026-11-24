-- A player's guardian conquests (GameConfig.Bounty, shared/BountyRules), saved in PlayerData as Conquests:
--   { Counts = { [guardianId] = n }, Paid = { [guardianId] = tiers paid }, Day, DayPaid = bool }
-- ConquestService counts a conquest and pays what it earns; this only holds the state.
--
--   ConquestBook.setupPlayer(player, progress)   the saved state, cleaned (the day's flag rolled)
--   ConquestBook.get(player)                     the live tables, or nil before setup (the day's flag rolled first)
--   ConquestBook.exportData(player)              a clean copy to save, or nil
--   ConquestBook.Changed                         a BindableEvent fired with the player when their board moved
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local BountyRules = require(ReplicatedStorage:WaitForChild("BountyRules"))
local GoalRules = require(ReplicatedStorage:WaitForChild("GoalRules"))

local ConquestBook = {}

ConquestBook.Changed = Instance.new("BindableEvent")
ConquestBook.sanitize = BountyRules.sanitize

local state = {} -- [player] = the saved tables

function ConquestBook.setupPlayer(player, progress)
    local data = BountyRules.sanitize(progress and progress.Conquests)
    BountyRules.roll(data, GoalRules.dayKey())
    state[player] = data
end

function ConquestBook.get(player)
    local data = state[player]
    if data then
        BountyRules.roll(data, GoalRules.dayKey())
    end
    return data
end

function ConquestBook.exportData(player)
    local data = ConquestBook.get(player)
    return if data then BountyRules.sanitize(data) else nil
end

function ConquestBook.removePlayer(player)
    state[player] = nil
end

return ConquestBook
