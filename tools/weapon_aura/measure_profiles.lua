-- Measures every realm weapon's blade / spearhead silhouette (run in Studio's command bar or through
-- execute_luau in Edit mode; it only reads ServerStorage.Weapons and parks temporary clones high above
-- the map, which it deletes). Weapon space: the point runs along -Z; Hilt and Tip are the blade's foot
-- and point (weapon attributes), so only the steel between them is measured: no guard, grip or plume.
-- For each of 14 stations along the steel (COUNT, from where START says it begins) it casts rays across the weapon in X and in Y (against the
-- weapon's own parts) and reports the centre line and half-width / half-thickness of the metal there.
-- Output: the rows of the P.Measured table in src/client/Combat/WeaponAuraProfiles.lua ({ z, cx, cy, halfWidth, halfThick }).
-- where the steel starts (t = 0 is the Hilt, the blade's foot), judged from the models: below it come
-- the guard's collar, the reed's sheaths, a spear's socket. Parts: which pieces count as steel (default Body).
local START = { Sword1 = 0.2, Sword2 = 0.12, Sword3 = 0.12, Sword4 = 0.1, Sword5 = 0.04, Sword6 = 0.12, Sword7 = 0.12,
    Sword8 = 0.06, Sword9 = 0.06, Sword10 = 0.12, Sword11 = 0.08, Sword12 = 0.12,
    Spear1 = 0.08, Spear2 = 0.3, Spear3 = 0.3, Spear4 = 0.1, Spear5 = 0.12, Spear6 = 0.1, Spear7 = 0.12, Spear8 = 0.06,
    Spear9 = 0.1, Spear10 = 0.12, Spear11 = 0.08, Spear12 = 0.12 }
local PARTS = { Spear1 = { Glow = true } }
local COUNT = 14
local STEP = 0.04
local ORIGIN = CFrame.new(0, 3000, 0)

local function measure(source)
    local model = Instance.new("Model")
    local parts = {}
    local only = PARTS[source.Name] or { Body = true }
    for _, piece in source:GetChildren() do
      if only[piece.Name] then
        local part = piece:Clone()
        part.Anchored = true
        part.CanQuery = true
        part.CFrame = ORIGIN * piece:GetAttribute("Offset")
        part.Parent = workspace
        table.insert(parts, part)
      end
    end
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Include
    params.FilterDescendantsInstances = parts
    local hilt, tip = source:GetAttribute("Hilt"), source:GetAttribute("Tip")
    local rows = {}
    local t0 = START[source.Name]
    for k = 0, COUNT - 1 do
        local t = t0 + (0.97 - t0) * k / (COUNT - 1)
        local z = hilt.Z + (tip.Z - hilt.Z) * t
        local xmin, xmax, ymin, ymax = math.huge, -math.huge, math.huge, -math.huge
        for s = -30, 30 do
            local v = s * STEP
            -- across X at height v
            local a = workspace:Raycast(ORIGIN:PointToWorldSpace(Vector3.new(-6, v, z)), ORIGIN:VectorToWorldSpace(Vector3.new(12, 0, 0)), params)
            local b = workspace:Raycast(ORIGIN:PointToWorldSpace(Vector3.new(6, v, z)), ORIGIN:VectorToWorldSpace(Vector3.new(-12, 0, 0)), params)
            if a and b then
                xmin = math.min(xmin, ORIGIN:PointToObjectSpace(a.Position).X)
                xmax = math.max(xmax, ORIGIN:PointToObjectSpace(b.Position).X)
            end
            -- across Y at offset v in X
            local c = workspace:Raycast(ORIGIN:PointToWorldSpace(Vector3.new(v, -6, z)), ORIGIN:VectorToWorldSpace(Vector3.new(0, 12, 0)), params)
            local d = workspace:Raycast(ORIGIN:PointToWorldSpace(Vector3.new(v, 6, z)), ORIGIN:VectorToWorldSpace(Vector3.new(0, -12, 0)), params)
            if c and d then
                ymin = math.min(ymin, ORIGIN:PointToObjectSpace(c.Position).Y)
                ymax = math.max(ymax, ORIGIN:PointToObjectSpace(d.Position).Y)
            end
        end
        if xmin == math.huge then
            table.insert(rows, string.format("{ %.3f, 0, 0, 0, 0 }", z))
        else
            table.insert(rows, string.format("{ %.3f, %.3f, %.3f, %.3f, %.3f }", z, (xmin + xmax) / 2,
                (ymin == math.huge) and 0 or (ymin + ymax) / 2, (xmax - xmin) / 2, math.max(0.04, (ymin == math.huge) and 0.04 or (ymax - ymin) / 2)))
        end
    end
    for _, p in parts do p:Destroy() end
    return rows
end

local out = {}
local ids = {}
for _, w in game.ServerStorage.Weapons:GetChildren() do
    if w:GetAttribute("Kind") then table.insert(ids, w.Name) end
end
table.sort(ids, function(a, b)
    local ka, kb = a:match("^%a+"), b:match("^%a+")
    if ka ~= kb then return ka > kb end
    return tonumber(a:match("%d+")) < tonumber(b:match("%d+"))
end)
for _, id in ids do
    local w = game.ServerStorage.Weapons[id]
    local rows = measure(w)
    table.insert(out, string.format("    %s = { Start = %.2f, Tip = Vector3.new(%.3f, %.3f, %.3f), -- stations { z, cx, cy, halfWidth, halfThick }\n        %s },",
        id, START[id], w:GetAttribute("Tip").X, w:GetAttribute("Tip").Y, w:GetAttribute("Tip").Z, table.concat(rows, ",\n        ")))
end
return table.concat(out, "\n")
