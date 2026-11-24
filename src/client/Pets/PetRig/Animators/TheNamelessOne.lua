-- The TheNamelessOne pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep, turtleRay = K.PetRig, K.pose, K.smoothstep, K.turtleRay

    local animateTheNamelessOne, NAMELESS_HALO, NAMELESS_SPARK -- animateTheNamelessOne's section below (its own locals stay in its block)
    do

        -- The Nameless One (skinned): a tall figure with no legs, wound in pale ribbons round nothing, a hollow where its face should be with one point of light
        -- floating in it, a broken halo behind its head. It floats and bobs, its streamers and scarves drifting on a current only it feels; its hood tilts
        -- toward you as if it were trying to read you; now and then one arm lifts and the glowing ends of its ribbons write a loop in the air.
        local NAMELESS_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        NAMELESS_HALO = Color3.fromRGB(184, 156, 255)
        NAMELESS_SPARK = Color3.fromRGB(244, 240, 255)
        local NAMELESS_HEM = {} -- each streamer: the line it swings out about (its outward direction crossed with up), and its own phase
        for k, degrees in { 22, 68, 112, 158, 202, 248, 292, 338 } do
            local angle = math.rad(degrees)
            NAMELESS_HEM[k - 1] = { axis = Vector3.new(math.cos(angle), 0, -math.sin(angle)), phase = (k - 1) * 0.8 }
        end
        local NAMELESS_TIP = { L = Vector3.new(-0.0201, -0.1086, 0.0106), R = Vector3.new(0.0201, -0.1086, 0.0106) } -- from each ArmX5 bone to its longer ribbon's tip, in metres
        local NAMELESS_SOLE, NAMELESS_HOVER = 0.6081, 0.12 -- metres from the middle of its box down to its lowest streamer; how far that floats clear of the ground

        -- It is taller than the height a companion is held at: lifted so its streamers float a hand's breadth clear of the ground under it, never lowered
        local function namelessHover(rig, s, t, u, fly)
            s.nextGround = s.nextGround or 0
            if t >= s.nextGround then
                s.nextGround = t + 0.15
                local from = rig.rootPart.Position
                local hit = workspace:Raycast(from, Vector3.new(0, -12 * u, 0), turtleRay)
                local onCharacter = hit and hit.Instance.Parent and hit.Instance.Parent:FindFirstChildOfClass("Humanoid")
                if not onCharacter then -- (a player walking under it: keep what it had)
                    s.liftTo = if hit then math.max(0, (NAMELESS_SOLE + NAMELESS_HOVER) * u - (from.Y - hit.Position.Y)) else 0
                end
            end
            local target = (s.liftTo or 0) * (1 - fly)
            s.lift = (s.lift or target) + (target - (s.lift or target)) * math.min(1, rig.deltaTime * 4)
            return s.lift
        end

        local function namelessGone(rig, s, gone)
            if s.gone == gone then
                return
            end
            s.gone = gone
            for _, key in { "Body", "Spark", "Halo", "QuillL", "QuillR" } do
                local part = rig.parts[key]
                if part then
                    part.Transparency = gone
                end
            end
            if s.namelessLight then
                s.namelessLight.Enabled = gone < 0.9
            end
        end

        local function namelessPen(rig)
            local metre = rig.meters
            local holder = Instance.new("Part")
            holder.Name = "Pen"
            holder.Anchored = true
            holder.CanCollide = false
            holder.CanTouch = false
            holder.CanQuery = false
            holder.CastShadow = false
            holder.Transparency = 1
            holder.Size = Vector3.one * 0.05
            local a, b = Instance.new("Attachment"), Instance.new("Attachment")
            a.Position, b.Position = Vector3.new(0, 0.01 * metre, 0), Vector3.new(0, -0.01 * metre, 0)
            a.Parent, b.Parent = holder, holder
            local trail = Instance.new("Trail")
            trail.Attachment0, trail.Attachment1 = a, b
            trail.FaceCamera = true
            trail.Lifetime = 0.5
            trail.LightEmission = 1
            trail.LightInfluence = 0
            trail.WidthScale = NumberSequence.new(1, 0.2)
            trail.Color = ColorSequence.new(NAMELESS_SPARK, NAMELESS_HALO)
            trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(1, 1) })
            trail.Enabled = false
            trail.Parent = holder
            holder.Parent = rig.model -- goes when the pet goes
            return { part = holder, trail = trail }
        end

        function animateTheNamelessOne(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > NAMELESS_FAR then
                namelessGone(rig, s, 0)
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special, Unwritten: both arms rise, forward and apart; at the burst its writing appears round it (Blasts.Unwritten) and its hands trace it;
            -- each word is struck through; and for a moment it is gone, then back
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local raise = smoothstep(0.04, 0.36, progress) * (1 - smoothstep(0.62, 0.72, progress))
            local write = smoothstep(0.4, 0.45, progress) * (1 - smoothstep(0.6, 0.66, progress))
            local gone = smoothstep(0.64, 0.72, progress) * (1 - smoothstep(0.8, 0.9, progress))
            namelessGone(rig, s, math.floor(gone * 20 + 0.5) / 20)

            -- now and then, while it is still, one arm lifts and its glowing ends write a loop in the air
            s.penSide = s.penSide or (if math.random() < 0.5 then "L" else "R")
            s.nextWrite = s.nextWrite or t + 5 + math.random() * 6
            local pen = 0
            if t >= s.nextWrite then
                local a = (t - s.nextWrite) / 2.6
                if a >= 1 then
                    s.nextWrite = t + 9 + math.random() * 9
                    s.penSide = if math.random() < 0.5 then "L" else "R"
                elseif pace < 0.3 and nova == 0 then
                    pen = smoothstep(0, 0.25, a) * (1 - smoothstep(0.78, 1, a))
                else
                    s.nextWrite = t + 4
                end
            end

            -- it floats: a slow bob, leaning into its way when it moves, banking on turns
            local look = rig.rootPart.CFrame.LookVector
            local heading = math.atan2(-look.X, -look.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.18, 0.18) - (s.bank or 0)) * math.min(1, dt * 3)
            local bob = 0.022 * math.sin(t * 1.1) + 0.008 * math.sin(t * 2.3 + 1)
            local lift = namelessHover(rig, s, t, u, fly)
            pose(m.Hips, CFrame.new(0, (bob + 0.05 * raise) * u + lift, 0) * CFrame.Angles(-0.14 * moving - 0.22 * fly + 0.03 * raise, 0.04 * math.sin(t * 0.37), s.bank + 0.025 * math.sin(t * 0.53)))
            pose(m.Body, CFrame.Angles(0.02 * math.sin(t * 1.1 - 0.6) - 0.04 * moving, 0.03 * math.sin(t * 0.41 + 1), 0))
            pose(m.Chest, CFrame.Angles(0.015 * math.sin(t * 1.1 - 1.2) + 0.08 * raise, 0.04 * math.sin(t * 0.33 + 2), 0))

            -- the hood turns toward you and tilts, slowly, as if reading you; it watches its own hand when it writes, and looks up at its writing
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            local calm = (1 - pace) * (1 - raise) * (1 - pen)
            local wantYaw = math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.7, 0.7) * calm + (if s.penSide == "L" then 0.45 else -0.45) * pen
            local wantPitch = math.clamp(toYou.Y, -0.5, 0.6) * 0.5 * calm - 0.3 * pen + 0.22 * raise
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2)
            local roll = (0.22 * math.sin(t * 0.31) + 0.06 * math.sin(t * 0.83)) * (1 - pace) * (1 - raise)
            pose(m.Neck, CFrame.Angles(0.4 * s.pitch, 0.4 * s.yaw, 0.3 * roll))
            pose(m.Head, CFrame.Angles(0.6 * s.pitch, 0.6 * s.yaw, 0.7 * roll))

            -- the point of light drifts in the hollow; the broken halo turns, fast while it writes, and burns white
            pose(m.Spark, CFrame.new(0.004 * math.sin(t * 1.7) * u, 0.003 * math.sin(t * 2.3 + 1) * u, 0))
            s.halo = ((s.halo or 0) + dt * (0.25 + 2.5 * raise + 4 * write)) % (2 * math.pi)
            pose(m.Halo, CFrame.new(0, 0.006 * math.sin(t * 0.9) * u, 0) * CFrame.Angles(0, 0, s.halo))
            local burn = NAMELESS_HALO:Lerp(NAMELESS_SPARK, math.max(0.6 * write, 0.4 * pen))
            for _, key in { "Halo", "QuillL", "QuillR" } do
                local part = rig.parts[key]
                if part then
                    part.Color = burn
                end
            end
            if not s.namelessLight and rig.points.Spark then
                local light = Instance.new("PointLight")
                light.Color = NAMELESS_SPARK
                light.Range = 0.5 * u
                light.Shadows = false
                light.Parent = rig.points.Spark
                s.namelessLight = light
            end
            if s.namelessLight then
                s.namelessLight.Brightness = 0.8 + 0.3 * math.sin(t * 2.1) + 2.5 * write
            end

            -- the arms hang and sway, trail behind as it goes, rise for the special; the writing hand traces small loops
            s.pens = s.pens or {}
            for _, side in { "L", "R" } do
                local out = if side == "L" then -1 else 1 -- a positive turn about Z swings a hanging arm out to its right; to its left, a negative one
                local mine = if side == s.penSide then pen else 0
                local phase = if side == "L" then 0 else 1.7
                pose(m["Arm" .. side .. "1"], CFrame.Angles(0.04 * math.sin(t * 0.8 + phase) - 0.18 * moving - 0.25 * fly + 1.25 * raise + 1.0 * mine, 0, out * (0.03 + 0.45 * raise + 0.12 * mine)))
                pose(m["Arm" .. side .. "2"], CFrame.Angles(0.05 + 0.04 * math.sin(t * 0.8 + phase + 0.5) + 0.35 * raise + 0.75 * mine, 0, 0))
                local loop = math.max(write, mine)
                local w = t * 9 + phase
                pose(m["Arm" .. side .. "3"], CFrame.Angles(0.3 * loop * math.sin(w) + 0.05 * math.sin(t * 1.1 + phase), 0.3 * loop * math.cos(w), 0))
                pose(m["Arm" .. side .. "4"], CFrame.Angles(0.12 * math.sin(t * 1.3 + phase) - 0.25 * moving - 0.3 * fly, 0, 0.08 * math.sin(t * 1.1 + phase)))
                pose(m["Arm" .. side .. "5"], CFrame.Angles(0.16 * math.sin(t * 1.3 + phase - 0.8) - 0.3 * moving - 0.35 * fly, 0, 0.1 * math.sin(t * 1.1 + phase - 0.7)))
                local active = (mine > 0.4 or write > 0.4) and gone < 0.5
                if active and not s.pens[side] then
                    s.pens[side] = namelessPen(rig)
                end
                local holder = s.pens[side]
                local bone = rig.points["Arm" .. side .. "5"]
                if holder and bone then
                    holder.part.CFrame = CFrame.new(bone.TransformedWorldCFrame:PointToWorldSpace(NAMELESS_TIP[side] * u))
                    holder.trail.Enabled = active
                end
            end

            -- the streamers drift out and back, each on its own wave, swirl a little, stream behind it as it goes, and flare at the burst
            for k, hem in NAMELESS_HEM do
                for i, tag in { "a", "b", "c" } do
                    local outward = (0.03 + 0.03 * math.sin(t * 1.2 + hem.phase - i * 0.7)) * (1 - 0.5 * pace) + 0.14 * write
                    local back = -(0.07 * moving + 0.1 * fly) * (0.6 + 0.4 * i)
                    pose(m["Hem" .. k .. tag], CFrame.Angles(back, 0.05 * math.sin(t * 0.9 + hem.phase - i * 0.6), 0) * CFrame.fromAxisAngle(hem.axis, outward))
                end
            end
            -- the scarves rise and ripple on the same current, blown back as it goes
            for _, side in { "L", "R" } do
                local sign = if side == "L" then -1 else 1
                for i = 1, 3 do
                    local wave = math.sin(t * 1.15 + (if side == "L" then 0 else 2) - i * 0.9)
                    pose(m["Scarf" .. side .. i], CFrame.Angles(0.04 * i * wave + (0.08 * moving + 0.12 * fly) * (0.5 + 0.25 * i), 0.05 * math.sin(t * 0.7 - i * 0.8 + sign), sign * 0.04 * wave))
                end
            end
        end
    end

    return { animateTheNamelessOne = animateTheNamelessOne, NAMELESS_HALO = NAMELESS_HALO, NAMELESS_SPARK = NAMELESS_SPARK }
end
