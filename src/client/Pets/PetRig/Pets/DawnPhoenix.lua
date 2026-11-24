-- DawnPhoenix: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Players, TweenService, SPARKLE, pose, smoothstep, Blasts, addStance = K.PetRig, K.Players, K.TweenService, K.SPARKLE, K.pose, K.smoothstep, K.Blasts, K.addStance


    do
        -- The Dawn Phoenix, The First Light (skinned: tools/blender/pets/dawn_phoenix.py, one mesh on 48 bones). A noble firebird hanging in the air
        -- beside its owner on great raised wings. Its wings beat as a bird's do: a quick, strong downstroke, then a slower recovery in which the elbow
        -- and the hand fold back and the hand trails the arm, the arm's fan of feathers opening its slots; the body rises a little on each
        -- downstroke while the neck takes the bob back, so its head rides steady as a raptor's does. Its crest and its two long central tail feathers
        -- trail and ripple after every move. It looks about slowly and regally, often at you, and blinks; now and then it turns its head right round
        -- to look back over its shoulder, stretches both wings high, preens at its shoulder, or rises into its proud display (wings high and wide, breast
        -- out, crest up, tail fanned, beak open in a call). Moving, it leans into its flight, beats faster and deeper, tucks its legs and streams its
        -- tail, and glides between bursts of beats. While its owner cultivates it rests on the air with its wings folded at its sides, legs tucked,
        -- eyes half closed, and now and then slowly opens its wings high like the sun coming up. Its special, The First Light: it draws its wings
        -- forward round its breast and bows, glowing like a coal (to 0.42); then throws its wings high and wide with a cry (Blasts.FirstLight: a ring of
        -- morning light runs out level round it, a flash of warm light, motes of dawn rising), holds, and settles.
        local DP = {
            FAR = 110, -- studs from the camera past which nobody can see it move: its bones rest
            BONES = {
                "Body", "Chest", "Neck1", "Neck2", "Neck3", "Head", "Jaw", "Crest1", "Crest2",
                "Tail1", "TailFanL", "TailFanR", "TailA1", "TailA2", "TailA3", "TailB1", "TailB2", "TailB3",
                "LegL1", "LegL2", "FootL", "ToesL", "LegR1", "LegR2", "FootR", "ToesR",
            },
            -- each wing's own plane at rest (game axes): elbow, wrist and hand fold in it (dawn_phoenix.py WING_NORMAL_G)
            WING_N = { L = Vector3.new(math.sin(math.rad(40)), math.cos(math.rad(40)), 0), R = Vector3.new(-math.sin(math.rad(40)), math.cos(math.rad(40)), 0) },
            -- lower, sweep, elbow, wrist, tip (radians), each checked in Blender for tears and folds (dawn_phoenix.py FOLD, WRAP)
            FOLD = { 1.0, 0.5, -1.3, 2.45, 0.3 }, -- resting, wings folded at its sides
            WRAP = { 0.55, -0.85, -0.55, -0.45, -0.2 }, -- the special's gathering, wings drawn forward round its breast
            -- stroke stances (up, sweep, elbow, hand, tip, sec): the glide and the proud display (dawn_phoenix.py STANCES)
            GLIDE = { -0.42, -0.08, -0.12, -0.08, -0.12, 0 },
            DISPLAY = { 0.55, -0.12, -0.1, -0.1, -0.2, 0 },
            STRETCH = { 0.75, 0, 0, 0, -0.15, 0 },
            LID_HINGE = { L = Vector3.new(0.8883, -0.1043, -0.4473), R = Vector3.new(0.8883, 0.1043, 0.4473) }, -- both lids of an eye turn on this line
            BLINK_U = math.rad(34),
            BLINK_L = math.rad(11),
            HOVER_LIFT = 0.12, -- metres it hangs above its bind height (its talons hang just off the ground otherwise)
            TUCK = { LegL1 = { 0.45, 0, 0 }, LegR1 = { 0.45, 0, 0 }, LegL2 = { -0.7, 0, 0 }, LegR2 = { -0.7, 0, 0 }, ToesL = { 0.8, 0, 0 }, ToesR = { 0.8, 0, 0 } },
            PREEN = { Neck2 = { -0.2, 0.45, 0 }, Neck3 = { -0.25, 0.5, 0.1 }, Head = { -0.35, 0.45, 0.2 } }, -- to its left; y and z flip for its right
            DISPLAY_BODY = { Chest = { -0.12, 0, 0 }, Neck1 = { 0.1, 0, 0 }, Head = { -0.15, 0, 0 }, Crest1 = { -0.22, 0, 0 }, Crest2 = { -0.15, 0, 0 } },
            GATHER_BODY = { Neck2 = { -0.25, 0, 0 }, Neck3 = { -0.2, 0, 0 }, Head = { 0.15, 0, 0 }, Crest1 = { 0.15, 0, 0 }, Crest2 = { 0.1, 0, 0 } },
            FIDGET_TIME = { turn = 3.2, stretch = 2.2, preen = 2.8, display = 2.6 },
            EMBER = Color3.fromRGB(255, 110, 25), -- deep: pale Neon blooms to white under the game's Bloom
            DAWN = Color3.fromRGB(255, 150, 45),
            GLOW = Color3.fromRGB(255, 140, 60),
            MOTES = { Color3.fromRGB(255, 165, 50), Color3.fromRGB(255, 120, 40), Color3.fromRGB(240, 90, 40) },
        }

        function DP.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        -- the flap through one beat (x 0..1, radians, + up): a quick, strong downstroke (45% of the beat), then a slower recovery
        function DP.stroke(x)
            if x < 0.45 then
                return 0.5 - smoothstep(0, 1, x / 0.45)
            end
            return -0.5 + smoothstep(0, 1, (x - 0.45) / 0.55)
        end

        -- how far into the recovery (0 on the downstroke): the elbow and hand fold back while it lasts
        function DP.recovery(x)
            return if x >= 0.45 then math.sin(math.pi * (x - 0.45) / 0.55) else 0
        end

        -- one wing's four bones and its arm's fan, open (game axes): up raises it, sweep takes it back; elbow, hand and tip fold back in its own plane
        function DP.openWing(tag, w, bend)
            local sg = if tag == "L" then 1 else -1
            local n = DP.WING_N[tag]
            return {
                CFrame.Angles(0, sg * w[2], -sg * w[1]),
                CFrame.fromAxisAngle(n, sg * w[3]),
                CFrame.fromAxisAngle(n, sg * w[4]) * CFrame.Angles(0, 0, sg * bend),
                CFrame.fromAxisAngle(n, sg * w[5]),
                CFrame.Angles(w[6], 0, 0),
            }
        end

        -- the same wing folded (FOLD or WRAP): lowered about the body's long axis, swept, and folded in its own plane
        function DP.foldWing(tag, f)
            local sg = if tag == "L" then 1 else -1
            local n = DP.WING_N[tag]
            return {
                CFrame.fromAxisAngle(n, sg * f[2]) * CFrame.fromAxisAngle(Vector3.zAxis, sg * f[1]),
                CFrame.fromAxisAngle(n, sg * f[3]),
                CFrame.fromAxisAngle(n, sg * f[4]),
                CFrame.fromAxisAngle(n, sg * f[5]),
                CFrame.identity,
            }
        end

        -- its own light and the embers off its crest's tip (both on bones, so they move with it)
        function DP.effects(rig, s)
            s.fxMade = true
            local chest, crest = rig.points.Chest, rig.points.Crest2
            if chest then
                local a = Instance.new("Attachment")
                a.Name = "Glow"
                a.Parent = chest
                local light = Instance.new("PointLight")
                light.Name = "PulseLight"
                light.Color = DP.GLOW
                light.Range = 6 * rig.unit
                light.Brightness = 0.8
                light.Shadows = false
                light.Parent = a
                rig.light = light
            end
            if crest and not DP.reduced() and not (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer) then
                local a = Instance.new("Attachment")
                a.Name = "Embers"
                a.Parent = crest
                local embers = Instance.new("ParticleEmitter")
                embers.Name = "Embers"
                embers.Texture = SPARKLE
                embers.Rate = 2.5
                embers.Lifetime = NumberRange.new(0.6, 1.1)
                embers.Speed = NumberRange.new(0.2 * rig.unit, 0.5 * rig.unit)
                embers.SpreadAngle = Vector2.new(35, 35)
                embers.Acceleration = Vector3.new(0, 0.35 * rig.unit, 0)
                embers.Drag = 1.5
                embers.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
                embers.Color = ColorSequence.new(DP.DAWN, DP.EMBER)
                embers.Transparency = NumberSequence.new(0.15, 1)
                embers.LightEmission = 0.6 -- (full emission on a warm colour piles up toward white)
                embers.LightInfluence = 0
                embers.Parent = a
            end
        end

        local function animateDawnPhoenix(rig, s, moving, fly, nova)
            if not s.fxMade then
                DP.effects(rig, s)
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > DP.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, math.min(rig.deltaTime, 0.1)
            local pace = math.max(moving, fly)
            local owner = rig.owner
            local cultivating = owner ~= nil and owner:GetAttribute("IsCultivating") == true

            -- the special, The First Light: gathering (wings drawn round its breast, bowed, glowing) to 0.42; thrown open; held; settled
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local special = progress > 0
            local gather = smoothstep(0.02, 0.34, progress) * (1 - smoothstep(0.38, 0.45, progress))
            local opened = smoothstep(0.38, 0.46, progress) * (1 - smoothstep(0.78, 0.97, progress))

            -- resting on the air while its owner cultivates: wings folded, now and then a slow sunrise display
            s.rest = (s.rest or 0) + ((if cultivating and not special then 1 else 0) - (s.rest or 0)) * math.min(1, dt * 1.5)
            local rest = smoothstep(0, 1, s.rest)
            s.nextSunrise = s.nextSunrise or t + 6
            if rest < 0.5 then
                s.nextSunrise = math.max(s.nextSunrise, t + 6)
            end
            if t >= s.nextSunrise then
                s.sunriseAt = t
                s.nextSunrise = t + 11 + math.random() * 6
            end
            local sunrise = 0
            if s.sunriseAt and t - s.sunriseAt < 3.6 then
                local a = (t - s.sunriseAt) / 3.6
                sunrise = smoothstep(0, 0.35, a) * (1 - smoothstep(0.7, 1, a)) * rest
            end

            -- now and then, calm: a slow look back over its shoulder, a stretch, a preen, its proud display
            local calm = (1 - pace) * (1 - rest) * (if special then 0 else 1)
            s.nextFidget = s.nextFidget or t + 5
            if t >= s.nextFidget then
                if calm > 0.8 then
                    local r = math.random()
                    s.fidgetKind = if r < 0.3 then "turn" elseif r < 0.55 then "stretch" elseif r < 0.8 then "preen" else "display"
                    s.fidgetAt = t
                    s.fidgetSide = if math.random() < 0.5 then 1 else -1
                    s.nextFidget = t + DP.FIDGET_TIME[s.fidgetKind] + 5 + math.random() * 6
                else
                    s.nextFidget = t + 2
                end
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / DP.FIDGET_TIME[s.fidgetKind], 0, 1) else 1
            local fidget = smoothstep(0, 0.22, env) * (1 - smoothstep(0.78, 1, env)) * calm
            local function kind(name)
                return if s.fidgetKind == name then fidget else 0
            end
            local turn, stretch, preen, display = kind("turn"), kind("stretch"), kind("preen"), kind("display")
            local proud = math.max(display, opened, sunrise)

            -- a glide between bursts of beats while it travels
            s.travel = if pace > 0.6 and not special then (s.travel or 0) + dt else 0
            local wantGlide = if s.travel > 1.5 and (s.travel % 5.4) > 3.4 then 1 else 0
            s.glide = (s.glide or 0) + (wantGlide - (s.glide or 0)) * math.min(1, dt * 2.5)
            local glide = smoothstep(0, 1, s.glide)

            -- the beat: faster and deeper as it travels, still in a glide, a stretch or its display, slow and small as it gathers or rests
            local held = math.max(glide, stretch, proud, rest)
            local rate = 1.25 + 0.75 * pace
            s.beat = ((s.beat or 0) + dt * rate * (1 - 0.6 * held)) % 1
            local amp = (0.85 + 0.3 * pace) * (1 - held) * (1 - 0.7 * gather)
            local flap = DP.stroke(s.beat) * amp - 0.1 * pace
            local lagged = DP.stroke((s.beat - 0.12) % 1) * amp - 0.1 * pace
            local rec = DP.recovery(s.beat) * amp
            local recLag = DP.recovery((s.beat - 0.1) % 1) * amp
            local wingStroke = { flap, 0.12 * rec, 0.32 * rec, 0.5 * recLag, 0.25 * rec - 0.12 * (amp - rec), -0.25 * rec }
            local function toward(target, weight)
                if weight <= 0 then
                    return
                end
                for k = 1, 6 do
                    wingStroke[k] += (target[k] - wingStroke[k]) * weight
                end
            end
            toward(DP.GLIDE, glide)
            toward(DP.STRETCH, stretch)
            toward(DP.DISPLAY, proud)
            local bend = 0.45 * (lagged - flap) -- the hand trailing the arm through the stroke

            -- the body: it rises a little on each downstroke and hangs above its bind height; it leans into its flight, bows as it gathers, swells
            -- its breast in its display
            local want = {}
            local bob = 0.022 * math.sin(2 * math.pi * s.beat + 1.3) * amp + 0.012 * math.sin(t * 1.1)
            local bodyPitch = -0.42 * pace * (1 - rest) - 0.12 * gather + 0.08 * proud + 0.03 * math.sin(t * 0.9)
            addStance(want, { Body = { bodyPitch, 0, 0.03 * math.sin(t * 0.6) * (1 - pace) } }, 1)
            addStance(want, { Chest = { 0.02 * math.sin(t * 1.3), 0, 0 } }, 1)
            -- the neck takes the body's lean and bob back: its head rides steady and level
            addStance(want, { Neck1 = { -0.3 * bodyPitch - 1.2 * bob, 0, 0 }, Neck3 = { -0.3 * bodyPitch + 0.6 * bob, 0, 0 }, Head = { -0.4 * bodyPitch, 0, 0 } }, 1)
            addStance(want, DP.DISPLAY_BODY, proud)
            addStance(want, DP.GATHER_BODY, gather)

            -- its gaze: slow and regal, often at you; a look back over its shoulder; a preen at its shoulder
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 3 + math.random() * 4
                s.atYou = math.random() < 0.45
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.2, (math.random() - 0.5) * 0.3
            end
            local look = (1 - 0.7 * pace) * (1 - math.max(preen, turn, gather, opened)) * (1 - 0.6 * rest)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.9, 0.9) else s.gazeYaw) * look + 1.15 * turn * (s.fidgetSide or 1)
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.2, 0.3) else s.gazePitch) * look
            local lastYaw = s.yaw or 0
            s.yaw = lastYaw + (wantYaw - lastYaw) * math.min(1, dt * 1.6)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 1.6)
            local yawSpeed = math.clamp((s.yaw - lastYaw) / math.max(dt, 1e-3), -3, 3)
            addStance(want, { Neck2 = { 0.05 * s.pitch, 0.25 * s.yaw, 0 }, Neck3 = { 0.1 * s.pitch, 0.32 * s.yaw, 0 }, Head = { 0.3 * s.pitch, 0.43 * s.yaw, 0.08 * s.yaw } }, 1)
            local side = s.fidgetSide or 1
            local nibble = 0.1 * math.sin(t * 13) * preen
            addStance(want, { Neck2 = { DP.PREEN.Neck2[1], DP.PREEN.Neck2[2] * side, 0 }, Neck3 = { DP.PREEN.Neck3[1], DP.PREEN.Neck3[2] * side, DP.PREEN.Neck3[3] * side },
                Head = { DP.PREEN.Head[1] + nibble, DP.PREEN.Head[2] * side, DP.PREEN.Head[3] * side } }, preen)
            addStance(want, { Chest = { -0.06, 0, 0 }, Head = { -0.12, 0, 0 } }, stretch)

            -- its crest: trailing every turn of its head, streaming back as it flies, raised in its display; a breath of air through it
            addStance(want, { Crest1 = { 0.05 * math.sin(t * 1.4) + 0.12 * pace, -0.12 * yawSpeed, 0 },
                Crest2 = { 0.07 * math.sin(t * 1.4 - 0.7) + 0.1 * pace, -0.2 * yawSpeed + 0.05 * math.sin(t * 2.1), 0 } }, 1)

            -- its tail: the two long feathers rippling, a wave running down each; streaming level as it flies; fanned wide in its display
            local wave = 1 + 1.2 * pace
            for k = 1, 3 do
                want["TailA" .. k] = (want["TailA" .. k] or Vector3.zero)
                    + Vector3.new(0.05 * math.sin(t * 1.2 - k * 0.7), 0.1 * wave * math.sin(t * 1.5 - k * 0.8), 0)
                want["TailB" .. k] = (want["TailB" .. k] or Vector3.zero)
                    + Vector3.new(0.05 * math.sin(t * 1.2 - k * 0.7 + 0.6), 0.1 * wave * math.sin(t * 1.5 - k * 0.8 + 0.6), 0)
            end
            local spread = 0.25 * proud - 0.15 * pace + 0.04 * math.sin(t * 0.8)
            addStance(want, { Tail1 = { 0.06 * math.sin(t * 1.1) - 0.3 * pace + 0.1 * gather, 0.06 * math.sin(t * 0.7), 0 },
                TailFanL = { 0, -spread, 0 }, TailFanR = { 0, spread, 0 } }, 1)

            -- its legs: hanging relaxed as it hovers, toes half curled; tucked up as it flies, rests or gathers
            addStance(want, { LegL1 = { 0.05 * math.sin(t * 1.1), 0, 0 }, LegR1 = { 0.05 * math.sin(t * 1.1 + 0.5), 0, 0 }, ToesL = { 0.3, 0, 0 }, ToesR = { 0.3, 0, 0 } }, 1)
            addStance(want, DP.TUCK, math.max(pace, rest, gather))

            -- its beak: open in its call (display, the special's cry), a little as it preens
            local call = math.max(proud * (if display > 0 or opened > 0 then 1 else 0.3), 0.3 * preen)
            addStance(want, { Jaw = { -0.35 * call, 0, 0 } }, 1)

            local lift = (DP.HOVER_LIFT + bob - 0.04 * gather) * u
            for _, name in DP.BONES do
                local a = want[name] or Vector3.zero
                pose(m[name], CFrame.new(0, if name == "Body" then lift else 0, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- its wings: open (the stroke, its stances), folded at its sides as it rests, drawn round its breast as it gathers
            local fold = rest * (1 - sunrise)
            for _, tag in { "L", "R" } do
                local open = DP.openWing(tag, wingStroke, bend)
                local folded = DP.foldWing(tag, DP.FOLD)
                local wrapped = DP.foldWing(tag, DP.WRAP)
                local bones = { "Wing" .. tag .. "1", "Wing" .. tag .. "2", "Wing" .. tag .. "3", "Wing" .. tag .. "4", "Wing" .. tag .. "Sec" }
                for k, name in bones do
                    pose(m[name], open[k]:Lerp(folded[k], fold):Lerp(wrapped[k], gather))
                end
            end

            -- its eyes: a blink now and then; half closed, calm, as it rests
            s.nextBlink = s.nextBlink or t + 2
            if t >= s.nextBlink then
                s.blinkAt = t
                s.nextBlink = t + 2.5 + math.random() * 3.5
            end
            local blink = if s.blinkAt and t - s.blinkAt < 0.2 then math.sin(math.pi * (t - s.blinkAt) / 0.2) else 0
            local shut = math.max(blink, 0.4 * rest * (1 - sunrise), 0.5 * gather)
            for _, tag in { "L", "R" } do
                local hinge = DP.LID_HINGE[tag]
                pose(m["LidU" .. tag], CFrame.fromAxisAngle(hinge, -DP.BLINK_U * shut))
                pose(m["LidL" .. tag], CFrame.fromAxisAngle(hinge, DP.BLINK_L * shut))
            end
        end

        -- The First Light (animateDawnPhoenix, the burst): its wings thrown open, a ring of morning light runs out level round it like the first light
        -- along the horizon, a warm flash, motes of dawn rising and drifting. (A bone's TransformedWorldCFrame is where it is drawn.)
        function Blasts.FirstLight(rig, fx)
            local u = rig.unit
            local chest = rig.points.Chest
            local centre = if chest then chest.TransformedWorldCFrame.Position else fx.origin
            local reduced = DP.reduced() or (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer)

            local segments = if reduced then 14 else 24
            local r0, r1 = 0.45 * u, 4.4 * u
            for k = 1, segments do
                local a = k / segments * 2 * math.pi
                local out = Vector3.new(math.cos(a), 0, math.sin(a))
                local function at(r)
                    local here = centre + out * r
                    return CFrame.lookAt(here, here + out:Cross(Vector3.yAxis))
                end
                local bead = fx.neon(Vector3.new(0.07 * u, 0.05 * u, 2 * math.pi * r0 / segments * 0.9), at(r0), if k % 2 == 0 then DP.DAWN else DP.EMBER)
                bead.Transparency = 0.15
                TweenService:Create(bead, TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                    CFrame = at(r1),
                    Size = Vector3.new(0.03 * u, 0.02 * u, 2 * math.pi * r1 / segments * 0.85),
                    Transparency = 1,
                }):Play()
            end

            -- (a bigger, brighter flash and a 2.5 light washed the bird pale yellow under Bloom, seen in Play)
            local flash = fx.neon(Vector3.one * 0.15 * u, CFrame.new(centre), DP.EMBER)
            flash.Shape = Enum.PartType.Ball
            flash.Transparency = 0.6
            TweenService:Create(flash, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 0.9 * u, Transparency = 1 }):Play()
            if not reduced then
                local light = Instance.new("PointLight")
                light.Color = DP.GLOW
                light.Range = 12 * u
                light.Brightness = 1.4
                light.Shadows = false
                light.Parent = flash
                TweenService:Create(light, TweenInfo.new(1.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 }):Play()
            end

            for k = 1, (if reduced then 6 else 14) do
                local start = centre + Vector3.new(math.random() - 0.5, math.random() * 0.4, math.random() - 0.5) * u
                local mote = fx.neon(Vector3.one * 0.07 * u, CFrame.new(start), DP.MOTES[(k % #DP.MOTES) + 1])
                mote.Shape = Enum.PartType.Ball
                mote.Transparency = 0.2
                local drift = Vector3.new(math.random() - 0.5, 1.6 + math.random() * 0.9, math.random() - 0.5) * u
                TweenService:Create(mote, TweenInfo.new(1.2 + math.random() * 0.3, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), {
                    CFrame = CFrame.new(start + drift),
                    Size = Vector3.one * 0.03 * u,
                    Transparency = 1,
                }):Play()
            end
            if rig.burst then
                rig.burst:Emit(if reduced then 8 else 16)
            end
        end

        PetRig.Profiles.DawnPhoenix = {
            Skinned = true,
            LightScale = 0.6, -- a warm glow round it, not a lamp
            Bones = {
                "Body", "Chest", "Neck1", "Neck2", "Neck3", "Head", "Jaw", "Crest1", "Crest2", "LidUL", "LidLL", "LidUR", "LidLR",
                "WingL1", "WingL2", "WingL3", "WingL4", "WingLSec", "WingR1", "WingR2", "WingR3", "WingR4", "WingRSec",
                "Tail1", "TailFanL", "TailFanR", "TailA1", "TailA2", "TailA3", "TailB1", "TailB2", "TailB3",
                "LegL1", "LegL2", "FootL", "ToesL", "LegR1", "LegR2", "FootR", "ToesR",
            },
            -- (only bones that carry weight: the importer drops a weightless bone, so the tips' own bones are not read)
            Points = { "Chest", "Head", "Crest2", "WingL4", "WingR4", "TailA3", "TailB3" },
            Effects = {
                Burst = "Body",
                Trail = { "TailA3", "TailB3" }, -- two threads of light off its long tail feathers in flight
                TrailWidth = 0.05,
                TrailTaper = true,
                Blast = "FirstLight",
                NovaLight = 0.8,
            },
            Colors = { -- (Sun and Orange colour its burst sparks and its tail's threads: deep, so they never bloom white)
                Gold = Color3.fromRGB(255, 160, 50),
                Amber = Color3.fromRGB(150, 40, 20),
                Orange = Color3.fromRGB(240, 90, 20),
                Sun = Color3.fromRGB(255, 145, 50),
                Ivory = Color3.fromRGB(255, 232, 200),
            },
            Animate = animateDawnPhoenix,
        }
    end
end
