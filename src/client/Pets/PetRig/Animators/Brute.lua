-- The Brute pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep, dropToGround = K.PetRig, K.pose, K.smoothstep, K.dropToGround


    local animateBrute, animateWinged, animateDreamEater -- the five pets rigged in Studio (2026-11-12): their sections below
    do
        -- The owner, 2026-11-12: "remove all the aura in pet, just add a rig animation for them". These five were single meshes that showed only
        -- a see-through energy shell, a light and particles; their meshes were split into limbs in Studio (segment) and now move.

        -- Brutes (the Heavenbreaker Ape, the Worldroot Colossus): they stand on the ground and knuckle-walk, arms swinging in turn with a heavy
        -- roll of the shoulders; standing, they breathe deep and the ape looks about. Flying, the arms trail back. The special: both arms rise
        -- over the head and slam down (its Blast lands with the slam). rig.profile.Sole: template units from its middle down to its feet.
        function animateBrute(rig, s, moving, fly, nova)
            local m, u, t, dt = rig.motors, rig.unit, s.time, rig.deltaTime
            local drop = dropToGround(rig, s, t, u, fly, rig.profile.Sole)
            s.stride = (s.stride or 0) + dt * (1.4 + 6 * moving)
            local stride, breathe = s.stride, math.sin(t * 1.3)
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local raise = smoothstep(0.05, 0.38, progress) * (1 - smoothstep(0.42, 0.5, progress))
            local slam = smoothstep(0.42, 0.5, progress) * (1 - smoothstep(0.62, 0.85, progress))
            local roll = math.sin(stride) * moving
            pose(m.Body, CFrame.new(0, -drop + (0.03 * breathe + 0.06 * math.abs(roll) - 0.08 * slam) * u, 0)
                * CFrame.Angles(0.025 * breathe - 0.12 * moving - 0.15 * raise + 0.25 * slam, 0.06 * roll, 0.07 * roll))
            s.nextGlance = s.nextGlance or 0
            if t >= s.nextGlance then
                s.nextGlance = t + 3 + math.random() * 4
                s.glance = (math.random() - 0.5) * 0.9
            end
            s.yaw = (s.yaw or 0) + ((s.glance or 0) * (1 - moving) * (1 - raise) - (s.yaw or 0)) * math.min(1, dt * 2)
            pose(m.Head, CFrame.Angles(0.04 * breathe + 0.25 * raise - 0.15 * slam, s.yaw, 0.03 * math.sin(t * 0.7)))
            for _, name in { "ArmL", "ArmR" } do
                local side = rig.sides[name] or 0
                local phase = if side > 0 then 0 else math.pi
                local swing = 0.55 * math.sin(stride + phase) * moving
                local hang = 0.04 * math.sin(t * 1.3 + phase)
                pose(m[name], CFrame.Angles(swing + hang - 0.6 * fly - 2.4 * raise + 0.4 * slam, 0, side * (0.08 * fly + 0.15 * raise)))
            end
            pose(m.Legs, CFrame.Angles(-0.12 * roll, 0, 0.05 * roll))
        end

        -- Winged (the Prismatic Phoenix, the Eternal Clockwork Dragon): they hover by their owner. Their wings beat slow, long strokes at rest and
        -- quicker, deeper ones when they move or fly; the body rises on each down-stroke; the tail sways and lifts against the beat; the head looks
        -- about. The special: wings swept wide and held, head thrown up (its Blast opens from it).
        function animateWinged(rig, s, moving, fly, nova)
            local m, u, t, dt = rig.motors, rig.unit, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            s.flap = (s.flap or 0) + dt * (2.2 + 4.5 * pace)
            local beat = math.sin(s.flap)
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local spread = smoothstep(0.05, 0.3, progress) * (1 - smoothstep(0.75, 0.95, progress))
            local still = 1 - spread
            pose(m.Body, CFrame.new(0, (-0.08 * beat * still + 0.05 * math.sin(t * 0.9)) * u, 0)
                * CFrame.Angles(-0.1 * pace + 0.04 * beat * still - 0.12 * spread, 0, 0.04 * math.sin(t * 0.6)))
            s.nextGlance = s.nextGlance or 0
            if t >= s.nextGlance then
                s.nextGlance = t + 2.5 + math.random() * 3.5
                s.glance = (math.random() - 0.5) * 0.8
            end
            s.yaw = (s.yaw or 0) + ((s.glance or 0) * (1 - pace) * still - (s.yaw or 0)) * math.min(1, dt * 3)
            pose(m.Head, CFrame.Angles(0.05 * math.sin(t * 1.1) - 0.05 * beat * still + 0.4 * spread, s.yaw, 0))
            local depth = 0.35 + 0.25 * pace
            for _, name in { "WingL", "WingR" } do
                local side = rig.sides[name] or 0
                pose(m[name], CFrame.Angles(0, side * (0.1 * beat * still - 0.25 * spread), side * ((depth * beat + 0.05) * still + 0.55 * spread)))
            end
            if m.Tail then
                pose(m.Tail, CFrame.Angles(0.12 * beat * still - 0.1 * pace - 0.25 * spread, 0.18 * math.sin(t * 0.8), 0.05 * math.sin(t * 1.3)))
            end
        end

        -- The Thousand-Year Dream Eater: it swims through the air beside its owner, a slow wave running from its head through its body to its fins,
        -- rolling a little as it turns. The special: it opens up, head raised and fins spread, and draws in a dream (Blasts.SwallowedDream).
        function animateDreamEater(rig, s, moving, fly, nova)
            local m, u, t = rig.motors, rig.unit, s.time
            local pace = math.max(moving, fly)
            local speed = 1.2 + 2.2 * pace
            s.swim = (s.swim or 0) + rig.deltaTime * speed
            local w = s.swim
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local open = smoothstep(0.05, 0.3, progress) * (1 - smoothstep(0.7, 0.95, progress))
            pose(m.Body, CFrame.new(0, (0.12 * math.sin(w) + 0.05 * open) * u, 0)
                * CFrame.Angles(0.08 * math.sin(w - 0.6) - 0.08 * pace - 0.1 * open, 0.05 * math.sin(w * 0.5), 0.07 * math.sin(w * 0.5 + 1)))
            pose(m.Head, CFrame.Angles(0.1 * math.sin(w + 0.9) + 0.3 * open, 0.06 * math.sin(w * 0.5 + 0.5), 0))
            pose(m.Fins, CFrame.Angles(0.07 * math.sin(w - 1.4) - 0.05 * open, 0.05 * math.sin(w - 1), 0.05 * math.sin(w * 0.5 - 0.8)))
        end
    end

    return { animateBrute = animateBrute, animateWinged = animateWinged, animateDreamEater = animateDreamEater }
end
