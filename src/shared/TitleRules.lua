-- Every title a cultivator can earn and wear (the owner, November 9, 2026): Developer, Content Creator, VIP (the pass, November 10), Beta Tester, one for each of the twelve
-- realms, one for securing an egg from each guardian, the beast collector titles, Keeper of Secrets and Relic Seeker.
-- A worn title shows over the player's head (TitleController) in its own colour, a sheen of light sweeping across it now and
-- then; a Shimmer is the colour of a grander title's sheen (it sweeps more often).
-- The Developer title alone has a Style (the owner, 2026-11-24: "apply it only to developer title, keep the other sheen and typography as it is"): the
-- ornate banner round its words on the nameplate (client/UI/TitleBanner draws rendered art: a gold-and-steel plate with wings and a crowned crystal),
-- with Concept (the idea, in words), Depth (the colour of a layer under the letters, so they read at a distance) and Rule (the colour the banner's glow
-- is tinted). Every other title shows as it always did: its own lettering and colour, its sheen.
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
    { Id = "Faction", Name = "FACTION" },
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
        How = if index == 1 then "Start cultivating in the Qi Awakening realm."
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

-- The factions' titles (GameConfig.Faction): given to a member for good (TitleService reads their Faction). No bonus: the factions are
-- equal in power. Each in its faction's colour.
local FACTION_TITLES = { Orthodox = "Orthodox Disciple", Unorthodox = "Unorthodox Wanderer", Demonic = "Demonic Blade" }
for _, factionId in GameConfig.Faction.Order do
    local info = GameConfig.Faction.Factions[factionId]
    add({ Id = info.TitleId, Group = "Faction", Text = FACTION_TITLES[factionId], Color = info.Color,
        Shimmer = info.Color:Lerp(Color3.new(1, 1, 1), 0.55), Faction = factionId,
        How = "Join the " .. info.DisplayName .. " at " .. info.Hq .. ". Only its members wear it." })
end

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
    OrthodoxDisciple = { "RomanAntique", 400 },  -- a stone-cut hand: disciplined
    UnorthodoxWanderer = { "Fondamento", 400, "Italic" }, -- a free brush hand
    DemonicBlade = { "GrenzeGotisch", 700 },     -- blackletter
}

for order, entry in TitleRules.List do
    entry.Order = order
    entry.Font = FONTS[entry.Id] or { "Merriweather", 700 }
end

-- (the Forge: ember letters on deep crimson, a banner of gold and steel with a glow the colour of the Rule)
TitleRules.ById.Developer.Style = { Concept = "The Forge: the maker's mark, ember letters on deep crimson in a gold and steel banner", Depth = rgb(96, 14, 26),
    Rule = rgb(255, 206, 96) }

-- What a worn title gives (the owner, 2026-11-18: "ADDITIONAL BONUS ON TITLES: ATTACK BOOST, QI BOOST, MUTATION BOOST, LUCK BOOST,
-- SPIRIT STONE BOOST"): one bonus each, only while it is the one they show, so the choice matters. Kind: "Attack" (their strikes'
-- damage), "Qi" (every Qi they earn), "Mutation" (every mutation's chance on a hatch), "Luck" (their luck: rare beasts and the
-- Grand mutations, with the Luck pass's), "Stones" (the Spirit Stones of a daily reward and a spin: not a pet's sale, so no loop).
-- Percent: kept small. The realms give Qi, climbing with them; each guardian's thief title, Attack; the collector titles, Luck
-- and Mutation; Keeper of Secrets, Mutation; Relic Seeker and Beta Tester, Stones. Developer, Content Creator and VIP give none
-- (VIP has its own pass perks). Mutation stays at 8% or less: with it and the Luck pass, a Merchant egg's pet still sells back for
-- under its price (about 0.999; re-check with tools/balance/progression_sim.py before raising any of these).
TitleRules.BonusKinds = {
    Attack = { Name = "Attack" },
    Qi = { Name = "Qi" },
    Mutation = { Name = "Mutation chance" },
    Luck = { Name = "Luck" },
    Stones = { Name = "Spirit Stones" },
}
local BONUSES = {
    Realm1 = { "Qi", 1 }, Realm2 = { "Qi", 1 }, Realm3 = { "Qi", 2 }, Realm4 = { "Qi", 2 }, Realm5 = { "Qi", 3 }, Realm6 = { "Qi", 3 },
    Realm7 = { "Qi", 4 }, Realm8 = { "Qi", 4 }, Realm9 = { "Qi", 5 }, Realm10 = { "Qi", 5 }, Realm11 = { "Qi", 6 }, Realm12 = { "Qi", 6 },
    PrideThief = { "Attack", 3 }, BambooShadow = { "Attack", 4 }, Ashwalker = { "Attack", 5 }, MoonSaver = { "Attack", 6 },
    PangusRival = { "Attack", 8 },
    BeastSeeker = { "Luck", 2 }, BeastTamer = { "Mutation", 4 }, BeastMaster = { "Luck", 6 }, CodexKeeper = { "Mutation", 8 },
    SecretKeeper = { "Mutation", 6 }, RelicSeeker = { "Stones", 15 }, BetaTester = { "Stones", 5 },
}
for id, bonus in BONUSES do
    assert(TitleRules.ById[id] and TitleRules.BonusKinds[bonus[1]], "TitleRules: a bonus for an unknown title or kind: " .. id)
    TitleRules.ById[id].Bonus = { Kind = bonus[1], Percent = bonus[2] }
end

-- "+3% Qi", or nil for a title with no bonus
function TitleRules.bonusText(entry)
    local bonus = entry and entry.Bonus
    return if bonus then "+" .. bonus.Percent .. "% " .. TitleRules.BonusKinds[bonus.Kind].Name else nil
end

-- the multiplier of that kind from the title the player shows now (their "Title" attribute, set by the server: TitleBook), 1 if none
function TitleRules.multiplier(player, kind)
    local entry = player and TitleRules.ById[player:GetAttribute("Title") or ""]
    local bonus = entry and entry.Bonus
    return if bonus and bonus.Kind == kind then 1 + bonus.Percent / 100 else 1
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
