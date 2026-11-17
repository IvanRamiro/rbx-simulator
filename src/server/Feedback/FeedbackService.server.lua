-- Players' feedback from the Feedback window (client/UI/FeedbackController), kept for the developers to read
-- (tools/roblox/read_feedback.lua). Each report is checked here (its kind, its length, the limits in GameConfig.Feedback),
-- the server adds where the player is in the game, and it is stored:
--   entries  DataStore "BetaFeedback", one key per report: "F_<server time in ms>_<userId>"
--   index    OrderedDataStore "BetaFeedbackIndex": the same key -> its time (Unix seconds), to list them newest first
--   counts   DataStore "BetaFeedbackCount", one key per player ("U_<userId>"): { Day, Count }, so rejoining doesn't reset the
--            daily limit (the 10-minute limit is kept in memory)
-- In Studio every name starts with the StudioTestSave name (or "Studio"), as the Hall of Records' do, so a test never
-- touches the real reports. Each call checks the request budget first (keeping RESERVE a minute for the player saves) and
-- tries again with a short wait.
-- What a player writes is never shown to anyone else in the game (only the developers read it, outside the game), so it
-- isn't run through the chat filter; nor is it trusted for anything: it is stored as text, and the details the client
-- sends (device, screen, errors) are checked and cut down to size.
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))

local RULES = GameConfig.Feedback
local RESERVE = 10                  -- requests a minute left for PlayerData's saves
local TRIES = 3
local BACKOFF = { 1, 2 }
local BUDGET_WAIT = 3               -- seconds to wait for budget before giving up
local ERROR_LINES, ERROR_LENGTH = 5, 200
local DEVICES = { Touch = true, Gamepad = true, Keyboard = true }
local VERSION = 1                   -- the shape of a stored report

local prefix = ""
if RunService:IsStudio() then
    local name = ServerStorage:GetAttribute("StudioTestSave")
    prefix = (if typeof(name) == "string" and name ~= "" then name elseif name then "StudioTestSave" else "Studio") .. "_"
end

local warned = {}
local function warnOnce(key, message)
    if not warned[key] then
        warned[key] = true
        warn("FeedbackService: " .. message)
    end
end

local function open(ordered, name)
    local ok, store = pcall(function()
        if ordered then
            return DataStoreService:GetOrderedDataStore(prefix .. name)
        end
        return DataStoreService:GetDataStore(prefix .. name)
    end)
    if not ok then
        warnOnce(name, "can't open " .. name .. ": " .. tostring(store))
        return nil
    end
    return store
end

local entryStore = open(false, "BetaFeedback")
local indexStore = open(true, "BetaFeedbackIndex")
local countStore = open(false, "BetaFeedbackCount")

local function hasBudget(requestType)
    local deadline = os.clock() + BUDGET_WAIT
    while true do
        local ok, budget = pcall(DataStoreService.GetRequestBudgetForRequestType, DataStoreService, requestType)
        if not ok or budget > RESERVE then
            return true
        end
        if os.clock() > deadline then
            return false
        end
        task.wait(0.5)
    end
end

-- ok, result | false, err
local function attempt(requestType, fn)
    local err = "no store"
    for try = 1, TRIES do
        if not hasBudget(requestType) then
            return false, "budget"
        end
        local ok, result = pcall(fn)
        if ok then
            return true, result
        end
        err = tostring(result)
        warnOnce(err:sub(1, 60), err)
        if try < TRIES then
            task.wait(BACKOFF[try])
        end
    end
    return false, err
end

