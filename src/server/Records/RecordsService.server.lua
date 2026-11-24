-- The Hall of Records on Yggdrasil (shared/RecordsConfig; the hall itself: WorldBuilder.buildHallOfRecords; its boards drawn by
-- client/World/HallOfRecords). Keeps the records every server shares and publishes each board's data, as JSON, in a StringValue
-- under ReplicatedStorage.HallOfRecords (Qi, PlayTime, Thieves, Rarest, Firsts, Feed), changed only when its data changes.
--   ladders   each player's Qi, play time (whole minutes) and eggs carried home go to an OrderedDataStore each, at most every
--             RecordsConfig.WriteEvery seconds and only when changed, and once more as they leave; the top rows are read every
--             RefreshEvery seconds (plus a jitter). Only data this server saves is written (PlayerData.canSave).
--   Firsts    a first this server sees (a realm reached, the top rank, a guardian's first egg carried home, a Divine or Secret
--             beast's first hatch) that its copy of the record lacks is claimed with UpdateAsync, which sets it only if it is still
--             free: a first is never overwritten.
--   Rarest    a hatch of 1 in 100 or rarer that beats this server's copy of the rarest ten is added with UpdateAsync (capped).
--   Feed      the Chronicle: big moments go to a MemoryStore SortedMap for every server (and show here at once).
-- A store that keeps failing is asked again after a wait that doubles, up to RecordsConfig.MaxBackoff. Without DataStores (an
-- unpublished place, Studio with API access off) the ladders show this server's players and the rest stays this server's.
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserService = game:GetService("UserService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PassRules = require(ReplicatedStorage:WaitForChild("PassRules"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RecordsConfig = require(ReplicatedStorage:WaitForChild("RecordsConfig"))

local serverRoot = script.Parent.Parent
local PlayerData = require(serverRoot:WaitForChild("Data"):WaitForChild("PlayerData"))
local Quests = require(serverRoot:WaitForChild("Quests"):WaitForChild("Quests"))
local RecordBook = require(script.Parent:WaitForChild("RecordBook"))
local RecordStores = require(script.Parent:WaitForChild("RecordStores"))
local RecordsCore = require(script.Parent:WaitForChild("RecordsCore"))

local LADDER = {}
for _, ladder in RecordsConfig.Ladders do
    LADDER[ladder.Id] = ladder
end
local CLAIM_EVERY = 5 -- seconds between flushes of this server's pending first and rarest claims

-- ---------- the published boards ----------
local folder = ReplicatedStorage:FindFirstChild(RecordsConfig.FolderName) or Instance.new("Folder")
folder.Name = RecordsConfig.FolderName
local values = {}
for _, id in { "Qi", "PlayTime", "Thieves", "Rarest", "Firsts", "Feed" } do
    local value = folder:FindFirstChild(id) or Instance.new("StringValue")
    value.Name = id
    value.Parent = folder
    values[id] = value
end
folder.Parent = ReplicatedStorage

local function publish(id, data)
    local ok, json = pcall(HttpService.JSONEncode, HttpService, data)
    if ok and values[id].Value ~= json then
        values[id].Value = json
    end
end

-- ---------- names (public only: display names and usernames) ----------
local names = {} -- [userId] = { d = display name, u = username }
local function resolveNames(userIds)
    local missing = {}
    for userId in userIds do
        if not names[userId] then
            local player = Players:GetPlayerByUserId(userId)
            if player then
                names[userId] = { d = player.DisplayName, u = player.Name }
            else
                table.insert(missing, userId)
            end
        end
    end
    for start = 1, #missing, 200 do
        local batch = table.move(missing, start, math.min(start + 199, #missing), 1, {})
        local ok, infos = pcall(UserService.GetUserInfosByUserIdsAsync, UserService, batch)
        if ok then
            for _, info in infos do
                names[info.Id] = { d = info.DisplayName, u = info.Username }
            end
        end
    end
end
local function nameOf(userId, stored)
    local known = names[userId]
    return if known then known.d else (if stored and stored ~= "" then stored else "A cultivator"), known and known.u or ""
end

-- ---------- backoff ----------
local nextTry = {}  -- [source] = os.clock() when it may be asked again
local waitFor = {}  -- [source] = the current wait after failures
local function ready(source)
    return os.clock() >= (nextTry[source] or 0)
end
local function result(source, ok)
    if ok then
        waitFor[source] = nil
    else
        waitFor[source] = math.min((waitFor[source] or 15) * 2, RecordsConfig.MaxBackoff)
        nextTry[source] = os.clock() + waitFor[source]
    end
end

-- ---------- what this server knows ----------
local ladderRows = {} -- [ladder id] = { { UserId, Value }, ... }
local firsts = {}     -- RecordsCore.sanitizeFirsts form
local rarest = {}     -- RecordsCore.sanitizeRarest form
local feed = {}       -- newest first: { k, u, n, ... , t }
local pendingFirsts = {} -- [first id] = claim
local pendingRarest = {} -- { hatch, ... }

local function rankNameFor(userId, qi)
    local player = Players:GetPlayerByUserId(userId)
    local own = player and Ranks.getPlayerRankName(player)
    if own and own ~= "" then
        return own
    end
    local best = GameConfig.Ranks[1]
    for _, rank in GameConfig.Ranks do
        if rank.QiRequired <= qi then
            best = rank
        end
    end
    return best.Name
end

-- each player's values now (nil before their data loads)
local function valuesOf(player)
    local qi = PlayerData.getStats(player)
    local minutes, eggs = RecordBook.playMinutes(player), RecordBook.eggsSecured(player)
    if not (qi and minutes and eggs) then
        return nil
    end
    return { Qi = math.floor(qi.Value), PlayTime = minutes, Thieves = eggs }
end

-- a ladder's rows from this server's players alone (no store here)
local function localRows(id)
    local rows = {}
    for _, player in Players:GetPlayers() do
        local v = valuesOf(player)
        if v and v[id] > 0 then
            table.insert(rows, { UserId = player.UserId, Value = v[id] })
        end
    end
    table.sort(rows, function(a, b)
        return a.Value > b.Value
    end)
    while #rows > LADDER[id].Rows do
        table.remove(rows)
    end
    return rows
end

local function publishAll()
    local ids = {}
    for _, rows in ladderRows do
        for _, row in rows do
            ids[row.UserId] = true
        end
    end
    for _, e in firsts do
        ids[e.u] = true
    end
    for _, e in rarest do
        ids[e.u] = true
    end
    for _, e in feed do
        ids[e.u] = true
    end
    resolveNames(ids)
    for id, ladder in LADDER do
        local rows = {}
        for _, row in ladderRows[id] or localRows(id) do
            local display, username = nameOf(row.UserId)
            table.insert(rows, { u = row.UserId, d = display, un = username, v = row.Value,
                r = if id == "Qi" then rankNameFor(row.UserId, row.Value) else nil })
            if #rows >= ladder.Rows then
                break
            end
        end
        publish(id, { rows = rows })
    end
    local firstRows = {}
    for id, e in firsts do
        firstRows[id] = { u = e.u, d = (nameOf(e.u, e.n)), t = e.t }
    end
    publish("Firsts", { firsts = firstRows })
    local cards = {}
    for _, e in rarest do
        if #cards >= RecordsConfig.Rarest.Show then
            break
        end
        table.insert(cards, { u = e.u, d = (nameOf(e.u, e.n)), p = e.p, s = e.s, m = e.m, o = e.o, t = e.t })
    end
    publish("Rarest", { rows = cards })
    local lines = {}
    for _, e in feed do
        local line = table.clone(e)
        line.d = (nameOf(e.u, e.n))
        line.n = nil
        table.insert(lines, line)
        if #lines >= RecordsConfig.Feed.Show then
            break
        end
    end
    publish("Feed", { rows = lines })
end

-- ---------- the Chronicle ----------
local feedTie = 0
local function addFeat(feat)
    feat.t = os.time()
    feedTie += 1
    local key = RecordsCore.feedKey(workspace:GetServerTimeNow(), feedTie + math.random(0, 999) * 10)
    feat.key = key
    table.insert(feed, 1, feat)
    while #feed > RecordsConfig.Feed.Show do
        table.remove(feed)
    end
    publishAll()
    task.spawn(function()
        local ok = RecordStores.feed.add(key, feat)
        result("feedWrite", ok)
    end)
end

-- ---------- claims ----------
local function claimFirst(player, id)
    if firsts[id] or pendingFirsts[id] or not RecordsConfig.FirstById[id] or not PlayerData.canSave(player) then
        return
    end
    pendingFirsts[id] = { u = player.UserId, n = player.DisplayName, t = os.time() }
end

local function flushFirsts()
    if next(pendingFirsts) == nil or not ready("firsts") then
        return
    end
    local claims = pendingFirsts
    pendingFirsts = {}
    if not RecordStores.available("data") then
        -- no store here: this server keeps its own firsts
        for id, claim in claims do
            firsts[id] = firsts[id] or claim
        end
        publishAll()
        return
    end
    local now
    local ok = RecordStores.records.update("Firsts", function(stored)
        local toStore, record = RecordsCore.mergeFirsts(RecordsCore.sanitizeFirsts(stored, nil), claims)
        now = record
        return toStore
    end)
    result("firsts", ok)
    if not ok then
        for id, claim in claims do -- (tried again later; one claimed meanwhile by another server stays theirs)
            pendingFirsts[id] = pendingFirsts[id] or claim
        end
        return
    end
    local before = firsts
    firsts = RecordsCore.sanitizeFirsts(now, RecordsConfig.FirstById)
    for id, claim in claims do
        local entry = firsts[id]
        if entry and entry.u == claim.u and entry.t == claim.t and not before[id] then
            addFeat({ k = "First", u = claim.u, n = claim.n, f = id })
        end
    end
    publishAll()
end

local function flushRarest()
    if #pendingRarest == 0 or not ready("rarest") then
        return
    end
    local claims = pendingRarest
    pendingRarest = {}
    local keep = RecordsConfig.Rarest.Keep
    if not RecordStores.available("data") then
        local _, merged = RecordsCore.mergeRarest(rarest, claims, keep)
        rarest = merged
        publishAll()
        return
    end
    local now
    local ok = RecordStores.records.update("Rarest", function(stored)
        local toStore, list = RecordsCore.mergeRarest(stored, claims, keep)
        now = list
        return toStore
    end)
    result("rarest", ok)
    if not ok then
        table.move(claims, 1, #claims, #pendingRarest + 1, pendingRarest)
        return
    end
    rarest = now
    publishAll()
end

-- ---------- reading the stores ----------
local function refresh()
    for id, ladder in LADDER do
        if RecordStores.available("data") and ready("ladder" .. id) then
            local ok, rows = RecordStores.ladder(ladder.Store).top(ladder.Rows)
            result("ladder" .. id, ok)
            if ok then
                ladderRows[id] = rows
            end
        end
        if not RecordStores.available("data") then
            ladderRows[id] = nil -- (publishAll ranks this server's players)
        end
    end
    if RecordStores.available("data") then
        if ready("firstsRead") then
            local ok, stored = RecordStores.records.get("Firsts")
            result("firstsRead", ok)
            if ok then
                firsts = RecordsCore.sanitizeFirsts(stored, RecordsConfig.FirstById)
            end
        end
        if ready("rarestRead") then
            local ok, stored = RecordStores.records.get("Rarest")
            result("rarestRead", ok)
            if ok then
                rarest = RecordsCore.sanitizeRarest(stored, RecordsConfig.Rarest.Keep)
            end
        end
    end
    publishAll()
end

local function refreshFeed()
    if not (RecordStores.available("memory") and ready("feed")) then
        return
    end
    local ok, items = RecordStores.feed.latest(RecordsConfig.Feed.Show)
    result("feed", ok)
    if not ok then
        return
    end
    -- the shared feed, with this server's own feats it doesn't hold yet (a write can take a moment)
    local merged, seen = {}, {}
    for _, e in items do
        if typeof(e) == "table" and typeof(e.key) == "string" and typeof(e.u) == "number" and typeof(e.t) == "number" then
            seen[e.key] = true
            table.insert(merged, e)
        end
    end
    for _, e in feed do
        if not seen[e.key] and os.time() - e.t < 120 then
            table.insert(merged, e)
        end
    end
    table.sort(merged, function(a, b)
        return a.key > b.key
    end)
    feed = merged
    publishAll()
end

-- ---------- writing the ladders ----------
local written = {} -- [player] = { [ladder id] = { value, at } }
local lastKnown = {} -- [player] = { values = valuesOf, canSave = bool }: what to write as they leave

local function writeLadders(player, force)
    local known = lastKnown[player]
    local now = valuesOf(player)
    if now then
        lastKnown[player] = { values = now, canSave = PlayerData.canSave(player) }
        known = lastKnown[player]
    end
    if not (known and known.canSave and RecordStores.available("data")) then
        return
    end
    -- (held in a local: each write below yields, and the player may leave meanwhile: setupPlayer's leave clears written[player], and the next
    -- ladder's `written[player][id]` raised "attempt to index nil with 'Thieves'", seen in Play on 2026-11-24)
    local mine = written[player] or {}
    written[player] = mine
    for id, ladder in LADDER do
        local value = known.values[id]
        local last = mine[id]
        if value > 0 and not (last and (last.value == value or (not force and os.clock() - last.at < RecordsConfig.WriteEvery))) then
            local ok = RecordStores.ladder(ladder.Store).set(player.UserId, value)
            if ok and written[player] == mine then
                mine[id] = { value = value, at = os.clock() }
            end
        end
    end
end

-- ---------- the moments ----------
local realmOf = {} -- [player] = their realm's index, as last seen

local function realmIndex(rankName)
    local rank = Ranks.getRank(rankName)
    return rank and table.find(RecordsConfig.Realms, rank.Realm) or 1
end

local function sawRank(player, rankName, fromJoin)
    local index = realmIndex(rankName)
    for realm = 2, index do
        claimFirst(player, "Realm" .. realm)
    end
    if rankName == RecordsConfig.TopRank then
        claimFirst(player, "TopRank")
    end
    local before = realmOf[player]
    realmOf[player] = index
    if not fromJoin and before and index > before and index >= RecordsConfig.Feed.FromRealm then
        addFeat({ k = "Realm", u = player.UserId, n = player.DisplayName, r = RecordsConfig.Realms[index] })
    end
end

local function onHatched(player, eggId, petId, size, mutation)
    local pet = GameConfig.Pets[petId]
    if not pet or player.Parent ~= Players then
        return
    end
    -- (after the egg breaks open, so nothing here spoils the hatcher's reveal)
    task.wait(GameConfig.HatchingAltar.Stage + 1)
    if player.Parent ~= Players then
        return
    end
    claimFirst(player, "Beast_" .. petId)
    local odds = RecordsConfig.hatchOdds(eggId, petId, size, mutation)
    if odds and PlayerData.canSave(player)
        and RecordsCore.qualifies(rarest, odds, RecordsConfig.Rarest.Keep, RecordsConfig.Rarest.MostLikely) then
        table.insert(pendingRarest, { id = HttpService:GenerateGUID(false), u = player.UserId, n = player.DisplayName, p = petId,
            s = size, m = mutation, e = eggId, o = odds, t = os.time() })
    end
    local order = PassRules.RarityOrder[pet.Rarity] or 1
    local rules = RecordsConfig.Feed
    if rules.Rarities[pet.Rarity] or (size == "Giant" and order >= PassRules.RarityOrder[rules.GiantFrom]) or rules.Sizes[size]
        or (mutation and rules.Mutations[mutation]) or (odds and odds < rules.RarerThan) then
        addFeat({ k = "Hatch", u = player.UserId, n = player.DisplayName, p = petId, s = size, m = mutation, o = odds })
    end
end
RecordBook.Hatched.Event:Connect(onHatched)

Quests.Moment.Event:Connect(function(player, kind, guardianId)
    if kind == "Secure" and typeof(guardianId) == "string" then
        RecordBook.addEggSecured(player)
        PlayerData.saveSoon(player)
        claimFirst(player, "Guardian_" .. guardianId)
    end
end)

-- ---------- players ----------
local function setupPlayer(player)
    local progress, isNew = PlayerData.waitForData(player)
    if not progress or player.Parent ~= Players then
        return
    end
    RecordBook.setupPlayer(player, if isNew then nil else progress)
    local stats = player:WaitForChild("leaderstats", 30)
    local rank = stats and stats:WaitForChild("Rank", 30)
    if not rank or player.Parent ~= Players then
        return
    end
    sawRank(player, rank.Value, true)
    rank.Changed:Connect(function(value)
        sawRank(player, value, false)
    end)
    writeLadders(player, true)
    -- the values written as they leave follow every change of their Qi: PlayerData.release clears their data before PlayerRemoving runs here, so the last
    -- write fell back to what was seen up to 30 s earlier and the Qi they earned in their last seconds was missing (bug audit, 2026-11-24)
    local qi = PlayerData.getStats(player)
    if qi then
        qi.Changed:Connect(function()
            local now = valuesOf(player)
            if now and lastKnown[player] then
                lastKnown[player] = { values = now, canSave = PlayerData.canSave(player) }
            end
        end)
    end
    publishAll()
end

Players.PlayerAdded:Connect(setupPlayer)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end

Players.PlayerRemoving:Connect(function(player)
    writeLadders(player, true)
    written[player] = nil
    lastKnown[player] = nil
    realmOf[player] = nil
end)

game:BindToClose(function()
    for _, player in Players:GetPlayers() do
        task.spawn(writeLadders, player, true)
    end
    task.spawn(flushFirsts)
    task.spawn(flushRarest)
    task.wait(2)
end)

-- the claims, every few seconds
task.spawn(function()
    while true do
        task.wait(CLAIM_EVERY)
        flushFirsts()
        flushRarest()
    end
end)

-- the players' own lines (minutes tick) and their ladder writes
task.spawn(function()
    while true do
        task.wait(30)
        for _, player in Players:GetPlayers() do
            RecordBook.publish(player)
            task.spawn(writeLadders, player, false)
        end
    end
end)

task.spawn(function()
    while true do
        refreshFeed()
        task.wait(RecordsConfig.FeedEvery)
    end
end)

while true do
    refresh()
    task.wait(RecordsConfig.RefreshEvery + math.random() * RecordsConfig.RefreshJitter)
end
