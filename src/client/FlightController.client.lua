-- Free flight for your own character, plus its HUD button.
--
-- The server decides whether you may fly and how fast (the "FlightSpeed" and
-- "IsFlying" attributes, see FlightService); this script only asks to take
-- off or land and then moves the character while "IsFlying" is true.
--
-- Controls: Q (or gamepad Y, or the Fly button) takes off and lands. While
-- flying you move with the normal movement controls (WASD, thumbstick or the
-- touch joystick) in the direction the camera faces, so looking up or down
-- climbs or dives. Space / gamepad A also climb, Ctrl or C / gamepad B descend.
--
-- Flying uses a LinearVelocity (movement) and an AlignOrientation (keeps the
-- body level and facing the way you fly) on the root part, with the humanoid
-- in PlatformStand so it doesn't fight them.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local applyHudScale = require(script.Parent:WaitForChild("HudScale"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local HUD_NAME = "FlightHud"
local PANEL_COLOR = Color3.fromRGB(20, 20, 30)
local FLY_COLOR = Color3.fromRGB(70, 130, 200)
local LAND_COLOR = Color3.fromRGB(200, 120, 60)
local LOCKED_COLOR = Color3.fromRGB(90, 90, 90)

local CLIMB_SPEED_FACTOR = 0.7 -- Climbing and descending speed compared with flight speed
local TAKE_OFF_BOOST = 12 -- Upward speed when taking off, in studs per second
local MAX_TILT = math.rad(70) -- How far the body leans forward at full speed (stretched out, see PoseController)
local MIN_HEIGHT_ABOVE_VOID = 60 -- Never dive closer than this to where Roblox removes fallen parts
local PITCH_DEADZONE = math.rad(25) -- Camera pitch that still flies level
local GROUND_CLEARANCE = 4 -- Studs above the ground where diving stops (land with Q instead)

local flight = GameConfig.Flight
local lastToggleRequestTime = 0

-- Build the HUD ------------------------------------------------------------

local oldHud = playerGui:FindFirstChild(HUD_NAME)
if oldHud then
    oldHud:Destroy()
end

local hud = Instance.new("ScreenGui")
hud.Name = HUD_NAME
hud.ResetOnSpawn = false

-- Right side, middle of the screen (clear of the mobile jump button)
local panel = Instance.new("Frame")
panel.Name = "Panel"
panel.AnchorPoint = Vector2.new(1, 0.5)
panel.Position = UDim2.new(1, -16, 0.5, 0)
panel.Size = UDim2.fromOffset(200, 96)
panel.BackgroundColor3 = PANEL_COLOR
panel.BackgroundTransparency = 0.25
panel.Parent = hud
applyHudScale(panel)

local panelCorner = Instance.new("UICorner")
panelCorner.CornerRadius = UDim.new(0, 12)
panelCorner.Parent = panel

local flyButton = Instance.new("TextButton")
flyButton.Name = "FlyButton"
flyButton.Position = UDim2.fromOffset(10, 10)
flyButton.Size = UDim2.new(1, -20, 0, 42)
flyButton.Font = Enum.Font.GothamBold
flyButton.TextScaled = true
flyButton.TextColor3 = Color3.new(1, 1, 1)
flyButton.Parent = panel

local buttonCorner = Instance.new("UICorner")
buttonCorner.CornerRadius = UDim.new(0, 10)
buttonCorner.Parent = flyButton

local infoLabel = Instance.new("TextLabel")
infoLabel.Name = "InfoLabel"
infoLabel.Position = UDim2.fromOffset(10, 58)
infoLabel.Size = UDim2.new(1, -20, 0, 30)
infoLabel.BackgroundTransparency = 1
infoLabel.Font = Enum.Font.Gotham
infoLabel.TextScaled = true
infoLabel.TextWrapped = true
infoLabel.TextColor3 = Color3.fromRGB(200, 200, 210)
infoLabel.Parent = panel

hud.Parent = playerGui

local function getFlightSpeed()
    local speed = player:GetAttribute("FlightSpeed")
    return if typeof(speed) == "number" then speed else 0
end

local function isFlying()
    return player:GetAttribute("IsFlying") == true
end

