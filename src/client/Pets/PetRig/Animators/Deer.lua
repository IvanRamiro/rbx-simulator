-- The Deer pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local pose, smoothstep = K.pose, K.smoothstep

    local animateDeer -- animateDeer's section below (its own locals stay in its block)
    do

        local DEER_LEGS = { LegBL = 0, LegFL = math.pi / 2, LegBR = math.pi, LegFR = 3 * math.pi / 2 }
        function animateDeer(rig, s, moving, fly, nova)
            local m, u, t = rig.motors, rig.unit, s.time
            local pace = math.max(moving, fly)
            s.stride = (s.stride or 0) + rig.deltaTime * (1.2 + 6 * pace)
            local stride = s.stride
            local breathe = math.sin(t * 1.2)
            s.grove = if rig.nova then (s.grove or 0) + rig.deltaTime else 0
            local rear = smoothstep(0, 0.7, s.grove) * (1 - smoothstep(0.9, 1.08, s.grove)) * math.min(1, nova * 3)
            local land = smoothstep(0.98, 1.1, s.grove) * (1 - smoothstep(1.2, 1.8, s.grove))

            pose(m.Body, CFrame.new(0, (0.015 * breathe + 0.04 * math.abs(math.sin(stride * 2)) * pace + 0.25 * rear - 0.05 * land) * u, 0)
                * CFrame.Angles(-0.5 * rear + 0.1 * land + 0.02 * math.sin(stride * 2) * pace, 0, 0.03 * math.sin(stride) * pace))
            local look = 0.35 * math.sin(t * 0.3) * (1 - pace) * (1 - rear)
            pose(m.Neck, CFrame.Angles(0.04 * math.sin(t * 0.8) - 0.05 * math.sin(stride * 2) * pace + 0.3 * rear - 0.1 * land, look * 0.45, 0))
            pose(m.Head, CFrame.Angles(0.05 * math.sin(t * 1.1 + 1) + 0.2 * rear * math.sin(s.grove * 9) - 0.08 * land, look * 0.55, 0.05 * math.sin(t * 0.6)))

            for name, phase in DEER_LEGS do
                local front = string.sub(name, 4, 4) == "F"
                local swing = math.sin(stride + phase)
                local lift = math.max(0, math.sin(stride + phase + 1.2))
                local rearing = if front then 0.9 * rear - 0.25 * land else 0.45 * rear
                pose(m[name], CFrame.Angles((0.3 + 0.15 * fly) * swing * pace + rearing, 0, 0))
                pose(m[name .. "2"], CFrame.Angles((if front then -1 else 1) * (0.7 * lift * pace + (if front then 1.4 else 0.2) * rear), 0, 0))
            end
        end
    end

    return { animateDeer = animateDeer }
end
