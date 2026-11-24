-- The Panda pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local pose, smoothstep = K.pose, K.smoothstep

    local animatePanda -- animatePanda's section below (its own locals stay in its block)
    do

        local PANDA_LEGS = { LegFL = 0, LegBR = 0.3, LegFR = math.pi, LegBL = math.pi + 0.3 }
        function animatePanda(rig, s, moving, fly, nova)
            local m, u, t = rig.motors, rig.unit, s.time
            local pace = math.max(moving, fly)
            s.stride = (s.stride or 0) + rig.deltaTime * (1 + 5 * pace)
            local stride = s.stride
            local breathe = math.sin(t * 1.1)
            s.lotus = if rig.nova then (s.lotus or 0) + rig.deltaTime else 0
            local rear = smoothstep(0, 0.75, s.lotus) * (1 - smoothstep(0.88, 1.06, s.lotus)) * math.min(1, nova * 3)
            local impact = smoothstep(0.95, 1.1, s.lotus) * (1 - smoothstep(1.2, 1.9, s.lotus))

            pose(m.Body, CFrame.new(0, (0.02 * breathe + 0.04 * math.abs(math.sin(stride)) * pace + 0.32 * rear - 0.06 * impact) * u, 0)
                * CFrame.Angles(0.03 * breathe - 0.6 * rear + 0.14 * impact, 0, 0.06 * math.sin(stride) * pace))
            pose(m.Head, CFrame.Angles(0.05 * math.sin(t * 0.7) + 0.04 * math.sin(stride * 2) * pace + 0.3 * rear - 0.12 * impact,
                0.25 * math.sin(t * 0.35) * (1 - pace) * (1 - rear), 0.05 * math.sin(t * 0.5) + 0.04 * math.sin(stride) * pace))

            for name, phase in PANDA_LEGS do
                local front = string.sub(name, 4, 4) == "F"
                local swing = 0.35 * math.sin(stride + phase) * pace
                local lift = if front then -0.75 * rear + 0.3 * impact else 0.6 * rear - 0.1 * impact
                pose(m[name], CFrame.Angles(swing + lift, 0, 0))
            end
        end
    end

    return { animatePanda = animatePanda }
end
