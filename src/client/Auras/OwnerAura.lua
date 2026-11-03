-- OwnerAura: the owner's own aura, designed on the Studio AuraWorkbench (2026-11-03/04) and worn by
-- the user ids in GameConfig.OwnerAura in place of their realm aura. Its pieces are kept as a
-- template in ReplicatedStorage.AuraMeshes.OwnerAura:
--   Ground  the energy circle (with the surge's ripple and dust ring), the gold and silver rising
--           light, the rising silver, the drifting mist, the embers and the gold and silver ground
--           clouds: each held at its Height above the floor under the character, and turned by its
--           Spin (radians a second) when it has one
--   Body    the two vortex portals and the chain glitter rods, held round the root at their Offset,
--           and the celestial sphere, which follows the head
--   Torso   the sphere's tether end (with its rising motes), for the upper torso
--   Hands   on each hand, a chain into its portal and three silver smoke beams along it
--   BodyHighlight  the faint gold outline that flashes silver at a surge
-- and, built here: the body aura (RealmAura.bodyAura, gold) and four tapered ribbons spiralling from
-- the shins to above the head.
--
-- What moves, every frame:
--   the sphere follows the head on an underdamped spring, pulses with the torso's speed, trembles on
--     sharp moves, breathes at rest, and swells with the surge; its one-particle layers re-emit on a
--     timer and scale with the pulse; three stars orbit it
--   the rising silver's emitters sweep: each one's Acceleration swings on smooth noise (its Sweep,
--     Lift and Tempo attributes)
--   the chains shake: each hand beam's curve trembles round its base (Curve0, Curve1, Jitter), and
--     the portal end of each chain wobbles
--   the surge, while meditating: every 6 to 8 s it builds for 1.1 s and strikes. At the strike the
--     body flashes silver, the ripple and dust ring burst, the embers scatter, the light rings rise
--     faster and denser, the sphere bursts with sparkles and the chains rattle. A viewer's screen
--     near the aura darkens through the build, flashes at the strike and shakes, scaled by the
--     camera's distance
--
-- The portals, chains and their smoke and glitter show only while the owner meditates, when the
-- floating pose spreads the arms toward them (Character/PoseController).
-- Other players see a lighter aura with distance: beyond NEAR_LOD studs every emitter's rate halves,
-- and beyond FAR_LOD it drops to a fifth. The owner always sees their own in full.
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RealmAura = require(script.Parent:WaitForChild("RealmAura"))

local OwnerAura = {}

local RIBBON_RADIUS = 3.2
local RIBBON_LOW, RIBBON_HIGH = -2.1, 2.3   -- from the shins to just above the head
local RIBBON_PERIOD = 4.4
local RIBBON_SPIN = 2.6
local RIBBON_WIDTH = 1.8
local FLOOR_CHECK = 0.1                     -- seconds between floor checks
local MEDITATION_ONLY = { PortalLeft = true, PortalRight = true, ChainSmokeLeft = true, ChainSmokeRight = true }

local SPHERE_STIFF = 38                                   -- the spring's pull
local SPHERE_DAMP = 2 * math.sqrt(SPHERE_STIFF) * 0.55    -- under 1: a little overshoot, then settle
local SPHERE_CYCLE = 3.6                    -- the one-particle layers re-emit this often (4 s lives)
local SPHERE_LAYERS = { "LuminousOrb", "OuterSwirl", "ShineRays" }

local SURGE_BUILD, SURGE_SETTLE, SURGE_AFTER = 1.1, 1.6, 1.2   -- seconds
local SURGE_FLASH, SURGE_SHAKE = 0.35, 0.45                    -- seconds: the screen flash, the shake
local SCREEN_NEAR, SCREEN_FAR = 25, 75      -- studs: full screen effects inside, none beyond
local RIM, RIM_FLASH = Color3.fromRGB(255, 210, 120), Color3.fromRGB(255, 255, 255)
local RIM_TRANSPARENCY = 0.7

local NEAR_LOD, FAR_LOD = 50, 110           -- studs from the camera, for other players' auras
local LOD_CHECK = 0.5                       -- seconds between distance checks

local records = {}
local stepping = nil
local grade = nil                           -- the viewer's colour grade, shared by every owner aura
local shake = { since = -1, amp = 0, clock = 0 }

function OwnerAura.isOwner(player)
    return player ~= nil and table.find(GameConfig.OwnerAura.UserIds, player.UserId) ~= nil
end

local function template()
    local meshes = ReplicatedStorage:FindFirstChild("AuraMeshes")
    return meshes and meshes:FindFirstChild("OwnerAura")
end

-- 1 when the camera is near the aura, 0 far away
local function nearness(root)
    local camera = workspace.CurrentCamera
    if not camera then
        return 0
    end
    local distance = (camera.CFrame.Position - root.Position).Magnitude
    return math.clamp(1 - (distance - SCREEN_NEAR) / (SCREEN_FAR - SCREEN_NEAR), 0, 1)
end

-- switch the meditation pieces on or off (their emitters, beams and lights)
local function setMeditating(record, on)
    if record.meditating == on then
        return
    end
    record.meditating = on
    for _, inst in record.meditationItems do
        if inst.Parent then
            inst.Enabled = on
            if not on and inst:IsA("ParticleEmitter") then
                inst:Clear()
            end
        end
    end
end

-- other players' auras thin with distance; the owner's own never does
local function updateLod(record, dt)
    if record.player == Players.LocalPlayer then
        return
    end
    record.lodClock -= dt
    if record.lodClock > 0 then
        return
    end
    record.lodClock = LOD_CHECK
    local camera = workspace.CurrentCamera
    local distance = if camera then (camera.CFrame.Position - record.root.Position).Magnitude else 0
    local scale = if distance > FAR_LOD then 0.2 elseif distance > NEAR_LOD then 0.5 else 1
    if scale == record.lod then
        return
    end
    record.lod = scale
    for emitter, rate in record.rates do
        if emitter.Parent then
            emitter.Rate = rate * scale
        end
    end
end

local function stepSphere(record, dt)
    local s = record.sphere
    local surge = record.surge.value
    -- the body's motion: speed drives the pulse, acceleration the tremble (the idle peaks near 0.7)
    local v = (s.torso.Position - s.lastTorso) / dt
    local a = (v - s.lastV).Magnitude / dt
    s.lastTorso, s.lastV = s.torso.Position, v
    s.energy += (math.clamp(v.Magnitude / 0.5, 0, 1) - s.energy) * (1 - math.exp(-dt * 6))
    s.jolt += (math.clamp(a / 3, 0, 1) - s.jolt) * (1 - math.exp(-dt * 10))
    -- follow the head on the spring
    local target = s.head.Position + Vector3.new(0, s.height, 0)
    s.vel += (SPHERE_STIFF * (target - s.pos) - SPHERE_DAMP * s.vel) * dt
    s.pos += s.vel * dt
    local clock = record.clock
    local amp = 0.05 * s.jolt + 0.1 * surge
    local tremble = Vector3.new(math.noise(clock * 24, 1), math.noise(clock * 24, 2), math.noise(clock * 24, 3)) * 2 * amp
    local scale = 1 + 0.035 * math.sin(clock * 2.2) + 0.12 * s.energy + 0.14 * surge
    local size = s.base * scale
    s.part.Size = Vector3.new(size, size, size)
    s.part.CFrame = CFrame.new(s.pos + tremble) * CFrame.Angles(0, clock * 0.25, 0)
    if s.tether then
        s.tether.Position = Vector3.new(0, -size * 0.48, 0)
    end
    -- the star and its light: brighter with motion and the surge
    local lift = 1 + 0.5 * s.energy + 0.9 * surge
    if s.star then
        s.star.Brightness = 3 * lift
    end
    if s.light then
        s.light.Brightness = 1.6 * lift
    end
    -- the one-particle layers: one always showing, growing with the pulse
    s.layerClock += dt
    local fire = s.layerClock >= SPHERE_CYCLE
    if fire then
        s.layerClock -= SPHERE_CYCLE
    end
    for _, layer in s.layers do
        layer.emitter.Size = NumberSequence.new(layer.size * scale)
        if fire then
            layer.emitter:Emit(1)
        end
    end
    -- the orbiting stars, quicker in a surge
    for _, orb in s.orbs do
        local angle = orb.phase + clock * orb.speed * (1 + 0.5 * surge)
        orb.attachment.Position = orb.frame * Vector3.new(orb.radius * math.cos(angle), 0, orb.radius * math.sin(angle))
    end
    -- aim the tether's motes at the sphere (their emitter shoots along the attachment's up)
    if s.motes and s.tether then
        s.motes.WorldCFrame = CFrame.lookAt(s.motes.WorldPosition, s.tether.WorldPosition) * CFrame.Angles(-math.pi / 2, 0, 0)
    end
