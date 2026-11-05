-- What this player's Codex holds, kept here so every window reads the same copy (the server sends it as CodexEvent "State").
--   CodexState.found      [petId] = true for every beast ever owned
--   CodexState.claimed    [rewardId] = true
--   CodexState.owned      [petId] = { Count, Level } for what they hold now
--   CodexState.loaded     false until the first arrives
--   CodexState.Changed    fires with a list of the beasts just discovered
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))

local changed = Instance.new("BindableEvent")

local CodexState = { found = {}, claimed = {}, owned = {}, loaded = false, Changed = changed.Event }

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
    CodexState.loaded = true
    changed:Fire(discovered)
end)

return CodexState
