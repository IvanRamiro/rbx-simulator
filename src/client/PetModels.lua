-- What each pet companion looks like: small, original low-poly models built
-- from plain parts when needed (no uploaded meshes). Purely visual.
--
-- Each pet is a list of parts around the pet's centre, facing -Z (forward),
-- with +Y up and +X to the pet's right.
--   Shape         "Block", "Ball", "Wedge" or "Ellipsoid" (a block stretched
--                 into a smooth egg shape by a built-in sphere mesh)
--   Size          Size in studs, before the pet's Scale
--   At            Position and rotation relative to the pet's centre
--   Color         Colour of the part
--   Neon          Glows (for eyes, flames, energy)
--   Glass         Slightly see-through glassy surface (for water)
--   Transparency  0 to 1 (optional)
-- Scale makes the whole pet bigger or smaller (rarer pets are a little larger).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local PetModels = {}

local function at(x, y, z, rx, ry, rz)
    return CFrame.new(x, y, z) * CFrame.Angles(math.rad(rx or 0), math.rad(ry or 0), math.rad(rz or 0))
end

local BLACK = Color3.fromRGB(25, 25, 35)

-- Adds a pair of parts mirrored left and right. `make(side)` returns the
-- part for side = -1 (left) or 1 (right).
local function mirrored(parts, make)
    table.insert(parts, make(-1))
    table.insert(parts, make(1))
end

-- Pets ------------------------------------------------------------------------

local function aquaWisp()
    local water = Color3.fromRGB(70, 185, 255)
    local core = Color3.fromRGB(215, 248, 255)
    local parts = {
        { Shape = "Ball", Size = Vector3.new(1.4, 1.4, 1.4), At = at(0, 0, 0), Color = water, Glass = true, Transparency = 0.25 },
        { Shape = "Ball", Size = Vector3.new(0.7, 0.7, 0.7), At = at(0, 0, 0), Color = core, Neon = true },
        -- A droplet tail curling up behind it
        { Shape = "Ellipsoid", Size = Vector3.new(0.6, 0.6, 1.2), At = at(0, 0.35, 0.8, 35), Color = water, Glass = true, Transparency = 0.3 },
        { Shape = "Ellipsoid", Size = Vector3.new(0.35, 0.35, 0.7), At = at(0, 0.75, 1.3, 55), Color = core, Neon = true },
    }
    mirrored(parts, function(side)
        return { Shape = "Ball", Size = Vector3.new(0.18, 0.18, 0.18), At = at(0.25 * side, 0.15, -0.62), Color = BLACK }
    end)
    mirrored(parts, function(side)
        return { Shape = "Ellipsoid", Size = Vector3.new(0.15, 0.5, 0.7), At = at(0.72 * side, -0.1, 0.1, 0, 0, -25 * side), Color = water, Glass = true, Transparency = 0.3 }
    end)
    return { Scale = 0.9, Parts = parts }
end

local function emberWyrm()
    local scales = Color3.fromRGB(255, 120, 40)
    local dark = Color3.fromRGB(165, 45, 20)
    local flame = Color3.fromRGB(255, 205, 90)
    local parts = {
        { Shape = "Ellipsoid", Size = Vector3.new(0.9, 0.8, 1), At = at(0, 0.4, -0.7), Color = scales },
        { Shape = "Block", Size = Vector3.new(0.5, 0.35, 0.5), At = at(0, 0.3, -1.3), Color = scales },
        -- Body segments getting smaller towards the tail
        { Shape = "Ball", Size = Vector3.new(0.85, 0.85, 0.85), At = at(0, 0, 0), Color = scales },
        { Shape = "Ball", Size = Vector3.new(0.7, 0.7, 0.7), At = at(0, -0.1, 0.65), Color = scales },
        { Shape = "Ball", Size = Vector3.new(0.55, 0.55, 0.55), At = at(0, 0.05, 1.2), Color = dark },
        { Shape = "Ball", Size = Vector3.new(0.4, 0.4, 0.4), At = at(0, 0.25, 1.65), Color = dark },
        { Shape = "Ellipsoid", Size = Vector3.new(0.3, 0.6, 0.3), At = at(0, 0.6, 1.95, -30), Color = flame, Neon = true },
    }
    mirrored(parts, function(side)
        return { Shape = "Wedge", Size = Vector3.new(0.15, 0.5, 0.35), At = at(0.25 * side, 0.95, -0.55, -20), Color = dark }
    end)
    mirrored(parts, function(side)
        return { Shape = "Ball", Size = Vector3.new(0.15, 0.15, 0.15), At = at(0.3 * side, 0.55, -1.05), Color = flame, Neon = true }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.9, 0.06, 0.6), At = at(0.7 * side, 0.35, 0.1, 0, 0, 25 * side), Color = dark }
    end)
    return { Scale = 1, Parts = parts }
end

