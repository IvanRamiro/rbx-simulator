-- Draws the day and night cycle and the weather on this client (WeatherConfig's presets, WeatherRules' clock): Lighting's
-- ClockTime, light and ambients, the Atmosphere, the Terrain clouds, a grade of its own, the islands' lamps (brighter at
-- night and in rain), and the rain and the Qi motes round the camera.
--
-- What it owns, all made here at runtime (nothing is saved in the place):
--   Lighting.WeatherGrade      a ColorCorrectionEffect of its own. The hatch, the tribulation and the pets' specials grade
--                              the screen with their own effects and remove them, so nothing has to be put back
--   Terrain.Clouds             made if the place has none
--   Camera.WeatherRain/Motes   two invisible parts carrying one emitter each, moved with the camera
-- It also writes Lighting's ClockTime, Brightness, Ambient, OutdoorAmbient and ExposureCompensation and the Atmosphere,
-- which nothing else in the game changes. The place's AuraBloom and AuraColorCorrection are left alone.
--
-- Cost: one Heartbeat. The look is worked out 5 times a second; the rain's area moves only when the camera has moved 4 studs;
-- a roof check (one ray up) twice a second while it rains. Rain: up to 520 drops a second on a PC (about 430 alive at once),
-- 180 on a phone, 60 with Reduced Effects; none under a roof. Qi motes: 40 a second (16 on a phone, 6 with Reduced Effects).
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local WeatherConfig = require(ReplicatedStorage:WaitForChild("WeatherConfig"))
local WeatherRules = require(ReplicatedStorage:WaitForChild("WeatherRules"))
local Quality = require(script.Parent.Parent:WaitForChild("Performance"):WaitForChild("Quality"))

local player = Players.LocalPlayer
local STATES = WeatherConfig.States
local ORDER = WeatherConfig.Weather.Order
local NEUTRAL = WeatherConfig.Neutral
local TIMES = WeatherConfig.Times
local RAIN = WeatherConfig.Rain
local MOTES = WeatherConfig.Motes

-- a Qi Bloom tells everyone when it begins: cultivating gathers more Qi while it lasts (QiService adds it)
do
    local Toast = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("Toast"))
    local bloomNotice = Toast.new("QiBloomNotice", Color3.fromRGB(120, 255, 214), 6)
    local last = ReplicatedStorage:GetAttribute("Weather")
    ReplicatedStorage:GetAttributeChangedSignal("Weather"):Connect(function()
        local now = ReplicatedStorage:GetAttribute("Weather")
        if now == "QiBloom" and last ~= "QiBloom" then
            bloomNotice:show("A Qi Bloom! Cultivate now for +" .. STATES.QiBloom.QiBonusPercent .. "% Qi.", "Reward")
        end
        last = now
    end)
end

local LOOK_EVERY = 0.2   -- seconds between working out the look
local COVER_EVERY = 0.5  -- seconds between roof checks while it rains
local FOLLOW_STEP = 4    -- studs the camera moves before the rain's area follows
local RAIN_TEXTURE = "rbxasset://textures/particles/SquareParticle.png" -- Roblox's own plain square, squashed into a streak
local MOTE_TEXTURE = "rbxassetid://135169457468310" -- the game's soft glow (the auras, the hatch)

local function reduced()
    return player:GetAttribute("SettingReducedEffects") == true
end

-- ---------- what it draws with ----------
local atmosphere = Lighting:FindFirstChildOfClass("Atmosphere")
if not atmosphere then
    atmosphere = Instance.new("Atmosphere")
    atmosphere.Parent = Lighting
end

local grade = Instance.new("ColorCorrectionEffect")
grade.Name = "WeatherGrade"
grade.Parent = Lighting

local terrain = Workspace:WaitForChild("Terrain")
local clouds = terrain:FindFirstChildOfClass("Clouds")
if not clouds then
    clouds = Instance.new("Clouds")
    clouds.Parent = terrain
end

