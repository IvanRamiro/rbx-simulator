local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local PetModels = require(script.Parent:WaitForChild("PetModels"))
local PetRig = require(script.Parent:WaitForChild("PetRig"))
local PetPreload = require(script.Parent:WaitForChild("PetPreload"))

-- where each pet walks, in studs from its owner (x to the right, z behind): beside them, never in the line between them and
-- the camera, which sits straight behind them. Pets are about 6 studs long.
-- where each equipped beast walks (studs: X to the owner's right, Y behind them); the last three are the slots pass's (PassRules)
local FOLLOW_SLOTS = { Vector2.new(6.4, 2.4), Vector2.new(-6.4, 2.4), Vector2.new(12.5, 1.2), Vector2.new(-12.5, 1.2), Vector2.new(4.2, 9.5), Vector2.new(-4.2, 9.5) }
local FOLLOW_HEIGHT = 0.9
local FOLLOW_SHARPNESS = 6
local SNAP_DISTANCE = 40
local BOB_HEIGHT = 0.25
local BOB_SPEED = 2
local ORBIT_RADIUS = 6.5
local ORBIT_HEIGHT = 1.6
local ORBIT_SPEED = 0.6
local updateWarned = {} -- [petId] = true once its update has failed and been reported
local NOVA_INTERVAL = 25
local Quality = require(script.Parent.Parent:WaitForChild("Quality"))
local CULL_DISTANCE = if Quality.Low then 80 else 250 -- studs from the camera: other players' pets farther away are hidden and not animated
local RANK_CHECK_INTERVAL = 0.5
-- Another player's pets farther from the camera pose less often: every 2nd frame past LOD_HALF, every 3rd past LOD_THIRD
-- (they still move every frame). A rig's pose costs 20-40 microseconds a frame (measured in Play, 2026-11-12), and a busy hub
-- holds dozens. The player's own pets always pose every frame.
local LOD_HALF = if Quality.Low then 30 else 60
local LOD_THIRD = if Quality.Low then 55 else 140
-- another player's pets play their specials only this near the camera, and never with Reduced Effects on (release audit,
-- 2026-11-12: each makes parts, emitters and a light, every 25 s per pet of everyone cultivating)
local NOVA_REACH = if Quality.Low then 40 else 60

local function novaAllowed(player, pet)
    if player == Players.LocalPlayer then
        return true
    end
    if Players.LocalPlayer:GetAttribute("SettingReducedEffects") == true then
        return false
    end
    local camera = workspace.CurrentCamera
    return camera ~= nil and pet.rootPart ~= nil and (camera.CFrame.Position - pet.rootPart.Position).Magnitude <= NOVA_REACH
end

local container = Instance.new("Folder")
container.Name = "PetCompanions"
container.Parent = workspace

local companions = {}

local function destroyPet(pet)
    pet.model:Destroy()
end

local function clearPets(entry)
    for _, pet in entry.pets do
        destroyPet(pet)
    end
    entry.pets = {}
end

local function getRankNumber(player)
    return Ranks.getIndex(Ranks.getPlayerRankName(player))
end

-- `hidden`: its owner is culled (far away), so it waits out of the world like their other pets. `key` is "PetId:Size".
local function buildPet(key, rootPart, hidden)
    local petId, size = string.match(key, "^([^:]+):?(.*)$")
    local model, petRoot = PetModels.build(petId, size)
    if not model then
        return nil
    end
    -- every piece moved, before parenting: a hidden pet waits out of the world, where pieces welded to its root
    -- wouldn't follow the root alone (they'd show offset once its owner came near)
    model:PivotTo(rootPart.CFrame)
    model.Parent = if hidden then nil else container
    return {
        model = model,
        rootPart = petRoot,
        cframe = rootPart.CFrame,
        petId = petId,
        key = key,
        scale = model:GetAttribute("SizeScale") or 1, -- its hatch size: where it walks and how high it rides scale with it
        rig = PetModels.getRig(model),
        speed = 0,
    }
end

-- Keeps a player's pets matching their EquippedPets ("PetId:Size", ...): pets still equipped stay where they are,
-- new ones appear at the player's side, unequipped ones go. A new character starts them all again.
local function syncPets(player, entry)
    local character = player.Character
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    local equipped = player:GetAttribute("EquippedPets")
    equipped = if typeof(equipped) == "string" and rootPart then equipped else ""
    if equipped == entry.equipped and entry.settled and rootPart == entry.rootPart then
        return
    end
    entry.equipped = equipped

    -- a pet joins once its meshes have arrived, so it appears whole (PetPreload)
    local shown = {}
    entry.settled = true
    for _, key in string.split(equipped, ",") do
        local petId = string.match(key, "^[^:]+")
        if petId then
            if PetPreload.isReady(petId) then
                table.insert(shown, key)
            else
                PetPreload.want(petId)
                entry.settled = false
            end
        end
    end
    local key = table.concat(shown, ",")

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
        spare[pet.key] = spare[pet.key] or {}
        table.insert(spare[pet.key], pet)
    end
    entry.pets = {}
    if key ~= "" then
        for _, petKey in string.split(key, ",") do
            local pet = spare[petKey] and table.remove(spare[petKey]) or buildPet(petKey, rootPart, entry.culled)
            if pet then
                if pet.rig then
                    pet.rig.owner = player -- (a special can show its owner: the Obsidian Guardian's)
                elseif Quality.Low and player ~= Players.LocalPlayer then
                    -- an unrigged pet's light (PetRig's sweep covers rigged ones): another player's pet on a phone gives it up
                    for _, d in pet.model:GetDescendants() do
                        if d:IsA("PointLight") then
                            d.Enabled = false
                        end
                    end
                end
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

