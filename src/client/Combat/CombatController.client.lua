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

local player = Players.LocalPlayer
local readyAt = 0

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
    if not humanoid or humanoid.Health <= 0 or player:GetAttribute("IsCultivating") == true then
        return
    end
    local now = os.clock()
    local kind, cooldown = strikeKind()
    if now < readyAt then
        return
    end
    readyAt = now + cooldown
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

RemoteEvents.CombatEvent.OnClientEvent:Connect(function(source, kind, position)
    if typeof(source) ~= "Instance" or not source:IsA("Player") then
        return
    end
    if source ~= player then
        CombatFx.play(source, kind)
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
    button.Position = UDim2.new(1, -230, 1, -100)
    button.Size = UDim2.fromOffset(72, 72)
    button.BackgroundColor3 = Color3.fromRGB(20, 20, 30)
    button.BackgroundTransparency = 0.3
    button.Font = Enum.Font.GothamBold
    button.TextScaled = true
    button.TextColor3 = Color3.new(1, 1, 1)
    button.Text = "Strike"
    button.Parent = gui
    Instance.new("UICorner", button).CornerRadius = UDim.new(0.5, 0)
    local padding = Instance.new("UIPadding")
    padding.PaddingLeft, padding.PaddingRight = UDim.new(0, 10), UDim.new(0, 10)
    padding.Parent = button
    button.Activated:Connect(strike)
    gui.Parent = player:WaitForChild("PlayerGui")
end
