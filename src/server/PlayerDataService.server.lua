
local Players = game:GetService("Players")

local PlayerData = require(script.Parent:WaitForChild("PlayerData"))

Players.PlayerAdded:Connect(PlayerData.startLoading)
Players.PlayerRemoving:Connect(PlayerData.release)

-- Give final saves time to finish when the server shuts down
game:BindToClose(PlayerData.releaseAll)

-- Handle players who joined before this script finished loading
for _, player in Players:GetPlayers() do
    PlayerData.startLoading(player)
end

-- Autosave everyone regularly. Each save runs on its own so one slow save
-- doesn't hold up the others.
while true do
    task.wait(PlayerData.AUTOSAVE_INTERVAL)

    for _, player in Players:GetPlayers() do
        task.spawn(PlayerData.save, player)
    end
end
