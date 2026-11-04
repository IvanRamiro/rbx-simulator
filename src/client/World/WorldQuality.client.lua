-- On a phone (Quality.Low) the islands' own emitters run at a share of their rate: flames, spray, motes.
-- Eggs on their stands are left alone: EggAura sets those rates itself. With streaming on, parts arrive
-- and leave as the player moves, and a part that returns is a new instance with its full rate, so
-- every arrival is thinned once.
local Workspace = game:GetService("Workspace")

local Quality = require(script.Parent.Parent:WaitForChild("Quality"))

if not Quality.Low then
    return
end

local WORLD_RATE = 0.4
local LEFT_ALONE = { "EggStands", "EggAuras" }

local function thin(instance)
    if not instance:IsA("ParticleEmitter") then
        return
    end
    for _, name in LEFT_ALONE do
        if instance:FindFirstAncestor(name) then
            return
        end
    end
    instance.Rate *= WORLD_RATE
end

local world = Workspace:WaitForChild("FloatingIslands")
world.DescendantAdded:Connect(thin)
for _, instance in world:GetDescendants() do
    thin(instance)
end
