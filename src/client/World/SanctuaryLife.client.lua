-- The Blossom Sanctuary's life, drawn by each client and cheap (the owner's directive, 2026-11-16: wind, petals, water, koi):
-- * koi swimming smooth loops round the pond (Pond.Loops, Pond.Koi: WorldBuilder.buildSanctuary), their tails swinging, and now
--   and then one leaping out with a small splash, a ripple and a sound;
-- * soft ripples rising where the koi swim (the kit's BS_Ripple ring, when it is in the place);
-- * blossom petals drifting past the camera on a slowly turning wind with gusts (one emitter that follows the camera, and one
--   under the Elder tree by the bridge); fewer in rain, none with Reduced Effects off-island; lit by the scene (LightInfluence 1),
--   so they darken with the night on their own;
-- * the blossom canopies swaying a little in the same wind (each canopy turned a fraction of a degree about its base), near the
--   camera only, not on a phone (Quality.Low) or with Reduced Effects;
-- * the pond's water sound near it, and a koi's splash; now and then a few seconds of wind chimes at the shrine on the Lookout.
-- Nothing here touches Lighting or the weather's own effects (WeatherController owns those); it only reads the weather.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local WeatherRules = require(ReplicatedStorage:WaitForChild("WeatherRules"))
local Quality = require(script.Parent.Parent:WaitForChild("Performance"):WaitForChild("Quality"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local ISLAND = GameConfig.TrainingStation.Island

local KOI_SPEED = 2.6          -- studs a second along its loop
local KOI_NEAR = 220           -- studs from the pond within which the koi swim (beyond, they rest where they are)
local LEAP_EVERY = { 7, 15 }   -- seconds between leaps (one fish at a time)
local LEAP_TIME = 0.95
local LEAP_HEIGHT = 2.4
local RIPPLE_EVERY = { 1.2, 2.6 }
local RIPPLE_TIME = 2.4
local SWAY_NEAR = 170          -- canopies sway within this of the camera
local SWAY_ANGLE = math.rad(0.7)
local PETAL_RATE = if Quality.Low then 10 else 24
local PETAL_REDUCED = 4
-- Roblox's own soft puff, small, squashed and tumbling: reads as a soft petal (its plain square read as white confetti in Play)
local PETAL_TEXTURE = "rbxasset://textures/particles/smoke_main.dds"
local SPLASH_TEXTURE = "rbxasset://textures/particles/SquareParticle.png"

local function reduced()
    return player:GetAttribute("SettingReducedEffects") == true
end

local world = Workspace:WaitForChild("FloatingIslands")
local island = world:WaitForChild(ISLAND, 60)
if not island then
    return
end

-- ---------- the wind: one slowly turning direction, with gusts ----------
local windAngle, gust, gustUntil, nextGust = math.random() * math.pi * 2, 0, 0, os.clock() + 8
local function wind(now, dt)
    windAngle += math.noise(now * 0.05, 3.7) * dt * 0.6
    if now > nextGust then
        gustUntil = now + 2.5 + math.random() * 2
        nextGust = now + 9 + math.random() * 10
    end
    local want = if now < gustUntil then 1 else 0
    gust += (want - gust) * math.min(1, dt * 1.5)
    return Vector3.new(math.cos(windAngle), 0, math.sin(windAngle)), gust
end

local function raining()
    local _, _, from, to, k = WeatherRules.current()
    return (if k >= 0.5 then to else from) == "Rain"
end

-- ---------- petals ----------
local PINK = Color3.fromRGB(236, 132, 172)
local PALE = Color3.fromRGB(250, 192, 214)
local function petalEmitter(parent)
    local e = Instance.new("ParticleEmitter")
    e.Name = "Petals"
    e.Texture = PETAL_TEXTURE
    e.Color = ColorSequence.new(PALE, PINK)
    e.LightEmission = 0.15
    e.LightInfluence = 1
    e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 0.16) })
    -- the squash swings from flat to wide and back: a small square tumbling end over end, read as a petal
    e.Squash = NumberSequence.new({ NumberSequenceKeypoint.new(0, -0.7), NumberSequenceKeypoint.new(0.12, 0.7), NumberSequenceKeypoint.new(0.25, -0.6),
        NumberSequenceKeypoint.new(0.4, 0.7), NumberSequenceKeypoint.new(0.55, -0.7), NumberSequenceKeypoint.new(0.7, 0.6),
        NumberSequenceKeypoint.new(0.85, -0.7), NumberSequenceKeypoint.new(1, 0.6) })
    e.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.1, 0.05), NumberSequenceKeypoint.new(0.85, 0.1),
        NumberSequenceKeypoint.new(1, 1) })
    e.Lifetime = NumberRange.new(6, 9)
    e.Speed = NumberRange.new(0.5, 1.5)
    e.SpreadAngle = Vector2.new(180, 180)
    e.Rotation = NumberRange.new(0, 360)
    e.RotSpeed = NumberRange.new(-120, 120)
    e.Drag = 0.8
    e.Acceleration = Vector3.new(0, -1.6, 0)
    e.Shape = Enum.ParticleEmitterShape.Box
    e.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
    e.Rate = 0
    e.Parent = parent
    return e
