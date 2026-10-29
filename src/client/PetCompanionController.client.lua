-- Shows every player's equipped pets as small companions that float behind
-- them (including other players' pets). While a player cultivates, their
-- pets slowly circle around them instead.
--
-- Purely visual and only on this client, in a local "PetCompanions" folder.
-- The server says which pets are equipped through the replicated
-- "EquippedPetIds" attribute (e.g. "AquaWisp,VoltFox"); models come from PetModels.
--
-- Each pet is welded to an invisible root part, so one per-frame update moves
-- every companion by moving just their roots, in a single BulkMoveTo.
--
-- While a player cultivates, each of their pets also shows the aura of its
-- own element (AuraBuilder), if that element's aura has been made.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local PetModels = require(script.Parent:WaitForChild("PetModels"))
local AuraBuilder = require(script.Parent:WaitForChild("AuraBuilder"))

local FOLLOW_SPACING = 4.8 -- Studs between pets side by side
local FOLLOW_DISTANCE = 5.5 -- Studs behind the player
local FOLLOW_HEIGHT = 0.9 -- Studs above the player's root part
local FOLLOW_SHARPNESS = 6 -- Higher = pets catch up faster
local SNAP_DISTANCE = 40 -- Pets this far away (e.g. after a respawn) jump straight to their spot
local BOB_HEIGHT = 0.25
local BOB_SPEED = 2
local ORBIT_RADIUS = 6.5 -- While cultivating
local ORBIT_HEIGHT = 1.6
local ORBIT_SPEED = 0.6 -- Radians per second

local container = Instance.new("Folder")
container.Name = "PetCompanions"
container.Parent = workspace

-- companions[player] = {
--     key = "AquaWisp,VoltFox", rootPart = the root part the pets follow,
--     version = PetModels.Version the pets were built with,
--     pets = { { model, rootPart, cframe, petId, aura } },
-- }
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
    local leaderstats = player:FindFirstChild("leaderstats")
    local rankValue = leaderstats and leaderstats:FindFirstChild("Rank")
    local rank = rankValue and Ranks.getRank(rankValue.Value)
    return rank and rank.Id
end

-- Gives the pet its element's aura while its owner cultivates, and fades it
-- away afterwards. Elements without an aura yet are skipped.
local function syncPetAura(player, pet, cultivating)
    if cultivating and not pet.aura and not pet.noAura then
        local aura = AuraBuilder.build(player, pet.model, pet.rootPart, pet.petId, getRankId(player), true)
        if aura then
            aura.model.Parent = container
            AuraBuilder.show(aura)
            pet.aura = aura
        else
            pet.noAura = true -- Nothing to show for this element; don't try every frame
        end
    elseif not cultivating and pet.aura then
        -- Keeps following the pet while it fades, then goes
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

-- Rebuilds a player's pets when their equipped pets or character change
local function syncPets(player, entry)
    local character = player.Character
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    local key = player:GetAttribute("EquippedPetIds")
    key = if typeof(key) == "string" and rootPart then key else ""

    -- Also rebuild when a pet's Blender mesh finishes loading (PetModels.Version)
    if key == entry.key and rootPart == entry.rootPart and entry.version == PetModels.Version then
        return
    end

    clearPets(entry)
    entry.key = key
    entry.rootPart = rootPart
    entry.version = PetModels.Version
    if key == "" then
        return
    end

    for _, petId in string.split(key, ",") do
        local model, petRoot = PetModels.build(petId)
        if model then
            -- Parent first: the welds lock in each piece's offset from the root
            -- when they activate, so the root may only move after that
            model.Parent = container
            -- Start at the player; the first frames glide them into place
            petRoot.CFrame = rootPart.CFrame
            table.insert(entry.pets, { model = model, rootPart = petRoot, cframe = rootPart.CFrame, petId = petId })
        end
    end
end

-- The player's facing direction, kept level so pets don't tilt with the body
local function levelFacing(rootPart)
    local look = rootPart.CFrame.LookVector
    local flatLook = Vector3.new(look.X, 0, look.Z)
    if flatLook.Magnitude < 0.01 then
        flatLook = Vector3.new(0, 0, -1)
    end
    local position = rootPart.Position
    return CFrame.lookAt(position, position + flatLook.Unit)
end

-- Where pet number `index` of `count` should be right now
local function getTargetCFrame(player, rootPart, index, count, now)
    local bob = math.sin(now * BOB_SPEED + index * 1.7) * BOB_HEIGHT

    if player:GetAttribute("IsCultivating") == true then
        -- Spread evenly around a slow circle, facing the way they travel
        local angle = now * ORBIT_SPEED + (index - 1) / count * 2 * math.pi
        local center = rootPart.Position + Vector3.new(0, ORBIT_HEIGHT + bob, 0)
        local position = center + Vector3.new(math.cos(angle), 0, math.sin(angle)) * ORBIT_RADIUS
        local heading = Vector3.new(-math.sin(angle), 0, math.cos(angle))
        return CFrame.lookAt(position, position + heading)
    end

    -- A row behind the player, the outer pets a little further back
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
            if (pet.cframe.Position - target.Position).Magnitude > SNAP_DISTANCE then
                pet.cframe = target
            else
                pet.cframe = pet.cframe:Lerp(target, blend)
            end

            table.insert(parts, pet.rootPart)
            table.insert(cframes, pet.cframe)
        end
    end

    if #parts > 0 then
        workspace:BulkMoveTo(parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)
    end

    -- Pet auras, placed around the pets' new positions
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
    companions[player] = { key = "", rootPart = nil, version = 0, pets = {} }
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
