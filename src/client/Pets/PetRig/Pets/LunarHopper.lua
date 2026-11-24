-- LunarHopper: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Players, TweenService, SPARKLE, tweenAfter, pose, smoothstep, Blasts, addStance, dropToGround = K.PetRig, K.Players, K.TweenService, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.addStance, K.dropToGround


    do
        -- The Lunar Hopper (skinned): the jade rabbit of the moon. A round, soft rabbit sat up on its big flat feet, pearl white with a cool moonlit sheen;
        -- long lop ears hanging beside its full cheeks, their tips dipped in moonlight; big moonstone eyes and a crescent of moonlight on its brow; in its
        -- front paws a little jade pestle for pounding the moon's elixir. It sits breathing softly, its nose twitching, looking about with its big eyes;
        -- now and then it flicks an ear, perks both up, wiggles its tail or gives its pestle a couple of little taps; still a long while, it loafs down,
        -- ears laid back and eyes shut. It moves in soft, floaty hops that hang a moment at the top (its lore: each leap lands a little further from the
        -- ground than it should), its ears trailing, a puff of moon dust where it lands; in the air it floats, feet trailing and ears streaming. Its
        -- special, Moon Elixir: it raises its pestle and pounds three times, each stroke chiming; on the third (the burst, 0.42, Blasts.MoonElixir) the
        -- elixir bursts into light, a ring of little moons running out across the ground and motes of moonlight rising; it holds its pestle up, proud.
        local LH = {
            FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
            SOLE = 0.2508, -- metres from the middle of its box down to its soles: it sits on the ground (the box counts its RootPart, a 0.05 m cube
            -- at the origin reaching 0.025 m under its soles: half its height, 0.2633, floated it 1.25 cm, measured on the Volt Fox in Play)
            LID_HINGE = { L = Vector3.new(0.8775, -0.1038, -0.4682), R = Vector3.new(0.8775, 0.1038, 0.4682) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(66),
            BLINK_LOWER = math.rad(22),
            MOON = Color3.fromRGB(143, 188, 255),
            GLOW = Color3.fromRGB(214, 232, 255),
            PEARL = Color3.fromRGB(244, 242, 250),
            BROW = Color3.fromRGB(70, 128, 255), -- its crescent's Neon: deeper than its moonlight blue (Neon brightens: at 8fbcff it read white)
            BROW_BRIGHT = Color3.fromRGB(125, 175, 255),
            CRESCENT = "rbxassetid://74795285586917", -- a little crescent moon of light (tools/vfx/hopper_particles.py)
            HOP_RATE = 2.0, -- hops a second at a full run
            HOP = 0.075, -- metres: how high it hops
            -- its stances (game axes; left values, the right mirrored), each checked in Blender against the ground and for torn skin (lunar_hopper.py)
            CROUCH = { Body = { -0.2, 0, 0 }, Chest = { -0.08, 0, 0 }, Head = { 0.12, 0, 0 }, EarL1 = { 0, 0.25, 0 }, EarR1 = { 0, -0.25, 0 },
                EarL2 = { -0.2, 0, 0 }, EarR2 = { -0.2, 0, 0 }, ArmL1 = { -0.2, 0, 0 }, ArmR1 = { -0.2, 0, 0 } },
            LEAP = { Body = { -0.3, 0, 0 }, Chest = { -0.1, 0, 0 }, Head = { 0.3, 0, 0 }, EarL1 = { 0, 0.35, -0.2 }, EarR1 = { 0, -0.35, 0.2 },
                EarL2 = { -0.45, 0, 0 }, EarR2 = { -0.45, 0, 0 }, LegL1 = { -0.15, 0, 0 }, LegR1 = { -0.15, 0, 0 }, FootL = { -0.3, 0, 0 }, FootR = { -0.3, 0, 0 },
                ArmL1 = { 0.2, 0, 0 }, ArmR1 = { 0.2, 0, 0 }, Tail = { -0.25, 0, 0 } },
            LOAF = { Body = { -0.14, 0, 0 }, Chest = { -0.05, 0, 0 }, Head = { -0.2, 0, 0 }, EarL1 = { 0, 0.45, 0.12 }, EarR1 = { 0, -0.45, -0.12 },
                EarL2 = { -0.3, 0, 0 }, EarR2 = { -0.3, 0, 0 }, ArmL1 = { -0.25, 0, 0 }, ArmR1 = { -0.25, 0, 0 } },
            POUND_UP = { ArmL1 = { 0.5, 0, 0 }, ArmR1 = { 0.5, 0, 0 }, ArmL2 = { 0.25, 0, 0 }, ArmR2 = { 0.25, 0, 0 }, Body = { 0.12, 0, 0 }, Head = { 0.18, 0, 0 },
                EarL1 = { 0, 0.2, -0.15 }, EarR1 = { 0, -0.2, 0.15 } },
            POUND_DOWN = { ArmL1 = { -0.25, 0, 0 }, ArmR1 = { -0.25, 0, 0 }, ArmL2 = { -0.2, 0, 0 }, ArmR2 = { -0.2, 0, 0 }, Body = { -0.15, 0, 0 }, Head = { -0.12, 0, 0 },
                EarL2 = { 0.25, 0, 0 }, EarR2 = { 0.25, 0, 0 } },
            HOVER = { LegL1 = { -0.12, 0, 0 }, LegR1 = { -0.12, 0, 0 }, FootL = { -0.3, 0, 0 }, FootR = { -0.3, 0, 0 }, EarL1 = { 0, 0.3, 0 }, EarR1 = { 0, -0.3, 0 },
                EarL2 = { -0.3, 0, 0 }, EarR2 = { -0.3, 0, 0 }, Tail = { -0.2, 0, 0 } },
            PERK = { EarL1 = { 0, 0, -0.3 }, EarR1 = { 0, 0, 0.3 }, EarL2 = { 0.2, 0, 0 }, EarR2 = { 0.2, 0, 0 } },
            BONES = { "Hips", "Body", "Chest", "Neck", "Head", "EyeL", "EyeR", "EarL1", "EarL2", "EarR1", "EarR2", "ArmL1", "ArmL2", "PawL", "ArmR1", "ArmR2",
                "PawR", "Pestle", "LegL1", "LegL2", "FootL", "LegR1", "LegR2", "FootR", "Tail" },
        }

        function LH.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        -- its moonlight: a soft light at its brow, a point between its paws where it grips its pestle (where its strokes chime and its elixir bursts), a
        -- puff of moon dust for its landings
        function LH.glow(rig, s)
            s.glowMade = true
            local u = rig.meters
            -- (offsets are placed in the world and carried into each bone's own frame: every bone has its own rest turn, so a fixed offset in a
            -- bone's axes lands somewhere else, as the first try at its pestle's end did)
            local head, pawL, pawR = rig.points.Head, rig.points.PawL, rig.points.PawR
            local up = rig.rootPart.CFrame.UpVector
            if head then
                local a = Instance.new("Attachment")
                a.Name = "Moonlight"
                local frame = head.TransformedWorldCFrame
                a.Position = frame:PointToObjectSpace(frame.Position + up * 0.15 * u)
                a.Parent = head
                local light = Instance.new("PointLight")
                light.Name = "PulseLight"
                light.Color = LH.MOON
                light.Range = 4 * rig.unit
                light.Brightness = 0.6
                light.Shadows = false
                light.Parent = a
                rig.light = light
            end
            if pawL and pawR then
                local grip = Instance.new("Attachment")
                grip.Name = "Grip"
                local mid = (pawL.TransformedWorldCFrame.Position + pawR.TransformedWorldCFrame.Position) / 2
                grip.Position = pawL.TransformedWorldCFrame:PointToObjectSpace(mid)
                grip.Parent = pawL
                rig.grip = grip
                local chime = Instance.new("ParticleEmitter")
                chime.Name = "Chime"
                chime.Texture = SPARKLE
                chime.Enabled = false
                chime.Lifetime = NumberRange.new(0.3, 0.55)
                chime.Speed = NumberRange.new(0.8 * rig.unit, 1.6 * rig.unit)
                chime.SpreadAngle = Vector2.new(180, 180)
                chime.Drag = 3
                chime.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
                chime.Color = ColorSequence.new(LH.GLOW, LH.MOON)
                chime.LightEmission = 1
                chime.LightInfluence = 0
                chime.Parent = grip
                s.chime = chime
            end
            if not LH.reduced() and not (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer) then
                local feet = Instance.new("Attachment")
                feet.Name = "Landing"
                feet.Position = Vector3.new(0, -LH.SOLE * u, 0)
                feet.Parent = rig.rootPart
                local dust = Instance.new("ParticleEmitter")
                dust.Name = "MoonDust"
                dust.Texture = SPARKLE
                dust.Enabled = false
                dust.Lifetime = NumberRange.new(0.4, 0.8)
                dust.Speed = NumberRange.new(0.4 * rig.unit, 0.9 * rig.unit)
                dust.SpreadAngle = Vector2.new(70, 70)
                dust.Acceleration = Vector3.new(0, 0.5 * rig.unit, 0)
                dust.Drag = 2
                dust.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.08 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
                dust.Color = ColorSequence.new(LH.GLOW, LH.MOON)
                dust.Transparency = NumberSequence.new(0.2, 1)
                dust.LightEmission = 0.8
                dust.LightInfluence = 0
                dust.EmissionDirection = Enum.NormalId.Top
                dust.Parent = feet
                s.dust = dust
            end
        end

        local function animateLunarHopper(rig, s, moving, fly, nova)
            if not s.glowMade then
                LH.glow(rig, s)
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > LH.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, LH.SOLE)

            -- the special, Moon Elixir: its pestle raised (to 0.14), three strokes (the third at the burst, 0.42), held up proud, then settling
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local special = progress > 0
            local raise = smoothstep(0.02, 0.14, progress) * (1 - smoothstep(0.62, 0.82, progress))
            local stroke = 0
            for _, at in { 0.2, 0.31, 0.42 } do
                stroke = math.max(stroke, math.max(0, 1 - math.abs(progress - at) / 0.035))
            end
            local proud = smoothstep(0.44, 0.52, progress) * (1 - smoothstep(0.62, 0.82, progress))
            if special then
                for k, at in { 0.2, 0.31 } do
                    if progress >= at and (s.chimed or 0) < k and s.chime then
                        s.chimed = k
                        s.chime:Emit(if LH.reduced() then 4 else 10)
                    end
                end
            else
                s.chimed = 0
            end

            -- still a long while, it loafs; now and then it flicks an ear, perks both up, wiggles its tail or taps its pestle
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            local wantNap = if s.still > 12 then 1 else 0
            s.nap = (s.nap or 0) + (wantNap - (s.nap or 0)) * math.min(1, dt * (if wantNap > (s.nap or 0) then 0.8 else 5))
            local nap = smoothstep(0, 1, s.nap)
            s.nextFidget = s.nextFidget or t + 4
            if t >= s.nextFidget then
                local r = math.random()
                s.fidgetAt = t
                s.fidgetKind = if r < 0.3 then "flick" elseif r < 0.55 then "perk" elseif r < 0.78 then "wiggle" else "tap"
                s.flickSide = if math.random() < 0.5 then 1 else -1
                s.nextFidget = t + 5 + math.random() * 6
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / 1.4, 0, 1) else 1
            local fidget = math.sin(math.pi * env) * (1 - pace) * (1 - nap) * (1 - raise)

            local want = {}
            addStance(want, LH.LOAF, nap * (1 - raise))
            addStance(want, LH.POUND_UP, math.max(raise * (1 - stroke), proud))
            addStance(want, LH.POUND_DOWN, raise * stroke)
            addStance(want, LH.PERK, math.max(proud, if s.fidgetKind == "perk" then fidget else 0))
            if s.fidgetKind == "flick" then
                local side = s.flickSide or 1
                local key = if side > 0 then "L" else "R"
                local flick = fidget * (0.6 + 0.4 * math.sin(t * 18))
                addStance(want, { ["Ear" .. key .. "1"] = { 0, 0, -0.45 * side }, ["Ear" .. key .. "2"] = { 0.3, 0, -0.2 * side } }, flick)
            elseif s.fidgetKind == "tap" then
                local tap = math.max(0, math.sin(env * math.pi * 4))
                addStance(want, LH.POUND_UP, fidget * 0.45 * (1 - tap))
                addStance(want, LH.POUND_DOWN, fidget * 0.35 * tap)
            end

            -- its hops: a crouch, a floaty leap that hangs a moment at the top, a soft landing; ears trailing; moon dust where it lands. In the air it
            -- floats, feet trailing and ears streaming.
            local onFoot = moving * (1 - fly)
            s.hopAmt = (s.hopAmt or 0) + (math.min(1, onFoot * 1.6) - (s.hopAmt or 0)) * math.min(1, dt * 4)
            local hopAmt = s.hopAmt
            if hopAmt > 0.02 then
                s.hop = ((s.hop or 0) + dt * LH.HOP_RATE * math.max(0.6, hopAmt)) % 1
            else
                s.hop = 0
            end
            local p = s.hop
            local air = if p > 0.12 and p < 0.74 then (p - 0.12) / 0.62 else -1
            local arc = if air >= 0 then math.sin(math.pi * air) ^ 0.7 else 0 -- (^0.7: it hangs at the top a moment)
            local crouch = math.max(0, 1 - math.abs(p - 0.05) / 0.08, 1 - math.abs(p - 0.82) / 0.1) * hopAmt
            local leap = (if air >= 0 then math.sin(math.pi * air) else 0) * hopAmt
            local fall = (if air >= 0 then math.max(0, -math.cos(math.pi * air)) else 0) * hopAmt
            addStance(want, LH.CROUCH, crouch)
            addStance(want, LH.LEAP, leap)
            addStance(want, { EarL1 = { 0, 0, -0.3 }, EarR1 = { 0, 0, 0.3 } }, fall) -- its ears float up as it comes down
            local landed = air < 0 and p >= 0.74
            if landed and not s.landed and hopAmt > 0.4 and s.dust then
                s.dust:Emit(5)
            end
            s.landed = landed
            local float = math.sin(t * 2.2)
            addStance(want, LH.HOVER, fly)
            addStance(want, { Body = { 0.04 * float, 0, 0 }, EarL2 = { -0.15 * float, 0, 0 }, EarR2 = { -0.15 * float, 0, 0 } }, fly)

            -- breathing softly, its nose twitching now and then; its head looking about, often at you
            local breath = math.sin(t * 1.4)
            addStance(want, { Chest = { 0.015 * breath, 0, 0 }, Body = { 0.01 * breath, 0, 0 } }, 1)
            s.nextTwitch = s.nextTwitch or t + 2
            local twitch = 0
            if t >= s.nextTwitch then
                local a = (t - s.nextTwitch) / 0.5
                if a >= 1 then
                    s.nextTwitch = t + 1.5 + math.random() * 3.5
                else
                    twitch = math.sin(a * math.pi * 6) * (1 - a)
                end
            end
            addStance(want, { Head = { 0.025 * twitch, 0, 0 } }, (1 - nap) * (1 - pace))
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2.2 + math.random() * 3
                s.atYou = math.random() < 0.55
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.1, (math.random() - 0.5) * 0.3
            end
            local calm = (1 - 0.7 * pace) * (1 - raise) * (1 - 0.8 * nap)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.2, 0.35) else s.gazePitch) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 3)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 3)
            addStance(want, {
                Neck = { 0.15 * s.pitch, 0.3 * s.yaw, 0 }, Head = { 0.3 * s.pitch, 0.4 * s.yaw, 0.1 * s.yaw },
                EyeL = { 0.25 * s.pitch, 0.25 * s.yaw, 0 }, EyeR = { 0.25 * s.pitch, 0.25 * s.yaw, 0 },
            }, 1)

            -- its ears swaying softly; its tail: a wiggle in its fidget
            local sway = math.sin(t * 0.9)
            addStance(want, { EarL2 = { 0.05 * sway, 0, 0 }, EarR2 = { 0.05 * math.sin(t * 0.9 + 0.8), 0, 0 } }, 1 - nap)
            local wiggle = if s.fidgetKind == "wiggle" then fidget else 0
            addStance(want, { Tail = { 0, 0.45 * math.sin(t * 16), 0 } }, wiggle)

            local lift = (LH.HOP * arc * hopAmt) * u - drop
            for _, name in LH.BONES do
                local a = want[name] or Vector3.zero
                pose(m[name], CFrame.new(0, if name == "Hips" then lift else 0, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- its crescent breathing with soft light; brightest as its elixir bursts
            local crescent = rig.parts.Crescent
            if crescent then
                crescent.Color = LH.BROW:Lerp(LH.BROW_BRIGHT, math.clamp(0.35 + 0.3 * math.sin(t * 1.3) + 0.65 * proud, 0, 1))
            end
            if rig.light then
                rig.light.Brightness = 0.6 + 1.2 * proud
            end

            -- the eyes: blinks; closed as it loafs; wide as its elixir bursts and when it perks up
            local wide = math.max(proud, if s.fidgetKind == "perk" then fidget else 0)
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.25
                if a >= 1 then
                    s.nextBlink = t + 2 + math.random() * 4
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local close = math.max(blink, nap) * (1 - wide)
            local upper = LH.BLINK_UPPER * close - math.rad(12) * wide
            local lower = LH.BLINK_LOWER * close - math.rad(6) * wide
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(LH.LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(LH.LID_HINGE[side], lower))
            end
        end

        -- Its third stroke (animateLunarHopper): a little moon of elixir lifts out of its pestle and rises to hang above its head (0.35 s); it bursts: a
        -- flash of moonlight, a ring of crescent moons spilling out round it and settling across the ground, motes of moonlight rising; then it all fades.
        function Blasts.MoonElixir(rig, fx)
            local u = rig.unit
            -- where its paws grip the pestle now: through the bone's animated frame (an attachment's WorldPosition leaves the bone's pose out)
            local grip = rig.grip
            local at = if grip and grip.Parent and grip.Parent:IsA("Bone") then grip.Parent.TransformedWorldCFrame:PointToWorldSpace(grip.Position) else fx.origin
            local head = rig.points.Head
            -- (its head's bone is down at its jaw: its crown is 0.18 m above it, and the little moon hangs a hand's breadth over that)
            local top = (if head then head.TransformedWorldCFrame.Position else rig.rootPart.Position) + Vector3.new(0, 0.34 * rig.meters, 0)
            local params = RaycastParams.new()
            params.FilterDescendantsInstances = { rig.model }
            local hit = workspace:Raycast(rig.rootPart.Position, Vector3.new(0, -10 * u, 0), params)
            local ground = if hit then hit.Position else rig.rootPart.Position - Vector3.new(0, LH.SOLE * rig.meters, 0)
            local reduced = LH.reduced()
            local RISE, HANG = 0.35, 0.15

            -- the little moon: lifting out of its pestle and rising over its head, a soft light going with it
            local moon = fx.neon(Vector3.one * 0.2 * u, CFrame.new(at), LH.BROW_BRIGHT)
            moon.Shape = Enum.PartType.Ball
            moon.Transparency = 0.05
            TweenService:Create(moon, TweenInfo.new(RISE, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), { CFrame = CFrame.new(top), Size = Vector3.one * 0.5 * u }):Play()
            local light = Instance.new("PointLight")
            light.Color = LH.MOON
            light.Range = 6 * u
            light.Brightness = 1.2
            light.Shadows = false
            light.Parent = moon
            tweenAfter(RISE, moon, TweenInfo.new(HANG, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { Size = Vector3.one * 0.62 * u }) -- it hangs there a beat, swelling
            tweenAfter(RISE + HANG, light, TweenInfo.new(0.12), { Brightness = 3, Range = 12 * u })
            tweenAfter(RISE + HANG + 0.2, light, TweenInfo.new(0.9), { Brightness = 0 })
            -- its burst: swelling and fading in a flash (in the pale moonlight colour Neon washed white against its fur: its brighter brow blue)
            tweenAfter(RISE + HANG, moon, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 2.6 * u, Transparency = 1 })

            task.delay(RISE + HANG, function()
                if not moon.Parent then
                    return
                end
                -- a ring of crescent moons spilling out from it and settling across the ground round it, each turned its own way: billboards riding
                -- tweened anchors (as particles, a tween does not carry them, and flown on speed and drag they stayed hidden in the burst)
                local count = if reduced then 5 else 8
                for k = 1, count do
                    local a = (k - 1) / count * 2 * math.pi + 0.3
                    local out = Vector3.new(math.cos(a), 0, math.sin(a))
                    local rest = ground + out * 3.2 * u + Vector3.new(0, 0.6 * u, 0)
                    local anchor = fx.neon(Vector3.one * 0.05, CFrame.new(top), LH.MOON)
                    anchor.Transparency = 1
                    local board = Instance.new("BillboardGui")
                    board.Size = UDim2.fromScale(0.5 * u, 0.5 * u)
                    board.LightInfluence = 0
                    board.Brightness = 1.3
                    board.Parent = anchor
                    local image = Instance.new("ImageLabel")
                    image.BackgroundTransparency = 1
                    image.Size = UDim2.fromScale(1, 1)
                    image.Image = LH.CRESCENT
                    image.Rotation = math.deg(a) + 90
                    image.Parent = board
                    TweenService:Create(anchor, TweenInfo.new(0.9, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), { CFrame = CFrame.new(rest) }):Play()
                    TweenService:Create(board, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = UDim2.fromScale(1.3 * u, 1.3 * u) }):Play()
                    tweenAfter(0.85, image, TweenInfo.new(0.45), { ImageTransparency = 1 })
                end
                -- motes of moonlight rising from where it burst
                if not reduced then
                    local motes = Instance.new("ParticleEmitter")
                    motes.Texture = SPARKLE
                    motes.Enabled = false
                    motes.Lifetime = NumberRange.new(0.8, 1.3)
                    motes.Speed = NumberRange.new(1.5 * u, 3.5 * u)
                    motes.SpreadAngle = Vector2.new(180, 180)
                    motes.Acceleration = Vector3.new(0, 1.2 * u, 0)
                    motes.Drag = 1.8
                    motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15 * u), NumberSequenceKeypoint.new(1, 0) })
                    motes.Color = ColorSequence.new(LH.GLOW, LH.MOON)
                    motes.LightEmission = 1
                    motes.LightInfluence = 0
                    motes.Parent = moon
                    motes:Emit(32)
                end
            end)
        end

        local bones = table.clone(LH.BONES)
        for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
            table.insert(bones, name)
        end
        PetRig.Profiles.LunarHopper = {
            Skinned = true,
            Bones = bones,
            Points = { "Head", "PawL", "PawR" },
            GlowColors = {
                f4f8ff = Color3.fromRGB(244, 248, 255), -- the catch-lights in its eyes
                ["8fbcff"] = LH.BROW, -- the crescent on its brow
            },
            Effects = {
                Blast = "MoonElixir",
                NovaLight = 2,
            },
            Colors = {
                Gold = LH.GLOW,
                Amber = LH.MOON,
                Orange = LH.MOON,
                Sun = LH.PEARL,
                Ivory = LH.PEARL,
            },
            Animate = animateLunarHopper,
        }
    end
end