end

local function carrier(name, size)
    local part = Instance.new("Part")
    part.Name = name
    part.Size = size
    part.Transparency = 1
    part.Anchored = true
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.CastShadow = false
    return part
end

local cameraPetals = carrier("SanctuaryPetals", Vector3.new(70, 18, 70))
local cameraEmitter = petalEmitter(cameraPetals)
local treePetals = carrier("ElderPetals", Vector3.new(26, 2, 26))
local treeEmitter = petalEmitter(treePetals)
local carriedAt = nil

-- the Elder by the bridge: under its canopy (found once its kit has streamed in)
-- (kept between frames: searching the kit's ~430 pieces each frame cost about 0.2 ms; searched again at most once a second
-- while it isn't streamed in, and whenever the one found streams out)
local elder, elderSearchedAt = nil, -math.huge
local function findElder()
    if elder and elder.Parent then
        return elder
    end
    local now = os.clock()
    if now - elderSearchedAt < 1 then
        return nil
    end
    elderSearchedAt = now
    local kit = island:FindFirstChild("Kit")
    local best = nil
    for _, part in kit and kit:GetChildren() or {} do
        if part:IsA("BasePart") and string.find(part.Name, "^BS_TreeElder__Blossom") then
            if not best or part.Size.X > best.Size.X then
                best = part
            end
        end
    end
    elder = best
    return best
end

-- ---------- canopies ----------
local canopies = {} -- [part] = { rest = CFrame, pivot = Vector3 (in the part's space), phase = number }
local function addCanopy(part)
    if canopies[part] or not part:IsA("BasePart") then
        return
    end
    local name = part.Name
    if string.find(name, "__Blossom") and string.sub(name, 1, 7) == "BS_Tree" then
        canopies[part] = {
            rest = part.CFrame,
            pivot = Vector3.new(0, -part.Size.Y * 0.5, 0), -- the canopy's base, where its limbs carry it
            phase = (part.Position.X * 0.13 + part.Position.Z * 0.07) % (math.pi * 2),
        }
    end
end
island.DescendantAdded:Connect(addCanopy)
for _, item in island:GetDescendants() do
    addCanopy(item)
end

-- ---------- koi ----------
local pond = nil
local fish = {}      -- { model, loop, phase, parts, rests, tails = { [i] = hinge }, s }
local loops = {}     -- [index] = { points }
local leap = nil     -- { fish, start }
local nextLeap = os.clock() + 6
local nextRipple = os.clock() + 2
local rippleTemplate = nil
local ripples = {}   -- { part, start, at, size }
local stopWater = nil
local nextChime = os.clock() + 12
local CHIME_EVERY = { 25, 50 }
local CHIME_NEAR = 110

local splashPart = carrier("KoiSplash", Vector3.new(1, 0.2, 1))
local splash = Instance.new("ParticleEmitter")
splash.Texture = SPLASH_TEXTURE
splash.Color = ColorSequence.new(Color3.fromRGB(235, 250, 255))
splash.LightInfluence = 0.6
splash.LightEmission = 0.3
splash.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.18), NumberSequenceKeypoint.new(1, 0.06) })
splash.Transparency = NumberSequence.new(0.15, 1)
splash.Lifetime = NumberRange.new(0.5, 0.8)
splash.Speed = NumberRange.new(5, 9)
splash.SpreadAngle = Vector2.new(35, 35)
splash.EmissionDirection = Enum.NormalId.Top
splash.Acceleration = Vector3.new(0, -40, 0)
splash.Rate = 0
splash.Parent = splashPart

local function catmull(p0, p1, p2, p3, t)
    local t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (3 * p1 - p0 - 3 * p2 + p3) * t3)
end

local function loopPoint(points, u)
    local n = #points
    local f = (u % 1) * n
    local i = math.floor(f)
    local t = f - i
    local function at(k)
        return points[(k % n) + 1]
    end
    return catmull(at(i - 1), at(i), at(i + 1), at(i + 2), t)
end

