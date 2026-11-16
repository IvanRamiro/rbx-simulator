-- Builds the aura comparison stage, Workspace.AuraCompare (run in Studio's command bar, in Edit).
-- A marble platform floating 110 studs east of the hub's edge at the hub's ground height (centre
-- 440, 200, 0: open sky to the east, the hub and its tree to the west), two R15 dummies 14 studs
-- apart facing east (cloned from DevStage.AuraTestRange.Tier01, which joins with AnimationConstraints
-- like players' rigs), and a sign over each. Seen from the front (from the east), LIVE is on the left
-- and NEW on the right. AuraCompare.client.lua (beside this file; a template copied into src/client/Auras/Candidates/ for a comparison) dresses and poses them in
-- Play, in Studio only. Delete the model to take the stage away.
local CENTRE = Vector3.new(440, 200, 0) -- the platform's top, centre
local GAP = 14

local old = workspace:FindFirstChild("AuraCompare")
if old then
    old:Destroy()
end
local stage = Instance.new("Model")
stage.Name = "AuraCompare"
stage.ModelStreamingMode = Enum.ModelStreamingMode.Persistent
stage:SetAttribute("SubRank", 3)
stage:SetAttribute("TimeScale", 1)
stage:SetAttribute("Facing", 0)
stage:SetAttribute("View", 0)

local platform = Instance.new("Part")
platform.Name = "Platform"
platform.Shape = Enum.PartType.Cylinder
platform.Size = Vector3.new(2, 40, 40)
platform.CFrame = CFrame.new(CENTRE - Vector3.new(0, 1, 0)) * CFrame.Angles(0, 0, math.rad(90))
platform.Anchored = true
platform.Material = Enum.Material.Marble
platform.Color = Color3.fromRGB(122, 126, 136) -- a mid-grey marble: a white floor hides every additive ground layer
platform.TopSurface, platform.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
platform.Parent = stage
-- (the cylinder's axis is its X: turned 90 degrees about Z it stands upright, its top facing up)

local template = game:GetService("ServerStorage").DevStage.AuraTestRange.Tier01
local function dummy(name, z, label)
    local d = template:Clone()
    d.Name = name
    for _, child in d:GetChildren() do
        if child.Name == "Unique" or child:IsA("BaseScript") then
            child:Destroy() -- the test range's preview of the unique piece, and its Animate script
        end
    end
    for key in d:GetAttributes() do
        d:SetAttribute(key, nil)
    end
    -- a neutral grey body (the test range's are black, which flatters any glow)
    local grey = Color3.fromRGB(150, 150, 155)
    local colours = d:FindFirstChildOfClass("BodyColors")
    if colours then
        for _, prop in { "HeadColor3", "TorsoColor3", "LeftArmColor3", "RightArmColor3", "LeftLegColor3", "RightLegColor3" } do
            colours[prop] = grey
        end
    end
    for _, part in d:GetChildren() do
        if part:IsA("BasePart") and part.Name ~= "HumanoidRootPart" then
            part.Color = grey
        end
    end
    d.Parent = stage
    local root = d.HumanoidRootPart
    root.Anchored = true
    -- stand it facing east, then set its soles on the floor
    local at = CENTRE + Vector3.new(0, 3, z)
    d:PivotTo(CFrame.lookAt(at, at + Vector3.xAxis) * d:GetPivot():ToObjectSpace(root.CFrame):Inverse())
    local lowest = math.huge
    for _, part in { d.LeftFoot, d.RightFoot } do
        local cf, size = part.CFrame, part.Size
        for _, sx in { -1, 1 } do
            for _, sy in { -1, 1 } do
                for _, sz in { -1, 1 } do
                    lowest = math.min(lowest, (cf * Vector3.new(sx * size.X / 2, sy * size.Y / 2, sz * size.Z / 2)).Y)
                end
            end
        end
    end
    d:PivotTo(d:GetPivot() + Vector3.new(0, CENTRE.Y - lowest, 0))

    local sign = Instance.new("Part")
    sign.Name = "Sign"
    sign.Anchored, sign.CanCollide, sign.CanQuery, sign.CanTouch, sign.CastShadow = true, false, false, false, false
    sign.Size = Vector3.new(5.4, 1.3, 0.2)
    sign.Material = Enum.Material.SmoothPlastic
    sign.Color = Color3.fromRGB(28, 34, 44)
    local signAt = CENTRE + Vector3.new(0, 10.5, z)
    sign.CFrame = CFrame.lookAt(signAt, signAt + Vector3.xAxis) -- its front face looks east, at the viewer
    local gui = Instance.new("SurfaceGui")
    gui.Face = Enum.NormalId.Front
    gui.LightInfluence = 0
    gui.CanvasSize = Vector2.new(540, 130)
    local text = Instance.new("TextLabel")
    text.BackgroundTransparency = 1
    text.Size = UDim2.fromScale(1, 1)
    text.Font = Enum.Font.GothamBold
    text.TextScaled = true
    text.TextColor3 = Color3.fromRGB(235, 240, 245)
    text.Text = label
    text.Parent = gui
    gui.Parent = sign
    sign.Parent = stage
    return d
end
-- seen from the east (the front), +Z is on the left
dummy("LiveDummy", GAP / 2, "LIVE: Realm 1")
dummy("NewDummy", -GAP / 2, "NEW: Realm 1")
stage.PrimaryPart = platform
stage.Parent = workspace
print("AuraCompare stage at", CENTRE)
