-- Build-time only: stores an imported outfit (an FBX from tools/blender/outfits) in
-- ServerStorage.Outfits.<OutfitId>, each piece a MeshPart carrying the body part it rides
-- (attribute BodyPart) and where it sits on it (attribute Offset, a CFrame in that part's space).
-- OutfitService clones them onto a character. Require a clone, as with WorldBuilder:
--
--   local OB = require(game.ServerStorage.WorldBuild.OutfitBuilder:Clone())
--   OB.store(workspace.MurimOutfit, "Murim")
--
-- The pieces were authored round the owner's avatar at rest (Placements/<OutfitId>Outfit.lua). The
-- importer may turn the model half round, so the fit tries both 0 and 180 degrees.
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
OutfitBuilder.fit = fit

-- The importer hangs every rig's bones from one RootPart. Each piece rides its own body part, so
-- each chain moves into the piece it is named after (SkirtRoot, LeftCuffHem...), keeping its world position.
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
        local rest = frame.frame:ToObjectSpace(part.CFrame)
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

-- Moves an imported weapon's pieces into ServerStorage.Weapons.<name>: the body ("<prefix>_Body")
-- and each glow piece ("<prefix>_Glow_<hex>", found by its Hex), named as in its placements, each
-- with its "Offset" from the authored origin and a "Glow" attribute; glow pieces are Neon, their
-- exported colour. maps:
-- { <Piece> = { Color, Normal, Roughness, Metalness } }, our own uploads (the importer's are
-- unreliable). Returns the folder and how well the pieces fit their authored layout.
local function storePieces(name, placements, model, maps)
    local found = {}
    for _, d in model:GetDescendants() do
        if d:IsA("MeshPart") then
            local hex = string.match(d.Name, "_Glow_(%x+)$")
            for piece, info in placements.Pieces do
                if (hex and info.Hex == hex) or (not hex and not info.Hex and string.match(d.Name, "_Body$")) then
                    found[piece] = d
                end
            end
        end
    end
    for piece in placements.Pieces do
        assert(found[piece], "the import has no piece " .. piece)
    end
    local frame = fit(found, placements)
    assert(frame.worst < 0.05, ("the pieces do not match their authored layout (worst %.3f studs off)"):format(frame.worst))

    local root = ServerStorage:FindFirstChild("Weapons") or Instance.new("Folder")
    root.Name = "Weapons"
    root.Parent = ServerStorage
    local old = root:FindFirstChild(name)
    if old then
        old:Destroy()
    end
    local folder = Instance.new("Folder")
    folder.Name = name
    for piece, part in found do
        part.Name = piece
        part.Anchored = true
        part.CanCollide = false
        part.CanQuery = false
        part.CanTouch = false
        part.Massless = true
        local glow = placements.Pieces[piece].Hex ~= nil
        part.CastShadow = not glow
        part:SetAttribute("Glow", glow)
        if glow then
            part.Material = Enum.Material.Neon
            part.Color = Color3.fromHex(placements.Pieces[piece].Hex) -- the flying sword's is recoloured per realm in game
            part.TextureID = ""
            for _, child in part:GetChildren() do
                child:Destroy()
            end
        end
        part:SetAttribute("Offset", frame.frame:ToObjectSpace(part.CFrame))
        part.Parent = folder
    end
    model:Destroy()
    folder.Parent = root
    for piece, ids in maps or {} do
        local appearance = folder[piece]:FindFirstChildOfClass("SurfaceAppearance")
        if appearance then
            appearance.ColorMap, appearance.NormalMap = ids.Color, ids.Normal
            appearance.RoughnessMap, appearance.MetalnessMap = ids.Roughness, ids.Metalness
        end
    end
    return folder, { worst = frame.worst, turned = frame.turn ~= 0 }
end

-- Stores an imported flying sword (assets/weapons/FlyingSword.fbx) in ServerStorage.Weapons.FlyingSword:
-- "Body" and its Neon glow pieces (found by exported colour), each with its Offset from the sword's origin.
function OutfitBuilder.storeSword(model)
    local placements = require(ServerStorage.WorldBuild.Placements.FlyingSword:Clone())
    local folder, result = storePieces("FlyingSword", placements, model, placements.Maps)
    folder:SetAttribute("Top", placements.Top)
    return result
end

-- Stores a realm weapon (tools/blender/weapons; Placements/Weapons/<WeaponId>, its maps in
-- Placements/WeaponMaps) as ServerStorage.Weapons.<WeaponId>, with its Kind ("Sword" or "Spear") and
-- its Hilt and Tip (where its blade or head starts, and its point, from its grip) as attributes.
-- CombatService hands it to the clients, which show it striking (CombatFx).
--   OB.storeWeapon("Sword1", workspace.Sword1)
function OutfitBuilder.storeWeapon(weaponId, model)
    local source = ServerStorage.WorldBuild.Placements.Weapons:FindFirstChild(weaponId)
    assert(source, "no placements for weapon " .. tostring(weaponId))
    local placements = require(source:Clone())
    local maps = require(ServerStorage.WorldBuild.Placements.WeaponMaps:Clone())[weaponId]
    local folder, result = storePieces(weaponId, placements, model, maps and { Body = maps })
    folder:SetAttribute("Kind", placements.Kind)
    folder:SetAttribute("Hilt", placements.Hilt)
    folder:SetAttribute("Tip", placements.Tip)
    return result
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
