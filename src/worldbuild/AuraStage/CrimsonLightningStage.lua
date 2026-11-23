-- OBSOLETE since 2026-11-23 (RealmAura now builds Realm 7's lightning itself: LightningCorona; on this stage the right dummy would get it twice). Kept as the record of the comparison.
-- The Crimson Lightning comparison stage controller (Studio only; copied into a Script with RunContext = Client inside ServerStorage.DevStage.AuraCrimsonLightning by BuildCrimsonLightning).
-- Drag the stage into Workspace, press Play and stand within about 60 studs. LEFT dummy: Realm 7 (Divine) exactly as the game has it (RealmAura, tier 7, level 5, with its current unique
-- piece). RIGHT dummy: the same Realm 7 with its unique piece taken off and Crimson Lightning in its place.
-- Attributes on the stage folder (changing one restarts the right dummy's lightning): Reduced (Reduced Effects), Low (the phone tier), Speed (below 1: slow motion), Scale, Thickness.
local Players = game:GetService("Players")

local player = Players.LocalPlayer
local stage = script.Parent
local CrimsonLightning = require(stage:WaitForChild("CrimsonLightning"))
local RealmAura = require(player:WaitForChild("PlayerScripts"):WaitForChild("Auras"):WaitForChild("RealmAura"))

local current = stage:WaitForChild("DummyCurrent")
local candidate = stage:WaitForChild("DummyNew")
RealmAura.build(current:WaitForChild("HumanoidRootPart"), 7, 5)
RealmAura.build(candidate:WaitForChild("HumanoidRootPart"), 7, 5) -- (its empty "Unique" model keeps RealmAura from adding the old piece)

local handle
local function run()
    if handle then
        handle.destroy()
    end
    handle = CrimsonLightning.start(candidate.HumanoidRootPart, {
        Reduced = stage:GetAttribute("Reduced") == true,
        Low = stage:GetAttribute("Low") == true,
        Speed = stage:GetAttribute("Speed") or 1,
        Scale = stage:GetAttribute("Scale") or 1,
        Thickness = stage:GetAttribute("Thickness") or 1,
    })
end
run()
stage.AttributeChanged:Connect(run)