-- Hides or shows a player's pets.
local function setCulled(entry, culled)
    entry.culled = culled
    local parent = if culled then nil else container
    for _, pet in entry.pets do
        pet.model.Parent = parent
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

-- the height of the owner's root above their feet (a pet's place above the ground scales with its size from there)
local function hipOf(player)
    local humanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
    local rootPart = humanoid and humanoid.RootPart
    return if rootPart then humanoid.HipHeight + rootPart.Size.Y / 2 else 3
end

-- Each pet's place beside its owner, with its size (pets[i].scale): a pet rides at its size times the height a Normal one rides above
-- the ground (so a Giant's feet still reach it and a Small's do too), and walks its size times as far out (never nearer than a Normal
-- one). A pet farther out on the same side keeps clear of a big one nearer in.
local function followOffsets(pets, hip)
    local offsets = {}
    for index, pet in pets do
        local slot = FOLLOW_SLOTS[index] or FOLLOW_SLOTS[#FOLLOW_SLOTS]
        local f = pet.scale or 1
        local out = math.max(f, 1)
        local x = slot.X * out
        -- slots 3 and 4 walk outside 1 and 2, on the same side: past where that one walks, by their own share of the gap
        local inner = (index == 3 or index == 4) and offsets[index - 2]
        if inner then
            x = inner.x + (slot.X - FOLLOW_SLOTS[index - 2].X) * out
        end
        offsets[index] = { x = x, z = slot.Y * out, y = (hip + FOLLOW_HEIGHT) * f - hip, scale = f }
    end
    return offsets
end

local function getTargetCFrame(player, rootPart, index, count, now, offset, hip)
    local f = offset.scale
    local bob = math.sin(now * BOB_SPEED + index * 1.7) * BOB_HEIGHT * f

    if player:GetAttribute("IsCultivating") == true then
        local angle = now * ORBIT_SPEED + (index - 1) / count * 2 * math.pi
        local center = rootPart.Position + Vector3.new(0, (hip + ORBIT_HEIGHT) * f - hip + bob, 0)
        local position = center + Vector3.new(math.cos(angle), 0, math.sin(angle)) * ORBIT_RADIUS * math.max(f, 1)
        local heading = Vector3.new(-math.sin(angle), 0, math.cos(angle))
        return CFrame.lookAt(position, position + heading)
    end

    return levelFacing(rootPart) * CFrame.new(offset.x, offset.y + bob, offset.z)
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
        -- the player's own pets step out of the hatch cinematic's shot (a Giant beside them filled it: HatchCeremony sets this)
        far = far or (player == Players.LocalPlayer and player:GetAttribute("InHatchCinematic") == true)
        if far ~= (entry.culled == true) then
            setCulled(entry, far)
        end
        local every = 1
        if player ~= Players.LocalPlayer and rootPart and eye then
            local distance = (rootPart.Position - eye).Magnitude
            every = if distance > LOD_THIRD then 3 elseif distance > LOD_HALF then 2 else 1
        end
        entry.every = every
        if far then
            continue
        end

        local hip = hipOf(player)
        local offsets = followOffsets(entry.pets, hip)
        for index, pet in entry.pets do
            local target = getTargetCFrame(player, rootPart, index, #entry.pets, now, offsets[index], hip)
            local previous = pet.cframe.Position
            if (pet.cframe.Position - target.Position).Magnitude > SNAP_DISTANCE * math.max(pet.scale, 1) then
                pet.cframe = target
            else
                pet.cframe = pet.cframe:Lerp(target, blend)
            end
            -- ground travel only: the idle bob is up and down, and counting it kept a still pet from ever settling (its naps never came)
            local step = pet.cframe.Position - previous
            local moved = Vector2.new(step.X, step.Z).Magnitude / math.max(deltaTime, 1e-3)
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
            if not rig then
                continue
            end
            if cultivating then
                pet.nextNova = pet.nextNova or now + 6
                if now >= pet.nextNova then
                    pet.nextNova = now + NOVA_INTERVAL
                    if novaAllowed(player, pet) then
                        PetRig.nova(rig)
                    end
                end
            else
                pet.nextNova = nil
            end
            if rankedUp and novaAllowed(player, pet) then
                PetRig.nova(rig)
            end
            -- posed every entry.every frames, with the time since its last pose (each pet on its own beat, so a crowd's
            -- poses spread over the frames)
            pet.poseTime = (pet.poseTime or 0) + deltaTime
            pet.beat = ((pet.beat or math.random(0, 5)) + 1) % 6
            if pet.beat % (entry.every or 1) ~= 0 then
                continue
            end
            local poseTime = pet.poseTime
            pet.poseTime = 0
            -- (guarded: one rig that throws must not stop every pet after it this frame, release audit 2026-11-12)
            local ok, err = pcall(PetRig.update, rig, poseTime, { speed = pet.speed, flying = flying })
            if not ok and not updateWarned[rig.petId] then
                updateWarned[rig.petId] = true
                warn("PetCompanionController: " .. tostring(rig.petId) .. " failed to update: " .. tostring(err))
            end
        end
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
