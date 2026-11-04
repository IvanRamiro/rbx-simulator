local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local PetModels = require(script.Parent:WaitForChild("PetModels"))
local PetRig = require(script.Parent:WaitForChild("PetRig"))
local PetPreload = require(script.Parent:WaitForChild("PetPreload"))
local AuraBuilder = require(script.Parent.Parent:WaitForChild("Auras"):WaitForChild("AuraBuilder"))

local FOLLOW_SPACING = 4.8
local FOLLOW_DISTANCE = 5.5
local FOLLOW_HEIGHT = 0.9
local FOLLOW_SHARPNESS = 6
local SNAP_DISTANCE = 40
local BOB_HEIGHT = 0.25
local BOB_SPEED = 2
local ORBIT_RADIUS = 6.5
local ORBIT_HEIGHT = 1.6
local ORBIT_SPEED = 0.6
local NOVA_INTERVAL = 25
local CULL_DISTANCE = if require(script.Parent.Parent:WaitForChild("Quality")).Low then 80 else 250 -- studs from the camera: other players' pets farther away are hidden and not animated
local RANK_CHECK_INTERVAL = 0.5

local container = Instance.new("Folder")
container.Name = "PetCompanions"
container.Parent = workspace

local companions = {}

local function destroyAura(aura)
    if not aura.destroyed then
        AuraBuilder.destroy(aura)
    end
end

local function destroyPet(pet)
    if pet.aura then
        destroyAura(pet.aura)
    end
    for _, aura in pet.fading do
        destroyAura(aura)
    end
    pet.model:Destroy()
end

local function clearPets(entry)
    for _, pet in entry.pets do
        destroyPet(pet)
    end
    entry.pets = {}
end

local function getRankId(player)
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    return rank and rank.Id
end

local function getRankNumber(player)
    return Ranks.getIndex(Ranks.getPlayerRankName(player))
end

local function syncPetAura(player, pet, cultivating)
    if cultivating and not pet.aura and not pet.noAura then
        local aura = AuraBuilder.build(player, pet.model, pet.rootPart, pet.petId, getRankId(player))
        if aura then
            aura.model.Parent = if pet.model.Parent then container else nil
            AuraBuilder.show(aura)
            pet.aura = aura
        else
            pet.noAura = true
        end
    elseif not cultivating and pet.aura then
        local aura = pet.aura
        pet.aura = nil
        table.insert(pet.fading, aura)
        AuraBuilder.hide(aura)
        task.delay(AuraBuilder.REMOVE_DELAY, function()
            local index = table.find(pet.fading, aura)
            if index then
                table.remove(pet.fading, index)
            end
            destroyAura(aura)
        end)
    end
end

-- `hidden`: its owner is culled (far away), so it waits out of the world like their other pets.
-- It stays out of the world until its meshes have arrived, so it appears whole (PetPreload).
local function buildPet(petId, rootPart, entry)
    local model, petRoot = PetModels.build(petId)
    if not model then
        return nil
    end
    petRoot.CFrame = rootPart.CFrame
    local pet = {
        model = model,
        rootPart = petRoot,
        cframe = rootPart.CFrame,
        petId = petId,
        rig = PetModels.getRig(model),
        speed = 0,
        fading = {},
        loading = true,
    }
    PetPreload.whenReady(petId, function()
        -- deferred: an already-fetched pet answers at once, before syncPets has listed it
        task.defer(function()
            pet.loading = false
            if table.find(entry.pets, pet) and not entry.culled then
                model.Parent = container
            end
        end)
    end)
    return pet
end

-- Keeps a player's pets matching their EquippedPetIds: pets still equipped stay where they are,
-- new ones appear at the player's side, unequipped ones go. A new character starts them all again.
local function syncPets(player, entry)
    local character = player.Character
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    local key = player:GetAttribute("EquippedPetIds")
    key = if typeof(key) == "string" and rootPart then key else ""

    if key == entry.key and rootPart == entry.rootPart then
        return
    end
    if rootPart ~= entry.rootPart then
        clearPets(entry)
    end
    entry.key = key
    entry.rootPart = rootPart

    local spare = {}
    for _, pet in entry.pets do
        spare[pet.petId] = spare[pet.petId] or {}
        table.insert(spare[pet.petId], pet)
    end
    entry.pets = {}
    if key ~= "" then
        for _, petId in string.split(key, ",") do
            local pet = spare[petId] and table.remove(spare[petId]) or buildPet(petId, rootPart, entry)
            if pet then
                table.insert(entry.pets, pet)
            end
        end
    end
    for _, pets in spare do
        for _, pet in pets do
            destroyPet(pet)
        end
    end
end

-- Hides or shows a player's pets and their auras.
local function setCulled(entry, culled)
    entry.culled = culled
    local parent = if culled then nil else container
    for _, pet in entry.pets do
        pet.model.Parent = if pet.loading then nil else parent
        if pet.aura then
            pet.aura.model.Parent = parent
        end
        for _, aura in pet.fading do
            aura.model.Parent = parent
        end
    end
end

local function levelFacing(rootPart)
    local look = rootPart.CFrame.LookVector
    local flatLook = Vector3.new(look.X, 0, look.Z)
    if flatLook.Magnitude < 0.01 then
        flatLook = Vector3.new(0, 0, -1)
    end
    local position = rootPart.Position
    return CFrame.lookAt(position, position + flatLook.Unit)
