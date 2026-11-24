-- The SnowLeopard pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, SPARKLE, pose, smoothstep, addStance, dropToGround = K.PetRig, K.SPARKLE, K.pose, K.smoothstep, K.addStance, K.dropToGround

    local animateSnowLeopard, LEOPARD_BONES, LEOPARD_ICE, LEOPARD_SOLE, LEOPARD_STAR -- animateSnowLeopard's section below (its own locals stay in its block)
    do

        -- The Celestial Snow Leopard (skinned): a grown snow leopard, a hunter of the high snow. It prowls low, head level and forward, its shoulder blades
        -- rolling, its huge tail held low behind it, the tip lifting in a curl; now and then it stops, sinks into a stalking crouch and stares, its haunches
        -- wiggling; still a while, it lies down sphinx-like, its tail curled round beside it. Its stare is steady and intense; its ears turn on their own; its
        -- tail tip twitches. In the air it stretches out in a long leap.
        local LEOPARD_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        LEOPARD_SOLE = 0.297 -- metres from the middle of its box down to its paws: it walks on the ground
        local LEOPARD_LID_HINGE = { L = Vector3.new(0.939, -0.1562, -0.3064), R = Vector3.new(0.939, 0.1562, 0.3064) } -- both lids of an eye turn on this line
        local LEOPARD_BLINK_UPPER, LEOPARD_BLINK_LOWER = math.rad(52), math.rad(24)
        LEOPARD_ICE, LEOPARD_STAR = Color3.fromRGB(196, 232, 255), Color3.fromRGB(140, 200, 255)
        local LEOPARD_LEADS = { BL = 0, FL = math.pi / 2, BR = math.pi, FR = 3 * math.pi / 2 } -- a cat's lateral walk

        local function leopardLegs(f, b)
            local out = {}
            for _, side in { "L", "R" } do
                for k = 1, 3 do
                    out["LegF" .. side .. k] = { f[k], 0, 0 }
                    out["LegB" .. side .. k] = { b[k], 0, 0 }
                end
            end
            return out
        end

        local function leopardStance(base, f, b)
            for bone, a in leopardLegs(f, b) do
                base[bone] = a
            end
            return base
        end

        -- its stances, each searched in Blender against the ground and for torn skin: the same numbers as celestial_snow_leopard.py's CROUCH, LIE and LEAP
        local LEOPARD_CROUCH = leopardStance({ Shoulders = { 0.005, 0, 0 }, Head = { 0.228, 0, 0 } }, { -0.2, -1.387, -0.2 }, { 0.354, -0.419, 0.957 })
        local LEOPARD_CROUCH_DROP = 0.098
        local LEOPARD_LIE = leopardStance({ Hips = { -0.158, 0, 0 }, Shoulders = { 0.265, 0, 0 }, Head = { 0.16, 0, 0 },
            Tail1 = { 0, 0.4, 0 }, Tail2 = { 0, 0.4, 0 }, Tail3 = { 0, 0.35, 0 } }, { 0.226, 1.261, -0.698 }, { 0.23, -1.026, -0.306 })
        local LEOPARD_LIE_DROP = 0.182
        local LEOPARD_LEAP = leopardStance({ Hips = { -0.12, 0, 0 }, Shoulders = { -0.2, 0, 0 }, Head = { 0.155, 0, 0 } }, { 0.756, -0.247, -0.29 }, { -0.511, 0.407, -0.106 })
        for k = 1, 7 do
            LEOPARD_LEAP["Tail" .. k] = { -0.05, 0, 0 }
        end

        local function leopardBones()
            local bones = { "Hips", "Body", "Chest", "Shoulders", "Neck", "Head", "EyeL", "EyeR", "EarL", "EarR" }
            for k = 1, 7 do
                table.insert(bones, "Tail" .. k)
            end
            for _, key in { "FL", "FR", "BL", "BR" } do
                for k = 1, 3 do
                    table.insert(bones, "Leg" .. key .. k)
                end
                table.insert(bones, "Paw" .. key)
            end
            return bones
        end
        LEOPARD_BONES = leopardBones() -- every bone its stances pose (the lids turn on their hinges on their own)

        -- a fine frost drifts off it: its breath of the high snow, rising from its back and tail
        local function leopardFrost(rig, s)
            s.frostMade = true
            local tail = rig.points.Tail4
            if not tail then
                return
            end
            local frost = Instance.new("ParticleEmitter")
            frost.Name = "Frost"
            frost.Texture = SPARKLE
            frost.Rate = 2
            frost.Lifetime = NumberRange.new(1.4, 2.2)
            frost.Speed = NumberRange.new(0.03 * rig.unit, 0.12 * rig.unit)
            frost.SpreadAngle = Vector2.new(180, 180)
            frost.Acceleration = Vector3.new(0, 0.08 * rig.unit, 0)
            frost.Drag = 1
            frost.Rotation = NumberRange.new(0, 360)
            frost.RotSpeed = NumberRange.new(-30, 30)
            frost.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.06 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
            frost.Color = ColorSequence.new(Color3.fromRGB(240, 250, 255), LEOPARD_STAR)
            frost.LightEmission = 1
            frost.LightInfluence = 0
            frost.Parent = tail
        end

        function animateSnowLeopard(rig, s, moving, fly, nova)
            if not s.frostMade then
                leopardFrost(rig, s)
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > LEOPARD_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, LEOPARD_SOLE)

            -- the special, Where the Sky Begins: it sinks into a crouch, its haunches wiggling, eyes fixed (progress to 0.38); it pounces up in a long leap,
            -- frost bursting from where it sprang (Blasts.WhereTheSkyBegins, at 0.42); it lands in a crouch and rises
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local gather = smoothstep(0.02, 0.2, progress) * (1 - smoothstep(0.38, 0.43, progress)) + smoothstep(0.62, 0.68, progress) * (1 - smoothstep(0.78, 0.95, progress))
            local wiggle = smoothstep(0.15, 0.22, progress) * (1 - smoothstep(0.34, 0.39, progress))
            local leap = if progress > 0.4 and progress < 0.66 then math.sin(math.pi * (progress - 0.4) / 0.26) else 0
            local special = progress > 0

            -- still a moment, it sinks into a stalking crouch and stares, now and then; still a while, it lies down; it is up as soon as it has somewhere to go
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            local wantLie = if s.still > 8 then 1 else 0
            if s.still > 2.5 and wantLie == 0 and t >= (s.nextStalk or 0) then
                s.stalkUntil = t + 2 + math.random() * 1.5
                s.nextStalk = s.stalkUntil + 2.5 + math.random() * 3
            end
            local wantStalk = if s.still > 2.5 and wantLie == 0 and t < (s.stalkUntil or 0) then 1 else 0
            s.lie = (s.lie or 0) + (wantLie - (s.lie or 0)) * math.min(1, dt * (if wantLie > (s.lie or 0) then 1.2 else 6))
            s.stalk = (s.stalk or 0) + (wantStalk - (s.stalk or 0)) * math.min(1, dt * (if wantStalk > (s.stalk or 0) then 3 else 4))
            local lie, stalk = smoothstep(0, 1, s.lie), smoothstep(0, 1, s.stalk)
            local crouch = math.max(stalk, gather)

            -- the prowl: a cat's lateral walk, low and smooth, the shoulder blades rolling with each forefoot; in the air a long stretched leap
            s.stride = (s.stride or 0) + dt * 7.5 * moving
            local onFoot = moving * (1 - fly) * (1 - crouch)
            local want = {}
            addStance(want, LEOPARD_CROUCH, crouch * (1 - lie))
            addStance(want, LEOPARD_LIE, lie)
            addStance(want, LEOPARD_LEAP, math.min(1, fly * 0.9 + leap))
            for key, lead in LEOPARD_LEADS do
                local phase = s.stride + lead
                local swing, lift = math.sin(phase), math.max(0, math.cos(phase))
                local stance
                if string.sub(key, 1, 1) == "F" then
                    stance = { ["Leg" .. key .. "1"] = { 0.38 * swing, 0, 0 }, ["Leg" .. key .. "2"] = { -0.55 * lift, 0, 0 }, ["Leg" .. key .. "3"] = { 0.25 * lift, 0, 0 },
                        ["Paw" .. key] = { -0.3 * lift, 0, 0 } }
                else
                    stance = { ["Leg" .. key .. "1"] = { -0.38 * swing, 0, 0 }, ["Leg" .. key .. "2"] = { 0.45 * lift, 0, 0 }, ["Leg" .. key .. "3"] = { -0.55 * lift, 0, 0 } }
                end
                addStance(want, stance, onFoot)
            end
            local roll = math.sin(s.stride + math.pi / 2)
            addStance(want, { Shoulders = { 0, 0.06 * roll, 0.03 * roll }, Hips = { 0, -0.05 * roll, -0.025 * roll }, Neck = { -0.05, -0.05 * roll, 0 } }, onFoot)

            -- the body: breathing, deeper lying down; banking on turns; the haunches wiggling before a pounce
            local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.16, 0.16) - (s.bank or 0)) * math.min(1, dt * 3)
            local breath = math.sin(t * (1.3 - 0.4 * lie))
            local wig = math.sin(t * 18) * math.max(wiggle, 0.4 * stalk * math.max(0, math.sin(t * 0.9)) ^ 6)
            addStance(want, { Hips = { 0, 0.08 * wig, s.bank * moving }, Chest = { 0.012 * breath * (1 + lie), 0, 0 } }, 1)

            -- its stare: steady and intense, holding on you; when it crouches it locks on what is ahead
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2.5 + math.random() * 3
                s.atYou = math.random() < 0.5
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 0.9, (math.random() - 0.5) * 0.25
            end
            local calm = (1 - 0.7 * pace) * (1 - crouch)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.25, 0.3) else s.gazePitch) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.5)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.5)
            local turn = 1 - 0.4 * lie
            addStance(want, {
                Neck = { 0.25 * s.pitch, 0.4 * s.yaw * turn, 0 }, Head = { 0.45 * s.pitch, 0.55 * s.yaw * turn, 0 },
                EyeL = { 0.2 * s.pitch, 0.2 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
            }, 1)

            -- the ears: each turns on its own now and then; flattened in the crouch and the leap
            local flat = math.max(crouch, 0.5 * fly, leap)
            for _, side in { "L", "R" } do
                local sign = if side == "L" then 1 else -1
                local swivel = math.max(0, math.sin(t * 0.6 + (if side == "L" then 0 else 2.7))) ^ 10
                addStance(want, { ["Ear" .. side] = { -0.15 * swivel - 0.45 * flat, sign * (0.35 * swivel + 0.25 * flat), 0 } }, 1)
            end

            -- the tail: held low and heavy behind it, the tip lifting in a curl and twitching now and then; streaming in the leap; lashing before a pounce
            for k = 1, 7 do
                local sway = (0.025 + 0.04 * k / 7) * math.sin(t * 0.8 - k * 0.5) * (1 - 0.6 * lie)
                local twitch = if k >= 6 then 0.25 * math.max(0, math.sin(t * 2.1 + k)) ^ 10 * (1 - lie) else 0
                local lash = 0.12 * math.sin(t * 9 - k * 0.7) * math.max(wiggle, 0.5 * stalk) * k / 7
                addStance(want, { ["Tail" .. k] = { 0.02 * math.sin(t * 0.5 - k * 0.6) - 0.04 * moving, sway + twitch + lash, 0 } }, 1)
            end

            for _, name in LEOPARD_BONES do
                local a = want[name] or Vector3.zero
                local lift = if name == "Hips"
                    then (-LEOPARD_CROUCH_DROP * crouch * (1 - lie) - LEOPARD_LIE_DROP * lie + 0.32 * leap + 0.006 * onFoot * math.abs(math.sin(s.stride * 2))) * u - drop
                    else 0
                pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- the eyes: slow, rare blinks; a steady stare when it crouches; heavy lids lying down
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.24
                if a >= 1 then
                    s.nextBlink = t + 3.5 + math.random() * 4
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local doze = smoothstep(0.3, 0.9, 0.5 + 0.5 * math.sin(t * 0.35))
            local close = math.max(blink * (1 - crouch), lie * (0.35 + 0.55 * doze)) * (1 - gather)
            local upper = LEOPARD_BLINK_UPPER * close - math.rad(5) * crouch
            local lower = LEOPARD_BLINK_LOWER * close - math.rad(4) * crouch
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(LEOPARD_LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(LEOPARD_LID_HINGE[side], lower))
            end
        end
    end

    return { animateSnowLeopard = animateSnowLeopard, LEOPARD_BONES = LEOPARD_BONES, LEOPARD_ICE = LEOPARD_ICE, LEOPARD_SOLE = LEOPARD_SOLE, LEOPARD_STAR = LEOPARD_STAR }
end