local function carrier(name, size)
    local part = Instance.new("Part")
    part.Name = name
    part.Anchored = true
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.CastShadow = false
    part.Transparency = 1
    part.Size = size
    return part
end

local rainPart = carrier("WeatherRain", Vector3.new(RAIN.Area, 1, RAIN.Area))
local rain = Instance.new("ParticleEmitter")
rain.Name = "Rain"
rain.Texture = RAIN_TEXTURE
-- upright in the world, turned to face the camera, squashed tall and thin (a streak texture with VelocityParallel lay on its side)
rain.Orientation = Enum.ParticleOrientation.FacingCameraWorldUp
rain.Squash = NumberSequence.new(3)
rain.EmissionDirection = Enum.NormalId.Bottom
rain.Shape = Enum.ParticleEmitterShape.Box
rain.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
rain.Speed = NumberRange.new(RAIN.Speed * 0.9, RAIN.Speed * 1.1)
rain.SpreadAngle = Vector2.new(4, 4)
rain.Acceleration = Vector3.new(0, 0, 0)
rain.Lifetime = NumberRange.new(0.75, 0.9)
local DROP = if Quality.Low then 0.42 else 0.32 -- a little thicker on a phone's small screen, where fewer fall
rain.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, DROP, 0.06), NumberSequenceKeypoint.new(1, DROP, 0.06) })
rain.Transparency = NumberSequence.new({
    NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.08, 0.5), NumberSequenceKeypoint.new(0.85, 0.55),
    NumberSequenceKeypoint.new(1, 1),
})
rain.Color = ColorSequence.new(RAIN.Color)
rain.LightEmission = 0.1
rain.LightInfluence = 0.6
rain.Brightness = 1
rain.Rate = 0
rain.Enabled = true
rain.Parent = rainPart

local motesPart = carrier("WeatherMotes", Vector3.new(MOTES.Area, MOTES.Height, MOTES.Area))
local motes = Instance.new("ParticleEmitter")
motes.Name = "QiMotes"
motes.Texture = MOTE_TEXTURE
motes.Shape = Enum.ParticleEmitterShape.Box
motes.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
motes.EmissionDirection = Enum.NormalId.Top
motes.Speed = NumberRange.new(0.4, 1.4)
motes.SpreadAngle = Vector2.new(40, 40)
motes.Acceleration = Vector3.new(0, 0.35, 0)
motes.Drag = 0.4
motes.Lifetime = NumberRange.new(5, 8)
motes.Size = NumberSequence.new({
    NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.2, 0.5, 0.12), NumberSequenceKeypoint.new(0.8, 0.4, 0.1),
    NumberSequenceKeypoint.new(1, 0),
})
motes.Transparency = NumberSequence.new({
    NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.2, 0.25), NumberSequenceKeypoint.new(0.8, 0.35),
    NumberSequenceKeypoint.new(1, 1),
})
-- jade turning gold as each one rises
motes.Color = ColorSequence.new({
    ColorSequenceKeypoint.new(0, MOTES.Colors[1]), ColorSequenceKeypoint.new(0.45, MOTES.Colors[2]),
    ColorSequenceKeypoint.new(1, MOTES.Colors[2]),
})
motes.LightEmission = 1
motes.LightInfluence = 0
motes.Brightness = 1.6
motes.RotSpeed = NumberRange.new(-20, 20)
motes.Rate = 0
motes.Parent = motesPart

local function placeCarriers(camera)
    rainPart.Parent = camera
    motesPart.Parent = camera
end

-- ---------- the islands' lamps ----------
-- the PointLights of the islands' kit pieces (the crystal lamps, lanterns, braziers): brighter after dark and in rain.
-- Eggs, relics, the shops' effects and the rest are other scripts' and are left alone. Streaming brings lamps in and out.
local lamps = setmetatable({}, { __mode = "k" }) -- [light] = its built brightness
local lampShare = 1

local function isLamp(item)
    return item:IsA("Light") and item.Parent ~= nil and item.Parent.Parent ~= nil and item.Parent.Parent.Name == "Kit"
end

