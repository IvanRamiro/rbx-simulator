-- FrostfangSerpent: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Debris, Players, TweenService, SPARKLE, tweenAfter, pose, smoothstep, Blasts, dropToGround = K.PetRig, K.Debris, K.Players, K.TweenService, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.dropToGround


    -- ---------- The Frostfang Serpent: all of it in one block, so its locals are freed at its end (the main chunk sits at Luau's limit of 200 locals) ----------
    do
        -- The Frostfang Serpent (skinned): a frozen-hood king cobra. It rests coiled, its front reared in an S, its great hood of frosted ice spread and
        -- crowned with blades of clear ice; it stares, unblinking (a snake has no lids), its head following you; its tongue flicks; now and then it hisses,
        -- hood flared, mouth open on two glowing crystal fangs that swing down from its palate. Around it, time stops: shards of ice drift off it and hang
        -- still in the air, and now and then it sheds a pane of clear ice that slides off its coil and shatters. It never uncoils: to go anywhere it leans
        -- into a glide, its hood half folded, a ripple running round its coil, frost forming where it passes; on the wing it hovers, coiled. Its special,
        -- The Moment That Matters: it rears, hood flared, fangs out, and strikes; where it bites, a hexagon of stopped time spreads, everything in it hanging
        -- still, and then shatters (Blasts.TheMomentThatMatters).
        local FS = {
            FAR = 110, -- studs from the camera past which nobody can see it fidget: its bones rest
            SOLE = 0.4331, -- metres from the middle of its box down to its coil (frostfang_serpent.py)
            HOVER_UP = 0.28, -- metres it rises on the wing
            RIPPLE = 0.07, -- radians: each coil bone's sway as the ripple runs round its coil (frostfang_serpent.py's RIPPLE, RIPPLE_STEP: checked at
            RIPPLE_STEP = 0.9, -- four phases of it and along the slerps between)
            COILS = 12,
            HEAD_AT = Vector3.new(0, 0.81, -0.17), -- its Head bone's head, metres in its own axes
            BITE_AT = Vector3.new(0, 0.785, -0.304), -- just past the end of its snout
            -- its stances, fitted in Blender (frostfang_serpent.py's pose_tables: its spine laid along a curve, carried along it without twisting) and checked
            -- there in each and along every slerp the game makes (skin against itself, ice against body, fangs and tongue against its jaw, ground)
            GLIDE = {
                Base = { -0.0004, 0, -0.0001 }, Coil1 = { 0.0004, 0, 0.0001 }, Head = { 0.1582, -0.1805, 0.3602 }, HoodL1 = { 0, 0.45, 0 },
                HoodL2 = { 0, 0.3825, 0 }, HoodR1 = { 0, -0.45, 0 }, HoodR2 = { 0, -0.3825, 0 }, Up1 = { 0.0001, 0.0008, 0.0039 }, Up2 = { 0.0586, 0.0421, 0.0011 },
                Up3 = { -0.4547, 0.147, -0.0747 }, Up4 = { -0.3282, 0.172, -0.0175 }, Up5 = { -0.0947, 0.0622, -0.0569 }, Up6 = { 0.2892, -0.0095, -0.0779 },
                Up7 = { 0.4365, -0.0358, 0.0316 },
            },
            HOVER = {
                HoodL1 = { 0, 0.2, 0 }, HoodL2 = { 0, 0.17, 0 }, HoodR1 = { 0, -0.2, 0 }, HoodR2 = { 0, -0.17, 0 },
            },
            REAR = {
                Base = { -0.0004, 0, -0.0001 }, Coil1 = { 0.0004, 0, 0.0001 }, Fangs = { 1.5359, 0, 0 }, Head = { -0.1142, -0.0435, 0.0211 },
                HoodL1 = { 0, -0.25, 0 }, HoodL2 = { 0, -0.2125, 0 }, HoodR1 = { 0, 0.25, 0 }, HoodR2 = { 0, 0.2125, 0 }, Jaw = { -0.62, 0, 0 },
                Up1 = { 0.0001, 0.0008, 0.0039 }, Up2 = { -0.0032, 0.0031, -0.0121 }, Up3 = { 0.004, -0.0056, 0.0809 }, Up4 = { -0.1414, 0.0563, 0.0459 },
                Up5 = { 0.0509, 0.043, -0.1461 }, Up6 = { 0.1458, 0.0148, -0.0478 }, Up7 = { 0.5123, -0.0035, 0.1038 },
            },
            STRIKE = {
                Base = { -0.0004, 0, -0.0001 }, Coil1 = { 0.0004, 0, 0.0001 }, Fangs = { 1.5359, 0, 0 }, Head = { 0.8838, 0.1823, 0.5587 }, HoodL1 = { 0, -0.3, 0 },
                HoodL2 = { 0, -0.255, 0 }, HoodR1 = { 0, 0.3, 0 }, HoodR2 = { 0, 0.255, 0 }, Jaw = { -0.7, 0, 0 }, Up1 = { 0.0001, 0.0008, 0.0039 },
                Up2 = { 0.0665, 0.0407, -0.0123 }, Up3 = { -0.6528, 0.2057, -0.0025 }, Up4 = { -0.6655, 0.3253, 0.0291 }, Up5 = { -0.2564, 0.1942, -0.2569 },
                Up6 = { -0.0526, 0.0489, -0.2818 }, Up7 = { 0.7032, -0.1128, 0.0112 },
            },
            HISS = {
                Fangs = { 1.5359, 0, 0 }, Head = { -0.1, 0, 0 }, HoodL1 = { 0, -0.22, 0 }, HoodL2 = { 0, -0.187, 0 }, HoodR1 = { 0, 0.22, 0 },
                HoodR2 = { 0, 0.187, 0 }, Jaw = { -0.42, 0, 0 }, Up6 = { 0.12, 0, 0 }, Up7 = { 0.12, 0, 0 },
            },
            TONGUE_UP = {
                Tongue = { 0, 0, 0, 0, 0.0075, 0 },
            },
            TONGUE = {
                Tongue = { 0, 0, 0, 0, 0.01, -0.07 },
            },
            BONES = {
                "Base", "Coil1", "Coil2", "Coil3", "Coil4", "Coil5", "Coil6", "Coil7", "Coil8", "Coil9", "Coil10", "Coil11", "Coil12",
                "Up1", "Up2", "Up3", "Up4", "Up5", "Up6", "Up7", "Head", "Jaw", "Fangs", "HoodL1", "HoodL2", "HoodR1", "HoodR2",
            },
            -- where on its coil a pane of ice may peel off: a coil bone, and its body's radius there (metres)
            SHED = { { "Coil2", 0.088 }, { "Coil4", 0.08 }, { "Coil6", 0.071 }, { "Coil8", 0.06 } },
            CORE = Color3.fromRGB(240, 252, 255),
            MAIN = Color3.fromRGB(130, 210, 255),
            DEEP = Color3.fromRGB(60, 120, 210),
            ICE = Color3.fromRGB(176, 226, 255),
        }

        function FS.cf(a, u)
            if not a then
                return CFrame.identity
            end
            local move = if a[4] then CFrame.new(a[4] * u, a[5] * u, a[6] * u) else CFrame.identity
            return move * CFrame.Angles(a[1], a[2], a[3])
        end

        function FS.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        -- The ripple round its coil: each coil bone's own turn the difference from the one before, so each lies at most RIPPLE off its rest.
        function FS.ripple(phase, k)
            local function world(j)
                return if j == 0 then 0 else FS.RIPPLE * math.sin(phase - FS.RIPPLE_STEP * j)
            end
            return world(k) - world(k - 1)
        end

        -- Once, at rest: where the bite lands, carried on its Head bone; its cold light; the stopped-time shards drifting off it and the frost it leaves.
        function FS.init(rig, s)
            s.inited = true
            local head = rig.points.Head
            if head then
                local headCf = head.TransformedWorldCFrame
                local world = headCf.Position + rig.rootPart.CFrame:VectorToWorldSpace((FS.BITE_AT - FS.HEAD_AT) * rig.meters)
                s.biteOffset = headCf:PointToObjectSpace(world)
                local at = Instance.new("Attachment")
                at.Name = "ColdLight"
                at.Parent = head
                local light = Instance.new("PointLight")
                light.Name = "PulseLight"
                light.Color = FS.MAIN
                light.Range = 5 * rig.unit
                light.Brightness = 1
                light.Shadows = false
                light.Parent = at
                rig.light = light
                -- shards of ice that drift off it and stop: time standing still round it (they hang where they stop, so it leaves them behind as it goes)
                local shards = Instance.new("ParticleEmitter")
                shards.Name = "StoppedTime"
                shards.Texture = SPARKLE
                shards.Rate = if FS.reduced() then 0.8 else 2.5
                shards.Lifetime = NumberRange.new(2.2, 3.4)
                shards.Speed = NumberRange.new(0.6 * rig.unit, 1.4 * rig.unit)
                shards.SpreadAngle = Vector2.new(180, 180)
                shards.Drag = 7 -- out, and then still
                shards.Rotation = NumberRange.new(0, 360)
                shards.RotSpeed = NumberRange.new(0, 0)
                shards.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.08, 0.1 * rig.unit), NumberSequenceKeypoint.new(0.8, 0.09 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
                shards.Color = ColorSequence.new(FS.CORE, FS.MAIN)
                shards.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(0.85, 0.35), NumberSequenceKeypoint.new(1, 1) })
                shards.LightEmission = 0.8
                shards.LightInfluence = 0.2
                shards.Parent = at
            end
            local base = rig.points.Base
            if base then
                local frost = Instance.new("ParticleEmitter")
                frost.Name = "Frost"
                frost.Texture = SPARKLE
                frost.Rate = 0
                frost.Lifetime = NumberRange.new(1.2, 2)
                frost.Speed = NumberRange.new(0, 0)
                frost.Acceleration = Vector3.zero
                frost.Rotation = NumberRange.new(0, 360)
                frost.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.18 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
                frost.Color = ColorSequence.new(FS.CORE, FS.ICE)
                frost.Transparency = NumberSequence.new(0.35, 1)
                frost.LightEmission = 0.5
                frost.Parent = base
                s.frost = frost
            end
        end

        function FS.folder(rig)
            local folder = Instance.new("Folder")
            folder.Name = "PetSpecial"
            folder.Parent = rig.model.Parent or workspace
            Debris:AddItem(folder, 2.5)
            return folder
        end

        function FS.glass(folder, size, cframe, transparency)
            local part = Instance.new("Part")
            part.Anchored = true
            part.CanCollide = false
            part.CanTouch = false
            part.CanQuery = false
            part.CastShadow = false
            part.Material = Enum.Material.Glass
            part.Color = FS.ICE
            part.Transparency = transparency or 0.35
            part.Size = size
            part.CFrame = cframe
            part.Parent = folder
            return part
        end

        -- It sheds a pane of clear ice: it lifts off its coil, slides away down its side and shatters on the ground.
        function FS.shed(rig)
            if FS.reduced() then
                return
            end
            local pick = FS.SHED[math.random(1, #FS.SHED)]
            local bone = rig.points[pick[1]]
            if not bone then
                return
            end
            local u = rig.unit
            local at = bone.TransformedWorldCFrame.Position + Vector3.new(0, pick[2] * rig.meters, 0)
            local out = (at - rig.rootPart.Position) * Vector3.new(1, 0, 1)
            out = if out.Magnitude > 1e-3 then out.Unit else rig.rootPart.CFrame.RightVector
            local folder = FS.folder(rig)
            local pane = FS.glass(folder, Vector3.new(0.34 * u, 0.025 * u, 0.24 * u), CFrame.lookAt(at, at + out) * CFrame.Angles(0, 0, math.rad(8)), 0.3)
            local land = at + out * 0.45 * u - Vector3.new(0, pick[2] * rig.meters * 1.6, 0)
            TweenService:Create(pane, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                CFrame = CFrame.lookAt(land, land + out) * CFrame.Angles(math.rad(-35), 0, math.rad(20)),
            }):Play()
            local bits = Instance.new("ParticleEmitter")
            bits.Texture = SPARKLE
            bits.Enabled = false
            bits.Lifetime = NumberRange.new(0.4, 0.8)
            bits.Speed = NumberRange.new(0.8 * u, 1.8 * u)
            bits.SpreadAngle = Vector2.new(70, 70)
            bits.Acceleration = Vector3.new(0, -5 * u, 0)
            bits.Size = NumberSequence.new(0.07 * u, 0)
            bits.Color = ColorSequence.new(FS.CORE, FS.ICE)
            bits.LightEmission = 0.6
            bits.Parent = pane
            task.delay(0.7, function()
                if pane.Parent then
                    bits:Emit(14) -- it shatters
                    pane.Transparency = 1
                end
            end)
        end

        local function animateFrostfangSerpent(rig, s, moving, fly, nova)
            if not s.inited then
                FS.init(rig, s) -- at rest, before any pose
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > FS.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime

            -- the special, The Moment That Matters: it settles if it is flying; rears, hood flared, fangs out (to 0.26); holds, swaying back, coiled to
            -- strike; strikes (0.38 to 0.42: Blasts.TheMomentThatMatters, where it bites); holds the strike; settles by 0.92
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local active = if rig.nova then 1 else 0
            s.air = (s.air or 0) + (fly * (1 - active) - (s.air or 0)) * math.min(1, dt * 2.5)
            local air = s.air
            local rear = smoothstep(0.03, 0.26, progress) * active
            local strike = smoothstep(0.38, 0.42, progress) * active
            local settle = smoothstep(0.66, 0.92, progress) * active
            local coil = math.sin(math.pi * smoothstep(0.26, 0.38, progress)) * active -- drawn back, about to strike

            local drop = dropToGround(rig, s, t, u, air, FS.SOLE)

            -- gliding: it leans in, its hood half folded, a ripple running round its coil; frost forms where it passes
            local gliding = moving * (1 - smoothstep(0.05, 0.3, air)) * (1 - active)
            s.wave = (s.wave or 0) + dt * (2.2 + 4 * moving) * gliding
            if s.frost then
                s.frost.Rate = if FS.reduced() then 0 else 14 * gliding
            end

            -- idle business, when it is still: a hiss now and then, hood flared, fangs out; or a pane of ice sheds off its coil
            local still = (1 - moving) * (1 - smoothstep(0.05, 0.3, air)) * (1 - active)
            s.nextIdle = s.nextIdle or t + 6
            if t >= s.nextIdle and still > 0.9 then
                s.idleAt, s.idleKind = t, if math.random() < 0.6 then "hiss" else "shed"
                s.nextIdle = t + 9 + math.random() * 9
                if s.idleKind == "shed" then
                    FS.shed(rig)
                end
            end
            local idle = if s.idleAt then (t - s.idleAt) / 1.8 else 1
            local hiss = (if s.idleKind == "hiss" and idle < 1 then smoothstep(0, 0.25, idle) * (1 - smoothstep(0.75, 1, idle)) else 0) * still

            -- its gaze: steady, a cobra's stare; it settles on you and holds; its column sways a little as it breathes
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 3 + math.random() * 4
                s.atYou = math.random() < 0.6
                s.gazeYaw = (math.random() - 0.5) * 1.4
            end
            local calm = (1 - 0.5 * gliding) * (1 - rear) * (1 - strike)
            local wantYaw = math.clamp(if s.atYou then math.atan2(-toYou.X, -toYou.Z) else s.gazeYaw, -1, 1) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 1.8)
            local sway = math.sin(t * 0.7)
            local breath = math.sin(t * 1.1)

            for _, name in FS.BONES do
                local rest = CFrame.identity
                local glide = FS.cf(FS.GLIDE[name], u)
                local cf = rest:Lerp(glide, gliding)
                local k = tonumber(string.match(name, "^Coil(%d+)$"))
                if k then
                    cf *= CFrame.Angles(0, FS.ripple(s.wave, k) * gliding, 0)
                end
                cf = cf:Lerp(FS.cf(FS.HOVER[name], u), air)
                cf = cf:Lerp(FS.cf(FS.HISS[name], u), hiss)
                if active == 1 then
                    local reared, struck = FS.cf(FS.REAR[name], u), FS.cf(FS.STRIKE[name], u)
                    local special = if strike > 0 then reared:Lerp(struck, strike):Lerp(CFrame.identity, settle) else cf:Lerp(reared, rear)
                    cf = special
                end
                -- over the stance: its breath and sway, its stare, drawn back before it strikes
                if name == "Up3" or name == "Up4" then
                    cf *= CFrame.Angles(0.012 * breath, 0.03 * sway * calm, 0)
                elseif name == "Up5" or name == "Up6" or name == "Up7" then
                    cf *= CFrame.Angles(-0.08 * coil, 0.25 * s.yaw, 0)
                elseif name == "Head" then
                    cf *= CFrame.Angles(0.06 * coil, 0.3 * s.yaw, 0.08 * s.yaw)
                end
                if name == "Base" then
                    cf = CFrame.new(0, FS.HOVER_UP * air * u - drop, 0) * cf
                end
                pose(m[name], cf)
            end

            -- its tongue: a flick now and then: up into its mouth's gap, out between its lips, back
            s.nextFlick = s.nextFlick or t + 2
            local up, out = 0, 0
            if t >= s.nextFlick then
                local a = (t - s.nextFlick) / 0.5
                if a >= 1 then
                    s.nextFlick = t + 1.5 + math.random() * 3
                elseif active == 0 and hiss == 0 then
                    up = smoothstep(0, 0.15, a) * (1 - smoothstep(0.85, 1, a))
                    out = math.sin(math.pi * smoothstep(0.15, 0.85, a))
                end
            end
            pose(m.Tongue, FS.cf(FS.TONGUE_UP.Tongue, u):Lerp(FS.cf(FS.TONGUE.Tongue, u), out):Lerp(CFrame.identity, 1 - up))
        end

        -- It has struck (animateFrostfangSerpent): where it bit, a hexagon of stopped time spreads across the ground, everything in it hanging still: shards
        -- of ice, motes of frost; a pale flash; then it all shatters outward and is gone.
        function Blasts.TheMomentThatMatters(rig, fx)
            local u, metre = rig.unit, rig.meters
            local s = rig.state
            local head = rig.points.Head
            local bite = if head and s.biteOffset then head.TransformedWorldCFrame:PointToWorldSpace(s.biteOffset) else rig.rootPart.Position
            local params = RaycastParams.new()
            params.FilterDescendantsInstances = { rig.model }
            local hit = workspace:Raycast(bite + Vector3.new(0, 1 * u, 0), Vector3.new(0, -12 * u, 0), params)
            local groundY = if hit then hit.Position.Y else bite.Y - 0.3 * metre
            local centre = Vector3.new(bite.X, groundY, bite.Z)
            local folder = FS.folder(rig)
            local reduced = FS.reduced()

            -- the hexagon: six walls of clear ice standing round it on a line of cold light, spreading out (low and faint, it was lost in the grass: seen in Play)
            local sides = {}
            for k = 0, 5 do
                local a = k / 6 * 2 * math.pi
                local function place(r, y)
                    local at = centre + Vector3.new(math.cos(a) * r, y, math.sin(a) * r)
                    return CFrame.lookAt(at, centre + Vector3.new(0, y, 0))
                end
                local wall = FS.glass(folder, Vector3.new(0.35 * u, 0.9 * u, 0.05 * u), place(0.3 * u, 0.45 * u), 0.45)
                local bar = FS.glass(folder, Vector3.new(0.35 * u, 0.08 * u, 0.12 * u), place(0.3 * u, 0.04 * u), 0.1)
                bar.Material = Enum.Material.Neon
                bar.Color = FS.MAIN
                local grow = TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
                TweenService:Create(wall, grow, { CFrame = place(3 * u, 0.45 * u), Size = Vector3.new(3.1 * u, 0.9 * u, 0.05 * u) }):Play()
                TweenService:Create(bar, grow, { CFrame = place(3 * u, 0.04 * u), Size = Vector3.new(3.2 * u, 0.08 * u, 0.12 * u) }):Play()
                table.insert(sides, { wall, function(r) return place(r, 0.45 * u) end })
                table.insert(sides, { bar, function(r) return place(r, 0.04 * u) end })
            end
            -- inside it, things hang still: shards of ice in the air, and a burst of frost that stops dead
            local count = if reduced then 8 else 18
            local shards = {}
            for k = 1, count do
                local a = math.random() * 2 * math.pi
                local r = (0.4 + 2.2 * math.random()) * u
                local at = centre + Vector3.new(math.cos(a) * r, (0.3 + 1.3 * math.random()) * u, math.sin(a) * r)
                local shard = FS.glass(folder, Vector3.new(0.1, 0.4, 0.1) * u * (0.8 + 0.6 * math.random()), CFrame.new(at) * CFrame.Angles(math.random() * 6, math.random() * 6, math.random() * 6), 1)
                tweenAfter(0.05 + 0.2 * math.random(), shard, TweenInfo.new(0.1), { Transparency = 0.15 })
                table.insert(shards, { shard, at, a })
            end
            if not reduced then
                local motes = Instance.new("ParticleEmitter")
                motes.Texture = SPARKLE
                motes.Enabled = false
                motes.Lifetime = NumberRange.new(1.1, 1.3)
                motes.Speed = NumberRange.new(2 * u, 5 * u)
                motes.SpreadAngle = Vector2.new(180, 60)
                motes.Drag = 25 -- flung out, and stopped dead
                motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.14 * u), NumberSequenceKeypoint.new(0.85, 0.12 * u), NumberSequenceKeypoint.new(1, 0) })
                motes.Color = ColorSequence.new(FS.CORE, FS.MAIN)
                motes.LightEmission = 0.8
                motes.LightInfluence = 0.2
                local holder = fx.neon(Vector3.one * 0.05, CFrame.new(centre + Vector3.new(0, 0.5 * u, 0)), FS.CORE)
                holder.Transparency = 1
                motes.Parent = holder
                motes:Emit(40)
            end
            -- a pale flash, and a cold light
            local flash = fx.neon(Vector3.one * 0.6 * u, CFrame.new(bite), FS.CORE)
            flash.Shape = Enum.PartType.Ball
            flash.Transparency = 0.3
            TweenService:Create(flash, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 2.4 * u, Transparency = 1 }):Play()
            local light = Instance.new("PointLight")
            light.Color = FS.MAIN
            light.Range = 9 * u
            light.Brightness = 2.2
            light.Shadows = false
            light.Parent = flash
            TweenService:Create(light, TweenInfo.new(1.1), { Brightness = 0 }):Play()
            -- held; then it all shatters outward
            task.delay(0.95, function()
                for _, side in sides do
                    local slab, place = side[1], side[2]
                    if slab.Parent then
                        TweenService:Create(slab, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = place(3.8 * u), Transparency = 1 }):Play()
                    end
                end
                for _, sh in shards do
                    local shard, at, a = sh[1], sh[2], sh[3]
                    if shard.Parent then
                        local away = at + Vector3.new(math.cos(a), 0.4, math.sin(a)) * 1.2 * u
                        TweenService:Create(shard, TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                            CFrame = CFrame.new(away) * CFrame.Angles(math.random() * 6, math.random() * 6, math.random() * 6), Transparency = 1,
                        }):Play()
                    end
                end
            end)
        end

        PetRig.Profiles.FrostfangSerpent = {
            Skinned = true,
            Bones = (function()
                local bones = table.clone(FS.BONES)
                table.insert(bones, "Tongue")
                return bones
            end)(),
            Points = { "Head", "Base", "Coil2", "Coil4", "Coil6", "Coil8" },
            GlowColors = {
                c8f2ff = Color3.fromRGB(200, 242, 255), -- its crystal fangs
                ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
            },
            SeeThrough = { Ice = 0.35 }, -- the blades round its hood: clear ice
            Effects = {
                Blast = "TheMomentThatMatters",
                Pulse = "Fangs",
                NovaLight = 2,
            },
            Colors = {
                Gold = FS.MAIN,
                Amber = FS.DEEP,
                Orange = FS.ICE,
                Sun = FS.CORE,
                Ivory = Color3.fromRGB(232, 246, 255),
            },
            Animate = animateFrostfangSerpent,
        }
    end
end
