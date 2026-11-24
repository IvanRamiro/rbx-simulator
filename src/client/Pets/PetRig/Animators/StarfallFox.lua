-- The StarfallFox pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Debris, SPARKLE, pose, smoothstep, dropToGround = K.PetRig, K.Debris, K.SPARKLE, K.pose, K.smoothstep, K.dropToGround

    local animateStarfallFox, FOX_STAR -- animateStarfallFox's section below (its own locals stay in its block)
    do

        -- The Starfall Fox (skinned): sly and quick. Its head snaps from thing to thing and its pupils get there first; it stops to watch the sky; and when nothing is looking it digs a little with its forepaws, then checks over its shoulder that nobody saw.
        -- It stands and trots on the ground (`dropToGround`), and flying it stretches out in long bounds with its tail streaming behind it like a comet. Its eyelids are bands fixed all along the rim of the eye: they close by stretching, on a hinge along each eye's long axis (+ closes the upper).
        local FOX_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        local FOX_LID_HINGE = { L = Vector3.new(-0.692, 0.3916, 0.6064), R = Vector3.new(-0.692, -0.3916, -0.6064) }
        local FOX_BLINK_UPPER, FOX_BLINK_LOWER = math.rad(9.8), math.rad(5)
        local FOX_LEADS = { FL = 0, BR = 0.35, FR = math.pi, BL = math.pi + 0.35 }
        local FOX_TAIL = { "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "TailTip" }
        local FOX_FALL_FROM, FOX_CATCH = 0.1, 0.42 -- of the special: the falling star shows, and reaches its teeth (PetRig.NOVA_BURST)
        FOX_STAR = "rbxassetid://95572555201628"
        local FOX_SOLE = 0.625 -- metres from the model's centre down to its soles: it stands on the ground (it digs, so it can't hover), and leaves it only to fly

        -- The star it is going to catch, coming down out of the sky at a slant
        local function foxFallingStar(rig, s)
            local metre = rig.meters
            local holder = Instance.new("Part")
            holder.Name = "FallingStar"
            holder.Anchored = true
            holder.CanCollide = false
            holder.CanTouch = false
            holder.CanQuery = false
            holder.CastShadow = false
            holder.Transparency = 1
            holder.Size = Vector3.one * 0.05
            local a, b = Instance.new("Attachment"), Instance.new("Attachment")
            a.Position, b.Position = Vector3.new(0, 0.05 * metre, 0), Vector3.new(0, -0.05 * metre, 0)
            a.Parent, b.Parent = holder, holder
            local streak = Instance.new("Trail")
            streak.Attachment0, streak.Attachment1 = a, b
            streak.FaceCamera = true
            streak.Lifetime = 0.34
            streak.LightEmission = 1
            streak.LightInfluence = 0
            streak.WidthScale = NumberSequence.new(1, 0)
            streak.Color = ColorSequence.new(Color3.fromRGB(255, 240, 200), Color3.fromRGB(120, 140, 255))
            streak.Transparency = NumberSequence.new(0, 1)
            streak.Parent = holder
            local star = Instance.new("ParticleEmitter")
            star.Texture = FOX_STAR
            star.Rate = 0
            star.Lifetime = NumberRange.new(PetRig.NOVA_TIME)
            star.Speed = NumberRange.new(0)
            star.LockedToPart = true
            star.Rotation = NumberRange.new(0, 360)
            star.RotSpeed = NumberRange.new(180, 180)
            star.Size = NumberSequence.new(0.34 * metre)
            star.LightEmission = 1
            star.LightInfluence = 0
            star.Parent = a
            holder.CFrame = CFrame.new(rig.rootPart.Position + rig.rootPart.CFrame:VectorToWorldSpace(Vector3.new(-3.2, 9, -5) * metre))
            holder.Parent = rig.model.Parent or workspace
            star:Emit(1)
            Debris:AddItem(holder, PetRig.NOVA_TIME)
            s.foxStar = holder
            s.foxFrom = nil -- measured afresh from this star
        end

        function animateStarfallFox(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > FOX_FAR then
                if s.foxDust then
                    s.foxDust.FL.Rate, s.foxDust.FR.Rate = 0, 0
                end
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, FOX_SOLE)

            -- the special: it spots a falling star and crouches, rump up, wiggling; it leaps and takes it out of the air in its teeth; it lands, and straight away it digs, and buries it
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local crouch = smoothstep(0.02, 0.18, progress) * (1 - smoothstep(0.33, 0.37, progress))
            local spring = smoothstep(0.34, 0.41, progress) * (1 - smoothstep(0.43, 0.5, progress))
            local air = smoothstep(0.34, 0.42, progress) * (1 - smoothstep(0.5, 0.6, progress))
            local fall = smoothstep(0.46, 0.53, progress) * (1 - smoothstep(0.57, 0.63, progress))
            local land = smoothstep(0.58, 0.62, progress) * (1 - smoothstep(0.63, 0.72, progress))
            local bury = smoothstep(0.66, 0.71, progress) * (1 - smoothstep(0.92, 0.99, progress))
            local gape = smoothstep(0.26, 0.36, progress) * (1 - smoothstep(0.415, 0.43, progress))
            -- (only before the catch: seen first after it, the burst has gone and nothing would take the star away)
            if rig.nova and progress >= FOX_FALL_FROM and progress < FOX_CATCH and not rig.nova.starFell then
                rig.nova.starFell = true
                foxFallingStar(rig, s)
            end
            local mouth = rig.points.Mouth
            if s.foxStar and mouth then
                local q = math.clamp((progress - FOX_FALL_FROM) / (FOX_CATCH - FOX_FALL_FROM), 0, 1)
                s.foxFrom = s.foxFrom or (s.foxStar.Position - mouth.TransformedWorldCFrame.Position)
                s.foxStar.CFrame = CFrame.new(mouth.TransformedWorldCFrame.Position + s.foxFrom * (1 - q ^ 1.5))
            else
                s.foxFrom = nil
            end

            -- when nothing is going on it digs, a little furtively, and looks round to see who saw
            s.nextDig = s.nextDig or t + 8 + math.random() * 8
            local dig, glance = 0, 0
            if t >= s.nextDig then
                local a = (t - s.nextDig) / 3.6
                if a >= 1 then
                    s.nextDig = t + 15 + math.random() * 14
                    s.glanceSide = if math.random() < 0.5 then 1 else -1
                elseif pace < 0.25 and nova == 0 then
                    dig = smoothstep(0, 0.1, a) * (1 - smoothstep(0.62, 0.72, a))
                    glance = smoothstep(0.7, 0.76, a) * (1 - smoothstep(0.93, 1, a))
                else
                    s.nextDig = t + 3
                end
            end
            -- and it watches the sky. It is always a little hopeful
            s.nextSky = s.nextSky or t + 4 + math.random() * 5
            local sky = 0
            if t >= s.nextSky then
                local a = (t - s.nextSky) / 3
                if a >= 1 then
                    s.nextSky = t + 9 + math.random() * 10
                elseif pace < 0.25 and nova == 0 and dig == 0 and glance == 0 then
                    sky = smoothstep(0, 0.1, a) * (1 - smoothstep(0.82, 1, a))
                else
                    s.nextSky = t + 2
                end
            end
            local digging = math.max(dig, bury)

            -- its head doesn't wander: it snaps to something new and holds, and the pupils get there first
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 1 + math.random() * 2.6
                s.gazeTo = (math.random() - 0.5) * 1.1
                s.nodTo = (math.random() - 0.5) * 0.2
                s.tiltTo = if math.random() < 0.3 then (math.random() - 0.5) * 0.5 else 0
            end
            local calm = (1 - pace * 0.75) * (1 - nova) * (1 - digging) * (1 - sky * 0.6)
            local yawTo = (s.gazeTo or 0) * calm + 1.15 * glance * (s.glanceSide or 1)
            local snap = math.min(1, dt * 13)
            s.yaw = (s.yaw or 0) + (yawTo - (s.yaw or 0)) * snap
            s.nod = (s.nod or 0) + ((s.nodTo or 0) * calm - (s.nod or 0)) * snap
            s.tilt = (s.tilt or 0) + (((s.tiltTo or 0) * calm + 0.16 * sky) - (s.tilt or 0)) * snap
            s.eyeYaw = (s.eyeYaw or 0) + (yawTo - (s.eyeYaw or 0)) * math.min(1, dt * 30)

            -- the body: a light trot, two beats to a stride; flying, long bounds
            s.stride = (s.stride or 0) + dt * (9 * moving + 4.2 * fly)
            local stride = s.stride
            local breath = math.sin(t * 1.3)
            local look = rig.rootPart.CFrame.LookVector
            local heading = math.atan2(-look.X, -look.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.1, -0.22, 0.22) - (s.bank or 0)) * math.min(1, dt * 4)
            local pitch = 0.012 * math.sin(t * 1.3 - 0.7) - 0.03 * moving + 0.05 * fly + 0.06 * fly * math.sin(stride) - 0.08 * crouch + 0.5 * spring - 0.34 * fall - 0.05 * land - 0.3 * digging
            local rise = 0.012 * moving * math.cos(2 * stride) + 0.06 * fly + 0.03 * fly * math.sin(stride - 0.8) - 0.11 * crouch + 0.92 * air - 0.09 * land - 0.1 * digging
            pose(m.Body, CFrame.new(0, rise * u - drop, 0) * CFrame.Angles(pitch, 0, s.bank + 0.018 * moving * math.sin(stride)))
            pose(m.Hips, CFrame.Angles(-0.2 * crouch + 0.06 * fly * math.sin(stride - 1), 0.1 * crouch * math.sin(t * 24) + 0.03 * moving * math.sin(stride), 0))
            pose(m.Chest, CFrame.new(0, 0.004 * breath * u, 0) * CFrame.Angles(0.05 * fly * math.sin(stride + 0.4), 0, 0))

            -- the head keeps level over all of it, and looks up at what's falling
            local upward = 0.32 * sky + 0.3 * crouch + 0.14 * air
            pose(m.Neck, CFrame.Angles(-pitch * 0.45 + 0.5 * upward - 0.14 * digging + 0.01 * breath, s.yaw * 0.42, s.tilt * 0.3))
            pose(m.Head, CFrame.Angles(-pitch * 0.45 + 0.5 * upward + s.nod - 0.16 * digging + 0.012 * moving * math.cos(2 * stride - 0.5), s.yaw * 0.58, s.tilt * 0.7 - s.bank * 0.5))
            pose(m.Jaw, CFrame.Angles(-(0.36 * gape + 0.06 * pace * (0.5 + 0.5 * math.sin(t * 7))), 0, 0))

            -- it narrows its eyes at things: the lids rest low, close further as it stalks, and open wide in the leap
            s.nextBlink = s.nextBlink or t + 2
            if t >= s.nextBlink then
                s.nextBlink = t + 1.8 + math.random() * 3.6
                s.blinkAt = t
            end
            local shut = if s.blinkAt and t - s.blinkAt < 0.2 then 1 - math.abs(2 * (t - s.blinkAt) / 0.2 - 1) else 0
            shut = math.max(shut, 0.32 * crouch, 0.22 * digging)
            local wide = math.rad(3.4) * math.max(air, sky * 0.7, glance)
            for _, side in { "L", "R" } do
                local up = if side == "L" then -1 else 1
                pose(m["LidU" .. side], CFrame.fromAxisAngle(FOX_LID_HINGE[side], FOX_BLINK_UPPER * shut - wide))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(FOX_LID_HINGE[side], -FOX_BLINK_LOWER * shut))
                pose(m["Eye" .. side], CFrame.Angles(math.clamp(0.05 * sky + 0.05 * crouch - 0.04 * digging, -0.05, 0.05), math.clamp((s.eyeYaw - s.yaw) * 0.25 + s.eyeYaw * 0.05, -0.06, 0.06), 0))
                local offset = if side == "L" then 0 else 1.9
                local flick = math.max(0, math.sin(t * 0.9 + offset)) ^ 20
                pose(m["Ear" .. side], CFrame.Angles(0.04 * math.sin(t * 1.1 + offset) + 0.42 * pace + 0.28 * digging + 0.5 * air - 0.12 * math.max(sky, crouch) - 0.26 * flick, 0, up * (0.03 * math.sin(t * 0.7 + offset) + 0.14 * flick + 0.1 * pace)))
            end

            -- the legs
            local reach = 0.55 * moving
            local sink = crouch + 0.7 * land
            for key, lead in FOX_LEADS do
                local fore = string.sub(key, 1, 1) == "F"
                local sign = if fore then 1 else -1
                local phase = stride + lead
                local swing = math.sin(phase) * reach
                local fold = math.max(0, math.cos(phase)) * moving * 0.75
                -- flying: fore and hind pairs reach and gather together
                local bound = (if fore then 0.3 + 0.55 * math.sin(stride) else -0.3 + 0.55 * math.sin(stride + 0.8)) * fly
                local boundFold = (0.5 + 0.5 * math.sin(stride + (if fore then 1.4 else 2.2))) * fly * 0.5
                -- digging: the forepaws go at it in turn, fast; the hind legs just brace
                local paw = 0
                if fore then
                    local scrape = math.sin(t * 17 + (if key == "FL" then 0 else math.pi))
                    paw = 0.5 + 0.34 * scrape
                end
                local stretch = air * (if fore then 1 else -1.25)
                local a = swing + bound + digging * paw + stretch - pitch * (1 - air)
                local knee = fold + boundFold + digging * (if fore then 0.45 + 0.3 * math.sin(t * 17 + (if key == "FL" then 1 else 1 + math.pi)) else 0)
                -- crouching, the paws stay planted: the forelegs fold deep, elbows up, and the hind legs barely, since the rump stays high
                local hips = if fore then 0 else 0.2 * crouch
                pose(m["Leg" .. key .. "1"], CFrame.Angles(a + hips + (if fore then -1 else 0.2) * sink, 0, 0))
                pose(m["Leg" .. key .. "2"], CFrame.Angles(-sign * knee + (if fore then 1.85 else -0.42) * sink, 0, 0))
                pose(m["Paw" .. key], CFrame.Angles(sign * knee * 0.4 + (if fore then -0.85 else 0.22) * sink - 0.3 * sign * air, 0, 0))
            end

            -- the tail: a slow wave from root to tip; at speed it streams out behind; stalking, it lashes at the very end
            local wave = 0.05 + 0.11 * moving + 0.08 * fly + 0.05 * digging
            local rate = 1.5 + 5 * moving + 2.5 * fly
            s.wave = (s.wave or 0) + dt * rate
            local stream = math.max(fly, moving * 0.35, air)
            for index, name in FOX_TAIL do
                local along = index / #FOX_TAIL
                local lash = 0.1 * crouch * along * math.sin(t * 16 - index * 0.9)
                local down = (if index <= 2 then 0.1 * stream - 0.16 * digging - 0.12 * crouch else 0.17 * stream)
                pose(m[name], CFrame.Angles(down + 0.012 * math.sin(s.wave * 0.7 - index * 0.5), wave * math.sin(s.wave - index * 0.75) * (0.55 + 0.6 * along) + lash + s.bank * 0.12, 0))
            end

            -- gold kicked up from where it digs
            if not s.foxDust and rig.points.PawFL and rig.points.PawFR then
                s.foxDust = {}
                for _, key in { "FL", "FR" } do
                    local dust = Instance.new("ParticleEmitter")
                    dust.Name = "GoldDust"
                    dust.Texture = SPARKLE
                    dust.Rate = 0
                    dust.Lifetime = NumberRange.new(0.3, 0.55)
                    dust.Speed = NumberRange.new(0.5 * u, 1.1 * u)
                    dust.EmissionDirection = Enum.NormalId.Back
                    dust.SpreadAngle = Vector2.new(35, 35)
                    dust.Acceleration = Vector3.new(0, -3 * u, 0)
                    dust.Size = NumberSequence.new(0.035 * u, 0)
                    dust.Color = ColorSequence.new(Color3.fromRGB(255, 214, 120), Color3.fromRGB(214, 120, 28))
                    dust.LightEmission = 0.5
                    dust.LightInfluence = 0.5
                    dust.Parent = rig.points["Paw" .. key]
                    s.foxDust[key] = dust
                end
            end
            if s.foxDust then
                local rateNow = 10 * dig + 22 * bury
                s.foxDust.FL.Rate, s.foxDust.FR.Rate = rateNow, rateNow
            end
        end
    end

    return { animateStarfallFox = animateStarfallFox, FOX_STAR = FOX_STAR }
end
