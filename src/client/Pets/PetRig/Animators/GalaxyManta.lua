-- The GalaxyManta pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep, WIND_FAR = K.PetRig, K.pose, K.smoothstep, K.WIND_FAR

    local animateGalaxyManta -- animateGalaxyManta's section below (its own locals stay in its block)
    do

        -- The Galaxy Manta (a skinned pet, like the Wind Sprite): waves run out along its wings and back across them; a little galaxy turns under it, on its own bones, so
        -- the body can bank and roll over it. Rings turning at slightly different speeds wind and unwind the arms.
        local MANTA_SPAN = { 0.10, 0.13, 0.17, 0.2 }

        function animateGalaxyManta(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > WIND_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special: it rears until the galaxy faces the world, gathering, then sweeps down as it is thrown open
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local rear = smoothstep(0, 0.3, progress) * (1 - smoothstep(0.62, 0.95, progress))
            local gather = smoothstep(0.08, 0.4, progress) * (1 - smoothstep(0.42, 0.47, progress))
            local sweep = smoothstep(0.41, 0.46, progress) * (1 - smoothstep(0.52, 0.85, progress))

            -- it leans into its turns, a wing dropping
            local look = rig.rootPart.CFrame.LookVector
            local heading = math.atan2(-look.X, -look.Z)
            local turned = heading - (s.heading or heading)
            turned = (turned + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            local turnRate = if dt > 0 then turned / dt else 0
            s.bank = (s.bank or 0) + (math.clamp(turnRate * 0.3, -0.6, 0.6) - (s.bank or 0)) * math.min(1, dt * 3)

            -- now and then, for no reason but joy, a slow barrel roll
            s.nextRoll = s.nextRoll or t + 9 + math.random() * 10
            local rollAngle, rollLift = 0, 0
            if t >= s.nextRoll then
                local a = (t - s.nextRoll) / 3.2
                if a >= 1 then
                    s.nextRoll = t + 18 + math.random() * 16
                    s.rollSide = if math.random() < 0.5 then 1 else -1
                elseif pace < 0.25 and nova == 0 then
                    rollAngle = (s.rollSide or 1) * 2 * math.pi * smoothstep(0.05, 0.95, a)
                    rollLift = math.sin(math.pi * a)
                else
                    s.nextRoll = t + 4
                end
            end
            local calm = 1 - 0.75 * rollLift

            -- every so often it opens its mouth and spreads its horn fins, feeding on the dark
            s.nextFeed = s.nextFeed or t + 6 + math.random() * 8
            local feed = 0
            if t >= s.nextFeed then
                local a = (t - s.nextFeed) / 2.8
                if a >= 1 then
                    s.nextFeed = t + 13 + math.random() * 12
                else
                    feed = smoothstep(0, 0.22, a) * (1 - smoothstep(0.72, 1, a))
                end
            end
            local open = math.max(feed * (1 - pace), 0.8 * rear)

            s.flap = (s.flap or 0) + dt * (1.5 + 0.9 * moving + 1.7 * fly + 0.8 * sweep - 0.7 * gather)
            local flap = s.flap
            local hover = -0.035 * math.sin(flap + 0.7) + 0.02 * math.sin(t * 0.61) + 0.05 * fly + 0.45 * rollLift + 0.32 * rear
            pose(m.Body, CFrame.new(0, hover * u, 0)
                * CFrame.Angles(0.05 * math.sin(flap + 1.6) - 0.13 * moving - 0.24 * fly + 1.08 * rear - 0.32 * sweep, 0, s.bank + rollAngle))
            pose(m.Head, CFrame.Angles(0.035 * math.sin(flap + 0.8) + 0.06 * pace - 0.3 * rear, 0.05 * math.sin(t * 0.37), 0))

            -- the wings: each joint a little behind the last, so the beat travels out to the tip; the back of the wing follows the front
            local stroke = (0.9 + 0.35 * moving + 0.2 * fly) * calm
            local back = 0.2 * moving + 0.42 * fly - 0.2 * gather
            for k = 1, 4 do
                local beat = stroke * MANTA_SPAN[k] * math.sin(flap - k * 0.55)
                local lift = (if k == 1 then 0.1 else 0.05) * (1 - pace) * 0.4 + 0.2 * gather + 0.05 * rear - 0.3 * sweep * (k + 1) / 3
                local swing = if k == 1 then back else 0
                pose(m["WingL" .. k], CFrame.Angles(0, swing, -(beat + lift)))
                pose(m["WingR" .. k], CFrame.Angles(0, -swing, beat + lift))
                local fold = (0.12 + 0.05 * k) * math.sin(flap - k * 0.55 - 1.3) * calm + 0.14 * moving + 0.2 * fly - 0.2 * gather
                pose(m["WingRearL" .. k], CFrame.Angles(fold, 0, 0))
                pose(m["WingRearR" .. k], CFrame.Angles(fold, 0, 0))
            end

            -- the eyes turn slowly, and old: an animal watching, not a toy
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2.5 + math.random() * 4
                s.gazeTo = (math.random() - 0.5) * 0.5
            end
            s.gaze = (s.gaze or 0) + ((s.gazeTo or 0) - (s.gaze or 0)) * math.min(1, dt * 3)
            pose(m.EyeL, CFrame.Angles(0, s.gaze, 0))
            pose(m.EyeR, CFrame.Angles(0, s.gaze, 0))

            pose(m.Smile, CFrame.new(0, 0, 0.03 * open * u))
            pose(m.Mouth, CFrame.new(0, 0, -0.036 * open * u))

            -- the horn fins furl and open; they spread as it feeds and stream back at speed
            for k = 1, 3 do
                local sway = 0.06 * math.sin(t * 0.9 - k * 0.7)
                local spread = 0.2 * open - 0.13 * k * pace * 0.5
                pose(m["HornL" .. k], CFrame.Angles(sway + 0.12 * pace, -spread, 0.03 * math.sin(t * 0.7 - k)))
                pose(m["HornR" .. k], CFrame.Angles(sway + 0.12 * pace, spread, -0.03 * math.sin(t * 0.7 - k)))
            end

            -- the tail: a slow wave, straightening with speed, tucking under as it rears
            local whip = 1 + 0.5 * moving
            local level = 0.055 * pace - 0.09 * rear
            for k = 1, 8 do
                local f = k / 8
                pose(m["Tail" .. k], CFrame.Angles(level + 0.03 * math.sin(t * 1.1 - k * 0.5) + 0.05 * sweep, whip * (0.035 + 0.05 * f) * math.sin(t * 1.7 - k * 0.62) * (1 - 0.5 * fly), 0))
            end
            pose(m.TailTip, CFrame.Angles(0, 0.1 * math.sin(t * 2.3), 0))

            -- the galaxy turns, its arms trailing. At speed it lags behind and tips; when it rears, the wheel rises and faces forward with it, spinning up
            s.spin = (s.spin or 0) + dt * (0.24 + 0.2 * pace + 3.4 * gather + 2.6 * sweep)
            local follow = CFrame.new(0, (0.82 * rear + 0.3 * rollLift) * u, (0.3 * pace - 0.62 * rear) * u) * CFrame.Angles(1.08 * rear - 0.22 * pace, 0, 0)
            pose(m.SpiralOuter, follow * CFrame.Angles(0, -s.spin, 0))
            pose(m.SpiralMid, follow * CFrame.Angles(0, -(s.spin * 1.14 + 0.14 * math.sin(t * 0.23)), 0))
            pose(m.SpiralInner, follow * CFrame.Angles(0, -(s.spin * 1.34 + 0.3 * math.sin(t * 0.17)), 0))
            s.orbit = (s.orbit or 0) + dt * (0.34 + 0.7 * nova)
            pose(m.Orbit, follow * CFrame.Angles(0, -s.orbit, 0))
        end
    end

    return { animateGalaxyManta = animateGalaxyManta }
end
