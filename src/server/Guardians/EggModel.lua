-- A loose egg model (on a stand, carried, dropped or hatching), built from its mesh in
-- ServerStorage.EggMeshes (stored by WorldBuilder.storeEgg). Parts are welded to the body ("Egg",
-- the PrimaryPart); glow pieces are Neon in their exported colour, as on the stands.
--
--   EggModel.build(eggId, height)  a Model `height` studs tall, its pivot at the egg's centre;
--                                  every part non-colliding, unanchored and massless.
local ServerStorage = game:GetService("ServerStorage")

local EggModel = {}

function EggModel.build(eggId, height)
    local folder = ServerStorage:FindFirstChild("EggMeshes")
    local source = folder and folder:FindFirstChild(eggId)
    assert(source and source:IsA("Model"), "missing egg mesh ServerStorage.EggMeshes." .. eggId)
    local boxCFrame, boxSize = source:GetBoundingBox()
    local scale = height / boxSize.Y

    local model = Instance.new("Model")
    model.Name = eggId
    local body
    local parts = {}
    for _, original in source:GetDescendants() do
        if original:IsA("BasePart") then
            local part = original:Clone()
            local hex = string.match(original.Name, "_Glow_(%x%x%x%x%x%x)$")
            for _, child in part:GetChildren() do
                if hex or not child:IsA("SurfaceAppearance") then
                    child:Destroy()
                end
            end
            if hex then
                part.Color = Color3.fromHex(hex)
                part.Material = Enum.Material.Neon
                if part:IsA("MeshPart") then
                    part.TextureID = ""
                end
            end
            local relative = boxCFrame:ToObjectSpace(original.CFrame)
            part.Size = original.Size * scale
            part.CFrame = relative.Rotation + relative.Position * scale
            part.Anchored = false
            part.CanCollide = false
            part.CanQuery = false
            part.CanTouch = false
            part.Massless = true
            part.CastShadow = not hex
            part.Parent = model
            table.insert(parts, part)
            if not hex and (not body or original.Name == eggId .. "_Body") then
                body = part
            end
        end
    end
    body.Name = "Egg"
    model.PrimaryPart = body
    for _, part in parts do
        if part ~= body then
            local weld = Instance.new("Weld")
            weld.Part0, weld.Part1 = body, part
            weld.C0 = body.CFrame:ToObjectSpace(part.CFrame)
            weld.Parent = part
        end
    end
    -- the pivot stays at the egg's centre wherever the body's own centre is
    body.PivotOffset = body.CFrame:Inverse()
    return model
end

return EggModel
