-- VoltFox: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Players, RunService, TweenService, SPARKLE, tweenAfter, pose, smoothstep, Blasts, addStance, dropToGround = K.PetRig, K.Players, K.RunService, K.TweenService, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.addStance, K.dropToGround


    do
        -- The Volt Fox (skinned): a thundercloud fox kit, after the raijū, the thunder beast of the old stories that runs in the storm clouds. A storm-grey
        -- kit with a big head, a short pale muzzle and great ears forked at their tips in electric blue; zigzag bolts of blue down its legs and on its
        -- cheeks; bright storm-blue eyes. Its tail is a short stalk carrying a little thundercloud of its own, lightning flickering inside it and hanging
        -- under it. It stands alert, its cloud drifting over it; it looks about, often at you; now and then it flicks an ear, sits down a while, drops
        -- into a playful bow with its cloud wagging, or looks up as its cloud rumbles; still a long while, it sits and nods off, its cloud dimming. It
        -- trots, diagonal pairs together, its cloud bobbing along behind; in the air it runs on nothing, legs stretched, its cloud trailing. Its special,
        -- Thunder Comes Home: it lifts its cloud high, the cloud billowing up dark and flashing (to 0.42); a bolt leaps from it over its head and strikes
        -- the ground in front of it (Blasts.ThunderComesHome); the strike becomes a ball of lightning that bounces back to it and leaps home into its
        -- cloud (0.81), which flashes bright; it shakes out its fur, pleased.
        local VF = {
            FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
            SOLE = 0.2537, -- metres from the middle of its box down to its paws: it stands on the ground (the box counts its RootPart, a 0.05 m cube at
            -- the origin, so it reaches 0.025 m under its paws: half its height, 0.2662, left it floating 1.25 cm, measured in Play)
            LID_HINGE = { L = Vector3.new(0.8206, -0.1693, -0.5458), R = Vector3.new(0.8206, 0.1693, 0.5458) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(70), -- (the two add past the 94 degrees between the lids' edges: at 62 + 22 a slit of iris showed)
            BLINK_LOWER = math.rad(30),
            CLOUD_CENTRE = Vector3.new(0, 0.085, 0.03), -- metres from its Cloud bone to the middle of its cloud (game axes: up, back)
            BOLT = Color3.fromRGB(40, 160, 255), -- its lightning's Neon: deeper than its 7fe8ff paint (Neon brightens pale colours to white)
            BOLT_HOT = Color3.fromRGB(150, 228, 255),
            SPARK = Color3.fromRGB(196, 246, 255),
            STORM = Color3.fromRGB(70, 80, 112), -- its cloud's billows
            STORM_DIM = Color3.fromRGB(30, 70, 120), -- its lightning as it dozes
            STRIDE = 10, -- radians of its trot a second at a full run
            -- its trot (volt_fox.py TROT_FRONT, TROT_HIND, searched over the cycle in Blender): per leg, swing = sin(phase), lift = max(0, cos(phase));
            -- Leg1 = a*swing + b*lift, Leg2 = c*lift, Paw = d*lift + e*max(0, swing). Lifted 1.8 to 3.3 cm, planted within 5 mm of the ground.
            TROT_LEAD = { FL = 0, BR = 0, FR = math.pi, BL = math.pi }, -- diagonal pairs together
            TROT_FRONT = { 0.26, 0.62, -1.2, 0.5, -0.6 },
            TROT_HIND = { 0.3, 0, 0.75, 0.1, -0.15 },
            -- its stances (game axes; the right side mirrors y and z), each checked in Blender against the ground and for torn skin (volt_fox.py)
            SIT = { Body = { 0.36, 0, 0 }, Chest = { 0.1, 0, 0 }, Neck = { -0.12, 0, 0 }, Head = { -0.14, 0, 0 }, Tail1 = { 0.3, 0, 0 },
                LegFL1 = { -0.5, 0, 0 }, LegFR1 = { -0.5, 0, 0 }, PawFL = { 0.45, 0, 0 }, PawFR = { 0.45, 0, 0 },
                LegBL1 = { 1.55, 0, 0 }, LegBR1 = { 1.55, 0, 0 }, LegBL2 = { -2.45, 0, 0 }, LegBR2 = { -2.45, 0, 0 }, PawBL = { 0.9, 0, 0 }, PawBR = { 0.9, 0, 0 } },
            SIT_DROP = 0.042, -- metres its hips come down as it sits
            DOZE = { Neck = { -0.18, 0, 0 }, Head = { -0.24, 0.12, 0.08 }, EarL = { 0.4, 0, 0.1 }, EarR = { 0.4, 0, -0.1 }, Tail1 = { 0.12, 0, 0 } }, -- over SIT
            BOW = { Body = { -0.25, 0, 0 }, Chest = { -0.1, 0, 0 }, Neck = { 0.22, 0, 0 }, Head = { 0.22, 0, 0 }, Tail1 = { -0.45, 0, 0 },
                EarL = { -0.15, 0, 0 }, EarR = { -0.15, 0, 0 }, LegFL1 = { 0.9, 0, 0 }, LegFR1 = { 0.9, 0, 0 }, LegFL2 = { -0.1, 0, 0 }, LegFR2 = { -0.1, 0, 0 },
                PawFL = { -0.6, 0, 0 }, PawFR = { -0.6, 0, 0 }, LegBL1 = { 0.15, 0, 0 }, LegBR1 = { 0.15, 0, 0 }, PawBL = { -0.1, 0, 0 }, PawBR = { -0.1, 0, 0 } },
            RAISE = { Tail1 = { -0.6, 0, 0 }, Neck = { 0.18, 0, 0 }, Head = { 0.32, 0, 0 }, EarL = { -0.2, 0, -0.15 }, EarR = { -0.2, 0, 0.15 }, Body = { 0.08, 0, 0 } },
            FLY = { Tail1 = { 0.25, 0, 0 }, EarL = { 0.45, 0, 0 }, EarR = { 0.45, 0, 0 }, LegFL1 = { 0.5, 0, 0 }, LegFR1 = { 0.5, 0, 0 }, LegFL2 = { -0.35, 0, 0 },
                LegFR2 = { -0.35, 0, 0 }, LegBL1 = { -0.5, 0, 0 }, LegBR1 = { -0.5, 0, 0 }, LegBL2 = { 0.4, 0, 0 }, LegBR2 = { 0.4, 0, 0 } },
            LOOK_UP = { Neck = { 0.15, 0, 0 }, Head = { 0.35, 0, 0 }, EarL = { 0.3, 0, 0 }, EarR = { 0.3, 0, 0 } }, -- up at its rumbling cloud, ears back
            WATCH = { Neck = { -0.1, 0, 0 }, Head = { -0.2, 0, 0 }, EarL = { -0.2, 0, -0.1 }, EarR = { -0.2, 0, 0.1 } }, -- down at the ball of lightning, ears pricked
            FIDGET_TIME = { flick = 0.8, sit = 5, bow = 2.4, rumble = 2.2 },
            HOME = 0.81, -- the ball of lightning reaches its cloud (Blasts.ThunderComesHome: 1.0 s after the strike at 0.42 of 2.6 s)
            BONES = { "Hips", "Body", "Chest", "Neck", "Head", "EyeL", "EyeR", "EarL", "EarR", "Tail1", "Tail2", "Cloud" },
        }
        for _, key in { "FL", "FR", "BL", "BR" } do
            table.insert(VF.BONES, "Leg" .. key .. "1")
            table.insert(VF.BONES, "Leg" .. key .. "2")
            table.insert(VF.BONES, "Paw" .. key)
        end

        function VF.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        -- inside its cloud: a light that flashes with its lightning, and the storm billowing out round it as it gathers itself for its special
        function VF.glow(rig, s)
            s.glowMade = true
            local cloud = rig.points.Cloud
            if not cloud then
                return
            end
            -- (placed in the world and carried into the bone's own frame: every bone has its own rest turn)
            local frame = cloud.TransformedWorldCFrame
            local root = rig.rootPart.CFrame
            local centre = frame.Position + root.UpVector * VF.CLOUD_CENTRE.Y * rig.meters - root.LookVector * VF.CLOUD_CENTRE.Z * rig.meters
            s.cloudOffset = frame:PointToObjectSpace(centre)
            local a = Instance.new("Attachment")
            a.Name = "Storm"
            a.Position = s.cloudOffset
            a.Parent = cloud
            local light = Instance.new("PointLight")
            light.Name = "StormLight"
            light.Color = VF.BOLT_HOT
            light.Range = 4 * rig.unit
            light.Brightness = 0
            light.Shadows = false
            light.Parent = a
            s.stormLight = light -- (its own, not rig.light: the shared pulse would set it every frame and wash out the flicker)
            if not VF.reduced() and not (PetRig.Quality.Low and rig.owner ~= Players.LocalPlayer) then
                local billow = Instance.new("ParticleEmitter")
                billow.Name = "Billow"
                billow.Texture = "rbxasset://textures/particles/smoke_main.dds"
                billow.Rate = 0
                billow.Lifetime = NumberRange.new(0.6, 1.0)
                billow.Speed = NumberRange.new(0.3 * rig.unit, 0.7 * rig.unit)
                billow.SpreadAngle = Vector2.new(180, 180)
                billow.Drag = 2
                billow.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5 * rig.unit), NumberSequenceKeypoint.new(1, 1.3 * rig.unit) })
                billow.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.2, 0.45), NumberSequenceKeypoint.new(1, 1) })
                billow.Color = ColorSequence.new(VF.STORM)
                billow.RotSpeed = NumberRange.new(-40, 40)
                billow.Rotation = NumberRange.new(0, 360)
                billow.LightInfluence = 0.6
                billow.Parent = a
                s.billow = billow
            end
        end

        local function animateVoltFox(rig, s, moving, fly, nova)
            if not s.glowMade then
                VF.glow(rig, s)
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > VF.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, VF.SOLE)

            -- the special, Thunder Comes Home: its cloud lifted high and billowing, rumbling and flashing (to 0.42); the strike (0.42); it watches the
            -- ball of lightning bounce back to it, looks up as it leaps home into its cloud (0.81), and shakes out its fur
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local special = progress > 0
            local charge = smoothstep(0.02, 0.3, progress) * (1 - smoothstep(0.43, 0.55, progress))
            local watch = smoothstep(0.44, 0.52, progress) * (1 - smoothstep(0.66, 0.74, progress))
            local look = smoothstep(0.66, 0.76, progress) * (1 - smoothstep(0.84, 0.92, progress))
            local shake = smoothstep(0.82, 0.85, progress) * (1 - smoothstep(0.9, 0.98, progress))
            local wide = smoothstep(0.38, 0.43, progress) * (1 - smoothstep(0.6, 0.72, progress))
            if not special then
                s.homeAt = nil
            end
            local home = if s.homeAt then math.exp(-(t - s.homeAt) * 5) else 0

            -- still a long while, it sits and nods off; now and then it flicks an ear, sits a while, drops into a bow or looks up at its rumbling cloud
            s.still = if pace < 0.05 and not special then (s.still or 0) + dt else 0
            local wantDoze = if s.still > 12 then 1 else 0
            s.doze = (s.doze or 0) + (wantDoze - (s.doze or 0)) * math.min(1, dt * (if wantDoze > (s.doze or 0) then 0.8 else 5))
            local doze = smoothstep(0, 1, s.doze)
            s.nextFidget = s.nextFidget or t + 4
            if t >= s.nextFidget then
                local r = math.random()
                s.fidgetAt = t
                s.fidgetKind = if r < 0.32 then "flick" elseif r < 0.55 then "sit" elseif r < 0.8 then "bow" else "rumble"
                s.flickSide = if math.random() < 0.5 then 1 else -1
                s.nextFidget = t + VF.FIDGET_TIME[s.fidgetKind] + 3 + math.random() * 5
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / VF.FIDGET_TIME[s.fidgetKind], 0, 1) else 1
            local calmness = (1 - pace) * (1 - doze) * (1 - math.max(charge, watch, look))
            local fidget = (if s.fidgetKind == "sit" then smoothstep(0, 0.12, env) * (1 - smoothstep(0.88, 1, env)) else math.sin(math.pi * env)) * calmness
            local function kind(name)
                return if s.fidgetKind == name then fidget else 0
            end
            local rumble = math.max(kind("rumble"), charge)

            local want = {}
            local sitting = math.max(doze, kind("sit")) * (1 - charge)
            addStance(want, VF.SIT, sitting)
            addStance(want, VF.DOZE, doze * (1 - charge))
            addStance(want, VF.BOW, kind("bow"))
            addStance(want, VF.RAISE, charge)
            addStance(want, VF.LOOK_UP, math.max(kind("rumble"), look))
            addStance(want, VF.WATCH, watch)
            if s.fidgetKind == "flick" then
                local side = s.flickSide or 1
                local flick = kind("flick") * (0.6 + 0.4 * math.sin(t * 20))
                addStance(want, { [if side > 0 then "EarL" else "EarR"] = { 0.45, 0, 0.3 * side } }, flick)
            end

            -- its trot: diagonal pairs together, each leg lifted as it swings forward; in the air it runs on nothing, legs stretched out and paddling
            local onFoot = moving * (1 - fly)
            s.stride = (s.stride or 0) + dt * VF.STRIDE * math.max(onFoot, 0.6 * fly)
            for key, lead in VF.TROT_LEAD do
                local swing, lift = math.sin(s.stride + lead), math.max(0, math.cos(s.stride + lead))
                local k = if string.sub(key, 1, 1) == "F" then VF.TROT_FRONT else VF.TROT_HIND
                addStance(want, {
                    ["Leg" .. key .. "1"] = { k[1] * swing + k[2] * lift, 0, 0 },
                    ["Leg" .. key .. "2"] = { k[3] * lift, 0, 0 },
                    ["Paw" .. key] = { k[4] * lift + k[5] * math.max(0, swing), 0, 0 },
                }, onFoot)
                addStance(want, { ["Leg" .. key .. "1"] = { 0.15 * swing, 0, 0 } }, fly)
            end
            addStance(want, VF.FLY, fly)
            local beat = math.sin(2 * s.stride)
            addStance(want, { Body = { 0.02 * beat, 0, 0 }, Head = { -0.03 * beat, 0, 0 } }, onFoot)

            -- breathing; its head looking about, often at you
            local breath = math.sin(t * 1.5)
            addStance(want, { Chest = { 0.015 * breath, 0, 0 }, Body = { 0.01 * breath, 0, 0 } }, 1)
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2 + math.random() * 3
                s.atYou = math.random() < 0.55
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.2, (math.random() - 0.5) * 0.3
            end
            local calm = (1 - 0.7 * pace) * (1 - math.max(charge, watch, look, kind("rumble"))) * (1 - 0.8 * doze)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.2, 0.35) else s.gazePitch) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 3.5)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 3.5)
            addStance(want, {
                Neck = { 0.15 * s.pitch, 0.3 * s.yaw, 0 }, Head = { 0.3 * s.pitch, 0.4 * s.yaw, 0.12 * s.yaw },
                EyeL = { 0.25 * s.pitch, 0.25 * s.yaw, 0 }, EyeR = { 0.25 * s.pitch, 0.25 * s.yaw, 0 },
            }, 1)
            -- shaking out its fur once its thunder is home
            addStance(want, { Body = { 0, 0, 0.12 * math.sin(t * 38) }, Chest = { 0, 0, -0.1 * math.sin(t * 38) }, Head = { 0, 0, 0.14 * math.sin(t * 38 + 0.6) } }, shake)

            -- its tail and cloud: drifting slowly; wagging in its bow; bobbing behind its trot; trailing in the air; shuddering as it rumbles
            local drift = math.sin(t * 0.8)
            addStance(want, { Tail1 = { 0.04 * math.sin(t * 0.6), 0.1 * drift, 0 }, Tail2 = { 0, 0.08 * math.sin(t * 0.8 - 0.7), 0 },
                Cloud = { 0.05 * math.sin(t * 1.1 - 1.2), 0.06 * math.sin(t * 0.7), 0.04 * math.sin(t * 0.9 + 0.5) } }, 1 - 0.6 * doze)
            addStance(want, { Tail1 = { 0, 0.45 * math.sin(t * 13), 0 }, Tail2 = { 0, 0.3 * math.sin(t * 13 - 0.8), 0 } }, kind("bow"))
            addStance(want, { Tail1 = { 0, 0.12 * math.sin(s.stride), 0 }, Cloud = { 0.1 * math.sin(2 * s.stride - 0.9), 0, 0.05 * math.sin(s.stride - 0.6) } }, onFoot)
            addStance(want, { Tail2 = { 0.15 * math.sin(t * 3), 0, 0 }, Cloud = { 0.08 * math.sin(t * 2.6), 0.1 * math.sin(t * 1.9), 0 } }, fly)
            local jolt = rumble * 0.05
            addStance(want, { Cloud = { jolt * math.sin(t * 47), jolt * math.sin(t * 39 + 1), jolt * math.sin(t * 53 + 2) } }, 1)

            local lift = -VF.SIT_DROP * sitting * u - drop
            for _, name in VF.BONES do
                local a = want[name] or Vector3.zero
                pose(m[name], CFrame.new(0, if name == "Hips" then lift else 0, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- the lightning in its cloud: flickering now and then, often as it rumbles, rarely as it dozes; its light flashing with it
            s.nextFlicker = s.nextFlicker or 0
            if t >= s.nextFlicker then
                s.nextFlicker = t + 0.06 + math.random() * 0.1
                local chance = (0.1 + 0.5 * rumble) * (1 - 0.8 * doze)
                s.flash = if math.random() < chance then 1 else 0
            end
            local flash = math.max(s.flash or 0, home)
            local bolts = rig.parts.Lightning
            if bolts then
                bolts.Transparency = 0.55 * (1 - flash)
                bolts.Color = (VF.BOLT:Lerp(VF.STORM_DIM, 0.6 * doze)):Lerp(VF.BOLT_HOT, flash)
            end
            if s.stormLight then
                s.stormLight.Brightness = 1.4 * flash + 2.5 * home
                s.stormLight.Range = (4 + 6 * home) * rig.unit
            end
            if s.billow then
                s.billow.Rate = if charge > 0.05 then 18 * charge else 0
            end

            -- the eyes: blinks; shut as it dozes; wide at the strike
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.22
                if a >= 1 then
                    s.nextBlink = t + 2 + math.random() * 4
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local close = math.max(blink, doze) * (1 - wide)
            local upper = VF.BLINK_UPPER * close - math.rad(12) * wide
            local lower = VF.BLINK_LOWER * close - math.rad(6) * wide
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(VF.LID_HINGE[side], -upper))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(VF.LID_HINGE[side], lower))
            end
        end

        -- Its cloud lifted high (animateVoltFox): a bolt leaps from it, arcing over its head, and strikes the ground in front of it twice; the strike
        -- becomes a crackling ball of lightning (the thunder beast's own form) that bounces back to it in two hops and leaps home into its cloud.
        function Blasts.ThunderComesHome(rig, fx)
            local u, metre = rig.unit, rig.meters
            local s = rig.state
            local reduced = VF.reduced()
            local cloud = rig.points.Cloud
            local function cloudAt()
                if cloud and cloud.Parent then
                    return cloud.TransformedWorldCFrame:PointToWorldSpace(s.cloudOffset or Vector3.zero)
                end
                return rig.rootPart.Position + Vector3.new(0, 0.3 * metre, 0)
            end
            local params = RaycastParams.new()
            params.FilterDescendantsInstances = { rig.model }
            local function groundAt(at)
                local hit = workspace:Raycast(at + Vector3.new(0, 0.6 * metre, 0), Vector3.new(0, -10 * u, 0), params)
                return if hit then hit.Position else Vector3.new(at.X, rig.rootPart.Position.Y - VF.SOLE * metre, at.Z)
            end
            local root = rig.rootPart.CFrame
            local strike = groundAt(root.Position + root.LookVector * 0.55 * metre)
            local from = cloudAt()

            -- the bolt: from its cloud up over its head and down into the ground, jagged all the way (each kink thrown sideways off the line), a fork
            -- or two off it; a hot core in a soft blue sleeve; it strikes, blinks out, strikes again. (With three and five kinks thrown any way it read
            -- as a smooth tent over its head, seen in Play.)
            local segments = {}
            local function jag(a, b, kinks, width, color, wander)
                local last = a
                local line = b - a
                local side = line:Cross(Vector3.yAxis)
                side = if side.Magnitude > 1e-3 then side.Unit else root.RightVector
                local across = line.Unit:Cross(side)
                for k = 1, kinks do
                    local at = a:Lerp(b, k / kinks)
                    if k < kinks then
                        local span = line.Magnitude / kinks
                        at += (side * (math.random() - 0.5) * 2 + across * (math.random() - 0.5)) * span * wander
                    end
                    local length = (at - last).Magnitude
                    if length > 1e-3 then
                        local cf = CFrame.lookAt((last + at) / 2, at)
                        table.insert(segments, fx.neon(Vector3.new(width, width, length), cf, color))
                        local sleeve = fx.neon(Vector3.new(width * 3, width * 3, length + width), cf, VF.BOLT)
                        sleeve.Transparency = 0.7
                        sleeve:SetAttribute("Sleeve", true)
                        table.insert(segments, sleeve)
                    end
                    last = at
                end
                return last
            end
            -- it turns 0.3 m over its head bone, just clear of its ear tips. (Not over its root: the follow floats the root half a metre up and its
            -- hips are pulled back down to the ground, so a turn set off the root stood 0.8 m high, measured in Play.)
            local headBone = rig.points.Head
            local brow = if headBone then headBone.TransformedWorldCFrame.Position else root.Position
            local over = brow + Vector3.yAxis * 0.3 * metre + root.LookVector * 0.06 * metre
            jag(from, over, 5, 0.06 * u, VF.BOLT_HOT, 0.55)
            jag(over, strike, 8, 0.08 * u, VF.BOLT_HOT, 0.6)
            local forks = if reduced then 1 else 2
            for k = 1, forks do
                local base = over:Lerp(strike, 0.25 + 0.25 * k)
                local out = (root.RightVector * (if k == 1 then 1 else -1) * 0.22 - root.UpVector * 0.16) * metre
                jag(base, base + out, 4, 0.035 * u, VF.BOLT_HOT, 0.5)
            end
            for _, seg in segments do
                local shown = seg.Transparency
                task.delay(0.07, function()
                    seg.Transparency = 1
                end)
                task.delay(0.11, function()
                    seg.Transparency = shown
                end)
                tweenAfter(0.2, seg, TweenInfo.new(0.22), { Transparency = 1 })
            end

            -- the strike: a flash of light, sparks thrown up off the ground
            local flashHolder = fx.neon(Vector3.one * 0.05, CFrame.new(strike + Vector3.new(0, 0.3 * metre, 0)), VF.BOLT_HOT)
            flashHolder.Transparency = 1
            local light = Instance.new("PointLight")
            light.Color = VF.BOLT_HOT
            light.Range = 14 * u
            light.Brightness = 2.5 -- (at 4 it washed its grey fur out to white)
            light.Shadows = false
            light.Parent = flashHolder
            task.delay(0.07, function()
                light.Brightness = 0.4
            end)
            task.delay(0.11, function()
                light.Brightness = 2.5
            end)
            tweenAfter(0.2, light, TweenInfo.new(0.5), { Brightness = 0 })
            local sparkHolder = fx.neon(Vector3.one * 0.05, CFrame.lookAt(strike, strike + Vector3.yAxis), VF.SPARK)
            sparkHolder.Transparency = 1
            local sparks = Instance.new("ParticleEmitter")
            sparks.Texture = SPARKLE
            sparks.Enabled = false
            sparks.Lifetime = NumberRange.new(0.3, 0.6)
            sparks.Speed = NumberRange.new(3 * u, 6 * u)
            sparks.SpreadAngle = Vector2.new(60, 60)
            sparks.Acceleration = Vector3.new(0, -14 * u, 0)
            sparks.Drag = 1
            sparks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.16 * u), NumberSequenceKeypoint.new(1, 0) })
            sparks.Color = ColorSequence.new(VF.SPARK, VF.BOLT)
            sparks.LightEmission = 1
            sparks.LightInfluence = 0
            sparks.Parent = sparkHolder
            sparks:Emit(if reduced then 12 else 28)

            -- the ball of lightning: born in the strike, crackling; two hops back to it, then a leap home into its cloud
            local R = 0.07 * metre
            local ball = fx.neon(Vector3.one * 0.02 * u, CFrame.new(strike + Vector3.new(0, R, 0)), VF.BOLT)
            ball.Shape = Enum.PartType.Ball
            ball.Transparency = 0.05
            TweenService:Create(ball, TweenInfo.new(0.15, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = Vector3.one * 2 * R }):Play()
            local glow = Instance.new("PointLight")
            glow.Color = VF.BOLT
            glow.Range = 6 * u
            glow.Brightness = 1.6
            glow.Shadows = false
            glow.Parent = ball
            -- its crackle: three little arcs round it, re-struck twenty times a second wherever it is
            local arcs = {}
            for k = 1, (if reduced then 2 else 3) do
                local arc = fx.neon(Vector3.new(0.03 * u, 0.03 * u, 0.1), ball.CFrame, VF.BOLT_HOT)
                arc.Transparency = 1
                arcs[k] = arc
            end
            task.spawn(function()
                while ball.Parent and ball.Transparency < 0.95 do
                    local centre = ball.Position
                    local r = ball.Size.X / 2
                    for _, arc in arcs do
                        local a = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5)
                        local b = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5)
                        if a.Magnitude > 1e-3 and b.Magnitude > 1e-3 then
                            local p, q = centre + a.Unit * r * 1.1, centre + b.Unit * r * 1.6
                            arc.Size = Vector3.new(0.03 * u, 0.03 * u, (q - p).Magnitude)
                            arc.CFrame = CFrame.lookAt((p + q) / 2, q)
                            arc.Transparency = if math.random() < 0.75 then 0 else 1
                        end
                    end
                    task.wait(0.05)
                end
                for _, arc in arcs do
                    arc.Transparency = 1
                end
            end)
            local function hop(to, height, time, after)
                local start = ball.Position
                local apex = (start + to) / 2 + Vector3.new(0, height, 0)
                TweenService:Create(ball, TweenInfo.new(time / 2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = CFrame.new(apex) }):Play()
                tweenAfter(time / 2, ball, TweenInfo.new(time / 2, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { CFrame = CFrame.new(to) })
                task.delay(time, after)
            end
            local function landing(at)
                if reduced or not ball.Parent then
                    return
                end
                local holder = fx.neon(Vector3.one * 0.05, CFrame.lookAt(at, at + Vector3.yAxis), VF.SPARK)
                holder.Transparency = 1
                local puff = sparks:Clone()
                puff.Speed = NumberRange.new(1.5 * u, 3 * u)
                puff.Parent = holder
                puff:Emit(10)
            end
            task.delay(0.15, function()
                if not ball.Parent then
                    return
                end
                local now = rig.rootPart.CFrame
                local nearer = groundAt(strike:Lerp(now.Position + now.LookVector * 0.3 * metre, 0.5)) + Vector3.new(0, R, 0)
                hop(nearer, 0.22 * metre, 0.28, function()
                    landing(nearer - Vector3.new(0, R, 0))
                    if not ball.Parent then
                        return
                    end
                    local here = rig.rootPart.CFrame
                    local feet = groundAt(here.Position + here.LookVector * 0.3 * metre) + Vector3.new(0, R, 0)
                    hop(feet, 0.15 * metre, 0.24, function()
                        landing(feet - Vector3.new(0, R, 0))
                        if not ball.Parent then
                            return
                        end
                        -- the leap home: rising fast into its cloud, wherever its cloud is by now
                        local leap = 0.33
                        local start = ball.Position
                        local conn
                        local began = os.clock()
                        conn = RunService.Heartbeat:Connect(function()
                            local f = math.clamp((os.clock() - began) / leap, 0, 1)
                            if not ball.Parent then
                                conn:Disconnect()
                                return
                            end
                            local target = cloudAt()
                            local e = f * f
                            ball.CFrame = CFrame.new(start:Lerp(target, e) + Vector3.new(0, 0.12 * metre * math.sin(math.pi * f), 0))
                            ball.Size = Vector3.one * 2 * R * (1 - 0.6 * e)
                            if f >= 1 then
                                conn:Disconnect()
                                ball.Transparency = 1
                                glow.Enabled = false
                                s.homeAt = s.time -- its cloud flashes (animateVoltFox)
                            end
                        end)
                    end)
                end)
            end)
        end

        local bones = table.clone(VF.BONES)
        for _, name in { "LidUL", "LidUR", "LidLL", "LidLR" } do
            table.insert(bones, name)
        end
        PetRig.Profiles.VoltFox = {
            Skinned = true,
            Bones = bones,
            Points = { "Head", "Cloud" },
            GlowColors = {
                f6fbff = Color3.fromRGB(246, 251, 255), -- the catch-lights in its eyes
                ["7fe8ff"] = VF.BOLT, -- the lightning in and under its cloud
            },
            SeeThrough = { Cloud = 0.22 }, -- its cloud: the lightning shows through it
            Effects = {
                Blast = "ThunderComesHome",
                NovaLight = 2,
            },
            Colors = {
                Gold = VF.BOLT_HOT,
                Amber = VF.BOLT,
                Orange = VF.BOLT,
                Sun = VF.SPARK,
                Ivory = Color3.fromRGB(214, 222, 236),
            },
            Animate = animateVoltFox,
        }
    end
end
