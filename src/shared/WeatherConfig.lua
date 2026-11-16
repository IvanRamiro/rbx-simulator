-- The day and night cycle and the weather (WeatherRules does the time maths, WeatherService publishes what it is now, and
-- each client's WeatherController draws it). Everything here is a named, hand-tuned preset, so it is tuned in one place.
--
-- The time of day and the weather come from the server's clock (workspace:GetServerTimeNow(), the same in every server and
-- on every client), the way the Wandering Merchant keeps his hours: no server sends anything for them to agree.
--
-- The day: 24 minutes of real time. A long bright day (14.5 min), a 2.5-minute golden dusk, a 5-minute moonlit night that
-- stays readable (the auras, the lamps and the Neon glows carry it), and a 2-minute dawn. Most visits see a dusk or a night.
--
-- The weather: one "spell" every 5 minutes (it doesn't divide the day, so a spell falls at a new time of day each cycle),
-- picked by Weight; a change blends over Transition seconds. Fog is never picked for a spell that runs into the night.
local WeatherConfig = {}

WeatherConfig.Day = {
    -- in order, real seconds each and the ClockTime each runs from and to (past 24 wraps round midnight)
    Segments = {
        { Name = "Day", Seconds = 870, From = 7, To = 16.5 },
        -- the golden hour gets the most of the dusk: Roblox's sky turns from blue to starry between about 17.6 and 18.0
        { Name = "Dusk", Seconds = 110, From = 16.5, To = 17.9 },
        { Name = "Dusk", Seconds = 40, From = 17.9, To = 19 },
        { Name = "Night", Seconds = 300, From = 19, To = 29 },
        { Name = "Dawn", Seconds = 120, From = 29, To = 31 },
    },
    Offset = 0, -- seconds added to the server's clock (moves where the cycle stands at a given moment)
}

WeatherConfig.Weather = {
    Spell = 300,       -- seconds each weather lasts before the next is picked (the same one may come again)
    Transition = 40,   -- seconds a change blends over (clouds first, then the rain or the fog)
    ForcedBlend = 20,  -- seconds a Studio test change blends over
    Seed = 4111,       -- a spell's number times SEED_STEP plus this seeds its pick
    NightFor = 0.5,    -- a spell "runs into the night" where the night is more than this (WeatherRules.nightAt)
    Order = { "Clear", "Cloudy", "Rain", "Fog", "QiBloom" },
}

-- Each weather: its odds (Weight), whether it may last two spells running (Repeat = false: never; 5 minutes of rain or fog
-- at a time is plenty), whether it may come in the night (NotAtNight), and how it changes the time of day's look. A field left out keeps its Neutral value.
--   Light, Ambient    the sun's (or moon's) Brightness and both ambients, as a share of the time of day's
--   Grey              how far the ambients and the haze's colour turn grey (0..1)
--   Density, Haze, Offset, Glare   added to the Atmosphere's (Glare as a share)
--   Cover, CloudDensity, CloudShade   the Terrain clouds (CloudShade darkens their colour)
--   Saturation, Contrast, Exposure    added to the grade (Exposure to Lighting.ExposureCompensation)
--   Tint              the grade's tint, multiplied into the time of day's
--   Lamps             added to how bright the islands' lamps burn (1 = as built)
--   Rain, Motes       how much rain, and how many glowing Qi motes (0..1)
WeatherConfig.Neutral = {
    Light = 1, Ambient = 1, Grey = 0, Density = 0, Haze = 0, Offset = 0, Glare = 1,
    Cover = 0.55, CloudDensity = 0.25, CloudShade = 1,
    Saturation = 0, Contrast = 0, Exposure = 0, Tint = Color3.new(1, 1, 1), Lamps = 0, Rain = 0, Motes = 0,
}

