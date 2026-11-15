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
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Hud = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Hud"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))
local Toast = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Toast"))
local TouchActions = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("TouchActions"))
local UiKit = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiKit"))
local UiTheme = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiTheme"))
local HudMetrics = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("HudMetrics"))
local QinggongFx = require(script.Parent:WaitForChild("QinggongFx"))

local player = Players.LocalPlayer
local qinggong = GameConfig.Qinggong

local GLIDE_COLOR = UiTheme.Colors.AccentBright
local STAMINA_COLOR = UiTheme.Colors.Highlight
local STAMINA_LOW = UiTheme.Colors.Danger
local FLIGHT_COLOR = UiTheme.Colors.Highlight
local NEW_PRESS_GAP = 0.18 -- jump requests closer than this are one held press
local HARD_LANDING_SPEED = 25 -- a fall faster than this lands with an impact even without Qinggong
local FULL_IMPACT_SPEED = 110 -- the fall speed of a full-strength landing

-- ---------- the air leaps (the HUD's right column, under the quest panel) ----------
-- One slim panel in the quest panel's column (Hud.Quest: it follows the panel as it folds, and goes with it while a window is
-- open), as wide as the panel (Hud.rightColumnWidth): AIR LEAPS, a gold diamond for each leap left and a dim one for each used,
-- and the count. GLIDING or SWORD FLIGHT in the word's place while they last. Stamina (it fuels dashes and sword flight) shows
-- only in flight (the owner, 2026-11-16): a bar under the leaps, red and pulsing when it runs low; it is hidden on the ground.
local C = UiTheme.Colors
local ROW, BAR_ROW, PAD = 32, 22, UiTheme.Pad.Card
local WORD_WIDTH, COUNT_WIDTH, GAP = 96, 44, 8 -- the label's room, the count's room, and the gap either side of the diamonds
local leapPanel = UiKit.panel({ Name = "AirLeaps", Brackets = false, LayoutOrder = 10, Parent = Hud.Quest })
local leapWord = UiKit.boldLabel({
    Name = "Word", TextSize = 13, Text = "AIR LEAPS", TextColor3 = C.Edge, Position = UDim2.fromOffset(PAD, 0),
    Size = UDim2.fromOffset(WORD_WIDTH, ROW), Parent = leapPanel,
})
local leapCount = UiKit.boldLabel({
    Name = "Count", TextSize = 15, Text = "", TextXAlignment = Enum.TextXAlignment.Right, AnchorPoint = Vector2.new(1, 0),
    Position = UDim2.new(1, -PAD, 0, 0), Size = UDim2.fromOffset(COUNT_WIDTH, ROW), Parent = leapPanel,
})
-- the diamonds: all the room between the label and the count, right-aligned against the count; each diamond shrinks so any
-- number of leaps fits (the top ranks have 11: at a fixed 16 each they ran left over AIR LEAPS, the owner's screenshot
-- 2026-11-16)
local pips = Instance.new("Frame")
pips.Name = "Pips"
pips.BackgroundTransparency = 1
pips.AnchorPoint = Vector2.new(1, 0)
pips.Position = UDim2.new(1, -(PAD + COUNT_WIDTH + GAP), 0, 0)
pips.Size = UDim2.fromOffset(0, ROW) -- (sized by layoutPips, from the label's real width)
pips.ClipsDescendants = true -- (never past its room, whatever the count)
pips.Parent = leapPanel
-- the label's real width, back in the HUD's own units (TextBounds is on the screen, after the HUD's scale and any readable-text
-- minimum: a fixed 96 let the bar run 7 px into AIR LEAPS on a desktop screen)
local function wordWidth()
    return math.max(WORD_WIDTH, math.ceil(leapWord.TextBounds.X / math.max(HudMetrics.scale(), 0.01)))
end
local function pipRoom()
    return math.max(0, Hud.rightColumnWidth() - (PAD + wordWidth() + GAP + GAP + COUNT_WIDTH + PAD))
end
local function layoutPips()
    pips.Size = UDim2.fromOffset(pipRoom(), ROW)
end
UiKit.list(pips, {
    FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Right,
    VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 7),
})
local staminaRow = Instance.new("Frame")
staminaRow.Name = "StaminaRow"
staminaRow.BackgroundTransparency = 1
staminaRow.Position = UDim2.fromOffset(PAD, ROW - 2)
staminaRow.Size = UDim2.new(1, -PAD * 2, 0, BAR_ROW - 6)
staminaRow.Visible = false
staminaRow.Parent = leapPanel
local staminaBack = UiKit.bar({ Name = "Stamina", Fill = STAMINA_COLOR, Size = UDim2.fromScale(1, 1), Parent = staminaRow })
staminaBack:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(1, 0)
local staminaFill = staminaBack:FindFirstChild("Fill")
staminaFill:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(1, 0)
staminaFill.Size = UDim2.fromScale(1, 1)
local staminaText = UiKit.label({ -- on the row, not the track, which clips what's inside it
    Name = "StaminaText", Font = "Strong", TextSize = 10, TextColor3 = Color3.new(1, 1, 1), TextStrokeTransparency = 0.25,
    TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.fromScale(1, 1), ZIndex = 4, Parent = staminaRow,
})

