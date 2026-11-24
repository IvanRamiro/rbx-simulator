-- The LanternWarden pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, SPARKLE, pose, smoothstep, dropToGround = K.PetRig, K.SPARKLE, K.pose, K.smoothstep, K.dropToGround

    local animateLanternWarden, WARDEN_SOLE -- animateLanternWarden's section below (its own locals stay in its block)
    do

        -- The Lantern Warden (skinned): it stoops along on two thin legs, in no hurry, with its lantern swinging on the chain and its cape following late. Its face is a mask and doesn't change: what changes is the angle of its head, held very still and then slowly tilted,
        -- and the pupils behind the slits, which slide about on their own (they turn on a pivot inside the mask, so they stay behind it) and blink by drawing back into the dark. When its light dims it turns and gives the lantern a tap.
        local WARDEN_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        WARDEN_SOLE = 1.145 -- metres from the middle of its box down to its toes: it walks on the ground, and leaves it only to fly
        local WARDEN_GLANCE = 0.2 -- radians either way the pupils slide
        local WARDEN_LEGS = { L = 0, R = math.pi }
        local WARDEN_LIGHT, WARDEN_DIM = Color3.fromRGB(255, 118, 26), Color3.fromRGB(110, 46, 12)

        -- The lantern hangs: a damped pendulum, driven by how the Warden is accelerating
        local function wardenPendulum(rig, s, dt, fly)
            local at = rig.rootPart.Position
            local step = math.clamp(dt, 0.001, 0.05)
            local moved = at - (s.lastAt or at)
            s.lastAt = at
            local inFrame = rig.rootPart.CFrame:VectorToObjectSpace(moved / math.max(dt, 0.001))
            -- more than 20 studs in one frame is not movement (a dash at 170 studs/s is under 3): it was teleported, or caught up with a teleported player
            if moved.Magnitude > 20 then
                inFrame = s.lastV or Vector3.zero
            end
            -- what it feels is its acceleration, smoothed: the follow path's small corrections shouldn't reach the lantern
            local push = (inFrame - (s.lastV or inFrame)) / step
            s.lastV = inFrame
            s.push = (s.push or Vector3.zero):Lerp(push, math.min(1, step * 9))
            local forward, sideways = math.clamp(-s.push.Z, -24, 24), math.clamp(s.push.X, -24, 24)
            local unit = rig.meters
            s.swingX = s.swingX or 0
            s.swingZ = s.swingZ or 0
            s.spinX = s.spinX or 0
            s.spinZ = s.spinZ or 0
            -- a pendulum about 0.35 m long: stiffness g/L, and it settles in a few swings
            local stiff, damp = 26, 2.2
            local restX = -0.5 * fly
            s.spinX = math.clamp(s.spinX + (-stiff * (s.swingX - restX) - damp * s.spinX - 2.4 * forward / unit) * step, -4, 4)
            s.spinZ = math.clamp(s.spinZ + (-stiff * s.swingZ - damp * s.spinZ - 2.4 * sideways / unit) * step, -4, 4)
            s.swingX += s.spinX * step
            s.swingZ += s.spinZ * step
            if math.abs(s.swingX) > 0.8 then -- the chain's limit: it stops there, and doesn't store up speed against it
                s.swingX = math.clamp(s.swingX, -0.8, 0.8)
                s.spinX = 0
            end
            if math.abs(s.swingZ) > 0.6 then
                s.swingZ = math.clamp(s.swingZ, -0.6, 0.6)
                s.spinZ = 0
            end
            return s.swingX, s.swingZ
        end

        function animateLanternWarden(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > WARDEN_FAR then
                s.lastAt, s.lastV = nil, nil -- its lantern starts afresh when it comes back into view
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, WARDEN_SOLE)

            -- the special: it lifts the crook and reaches for the lantern, and the flame stands up; a path of small lights runs out from its feet, winds once round it and comes back to exactly where it started; it watches them all the way, and then tilts its head
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local raise = smoothstep(0, 0.36, progress) * (1 - smoothstep(0.62, 0.86, progress))
            local surge = smoothstep(0.36, 0.42, progress) * (1 - smoothstep(0.5, 0.86, progress))
            local round = math.clamp((progress - 0.42) / 0.42, 0, 1)
            local watching = smoothstep(0.42, 0.47, progress) * (1 - smoothstep(0.82, 0.88, progress))
            local puzzled = smoothstep(0.84, 0.9, progress) * (1 - smoothstep(0.95, 1, progress))

            -- its light sometimes sinks: it turns to it, and taps
            s.nextTap = s.nextTap or t + 9 + math.random() * 8
            local tap, sunk = 0, 0
            if t >= s.nextTap then
                local a = (t - s.nextTap) / 3.2
                if a >= 1 then
                    s.nextTap = t + 13 + math.random() * 14
                elseif pace < 0.25 and nova == 0 then
                    tap = smoothstep(0.08, 0.26, a) * (1 - smoothstep(0.8, 1, a))
                    sunk = smoothstep(0, 0.14, a) * (1 - smoothstep(0.58, 0.64, a))
                    if a > 0.5 and a < 0.62 then
                        local knock = math.sin((a - 0.5) / 0.12 * math.pi * 2)
                        s.spinX = (s.spinX or 0) + 5 * knock * math.min(dt, 0.05)
                    end
                else
                    s.nextTap = t + 3
                end
            end

            -- the head: very still, and then slowly somewhere else, at an angle no neck would choose
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2.4 + math.random() * 4
                s.gazeTo = (math.random() - 0.5) * 1.0
                s.nodTo = (math.random() - 0.5) * 0.16
                s.tiltTo = if math.random() < 0.45 then (math.random() - 0.5) * 0.7 else 0
            end
            local calm = (1 - pace * 0.7) * (1 - nova) * (1 - tap)
            local yawTo = (s.gazeTo or 0) * calm + 0.62 * tap + 0.7 * raise * (1 - watching) + 0.85 * watching * math.sin(round * 2 * math.pi)
            local nodTo = (s.nodTo or 0) * calm + 0.16 * tap + 0.44 * raise * (1 - watching) - 0.42 * watching
            local tiltTo = (s.tiltTo or 0) * calm + 0.14 * tap + 0.55 * puzzled
            local slow = math.min(1, dt * 2.8)
            s.yaw = (s.yaw or 0) + (yawTo - (s.yaw or 0)) * slow
            s.nod = (s.nod or 0) + (nodTo - (s.nod or 0)) * slow
            s.tilt = (s.tilt or 0) + (tiltTo - (s.tilt or 0)) * slow

            -- the walk: long, slow stilt steps, the cape riding a little after each
            s.stride = (s.stride or 0) + dt * 5.4 * moving
            local stride = s.stride
            local breath = math.sin(t * 0.9)
            local look = rig.rootPart.CFrame.LookVector
            local heading = math.atan2(-look.X, -look.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.16, 0.16) - (s.bank or 0)) * math.min(1, dt * 3)
            local pitch = 0.008 * math.sin(t * 0.9 - 0.6) - 0.05 * moving - 0.18 * fly + 0.1 * raise
            local rise = 0.012 * moving * math.cos(2 * stride) + 0.14 * fly + 0.03 * fly * math.sin(t * 1.5) + 0.03 * raise
            pose(m.Body, CFrame.new(0, rise * u - drop, 0) * CFrame.Angles(pitch, 0.05 * moving * math.sin(stride), s.bank + 0.045 * moving * math.sin(stride)))
            pose(m.Chest, CFrame.new(0, 0.004 * breath * u, 0) * CFrame.Angles(0.012 * moving * math.cos(2 * stride - 0.6), 0, 0))
            pose(m.Neck, CFrame.Angles(-pitch * 0.4 + s.nod * 0.42, s.yaw * 0.42, s.tilt * 0.26))
            pose(m.Head, CFrame.Angles(-pitch * 0.4 + s.nod * 0.58, s.yaw * 0.58, s.tilt * 0.74 - s.bank * 0.4))
            pose(m.Hat, CFrame.Angles(0.12 * fly + 0.012 * moving * math.cos(2 * stride - 1), 0, 0.012 * moving * math.sin(stride - 0.8)))

            -- the pupils get there first, and blink by drawing back into the dark
            s.nextBlink = s.nextBlink or t + 2
            if t >= s.nextBlink then
                s.nextBlink = t + 2.5 + math.random() * 4.5
                s.blinkAt = t
            end
            local shut = if s.blinkAt and t - s.blinkAt < 0.2 then 1 - math.abs(2 * (t - s.blinkAt) / 0.2 - 1) else 0
            s.eyeYaw = (s.eyeYaw or 0) + (math.clamp((yawTo - s.yaw) * 0.9 + 0.5 * math.sin(t * 0.37) * calm, -1, 1) - (s.eyeYaw or 0)) * math.min(1, dt * 16)
            local eye = CFrame.new(0, 0, 0.03 * shut * u) * CFrame.Angles(0, s.eyeYaw * WARDEN_GLANCE, 0)
            pose(m.EyeL, eye)
            pose(m.EyeR, eye)

            -- the legs: a bird's: the knee leads, and the shin folds as it comes through
            local reach = 0.5 * moving
            for side, lead in WARDEN_LEGS do
                local phase = stride + lead
                local swing = math.sin(phase) * reach
                local fold = math.max(0, math.cos(phase)) * moving
                -- flying: they trail, one a little behind the other, toes hanging
                local trail = fly * (if side == "L" then -0.5 else -0.32) + 0.05 * fly * math.sin(t * 1.5 + lead)
                pose(m["Leg" .. side .. "1"], CFrame.Angles(swing + trail - pitch, 0, 0))
                pose(m["Leg" .. side .. "2"], CFrame.Angles(-0.9 * fold + 0.25 * fly, 0, 0))
                pose(m["Leg" .. side .. "3"], CFrame.Angles(1.0 * fold + 0.18 * fly, 0, 0))
                pose(m["Foot" .. side], CFrame.Angles(-0.5 * fold - 0.34 * fly, 0, 0))
            end

            -- the cape: its hems trail at speed, bounce with each step, and flare in the air
            local bounce = moving * math.abs(math.sin(stride - 0.5))
            for tier, key in { Mid = 0.6, Low = 1 } do
                local trail = (0.14 * moving + 0.26 * fly) * key
                local flare = (0.05 * bounce + 0.2 * fly + 0.014 * (breath + 1)) * key
                local sway = 0.05 * moving * math.sin(stride - 0.9) * key
                pose(m[tier .. "F"], CFrame.Angles(-trail + flare * 0.6, 0, sway))
                pose(m[tier .. "B"], CFrame.Angles(-trail - flare, 0, sway))
                pose(m[tier .. "L"], CFrame.Angles(-trail * 0.6, 0, sway - flare))
                pose(m[tier .. "R"], CFrame.Angles(-trail * 0.6, 0, sway + flare))
            end

            -- the crook lifts for the special and gives a little with each step; the lantern swings
            local give = 0.012 * moving * math.cos(2 * stride - 1)
            pose(m.Crook1, CFrame.Angles(0.1 * raise + give + 0.14 * fly, 0, 0))
            pose(m.Crook2, CFrame.Angles(0.22 * raise + give, 0, 0.012 * moving * math.sin(stride - 1)))
            pose(m.Crook3, CFrame.Angles(0.26 * raise + give, 0, 0.018 * moving * math.sin(stride - 1.3)))
            local swingX, swingZ = wardenPendulum(rig, s, dt, fly)
            swingX += 0.03 * math.sin(t * 0.8) - pitch * 0.5 + 0.05 * moving * math.sin(2 * stride - 1)
            swingZ += 0.024 * math.sin(t * 0.53) + 0.09 * moving * math.sin(stride - 1.2)
            pose(m.Chain1, CFrame.Angles(swingX, 0, swingZ))
            pose(m.Chain2, CFrame.Angles(swingX * 0.3, 0, swingZ * 0.3))
            pose(m.Lantern, CFrame.Angles(swingX * 0.14, 0.2 * math.sin(t * 0.31), swingZ * 0.14))

            -- its left hand goes to the lantern; flying, its right holds its hat on
            local reachUp = math.max(raise, tap)
            local knock = if tap > 0.9 then 0.1 * math.sin(t * 16) else 0
            pose(m.ArmL1, CFrame.Angles(0.742 * reachUp + 0.36 * raise + 0.012 * breath + 0.05 * moving * math.sin(stride + 1), 0.496 * reachUp, 0))
            pose(m.ArmL2, CFrame.Angles(knock, 0.083 * reachUp, 0))
            pose(m.HandL, CFrame.Angles(0.3 * reachUp, 0, 0))
            pose(m.ArmR1, CFrame.Angles(1.111 * fly + 0.012 * breath - 0.05 * moving * math.sin(stride + 1), -0.193 * fly, 0))
            pose(m.ArmR2, CFrame.Angles(0.68 * fly, -0.45 * fly, 0))
            pose(m.HandR, CFrame.Angles(0.3 * fly, 0, 0))

            -- the flame. Nobody lit it, and nobody quite controls it
            local flicker = 0.5 + 0.5 * math.sin(t * 7.3 + 2.1 * math.sin(t * 2.3))
            local strength = (0.84 + 0.16 * flicker) * (1 - 0.72 * sunk) + 0.5 * surge
            local panels = rig.parts.Panels
            if panels then
                panels.Color = if strength > 1 then WARDEN_LIGHT:Lerp(Color3.fromRGB(255, 176, 84), math.min(1, strength - 1)) else WARDEN_DIM:Lerp(WARDEN_LIGHT, strength)
            end
            if not s.wardenLight and rig.points.Flame then
                local light = Instance.new("PointLight")
                light.Name = "LanternLight"
                light.Color = Color3.fromRGB(255, 170, 90)
                light.Shadows = false
                light.Parent = rig.points.Flame
                s.wardenLight = light
                -- a few sparks drifting up, the only thing about it that hurries
                local motes = Instance.new("ParticleEmitter")
                motes.Name = "Motes"
                motes.Texture = SPARKLE
                motes.Rate = 2.2
                motes.Lifetime = NumberRange.new(1.1, 1.9)
                motes.Speed = NumberRange.new(0.1 * u, 0.26 * u)
                motes.EmissionDirection = Enum.NormalId.Top
                motes.SpreadAngle = Vector2.new(50, 50)
                motes.Acceleration = Vector3.new(0, 0.12 * u, 0)
                motes.Drag = 0.6
                motes.Size = NumberSequence.new(0.03 * u, 0)
                motes.Color = ColorSequence.new(Color3.fromRGB(255, 220, 150), Color3.fromRGB(255, 130, 50))
                motes.LightEmission = 1
                motes.LightInfluence = 0
                motes.Parent = rig.points.Flame
            end
            if s.wardenLight then
                s.wardenLight.Range = (2.2 + 0.9 * surge) * u
                s.wardenLight.Brightness = 1.2 * strength
            end
        end
    end

    return { animateLanternWarden = animateLanternWarden, WARDEN_SOLE = WARDEN_SOLE }
end
