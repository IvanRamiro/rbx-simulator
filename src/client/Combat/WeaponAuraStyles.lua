-- The look of each realm's weapon aura (WeaponAura builds them). One entry per realm, a sword and a spear that belong
-- together: the same palette and the same idea, each fitted to its own blade (Sword = {...} and Spear = {...} replace
-- or add to the shared fields). Colours are saturated on purpose (Neon blooms pale ones to white); a layer's colour is
-- written with the palette's names (Core, Main, Deep, Accent). Rates are particles a second at full detail.
local S = {}

S.Textures = {
    Glow = "rbxassetid://135169457468310",
    Streak = "rbxassetid://115312010132075",
    Spike = "rbxassetid://89522570963572",
    Star = "rbxassetid://84556863870846",
    Smoke = "rbxassetid://80021798595720",
    Ring = "rbxassetid://133636855384267",
    Law = "rbxassetid://75983337371298",
    Mist = "rbxassetid://106430686548190",
    Ribbon = "rbxassetid://99893839045856",
    Wind = "rbxassetid://124753331461910",
    Flare = "rbxassetid://14054628491",
    Glitter = "rbxassetid://14049414463",
    Chip = "rbxassetid://86117030913477",
    Flame = "rbxassetid://106209125427468",
    Clouds = "rbxassetid://138514806240957",
    Fire = "rbxasset://textures/particles/fire_main.dds",
    Sparks = "rbxasset://textures/particles/sparkles_main.dds",
}
local T = S.Textures

local function c(r, g, b)
    return Color3.fromRGB(r, g, b)
end

S.Tiers = {}

-- shared pieces ---------------------------------------------------------------------------------------------------------
local function merge(base, over)
    local out = table.clone(base)
    for k, v in over do
        out[k] = v
    end
    return out
end

-- soft light born from the blade's own surface and locked to it: the aura's body, moving with every swing
local function body(over)
    return merge({ Texture = T.Glow, Rate = 10, Lifetime = { 0.35, 0.6 }, Speed = 0, Locked = true, Shape = "Box", ShapeStyle = "Surface",
        Size = { { 0, 0.8 }, { 0.3, 1.35 }, { 1, 0.5 } }, Transparency = { { 0, 1 }, { 0.2, 0.55 }, { 1, 1 } },
        Color = { { 0, "Main" }, { 1, "Deep" } } }, over)
end
local TIP_GLINT = { At = "tip", Texture = T.Star, Rate = 1.1, Lifetime = { 0.6, 0.9 }, Level = 2, Size = { { 0, 0.1 }, { 0.3, 0.8 }, { 1, 0 } },
    Transparency = { { 0, 1 }, { 0.2, 0.05 }, { 1, 1 } }, Rotation = { 0, 90 }, Color = { { 0, "Core" }, { 1, "Core" } } }

-- ---------- 1. Qi Awakening: dew on a reed, breath on bamboo ----------
S.Tiers[1] = {
    Name = "Dew and Breath",
    Palette = { Core = c(225, 250, 255), Main = c(90, 190, 255), Deep = c(40, 130, 230), Accent = c(150, 235, 200) },
    Stations = 6,
    -- a hairline along both edges, and beads of light running down them
    Rim = { Width = 0.05, Brightness = 2.4, Color = { { 0, "Core" }, { 1, "Main" } }, Transparency = { { 0, 0.2 }, { 1, 0.45 } } },
    Flow = { Width = 0.1, Texture = T.Glow, Length = 0.9, Speed = 1.0, Brightness = 2.8, Mirror = true,
        Color = { { 0, "Core" }, { 1, "Main" } }, Transparency = { { 0, 0.2 }, { 1, 0.55 } } },
    Halo = { Scale = 1.9, Add = 0.1, Transparency = { { 0, 0.8 }, { 1, 0.9 } }, Brightness = 1.4 },
    Emitters = {
        -- breath: a thin veil of mist hugging the blade and rising off it
        { Texture = T.Mist, Rate = 5, Lifetime = { 1.0, 1.5 }, Speed = 0.25, Locked = true, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, 0.9, 0 },
            Size = { { 0, 0.7 }, { 1, 1.5 } }, Transparency = { { 0, 1 }, { 0.3, 0.74 }, { 1, 1 } }, Color = { { 0, "Main" }, { 1, "Core" } }, LightEmission = 0.6 },
        -- dew: beads that slide off the blade and fall
        { Texture = T.Glow, Rate = 7, Lifetime = { 0.9, 1.4 }, Speed = { 0.1, 0.5 }, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, -3, 0 },
            Size = { { 0, 0.1 }, { 0.3, 0.22 }, { 1, 0.04 } }, Transparency = { { 0, 1 }, { 0.15, 0.1 }, { 1, 1 } }, Color = { { 0, "Core" }, { 1, "Main" } } },
        TIP_GLINT,
    },
    Wake = { Lifetime = 0.25, Texture = T.Glow, Brightness = 1.8 },
    Light = { Range = 7, Brightness = 0.6 },
}

