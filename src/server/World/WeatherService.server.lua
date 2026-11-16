-- The day and night cycle and the weather, from the server (WeatherConfig, WeatherRules). The clock and the weather follow
-- the server's time alone, so every client works them out for itself (WeatherController draws them, smoothly); this script
-- sets the starting Lighting every client joins with (the noon look), and publishes what it is now on ReplicatedStorage
-- for anything in the game that asks:
--   Weather    the weather now: "Clear", "Cloudy", "Rain", "Fog" or "QiBloom" (the one blending in, once it's under way)
--   DayPhase   "Day", "Dusk", "Night" or "Dawn"
-- A Studio test forces a weather or a time with ReplicatedStorage's WeatherForce, ClockForce and WeatherShift attributes
-- (WeatherRules); in a live server they are cleared at the start, so a place saved with one left on can't keep it.
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local WeatherConfig = require(ReplicatedStorage:WaitForChild("WeatherConfig"))
local WeatherRules = require(ReplicatedStorage:WaitForChild("WeatherRules"))

local PUBLISH_EVERY = 1 -- seconds

if not RunService:IsStudio() then
    for _, name in { "WeatherForce", "ClockForce", "WeatherShift" } do
        ReplicatedStorage:SetAttribute(name, nil)
    end
end

-- the look every client starts from, before its WeatherController takes over (and if it never does)
local noon = WeatherConfig.Noon
Lighting.ClockTime = 14.5
Lighting.Brightness = noon.Brightness
Lighting.Ambient = noon.Ambient
Lighting.OutdoorAmbient = noon.OutdoorAmbient
local atmosphere = Lighting:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere")
atmosphere.Density = noon.AtmoDensity
atmosphere.Offset = noon.AtmoOffset
atmosphere.Color = noon.AtmoColor
atmosphere.Decay = noon.AtmoDecay
atmosphere.Glare = noon.AtmoGlare
atmosphere.Haze = noon.AtmoHaze
atmosphere.Parent = Lighting

while true do
    local _, phase, from, to, k = WeatherRules.current()
    local weather = if k >= 0.5 then to else from
    if ReplicatedStorage:GetAttribute("Weather") ~= weather then
        ReplicatedStorage:SetAttribute("Weather", weather)
    end
    if ReplicatedStorage:GetAttribute("DayPhase") ~= phase then
        ReplicatedStorage:SetAttribute("DayPhase", phase)
    end
    task.wait(PUBLISH_EVERY)
end
