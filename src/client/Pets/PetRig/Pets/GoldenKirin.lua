-- GoldenKirin: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Players, TweenService, SPARKLE, tweenAfter, pose, smoothstep, Blasts, addStance, dropToGround = K.PetRig, K.Players, K.TweenService, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.addStance, K.dropToGround


    do
        -- The Golden Kirin (skinned): a radiant celestial kirin, pearl-white, its legs dipped in gold, gold flame-scrolls on its shoulders and haunches,
        -- two gold crescent horns, long gold barbels, a mane and tail of silk ribbons, big golden sun-eyes, a sunburst arc of light behind its head and a lotus
        -- of light under each hoof: it never touches the ground. It stands proud and gentle, its silk stirring in a breeze nothing else feels, its halo
        -- rocking softly, the lotuses turning slowly under it; it looks at you; now and then it lifts a foreleg high and sets it down, bows its head, or
        -- swishes its tail; still a long while, it lies down on the air. It walks in a high-stepping prance; in the air it bounds on nothing, a ribbon of
        -- light streaming from its tail. Its special, Lotus Bloom: it rears, forelegs folded high, its halo flaring (to 0.4); at the burst (0.42:
        -- Blasts.LotusBloom) a great lotus of golden light opens on the air beneath it, a ring of light running out across the ground and motes rising; it
        -- comes down and bows.
        local KG = {
            FAR = 110, -- studs from the camera past which nobody can see it fidget: its bones rest
            SOLE = 0.5325, -- metres from the middle of its box (the root at 0 to its halo's top, 1.0769) down to its lotuses (0.006): they rest on the ground
            LID_HINGE = { L = Vector3.new(0.7877, -0.052, -0.6139), R = Vector3.new(0.7877, 0.052, 0.6139) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(56),
            BLINK_LOWER = math.rad(28),
            GOLD = Color3.fromRGB(255, 214, 120),
            LIGHT = Color3.fromRGB(255, 244, 206),
            DEEP = Color3.fromRGB(236, 170, 60),
            PETAL = Color3.fromRGB(255, 168, 40),
            TROT = { FL = 0, BR = 0, FR = math.pi, BL = math.pi }, -- diagonal pairs together
            LOTUS_TURN = { FL = 0.35, FR = -0.3, BL = -0.32, BR = 0.28 }, -- how fast each lotus turns under its hoof (radians a second)
            PRANCE = { LegFL1 = { 0.7, 0, 0 }, LegFL2 = { -1.3, 0, 0 }, LegFL3 = { 0.6, 0, 0 }, Neck1 = { -0.12, 0, 0 }, Head = { 0.15, 0, 0 }, Tail1 = { 0.35, 0, 0 } },
            BOW = { Neck1 = { 0.3, 0, 0 }, Neck2 = { 0.25, 0, 0 }, Head = { 0.2, 0, 0 } },
            BONES = { "Hips", "Body", "Chest", "Neck1", "Neck2", "Head", "EyeL", "EyeR", "EarL", "EarR", "Tail1", "Tail2", "Tail3", "Halo" },
        }
        for _, key in { "FL", "FR", "BL", "BR" } do
            for k = 1, 3 do
                table.insert(KG.BONES, "Leg" .. key .. k)
            end
            table.insert(KG.BONES, "Hoof" .. key)
        end

        function KG.stance(base, f, b)
            for _, side in { "L", "R" } do
                for k = 1, 3 do
                    base["LegF" .. side .. k] = { f[k], 0, 0 }
                    base["LegB" .. side .. k] = { b[k], 0, 0 }
                end
            end
            return base
        end

        -- its stances, each searched in Blender against the ground and for torn skin: the same numbers as golden_kirin.py's REAR, LIE and LEAP
        KG.REAR = KG.stance({ Body = { 0.5, 0, 0 }, Neck1 = { -0.15, 0, 0 }, Head = { -0.05, 0, 0 } }, { -0.1, -0.5, 1.2 }, { -0.25, -0.2, 0.05 })
        KG.REAR_DROP = 0.042
        KG.LIE = KG.stance({ Body = { -0.1, 0, 0 }, Head = { 0.25, 0, 0 } }, { 0.4, -2.1, 0 }, { -0.4, -0.65, 1.8 })
        KG.LIE_DROP = 0.19
        KG.LEAP = KG.stance({ Body = { -0.04, 0, 0 }, Head = { 0.2, 0, 0 }, Tail1 = { 0.3, 0, 0 } }, { 0.6, -1.4, 0.3 }, { -0.4, 0.25, 0.1 })

        function KG.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        -- its light (on the halo's bone, so it goes where its head goes), a few motes drifting off the halo, and the ribbon of light off its tail in the air
        function KG.glow(rig, s)
            s.glowMade = true
            local halo, tail = rig.points.Halo, rig.points.Tail3
            if not halo then
                return
            end
            local at = Instance.new("Attachment")
            at.Name = "HaloLight"
            at.Parent = halo
            local light = Instance.new("PointLight")
            light.Name = "PulseLight"
            light.Color = KG.GOLD
            light.Range = 5 * rig.unit
            light.Brightness = 1.2
            light.Shadows = false
            light.Parent = at
            rig.light = light
            local motes = Instance.new("ParticleEmitter")
            motes.Name = "HaloMotes"
            motes.Texture = SPARKLE
            motes.Rate = 2.5
            motes.Lifetime = NumberRange.new(1.2, 2)
            motes.Speed = NumberRange.new(0.04 * rig.unit, 0.12 * rig.unit)
            motes.SpreadAngle = Vector2.new(180, 180)
            motes.Acceleration = Vector3.new(0, 0.08 * rig.unit, 0)
            motes.Drag = 1
            motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.05 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
            motes.Color = ColorSequence.new(KG.LIGHT, KG.GOLD)
            motes.LightEmission = 1
            motes.LightInfluence = 0
            motes.Parent = at
            if tail then
                local top, bottom = Instance.new("Attachment"), Instance.new("Attachment")
                top.Position, bottom.Position = Vector3.new(0, 0.04 * rig.meters, 0), Vector3.new(0, -0.04 * rig.meters, 0)
                top.Parent, bottom.Parent = tail, tail
                local trail = Instance.new("Trail")
                trail.Name = "SilkTrail"
                trail.Attachment0, trail.Attachment1 = top, bottom
                trail.Lifetime = 0.5
                trail.FaceCamera = true
                trail.LightEmission = 1
                trail.LightInfluence = 0
                trail.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0.2) })
                trail.Color = ColorSequence.new(KG.LIGHT, KG.GOLD)
                trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(1, 1) })
                trail.Enabled = false
                trail.Parent = tail
                s.trail = trail
            end
        end

        local function animateGoldenKirin(rig, s, moving, fly, nova)
            if not s.glowMade then
                KG.glow(rig, s)
            end
            local camera = workspace.CurrentCamera
            if s.trail then
                s.trail.Enabled = fly > 0.4 and not KG.reduced()
            end
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > KG.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, KG.SOLE)

            -- the special, Lotus Bloom: it rears, forelegs folded high (to 0.32); at the burst (0.42) the lotus blooms under it; it comes down (0.55 to
            -- 0.75) and bows (0.7 to 0.95)
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local rise = smoothstep(0.04, 0.32, progress) * (1 - smoothstep(0.55, 0.75, progress))
            local bow = smoothstep(0.7, 0.8, progress) * (1 - smoothstep(0.86, 0.97, progress))
            local special = progress > 0

            -- still a long while, it lies down; now and then it prances in place, bows its head, or swishes its tail
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            local wantLie = if s.still > 10 then 1 else 0
            s.lie = (s.lie or 0) + (wantLie - (s.lie or 0)) * math.min(1, dt * (if wantLie > (s.lie or 0) then 1 else 5))
            local lie = smoothstep(0, 1, s.lie)
            s.nextFidget = s.nextFidget or t + 4
            if t >= s.nextFidget then
                local r = math.random()
                s.fidgetAt, s.fidgetKind = t, if r < 0.4 then "prance" elseif r < 0.7 then "bow" else "swish"
                s.nextFidget = t + 6 + math.random() * 5
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / 1.6, 0, 1) else 1
            local fidget = math.sin(math.pi * env) * (1 - pace) * (1 - lie) * (1 - rise)

            -- the prance, diagonal pairs together, the forelegs lifted high at the knee; in the air a bounding run on nothing
            s.stride = (s.stride or 0) + dt * (6.5 * moving + 5.5 * fly)
            local onFoot = moving * (1 - fly)
            local want = {}
            addStance(want, KG.REAR, rise)
            addStance(want, KG.LIE, lie * (1 - rise))
            addStance(want, KG.LEAP, fly * (0.55 + 0.45 * math.sin(s.stride)))
            addStance(want, KG.PRANCE, if s.fidgetKind == "prance" then fidget else 0)
            addStance(want, KG.BOW, math.max(bow, if s.fidgetKind == "bow" then fidget else 0))
            for key, lead in KG.TROT do
                local phase = s.stride + lead
                local swing, lift = math.sin(phase), math.max(0, math.cos(phase))
                local stance
                if string.sub(key, 1, 1) == "F" then
                    stance = { ["Leg" .. key .. "1"] = { 0.3 * swing + 0.3 * lift, 0, 0 }, ["Leg" .. key .. "2"] = { 0.1 * lift, 0, 0 },
                        ["Leg" .. key .. "3"] = { -1.2 * lift, 0, 0 }, ["Hoof" .. key] = { -0.35 * lift, 0, 0 } }
                else
                    stance = { ["Leg" .. key .. "1"] = { -0.3 * swing, 0, 0 }, ["Leg" .. key .. "2"] = { -0.3 * lift, 0, 0 }, ["Leg" .. key .. "3"] = { 0.6 * lift, 0, 0 } }
                end
                addStance(want, stance, onFoot)
            end

            -- the body: breathing, banking on turns, the head carried high as it prances
            local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.18, 0.18) - (s.bank or 0)) * math.min(1, dt * 3)
            local breath = math.sin(t * 1.1)
            addStance(want, { Hips = { 0, 0, s.bank * pace }, Chest = { 0.012 * breath, 0, 0 }, Neck1 = { -0.06 * onFoot, 0, 0 } }, 1)

            -- its gaze: gentle, often on you; up at the sky as it rears
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2.5 + math.random() * 3.5
                s.atYou = math.random() < 0.55
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.3
            end
            local calm = (1 - 0.7 * pace) * (1 - rise)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.25, 0.3) else s.gazePitch) * calm + 0.3 * rise
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.5)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.5)
            addStance(want, {
                Neck2 = { 0.3 * s.pitch, 0.35 * s.yaw * (1 - 0.4 * lie), 0 }, Head = { 0.4 * s.pitch, 0.5 * s.yaw * (1 - 0.4 * lie), 0 },
                EyeL = { 0.2 * s.pitch, 0.2 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
            }, 1)

            -- the ears: a flick now and then; laid back on the wing
            for _, side in { "L", "R" } do
                local sign = if side == "L" then 1 else -1
                local flick = math.max(0, math.sin(t * 2.9 + (if side == "L" then 1 else 4))) ^ 30
                addStance(want, { ["Ear" .. side] = { 0.2 * flick - 0.35 * fly, sign * (0.15 * flick + 0.25 * fly), 0 } }, 1)
            end

            -- the tail: its silk always stirring, a wave running down it; swished from side to side in its fidget; raised in the bound
            local wave = 1.3 + 1.5 * pace
            local swish = if s.fidgetKind == "swish" then fidget else 0
            addStance(want, {
                Tail1 = { 0.05 * math.sin(t * 0.9) + 0.25 * fly + 0.1 * onFoot, 0.12 * math.sin(t * wave) + 0.4 * swish * math.sin(t * 6), 0 },
                Tail2 = { 0.06 * math.sin(t * 0.9 - 0.7), 0.16 * math.sin(t * wave - 0.8) + 0.4 * swish * math.sin(t * 6 - 0.8), 0 },
                Tail3 = { 0.08 * math.sin(t * 0.9 - 1.4) - 0.15 * fly, 0.2 * math.sin(t * wave - 1.6) + 0.3 * swish * math.sin(t * 6 - 1.6), 0 },
            }, 1)

            -- the halo: rocking softly behind its head
            addStance(want, { Halo = { 0, 0, 0.07 * math.sin(t * 0.6) } }, 1)

            for _, name in KG.BONES do
                local a = want[name] or Vector3.zero
                local lift = if name == "Hips"
                    then (-KG.REAR_DROP * rise - KG.LIE_DROP * lie * (1 - rise) + 0.014 * onFoot * math.abs(math.sin(s.stride))) * u - drop
                    else 0
                pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end
            -- the lotuses turn slowly under its hooves, coming down with it to the ground
            for key, speed in KG.LOTUS_TURN do
                pose(m["Lotus" .. key], CFrame.new(0, -drop, 0) * CFrame.Angles(0, t * speed, 0))
            end

            -- the eyes: slow blinks; dozing as it lies; wide as the lotus blooms
            local wide = smoothstep(0.38, 0.45, progress) * (1 - smoothstep(0.6, 0.75, progress))
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
            local close = math.max(blink, lie * 0.5 * doze, bow * 0.6) * (1 - wide)
            local upper = KG.BLINK_UPPER * close - math.rad(6) * wide
            local lower = KG.BLINK_LOWER * close - math.rad(5) * wide
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(KG.LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(KG.LID_HINGE[side], lower))
            end
        end

        -- It has reared, its halo flaring (animateGoldenKirin): a great lotus of golden light opens on the air under it, two rings of petals unfolding outward,
        -- a ring of light running out across the ground, golden motes rising; then it all fades.
        function Blasts.LotusBloom(rig, fx)
            local u = rig.unit
            local params = RaycastParams.new()
            params.FilterDescendantsInstances = { rig.model }
            local from = rig.rootPart.Position
            local hit = workspace:Raycast(from, Vector3.new(0, -8 * u, 0), params)
            local ground = if hit then hit.Position else from - Vector3.new(0, KG.SOLE * rig.meters, 0)
            local centre = ground + Vector3.new(0, 0.06 * u, 0)
            local reduced = KG.reduced()
            local turn = math.random() * 2 * math.pi

            -- the petals: ellipsoids of light, lying out from the middle and tipped up, unfolding from a bud
            local function petals(count, reach, length, width, tilt, offset, color, delay)
                for k = 1, count do
                    local a = turn + offset + (k - 1) / count * 2 * math.pi
                    local out = Vector3.new(math.cos(a), 0, math.sin(a))
                    local function at(r, tip)
                        return CFrame.lookAt(centre + out * r, centre + out * (r + 1)) * CFrame.Angles(tip, 0, 0)
                    end
                    local petal = fx.neon(Vector3.new(width, 0.04, length) * u * 0.2, at(0.05 * u, math.rad(70)), color)
                    local shape = Instance.new("SpecialMesh")
                    shape.MeshType = Enum.MeshType.Sphere
                    shape.Parent = petal
                    petal.Transparency = 0.15
                    tweenAfter(delay, petal, TweenInfo.new(0.45, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
                        { Size = Vector3.new(width, 0.04, length) * u, CFrame = at(reach * u, math.rad(tilt)) })
                    tweenAfter(0.95 + delay, petal, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
                end
            end
            -- wider than the kirin itself (at 1.0 across it bloomed smaller than the pet: seen in Play); deeper than its gold, as Neon blooms a pale gold
            -- to white
            petals(8, 1.6, 1.8, 0.8, 18, 0, KG.PETAL, 0)
            petals(8, 0.9, 1.3, 0.6, 38, math.pi / 8, KG.GOLD, 0.08)

            -- the heart of it, and its light
            local heart = fx.neon(Vector3.one * 0.4 * u, CFrame.new(centre + Vector3.new(0, 0.15 * u, 0)), KG.LIGHT)
            heart.Shape = Enum.PartType.Ball
            heart.Transparency = 0.1
            TweenService:Create(heart, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 1.1 * u }):Play()
            tweenAfter(0.6, heart, TweenInfo.new(0.9), { Size = Vector3.one * 0.2 * u, Transparency = 1 })
            local light = Instance.new("PointLight")
            light.Color = KG.GOLD
            light.Range = 12 * u
            light.Brightness = 2.5
            light.Shadows = false
            light.Parent = heart
            tweenAfter(0.5, light, TweenInfo.new(1.1), { Brightness = 0 })

            -- a ring of light running out across the ground
            local ring = fx.neon(Vector3.new(0.03 * u, 0.6 * u, 0.6 * u), CFrame.new(ground + Vector3.new(0, 0.03 * u, 0)) * CFrame.Angles(0, 0, math.pi / 2), KG.PETAL)
            ring.Shape = Enum.PartType.Cylinder
            ring.Transparency = 0.35
            TweenService:Create(ring, TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.03 * u, 10 * u, 10 * u), Transparency = 1 }):Play()

            -- golden motes rising off it
            if not reduced then
                local holder = fx.neon(Vector3.one * 0.05, CFrame.new(centre), KG.LIGHT)
                holder.Transparency = 1
                local motes = Instance.new("ParticleEmitter")
                motes.Texture = SPARKLE
                motes.Enabled = false
                motes.Shape = Enum.ParticleEmitterShape.Disc
                motes.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
                motes.Lifetime = NumberRange.new(0.8, 1.4)
                motes.Speed = NumberRange.new(0.8 * u, 2 * u)
                motes.SpreadAngle = Vector2.new(15, 15)
                motes.Acceleration = Vector3.new(0, 0.5 * u, 0)
                motes.Drag = 1.2
                motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.14 * u), NumberSequenceKeypoint.new(1, 0) })
                motes.Color = ColorSequence.new(KG.LIGHT, KG.GOLD)
                motes.LightEmission = 1
                motes.LightInfluence = 0
                motes.Parent = holder
                holder.Size = Vector3.new(3 * u, 0.05, 3 * u)
                holder.CFrame = CFrame.new(centre)
                motes:Emit(36)
            end
        end

        local bones = table.clone(KG.BONES)
        for _, name in { "LidUL", "LidUR", "LidLL", "LidLR", "LotusFL", "LotusFR", "LotusBL", "LotusBR" } do
            table.insert(bones, name)
        end
        PetRig.Profiles.GoldenKirin = {
            Skinned = true,
            Bones = bones,
            Points = { "Head", "Halo", "Tail3" },
            GlowColors = {
                fffaf0 = Color3.fromRGB(255, 252, 240), -- the catch-lights in its eyes
                ffe7a0 = Color3.fromRGB(255, 220, 130), -- its sunburst: warmer than drawn, or Neon blooms it to plain white
                ffd986 = Color3.fromRGB(255, 205, 110), -- the lotuses of light under its hooves
            },
            Effects = {
                Blast = "LotusBloom",
                Pulse = "Halo",
                NovaLight = 3,
            },
            Colors = {
                Gold = KG.GOLD,
                Amber = KG.DEEP,
                Orange = KG.DEEP,
                Sun = KG.LIGHT,
                Ivory = Color3.fromRGB(250, 246, 236),
            },
            Animate = animateGoldenKirin,
        }
    end
end
