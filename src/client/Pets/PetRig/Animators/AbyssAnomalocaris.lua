-- The AbyssAnomalocaris pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep = K.PetRig, K.pose, K.smoothstep

    local animateAbyssAnomalocaris, ANOMALO_GLOW, ANOMALO_RING -- animateAbyssAnomalocaris's section below (its own locals stay in its block)
    do

        -- The Abyss Anomalocaris (skinned): a hunter from the first sea that still swims through the air. A wave runs back along its nine pairs of flaps, each a
        -- little behind the one before (the flaps are weighted by their place along the body, so where two overlap they move as one); its trunk undulates
        -- with it, its tail fan steers, and it banks into its turns. Its great arms rest curled under its head, tucking in at speed and now and then
        -- flexing open and shut as if tasting the water; its eyes swivel on their short stalks. Left is -X: a left flap rises with a negative turn about Z.
        local ANOMALO_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        local ANOMALO_FLAPS = 9
        local ANOMALO_TRUNK = { "Seg4", "Seg5", "Seg6", "Seg7", "Seg8", "Seg9", "Tail" }
        ANOMALO_GLOW = Color3.fromRGB(190, 36, 146) -- deep: as Neon it blooms, and a paler magenta read as a bright pink fringe
        ANOMALO_RING = "rbxassetid://12403112662" -- a thin glowing ring with brighter arcs (also RealmAura's)

        function animateAbyssAnomalocaris(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > ANOMALO_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special, The First Hunt: the arms open wide as it draws back; it lunges, and the arms snap shut on the burst (PetRig.NOVA_BURST); it holds
            -- them shut a moment, flaps beating hard, then settles
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local open = smoothstep(0.04, 0.3, progress) * (1 - smoothstep(0.39, 0.43, progress))
            local draw = smoothstep(0.1, 0.36, progress) * (1 - smoothstep(0.37, 0.42, progress))
            local lunge = smoothstep(0.37, 0.42, progress) * (1 - smoothstep(0.5, 0.82, progress))
            local snap = smoothstep(0.4, 0.43, progress) * (1 - smoothstep(0.62, 0.9, progress))

            -- it banks into its turns
            local look = rig.rootPart.CFrame.LookVector
            local heading = math.atan2(-look.X, -look.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.25, -0.45, 0.45) - (s.bank or 0)) * math.min(1, dt * 3)

            -- now and then, still, it flexes its arms open and shut, twice, as if tasting the water
            s.nextFlex = s.nextFlex or t + 7 + math.random() * 7
            local flex = 0
            if t >= s.nextFlex then
                local a = (t - s.nextFlex) / 2.4
                if a >= 1 then
                    s.nextFlex = t + 12 + math.random() * 12
                elseif pace < 0.25 and nova == 0 then
                    flex = math.sin(math.pi * a) * (0.5 + 0.5 * math.sin(a * math.pi * 4 - math.pi / 2))
                else
                    s.nextFlex = t + 4
                end
            end

            s.swim = (s.swim or 0) + dt * (2.3 + 2.6 * pace + 3.2 * lunge)
            local swim = s.swim
            local hover = 0.022 * math.sin(t * 0.9) + 0.008 * math.sin(swim) + 0.04 * fly
            pose(m.Body, CFrame.new(0, hover * u, (0.1 * draw - 0.2 * lunge) * u)
                * CFrame.Angles(0.012 * math.sin(swim * 0.5 + 0.6) - 0.08 * pace + 0.12 * draw - 0.1 * lunge, 0, s.bank))

            -- the trunk: a slow wave back along it, stronger at speed; the tail swings out of the turn
            local sway = 0.03 + 0.045 * pace + 0.04 * lunge
            for i, name in ANOMALO_TRUNK do
                pose(m[name], CFrame.Angles(0.012 * math.sin(swim * 0.5 - i * 0.6), sway * math.sin(swim * 0.5 - i * 0.55) - s.bank * 0.06, 0))
            end
            pose(m.Seg2, CFrame.Angles(0, -0.4 * sway * math.sin(swim * 0.5 + 0.5), 0))
            pose(m.Seg1, CFrame.Angles(0.04 * draw, -0.3 * sway * math.sin(swim * 0.5 + 1), 0))
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2 + math.random() * 3
                s.gazeTo = (math.random() - 0.5) * 0.7
                s.nodTo = (math.random() - 0.5) * 0.1
            end
            local calm = (1 - 0.6 * pace) * (1 - open)
            s.gaze = (s.gaze or 0) + ((s.gazeTo or 0) * calm - (s.gaze or 0)) * math.min(1, dt * 2.5)
            s.nod = (s.nod or 0) + ((s.nodTo or 0) * calm - (s.nod or 0)) * math.min(1, dt * 2.5)
            pose(m.Head, CFrame.Angles(s.nod + 0.06 * draw - 0.08 * lunge, s.gaze * 0.25, 0))

            -- the flaps: the wave, each flap 0.42 rad behind the one in front
            local amp = (0.15 + 0.1 * pace + 0.14 * lunge) * (1 - 0.4 * open)
            for k = 1, ANOMALO_FLAPS do
                local a = amp * math.sin(swim - (k - 1) * 0.42) + 0.03 * fly
                pose(m["FlapL" .. k], CFrame.Angles(0, 0, -a))
                pose(m["FlapR" .. k], CFrame.Angles(0, 0, a))
            end

            -- the tail fan steers: raised as it climbs, the V opening when it lunges
            pose(m.Tail, CFrame.Angles(-0.05 * pace + 0.12 * draw - 0.08 * lunge + 0.02 * math.sin(swim * 0.5 - 4.5), -s.bank * 0.35 + sway * math.sin(swim * 0.5 - 4.4), 0))
            for j = 1, 3 do
                local beat = 0.06 * math.sin(swim * 0.5 - 4.6 - j * 0.3)
                local spread = 0.12 * lunge + 0.03 * pace
                pose(m["FanL" .. j], CFrame.Angles(beat, 0, -spread))
                pose(m["FanR" .. j], CFrame.Angles(beat, 0, spread))
            end

            -- the arms: curled at rest, breathing; tucked tighter at speed; opened wide for the hunt, then snapped shut on it
            local curl = 0.06 * math.sin(t * 0.8) + 0.25 * pace - 1.0 * open + 0.55 * snap - 0.55 * flex
            local spread = 0.24 * open + 0.06 * flex - 0.04 * snap
            for i = 1, 6 do
                local bend = -curl * (0.12 + 0.09 * (i - 1))
                local reach = if i == 1 then 0.25 * lunge + 0.1 * open else 0
                pose(m["ArmL" .. i], CFrame.Angles(bend + reach, if i == 1 then spread else 0, 0))
                pose(m["ArmR" .. i], CFrame.Angles(bend + reach, if i == 1 then -spread else 0, 0))
            end

            -- the eyes swivel on their stalks; on the hunt both swing forward onto the prey
            local focus = math.max(open, 0.6 * lunge)
            pose(m.StalkL, CFrame.Angles(0, s.gaze * 0.5 + 0.08 * math.sin(t * 0.7) - 0.4 * focus, -0.06 * math.sin(t * 0.9 + 1)))
            pose(m.StalkR, CFrame.Angles(0, s.gaze * 0.5 + 0.08 * math.sin(t * 0.7 + 2) + 0.4 * focus, 0.06 * math.sin(t * 0.9 + 2.5)))
            pose(m.EyeL, CFrame.Angles(0, 0.1 * math.sin(t * 0.5), 0))
            pose(m.EyeR, CFrame.Angles(0, 0.1 * math.sin(t * 0.5 + 1.3), 0))

            -- the edges' light breathes with the wave; on the snap it flares
            local shine = 0.08 * (0.5 + 0.5 * math.sin(swim * 0.5)) + 0.55 * snap
            local colour = ANOMALO_GLOW:Lerp(Color3.fromRGB(240, 120, 205), shine)
            for _, key in { "EdgesL", "EdgesR" } do
                local edge = rig.parts[key]
                if edge then
                    edge.Color = colour
                end
            end
        end
    end

    return { animateAbyssAnomalocaris = animateAbyssAnomalocaris, ANOMALO_GLOW = ANOMALO_GLOW, ANOMALO_RING = ANOMALO_RING }
end
