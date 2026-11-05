-- The touch buttons round Roblox's jump button, kept down to what's useful right now, so the thumb never has to pick among
-- them: never more than two beside the jump button.
--   Near something to fight:  Strike and Dash
--   Otherwise:                Sword (once it can be ridden) and Dash
--   Riding the sword:         Sword, to land
--   Cultivating:              nothing, the player is sitting down
-- Strike and Sword share the larger place beside the jump button, Dash has the one above it.
--   TouchActions.add(name, text, onPress)   name is "Strike", "Sword" or "Dash"; on a screen without touch it does nothing
-- In Studio, the player's HudTestTouch attribute shows them without a touch screen.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local UiKit = require(script.Parent:WaitForChild("UiKit"))

local player = Players.LocalPlayer
local FIGHT_DISTANCE = 90 -- studs from something that can be struck
local CHECK_EVERY = 0.4
local SLOTS = {
    Strike = { Position = UDim2.new(1, -148, 1, -52), Size = 62 },
    Sword = { Position = UDim2.new(1, -148, 1, -52), Size = 62 },
    Dash = { Position = UDim2.new(1, -112, 1, -128), Size = 54 },
}

local TouchActions = {}
local buttons = {}
local gui = nil

local function wanted()
    return UserInputService.TouchEnabled or (RunService:IsStudio() and player:GetAttribute("HudTestTouch") == true)
end

local function nearSomethingToStrike()
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if not root then
        return false
    end
    for _, target in CollectionService:GetTagged(GameConfig.Combat.TargetTag) do
        local at = if target:IsA("Model") then target:GetPivot().Position elseif target:IsA("BasePart") then target.Position else nil
        if at and (at - root.Position).Magnitude <= FIGHT_DISTANCE then
            return true
        end
    end
    return false
end

local function refresh()
    local flying = player:GetAttribute("IsFlying") == true
    local cultivating = player:GetAttribute("IsCultivating") == true
    local fighting = nearSomethingToStrike()
    local canRide = (player:GetAttribute("QinggongFlightSpeed") or 0) > 0
    local show = {
        Strike = fighting and not flying and not cultivating,
        Sword = (flying or (canRide and not fighting)) and not cultivating,
        Dash = not flying and not cultivating,
    }
    for name, button in buttons do
        button.Visible = show[name] == true
    end
end

function TouchActions.add(name, text, onPress)
    if not wanted() then
        return nil
    end
    if not gui then
        gui = Instance.new("ScreenGui")
        gui.Name = "TouchActions"
        gui.ResetOnSpawn = false
        gui.Parent = player:WaitForChild("PlayerGui")
        task.spawn(function()
            while gui.Parent do
                refresh()
                task.wait(CHECK_EVERY)
            end
        end)
    end
    local slot = SLOTS[name]
    local button = Instance.new("TextButton")
    button.Name = name
    button.AnchorPoint = Vector2.new(0.5, 0.5)
    button.Position = slot.Position
    button.Size = UDim2.fromOffset(slot.Size, slot.Size)
    UiKit.touchButton(button, text)
    button.Parent = gui
    button.Activated:Connect(onPress)
    buttons[name] = button
    refresh()
    return button
end

return TouchActions