local function updateHud()
    local keyName = flight.Keybind.Name
    local speed = getFlightSpeed()

    local leaderstats = player:FindFirstChild("leaderstats")
    local rankValue = leaderstats and leaderstats:FindFirstChild("Rank")
    local _, nextLevel = Ranks.getFlightSpeed(if rankValue then rankValue.Value else "")
    local nextRank = nextLevel and Ranks.getRankById(nextLevel.RankId)

    if speed <= 0 then
        flyButton.Text = "Fly (locked)"
        flyButton.BackgroundColor3 = LOCKED_COLOR
        flyButton.AutoButtonColor = false
        infoLabel.Text = if nextRank then "Unlocks at " .. nextRank.Name else ""
        return
    end

    flyButton.AutoButtonColor = true
    if isFlying() then
        flyButton.Text = "Land [" .. keyName .. "]"
        flyButton.BackgroundColor3 = LAND_COLOR
    else
        flyButton.Text = "Fly [" .. keyName .. "]"
        flyButton.BackgroundColor3 = FLY_COLOR
    end

    infoLabel.Text = if nextRank
        then "Speed " .. speed .. " (" .. nextLevel.Speed .. " at " .. nextRank.Name .. ")"
        else "Speed " .. speed .. " (max)"
end

local function requestToggleFlight()
    -- Local cooldown only avoids spamming the server; the server checks too
    local now = os.clock()
    if now - lastToggleRequestTime < flight.ToggleCooldown or getFlightSpeed() <= 0 then
        return
    end
    lastToggleRequestTime = now

    RemoteEvents.FlightEvent:FireServer(not isFlying())
end

flyButton.Activated:Connect(requestToggleFlight)

UserInputService.InputBegan:Connect(function(input, gameProcessedEvent)
    if gameProcessedEvent then
        return -- Typing in chat
    end

    if input.KeyCode == flight.Keybind or input.KeyCode == flight.GamepadButton then
        requestToggleFlight()
    end
end)

-- Flying movement ------------------------------------------------------------

-- Turns the humanoid's MoveDirection into a 3D flying direction that follows
-- the camera, so looking up or down while moving forward climbs or dives.
-- MoveDirection is filled in by Roblox's own controls on every device
-- (keyboard, gamepad and the touch joystick) and keeps updating while
-- PlatformStand is on. (Reading the controls through PlayerModule doesn't
-- work everywhere: in current Studio it isn't in PlayerScripts, so flight got
-- no input at all and players could only float. Checked in Studio.)
local function getFlyDirection(humanoid, camera)
    local moveDirection = humanoid.MoveDirection
    if moveDirection.Magnitude < 0.01 then
        return Vector3.zero
    end

    -- How much of the input is "forward" and "right" relative to the camera
    local flatLook = Vector3.new(camera.LookVector.X, 0, camera.LookVector.Z)
    local flatRight = Vector3.new(camera.RightVector.X, 0, camera.RightVector.Z)
    if flatLook.Magnitude < 0.01 or flatRight.Magnitude < 0.01 then
        return moveDirection -- Looking straight up or down: just move flat
    end
    local forward = moveDirection:Dot(flatLook.Unit)
    local right = moveDirection:Dot(flatRight.Unit)

    -- The usual third-person camera looks a little down at the character, so
    -- small camera pitches fly level; only looking clearly up or down climbs
    -- or dives. (Without this, flying forward kept sinking into the ground.)
    local pitch = math.asin(math.clamp(camera.LookVector.Y, -1, 1))
    local steer = math.max(math.abs(pitch) - PITCH_DEADZONE, 0) / (math.pi / 2 - PITCH_DEADZONE) * math.pi / 2
    local look = flatLook.Unit * math.cos(steer) + Vector3.new(0, math.sign(pitch) * math.sin(steer), 0)

    local direction = look * forward + flatRight.Unit * right
    return if direction.Magnitude > 1 then direction.Unit else direction
end

-- State while flying; nil on the ground
local active = nil -- { humanoid, rootPart, attachment, mover, aligner, velocity }

local function stopFlying()
    if not active then
        return
    end

    local state = active
    active = nil
    state.attachment:Destroy() -- Also removes the mover and aligner parented to it
    if state.humanoid.Parent then
        state.humanoid.PlatformStand = false
        state.humanoid:ChangeState(Enum.HumanoidStateType.Freefall)
    end
end

