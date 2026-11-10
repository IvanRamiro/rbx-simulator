-- Every title a cultivator can earn and wear (the owner, November 9, 2026): Developer, Content Creator, VIP (the pass, November 10), Beta Tester, one for each of the twelve
-- realms, one for securing an egg from each guardian, the beast collector titles, Keeper of Secrets and Relic Seeker.
-- A worn title shows over the player's head (TitleController) in its own colour, a sheen of light sweeping across it now and
-- then; a Shimmer is the colour of a grander title's sheen (it sweeps more often).
-- The server (server/Titles) decides who has earned what; this is what each one is, and how it is earned.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local CodexRules = require(ReplicatedStorage:WaitForChild("CodexRules"))

local TitleRules = {}

local function rgb(r, g, b)
    return Color3.fromRGB(r, g, b)
end

-- The window's sections, in order.
TitleRules.Groups = {
    { Id = "Special", Name = "SPECIAL" },
    { Id = "Realm", Name = "REALMS" },
    { Id = "Guardian", Name = "GUARDIANS" },
    { Id = "Collection", Name = "COLLECTION" },
}

-- The twelve realms' titles, in the realms' order: each an epithet of its own (not the realm's or a rank's name), in the
-- realm's colour, brightening as the realms climb; from the Divine Realm up, a light runs across them.
local REALM_TITLES = {
    { Realm = "Qi Awakening", Text = "the Awakened", Color = rgb(150, 226, 255) },
    { Realm = "Qi Foundation", Text = "Bedrock Disciple", Color = rgb(112, 192, 255) },
    { Realm = "Spirit Core", Text = "Core Forger", Color = rgb(124, 236, 184) },
    { Realm = "Spirit Soul", Text = "Soul-Tempered", Color = rgb(72, 214, 152) },
    { Realm = "Ascendant Realm", Text = "Cloud Strider", Color = rgb(255, 228, 124) },
    { Realm = "Immortal Realm", Text = "the Deathless", Color = rgb(255, 198, 72) },
    { Realm = "Divine Realm", Text = "Heaven's Chosen", Color = rgb(206, 156, 255), Shimmer = rgb(255, 236, 255) },
    { Realm = "Cosmic Realm", Text = "Starborn", Color = rgb(150, 172, 255), Shimmer = rgb(236, 244, 255) },
    { Realm = "Void Realm", Text = "Void-Touched", Color = rgb(176, 116, 255), Shimmer = rgb(90, 220, 255) },
    { Realm = "Heavenly Dao", Text = "Keeper of the Dao", Color = rgb(255, 238, 196), Shimmer = rgb(255, 255, 255) },
    { Realm = "Primordial Realm", Text = "the Primeval", Color = rgb(255, 156, 92), Shimmer = rgb(255, 234, 160) },
    { Realm = "Eternal Transcendence", Text = "the Eternal", Color = rgb(255, 244, 214), Shimmer = rgb(160, 220, 255) },
}

-- The guardians' titles: for carrying an egg of theirs home (GameConfig.Guardians; the egg secured, Guardian.lua). They are
-- never beaten, only robbed, so each names the theft.
local GUARDIAN_TITLES = {
    { Guardian = "StoneLion", Id = "PrideThief", Text = "Pride Thief", Color = rgb(222, 200, 156) },
    { Guardian = "MantisSage", Id = "BambooShadow", Text = "Bamboo Shadow", Color = rgb(146, 224, 124) },
    { Guardian = "EmberXuanwu", Id = "Ashwalker", Text = "Ashwalker", Color = rgb(255, 136, 76) },
    { Guardian = "Tiangou", Id = "MoonSaver", Text = "Moon-Saver", Color = rgb(206, 218, 255), Shimmer = rgb(255, 255, 255) },
    { Guardian = "Pangu", Id = "PangusRival", Text = "Pangu's Rival", Color = rgb(255, 204, 112), Shimmer = rgb(255, 120, 80) },
}

-- The beast collector titles: beasts in the player's Spirit Beast Codex (Count nil: every beast there is).
local COLLECTOR_TITLES = {
    { Id = "BeastSeeker", Text = "Beast Seeker", Count = 10, Color = rgb(184, 232, 164) },
    { Id = "BeastTamer", Text = "Beast Tamer", Count = 25, Color = rgb(124, 222, 204) },
    { Id = "BeastMaster", Text = "Beast Master", Count = 45, Color = rgb(255, 212, 124) },
    { Id = "CodexKeeper", Text = "Keeper of the Codex", Count = nil, Color = rgb(255, 226, 140), Shimmer = rgb(140, 255, 214) },
}

TitleRules.List = {}
TitleRules.ById = {}

local function add(entry)
    table.insert(TitleRules.List, entry)
    TitleRules.ById[entry.Id] = entry
end

add({ Id = "Developer", Group = "Special", Text = "Developer", Color = rgb(255, 104, 96), Shimmer = rgb(255, 214, 96),
    How = "Made this game." })
add({ Id = "ContentCreator", Group = "Special", Text = "Content Creator", Color = rgb(255, 110, 196), Shimmer = rgb(255, 236, 140),
    How = "Given to creators who make videos and streams of the game." })
add({ Id = "BetaTester", Group = "Special", Text = "Beta Tester", Color = rgb(96, 240, 210), Shimmer = rgb(130, 170, 255),
    How = "Played during the beta, before the game's launch." })
add({ Id = "VIP", Group = "Special", Text = "VIP", Color = rgb(255, 206, 84), Shimmer = rgb(255, 250, 220),
    How = "Own the VIP pass, in the Store." })

