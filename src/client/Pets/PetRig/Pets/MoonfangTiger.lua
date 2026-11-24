-- MoonfangTiger: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Lighting, Players, TweenService, SPARKLE, tweenAfter, pose, smoothstep, Blasts, addStance, dropToGround = K.PetRig, K.Lighting, K.Players, K.TweenService, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.addStance, K.dropToGround


    do
        -- The Moonfang Tiger (skinned): a grown Bengal tiger of the Ancient Grove, after the owner's reference photo (2026-11-12), heavy in the shoulder
        -- and low in the belly: deep orange, black stripes slanting back down its flanks and curving round its haunches, white muzzle, chin, ruffs and belly,
        -- a tiger's brow mark (three level bars crossed by an upright) in ink, amber eyes under scowling lids. Two long fangs of clear moonstone that keep the moonlight they catch: they
        -- glow, brighter in a dark realm. It stands square and watchful; it looks about, often at you, and blinks slowly; now and then it lashes its tail,
        -- scans the far distance with its ears pricked, bares its fangs with its ears laid back, or sinks into a stalk, belly low, its tail tip twitching.
        -- Still a long while, it lies down, head up, then lays its head on its paws and dozes. It walks with a heavy prowl (hind, fore, hind, fore, each
        -- paw sliding back flat on the ground), its head low and level and its tail swinging; in the air it stretches out in a leap. Its special, When the
        -- Moon Watches: it sinks into a stalk, ears flat, its fangs filling with light (to 0.42); it pounces (the burst: Blasts.WhenTheMoonWatches): a full
        -- moon opens over it and a shaft of moonlight falls on it, and where it lands two crescents of moonlight are cut into the ground, a bite; it looks
        -- up at the moon, which fades.
        local MF = {
            FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
            SOLE = 0.3017, -- metres from the middle of its box (the RootPart's cube counted) down to its paws (moonfang_tiger.py)
            LID_HINGE = { L = Vector3.new(0.7448, -0.4918, -0.451), R = Vector3.new(0.7448, 0.4918, 0.451) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(31), -- (the two add past the 41 degrees between its lids' edges)
            BLINK_LOWER = math.rad(16),
            -- its prowl: each leg's turns (upper, middle, lower) at sixteen steps through the cycle, found in Blender by a solver that keeps each paw
            -- flat on the ground as it slides back and lifts it 5 cm as it swings forward (moonfang_tiger.py find_walk: planted within 0.4 mm, no torn
            -- skin anywhere in the cycle); its paw turned back level. Hind, fore, hind, fore, a quarter of a cycle apart, as a big cat walks.
            WALK_FRONT = { { 0.371, -0.264, -0.073 }, { 0.28, -0.18, -0.054 }, { 0.199, -0.114, -0.037 }, { 0.125, -0.063, -0.022 }, { 0.059, -0.025, -0.01 }, { -0.002, 0.001, 0.001 }, { -0.057, 0.017, 0.007 }, { -0.107, 0.023, 0.01 }, { -0.151, 0.02, 0.011 }, { -0.188, 0.007, 0.008 }, { -0.236, 0.015, 0.013 }, { -0.393, 0.312, 0.125 }, { -0.412, 0.488, 0.191 }, { -0.301, 0.523, 0.193 }, { -0.105, 0.404, 0.137 }, { 0.123, 0.145, 0.04 } },
            WALK_HIND = { { 0.198, 0.024, 0.065 }, { 0.163, 0.009, 0.057 }, { 0.127, -0.002, 0.045 }, { 0.086, -0.006, 0.032 }, { 0.044, -0.006, 0.017 }, { 0, -0.001, -0.006 }, { -0.05, 0.012, -0.02 }, { -0.1, 0.028, -0.041 }, { -0.153, 0.05, -0.064 }, { -0.207, 0.078, -0.088 }, { -0.254, 0.094, -0.107 }, { -0.146, -0.081, -0.032 }, { 0.004, -0.231, 0.048 }, { 0.154, -0.3, 0.117 }, { 0.249, -0.263, 0.152 }, { 0.261, -0.138, 0.132 } },
            WALK_LEAD = { BL = 0, FL = 0.25, BR = 0.5, FR = 0.75 },
            WALK_RATE = 1.4, -- cycles a second at a full walk
            -- its stances (game axes; turns x, y, z), each checked in Blender against the ground and for torn skin (moonfang_tiger.py)
            CROUCH = { Head = { 0.12, 0, 0 }, Shoulders = { -0.04, 0, 0 }, LegBL1 = { 0.283, 0, 0 }, LegBL2 = { -0.576, 0, 0 }, LegBL3 = { 0.21, 0, 0 },
                LegBR1 = { 0.283, 0, 0 }, LegBR2 = { -0.576, 0, 0 }, LegBR3 = { 0.21, 0, 0 }, LegFL1 = { -0.416, 0, 0 }, LegFL2 = { 0.796, 0, 0 },
                LegFL3 = { 0.303, 0, 0 }, LegFR1 = { -0.416, 0, 0 }, LegFR2 = { 0.796, 0, 0 }, LegFR3 = { 0.303, 0, 0 }, PawBL = { 0.083, 0, 0 },
                PawBR = { 0.083, 0, 0 }, PawFL = { -0.683, 0, 0 }, PawFR = { -0.683, 0, 0 } },
            CROUCH_DROP = 0.085, -- metres its hips come down in its stalk
            LIE = { Head = { 0.1, 0, 0 }, Hips = { -0.05, 0, 0 }, Shoulders = { 0.08, 0, 0 }, LegBL1 = { 0.632, 0, 0 }, LegBL2 = { -0.655, 0, 0 },
                LegBL3 = { 0.411, 0, 0 }, LegBR1 = { 0.632, 0, 0 }, LegBR2 = { -0.655, 0, 0 }, LegBR3 = { 0.411, 0, 0 }, LegFL1 = { -0.058, 0, 0 },
                LegFL2 = { 0.762, 0, 0 }, LegFL3 = { 0.253, 0, 0 }, LegFR1 = { -0.058, 0, 0 }, LegFR2 = { 0.762, 0, 0 }, LegFR3 = { 0.253, 0, 0 },
                PawBL = { -0.388, 0, 0 }, PawBR = { -0.388, 0, 0 }, PawFL = { -0.957, 0, 0 }, PawFR = { -0.957, 0, 0 }, Tail1 = { -0.25, 0.35, 0 },
                Tail2 = { 0.05, 0.35, 0 }, Tail3 = { 0.05, 0.3, 0 } },
            LIE_DROP = 0.105,
            STALK_HEAD = { Neck = { -0.12, 0, 0 }, Head = { 0.18, 0, 0 } }, -- over CROUCH: head low and level, eyes on its prey
            EARS_BACK = { EarL = { -0.4, 0.3, 0 }, EarR = { -0.4, -0.3, 0 } },
            DOZE_HEAD = { Neck = { -0.14, 0, 0 }, Head = { -0.2, 0.15, 0.06 } }, -- over LIE: its head sunk on its paws
            GLARE = { Shoulders = { 0.06, 0, 0 }, Neck = { 0.28, 0, 0 }, Head = { 0.32, 0, 0 } }, -- up at the moon (EARS_BACK with it)
            SNARL = { Neck = { 0.2, 0, 0 }, Head = { 0.35, 0, 0 } },
            LUNGE = 0.22, -- metres its pounce carries it forward
            HOP = 0.07, -- and how high, every paw off the ground
            FIDGET_TIME = { lash = 1.6, scan = 3, snarl = 1.6, stalk = 3.2 },
            FANG = Color3.fromRGB(60, 150, 255), -- its fangs' Neon, keeping moonlight (deeper than its 8fd0ff paint: Neon pales to white)
            FANG_FULL = Color3.fromRGB(150, 215, 255),
            MOON = Color3.fromRGB(110, 175, 255), -- the moon's Neon (at 170, 210, 255 it bloomed pure white and read as a sun, seen in Play)
            MARIA = Color3.fromRGB(55, 105, 210), -- its seas
            MOON_DEEP = Color3.fromRGB(70, 120, 230),
            MOON_HOT = Color3.fromRGB(215, 235, 255),
            BONES = { "Hips", "Body", "Chest", "Shoulders", "Neck", "Head", "EyeL", "EyeR", "EarL", "EarR" },
        }
        for k = 1, 7 do
            table.insert(MF.BONES, "Tail" .. k)
        end
        for _, key in { "FL", "FR", "BL", "BR" } do
            for k = 1, 3 do
                table.insert(MF.BONES, "Leg" .. key .. k)
            end
            table.insert(MF.BONES, "Paw" .. key)
        end

        -- both forelegs f = { upper, fore, wrist } and both hind legs b, the same each side, each paw turned back level (moonfang_tiger.py legs4)
        function MF.legs4(into, f, b)
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
        MF.POUNCE = MF.legs4({ Hips = { -0.1, 0, 0 }, Shoulders = { -0.12, 0, 0 }, Head = { 0.1, 0, 0 } }, { 0.6, -0.2, -0.25 }, { -0.45, 0.32, -0.08 })
        MF.LEAP = MF.legs4({ Body = { 0.05, 0, 0 }, Head = { -0.05, 0, 0 } }, { 0.75, -0.35, -0.2 }, { -0.75, 0.25, 0.05 })
        for k = 1, 7 do
            MF.POUNCE["Tail" .. k] = { -0.06, 0, 0 }
            MF.LEAP["Tail" .. k] = { -0.05, 0, 0 }
        end

        function MF.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        -- a leg's turns at g through its cycle (0..1), between the solved steps
        function MF.walkAt(rows, g)
            local n = #rows
            local x = (g % 1) * n
            local i = math.floor(x)
            local w = x - i
            local a, b = rows[i % n + 1], rows[(i + 1) % n + 1]
            return { a[1] + (b[1] - a[1]) * w, a[2] + (b[2] - a[2]) * w, a[3] + (b[3] - a[3]) * w }
        end

        local function animateMoonfangTiger(rig, s, moving, fly, nova)
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            -- its fangs keep the moonlight: they glow, brighter in a dark realm and as it gathers itself for its special
            local clock = Lighting.ClockTime
            local night = if clock < 6.2 or clock > 17.8 then 1 else 0
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local special = progress > 0
            local fill = smoothstep(0.05, 0.4, progress) * (1 - smoothstep(0.75, 1, progress))
            local fangs = rig.parts.Fangs
            if fangs then
                local glow = math.clamp(0.25 + 0.35 * night + 0.08 * math.sin(t * 1.3) + fill, 0, 1)
                fangs.Color = MF.FANG:Lerp(MF.FANG_FULL, glow)
                fangs.Transparency = 0.15 * (1 - glow)
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > MF.FAR then
                return
            end
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, MF.SOLE)

            -- the special: it sinks into a stalk, ears flat, fangs filling (to 0.42); it pounces, forward and up off the ground (the burst); it looks up at
            -- the moon; it settles
            local stalk = smoothstep(0.02, 0.2, progress) * (1 - smoothstep(0.37, 0.42, progress))
            local pounce = smoothstep(0.37, 0.43, progress) * (1 - smoothstep(0.56, 0.68, progress))
            local hop = math.sin(math.pi * math.clamp((progress - 0.39) / 0.14, 0, 1))
            local lunge = smoothstep(0.38, 0.46, progress) * (1 - smoothstep(0.58, 0.85, progress))
            local glare = smoothstep(0.6, 0.7, progress) * (1 - smoothstep(0.88, 0.97, progress))

            -- still a long while, it lies down, head up; longer, it lays its head on its paws and dozes. Now and then it lashes its tail, scans the
            -- distance, bares its fangs, or sinks into a stalk
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            local wantLie = if s.still > 14 then 1 else 0
            s.lie = (s.lie or 0) + (wantLie - (s.lie or 0)) * math.min(1, dt * (if wantLie > (s.lie or 0) then 0.9 else 5))
            local lie = smoothstep(0, 1, s.lie)
            local wantDoze = if s.still > 26 then 1 else 0
            s.doze = (s.doze or 0) + (wantDoze - (s.doze or 0)) * math.min(1, dt * (if wantDoze > (s.doze or 0) then 0.5 else 5))
            local doze = smoothstep(0, 1, s.doze) * lie
            s.nextFidget = s.nextFidget or t + 4
            if t >= s.nextFidget then
                local r = math.random()
                s.fidgetAt = t
                s.fidgetKind = if r < 0.3 then "lash" elseif r < 0.58 then "scan" elseif r < 0.8 then "snarl" else "stalk"
                s.scanSide = if math.random() < 0.5 then 1 else -1
                s.nextFidget = t + MF.FIDGET_TIME[s.fidgetKind] + 4 + math.random() * 5
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / MF.FIDGET_TIME[s.fidgetKind], 0, 1) else 1
            local calmness = (1 - pace) * (1 - lie) * (if special then 0 else 1)
            local fidget = smoothstep(0, 0.18, env) * (1 - smoothstep(0.8, 1, env)) * calmness
            local function kind(name)
                return if s.fidgetKind == name then fidget else 0
            end

            local want = {}
            local crouch = math.max(stalk, kind("stalk"))
            addStance(want, MF.CROUCH, crouch * (1 - pounce))
            addStance(want, MF.STALK_HEAD, crouch * (1 - pounce))
            addStance(want, MF.EARS_BACK, math.max(stalk, pounce, glare, kind("snarl")))
            addStance(want, MF.POUNCE, pounce)
            addStance(want, MF.GLARE, glare)
            addStance(want, MF.SNARL, kind("snarl"))
            addStance(want, MF.LIE, lie * (1 - crouch))
            addStance(want, MF.DOZE_HEAD, doze)
            local scan = kind("scan")
            addStance(want, { Neck = { 0.04, 0.3 * (s.scanSide or 1), 0 }, Head = { 0.08, 0.45 * (s.scanSide or 1), 0.05 * (s.scanSide or 1) },
                EarL = { 0.15, 0, 0 }, EarR = { 0.15, 0, 0 } }, scan)

            -- its prowl: hind, fore, hind, fore; its shoulders rolling, its head low and level; in the air it stretches out in a leap
            local onFoot = moving * (1 - fly)
            s.stride = (s.stride or 0) + dt * MF.WALK_RATE * onFoot
            for key, lead in MF.WALK_LEAD do
                local rows = if string.sub(key, 1, 1) == "F" then MF.WALK_FRONT else MF.WALK_HIND
                local a = MF.walkAt(rows, s.stride + lead)
                addStance(want, {
                    ["Leg" .. key .. "1"] = { a[1], 0, 0 },
                    ["Leg" .. key .. "2"] = { a[2], 0, 0 },
                    ["Leg" .. key .. "3"] = { a[3], 0, 0 },
                    ["Paw" .. key] = { -(a[1] + a[2] + a[3]), 0, 0 },
                }, onFoot)
            end
            local roll = math.sin(2 * math.pi * s.stride)
            addStance(want, { Shoulders = { 0, 0.05 * roll, 0.03 * roll }, Hips = { 0, -0.04 * roll, -0.02 * roll }, Neck = { -0.08, -0.03 * roll, 0 },
                Head = { 0.06, 0, 0 } }, onFoot)
            addStance(want, MF.LEAP, fly)

            -- breathing; its head looking about, often at you (not while it stalks, pounces or glares)
            local breath = math.sin(t * (if lie > 0.5 then 1.1 else 1.4))
            addStance(want, { Chest = { 0.012 * breath, 0, 0 }, Body = { 0.008 * breath, 0, 0 } }, 1)
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2.5 + math.random() * 3.5
                s.atYou = math.random() < 0.5
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.2
            end
            local calm = (1 - 0.6 * pace) * (1 - math.max(crouch, pounce, glare, scan)) * (1 - 0.9 * doze)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.7, 0.7) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.15, 0.3) else s.gazePitch) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.5) -- (slower than a kit's: a big cat's head turns deliberately)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.5)
            addStance(want, {
                Neck = { 0.12 * s.pitch, 0.32 * s.yaw, 0 }, Head = { 0.25 * s.pitch, 0.4 * s.yaw, 0.08 * s.yaw },
                EyeL = { 0.2 * s.pitch, 0.25 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.25 * s.yaw, 0 },
            }, 1)
            -- its ears: now and then one turns back to a sound behind it
            s.nextEar = s.nextEar or t + 3
            if t >= s.nextEar then
                s.nextEar = t + 3 + math.random() * 5
                s.earAt, s.earSide = t, if math.random() < 0.5 then 1 else -1
            end
            local ear = if s.earAt then math.sin(math.pi * math.clamp((t - s.earAt) / 0.9, 0, 1)) * calm else 0
            addStance(want, { [if (s.earSide or 1) > 0 then "EarL" else "EarR"] = { -0.25, 0.35 * (s.earSide or 1), 0 } }, ear)

            -- its tail: low, swaying slowly, a wave running down it to its black tip, which never quite stops; lashing hard; swinging with its prowl;
            -- in a stalk only the tip twitching; lying, curled round to one side
            local tailCalm = 1 - math.max(crouch, pounce)
            local lash = kind("lash")
            for k = 1, 7 do
                local wave = math.sin(t * 0.9 - k * 0.45)
                local tip = smoothstep(4, 7, k)
                addStance(want, { ["Tail" .. k] = { 0.02 * math.sin(t * 0.6 - k * 0.3), 0.05 * wave + 0.06 * tip * math.sin(t * 2.3 - k), 0 } },
                    tailCalm * (1 - 0.6 * doze))
                addStance(want, { ["Tail" .. k] = { 0.03, 0.18 * math.sin(t * 9 - k * 0.6), 0 } }, lash)
                addStance(want, { ["Tail" .. k] = { 0, 0.07 * math.sin(2 * math.pi * s.stride - k * 0.5), 0 } }, onFoot)
                addStance(want, { ["Tail" .. k] = { 0, 0.22 * tip * math.sin(t * 11 - k), 0 } }, crouch)
            end

            local lift = -MF.CROUCH_DROP * crouch * (1 - pounce) * u - MF.LIE_DROP * lie * (1 - crouch) * u + MF.HOP * hop * u - drop
            local forward = MF.LUNGE * lunge * u
            for _, name in MF.BONES do
                local a = want[name] or Vector3.zero
                pose(m[name], CFrame.new(0, if name == "Hips" then lift else 0, if name == "Hips" then -forward else 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- its eyes: slow blinks; narrowed as it stalks, bares its fangs or glares; shut as it dozes
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.32
                if a >= 1 then
                    s.nextBlink = t + 3 + math.random() * 5
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local narrow = 0.3 * math.max(crouch, glare, kind("snarl"))
            local close = math.max(blink, doze, narrow) * (1 - 0.6 * pounce)
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(MF.LID_HINGE[side], -MF.BLINK_UPPER * close))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(MF.LID_HINGE[side], MF.BLINK_LOWER * close))
            end
        end

        -- It pounces (animateMoonfangTiger): over it a full moon opens, a shaft of its light falling on the tiger; where it lands two crescents of
        -- moonlight are cut into the ground, a bite, flaring and fading as moon-dust lifts off them; the moon watches a moment and fades (by 1.9 s).
        function Blasts.WhenTheMoonWatches(rig, fx)
            local u, metre = rig.unit, rig.meters
            local reduced = MF.reduced()
            local params = RaycastParams.new()
            params.FilterDescendantsInstances = { rig.model }
            local root = rig.rootPart.CFrame
            local flat = Vector3.new(root.LookVector.X, 0, root.LookVector.Z)
            flat = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.zAxis
            local right = flat:Cross(Vector3.yAxis)
            local function groundAt(at)
                local hit = workspace:Raycast(at + Vector3.new(0, 0.6 * metre, 0), Vector3.new(0, -10 * u, 0), params)
                return if hit then hit.Position else Vector3.new(at.X, rig.rootPart.Position.Y - MF.SOLE * metre, at.Z)
            end
            local feet = groundAt(root.Position)

            -- the moon: a full moon over it and a little ahead, blooming open; a soft halo round it
            local moonAt = feet + Vector3.yAxis * 2.4 * metre + flat * 0.3 * metre
            local R = 0.32 * metre
            local moon = fx.neon(Vector3.one * 0.05, CFrame.new(moonAt), MF.MOON)
            moon.Shape = Enum.PartType.Ball
            moon.Transparency = 0.05
            TweenService:Create(moon, TweenInfo.new(0.22, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = Vector3.one * 2 * R }):Play()
            -- its seas, on the face toward whoever is watching
            local camera = workspace.CurrentCamera
            local toEye = if camera then (camera.CFrame.Position - moonAt) else -flat
            toEye = if toEye.Magnitude > 1e-3 then toEye.Unit else -flat
            local across = toEye:Cross(Vector3.yAxis)
            across = if across.Magnitude > 1e-3 then across.Unit else right
            local up = across:Cross(toEye)
            for _, sea in { { -0.3, 0.25, 0.32 }, { 0.28, 0.1, 0.24 }, { 0.05, -0.38, 0.2 }, { -0.4, -0.2, 0.14 } } do
                local at = moonAt + (across * sea[1] + up * sea[2]) * R
                at += toEye * math.sqrt(math.max(0, 1 - sea[1] ^ 2 - sea[2] ^ 2)) * R * 1.01
                local disc = fx.neon(Vector3.new(0.01 * metre, 0.05, 0.05), CFrame.lookAt(at, at + toEye) * CFrame.Angles(0, math.pi / 2, 0), MF.MARIA)
                disc.Shape = Enum.PartType.Cylinder
                disc.Transparency = 0.45 -- (at 0.25 they read as polka dots, seen in Play)
                TweenService:Create(disc, TweenInfo.new(0.22, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = Vector3.new(0.01 * metre, 2 * sea[3] * R, 2 * sea[3] * R) }):Play()
                tweenAfter(1.25, disc, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
            end
            local halo = fx.neon(Vector3.one * 0.05, CFrame.new(moonAt), MF.MOON_DEEP)
            halo.Shape = Enum.PartType.Ball
            halo.Transparency = 0.82
            TweenService:Create(halo, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 3.6 * R }):Play()
            tweenAfter(1.25, moon, TweenInfo.new(0.55, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1, Size = Vector3.one * 1.6 * R })
            tweenAfter(1.15, halo, TweenInfo.new(0.55), { Transparency = 1 })
            local moonLight = Instance.new("PointLight")
            moonLight.Color = MF.MOON
            moonLight.Range = 16 * u
            moonLight.Brightness = 0
            moonLight.Shadows = false
            moonLight.Parent = moon
            TweenService:Create(moonLight, TweenInfo.new(0.2), { Brightness = 1.2 }):Play() -- (a cold wash over it: brighter, its orange coat goes grey)
            tweenAfter(1.2, moonLight, TweenInfo.new(0.6), { Brightness = 0 })

            -- its light falling on the tiger: a shaft from the moon to the ground under it, widening and fading
            local shaftTop, shaftFoot = moonAt - Vector3.yAxis * R * 0.6, feet
            local length = (shaftTop - shaftFoot).Magnitude
            -- (0.7 m wide it swallowed its owner and the whole platform in blue, seen in Play)
            local shaft = fx.neon(Vector3.new(length, 0.12 * metre, 0.12 * metre), CFrame.new((shaftTop + shaftFoot) / 2) * CFrame.Angles(0, 0, math.pi / 2), MF.MOON_DEEP)
            shaft.Shape = Enum.PartType.Cylinder
            shaft.Transparency = 0.9
            TweenService:Create(shaft, TweenInfo.new(0.18), { Transparency = 0.78, Size = Vector3.new(length, 0.3 * metre, 0.3 * metre) }):Play()
            tweenAfter(0.3, shaft, TweenInfo.new(0.8, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1, Size = Vector3.new(length, 0.42 * metre, 0.42 * metre) })

            -- the bite: two crescents of moonlight raked into the ground where it lands, side by side and curving the same way, like the marks of its two
            -- fangs, each drawn in one sweep from tip to tip, thick in the middle, fine at the ends; flaring, then fading as moon-dust lifts off them.
            -- (Facing each other, bowed apart, the two closed into a broken ring, seen from above in Play.)
            local strike = groundAt(root.Position + flat * (MF.LUNGE + 0.55) * metre)
            local segs = if reduced then 8 else 14
            local crescents = {}
            for _, side in { -1, 1 } do
                local centre = strike + right * side * 0.09 * metre
                local radius = 0.3 * metre
                local last
                for k = 0, segs do
                    local a = math.rad(-65 + 130 * k / segs)
                    -- each runs forward along the way it pounced, bowing to its right
                    local at = centre + right * (math.cos(a) - 0.8) * radius + flat * math.sin(a) * radius + Vector3.yAxis * 0.02 * metre
                    if last then
                        local width = (0.025 + 0.06 * math.cos(math.rad(-65 + 130 * (k - 0.5) / segs))) * metre
                        local seg = fx.neon(Vector3.new(width, 0.02 * metre, (at - last).Magnitude + width * 0.5), CFrame.lookAt((last + at) / 2, at), MF.MOON_HOT)
                        seg.Transparency = 1
                        tweenAfter(0.03 + 0.12 * k / segs, seg, TweenInfo.new(0.05), { Transparency = 0 })
                        tweenAfter(0.3, seg, TweenInfo.new(0.25), { Color = MF.FANG_FULL })
                        tweenAfter(0.75 + 0.3 * k / segs, seg, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
                        table.insert(crescents, seg)
                    end
                    last = at
                end
            end
            -- a ring of moonlight running out over the ground from the bite
            local ring = fx.neon(Vector3.new(0.03 * metre, 0.3 * metre, 0.3 * metre), CFrame.new(strike + Vector3.yAxis * 0.015 * metre) * CFrame.Angles(0, 0, math.pi / 2), MF.MOON)
            ring.Shape = Enum.PartType.Cylinder
            ring.Transparency = 0.55
            TweenService:Create(ring, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.01 * metre, 2.6 * metre, 2.6 * metre), Transparency = 1 }):Play()
            -- moon-dust off the bite
            local dustHolder = fx.neon(Vector3.one * 0.05, CFrame.lookAt(strike, strike + Vector3.yAxis), MF.MOON)
            dustHolder.Transparency = 1
            local dust = Instance.new("ParticleEmitter")
            dust.Texture = SPARKLE
            dust.Enabled = false
            dust.Lifetime = NumberRange.new(0.6, 1.1)
            dust.Speed = NumberRange.new(0.6 * u, 1.6 * u)
            dust.SpreadAngle = Vector2.new(50, 50)
            dust.Acceleration = Vector3.new(0, 0.8 * u, 0)
            dust.Drag = 2
            dust.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12 * u), NumberSequenceKeypoint.new(1, 0) })
            dust.Color = ColorSequence.new(MF.MOON_HOT, MF.MOON_DEEP)
            dust.LightEmission = 1
            dust.LightInfluence = 0
            dust.Parent = dustHolder
            dust:Emit(if reduced then 10 else 24)
            task.delay(0.5, function()
                if dust.Parent then
                    dust:Emit(if reduced then 6 else 14)
                end
            end)
        end

        local bones = table.clone(MF.BONES)
        for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
            table.insert(bones, name)
        end
        PetRig.Profiles.MoonfangTiger = {
            Skinned = true,
            Bones = bones,
            Points = { "Head" },
            GlowColors = {
                ["8fd0ff"] = MF.FANG, -- its fangs, keeping the moonlight
                ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
            },
            Effects = {
                Blast = "WhenTheMoonWatches",
                NovaLight = 1.5,
            },
            Colors = {
                Gold = MF.MOON_HOT,
                Amber = MF.MOON,
                Orange = MF.MOON_DEEP,
                Sun = MF.FANG_FULL,
                Ivory = Color3.fromRGB(248, 242, 230),
            },
            Animate = animateMoonfangTiger,
        }
    end
end