-- ---------- 2. Qi Foundation: a current of jade ----------
S.Tiers[2] = {
    Name = "Jade Current",
    Palette = { Core = c(215, 255, 240), Main = c(50, 225, 170), Deep = c(20, 130, 190), Accent = c(130, 210, 255) },
    Stations = 6,
    Rim = { Width = 0.06, Brightness = 2.4, Color = { { 0, "Core" }, { 1, "Main" } }, Transparency = { { 0, 0.15 }, { 1, 0.4 } } },
    -- a ribbon of jade water flowing along the edges, quick toward the point
    Flow = { Width = 0.11, Texture = T.Glow, Length = 1.1, Speed = 2.2, Brightness = 2.8,
        Color = { { 0, "Main" }, { 1, "Accent" } }, Transparency = { { 0, 0.3 }, { 1, 0.6 } } },
    Halo = { Scale = 2.1, Add = 0.1, Transparency = { { 0, 0.76 }, { 1, 0.88 } }, Brightness = 1.5 },
    Emitters = {
        body({ Rate = 8, Color = { { 0, "Main" }, { 1, "Accent" } } }),
        -- chips of jade that break away, turning, and drift down
        { Texture = T.Chip, Rate = 3, Lifetime = { 1.1, 1.6 }, Speed = { 0.3, 0.9 }, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, -1.2, 0 }, LightEmission = 0.5,
            RotSpeed = { -140, 140 }, Rotation = { 0, 360 }, Size = { { 0, 0.05 }, { 0.2, 0.26 }, { 1, 0.12 } }, Transparency = { { 0, 1 }, { 0.15, 0.1 }, { 0.8, 0.3 }, { 1, 1 } },
            Color = { { 0, "Core" }, { 1, "Main" } }, Level = 2 },
        TIP_GLINT,
    },
    Wake = { Lifetime = 0.3, Texture = T.Glow, Brightness = 1.8 },
    Light = { Range = 8, Brightness = 0.7 },
}

