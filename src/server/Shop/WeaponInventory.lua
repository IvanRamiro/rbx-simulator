-- The weapons a player owns (shared/Shop.lua) and the one they strike with. Saved in PlayerData as
-- Weapons = { { InstanceId, WeaponId, Element?, Name? } } (a forged weapon carries its element and
-- the name its owner gave it, GameConfig.Forge) and EquippedWeapon (an InstanceId, or nil for the
-- Qi Palm), and mirrored to the client as the player attributes "WeaponId" and "WeaponElement".
-- A player who owns no weapon is given GameConfig.StarterWeapon, equipped.
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))

local WeaponInventory = {}

local held = {} -- [player] = { weapons = { { InstanceId, WeaponId, Element?, Name? } }, equipped = InstanceId or nil }

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
    player:SetAttribute("WeaponElement", weapon and weapon.Element)
end

local function record(weapon)
    return { InstanceId = weapon.InstanceId, WeaponId = weapon.WeaponId, Element = weapon.Element, Name = weapon.Name }
end

-- Cleans saved weapons: known weapons, unique ids, at most MaxOwnedWeapons; an element only if known,
-- with a name of at most the forge's length (filtered when it was given); an equipped id only if owned.
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
                -- the forge counts a name's characters (utf8.len, ShopService); nil for broken UTF-8
                local length = typeof(weapon.Name) == "string" and utf8.len(weapon.Name)
                local forged = Shop.element(weapon.Element) ~= nil and length and length <= GameConfig.Forge.NameLength.Max
                table.insert(weapons, { InstanceId = weapon.InstanceId, WeaponId = weapon.WeaponId,
                    Element = if forged then weapon.Element else nil, Name = if forged then weapon.Name else nil })
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

-- `progress` is nil for a new player, who is given the starter weapon. Only then: a player who
-- sold every weapon keeps the Qi Palm, or the starter could be sold again on every rejoin.
function WeaponInventory.setupPlayer(player, progress)
    local weapons, equipped = WeaponInventory.sanitize(progress and progress.Weapons, progress and progress.EquippedWeapon)
    local data = { weapons = weapons, equipped = equipped }
    if progress == nil then
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

-- Gives an owned weapon an element and a name (the forge; the caller has checked and charged).
-- False when it isn't theirs.
function WeaponInventory.forge(player, instanceId, element, name)
    local data = held[player]
    local weapon = data and find(data, instanceId)
    if not weapon or not Shop.element(element) then
        return false
    end
    weapon.Element, weapon.Name = element, name
    mirror(player)
    return true
end

-- One owned weapon's record { InstanceId, WeaponId, Element?, Name? }, or nil.
function WeaponInventory.get(player, instanceId)
    local data = held[player]
    local weapon = data and find(data, instanceId)
    return weapon and record(weapon)
end

-- Takes an unequipped weapon out of the inventory; its record, or nil.
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
    return record(weapon)
end

-- The weapon the player strikes with (shared/Shop.lua's entry) and its element, or nil for the Qi Palm.
function WeaponInventory.equipped(player)
    local data = held[player]
    local weapon = data and data.equipped and find(data, data.equipped)
    return weapon and Shop.weapon(weapon.WeaponId), weapon and weapon.Element
end

-- For the client's windows: { Weapons = { { InstanceId, WeaponId, Element?, Name? } }, Equipped = InstanceId or nil }.
function WeaponInventory.snapshot(player)
    local data = held[player]
    if not data then
        return nil
    end
    local weapons = {}
    for _, weapon in data.weapons do
        table.insert(weapons, record(weapon))
    end
    return { Weapons = weapons, Equipped = data.equipped }
end

-- For saving (nil until the player is set up).
function WeaponInventory.exportData(player)
    local data = held[player]
    if not data then
        return nil
    end
    local weapons = {}
    for _, weapon in data.weapons do
        table.insert(weapons, record(weapon))
    end
    return { Weapons = weapons, Equipped = data.equipped }
end

function WeaponInventory.removePlayer(player)
    held[player] = nil
end

return WeaponInventory
