-- EmberWyrm: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Debris, Players, TweenService, SPARKLE, tweenAfter, pose, smoothstep, Blasts, addStance, dropToGround = K.PetRig, K.Debris, K.Players, K.TweenService, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.addStance, K.dropToGround


    do
        -- The Ember Wyrm (skinned): a campfire salamander. A chubby baby wyrm of charcoal crust cracked with glowing magma, ember spots down its flanks, a
        -- warm ember belly, sleepy ember eyes and coal-glow cheeks; a crest of little flames down its back and a tail tip that burns like a campfire. It
        -- sits low and content, breathing slowly, its flames flickering; it looks about, sleepy-eyed, and now and then wags its tail, sniffs the ground or
        -- stretches up proud; still a long while, it naps, its legs splayed flat and its tail curled round, its fire low. It walks with a salamander's
        -- sprawl, its body bending side to side; in the air it swims on nothing, legs swept back. Its special, Bonfire: it rears up proud and swings its
        -- burning tail up over its back (to 0.42); at the burst (Blasts.Bonfire) its campfire roars up into a bonfire, embers showering round it and a
        -- ring of fire running out across the ground; it settles, content.
        local EW = {
            FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
            SOLE = 0.1577, -- metres from the middle of its box down to its pads: it stands on the ground (the box counts its RootPart, a 0.05 m cube
            -- at the origin reaching 0.025 m under its pads: half its height, 0.1702, floated it 1.25 cm, measured on the Volt Fox in Play)
            LID_HINGE = { L = Vector3.new(0.7722, 0.0578, -0.6328), R = Vector3.new(0.7722, -0.0578, 0.6328) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(70),
            BLINK_LOWER = math.rad(24),
            FLAME = Color3.fromRGB(255, 122, 30),
            CORE = Color3.fromRGB(255, 208, 74),
            HOT = Color3.fromRGB(255, 236, 170),
            EMBER = Color3.fromRGB(255, 92, 20),
            BONFIRE_FLAME = "rbxassetid://106209125427468", -- a cel-shaded tongue of its own fire, 4x4 looping flipbook (tools/vfx/wyrm_particles.py)
            TROT ={ FL = 0, BR = 0, FR = math.pi, BL = math.pi }, -- diagonal pairs together
            SIDE = { FL = 1, BL = 1, FR = -1, BR = -1 },
            -- its stances, each checked in Blender against the ground and for torn skin (ember_wyrm.py: NAP, PROUD, the walk, STOKE)
            NAP = { Head = { 0.12, 0.35, 0.1 }, Neck = { 0, 0.2, 0 }, Tail1 = { 0, -0.35, 0 }, Tail2 = { 0, -0.45, 0 }, Tail3 = { 0, -0.5, 0 }, Tail4 = { 0, -0.4, 0 },
                LegFL1 = { 0, 0, -0.25 }, LegBL1 = { 0, 0, -0.25 }, LegFR1 = { 0, 0, 0.25 }, LegBR1 = { 0, 0, 0.25 } },
            NAP_DROP = 0.03,
            PROUD = { Body = { 0.25, 0, 0 }, Chest = { 0.15, 0, 0 }, Neck = { -0.05, 0, 0 }, Head = { -0.2, 0, 0 }, Tail1 = { -0.15, 0, 0 },
                LegFL1 = { -0.35, 0, 0 }, LegFL2 = { 0.3, 0, 0 }, LegFR1 = { -0.35, 0, 0 }, LegFR2 = { 0.3, 0, 0 } },
            STOKE = { Tail1 = { -0.3, 0, 0 }, Tail2 = { -0.4, 0, 0 }, Tail3 = { -0.4, 0, 0 }, Tail4 = { -0.3, 0, 0 } },
            SNIFF = { Neck = { 0.25, 0, 0 }, Head = { 0.3, 0, 0 } },
            BONES = { "Hips", "Body", "Chest", "Neck", "Head", "EyeL", "EyeR", "Tail1", "Tail2", "Tail3", "Tail4", "Campfire" },
        }
        for _, key in { "FL", "FR", "BL", "BR" } do
            table.insert(EW.BONES, "Leg" .. key .. "1")
            table.insert(EW.BONES, "Leg" .. key .. "2")
            table.insert(EW.BONES, "Hand" .. key)
        end

        function EW.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        -- its warm light and the embers drifting up off its campfire: both on the campfire's bone
        function EW.glow(rig, s)
            s.glowMade = true
            local fire = rig.points.Campfire
            if not fire then
                return
            end
            local a = Instance.new("Attachment")
            a.Name = "Fire"
            a.Position = Vector3.new(0, 0.08 * rig.meters, 0)
            a.Parent = fire
            s.fire = a
            local light = Instance.new("PointLight")
            light.Name = "PulseLight"
            light.Color = EW.FLAME
            light.Range = 5 * rig.unit
            light.Brightness = 1.2
            light.Shadows = false
            light.Parent = a
            rig.light = light
            if not EW.reduced() and not (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer) then
                local embers = Instance.new("ParticleEmitter")
                embers.Name = "Embers"
                embers.Texture = SPARKLE
                embers.Rate = 4
                embers.Lifetime = NumberRange.new(0.7, 1.3)
                embers.Speed = NumberRange.new(0.3 * rig.unit, 0.7 * rig.unit)
                embers.SpreadAngle = Vector2.new(25, 25)
                embers.Acceleration = Vector3.new(0, 0.4 * rig.unit, 0)
                embers.Drag = 1.2
                embers.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.07 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
                embers.Color = ColorSequence.new(EW.HOT, EW.EMBER)
                embers.LightEmission = 1
                embers.LightInfluence = 0
                embers.EmissionDirection = Enum.NormalId.Top
                embers.Parent = a
                s.embers = embers
            end
        end

        local function animateEmberWyrm(rig, s, moving, fly, nova)
            if not s.glowMade then
                EW.glow(rig, s)
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > EW.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, EW.SOLE)

            -- the special, Bonfire: it rears up proud and swings its burning tail up over its back (to 0.42); the bonfire roars (0.42); it settles
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local rise = smoothstep(0.04, 0.34, progress) * (1 - smoothstep(0.55, 0.8, progress))
            local stoke = smoothstep(0.12, 0.4, progress) * (1 - smoothstep(0.6, 0.85, progress))
            local special = progress > 0

            -- still a long while, it naps; now and then it wags its tail, sniffs the ground or stretches up proud
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            local wantNap = if s.still > 12 then 1 else 0
            s.nap = (s.nap or 0) + (wantNap - (s.nap or 0)) * math.min(1, dt * (if wantNap > (s.nap or 0) then 0.8 else 5))
            local nap = smoothstep(0, 1, s.nap)
            s.nextFidget = s.nextFidget or t + 4
            if t >= s.nextFidget then
                local r = math.random()
                s.fidgetAt, s.fidgetKind = t, if r < 0.4 then "wag" elseif r < 0.7 then "sniff" else "stretch"
                s.nextFidget = t + 6 + math.random() * 6
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / 1.6, 0, 1) else 1
            local fidget = math.sin(math.pi * env) * (1 - pace) * (1 - nap) * (1 - rise)

            local want = {}
            addStance(want, EW.PROUD, math.max(rise, if s.fidgetKind == "stretch" then fidget * 0.6 else 0))
            addStance(want, EW.STOKE, stoke)
            addStance(want, EW.NAP, nap * (1 - rise))
            addStance(want, EW.SNIFF, if s.fidgetKind == "sniff" then fidget else 0)

            -- the sprawling walk: diagonal pairs reaching forward and lifted together, the body bending side to side; in the air it swims on nothing,
            -- legs swept back, its whole body waving
            s.stride = (s.stride or 0) + dt * (7 * moving + 5 * fly)
            local onFoot = moving * (1 - fly)
            local wave = math.sin(s.stride)
            addStance(want, { Hips = { 0, -0.2 * wave * onFoot - 0.25 * wave * fly, 0 }, Chest = { 0, 0.3 * wave * onFoot + 0.3 * wave * fly, 0 },
                Head = { 0, -0.2 * wave * pace, 0 } }, 1)
            for key, lead in EW.TROT do
                local phase = s.stride + lead
                local sd = EW.SIDE[key]
                local swing, lift = math.sin(phase), math.max(0, math.cos(phase))
                addStance(want, { ["Leg" .. key .. "1"] = { 0, -sd * 0.45 * swing, -sd * 0.3 * lift } }, onFoot)
                -- swept back and tucked in the air (back is +yaw on the left, -yaw on the right; lifted, -z on the left, +z on the right)
                addStance(want, { ["Leg" .. key .. "1"] = { 0, sd * 0.6, -sd * 0.25 } }, fly)
            end

            -- breathing slowly; its head looking about, sleepy, often at you
            local breath = math.sin(t * 1.0)
            addStance(want, { Chest = { 0.02 * breath, 0, 0 }, Body = { 0.012 * breath, 0, 0 } }, 1)
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2.5 + math.random() * 3.5
                s.atYou = math.random() < 0.5
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.3
            end
            local calm = (1 - 0.7 * pace) * (1 - rise) * (1 - 0.8 * nap)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.2, 0.35) else s.gazePitch) * calm - 0.25 * rise
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.5)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.5)
            addStance(want, {
                Neck = { 0.3 * s.pitch, 0.35 * s.yaw, 0 }, Head = { 0.4 * s.pitch, 0.5 * s.yaw, 0 },
                EyeL = { 0.2 * s.pitch, 0.2 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
            }, 1)

            -- its tail: a slow sway, a happy wag in its fidget, waving as it swims through the air
            local wag = if s.fidgetKind == "wag" then fidget else 0
            for k = 1, 4 do
                local sway = 0.06 * math.sin(t * 0.8 - k * 0.6) + 0.35 * wag * math.sin(t * 9 - k * 0.7) + (0.15 * onFoot + 0.3 * fly) * math.sin(s.stride - k * 0.9)
                addStance(want, { ["Tail" .. k] = { 0, sway, 0 } }, 1)
            end

            -- its campfire: flickering, a little wild
            local flick = math.sin(t * 13) * 0.6 + math.sin(t * 21 + 1.3) * 0.4
            addStance(want, { Campfire = { 0.06 * flick, 0.08 * math.sin(t * 7.3), 0.07 * math.sin(t * 11.1 + 0.4) } }, 1)

            for _, name in EW.BONES do
                local a = want[name] or Vector3.zero
                local lift = if name == "Hips" then (-EW.NAP_DROP * nap * (1 - rise) + 0.006 * onFoot * math.abs(wave)) * u - drop else 0
                pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- its flames flickering; low as it naps; the embers rising slower as it sleeps
            local flames, cores = rig.parts.Flames, rig.parts.Cores
            local flare = 0.5 + 0.5 * math.sin(t * 9 + math.sin(t * 3.7) * 2)
            if flames then
                flames.Color = EW.EMBER:Lerp(EW.FLAME, 0.6 + 0.4 * flare * (1 - 0.6 * nap))
            end
            if cores then
                cores.Color = EW.FLAME:Lerp(EW.CORE, 0.55 + 0.45 * flare * (1 - 0.6 * nap))
            end
            if s.embers then
                s.embers.Rate = 4 * (1 - 0.7 * nap) + 10 * stoke
            end

            -- the eyes: sleepy, slow blinks; closed as it naps; wide as its bonfire roars
            local wide = smoothstep(0.38, 0.45, progress) * (1 - smoothstep(0.6, 0.75, progress))
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.35
                if a >= 1 then
                    s.nextBlink = t + 2.5 + math.random() * 4
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local close = math.max(blink, nap) * (1 - wide)
            local upper = EW.BLINK_UPPER * close - math.rad(14) * wide
            local lower = EW.BLINK_LOWER * close - math.rad(6) * wide
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(EW.LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(EW.LID_HINGE[side], lower))
            end
        end

        -- It has swung its tail up over its back (animateEmberWyrm): its campfire roars up into a bonfire, a column of flame with a bright heart, embers
        -- showering round it, a ring of fire running out across the ground; then it all dies down.
        function Blasts.Bonfire(rig, fx)
            local u = rig.unit
            local fire = rig.points.Campfire
            local at = if fire then fire.TransformedWorldCFrame.Position else fx.origin
            local params = RaycastParams.new()
            params.FilterDescendantsInstances = { rig.model }
            local hit = workspace:Raycast(rig.rootPart.Position, Vector3.new(0, -10 * u, 0), params)
            local ground = if hit then hit.Position else rig.rootPart.Position - Vector3.new(0, EW.SOLE * rig.meters, 0)
            local reduced = EW.reduced()

            -- the column: tongues of its own cel-shaded fire roaring up off its campfire for most of a second, big and fast at first, then dying down
            -- (painted in its flames' bands, so the texture's colour is drawn untinted). It pours from the campfire bone itself, so the column goes
            -- where its tail goes as it circles its owner; the flames left in the air stay where they rose.
            local column = Instance.new("ParticleEmitter")
            column.Texture = EW.BONFIRE_FLAME
            column.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
            column.FlipbookMode = Enum.ParticleFlipbookMode.Loop
            column.FlipbookFramerate = NumberRange.new(20, 28)
            column.FlipbookStartRandom = true
            -- (the bone turns as the tail swings over: a small launch any way, and the world's up does the rising)
            column.SpreadAngle = Vector2.new(180, 180)
            column.Speed = NumberRange.new(0.6 * u, 1.4 * u)
            column.Acceleration = Vector3.new(0, 10 * u, 0)
            column.Drag = 0.8
            column.Lifetime = NumberRange.new(0.5, 0.8)
            column.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.9 * u, 0.2 * u), NumberSequenceKeypoint.new(0.2, 1.45 * u, 0.25 * u),
                NumberSequenceKeypoint.new(1, 0.35 * u, 0.1 * u) }) -- wide at its foot, licking up to a point
            column.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.08, 0), NumberSequenceKeypoint.new(0.7, 0.05), NumberSequenceKeypoint.new(1, 1) })
            column.Rotation = NumberRange.new(-8, 8)
            column.RotSpeed = NumberRange.new(-15, 15)
            column.LightEmission = 0.3
            column.LightInfluence = 0
            column.Brightness = 1.3
            column.ZOffset = 0.3
            column.Rate = if reduced then 22 else 55
            if fire then
                column.Parent = fire
                Debris:AddItem(column, 2)
            else
                local base = fx.neon(Vector3.one * 0.05, CFrame.new(at), EW.FLAME)
                base.Transparency = 1
                column.Parent = base
            end
            column:Emit(if reduced then 4 else 8)
            tweenAfter(0.45, column, TweenInfo.new(0.4), { Rate = if reduced then 5 else 12 })
            task.delay(0.85, function()
                column.Enabled = false
            end)
            local light = Instance.new("PointLight")
            light.Color = EW.FLAME
            light.Range = 12 * u
            light.Brightness = 2 -- (at 3 it washed the charcoal of its own hide out to orange)
            light.Shadows = false
            local holder = fx.neon(Vector3.one * 0.05, CFrame.new(at + Vector3.new(0, 1 * u, 0)), EW.CORE)
            holder.Transparency = 1
            light.Parent = holder
            tweenAfter(0.4, light, TweenInfo.new(1.1), { Brightness = 0 })

            -- embers showering up and falling round it
            if not reduced then
                local embers = Instance.new("ParticleEmitter")
                embers.Texture = SPARKLE
                embers.Enabled = false
                embers.Lifetime = NumberRange.new(0.6, 1.1)
                embers.Speed = NumberRange.new(2.5 * u, 5 * u)
                embers.SpreadAngle = Vector2.new(35, 35)
                embers.Acceleration = Vector3.new(0, -6 * u, 0)
                embers.Drag = 0.6
                embers.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.14 * u), NumberSequenceKeypoint.new(1, 0) })
                embers.Color = ColorSequence.new(EW.HOT, EW.EMBER)
                embers.LightEmission = 1
                embers.LightInfluence = 0
                embers.Parent = holder
                holder.CFrame = CFrame.lookAt(holder.Position, holder.Position + Vector3.yAxis)
                embers:Emit(45)
            end

            -- a ring of fire running out across the ground
            local ring = fx.neon(Vector3.new(0.04 * u, 0.6 * u, 0.6 * u), CFrame.new(ground + Vector3.new(0, 0.04 * u, 0)) * CFrame.Angles(0, 0, math.pi / 2), EW.FLAME)
            ring.Shape = Enum.PartType.Cylinder
            ring.Transparency = 0.3
            TweenService:Create(ring, TweenInfo.new(0.8, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.04 * u, 8 * u, 8 * u), Transparency = 1 }):Play()
        end

        local bones = table.clone(EW.BONES)
        for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
            table.insert(bones, name)
        end
        PetRig.Profiles.EmberWyrm = {
            Skinned = true,
            Bones = bones,
            Points = { "Campfire" },
            GlowColors = {
                fff4e0 = Color3.fromRGB(255, 246, 228), -- the catch-lights in its eyes
                ff7a1e = EW.FLAME, -- its flames
                ffd04a = EW.CORE, -- the bright hearts of its flames, seen through them
            },
            SeeThroughGlow = { ff7a1e = 0.35 }, -- (Neon is solid: an opaque flame hid its yellow heart)
            Effects = {
                Blast = "Bonfire",
                NovaLight = 3,
            },
            Colors = {
                Gold = EW.CORE,
                Amber = EW.EMBER,
                Orange = EW.FLAME,
                Sun = EW.HOT,
                Ivory = Color3.fromRGB(255, 220, 180),
            },
            Animate = animateEmberWyrm,
        }
    end
end
