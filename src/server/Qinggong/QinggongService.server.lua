-- Grants each player their rank's Qinggong level as attributes: "QinggongAirLeaps",
-- "QinggongRunSpeed", "QinggongMaxStamina", "QinggongDashSpeed" and "QinggongFlightSpeed" (0 before
-- sword flight unlocks). Sets WalkSpeed, except while meditating, when the client's hover holds it
-- at 0 and restores the run speed afterwards.
--
-- Also relays each player's Qinggong effects to everyone else. They are cosmetic, so the server
-- only checks for a known kind, a sane value and no flooding.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))

local FX_KINDS = { Takeoff = true, Leap = true, Glide = true, Land = true, Dash = true }
local FX_PER_SECOND = 8 -- above what play produces (a leap every 0.2 s at most); each is sent to everyone
local fxBudgets = {}

local function applyLevel(player, rankValue)
    local level = Ranks.getQinggong(rankValue.Value)
    player:SetAttribute("QinggongAirLeaps", level.AirLeaps)
    player:SetAttribute("QinggongRunSpeed", level.RunSpeed)
    player:SetAttribute("QinggongMaxStamina", level.Stamina)
    player:SetAttribute("QinggongDashSpeed", level.DashSpeed)
    player:SetAttribute("QinggongFlightSpeed", level.FlightSpeed)

    local humanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
    if humanoid and player:GetAttribute("IsCultivating") ~= true then
        humanoid.WalkSpeed = level.RunSpeed
    end
end

local function setupPlayer(player)
    local first = Ranks.getQinggong("")
    player:SetAttribute("QinggongRunSpeed", first.RunSpeed)
    player:SetAttribute("QinggongAirLeaps", first.AirLeaps)
    player:SetAttribute("QinggongMaxStamina", first.Stamina)
    player:SetAttribute("QinggongDashSpeed", first.DashSpeed)
    player:SetAttribute("QinggongFlightSpeed", 0)

    if not PlayerData.waitForData(player) then
        return
    end
    local leaderstats = player:WaitForChild("leaderstats", 30)
    local rankValue = leaderstats and leaderstats:WaitForChild("Rank", 30)
    if not rankValue then
        return
    end

    applyLevel(player, rankValue)
    rankValue.Changed:Connect(function()
        applyLevel(player, rankValue)
    end)
    player.CharacterAdded:Connect(function(character)
        character:WaitForChild("Humanoid")
        applyLevel(player, rankValue)
    end)
end

RemoteEvents.QinggongFxEvent.OnServerEvent:Connect(function(player, kind, value)
    if type(kind) ~= "string" or not FX_KINDS[kind] then
        return
    end
    value = if type(value) == "number" and value == value then math.clamp(value, 0, 10) else 0
    local now = os.clock()
    local budget = fxBudgets[player]
    if not budget or now - budget.start >= 1 then
        budget = { start = now, count = 0 }
        fxBudgets[player] = budget
    end
    budget.count += 1
    if budget.count > FX_PER_SECOND then
        return
    end
    for _, other in Players:GetPlayers() do
        if other ~= player then
            RemoteEvents.QinggongFxEvent:FireClient(other, player, kind, value)
        end
    end
end)

Players.PlayerRemoving:Connect(function(player)
    fxBudgets[player] = nil
end)

Players.PlayerAdded:Connect(setupPlayer)
for _, player in Players:GetPlayers() do
    task.spawn(setupPlayer, player)
end
