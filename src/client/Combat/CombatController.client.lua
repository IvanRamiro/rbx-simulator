-- Striking with the equipped weapon (the "WeaponId" attribute; GameConfig.WeaponKinds) or the Qi
-- Palm (GameConfig.Combat.Palm): left click, gamepad R2 or the touch Strike button. The strike's
-- effects play here at once (CombatFx) and the server is asked to resolve it (CombatEvent); the
-- server relays every strike back for everyone's effects and where it landed.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local CombatFx = require(script.Parent:WaitForChild("CombatFx"))
local Toast = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Toast"))
local UiKit = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiKit"))

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
        message:show("Guardians can't be struck from the air: land first.", Color3.new(1, 1, 1))
    end
    CombatFx.play(player, kind)
    RemoteEvents.CombatEvent:FireServer()
end

UserInputService.InputBegan:Connect(function(input, gameProcessed)
    if gameProcessed then
        return
    end
    if input.UserInputType == Enum.UserInputType.MouseButton1 or input.KeyCode == Enum.KeyCode.ButtonR2 then
        strike()
    end
end)

RemoteEvents.CombatEvent.OnClientEvent:Connect(function(source, kind, position, step)
    if typeof(source) ~= "Instance" or not source:IsA("Player") then
        return
    end
    if source ~= player then
        CombatFx.play(source, kind, step)
    elseif step then
        CombatFx.syncCombo(player, kind, step) -- a press the server dropped can't leave the count wrong
    end
    if typeof(position) == "Vector3" then
        CombatFx.hit(source, position)
    end
end)

if UserInputService.TouchEnabled then
    local gui = Instance.new("ScreenGui")
    gui.Name = "CombatTouch"
    gui.ResetOnSpawn = false
    local button = Instance.new("TextButton")
    button.Name = "Strike"
    button.AnchorPoint = Vector2.new(0.5, 0.5)
    button.Position = UDim2.new(1, -148, 1, -52)
    button.Size = UDim2.fromOffset(62, 62)
    UiKit.touchButton(button, "Strike")
    button.Parent = gui
    button.Activated:Connect(strike)
    gui.Parent = player:WaitForChild("PlayerGui")
end
