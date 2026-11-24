-- The EclipseCat pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, SPARKLE, pose, smoothstep, dropToGround = K.PetRig, K.SPARKLE, K.pose, K.smoothstep, K.dropToGround

    local animateEclipseCat, CAT_CORONA, CAT_LEADS, CAT_SOLE, CAT_SUN -- animateEclipseCat's section below (its own locals stay in its block)
    do

        -- The Eclipse Cat (skinned): a stylized black cat with a crescent tail, after the owner's concept sheet. It walks a cat's lateral walk with its tail
        -- held high; still for a few seconds, it sits, its tail lying behind it; its gaze wanders and now and then settles on you with a slow blink, the
        -- way a cat tells someone it trusts them; its ears swivel on their own, its tail sways and the tip flicks; gold and violet sparkles drift off it.
        local CAT_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        CAT_SOLE = 0.5573 -- metres from the middle of its box down to its paws: it walks on the ground
        local CAT_LID_HINGE = { L = Vector3.new(0.8802, -0.3085, -0.3606), R = Vector3.new(0.8802, 0.3085, 0.3606) } -- both lids of an eye turn on this line
        local CAT_BLINK_UPPER, CAT_BLINK_LOWER = math.rad(42), math.rad(18)
        CAT_LEADS = { BL = 0, FL = math.pi / 2, BR = math.pi, FR = 3 * math.pi / 2 } -- a lateral walk: a hind foot, then the fore on its side
        -- its sit, found by a search in Blender over these joints (paws flat on the ground, the seat down): the same numbers as eclipse_cat.py's SIT
        local CAT_SIT = { body = 0.38, drop = 0.045, back = 0.02, hips = 0.7, fore = -0.38, thigh = -0.4, shin = -1.1, hock = 0.42 }
        local CAT_SIT_TAIL = { { 0.5, 1.1 }, { 0.2, 0.7 }, { 0, 0.6 }, { -0.1, 0.5 }, { 0, 0.4 }, { 0, 0.3 } }
        CAT_SUN, CAT_CORONA = Color3.fromRGB(255, 210, 120), Color3.fromRGB(255, 244, 214)

        local function catSparkles(rig, s)
            s.sparkles = true
            local tip = rig.points.Tail6
            if not tip then
                return
            end
            local sparkles = Instance.new("ParticleEmitter")
            sparkles.Name = "Sparkles"
            sparkles.Texture = SPARKLE
            sparkles.Rate = 2.2
            sparkles.Lifetime = NumberRange.new(1.2, 2)
            sparkles.Speed = NumberRange.new(0.05 * rig.unit, 0.2 * rig.unit)
            sparkles.SpreadAngle = Vector2.new(180, 180)
            sparkles.Acceleration = Vector3.new(0, 0.12 * rig.unit, 0)
            sparkles.Drag = 1
            sparkles.Rotation = NumberRange.new(0, 360)
            sparkles.RotSpeed = NumberRange.new(-40, 40)
            sparkles.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.09 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
            sparkles.Color = ColorSequence.new(Color3.fromRGB(255, 214, 130), Color3.fromRGB(176, 124, 255))
            sparkles.LightEmission = 1
            sparkles.LightInfluence = 0
            sparkles.Parent = tip
        end

        function animateEclipseCat(rig, s, moving, fly, nova)
            if not s.sparkles then
                catSparkles(rig, s)
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > CAT_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, CAT_SOLE)

            -- the special, Totality: it sits and looks up to the sky as the moon crosses the sun (Blasts.Totality); at totality it purrs, a tremor through
            -- it, its eyes wide; then the light comes back
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local look = smoothstep(0.04, 0.3, progress) * (1 - smoothstep(0.78, 0.95, progress))
            local purr = smoothstep(0.42, 0.47, progress) * (1 - smoothstep(0.68, 0.78, progress))

            -- it sits after a few seconds still, and for its special; it gets up as soon as it has somewhere to go
            s.still = if pace < 0.05 then (s.still or 0) + dt else 0
            local wantSit = if pace > 0.1 then 0 elseif nova > 0 or s.still > 4 then 1 else 0
            s.sit = (s.sit or 0) + (wantSit - (s.sit or 0)) * math.min(1, dt * (if wantSit > (s.sit or 0) then 2.4 else 6))
            local sit = smoothstep(0, 1, s.sit)

            -- the legs: a lateral walk; in the air a stretched leap, forelegs reaching, hind legs pushed back; folded into the sit
            s.stride = (s.stride or 0) + dt * (8.5 * moving + 2 * fly)
            for key, lead in CAT_LEADS do
                local phase = s.stride + lead
                local swing, lift = math.sin(phase), math.max(0, math.cos(phase))
                local p1, p2, p3, p4
                if string.sub(key, 1, 1) == "F" then
                    p1 = moving * 0.4 * swing + fly * 0.8
                    p2 = moving * 0.1 * lift
                    p3 = -moving * 0.9 * lift - fly * 0.35
                    p4 = -moving * 0.3 * lift
                    p1 = p1 * (1 - sit) + CAT_SIT.fore * sit
                    p2, p3, p4 = p2 * (1 - sit), p3 * (1 - sit), p4 * (1 - sit)
                else
                    p1 = -moving * 0.4 * swing - fly * 0.8
                    p2 = moving * 0.45 * lift + fly * 0.45
                    p3 = -moving * 0.6 * lift
                    p4 = 0
                    p1 = p1 * (1 - sit) + CAT_SIT.thigh * sit
                    p2 = p2 * (1 - sit) + CAT_SIT.shin * sit
                    p3 = p3 * (1 - sit) + CAT_SIT.hock * sit
                end
                pose(m["Leg" .. key .. "1"], CFrame.Angles(p1, 0, 0))
                pose(m["Leg" .. key .. "2"], CFrame.Angles(p2, 0, 0))
                pose(m["Leg" .. key .. "3"], CFrame.Angles(p3, 0, 0))
                pose(m["Paw" .. key], CFrame.Angles(p4, 0, 0))
            end

            -- the body: a slight sway with its steps, banking on turns, a purr's tremor; lowered and tipped back into the sit
            local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.16, 0.16) - (s.bank or 0)) * math.min(1, dt * 3)
            local breath = math.sin(t * 1.6)
            local tremor = 0.0015 * purr * math.sin(t * 62)
            pose(m.Body, CFrame.new(0, (0.003 * breath + tremor - CAT_SIT.drop * sit + 0.012 * moving * math.abs(math.sin(s.stride))) * u - drop, CAT_SIT.back * sit * u)
                * CFrame.Angles(CAT_SIT.body * sit + 0.1 * fly, 0.04 * moving * math.sin(s.stride), s.bank))
            pose(m.Hips, CFrame.Angles(CAT_SIT.hips * sit - 0.05 * fly, -0.05 * moving * math.sin(s.stride), 0))
            pose(m.Chest, CFrame.Angles(0.01 * breath, 0.03 * moving * math.sin(s.stride + 1), 0))

            -- its gaze wanders; now and then it turns to you and holds; it looks to the sky in the special; a curious tilt of the head
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2 + math.random() * 3.5
                s.atYou = math.random() < 0.45
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 0.9, (math.random() - 0.5) * 0.3
                s.tilt = if math.random() < 0.3 then (math.random() - 0.5) * 0.5 else 0
            end
            local calm = (1 - 0.7 * pace) * (1 - look)
            local wantYaw = if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.9, 0.9) else s.gazeYaw
            local wantPitch = if s.atYou then math.clamp(toYou.Y * 0.6, -0.3, 0.4) else s.gazePitch
            s.yaw = (s.yaw or 0) + (wantYaw * calm - (s.yaw or 0)) * math.min(1, dt * 3)
            s.pitch = (s.pitch or 0) + (wantPitch * calm - (s.pitch or 0)) * math.min(1, dt * 3)
            s.headTilt = (s.headTilt or 0) + ((s.tilt or 0) * calm - (s.headTilt or 0)) * math.min(1, dt * 2.5)
            pose(m.Neck, CFrame.Angles(0.3 * s.pitch + 0.25 * look - 0.08 * moving + 0.015 * breath, 0.4 * s.yaw, 0))
            pose(m.Head, CFrame.Angles(0.5 * s.pitch + 0.55 * look + 0.03 * moving * math.sin(2 * s.stride), 0.6 * s.yaw, s.headTilt))
            for _, side in { "L", "R" } do
                pose(m["Eye" .. side], CFrame.Angles(0.25 * s.pitch, 0.25 * s.yaw, 0))
            end

            -- the eyes: quick blinks; a slow blink when it is looking at you; content, half-lidded, when it sits; wide in the special
            s.nextBlink = s.nextBlink or t + 2
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / (if s.slowBlink then 1.4 else 0.18)
                if a >= 1 then
                    s.nextBlink = t + 2.5 + math.random() * 3.5
                    s.slowBlink = s.atYou and math.random() < 0.6
                else
                    blink = if s.slowBlink then smoothstep(0, 0.4, a) * (1 - smoothstep(0.6, 1, a)) * 0.8 else 1 - math.abs(2 * a - 1)
                end
            end
            local close = math.max(blink, 0.22 * sit * (1 - look)) * (1 - 0.8 * look)
            local upper = CAT_BLINK_UPPER * close - math.rad(6) * look
            local lower = CAT_BLINK_LOWER * close - math.rad(4) * look
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(CAT_LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(CAT_LID_HINGE[side], lower))
            end

            -- the ears: each swivels on its own now and then; laid back in the leap
            for _, side in { "L", "R" } do
                local sign = if side == "L" then -1 else 1
                local offset = if side == "L" then 0 else 2.6
                local swivel = math.max(0, math.sin(t * 0.7 + offset)) ^ 10
                pose(m["Ear" .. side], CFrame.Angles(-0.35 * fly - 0.12 * swivel, sign * (0.35 * swivel + 0.2 * fly), 0))
            end

            -- the tail: a slow sway along it, the tip flicking now and then; streaming in the leap; lying behind it in the sit
            for k = 1, 6 do
                local wave = math.sin(t * 1.1 - k * 0.55)
                local sway = (0.05 + 0.05 * k / 6) * wave * (1 - 0.6 * sit) * (1 - 0.5 * fly)
                local flick = if k >= 5 then 0.2 * math.max(0, math.sin(t * 2.3 + k)) ^ 8 else 0
                local rest = CAT_SIT_TAIL[k]
                pose(m["Tail" .. k], CFrame.Angles(rest[1] * sit - 0.1 * fly + 0.015 * math.sin(t * 0.8 - k * 0.6), rest[2] * sit + sway + flick, 0))
            end

            -- the pendant swings with it
            pose(m.Pendant, CFrame.Angles(0.15 * moving * math.sin(2 * s.stride) - 0.12 * fly + 0.03 * math.sin(t * 1.3), 0, 0.06 * math.sin(t * 0.9)))
        end
    end

    return { animateEclipseCat = animateEclipseCat, CAT_CORONA = CAT_CORONA, CAT_LEADS = CAT_LEADS, CAT_SOLE = CAT_SOLE, CAT_SUN = CAT_SUN }
end