local function fitLeapPanel()
    local flying = staminaRow.Visible
    leapPanel.Size = UDim2.fromOffset(Hud.rightColumnWidth(), if flying then ROW + BAR_ROW else ROW)
end
Hud.CompactChanged:Connect(fitLeapPanel)
fitLeapPanel()

local shownPips = -1 -- the leaps total the diamonds were made for
local MIN_PIP = 10 -- below this a diamond can't be read: many leaps show as a bar instead
local pipBar -- the bar's fill, while the leaps are shown as a bar
local function drawPips(left, total)
    if total ~= shownPips then
        layoutPips()
        shownPips = total
        pipBar = nil
        pips:ClearAllChildren()
        -- one cell per leap, as big as the room allows (16 at most), the gap a third of a cell
        local count = math.max(total, 1)
        local cellSize = math.min(16, math.floor(pipRoom() / (count + (count - 1) / 3)))
        if cellSize < MIN_PIP then
            -- too many to draw as diamonds (the top ranks have 11): a slim gold bar the leaps drain, the count beside it
            local track = UiKit.bar({ Name = "LeapBar", Fill = C.Highlight, AnchorPoint = Vector2.new(1, 0.5),
                Position = UDim2.fromScale(1, 0.5), Size = UDim2.new(1, 0, 0, 8), Parent = pips })
            track:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(1, 0)
            pipBar = track:FindFirstChild("Fill")
            pipBar:FindFirstChildOfClass("UICorner").CornerRadius = UDim.new(1, 0)
        else
            local gap = math.max(2, math.floor(cellSize / 3 + 0.5))
            UiKit.list(pips, {
                FillDirection = Enum.FillDirection.Horizontal, HorizontalAlignment = Enum.HorizontalAlignment.Right,
                VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, gap),
            })
            for i = 1, total do
                local cell = Instance.new("Frame") -- (a laid-out frame isn't drawn turned: the diamond turns inside it)
                cell.Name = "Pip"
                cell.BackgroundTransparency = 1
                cell.Size = UDim2.fromOffset(cellSize, cellSize)
                cell.LayoutOrder = i
                cell.Parent = pips
                local diamond = Instance.new("Frame")
                diamond.Name = "Diamond"
                diamond.AnchorPoint = Vector2.new(0.5, 0.5)
                diamond.Position = UDim2.fromScale(0.5, 0.5)
                local side = math.floor(cellSize * 0.7)
                diamond.Size = UDim2.fromOffset(side, side)
                diamond.Rotation = 45
                diamond.BorderSizePixel = 0
                diamond.Parent = cell
                UiKit.stroke(diamond, Color3.fromRGB(70, 44, 10), 0, 1.5)
            end
        end
    end
    if pipBar then
        pipBar.Size = UDim2.fromScale(if total > 0 then left / total else 0, 1)
        return
    end
    for _, cell in pips:GetChildren() do
        local diamond = cell:FindFirstChild("Diamond")
        if diamond then
            local lit = cell.LayoutOrder <= left
            diamond.BackgroundColor3 = if lit then C.Highlight else C.Well
            diamond:FindFirstChildOfClass("UIStroke").Color = if lit then Color3.fromRGB(70, 44, 10) else C.EdgeDim
        end
    end
end

local staminaMessage = Toast.new("StaminaMessage", Color3.new(1, 1, 1), 3)
local outOfStaminaNoted = 0
local stamina = 0
local function refuseDash()
    Sfx.play("Error")
    if os.clock() - outOfStaminaNoted > 10 then -- (the bar is hidden on the ground: say it, now and then)
        outOfStaminaNoted = os.clock()
        staminaMessage:show("Out of stamina: wait a moment, then dash again.", "Warning")
    end
end

local leapsUsed = 0
local lastJumpRequest = 0
local lastLeapTime = 0
local gliding = false

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
    local flying = flight ~= nil
    local total = maxLeaps()
    local left = math.max(0, total - leapsUsed)
    leapWord.Text = if flying then "SWORD FLIGHT" elseif gliding then "GLIDING" else "AIR LEAPS"
    leapWord.TextColor3 = if flying then FLIGHT_COLOR elseif gliding then GLIDE_COLOR else UiTheme.Colors.Edge
    pips.Visible = not flying
    leapCount.Visible = not flying
    -- in flight the diamonds and count are hidden: SWORD FLIGHT takes the row; otherwise the label keeps to its room
    leapWord.Size = if flying then UDim2.new(1, -PAD * 2, 0, ROW) else UDim2.fromOffset(WORD_WIDTH, ROW)
    drawPips(left, total)
    leapCount.Text = left .. "/" .. total
    leapCount.TextColor3 = if left == 0 and total > 0 then UiTheme.Colors.Muted else UiTheme.Colors.Text
    leapPanel.Visible = total > 0 or flying
    if staminaRow.Visible ~= flying then
        staminaRow.Visible = flying
        fitLeapPanel()
    end
end

-- the column's width (the screen's class) or the label's width (text size) changed: the diamonds are sized for it again
local function relayoutPips()
    layoutPips()
    shownPips = -1
    updateHud()
