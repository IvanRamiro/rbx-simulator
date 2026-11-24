-- The CometStag pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, SPARKLE, pose, smoothstep, addStance, dropToGround = K.PetRig, K.SPARKLE, K.pose, K.smoothstep, K.addStance, K.dropToGround

    local animateCometStag, STAG_BONES, STAG_DUST, STAG_ICE, STAG_ION, stagGlow -- animateCometStag's section below (its own locals stay in its block)
    do

        -- The Comet Stag (skinned): a powerful night-blue stag whose antlers sweep back like a comet's two tails, a comet's nucleus glowing on its brow. It
        -- stands proud, head high, its big ears turning on their own; now and then it tosses its antlers or paws the ground; still a long while, it lies down,
        -- legs folded under it. It trots on the ground; in the air it runs on nothing in long bounds, a comet's trail streaming from its brow, and comet dust
        -- drifts off the tips of its antlers.
        local STAG_FAR = 110 -- studs from the camera past which nobody can see it fidget: its bones rest
        local STAG_SOLE = 0.7009 -- metres from the middle of its box down to its hooves: it stands on the ground
        local STAG_LID_HINGE = { L = Vector3.new(0.5963, -0.1038, -0.796), R = Vector3.new(0.5963, 0.1038, 0.796) } -- both lids of an eye turn on this line
        local STAG_BLINK_UPPER, STAG_BLINK_LOWER = math.rad(58), math.rad(26)
        local STAG_NUCLEUS = Vector3.new(0, 0.966, -0.452) -- its brow's nucleus, in the model's axes (metres)
        local STAG_TIPS = { Vector3.new(-0.285, 1.2, 0.33), Vector3.new(0.285, 1.2, 0.33) } -- the ends of its two palms, where the comet dust comes off
        STAG_ICE, STAG_ION, STAG_DUST = Color3.fromRGB(234, 246, 255), Color3.fromRGB(110, 190, 255), Color3.fromRGB(255, 214, 140)
        local STAG_TROT = { FL = 0, BR = 0, FR = math.pi, BL = math.pi } -- a trot: diagonal pairs together

        local function stagLegs(f, b)
            local out = {}
            for _, side in { "L", "R" } do
                for k = 1, 3 do
                    out["LegF" .. side .. k] = { f[k], 0, 0 }
                    out["LegB" .. side .. k] = { b[k], 0, 0 }
                end
            end
            return out
        end

        local function stagStance(base, f, b)
            for bone, a in stagLegs(f, b) do
                base[bone] = a
            end
            return base
        end

        -- its stances, each searched in Blender against the ground and for torn skin: the same numbers as comet_stag.py's REAR, LIE and LEAP
        local STAG_REAR = stagStance({ Body = { 0.573, 0, 0 }, Neck1 = { -0.15, 0, 0 }, Head = { -0.038, 0, 0 } }, { -0.067, -0.169, 0.906 }, { -0.249, -0.224, 0.02 })
        local STAG_REAR_DROP = 0.061
        local STAG_LIE = stagStance({ Body = { -0.171, 0, 0 }, Head = { 0.27, 0, 0 } }, { 0.569, -2.153, -0.182 }, { -0.2, -1.438, 0.638 })
        local STAG_LIE_DROP = 0.311
        local STAG_LEAP = stagStance({ Body = { -0.039, 0, 0 }, Head = { 0.2, 0, 0 }, Tail1 = { 0.3, 0, 0 } }, { 0.679, -1.558, 0.307 }, { -0.39, 0.255, 0.091 })
        local STAG_TOSS = { Neck1 = { -0.25, 0, 0 }, Neck2 = { -0.2, 0, 0 }, Head = { -0.35, 0, 0 } }
        local STAG_PAW = { LegFL1 = { 0.55, 0, 0 }, LegFL2 = { -1.1, 0, 0 }, LegFL3 = { 0.3, 0, 0 }, Neck1 = { 0.1, 0, 0 }, Head = { 0.3, 0, 0 } }

        local function stagBones()
            local bones = { "Hips", "Body", "Chest", "Neck1", "Neck2", "Head", "EyeL", "EyeR", "EarL", "EarR", "Tail1", "Tail2" }
            for _, key in { "FL", "FR", "BL", "BR" } do
                for k = 1, 3 do
                    table.insert(bones, "Leg" .. key .. k)
                end
                table.insert(bones, "Hoof" .. key)
            end
            return bones
        end
        STAG_BONES = stagBones() -- every bone its stances pose (the lids turn on their hinges on their own)

        -- where a point of the model, given in its axes, is at rest in the world: measured from the nucleus glow piece, which (a skinned part) stays where it
        -- was bound. Called before any pose, so the head bone stands at rest too.
        local function stagAtRest(rig, point)
            local nucleus = rig.parts.Nucleus
            if not nucleus then
                return nil
            end
            return nucleus.Position + rig.rootPart.CFrame:VectorToWorldSpace((point - STAG_NUCLEUS) * rig.meters)
        end

        -- its light, its comet trail and the dust off its antlers: all on the head's bone, so they go where its head goes
        function stagGlow(rig, s)
            s.glowMade = true
            local head = rig.points.Head
            local at = stagAtRest(rig, STAG_NUCLEUS)
            if not (head and at) then
                return
            end
            local function attach(name, world)
                local a = Instance.new("Attachment")
                a.Name = name
                a.CFrame = head.TransformedWorldCFrame:ToObjectSpace(CFrame.new(world))
                a.Parent = head
                return a
            end
            local nucleus = attach("Nucleus", at)
            s.nucleus = nucleus
            local light = Instance.new("PointLight")
            light.Name = "PulseLight"
            light.Color = STAG_ICE
            light.Range = 5 * rig.unit
            light.Brightness = 1.4
            light.Shadows = false
            light.Parent = nucleus
            rig.light = light
            -- the comet's trail, streaming back from its brow when it runs on the air
            local up = rig.rootPart.CFrame.UpVector * 0.05 * rig.meters
            local top, bottom = attach("TrailTop", at + up), attach("TrailBottom", at - up)
            local trail = Instance.new("Trail")
            trail.Name = "CometTrail"
            trail.Attachment0, trail.Attachment1 = top, bottom
            trail.Lifetime = 0.7
            trail.FaceCamera = true
            trail.LightEmission = 1
            trail.LightInfluence = 0
            trail.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0.15) })
            trail.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, STAG_ICE), ColorSequenceKeypoint.new(0.35, STAG_ION), ColorSequenceKeypoint.new(1, STAG_DUST) })
            trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(1, 1) })
            trail.Enabled = false
            trail.Parent = head
            s.trail = trail
            -- comet dust drifting off the tips of its antlers
            for k, tip in STAG_TIPS do
                local world = stagAtRest(rig, tip)
                local a = attach("Tip" .. k, world)
                local dust = Instance.new("ParticleEmitter")
                dust.Name = "CometDust"
                dust.Texture = SPARKLE
                dust.Rate = 3
                dust.Lifetime = NumberRange.new(0.8, 1.4)
                dust.Speed = NumberRange.new(0.05 * rig.unit, 0.15 * rig.unit)
                dust.SpreadAngle = Vector2.new(60, 60)
                dust.Acceleration = Vector3.new(0, -0.05 * rig.unit, 0)
                dust.Drag = 1.5
                dust.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.06 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
                dust.Color = ColorSequence.new(STAG_DUST, STAG_ION)
                dust.LightEmission = 1
                dust.LightInfluence = 0
                dust.Parent = a
            end
        end

        function animateCometStag(rig, s, moving, fly, nova)
            if not s.glowMade then
                stagGlow(rig, s) -- before any pose: the head bone is at rest
            end
            local camera = workspace.CurrentCamera
            if s.trail then
                s.trail.Enabled = fly > 0.4
            end
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > STAG_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, STAG_SOLE)

            -- the special, Once in a Lifetime: it rears, forelegs striking (to 0.4); at the burst (0.42) a comet leaves its brow and arcs across the sky
            -- (Blasts.OnceInALifetime); it watches it go, head raised and turning, and comes down
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local rise = smoothstep(0.04, 0.32, progress) * (1 - smoothstep(0.55, 0.78, progress))
            local watch = smoothstep(0.42, 0.55, progress) * (1 - smoothstep(0.82, 0.97, progress))
            local special = progress > 0

            -- still a long while, it lies down; now and then it tosses its antlers or paws the ground
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            local wantLie = if s.still > 10 then 1 else 0
            s.lie = (s.lie or 0) + (wantLie - (s.lie or 0)) * math.min(1, dt * (if wantLie > (s.lie or 0) then 1 else 5))
            local lie = smoothstep(0, 1, s.lie)
            s.nextFidget = s.nextFidget or t + 4
            if t >= s.nextFidget then
                s.fidgetAt, s.fidgetKind = t, if math.random() < 0.55 then "toss" else "paw"
                s.nextFidget = t + 6 + math.random() * 5
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / 1.4, 0, 1) else 1
            local fidget = math.sin(math.pi * env) * (1 - pace) * (1 - lie) * (1 - rise)

            -- the trot, diagonal pairs together; in the air a bounding run on nothing, the legs reaching and folding
            s.stride = (s.stride or 0) + dt * (7 * moving + 6 * fly)
            local onFoot = moving * (1 - fly)
            local want = {}
            addStance(want, STAG_REAR, rise)
            addStance(want, STAG_LIE, lie * (1 - rise))
            addStance(want, STAG_LEAP, fly * (0.55 + 0.45 * math.sin(s.stride)))
            addStance(want, STAG_TOSS, if s.fidgetKind == "toss" then fidget else 0)
            addStance(want, STAG_PAW, if s.fidgetKind == "paw" then fidget * (0.6 + 0.4 * math.sin(t * 9)) else 0)
            for key, lead in STAG_TROT do
                local phase = s.stride + lead
                local swing, lift = math.sin(phase), math.max(0, math.cos(phase))
                local stance
                if string.sub(key, 1, 1) == "F" then
                    stance = { ["Leg" .. key .. "1"] = { 0.35 * swing, 0, 0 }, ["Leg" .. key .. "2"] = { 0.15 * lift, 0, 0 }, ["Leg" .. key .. "3"] = { -1.0 * lift, 0, 0 },
                        ["Hoof" .. key] = { -0.3 * lift, 0, 0 } }
                else
                    stance = { ["Leg" .. key .. "1"] = { -0.35 * swing, 0, 0 }, ["Leg" .. key .. "2"] = { -0.3 * lift, 0, 0 }, ["Leg" .. key .. "3"] = { 0.6 * lift, 0, 0 } } -- (signs found by a search in Blender: this folds the hock up)
                end
                addStance(want, stance, onFoot)
            end

            -- the body: breathing, banking on turns; head high and level as it trots
            local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.18, 0.18) - (s.bank or 0)) * math.min(1, dt * 3)
            local breath = math.sin(t * 1.1)
            addStance(want, { Hips = { 0, 0, s.bank * pace }, Chest = { 0.012 * breath, 0, 0 }, Neck1 = { -0.05 * onFoot, 0, 0 } }, 1)

            -- its gaze: calm, watchful, now and then on you; up and across the sky after its comet
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2.5 + math.random() * 3.5
                s.atYou = math.random() < 0.45
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.3
            end
            local calm = (1 - 0.7 * pace) * (1 - rise)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm - 0.6 * watch * smoothstep(0.45, 0.8, progress)
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.25, 0.3) else s.gazePitch) * calm + 0.45 * watch
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.5)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.5)
            addStance(want, {
                Neck2 = { 0.3 * s.pitch, 0.35 * s.yaw * (1 - 0.4 * lie), 0 }, Head = { 0.4 * s.pitch, 0.5 * s.yaw * (1 - 0.4 * lie), 0 },
                EyeL = { 0.2 * s.pitch, 0.2 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
            }, 1)

            -- the ears: big and turning on their own, now and then flicking; laid back on the wing
            for _, side in { "L", "R" } do
                local sign = if side == "L" then 1 else -1
                local swivel = math.max(0, math.sin(t * 0.55 + (if side == "L" then 0 else 2.4))) ^ 8
                local flick = math.max(0, math.sin(t * 3.3 + (if side == "L" then 1 else 4))) ^ 30
                addStance(want, { ["Ear" .. side] = { -0.1 * swivel + 0.15 * flick - 0.4 * fly, sign * (0.45 * swivel + 0.3 * fly), 0 } }, 1)
            end

            -- the tail: a short flick now and then; raised in the bound
            local flick = math.max(0, math.sin(t * 1.7)) ^ 16
            addStance(want, { Tail1 = { 0.4 * flick + 0.2 * fly + 0.15 * onFoot, 0.15 * math.sin(t * 7) * flick, 0 } }, 1)

            for _, name in STAG_BONES do
                local a = want[name] or Vector3.zero
                local lift = if name == "Hips"
                    then (-STAG_REAR_DROP * rise - STAG_LIE_DROP * lie * (1 - rise) + 0.012 * onFoot * math.abs(math.sin(s.stride))) * u - drop
                    else 0
                pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- the eyes: slow blinks; wide as it watches its comet go
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.22
                if a >= 1 then
                    s.nextBlink = t + 3 + math.random() * 4
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local doze = smoothstep(0.3, 0.9, 0.5 + 0.5 * math.sin(t * 0.3))
            local close = math.max(blink, lie * 0.5 * doze) * (1 - watch)
            local upper = STAG_BLINK_UPPER * close - math.rad(6) * watch
            local lower = STAG_BLINK_LOWER * close - math.rad(4) * watch
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(STAG_LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(STAG_LID_HINGE[side], lower))
            end
        end
    end

    return { animateCometStag = animateCometStag, STAG_BONES = STAG_BONES, STAG_DUST = STAG_DUST, STAG_ICE = STAG_ICE, STAG_ION = STAG_ION, stagGlow = stagGlow }
end