WeatherConfig.States = {
    Clear = { Weight = 46 },
    Cloudy = {
        Weight = 24,
        Light = 0.78, Ambient = 0.96, Grey = 0.35, Density = 0.04, Haze = 0.6, Glare = 0.3,
        Cover = 0.74, CloudDensity = 0.5, CloudShade = 0.86, Saturation = -0.06, Lamps = 0.15,
    },
    Rain = {
        Weight = 14, Repeat = false,
        Light = 0.6, Ambient = 0.92, Grey = 0.85, Density = 0.08, Haze = 1.0, Offset = -0.03, Glare = 0,
        Cover = 0.9, CloudDensity = 0.7, CloudShade = 0.68, Saturation = -0.14, Contrast = 0.04,
        Tint = Color3.fromRGB(242, 245, 250), Lamps = 0.35, Rain = 1,
    },
    Fog = {
        Weight = 12, Repeat = false, NotAtNight = true,
        Light = 0.82, Ambient = 1.04, Grey = 0.5, Density = 0.16, Haze = 2.0, Offset = -0.12, Glare = 0,
        Cover = 0.6, CloudDensity = 0.4, CloudShade = 0.95, Saturation = -0.08, Contrast = -0.03, Lamps = 0.2,
    },
    -- the rare one: the air fills with slow glowing motes of Qi, the light turns faintly jade and gold. Only a look for now.
    QiBloom = {
        Weight = 6, Repeat = false,
        Light = 1, Ambient = 1.04, Haze = 0.3, Cover = 0.3, CloudDensity = 0.25,
        Saturation = 0.06, Tint = Color3.fromRGB(240, 255, 246), Lamps = 0.2, Motes = 1,
    },
}

-- The time of day's looks, by ClockTime (0..24), blended between neighbours. Noon is the look the game had before the cycle
-- (WorldConfig's old fixed lighting at 14.5), so the daytime the owner tuned the auras and pets under is unchanged.
--   Brightness, Ambient, OutdoorAmbient, Exposure: Lighting's (Exposure is ExposureCompensation)
--   AtmoDensity .. AtmoHaze: the Atmosphere's
--   CloudColor: the Terrain clouds' colour
--   Tint, Saturation, Contrast: the weather's own grade (WeatherGrade; the place's AuraColorCorrection is left as it is)
--   Lamps: how bright the islands' lamps burn (1 = as built)
local NOON = {
    Brightness = 2.2, Ambient = Color3.fromRGB(60, 70, 90), OutdoorAmbient = Color3.fromRGB(130, 140, 165), Exposure = 0,
    AtmoDensity = 0.32, AtmoOffset = 0.2, AtmoColor = Color3.fromRGB(199, 220, 240), AtmoDecay = Color3.fromRGB(106, 132, 170),
    AtmoGlare = 0.15, AtmoHaze = 1.2,
    CloudColor = Color3.fromRGB(255, 255, 255), Tint = Color3.new(1, 1, 1), Saturation = 0, Contrast = 0, Lamps = 1,
}

-- the moonlit night: a deep blue sky, the ground lit cool and soft enough to read, the lamps and glows doing the rest
local NIGHT = {
    Brightness = 1.1, Ambient = Color3.fromRGB(74, 84, 126), OutdoorAmbient = Color3.fromRGB(112, 126, 176), Exposure = 0.15,
    AtmoDensity = 0.3, AtmoOffset = 0.15, AtmoColor = Color3.fromRGB(70, 88, 135), AtmoDecay = Color3.fromRGB(40, 52, 96),
    AtmoGlare = 0, AtmoHaze = 0.6,
    CloudColor = Color3.fromRGB(120, 132, 170), Tint = Color3.fromRGB(226, 234, 255), Saturation = 0.04, Contrast = 0.04, Lamps = 1.9,
}

WeatherConfig.Noon = NOON
WeatherConfig.Night = NIGHT