-- ---------- 3. Spirit Core: flame round a burning core ----------
S.Tiers[3] = {
    Name = "Core Flame",
    Palette = { Core = c(215, 255, 175), Main = c(30, 230, 140), Deep = c(10, 120, 80), Accent = c(255, 150, 50) },
    Stations = 6,
    Rim = { Width = 0.06, Brightness = 2.6, Color = { { 0, "Core" }, { 1, "Main" } }, Transparency = { { 0, 0.1 }, { 1, 0.35 } } },
    Halo = { Scale = 2.2, Add = 0.12, Transparency = { { 0, 0.7 }, { 1, 0.86 } }, Brightness = 1.7, Color = { { 0, "Main" }, { 1, "Deep" } } },
    Emitters = {
        -- tongues of flame licking up the blade from its own surface
        { Texture = T.Fire, Rate = 10, Lifetime = { 0.45, 0.7 }, Speed = { 0.2, 0.6 }, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, 4, 0 },
            Rotation = { -25, 25 }, Size = { { 0, 0.5 }, { 0.35, 0.95 }, { 1, 0.15 } }, Transparency = { { 0, 1 }, { 0.15, 0.45 }, { 0.7, 0.75 }, { 1, 1 } },
            Color = { { 0, "Core" }, { 0.5, "Main" }, { 1, "Deep" } }, Brightness = 1.4 },
        -- embers thrown off
        { Texture = T.Glow, Rate = 7, Lifetime = { 0.7, 1.2 }, Speed = { 0.6, 1.6 }, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, 3, 0 }, Spread = 40,
            Size = { { 0, 0.14 }, { 1, 0.02 } }, Transparency = { { 0, 1 }, { 0.1, 0 }, { 1, 1 } }, Color = { { 0, "Core" }, { 1, "Accent" } }, Level = 2 },
        TIP_GLINT,
    },
    Spear = { Emitters = {
        { Texture = T.Fire, Rate = 12, Lifetime = { 0.4, 0.7 }, Speed = { 0.2, 0.6 }, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, 4.5, 0 },
            Rotation = { -25, 25 }, Size = { { 0, 0.55 }, { 0.35, 1.05 }, { 1, 0.15 } }, Transparency = { { 0, 1 }, { 0.15, 0.4 }, { 0.7, 0.75 }, { 1, 1 } },
            Color = { { 0, "Core" }, { 0.5, "Accent" }, { 1, "Deep" } }, Brightness = 1.4 },
        { Texture = T.Glow, Rate = 9, Lifetime = { 0.8, 1.3 }, Speed = { 0.6, 1.8 }, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, 3.4, 0 }, Spread = 40,
            Size = { { 0, 0.16 }, { 1, 0.02 } }, Transparency = { { 0, 1 }, { 0.1, 0 }, { 1, 1 } }, Color = { { 0, "Core" }, { 1, "Accent" } }, Level = 2 },
        TIP_GLINT,
    } },
    Wake = { Lifetime = 0.3, Texture = T.Glow, Brightness = 1.8 },
    Light = { Range = 9, Brightness = 0.9 },
}

-- ---------- 4. Spirit Soul: an echo that trails the steel ----------
S.Tiers[4] = {
    Name = "Soul Echo",
    Palette = { Core = c(230, 255, 252), Main = c(60, 225, 205), Deep = c(20, 100, 150), Accent = c(200, 235, 255) },
    Stations = 6,
    Rim = { Width = 0.05, Brightness = 2.4, Color = { { 0, "Core" }, { 1, "Main" } }, Transparency = { { 0, 0.15 }, { 1, 0.4 } } },
    -- the blade's ghost: a second outline standing a little way out, slowly breathing along
    Echo = { Hug = 2.6, Pad = 0.12, Width = 0.05, Texture = T.Glow, Length = 2.4, Speed = 0.5, Brightness = 2, Mirror = true,
        Color = { { 0, "Accent" }, { 1, "Main" } }, Transparency = { { 0, 0.45 }, { 1, 0.8 } } },
    Halo = { Scale = 2.0, Add = 0.1, Transparency = { { 0, 0.8 }, { 1, 0.9 } }, Brightness = 1.4 },
    Emitters = {
        -- soul smoke: slow swirls peeling off
        { Texture = T.Wind, Rate = 4, Lifetime = { 1.0, 1.5 }, Speed = 0.3, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, 0.8, 0 }, RotSpeed = { -30, 30 }, Rotation = { 0, 360 },
            Size = { { 0, 0.5 }, { 1, 1.3 } }, Transparency = { { 0, 1 }, { 0.25, 0.76 }, { 1, 1 } }, Color = { { 0, "Accent" }, { 1, "Main" } }, LightEmission = 0.7 },
        body({ Rate = 7, Color = { { 0, "Accent" }, { 1, "Main" } } }),
        TIP_GLINT,
    },
    Extras = { { Kind = "Sweep", Every = 3.2, Run = 0.6, Emitter = { Texture = T.Star, Lifetime = 0.5, Size = { { 0, 0.7 }, { 1, 0 } }, Color = { { 0, "Core" }, { 1, "Core" } },
        Transparency = { { 0, 1 }, { 0.2, 0.1 }, { 1, 1 } } } } },
    Wake = { Lifetime = 0.34, Texture = T.Glow, Brightness = 1.6, Transparency = { { 0, 0.5 }, { 1, 1 } } },
    Light = { Range = 8, Brightness = 0.7 },
}

