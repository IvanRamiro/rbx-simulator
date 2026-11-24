-- The Sphinx pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local pose = K.pose

    local animateSphinx -- animateSphinx's section below (its own locals stay in its block)
    do

        local SPHINX_LEGS = { LegFL = 0, LegBR = 0.2, LegFR = math.pi, LegBL = math.pi + 0.2 }
        function animateSphinx(rig, s, moving, fly, nova)
            local m, u, t = rig.motors, rig.unit, s.time
            local pace = math.max(moving, fly)
            s.stride = (s.stride or 0) + rig.deltaTime * (1 + 5.5 * pace)
            local stride = s.stride
            local breathe = math.sin(t * 0.9)
            local rise = math.sin(math.min(nova * 1.3, 1) * math.pi / 2)

            pose(m.Body, CFrame.new(0, (0.015 * breathe + 0.03 * math.abs(math.sin(stride)) * pace + 0.1 * rise) * u, 0)
                * CFrame.Angles(0.02 * breathe - 0.22 * rise, 0, 0.05 * math.sin(stride) * pace))
            local gaze = 0.32 * math.sin(t * 0.25) * (1 - pace) * (1 - rise)
            pose(m.Head, CFrame.Angles(0.04 * math.sin(t * 0.6) + 0.12 * rise, gaze, 0.06 * math.sin(t * 0.35) * (1 - pace)))

            for name, phase in SPHINX_LEGS do
                local front = string.sub(name, 4, 4) == "F"
                local swing = 0.38 * math.sin(stride + phase) * pace
                pose(m[name], CFrame.Angles(swing + (if front then -0.3 * rise else 0.22 * rise), 0, 0))
            end

            local sway = math.sin(t * 0.8)
            pose(m.Tail, CFrame.Angles(0.08 * math.sin(t * 0.6) - 0.35 * rise, 0.25 * sway, 0))
            pose(m.Tail2, CFrame.Angles(0.12 * math.sin(t * 0.6 - 0.7) - 0.3 * rise, 0.35 * math.sin(t * 0.8 - 0.9), 0))
        end
    end

    return { animateSphinx = animateSphinx }
end
