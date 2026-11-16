-- A player's own records for the Hall of Records (shared/RecordsConfig), saved in PlayerData as Records = { PlayTime = <seconds
-- in the game>, EggsSecured = <eggs carried home> } (save schema 25). Play time runs while the player is in the game (from their
-- data loading to leaving); an egg counts when Guardian.lua secures it. The player's "RecordPlayMinutes" and "RecordEggsSecured"
-- attributes show them on the boards' "You" lines. RecordsService puts them on the ladders.
-- Also the hall's hatch hook: PetService calls RecordBook.hatched, and RecordsService listens to RecordBook.Hatched.
local RecordBook = {}

local MAX_SECONDS = 50 * 365 * 86400
local MAX_EGGS = 10000000

RecordBook.Hatched = Instance.new("BindableEvent") -- (player, eggId, petId, size)

local state = {} -- [player] = { seconds = saved play time, since = os.clock() at join, eggs = eggs secured }

local function count(value, most)
    if typeof(value) ~= "number" or value ~= value or value <= 0 then
        return 0
    end
    return math.min(math.floor(value), most)
end

function RecordBook.sanitize(raw)
    raw = if typeof(raw) == "table" then raw else {}
    return { PlayTime = count(raw.PlayTime, MAX_SECONDS), EggsSecured = count(raw.EggsSecured, MAX_EGGS) }
end

local function playSeconds(data)
    return math.min(data.seconds + (os.clock() - data.since), MAX_SECONDS)
end

function RecordBook.publish(player)
    local data = state[player]
    if data then
        player:SetAttribute("RecordPlayMinutes", math.floor(playSeconds(data) / 60))
        player:SetAttribute("RecordEggsSecured", data.eggs)
    end
end

function RecordBook.setupPlayer(player, progress)
    local saved = RecordBook.sanitize(progress and progress.Records)
    state[player] = { seconds = saved.PlayTime, since = os.clock(), eggs = saved.EggsSecured }
    RecordBook.publish(player)
end

function RecordBook.isSetUp(player)
    return state[player] ~= nil
end

function RecordBook.removePlayer(player)
    state[player] = nil
end

-- whole minutes in the game so far, or nil before set-up
function RecordBook.playMinutes(player)
    local data = state[player]
    return data and math.floor(playSeconds(data) / 60)
end

function RecordBook.eggsSecured(player)
    local data = state[player]
    return data and data.eggs
end

function RecordBook.addEggSecured(player)
    local data = state[player]
    if not data then
        return false
    end
    data.eggs = math.min(data.eggs + 1, MAX_EGGS)
    RecordBook.publish(player)
    return true
end

function RecordBook.exportData(player)
    local data = state[player]
    if not data then
        return nil
    end
    return { PlayTime = math.floor(playSeconds(data)), EggsSecured = data.eggs }
end

-- a hatch at the Hatching Altar (PetService), for the Rarest Beasts, the Firsts and the Chronicle
function RecordBook.hatched(player, eggId, petId, size)
    RecordBook.Hatched:Fire(player, eggId, petId, size)
end

return RecordBook
