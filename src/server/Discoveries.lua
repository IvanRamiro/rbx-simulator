local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local Discoveries = {}

local found = {}

local relicsById = {}
for _, relic in GameConfig.Relics do
    relicsById[relic.Id] = relic
end

function Discoveries.getRelic(relicId)
    return relicsById[relicId]
end

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

function Discoveries.markFound(player, relicId)
    local set = found[player]
    if not set or set[relicId] or not relicsById[relicId] then
        return false
    end

    set[relicId] = true
    return true
end

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