-- ---------- 5. Ascendant: gold wind drawn through the sky ----------
S.Tiers[5] = {
    Name = "Gold Wind",
    Palette = { Core = c(255, 240, 170), Main = c(255, 185, 40), Deep = c(200, 105, 20), Accent = c(255, 225, 130) },
    Stations = 6,
    Rim = { Width = 0.07, Brightness = 2.6, Color = { { 0, "Core" }, { 1, "Main" } }, Transparency = { { 0, 0.1 }, { 1, 0.35 } } },
    Flow = { Width = 0.12, Texture = T.Glow, Length = 2.0, Speed = 3.6, Brightness = 2.8, Color = { { 0, "Core" }, { 1, "Main" } }, Transparency = { { 0, 0.3 }, { 1, 0.65 } } },
    Halo = { Scale = 2.1, Add = 0.1, Transparency = { { 0, 0.72 }, { 1, 0.86 } }, Brightness = 1.7 },
    Emitters = {
        -- wind: swirls of gold shed behind
        { Texture = T.Wind, Rate = 4, Lifetime = { 0.7, 1.0 }, Speed = 0.4, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, 1.2, 0 }, RotSpeed = { -60, 60 }, Rotation = { 0, 360 },
            Size = { { 0, 0.6 }, { 1, 1.6 } }, Transparency = { { 0, 1 }, { 0.25, 0.7 }, { 1, 1 } }, Color = { { 0, "Core" }, { 1, "Main" } }, Level = 2 },
        -- gold slivers rising off the steel
        { Texture = T.Streak, Rate = 9, Lifetime = { 0.4, 0.7 }, Speed = { 0.6, 1.4 }, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, 5, 0 }, Orientation = "VelocityParallel",
            Size = { { 0, 0.5 }, { 1, 0.15 } }, Transparency = { { 0, 1 }, { 0.15, 0.1 }, { 1, 1 } }, Color = { { 0, "Core" }, { 1, "Main" } }, Brightness = 1.5 },
        TIP_GLINT,
    },
    Wake = { Lifetime = 0.36, Texture = T.Glow, Brightness = 2, WidthScale = { { 0, 1.2 }, { 1, 0 } } },
    Light = { Range = 9, Brightness = 0.9 },
}

-- ---------- 6. Immortal: pearl light and a falling bloom ----------
S.Tiers[6] = {
    Name = "Pearl Bloom",
    Palette = { Core = c(255, 250, 235), Main = c(255, 205, 110), Deep = c(255, 150, 70), Accent = c(255, 190, 215) },
    Stations = 6,
    Rim = { Width = 0.06, Brightness = 2.6, Color = { { 0, "Core" }, { 1, "Main" } }, Transparency = { { 0, 0.05 }, { 1, 0.3 } } },
    Halo = { Scale = 2.8, Add = 0.16, Transparency = { { 0, 0.6 }, { 1, 0.82 } }, Brightness = 1.9, Color = { { 0, "Core" }, { 1, "Main" } } },
    Emitters = {
        body({ Rate = 8, Size = { { 0, 0.7 }, { 0.3, 1.25 }, { 1, 0.4 } }, Color = { { 0, "Core" }, { 1, "Main" } }, Transparency = { { 0, 1 }, { 0.2, 0.78 }, { 1, 1 } } }),
        -- motes of pearl falling slowly, as petals of light do
        { Texture = T.Star, Rate = 6, Lifetime = { 1.3, 2 }, Speed = { 0.2, 0.7 }, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, -0.7, 0 }, RotSpeed = { -90, 90 }, Rotation = { 0, 360 },
            Size = { { 0, 0.05 }, { 0.2, 0.34 }, { 1, 0.08 } }, Transparency = { { 0, 1 }, { 0.15, 0.05 }, { 1, 1 } }, Color = { { 0, "Core" }, { 1, "Accent" } }, Level = 2 },
        TIP_GLINT,
    },
    Extras = { { Kind = "Sweep", Every = 2.6, Run = 0.5, Burst = 3, Emitter = { Texture = T.Flare, Lifetime = 0.5, Size = { { 0, 0.9 }, { 1, 0 } }, Color = { { 0, "Core" }, { 1, "Main" } },
        Transparency = { { 0, 1 }, { 0.2, 0.15 }, { 1, 1 } }, Rotation = { 0, 360 } } } },
    Wake = { Lifetime = 0.34, Texture = T.Glow, Brightness = 1.9 },
    Light = { Range = 10, Brightness = 1.0 },
}

