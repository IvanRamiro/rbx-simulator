-- The SolarButterfly pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Lighting, SPARKLE, pose, smoothstep, dropToGround = K.PetRig, K.Lighting, K.SPARKLE, K.pose, K.smoothstep, K.dropToGround

    local animateSolarButterfly, BFLY_DUSK, BFLY_GOLD, BFLY_ROSE -- animateSolarButterfly's section below (its own locals stay in its block)
    do

        -- The Solar Butterfly (skinned): a swallowtail of sunset glass. It flies in slow, deep wingbeats with glides between, bobbing as butterflies do; still
        -- a few seconds, it drifts down and lands on its legs to bask, wings spread flat to the sun, now and then closing them up over its back and opening them
        -- again; its antennae sway and twitch; warm motes of stored sunlight drift off its eyespots, more after dark.
        local BFLY_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        local BFLY_LEGS = 0.0737 -- metres from its Body bone down to the tips of its legs (solar_butterfly.py): where it stands when it lands. Measured from the
        -- bone, not the box: the importer's root part sits at the model's origin, under a pet that floats, so the box's middle is not where it seems
        BFLY_GOLD, BFLY_ROSE, BFLY_DUSK = Color3.fromRGB(255, 196, 80), Color3.fromRGB(255, 110, 90), Color3.fromRGB(150, 80, 200)
        -- its wings in the game's axes (a turn about its length; L takes the opposite sign): the same numbers as solar_butterfly.py's wings(), each checked in
        -- Blender for torn skin: raised to 0.95 and lowered to -0.5 in the beat, flat at -0.12 basking, closed over its back at 1.3
        local BFLY_UP, BFLY_DOWN, BFLY_FLAT, BFLY_CLOSED, BFLY_GLIDE = 0.95, -0.5, -0.12, 1.3, 0.3

        local function bflyWings(m, raise, bend, hindLag)
            for _, side in { "L", "R" } do
                local up = if side == "L" then -1 else 1
                pose(m["Fore" .. side .. "1"], CFrame.Angles(0, 0, up * raise))
                pose(m["Fore" .. side .. "2"], CFrame.Angles(0, 0, up * bend))
                pose(m["Hind" .. side .. "1"], CFrame.Angles(0, 0, up * (raise - hindLag)))
                pose(m["Hind" .. side .. "2"], CFrame.Angles(0, 0, up * bend * 0.8))
            end
        end

        -- warm motes of stored sunlight drifting off its eyespots; more after dark
        local function bflyMotes(rig, s)
            s.motesMade = true
            s.motes = {}
            for _, name in { "HindL2", "HindR2" } do
                local point = rig.points[name]
                if point then
                    local motes = Instance.new("ParticleEmitter")
                    motes.Name = "Sunlight"
                    motes.Texture = SPARKLE
                    motes.Rate = 1.2
                    motes.Lifetime = NumberRange.new(1.2, 2)
                    motes.Speed = NumberRange.new(0.03 * rig.unit, 0.1 * rig.unit)
                    motes.SpreadAngle = Vector2.new(180, 180)
                    motes.Acceleration = Vector3.new(0, 0.08 * rig.unit, 0)
                    motes.Drag = 1
                    motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.07 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
                    motes.Color = ColorSequence.new(BFLY_GOLD, BFLY_ROSE)
                    motes.LightEmission = 1
                    motes.LightInfluence = 0
                    motes.Parent = point
                    table.insert(s.motes, motes)
                end
            end
        end

        function animateSolarButterfly(rig, s, moving, fly, nova)
            if not s.motesMade then
                bflyMotes(rig, s)
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            -- after dark it spends its sunlight a little faster
            local clock = Lighting.ClockTime
            local night = if clock < 6.2 or clock > 17.8 then 1 else 0
            for _, motes in s.motes do
                motes.Rate = 1.2 + 2.3 * night
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > BFLY_FAR then
                return
            end
            local pace = math.max(moving, fly)

            -- the special, Afterglow: it rises a little and spreads its wings wide and still as the sunlight gathers in them (to 0.42); then lets it go
            -- (Blasts.Afterglow) with one slow, deep wingbeat, and flies on
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local spread = smoothstep(0.02, 0.25, progress) * (1 - smoothstep(0.42, 0.5, progress))
            local release = if progress > 0.42 and progress < 0.8 then math.sin(math.pi * (progress - 0.42) / 0.38) else 0
            local special = progress > 0

            -- still a few seconds, it drifts down and lands to bask; it takes off as soon as it has somewhere to go
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            local wantLand = if s.still > 4 then 1 else 0
            s.land = (s.land or 0) + (wantLand - (s.land or 0)) * math.min(1, dt * (if wantLand > (s.land or 0) then 0.9 else 4))
            local land = smoothstep(0, 1, s.land)
            local bodyBone = rig.points.Body
            if bodyBone and not s.sole then
                s.sole = rig.rootPart.CFrame:PointToObjectSpace(bodyBone.WorldPosition).Y * -1 / u + BFLY_LEGS -- (WorldPosition leaves out its own Transform)
            end
            local drop = dropToGround(rig, s, t, u, 0, s.sole or 0.15)

            -- flight: slow, deep beats; now and then a glide with its wings held up in a shallow V
            s.nextGlide = s.nextGlide or t + 2
            if t >= s.nextGlide then
                s.glideUntil = t + 0.6 + math.random() * 0.6
                s.nextGlide = s.glideUntil + 1.6 + math.random() * 2
            end
            local gliding = if t < (s.glideUntil or 0) then 1 else 0
            s.glide = (s.glide or 0) + (gliding - (s.glide or 0)) * math.min(1, dt * 6)
            local rate = (1.7 + 0.8 * moving + 0.5 * fly) * (1 - 0.8 * s.glide) * (1 - land) * (1 - spread)
            s.beat = (s.beat or 0) + dt * rate * 2 * math.pi
            local wave = math.sin(s.beat)
            local mid, half = (BFLY_UP + BFLY_DOWN) / 2, (BFLY_UP - BFLY_DOWN) / 2
            local flying = (1 - land) * (1 - spread)
            local raise = (mid + half * wave) * (1 - s.glide) + BFLY_GLIDE * s.glide
            local bend = 0.12 * math.sin(s.beat - 0.8) * (1 - s.glide)

            -- basking: wings flat to the sun; now and then closed up over its back a while, then opened again
            s.nextClose = s.nextClose or t + 3
            if land > 0.9 and t >= s.nextClose then
                s.closeAt = t
                s.nextClose = t + 5 + math.random() * 5
            end
            local closeEnv = if s.closeAt then math.clamp((t - s.closeAt) / 2.6, 0, 1) else 1
            local closed = math.min(1, math.sin(math.pi * closeEnv) * 1.6) * land
            local bask = BFLY_FLAT + 0.05 * math.sin(t * 0.9)
            local landed = bask * (1 - closed) + BFLY_CLOSED * closed

            -- the special: held flat and wide, then one slow, deep beat as it lets the light go
            local held = BFLY_FLAT - 0.05
            local deep = BFLY_UP * math.sin(math.pi * math.clamp((progress - 0.42) / 0.38, 0, 1)) * 1.0
            local wingRaise = raise * flying + landed * land * (1 - spread) + held * spread * (1 - release) + deep * release * (if progress > 0.42 then 1 else 0)
            bflyWings(m, wingRaise, bend * flying, 0.08 * flying)

            -- the body: rides each downstroke and bobs as butterflies do; settles onto its legs when it lands; rises into its special
            local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.12, -0.3, 0.3) - (s.bank or 0)) * math.min(1, dt * 3)
            local bob = (0.05 * math.sin(s.beat - 1.4) + 0.035 * math.sin(t * 1.3) + 0.02 * math.sin(t * 3.1 + 1)) * flying + 0.1 * spread
            local drift = 0.025 * math.sin(t * 1.1) * flying
            local lift = bob * u * (1 - land) - drop * land
            local pitch = (-0.08 * moving + 0.05 * math.sin(s.beat - 1.8)) * flying - 0.1 * spread
            pose(m.Body, CFrame.new(drift * u, lift, 0) * CFrame.Angles(pitch, 0.05 * math.sin(t * 0.8) * flying, s.bank * flying - drift * 1.5))
            for index, name in { "Abd1", "Abd2", "Abd3" } do
                pose(m[name], CFrame.Angles(-0.05 * math.sin(s.beat - 1.6 - index * 0.5) * flying + 0.04 * land * math.sin(t * 0.7 + index), 0, 0))
            end

            -- the head and antennae: it looks about, and to you; its antennae sway, now and then one twitches
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 1.5 + math.random() * 2.5
                s.atYou = math.random() < 0.4
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 0.7, (math.random() - 0.5) * 0.3
            end
            local wantYaw = if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.5, 0.5) else s.gazeYaw
            local wantPitch = if s.atYou then math.clamp(toYou.Y * 0.4, -0.2, 0.3) else s.gazePitch
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 4)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 4)
            pose(m.Head, CFrame.Angles(0.5 * s.pitch, 0.5 * s.yaw, 0.1 * s.yaw))
            for _, side in { "L", "R" } do
                local sign = if side == "L" then 1 else -1
                local twitch = math.max(0, math.sin(t * 1.9 + (if side == "L" then 0 else 2.1))) ^ 16
                local sway = 0.06 * math.sin(t * 1.4 + (if side == "L" then 0 else 1.2))
                pose(m["Ant" .. side .. "1"], CFrame.Angles(0.05 * math.sin(s.beat - 2) * flying + sway - 0.1 * spread, sign * 0.05 * twitch, 0))
                pose(m["Ant" .. side .. "2"], CFrame.Angles(0.25 * twitch + 0.04 * math.sin(t * 2.3 + sign), 0, 0))
            end
        end
    end

    return { animateSolarButterfly = animateSolarButterfly, BFLY_DUSK = BFLY_DUSK, BFLY_GOLD = BFLY_GOLD, BFLY_ROSE = BFLY_ROSE }
end
