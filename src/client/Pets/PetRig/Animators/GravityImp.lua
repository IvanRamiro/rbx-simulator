-- The GravityImp pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep, dropToGround = K.PetRig, K.pose, K.smoothstep, K.dropToGround

    local animateGravityImp, IMP -- animateGravityImp's section below (its own locals stay in its block)
    do

        -- The Gravity Imp (skinned): a small, smug violet imp who lives on a moonlet of its own, and whichever way its feet are on it is down. It stands on top
        -- with its fists on its hips, watching you, one brow up; now and then it chuckles to itself, an ear flicks, its spade of a tail sways. Now and then it
        -- strolls forward over the front and down under its moonlet (the moonlet rising so it hangs clear of the ground), turns round to face you and hangs there
        -- upside down, smirking, then carries on over the back to the top. When its owner goes anywhere it treads its moonlet round under it like a treadmill;
        -- when they fly it sits on top, leaning back on its hands. Three pebbles circle the moonlet round its own middle.
        IMP = {
            FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
            CORE_SOLE = 0.1497, -- metres from its Core bone (the moonlet's middle) down to its lowest point, standing on top (gravity_imp.py)
            -- metres from the Core down to its lowest point as it stands further round its moonlet, every 15 degrees from the top to underneath (measured in Blender)
            UNDER = { 0.1497, 0.1497, 0.1582, 0.2136, 0.256, 0.2838, 0.2923, 0.2831, 0.2942, 0.3832, 0.4584, 0.5044, 0.5168 },
            HOVER = 0.2, -- metres its moonlet hangs above the ground; a little lower as it treads along
            WALK_HOVER = 0.12,
            RADIUS = 0.15, -- the moonlet's, in metres
            STROLL = 1.1, -- radians a second it walks round its moonlet
            LID_HINGE = { L = Vector3.new(0.9395, -0.1562, -0.3049), R = Vector3.new(0.9395, 0.1562, 0.3049) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(40),
            BLINK_LOWER = math.rad(10),
            VIOLET = Color3.fromRGB(210, 140, 255),
            DEEP = Color3.fromRGB(110, 60, 190),
            STONE = Color3.fromRGB(112, 102, 90), -- the ground's own stones, earth-grey (a violet-grey read as lilac cubes under its light: seen in Play)
            DUST = Color3.fromRGB(176, 164, 140),
            -- its walk on top, as on a treadmill (searched in Blender: planted soles within 1.4 mm of resting on the moonlet): legs swing at the hips, a knee lifts
            -- a foot, a planted foot turns twice its leg's swing to lie along the moonlet's curve, the hips dip 4 mm as both feet are down
            SWING = 0.36,
            LIFT = 0.75,
            TILT = 2.0,
            DIP = 0.004,
            -- stances, each checked in Blender (gravity_imp.py's POSES) and along the slerp from one to another: turns x, y, z; then a move in metres, the game's axes
            AKIMBO = { -- fists on its hips, elbows out
                ArmL1 = { -0.0938, 0.0388, -0.4486 }, ArmL2 = { 0.0559, -0.1789, 1.2647 }, HandL = { -0.3102, 0.376, -0.8454 },
                ArmR1 = { -0.0938, -0.0388, 0.4486 }, ArmR2 = { 0.0559, 0.1789, -1.2647 }, HandR = { -0.3102, -0.376, 0.8454 },
            },
            SIT = { -- sat on top, legs out round its belly, leaning back on its hands: how it rides when its owner flies
                Hips = { 0.22, 0, 0, 0, -0.07, 0.01 },
                ArmL1 = { -0.4136, 0.1613, 0.1756 }, ArmL2 = { 0.0204, -0.0115, 0.0343 }, HandL = { 0.8306, 1.2185, -1.6622 },
                ArmR1 = { -0.4136, -0.1613, -0.1756 }, ArmR2 = { 0.0204, 0.0115, -0.0343 }, HandR = { 0.8306, -1.2185, 1.6622 },
                LegL1 = { 1.35, 0, -0.35 }, LegL2 = { -0.1, 0, 0 }, FootL = { -1.7, 0, 0 },
                LegR1 = { 1.35, 0, 0.35 }, LegR2 = { -0.1, 0, 0 }, FootR = { -1.7, 0, 0 },
            },
            STOMP = { -- its special: a sumo's stamp, its right leg out to its side (a knee forward would meet its belly), its weight on its left
                Hips = { 0, 0, -0.06, 0, -0.002, 0 },
                LegR1 = { 0.1, 0, 1.25 }, LegR2 = { 0, 0, -1.25 }, FootR = { 0, 0, 0.16 }, LegL1 = { 0, 0, 0.06 }, FootL = { 0, 0, -0.06 },
            },
            BALANCE = { -- its arms out for balance as it stamps, elbows bent up
                ArmL1 = { 0, 0, -0.85 }, ArmL2 = { 0, 0, -0.55 }, HandL = { 0, 0, -0.25 },
                ArmR1 = { 0, 0, 0.85 }, ArmR2 = { 0, 0, 0.55 }, HandR = { 0, 0, 0.25 },
            },
            LEGS = { LegL1 = true, LegL2 = true, FootL = true, LegR1 = true, LegR2 = true, FootR = true },
            -- the pebbles' orbits round the imp's own middle (each tilted about the line to where it rests, so it rests on it), and how fast each goes round
            ORBITS = {
                { Vector3.new(-0.1388, 0.9703, -0.1982), 0.9 },
                { Vector3.new(0.117, 0.9397, -0.3214), -0.7 },
                { Vector3.new(0.1511, 0.9877, 0.0405), 1.25 },
            },
            BONES = {
                "Hips", "Chest", "Head", "EarL", "EarR", "BrowL", "BrowR",
                "ArmL1", "ArmL2", "HandL", "ArmR1", "ArmR2", "HandR", "LegL1", "LegL2", "FootL", "LegR1", "LegR2", "FootR",
                "Tail1", "Tail2", "Tail3", "Tail4",
            },
        }

        -- a stance's turn (and move) as a CFrame
        function IMP.cf(a, u)
            local move = if a[4] then CFrame.new(a[4] * u, a[5] * u, a[6] * u) else CFrame.identity
            return move * CFrame.Angles(a[1], a[2], a[3])
        end

        -- how far below its moonlet's middle it reaches, standing this far round it (0 on top, pi underneath)
        function IMP.under(a)
            local f = a % (2 * math.pi)
            if f > math.pi then
                f = 2 * math.pi - f
            end
            local k = f / (math.pi / 12)
            local i = math.min(math.floor(k), #IMP.UNDER - 2)
            return IMP.UNDER[i + 1] + (IMP.UNDER[i + 2] - IMP.UNDER[i + 1]) * (k - i)
        end

        function animateGravityImp(rig, s, moving, fly, nova)
            if not s.lightMade then
                -- its glow follows its moonlet: hung on the Core bone (a skinned part stays where it was bound, so a light on the veins stayed behind when it rose)
                s.lightMade = true
                local core = rig.points.Core
                if core then
                    local light = Instance.new("PointLight")
                    light.Name = "PulseLight"
                    light.Color = IMP.VIOLET
                    light.Range = 5 * rig.unit
                    light.Brightness = 1.2
                    light.Shadows = false
                    light.Parent = core
                    rig.light = light
                end
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > IMP.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime

            -- the special, Which Way Is Down: it stands (if it sat), lifts its right foot out to its side, arms out, and stamps on its moonlet at 0.42
            -- (Blasts.WhichWayIsDown); the moonlet jolts, its ears flap, the pebbles whirl; then fists back on its hips
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local active = if rig.nova then 1 else 0
            s.sit = (s.sit or 0) + (fly * (1 - active) - (s.sit or 0)) * math.min(1, dt * 3)
            local standing = 1 - smoothstep(0, 0.35, s.sit) -- (it stands before it stamps: the seat to the stamp was never checked)
            local up = smoothstep(0.06, 0.3, progress) * (1 - smoothstep(0.405, 0.425, progress)) * standing
            local balance = smoothstep(0.04, 0.2, progress) * (1 - smoothstep(0.46, 0.62, progress)) * standing
            local impact = if progress > 0.42 then math.exp(-(progress - 0.42) * 12) else 0
            local whirl = smoothstep(0.42, 0.5, progress) * (1 - smoothstep(0.7, 0.95, progress))

            -- how fast it is going, in metres a second (its root follows its owner)
            local here = rig.rootPart.Position
            local travel = if s.lastPos and dt > 0 then Vector3.new(here.X - s.lastPos.X, 0, here.Z - s.lastPos.Z).Magnitude / dt / u else 0
            s.lastPos = here
            s.speed = (s.speed or 0) + (math.min(travel, 4) - (s.speed or 0)) * math.min(1, dt * 4)

            -- strolling round its moonlet: over the front and down, turn to face you, hang a while, turn back, on over the back to the top. Anything else
            -- happening (its owner moving or flying, the special) and it hurries home to the top the short way
            s.mode = s.mode or "top"
            s.a = s.a or 0
            s.turn = s.turn or 0
            s.nextStroll = s.nextStroll or t + 10 + math.random() * 8
            local idle = moving < 0.1 and fly < 0.1 and active == 0
            local strolling = 0
            if s.mode == "top" then
                if idle and t >= s.nextStroll then
                    s.mode = "down"
                end
            elseif not idle then
                s.mode = "home"
            end
            if s.mode == "down" then
                s.a = math.min(math.pi, s.a + dt * IMP.STROLL)
                strolling = 1
                if s.a >= math.pi then
                    s.mode = "turn"
                end
            elseif s.mode == "turn" then
                s.turn = math.min(math.pi, s.turn + dt * 4.5)
                if s.turn >= math.pi then
                    s.mode = "hang"
                    s.hangUntil = t + 5 + math.random() * 4
                end
            elseif s.mode == "hang" then
                if t >= (s.hangUntil or 0) then
                    s.mode = "unturn"
                end
            elseif s.mode == "unturn" then
                s.turn = math.max(0, s.turn - dt * 4.5)
                if s.turn <= 0 then
                    s.mode = "up"
                end
            elseif s.mode == "up" then
                s.a = math.min(2 * math.pi, s.a + dt * IMP.STROLL)
                strolling = 1
                if s.a >= 2 * math.pi then
                    s.a = 0
                    s.mode = "top"
                    s.nextStroll = t + 18 + math.random() * 14 -- (a lap takes 12 to 16 s: at 12 to 22 s between, it was off the top nearly half the time)
                end
            elseif s.mode == "home" then
                s.turn = math.max(0, s.turn - dt * 6)
                local home = if s.a > math.pi then 2 * math.pi else 0
                local stride = dt * 3
                if math.abs(home - s.a) <= stride then
                    s.a = 0
                    s.mode = "top"
                    s.nextStroll = t + 10 + math.random() * 8
                else
                    s.a += if home > s.a then stride else -stride
                    strolling = 1
                end
            end
            local walking = moving * (1 - fly)
            local lean = 0.16 * walking * (1 - strolling) -- treading along, it stands a little forward of the top, as on a ball
            local onTop = 1 - smoothstep(0.2, 0.9, math.min(s.a, 2 * math.pi - s.a)) -- (the special caught it underneath: it stamps once it is back on top)
            up *= onTop
            balance *= onTop
            local pivot = CFrame.Angles(-(s.a + lean), 0, 0) * CFrame.Angles(0, s.turn, 0)
            pose(m.Pivot, pivot)

            -- its moonlet: hanging above the ground (higher as it goes round, so it hangs clear underneath), bobbing; turning under its feet as it treads
            -- along; a jolt when it stamps; tilting into its owner's turns
            local core = rig.points.Core
            if core and not s.sole then
                s.sole = rig.rootPart.CFrame:PointToObjectSpace(core.WorldPosition).Y * -1 / u + IMP.CORE_SOLE -- (WorldPosition leaves out its own Transform)
            end
            local drop = dropToGround(rig, s, t, u, fly, s.sole or 0.2)
            local hover = (IMP.HOVER * (1 - walking) + IMP.WALK_HOVER * walking) * (1 - fly)
            local bob = 0.012 * math.sin(t * 1.4) + 0.004 * math.sin(t * 3.1 + 1)
            local jolt = -0.03 * impact * math.cos(math.max(0, progress - 0.42) * 45)
            local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.25, 0.25) - (s.bank or 0)) * math.min(1, dt * 3)
            local lift = (hover + IMP.under(s.a) - IMP.UNDER[1] + bob + jolt) * u - drop
            pose(m.Core, CFrame.new(0, lift, 0) * CFrame.Angles(0, 0, s.bank))
            s.spin = (s.spin or 0) + dt * (math.min(s.speed / IMP.RADIUS, 9) * walking * (1 - strolling) + 0.25 * fly)
            pose(m.Planet, CFrame.Angles(s.spin, 0, 0))

            -- its legs: stepping as it treads along or strolls round
            local stepping = math.max(walking * (1 - strolling), strolling) * (1 - s.sit) * (1 - up)
            s.step = (s.step or 0) + dt * math.min(5 + 9 * math.max(s.speed, strolling * 0.6), 14) * stepping
            local cfs = {}
            for _, name in IMP.BONES do
                cfs[name] = CFrame.identity
            end
            for tag, lead in { L = 0, R = math.pi } do
                local sw = math.sin(s.step + lead) * stepping
                local lf = math.max(0, math.cos(s.step + lead)) * stepping
                cfs["Leg" .. tag .. "1"] = CFrame.Angles(IMP.SWING * sw, 0, 0)
                cfs["Leg" .. tag .. "2"] = CFrame.Angles(-IMP.LIFT * lf, 0, 0)
                cfs["Foot" .. tag] = CFrame.Angles(-IMP.TILT * IMP.SWING * sw + IMP.LIFT * lf * 0.6, 0, 0)
                cfs["Arm" .. tag .. "1"] = CFrame.Angles(-0.3 * sw, 0, 0)
            end

            -- where it looks: at you, mostly, smugly, or about; its head turns in its own frame, whichever way up it is
            local toYou = (rig.rootPart.CFrame * pivot):VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2.5 + math.random() * 3.5
                s.atYou = math.random() < 0.6
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.1, (math.random() - 0.5) * 0.3
            end
            local wantYaw = if s.atYou or active == 1 then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.7, 0.7) else s.gazeYaw
            local wantPitch = if s.atYou or active == 1 then math.clamp(toYou.Y * 0.5, -0.28, 0.3) else s.gazePitch
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 4)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 4)
            local smug = if s.atYou or active == 1 then 1 else 0
            s.smug = (s.smug or 0) + (smug - (s.smug or 0)) * math.min(1, dt * 3)

            -- now and then a chuckle to itself: its shoulders bounce, its head tips back
            s.nextChuckle = s.nextChuckle or t + 6
            if t >= s.nextChuckle then
                s.chuckleAt = t
                s.nextChuckle = t + 7 + math.random() * 7
            end
            local ch = if s.chuckleAt then (t - s.chuckleAt) / 0.9 else 1
            local chuckle = if ch < 1 then math.sin(math.pi * ch) else 0
            cfs.Chest = CFrame.new(0, 0.002 * u * math.abs(math.sin(ch * math.pi * 6)) * chuckle, 0) * CFrame.Angles(0.04 * chuckle, 0, 0)
            cfs.Head = CFrame.Angles(math.clamp(s.pitch + 0.1 * chuckle, -0.28, 0.3), s.yaw, 0.12 * s.smug * (1 - math.abs(s.yaw) / 0.7) + 0.04 * math.sin(t * 0.7))
            cfs.BrowL = CFrame.new(0, (0.0045 * s.smug + 0.002 * up) * u, 0)
            cfs.BrowR = CFrame.new(0, (-0.0015 * s.smug + 0.002 * up) * u, 0)

            -- its ears: a little droop, a flick now and then, a bounce as it walks, perked as it winds up to stamp and flapping when it does, drooped as it
            -- sits back (within what Blender checked: droop -0.3 to 0.45, swing -0.3 to 0.3)
            s.nextFlick = s.nextFlick or t + 2
            if t >= s.nextFlick then
                s.flickAt, s.flickEar = t, if math.random() < 0.5 then "L" else "R"
                s.nextFlick = t + 2 + math.random() * 4
            end
            local fl = if s.flickAt then (t - s.flickAt) / 0.35 else 1
            local flick = if fl < 1 then math.sin(math.pi * fl) else 0
            for tag, sign in { L = 1, R = -1 } do
                local droop = 0.06 + 0.07 * math.sin(2 * s.step) * stepping + 0.15 * s.sit - 0.3 * up + 0.4 * impact
                local swing = (if s.flickEar == tag then 0.28 * flick else 0) + 0.04 * math.sin(t * 1.1 + sign)
                droop = math.clamp(droop, -0.3, 0.45)
                cfs["Ear" .. tag] = CFrame.Angles(0, sign * math.clamp(swing, -0.3, 0.3), sign * droop)
            end

            -- its tail: a lazy sway down its length, its spade flicking now and then (within what Blender checked: sway 0.45, rise -0.15 to 0.25)
            local spade = flick * 0.25
            for k = 1, 4 do
                local sway = 0.22 * math.sin(t * 1.5 - 0.6 * k) + 0.12 * math.sin(s.step) * stepping + (if k == 4 then spade else 0)
                local rise = 0.06 + 0.08 * math.sin(t * 0.8 - 0.5 * k)
                cfs["Tail" .. k] = CFrame.Angles(math.clamp(rise, -0.15, 0.25), math.clamp(sway, -0.45, 0.45), 0)
            end

            -- the stances over all that, each a slerp (CFrame:Lerp) as Blender checked them: fists on its hips unless it treads along; the seat when its
            -- owner flies (its legs swing out ahead, its hips lower after: straight, its feet swept through its moonlet); the stamp
            local akimbo = 1 - walking * (1 - strolling)
            local hips = smoothstep(0.4, 1, s.sit)
            local legs = math.min(1, s.sit / 0.5)
            cfs.Hips = CFrame.new(0, -IMP.DIP * math.sin(s.step) ^ 2 * stepping * u, 0)
            for _, name in IMP.BONES do
                local cf = cfs[name]
                local a = IMP.AKIMBO[name]
                if a then
                    cf = cf:Lerp(IMP.cf(a, u), akimbo)
                end
                a = IMP.SIT[name]
                if a then
                    cf = cf:Lerp(IMP.cf(a, u), if IMP.LEGS[name] then legs elseif name == "Hips" then hips else s.sit)
                end
                a = IMP.STOMP[name]
                if a then
                    cf = cf:Lerp(IMP.cf(a, u), up)
                end
                a = IMP.BALANCE[name]
                if a then
                    cf = cf:Lerp(IMP.cf(a, u), balance)
                end
                pose(m[name], cf)
            end

            -- the pebbles round their orbits, whirling after the stamp
            s.orbit = s.orbit or { 0, 2.1, 4.2 }
            for k, orbit in IMP.ORBITS do
                s.orbit[k] += dt * orbit[2] * (1 + 4 * whirl)
                pose(m["Pebble" .. k], CFrame.fromAxisAngle(orbit[1], s.orbit[k]))
            end

            -- the lids: a quick blink now and then; heavy-lidded the rest of the time (as it was made)
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local b = (t - s.nextBlink) / 0.18
                if b >= 1 then
                    s.nextBlink = t + 2.5 + math.random() * 3
                else
                    blink = 1 - math.abs(2 * b - 1)
                end
            end
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(IMP.LID_HINGE[side], -IMP.BLINK_UPPER * blink))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(IMP.LID_HINGE[side], IMP.BLINK_LOWER * blink))
            end
        end
    end

    return { animateGravityImp = animateGravityImp, IMP = IMP }
end
