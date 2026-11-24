-- The DreamMoth pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Debris, pose, smoothstep = K.PetRig, K.Debris, K.pose, K.smoothstep

    local animateDreamMoth, mothThreads -- animateDreamMoth's section below (its own locals stay in its block)
    do

        -- The Dream Moth (skinned): it flutters, never still, drifting a little off its line as a moth does; now and then it fans its wings slowly, or uncurls its tongue to taste the air. Its eyes are compound eyes with no lids:
        -- what moves in them is the pseudopupil, the dark spot a real insect's eye seems to turn on you. Here it really does: each one turns, on the eye's centre, toward whoever is looking.
        local MOTH_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        local MOTH_REST = { L = Vector3.new(-0.3862, 0.0736, -0.9195), R = Vector3.new(0.3862, 0.0736, -0.9195) } -- where each pseudopupil points at rest, in the head's axes
        local MOTH_PUPIL_TURN = 0.45 -- radians it may turn from there
        local MOTH_PUPIL_SHARE = 0.55 -- and only this share of the way to the camera: each eye is half sunk in the head, so what shows of it lies outward of its centre, and a pupil turned all the way sits at the inner edge of what you see (cross-eyed)
        -- how far each stretch of the coiled tongue turns: unrolling it undoes these (from tools/blender/pets/dream_moth.py, its BENDS)
        local MOTH_BENDS = { 0.2938, 0.3333, 0.3963, 0.4776, 0.5747, 0.6861, 0.8106, 0.9473, 1.0956, 1.2549, 1.4247 }
        local MOTH_THREADS = 5
        local MOTH_THREAD_FROM, MOTH_THREAD_TO = 0.06, 0.42 -- of the special: the dream's threads drift in, and reach its tongue at the burst
        local MOTH_COLOURS = { Color3.fromRGB(255, 200, 236), Color3.fromRGB(214, 180, 255), Color3.fromRGB(176, 214, 255), Color3.fromRGB(255, 226, 200), Color3.fromRGB(236, 200, 255) }

        -- The faint threads of a dream nobody remembers, spiralling in to its tongue
        function mothThreads(rig, s)
            local metre = rig.meters
            s.mothThreads = {}
            local folder = rig.model.Parent or workspace
            for k = 1, MOTH_THREADS do
                local holder = Instance.new("Part")
                holder.Name = "DreamThread"
                holder.Anchored = true
                holder.CanCollide = false
                holder.CanTouch = false
                holder.CanQuery = false
                holder.CastShadow = false
                holder.Transparency = 1
                holder.Size = Vector3.one * 0.05
                local a, b = Instance.new("Attachment"), Instance.new("Attachment")
                a.Position, b.Position = Vector3.new(0, 0.018 * metre, 0), Vector3.new(0, -0.018 * metre, 0)
                a.Parent, b.Parent = holder, holder
                local trail = Instance.new("Trail")
                trail.Attachment0, trail.Attachment1 = a, b
                trail.FaceCamera = true
                trail.Lifetime = 0.55
                trail.LightEmission = 0.4
                trail.LightInfluence = 0
                trail.WidthScale = NumberSequence.new(1, 0)
                local colour = MOTH_COLOURS[k]
                trail.Color = ColorSequence.new(colour, colour:Lerp(Color3.new(1, 1, 1), 0.35))
                trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(1, 1) })
                trail.Parent = holder
                holder.Parent = folder
                Debris:AddItem(holder, PetRig.NOVA_TIME)
                table.insert(s.mothThreads, { part = holder, angle = (k / MOTH_THREADS) * 2 * math.pi + math.random() * 0.6, rise = (math.random() - 0.5) * 0.9, reach = (0.75 + 0.35 * math.random()) * metre })
            end
        end

        function animateDreamMoth(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > MOTH_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special: its tongue uncurls; threads of a forgotten dream drift in, spiralling, to the tip of it; then one slow, great wingbeat, and its tongue curls back up
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local sipping = smoothstep(0, 0.22, progress) * (1 - smoothstep(0.56, 0.8, progress))
            local lift = smoothstep(0.3, 0.42, progress) * (1 - smoothstep(0.44, 0.52, progress))
            local stroke = smoothstep(0.44, 0.52, progress) * (1 - smoothstep(0.56, 0.78, progress))
            local stillness = smoothstep(0.08, 0.3, progress) * (1 - smoothstep(0.42, 0.5, progress))
            -- (only before they reach its tongue: seen first after that, the burst has gone and nothing would take them away)
            if rig.nova and progress >= MOTH_THREAD_FROM and progress < MOTH_THREAD_TO and not rig.nova.threaded then
                rig.nova.threaded = true
                mothThreads(rig, s)
            end
            local tip = rig.points.Tongue12
            if s.mothThreads and tip then
                local q = math.clamp((progress - MOTH_THREAD_FROM) / (MOTH_THREAD_TO - MOTH_THREAD_FROM), 0, 1)
                local at = tip.TransformedWorldCFrame.Position
                local facing = rig.rootPart.CFrame
                for _, thread in s.mothThreads do
                    if thread.part.Parent then
                        local away = thread.reach * (1 - q) ^ 1.3
                        local angle = thread.angle + q * 1.6 * math.pi -- (slow enough that the trail stays a curve, not a zigzag)
                        local offset = facing:VectorToWorldSpace(Vector3.new(math.cos(angle) * away, thread.rise * away, math.sin(angle) * away))
                        thread.part.CFrame = CFrame.new(at + offset)
                    end
                end
            end

            -- now and then it fans its wings slowly, and now and then it tastes the air
            s.nextFan = s.nextFan or t + 6 + math.random() * 6
            local fanning = 0
            if t >= s.nextFan then
                local a = (t - s.nextFan) / 3.4
                if a >= 1 then
                    s.nextFan = t + 12 + math.random() * 10
                elseif pace < 0.3 and nova == 0 then
                    fanning = smoothstep(0, 0.15, a) * (1 - smoothstep(0.85, 1, a))
                else
                    s.nextFan = t + 3
                end
            end
            s.nextTaste = s.nextTaste or t + 10 + math.random() * 8
            local taste = 0
            if t >= s.nextTaste then
                local a = (t - s.nextTaste) / 2.4
                if a >= 1 then
                    s.nextTaste = t + 14 + math.random() * 12
                elseif nova == 0 then
                    taste = 0.6 * smoothstep(0, 0.3, a) * (1 - smoothstep(0.65, 1, a))
                end
            end
            local uncurl = math.max(sipping, taste)

            -- the wings: a quick flutter, the hindwings a moment behind; fanning, slow and deep; in the special, held still, then lifted high and brought down once
            local rate = (2.4 + 0.9 * moving + 0.6 * fly) * (1 - 0.6 * fanning) * (1 - 0.85 * stillness)
            s.beat = (s.beat or 0) + dt * rate * 2 * math.pi
            local beat = s.beat
            local amp = (0.42 + 0.14 * moving + 0.1 * fly) * (1 + 0.6 * fanning) * (1 - 0.8 * stillness)
            local base = 0.12 + 0.3 * fanning + 1.0 * lift - 0.7 * stroke
            for _, side in { "L", "R" } do
                local up = if side == "L" then -1 else 1
                pose(m["Fore" .. side .. "1"], CFrame.Angles(0, up * 0.06 * math.sin(beat - 0.6), up * (base + amp * math.sin(beat))))
                pose(m["Fore" .. side .. "2"], CFrame.Angles(0, 0, up * (0.22 * amp * math.sin(beat - 0.9) - 0.12 * stroke)))
                pose(m["Hind" .. side .. "1"], CFrame.Angles(0, 0, up * (base * 0.85 + 0.9 * amp * math.sin(beat - 0.4))))
                pose(m["Hind" .. side .. "2"], CFrame.Angles(0, 0, up * (0.2 * amp * math.sin(beat - 1.2) - 0.1 * stroke)))
            end

            -- the body rides each downstroke, and a moth never flies quite straight
            local drift = 0.03 * math.sin(t * 1.3) + 0.018 * math.sin(t * 2.9 + 1)
            local rise = 0.022 * math.sin(beat - 1.3) + 0.02 * math.sin(t * 1.7) + 0.08 * lift
            local look = rig.rootPart.CFrame.LookVector
            local heading = math.atan2(-look.X, -look.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.12, -0.3, 0.3) - (s.bank or 0)) * math.min(1, dt * 3)
            local pitch = -0.06 * moving - 0.04 * fly - 0.16 * sipping
            pose(m.Body, CFrame.new(drift * u, rise * u, 0) * CFrame.Angles(pitch + 0.03 * math.sin(beat - 1.6), 0.05 * math.sin(t * 0.9), s.bank - drift * 1.6))
            for index, name in { "Abd1", "Abd2", "Abd3" } do
                pose(m[name], CFrame.Angles(-0.05 * math.sin(beat - 1.8 - index * 0.5) - 0.06 * moving + 0.05 * sipping, 0.05 * math.sin(t * 1.1 - index * 0.6), 0))
            end

            -- the head: curious, cocking this way and that
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 1.5 + math.random() * 2.5
                s.gazeTo = (math.random() - 0.5) * 0.6
                s.tiltTo = (math.random() - 0.5) * 0.5
            end
            local calm = (1 - 0.6 * pace) * (1 - nova)
            local follow = math.min(1, dt * 5)
            s.yaw = (s.yaw or 0) + ((s.gazeTo or 0) * calm - (s.yaw or 0)) * follow
            s.tilt = (s.tilt or 0) + ((s.tiltTo or 0) * calm - (s.tilt or 0)) * follow
            pose(m.Head, CFrame.Angles(-pitch * 0.5 - 0.22 * sipping + 0.02 * math.sin(beat - 2), s.yaw, s.tilt))

            -- its feathery antennae: sweeping slowly, twitching, laid back at speed and in the wingbeat
            for _, side in { "L", "R" } do
                local sign = if side == "L" then -1 else 1
                local offset = if side == "L" then 0 else 2.1
                local twitch = math.max(0, math.sin(t * 0.8 + offset)) ^ 18
                pose(m["Ant" .. side .. "1"], CFrame.Angles(0.08 * math.sin(t * 0.9 + offset) - 0.35 * pace - 0.3 * stroke + 0.2 * twitch, 0, sign * (0.06 * math.sin(t * 0.6 + offset) + 0.1 * twitch)))
                pose(m["Ant" .. side .. "2"], CFrame.Angles(0.06 * math.sin(t * 1.3 + offset) - 0.2 * pace + 0.15 * twitch, 0, 0))
            end

            -- the tongue: coiled, or uncurling to taste or to drink
            pose(m.Tongue1, CFrame.Angles(0.3 * uncurl, 0, 0))
            for k = 1, #MOTH_BENDS do
                pose(m["Tongue" .. (k + 1)], CFrame.Angles(-MOTH_BENDS[k] * 0.92 * uncurl, 0, 0))
            end

            -- the legs hang and paddle a little
            for _, key in { "F", "M", "B" } do
                for _, side in { "L", "R" } do
                    local offset = (if key == "F" then 0 elseif key == "M" then 1.3 else 2.6) + (if side == "L" then 0 else 0.7)
                    pose(m["Leg" .. key .. side .. "1"], CFrame.Angles(0.08 * math.sin(t * 1.5 + offset) - 0.4 * pace, 0, 0))
                    pose(m["Leg" .. key .. side .. "2"], CFrame.Angles(0.1 * math.sin(t * 1.5 + offset - 0.6) - 0.3 * pace, 0, 0))
                end
            end

            -- the pseudopupils turn toward whoever is looking, as far as they can, and drift back when nobody is in front of it
            if camera then
                for _, side in { "L", "R" } do
                    local bone = rig.points["Pupil" .. side]
                    if bone then
                        -- in the model's own axes as the head now holds them: what the head's pose has turned (its posed frame against its rest frame, both in the world), applied to the model's frame
                        local head = bone.Parent
                        local turnedBy = if head and head:IsA("Bone") then head.TransformedWorldCFrame.Rotation * head.WorldCFrame.Rotation:Inverse() else CFrame.identity
                        local frame = turnedBy * rig.rootPart.CFrame.Rotation
                        local toward = frame:VectorToObjectSpace(camera.CFrame.Position - bone.TransformedWorldCFrame.Position)
                        local rest = MOTH_REST[side]
                        local want = CFrame.identity
                        if toward.Magnitude > 0.01 then
                            local d = toward.Unit
                            local axis = rest:Cross(d)
                            local angle = math.acos(math.clamp(rest:Dot(d), -1, 1))
                            if axis.Magnitude > 1e-4 and angle < 1.6 then
                                want = CFrame.fromAxisAngle(axis.Unit, math.min(angle * MOTH_PUPIL_SHARE, MOTH_PUPIL_TURN))
                            end
                        end
                        local key = "pupil" .. side
                        s[key] = (s[key] or CFrame.identity):Lerp(want, math.min(1, dt * 6))
                        pose(m["Pupil" .. side], s[key])
                    end
                end
            end
        end
    end

    return { animateDreamMoth = animateDreamMoth, mothThreads = mothThreads }
end