-- ---------- 7. Divine: lightning bound to the steel ----------
S.Tiers[7] = {
    Name = "Bound Thunder",
    Palette = { Core = c(232, 215, 255), Main = c(140, 90, 255), Deep = c(60, 30, 190), Accent = c(130, 200, 255) },
    Stations = 9,
    Rim = { Width = 0.07, Brightness = 2.8, Color = { { 0, "Core" }, { 1, "Main" } }, Transparency = { { 0, 0.05 }, { 0.5, 0.3 }, { 1, 0.1 } } },
    Halo = { Scale = 2.2, Add = 0.1, Transparency = { { 0, 0.72 }, { 1, 0.86 } }, Brightness = 1.8, Color = { { 0, "Main" }, { 1, "Deep" } } },
    Emitters = {
        -- crackle: short sharp sparks thrown off every side
        { Texture = T.Spike, Rate = 12, Lifetime = { 0.12, 0.22 }, Speed = { 3, 6 }, Shape = "Box", ShapeStyle = "Surface", Spread = 70, Orientation = "VelocityParallel",
            Size = { { 0, 0.5 }, { 1, 0.1 } }, Transparency = { { 0, 0 }, { 1, 1 } }, Color = { { 0, "Core" }, { 1, "Accent" } }, Brightness = 2 },
        body({ Rate = 7, Color = { { 0, "Core" }, { 1, "Main" } } }),
        TIP_GLINT,
    },
    Extras = { { Kind = "Lightning", Count = 3, Every = 0.11, Chance = 0.75, Span = 1.2, Reach = 0.22, Width = 0.08, Brightness = 3.2,
        Color = { { 0, "Core" }, { 0.5, "Accent" }, { 1, "Main" } } } },
    Wake = { Lifetime = 0.3, Texture = T.Streak, Brightness = 2.2 },
    Light = { Range = 10, Brightness = 1.1 },
}