local function voltFox()
    local fur = Color3.fromRGB(255, 210, 60)
    local cream = Color3.fromRGB(255, 245, 210)
    local spark = Color3.fromRGB(170, 110, 255)
    local parts = {
        { Shape = "Ellipsoid", Size = Vector3.new(0.8, 0.75, 1.3), At = at(0, 0, 0.1), Color = fur },
        { Shape = "Ellipsoid", Size = Vector3.new(0.85, 0.75, 0.8), At = at(0, 0.45, -0.7), Color = fur },
        { Shape = "Ellipsoid", Size = Vector3.new(0.4, 0.3, 0.45), At = at(0, 0.35, -1.15), Color = cream },
        { Shape = "Ball", Size = Vector3.new(0.12, 0.12, 0.12), At = at(0, 0.38, -1.38), Color = BLACK },
        -- A zig-zag lightning-bolt tail with a glowing tip
        { Shape = "Block", Size = Vector3.new(0.25, 0.25, 0.6), At = at(0, 0.3, 0.95, 40), Color = fur },
        { Shape = "Block", Size = Vector3.new(0.25, 0.25, 0.6), At = at(0, 0.75, 1.2, -30), Color = fur },
        { Shape = "Block", Size = Vector3.new(0.22, 0.22, 0.5), At = at(0, 1.15, 1.5, 45), Color = spark, Neon = true },
    }
    mirrored(parts, function(side)
        return { Shape = "Wedge", Size = Vector3.new(0.12, 0.5, 0.35), At = at(0.25 * side, 0.95, -0.7, 0, 90 * side), Color = fur }
    end)
    mirrored(parts, function(side)
        return { Shape = "Ball", Size = Vector3.new(0.14, 0.14, 0.14), At = at(0.22 * side, 0.55, -1.05), Color = BLACK }
    end)
    mirrored(parts, function(side)
        return { Shape = "Ball", Size = Vector3.new(0.12, 0.12, 0.12), At = at(0.38 * side, 0.3, -0.9), Color = spark, Neon = true }
    end)
    for _, z in { -0.3, 0.45 } do
        mirrored(parts, function(side)
            return { Shape = "Block", Size = Vector3.new(0.2, 0.35, 0.2), At = at(0.25 * side, -0.45, z), Color = fur }
        end)
    end
    return { Scale = 1, Parts = parts }
end

local function goldenKirin()
    local gold = Color3.fromRGB(230, 185, 70)
    local darkGold = Color3.fromRGB(185, 135, 45)
    local jade = Color3.fromRGB(90, 220, 140)
    local parts = {
        { Shape = "Ellipsoid", Size = Vector3.new(0.85, 0.8, 1.5), At = at(0, 0, 0), Color = gold },
        { Shape = "Block", Size = Vector3.new(0.4, 0.7, 0.4), At = at(0, 0.5, -0.6, -25), Color = gold },
        { Shape = "Ellipsoid", Size = Vector3.new(0.55, 0.5, 0.75), At = at(0, 0.95, -0.9), Color = gold },
        { Shape = "Ellipsoid", Size = Vector3.new(0.2, 0.6, 0.8), At = at(0, 0.75, -0.45, -25), Color = jade, Neon = true },
        { Shape = "Ellipsoid", Size = Vector3.new(0.2, 0.2, 0.6), At = at(0, 0.2, 0.85, 30), Color = jade, Neon = true },
    }
    -- Branching jade antlers
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.08, 0.6, 0.08), At = at(0.15 * side, 1.4, -0.85, 0, 0, -20 * side), Color = jade, Neon = true }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.07, 0.35, 0.07), At = at(0.3 * side, 1.45, -0.85, 0, 0, -60 * side), Color = jade, Neon = true }
    end)
    mirrored(parts, function(side)
        return { Shape = "Ball", Size = Vector3.new(0.1, 0.1, 0.1), At = at(0.2 * side, 1, -1.15), Color = BLACK }
    end)
    for _, z in { -0.5, 0.5 } do
        mirrored(parts, function(side)
            return { Shape = "Block", Size = Vector3.new(0.15, 0.6, 0.15), At = at(0.25 * side, -0.6, z), Color = darkGold }
        end)
        mirrored(parts, function(side)
            return { Shape = "Block", Size = Vector3.new(0.17, 0.12, 0.17), At = at(0.25 * side, -0.92, z), Color = jade, Neon = true }
        end)
    end
    return { Scale = 1.15, Parts = parts }
end

