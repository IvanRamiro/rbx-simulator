-- The Golem pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local pose = K.pose

    local animateGolem -- animateGolem's section below (its own locals stay in its block)
    do

        function animateGolem(rig, s, moving, fly, nova)
            local m, u, t = rig.motors, rig.unit, s.time
            local pace = math.max(moving, fly)
            s.stride = (s.stride or 0) + rig.deltaTime * (1.2 + 4.5 * pace)
            local stride = s.stride
            local breathe = math.sin(t * 0.9)
            local slam = math.sin(math.min(nova * 1.4, 1) * math.pi / 2)

            pose(m.Body, CFrame.new(0, (0.025 * breathe + 0.06 * math.abs(math.sin(stride)) * pace - 0.12 * slam) * u, 0)
                * CFrame.Angles(0.04 * breathe - 0.08 * pace + 0.25 * slam, 0, 0.07 * math.sin(stride) * pace))
            pose(m.Head, CFrame.Angles(0.05 * math.sin(t * 0.6) - 0.2 * slam, 0.18 * math.sin(t * 0.35) * (1 - pace), 0.04 * math.sin(t * 0.5)))

            for _, name in { "LegL", "LegR" } do
                local side = if name == "LegL" then 0 else math.pi
                pose(m[name], CFrame.Angles(0.32 * math.sin(stride + side) * pace - 0.15 * slam, 0, 0))
            end
            for _, name in { "ArmL", "ArmR" } do
                local side = if name == "ArmL" then math.pi else 0
                local heavy = name == "ArmR"
                local lift = (if heavy then 1.6 else 1.2) * slam
                pose(m[name], CFrame.Angles(0.3 * math.sin(stride + side) * pace + 0.05 * breathe - lift, 0, (if heavy then -0.05 else 0.05) * breathe))
                pose(m[name .. "2"], CFrame.Angles(-0.12 * math.max(0, math.sin(stride + side)) * pace - 0.25 * slam, 0, 0))
            end
        end
    end

    return { animateGolem = animateGolem }
end
