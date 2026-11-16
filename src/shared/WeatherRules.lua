-- The time maths of the day and night cycle and the weather (WeatherConfig), shared so the server and every client agree:
-- both come from the server's clock alone.
--
--   WeatherRules.now()             the server's clock (workspace:GetServerTimeNow()), plus a Studio test's shift
--   WeatherRules.clockAt(t)        the ClockTime (0..24) at t, and the phase's name ("Day", "Dusk", "Night", "Dawn")
--   WeatherRules.nightAt(clock)    how much night a ClockTime is (0 by day, 1 in the night, a ramp through dusk and dawn)
--   WeatherRules.spellAt(t)        which weather spell t falls in (its number) and that spell's weather
--   WeatherRules.weatherAt(t)      the weather blending out, the one blending in, and how far in (0..1); the two are the
--                                  same once a change is done
--   WeatherRules.current()         the clock, phase and weather now, with a Studio test's forced time or weather
--   WeatherRules.schedule(t, n)    the next n spells from t: { { Start, Weather } } (for testing and tuning)
--
-- Studio only (RunService:IsStudio()), set on ReplicatedStorage from a Server execute_luau or the command bar, and cleared
-- after the test (WeatherService clears them in a live server):
--   WeatherForce  a weather's name: it blends in over ForcedBlend and stays
--   ClockForce    a ClockTime (0..24): the time stands still there
--   WeatherShift  seconds added to the clock: jump the cycle and the weather ahead to see what's coming
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local WeatherConfig = require(ReplicatedStorage:WaitForChild("WeatherConfig"))

local WeatherRules = {}

local DAY = WeatherConfig.Day
local WEATHER = WeatherConfig.Weather
local SEED_STEP = 7919 -- odd (a prime): a spell's number times this seeds its pick
local STUDIO = RunService:IsStudio()

local cycleLength = 0
for _, segment in DAY.Segments do
    assert(segment.Seconds > 0 and segment.To > segment.From, "WeatherConfig.Day: each segment needs Seconds and From < To")
    cycleLength += segment.Seconds
end
WeatherRules.CycleLength = cycleLength

local totalWeight = 0
for _, name in WEATHER.Order do
    local state = WeatherConfig.States[name]
    assert(state and state.Weight and state.Weight >= 0, "WeatherConfig.States." .. name .. " needs a Weight")
    totalWeight += state.Weight
end
assert(WEATHER.Transition < WEATHER.Spell, "WeatherConfig.Weather.Transition must be shorter than Spell")

function WeatherRules.now()
    local shift = if STUDIO then ReplicatedStorage:GetAttribute("WeatherShift") else nil
    return Workspace:GetServerTimeNow() + DAY.Offset + (if type(shift) == "number" then shift else 0)
end

function WeatherRules.clockAt(t)
    local into = t % cycleLength
    for _, segment in DAY.Segments do
        if into < segment.Seconds then
            local clock = segment.From + (segment.To - segment.From) * (into / segment.Seconds)
            return clock % 24, segment.Name
        end
        into -= segment.Seconds
    end
    local last = DAY.Segments[#DAY.Segments]
    return last.To % 24, last.Name
end

local function smoothstep(a, b, x)
    local k = math.clamp((x - a) / (b - a), 0, 1)
    return k * k * (3 - 2 * k)
end
WeatherRules.smoothstep = smoothstep

-- the sun sets about 18.0 and rises about 6.0 (latitude 0): full night from 19.2 to 4.8
function WeatherRules.nightAt(clock)
    if clock >= 12 then
        return smoothstep(17.6, 19.2, clock)
    end
    return 1 - smoothstep(4.8, 6.4, clock)
end

-- a spell's own draw: by Weight, leaving out what can't come in the night if it runs into one, and (on a redraw) the
-- weathers that may not follow themselves
local function draw(index, onlyRepeatable)
    -- does this spell run into the night?
    local nightly = false
    for step = 0, 4 do
        local clock = WeatherRules.clockAt(index * WEATHER.Spell + WEATHER.Spell * step / 4)
        if WeatherRules.nightAt(clock) > WEATHER.NightFor then
            nightly = true
        end
    end
    local function allowed(state)
        return not (nightly and state.NotAtNight) and not (onlyRepeatable and state.Repeat == false)
    end
    local weight = 0
    for _, name in WEATHER.Order do
        if allowed(WeatherConfig.States[name]) then
            weight += WeatherConfig.States[name].Weight
        end
    end
    local random = Random.new(index * SEED_STEP + WEATHER.Seed + (if onlyRepeatable then 1 else 0))
    local roll = random:NextNumber() * weight
    for _, name in WEATHER.Order do
        local state = WeatherConfig.States[name]
        if allowed(state) then
            roll -= state.Weight
            if roll < 0 then
                return name
            end
        end
    end
    return WEATHER.Order[1]
end

-- A weather marked Repeat = false (rain, fog, the Qi Bloom) never lasts two spells running: when a spell draws the same one as
-- the spell before drew, it draws again from the others. (Only a first draw can give one of them, so two never touch.)
function WeatherRules.spellAt(t)
    local index = math.floor(t / WEATHER.Spell)
    local name = draw(index, false)
    if WeatherConfig.States[name].Repeat == false and draw(index - 1, false) == name then
        name = draw(index, true)
    end
    return index, name
end

function WeatherRules.weatherAt(t)
    local index, name = WeatherRules.spellAt(t)
    local into = t - index * WEATHER.Spell
    if into >= WEATHER.Transition then
        return name, name, 1
    end
    local _, before = WeatherRules.spellAt((index - 1) * WEATHER.Spell)
    if before == name then
        return name, name, 1
    end
    return before, name, smoothstep(0, 1, into / WEATHER.Transition)
end

-- the forced weather and clock of a Studio test (nil when none, and always nil in a live game)
function WeatherRules.forced()
    if not STUDIO then
        return nil, nil
    end
    local weather = ReplicatedStorage:GetAttribute("WeatherForce")
    local clock = ReplicatedStorage:GetAttribute("ClockForce")
    weather = if type(weather) == "string" and WeatherConfig.States[weather] then weather else nil
    clock = if type(clock) == "number" then clock % 24 else nil
    return weather, clock
end

local function phaseOf(clock)
    if clock >= 19 or clock < 5 then
        return "Night"
    elseif clock < 7 then
        return "Dawn"
    elseif clock < 16.5 then
        return "Day"
    end
    return "Dusk"
end
WeatherRules.phaseOf = phaseOf

-- the clock, its phase, then the weather out, the weather in and how far in
function WeatherRules.current()
    local t = WeatherRules.now()
    local forcedWeather, forcedClock = WeatherRules.forced()
    local clock, phase = WeatherRules.clockAt(t)
    if forcedClock then
        clock, phase = forcedClock, phaseOf(forcedClock)
    end
    if forcedWeather then
        return clock, phase, forcedWeather, forcedWeather, 1
    end
    local from, to, k = WeatherRules.weatherAt(t)
    return clock, phase, from, to, k
end

function WeatherRules.schedule(t, count)
    local list = {}
    local index = math.floor(t / WEATHER.Spell)
    for i = 0, count - 1 do
        local start = (index + i) * WEATHER.Spell
        local _, name = WeatherRules.spellAt(start)
        table.insert(list, { Start = start, Weather = name })
    end
    return list
end

return WeatherRules
