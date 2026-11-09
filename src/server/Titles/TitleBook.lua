-- A player's titles (shared/TitleRules), saved in PlayerData as Titles: the ones they have earned (Earned, kept for good)
-- and what they chose to wear (Worn: "Auto", "None", or a title's id). The title they show is the "Title" attribute on
-- the player, which every client draws over their head (TitleController). Developer is never saved: it follows
-- GameConfig.Titles.DeveloperUserIds each time they join. TitleService decides when one is earned.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local TitleRules = require(ReplicatedStorage:WaitForChild("TitleRules"))

local TitleBook = {}

local state = {} -- [player] = { earned = { [id] = true }, worn = "Auto" | "None" | id }

local function cleanWorn(worn)
    if worn == "Auto" or worn == "None" or (typeof(worn) == "string" and TitleRules.ById[worn]) then
        return worn
    end
    return "Auto"
end

function TitleBook.sanitize(raw)
    raw = if typeof(raw) == "table" then raw else {}
    local earned = {}
    if typeof(raw.Earned) == "table" then
        for _, id in raw.Earned do
            if typeof(id) == "string" and TitleRules.ById[id] and id ~= "Developer" and not table.find(earned, id) then
                table.insert(earned, id)
            end
        end
    end
    return { Earned = earned, Worn = cleanWorn(raw.Worn) }
end

local function show(player)
    local data = state[player]
    if data then
        player:SetAttribute("Title", TitleRules.resolve(data.worn, data.earned))
    end
end

function TitleBook.setupPlayer(player, progress)
    local saved = TitleBook.sanitize(progress and progress.Titles)
    local data = { earned = {}, worn = saved.Worn }
    for _, id in saved.Earned do
        data.earned[id] = true
    end
    if table.find(GameConfig.Titles.DeveloperUserIds, player.UserId) then
        data.earned.Developer = true
    end
    state[player] = data
    show(player)
end

function TitleBook.isSetUp(player)
    return state[player] ~= nil
end

function TitleBook.removePlayer(player)
    state[player] = nil
end

function TitleBook.has(player, id)
    local data = state[player]
    return data ~= nil and data.earned[id] == true
end

-- True when it is new to them.
function TitleBook.earn(player, id)
    local data = state[player]
    if not data or not TitleRules.ById[id] or data.earned[id] then
        return false
    end
    data.earned[id] = true
    show(player)
    return true
end

-- What they wear: "Auto", "None" or an earned title's id. False if they can't.
function TitleBook.wear(player, choice)
    local data = state[player]
    if not data or not (choice == "Auto" or choice == "None" or (typeof(choice) == "string" and data.earned[choice])) then
        return false
    end
    data.worn = choice
    show(player)
    return true
end

function TitleBook.exportData(player)
    local data = state[player]
    if not data then
        return nil
    end
    local earned = {}
    for _, entry in TitleRules.List do
        if data.earned[entry.Id] and entry.Id ~= "Developer" then
            table.insert(earned, entry.Id)
        end
    end
    return { Earned = earned, Worn = data.worn }
end

-- Their book, for their Titles window: what they have earned, what they chose, and what that shows.
function TitleBook.publish(player)
    local data = state[player]
    if not data then
        return
    end
    local earned = {}
    for id in data.earned do
        table.insert(earned, id)
    end
    RemoteEvents.TitleEvent:FireClient(player, "State", { Earned = earned, Worn = data.worn, Showing = player:GetAttribute("Title") })
end

return TitleBook
