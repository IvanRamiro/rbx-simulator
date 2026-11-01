-- Outfits worn over a player's avatar (GameConfig.Outfits), by OwnerUserIds or, once GamePassId is
-- set, by owners of that game pass. Pieces (ServerStorage.Outfits.<OutfitId>, stored by
-- WorldBuild.OutfitBuilder) are welded to body parts; clashing accessories are hidden while worn.
-- The choice is saved in PlayerData as OutfitId.
--
-- The worn model lives in Workspace.WornOutfits, not in the character: the character's Animator
-- resets every Bone's Transform inside it each frame (measured in Play), undoing the robes' sway.
-- Its "Character" ObjectValue points the client at its wearer.
--
-- Remote: OutfitEvent (client -> server) with an outfit id to wear it, or "" to take it off.
-- Player attributes: OutfitId (the outfit worn), OwnedOutfits (comma-separated, for the HUD).
local CollectionService = game:GetService("CollectionService")
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))

local OUTFIT_TAG = "WornOutfit"
local REQUEST_COOLDOWN = 1
-- accessory types the robes cover or clash with; hair, hats and faces stay
local HIDDEN_TYPES = {
    [Enum.AccessoryType.Back] = true, [Enum.AccessoryType.Waist] = true, [Enum.AccessoryType.Shoulder] = true,
    [Enum.AccessoryType.Front] = true, [Enum.AccessoryType.Jacket] = true, [Enum.AccessoryType.Sweater] = true,
    [Enum.AccessoryType.Shirt] = true, [Enum.AccessoryType.TShirt] = true, [Enum.AccessoryType.Pants] = true,
    [Enum.AccessoryType.Shorts] = true, [Enum.AccessoryType.DressSkirt] = true,
    [Enum.AccessoryType.LeftShoe] = true, [Enum.AccessoryType.RightShoe] = true,
}

local lastRequest = {}
local ownership = {}

local function ownsOutfit(player, outfitId)
    local config = GameConfig.Outfits[outfitId]
    if not config then
        return false
    end
    if table.find(config.OwnerUserIds or {}, player.UserId) then
        return true
    end
    if (config.GamePassId or 0) > 0 then
        local ok, owns = pcall(MarketplaceService.UserOwnsGamePassAsync, MarketplaceService, player.UserId, config.GamePassId)
        return ok and owns
    end
    return false
end

local function hideAccessory(accessory)
    local handle = accessory:FindFirstChild("Handle")
    if accessory:IsA("Accessory") and HIDDEN_TYPES[accessory.AccessoryType] and handle and handle:IsA("BasePart")
        and handle:GetAttribute("OutfitHiddenTransparency") == nil then
        handle:SetAttribute("OutfitHiddenTransparency", handle.Transparency)
        handle.Transparency = 1
    end
end

local wornFolder = workspace:FindFirstChild("WornOutfits") or Instance.new("Folder")
wornFolder.Name = "WornOutfits"
wornFolder.Parent = workspace
local wornBy = {}

local function takeOff(character)
    local worn = wornBy[character]
    wornBy[character] = nil
    if worn then
        worn:Destroy()
    end
    for _, accessory in character:GetChildren() do
        local handle = accessory:IsA("Accessory") and accessory:FindFirstChild("Handle")
        if handle and handle:GetAttribute("OutfitHiddenTransparency") ~= nil then
            handle.Transparency = handle:GetAttribute("OutfitHiddenTransparency")
            handle:SetAttribute("OutfitHiddenTransparency", nil)
        end
    end
end

local function dress(character, outfitId)
    takeOff(character)
    local source = ServerStorage:FindFirstChild("Outfits") and ServerStorage.Outfits:FindFirstChild(outfitId)
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    if not source or not humanoid or humanoid.RigType ~= Enum.HumanoidRigType.R15 then
        return
    end
    local worn = Instance.new("Model")
    worn.Name = character.Name .. "_Outfit"
    worn:SetAttribute("OutfitId", outfitId)
    local link = Instance.new("ObjectValue")
    link.Name = "Character"
    link.Value = character
    link.Parent = worn
    for _, piece in source:GetChildren() do
        local bodyPart = character:FindFirstChild(piece:GetAttribute("BodyPart"))
        local offset = piece:GetAttribute("Offset")
        if bodyPart and bodyPart:IsA("BasePart") and typeof(offset) == "CFrame" then
            local part = piece:Clone()
            part.Anchored = false
            part.CFrame = bodyPart.CFrame * offset
            local weld = Instance.new("Weld")
            weld.Part0, weld.Part1, weld.C0 = bodyPart, part, offset
            weld.Parent = part
            part.Parent = worn
        end
    end
    worn.Parent = wornFolder
    wornBy[character] = worn
    character.Destroying:Once(function()
        if wornBy[character] == worn then
            takeOff(character)
        end
    end)
    CollectionService:AddTag(worn, OUTFIT_TAG)
    for _, accessory in character:GetChildren() do
        hideAccessory(accessory)
    end
end

local function applyToCharacter(player, character)
    local outfitId = player:GetAttribute("OutfitId")
    if outfitId and outfitId ~= "" then
        dress(character, outfitId)
    else
        takeOff(character)
    end
end

local function onCharacterAdded(player, character)
    -- hide accessories that load after the robes
    character.ChildAdded:Connect(function(child)
        if child:IsA("Accessory") and wornBy[character] then
            task.defer(hideAccessory, child)
        end
    end)
    if not player:HasAppearanceLoaded() then
        player.CharacterAppearanceLoaded:Wait()
    end
    if player.Character == character then
        applyToCharacter(player, character)
    end
end

local function onPlayerAdded(player)
    ownership[player] = {}
    player.CharacterAdded:Connect(function(character)
        onCharacterAdded(player, character)
    end)
    -- the old character isn't always destroyed on respawn: its robes would stay behind and fall
    player.CharacterRemoving:Connect(takeOff)
    if player.Character then
        task.spawn(onCharacterAdded, player, player.Character)
    end

    local owned = {}
    for outfitId in GameConfig.Outfits do
        if ownsOutfit(player, outfitId) then
            ownership[player][outfitId] = true
            table.insert(owned, outfitId)
        end
    end
    table.sort(owned)
    player:SetAttribute("OwnedOutfits", table.concat(owned, ","))

    local progress = PlayerData.waitForData(player)
    if progress and progress.OutfitId and ownership[player] and ownership[player][progress.OutfitId] then
        player:SetAttribute("OutfitId", progress.OutfitId)
        if player.Character then
            applyToCharacter(player, player.Character)
        end
    end
end

RemoteEvents.OutfitEvent.OnServerEvent:Connect(function(player, outfitId)
    if typeof(outfitId) ~= "string" or #outfitId > 32 then
        return
    end
    local now = os.clock()
    if lastRequest[player] and now - lastRequest[player] < REQUEST_COOLDOWN then
        return
    end
    lastRequest[player] = now
    if outfitId ~= "" and not (ownership[player] and ownership[player][outfitId]) then
        return
    end
    player:SetAttribute("OutfitId", if outfitId == "" then nil else outfitId)
    if player.Character then
        applyToCharacter(player, player.Character)
    end
    PlayerData.saveSoon(player)
end)

Players.PlayerAdded:Connect(onPlayerAdded)
Players.PlayerRemoving:Connect(function(player)
    lastRequest[player] = nil
    ownership[player] = nil
    if player.Character then
        takeOff(player.Character)
    end
end)
for _, player in Players:GetPlayers() do
    task.spawn(onPlayerAdded, player)
end
