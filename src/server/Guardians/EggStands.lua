-- The egg stands behind each island's guardian: the eggs players carry off (Guardian.lua) and hatch
-- at Yggdrasil's Hatching Altar (PetService). A stand holds one egg, shown with its glow ring, its
-- light and its aura:
--   * taking it empties the stand (EggStands.take);
--   * a dropped egg that times out, or a theft that fails, puts it back (EggStands.restore);
--   * a secured one leaves the stand empty for GameConfig.EggTheft.RespawnTime seconds, then a
--     random egg of its island's guardian's eggs appears there (EggStands.respawn).
-- Stands are found in Workspace.FloatingIslands.<Island>.EggStands (WorldBuilder.buildEggStands):
-- a Model per stand (named after the egg it was built with: its slot's name, which stays) with a
-- Pedestal, a GlowRing, the egg's body "Egg" and its "<EggId>_Glow_<hex>" pieces, and the
-- AuraOrigin attribute (the egg's resting point, facing the stand's front). Each egg's aura (an
-- "EggAura" model in the island's EggAuras folder) is kept as a template when the server starts, so
-- any stand can show any of its island's eggs; the aura's Stand attribute names its stand for the
-- client (src/client/Auras/EggAura.lua).
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local EggModel = require(script.Parent:WaitForChild("EggModel"))
local WorldConfig = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("WorldConfig"))

local EggStands = {}

local AURA_TAG = "EggAura"
local STUDS_PER_EGG_UNIT = 1.3 -- the stands' egg scale (WorldBuilder: EGG_STUDS_PER_UNIT)
local TAKE_DISTANCE = 12

local slotsByIsland = {} -- [island] = { slot }
local looks = {}         -- [eggId] = { ring = Color3, light = PointLight template, extras = { Instance }, aura = Model, auraOffset = CFrame }
local onTake             -- function(player, slot), set by GuardianService

local templates = Instance.new("Folder")
templates.Name = "EggStandTemplates"
templates.Parent = ServerStorage

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

-- The egg's look as built on its first stand: its ring colour, its light and sparkles, its aura.
local function learnLook(slot, aurasFolder)
    local eggId = slot.eggId
    if looks[eggId] then
        return
    end
    local look = { extras = {} }
    local ring = slot.stand:FindFirstChild("GlowRing")
    look.ring = ring and ring.Color
    local body = slot.stand:FindFirstChild("Egg")
    for _, child in body and body:GetChildren() or {} do
        if child:IsA("Light") or child:IsA("ParticleEmitter") then
            table.insert(look.extras, child:Clone())
        end
    end
    for _, aura in aurasFolder and aurasFolder:GetChildren() or {} do
        if CollectionService:HasTag(aura, AURA_TAG) and aura:GetAttribute("EggId") == eggId then
            look.auraOffset = slot.rest:ToObjectSpace(aura:GetPivot())
            local template = aura:Clone()
            template.Parent = templates
            look.aura = template
            slot.aura = aura
            aura:SetAttribute("Stand", slot.name)
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
    local height = box.Y * STUDS_PER_EGG_UNIT
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
    if look.aura then
        local aura = look.aura:Clone()
        aura:SetAttribute("Stand", slot.name)
        aura:PivotTo(slot.rest * look.auraOffset)
        aura.Parent = slot.aurasFolder
        slot.aura = aura
    end
    slot.eggId = eggId
    slot.stand:SetAttribute("EggId", eggId)
    setPrompt(slot)
end

local function clear(slot)
    for _, part in eggParts(slot.stand) do
        part:Destroy()
    end
    if slot.aura then
        slot.aura:Destroy()
        slot.aura = nil
    end
    slot.stand:SetAttribute("EggId", nil)
    slot.eggId = nil
    setPrompt(slot)
end

local function register(island, stand, aurasFolder)
    local origin = stand:GetAttribute("AuraOrigin")
    local pedestal = stand:FindFirstChild("Pedestal")
    if typeof(origin) ~= "CFrame" or not GameConfig.Eggs[stand:GetAttribute("EggId") or ""] then
        warn("EggStands: " .. stand:GetFullName() .. " has no AuraOrigin or egg; skipped")
        return
    end
    local slot = {
        island = island, stand = stand, name = stand.Name, rest = origin, eggId = stand:GetAttribute("EggId"),
        aurasFolder = aurasFolder, prompt = pedestal and pedestal:FindFirstChildWhichIsA("ProximityPrompt"),
    }
    learnLook(slot, aurasFolder)
    setPrompt(slot)
    if slot.prompt then
        slot.prompt.HoldDuration = 0.5
        slot.prompt.Triggered:Connect(function(player)
            if slot.eggId and onTake then
                onTake(player, slot)
            end
        end)
    end
    slotsByIsland[island] = slotsByIsland[island] or {}
    table.insert(slotsByIsland[island], slot)
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
                    register(island, stand, folder:FindFirstChild("EggAuras"))
                end
            end
        end
    end
end

-- What to do when a player asks to take a stand's egg: function(player, slot).
function EggStands.setTakeHandler(handler)
    onTake = handler
end

function EggStands.slots(island)
    return slotsByIsland[island] or {}
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

-- A theft succeeded: after the respawn time a random egg of `eggIds` appears on the stand.
function EggStands.respawn(slot, eggIds)
    if slot.respawn then
        task.cancel(slot.respawn)
    end
    slot.respawn = task.delay(GameConfig.EggTheft.RespawnTime, function()
        slot.respawn = nil
        if slot.eggId == nil and slot.stand.Parent then
            show(slot, eggIds[math.random(1, #eggIds)])
        end
    end)
end

return EggStands