TitleRules.RealmTitleIds = {} -- [realm name] = its title's id
for index, entry in REALM_TITLES do
    local id = "Realm" .. index
    TitleRules.RealmTitleIds[entry.Realm] = id
    add({ Id = id, Group = "Realm", Text = entry.Text, Color = entry.Color, Shimmer = entry.Shimmer, RealmIndex = index,
        How = if index == 1 then "Begin cultivating, in the Qi Awakening realm."
            else "Reach the " .. entry.Realm .. (if string.find(entry.Realm, "Realm") then "." else " realm.") })
end

TitleRules.GuardianTitleIds = {} -- [guardian id] = its title's id
for _, entry in GUARDIAN_TITLES do
    local guardian = GameConfig.Guardians[entry.Guardian]
    TitleRules.GuardianTitleIds[entry.Guardian] = entry.Id
    add({ Id = entry.Id, Group = "Guardian", Text = entry.Text, Color = entry.Color, Shimmer = entry.Shimmer,
        How = "Carry an egg home from " .. (if guardian then guardian.DisplayName else entry.Guardian) .. "." })
end

-- every beast that can be hatched (the Codex's own list: a retired beast in no egg doesn't count)
local beastCount = CodexRules.Total
TitleRules.CollectorTitles = {}
for _, entry in COLLECTOR_TITLES do
    local count = entry.Count or beastCount
    table.insert(TitleRules.CollectorTitles, { Id = entry.Id, Count = count })
    add({ Id = entry.Id, Group = "Collection", Text = entry.Text, Color = entry.Color, Shimmer = entry.Shimmer, Count = count,
        How = if entry.Count then "Have " .. count .. " beasts in your Spirit Beast Codex." else "Have every beast in your Spirit Beast Codex." })
end
add({ Id = "SecretKeeper", Group = "Collection", Text = "Keeper of Secrets", Color = rgb(206, 140, 255), Shimmer = rgb(120, 96, 255),
    How = "Own a Secret beast." })
add({ Id = "RelicSeeker", Group = "Collection", Text = "Relic Seeker", Color = rgb(244, 196, 116),
    How = "Find every relic on the islands." })

-- Each title's lettering (Roblox's own font families: { family, weight, "Italic" }), chosen for what it means: Developer
-- engineered and sharp, Content Creator a bold thumbnail face, Beta Tester futuristic; the realms climbing from brush
-- calligraphy through stone, forged metal and refined book type to Roman inscription, ornate blackletter and the far-future
-- faces of the stars and the void; the guardians' thieves as their quarry suggests; a beast keeper's sturdy hand, the
-- Keeper of Secrets in blackletter, the Relic Seeker in an explorer's typewritten notes.
local FONTS = {
    Developer = { "Sarpanch", 900 },
    ContentCreator = { "LuckiestGuy", 400 },
    BetaTester = { "Michroma", 400 },
    VIP = { "Bangers", 400 },                    -- a bold marquee face, in gold
    Realm1 = { "Fondamento", 400, "Italic" },    -- the Awakened
    Realm2 = { "Oswald", 600 },                  -- Bedrock Disciple
    Realm3 = { "Sarpanch", 700 },                -- Core Forger
    Realm4 = { "AccanthisADFStd", 400 },         -- Soul-Tempered
    Realm5 = { "Fondamento", 400 },              -- Cloud Strider
    Realm6 = { "RomanAntique", 400 },            -- the Deathless
    Realm7 = { "GrenzeGotisch", 600 },           -- Heaven's Chosen
    Realm8 = { "Jura", 700 },                    -- Starborn
    Realm9 = { "Zekton", 400 },                  -- Void-Touched
    Realm10 = { "AccanthisADFStd", 400 },        -- Keeper of the Dao
    Realm11 = { "GrenzeGotisch", 900 },          -- the Primeval
    Realm12 = { "RomanAntique", 400 },           -- the Eternal
    PrideThief = { "Oswald", 700 },
    BambooShadow = { "Fondamento", 400, "Italic" },
    Ashwalker = { "Sarpanch", 800 },
    MoonSaver = { "AccanthisADFStd", 400 },
    PangusRival = { "RomanAntique", 400 },
    BeastSeeker = { "DenkOne", 400 },
    BeastTamer = { "DenkOne", 400 },
    BeastMaster = { "Oswald", 700 },
    CodexKeeper = { "AccanthisADFStd", 400 },
    SecretKeeper = { "GrenzeGotisch", 700 },
    RelicSeeker = { "SpecialElite", 400 },
}

for order, entry in TitleRules.List do
    entry.Order = order
    entry.Font = FONTS[entry.Id] or { "Merriweather", 700 }
end

-- What a player wearing "Auto" (their choice until they pick one) shows: Developer, else Content Creator, else VIP, else
-- Beta Tester, else their highest realm's title. earned: { [id] = true }
function TitleRules.autoPick(earned)
    if earned.Developer then
        return "Developer"
    end
    if earned.ContentCreator then
        return "ContentCreator"
    end
    if earned.VIP then
        return "VIP"
    end
    if earned.BetaTester then
        return "BetaTester"
    end
    for index = #REALM_TITLES, 1, -1 do
        if earned["Realm" .. index] then
            return "Realm" .. index
        end
    end
    return nil
end

-- The title a choice shows: "Auto", "None" (nothing), or a title's id (shown only if earned).
function TitleRules.resolve(worn, earned)
    if worn == "None" then
        return nil
    elseif worn == "Auto" or worn == nil then
        return TitleRules.autoPick(earned)
    end
    return if earned[worn] then worn else TitleRules.autoPick(earned)
end

return TitleRules
