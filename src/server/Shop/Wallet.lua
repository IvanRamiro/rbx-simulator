-- A player's Spirit Stones (GameConfig.SpiritStones). Saved in PlayerData as SpiritStones and
-- mirrored to the client as the player attribute "SpiritStones".
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Analytics = require(script.Parent.Parent:WaitForChild("Analytics"):WaitForChild("Analytics"))

local Wallet = {}

local stones = {}

local function mirror(player)
    player:SetAttribute("SpiritStones", stones[player])
end

-- A whole number from 0 to SpiritStones.Max.
function Wallet.sanitize(raw)
    if typeof(raw) == "number" and raw == raw then
        return math.clamp(math.floor(raw), 0, GameConfig.SpiritStones.Max)
    end
    return 0
end

function Wallet.setupPlayer(player, progress)
    stones[player] = Wallet.sanitize(progress and progress.SpiritStones)
    mirror(player)
end

function Wallet.balance(player)
    return stones[player] or 0
end

-- Adds stones; false when the player isn't set up. `kind` and `sku` say what paid them (analytics).
function Wallet.add(player, amount, kind, sku)
    if stones[player] == nil or typeof(amount) ~= "number" or amount ~= amount or amount < 0 then
        return false
    end
    stones[player] = math.min(stones[player] + math.floor(amount), GameConfig.SpiritStones.Max)
    mirror(player)
    Analytics.stones(player, "Source", math.floor(amount), stones[player], kind, sku)
    return true
end

-- Spends stones; false (and nothing spent) when the player hasn't enough.
function Wallet.spend(player, amount, kind, sku)
    if stones[player] == nil or typeof(amount) ~= "number" or amount ~= amount or amount < 0 or stones[player] < amount then
        return false
    end
    stones[player] -= amount
    mirror(player)
    Analytics.stones(player, "Sink", amount, stones[player], kind, sku)
    return true
end

-- For saving (nil until the player is set up).
function Wallet.exportData(player)
    return stones[player]
end

function Wallet.removePlayer(player)
    stones[player] = nil
end

return Wallet