end

local function stepSurge(record, dt)
    local surge = record.surge
    if not record.meditating then
        surge.value, surge.build, surge.after, surge.since, surge.wait = 0, 0, 0, -1, 3
    else
        local value, build, after = 0, 0, 0
        surge.wait -= dt
        if surge.wait <= 0 then        -- the strike
            surge.wait = 6 + math.random() * 2
            surge.since = 0
            for _, emitter in surge.bursts do
                emitter.e:Emit(emitter.count)
            end
            for _, sound in surge.rattles do
                sound.PlaybackSpeed = 0.9 + math.random() * 0.2
                sound:Play()
            end
            if record.root == shake.root or shake.since < 0 or shake.since >= SURGE_SHAKE then
                shake.since, shake.root = 0, record.root
            end
        elseif surge.wait < SURGE_BUILD then   -- the build: an ease-in rise
            local k = 1 - surge.wait / SURGE_BUILD
            value, build = k * k, k * k
        end
        if surge.since >= 0 then
            surge.since += dt
            if surge.since < SURGE_SETTLE then
                value = math.max(value, (1 - surge.since / SURGE_SETTLE) ^ 2)
            end
            if surge.since < SURGE_AFTER then
                after = (1 - surge.since / SURGE_AFTER) ^ 2
            end
        end
        surge.value, surge.build, surge.after = value, build, after
    end
    -- the body's outline: a faint gold rim, flashing silver at the strike
    local after = surge.after
    if record.highlight then
        record.highlight.FillTransparency = 1 - 0.55 * after
        record.highlight.OutlineTransparency = RIM_TRANSPARENCY - (RIM_TRANSPARENCY - 0.1) * after
        record.highlight.OutlineColor = RIM:Lerp(RIM_FLASH, after)
    end
    -- the light rings rise faster and denser after the strike
    local lod = record.lod
    for _, ring in surge.rings do
        ring.e.Rate = ring.rate * lod * (1 + 1.2 * after)
        ring.e.Speed = NumberRange.new(ring.s0 * (1 + 0.8 * after), ring.s1 * (1 + 0.8 * after))
    end
    -- the chains shake harder with the surge
    local jerk = 1 + 3 * surge.value
    local t = record.clock * 16
    for _, j in record.jitters do
        j.beam.CurveSize0 = j.c0 + math.noise(t, j.seed, 1) * 2 * j.amp * jerk
        j.beam.CurveSize1 = j.c1 + math.noise(j.seed, t, 2) * 2 * j.amp * jerk
    end
    local te = record.clock * 22
    for _, e in record.chainEnds do
        e.attachment.Position = e.base + Vector3.new(math.noise(te, e.seed, 3), math.noise(te, e.seed, 4), math.noise(te, e.seed, 5)) * 0.12 * jerk
    end