end
Hud.CompactChanged:Connect(relayoutPips)
leapWord:GetPropertyChangedSignal("TextBounds"):Connect(function()
    if leapWord.Text == "AIR LEAPS" then -- (SWORD FLIGHT has the row to itself, with the diamonds hidden)
        relayoutPips()
    end
end)

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
    if not staminaRow.Visible then
        return
    end
    local total = maxStamina()
    local share = if total > 0 then math.clamp(stamina / total, 0, 1) else 0
    staminaFill.Size = UDim2.fromScale(share, 1)
    local low = share < 0.25
    staminaFill.BackgroundColor3 = if low then STAMINA_LOW else STAMINA_COLOR
    staminaFill.BackgroundTransparency = if low then 0.25 + 0.25 * math.sin(os.clock() * 8) else 0
    staminaText.Text = "STAMINA  " .. math.floor(share * 100 + 0.5) .. "%"
end

-- ---------- dash ----------
local function dash()
    local humanoid, rootPart = getCharacterParts()
    local now = os.clock()
    local config = qinggong.Dash
    if humanoid and not flight and now >= dashReadyAt and stamina < config.Cost then
        refuseDash()
    end
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
local knownMax = maxStamina()
player:GetAttributeChangedSignal("QinggongMaxStamina"):Connect(function()
    -- the first value to arrive (on joining) fills the bar; later changes only cap it
    stamina = if knownMax == 0 then maxStamina() else math.min(stamina, maxStamina())
    knownMax = maxStamina()
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

TouchActions.add("Dash", "Dash", dash)
TouchActions.add("Sword", "Sword", requestFlight)
task.spawn(function()
    local rankValue = player:WaitForChild("leaderstats"):WaitForChild("Rank")
    rankValue.Changed:Connect(updateHud)
    updateHud()
end)
updateHud()
