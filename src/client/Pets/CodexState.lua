-- What this player's Codex holds, kept here so every window reads the same copy (the server sends it as CodexEvent "State").
--   CodexState.found      [petId] = true for every beast ever owned
--   CodexState.claimed    [rewardId] = true
--   CodexState.earned     [rewardId] = the realm an earned, unclaimed reward pays at
--   CodexState.owned      [petId] = { Count, Level } for what they hold now
--   CodexState.mutations  [petId] = { [mutationId] = true } for the mutations found on each beast (PetRules.Mutations)
--   CodexState.loaded     false until the first arrives
--   CodexState.Changed    fires with a list of the beasts just discovered
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))

local changed = Instance.new("BindableEvent")

local CodexState = { found = {}, claimed = {}, earned = {}, owned = {}, mutations = {}, loaded = false, Changed = changed.Event }

RemoteEvents.CodexEvent.OnClientEvent:Connect(function(action, data)
    if action ~= "State" or typeof(data) ~= "table" then
        return
    end
    local found, discovered = {}, {}
    for _, petId in data.Found do
        found[petId] = true
        if CodexState.loaded and not CodexState.found[petId] then
            table.insert(discovered, petId)
        end
    end
    local claimed = {}
    for _, id in data.Claimed do
        claimed[id] = true
    end
    CodexState.found, CodexState.claimed, CodexState.owned = found, claimed, data.Owned or {}
    CodexState.earned = if typeof(data.Earned) == "table" then data.Earned else {}
    local mutations = {}
    for petId, list in if typeof(data.Mutations) == "table" then data.Mutations else {} do
        mutations[petId] = {}
        for _, id in list do
            mutations[petId][id] = true
        end
    end
    CodexState.mutations = mutations
    CodexState.loaded = true
    changed:Fire(discovered)
end)

return CodexState
