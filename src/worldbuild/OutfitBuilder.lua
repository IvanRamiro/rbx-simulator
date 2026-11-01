-- Build-time only: stores an imported outfit (an FBX from tools/blender/outfits) in
-- ServerStorage.Outfits.<OutfitId>, each piece a MeshPart carrying the body part it rides
-- (attribute BodyPart) and where it sits on it (attribute Offset, a CFrame in that part's space).
-- OutfitService clones them onto a character. Require a clone, as with WorldBuilder:
--
--   local OB = require(game.ServerStorage.WorldBuild.OutfitBuilder:Clone())
--   OB.store(workspace.MurimOutfit, "Murim")
--
-- The pieces were authored round the owner's avatar at rest (Placements/<OutfitId>Outfit.lua). The
-- importer may turn the model half round, so the fit is found by matching the pieces' centres as
-- authored to where they came in, turned 0 or 180 degrees, whichever matches.
local ServerStorage = game:GetService("ServerStorage")

local OutfitBuilder = {}

local function placementsFor(outfitId)
    return require(ServerStorage.WorldBuild.Placements:FindFirstChild(outfitId .. "Outfit"):Clone())
end

-- The import's pieces by name ("<prefix>_<Piece>" in the FBX).
local function findPieces(model, placements)
    local found = {}
    for _, d in model:GetDescendants() do
        if d:IsA("MeshPart") then
            local piece = string.match(d.Name, "_(%w+)$")
            if piece and placements.Pieces[piece] then
                found[piece] = d
            end
        end
    end
    return found
end

-- The import's frame relative to the authored one: a turn about Y (0 or 180 degrees) and a shift,
-- and how far the worst piece is off under it.
local function fit(found, placements)
    local best
    for _, turn in { 0, math.pi } do
        local rotation = CFrame.Angles(0, turn, 0)
        local sumAuthored, sumImported, n = Vector3.zero, Vector3.zero, 0
        for piece, part in found do
            sumAuthored += rotation * placements.Pieces[piece].Centre
            sumImported += part.Position
            n += 1
        end
        local shift = (sumImported - sumAuthored) / n
        local frame = CFrame.new(shift) * rotation
        local worst = 0
        for piece, part in found do
            worst = math.max(worst, ((frame * placements.Pieces[piece].Centre) - part.Position).Magnitude)
        end
        if not best or worst < best.worst then
            best = { frame = frame, worst = worst, turn = turn }
        end
    end
    return best
end

-- The importer hangs every rig's bones from one RootPart. Each piece rides its own body part, so
-- each chain moves into its piece (bones are named after it: SkirtRoot, LeftCuffHem...), keeping
-- where it is in the world.
local function adoptBones(model, found)
    for _, bone in model:GetDescendants() do
        if bone:IsA("Bone") and not bone.Parent:IsA("Bone") then
            for piece, part in found do
                if string.sub(bone.Name, 1, #piece) == piece and not found[piece .. "Root"] then
                    local world = bone.Parent.CFrame * bone.CFrame
                    bone.Parent = part
                    bone.CFrame = part.CFrame:ToObjectSpace(world)
                    break
                end
            end
        end
    end
end

function OutfitBuilder.store(model, outfitId)
    local placements = placementsFor(outfitId)
    local found = findPieces(model, placements)
    for piece in placements.Pieces do
        assert(found[piece], "the import has no piece " .. piece)
    end
    adoptBones(model, found)
    for _, bone in model:GetDescendants() do
        assert(not bone:IsA("Bone") or bone:FindFirstAncestorWhichIsA("MeshPart"), "bone " .. bone.Name .. " has no piece")
    end
    local frame = fit(found, placements)
    assert(frame.worst < 0.05, ("the pieces do not match their authored layout (worst %.3f studs off)"):format(frame.worst))

    local root = ServerStorage:FindFirstChild("Outfits") or Instance.new("Folder")
    root.Name = "Outfits"
    root.Parent = ServerStorage
    local old = root:FindFirstChild(outfitId)
    if old then
        old:Destroy()
    end
    local folder = Instance.new("Folder")
    folder.Name = outfitId

    for piece, part in found do
        local info = placements.Pieces[piece]
        local rest = frame.frame:ToObjectSpace(part.CFrame)                 -- where it sits round the avatar at rest
        local offset = CFrame.new(placements.BodyParts[info.Part]):ToObjectSpace(rest)
        part.Name = piece
        part.Anchored = true
        part.CanCollide = false
        part.CanQuery = false
        part.CanTouch = false
        part.Massless = true
        part.CastShadow = true
        part:SetAttribute("BodyPart", info.Part)
        part:SetAttribute("Offset", offset)
        part:SetAttribute("Skinned", info.Skinned)
        part.Parent = folder
    end
    model:Destroy()
    folder.Parent = root
    if placements.Maps then
        OutfitBuilder.setMaps(outfitId, placements.Maps)
    end
    return { pieces = #folder:GetChildren(), worst = frame.worst, turned = frame.turn ~= 0 }
end

-- Sets the pieces' maps: { <Piece> = { Color = id, Normal = id, Roughness = id, Metalness = id } }.
function OutfitBuilder.setMaps(outfitId, maps)
    local folder = ServerStorage.Outfits[outfitId]
    for piece, ids in maps do
        local part = folder:FindFirstChild(piece)
        local appearance = part and part:FindFirstChildOfClass("SurfaceAppearance")
        if appearance then
            appearance.ColorMap = ids.Color or appearance.ColorMap
            appearance.NormalMap = ids.Normal or appearance.NormalMap
            appearance.RoughnessMap = ids.Roughness
            appearance.MetalnessMap = ids.Metalness
        end
    end
end

return OutfitBuilder
