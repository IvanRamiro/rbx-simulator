-- LotusElephant: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Players, RunService, TweenService, SPARKLE, tweenAfter, pose, smoothstep, Blasts, addStance, dropToGround = K.PetRig, K.Players, K.RunService, K.TweenService, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.addStance, K.dropToGround



    do
        -- The Lotus Elephant (skinned; its id stays ThousandEyedGuardian, the pet it replaced): a white elephant carrying a living lotus pond on its back,
        -- after the white elephant of the old stories that brings the rain, and the elephant that carries peace on its back. A young Asian elephant, its
        -- twin-domed head the highest point of it, its skin the pale of white jade, freckled pink on its trunk and ear rims; for a saddle cloth a great lotus
        -- leaf, and on it a lotus in bloom round a seed-pod whose seeds glow gold with Qi; gold-capped milk tusks; gold anklets with a bell on each. It
        -- stands calm, fanning its ears slowly, as elephants do; its trunk sways and now and then lifts to greet you, swings side to side, or rises for a
        -- short trumpet; it looks about, often at you, and blinks slowly. Still a long while, it dozes on its feet, one hind foot resting on its toe, and
        -- its lotus half closes, as a lotus does at night. It walks unhurried, one foot at a time (hind, fore, hind, fore), its head nodding; in the air
        -- it swims, as elephants do, its trunk up like a snorkel and its legs paddling. Its special, Rain Over Dry Fields: it raises its trunk to the sky
        -- as the lotus on its back opens wide and its seeds blaze (to 0.42); it sprays (the burst: Blasts.RainOverDryFields): a fountain of golden water
        -- arcs up out of its trunk and falls in a ring round it, a ripple where each drop lands, a fine golden rain over it; it flaps its ears, content.
        local LE = {
            FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
            SOLE = 0.4623, -- metres from the middle of its box (the RootPart's cube counted) down to its feet (lotus_elephant.py)
            LID_HINGE = { L = Vector3.new(0.7584, -0.1385, -0.6369), R = Vector3.new(0.7584, 0.1385, 0.6369) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(28), -- (the two add past the 33 degrees between its lids' edges)
            BLINK_LOWER = math.rad(8),
            -- each inner petal of its lotus opens on its own line (game axes): a positive turn tips it outward (lotus_elephant.py petal_frames)
            PETAL_HINGE = { Vector3.new(-1, 0, 0), Vector3.new(-0.7071, 0, 0.7071), Vector3.new(0, 0, 1), Vector3.new(0.7071, 0, 0.7071),
                Vector3.new(1, 0, 0), Vector3.new(0.7071, 0, -0.7071), Vector3.new(0, 0, -1), Vector3.new(-0.7071, 0, -0.7071) },
            PETAL_OPEN = 0.45, -- radians its inner petals open in its special (checked in Blender: they come to lie between the outer ring's)
            -- its walk: each leg's turns (upper, middle, lower) at sixteen steps through the cycle, found in Blender by a solver that keeps each foot flat
            -- on the ground as it slides back and lifts it 4 cm as it swings forward (lotus_elephant.py find_walk: planted within 1 mm, no torn skin)
            WALK_FRONT = { { 0.166, -0.042, -0.041 }, { 0.141, -0.039, -0.039 }, { 0.112, -0.033, -0.035 }, { 0.082, -0.026, -0.029 }, { 0.047, -0.015, -0.018 }, { 0.01, -0.003, -0.004 }, { -0.024, 0.005, 0.009 }, { -0.051, 0.003, 0.015 }, { -0.067, -0.013, 0.008 }, { -0.075, -0.038, -0.011 }, { -0.087, -0.058, -0.027 }, { -0.296, 0.179, 0.23 }, { -0.444, 0.423, 0.447 }, { -0.436, 0.525, 0.505 }, { -0.322, 0.501, 0.441 }, { -0.126, 0.333, 0.262 } },
            WALK_HIND = { { 0.062, 0.138, 0.002 }, { 0.06, 0.093, 0.008 }, { 0.053, 0.058, 0.01 }, { 0.042, 0.032, 0.008 }, { 0.026, 0.013, 0.005 }, { 0.006, 0.002, 0.002 }, { -0.017, -0.003, -0.003 }, { -0.044, -0.001, -0.008 }, { -0.075, 0.007, -0.012 }, { -0.109, 0.021, -0.016 }, { -0.147, 0.043, -0.022 }, { -0.071, -0.114, -0.023 }, { 0.119, -0.361, -0.072 }, { 0.262, -0.462, -0.103 }, { 0.323, -0.424, -0.08 }, { 0.265, -0.242, -0.008 } },
            WALK_LEAD = { BL = 0, FL = 0.25, BR = 0.5, FR = 0.75 },
            WALK_RATE = 1.0, -- cycles a second at a full walk: unhurried
            -- its stances (game axes; turns x, y, z), each checked in Blender against the ground and for torn skin (lotus_elephant.py)
            TRUMPET = { Neck = { 0.12, 0, 0 }, Head = { 0.22, 0, 0 }, Trunk1 = { 0.55, 0, 0 }, Trunk2 = { 0.6, 0, 0 }, Trunk3 = { 0.55, 0, 0 },
                Trunk4 = { 0.45, 0, 0 }, Trunk5 = { 0.4, 0, 0 }, Trunk6 = { 0.35, 0, 0 }, EarL = { 0, -0.5, 0 }, EarR = { 0, 0.5, 0 } },
            GREET = { Head = { 0.08, 0, 0 }, Trunk1 = { 0.3, 0, 0 }, Trunk2 = { 0.35, 0, 0 }, Trunk3 = { 0.35, 0, 0 }, Trunk4 = { 0.45, 0, 0 },
                Trunk5 = { 0.55, 0, 0 }, Trunk6 = { 0.6, 0, 0 }, EarL = { 0, -0.45, 0 }, EarR = { 0, 0.45, 0 } },
            CURL = { Trunk3 = { -0.2, 0, 0 }, Trunk4 = { -0.35, 0, 0 }, Trunk5 = { -0.45, 0, 0 }, Trunk6 = { -0.5, 0, 0 } },
            SWING = { Trunk1 = { 0, 0.15, 0 }, Trunk2 = { 0, 0.2, 0 }, Trunk3 = { 0, 0.2, 0 }, Trunk4 = { 0, 0.2, 0 }, Trunk5 = { 0, 0.15, 0 }, Trunk6 = { 0, 0.1, 0 } },
            DOZE = { Neck = { -0.05, 0, 0 }, Head = { -0.1, 0, 0 }, Trunk3 = { -0.1, 0, 0 }, Trunk4 = { -0.2, 0, 0 }, Trunk5 = { -0.3, 0, 0 },
                Trunk6 = { -0.35, 0, 0 }, LegBR1 = { 0.08, 0, 0 }, LegBR2 = { -0.22, 0, 0 }, LegBR3 = { 0.22, 0, 0 }, PawBR = { -0.1, 0, 0 },
                Hips = { 0, 0, -0.03 }, EarL = { 0, 0.06, 0 }, EarR = { 0, -0.06, 0 } },
            SWIM = { Head = { 0.1, 0, 0 }, Trunk1 = { 0.3, 0, 0 }, Trunk2 = { 0.35, 0, 0 }, Trunk3 = { 0.3, 0, 0 }, Trunk4 = { 0.25, 0, 0 },
                EarL = { 0, -0.3, 0 }, EarR = { 0, 0.3, 0 } },
            FIDGET_TIME = { greet = 2.2, flap = 1.4, swing = 2.6, trumpet = 1.8 },
            SEED = Color3.fromRGB(255, 170, 30), -- its seeds' Neon (deeper than its ffc24a paint: Neon pales to white)
            SEED_HOT = Color3.fromRGB(255, 214, 110),
            RAIN = Color3.fromRGB(255, 186, 50), -- its golden rain (saturated, or Neon blooms it white)
            RAIN_DEEP = Color3.fromRGB(230, 140, 30),
            RIPPLE = Color3.fromRGB(255, 220, 140),
            G = 6, -- metres a second squared its rain falls by: slower than the world's, a little dreamlike
            BONES = { "Hips", "Body", "Chest", "Shoulders", "Neck", "Head", "EyeL", "EyeR", "EarL", "EarR", "Tail1", "Tail2", "Tail3", "Lotus" },
        }
        for k = 1, 6 do
            table.insert(LE.BONES, "Trunk" .. k)
        end
        for k = 1, 8 do
            table.insert(LE.BONES, "Petal" .. k)
        end
        for _, key in { "FL", "FR", "BL", "BR" } do
            for k = 1, 3 do
                table.insert(LE.BONES, "Leg" .. key .. k)
            end
            table.insert(LE.BONES, "Paw" .. key)
        end

        function LE.legs4(into, f, b)
            for _, side in { "L", "R" } do
                for k = 1, 3 do
                    into["LegF" .. side .. k] = { f[k], 0, 0 }
                    into["LegB" .. side .. k] = { b[k], 0, 0 }
                end
                into["PawF" .. side] = { -(f[1] + f[2] + f[3]), 0, 0 }
                into["PawB" .. side] = { -(b[1] + b[2] + b[3]), 0, 0 }
            end
            return into
        end
        LE.legs4(LE.SWIM, { 0.35, -0.3, 0.1 }, { -0.35, 0.3, -0.1 })

        function LE.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        function LE.walkAt(rows, g)
            local n = #rows
            local x = (g % 1) * n
            local i = math.floor(x)
            local w = x - i
            local a, b = rows[i % n + 1], rows[(i + 1) % n + 1]
            return { a[1] + (b[1] - a[1]) * w, a[2] + (b[2] - a[2]) * w, a[3] + (b[3] - a[3]) * w }
        end

        local function animateLotusElephant(rig, s, moving, fly, nova)
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local special = progress > 0
            local raise = smoothstep(0.04, 0.36, progress) * (1 - smoothstep(0.62, 0.86, progress))
            local bloom = smoothstep(0.08, 0.4, progress) * (1 - smoothstep(0.75, 0.98, progress))
            local content = smoothstep(0.8, 0.84, progress) * (1 - smoothstep(0.93, 0.99, progress))
            -- its seeds glow gold with Qi, brighter as its lotus opens
            local seeds = rig.parts.Seeds
            if seeds then
                local glow = math.clamp(0.35 + 0.1 * math.sin(t * 1.1) + 0.65 * bloom, 0, 1)
                seeds.Color = LE.SEED:Lerp(LE.SEED_HOT, glow)
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > LE.FAR then
                return
            end
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, LE.SOLE)

            -- still a long while, it dozes on its feet; now and then it greets you, flaps its ears, swings its trunk or gives a short trumpet
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            local wantDoze = if s.still > 16 then 1 else 0
            s.doze = (s.doze or 0) + (wantDoze - (s.doze or 0)) * math.min(1, dt * (if wantDoze > (s.doze or 0) then 0.5 else 5))
            local doze = smoothstep(0, 1, s.doze)
            s.nextFidget = s.nextFidget or t + 4
            if t >= s.nextFidget then
                local r = math.random()
                s.fidgetAt = t
                s.fidgetKind = if r < 0.3 then "greet" elseif r < 0.55 then "flap" elseif r < 0.82 then "swing" else "trumpet"
                s.nextFidget = t + LE.FIDGET_TIME[s.fidgetKind] + 4 + math.random() * 5
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / LE.FIDGET_TIME[s.fidgetKind], 0, 1) else 1
            local calmness = (1 - pace) * (1 - doze) * (if special then 0 else 1)
            local fidget = smoothstep(0, 0.2, env) * (1 - smoothstep(0.75, 1, env)) * calmness
            local function kind(name)
                return if s.fidgetKind == name then fidget else 0
            end

            local want = {}
            addStance(want, LE.TRUMPET, math.max(raise, 0.7 * kind("trumpet")))
            addStance(want, LE.GREET, kind("greet") * (1 - raise))
            addStance(want, { Trunk5 = { 0, 0.25 * math.sin(t * 7), 0 }, Trunk6 = { 0.1 * math.sin(t * 7 + 0.5), 0.3 * math.sin(t * 7 - 0.6), 0 } }, kind("greet"))
            addStance(want, LE.SWING, kind("swing") * 2.2 * math.sin(t * 2.4))
            addStance(want, LE.DOZE, doze)

            -- its ears: fanning slowly all the time, as an elephant's do to cool it; flapping fast now and then, and when its special is done
            local fan = 0.12 * (0.5 + 0.5 * math.sin(t * (if doze > 0.5 then 0.7 else 1.3))) * (1 - 0.5 * doze)
            local flap = math.max(kind("flap"), content) * (0.5 + 0.5 * math.sin(t * 11))
            addStance(want, { EarL = { 0, -(fan + 0.45 * flap), 0.03 * flap }, EarR = { 0, fan + 0.45 * flap, -0.03 * flap } }, 1)

            -- its walk: hind, fore, hind, fore, each foot set down flat; its head nodding, its trunk swinging with its steps
            local onFoot = moving * (1 - fly)
            s.stride = (s.stride or 0) + dt * LE.WALK_RATE * onFoot
            for key, lead in LE.WALK_LEAD do
                local rows = if string.sub(key, 1, 1) == "F" then LE.WALK_FRONT else LE.WALK_HIND
                local a = LE.walkAt(rows, s.stride + lead)
                addStance(want, {
                    ["Leg" .. key .. "1"] = { a[1], 0, 0 },
                    ["Leg" .. key .. "2"] = { a[2], 0, 0 },
                    ["Leg" .. key .. "3"] = { a[3], 0, 0 },
                    ["Paw" .. key] = { -(a[1] + a[2] + a[3]), 0, 0 },
                }, onFoot)
            end
            local step = math.sin(2 * math.pi * s.stride)
            local nod = math.sin(4 * math.pi * s.stride)
            addStance(want, { Head = { 0.035 * nod, 0, 0 }, Shoulders = { 0, 0.03 * step, 0.02 * step }, Hips = { 0, -0.03 * step, -0.015 * step },
                Lotus = { 0.03 * nod, 0, 0.03 * step } }, onFoot)
            addStance(want, LE.SWING, onFoot * 0.5 * step)
            -- in the air it swims, its legs paddling
            addStance(want, LE.SWIM, fly)
            for key, lead in LE.WALK_LEAD do
                local paddle = math.sin(t * 3.2 + lead * 2 * math.pi)
                addStance(want, { ["Leg" .. key .. "1"] = { 0.25 * paddle, 0, 0 }, ["Leg" .. key .. "2"] = { -0.2 * math.max(0, paddle), 0, 0 } }, fly)
            end

            -- breathing; its trunk swaying a little; its head looking about, often at you
            local breath = math.sin(t * 1.0)
            addStance(want, { Chest = { 0.01 * breath, 0, 0 }, Body = { 0.006 * breath, 0, 0 } }, 1)
            local sway = (1 - math.max(raise, kind("greet"), kind("swing"))) * (1 - 0.5 * pace)
            addStance(want, { Trunk2 = { 0.02 * math.sin(t * 0.7), 0.04 * math.sin(t * 0.5), 0 }, Trunk4 = { 0.03 * math.sin(t * 0.7 - 0.8), 0.06 * math.sin(t * 0.5 - 0.9), 0 },
                Trunk6 = { 0.05 * math.sin(t * 0.9 - 1.5), 0.08 * math.sin(t * 0.6 - 1.6), 0 } }, sway)
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 3 + math.random() * 4
                s.atYou = math.random() < 0.55
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 0.8, (math.random() - 0.5) * 0.2
            end
            local calm = (1 - 0.6 * pace) * (1 - raise) * (1 - 0.9 * doze)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.6, 0.6) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.4, -0.12, 0.25) else s.gazePitch) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 1.8) -- (slow: an elephant turns its head deliberately)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 1.8)
            addStance(want, {
                Neck = { 0.1 * s.pitch, 0.3 * s.yaw, 0 }, Head = { 0.2 * s.pitch, 0.35 * s.yaw, 0.06 * s.yaw },
                EyeL = { 0.2 * s.pitch, 0.2 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
            }, 1)
            -- its tail: swishing
            local swish = math.sin(t * 1.6)
            addStance(want, { Tail1 = { 0.05, 0.25 * swish, 0 }, Tail2 = { 0, 0.3 * math.sin(t * 1.6 - 0.6), 0 }, Tail3 = { 0, 0.35 * math.sin(t * 1.6 - 1.2), 0 } },
                1 - 0.6 * doze)
            -- its lotus: breathing a little open and closed; opening wide in its special; half closing as it dozes, as a lotus closes at night
            addStance(want, { Lotus = { 0.02 * math.sin(t * 0.8), 0, 0.02 * math.sin(t * 0.6) } }, 1)
            local open = LE.PETAL_OPEN * bloom + 0.03 * math.sin(t * 0.9) - 0.12 * doze

            local lift = -drop
            for _, name in LE.BONES do
                local a = want[name] or Vector3.zero
                if string.sub(name, 1, 5) == "Petal" then
                    local k = tonumber(string.sub(name, 6))
                    pose(m[name], CFrame.fromAxisAngle(LE.PETAL_HINGE[k], open + 0.02 * math.sin(t * 1.3 + k)))
                else
                    pose(m[name], CFrame.new(0, if name == "Hips" then lift else 0, 0) * CFrame.Angles(a.X, a.Y, a.Z))
                end
            end

            -- its eyes: slow blinks; shut as it dozes; wide as it sprays
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.4
                if a >= 1 then
                    s.nextBlink = t + 3.5 + math.random() * 5
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local close = math.max(blink, doze) * (1 - raise)
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(LE.LID_HINGE[side], -LE.BLINK_UPPER * close + math.rad(6) * raise))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(LE.LID_HINGE[side], LE.BLINK_LOWER * close))
            end
        end

        -- Its trunk raised to the sky (animateLotusElephant), it sprays: a fountain of golden water arcs up out of its trunk and falls in a ring round
        -- it, a ripple spreading on the ground where each drop lands, a fine golden rain falling over it the while; all down by 1.9 s.
        function Blasts.RainOverDryFields(rig, fx)
            local u, metre = rig.unit, rig.meters
            local reduced = LE.reduced()
            local params = RaycastParams.new()
            params.FilterDescendantsInstances = { rig.model }
            local root = rig.rootPart.CFrame
            local function groundAt(at)
                local hit = workspace:Raycast(at + Vector3.new(0, 0.8 * metre, 0), Vector3.new(0, -12 * u, 0), params)
                return if hit then hit.Position else Vector3.new(at.X, rig.rootPart.Position.Y - LE.SOLE * metre, at.Z)
            end
            local feet = groundAt(root.Position)
            local tipBone = rig.points.Trunk6
            local tip = if tipBone then tipBone.TransformedWorldCFrame.Position else root.Position + Vector3.yAxis * metre
            local g = LE.G * metre

            -- a ripple: a thin ring of light running out over the ground and fading
            local function ripple(at, size)
                if not fx then
                    return
                end
                local ring = fx.neon(Vector3.new(0.01 * metre, 0.04 * metre, 0.04 * metre), CFrame.new(at + Vector3.yAxis * 0.01 * metre) * CFrame.Angles(0, 0, math.pi / 2), LE.RIPPLE)
                ring.Shape = Enum.PartType.Cylinder
                ring.Transparency = 0.35
                TweenService:Create(ring, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                    Size = Vector3.new(0.005 * metre, size * metre, size * metre), Transparency = 1,
                }):Play()
            end

            -- the jet: a column of water bursting up out of its trunk, thinning and fading
            local jetLength = 0.9 * metre
            local jet = fx.neon(Vector3.new(jetLength, 0.05 * metre, 0.05 * metre), CFrame.new(tip + Vector3.yAxis * jetLength / 2) * CFrame.Angles(0, 0, math.pi / 2), LE.RAIN)
            jet.Shape = Enum.PartType.Cylinder
            jet.Transparency = 0.15
            TweenService:Create(jet, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                Transparency = 1, Size = Vector3.new(jetLength * 1.2, 0.015 * metre, 0.015 * metre), CFrame = CFrame.new(tip + Vector3.yAxis * jetLength * 0.7) * CFrame.Angles(0, 0, math.pi / 2),
            }):Play()

            -- the fountain: drops of golden water flung up out of its trunk, falling in a ring round it, each drawing a short streak behind it (each
            -- flies its own arc, worked out to land in 1.1 to 1.3 s at its own distance). (Small and bare, 22 of them read as a few gold dots, seen in
            -- Play: an Epic's special must carry from across the island.)
            local count = if reduced then 12 else 28
            local drops = {}
            for k = 1, count do
                local a = (k / count) * 2 * math.pi + math.random() * 0.4
                local reach = (0.55 + 0.75 * math.random()) * metre
                local land = groundAt(feet + Vector3.new(math.cos(a) * reach, 0, math.sin(a) * reach))
                local T = 1.1 + 0.2 * math.random()
                local start = tip + Vector3.yAxis * 0.03 * metre
                local horizontal = Vector3.new(land.X - start.X, 0, land.Z - start.Z) / T
                local vy = (land.Y - start.Y + 0.5 * g * T * T) / T
                local size = (0.035 + 0.02 * math.random()) * metre
                local drop = fx.neon(Vector3.one * size, CFrame.new(start), if k % 3 == 0 then LE.RAIN_DEEP else LE.RAIN)
                drop.Shape = Enum.PartType.Ball
                drop.Transparency = 1
                local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
                a0.Position, a1.Position = Vector3.new(0, size * 0.4, 0), Vector3.new(0, -size * 0.4, 0)
                a0.Parent, a1.Parent = drop, drop
                local streak = Instance.new("Trail")
                streak.Attachment0, streak.Attachment1 = a0, a1
                streak.Lifetime = 0.22
                streak.FaceCamera = true
                streak.LightEmission = 1
                streak.LightInfluence = 0
                streak.Color = ColorSequence.new(LE.RIPPLE, LE.RAIN)
                streak.Transparency = NumberSequence.new(0.25, 1)
                streak.WidthScale = NumberSequence.new(1, 0.2)
                streak.Enabled = not reduced
                streak.Parent = drop
                table.insert(drops, { part = drop, start = start, v = horizontal + Vector3.yAxis * vy, T = T, delay = 0.12 * math.random(), land = land, done = false })
            end
            local began = os.clock()
            local conn
            conn = RunService.Heartbeat:Connect(function()
                local now = os.clock() - began
                local live = false
                for _, d in drops do
                    if not d.done then
                        live = true
                        local f = now - d.delay
                        if f >= 0 and d.part.Parent then
                            if f >= d.T then
                                d.done = true
                                d.part.Transparency = 1
                                ripple(d.land, 0.5 + 0.3 * math.random())
                            else
                                d.part.Transparency = 0.05
                                d.part.CFrame = CFrame.new(d.start + d.v * f - Vector3.yAxis * 0.5 * g * f * f)
                            end
                        elseif not d.part.Parent then
                            d.done = true
                        end
                    end
                end
                if not live then
                    conn:Disconnect()
                end
            end)
            task.delay(1.9, function()
                if conn.Connected then
                    conn:Disconnect()
                end
            end)

            -- a fine golden rain over it, from a disc of air above
            local cloud = fx.neon(Vector3.new(2.2 * metre, 0.05, 2.2 * metre), CFrame.new(feet + Vector3.yAxis * 1.6 * metre), LE.RAIN)
            cloud.Transparency = 1
            local rain = Instance.new("ParticleEmitter")
            rain.Texture = SPARKLE
            rain.Shape = Enum.ParticleEmitterShape.Box
            rain.EmissionDirection = Enum.NormalId.Bottom
            rain.Rate = if reduced then 18 else 45
            rain.Lifetime = NumberRange.new(0.7, 0.9)
            rain.Speed = NumberRange.new(1.8 * metre, 2.2 * metre)
            rain.SpreadAngle = Vector2.new(4, 4)
            rain.Squash = NumberSequence.new(-1.2) -- stretched along its fall: streaks
            rain.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05 * metre), NumberSequenceKeypoint.new(1, 0.03 * metre) })
            rain.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.2, 0.3), NumberSequenceKeypoint.new(1, 0.6) })
            rain.Color = ColorSequence.new(LE.RIPPLE, LE.RAIN)
            rain.LightEmission = 0.8
            rain.LightInfluence = 0
            rain.Enabled = false
            rain.Parent = cloud
            task.delay(0.1, function() -- (from 0.1 to 0.9 s: the drops are up by then)
                if rain.Parent then
                    rain.Enabled = true
                end
            end)
            task.delay(0.9, function()
                if rain.Parent then
                    rain.Enabled = false
                end
            end)

            -- a warm light from the spray
            local glowAt = fx.neon(Vector3.one * 0.05, CFrame.new(tip + Vector3.yAxis * 0.5 * metre), LE.RAIN)
            glowAt.Transparency = 1
            local light = Instance.new("PointLight")
            light.Color = LE.RAIN
            light.Range = 10 * u
            light.Brightness = 0
            light.Shadows = false
            light.Parent = glowAt
            TweenService:Create(light, TweenInfo.new(0.2), { Brightness = 1.1 }):Play()
            tweenAfter(0.8, light, TweenInfo.new(0.9), { Brightness = 0 })
        end

        local bones = table.clone(LE.BONES)
        for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
            table.insert(bones, name)
        end
        PetRig.Profiles.ThousandEyedGuardian = {
            Skinned = true,
            Bones = bones,
            Points = { "Head", "Trunk6" },
            GlowColors = {
                ffc24a = LE.SEED, -- the seeds in its lotus, glowing with Qi
                ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
            },
            Effects = {
                Blast = "RainOverDryFields",
                NovaLight = 1.5,
            },
            Colors = {
                Gold = LE.RAIN,
                Amber = LE.SEED,
                Orange = LE.RAIN_DEEP,
                Sun = LE.SEED_HOT,
                Ivory = Color3.fromRGB(236, 230, 218),
            },
            Animate = animateLotusElephant,
        }
    end
end
