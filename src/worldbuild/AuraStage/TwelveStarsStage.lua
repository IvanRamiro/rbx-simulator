-- The Twelve Stars stage controller (Studio only; its source is copied into a Script with RunContext = Client inside ServerStorage.DevStage.AuraTwelveStars by BuildTwelveStars).
-- Drag the stage into Workspace, press Play and stand within about 100 studs (the game's own aura culling switches other players' auras off beyond 120).
-- Left dummy: the current Eternal Transcendence aura (RealmAura, tier 12, level 5) WITH Twelve Stars on top. Right dummy: the current aura alone, to compare.
-- Attributes on the stage folder (change them while playing and it restarts): Shape (0 cycles the Ascent, the Lotus and the Gate; 1, 2, 3 hold one), Reduced (Reduced Effects),
-- Low (the phone tier), Sky (the slight sky shift), Sounds, Speed (below 1: slow motion), FaceToward (a Vector3: face a fixed point instead of the camera).
local Players = game:GetService("Players")

local player = Players.LocalPlayer
local stage = script.Parent
local TwelveStars = require(stage:WaitForChild("TwelveStars"))
local RealmAura = require(player:WaitForChild("PlayerScripts"):WaitForChild("Auras"):WaitForChild("RealmAura"))

local with = stage:WaitForChild("DummyWith")
local alone = stage:WaitForChild("DummyAlone")
RealmAura.build(with:WaitForChild("HumanoidRootPart"), 12, 5)
RealmAura.build(alone:WaitForChild("HumanoidRootPart"), 12, 5)

local handle
local function run()
    if handle then
        handle.destroy()
    end
    handle = TwelveStars.start(with.HumanoidRootPart, {
        Shape = stage:GetAttribute("Shape") or 0,
        Reduced = stage:GetAttribute("Reduced") == true,
        Low = stage:GetAttribute("Low") == true,
        Sky = stage:GetAttribute("Sky") ~= false,
        Sounds = stage:GetAttribute("Sounds") ~= false,
        Speed = stage:GetAttribute("Speed") or 1,
        FaceToward = stage:GetAttribute("FaceToward"),
        Gem = stage:FindFirstChild("GemTemplate"),
    })
end
run()
stage.AttributeChanged:Connect(run)
