-- Builds the Black Tempest dev stage (Studio, Edit mode; nothing here ships to players):
--
--   require(game.ServerStorage.WorldBuild.AuraStage.BuildBlackTempest:Clone()).build()
--
-- It makes ServerStorage.DevStage.AuraBlackTempest: a big dark platform, DummyAura in the middle (the aura alone, no realm aura under it), DummyWitness 35 studs away, the module and the
-- Script that runs it on the client. Drag the folder into Workspace and press Play. It replaces a stage built before; the module and the controller are copied from their synced
-- sources (ServerStorage.WorldBuild.AuraStage), so edit those and build again.
local ServerStorage = game:GetService("ServerStorage")

local AT = Vector3.new(500, 300, 700) -- open sky east of Murim Crossing, clear of every island

local BuildBlackTempest = {}

function BuildBlackTempest.build()
    local devStage = ServerStorage:FindFirstChild("DevStage")
    assert(devStage, "no ServerStorage.DevStage")
    local old = devStage:FindFirstChild("AuraBlackTempest")
    if old then
        old:Destroy()
    end
    local sources = ServerStorage.WorldBuild.AuraStage

    local stage = Instance.new("Folder")
    stage.Name = "AuraBlackTempest"
    for name, value in { Reduced = false, Low = false, Sounds = true, Grade = true, Shake = true, Speed = 1, Scale = 1, Gap = 16, Eyes = true, Awaken = false, Surge = false } do
        stage:SetAttribute(name, value)
    end

    local platform = Instance.new("Part")
    platform.Name = "Platform"
    platform.Size = Vector3.new(170, 2, 170)
    platform.Anchored = true
    platform.Material = Enum.Material.Slate
    platform.Color = Color3.fromRGB(58, 54, 60)
    platform.CFrame = CFrame.new(AT - Vector3.new(0, 4, 0))
    platform.Parent = stage

    local template = devStage.AuraTestRange.Tier12
    for _, entry in { { "DummyAura", Vector3.new(0, 0, 0) }, { "DummyWitness", Vector3.new(35, 0, 12) } } do
        local dummy = template:Clone()
        dummy.Name = entry[1]
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
        dummy.Parent = stage
        dummy:PivotTo(CFrame.new(AT + entry[2]))
    end

    local module = Instance.new("ModuleScript")
    module.Name = "BlackTempest"
    module.Source = sources.BlackTempest.Source
    module.Parent = stage
    local controller = Instance.new("Script")
    controller.Name = "BlackTempestStage"
    controller.RunContext = Enum.RunContext.Client
    controller.Source = sources.BlackTempestStage.Source
    controller.Parent = stage

    stage.Parent = devStage
    return stage:GetFullName()
end

return BuildBlackTempest
