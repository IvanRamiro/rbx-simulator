-- The Black Tempest stage controller (Studio only; copied into a Script with RunContext = Client inside ServerStorage.DevStage.AuraBlackTempest by BuildBlackTempest).
-- Drag the stage into Workspace, press Play and stand within about 60 studs (the screen darkens as you get closer). The middle dummy wears the aura alone (no realm aura under it);
-- the other dummy, 35 studs away, is a witness, to show how far it reaches.
-- Attributes on the stage folder: Awaken and Surge (flip either to play it again: the awakening, or one rupture), Reduced (Reduced Effects), Low (the phone tier), Sounds, Grade (the screen
-- grade), Shake, Speed (below 1: slow motion), Scale (the radius), Gap (seconds between ruptures), Eyes. Changing any other attribute restarts it.
local stage = script.Parent
local BlackTempest = require(stage:WaitForChild("BlackTempest"))

local dummy = stage:WaitForChild("DummyAura")

local handle
local function run()
    if handle then
        handle.destroy()
    end
    handle = BlackTempest.start(dummy:WaitForChild("HumanoidRootPart"), {
        Reduced = stage:GetAttribute("Reduced") == true,
        Low = stage:GetAttribute("Low") == true,
        Sounds = stage:GetAttribute("Sounds") ~= false,
        Grade = stage:GetAttribute("Grade") ~= false,
        Shake = stage:GetAttribute("Shake") ~= false,
        Speed = stage:GetAttribute("Speed") or 1,
        Scale = stage:GetAttribute("Scale") or 1,
        Gap = stage:GetAttribute("Gap") or 16,
        Eyes = stage:GetAttribute("Eyes") ~= false,
    })
end
run()
stage.AttributeChanged:Connect(function(name)
    if name == "Awaken" then
        handle.awaken()
    elseif name == "Surge" then
        handle.surge()
    else
        run()
    end
end)
