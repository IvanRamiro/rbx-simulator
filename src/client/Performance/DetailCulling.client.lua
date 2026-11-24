-- Far small things are not drawn (2026-11-23, the owner's "do not sacrifice performance for decoration"). Every MeshPart of an island costs a draw call whenever it is in view,
-- and a view from the hub across to Jade Grove holds hundreds of fern, rock and lantern parts that are a few pixels wide.
--
-- HOW a part is taken out (changed 2026-11-24, measured in Studio Play with SceneDrawcallCount, four views): the first version made a far part invisible
-- (LocalTransparencyModifier = 1). That is WORSE than doing nothing: an invisible part still goes to the renderer, in the sorted transparent pass where it cannot be batched
-- (hub from behind: 3,794 draws with it, 2,130 with every part shown, 1,625 with the far parts out of the world; on the ground at the pad: 590 / 475 / 420; the high view 1,546 / 1,021 / 833).
-- So a far part is now MOVED OUT OF THE WORLD (its Parent becomes a client-only holder in ReplicatedStorage) and put back where it was when the camera comes near.
-- Nothing is changed for anyone else, nothing is destroyed.
--
-- A part is taken out once the camera is farther from it than `max(MIN_CULL, K * its longest side)`: a part about 1/K of the distance across is a few pixels, so small things go
-- first and big ones (a tree's crown, a hall, a bridge, a mountain's rock) are never taken out inside MAX_CULL. Put back a little nearer (hysteresis), so nothing flickers at the edge.
--   * K is 90 (about 10 pixels on a 1080p screen); on a phone (Quality.Low) 55.
--   * Left alone: anything that collides (CanCollide) or is something to press or click (ProximityPrompt, ClickDetector below it), anything in a Model that has a Humanoid (the people),
--     the eggs and relics, anything with the attribute "NoCull" on it or an ancestor.
--   * A few hundred parts a frame, so a whole island's worth costs a fraction of a millisecond. A part that streams in is registered as it arrives; when the server streams its
--     parent out (or destroys it) while it is in the holder, it is destroyed here too, so nothing is left behind.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Quality = require(script.Parent:WaitForChild("Quality"))

local K = if Quality.Low then 55 else 90
local MIN_CULL = 150      -- never taken out nearer than this, whatever its size
local MAX_CULL = 2400     -- a part that would only go beyond this stays (a 26-stud crown at 2,400 studs is about 10 pixels)
local HYSTERESIS = 0.92   -- put back inside this share of its distance
local PER_FRAME = 300

local EXCLUDE = { EggStands = true, Relics = true, Checkpoint = true }

local world = Workspace:WaitForChild("FloatingIslands")
local holder = Instance.new("Folder")
holder.Name = "DetailCullingHolder"
holder.Parent = ReplicatedStorage

local registry = {}   -- { part, cull, out, home } (home: the parent it goes back to, while it is out)
local known = {}      -- [part] = true, so a part is registered once (and stays so while it is out of the world)

-- the distance beyond which this part is taken out, or nil if it never is
local function cullFor(part)
    if not part:IsA("MeshPart") or part.Transparency >= 1 or part.CanCollide then
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
    if part:FindFirstChildWhichIsA("ProximityPrompt", true) or part:FindFirstChildWhichIsA("ClickDetector", true) then
        return nil
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
        table.insert(registry, { part = part, cull = cull, out = false, home = nil })
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

local function forget(index, count)
    local entry = registry[index]
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
        if entry.out then
            if part.Parent ~= holder then
                -- destroyed by the server while it was out (or moved by something else): forget it
                forget(cursor, count)
                count -= 1
            elseif not entry.home:IsDescendantOf(world) then
                -- its parent was streamed out while it was in the holder: it would never come back, so it goes too
                part:Destroy()
                forget(cursor, count)
                count -= 1
            else
                if (part.Position - at).Magnitude < entry.cull * HYSTERESIS then
                    part.Parent = entry.home
                    entry.out, entry.home = false, nil
                end
                cursor += 1
            end
        elseif not part:IsDescendantOf(world) then -- streamed out (or destroyed): forget it (an Atomic model streams out whole and
            -- its parts keep their parent, so part.Parent alone kept them listed for the session: bug audit, 2026-11-24)
            forget(cursor, count)
            count -= 1
        else
            if (part.Position - at).Magnitude > entry.cull then
                entry.home = part.Parent
                entry.out = true
                part.Parent = holder
            end
            cursor += 1
        end
    end
end)
