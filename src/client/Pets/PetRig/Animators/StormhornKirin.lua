-- The StormhornKirin pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep, WIND_FAR = K.PetRig, K.pose, K.smoothstep, K.WIND_FAR

    local animateStormhornKirin -- animateStormhornKirin's section below (its own locals stay in its block)
    do

        -- The Stormhorn Kirin (skinned): a proud walker on the air. A rocking canter with a real lead, its hooves throwing sparks where they land; its head carried high and low with the
        -- stride, its mane and tail on a wind only it feels, lightning flickering in the mane. It paws and tosses its head when it stands. Its joints: +X swings a limb's far end forward, and raises
        -- what points ahead. Hind legs bend the other way at the stifle (Leg2) from the hock (Leg3).
        local KIRIN_LEADS = { FL = 0, BR = 0.3, FR = math.pi, BL = math.pi + 0.3 }
        local KIRIN_LID_HINGE = { L = Vector3.new(0.4472, -0.2227, -0.8662), R = Vector3.new(0.4472, 0.2227, 0.8662) }
        local KIRIN_BLINK_UPPER, KIRIN_BLINK_LOWER = math.rad(36), math.rad(12)
        local KIRIN_MANE = { A = 0, B = 0.9, C = 1.8 }

        -- Its hoof sparks, set up on its first frame however far it is: each model's emitters start enabled,
        -- and they must throw sparks only where a hoof lands.
        local function kirinSparks(rig, s)
            s.sparks = {}
            for key in KIRIN_LEADS do
                local hoof = rig.points["Hoof" .. key]
                local sparks = hoof and hoof:FindFirstChild("Sparks")
                if sparks then
                    sparks.Enabled = false -- only where a hoof lands: hot, thrown out, falling under gravity
                    sparks.Texture = "rbxassetid://113649240058592"
                    sparks.Orientation = Enum.ParticleOrientation.VelocityParallel
                    sparks.Rotation = NumberRange.new(90)
                    sparks.Speed = NumberRange.new(2.6 * rig.unit, 5 * rig.unit)
                    sparks.SpreadAngle = Vector2.new(70, 70)
                    sparks.Acceleration = Vector3.new(0, -8 * rig.unit, 0)
                    sparks.Drag = 1.5
                    sparks.Lifetime = NumberRange.new(0.2, 0.42)
                    sparks.Size = NumberSequence.new(0.13 * rig.unit, 0.05 * rig.unit)
                    sparks.Color = ColorSequence.new(Color3.fromRGB(225, 238, 255), Color3.fromRGB(255, 190, 110))
                    s.sparks[key] = sparks
                end
            end
        end

        function animateStormhornKirin(rig, s, moving, fly, nova)
            if not s.sparks then
                kirinSparks(rig, s)
            end
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > WIND_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special: it rears, its horn raised; the forelegs come down as lightning flares through its mane
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local rear = smoothstep(0, 0.3, progress) * (1 - smoothstep(0.39, 0.46, progress))
            local slam = smoothstep(0.39, 0.46, progress) * (1 - smoothstep(0.52, 0.86, progress))

            -- now and then, standing: it paws the air and stamps, or tosses its head
            s.nextPaw = s.nextPaw or t + 5 + math.random() * 6
            local paw = 0
            if t >= s.nextPaw then
                local a = (t - s.nextPaw) / 1.9
                if a >= 1 then
                    s.nextPaw = t + 10 + math.random() * 10
                elseif pace < 0.2 and nova == 0 then
                    paw = math.sin(a * math.pi) * (0.65 + 0.35 * math.sin(a * math.pi * 6))
                    if a > 0.8 and not s.stamped then
                        s.stamped = true
                        s.flickerUntil = t + 0.3
                        local sparks = s.sparks and s.sparks.FR
                        if sparks then
                            sparks:Emit(7)
                        end
                    end
                end
            else
                s.stamped = false
            end
            s.nextToss = s.nextToss or t + 8 + math.random() * 8
            local toss = 0
            if t >= s.nextToss then
                local a = (t - s.nextToss) / 1.1
                if a >= 1 then
                    s.nextToss = t + 9 + math.random() * 9
                elseif pace < 0.3 and nova == 0 then
                    toss = math.sin(a * math.pi) * math.sin(a * math.pi * 2.5)
                end
            end

            -- the stride
            s.stride = (s.stride or 0) + dt * (10.5 * moving + 4.5 * fly)
            local stride = s.stride
            local rock = math.sin(stride + 0.6)
            local tuck = math.sin(math.min(fly, 1) * math.pi / 2)
            for key, lead in KIRIN_LEADS do
                local phase = stride + lead
                local a, lift = math.sin(phase), math.max(0, math.cos(phase)) ^ 1.2
                local landing = math.cos(phase)
                if moving > 0.5 and (s.lastLanding and s.lastLanding[key] or 0) > 0 and landing <= 0 and s.sparks[key] then
                    s.sparks[key]:Emit(3)
                end
                s.lastLanding = s.lastLanding or {}
                s.lastLanding[key] = landing
                local sideSign = if string.sub(key, 2, 2) == "L" then 1 else -1
                local idle = 0.018 * math.sin(t * 0.8 + lead)
                local p1, p2, p3, p4
                if string.sub(key, 1, 1) == "F" then
                    p1 = idle + moving * (0.52 * a + 0.05) + tuck * (0.72 + 0.14 * a) * (1 - moving) + rear * (if sideSign > 0 then 0.78 + 0.22 * math.sin(t * 11) else 0.36 - 0.22 * math.sin(t * 11)) + slam * 0.2
                    p2 = moving * 0.08 + tuck * 0.18 + rear * 0.16
                    p3 = -moving * (1.3 * lift + 0.08) - tuck * 1.45 - rear * (if sideSign > 0 then 1.55 else 1.1) - slam * 0.1
                    p4 = -moving * (0.5 * lift + 0.08) - tuck * 0.62 - rear * 0.6
                    if key == "FR" then
                        p1 += 0.62 * paw
                        p3 -= 1.25 * paw
                        p4 -= 0.55 * paw
                    end
                else
                    p1 = idle + moving * (0.44 * a - 0.08) + tuck * (-0.5 + 0.12 * a) * (1 - moving) - rear * 0.8 - slam * 0.12
                    p2 = moving * 0.64 * lift + tuck * 0.2 + rear * 0.12
                    p3 = -moving * (0.95 * lift + 0.06) - tuck * 0.32 - rear * 0.16
                    p4 = -moving * 0.46 * lift - tuck * 0.32 + rear * 0.14
                end
                pose(m["Leg" .. key .. "1"], CFrame.Angles(p1, 0, 0))
                pose(m["Leg" .. key .. "2"], CFrame.Angles(p2, 0, 0))
                pose(m["Leg" .. key .. "3"], CFrame.Angles(p3, 0, 0))
                pose(m["Hoof" .. key], CFrame.Angles(p4, 0, 0))
            end

            -- it leans into turns
            local look = rig.rootPart.CFrame.LookVector
            local heading = math.atan2(-look.X, -look.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.12, -0.28, 0.28) - (s.bank or 0)) * math.min(1, dt * 3)

            local hover = 0.1 + 0.012 * math.sin(t * 1.5) + moving * 0.034 * math.sin(2 * stride + 0.4) + 0.05 * fly + 0.015 * math.sin(t * 2.1) * fly + 0.2 * rear
            pose(m.Body, CFrame.new(0, hover * u, 0) * CFrame.Angles(0.006 * math.sin(t * 1.5) + moving * (0.045 * rock - 0.02) + 0.13 * fly + 0.84 * rear - 0.1 * slam, 0.02 * math.sin(t * 0.31), s.bank))
            pose(m.Hips, CFrame.Angles(-moving * 0.06 * math.sin(stride + 1.7) + 0.05 * tuck, 0.03 * math.sin(t * 0.5) * (1 - pace), 0))
            pose(m.Chest, CFrame.Angles(moving * 0.03 * math.sin(stride - 0.4), 0, 0.012 * math.sin(t * 0.8)))

            -- head and neck: its gaze wanders, its head follows slowly; low and reaching at speed
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 1.6 + math.random() * 3.2
                s.gazeTo = (math.random() - 0.5) * 0.7
            end
            local calm = (1 - pace * 0.75) * (1 - nova)
            s.gaze = (s.gaze or 0) + ((s.gazeTo or 0) * calm - (s.gaze or 0)) * math.min(1, dt * 2.2)
            local nod = moving * 0.055 * math.sin(2 * stride - 0.5)
            pose(m.Neck1, CFrame.Angles(0.012 * math.sin(t * 1.5 - 0.5) - 0.2 * moving - 0.05 * fly - 0.24 * rear + 0.14 * slam + 0.05 * toss - 0.1 * paw, s.gaze * 0.28, s.bank * 0.5))
            pose(m.Neck2, CFrame.Angles(0.012 * math.sin(t * 1.5 - 1) - 0.1 * moving - 0.17 * rear - 0.34 * slam + 0.08 * toss - 0.07 * paw + nod, s.gaze * 0.36, 0))
            pose(m.Head, CFrame.Angles(0.012 * math.sin(t * 1.5 - 1.5) + 0.22 * moving + 0.08 * fly + 0.4 * rear + 0.06 * slam - 0.2 * toss + 0.12 * paw - nod * 0.6, s.gaze * 0.5, 0.05 * math.sin(t * 0.37) * calm))
            pose(m.Jaw, CFrame.Angles(-(0.16 * rear + 0.24 * slam + 0.1 * math.max(0, toss)), 0, 0))

            -- the eye: blinks slowly, turns ahead of the head; a sterner lid when it runs
            s.nextBlink = s.nextBlink or t + 2
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.2
                if a >= 1 then
                    s.nextBlink = t + (if math.random() < 0.15 then 0.14 else 2.8 + math.random() * 4)
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local rest = math.rad(4 + 7 * pace - 6 * rear)
            local upper = rest + (KIRIN_BLINK_UPPER - rest) * math.max(blink, slam * 0.25)
            local lower = KIRIN_BLINK_LOWER * blink
            for _, side in { "L", "R" } do
                pose(m["Eye" .. side], CFrame.Angles(0, s.gaze * 0.6, 0))
                pose(m["LidU" .. side], CFrame.fromAxisAngle(KIRIN_LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(KIRIN_LID_HINGE[side], lower))
            end

            -- ears flick; the frills at its jaw trail
            for _, side in { "L", "R" } do
                local sign = if side == "L" then -1 else 1
                local offset = if side == "L" then 0 else 2.2
                local flick = math.max(0, math.sin(t * 0.9 + offset)) ^ 16
                pose(m["Ear" .. side], CFrame.Angles(-0.14 * pace - 0.3 * rear + 0.4 * flick * (1 - pace), sign * 0.12 * flick, 0))
                pose(m["Frill" .. side], CFrame.Angles(0.07 * math.sin(t * 2.4 + offset) - 0.16 * pace, sign * (0.05 * math.sin(t * 1.5 + offset) - 0.1 * pace), 0))
            end

            -- the mane on its wind: heavier at rest, streaming out as it runs, lifting up and back as it rears
            local gust = 0.5 + 0.5 * math.sin(t * 0.47)
            local waveSpeed = 2.1 + 4.2 * pace
            for cluster, phase in KIRIN_MANE do
                local base = 0.16 * (1 - pace) + 0.2 * moving - 0.12 * fly - 0.36 * rear + 0.2 * slam -- (a neck reaching forward would throw it straight up)
                local wave = (0.06 + 0.05 * gust + 0.07 * pace)
                pose(m["Mane" .. cluster .. "1"], CFrame.Angles(base + wave * math.sin(t * waveSpeed - phase), 0.05 * math.sin(t * 1.3 - phase), 0))
                pose(m["Mane" .. cluster .. "2"], CFrame.Angles(base * 0.8 + 1.5 * wave * math.sin(t * waveSpeed - phase - 1.1), 0.09 * math.sin(t * 1.3 - phase - 1), 0))
            end

            -- the tail: a slow swish at rest, a long wave at speed; it clamps down as it rears
            local droop = 0.045 * (1 - pace) - 0.02 * fly + 0.1 * rear
            for k = 1, 6 do
                local f = k / 6
                pose(m["Tail" .. k], CFrame.Angles(droop + (0.025 + 0.05 * pace) * math.sin(t * (1.7 + 3 * pace) - k * 0.65),
                    (0.03 + 0.05 * f) * (1 + 0.5 * pace) * math.sin(t * (1.05 + 1.6 * pace) - k * 0.55), 0))
            end
            pose(m.TailTip, CFrame.Angles(0, 0.1 * math.sin(t * 2.4), 0))

            -- lightning flickers in the mane: a few quick stutters every so often, oftener at speed, without pause during its special
            s.nextFlicker = s.nextFlicker or t + 1
            if t >= s.nextFlicker then
                s.flickerUntil = t + 0.16 + math.random() * 0.22
                s.nextFlicker = t + (1.1 + 2.6 * math.random()) * (1 - 0.6 * pace)
            end
            local bolts = rig.parts.Bolts
            if bolts then
                local lit = nova > 0.3 or (t < (s.flickerUntil or 0) and math.sin(t * 73) > -0.35)
                bolts.Transparency = if lit then 0 else 1
            end
        end
    end

    return { animateStormhornKirin = animateStormhornKirin }
end
