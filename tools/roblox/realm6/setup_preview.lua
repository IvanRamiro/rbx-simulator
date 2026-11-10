-- Realm 6 (Immortal): the workbench preview. Run in Studio's command bar (Edit) once, after the build_*.lua scripts. It puts
-- a client Script, Realm6AuraPreview, on the AuraWorkbench that in Play starts Realm6Motion (the vortex comets) and, when
-- the workbench's attributes Realm6ShowWings / Realm6ShowHalos are true, the wings and the halos.
-- The Studio-built Beams and emitters show on their own, in Edit too. Drag AuraWorkbench from ServerStorage.DevStage to
-- Workspace to use it, and back afterwards.
local ServerStorage = game:GetService("ServerStorage")
local bench = workspace:FindFirstChild("AuraWorkbench") or ServerStorage.DevStage.AuraWorkbench
local old = bench:FindFirstChild("Realm6AuraPreview")
if old then
	old:Destroy()
end
local s = Instance.new("Script")
s.Name = "Realm6AuraPreview"
s.RunContext = Enum.RunContext.Client
s.Source = [[
-- Studio only: the Realm 6 aura on this workbench's dummy in Play (tools/roblox/realm6/setup_preview.lua made this).
local Players = game:GetService("Players")

local player = Players.LocalPlayer
local auras = player:WaitForChild("PlayerScripts"):WaitForChild("Auras")
local dummy = script.Parent:WaitForChild("AuraDummy")
dummy:WaitForChild("UpperTorso", 10)
dummy:WaitForChild("Head", 10)

local handles = {}
-- the wings and halos (runtime pieces) only when the workbench asks for them: attributes Realm6ShowWings, Realm6ShowHalos
local show = { Realm6Wings = script.Parent:GetAttribute("Realm6ShowWings") == true, Realm6Halos = script.Parent:GetAttribute("Realm6ShowHalos") == true }
for _, name in { "Realm6Wings", "Realm6Halos" } do
	local module = auras:FindFirstChild(name)
	if module and show[name] then
		table.insert(handles, { kind = "aura", handle = require(module).attach(dummy, { isLocal = true }) })
	end
end
local motion = auras:FindFirstChild("Realm6Motion")
if motion then
	table.insert(handles, { kind = "motion", handle = require(motion).start(dummy, { isLocal = true }) })
end
script.Destroying:Connect(function()
	for _, h in handles do
		if h.handle then
			if h.kind == "aura" then
				h.handle.destroyNow()
			else
				h.handle.stop()
			end
		end
	end
end)
]]
s.Parent = bench
if bench:GetAttribute("Realm6ShowWings") == nil then
	bench:SetAttribute("Realm6ShowWings", false)
end
if bench:GetAttribute("Realm6ShowHalos") == nil then
	bench:SetAttribute("Realm6ShowHalos", false)
end
print("Realm6AuraPreview set up on " .. bench:GetFullName())
