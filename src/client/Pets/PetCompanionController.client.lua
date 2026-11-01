local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local PetModels = require(script.Parent:WaitForChild("PetModels"))
local PetRig = require(script.Parent:WaitForChild("PetRig"))
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

local container = Instance.new("Folder")
container.Name = "PetCompanions"
container.Parent = workspace

local companions = {}

local function clearPets(entry)
    for _, pet in entry.pets do
        for _, aura in { pet.aura, pet.fading } do
            if not aura.destroyed then
                AuraBuilder.destroy(aura)
            end
        end
        pet.model:Destroy()
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
            aura.model.Parent = container
            AuraBuilder.show(aura)
            pet.aura = aura
        else
            pet.noAura = true
        end
    elseif not cultivating and pet.aura then
        local aura = pet.aura
        pet.aura = nil
        pet.fading = aura
        AuraBuilder.hide(aura)
        task.delay(AuraBuilder.REMOVE_DELAY, function()
            if pet.fading == aura then
                pet.fading = nil
            end
            if not aura.destroyed then
                AuraBuilder.destroy(aura)
            end
        end)
    end
end

local function syncPets(player, entry)
    local character = player.Character
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    local key = player:GetAttribute("EquippedPetIds")
    key = if typeof(key) == "string" and rootPart then key else ""

    if key == entry.key and rootPart == entry.rootPart then
        return
    end

    clearPets(entry)
    entry.key = key
    entry.rootPart = rootPart
    if key == "" then
        return
    end

    for _, petId in string.split(key, ",") do
        local model, petRoot = PetModels.build(petId)
        if model then
            model.Parent = container
            petRoot.CFrame = rootPart.CFrame
            table.insert(entry.pets, {
                model = model,
                rootPart = petRoot,
                cframe = rootPart.CFrame,
                petId = petId,
                rig = PetModels.getRig(model),
                speed = 0,
            })
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

    for player, entry in companions do
        syncPets(player, entry)

        local rootPart = entry.rootPart
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
        local rank = getRankNumber(player)
        local rankedUp = entry.rank ~= nil and rank ~= nil and rank > entry.rank
        entry.rank = rank
        -- Pets fly with their owner: during (future sword) flight, and whenever the owner has been
        -- off the ground for a moment (a Qinggong leap, a glide or a long fall).
        local ownerHumanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
        local airborne = ownerHumanoid ~= nil and ownerHumanoid.FloorMaterial == Enum.Material.Air
        entry.airborneTime = if airborne then (entry.airborneTime or 0) + deltaTime else 0
        local flying = player:GetAttribute("IsFlying") == true or entry.airborneTime > 0.35
        local cultivating = player:GetAttribute("IsCultivating") == true
        for _, pet in entry.pets do
            local rig = pet.rig
            if not rig then
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
        local cultivating = player:GetAttribute("IsCultivating") == true
        for _, pet in entry.pets do
            syncPetAura(player, pet, cultivating)
            for _, aura in { pet.aura, pet.fading } do
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