local function loadPond()
    pond = island:FindFirstChild("Pond")
    if not pond then
        return false
    end
    table.clear(loops)
    local loopFolder = pond:FindFirstChild("Loops")
    for _, config in loopFolder and loopFolder:GetChildren() or {} do
        local index = tonumber(string.match(config.Name, "%d+"))
        local points = {}
        for k = 1, config:GetAttribute("Count") or 0 do
            points[k] = config:GetAttribute("P" .. k)
        end
        local length = 0
        for k = 1, #points do
            length += (points[k % #points + 1] - points[k]).Magnitude
        end
        loops[index] = { points = points, length = length }
    end
    table.clear(fish)
    local koi = pond:FindFirstChild("Koi")
    for _, model in koi and koi:GetChildren() or {} do
        local entry = { model = model, loop = model:GetAttribute("Loop"), phase = model:GetAttribute("Phase") or 0, parts = {}, rests = {}, hinges = {} }
        for _, part in model:GetDescendants() do
            if part:IsA("BasePart") and part:GetAttribute("Rest") then
                table.insert(entry.parts, part)
                table.insert(entry.rests, part:GetAttribute("Rest"))
                entry.hinges[#entry.parts] = part:GetAttribute("Hinge")
            end
        end
        if loops[entry.loop] and #entry.parts > 0 then
            entry.speed = KOI_SPEED * (0.85 + 0.3 * ((entry.phase * 7.3) % 1))
            table.insert(fish, entry)
        end
    end
    rippleTemplate = pond:FindFirstChild("RippleTemplate")
    return #fish > 0
end

local function ripple(at, size)
    if not rippleTemplate or #ripples >= 8 then
        return
    end
    local ring = rippleTemplate:Clone()
    ring.Name = "Ripple"
    ring.Transparency = 0.45
    ring.Parent = pond
    table.insert(ripples, { part = ring, start = os.clock(), at = at, size = size, base = rippleTemplate.Size })
end

local function doSplash(at, count)
    splashPart.CFrame = CFrame.new(at)
    splashPart.Parent = Workspace.CurrentCamera
    splash:Emit(count)
    ripple(at, 3.2)
    Sfx.play("KoiSplash", at)
end

local koiParts, koiFrames = {}, {} -- (reused each frame)
local function swimKoi(now, water)
    local parts, frames = koiParts, koiFrames
    table.clear(parts)
    table.clear(frames)
    for _, entry in fish do
        local loop = loops[entry.loop]
        local u = (now * entry.speed / loop.length + entry.phase) % 1
        local pos = loopPoint(loop.points, u)
        local ahead = loopPoint(loop.points, u + 0.004)
        local dir = (ahead - pos)
        dir = if dir.Magnitude > 1e-3 then dir.Unit else Vector3.zAxis
        pos += Vector3.new(0, math.sin(now * 0.7 + entry.phase * 9) * 0.25, 0)
        local pitch = 0
        if leap and leap.fish == entry then
            local s = (now - leap.start) / LEAP_TIME
            if s >= 1 then
                doSplash(Vector3.new(pos.X, water, pos.Z) + dir * 1.2, 10)
                leap = nil
            else
                pos = Vector3.new(pos.X, water - 1 + (LEAP_HEIGHT + 1) * 4 * s * (1 - s), pos.Z)
                pitch = (0.5 - s) * 1.8
            end
        end
        -- +Z is the fish's nose: look along -dir so +Z points the way it swims
        local frame = CFrame.lookAt(pos, pos - dir) * CFrame.Angles(-pitch, math.sin(now * 5 + entry.phase * 11) * 0.07, 0)
        local swing = math.sin(now * 7 + entry.phase * 13) * 0.45
        for i, part in entry.parts do
            local rest = entry.rests[i]
            local hinge = entry.hinges[i]
            local cf = if hinge then frame * CFrame.new(hinge) * CFrame.Angles(0, swing, 0) * CFrame.new(-hinge) * rest else frame * rest
            table.insert(parts, part)
            table.insert(frames, cf)
        end
        entry.at = pos
    end
    if #parts > 0 then
        Workspace:BulkMoveTo(parts, frames, Enum.BulkMoveMode.FireCFrameChanged)
    end
    if not leap and now > nextLeap and #fish > 0 then
        local entry = fish[math.random(#fish)]
        leap = { fish = entry, start = now }
        nextLeap = now + LEAP_EVERY[1] + math.random() * (LEAP_EVERY[2] - LEAP_EVERY[1])
        if entry.at then
            doSplash(Vector3.new(entry.at.X, water, entry.at.Z), 6)
        end
    end
    if now > nextRipple and #fish > 0 then
        nextRipple = now + RIPPLE_EVERY[1] + math.random() * (RIPPLE_EVERY[2] - RIPPLE_EVERY[1])
        local entry = fish[math.random(#fish)]
        if entry.at then
            ripple(Vector3.new(entry.at.X, water, entry.at.Z), 2.4 + math.random() * 1.6)
        end
    end
end

local function growRipples(now, water)
    for i = #ripples, 1, -1 do
        local r = ripples[i]
        local s = (now - r.start) / RIPPLE_TIME
        if s >= 1 or not r.part.Parent then
            r.part:Destroy()
            table.remove(ripples, i)
        else
            local k = 1 - (1 - s) ^ 2
            local scale = 0.25 + r.size * k
            r.part.Size = Vector3.new(r.base.X * scale, r.base.Y, r.base.Z * scale)
            r.part.CFrame = CFrame.new(r.at.X, water + 0.04, r.at.Z)
            r.part.Transparency = 0.45 + 0.55 * s
        end
    end
end

-- ---------- each frame ----------
local swayTick = 0
local pondTriedAt = -math.huge
local swayParts, swayFrames = {}, {} -- (reused each sway)
RunService.Heartbeat:Connect(function(dt)
    local camera = Workspace.CurrentCamera
    if not camera then
        return
    end
    local now = os.clock()
    local camPos = camera.CFrame.Position
    local centre = island:GetAttribute("Centre")
    local reach = island:GetAttribute("Reach") or 335
    local near = centre ~= nil and (Vector3.new(camPos.X, centre.Y, camPos.Z) - centre).Magnitude < reach + 40
    local dir, g = wind(now, dt)

    -- petals
    local rain = raining()
    local rate = 0
    if near then
        rate = if reduced() then PETAL_REDUCED else PETAL_RATE
        rate *= (if rain then 0.35 else 1) * (1 + g * 1.2)
    end
    cameraEmitter.Rate = rate
    if rate > 0 then
        if not carriedAt or (camPos - carriedAt).Magnitude > 4 then
            carriedAt = camPos
            cameraPetals.CFrame = CFrame.new(camPos + Vector3.new(0, 6, 0) - dir * 14)
            cameraPetals.Parent = camera
        end
    end
    local push = dir * (2.2 + g * 4.5)
    cameraEmitter.Acceleration = Vector3.new(push.X, -1.6, push.Z)
    treeEmitter.Acceleration = cameraEmitter.Acceleration
    local elder = near and findElder()
    if elder and (elder.Position - camPos).Magnitude < 160 then
        treePetals.CFrame = CFrame.new(elder.Position - Vector3.new(0, elder.Size.Y * 0.35, 0))
        treePetals.Parent = camera
        treeEmitter.Rate = rate * 0.35
    else
        treeEmitter.Rate = 0
    end

    -- the pond (loaded again if it streamed in before its fish: a second's wait between tries)
    if near and (not pond or not pond.Parent or #fish == 0) and now - pondTriedAt > 1 then
        pondTriedAt = now
        loadPond()
    end
    local water = pond and pond.Parent and pond:GetAttribute("Water")
    local pondCentre = pond and pond.Parent and pond.PrimaryPart
    local pondNear = water and pondCentre and (pondCentre.Position - camPos).Magnitude < KOI_NEAR
    if pondNear then
        swimKoi(now, water)
        growRipples(now, water)
        if not stopWater then
            stopWater = Sfx.loop("PondWater", pondCentre)
        end
    elseif stopWater then
        stopWater()
        stopWater = nil
    end

    -- the shrine's chimes, now and then, from the hall (its first part, once streamed in)
    if near and now > nextChime then
        nextChime = now + CHIME_EVERY[1] + math.random() * (CHIME_EVERY[2] - CHIME_EVERY[1])
        local kit = island:FindFirstChild("Kit")
        local hall = kit and kit:FindFirstChild("BS_ShrineHall_1")
        if hall and (hall.Position - camPos).Magnitude < CHIME_NEAR then
            Sfx.play("ShrineChime", hall)
        end
    end

    -- the canopies (about 20 times a second)
    swayTick += dt
    if near and swayTick >= 0.05 and not Quality.Low and not reduced() then
        swayTick = 0
        local parts, frames = swayParts, swayFrames
        table.clear(parts)
        table.clear(frames)
        local axis = Vector3.new(dir.Z, 0, -dir.X)
        for part, c in canopies do
            if part.Parent and (part.Position - camPos).Magnitude < SWAY_NEAR then
                local angle = SWAY_ANGLE * (math.sin(now * 0.9 + c.phase) * 0.6 + g * 0.8 + math.sin(now * 2.3 + c.phase * 2) * 0.15)
                local pivot = c.rest * c.pivot
                local turn = CFrame.fromAxisAngle(axis, angle)
                table.insert(parts, part)
                table.insert(frames, CFrame.new(pivot) * turn * CFrame.new(-pivot) * c.rest)
            end
        end
        if #parts > 0 then
            Workspace:BulkMoveTo(parts, frames, Enum.BulkMoveMode.FireCFrameChanged)
        end
    end
end)

-- a part that streamed out and back is a new instance at rest; a canopy that left is forgotten
island.DescendantRemoving:Connect(function(item)
    canopies[item] = nil
end)
