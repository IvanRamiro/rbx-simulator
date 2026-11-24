-- AquaWisp: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Debris, Players, TweenService, SPARKLE, tweenAfter, pose, smoothstep, Blasts, addStance = K.PetRig, K.Debris, K.Players, K.TweenService, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.addStance


    do
        -- The Aqua Wisp (skinned): a small water seahorse, a current made into a creature. Sea-blue going to clear aqua, pale as foam on its belly, light
        -- netted over it; a crown of curling wave-crests, big ocean eyes, a short snout with a little round mouth, a see-through fan on its back and two
        -- little fins behind its cheeks, leafy fronds down its back, its tail curled into a spiral. It hovers upright, bobbing, its fan rippling fast as a
        -- real seahorse's does and its little fins fluttering; its tail slowly curls and lets out; it looks at you and tilts its head. Now and then it
        -- twirls round, curls its tail up tight, or blows a few bubbles. Moving, it leans into the current. Its special, Tide Spiral: it curls tight and
        -- twirls faster and faster (to 0.42); at the burst (Blasts.TideSpiral) three ribbons of water spiral up around it and burst into a shower of
        -- droplets, ripples running out across the ground; it arches up, wide-eyed, and settles.
        local AW = {
            FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
            LID_HINGE = { L = Vector3.new(0.7599, -0.0683, -0.6464), R = Vector3.new(0.7599, 0.0683, 0.6464) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(56),
            BLINK_LOWER = math.rad(28),
            GLINTS = Vector3.new(0, 0.8339, -0.0725), -- the middle of its eyes' catch-lights piece, in the model's axes (metres): it stays where it was bound
            MOUTH = Vector3.new(0, 0.782, -0.198), -- the tip of its snout (aqua_wisp.py SNOUT), where its bubbles come from
            FOAM = Color3.fromRGB(236, 252, 255),
            AQUA = Color3.fromRGB(60, 196, 232),
            SEA = Color3.fromRGB(32, 128, 214),
            -- its stances, checked in Blender for torn skin (aqua_wisp.py's pose_library: CURL, LEAN, LOOK, TWIST, the fin wave and flap)
            LEAN = { Body = { -0.35, 0, 0 }, Chest = { -0.1, 0, 0 }, Head = { 0.25, 0, 0 } },
            BONES = { "Body", "Chest", "Neck", "Head", "Crest", "EyeL", "EyeR", "PecL", "PecR", "Dorsal1", "Dorsal2", "Dorsal3" },
        }
        for k = 1, 6 do
            table.insert(AW.BONES, "Tail" .. k)
        end

        function AW.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        -- where a point of the model (its axes, metres) is at rest in the world: measured from the catch-lights piece, which (a skinned part) stays where
        -- it was bound. Called before any pose.
        function AW.atRest(rig, point)
            local glints = rig.parts.Glints
            if not glints then
                return nil
            end
            return glints.Position + rig.rootPart.CFrame:VectorToWorldSpace((point - AW.GLINTS) * rig.meters)
        end

        -- its soft light, and where its bubbles come from: both on the head's bone
        function AW.glow(rig, s)
            s.glowMade = true
            local head = rig.points.Head
            local mouth = AW.atRest(rig, AW.MOUTH)
            if not (head and mouth) then
                return
            end
            local a = Instance.new("Attachment")
            a.Name = "Mouth"
            a.CFrame = head.TransformedWorldCFrame:ToObjectSpace(CFrame.new(mouth))
            a.Parent = head
            s.mouth = a
            local light = Instance.new("PointLight")
            light.Name = "PulseLight"
            light.Color = AW.AQUA
            light.Range = 4 * rig.unit
            light.Brightness = 0.9
            light.Shadows = false
            light.Parent = a
            rig.light = light
        end

        -- a few bubbles from its mouth, wobbling up and popping
        function AW.bubbles(rig, s, count)
            if not s.mouth or AW.reduced() or (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer) or not rig.rootPart:IsDescendantOf(workspace) then
                return
            end
            local u = rig.unit
            for k = 1, count do
                task.delay((k - 1) * 0.22, function()
                    if not s.mouth.Parent then
                        return
                    end
                    local size = (0.12 + 0.08 * math.random()) * u
                    local from = s.mouth.WorldPosition
                    local bubble = Instance.new("Part")
                    bubble.Name = "Bubble"
                    bubble.Shape = Enum.PartType.Ball
                    bubble.Material = Enum.Material.Glass
                    bubble.Color = AW.FOAM
                    bubble.Transparency = 0.55
                    bubble.Size = Vector3.one * size * 0.4
                    bubble.Anchored = true
                    bubble.CanCollide = false
                    bubble.CanTouch = false
                    bubble.CanQuery = false
                    bubble.CastShadow = false
                    bubble.CFrame = CFrame.new(from)
                    bubble.Parent = rig.model
                    local rise = 1.6 + 0.6 * math.random()
                    local drift = Vector3.new((math.random() - 0.5) * 0.5, 0, (math.random() - 0.5) * 0.5) * u
                    TweenService:Create(bubble, TweenInfo.new(rise, Enum.EasingStyle.Sine, Enum.EasingDirection.Out),
                        { CFrame = CFrame.new(from + Vector3.new(0, 1.4 * u, 0) + drift), Size = Vector3.one * size }):Play()
                    tweenAfter(rise, bubble, TweenInfo.new(0.12), { Size = Vector3.one * size * 1.5, Transparency = 1 }) -- it pops
                    Debris:AddItem(bubble, rise + 0.3)
                end)
            end
        end

        local function animateAquaWisp(rig, s, moving, fly, nova)
            if not s.glowMade then
                AW.glow(rig, s) -- before any pose: the head bone is at rest
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > AW.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special, Tide Spiral: it curls tight and twirls, faster and faster (to 0.42); at the burst it arches up, its tail flung open; it settles
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local wind = smoothstep(0.03, 0.4, progress) * (1 - smoothstep(0.42, 0.5, progress))
            local arch = smoothstep(0.41, 0.47, progress) * (1 - smoothstep(0.6, 0.85, progress))
            local spinTurns = if progress > 0 and progress < 0.42 then 2.5 * smoothstep(0.03, 0.42, progress) ^ 2 else 0
            local special = progress > 0

            -- now and then it twirls, curls its tail up tight, or blows bubbles
            s.nextFidget = s.nextFidget or t + 4
            if t >= s.nextFidget and not special then
                local r = math.random()
                s.fidgetAt, s.fidgetKind = t, if r < 0.35 then "twirl" elseif r < 0.65 then "curl" else "bubbles"
                s.nextFidget = t + 6 + math.random() * 6
                if s.fidgetKind == "bubbles" then
                    AW.bubbles(rig, s, 3 + math.random(0, 2))
                end
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / 1.4, 0, 1) else 1
            local fidget = math.sin(math.pi * env) * (1 - pace)
            local twirl = if s.fidgetKind == "twirl" and env < 1 then smoothstep(0, 1, env) * 2 * math.pi * (1 - pace) else 0

            local want = {}
            -- hovering upright, bobbing; leaning into the current when it moves
            local bob = math.sin(t * 1.4)
            addStance(want, AW.LEAN, pace * (0.6 + 0.4 * fly))
            addStance(want, { Body = { 0.04 * math.sin(t * 0.9) - 0.25 * arch, twirl + spinTurns * 2 * math.pi, 0.03 * math.sin(t * 0.7) } }, 1)

            -- its tail: slowly curling and letting out; tight in its fidget and its special; flung open as the spiral bursts; trailing when it moves
            local curl = 0.12 * math.sin(t * 0.8) + 0.35 * (if s.fidgetKind == "curl" then fidget else 0) + 0.45 * wind - 0.5 * arch - 0.18 * pace
            for k = 1, 6 do
                addStance(want, { ["Tail" .. k] = { -curl * (0.5 + 0.1 * k), 0.05 * math.sin(t * 1.1 - k * 0.6), 0 } }, 1)
            end

            -- its fan rippling fast, a wave running up it; its little fins fluttering; faster as it moves and as it winds up
            local beat = 18 + 10 * pace + 14 * wind
            s.beat = (s.beat or 0) + dt * beat
            local amp = 0.32 + 0.12 * pace + 0.1 * wind
            for k = 1, 3 do
                addStance(want, { ["Dorsal" .. k] = { 0, amp * math.sin(s.beat - k * 1.1), 0 } }, 1)
            end
            local flutter = math.sin(s.beat * 0.8)
            addStance(want, { PecL = { 0, 0.35 * flutter + 0.2, 0.15 * flutter }, PecR = { 0, -0.35 * flutter - 0.2, -0.15 * flutter } }, 1)

            -- its gaze: curious, often on you, the head tilting as it looks; up at the sky as the spiral bursts
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2 + math.random() * 3
                s.atYou = math.random() < 0.6
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.4
                s.tilt = (math.random() - 0.5) * 0.5
            end
            local calm = (1 - 0.6 * pace) * (1 - wind)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.3, 0.35) else s.gazePitch) * calm + 0.45 * arch
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 3)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 3)
            s.headTilt = (s.headTilt or 0) + ((s.tilt or 0) * calm - (s.headTilt or 0)) * math.min(1, dt * 2)
            addStance(want, {
                Neck = { 0.3 * s.pitch + 0.02 * bob, 0.35 * s.yaw, 0 },
                Head = { 0.4 * s.pitch, 0.5 * s.yaw, s.headTilt },
                EyeL = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
                EyeR = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
                Crest = { 0.08 * math.sin(t * 1.3), 0, 0.06 * math.sin(t * 0.9) - 0.15 * arch },
            }, 1)

            for _, name in AW.BONES do
                local a = want[name] or Vector3.zero
                local lift = if name == "Body" then (0.03 * bob + 0.05 * arch) * u else 0
                pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- the eyes: blinks; wide as the spiral bursts
            local wide = smoothstep(0.38, 0.44, progress) * (1 - smoothstep(0.65, 0.8, progress))
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.2
                if a >= 1 then
                    s.nextBlink = t + 2.5 + math.random() * 4
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local close = blink * (1 - wide)
            local upper = AW.BLINK_UPPER * close - math.rad(6) * wide
            local lower = AW.BLINK_LOWER * close - math.rad(5) * wide
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(AW.LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(AW.LID_HINGE[side], lower))
            end
        end

        -- It has wound itself up, twirling (animateAquaWisp): three ribbons of water spiral up around it from the ground and burst at the top into a shower
        -- of droplets; ripples run out across the ground; then it all fades.
        local SPIRAL_TIME, SPIRAL_STEPS = 0.85, 14
        function Blasts.TideSpiral(rig, fx)
            local u = rig.unit
            local params = RaycastParams.new()
            params.FilterDescendantsInstances = { rig.model }
            local from = rig.rootPart.Position
            local hit = workspace:Raycast(from, Vector3.new(0, -10 * u, 0), params)
            local ground = if hit then hit.Position else from - Vector3.new(0, 1.5 * u, 0)
            local top = math.max(from.Y + 1.2 * u, ground.Y + 3.5 * u)
            local reduced = AW.reduced()
            local turn = math.random() * 2 * math.pi

            -- the ribbons: a bright head of water on each, a trail behind it, rising round it in a narrowing spiral
            local function spiral(k, f)
                local a = turn + (k - 1) * 2 * math.pi / 3 + f * 2.5 * math.pi
                local r = (1.7 - 0.9 * f) * u
                return Vector3.new(from.X + math.cos(a) * r, ground.Y + 0.1 * u + (top - ground.Y) * f, from.Z + math.sin(a) * r)
            end
            local step = SPIRAL_TIME / SPIRAL_STEPS
            for k = 1, 3 do
                local head = fx.neon(Vector3.one * 0.22 * u, CFrame.new(spiral(k, 0)), AW.FOAM)
                head.Shape = Enum.PartType.Ball
                local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
                a0.Position, a1.Position = Vector3.new(0, 0.14 * u, 0), Vector3.new(0, -0.14 * u, 0)
                a0.Parent, a1.Parent = head, head
                local trail = Instance.new("Trail")
                trail.Attachment0, trail.Attachment1 = a0, a1
                trail.Lifetime = 0.45
                trail.FaceCamera = true
                trail.LightEmission = 0.7
                trail.LightInfluence = 0.2
                trail.MinLength = 0
                trail.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0.2) })
                trail.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, AW.FOAM), ColorSequenceKeypoint.new(0.4, AW.AQUA), ColorSequenceKeypoint.new(1, AW.SEA) })
                trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05), NumberSequenceKeypoint.new(1, 1) })
                trail.Parent = head
                for j = 1, SPIRAL_STEPS do
                    tweenAfter((j - 1) * step, head, TweenInfo.new(step, Enum.EasingStyle.Linear), { CFrame = CFrame.new(spiral(k, j / SPIRAL_STEPS)) })
                end
                tweenAfter(SPIRAL_TIME, head, TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 0.5 * u, Transparency = 1 })
            end

            -- the burst at the top: a splash of light, a shower of droplets falling round it
            local crown = fx.neon(Vector3.one * 0.1 * u, CFrame.new(from.X, top, from.Z), AW.FOAM)
            crown.Shape = Enum.PartType.Ball
            crown.Transparency = 1
            tweenAfter(SPIRAL_TIME, crown, TweenInfo.new(0.05), { Transparency = 0.2 })
            tweenAfter(SPIRAL_TIME + 0.05, crown, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 1.6 * u, Transparency = 1 })
            local light = Instance.new("PointLight")
            light.Color = AW.AQUA
            light.Range = 10 * u
            light.Brightness = 0
            light.Shadows = false
            light.Parent = crown
            tweenAfter(SPIRAL_TIME, light, TweenInfo.new(0.1), { Brightness = 2.5 })
            tweenAfter(SPIRAL_TIME + 0.15, light, TweenInfo.new(0.6), { Brightness = 0 })
            local drops = Instance.new("ParticleEmitter")
            drops.Texture = SPARKLE
            drops.Enabled = false
            drops.Lifetime = NumberRange.new(0.5, 0.8)
            drops.Speed = NumberRange.new(1.5 * u, 3.5 * u)
            drops.SpreadAngle = Vector2.new(70, 70)
            drops.Acceleration = Vector3.new(0, -9 * u, 0)
            drops.Drag = 0.5
            drops.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.16 * u), NumberSequenceKeypoint.new(1, 0.04 * u) })
            drops.Color = ColorSequence.new(AW.FOAM, AW.AQUA)
            drops.LightEmission = 0.8
            drops.LightInfluence = 0.2
            drops.Parent = crown
            crown.CFrame = CFrame.lookAt(crown.Position, crown.Position + Vector3.yAxis)
            task.delay(SPIRAL_TIME, function()
                if drops.Parent then
                    drops:Emit(if reduced then 14 else 40)
                end
            end)

            -- ripples running out across the ground, one after another
            for k = 1, (if reduced then 2 else 3) do
                local ring = fx.neon(Vector3.new(0.03 * u, 0.6 * u, 0.6 * u), CFrame.new(ground + Vector3.new(0, 0.03 * u, 0)) * CFrame.Angles(0, 0, math.pi / 2), AW.AQUA)
                ring.Shape = Enum.PartType.Cylinder
                ring.Transparency = 1
                local at = SPIRAL_TIME + 0.1 + (k - 1) * 0.15
                tweenAfter(at, ring, TweenInfo.new(0.05), { Transparency = 0.35 })
                tweenAfter(at + 0.05, ring, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.03 * u, (5 + k) * u, (5 + k) * u), Transparency = 1 })
            end
        end

        local bones = table.clone(AW.BONES)
        for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
            table.insert(bones, name)
        end
        PetRig.Profiles.AquaWisp = {
            Skinned = true,
            Bones = bones,
            Points = { "Head" },
            GlowColors = {
                ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
            },
            SeeThrough = { Fins = 0.35 }, -- its fan, its little fins and its fronds: clear water
            Effects = {
                Blast = "TideSpiral",
                Pulse = "Glints",
                NovaLight = 2,
            },
            Colors = {
                Gold = AW.AQUA,
                Amber = AW.SEA,
                Orange = AW.SEA,
                Sun = AW.FOAM,
                Ivory = AW.FOAM,
            },
            Animate = animateAquaWisp,
        }
    end
end
