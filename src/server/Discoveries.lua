-- Server-only record of which Spirit Relics each player has found.
-- PlayerData loads it from and saves it to the DataStore; DiscoveryService
-- adds to it when a player attunes to a relic.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local Discoveries = {}

-- found[player] = { [relicId] = true, ... }
local found = {}

local relicsById = {}
for _, relic in GameConfig.Relics do
    relicsById[relic.Id] = relic
end

-- The relic's definition from GameConfig.Relics, or nil for an unknown Id
function Discoveries.getRelic(relicId)
    return relicsById[relicId]
end

-- Call once after a player's data has loaded, with their saved relic Ids
-- (already validated by PlayerData). Safe to call again.
function Discoveries.setupPlayer(player, savedRelicIds)
    if found[player] then
        return
    end

    local set = {}
    for _, relicId in savedRelicIds or {} do
        set[relicId] = true
    end
    found[player] = set
end

function Discoveries.removePlayer(player)
    found[player] = nil
end

function Discoveries.isSetUp(player)
    return found[player] ~= nil
end

function Discoveries.hasFound(player, relicId)
    local set = found[player]
    return set ~= nil and set[relicId] == true
end

-- Records a find. Returns true only if it's new. Only call this with a relic
-- Id from the server's own relic (never one sent by a client).
function Discoveries.markFound(player, relicId)
    local set = found[player]
    if not set or set[relicId] or not relicsById[relicId] then
        return false
    end

    set[relicId] = true
    return true
end

-- The player's found relic Ids in GameConfig order, or nil if they aren't set up
function Discoveries.exportData(player)
    local set = found[player]
    if not set then
        return nil
    end

    local relicIds = {}
    for _, relic in GameConfig.Relics do
        if set[relic.Id] then
            table.insert(relicIds, relic.Id)
        end
    end
    return relicIds
end

return Discoveries
