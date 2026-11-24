-- The GlacierPuff pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep, dropToGround = K.PetRig, K.pose, K.smoothstep, K.dropToGround

    local animateGlacierPuff, PUFF_FROST, PUFF_ICE -- animateGlacierPuff's section below (its own locals stay in its block)
    do

        -- The Glacier Puff (skinned): a little pufferfish of glacier ice that swims through the air. It hangs half a metre up, its pectoral fins whirring, its
        -- tail sculling, its body wagging as a fish's does; its eyes wander, each its own way, and now and then both fix on you; every few seconds it gulps, and
        -- a few bubbles of frost rise from its mouth. Now and then something startles it and it half puffs, a few spines of hoarfrost pricking out of its ice,
        -- and settles again. It swims faster, nose down, when its owner goes somewhere.
        local PUFF_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        local PUFF_ZONES = 8
        local PUFF_T, PUFF_S = 0.06, 0.054 -- metres each puff bone moves out at full puff, and how much further its spines slide out of the ice (glacier_puff.py)
        local PUFF_BODY_SOLE = 0.153 -- metres from its Body bone down to its lowest point (glacier_puff.py)
        local PUFF_HOVER = 0.45 -- metres above the ground it swims
        PUFF_FROST, PUFF_ICE = Color3.fromRGB(226, 244, 255), Color3.fromRGB(150, 210, 250)
        local PUFF_DIRS = {} -- each puff bone's way out, in the game's axes: round its length, 1 its left, then up, its right, down
        for k = 1, PUFF_ZONES do
            local a = 2 * math.pi * (k - 1) / PUFF_ZONES
            PUFF_DIRS[k] = Vector3.new(-math.cos(a), math.sin(a), 0)
        end

        -- frost bubbles from its mouth when it gulps
        local function puffBubbles(rig, s)
            s.bubblesMade = true
            local jaw = rig.points.Jaw
            if not jaw then
                return
            end
            local bubbles = Instance.new("ParticleEmitter")
            bubbles.Name = "FrostBubbles"
            bubbles.Texture = "rbxasset://textures/particles/explosion01_implosion_main.dds"
            bubbles.Enabled = false
            bubbles.Lifetime = NumberRange.new(0.8, 1.4)
            bubbles.Speed = NumberRange.new(0.15 * rig.unit, 0.35 * rig.unit)
            bubbles.SpreadAngle = Vector2.new(25, 25)
            bubbles.EmissionDirection = Enum.NormalId.Front
            bubbles.Acceleration = Vector3.new(0, 0.35 * rig.unit, 0)
            bubbles.Drag = 1.5
            bubbles.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.025 * rig.unit), NumberSequenceKeypoint.new(0.5, 0.045 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
            bubbles.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.25), NumberSequenceKeypoint.new(1, 1) })
            bubbles.Color = ColorSequence.new(PUFF_FROST, PUFF_ICE)
            bubbles.LightEmission = 0.4
            bubbles.LightInfluence = 0.3
            bubbles.Parent = jaw
            s.bubbles = bubbles
        end

        function animateGlacierPuff(rig, s, moving, fly, nova)
            if not s.bubblesMade then
                puffBubbles(rig, s)
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > PUFF_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special, Hoarfrost Bloom: it takes a great gulp of air and swells into a ball of hoarfrost spines (to 0.42; Blasts.HoarfrostBloom), hangs
            -- there turning slowly, then lets the air go in a sigh of frost bubbles and is a smooth little fish again
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local swell = smoothstep(0.08, 0.4, progress) * (1 - smoothstep(0.74, 0.94, progress))
            local gulpIn = if progress > 0.02 and progress < 0.12 then math.sin(math.pi * (progress - 0.02) / 0.1) else 0
            if progress > 0.76 and not s.sighed then
                s.sighed = true
                if s.bubbles then
                    s.bubbles:Emit(14)
                end
            elseif progress == 0 then
                s.sighed = false
            end

            -- startled now and then: a quick half puff, a few spines pricking out, and it settles
            s.nextStartle = s.nextStartle or t + 12 + math.random() * 10
            if t >= s.nextStartle and progress == 0 then
                s.startleAt = t
                s.nextStartle = t + 14 + math.random() * 12
            end
            local startleEnv = if s.startleAt then (t - s.startleAt) / 1.6 else 1
            local startle = if startleEnv < 1 then smoothstep(0, 0.12, startleEnv) * (1 - smoothstep(0.45, 1, startleEnv)) * 0.5 else 0
            local puff = math.max(swell, startle)
            for k = 1, PUFF_ZONES do
                pose(m["Puff" .. k], CFrame.new(PUFF_DIRS[k] * (PUFF_T * puff * u)))
                pose(m["Spike" .. k], CFrame.new(PUFF_DIRS[k] * (PUFF_S * puff * u)))
            end

            -- swimming: its body wags as a fish's does, the tail sculling behind it, faster when it goes somewhere; puffed, it can only paddle
            local stiff = 1 - 0.7 * puff
            s.swim = (s.swim or 0) + dt * (2.4 + 4 * pace) * (1 - 0.5 * puff)
            local wag = math.sin(s.swim)
            local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.1, -0.3, 0.3) - (s.bank or 0)) * math.min(1, dt * 3)
            local bodySole = rig.points.Body
            if bodySole and not s.sole then
                s.sole = rig.rootPart.CFrame:PointToObjectSpace(bodySole.WorldPosition).Y * -1 / u + PUFF_BODY_SOLE -- (WorldPosition leaves out its own Transform)
            end
            local drop = dropToGround(rig, s, t, u, fly, s.sole or 0.2)
            local bob = 0.03 * math.sin(t * 1.3) + 0.012 * math.sin(t * 2.9 + 1)
            local lift = (PUFF_HOVER * (1 - fly) + bob + 0.05 * swell) * u - drop
            local spin = if progress > 0.3 and progress < 0.9 then 2 * math.pi * smoothstep(0.3, 0.9, progress) else 0
            pose(m.Body, CFrame.new(0, lift, 0) * CFrame.Angles(-0.18 * pace + 0.04 * math.sin(t * 0.9), 0.09 * wag * stiff + spin, s.bank + 0.05 * math.sin(t * 0.7)))
            pose(m.Tail1, CFrame.Angles(0, -0.2 * math.sin(s.swim - 0.8) * stiff, 0))
            pose(m.Tail2, CFrame.Angles(0, -0.32 * math.sin(s.swim - 1.6) * (0.4 + 0.6 * stiff), 0))

            -- its fins: the pectorals whir, a blur of small fast beats, harder when it swims fast or is puffed; the dorsal and anal fins ripple
            s.whir = (s.whir or 0) + dt * (14 + 10 * pace + 8 * puff)
            local beat = math.sin(s.whir)
            for _, tag in { "L", "R" } do
                local sign = if tag == "L" then 1 else -1
                local back = -0.14 + 0.36 * (0.5 + 0.5 * beat) -- between 0.22 forward and -0.5 back (checked in Blender: further forward meets its cheek)
                pose(m["Fin" .. tag], CFrame.Angles(0, sign * math.clamp(back - 0.2 * pace, -0.5, 0.22), 0))
            end
            pose(m.Dorsal, CFrame.Angles(0, 0, 0.18 * math.sin(s.swim * 1.5)))
            pose(m.Anal, CFrame.Angles(0, 0, -0.18 * math.sin(s.swim * 1.5 + 0.6)))

            -- its eyes: each wanders its own way; now and then both fix on you
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.eyes = s.eyes or { L = { yaw = 0, pitch = 0, next = 0 }, R = { yaw = 0, pitch = 0, next = 0 } }
            s.nextBoth = s.nextBoth or t + 3
            if t >= s.nextBoth then
                s.bothUntil = t + 1.2 + math.random() * 1.5
                s.nextBoth = s.bothUntil + 3 + math.random() * 4
            end
            local both = t < (s.bothUntil or 0) or swell > 0.1
            for tag, eye in s.eyes do
                local sign = if tag == "L" then 1 else -1
                if t >= eye.next then
                    eye.next = t + 0.6 + math.random() * 1.8
                    eye.wantYaw, eye.wantPitch = (math.random() - 0.5) * 0.9, (math.random() - 0.5) * 0.5
                end
                local wy = if both then math.clamp(math.atan2(-toYou.X, -toYou.Z) * 0.5 - sign * 0.15, -0.45, 0.45) else eye.wantYaw or 0
                local wp = if both then math.clamp(toYou.Y * 0.5, -0.3, 0.3) else eye.wantPitch or 0
                eye.yaw += (wy - eye.yaw) * math.min(1, dt * 10)
                eye.pitch += (wp - eye.pitch) * math.min(1, dt * 10)
                pose(m["Eye" .. tag], CFrame.Angles(eye.pitch, eye.yaw, 0))
            end

            -- it gulps every few seconds, a few frost bubbles rising from its mouth; it takes a great gulp before it swells
            s.nextGulp = s.nextGulp or t + 2
            if t >= s.nextGulp then
                s.gulpAt = t
                s.nextGulp = t + 2.5 + math.random() * 3.5
                if s.bubbles and swell < 0.1 then
                    s.bubbles:Emit(3)
                end
            end
            local gulpEnv = if s.gulpAt then (t - s.gulpAt) / 0.45 else 1
            local gulp = if gulpEnv < 1 then math.sin(math.pi * gulpEnv) else 0
            pose(m.Jaw, CFrame.Angles(-0.35 * math.max(gulp, gulpIn), 0, 0))
        end
    end

    return { animateGlacierPuff = animateGlacierPuff, PUFF_FROST = PUFF_FROST, PUFF_ICE = PUFF_ICE }
end
