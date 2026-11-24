-- The VoidscaleHydra pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep, dropToGround = K.PetRig, K.pose, K.smoothstep, K.dropToGround

    local animateVoidscaleHydra, HYDRA_LIGHT -- animateVoidscaleHydra's section below (its own locals stay in its block)
    do

        -- The Voidscale Hydra (skinned): a low sprawling reptile with three necks, the middle one forking into two young heads. It walks like a monitor
        -- lizard, legs swinging out in diagonal pairs, its body swaying side to side and its tail following the wave. Each neck sways on its own and each head
        -- chooses its own gaze; the tongues of light flick out, each in its own time; now and then the two young heads turn on each other and hiss.
        local HYDRA_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        local HYDRA_SOLE = 0.2621 -- metres from the middle of its box down to its claws: it walks on the ground
        HYDRA_LIGHT = Color3.fromRGB(70, 150, 255)
        local HYDRA_HEADS = { -- each head's forward line in the model's axes, how far its tongue reaches (metres), its neck and the bones that carry it
            L = { dir = Vector3.new(-0.2067, -0.0316, -0.9779), reach = 0.084, neck = { "NeckL1", "NeckL2", "NeckL3", "NeckL4" }, phase = 0 },
            R = { dir = Vector3.new(0.1787, -0.0936, -0.9794), reach = 0.084, neck = { "NeckR1", "NeckR2", "NeckR3", "NeckR4" }, phase = 2.1 },
            ML = { dir = Vector3.new(-0.2186, -0.0094, -0.9758), reach = 0.0538, neck = { "ForkL1", "ForkL2" }, phase = 4.0 },
            MR = { dir = Vector3.new(0.1998, -0.1263, -0.9717), reach = 0.0538, neck = { "ForkR1", "ForkR2" }, phase = 5.3 },
        }
        local HYDRA_LEGS = { FL = 0, BR = 0, FR = math.pi, BL = math.pi } -- diagonal pairs swing together

        function animateVoidscaleHydra(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > HYDRA_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, HYDRA_SOLE)

            -- the special, The Void Between: the necks rise and draw back as a rift tears open in the air before it; at the burst all four heads strike into
            -- it, tongues out; they hold, then draw back as it closes
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local rear = smoothstep(0.04, 0.34, progress) * (1 - smoothstep(0.38, 0.43, progress))
            local strike = smoothstep(0.38, 0.43, progress) * (1 - smoothstep(0.55, 0.85, progress))

            -- now and then the two young heads squabble: they turn on each other, hiss with their tongues out, shake, and turn away
            s.nextSquabble = s.nextSquabble or t + 8 + math.random() * 8
            local squabble = 0
            if t >= s.nextSquabble then
                local a = (t - s.nextSquabble) / 2.2
                if a >= 1 then
                    s.nextSquabble = t + 14 + math.random() * 12
                elseif pace < 0.3 and nova == 0 then
                    squabble = smoothstep(0, 0.2, a) * (1 - smoothstep(0.75, 1, a))
                else
                    s.nextSquabble = t + 4
                end
            end

            -- the walk: legs out in diagonal pairs, the body swaying, the tail following
            s.stride = (s.stride or 0) + dt * (2.2 + 7.5 * moving + 2 * fly) * (if pace > 0.05 then 1 else 0.15)
            local stride = s.stride
            local sway = 0.13 * moving * math.sin(stride)
            local breath = math.sin(t * 1.3)
            pose(m.Body, CFrame.new(0, 0.005 * breath * u - drop + 0.03 * rear * u, (0.05 * rear - 0.07 * strike) * u) * CFrame.Angles(0.03 * rear - 0.03 * strike + 0.01 * breath, sway, 0.03 * moving * math.sin(stride)))
            pose(m.Chest, CFrame.Angles(0.12 * rear - 0.08 * strike, -0.6 * sway, 0))
            pose(m.Hips, CFrame.Angles(0, -0.7 * sway, 0))
            for k = 1, 5 do
                pose(m["Tail" .. k], CFrame.Angles(0.02 * math.sin(t * 0.7 - k * 0.5), (0.05 + 0.12 * moving) * math.sin(stride - 0.9 - k * 0.6) + 0.04 * math.sin(t * 0.5 - k * 0.4) * (1 - moving), 0))
            end
            for leg, lead in HYDRA_LEGS do
                local front, side = string.sub(leg, 1, 1), string.sub(leg, 2, 2)
                local phase = stride + lead
                local swing = 0.42 * moving * math.sin(phase) * (if front == "F" then 1 else -1)
                local lift = 0.32 * moving * math.max(0, math.cos(phase))
                local up = if side == "L" then -lift else lift -- a leg out to its left rises with a negative turn about Z
                pose(m["Upper" .. front .. side], CFrame.Angles(0, swing, up + (if side == "L" then 0.3 else -0.3) * fly))
                pose(m["Lower" .. front .. side], CFrame.Angles(0, 0, (if side == "L" then 0.5 else -0.5) * lift))
                pose(m["Foot" .. front .. side], CFrame.Angles(0, -0.5 * swing, (if side == "L" then -0.3 else 0.3) * lift))
            end

            -- the necks and heads: each its own sway and its own gaze
            s.gaze = s.gaze or {}
            s.tongue = s.tongue or {}
            for key, head in HYDRA_HEADS do
                local g = s.gaze[key]
                if not g or t >= g.next then
                    g = { next = t + 1.6 + math.random() * 3, yaw = (math.random() - 0.5) * 0.9, pitch = (math.random() - 0.5) * 0.35, cy = g and g.cy or 0, cp = g and g.cp or 0 }
                    s.gaze[key] = g
                end
                local young = key == "ML" or key == "MR"
                local toward = if key == "ML" then -1 elseif key == "MR" then 1 else 0 -- the young heads turn on each other
                local wantYaw = g.yaw * (1 - rear) * (1 - strike) + (if young then toward * 0.55 * squabble else 0)
                local wantPitch = g.pitch * (1 - rear) * (1 - strike) + (if young then 0.15 * squabble else 0)
                g.cy += (wantYaw - g.cy) * math.min(1, dt * 3)
                g.cp += (wantPitch - g.cp) * math.min(1, dt * 3)
                local n = #head.neck
                for i, name in head.neck do
                    local share = i / n
                    local idle = 0.05 * math.sin(t * 0.8 + head.phase + i * 0.5) * (1 - 0.5 * pace)
                    local yawTo = if young then toward * 0.25 * squabble * share else 0
                    pose(m[name], CFrame.Angles(0.18 * rear / n * (if i == 1 then 2 else 1) - 0.12 * strike * (if i == 1 then 1.5 else -0.6) + 0.04 * idle,
                        idle + yawTo + g.cy * 0.25 / n, 0))
                end
                local shake = if young then 0.12 * squabble * math.sin(t * 34 + head.phase) else 0
                pose(m["Head" .. key], CFrame.Angles(g.cp + 0.1 * rear - 0.25 * strike, g.cy * 0.75 + shake, 0))

                -- its tongue flicks: out and in twice, quickly, every few seconds; out and held in the special and the squabble
                local tg = s.tongue[key]
                if not tg or t >= tg.next then
                    tg = { at = t, next = t + 2 + math.random() * 3.5 }
                    s.tongue[key] = tg
                end
                local a = (t - tg.at) / 0.5
                local flick = if a < 1 then math.max(0, math.sin(a * 2 * math.pi)) else 0
                local out = math.max(flick, strike, if young then squabble else 0)
                pose(m["Tongue" .. key], CFrame.new(head.dir * (head.reach * out * u)))
            end

            -- the eyes and tongues brighten as it strikes
            local light = HYDRA_LIGHT:Lerp(Color3.fromRGB(190, 225, 255), 0.5 * strike)
            for _, key in { "LightL", "LightR", "LightML", "LightMR" } do
                local part = rig.parts[key]
                if part then
                    part.Color = light
                end
            end
        end
    end

    return { animateVoidscaleHydra = animateVoidscaleHydra, HYDRA_LIGHT = HYDRA_LIGHT }
end
