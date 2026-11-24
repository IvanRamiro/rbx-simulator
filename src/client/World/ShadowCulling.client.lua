-- Far shadows are not drawn (2026-11-24, the owner's "do not sacrifice performance for decoration"; the release checklist's B10).
-- Measured in Studio Play with SceneAnalysisService:GetTriangleCompositionAsync at the hub: the SHADOW pass drew 2.52M triangles in 1,375 draw calls, against 486k triangles
-- and 762 draw calls for everything the player sees (the opaque pass). (Stats.SceneDrawcallCount leaves the shadow pass out, which is why the draw-call readings of the
-- earlier DetailCulling work never showed it.) A shadow a few hundred studs away is a few pixels of a low-resolution map and nobody can tell it is missing; the cost is the
-- same as a shadow beside the player. With every part beyond 150 studs not casting: 1.10M triangles in 739 draws (56 % and 46 % less); beyond 200 studs, 1.06M in 724.
--
-- A part stops casting a shadow (CastShadow = false, on this client only: nothing is changed for anyone else) once the camera is farther from it than SHADOW_DISTANCE, and
-- casts again a little nearer (hysteresis, so nothing flickers at the edge). Left alone: the big masses (a part with a side of BIG studs or more: a mountain's, a hall's,
-- a bridge's shadow is seen from far and falls on what is near), anything with the attribute "NoCull" on it or an ancestor, and anything that never cast (CastShadow was
-- already false). A part that leaves the world (DetailCulling takes far small ones out, the server streams a model out) gets its shadow back at once, so nothing is ever
-- left without one when it returns. A few hundred parts a frame.
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Quality = require(script.Parent.Parent:WaitForChild("Quality"))

local SHADOW_DISTANCE = if Quality.Low then 120 else 200 -- studs from the camera
local BIG = 60          -- a part with a side this long keeps its shadow at any distance
local HYSTERESIS = 0.9  -- casts again inside this share of the distance
local PER_FRAME = 300

local world = Workspace:WaitForChild("FloatingIslands")
local registry = {}   -- { part, off }
local known = {}      -- [part] = true

local function register(part)
    if known[part] or not part:IsA("BasePart") or not part.CastShadow or part.Transparency >= 1 then
        return
    end
    if math.max(part.Size.X, part.Size.Y, part.Size.Z) >= BIG then
        return
    end
    local ancestor = part
    while ancestor and ancestor ~= world do
        if ancestor:GetAttribute("NoCull") or ancestor:FindFirstChildOfClass("Humanoid") then
            return
        end
        ancestor = ancestor.Parent
    end
    known[part] = true
    table.insert(registry, { part = part, off = false })
end

for _, d in world:GetDescendants() do
    register(d)
end
world.DescendantAdded:Connect(function(d)
    if d:IsA("BasePart") then
        task.defer(register, d) -- (after the rest of what arrived with it has its parent and size)
    end
end)

local function forget(index, count)
    local entry = registry[index]
    if entry.off then
        entry.part.CastShadow = true -- (it left the world with its shadow off: it must have it when it comes back)
    end
    known[entry.part] = nil
    registry[index] = registry[count]
    registry[count] = nil
end

local cursor = 1
RunService.Heartbeat:Connect(function()
    local camera = Workspace.CurrentCamera
    local count = #registry
    if not camera or count == 0 then
        return
    end
    local at = camera.CFrame.Position
    for _ = 1, math.min(count, PER_FRAME) do
        if count == 0 then
            return
        end
        if cursor > count then
            cursor = 1
        end
        local entry = registry[cursor]
        local part = entry.part
        if not part:IsDescendantOf(world) then
            forget(cursor, count)
            count -= 1
        else
            local distance = (part.Position - at).Magnitude
            if entry.off then
                if distance < SHADOW_DISTANCE * HYSTERESIS then
                    part.CastShadow = true
                    entry.off = false
                end
            elseif distance > SHADOW_DISTANCE then
                part.CastShadow = false
                entry.off = true
            end
            cursor += 1
        end
    end
end)
