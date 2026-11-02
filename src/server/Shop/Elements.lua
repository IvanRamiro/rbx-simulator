-- The forge's elements a player has unlocked (GameConfig.Forge): those of the relics they have
-- attuned (Discoveries; GameConfig.Relics.<n>.Element) and those dropped by the guardians whose eggs
-- they secured (GameConfig.Guardians.<Id>.Element), which are saved in PlayerData as ForgeElements.
-- An element, once unlocked, stays unlocked.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Discoveries = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("Discoveries"))

local Elements = {}

local dropped = {} -- [player] = { [element] = true }, from guardians

-- Cleans saved guardian elements: known elements, each once.
function Elements.sanitize(raw)
    local clean = {}
    if typeof(raw) == "table" then
        for _, element in raw do
            if typeof(element) == "string" and GameConfig.Forge.Elements[element] and not table.find(clean, element) then
                table.insert(clean, element)
            end
        end
    end
    return clean
end

function Elements.setupPlayer(player, progress)
    local set = {}
    for _, element in Elements.sanitize(progress and progress.ForgeElements) do
        set[element] = true
    end
    dropped[player] = set
end

-- The player's unlocked elements, as a set.
local function unlockedSet(player)
    local set = table.clone(dropped[player] or {})
    for _, relicId in Discoveries.exportData(player) or {} do
        local relic = Discoveries.getRelic(relicId)
        if relic and relic.Element then
            set[relic.Element] = true
        end
    end
    return set
end

function Elements.has(player, element)
    return unlockedSet(player)[element] == true
end

-- The unlocked elements in GameConfig.Forge.Order (for the client's forge).
function Elements.list(player)
    local set = unlockedSet(player)
    local list = {}
    for _, element in GameConfig.Forge.Order do
        if set[element] then
            table.insert(list, element)
        end
    end
    return list
end

-- A guardian's drop: unlocks its element; true when the player didn't have it yet.
function Elements.unlock(player, element)
    local set = dropped[player]
    if not set or not GameConfig.Forge.Elements[element] then
        return false
    end
    local new = not Elements.has(player, element)
    set[element] = true
    return new
end

-- For saving (nil until the player is set up): the guardian elements only, relics being saved as finds.
function Elements.exportData(player)
    local set = dropped[player]
    if not set then
        return nil
    end
    local list = {}
    for _, element in GameConfig.Forge.Order do
        if set[element] then
            table.insert(list, element)
        end
    end
    return list
end

function Elements.removePlayer(player)
    dropped[player] = nil
end

for _, element in GameConfig.Forge.Order do
    assert(GameConfig.Forge.Elements[element], "GameConfig.Forge.Order names an unknown element " .. element)
end
for _, relic in GameConfig.Relics do
    assert(relic.Element == nil or GameConfig.Forge.Elements[relic.Element], "Relic " .. relic.Id .. " has an unknown Element")
end

return Elements
