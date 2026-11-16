-- Striking with the equipped weapon (the "WeaponId" attribute; GameConfig.WeaponKinds) or the Qi
-- Palm (GameConfig.Combat.Palm): left click, gamepad R2 or the touch Strike button. The strike's
-- effects play here at once (CombatFx) and the server is asked to resolve it (CombatEvent); the
-- server relays every strike back for everyone's effects, where it landed, and what it did there
-- (its damage, whether it was critical, the target struck).
--
-- Equipping and putting away (the owner, 2026-11-11, and 2026-11-16: "replace it with the box for inventory weapon"): the weapon
-- sits in slot 1 of the inventory bar (Hud.Inventory); pressing the slot, key 1 or gamepad X asks the server (WeaponDrawEvent)
-- to draw it into the hand or put it back across the back. With no weapon the slot is empty and says where to buy one.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local CombatFx = require(script.Parent:WaitForChild("CombatFx"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local Toast = require(UI:WaitForChild("Toast"))
local UiKit = require(UI:WaitForChild("UiKit"))
local TouchActions = require(UI:WaitForChild("TouchActions"))
local Portraits = require(UI:WaitForChild("Portraits"))

local player = Players.LocalPlayer
local readyAt = 0
local airNoted = false -- the note about striking from sword flight shows once a session
local message = Toast.new("CombatMessage", Color3.new(1, 1, 1), 4)

-- "Palm", "Sword" or "Spear", and its cooldown
local function strikeKind()
    local weapon = Shop.weapon(player:GetAttribute("WeaponId"))
    if not weapon then
        return "Palm", GameConfig.Combat.Palm.Cooldown
    end
    return weapon.Kind, GameConfig.WeaponKinds[weapon.Kind].Cooldown
end

local function strike()
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    if not humanoid or humanoid.Health <= 0 or player:GetAttribute("IsCultivating") == true
        or player:GetAttribute("CarryingEgg") ~= nil then -- both hands are round the egg
        return
    end
    local now = os.clock()
    local kind, cooldown = strikeKind()
    if now < readyAt then
        return
    end
    readyAt = now + cooldown
    if player:GetAttribute("IsFlying") == true and not airNoted then
        airNoted = true
        message:show("You can't hit guardians from the air. Land first.", "Warning")
    end
    CombatFx.play(player, kind)
    RemoteEvents.CombatEvent:FireServer()
end

-- ---------- drawing and sheathing ----------
local DRAW_KEYS = { [Enum.KeyCode.One] = true, [Enum.KeyCode.ButtonX] = true }

-- a weapon to draw, and nothing in the way: not cultivating, not carrying an egg
local function canToggle()
    return player:GetAttribute("WeaponId") ~= nil and player:GetAttribute("IsCultivating") ~= true
        and player:GetAttribute("CarryingEgg") == nil
end

local function toggleDrawn()
    if canToggle() then
        RemoteEvents.WeaponDrawEvent:FireServer(player:GetAttribute("WeaponDrawn") ~= true)
    end
end

-- slot 1 of the inventory bar: the weapon's picture (its forged element's glow too) and name, lit and marked EQUIPPED while in hand
local slot = Hud.Inventory.addSlot(1, { Name = "WeaponSlot" })
local shownWeapon = nil -- the weapon and element the slot's picture shows: it's rebuilt only when they change
slot.Button.Activated:Connect(function()
    if player:GetAttribute("WeaponId") == nil then
        message:show("You have no weapon. Buy one at the Blacksmith on Yggdrasil.", "Info")
    elseif player:GetAttribute("CarryingEgg") ~= nil then
        message:show("Your hands are full: bring the egg home first.", "Warning")
    elseif player:GetAttribute("IsCultivating") == true then
        message:show(if UiKit.usingTouch() then "Stop cultivating first (tap the lotus)." else "Stop cultivating first (press E).", "Info")
    else
        toggleDrawn()
    end
end)

local function refreshSlot()
    local weaponId = player:GetAttribute("WeaponId")
    local weapon = Shop.weapon(weaponId)
    if not weapon then
        shownWeapon = nil
        slot.setEmpty("NO\nWEAPON", "Buy one at the Blacksmith")
        return
    end
    local elementName = player:GetAttribute("WeaponElement")
    local key = weaponId .. "|" .. tostring(elementName)
    if key ~= shownWeapon then
        shownWeapon = key
        local element = Shop.element(elementName)
        local picture = Portraits.weapon(weaponId, element and element.Color, 56)
        picture.BackgroundTransparency = 1
        local edge = picture:FindFirstChildOfClass("UIStroke")
        if edge then
            edge:Destroy()
        end
        slot.setItem(weapon.Name, picture)
    end
    slot.setEquipped(player:GetAttribute("WeaponDrawn") == true)
end
for _, name in { "WeaponId", "WeaponElement", "WeaponDrawn" } do
    player:GetAttributeChangedSignal(name):Connect(refreshSlot)
end
refreshSlot()

UserInputService.InputBegan:Connect(function(input, gameProcessed)
    if gameProcessed then
        return
    end
    if input.UserInputType == Enum.UserInputType.MouseButton1 or input.KeyCode == Enum.KeyCode.ButtonR2 then
        strike()
    elseif DRAW_KEYS[input.KeyCode] then
        toggleDrawn()
    end
end)

RemoteEvents.CombatEvent.OnClientEvent:Connect(function(source, kind, position, step, damage, critical, target)
    if typeof(source) ~= "Instance" or not source:IsA("Player") then
        return
    end
    if source ~= player then
        CombatFx.play(source, kind, step)
    elseif step then
        CombatFx.syncCombo(player, kind, step) -- a press the server dropped can't leave the count wrong
    end
    if typeof(position) == "Vector3" then
        CombatFx.hit(source, position, {
            damage = if typeof(damage) == "number" then damage else nil,
            critical = critical == true,
            target = if typeof(target) == "Instance" and target:IsA("Model") then target else nil,
        })
    end
end)

TouchActions.add("Strike", "Strike", strike)
