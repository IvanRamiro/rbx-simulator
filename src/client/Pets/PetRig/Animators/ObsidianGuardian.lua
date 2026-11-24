-- The ObsidianGuardian pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, pose, smoothstep, dropToGround = K.PetRig, K.pose, K.smoothstep, K.dropToGround

    local animateObsidianGuardian, GUARD_BONES, GUARD_GLASS, GUARD_PALE, GUARD_VIOLET -- animateObsidianGuardian's section below (its own locals stay in its block)
    do

        -- The Obsidian Guardian (skinned): a gargoyle of black glass. It perches as gargoyles do, crouched with its hands on the ledge before it and its wings
        -- folded up behind it, their shards hanging round it like a cloak, and keeps as still as the stone it is; then its head snaps round to watch you, its
        -- brow shards lowering, and holds. Now and then it mantles, raising its wings forward over its shoulders, and settles again; its tail's point twitches.
        -- When its owner goes anywhere it takes off and flies low beside them in slow, heavy beats with long glides between, and lands again the moment they stop.
        local GUARD_FAR = 90 -- studs from the camera past which nobody can see it fidget: its bones rest
        local GUARD_HIPS_SOLE = 0.2458 -- metres from its Hips bone down to its talons as it perches (obsidian_guardian.py): where it stands when it lands.
        -- Measured from the bone, not the box: the importer's root part sits at the model's origin, so the box's middle is not where it seems
        local GUARD_HOVER = 0.9 -- metres above the ground it flies when its owner goes anywhere on foot
        GUARD_VIOLET, GUARD_PALE, GUARD_GLASS = Color3.fromRGB(154, 80, 255), Color3.fromRGB(226, 206, 255), Color3.fromRGB(34, 22, 52)
        -- its poses, each checked in Blender (obsidian_guardian.py's POSES) against the ground, for torn skin, and for its wings cutting into it: at each pose and
        -- along the way to it from the perch. Its left side; the right is its mirror. Glide, Up and Down are on the wing (the body pitched, the tail trailing,
        -- the arms tucked); Mantle is the wings raised forward over its shoulders as it perches; Rise is the special: chest up, wings spread wide
        local GUARD_FLY_BODY = {
            Hips = { -0.45, 0, 0 }, Neck = { 0.22, 0, 0 }, Head = { 0.25, 0, 0 },
            Tail1 = { -0.175, 0.199, 0 }, Tail2 = { 0.335, 1.314, 0 }, Tail3 = { -1.184, 0.181, 0 }, Tail4 = { -0.159, 0.399, 0 }, Tail5 = { -0.159, 0.714, 0 },
            ArmL1 = { 0.2, 0, -0.3 }, ArmL2 = { -1.4, 0, 0 },
        }
        local GUARD_GLIDE = {
            WingL1 = { 0.376, -0.61, 0.253 }, WingL2 = { 0.334, -2.985, -1.33 }, WingLS = { 0.887, 0.172, -0.13 },
            WingLF1 = { 1.14, 0.193, -0.189 }, WingLF2 = { 0.988, 0.182, -0.153 }, WingLF3 = { 0.786, 0.159, -0.109 },
        }
        local GUARD_UP = {
            WingL1 = { -0.169, -0.271, -0.288 }, WingL2 = { 0.48, 3.093, -1.119 }, WingLS = { 0.988, 0.182, -0.153 },
            WingLF1 = { 1.038, 0.186, -0.165 }, WingLF2 = { 0.887, 0.172, -0.13 }, WingLF3 = { 0.686, 0.145, -0.088 },
        }
        local GUARD_DOWN = {
            WingL1 = { 0.913, -0.676, 0.807 }, WingL2 = { 0.277, -2.802, -1.621 }, WingLS = { 0.937, 0.177, -0.142 },
            WingLF1 = { 1.191, 0.195, -0.201 }, WingLF2 = { 1.038, 0.186, -0.165 }, WingLF3 = { 0.837, 0.166, -0.119 },
        }
        local GUARD_MANTLE = {
            WingL1 = { -0.437, -0.647, -0.035 }, WingL2 = { -1.119, 0.447, 0.609 }, WingLS = { 0.587, 0.128, -0.07 },
            WingLF1 = { 0.488, 0.11, -0.053 }, WingLF2 = { 0.439, 0.1, -0.045 }, WingLF3 = { 0.39, 0.09, -0.038 },
        }
        local GUARD_RISE = {
            Body = { 0.32, 0, 0 }, Chest = { 0.12, 0, 0 }, Neck = { -0.2, 0, 0 }, Head = { -0.12, 0, 0 }, ArmL1 = { 0.25, 0, -0.2 }, ArmL2 = { -0.3, 0, 0 },
            WingL1 = { -0.696, -0.464, 0.039 }, WingL2 = { -2.721, 0.026, 1.913 }, WingLS = { 0.988, 0.182, -0.153 },
            WingLF1 = { 1.242, 0.197, -0.214 }, WingLF2 = { 1.089, 0.19, -0.177 }, WingLF3 = { 0.887, 0.172, -0.13 },
        }
        local GUARD_SIDED = { "Wing", "Arm", "Leg", "Brow", "Hand", "Foot" }

        -- a pose's turns as CFrames, its left side mirrored onto its right (a mirror keeps a turn about X and flips those about Y and Z)
        local function guardPose(stance)
            local out = {}
            for bone, a in stance do
                out[bone] = CFrame.Angles(a[1], a[2], a[3])
                for _, prefix in GUARD_SIDED do
                    if string.sub(bone, 1, #prefix) == prefix and string.sub(bone, #prefix + 1, #prefix + 1) == "L" then
                        out[prefix .. "R" .. string.sub(bone, #prefix + 2)] = CFrame.Angles(a[1], -a[2], -a[3])
                    end
                end
            end
            return out
        end
        local GUARD_POSES = {
            FlyBody = guardPose(GUARD_FLY_BODY),
            Glide = guardPose(GUARD_GLIDE),
            Up = guardPose(GUARD_UP),
            Down = guardPose(GUARD_DOWN),
            Mantle = guardPose(GUARD_MANTLE),
            Rise = guardPose(GUARD_RISE),
        }

        local function guardBones()
            local bones = { "Hips", "Body", "Chest", "Neck", "Head", "BrowL", "BrowR" }
            for k = 1, 5 do
                table.insert(bones, "Tail" .. k)
            end
            for _, tag in { "L", "R" } do
                for _, name in { "Arm%s1", "Arm%s2", "Hand%s", "Leg%s1", "Leg%s2", "Leg%s3", "Foot%s", "Wing%s1", "Wing%s2", "Wing%s3", "Wing%sS", "Wing%sF1", "Wing%sF2", "Wing%sF3" } do
                    table.insert(bones, string.format(name, tag))
                end
            end
            return bones
        end
        GUARD_BONES = guardBones()
        local GUARD_WINGS = {}
        for _, name in GUARD_BONES do
            if string.sub(name, 1, 4) == "Wing" then
                table.insert(GUARD_WINGS, name)
            end
        end

        -- every bone in `into` turned the share `weight` of the way toward `stance` (by the shortest way round: its wings turn far)
        local function guardToward(into, stance, weight, bones)
            if weight <= 0 then
                return
            end
            for _, name in bones do
                local target = stance[name]
                if target or weight >= 1 then
                    into[name] = (into[name] or CFrame.identity):Lerp(target or CFrame.identity, weight)
                elseif into[name] then
                    into[name] = into[name]:Lerp(CFrame.identity, weight)
                end
            end
        end

        function animateObsidianGuardian(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > GUARD_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)

            -- the special, Honest Glass: it rises on its haunches, wings spread wide, and turns its face to you and holds you in it (to 0.42); its mirror flashes
            -- and gives you back to yourself (Blasts.HonestGlass); it watches the figure break, then folds its wings and settles
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local special = progress > 0
            local rise = smoothstep(0.02, 0.3, progress) * (1 - smoothstep(0.8, 0.98, progress))
            local stare = smoothstep(0.06, 0.2, progress) * (1 - smoothstep(0.7, 0.85, progress))
            local flash = if progress > 0.4 and progress < 0.56 then math.sin(math.pi * (progress - 0.4) / 0.16) else 0

            -- perched or on the wing: it takes off as soon as there is somewhere to go and lands the moment its owner stops
            s.still = if pace < 0.05 then (s.still or 0) + dt else 0
            local wantLand = if (s.still > 0.8 or special) and fly < 0.05 then 1 else 0
            s.land = (s.land or 1) + (wantLand - (s.land or 1)) * math.min(1, dt * (if wantLand > (s.land or 1) then 1.8 else 3.5))
            local land = smoothstep(0, 1, s.land)
            local flying = 1 - land
            local open = smoothstep(0.55, 1, flying) -- its beat fades in only once its wings are open: unfolding straight into a downstroke cuts through it
            local hips = rig.points.Hips
            if hips and not s.sole then
                s.sole = rig.rootPart.CFrame:PointToObjectSpace(hips.WorldPosition).Y * -1 / u + GUARD_HIPS_SOLE -- (WorldPosition leaves out its own Transform)
            end
            local drop = dropToGround(rig, s, t, u, fly, s.sole or 0.5)

            -- on the wing: slow, heavy beats, the body lifting on each downstroke; now and then a long glide on still wings
            s.nextGlide = s.nextGlide or t + 3
            if t >= s.nextGlide then
                s.glideUntil = t + 1 + math.random() * 1.2
                s.nextGlide = s.glideUntil + 2.5 + math.random() * 3
            end
            local gliding = if t < (s.glideUntil or 0) then 1 else 0
            s.glide = (s.glide or 0) + (gliding - (s.glide or 0)) * math.min(1, dt * 3)
            s.beat = (s.beat or 0) + dt * (3.4 + 1.4 * pace) * (1 - 0.9 * s.glide) * open
            local stroke = 0.5 + 0.5 * math.sin(s.beat) -- 1 at the top of the stroke, 0 at the bottom
            local want = {}
            guardToward(want, GUARD_POSES.FlyBody, flying, GUARD_BONES)
            local wings = {}
            guardToward(wings, GUARD_POSES.Down, 1, GUARD_WINGS)
            guardToward(wings, GUARD_POSES.Up, stroke, GUARD_WINGS)
            local hold = 1 - open * (1 - s.glide)
            guardToward(wings, GUARD_POSES.Glide, hold, GUARD_WINGS)
            for _, name in GUARD_WINGS do
                want[name] = CFrame.identity:Lerp(wings[name], flying)
            end

            -- perched: still as stone. Now and then it mantles, raising its wings forward over its shoulders a while, and folds them again; now and then a shiver
            -- runs through its wings and they settle with a rattle of glass
            local perched = land * (1 - rise)
            s.nextMantle = s.nextMantle or t + 8 + math.random() * 6
            if t >= s.nextMantle and perched > 0.95 then
                s.mantleAt = t
                s.nextMantle = t + 14 + math.random() * 10
            end
            local mantleEnv = if s.mantleAt then math.clamp((t - s.mantleAt) / 4.5, 0, 1) else 1
            local mantle = smoothstep(0, 0.25, mantleEnv) * (1 - smoothstep(0.7, 1, mantleEnv)) * perched
            guardToward(want, GUARD_POSES.Mantle, mantle, GUARD_WINGS)
            s.nextShiver = s.nextShiver or t + 5
            if t >= s.nextShiver then
                s.shiverAt = t
                s.nextShiver = t + 7 + math.random() * 8
            end
            local shiverEnv = if s.shiverAt then math.clamp((t - s.shiverAt) / 0.7, 0, 1) else 1
            local shiver = math.sin(math.pi * shiverEnv) * math.sin(t * 38) * 0.035 * perched * (1 - mantle)
            for _, tag in { "L", "R" } do
                local sign = if tag == "L" then 1 else -1
                want["Wing" .. tag .. "1"] = CFrame.Angles(0, 0, shiver * sign) * want["Wing" .. tag .. "1"]
            end

            -- the special: up on its haunches, wings spread wide
            guardToward(want, GUARD_POSES.Rise, rise, GUARD_BONES)

            -- its gaze: still for seconds, then its head snaps round to a new mark and holds; most often the mark is you. In the special it holds you
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextSnap = s.nextSnap or t + 2
            s.markYaw, s.markPitch = s.markYaw or 0, s.markPitch or 0 -- (straight ahead until its first snap)
            if t >= s.nextSnap then
                s.nextSnap = t + 2.5 + math.random() * 4
                s.atYou = math.random() < 0.6
                s.markYaw, s.markPitch = (math.random() - 0.5) * 1.6, (math.random() - 0.4) * 0.35
                s.snapAt = t
            end
            local atYou = s.atYou or stare > 0
            local yawToYou = math.clamp(math.atan2(-toYou.X, -toYou.Z), -1.3, 1.3)
            -- in the special it turns on its perch to face you, so its head need not turn into its own spread wings; on the wing, or rising, the head turns
            -- no more than 0.4 either way (checked in Blender: a head turned further meets the raised wings)
            s.turn = (s.turn or 0) + (yawToYou * stare * land - (s.turn or 0)) * math.min(1, dt * 4)
            local reach = 1 - 0.6 * math.max(flying, rise)
            local wantYaw = math.clamp((if atYou then yawToYou else s.markYaw) - s.turn, -reach, reach)
            local wantPitch = (if atYou then math.clamp(toYou.Y * 0.6, -0.25, 0.35) else s.markPitch) * reach
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 14)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 14)
            want.Neck = CFrame.Angles(0.4 * s.pitch, 0.38 * s.yaw, 0) * (want.Neck or CFrame.identity)
            want.Head = CFrame.Angles(0.6 * s.pitch, 0.62 * s.yaw, 0.1 * s.yaw) * (want.Head or CFrame.identity)

            -- its brow shards: lowered for a moment as its head snaps round, lowered hard as it stares in the special, lifted as its mirror flashes
            local snapGlare = if s.snapAt then math.max(0, 1 - (t - s.snapAt) / 1.4) else 0
            local glare = math.max(snapGlare * 0.7, stare) * (1 - flash)
            for _, tag in { "L", "R" } do
                local sign = if tag == "L" then 1 else -1
                want["Brow" .. tag] = CFrame.Angles(0.2 * flash, 0, sign * (0.25 * flash - 0.3 * glare))
            end

            -- the tail: on the wing it trails, swaying slowly; perched, its point twitches now and then
            s.nextTwitch = s.nextTwitch or t + 3
            if t >= s.nextTwitch then
                s.twitchAt = t
                s.nextTwitch = t + 3 + math.random() * 5
            end
            local twitchEnv = if s.twitchAt then math.clamp((t - s.twitchAt) / 0.5, 0, 1) else 1
            local twitch = math.sin(math.pi * twitchEnv) * 0.25 * land
            for k = 1, 5 do
                local sway = 0.05 * k / 5 * math.sin(t * 1.3 - k * 0.6) * flying
                local flick = if k >= 4 then twitch * (k - 3) * 0.5 else 0
                want["Tail" .. k] = CFrame.Angles(0.03 * math.sin(s.beat - k * 0.5) * flying, sway + flick, 0) * (want["Tail" .. k] or CFrame.identity)
            end

            -- banking on its turns; low over the ground on foot, landing on its talons when it perches
            local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.12, -0.3, 0.3) - (s.bank or 0)) * math.min(1, dt * 3)
            local heave = (0.05 * (1 - stroke) * open * (1 - s.glide) + 0.03 * math.sin(t * 1.1)) * flying
            local lift = (GUARD_HOVER * (1 - fly) + heave) * flying * u - drop -- (drop is nothing while its owner flies: it keeps to their height)
            want.Hips = CFrame.new(0, lift, 0) * CFrame.Angles(0, s.turn, s.bank * flying) * (want.Hips or CFrame.identity)

            for _, name in GUARD_BONES do
                pose(m[name], want[name] or CFrame.identity)
            end
        end
    end

    return { animateObsidianGuardian = animateObsidianGuardian, GUARD_BONES = GUARD_BONES, GUARD_GLASS = GUARD_GLASS, GUARD_PALE = GUARD_PALE, GUARD_VIOLET = GUARD_VIOLET }
end