end

-- the viewer's screen: the strongest nearby surge darkens it through the build and flashes it at
-- the strike
local function stepScreen()
    local build, flash = 0, 0
    for record in records do
        local near = nearness(record.root)
        local surge = record.surge
        local f = if surge.since >= 0 and surge.since < SURGE_FLASH then (1 - surge.since / SURGE_FLASH) ^ 2 else 0
        build = math.max(build, surge.build * near)
        flash = math.max(flash, f * near)
    end
    if not grade or not grade.Parent then
        grade = Instance.new("ColorCorrectionEffect")
        grade.Name = "OwnerAuraGrade"
        grade.Parent = Lighting
    end
    grade.Brightness = -0.07 * build + 0.28 * flash
    grade.Contrast = 0.15 * build + 0.1 * flash
    grade.Saturation = 0.12 * build
    grade.TintColor = Color3.new(1, 1, 1):Lerp(Color3.fromRGB(222, 232, 255), flash)
end

-- the camera shake runs after the camera has moved this frame
local function shakeCamera(dt)
    if shake.since < 0 or not shake.root then
        return
    end
    shake.since += dt
    shake.clock += dt
    if shake.since >= SURGE_SHAKE or not shake.root.Parent then
        shake.since = -1
        return
    end
    local camera = workspace.CurrentCamera
    local amp = math.rad(0.9) * (1 - shake.since / SURGE_SHAKE) ^ 2 * nearness(shake.root)
    if camera and amp > 0 then
        local t = shake.clock * 40
        camera.CFrame *= CFrame.Angles(math.noise(t, 1) * 2 * amp, math.noise(t, 2) * 2 * amp, math.noise(t, 3) * amp)
    end
