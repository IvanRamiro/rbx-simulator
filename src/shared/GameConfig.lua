
local GameConfig = {
    GameName = "Qi Aura Simulator",

    StartingQi = 0,

    -- Cultivation (automatic Qi while the player meditates)
    CultivationQiReward = 10, -- Base Qi per interval while cultivating, before pet bonuses
    CultivationInterval = 1, -- Seconds between cultivation rewards
    CultivationToggleCooldown = 0.5, -- Seconds before a player can start cultivating again
    CultivationKeybind = Enum.KeyCode.E, -- Keyboard shortcut to start/stop cultivating

    -- Qi Spring training station on the starting island. Cultivating within
    -- Radius studs of its centre adds QiBonusPercent to every reward, on top
    -- of pet bonuses (50 means +50%).
    TrainingStation = {
        DisplayName = "Qi Spring",
        QiBonusPercent = 50,
        Radius = 10,
    },

    -- Flight. It unlocks at a cultivation rank, and later ranks make it
    -- faster (the flight-speed upgrades). Speeds are in studs per second;
    -- walking is 16.
    Flight = {
        Keybind = Enum.KeyCode.Q, -- Keyboard toggle (F is the egg, E is cultivating)
        GamepadButton = Enum.KeyCode.ButtonY,
        ToggleCooldown = 0.3, -- Seconds between take-offs and landings
        Acceleration = 4, -- How quickly flight speeds up and slows down (higher = snappier)
        -- Each level applies from its rank onwards. The first one unlocks flight.
        SpeedLevels = {
            { RankId = "QiGatherer", Speed = 28 },
            { RankId = "QiAwakener", Speed = 34 },
            { RankId = "FoundationInitiate", Speed = 40 },
            { RankId = "PerfectFoundation", Speed = 50 },
            { RankId = "CoreInitiate", Speed = 58 },
            { RankId = "GoldenSpiritCore", Speed = 70 },
        },
    },

    -- Levitation while cultivating (visual only)
    LevitationHeight = 1.5, -- Studs the character rises above its normal height
    LevitationBobHeight = 0.3, -- Studs of gentle up-and-down motion while hovering
    LevitationBobTime = 1.6, -- Seconds for each half of the bob
    MeditationAnimationId = 0, -- Optional pose animation you own (number ID); 0 = hover only

    StartingRank = "Qi Initiate", -- Must be the first entry in Ranks below

    -- Cultivation ranks, lowest first: major realms of five levels each (see
    -- Qi_Aura_Simulator_Ranks_And_Pets.md). Only the first three realms are in
    -- the game so far; add later realms to the end of the list.
    --   Id          Stable ID used in saved data; never change it
    --   Name        Shown to players (must be unique)
    --   Realm       The major realm this rank belongs to
    --   Level       1 to 5 within the realm. Level 5 is a milestone and gets a
    --               bigger breakthrough effect, as does reaching a new realm.
    --   QiRequired  Qi a player must have to rank up into this rank (Qi is not
    --               spent). Players move up one rank at a time.
    --   AuraTier    1 to 5: how powerful the aura looks (AuraStyles.Tiers)
    -- Balanced for roughly 4 minutes of cultivating to finish Qi Awakening,
    -- 25 minutes for Qi Foundation and 80 minutes for Spirit Core (see
    -- tools/balance_report.py, which prints the timings for these numbers).
    Ranks = {
        -- Realm 1: Qi Awakening
        { Id = "QiInitiate", Name = "Qi Initiate", Realm = "Qi Awakening", Level = 1, QiRequired = 0, AuraTier = 1 },
        { Id = "QiGatherer", Name = "Qi Gatherer", Realm = "Qi Awakening", Level = 2, QiRequired = 300, AuraTier = 1 },
        { Id = "QiCondenser", Name = "Qi Condenser", Realm = "Qi Awakening", Level = 3, QiRequired = 900, AuraTier = 2 },
        { Id = "QiAdept", Name = "Qi Adept", Realm = "Qi Awakening", Level = 4, QiRequired = 2000, AuraTier = 2 },
        { Id = "QiAwakener", Name = "Qi Awakener", Realm = "Qi Awakening", Level = 5, QiRequired = 4000, AuraTier = 2 },

        -- Realm 2: Qi Foundation
        { Id = "FoundationInitiate", Name = "Foundation Initiate", Realm = "Qi Foundation", Level = 1, QiRequired = 6500, AuraTier = 3 },
        { Id = "FoundationBuilder", Name = "Foundation Builder", Realm = "Qi Foundation", Level = 2, QiRequired = 10000, AuraTier = 3 },
        { Id = "FoundationAdept", Name = "Foundation Adept", Realm = "Qi Foundation", Level = 3, QiRequired = 15000, AuraTier = 3 },
        { Id = "FoundationMaster", Name = "Foundation Master", Realm = "Qi Foundation", Level = 4, QiRequired = 21000, AuraTier = 4 },
        { Id = "PerfectFoundation", Name = "Perfect Foundation", Realm = "Qi Foundation", Level = 5, QiRequired = 29000, AuraTier = 4 },

        -- Realm 3: Spirit Core
        { Id = "CoreInitiate", Name = "Core Initiate", Realm = "Spirit Core", Level = 1, QiRequired = 40000, AuraTier = 4 },
        { Id = "CoreFormation", Name = "Core Formation", Realm = "Spirit Core", Level = 2, QiRequired = 55000, AuraTier = 5 },
        { Id = "CoreAdept", Name = "Core Adept", Realm = "Spirit Core", Level = 3, QiRequired = 72000, AuraTier = 5 },
        { Id = "CoreMaster", Name = "Core Master", Realm = "Spirit Core", Level = 4, QiRequired = 95000, AuraTier = 5 },
        { Id = "GoldenSpiritCore", Name = "Golden Spirit Core", Realm = "Spirit Core", Level = 5, QiRequired = 120000, AuraTier = 5 },
    },

    -- Pets
    MaxEquippedPets = 3,

    -- Pet catalogue, keyed by stable pet ID (used in saved data; never change
    -- an ID). While equipped, a pet adds QiBonusPercent to cultivation rewards
    -- (25 means +25%). Each pet's aura look is in src/client/AuraStyles.lua.
    -- Rarer pets are stronger, but kept modest so one lucky hatch speeds
    -- progress up rather than skipping it.
    Pets = {
        AquaWisp = { DisplayName = "Aqua Wisp", Rarity = "Common", Theme = "Water", QiBonusPercent = 10 },
        EmberWyrm = { DisplayName = "Ember Wyrm", Rarity = "Uncommon", Theme = "Fire", QiBonusPercent = 20 },
        VoltFox = { DisplayName = "Volt Fox", Rarity = "Rare", Theme = "Lightning", QiBonusPercent = 35 },
        GoldenKirin = { DisplayName = "Golden Kirin", Rarity = "Legendary", Theme = "Nature", QiBonusPercent = 60 },
        NineTailMoonfox = { DisplayName = "Nine-Tail Moonfox", Rarity = "Mythical", Theme = "Moon", QiBonusPercent = 100 },
        OriginSerpent = { DisplayName = "Origin Serpent", Rarity = "Secret", Theme = "Primordial", QiBonusPercent = 150 },
    },

    -- Rarities from most to least common, with the colour used in the UI
    PetRarityColors = {
        Common = Color3.fromRGB(220, 225, 235),
        Uncommon = Color3.fromRGB(120, 230, 140),
        Rare = Color3.fromRGB(120, 200, 255),
        Epic = Color3.fromRGB(190, 140, 255),
        Legendary = Color3.fromRGB(255, 200, 70),
        Mythical = Color3.fromRGB(255, 110, 160),
        Secret = Color3.fromRGB(255, 255, 255),
    },

    MaxOwnedPets = 50, -- Hatching stops granting pets once a player owns this many

    -- Given once to brand-new players
    StarterPetIds = { "AquaWisp" },

    -- Development only: set GrantDevTestPets to true to also give brand-new
    -- players these pets while playtesting in Studio. Never granted in the live game.
    GrantDevTestPets = false,
    DevTestPetIds = { "EmberWyrm", "VoltFox", "GoldenKirin", "NineTailMoonfox", "OriginSerpent" },

    -- Beginner Qi Egg on the starting island. The server rolls the pet; each
    -- pet's chance is its Weight divided by the total of all weights. These
    -- follow the design guide's rarity chances (Common 45%, Uncommon 27%,
    -- Rare 15%, Epic 8%, Legendary 4%, Mythical 0.9%, Secret 0.1%). There is
    -- no Epic pet yet, so Volt Fox (Rare) also has the Epic share for now.
    BeginnerEgg = {
        DisplayName = "Beginner Qi Egg",
        -- Seconds between hatches for each player. Hatching is free, so this
        -- sets how fast players find rare pets (about 1 Legendary per 19
        -- minutes of hatching on average).
        Cooldown = 45,
        Pool = {
            { PetId = "AquaWisp", Weight = 45 },
            { PetId = "EmberWyrm", Weight = 27 },
            { PetId = "VoltFox", Weight = 23 },
            { PetId = "GoldenKirin", Weight = 4 },
            { PetId = "NineTailMoonfox", Weight = 0.9 },
            { PetId = "OriginSerpent", Weight = 0.1 },
        },
    },
}

return GameConfig
