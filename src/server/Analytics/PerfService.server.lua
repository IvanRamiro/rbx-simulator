-- Each player's device, measured as they play (client/Performance/PerfProbe): its frame rate and memory every two minutes,
-- logged for the Creator Dashboard as ClientFps (the average; by device, and the slow end in a band) and ClientMemory (MB;
-- by device, in a band). Bands, not numbers, as the breakdowns: a dashboard splits by each distinct value.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Analytics = require(script.Parent:WaitForChild("Analytics"))

local MIN_GAP = 90 -- seconds between one player's reports (they send every 120)
local DEVICES = { Phone = true, Tablet = true, PC = true, Console = true }

local last = {}

local function band(value, edges, labels)
    for i, edge in edges do
        if value < edge then
            return labels[i]
        end
    end
    return labels[#labels]
end

RemoteEvents.PerfEvent.OnServerEvent:Connect(function(player, fps, low, memory, device, phoneTier)
    if typeof(fps) ~= "number" or typeof(low) ~= "number" or typeof(memory) ~= "number" or not DEVICES[device] then
        return
    end
    if fps ~= fps or low ~= low or memory ~= memory or fps <= 0 or fps > 1000 or low <= 0 or memory <= 0 or memory > 100000 then
        return
    end
    if os.clock() - (last[player] or -math.huge) < MIN_GAP then
        return
    end
    last[player] = os.clock()
    local tier = if phoneTier == true then " (phone tier)" else ""
    Analytics.event(player, "ClientFps", math.round(fps), device .. tier,
        "slowest 5%: " .. band(low, { 20, 30, 45 }, { "under 20", "20 to 30", "30 to 45", "45 and up" }))
    Analytics.event(player, "ClientMemory", math.round(memory), device .. tier,
        band(memory, { 1000, 1500, 2000, 3000 }, { "under 1 GB", "1 to 1.5 GB", "1.5 to 2 GB", "2 to 3 GB", "3 GB and up" }))
end)

Players.PlayerRemoving:Connect(function(player)
    last[player] = nil
end)
