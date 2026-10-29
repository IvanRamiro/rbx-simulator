
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local TrainingEvent = require(ReplicatedStorage:WaitForChild("TrainingEvent"))

-- Last accepted training time for each player, keyed by Player
local lastTrainingTime = {}

local function setupPlayer(player)
    if player:FindFirstChild("leaderstats") then
        return
    end

    local leaderstats = Instance.new("Folder")
    leaderstats.Name = "leaderstats"

    local qi = Instance.new("IntValue")
    qi.Name = "Qi"
    qi.Value = GameConfig.StartingQi
    qi.Parent = leaderstats

    -- Parent last so clients see the finished folder all at once
    leaderstats.Parent = player
end

local function getQiValue(player)
    local leaderstats = player:FindFirstChild("leaderstats")
    return leaderstats and leaderstats:FindFirstChild("Qi")
end

-- The client sends no arguments. Anything extra it sends is ignored, so the
-- client can never choose how much Qi it receives.
local function trainPlayer(player)
    -- Ignore requests from players who are leaving or not fully set up
    if player.Parent ~= Players then
        return
    end

    local qi = getQiValue(player)
    if not qi then
        return
    end

    local now = os.clock()
    local lastTime = lastTrainingTime[player]

    if lastTime and now - lastTime < GameConfig.TrainingCooldown then
        return
    end

    lastTrainingTime[player] = now
    qi.Value += GameConfig.TrainingQiReward
end

Players.PlayerAdded:Connect(setupPlayer)

Players.PlayerRemoving:Connect(function(player)
    lastTrainingTime[player] = nil
end)

TrainingEvent.OnServerEvent:Connect(trainPlayer)

-- Handle players who joined before this script finished loading
for _, player in Players:GetPlayers() do
    setupPlayer(player)
end
