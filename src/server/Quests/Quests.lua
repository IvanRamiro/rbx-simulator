-- Where each player is in the first quests (GameConfig.Quests): the step they're on, from
-- 1 to #Quests, and Quests.DONE (#Quests + 1) once all are done or skipped. Saved in PlayerData as
-- Quest; mirrored to the player's "QuestStep" attribute for their QUEST tracker. QuestService
-- moves it on.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local Quests = {}

Quests.DONE = #GameConfig.Quests + 1

-- a moment another service saw, for QuestService: Fire(player, kind, goal)
Quests.Moment = Instance.new("BindableEvent")

local steps = {} -- [player] = step

-- A saved step: a whole number from 1 to DONE; a new player (nil) starts at 1.
function Quests.sanitize(raw)
    if typeof(raw) == "number" and raw == raw and raw % 1 == 0 then
        return math.clamp(raw, 1, Quests.DONE)
    end
    return 1
end

-- `progress` is nil for a new player.
function Quests.setupPlayer(player, progress)
    Quests.set(player, Quests.sanitize(progress and progress.Quest))
end

function Quests.get(player)
    return steps[player]
end

function Quests.set(player, step)
    steps[player] = step
    player:SetAttribute("QuestStep", step)
end

function Quests.exportData(player)
    return steps[player]
end

function Quests.removePlayer(player)
    steps[player] = nil
end

return Quests
