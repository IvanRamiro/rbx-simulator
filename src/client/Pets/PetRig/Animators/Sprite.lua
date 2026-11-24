-- The Sprite pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local pose = K.pose

    local animateSprite -- animateSprite's section below (its own locals stay in its block)
    do

        function animateSprite(rig, s, moving, fly, nova)
            local m, u, t = rig.motors, rig.unit, s.time
            local pace = math.max(moving, fly)
            local bloom = math.sin(math.min(nova * 1.3, 1) * math.pi / 2)
            local drift = math.sin(t * 1.4)

            pose(m.Body, CFrame.new(0, (0.12 * drift + 0.25 * bloom) * u, 0)
                * CFrame.Angles(-0.18 * pace + 0.05 * math.sin(t * 0.9), 0.15 * math.sin(t * 0.4), 0.06 * math.sin(t * 0.7)))
            pose(m.Cap, CFrame.Angles(0.08 * math.sin(t * 1.4 + 0.6) + 0.12 * pace - 0.25 * bloom, t * 0.4 % (2 * math.pi), 0.08 * math.sin(t * 1.1)))
            for _, name in { "ArmL", "ArmR" } do
                local side = rig.sides[name] or 0
                local wave = math.sin(t * 1.8 + side)
                pose(m[name], CFrame.Angles(0.25 * wave * (1 - pace) - 0.3 * pace - 0.6 * bloom, 0, side * (0.15 * math.sin(t * 1.2 + side) - 0.7 * bloom)))
            end
            pose(m.Threads, CFrame.Angles(0.25 * math.sin(t * 2.1) + 0.45 * pace, 0.3 * math.sin(t * 1.3), 0.2 * math.sin(t * 1.7 + 1)))
        end
    end

    return { animateSprite = animateSprite }
end
