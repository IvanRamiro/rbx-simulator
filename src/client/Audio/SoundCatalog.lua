-- Every sound in the game, by name (Sfx plays them). Only Roblox's licensed libraries: Pro Sound
-- Effects (the "ProSoundEffects" uploads) and APM Music (the "APMOfficial" uploads), free to use in
-- any Roblox experience. Each one was checked to load in this place.
--
--   Id      an asset id, or a list played at random (variants)
--   Volume  0..10 (before its SoundGroup's volume)
--   Pitch   a PlaybackSpeed, or {min, max} picked at random
--   Group   "Effects" (default), "Interface", "Ambience" or "Music"
--   Near    studs within which it plays at full volume (default 10)
--   Reach   studs beyond which it is silent, and not played at all (default 120)
--   Start   seconds into the file it starts (skipping a quiet lead-in)
--   Length  seconds it plays before a quick fade (cutting a long tail)
--   With    another entry (or a list) played with it, at the same place: a layered sound
--   FadeIn, FadeOut  seconds, for a loop
--
-- Levels were set from each file's measured loudness (PlaybackLoudness in Play; the files differ
-- by up to 200 times), so sounds of a kind sit together: a guardian's blows loudest, then the egg,
-- then the player's own moves, then the interface; the beds and music by their average. Starts
-- skip lead-ins measured the same way. Re-measure before swapping a file.
local function guardian(spec)
    spec.Near = spec.Near or 40
    spec.Reach = spec.Reach or 420 -- as far as a guardian is animated
    return spec
end

