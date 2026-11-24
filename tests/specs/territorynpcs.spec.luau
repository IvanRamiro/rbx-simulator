-- The 30 territory people's data (src/worldbuild/Placements/TerritoryNpcs.lua): who stands where, how each is dressed, what each says. Data only: the
-- builder (TerritoryNpcBuilder) needs Studio and is looked at there.
local t = require("@env/t")
local Data = require("@shared/TerritoryNpcs")

-- the markers of each territory's Spots folder that are NPC places (Placements/Murim*.lua), as the proposal note lists them
local SPOTS = {
    Dawnspire = { "NpcCorridor1", "NpcCorridor2", "NpcPavilion1", "NpcPavilion2", "NpcPond", "NpcStairFoot", "NpcTea1", "NpcTea2", "NpcTea3", "NpcTea4" },
    Windrift = { "NpcHearth1", "NpcHearth2", "NpcHearth3", "NpcHearth4", "NpcHearth5", "NpcHearth6", "NpcHearth7", "NpcHearth8", "NpcHearth9", "NpcHearth10" },
    Nightfall = { "Npc1", "Npc2", "Npc3", "Npc4", "Npc5", "Npc6", "Npc7", "Npc8", "Npc9", "Npc10" },
}

-- words no line may use: nothing here hints at the game's systems (the owner's plain-words and no-hint rules)
local FORBIDDEN = { "trial", "token", "vault", "weapon", "rank", "egg", "pet", "guardian", "stone", "realm" }

local SHAPES = { Block = true, Cylinder = true, Ball = true, Wedge = true }
local MATERIALS = { Fabric = true, SmoothPlastic = true, Metal = true, Wood = true }
local FACES = { Curator = true, Forgemaster = true, Appraiser = true }

local function set(list)
    local s = {}
    for _, v in list do
        s[v] = true
    end
    return s
end

local BODY = set(Data.BodyParts)

local function validColour(c, what)
    t.ok(c ~= nil, what .. ": colour missing")
    for _, channel in { "R", "G", "B" } do
        local value = c[channel]
        t.ok(type(value) == "number" and value >= 0 and value <= 1, what .. ": colour " .. channel .. " out of range")
    end
end

local function words(text)
    local found = {}
    for word in string.gmatch(string.lower(text), "%a+") do
        found[word] = true
    end
    return found
end

