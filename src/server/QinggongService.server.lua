-- Grants each player the Qinggong level of their rank: the number of mid-air leaps and the run
-- speed (the "QinggongAirLeaps" and "QinggongRunSpeed" attributes). WalkSpeed is set here except
-- while the player meditates, when the client's hover holds it at 0 and restores the run speed.
--
-- Also relays each player's Qinggong effects (takeoff, leap, glide, land) to everyone else, so
-- they see them too. The effects are cosmetic, so the server only checks that the event is a
-- known kind with a sane value and that a player is not flooding it.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local PlayerData = require(script.Parent:WaitForChild("PlayerData"))

local FX_KINDS = { Takeoff = true, Leap = true, Glide = true, Land = true }
local FX_PER_SECOND = 20 -- far above what play produces (a leap every 0.2 s at most)
local fxBudgets = {}

local function applyLevel(player, rankValue)
    local level = Ranks.getQinggong(rankValue.Value)
    player:SetAttribute("QinggongAirLeaps", level.AirLeaps)
    player:SetAttribute("QinggongRunSpeed", level.RunSpeed)

    local humanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
    if humanoid and player:GetAttribute("IsCultivating") ~= true then
        humanoid.WalkSpeed = level.RunSpeed
    end
end

local function setupPlayer(player)
    local first = Ranks.getQinggong("")
    player:SetAttribute("QinggongAirLeaps", first.AirLeaps)

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
