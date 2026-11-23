-- Far small things are not drawn (2026-11-23, the owner's "do not sacrifice performance for decoration"). Every MeshPart of an island costs a draw call whenever it is in view,
-- and a view from the hub across to Jade Grove holds hundreds of fern, rock and lantern parts that are a few pixels wide: measured in Studio, Jade's new library alone added
-- about 600 draw calls to the hub's view north, and hiding the parts took exactly those 555 back (a hidden part costs nothing; shadows were not the cost).
--
-- A part is hidden (LocalTransparencyModifier = 1, on this client only: nothing is changed for anyone else, nothing is destroyed, collision and queries are untouched) once the
-- camera is farther from it than `max(MIN_CULL, K * its longest side)`: a part about 1/K of the distance across is a few pixels, so small things go first and big ones (a tree's
-- crown, a hall, a bridge, a mountain's rock) are never hidden inside the streaming radius. Shown again a little nearer (hysteresis), so nothing flickers at the edge.
--   * K is 90 (about 10 pixels on a 1080p screen); on a phone (Quality.Low) 55.
--   * Left alone: anything in a Model that has a Humanoid (the people), the eggs and relics, anything with the attribute "NoCull" on it or an ancestor.
--   * A few hundred parts a frame, so a whole island's worth costs a fraction of a millisecond; parts that stream in are registered as they arrive, parts that stream out are dropped.
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Quality = require(script.Parent.Parent:WaitForChild("Quality"))

local K = if Quality.Low then 55 else 90
local MIN_CULL = 150      -- never hidden nearer than this, whatever its size
local MAX_CULL = 1200     -- a part that would only be hidden beyond this is never hidden (past the streaming radius it is not there anyway)
local HYSTERESIS = 0.92   -- shown again inside this share of its distance
local PER_FRAME = 300

local EXCLUDE = { EggStands = true, Relics = true, Checkpoint = true }

local world = Workspace:WaitForChild("FloatingIslands")
local registry = {}   -- { part, cull, hidden }
local known = {}      -- [part] = true, so a part is registered once

-- the distance beyond which this part is hidden, or nil if it never is
local function cullFor(part)
    if not part:IsA("MeshPart") or part.Transparency >= 1 then
        return nil
    end
    local cull = math.max(MIN_CULL, K * math.max(part.Size.X, part.Size.Y, part.Size.Z))
    if cull > MAX_CULL then
        return nil
    end
    local ancestor = part
    while ancestor and ancestor ~= world do
        if ancestor:GetAttribute("NoCull") or EXCLUDE[ancestor.Name] or ancestor:FindFirstChildOfClass("Humanoid") then
            return nil
        end
        ancestor = ancestor.Parent
    end
    return cull
end

local function register(part)
    if known[part] then
        return
    end
    local cull = cullFor(part)
    if cull then
        known[part] = true
        table.insert(registry, { part = part, cull = cull, hidden = false })
    end
end

for _, d in world:GetDescendants() do
    register(d)
end
world.DescendantAdded:Connect(function(d)
    if d:IsA("MeshPart") then
        task.defer(register, d) -- (after the rest of what arrived with it has its parent and size)
    end
end)

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
        if not part:IsDescendantOf(world) then -- streamed out (or destroyed): forget it (an Atomic model streams out whole and
            -- its parts keep their parent, so part.Parent alone kept them listed for the session: bug audit, 2026-11-24)
            known[part] = nil
            registry[cursor] = registry[count]
            registry[count] = nil
            count -= 1
        else
            local distance = (part.Position - at).Magnitude
            if entry.hidden then
                if distance < entry.cull * HYSTERESIS then
                    part.LocalTransparencyModifier = 0
                    entry.hidden = false
                end
            elseif distance > entry.cull then
                part.LocalTransparencyModifier = 1
                entry.hidden = true
            end
            cursor += 1
        end
    end
end)
