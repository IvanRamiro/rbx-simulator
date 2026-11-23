-- Build-time only: stores an imported guardian (an FBX from tools/blender/guardians) in ServerStorage.Guardians.<GuardianId> for GuardianService to
-- clone. Every guardian is skinned (a skeleton and weight-painted pieces, posed through Bone.Transform by GuardianAnim); the older jointed form
-- (rigid segments on Motor6Ds, the Ember Xuanwu's) went with that guardian on 2026-11-23. Require a clone:
--
--   local GB = require(game.ServerStorage.WorldBuild.GuardianBuilder:Clone())
--   GB.storeSkinned(workspace.CinderRoc, "EmberXuanwu")     -- the import's Model and the guardian's id (Placements/<id>Skinned names its pieces)
--
-- The Model:
--   Root      invisible anchored PrimaryPart; the Model's pivot is the origin, on the ground.
--   <Piece>   unanchored, massless MeshParts welded to the Root, with the skeleton's Bones inside the skin.
-- Glow pieces are Neon (Placements.Glow gives each one's colour). The import is fitted from three bones whose authored positions are known, so it may
-- come in anywhere and either way round.
local ServerStorage = game:GetService("ServerStorage")

local GuardianBuilder = {}

local ROOT_SIZE = Vector3.new(4, 1, 4)

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
