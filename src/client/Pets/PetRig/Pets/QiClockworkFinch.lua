-- QiClockworkFinch: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Players, tweenAfter, pose, smoothstep, Blasts, addStance = K.PetRig, K.Players, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.addStance


    do
        -- The Qi Clockwork Finch (skinned, every piece rigid on its own bone, as an automaton's are): a cloisonne singing-bird automaton, gilt wire cells
        -- filled with enamel in a goldfinch's colours, onyx eyes behind brass shutters, a gear-toothed brass collar with Qi seeping from its seam, and on
        -- its back a jade bi disc for a winding key. It moves like a clock: its head turns in ticks, the seam flickering on each one; its wings whirr in
        -- quick bursts and glide between; it blinks with a snap of its shutters. Now and then it sings a few notes, tail fanned, or cocks its head. Still
        -- a long while, it runs down: its beats slow, its head and wings droop, its eyes half shut, its key creaking to a stop; then the key spins and it
        -- snaps back to life. Moving, it leans into its flight, legs tucked. Its special, The Hour of a Lost City: its key spins hard, winding it (to
        -- 0.3); it rears and sings, tail fanned (the burst, 0.42: Blasts.HourOfALostCity): round it a city of jade light rises out of the ground, towers
        -- and pagodas of a place that no longer exists; the hour strikes through it, three times, every window flaring; then it sinks away.
        local QF = {
            FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
            LID_HINGE = { L = Vector3.new(0.7801, 0.0688, -0.6219), R = Vector3.new(0.7801, -0.0688, 0.6219) }, -- both shutters of an eye turn on this line
            BLINK_UPPER = math.rad(78), -- (the two add past the 104 degrees between the shutters' edges)
            BLINK_LOWER = math.rad(34),
            KEY_AXIS = Vector3.new(0, 0.6, 0.8), -- its key turns on its stem (game axes)
            -- its stances (game axes; turns x, y, z), each checked in Blender (clockwork_finch.py: wing plates against body, head, key and the other wing;
            -- tail against wings; head against body and key; lower beak against body; and along every slerp between them)
            FLAP_UP = { WingL = { 0, 0, -0.55 }, WingR = { 0, 0, 0.55 }, WingTipL = { 0, -0.08, -0.25 }, WingTipR = { 0, 0.08, 0.25 } },
            FLAP_DOWN = { WingL = { 0, -0.22, 0.38 }, WingR = { 0, 0.22, -0.38 }, WingTipL = { 0, 0, 0.32 }, WingTipR = { 0, 0, -0.32 } },
            FOLD = { WingL = { 0, 0, 0.04 }, WingR = { 0, 0, -0.04 }, WingTipL = { 0, 0.6, 0.05 }, WingTipR = { 0, -0.6, -0.05 } },
            SING = { Head = { 0.2, 0, 0 }, Jaw = { -0.35, 0, 0 } },
            TAIL_FAN = { Tail1 = { 0, 0.35, 0 }, Tail2 = { 0, 0.17, 0 }, Tail4 = { 0, -0.17, 0 }, Tail5 = { 0, -0.35, 0 } },
            TAIL_UP = { Tail1 = { -0.3, 0, 0 }, Tail2 = { -0.3, 0, 0 }, Tail3 = { -0.3, 0, 0 }, Tail4 = { -0.3, 0, 0 }, Tail5 = { -0.3, 0, 0 } },
            RUN_DOWN = { Body = { -0.1, 0, 0 }, Head = { -0.35, 0, 0.15 }, Tail1 = { 0.2, 0, 0 }, Tail2 = { 0.2, 0, 0 }, Tail3 = { 0.2, 0, 0 }, Tail4 = { 0.2, 0, 0 },
                Tail5 = { 0.2, 0, 0 }, WingL = { 0, -0.1, 0.2 }, WingR = { 0, 0.1, -0.2 }, WingTipL = { 0, 0.3, 0.1 }, WingTipR = { 0, -0.3, -0.1 } },
            TILT = { Head = { 0, 0, 0.35 } },
            LEGS_TUCK = { LegL = { 0.4, 0, 0 }, LegR = { 0.4, 0, 0 } },
            TICK = 0.5, -- seconds between the ticks of its head
            WHIRR = 7, -- wing beats a second in a burst
            BONES = { "Body", "Head", "Jaw", "Key", "EyeL", "EyeR", "WingL", "WingTipL", "WingR", "WingTipR", "Tail1", "Tail2", "Tail3", "Tail4", "Tail5",
                "LegL", "LegR" },
            QI = Color3.fromRGB(28, 245, 143), -- the Qi it is wound with: jade light
            QI_DIM = Color3.fromRGB(16, 140, 86),
            QI_BRIGHT = Color3.fromRGB(150, 255, 200),
            GOLD = Color3.fromRGB(236, 192, 96),
            LAPIS = Color3.fromRGB(34, 58, 150),
            CORAL = Color3.fromRGB(226, 74, 58),
            IVORY = Color3.fromRGB(246, 240, 226),
        }

        function QF.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        -- Once: a soft jade light at its key.
        function QF.init(rig, s)
            s.inited = true
            local key = rig.points.Key
            if key then
                local a = Instance.new("Attachment")
                a.Name = "QiGlow"
                a.Parent = key
                local light = Instance.new("PointLight")
                light.Name = "QiLight"
                light.Color = QF.QI
                light.Range = 3.5 * rig.unit
                light.Brightness = 0.4
                light.Shadows = false
                light.Parent = a
                s.light = light
            end
        end

        local function animateQiClockworkFinch(rig, s, moving, fly, nova)
            if not s.inited then
                QF.init(rig, s)
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > QF.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special: wound hard (to 0.3); rearing to sing, tail fanned (to 0.42, the burst); singing on (to 0.85); settling
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local special = progress > 0
            local wind = smoothstep(0.02, 0.1, progress) * (1 - smoothstep(0.3, 0.38, progress))
            local rear = smoothstep(0.3, 0.42, progress) * (1 - smoothstep(0.85, 0.98, progress))

            -- still a long while, it runs down; then its key spins and it snaps back to life
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            if s.still > 16 and not s.runDownAt then
                s.runDownAt = t
            end
            if s.runDownAt and (pace > 0.05 or special) then
                s.runDownAt = nil
            end
            local down, rewind = 0, 0
            if s.runDownAt then
                local a = t - s.runDownAt
                down = smoothstep(0, 2.2, a) * (1 - smoothstep(4.6, 4.75, a)) -- winding down, a long droop, then snapping back
                rewind = if a > 3.6 and a < 4.8 then math.sin(math.pi * (a - 3.6) / 1.2) else 0
                if a > 5 then
                    s.runDownAt = nil
                    s.still = 0
                end
            end

            -- now and then: a few sung notes, tail fanned; or a cock of its head
            s.nextFidget = s.nextFidget or t + 4
            if t >= s.nextFidget then
                s.fidgetAt = t
                s.fidgetKind = if math.random() < 0.55 then "sing" else "tilt"
                s.fidgetSide = if math.random() < 0.5 then 1 else -1
                s.nextFidget = t + 5 + math.random() * 6
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / 1.6, 0, 1) else 1
            local fidget = math.sin(math.pi * env) * (1 - pace) * (1 - down) * (if special then 0 else 1)
            local notes = if s.fidgetKind == "sing" then math.max(0, math.sin(env * math.pi * 6)) * fidget else 0

            local want = {}
            -- its wings: quick whirring bursts, gliding between (in flight, beating on); slowing to nothing as it runs down
            s.nextBurst = s.nextBurst or t
            if t >= s.nextBurst then
                s.burstAt = t
                s.burstLen = 0.6 + math.random() * 0.5
                s.nextBurst = t + s.burstLen + 0.4 + math.random() * 0.6
            end
            local bursting = if s.burstAt and t - s.burstAt < s.burstLen then 1 else 0
            local beating = math.max(bursting, pace, wind, rear) * (1 - down)
            s.beatAmt = (s.beatAmt or 0) + (beating - (s.beatAmt or 0)) * math.min(1, dt * 10)
            s.phase = ((s.phase or 0) + dt * QF.WHIRR * (0.4 + 0.6 * s.beatAmt) * (1 - 0.7 * down) * 2 * math.pi) % (2 * math.pi)
            local b = math.sin(s.phase)
            addStance(want, QF.FLAP_UP, math.max(0, b) * (0.25 + 0.75 * s.beatAmt) * (1 - rear) + 0.25 * (1 - s.beatAmt) * (1 - down) * (1 - rear))
            addStance(want, QF.FLAP_DOWN, math.max(0, -b) * (0.25 + 0.75 * s.beatAmt) * (1 - rear))
            addStance(want, QF.FLAP_UP, rear * (0.7 + 0.3 * b))
            addStance(want, QF.FOLD, wind * 0.8)
            addStance(want, QF.RUN_DOWN, down)
            addStance(want, QF.SING, math.max(rear, notes))
            addStance(want, QF.TAIL_FAN, math.max(rear, if s.fidgetKind == "sing" then fidget else 0))
            addStance(want, QF.TAIL_UP, pace * 0.6)
            addStance(want, QF.LEGS_TUCK, math.max(pace, 0.4))
            addStance(want, { Body = { -0.15, 0, 0 } }, pace)
            if s.fidgetKind == "tilt" then
                addStance(want, { Head = { 0, 0, 0.35 * (s.fidgetSide or 1) } }, fidget)
            end
            addStance(want, { Jaw = { -0.35 * math.max(0, math.sin(t * 22)), 0, 0 } }, rear * (if progress > 0.42 then 1 else 0)) -- singing through its special

            -- its gaze, in ticks: each half second its head snaps to where it wants to look
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2 + math.random() * 3
                s.atYou = math.random() < 0.6
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.6, (math.random() - 0.5) * 0.4
            end
            local calm = (1 - 0.7 * pace) * (1 - down) * (1 - rear) * (1 - wind)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -1, 1) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.6, -0.3, 0.3) else s.gazePitch) * calm
            local tick = math.floor(t / QF.TICK)
            if tick ~= s.lastTick then
                s.lastTick = tick
                s.tickAt = t
                s.yawTo = math.floor(wantYaw / 0.15 + 0.5) * 0.15 -- in steps, as a clock hand moves
                s.pitchTo = math.floor(wantPitch / 0.1 + 0.5) * 0.1
            end
            s.yaw = (s.yaw or 0) + ((s.yawTo or 0) - (s.yaw or 0)) * math.min(1, dt * 22)
            s.pitch = (s.pitch or 0) + ((s.pitchTo or 0) - (s.pitch or 0)) * math.min(1, dt * 22)
            addStance(want, { Head = { 0.4 * s.pitch, 0.55 * s.yaw, 0.05 * s.yaw }, EyeL = { 0.2 * s.pitch, 0.2 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.2 * s.yaw, 0 } }, 1)
            local tickFlash = if s.tickAt then math.max(0, 1 - (t - s.tickAt) / 0.15) else 0

            local bob = (0.012 * math.sin(t * 2.1) - 0.02 * down) * u
            for _, name in QF.BONES do
                local a = want[name] or Vector3.zero
                if name == "Key" then
                    continue
                end
                pose(m[name], CFrame.new(0, if name == "Body" then bob else 0, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- its key: turning slowly as it runs; creaking to a stop as it runs down; spinning as it rewinds and as it is wound
            local keySpeed = (0.7 + 0.8 * pace) * (1 - down) + 9 * rewind + 10 * wind + 2 * rear
            s.keyAngle = ((s.keyAngle or 0) + dt * keySpeed) % (2 * math.pi)
            pose(m.Key, CFrame.fromAxisAngle(QF.KEY_AXIS, s.keyAngle))

            -- the Qi in it: the seam flickering at each tick; brighter as it is wound, dim as it runs down
            local glow = math.clamp(0.45 + 0.35 * tickFlash + 0.6 * math.max(wind, rear, rewind) - 0.4 * down, 0, 1)
            local qiColour = QF.QI_DIM:Lerp(QF.QI, math.min(1, glow * 1.4)):Lerp(QF.QI_BRIGHT, math.max(0, glow - 0.7) / 0.3)
            for _, key in { "Seam", "KeyLight" } do
                local part = rig.parts[key]
                if part then
                    part.Color = qiColour
                end
            end
            if s.light then
                s.light.Brightness = 0.25 + 1.4 * math.max(wind, rear, rewind) + 0.2 * tickFlash
            end

            -- its shutters: a quick snap of a blink; half shut as it runs down; wide as it sings out
            local wide = rear
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.14
                if a >= 1 then
                    s.nextBlink = t + 2.5 + math.random() * 4
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local close = math.max(blink, 0.55 * down) * (1 - wide)
            local upper = QF.BLINK_UPPER * close - math.rad(8) * wide
            local lower = QF.BLINK_LOWER * close - math.rad(4) * wide
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(QF.LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(QF.LID_HINGE[side], lower))
            end
        end

        -- Its song, the hour of a city that no longer exists (animateQiClockworkFinch, the burst): round it, out of the ground, a city of jade light rises,
        -- towers and tiered pagodas with gold roofs, a bell tower behind it; the hour strikes, three times, every window flaring; then the city sinks
        -- back into the ground and is gone (by 1.8 s).
        function Blasts.HourOfALostCity(rig, fx)
            local u = rig.unit
            local reduced = QF.reduced()
            local params = RaycastParams.new()
            params.FilterDescendantsInstances = { rig.model }
            local hit = workspace:Raycast(rig.rootPart.Position, Vector3.new(0, -12 * u, 0), params)
            local ground = if hit then hit.Position else rig.rootPart.Position - Vector3.new(0, 1.5 * u, 0)
            local facing = rig.rootPart.CFrame.LookVector
            local base = math.atan2(facing.X, facing.Z)
            local RISE, HOLD, SINK = 0.45, 0.75, 0.5
            local parts = {}
            local function piece(size, cf, colour, see)
                local p = fx.neon(size, cf - Vector3.new(0, 0, 0), colour)
                p.Transparency = see
                table.insert(parts, { part = p, see = see })
                return p
            end
            -- a building: its storeys, each under a gold roof of two stepped eaves (one flat slab read as a plate), a spire; built at its spot, then sunk
            -- below the ground to rise. (Built at a third of this, the city stood knee-high round it and read as lanterns, seen in Play.)
            local function building(at, width, storeys, spire)
                local group = {}
                local y = 0
                local w = width
                for k = 1, storeys do
                    local h = (1.5 - 0.15 * k) * u
                    table.insert(group, piece(Vector3.new(w, h, w), CFrame.new(at + Vector3.new(0, y + h / 2, 0)), QF.QI, 0.72)) -- (at 0.6, up close, solid glowing boxes)
                    y += h
                    table.insert(group, piece(Vector3.new(w * 1.6, 0.1 * u, w * 1.6), CFrame.new(at + Vector3.new(0, y + 0.05 * u, 0)), QF.GOLD, 0.5))
                    table.insert(group, piece(Vector3.new(w * 1.2, 0.12 * u, w * 1.2), CFrame.new(at + Vector3.new(0, y + 0.16 * u, 0)), QF.GOLD, 0.45))
                    y += 0.22 * u
                    w *= 0.8
                end
                if spire then
                    table.insert(group, piece(Vector3.new(0.12 * u, 1.1 * u, 0.12 * u), CFrame.new(at + Vector3.new(0, y + 0.55 * u, 0)), QF.GOLD, 0.3))
                    y += 1.1 * u
                end
                return group, y
            end
            local count = if reduced then 5 else 8
            local groups = {}
            for k = 1, count do
                local a = base + math.pi + (k - (count + 1) / 2) / count * 2 * math.pi * 0.85 -- round it, the widest gap in front of it (where you are)
                local r = (5.2 + 1.6 * ((k * 7) % 3) / 2) * u
                local at = ground + Vector3.new(math.sin(a) * r, 0, math.cos(a) * r)
                local g, h = building(at, (1.1 + 0.3 * ((k * 5) % 3)) * u, 2 + (k * 3) % 3, k % 2 == 0)
                table.insert(groups, { parts = g, height = h, delay = 0.04 * math.abs(k - (count + 1) / 2) })
            end
            -- the bell tower, behind it, tallest
            local back = ground - Vector3.new(facing.X, 0, facing.Z).Unit * 8 * u
            local tower, th = building(back, 1.5 * u, 5, true)
            table.insert(groups, { parts = tower, height = th, delay = 0.1 })
            -- rising out of the ground; holding; sinking back
            for _, g in groups do
                for _, p in g.parts do
                    local final = p.CFrame
                    p.CFrame = final - Vector3.new(0, g.height + 0.1 * u, 0)
                    tweenAfter(g.delay, p, TweenInfo.new(RISE, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), { CFrame = final })
                    tweenAfter(g.delay + RISE + HOLD, p, TweenInfo.new(SINK, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                        CFrame = final - Vector3.new(0, g.height + 0.1 * u, 0), Transparency = 1,
                    })
                end
            end
            -- the hour strikes: three times, every window flaring and fading
            for k = 0, 2 do
                local at = RISE + 0.05 + k * 0.22
                for _, entry in parts do
                    if entry.part.Color == QF.QI then
                        tweenAfter(at, entry.part, TweenInfo.new(0.05), { Transparency = 0.15, Color = QF.QI_BRIGHT })
                        tweenAfter(at + 0.05, entry.part, TweenInfo.new(0.16), { Transparency = entry.see, Color = QF.QI })
                    end
                end
            end
            -- a soft jade light over it all, striking with the hour
            local light = Instance.new("PointLight")
            light.Color = QF.QI
            light.Range = 8 * u
            light.Brightness = 0.2 -- (brighter and wider, it lit the finch itself green and its gold wires lime, seen in Play)
            light.Shadows = false
            local holder = fx.neon(Vector3.one * 0.05, CFrame.new(ground + Vector3.new(0, 3 * u, 0)), QF.QI)
            holder.Transparency = 1
            light.Parent = holder
            for k = 0, 2 do
                tweenAfter(RISE + 0.05 + k * 0.22, light, TweenInfo.new(0.05), { Brightness = 0.5 })
                tweenAfter(RISE + 0.1 + k * 0.22, light, TweenInfo.new(0.16), { Brightness = 0.2 })
            end
            tweenAfter(RISE + HOLD, light, TweenInfo.new(SINK), { Brightness = 0 })
        end

        local bones = table.clone(QF.BONES)
        for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
            table.insert(bones, name)
        end
        PetRig.Profiles.QiClockworkFinch = {
            Skinned = true,
            Bones = bones,
            Points = { "Body", "Head", "Key" },
            GlowColors = {
                ["1cf58f"] = QF.QI, -- the Qi it is wound with, in its collar's seam and its key's hole
                ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its onyx eyes
            },
            Effects = {
                Blast = "HourOfALostCity",
                NovaLight = 1.5,
            },
            Colors = {
                Gold = QF.GOLD,
                Amber = QF.QI,
                Orange = QF.CORAL,
                Sun = QF.QI_BRIGHT,
                Ivory = QF.IVORY,
            },
            Animate = animateQiClockworkFinch,
        }
    end
end
