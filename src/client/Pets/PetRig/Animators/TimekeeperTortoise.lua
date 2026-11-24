-- The TimekeeperTortoise pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep, dropToGround = K.PetRig, K.pose, K.smoothstep, K.dropToGround

    local animateTimekeeperTortoise, TORT -- animateTimekeeperTortoise's section below (its own locals stay in its block)
    do

        -- The Timekeeper Tortoise (skinned): an ancient giant tortoise whose shell is a sundial. It walks impossibly slowly, a deliberate diagonal step, and yet
        -- is never left behind; standing, it turns its old head slowly to look about or at you, its long white brows lifting when it does, blinks slow heavy
        -- blinks and chews on nothing; its tail sways. When its owner flies it pulls itself into its shell and drifts beside them like a stone.
        TORT = {
            FAR = 100, -- studs from the camera past which nobody can see it fidget: its bones rest
            BODY_SOLE = 0.36, -- metres from its Body bone down to the soles of its feet (timekeeper_tortoise.py): it stands on the ground
            LID_HINGE = { L = Vector3.new(0.5402, 0.1012, -0.8354), R = Vector3.new(0.5402, -0.1012, 0.8354) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(40),
            BLINK_LOWER = math.rad(16),
            GOLD = Color3.fromRGB(255, 207, 110),
            SEPIA = Color3.fromRGB(255, 236, 200),
            -- its walk, checked in Blender at eight points of its cycle: diagonal pairs; each leg swings at its shoulder, its knee lifting the foot (front legs one
            -- way, hind legs the other), the shoulder raised or lowered by the arc its swing would trace, so a planted foot stays on the ground
            LEADS = { FL = 0, BR = 0, FR = math.pi, BL = math.pi },
            ARC = { F = { 0.0196, 0.0041 }, B = { -0.01745, 0.00385 } }, -- a foot's height through its swing's arc: a * sw + b * sw^2 (metres, at full swing)
            SWING = 0.22,
            LIFT = 0.6,
            -- pulled into its shell (checked in Blender: its face peeks out of the front opening between its folded forelegs; nothing pokes through the dome)
            TUCK = {
                Neck1 = { -0.3, 0, 0 }, Neck2 = { 0.3, 0, 0 }, Head = { 0.1, 0, 0 },
                LegFL2 = { 0.9, 0, 0 }, LegFR2 = { 0.9, 0, 0 }, LegBL2 = { -0.9, 0, 0 }, LegBR2 = { -0.9, 0, 0 },
            },
            TUCK_MOVE = { -- metres, the game's axes
                Neck1 = Vector3.new(0, -0.08, 0.22),
                LegFL1 = Vector3.new(0.05, 0.1, 0.03), LegFR1 = Vector3.new(-0.05, 0.1, 0.03), LegBL1 = Vector3.new(0.05, 0.1, -0.03), LegBR1 = Vector3.new(-0.05, 0.1, -0.03), -- (a left leg moves in along +X)
            },
            -- the special's stance: planted, its head raised and its brows up, proud
            PLANT = { Neck1 = { 0.12, 0, 0 }, Neck2 = { 0.12, 0, 0 }, Head = { 0.18, 0, 0 }, BrowL = { -0.25, 0, 0 }, BrowR = { -0.25, 0, 0 } },
            BONES = {
                "Body", "Neck1", "Neck2", "Head", "Jaw", "BrowL", "BrowR", "Tail",
                "LegFL1", "LegFL2", "FootFL", "LegFR1", "LegFR2", "FootFR", "LegBL1", "LegBL2", "FootBL", "LegBR1", "LegBR2", "FootBR",
            },
        }

        function animateTimekeeperTortoise(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > TORT.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime

            -- the special, Stopped Hour: it plants itself and raises its head (to 0.42; Blasts.StoppedHour), and for a heartbeat time stops: it does not move
            -- at all, not a blink; then time starts again and it settles
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local plant = smoothstep(0.03, 0.3, progress) * (1 - smoothstep(0.78, 0.98, progress))
            local stopped = if progress > 0.42 and progress < 0.72 then 1 else 0
            s.clock = (s.clock or 0) + dt * (1 - stopped) -- its own time, which stops with the world's
            local tt = s.clock

            local hips = rig.points.Body
            if hips and not s.sole then
                s.sole = rig.rootPart.CFrame:PointToObjectSpace(hips.WorldPosition).Y * -1 / u + TORT.BODY_SOLE -- (WorldPosition leaves out its own Transform)
            end
            local drop = dropToGround(rig, s, t, u, fly, s.sole or 0.5)
            local tuck = smoothstep(0, 1, fly) * (1 - plant)

            -- the walk: slow and deliberate however fast its owner goes, and yet it keeps up
            local step = moving * (1 - tuck) * (1 - plant)
            s.step = (s.step or 0) + dt * (2.2 + 1.3 * moving) * step * (1 - stopped)
            local want, moves = {}, {}
            for key, lead in TORT.LEADS do
                local sw = math.sin(s.step + lead) * step
                local lf = math.max(0, math.cos(s.step + lead)) * step
                local a1 = TORT.SWING * sw
                local a2 = (if string.sub(key, 1, 1) == "F" then 1 else -1) * TORT.LIFT * lf
                local arc = TORT.ARC[string.sub(key, 1, 1)]
                want["Leg" .. key .. "1"] = Vector3.new(a1, 0, 0)
                want["Leg" .. key .. "2"] = Vector3.new(a2, 0, 0)
                want["Foot" .. key] = Vector3.new(-(a1 + a2), 0, 0)
                moves["Leg" .. key .. "1"] = Vector3.new(0, -(arc[1] * sw + arc[2] * sw * sw), 0)
            end

            -- looking about: slowly, as an old one does; most often at you; its brows lift when it looks at you
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 4 + math.random() * 5
                s.atYou = math.random() < 0.55
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.2, (math.random() - 0.5) * 0.3
            end
            local calm = (1 - tuck) * (1 - 0.6 * step)
            local wantYaw = (if s.atYou or plant > 0 then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.4, -0.2, 0.25) else s.gazePitch) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 1.2) * (1 - stopped)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 1.2) * (1 - stopped)
            local yawShare = math.clamp(s.yaw / 0.8, -1, 1) -- (as far as Blender checked: neck 0.35, head 0.45)
            local brow = (if s.atYou then 1 else 0) * calm
            s.brow = (s.brow or 0) + (brow - (s.brow or 0)) * math.min(1, dt * 2) * (1 - stopped)
            local bob = 0.04 * math.sin(s.step * 2) * step
            want.Neck1 = Vector3.new(0.02 * math.sin(tt * 0.5), 0, 0)
            want.Neck2 = Vector3.new(0.4 * s.pitch + bob, 0.35 * yawShare, 0)
            want.Head = Vector3.new(0.6 * s.pitch - bob * 0.5, 0.45 * yawShare, 0.1 * yawShare)
            want.BrowL = Vector3.new(-0.22 * s.brow + 0.03 * math.sin(tt * 0.8), 0, 0)
            want.BrowR = Vector3.new(-0.22 * s.brow + 0.03 * math.sin(tt * 0.8 + 1), 0, 0)

            -- it chews on nothing now and then
            s.nextChew = s.nextChew or t + 5
            if t >= s.nextChew then
                s.chewAt = tt
                s.nextChew = t + 6 + math.random() * 6
            end
            local chewEnv = if s.chewAt then (tt - s.chewAt) / 1.8 else 1
            local chew = if chewEnv < 1 then (0.5 - 0.5 * math.cos(chewEnv * 6 * math.pi)) * math.sin(math.pi * chewEnv) else 0
            want.Jaw = Vector3.new(-0.12 * chew * (1 - tuck), 0, 0)
            want.Tail = Vector3.new(0, 0.25 * math.sin(tt * 0.6) + 0.15 * math.sin(s.step) * step, 0)

            -- the special's stance, and the tuck
            for name, a in TORT.PLANT do
                want[name] = (want[name] or Vector3.zero) * (1 - plant) + Vector3.new(a[1], a[2], a[3]) * plant
            end
            for _, name in TORT.BONES do
                local a = TORT.TUCK[name]
                local target = if a then Vector3.new(a[1], a[2], a[3]) else Vector3.zero
                if string.sub(name, 1, 4) == "Foot" or name == "Jaw" or string.sub(name, 1, 4) == "Brow" or name == "Tail" or name == "Body" then
                    target = want[name] or Vector3.zero -- (these keep their own turns when it tucks)
                end
                want[name] = (want[name] or Vector3.zero) * (1 - tuck) + target * tuck
                moves[name] = (moves[name] or Vector3.zero) * (1 - tuck) + (TORT.TUCK_MOVE[name] or Vector3.zero) * tuck
            end

            -- its body: a slow roll with its step; tucked and drifting, a slow tilt; it stands on the ground, or keeps to its owner's height when they fly
            local sway = 0.025 * math.sin(s.step) * step
            local drift = Vector3.new(0.05 * math.sin(tt * 0.7), 0, 0.04 * math.sin(tt * 0.5)) * tuck
            local lift = -drop + 0.004 * math.abs(math.sin(2 * s.step)) * step * u
            pose(m.Body, CFrame.new(0, lift, 0) * CFrame.Angles(drift.X, 0, sway + drift.Z))
            for _, name in TORT.BONES do
                if name ~= "Body" then
                    local a = want[name] or Vector3.zero
                    local mv = moves[name] or Vector3.zero
                    pose(m[name], CFrame.new(mv * u) * CFrame.Angles(a.X, a.Y, a.Z))
                end
            end

            -- the lids: a slow, heavy blink now and then; none while time stands still
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink and stopped == 0 then
                local a = (t - s.nextBlink) / 0.6
                if a >= 1 then
                    s.nextBlink = t + 4 + math.random() * 5
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local shut = math.max(blink, 0.85 * tuck)
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(TORT.LID_HINGE[side], -TORT.BLINK_UPPER * shut))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(TORT.LID_HINGE[side], TORT.BLINK_LOWER * shut))
            end
        end
    end

    return { animateTimekeeperTortoise = animateTimekeeperTortoise, TORT = TORT }
end
