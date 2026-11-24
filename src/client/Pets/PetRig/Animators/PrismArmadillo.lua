-- The PrismArmadillo pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep, dropToGround = K.PetRig, K.pose, K.smoothstep, K.dropToGround

    local animatePrismArmadillo -- animatePrismArmadillo's section below (its own locals stay in its block)
    do

        -- The Prism Armadillo (skinned): it scurries on short quick legs, sniffs at everything, rears up on its hind legs to look about, and now and then rolls up into its armour for a moment, purely to show off. Its eyes have no upper lids:
        -- soft cheek pads turn up round each eye from below (a pleased squint, or all the way for a blink). Flying, it rolls up and spins through the air. Its crest prisms each drift slowly through the spectrum.
        local ARMA_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        local ARMA_SOLE = 0.24 -- metres from the middle of its box down to its claws: it walks on the ground
        local ARMA_CHEEK = { L = Vector3.new(0.2668, -0.441, -0.8569), R = Vector3.new(-0.2668, -0.441, -0.8569) } -- each pad's hinge, through its eye's centre: a positive turn carries it up over the eye
        local ARMA_BLINK, ARMA_SQUINT = 1.15, 0.5
        local ARMA_LEGS = { FL = 0, BR = 0, FR = math.pi, BL = math.pi }
        local ARMA_CRESTS = 6

        -- The special's spin, as a turn at each moment of it (armaSpinAngle), so it always ends facing
        -- forward: its speed rises and falls with armaWhirl, scaled to the whole number of turns nearest
        -- ARMA_SPIN_RATE turns a second at full speed. ARMA_SPIN[i] is the share of the spin done by
        -- progress (i - 1) / ARMA_SPIN_STEPS; armaSpin is the whole spin's length in full-speed specials.
        local ARMA_SPIN_RATE, ARMA_SPIN_STEPS = 2.4, 200
        local function armaWhirl(progress)
            return smoothstep(0.1, 0.3, progress) * (1 - smoothstep(0.4, 0.46, progress))
        end
        local ARMA_SPIN, armaSpin = { 0 }, 0
        for i = 1, ARMA_SPIN_STEPS do
            armaSpin += armaWhirl((i - 0.5) / ARMA_SPIN_STEPS) / ARMA_SPIN_STEPS
            ARMA_SPIN[i + 1] = armaSpin
        end
        for i, done in ARMA_SPIN do
            ARMA_SPIN[i] = done / armaSpin
        end
        local function armaSpinAngle(progress)
            local turns = math.max(1, math.floor(ARMA_SPIN_RATE * PetRig.NOVA_TIME * armaSpin + 0.5))
            local x = math.clamp(progress, 0, 1) * ARMA_SPIN_STEPS
            local i = math.min(math.floor(x), ARMA_SPIN_STEPS - 1)
            local done = ARMA_SPIN[i + 1] + (ARMA_SPIN[i + 2] - ARMA_SPIN[i + 1]) * (x - i)
            return done * turns * 2 * math.pi
        end

        function animatePrismArmadillo(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - rig.rootPart.Position).Magnitude > ARMA_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, ARMA_SOLE)

            -- the special: it rolls up, spins in place faster and faster, and pops open in a flash of every colour, very pleased with itself
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local curled = smoothstep(0, 0.12, progress) * (1 - smoothstep(0.44, 0.52, progress))
            local hop = smoothstep(0.44, 0.5, progress) * (1 - smoothstep(0.52, 0.64, progress))
            local proud = smoothstep(0.5, 0.58, progress) * (1 - smoothstep(0.86, 0.98, progress))
            local flash = smoothstep(0.36, 0.43, progress) * (1 - smoothstep(0.46, 0.66, progress))
            s.whirl = armaSpinAngle(progress) % (2 * math.pi)

            -- now and then: it rolls up for a moment just to be admired; or rears up to look about
            s.nextShow = s.nextShow or t + 10 + math.random() * 8
            local show = 0
            if t >= s.nextShow then
                local a = (t - s.nextShow) / 2.6
                if a >= 1 then
                    s.nextShow = t + 16 + math.random() * 14
                    s.pleasedUntil = t + 1.6
                elseif pace < 0.25 and nova == 0 then
                    show = smoothstep(0, 0.12, a) * (1 - smoothstep(0.7, 0.82, a))
                else
                    s.nextShow = t + 3
                end
            end
            s.nextRear = s.nextRear or t + 5 + math.random() * 6
            local rear = 0
            if t >= s.nextRear then
                local a = (t - s.nextRear) / 3.2
                if a >= 1 then
                    s.nextRear = t + 12 + math.random() * 12
                elseif pace < 0.25 and nova == 0 and show == 0 then
                    rear = smoothstep(0, 0.2, a) * (1 - smoothstep(0.78, 1, a))
                else
                    s.nextRear = t + 2
                end
            end
            local roll = math.max(curled, show, fly)

            -- the body
            s.stride = (s.stride or 0) + dt * 11 * moving
            local stride = s.stride
            local breath = math.sin(t * 1.6)
            local look = rig.rootPart.CFrame.LookVector
            local heading = math.atan2(-look.X, -look.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.08, -0.18, 0.18) - (s.bank or 0)) * math.min(1, dt * 4)
            -- flying, it is a ball rolling forward through the air
            s.tumble = ((s.tumble or 0) + dt * fly * 2 * math.pi * 1.3) % (2 * math.pi)
            local tumble = if fly > 0.5 then s.tumble else s.tumble * fly
            local lift = 0.012 * moving * math.abs(math.sin(stride)) + 0.12 * hop + 0.04 * rear - 0.03 * roll
            pose(m.Body, CFrame.new(0, lift * u - drop, 0) * CFrame.Angles(0.25 * rear - tumble + 0.1 * hop, s.whirl, s.bank * (1 - roll) + 0.02 * moving * math.sin(stride)))

            -- the armour's joints: rolled up as far as it is (the same numbers as tools/blender/pets/prism_armadillo.py's ball()), and a little give with each step
            pose(m.Front, CFrame.Angles(-0.46 * roll + 0.75 * rear * (1 - roll) + 0.2 * proud + 0.01 * breath, 0, 0))
            pose(m.Mid, CFrame.Angles(0.3 * roll + 0.012 * moving * math.sin(2 * stride), 0, 0))
            pose(m.Back, CFrame.Angles(0.3 * roll, 0, 0))
            pose(m.Pelvis, CFrame.Angles(0.48 * roll, 0, 0))

            -- the head: sniffing, curious, tucked away when rolled
            s.nextSniff = s.nextSniff or t + 1
            if t >= s.nextSniff then
                s.nextSniff = t + 1.2 + math.random() * 2.4
                s.sniffAt = t
                s.gazeTo = (math.random() - 0.5) * 0.9
                s.nodTo = (math.random() - 0.5) * 0.25
            end
            local sniff = if s.sniffAt and t - s.sniffAt < 0.7 then math.sin((t - s.sniffAt) * 26) * (1 - (t - s.sniffAt) / 0.7) else 0
            local calm = (1 - roll) * (1 - 0.5 * moving)
            s.yaw = (s.yaw or 0) + ((s.gazeTo or 0) * calm - (s.yaw or 0)) * math.min(1, dt * 6)
            s.nod = (s.nod or 0) + ((s.nodTo or 0) * calm - (s.nod or 0)) * math.min(1, dt * 6)
            pose(m.Neck, CFrame.Angles(-1.25 * roll - 0.35 * rear * (1 - roll) + 0.3 * proud + s.nod * 0.5, s.yaw * 0.45, 0))
            pose(m.Head, CFrame.Angles(-1.1 * roll - 0.2 * rear * (1 - roll) + 0.2 * proud + s.nod * 0.5 + 0.03 * sniff, s.yaw * 0.55, 0.1 * proud * math.sin(t * 3)))

            -- the cheek pads: a blink now and then; pleased, half up
            s.nextBlink = s.nextBlink or t + 2
            if t >= s.nextBlink then
                s.nextBlink = t + 2.5 + math.random() * 3.5
                s.blinkAt = t
            end
            local shut = if s.blinkAt and t - s.blinkAt < 0.2 then 1 - math.abs(2 * (t - s.blinkAt) / 0.2 - 1) else 0
            local pleased = math.max(proud, if s.pleasedUntil and t < s.pleasedUntil then 1 else 0)
            s.pleased = (s.pleased or 0) + (pleased - (s.pleased or 0)) * math.min(1, dt * 5)
            local cheek = math.max(ARMA_BLINK * shut, ARMA_SQUINT * s.pleased, ARMA_BLINK * roll)
            for _, side in { "L", "R" } do
                pose(m["Cheek" .. side], CFrame.fromAxisAngle(ARMA_CHEEK[side], cheek))
                local offset = if side == "L" then 0 else 1.7
                local flick = math.max(0, math.sin(t * 0.9 + offset)) ^ 18
                local sign = if side == "L" then -1 else 1
                pose(m["Ear" .. side], CFrame.Angles(0.7 * roll + 0.3 * moving - 0.25 * rear + 0.3 * flick + 0.04 * math.sin(t * 1.3 + offset), 0, sign * (0.08 * flick)))
            end

            -- the legs: a quick little trot; rearing, the forelegs lift; rolled, all folded in
            local reach = 0.45 * moving * (1 - roll)
            for key, lead in ARMA_LEGS do
                local fore = string.sub(key, 1, 1) == "F"
                local phase = stride + lead
                local swing = math.sin(phase) * reach
                local fold = math.max(0, math.cos(phase)) * moving * (1 - roll) * 0.6
                local tuck1 = if fore then -0.9 else 0.9
                local tuck2 = if fore then 1.4 else -1.2
                local reared = if fore then -0.4 * rear else 0.25 * rear
                pose(m["Leg" .. key .. "1"], CFrame.Angles(swing + tuck1 * roll + reared * (1 - roll) - 0.25 * rear * (if fore then 0 else 1), 0, 0))
                pose(m["Leg" .. key .. "2"], CFrame.Angles((if fore then -fold else fold) + tuck2 * roll, 0, 0))
                pose(m["Paw" .. key], CFrame.Angles((if fore then 0.4 * fold else -0.3 * fold), 0, 0))
            end

            -- the tail: swishing as it goes, tucked when rolled
            for index, name in { "Tail1", "Tail2", "Tail3" } do
                local tuck = ({ 0.9, 0.8, 0.7 })[index]
                pose(m[name], CFrame.Angles(tuck * roll - 0.3 * rear * (index == 1 and 1 or 0) * (1 - roll), (0.08 + 0.12 * moving) * math.sin(t * 2.4 + stride - index * 0.7) * (1 - roll), 0))
            end

            -- the crest: each prism drifting through the spectrum, a step behind the one before; flashing white-bright when it shows off
            local bright = math.max(flash, 0.6 * show * smoothstep(0.3, 0.6, show))
            for k = 1, ARMA_CRESTS do
                local part = rig.parts["Crest" .. k]
                if part then
                    local hue = ((k - 1) / ARMA_CRESTS + t * 0.05 + 2 * s.whirl / (2 * math.pi)) % 1
                    part.Color = Color3.fromHSV(hue, 0.62 - 0.14 * bright, 1) -- (Neon pales a colour: below about 0.45 saturation the prisms all read white)
                end
            end
        end
    end

    return { animatePrismArmadillo = animatePrismArmadillo }
end
