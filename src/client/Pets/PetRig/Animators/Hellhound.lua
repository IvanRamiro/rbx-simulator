-- The Hellhound pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local pose = K.pose

    local animateHellhound -- animateHellhound's section below (its own locals stay in its block)
    do

        local HOUND_HEADS = { C = 0, L = 2.1, R = 4.2 }
        function animateHellhound(rig, s, moving, fly, nova)
            local m, u, t = rig.motors, rig.unit, s.time
            s.stride = (s.stride or 0) + rig.deltaTime * (7 * moving + 9 * fly)
            local stride = s.stride

            pose(m.Body, CFrame.new(0, (0.02 * math.sin(t * 1.8) + 0.04 * math.abs(math.sin(stride)) * moving + 0.06 * math.sin(stride) * fly) * u, 0)
                * CFrame.Angles(0.06 * math.sin(stride) * fly - 0.05 * moving + 0.08 * nova, 0, 0.03 * math.sin(stride * 0.5) * moving))

            for _, name in { "LegFL", "LegFR", "LegBL", "LegBR" } do
                local front = string.sub(name, 4, 4) == "F"
                local left = string.sub(name, 5, 5) == "L"
                local trot = 0.45 * math.sin(stride + (if front == left then 0 else math.pi)) * moving
                local gallop = (0.65 * math.sin(stride + (if front then 0 else math.pi) + (if left then 0.3 else 0)) + (if front then 0.25 else -0.25)) * fly
                pose(m[name], CFrame.Angles(trot + gallop, 0, 0))
            end

            for tag, phase in HOUND_HEADS do
                local side = rig.sides["Head" .. tag] or 0
                local sniff = 0.04 * math.sin(t * 9 + phase) * math.max(0, math.sin(t * 0.7 + phase)) ^ 4
                local snap = math.max(0, math.sin(t * 0.45 + phase)) ^ 14
                local yaw = (0.32 * math.sin(t * 0.55 + phase) + side * 0.08) * (1 - 0.5 * moving) * (1 - nova)
                local pitch = 0.08 * math.sin(t * 0.8 + phase) + sniff - 0.1 * fly + 0.6 * nova - 0.15 * snap
                pose(m["Head" .. tag], CFrame.new(0, 0, -0.08 * u * snap) * CFrame.Angles(pitch, yaw, 0.08 * math.sin(t * 0.6 + phase)))
                local growl = 0.05 * (0.5 + 0.5 * math.sin(t * 13 + phase)) * math.max(0, math.sin(t * 0.3 + phase))
                pose(m["Jaw" .. tag], CFrame.Angles(-(0.5 * snap + 0.7 * nova + growl + 0.08 * fly), 0, 0))
            end

            local wag = math.sin(t * (2.2 + 4 * moving + 4 * fly))
            pose(m.Tail1, CFrame.Angles(0.1 * math.sin(t * 1.1) - 0.15 * fly, (0.22 + 0.15 * moving) * wag, 0))
            pose(m.Tail2, CFrame.Angles(0.1 * math.sin(t * 1.1 - 0.8), (0.3 + 0.2 * moving) * math.sin(t * (2.2 + 4 * moving + 4 * fly) - 0.9), 0))
        end
    end

    return { animateHellhound = animateHellhound }
end
