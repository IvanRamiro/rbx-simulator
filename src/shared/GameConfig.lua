local GameConfig = {

    StartingQi = 0,

    CultivationQiReward = 10,
    CultivationInterval = 1,
    CultivationToggleCooldown = 0.5,
    CultivationKeybind = Enum.KeyCode.E,

    TrainingStation = {
        DisplayName = "Qi Spring",
        QiBonusPercent = 50,
        Radius = 10,
    },

    -- Qinggong: leap again in mid-air (once per air leap) and hold jump while falling to glide.
    -- The air leaps reach the high places on the islands (the Elder Jade Tree's crown, the Void
    -- Shard's climb); the islands themselves are joined by bridges.
    Qinggong = {
        LeapUpSpeed = 52,
        LeapForwardSpeed = 34,
        LeapCooldown = 0.2,
        GlideFallSpeed = 14,
        GlideSpeedFactor = 1.1, -- relative to run speed
        -- Stamina fuels only dashes and sword flight; it refills after RegenDelay, faster on the ground.
        Stamina = { RegenGround = 32, RegenAir = 14, RegenDelay = 0.6 },
        Dash = { Cost = 25, Duration = 0.2, Cooldown = 0.45 },
        -- Per rank. DashSpeed is studs/s while dashing; FlightSpeed is 0 before SwordFlight unlocks.
        Levels = {
            { RankId = "QiInitiate", AirLeaps = 1, RunSpeed = 22, Stamina = 100, DashSpeed = 70, FlightSpeed = 0 },
            { RankId = "QiGatherer", AirLeaps = 2, RunSpeed = 24, Stamina = 110, DashSpeed = 74, FlightSpeed = 0 },
            { RankId = "QiAwakener", AirLeaps = 3, RunSpeed = 26, Stamina = 120, DashSpeed = 78, FlightSpeed = 0 },
            { RankId = "FoundationInitiate", AirLeaps = 4, RunSpeed = 28, Stamina = 135, DashSpeed = 82, FlightSpeed = 48 },
            { RankId = "PerfectFoundation", AirLeaps = 5, RunSpeed = 30, Stamina = 150, DashSpeed = 86, FlightSpeed = 56 },
            { RankId = "DivineInitiate", AirLeaps = 6, RunSpeed = 32, Stamina = 170, DashSpeed = 92, FlightSpeed = 64 },
            { RankId = "VoidWalker", AirLeaps = 7, RunSpeed = 34, Stamina = 190, DashSpeed = 100, FlightSpeed = 72 },
        },
    },

    -- Combat (src/server/Combat/CombatService). A player strikes with their equipped weapon
    -- (WeaponKinds, WeaponTiers below), or the Qi Palm with none. Damage grows by RankPowerStep of the
    -- base per rank above the first. A strike hits the nearest target within Arc degrees of facing
    -- whose body is within Range studs.
    Combat = {
        TargetTag = "CombatTarget",
        RankPowerStep = 0.12,
        Palm = { Damage = 10, Range = 9, Cooldown = 0.45, Arc = 75 },
    },

    -- Weapons (src/server/Shop; the Blacksmith on Yggdrasil): a sword and a spear for every realm,
    -- sold from that realm on for Spirit Stones (shared/Shop.lua names them Sword<tier>, Spear<tier>).
    -- A strike's damage is the tier's Damage times the kind's DamageScale times the rank's power
    -- (Combat.damageOf). The sword strikes fast and wide; the spear slower, farther and harder, for
    -- the same damage over time. With none equipped a player strikes with the Qi Palm (Combat.Palm).
    WeaponKinds = {
        Sword = { Range = 12, Arc = 80, Cooldown = 0.55, DamageScale = 1 },
        Spear = { Range = 18, Arc = 35, Cooldown = 0.85, DamageScale = 0.85 / 0.55 },
    },
    WeaponTiers = { -- one per realm, in the order of Ranks' realms; Price in Spirit Stones
        { Realm = "Qi Awakening", Damage = 16, Price = 60, Sword = "Reedwhisper Sword", Spear = "Bamboo Thorn Spear" },
        { Realm = "Qi Foundation", Damage = 21, Price = 160, Sword = "Jadevein Sword", Spear = "Jade Crane Spear" },
        { Realm = "Spirit Core", Damage = 26, Price = 400, Sword = "Coreflame Sword", Spear = "Ember Fang Spear" },
        { Realm = "Spirit Soul", Damage = 30, Price = 1050, Sword = "Soulmirror Sword", Spear = "Moonpiercer Spear" },
        { Realm = "Ascendant Realm", Damage = 35, Price = 2700, Sword = "Skyrise Sword", Spear = "Cloudspine Spear" },
        { Realm = "Immortal Realm", Damage = 40, Price = 7100, Sword = "Lotusfall Sword", Spear = "Crane Feather Spear" },
        { Realm = "Divine Realm", Damage = 45, Price = 18500, Sword = "Thunderjudge Sword", Spear = "Thunderhowl Spear" },
        { Realm = "Cosmic Realm", Damage = 50, Price = 48000, Sword = "Starriver Sword", Spear = "Comet Tail Spear" },
        { Realm = "Void Realm", Damage = 54, Price = 125000, Sword = "Voidsilence Sword", Spear = "Abyss Fang Spear" },
        { Realm = "Heavenly Dao", Damage = 59, Price = 325000, Sword = "Dao Heart Sword", Spear = "Heaven Pillar Spear" },
        { Realm = "Primordial Realm", Damage = 64, Price = 850000, Sword = "Chaos Origin Sword", Spear = "Primeval Dragon Spear" },
        { Realm = "Eternal Transcendence", Damage = 69, Price = 2200000, Sword = "Eternity Sword", Spear = "Eternal Sun Spear" },
    },
    StarterWeapon = "Sword1", -- every player's first weapon, given when they own none
    MaxOwnedWeapons = 30,

    -- Spirit Stones: the currency of the Blacksmith and Buy & Sell (Qi is never spent: ranks are
    -- reached by total Qi). Earned by selling pets and weapons, securing guardians' eggs
    -- (Guardians.<Id>.SecureStones) and a relic's first attunement.
    SpiritStones = {
        -- a pet's worth: its rarity's value times RealmFactor per realm of its egg's required rank
        PetValue = { Common = 6, Uncommon = 12, Rare = 25, Epic = 50, Legendary = 110, Mythical = 250, Secret = 600 },
        RealmFactor = 2.6, -- as weapon prices climb
        WeaponRefund = 0.4, -- the share of its price a weapon sells back for
        RelicShare = 0.2, -- a relic's first attunement pays this share of its Qi reward in stones
        Max = 1e12,
    },

    -- Guardians (src/server/Guardians/GuardianService; design doc section 7). While a guardian
    -- stands, its island's stands hatch only eggs taken from it: a thief earns the best of Eggs
    -- their rank opens, secured in the SafeZone. Positions are island-local studs. Egg positions
    -- are in the guardian's frame (front toward -Z): Under where it keeps the egg, Offered where it
    -- sets it down when weakened (if it holds it out of reach).
    -- Attack kinds: Sweep strikes in front (Range, Arc); Wave rolls along the ground to Radius (all
    -- round, or within Arc) and a jump clears it; Pounce leaps onto the thief (enraged only).
    GuardianTag = "Guardian",
    Guardians = {
        StoneLion = {
            DisplayName = "Awakened Stone Lion",
            Island = "Yggdrasil",
            Lair = Vector3.new(128, 0.4, -62),
            Facing = Vector3.new(0, 0.4, 0), -- toward the World Tree
            Eggs = { "BeginnerQiEgg", "SpiritBreezeEgg", "ElementalCoreEgg" },
            SafeZone = { Centre = Vector3.new(170, -1.5, 6), Radius = 15, Name = "Egg Garden" },
            SecureStones = 150,     -- Spirit Stones for securing its egg
            MaxHealth = 1200,      -- a beginner's Qi Palm weakens it alone in ~72 strikes (about half a minute)
            WeakenedAt = 0.4,      -- share of health below which it falters and the egg can be taken
            HitRadius = 14,        -- its body round the chest
            EngageRadius = 24,
            LeashRadius = 60,      -- from the lair
            CalmAfter = 12,        -- seconds with nobody near before it heals and sleeps
            RespawnTime = 30,      -- seconds after an egg is secured
            DropTime = 30,         -- seconds a dropped egg waits for its thief
            WalkSpeed = 12,
            ChaseSpeed = 21,       -- below a beginner's run (22): dashes and its pounces decide it
            TurnSpeed = 140,       -- degrees per second
            Egg = { Height = 4, Under = Vector3.new(4.55, 1.9, -15), CarriedHeight = 2.6 }, -- under the raised right paw
            WeakenedHint = "falters: take the egg from under its paw!",
            Stagger = 1.1,         -- seconds a knocked-back player is off their feet
            WeakenedSlowdown = 1.7, -- attack cooldown multiplier while weakened
            Attacks = {
                -- the left paw slams (the right one pins the egg)
                Slam = { Kind = "Sweep", Range = 24, Arc = 55, WindUp = 0.75, Cooldown = 2.6, Knockback = 45 },
                Roar = { Kind = "Wave", Radius = 44, WaveSpeed = 34, WindUp = 1.1, Cooldown = 8, Knockback = 40 },
                Pounce = { Kind = "Pounce", MinRange = 16, MaxRange = 46, WindUp = 0.6, Air = 0.95, Height = 9, Cooldown = 4.5, Radius = 12, Knockback = 55 },
            },
        },
        MantisSage = {
            DisplayName = "Bamboo Mantis Sage",
            Island = "JadeGrove",
            Lair = Vector3.new(50, 2.4, 26),    -- the only open, level ground far from the glade
            Facing = Vector3.new(0, 2.4, 6),
            Eggs = { "JadeSpiritEgg", "BloomwoodEgg", "AncientGroveEgg" },
            SafeZone = { Centre = Vector3.new(-30, 4, 41), Radius = 15, Name = "Bloom Glade" },
            SecureStones = 600,     -- Spirit Stones for securing its egg
            MaxHealth = 2000,      -- a Qi Gatherer's palm (11 a strike) weakens it alone in ~110 strikes
            WeakenedAt = 0.4,
            HitRadius = 13,
            EngageRadius = 26,
            LeashRadius = 60,
            CalmAfter = 12,
            RespawnTime = 30,
            DropTime = 30,
            WalkSpeed = 13,
            ChaseSpeed = 23,       -- below a Qi Gatherer's run (24); its leaps are long and high
            TurnSpeed = 160,
            TurnsToFace = true,    -- awake at its lair, it turns to face whoever it watches
            -- held in its folded forearms, set down on the ground when weakened
            Egg = { Height = 4, Under = Vector3.new(0, 20.2, -12.3), Offered = Vector3.new(0, 1.9, -16), CarriedHeight = 2.6 },
            WeakenedHint = "lowers its blades and sets the egg down: take it!",
            Stagger = 1.1,
            WeakenedSlowdown = 1.7,
            Attacks = {
                Scythe = { Kind = "Sweep", Range = 26, Arc = 65, WindUp = 0.6, Cooldown = 2.2, Knockback = 45 },
                BladeWave = { Kind = "Wave", Arc = 50, Radius = 46, WaveSpeed = 40, WindUp = 0.9, Cooldown = 6.5, Knockback = 40 },
                Leap = { Kind = "Pounce", MinRange = 16, MaxRange = 72, WindUp = 0.5, Air = 1.1, Height = 16, Cooldown = 4.2, Radius = 12, Knockback = 55 },
            },
        },
    },

    -- Sword flight (src/server/Qinggong/FlightService), from UnlockRank. Drains stamina (Cost per
    -- second while moving, HoverCost while still) and needs MinStamina to take off. Qi barriers
    -- still hold: flight never reaches an island above the rider's rank.
    SwordFlight = {
        UnlockRank = "FoundationInitiate",
        Cost = 8,
        HoverCost = 4,
        MinStamina = 25,
        ClimbSpeed = 22, -- vertical, on the jump / crouch keys
        -- the sword's glow per realm (saturated: Neon blooms pale ones)
        RealmGlow = {
            ["Qi Awakening"] = Color3.fromRGB(40, 140, 255),
            ["Qi Foundation"] = Color3.fromRGB(40, 140, 255),
            ["Spirit Core"] = Color3.fromRGB(20, 210, 150),
            ["Spirit Soul"] = Color3.fromRGB(20, 210, 150),
            ["Ascendant Realm"] = Color3.fromRGB(255, 170, 30),
            ["Immortal Realm"] = Color3.fromRGB(255, 170, 30),
        },
        DefaultGlow = Color3.fromRGB(100, 60, 255), -- Divine Realm and above (bluer than 8246ff, which Neon turned pink)
    },

    RelicTag = "SpiritRelic",
    EggTag = "PetEggStand",
    -- a barrier at each island bridge: only players of its RankId pass
    BridgeBarrierTag = "QiBarrier",
    Relics = {
        { Id = "IslandRoot", DisplayName = "Root of the Island", QiReward = 300, RequiredRank = "QiInitiate" },
        { Id = "GroveHeart", DisplayName = "Grove Heart", QiReward = 800, RequiredRank = "QiGatherer" },
        { Id = "JadeSeed", DisplayName = "Jade Seed", QiReward = 800, RequiredRank = "QiGatherer" },
        { Id = "WhisperingSpring", DisplayName = "Whispering Spring", QiReward = 800, RequiredRank = "QiGatherer" },
        { Id = "EmberHeart", DisplayName = "Ember Heart", QiReward = 1500, RequiredRank = "QiAwakener" },
        { Id = "AshenSigil", DisplayName = "Ashen Sigil", QiReward = 1500, RequiredRank = "QiAwakener" },
        { Id = "CalderaCrown", DisplayName = "Caldera Crown", QiReward = 1500, RequiredRank = "QiAwakener" },
        { Id = "MoonMirror", DisplayName = "Moon Mirror", QiReward = 3000, RequiredRank = "FoundationInitiate" },
        { Id = "StarWell", DisplayName = "Star Well", QiReward = 3000, RequiredRank = "FoundationInitiate" },
        { Id = "OriginAltar", DisplayName = "Origin Altar", QiReward = 250000, RequiredRank = "DivineInitiate" },
        { Id = "VoidShard", DisplayName = "Void Shard", QiReward = 1000000, RequiredRank = "VoidWalker" },
    },

    LevitationHeight = 1.5,
    LevitationBobHeight = 0.3,
    LevitationBobTime = 1.6,
    MeditationAnimationId = 0,

    StartingRank = "Qi Initiate",

    Ranks = {
        { Id = "QiInitiate", Name = "Qi Initiate", Realm = "Qi Awakening", Level = 1, QiRequired = 0, AuraTier = 1, QiMultiplier = 1 },
        { Id = "QiGatherer", Name = "Qi Gatherer", Realm = "Qi Awakening", Level = 2, QiRequired = 300, AuraTier = 1, QiMultiplier = 1 },
        { Id = "QiCondenser", Name = "Qi Condenser", Realm = "Qi Awakening", Level = 3, QiRequired = 900, AuraTier = 2, QiMultiplier = 1 },
        { Id = "QiAdept", Name = "Qi Adept", Realm = "Qi Awakening", Level = 4, QiRequired = 2000, AuraTier = 2, QiMultiplier = 1 },
        { Id = "QiAwakener", Name = "Qi Awakener", Realm = "Qi Awakening", Level = 5, QiRequired = 4000, AuraTier = 2, QiMultiplier = 1 },

        { Id = "FoundationInitiate", Name = "Foundation Initiate", Realm = "Qi Foundation", Level = 1, QiRequired = 6500, AuraTier = 3, QiMultiplier = 1 },
        { Id = "FoundationBuilder", Name = "Foundation Builder", Realm = "Qi Foundation", Level = 2, QiRequired = 10000, AuraTier = 3, QiMultiplier = 1 },
        { Id = "FoundationAdept", Name = "Foundation Adept", Realm = "Qi Foundation", Level = 3, QiRequired = 15000, AuraTier = 3, QiMultiplier = 1 },
        { Id = "FoundationMaster", Name = "Foundation Master", Realm = "Qi Foundation", Level = 4, QiRequired = 21000, AuraTier = 4, QiMultiplier = 1 },
        { Id = "PerfectFoundation", Name = "Perfect Foundation", Realm = "Qi Foundation", Level = 5, QiRequired = 29000, AuraTier = 4, QiMultiplier = 1 },

        { Id = "CoreInitiate", Name = "Core Initiate", Realm = "Spirit Core", Level = 1, QiRequired = 40000, AuraTier = 4, QiMultiplier = 1 },
        { Id = "CoreFormation", Name = "Core Formation", Realm = "Spirit Core", Level = 2, QiRequired = 55000, AuraTier = 5, QiMultiplier = 1 },
        { Id = "CoreAdept", Name = "Core Adept", Realm = "Spirit Core", Level = 3, QiRequired = 72000, AuraTier = 5, QiMultiplier = 1 },
        { Id = "CoreMaster", Name = "Core Master", Realm = "Spirit Core", Level = 4, QiRequired = 95000, AuraTier = 5, QiMultiplier = 1 },
        { Id = "GoldenSpiritCore", Name = "Golden Spirit Core", Realm = "Spirit Core", Level = 5, QiRequired = 120000, AuraTier = 5, QiMultiplier = 1 },
        { Id = "SoulAwakening", Name = "Soul Awakening", Realm = "Spirit Soul", Level = 1, QiRequired = 148000, AuraTier = 5, QiMultiplier = 2 },
        { Id = "SoulTempering", Name = "Soul Tempering", Realm = "Spirit Soul", Level = 2, QiRequired = 234000, AuraTier = 5, QiMultiplier = 2 },
        { Id = "SoulRefinement", Name = "Soul Refinement", Realm = "Spirit Soul", Level = 3, QiRequired = 335000, AuraTier = 5, QiMultiplier = 2 },
        { Id = "SoulManifestation", Name = "Soul Manifestation", Realm = "Spirit Soul", Level = 4, QiRequired = 451000, AuraTier = 5, QiMultiplier = 2 },
        { Id = "SpiritSoulMaster", Name = "Spirit Soul Master", Realm = "Spirit Soul", Level = 5, QiRequired = 582000, AuraTier = 5, QiMultiplier = 2 },

        { Id = "AscendantInitiate", Name = "Ascendant Initiate", Realm = "Ascendant Realm", Level = 1, QiRequired = 688000, AuraTier = 5, QiMultiplier = 4 },
        { Id = "SkyAscendant", Name = "Sky Ascendant", Realm = "Ascendant Realm", Level = 2, QiRequired = 982000, AuraTier = 5, QiMultiplier = 4 },
        { Id = "HeavenlyAdept", Name = "Heavenly Adept", Realm = "Ascendant Realm", Level = 3, QiRequired = 1330000, AuraTier = 5, QiMultiplier = 4 },
        { Id = "CelestialMaster", Name = "Celestial Master", Realm = "Ascendant Realm", Level = 4, QiRequired = 1730000, AuraTier = 5, QiMultiplier = 4 },
        { Id = "AscendantSovereign", Name = "Ascendant Sovereign", Realm = "Ascendant Realm", Level = 5, QiRequired = 2180000, AuraTier = 5, QiMultiplier = 4 },

        { Id = "LesserImmortal", Name = "Lesser Immortal", Realm = "Immortal Realm", Level = 1, QiRequired = 2500000, AuraTier = 5, QiMultiplier = 8 },
        { Id = "TrueImmortal", Name = "True Immortal", Realm = "Immortal Realm", Level = 2, QiRequired = 3480000, AuraTier = 5, QiMultiplier = 8 },
        { Id = "GoldenImmortal", Name = "Golden Immortal", Realm = "Immortal Realm", Level = 3, QiRequired = 4630000, AuraTier = 5, QiMultiplier = 8 },
        { Id = "ImmortalLord", Name = "Immortal Lord", Realm = "Immortal Realm", Level = 4, QiRequired = 5950000, AuraTier = 5, QiMultiplier = 8 },
        { Id = "ImmortalEmperor", Name = "Immortal Emperor", Realm = "Immortal Realm", Level = 5, QiRequired = 7450000, AuraTier = 5, QiMultiplier = 8 },

        { Id = "DivineInitiate", Name = "Divine Initiate", Realm = "Divine Realm", Level = 1, QiRequired = 8460000, AuraTier = 5, QiMultiplier = 16 },
        { Id = "DivineAdept", Name = "Divine Adept", Realm = "Divine Realm", Level = 2, QiRequired = 11400000, AuraTier = 5, QiMultiplier = 16 },
        { Id = "DivineLord", Name = "Divine Lord", Realm = "Divine Realm", Level = 3, QiRequired = 14900000, AuraTier = 5, QiMultiplier = 16 },
        { Id = "DivineKing", Name = "Divine King", Realm = "Divine Realm", Level = 4, QiRequired = 18900000, AuraTier = 5, QiMultiplier = 16 },
        { Id = "DivineEmperor", Name = "Divine Emperor", Realm = "Divine Realm", Level = 5, QiRequired = 23400000, AuraTier = 5, QiMultiplier = 16 },

        { Id = "StarInitiate", Name = "Star Initiate", Realm = "Cosmic Realm", Level = 1, QiRequired = 26300000, AuraTier = 5, QiMultiplier = 32 },
        { Id = "StarForger", Name = "Star Forger", Realm = "Cosmic Realm", Level = 2, QiRequired = 34500000, AuraTier = 5, QiMultiplier = 32 },
        { Id = "NebulaMaster", Name = "Nebula Master", Realm = "Cosmic Realm", Level = 3, QiRequired = 44200000, AuraTier = 5, QiMultiplier = 32 },
        { Id = "GalaxySovereign", Name = "Galaxy Sovereign", Realm = "Cosmic Realm", Level = 4, QiRequired = 55300000, AuraTier = 5, QiMultiplier = 32 },
        { Id = "CosmicEmperor", Name = "Cosmic Emperor", Realm = "Cosmic Realm", Level = 5, QiRequired = 67900000, AuraTier = 5, QiMultiplier = 32 },

        { Id = "VoidWalker", Name = "Void Walker", Realm = "Void Realm", Level = 1, QiRequired = 76400000, AuraTier = 5, QiMultiplier = 64 },
        { Id = "VoidShaper", Name = "Void Shaper", Realm = "Void Realm", Level = 2, QiRequired = 99900000, AuraTier = 5, QiMultiplier = 64 },
        { Id = "VoidMaster", Name = "Void Master", Realm = "Void Realm", Level = 3, QiRequired = 128000000, AuraTier = 5, QiMultiplier = 64 },
        { Id = "SpaceTimeLord", Name = "Space-Time Lord", Realm = "Void Realm", Level = 4, QiRequired = 160000000, AuraTier = 5, QiMultiplier = 64 },
        { Id = "VoidSovereign", Name = "Void Sovereign", Realm = "Void Realm", Level = 5, QiRequired = 196000000, AuraTier = 5, QiMultiplier = 64 },

        { Id = "DaoSeeker", Name = "Dao Seeker", Realm = "Heavenly Dao", Level = 1, QiRequired = 219000000, AuraTier = 5, QiMultiplier = 128 },
        { Id = "DaoAdept", Name = "Dao Adept", Realm = "Heavenly Dao", Level = 2, QiRequired = 282000000, AuraTier = 5, QiMultiplier = 128 },
        { Id = "DaoMaster", Name = "Dao Master", Realm = "Heavenly Dao", Level = 3, QiRequired = 357000000, AuraTier = 5, QiMultiplier = 128 },
        { Id = "HeavenlyLawkeeper", Name = "Heavenly Lawkeeper", Realm = "Heavenly Dao", Level = 4, QiRequired = 443000000, AuraTier = 5, QiMultiplier = 128 },
        { Id = "DaoSovereign", Name = "Dao Sovereign", Realm = "Heavenly Dao", Level = 5, QiRequired = 540000000, AuraTier = 5, QiMultiplier = 128 },

        { Id = "PrimordialAwakening", Name = "Primordial Awakening", Realm = "Primordial Realm", Level = 1, QiRequired = 604000000, AuraTier = 5, QiMultiplier = 256 },
        { Id = "AncientOrigin", Name = "Ancient Origin", Realm = "Primordial Realm", Level = 2, QiRequired = 785000000, AuraTier = 5, QiMultiplier = 256 },
        { Id = "PrimordialLord", Name = "Primordial Lord", Realm = "Primordial Realm", Level = 3, QiRequired = 998000000, AuraTier = 5, QiMultiplier = 256 },
        { Id = "OriginEmperor", Name = "Origin Emperor", Realm = "Primordial Realm", Level = 4, QiRequired = 1240000000, AuraTier = 5, QiMultiplier = 256 },
        { Id = "PrimordialSovereign", Name = "Primordial Sovereign", Realm = "Primordial Realm", Level = 5, QiRequired = 1520000000, AuraTier = 5, QiMultiplier = 256 },

        { Id = "EternalInitiate", Name = "Eternal Initiate", Realm = "Eternal Transcendence", Level = 1, QiRequired = 1700000000, AuraTier = 5, QiMultiplier = 512 },
        { Id = "EternalAscendant", Name = "Eternal Ascendant", Realm = "Eternal Transcendence", Level = 2, QiRequired = 2190000000, AuraTier = 5, QiMultiplier = 512 },
        { Id = "InfinityMaster", Name = "Infinity Master", Realm = "Eternal Transcendence", Level = 3, QiRequired = 2770000000, AuraTier = 5, QiMultiplier = 512 },
        { Id = "TranscendentOne", Name = "Transcendent One", Realm = "Eternal Transcendence", Level = 4, QiRequired = 3430000000, AuraTier = 5, QiMultiplier = 512 },
        { Id = "EternalOrigin", Name = "Eternal Origin", Realm = "Eternal Transcendence", Level = 5, QiRequired = 4180000000, AuraTier = 5, QiMultiplier = 512 },
    },

    MaxEquippedPets = 3,

    Pets = {
        AquaWisp = { DisplayName = "Aqua Wisp", Rarity = "Common", Theme = "Water", QiBonusPercent = 10 },
        EmberWyrm = { DisplayName = "Ember Wyrm", Rarity = "Uncommon", Theme = "Fire", QiBonusPercent = 20 },
        LunarHopper = { DisplayName = "Lunar Hopper", Rarity = "Rare", Theme = "Moonlight", QiBonusPercent = 35 },
        VoltFox = { DisplayName = "Volt Fox", Rarity = "Epic", Theme = "Lightning", QiBonusPercent = 50 },
        GoldenKirin = { DisplayName = "Golden Kirin", Rarity = "Legendary", Theme = "Nature", QiBonusPercent = 60 },
        AstralWhale = { DisplayName = "Astral Whale", Rarity = "Mythical", Theme = "Cosmic", QiBonusPercent = 100 },
        NineTailMoonfox = { DisplayName = "Nine-Tail Moonfox", Rarity = "Mythical", Theme = "Moon", QiBonusPercent = 100 },
        OriginSerpent = { DisplayName = "Origin Serpent", Rarity = "Secret", Theme = "Primordial", QiBonusPercent = 150 },

        MossGolem = { DisplayName = "Moss Golem", Rarity = "Common", Theme = "Earth", QiBonusPercent = 10 },
        MyceliumSprite = { DisplayName = "Mycelium Sprite", Rarity = "Uncommon", Theme = "Forest", QiBonusPercent = 20 },
        JadeSpiritPanda = { DisplayName = "Jade Spirit Panda", Rarity = "Rare", Theme = "Nature", QiBonusPercent = 35 },
        JadeAntlerDeer = { DisplayName = "Jade Antler Deer", Rarity = "Epic", Theme = "Nature", QiBonusPercent = 50 },

        MagmaCub = { DisplayName = "Magma Cub", Rarity = "Common", Theme = "Lava", QiBonusPercent = 10 },
        SunscaleDragon = { DisplayName = "Sunscale Dragon", Rarity = "Legendary", Theme = "Solar", QiBonusPercent = 60 },
        DawnPhoenix = { DisplayName = "Dawn Phoenix", Rarity = "Legendary", Theme = "Fire", QiBonusPercent = 60 },
        WindSprite = { DisplayName = "Wind Sprite", Rarity = "Common", Theme = "Wind", QiBonusPercent = 10 },
        CloudSheep = { DisplayName = "Cloud Sheep", Rarity = "Uncommon", Theme = "Clouds", QiBonusPercent = 25 },
        SpiritCrane = { DisplayName = "Spirit Crane", Rarity = "Rare", Theme = "Spiritual energy", QiBonusPercent = 40 },
        AzureSkyDragon = { DisplayName = "Azure Sky Dragon", Rarity = "Epic", Theme = "Wind and sky", QiBonusPercent = 60 },
        StormhornKirin = { DisplayName = "Stormhorn Kirin", Rarity = "Legendary", Theme = "Storms", QiBonusPercent = 70 },

        GlacierPuff = { DisplayName = "Glacier Puff", Rarity = "Common", Theme = "Ice", QiBonusPercent = 15 },
        ThunderJelly = { DisplayName = "Thunder Jelly", Rarity = "Uncommon", Theme = "Electricity", QiBonusPercent = 25 },
        CrystalBeetle = { DisplayName = "Crystal Beetle", Rarity = "Rare", Theme = "Crystal", QiBonusPercent = 45 },
        GravityImp = { DisplayName = "Gravity Imp", Rarity = "Epic", Theme = "Gravity", QiBonusPercent = 65 },
        ThunderclawDrake = { DisplayName = "Thunderclaw Drake", Rarity = "Legendary", Theme = "Lightning", QiBonusPercent = 80 },
        FrostfangSerpent = { DisplayName = "Frostfang Serpent", Rarity = "Mythical", Theme = "Ice", QiBonusPercent = 130 },

        DreamMoth = { DisplayName = "Dream Moth", Rarity = "Common", Theme = "Dreams", QiBonusPercent = 15 },
        CrystalSnail = { DisplayName = "Crystal Snail", Rarity = "Uncommon", Theme = "Crystals", QiBonusPercent = 30 },
        PrismArmadillo = { DisplayName = "Prism Armadillo", Rarity = "Rare", Theme = "Crystals", QiBonusPercent = 50 },
        LanternWarden = { DisplayName = "Lantern Warden", Rarity = "Epic", Theme = "Light", QiBonusPercent = 70 },
        JadeWyrmTurtle = { DisplayName = "Jade Wyrm Turtle", Rarity = "Legendary", Theme = "Earth", QiBonusPercent = 85 },

        EchoBat = { DisplayName = "Echo Bat", Rarity = "Common", Theme = "Sound", QiBonusPercent = 15 },
        QiClockworkFinch = { DisplayName = "Qi Clockwork Finch", Rarity = "Uncommon", Theme = "Magical machinery", QiBonusPercent = 30 },
        MoonfangTiger = { DisplayName = "Moonfang Tiger", Rarity = "Rare", Theme = "Moonlight", QiBonusPercent = 55 },
        ThousandEyedGuardian = { DisplayName = "Thousand-Eyed Guardian", Rarity = "Epic", Theme = "Mysticism", QiBonusPercent = 80 },
        NinefoldSpiritSerpent = { DisplayName = "Ninefold Spirit Serpent", Rarity = "Legendary", Theme = "Spiritual energy", QiBonusPercent = 95 },
        WorldrootColossus = { DisplayName = "Worldroot Colossus", Rarity = "Mythical", Theme = "Ancient nature", QiBonusPercent = 160 },

        SandPhantom = { DisplayName = "Sand Phantom", Rarity = "Common", Theme = "Sand", QiBonusPercent = 15 },
        SolarButterfly = { DisplayName = "Solar Butterfly", Rarity = "Uncommon", Theme = "Solar energy", QiBonusPercent = 30 },
        ObsidianGuardian = { DisplayName = "Obsidian Guardian", Rarity = "Rare", Theme = "Darkness and crystal", QiBonusPercent = 55 },
        GoldenManeLion = { DisplayName = "Golden Mane Lion", Rarity = "Epic", Theme = "Solar energy", QiBonusPercent = 75 },
        BonefireDragon = { DisplayName = "Bonefire Dragon", Rarity = "Legendary", Theme = "Spectral fire", QiBonusPercent = 90 },

        DreadfangCerberus = { DisplayName = "Dreadfang Cerberus", Rarity = "Epic", Theme = "Shadow", QiBonusPercent = 85 },
        PrismaticPhoenix = { DisplayName = "Prismatic Phoenix", Rarity = "Mythical", Theme = "Rainbow energy", QiBonusPercent = 170 },

        StarfallFox = { DisplayName = "Starfall Fox", Rarity = "Common", Theme = "Stars", QiBonusPercent = 20 },
        CosmicJellyfish = { DisplayName = "Cosmic Jellyfish", Rarity = "Uncommon", Theme = "Nebulae", QiBonusPercent = 40 },
        NebulaOwl = { DisplayName = "Nebula Owl", Rarity = "Rare", Theme = "Cosmic energy", QiBonusPercent = 65 },
        CelestialSnowLeopard = { DisplayName = "Celestial Snow Leopard", Rarity = "Epic", Theme = "Ice and celestial energy", QiBonusPercent = 95 },
        CometStag = { DisplayName = "Comet Stag", Rarity = "Legendary", Theme = "Comets", QiBonusPercent = 115 },
        CelestialPearlDragon = { DisplayName = "Celestial Pearl Dragon", Rarity = "Mythical", Theme = "Celestial energy", QiBonusPercent = 190 },

        EclipseCat = { DisplayName = "Eclipse Cat", Rarity = "Epic", Theme = "Darkness and eclipses", QiBonusPercent = 110 },
        TimekeeperTortoise = { DisplayName = "Timekeeper Tortoise", Rarity = "Legendary", Theme = "Time", QiBonusPercent = 130 },
        GalaxyManta = { DisplayName = "Galaxy Manta", Rarity = "Mythical", Theme = "Cosmic energy", QiBonusPercent = 220 },

        Shadowcoil = { DisplayName = "Shadowcoil", Rarity = "Rare", Theme = "Shadow", QiBonusPercent = 100 },
        RuneSphinx = { DisplayName = "Rune Sphinx", Rarity = "Legendary", Theme = "Ancient magic", QiBonusPercent = 170 },
        ThousandYearDreamEater = { DisplayName = "Thousand-Year Dream Eater", Rarity = "Mythical", Theme = "Dreams", QiBonusPercent = 280 },
        TheNamelessOne = { DisplayName = "The Nameless One", Rarity = "Secret", Theme = "Unknown cosmic energy", QiBonusPercent = 420 },

        HeavenbreakerApe = { DisplayName = "Heavenbreaker Ape", Rarity = "Legendary", Theme = "Heavenly power", QiBonusPercent = 205 },
        VoidscaleHydra = { DisplayName = "Voidscale Hydra", Rarity = "Mythical", Theme = "Void", QiBonusPercent = 340 },

        EternalClockworkDragon = { DisplayName = "Eternal Clockwork Dragon", Rarity = "Secret", Theme = "Time", QiBonusPercent = 600 },
    },

    PetRarityColors = {
        Common = Color3.fromRGB(220, 225, 235),
        Uncommon = Color3.fromRGB(120, 230, 140),
        Rare = Color3.fromRGB(120, 200, 255),
        Epic = Color3.fromRGB(190, 140, 255),
        Legendary = Color3.fromRGB(255, 200, 70),
        Mythical = Color3.fromRGB(255, 110, 160),
        Secret = Color3.fromRGB(255, 255, 255),
    },

    MaxOwnedPets = 50,

    StarterPetIds = { "AquaWisp" },

    GrantDevTestPets = false,
    DevTestPetIds = { "EmberWyrm", "VoltFox", "GoldenKirin", "NineTailMoonfox", "OriginSerpent" },

    Eggs = {
        BeginnerQiEgg = {
            DisplayName = "Beginner Qi Egg",
            RequiredRank = "QiInitiate",
            Cooldown = 45,
            Pool = {
                { PetId = "AquaWisp", Weight = 45 },
                { PetId = "EmberWyrm", Weight = 27 },
                { PetId = "LunarHopper", Weight = 15 },
                { PetId = "VoltFox", Weight = 8 },
                { PetId = "GoldenKirin", Weight = 4 },
                { PetId = "AstralWhale", Weight = 0.9 },
                { PetId = "OriginSerpent", Weight = 0.1 },
            },
        },
        JadeSpiritEgg = {
            DisplayName = "Jade Spirit Egg",
            RequiredRank = "QiGatherer",
            Cooldown = 45,
            Pool = {
                { PetId = "MossGolem", Weight = 45 },
                { PetId = "MyceliumSprite", Weight = 27 },
                { PetId = "JadeSpiritPanda", Weight = 15 },
                { PetId = "JadeAntlerDeer", Weight = 8 },
                { PetId = "GoldenKirin", Weight = 5 },
            },
        },
        InfernoEgg = {
            DisplayName = "Inferno Egg",
            RequiredRank = "QiAwakener",
            Cooldown = 45,
            Pool = {
                { PetId = "MagmaCub", Weight = 45 },
                { PetId = "EmberWyrm", Weight = 50 },
                { PetId = "SunscaleDragon", Weight = 2.5 },
                { PetId = "DawnPhoenix", Weight = 2.5 },
            },
        },

        SpiritBreezeEgg = {
            DisplayName = "Spirit Breeze Egg",
            RequiredRank = "QiAdept",
            Cooldown = 45,
            Pool = {
                { PetId = "WindSprite", Weight = 45 },
                { PetId = "CloudSheep", Weight = 27 },
                { PetId = "SpiritCrane", Weight = 15 },
                { PetId = "AzureSkyDragon", Weight = 8 },
                { PetId = "StormhornKirin", Weight = 5 },
            },
        },
        ElementalCoreEgg = {
            DisplayName = "Elemental Core Egg",
            RequiredRank = "FoundationInitiate",
            Cooldown = 45,
            Pool = {
                { PetId = "GlacierPuff", Weight = 45 },
                { PetId = "ThunderJelly", Weight = 27 },
                { PetId = "CrystalBeetle", Weight = 15 },
                { PetId = "GravityImp", Weight = 8 },
                { PetId = "ThunderclawDrake", Weight = 4 },
                { PetId = "FrostfangSerpent", Weight = 1 },
            },
        },
        BloomwoodEgg = {
            DisplayName = "Bloomwood Egg",
            RequiredRank = "FoundationAdept",
            Cooldown = 45,
            Pool = {
                { PetId = "DreamMoth", Weight = 45 },
                { PetId = "CrystalSnail", Weight = 27 },
                { PetId = "PrismArmadillo", Weight = 15 },
                { PetId = "LanternWarden", Weight = 8 },
                { PetId = "JadeWyrmTurtle", Weight = 5 },
            },
        },
        AncientGroveEgg = {
            DisplayName = "Ancient Grove Egg",
            RequiredRank = "CoreInitiate",
            Cooldown = 45,
            Pool = {
                { PetId = "EchoBat", Weight = 45 },
                { PetId = "QiClockworkFinch", Weight = 27 },
                { PetId = "MoonfangTiger", Weight = 15 },
                { PetId = "ThousandEyedGuardian", Weight = 8 },
                { PetId = "NinefoldSpiritSerpent", Weight = 4 },
                { PetId = "WorldrootColossus", Weight = 1 },
            },
        },
        MagmaHeartEgg = {
            DisplayName = "Magma Heart Egg",
            RequiredRank = "PerfectFoundation",
            Cooldown = 45,
            Pool = {
                { PetId = "SandPhantom", Weight = 45 },
                { PetId = "SolarButterfly", Weight = 27 },
                { PetId = "ObsidianGuardian", Weight = 15 },
                { PetId = "GoldenManeLion", Weight = 8 },
                { PetId = "BonefireDragon", Weight = 5 },
            },
        },
        PhoenixAshEgg = {
            DisplayName = "Phoenix Ash Egg",
            RequiredRank = "CoreAdept",
            Cooldown = 45,
            Pool = {
                { PetId = "MagmaCub", Weight = 45 },
                { PetId = "EmberWyrm", Weight = 42 },
                { PetId = "DreadfangCerberus", Weight = 8 },
                { PetId = "SunscaleDragon", Weight = 2 },
                { PetId = "BonefireDragon", Weight = 2 },
                { PetId = "PrismaticPhoenix", Weight = 1 },
            },
        },
        CelestialEgg = {
            DisplayName = "Celestial Egg",
            RequiredRank = "SoulAwakening",
            Cooldown = 45,
            Pool = {
                { PetId = "StarfallFox", Weight = 45 },
                { PetId = "CosmicJellyfish", Weight = 27 },
                { PetId = "NebulaOwl", Weight = 15 },
                { PetId = "CelestialSnowLeopard", Weight = 8 },
                { PetId = "CometStag", Weight = 4 },
                { PetId = "CelestialPearlDragon", Weight = 1 },
            },
        },
        AstralSanctumEgg = {
            DisplayName = "Astral Sanctum Egg",
            RequiredRank = "AscendantInitiate",
            Cooldown = 45,
            Pool = {
                { PetId = "StarfallFox", Weight = 45 },
                { PetId = "CosmicJellyfish", Weight = 27 },
                { PetId = "NebulaOwl", Weight = 15 },
                { PetId = "EclipseCat", Weight = 8 },
                { PetId = "TimekeeperTortoise", Weight = 4 },
                { PetId = "GalaxyManta", Weight = 1 },
            },
        },
        HeavenlyThroneEgg = {
            DisplayName = "Heavenly Throne Egg",
            RequiredRank = "LesserImmortal",
            Cooldown = 45,
            Pool = {
                { PetId = "CelestialSnowLeopard", Weight = 47.5 },
                { PetId = "EclipseCat", Weight = 47.5 },
                { PetId = "CometStag", Weight = 2 },
                { PetId = "TimekeeperTortoise", Weight = 2 },
                { PetId = "CelestialPearlDragon", Weight = 0.5 },
                { PetId = "GalaxyManta", Weight = 0.5 },
            },
        },
        ForbiddenOriginEgg = {
            DisplayName = "Forbidden Origin Egg",
            RequiredRank = "DivineInitiate",
            Cooldown = 45,
            Pool = {
                { PetId = "Shadowcoil", Weight = 87 },
                { PetId = "EclipseCat", Weight = 8 },
                { PetId = "RuneSphinx", Weight = 4 },
                { PetId = "ThousandYearDreamEater", Weight = 0.9 },
                { PetId = "TheNamelessOne", Weight = 0.1 },
            },
        },
        VoidRiftEgg = {
            DisplayName = "Void Rift Egg",
            RequiredRank = "VoidWalker",
            Cooldown = 45,
            Pool = {
                { PetId = "Shadowcoil", Weight = 87 },
                { PetId = "EclipseCat", Weight = 8 },
                { PetId = "HeavenbreakerApe", Weight = 4 },
                { PetId = "VoidscaleHydra", Weight = 0.9 },
                { PetId = "TheNamelessOne", Weight = 0.1 },
            },
        },
        PrimordialAbyssEgg = {
            DisplayName = "Primordial Abyss Egg",
            RequiredRank = "PrimordialAwakening",
            Cooldown = 45,
            Pool = {
                { PetId = "HeavenbreakerApe", Weight = 99 },
                { PetId = "VoidscaleHydra", Weight = 0.45 },
                { PetId = "ThousandYearDreamEater", Weight = 0.45 },
                { PetId = "EternalClockworkDragon", Weight = 0.05 },
                { PetId = "TheNamelessOne", Weight = 0.05 },
            },
        },
    },

    -- Outfits worn over the player's avatar (src/server/Outfits/OutfitService), by the user ids
    -- listed, or by anyone who owns its game pass once GamePassId is set.
    Outfits = {
        Murim = {
            DisplayName = "Murim Robes",
            OwnerUserIds = { 4993575280 },
            GamePassId = 0,
        },
    },
}

return GameConfig