local function addLamp(item)
    if isLamp(item) and not lamps[item] then
        lamps[item] = item.Brightness
        item.Brightness = lamps[item] * lampShare
    end
end

task.spawn(function()
    local world = Workspace:WaitForChild("FloatingIslands")
    world.DescendantAdded:Connect(addLamp)
    for _, item in world:GetDescendants() do
        addLamp(item)
    end
end)

local function setLamps(share)
    if math.abs(share - lampShare) < 0.03 then
        return
    end
    lampShare = share
    for light, built in lamps do
        if light.Parent then
            light.Brightness = built * share
        end
    end
end

-- ---------- the look ----------
local function lerp(a, b, k)
    return a + (b - a) * k
end

local function toGrey(colour, amount)
    if amount <= 0 then
        return colour
    end
    local y = colour.R * 0.3 + colour.G * 0.55 + colour.B * 0.15
    return Color3.new(lerp(colour.R, y, amount), lerp(colour.G, y, amount), lerp(colour.B, y, amount))
end

local function scaled(colour, by)
    return Color3.new(math.min(colour.R * by, 1), math.min(colour.G * by, 1), math.min(colour.B * by, 1))
end

-- the time of day's look at a ClockTime, blended into `out`
local timeOfDay = {}
local function lookAt(clock, out)
    local before, after = TIMES[1], TIMES[#TIMES]
    for i = 1, #TIMES - 1 do
        if clock >= TIMES[i].Clock and clock <= TIMES[i + 1].Clock then
            before, after = TIMES[i], TIMES[i + 1]
            break
        end
    end
    local span = after.Clock - before.Clock
    local k = if span > 0 then (clock - before.Clock) / span else 0
    for key, a in before.Look do
        local b = after.Look[key]
        out[key] = if typeof(a) == "Color3" then a:Lerp(b, k) else lerp(a, b, k)
    end
    return out
end

-- the weathers' share of the screen now, eased toward what WeatherRules says (so a Studio test's change blends too)
local mix = {}
for _, name in ORDER do
    mix[name] = 0
