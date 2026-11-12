-- Which of the Wandering Merchant's deals a player has bought this visit (shared/Merchant.lua), saved in PlayerData as
-- Merchant = { Visit = <the visit's number>, Bought = { <deal ids> } }, so leaving and rejoining (or another server) can't
-- sell them the same deal twice. A record of an earlier visit means nothing bought this one: it is cleared on first use.
local MerchantLedger = {}

local MAX_BOUGHT = 16 -- more than a visit ever offers (GameConfig.WanderingMerchant.Deals.Max)
local MAX_ID_LENGTH = 64

local state = {} -- [player] = { visit = number, bought = { [dealId] = true } }

function MerchantLedger.sanitize(raw)
    raw = if typeof(raw) == "table" then raw else {}
    local visit = if typeof(raw.Visit) == "number" and raw.Visit == raw.Visit then math.max(0, math.floor(raw.Visit)) else 0
    local bought = {}
    if typeof(raw.Bought) == "table" then
        for _, id in raw.Bought do
            if #bought >= MAX_BOUGHT then
                break
            end
            if typeof(id) == "string" and #id > 0 and #id <= MAX_ID_LENGTH and not table.find(bought, id) then
                table.insert(bought, id)
            end
        end
    end
    return { Visit = visit, Bought = bought }
end

function MerchantLedger.setupPlayer(player, progress)
    local saved = MerchantLedger.sanitize(progress and progress.Merchant)
    local data = { visit = saved.Visit, bought = {} }
    for _, id in saved.Bought do
        data.bought[id] = true
    end
    state[player] = data
end

function MerchantLedger.isSetUp(player)
    return state[player] ~= nil
end

local function forVisit(player, visit)
    local data = state[player]
    if data and data.visit ~= visit then
        data.visit = visit
        data.bought = {}
    end
    return data
end

function MerchantLedger.hasBought(player, visit, dealId)
    local data = forVisit(player, visit)
    return data ~= nil and data.bought[dealId] == true
end

-- False when the player isn't set up.
function MerchantLedger.markBought(player, visit, dealId)
    local data = forVisit(player, visit)
    if not data then
        return false
    end
    data.bought[dealId] = true
    return true
end

-- For saving (nil until the player is set up).
function MerchantLedger.exportData(player)
    local data = state[player]
    if not data then
        return nil
    end
    local bought = {}
    for id in data.bought do
        table.insert(bought, id)
    end
    table.sort(bought)
    return { Visit = data.visit, Bought = bought }
end

function MerchantLedger.removePlayer(player)
    state[player] = nil
end

return MerchantLedger
