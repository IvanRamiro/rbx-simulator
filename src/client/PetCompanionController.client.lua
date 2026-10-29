-- Shows every player's equipped pets as small companions that float behind
-- them (including other players' pets). While a player cultivates, their
-- pets slowly circle around them instead.
--
-- Purely visual and only on this client, in a local "PetCompanions" folder.
-- The server says which pets are equipped through the replicated
-- "EquippedPetIds" attribute (e.g. "AquaWisp,VoltFox"); models come from PetModels.
--
-- One per-frame update moves every companion's parts in a single BulkMoveTo.

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local PetModels = require(script.Parent:WaitForChild("PetModels"))

local FOLLOW_SPACING = 2.4 -- Studs between pets side by side
local FOLLOW_DISTANCE = 3 -- Studs behind the player
local FOLLOW_HEIGHT = 0.6 -- Studs above the player's root part
local FOLLOW_SHARPNESS = 6 -- Higher = pets catch up faster
local SNAP_DISTANCE = 40 -- Pets this far away (e.g. after a respawn) jump straight to their spot
local BOB_HEIGHT = 0.25
local BOB_SPEED = 2
local ORBIT_RADIUS = 3.4 -- While cultivating
local ORBIT_HEIGHT = 1.4
local ORBIT_SPEED = 0.6 -- Radians per second

local container = Instance.new("Folder")
container.Name = "PetCompanions"
container.Parent = workspace

-- companions[player] = {
--     key = "AquaWisp,VoltFox", rootPart = the root part the pets follow,
--     pets = { { model, parts = { { Part, Offset } }, cframe } },
-- }
local companions = {}

local function clearPets(entry)
    for _, pet in entry.pets do
        pet.model:Destroy()
    end
    entry.pets = {}
end

-- Rebuilds a player's pets when their equipped pets or character change
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
        local model, parts = PetModels.build(petId)
        if model then
            model.Parent = container
            -- Start at the player; the first frames glide them into place
            table.insert(entry.pets, { model = model, parts = parts, cframe = rootPart.CFrame })
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

            for _, piece in pet.parts do
                table.insert(parts, piece.Part)
                table.insert(cframes, pet.cframe * piece.Offset)
            end
        end
    end

    if #parts > 0 then
        workspace:BulkMoveTo(parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)
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