end
local target = {}
local weather = {} -- the blended weather parameters (WeatherConfig.Neutral's fields)
local started = false

local function blendWeather(dt, from, to, k)
    for _, name in ORDER do
        target[name] = 0
    end
    target[from] += 1 - k
    target[to] += k
    local step = dt / WeatherConfig.Weather.ForcedBlend
    local total = 0
    for _, name in ORDER do
        mix[name] = if started then mix[name] + math.clamp(target[name] - mix[name], -step, step) else target[name]
        total += mix[name]
    end
    started = true
    -- the weighted parameters (Tint by its channels)
    local r, g, b = 0, 0, 0
    for key, neutral in NEUTRAL do
        if typeof(neutral) ~= "Color3" then
            weather[key] = 0
        end
    end
    for _, name in ORDER do
        local w = mix[name] / total
        if w > 0 then
            local state = STATES[name]
            for key, neutral in NEUTRAL do
                if typeof(neutral) == "Color3" then
                    local c = state[key] or neutral
                    r, g, b = r + c.R * w, g + c.G * w, b + c.B * w
                else
                    weather[key] += (state[key] or neutral) * w
                end
            end
        end
    end
    weather.Tint = Color3.new(r, g, b)
end

local rainShare, motesShare, night = 0, 0, 0
local function applyLook(dt)
    local clock, _, from, to, k = WeatherRules.current()
    blendWeather(dt, from, to, k)
    local t = lookAt(clock, timeOfDay)
    local w = weather
    night = WeatherRules.nightAt(clock)

    Lighting.ClockTime = clock
    Lighting.Brightness = t.Brightness * w.Light
    Lighting.Ambient = scaled(toGrey(t.Ambient, w.Grey * 0.6), w.Ambient)
    Lighting.OutdoorAmbient = scaled(toGrey(t.OutdoorAmbient, w.Grey * 0.6), w.Ambient)
    Lighting.ExposureCompensation = t.Exposure + w.Exposure

    atmosphere.Density = math.clamp(t.AtmoDensity + w.Density, 0, 1)
    atmosphere.Offset = math.clamp(t.AtmoOffset + w.Offset, 0, 1)
    atmosphere.Color = toGrey(t.AtmoColor, w.Grey)
    atmosphere.Decay = toGrey(t.AtmoDecay, w.Grey)
    atmosphere.Glare = t.AtmoGlare * w.Glare
    atmosphere.Haze = t.AtmoHaze + w.Haze

    clouds.Cover = math.clamp(w.Cover, 0, 1)
    clouds.Density = math.clamp(w.CloudDensity, 0, 1)
    clouds.Color = scaled(t.CloudColor, w.CloudShade)

    grade.TintColor = Color3.new(t.Tint.R * w.Tint.R, t.Tint.G * w.Tint.G, t.Tint.B * w.Tint.B)
    grade.Saturation = t.Saturation + w.Saturation
    grade.Contrast = t.Contrast + w.Contrast

    setLamps(t.Lamps + w.Lamps)
    -- the clouds gather first: the rain and the motes come in over the second half of a change, and go in the first
    rainShare = WeatherRules.smoothstep(0.45, 1, w.Rain)
    motesShare = WeatherRules.smoothstep(0.45, 1, w.Motes)
end

-- ---------- the rain and the motes ----------
local coverParams = RaycastParams.new()
coverParams.FilterType = Enum.RaycastFilterType.Include
coverParams.IgnoreWater = true
task.spawn(function()
    coverParams.FilterDescendantsInstances = { Workspace:WaitForChild("FloatingIslands") }
end)

local covered = false
local lastCover = 0
local followed = nil
local rainColourNight = -1

local function rates()
    if reduced() then
        return RAIN.ReducedRate, MOTES.ReducedRate
    elseif Quality.Low then
        return RAIN.PhoneRate, MOTES.PhoneRate
    end
    return RAIN.Rate, MOTES.Rate
end

local function setRate(emitter, rate)
    if math.abs(emitter.Rate - rate) > math.max(1, rate * 0.02) or (rate == 0 and emitter.Rate ~= 0) then
        emitter.Rate = rate
    end
end

local function updateParticles(camera, now)
    local at = camera.CFrame.Position
    if rainShare > 0 and now - lastCover > COVER_EVERY then
        lastCover = now
        covered = Workspace:Raycast(at, Vector3.new(0, RAIN.CoverReach, 0), coverParams) ~= nil
    end
    local rainRate, motesRate = rates()
    setRate(rain, if covered then 0 else rainRate * rainShare)
    setRate(motes, motesRate * motesShare)
    if rainShare <= 0 and motesShare <= 0 then
        return
    end
    if not followed or (at - followed).Magnitude > FOLLOW_STEP then
        followed = at
        local look = camera.CFrame.LookVector
        local ahead = Vector3.new(look.X, 0, look.Z)
        ahead = if ahead.Magnitude > 0.01 then ahead.Unit * RAIN.Ahead else Vector3.zero
        rainPart.CFrame = CFrame.new(at + ahead + Vector3.new(0, RAIN.Height, 0))
        motesPart.CFrame = CFrame.new(at + ahead * 0.5)
    end
    -- the drops darken with the night (a new ColorSequence only when it has changed enough to see)
    if math.abs(night - rainColourNight) > 0.05 then
        rainColourNight = night
        rain.Color = ColorSequence.new(RAIN.Color:Lerp(RAIN.NightColor, night))
    end
end

-- ---------- the loop ----------
local sinceLook = math.huge
RunService.Heartbeat:Connect(function(dt)
    sinceLook += dt
    if sinceLook >= LOOK_EVERY then
        applyLook(math.min(sinceLook, 1))
        sinceLook = 0
    end
    local camera = Workspace.CurrentCamera
    if camera then
        if rainPart.Parent ~= camera then
            placeCarriers(camera)
        end
        updateParticles(camera, os.clock())
    end
end)
