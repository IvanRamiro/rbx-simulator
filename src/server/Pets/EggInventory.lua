-- The eggs a player has taken from guardians and secured, to hatch at Yggdrasil's Hatching Altar
-- (PetService). Saved in PlayerData as Eggs = { [EggId] = count } and mirrored to the client as
-- player attributes "Egg_<EggId>".
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local EggInventory = {}

EggInventory.MAX_PER_EGG = 99

local held = {}

local function mirror(player, eggId)
    local count = held[player] and held[player][eggId] or 0
    player:SetAttribute("Egg_" .. eggId, if count > 0 then count else nil)
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
    for eggId in held[player] do
        mirror(player, eggId)
    end
end

function EggInventory.count(player, eggId)
    return held[player] and held[player][eggId] or 0
end

-- Adds one egg; false when the player isn't set up or already holds the most of it.
function EggInventory.grant(player, eggId)
    local eggs = held[player]
    if not (eggs and GameConfig.Eggs[eggId]) or (eggs[eggId] or 0) >= EggInventory.MAX_PER_EGG then
        return false
    end
    eggs[eggId] = (eggs[eggId] or 0) + 1
    mirror(player, eggId)
    return true
end

-- Spends one egg; false when the player holds none.
function EggInventory.take(player, eggId)
    local eggs = held[player]
    if not (eggs and (eggs[eggId] or 0) > 0) then
        return false
    end
    eggs[eggId] -= 1
    if eggs[eggId] == 0 then
        eggs[eggId] = nil
    end
    mirror(player, eggId)
    return true
end

-- A copy for saving (nil until the player is set up).
function EggInventory.exportData(player)
    local eggs = held[player]
    return eggs and table.clone(eggs)
end

function EggInventory.removePlayer(player)
    held[player] = nil
end

return EggInventory
