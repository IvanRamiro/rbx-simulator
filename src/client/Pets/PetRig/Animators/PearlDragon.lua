-- The PearlDragon pet's animation (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, SPARKLE, pose, smoothstep, addStance, dropToGround = K.PetRig, K.SPARKLE, K.pose, K.smoothstep, K.addStance, K.dropToGround

    local animatePearlDragon, PEARL_BONES, PEARL_GLOW, PEARL_SOLE, pearlAt, pearlGlow -- animatePearlDragon's section below (its own locals stay in its block)
    do

        -- The Celestial Pearl Dragon (skinned): a fierce winged dragon of pearl-white nacre that holds its pearl to its chest in its right forefoot. Standing,
        -- it keeps its great wings raised behind it, breathing with it, and now and then flexes them and settles; its head moves slowly and deliberately, its
        -- stare holding on you; its tail sways. It never walks on three legs: to go anywhere it lifts off on heavy wingbeats and hovers low, its legs tucked,
        -- its tail streaming.
        local PEARL_FAR = 110 -- studs from the camera past which nobody can see it fidget: its bones rest
        PEARL_SOLE = 0.5741 -- metres from the middle of its box down to its feet: it stands on the ground
        local PEARL_LID_HINGE = { L = Vector3.new(0.7386, -0.308, -0.5997), R = Vector3.new(0.7386, 0.308, 0.5997) } -- both lids of an eye turn on this line
        local PEARL_BLINK_UPPER, PEARL_BLINK_LOWER = math.rad(40), math.rad(20)
        local PEARL_HOVER = 0.32 -- metres it hovers above the ground when it goes anywhere
        PEARL_GLOW = Color3.fromRGB(255, 230, 214)

        local function pearlWings(lift, sweep, elbow, hand, fan)
            local out = {}
            for tag, sign in { L = 1, R = -1 } do
                out["Wing" .. tag .. "1"] = { 0, sweep * sign, -lift * sign }
                out["Wing" .. tag .. "2"] = { 0, elbow * sign, 0 }
                out["Wing" .. tag .. "3"] = { 0, hand * sign, 0 }
                for j = 0, 3 do
                    out["Wing" .. tag .. "F" .. (j + 1)] = { 0, fan * sign * j / 3, 0 }
                end
            end
            return out
        end

        -- its poses, each checked in Blender against the ground and for torn skin: the same numbers as celestial_pearl_dragon.py's FLEX, BEAT_UP, BEAT_DOWN, TUCK
        -- and REAR
        local PEARL_FLEX = pearlWings(-0.15, 0.1, 0, -0.2, 0.3)
        local PEARL_BEAT_UP = pearlWings(0.45, -0.1, 0, 0, 0)
        local PEARL_BEAT_DOWN = pearlWings(-0.7, 0.05, 0, 0.15, 0)
        local PEARL_TUCK = {
            LegFL1 = { 0.5, 0, 0 }, LegFL2 = { -1.0, 0, 0 }, LegFL3 = { 0.5, 0, 0 },
            LegBL1 = { -0.6, 0, 0 }, LegBL2 = { 0.7, 0, 0 }, LegBR1 = { -0.6, 0, 0 }, LegBR2 = { 0.7, 0, 0 },
        }
        local PEARL_REAR = {
            Body = { 0.611, 0, 0 }, Chest = { 0.15, 0, 0 }, Neck1 = { -0.2, 0, 0 }, Neck2 = { -0.15, 0, 0 }, Head = { -0.25, 0, 0 },
            LegFL1 = { -0.386, 0, 0 }, LegFL2 = { 0.344, 0, 0 }, LegFL3 = { 0.059, 0, 0 }, ArmR2 = { 0.3, 0, 0 },
            LegBL1 = { -0.295, 0, 0 }, LegBR1 = { -0.295, 0, 0 }, LegBL2 = { 0.008, 0, 0 }, LegBR2 = { 0.008, 0, 0 }, LegBL3 = { 0.543, 0, 0 }, LegBR3 = { 0.543, 0, 0 },
            Tail1 = { -0.055, 0, 0 }, Tail2 = { -0.028, 0, 0 },
        }
        for bone, a in pearlWings(0.5, -0.2, 0, 0, 0) do
            PEARL_REAR[bone] = a
        end
        local PEARL_REAR_DROP = -0.019 -- metres its hips move in the rear

        local function pearlBones()
            local bones = { "Hips", "Body", "Chest", "Neck1", "Neck2", "Neck3", "Head", "EyeL", "EyeR", "ArmR1", "ArmR2", "ArmR3", "HandR" }
            for k = 1, 6 do
                table.insert(bones, "Tail" .. k)
            end
            for _, key in { "FL", "BL", "BR" } do
                for k = 1, 3 do
                    table.insert(bones, "Leg" .. key .. k)
                end
                table.insert(bones, "Paw" .. key)
            end
            for _, tag in { "L", "R" } do
                for k = 1, 3 do
                    table.insert(bones, "Wing" .. tag .. k)
                end
                for j = 1, 4 do
                    table.insert(bones, "Wing" .. tag .. "F" .. j)
                end
            end
            return bones
        end
        PEARL_BONES = pearlBones() -- every bone its stances pose (the lids turn on their hinges on their own)

        -- where the pearl is now: the hand's bone carries it, at the offset it had at rest
        function pearlAt(rig, s)
            local hand = rig.points.HandR
            if not hand then
                return rig.rootPart.Position
            end
            if not s.pearlOffset then
                local pearl = rig.parts.Pearl
                s.pearlOffset = if pearl then hand.TransformedWorldCFrame:PointToObjectSpace(pearl.Position) else Vector3.zero
            end
            return hand.TransformedWorldCFrame:PointToWorldSpace(s.pearlOffset)
        end

        -- its glow: the light and the drifting motes ride on the hand's bone, where the pearl is (a skinned piece's own CFrame stays where it was bound)
        function pearlGlow(rig, s)
            local hand = rig.points.HandR
            if not hand then
                return
            end
            local at = Instance.new("Attachment")
            at.Name = "Pearl"
            at.CFrame = CFrame.new(s.pearlOffset)
            at.Parent = hand
            local light = Instance.new("PointLight")
            light.Name = "PulseLight"
            light.Color = PEARL_GLOW
            light.Range = 5 * rig.unit
            light.Brightness = 1.4
            light.Shadows = false
            light.Parent = at
            rig.light = light
            local motes = Instance.new("ParticleEmitter")
            motes.Name = "Motes"
            motes.Texture = SPARKLE
            motes.Rate = 4
            motes.Lifetime = NumberRange.new(1.2, 2)
            motes.Speed = NumberRange.new(0.05 * rig.unit, 0.2 * rig.unit)
            motes.SpreadAngle = Vector2.new(180, 180)
            motes.Acceleration = Vector3.new(0, 0.15 * rig.unit, 0)
            motes.Drag = 1
            motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.3, 0.08 * rig.unit), NumberSequenceKeypoint.new(1, 0) })
            motes.Color = ColorSequence.new(Color3.fromRGB(255, 240, 214), Color3.fromRGB(196, 176, 255))
            motes.LightEmission = 1
            motes.LightInfluence = 0
            motes.Parent = at
        end

        function animatePearlDragon(rig, s, moving, fly, nova)
            if not s.pearlOffset then
                pearlAt(rig, s) -- at rest, before any pose: where the pearl sits in the hand
                pearlGlow(rig, s)
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > PEARL_FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, PEARL_SOLE)

            -- the special, Heaven Condensed: it rears on its hind legs, wings flared, and raises the pearl to the sky; it watches heaven's light pour down into
            -- it (Blasts.HeavenCondensed); then it lunges, head and pearl thrust forward, wings snapping down, as the light bursts out of the pearl; it settles
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local rise = smoothstep(0.02, 0.28, progress) * (1 - smoothstep(0.8, 0.97, progress))
            local skyward = smoothstep(0.2, 0.4, progress) * (1 - smoothstep(0.6, 0.67, progress))
            local lunge = smoothstep(0.64, 0.69, progress) * (1 - smoothstep(0.76, 0.9, progress))

            -- on the wing: heavy beats, the body lifting on each downstroke; it hovers low when it goes anywhere, higher when it flies
            s.beat = (s.beat or 0) + dt * (4.2 + 1.2 * fly) * pace
            local stroke = math.sin(s.beat)
            local up, down = math.max(0, stroke), math.max(0, -stroke)
            local hover = (PEARL_HOVER * pace + 0.03 * pace * math.cos(s.beat)) * (1 - rise)

            local want = {}
            addStance(want, PEARL_REAR, rise)
            addStance(want, PEARL_TUCK, pace * (1 - rise))
            addStance(want, PEARL_BEAT_UP, up * pace + 0.6 * rise * (1 - lunge))
            addStance(want, PEARL_BEAT_DOWN, down * pace + lunge)
            addStance(want, {
                Neck1 = { 0.1 * skyward - 0.25 * lunge, 0, 0 }, Neck2 = { 0.15 * skyward - 0.25 * lunge, 0, 0 }, Head = { 0.3 * skyward - 0.15 * lunge, 0, 0 },
                ArmR2 = { 0.15 * skyward + 0.35 * lunge, 0, 0 }, ArmR3 = { 0.2 * lunge, 0, 0 },
            }, 1)

            -- standing: it breathes, its raised wings breathing with it; now and then they flex and settle, or it tosses its head with a snort
            local breath = math.sin(t * 1.2)
            local calmness = (1 - pace) * (1 - rise)
            s.nextFlex = s.nextFlex or t + 5
            if t >= s.nextFlex then
                s.flexAt, s.flexKind = t, if math.random() < 0.6 then "wings" else "snort"
                s.nextFlex = t + 6 + math.random() * 5
            end
            local env = if s.flexAt then math.clamp((t - s.flexAt) / 1.6, 0, 1) else 1
            local flex = math.sin(math.pi * env) * calmness
            addStance(want, PEARL_FLEX, (if s.flexKind == "wings" then flex else 0))
            addStance(want, pearlWings(0.04 * breath, 0, 0, 0, 0), calmness)
            local snort = if s.flexKind == "snort" then flex else 0
            addStance(want, { Chest = { 0.015 * breath, 0, 0 }, Head = { 0.18 * snort * math.sin(math.pi * 2 * env), 0, 0.1 * snort } }, 1)

            -- banking on turns
            local heading = math.atan2(-rig.rootPart.CFrame.LookVector.X, -rig.rootPart.CFrame.LookVector.Z)
            local turned = (heading - (s.heading or heading) + math.pi) % (2 * math.pi) - math.pi
            s.heading = heading
            s.bank = (s.bank or 0) + (math.clamp((if dt > 0 then turned / dt else 0) * 0.1, -0.25, 0.25) - (s.bank or 0)) * math.min(1, dt * 3)
            addStance(want, { Hips = { 0.08 * pace, 0, s.bank * pace }, Body = { -0.06 * pace, 0, 0 } }, 1)

            -- its gaze: slow and deliberate, a predator's; it settles on you and holds
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 3 + math.random() * 3.5
                s.atYou = math.random() < 0.55
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.0, (math.random() - 0.5) * 0.25
            end
            local calm = (1 - 0.7 * pace) * (1 - rise)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.75, 0.75) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.2, 0.3) else s.gazePitch) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2.2)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2.2)
            addStance(want, {
                Neck2 = { 0.25 * s.pitch, 0.3 * s.yaw, 0 }, Neck3 = { 0.25 * s.pitch, 0.3 * s.yaw, 0 }, Head = { 0.4 * s.pitch, 0.4 * s.yaw, 0 },
                EyeL = { 0.2 * s.pitch, 0.15 * s.yaw, 0 }, EyeR = { 0.2 * s.pitch, 0.15 * s.yaw, 0 },
            }, 1)

            -- the tail: a slow, heavy sway; streaming out behind it on the wing
            for k = 1, 6 do
                local sway = (0.03 + 0.04 * k / 6) * math.sin(t * 0.7 - k * 0.5) * (1 - 0.6 * pace)
                addStance(want, { ["Tail" .. k] = { 0.02 * math.sin(t * 0.5 - k * 0.6) + 0.05 * pace + 0.04 * pace * math.sin(s.beat - k * 0.6), sway, 0 } }, 1)
            end

            for _, name in PEARL_BONES do
                local a = want[name] or Vector3.zero
                local lift = if name == "Hips" then (hover + 0.025 * pace * down + PEARL_REAR_DROP * rise) * u - drop else 0
                pose(m[name], CFrame.new(0, lift, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- the eyes: a slow blink now and then; wide as it watches heaven's light, narrowed in the lunge
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.3
                if a >= 1 then
                    s.nextBlink = t + 4 + math.random() * 4
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local close = math.max(blink * (1 - skyward), 0.3 * lunge)
            local upper = PEARL_BLINK_UPPER * close - math.rad(7) * skyward
            local lower = PEARL_BLINK_LOWER * close - math.rad(5) * skyward
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(PEARL_LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(PEARL_LID_HINGE[side], lower))
            end
        end
    end

    return { animatePearlDragon = animatePearlDragon, PEARL_BONES = PEARL_BONES, PEARL_GLOW = PEARL_GLOW, PEARL_SOLE = PEARL_SOLE, pearlAt = pearlAt, pearlGlow = pearlGlow }
end
