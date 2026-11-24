-- The Cub pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local pose, smoothstep = K.pose, K.smoothstep

    local animateCub -- animateCub's section below (its own locals stay in its block)
    do

        function animateCub(rig, s, moving, fly, nova)
            local m, u, t = rig.motors, rig.unit, s.time
            local pace = math.max(moving, fly)
            s.stride = (s.stride or 0) + rig.deltaTime * (1.4 + 6.5 * pace)
            local stride = s.stride
            local breathe = math.sin(t * 1.6)
            local tilt = math.sin(t * 0.45) ^ 3 * (1 - pace)
            local wind = math.sin(math.min(nova * 1.6, 1) * math.pi / 2)
            s.erupt = if rig.nova then (s.erupt or 0) + rig.deltaTime else 0
            local hop = smoothstep(0.55, 0.85, s.erupt) * (1 - smoothstep(0.95, 1.25, s.erupt))

            pose(m.Body, CFrame.new(0, (0.02 * breathe + 0.05 * math.abs(math.sin(stride)) * pace - 0.06 * wind + 0.3 * hop) * u, 0)
                * CFrame.Angles(0.04 * breathe - 0.1 * pace + 0.25 * wind - 0.15 * hop, 0, 0.07 * math.sin(stride) * pace))
            pose(m.Head, CFrame.Angles(0.06 * math.sin(t * 0.9) - 0.15 * wind + 0.3 * hop, 0.25 * math.sin(t * 0.37) * (1 - pace), 0.3 * tilt))

            for _, side in { "L", "R" } do
                local phase = if side == "L" then 0 else math.pi
                local arm = m["Arm" .. side]
                local leg = m["Leg" .. side]
                local slam = (if side == "L" then 1.4 else 1.1) * wind
                if arm then
                    pose(arm, CFrame.Angles(0.45 * math.sin(stride + phase) * pace - slam + 0.6 * hop, 0, 0))
                end
                if leg then
                    pose(leg, CFrame.Angles(0.4 * math.sin(stride + phase + math.pi) * pace - 0.3 * hop, 0, 0))
                end
            end

            pose(m.Tail, CFrame.Angles(0.08 * math.sin(t * 2.2) + 0.25 * hop, 0.3 * math.sin(t * 1.7 + 0.5) + 0.2 * math.sin(stride) * pace, 0))
        end
    end

    return { animateCub = animateCub }
end