-- ---------- 8. Cosmic: a river of stars ----------
S.Tiers[8] = {
    Name = "Star River",
    Palette = { Core = c(220, 232, 255), Main = c(110, 125, 255), Deep = c(50, 40, 170), Accent = c(255, 165, 235) },
    Stations = 6,
    Rim = { Width = 0.06, Brightness = 2.4, Color = { { 0, "Core" }, { 1, "Main" } }, Transparency = { { 0, 0.1 }, { 1, 0.4 } } },
    Flow = { Width = 0.1, Texture = T.Glow, Length = 0.6, Speed = 0.8, Brightness = 2.8, Color = { { 0, "Accent" }, { 0.5, "Main" }, { 1, "Deep" } }, Transparency = { { 0, 0.35 }, { 1, 0.7 } } },
    Halo = { Scale = 2.3, Add = 0.12, Transparency = { { 0, 0.74 }, { 1, 0.88 } }, Brightness = 1.6, Color = { { 0, "Main" }, { 1, "Deep" } } },
    Emitters = {
        -- nebula: soft coloured cloud over the blade
        { Texture = T.Glitter, Rate = 5, Lifetime = { 1.0, 1.5 }, Speed = 0.2, Locked = true, Shape = "Box", ShapeStyle = "Surface", RotSpeed = { -20, 20 }, Rotation = { 0, 360 },
            Size = { { 0, 0.8 }, { 1, 1.5 } }, Transparency = { { 0, 1 }, { 0.3, 0.72 }, { 1, 1 } }, Color = { { 0, "Accent" }, { 1, "Main" } } },
        -- stars that fall away
        { Texture = T.Star, Rate = 6, Lifetime = { 0.9, 1.4 }, Speed = { 0.4, 1 }, Shape = "Box", ShapeStyle = "Surface", Size = { { 0, 0.05 }, { 0.2, 0.3 }, { 1, 0.05 } },
            Transparency = { { 0, 1 }, { 0.15, 0.05 }, { 1, 1 } }, Color = { { 0, "Core" }, { 1, "Accent" } }, Level = 2 },
    },
    Extras = { { Kind = "Orbit", Count = 3, Speed = 3.4, Rise = 0.3, Radius = 0.22,
        Emitter = { Texture = T.Star, Rate = 11, Lifetime = 0.5, Size = { { 0, 0.3 }, { 1, 0 } }, Transparency = { { 0, 0.1 }, { 1, 1 } }, Color = { { 0, "Core" }, { 1, "Accent" } } } } },
    Wake = { Lifetime = 0.32, Texture = T.Glow, Brightness = 1.8, Color = { { 0, "Core" }, { 1, "Accent" } } },
    Light = { Range = 9, Brightness = 0.9 },
}

-- ---------- 9. Void: a blade the dark leans into ----------
S.Tiers[9] = {
    Name = "Void Leak",
    Palette = { Core = c(225, 180, 255), Main = c(150, 60, 255), Deep = c(30, 6, 60), Accent = c(70, 20, 120) },
    Stations = 7,
    Rim = { Width = 0.06, Brightness = 2.8, Color = { { 0, "Core" }, { 1, "Main" } }, Transparency = { { 0, 0.05 }, { 1, 0.3 } } },
    -- the dark pulled round the steel (normal blending, not light), with the violet edge showing through it
    Halo = { Scale = 2.6, Add = 0.14, Transparency = { { 0, 0.3 }, { 1, 0.55 } }, Brightness = 1, LightEmission = 0, Color = { { 0, "Deep" }, { 1, "Deep" } } },
    Echo = { Hug = 2.2, Pad = 0.1, Width = 0.05, Texture = T.Glow, Length = 2, Speed = -0.6, Brightness = 2, Mirror = true, Color = { { 0, "Main" }, { 1, "Accent" } }, Transparency = { { 0, 0.4 }, { 1, 0.8 } } },
    Emitters = {
        -- smoke of nothing: dark, rising slowly
        { Texture = T.Smoke, Rate = 6, Lifetime = { 0.9, 1.3 }, Speed = 0.3, Locked = false, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, 0.9, 0 }, LightEmission = 0, RotSpeed = { -40, 40 }, Rotation = { 0, 360 },
            Size = { { 0, 0.5 }, { 1, 1.3 } }, Transparency = { { 0, 1 }, { 0.2, 0.35 }, { 1, 1 } }, Color = { { 0, "Deep" }, { 1, "Accent" } },
            Flipbook = { Layout = "Grid4x4", Mode = "Random", Fps = 0, Random = true } },
        -- shards that come away from the steel
        { Texture = T.Spike, Rate = 4, Lifetime = { 0.6, 1.0 }, Speed = { 0.6, 1.6 }, Shape = "Box", ShapeStyle = "Surface", Orientation = "VelocityParallel", Spread = 60,
            Size = { { 0, 0.5 }, { 1, 0.1 } }, Transparency = { { 0, 1 }, { 0.1, 0.1 }, { 1, 1 } }, Color = { { 0, "Core" }, { 1, "Main" } }, Level = 2 },
        TIP_GLINT,
    },
    Wake = { Lifetime = 0.34, Texture = T.Glow, Brightness = 1.8, Color = { { 0, "Main" }, { 1, "Deep" } } },
    Light = { Range = 8, Brightness = 0.7 },
}

