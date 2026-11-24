-- BonefireDragon: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Players, SPARKLE, tweenAfter, pose, smoothstep, Blasts, addStance, emitter = K.PetRig, K.Players, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.addStance, K.emitter


    do
        -- The Bonefire Dragon (skinned): the bones of a dragon that refused to finish dying, held together and up off the ground by the blue soul fire
        -- burning in its ribs (bonefire_dragon.py). Every bone is rigid on its own skeleton bone. It hangs in the air in a predator's crouch, rising and
        -- sinking slowly, its bones creaking as they sway; the fire in its chest flickers up through the ribs and a point of cold light burns deep in each
        -- socket, flames streaming from them. Its head hangs low and sways, turning to look about, often at you; its heavy brows glare, and lift when it
        -- is curious; its jaw hangs open on the fire in its throat. The bare bones of its wings flex as it hovers and beat slow and heavy when it goes
        -- anywhere; its tail waves to its spiked knot. Now and then it roars, clatters its teeth, swipes a forefoot, shakes its whole frame with a rattle,
        -- or lets its fire flare. Its special, Ossuary Pyre: it rears up as the fire in its ribs blazes, then slams down; a ring of burning bone spires
        -- bursts up from the ground round it and a pillar of soul fire roars out of its chest (Blasts.OssuaryPyre).
        local BF = {
            FAR = 120, -- studs from the camera past which nobody can see it fidget: its bones rest
            SOUL = Color3.fromRGB(61, 123, 255), -- its fire (Neon: saturated; a paler blue blooms white)
            SOUL_HOT = Color3.fromRGB(200, 228, 255),
            SOUL_DEEP = Color3.fromRGB(40, 30, 150),
            EYE = Color3.fromRGB(74, 166, 255),
            EYE_HOT = Color3.fromRGB(210, 238, 255),
            BONE = Color3.fromRGB(226, 214, 188),
            SPIRE = Color3.fromRGB(176, 160, 132), -- the bone spires of its special: aged ivory, darker than its own bones so they read in daylight
            FIRE = "rbxasset://textures/particles/fire_main.dds",
            SMOKE = "rbxasset://textures/particles/smoke_main.dds",
            -- each brow turns about the line out of its socket (bonefire_dragon.py's socket frame): a positive turn lowers its front (a glare)
            BROW_AXIS = { L = Vector3.new(-0.7226, 0.3011, -0.6222), R = Vector3.new(0.7226, 0.3011, -0.6222) },
            -- its moves (game axes): the same numbers as bonefire_dragon.py's ROAR, RISE and SWIPE, each checked there
            ROAR = { Jaw = { -0.42, 0, 0 }, Head = { 0.22, 0, 0 }, Neck2 = { 0.1, 0, 0 }, Neck1 = { 0.06, 0, 0 } },
            SWIPE = { LegFL1 = { -0.55, 0.1, 0 }, LegFL2 = { 0.7, 0, 0 }, LegFL3 = { 0.4, 0, 0 }, PawFL = { 0.3, 0, 0 } },
            SLAM = { Body = { -0.12, 0, 0 }, Chest = { -0.1, 0, 0 }, Neck1 = { -0.08, 0, 0 }, Head = { -0.1, 0, 0 }, LegFL1 = { -0.35, 0, 0 },
                LegFR1 = { -0.35, 0, 0 }, LegFL2 = { 0.45, 0, 0 }, LegFR2 = { 0.45, 0, 0 } },
            FIDGET_TIME = { roar = 1.8, clatter = 1.1, swipe = 1.3, shake = 1.2, flare = 2.0 },
        }

        local function bfWings(lift, sweep, elbow, hand, fan)
            local out = {}
            for tag, sign in { L = 1, R = -1 } do
                out["Wing" .. tag .. "1"] = { 0, sweep * sign, -lift * sign }
                out["Wing" .. tag .. "2"] = { 0, elbow * sign, 0 }
                out["Wing" .. tag .. "3"] = { 0, hand * sign, 0 }
                for j = 0, 2 do
                    out["Wing" .. tag .. "F" .. (j + 1)] = { 0, fan * sign * (j / 2 - 0.5), 0 }
                end
            end
            return out
        end
        BF.BEAT_UP = bfWings(0.5, -0.1, -0.25, -0.2, 0.3)
        BF.BEAT_DOWN = bfWings(-0.55, 0.12, -0.35, -0.3, 0.4)
        BF.RISE = bfWings(0.35, -0.05, -0.45, -0.4, 0.5)
        for bone, a in { Body = { 0.2, 0, 0 }, Chest = { 0.16, 0, 0 }, Neck1 = { -0.1, 0, 0 }, Head = { -0.12, 0, 0 }, LegFL1 = { 0.5, 0, 0 },
            LegFR1 = { 0.5, 0, 0 }, LegFL2 = { -0.6, 0, 0 }, LegFR2 = { -0.6, 0, 0 } } do
            BF.RISE[bone] = a
        end

        function BF.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        BF.BONES = { "Hips", "Body", "Chest", "Neck1", "Neck2", "Head", "Jaw", "Soul", "EyeL", "EyeR" }
        for k = 1, 6 do
            table.insert(BF.BONES, "Tail" .. k)
        end
        for _, key in { "FL", "FR", "BL", "BR" } do
            for k = 1, 3 do
                table.insert(BF.BONES, "Leg" .. key .. k)
            end
            table.insert(BF.BONES, "Paw" .. key)
        end
        for _, tag in { "L", "R" } do
            for k = 1, 3 do
                table.insert(BF.BONES, "Wing" .. tag .. k)
            end
            for j = 1, 3 do
                table.insert(BF.BONES, "Wing" .. tag .. "F" .. j)
            end
        end

        -- Its living fire, made once: flames licking up out of its chest through the ribs, embers drifting off its spine, and a flame streaming from
        -- each socket. Fewer for another player's pet on a phone, and with reduced effects.
        function BF.fires(rig)
            local soul = rig.parts.Soul
            if not soul then
                return nil
            end
            local u = rig.unit
            local few = BF.reduced() or (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer)
            local fires = {}
            fires.chest = emitter(soul, {
                Name = "SoulFire",
                Texture = BF.FIRE,
                Rate = if few then 7 else 15,
                Lifetime = NumberRange.new(0.45, 0.8),
                Speed = NumberRange.new(0.4 * u, 0.9 * u),
                SpreadAngle = Vector2.new(28, 28),
                Acceleration = Vector3.new(0, 1.6 * u, 0),
                Drag = 1,
                EmissionDirection = Enum.NormalId.Top,
                Rotation = NumberRange.new(0, 360),
                RotSpeed = NumberRange.new(-60, 60),
                Size = NumberSequence.new({
                    NumberSequenceKeypoint.new(0, 0.42 * u),
                    NumberSequenceKeypoint.new(0.5, 0.34 * u),
                    NumberSequenceKeypoint.new(1, 0.06 * u),
                }),
                Color = ColorSequence.new({
                    ColorSequenceKeypoint.new(0, BF.SOUL_HOT),
                    ColorSequenceKeypoint.new(0.35, BF.SOUL),
                    ColorSequenceKeypoint.new(1, BF.SOUL_DEEP),
                }),
                Transparency = NumberSequence.new({
                    NumberSequenceKeypoint.new(0, 0.6),
                    NumberSequenceKeypoint.new(0.2, 0.35),
                    NumberSequenceKeypoint.new(1, 1),
                }),
                Brightness = 1.2, -- (stacked additive flames wash to white: kept low, seen in Play)
            })
            fires.chestRate = fires.chest.Rate
            if not few then
                fires.embers = emitter(soul, {
                    Name = "SoulEmbers",
                    Texture = SPARKLE,
                    Rate = 3,
                    Lifetime = NumberRange.new(1.4, 2.4),
                    Speed = NumberRange.new(0.6 * u, 1.2 * u),
                    SpreadAngle = Vector2.new(35, 35),
                    EmissionDirection = Enum.NormalId.Top,
                    Acceleration = Vector3.new(0, 0.4 * u, 0),
                    Drag = 0.6,
                    Size = NumberSequence.new({
                        NumberSequenceKeypoint.new(0, 0),
                        NumberSequenceKeypoint.new(0.2, 0.07 * u),
                        NumberSequenceKeypoint.new(1, 0),
                    }),
                    Color = ColorSequence.new(BF.SOUL_HOT, BF.SOUL),
                    Transparency = NumberSequence.new(0.1, 1),
                })
            end
            fires.eyes = {}
            for _, side in { "L", "R" } do
                local bone = rig.points["Eye" .. side]
                if bone then
                    table.insert(fires.eyes, emitter(bone, {
                        Name = "EyeFlame",
                        Texture = BF.FIRE,
                        Rate = if few then 5 else 11,
                        Lifetime = NumberRange.new(0.25, 0.42),
                        Speed = NumberRange.new(0.15 * u, 0.35 * u),
                        SpreadAngle = Vector2.new(15, 15),
                        Acceleration = Vector3.new(0, 1.2 * u, 0),
                        Rotation = NumberRange.new(-20, 20),
                        Size = NumberSequence.new({
                            NumberSequenceKeypoint.new(0, 0.1 * u),
                            NumberSequenceKeypoint.new(1, 0.02 * u),
                        }),
                        Color = ColorSequence.new(BF.EYE_HOT, BF.EYE),
                        Transparency = NumberSequence.new({
                            NumberSequenceKeypoint.new(0, 0.3),
                            NumberSequenceKeypoint.new(1, 1),
                        }),
                        Brightness = 1.4,
                    }))
                end
            end
            fires.eyeRate = if few then 5 else 11
            return fires
        end

        local function animateBonefireDragon(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > BF.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            if s.fires == nil then
                s.fires = BF.fires(rig) or false
            end

            -- the special, Ossuary Pyre: it rears up, its fire blazing (to 0.4); at the burst (0.42) it slams down (to 0.62); it settles (to 0.9)
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local special = progress > 0
            local rise = smoothstep(0.02, 0.36, progress) * (1 - smoothstep(0.4, 0.47, progress))
            local slam = smoothstep(0.4, 0.47, progress) * (1 - smoothstep(0.6, 0.88, progress))

            -- now and then it roars, clatters its teeth, swipes a forefoot, shakes its whole frame or lets its fire flare
            s.nextFidget = s.nextFidget or t + 4
            if t >= s.nextFidget and not special then
                local r = math.random()
                s.fidgetAt = t
                s.fidgetKind = if r < 0.22 then "roar" elseif r < 0.44 then "clatter" elseif r < 0.62 then "swipe" elseif r < 0.8 then "shake" else "flare"
                s.nextFidget = t + BF.FIDGET_TIME[s.fidgetKind] + 4 + math.random() * 5
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / BF.FIDGET_TIME[s.fidgetKind], 0, 1) else 1
            local fidget = math.sin(math.pi * env) * (1 - 0.6 * pace) * (if special then 0 else 1)
            local function kind(name)
                return if s.fidgetKind == name then fidget else 0
            end
            local flare = kind("flare")

            local want = {}
            -- its wings: the bare bones flex slowly as it hovers; they beat slow and heavy when it goes anywhere; raised high as it rears
            s.beat = (s.beat or 0) + dt * (1.1 + 2.6 * pace)
            local stroke = math.sin(s.beat)
            local up, down = math.max(0, stroke), math.max(0, -stroke)
            local amp = (0.12 + 0.88 * pace) * (1 - rise) * (1 - slam)
            addStance(want, BF.BEAT_UP, up * amp + 0.4 * flare)
            addStance(want, BF.BEAT_DOWN, down * amp + 0.5 * slam)
            addStance(want, bfWings(0, 0, 0.06 * math.sin(t * 0.9), 0.08 * math.sin(t * 0.9 - 0.6), 0.12 * math.sin(t * 0.7)), (1 - pace) * (1 - rise))
            addStance(want, BF.RISE, rise)
            addStance(want, BF.SLAM, slam)

            -- its head: low and swaying, looking about, often at you
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2.2 + math.random() * 3
                s.atYou = math.random() < 0.55
                s.curious = s.atYou and math.random() < 0.4
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.3
            end
            local calm = (1 - 0.5 * pace) * (1 - rise) * (1 - slam)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.7, 0.7) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.45, -0.2, 0.3) else s.gazePitch) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.2)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.2)
            local sway = 0.08 * math.sin(t * 0.55) * calm
            addStance(want, { Neck1 = { 0.15 * s.pitch, 0.3 * s.yaw + sway, 0 }, Neck2 = { 0.2 * s.pitch, 0.35 * s.yaw + sway, 0.04 * math.sin(t * 0.45) },
                Head = { 0.35 * s.pitch, 0.35 * s.yaw, 0.06 * math.sin(t * 0.4) }, EyeL = { 0.3 * s.pitch, 0.3 * s.yaw, 0 },
                EyeR = { 0.3 * s.pitch, 0.3 * s.yaw, 0 } }, 1)

            -- its jaw: hanging open on its fire, moving with its breath; roaring; its teeth clattering
            addStance(want, { Jaw = { 0.05 * math.sin(t * 1.3) + 0.02 * math.sin(t * 3.1), 0, 0 } }, (1 - kind("roar")) * (1 - slam))
            addStance(want, BF.ROAR, math.max(kind("roar"), slam, 0.5 * rise))
            local clatter = kind("clatter")
            if clatter > 0 then
                addStance(want, { Jaw = { 0.13 * math.sin(t * 34), 0, 0 }, Head = { 0.02 * math.sin(t * 34 + 1), 0, 0 } }, clatter)
            end

            -- its legs: drawn up in a crouch, the claws flexing; trailing back as it goes; a forefoot swiping now and then
            local flex = 0.07 * math.sin(t * 0.9)
            addStance(want, { LegFL1 = { flex, 0, 0 }, LegFR1 = { -flex, 0, 0 }, PawFL = { 0.12 * math.sin(t * 0.9 + 1), 0, 0 }, PawFR = { -0.12 * math.sin(t * 0.9 + 1), 0, 0 },
                LegBL1 = { 0.5 * flex, 0, 0 }, LegBR1 = { -0.5 * flex, 0, 0 } }, (1 - pace) * (1 - rise))
            addStance(want, { LegFL1 = { 0.3, 0, 0 }, LegFR1 = { 0.3, 0, 0 }, LegBL1 = { 0.35, 0, 0 }, LegBR1 = { 0.35, 0, 0 }, LegBL2 = { -0.2, 0, 0 },
                LegBR2 = { -0.2, 0, 0 } }, pace)
            addStance(want, BF.SWIPE, kind("swipe"))

            -- the tail: a slow wave running down it to its knot; streaming as it goes
            for k = 1, 6 do
                local w = (0.06 + 0.07 * k / 6) * math.sin(t * 0.9 - k * 0.55) * (1 - 0.55 * pace)
                addStance(want, { ["Tail" .. k] = { 0.035 * math.sin(t * 0.7 - k * 0.5) - 0.02 * pace, w, 0 } }, 1)
            end

            -- a shake: its whole frame rattles
            local shake = kind("shake")
            if shake > 0 then
                for k, name in { "Chest", "Neck1", "Neck2", "Head", "Jaw", "Tail2", "Tail4", "WingL1", "WingR1" } do
                    addStance(want, { [name] = { 0.035 * math.sin(t * 38 + k * 1.7), 0.035 * math.sin(t * 31 + k * 2.3), 0.02 * math.sin(t * 27 + k) } }, shake)
                end
            end

            -- it rises and sinks slowly in the air; with each downstroke; up as it rears, down as it slams
            local lift = (0.025 * math.sin(t * 1.2) + 0.03 * down * amp + 0.08 * rise - 0.05 * slam) * u
            for _, name in BF.BONES do
                local a = want[name] or Vector3.zero
                local y = if name == "Hips" then lift elseif name == "Soul" then (0.008 * math.sin(t * 2.3) + 0.02 * rise) * u else 0
                pose(m[name], CFrame.new(0, y, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- its brows: a steady glare; lifted when it is curious about you; low and hard as it roars
            local glare = 0.12 + 0.2 * math.max(kind("roar"), rise, slam) - 0.3 * (if s.curious then calm else 0)
            s.glare = (s.glare or glare) + (glare - (s.glare or glare)) * math.min(1, dt * 4)
            pose(m.BrowL, CFrame.fromAxisAngle(BF.BROW_AXIS.L, s.glare))
            pose(m.BrowR, CFrame.fromAxisAngle(BF.BROW_AXIS.R, -s.glare))

            -- its fire: the eyes and throat brighten as it roars, rears and flares; the flames in its chest leap
            local heat = math.max(kind("roar"), flare, rise, slam)
            local eyes = rig.parts.Eyes
            if eyes then
                eyes.Color = BF.EYE:Lerp(BF.EYE_HOT, 0.15 + 0.15 * math.sin(t * 2.7) + 0.6 * heat)
            end
            local maw = rig.parts.Maw
            if maw then
                maw.Color = BF.SOUL_DEEP:Lerp(BF.SOUL, 0.55 + 0.2 * math.sin(t * 1.9) + 0.45 * heat)
            end
            local fires = s.fires
            if fires then
                fires.chest.Rate = fires.chestRate * (1 + 1.2 * heat)
                for _, flame in fires.eyes do
                    flame.Rate = fires.eyeRate * (1 + heat)
                end
            end
        end

        -- It slams down (animateBonefireDragon): a ring of bone spires bursts up from the ground round it, each crowned with blue soul fire, and a
        -- pillar of soul fire roars up out of its chest; a flash of cold light. The spires sink back into the ground; gone by 1.6 s.
        function Blasts.OssuaryPyre(rig, fx)
            local u = rig.unit
            local reduced = BF.reduced()
            local soul = rig.parts.Soul
            local origin = if soul then soul.Position else rig.rootPart.Position

            -- the ground under it (in the world; a portrait has none, so a little below it there)
            local ground = origin - Vector3.new(0, 4 * u, 0)
            if rig.rootPart:IsDescendantOf(workspace) then
                local params = RaycastParams.new()
                local ignore = { rig.model }
                for _, player in Players:GetPlayers() do
                    if player.Character then
                        table.insert(ignore, player.Character)
                    end
                end
                local companions = workspace:FindFirstChild("PetCompanions")
                if companions then
                    table.insert(ignore, companions)
                end
                params.FilterDescendantsInstances = ignore
                params.FilterType = Enum.RaycastFilterType.Exclude
                local hit = workspace:Raycast(origin, Vector3.new(0, -40, 0), params)
                if hit then
                    ground = hit.Position
                end
            end

            local holder = fx.neon(Vector3.one * 0.05, CFrame.new(origin), BF.SOUL)
            holder.Transparency = 1
            local folder = holder.Parent
            local light = Instance.new("PointLight")
            light.Color = BF.SOUL
            light.Range = 16 * u
            light.Brightness = 2.5
            light.Shadows = false
            light.Parent = holder
            tweenAfter(0.25, light, TweenInfo.new(1.0), { Brightness = 0 })

            -- the pillar of soul fire out of its chest
            local pillar = emitter(holder, {
                Name = "SoulPillar",
                Texture = BF.FIRE,
                Rate = 0,
                Lifetime = NumberRange.new(0.45, 0.7),
                Speed = NumberRange.new(7 * u, 11 * u),
                SpreadAngle = Vector2.new(9, 9),
                EmissionDirection = Enum.NormalId.Top,
                Drag = 2,
                Rotation = NumberRange.new(0, 360),
                RotSpeed = NumberRange.new(-90, 90),
                Size = NumberSequence.new({
                    NumberSequenceKeypoint.new(0, 0.6 * u),
                    NumberSequenceKeypoint.new(0.4, 0.85 * u),
                    NumberSequenceKeypoint.new(1, 0.2 * u),
                }),
                Color = ColorSequence.new({
                    ColorSequenceKeypoint.new(0, BF.SOUL_HOT),
                    ColorSequenceKeypoint.new(0.4, BF.SOUL),
                    ColorSequenceKeypoint.new(1, BF.SOUL_DEEP),
                }),
                Transparency = NumberSequence.new({
                    NumberSequenceKeypoint.new(0, 0.4),
                    NumberSequenceKeypoint.new(1, 1),
                }),
                Brightness = 1.3, -- (at 3, with 50 a second, it washed the whole screen white in Play)
            })
            pillar:Emit(if reduced then 10 else 20)
            if not reduced then
                pillar.Rate = 26
                task.delay(0.4, function()
                    pillar.Enabled = false
                end)
            end

            -- the ring of bone spires, bursting up round it and sinking back
            local count = if reduced then 4 else 8
            local spin = math.random() * 2 * math.pi
            for k = 1, count do
                local angle = spin + k / count * 2 * math.pi
                local out = Vector3.new(math.cos(angle), 0, math.sin(angle))
                local base = ground + out * (3.2 + 0.4 * (k % 2)) * u
                local height = (1.6 + 0.6 * ((k * 7) % 3) / 2) * u
                local tilt = CFrame.fromAxisAngle(Vector3.yAxis:Cross(out).Unit, -0.38)
                local spire = Instance.new("Part")
                spire.Anchored = true
                spire.CanCollide = false
                spire.CanTouch = false
                spire.CanQuery = false
                spire.CastShadow = false
                spire.Material = Enum.Material.Limestone -- (porous, like old bone: smooth plastic read as white eggs in the sun)
                spire.Color = BF.SPIRE
                spire.Size = Vector3.new(0.34 * u, height, 0.34 * u)
                local mesh = Instance.new("SpecialMesh")
                mesh.MeshType = Enum.MeshType.Sphere
                mesh.Parent = spire
                local sunk = CFrame.new(base) * tilt * CFrame.new(0, -height * 0.55, 0)
                local risen = CFrame.new(base) * tilt * CFrame.new(0, height * 0.32, 0)
                spire.CFrame = sunk
                spire.Parent = folder
                local delay = 0.03 * k
                tweenAfter(delay, spire, TweenInfo.new(0.16, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { CFrame = risen })
                tweenAfter(delay + 0.85, spire, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { CFrame = sunk })
                -- its crown of fire, and a burst of it at its root
                local tip = Instance.new("Attachment")
                tip.Position = Vector3.new(0, height * 0.42, 0)
                tip.Parent = spire
                local crown = emitter(tip, {
                    Name = "SpireFire",
                    Texture = BF.FIRE,
                    Rate = 0,
                    Lifetime = NumberRange.new(0.3, 0.5),
                    Speed = NumberRange.new(0.8 * u, 1.6 * u),
                    SpreadAngle = Vector2.new(18, 18),
                    EmissionDirection = Enum.NormalId.Top,
                    Acceleration = Vector3.new(0, 2 * u, 0),
                    Size = NumberSequence.new({
                        NumberSequenceKeypoint.new(0, 0.38 * u),
                        NumberSequenceKeypoint.new(1, 0.06 * u),
                    }),
                    Color = ColorSequence.new(BF.SOUL_HOT, BF.SOUL),
                    Transparency = NumberSequence.new({
                        NumberSequenceKeypoint.new(0, 0.35),
                        NumberSequenceKeypoint.new(1, 1),
                    }),
                    Brightness = 1.2,
                })
                task.delay(delay + 0.1, function()
                    if crown.Parent then
                        crown.Rate = if reduced then 6 else 10
                    end
                end)
                task.delay(delay + 0.8, function()
                    if crown.Parent then
                        crown.Enabled = false
                    end
                end)
                if not reduced then
                    local root = Instance.new("Attachment")
                    root.WorldPosition = base
                    root.Parent = holder
                    local dust = emitter(root, {
                        Name = "SpireDust",
                        Texture = BF.SMOKE,
                        Rate = 0,
                        LightEmission = 0.15,
                        Lifetime = NumberRange.new(0.5, 0.8),
                        Speed = NumberRange.new(1 * u, 2 * u),
                        SpreadAngle = Vector2.new(70, 70),
                        EmissionDirection = Enum.NormalId.Top,
                        Drag = 3,
                        Size = NumberSequence.new({
                            NumberSequenceKeypoint.new(0, 0.3 * u),
                            NumberSequenceKeypoint.new(1, 0.9 * u),
                        }),
                        Color = ColorSequence.new(Color3.fromRGB(150, 160, 185)),
                        Transparency = NumberSequence.new({
                            NumberSequenceKeypoint.new(0, 0.5),
                            NumberSequenceKeypoint.new(1, 1),
                        }),
                    })
                    task.delay(delay, function()
                        if dust.Parent then
                            dust:Emit(5)
                        end
                    end)
                end
            end
        end

        local bones = table.clone(BF.BONES)
        for _, name in { "BrowL", "BrowR" } do
            table.insert(bones, name)
        end
        PetRig.Profiles.BonefireDragon = {
            Skinned = true,
            Bones = bones,
            Points = { "Head", "EyeL", "EyeR" },
            GlowColors = {
                ["3d7bff"] = BF.SOUL, -- its soul fire (and the fire in its throat)
                ["4aa6ff"] = BF.EYE, -- the cold light deep in its sockets
            },
            Effects = {
                Light = "Soul",
                Pulse = "Soul",
                Blast = "OssuaryPyre",
                NovaLight = 1.5,
            },
            Colors = {
                Gold = BF.SOUL,
                Amber = BF.SOUL_DEEP,
                Orange = BF.SOUL,
                Sun = BF.SOUL_HOT,
                Ivory = BF.BONE,
            },
            Animate = animateBonefireDragon,
        }
    end
end
