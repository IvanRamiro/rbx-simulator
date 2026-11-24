-- Every RemoteEvent the game uses, by name (EVENT_NAMES). The server creates them in ReplicatedStorage.Remotes;
-- a client waits for each. Add a name here to add a remote.
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
    "GoalEvent",
    "BountyEvent", -- the guardian board (server/Guardians/ConquestService): "Get"; the server answers "State" and tells a "Conquered"
    "TitleEvent",
    "TribulationEvent",
    "PerfEvent",
    "MerchantEvent",
    "PenEvent",
    "SpinEvent",
    "BoostEvent", -- the timed Qi boost: the server tells the buyer ("Bought", minutes) once the purchase is saved
    "AuctionEvent", -- the Auction House (server/Auction/AuctionService): browse, list, bid, cancel, mail
    "FeedbackEvent", -- the Feedback window: the player sends a report, the server answers "Sent" or why not (server/Feedback)
    "FactionEvent", -- the Murim factions: join (the pledge), the trial and the vault; the server answers (server/Factions/FactionService)
    "BetaGiftEvent", -- the beta gift: the player picks their free Exclusive beast, the server answers (server/Rewards/BetaGiftService)
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
