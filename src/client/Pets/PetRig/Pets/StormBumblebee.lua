-- StormBumblebee: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Players, TweenService, SPARKLE, tweenAfter, pose, smoothstep, Blasts = K.PetRig, K.Players, K.TweenService, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts


    do
        -- The Storm Bumblebee (skinned): a fat, fuzzy bumblebee charged with static. It hovers, bobbing, its small smoky wings a blur of a figure-eight
        -- beat; little arcs of static crackle across its fur, a spark glows at the tip of each feeler, and in the baskets of its hind legs it carries
        -- balls of stored lightning. It turns its head to look at you, twitches a feeler, pumps its abdomen as it breathes. Now and then it zips off to one
        -- side and back, throws a barrel roll for the fun of it, or shivers, every hair crackling at once. Moving, it leans into its flight, legs trailing.
        -- Its special, A Lesson Learned Once: it rises, buzzing harder, fur crackling and glowing; curls its abdomen under, its sting of light sliding out;
        -- and dives, driving the sting into the ground (at 0.42: Blasts.ALessonLearnedOnce): a crack of lightning, arcs spreading out across the ground.
        -- Then it pops back up and shakes itself off.
        local SB = {
            FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
            -- its stances, each checked in Blender (storm_bumblebee.py's pose_tables: wings against body, legs against abdomen and each other, feelers,
            -- abdomen against thorax) and along every slerp between them: turns x, y, z; then a move in metres
            ZIP = {
                Abd1 = { 0.06, 0, 0 }, AntL1 = { -0.25, 0, 0 }, AntR1 = { -0.25, 0, 0 }, Body = { -0.32, 0, 0 }, Head = { 0.15, 0, 0 },
                LegL1 = { -0.2, 0, -0.12 }, LegL2 = { -0.25, 0, -0.12 }, LegL3 = { -0.28, 0, -0.22 }, LegR1 = { -0.2, 0, 0.12 }, LegR2 = { -0.25, 0, 0.12 },
                LegR3 = { -0.28, 0, 0.22 }, ShinL1 = { -0.15, 0, 0 }, ShinL2 = { -0.15, 0, 0 }, ShinL3 = { -0.12, 0, 0 }, ShinR1 = { -0.15, 0, 0 },
                ShinR2 = { -0.15, 0, 0 }, ShinR3 = { -0.12, 0, 0 },
            },
            CHARGE = {
                Abd1 = { -0.12, 0, 0 }, Abd2 = { -0.08, 0, 0 }, AntL1 = { 0.25, 0, -0.2 }, AntL2 = { 0.2, 0, 0 }, AntR1 = { 0.25, 0, 0.2 }, AntR2 = { 0.2, 0, 0 },
                Body = { 0.3, 0, 0 }, Head = { -0.1, 0, 0 },
            },
            STING = { -- nose up, abdomen curled under, its sting slid out and aimed straight down, its legs splayed out of the way
                Abd1 = { 0.2, 0, 0 }, Abd2 = { 0.52, 0, 0 }, Body = { 0.2, 0, 0 }, Head = { -0.12, 0, 0 }, LegL1 = { 0.5, 0, -0.25 }, LegL2 = { 0.3, 0, -0.45 },
                LegL3 = { 0.55, 0, -0.5 }, LegR1 = { 0.5, 0, 0.25 }, LegR2 = { 0.3, 0, 0.45 }, LegR3 = { 0.55, 0, 0.5 }, ShinL1 = { 0.4, 0, 0 },
                ShinL3 = { 0.15, 0, 0 }, ShinR1 = { 0.4, 0, 0 }, ShinR3 = { 0.15, 0, 0 }, Sting = { 0, 0, 0, 0, -0.0258, 0.0452 },
            },
            -- LOOK (checked): Head { 0.05, 0.3, 0.08 }, AntL1 { 0, 0.2, 0 }, AntR1 { 0, -0.2, 0 }: built from its gaze in animateStormBumblebee
            TWITCH = { AntL1 = { 0.2, 0.1, -0.2 }, AntL2 = { 0.3, 0, 0 } },
            -- its wings' figure-eight beat, inside the box checked at its corners: roll (up -, down +) and sweep (forward -, back +), left wing
            ROLL = { -0.6, 0.24 },
            SWEEP = { -0.4, 0.14 },
            BEAT = 26, -- beats a second: faster than the frames, it strobes into a blur
            RISE = 0.25, -- metres it climbs while it charges
            TIP_BELOW = 0.2579, -- metres from the middle of its box (the game's: its RootPart, at its origin, counts) down to its sting's tip, stinging
            STING_AT = Vector3.new(0, 0.3767, 0.3981), -- its Sting bone, metres in its own axes
            TIP_AT = Vector3.new(0, 0.345, 0.4537), -- its sting's tip, sheathed
            BONES = {
                "Body", "Head", "Abd1", "Abd2", "Sting", "AntL1", "AntL2", "AntR1", "AntR2", "WingL", "WingR",
                "LegL1", "ShinL1", "LegL2", "ShinL2", "LegL3", "ShinL3", "LegR1", "ShinR1", "LegR2", "ShinR2", "LegR3", "ShinR3",
            },
            CORE = Color3.fromRGB(255, 250, 200),
            MAIN = Color3.fromRGB(255, 220, 80),
            DEEP = Color3.fromRGB(170, 110, 255),
            ARC = Color3.fromRGB(238, 228, 255),
            TIP = Color3.fromRGB(255, 242, 160),
        }

        function SB.cf(a, u)
            if not a then
                return CFrame.identity
            end
            local move = if a[4] then CFrame.new(a[4] * u, a[5] * u, a[6] * u) else CFrame.identity
            return move * CFrame.Angles(a[1], a[2], a[3])
        end

        function SB.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        -- Once, at rest: where its sting's tip is, carried on its Sting bone; its light; the static sparks off its fur.
        function SB.init(rig, s)
            s.inited = true
            local sting = rig.points.Sting
            if sting then
                local cf = sting.TransformedWorldCFrame
                local world = cf.Position + rig.rootPart.CFrame:VectorToWorldSpace((SB.TIP_AT - SB.STING_AT) * rig.meters)
                s.tipOffset = cf:PointToObjectSpace(world)
            end
            local body = rig.points.Body
            if body then
                local at = Instance.new("Attachment")
                at.Name = "Static"
                at.Parent = body
                local light = Instance.new("PointLight")
                light.Name = "PulseLight"
                light.Color = SB.MAIN
                light.Range = 4 * rig.unit
                light.Brightness = 1
                light.Shadows = false
                light.Parent = at
                rig.light = light
                local sparks = Instance.new("ParticleEmitter")
                sparks.Name = "StaticSparks"
                sparks.Texture = SPARKLE
                sparks.Rate = 0
                sparks.Lifetime = NumberRange.new(0.15, 0.35)
                sparks.Speed = NumberRange.new(0.6 * rig.unit, 1.6 * rig.unit)
                sparks.SpreadAngle = Vector2.new(180, 180)
                sparks.Size = NumberSequence.new(0.07 * rig.unit, 0)
                sparks.Color = ColorSequence.new(SB.CORE, SB.ARC)
                sparks.LightEmission = 1
                sparks.LightInfluence = 0
                sparks.Parent = at
                s.sparks = sparks
            end
        end

        -- The ground under it, looked up now and then (a player walking under it: keep what it had).
        function SB.groundBelow(rig, s, t)
            s.nextGround = s.nextGround or 0
            if t >= s.nextGround then
                s.nextGround = t + 0.2
                local params = RaycastParams.new()
                params.FilterDescendantsInstances = { rig.model }
                local from = rig.rootPart.Position
                local hit = workspace:Raycast(from, Vector3.new(0, -14 * rig.unit, 0), params)
                local onCharacter = hit and hit.Instance.Parent and hit.Instance.Parent:FindFirstChildOfClass("Humanoid")
                if not onCharacter then
                    s.height = if hit then (from.Y - hit.Position.Y) / rig.meters else nil -- metres from the middle of its box to the ground
                end
            end
            return s.height
        end

        local function animateStormBumblebee(rig, s, moving, fly, nova)
            if not s.inited then
                SB.init(rig, s) -- at rest, before any pose
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > SB.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local reduced = SB.reduced()

            -- the special, A Lesson Learned Once: it rises, charging (to 0.28); curls, its sting out (0.28 to 0.36); dives, the sting into the ground
            -- (0.36 to 0.42: Blasts.ALessonLearnedOnce); holds it there; pops back up (0.58 to 0.75) and shakes itself off (to 0.92)
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local active = if rig.nova then 1 else 0
            if active == 1 and not s.diving then
                s.diving = rig.nova.start
                local height = SB.groundBelow(rig, s, t)
                -- the dive: down until its sting's tip, curled, meets the ground (its rise has gone by then; counted in, the sting went a stud into
                -- the ground: seen in Play); no ground found: a short dip
                s.dive = if height then math.clamp(height - SB.TIP_BELOW + 0.015, 0, 2.2) else 0.3
            elseif active == 0 then
                s.diving = nil
            end
            local charge = smoothstep(0.02, 0.28, progress) * (1 - smoothstep(0.3, 0.38, progress)) * active
            local curl = smoothstep(0.28, 0.36, progress) * (1 - smoothstep(0.58, 0.72, progress)) * active
            local rise = smoothstep(0.02, 0.28, progress) * (1 - smoothstep(0.36, 0.42, progress)) * active
            local dive = smoothstep(0.36, 0.42, progress) * (1 - smoothstep(0.58, 0.75, progress)) * active
            local shake = if active == 1 and progress > 0.72 and progress < 0.92 then math.sin(math.pi * (progress - 0.72) / 0.2) else 0
            local stuck = if active == 1 and progress > 0.42 and progress < 0.58 then 1 else 0

            -- idle business, when it is still: a zip off to one side and back, a barrel roll, or a shiver of static
            local still = (1 - moving) * (1 - active)
            s.nextIdle = s.nextIdle or t + 5
            if t >= s.nextIdle and still > 0.9 then
                local r = math.random()
                s.idleAt, s.idleKind = t, if r < 0.45 then "zip" elseif r < 0.7 then "roll" else "shiver"
                s.zipSide = if math.random() < 0.5 then 1 else -1
                s.nextIdle = t + 6 + math.random() * 7
                if s.idleKind == "shiver" and s.sparks and not reduced then
                    s.sparks:Emit(14)
                end
            end
            local idleLen = if s.idleKind == "roll" then 0.9 elseif s.idleKind == "zip" then 1.1 else 0.8
            local idle = if s.idleAt then (t - s.idleAt) / idleLen else 1
            local live = if idle < 1 then still else 0
            local zip = if s.idleKind == "zip" and idle < 1 then math.sin(math.pi * idle) * live else 0
            local roll = if s.idleKind == "roll" and idle < 1 then smoothstep(0, 1, idle) * live else 0
            local shiver = if s.idleKind == "shiver" and idle < 1 then math.sin(math.pi * idle) * live else 0

            -- its gaze: now on you, now about; a feeler twitch now and then
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2 + math.random() * 3
                s.atYou = math.random() < 0.55
                s.gazeYaw = (math.random() - 0.5) * 1.6
                s.twitchAt, s.twitchSide = t, if math.random() < 0.5 then "L" else "R"
            end
            local wantYaw = math.clamp(if s.atYou then math.atan2(-toYou.X, -toYou.Z) else s.gazeYaw, -1, 1) * (1 - active) * (1 - zip)
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 3)
            local twitch = if s.twitchAt then math.max(0, math.sin(math.pi * math.clamp((t - s.twitchAt) / 0.35, 0, 1))) else 0

            -- the buzz: faster as it charges; the hover bob; its abdomen pumping as it breathes
            s.phase = (s.phase or 0) + dt * SB.BEAT * 2 * math.pi * (1 + 0.5 * charge)
            local bob = math.sin(t * 2.4) * 0.018 * (1 - active)
            local breath = math.sin(t * 3.1)
            local lean = math.max(moving, fly * 0.6) * (1 - active)
            local look = math.abs(s.yaw)

            for _, name in SB.BONES do
                local cf = CFrame.identity:Lerp(SB.cf(SB.ZIP[name], u), math.max(lean, zip * 0.7))
                if active == 1 then
                    cf = cf:Lerp(SB.cf(SB.CHARGE[name], u), charge):Lerp(SB.cf(SB.STING[name], u), curl)
                end
                -- its gaze (LOOK, checked turned to its left; to its right, its mirror) and a feeler's twitch (TWITCH, its left; mirrored for its right)
                local side = string.match(name, "^Ant([LR])%d$")
                if name == "Head" then
                    cf *= CFrame.Angles(0.05 * look, 0.3 * s.yaw, 0.08 * s.yaw)
                elseif side then
                    local sign = if side == "L" then 1 else -1
                    cf *= CFrame.Angles(0, 0.2 * sign * look * (if string.sub(name, -1) == "1" then 1 else 0), 0)
                    if side == s.twitchSide then
                        local tw = SB.TWITCH["AntL" .. string.sub(name, -1)]
                        cf *= CFrame.Angles(tw[1] * twitch, tw[2] * sign * twitch, tw[3] * sign * twitch)
                    end
                end
                if name == "Abd1" then
                    cf *= CFrame.Angles(0.025 * breath, 0, 0)
                elseif name == "WingL" or name == "WingR" then
                    local sign = if name == "WingL" then 1 else -1
                    local rollMid, rollAmp = (SB.ROLL[1] + SB.ROLL[2]) / 2, (SB.ROLL[2] - SB.ROLL[1]) / 2
                    local sweepMid, sweepAmp = (SB.SWEEP[1] + SB.SWEEP[2]) / 2, (SB.SWEEP[2] - SB.SWEEP[1]) / 2
                    cf = CFrame.Angles(0, sign * (sweepMid + sweepAmp * math.cos(s.phase)), sign * (rollMid + rollAmp * math.sin(s.phase)))
                elseif name == "Body" then
                    -- over the stance: the bob; the zip off to one side; the roll; the shiver; the rise, the dive and the shake
                    local jitter = (shiver + 0.4 * charge + 0.6 * shake) * 0.06
                    cf = CFrame.new((s.zipSide or 1) * 0.38 * zip * u, (bob + SB.RISE * rise - (s.dive or 0) * dive + 0.08 * math.sin(math.pi * roll)) * u, 0)
                        * cf
                        * CFrame.Angles(jitter * math.sin(t * 61), jitter * math.sin(t * 53 + 1), (s.zipSide or 1) * -0.3 * zip + 2 * math.pi * roll + jitter * math.sin(t * 47 + 2))
                end
                pose(m[name], cf)
            end

            -- the static: little arcs flickering across its fur, more as it charges; the sparks off it
            s.nextFlicker = s.nextFlicker or 0
            if t >= s.nextFlicker then
                s.nextFlicker = t + 0.06 + math.random() * 0.08
                local chance = 0.12 + 0.75 * math.max(charge, shiver, shake) + 0.5 * stuck
                for _, key in { "CrackleA", "CrackleB" } do
                    local part = rig.parts[key]
                    if part then
                        part.Transparency = if math.random() < chance then 0 else 1
                    end
                end
            end
            if s.sparks then
                s.sparks.Rate = if reduced then 0 else 1.5 + 30 * charge + 12 * stuck
            end
            -- the spark at each feeler's tip and its sting, brightening as it charges
            local tips = rig.parts.Tips
            if tips then
                tips.Color = SB.TIP:Lerp(Color3.new(1, 1, 1), 0.25 + 0.25 * math.sin(t * 9) + 0.5 * charge)
            end
            local sting = rig.parts.Sting
            if sting then
                sting.Color = SB.CORE:Lerp(Color3.new(1, 1, 1), curl)
            end
        end

        -- It has driven its sting into the ground (animateStormBumblebee): a crack of light, a scorch, and arcs of lightning running out across the ground
        -- from it, forking as they go; sparks thrown up; then it all flickers out.
        function Blasts.ALessonLearnedOnce(rig, fx)
            local u = rig.unit
            local s = rig.state
            local sting = rig.points.Sting
            local tip = if sting and s.tipOffset then sting.TransformedWorldCFrame:PointToWorldSpace(s.tipOffset) else rig.rootPart.Position
            local params = RaycastParams.new()
            params.FilterDescendantsInstances = { rig.model }
            local hit = workspace:Raycast(tip + Vector3.new(0, 0.6 * u, 0), Vector3.new(0, -8 * u, 0), params)
            local ground = if hit then hit.Position else tip - Vector3.new(0, 0.2 * u, 0)
            local reduced = SB.reduced()

            -- the strike itself: a short bolt from its sting into the ground, and a flash
            local function bolt(from, to, width, color, kinks)
                local last = from
                local parts = {}
                for k = 1, kinks do
                    local f = k / kinks
                    local at = from:Lerp(to, f)
                    if k < kinks then
                        local side = (to - from):Cross(Vector3.yAxis)
                        side = if side.Magnitude > 1e-3 then side.Unit else Vector3.xAxis
                        at += side * (math.random() - 0.5) * 0.35 * (to - from).Magnitude / kinks * 2 + Vector3.new(0, (math.random() - 0.5) * 0.05 * u, 0)
                    end
                    local length = (at - last).Magnitude
                    if length > 1e-3 then
                        local seg = fx.neon(Vector3.new(width, width, length), CFrame.lookAt((last + at) / 2, at), color)
                        table.insert(parts, seg)
                    end
                    last = at
                end
                return parts
            end
            for _, seg in bolt(tip, ground, 0.1 * u, SB.CORE, 4) do
                tweenAfter(0.25, seg, TweenInfo.new(0.2), { Transparency = 1 })
            end
            local flash = fx.neon(Vector3.one * 0.4 * u, CFrame.new(ground + Vector3.new(0, 0.1 * u, 0)), SB.CORE)
            flash.Shape = Enum.PartType.Ball
            flash.Transparency = 0.2
            TweenService:Create(flash, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 2.2 * u, Transparency = 1 }):Play()
            local light = Instance.new("PointLight")
            light.Color = SB.MAIN
            light.Range = 10 * u
            light.Brightness = 2
            light.Shadows = false
            light.Parent = flash
            TweenService:Create(light, TweenInfo.new(1), { Brightness = 0 }):Play()

            -- a scorch where it struck
            local scorch = fx.neon(Vector3.new(0.02 * u, 1.3 * u, 1.3 * u), CFrame.new(ground + Vector3.new(0, 0.02 * u, 0)) * CFrame.Angles(0, 0, math.pi / 2), Color3.fromRGB(40, 36, 52))
            scorch.Shape = Enum.PartType.Cylinder
            scorch.Material = Enum.Material.SmoothPlastic
            scorch.Transparency = 0.25
            tweenAfter(0.9, scorch, TweenInfo.new(0.8), { Transparency = 1 })

            -- the arcs: out across the ground from it, each a run of kinked segments lit one after another, some forking
            local count = if reduced then 4 else 7
            local facing = math.random() * 2 * math.pi
            for k = 1, count do
                local a = facing + k / count * 2 * math.pi + (math.random() - 0.5) * 0.4
                local reach = (2 + 1.4 * math.random()) * u
                local from = ground + Vector3.new(0, 0.06 * u, 0)
                local to = from + Vector3.new(math.cos(a), 0, math.sin(a)) * reach
                local segs = bolt(from, to, 0.09 * u, if k % 2 == 0 then SB.ARC else SB.MAIN, 7)
                if not reduced and k % 2 == 1 then
                    local mid = from:Lerp(to, 0.5)
                    local b = a + (if math.random() < 0.5 then 0.6 else -0.6)
                    for _, seg in bolt(mid, mid + Vector3.new(math.cos(b), 0, math.sin(b)) * reach * 0.45, 0.06 * u, SB.ARC, 4) do
                        table.insert(segs, seg)
                    end
                end
                for j, seg in segs do
                    seg.Transparency = 1
                    tweenAfter(0.03 * j, seg, TweenInfo.new(0.05), { Transparency = 0 }) -- running out from it
                    tweenAfter(0.55 + 0.03 * j, seg, TweenInfo.new(0.45), { Transparency = 1 })
                end
            end

            -- sparks thrown up
            if not reduced then
                local holder = fx.neon(Vector3.one * 0.05, CFrame.new(ground + Vector3.new(0, 0.15 * u, 0)), SB.CORE)
                holder.Transparency = 1
                local sparks = Instance.new("ParticleEmitter")
                sparks.Texture = SPARKLE
                sparks.Enabled = false
                sparks.Lifetime = NumberRange.new(0.4, 0.8)
                sparks.Speed = NumberRange.new(3 * u, 7 * u)
                sparks.SpreadAngle = Vector2.new(70, 70)
                sparks.Acceleration = Vector3.new(0, -12 * u, 0)
                sparks.Size = NumberSequence.new(0.12 * u, 0)
                sparks.Color = ColorSequence.new(SB.CORE, SB.MAIN)
                sparks.LightEmission = 1
                sparks.Parent = holder
                holder.CFrame = CFrame.lookAt(holder.Position, holder.Position + Vector3.yAxis)
                sparks:Emit(30)
            end
        end

        PetRig.Profiles.StormBumblebee = {
            Skinned = true,
            Bones = SB.BONES,
            Points = { "Body", "Head", "Abd2", "Sting" },
            GlowColors = {
                fff2a0 = SB.TIP, -- the sparks at its feelers' tips
                ffe066 = Color3.fromRGB(255, 224, 102), -- the stored lightning in its leg baskets
                fff9dc = SB.CORE, -- its sting of light
                eee4ff = SB.ARC, -- the arcs crackling across its fur
                ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
            },
            SeeThrough = { Wings = 0.45 }, -- its wings: smoky glass, dark-veined
            Effects = {
                Blast = "ALessonLearnedOnce",
                Pulse = "Charge",
                NovaLight = 2,
            },
            Colors = {
                Gold = SB.MAIN,
                Amber = SB.DEEP,
                Orange = SB.MAIN,
                Sun = SB.CORE,
                Ivory = Color3.fromRGB(255, 252, 236),
            },
            Animate = animateStormBumblebee,
        }
    end
end
