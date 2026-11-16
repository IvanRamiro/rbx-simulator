-- The eggs a player has taken from guardians and secured, to hatch at Yggdrasil's Hatching Altar
-- (PetService). Saved in PlayerData as Eggs = { [EggId] = count } and mirrored to the client as
-- player attributes "Egg_<EggId>".
--
-- Paid eggs (save schema 24, PaidEggs = { [EggId] = count }, never more than Eggs holds of it): how many of those eggs came from
-- Robux (the Exclusive Egg bought in the Shop; an egg won with a spin bought with Robux). Roblox's policy lets some players trade
-- only items that didn't come from Robux (vault: Auction House Design 2026-11-16), so a pet hatched from a paid egg is marked
-- paid (PetInventory: Paid). Eggs of one kind are all alike, so a hatch takes a PAID one first while any is held: every paid
-- egg becomes a paid pet at the earliest hatch, never parked behind free ones, and a free egg is never the one counted paid
-- by mistake (the count can only go down by a hatch or the exact undo of a grant: EggInventory.revoke).
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local EggInventory = {}

EggInventory.MAX_PER_EGG = 99

local held = {}
local paidHeld = {} -- [player] = { [EggId] = how many of held's eggs of it are paid }

local function mirror(player, eggId)
    local count = held[player] and held[player][eggId] or 0
    player:SetAttribute("Egg_" .. eggId, if count > 0 then count else nil)
end

-- Cleans saved paid counts: whole numbers from 1 up to what `eggs` (already sanitized) holds of that egg.
function EggInventory.sanitizePaid(raw, eggs)
    local paid = {}
    if typeof(raw) == "table" then
        for eggId, count in raw do
            local held = typeof(eggId) == "string" and eggs[eggId]
            if held and typeof(count) == "number" and count == count then
                count = math.clamp(math.floor(count), 0, held)
                if count > 0 then
                    paid[eggId] = count
                end
            end
        end
    end
    return paid
end

-- Cleans saved egg counts: known eggs only, whole numbers from 1 to MAX_PER_EGG.
function EggInventory.sanitize(raw)
    local eggs = {}
    if typeof(raw) == "table" then
        for eggId, count in raw do
            if typeof(eggId) == "string" and GameConfig.Eggs[eggId] and typeof(count) == "number" and count == count then
                count = math.clamp(math.floor(count), 0, EggInventory.MAX_PER_EGG)
                if count > 0 then
                    eggs[eggId] = count
                end
            end
        end
    end
    return eggs
end

function EggInventory.setupPlayer(player, progress)
    held[player] = EggInventory.sanitize(progress and progress.Eggs)
    if not progress and GameConfig.GrantDevTestPets and RunService:IsStudio() then -- a new save in Studio: eggs to test hatching
        for eggId, count in GameConfig.DevTestEggs or {} do
            if GameConfig.Eggs[eggId] then
                held[player][eggId] = math.min(count, EggInventory.MAX_PER_EGG)
            end
        end
    end
    paidHeld[player] = EggInventory.sanitizePaid(progress and progress.PaidEggs, held[player])
    for eggId in held[player] do
        mirror(player, eggId)
    end
end

-- How many of the player's eggs of this kind came from Robux.
function EggInventory.paidCount(player, eggId)
    return paidHeld[player] and paidHeld[player][eggId] or 0
end

function EggInventory.count(player, eggId)
    return held[player] and held[player][eggId] or 0
end

-- Adds one egg (`paid`: it came from Robux); false when the player isn't set up or already holds the most of it.
function EggInventory.grant(player, eggId, paid)
    local eggs = held[player]
    if not (eggs and GameConfig.Eggs[eggId]) or (eggs[eggId] or 0) >= EggInventory.MAX_PER_EGG then
        return false
    end
    eggs[eggId] = (eggs[eggId] or 0) + 1
    if paid == true then
        local paidEggs = paidHeld[player]
        paidEggs[eggId] = (paidEggs[eggId] or 0) + 1
    end
    mirror(player, eggId)
    return true
end

local function dropOne(player, eggId)
    local eggs = held[player]
    eggs[eggId] -= 1
    if eggs[eggId] == 0 then
        eggs[eggId] = nil
    end
    local paidEggs = paidHeld[player]
    if (paidEggs[eggId] or 0) > (eggs[eggId] or 0) then -- (never more paid than held)
        paidEggs[eggId] = if (eggs[eggId] or 0) > 0 then eggs[eggId] else nil
    end
    mirror(player, eggId)
end

-- Spends one egg to hatch it: a paid one first while any is held. Returns true and whether it was paid; false when none is held.
function EggInventory.take(player, eggId)
    local eggs = held[player]
    if not (eggs and (eggs[eggId] or 0) > 0) then
        return false, false
    end
    local paidEggs = paidHeld[player]
    local paid = (paidEggs[eggId] or 0) > 0
    if paid then
        paidEggs[eggId] -= 1
        if paidEggs[eggId] == 0 then
            paidEggs[eggId] = nil
        end
    end
    dropOne(player, eggId)
    return true, paid
end

-- Undoes a grant exactly (a purchase or a deal taken back): one egg of this kind, a paid one only if the grant was paid.
function EggInventory.revoke(player, eggId, paid)
    local eggs = held[player]
    if not (eggs and (eggs[eggId] or 0) > 0) then
        return false
    end
    local paidEggs = paidHeld[player]
    if paid == true and (paidEggs[eggId] or 0) > 0 then
        paidEggs[eggId] -= 1
        if paidEggs[eggId] == 0 then
            paidEggs[eggId] = nil
        end
    end
    dropOne(player, eggId)
    return true
end

-- A copy for saving (nil until the player is set up).
function EggInventory.exportData(player)
    local eggs = held[player]
    return eggs and table.clone(eggs)
end

-- The paid counts, for saving (nil until the player is set up).
function EggInventory.exportPaid(player)
    local paid = paidHeld[player]
    return paid and table.clone(paid)
end

function EggInventory.removePlayer(player)
    held[player] = nil
    paidHeld[player] = nil
end

return EggInventory