end

local function getTargetCFrame(player, rootPart, index, count, now)
    local bob = math.sin(now * BOB_SPEED + index * 1.7) * BOB_HEIGHT

    if player:GetAttribute("IsCultivating") == true then
        local angle = now * ORBIT_SPEED + (index - 1) / count * 2 * math.pi
        local center = rootPart.Position + Vector3.new(0, ORBIT_HEIGHT + bob, 0)
        local position = center + Vector3.new(math.cos(angle), 0, math.sin(angle)) * ORBIT_RADIUS
        local heading = Vector3.new(-math.sin(angle), 0, math.cos(angle))
        return CFrame.lookAt(position, position + heading)
    end

    local side = index - (count + 1) / 2
    local offset = Vector3.new(side * FOLLOW_SPACING, FOLLOW_HEIGHT + bob, FOLLOW_DISTANCE + math.abs(side) * 0.6)
    return levelFacing(rootPart) * CFrame.new(offset)
end

local function updateCompanions(deltaTime)
    local now = os.clock()
    local blend = 1 - math.exp(-FOLLOW_SHARPNESS * deltaTime)
    local parts, cframes = {}, {}
    local camera = workspace.CurrentCamera
    local eye = camera and camera.CFrame.Position

    for player, entry in companions do
        syncPets(player, entry)
        local rootPart = entry.rootPart
        local far = rootPart ~= nil and eye ~= nil and player ~= Players.LocalPlayer
            and (rootPart.Position - eye).Magnitude > CULL_DISTANCE
        if far ~= (entry.culled == true) then
            setCulled(entry, far)
        end
        if far then
            continue
        end

        for index, pet in entry.pets do
            local target = getTargetCFrame(player, rootPart, index, #entry.pets, now)
            local previous = pet.cframe.Position
            if (pet.cframe.Position - target.Position).Magnitude > SNAP_DISTANCE then
                pet.cframe = target
            else
                pet.cframe = pet.cframe:Lerp(target, blend)
            end
            local moved = (pet.cframe.Position - previous).Magnitude / math.max(deltaTime, 1e-3)
            pet.speed += (math.min(moved, 60) - pet.speed) * math.min(1, deltaTime * 8)

            table.insert(parts, pet.rootPart)
            table.insert(cframes, pet.cframe)
        end
    end

    if #parts > 0 then
        workspace:BulkMoveTo(parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)
    end

    for player, entry in companions do
        if entry.culled then
            continue
        end
        local rankedUp = false
        if now >= (entry.rankCheck or 0) then
            entry.rankCheck = now + RANK_CHECK_INTERVAL
            local rank = getRankNumber(player)
            rankedUp = entry.rank ~= nil and rank ~= nil and rank > entry.rank
            entry.rank = rank
        end
        -- Pets fly with their owner: during sword flight, and whenever the owner has been off the
        -- ground for a moment (a Qinggong leap, a glide or a long fall).
        local ownerHumanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
        local airborne = ownerHumanoid ~= nil and ownerHumanoid.FloorMaterial == Enum.Material.Air
        entry.airborneTime = if airborne then (entry.airborneTime or 0) + deltaTime else 0
        local flying = player:GetAttribute("IsFlying") == true or entry.airborneTime > 0.35
        local cultivating = player:GetAttribute("IsCultivating") == true
        for _, pet in entry.pets do
            local rig = pet.rig
            if not rig or pet.loading then
                continue
            end
            if cultivating then
                pet.nextNova = pet.nextNova or now + 6
                if now >= pet.nextNova then
                    pet.nextNova = now + NOVA_INTERVAL
                    PetRig.nova(rig)
                end
            else
                pet.nextNova = nil
            end
            if rankedUp then
                PetRig.nova(rig)
            end
            PetRig.update(rig, deltaTime, { speed = pet.speed, flying = flying })
        end
    end

    local auraParts, auraCFrames = {}, {}
    for player, entry in companions do
        if entry.culled then
            continue
        end
        local cultivating = player:GetAttribute("IsCultivating") == true
        for _, pet in entry.pets do
            if pet.loading then
                continue
            end
            syncPetAura(player, pet, cultivating)
            if pet.aura then
                AuraBuilder.update(pet.aura, now, auraParts, auraCFrames)
            end
            for _, aura in pet.fading do
                AuraBuilder.update(aura, now, auraParts, auraCFrames)
            end
        end
    end
    if #auraParts > 0 then
        workspace:BulkMoveTo(auraParts, auraCFrames, Enum.BulkMoveMode.FireCFrameChanged)
    end
end

local function watchPlayer(player)
    companions[player] = { key = "", rootPart = nil, pets = {} }
end

local function unwatchPlayer(player)
    local entry = companions[player]
    if entry then
        clearPets(entry)
        companions[player] = nil
    end
end

Players.PlayerAdded:Connect(watchPlayer)
Players.PlayerRemoving:Connect(unwatchPlayer)

for _, player in Players:GetPlayers() do
    watchPlayer(player)
end

RunService.RenderStepped:Connect(updateCompanions)
