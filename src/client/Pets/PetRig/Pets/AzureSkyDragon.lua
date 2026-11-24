-- AzureSkyDragon: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Players, RunService, TweenService, SPARKLE, tweenAfter, pose, smoothstep, Blasts, addStance = K.PetRig, K.Players, K.RunService, K.TweenService, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.addStance


    do
        -- The Azure Sky Dragon (skinned): a great dragon of the high sky, built in a glide (the owner's reference, 2026-11-12: a dragon gliding through an
        -- aurora above the clouds, jaws open). It never lands: its broad wings beat slow and heavy, its body rising on each downstroke, deeper and faster
        -- when it goes anywhere; it banks into its turns; its long spined tail waves behind it; its long neck reaches forward and turns its head to look
        -- about, often at you, under heavy brows, its glowing ice eyes narrowed; its jaw works open and shut on its teeth and the pale light in its throat
        -- breathes. Now and then it roars, snaps its jaws, banks round, lashes its tail or reaches its claws forward. Its special, Aurora Gale: it rears
        -- back, wings raised, the light gathering in its throat; then it lunges and breathes a cone of aurora wind (Blasts.AuroraGale).
        local AZ = {
            FAR = 120, -- studs from the camera past which nobody can see it fidget: its bones rest
            LID_HINGE = { L = Vector3.new(0.5938, -0.2983, -0.7473), R = Vector3.new(0.5938, 0.2983, 0.7473) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(40),
            BLINK_LOWER = math.rad(22),
            ICE = Color3.fromRGB(90, 215, 255), -- the light in its throat (Neon: saturated; its pale ice blooms white)
            ICE_HOT = Color3.fromRGB(190, 245, 255),
            ICE_DIM = Color3.fromRGB(20, 90, 140),
            AURORA = { Color3.fromRGB(40, 175, 255), Color3.fromRGB(140, 80, 255), Color3.fromRGB(30, 255, 150) }, -- its breath: ice, violet, green (Neon: saturated; the paler first picks bloomed white in Play)
            -- its moves (game axes), each checked in Blender for torn skin: the same numbers as azure_sky_dragon.py's BEAT_UP, BEAT_DOWN, ROAR, BANK, REACH
            ROAR = { Jaw = { -0.22, 0, 0 }, Head = { 0.16, 0, 0 }, Neck3 = { 0.08, 0, 0 }, Neck2 = { 0.05, 0, 0 } },
            SNAP = { Jaw = { 0.2, 0, 0 } }, -- (its jaw near shut: modelled open, it closes on its teeth)
            BANK = { Body = { 0, 0, 0.25 }, Chest = { 0, 0.1, 0.1 }, Neck2 = { 0, 0.15, 0 }, Head = { 0, 0.15, 0 } },
            REACH = { LegFL1 = { -0.5, 0, 0 }, LegFL2 = { 0.6, 0, 0 }, LegFR1 = { -0.5, 0, 0 }, LegFR2 = { 0.6, 0, 0 }, PawFL = { 0.4, 0, 0 }, PawFR = { 0.4, 0, 0 } },
            FIDGET_TIME = { roar = 1.8, snap = 0.9, bank = 2.4, lash = 1.4, reach = 1.8 },
        }

        local function azWings(lift, sweep, hand, fan)
            local out = {}
            for tag, sign in { L = 1, R = -1 } do
                out["Wing" .. tag .. "1"] = { 0, sweep * sign, -lift * sign }
                out["Wing" .. tag .. "2"] = { 0, 0, 0 }
                out["Wing" .. tag .. "3"] = { 0, hand * sign, 0 }
                for j = 0, 3 do
                    out["Wing" .. tag .. "F" .. (j + 1)] = { 0, fan * sign * j / 3, 0 }
                end
            end
            return out
        end
        AZ.BEAT_UP = azWings(0.55, -0.08, -0.1, 0)
        AZ.BEAT_DOWN = azWings(-0.6, 0.06, 0.18, 0)

        function AZ.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        AZ.BONES = { "Hips", "Body", "Chest", "Neck1", "Neck2", "Neck3", "Head", "Jaw", "EyeL", "EyeR" }
        for k = 1, 6 do
            table.insert(AZ.BONES, "Tail" .. k)
        end
        for _, key in { "FL", "FR", "BL", "BR" } do
            for k = 1, 3 do
                table.insert(AZ.BONES, "Leg" .. key .. k)
            end
            table.insert(AZ.BONES, "Paw" .. key)
        end
        for _, tag in { "L", "R" } do
            for k = 1, 3 do
                table.insert(AZ.BONES, "Wing" .. tag .. k)
            end
            for j = 1, 4 do
                table.insert(AZ.BONES, "Wing" .. tag .. "F" .. j)
            end
        end

        local function animateAzureSkyDragon(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > AZ.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special, Aurora Gale: it rears back, wings raised, its throat's light gathering (to 0.4); at the burst (0.42) it lunges and breathes
            -- (to 0.7); it settles (to 0.9)
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local special = progress > 0
            local gather = smoothstep(0.02, 0.36, progress) * (1 - smoothstep(0.4, 0.46, progress))
            local breathe = smoothstep(0.4, 0.46, progress) * (1 - smoothstep(0.66, 0.88, progress))
            local wide = smoothstep(0.38, 0.44, progress) * (1 - smoothstep(0.6, 0.72, progress))

            -- now and then it roars, snaps, banks round, lashes its tail or reaches its claws forward
            s.nextFidget = s.nextFidget or t + 4
            if t >= s.nextFidget and not special then
                local r = math.random()
                s.fidgetAt = t
                s.fidgetKind = if r < 0.24 then "roar" elseif r < 0.42 then "snap" elseif r < 0.62 then "bank" elseif r < 0.82 then "lash" else "reach"
                s.nextFidget = t + AZ.FIDGET_TIME[s.fidgetKind] + 4 + math.random() * 5
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / AZ.FIDGET_TIME[s.fidgetKind], 0, 1) else 1
            local fidget = math.sin(math.pi * env) * (1 - 0.6 * pace) * (if special then 0 else 1)
            local function kind(name)
                return if s.fidgetKind == name then fidget else 0
            end

            -- its wings: slow, heavy beats as it glides beside you; deeper and quicker when it goes anywhere; raised as it gathers its breath, driving
            -- down as it breathes
            s.beat = (s.beat or 0) + dt * (1.7 + 2.8 * pace)
            local stroke = math.sin(s.beat)
            local up, down = math.max(0, stroke), math.max(0, -stroke)
            local amp = (0.4 + 0.6 * pace) * (1 - gather) * (1 - breathe)
            local want = {}
            addStance(want, AZ.BEAT_UP, up * amp + gather)
            addStance(want, AZ.BEAT_DOWN, down * amp + breathe)

            -- banking into its turns, and the bank fidget
            local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.12, -0.3, 0.3) - (s.bank or 0)) * math.min(1, dt * 3)
            addStance(want, { Body = { 0, 0, s.bank }, Chest = { 0, 0, 0.5 * s.bank } }, 1)
            addStance(want, AZ.BANK, kind("bank") * (if (s.fidgetAt or 0) % 2 < 1 then 1 else -1))

            -- its head: looking about, often at you; reared back as it gathers its breath, thrust forward as it breathes
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2.5 + math.random() * 3
                s.atYou = math.random() < 0.55
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.3
            end
            local calm = (1 - 0.5 * pace) * (1 - gather) * (1 - breathe)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.7, 0.7) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.45, -0.2, 0.3) else s.gazePitch) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.5)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.5)
            addStance(want, { Neck2 = { 0.2 * s.pitch, 0.3 * s.yaw, 0 }, Neck3 = { 0.2 * s.pitch, 0.3 * s.yaw, 0 }, Head = { 0.35 * s.pitch, 0.35 * s.yaw, 0 },
                EyeL = { 0.2 * s.pitch, 0.15 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.15 * s.yaw, 0 } }, 1)
            addStance(want, { Neck1 = { 0.12, 0, 0 }, Neck2 = { 0.12, 0, 0 }, Head = { 0.3, 0, 0 } }, gather)
            addStance(want, { Neck1 = { -0.12, 0, 0 }, Neck2 = { -0.08, 0, 0 }, Head = { -0.1, 0, 0 } }, breathe)
            -- its jaw: working a little open and shut as it breathes; roaring; snapping shut
            local growl = 0.04 * math.sin(t * 1.4) + 0.02 * math.sin(t * 3.7)
            addStance(want, { Jaw = { growl, 0, 0 } }, (1 - kind("roar")) * (1 - breathe))
            addStance(want, AZ.ROAR, math.max(breathe, kind("roar"), 0.5 * gather))
            local snap = kind("snap")
            if snap > 0 then
                addStance(want, AZ.SNAP, if env < 0.4 then 1 else math.max(0, 1 - (env - 0.4) * 2.5))
            end
            -- its legs drawn up, paddling a little with its beats; reaching forward now and then
            local paddle = 0.06 * math.sin(s.beat + 0.6)
            addStance(want, { LegFL1 = { paddle, 0, 0 }, LegFR1 = { -paddle, 0, 0 }, LegBL1 = { -0.5 * paddle, 0, 0 }, LegBR1 = { 0.5 * paddle, 0, 0 } }, 1 - pace)
            addStance(want, AZ.REACH, kind("reach"))
            -- the tail: a slow wave running back down it; streaming out as it travels; a lash now and then
            local lash = kind("lash")
            for k = 1, 6 do
                local w = (0.05 + 0.05 * k / 6) * math.sin(t * 1.1 - k * 0.6) * (1 - 0.5 * pace) + 0.3 * lash * math.sin(math.pi * env * 2 - k * 0.4) * (k / 6)
                addStance(want, { ["Tail" .. k] = { 0.03 * math.sin(t * 0.8 - k * 0.5) + 0.03 * pace * math.sin(s.beat - k * 0.6), w, 0 } }, 1)
            end

            for _, name in AZ.BONES do
                local a = want[name] or Vector3.zero
                local lift = if name == "Hips" then (0.03 * down * amp - 0.015 * up * amp + 0.015 * math.sin(t * 0.8)) * u else 0
                pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- the light in its throat: breathing slow; gathering bright as it draws its breath, blazing as it breathes
            local throat = rig.parts.Breath
            if throat then
                local glow = 0.35 + 0.25 * math.sin(t * 1.4) + 0.65 * gather + 0.8 * breathe
                throat.Color = if glow < 0.6 then AZ.ICE_DIM:Lerp(AZ.ICE, glow / 0.6) else AZ.ICE:Lerp(AZ.ICE_HOT, math.min(1, (glow - 0.6) / 0.6))
            end

            -- the eyes: a slow blink now and then; narrowed as it gathers; wide as it breathes
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.24
                if a >= 1 then
                    s.nextBlink = t + 3 + math.random() * 4
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local close = math.max(blink, 0.4 * gather) * (1 - wide)
            local upper = AZ.BLINK_UPPER * close - math.rad(8) * wide
            local lower = AZ.BLINK_LOWER * close - math.rad(5) * wide
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(AZ.LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(AZ.LID_HINGE[side], lower))
            end
        end

        -- It breathes (animateAzureSkyDragon): a cone of aurora wind pours from its jaws, ribbons of ice, violet and green light streaming out and
        -- spreading as they go; a ring of pressure bursts from its mouth; ice glitter rides the gale; a flash of cold light. Gone by 1.6 s.
        function Blasts.AuroraGale(rig, fx)
            local u = rig.unit
            local reduced = AZ.reduced()
            local forward = rig.rootPart.CFrame.LookVector
            local jaw = rig.points.Jaw
            local mouth = (if jaw then jaw.TransformedWorldCFrame.Position else rig.rootPart.Position) + forward * 0.35 * u
            local aim = (forward - Vector3.yAxis * 0.12).Unit
            local right = aim:Cross(Vector3.yAxis).Unit
            local upward = right:Cross(aim).Unit
            local STREAKS = if reduced then 10 else 22
            local REACH, SPREAD, LIFE = 7 * u, 1.9 * u, 0.9

            local light = Instance.new("PointLight")
            light.Color = AZ.ICE
            light.Range = 14 * u
            light.Brightness = 3.5
            light.Shadows = false
            local holder = fx.neon(Vector3.one * 0.05, CFrame.lookAt(mouth, mouth + aim), AZ.ICE)
            holder.Transparency = 1
            light.Parent = holder
            tweenAfter(0.3, light, TweenInfo.new(1.0), { Brightness = 0 })

            -- the ring of pressure, rolling out from its jaws
            local ring = fx.neon(Vector3.new(0.05, 0.5 * u, 0.5 * u), CFrame.lookAt(mouth, mouth + aim) * CFrame.Angles(0, math.pi / 2, 0), AZ.ICE_HOT)
            ring.Shape = Enum.PartType.Cylinder
            ring.Transparency = 0.2
            TweenService:Create(ring, TweenInfo.new(0.55, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
                { Size = Vector3.new(0.05, 3.2 * u, 3.2 * u), CFrame = CFrame.lookAt(mouth + aim * 1.6 * u, mouth + aim * 3 * u) * CFrame.Angles(0, math.pi / 2, 0), Transparency = 1 }):Play()

            -- the gale: streaks of aurora light, each flying out along its own line in the cone, lengthening, then thinning away
            local streaks = {}
            for i = 1, STREAKS do
                local a = math.random() * 2 * math.pi
                local r = math.sqrt(math.random())
                local dir = (aim + (right * math.cos(a) + upward * math.sin(a)) * r * SPREAD / REACH).Unit
                local colour = AZ.AURORA[(i - 1) % #AZ.AURORA + 1]
                local seg = fx.neon(Vector3.new(0.08 * u, 0.08 * u, 0.1), CFrame.lookAt(mouth, mouth + dir), colour)
                seg.Transparency = 1
                streaks[i] = { part = seg, dir = dir, delay = math.random() * 0.25, speed = 0.8 + 0.4 * math.random() }
            end
            local began = os.clock()
            local conn
            conn = RunService.Heartbeat:Connect(function()
                if not holder.Parent then
                    conn:Disconnect()
                    return
                end
                local now = os.clock() - began
                local done = true
                for _, st in streaks do
                    local k = math.clamp((now - st.delay) / LIFE, 0, 1)
                    if k < 1 then
                        done = false
                    end
                    local head = REACH * (1 - (1 - k) ^ 2) * st.speed
                    local tail = math.max(0, head - (0.8 + 2.2 * k) * u)
                    local p0, p1 = mouth + st.dir * tail, mouth + st.dir * head
                    local length = (p1 - p0).Magnitude
                    if length > 1e-3 then
                        local w = (0.1 + 0.18 * k) * u
                        st.part.Size = Vector3.new(w, w * 0.4, length)
                        st.part.CFrame = CFrame.lookAt((p0 + p1) / 2, p1)
                    end
                    st.part.Transparency = if k <= 0 then 1 else 0.15 + 0.85 * smoothstep(0.45, 1, k)
                end
                if done then
                    conn:Disconnect()
                end
            end)

            -- ice glitter riding the gale
            if not reduced then
                local glitter = Instance.new("ParticleEmitter")
                glitter.Texture = SPARKLE
                glitter.Enabled = false
                glitter.Lifetime = NumberRange.new(0.5, 0.9)
                glitter.Speed = NumberRange.new(6 * u, 10 * u)
                glitter.SpreadAngle = Vector2.new(16, 16)
                glitter.Drag = 1.5
                glitter.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.16 * u), NumberSequenceKeypoint.new(1, 0) })
                glitter.Color = ColorSequence.new(AZ.ICE_HOT, AZ.AURORA[2])
                glitter.LightEmission = 1
                glitter.LightInfluence = 0
                glitter.EmissionDirection = Enum.NormalId.Front
                glitter.Parent = holder
                glitter:Emit(36)
            end
        end

        local bones = table.clone(AZ.BONES)
        for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
            table.insert(bones, name)
        end
        PetRig.Profiles.AzureSkyDragon = {
            Skinned = true,
            Bones = bones,
            Points = { "Head", "Jaw" },
            GlowColors = {
                ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
                bff4ff = AZ.ICE, -- the light in its throat (its pale ice blooms white as Neon)
            },
            Effects = {
                Blast = "AuroraGale",
                NovaLight = 2,
            },
            Colors = {
                Gold = AZ.ICE_HOT,
                Amber = AZ.ICE,
                Orange = AZ.AURORA[2],
                Sun = AZ.ICE_HOT,
                Ivory = Color3.fromRGB(220, 236, 250),
            },
            Animate = animateAzureSkyDragon,
        }
    end
end
