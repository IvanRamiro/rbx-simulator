-- EchoBat: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Players, TweenService, SPARKLE, pose, smoothstep, Blasts, addStance = K.PetRig, K.Players, K.TweenService, K.SPARKLE, K.pose, K.smoothstep, K.Blasts, K.addStance


    do
        -- The Echo Bat (skinned): a small, plush fruit bat of the Ancient Grove, made of rings that keep sound (the grove's growth rings and a record's
        -- grooves). Cocoa fur, a fawn face, a cream bib on its chest ringed twice like a ripple; big calla-lily trumpet ears, ivory inside and cut with
        -- grooves, three of them glowing teal with the sounds it has kept; plum wings on three long fingers. It hovers on slow, lazy wing beats, rising a
        -- little on each downstroke; its ears swivel on their own, listening; it looks about, often at you, and blinks. Now and then it cocks its head to
        -- listen, flicks an ear, or chirps (a small ring of sound out of each ear). Still a long while, it dozes on the air, eyes half shut, legs tucked,
        -- beating slower. Moving, it leans into a glide, beating harder. Its special, A Voice from a Hundred Years Ago: it draws its wings up and its ears
        -- back, listening (to 0.3); rears, head up, wings spread, ears flaring (the burst, 0.42: Blasts.HundredYearEcho): rings of sound pour out of its
        -- ears and ripple out round it; then older rings, gold, come back to it out of the distance and into its ears, which glow gold as they land.
        local EB = {
            FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
            LID_HINGE = { L = Vector3.new(0.9149, 0.1203, -0.3853), R = Vector3.new(0.9149, -0.1203, 0.3853) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(76), -- (the two add past the 102 degrees between its lids' edges: at 64 + 22 a band of eye showed)
            BLINK_LOWER = math.rad(32),
            -- its ears' mouths, from each ear's bone (metres, its own axes), and the way each faces: from echo_bat.py
            EAR_AT = { L = Vector3.new(-0.0581, 0.6577, -0.0328), R = Vector3.new(0.0581, 0.6577, -0.0328) },
            MOUTH_AT = { L = Vector3.new(-0.15, 0.83, -0.1), R = Vector3.new(0.15, 0.83, -0.1) },
            MOUTH_FACING = { L = Vector3.new(-0.568, 0.613, -0.548), R = Vector3.new(0.568, 0.613, -0.548) },
            -- its stances (game axes; turns x, y, z), each checked in Blender (echo_bat.py: membranes against head, ears and trunk, wing against wing,
            -- arms against head; and along every slerp between them; no torn skin)
            FLAP_UP = { ArmL = { 0, 0.1, -0.75 }, ArmR = { 0, -0.1, 0.75 }, ForeL = { 0, 0, -0.12 }, ForeR = { 0, 0, 0.12 }, Fing1L = { 0, -0.05, -0.1 },
                Fing1R = { 0, 0.05, 0.1 }, Fing2L = { 0, -0.08, -0.08 }, Fing2R = { 0, 0.08, 0.08 }, Fing3L = { 0, -0.1, 0 }, Fing3R = { 0, 0.1, 0 },
                Body = { 0.06, 0, 0 }, EarL = { 0.1, 0, 0.05 }, EarR = { 0.1, 0, -0.05 } },
            FLAP_DOWN = { ArmL = { 0, -0.12, 0.6 }, ArmR = { 0, 0.12, -0.6 }, ForeL = { 0, 0, 0.12 }, ForeR = { 0, 0, -0.12 }, Fing1L = { 0, 0.06, 0.22 },
                Fing1R = { 0, -0.06, -0.22 }, Fing2L = { 0, 0.08, 0.22 }, Fing2R = { 0, -0.08, -0.22 }, Fing3L = { 0, 0.1, 0.18 }, Fing3R = { 0, -0.1, -0.18 },
                Body = { -0.05, 0, 0 }, EarL = { -0.08, 0, -0.04 }, EarR = { -0.08, 0, 0.04 } },
            GLIDE = { ArmL = { 0, -0.05, 0.28 }, ArmR = { 0, 0.05, -0.28 }, ForeL = { 0, 0, -0.1 }, ForeR = { 0, 0, 0.1 }, Fing1L = { 0, -0.12, 0 },
                Fing1R = { 0, 0.12, 0 }, Fing2L = { 0, -0.08, 0.05 }, Fing2R = { 0, 0.08, -0.05 }, Fing3L = { 0, -0.04, 0.1 }, Fing3R = { 0, 0.04, -0.1 },
                Body = { -0.18, 0, 0 }, Head = { 0.12, 0, 0 }, EarL = { -0.2, 0, -0.05 }, EarR = { -0.2, 0, 0.05 } },
            ECHO = { Head = { 0.32, 0, 0 }, Body = { 0.12, 0, 0 }, EarL = { -0.2, -0.15, 0.2 }, EarR = { -0.2, 0.15, -0.2 }, ArmL = { 0, -0.1, -0.35 },
                ArmR = { 0, 0.1, 0.35 }, ForeL = { 0, 0, -0.15 }, ForeR = { 0, 0, 0.15 }, Fing1L = { 0, -0.1, -0.1 }, Fing1R = { 0, 0.1, 0.1 },
                Fing2L = { 0, -0.12, 0 }, Fing2R = { 0, 0.12, 0 }, Fing3L = { 0, -0.12, 0.05 }, Fing3R = { 0, 0.12, -0.05 } },
            LISTEN = { L = { Head = { 0.08, 0.22, 0.28 }, EarL = { -0.15, -0.2, 0.1 }, EarR = { -0.05, 0.25, -0.05 } }, -- cocked to its left; its right mirrored
                R = { Head = { 0.08, -0.22, -0.28 }, EarR = { -0.15, 0.2, -0.1 }, EarL = { -0.05, -0.25, 0.05 } } },
            FLICK = { L = { EarL = { 0.3, 0.15, 0.25 } }, R = { EarR = { 0.3, -0.15, -0.25 } } },
            LEGS_TUCK = { LegL = { -0.4, 0, 0.1 }, LegR = { -0.4, 0, -0.1 } },
            BEAT = { 1.5, 2.9 }, -- wing beats a second: hovering lazily, and flying
            LIFT = 0.024, -- metres it rises on each downstroke
            BONES = { "Body", "Head", "EarL", "EarR", "EyeL", "EyeR", "ArmL", "ForeL", "HandL", "Fing1L", "Fing2L", "Fing3L", "ArmR", "ForeR", "HandR",
                "Fing1R", "Fing2R", "Fing3R", "LegL", "LegR" },
            RING = "rbxassetid://12403112662", -- a thin glowing ring with brighter arcs (also RealmAura's)
            ECHO_COLOR = Color3.fromRGB(31, 224, 198), -- the sounds it keeps: sea-glass teal
            ECHO_DIM = Color3.fromRGB(16, 150, 136),
            ECHO_BRIGHT = Color3.fromRGB(140, 255, 236),
            OLD = Color3.fromRGB(240, 192, 104), -- a voice from a hundred years ago: old gold
            RING_OUT = Color3.fromRGB(90, 255, 225), -- its rings of sound (particles: saturated, or they wash out white)
            RING_OLD = Color3.fromRGB(255, 196, 80), RING_OLD_DEEP = Color3.fromRGB(230, 150, 50), -- (in a table, "A, B = x, y" made A a nil entry: the Echo Bat's special threw on every use, release audit 2026-11-12)
            PLUM = Color3.fromRGB(150, 90, 120),
            IVORY = Color3.fromRGB(246, 234, 214),
        }

        function EB.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        -- Each ear's mouth now: where it is and the way it faces in the world, carried on its ear's bone (offsets taken at rest, in the bone's own frame).
        function EB.mouth(rig, s, side)
            local bone = rig.points["Ear" .. side]
            local m = s.mouths and s.mouths[side]
            if not bone or not m then
                local root = rig.rootPart.CFrame
                return root:PointToWorldSpace(EB.MOUTH_AT[side] * rig.meters), root:VectorToWorldSpace(EB.MOUTH_FACING[side])
            end
            local cf = bone.TransformedWorldCFrame
            return cf:PointToWorldSpace(m.at), cf:VectorToWorldSpace(m.facing)
        end

        -- Once, at rest, before any pose: each ear's mouth on its bone; a soft teal light at its head; the little rings of its chirps.
        function EB.init(rig, s)
            s.inited = true
            s.mouths = {}
            local root = rig.rootPart.CFrame
            for _, side in { "L", "R" } do
                local bone = rig.points["Ear" .. side]
                if bone then
                    local cf = bone.TransformedWorldCFrame
                    local world = cf.Position + root:VectorToWorldSpace((EB.MOUTH_AT[side] - EB.EAR_AT[side]) * rig.meters)
                    s.mouths[side] = { at = cf:PointToObjectSpace(world), facing = cf:VectorToObjectSpace(root:VectorToWorldSpace(EB.MOUTH_FACING[side])) }
                end
            end
            local head = rig.points.Head
            if head then
                local a = Instance.new("Attachment")
                a.Name = "EchoLight"
                local frame = head.TransformedWorldCFrame
                a.Position = frame:PointToObjectSpace(frame.Position + root.UpVector * 0.25 * rig.meters)
                a.Parent = head
                local light = Instance.new("PointLight")
                light.Name = "EchoGlow"
                light.Color = EB.ECHO_COLOR
                light.Range = 4 * rig.unit
                light.Brightness = 0.35
                light.Shadows = false
                light.Parent = a
                s.light = light
            end
            if not (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer) then
                s.chirps = {}
                for _, side in { "L", "R" } do
                    local a = Instance.new("Attachment")
                    a.Name = "Chirp" .. side
                    a.Parent = rig.rootPart
                    local ring = Instance.new("ParticleEmitter")
                    ring.Name = "ChirpRing"
                    ring.Texture = EB.RING
                    ring.Enabled = false
                    ring.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
                    ring.EmissionDirection = Enum.NormalId.Front
                    ring.SpreadAngle = Vector2.zero
                    ring.Lifetime = NumberRange.new(0.45)
                    ring.Speed = NumberRange.new(2.6 * rig.unit)
                    ring.Drag = 1.2
                    ring.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.18 * rig.unit), NumberSequenceKeypoint.new(1, 0.95 * rig.unit) })
                    ring.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.25), NumberSequenceKeypoint.new(1, 1) })
                    ring.Color = ColorSequence.new(EB.RING_OUT, EB.ECHO_COLOR)
                    ring.LightEmission = 0.6
                    ring.LightInfluence = 0
                    ring.Parent = a
                    s.chirps[side] = { at = a, ring = ring }
                end
            end
        end

        function EB.chirp(rig, s)
            if not s.chirps or EB.reduced() then
                return
            end
            for side, c in s.chirps do
                local at, facing = EB.mouth(rig, s, side)
                c.at.WorldCFrame = CFrame.lookAt(at, at + facing)
                c.ring:Emit(1)
            end
        end

        local function animateEchoBat(rig, s, moving, fly, nova)
            if not s.inited then
                EB.init(rig, s) -- at rest, before any pose
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > EB.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special: listening, wings drawn up and ears laid back (to 0.3); rearing into its echo (to 0.42, the burst); held, its ears trembling
            -- (to 0.7); settling (to 0.95). Its ears glow bright as the rings pour out, and gold as the old ones come back in (0.84 to 0.97).
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local special = progress > 0
            local gather = smoothstep(0.02, 0.28, progress) * (1 - smoothstep(0.3, 0.4, progress))
            local rear = smoothstep(0.3, 0.42, progress) * (1 - smoothstep(0.7, 0.95, progress))
            local tremble = if progress > 0.42 and progress < 0.72 then math.sin(t * 60) * (1 - (progress - 0.42) / 0.3) else 0
            local homecoming = smoothstep(0.82, 0.86, progress) * (1 - smoothstep(0.95, 1, progress))

            -- still a long while, it dozes on the air; now and then it cocks its head to listen, flicks an ear, or chirps
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            local wantDoze = if s.still > 14 then 1 else 0
            s.doze = (s.doze or 0) + (wantDoze - (s.doze or 0)) * math.min(1, dt * (if wantDoze > (s.doze or 0) then 0.7 else 5))
            local doze = smoothstep(0, 1, s.doze)
            s.nextFidget = s.nextFidget or t + 4
            if t >= s.nextFidget then
                local r = math.random()
                s.fidgetAt = t
                s.fidgetKind = if r < 0.38 then "listen" elseif r < 0.68 then "flick" else "chirp"
                s.fidgetSide = if math.random() < 0.5 then "L" else "R"
                s.nextFidget = t + 4.5 + math.random() * 5.5
                s.chirped = false
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / (if s.fidgetKind == "listen" then 2.2 else 1.1), 0, 1) else 1
            local fidget = math.sin(math.pi * env) * (1 - pace) * (1 - doze) * (if special then 0 else 1)
            if s.fidgetKind == "chirp" and not s.chirped and env > 0.3 and fidget > 0.2 then
                s.chirped = true
                EB.chirp(rig, s)
            end

            local want = {}
            -- the wing beat: lazy as it hovers, harder as it flies, slower as it dozes; hard through its special
            local rate = (EB.BEAT[1] + (EB.BEAT[2] - EB.BEAT[1]) * pace) * (1 - 0.35 * doze) * (1 + 0.5 * rear)
            s.phase = ((s.phase or 0) + dt * rate * 2 * math.pi) % (2 * math.pi)
            local b = math.sin(s.phase)
            local amp = (0.6 + 0.35 * pace) * (1 - 0.4 * doze) * (1 - gather) + 0.4 * rear
            addStance(want, EB.FLAP_UP, math.max(0, b) * amp + 0.7 * gather)
            addStance(want, EB.FLAP_DOWN, math.max(0, -b) * amp)
            addStance(want, EB.GLIDE, pace * 0.75 * (1 - rear))
            addStance(want, EB.ECHO, rear)
            addStance(want, { Head = { -0.12, 0, 0 }, EarL = { 0.2, 0.1, -0.05 }, EarR = { 0.2, -0.1, 0.05 } }, gather) -- head down, ears back: listening
            addStance(want, { EarL = { 0, 0, 0.05 * tremble }, EarR = { 0, 0, -0.05 * tremble } }, 1)
            addStance(want, EB.LEGS_TUCK, math.max(doze, pace * 0.6))
            addStance(want, { Head = { -0.1, 0, 0 }, EarL = { 0.15, 0, 0.08 }, EarR = { 0.15, 0, -0.08 } }, doze) -- head nodding, ears drooping
            if s.fidgetKind == "listen" then
                addStance(want, EB.LISTEN[s.fidgetSide or "L"], fidget)
            elseif s.fidgetKind == "flick" then
                addStance(want, EB.FLICK[s.fidgetSide or "L"], fidget * (0.6 + 0.4 * math.sin(t * 20)))
            elseif s.fidgetKind == "chirp" then
                addStance(want, { Head = { 0.12, 0, 0 } }, fidget)
            end

            -- its ears swivel on their own, listening; its gaze: now on you, now about
            s.nextEars = s.nextEars or 0
            if t >= s.nextEars then
                s.nextEars = t + 1.2 + math.random() * 2.2
                s.earL, s.earR = (math.random() - 0.5) * 0.24, (math.random() - 0.5) * 0.24
            end
            s.earLNow = (s.earLNow or 0) + ((s.earL or 0) - (s.earLNow or 0)) * math.min(1, dt * 6)
            s.earRNow = (s.earRNow or 0) + ((s.earR or 0) - (s.earRNow or 0)) * math.min(1, dt * 6)
            local calm = (1 - 0.6 * pace) * (1 - doze) * (1 - math.max(gather, rear))
            addStance(want, { EarL = { 0, s.earLNow, 0 }, EarR = { 0, s.earRNow, 0 } }, calm)
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2 + math.random() * 3
                s.atYou = math.random() < 0.55
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.4, (math.random() - 0.5) * 0.4
            end
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -1, 1) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.6, -0.3, 0.4) else s.gazePitch) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 3)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 3)
            addStance(want, { Head = { 0.25 * s.pitch, 0.4 * s.yaw, 0.05 * s.yaw }, EyeL = { 0.2 * s.pitch, 0.25 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.25 * s.yaw, 0 } }, 1)
            addStance(want, { Body = { 0.015 * math.sin(t * 1.3), 0, 0 } }, 1) -- breathing

            local lift = -EB.LIFT * b * amp * u
            for _, name in EB.BONES do
                local a = want[name] or Vector3.zero
                pose(m[name], CFrame.new(0, if name == "Body" then lift else 0, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- the sounds it keeps, glowing softly in its ears, a slow ripple; bright through its echo, gold as the old voice comes home
            local echo = rig.parts.Echo
            if echo then
                local ripple = 0.5 + 0.5 * math.sin(t * 1.7)
                local c = EB.ECHO_DIM:Lerp(EB.ECHO_COLOR, 0.45 + 0.55 * ripple)
                c = c:Lerp(EB.ECHO_DIM, gather * 0.8):Lerp(EB.ECHO_BRIGHT, math.max(rear * (1 - homecoming), if s.fidgetKind == "chirp" then fidget * 0.6 else 0))
                echo.Color = c:Lerp(EB.OLD, homecoming)
            end
            if s.light then
                s.light.Brightness = 0.35 + 1.6 * rear * (1 - homecoming) + 0.2 * (1 - doze) * math.sin(t * 1.7)
                s.light.Color = EB.ECHO_COLOR:Lerp(EB.OLD, homecoming)
            end

            -- the eyes: blinks; half shut as it dozes, shut as it gathers; wide through its echo and when it listens
            local wide = math.max(rear, if s.fidgetKind == "listen" then fidget else 0)
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.22
                if a >= 1 then
                    s.nextBlink = t + 2 + math.random() * 4
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local close = math.max(blink, 0.92 * doze, gather) * (1 - wide) -- (dozing at 0.6, its half-shut lids read as a scowl in Play)
            local upper = EB.BLINK_UPPER * close - math.rad(10) * wide
            local lower = EB.BLINK_LOWER * close - math.rad(6) * wide
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(EB.LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(EB.LID_HINGE[side], lower))
            end
        end

        -- Its echo (animateEchoBat, the burst): rings of sound pour out of its ears, three from each, and two ripples spread round it like the rings on its
        -- chest; then, out of the distance in front of each ear, older rings, gold, come back to it and shrink into its ears: a voice from a hundred years
        -- ago. All of it gone by 1.4 s.
        function Blasts.HundredYearEcho(rig, fx)
            local u = rig.unit
            local s = rig.state
            local reduced = EB.reduced()
            local function ringEmitter(holder, life, speed, size0, size1, transparency, color, fade)
                local ring = Instance.new("ParticleEmitter")
                ring.Texture = EB.RING
                ring.Enabled = false
                ring.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
                ring.EmissionDirection = Enum.NormalId.Front
                ring.SpreadAngle = Vector2.zero
                ring.Lifetime = NumberRange.new(life)
                ring.Speed = NumberRange.new(speed)
                ring.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, size0), NumberSequenceKeypoint.new(1, size1) })
                ring.Transparency = transparency
                ring.Color = ColorSequence.new(color, fade or color)
                ring.LightEmission = 0.6 -- (at 1 they washed out near white in Play: the gold read as no colour at all)
                ring.LightInfluence = 0
                ring.Parent = holder
                return ring
            end
            local count = if reduced then 2 else 3
            for _, side in { "L", "R" } do
                local at, facing = EB.mouth(rig, s, side)
                -- out of its ear
                local out = fx.neon(Vector3.one * 0.05, CFrame.lookAt(at, at + facing), EB.ECHO_COLOR)
                out.Transparency = 1
                local rings = ringEmitter(out, 0.75, 6 * u, 0.3 * u, 2.6 * u, NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05),
                    NumberSequenceKeypoint.new(0.6, 0.5), NumberSequenceKeypoint.new(1, 1) }), EB.RING_OUT, EB.ECHO_COLOR)
                for k = 0, count - 1 do
                    task.delay(k * 0.13, function()
                        if rings.Parent then
                            rings:Emit(1)
                        end
                    end)
                end
                -- and home again: from out in front of it, back into its ear, older and gold
                local far = at + facing * 3.2 * u
                local back = fx.neon(Vector3.one * 0.05, CFrame.lookAt(far, at), EB.OLD)
                back.Transparency = 1
                local old = ringEmitter(back, 0.55, 3.2 * u / 0.55, 2 * u, 0.25 * u, NumberSequence.new({ NumberSequenceKeypoint.new(0, 1),
                    NumberSequenceKeypoint.new(0.35, 0.35), NumberSequenceKeypoint.new(0.9, 0.2), NumberSequenceKeypoint.new(1, 1) }), EB.RING_OLD, EB.RING_OLD_DEEP)
                for k = 0, count - 1 do
                    task.delay(0.5 + k * 0.13, function()
                        if old.Parent then
                            old:Emit(1)
                        end
                    end)
                end
            end
            -- two ripples swelling round it, like the rings on its chest
            local body = rig.points.Body
            local centre = if body then body.TransformedWorldCFrame.Position else rig.rootPart.Position
            local flat = fx.neon(Vector3.one * 0.05, CFrame.lookAt(centre, centre + Vector3.yAxis), EB.ECHO_COLOR)
            flat.Transparency = 1
            local ripple = ringEmitter(flat, 0.9, 0, 0.6 * u, 5.5 * u, NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(1, 1) }), EB.ECHO_COLOR)
            ripple.Orientation = Enum.ParticleOrientation.FacingCamera -- (lying flat across a rise, with or without drag, it never showed in Play: facing you it swells round it)
            ripple:Emit(1)
            task.delay(0.16, function()
                if ripple.Parent then
                    ripple:Emit(1)
                end
            end)
            -- a teal flash about its head
            local head = rig.points.Head
            local light = Instance.new("PointLight")
            light.Color = EB.ECHO_COLOR
            light.Range = 6 * u
            light.Brightness = 1.2 -- (at 2.2 and 9 it washed the bat and the ground round it teal in Play)
            light.Shadows = false
            light.Parent = fx.neon(Vector3.one * 0.05, CFrame.new(if head then head.TransformedWorldCFrame.Position else centre), EB.ECHO_COLOR)
            light.Parent.Transparency = 1
            TweenService:Create(light, TweenInfo.new(1.1), { Brightness = 0 }):Play()
            -- a few motes of sound drifting off its ears
            if not reduced then
                local at = EB.mouth(rig, s, "L")
                local motes = Instance.new("ParticleEmitter")
                motes.Texture = SPARKLE
                motes.Enabled = false
                motes.Lifetime = NumberRange.new(0.6, 1.1)
                motes.Speed = NumberRange.new(0.6 * u, 1.6 * u)
                motes.SpreadAngle = Vector2.new(180, 180)
                motes.Drag = 2
                motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * u), NumberSequenceKeypoint.new(1, 0) })
                motes.Color = ColorSequence.new(EB.ECHO_BRIGHT, EB.ECHO_COLOR)
                motes.LightEmission = 1
                motes.LightInfluence = 0
                motes.Parent = light.Parent
                light.Parent.CFrame = CFrame.new((at + EB.mouth(rig, s, "R")) / 2)
                motes:Emit(16)
            end
        end

        local bones = table.clone(EB.BONES)
        for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
            table.insert(bones, name)
        end
        PetRig.Profiles.EchoBat = {
            Skinned = true,
            Bones = bones,
            Points = { "Body", "Head", "EarL", "EarR" },
            GlowColors = {
                ["1fe0c6"] = EB.ECHO_COLOR, -- the sounds it keeps, in the grooves of its ears
                ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
            },
            Effects = {
                Blast = "HundredYearEcho",
                NovaLight = 2,
            },
            Colors = {
                Gold = EB.ECHO_COLOR,
                Amber = EB.OLD,
                Orange = EB.PLUM,
                Sun = EB.ECHO_BRIGHT,
                Ivory = EB.IVORY,
            },
            Animate = animateEchoBat,
        }
    end
end
