-- A player's Spirit Beast Codex, saved in PlayerData as Codex: every beast they have ever owned (Found) and the
-- rewards they have taken (Claimed). An entry is never lost: selling or fusing the pet leaves it in the book.
-- CodexRules holds what counts and what it pays; PetService pays it.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CodexRules = require(ReplicatedStorage:WaitForChild("CodexRules"))
local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))

local Codex = {}

local state = {} -- [player] = { found = { [petId] = true }, claimed = { [rewardId] = true } }

function Codex.sanitize(raw)
    raw = if typeof(raw) == "table" then raw else {}
    local found, claimed = {}, {}
    if typeof(raw.Found) == "table" then
        for _, petId in raw.Found do
            if typeof(petId) == "string" and GameConfig.Pets[petId] and not table.find(found, petId) then
                table.insert(found, petId)
            end
        end
    end
    if typeof(raw.Claimed) == "table" then
        for _, id in raw.Claimed do
            if CodexRules.reward(id) and not table.find(claimed, id) then
                table.insert(claimed, id)
            end
        end
    end
    return { Found = found, Claimed = claimed }
end

function Codex.setupPlayer(player, progress)
    local saved = Codex.sanitize(progress and progress.Codex)
    local data = { found = {}, claimed = {} }
    for _, petId in saved.Found do
        data.found[petId] = true
    end
    for _, id in saved.Claimed do
        data.claimed[id] = true
    end
    state[player] = data
end

function Codex.removePlayer(player)
    state[player] = nil
end

function Codex.isFound(player, petId)
    local data = state[player]
    return data ~= nil and data.found[petId] == true
end

-- True when this is a new entry.
function Codex.discover(player, petId)
    local data = state[player]
    if not data or not GameConfig.Pets[petId] or data.found[petId] then
        return false
    end
    data.found[petId] = true
    return true
end

function Codex.qiPercent(player)
    local data = state[player]
    return if data then CodexRules.qiPercent(data.claimed) else 0
end

-- Marks a reward taken and returns it; nil if it isn't earned, or was taken already.
function Codex.claim(player, rewardId)
    local data = state[player]
    local reward = CodexRules.reward(rewardId)
    if not (data and reward) or data.claimed[reward.Id] or not CodexRules.isEarned(reward, data.found) then
        return nil
    end
    data.claimed[reward.Id] = true
    return reward
end

local function sorted(set)
    local list = {}
    for key in set do
        table.insert(list, key)
    end
    table.sort(list)
    return list
end

function Codex.exportData(player)
    local data = state[player]
    if not data then
        return nil
    end
    return { Found = sorted(data.found), Claimed = sorted(data.claimed) }
end

-- owned: { [petId] = { Count, Level } }, what they hold now, for the book's pages
function Codex.publish(player, owned)
    local data = Codex.exportData(player)
    if data then
        data.Owned = owned
        RemoteEvents.CodexEvent:FireClient(player, "State", data)
    end
end

return Codex
