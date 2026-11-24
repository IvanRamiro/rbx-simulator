-- The JadeWyrmTurtle pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep = K.PetRig, K.pose, K.smoothstep

    local animateJadeWyrmTurtle, dropToGround, turtleRay -- animateJadeWyrmTurtle's section below (its own locals stay in its block)
    do

        -- The Jade Wyrm Turtle (skinned): half wyrm, half mountain, and in no hurry. Everything it does is slow and carries weight: it treads one foot at a time and the whole crag rocks over it, its long neck
        -- wanders on its own, the plum and the pine sway after the shell does. Now and then it turns its neck right round to look at its garden. It stands on the ground rather than hovering (Body drops to it).
        local TURTLE_LEADS = { FL = 0, BR = 0.35, FR = math.pi, BL = math.pi + 0.35 }
        local TURTLE_LID_HINGE = { L = Vector3.new(0.539, 0.0867, -0.8379), R = Vector3.new(0.539, -0.0867, 0.8379) }
        local TURTLE_BLINK_UPPER, TURTLE_BLINK_LOWER = math.rad(38), math.rad(16)
        local TURTLE_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        local TURTLE_SOLE = 0.96 -- metres from the middle of its box down to the soles of its feet
        local TURTLE_PADS = { PadA = Vector3.new(-0.5, 0.2, -0.8), PadB = Vector3.new(0.6, 0.2, -0.3), PadC = Vector3.new(0, 1, 0.2) } -- which way each mass of blossom swells

        turtleRay = RaycastParams.new()
        turtleRay.RespectCanCollide = true

        function dropToGround(rig, s, t, u, fly, sole)
            local from = rig.rootPart.Position
            s.nextGround = s.nextGround or 0
            if t >= s.nextGround then
                s.nextGround = t + 0.15
                local hit = workspace:Raycast(from, Vector3.new(0, -8 * u, 0), turtleRay)
                local onCharacter = hit and hit.Instance.Parent and hit.Instance.Parent:FindFirstChildOfClass("Humanoid")
                if not onCharacter then -- (a player walking under it: keep what it had)
                    s.groundAt = if hit then hit.Position.Y else nil
                end
            end
            -- The ground's height eases (a step, a slope, a ledge), but the root's own rise and fall (the follow bob) is taken out every frame:
            -- eased with the ground, the bob lagged and the pet floated up off its feet and back (seen in Studio, 2026-11-10).
            local dt = math.min(1, rig.deltaTime * 4)
            if s.groundAt then
                s.ground = if s.ground then s.ground + (s.groundAt - s.ground) * dt else s.groundAt
            end
            local wantGrounded = if s.groundAt then 1 else 0
            s.grounded = if s.grounded then s.grounded + (wantGrounded - s.grounded) * dt else wantGrounded
            local height = if s.ground then math.clamp(from.Y - sole * u - s.ground, -0.3 * u, 2.6 * u) else 0
            s.drop = height * s.grounded * (1 - fly)
            return s.drop
        end

        function animateJadeWyrmTurtle(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > TURTLE_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, TURTLE_SOLE)

            -- the special: one forefoot rises, slowly, the whole mountain leaning off it; it comes down; the mountain rings; and the garden has grown
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local raise = smoothstep(0, 0.37, progress) * (1 - smoothstep(0.385, 0.425, progress))
            local plant = smoothstep(0.40, 0.43, progress) * (1 - smoothstep(0.46, 0.9, progress))
            local ring = plant * math.sin(math.max(0, progress - 0.42) * 62)
            local grown = smoothstep(0.43, 0.6, progress) * (1 - smoothstep(0.8, 1, progress))

            -- it looks back at its garden, the long way round
            s.nextGarden = s.nextGarden or t + 9 + math.random() * 8
            local garden = 0
            if t >= s.nextGarden then
                local a = (t - s.nextGarden) / 5.2
                if a >= 1 then
                    s.nextGarden = t + 15 + math.random() * 14
                    s.gardenSide = if math.random() < 0.5 then 1 else -1
                elseif pace < 0.2 and nova == 0 then
                    garden = smoothstep(0, 0.34, a) * (1 - smoothstep(0.66, 1, a))
                else
                    s.nextGarden = t + 4
                end
            end
            garden *= s.gardenSide or 1
            -- a slow chew over nothing
            s.nextChew = s.nextChew or t + 5 + math.random() * 8
            local chew = 0
            if t >= s.nextChew then
                local a = (t - s.nextChew) / 2.4
                if a >= 1 then
                    s.nextChew = t + 9 + math.random() * 12
                elseif pace < 0.4 and nova == 0 then
                    chew = math.abs(math.sin(a * math.pi * 3)) * math.sin(a * math.pi)
                end
            end

            -- the tread: one foot at a time. A foot rises out and forward, is set down, and the body rolls over it
            s.stride = (s.stride or 0) + dt * (3.6 * moving)
            s.swim = (s.swim or 0) + dt * 1.7 * fly
            local stride, stroke = s.stride, math.sin(s.swim)
            local breath = math.sin(t * 0.85)
            for key, lead in TURTLE_LEADS do
                local phase = stride + lead
                local a, lift = math.sin(phase), moving * math.max(0, math.cos(phase)) ^ 1.4
                local out = if string.sub(key, 2, 2) == "L" then -1 else 1 -- a turn about Z that swings this foot out and up
                local front = string.sub(key, 1, 1) == "F"
                local swingX = moving * 0.3 * a + 0.012 * math.sin(t * 0.6 + lead)
                local outZ = 0.26 * lift
                local bendZ = -0.44 * lift
                local footX = -swingX * 0.9 - 0.14 * lift
                -- on the air it rows, as sea turtles do: long slow strokes from the front, the hind feet trailing
                if front then
                    swingX += fly * (0.06 + 0.5 * stroke)
                    outZ += fly * (0.34 + 0.12 * stroke)
                    bendZ += fly * 0.26
                    footX += fly * (0.16 * stroke - 0.62)
                else
                    swingX += fly * (-0.52 + 0.14 * stroke)
                    outZ += fly * 0.2
                    bendZ += fly * 0.12
                    footX += fly * -0.5
                end
                if key == "FR" then
                    swingX += 0.14 * raise
                    outZ += 0.62 * raise
                    bendZ -= 0.96 * raise
                    footX += 0.32 * raise + 0.04 * raise * math.sin(t * 9)
                end
                pose(m["Leg" .. key .. "1"], CFrame.Angles(swingX, 0, out * outZ))
                pose(m["Leg" .. key .. "2"], CFrame.Angles(0, 0, out * bendZ))
                pose(m["Foot" .. key], CFrame.Angles(footX, 0, 0))
            end

            -- the body rolls over the foot that bears it, and a mountain doesn't bob quickly. It leans into a turn only a little
            local look = rig.rootPart.CFrame.LookVector
            local heading = math.atan2(-look.X, -look.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.05, -0.1, 0.1) - (s.bank or 0)) * math.min(1, dt * 2)
            local rollOver = moving * 0.036 * math.sin(stride + 0.5)
            local fall = moving * 0.014 * math.cos(2 * stride + 0.6)
            pose(m.Body, CFrame.new(0, (-drop / u + 0.006 * breath + fall + 0.13 * raise - 0.025 * plant + 0.05 * fly + 0.014 * math.sin(s.swim + 0.8) * fly) * u, 0)
                * CFrame.Angles(0.004 * breath + 0.1 * raise - 0.05 * plant + 0.09 * fly + 0.03 * stroke * fly, 0.012 * math.sin(t * 0.27) + moving * 0.018 * math.sin(stride), rollOver + 0.1 * raise + s.bank))
            pose(m.Shell, CFrame.new(0, (0.004 * breath + 0.012 * ring) * u, 0))

            -- the neck: its gaze wanders and the neck follows late; at each joint a little less of the body's roll
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2.6 + math.random() * 4.5
                s.gazeTo = (math.random() - 0.5) * 0.9
                s.gazeUp = (math.random() - 0.5) * 0.14
            end
            local calm = (1 - pace * 0.7) * (1 - nova) * (1 - math.abs(garden))
            s.gaze = (s.gaze or 0) + ((s.gazeTo or 0) * calm - (s.gaze or 0)) * math.min(1, dt * 1.1)
            s.tip = (s.tip or 0) + ((s.gazeUp or 0) * calm - (s.tip or 0)) * math.min(1, dt * 0.9)
            local sway = moving * 0.05 * math.sin(stride - 0.6)
            local lift = 0.2 * raise - 0.1 * plant
            local reach = fly * 0.28 + moving * 0.1
            pose(m.Neck1, CFrame.Angles(0.012 * math.sin(t * 0.85 - 0.5) + lift * 0.8 - reach * 0.6, s.gaze * 0.14 + 0.28 * garden - sway, -rollOver * 0.5 - 0.06 * raise))
            pose(m.Neck2, CFrame.Angles(0.01 * math.sin(t * 0.85 - 0.9) + lift - reach * 0.7 + 0.02 * ring, s.gaze * 0.2 + 0.42 * garden - sway * 0.7, -0.04 * raise))
            pose(m.Neck3, CFrame.Angles(0.01 * math.sin(t * 0.85 - 1.3) + lift * 0.7 - reach * 0.2 + s.tip * 0.5 - 0.03 * ring + 0.1 * math.abs(garden), s.gaze * 0.26 + 0.45 * garden - sway * 0.3, 0))
            local lookUp = math.abs(garden)
            pose(m.Neck4, CFrame.Angles(s.tip * 0.5 + reach * 0.5 - lift * 0.3, s.gaze * 0.3 + 0.31 * garden, 0))
            pose(m.Head, CFrame.Angles(0.008 * math.sin(t * 0.85 - 1.8) + s.tip + reach * 0.6 - lift * 0.55 - 0.04 * ring + 0.24 * lookUp, s.gaze * 0.4 + 0.28 * garden, 0.05 * math.sin(t * 0.31) * calm))
            pose(m.Jaw, CFrame.Angles(-(0.14 * chew + 0.14 * raise + 0.24 * plant + 0.02 * math.max(0, breath)), 0, 0))

            -- old eyes: a slow blink, closing as the foot comes down, and they look about ahead of the head
            s.nextBlink = s.nextBlink or t + 2.5
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.62
                if a >= 1 then
                    s.nextBlink = t + 3.2 + math.random() * 5
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local shut = math.max(blink, 0.45 * math.abs(garden), plant, 0.55 * chew)
            for _, side in { "L", "R" } do
                pose(m["Eye" .. side], CFrame.Angles(s.tip * 0.5, s.gaze * 0.7 + 0.4 * garden, 0))
                pose(m["LidU" .. side], CFrame.fromAxisAngle(TURTLE_LID_HINGE[side], -TURTLE_BLINK_UPPER * shut))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(TURTLE_LID_HINGE[side], TURTLE_BLINK_LOWER * shut))
                local sign = if side == "L" then -1 else 1
                local offset = if side == "L" then 0 else 1.7
                pose(m["Frill" .. side], CFrame.Angles(0.04 * math.sin(t * 1.1 + offset), sign * (0.07 * math.sin(t * 0.8 + offset) - 0.14 * pace + 0.1 * raise), 0))
            end

            -- the tail: a long lazy wave that starts at the body; on the air it trails straight
            local waveSpeed = 0.9 + 1.6 * moving + 0.8 * fly
            for k = 1, 6 do
                local f = k / 6
                pose(m["Tail" .. k], CFrame.Angles(0.012 * math.sin(t * 0.7 - k * 0.5) - 0.03 * fly + 0.03 * raise - 0.05 * ring * (1 - f),
                    (0.035 + 0.04 * f) * (1 + 0.7 * moving) * math.sin(t * waveSpeed - k * 0.62), 0))
            end
            pose(m.TailTip, CFrame.Angles(0.1 * math.sin(t * 0.8) - 0.1 * fly, 0.12 * math.sin(t * 1.2 - 4), 0))

            -- the garden: a breeze of its own, and every roll of the shell reaching the trees a moment late
            s.treeLag = (s.treeLag or 0) + ((rollOver + 0.1 * raise - 0.06 * plant) - (s.treeLag or 0)) * math.min(1, dt * 2.4)
            local gust = 0.5 + 0.5 * math.sin(t * 0.37)
            local windX, windZ = 0.012 * gust * math.sin(t * 1.3), 0.012 * gust * math.sin(t * 1.05 + 1)
            local shake = 0.05 * ring + 0.1 * fly * math.sin(t * 2.1) * 0.2
            pose(m.Plum1, CFrame.Angles(windX + 0.3 * shake + 0.03 * fly, 0, s.treeLag * 0.4 + windZ))
            pose(m.Plum2, CFrame.Angles(windX * 1.4 + 0.5 * shake, 0.01 * math.sin(t * 0.7), s.treeLag * 0.7 + windZ * 1.4))
            local padIndex = 0
            for name, out in TURTLE_PADS do
                padIndex += 1
                local at = out * (0.008 * math.sin(t * 1.2 + padIndex * 1.9) + 0.055 * grown + 0.03 * ring) * u
                pose(m[name], CFrame.new(at) * CFrame.Angles(0.02 * math.sin(t * 0.9 + padIndex), 0, 0.02 * math.sin(t * 0.8 + padIndex * 2.3)))
            end
            pose(m.Pine1, CFrame.Angles(windX * 0.7 + 0.25 * shake, 0, s.treeLag * 0.45))
            for index, name in { "PineA", "PineB", "PineC" } do
                pose(m[name], CFrame.Angles(0.016 * math.sin(t * 1.05 + index * 1.4) + 0.3 * shake, 0, 0.022 * gust * math.sin(t * 0.95 + index * 2.1)))
            end

            -- petals, always a few, drifting down off the plum: more when it walks, a flurry when it stamps (Blasts.BetweenSteps)
            if not s.petals then
                s.petals = {}
                for name in TURTLE_PADS do
                    local bone = rig.points[name]
                    if bone then
                        local petals = Instance.new("ParticleEmitter")
                        petals.Name = "Petals"
                        petals.Texture = "rbxassetid://87701005821132"
                        petals.Rate = 0.5
                        petals.Lifetime = NumberRange.new(2.6, 4)
                        petals.Speed = NumberRange.new(0.15 * rig.unit, 0.5 * rig.unit)
                        petals.SpreadAngle = Vector2.new(180, 180)
                        petals.Acceleration = Vector3.new(0.12 * rig.unit, -0.42 * rig.unit, 0)
                        petals.Drag = 0.8
                        petals.Rotation = NumberRange.new(0, 360)
                        petals.RotSpeed = NumberRange.new(-110, 110)
                        petals.Size = NumberSequence.new(0.036 * rig.unit)
                        petals.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.08, 0), NumberSequenceKeypoint.new(0.8, 0), NumberSequenceKeypoint.new(1, 1) })
                        petals.LightEmission = 0
                        petals.LightInfluence = 0.9
                        petals.Parent = bone
                        s.petals[name] = petals
                    end
                end
            end
            for _, petals in s.petals do
                petals.Rate = 0.4 + 0.5 * moving
            end
        end
    end

    return { animateJadeWyrmTurtle = animateJadeWyrmTurtle, dropToGround = dropToGround, turtleRay = turtleRay }
end
