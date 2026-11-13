-- The Robux purchases (developer products) a player has been given, saved in PlayerData as Receipts = { <PurchaseId>, ... },
-- newest last, so a purchase Roblox offers again (ProcessReceipt retries until it hears PurchaseGranted, in this server or another)
-- is never given twice. Only the newest MAX_KEPT are kept: Roblox stops offering a purchase once it has been granted.
local Receipts = {}

local MAX_KEPT = 50
local MAX_ID_LENGTH = 100

local state = {} -- [player] = { <PurchaseId>, ... }

function Receipts.sanitize(raw)
    local kept = {}
    if typeof(raw) == "table" then
        for _, id in raw do
            if typeof(id) == "string" and #id > 0 and #id <= MAX_ID_LENGTH and not table.find(kept, id) then
                table.insert(kept, id)
            end
        end
    end
    while #kept > MAX_KEPT do
        table.remove(kept, 1)
    end
    return kept
end

function Receipts.setupPlayer(player, progress)
    state[player] = Receipts.sanitize(progress and progress.Receipts)
end

function Receipts.isSetUp(player)
    return state[player] ~= nil
end

function Receipts.has(player, purchaseId)
    return state[player] ~= nil and table.find(state[player], purchaseId) ~= nil
end

function Receipts.add(player, purchaseId)
    local kept = state[player]
    if not kept or table.find(kept, purchaseId) then
        return
    end
    table.insert(kept, purchaseId)
    while #kept > MAX_KEPT do
        table.remove(kept, 1)
    end
end

-- Takes a purchase back out (its grant couldn't be saved: Roblox will offer it again).
function Receipts.remove(player, purchaseId)
    local kept = state[player]
    local index = kept and table.find(kept, purchaseId)
    if index then
        table.remove(kept, index)
    end
end

function Receipts.exportData(player)
    return if state[player] then table.clone(state[player]) else nil
end

function Receipts.removePlayer(player)
    state[player] = nil
end

return Receipts
