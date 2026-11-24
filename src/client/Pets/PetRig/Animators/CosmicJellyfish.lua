-- The CosmicJellyfish pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep = K.PetRig, K.pose, K.smoothstep

    local animateCosmicJellyfish, jellyBones -- animateCosmicJellyfish's section below (its own locals stay in its block)
    do

        -- The Cosmic Jellyfish (skinned; its glass is its own mesh): it has no eyes and no thoughts, and yet its bell leans gently toward you wherever you stand. It swims as a real one does: the bell closes quickly, it rises, it opens slowly and sinks
        -- a little, and everything below it follows late. The nebula in the bell turns slowly on its own bone, faster at each beat. A rim section's axis is its tangent: a positive turn draws the margin in.
        local JELLY_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        local JELLY_RIM_AXIS, JELLY_ARMS = {}, { "A0", "A1", "A2", "A3" }
        for k = 0, 7 do
            local angle = -math.pi / 2 + math.rad(22.5 + 45 * k)
            JELLY_RIM_AXIS[k] = Vector3.new(math.sin(angle), 0, math.cos(angle))
        end
        local JELLY_TENTS = {}
        for name, degrees in { FL = -45, L = 0, BL = 45, BR = 135, R = 180, FR = -135 } do
            local angle = math.rad(degrees)
            JELLY_TENTS[name] = { axis = Vector3.new(math.sin(angle), 0, math.cos(angle)), offset = degrees * 0.031 }
        end
        local JELLY_CHAIN = { a = 0.5, b = 1.0, c = 1.2 }

        function jellyBones()
            local bones = { "Body", "Apex", "Nebula" }
            for k = 0, 7 do
                table.insert(bones, "Rim" .. k)
            end
            for _, arm in JELLY_ARMS do
                for _, tag in { "a", "b", "c" } do
                    table.insert(bones, arm .. tag)
                end
            end
            for name in JELLY_TENTS do
                for _, tag in { "a", "b", "c" } do
                    table.insert(bones, "T" .. name .. tag)
                end
            end
            return bones
        end

        function animateCosmicJellyfish(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > JELLY_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special: the bell opens wide and slow as the nebula spins up; it closes once, hard; a ring of gas rolls off it (Blasts.RollingNebula)
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local open = smoothstep(0, 0.36, progress) * (1 - smoothstep(0.385, 0.425, progress))
            local snap = smoothstep(0.4, 0.44, progress) * (1 - smoothstep(0.47, 0.88, progress))

            -- the beat: closes in a fifth of its time, opens slowly over half. Held still while it does its special
            s.phase = (s.phase or math.random()) + dt * (0.42 + 0.5 * moving + 0.45 * fly) * (1 - 0.9 * nova)
            local p = s.phase % 1
            local close = smoothstep(0, 0.2, p) * (1 - smoothstep(0.2, 0.72, p))
            local heave = smoothstep(0, 0.3, p) - smoothstep(0.3, 1, p)
            s.late = (s.late or 0) + (close - (s.late or 0)) * math.min(1, dt * 4)

            local draw = 0.34 * close * (1 - nova) - 0.05 - 0.24 * open + 0.52 * snap
            for k = 0, 7 do
                pose(m["Rim" .. k], CFrame.fromAxisAngle(JELLY_RIM_AXIS[k], draw + 0.022 * math.sin(t * 1.7 + k * 0.8)))
            end
            pose(m.Apex, CFrame.new(0, (0.05 * close * (1 - nova) - 0.02 * open + 0.06 * snap) * u, 0))

            -- it knows where you are: the bell leans a little toward the camera, whichever way the pet is going
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            local calm = (1 - pace) * (1 - nova)
            s.leanX = (s.leanX or 0) + (toYou.Z * 0.15 * calm - (s.leanX or 0)) * math.min(1, dt * 1.4)
            s.leanZ = (s.leanZ or 0) + (-toYou.X * 0.15 * calm - (s.leanZ or 0)) * math.min(1, dt * 1.4)

            local look = rig.rootPart.CFrame.LookVector
            local heading = math.atan2(-look.X, -look.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.1, -0.2, 0.2) - (s.bank or 0)) * math.min(1, dt * 3)
            local rise = 0.05 * (1 + pace) * heave + 0.012 * math.sin(t * 0.6) - 0.05 * open + 0.3 * snap
            pose(m.Body, CFrame.new(0, rise * u, 0) * CFrame.Angles(s.leanX - 0.5 * moving - 0.6 * fly + 0.03 * math.sin(t * 0.47), 0.05 * math.sin(t * 0.23), s.leanZ + s.bank + 0.03 * math.sin(t * 0.37)))

            -- the nebula turns, faster at each beat, and burns brighter as it spins up
            s.spin = ((s.spin or 0) + dt * (0.28 + 0.9 * s.late + 0.5 * pace + 3.6 * open + 2.2 * snap)) % (2 * math.pi)
            pose(m.Nebula, CFrame.new(0, 0.012 * close * u, 0) * CFrame.Angles(0, s.spin, 0))
            local clover = rig.parts.Clover
            if clover then
                clover.Color = rig.profile.GlowColors["ffb04a"]:Lerp(Color3.fromRGB(255, 160, 70), math.max(0.6 * s.late, open, snap))
            end

            -- all below it follows late: dragged behind it as it goes, drawn in after each beat and let go; each strand on its own wave, more of it toward the tip
            local back = -(0.34 * moving + 0.42 * fly)
            local gather = 0.14 * s.late - 0.1 * open + 0.26 * snap
            local swing = 0.05 + 0.03 * pace
            for name, tent in JELLY_TENTS do
                local index = 0
                for tag, share in JELLY_CHAIN do
                    index = if tag == "a" then 1 elseif tag == "b" then 2 else 3
                    local wave = swing * index * 0.55 * math.sin(t * (1.2 + pace) - index * 0.9 + tent.offset)
                    local across = swing * index * 0.45 * math.sin(t * 0.85 - index * 0.8 + tent.offset * 1.7)
                    pose(m["T" .. name .. tag], CFrame.fromAxisAngle(tent.axis, gather * share) * CFrame.Angles(back * share + wave, 0, across))
                end
            end
            for index, arm in JELLY_ARMS do
                for tag, share in JELLY_CHAIN do
                    local joint = if tag == "a" then 1 elseif tag == "b" then 2 else 3
                    pose(m[arm .. tag], CFrame.Angles(back * share * 0.7 + 0.05 * joint * math.sin(t * 1.05 - joint * 0.8 + index * 1.6), 0.09 * math.sin(t * 0.5 + index * 1.3) * (1 + 0.5 * s.late), 0.05 * joint * math.sin(t * 0.8 - joint + index * 2.1)))
                end
            end

            -- a scrap of nebula sheds a little of itself as it goes
            if not s.gas then
                local bone = rig.points.Apex
                if bone then
                    local gas = Instance.new("ParticleEmitter")
                    gas.Name = "Gas"
                    gas.Texture = "rbxassetid://16172858603"
                    gas.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
                    gas.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
                    gas.Lifetime = NumberRange.new(1.6, 2.4)
                    gas.Speed = NumberRange.new(0.1 * rig.unit, 0.3 * rig.unit)
                    gas.SpreadAngle = Vector2.new(180, 180)
                    gas.Drag = 0.8
                    gas.Rotation = NumberRange.new(0, 360)
                    gas.RotSpeed = NumberRange.new(-14, 14)
                    gas.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * rig.unit), NumberSequenceKeypoint.new(1, 0.42 * rig.unit) })
                    gas.Color = ColorSequence.new(Color3.fromRGB(232, 72, 128), Color3.fromRGB(128, 84, 226))
                    gas.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.6), NumberSequenceKeypoint.new(1, 1) })
                    gas.LightEmission = 0.4
                    gas.LightInfluence = 0.5
                    gas.Parent = bone
                    s.gas = gas
                end
            end
            if s.gas then
                s.gas.Rate = 0.7 + 1.8 * pace
            end
        end
    end

    return { animateCosmicJellyfish = animateCosmicJellyfish, jellyBones = jellyBones }
end
