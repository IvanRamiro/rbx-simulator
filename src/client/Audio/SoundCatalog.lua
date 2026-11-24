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
--   Fade    seconds of the fade at the Length cut (default 0.15)
--   With    another entry (or a list) played with it, at the same place: a layered sound; a layer may be
--           { name, delay } to come in that many seconds later
--   Notes   a list of PlaybackSpeeds picked at random (a scale's notes), in place of Pitch
--   Gap     seconds within which the same sound asked again is dropped (default 0.04)
--   Max     copies of it playing at once (default 6)
--   Key     it still plays when the game is crowded with sounds (Sfx's ALIVE_LIMIT)
--   Duck    { level, seconds }: the music dips to that share for that long under it
--   Moment  seconds this big moment holds the stage: notices (`Defer`) asked meanwhile wait until it ends
--   Defer   a notice: it waits out a big moment instead of playing over it
--   FadeIn, FadeOut  seconds, for a loop
--
-- The audio identity (2026-11-15): celestial and serene. Rewards and Qi are crystal, harp, bell-tone and shimmer; the
-- big moments share one family (a glowing magic impact, Harp Glissando (C) rising a third up, a bright ding, falling
-- twinkles), sized by how big the moment is; combat is solid and physical; the interface is short, clean clicks and soft
-- tones. No gongs or other Chinese instruments.
--
-- Levels were set from each file's measured loudness (PlaybackLoudness in Play; the files differ
-- by up to 200 times), so sounds of a kind sit together: a guardian's blows loudest, then the egg,
-- then the player's own moves, then the interface; the beds and music by their average. Starts
-- skip lead-ins measured the same way. Re-measure before swapping a file.
local PetSounds = require(script.Parent:WaitForChild("PetSounds"))

local function guardian(spec)
    spec.Near = spec.Near or 40
    spec.Reach = spec.Reach or 420 -- as far as a guardian is animated
    return spec
end

local catalog = {
    -- ---------- the Awakened Stone Lion ----------
    LionAwaken = guardian({ Id = "9118694131", Volume = 5, Pitch = 0.8, Start = 1.1, With = "LionGrowl" }), -- stone cracks open
    LionGrowl = guardian({ Id = "9113973164", Volume = 0.8, Pitch = 0.75 }),
    LionSlam = guardian({ Id = { "9119037589", "9119037874" }, Volume = 1, Pitch = { 0.8, 0.9 } }),
    LionRoar = guardian({ Id = "9120030751", Volume = 3.2, Pitch = 0.9 }),                               -- a roar with thunder in it
    LionLand = guardian({ Id = { "9114362615", "9114362918" }, Volume = 3, Pitch = 0.85, With = "RockDebris" }),
    LionWeaken = guardian({ Id = "9125628981", Volume = 2.2, Pitch = 0.8 }),
    LionReady = guardian({ Id = "9113973164", Volume = 0.37, Pitch = 0.62, Length = 0.55, Fade = 0.2 }),      -- a low growl as the paw lifts (a wind-up's first sound; measured 405 x 0.37 = 150, the cues sit near the player's swings, under the blows)
    RockDebris = guardian({ Id = "9118587494", Volume = 1.2, Pitch = 0.8, Start = 0.2 }),

    -- ---------- the Bamboo Mantis Sage ----------
    MantisAwaken = guardian({ Id = "9125405458", Volume = 4, Pitch = 0.8, Start = 0.3, With = "BladeRing" }), -- bamboo creaks, blades ring out
    BladeRing = guardian({ Id = "9116689911", Volume = 2.5, Pitch = 0.6 }),
    MantisScythe = guardian({ Id = { "9119699577", "9119699897", "9126014082" }, Volume = 2.5, Pitch = { 0.75, 0.85 } }),
    MantisBladeWave = guardian({ Id = "9114159981", Volume = 3, Pitch = 0.9 }),
    MantisReady = guardian({ Id = "9116689911", Volume = 1.1, Pitch = 0.95, Length = 0.45, Fade = 0.15 }),     -- the scythes ring as they rise
    MantisLand = guardian({ Id = "9113470014", Volume = 0.8, Pitch = 0.8, Start = 0.5, Length = 0.6 }),
    MantisWeaken = guardian({ Id = "9119577515", Volume = 5, Pitch = 0.8 }),                             -- bamboo stalks snapping

    -- ---------- the Cinder Roc (Ember Peak, 2026-11-23: the Xuanwu's place) ----------
    -- Its cry is the Dawn Phoenix pet's voice, pitched down a third and held long (a bigger bird, a heavier one); every other layer is a sound this game already
    -- measured and levelled, set at the Roc's own pitches. Levels are first settings, not yet judged by ear.
    RocCry = guardian({ Id = "9114661938", Volume = 2.4, Pitch = 0.62, Length = 2.0, Fade = 0.4 }),
    RocWhoosh = guardian({ Id = "9126013811", Volume = 3, Pitch = 0.5 }),                                       -- a great wing cutting the air
    RocAwaken = guardian({ Id = "9113220677", Volume = 2, Pitch = 0.85, With = { "FireSurge", { "RocCry", 0.9 } } }), -- the mountain breaks, fire rises, then the cry
    FireSurge = guardian({ Id = "9114432334", Volume = 2.7, Length = 4 }),
    RocReady = guardian({ Id = "9126014082", Volume = 1.4, Pitch = 0.55, Length = 0.7, Fade = 0.2 }),         -- the wing cocked back: a low rush of feathers
    RocScythe = guardian({ Id = "9113611449", Volume = 4, Pitch = 1.05, With = "RocWhoosh" }),                 -- the blow, with the wing's whoosh under it
    RocGaleGather = guardian({ Id = "9114432334", Volume = 1.4, Pitch = 1.35, Length = 1.1, Fade = 0.3 }),    -- the breath drawn in as the wings rise
    RocGale = guardian({ Id = "9114362918", Volume = 3, Pitch = 0.9, With = { "QuakeRumble", "RocWhoosh" } }), -- both wings hammer down
    QuakeRumble = guardian({ Id = "9113222322", Volume = 2.4, Length = 3.5 }),
    RocLand = guardian({ Id = "9119037589", Volume = 0.9, Pitch = 0.7, With = { "FlameBurst", "RocWhoosh" } }),
    FlameBurst = guardian({ Id = "9114463208", Volume = 1.6 }),
    RocWeaken = guardian({ Id = "9116308360", Volume = 1.2, Pitch = 0.65, With = { { "RocCryWeak", 0.25 } } }),
    RocCryWeak = guardian({ Id = "9114661950", Volume = 1.6, Pitch = 0.5, Length = 2.2, Fade = 0.6 }),        -- a worn-out cry

    -- ---------- Tiangou the Moon-Eater ----------
    TiangouAwaken = guardian({ Id = "9120790529", Volume = 1.1, Pitch = 0.85 }),
    TiangouHowl = guardian({ Id = "9120790553", Volume = 0.75, Pitch = 0.8, Start = 0.9, Length = 3.6 }),
    TiangouBite = guardian({ Id = "9120048719", Volume = 0.75, Pitch = 1.1, Start = 0.2, Length = 0.7, With = "JawCrunch" }),
    JawCrunch = guardian({ Id = "9113660664", Volume = 1.4, Pitch = 0.7 }),
    TiangouReady = guardian({ Id = "9120790529", Volume = 0.26, Pitch = 1, Length = 0.45, Fade = 0.15 }),      -- a growl as the jaws open
    TiangouLand = guardian({ Id = "9113470020", Volume = 0.8, Pitch = 0.8, Start = 0.6, Length = 0.5 }),
    TiangouWeaken = guardian({ Id = "9113954502", Volume = 6, Pitch = 0.85 }),                         -- lonely howls, echoing

    -- ---------- Pangu the World-Splitter ----------
    PanguAwaken = guardian({ Id = "9114630281", Volume = 2.1, Pitch = 0.75, With = "QuakeRumble" }),     -- a giant's groan over the earth
    PanguCleave = guardian({ Id = "9126234246", Volume = 1.7, Pitch = 0.85 }),
    PanguSplit = guardian({ Id = "9116282875", Volume = 1, Start = 1.3, Length = 2.8 }),              -- lightning tears the sky
    PanguNova = guardian({ Id = "9120703628", Volume = 0.9, Pitch = 0.85, Start = 1.6, Length = 1.8, With = "NovaBoom" }),
    NovaBoom = guardian({ Id = "9114362615", Volume = 2.5, Pitch = 0.7 }),
    PanguReady = guardian({ Id = "9114630281", Volume = 0.67, Pitch = 0.95, Length = 0.6, Fade = 0.2 }),         -- a titan's groan as the weapon lifts
    PanguLand = guardian({ Id = "9113220677", Volume = 2, Pitch = 0.8, Length = 2.5, With = "LionSlam" }),
    PanguWeaken = guardian({ Id = "9114628113", Volume = 1.7, Pitch = 0.8 }),

    -- ---------- every guardian ----------
    GuardianLeap = guardian({ Id = "9113080339", Volume = 3, Pitch = 0.8, Start = 0.3 }),
    -- a guardian notices its egg is gone (played a beat after the theft, at the guardian; GuardianController ALERTS)
    TiangouAlert = guardian({ Id = "9120790529", Volume = 1.1, Pitch = 0.9, Length = 1.6, Fade = 0.4 }),
    PanguAlert = guardian({ Id = "9114630281", Volume = 1.6, Pitch = 0.8, Length = 1.8, Fade = 0.5 }),

    -- ---------- the egg's theft ----------
    -- Levels below are each file's peak PlaybackLoudness at volume 1 (measured muted in Play, 2026-11-15) times its Volume,
    -- the number after "=" in the comments: the interface sits near 90, the player's feedback 130 to 170, the big moments'
    -- loudest layer 250 to 300.
    -- the take: a quick upward zip and a soft glowing thud at the stand, heard by anyone near (Magic Zoom Up 2: 239 x 0.7 =
    -- 167; Magic Burst 5: 259 x 0.55 = 142)
    EggSteal = { Id = "9125647528", Volume = 0.7, Pitch = { 0.97, 1.03 }, Near = 20, Reach = 200, With = "StealThud" },
    StealThud = { Id = "9116385087", Volume = 0.55, Pitch = 1.1, Near = 20, Reach = 200 },
    -- and the thief alone hears the danger: a hissing reversed whoosh (69 x 2.2 = 152), while the guardian turns
    StealSting = { Id = "9118158081", Volume = 2.2, Key = true },
    -- knocked loose: the egg thuds down and its glow spills (Body Fall Thud 1: 213 x 0.8 = 170; Falling Shimmer: 97 x 1.3)
    EggDrop = { Id = "9113480917", Volume = 0.8, Pitch = { 0.9, 1 }, Near = 20, Reach = 200, With = { { "DropSpill", 0.05 } } },
    DropSpill = { Id = "9116418035", Volume = 1.3, Start = 0.7, Length = 1.4, Fade = 0.4, Near = 20, Reach = 200 },
    -- picked back up: the zip again and a glassy tone (184 x 0.85 = 156; 141 x 0.8 = 113)
    EggRecover = { Id = "9125648149", Volume = 0.85, Near = 20, Reach = 200, With = { { "RecoverTone", 0.15 } } },
    RecoverTone = { Id = "9126073644", Volume = 0.8, Pitch = 1.12, Near = 20, Reach = 200 },
    -- whisked back to its stand (a sparkling pass-by: 162 x 1.1 = 178)
    EggReturn = { Id = "9125635297", Volume = 1.1, Near = 20, Reach = 200, Length = 2.2 },
    -- SECURED: the thief's reward stinger, flat, about 3 s, landing with the gold flash (GuardianFx.secure) and the toast:
    --   0.00  impact: Magic Burst 1, its 0.1 s lead-in skipped (461 x 0.65 = 300), a glowing tonal decay;
    --   0.00  an upward tubular zip into it (184 x 0.8 = 147);
    --   0.08  the rising chime: Harp Glissando (C), the one rising run of the set (its spectrum climbs for a second),
    --         lifted a major third and quickened (90 x 2.2 = 198);
    --   0.80  a bright bell-tone ding as the run tops out (219 x 0.85 = 186);
    --   0.90  the shimmer tail: descending twinkles (97 x 1.9 = 184), fading out by about 3.1 s.
    -- The music dips under it.
    EggSecure = { Id = "9116384485", Volume = 0.65, Start = 0.1, Length = 2.2, Fade = 0.6, Key = true, Duck = { 0.3, 2.6 }, Moment = 2.6,
        With = { { "SecureZip", 0 }, { "SecureHarp", 0.08 }, { "SecureDing", 0.8 }, { "SecureTail", 0.9 } } },
    SecureZip = { Id = "9125648149", Volume = 0.8, Key = true },
    SecureHarp = { Id = "1840525370", Volume = 2.2, Start = 0.3, Pitch = 1.26, Length = 2.3, Fade = 0.6, Key = true },
    SecureDing = { Id = "9126072453", Volume = 0.85, Start = 0.25, Key = true },
    SecureTail = { Id = "9116418035", Volume = 1.9, Start = 0.65, Length = 1.6, Fade = 0.6, Key = true },
    -- the same moment as anyone near hears it: quieter, from where the egg was secured
    EggSecureWorld = { Id = "9116384485", Volume = 0.4, Start = 0.1, Length = 2, Fade = 0.6, Near = 15, Reach = 160,
        With = { { "SecureWorldHarp", 0.08 }, { "SecureWorldTail", 0.9 } } },
    SecureWorldHarp = { Id = "1840525370", Volume = 1.4, Start = 0.3, Pitch = 1.26, Length = 2, Fade = 0.6, Near = 15, Reach = 160 },
    SecureWorldTail = { Id = "9116418035", Volume = 1.2, Start = 0.65, Length = 1.4, Fade = 0.6, Near = 15, Reach = 160 },
    ChaseLoop = { Id = "9043365842", Volume = 0.3, Group = "Music" },                                  -- a heartbeat under the battle drums

    -- ---------- the Heavenly Tribulation (TribulationController; picks from the Aura Sound Library, levels to measure in Play) ----------
    TribulationStorm = { Id = "9119806923", Volume = 1.1, Near = 40, Reach = 320, FadeIn = 2, FadeOut = 2 },     -- a deep pulsing rumble: the storm overhead
    TribulationGather = { Id = "9120032392", Volume = 2.2, Near = 40, Reach = 320, Length = 6 },                 -- thunder rolling in
    TribulationStrike = { Id = "9114246605", Volume = 2.4, Pitch = { 0.85, 1 }, Near = 25, Reach = 260, Max = 3, With = "TribulationBoom" }, -- the crack
    TribulationBoom = { Id = { "9113551995", "9113552058" }, Volume = 2.6, Pitch = { 0.8, 0.95 }, Near = 25, Reach = 260, Max = 3 },          -- and its boom
    TribulationArc = { Id = "9114236059", Volume = 0.8, Pitch = { 1.1, 1.3 }, Near = 15, Reach = 120, Length = 0.9, Max = 3 },               -- a ring charging

    -- ---------- strikes and movement ----------
    -- (Max: a flurry of blows from many players plays a few copies at once, not one per hit)
    PalmStrike = { Id = { "9125496394", "9119699577" }, Volume = 1.2, Pitch = { 1, 1.15 }, Reach = 90, Max = 3 },
    SwordSwing = { Id = { "9126014082", "9126013811", "9119700022" }, Volume = 1.3, Pitch = { 0.95, 1.1 }, Reach = 90, Max = 3 },
    -- the spear's own voice (November 11, 2026; it used the sword's swishes pitched down): a heavy whoosh for the thrust (its files
    -- open with a tenth of a second of quiet, skipped), a thick bamboo swish for the slash
    SpearThrust = { Id = { "9120729007", "9120729339" }, Volume = 0.54, Pitch = { 0.85, 0.95 }, Start = 0.07, Reach = 90, Max = 3 },
    SpearSwing = { Id = { "9125495638", "9125495498" }, Volume = 3.1, Pitch = { 0.8, 0.9 }, Reach = 90, Max = 3 },
    QiImpact = { Id = { "9113572426", "9113484814" }, Volume = 0.55, Pitch = { 0.9, 1.05 }, Near = 15, Reach = 150, Max = 4 },
    -- where a strike lands, by the kind of blow (CombatFx.hit; measured muted in Play, November 11, 2026: peaks 407 and 460, about 300 at
    -- pitch 0.8, 90, and 118, levelled to the swings' and QiImpact's 145 to 165): a blade's cut (a sword slicing through with a ring of
    -- metal), a spear's thrust (a blade struck on a metal rod), a fist (a boxer's thud under the burst of Qi), and the ring of a
    -- critical strike over any of them (an anvil's bright ding)
    BladeHit = { Id = { "9119746598", "9119746751" }, Volume = 0.37, Pitch = { 0.95, 1.08 }, Length = 0.6, Near = 15, Reach = 150, Max = 4 },
    SpearHit = { Id = { "9113449585", "9113449244", "9113449377" }, Volume = 0.55, Pitch = { 0.75, 0.85 }, Near = 15, Reach = 150, Max = 4 },
    PalmHit = { Id = { "9113565281", "9113576289" }, Volume = 1.0, Pitch = { 0.95, 1.08 }, Near = 15, Reach = 150, Max = 4, With = "QiImpact" },
    -- the weight under a heavy blow (a sword's finisher, a spear's thrust, a critical strike): the fist's thud, two octaves of body lower and cut short,
    -- played with the blow's own sound (CombatFx.landHit). A new layer from files already in the game (measured muted in Play, 2026-11-18: 291 and 264 at
    -- pitch 0.63 x 0.45 = 131 and 119, a layer under the blade's 183, the spear's 141 and the fist's 213)
    HeavyThump = { Id = { "9113565281", "9113576289" }, Volume = 0.45, Pitch = { 0.58, 0.68 }, Length = 0.4, Fade = 0.12, Near = 15, Reach = 150, Max = 2 },
    CritHit = { Id = "9113133466", Volume = 1.3, Pitch = { 1.0, 1.1 }, Near = 15, Reach = 150, Max = 2 },
    -- the combat forms' voices (2026-11-24, shared/FormRules; CombatFx.formVoice): layers from files already in the game, played WITH a strike's own swing so
    -- every form sounds like itself. FormAir: the quick forms (Gale, Swallow, Flurry), a thin high whistle of air; FormWeight: the heavy ones (Mountain, Tiger,
    -- Stone), a low body under the swing; the finishers: FormFinishAir a rush of wind that opens out, FormFinishWeight the ground taking the blow. Levelled by measured
    -- loudness in Play (peak x volume; the swings are 168 to 208): FormAir about 100, FormWeight about 105, the finishers about 130 and 200. NOT judged by ear.
    FormAir = { Id = { "9125495638", "9125495498" }, Volume = 1.9, Pitch = { 1.55, 1.75 }, Length = 0.3, Fade = 0.1, Reach = 90, Max = 2 },
    FormWeight = { Id = { "9113565281", "9113576289" }, Volume = 0.35, Pitch = { 0.5, 0.6 }, Length = 0.5, Fade = 0.18, Reach = 90, Max = 2 },
    FormFinishAir = { Id = "9116416120", Volume = 0.52, Start = 1.5, Length = 1.1, Fade = 0.4, Pitch = { 1.05, 1.15 }, Reach = 100, Max = 2 },
    FormFinishWeight = { Id = { "9113565281", "9113576289" }, Volume = 0.65, Pitch = { 0.42, 0.5 }, Length = 0.8, Fade = 0.3, Reach = 100, Max = 2 },
    Knockback = { Id = "9113502359", Volume = 1, Pitch = { 0.92, 1.05 }, Gap = 0.15, Key = true },     -- the player is struck (Body Hits 4: 201)
    Dash = { Id = "9119467121", Volume = 1.8, Pitch = { 1, 1.1 }, Start = 0.3, Reach = 90, Max = 3 },
    Leap = { Id = "9125496163", Volume = 1.8, Pitch = { 1, 1.15 }, Reach = 90, Max = 3 },
    Land = { Id = "9113470014", Volume = 0.25, Pitch = { 1.05, 1.15 }, Start = 0.5, Length = 0.3, Reach = 70, Max = 3 },
    GlideLoop = { Id = "9113286969", Volume = 2, Start = 1.7, Reach = 80 },
    FlightLoop = { Id = "9125742262", Volume = 0.35, Reach = 100 },
    SwordTakeoff = { Id = "9116689911", Volume = 1.2, Pitch = 1.1, Reach = 100, With = "TakeoffRush" }, -- the blade rings, the air rushes
    TakeoffRush = { Id = "9116416120", Volume = 0.7, Start = 1.5, Length = 1.2, Reach = 100 },

    -- ---------- cultivation ----------
    CultivateLoop = { Id = "9116389876", Volume = 0.15, Near = 6, Reach = 40, FadeIn = 1.5 },             -- a deep, slowly surging hum
    -- sitting down to cultivate: a soft humming swell (Magic Glow Short Pulsing Bursts 9: 240 x 0.5 = 120); rising from it, the
    -- shimmer falls away (97 x 0.9)
    CultivateStart = { Id = "9116393976", Volume = 0.5, Near = 8, Reach = 50 },
    CultivateStop = { Id = "9116418035", Volume = 0.9, Start = 0.7, Length = 1, Fade = 0.4, Near = 8, Reach = 50 },
    -- the Qi flowing in, for the cultivator alone: a tiny high ping (150 x 0.28 = 42), on a note of a major pentatonic picked at
    -- random, at most every 2.3 s however fast the Qi ticks, so it twinkles instead of ticking
    QiTick = { Id = "9126076030", Volume = 0.28, Notes = { 1, 1.125, 1.25, 1.5, 1.667, 2 }, Gap = 2.3, Max = 1 },
    -- the breakthrough is ready: a bright bell-tone ding (91 x 1.8 = 164)
    BreakthroughReady = { Id = "9126073011", Volume = 1.8, Group = "Interface", Gap = 1, Defer = true },
    -- the breakthrough as others near it hear it, by kind (BreakthroughStyles.gradeOf), with its visual: a step, a realm's fifth level,
    -- a new realm (after the Tribulation, an angelic vocal over it). No gong. (The breaker's own are the Bt entries below.)
    BreakthroughStep = { Id = "9116385087", Volume = 0.6, Near = 20, Reach = 200, With = { { "BreakthroughHarpShort", 0.05 } } },
    BreakthroughHarpShort = { Id = "1840525370", Volume = 1.8, Start = 0.3, Pitch = 1.26, Length = 1.3, Fade = 0.4, Near = 20, Reach = 200 },
    BreakthroughMilestone = { Id = "9116384485", Volume = 0.55, Start = 0.1, Length = 2.4, Fade = 0.6, Near = 20, Reach = 200,
        With = { { "BreakthroughHarp", 0.05 }, { "BreakthroughTail", 0.7 } } },
    BreakthroughRealm = { Id = "9116384485", Volume = 0.65, Start = 0.1, Length = 2.6, Fade = 0.6, Near = 25, Reach = 220, Key = true,
        With = { { "BreakthroughHarp", 0.05 }, { "BreakthroughChoir", 0 }, { "BreakthroughTail", 0.9 } } },
    BreakthroughHarp = { Id = "1840525370", Volume = 2, Start = 0.3, Pitch = 1.26, Length = 2, Fade = 0.6, Near = 20, Reach = 220 },
    BreakthroughTail = { Id = "9116418035", Volume = 1.7, Start = 0.65, Length = 1.8, Fade = 0.6, Near = 20, Reach = 220 },
    -- APM "Heavenly sting": an angelic vocal reveal, 269 at its peak 1 s in (x 0.7 = 188), cut at 3.6 s
    BreakthroughChoir = { Id = "1839901317", Volume = 0.7, Length = 3.6, Fade = 0.8, Near = 25, Reach = 220 },
    -- the breakthrough as the one breaking through hears it (BreakthroughShow; flat, the interface's group; every file is one the game
    -- already uses, at the level it is used at, layered anew): a drawn breath (the hatch's hush), a humming swell whose pitch the
    -- show raises through the gather, a low thud for each beat of the realm's own signature, and the break by grade: a step is the
    -- glowing thud and a short harp; a fifth level adds the stinger, a deep thud, the harp, the ding and the tail; a new realm the
    -- air rush, the choir and the fairy dust; the apex the deeper impact under all of it
    BtBreath = { Id = "9118158081", Volume = 1.4, Group = "Interface", Length = 1.1, Fade = 0.25 },
    BtRise = { Id = "9116393976", Volume = 0.6, Group = "Interface" },
    BtBeat = { Id = "9116385087", Volume = 0.5, Pitch = 0.6, Group = "Interface", Gap = 0.1, Max = 3 },
    BtThump = { Id = "9113480917", Volume = 0.85, Pitch = 0.55, Group = "Interface" },
    BtBreakStep = { Id = "9116385087", Volume = 0.7, Group = "Interface", Key = true, With = { { "RevealHarpShort", 0.05 }, { "RewardTail", 0.3 } } },
    BtBreakMilestone = { Id = "9116384485", Volume = 0.62, Start = 0.1, Length = 2.5, Fade = 0.6, Group = "Interface", Key = true, Moment = 3,
        With = { { "BtThump", 0 }, { "RevealHarp", 0.05 }, { "RevealTail", 0.7 }, { "RevealDing", 0.9 } } },
    BtBreakRealm = { Id = "9116384485", Volume = 0.65, Start = 0.1, Length = 2.6, Fade = 0.6, Group = "Interface", Key = true, Moment = 4,
        With = { { "BtThump", 0 }, { "HatchPillar", 0.05 }, { "RevealHarp", 0.1 }, { "RevealChoir", 0 }, { "RevealDing", 0.8 }, { "RevealTail", 0.9 },
            { "RevealDust", 1 } } },
    BtBreakApex = { Id = "9116384485", Volume = 0.65, Start = 0.1, Length = 2.6, Fade = 0.6, Group = "Interface", Key = true, Moment = 5,
        With = { { "RevealDeep", 0 }, { "BtThump", 0 }, { "HatchPillar", 0.05 }, { "RevealHarp", 0.1 }, { "RevealChoir", 0 }, { "RevealDing", 0.8 },
            { "RevealTail", 0.9 }, { "RevealDust", 1 }, { "RevealChoir", 1.6 } } },

    -- ---------- hatching ----------
    -- the build: an ice-like crackle of the shell (Ice Crackle Large Block Cracks 1: 478 x 0.3 = 143), and for the hatcher a
    -- shimmering swell timed so its burst lands on the crack (Angel Sparkle 5 swells for 2.17 s: 207 x 0.7 = 145)
    EggRumble = { Id = "9114858583", Volume = 0.3, Pitch = 1.1, Start = 0.2, Length = 2, Fade = 0.4, Near = 15, Reach = 90 },
    HatchSwell = { Id = "9113122880", Volume = 0.7, Length = 2.45, Fade = 0.3, Key = true, Moment = 2.4 },
    -- the crack: a real eggshell's crunch (Crack Egg Crunchy 11: 121 x 1.3 = 157) and glass breaking under it (80 x 1.8 = 144)
    EggCrack = { Id = "9113959343", Volume = 1.3, Start = 0.12, Near = 15, Reach = 90, Key = true, With = "CrackShatter" },
    CrackShatter = { Id = "9114591872", Volume = 1.8, Length = 0.7, Near = 15, Reach = 90 },
    -- the reveal, a sound of its own for each rarity, each adding to the one below (HatchCeremony's ladder; every file is one the game
    -- already uses, at the level it's used at): Common, a sparkling chime; Uncommon, a ping on it; Rare, a glowing thud under it;
    -- Epic, a short rising harp and a glassy tone too; Legendary, the reward stinger's impact, full harp and shimmer; Mythical, a
    -- bright ding and fairy dust on that; Secret, the deeper impact and the angelic vocal; Divine, both impacts, the vocal, the ding
    -- and the dust
    HatchReveal = { Id = "9125635430", Volume = 0.5, Group = "Interface", Moment = 1.5 },                               -- 275 x 0.5 = 137
    HatchRevealUncommon = { Id = "9125635430", Volume = 0.5, Group = "Interface", Moment = 1.5, With = { { "RevealPing", 0.12 } } },
    RevealPing = { Id = "9126076118", Volume = 0.45, Pitch = 1.25, Group = "Interface" },                                -- SummonPing's
    HatchRevealRare = { Id = "9116385087", Volume = 0.6, Group = "Interface", With = "HatchReveal" },
    HatchRevealEpic = { Id = "9116385087", Volume = 0.65, Group = "Interface", Duck = { 0.5, 2.5 }, Moment = 2,
        With = { "HatchReveal", { "RevealHarpShort", 0.05 }, { "RevealGlass", 0.35 } } },
    RevealHarpShort = { Id = "1840525370", Volume = 1.8, Start = 0.3, Pitch = 1.26, Length = 1.3, Fade = 0.4, Group = "Interface" },
    RevealGlass = { Id = "9126073644", Volume = 0.8, Pitch = 1.12, Group = "Interface" },                               -- FuseTone's
    HatchRevealLegendary = { Id = "9116384485", Volume = 0.6, Start = 0.1, Length = 2.4, Fade = 0.6, Group = "Interface", Key = true,
        Duck = { 0.35, 3.5 }, Moment = 3, With = { { "RevealHarp", 0.05 }, { "HatchReveal", 0.1 }, { "RevealTail", 0.8 } } },
    HatchRevealMythical = { Id = "9116384485", Volume = 0.62, Start = 0.1, Length = 2.5, Fade = 0.6, Group = "Interface", Key = true,
        Duck = { 0.3, 4 }, Moment = 3.2,
        With = { { "RevealHarp", 0.05 }, { "HatchReveal", 0.1 }, { "RevealDing", 0.8 }, { "RevealTail", 0.85 }, { "RevealDust", 0.9 } } },
    HatchRevealSecret = { Id = "9116384473", Volume = 0.55, Start = 0.2, Length = 2.4, Fade = 0.6, Group = "Interface", Key = true,
        Duck = { 0.25, 4.5 }, Moment = 3.5, With = { { "RevealHarp", 0.05 }, { "HatchReveal", 0.1 }, { "RevealChoir", 0 }, { "RevealTail", 0.9 } } },
    HatchRevealDivine = { Id = "9116384485", Volume = 0.65, Start = 0.1, Length = 2.6, Fade = 0.6, Group = "Interface", Key = true,
        Duck = { 0.25, 4.5 }, Moment = 3.5,
        With = { { "RevealDeep", 0 }, { "RevealHarp", 0.05 }, { "HatchReveal", 0.1 }, { "RevealChoir", 0 }, { "RevealDing", 0.8 },
            { "RevealTail", 0.9 }, { "RevealDust", 1 } } },
    RevealHarp = { Id = "1840525370", Volume = 2, Start = 0.3, Pitch = 1.26, Length = 2, Fade = 0.6, Group = "Interface" },
    RevealTail = { Id = "9116418035", Volume = 1.7, Start = 0.65, Length = 1.8, Fade = 0.6, Group = "Interface" },
    RevealChoir = { Id = "1839901317", Volume = 0.75, Length = 4, Fade = 1, Group = "Interface" },
    RevealDing = { Id = "9126072453", Volume = 0.75, Start = 0.25, Group = "Interface" },                              -- RewardDing's
    RevealDust = { Id = "9114369623", Volume = 1.1, Start = 0.2, Length = 2, Fade = 0.6, Group = "Interface" },        -- PremiumDust's
    RevealDeep = { Id = "9116384473", Volume = 0.45, Start = 0.2, Length = 2.2, Fade = 0.6, Group = "Interface" },     -- PremiumPurchase's
    -- the held breath before a grand one breaks (Legendary up): a humming swell (TakeReadySwell's, 240 x 0.6); a Secret's and a
    -- Divine's drawn breath, the reversed whoosh (StealSting's); the Divine's pillar coming down, the air rush (TakeoffRush's)
    HatchCharge = { Id = "9116393976", Volume = 0.6, Group = "Interface", Length = 1.4, Fade = 0.3 },
    HatchHush = { Id = "9118158081", Volume = 1.6, Group = "Interface", Length = 0.9, Fade = 0.15 },
    HatchPillar = { Id = "9116416120", Volume = 0.8, Start = 1.5, Length = 1.4, Fade = 0.4, Group = "Interface" },
    -- the size stamps: Large, a bright thud and a glassy tone; Giant, after its trembling beat (EggRumble), a deep slam
    SizeLarge = { Id = "9116385087", Volume = 0.55, Pitch = 1.12, Group = "Interface", With = { { "SizeTone", 0.05 } } },
    SizeTone = { Id = "9126073644", Volume = 0.9, Group = "Interface" },
    SizeGiant = { Id = "9116384485", Volume = 0.7, Start = 0.1, Pitch = 0.82, Length = 2, Fade = 0.6, Group = "Interface", Key = true,
        Duck = { 0.4, 2.5 }, Moment = 2.2, With = { { "SizeGiantThud", 0 }, { "RevealTail", 0.4 } } },
    SizeGiantThud = { Id = "9116385087", Volume = 0.6, Pitch = 0.7, Group = "Interface" },
    -- a big one landing on the card: a heavy body thud (EggDrop's, 213 x 0.7); a Small one: a light poof (PetSummon's) and a high ping
    SizeLand = { Id = "9113480917", Volume = 0.7, Pitch = 0.8, Group = "Interface" },
    SizeSmall = { Id = "9116405867", Volume = 0.5, Pitch = 1.35, Group = "Interface", With = { { "SizeSmallPing", 0.06 } } },
    SizeSmallPing = { Id = "9126076118", Volume = 0.45, Notes = { 1.5, 1.68 }, Group = "Interface" },
    -- the mutation stamps (2026-11-17; a Colossal's is SizeGiant pitched down): a glassy tone over a bright thud; Rainbow and up, the
    -- choir and a ding over the reward stinger (the sounds already in the game, layered anew)
    MutationStamp = { Id = "9126073644", Volume = 0.85, Pitch = 1.25, Group = "Interface", With = { { "SizeLarge", 0 }, { "RevealDing", 0.1 } } },
    MutationGrand = { Id = "9116384485", Volume = 0.6, Start = 0.1, Pitch = 1.1, Length = 2.2, Fade = 0.6, Group = "Interface", Key = true,
        Duck = { 0.4, 2.5 }, Moment = 2, With = { { "RevealChoir", 0 }, { "RevealDing", 0.15 }, { "RevealDust", 0.3 } } },
    -- another player's hatch at the Sanctum, as anyone near hears it: the crack and a chime, quieter (a grand one with the thud)
    HatchNearby = { Id = "9113959343", Volume = 1, Start = 0.12, Near = 12, Reach = 80, With = { "CrackShatterNear", { "HatchNearbyChime", 0.05 } } },
    CrackShatterNear = { Id = "9114591872", Volume = 1.3, Length = 0.7, Near = 12, Reach = 80 },
    HatchNearbyChime = { Id = "9125635430", Volume = 0.4, Near = 12, Reach = 80 },
    HatchNearbyGrand = { Id = "9116384485", Volume = 0.35, Start = 0.1, Length = 2, Fade = 0.6, Near = 15, Reach = 140, With = "HatchNearby" },

    -- ---------- pets ----------
    -- a pet appears at its owner's side (equipped), heard near it: a punchy magic poof and a sparkle ping (178 x 0.6 = 107);
    -- it leaves with a softer, wheezy poof (104 x 0.8 = 83)
    PetSummon = { Id = "9116405867", Volume = 0.6, Pitch = { 1.05, 1.2 }, Near = 10, Reach = 60, Max = 3, With = { { "SummonPing", 0.05 } } },
    SummonPing = { Id = "9126076118", Volume = 0.4, Notes = { 1, 1.125, 1.25 }, Near = 10, Reach = 60, Max = 3 },
    PetDismiss = { Id = "9116406643", Volume = 0.8, Pitch = { 1.1, 1.2 }, Near = 10, Reach = 60, Max = 3 },
    -- a Giant walker's footfall, low and soft (StealThud's body thud, slowed): heard near it, never loud; and its landing when its
    -- owner comes down from the air (SizeLand's thud, deeper)
    GiantStep = { Id = "9116385087", Volume = 0.3, Pitch = { 0.5, 0.6 }, Near = 14, Reach = 70, Gap = 0.12, Max = 3 },
    GiantLand = { Id = "9113480917", Volume = 0.55, Pitch = { 0.55, 0.62 }, Near = 16, Reach = 90, Gap = 0.3, Max = 2 },
    -- a fusion: a humming swell (240 x 0.8 = 192), a glassy tone and the shimmer falling away
    PetFuse = { Id = "9116393976", Volume = 0.8, Group = "Interface", With = { { "FuseTone", 0.28 }, { "FuseTail", 0.45 } } },
    FuseTone = { Id = "9126073644", Volume = 1, Pitch = 1.12, Group = "Interface" },
    FuseTail = { Id = "9116418035", Volume = 1.4, Start = 0.65, Length = 1.2, Fade = 0.4, Group = "Interface" },
    -- the pen: a beast let in (a poof and a ping), and the pen growing, heard by anyone near it: stone set on stone, a short
    -- rising harp and the shimmer (Rock Hits Rock 10: 218 x 0.7 = 153)
    PenPlace = { Id = "9116405618", Volume = 0.55, Pitch = { 1.05, 1.15 }, Group = "Interface", With = { { "SummonPing", 0.05 } } },
    PenUpgrade = { Id = "9118609285", Volume = 0.7, Length = 0.6, Near = 20, Reach = 140,
        With = { { "PenStone", 0.1 }, { "PenHarp", 0.15 }, { "PenTail", 0.6 } } },
    PenStone = { Id = "9118654334", Volume = 0.5, Start = 0.3, Near = 20, Reach = 140 },
    PenHarp = { Id = "1840525370", Volume = 1.6, Start = 0.3, Pitch = 1.26, Length = 1.5, Fade = 0.5, Near = 20, Reach = 140 },
    PenTail = { Id = "9116418035", Volume = 1.3, Start = 0.65, Length = 1.4, Fade = 0.5, Near = 20, Reach = 140 },

    -- ---------- rewards and purchases (flat: the player's own) ----------
    -- a reward claimed (daily, codes, the Codex, Qi earned away): a short rising harp, a soft glassy bell-tone and the shimmer falling
    -- away. The owner, 2026-11-18, on the old one (a coin pour and a hard ding): "ABSOLUTELY TERRIBLE", so the coins are gone; the
    -- harp and the glassy tone are sounds the game already uses (RevealHarp, SizeTone), set lower. Not heard by the one who wrote it:
    -- change these numbers if it is still wrong.
    RewardClaim = { Id = "1840525370", Volume = 1.3, Start = 0.3, Pitch = 1.12, Length = 1.2, Fade = 0.4, Group = "Interface", Duck = { 0.7, 1.5 },
        Defer = true, With = { { "RewardDing", 0.28 }, { "RewardTail", 0.5 } } },                       -- harp 90 x 1.3 = 117
    RewardDing = { Id = "9126073644", Volume = 0.95, Pitch = 1.33, Group = "Interface" },               -- glassy tone 128 x 0.95 = 122
    RewardTail = { Id = "9116418035", Volume = 0.9, Start = 0.7, Length = 1.4, Fade = 0.5, Group = "Interface" },
    -- a quest step done: the short rising harp and the ding at its top
    QuestComplete = { Id = "1840525370", Volume = 1.9, Start = 0.3, Pitch = 1.26, Length = 1.5, Fade = 0.4, Group = "Interface", Defer = true,
        With = { { "RewardDing", 0.7 } } },                                                               -- 90 x 1.9 = 171
    -- a relic attuned: twinkling fairy dust over a soft glowing thud (110 x 1.1 = 121)
    Attune = { Id = "9114369623", Volume = 1.1, Group = "Interface", Length = 2.5, Fade = 0.5, With = "AttuneThud" },
    AttuneThud = { Id = "9116385087", Volume = 0.45, Pitch = 1.05, Group = "Interface" },
    -- a notice (a title earned, the guardian's egg can be taken)
    Notify = { Id = "9126073318", Volume = 1.6, Group = "Interface", Gap = 0.3, Defer = true },                     -- 100 x 1.6 = 160
    TakeReady = { Id = "9126073644", Volume = 1.1, Group = "Interface", Gap = 1, Defer = true, With = "TakeReadySwell" }, -- glassy tone 141 x 1.1 = 155
    TakeReadySwell = { Id = "9116393976", Volume = 0.45, Group = "Interface" },
    -- spending at a shop or the Merchant: coins and a small ding; selling: coins coming in and the reward ding
    Purchase = { Id = "9125445146", Volume = 0.9, Group = "Interface", Gap = 0.15, With = { { "PurchaseTick", 0.08 } } },
    PurchaseTick = { Id = "9126073001", Volume = 1.8, Group = "Interface" },                           -- 72 x 1.8 = 130
    Sell = { Id = "9113849011", Volume = 0.85, Pitch = 1.05, Group = "Interface", Gap = 0.15, With = { { "RewardDing", 0.1 } } }, -- 161 x 0.85 = 137
    -- a blade forged: the anvil rings, the blade shings, its element shimmers in
    Forge = { Id = "9113133597", Volume = 1.1, Group = "Interface", With = { { "ForgeShing", 0.18 }, { "RewardTail", 0.35 } } }, -- 154 x 1.1 = 170
    ForgeShing = { Id = "9119076604", Volume = 0.95, Group = "Interface" },                            -- 160 x 0.95 = 152
    WeaponEquip = { Id = "9119076604", Volume = 0.7, Pitch = { 1.08, 1.15 }, Group = "Interface", Gap = 0.2 }, -- a blade taken up: its shing
    -- a Robux pass or the Exclusive Egg bought: the reward stinger's family, a deeper impact and fairy dust
    PremiumPurchase = { Id = "9116384473", Volume = 0.55, Start = 0.2, Length = 2.2, Fade = 0.6, Group = "Interface", Key = true,
        Duck = { 0.4, 3 }, Moment = 2.5, With = { { "RevealHarp", 0.05 }, { "RewardDing", 0.75 }, { "PremiumDust", 0.9 } } }, -- 407 x 0.55 = 224
    PremiumDust = { Id = "9114369623", Volume = 1.1, Start = 0.2, Length = 2, Fade = 0.6, Group = "Interface" },

    -- ---------- the Spin Wheel (SpinController; the wheel's own sounds come from it, heard by anyone near) ----------
    -- the push: an air rush as it starts (the takeoff's rush, 0.6); a tick each time a peg passes the pointer (the hatch reel's
    -- card, sounded at the pointer, Max 3 so a fast run is a rattle, not a pile-up); a soft glowing thud as it stops
    WheelStart = { Id = "9116416120", Volume = 0.6, Start = 1.5, Length = 1, Fade = 0.3, Near = 15, Reach = 90 },
    WheelTick = { Id = "9119717971", Volume = 1.5, Pitch = { 0.96, 1.04 }, Near = 12, Reach = 70, Gap = 0.03, Max = 3, Length = 0.12, Fade = 0.05 },
    WheelStop = { Id = "9116385087", Volume = 0.45, Pitch = 1.15, Near = 15, Reach = 90 },
    -- what the spinner won, flat, by its size: a small one is RewardClaim; a big one (the large stones, the long Qi, an egg) the
    -- glowing thud under the short rising harp and the ding; the jackpot the big-moment family with the angelic vocal
    SpinWinBig = { Id = "9116385087", Volume = 0.6, Group = "Interface", Duck = { 0.5, 2.5 }, Moment = 2,
        With = { { "RevealHarp", 0.05 }, { "RewardDing", 0.7 }, { "RewardTail", 0.8 } } },
    SpinJackpot = { Id = "9116384485", Volume = 0.65, Start = 0.1, Length = 2.6, Fade = 0.6, Group = "Interface", Key = true,
        Duck = { 0.25, 4.5 }, Moment = 3.5, With = { { "RevealHarp", 0.05 }, { "RevealChoir", 0 }, { "RewardDing", 0.8 }, { "PremiumDust", 0.9 } } },
    -- the jackpot as anyone near the wheel hears it
    SpinJackpotWorld = { Id = "9116384485", Volume = 0.4, Start = 0.1, Length = 2, Fade = 0.6, Near = 15, Reach = 160,
        With = { { "SecureWorldHarp", 0.08 }, { "SecureWorldTail", 0.9 } } },

    -- ---------- the Wandering Merchant (everyone: the whole server hears his announcement) ----------
    MerchantArrive = { Id = "9114134470", Volume = 0.75, Group = "Interface", Length = 2.6, Fade = 0.5 },  -- a shop door's chime, 206 x 0.75
    MerchantLeave = { Id = "9114134274", Volume = 0.6, Pitch = 0.94, Group = "Interface", Length = 2.8, Fade = 0.6 }, -- 179 x 0.6

    -- ---------- the interface ----------
    -- clean, short and quiet: a toggle-switch click for buttons (158 x 0.55 = 87), a dull pop for tabs and pages (93 x 0.95),
    -- a soft sparkle tone opening a window (83 x 1.25), the same lower and softer closing it, and a fuzzy low tone refusing
    Click = { Id = "9119717529", Volume = 0.55, Pitch = { 1.05, 1.15 }, Group = "Interface", Gap = 0.06, Max = 2 },
    Tab = { Id = "9119717950", Volume = 0.95, Pitch = { 1, 1.08 }, Group = "Interface", Gap = 0.06, Max = 2 },
    ReelTick = { Id = "9119717971", Volume = 1.1, Group = "Interface", Gap = 0.05, Max = 4, Length = 0.12, Fade = 0.05 }, -- the hatch reel's cards
    Open = { Id = "9119834248", Volume = 1.25, Pitch = { 0.98, 1.03 }, Group = "Interface", Gap = 0.1 },
    Close = { Id = "9119834602", Volume = 0.9, Pitch = 0.82, Group = "Interface", Gap = 0.1 },
    Error = { Id = "9126052471", Volume = 2.1, Pitch = 0.95, Group = "Interface", Length = 0.5, Fade = 0.15, Gap = 0.25, Max = 1 }, -- 55 x 2.1 = 115

    -- ---------- each island's bed ----------
    AmbYggdrasil = { Id = "9116971178", Volume = 1.6, Group = "Ambience" },    -- birds in the morning forest
    AmbJade = { Id = "9119646409", Volume = 0.35, Group = "Ambience" },        -- a stream through the grove
    AmbEmber = { Id = "9112823197", Volume = 0.13, Group = "Ambience" },       -- lava bubbling and rumbling
    AmbMoon = { Id = "9117114457", Volume = 1.3, Group = "Ambience" },         -- night insects
    AmbAbyss = { Id = "9114625552", Volume = 0.24, Group = "Ambience" },       -- an eerie wind
    -- the Blossom Sanctuary (2026-11-16): Pro Sound Effects' "Leaves Rustle Wind Blowing Through Trees 1" as its bed (a few birds in it);
    -- the pond's water near it (the grove's stream, low), and a koi's leap: "Small Splash Shallow Water Fountain Pool 1" (SanctuaryLife)
    -- (measured 2026-11-16: wind 5.8 x 1.8 = 10.4, a little under the hub's birds, 8 x 1.6; the pond 36.7 x 0.22 = 8 beside it)
    AmbSanctuary = { Id = "9116258071", Volume = 1.8, Group = "Ambience" },
    PondWater = { Id = "9119646409", Volume = 0.22, Group = "Ambience", Near = 30, Reach = 110 },
    KoiSplash = { Id = "9119293555", Volume = 0.45, Pitch = { 0.95, 1.15 }, Near = 12, Reach = 70, Max = 2 },
    -- the shrine's wind chimes: a few seconds of Pro Sound Effects' "Wind Chimes 3" (41 s, glass and ceramic) now and then (SanctuaryLife)
    ShrineChime = { Id = "9120750073", Volume = 0.25, Start = 4, Length = 4.5, Fade = 1.2, Near = 18, Reach = 110, Max = 1, Gap = 10 },
    -- the weather (WeatherConfig, AudioController): Pro Sound Effects' "Rain On Water 1", a 61 s outdoor loop
    AmbRain = { Id = "9112854469", Volume = 0.4, Group = "Ambience", FadeIn = 6, FadeOut = 6 }, -- 39 x 0.4: a little over the birds (9 x 1.6)

    -- ---------- music (APM) ----------
    MusicHub = { Id = "1847656215", Volume = 0.4, Group = "Music", FadeIn = 2.5 },     -- Forests Of The Orient
    MusicJade = { Id = "1840356481", Volume = 1.3, Group = "Music", FadeIn = 2.5 },    -- Ethnic Lullaby: bamboo flute
    MusicEmber = { Id = "9041879299", Volume = 1.3, Group = "Music", FadeIn = 2.5 },   -- Territory Conquest: tense drums
    MusicMoon = { Id = "1837129588", Volume = 0.16, Group = "Music", FadeIn = 2.5 },   -- Orient At Twilight
    MusicAbyss = { Id = "9042642782", Volume = 0.5, Group = "Music", FadeIn = 2.5 },   -- Alien Nation: dark percussion
    MusicBattle = { Id = "1840898686", Volume = 0.35, Group = "Music", FadeIn = 1.5 }, -- Kodo Ceremonial: taiko from the first beat
}

-- every animated pet's voice and special (PetSounds)
for name, spec in PetSounds.Entries do
    catalog[name] = spec
end

return catalog
