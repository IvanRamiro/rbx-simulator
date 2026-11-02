-- Spawns every guardian in GameConfig.Guardians into Workspace.Guardians from its stored model
-- (ServerStorage.Guardians.<Id>, stored by WorldBuild.GuardianBuilder) and drives its encounter
-- (Guardian.lua) with strikes, players leaving and a step every frame. Its island's egg stands
-- (EggStands.lua) are what it guards: a stand's "Take" goes to it.
--
-- A guardian whose model or one of whose egg meshes (ServerStorage.EggMeshes) isn't stored is
-- skipped with a warning; its island's stands then can't be taken (a stand's "Take" finds no
-- guardian to go through).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Combat = require(script.Parent.Parent:WaitForChild("Combat"):WaitForChild("Combat"))
local Guardian = require(script.Parent:WaitForChild("Guardian"))
local EggStands = require(script.Parent:WaitForChild("EggStands"))

local folder = workspace:FindFirstChild("Guardians") or Instance.new("Folder")
folder.Name = "Guardians"
folder.Parent = workspace

local guardians = {}

-- Why a guardian can't be spawned, or nil.
local function missingPiece(id, config)
    local stored = ServerStorage:FindFirstChild("Guardians")
    if not (stored and stored:FindFirstChild(id)) then
        return "ServerStorage.Guardians." .. id
    end
    local eggMeshes = ServerStorage:FindFirstChild("EggMeshes")
    for _, eggId in config.Eggs do
        if not (eggMeshes and eggMeshes:FindFirstChild(eggId)) then
            return "ServerStorage.EggMeshes." .. eggId
        end
    end
    return nil
end

for id, config in GameConfig.Guardians do
    local missing = missingPiece(id, config)
    if missing then
        warn("GuardianService: " .. missing .. " isn't stored; the " .. config.DisplayName .. " is skipped")
    else
        table.insert(guardians, Guardian.new(id, config, ServerStorage.Guardians[id], folder))
    end
end

EggStands.load()

-- a stand's egg is taken through its island's guardian (a stand with none standing can't be taken)
EggStands.setTakeHandler(function(player, slot)
    for _, guardian in guardians do
        if guardian.config.Island == slot.island then
            guardian:takeFromStand(player, slot)
            return
        end
    end
end)

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

-- each guardian steps alone: an error in one must not freeze the others (or a carried egg with them)
local failed = {}
RunService.Heartbeat:Connect(function(dt)
    for _, guardian in guardians do
        local ok, err = pcall(guardian.step, guardian, dt)
        if not ok and not failed[guardian] then
            failed[guardian] = true -- once: it would repeat every frame
            warn("Guardian " .. tostring(guardian.id) .. " step failed: " .. tostring(err))
        end
    end
end)
