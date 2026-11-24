-- The SunDragon pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local pose = K.pose

    local SUN_DRAGON_LEGS = { LegFL = 0, LegBR = 0.25, LegFR = math.pi, LegBL = math.pi + 0.25 }
    local animateSunDragon -- animateSunDragon's section below (its own locals stay in its block)
    do
        function animateSunDragon(rig, s, moving, fly, nova)
            local m, u, t = rig.motors, rig.unit, s.time
            s.stride = (s.stride or 0) + rig.deltaTime * (1.2 + 5.5 * moving)
            s.flap = (s.flap or 0) + rig.deltaTime * (1.1 + 5.5 * fly)
            local stride, beat = s.stride, math.sin(s.flap)
            local breathe = math.sin(t * 0.9)
            local flare = math.sin(math.min(nova * 1.3, 1) * math.pi / 2)

            pose(m.Body, CFrame.new(0, (0.02 * breathe + 0.03 * math.abs(math.sin(stride)) * moving + 0.07 * beat * fly + 0.12 * flare) * u, 0)
                * CFrame.Angles(0.02 * breathe + 0.22 * fly - 0.25 * flare, 0, 0.04 * math.sin(stride) * moving))
            local gaze = 0.3 * math.sin(t * 0.3) * (1 - fly) * (1 - flare)
            pose(m.Neck, CFrame.Angles(0.04 * math.sin(t * 0.7) - 0.18 * fly + 0.2 * flare, gaze * 0.5, 0))
            pose(m.Head, CFrame.Angles(0.05 * math.sin(t * 0.85 + 1) - 0.1 * fly + 0.28 * flare, gaze * 0.6, 0.05 * math.sin(t * 0.5)))

            for _, side in { "L", "R" } do
                local sign = rig.sides["Wing" .. side] or 0
                local rest = 0.05 * breathe
                local stroke = (0.6 * beat - 0.05) * fly
                pose(m["Wing" .. side], CFrame.Angles(0, sign * (0.06 * breathe - 0.25 * flare), sign * (rest + stroke + 0.3 * flare)))
                pose(m["Wing" .. side .. "2"], CFrame.Angles(0, sign * 0.15 * math.max(0, -beat) * fly,
                    sign * (0.04 * math.sin(t * 0.9 + 0.6) + 0.35 * math.max(0, beat) * fly + 0.25 * flare)))
            end

            for name, phase in SUN_DRAGON_LEGS do
                local front = string.sub(name, 4, 4) == "F"
                local swing = 0.35 * math.sin(stride + phase) * moving
                local tuck = (if front then 0.7 else -0.45) * fly
                pose(m[name], CFrame.Angles(swing + tuck + (if front then -0.35 else 0.2) * flare, 0, 0))
            end

            local sway = math.sin(t * 0.75)
            pose(m.Tail, CFrame.Angles(0.06 * math.sin(t * 0.6) - 0.2 * fly + 0.15 * flare, 0.22 * sway, 0))
            pose(m.Tail2, CFrame.Angles(0.1 * math.sin(t * 0.6 - 0.7) - 0.15 * fly + 0.25 * flare, 0.32 * math.sin(t * 0.75 - 0.9), 0))
        end
    end

    return { SUN_DRAGON_LEGS = SUN_DRAGON_LEGS, animateSunDragon = animateSunDragon }
end
