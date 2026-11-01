-- Qinggong movement: jump, leap again in mid-air (up to the rank's air leaps), and hold jump
-- while falling to glide. Leaps refill on landing. Keyboard, gamepad and touch.
-- Each takeoff, leap, glide, dash and landing plays its effect here at once (QinggongFx) and is
-- sent to the server, which relays it to other players.
--
-- Stamina (GameConfig.Qinggong.Stamina) fuels dashes and sword flight only. It refills after a
-- short pause, faster on the ground. Movement is the client's (it owns the character's physics);
-- the server grants flight and limits how long it lasts (FlightService).
--   Dash   Q / gamepad B / the touch Dash button: a short burst along the move direction (or the
--          facing), on the ground or in the air.
--   Sword  G / gamepad Y / the touch Sword button: take off on the flying sword or land. While
--          flying, move with the camera (look up or down to climb or dive), hold jump to rise and
--          Ctrl, C or gamepad L2 to sink; still, the sword hovers.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local applyHudScale = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudScale"))
local QinggongFx = require(script.Parent:WaitForChild("QinggongFx"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
local qinggong = GameConfig.Qinggong

local HUD_NAME = "QinggongHud"
local PIP_READY = Color3.fromRGB(150, 235, 255)
local PIP_SPENT = Color3.fromRGB(60, 70, 85)
local GLIDE_COLOR = Color3.fromRGB(190, 255, 220)
local STAMINA_COLOR = Color3.fromRGB(255, 205, 90)
local STAMINA_LOW = Color3.fromRGB(200, 90, 70)
local FLIGHT_COLOR = Color3.fromRGB(255, 225, 140)
local NEW_PRESS_GAP = 0.18 -- jump requests closer than this are one held press
local HARD_LANDING_SPEED = 25 -- a fall faster than this lands with an impact even without Qinggong
local FULL_IMPACT_SPEED = 110 -- the fall speed of a full-strength landing
local MAX_PIPS = GameConfig.Qinggong.Levels[#GameConfig.Qinggong.Levels].AirLeaps

local oldHud = playerGui:FindFirstChild(HUD_NAME)
if oldHud then
    oldHud:Destroy()
end

local hud = Instance.new("ScreenGui")
hud.Name = HUD_NAME
hud.ResetOnSpawn = false

local panel = Instance.new("Frame")
panel.Name = "Panel"
panel.AnchorPoint = Vector2.new(1, 0.5)
panel.Position = UDim2.new(1, -16, 0.5, 0)
panel.Size = UDim2.fromOffset(200, 96)
panel.BackgroundColor3 = Color3.fromRGB(20, 20, 30)
panel.BackgroundTransparency = 0.25
panel.Parent = hud
applyHudScale(panel)
Instance.new("UICorner", panel).CornerRadius = UDim.new(0, 12)

local title = Instance.new("TextLabel")
title.BackgroundTransparency = 1
title.Position = UDim2.fromOffset(10, 6)
title.Size = UDim2.new(1, -20, 0, 22)
title.Font = Enum.Font.GothamBold
title.TextScaled = true
title.TextColor3 = Color3.new(1, 1, 1)
title.TextXAlignment = Enum.TextXAlignment.Left
title.Text = "Qinggong"
title.Parent = panel

local pipRow = Instance.new("Frame")
pipRow.BackgroundTransparency = 1
pipRow.Position = UDim2.fromOffset(10, 32)
pipRow.Size = UDim2.new(1, -20, 0, 14)
pipRow.Parent = panel
local pipLayout = Instance.new("UIListLayout")
pipLayout.FillDirection = Enum.FillDirection.Horizontal
pipLayout.Padding = UDim.new(0, 6)
pipLayout.Parent = pipRow

local pips = {}
for index = 1, MAX_PIPS do
    local pip = Instance.new("Frame")
    pip.Size = UDim2.fromOffset(18, 14)
    pip.BorderSizePixel = 0
    pip.LayoutOrder = index
    pip.Parent = pipRow
    Instance.new("UICorner", pip).CornerRadius = UDim.new(0.5, 0)
    pips[index] = pip
end

local staminaBack = Instance.new("Frame")
staminaBack.Name = "Stamina"
staminaBack.Position = UDim2.fromOffset(10, 52)
staminaBack.Size = UDim2.new(1, -20, 0, 8)
staminaBack.BackgroundColor3 = PIP_SPENT
staminaBack.BorderSizePixel = 0
staminaBack.Parent = panel
Instance.new("UICorner", staminaBack).CornerRadius = UDim.new(0.5, 0)
local staminaFill = Instance.new("Frame")
staminaFill.Size = UDim2.fromScale(1, 1)
staminaFill.BackgroundColor3 = STAMINA_COLOR
staminaFill.BorderSizePixel = 0
staminaFill.Parent = staminaBack
Instance.new("UICorner", staminaFill).CornerRadius = UDim.new(0.5, 0)

local info = Instance.new("TextLabel")
info.BackgroundTransparency = 1
info.Position = UDim2.fromOffset(10, 66)
info.Size = UDim2.new(1, -20, 0, 20)
info.Font = Enum.Font.Gotham
info.TextScaled = true
info.TextColor3 = Color3.fromRGB(200, 200, 210)
info.TextXAlignment = Enum.TextXAlignment.Left
info.Parent = panel

hud.Parent = playerGui

local leapsUsed = 0
local lastJumpRequest = 0
local lastLeapTime = 0
local gliding = false

local stamina = 0
local staminaSpentAt = 0
local dashUntil = 0
local dashReadyAt = 0
local dashDirection = Vector3.zero
local flight = nil -- { velocity, mover, aligner, yaw, landAskedAt } while flying

local function maxStamina()
    local value = player:GetAttribute("QinggongMaxStamina")
    return if typeof(value) == "number" then value else 0
end
stamina = maxStamina()
local function maxLeaps()
    local leaps = player:GetAttribute("QinggongAirLeaps")
    return if typeof(leaps) == "number" then leaps else 0
end

local function updateHud()
    local total = maxLeaps()
    for index, pip in pips do
        pip.Visible = index <= total
        pip.BackgroundColor3 = if index <= total - leapsUsed then PIP_READY else PIP_SPENT
    end
    if flight then
        info.Text = "Sword flight"
        info.TextColor3 = FLIGHT_COLOR
        return
    end
    if gliding then
        info.Text = "Gliding"
        info.TextColor3 = GLIDE_COLOR
        return
    end
    info.TextColor3 = Color3.fromRGB(200, 200, 210)
    local _, nextLevel = Ranks.getQinggong(Ranks.getPlayerRankName(player))
    local nextRank = nextLevel and Ranks.getRankById(nextLevel.RankId)
    info.Text = if nextRank then (nextLevel.AirLeaps .. " leaps at " .. nextRank.Name) else "Air leaps: " .. total
end

local function getCharacterParts()
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    if humanoid and rootPart and humanoid.Health > 0 then
        return humanoid, rootPart
    end
    return nil
end

local function isAirborne(humanoid)
    if humanoid.FloorMaterial ~= Enum.Material.Air then
        return false
    end
    local state = humanoid:GetState()
    return state == Enum.HumanoidStateType.Freefall or state == Enum.HumanoidStateType.Jumping
end

local function playFx(kind, value)
    QinggongFx.play(player, kind, value)
    RemoteEvents.QinggongFxEvent:FireServer(kind, value)
end

local function spend(amount)
    stamina = math.max(0, stamina - amount)
    staminaSpentAt = os.clock()
end

local function updateStaminaBar()
    local total = maxStamina()
    local share = if total > 0 then math.clamp(stamina / total, 0, 1) else 0
    staminaFill.Size = UDim2.fromScale(share, 1)
    staminaFill.BackgroundColor3 = if share < 0.2 then STAMINA_LOW else STAMINA_COLOR
end

-- ---------- dash ----------
local function dash()
    local humanoid, rootPart = getCharacterParts()
    local now = os.clock()
    local config = qinggong.Dash
    if not humanoid or flight or now < dashReadyAt or stamina < config.Cost then
        return
    end
    if player:GetAttribute("IsCultivating") == true or player:GetAttribute("IsFlying") == true then
        return
    end
    local direction = humanoid.MoveDirection
    if direction.Magnitude < 0.05 then
        direction = rootPart.CFrame.LookVector * Vector3.new(1, 0, 1)
    end
    if direction.Magnitude < 0.05 then
        return
    end
    dashDirection = direction.Unit
    dashUntil = now + config.Duration
    dashReadyAt = now + config.Cooldown
    spend(config.Cost)
    playFx("Dash", 0)
end

-- ---------- sword flight ----------
local isJumpHeld -- with the jump keys, below

local function isDescendKey(input)
    return input.KeyCode == Enum.KeyCode.LeftControl or input.KeyCode == Enum.KeyCode.C or input.KeyCode == Enum.KeyCode.ButtonL2
end
local descendHeld = false

local function requestFlight()
    if player:GetAttribute("IsFlying") == true then
        RemoteEvents.FlightEvent:FireServer(false)
        return
    end
    if (player:GetAttribute("QinggongFlightSpeed") or 0) <= 0 or stamina < GameConfig.SwordFlight.MinStamina then
        return
    end
    if player:GetAttribute("IsCultivating") == true then
        return
    end
    RemoteEvents.FlightEvent:FireServer(true)
end

local function startFlight()
    local humanoid, rootPart = getCharacterParts()
    if flight or not humanoid then
        return
    end
    local attachment = rootPart:FindFirstChild("RootAttachment") or Instance.new("Attachment", rootPart)
    local mover = Instance.new("LinearVelocity")
    mover.Name = "SwordFlightMover"
    mover.Attachment0 = attachment
    mover.RelativeTo = Enum.ActuatorRelativeTo.World
    mover.MaxForce = math.huge
    mover.VectorVelocity = rootPart.AssemblyLinearVelocity * Vector3.new(1, 0.3, 1)
    mover.Parent = rootPart
    local aligner = Instance.new("AlignOrientation")
    aligner.Name = "SwordFlightAlign"
    aligner.Mode = Enum.OrientationAlignmentMode.OneAttachment
    aligner.Attachment0 = attachment
    aligner.MaxTorque = math.huge
    aligner.Responsiveness = 18
    aligner.CFrame = rootPart.CFrame.Rotation
    aligner.Parent = rootPart
    humanoid.PlatformStand = true
    if gliding then
        gliding = false
        playFx("Glide", 0)
    end
    flight = { velocity = mover.VectorVelocity, mover = mover, aligner = aligner, landAskedAt = nil, yaw = rootPart.CFrame.LookVector }
    updateHud()
end

local function stopFlight()
    if not flight then
        return
    end
    flight.mover:Destroy()
    flight.aligner:Destroy()
    flight = nil
    local humanoid = getCharacterParts()
    if humanoid then
        humanoid.PlatformStand = false
        humanoid:ChangeState(Enum.HumanoidStateType.Freefall)
    end
    updateHud()
end

local function flyStep(humanoid, rootPart, deltaTime)
    local camera = workspace.CurrentCamera
    local config = GameConfig.SwordFlight
    local speed = player:GetAttribute("QinggongFlightSpeed") or 0
    local move = humanoid.MoveDirection
    local target = Vector3.zero
    if camera and move.Magnitude > 0.05 then
        local look, right = camera.CFrame.LookVector, camera.CFrame.RightVector
        local flatLook = (look * Vector3.new(1, 0, 1)).Unit
        local flatRight = (right * Vector3.new(1, 0, 1)).Unit
        target = (look * move:Dot(flatLook) + right * move:Dot(flatRight)) * speed
    end
    local climb = (if isJumpHeld(humanoid) then 1 else 0) - (if descendHeld then 1 else 0)
    target += Vector3.new(0, climb * config.ClimbSpeed, 0)
    flight.velocity = flight.velocity:Lerp(target, 1 - math.exp(-3.5 * deltaTime))
    flight.mover.VectorVelocity = flight.velocity

    local flat = flight.velocity * Vector3.new(1, 0, 1)
    if flat.Magnitude > 2 then
        flight.yaw = flat.Unit
    elseif camera then
        local camFlat = camera.CFrame.LookVector * Vector3.new(1, 0, 1)
        if camFlat.Magnitude > 0.1 then
            flight.yaw = flight.yaw:Lerp(camFlat.Unit, 1 - math.exp(-2 * deltaTime)).Unit
        end
    end
    local lean = -math.clamp(flat.Magnitude / math.max(speed, 1), 0, 1) * math.rad(14)
    flight.aligner.CFrame = CFrame.lookAt(Vector3.zero, flight.yaw) * CFrame.Angles(lean, 0, 0)

    local moving = flight.velocity.Magnitude > 4
    spend((if moving then config.Cost else config.HoverCost) * deltaTime)
    -- out of stamina: ask to land, again every 0.6 s (the server ignores a toggle within 0.5 s of the last)
    if stamina <= 0 and os.clock() - (flight.landAskedAt or -math.huge) > 0.6 then
        flight.landAskedAt = os.clock()
        RemoteEvents.FlightEvent:FireServer(false)
    end
end

player:GetAttributeChangedSignal("IsFlying"):Connect(function()
    if player:GetAttribute("IsFlying") == true then
        startFlight()
    else
        stopFlight()
    end
end)

local function airLeap(humanoid, rootPart)
    leapsUsed += 1
    lastLeapTime = os.clock()
    local direction = humanoid.MoveDirection
    local horizontal = if direction.Magnitude > 0.05
        then direction.Unit * qinggong.LeapForwardSpeed
        else rootPart.AssemblyLinearVelocity * Vector3.new(0.5, 0, 0.5)
    rootPart.AssemblyLinearVelocity = horizontal + Vector3.new(0, qinggong.LeapUpSpeed, 0)
    playFx("Leap", leapsUsed)
    updateHud()
end

UserInputService.JumpRequest:Connect(function()
    local now = os.clock()
    local isNewPress = now - lastJumpRequest > NEW_PRESS_GAP
    lastJumpRequest = now
    if not isNewPress or now - lastLeapTime < qinggong.LeapCooldown then
        return
    end

    local humanoid, rootPart = getCharacterParts()
    if not humanoid or not isAirborne(humanoid) or leapsUsed >= maxLeaps() then
        return
    end
    if player:GetAttribute("IsFlying") == true or player:GetAttribute("IsCultivating") == true then
        return
    end
    airLeap(humanoid, rootPart)
end)

local jumpKeyHeld = false
local function isJumpKey(input)
    return input.KeyCode == Enum.KeyCode.Space or input.KeyCode == Enum.KeyCode.ButtonA
end
UserInputService.InputBegan:Connect(function(input, gameProcessed)
    if UserInputService:GetFocusedTextBox() then
        return
    end
    if isJumpKey(input) then
        jumpKeyHeld = true
    elseif isDescendKey(input) then
        descendHeld = true
    elseif gameProcessed then
        return
    elseif input.KeyCode == Enum.KeyCode.Q or input.KeyCode == Enum.KeyCode.ButtonB then
        dash()
    elseif input.KeyCode == Enum.KeyCode.G or input.KeyCode == Enum.KeyCode.ButtonY then
        requestFlight()
    end
end)
UserInputService.InputEnded:Connect(function(input)
    if isJumpKey(input) then
        jumpKeyHeld = false
    elseif isDescendKey(input) then
        descendHeld = false
    end
end)
UserInputService.WindowFocusReleased:Connect(function()
    jumpKeyHeld = false
    descendHeld = false
end)

function isJumpHeld(humanoid)
    -- the touch jump button keeps Humanoid.Jump set while it is held
    return jumpKeyHeld or (UserInputService.TouchEnabled and humanoid.Jump)
end

-- the flight since the feet last left the ground, for the landing effect
local airborne = false
local fastestFall = 0
local usedQinggong = false

local function land()
    if os.clock() - lastLeapTime < 0.15 then
        return -- a leap fired on the frame the feet touched down: it carries on upward, so no landing
    end
    local strength = math.clamp((fastestFall - HARD_LANDING_SPEED) / (FULL_IMPACT_SPEED - HARD_LANDING_SPEED), 0, 1)
    if usedQinggong or strength > 0 then
        playFx("Land", if usedQinggong then math.max(strength, 0.3) else strength)
    end
end

RunService.Heartbeat:Connect(function(deltaTime)
    local humanoid, rootPart = getCharacterParts()
    local wasGliding = gliding
    gliding = false
    local now = os.clock()

    if not flight and now - staminaSpentAt > qinggong.Stamina.RegenDelay then
        local onGround = humanoid ~= nil and humanoid.FloorMaterial ~= Enum.Material.Air
        stamina = math.min(maxStamina(), stamina + (if onGround then qinggong.Stamina.RegenGround else qinggong.Stamina.RegenAir) * deltaTime)
    end
    updateStaminaBar()

    if humanoid and flight then
        flyStep(humanoid, rootPart, deltaTime)
        return
    end
    if humanoid and now < dashUntil then
        local speed = player:GetAttribute("QinggongDashSpeed") or 70
        local velocity = rootPart.AssemblyLinearVelocity
        rootPart.AssemblyLinearVelocity = dashDirection * speed + Vector3.new(0, math.max(velocity.Y, -2), 0)
    end

    if humanoid then
        local inAir = isAirborne(humanoid)
        if inAir then
            fastestFall = math.max(fastestFall, -rootPart.AssemblyLinearVelocity.Y)
            usedQinggong = usedQinggong or leapsUsed > 0 or wasGliding
        elseif airborne then
            land()
        end
        if inAir ~= airborne then
            airborne = inAir
            fastestFall = 0
            usedQinggong = false
        end
        if not inAir then
            if leapsUsed ~= 0 then
                leapsUsed = 0
                updateHud()
            end
        elseif player:GetAttribute("IsFlying") ~= true and isJumpHeld(humanoid) then
            local velocity = rootPart.AssemblyLinearVelocity
            if velocity.Y < -qinggong.GlideFallSpeed then
                gliding = true
                local direction = humanoid.MoveDirection
                local horizontal = Vector3.new(velocity.X, 0, velocity.Z)
                if direction.Magnitude > 0.05 then
                    horizontal = horizontal:Lerp(direction.Unit * humanoid.WalkSpeed * qinggong.GlideSpeedFactor, math.min(1, deltaTime * 4))
                end
                rootPart.AssemblyLinearVelocity = horizontal + Vector3.new(0, -qinggong.GlideFallSpeed, 0)
            end
        end
    end

    if gliding ~= wasGliding then
        updateHud()
        playFx("Glide", if gliding then 1 else 0)
    end
end)

local function watchJumps(character)
    local humanoid = character:WaitForChild("Humanoid")
    humanoid.StateChanged:Connect(function(_, new)
        if new == Enum.HumanoidStateType.Jumping and player:GetAttribute("IsCultivating") ~= true
            and player:GetAttribute("IsFlying") ~= true then
            playFx("Takeoff", 0)
        end
    end)
end
if player.Character then
    task.spawn(watchJumps, player.Character)
end
player.CharacterAdded:Connect(watchJumps)

RemoteEvents.QinggongFxEvent.OnClientEvent:Connect(function(source, kind, value)
    if typeof(source) == "Instance" and source:IsA("Player") and source ~= player then
        QinggongFx.play(source, kind, value)
    end
end)

player:GetAttributeChangedSignal("QinggongAirLeaps"):Connect(updateHud)
player:GetAttributeChangedSignal("QinggongMaxStamina"):Connect(function()
    stamina = math.min(stamina, maxStamina())
end)
player.CharacterAdded:Connect(function()
    leapsUsed = 0
    airborne = false
    dashUntil = 0
    if flight then
        flight = nil -- its constraints went with the old character
    end
    stamina = maxStamina()
    updateHud()
end)

if UserInputService.TouchEnabled then
    local touchGui = Instance.new("ScreenGui")
    touchGui.Name = "QinggongTouch"
    touchGui.ResetOnSpawn = false
    local function touchButton(name, text, position)
        local button = Instance.new("TextButton")
        button.Name = name
        button.AnchorPoint = Vector2.new(0.5, 0.5)
        button.Position = position
        button.Size = UDim2.fromOffset(64, 64)
        button.BackgroundColor3 = Color3.fromRGB(20, 20, 30)
        button.BackgroundTransparency = 0.3
        button.Font = Enum.Font.GothamBold
        button.TextScaled = true
        button.TextColor3 = Color3.new(1, 1, 1)
        button.Text = text
        button.Parent = touchGui
        Instance.new("UICorner", button).CornerRadius = UDim.new(0.5, 0)
        local padding = Instance.new("UIPadding")
        padding.PaddingLeft, padding.PaddingRight = UDim.new(0, 10), UDim.new(0, 10)
        padding.Parent = button
        return button
    end
    touchButton("Dash", "Dash", UDim2.new(1, -170, 1, -170)).Activated:Connect(dash)
    local swordButton = touchButton("Sword", "Sword", UDim2.new(1, -95, 1, -220))
    swordButton.Activated:Connect(requestFlight)
    local function showSword()
        swordButton.Visible = (player:GetAttribute("QinggongFlightSpeed") or 0) > 0
    end
    player:GetAttributeChangedSignal("QinggongFlightSpeed"):Connect(showSword)
    showSword()
    touchGui.Parent = playerGui
end
task.spawn(function()
    local rankValue = player:WaitForChild("leaderstats"):WaitForChild("Rank")
    rankValue.Changed:Connect(updateHud)
    updateHud()
end)
updateHud()
