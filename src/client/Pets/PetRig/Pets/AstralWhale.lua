-- AstralWhale: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Players, RunService, TweenService, SPARKLE, tweenAfter, pose, smoothstep, Blasts, addStance = K.PetRig, K.Players, K.RunService, K.TweenService, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.addStance


    do
        -- The Astral Whale (skinned): the starsong humpback. A humpback calf: a big soft head with knobbly tubercles along its rostrum, a gentle smile
        -- arching back to its eye, a deep throat pleated from chin to navel, a small dorsal fin on a hump, wide notched flukes and long wing-like
        -- flippers knobbed along their leading edge. Its skin is the sky at dusk from the zenith down: night indigo on its back with faint stars, dusk
        -- violet, a band of rose, pearl beneath. In the grooves of its throat lie golden strings; the knobs of its flippers are small pale stars. It
        -- swims in the air in slow strokes, bobbing, flippers gliding, and looks at you often; its strings breathe softly and its stars twinkle. Now
        -- and then it spouts a puff of stardust, waves a flipper, hums (a ripple of light runs along its strings) or rolls over slowly; left alone a
        -- long while it sleeps as humpbacks do, tilted head-up, eyes shut, its strings dim. Its special, Song Between Stars: it rolls belly-up and
        -- arches into its song, its strings shimmering like a strummed harp; at the burst (Blasts.SongBetweenStars) three golden rings of sound ripple
        -- out through the air, and each faint star hanging round it chimes bright as a ring reaches it; it rolls back and spouts stardust.
        local AWH = {
            FAR = 110, -- studs from the camera past which nobody can see it fidget: its bones rest
            LID_HINGE = { L = Vector3.new(0.4959, -0.1035, -0.8622), R = Vector3.new(0.4959, 0.1035, 0.8622) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(66), -- (with the lower, past the 88 degrees between the lids' edges: they meet)
            BLINK_LOWER = math.rad(30),
            GLINTS = Vector3.new(0, 0.2895, -0.2392), -- the middle of its eyes' catch-lights piece, in the model's axes (metres): it stays where it was bound
            BLOWHOLE = Vector3.new(0, 0.396, -0.236), -- on top of its head (astral_whale.py BLOWHOLES)
            GOLD = Color3.fromRGB(255, 176, 48), -- its strings' Neon: a saturated gold (a pale one blooms white)
            GOLD_DIM = Color3.fromRGB(150, 92, 24),
            GOLD_HOT = Color3.fromRGB(255, 214, 120),
            STAR = Color3.fromRGB(110, 160, 255),
            STAR_HOT = Color3.fromRGB(205, 225, 255),
            DUSK = Color3.fromRGB(160, 120, 235),
            PEARL = Color3.fromRGB(236, 232, 244),
            -- its swimming stroke: each bone's share (astral_whale.py SWIM_UP / SWIM_DOWN, checked in Blender), and how far behind the head it moves
            SWIM = { { "Head", -0.06, 0 }, { "Spine1", 0.08, 0.5 }, { "Spine2", 0.14, 1.0 }, { "Tail", 0.2, 1.5 }, { "Fluke", 0.32, 2.0 } },
            -- its stances (game axes; the right flipper mirrors y and z), each checked in Blender for torn skin (astral_whale.py)
            GLIDE = { PecL1 = { 0, 0.45, -0.1 }, PecL2 = { 0, 0.15, 0 }, PecR1 = { 0, -0.45, 0.1 }, PecR2 = { 0, -0.15, 0 } },
            SING = { Head = { 0.26, 0, 0 }, Chest = { 0.08, 0, 0 }, Spine1 = { -0.1, 0, 0 }, Spine2 = { -0.14, 0, 0 }, Tail = { -0.16, 0, 0 }, Fluke = { -0.22, 0, 0 },
                PecL1 = { 0, -0.35, -0.3 }, PecL2 = { 0, -0.1, -0.15 }, PecR1 = { 0, 0.35, 0.3 }, PecR2 = { 0, 0.1, 0.15 } },
            SLEEP_TILT = 0.35, -- radians its body tilts head-up as it sleeps (at 0.6 it read as an odd lean, seen in Play)
            SLEEP_LIFT = 0.15, -- metres it rises as it tilts, so its flukes stay where they hung
            ROLL = 0.85 * math.pi, -- how far over it rolls to sing (belly-up)
            FIDGET_TIME = { spout = 1.6, wave = 2.2, hum = 2.4, roll = 2.8 },
            BONES = { "Body", "Chest", "Head", "Spine1", "Spine2", "Tail", "Fluke", "EyeL", "EyeR", "PecL1", "PecL2", "PecR1", "PecR2" },
        }

        function AWH.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        -- where a point of the model (its axes, metres) is at rest in the world: measured from the catch-lights piece, which (a skinned part) stays where
        -- it was bound. Called before any pose.
        function AWH.atRest(rig, point)
            local glints = rig.parts.Glints
            if not glints then
                return nil
            end
            return glints.Position + rig.rootPart.CFrame:VectorToWorldSpace((point - AWH.GLINTS) * rig.meters)
        end

        -- its blowhole, where its stardust spouts from: on its head's bone
        function AWH.glow(rig, s)
            s.glowMade = true
            local head = rig.points.Head
            local at = AWH.atRest(rig, AWH.BLOWHOLE)
            if not head or not at or AWH.reduced() or (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer) then
                return
            end
            local a = Instance.new("Attachment")
            a.Name = "Blowhole"
            a.Position = head.TransformedWorldCFrame:PointToObjectSpace(at)
            a.Parent = head
            local spout = Instance.new("ParticleEmitter")
            spout.Name = "Stardust"
            spout.Texture = SPARKLE
            spout.Enabled = false
            spout.Lifetime = NumberRange.new(0.7, 1.2)
            spout.Speed = NumberRange.new(2.2 * rig.unit, 3.4 * rig.unit)
            spout.SpreadAngle = Vector2.new(14, 14)
            spout.Acceleration = Vector3.new(0, -2.2 * rig.unit, 0)
            spout.Drag = 1.2
            spout.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
            spout.Color = ColorSequence.new(AWH.STAR_HOT, AWH.DUSK)
            spout.LightEmission = 1
            spout.LightInfluence = 0
            spout.EmissionDirection = Enum.NormalId.Top
            spout.Parent = a
            s.spout = spout
        end

        local function animateAstralWhale(rig, s, moving, fly, nova)
            if not s.glowMade then
                AWH.glow(rig, s)
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > AWH.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special, Song Between Stars: it rolls belly-up and arches into its song (to 0.4), its strings shimmering; the burst (0.42); it rolls
            -- back (0.72 to 0.92) and spouts stardust
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local special = progress > 0
            local roll = smoothstep(0.03, 0.3, progress) * (1 - smoothstep(0.72, 0.92, progress))
            local sing = smoothstep(0.12, 0.38, progress) * (1 - smoothstep(0.75, 0.9, progress))
            local wide = smoothstep(0.38, 0.43, progress) * (1 - smoothstep(0.62, 0.74, progress))
            if special then
                if progress >= 0.9 and not s.spouted then
                    s.spouted = true
                    if s.spout then
                        s.spout:Emit(18)
                    end
                end
            else
                s.spouted = false
            end

            -- left alone a long while it sleeps, tilted head-up; now and then it spouts, waves a flipper, hums or rolls over
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            local wantSleep = if s.still > 14 then 1 else 0
            s.sleep = (s.sleep or 0) + (wantSleep - (s.sleep or 0)) * math.min(1, dt * (if wantSleep > (s.sleep or 0) then 0.5 else 4))
            local sleep = smoothstep(0, 1, s.sleep)
            s.nextFidget = s.nextFidget or t + 5
            if t >= s.nextFidget then
                local r = math.random()
                s.fidgetAt = t
                s.fidgetKind = if r < 0.3 then "spout" elseif r < 0.55 then "wave" elseif r < 0.8 then "hum" else "roll"
                s.waveSide = if math.random() < 0.5 then "L" else "R"
                s.spoutDone = false
                s.nextFidget = t + AWH.FIDGET_TIME[s.fidgetKind] + 5 + math.random() * 6
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / AWH.FIDGET_TIME[s.fidgetKind], 0, 1) else 1
            local free = (1 - pace) * (1 - sleep) * (1 - roll)
            local fidget = math.sin(math.pi * env) * free
            local function kind(name)
                return if s.fidgetKind == name then fidget else 0
            end
            if s.fidgetKind == "spout" and env >= 0.35 and not s.spoutDone and free > 0.5 then
                s.spoutDone = true
                if s.spout then
                    s.spout:Emit(12)
                end
            end

            local want = {}
            -- its swimming stroke: a slow wave down its spine to its flukes, stronger as it moves; asleep, barely
            s.stroke = (s.stroke or 0) + dt * (1.5 + 3.5 * pace) * (1 - 0.6 * sleep)
            local amp = (0.45 + 0.55 * pace) * (1 - 0.7 * sleep) * (1 - 0.6 * sing)
            for _, row in AWH.SWIM do
                addStance(want, { [row[1]] = { row[2] * math.sin(s.stroke - row[3]), 0, 0 } }, amp)
            end
            -- its flippers: gliding, a slow easy flap; swept back as it moves; spread wide as it sings; one waved in its fidget; drooping asleep
            local flap = 0.12 * math.sin(t * 0.9) * (1 - pace) * (1 - sleep)
            addStance(want, { PecL1 = { 0, 0, flap }, PecR1 = { 0, 0, -flap }, PecL2 = { 0, 0, 0.5 * flap }, PecR2 = { 0, 0, -0.5 * flap } }, 1)
            addStance(want, AWH.GLIDE, pace * (1 - sing))
            addStance(want, AWH.SING, sing)
            addStance(want, { PecL1 = { 0, 0, 0.22 }, PecR1 = { 0, 0, -0.22 } }, sleep)
            local wave = kind("wave")
            if wave > 0 then
                local sd = if s.waveSide == "L" then 1 else -1
                local key = "Pec" .. s.waveSide
                addStance(want, { [key .. "1"] = { 0, 0, sd * (-0.45 + 0.12 * math.sin(t * 7)) }, [key .. "2"] = { 0, 0, sd * 0.2 * math.sin(t * 7 - 0.8) } }, wave)
            end
            -- its head: looking about, often at you; lifting a little as it spouts or hums
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2.5 + math.random() * 3.5
                s.atYou = math.random() < 0.6
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 0.8, (math.random() - 0.5) * 0.2
            end
            local calm = (1 - 0.7 * pace) * (1 - roll) * (1 - sleep)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.5, 0.5) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.4, -0.15, 0.25) else s.gazePitch) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2)
            addStance(want, { Head = { 0.25 * s.pitch + 0.12 * math.max(kind("spout"), kind("hum")), 0.3 * s.yaw, 0 }, Chest = { 0.1 * s.pitch, 0.15 * s.yaw, 0 },
                EyeL = { 0.2 * s.pitch, 0.25 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.25 * s.yaw, 0 } }, 1)

            -- its whole body: bobbing; rolled belly-up to sing, or slowly right over in its fidget; tilted head-up asleep
            local bob = math.sin(t * 0.8)
            local rollTurn = AWH.ROLL * roll + 2 * math.pi * smoothstep(0.1, 0.9, if s.fidgetKind == "roll" then env else 0) * (if s.fidgetKind == "roll" then 1 else 0)
            local bodyTurn = Vector3.new(0.03 * bob + AWH.SLEEP_TILT * sleep, 0.04 * math.sin(s.stroke * 0.5) * pace, rollTurn)
            local lift = (0.035 * bob + AWH.SLEEP_LIFT * sleep + 0.06 * roll) * u

            for _, name in AWH.BONES do
                local a = want[name] or Vector3.zero
                if name == "Body" then
                    pose(m.Body, CFrame.new(0, lift, 0) * CFrame.Angles(a.X + bodyTurn.X, a.Y + bodyTurn.Y, a.Z + bodyTurn.Z))
                else
                    pose(m[name], CFrame.Angles(a.X, a.Y, a.Z))
                end
            end

            -- its golden strings: breathing softly; a ripple of light running along them as it hums; shimmering like a strummed harp as it sings; dim
            -- asleep. Its stars twinkle, brightest as it sings.
            local hum = kind("hum")
            local strum = math.max(sing, hum)
            for k, key in { "StringsA", "StringsB" } do
                local part = rig.parts[key]
                if part then
                    local rest = 0.45 + 0.25 * math.sin(t * 1.2 + k * 1.6)
                    local shimmer = 0.5 + 0.5 * math.sin(t * (if sing > hum then 16 else 6) + k * math.pi)
                    local glow = (rest * (1 - strum) + (0.55 + 0.45 * shimmer) * strum) * (1 - 0.6 * sleep)
                    part.Color = if glow < 0.5 then AWH.GOLD_DIM:Lerp(AWH.GOLD, glow * 2) else AWH.GOLD:Lerp(AWH.GOLD_HOT, (glow - 0.5) * 2)
                end
            end
            local stars = rig.parts.Stars
            if stars then
                stars.Color = AWH.STAR:Lerp(AWH.STAR_HOT, math.clamp(0.3 + 0.25 * math.sin(t * 2.3) + 0.15 * math.sin(t * 5.1 + 1) + 0.6 * sing, 0, 1))
            end

            -- the eyes: slow blinks; shut asleep and happily as it hums; wide at the burst
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.32
                if a >= 1 then
                    s.nextBlink = t + 2.5 + math.random() * 4
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local close = math.max(blink, sleep, 0.85 * hum) * (1 - wide)
            local upper = AWH.BLINK_UPPER * close - math.rad(12) * wide
            local lower = AWH.BLINK_LOWER * close - math.rad(6) * wide
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(AWH.LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(AWH.LID_HINGE[side], lower))
            end
        end

        -- It has rolled belly-up and is singing (animateAstralWhale): faint stars hang round it; three golden rings of sound ripple out from it through
        -- the air, a quarter second apart, and each star chimes bright as each ring reaches it; it all fades as the song ends.
        function Blasts.SongBetweenStars(rig, fx)
            local u = rig.unit
            local reduced = AWH.reduced()
            local chest = rig.points.Chest
            local centre = if chest then chest.TransformedWorldCFrame.Position else rig.rootPart.Position
            local RINGS = if reduced then 2 else 3
            local SEGMENTS = if reduced then 20 else 40 -- (at 28 the ring read as a polygon, seen in Play)
            local GROW, START, REACH = 1.15, 0.8 * u, 7.5 * u -- seconds a ring takes; studs from its middle it starts and ends at

            local light = Instance.new("PointLight")
            light.Color = AWH.GOLD
            light.Range = 10 * u
            light.Brightness = 2
            light.Shadows = false
            local holder = fx.neon(Vector3.one * 0.05, CFrame.new(centre), AWH.GOLD)
            holder.Transparency = 1
            light.Parent = holder
            tweenAfter(0.3, light, TweenInfo.new(1.3), { Brightness = 0 })

            -- the stars: faint points hanging round it in the air, at their own distances and heights
            local stars = {}
            for k = 1, (if reduced then 7 else 12) do
                local a = (k - 1) / (if reduced then 7 else 12) * 2 * math.pi + math.random() * 0.4
                local r = (2.4 + math.random() * 4.6) * u
                local at = centre + Vector3.new(math.cos(a) * r, (math.random() - 0.35) * 2.2 * u, math.sin(a) * r)
                local star = fx.neon(Vector3.one * 0.1 * u, CFrame.new(at), AWH.STAR)
                star.Shape = Enum.PartType.Ball
                star.Transparency = 1
                TweenService:Create(star, TweenInfo.new(0.3), { Transparency = 0.45 }):Play()
                stars[k] = { part = star, dist = r, rang = 0 }
            end
            local function chime(st, ring)
                st.rang = ring
                local part = st.part
                if not part.Parent then
                    return
                end
                local big = (0.42 - 0.08 * ring) * u
                part.Color = AWH.STAR_HOT
                part.Size = Vector3.one * big
                part.Transparency = 0
                TweenService:Create(part, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 0.12 * u, Transparency = 0.4 }):Play()
                if not reduced and ring == 1 then
                    local sparks = Instance.new("ParticleEmitter")
                    sparks.Texture = SPARKLE
                    sparks.Enabled = false
                    sparks.Lifetime = NumberRange.new(0.3, 0.6)
                    sparks.Speed = NumberRange.new(0.8 * u, 1.6 * u)
                    sparks.SpreadAngle = Vector2.new(180, 180)
                    sparks.Drag = 3
                    sparks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12 * u), NumberSequenceKeypoint.new(1, 0) })
                    sparks.Color = ColorSequence.new(AWH.STAR_HOT, AWH.STAR)
                    sparks.LightEmission = 1
                    sparks.LightInfluence = 0
                    sparks.Parent = part
                    sparks:Emit(6)
                end
            end

            -- the rings of sound: each a circle of short golden strokes, growing out, rippling up and down as it goes like a plucked string (flat,
            -- they read as plain yellow hoops, seen in Play), fading from hot gold to pale
            for ring = 1, RINGS do
                task.delay((ring - 1) * 0.25, function()
                    if not holder.Parent then
                        return
                    end
                    local strokes = {}
                    for i = 1, SEGMENTS do
                        local seg = fx.neon(Vector3.new(0.06 * u, 0.06 * u, 0.1), CFrame.new(centre), AWH.GOLD)
                        seg.Transparency = 1
                        strokes[i] = seg
                    end
                    local began = os.clock()
                    local conn
                    conn = RunService.Heartbeat:Connect(function()
                        if not strokes[1].Parent then
                            conn:Disconnect()
                            return
                        end
                        local now = os.clock() - began
                        local f = math.clamp(now / GROW, 0, 1)
                        local r = START + (REACH - START) * (1 - (1 - f) ^ 2)
                        local width = (0.06 - 0.035 * f) * u
                        -- the ripple: a gentle wave a few hundredths of the ring's size, settling as it spreads (a fixed 0.28 stud wobble bent the
                        -- rings into lassos, seen in Play)
                        local swell = 0.045 * r * (1 - 0.6 * f)
                        local function at(a: number)
                            return centre + Vector3.new(math.cos(a) * r, swell * math.sin(8 * a + now * 9 + ring * 1.7), math.sin(a) * r)
                        end
                        local colour = AWH.GOLD_HOT:Lerp(AWH.GOLD, math.min(1, f * 2)):Lerp(AWH.PEARL, math.max(0, f - 0.5) * 1.2)
                        for i, seg in strokes do
                            local p0, p1 = at((i - 1) / SEGMENTS * 2 * math.pi), at(i / SEGMENTS * 2 * math.pi)
                            seg.Size = Vector3.new(width, width, (p1 - p0).Magnitude * 1.06)
                            seg.CFrame = CFrame.lookAt((p0 + p1) / 2, p1)
                            seg.Transparency = 0.1 + 0.9 * f * f
                            seg.Color = colour
                        end
                        for _, st in stars do
                            if st.rang < ring and r >= st.dist then
                                chime(st, ring)
                            end
                        end
                        if f >= 1 then
                            conn:Disconnect()
                            for _, seg in strokes do
                                seg.Transparency = 1
                            end
                        end
                    end)
                end)
            end
            -- the stars fade as the song ends
            for _, st in stars do
                tweenAfter(1.45, st.part, TweenInfo.new(0.4), { Transparency = 1 })
            end
        end

        local bones = table.clone(AWH.BONES)
        for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
            table.insert(bones, name)
        end
        PetRig.Profiles.AstralWhale = {
            Skinned = true,
            Bones = bones,
            Points = { "Head", "Chest" },
            GlowColors = {
                f4f6ff = Color3.fromRGB(244, 246, 255), -- the catch-lights in its eyes
                ffc45c = AWH.GOLD, -- its golden strings
                a9c8ff = AWH.STAR, -- the star knobs on its flippers
            },
            Effects = {
                Blast = "SongBetweenStars",
                NovaLight = 2,
            },
            Colors = {
                Gold = AWH.GOLD,
                Amber = AWH.GOLD_DIM,
                Orange = AWH.GOLD,
                Sun = AWH.GOLD_HOT,
                Ivory = AWH.PEARL,
            },
            Animate = animateAstralWhale,
        }
    end
end
