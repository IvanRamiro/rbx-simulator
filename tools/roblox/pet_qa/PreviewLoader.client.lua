-- QA HARNESS for the exclusive beasts' rigs (kept here, outside src, so Rojo does not sync it). Copy it, with the preview data modules the rig scripts write (src/client/Pets/_Preview/<PetId>Data.lua), into src/client/Pets/_Preview/ (never commit them there).
-- the exclusive beasts remade as skinned rigs can't be seen in Studio before the owner imports their FBX, and
-- an EditableMesh can't be made on a client here (its memory budget is zero), so this stands in for the import:
--   1. PetPreview = "EclipseDreadwing,Crysalith" (an attribute the client sets on its player) swaps this client's copy of the template for a
--      skeleton-only one built from the Blender export (the Bones with their rest heads; one invisible box per piece so the model's box, and with it
--      its scale, are the real model's). The real PetModels / PetRig / PetCompanionController path then runs on it.
--   2. PetPoints = "<PetId>" draws that beast's vertices (about 3000 coloured points, linear-blend skinned from the live bones each frame, the way the
--      engine would skin the mesh) over any model of that name in the workspace, so the pose of the real animation can be seen.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

if not RunService:IsStudio() then
    return
end

local player = Players.LocalPlayer
local PetModels = require(script.Parent.Parent:WaitForChild("PetModels"))
local CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
local B64 = {}
for i = 1, 64 do
    B64[string.byte(CHARS, i)] = i - 1
end

