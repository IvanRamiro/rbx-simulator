
-- Shows the player's Qi and lets them train with a button or keybind.
-- The client only *asks* to train; the server decides whether it counts
-- and how much Qi to award.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local TrainingEvent = require(ReplicatedStorage:WaitForChild("TrainingEvent"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local HUD_NAME = "QiHud"
local READY_COLOR = Color3.fromRGB(70, 160, 110)
local COOLDOWN_COLOR = Color3.fromRGB(90, 90, 90)

local keyName = GameConfig.TrainingKeybind.Name
local isOnCooldown = false

-- Build the HUD ------------------------------------------------------------

-- Remove a leftover HUD if this script somehow runs twice
local oldHud = playerGui:FindFirstChild(HUD_NAME)
if oldHud then
    oldHud:Destroy()
end

local hud = Instance.new("ScreenGui")
hud.Name = HUD_NAME
hud.ResetOnSpawn = false -- Keep the HUD (and its connections) when the character respawns

local panel = Instance.new("Frame")
panel.Name = "Panel"
panel.AnchorPoint = Vector2.new(0.5, 1)
panel.Position = UDim2.new(0.5, 0, 1, -24)
panel.Size = UDim2.fromOffset(240, 110)
panel.BackgroundColor3 = Color3.fromRGB(20, 20, 30)
panel.BackgroundTransparency = 0.25
panel.Parent = hud

local panelCorner = Instance.new("UICorner")
panelCorner.CornerRadius = UDim.new(0, 12)
panelCorner.Parent = panel

local qiLabel = Instance.new("TextLabel")
qiLabel.Name = "QiLabel"
qiLabel.Position = UDim2.fromOffset(10, 8)
qiLabel.Size = UDim2.new(1, -20, 0, 36)
qiLabel.BackgroundTransparency = 1
qiLabel.Font = Enum.Font.GothamBold
qiLabel.TextScaled = true
qiLabel.TextColor3 = Color3.fromRGB(150, 230, 255)
qiLabel.Text = "Qi: ..."
qiLabel.Parent = panel

local trainButton = Instance.new("TextButton")
trainButton.Name = "TrainButton"
trainButton.Position = UDim2.fromOffset(10, 52)
trainButton.Size = UDim2.new(1, -20, 0, 48)
trainButton.BackgroundColor3 = READY_COLOR
trainButton.AutoButtonColor = true
trainButton.Font = Enum.Font.GothamBold
trainButton.TextScaled = true
trainButton.TextColor3 = Color3.new(1, 1, 1)
trainButton.Text = "Train [" .. keyName .. "]"
trainButton.Parent = panel

local buttonCorner = Instance.new("UICorner")
buttonCorner.CornerRadius = UDim.new(0, 10)
buttonCorner.Parent = trainButton

hud.Parent = playerGui

-- Training -----------------------------------------------------------------

local function setButtonReady(isReady)
    trainButton.BackgroundColor3 = if isReady then READY_COLOR else COOLDOWN_COLOR
    trainButton.Text = if isReady then "Train [" .. keyName .. "]" else "Meditating..."
end

local function requestTraining()
    -- Local cooldown only avoids spamming the server; the server enforces the real one
    if isOnCooldown then
        return
    end

    isOnCooldown = true
    setButtonReady(false)
    TrainingEvent:FireServer()

    task.delay(GameConfig.TrainingCooldown, function()
        isOnCooldown = false
        setButtonReady(true)
    end)
end

trainButton.Activated:Connect(requestTraining)

UserInputService.InputBegan:Connect(function(input, gameProcessedEvent)
    -- gameProcessedEvent is true while typing in chat or a text box
    if gameProcessedEvent then
        return
    end

    if input.KeyCode == GameConfig.TrainingKeybind then
        requestTraining()
    end
end)

-- Qi display ---------------------------------------------------------------

local qiValue = player:WaitForChild("leaderstats"):WaitForChild("Qi")

local function updateQiLabel()
    qiLabel.Text = "Qi: " .. qiValue.Value
end

qiValue.Changed:Connect(updateQiLabel)
updateQiLabel()
