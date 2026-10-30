local Players = game:GetService("Players")

local PlayerData = require(script.Parent:WaitForChild("PlayerData"))

Players.PlayerAdded:Connect(PlayerData.startLoading)
Players.PlayerRemoving:Connect(PlayerData.release)

game:BindToClose(PlayerData.releaseAll)

for _, player in Players:GetPlayers() do
    PlayerData.startLoading(player)
end

while true do
    task.wait(PlayerData.AUTOSAVE_INTERVAL)

    for _, player in Players:GetPlayers() do
        task.spawn(PlayerData.save, player)
    end
end
