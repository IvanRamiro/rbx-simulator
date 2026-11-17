-- Prints the newest players' feedback (server/Feedback/FeedbackService), newest first. Read-only: it changes nothing.
--
-- How to run: open the place in Studio (Edit, no Play needed), make sure Game Settings > Security > "Enable Studio Access to
-- API Services" is on, set the options below, paste this whole file into the Command Bar (View > Command Bar) and press Enter.
-- The reports print in the Output window.
--
-- LIVE = true reads the REAL reports that players sent in the published game (the stores "BetaFeedback" and
-- "BetaFeedbackIndex", no prefix). LIVE = false reads the Studio test stores instead: the same names with the prefix a Studio
-- Play test uses (ServerStorage's StudioTestSave attribute, or "Studio" when it is not set).
local LIVE = true
local COUNT = 20          -- how many of the newest to print (at most 100)
local ONLY = nil          -- nil for every kind, or "Bug", "Idea" or "Other"

local DataStoreService = game:GetService("DataStoreService")
local ServerStorage = game:GetService("ServerStorage")

local prefix = ""
if not LIVE then
    local name = ServerStorage:GetAttribute("StudioTestSave")
    prefix = (if typeof(name) == "string" and name ~= "" then name elseif name then "StudioTestSave" else "Studio") .. "_"
end
local entries = DataStoreService:GetDataStore(prefix .. "BetaFeedback")
local index = DataStoreService:GetOrderedDataStore(prefix .. "BetaFeedbackIndex")

local ok, page = pcall(function()
    return index:GetSortedAsync(false, math.clamp(COUNT, 1, 100)):GetCurrentPage()
end)
if not ok then
    warn("read_feedback: can't read " .. prefix .. "BetaFeedbackIndex: " .. tostring(page))
    return
end

local function join(list)
    local out = {}
    for _, v in list or {} do
        table.insert(out, tostring(v))
    end
    return table.concat(out, ", ")
end

local lines = { string.format("===== %d newest feedback reports (%s) =====", #page, if LIVE then "LIVE" else "Studio test: " .. prefix) }
local shown = 0
for _, item in page do
    local got, entry = pcall(function()
        return entries:GetAsync(item.key)
    end)
    if not got then
        table.insert(lines, "  " .. item.key .. ": can't read it: " .. tostring(entry))
    elseif typeof(entry) ~= "table" then
        table.insert(lines, "  " .. item.key .. ": (gone)")
    elseif ONLY == nil or entry.Category == ONLY then
        shown += 1
        table.insert(lines, "")
        table.insert(lines, string.format("#%d  [%s]  %s  %s (@%s, %s)", shown, string.upper(tostring(entry.Category)),
            tostring(entry.When), tostring(entry.DisplayName), tostring(entry.Name), tostring(entry.UserId)))
        table.insert(lines, string.format("    %s, realm %s, island %s, at (%s), %s min into the session",
            tostring(entry.Rank), tostring(entry.Realm), tostring(entry.Island), join(entry.Position), tostring(entry.SessionMinutes)))
        table.insert(lines, string.format("    %s, screen %s, phone tier %s, place v%s, server %s",
            tostring(entry.Device), join(entry.Screen), tostring(entry.QualityLow), tostring(entry.PlaceVersion), tostring(entry.JobId)))
        for line in string.gmatch(tostring(entry.Text) .. "\n", "([^\n]*)\n") do
            table.insert(lines, "    > " .. line)
        end
        for _, err in entry.Errors or {} do
            table.insert(lines, "    ! " .. tostring(err))
        end
        table.insert(lines, "    key " .. item.key)
    end
end
print(table.concat(lines, "\n"))