-- ---------- the limits ----------
local recent = {}   -- [player] = { os.clock() of each report sent in the last WindowSeconds }
local busy = {}     -- [player] = true while one of theirs is being stored
local joinedAt = {} -- [player] = os.clock() when they joined (their play session's length)

local function today()
    return math.floor(os.time() / 86400) -- the day number, UTC
end

local function trimRecent(player)
    local list = recent[player] or {}
    local now = os.clock()
    for index = #list, 1, -1 do
        if now - list[index] >= RULES.WindowSeconds then
            table.remove(list, index)
        end
    end
    recent[player] = list
    return list
end

-- counts one more for today; false, reason when the day's limit is reached or the store can't answer
local function countToday(player)
    if not countStore then
        return false, "busy"
    end
    local full = false
    local ok = attempt(Enum.DataStoreRequestType.UpdateAsync, function()
        countStore:UpdateAsync("U_" .. player.UserId, function(stored)
            local day = today()
            local count = if typeof(stored) == "table" and stored.Day == day and typeof(stored.Count) == "number" then stored.Count else 0
            if count >= RULES.PerDay then
                full = true
                return nil -- (unchanged)
            end
            full = false
            return { Day = day, Count = count + 1 }, { player.UserId }
        end)
    end)
    if not ok then
        return false, "busy"
    end
    if full then
        return false, "day"
    end
    return true
end

-- ---------- checking what the client sent ----------
local function cleanText(text)
    if typeof(text) ~= "string" or #text > RULES.MaxLength * 4 or not utf8.len(text) then
        return nil
    end
    text = string.gsub(text, "[%z\1-\8\11-\31\127]", "") -- control characters out (new lines and tabs stay)
    text = string.gsub(string.gsub(text, "^%s+", ""), "%s+$", "")
    local length = utf8.len(text)
    if not length or length < RULES.MinLength or length > RULES.MaxLength then
        return nil
    end
    return text
end

local function cleanNumber(value, low, high)
    if typeof(value) ~= "number" or value ~= value then
        return nil
    end
    return math.clamp(math.round(value), low, high)
end

local function cleanErrors(list)
    local out = {}
    if typeof(list) ~= "table" then
        return out
    end
    for index = 1, ERROR_LINES do
        local line = list[index]
        if typeof(line) == "string" then
            line = string.sub(line, 1, ERROR_LENGTH)
            if utf8.len(line) then -- (a cut through a character makes it invalid: dropped)
                table.insert(out, (string.gsub(line, "[%z\1-\8\11-\31\127]", "")))
            end
        end
    end
    return out
end

-- ---------- what the server adds ----------
local function aboutPlayer(player)
    local rankName = Ranks.getPlayerRankName(player)
    local rank = rankName and Ranks.getRank(rankName)
    local position = nil
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if root then
        local p = root.Position
        position = { math.round(p.X), math.round(p.Y), math.round(p.Z) }
    end
    return {
        UserId = player.UserId,
        Name = player.Name,
        DisplayName = player.DisplayName,
        Rank = rankName,
        Realm = rank and rank.Realm or nil,
        Island = player:GetAttribute("Island"),
        Position = position,
        PlaceVersion = game.PlaceVersion,
        JobId = if game.JobId ~= "" then game.JobId else "Studio",
        SessionMinutes = math.round((os.clock() - (joinedAt[player] or os.clock())) / 6) / 10,
    }
end

local function reply(player, ok, message)
    if player.Parent == Players then
        RemoteEvents.FeedbackEvent:FireClient(player, "Result", { Ok = ok, Message = message })
    end
end

local MESSAGES = {
    invalid = "Please pick Bug, Idea or Other, and write " .. RULES.MinLength .. " to " .. RULES.MaxLength .. " characters.",
    day = "You've reached today's feedback limit. Thank you for all of it! You can send more tomorrow.",
    busy = "We couldn't send your feedback right now. Please try again in a minute.",
}

local function send(player, data)
    if typeof(data) ~= "table" then
        return reply(player, false, MESSAGES.invalid)
    end
    local category = data.Category
    local text = cleanText(data.Text)
    if typeof(category) ~= "string" or not table.find(RULES.Categories, category) or not text then
        return reply(player, false, MESSAGES.invalid)
    end
    local list = trimRecent(player)
    if #list >= RULES.PerWindow then
        local wait = math.max(1, math.ceil((RULES.WindowSeconds - (os.clock() - list[1])) / 60))
        return reply(player, false, "You've sent a lot of feedback just now. Please wait " .. wait
            .. (if wait == 1 then " minute" else " minutes") .. " and try again.")
    end
    if not (entryStore and indexStore) then
        return reply(player, false, MESSAGES.busy)
    end
    table.insert(list, os.clock()) -- (held while it is stored: two quick sends can't both slip under the limit)
    local counted, why = countToday(player)
    if not counted then
        table.remove(list)
        return reply(player, false, MESSAGES[why] or MESSAGES.busy)
    end

    local screen = if typeof(data.Screen) == "table" then data.Screen else {}
    local entry = aboutPlayer(player)
    local now = workspace:GetServerTimeNow()
    entry.Version = VERSION
    entry.Category = category
    entry.Text = text
    entry.Time = math.floor(now)
    entry.When = DateTime.fromUnixTimestamp(math.floor(now)):ToIsoDate()
    entry.Device = if typeof(data.Device) == "string" and DEVICES[data.Device] then data.Device else "Unknown"
    entry.Screen = { cleanNumber(screen[1], 0, 10000) or 0, cleanNumber(screen[2], 0, 10000) or 0 }
    entry.QualityLow = data.QualityLow == true
    entry.Errors = cleanErrors(data.Errors)
    local key = "F_" .. math.floor(now * 1000) .. "_" .. player.UserId

    local ok = attempt(Enum.DataStoreRequestType.SetIncrementAsync, function()
        entryStore:SetAsync(key, entry, { player.UserId })
    end)
    if ok then
        -- the index only lists it; if it fails the report is still kept (the reader can also list the store's keys)
        attempt(Enum.DataStoreRequestType.SetIncrementSortedAsync, function()
            indexStore:SetAsync(key, entry.Time)
        end)
        reply(player, true)
    else
        table.remove(list)
        reply(player, false, MESSAGES.busy)
    end
end

RemoteEvents.FeedbackEvent.OnServerEvent:Connect(function(player, action, data)
    if action ~= "Send" or busy[player] then
        return
    end
    busy[player] = true
    local ok, err = pcall(send, player, data)
    busy[player] = nil
    if not ok then
        warnOnce("send" .. tostring(err):sub(1, 60), "a report failed: " .. tostring(err))
        reply(player, false, MESSAGES.busy)
    end
end)

Players.PlayerAdded:Connect(function(player)
    joinedAt[player] = os.clock()
end)
for _, player in Players:GetPlayers() do
    joinedAt[player] = joinedAt[player] or os.clock()
end
Players.PlayerRemoving:Connect(function(player)
    recent[player] = nil
    busy[player] = nil
    joinedAt[player] = nil
end)
