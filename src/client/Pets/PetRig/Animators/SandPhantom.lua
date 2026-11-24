-- The SandPhantom pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep, addStance, dropToGround = K.PetRig, K.pose, K.smoothstep, K.addStance, K.dropToGround

    local animateSandPhantom, SAND_AWAY, SAND_BONES, SAND_DUSK, SAND_GOLD, SAND_PALE, SAND_SOLE -- animateSandPhantom's section below (its own locals stay in its block)
    do

        -- The Sand Phantom (skinned): a desert jerboa spirit. It hops on its long hind legs, both feet together, its long tail held out behind it for balance;
        -- still, it sits up tall to look about, freezes when something catches its eye, or washes its face with its tiny forepaws. Its gaze darts, quick and
        -- shy; its huge ears turn on their own; fine sand streams off its tail's brush and its ears as if blown by a wind only it feels.
        local SAND_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        SAND_SOLE = 0.2988 -- metres from the middle of its box down to its feet: it sits on the ground
        local SAND_LID_HINGE = { L = Vector3.new(0.765, -0.0686, -0.6403), R = Vector3.new(0.765, 0.0686, 0.6403) } -- both lids of an eye turn on this line
        local SAND_BLINK_UPPER, SAND_BLINK_LOWER = math.rad(62), math.rad(28)
        SAND_GOLD, SAND_PALE, SAND_DUSK = Color3.fromRGB(226, 182, 110), Color3.fromRGB(246, 226, 180), Color3.fromRGB(176, 124, 70)
        local SAND_HOP = 0.16 -- metres it rises at the top of a hop
        SAND_AWAY = 0.8 -- metres to its right it re-forms in its special: clear of where it stood, and still in a following camera's view

        local function sandHind(t, s, h, f)
            local out = {}
            for _, side in { "L", "R" } do
                out["LegB" .. side .. "1"], out["LegB" .. side .. "2"], out["LegB" .. side .. "3"], out["FootB" .. side] = { t, 0, 0 }, { s, 0, 0 }, { h, 0, 0 }, { f, 0, 0 }
            end
            return out
        end

        local function sandStance(base, hind)
            for bone, a in hind do
                base[bone] = a
            end
            return base
        end

        -- its stances, each searched in Blender against the ground and for torn skin: the same numbers as sand_phantom.py's CROUCH, SPRING and UPRIGHT
        local SAND_CROUCH = sandStance({ Body = { -0.064, 0, 0 } }, sandHind(0.308, -0.47, 0.062, 0.3))
        local SAND_CROUCH_DROP = 0.025
        local SAND_SPRING = sandStance({ Body = { 0.1, 0, 0 } }, sandHind(-0.6, 0.6, -0.4, -0.5)) -- only ever with the hop's lift, which keeps its feet clear
        local SAND_UPRIGHT = sandStance({ Body = { 0.261, 0, 0 }, Chest = { 0.1, 0, 0 }, Head = { -0.2, 0, 0 } }, sandHind(0.208, -0.117, -0.496, 0.019))
        local SAND_UPRIGHT_RISE = 0.046
        local SAND_GROOM = { ArmL1 = { 0.6, 0, 0 }, ArmL2 = { -0.6, 0, 0 }, ArmR1 = { 0.6, 0, 0 }, ArmR2 = { -0.6, 0, 0 }, Head = { 0.25, 0, 0 } }
        for k = 1, 6 do
            SAND_SPRING["Tail" .. k] = { 0.05, 0, 0 }
        end

        local function sandBones()
            local bones = { "Hips", "Body", "Chest", "Neck", "Head", "EyeL", "EyeR", "EarL", "EarR", "ArmL1", "ArmL2", "HandL", "ArmR1", "ArmR2", "HandR" }
            for k = 1, 6 do
                table.insert(bones, "Tail" .. k)
            end
            for _, side in { "L", "R" } do
                for k = 1, 3 do
                    table.insert(bones, "LegB" .. side .. k)
                end
                table.insert(bones, "FootB" .. side)
            end
            return bones
        end
        SAND_BONES = sandBones() -- every bone its stances pose (the lids turn on their hinges on their own)

        local function sandEmitter(parent, rate, size, speed, unit)
            local sand = Instance.new("ParticleEmitter")
            sand.Name = "BlowingSand"
            sand.Texture = "rbxasset://textures/particles/smoke_main.dds"
            sand.Rate = rate
            sand.Lifetime = NumberRange.new(0.6, 1.1)
            sand.Speed = NumberRange.new(speed * 0.5 * unit, speed * unit)
            sand.SpreadAngle = Vector2.new(25, 25)
            sand.EmissionDirection = Enum.NormalId.Back
            sand.Acceleration = Vector3.new(0, -0.15 * unit, 0)
            sand.Drag = 1.2
            sand.Rotation = NumberRange.new(0, 360)
            sand.RotSpeed = NumberRange.new(-40, 40)
            sand.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, size * unit), NumberSequenceKeypoint.new(1, size * 2.5 * unit) })
            sand.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(1, 1) })
            sand.Color = ColorSequence.new(SAND_PALE, SAND_GOLD)
            sand.LightEmission = 0.1
            sand.LightInfluence = 0.8
            sand.Parent = parent
            return sand
        end

        -- sand streaming off its tail's brush and its ears; and, kept off until its special, the sand it blows away into
        local function sandStreams(rig, s)
            s.sandMade = true
            s.streams = {}
            for name, rate in { Tail6 = 6, EarL = 1.5, EarR = 1.5 } do
                local point = rig.points[name]
                if point then
                    table.insert(s.streams, sandEmitter(point, rate, 0.025, 0.18, rig.unit))
                end
            end
            local hips = rig.points.Hips
            if hips then
                local blow = sandEmitter(hips, 90, 0.07, 0.9, rig.unit)
                blow.Name = "Dissolve"
                blow.EmissionDirection = Enum.NormalId.Right
                blow.SpreadAngle = Vector2.new(50, 50)
                blow.Lifetime = NumberRange.new(0.5, 0.9)
                blow.Shape = Enum.ParticleEmitterShape.Sphere
                blow.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(0.6, 0.35), NumberSequenceKeypoint.new(1, 1) })
                blow.Color = ColorSequence.new(SAND_GOLD, SAND_DUSK)
                blow.LightInfluence = 0.25
                blow.Enabled = false
                s.dissolve = blow
            end
        end

        -- its skin and the glints in its eyes go together: 0, all there; 1, gone into sand
        local function sandGone(rig, s, gone)
            if s.gone == gone then
                return
            end
            s.gone = gone
            for _, key in { "Body", "Glints" } do
                local part = rig.parts[key]
                if part then
                    part.Transparency = gone
                end
            end
            for _, stream in s.streams or {} do
                stream.Enabled = gone < 0.5
            end
        end

        function animateSandPhantom(rig, s, moving, fly, nova)
            if not s.sandMade then
                sandStreams(rig, s)
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime

            -- the special, Mirage: it sits up tall and stares at you (to 0.18); it blows away downwind as sand and is gone (0.2-0.38); a dust devil spins up a
            -- little to its right (Blasts.Mirage, at 0.42) and it re-forms inside it (0.6-0.72), shakes the sand off (0.72-0.8) and hops back (0.8-1)
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local stare = smoothstep(0.0, 0.14, progress) * (1 - smoothstep(0.34, 0.4, progress))
            local gone = smoothstep(0.2, 0.36, progress) * (1 - smoothstep(0.6, 0.72, progress))
            local shake = if progress > 0.72 and progress < 0.8 then math.sin(math.pi * (progress - 0.72) / 0.08) else 0
            local away = if progress < 0.4 then 0 elseif progress < 0.8 then 1 else 1 - smoothstep(0.8, 1.0, progress)
            local backHop = if progress > 0.8 and progress < 1 then math.abs(math.sin(math.pi * 2 * (progress - 0.8) / 0.2)) else 0
            -- (before the far check: it must come back whether or not anyone is watching)
            sandGone(rig, s, gone)
            if s.dissolve then
                s.dissolve.Enabled = progress > 0.18 and progress < 0.36
            end

            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > SAND_FAR then
                return
            end
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, SAND_SOLE)
            local special = progress > 0

            -- still, now and then it sits up tall to look about, freezes, or washes its face
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            s.nextIdle = s.nextIdle or t + 2
            if s.still > 1.5 and t >= s.nextIdle then
                local r = math.random()
                s.idleKind = if r < 0.45 then "up" elseif r < 0.75 then "freeze" else "groom"
                s.idleAt = t
                s.idleFor = if s.idleKind == "groom" then 2.2 elseif s.idleKind == "up" then 2.6 else 1.2
                s.nextIdle = t + s.idleFor + 1.5 + math.random() * 3
            end
            local idleEnv = if s.idleAt and pace < 0.05 and not special then math.clamp((t - s.idleAt) / s.idleFor, 0, 1) else 1
            local idle = math.min(1, math.sin(math.pi * idleEnv) * 2.2)
            local up = math.max(if s.idleKind == "up" then idle else 0, stare)
            local groom = if s.idleKind == "groom" then idle else 0
            local frozen = if s.idleKind == "freeze" then idle else 0

            -- the hop: both feet together, gathered on the ground, flung back in the air; in flight a long stretched leap; hopping back after its special
            s.hopPhase = (s.hopPhase or 0) + dt * (11 * moving + 6 * fly)
            local air = math.max(0, math.sin(s.hopPhase)) * moving * (1 - fly)
            local land = math.max(0, -math.sin(s.hopPhase)) * moving * (1 - fly)
            local want = {}
            addStance(want, SAND_CROUCH, math.min(1, land + 0.4 * (1 - backHop) * smoothstep(0.78, 0.82, progress) * (if progress < 1 then 1 else 0)))
            addStance(want, SAND_SPRING, math.min(1, air + 0.85 * fly + backHop))
            addStance(want, SAND_UPRIGHT, up * (1 - pace))
            addStance(want, SAND_GROOM, groom * (0.75 + 0.25 * math.sin(t * 14)))

            -- the body: quick, light breathing; banking on turns; shaking the sand off
            local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.18, 0.18) - (s.bank or 0)) * math.min(1, dt * 3)
            local breath = math.sin(t * 4.5) * (1 - frozen)
            local shiver = 0.25 * shake * math.sin(t * 45)
            addStance(want, { Hips = { 0, shiver * 0.4, s.bank * pace + shiver }, Chest = { 0.02 * breath, 0, -shiver * 0.8 }, Head = { 0, 0, shiver * 0.6 } }, 1)

            -- its gaze: darting, quick and shy; it stares at you before it vanishes; frozen, it holds still
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze and frozen < 0.1 then
                s.nextGaze = t + 0.4 + math.random() * 1.1
                s.atYou = math.random() < 0.35
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.4, (math.random() - 0.5) * 0.4
            end
            local look = math.max(stare, 0)
            local wantYaw = if s.atYou or look > 0 then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.9, 0.9) else s.gazeYaw
            local wantPitch = if s.atYou or look > 0 then math.clamp(toYou.Y * 0.6, -0.3, 0.4) else s.gazePitch
            local calm = (1 - 0.6 * pace) * (1 - groom)
            s.yaw = (s.yaw or 0) + (wantYaw * calm - (s.yaw or 0)) * math.min(1, dt * 12)
            s.pitch = (s.pitch or 0) + (wantPitch * calm - (s.pitch or 0)) * math.min(1, dt * 12)
            addStance(want, {
                Neck = { 0.3 * s.pitch, 0.4 * s.yaw, 0 }, Head = { 0.45 * s.pitch, 0.55 * s.yaw, 0.12 * s.yaw },
                EyeL = { 0.2 * s.pitch, 0.2 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.2 * s.yaw, 0 },
            }, 1)

            -- the ears: huge, each turning on its own; pricked up and forward when it freezes or stares; laid back in the hop and the leap
            for _, side in { "L", "R" } do
                local sign = if side == "L" then 1 else -1
                local swivel = math.max(0, math.sin(t * 0.9 + (if side == "L" then 0 else 2.2))) ^ 6
                local prick = math.max(frozen, stare)
                addStance(want, { ["Ear" .. side] = { -0.2 * swivel + 0.15 * prick - 0.35 * math.max(air, fly), sign * (0.4 * swivel * (1 - prick) + 0.2 * math.max(air, fly)), 0 } }, 1)
            end

            -- the tail: held out behind it, swaying; it swings up as it lands and down as it springs, balancing each hop; still when it freezes
            for k = 1, 6 do
                local sway = (0.03 + 0.04 * k / 6) * math.sin(t * 1.3 - k * 0.5) * (1 - frozen)
                local balance = (0.12 * land - 0.08 * air) * (k <= 2 and 1 or 0.4)
                addStance(want, { ["Tail" .. k] = { balance + 0.02 * math.sin(t * 0.8 - k * 0.6), sway, 0 } }, 1)
            end

            local awayX = SAND_AWAY * away
            for _, name in SAND_BONES do
                local a = want[name] or Vector3.zero
                local offset = Vector3.zero
                if name == "Hips" then
                    local lift = SAND_HOP * air + 0.75 * SAND_HOP * backHop - SAND_CROUCH_DROP * land + SAND_UPRIGHT_RISE * up * (1 - pace)
                    offset = Vector3.new(awayX * u, lift * u - drop, 0)
                end
                pose(m[name], CFrame.new(offset) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- the eyes: quick blinks, wide as it stares, never while frozen
            s.nextBlink = s.nextBlink or t + 2
            local blink = 0
            if t >= s.nextBlink and frozen < 0.1 then
                local a = (t - s.nextBlink) / 0.14
                if a >= 1 then
                    s.nextBlink = t + 1.8 + math.random() * 3
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local close = blink * (1 - stare)
            local upper = SAND_BLINK_UPPER * close - math.rad(6) * math.max(stare, frozen)
            local lower = SAND_BLINK_LOWER * close - math.rad(4) * math.max(stare, frozen)
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(SAND_LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(SAND_LID_HINGE[side], lower))
            end
        end
    end

    return { animateSandPhantom = animateSandPhantom, SAND_AWAY = SAND_AWAY, SAND_BONES = SAND_BONES, SAND_DUSK = SAND_DUSK, SAND_GOLD = SAND_GOLD, SAND_PALE = SAND_PALE, SAND_SOLE = SAND_SOLE }
end