local function nineTailMoonfox()
    local fur = Color3.fromRGB(245, 245, 255)
    local lilac = Color3.fromRGB(190, 160, 255)
    local violet = Color3.fromRGB(150, 110, 255)
    local parts = {
        { Shape = "Ellipsoid", Size = Vector3.new(0.75, 0.7, 1.2), At = at(0, 0, 0.1), Color = fur },
        { Shape = "Ellipsoid", Size = Vector3.new(0.8, 0.7, 0.75), At = at(0, 0.45, -0.65), Color = fur },
        { Shape = "Ellipsoid", Size = Vector3.new(0.35, 0.28, 0.4), At = at(0, 0.35, -1.05), Color = fur },
        { Shape = "Ball", Size = Vector3.new(0.12, 0.12, 0.12), At = at(0, 0.72, -0.98), Color = lilac, Neon = true }, -- Moon mark
    }
    mirrored(parts, function(side)
        return { Shape = "Wedge", Size = Vector3.new(0.12, 0.5, 0.35), At = at(0.25 * side, 0.92, -0.6, 0, 90 * side), Color = fur }
    end)
    mirrored(parts, function(side)
        return { Shape = "Ball", Size = Vector3.new(0.13, 0.13, 0.13), At = at(0.2 * side, 0.52, -0.98), Color = violet, Neon = true }
    end)
    -- Nine tails fanned out behind, each with a glowing tip
    for tail = 1, 9 do
        local base = at(0, 0.15, 0.75, 25, 0, -60 + (tail - 1) * 15)
        table.insert(parts, { Shape = "Ellipsoid", Size = Vector3.new(0.22, 0.85, 0.22), At = base * CFrame.new(0, 0.5, 0), Color = fur })
        table.insert(parts, { Shape = "Ball", Size = Vector3.new(0.2, 0.2, 0.2), At = base * CFrame.new(0, 0.95, 0), Color = lilac, Neon = true })
    end
    return { Scale = 1.2, Parts = parts }
end

local function originSerpent()
    local scales = Color3.fromRGB(70, 25, 110)
    local amber = Color3.fromRGB(235, 150, 60)
    local parts = {}
    -- A rising coil of segments with a glowing amber band on every third one
    for segment = 0, 9 do
        local t = segment / 9
        local angle = t * 2.6 * math.pi
        local radius = 0.65 - 0.2 * t
        local size = 0.55 - 0.2 * t
        table.insert(parts, {
            Shape = "Ball",
            Size = Vector3.new(size, size, size),
            At = at(math.cos(angle) * radius, -0.4 + t, math.sin(angle) * radius),
            Color = if segment % 3 == 1 then amber else scales,
            Neon = segment % 3 == 1,
        })
    end
    table.insert(parts, { Shape = "Ellipsoid", Size = Vector3.new(0.6, 0.45, 0.8), At = at(0, 0.85, -0.45), Color = scales })
    table.insert(parts, { Shape = "Wedge", Size = Vector3.new(0.08, 0.4, 0.5), At = at(0, 1.15, -0.35), Color = amber, Neon = true })
    table.insert(parts, { Shape = "Ball", Size = Vector3.new(0.3, 0.3, 0.3), At = at(0, 1.6, 0.2), Color = amber, Neon = true }) -- Origin pearl
    mirrored(parts, function(side)
        return { Shape = "Ball", Size = Vector3.new(0.12, 0.12, 0.12), At = at(0.18 * side, 0.95, -0.75), Color = amber, Neon = true }
    end)
    return { Scale = 1.25, Parts = parts }
end

PetModels.Pets = {
    AquaWisp = aquaWisp(),
    EmberWyrm = emberWyrm(),
    VoltFox = voltFox(),
    GoldenKirin = goldenKirin(),
    NineTailMoonfox = nineTailMoonfox(),
    OriginSerpent = originSerpent(),
}

-- Building ----------------------------------------------------------------------

local PART_SHAPES = {
    Block = Enum.PartType.Block,
    Ball = Enum.PartType.Ball,
    Wedge = Enum.PartType.Wedge,
    Ellipsoid = Enum.PartType.Block,
}

-- Builds a pet's model (not yet parented). Returns the model and a list of
-- { Part = part, Offset = CFrame } so the caller can move every part at once
-- with workspace:BulkMoveTo(part, petCFrame * offset). Unknown pets return nil.
function PetModels.build(petId)
    local design = PetModels.Pets[petId]
    if not design then
        return nil
    end

    local model = Instance.new("Model")
    model.Name = petId
    local parts = {}

    for _, spec in design.Parts do
        local part = Instance.new("Part")
        part.Shape = PART_SHAPES[spec.Shape]
        part.Size = spec.Size * design.Scale
        part.Color = spec.Color
        part.Material = if spec.Neon then Enum.Material.Neon elseif spec.Glass then Enum.Material.Glass else Enum.Material.SmoothPlastic
        part.Transparency = spec.Transparency or 0
        part.TopSurface = Enum.SurfaceType.Smooth
        part.BottomSurface = Enum.SurfaceType.Smooth
        -- Visual only: never collides, triggers touches, blocks raycasts or casts shadows
        part.Anchored = true
        part.CanCollide = false
        part.CanTouch = false
        part.CanQuery = false
        part.CastShadow = false

        if spec.Shape == "Ellipsoid" then
            local mesh = Instance.new("SpecialMesh")
            mesh.MeshType = Enum.MeshType.Sphere
            mesh.Parent = part
        end

        part.Parent = model

        local offset = spec.At
        table.insert(parts, { Part = part, Offset = offset - offset.Position + offset.Position * design.Scale })
    end

    return model, parts
end

-- Catch config mistakes as soon as the game starts
for petId in GameConfig.Pets do
    assert(PetModels.Pets[petId], "PetModels has no model for pet " .. petId)
end

for petId, design in PetModels.Pets do
    for _, spec in design.Parts do
        assert(PART_SHAPES[spec.Shape], "PetModels: " .. petId .. " uses an unknown Shape: " .. tostring(spec.Shape))
    end
end

return PetModels
