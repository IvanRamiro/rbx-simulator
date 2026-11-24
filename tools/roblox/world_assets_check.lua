-- The unique-asset check (the owner, 2026-11-22: "every map must have its own dedicated asset collection ... I do not want shared environment assets
-- between maps"). Run in Studio Edit mode with execute_luau (paste this file's body). It reads ServerStorage.WorldAssets and Workspace.FloatingIslands and
-- reports, per map: how many templates it owns, and which of them are trees, rocks and plants (by name); then FAILS on
--   1. a MeshId that two maps' template folders both hold (a shared model), and
--   2. a placed MeshPart on a map whose MeshId belongs to another map's templates (a borrowed model).
-- NpcAssets (people, not environment) and the bridge kits are not environment dressing and are not counted as other maps' assets.
-- Returns a table: { Maps = {...}, Shared = {...}, Borrowed = { ["<Island> uses <Map>"] = count }, Pass = bool }.
local ServerStorage = game:GetService("ServerStorage")

local ISLAND_KITS = { -- the kits an island may place from
    Yggdrasil = { "YggdrasilAssets" },
    BeginnerIsle = { "BeginnerIslandAssets" },
    JadeGrove = { "JadeGroveAssets" },
    EmberPeak = { "EmberPeakAssets" },
    MoonlitIsle = { "MoonlitIsleAssets" },
    OriginAbyss = { "OriginAbyssAssets" },
    BlossomSanctuary = { "BlossomSanctuaryAssets" },
    MurimCrossing = { "DawnspireAssets", "WindriftAssets", "NightfallAssets", "TrialAssets" }, -- (TrialAssets: the trial props, the gate, the token and the dummy, belong to Murim Crossing alone)
}
local CATEGORY = { -- by template name (a lowercase substring), for the per-map counts
    Trees = { "tree", "pine", "bamboo", "thorn", "willow", "grove" },
    Rocks = { "rock", "stone", "basalt", "outcrop", "obsidian", "slate", "boulder", "crag", "formation", "monolith", "shard" },
    Plants = { "fern", "flower", "lily", "reed", "moss", "mushroom", "bush", "shrub", "grass", "vine", "plantain", "herb" },
}

local root = ServerStorage:FindFirstChild("WorldAssets")
if not root then
    return { Pass = false, Error = "no ServerStorage.WorldAssets" }
end

-- every template folder: name -> folder (the Murim territories sit one level down)
local kits = {}
for _, child in root:GetChildren() do
    if child.Name == "MurimAssets" then
        for _, territory in child:GetChildren() do
            kits[territory.Name] = territory
        end
    elseif child.Name ~= "NpcAssets" then
        kits[child.Name] = child
    end
end

local out = { Maps = {}, Shared = {}, Borrowed = {} }
local owner = {} -- MeshId -> kit name
local function category(name)
    local lower = string.lower(name)
    for cat, words in CATEGORY do
        for _, word in words do
            if string.find(lower, word, 1, true) then
                return cat
            end
        end
    end
    return "Other"
end
for kitName, folder in kits do
    local base, counts = {}, { Trees = {}, Rocks = {}, Plants = {}, Other = {} }
    for _, template in folder:GetChildren() do
        if template:IsA("MeshPart") then
            local piece = string.gsub(template.Name, "__.*$", "")
            piece = string.gsub(piece, "_%d+$", "")
            base[piece] = true
            counts[category(piece)][piece] = true
            local id = template.MeshId
            if owner[id] and owner[id] ~= kitName then
                out.Shared[#out.Shared + 1] = id .. ": " .. owner[id] .. " and " .. kitName
            end
            owner[id] = kitName
        end
    end
    local function size(set)
        local n = 0
        for _ in set do
            n += 1
        end
        return n
    end
    out.Maps[kitName] = { Templates = #folder:GetChildren(), Pieces = size(base), Trees = size(counts.Trees), Rocks = size(counts.Rocks), Plants = size(counts.Plants) }
end

local islands = workspace:FindFirstChild("FloatingIslands")
for islandName, allowed in ISLAND_KITS do
    local island = islands and islands:FindFirstChild(islandName)
    if island then
        local ok = {}
        for _, name in allowed do
            ok[name] = true
        end
        for _, d in island:GetDescendants() do
            if d:IsA("MeshPart") and owner[d.MeshId] and not ok[owner[d.MeshId]] then
                local key = islandName .. " uses " .. owner[d.MeshId]
                out.Borrowed[key] = (out.Borrowed[key] or 0) + 1
            end
        end
    end
end

out.Pass = #out.Shared == 0 and next(out.Borrowed) == nil
return out
