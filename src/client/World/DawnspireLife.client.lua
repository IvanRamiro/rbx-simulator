-- Dawnspire Hall's air (the owner's polish list, 2026-11-23): blossom petals drifting through the Orthodox territory's gardens and terraces, drawn by each client and cheap.
-- Not the Blossom Sanctuary's pink petals (SanctuaryLife): these are near-white with a faint blush, fall slower and drift in wide, slow gusts. One emitter that rides with
-- the camera while it is inside the territory's reach (DawnspireBuilder writes the territory's "Centre" and "Radius" attributes); nothing at all outside it.
--   * Reduced Effects (the player's setting): a trickle; a phone (Quality.Low): fewer; rain: fewer; lit by the scene (LightInfluence 1), so they darken with the night.
--   * Nothing here touches Lighting or the weather's own effects (WeatherController owns those); it only reads the weather.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local WeatherRules = require(ReplicatedStorage:WaitForChild("WeatherRules"))
local Quality = require(script.Parent.Parent:WaitForChild("Performance"):WaitForChild("Quality"))

local player = Players.LocalPlayer

local PETAL_RATE = if Quality.Low then 6 else 14
local PETAL_REDUCED = 2
local PETAL_TEXTURE = "rbxasset://textures/particles/smoke_main.dds" -- (a soft puff, squashed and tumbling reads as a petal: as the Sanctuary's)
local REACH_MARGIN = 30 -- studs past the territory's Radius where the petals still come

local function reduced()
    return player:GetAttribute("SettingReducedEffects") == true
end

local function raining()
    local _, _, from, to, k = WeatherRules.current()
    return (if k >= 0.5 then to else from) == "Rain"
end

-- the territory: found once it has streamed in, and again if it streams out and back (a new instance each time)
local pad = Workspace:WaitForChild("FloatingIslands"):WaitForChild("MurimCrossing"):WaitForChild("OrthodoxPad")
local territory
local function findTerritory()
    if territory and territory.Parent then
        return territory
    end
    territory = pad:FindFirstChild("Territory")
    return territory
end

local function petals(parent)
    local e = Instance.new("ParticleEmitter")
    e.Name = "DawnspirePetals"
    e.Texture = PETAL_TEXTURE
    e.Color = ColorSequence.new(Color3.fromRGB(255, 251, 252), Color3.fromRGB(250, 224, 234))
    e.LightEmission = 0.1
    e.LightInfluence = 1
    e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.24), NumberSequenceKeypoint.new(1, 0.18) })
    e.Squash = NumberSequence.new({ NumberSequenceKeypoint.new(0, -0.7), NumberSequenceKeypoint.new(0.15, 0.7), NumberSequenceKeypoint.new(0.3, -0.6),
        NumberSequenceKeypoint.new(0.45, 0.7), NumberSequenceKeypoint.new(0.6, -0.7), NumberSequenceKeypoint.new(0.8, 0.6), NumberSequenceKeypoint.new(1, -0.5) })
    e.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.12, 0.08), NumberSequenceKeypoint.new(0.85, 0.12), NumberSequenceKeypoint.new(1, 1) })
    e.Lifetime = NumberRange.new(8, 12)
    e.Speed = NumberRange.new(0.3, 1)
    e.SpreadAngle = Vector2.new(180, 180)
    e.Rotation = NumberRange.new(0, 360)
    e.RotSpeed = NumberRange.new(-90, 90)
    e.Drag = 1
    e.Acceleration = Vector3.new(0, -1, 0)
    e.Shape = Enum.ParticleEmitterShape.Box
    e.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
    e.Rate = 0
    e.Parent = parent
    return e
end

local carrier = Instance.new("Part")
carrier.Name = "DawnspirePetals"
carrier.Size = Vector3.new(60, 16, 60)
carrier.Transparency = 1
carrier.Anchored = true
carrier.CanCollide = false
carrier.CanQuery = false
carrier.CanTouch = false
carrier.CastShadow = false
local emitter = petals(carrier)
local carriedAt = nil

local windAngle, gust, gustUntil, nextGust = math.random() * math.pi * 2, 0, 0, os.clock() + 10
RunService.Heartbeat:Connect(function(dt)
    local camera = Workspace.CurrentCamera
    if not camera then
        return
    end
    local now = os.clock()
    local camPos = camera.CFrame.Position
    local area = findTerritory()
    local centre = area and area:GetAttribute("Centre")
    local radius = area and area:GetAttribute("Radius") or 150
    local near = centre ~= nil and (Vector3.new(camPos.X, centre.Y, camPos.Z) - centre).Magnitude < radius + REACH_MARGIN

    windAngle += math.noise(now * 0.04, 8.3) * dt * 0.5
    if now > nextGust then
        gustUntil = now + 3 + math.random() * 3
        nextGust = now + 12 + math.random() * 12
    end
    gust += ((if now < gustUntil then 1 else 0) - gust) * math.min(1, dt * 1.2)
    local dir = Vector3.new(math.cos(windAngle), 0, math.sin(windAngle))

    local rate = 0
    if near then
        rate = if reduced() then PETAL_REDUCED else PETAL_RATE
        rate *= (if raining() then 0.4 else 1) * (1 + gust)
    end
    emitter.Rate = rate
    if rate > 0 then
        if not carriedAt or (camPos - carriedAt).Magnitude > 4 then
            carriedAt = camPos
            carrier.CFrame = CFrame.new(camPos + Vector3.new(0, 5, 0) - dir * 12)
            carrier.Parent = camera
        end
        local push = dir * (1.4 + gust * 3.5)
        emitter.Acceleration = Vector3.new(push.X, -1, push.Z)
    end
end)
