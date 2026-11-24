-- The WindSprite pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep = K.PetRig, K.pose, K.smoothstep

    local animateWindSprite, WIND_FAR -- animateWindSprite's section below (its own locals stay in its block)
    do

        -- The Wind Sprite is one smooth skin on a skeleton, so its joints are Bones (PetRig.buildSkinned). Axes as everywhere: -Z ahead, +X to its right; its left is -X.
        local WIND_LID_HINGE = { L = Vector3.new(0.9574, -0.1218, -0.2618), R = Vector3.new(0.9574, 0.1218, 0.2618) } -- both lids of an eye turn on this line
        local WIND_BLINK_UPPER, WIND_BLINK_LOWER = math.rad(72), math.rad(22)
        local WIND_CREST_TURN = math.rad(35) -- both hair bones turned at rest: built side-on its curl reads from the front as a stump; turned, as a curled topknot
        WIND_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest

        local function windLids(m, side, upper, lower)
            local hinge = WIND_LID_HINGE[side]
            pose(m["LidU" .. side], CFrame.fromAxisAngle(hinge, -upper))
            pose(m["LidL" .. side], CFrame.fromAxisAngle(hinge, lower))
        end

        function animateWindSprite(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > WIND_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special: it fills its cheeks, leaning back, then blows the gale out at the moment of the burst
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local inhale = smoothstep(0, 0.36, progress) * (1 - smoothstep(0.41, 0.47, progress))
            local blow = smoothstep(0.4, 0.45, progress) * (1 - smoothstep(0.74, 0.92, progress))

            -- blinks, now and then a double
            s.nextBlink = s.nextBlink or t + 1 + math.random() * 2
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.17
                if a >= 1 then
                    s.nextBlink = t + (if math.random() < 0.18 then 0.12 else 2.2 + math.random() * 3.6)
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end

            -- its eyes dart about; its head follows them, late
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 0.8 + math.random() * 2.4
                s.gazeYawTo, s.gazePitchTo = (math.random() - 0.5) * 0.62, (math.random() - 0.45) * 0.24
            end
            local calm = (1 - pace * 0.7) * (1 - nova)
            s.gazeYaw = (s.gazeYaw or 0) + ((s.gazeYawTo or 0) * calm - (s.gazeYaw or 0)) * math.min(1, dt * 24)
            s.gazePitch = (s.gazePitch or 0) + ((s.gazePitchTo or 0) * calm - (s.gazePitch or 0)) * math.min(1, dt * 24)
            s.headYaw = (s.headYaw or 0) + (s.gazeYaw * 0.65 - (s.headYaw or 0)) * math.min(1, dt * 3.5)

            -- the look it gets when it is up to something: a raised brow, narrowed eyes, a crooked smile
            s.nextSly = s.nextSly or t + 5 + math.random() * 6
            local sly = 0
            if t >= s.nextSly then
                local a = (t - s.nextSly) / 2.6
                if a >= 1 then
                    s.nextSly = t + 7 + math.random() * 9
                    s.slySide = if math.random() < 0.5 then 1 else -1
                else
                    sly = smoothstep(0, 0.14, a) * (1 - smoothstep(0.82, 1, a))
                end
            end
            sly *= (1 - nova)
            local slySide = s.slySide or 1

            -- every so often it reaches out with one sleeve and tugs, twice, to get your attention
            s.nextTug = s.nextTug or t + 8 + math.random() * 8
            local reach, tug, tugSide = 0, 0, s.tugSide or 1
            if t >= s.nextTug then
                local a = (t - s.nextTug) / 2.1
                if a >= 1 then
                    s.nextTug = t + 14 + math.random() * 12
                    s.tugSide = -tugSide
                elseif pace < 0.25 and nova == 0 then
                    reach = smoothstep(0, 0.2, a) * (1 - smoothstep(0.82, 1, a))
                    tug = reach * math.max(0, math.sin((a - 0.22) * math.pi * 2 * 3.2)) * (if a > 0.22 and a < 0.85 then 1 else 0)
                end
            end
            local tugBody = reach * tugSide

            -- body and head
            local hover = 0.03 * math.sin(t * 1.9) + 0.012 * math.sin(t * 3.3 + 1) + 0.03 * fly + 0.2 * nova
            pose(m.Body, CFrame.new(0, hover * u, 0)
                * CFrame.Angles(0.03 * math.sin(t * 1.9 - 0.7) - 0.26 * moving - 0.5 * fly + 0.3 * inhale - 0.2 * blow - 0.1 * tug,
                    0.05 * math.sin(t * 0.43) + 0.12 * tugBody,
                    0.035 * math.sin(t * 0.71) - 0.09 * tugBody))
            pose(m.Head, CFrame.Angles(0.04 * math.sin(t * 1.9 - 1.6) + s.gazePitch * 0.4 + 0.14 * moving + 0.3 * fly - 0.12 * inhale + 0.2 * blow,
                s.headYaw + 0.2 * tugBody, 0.05 * math.sin(t * 0.37) * calm - 0.1 * tugBody + 0.07 * sly * slySide))

            -- the face
            local gazePitch = s.gazePitch
            local squeeze = math.max(blink, 0.82 * blow)
            local rest = math.rad(6 - 8 * inhale + 14 * sly + 5 * tug)
            local upper = rest + (WIND_BLINK_UPPER - rest) * squeeze - gazePitch * 0.35
            local lower = math.rad(7) * sly + WIND_BLINK_LOWER * squeeze
            for _, side in { "L", "R" } do
                pose(m["Eye" .. side], CFrame.Angles(gazePitch, s.gazeYaw, 0))
                windLids(m, side, upper, lower)
            end
            local browL = 0.008 * sly * (if slySide > 0 then 1.5 else -0.4) + 0.012 * inhale - 0.012 * blow
            local browR = 0.008 * sly * (if slySide < 0 then 1.5 else -0.4) + 0.012 * inhale - 0.012 * blow
            pose(m.BrowL, CFrame.new(0, browL * u, 0))
            pose(m.BrowR, CFrame.new(0, browR * u, 0))
            local pucker = math.max(inhale * 0.55, blow)
            pose(m.Smile, CFrame.new(0.006 * sly * slySide * u, 0.004 * sly * u, 0.03 * pucker * u) * CFrame.Angles(0, 0, 0.14 * sly * slySide))
            pose(m.Blow, CFrame.new(0, 0, -0.036 * pucker * u))
            local puff = inhale + 0.45 * blow
            pose(m.CheekL, CFrame.new(-0.032 * puff * u, 0, -0.026 * puff * u))
            pose(m.CheekR, CFrame.new(0.032 * puff * u, 0, -0.026 * puff * u))

            -- ears and hair take the wind
            for _, side in { "L", "R" } do
                local sign = if side == "L" then -1 else 1
                local offset = if side == "L" then 0 else 2.3
                local flick = math.max(0, math.sin(t * 1.1 + offset)) ^ 14
                pose(m["Ear" .. side], CFrame.Angles(0.38 * pace + 0.35 * blow + 0.04 * math.sin(t * 2.1 + offset), 0,
                    sign * (0.05 * math.sin(t * 0.9 + offset) + 0.32 * flick + 0.22 * inhale - 0.14 * pace)))
            end
            pose(m.Crest1, CFrame.Angles(0.05 * math.sin(t * 1.4) + 0.2 * pace + 0.3 * blow, WIND_CREST_TURN, 0.05 * math.sin(t * 0.9)))
            pose(m.Crest2, CFrame.Angles(0.09 * math.sin(t * 1.4 - 0.9) + 0.26 * pace + 0.4 * blow, WIND_CREST_TURN, 0.08 * math.sin(t * 0.9 - 1)))

            -- the sleeves: trailing when it flies, and the tug
            for _, side in { "L", "R" } do
                local sign = if side == "L" then -1 else 1
                local mine = if (side == "L") == (tugSide < 0) then 1 else 0
                local idle = 0.06 * math.sin(t * 1.9 - 1 + sign)
                local lift = mine * reach * 1.15 - mine * tug * 0.42
                local trail = -0.75 * moving - 1.05 * fly + 0.5 * inhale - 0.6 * blow
                pose(m["Arm" .. side .. "1"], CFrame.Angles(idle + trail + lift, sign * -0.35 * mine * reach, sign * 0.1 * math.sin(t * 1.3) * (1 - pace)))
                pose(m["Arm" .. side .. "2"], CFrame.Angles(idle * 0.7 + trail * 0.45 + mine * reach * 0.45 - mine * tug * 0.3, 0, 0))
            end
            pose(m.Tassel, CFrame.Angles(-0.42 * pace - 0.5 * blow + 0.08 * math.sin(t * 1.9 - 1.4) + 0.3 * tug, 0, 0.1 * math.sin(t * 1.17)))

            -- its wings flutter all the time, too fast to count
            s.flap = (s.flap or 0) + dt * (42 + 14 * moving + 22 * fly + 18 * nova)
            local amplitude = 0.085 + 0.2 * moving + 0.36 * fly + 0.42 * nova
            local beat = amplitude * math.sin(s.flap)
            local flex = amplitude * 0.75 * math.sin(s.flap - 1)
            local rise = 0.05 + 0.08 * fly + 0.22 * nova
            local sweep = 0.22 * moving + 0.42 * fly - 0.2 * inhale
            pose(m.WingL, CFrame.Angles(0, -sweep, -(rise + beat)))
            pose(m.WingR, CFrame.Angles(0, sweep, rise + beat))
            pose(m.WingMidL, CFrame.Angles(0, 0, -flex))
            pose(m.WingMidR, CFrame.Angles(0, 0, flex))

            -- the curl: a wave running down it; speed and the blow unwind it, and an in-breath winds it tight
            local open = math.rad(10) * moving + math.rad(15) * fly + math.rad(17) * blow - math.rad(4) * inhale
            for k = 1, 7 do
                local f = k / 7
                pose(m["Tail" .. k], CFrame.Angles(open + 0.05 * (0.4 + f) * math.sin(t * 1.6 - k * 0.6),
                    0.045 * (0.5 + f) * (1 + moving) * math.sin(t * 1.15 - k * 0.5), 0.025 * math.sin(t * 0.8 - k * 0.45)))
            end
            pose(m.TailTip, CFrame.Angles(open + 0.1 * math.sin(t * 1.6 - 5), 0, 0.05 * math.sin(t * 2.1)))
        end
    end

    return { animateWindSprite = animateWindSprite, WIND_FAR = WIND_FAR }
end
