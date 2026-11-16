-- Each player's Auction House journal, saved in PlayerData as Auction (save schema 23; vault: Auction House Design 2026-11-16):
--   Out     = { [listingId] = { Kind, Item, StartBid, Hours, Fee, Paid, Rarity, Value, Cap, Show, SellerName, At } }
--             an item (and its fee) out of the inventory whose listing may not exist yet
--   Bids    = { [bidId] = { L = listingId, Amount, At } }   stones out of the wallet whose bid may not be on its listing yet
--   Claimed = { [mailId] = time }                            mail given whose mailbox may not have crossed it off yet
--   Mine    = { listingId, ... }                             the player's listings (until seen closed)
--   Watch   = { listingId, ... }                             listings they bid on (until seen closed)
-- AuctionCore keeps it: an Out or Bids entry holds a real item or real stones, so sanitize never drops a readable one (the caps are
-- far above what the Auction House lets a player have in flight).
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))

local AuctionLedger = {}

local MAX_ID = 64
local MAX_OUT, MAX_BIDS, MAX_CLAIMED, MAX_POINTERS = 40, 60, 400, 40

local state = {} -- [player] = the live ledger

local function isId(id, length)
    return typeof(id) == "string" and #id > 0 and #id <= (length or MAX_ID)
end

local function wholeOr(n, default)
    return if typeof(n) == "number" and n == n and n >= 0 and n <= GameConfig.SpiritStones.Max then math.floor(n) else default
end

local function shortText(text)
    return if typeof(text) == "string" and #text <= 120 then text else nil
end

-- an item record as it left the inventory: a pet { InstanceId, PetId, Level, Size, Worth, Locked, Paid } or a weapon
-- { InstanceId, WeaponId, Element, Name }; nil if it isn't one
function AuctionLedger.sanitizeItem(kind, item)
    if typeof(item) ~= "table" or not isId(item.InstanceId) then
        return nil
    end
    if kind == "Pet" and typeof(item.PetId) == "string" and GameConfig.Pets[item.PetId] then
        return {
            InstanceId = item.InstanceId, PetId = item.PetId, Level = tonumber(item.Level) or 1,
            Size = if typeof(item.Size) == "string" then item.Size else "Normal", Worth = tonumber(item.Worth), Locked = false,
            Paid = if item.Paid == true then true else nil,
        }
    elseif kind == "Weapon" and Shop.weapon(item.WeaponId) then
        return {
            InstanceId = item.InstanceId, WeaponId = item.WeaponId,
            Element = if Shop.element(item.Element) then item.Element else nil, Name = shortText(item.Name),
        }
    end
    return nil
end

local function pointers(raw)
    local list = {}
    if typeof(raw) == "table" then
        for _, id in raw do
            if isId(id) and not table.find(list, id) then
                table.insert(list, id)
            end
        end
    end
    while #list > MAX_POINTERS do
        table.remove(list, 1)
    end
    return list
end

function AuctionLedger.sanitize(raw)
    raw = if typeof(raw) == "table" then raw else {}
    local out, bids, claimed = {}, {}, {}
    local n = 0
    for id, entry in if typeof(raw.Out) == "table" then raw.Out else {} do
        local item = isId(id) and typeof(entry) == "table" and AuctionLedger.sanitizeItem(entry.Kind, entry.Item)
        if item and n < MAX_OUT then
            n += 1
            out[id] = {
                Kind = entry.Kind, Item = item, StartBid = wholeOr(entry.StartBid, 1), Hours = wholeOr(entry.Hours, 1),
                Fee = wholeOr(entry.Fee, 0), Paid = entry.Paid == true, Rarity = shortText(entry.Rarity),
                Value = wholeOr(entry.Value, 0), Cap = wholeOr(entry.Cap, 1),
                Show = if typeof(entry.Show) == "table" then { Name = shortText(entry.Show.Name) } else nil,
                SellerName = shortText(entry.SellerName), At = wholeOr(entry.At, 0),
            }
        end
    end
    n = 0
    for id, entry in if typeof(raw.Bids) == "table" then raw.Bids else {} do
        local amount = typeof(entry) == "table" and wholeOr(entry.Amount, nil)
        if isId(id) and amount and amount >= 1 and isId(entry.L) and n < MAX_BIDS then
            n += 1
            bids[id] = { L = entry.L, Amount = amount, At = wholeOr(entry.At, 0) }
        end
    end
    n = 0
    for id, at in if typeof(raw.Claimed) == "table" then raw.Claimed else {} do
        if isId(id, 80) and n < MAX_CLAIMED then
            n += 1
            claimed[id] = wholeOr(at, 0)
        end
    end
    return { Out = out, Bids = bids, Claimed = claimed, Mine = pointers(raw.Mine), Watch = pointers(raw.Watch) }
end

-- Every pet or weapon id in a raw journal (PlayerData refuses a save holding one this server doesn't know: newer content).
function AuctionLedger.itemIds(raw)
    local pets, weapons = {}, {}
    if typeof(raw) == "table" and typeof(raw.Out) == "table" then
        for _, entry in raw.Out do
            local item = typeof(entry) == "table" and entry.Item
            if typeof(item) == "table" then
                if typeof(item.PetId) == "string" then
                    table.insert(pets, item.PetId)
                end
                if typeof(item.WeaponId) == "string" then
                    table.insert(weapons, item.WeaponId)
                end
            end
        end
    end
    return pets, weapons
end

function AuctionLedger.setupPlayer(player, progress)
    state[player] = AuctionLedger.sanitize(progress and progress.Auction)
end

function AuctionLedger.get(player)
    return state[player]
end

function AuctionLedger.isSetUp(player)
    return state[player] ~= nil
end

local function copy(value)
    if typeof(value) ~= "table" then
        return value
    end
    local result = {}
    for k, v in value do
        result[k] = copy(v)
    end
    return result
end

-- For saving (nil until the player is set up).
function AuctionLedger.exportData(player)
    return if state[player] then copy(state[player]) else nil
end

function AuctionLedger.removePlayer(player)
    state[player] = nil
end

return AuctionLedger