-- ---------- 10. Heavenly Dao: two lights twisted about each other ----------
S.Tiers[10] = {
    Name = "Dual Helix",
    Palette = { Core = c(255, 252, 246), Main = c(238, 230, 255), Deep = c(16, 12, 30), Accent = c(255, 215, 120) },
    Stations = 6,
    Rim = { Width = 0.055, Brightness = 2.6, Color = { { 0, "Core" }, { 1, "Main" } }, Transparency = { { 0, 0.1 }, { 1, 0.4 } } },
    Halo = { Scale = 2.0, Add = 0.1, Transparency = { { 0, 0.78 }, { 1, 0.9 } }, Brightness = 1.5 },
    Emitters = {
        body({ Rate = 6, Color = { { 0, "Core" }, { 1, "Main" } } }),
        { Texture = T.Star, Rate = 5, Lifetime = { 0.8, 1.2 }, Speed = { 0.4, 1 }, Shape = "Box", ShapeStyle = "Surface", Size = { { 0, 0.05 }, { 0.2, 0.28 }, { 1, 0.05 } },
            Transparency = { { 0, 1 }, { 0.15, 0.05 }, { 1, 1 } }, Color = { { 0, "Core" }, { 1, "Accent" } }, Level = 2 },
        TIP_GLINT,
    },
    -- one ribbon of white light, one of black glass, turning opposite ways
    Extras = { { Kind = "Helix", Count = 2, Opposed = true, Turns = 1.5, Speed = 2.2, Radius = 0.14, Width = 0.1, Links = 6, Brightness = 2.4,
        Colors = { { { 0, "Core" }, { 1, "Main" } }, { { 0, "Deep" }, { 1, "Deep" } } }, Transparency = { { 0, 0.1 }, { 1, 0.25 } } } },
    Wake = { Lifetime = 0.3, Texture = T.Glow, Brightness = 1.8 },
    Light = { Range = 9, Brightness = 0.9 },
}

-- ---------- 11. Primordial: violet fire from the first age ----------
S.Tiers[11] = {
    Name = "First Fire",
    Palette = { Core = c(255, 200, 130), Main = c(175, 70, 255), Deep = c(60, 10, 95), Accent = c(255, 110, 40) },
    Stations = 6,
    Rim = { Width = 0.07, Brightness = 2.8, Color = { { 0, "Core" }, { 0.5, "Accent" }, { 1, "Main" } }, Transparency = { { 0, 0.05 }, { 1, 0.35 } } },
    Flow = { Width = 0.13, Texture = T.Glow, Length = 1.6, Speed = 0.6, Brightness = 2.8, Color = { { 0, "Accent" }, { 1, "Main" } }, Transparency = { { 0, 0.35 }, { 1, 0.7 } } },
    Halo = { Scale = 2.4, Add = 0.14, Transparency = { { 0, 0.66 }, { 1, 0.84 } }, Brightness = 1.8, Color = { { 0, "Main" }, { 1, "Deep" } } },
    Emitters = {
        -- heavy violet fire, slow
        { Texture = T.Fire, Rate = 8, Lifetime = { 0.7, 1.1 }, Speed = { 0.2, 0.5 }, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, 3, 0 }, Rotation = { -20, 20 },
            Size = { { 0, 0.6 }, { 0.35, 1.2 }, { 1, 0.2 } }, Transparency = { { 0, 1 }, { 0.15, 0.4 }, { 0.7, 0.75 }, { 1, 1 } }, Color = { { 0, "Core" }, { 0.35, "Main" }, { 1, "Deep" } }, Brightness = 1.3 },
        -- ash that rises dark
        { Texture = T.Smoke, Rate = 4, Lifetime = { 1.1, 1.6 }, Speed = 0.4, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, 1.5, 0 }, LightEmission = 0, RotSpeed = { -30, 30 }, Rotation = { 0, 360 },
            Size = { { 0, 0.5 }, { 1, 1.4 } }, Transparency = { { 0, 1 }, { 0.2, 0.4 }, { 1, 1 } }, Color = { { 0, "Deep" }, { 1, "Deep" } }, Level = 2,
            Flipbook = { Layout = "Grid4x4", Mode = "Random", Fps = 0, Random = true } },
        { Texture = T.Glow, Rate = 6, Lifetime = { 0.9, 1.5 }, Speed = { 0.5, 1.4 }, Shape = "Box", ShapeStyle = "Surface", Accel = { 0, 2.5, 0 }, Spread = 45,
            Size = { { 0, 0.15 }, { 1, 0.02 } }, Transparency = { { 0, 1 }, { 0.1, 0 }, { 1, 1 } }, Color = { { 0, "Core" }, { 1, "Accent" } }, Level = 2 },
    },
    Wake = { Lifetime = 0.36, Texture = T.Glow, Brightness = 2, Color = { { 0, "Accent" }, { 1, "Main" } }, WidthScale = { { 0, 1.2 }, { 1, 0 } } },
    Light = { Range = 10, Brightness = 1.0 },
}

