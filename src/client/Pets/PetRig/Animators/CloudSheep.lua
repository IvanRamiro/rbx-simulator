-- The CloudSheep pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep = K.PetRig, K.pose, K.smoothstep

    local animateCloudSheep -- animateCloudSheep's section below (its own locals stay in its block)
    do


        -- The Cloud Sheep (skinned): always half asleep, its hooves paddling at the air. It breathes with its whole fleece, its lobes on their own bones; its head sinks as it nods off and comes up with a
        -- start; it yawns. +X swings a limb's far end forward.
        local SHEEP_LEADS = { FL = 0, BR = 0.4, FR = math.pi, BL = math.pi + 0.4 }
        local SHEEP_LID_HINGE = { L = Vector3.new(0.7476, 0.1035, -0.6561), R = Vector3.new(0.7476, -0.1035, 0.6561) }
        local SHEEP_WOOL = { WoolTop = Vector3.new(0, 1, 0), WoolBack = Vector3.new(0, 0.1, 1), WoolChest = Vector3.new(0, 0.3, -1), WoolL = Vector3.new(-1, 0.1, 0), WoolR = Vector3.new(1, 0.1, 0) }

        function animateCloudSheep(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > 90 then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special: it tucks its legs and draws in a huge breath, swelling, then lets it all go in one long sigh
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local inhale = smoothstep(0, 0.38, progress) * (1 - smoothstep(0.42, 0.56, progress))
            local sigh = smoothstep(0.41, 0.47, progress) * (1 - smoothstep(0.66, 0.95, progress))

            -- nodding off: its head sinks over seconds, its eyes close, and then it starts awake
            s.nextNod = s.nextNod or t + 4 + math.random() * 5
            local nod, startle = 0, 0
            if t >= s.nextNod then
                local a = t - s.nextNod
                if a > 4 then
                    s.nextNod = t + 7 + math.random() * 8
                elseif pace < 0.25 and nova == 0 then
                    nod = smoothstep(0, 3.1, a) * (1 - smoothstep(3.1, 3.28, a))
                    startle = smoothstep(3.08, 3.2, a) * (1 - smoothstep(3.2, 4, a))
                else
                    s.nextNod = t + 3
                end
            end
            s.nextYawn = s.nextYawn or t + 10 + math.random() * 8
            local yawn = 0
            if t >= s.nextYawn then
                local a = (t - s.nextYawn) / 2.6
                if a >= 1 then
                    s.nextYawn = t + 13 + math.random() * 12
                elseif nod == 0 and pace < 0.4 and nova == 0 then
                    yawn = smoothstep(0, 0.34, a) * (1 - smoothstep(0.66, 1, a))
                end
            end

            -- its breath, in the whole fleece: slow, and the lobes never quite together
            local breath = math.sin(t * 1.15)
            local index = 0
            for name, out in SHEEP_WOOL do
                index += 1
                local amount = 0.011 * (breath + 0.3 * math.sin(t * 0.7 + index * 1.7)) + 0.012 * yawn + 0.09 * inhale - 0.03 * sigh
                local back = Vector3.new(0, 0, 0.022 * pace * (if name == "WoolBack" then 1.5 else 0.6))
                local at = (out * amount + back) * u
                pose(m[name], CFrame.new(at.X, at.Y, at.Z))
            end
            pose(m.WoolCap, CFrame.new(0, (0.006 * breath + 0.03 * inhale) * u, 0))

            local hover = 0.015 * math.sin(t * 0.95) + 0.02 * fly + 0.2 * inhale + 0.08 * sigh
            pose(m.Body, CFrame.new(0, hover * u, 0) * CFrame.Angles(0.02 * math.sin(t * 0.95 - 0.8) - 0.09 * moving - 0.16 * fly + 0.14 * inhale - 0.1 * sigh, 0.03 * math.sin(t * 0.31), 0.03 * math.sin(t * 0.53)))

            -- the head hangs low; it sinks to sleep; it looks slowly about
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 3 + math.random() * 5
                s.gazeTo = (math.random() - 0.5) * 0.6
            end
            s.gaze = (s.gaze or 0) + ((s.gazeTo or 0) * (1 - nod) * (1 - nova) - (s.gaze or 0)) * math.min(1, dt * 1.2)
            pose(m.Head, CFrame.new(0, 0, (0.02 * moving) * u) * CFrame.Angles(0.012 * math.sin(t * 1.15 - 0.6) - 0.48 * nod + 0.2 * startle + 0.26 * yawn + 0.1 * moving + 0.2 * inhale - 0.04 * sigh, s.gaze, 0.1 * nod))

            -- half asleep: the lids rest low, and close as it nods off
            s.nextBlink = s.nextBlink or t + 2
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.34
                if a >= 1 then
                    s.nextBlink = t + 2.5 + math.random() * 4
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local shut = math.max(blink, nod, yawn, sigh * 0.9, inhale * 0.7) * (1 - startle)
            local wide = math.rad(14) * startle
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(SHEEP_LID_HINGE[side], -math.rad(26) * shut + wide))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(SHEEP_LID_HINGE[side], math.rad(14) * shut))
                pose(m["Eye" .. side], CFrame.Angles(0, s.gaze * 0.5, 0))
                local sign = if side == "L" then -1 else 1
                local offset = if side == "L" then 0 else 1.9
                local flick = math.max(0, math.sin(t * 0.8 + offset)) ^ 18
                pose(m["Ear" .. side], CFrame.Angles(0.06 * math.sin(t * 1.15 + offset) - 0.34 * nod + 0.34 * startle + 0.3 * flick - 0.34 * pace, 0, sign * 0.06 * math.sin(t * 0.7 + offset)))
            end
            local open = math.max(yawn, sigh * 0.85)
            pose(m.Smile, CFrame.new(0, 0, 0.03 * open * u))
            pose(m.Mouth, CFrame.new(0, 0.006 * open * u, -0.03 * open * u))

            -- it paddles, slowly, even asleep: swimming on the air
            s.stride = (s.stride or 0) + dt * (1.5 - 0.8 * nod + 7 * moving + 3 * fly)
            local tuck = math.max(inhale, sigh * 0.7, fly * 0.55)
            local reach = (0.2 + 0.32 * pace) * (1 - tuck)
            for key, lead in SHEEP_LEADS do
                local phase = s.stride + lead
                local a, lift = math.sin(phase), math.max(0, math.cos(phase))
                if string.sub(key, 1, 1) == "F" then
                    pose(m["Leg" .. key .. "1"], CFrame.Angles(reach * a + 1.0 * tuck, 0, 0))
                    pose(m["Leg" .. key .. "2"], CFrame.Angles(-(0.26 + 0.7 * pace) * lift * (1 - tuck) - 1.6 * tuck, 0, 0))
                    pose(m["Hoof" .. key], CFrame.Angles(-0.34 * lift - 0.6 * tuck, 0, 0))
                else
                    pose(m["Leg" .. key .. "1"], CFrame.Angles(reach * a - 0.95 * tuck, 0, 0))
                    pose(m["Leg" .. key .. "2"], CFrame.Angles((0.24 + 0.6 * pace) * lift * (1 - tuck) + 1.5 * tuck, 0, 0))
                    pose(m["Hoof" .. key], CFrame.Angles(-0.3 * lift - 0.45 * tuck, 0, 0))
                end
            end

            pose(m.Tail, CFrame.Angles(0.08 * math.sin(t * 1.15 + 0.5) - 0.2 * pace, 0.16 * math.sin(t * 1.9) + 0.3 * math.max(0, math.sin(t * 0.37)) ^ 10 * math.sin(t * 11), 0))
        end
    end

    return { animateCloudSheep = animateCloudSheep }
end
