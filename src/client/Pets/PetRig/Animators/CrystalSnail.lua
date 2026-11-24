-- The CrystalSnail pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, SPARKLE, pose, smoothstep, dropToGround = K.PetRig, K.SPARKLE, K.pose, K.smoothstep, K.dropToGround

    local animateCrystalSnail, SNAIL_SOLE -- animateCrystalSnail's section below (its own locals stay in its block)
    do

        -- The Crystal Snail (skinned): it glides on a slow wave of its foot, stretching forward and gathering itself, and leaves a faint road of crystal glints where it has been. Its eyes are on stalks with no lids:
        -- like a real snail it blinks by drawing a stalk in (one at a time, in quickly, out slowly), and what it feels shows in how the stalks lean, wave and droop. Shy now and then, it draws both in and lets them out again bit by bit.
        local SNAIL_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        SNAIL_SOLE = 0.2606 -- metres from the middle of its box down to its sole: it glides on the ground
        local SNAIL_STALK = { L = Vector3.new(-0.2266, 0.8952, -0.3837), R = Vector3.new(0.2266, 0.8952, -0.3837) } -- each stalk's line, root to eye, in the model's axes
        local SNAIL_DRAW = 0.0753 -- metres each of a stalk's two moving joints draws back when it is all the way in (tools/blender/pets/crystal_snail.py's retract())
        local SNAIL_GEMS = Color3.fromRGB(70, 225, 190)

        local function snailRoad(rig, s, u)
            local tip = rig.points.TailTip
            if not tip then
                return
            end
            local road = Instance.new("ParticleEmitter")
            road.Name = "CrystalRoad"
            road.Texture = SPARKLE
            road.Rate = 0
            road.Lifetime = NumberRange.new(1.6, 2.4)
            road.Speed = NumberRange.new(0)
            road.Rotation = NumberRange.new(0, 360)
            road.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.12, 0.07 * u), NumberSequenceKeypoint.new(0.7, 0.05 * u), NumberSequenceKeypoint.new(1, 0) })
            road.Color = ColorSequence.new(Color3.fromRGB(190, 255, 236), Color3.fromRGB(110, 220, 230))
            road.LightEmission = 0.6
            road.LightInfluence = 0.4
            road.Parent = tip
            s.snailRoad = road
        end

        function animateCrystalSnail(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > SNAIL_FAR then
                if s.snailRoad then
                    s.snailRoad.Rate = 0
                end
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, SNAIL_SOLE)
            if not s.snailRoad then
                snailRoad(rig, s, u)
            end

            -- the special: it draws itself in under its shell, stalks first; its crystals brighten; a road of crystal grows up behind it; then the stalks come out, to see whether anyone noticed, and the rest of it after
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local hide = smoothstep(0.04, 0.3, progress) * (1 - smoothstep(0.66, 0.86, progress))
            local stalksIn = smoothstep(0, 0.16, progress) * (1 - smoothstep(0.5, 0.64, progress))
            local glow = smoothstep(0.18, 0.42, progress) * (1 - smoothstep(0.48, 0.8, progress))
            local peek = smoothstep(0.56, 0.66, progress) * (1 - smoothstep(0.84, 0.98, progress))

            -- shy now and then: both stalks in, and out again slowly
            s.nextShy = s.nextShy or t + 12 + math.random() * 10
            local shy = 0
            if t >= s.nextShy then
                local a = (t - s.nextShy) / 3
                if a >= 1 then
                    s.nextShy = t + 16 + math.random() * 14
                elseif nova == 0 then
                    shy = smoothstep(0, 0.08, a) * (1 - smoothstep(0.25, 1, a))
                end
            end
            -- it blinks one stalk at a time: in quickly, out slowly
            s.nextBlink = s.nextBlink or t + 2
            if t >= s.nextBlink then
                s.nextBlink = t + 2 + math.random() * 3.5
                s.blinkAt = t
                s.blinkSide = if math.random() < 0.5 then "L" else "R"
            end
            local blink = 0
            if s.blinkAt then
                local a = t - s.blinkAt
                blink = smoothstep(0, 0.07, a) * (1 - smoothstep(0.12, 0.5, a))
            end

            -- the gaze: the head turns slowly; the stalks wander on their own
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2 + math.random() * 3
                s.gazeTo = (math.random() - 0.5) * 0.8
                s.nodTo = (math.random() - 0.5) * 0.18
                s.tiltTo = if math.random() < 0.35 then (math.random() - 0.5) * 0.4 else 0
            end
            local calm = (1 - 0.5 * pace) * (1 - hide)
            local follow = math.min(1, dt * 2.2)
            s.yaw = (s.yaw or 0) + (((s.gazeTo or 0) * calm + 0.5 * peek * math.sin(t * 2.2)) - (s.yaw or 0)) * follow
            s.nod = (s.nod or 0) + ((s.nodTo or 0) * calm - (s.nod or 0)) * follow
            s.tilt = (s.tilt or 0) + ((s.tiltTo or 0) * calm - (s.tilt or 0)) * follow

            -- the glide: a slow wave runs back along the foot; the front stretches forward and gathers
            s.glide = (s.glide or 0) + dt * (1 + 4 * moving)
            local wave = s.glide
            local stretch = (0.5 + 0.5 * math.sin(wave)) * moving
            local look = rig.rootPart.CFrame.LookVector
            local heading = math.atan2(-look.X, -look.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.15, 0.15) - (s.bank or 0)) * math.min(1, dt * 3)
            local breath = math.sin(t * 1.1)
            pose(m.Body, CFrame.new(0, (0.004 * breath + 0.05 * fly) * u - drop, 0) * CFrame.Angles(0.06 * fly + 0.008 * breath, -s.bank * 0.6, 0.04 * fly * math.sin(t * 1.4)))
            pose(m.Front, CFrame.new(0, -0.025 * hide * u + 0.006 * moving * math.sin(wave - 0.5) * u, (0.08 * hide - 0.045 * stretch) * u)
                * CFrame.Angles(0.06 * stretch - 0.15 * hide + 0.15 * fly + 0.02 * breath, s.yaw * 0.4 + s.bank, 0))
            pose(m.Head, CFrame.Angles(0.12 * stretch - 0.35 * hide + s.nod + 0.08 * peek, s.yaw * 0.6, s.tilt))
            pose(m.Tail1, CFrame.Angles(0.025 * moving * math.sin(wave - 1.2) - 0.35 * fly, 0.08 * math.sin(t * 0.6) * (1 - moving) - s.bank, 0))
            pose(m.Tail2, CFrame.Angles(0.035 * moving * math.sin(wave - 2.2) - 0.45 * fly, 0.1 * math.sin(t * 0.6 - 0.8) * (1 - moving) - s.bank * 1.3, 0))
            pose(m.TailTip, CFrame.Angles(-0.2 * fly, 0, 0))
            pose(m.Shell, CFrame.Angles(0.02 * moving * math.sin(wave - 0.6) + 0.012 * math.sin(t * 0.7) + 0.02 * glow * math.sin(t * 38), 0, 0.025 * math.sin(t * 0.5) + 0.03 * moving * math.sin(wave * 0.5)))

            -- the stalks: each wanders, leans back at speed and in the air, forward when it peeks out; drawn in to blink, when shy, and in the special
            for _, side in { "L", "R" } do
                local sign = if side == "L" then -1 else 1
                local offset = if side == "L" then 0 else 2.3
                local lean = 0.12 * math.sin(t * 0.8 + offset) + 0.35 * moving + 0.5 * fly - 0.3 * peek
                local spread = sign * (0.1 * math.sin(t * 0.6 + offset) + 0.08 * peek * math.sin(t * 3 + offset))
                local drawn = math.max(if s.blinkSide == side then blink else 0, shy, stalksIn, 0.8 * hide)
                local back = SNAIL_STALK[side] * (-drawn * SNAIL_DRAW * u)
                pose(m["Stalk" .. side .. "1"], CFrame.Angles(lean, 0, spread))
                pose(m["Stalk" .. side .. "2"], CFrame.new(back) * CFrame.Angles(0.2 * lean + 0.08 * math.sin(t * 1.3 + offset), 0, sign * 0.06 * math.sin(t * 1.1 + offset)))
                pose(m["Stalk" .. side .. "3"], CFrame.new(back) * CFrame.Angles(0.05 * math.sin(t * 1.7 + offset), 0, 0))
            end

            -- the glowing crystals breathe; in the special they burn
            local gems = rig.parts.Gems
            if gems then
                gems.Color = SNAIL_GEMS:Lerp(Color3.fromRGB(200, 255, 240), 0.18 * (0.5 + 0.5 * math.sin(t * 1.4)) + 0.6 * glow)
            end
            if s.snailRoad then
                s.snailRoad.Rate = 7 * moving * (1 - fly)
            end
        end
    end

    return { animateCrystalSnail = animateCrystalSnail, SNAIL_SOLE = SNAIL_SOLE }
end
