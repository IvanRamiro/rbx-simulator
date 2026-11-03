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
            -- the last three realms (the owner, 2026-11-02: "the speed doesn't feel enough even though I am
            -- max realm"): each a big step faster, flight always faster than the run
            { RankId = "DaoSeeker", AirLeaps = 8, RunSpeed = 44, Stamina = 215, DashSpeed = 115, FlightSpeed = 88 },
            { RankId = "PrimordialAwakening", AirLeaps = 9, RunSpeed = 54, Stamina = 240, DashSpeed = 130, FlightSpeed = 104 },
            { RankId = "EternalInitiate", AirLeaps = 10, RunSpeed = 64, Stamina = 270, DashSpeed = 150, FlightSpeed = 120 },
            { RankId = "EternalOrigin", AirLeaps = 11, RunSpeed = 76, Stamina = 300, DashSpeed = 170, FlightSpeed = 140 },
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
    -- (Combat.powerOf). The sword strikes fast and wide; the spear slower, farther and harder, for
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
    StarterWeapon = "Sword1", -- every player's first weapon, given once: to a new player, or to a save from before weapons (PlayerData)
    MaxOwnedWeapons = 30,

    -- The relic forge, at the Blacksmith: a relic unlocks its element for good (Relics.<n>.Element
    -- when attuned; Guardians.<Id>.Element when its egg is secured). Forging gives an owned weapon an
    -- element and a name the player chooses, for PriceShare of its price (at least MinPrice), again
    -- for each re-forge. A forged weapon strikes DamageBonus harder, glows and trails in its
    -- element's colours and bursts with its element (CombatFx). Neon colours stay saturated.
    Forge = {
        DamageBonus = 0.1,
        PriceShare = 0.5,
        MinPrice = 30,
        NameLength = { Min = 3, Max = 20 },
        Order = { "Wood", "Fire", "Frost", "Void", "Earth", "Wind" },
        Elements = {
            Wood = { DisplayName = "Wood", Color = Color3.fromRGB(40, 200, 70), Core = Color3.fromRGB(190, 255, 150),
                Source = "the Root of the Island and Jade Grove's relics" },
            Fire = { DisplayName = "Fire", Color = Color3.fromRGB(255, 90, 20), Core = Color3.fromRGB(255, 215, 120),
                Source = "Ember Peak's relics" },
            Frost = { DisplayName = "Frost", Color = Color3.fromRGB(40, 170, 255), Core = Color3.fromRGB(210, 245, 255),
                Source = "Moonlit Isle's relics" },
            Void = { DisplayName = "Void", Color = Color3.fromRGB(110, 40, 255), Core = Color3.fromRGB(205, 165, 255),
                Source = "Origin Abyss's relics" },
            Earth = { DisplayName = "Earth", Color = Color3.fromRGB(205, 130, 35), Core = Color3.fromRGB(255, 220, 150),
                Source = "the Awakened Stone Lion: secure its egg" },
            Wind = { DisplayName = "Wind", Color = Color3.fromRGB(30, 230, 190), Core = Color3.fromRGB(200, 255, 240),
                Source = "the Bamboo Mantis Sage: secure its egg" },
        },
    },

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

    -- Guardians (src/server/Guardians/GuardianService; design doc section 7). A guardian holds no
    -- egg: it guards its island's three egg stands (EggStands). Weakened below WeakenedAt, one of
    -- their eggs can be taken (if the thief's rank can hatch it) and carried to the SafeZone: a
    -- circle (island-local studs), or with Island a whole island, Yggdrasil, home across the
    -- bridge. A secured egg goes to the egg inventory and is hatched at the Hatching Altar; its stand
    -- shows a random one of Eggs after EggTheft.RespawnTime. Positions are island-local studs.
    -- Attack kinds: Sweep strikes in front (Range, Arc); Wave rolls along the ground to Radius (all
    -- round, or within Arc) and a jump clears it; Pounce leaps onto the thief (enraged only).
    GuardianTag = "Guardian",
    EggTheft = {
        RespawnTime = 180, -- seconds a stand stays empty after its egg is secured
    },
    -- Yggdrasil's Hatching Altar (WorldBuilder.buildAltar, PetService): where every egg carried home is
    -- hatched. Centre is island-local (on the ground), Yaw turns its front (local +Z) toward the
    -- World Tree and the bridges. Stage: seconds an egg rests in the cradle before it breaks (one
    -- egg at a time per player: the client's Hatch button waits as long).
    HatchingAltar = { Island = "Yggdrasil", Centre = Vector3.new(100, -0.2, -130), Yaw = -1.4, Stage = 2.6 },
    -- the size of a stand's egg (and a carried one): studs per unit of its Blender model
    EggStudsPerUnit = 1.3,
    Guardians = {
        StoneLion = {
            DisplayName = "Awakened Stone Lion",
            Island = "Yggdrasil",
            Lair = Vector3.new(128, 0.4, -62),
            Facing = Vector3.new(0, 0.4, 0), -- toward the World Tree
            Eggs = { "BeginnerQiEgg", "SpiritBreezeEgg", "ElementalCoreEgg" },
            -- its eggs are the Egg Garden's (Yggdrasil's own stands): carried to the Hatching Altar
            SafeZone = { Altar = true, Radius = 12, Name = "Hatching Altar" }, -- round HatchingAltar.Centre
            SecureStones = 150,     -- Spirit Stones for securing its egg
            Element = "Earth",      -- the relic it drops when its egg is secured unlocks this element (Forge)
            MaxHealth = 1200,      -- a beginner's Qi Palm weakens it alone in ~108 strikes (about 50 seconds)
            WeakenedAt = 0.1,      -- share of health below which it falters and its stands' eggs can be taken
            HitRadius = 14,        -- its body round the chest
            EngageRadius = 24,
            LeashRadius = 60,      -- from the lair
            CalmAfter = 12,        -- seconds with nobody near before it heals and sleeps
            RespawnTime = 30,      -- seconds it rests (Resting) after an egg is secured; its stand: EggTheft
            DropTime = 30,         -- seconds a dropped egg waits for its thief
            WalkSpeed = 12,
            ChaseSpeed = 21,       -- below a beginner's run (22): dashes and its pounces decide it
            TurnSpeed = 140,       -- degrees per second
            Egg = { CarriedHeight = 2.6 }, -- carried over the thief's head
            WeakenedHint = "falters: take an egg from the Egg Garden and carry it to the Hatching Altar!",
            Stagger = 1.1,         -- seconds a knocked-back player is off their feet
            WeakenedSlowdown = 1.7, -- attack cooldown multiplier while weakened
            Attacks = {
                -- a forepaw slams
                Slam = { Kind = "Sweep", Range = 24, Arc = 55, WindUp = 0.75, Cooldown = 2.6, Knockback = 45 },
                Roar = { Kind = "Wave", Radius = 44, WaveSpeed = 34, WindUp = 1.1, Cooldown = 8, Knockback = 40 },
                Pounce = { Kind = "Pounce", MinRange = 16, MaxRange = 46, WindUp = 0.6, Air = 0.95, Height = 9, Cooldown = 4.5, Radius = 12, Knockback = 55 },
            },
        },
        MantisSage = {
            DisplayName = "Bamboo Mantis Sage",
            Island = "JadeGrove",
            Lair = Vector3.new(0, 0.6, 0),      -- the middle of the Mantis Arena, its three egg stands behind it
            Facing = Vector3.new(81.7, 0.6, 96.4), -- toward the Grove Gate, where challengers arrive
            Eggs = { "JadeSpiritEgg", "BloomwoodEgg", "AncientGroveEgg" },
            SafeZone = { Island = "Yggdrasil", Name = "Yggdrasil" },   -- home across the bridge: secured on setting foot on the hub
            SecureStones = 600,     -- Spirit Stones for securing its egg
            Element = "Wind",
            MaxHealth = 2000,      -- a Qi Gatherer's palm (11 a strike) weakens it alone in ~165 strikes
            WeakenedAt = 0.1,
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
            Egg = { CarriedHeight = 2.6 },
            WeakenedHint = "lowers its blades: take an egg from the stands behind it and carry it home to Yggdrasil!",
            Stagger = 1.1,
            WeakenedSlowdown = 1.7,
            Attacks = {
                Scythe = { Kind = "Sweep", Range = 26, Arc = 65, WindUp = 0.6, Cooldown = 2.2, Knockback = 45 },
                BladeWave = { Kind = "Wave", Arc = 50, Radius = 46, WaveSpeed = 40, WindUp = 0.9, Cooldown = 6.5, Knockback = 40 },
                Leap = { Kind = "Pounce", MinRange = 16, MaxRange = 72, WindUp = 0.5, Air = 1.1, Height = 16, Cooldown = 4.2, Radius = 12, Knockback = 55 },
            },
        },
        EmberXuanwu = {
            DisplayName = "Ember Xuanwu",
            Island = "EmberPeak",
            -- the Cinder Arena's middle, set 3.5 studs toward the gate so its beak (29 studs ahead of
            -- its origin) clears the egg pedestals behind it when it turns to face them
            Lair = Vector3.new(0.6, 0.5, 3.4),
            Facing = Vector3.new(22.0, 0.5, 121.0), -- toward the Ember Gate, where challengers arrive
            Eggs = { "InfernoEgg", "MagmaHeartEgg", "PhoenixAshEgg" },
            SafeZone = { Island = "Yggdrasil", Name = "Yggdrasil" },   -- home across the bridge: secured on setting foot on the hub
            SecureStones = 1500,    -- Spirit Stones for securing its egg
            Element = "Fire",
            MaxHealth = 3200,      -- a Qi Awakener's starter sword (~24 a strike) weakens it alone in ~120 strikes
            WeakenedAt = 0.1,
            HitRadius = 15,        -- its shell
            EngageRadius = 28,     -- the egg pedestals stand just outside it (31)
            LeashRadius = 62,
            CalmAfter = 12,
            RespawnTime = 30,
            DropTime = 30,
            WalkSpeed = 9,
            ChaseSpeed = 20,       -- slow (a Qi Awakener runs 26): its charge decides the chase
            ChaseStop = 22,        -- it stops this far from the thief: its beak is 29 studs ahead of its origin
            TurnSpeed = 75,        -- a ponderous turn: those who circle it meet its quake
            TurnsToFace = true,
            Egg = { CarriedHeight = 2.6 },
            WeakenedHint = "sinks low: take an egg from the stands behind it and carry it home to Yggdrasil!",
            Stagger = 1.2,
            WeakenedSlowdown = 1.7,
            Attacks = {
                -- the serpent rears back over the volcano and strikes down at the ground before it
                SerpentLash = { Kind = "Sweep", Range = 30, Arc = 70, WindUp = 0.8, Cooldown = 2.8, Knockback = 50 },
                -- it rears onto its hind legs and stomps: a quake ring rolls out all round (jump it)
                Quake = { Kind = "Wave", Radius = 50, WaveSpeed = 30, WindUp = 1.3, Cooldown = 7.5, Knockback = 45 },
                -- a ground-shaking lunge, low and heavy
                Charge = { Kind = "Pounce", MinRange = 16, MaxRange = 56, WindUp = 0.9, Air = 1.0, Height = 3, Cooldown = 5, Radius = 15, Knockback = 60 },
            },
        },
        Tiangou = {
            DisplayName = "Tiangou the Moon-Eater",
            Called = "Tiangou",                    -- how messages name it (default: "The " .. DisplayName)
            Island = "MoonlitIsle",
            Lair = Vector3.new(0, 1, 14),          -- the middle of the Lunar Court, its egg pedestals behind it over the bay
            Facing = Vector3.new(-27, 1, 118.2),   -- toward the Crescent Arch, where challengers arrive
            Eggs = { "CelestialEgg", "AstralSanctumEgg", "HeavenlyThroneEgg" },
            SafeZone = { Island = "Yggdrasil", Name = "Yggdrasil" },   -- home across the bridge: secured on setting foot on the hub
            SecureStones = 4000,
            Element = "Frost",
            MaxHealth = 11000,     -- a Soul Awakening's Spirit Soul sword (~84 a strike) weakens it alone in ~118 strikes
            WeakenedAt = 0.1,
            HitRadius = 10,        -- its body from chest to haunch
            EngageRadius = 27,
            LeashRadius = 62,
            CalmAfter = 12,
            RespawnTime = 30,
            DropTime = 30,
            WalkSpeed = 14,
            ChaseSpeed = 27,       -- a hound: just below a Soul Awakening's run (30); its leaps decide the chase
            ChaseStop = 17,        -- its nose is 22 studs ahead of its origin
            TurnSpeed = 180,
            TurnsToFace = true,
            Egg = { CarriedHeight = 2.6 },
            WeakenedHint = "staggers: take an egg from the stands behind it and carry it home to Yggdrasil!",
            Stagger = 1.1,
            WeakenedSlowdown = 1.7,
            Attacks = {
                Bite = { Kind = "Sweep", Range = 25, Arc = 60, WindUp = 0.5, Cooldown = 2.0, Knockback = 50 },
                -- it howls at the sky and the eclipse flares: a ring of frost rolls out all round (jump it)
                EclipseHowl = { Kind = "Wave", Radius = 52, WaveSpeed = 36, WindUp = 1.0, Cooldown = 7, Knockback = 45 },
                -- long, high arcs: watch the sky
                MoonLeap = { Kind = "Pounce", MinRange = 18, MaxRange = 85, WindUp = 0.55, Air = 1.4, Height = 26, Cooldown = 4.2, Radius = 13, Knockback = 60 },
            },
        },
        Pangu = {
            DisplayName = "Pangu the World-Splitter",
            Called = "Pangu",
            Island = "OriginAbyss",
            Lair = Vector3.new(0, 0.8, 0),         -- the middle of the Void Court, its egg plinths behind him under the Thorn Crown
            Facing = Vector3.new(-85.8, 0.8, 122.8), -- toward the Gate of Descent, where challengers arrive
            Eggs = { "ForbiddenOriginEgg", "VoidRiftEgg", "PrimordialAbyssEgg" },
            SafeZone = { Island = "Yggdrasil", Name = "Yggdrasil" },   -- home across the bridge: secured on setting foot on the hub
            SecureStones = 12000,
            Element = "Void",
            MaxHealth = 24000,     -- a Divine Initiate's Divine sword (~180 a strike) weakens him alone in ~120 strikes
            WeakenedAt = 0.1,
            HitRadius = 8,         -- a titan on two legs: narrow at the ground
            EngageRadius = 26,
            LeashRadius = 62,
            CalmAfter = 12,
            RespawnTime = 30,
            DropTime = 30,
            WalkSpeed = 12,
            ChaseSpeed = 28,       -- just below a Divine Initiate's run (32): his leaps and his fissure decide it
            ChaseStop = 12,
            TurnSpeed = 110,
            TurnsToFace = true,
            Egg = { CarriedHeight = 2.6 },
            WeakenedHint = "sinks to one knee: take an egg from the stands behind him and carry it home to Yggdrasil!",
            Stagger = 1.2,
            WeakenedSlowdown = 1.6,
            Attacks = {
                AxeCleave = { Kind = "Sweep", Range = 30, Arc = 75, WindUp = 0.9, Cooldown = 2.6, Knockback = 60 },
                -- both hands on the axe, overhead, down: a fissure races straight ahead (jump it, or step aside)
                SkySplitter = { Kind = "Wave", Arc = 15, Radius = 70, WaveSpeed = 55, WindUp = 1.2, Cooldown = 6, Knockback = 55 },
                -- the cosmic egg raised high, the chaos in him bursts out all round (jump it)
                ChaosNova = { Kind = "Wave", Radius = 44, WaveSpeed = 32, WindUp = 1.4, Cooldown = 9, Knockback = 50 },
                TitanLeap = { Kind = "Pounce", MinRange = 20, MaxRange = 75, WindUp = 0.8, Air = 1.5, Height = 22, Cooldown = 5, Radius = 16, Knockback = 65 },
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
    -- a barrier at each island bridge: only players of its RankId pass
    BridgeBarrierTag = "QiBarrier",
    Relics = {
        { Id = "IslandRoot", DisplayName = "Root of the Island", QiReward = 300, RequiredRank = "QiInitiate", Element = "Wood" },
        { Id = "GroveHeart", DisplayName = "Grove Heart", QiReward = 800, RequiredRank = "QiGatherer", Element = "Wood" },
        { Id = "JadeSeed", DisplayName = "Jade Seed", QiReward = 800, RequiredRank = "QiGatherer", Element = "Wood" },
        { Id = "WhisperingSpring", DisplayName = "Whispering Spring", QiReward = 800, RequiredRank = "QiGatherer", Element = "Wood" },
        { Id = "EmberHeart", DisplayName = "Ember Heart", QiReward = 1500, RequiredRank = "QiAwakener", Element = "Fire" },
        { Id = "AshenSigil", DisplayName = "Ashen Sigil", QiReward = 1500, RequiredRank = "QiAwakener", Element = "Fire" },
        { Id = "CalderaCrown", DisplayName = "Caldera Crown", QiReward = 1500, RequiredRank = "QiAwakener", Element = "Fire" },
        { Id = "MoonMirror", DisplayName = "Moon Mirror", QiReward = 3000, RequiredRank = "FoundationInitiate", Element = "Frost" },
        { Id = "StarWell", DisplayName = "Star Well", QiReward = 3000, RequiredRank = "FoundationInitiate", Element = "Frost" },
        { Id = "OriginAltar", DisplayName = "Origin Altar", QiReward = 250000, RequiredRank = "DivineInitiate", Element = "Void" },
        { Id = "VoidShard", DisplayName = "Void Shard", QiReward = 1000000, RequiredRank = "VoidWalker", Element = "Void" },
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

    -- The System's first quests: a new player's guided path through the game's loop, one at a
    -- time, each with a small reward (QuestService checks them; the QUEST tracker shows them).
    -- Kind says what completes it: "Qi" (Qi at least Goal), "Equip" (a pet equipped), "Rank"
    -- (this rank reached), "Leap" (an air leap), "GuardianHit" (a strike on a guardian),
    -- "TakeEgg" (carrying a guardian's egg), "Hatch" (a pet hatched since the quest began).
    -- Existing saves start with them done (PlayerData migration 8); a player can skip them.
    Quests = {
        { Id = "Cultivate", Kind = "Qi", Goal = 100, Reward = 20, Title = "Gather Qi",
            Text = "Sit in meditation: press E, or tap CULTIVATE. Gather 100 Qi." },
        { Id = "Companion", Kind = "Equip", Reward = 20, Title = "Your First Companion",
            Text = "Open Pets and equip your Aqua Wisp. Equipped pets add to the Qi you gather." },
        { Id = "Breakthrough", Kind = "Rank", Goal = "QiGatherer", Reward = 40, Title = "Break Through",
            Text = "Gather 300 Qi, then press BREAK THROUGH to become a Qi Gatherer." },
        { Id = "Leap", Kind = "Leap", Reward = 20, Title = "Walk on Air",
            Text = "Jump, then jump again in mid-air: an air leap. Hold jump while falling to glide." },
        { Id = "Guardian", Kind = "GuardianHit", Reward = 30, Title = "The Stone Lion",
            Text = "Find the Awakened Stone Lion in the Egg Garden and strike it (click, or tap Strike)." },
        { Id = "Egg", Kind = "TakeEgg", Reward = 60, Title = "Steal an Egg",
            Text = "Weaken a guardian until it falters, then take an egg from its stands. It will chase you!" },
        { Id = "Hatch", Kind = "Hatch", Reward = 80, Title = "Hatch It",
            Text = "Carry the egg to the Hatching Altar and hatch it." },
    },

    MaxOwnedPets = 50,

    StarterPetIds = { "AquaWisp" },

    GrantDevTestPets = false,
    DevTestPetIds = { "EmberWyrm", "VoltFox", "GoldenKirin", "NineTailMoonfox", "OriginSerpent" },

    Eggs = {
        BeginnerQiEgg = {
            DisplayName = "Beginner Qi Egg",
            RequiredRank = "QiInitiate",
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