WeatherConfig.Times = {
    { Clock = 0, Look = NIGHT },
    { Clock = 4.9, Look = NIGHT },
    -- dawn: a rose and peach sky, the light warming up
    { Clock = 5.9, Look = {
        Brightness = 1.4, Ambient = Color3.fromRGB(78, 74, 100), OutdoorAmbient = Color3.fromRGB(128, 118, 150), Exposure = 0.1,
        AtmoDensity = 0.33, AtmoOffset = 0.2, AtmoColor = Color3.fromRGB(236, 186, 176), AtmoDecay = Color3.fromRGB(150, 110, 150),
        AtmoGlare = 0.4, AtmoHaze = 1.4,
        CloudColor = Color3.fromRGB(255, 214, 205), Tint = Color3.fromRGB(255, 240, 236), Saturation = 0.04, Contrast = 0.02, Lamps = 1.4,
    } },
    { Clock = 7.2, Look = {
        Brightness = 2.0, Ambient = Color3.fromRGB(64, 70, 90), OutdoorAmbient = Color3.fromRGB(132, 136, 160), Exposure = 0,
        AtmoDensity = 0.32, AtmoOffset = 0.2, AtmoColor = Color3.fromRGB(214, 220, 236), AtmoDecay = Color3.fromRGB(120, 132, 170),
        AtmoGlare = 0.25, AtmoHaze = 1.3,
        CloudColor = Color3.fromRGB(255, 246, 236), Tint = Color3.fromRGB(255, 250, 246), Saturation = 0, Contrast = 0, Lamps = 1,
    } },
    { Clock = 9, Look = NOON },
    { Clock = 15.6, Look = NOON },
    -- golden hour
    { Clock = 17.2, Look = {
        Brightness = 2.0, Ambient = Color3.fromRGB(70, 66, 82), OutdoorAmbient = Color3.fromRGB(150, 134, 140), Exposure = 0,
        AtmoDensity = 0.33, AtmoOffset = 0.2, AtmoColor = Color3.fromRGB(240, 206, 170), AtmoDecay = Color3.fromRGB(160, 120, 130),
        AtmoGlare = 0.5, AtmoHaze = 1.5,
        CloudColor = Color3.fromRGB(255, 222, 180), Tint = Color3.fromRGB(255, 244, 228), Saturation = 0.06, Contrast = 0.02, Lamps = 1.2,
    } },
    -- sunset: the sun on the rim, a deep coral and violet sky
    { Clock = 18.1, Look = {
        Brightness = 1.5, Ambient = Color3.fromRGB(80, 74, 112), OutdoorAmbient = Color3.fromRGB(138, 122, 162), Exposure = 0.12,
        AtmoDensity = 0.34, AtmoOffset = 0.2, AtmoColor = Color3.fromRGB(240, 160, 140), AtmoDecay = Color3.fromRGB(130, 80, 130),
        AtmoGlare = 0.6, AtmoHaze = 1.6,
        CloudColor = Color3.fromRGB(255, 176, 150), Tint = Color3.fromRGB(255, 236, 232), Saturation = 0.08, Contrast = 0.03, Lamps = 1.6,
    } },
    -- twilight: blue hour, on its way to the night
    { Clock = 18.9, Look = {
        Brightness = 1.2, Ambient = Color3.fromRGB(74, 80, 122), OutdoorAmbient = Color3.fromRGB(112, 120, 172), Exposure = 0.15,
        AtmoDensity = 0.31, AtmoOffset = 0.17, AtmoColor = Color3.fromRGB(110, 110, 170), AtmoDecay = Color3.fromRGB(60, 58, 112),
        AtmoGlare = 0.1, AtmoHaze = 0.9,
        CloudColor = Color3.fromRGB(160, 150, 196), Tint = Color3.fromRGB(232, 232, 255), Saturation = 0.05, Contrast = 0.04, Lamps = 1.8,
    } },
    { Clock = 19.8, Look = NIGHT },
    { Clock = 24, Look = NIGHT },
}

-- The rain and the motes, round the camera (WeatherController). Rates are particles a second at full rain.
WeatherConfig.Rain = {
    Rate = 520,            -- on a PC
    PhoneRate = 180,       -- Quality.Low
    ReducedRate = 60,      -- with Reduced Effects on: a few streaks, so it still reads as rain
    Area = 64,             -- studs square the drops fall over, centred a little ahead of the camera
    Height = 40,           -- studs above the camera they start
    Ahead = 14,            -- studs ahead of the camera the area's centre sits
    Speed = 105,           -- studs a second
    CoverReach = 70,       -- studs above the camera a roof (or the World Tree's crown) stops the rain there
    Color = Color3.fromRGB(196, 214, 236),
    NightColor = Color3.fromRGB(120, 140, 182),
    Sound = "AmbRain",     -- SoundCatalog (AudioController plays it)
}

WeatherConfig.Motes = {
    Rate = 40, PhoneRate = 16, ReducedRate = 6,
    Area = 80, Height = 18,
    Colors = { Color3.fromRGB(120, 255, 214), Color3.fromRGB(255, 222, 130) },
}

-- The phases' names for the server's "DayPhase" attribute and anyone who asks (WeatherRules.phaseAt).
WeatherConfig.Phases = { "Day", "Dusk", "Night", "Dawn" }

return WeatherConfig