local function decode(str)
    local n = #str
    local pad = if string.sub(str, -2) == "==" then 2 elseif string.sub(str, -1) == "=" then 1 else 0
    local out = buffer.create(n // 4 * 3)
    local o = 0
    for i = 1, n, 4 do
        local a, b, c, d = string.byte(str, i, i + 3)
        local v = bit32.bor(bit32.lshift(B64[a], 18), bit32.lshift(B64[b], 12), bit32.lshift(B64[c] or 0, 6), B64[d] or 0)
        buffer.writeu8(out, o, bit32.rshift(v, 16))
        buffer.writeu8(out, o + 1, bit32.band(bit32.rshift(v, 8), 255))
        buffer.writeu8(out, o + 2, bit32.band(v, 255))
        o += 3
    end
    return out, n // 4 * 3 - pad
end

-- every piece's vertices in the game's axes, its bounding box
local decoded = {}
local function decodeData(petId)
    if decoded[petId] then
        return decoded[petId]
    end
    local data = require(script.Parent:WaitForChild(petId .. "Data"))
    local info = { data = data, pieces = {}, lo = Vector3.one * -0.025, hi = Vector3.one * 0.025 }
    for _, piece in data.Pieces do
        local verts = decode(piece.Verts)
        local n = buffer.len(verts) // 12
        local pos = table.create(n)
        local lo, hi = Vector3.one * math.huge, Vector3.one * -math.huge
        for i = 0, n - 1 do
            local v = Vector3.new(buffer.readf32(verts, i * 12), buffer.readf32(verts, i * 12 + 4), buffer.readf32(verts, i * 12 + 8))
            pos[i + 1] = v
            lo = lo:Min(v)
            hi = hi:Max(v)
        end
        table.insert(info.pieces, { piece = piece, pos = pos, lo = lo, hi = hi, n = n })
        info.lo = info.lo:Min(lo)
        info.hi = info.hi:Max(hi)
    end
    info.centre = (info.lo + info.hi) / 2
    decoded[petId] = info
    return info
end

local function buildTemplate(petId)
    local info = decodeData(petId)
    local model = Instance.new("Model")
    model.Name = petId
    local holder = Instance.new("Part")
    holder.Name = "RootPart"
    holder.Size = Vector3.one * 0.05
    holder.Anchored = true
    holder.CanCollide = false
    holder.CFrame = CFrame.new(0, 0, 0)
    holder.Parent = model
    model.PrimaryPart = holder
    local byName, instances = {}, {}
    for _, b in info.data.Bones do
        byName[b[1]] = Vector3.new(b[3], b[4], b[5])
    end
    for _, b in info.data.Bones do
        local bone = Instance.new("Bone")
        bone.Name = b[1]
        local parentPos = if b[2] == "" then Vector3.zero else byName[b[2]]
        bone.CFrame = CFrame.new(byName[b[1]] - parentPos)
        bone.Parent = if b[2] == "" then holder else instances[b[2]]
        instances[b[1]] = bone
    end
    for _, p in info.pieces do
        local box = Instance.new("Part")
        box.Name = p.piece.Name
        box.Anchored = false
        box.CanCollide = false
        box.Transparency = 1
        box.Size = (p.hi - p.lo):Max(Vector3.one * 0.01)
        box.CFrame = CFrame.new((p.lo + p.hi) / 2)
        box.Parent = model
    end
    return model
end

local built = {}
local function apply(petId)
    if built[petId] then
        return
    end
    built[petId] = true
    local ok, result = pcall(function()
        local template = buildTemplate(petId)
        local folder = ReplicatedStorage:WaitForChild("PetMeshes")
        local old = folder:FindFirstChild(petId, true)
        local parent = if old then old.Parent else folder
        if old then
            old:Destroy()
        end
        template.Parent = parent
    end)
    if not ok then
        built[petId] = nil
        warn("PreviewLoader: " .. petId .. " failed: " .. tostring(result))
    else
        player:SetAttribute("PetPreviewDone", (player:GetAttribute("PetPreviewDone") or "") .. petId .. ",")
    end
end

local function onPreview()
    local list = player:GetAttribute("PetPreview")
    if typeof(list) == "string" then
        for _, petId in string.split(list, ",") do
            if petId ~= "" then
                task.spawn(apply, petId)
            end
        end
    end
end
player:GetAttributeChangedSignal("PetPreview"):Connect(onPreview)
onPreview()

-- ---------- the skinned points ----------
local MAX_POINTS = 3200
local overlays = {} -- [model] = { petId, rig, bones = { [i] = Bone }, boneNames, parts, cframes, verts = { { v, i1..i4, w1..w4, part } } }
local folder = Instance.new("Folder")
folder.Name = "QAPoints"
folder.Parent = workspace

local function attach(model, petId)
    local rig = PetModels.getRig(model)
    if not rig or not rig.restCF then
        return
    end
    local info = decodeData(petId)
    local boneNames, boneIndex = {}, {}
    for i, b in info.data.Bones do
        boneNames[i] = b[1]
        boneIndex[b[1]] = i
    end
    local bones = {}
    for _, d in model:GetDescendants() do
        if d:IsA("Bone") then
            bones[boneIndex[d.Name]] = d
        end
    end
    local total = 0
    for _, p in info.pieces do
        total += p.n
    end
    local stride = math.max(1, math.ceil(total / MAX_POINTS))
    local scale = rig.meters
    local pts, parts, cframes = {}, {}, {}
    local size = 0.13 * scale / 4.8
    for _, p in info.pieces do
        local idx, wts, cols = decode(p.piece.BoneIdx), decode(p.piece.Wts), decode(p.piece.Cols)
        for i = 1, p.n, stride do
            local bind = (p.pos[i] - info.centre) * scale
            local part = Instance.new("Part")
            part.Size = Vector3.one * (if p.piece.Glow then size * 1.6 else size)
            part.Anchored = true
            part.CanCollide = false
            part.CanQuery = false
            part.CanTouch = false
            part.CastShadow = false
            part.Material = Enum.Material.Neon
            local base = Color3.fromRGB(buffer.readu8(cols, (i - 1) * 3), buffer.readu8(cols, (i - 1) * 3 + 1), buffer.readu8(cols, (i - 1) * 3 + 2))
            local h, sat, val = base:ToHSV()
            part.Color = if p.piece.Glow then Color3.fromHex(p.piece.Glow) else Color3.fromHSV(h, math.min(1, sat * 1.1), math.clamp(val * 2.5 + 0.18, 0.2, 1))
            part.Parent = folder
            local entry = { bind = bind, part = part }
            for k = 0, 3 do
                entry[k * 2 + 1] = buffer.readu8(idx, (i - 1) * 4 + k) + 1
                entry[k * 2 + 2] = buffer.readu8(wts, (i - 1) * 4 + k) / 255
            end
            table.insert(pts, entry)
            table.insert(parts, part)
        end
    end
    overlays[model] = { petId = petId, rig = rig, bones = bones, boneNames = boneNames, pts = pts, parts = parts, cframes = table.create(#parts), skin = table.create(#boneNames) }
    model.Destroying:Once(function()
        local o = overlays[model]
        overlays[model] = nil
        if o then
            for _, part in o.parts do
                part:Destroy()
            end
        end
    end)
end

local function sweep()
    local petId = player:GetAttribute("PetPoints")
    if typeof(petId) ~= "string" or petId == "" then
        for model in overlays do
            local o = overlays[model]
            overlays[model] = nil
            for _, part in o.parts do
                part:Destroy()
            end
        end
        return
    end
    for _, container in { workspace, workspace:FindFirstChild("PetCompanions") } do
        local model = container and container:FindFirstChild(petId)
        if model and model:IsA("Model") and not overlays[model] then
            attach(model, petId)
            for _, d in model:GetDescendants() do -- (the real model has no mesh in the preview; hide nothing)
                if d:IsA("BasePart") then
                    d.Transparency = 1
                end
            end
        end
    end
end

local lastSweep = 0
RunService.RenderStepped:Connect(function()
    local now = os.clock()
    if now - lastSweep > 0.5 then
        lastSweep = now
        sweep()
    end
    for model, o in overlays do
        local root = o.rig.rootPart
        local rootCF = root.CFrame
        local skin = o.skin
        for i, bone in o.bones do
            local rest = rootCF * o.rig.restCF[o.boneNames[i]]
            skin[i] = bone.TransformedWorldCFrame * rest:Inverse()
        end
        local cframes = o.cframes
        for n, e in o.pts do
            local v = rootCF * e.bind
            local acc = Vector3.zero
            local wsum = 0
            for k = 0, 3 do
                local w = e[k * 2 + 2]
                if w > 0 then
                    acc += skin[e[k * 2 + 1]] * v * w
                    wsum += w
                end
            end
            cframes[n] = CFrame.new(if wsum > 0 then acc / wsum else v)
        end
        workspace:BulkMoveTo(o.parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)
    end
end)
