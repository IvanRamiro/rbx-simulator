-- CrystalBeetle: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Players, TweenService, SPARKLE, tweenAfter, pose, smoothstep, Blasts, dropToGround, leopardGroundAt = K.PetRig, K.Players, K.TweenService, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.dropToGround, K.leopardGroundAt

    -- ---------- The Crystal Beetle: all of it in one block, so its locals are freed at its end. PetRig's main chunk sits at Luau's limit of 200 locals
    -- (a top-level table of the beetle's pushed it over, though twenty plain locals fitted): a new pet goes in a block of its own here. ----------
    do
        -- The Crystal Beetle (skinned): a stout, proud rhinoceros beetle of indigo chitin, its wing cases domes of crystal ringed with a growth layer for every
        -- year, its great horn a quartz crystal grown a segment a year. Every piece of it is a rigid plate on its own bone, as an insect's are. It stands
        -- square on its six legs, turning its head slowly, proud; now and then it tosses its horn, shoves at nothing with its head down, flicks its clubbed
        -- antennae, settles its wing cases with a shrug. It walks in a tripod gait (three legs down, three swinging forward). When its owner flies it opens its
        -- wing cases, swings its wings out from under them and buzzes alongside, its legs hanging.
        local BEETLE = {
            FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
            BODY_SOLE = 0.1097, -- metres from its Body bone down to its feet (crystal_beetle.py)
            -- its walk, checked in Blender at every quarter of its cycle: each leg swings about the upright through its hip (a planted foot keeps exactly its
            -- height), lifting at the hip and the knee as it swings forward; the front left, middle right and hind left together, then the others
            SWING = 0.3,
            LIFT = 0.22,
            KNEE = 0.3,
            LEGS = { { "L", 1, 1, 0 }, { "L", 2, 1, math.pi }, { "L", 3, 1, 0 }, { "R", 1, -1, math.pi }, { "R", 2, -1, 0 }, { "R", 3, -1, math.pi } }, -- side, pair, sign, lead
            -- stances, each checked in Blender (crystal_beetle.py's POSES) and along the slerp from one to another: turns x, y, z; then a move in metres
            FLY = { -- on the wing (its wings' own turns are built in animateCrystalBeetle: spread first, then beating)
                Body = { 0.42, 0, 0, 0, 0.05, 0 },
                ElyL = { -0.4, 0, -1.1 }, ElyR = { -0.4, 0, 1.1 },
                LegL1 = { 0, -0.15, 0.22 }, ShinL1 = { 0, 0, -0.2 }, LegL2 = { 0, 0, 0.22 }, ShinL2 = { 0, 0, -0.2 }, LegL3 = { 0, 0.15, 0.22 }, ShinL3 = { 0, 0, -0.2 },
                LegR1 = { 0, 0.15, -0.22 }, ShinR1 = { 0, 0, 0.2 }, LegR2 = { 0, 0, -0.22 }, ShinR2 = { 0, 0, 0.2 }, LegR3 = { 0, -0.15, -0.22 }, ShinR3 = { 0, 0, 0.2 },
            },
            WING_SPREAD = 1.35,
            WING_UP = 0.6, -- its wings beat mostly above level: lower, they met its legs
            WING_DOWN = 0.25,
            REAR = { -- its special, wound up: reared on its hind legs, front legs up, head back
                Body = { 0.38, 0, 0, 0, 0.094, 0.01 }, Head = { 0.2, 0, 0 },
                LegL1 = { 0, 0, -0.55 }, ShinL1 = { 0, 0, 0.45 }, LegR1 = { 0, 0, 0.55 }, ShinR1 = { 0, 0, -0.45 },
            },
            STRIKE = { -- struck: its front slammed down, its head swung down, the horn level before it (pitched to the ground, its face went in first)
                Body = { -0.12, 0, 0, 0, 0.022, 0 }, Head = { -0.5, 0, 0 },
                LegL1 = { 0, -0.25, -0.12 }, LegR1 = { 0, 0.25, 0.12 },
            },
            SHRUG = { ElyL = { -0.18, 0, -0.08 }, ElyR = { -0.18, 0, 0.08 } },
            BONES = {
                "Head", "AntL", "AntR", "ElyL", "ElyR",
                "LegL1", "ShinL1", "FootL1", "LegL2", "ShinL2", "FootL2", "LegL3", "ShinL3", "FootL3",
                "LegR1", "ShinR1", "FootR1", "LegR2", "ShinR2", "FootR2", "LegR3", "ShinR3", "FootR3",
            },
            CYAN = Color3.fromRGB(160, 245, 255),
            DEEP = Color3.fromRGB(40, 140, 175),
            PALE = Color3.fromRGB(225, 252, 255),
        }

        function BEETLE.cf(a, u)
            local move = if a[4] then CFrame.new(a[4] * u, a[5] * u, a[6] * u) else CFrame.identity
            return move * CFrame.Angles(a[1], a[2], a[3])
        end

        local function animateCrystalBeetle(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > BEETLE.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime

            -- the special, Ring of Years: it lands if it is flying, rears on its hind legs (to 0.32), slams its front down (at 0.42: Blasts.RingOfYears),
            -- holds it, and settles
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local active = if rig.nova then 1 else 0
            s.air = (s.air or 0) + (fly * (1 - active) - (s.air or 0)) * math.min(1, dt * 3)
            local grounded = 1 - smoothstep(0, 0.3, s.air)
            local rear = smoothstep(0.05, 0.3, progress) * (1 - smoothstep(0.37, 0.42, progress)) * grounded
            local strike = smoothstep(0.37, 0.42, progress) * (1 - smoothstep(0.62, 0.9, progress)) * grounded
            local impact = if progress > 0.42 then math.exp(-(progress - 0.42) * 14) else 0

            -- it stands on the ground, or keeps to its owner's height on the wing
            local body = rig.points.Body
            if body and not s.sole then
                s.sole = rig.rootPart.CFrame:PointToObjectSpace(body.WorldPosition).Y * -1 / u + BEETLE.BODY_SOLE -- (WorldPosition leaves out its own Transform)
            end
            local drop = dropToGround(rig, s, t, u, s.air, s.sole or 0.11)

            -- idle business: a toss of the horn, a shove with its head down, a shrug of its wing cases
            s.nextIdle = s.nextIdle or t + 4
            if t >= s.nextIdle and moving < 0.1 and s.air < 0.1 and active == 0 then
                s.idleAt, s.idleKind = t, math.random(1, 3)
                s.nextIdle = t + 6 + math.random() * 6
            end
            local idle = if s.idleAt then (t - s.idleAt) / 1.8 else 1
            local env = if idle < 1 then math.sin(math.pi * idle) else 0
            local toss = if s.idleKind == 1 then env else 0
            local shove = if s.idleKind == 2 then env else 0
            local shrug = if s.idleKind == 3 then env else 0

            -- its legs: the tripod gait as it goes, or a few plodding steps in place as it shoves
            local walking = math.max(moving, 0.5 * shove) * grounded * (1 - rear) * (1 - strike)
            s.step = (s.step or 0) + dt * (4 + 7 * moving) * walking
            local want = {}
            for _, leg in BEETLE.LEGS do
                local tag, k, sign, lead = leg[1], leg[2], leg[3], leg[4]
                local sw = math.sin(s.step + lead) * walking
                local lf = math.max(0, math.cos(s.step + lead)) * walking
                want["Leg" .. tag .. k] = CFrame.Angles(0, -BEETLE.SWING * sw * sign, -BEETLE.LIFT * lf * sign)
                want["Shin" .. tag .. k] = CFrame.Angles(0, 0, BEETLE.KNEE * lf * sign)
                want["Foot" .. tag .. k] = CFrame.identity
            end

            -- its head: slowly, proudly about, sometimes at you; tossing its horn, or down to shove
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 3 + math.random() * 4
                s.atYou = math.random() < 0.5
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 0.6, (math.random() - 0.4) * 0.25
            end
            local wantYaw = if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.38, 0.38) else s.gazeYaw
            local wantPitch = if s.atYou then math.clamp(toYou.Y * 0.4, -0.2, 0.18) else s.gazePitch
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2)
            local calm = (1 - rear) * (1 - strike)
            local yaw = math.clamp(s.yaw * calm + 0.3 * math.sin(idle * 2 * math.pi * 2) * toss, -0.38, 0.38)
            local pitch = math.clamp(s.pitch * calm - 0.2 * shove + 0.1 * toss, -0.2, 0.18)
            want.Head = CFrame.Angles(pitch, yaw, 0)

            -- its antennae: the clubs flick now and then
            s.nextFlick = s.nextFlick or t + 1
            if t >= s.nextFlick then
                s.flickAt = t
                s.nextFlick = t + 1.5 + math.random() * 3
            end
            local fl = if s.flickAt then (t - s.flickAt) / 0.3 else 1
            local flick = if fl < 1 then math.sin(math.pi * fl) else 0
            want.AntL = CFrame.Angles(0.15 * math.sin(t * 1.3) + 0.25 * flick, -0.2 * flick, 0)
            want.AntR = CFrame.Angles(0.15 * math.sin(t * 1.3 + 1) + 0.25 * flick, 0.2 * flick, 0)

            -- its wing cases: a shrug now and then; open on the wing (first: its wings swing out after, from under them)
            want.ElyL = BEETLE.cf(BEETLE.SHRUG.ElyL, u):Lerp(CFrame.identity, 1 - shrug)
            want.ElyR = BEETLE.cf(BEETLE.SHRUG.ElyR, u):Lerp(CFrame.identity, 1 - shrug)
            local cases = math.min(1, s.air / 0.6)
            local spread = smoothstep(0.4, 1, s.air)
            s.buzz = (s.buzz or 0) + dt * 110 * spread
            local beat = math.sin(s.buzz)
            local flap = (-BEETLE.WING_UP * math.max(beat, 0) + BEETLE.WING_DOWN * math.max(-beat, 0)) * spread
            pose(m.WingL, CFrame.Angles(0, 0, flap) * CFrame.Angles(0, -BEETLE.WING_SPREAD * spread, 0))
            pose(m.WingR, CFrame.Angles(0, 0, -flap) * CFrame.Angles(0, BEETLE.WING_SPREAD * spread, 0))

            -- the stances over all that, each a slerp (CFrame:Lerp) as Blender checked them
            for _, name in BEETLE.BONES do
                local cf = want[name] or CFrame.identity
                local a = BEETLE.FLY[name]
                if a then
                    cf = cf:Lerp(BEETLE.cf(a, u), if string.sub(name, 1, 3) == "Ely" then cases else s.air)
                end
                a = BEETLE.REAR[name]
                if a then
                    cf = cf:Lerp(BEETLE.cf(a, u), rear)
                end
                a = BEETLE.STRIKE[name]
                if a then
                    cf = cf:Lerp(BEETLE.cf(a, u), strike)
                end
                pose(m[name], cf)
            end

            -- its body: square on the ground (dropped onto it), hovering and bobbing on the wing; rearing, slamming down, a jolt as it lands
            local hover = (0.04 * math.sin(t * 2.2) + 0.012 * math.sin(s.buzz * 0.05)) * s.air
            local bodyCf = CFrame.new(0, (hover - 0.012 * impact) * u - drop, 0)
            local stance = CFrame.identity:Lerp(BEETLE.cf(BEETLE.FLY.Body, u), s.air)
            stance = stance:Lerp(BEETLE.cf(BEETLE.REAR.Body, u), rear)
            stance = stance:Lerp(BEETLE.cf(BEETLE.STRIKE.Body, u), strike)
            pose(m.Body, bodyCf * stance)
        end

        -- It has slammed its front down (animateCrystalBeetle): a ring of crystal points bursts up out of the ground round it, one after another, one for every
        -- year it has lived; a ripple of cyan light runs out along the ground; then the points shatter into glitter and are gone.
        function Blasts.RingOfYears(rig, fx)
            local u, metre, neon = rig.unit, rig.meters, fx.neon
            local head = rig.points.Head
            local centre = if head then head.TransformedWorldCFrame.Position else rig.rootPart.Position
            local params = RaycastParams.new()
            params.FilterDescendantsInstances = { rig.model }
            local hit = workspace:Raycast(centre + Vector3.new(0, 1 * u, 0), Vector3.new(0, -12 * u, 0), params)
            local groundY = if hit then hit.Position.Y else centre.Y - 0.15 * metre
            local player = Players.LocalPlayer
            local reduced = player and player:GetAttribute("SettingReducedEffects") == true
            local count = if reduced then 8 else 14
            local facing = fx.facing

            local glitter = Instance.new("ParticleEmitter")
            glitter.Texture = SPARKLE
            glitter.Enabled = false
            glitter.Lifetime = NumberRange.new(0.4, 0.8)
            glitter.Speed = NumberRange.new(0.8 * u, 2 * u)
            glitter.SpreadAngle = Vector2.new(180, 180)
            glitter.Acceleration = Vector3.new(0, -3 * u, 0)
            glitter.Drag = 2
            glitter.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12 * u), NumberSequenceKeypoint.new(1, 0) })
            glitter.Color = ColorSequence.new(BEETLE.PALE, BEETLE.CYAN)
            glitter.LightEmission = 0.9
            glitter.LightInfluence = 0.1

            for k = 1, count do
                local a = (k - 1) / count * 2 * math.pi
                local out = facing:VectorToWorldSpace(Vector3.new(math.sin(a), 0, -math.cos(a)))
                local at = leopardGroundAt(Vector3.new(centre.X, groundY, centre.Z) + out * ((1.5 + 0.25 * (k % 2)) * u), metre)
                if at then
                    local tall = (0.55 + 0.35 * math.random()) * u
                    local thick = (0.14 + 0.06 * math.random()) * u
                    local tilt = CFrame.lookAt(at, at + out) * CFrame.Angles(math.rad(-22), 0, 0) * CFrame.Angles(0, math.rad(45), 0) -- upright, leaning out 22 degrees, a diamond across (at -68 they lay flat: seen in Play)
                    local spike = neon(Vector3.new(thick, tall, thick), tilt * CFrame.new(0, -tall * 0.6, 0), BEETLE.CYAN)
                    spike.Material = Enum.Material.Glass
                    spike.Transparency = 0.2
                    local core = neon(Vector3.new(thick * 0.35, tall * 0.85, thick * 0.35), spike.CFrame, BEETLE.PALE)
                    core.Transparency = 0.3
                    local delay = (k - 1) * 0.018 -- one after another round the ring
                    tweenAfter(delay, spike, TweenInfo.new(0.12, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { CFrame = tilt * CFrame.new(0, tall * 0.42, 0) })
                    tweenAfter(delay, core, TweenInfo.new(0.12, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { CFrame = tilt * CFrame.new(0, tall * 0.42, 0) })
                    tweenAfter(0.75 + delay * 0.5, spike, TweenInfo.new(0.18), { Transparency = 1, Size = Vector3.new(thick * 0.3, tall * 0.5, thick * 0.3) })
                    tweenAfter(0.75 + delay * 0.5, core, TweenInfo.new(0.18), { Transparency = 1 })
                    if not reduced then
                        local shards = glitter:Clone()
                        shards.Parent = spike
                        task.delay(0.75 + delay * 0.5, function()
                            if shards.Parent then
                                shards:Emit(6) -- it shatters
                            end
                        end)
                    end
                end
            end
            glitter:Destroy()

            -- a ripple of cyan light along the ground
            local ripple = neon(Vector3.new(0.03 * u, 0.6 * u, 0.6 * u), CFrame.new(centre.X, groundY + 0.04 * u, centre.Z) * CFrame.Angles(0, 0, math.pi / 2), BEETLE.CYAN)
            ripple.Shape = Enum.PartType.Cylinder
            ripple.Transparency = 0.35
            TweenService:Create(ripple, TweenInfo.new(0.55, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.02 * u, 4.2 * u, 4.2 * u), Transparency = 1 }):Play()
            local flash = neon(Vector3.one * 0.1, CFrame.new(centre), BEETLE.CYAN)
            flash.Transparency = 1
            local light = Instance.new("PointLight")
            light.Color = BEETLE.CYAN
            light.Range = 6 * u
            light.Brightness = 0
            light.Shadows = false
            light.Parent = flash
            TweenService:Create(light, TweenInfo.new(0.08), { Brightness = 2 }):Play()
            tweenAfter(0.5, light, TweenInfo.new(0.5), { Brightness = 0 })
        end

        PetRig.Profiles.CrystalBeetle = {
            Skinned = true,
            Bones = {
                "Body", "Head", "AntL", "AntR", "ElyL", "ElyR", "WingL", "WingR",
                "LegL1", "ShinL1", "FootL1", "LegL2", "ShinL2", "FootL2", "LegL3", "ShinL3", "FootL3",
                "LegR1", "ShinR1", "FootR1", "LegR2", "ShinR2", "FootR2", "LegR3", "ShinR3", "FootR3",
            },
            Points = { "Body", "Head" },
            GlowColors = {
                ["9ff4ff"] = Color3.fromRGB(159, 244, 255), -- the newest crystal: its horn's tip
                ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
            },
            Effects = {
                Blast = "RingOfYears",
                Pulse = "Tip",
                Light = "Tip",
                NovaLight = 2,
            },
            Colors = {
                Gold = BEETLE.CYAN,
                Amber = Color3.fromRGB(214, 152, 64),
                Orange = BEETLE.DEEP,
                Sun = BEETLE.PALE,
                Ivory = Color3.fromRGB(240, 250, 255),
            },
            Animate = animateCrystalBeetle,
        }
    end
end
