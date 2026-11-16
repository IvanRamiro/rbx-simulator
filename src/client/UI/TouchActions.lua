-- The touch buttons round Roblox's jump button, kept down to what's useful right now, so the thumb never has to pick among
-- them: never more than two big ones beside the jump button, and the small lotus (Meditate: the owner, 2026-11-16, "a small
-- round meditate button" for touch screens; a keyboard presses E instead).
--   Near something to fight, or the weapon in hand:  Strike and Dash, and Meditate
--   Otherwise:                Sword (once it can be ridden) and Dash, and Meditate
--   Riding the sword:         Sword, to land
--   Cultivating:              Meditate alone, to stand up (the player is sitting down)
-- Strike and Sword share the larger place beside the jump button, Dash has the one above it, Meditate the small one over the
-- jump button's right shoulder. Each stands on a ring round the jump button, the same GAP clear of it, wherever Roblox puts that
-- button for the screen (it is 70 px on a small screen and 120 on a larger one: fixed places that suited the small one put Dash
-- on top of the large one, a tablet's).
--   TouchActions.add(name, text, onPress, image)   name is "Strike", "Sword", "Dash" or "Meditate"; image (optional) shows in
--                                                  place of words. On a screen without touch it does nothing and returns nil.
-- In Studio, the player's HudTestTouch attribute shows them without a touch screen.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local HudMetrics = require(script.Parent:WaitForChild("HudMetrics"))
local UiKit = require(script.Parent:WaitForChild("UiKit"))

local player = Players.LocalPlayer
local FIGHT_DISTANCE = 90 -- studs from something that can be struck
local CHECK_EVERY = 0.4
local GAP = 14 -- px between a button's edge and the jump button's
local SLOTS = { -- Angle: degrees round the jump button's middle, 180 straight left, 90 straight up
    Strike = { Angle = 180, Size = 62 },
    Sword = { Angle = 180, Size = 62 },
    Dash = { Angle = 125, Size = 54 },
    Meditate = { Angle = 68, Size = 46 }, -- small: 46 px, a thumb's 44
}

local TouchActions = {}
local buttons = {}
local gui = nil

-- Roblox's jump button: its middle, as an offset from the screen's bottom right corner, and its radius. Read from the button itself
-- when it is there, otherwise from the rule Roblox's touch controls place it by (a 70 px button on a screen under 500 px on its
-- shorter side, 120 otherwise).
local function jumpButton()
    local touchGui = player:FindFirstChild("PlayerGui") and player.PlayerGui:FindFirstChild("TouchGui")
    local jump = touchGui and touchGui:FindFirstChild("JumpButton", true)
    local _, any = next(buttons)
    local room = if any and any.Parent then any.Parent else gui -- what the buttons stand in (the screen)
    if jump and jump:IsA("GuiObject") and jump.AbsoluteSize.X > 0 and room then
        local corner = room.AbsolutePosition + room.AbsoluteSize
        local middle = jump.AbsolutePosition + jump.AbsoluteSize / 2
        return middle - corner, jump.AbsoluteSize.X / 2
    end
    local area = if room then room.AbsoluteSize else Vector2.new(1280, 720)
    local small = math.min(area.X, area.Y) <= 500
    local size = if small then 70 else 120
    -- (Roblox: Position = (1, -(size * 1.5 - 10), 1, -size - 20) on a small screen, (1, -(size * 1.5 - 10), 1, -size * 1.75) otherwise)
    local middleY = if small then -size - 20 + size / 2 else -size * 1.75 + size / 2
    return Vector2.new(-(size * 1.5 - 10) + size / 2, middleY), size / 2
end

local function place()
    local middle, radius = jumpButton()
    for name, button in buttons do
        local slot = SLOTS[name]
        local reach = radius + GAP + slot.Size / 2
        local angle = math.rad(slot.Angle)
        local at = middle + Vector2.new(math.cos(angle), -math.sin(angle)) * reach
        button.Position = UDim2.new(1, math.round(at.X), 1, math.round(at.Y)) -- (whole pixels: the gaps stay equal on the screen)
    end
end

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
    -- (a drawn weapon is a wish to fight: on a keyboard a click swings it anywhere, so a touch screen gets Strike too)
    local fighting = nearSomethingToStrike() or player:GetAttribute("WeaponDrawn") == true
    local canRide = (player:GetAttribute("QinggongFlightSpeed") or 0) > 0
    local show = {
        Strike = fighting and not flying and not cultivating,
        Sword = (flying or (canRide and not fighting)) and not cultivating,
        Dash = not flying and not cultivating,
        Meditate = not flying and player:GetAttribute("CarryingEgg") == nil,
    }
    for name, button in buttons do
        button.Visible = show[name] == true
    end
end

function TouchActions.add(name, text, onPress, image)
    if not wanted() then
        return nil
    end
    if not gui then
        gui = Instance.new("ScreenGui")
        gui.Name = "TouchActions"
        gui.ResetOnSpawn = false
        gui.Parent = player:WaitForChild("PlayerGui")
        gui:GetPropertyChangedSignal("AbsoluteSize"):Connect(place)
        HudMetrics.Changed:Connect(place) -- (the screen's size: and in Studio, its HudTestViewport stand-in)
        for _, name in { "WeaponDrawn", "IsFlying", "IsCultivating", "CarryingEgg" } do -- (at once, not at the next check)
            player:GetAttributeChangedSignal(name):Connect(refresh)
        end
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
    button.Size = UDim2.fromOffset(slot.Size, slot.Size)
    UiKit.touchButton(button, text, image)
    button.Parent = gui
    button.Activated:Connect(onPress)
    buttons[name] = button
    place()
    refresh()
    return button
end

return TouchActions
