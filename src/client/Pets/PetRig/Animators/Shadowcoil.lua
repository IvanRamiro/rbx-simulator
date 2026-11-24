-- The Shadowcoil pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep, dropToGround = K.PetRig, K.pose, K.smoothstep, K.dropToGround

    local animateShadowcoil, SHADOW_BONES, SHADOW_EYESHINE, SHADOW_INK, SHADOW_RIM, SHADOW_SOLE, addStance, shadowDisc -- animateShadowcoil's section below (its own locals stay in its block)
    do

        -- The Shadowcoil (skinned): a shadow stoat, ink black, with wisps of smoke along its back and a tail that coils like a curl of smoke. It bounds
        -- the way a stoat does, forepaws then hind paws, its back humping; still a moment, it rears up on its hind legs to look about; still a while
        -- longer, it lies down curled, its tail coiled behind it, and dozes; its glances are quick and sly, its eyes darting ahead of its head; a
        -- faint smoke drifts off its tail.
        local SHADOW_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        SHADOW_SOLE = 0.3253 -- metres from the middle of its box down to its paws: it runs on the ground
        local SHADOW_LID_HINGE = { L = Vector3.new(0.8851, -0.1728, -0.4322), R = Vector3.new(0.8851, 0.1728, 0.4322) } -- both lids of an eye turn on this line
        local SHADOW_BLINK_UPPER, SHADOW_BLINK_LOWER = math.rad(62), math.rad(22)
        local SHADOW_SINK = 0.7 -- metres it pours itself down into its shadow in the special: all of its height
        SHADOW_INK, SHADOW_RIM, SHADOW_EYESHINE = Color3.fromRGB(12, 7, 24), Color3.fromRGB(118, 92, 196), Color3.fromRGB(168, 255, 224)
        local SHADOW_LIE_DROP = 0.097 -- metres its hips come down when it lies
        -- its poses, each checked in Blender against the ground and for torn skin: the same numbers as shadowcoil.py's Gather, Stretch, REAR and LIE
        local SHADOW_GATHER = {
            Hips = { -0.25, 0, 0 }, Body = { 0.2, 0, 0 }, Chest = { 0.15, 0, 0 },
            LegFL1 = { -0.6, 0, 0 }, LegFR1 = { -0.6, 0, 0 }, LegBL1 = { 0.7, 0, 0 }, LegBR1 = { 0.7, 0, 0 }, LegBL2 = { -0.4, 0, 0 }, LegBR2 = { -0.4, 0, 0 },
        }
        local SHADOW_STRETCH = {
            Hips = { 0.15, 0, 0 }, Body = { -0.1, 0, 0 },
            LegFL1 = { 0.75, 0, 0 }, LegFR1 = { 0.75, 0, 0 }, LegBL1 = { -0.75, 0, 0 }, LegBR1 = { -0.75, 0, 0 }, LegBL2 = { 0.4, 0, 0 }, LegBR2 = { 0.4, 0, 0 },
        }
        local SHADOW_REAR = {
            Body = { 1.05, 0, 0 }, Chest = { -0.15, 0, 0 }, Neck = { -0.35, 0, 0 }, Head = { -0.4, 0, 0 },
            LegFL1 = { -0.9, 0, 0 }, LegFR1 = { -0.9, 0, 0 }, LegFL2 = { 0.9, 0, 0 }, LegFR2 = { 0.9, 0, 0 }, LegFL3 = { 0.6, 0, 0 }, LegFR3 = { 0.6, 0, 0 },
        }
        local SHADOW_LIE = {
            Body = { 0, 0.25, 0 }, Chest = { 0, 0.3, 0 }, Shoulders = { 0, 0.3, 0 }, Neck = { 0.1, 0.35, 0 }, Head = { 0.05, 0.3, 0 },
            LegFL1 = { -0.557, 0, 0 }, LegFR1 = { -0.557, 0, 0 }, LegFL2 = { -1.459, 0, 0 }, LegFR2 = { -1.459, 0, 0 }, LegFL3 = { -0.624, 0, 0 }, LegFR3 = { -0.624, 0, 0 },
            LegBL1 = { 0.646, 0, 0 }, LegBR1 = { 0.646, 0, 0 }, LegBL2 = { -1.205, 0, 0 }, LegBR2 = { -1.205, 0, 0 }, LegBL3 = { 0.865, 0, 0 }, LegBR3 = { 0.865, 0, 0 },
            Tail1 = { 0, 0.03, 0 }, Tail2 = { 0.14, 0.03, 0 }, Tail3 = { -0.55, 0, 0 }, Tail4 = { -0.27, 0, 0 },
        }

        -- every bone it poses through its stances (the lids turn on their hinges on their own)
        local function shadowBones()
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
        SHADOW_BONES = shadowBones()

        -- adds a stance (bone: { rx, ry, rz }), scaled by weight, into a table of wanted turns: a pet blends its poses by adding them
        function addStance(into, stance, weight)
            if weight <= 0 then
                return
            end
            for bone, a in stance do
                into[bone] = (into[bone] or Vector3.zero) + Vector3.new(a[1], a[2], a[3]) * weight
            end
        end

        -- a flat disc of shadow on the ground: a cylinder stood on its end; its top at `top` metres above the ground
        function shadowDisc(part, ground, top, thickness, width, metre)
            part.Size = Vector3.new(thickness * metre, width * metre, width * metre)
            part.CFrame = CFrame.new(ground + Vector3.new(0, (top - thickness / 2) * metre, 0)) * CFrame.Angles(0, 0, math.pi / 2)
        end

        -- its skin and the glints in its eyes go together: 0, all there; 1, gone
        local function shadowGone(rig, s, gone)
            if s.gone == gone then
                return
            end
            s.gone = gone
            for _, key in { "Body", "Glints" } do
                local part = rig.parts[key]
                if part then
                    part.Transparency = gone
                end
            end
            if s.smoke then
                s.smoke.Enabled = gone < 0.5
            end
        end

        local function shadowSmoke(rig, s)
            s.smokeMade = true
            local tip = rig.points.Tail7
            if not tip then
                return
            end
            local smoke = Instance.new("ParticleEmitter")
            smoke.Name = "Smoke"
            smoke.Texture = "rbxasset://textures/particles/smoke_main.dds"
            smoke.Rate = 2.5
            smoke.Lifetime = NumberRange.new(1.4, 2.2)
            smoke.Speed = NumberRange.new(0.02 * rig.unit, 0.08 * rig.unit)
            smoke.SpreadAngle = Vector2.new(180, 180)
            smoke.Acceleration = Vector3.new(0, 0.1 * rig.unit, 0)
            smoke.Drag = 1.5
            smoke.Rotation = NumberRange.new(0, 360)
            smoke.RotSpeed = NumberRange.new(-25, 25)
            smoke.Size = NumberSequence.new(0.08 * rig.unit, 0.3 * rig.unit)
            smoke.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.72), NumberSequenceKeypoint.new(1, 1) })
            smoke.Color = ColorSequence.new(Color3.fromRGB(84, 70, 120), Color3.fromRGB(34, 26, 52))
            smoke.LightEmission = 0
            smoke.LightInfluence = 0.6
            smoke.Parent = tip
            s.smoke = smoke
        end

        -- the shadow it pours itself into before the special's loop (Blasts.FirstMove carries on from it): the model's own, so it goes when the pet goes
        local function shadowPool(rig)
            local pool = {}
            for _, look in { { "ShadowPool", SHADOW_INK, Enum.Material.SmoothPlastic }, { "ShadowRim", SHADOW_RIM, Enum.Material.Neon } } do
                local part = Instance.new("Part")
                part.Name = look[1]
                part.Shape = Enum.PartType.Cylinder
                part.Color = look[2]
                part.Material = look[3]
                part.Anchored = true
                part.CanCollide = false
                part.CanTouch = false
                part.CanQuery = false
                part.CastShadow = false
                part.Transparency = 1
                part.Size = Vector3.one * 0.05
                part.CFrame = rig.rootPart.CFrame
                part.Parent = rig.model
                table.insert(pool, part)
            end
            return pool
        end

        function animateShadowcoil(rig, s, moving, fly, nova)
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special, First Move: it crouches, eyes wide; pours itself down into its own shadow and is gone; the shadow races round a loop on the
            -- ground (Blasts.FirstMove) and back; it bursts up out of it in a leap and lands where it was
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local notice = smoothstep(0, 0.08, progress) * (1 - smoothstep(0.12, 0.3, progress))
            local sink = smoothstep(0.12, 0.4, progress) * (1 - smoothstep(0.73, 0.8, progress))
            local hop = if progress > 0.76 and progress < 0.92 then math.sin(math.pi * (progress - 0.76) / 0.16) else 0
            -- (before the far check: it must come back whether or not anyone is watching)
            shadowGone(rig, s, smoothstep(0.2, 0.38, progress) * (1 - smoothstep(0.72, 0.77, progress)))
            local pooling = progress > 0.06 and progress < PetRig.NOVA_BURST
            if pooling or s.poolShown then
                s.pool = s.pool or shadowPool(rig)
                s.poolShown = pooling
                local ground = rig.rootPart.Position - Vector3.new(0, SHADOW_SOLE * u + (s.drop or 0), 0)
                local grow = smoothstep(0.08, 0.36, progress)
                shadowDisc(s.pool[1], ground, 0.02, 0.012, 0.15 + 0.65 * grow, u)
                shadowDisc(s.pool[2], ground, 0.0145, 0.014, (0.15 + 0.65 * grow) * 1.12, u)
                local show = if pooling then smoothstep(0.06, 0.2, progress) else 0
                s.pool[1].Transparency = 1 - 0.88 * show
                s.pool[2].Transparency = 1 - 0.45 * show
            end

            if not s.smokeMade then
                shadowSmoke(rig, s)
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > SHADOW_FAR then
                return
            end
            local drop = dropToGround(rig, s, t, u, fly, SHADOW_SOLE)
            local special = progress > 0

            -- still a moment, it rears up to look about, now and then; still a while, it lies down; it is up and away as soon as it has somewhere to go
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            local wantLie = if s.still > 9 then 1 else 0
            if s.still > 2.5 and wantLie == 0 and t >= (s.nextRear or 0) then
                s.rearUntil = t + 1.8 + math.random() * 1.2
                s.nextRear = s.rearUntil + 3 + math.random() * 4
            end
            local wantRear = if s.still > 2.5 and wantLie == 0 and t < (s.rearUntil or 0) then 1 else 0
            s.lie = (s.lie or 0) + (wantLie - (s.lie or 0)) * math.min(1, dt * (if wantLie > (s.lie or 0) then 1.2 else 6))
            s.rear = (s.rear or 0) + (wantRear - (s.rear or 0)) * math.min(1, dt * (if wantRear > (s.rear or 0) then 5 else 4))
            local lie, rear = smoothstep(0, 1, s.lie), smoothstep(0, 1, s.rear)

            -- the bound: gathered, back humped and hind paws under it, then stretched out, forelegs reaching; each pair folds its paws as it swings
            -- through; in the air a long stretched leap
            s.stride = (s.stride or 0) + dt * 9 * moving
            local g = math.sin(s.stride)
            local onFoot = moving * (1 - fly)
            local gathered, stretched = math.max(0, g) * onFoot + 0.5 * notice, math.max(0, -g) * onFoot
            local want = {}
            addStance(want, SHADOW_GATHER, gathered)
            addStance(want, SHADOW_STRETCH, math.min(1, stretched + 0.9 * fly + hop))
            addStance(want, SHADOW_REAR, rear)
            addStance(want, SHADOW_LIE, lie)
            local frontLift = math.max(0, -math.cos(s.stride)) * onFoot
            local hindLift = math.max(0, math.cos(s.stride)) * onFoot
            for _, side in { "L", "R" } do
                addStance(want, { ["LegF" .. side .. "2"] = { -0.3, 0, 0 }, ["LegF" .. side .. "3"] = { -0.5, 0, 0 }, ["PawF" .. side] = { -0.2, 0, 0 } }, frontLift)
                addStance(want, { ["LegB" .. side .. "2"] = { -0.35, 0, 0 }, ["LegB" .. side .. "3"] = { 0.4, 0, 0 } }, hindLift)
            end

            -- the body: banking on turns, breathing, slower and deeper lying down
            local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.16, 0.16) - (s.bank or 0)) * math.min(1, dt * 3)
            addStance(want, { Hips = { 0, 0, s.bank }, Chest = { 0.012 * math.sin(t * 1.7), 0, 0 }, Body = { 0.015 * lie * math.sin(t * 1.1), 0, 0 } }, 1)

            -- its gaze: quick sly glances, the eyes darting ahead and the head following; often at you; wider when it rears to look about
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 0.7 + math.random() * 1.5
                s.atYou = math.random() < 0.4
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.4, (math.random() - 0.5) * 0.3
            end
            local calm = 1 - 0.7 * pace
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw * (1 + 0.3 * rear)) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.6, -0.25, 0.35) else s.gazePitch + 0.1 * rear) * calm
            s.eyeYaw = (s.eyeYaw or 0) + (wantYaw - (s.eyeYaw or 0)) * math.min(1, dt * 14)
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 5)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 5)
            local turn = 1 - 0.5 * lie
            addStance(want, {
                Neck = { 0.3 * s.pitch - 0.06 * moving, 0.4 * s.yaw * turn, 0 },
                Head = { 0.5 * s.pitch, 0.6 * s.yaw * turn, 0 },
            }, 1)
            local eyeYaw = math.clamp(0.25 * s.yaw + (s.eyeYaw - s.yaw), -0.3, 0.3)
            addStance(want, { EyeL = { 0.25 * s.pitch, eyeYaw, 0 }, EyeR = { 0.25 * s.pitch, eyeYaw, 0 } }, 1)

            -- the ears: each twitches on its own now and then; laid back in the leap and as it goes down into its shadow
            local flat = math.max(notice, sink, 0.6 * fly)
            for _, side in { "L", "R" } do
                local sign = if side == "L" then 1 else -1
                local twitch = math.max(0, math.sin(t * 0.8 + (if side == "L" then 0 else 2.3))) ^ 12
                addStance(want, { ["Ear" .. side] = { -0.15 * twitch - 0.4 * flat, sign * (0.3 * twitch + 0.3 * flat), 0 } }, 1)
            end

            -- the tail: smoke drifting, a slow wave along it; bobbing with the bound and streaming behind it at speed; coiled behind it lying down
            for k = 1, 7 do
                local sway = (0.035 + 0.05 * k / 7) * math.sin(t * 0.9 - k * 0.55) * (1 - 0.6 * lie) * (1 - 0.5 * fly)
                local drift = 0.03 * math.sin(t * 0.6 - k * 0.7)
                local stream = (if k <= 3 then 0.07 else 0.03) * pace + (if k == 1 then 0.06 * g * onFoot else 0)
                addStance(want, { ["Tail" .. k] = { drift + stream, sway, 0 } }, 1)
            end

            for _, name in SHADOW_BONES do
                local a = want[name] or Vector3.zero
                -- (its hips rise by what each phase of the bound needs to keep every paw on or above the ground, measured in Blender)
                local lift = if name == "Hips"
                    then (0.027 * gathered + 0.014 * stretched + 0.034 * frontLift - SHADOW_LIE_DROP * lie - SHADOW_SINK * sink + 0.2 * hop) * u - drop
                    else 0
                pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- the eyes: quick blinks; a sly half-lid when it looks at you; heavy lids lying down, now and then shut a while; wide as it notices
            s.nextBlink = s.nextBlink or t + 2
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.16
                if a >= 1 then
                    s.nextBlink = t + 2 + math.random() * 3
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local doze = smoothstep(0.3, 0.9, 0.5 + 0.5 * math.sin(t * 0.4))
            local close = math.max(blink, (if s.atYou then 0.22 else 0) * (1 - pace), lie * (0.55 + 0.45 * doze)) * (1 - notice)
            local upper = SHADOW_BLINK_UPPER * close - math.rad(6) * notice
            local lower = SHADOW_BLINK_LOWER * close - math.rad(5) * notice
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(SHADOW_LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(SHADOW_LID_HINGE[side], lower))
            end
        end
    end

    return { animateShadowcoil = animateShadowcoil, SHADOW_BONES = SHADOW_BONES, SHADOW_EYESHINE = SHADOW_EYESHINE, SHADOW_INK = SHADOW_INK, SHADOW_RIM = SHADOW_RIM, SHADOW_SOLE = SHADOW_SOLE, addStance = addStance, shadowDisc = shadowDisc }
end
