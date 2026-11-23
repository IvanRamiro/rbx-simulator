-- Builds the Twelve Stars dev stage (Studio, Edit mode; nothing here ships to players):
--
--   require(game.ServerStorage.WorldBuild.AuraStage.BuildTwelveStars:Clone()).build()
--
-- It makes ServerStorage.DevStage.AuraTwelveStars: a dark platform, two dummies (DummyWith wears the current Eternal aura plus Twelve Stars, DummyAlone the current aura alone),
-- the gem's mesh template (the PDS kit's icosphere), the module and the Script that runs it on the client. Drag the folder into Workspace and press Play. It replaces a stage
-- built before. The module and the controller are copied from their synced sources (ServerStorage.WorldBuild.AuraStage), so edit those and build again.
local ServerStorage = game:GetService("ServerStorage")

local AT = Vector3.new(500, 300, 700) -- open sky east of Murim Crossing, clear of every island

local BuildTwelveStars = {}

function BuildTwelveStars.build()
    local devStage = ServerStorage:FindFirstChild("DevStage")
    assert(devStage, "no ServerStorage.DevStage")
    local old = devStage:FindFirstChild("AuraTwelveStars")
    if old then
        old:Destroy()
    end
    local sources = ServerStorage.WorldBuild.AuraStage

    local stage = Instance.new("Folder")
    stage.Name = "AuraTwelveStars"
    stage:SetAttribute("Shape", 0)
    stage:SetAttribute("Reduced", false)
    stage:SetAttribute("Low", false)
    stage:SetAttribute("Sky", true)
    stage:SetAttribute("Sounds", true)
    stage:SetAttribute("Speed", 1)

    local platform = Instance.new("Part")
    platform.Name = "Platform"
    platform.Size = Vector3.new(90, 2, 50)
    platform.Anchored = true
    platform.Material = Enum.Material.SmoothPlastic
    platform.Color = Color3.fromRGB(22, 26, 44)
    platform.CFrame = CFrame.new(AT - Vector3.new(0, 4, 0))
    platform.Parent = stage

    -- the dummies: the range's Eternal dummy, cleaned (no preview copy of a unique piece, no tier attributes, no scripts: RealmAura is called by the controller)
    local template = devStage.AuraTestRange.Tier12
    for i, name in { "DummyWith", "DummyAlone" } do
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
        dummy.Parent = stage
        dummy:PivotTo(CFrame.new(AT + Vector3.new(if i == 1 then -9 else 9, 0, 0)))
    end

    -- the twelfth star's gem: the PDS kit's icosphere (the module sets its size, glass material and colour)
    local kit = devStage["PDS' Particles & Models Kit"]["PDS Models Pack for BSED:R"].Meshes
    local gem = kit.Icosphere:Clone()
    gem.Name = "GemTemplate"
    gem.Anchored = true
    gem.Transparency = 1
    gem.CFrame = CFrame.new(AT + Vector3.new(0, -20, 0))
    gem.Parent = stage

    local module = Instance.new("ModuleScript")
    module.Name = "TwelveStars"
    module.Source = sources.TwelveStars.Source
    module.Parent = stage
    local controller = Instance.new("Script")
    controller.Name = "TwelveStarsStage"
    controller.RunContext = Enum.RunContext.Client
    controller.Source = sources.TwelveStarsStage.Source
    controller.Parent = stage

    stage.Parent = devStage
    return stage:GetFullName()
end

return BuildTwelveStars
