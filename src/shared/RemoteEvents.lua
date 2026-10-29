
-- Returns every RemoteEvent the game uses, e.g. RemoteEvents.CultivationEvent.
-- They live in ReplicatedStorage.Remotes so their names can't collide with
-- ModuleScripts in ReplicatedStorage.
-- Only the server creates them; clients wait for the replicated copies.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local REMOTES_FOLDER_NAME = "Remotes"

-- To add a new RemoteEvent, add its name here
local EVENT_NAMES = {
    "CultivationEvent", -- Client sends true to start cultivating, false to stop
    "RankUpEvent",
    "FlightEvent", -- Client sends true to take off, false to land
    "EquipPetEvent",
    "UnequipPetEvent",
    "SetAuraPetEvent",
    "PetInventoryUpdatedEvent", -- Server to client only
    "EggHatchResultEvent", -- Server to client only
}

local RemoteEvents = {}

if RunService:IsServer() then
    local remotes = ReplicatedStorage:FindFirstChild(REMOTES_FOLDER_NAME)
    if not remotes then
        remotes = Instance.new("Folder")
        remotes.Name = REMOTES_FOLDER_NAME
        remotes.Parent = ReplicatedStorage
    end

    for _, eventName in EVENT_NAMES do
        local event = remotes:FindFirstChild(eventName)
        if not event then
            event = Instance.new("RemoteEvent")
            event.Name = eventName
            event.Parent = remotes
        end

        RemoteEvents[eventName] = event
    end
else
    local remotes = ReplicatedStorage:WaitForChild(REMOTES_FOLDER_NAME)

    for _, eventName in EVENT_NAMES do
        RemoteEvents[eventName] = remotes:WaitForChild(eventName)
    end
end

return RemoteEvents
