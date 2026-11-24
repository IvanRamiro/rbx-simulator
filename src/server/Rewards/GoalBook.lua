-- A player's daily and weekly goal progress (GameConfig.Goals, shared/GoalRules), saved in PlayerData as Goals:
--   { Day, DayProgress = { [goalId] = n }, DayClaimed = { [goalId] = true }, DayBonus = bool, Week, WeekProgress, WeekClaimed, WeekBonus }
-- A period's tables belong to its number (Day, Week): when the number moves on they start empty. Other services only call GoalBook.count (a thing the server
-- saw: a minute cultivated, a strike on a guardian, an egg carried home, a hatch, a spin, a combo); GoalService pays the claims and tells the player.
--
--   GoalBook.count(player, kind, amount)   `amount` more of this kind (a combo's count is the best so far: the goal's own Mode decides)
--   GoalBook.Changed                       a BindableEvent fired with the player when their progress moved
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GoalRules = require(ReplicatedStorage:WaitForChild("GoalRules"))

local GoalBook = {}

GoalBook.Changed = Instance.new("BindableEvent")

local state = {} -- [player] = the saved tables

GoalBook.sanitize = GoalRules.sanitize -- (shared, so the plain-Luau specs can test it)
GoalBook.roll = GoalRules.roll

function GoalBook.setupPlayer(player, progress)
    local data = GoalBook.sanitize(progress and progress.Goals)
    GoalBook.roll(data)
    state[player] = data
end

function GoalBook.get(player)
    local data = state[player]
    if data then
        GoalBook.roll(data)
    end
    return data
end

-- the table of a scope's progress, claims and bonus flag in `data`
function GoalBook.scopeOf(data, scope)
    if scope == "Weekly" then
        return data.WeekProgress, data.WeekClaimed, "WeekBonus"
    end
    return data.DayProgress, data.DayClaimed, "DayBonus"
end

function GoalBook.count(player, kind, amount)
    local data = GoalBook.get(player)
    if not data or typeof(kind) ~= "string" then
        return
    end
    local moved = false
    for _, scope in { "Daily", "Weekly" } do
        local progress = GoalBook.scopeOf(data, scope)
        local key = if scope == "Weekly" then data.Week else data.Day
        for _, goal in GoalRules.pick(scope, player.UserId, key) do
            if goal.Kind == kind then
                local before = progress[goal.Id] or 0
                local after = GoalRules.advance(before, goal, amount)
                if after ~= before then
                    progress[goal.Id] = after
                    moved = true
                end
            end
        end
    end
    if moved then
        GoalBook.Changed:Fire(player)
    end
end

function GoalBook.exportData(player)
    local data = GoalBook.get(player)
    if not data then
        return nil
    end
    return GoalBook.sanitize(data)
end

function GoalBook.removePlayer(player)
    state[player] = nil
end

return GoalBook