end

local function step(dt)
    if dt <= 0 then
        return
    end
    for record in records do
        local root = record.root
        if not root:IsDescendantOf(workspace) then
            OwnerAura.destroy(record.fx)
            continue
        end
        record.clock += dt
        local clock = record.clock
        setMeditating(record, record.player:GetAttribute("IsCultivating") == true)
        updateLod(record, dt)

        -- the ribbons: up and down on a smooth cosine, a quarter period apart, alternate ways round
        for _, r in record.ribbons do
            r.angle += dt * RIBBON_SPIN * r.dir
            local k = 0.5 - 0.5 * math.cos((clock / RIBBON_PERIOD + r.phase) * math.pi * 2)
            local y = RIBBON_LOW + (RIBBON_HIGH - RIBBON_LOW) * k
            local pos = Vector3.new(math.cos(r.angle) * RIBBON_RADIUS, y, math.sin(r.angle) * RIBBON_RADIUS)
            r.a0.Position = pos + Vector3.new(0, RIBBON_WIDTH / 2, 0)
            r.a1.Position = pos - Vector3.new(0, RIBBON_WIDTH / 2, 0)
        end

        -- the floor under the character, ten times a second
        record.floorClock -= dt
        if record.floorClock <= 0 then
            record.floorClock = FLOOR_CHECK
            local hit = workspace:Raycast(root.Position, Vector3.new(0, -14, 0), record.rayParams)
            record.floorY = if hit then hit.Position.Y else root.Position.Y - 3
        end
        local _, yaw = root.CFrame:ToOrientation()
        local flat = CFrame.fromOrientation(0, yaw, 0)
        for _, g in record.ground do
            g.part.CFrame = CFrame.new(root.Position.X, record.floorY + g.height, root.Position.Z) * flat * g.turn
                * CFrame.Angles(0, clock * g.spin, 0)
        end
        for _, b in record.body do
            b.part.CFrame = root.CFrame * b.offset
        end

        -- the rising silver sweeps: each emitter's push swings on its own smooth noise
        for _, sw in record.sweeps do
            local t = clock * sw.tempo
            local x = math.noise(t, sw.seed, 0) * 2
            local z = math.noise(sw.seed, t, 7) * 2
            local gust = 1 + math.max(0, math.noise(t * 0.5, sw.seed, 3) * 2 - 0.4) * 1.5
            sw.e.Acceleration = Vector3.new(x * sw.sweep * gust, sw.lift, z * sw.sweep * gust)
        end

        stepSurge(record, dt)
        if record.sphere then
            stepSphere(record, dt)
        end

        -- glitter bursting at random points along the chains, while meditating
        if record.meditating and #record.rods > 0 then
            record.nextBurst -= dt
            if record.nextBurst <= 0 then
                record.nextBurst = 0.25 + math.random() * 0.35
                local rod = record.rods[math.random(1, #record.rods)]
                local at = rod:FindFirstChild("BurstPoint")
                if at then
                    at.Position = Vector3.new(0, 0, (math.random() - 0.5) * rod.Size.Z * 0.9)
                    local glitter, flashFx = at:FindFirstChild("GlitterBurst"), at:FindFirstChild("BurstFlash")
                    if glitter then
                        glitter:Emit(math.random(40, 60))
                    end
                    if flashFx then
                        flashFx:Emit(1)
                    end
                end
            end
        end
    end
    stepScreen()
end

-- the sphere's moving parts, found in its clone
local function buildSphere(record, part, character)
    local head = character:FindFirstChild("Head")
    local torso = character:FindFirstChild("UpperTorso") or character:FindFirstChild("Torso")
    if not head or not torso then
        return
    end
    local core = part:FindFirstChild("Core")
    local s = { part = part, head = head, torso = torso, height = part:GetAttribute("Height") or 8,
        base = part:GetAttribute("BaseSize") or part.Size.X, layers = {}, orbs = {}, layerClock = 0,
        energy = 0, jolt = 0, vel = Vector3.zero, lastTorso = torso.Position, lastV = Vector3.zero,
        star = core and core:FindFirstChild("Star"), light = core and core:FindFirstChild("CoreLight"),
        tether = part:FindFirstChild("Tether") }
    s.pos = head.Position + Vector3.new(0, s.height, 0)
    if core then
        for _, name in SPHERE_LAYERS do
            local emitter = core:FindFirstChild(name)
            if emitter then
                table.insert(s.layers, { emitter = emitter, size = emitter:GetAttribute("BaseParticleSize") or 5 })
                emitter:Emit(1)
            end
        end
        local sparkle = core:FindFirstChild("SurgeSparkle")
        if sparkle then
            table.insert(record.surge.bursts, { e = sparkle, count = 8 })
        end
    end
    for i = 1, 3 do
        local orb = part:FindFirstChild("Orb" .. i)
        if orb and orb:GetAttribute("RingFrame") then
            table.insert(s.orbs, { attachment = orb, frame = orb:GetAttribute("RingFrame"), radius = orb:GetAttribute("Radius") or 5,
                speed = orb:GetAttribute("Speed") or 1, phase = i * 2.1 })
        end
    end
    -- the tether's end on the upper torso, its beams relinked to it
    local source = template()
    local tetherSource = source and source:FindFirstChild("Torso") and source.Torso:FindFirstChild("SphereTether")
    if tetherSource then
        local motes = tetherSource:Clone()
        motes.Name = "OwnerSphereTether"
        motes.Parent = torso
        table.insert(record.made, motes)
        s.motes = motes
        for _, beam in part:GetChildren() do
            if beam:IsA("Beam") and beam.Name:sub(1, 6) == "Tether" then
                beam.Attachment0 = motes
            end
        end
    end
    record.sphere = s
end

-- builds the owner's aura round a character; returns its folder (OwnerAuraFX, under the root), or
-- nil when the template is missing
function OwnerAura.build(player, character, root)
    local source = template()
    if not source then
        warn("[OwnerAura] ReplicatedStorage.AuraMeshes.OwnerAura is missing")
        return nil
    end
    local old = root:FindFirstChild("OwnerAuraFX")
    if old then
        OwnerAura.destroy(old)
    end
    local fx = Instance.new("Folder")
    fx.Name = "OwnerAuraFX"
    fx.Parent = root

    local record = { player = player, character = character, root = root, fx = fx, clock = 0, floorClock = 0,
        floorY = root.Position.Y - 3, ground = {}, body = {}, ribbons = {}, rods = {}, meditationItems = {},
        made = {}, meditating = nil, nextBurst = 0, sweeps = {}, jitters = {}, chainEnds = {}, rates = {},
        lod = 1, lodClock = 0,
        surge = { value = 0, build = 0, after = 0, since = -1, wait = 3, bursts = {}, rattles = {}, rings = {} } }
    local rayParams = RaycastParams.new()
    rayParams.FilterType = Enum.RaycastFilterType.Exclude
    rayParams.FilterDescendantsInstances = { character }
    record.rayParams = rayParams

    local function collect(inst)
        for _, d in inst:GetDescendants() do
            if d:IsA("ParticleEmitter") or d:IsA("Beam") or d:IsA("Light") then
                table.insert(record.meditationItems, d)
            end
        end
    end

    for _, src in source.Ground:GetChildren() do
        local part = src:Clone()
        part.Parent = fx
        table.insert(record.ground, { part = part, height = src:GetAttribute("Height") or 0,
            turn = src:GetAttribute("Turn") or CFrame.identity, spin = src:GetAttribute("Spin") or 0 })
        for _, e in part:GetDescendants() do
            if e:IsA("ParticleEmitter") and e:GetAttribute("Sweep") then
                table.insert(record.sweeps, { e = e, seed = math.random() * 100, sweep = e:GetAttribute("Sweep"),
                    lift = e:GetAttribute("Lift") or 0, tempo = e:GetAttribute("Tempo") or 1 })
            end
        end
    end
    -- the surge's pieces on the ground
    local circle = fx:FindFirstChild("GroundCircle")
    for _, name in { "SurgeRipple", "SurgeShock" } do
        local e = circle and circle:FindFirstChild(name, true)
        if e then
            table.insert(record.surge.bursts, { e = e, count = 1 })
        end
    end
    local embers = fx:FindFirstChild("GroundEmbers")
    if embers and embers:FindFirstChild("Embers") then
        table.insert(record.surge.bursts, { e = embers.Embers, count = 30 })
    end
    for _, pair in { { "LightBeams", "LightBeam" }, { "SilverBeams", "SilverBeam" } } do
        local part = fx:FindFirstChild(pair[1])
        local e = part and part:FindFirstChild(pair[2])
        if e then
            table.insert(record.surge.rings, { e = e, rate = e.Rate, s0 = e.Speed.Min, s1 = e.Speed.Max })
        end
    end

    local portals = {}
    for _, src in source.Body:GetChildren() do
        local part = src:Clone()
        part.Parent = fx
        if part.Name == "CelestialSphere" then
            buildSphere(record, part, character)
        else
            table.insert(record.body, { part = part, offset = src:GetAttribute("Offset") or CFrame.identity })
        end
        if MEDITATION_ONLY[part.Name] then
            collect(part)
        end
        if part.Name:sub(1, 6) == "Portal" then
            portals[part.Name:sub(7)] = part
        elseif part.Name:sub(1, 10) == "ChainSmoke" then
            table.insert(record.rods, part)
        end
    end

    -- the chains and their smoke, from each hand into its portal
    for _, side in { "Left", "Right" } do
        local hand = character:FindFirstChild(side .. "Hand")
        local folder = source.Hands:FindFirstChild(side .. "Hand")
        local portal = portals[side]
        if hand and folder and portal then
            local grip = folder.ChainGrip:Clone()
            grip.Name = "OwnerChainGrip"
            grip.Parent = hand
            table.insert(record.made, grip)
            local rattle = grip:FindFirstChildOfClass("Sound")
            if rattle then
                table.insert(record.surge.rattles, rattle)
            end
            local chainEnd = portal:FindFirstChild("ChainEnd", true)
            if chainEnd then
                table.insert(record.chainEnds, { attachment = chainEnd, base = chainEnd.Position, seed = math.random() * 100 })
            end
            for _, src in folder:GetChildren() do
                if src:IsA("Beam") then
                    local beam = src:Clone()
                    beam.Name = "Owner" .. src.Name
                    beam.Attachment0 = grip
                    beam.Attachment1 = chainEnd
                    beam.Parent = hand
                    table.insert(record.made, beam)
                    table.insert(record.meditationItems, beam)
                    if beam:GetAttribute("Jitter") then
                        table.insert(record.jitters, { beam = beam, seed = math.random() * 100, amp = beam:GetAttribute("Jitter"),
                            c0 = beam:GetAttribute("Curve0") or 0, c1 = beam:GetAttribute("Curve1") or 0 })
                    end
                end
            end
        end
    end

    -- the body's outline
    local highlightSource = source:FindFirstChild("BodyHighlight")
    if highlightSource then
        local highlight = highlightSource:Clone()
        highlight.Adornee = character
        highlight.Enabled = true
        highlight.Parent = fx
        record.highlight = highlight
    end

    -- the ribbons: tapered trails behind points on a helix round the body
    local texture = source:GetAttribute("RibbonTexture") or "rbxassetid://124753331461910"
    for i, phase in { 0, 0.5, 0.25, 0.75 } do
        local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
        a0.Name, a1.Name = "OwnerRibbon" .. i .. "A", "OwnerRibbon" .. i .. "B"
        a0.Parent, a1.Parent = root, root
        local trail = Instance.new("Trail")
        trail.Name = "OwnerRibbon" .. i
        trail.Attachment0, trail.Attachment1 = a0, a1
        trail.Texture = texture
        trail.TextureMode = Enum.TextureMode.Stretch
        trail.Color = ColorSequence.new(Color3.fromRGB(255, 220, 140))
        trail.LightEmission = 1
        trail.Brightness = 4
        trail.LightInfluence = 0
        trail.FaceCamera = false
        trail.Lifetime = 1.25
        trail.MinLength = 0.05
        trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.14, 0.02),
            NumberSequenceKeypoint.new(0.65, 0.18), NumberSequenceKeypoint.new(1, 1) })
        trail.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05), NumberSequenceKeypoint.new(0.2, 1),
            NumberSequenceKeypoint.new(0.45, 0.9), NumberSequenceKeypoint.new(1, 0.04) })
        trail.Parent = root
        table.insert(record.made, a0)
        table.insert(record.made, a1)
        table.insert(record.made, trail)
        table.insert(record.ribbons, { a0 = a0, a1 = a1, phase = phase, dir = if i % 2 == 1 then 1 else -1, angle = i * math.pi / 2 })
    end

    -- the gold body aura over the whole body
    record.undressBody = RealmAura.bodyAura(root, fx, source:GetAttribute("BodyColor") or Color3.fromRGB(255, 170, 40),
        source:GetAttribute("BodyLevel") or 0.4)

    -- every emitter's own rate, for the distance thinning of other players' auras
    local function noteRates(inst)
        for _, e in inst:GetDescendants() do
            if e:IsA("ParticleEmitter") and e.Rate > 0 then
                record.rates[e] = e.Rate
            end
        end
    end
    noteRates(fx)
    for _, inst in record.made do
        if inst:IsA("ParticleEmitter") then
            record.rates[inst] = inst.Rate
        else
            noteRates(inst)
        end
    end

    setMeditating(record, player:GetAttribute("IsCultivating") == true)
    records[record] = true
    record.fxConnection = fx.Destroying:Connect(function()
        OwnerAura.destroy(fx)
    end)
    if not stepping then
        stepping = RunService.RenderStepped:Connect(step)
        RunService:BindToRenderStep("OwnerAuraShake", Enum.RenderPriority.Camera.Value + 2, shakeCamera)
    end
    return fx
end

-- removes everything the aura made, at once (a rebuild in the same frame dresses the same parts)
function OwnerAura.destroy(fx)
    for record in records do
        if record.fx == fx then
            records[record] = nil
            if record.fxConnection then
                record.fxConnection:Disconnect()
            end
            if record.undressBody then
                record.undressBody()
            end
            for _, inst in record.made do
                inst:Destroy()
            end
            if shake.root == record.root then
                shake.since, shake.root = -1, nil
            end
        end
    end
    if fx.Parent then
        fx:Destroy()
    end
    if next(records) == nil and stepping then
        stepping:Disconnect()
        stepping = nil
        RunService:UnbindFromRenderStep("OwnerAuraShake")
        if grade then
            grade:Destroy()
            grade = nil
        end
    end
end

return OwnerAura
