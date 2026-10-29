
-- Returns the RemoteEvent players use to request a training action.
-- The RemoteEvent lives in ReplicatedStorage.Remotes so its name can't collide
-- with this ModuleScript (which is also called "TrainingEvent").
-- Only the server creates it; clients wait for the replicated copy.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local REMOTES_FOLDER_NAME = "Remotes"
local EVENT_NAME = "TrainingEvent"

if RunService:IsServer() then
    local remotes = ReplicatedStorage:FindFirstChild(REMOTES_FOLDER_NAME)
    if not remotes then
        remotes = Instance.new("Folder")
        remotes.Name = REMOTES_FOLDER_NAME
        remotes.Parent = ReplicatedStorage
    end

    local trainingEvent = remotes:FindFirstChild(EVENT_NAME)
    if not trainingEvent then
        trainingEvent = Instance.new("RemoteEvent")
        trainingEvent.Name = EVENT_NAME
        trainingEvent.Parent = remotes
    end

    return trainingEvent
end

return ReplicatedStorage:WaitForChild(REMOTES_FOLDER_NAME):WaitForChild(EVENT_NAME)
