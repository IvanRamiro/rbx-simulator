-- The weapons a player owns (shared/Shop.lua) and the one they strike with. Saved in PlayerData as
-- Weapons = { { InstanceId, WeaponId } } and EquippedWeapon (an InstanceId, or nil for the Qi Palm),
-- and mirrored to the client as the player attribute "WeaponId" (the equipped weapon's id).
-- A player who owns no weapon is given GameConfig.StarterWeapon, equipped.
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))

local WeaponInventory = {}

local held = {} -- [player] = { weapons = { { InstanceId, WeaponId } }, equipped = InstanceId or nil }

local function find(data, instanceId)
    for index, weapon in data.weapons do
        if weapon.InstanceId == instanceId then
            return weapon, index
        end
    end
    return nil
end

local function mirror(player)
    local data = held[player]
    local weapon = data and data.equipped and find(data, data.equipped)
    player:SetAttribute("WeaponId", weapon and weapon.WeaponId)
end

-- Cleans saved weapons: known weapons, unique ids, at most MaxOwnedWeapons; an equipped id only if owned.
function WeaponInventory.sanitize(rawWeapons, rawEquipped)
    local weapons, seen = {}, {}
    if typeof(rawWeapons) == "table" then
        for _, weapon in rawWeapons do
            if #weapons >= GameConfig.MaxOwnedWeapons then
                break
            end
            local valid = typeof(weapon) == "table" and typeof(weapon.InstanceId) == "string" and #weapon.InstanceId > 0
                and #weapon.InstanceId <= 64 and Shop.weapon(weapon.WeaponId) ~= nil
            if valid and not seen[weapon.InstanceId] then
                seen[weapon.InstanceId] = true
                table.insert(weapons, { InstanceId = weapon.InstanceId, WeaponId = weapon.WeaponId })
            end
        end
    end
    return weapons, if typeof(rawEquipped) == "string" and seen[rawEquipped] then rawEquipped else nil
end

local function add(data, weaponId)
    local weapon = { InstanceId = HttpService:GenerateGUID(false), WeaponId = weaponId }
    table.insert(data.weapons, weapon)
    return weapon
end

function WeaponInventory.setupPlayer(player, progress)
    local weapons, equipped = WeaponInventory.sanitize(progress and progress.Weapons, progress and progress.EquippedWeapon)
    local data = { weapons = weapons, equipped = equipped }
    if #weapons == 0 then
        data.equipped = add(data, GameConfig.StarterWeapon).InstanceId
    end
    held[player] = data
    mirror(player)
end

function WeaponInventory.isFull(player)
    local data = held[player]
    return data == nil or #data.weapons >= GameConfig.MaxOwnedWeapons
end

function WeaponInventory.owns(player, weaponId)
    local data = held[player]
    for _, weapon in data and data.weapons or {} do
        if weapon.WeaponId == weaponId then
            return true
        end
    end
    return false
end

-- Adds a weapon; its InstanceId, or nil when the player isn't set up or has no room.
function WeaponInventory.grant(player, weaponId)
    if WeaponInventory.isFull(player) or not Shop.weapon(weaponId) then
        return nil
    end
    return add(held[player], weaponId).InstanceId
end

-- Equips an owned weapon (nil: the Qi Palm); false when it isn't theirs.
function WeaponInventory.equip(player, instanceId)
    local data = held[player]
    if not data or (instanceId ~= nil and not find(data, instanceId)) then
        return false
    end
    data.equipped = instanceId
    mirror(player)
    return true
end

-- Takes an unequipped weapon out of the inventory; its WeaponId, or nil.
function WeaponInventory.take(player, instanceId)
    local data = held[player]
    if not data then
        return nil
    end
    local weapon, index = find(data, instanceId)
    if not weapon or data.equipped == instanceId then
        return nil
    end
    table.remove(data.weapons, index)
    return weapon.WeaponId
end

-- The weapon the player strikes with (shared/Shop.lua's entry), or nil for the Qi Palm.
function WeaponInventory.equipped(player)
    local data = held[player]
    local weapon = data and data.equipped and find(data, data.equipped)
    return weapon and Shop.weapon(weapon.WeaponId)
end

-- For the client's windows: { Weapons = { { InstanceId, WeaponId } }, Equipped = InstanceId or nil }.
function WeaponInventory.snapshot(player)
    local data = held[player]
    return data and { Weapons = table.clone(data.weapons), Equipped = data.equipped }
end

-- For saving (nil until the player is set up).
function WeaponInventory.exportData(player)
    local data = held[player]
    if not data then
        return nil
    end
    local weapons = {}
    for _, weapon in data.weapons do
        table.insert(weapons, { InstanceId = weapon.InstanceId, WeaponId = weapon.WeaponId })
    end
    return { Weapons = weapons, Equipped = data.equipped }
end

function WeaponInventory.removePlayer(player)
    held[player] = nil
end

return WeaponInventory
