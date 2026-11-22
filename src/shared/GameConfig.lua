-- The game's tuning in one table: cultivation, Qinggong, combat, weapons, Spirit Stones, guardians and egg theft, relics,
-- pets and eggs, the shop and passes. The design doc's tables are generated from it. Shared by server and client.
local GameConfig = {

    StartingQi = 0,

    CultivationQiReward = 10,
    CultivationInterval = 1,
    CultivationToggleCooldown = 1, -- also limits how often a client can make everyone rebuild its aura
    CultivationKeybind = Enum.KeyCode.E,

    -- The Training Ground on the Blossom Sanctuary (the owner, 2026-11-16: the hub's Qi Spring was removed and its +50% moved
    -- there): cultivating inside its kerb adds QiBonusPercent. QiService reads the ground's outline from
    -- Placements.BlossomSanctuary.TrainingGround (tools/blender/world/blossom_layout.py).
    TrainingStation = {
        DisplayName = "Blossom Sanctuary",
        QiBonusPercent = 50,
        Island = "BlossomSanctuary",
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
        -- Per rank. DashSpeed is studs/s while dashing; FlightSpeed is the sword's speed once SwordFlight.UnlockRank is reached
        -- (Ranks.getFlightSpeed: 0 below it, whatever the level says).
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
        -- A critical strike (the owner, November 11, 2026): any strike that lands has this Chance of striking Multiplier times as
        -- hard. The server rolls it (CombatService) and tells the clients, who only show it (CombatFx).
        Crit = { Chance = 0.1, Multiplier = 1.5 },
    },

    -- Weapons (src/server/Shop; the Blacksmith on Yggdrasil): a sword and a spear for every realm,
    -- sold from that realm on for Spirit Stones (shared/Shop.lua names them Sword<tier>, Spear<tier>).
    -- A strike's damage is the tier's Damage times the kind's DamageScale times the rank's power
    -- (Combat.powerOf). The sword strikes fast and wide; the spear slower, farther and harder, for
    -- the same damage over time. With none equipped a player strikes with the Qi Palm (Combat.Palm).
    -- Strikes within ComboWindow seconds of the last continue the weapon's combo. The spear's combo is a
    -- long straight thrust, then a sweeping slash (its Slash reach: shorter and much wider).
    WeaponKinds = {
        Sword = { Range = 12, Arc = 80, Cooldown = 0.55, DamageScale = 1, ComboWindow = 1.1 },
        Spear = { Range = 18, Arc = 35, Cooldown = 0.85, DamageScale = 0.85 / 0.55, ComboWindow = 1.7,
            Slash = { Range = 13, Arc = 85 } },
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
    StarterWeapon = "Sword1", -- given only once, to a save from before weapons (PlayerData migration 6); new players start with the Qi Palm
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
                Source = "the Awakened Stone Lion's egg and bring it home" },
            Wind = { DisplayName = "Wind", Color = Color3.fromRGB(30, 230, 190), Core = Color3.fromRGB(200, 255, 240),
                Source = "the Bamboo Mantis Sage's egg and bring it home" },
        },
    },

    -- Spirit Stones: the currency of the Blacksmith and Buy & Sell (Qi is never spent: ranks are
    -- reached by total Qi). Earned by selling pets and weapons, securing guardians' eggs
    -- (by the egg: Shop.eggStones) and a relic's first attunement (Shop.relicStones).
    SpiritStones = {
        -- a pet's worth: its rarity's value times RealmFactor per realm of its egg's required rank
        PetValue = { Common = 6, Uncommon = 12, Rare = 25, Epic = 50, Legendary = 110, Mythical = 250, Secret = 600, Divine = 1500 },
        RealmFactor = 2.6, -- as weapon prices climb
        WeaponRefund = 0.4, -- the share of its price a weapon sells back for
        -- the rewards' ladder (Shop.rankValue): a rank's value is the price of a weapon of its realm,
        -- rising smoothly between realms. An egg pays EggShare of its required rank's value when
        -- secured, a relic RelicShare of its own on first attunement, each at least MinReward
        EggShare = 0.25,
        -- and that share falls by EggShareFalloff for each realm past the first (release balance, 2026-11-12: from Spirit Soul on, an active
        -- thief earned 8 to 50 weapons' worth of stones per realm against one weapon needed, and stones stopped meaning anything; now 3 to 6)
        EggShareFalloff = 0.8,
        -- an egg's reference price (Shop.marketEggPrice), as a share of its required rank's value: 4 times what stealing (more past the
        -- first realm, EggShareFalloff) one pays. The Marketplace sold eggs at this price until it became the Auction House
        -- (2026-11-16); it is still what the Wandering Merchant's discounts are taken off. On average an egg's pet sells for less
        -- than this, so buying eggs to sell their pets loses stones (checked against every egg's pool, 2026-11-04; re-measured
        -- 2026-11-12 with the Luck pass: at most 0.88 of the price, the Primordial Abyss Egg. Re-check whenever pet values, pools,
        -- luck or discounts change)
        MarketEggShare = 1,
        RelicShare = 0.5,
        MinReward = 40,
        Max = 1e12,
    },

    -- The Auction House (the owner, 2026-11-16: the Market "should become a player-driven marketplace where players can buy and sell
    -- eligible items through auctions"; vault: Auction House Design 2026-11-16). One auction house for every server (server/Auction,
    -- shared/AuctionRules). Pets and weapons are listed for a starting bid and a duration; bids are Spirit Stones, taken at once and
    -- given back when someone bids higher; the top bid wins at the end. Values are multiples of the item's sell value (what Buy & Sell
    -- pays: Shop.petValue, Shop.weaponRefund).
    AuctionHouse = {
        MinRank = "CoreInitiate",   -- the rank that may use it (about an hour of play): no fresh alt account can use it at once
        MinAccountAgeDays = 3,      -- and a Roblox account at least this old
        Hours = { 1, 4, 12, 24 },   -- the durations a seller can pick
        MaxListings = 5,            -- listings a player may have at once
        MaxBidOn = 10,              -- listings a player may be bidding on at once
        ListingFee = { Share = 0.02, Min = 2 }, -- of the starting bid, paid when listing and kept even if nothing sells: stops list/cancel spam
        SaleTax = 0.1,              -- of the final price, taken from what the seller gets: a Spirit Stone sink
        StartFloor = 1,             -- the lowest starting bid: the item's sell value (selling at Buy & Sell pays that much anyway)
        StartCeiling = 20,          -- the highest starting bid, in sell values
        -- the highest bid allowed, in sell values: rare beasts may fetch a lot, but junk can't carry a fortune between accounts
        PriceCap = { Common = 10, Uncommon = 10, Rare = 15, Epic = 20, Legendary = 30, Mythical = 50, Secret = 100, Divine = 100, Weapon = 5 },
        -- and times these for a big pet (2026-11-17: a Colossal is 1 in 250), and times its mutation's Cap (PetRules.Mutations)
        SizeCap = { Large = 1.2, Giant = 1.5, Colossal = 2 },
        MinRaise = 0.05,            -- a new bid beats the top bid by at least this share (and at least 1 stone)
        SnipeWindow = 60,           -- seconds: a bid this close to the end...
        SnipeExtend = 60,           -- ...moves the end to this many seconds after it
        MaxExtension = 1800,        -- seconds past its first end an auction can be moved, at most
        Reach = 45,                 -- studs from the Auction House's prompt an action may be asked from
        PageSize = 8,               -- listings on one page of the window
    },

    -- Guardians (src/server/Guardians/GuardianService; design doc section 7). A guardian holds no
    -- egg: it guards its island's three egg stands (EggStands). Weakened below WeakenedAt, one of
    -- their eggs can be taken (if the thief's rank can hatch it) and carried to the SafeZone: its
    -- Island, a whole island (Yggdrasil, home across the bridge). A secured egg goes to the egg
    -- inventory and is hatched at the Hatching Altar; its stand shows a random one of Eggs after
    -- EggTheft.RespawnTime. Positions are island-local studs.
    -- Attack kinds: Sweep strikes in front (Range, Arc); Wave rolls along the ground to Radius (all
    -- round, or within Arc) and a jump clears it; Pounce leaps onto the thief (enraged only).
    GuardianTag = "Guardian",
    EggTheft = {
        RespawnTime = 180, -- seconds a stand stays empty after its egg is secured
        -- to take an egg a player must have dealt this share of what weakening its guardian takes, so
        -- nobody walks off with an egg someone else earned
        TakeShare = 0.1,
        RetakeCooldown = 30, -- seconds before a player whose egg went back can take another: no holding a guardian hostage
        SecureQiMinutes = 5, -- securing an egg pays this many minutes of cultivating (server/Cultivation/QiReward)
    },
    -- Yggdrasil's Hatching Altar (WorldBuilder.buildAltar, PetService): where every egg carried home is
    -- hatched. Centre is island-local (on the ground), Yaw turns its front (local +Z) toward the
    -- World Tree and the bridges. Stage: seconds an egg rests in the cradle before it breaks (one
    -- egg at a time per player: the client's Hatch button waits as long).
    HatchingAltar = { Island = "Yggdrasil", Centre = Vector3.new(0, 0.25, -178), Yaw = 0, Stage = 3.8 }, -- the Hatching Sanctum, on the north avenue between the Merchant and the Ring Road, facing the tree (the hub's redesign, 2026-11-15: hub_ground.SANCTUM). Stage: seconds to the crack, the length of the hatch cinematic
    -- the size of a stand's egg (and a carried one): studs per unit of its Blender model
    EggStudsPerUnit = 1.3,
    EggGlowTag = "GlowingEgg",
    -- Each egg's colour: its stand's ring and light, and its Highlight (src/client/World/EggGlow).
    EggGlow = {
        BeginnerQiEgg = Color3.fromRGB(50, 180, 255),
        SpiritBreezeEgg = Color3.fromRGB(90, 190, 255),
        ElementalCoreEgg = Color3.fromRGB(40, 220, 255),
        JadeSpiritEgg = Color3.fromRGB(40, 225, 120),
        BloomwoodEgg = Color3.fromRGB(255, 80, 180),
        AncientGroveEgg = Color3.fromRGB(150, 240, 40),
        InfernoEgg = Color3.fromRGB(255, 85, 15),
        MagmaHeartEgg = Color3.fromRGB(255, 120, 20),
        PhoenixAshEgg = Color3.fromRGB(255, 95, 20),
        CelestialEgg = Color3.fromRGB(70, 130, 255),
        AstralSanctumEgg = Color3.fromHex("643cff"),   -- bluer than it looks: Neon pales violet
        HeavenlyThroneEgg = Color3.fromRGB(255, 185, 40),
        ForbiddenOriginEgg = Color3.fromHex("643cff"),
        VoidRiftEgg = Color3.fromHex("3c64ff"),
        PrimordialAbyssEgg = Color3.fromHex("ff3cb4"),
    },
    Guardians = {
        StoneLion = {
            DisplayName = "Awakened Stone Lion",
            Island = "BeginnerIsle",
            Lair = Vector3.new(0, 0, 0),         -- the middle of the Lion Court, its three egg stands behind it
            Facing = Vector3.new(-99.6, 0, 26.4), -- toward the Lion Gate, where challengers arrive
            Eggs = { "BeginnerQiEgg", "SpiritBreezeEgg", "ElementalCoreEgg" },
            SafeZone = { Island = "Yggdrasil", Name = "Yggdrasil" },   -- home across the bridge: secured on setting foot on the hub
            Element = "Earth",      -- the relic it drops when its egg is secured unlocks this element (Forge)
            MaxHealth = 1200,      -- a beginner's Qi Palm weakens it alone in ~108 strikes (about 50 seconds)
            WeakenedAt = 0.1,      -- share of health below which it falters and its stands' eggs can be taken
            HitRadius = 14,        -- its body round the chest
            EngageRadius = 24,
            AwakenTime = 2.6,      -- seconds before its first blow: it rises from sitting and shakes its mane (default 1.6)
            LeashRadius = 60,      -- from the lair
            CalmAfter = 12,        -- seconds with nobody near before it heals and sleeps
            RespawnTime = 30,      -- its cooldown: seconds from an egg's secure until it can be fought and robbed again (it rests at its lair, Resting; longer while all its stands are empty); its stand: EggTheft
            DropTime = 30,         -- seconds a dropped egg waits for its thief
            WalkSpeed = 12,
            ChaseSpeed = 21,       -- below a beginner's run (22): dashes and its pounces decide it
            TurnSpeed = 140,       -- degrees per second
            Egg = { CarriedHeight = 2.6 }, -- its height, carried in the thief's arms
            WeakenedHint = "is weak! Take an egg from the stands behind it and carry it home to Yggdrasil!",
            Stagger = 0.8,         -- seconds a knocked-back player is off their feet (softer on the first two guardians: a beginner mustn't spend the fight walking back)
            KnockGrace = 4,        -- seconds after a knock in which its blows can't knock the same player again (default 0.6)
            WeakenedSlowdown = 1.7, -- attack cooldown multiplier while weakened
            Attacks = {
                -- a forepaw slams
                Slam = { Kind = "Sweep", Range = 24, Arc = 55, WindUp = 0.75, Cooldown = 2.6, Knockback = 28 },
                Roar = { Kind = "Wave", Radius = 44, WaveSpeed = 34, WindUp = 1.1, Cooldown = 8, Knockback = 26 },
                Pounce = { Kind = "Pounce", MinRange = 16, MaxRange = 46, WindUp = 0.6, Air = 0.95, Height = 9, Cooldown = 4.5, Radius = 12, Knockback = 34 },
            },
        },
        MantisSage = {
            DisplayName = "Bamboo Mantis Sage",
            Island = "JadeGrove",
            Lair = Vector3.new(0, 0.6, 0),      -- the middle of the Mantis Arena, its three egg stands behind it
            Facing = Vector3.new(81.7, 0.6, 96.4), -- toward the Grove Gate, where challengers arrive
            Eggs = { "JadeSpiritEgg", "BloomwoodEgg", "AncientGroveEgg" },
            SafeZone = { Island = "Yggdrasil", Name = "Yggdrasil" },   -- home across the bridge: secured on setting foot on the hub
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
            WeakenedHint = "drops its blades! Take an egg from the stands behind it and carry it home to Yggdrasil!",
            Stagger = 0.8,
            KnockGrace = 3.5,
            WeakenedSlowdown = 1.7,
            Attacks = {
                Scythe = { Kind = "Sweep", Range = 26, Arc = 65, WindUp = 0.6, Cooldown = 2.2, Knockback = 28 },
                BladeWave = { Kind = "Wave", Arc = 50, Radius = 46, WaveSpeed = 40, WindUp = 0.9, Cooldown = 6.5, Knockback = 26 },
                Leap = { Kind = "Pounce", MinRange = 16, MaxRange = 72, WindUp = 0.5, Air = 1.1, Height = 16, Cooldown = 4.2, Radius = 12, Knockback = 34 },
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
            WeakenedHint = "is worn out! Take an egg from the stands behind it and carry it home to Yggdrasil!",
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
            WeakenedHint = "is weak! Take an egg from the stands behind it and carry it home to Yggdrasil!",
            Stagger = 1.1,
            WeakenedSlowdown = 1.7,
            Attacks = {
                Bite = { Kind = "Sweep", Range = 25, Arc = 60, WindUp = 0.5, Cooldown = 2.0, Knockback = 50 },
                -- it howls at the sky and the eclipse flares: a ring of frost rolls out all round (jump it)
                EclipseHowl = { Kind = "Wave", Radius = 52, WaveSpeed = 36, WindUp = 1.0, Cooldown = 7, Knockback = 45 },
                -- long, low bounds: about one body height off the ground (the owner: 26 "jumps too high")
                MoonLeap = { Kind = "Pounce", MinRange = 18, MaxRange = 85, WindUp = 0.55, Air = 1.2, Height = 12, Cooldown = 4.2, Radius = 13, Knockback = 60 },
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
            WeakenedHint = "falls to one knee! Take an egg from the stands behind him and carry it home to Yggdrasil!",
            Stagger = 1.2,
            WeakenedSlowdown = 1.6,
            Attacks = {
                AxeCleave = { Kind = "Sweep", Range = 30, Arc = 75, WindUp = 0.9, Cooldown = 2.6, Knockback = 60 },
                -- both hands on the axe, overhead, down: a fissure races straight ahead (jump it, or step aside)
                SkySplitter = { Kind = "Wave", Arc = 15, Radius = 70, WaveSpeed = 55, WindUp = 1.2, Cooldown = 6, Knockback = 55 },
                -- the cosmic egg raised high, the chaos in him bursts out all round (jump it)
                ChaosNova = { Kind = "Wave", Radius = 44, WaveSpeed = 32, WindUp = 1.4, Cooldown = 9, Knockback = 50 },
                TitanLeap = { Kind = "Pounce", MinRange = 20, MaxRange = 75, WindUp = 0.8, Air = 1.5, Height = 14, Cooldown = 5, Radius = 16, Knockback = 65 },
            },
        },
    },

    -- Sword flight (src/server/Qinggong/FlightService), from UnlockRank on every device (keyboard, gamepad and touch alike:
    -- the server refuses a take-off below it). The owner, 2026-11-17: "flight is locked for all platforms until the player
    -- reaches Realm 6" (the Immortal Realm; it was Foundation Initiate before). Drains stamina (Cost per second while moving,
    -- HoverCost while still) and needs MinStamina to take off. Qi barriers still hold: flight never reaches an island above the
    -- rider's rank.
    SwordFlight = {
        UnlockRank = "LesserImmortal",
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
        { Id = "IslandRoot", DisplayName = "Root of the Island", QiReward = 300, RequiredRank = "QiInitiate", Element = "Wood", Reach = 16 }, -- Reach: its prompt's studs (default 12). The rebuilt hub's cradle roots close round it, so it is attuned from the last root shelf, 13 studs off (2026-11-12)
        { Id = "GroveHeart", DisplayName = "Grove Heart", QiReward = 800, RequiredRank = "QiGatherer", Element = "Wood" },
        { Id = "JadeSeed", DisplayName = "Jade Seed", QiReward = 800, RequiredRank = "QiGatherer", Element = "Wood" },
        { Id = "WhisperingSpring", DisplayName = "Whispering Spring", QiReward = 800, RequiredRank = "QiGatherer", Element = "Wood" },
        { Id = "EmberHeart", DisplayName = "Ember Heart", QiReward = 1500, RequiredRank = "QiAwakener", Element = "Fire" },
        { Id = "AshenSigil", DisplayName = "Ashen Sigil", QiReward = 1500, RequiredRank = "QiAwakener", Element = "Fire" },
        { Id = "CalderaCrown", DisplayName = "Caldera Crown", QiReward = 1500, RequiredRank = "QiAwakener", Element = "Fire" },
        { Id = "MoonMirror", DisplayName = "Moon Mirror", QiReward = 20000, RequiredRank = "SoulAwakening", Element = "Frost" },
        { Id = "StarWell", DisplayName = "Star Well", QiReward = 20000, RequiredRank = "SoulAwakening", Element = "Frost" },
        { Id = "OriginAltar", DisplayName = "Origin Altar", QiReward = 250000, RequiredRank = "DivineInitiate", Element = "Void" },
        { Id = "VoidShard", DisplayName = "Void Shard", QiReward = 1000000, RequiredRank = "VoidWalker", Element = "Void" },
    },

    StartingRank = "Qi Initiate",

    Ranks = {
        -- (every QiRequired raised 2026-11-12 for the release balance: 2x at the start tapering to 1.5x at Soul Awakening and after)
        -- QiMultiplier (the balance of 2026-11-16; the owner: "player should be able to reach max realm within 5 days if free to play",
        -- then Qi passes capped at 4x plus timed boosts): x1 for the first three realms, x2 at Spirit Soul, then about 2.3x a realm
        -- (5, 12, 30, 70, 160, 400, 900, 2000; it doubled up to 512 before). With the egg stands' fix (EggStands.respawn) a free player
        -- who plays well reaches Eternal Origin in about 5 days at 4 hours a day (tools/balance/progression_sim.py). The thresholds
        -- were left as they were, so no save's rank moves (PlayerData lowers a rank whose Qi is under its QiRequired).
        { Id = "QiInitiate", Name = "Qi Initiate", Realm = "Qi Awakening", Level = 1, QiRequired = 0, AuraTier = 1, QiMultiplier = 1 },
        { Id = "QiGatherer", Name = "Qi Gatherer", Realm = "Qi Awakening", Level = 2, QiRequired = 600, AuraTier = 1, QiMultiplier = 1 },
        { Id = "QiCondenser", Name = "Qi Condenser", Realm = "Qi Awakening", Level = 3, QiRequired = 1700, AuraTier = 2, QiMultiplier = 1 },
        { Id = "QiAdept", Name = "Qi Adept", Realm = "Qi Awakening", Level = 4, QiRequired = 3800, AuraTier = 2, QiMultiplier = 1 },
        { Id = "QiAwakener", Name = "Qi Awakener", Realm = "Qi Awakening", Level = 5, QiRequired = 7500, AuraTier = 2, QiMultiplier = 1 },

        { Id = "FoundationInitiate", Name = "Foundation Initiate", Realm = "Qi Foundation", Level = 1, QiRequired = 12000, AuraTier = 3, QiMultiplier = 1 },
        { Id = "FoundationBuilder", Name = "Foundation Builder", Realm = "Qi Foundation", Level = 2, QiRequired = 18000, AuraTier = 3, QiMultiplier = 1 },
        { Id = "FoundationAdept", Name = "Foundation Adept", Realm = "Qi Foundation", Level = 3, QiRequired = 26000, AuraTier = 3, QiMultiplier = 1 },
        { Id = "FoundationMaster", Name = "Foundation Master", Realm = "Qi Foundation", Level = 4, QiRequired = 36000, AuraTier = 4, QiMultiplier = 1 },
        { Id = "PerfectFoundation", Name = "Perfect Foundation", Realm = "Qi Foundation", Level = 5, QiRequired = 49000, AuraTier = 4, QiMultiplier = 1 },

        { Id = "CoreInitiate", Name = "Core Initiate", Realm = "Spirit Core", Level = 1, QiRequired = 67000, AuraTier = 4, QiMultiplier = 1 },
        { Id = "CoreFormation", Name = "Core Formation", Realm = "Spirit Core", Level = 2, QiRequired = 90000, AuraTier = 5, QiMultiplier = 1 },
        { Id = "CoreAdept", Name = "Core Adept", Realm = "Spirit Core", Level = 3, QiRequired = 120000, AuraTier = 5, QiMultiplier = 1 },
        { Id = "CoreMaster", Name = "Core Master", Realm = "Spirit Core", Level = 4, QiRequired = 150000, AuraTier = 5, QiMultiplier = 1 },
        { Id = "GoldenSpiritCore", Name = "Golden Spirit Core", Realm = "Spirit Core", Level = 5, QiRequired = 180000, AuraTier = 5, QiMultiplier = 1 },
        { Id = "SoulAwakening", Name = "Soul Awakening", Realm = "Spirit Soul", Level = 1, QiRequired = 220000, AuraTier = 5, QiMultiplier = 2 },
        { Id = "SoulTempering", Name = "Soul Tempering", Realm = "Spirit Soul", Level = 2, QiRequired = 350000, AuraTier = 5, QiMultiplier = 2 },
        { Id = "SoulRefinement", Name = "Soul Refinement", Realm = "Spirit Soul", Level = 3, QiRequired = 500000, AuraTier = 5, QiMultiplier = 2 },
        { Id = "SoulManifestation", Name = "Soul Manifestation", Realm = "Spirit Soul", Level = 4, QiRequired = 680000, AuraTier = 5, QiMultiplier = 2 },
        { Id = "SpiritSoulMaster", Name = "Spirit Soul Master", Realm = "Spirit Soul", Level = 5, QiRequired = 870000, AuraTier = 5, QiMultiplier = 2 },

        { Id = "AscendantInitiate", Name = "Ascendant Initiate", Realm = "Ascendant Realm", Level = 1, QiRequired = 1000000, AuraTier = 5, QiMultiplier = 5 },
        { Id = "SkyAscendant", Name = "Sky Ascendant", Realm = "Ascendant Realm", Level = 2, QiRequired = 1500000, AuraTier = 5, QiMultiplier = 5 },
        { Id = "HeavenlyAdept", Name = "Heavenly Adept", Realm = "Ascendant Realm", Level = 3, QiRequired = 2000000, AuraTier = 5, QiMultiplier = 5 },
        { Id = "CelestialMaster", Name = "Celestial Master", Realm = "Ascendant Realm", Level = 4, QiRequired = 2600000, AuraTier = 5, QiMultiplier = 5 },
        { Id = "AscendantSovereign", Name = "Ascendant Sovereign", Realm = "Ascendant Realm", Level = 5, QiRequired = 3300000, AuraTier = 5, QiMultiplier = 5 },

        { Id = "LesserImmortal", Name = "Lesser Immortal", Realm = "Immortal Realm", Level = 1, QiRequired = 3800000, AuraTier = 5, QiMultiplier = 12 },
        { Id = "TrueImmortal", Name = "True Immortal", Realm = "Immortal Realm", Level = 2, QiRequired = 5200000, AuraTier = 5, QiMultiplier = 12 },
        { Id = "GoldenImmortal", Name = "Golden Immortal", Realm = "Immortal Realm", Level = 3, QiRequired = 6900000, AuraTier = 5, QiMultiplier = 12 },
        { Id = "ImmortalLord", Name = "Immortal Lord", Realm = "Immortal Realm", Level = 4, QiRequired = 8900000, AuraTier = 5, QiMultiplier = 12 },
        { Id = "ImmortalEmperor", Name = "Immortal Emperor", Realm = "Immortal Realm", Level = 5, QiRequired = 11000000, AuraTier = 5, QiMultiplier = 12 },

        { Id = "DivineInitiate", Name = "Divine Initiate", Realm = "Divine Realm", Level = 1, QiRequired = 13000000, AuraTier = 5, QiMultiplier = 30 },
        { Id = "DivineAdept", Name = "Divine Adept", Realm = "Divine Realm", Level = 2, QiRequired = 17000000, AuraTier = 5, QiMultiplier = 30 },
        { Id = "DivineLord", Name = "Divine Lord", Realm = "Divine Realm", Level = 3, QiRequired = 22000000, AuraTier = 5, QiMultiplier = 30 },
        { Id = "DivineKing", Name = "Divine King", Realm = "Divine Realm", Level = 4, QiRequired = 28000000, AuraTier = 5, QiMultiplier = 30 },
        { Id = "DivineEmperor", Name = "Divine Emperor", Realm = "Divine Realm", Level = 5, QiRequired = 35000000, AuraTier = 5, QiMultiplier = 30 },

        { Id = "StarInitiate", Name = "Star Initiate", Realm = "Cosmic Realm", Level = 1, QiRequired = 39000000, AuraTier = 5, QiMultiplier = 70 },
        { Id = "StarForger", Name = "Star Forger", Realm = "Cosmic Realm", Level = 2, QiRequired = 52000000, AuraTier = 5, QiMultiplier = 70 },
        { Id = "NebulaMaster", Name = "Nebula Master", Realm = "Cosmic Realm", Level = 3, QiRequired = 66000000, AuraTier = 5, QiMultiplier = 70 },
        { Id = "GalaxySovereign", Name = "Galaxy Sovereign", Realm = "Cosmic Realm", Level = 4, QiRequired = 83000000, AuraTier = 5, QiMultiplier = 70 },
        { Id = "CosmicEmperor", Name = "Cosmic Emperor", Realm = "Cosmic Realm", Level = 5, QiRequired = 100000000, AuraTier = 5, QiMultiplier = 70 },

        { Id = "VoidWalker", Name = "Void Walker", Realm = "Void Realm", Level = 1, QiRequired = 110000000, AuraTier = 5, QiMultiplier = 160 },
        { Id = "VoidShaper", Name = "Void Shaper", Realm = "Void Realm", Level = 2, QiRequired = 150000000, AuraTier = 5, QiMultiplier = 160 },
        { Id = "VoidMaster", Name = "Void Master", Realm = "Void Realm", Level = 3, QiRequired = 190000000, AuraTier = 5, QiMultiplier = 160 },
        { Id = "SpaceTimeLord", Name = "Space-Time Lord", Realm = "Void Realm", Level = 4, QiRequired = 240000000, AuraTier = 5, QiMultiplier = 160 },
        { Id = "VoidSovereign", Name = "Void Sovereign", Realm = "Void Realm", Level = 5, QiRequired = 290000000, AuraTier = 5, QiMultiplier = 160 },

        { Id = "DaoSeeker", Name = "Dao Seeker", Realm = "Heavenly Dao", Level = 1, QiRequired = 330000000, AuraTier = 5, QiMultiplier = 400 },
        { Id = "DaoAdept", Name = "Dao Adept", Realm = "Heavenly Dao", Level = 2, QiRequired = 420000000, AuraTier = 5, QiMultiplier = 400 },
        { Id = "DaoMaster", Name = "Dao Master", Realm = "Heavenly Dao", Level = 3, QiRequired = 540000000, AuraTier = 5, QiMultiplier = 400 },
        { Id = "HeavenlyLawkeeper", Name = "Heavenly Lawkeeper", Realm = "Heavenly Dao", Level = 4, QiRequired = 660000000, AuraTier = 5, QiMultiplier = 400 },
        { Id = "DaoSovereign", Name = "Dao Sovereign", Realm = "Heavenly Dao", Level = 5, QiRequired = 810000000, AuraTier = 5, QiMultiplier = 400 },

        { Id = "PrimordialAwakening", Name = "Primordial Awakening", Realm = "Primordial Realm", Level = 1, QiRequired = 910000000, AuraTier = 5, QiMultiplier = 900 },
        { Id = "AncientOrigin", Name = "Ancient Origin", Realm = "Primordial Realm", Level = 2, QiRequired = 1200000000, AuraTier = 5, QiMultiplier = 900 },
        { Id = "PrimordialLord", Name = "Primordial Lord", Realm = "Primordial Realm", Level = 3, QiRequired = 1500000000, AuraTier = 5, QiMultiplier = 900 },
        { Id = "OriginEmperor", Name = "Origin Emperor", Realm = "Primordial Realm", Level = 4, QiRequired = 1900000000, AuraTier = 5, QiMultiplier = 900 },
        { Id = "PrimordialSovereign", Name = "Primordial Sovereign", Realm = "Primordial Realm", Level = 5, QiRequired = 2300000000, AuraTier = 5, QiMultiplier = 900 },

        { Id = "EternalInitiate", Name = "Eternal Initiate", Realm = "Eternal Transcendence", Level = 1, QiRequired = 2600000000, AuraTier = 5, QiMultiplier = 2000 },
        { Id = "EternalAscendant", Name = "Eternal Ascendant", Realm = "Eternal Transcendence", Level = 2, QiRequired = 3300000000, AuraTier = 5, QiMultiplier = 2000 },
        { Id = "InfinityMaster", Name = "Infinity Master", Realm = "Eternal Transcendence", Level = 3, QiRequired = 4200000000, AuraTier = 5, QiMultiplier = 2000 },
        { Id = "TranscendentOne", Name = "Transcendent One", Realm = "Eternal Transcendence", Level = 4, QiRequired = 5100000000, AuraTier = 5, QiMultiplier = 2000 },
        { Id = "EternalOrigin", Name = "Eternal Origin", Realm = "Eternal Transcendence", Level = 5, QiRequired = 6300000000, AuraTier = 5, QiMultiplier = 2000 },
    },

    MaxEquippedPets = 3,

    -- A pet has three separate numbers, and none is worked out from another, so each egg can be balanced on its own:
    --   Rarity       what the pet is classed as, here: its colour, its sell value, what's protected from selling
    --   QiBonus      how much it adds to cultivation while equipped, in percent (here, before its level)
    --   HatchChance  how likely one egg is to hatch it, in percent (in GameConfig.Eggs, per egg: the same pet can differ from egg to egg)
    Pets = {
        AquaWisp = { DisplayName = "Aqua Wisp", Rarity = "Common", Theme = "Water", QiBonus = 10 },
        EmberWyrm = { DisplayName = "Ember Wyrm", Rarity = "Uncommon", Theme = "Fire", QiBonus = 20 },
        LunarHopper = { DisplayName = "Lunar Hopper", Rarity = "Rare", Theme = "Moonlight", QiBonus = 35 },
        VoltFox = { DisplayName = "Volt Fox", Rarity = "Epic", Theme = "Lightning", QiBonus = 50 },
        GoldenKirin = { DisplayName = "Golden Kirin", Rarity = "Legendary", Theme = "Nature", QiBonus = 60 },
        AstralWhale = { DisplayName = "Astral Whale", Rarity = "Mythical", Theme = "Cosmic", QiBonus = 100 },
        NineTailMoonfox = { DisplayName = "Nine-Tail Moonfox", Rarity = "Mythical", Theme = "Moon", QiBonus = 120, ValueRealm = 5 }, -- the Exclusive Egg's Mythical (the owner, 2026-11-15; Secret until then)
        -- the Exclusive Egg's own beasts (the owner, 2026-11-13). ValueRealm: they sell as beasts of the Ascendant Realm (Shop.petValue), not of
        -- the first realm their egg (open to every rank) would say
        EclipseDreadwing = { DisplayName = "Eclipse Dreadwing", Rarity = "Divine", Theme = "Void and eclipse", QiBonus = 300, ValueRealm = 5 }, -- the Exclusive Egg's Divine (the owner, 2026-11-15; Mythical until then)
        Crysalith = { DisplayName = "Crysalith", Rarity = "Secret", Theme = "Frost and crystal", QiBonus = 180, ValueRealm = 5 }, -- the Exclusive Egg's Secret (the owner, 2026-11-15; Divine until then)
        OriginSerpent = { DisplayName = "Origin Serpent", Rarity = "Secret", Theme = "Primordial", QiBonus = 150 },

        MossGolem = { DisplayName = "Moss Golem", Rarity = "Common", Theme = "Earth", QiBonus = 10 },
        MyceliumSprite = { DisplayName = "Mycelium Sprite", Rarity = "Uncommon", Theme = "Forest", QiBonus = 20 },
        JadeSpiritPanda = { DisplayName = "Jade Spirit Panda", Rarity = "Rare", Theme = "Nature", QiBonus = 35 },
        JadeAntlerDeer = { DisplayName = "Jade Antler Deer", Rarity = "Epic", Theme = "Nature", QiBonus = 50 },

        MagmaCub = { DisplayName = "Magma Cub", Rarity = "Common", Theme = "Lava", QiBonus = 10 },
        SunscaleDragon = { DisplayName = "Sunscale Dragon", Rarity = "Legendary", Theme = "Solar", QiBonus = 60 },
        DawnPhoenix = { DisplayName = "Dawn Phoenix", Rarity = "Mythical", Theme = "Fire", QiBonus = 110 }, -- Mythical since 2026-11-16 (the owner's call, with its remake)
        WindSprite = { DisplayName = "Wind Sprite", Rarity = "Common", Theme = "Wind", QiBonus = 10 },
        CloudSheep = { DisplayName = "Cloud Sheep", Rarity = "Uncommon", Theme = "Clouds", QiBonus = 25 },
        SpiritCrane = { DisplayName = "Spirit Crane", Rarity = "Rare", Theme = "Spiritual energy", QiBonus = 40 },
        AzureSkyDragon = { DisplayName = "Azure Sky Dragon", Rarity = "Epic", Theme = "Wind and sky", QiBonus = 55 },
        StormhornKirin = { DisplayName = "Stormhorn Kirin", Rarity = "Legendary", Theme = "Storms", QiBonus = 70 },

        GlacierPuff = { DisplayName = "Glacier Puff", Rarity = "Common", Theme = "Ice", QiBonus = 15 },
        StormBumblebee = { DisplayName = "Storm Bumblebee", Rarity = "Uncommon", Theme = "Electricity", QiBonus = 25 }, -- (replaced the Thunder Jelly, November 9, 2026: PlayerData migration 12)
        CrystalBeetle = { DisplayName = "Crystal Beetle", Rarity = "Rare", Theme = "Crystal", QiBonus = 45 },
        GravityImp = { DisplayName = "Gravity Imp", Rarity = "Epic", Theme = "Gravity", QiBonus = 65 },
        ThunderclawDrake = { DisplayName = "Thunderclaw Drake", Rarity = "Legendary", Theme = "Lightning", QiBonus = 80 },
        FrostfangSerpent = { DisplayName = "Frostfang Serpent", Rarity = "Mythical", Theme = "Ice", QiBonus = 130 },

        DreamMoth = { DisplayName = "Dream Moth", Rarity = "Common", Theme = "Dreams", QiBonus = 15 },
        CrystalSnail = { DisplayName = "Crystal Snail", Rarity = "Uncommon", Theme = "Crystals", QiBonus = 30 },
        PrismArmadillo = { DisplayName = "Prism Armadillo", Rarity = "Rare", Theme = "Crystals", QiBonus = 50 },
        LanternWarden = { DisplayName = "Lantern Warden", Rarity = "Epic", Theme = "Light", QiBonus = 70 },
        JadeWyrmTurtle = { DisplayName = "Jade Wyrm Turtle", Rarity = "Legendary", Theme = "Earth", QiBonus = 85 },

        EchoBat = { DisplayName = "Echo Bat", Rarity = "Common", Theme = "Sound", QiBonus = 20 },
        QiClockworkFinch = { DisplayName = "Qi Clockwork Finch", Rarity = "Uncommon", Theme = "Magical machinery", QiBonus = 38 },
        MoonfangTiger = { DisplayName = "Moonfang Tiger", Rarity = "Rare", Theme = "Moonlight", QiBonus = 62 },
        ThousandEyedGuardian = { DisplayName = "Lotus Elephant", Rarity = "Epic", Theme = "Rain and lotus", QiBonus = 80 }, -- (was the Thousand-Eyed Guardian; the id kept for saves)
        NinefoldSpiritSerpent = { DisplayName = "Ninefold Spirit Serpent", Rarity = "Legendary", Theme = "Spiritual energy", QiBonus = 95 },
        WorldrootColossus = { DisplayName = "Worldroot Colossus", Rarity = "Mythical", Theme = "Ancient nature", QiBonus = 160 },

        SandPhantom = { DisplayName = "Sand Phantom", Rarity = "Common", Theme = "Sand", QiBonus = 20 },
        SolarButterfly = { DisplayName = "Solar Butterfly", Rarity = "Uncommon", Theme = "Solar energy", QiBonus = 38 },
        ObsidianGuardian = { DisplayName = "Obsidian Guardian", Rarity = "Rare", Theme = "Darkness and crystal", QiBonus = 55 },
        GoldenManeLion = { DisplayName = "Golden Mane Lion", Rarity = "Epic", Theme = "Solar energy", QiBonus = 80 },
        BonefireDragon = { DisplayName = "Bonefire Dragon", Rarity = "Legendary", Theme = "Spectral fire", QiBonus = 100 },

        DreadfangCerberus = { DisplayName = "Dreadfang Cerberus", Rarity = "Epic", Theme = "Shadow", QiBonus = 95 },
        PrismaticPhoenix = { DisplayName = "Prismatic Phoenix", Rarity = "Mythical", Theme = "Rainbow energy", QiBonus = 170 },

        StarfallFox = { DisplayName = "Starfall Fox", Rarity = "Common", Theme = "Stars", QiBonus = 30 },
        CosmicJellyfish = { DisplayName = "Cosmic Jellyfish", Rarity = "Uncommon", Theme = "Nebulae", QiBonus = 55 },
        NebulaOwl = { DisplayName = "Nebula Owl", Rarity = "Rare", Theme = "Cosmic energy", QiBonus = 80 },
        CelestialSnowLeopard = { DisplayName = "Celestial Snow Leopard", Rarity = "Epic", Theme = "Ice and celestial energy", QiBonus = 95 },
        CometStag = { DisplayName = "Comet Stag", Rarity = "Legendary", Theme = "Comets", QiBonus = 115 },
        CelestialPearlDragon = { DisplayName = "Celestial Pearl Dragon", Rarity = "Mythical", Theme = "Celestial energy", QiBonus = 190 },

        EclipseCat = { DisplayName = "Eclipse Cat", Rarity = "Epic", Theme = "Darkness and eclipses", QiBonus = 110 },
        TimekeeperTortoise = { DisplayName = "Timekeeper Tortoise", Rarity = "Legendary", Theme = "Time", QiBonus = 130 },
        GalaxyManta = { DisplayName = "Galaxy Manta", Rarity = "Mythical", Theme = "Cosmic energy", QiBonus = 220 },

        Shadowcoil = { DisplayName = "Shadowcoil", Rarity = "Rare", Theme = "Shadow", QiBonus = 100 },
        RuneSphinx = { DisplayName = "Rune Sphinx", Rarity = "Legendary", Theme = "Ancient magic", QiBonus = 170 },
        ThousandYearDreamEater = { DisplayName = "Thousand-Year Dream Eater", Rarity = "Mythical", Theme = "Dreams", QiBonus = 280 },
        TheNamelessOne = { DisplayName = "The Nameless One", Rarity = "Secret", Theme = "Unknown cosmic energy", QiBonus = 420 },

        HeavenbreakerApe = { DisplayName = "Heavenbreaker Ape", Rarity = "Legendary", Theme = "Heavenly power", QiBonus = 205 },
        VoidscaleHydra = { DisplayName = "Voidscale Hydra", Rarity = "Mythical", Theme = "Void", QiBonus = 340 },

        EternalClockworkDragon = { DisplayName = "Eternal Clockwork Dragon", Rarity = "Secret", Theme = "Time", QiBonus = 600 },
        AbyssAnomalocaris = { DisplayName = "Abyss Anomalocaris", Rarity = "Legendary", Theme = "Primordial seas", QiBonus = 230,
            -- sells as a realm-10 pet (Shop.petValue): its only egg is two realms past the egg before it, so at realm 11 it sold for
            -- 1.55M, more than a Primordial weapon, and its egg resold for 88% of its reference price (Shop.marketEggPrice) (others about half). 2026-11-13
            ValueRealm = 10 },
    },

    PetRarityColors = {
        Common = Color3.fromRGB(220, 225, 235),
        Uncommon = Color3.fromRGB(120, 230, 140),
        Rare = Color3.fromRGB(120, 200, 255),
        Epic = Color3.fromRGB(190, 140, 255),
        Legendary = Color3.fromRGB(255, 200, 70),
        Mythical = Color3.fromRGB(255, 110, 160),
        Secret = Color3.fromRGB(255, 255, 255),
        Divine = Color3.fromRGB(110, 240, 255), -- above Secret (the owner, 2026-11-13: the Exclusive Egg's top prize)
    },

    -- The quests: a player's guided path, one at a time, each with a reward (QuestService
    -- checks them; the QUEST tracker shows them). Kind says what completes it: "Qi" (Qi at least Goal),
    -- "Equip" (a pet equipped), "Rank" (this rank reached), "Leap" (an air leap), "GuardianHit" (a strike
    -- on a guardian), "TakeEgg" (carrying a guardian's egg), "Hatch" (a pet hatched since the quest
    -- began), "BuyWeapon" (a weapon bought, or two owned), "Relic" (this relic found), "Visit" (standing
    -- on this island), "Secure" (this guardian's egg secured), "Forge" (a forged weapon owned). Saves
    -- from before the quests skip them all (PlayerData migration 8), and a player can too.
    Quests = {
        { Id = "Cultivate", Kind = "Qi", Goal = 100, Reward = 20, Title = "Gather Qi",
            Text = "Press E to cultivate (on a phone, tap the lotus button). Gather 100 Qi." },
        { Id = "Companion", Kind = "Equip", Reward = 20, Title = "Your First Pet",
            Text = "Open Pets and equip your Aqua Wisp. Equipped pets help you gather more Qi." },
        { Id = "Breakthrough", Kind = "Rank", Goal = "QiGatherer", Reward = 40, Title = "Break Through",
            Text = "Gather 600 Qi, then press BREAK THROUGH to become a Qi Gatherer." },
        { Id = "Leap", Kind = "Leap", Reward = 20, Title = "Walk on Air",
            Text = "Jump, then jump again while in the air. Hold jump while falling to glide." },
        { Id = "Guardian", Kind = "GuardianHit", Reward = 30, Title = "The Stone Lion",
            Way = { "the Stone Lion", -480, 24 },
            Text = "Cross the west bridge to Beginner Isle. Find the Awakened Stone Lion and hit it (click, or tap Strike)." },
        { Id = "Egg", Kind = "TakeEgg", Reward = 60, Title = "Steal an Egg",
            Way = { "the Stone Lion", -480, 24 },
            Text = "Hit a guardian until it is weak, then take an egg from its stands. It will chase you!" },
        { Id = "Hatch", Kind = "Hatch", Reward = 80, Title = "Hatch It",
            Way = { "the Hatching Sanctum", 0, -178 },
            Text = "Carry the egg home across the bridge to Yggdrasil, then hatch it at the Hatching Sanctum." },
        -- the path on, island by island. Append only: a save holds its step number
        { Id = "Weapon", Kind = "BuyWeapon", Reward = 40, Title = "Get a Weapon",
            Way = { "the Blacksmith", 233, -172 },
            Text = "Visit the Blacksmith on Yggdrasil and buy your first weapon: a sword or a spear." },
        { Id = "Root", Kind = "Relic", Goal = "IslandRoot", Reward = 40, Title = "The Root of the Island",
            Way = { "the great root", 1, 238, Then = { "the relic", 88.5, 127, 153.3 } }, -- Then: where the world marker points once the player has reached the Way (QuestController)
            Text = "Climb down the great root of the World Tree and collect the relic at the bottom." },
        { Id = "JadeBridge", Kind = "Visit", Goal = "JadeGrove", Reward = 40, Title = "The Jade Bridge",
            Way = { "the Jade bridge", -160, -186 },
            Text = "Follow the marker across the bridge to Jade Grove." },
        { Id = "Mantis", Kind = "Secure", Goal = "MantisSage", Reward = 200, Title = "The Bamboo Mantis Sage",
            Way = { "the Mantis Sage", -384, -448 },
            Text = "Beat the Sage until it is weak, steal an egg and carry it home. Each egg you bring home gives lots of Qi." },
        { Id = "Awakener", Kind = "Rank", Goal = "QiAwakener", Reward = 60, Title = "The Ember Gate",
            Text = "Reach Qi Awakener to open the bridge to Ember Peak." },
        { Id = "EmberBridge", Kind = "Visit", Goal = "EmberPeak", Reward = 60, Title = "Into the Fire",
            Way = { "the Ember bridge", -44, -241 },
            Text = "Cross the rock bridge to Ember Peak. Stay off the lava." },
        { Id = "Xuanwu", Kind = "Secure", Goal = "EmberXuanwu", Reward = 400, Title = "The Ember Xuanwu",
            Way = { "the Ember Xuanwu", -128, -693 },
            Text = "Steal an egg from the Ember Xuanwu and carry it home. Jump over its shock rings." },
        { Id = "Forge", Kind = "Forge", Reward = 100, Title = "Forge a Weapon",
            Way = { "the Blacksmith", 233, -172 },
            Text = "Eggs you bring home and relics unlock elements. At the Blacksmith, give a weapon an element and a name." },
        -- (Id "Flight" kept: saves hold the step. Sword flight now comes at Lesser Immortal, so this step is the new realm.)
        { Id = "Flight", Kind = "Rank", Goal = "FoundationInitiate", Reward = 150, Title = "The Foundation Realm",
            Text = "Reach Foundation Initiate. You run faster and get one more air leap." },
        { Id = "MoonGate", Kind = "Rank", Goal = "SoulAwakening", Reward = 800, Title = "The Moonlit Gate",
            Text = "Cultivate, and bring eggs home for lots of Qi. At Soul Awakening, the bridge to Moonlit Isle opens." },
        { Id = "MoonBridge", Kind = "Visit", Goal = "MoonlitIsle", Reward = 300, Title = "The Moonlit Isle",
            Way = { "the Moonlit bridge", 57, -238 },
            Text = "Cross the bridge to Moonlit Isle." },
        { Id = "Tiangou", Kind = "Secure", Goal = "Tiangou", Reward = 1500, Title = "Tiangou the Moon-Eater",
            Way = { "Tiangou", 192, -790 },
            Text = "Steal an egg from Tiangou and carry it home. It jumps far and high." },
        { Id = "AbyssGate", Kind = "Rank", Goal = "DivineInitiate", Reward = 6000, Title = "The Gate of Descent",
            Text = "Reach Divine Initiate to open the bridge to Origin Abyss." },
        { Id = "AbyssBridge", Kind = "Visit", Goal = "OriginAbyss", Reward = 2000, Title = "Origin Abyss",
            Way = { "the Abyss bridge", 140, -201 },
            Text = "Cross the cracked bridge into Origin Abyss." },
        { Id = "Pangu", Kind = "Secure", Goal = "Pangu", Reward = 8000, Title = "Pangu the World-Splitter",
            Way = { "Pangu", 596, -856 },
            Text = "Steal an egg from Pangu and carry it all the way home." },
        { Id = "Summit", Kind = "Rank", Goal = "EternalOrigin", Reward = 50000, Title = "Eternal Origin",
            Text = "Reach the highest rank in the game." },
    },

    -- reasons to come back (server/Rewards/RewardService, shared/RewardRules). Daily: each streak day's
    -- Spirit Stones, times SpiritStones.RealmFactor per realm (a full week is worth about five weapons of
    -- the player's realm), and any minutes of Qi. Offline: the share
    -- of the cultivating rate paid for time away. Group: set GroupId to turn the group reward on.
    Rewards = {
        -- Spirit Stones at realm 1 (RewardRules scales them by realm). Raised four times on November 11, 2026: a day used to
        -- pay 5 stones against the 40 one stolen egg pays (15 seconds of play), so logging in wasn't worth it. Now day 1 is
        -- about half an egg, day 7 about six, and a full week about five weapons of the player's realm (measured 2026-11-12).
        -- BoostMinutes: minutes of the timed 2x Qi boost (TimedBoost), so free players get boosts too: 90 minutes a week (2026-11-16;
        -- they replaced 2, 3 and 5 minutes of Qi on days 3, 5 and 7, which no longer fit a day's card beside them)
        Daily = {
            { Stones = 20, BoostMinutes = 5 }, { Stones = 25, BoostMinutes = 5 }, { Stones = 30, BoostMinutes = 10 },
            { Stones = 35, BoostMinutes = 10 }, { Stones = 45, BoostMinutes = 15 }, { Stones = 55, BoostMinutes = 15 },
            { Stones = 100, BoostMinutes = 30 },
        },
        Offline = { Share = 0.2, MaxHours = 8, MinMinutes = 10 },
        Group = { GroupId = 0, Stones = 200 },
    },

    -- The Spin Wheel (the owner, 2026-11-16: "Add a SPIN THE WHEEL ROULETTE for rewards ... they can get 3 daily spins"; then "Place it
    -- to where my character standing"): a wheel in the hub (Placements/Yggdrasil.lua SpinWheel, SpinWheelBuilder), DailySpins free
    -- spins a UTC day (the daily reward's day: RewardRules.today), unused ones lost at the reset. The server rolls and pays
    -- (server/Rewards/SpinService, shared/SpinRules); every client turns the wheel to the segment it picked. Segments clockwise from
    -- the top, Weight out of their sum (100, so a weight is its percent):
    --   1 Stones  Share x the player's rank value (Shop.rankValue: a weapon of their realm at its first rank, rising between realms)  26.8
    --   2 Qi      Minutes of cultivating (QiReward.grantMinutes: Qi passes and pets count)                                           22
    --   3 Stones  2x segment 1                                                                                                       16
    --   4 Qi      15 minutes                                                                                                         12
    --   5 Egg     one of the best ordinary (non-Robux) egg the player's rank can take                                               10
    --   6 Stones  5x segment 1                                                                                                        8
    --   7 Spin    one more spin today                                                                                                 5
    --   8 Egg     JACKPOT: one Exclusive Egg (the 149 Robux egg), to hatch at the altar                                             0.2
    -- (The jackpot was 1 at first; the owner had it lowered the same day, "yes lower the chances for jackpot rate", so a free
    -- Exclusive Egg doesn't take from its sales: 0.2, the 0.8 moved to segment 1.)
    -- Worth a day (worked out 2026-11-16 over all 60 ranks): 3 / (1 - 0.05) = 3.16 spins; stones 0.62 of a
    -- rank value (0.84 to 1.83 daily-reward claims as the player climbs through a realm, the daily claim averaging 44 x RealmFactor per
    -- realm); 0.32 eggs (at their reference price, Shop.marketEggPrice, all in 1.0 to 2.8 claims; at what its pet sells for, about 1 to 2.2); 9.2 minutes
    -- of cultivating Qi (under two stolen eggs' bursts); and an Exclusive Egg about once in five months (1 in 158 days). It helps without
    -- replacing play: one active minute stealing eggs pays more stones.
    -- Where paid random items are restricted (PolicyService), the jackpot pays segment 6's stones instead of the Exclusive Egg, and
    -- the wheel shows it so (the owner, 2026-11-17: "apply this regions that restrict paid random items"). If Roblox can't answer, the
    -- player is treated as restricted.
    -- The stones segments pay the player's daily-stones pass bonus too (VIP +50%: the owner, 2026-11-17), SpinRules.stones.
    -- A full egg slot (EggInventory.MAX_PER_EGG) pays segment 6's stones instead.
    SpinWheel = {
        DailySpins = 3,
        MaxExtra = 20,        -- extra spins a day can hold (won ones)
        -- Spins bought with Robux (the owner, 2026-11-16: "if player already used up all his/her daily spins, they can still
        -- purchase spin using robux"; 1 for 5, 5 for 20). Developer products (ProductService pays them, once each). Bought spins
        -- never run out at the daily reset; a spin uses the day's free ones first, then won extras, then bought ones. A paid
        -- spin is a paid random item: where those are restricted (PolicyService) they aren't offered, and the wheel's odds are
        -- shown beside the buttons before anyone buys.
        MaxBought = 999,      -- bought spins a player can hold
        SpinProducts = {
            { Spins = 1, ProductId = 3732104097, Price = 5 },
            { Spins = 5, ProductId = 3732104157, Price = 20 },
        },
        Seconds = 6,          -- how long the wheel turns: the reward is paid when it stops
        Reach = 22,           -- studs from the wheel's prompt a spin may be asked from
        Segments = {
            { Kind = "Stones", Share = 0.2, Weight = 26.8, Color = Color3.fromRGB(66, 120, 230) },
            { Kind = "Qi", Minutes = 5, Weight = 22, Color = Color3.fromRGB(40, 190, 200) },
            { Kind = "Stones", Share = 0.4, Weight = 16, Color = Color3.fromRGB(120, 76, 220) },
            { Kind = "Qi", Minutes = 15, Weight = 12, Color = Color3.fromRGB(46, 170, 96) },
            { Kind = "Egg", Weight = 10, Color = Color3.fromRGB(236, 132, 40) },
            { Kind = "Stones", Share = 1, Weight = 8, Color = Color3.fromRGB(214, 60, 120) },
            { Kind = "Spin", Weight = 5, Color = Color3.fromRGB(70, 180, 255) },
            { Kind = "Jackpot", Weight = 0.2, Color = Color3.fromRGB(255, 196, 40) },
        },
    },

    -- each player's own view and sound (server/Data/Settings, client/UI/SettingsController)
    Settings = { Music = 1, Sound = 1, ReducedEffects = false, StatusMinimized = false, ShowQuest = true, TutorialDone = false, MenuHidden = false },

    MaxOwnedPets = 50,

    -- Duplicates (shared/PetRules): a spare copy can be fused into another of its kind, its levels adding on. Each
    -- level past the first adds QiPerLevel of the pet's base bonus. "Sell spares" at Buy & Sell only ever takes SpareRarities;
    -- a hatched AutoLock rarity starts locked, so it can't be sold or fused by accident.
    PetFusion = {
        MaxLevel = 5,
        QiPerLevel = 0.1,
        SpareRarities = { Common = true, Uncommon = true, Rare = true, Epic = true },
        AutoLock = { Mythical = true, Secret = true, Divine = true },
    },

    -- The Spirit Beast Codex's milestones (shared/CodexRules): discover Count beasts (no Count: all of them) for a lasting
    -- Qi bonus and Spirit Stones worth WeaponShare of a weapon of the player's realm. Each egg's full page pays too, by the rarest beast
    -- on it (PageShare), so a page that takes a Secret pays for the hunt however early its egg is. CreatorUserIds: the game's creators,
    -- whose book holds every beast from the start, those added later included (the owner, November 8, 2026).
    Codex = {
        CreatorUserIds = { 4993575280 },
        PageShare = { Legendary = 0.25, Mythical = 0.5, Secret = 1, Divine = 1 },
        Milestones = {
            { Count = 5, QiPercent = 2, WeaponShare = 0.25 },
            { Count = 10, QiPercent = 3, WeaponShare = 0.5 },
            { Count = 20, QiPercent = 5, WeaponShare = 0.75 },
            { Count = 30, QiPercent = 5, WeaponShare = 1 },
            { Count = 40, QiPercent = 10, WeaponShare = 1.5 },
            { Count = 50, QiPercent = 10, WeaponShare = 2 },
            { QiPercent = 25, WeaponShare = 5 },
        },
    },

    -- The Heavenly Tribulation (November 9, 2026): breaking through into a new realm, the heavens test the cultivator. Storm
    -- clouds gather over them, rings of light mark the ground where lightning will fall, and it falls; they dodge on foot
    -- (leaps and dashes; no sword flight). Lives hits and it is over: they may try again RetryAfter seconds later, no Qi lost.
    -- Survive every bolt and the breakthrough is theirs. Per realm entered (2 = Qi Foundation ... 12), bolts, the warning
    -- before each, the gap between them, how many fall together and how much they lead the cultivator's run all harden.
    Tribulation = {
        Lives = 3,
        RetryAfter = 60,       -- seconds
        Radius = 6,            -- studs: a bolt's reach, round the ring's middle
        Gather = 2.5,          -- seconds the storm gathers before the first bolt (to rise from meditation and get moving)
        CloudHeight = 55,      -- studs over the ground where the storm hangs
        Bolts = { 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 },                         -- realms 2 to 12
        Warn = { 1.45, 1.4, 1.3, 1.25, 1.2, 1.1, 1.05, 1.0, 0.95, 0.9, 0.85 },       -- seconds a ring shows before its bolt
        Gap = { 1.1, 1.05, 1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6 },         -- seconds from one bolt to the next
        Together = { 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3 },                              -- bolts falling at once (the others ring the cultivator)
        Lead = { 0, 0.2, 0.35, 0.45, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85 },          -- how far ahead of their run a bolt is aimed (share of the warning)
    },

    -- Titles (shared/TitleRules: what each is). DeveloperUserIds: who wears Developer (the game's creators). ContentCreatorUserIds:
    -- who wears Content Creator (add a creator's Roblox UserId; taken off the list, they lose it on their next join). Beta Tester
    -- follows Beta, below.
    Titles = {
        DeveloperUserIds = { 4993575280 },
        ContentCreatorUserIds = {},
    },

    -- The public beta (opened 2026-11-17). While Active, everyone who joins earns the TitleId title (TitleService), saved with
    -- their other titles, once. Turn Active off when the beta ends: nobody earns it after that, and those who already have it
    -- keep it for good.
    Beta = {
        Active = true,
        TitleId = "BetaTester",
    },

    -- The Feedback window (client/UI/FeedbackController, server/Feedback/FeedbackService): what a player may send, and how often.
    -- Kept in the "BetaFeedback" DataStore (read it with tools/roblox/read_feedback.lua).
    Feedback = {
        Categories = { "Bug", "Idea", "Other" },
        MinLength = 10,       -- characters, after trimming spaces
        MaxLength = 800,
        PerWindow = 3,        -- at most this many ...
        WindowSeconds = 600,  -- ... in any 10 minutes
        PerDay = 15,          -- and this many a day (UTC), kept in a small DataStore so rejoining doesn't reset it
    },

    StarterPetIds = { "AquaWisp" },
    -- Pets the game's creators always hold (server/Pets/PetInventory): on joining, a creator in UserIds who owns none of a pet here is
    -- given one, so a pet that no egg carries (the Nine-Tail Moonfox, a Lost Lineage) can still be shown off. The owner, 2026-11-12:
    -- "allow me to equip the fox".
    CreatorPets = { UserIds = { 4993575280 }, PetIds = { "NineTailMoonfox" } },

    GrantDevTestPets = false,
    DevTestPetIds = { "EmberWyrm", "VoltFox", "GoldenKirin", "NineTailMoonfox", "OriginSerpent" },
    DevTestEggs = { BeginnerQiEgg = 5 }, -- with GrantDevTestPets, in Studio, a new save also starts with these eggs (to test hatching)
    DevTestStones = 2000, -- with GrantDevTestPets, in Studio, a new save also starts with these Spirit Stones (to test buying)

    -- Each Pool's HatchChance values are percents and must add up to 100: PetInventory refuses to start otherwise, and the altar
    -- shows these numbers to the player exactly. tools/balance_report.py prints each egg's average Qi and any pet out of rarity order.
    Eggs = {
        BeginnerQiEgg = {
            DisplayName = "Beginner Qi Egg",
            RequiredRank = "QiInitiate",
            Pool = {
                { PetId = "AquaWisp", HatchChance = 45 },
                { PetId = "EmberWyrm", HatchChance = 27 },
                { PetId = "LunarHopper", HatchChance = 15 },
                { PetId = "VoltFox", HatchChance = 8 },
                { PetId = "GoldenKirin", HatchChance = 4 },
                { PetId = "AstralWhale", HatchChance = 0.9 },
                { PetId = "OriginSerpent", HatchChance = 0.1 },
            },
        },
        JadeSpiritEgg = {
            DisplayName = "Jade Spirit Egg",
            RequiredRank = "QiGatherer",
            Pool = {
                { PetId = "MossGolem", HatchChance = 45 },
                { PetId = "MyceliumSprite", HatchChance = 27 },
                { PetId = "JadeSpiritPanda", HatchChance = 15 },
                { PetId = "JadeAntlerDeer", HatchChance = 8 },
                { PetId = "GoldenKirin", HatchChance = 5 },
            },
        },
        InfernoEgg = {
            DisplayName = "Inferno Egg",
            RequiredRank = "QiAwakener",
            Pool = {
                { PetId = "MagmaCub", HatchChance = 45 },
                { PetId = "EmberWyrm", HatchChance = 27 },
                { PetId = "ObsidianGuardian", HatchChance = 15 },
                { PetId = "AzureSkyDragon", HatchChance = 8 },
                { PetId = "SunscaleDragon", HatchChance = 4 },
                { PetId = "DawnPhoenix", HatchChance = 1 },
            },
        },

        SpiritBreezeEgg = {
            DisplayName = "Spirit Breeze Egg",
            RequiredRank = "QiAdept",
            Pool = {
                { PetId = "WindSprite", HatchChance = 45 },
                { PetId = "CloudSheep", HatchChance = 27 },
                { PetId = "SpiritCrane", HatchChance = 15 },
                { PetId = "AzureSkyDragon", HatchChance = 8 },
                { PetId = "StormhornKirin", HatchChance = 5 },
            },
        },
        ElementalCoreEgg = {
            DisplayName = "Elemental Core Egg",
            RequiredRank = "FoundationInitiate",
            Pool = {
                { PetId = "GlacierPuff", HatchChance = 45 },
                { PetId = "StormBumblebee", HatchChance = 27 },
                { PetId = "CrystalBeetle", HatchChance = 15 },
                { PetId = "GravityImp", HatchChance = 8 },
                { PetId = "ThunderclawDrake", HatchChance = 4 },
                { PetId = "FrostfangSerpent", HatchChance = 1 },
            },
        },
        BloomwoodEgg = {
            DisplayName = "Bloomwood Egg",
            RequiredRank = "FoundationAdept",
            Pool = {
                { PetId = "DreamMoth", HatchChance = 45 },
                { PetId = "CrystalSnail", HatchChance = 27 },
                { PetId = "PrismArmadillo", HatchChance = 15 },
                { PetId = "LanternWarden", HatchChance = 8 },
                { PetId = "JadeWyrmTurtle", HatchChance = 5 },
            },
        },
        AncientGroveEgg = {
            DisplayName = "Ancient Grove Egg",
            RequiredRank = "CoreInitiate",
            Pool = {
                { PetId = "EchoBat", HatchChance = 45 },
                { PetId = "QiClockworkFinch", HatchChance = 27 },
                { PetId = "MoonfangTiger", HatchChance = 15 },
                { PetId = "ThousandEyedGuardian", HatchChance = 8 },
                { PetId = "NinefoldSpiritSerpent", HatchChance = 4 },
                { PetId = "WorldrootColossus", HatchChance = 1 },
            },
        },
        MagmaHeartEgg = {
            DisplayName = "Magma Heart Egg",
            RequiredRank = "PerfectFoundation",
            Pool = {
                { PetId = "SandPhantom", HatchChance = 45 },
                { PetId = "SolarButterfly", HatchChance = 27 },
                { PetId = "ObsidianGuardian", HatchChance = 15 },
                { PetId = "GoldenManeLion", HatchChance = 8 },
                { PetId = "BonefireDragon", HatchChance = 5 },
            },
        },
        PhoenixAshEgg = {
            DisplayName = "Phoenix Ash Egg",
            RequiredRank = "CoreAdept",
            Pool = {
                { PetId = "SandPhantom", HatchChance = 45 },
                { PetId = "SolarButterfly", HatchChance = 27 },
                { PetId = "ObsidianGuardian", HatchChance = 15 },
                { PetId = "DreadfangCerberus", HatchChance = 8 },
                { PetId = "BonefireDragon", HatchChance = 4 },
                { PetId = "PrismaticPhoenix", HatchChance = 1 },
            },
        },
        CelestialEgg = {
            DisplayName = "Celestial Egg",
            RequiredRank = "SoulAwakening",
            Pool = {
                { PetId = "StarfallFox", HatchChance = 45 },
                { PetId = "CosmicJellyfish", HatchChance = 27 },
                { PetId = "NebulaOwl", HatchChance = 15 },
                { PetId = "CelestialSnowLeopard", HatchChance = 8 },
                { PetId = "CometStag", HatchChance = 4 },
                { PetId = "CelestialPearlDragon", HatchChance = 1 },
            },
        },
        AstralSanctumEgg = {
            DisplayName = "Astral Sanctum Egg",
            RequiredRank = "AscendantInitiate",
            Pool = {
                { PetId = "StarfallFox", HatchChance = 45 },
                { PetId = "CosmicJellyfish", HatchChance = 27 },
                { PetId = "NebulaOwl", HatchChance = 15 },
                { PetId = "EclipseCat", HatchChance = 8 },
                { PetId = "TimekeeperTortoise", HatchChance = 4 },
                { PetId = "GalaxyManta", HatchChance = 1 },
            },
        },
        HeavenlyThroneEgg = {
            DisplayName = "Heavenly Throne Egg",
            RequiredRank = "LesserImmortal",
            Pool = {
                { PetId = "CelestialSnowLeopard", HatchChance = 47.5 },
                { PetId = "EclipseCat", HatchChance = 47.5 },
                { PetId = "CometStag", HatchChance = 2 },
                { PetId = "TimekeeperTortoise", HatchChance = 2 },
                { PetId = "CelestialPearlDragon", HatchChance = 0.5 },
                { PetId = "GalaxyManta", HatchChance = 0.5 },
            },
        },
        ForbiddenOriginEgg = {
            DisplayName = "Forbidden Origin Egg",
            RequiredRank = "DivineInitiate",
            Pool = {
                { PetId = "Shadowcoil", HatchChance = 87 },
                { PetId = "EclipseCat", HatchChance = 8 },
                { PetId = "RuneSphinx", HatchChance = 4 },
                { PetId = "ThousandYearDreamEater", HatchChance = 0.9 },
                { PetId = "TheNamelessOne", HatchChance = 0.1 },
            },
        },
        VoidRiftEgg = {
            DisplayName = "Void Rift Egg",
            RequiredRank = "VoidWalker",
            Pool = {
                { PetId = "Shadowcoil", HatchChance = 72 }, -- (87 until 2026-11-12: it hatched the same as the Forbidden Origin egg a realm earlier)
                { PetId = "EclipseCat", HatchChance = 10 },
                { PetId = "HeavenbreakerApe", HatchChance = 17 },
                { PetId = "VoidscaleHydra", HatchChance = 0.9 },
                { PetId = "TheNamelessOne", HatchChance = 0.1 },
            },
        },
        -- The Exclusive Egg (the owner, 2026-11-13): bought with Robux only (GameConfig.ExclusiveEgg, ProductService), never stolen,
        -- sold by the Merchant (nor, before 2026-11-16, at the Marketplace); open to every rank. No luck: its odds are the ones shown when it's bought.
        ExclusiveEgg = {
            DisplayName = "Exclusive Egg",
            RequiredRank = "QiInitiate",
            Exclusive = true,
            Pool = { -- odds follow rarity (the owner, 2026-11-15): Mythical 80, Secret 17, Divine 3
                { PetId = "NineTailMoonfox", HatchChance = 80 },
                { PetId = "Crysalith", HatchChance = 17 },
                { PetId = "EclipseDreadwing", HatchChance = 3 },
            },
        },
        PrimordialAbyssEgg = {
            DisplayName = "Primordial Abyss Egg",
            RequiredRank = "PrimordialAwakening",
            Pool = {
                { PetId = "HeavenbreakerApe", HatchChance = 60 },
                { PetId = "AbyssAnomalocaris", HatchChance = 39 },
                { PetId = "VoidscaleHydra", HatchChance = 0.45 },
                { PetId = "ThousandYearDreamEater", HatchChance = 0.45 },
                { PetId = "EternalClockworkDragon", HatchChance = 0.05 },
                { PetId = "TheNamelessOne", HatchChance = 0.05 },
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
        -- The three factions' robes (Faction below): the Murim Robes in each faction's colours (tools/outfits/faction_recolor.py).
        -- A faction's robe belongs to its members and nobody else, so it is as permanent as the pledge (OutfitService reads the
        -- player's Faction).
        OrthodoxRobes = { DisplayName = "Orthodox Robes", Faction = "Orthodox", Base = "Murim" },
        UnorthodoxRobes = { DisplayName = "Unorthodox Robes", Faction = "Unorthodox", Base = "Murim" },
        DemonicRobes = { DisplayName = "Demonic Robes", Faction = "Demonic", Base = "Murim" },
    },

    -- The three Murim factions (the owner, 2026-11-22; shared/FactionRules, server/Factions, client/Factions). Joining is for good: the
    -- pledge is a set-once record in its own DataStore (Store, key "U_<UserId>"; in Studio the name starts with the StudioTestSave
    -- name, or "Studio"), never in the save, so no save version changes and nothing can undo it. A member gets their faction's robes,
    -- a title (no bonus) and, after a trial at the TrialRealm, one secret weapon (Weapon): a bound weapon, never sold, never auctioned.
    -- The weapon's damage is the WeaponTier realm's weapon times WeaponBonus (so it is a prize, and the realm ladder still stands).
    -- Joining needs JoinRealm; anyone may walk in and read. The factions are equal in power: no faction gives Qi, luck or damage.
    Faction = {
        Store = "FactionPledges",
        KeyPrefix = "U_",
        JoinRealm = "Qi Foundation",
        TrialRealm = "Immortal Realm",
        RepRange = 22, -- studs from a faction's representative, to ask to join or to start the trial
        WeaponTier = 6,
        WeaponBonus = 1.1,
        Order = { "Orthodox", "Unorthodox", "Demonic" },
        Factions = {
            Orthodox = {
                DisplayName = "Orthodox Faction", Short = "Orthodox", Hq = "Dawnspire Hall", Master = "Master Hwa Rin",
                Color = Color3.fromRGB(96, 168, 255), Deep = Color3.fromRGB(24, 58, 120),
                Motto = "Keep your word. Protect the weak.",
                OutfitId = "OrthodoxRobes", TitleId = "OrthodoxDisciple",
                Weapon = { Id = "SecretOrthodox", Name = "Dawnspire Regent", Kind = "Sword" }, -- (the owner approved the redesign on 2026-11-22)
                Trial = { Name = "Trial of Discipline", Text = "Pass five gates up the Dawnspire stair, in order, before the time runs out." },
                Pages = {
                    { Title = "WHO WE ARE", Text = "The Orthodox Faction keeps the old rules. Its disciples train every day, keep their word and stand between the weak and danger. Their home is Dawnspire Hall, a white stone hall high above the clouds." },
                    { Title = "HOW WE FIGHT", Text = "They fight with clean, careful sword work. They never strike first and never strike a beaten foe. Their trial tests patience: you must follow the path in order." },
                    { Title = "WHAT YOU GET", Text = "The Orthodox Robes, white and blue. A seat in Dawnspire Hall. And in time, the chance to earn the Dawnspire Regent." },
                },
            },
            Unorthodox = {
                DisplayName = "Unorthodox Faction", Short = "Unorthodox", Hq = "Windrift Hold", Master = "Elder Kang Dal",
                Color = Color3.fromRGB(70, 200, 150), Deep = Color3.fromRGB(10, 70, 56),
                Motto = "No master. No map. Only skill.",
                OutfitId = "UnorthodoxRobes", TitleId = "UnorthodoxWanderer",
                Weapon = { Id = "SecretUnorthodox", Name = "Crosscurrent Saber", Kind = "Sword" }, -- (the owner, 2026-11-22: all three are swords; approved the design the same day)
                Trial = { Name = "Trial of Three Tokens", Text = "Find three tokens hidden around Windrift Hold before the time runs out. Nobody tells you the road." },
                Pages = {
                    { Title = "WHO WE ARE", Text = "The Unorthodox Faction answers to no one. Its fighters come from rivers, markets and back roads, and they judge each other by skill, not by rank. Windrift Hold stands over a waterfall, and every road into it is open." },
                    { Title = "HOW WE FIGHT", Text = "They fight in odd, quick ways and use whatever is at hand. Their trial tests your wits: you have to find your own way." },
                    { Title = "WHAT YOU GET", Text = "The Unorthodox Robes, teal and linen. A place at Windrift Hold. And in time, the chance to earn the Crosscurrent Saber." },
                },
            },
            Demonic = {
                DisplayName = "Demonic Faction", Short = "Demonic", Hq = "Nightfall Citadel", Master = "Lord Mu Yeong",
                Color = Color3.fromRGB(226, 52, 48), Deep = Color3.fromRGB(70, 6, 12),
                Motto = "Strength is the only law.",
                OutfitId = "DemonicRobes", TitleId = "DemonicBlade",
                Weapon = { Id = "SecretDemonic", Name = "Nightfall Talon", Kind = "Sword" }, -- (the owner approved the redesign on 2026-11-22)
                Trial = { Name = "Trial of Strength", Text = "Defeat every dummy the arena sends before the time runs out." },
                Pages = {
                    { Title = "WHO WE ARE", Text = "The Demonic Faction believes strength is the only law. Others fear it, and it does not mind. Nightfall Citadel is a black fortress where only the strong are heard." },
                    { Title = "HOW WE FIGHT", Text = "They fight hard and fast and give no ground. Their trial tests your strength: beat everything the arena sends." },
                    { Title = "WHAT YOU GET", Text = "The Demonic Robes, black and red. A seat in Nightfall Citadel. And in time, the chance to earn the Nightfall Talon." },
                },
            },
        },
        Equal = "All three factions are equally strong. Pick the one that feels like you.",
        Forever = "This choice is forever. You can never leave your faction or join another.",
    },

    -- The Store's game passes (the owner, November 10, 2026), in the order it shows them (shared/PassRules applies them). Created on
    -- Roblox and put on sale 2026-11-12 (the owner: "make my game passes live"). Each is
    -- sold once its GamePassId is set (the owner creates the pass in the Creator Dashboard); at 0 it shows "Coming soon" and
    -- nobody can buy it. Price is a fallback: the Store shows the pass's live price from Roblox. Icon: its picture
    -- (tools/ui/draw_store_icons.py: assets/ui/store/<Id>.png; <Id>_512.png is the picture to give the pass on Roblox).
    -- Headline: the card's big words. WasPrice: what it cost before the owner's price cut of 2026-11-13; the card shows it
    -- struck through only while the live price is lower, so it never claims a saving that isn't real.
    GamePasses = {
        { Id = "Luck", Name = "Lucky Cultivator", GamePassId = 2082626429, Price = 99, Headline = "2x LUCK!", WasPrice = 149, Icon = "rbxassetid://129170449479441",
            Text = "Rare beasts and rare mutations hatch twice as often.", Luck = 2 }, -- (shortened: the longer text was cut off in its card, UI audit 2026-11-11)
        { Id = "PetSlots", Name = "+3 Pet Slots", GamePassId = 2081480484, Price = 199, Headline = "+3 BEASTS!", WasPrice = 249, Icon = "rbxassetid://90769324952400",
            Text = "Equip 6 beasts at once instead of 3.", ExtraSlots = 3 },
        { Id = "VIP", Name = "VIP", GamePassId = 2083352447, Price = 249, Headline = "VIP PERKS!", WasPrice = 299, Icon = "rbxassetid://97387314672491",
            Text = "The VIP title and chat tag, +10% Qi and +50% daily Spirit Stones.", QiMultiplier = 1.1, DailyStones = 1.5, Title = "VIP" },
        -- The Qi boosts (the owner, 2026-11-15: "2x 3 + 4x 6 + 8x 12 etc... like the multiplier in steal an eggs"): tiers, not
        -- stacking. Only the highest QiTier a player owns counts (PassRules.qiMultiplier); VIP's QiMultiplier still multiplies on top.
        -- Capped at MaxQiTier (the owner, 2026-11-16: "just keep the multiplier until 4x then also add a consumable multiplier"):
        -- the 8x and 16x passes are Retired: taken off sale on Roblox, never shown, and anyone who owns one counts as the 4x tier (only
        -- the creator's account ever had them: the game wasn't public). They stay listed so their ownership is still checked.
        -- The 2x tier is the old Qi Surge pass (Id kept, so its owners keep it), renamed and repriced on Roblox the same day.
        -- Repriced on Roblox on 2026-11-16 by the owner's decision, from 3 and 6 Robux: 2x 49, 4x 149 (the timed boosts are 5, 12, 39).
        { Id = "QiSurge", Name = "Qi Boost", GamePassId = 2083202424, Price = 49, Headline = "2x QI!", Icon = "rbxassetid://71034417049645",
            Text = "Double Qi from cultivating, while you're away and from every Qi reward.", QiTier = 2 },
        { Id = "Qi4x", Name = "Greater Qi Boost", GamePassId = 2088004027, Price = 149, Headline = "4x QI!", Icon = "rbxassetid://71034417049645",
            Text = "Four times the Qi from cultivating, while you're away and from every Qi reward.", QiTier = 4 },
        { Id = "Qi8x", Name = "Grand Qi Boost", GamePassId = 2088975892, Price = 12, Headline = "8x QI!", Icon = "rbxassetid://71034417049645",
            Text = "Eight times the Qi from cultivating, while you're away and from every Qi reward.", QiTier = 8, Retired = true },
        { Id = "Qi16x", Name = "Supreme Qi Boost", GamePassId = 2087998028, Price = 24, Headline = "16x QI!", Icon = "rbxassetid://71034417049645",
            Text = "Sixteen times the Qi from cultivating, while you're away and from every Qi reward.", QiTier = 16, Retired = true },
    },
    MaxQiTier = 4, -- the most any Qi pass counts for (PassRules.qiTier)

    -- Timed Qi boosts (the owner, 2026-11-16: "add a consumable multiplier like 2x qi multiplier per 5 mins"): developer products
    -- (ProductService) that add minutes of Multiplier times Qi, on top of the Qi pass and VIP, on everything that gives Qi but offline Qi.
    -- Buying more adds time, up to MaxMinutes banked. The time runs only while the player is in the game: it is saved as seconds left
    -- (PlayerData's Boost, server/Shop/QiBoost) and runs again when they rejoin. The daily reward gives some too (Rewards.Daily
    -- BoostMinutes), so free players have them. Prices sit with the spins' (5 and 20 Robux): a short boost costs about a spin.
    TimedBoost = {
        Multiplier = 2,
        MaxMinutes = 24 * 60,
        Products = {
            { Minutes = 5, ProductId = 3732227230, Price = 5 },   -- "2x Qi Boost: 5 Minutes" (made 2026-11-16 via Open Cloud)
            { Minutes = 15, ProductId = 3732227300, Price = 12 }, -- "2x Qi Boost: 15 Minutes"
            { Minutes = 60, ProductId = 3732227320, Price = 39 }, -- "2x Qi Boost: 1 Hour"
        },
    },
    -- Lucky hatches (the Luck pass): every Rare-or-rarer beast that is also rarer than an egg's commonest is that many times likelier,
    -- taken from the others, which always keep at least this many percent between them (PassRules.luckyPool).
    LuckFloor = 10,
    -- The exclusive egg (the owner, November 10, 2026): shown in the Store, locked, until its beast is made. It will be sold for
    -- Robux per hatch, showing its odds, and not offered where Roblox restricts paid random items (PolicyService).
    -- Sold (the owner, 2026-11-13): 149 Robux an egg, a developer product (ProductId, made on Roblox); the egg goes to the player's eggs
    -- and is hatched at the Hatching Altar. Its contents: GameConfig.Eggs.ExclusiveEgg.
    ExclusiveEgg = {
        Name = "Exclusive Egg", Icon = "rbxassetid://80787462087085", EggId = "ExclusiveEgg", ProductId = 3730790355, Price = 149,
        Text = "Three beasts found in no other egg: the Nine-Tail Moonfox, Crysalith and the Eclipse Dreadwing.",
    },

    -- The Wandering Merchant (the owner, 2026-11-12, verbatim: "Implement wandering merchant for every 1 hour and the wandering
    -- merchant will only stay for 10 mins every 1 hour"; asked, the owner chose rotating 3 to 4 rare deals, at a fixed spot in the
    -- hub). He is in the hub (Placements/Yggdrasil.lua: Merchant) while os.time() % Every < Stay: the first Stay seconds of every
    -- UTC hour, the same in every server. Each visit offers Deals of the Pool, drawn without repeats from a seed of the visit's
    -- number (shared/Merchant.lua), so every server shows the same ones; each player can buy each deal once a visit. All in
    -- Spirit Stones (MerchantService):
    --   Egg  Count eggs at Discount off the egg's reference price (Shop.marketEggPrice, the old Marketplace price), for the egg's RequiredRank. At most
    --        MaxEggDiscount: with the Luck pass an egg's pet sells on average for at most 0.966 of the discounted price at today's
    --        deals (the Void Rift Egg, the worst; measured 2026-11-15 with hatch sizes' sell values, PetRules.Sizes; it was 0.949
    --        before sizes, after the 2026-11-12 Void Rift pool change; at 40% off it would pass even): re-check whenever pet values, pools, luck or
    --        discounts change.
    --   Pet  one beast, chosen, no luck involved: Rare, Epic or Legendary only, for PetMarkup times what it sells for
    --        (Shop.petValue, at level 1: at least MinPetMarkup, so buying one to sell it always loses stones), for the rank
    --        that can hatch it (Shop.petEggRank). Each is far less than hatching it would cost on average, which is the deal.
    -- Merchant.lua checks these rules as it loads.
    WanderingMerchant = {
        Every = 3600,        -- seconds: he comes once an hour
        Stay = 600,          -- seconds he stays: 10 minutes
        LeaveWarning = 60,   -- seconds before he leaves that everyone is told
        Deals = { Min = 3, Max = 4 },
        PetMarkup = 4,
        MinPetMarkup = 2.5,
        MaxEggDiscount = 0.4,
        PetRarities = { Rare = true, Epic = true, Legendary = true },
        Pool = { -- an array, in a fixed order: the draw depends on it (changing it changes every visit's deals)
            { Kind = "Egg", EggId = "BeginnerQiEgg", Count = 3, Discount = 0.25 },
            { Kind = "Egg", EggId = "SpiritBreezeEgg", Count = 3, Discount = 0.3 },
            { Kind = "Egg", EggId = "ElementalCoreEgg", Count = 3, Discount = 0.25 },
            { Kind = "Egg", EggId = "AncientGroveEgg", Count = 3, Discount = 0.3 },
            { Kind = "Egg", EggId = "CelestialEgg", Count = 3, Discount = 0.3 },
            { Kind = "Egg", EggId = "HeavenlyThroneEgg", Count = 3, Discount = 0.25 },
            { Kind = "Egg", EggId = "ForbiddenOriginEgg", Count = 3, Discount = 0.3 },
            { Kind = "Egg", EggId = "VoidRiftEgg", Count = 3, Discount = 0.25 },
            { Kind = "Pet", PetId = "GoldenKirin" },
            { Kind = "Pet", PetId = "AzureSkyDragon" },
            { Kind = "Pet", PetId = "SunscaleDragon" }, -- (the Dawn Phoenix's place until it became Mythical, 2026-11-16)
            { Kind = "Pet", PetId = "GravityImp" },
            { Kind = "Pet", PetId = "JadeWyrmTurtle" },
            { Kind = "Pet", PetId = "MoonfangTiger" },
            { Kind = "Pet", PetId = "NinefoldSpiritSerpent" },
            { Kind = "Pet", PetId = "CelestialSnowLeopard" },
            { Kind = "Pet", PetId = "CometStag" },
            { Kind = "Pet", PetId = "TimekeeperTortoise" },
            { Kind = "Pet", PetId = "RuneSphinx" },
            { Kind = "Pet", PetId = "HeavenbreakerApe" },
        },
    },
}

return GameConfig
