-- Build-time only: stores an imported guardian (an FBX from tools/blender/guardians) in
-- ServerStorage.Guardians.<GuardianId> as a jointed Model, ready for GuardianService to clone into
-- the world. Require a clone, as with WorldBuilder:
--
--   local GB = require(game.ServerStorage.WorldBuild.GuardianBuilder:Clone())
--   GB.store(workspace.StoneLion, "StoneLion")
--
-- The Model:
--   Root      an invisible anchored part under the chest, the PrimaryPart. The Model's pivot is
--             the origin, on the ground: the guardian is moved by pivoting the Model.
--   <Piece>   the MeshParts, unanchored and massless. A segment's first piece is named after it
--             (Body, Head, Jaw, Tail, FrontLeftUpper...); its other pieces are welded to that one.
--   Joints    a Motor6D per segment, named after it, from its parent segment (the Body from Root) at
--             the segment's pivot: animate a segment by its Motor6D's Transform.
-- Glow pieces are Neon, with the attribute Glow, in their look from the placements (Glow) or else
-- their exported colour.
--
-- The import is fitted like the outfits (OutfitBuilder.fit: by the pieces' centres, turned 0 or 180
-- degrees), so it may come in anywhere and either way round.
local ServerStorage = game:GetService("ServerStorage")

local OutfitBuilder = require(ServerStorage.WorldBuild.OutfitBuilder:Clone())

local GuardianBuilder = {}

local ROOT_SIZE = Vector3.new(4, 1, 4)

-- The import's pieces: "<prefix>_<Piece>", the glow pieces "<prefix>_<Segment>_Glow_<hex>".
local function findPieces(model, placements)
    local found = {}
    for _, d in model:GetDescendants() do
        if d:IsA("MeshPart") then
            local hex = string.match(d.Name, "_Glow_(%x+)$")
            for name, info in placements.Pieces do
                if (hex and info.Hex == hex) or (not hex and not info.Hex and string.match(d.Name, "_(%w+)$") == name) then
                    assert(not found[name], "the import has two pieces " .. name)
                    found[name] = d
                end
            end
        end
    end
    return found
end

function GuardianBuilder.store(model, guardianId)
    local placements = require(ServerStorage.WorldBuild.Placements:FindFirstChild(guardianId):Clone())
    local found = findPieces(model, placements)
    for name in placements.Pieces do
        assert(found[name], "the import has no piece " .. name)
    end
    local frame = OutfitBuilder.fit(found, placements)
    assert(frame.worst < 0.05, ("the pieces do not match their authored layout (worst %.3f studs off)"):format(frame.worst))

    local guardian = Instance.new("Model")
    guardian.Name = guardianId
    local root = Instance.new("Part")
    root.Name = "Root"
    root.Size = ROOT_SIZE
    root.CFrame = CFrame.new(0, ROOT_SIZE.Y / 2, 0)
    root.Anchored = true
    root.CanCollide = false
    root.CanTouch = false
    root.CanQuery = false
    root.Transparency = 1
    root.PivotOffset = CFrame.new(0, -ROOT_SIZE.Y / 2, 0) -- the Model's pivot is its origin, on the ground
    root.Parent = guardian
    guardian.PrimaryPart = root

    -- every piece where it was authored, round the origin
    for name, part in found do
        local info = placements.Pieces[name]
        part.CFrame = frame.frame:ToObjectSpace(part.CFrame)
        part.Name = name
        part.Anchored = false
        part.CanCollide = false
        part.CanQuery = false
        part.CanTouch = false
        part.Massless = true
        part:SetAttribute("Segment", info.Segment)
        if info.Hex then
            part:SetAttribute("Glow", true)
            part.Material = Enum.Material.Neon
            local look = placements.Glow and placements.Glow[name] or {}
            part.Color = look.Color or Color3.fromHex(info.Hex)
            if look.Scale then
                local at = part.CFrame
                part.Size *= look.Scale
                part.CFrame = at
            end
            part.CastShadow = false
            part.TextureID = ""
            for _, child in part:GetChildren() do
                child:Destroy()
            end
        else
            part.CastShadow = true
            local ids = placements.Maps[name]
            local appearance = part:FindFirstChildOfClass("SurfaceAppearance") or Instance.new("SurfaceAppearance")
            appearance.ColorMap, appearance.NormalMap = ids.Color, ids.Normal
            appearance.RoughnessMap, appearance.MetalnessMap = ids.Roughness, ids.Metalness
            appearance.Parent = part
        end
        part.Parent = guardian
    end

    -- a segment's other pieces ride its first
    for name, part in found do
        local segment = placements.Pieces[name].Segment
        if name ~= segment then
            local weld = Instance.new("Weld")
            weld.Part0, weld.Part1 = found[segment], part
            weld.C0 = found[segment].CFrame:ToObjectSpace(part.CFrame)
            weld.Parent = part
        end
    end

    -- the joints, each at its segment's pivot
    local joints = Instance.new("Folder")
    joints.Name = "Joints"
    for segment, pivot in placements.Pivots do
        local part0 = if pivot.Parent then found[pivot.Parent] else root
        local part1 = found[segment]
        assert(part0 and part1, "no piece for the joint " .. segment)
        local at = CFrame.new(pivot.Position)
        local motor = Instance.new("Motor6D")
        motor.Name = segment
        motor.Part0, motor.Part1 = part0, part1
        motor.C0 = part0.CFrame:ToObjectSpace(at)
        motor.C1 = part1.CFrame:ToObjectSpace(at)
        motor.Parent = joints
    end
    joints.Parent = guardian

    local folder = ServerStorage:FindFirstChild("Guardians") or Instance.new("Folder")
    folder.Name = "Guardians"
    folder.Parent = ServerStorage
    local old = folder:FindFirstChild(guardianId)
    if old then
        old:Destroy()
    end
    model:Destroy()
    guardian.Parent = folder
    local count = 0
    for _ in found do
        count += 1
    end
    return { pieces = count, worst = frame.worst, turned = frame.turn ~= 0 }
end

return GuardianBuilder
