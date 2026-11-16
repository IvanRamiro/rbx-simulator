-- The Hall of Records on Yggdrasil (the owner, 2026-11-16: "Display players' achievements. Show rarest pets discovered. Show
-- highest cultivation ranks. Display first players to complete special challenges"): what each board shows, where its data
-- lives and how it is worded. The server (server/Records/RecordsService) keeps the records; the client
-- (client/World/HallOfRecords) draws them on the hall's stones. Vault: Hall of Records Plan 2026-11-16.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local CodexRules = require(ReplicatedStorage:WaitForChild("CodexRules"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))

local RecordsConfig = {}

RecordsConfig.FolderName = "HallOfRecords" -- ReplicatedStorage.<FolderName>: one StringValue of JSON per board
RecordsConfig.Tag = "RecordBoard"           -- the hall's face parts; each has a Board attribute (a board id below)

-- The stores (in Studio each name starts with the StudioTestSave name, or "Studio": RecordStores).
-- The Qi ladder keeps the old leaderboard's store, so its entries carry over.
RecordsConfig.Ladders = {
    { Id = "Qi", Store = "QiLeaderboard", Rows = 10 },       -- whole Qi
    { Id = "PlayTime", Store = "HallPlayTime", Rows = 10 },  -- whole minutes in the game
    { Id = "Thieves", Store = "HallEggsSecured", Rows = 8 }, -- eggs carried home from the guardians
}
RecordsConfig.RecordStore = "HallOfRecords" -- DataStore: keys "Firsts" and "Rarest"
RecordsConfig.FeedMap = "HallFeats"         -- MemoryStore SortedMap: the Chronicle's feats

RecordsConfig.RefreshEvery = 90   -- seconds between reads of the ladders, the Firsts and the Rarest (each server)
RecordsConfig.RefreshJitter = 15  -- up to this much more, so servers don't read in step
RecordsConfig.FeedEvery = 60      -- seconds between reads of the Chronicle
RecordsConfig.WriteEvery = 120    -- seconds between a player's ladder writes (only when a value changed; always on leaving)
RecordsConfig.MaxBackoff = 600    -- the longest wait after a store keeps failing

RecordsConfig.Rarest = {
    Keep = 10,          -- hatches kept in the record
    Show = 6,           -- cards on the showcase
    MostLikely = 0.01,  -- only a hatch of 1 in 100 or rarer is a record
}
RecordsConfig.Feed = {
    Show = 9,                  -- entries in the Chronicle (four on its left page, five on its right)
    Keep = 3 * 86400,          -- seconds a feat stays in the feed
    FromRealm = 3,             -- reaching realm 3 (Spirit Core) or higher is a feat
    Rarities = { Mythical = true, Secret = true, Divine = true }, -- a hatch of these is a feat
    GiantFrom = "Legendary",   -- and a Giant of this rarity or higher
}

-- ---------- the Firsts: each set once, for good ----------
RecordsConfig.FirstGroups = { Realm = "FIRST TO REACH", Guardian = "FIRST EGG STOLEN FROM", Beast = "FIRST TO HATCH" } -- (the slabs' names)

local firsts = {}
local byId = {}
local function addFirst(entry)
    table.insert(firsts, entry)
    byId[entry.Id] = entry
end

-- the realms in order (the first realm is where everyone starts, so it has no first)
RecordsConfig.Realms = {}
for _, rank in GameConfig.Ranks do
    if RecordsConfig.Realms[#RecordsConfig.Realms] ~= rank.Realm then
        table.insert(RecordsConfig.Realms, rank.Realm)
    end
end
for index = 2, #RecordsConfig.Realms do
    addFirst({ Id = "Realm" .. index, Group = "Realm", Label = RecordsConfig.Realms[index], Realm = index })
end
local lastRank = GameConfig.Ranks[#GameConfig.Ranks]
RecordsConfig.TopRank = lastRank.Name
addFirst({ Id = "TopRank", Group = "Realm", Label = lastRank.Name, Highlight = true })

-- the guardians, in the islands' order
RecordsConfig.GuardianOrder = { "StoneLion", "MantisSage", "EmberXuanwu", "Tiangou", "Pangu" }
for _, guardianId in RecordsConfig.GuardianOrder do
    local guardian = GameConfig.Guardians[guardianId]
    if guardian then
        addFirst({ Id = "Guardian_" .. guardianId, Group = "Guardian", Label = guardian.DisplayName, Guardian = guardianId })
    end
end

-- every Divine and Secret beast that can be hatched, Divine first
local top = {}
for _, petId in CodexRules.Pets do
    local pet = GameConfig.Pets[petId]
    if pet and (pet.Rarity == "Divine" or pet.Rarity == "Secret") then
        table.insert(top, petId)
    end
end
table.sort(top, function(a, b)
    local ra, rb = GameConfig.Pets[a].Rarity, GameConfig.Pets[b].Rarity
    if ra ~= rb then
        return ra == "Divine"
    end
    return GameConfig.Pets[a].DisplayName < GameConfig.Pets[b].DisplayName
end)
for _, petId in top do
    addFirst({ Id = "Beast_" .. petId, Group = "Beast", Label = GameConfig.Pets[petId].DisplayName, PetId = petId,
        Rarity = GameConfig.Pets[petId].Rarity })
end

RecordsConfig.Firsts = firsts
RecordsConfig.FirstById = byId

-- ---------- the odds of a hatch ----------
-- How likely one egg was to give exactly this: the beast's chance in that egg's own pool (before any luck: luck changes the
-- player's odds, not how rare the beast is), times the size's chance when it is Large or Giant. nil if the egg doesn't hold it.
local SIZE_ODDS = {}
for name, info in PetRules.Sizes do
    if info.Order >= PetRules.Sizes.Large.Order then
        SIZE_ODDS[name] = info.Chance / 100
    end
end
function RecordsConfig.hatchOdds(eggId, petId, size)
    local egg = GameConfig.Eggs[eggId]
    if not egg then
        return nil
    end
    for _, entry in egg.Pool do
        if entry.PetId == petId then
            return entry.HatchChance / 100 * (SIZE_ODDS[size] or 1)
        end
    end
    return nil
end

-- ---------- words ----------
local function commas(n)
    local s = tostring(math.floor(n + 0.5))
    local out = string.reverse((string.gsub(string.reverse(s), "(%d%d%d)", "%1,")))
    return (string.gsub(out, "^,", ""))
end
RecordsConfig.commas = commas

-- "1 in 2,500"
function RecordsConfig.oneIn(odds)
    if typeof(odds) ~= "number" or odds <= 0 then
        return ""
    end
    local n = 1 / odds
    if n >= 100 then
        n = math.floor(n / 10 + 0.5) * 10 -- (no false precision: 1 in 2,500, not 1 in 2,499)
    end
    return "1 in " .. commas(n)
end

-- whole minutes as "312 h 05 m", "45 m"
function RecordsConfig.playTime(minutes)
    minutes = math.max(0, math.floor(minutes or 0))
    local hours = minutes // 60
    if hours == 0 then
        return minutes .. " m"
    end
    return commas(hours) .. " h " .. string.format("%02d", minutes % 60) .. " m"
end

-- seconds ago, in plain words
function RecordsConfig.ago(seconds)
    seconds = math.max(0, seconds)
    if seconds < 60 then
        return "just now"
    elseif seconds < 3600 then
        local m = seconds // 60
        return m .. (if m == 1 then " minute ago" else " minutes ago")
    elseif seconds < 86400 then
        local h = seconds // 3600
        return h .. (if h == 1 then " hour ago" else " hours ago")
    end
    local d = seconds // 86400
    return d .. (if d == 1 then " day ago" else " days ago")
end

local MONTHS = { "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" }
-- a unix time as "16 Nov 2026" (UTC: the same everywhere)
function RecordsConfig.date(t)
    if typeof(t) ~= "number" then
        return ""
    end
    local d = os.date("!*t", math.floor(t))
    return d.day .. " " .. MONTHS[d.month] .. " " .. d.year
end

return RecordsConfig
