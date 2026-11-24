-- The Lion pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local pose, smoothstep = K.pose, K.smoothstep

    local animateLion -- animateLion's section below (its own locals stay in its block)
    do

        local LION_LEGS = { LegFL = 0, LegBR = 0.15, LegFR = math.pi, LegBL = math.pi + 0.15 }
        function animateLion(rig, s, moving, fly, nova)
            local m, u, t = rig.motors, rig.unit, s.time
            local pace = math.max(moving, fly)
            s.stride = (s.stride or 0) + rig.deltaTime * (0.9 + 4.6 * pace)
            local stride = s.stride
            local breathe = math.sin(t * 0.85)
            s.roar = if rig.nova then (s.roar or 0) + rig.deltaTime else 0
            local rise = smoothstep(0.0, 0.45, s.roar) * (1 - smoothstep(1.7, 2.4, s.roar))
            local open = smoothstep(0.4, 0.75, s.roar) * (1 - smoothstep(1.5, 2.1, s.roar)) * math.min(1, nova * 3)

            pose(m.Body, CFrame.new(0, (0.012 * breathe + 0.03 * math.abs(math.sin(stride)) * pace + 0.04 * rise) * u, 0)
                * CFrame.Angles(0.012 * breathe - 0.08 * rise + 0.02 * math.sin(stride * 2) * pace, 0, 0.025 * math.sin(stride) * pace))
            local gaze = 0.38 * math.sin(t * 0.17) ^ 3 * (1 - pace) * (1 - rise)
            pose(m.Head, CFrame.Angles(0.03 * math.sin(t * 0.6 + 1) + 0.06 * math.sin(stride * 2) * pace - 0.3 * rise, gaze, 0.03 * math.sin(t * 0.31) * (1 - pace)))
            if m.Jaw then
                pose(m.Jaw, CFrame.Angles(0.012 * math.max(0, breathe) + 0.5 * open, 0, 0))
            end

            for name, phase in LION_LEGS do
                local front = string.sub(name, 4, 4) == "F"
                local swing = 0.42 * math.sin(stride + phase) * pace
                local brace = if front then -0.12 * rise else 0.1 * rise
                pose(m[name], CFrame.Angles(swing + brace + (if front then -0.5 else 0.6) * fly, 0, 0))
            end

            local flick = math.max(0, math.sin(t * 0.7)) ^ 10
            pose(m.Tail, CFrame.Angles(0.06 * math.sin(t * 0.5) + 0.1 * pace - 0.15 * rise, 0.22 * math.sin(t * 0.42), 0))
            pose(m.Tail2, CFrame.Angles(0.1 * math.sin(t * 0.5 - 0.8) + 0.3 * flick, 0.3 * math.sin(t * 0.42 - 1) + 0.25 * flick, 0.1 * math.sin(t * 0.9)))
        end
    end

    return { animateLion = animateLion }
end