local function startFlying()
    if active then
        return
    end

    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    if not (humanoid and rootPart) or humanoid.Health <= 0 then
        return
    end

    local attachment = Instance.new("Attachment")
    attachment.Name = "FlightAttachment"
    attachment.Parent = rootPart

    local mover = Instance.new("LinearVelocity")
    mover.Name = "FlightMover"
    mover.Attachment0 = attachment
    mover.RelativeTo = Enum.ActuatorRelativeTo.World
    mover.VelocityConstraintMode = Enum.VelocityConstraintMode.Vector
    mover.MaxForce = 1e6
    mover.VectorVelocity = Vector3.zero
    mover.Parent = attachment

    local aligner = Instance.new("AlignOrientation")
    aligner.Name = "FlightAligner"
    aligner.Attachment0 = attachment
    aligner.Mode = Enum.OrientationAlignmentMode.OneAttachment
    aligner.MaxTorque = 1e6
    aligner.Responsiveness = 15
    aligner.CFrame = rootPart.CFrame.Rotation
    aligner.Parent = attachment

    humanoid.PlatformStand = true

    active = {
        humanoid = humanoid,
        rootPart = rootPart,
        attachment = attachment,
        mover = mover,
        aligner = aligner,
        velocity = rootPart.AssemblyLinearVelocity * Vector3.new(1, 0, 1) + Vector3.new(0, TAKE_OFF_BOOST, 0),
    }
end

local function isDown(keyCodes, gamepadButton)
    for _, keyCode in keyCodes do
        if UserInputService:IsKeyDown(keyCode) then
            return true
        end
    end
    return UserInputService:IsGamepadButtonDown(Enum.UserInputType.Gamepad1, gamepadButton)
end

-- Diving stops just above the ground, so you don't scrape along it lying flat
local function isNearGround(state)
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = { state.rootPart.Parent }
    params.IgnoreWater = false
    return workspace:Raycast(state.rootPart.Position, Vector3.new(0, -GROUND_CLEARANCE, 0), params) ~= nil
end

local function updateFlight(deltaTime)
    local state = active
    if not state then
        return
    end

    if not state.rootPart.Parent or state.humanoid.Health <= 0 then
        stopFlying()
        return
    end

    -- Jumping can switch PlatformStand off; keep it on while flying
    if not state.humanoid.PlatformStand then
        state.humanoid.PlatformStand = true
    end

    local speed = getFlightSpeed()
    local camera = workspace.CurrentCamera.CFrame

    local direction = getFlyDirection(state.humanoid, camera)

    local climb = 0
    if UserInputService:GetFocusedTextBox() == nil then
        if isDown({ Enum.KeyCode.Space }, Enum.KeyCode.ButtonA) then
            climb += 1
        end
        if isDown({ Enum.KeyCode.LeftControl, Enum.KeyCode.C }, Enum.KeyCode.ButtonB) then
            climb -= 1
        end
    end

    local target = direction * speed + Vector3.new(0, climb * speed * CLIMB_SPEED_FACTOR, 0)
    if target.Y < 0 and (state.rootPart.Position.Y < workspace.FallenPartsDestroyHeight + MIN_HEIGHT_ABOVE_VOID
        or isNearGround(state)) then
        target = Vector3.new(target.X, 0, target.Z)
    end

    state.velocity = state.velocity:Lerp(target, 1 - math.exp(-flight.Acceleration * deltaTime))
    state.mover.VectorVelocity = state.velocity

    -- Face the way you fly (or the camera's way while hovering), leaning
    -- forward a little more the faster you go
    local horizontal = Vector3.new(state.velocity.X, 0, state.velocity.Z)
    local facing = if horizontal.Magnitude > 2 then horizontal else Vector3.new(camera.LookVector.X, 0, camera.LookVector.Z)
    if facing.Magnitude > 0.01 then
        local tilt = if speed > 0 then math.min(horizontal.Magnitude / speed, 1) * MAX_TILT else 0
        state.aligner.CFrame = CFrame.lookAt(Vector3.zero, facing.Unit) * CFrame.Angles(-tilt, 0, 0)
    end
end

RunService.RenderStepped:Connect(updateFlight)

local function updateFlightState()
    if isFlying() then
        startFlying()
    else
        stopFlying()
    end
    updateHud()
end

player:GetAttributeChangedSignal("IsFlying"):Connect(updateFlightState)
player:GetAttributeChangedSignal("FlightSpeed"):Connect(updateHud)
player.CharacterAdded:Connect(function()
    -- The old character's flight objects went with it
    active = nil
    updateFlightState()
end)

-- The next speed level depends on the rank, which arrives with leaderstats
task.spawn(function()
    local rankValue = player:WaitForChild("leaderstats"):WaitForChild("Rank")
    rankValue.Changed:Connect(updateHud)
    updateHud()
end)

updateFlightState()
