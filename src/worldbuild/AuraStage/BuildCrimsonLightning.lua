-- Builds the Crimson Lightning comparison stage (Studio, Edit mode; nothing here ships to players):
--
--   require(game.ServerStorage.WorldBuild.AuraStage.BuildCrimsonLightning:Clone()).build()
--
-- It makes ServerStorage.DevStage.AuraCrimsonLightning: a platform, DummyCurrent (Realm 7 as the game has it) and DummyNew (Realm 7 with its unique piece replaced by Crimson Lightning:
-- an empty "Unique" model stops RealmAura adding the old one), the module and the Script that runs it on the client. Drag it into Workspace and press Play. It replaces a stage built
-- before; the module and the controller are copied from their synced sources (ServerStorage.WorldBuild.AuraStage).
local ServerStorage = game:GetService("ServerStorage")

local AT = Vector3.new(500, 300, 700) -- open sky east of Murim Crossing, clear of every island

local BuildCrimsonLightning = {}

function BuildCrimsonLightning.build()
    local devStage = ServerStorage:FindFirstChild("DevStage")
    assert(devStage, "no ServerStorage.DevStage")
    local old = devStage:FindFirstChild("AuraCrimsonLightning")
    if old then
        old:Destroy()
    end
    local sources = ServerStorage.WorldBuild.AuraStage

    local stage = Instance.new("Folder")
    stage.Name = "AuraCrimsonLightning"
    for name, value in { Reduced = false, Low = false, Speed = 1, Scale = 1, Thickness = 1 } do
        stage:SetAttribute(name, value)
    end

    local platform = Instance.new("Part")
    platform.Name = "Platform"
    platform.Size = Vector3.new(90, 2, 50)
    platform.Anchored = true
    platform.Material = Enum.Material.SmoothPlastic
    platform.Color = Color3.fromRGB(22, 26, 44)
    platform.CFrame = CFrame.new(AT - Vector3.new(0, 4, 0))
    platform.Parent = stage

    local template = devStage.AuraTestRange.Tier12
    for i, name in { "DummyCurrent", "DummyNew" } do
        local dummy = template:Clone()
        dummy.Name = name
        for _, d in dummy:GetDescendants() do
            if d:IsA("LuaSourceContainer") then
                d:Destroy()
            end
        end
        local unique = dummy:FindFirstChild("Unique")
        if unique then
            unique:Destroy()
        end
        for k in dummy:GetAttributes() do
            dummy:SetAttribute(k, nil)
        end
        for _, d in dummy:GetDescendants() do
            if d:IsA("BasePart") then
                d.Anchored = true
            end
        end
        if name == "DummyNew" then
            local keep = Instance.new("Model") -- RealmAura keeps a dummy's own "Unique" model instead of cloning the realm's piece: an empty one means none
            keep.Name = "Unique"
            keep.Parent = dummy
        end
        dummy.Parent = stage
        dummy:PivotTo(CFrame.new(AT + Vector3.new(if i == 1 then -10 else 10, 0, 0)))
    end

    local module = Instance.new("ModuleScript")
    module.Name = "CrimsonLightning"
    module.Source = sources.CrimsonLightning.Source
    module.Parent = stage
    local controller = Instance.new("Script")
    controller.Name = "CrimsonLightningStage"
    controller.RunContext = Enum.RunContext.Client
    controller.Source = sources.CrimsonLightningStage.Source
    controller.Parent = stage

    stage.Parent = devStage
    return stage:GetFullName()
end

return BuildCrimsonLightning
