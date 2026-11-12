local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local REMOTES_FOLDER_NAME = "Remotes"

local EVENT_NAMES = {
    "CultivationEvent",
    "RankUpEvent",
    "EquipPetEvent",
    "UnequipPetEvent",
    "PetInventoryUpdatedEvent",
    "TogglePetLockEvent",
    "FusePetEvent",
    "PetActionResultEvent",
    "CodexEvent",
    "EggHatchResultEvent",
    "RelicResultEvent",
    "QinggongFxEvent",
    "OutfitEvent",
    "FlightEvent",
    "CombatEvent",
    "WeaponDrawEvent",
    "GuardianEvent",
    "ShopEvent",
    "HatchEggEvent",
    "QuestEvent",
    "SettingsEvent",
    "RewardEvent",
    "TitleEvent",
    "TribulationEvent",
    "PerfEvent",
    "MerchantEvent",
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
