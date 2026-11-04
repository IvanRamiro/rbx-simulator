-- The egg stands behind each island's guardian: the eggs players carry off (Guardian.lua) and hatch
-- at Yggdrasil's Hatching Altar (PetService). A stand holds one egg, shown with its glow ring and its
-- light; each client adds its Highlight and bloom (src/client/World/EggGlow.client.lua):
--   * taking it empties the stand (EggStands.take);
--   * a dropped egg that times out, or a theft that fails, puts it back (EggStands.restore);
--   * a secured one leaves the stand empty for GameConfig.EggTheft.RespawnTime seconds, then the
--     island's lowest-rank egg appears there unless another stand shows it, else a random one of
--     its eggs (EggStands.respawn).
-- Stands are found in Workspace.FloatingIslands.<Island>.EggStands (WorldBuilder.buildEggStands):
-- a Model per stand (named after the egg it was built with: its slot's name, which stays) with a
-- Pedestal, a GlowRing, the egg's body "Egg" and its "<EggId>_Glow_<hex>" pieces, and the EggRest
-- attribute (the egg's resting point, facing the stand's front).
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local EggModel = require(script.Parent:WaitForChild("EggModel"))
local WorldConfig = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("WorldConfig"))

local EggStands = {}

local TAKE_DISTANCE = 12

local slotsOf = {}       -- [island] = { [slot] = true }
local looks = {}         -- [eggId] = { ring = Color3, extras = { Light templates } }
local onTake             -- function(player, slot), set by GuardianService

-- The egg's pieces on a stand: everything but the stand's own pedestal and ring.
local function eggParts(stand)
    local parts = {}
    for _, child in stand:GetChildren() do
        if child:IsA("BasePart") and child.Name ~= "Pedestal" and child.Name ~= "GlowRing" then
            table.insert(parts, child)
        end
    end
    return parts
end

local function setPrompt(slot)
    local prompt = slot.prompt
    if not prompt then
        return
    end
    prompt.Enabled = slot.eggId ~= nil
    prompt.ActionText = "Take"
    prompt.ObjectText = slot.eggId and GameConfig.Eggs[slot.eggId].DisplayName or ""
end

-- The egg's look as built on its first stand: its ring colour and its light.
local function learnLook(slot)
    local eggId = slot.eggId
    if looks[eggId] then
        return
    end
    local look = { extras = {} }
    local ring = slot.stand:FindFirstChild("GlowRing")
    look.ring = ring and ring.Color
    local body = slot.stand:FindFirstChild("Egg")
    for _, child in body and body:GetChildren() or {} do
        if child:IsA("Light") then
            table.insert(look.extras, child:Clone())
        end
    end
    looks[eggId] = look
end

-- Shows `eggId` on the slot's stand (it holds none).
local function show(slot, eggId)
    local look = looks[eggId]
    local source = ServerStorage:FindFirstChild("EggMeshes") and ServerStorage.EggMeshes:FindFirstChild(eggId)
    assert(look and source, "no look for egg " .. eggId)
    local _, box = source:GetBoundingBox()
    local height = box.Y * GameConfig.EggStudsPerUnit
    local model = EggModel.build(eggId, height)
    model:PivotTo(CFrame.new(slot.rest.Position + Vector3.new(0, height / 2, 0)) * slot.rest.Rotation)
    model.PrimaryPart.Anchored = true
    for _, extra in look.extras do
        extra:Clone().Parent = model.PrimaryPart
    end
    for _, part in model:GetChildren() do
        part.Parent = slot.stand
    end
    model:Destroy()
    local ring = slot.stand:FindFirstChild("GlowRing")
    if ring and look.ring then
        ring.Color = look.ring
    end
    slot.eggId = eggId
    slot.stand:SetAttribute("EggId", eggId)
    setPrompt(slot)
end

local function clear(slot)
    for _, part in eggParts(slot.stand) do
        part:Destroy()
    end
    slot.stand:SetAttribute("EggId", nil)
    slot.eggId = nil
    setPrompt(slot)
end

local function register(island, stand)
    local rest = stand:GetAttribute("EggRest")
    local pedestal = stand:FindFirstChild("Pedestal")
    if typeof(rest) ~= "CFrame" or not GameConfig.Eggs[stand:GetAttribute("EggId") or ""] then
        warn("EggStands: " .. stand:GetFullName() .. " has no EggRest or egg; skipped")
        return
    end
    local slot = {
        island = island, stand = stand, name = stand.Name, rest = rest, eggId = stand:GetAttribute("EggId"),
        prompt = pedestal and pedestal:FindFirstChildWhichIsA("ProximityPrompt"),
    }
    slotsOf[island] = slotsOf[island] or {}
    slotsOf[island][slot] = true
    learnLook(slot)
    -- the egg built with the stand gets its Highlight like any egg made since
    local body = stand:FindFirstChild("Egg")
    if body then
        body:SetAttribute("EggId", slot.eggId)
        CollectionService:AddTag(body, GameConfig.EggGlowTag)
    end
    setPrompt(slot)
    if slot.prompt then
        slot.prompt.HoldDuration = 0.5
        slot.prompt.Triggered:Connect(function(player)
            if slot.eggId and onTake then
                onTake(player, slot)
            end
        end)
    end
end

-- Finds every island's stands (call once at start, after the world is loaded).
function EggStands.load()
    local world = workspace:WaitForChild(WorldConfig.FolderName)
    for island in WorldConfig.Islands do
        local folder = world:FindFirstChild(island)
        local stands = folder and folder:FindFirstChild("EggStands")
        if stands then
            for _, stand in stands:GetChildren() do
                if stand:IsA("Model") then
                    register(island, stand)
                end
            end
        end
    end
end

-- What to do when a player asks to take a stand's egg: function(player, slot).
function EggStands.setTakeHandler(handler)
    onTake = handler
end

-- Whether the player stands close enough to the slot's egg to take it.
function EggStands.within(slot, position)
    return (position - slot.rest.Position).Magnitude <= TAKE_DISTANCE
end

-- The egg leaves its stand with a thief; returns its id.
function EggStands.take(slot)
    local eggId = slot.eggId
    if slot.respawn then
        task.cancel(slot.respawn)
        slot.respawn = nil
    end
    clear(slot)
    return eggId
end

-- A theft failed: the egg goes back to its stand.
function EggStands.restore(slot, eggId)
    if slot.eggId == nil then
        show(slot, eggId)
    end
end

-- A theft succeeded: after the respawn time a random egg of `eggIds` appears on the stand, unless no
-- other stand of the guardian holds the first of them, the lowest-rank egg: then that one, so a player
-- who has just reached the island's rank always has an egg they can take.
function EggStands.respawn(slot, eggIds)
    if slot.respawn then
        task.cancel(slot.respawn)
    end
    slot.respawn = task.delay(GameConfig.EggTheft.RespawnTime, function()
        slot.respawn = nil
        if slot.eggId == nil and slot.stand.Parent then
            local lowestShown = false
            for other in slotsOf[slot.island] do
                lowestShown = lowestShown or (other ~= slot and other.eggId == eggIds[1])
            end
            show(slot, if lowestShown then eggIds[math.random(1, #eggIds)] else eggIds[1])
        end
    end)
end

return EggStands
