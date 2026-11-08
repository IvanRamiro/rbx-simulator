-- The Ascension Stele on Yggdrasil (WorldBuilder.buildLeaderboard): the cultivators with the most Qi
-- across every server. Each player's whole Qi goes into an OrderedDataStore every WriteEvery seconds
-- while it changes, and once more as they leave; the board re-reads the top entries every
-- RefreshEvery seconds. Without DataStores (a place not yet published, or Studio with API access
-- off) it ranks the players in this server instead. Qi is never spent, so it only climbs. Only
-- data this server saves is written (PlayerData.canSave), so fresh Studio data never lowers an
-- entry. The store keeps Qi alone: a cultivator in this server shows their own rank, any other the
-- rank their Qi reaches.
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))
local WorldConfig = require(script.Parent:WaitForChild("WorldConfig"))

local rules = WorldConfig.Leaderboard
local island = workspace:WaitForChild(WorldConfig.FolderName):WaitForChild(WorldConfig.StartIsland)
local stele = island:WaitForChild(rules.FolderName, 30)
if not stele then
    warn("LeaderboardService: no Ascension Stele on " .. WorldConfig.StartIsland .. " (WorldBuilder.buildLeaderboard)")
    return
end
local board = stele:WaitForChild("Board"):WaitForChild("SurfaceGui")
local rows = {}
for _, row in board:GetChildren() do
    local index = tonumber(string.match(row.Name, "^Row(%d+)$"))
    if index then
        rows[index] = row
    end
end

local store = nil
do
    local ok, result = pcall(function()
        return DataStoreService:GetOrderedDataStore(rules.StoreName)
    end)
    store = if ok then result else nil
    -- a Studio playtest on a test save (PlayerData) stays off the real board
    if game:GetService("RunService"):IsStudio() and game:GetService("ServerStorage"):GetAttribute("StudioTestSave") then
        store = nil
    end
end

-- DataStores that will never answer here: stop asking, and rank this server's players instead.
local function giveUpIfPermanent(err)
    local message = tostring(err)
    if string.find(message, "StudioAccessToApisNotAllowed") or string.find(message, "publish") then
        store = nil
    end
end

local names = {} -- [UserId] = name
local written = {} -- [Player] = { Qi = the last whole Qi written, At = os.clock() }

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

local function nameOf(userId)
    if not names[userId] then
        local player = Players:GetPlayerByUserId(userId)
        local ok, name = pcall(function()
            return if player then player.DisplayName else Players:GetNameFromUserIdAsync(userId)
        end)
        names[userId] = if ok then name else "Unknown cultivator"
    end
    return names[userId]
end

local function writeQi(player, force)
    local qiValue = PlayerData.getStats(player)
    if not (store and qiValue and PlayerData.canSave(player)) then
        return
    end
    local qi = math.floor(qiValue.Value)
    local last = written[player]
    if last and (last.Qi == qi or (not force and os.clock() - last.At < rules.WriteEvery)) then
        return
    end
    local ok, err = pcall(function()
        store:SetAsync(tostring(player.UserId), qi)
    end)
    if ok then
        if player.Parent then -- a write still running when the player left mustn't keep them
            written[player] = { Qi = qi, At = os.clock() }
        end
    else
        warn("LeaderboardService: couldn't record " .. player.Name .. "'s Qi: " .. tostring(err))
        giveUpIfPermanent(err)
    end
end

-- The top entries as { UserId, Qi }, best first.
local function topEntries()
    if store then
        local ok, page = pcall(function()
            return store:GetSortedAsync(false, #rows):GetCurrentPage()
        end)
        if ok then
            local entries = {}
            for _, entry in page do
                table.insert(entries, { UserId = tonumber(entry.key), Qi = entry.value })
            end
            return entries
        end
        warn("LeaderboardService: couldn't read the leaderboard: " .. tostring(page))
        giveUpIfPermanent(page)
    end
    local entries = {}
    for _, player in Players:GetPlayers() do
        local qiValue = PlayerData.getStats(player)
        if qiValue then
            table.insert(entries, { UserId = player.UserId, Qi = math.floor(qiValue.Value) })
        end
    end
    table.sort(entries, function(a, b)
        return a.Qi > b.Qi
    end)
    return entries
end

local function render(entries)
    for index, row in rows do
        local entry = entries[index]
        row.Cultivator.Text = if entry then nameOf(entry.UserId) else ""
        row.Rank.Text = if entry then rankNameFor(entry.UserId, entry.Qi) else ""
        row.Qi.Text = if entry then NumberFormat.compact(entry.Qi) else ""
    end
end

-- A player's Qi goes on the board as soon as their data loads, not at the next round.
local function onPlayerAdded(player)
    -- QiService makes leaderstats on the same data load, in no set order with this
    local stats = PlayerData.waitForData(player) and player:WaitForChild("leaderstats", 30)
    if stats and stats:WaitForChild("Qi", 30) and player.Parent == Players then
        writeQi(player, true)
        render(topEntries())
    end
end
Players.PlayerAdded:Connect(onPlayerAdded)
for _, player in Players:GetPlayers() do
    task.spawn(onPlayerAdded, player)
end

Players.PlayerRemoving:Connect(function(player)
    writeQi(player, true)
    written[player] = nil
end)

game:BindToClose(function()
    for _, player in Players:GetPlayers() do
        task.spawn(writeQi, player, true)
    end
end)

while true do
    for _, player in Players:GetPlayers() do
        task.spawn(writeQi, player, false)
    end
    render(topEntries())
    task.wait(rules.RefreshEvery)
end