return {
    -- ---------- the Awakened Stone Lion ----------
    LionAwaken = guardian({ Id = "9118694131", Volume = 5, Pitch = 0.8, Start = 1.1, With = "LionGrowl" }), -- stone cracks open
    LionGrowl = guardian({ Id = "9113973164", Volume = 0.8, Pitch = 0.75 }),
    LionSlam = guardian({ Id = { "9119037589", "9119037874" }, Volume = 1, Pitch = { 0.8, 0.9 } }),
    LionRoar = guardian({ Id = "9120030751", Volume = 3.2, Pitch = 0.9 }),                               -- a roar with thunder in it
    LionLand = guardian({ Id = { "9114362615", "9114362918" }, Volume = 3, Pitch = 0.85, With = "RockDebris" }),
    LionWeaken = guardian({ Id = "9125628981", Volume = 2.2, Pitch = 0.8 }),
    RockDebris = guardian({ Id = "9118587494", Volume = 1.2, Pitch = 0.8, Start = 0.2 }),

    -- ---------- the Bamboo Mantis Sage ----------
    MantisAwaken = guardian({ Id = "9125405458", Volume = 4, Pitch = 0.8, Start = 0.3, With = "BladeRing" }), -- bamboo creaks, blades ring out
    BladeRing = guardian({ Id = "9116689911", Volume = 2.5, Pitch = 0.6 }),
    MantisScythe = guardian({ Id = { "9119699577", "9119699897", "9126014082" }, Volume = 2.5, Pitch = { 0.75, 0.85 } }),
    MantisBladeWave = guardian({ Id = "9114159981", Volume = 3, Pitch = 0.9 }),
    MantisLand = guardian({ Id = "9113470014", Volume = 0.8, Pitch = 0.8, Start = 0.5, Length = 0.6 }),
    MantisWeaken = guardian({ Id = "9119577515", Volume = 5, Pitch = 0.8 }),                             -- bamboo stalks snapping

    -- ---------- the Ember Xuanwu ----------
    XuanwuAwaken = guardian({ Id = "9113220677", Volume = 2, Pitch = 0.85, With = "FireSurge" }),          -- the mountain breaks, fire rises
    FireSurge = guardian({ Id = "9114432334", Volume = 2.7, Length = 4 }),
    XuanwuLash = guardian({ Id = "9113611449", Volume = 5, Pitch = 0.8, With = "SerpentHiss" }),
    SerpentHiss = guardian({ Id = "9120049675", Volume = 4, Pitch = 0.9 }),
    XuanwuQuake = guardian({ Id = "9114362918", Volume = 3, Pitch = 0.75, With = "QuakeRumble" }),
    QuakeRumble = guardian({ Id = "9113222322", Volume = 2.4, Length = 3.5 }),
    XuanwuLand = guardian({ Id = "9119037589", Volume = 0.9, Pitch = 0.75, With = "FlameBurst" }),
    FlameBurst = guardian({ Id = "9114463208", Volume = 1.6 }),
    XuanwuWeaken = guardian({ Id = "9116308360", Volume = 1.2, Pitch = 0.65 }),

    -- ---------- Tiangou the Moon-Eater ----------
    TiangouAwaken = guardian({ Id = "9120790529", Volume = 1.1, Pitch = 0.85 }),
    TiangouHowl = guardian({ Id = "9120790553", Volume = 0.75, Pitch = 0.8, Start = 0.9, Length = 3.6 }),
    TiangouBite = guardian({ Id = "9120048719", Volume = 0.75, Pitch = 1.1, Start = 0.2, Length = 0.7, With = "JawCrunch" }),
    JawCrunch = guardian({ Id = "9113660664", Volume = 1.4, Pitch = 0.7 }),
    TiangouLand = guardian({ Id = "9113470020", Volume = 0.8, Pitch = 0.8, Start = 0.6, Length = 0.5 }),
    TiangouWeaken = guardian({ Id = "9113954502", Volume = 6, Pitch = 0.85 }),                         -- lonely howls, echoing

    -- ---------- Pangu the World-Splitter ----------
    PanguAwaken = guardian({ Id = "9114630281", Volume = 2.1, Pitch = 0.75, With = "QuakeRumble" }),     -- a giant's groan over the earth
    PanguCleave = guardian({ Id = "9126234246", Volume = 1.7, Pitch = 0.85 }),
    PanguSplit = guardian({ Id = "9116282875", Volume = 1, Start = 1.3, Length = 2.8 }),              -- lightning tears the sky
    PanguNova = guardian({ Id = "9120703628", Volume = 0.9, Pitch = 0.85, Start = 1.6, Length = 1.8, With = "NovaBoom" }),
    NovaBoom = guardian({ Id = "9114362615", Volume = 2.5, Pitch = 0.7 }),
    PanguLand = guardian({ Id = "9113220677", Volume = 2, Pitch = 0.8, Length = 2.5, With = "LionSlam" }),
    PanguWeaken = guardian({ Id = "9114628113", Volume = 1.7, Pitch = 0.8 }),

    -- ---------- every guardian ----------
    GuardianLeap = guardian({ Id = "9113080339", Volume = 3, Pitch = 0.8, Start = 0.3 }),

    -- ---------- the egg's theft ----------
    EggSteal = { Id = "9116394876", Volume = 7, Near = 20, Reach = 200 },
    EggDrop = { Id = "9118588165", Volume = 1, Near = 20, Reach = 200 },
    EggSecure = { Id = "1842361194", Volume = 6, Near = 20, Reach = 200, Start = 0.5, Length = 2.5 },  -- a bell-tree run
    EggReturn = { Id = "9125635297", Volume = 1.5, Near = 20, Reach = 200, Length = 2.2 },
    ChaseLoop = { Id = "9043365842", Volume = 0.3, Group = "Music" },                                  -- a heartbeat under the battle drums

    -- ---------- strikes and movement ----------
    PalmStrike = { Id = { "9125496394", "9119699577" }, Volume = 1.2, Pitch = { 1, 1.15 }, Reach = 90 },
    SwordSwing = { Id = { "9126014082", "9126013811", "9119700022" }, Volume = 1.3, Pitch = { 0.95, 1.1 }, Reach = 90 },
    SpearThrust = { Id = { "9126014082", "9126013811", "9119700022" }, Volume = 1.4, Pitch = { 0.75, 0.85 }, Reach = 90 },
    SkillPalm = { Id = { "9125496394", "9119699577" }, Volume = 1.8, Pitch = { 0.68, 0.76 }, Reach = 120 },
    SkillWave = { Id = { "9126014082", "9126013811", "9119700022" }, Volume = 1.9, Pitch = { 0.62, 0.7 }, Reach = 120 },
    SkillNova = { Id = "9113552058", Volume = 1.6, Pitch = 1, Length = 1.4, Near = 15, Reach = 140 },
    QiImpact = { Id = { "9113572426", "9113484814" }, Volume = 0.55, Pitch = { 0.9, 1.05 }, Near = 15, Reach = 150 },
    Knockback = { Id = "9113502359", Volume = 1 },
    Dash = { Id = "9119467121", Volume = 1.8, Pitch = { 1, 1.1 }, Start = 0.3, Reach = 90 },
    Leap = { Id = "9125496163", Volume = 1.8, Pitch = { 1, 1.15 }, Reach = 90 },
    Land = { Id = "9113470014", Volume = 0.25, Pitch = 1.1, Start = 0.5, Length = 0.3, Reach = 70 },
    GlideLoop = { Id = "9113286969", Volume = 2, Start = 1.7, Reach = 80 },
    FlightLoop = { Id = "9125742262", Volume = 0.35, Reach = 100 },
    SwordTakeoff = { Id = "9116689911", Volume = 1.2, Pitch = 1.1, Reach = 100, With = "TakeoffRush" }, -- the blade rings, the air rushes
    TakeoffRush = { Id = "9116416120", Volume = 0.7, Start = 1.5, Length = 1.2, Reach = 100 },

    -- ---------- cultivation ----------
    CultivateLoop = { Id = "9116389876", Volume = 0.15, Near = 6, Reach = 40, FadeIn = 1.5 },             -- a deep, slowly surging hum
    Breakthrough = { Id = "1840209851", Volume = 3, Near = 20, Reach = 200, Start = 1.7, Length = 6.5 }, -- a gong

    -- ---------- hatching and relics ----------
    EggRumble = { Id = "9117371566", Volume = 0.6, Pitch = 1.3, Start = 0.25, Near = 15, Reach = 90 },
    EggCrack = { Id = "9120826936", Volume = 0.4, Near = 15, Reach = 90 },
    HatchReveal = { Id = "9125635430", Volume = 0.5, Group = "Interface" },
    RareReveal = { Id = "9113415801", Volume = 0.8, Group = "Interface", With = "HatchReveal" },        -- a great bell over the chimes
    Attune = { Id = "9114369623", Volume = 1.1, Group = "Interface", Length = 2.5 },

    -- ---------- the interface ----------
    Click = { Id = "9120887392", Volume = 0.3, Pitch = 1.2, Group = "Interface", Length = 0.25 },
    Open = { Id = "9118835637", Volume = 1.3, Group = "Interface", Start = 0.3, Length = 0.8 },
    Purchase = { Id = "9125445146", Volume = 0.9, Group = "Interface", Length = 1.2 },                 -- coins on wood
    Error = { Id = "9120887676", Volume = 0.5, Pitch = 0.8, Group = "Interface" },

    -- ---------- each island's bed ----------
    AmbYggdrasil = { Id = "9116971178", Volume = 1.6, Group = "Ambience" },    -- birds in the morning forest
    AmbJade = { Id = "9119646409", Volume = 0.35, Group = "Ambience" },        -- a stream through the grove
    AmbEmber = { Id = "9112823197", Volume = 0.13, Group = "Ambience" },       -- lava bubbling and rumbling
    AmbMoon = { Id = "9117114457", Volume = 1.3, Group = "Ambience" },         -- night insects
    AmbAbyss = { Id = "9114625552", Volume = 0.24, Group = "Ambience" },       -- an eerie wind

    -- ---------- music (APM) ----------
    MusicHub = { Id = "1847656215", Volume = 0.4, Group = "Music", FadeIn = 2.5 },     -- Forests Of The Orient
    MusicJade = { Id = "1840356481", Volume = 1.3, Group = "Music", FadeIn = 2.5 },    -- Ethnic Lullaby: bamboo flute
    MusicEmber = { Id = "9041879299", Volume = 1.3, Group = "Music", FadeIn = 2.5 },   -- Territory Conquest: tense drums
    MusicMoon = { Id = "1837129588", Volume = 0.16, Group = "Music", FadeIn = 2.5 },   -- Orient At Twilight
    MusicAbyss = { Id = "9042642782", Volume = 0.5, Group = "Music", FadeIn = 2.5 },   -- Alien Nation: dark percussion
    MusicBattle = { Id = "1840898686", Volume = 0.35, Group = "Music", FadeIn = 1.5 }, -- Kodo Ceremonial: taiko from the first beat
}
