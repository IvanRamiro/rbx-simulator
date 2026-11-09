-- How this device really runs the game (November 9, 2026: the phone pass, the owner's "do the 3"). Studio can't measure a
-- phone, so every player's client measures itself: its frame rate (the average, and the slow end: the 95th percentile frame)
-- and its memory, every two minutes after the first, sent to the server for the Creator Dashboard (PerfService, as
-- ClientFps and ClientMemory, by device: Phone, Tablet, PC or Console). For developers (GameConfig.Titles.DeveloperUserIds),
-- a live readout at the top left, switched on in Settings (their "PerfReadout" attribute): frame rate, its slow end, memory,
-- the instances in the game and the parts drawn.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Stats = game:GetService("Stats")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Quality = require(script.Parent.Parent:WaitForChild("Quality"))

local player = Players.LocalPlayer
local FIRST_REPORT, REPORT_EVERY = 60, 120 -- seconds (the first after the loading has settled)
local WINDOW = 4096 -- frames kept for the slow end

local function deviceClass()
    local camera = Workspace.CurrentCamera
    local view = if camera then camera.ViewportSize else Vector2.new(1920, 1080)
    if UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled then
        return if math.min(view.X, view.Y) < 600 then "Phone" else "Tablet"
    elseif UserInputService.GamepadEnabled and not UserInputService.KeyboardEnabled and not UserInputService.MouseEnabled then
        return "Console"
    end
    return "PC"
end

local frames, count, head = table.create(WINDOW, 0), 0, 0
local spent = 0

local function measure()
    local n = math.min(count, WINDOW)
    if n < 30 then
        return nil
    end
    local list = table.move(frames, 1, n, 1, {})
    table.sort(list)
    local slow = list[math.max(1, math.floor(n * 0.95))]
    return count / math.max(spent, 1e-6), 1 / math.max(slow, 1e-6)
end

RunService.Heartbeat:Connect(function(dt)
    head = head % WINDOW + 1
    frames[head] = dt
    count += 1
    spent += dt
end)

-- the readout, for developers
local readout = nil
local isDeveloper = table.find(GameConfig.Titles.DeveloperUserIds, player.UserId) ~= nil
local function showReadout(on)
    if readout then
        readout.Parent:Destroy()
        readout = nil
    end
    if not on then
        return
    end
    local gui = Instance.new("ScreenGui")
    gui.Name = "PerfReadout"
    gui.ResetOnSpawn = false
    gui.DisplayOrder = 100
    local label = Instance.new("TextLabel")
    label.BackgroundColor3 = Color3.new(0, 0, 0)
    label.BackgroundTransparency = 0.35
    label.TextColor3 = Color3.fromRGB(180, 255, 190)
    label.Font = Enum.Font.Code
    label.TextSize = 14
    label.AutomaticSize = Enum.AutomaticSize.XY
    label.Position = UDim2.fromOffset(6, 6)
    label.TextXAlignment = Enum.TextXAlignment.Left
    label.Parent = gui
    gui.Parent = player:WaitForChild("PlayerGui")
    readout = label
end
if isDeveloper then
    player:GetAttributeChangedSignal("PerfReadout"):Connect(function()
        showReadout(player:GetAttribute("PerfReadout") == true)
    end)
end

local sinceReport = -FIRST_REPORT + REPORT_EVERY
local sinceReadout = 0
RunService.Heartbeat:Connect(function(dt)
    sinceReport += dt
    sinceReadout += dt
    if readout and sinceReadout >= 0.5 then
        sinceReadout = 0
        local fps, low = measure()
        readout.Text = string.format(" %s%s  %d fps (slowest 5%%: %d)  %d MB  %d instances  %d parts drawn ",
            deviceClass(), if Quality.Low then " (phone tier)" else "", math.round(fps or 0), math.round(low or 0),
            math.round(Stats:GetTotalMemoryUsageMb()), Stats.InstanceCount, Stats.PrimitivesCount)
    end
    if sinceReport >= REPORT_EVERY then
        sinceReport = 0
        local fps, low = measure()
        if fps then
            RemoteEvents.PerfEvent:FireServer(fps, low, Stats:GetTotalMemoryUsageMb(), deviceClass(), Quality.Low)
        end
        count, spent = 0, 0 -- each report its own two minutes
    end
end)