t.test("exactly 30 people, 10 in each territory", function()
    t.eq(#Data.People, 30, "people")
    local count = { Dawnspire = 0, Windrift = 0, Nightfall = 0 }
    for _, p in Data.People do
        t.ok(count[p.Territory] ~= nil, tostring(p.Id) .. ": unknown territory " .. tostring(p.Territory))
        count[p.Territory] += 1
    end
    for territory, n in count do
        t.eq(n, 10, territory)
    end
end)

t.test("each territory's ten spots are exactly the marked places, one person each", function()
    for territory, names in SPOTS do
        local expected = set(names)
        local seen = {}
        for _, p in Data.People do
            if p.Territory == territory then
                t.ok(expected[p.Spot], p.Id .. ": " .. tostring(p.Spot) .. " is not a spot of " .. territory)
                t.ok(not seen[p.Spot], territory .. ": two people on " .. p.Spot)
                seen[p.Spot] = true
            end
        end
        for _, name in names do
            t.ok(seen[name], territory .. ": nobody on " .. name)
        end
    end
end)

t.test("names, ids and titles are present and unique", function()
    local names, ids = {}, {}
    for _, p in Data.People do
        t.ok(type(p.Name) == "string" and #p.Name > 0, tostring(p.Id) .. ": name")
        t.ok(type(p.Role) == "string" and #p.Role > 0, tostring(p.Name) .. ": role")
        t.ok(type(p.Id) == "string" and #p.Id > 0, tostring(p.Name) .. ": id")
        t.ok(not names[p.Name], "name twice: " .. p.Name)
        t.ok(not ids[p.Id], "id twice: " .. p.Id)
        names[p.Name], ids[p.Id] = true, true
        t.ok(not string.find(p.Id, "[^%w]"), p.Id .. ": an id is letters and digits only (it is the model's name)")
    end
end)

t.test("every person has exactly two lines, short and plain", function()
    for _, p in Data.People do
        t.eq(#p.Lines, 2, p.Name .. ": lines")
        for i, line in p.Lines do
            t.ok(type(line) == "string" and #line >= 8, p.Name .. " line " .. i .. ": empty")
            t.ok(#line <= 90, p.Name .. " line " .. i .. ": too long for one press of Talk")
        end
    end
end)

t.test("no line hints at the game's systems", function()
    for _, p in Data.People do
        for i, line in p.Lines do
            local lower = string.lower(line)
            local present = words(line)
            for _, word in FORBIDDEN do
                t.ok(not present[word], p.Name .. " line " .. i .. " uses the word '" .. word .. "'")
                -- (the longer ones also as a part of a word: "tokens", "weapons", "guardians", "vaults", "trials")
                if #word >= 5 then
                    t.ok(not string.find(lower, word, 1, true), p.Name .. " line " .. i .. " contains '" .. word .. "'")
                end
            end
        end
    end
end)

t.test("each person has a pose, a lift and body colours", function()
    for _, p in Data.People do
        t.ok(p.Pose == "Stand" or p.Pose == "Sit", p.Name .. ": pose")
        t.ok(type(p.Lift) == "number" and p.Lift >= 0 and p.Lift <= 3, p.Name .. ": lift")
        t.ok(p.Yaw == nil or (type(p.Yaw) == "number" and math.abs(p.Yaw) <= 2 * math.pi), p.Name .. ": yaw")
        for _, group in { "Head", "Torso", "Arms", "Legs" } do
            validColour(p.Colours[group], p.Name .. " " .. group)
        end
        validColour(p.Hair, p.Name .. " hair")
    end
end)

t.test("Dawnspire's ten carry the facing the note gives; the other two territories use their spots' own", function()
    local facing = {
        NpcCorridor1 = 0, NpcCorridor2 = 0, NpcPavilion1 = -0.55, NpcPavilion2 = 2.59, NpcPond = 0, NpcStairFoot = 3.14,
        NpcTea1 = 0.785, NpcTea2 = -0.785, NpcTea3 = 2.356, NpcTea4 = -2.356,
    }
    for _, p in Data.People do
        if p.Territory == "Dawnspire" then
            t.near(p.Yaw, facing[p.Spot], 1e-6, p.Name .. ": yaw")
        else
            t.eq(p.Yaw, nil, p.Name .. ": these spots already face the fire")
        end
    end
end)

t.test("seated people have seat data, standing people have none", function()
    local seated = 0
    for _, p in Data.People do
        if p.Pose == "Sit" then
            seated += 1
            t.ok(p.Seat ~= nil, p.Name .. ": seat data")
            t.ok(p.Seat.Lower >= 0.8 and p.Seat.Lower <= 1.6, p.Name .. ": seat lower " .. tostring(p.Seat.Lower))
            t.ok(p.Seat.Back >= 0 and p.Seat.Back <= 3.5, p.Name .. ": seat back " .. tostring(p.Seat.Back))
            t.ok(p.Lift > 0, p.Name .. ": a seat has a height")
        else
            t.eq(p.Seat, nil, p.Name .. ": a standing person has no seat")
        end
    end
    t.eq(seated, 12, "seated people (the note: 4 + 4 + 4)")
end)

t.test("scales are sane (the child is the smallest, nobody is more than a little broader than the tallest)", function()
    local smallest, name
    for _, p in Data.People do
        local s = p.Scale
        if s then
            t.ok(s.Height >= 0.75 and s.Height <= 1.25, p.Name .. ": height")
            t.ok(s.Width >= 0.75 and s.Width <= 1.25, p.Name .. ": width")
            t.ok(s.Head >= 0.9 and s.Head <= 1.25, p.Name .. ": head")
            if not smallest or s.Height < smallest then
                smallest, name = s.Height, p.Name
            end
        end
    end
    t.eq(name, "Tomo", "the smallest person")
    t.near(smallest, 0.8, 1e-9, "Tomo's height")
end)

t.test("every face is one of the hub's, with options that exist for it", function()
    for _, p in Data.People do
        local f = p.Face
        t.ok(FACES[f.Owner], p.Name .. ": face " .. tostring(f.Owner))
        if f.Lashes ~= nil or f.Blush ~= nil then
            t.eq(f.Owner, "Curator", p.Name .. ": lashes and blush belong to the Curator's face")
        end
        if f.Moustache then
            t.ok(f.Owner ~= "Curator", p.Name .. ": the Curator has no moustache")
            validColour(f.Moustache, p.Name .. " moustache")
        end
        if f.Beard then
            validColour(f.Beard, p.Name .. " beard")
        end
    end
end)

t.test("each person has 3 to 14 well formed plain parts", function()
    for _, p in Data.People do
        t.ok(#p.Parts >= 3 and #p.Parts <= 14, p.Name .. ": " .. #p.Parts .. " parts")
        local names = {}
        for _, part in p.Parts do
            local what = p.Name .. " " .. tostring(part.Name)
            t.ok(type(part.Name) == "string" and #part.Name > 0, what .. ": name")
            t.ok(not names[part.Name], what .. ": two parts with one name")
            names[part.Name] = true
            t.ok(SHAPES[part.Shape], what .. ": shape " .. tostring(part.Shape))
            t.ok(MATERIALS[part.Material], what .. ": material " .. tostring(part.Material))
            t.ok(BODY[part.On], what .. ": body part " .. tostring(part.On))
            validColour(part.Colour, what)
            for _, axis in { "X", "Y", "Z" } do
                t.ok(part.Size[axis] >= 0.05 and part.Size[axis] <= 10, what .. ": size " .. axis)
                t.ok(math.abs(part.Offset[axis]) <= 8, what .. ": offset " .. axis)
                if part.Turn then
                    t.ok(math.abs(part.Turn[axis]) <= 360, what .. ": turn " .. axis)
                end
            end
            if part.Shape == "Ball" then
                t.ok(part.Size.X == part.Size.Y and part.Size.Y == part.Size.Z, what .. ": a ball is round")
            end
        end
    end
end)

t.test("the stand-ins for the eight kit people exist (plain parts, no kits)", function()
    local standIns = { "JoonSeok", "ChunHo", "Kiyo", "SeokHun", "Haru", "Daichi", "Ren", "DongHyun" }
    local byId = {}
    for _, p in Data.People do
        byId[p.Id] = p
    end
    for _, id in standIns do
        t.ok(byId[id] ~= nil, id .. " is missing")
        t.ok(#byId[id].Parts >= 6, id .. ": a stand-in needs enough parts to read as the garment")
    end
end)

t.finish("territorynpcs")