-- ---------- 12. Eternal Transcendence: three lights that never part ----------
S.Tiers[12] = {
    Name = "Three Lights",
    Palette = { Core = c(255, 246, 215), Main = c(255, 200, 80), Deep = c(150, 90, 255), Accent = c(60, 200, 255) },
    Stations = 6,
    Rim = { Width = 0.07, Brightness = 3, Color = { { 0, "Core" }, { 1, "Main" } }, Transparency = { { 0, 0.05 }, { 1, 0.3 } } },
    Halo = { Scale = 2.6, Add = 0.14, Transparency = { { 0, 0.66 }, { 1, 0.84 } }, Brightness = 1.8, Color = { { 0, "Main" }, { 1, "Deep" } } },
    Emitters = {
        body({ Rate = 7, Color = { { 0, "Core" }, { 1, "Main" } } }),
        { Texture = T.Star, Rate = 5, Lifetime = { 0.9, 1.4 }, Speed = { 0.4, 1 }, Shape = "Box", ShapeStyle = "Surface", Size = { { 0, 0.05 }, { 0.2, 0.3 }, { 1, 0.05 } },
            Transparency = { { 0, 1 }, { 0.15, 0.05 }, { 1, 1 } }, Color = { { 0, "Core" }, { 1, "Accent" } }, Level = 2 },
        TIP_GLINT,
    },
    -- gold, violet and azure threads winding up the blade at their own speeds, and bright beads circling it
    Extras = {
        { Kind = "Helix", Count = 3, Turns = 1.3, Speed = 2.0, Radius = 0.15, Width = 0.085, Links = 6, Brightness = 2.6,
            Colors = { { { 0, "Core" }, { 1, "Main" } }, { { 0, "Main" }, { 1, "Deep" } }, { { 0, "Core" }, { 1, "Accent" } } }, Transparency = { { 0, 0.1 }, { 1, 0.25 } } },
        { Kind = "Orbit", Count = 3, Speed = -3, Rise = 0.25, Radius = 0.3,
            Emitter = { Texture = T.Star, Rate = 9, Lifetime = 0.45, Size = { { 0, 0.28 }, { 1, 0 } }, Transparency = { { 0, 0.1 }, { 1, 1 } }, Color = { { 0, "Core" }, { 1, "Main" } } } },
        { Kind = "Sweep", Every = 3.4, Run = 0.5, Burst = 3, Emitter = { Texture = T.Flare, Lifetime = 0.5, Size = { { 0, 1 }, { 1, 0 } }, Color = { { 0, "Core" }, { 1, "Accent" } },
            Transparency = { { 0, 1 }, { 0.2, 0.1 }, { 1, 1 } }, Rotation = { 0, 360 } } },
    },
    Wake = { Lifetime = 0.4, Texture = T.Glow, Brightness = 2.2, Color = { { 0, "Core" }, { 0.5, "Main" }, { 1, "Deep" } }, WidthScale = { { 0, 1.3 }, { 1, 0 } } },
    Light = { Range = 11, Brightness = 1.2 },
}

return S
