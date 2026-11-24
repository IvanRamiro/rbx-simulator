-- The NebulaOwl pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Debris, pose, smoothstep = K.PetRig, K.Debris, K.pose, K.smoothstep

    local animateNebulaOwl -- animateNebulaOwl's section below (its own locals stay in its block)
    do

        -- The Nebula Owl (skinned; the head is its own piece, so it can turn right round under the ruff): it hovers without a sound and already knows what you are about to do. Its wings row slowly, each joint later than the last. Its head
        -- doesn't drift: it snaps to a new place and holds still, as an owl's does, and now and then turns all the way round to look behind it, one brow raised. It blinks one eye at a time. Up is a turn about Z: left wing negative, right positive.
        local OWL_LID_HINGE = { L = Vector3.new(0.9734, -0.1044, -0.204), R = Vector3.new(0.9734, 0.1044, 0.204) }
        local OWL_BLINK_UPPER, OWL_BLINK_LOWER = math.rad(64), math.rad(22)
        local OWL_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        local OWL_STAR_AHEAD = Vector3.new(0, -0.05, -0.9) -- metres from the middle of its box: where the new star is born, before its breast
        local OWL_GATHER_RADIUS = 0.95

        -- Gas drawn in from all round a point, the first part of its special. Blasts.StarsNotYetBorn stops it when the star lights.
        local function owlGather(rig, s)
            local metre = rig.meters
            local at = rig.rootPart.CFrame:PointToWorldSpace(OWL_STAR_AHEAD * metre)
            local holder = Instance.new("Part")
            holder.Name = "OwlGather"
            holder.Anchored = true
            holder.CanCollide = false
            holder.CanTouch = false
            holder.CanQuery = false
            holder.CastShadow = false
            holder.Transparency = 1
            holder.Size = Vector3.one * OWL_GATHER_RADIUS * 2 * metre
            holder.CFrame = CFrame.new(at)
            local gas = Instance.new("ParticleEmitter")
            gas.Texture = "rbxassetid://16867371255"
            gas.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
            gas.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
            gas.Shape = Enum.ParticleEmitterShape.Sphere
            gas.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
            gas.ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward
            gas.Rate = 30
            gas.Lifetime = NumberRange.new(0.55, 0.7)
            gas.Speed = NumberRange.new(OWL_GATHER_RADIUS * metre / 0.62)
            gas.Rotation = NumberRange.new(0, 360)
            gas.RotSpeed = NumberRange.new(-70, 70)
            gas.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.34 * metre), NumberSequenceKeypoint.new(1, 0.16 * metre) })
            gas.Color = ColorSequence.new(Color3.fromRGB(96, 52, 225), Color3.fromRGB(235, 90, 200))
            gas.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.42), NumberSequenceKeypoint.new(0.85, 0.15), NumberSequenceKeypoint.new(1, 0.9) })
            gas.LightEmission = 0.75
            gas.LightInfluence = 0
            gas.LockedToPart = true -- it gathers before its breast, wherever the owl goes (animateNebulaOwl moves it)
            gas.Parent = holder
            -- what the gas is falling into: a small star, growing, so the eye is already there when it lights
            local seed = Instance.new("ParticleEmitter")
            seed.Texture = "rbxassetid://95572555201628"
            seed.Rate = 0
            seed.Lifetime = NumberRange.new(PetRig.NOVA_TIME * PetRig.NOVA_BURST)
            seed.Speed = NumberRange.new(0)
            seed.Rotation = NumberRange.new(0, 360)
            seed.RotSpeed = NumberRange.new(25, 25)
            seed.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05 * metre), NumberSequenceKeypoint.new(1, 0.72 * metre) })
            seed.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.7), NumberSequenceKeypoint.new(1, 0) })
            seed.LightEmission = 1
            seed.LightInfluence = 0
            seed.LockedToPart = true
            seed.Parent = Instance.new("Attachment", holder)
            seed:Emit(1)
            holder.Parent = rig.model.Parent or workspace
            Debris:AddItem(holder, PetRig.NOVA_TIME * PetRig.NOVA_BURST + 1)
            s.gather, s.starAt = gas, at
        end

        function animateNebulaOwl(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > OWL_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special: wings lift and spread, slowly, as gas gathers before its breast; the star lights; one great silent downstroke; and it goes back to looking unimpressed, having known all along
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local open = smoothstep(0, 0.36, progress) * (1 - smoothstep(0.41, 0.47, progress))
            local stroke = smoothstep(0.41, 0.46, progress) * (1 - smoothstep(0.47, 0.76, progress))
            local awe = smoothstep(0.1, 0.38, progress) * (1 - smoothstep(0.5, 0.72, progress))
            if rig.nova and not rig.nova.gathering and progress < PetRig.NOVA_BURST then
                rig.nova.gathering = true
                owlGather(rig, s)
            end
            if s.gather and s.gather.Parent then
                -- the gas keeps before its breast as it follows its player, and the star lights there
                s.starAt = rig.rootPart.CFrame:PointToWorldSpace(OWL_STAR_AHEAD * rig.meters)
                s.gather.Parent.CFrame = CFrame.new(s.starAt)
            end

            -- now and then it turns its head right round to look behind it, in no hurry to turn back
            s.nextBehind = s.nextBehind or t + 6 + math.random() * 8
            local behind = 0
            if t >= s.nextBehind then
                local a = (t - s.nextBehind) / 3.1
                if a >= 1 then
                    s.nextBehind = t + 12 + math.random() * 14
                    s.behindSide = if math.random() < 0.5 then 1 else -1
                elseif pace < 0.25 and nova == 0 then
                    behind = smoothstep(0, 0.2, a) * (1 - smoothstep(0.78, 1, a))
                else
                    s.nextBehind = t + 3
                end
            end

            -- the head doesn't drift: it snaps to a new place and holds still
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 1.4 + math.random() * 3.2
                s.gazeTo = (math.random() - 0.5) * 1.5
                s.nodTo = (math.random() - 0.5) * 0.22
                s.tiltTo = if math.random() < 0.25 then (math.random() - 0.5) * 0.8 else 0
            end
            local calm = (1 - pace * 0.8) * (1 - nova)
            local yawTo = (s.gazeTo or 0) * calm * (1 - behind) + 2.65 * behind * (s.behindSide or 1)
            local snap = math.min(1, dt * (if behind > 0 then 5 else 11))
            s.yaw = (s.yaw or 0) + (yawTo - (s.yaw or 0)) * snap
            s.nod = (s.nod or 0) + (((s.nodTo or 0) * calm + 0.12 * awe) - (s.nod or 0)) * snap
            s.tilt = (s.tilt or 0) + ((s.tiltTo or 0) * calm * (1 - behind) - (s.tilt or 0)) * snap

            -- the wings row, each joint later than the last; flying, it beats and then glides. It makes no sound and it doesn't hurry
            s.beat = (s.beat or 0) + dt * (2 + 4.4 * moving + 1.6 * fly)
            local glide = 0.45 + 0.55 * math.max(0, math.sin(t * 0.7))
            local amp = 0.13 + 0.4 * moving + 0.22 * fly * glide
            local beat = s.beat
            local base = 0.02 - 0.04 * moving + 0.06 * fly
            for _, side in { "L", "R" } do
                local up = if side == "L" then -1 else 1
                pose(m["Wing" .. side .. "1"], CFrame.Angles(0, up * (0.07 * math.cos(beat) * (amp / 0.3) - 0.12 * open), up * (base + amp * math.sin(beat) + 0.34 * open - 0.42 * stroke)))
                pose(m["Wing" .. side .. "2"], CFrame.Angles(0, 0, up * (-0.06 + 0.6 * amp * math.sin(beat - 0.7) + 0.14 * open - 0.1 * stroke)))
                pose(m["Wing" .. side .. "3"], CFrame.Angles(0, 0, up * (-0.04 + 0.7 * amp * math.sin(beat - 1.3) + 0.1 * open - 0.34 * stroke)))
                pose(m["WingP" .. side], CFrame.Angles(0, 0, up * (0.6 * amp * math.sin(beat - 1.9) + 0.2 * open - 0.36 * stroke)))
            end

            -- the body rides each stroke a moment late, and leans into going forward; the head stays level, as an owl's does
            local look = rig.rootPart.CFrame.LookVector
            local heading = math.atan2(-look.X, -look.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.14, -0.3, 0.3) - (s.bank or 0)) * math.min(1, dt * 3)
            local pitch = -0.22 * moving - 0.12 * fly + 0.12 * open
            local rise = 0.1 * amp * math.sin(beat - 0.9) + 0.08 * open + 0.1 * stroke
            pose(m.Body, CFrame.new(0, rise * u, 0) * CFrame.Angles(pitch + 0.015 * math.sin(beat - 1.2), 0, s.bank))
            local breath = math.sin(t * 1.1)
            pose(m.Chest, CFrame.new(0, 0.004 * breath * u, -0.006 * breath * u))
            pose(m.Head, CFrame.new(0, 0.012 * math.sin(beat - 1.5) * u, 0) * CFrame.fromEulerAnglesYXZ(-pitch * 0.85 + s.nod, s.yaw + s.bank * 0.6, s.tilt - s.bank * 0.7))

            -- its lids rest low. It blinks slowly and, more often than not, one eye at a time
            s.nextBlink = s.nextBlink or t + 2
            if t >= s.nextBlink then
                s.nextBlink = t + 2.2 + math.random() * 4.5
                s.blinkAt = t
                local r = math.random()
                s.blinkWhich = if r < 0.35 then "L" elseif r < 0.7 then "R" else "both"
            end
            local shut = 0
            if s.blinkAt and t - s.blinkAt < 0.34 then
                shut = 1 - math.abs(2 * (t - s.blinkAt) / 0.34 - 1)
            end
            s.nextBrow = s.nextBrow or t + 4
            if t >= s.nextBrow then
                s.nextBrow = t + 5 + math.random() * 7
                s.browAt, s.browSide = t, if math.random() < 0.5 then "L" else "R"
            end
            local cock = if s.browAt then smoothstep(0, 0.12, t - s.browAt) * (1 - smoothstep(1.1, 1.5, t - s.browAt)) else 0
            for _, side in { "L", "R" } do
                local up = if side == "L" then -1 else 1
                local mine = if s.blinkWhich == side or s.blinkWhich == "both" then shut else 0
                local widen = math.rad(14) * math.max(awe, behind * 0.5)
                pose(m["LidU" .. side], CFrame.fromAxisAngle(OWL_LID_HINGE[side], -OWL_BLINK_UPPER * mine + widen))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(OWL_LID_HINGE[side], OWL_BLINK_LOWER * mine))
                pose(m["Eye" .. side], CFrame.Angles(s.nod * 0.25, s.yaw * 0.08 * (1 - behind), 0))
                local raised = math.max(awe * 0.8, if s.browSide == side then cock else 0, behind * (if (s.behindSide or 1) == up then 1 else 0.2))
                pose(m["Brow" .. side], CFrame.new(0, 0.014 * raised * u, 0) * CFrame.Angles(0, 0, up * 0.2 * raised))
                -- tufts lie back at speed and prick up at anything
                local offset = if side == "L" then 0 else 1.9
                local flick = math.max(0, math.sin(t * 0.7 + offset)) ^ 16
                pose(m["Tuft" .. side], CFrame.Angles(0.05 * math.sin(t * 0.9 + offset) + 0.5 * moving + 0.26 * fly - 0.12 * awe - 0.14 * flick, 0, up * (0.04 * math.sin(t * 0.6 + offset) + 0.12 * flick)))
                -- legs trail behind it in flight, talons drawn up; at rest they hang, opening a little at the top of the special
                pose(m["Leg" .. side], CFrame.Angles(0.03 * math.sin(t * 0.8 + offset) - 0.5 * pace + 0.2 * open, 0, 0))
                pose(m["Foot" .. side], CFrame.Angles(0.05 * math.sin(t * 1.1 + offset) - 0.6 * pace + 0.28 * open, 0, 0))
            end
            pose(m.BeakLow, CFrame.Angles(-(0.3 * stroke + 0.14 * cock * (if s.browSide == "L" then 1 else 0)), 0, 0))

            -- the tail steers and fans
            local fan = 0.04 + 0.1 * open + 0.1 * fly + 0.05 * math.abs(s.bank) * 3
            pose(m.Tail, CFrame.Angles(-pitch * 0.5 + 0.04 * math.sin(beat - 2.2) - 0.1 * moving, s.bank * 0.5, s.bank * 0.4))
            pose(m.TailL, CFrame.Angles(0, -fan, 0))
            pose(m.TailR, CFrame.Angles(0, fan, 0))

            -- the new stars in its wings breathe, each its own way; a little gas always leaks from the wingtips, more as it moves
            for index, name in { "StarsL", "StarsR" } do
                local part = rig.parts[name]
                if part then
                    local base2 = rig.profile.GlowColors["d6b4ff"]
                    part.Color = base2:Lerp(Color3.new(1, 1, 1), 0.28 * math.max(0, math.sin(t * 1.9 + index * 2.3)) ^ 3 + 0.5 * stroke)
                end
            end
            if not s.wisps then
                s.wisps = {}
                for _, name in { "WingPL", "WingPR" } do
                    local bone = rig.points[name]
                    if bone then
                        local gas = Instance.new("ParticleEmitter")
                        gas.Name = "Gas"
                        gas.Texture = "rbxassetid://16172858603"
                        gas.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
                        gas.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
                        gas.Rate = 0.8
                        gas.Lifetime = NumberRange.new(1.5, 2.3)
                        gas.Speed = NumberRange.new(0.1 * rig.unit, 0.3 * rig.unit)
                        gas.SpreadAngle = Vector2.new(180, 180)
                        gas.Drag = 0.8
                        gas.Rotation = NumberRange.new(0, 360)
                        gas.RotSpeed = NumberRange.new(-14, 14)
                        gas.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * rig.unit), NumberSequenceKeypoint.new(1, 0.42 * rig.unit) })
                        gas.Color = ColorSequence.new(Color3.fromRGB(150, 96, 240), Color3.fromRGB(220, 110, 200))
                        gas.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.62), NumberSequenceKeypoint.new(1, 1) })
                        gas.LightEmission = 0.35
                        gas.LightInfluence = 0.5
                        gas.Parent = bone
                        table.insert(s.wisps, gas)
                    end
                end
            end
            for _, gas in s.wisps do
                gas.Rate = 0.8 + 2.2 * pace
            end
        end
    end

    return { animateNebulaOwl = animateNebulaOwl }
end
