-- Build-time only: stores an imported guardian (an FBX from tools/blender/guardians) in
-- ServerStorage.Guardians.<GuardianId> as a jointed Model for GuardianService to clone. Require a clone:
--
--   local GB = require(game.ServerStorage.WorldBuild.GuardianBuilder:Clone())
--   GB.store(workspace.MantisSage, "MantisSage")
--
-- The Model:
--   Root      invisible anchored PrimaryPart; the Model's pivot is the origin, on the ground.
--   <Piece>   unanchored, massless MeshParts. A segment's first piece is named after it (Body,
--             Head, Jaw...); its other pieces are welded to that one.
--   Joints    a Motor6D per segment, named after it, from its parent segment (the Body from Root) at
--             the segment's pivot: animate a segment by its Motor6D's Transform.
-- Glow pieces are Neon with the attribute Glow. The import is fitted with OutfitBuilder.fit, so it
-- may come in anywhere and either way round.
local ServerStorage = game:GetService("ServerStorage")

local OutfitBuilder = require(ServerStorage.WorldBuild.OutfitBuilder:Clone())

local GuardianBuilder = {}

local ROOT_SIZE = Vector3.new(4, 1, 4)

-- The import's pieces: "<prefix>_<Piece>", glow pieces "<prefix>_<Segment>_Glow_<hex>" (matched by
-- segment and colour, since two segments may glow alike).
local function findPieces(model, placements)
    local found = {}
    for _, d in model:GetDescendants() do
        if d:IsA("MeshPart") then
            local segment, hex = string.match(d.Name, "_(%w+)_Glow_(%x+)$")
            for name, info in placements.Pieces do
                if (hex and info.Hex == hex and info.Segment == segment)
                    or (not hex and not info.Hex and string.match(d.Name, "_(%w+)$") == name) then
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
    root.PivotOffset = CFrame.new(0, -ROOT_SIZE.Y / 2, 0)
    root.Parent = guardian
    guardian.PrimaryPart = root

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

    for name, part in found do
        local segment = placements.Pieces[name].Segment
        if name ~= segment then
            local weld = Instance.new("Weld")
            weld.Part0, weld.Part1 = found[segment], part
            weld.C0 = found[segment].CFrame:ToObjectSpace(part.CFrame)
            weld.Parent = part
        end
    end

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

-- A guardian with a skeleton (tools/blender/guardians/<id>_v2.py): one skin and its other pieces on bones, posed through
-- Bone.Transform (GuardianAnim, rig.Skinned). `model` is the import. Its pieces stay welded to a Root at its feet, as a
-- jointed guardian's root is, so the server moves it the same way. Placements.<id>Skinned names the pieces.
function GuardianBuilder.storeSkinned(model, guardianId)
    local placements = require(ServerStorage.WorldBuild.Placements:FindFirstChild(guardianId .. "Skinned"):Clone())
    local bones, parts = {}, {}
    for _, d in model:GetDescendants() do
        if d:IsA("Bone") then
            bones[d.Name] = d
        elseif d:IsA("BasePart") then
            table.insert(parts, d)
        end
    end
    for name, info in placements.AddBones or {} do
        if not bones[name] then
            local bone = Instance.new("Bone")
            bone.Name = name
            bone.CFrame = info.CFrame
            bone.Parent = bones[info.Parent]
            bones[name] = bone
        end
    end
    -- the importer may turn or move it: found from three bones whose authored positions are known
    local function at(name)
        assert(bones[name], "the import has no bone " .. name)
        local cf = bones[name].CFrame
        local up = bones[name].Parent
        while up:IsA("Bone") do
            cf = up.CFrame * cf
            up = up.Parent
        end
        return up.CFrame:PointToWorldSpace(cf.Position)
    end
    local authored = placements.Fit
    local toImport = at("Head") - at("Hips")
    local toAuthored = authored.Head - authored.Hips
    local yaw = math.atan2(-toImport.Z, toImport.X) - math.atan2(-toAuthored.Z, toAuthored.X)
    local frame = CFrame.new(at("Hips")) * CFrame.Angles(0, yaw, 0) * CFrame.new(-authored.Hips)
    local worst = 0
    for name, position in authored do
        worst = math.max(worst, (frame:PointToObjectSpace(at(name)) - position).Magnitude)
    end
    assert(worst < 0.1, ("the skeleton does not match its authored layout (%.3f studs off)"):format(worst))

    local guardian = Instance.new("Model")
    guardian.Name = guardianId
    local root = Instance.new("Part")
    root.Name = "Root"
    root.Size = ROOT_SIZE
    root.CFrame = CFrame.new(0, ROOT_SIZE.Y / 2, 0)
    root.Anchored = true
    root.CanCollide, root.CanTouch, root.CanQuery = false, false, false
    root.Transparency = 1
    root.PivotOffset = CFrame.new(0, -ROOT_SIZE.Y / 2, 0)
    root.Parent = guardian
    guardian.PrimaryPart = root

    -- the importer's motors join the pieces, so moving one moves them all: every destination is worked out before any moves, or the
    -- same move lands once per piece. Checked first, so a bad one leaves the import as it was
    local targets = {}
    for _, part in parts do
        targets[part] = frame:ToObjectSpace(part.CFrame)
        assert(targets[part].Position.Magnitude < 200, ("%s would land %.0f studs from the guardian's feet"):format(part.Name, targets[part].Position.Magnitude))
    end
    local names = {}
    for part, target in targets do
        part.CFrame = target
    end
    local landed = (at("Hips") - authored.Hips).Magnitude
    assert(landed < 0.01, ("the hips landed %.3f studs from their place"):format(landed))
    for _, part in parts do
        if part.Name == "RootPart" then -- the importer's holder of the bones
            part.Transparency = 1
            part.CastShadow = false
        end
        part.Anchored = false
        part.CanCollide, part.CanQuery, part.CanTouch = false, false, false
        part.Massless = true
        local glow = placements.Glow[part.Name]
        if glow then
            part.Material = Enum.Material.Neon
            part.Color = glow
            part.CastShadow = false
            part.TextureID = ""
            local look = part:FindFirstChildOfClass("SurfaceAppearance")
            if look then
                look:Destroy()
            end
        end
        local weld = Instance.new("Weld")
        weld.Part0, weld.Part1 = root, part
        weld.C0 = root.CFrame:ToObjectSpace(part.CFrame)
        weld.Parent = part
        part.Parent = guardian
        names[#names + 1] = part.Name
    end
    guardian:SetAttribute("Rig", placements.Rig)

    local folder = ServerStorage:FindFirstChild("Guardians") or Instance.new("Folder")
    folder.Name = "Guardians"
    folder.Parent = ServerStorage
    local old = folder:FindFirstChild(guardianId)
    if old then
        old:Destroy() -- a new build replaces the old one outright
    end
    model:Destroy()
    guardian.Parent = folder
    return names, worst
end

return GuardianBuilder
