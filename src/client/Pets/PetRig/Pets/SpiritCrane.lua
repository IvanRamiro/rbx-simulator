-- SpiritCrane: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, TweenService, tweenAfter, pose, smoothstep, Blasts, addStance, dropToGround = K.PetRig, K.TweenService, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.addStance, K.dropToGround


    do
        -- The Spirit Crane (skinned; its look unchanged from the jointed crane the owner chose: tools/blender/pets/spirit_crane.py gives the same
        -- pieces, maps and glows a skeleton). A tall pearl-and-silver crane: its neck an S of four bones and its head, its folded wings chains of
        -- four that swing out into spread wings, its legs a hip, a knee in the feathered thigh, a heel that bends backward as a bird's does and a
        -- foot kept flat on the ground, its streamers a tail of three, a crest that flutters, a chest that breathes.
        -- It stands tall and calm, breathing, its neck swaying a little and its head bobbing; it glances about, often at you; now and then it
        -- preens under a wing, ruffles its feathers with a shake, bows, or does a little dancing hop with its wings half open. It walks with an
        -- elegant high step (each foot planted flat, the leg turns solved in Blender), its body bobbing and its neck taking the bob back so its
        -- head rides level. With its owner in the air it flies as a crane does: neck stretched out ahead, wings beating slow and deep with the
        -- tips trailing, legs trailed straight back under its tail. Its special, Halo Ascension: it gathers itself, wings half open (to 0.3); it
        -- rises onto its toes with its wings raised high and its neck lifted skyward (the burst at 0.42: Blasts.HaloAscension, three rings
        -- rising from its feet to its crown); it holds, then settles.
        local SC = {
            FAR = 90, -- studs from the camera past which nobody can see it fidget: its bones rest
            SOLE = 1.2233, -- metres from the middle of its box (the RootPart's cube counted) down to its feet (spirit_crane.py)
            -- a wing spread out of its fold (left; the right mirrors y): WingX1 = Angles(0, 0, -s * flap) * Angles(OPEN_X * o, s * OPEN_Y * o, 0)
            OPEN_X = -1.05,
            OPEN_Y = -1.48,
            FLEX = { 0.13, 0.22, 0.28 }, -- how far each outer wing bone trails the beat (Wing2, Wing3, Wing4)
            -- its walk: hip, knee and heel at sixteen steps through the cycle for the left leg (the right half a cycle on), found in Blender by a
            -- solver that keeps the foot flat on the ground as it slides back and lifts it 12 cm as it swings forward (planted within 1.2 mm),
            -- with the body bobbing WALK_BOB (lowest as each foot comes down); the foot turned back level
            WALK = {
                { 0.161, 0.004, -0.047 }, { 0.121, 0.005, -0.028 }, { 0.127, -0.008, -0.083 }, { 0.157, -0.027, -0.175 }, { 0.146, -0.035, -0.203 },
                { 0.057, -0.02, -0.107 }, { -0.045, -0.002, 0.011 }, { -0.123, 0.008, 0.089 }, { -0.163, 0.009, 0.108 }, { -0.16, -0.003, 0.059 },
                { -0.338, 0.043, 0.335 }, { -0.414, 0.076, 0.505 }, { -0.41, 0.096, 0.587 }, { -0.349, 0.106, 0.598 }, { -0.249, 0.102, 0.534 },
                { -0.113, 0.08, 0.379 },
            },
            WALK_RATE = 1.1, -- cycles a second at a full walk
            WALK_BOB = 0.012, -- metres
            -- its stances (game axes; turns x, y, z), each checked in Blender (spirit_crane.py: wings against body, neck and head and each other,
            -- legs against wings and tail, the head against the body, every seam between pieces, the feet on the ground, and along the blends)
            CROUCH = { -- feet where they stood, heels bent, body down CROUCH_DROP: the gather before a hop
                Body = { -0.08, 0, 0 }, Neck1 = { -0.1, 0, 0 }, Head = { 0.1, 0, 0 },
                LegL1 = { -0.214, 0, 0 }, LegL2 = { 0.09, 0, 0 }, LegL3 = { 0.465, 0, 0 }, FootL = { -0.261, 0, 0 },
                LegR1 = { -0.214, 0, 0 }, LegR2 = { 0.09, 0, 0 }, LegR3 = { 0.465, 0, 0 }, FootR = { -0.261, 0, 0 },
            },
            CROUCH_DROP = 0.08,
            HOP_LEGS = { LegL1 = { 0.35, 0, 0 }, LegL2 = { 0.3, 0, 0 }, LegL3 = { -0.75, 0, 0 }, FootL = { 0.1, 0, 0 },
                LegR1 = { 0.35, 0, 0 }, LegR2 = { 0.3, 0, 0 }, LegR3 = { -0.75, 0, 0 }, FootR = { 0.1, 0, 0 } }, -- in the air, legs folded
            HOP_HEIGHT = 0.22, -- metres off the ground at the top of its dancing hop
            NECK_UP = { Neck1 = { 0.12, 0, 0 }, Neck2 = { 0.1, 0, 0 }, Neck3 = { 0.06, 0, 0 }, Neck4 = { 0.05, 0, 0 }, Head = { 0.45, 0, 0 }, Crest = { -0.15, 0, 0 } },
            NECK_FORWARD = { Body = { -0.06, 0, 0 }, Neck1 = { -0.7, 0, 0 }, Neck2 = { -0.28, 0, 0 }, Neck3 = { 0.2, 0, 0 }, Neck4 = { 0.25, 0, 0 },
                Head = { 0.53, 0, 0 }, Crest = { -0.3, 0, 0 } },
            LEGS_TRAIL = { LegL1 = { -1.25, 0, 0 }, LegL2 = { 0.05, 0, 0 }, LegL3 = { -0.08, 0, 0 }, FootL = { -0.25, 0, 0 },
                LegR1 = { -1.25, 0, 0 }, LegR2 = { 0.05, 0, 0 }, LegR3 = { -0.08, 0, 0 }, FootR = { -0.25, 0, 0 } },
            TAIL_FLY = { Tail1 = { -0.2, 0, 0 }, Tail2 = { -0.08, 0, 0 }, Tail3 = { -0.05, 0, 0 } }, -- lifted over the trailing legs (+x lowers what points back)
            TAIL_UP = { Tail1 = { -0.25, 0, 0 }, Tail2 = { -0.12, 0, 0 }, Tail3 = { -0.08, 0, 0 } },
            PREEN = { Neck1 = { -0.1, 0.3, 0 }, Neck2 = { -0.25, 0.45, 0 }, Neck3 = { -0.35, 0.5, 0.1 }, Neck4 = { -0.3, 0.45, 0.1 }, Head = { -0.4, 0.35, 0.25 } }, -- (to its left; y and z flip for the right)
            BOW = { Body = { -0.2, 0, 0 }, Neck1 = { -0.35, 0, 0 }, Neck2 = { -0.25, 0, 0 }, Neck3 = { 0.05, 0, 0 }, Neck4 = { 0.15, 0, 0 }, Head = { 0.2, 0, 0 },
                Tail1 = { 0.25, 0, 0 } },
            FIDGET_TIME = { preen = 2.6, ruffle = 1.1, bow = 1.8, hop = 1.6, look = 2.4 },
            BONES = { "Body", "Chest", "Neck1", "Neck2", "Neck3", "Neck4", "Head", "Crest", "Tail1", "Tail2", "Tail3",
                "LegL1", "LegL2", "LegL3", "FootL", "LegR1", "LegR2", "LegR3", "FootR" },
            PEARL = Color3.fromRGB(225, 245, 245),
            TEAL = Color3.fromRGB(40, 210, 200),
        }

        -- a leg's turns at g through its cycle (0..1), between the solved steps
        function SC.walkAt(g)
            local rows = SC.WALK
            local n = #rows
            local x = (g % 1) * n
            local i = math.floor(x)
            local w = x - i
            local a, b = rows[i % n + 1], rows[(i + 1) % n + 1]
            return { a[1] + (b[1] - a[1]) * w, a[2] + (b[2] - a[2]) * w, a[3] + (b[3] - a[3]) * w }
        end

        local function animateSpiritCrane(rig, s, moving, fly, nova)
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > SC.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime
            local pace = math.max(moving, fly)
            local drop = dropToGround(rig, s, t, u, fly, SC.SOLE)

            -- the special: gathering, wings half open (to 0.3); risen, wings high and neck skyward (the burst at 0.42); holding; settling
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local special = progress > 0
            local gather = smoothstep(0.02, 0.28, progress) * (1 - smoothstep(0.34, 0.42, progress))
            local rise = smoothstep(0.32, 0.42, progress) * (1 - smoothstep(0.8, 0.97, progress))

            -- now and then, standing: a preen under one wing, a ruffling shake, a bow, a little dancing hop, a long look about
            s.nextFidget = s.nextFidget or t + 4
            if t >= s.nextFidget then
                local r = math.random()
                s.fidgetAt = t
                s.fidgetKind = if r < 0.24 then "preen" elseif r < 0.46 then "ruffle" elseif r < 0.64 then "bow" elseif r < 0.8 then "hop" else "look"
                s.fidgetSide = if math.random() < 0.5 then 1 else -1
                s.nextFidget = t + SC.FIDGET_TIME[s.fidgetKind] + 4 + math.random() * 6
            end
            local env = if s.fidgetAt then math.clamp((t - s.fidgetAt) / SC.FIDGET_TIME[s.fidgetKind], 0, 1) else 1
            local calmness = (1 - pace) * (if special then 0 else 1)
            local fidget = smoothstep(0, 0.2, env) * (1 - smoothstep(0.8, 1, env)) * calmness
            local function kind(name)
                return if s.fidgetKind == name then fidget else 0
            end

            local want = {}
            -- breathing; its neck swaying a little, its head bobbing
            local breath = math.sin(t * 1.2)
            addStance(want, { Chest = { 0.015 * breath, 0, 0 }, Body = { 0.006 * breath, 0, 0 } }, 1)
            addStance(want, { Neck2 = { 0.03 * math.sin(t * 0.7), 0.03 * math.sin(t * 0.43), 0 }, Neck3 = { -0.03 * math.sin(t * 0.7), 0.02 * math.sin(t * 0.43 + 0.6), 0 },
                Head = { 0.04 * math.sin(t * 0.9 + 1), 0, 0.03 * math.sin(t * 0.5) }, Crest = { 0.06 * math.sin(t * 1.7), 0.05 * math.sin(t * 1.3), 0 } }, calmness)

            -- the fidgets
            local side = s.fidgetSide or 1
            local preen = kind("preen")
            addStance(want, { Neck1 = { SC.PREEN.Neck1[1], SC.PREEN.Neck1[2] * side, 0 }, Neck2 = { SC.PREEN.Neck2[1], SC.PREEN.Neck2[2] * side, 0 },
                Neck3 = { SC.PREEN.Neck3[1], SC.PREEN.Neck3[2] * side, SC.PREEN.Neck3[3] * side }, Neck4 = { SC.PREEN.Neck4[1], SC.PREEN.Neck4[2] * side, SC.PREEN.Neck4[3] * side },
                Head = { SC.PREEN.Head[1] + 0.12 * math.sin(t * 14) * preen, SC.PREEN.Head[2] * side, SC.PREEN.Head[3] * side } }, preen)
            local ruffle = kind("ruffle")
            local shake = math.sin(t * 38) * ruffle
            addStance(want, { Body = { 0, 0, 0.03 * shake }, Tail1 = { 0, 0.12 * shake, 0 }, Tail2 = { 0, 0.15 * shake, 0 }, Crest = { 0, 0.2 * shake, 0.15 * shake },
                Head = { 0, 0, -0.06 * shake } }, 1)
            local bow = kind("bow")
            addStance(want, SC.BOW, bow * math.sin(math.pi * env))
            local look = kind("look")
            addStance(want, { Neck2 = { 0, 0.18 * side, 0 }, Neck3 = { 0, 0.25 * side, 0 }, Neck4 = { 0.04, 0.3 * side, 0.05 * side }, Head = { 0.05, 0.4 * side, 0.12 * side } }, look)

            -- the dancing hop: down into a crouch, up with its wings half open and legs folded, down again
            local hopKind = kind("hop") > 0
            local hopEnv = if s.fidgetKind == "hop" then env else 1
            local crouch = if hopKind then (smoothstep(0, 0.2, hopEnv) * (1 - smoothstep(0.25, 0.32, hopEnv)) + smoothstep(0.7, 0.78, hopEnv) * (1 - smoothstep(0.85, 1, hopEnv))) * calmness else 0
            local air = if hopKind then math.sin(math.pi * math.clamp((hopEnv - 0.28) / 0.46, 0, 1)) * calmness else 0
            addStance(want, SC.CROUCH, crouch)
            addStance(want, SC.HOP_LEGS, air)
            addStance(want, SC.TAIL_UP, air)

            -- the special's pose: gathering (a crouch, wings half open), then risen skyward
            addStance(want, SC.CROUCH, gather * 0.7)
            addStance(want, SC.NECK_UP, rise)
            addStance(want, SC.TAIL_UP, rise)

            -- its walk: an elegant high step, each foot planted flat; its body bobbing, its neck taking the bob back so its head rides level
            local onFoot = moving * (1 - fly)
            s.stride = (s.stride or 0) + dt * SC.WALK_RATE * onFoot
            for leg, lead in { L = 0, R = 0.5 } do
                local a = SC.walkAt(s.stride + lead)
                addStance(want, { ["Leg" .. leg .. "1"] = { a[1], 0, 0 }, ["Leg" .. leg .. "2"] = { a[2], 0, 0 }, ["Leg" .. leg .. "3"] = { a[3], 0, 0 },
                    ["Foot" .. leg] = { -(a[1] + a[2] + a[3]), 0, 0 } }, onFoot)
            end
            local bobPhase = math.cos(4 * math.pi * s.stride)
            addStance(want, { Neck1 = { 0.04 * bobPhase, 0, 0 }, Neck3 = { -0.03 * bobPhase, 0, 0 }, Head = { -0.03 * bobPhase, 0, 0 },
                Tail1 = { 0.03 * math.sin(2 * math.pi * s.stride), 0.04 * math.sin(2 * math.pi * s.stride), 0 } }, onFoot)

            -- in the air: neck stretched out ahead, legs trailed straight back under its tail
            addStance(want, SC.NECK_FORWARD, fly)
            addStance(want, SC.LEGS_TRAIL, fly)
            addStance(want, SC.TAIL_FLY, fly)

            -- its gaze, standing: often at you (not while it preens, bows or rises)
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 2.5 + math.random() * 3.5
                s.atYou = math.random() < 0.55
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.1, (math.random() - 0.5) * 0.25
            end
            local calm = (1 - 0.8 * pace) * (1 - math.max(preen, bow, look, rise, gather)) * (if special then 0 else 1)
            local wantYaw = (if s.atYou then math.clamp(math.atan2(-toYou.X, -toYou.Z), -0.8, 0.8) else s.gazeYaw) * calm
            local wantPitch = (if s.atYou then math.clamp(toYou.Y * 0.5, -0.2, 0.3) else s.gazePitch) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 3)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 3)
            addStance(want, { Neck3 = { 0.05 * s.pitch, 0.2 * s.yaw, 0 }, Neck4 = { 0.1 * s.pitch, 0.3 * s.yaw, 0 }, Head = { 0.25 * s.pitch, 0.45 * s.yaw, 0.08 * s.yaw } }, 1)

            -- the legs held upright under a pitched body while it stands (the feet stay flat where they are)
            local pitch = (want.Body or Vector3.zero).X
            local standing = 1 - fly
            for _, leg in { "L", "R" } do
                addStance(want, { ["Leg" .. leg .. "1"] = { -pitch, 0, 0 } }, standing * (1 - crouch) * (1 - gather * 0.7))
            end

            -- the body: down to the ground, its walk's bob, the crouch, the hop and the rise onto its toes
            local lift = (-SC.WALK_BOB * math.cos(4 * math.pi * s.stride) * onFoot - SC.CROUCH_DROP * math.max(crouch, gather * 0.7) + SC.HOP_HEIGHT * air
                + 0.04 * rise) * u - drop
            for _, name in SC.BONES do
                local a = want[name] or Vector3.zero
                pose(m[name], CFrame.new(0, if name == "Body" then lift else 0, 0) * CFrame.Angles(a.X, a.Y, a.Z))
            end

            -- its wings: folded, settling with each breath; spread and beating slow and deep in flight, the tips trailing the beat; half open
            -- for the hop and as it gathers; raised high as it rises; a quick shake as it ruffles
            s.beat = ((s.beat or 0) + dt * (1.6 + 0.6 * fly) * 2 * math.pi) % (2 * math.pi)
            local b = math.sin(s.beat)
            local open = math.clamp(math.max(fly, 0.5 * gather, rise, 0.75 * air, 0.12 * ruffle), 0, 1)
            local flap = (0.6 * b + 0.05) * fly + 0.15 * gather + 0.75 * rise + 0.45 * air + 0.1 * ruffle + 0.01 * breath
            for _, wing in { "L", "R" } do
                local sgn = if wing == "L" then 1 else -1
                pose(m["Wing" .. wing .. "1"], CFrame.Angles(0, 0, -sgn * flap) * CFrame.Angles(SC.OPEN_X * open, sgn * SC.OPEN_Y * open, 0))
                for k = 2, 4 do
                    local flex = -SC.FLEX[k - 1] * b * fly - (0.1 + 0.05 * k) * (rise + 0.6 * air) + 0.06 * shake
                    pose(m["Wing" .. wing .. k], CFrame.Angles(0, sgn * flex, 0))
                end
            end
        end

        -- It rises (animateSpiritCrane, the burst): three luminous rings rise from its feet to its crown and burst into drifting pearl feathers.
        -- (Its feet and crown are the skinned rig's FootL, FootR and Crest bones: a bone's WorldPosition leaves out only its own turn, which never
        -- moves its own origin.)
        function Blasts.HaloAscension(rig, fx)
            local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
            local footL, footR, crownPoint = rig.points.FootL, rig.points.FootR, rig.points.Crest
            local ankle = 0.05 * (rig.meters or 0) -- (the foot bones sit at the ankles, 5 cm over the soles)
            local ground = if footL and footR then (footL.WorldPosition + footR.WorldPosition) / 2 - Vector3.new(0, ankle, 0) else origin - Vector3.new(0, 1.2 * u, 0)
            local crown = if crownPoint then crownPoint.WorldPosition else origin + Vector3.new(0, 1.5 * u, 0)
            local height = crown.Y - ground.Y + 0.3 * u

            for index, delay in { 0, 0.15, 0.3 } do
                local color = if index == 1 then colors.Gold elseif index == 2 then colors.Sun else colors.Orange
                local radius = (1.3 - 0.15 * index) * u
                local segments = 20
                for step = 1, segments do
                    local angle = step / segments * 2 * math.pi + index * 0.4
                    local out = Vector3.new(math.cos(angle), 0, math.sin(angle))
                    local arc = 2 * math.pi * radius / segments
                    local here = ground + out * radius
                    local bead = neon(Vector3.new(0.05 * u, 0.05 * u, arc * 0.8), CFrame.lookAt(here, here + out:Cross(Vector3.yAxis)), color)
                    bead.Transparency = 1
                    local top = Vector3.new(crown.X, ground.Y + height, crown.Z) + out * 0.3 * u
                    TweenService:Create(bead, TweenInfo.new(0.1, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, delay), { Transparency = 0.2 }):Play()
                    TweenService:Create(bead, TweenInfo.new(0.8, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, 0, false, delay), {
                        CFrame = CFrame.lookAt(top, top + out:Cross(Vector3.yAxis)),
                        Size = Vector3.new(0.03 * u, 0.03 * u, arc * 0.25),
                    }):Play()
                    tweenAfter(delay + 0.7, bead, TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
                end
            end

            local halo = neon(Vector3.one * 0.15 * u, CFrame.new(crown), colors.Sun)
            halo.Shape = Enum.PartType.Ball
            halo.Transparency = 1
            TweenService:Create(halo, TweenInfo.new(0.15, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, 0.75), { Transparency = 0.3 }):Play()
            tweenAfter(0.9, halo, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                Size = Vector3.one * 1.6 * u,
                Transparency = 1,
            })

            for index = 1, 12 do
                local angle = index / 12 * 2 * math.pi + math.random() * 0.3
                local out = Vector3.new(math.cos(angle), 0, math.sin(angle))
                local start = crown + Vector3.new(0, 0.2 * u, 0)
                local plume = neon(Vector3.new(0.07, 0.015, 0.26) * u, CFrame.lookAt(start, start + out), if index % 3 == 0 then colors.Orange else colors.Sun)
                plume.Transparency = 1
                local mesh = Instance.new("SpecialMesh")
                mesh.MeshType = Enum.MeshType.Sphere
                mesh.Parent = plume
                local drift = angle + 0.8
                local finish = start + Vector3.new(math.cos(drift), 0, math.sin(drift)) * (1.4 + math.random() * 0.6) * u - Vector3.new(0, (0.6 + math.random() * 0.5) * u, 0)
                TweenService:Create(plume, TweenInfo.new(0.1, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, 0.8), { Transparency = 0.15 }):Play()
                tweenAfter(0.9, plume, TweenInfo.new(0.5, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), {
                    CFrame = CFrame.lookAt(finish, finish + Vector3.new(math.cos(drift + 1.4), -0.3, math.sin(drift + 1.4))),
                    Transparency = 1,
                })
            end

            local light = Instance.new("PointLight")
            light.Color = colors.Gold
            light.Range = 12 * u
            light.Brightness = 2
            light.Parent = halo
            TweenService:Create(light, TweenInfo.new(1.3), { Brightness = 0 }):Play()
            if rig.burst then
                rig.burst:Emit(25)
            end
        end

        PetRig.Profiles.SpiritCrane = {
            Skinned = true,
            Bones = {
                "Body", "Chest", "Neck1", "Neck2", "Neck3", "Neck4", "Head", "Crest", "Tail1", "Tail2", "Tail3",
                "WingL1", "WingL2", "WingL3", "WingL4", "WingR1", "WingR2", "WingR3", "WingR4",
                "LegL1", "LegL2", "LegL3", "FootL", "LegR1", "LegR2", "LegR3", "FootR",
            },
            Points = { "Crest", "Tail3", "WingL4", "WingR4", "FootL", "FootR" },
            GlowColors = { -- (as the jointed crane had them)
                a0f3f1 = Color3.fromRGB(30, 215, 205), -- its lotus crown
                ["95eded"] = Color3.fromRGB(20, 195, 210), -- the tips of its crest, wings and streamers
                edce76 = Color3.fromRGB(235, 160, 30), -- its irises
                ["3fe1dd"] = Color3.fromRGB(0, 185, 175), -- the turquoise rings round its eyes
            },
            Effects = {
                Light = "Body",
                Pulse = "Body",
                Burst = "Body",
                Sparks = { "Crest", "Tail3" },
                Trail = { "WingL4", "WingR4" },
                Blast = "HaloAscension",
                NovaLight = 3,
            },
            Colors = {
                Gold = SC.TEAL,
                Amber = Color3.fromRGB(30, 55, 70),
                Orange = Color3.fromRGB(230, 170, 60),
                Sun = SC.PEARL,
                Ivory = Color3.fromRGB(250, 250, 245),
            },
            Animate = animateSpiritCrane,
        }
    end
end
