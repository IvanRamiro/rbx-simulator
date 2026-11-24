-- NinefoldSpiritSerpent: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Debris, Players, RunService, TweenService, pose, smoothstep, Blasts, dropToGround, guardOwnerCharacter = K.PetRig, K.Debris, K.Players, K.RunService, K.TweenService, K.pose, K.smoothstep, K.Blasts, K.dropToGround, K.guardOwnerCharacter


    do
        -- The Ninefold Spirit Serpent (skinned): Qi you can see moving. A slender pearl-white serpent, loosely coiled on the ground, its front rising in a
        -- slow, swan-like S; nine rings of jade light ride its risen body, one for each meridian, each with four acupoint beads; a serene head with calm
        -- jade eyes under soft lids, a jade gem on its brow, and a halo of five jade fins behind it. Everything it does is unhurried. It rests coiled, its
        -- column swaying a little as it breathes, its fins breathing open and closed; its gaze settles on you and stays; it blinks slowly. Every several
        -- seconds light climbs its rings, the first to the ninth, each brightening in turn, and arrives at its brow, where the gem pulses: Qi climbing a
        -- cultivator's channels. Now and then it bows its head to you. Still a long while, it draws itself up tall and meditates, eyes half closed, the
        -- light climbing more often. It never uncoils: to go anywhere it leans its column forward like a swan's neck, fins folded, and glides on its coil,
        -- a ripple running round it; on the wing it hovers, coiled. Its special, Nine Gates, One Breath: it rises tall and still, fins spread; light
        -- flares up its nine rings in turn to the gem on its brow, which blazes; then the Qi leaves it as a ribbon of jade light that circles its owner
        -- once, up their back and down their front as a cultivator's Qi turns, and flows home into its tail, every ring flaring as it returns
        -- (Blasts.NineGatesOneBreath).
        local NS = {
            FAR = 110, -- studs from the camera past which nobody can see it fidget: its bones rest
            SOLE = 0.4638, -- metres from the middle of its box (the RootPart's cube counted, as stored in Studio) down to its coil (ninefold_serpent.py)
            HOVER_UP = 0.25, -- metres it rises on the wing
            RIPPLE = 0.015, -- radians: each coil bone's sway as the ripple runs round its coil, rising to RIPPLE_TAIL at its tail's tip (ninefold_serpent.py:
            RIPPLE_TAIL = 0.04, -- its turns and rings lie close, so more and they swayed into each other; checked at eight phases and along the slerps)
            RIPPLE_STEP = 0.9,
            COILS = 12,
            HEAD_AT = Vector3.new(0, 0.79, -0.165), -- its Head bone's head, metres in its own axes
            GEM_AT = Vector3.new(0, 0.834, -0.234), -- the gem on its brow
            LID_HINGE = { L = Vector3.new(0.7578, 0, -0.6525), R = Vector3.new(0.7578, 0, 0.6525) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(38), -- (the two add past the 54 degrees between its lids' edges)
            BLINK_LOWER = math.rad(18),
            -- its stances, fitted in Blender (ninefold_serpent.py's pose_tables: its spine laid along a curve, carried along it without twisting) and checked
            -- there in each and along every slerp the game makes (skin against itself, rings against skin, fins against its neck, ground; edge stretch)
            GLIDE = {
                Base = { -0.0047, 0, -0.0017 }, Coil1 = { 0.0047, 0, 0.0017 }, Head = { 0.3136, -0.129, 0.5014 }, Up1 = { 0.004, 0.0024, 0.004 },
                Up2 = { 0.0511, 0.0094, -0.016 }, Up3 = { -0.4086, 0.1183, 0.0866 }, Up4 = { -0.3234, 0.1508, 0.0407 }, Up5 = { -0.1478, 0.1221, -0.0858 },
                Up6 = { 0.1383, 0.1223, -0.3465 }, Up7 = { 0.2954, 0.077, 0.1408 }, Up8 = { 0.1713, -0.149, -0.1181 },
            },
            RISE = { -- drawn up tall and straight, head lifted: its meditation, and its special
                Base = { -0.0047, 0, -0.0017 }, Coil1 = { 0.0047, 0, 0.0017 }, Head = { -0.1703, -0.1948, 0.2186 }, Up1 = { 0.0039, 0.0018, 0.004 },
                Up2 = { -0.0051, -0.0088, -0.011 }, Up3 = { 0.0836, 0.0106, 0.0927 }, Up4 = { -0.0771, 0.022, 0.0711 }, Up5 = { -0.2174, 0.1328, -0.0463 },
                Up6 = { -0.0094, 0.1053, -0.2165 }, Up7 = { 0.5078, 0.07, 0.0292 }, Up8 = { 0.2391, -0.0148, -0.0375 },
            },
            LOOK = { Up6 = { 0, 0.2, 0 }, Up7 = { 0, 0.25, 0 }, Up8 = { 0, 0.25, 0 }, Head = { 0, 0.3, 0.06 } }, -- its gaze turned a full radian (scaled)
            BOW = { Up7 = { -0.08, 0, 0 }, Up8 = { -0.14, 0, 0 }, Head = { -0.28, 0, 0 } },
            -- its five fins (Fin1 by its left cheek): spread wide and raised; folded (gliding: folded further, they lay into its neck)
            FINS_OPEN = {
                Fin1 = { 0.06, 0.2941, -0.3089 }, Fin2 = { -0.1939, 0.2304, -0.1275 }, Fin3 = { -0.3, 0, 0 }, Fin4 = { -0.1939, -0.2304, 0.1275 },
                Fin5 = { 0.06, -0.2941, 0.3089 },
            },
            FINS_FOLD = {
                Fin1 = { 0.0082, -0.0493, 0.0602 }, Fin2 = { 0.0382, -0.0323, 0.0306 }, Fin3 = { 0.05, 0, 0 }, Fin4 = { 0.0382, 0.0323, -0.0306 },
                Fin5 = { 0.0082, 0.0493, -0.0602 },
            },
            BONES = { "Base", "Up1", "Up2", "Up3", "Up4", "Up5", "Up6", "Up7", "Up8", "Head", "EyeL", "EyeR" },
            RINGS = 9,
            CLIMB_STEP = 0.22, -- seconds from one ring lighting to the next as the light climbs
            RING = Color3.fromRGB(28, 226, 160), -- its rings' Neon at rest (deeper than their 35f5b8 paint: Neon pales a light mint to white)
            RING_HOT = Color3.fromRGB(120, 255, 210),
            RING_LOW = Color3.fromRGB(14, 120, 90), -- emptied, while its Qi is out circling its owner
            CORE = Color3.fromRGB(225, 255, 244),
            MOTES = 9, -- the ribbon's motes, one for each meridian (3 with reduced effects)
            CIRCUIT = 1.35, -- seconds for the ribbon's head to go out, round its owner and home
        }
        for k = 1, NS.COILS do
            table.insert(NS.BONES, "Coil" .. k)
        end
        for k = 1, 5 do
            table.insert(NS.BONES, "Fin" .. k)
        end

        function NS.cf(a, u)
            if not a then
                return CFrame.identity
            end
            local move = if a[4] then CFrame.new(a[4] * u, a[5] * u, a[6] * u) else CFrame.identity
            return move * CFrame.Angles(a[1], a[2], a[3])
        end

        function NS.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        -- The ripple round its coil: each coil bone's own turn the difference from the one before, so each lies at most its amplitude off its rest.
        function NS.ripple(phase, k)
            local function world(j)
                if j == 0 then
                    return 0
                end
                local amp = NS.RIPPLE + (NS.RIPPLE_TAIL - NS.RIPPLE) * smoothstep(NS.COILS - 3.5, NS.COILS, j)
                return amp * math.sin(phase - NS.RIPPLE_STEP * j)
            end
            return world(k) - world(k - 1)
        end

        -- How bright the light is in ring k (1..9) as it climbs: up fast as it arrives, fading more slowly behind it; `at` is when ring 1 lit.
        function NS.climbing(t, at, k, step)
            local x = t - (at + (k - 1) * step)
            if x < -0.12 then
                return 0
            end
            return if x < 0 then smoothstep(-0.12, 0, x) else 1 - smoothstep(0, 0.5, x)
        end

        -- Once, at rest: where its brow gem sits on its Head bone (its special's ribbon starts there), and a soft jade light at its head.
        function NS.init(rig, s)
            s.inited = true
            local head = rig.points.Head
            if head then
                local headCf = head.TransformedWorldCFrame
                local world = headCf.Position + rig.rootPart.CFrame:VectorToWorldSpace((NS.GEM_AT - NS.HEAD_AT) * rig.meters)
                s.gemOffset = headCf:PointToObjectSpace(world)
                local at = Instance.new("Attachment")
                at.Name = "JadeLight"
                at.Parent = head
                local light = Instance.new("PointLight")
                light.Name = "PulseLight"
                light.Color = Color3.fromRGB(150, 240, 210) -- (the rings' own jade, at 11.7 studs, washed the owner and the ground cyan: seen in Play)
                light.Range = 1.6 * rig.unit
                light.Brightness = 0.5
                light.Shadows = false
                light.Parent = at
                rig.light = light
            end
        end

        local function animateNinefoldSpiritSerpent(rig, s, moving, fly, nova)
            if not s.inited then
                NS.init(rig, s) -- at rest, before any pose
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > NS.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local reduced = NS.reduced()

            -- the special, Nine Gates, One Breath: it settles if it is flying and rises tall, fins spread (to 0.3); light flares up its rings, one by one,
            -- to its brow (0.08 to 0.42, the burst: the gem blazes and the Qi leaves it); its rings dim while the ribbon circles its owner, its eyes half
            -- closed; the Qi comes home into its tail (about 0.93) and every ring flares; it settles by 0.98
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local active = if rig.nova then 1 else 0
            s.air = (s.air or 0) + (fly * (1 - active) - (s.air or 0)) * math.min(1, dt * 2.5)
            local air = s.air
            local rise = smoothstep(0.02, 0.3, progress) * (1 - smoothstep(0.84, 0.98, progress)) * active
            local out = smoothstep(0.42, 0.5, progress) * (1 - smoothstep(0.86, 0.93, progress)) * active -- its Qi is out of it
            local home = (smoothstep(0.88, 0.93, progress) * (1 - smoothstep(0.93, 1, progress))) * active

            local drop = dropToGround(rig, s, t, u, air, NS.SOLE)

            -- gliding: it leans its column forward, fins folded, a ripple running round its coil
            local gliding = moving * (1 - smoothstep(0.05, 0.3, air)) * (1 - active)
            s.wave = (s.wave or 0) + dt * (1.6 + 2.6 * moving) * gliding

            -- still a long while, it draws itself up and meditates; now and then it bows its head to you
            local still = (1 - moving) * (1 - smoothstep(0.05, 0.3, air)) * (1 - active)
            s.still = if still > 0.95 then (s.still or 0) + dt else 0
            local wantMeditate = if s.still > 14 then 1 else 0
            s.meditate = (s.meditate or 0) + (wantMeditate - (s.meditate or 0)) * math.min(1, dt * (if wantMeditate > (s.meditate or 0) then 0.4 else 3))
            local meditate = smoothstep(0, 1, s.meditate) * still
            s.nextBow = s.nextBow or t + 8
            if t >= s.nextBow then
                s.nextBow = t + 10 + math.random() * 8
                if still > 0.9 and meditate < 0.1 then
                    s.bowAt = t
                end
            end
            local bowing = if s.bowAt then (t - s.bowAt) / 2.6 else 1
            local bow = (if bowing < 1 then math.sin(math.pi * smoothstep(0, 1, bowing)) else 0) * still * (1 - meditate)

            -- its gaze settles on you and stays, now and then wandering; its column sways a little as it breathes
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 3 + math.random() * 5
                s.atYou = math.random() < 0.75
                s.gazeYaw = (math.random() - 0.5) * 1.2
            end
            local calm = (1 - 0.6 * gliding) * (1 - rise) * (1 - 0.7 * meditate)
            local wantYaw = math.clamp(if s.atYou then math.atan2(-toYou.X, -toYou.Z) else s.gazeYaw, -1, 1) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.4, -0.1, 0.2) else 0) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 1.2) -- (slow: it turns as if it has all the time in the world)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 1.2)
            local breath = math.sin(t * (if meditate > 0.5 then 0.6 else 0.9))
            local sway = math.sin(t * 0.55)

            -- its fins: breathing open and closed with its breath; folded as it glides; spread wide in its special and as it meditates
            local open = math.max(0.12 + 0.12 * breath, 0.6 * meditate, rise)
            local fold = gliding * (1 - rise)

            for _, name in NS.BONES do
                local cf = CFrame.identity
                local k = tonumber(string.match(name, "^Coil(%d+)$"))
                if string.sub(name, 1, 3) == "Fin" then
                    cf = CFrame.identity:Lerp(NS.cf(NS.FINS_OPEN[name], u), open):Lerp(NS.cf(NS.FINS_FOLD[name], u), fold)
                elseif name == "EyeL" or name == "EyeR" then
                    cf = CFrame.Angles(0.5 * s.pitch, 0.18 * s.yaw, 0)
                else
                    cf = cf:Lerp(NS.cf(NS.GLIDE[name], u), gliding)
                    if k then
                        cf *= CFrame.Angles(0, NS.ripple(s.wave, k) * gliding, 0)
                    end
                    cf = cf:Lerp(NS.cf(NS.RISE[name], u), math.max(rise, 0.55 * meditate))
                    local bowTo = NS.BOW[name]
                    if bowTo then
                        cf *= CFrame.Angles(bowTo[1] * bow, 0, 0)
                    end
                    local look = NS.LOOK[name]
                    if look then
                        cf *= CFrame.Angles(0, look[2] * s.yaw, look[3] * s.yaw)
                    end
                    if name == "Up3" or name == "Up4" then
                        cf *= CFrame.Angles(0.012 * breath, 0.03 * sway * calm, 0)
                    elseif name == "Head" then
                        cf *= CFrame.Angles(s.pitch - 0.02 * breath, 0, 0)
                    end
                end
                if name == "Base" then
                    cf = CFrame.new(0, NS.HOVER_UP * air * u - drop, 0) * cf
                end
                pose(m[name], cf)
            end

            -- its eyes: slow blinks; half closed as it meditates and while its Qi is out circling its owner
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.5
                if a >= 1 then
                    s.nextBlink = t + 4 + math.random() * 5
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local close = math.max(blink, 0.7 * meditate, 0.75 * out)
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(NS.LID_HINGE[side], -NS.BLINK_UPPER * close))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(NS.LID_HINGE[side], NS.BLINK_LOWER * close))
            end

            -- its signature: every several seconds, light climbs its nine rings, the first to the ninth, and arrives at its brow, where the gem pulses
            -- (more often as it meditates; not with reduced effects, where its rings only breathe)
            s.nextClimb = s.nextClimb or t + 3
            if t >= s.nextClimb then
                s.nextClimb = t + (if meditate > 0.5 then 4.5 else 7) + math.random() * 3
                if not reduced and active == 0 and gliding < 0.5 then
                    s.climbAt = t
                end
            end
            local glowBase = 0.18 + 0.08 * breath
            local gemLight = glowBase
            for k = 1, NS.RINGS do
                local w = glowBase
                if s.climbAt then
                    w = math.max(w, NS.climbing(t, s.climbAt, k, NS.CLIMB_STEP))
                end
                if active == 1 then
                    w = math.max(w, NS.climbing(t, rig.nova.start + 0.08 * PetRig.NOVA_TIME, k, 0.035 * PetRig.NOVA_TIME) * (1 - out)) -- flaring up it
                    w = math.max(w * (1 - out), home)
                end
                local ring = rig.parts["Ring" .. k]
                if ring then
                    ring.Color = (if out > 0 then NS.RING:Lerp(NS.RING_LOW, out) else NS.RING):Lerp(NS.RING_HOT, w)
                end
            end
            if s.climbAt then
                gemLight = math.max(gemLight, NS.climbing(t, s.climbAt + NS.RINGS * NS.CLIMB_STEP, 1, 1) * 1)
            end
            if active == 1 then
                gemLight = math.max(gemLight, smoothstep(0.3, 0.42, progress) * (1 - smoothstep(0.5, 0.7, progress)), home)
            end
            local gem = rig.parts.Gem
            if gem then
                gem.Color = NS.RING:Lerp(NS.RING_HOT, gemLight):Lerp(NS.CORE, 0.6 * math.max(0, gemLight - 0.6))
            end
        end

        -- Its Qi blazes at its brow (animateNinefoldSpiritSerpent) and leaves it: a ribbon of jade light, nine motes long, runs from its brow to its owner,
        -- circles them once, up their back and over their head and down their front, as a cultivator's Qi turns, and flows home into the tip of its tail.
        -- (Its owner, else whoever stands nearest it; with nobody near, the ribbon circles the serpent itself.)
        function Blasts.NineGatesOneBreath(rig, fx)
            local u, metre = rig.unit, rig.meters
            local s = rig.state
            local reduced = NS.reduced()
            local folder = Instance.new("Folder")
            folder.Name = "PetSpecial"
            folder.Parent = rig.model.Parent or workspace
            Debris:AddItem(folder, NS.CIRCUIT + 1.2)
            local character = guardOwnerCharacter(rig)
            local ownerRoot = character and character:FindFirstChild("HumanoidRootPart")
            local humanoid = character and character:FindFirstChildOfClass("Humanoid")

            local function gem()
                local head = rig.points.Head
                return if head and s.gemOffset then head.TransformedWorldCFrame:PointToWorldSpace(s.gemOffset) else rig.rootPart.Position + Vector3.yAxis * metre
            end
            local function tail()
                local tip = rig.points.Coil12
                return if tip then tip.TransformedWorldCFrame.Position + Vector3.yAxis * 0.03 * metre else rig.rootPart.Position
            end
            -- the loop round its owner (or round itself), from where they stand now: its centre, its upright and its back-to-front axis, its two radii
            local function loop()
                if ownerRoot and ownerRoot.Parent then
                    local standing = (if humanoid then humanoid.HipHeight else 2) + ownerRoot.Size.Y / 2
                    local at = ownerRoot.Position
                    local bottom, top = at.Y - standing + 0.4, at.Y + ownerRoot.Size.Y / 2 + 2.2
                    local back = -(ownerRoot.CFrame.LookVector * Vector3.new(1, 0, 1)).Unit
                    return Vector3.new(at.X, (bottom + top) / 2, at.Z), back, (top - bottom) / 2, 1.4
                end
                local root = rig.rootPart
                local back = -(root.CFrame.LookVector * Vector3.new(1, 0, 1)).Unit
                return root.Position + Vector3.yAxis * 0.1 * metre, back, 0.62 * metre, 0.5 * metre
            end
            local START = 0.45 -- where on the loop the ribbon joins it: low on its owner's back (0 is the loop's foot)
            local function onLoop(theta)
                local centre, back, a, b = loop()
                return centre - Vector3.yAxis * a * math.cos(theta) + back * b * math.sin(theta)
            end
            local function arc(from, to, lift, x)
                local mid = (from + to) / 2 + Vector3.yAxis * lift
                return from:Lerp(mid, x):Lerp(mid:Lerp(to, x), x)
            end
            -- where the ribbon's head is, x from 0 (leaving its brow) to 1 (home in its tail): out (a quarter), round (half), home (a quarter)
            local function path(x)
                if x < 0.25 then
                    return arc(gem(), onLoop(START), 1.2 * u, smoothstep(0, 1, x / 0.25))
                elseif x < 0.75 then
                    return onLoop(START + 2 * math.pi * smoothstep(0, 1, (x - 0.25) / 0.5))
                end
                return arc(onLoop(START), tail(), 1 * u, smoothstep(0, 1, (x - 0.75) / 0.25))
            end

            local count = if reduced then 3 else NS.MOTES
            local motes = {}
            for k = 1, count do
                local size = (0.11 - 0.006 * (k - 1)) * u
                local mote = fx.neon(Vector3.one * size, CFrame.new(gem()), if k == 1 then NS.CORE else NS.RING_HOT:Lerp(NS.RING, (k - 1) / count))
                mote.Shape = Enum.PartType.Ball
                mote.Transparency = 1
                mote.Parent = folder
                if not reduced then
                    local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
                    a0.Position, a1.Position = Vector3.new(0, size * 0.35, 0), Vector3.new(0, -size * 0.35, 0)
                    a0.Parent, a1.Parent = mote, mote
                    local streak = Instance.new("Trail")
                    streak.Attachment0, streak.Attachment1 = a0, a1
                    streak.Lifetime = 0.28
                    streak.FaceCamera = true
                    streak.LightEmission = 1
                    streak.LightInfluence = 0
                    streak.Color = ColorSequence.new(NS.RING_HOT, NS.RING)
                    streak.Transparency = NumberSequence.new(0.2, 1)
                    streak.WidthScale = NumberSequence.new(1, 0.1)
                    streak.Parent = mote
                end
                table.insert(motes, { part = mote, delay = 0.05 * (k - 1) })
            end
            if not reduced then
                local light = Instance.new("PointLight")
                light.Color = NS.RING
                light.Range = 7 * u
                light.Brightness = 1.2
                light.Shadows = false
                light.Parent = motes[1].part
            end
            -- the gem's flash as the Qi leaves it
            local flash = fx.neon(Vector3.one * 0.12 * u, CFrame.new(gem()), NS.CORE)
            flash.Shape = Enum.PartType.Ball
            flash.Transparency = 0.2
            flash.Parent = folder
            TweenService:Create(flash, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 0.55 * u, Transparency = 1 }):Play()

            local began = os.clock()
            local conn
            conn = RunService.Heartbeat:Connect(function()
                local now = os.clock() - began
                local live = false
                for _, mote in motes do
                    local x = (now - mote.delay) / NS.CIRCUIT
                    if mote.part.Parent and x < 1 then
                        live = true
                        if x >= 0 then
                            mote.part.Transparency = 0.05 + 0.5 * smoothstep(0.92, 1, x)
                            mote.part.CFrame = CFrame.new(path(x))
                        end
                    elseif mote.part.Parent and mote.part.Transparency < 1 then
                        mote.part.Transparency = 1
                    end
                end
                if not live then
                    conn:Disconnect()
                end
            end)
            task.delay(NS.CIRCUIT + 1, function()
                if conn.Connected then
                    conn:Disconnect()
                end
            end)
        end

        local bones = table.clone(NS.BONES)
        for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
            table.insert(bones, name)
        end
        PetRig.Profiles.NinefoldSpiritSerpent = {
            LightScale = 0.4, -- its head light, soft: a glow round its head, not a lamp on its owner (seen in Play)
            Skinned = true,
            Bones = bones,
            Points = { "Head", "Base", "Coil12" },
            GlowColors = {
                ["35f5b8"] = NS.RING, -- its nine rings and the gem on its brow (each lit on its own in animateNinefoldSpiritSerpent)
            },
            Effects = {
                Blast = "NineGatesOneBreath",
                NovaLight = 1.6,
            },
            Colors = {
                Gold = NS.RING,
                Amber = Color3.fromRGB(14, 120, 90),
                Orange = NS.RING_HOT,
                Sun = NS.CORE,
                Ivory = Color3.fromRGB(240, 244, 246),
            },
            Animate = animateNinefoldSpiritSerpent,
        }
    end
end
