-- Spawns every guardian in GameConfig.Guardians into Workspace.Guardians from its stored model
-- (ServerStorage.Guardians.<Id>, stored by WorldBuild.GuardianBuilder) and drives its encounter
-- (Guardian.lua) with strikes, players leaving and a step every frame.
--
-- A guardian whose model isn't stored is skipped with a warning; its island's stands then hatch
-- freely (PetService only locks the eggs of a guardian standing in the world).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Combat = require(script.Parent.Parent:WaitForChild("Combat"):WaitForChild("Combat"))
local Guardian = require(script.Parent:WaitForChild("Guardian"))

local folder = workspace:FindFirstChild("Guardians") or Instance.new("Folder")
folder.Name = "Guardians"
folder.Parent = workspace

local guardians = {}

for id, config in GameConfig.Guardians do
    local stored = ServerStorage:FindFirstChild("Guardians")
    local source = stored and stored:FindFirstChild(id)
    if source then
        table.insert(guardians, Guardian.new(id, config, source, folder))
    else
        warn("GuardianService: ServerStorage.Guardians." .. id .. " isn't stored; the " .. config.DisplayName .. " is skipped")
    end
end

Combat.Hit.Event:Connect(function(player, target, damage)
    for _, guardian in guardians do
        if guardian.model == target then
            guardian:onHit(player, damage)
        end
    end
end)

Players.PlayerRemoving:Connect(function(player)
    for _, guardian in guardians do
        guardian:onPlayerRemoving(player)
    end
end)

RunService.Heartbeat:Connect(function(dt)
    for _, guardian in guardians do
        guardian:step(dt)
    end
end)
