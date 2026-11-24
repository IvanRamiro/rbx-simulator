-- OriginSerpent: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Players, RunService, SPARKLE, tweenAfter, pose, smoothstep, Blasts, addStance = K.PetRig, K.Players, K.RunService, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.addStance


    do
        -- The Origin Serpent (skinned): the first spirit vein, a loong. Its long body corkscrews up through the air round an invisible axis, its tail
        -- trailing below like a root of light, its neck carrying its head forward over the top; faceted carp scales of dark primordial slate, the world's
        -- first Qi glowing cyan in their seams, a vein of light down each flank, a pale plated belly, a row of spines down its back. A big, fierce head:
        -- a long flat-topped muzzle with a ridge down it, heavy brows over narrowed cyan slit eyes, a jaw open on great fangs and rows of teeth, spiny
        -- cheek frills, swept stag antlers tipped in cyan, two long glowing barbels. Two Qi rings, magenta and cyan, orbit round it. A slow wave runs up
        -- its coils as it floats; light pulses up its veins from its tail to its head; it looks at you often, growling low in its jaw, its barbels
        -- swaying. Now and then it roars, snaps, flicks its tail, rises in its coil or glares at you; left alone it settles, half-lidded, its rings
        -- slowing. Its special, The First Vein: its coils rise and its head rears as light races up its veins and its rings spin up; at the burst
        -- (Blasts.TheFirstVein) it roars and a double helix of cyan and magenta light erupts from its coil into the sky.
        local OS = {
            FAR = 110, -- studs from the camera past which nobody can see it fidget: its bones rest
            -- metres its whole coil is raised (the Root bone): the rig centres its tall box (7.5 studs) on the follow root about 3 studs up, which left
            -- its tail tip 0.45 studs under the floor (measured in Play, 2026-11-10); raised, the tail hangs clear, about 0.7 studs over the ground
            LIFT = 0.14,
            LID_HINGE = { L = Vector3.new(0.3861, -0.3492, -0.8538), R = Vector3.new(0.3861, 0.3492, 0.8538) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(46), -- (with the lower, past the 68 degrees between its narrowed lids' edges: they meet)
            BLINK_LOWER = math.rad(28),
            QI = Color3.fromRGB(30, 205, 255), -- its veins, barbels and cyan ring (Neon: saturated; a pale cyan blooms white)
            QI_HOT = Color3.fromRGB(170, 245, 255),
            QI_DIM = Color3.fromRGB(10, 90, 130),
            MAGENTA = Color3.fromRGB(255, 60, 205),
            MAGENTA_HOT = Color3.fromRGB(255, 170, 235),
            SILVER = Color3.fromRGB(206, 216, 232),
            -- its coil's slow wave: the bones up its body, each a little behind the last (origin_serpent.py SWAY_A/B, checked in Blender for torn skin)
            WAVE = { "Tail3", "Tail4", "Core", "Body1", "Body2", "Body3", "Body4" },
            -- its stances (game axes), each checked in Blender (origin_serpent.py: ROAR, SNAP, LOOK, RISE, FLICK)
            ROAR = { Jaw = { -0.32, 0, 0 }, Head = { 0.22, 0, 0 }, Neck = { 0.1, 0, 0 } },
            SNAP = { Jaw = { 0.22, 0, 0 } }, -- (its jaw near closed: further, its fangs would meet its lower jaw)
            RISE = { Core = { 0.1, 0, 0 }, Body1 = { 0.06, 0, 0 }, Body2 = { 0.06, 0, 0 }, Neck = { -0.1, 0, 0 }, Head = { 0.1, 0, 0 } },
            FLICK = { Tail1 = { 0.4, 0.35, 0 }, Tail2 = { 0.22, 0.15, 0 } },
            GLARE = { Neck = { -0.08, 0, 0 }, Head = { -0.12, 0, 0 } },
            FIDGET_TIME = { roar = 1.8, snap = 0.9, flick = 1.4, rise = 2.4, glare = 2.6 },
            BONES = { "Core", "Body1", "Body2", "Body3", "Body4", "Neck", "Head", "Jaw", "Tail4", "Tail3", "Tail2", "Tail1", "EyeL", "EyeR", "BarbelL", "BarbelR",
                "RingA", "RingB" },
        }

        function OS.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        local function animateOriginSerpent(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > OS.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special, The First Vein: its coils rise and its head rears (to 0.4) as light races up its veins and its rings spin up; the roar at the
            -- burst (0.42); it settles (0.7 to 0.92)
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local special = progress > 0
            local gather = smoothstep(0.02, 0.38, progress) * (1 - smoothstep(0.7, 0.92, progress))
            local roar = smoothstep(0.36, 0.44, progress) * (1 - smoothstep(0.62, 0.8, progress))
            local wide = smoothstep(0.38, 0.43, progress) * (1 - smoothstep(0.6, 0.72, progress))

            -- left alone a long while it settles; now and then it roars, snaps, flicks its tail, rises in its coil or glares at you
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            local wantRest = if s.still > 15 then 1 else 0
            s.rest = (s.rest or 0) + (wantRest - (s.rest or 0)) * math.min(1, dt * (if wantRest > (s.rest or 0) then 0.5 else 4))
            local rest = smoothstep(0, 1, s.rest)
            s.nextFidget = s.nextFidget or t + 5
            if t >= s.nextFidget then
                local r = math.random()
                s.fidgetAt = t
                s.fidgetKind = if r < 0.22 then "roar" elseif r < 0.4 then "snap" elseif r < 0.6 then "flick" elseif r < 0.8 then "rise" else "glare"
                s.nextFidget = t + OS.FIDGET_TIME[s.fidgetKind] + 4 + math.random() * 5
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / OS.FIDGET_TIME[s.fidgetKind], 0, 1) else 1
            local fidget = math.sin(math.pi * env) * (1 - pace) * (1 - rest) * (1 - gather)
            local function kind(name)
                return if s.fidgetKind == name then fidget else 0
            end

            local want = {}
            -- the slow wave up its coils, quicker as it moves; barely as it rests
            s.wave = (s.wave or 0) + dt * (0.9 + 2.2 * pace + 3 * gather)
            local amp = (0.6 + 0.4 * pace) * (1 - 0.6 * rest)
            for k, name in OS.WAVE do
                addStance(want, { [name] = { 0, 0.11 * math.sin(s.wave - k * 0.75), 0.02 * math.sin(s.wave * 0.7 - k * 0.5) } }, amp)
            end
            addStance(want, { Tail1 = { 0.12 * math.sin(s.wave * 1.3 - 6), 0.25 * math.sin(s.wave * 1.1 - 6.5), 0 }, Tail2 = { 0, 0.12 * math.sin(s.wave * 1.1 - 5.8), 0 } }, 1)
            addStance(want, OS.RISE, math.max(gather, kind("rise")))
            addStance(want, OS.FLICK, kind("flick"))
            addStance(want, OS.GLARE, kind("glare") + 0.5 * rest)
            -- its head: looking about, often at you; its jaw growling a little open and shut; roaring; snapping
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2 + math.random() * 3
                s.atYou = math.random() < 0.6
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.25
            end
            local calm = (1 - 0.6 * pace) * (1 - gather) * (1 - 0.7 * rest)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.6, 0.6) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.4, -0.2, 0.25) else s.gazePitch) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 3)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 3)
            addStance(want, { Neck = { 0.12 * s.pitch, 0.25 * s.yaw, 0 }, Head = { 0.25 * s.pitch, 0.35 * s.yaw, 0.1 * s.yaw },
                EyeL = { 0.2 * s.pitch, 0.25 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.25 * s.yaw, 0 } }, 1)
            local growl = 0.05 * math.sin(t * 1.6) + 0.03 * math.sin(t * 4.3)
            addStance(want, { Jaw = { growl, 0, 0 } }, (1 - rest) * (1 - roar))
            addStance(want, OS.SNAP, rest * 0.6)
            addStance(want, OS.ROAR, math.max(roar, kind("roar")))
            local snap = kind("snap")
            if snap > 0 then
                addStance(want, OS.SNAP, if env < 0.35 then 1 else math.max(0, 1 - (env - 0.35) * 3))
                addStance(want, { Jaw = { -0.18, 0, 0 } }, if env < 0.35 then env / 0.35 * 0.6 else 0)
            end
            -- its barbels swaying, streaming as it moves
            local sway = math.sin(t * 1.3)
            addStance(want, { BarbelL = { 0.1 * sway + 0.15 * pace, 0.12 * math.sin(t * 0.9), 0.08 * sway }, BarbelR = { 0.1 * sway + 0.15 * pace, -0.12 * math.sin(t * 0.9 + 0.6), -0.08 * sway } }, 1)
            -- its rings orbiting, the magenta one way and the cyan the other; faster as it moves; spinning up in its special; slow as it rests
            s.ringA = (s.ringA or 0) + dt * (0.8 + 1.2 * pace + 7 * gather) * (1 - 0.6 * rest)
            s.ringB = (s.ringB or 0) - dt * (1.0 + 1.4 * pace + 8 * gather) * (1 - 0.6 * rest)

            local bob = math.sin(t * 0.85)
            pose(m.Root, CFrame.new(0, OS.LIFT * u, 0))
            for _, name in OS.BONES do
                local a = want[name] or Vector3.zero
                if name == "Core" then
                    pose(m.Core, CFrame.new(0, (0.02 * bob + 0.04 * gather) * u, 0) * CFrame.Angles(a.X + 0.02 * bob, a.Y, a.Z))
                elseif name == "RingA" then
                    pose(m.RingA, CFrame.Angles(0, s.ringA, 0))
                elseif name == "RingB" then
                    pose(m.RingB, CFrame.Angles(0, s.ringB, 0))
                else
                    pose(m[name], CFrame.Angles(a.X, a.Y, a.Z))
                end
            end

            -- the first Qi pulsing up its veins from its tail to its head (racing in its special); dim as it rests. Its barbels and rings glow steady.
            s.pulse = (s.pulse or 0) + dt * (1.4 + 7 * gather)
            for k, key in { "VeinA", "VeinB", "VeinC", "VeinD" } do
                local part = rig.parts[key]
                if part then
                    local beat = math.max(0, math.sin(s.pulse - k * 0.9)) ^ 2
                    local glow = (0.35 + 0.65 * beat) * (1 - 0.5 * rest) + 0.4 * roar
                    part.Color = if glow < 0.5 then OS.QI_DIM:Lerp(OS.QI, glow * 2) else OS.QI:Lerp(OS.QI_HOT, math.min(1, (glow - 0.5) * 2))
                end
            end
            local ringA, ringB = rig.parts.RingA, rig.parts.RingB
            if ringA then
                ringA.Color = OS.MAGENTA:Lerp(OS.MAGENTA_HOT, math.clamp(0.2 * math.sin(t * 2.1) + 0.6 * gather, 0, 1))
            end
            if ringB then
                ringB.Color = OS.QI:Lerp(OS.QI_HOT, math.clamp(0.2 * math.sin(t * 2.4 + 1) + 0.6 * gather, 0, 1))
            end

            -- the eyes: slow blinks; narrowed in a glare and as it rests; wide at its roar
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.22
                if a >= 1 then
                    s.nextBlink = t + 3 + math.random() * 4
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local close = math.max(blink, 0.45 * kind("glare"), 0.55 * rest) * (1 - wide)
            local upper = OS.BLINK_UPPER * close - math.rad(10) * wide
            local lower = OS.BLINK_LOWER * close - math.rad(5) * wide
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(OS.LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(OS.LID_HINGE[side], lower))
            end
        end

        -- It roars (animateOriginSerpent): a double helix of cyan and magenta light erupts from its coil and climbs into the sky, the first spirit vein
        -- opening; a flash, sparks thrown off it; then it fades as it reaches its height.
        function Blasts.TheFirstVein(rig, fx)
            local u = rig.unit
            local reduced = OS.reduced()
            local core = rig.points.Core
            local base = if core then core.TransformedWorldCFrame.Position else rig.rootPart.Position
            local SEGMENTS = if reduced then 20 else 48 -- (strokes per strand: at 26, about 10 a turn, it read as a zig-zag of sticks in Play)
            local RISE, HEIGHT, TURNS, RADIUS = 0.6, 9 * u, 2.5, 1.3 * u

            local light = Instance.new("PointLight")
            light.Color = OS.QI
            light.Range = 12 * u
            light.Brightness = 3
            light.Shadows = false
            local holder = fx.neon(Vector3.one * 0.05, CFrame.new(base), OS.QI)
            holder.Transparency = 1
            light.Parent = holder
            tweenAfter(0.25, light, TweenInfo.new(1.0), { Brightness = 0 })

            -- two strands, each a line of short glowing strokes, climbing as a helix and fading out once it has risen
            local strands = {}
            for strand = 1, 2 do
                local colour = if strand == 1 then OS.QI else OS.MAGENTA
                local strokes = {}
                for i = 1, SEGMENTS do
                    local seg = fx.neon(Vector3.new(0.12 * u, 0.12 * u, 0.1), CFrame.new(base), colour)
                    seg.Transparency = 1
                    strokes[i] = seg
                end
                strands[strand] = strokes
            end
            local began = os.clock()
            local conn
            conn = RunService.Heartbeat:Connect(function()
                if not holder.Parent then
                    conn:Disconnect()
                    return
                end
                local now = os.clock() - began
                local grow = 1 - (1 - math.clamp(now / RISE, 0, 1)) ^ 3
                local fade = math.clamp((now - RISE - 0.15) / 0.75, 0, 1)
                local top = HEIGHT * grow
                for strand, strokes in strands do
                    local function at(k: number)
                        local sAlong = k / SEGMENTS
                        local a = sAlong * TURNS * 2 * math.pi + (strand - 1) * math.pi + now * 6
                        local r = RADIUS * (1 - 0.55 * sAlong)
                        return base + Vector3.new(math.cos(a) * r, sAlong * top, math.sin(a) * r)
                    end
                    for i, seg in strokes do
                        local p0, p1 = at(i - 1), at(i)
                        local length = (p1 - p0).Magnitude
                        if length > 1e-3 then
                            local w = (0.16 - 0.1 * (i / SEGMENTS)) * u
                            seg.Size = Vector3.new(w, w, length * 1.08)
                            seg.CFrame = CFrame.lookAt((p0 + p1) / 2, p1)
                        end
                        seg.Transparency = 0.05 + 0.95 * fade
                    end
                end
                if fade >= 1 then
                    conn:Disconnect()
                end
            end)

            -- sparks of the first Qi thrown off it as it erupts
            if not reduced then
                local sparks = Instance.new("ParticleEmitter")
                sparks.Texture = SPARKLE
                sparks.Enabled = false
                sparks.Lifetime = NumberRange.new(0.5, 1.0)
                sparks.Speed = NumberRange.new(3 * u, 6 * u)
                sparks.SpreadAngle = Vector2.new(60, 60)
                sparks.Acceleration = Vector3.new(0, -4 * u, 0)
                sparks.Drag = 1.2
                sparks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.18 * u), NumberSequenceKeypoint.new(1, 0) })
                sparks.Color = ColorSequence.new(OS.QI_HOT, OS.MAGENTA)
                sparks.LightEmission = 1
                sparks.LightInfluence = 0
                sparks.Parent = holder
                holder.CFrame = CFrame.lookAt(base, base + Vector3.yAxis)
                sparks:Emit(40)
            end
        end

        local bones = table.clone(OS.BONES)
        for _, name in { "Root", "LidUL", "LidUR", "LidLL", "LidLR" } do
            table.insert(bones, name)
        end
        PetRig.Profiles.OriginSerpent = {
            Skinned = true,
            Bones = bones,
            Points = { "Head", "Core" },
            GlowColors = {
                f2fbff = Color3.fromRGB(242, 251, 255), -- the catch-lights in its eyes
                ["38e0ff"] = OS.QI, -- its veins, barbels and cyan ring
                ff4fd8 = OS.MAGENTA, -- its magenta ring
            },
            Effects = {
                Blast = "TheFirstVein",
                NovaLight = 2,
            },
            Colors = {
                Gold = OS.QI_HOT,
                Amber = OS.QI,
                Orange = OS.MAGENTA,
                Sun = OS.QI_HOT,
                Ivory = OS.SILVER,
            },
            Animate = animateOriginSerpent,
        }
    end
end
