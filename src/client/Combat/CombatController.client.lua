-- Striking with the equipped weapon (the "WeaponId" attribute; GameConfig.WeaponKinds) or the Qi
-- Palm (GameConfig.Combat.Palm): left click, gamepad R2 or the touch Strike button. The strike's
-- effects play here at once (CombatFx) and the server is asked to resolve it (CombatEvent); the
-- server relays every strike back for everyone's effects, where it landed, and what it did there
-- (its damage, whether it was critical, the target struck).
--
-- Drawing and sheathing (the owner, 2026-11-11): key 1, gamepad X or the DRAW / SHEATHE button over the Cultivation
-- dock asks the server (WeaponDrawEvent) to draw the weapon into the hand or put it back across the back.
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
local TouchActions = require(UI:WaitForChild("TouchActions"))
local UiKit = require(UI:WaitForChild("UiKit"))

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
        message:show("Guardians can't be struck from the air: land first.", "Warning")
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

-- the pill sits over the middle of the dock's plate, not of the whole dock (whose left end is the lotus emblem), in a
-- strip as wide as the dock, so the Dock's list keeps it just above
local drawStrip = Instance.new("Frame")
drawStrip.Name = "DrawStrip"
drawStrip.BackgroundTransparency = 1
drawStrip.LayoutOrder = 26
drawStrip.Visible = false
drawStrip.Parent = Hud.Dock
local drawButton = UiKit.button({
    Name = "DrawButton", Tone = "Quiet", Font = "Strong", TextSize = 13, Text = "DRAW",
    AnchorPoint = Vector2.new(0.5, 0), Size = UDim2.fromOffset(150, 38), Parent = drawStrip,
})
local function placeDrawButton(size)
    if not size then
        return
    end
    local plateLeft = math.floor(size.Emblem * 0.45) -- as Hud lays out the dock's plate
    drawStrip.Size = UDim2.fromOffset(size.Width, 38)
    drawButton.Position = UDim2.fromOffset(plateLeft + (size.Width - plateLeft) / 2, 0)
end
Hud.CultivationDock.Resized:Connect(placeDrawButton)
placeDrawButton(Hud.CultivationDock.Size)
local drawKey = UiKit.keycap("1")
drawKey.AnchorPoint = Vector2.new(1, 0.5)
drawKey.Position = UDim2.new(1, -5, 0.5, 0)
drawKey.Size = UDim2.fromOffset(20, 20)
drawKey.Parent = drawButton
drawButton.Activated:Connect(toggleDrawn)

local function refreshDrawButton()
    drawStrip.Visible = canToggle()
    drawButton.Text = if player:GetAttribute("WeaponDrawn") == true then "SHEATHE" else "DRAW"
end
for _, name in { "WeaponId", "WeaponDrawn", "IsCultivating", "CarryingEgg" } do
    player:GetAttributeChangedSignal(name):Connect(refreshDrawButton)
end
refreshDrawButton()

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
