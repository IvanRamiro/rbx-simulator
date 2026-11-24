-- The 30 people of the three Murim territories (owner approved all 30 as written, 2026-11-24; see Claude Memory/Territory NPC Proposals 2026-11-24.md).
-- DATA ONLY, read by TerritoryNpcBuilder (Studio build) and tests/specs/territorynpcs.spec.luau (no Roblox globals here beyond Color3 and Vector3).
--
-- One row per person (People, in the note's order: Dawnspire, Windrift, Nightfall):
--   Id         the model's name and the attribute NpcId
--   Territory  "Dawnspire" | "Windrift" | "Nightfall"
--   Spot       the marker's name in that territory's Spots folder (tagged DawnspireNpcSpot / WindriftNpcSpot / NightfallNpcSpot)
--   Name, Role the name over the head is "Name, Role"
--   Yaw        radians, a turn ON TOP of the spot's own rotation. Dawnspire's ten spots have yaw 0 (the note gives each person's facing, in the pad's
--              frame: this is that number); Windrift's and Nightfall's spots already face the fire, so their rows have no Yaw.
--   Lift       studs from the spot (ground) to what the person stands or sits on: the pavilion floor (1.0) or the stool's top (1.0), a bench's top (0.5)
--   Pose       "Stand" | "Sit". The seated pose itself is NOT built here (NpcService / the client do it later); only the attribute and the placement.
--   Seat       seated people only: { Lower = studs the root drops under its standing height on that seat, Back = studs moved toward the seat, i.e.
--              away from the fire (local +Z; the person's front is -Z) }. FIRST GUESS, to be tuned in Studio: Lower from the note (1.0 to 1.3); Back is
--              the distance the note gives from the spot to the bench (2.2 to 3.2, Dawnspire's tea stools ARE the spots so 0), not the 0.3 to 0.8 a person
--              already on the seat would need.
--   Scale      optional { Height, Width, Head } (HumanoidDescription scales; dress parts follow them in the builder)
--   Colours    the four R15 colour groups { Head, Torso, Arms, Legs } (Torso also paints LowerTorso)
--   Hair       the colour of the borrowed brows (and of the hair parts)
--   Face       { Owner = "Curator" | "Forgemaster" | "Appraiser", Lashes = false, Blush = false, Beard = colour, Moustache = colour }
--              Owner: whose brows, eyes and mouth are borrowed from the hub's kit (as CrossingBuilder.wearFace does). Beard: the Forgemaster's beard
--              piece in that colour; Moustache: the owner's moustache piece (Forgemaster or Appraiser) in that colour. Curator's Lashes and Blush are on
--              unless false. The Forgemaster has no mouth piece: a beardless Forgemaster face gets a plain Mouth part below.
--   Parts      plain welded Parts, light and unable to collide: { Name, Shape, Size, Material, Colour, On, Offset, Turn }
--              Shape Block | Cylinder | Ball | Wedge; Material Fabric | SmoothPlastic | Metal | Wood; On = an R15 body part; Offset = studs in that
--              body part's frame, at scale 1; Turn = degrees (x, y, z) applied in Roblox's CFrame.Angles order; a Cylinder's long axis is X before it
--              turns (the helpers below stand it upright or lay it along Z).
--   Lines      exactly two: the first press of Talk, then the next. Plain everyday words, nothing about the game's systems.
-- Offsets were worked out from the R15 sizes CrossingBuilder.buildRep already uses (head about 1.2, torso 1.9 wide); every one is a first guess for
-- the Studio look.

local function rgb(r, g, b)
    return Color3.fromRGB(r, g, b)
end

local function v(x, y, z)
    return Vector3.new(x, y, z)
end

-- ---------- palettes (the territories' notes; the same constants as CrossingBuilder) ----------
local O_CLOTH, O_BLUE, O_GOLD = rgb(244, 246, 250), rgb(36, 78, 186), rgb(226, 176, 70)
local O_NAVY = rgb(30, 56, 140)
local U_JADE, U_COPPER, U_LINEN, U_WOOD = rgb(26, 88, 72), rgb(190, 112, 56), rgb(224, 210, 178), rgb(96, 82, 60)
local U_PATCH, U_TROUSER = rgb(58, 118, 98), rgb(50, 56, 48)
local D_BLACK, D_CRIMSON, D_IRON = rgb(24, 22, 28), rgb(176, 28, 40), rgb(46, 44, 54)
local IRON_LIGHT = rgb(96, 98, 108) -- plate that has to read against the black coat
local WOOD = rgb(132, 100, 68)
local WHITE = rgb(236, 236, 240)
local ROPE = rgb(150, 124, 86)
local STRAW = rgb(214, 186, 120)
local BRONZE = rgb(140, 100, 60)

-- ---------- part helpers ----------
local function part(name, shape, size, material, colour, on, offset, turn)
    return { Name = name, Shape = shape, Size = size, Material = material, Colour = colour, On = on, Offset = offset, Turn = turn }
end

local function block(name, size, material, colour, on, offset, turn)
    return part(name, "Block", size, material, colour, on, offset, turn)
end

local function ball(name, diameter, material, colour, on, offset)
    return part(name, "Ball", v(diameter, diameter, diameter), material, colour, on, offset, nil)
end

-- a Cylinder standing upright (its axis along Y): `length` tall
local function pole(name, length, diameter, material, colour, on, offset, tilt)
    return part(name, "Cylinder", v(length, diameter, diameter), material, colour, on, offset, v(tilt and tilt.X or 0, 0, 90 + (tilt and tilt.Z or 0)))
end

-- a Cylinder lying along Z (pointing the way the person faces)
local function lay(name, length, diameter, material, colour, on, offset)
    return part(name, "Cylinder", v(length, diameter, diameter), material, colour, on, offset, v(0, 90, 0))
end

-- a flat round disc, axis up (a hat's brim, a drum's head)
local function disc(name, thickness, diameter, material, colour, on, offset, turn)
    return part(name, "Cylinder", v(thickness, diameter, diameter), material, colour, on, offset, turn or v(0, 0, 90))
end

-- the long coat as the representatives wear it: a skirt hung from the hips (top 0.15 over the LowerTorso's centre)
local function coat(colour, length)
    length = length or 2.8
    return block("Skirt", v(2.3, length, 1.3), "Fabric", colour, "LowerTorso", v(0, 0.15 - length / 2, 0))
end

local function sash(colour, name)
    return block(name or "Sash", v(2.1, 0.45, 1.1), "Fabric", colour, "LowerTorso", v(0, 0.05, 0))
end

local function hairCap(colour)
    return block("Hair", v(1.06, 0.44, 1.06), "SmoothPlastic", colour, "Head", v(0, 0.48, 0.03))
end

local function topknot(colour)
    return ball("Topknot", 0.48, "SmoothPlastic", colour, "Head", v(0, 0.86, 0.03))
end

local function mouth()
    return block("Mouth", v(0.3, 0.06, 0.05), "SmoothPlastic", rgb(150, 70, 64), "Head", v(0, -0.26, -0.6))
end

local function beard(colour, name)
    return block(name or "Beard", v(0.8, 0.45, 0.28), "SmoothPlastic", colour, "Head", v(0, -0.42, -0.5))
end

-- a band round the head (a headband, a headscarf's edge), axis up
local function headband(colour)
    return disc("Headband", 0.25, 1.28, "Fabric", colour, "Head", v(0, 0.25, 0))
end

local SKIN = {
    Pale = rgb(246, 214, 184),
    Fair = rgb(240, 208, 178),
    Light = rgb(232, 196, 170),
    Warm = rgb(222, 180, 146),
    Tan = rgb(214, 168, 130),
    Brown = rgb(190, 140, 104),
    Red = rgb(178, 112, 88),
}

local People = {
    -- ================= Dawnspire Hall (Orthodox): the tea terrace =================
    {
        Id = "MinJun", Territory = "Dawnspire", Spot = "NpcCorridor1", Name = "Min Jun", Role = "Walk Guard",
        Yaw = 0, Lift = 0, Pose = "Stand",
        Scale = { Height = 1.08, Width = 0.95, Head = 1 },
        Colours = { Head = SKIN.Fair, Torso = O_CLOTH, Arms = O_CLOTH, Legs = O_NAVY },
        Hair = rgb(30, 28, 34), Face = { Owner = "Appraiser" },
        Parts = {
            coat(O_CLOTH),
            sash(O_BLUE),
            block("Buckle", v(0.35, 0.3, 0.12), "Metal", O_GOLD, "LowerTorso", v(0, 0.05, -0.58)),
            block("Cord", v(0.12, 0.9, 0.12), "Fabric", O_BLUE, "LowerTorso", v(0.95, -0.6, -0.5)),
            ball("Tassel", 0.26, "Fabric", O_GOLD, "LowerTorso", v(0.95, -1.15, -0.5)),
            hairCap(rgb(30, 28, 34)),
            topknot(rgb(30, 28, 34)),
            block("Pin", v(0.7, 0.08, 0.08), "Metal", O_GOLD, "Head", v(0, 0.86, 0.03)),
            pole("SpearShaft", 7.5, 0.2, "Wood", WOOD, "RightHand", v(0, 1.5, -0.1)),
            block("SpearHead", v(0.2, 0.9, 0.34), "Metal", rgb(190, 194, 204), "RightHand", v(0, 5.7, -0.1)),
        },
        Lines = { "Welcome to Dawnspire. Walk gently here, the tea is still hot.", "I guard this walk. I have never had to raise my voice." },
    },
    {
        Id = "SeoYun", Territory = "Dawnspire", Spot = "NpcCorridor2", Name = "Seo Yun", Role = "Scribe",
        Yaw = 0, Lift = 0, Pose = "Stand",
        Scale = { Height = 0.97, Width = 0.9, Head = 1 },
        Colours = { Head = SKIN.Pale, Torso = O_CLOTH, Arms = O_CLOTH, Legs = O_NAVY },
        Hair = rgb(170, 172, 180), Face = { Owner = "Curator", Lashes = false },
        Parts = {
            coat(O_CLOTH),
            sash(rgb(22, 20, 26), "Belt"),
            block("CuffL", v(1.06, 0.34, 1.06), "Fabric", O_BLUE, "LeftLowerArm", v(0, -0.3, 0)),
            block("CuffR", v(1.06, 0.34, 1.06), "Fabric", O_BLUE, "RightLowerArm", v(0, -0.3, 0)),
            hairCap(rgb(170, 172, 180)),
            ball("Bun", 0.5, "SmoothPlastic", rgb(170, 172, 180), "Head", v(0, 0.0, 0.6)),
            block("Pin", v(0.7, 0.08, 0.08), "Metal", O_GOLD, "Head", v(0, 0.0, 0.78)),
            lay("ScrollTube", 1.5, 0.32, "SmoothPlastic", rgb(226, 204, 160), "RightHand", v(0, -0.1, -0.4)),
            ball("TubeCap", 0.36, "Metal", O_GOLD, "RightHand", v(0, -0.1, -1.18)),
        },
        Lines = { "I copy the hall's rules by hand, one word at a time.", "My wrist is tired. My promise is not." },
    },
    {
        Id = "JoonSeok", Territory = "Dawnspire", Spot = "NpcPavilion1", Name = "Joon Seok", Role = "Sword Teacher",
        Yaw = -0.55, Lift = 1.0, Pose = "Stand",
        Scale = { Height = 1.04, Width = 1.12, Head = 1 },
        Colours = { Head = SKIN.Light, Torso = O_CLOTH, Arms = O_CLOTH, Legs = O_CLOTH },
        Hair = rgb(84, 82, 88), Face = { Owner = "Appraiser" },
        Parts = { -- stand-in for the scholar's robe and gat hat (kit K1 later)
            coat(O_CLOTH),
            sash(O_BLUE),
            block("SleeveL", v(1.5, 1.4, 1.3), "Fabric", O_CLOTH, "LeftLowerArm", v(0, 0.0, 0)),
            block("SleeveR", v(1.5, 1.4, 1.3), "Fabric", O_CLOTH, "RightLowerArm", v(0, 0.0, 0)),
            block("EdgeL", v(1.55, 0.2, 1.35), "Fabric", O_BLUE, "LeftLowerArm", v(0, -0.7, 0)),
            block("EdgeR", v(1.55, 0.2, 1.35), "Fabric", O_BLUE, "RightLowerArm", v(0, -0.7, 0)),
            hairCap(rgb(84, 82, 88)),
            disc("HatBrim", 0.12, 2.2, "SmoothPlastic", rgb(22, 20, 26), "Head", v(0, 0.72, 0.03)),
            pole("HatCrown", 0.9, 0.8, "SmoothPlastic", rgb(22, 20, 26), "Head", v(0, 1.2, 0.03)),
            block("PracticeSword", v(0.18, 2.6, 0.3), "Wood", WOOD, "LowerTorso", v(-1.2, -0.7, -0.2), v(0, 0, 10)),
            beard(rgb(118, 116, 120)),
        },
        Lines = { "A sword does not make a student. Patience does.", "Again. Slower." },
    },
    {
        Id = "HaEun", Territory = "Dawnspire", Spot = "NpcPavilion2", Name = "Ha Eun", Role = "Young Disciple",
        Yaw = 2.59, Lift = 1.0, Pose = "Stand",
        Scale = { Height = 0.88, Width = 0.88, Head = 1 },
        Colours = { Head = SKIN.Pale, Torso = O_CLOTH, Arms = O_CLOTH, Legs = O_NAVY },
        Hair = rgb(30, 28, 34), Face = { Owner = "Forgemaster" },
        Parts = {
            coat(O_CLOTH, 1.5),
            block("Collar", v(1.3, 0.18, 1.1), "Fabric", O_BLUE, "UpperTorso", v(0, 0.75, 0)),
            block("HemEdge", v(2.34, 0.1, 1.34), "Fabric", O_GOLD, "LowerTorso", v(0, -1.35, 0)),
            hairCap(rgb(30, 28, 34)),
            block("Ponytail", v(0.3, 1.1, 0.3), "SmoothPlastic", rgb(30, 28, 34), "Head", v(0, 0.2, 0.66), v(15, 0, 0)),
            block("Ribbon", v(0.4, 0.14, 0.4), "Fabric", O_BLUE, "Head", v(0, 0.62, 0.5)),
            block("PracticeSword", v(0.18, 3.0, 0.22), "Wood", WOOD, "UpperTorso", v(0, 0, 0.62), v(0, 0, 35)),
            mouth(),
        },
        Lines = { "Teacher says slow is the hardest speed. He is right. I hate it.", "I am not allowed to hurry. I am trying." },
    },
    {
        Id = "HaeWon", Territory = "Dawnspire", Spot = "NpcPond", Name = "Hae Won", Role = "Pond Keeper",
        Yaw = 0, Lift = 0, Pose = "Stand",
        Scale = { Height = 0.95, Width = 1.12, Head = 1 },
        Colours = { Head = SKIN.Brown, Torso = O_CLOTH, Arms = SKIN.Brown, Legs = rgb(60, 70, 100) },
        Hair = rgb(150, 150, 156), Face = { Owner = "Forgemaster" },
        Parts = {
            coat(O_CLOTH, 2.0),
            block("RollL", v(1.1, 0.7, 1.1), "Fabric", O_CLOTH, "LeftUpperArm", v(0, 0.1, 0)),
            block("RollR", v(1.1, 0.7, 1.1), "Fabric", O_CLOTH, "RightUpperArm", v(0, 0.1, 0)),
            block("Apron", v(1.9, 1.8, 0.2), "Fabric", O_BLUE, "LowerTorso", v(0, -0.7, -0.62)),
            disc("HatBrim", 0.1, 2.4, "Fabric", STRAW, "Head", v(0, 0.62, 0.03)),
            pole("HatCrown", 0.5, 1.3, "Fabric", STRAW, "Head", v(0, 0.88, 0.03)),
            disc("HatBand", 0.18, 1.32, "Fabric", O_BLUE, "Head", v(0, 0.66, 0.03)),
            pole("BroomPole", 6.0, 0.2, "Wood", WOOD, "RightHand", v(0, 1.2, -0.1)),
            block("BroomBrush", v(1.4, 0.9, 0.5), "Fabric", rgb(170, 140, 90), "RightHand", v(0, -1.9, -0.1)),
            mouth(),
        },
        Lines = { "The pond has no fish, but I sweep it every day.", "Some things you do for the quiet." },
    },
    {
        Id = "JiHo", Territory = "Dawnspire", Spot = "NpcStairFoot", Name = "Ji Ho", Role = "Courier",
        Yaw = 3.14, Lift = 0, Pose = "Stand",
        Scale = { Height = 1.05, Width = 0.9, Head = 1 },
        Colours = { Head = SKIN.Light, Torso = O_CLOTH, Arms = O_CLOTH, Legs = O_NAVY },
        Hair = rgb(30, 28, 34), Face = { Owner = "Appraiser" },
        Parts = {
            coat(O_CLOTH, 1.6),
            block("KneeTieL", v(1.06, 0.2, 1.06), "Fabric", O_BLUE, "LeftLowerLeg", v(0, 0.3, 0)),
            block("KneeTieR", v(1.06, 0.2, 1.06), "Fabric", O_BLUE, "RightLowerLeg", v(0, 0.3, 0)),
            headband(O_BLUE),
            block("Clasp", v(0.25, 0.25, 0.1), "Metal", O_GOLD, "Head", v(0, 0.25, -0.64)),
            hairCap(rgb(30, 28, 34)),
            block("Strap", v(0.2, 2.3, 0.12), "Fabric", O_BLUE, "UpperTorso", v(0, 0, -0.54), v(0, 0, -35)),
            block("Satchel", v(0.9, 0.8, 0.4), "Fabric", O_BLUE, "UpperTorso", v(-0.8, -0.9, -0.55)),
            block("Letter", v(0.5, 0.7, 0.06), "SmoothPlastic", rgb(238, 222, 176), "RightHand", v(0, -0.1, -0.3)),
        },
        Lines = { "I carry the hall's letters up these steps. I carry them. I never read them.", "Everyone here keeps what is not theirs." },
    },
    {
        Id = "ChunHo", Territory = "Dawnspire", Spot = "NpcTea1", Name = "Chun Ho", Role = "Old Swordmaster",
        Yaw = 0.785, Lift = 1.0, Pose = "Sit", Seat = { Lower = 1.2, Back = 0 },
        Scale = { Height = 0.92, Width = 0.92, Head = 1 },
        Colours = { Head = SKIN.Tan, Torso = O_CLOTH, Arms = rgb(196, 212, 238), Legs = rgb(236, 238, 244) },
        Hair = WHITE, Face = { Owner = "Forgemaster", Beard = WHITE },
        Parts = { -- stand-in for the long coat (kit K1 later); short, he is sitting
            coat(rgb(196, 212, 238), 1.4),
            block("Collar", v(1.4, 0.22, 1.15), "Fabric", O_BLUE, "UpperTorso", v(0, 0.78, 0)),
            hairCap(WHITE),
            ball("Bun", 0.5, "SmoothPlastic", WHITE, "Head", v(0, 0.86, 0.03)),
            lay("Cane", 3.2, 0.2, "Wood", WOOD, "LowerTorso", v(0, -0.5, -1.1)),
            pole("Cup", 0.4, 0.45, "SmoothPlastic", rgb(240, 240, 244), "RightHand", v(0, -0.2, -0.3)),
        },
        Lines = { "I held a sword for fifty years. Now I hold a teacup.", "The teacup is harder to keep steady." },
    },
    {
        Id = "YeRin", Territory = "Dawnspire", Spot = "NpcTea2", Name = "Ye Rin", Role = "Tea Server",
        Yaw = -0.785, Lift = 1.0, Pose = "Sit", Seat = { Lower = 1.2, Back = 0 },
        Colours = { Head = SKIN.Pale, Torso = O_CLOTH, Arms = O_CLOTH, Legs = O_NAVY },
        Hair = rgb(30, 28, 34), Face = { Owner = "Curator" },
        Parts = {
            coat(O_CLOTH, 1.4),
            block("Trim", v(1.4, 0.2, 1.15), "Fabric", O_BLUE, "UpperTorso", v(0, 0.78, 0)),
            sash(O_BLUE),
            block("SashBand", v(2.15, 0.12, 1.15), "Fabric", O_GOLD, "LowerTorso", v(0, 0.05, 0)),
            block("Bow", v(0.8, 0.5, 0.25), "Fabric", O_BLUE, "LowerTorso", v(0, 0.05, 0.65)),
            hairCap(rgb(30, 28, 34)),
            ball("Bun", 0.55, "SmoothPlastic", rgb(30, 28, 34), "Head", v(0, 0.9, 0.03)),
            block("Comb", v(0.5, 0.12, 0.12), "Metal", O_GOLD, "Head", v(0.35, 0.85, 0.03)),
            ball("Teapot", 0.7, "SmoothPlastic", rgb(244, 244, 248), "RightHand", v(0, -0.35, -0.5)),
            lay("Spout", 0.4, 0.12, "SmoothPlastic", rgb(244, 244, 248), "RightHand", v(0, -0.3, -0.95)),
        },
        Lines = { "Tea first, talk after. That is the rule of this table.", "Careful, it is hot." },
    },
    {
        Id = "NaYeon", Territory = "Dawnspire", Spot = "NpcTea3", Name = "Na Yeon", Role = "Herb Keeper",
        Yaw = 2.356, Lift = 1.0, Pose = "Sit", Seat = { Lower = 1.2, Back = 0 },
        Scale = { Height = 1, Width = 1.08, Head = 1 },
        Colours = { Head = SKIN.Fair, Torso = O_CLOTH, Arms = rgb(160, 180, 170), Legs = rgb(214, 216, 222) },
        Hair = rgb(70, 56, 48), Face = { Owner = "Curator" },
        Parts = {
            coat(O_CLOTH, 1.4),
            block("HeadCloth", v(1.12, 0.55, 1.12), "Fabric", O_BLUE, "Head", v(0, 0.45, 0.03)),
            ball("ClothKnot", 0.36, "Fabric", O_BLUE, "Head", v(0, 0.3, 0.62)),
            block("Pouch", v(0.5, 0.6, 0.35), "Fabric", rgb(112, 80, 54), "LowerTorso", v(0.9, -0.1, -0.55)),
            block("Cord", v(0.08, 2.0, 0.08), "Fabric", rgb(112, 80, 54), "UpperTorso", v(0, 0, -0.52), v(0, 0, 30)),
            block("LeafBundle", v(0.8, 0.3, 0.5), "Fabric", rgb(110, 140, 80), "LowerTorso", v(0, -0.4, -0.9)),
        },
        Lines = { "Rest and drink. Everyone here looks after everyone else.", "It is what the hall is for." },
    },
    {
        Id = "BoRa", Territory = "Dawnspire", Spot = "NpcTea4", Name = "Bo Ra", Role = "Guest from the Valley",
        Yaw = -2.356, Lift = 1.0, Pose = "Sit", Seat = { Lower = 1.2, Back = 0 },
        Scale = { Height = 0.97, Width = 1, Head = 1 },
        Colours = { Head = SKIN.Warm, Torso = rgb(232, 218, 190), Arms = rgb(232, 218, 190), Legs = rgb(140, 108, 76) },
        Hair = rgb(88, 64, 48), Face = { Owner = "Curator" },
        Parts = {
            coat(rgb(150, 118, 84), 1.5),
            hairCap(rgb(88, 64, 48)),
            block("Plait", v(0.3, 1.4, 0.3), "SmoothPlastic", rgb(88, 64, 48), "Head", v(0, -0.7, 0.55)),
            disc("HatBrim", 0.1, 1.8, "Fabric", STRAW, "LowerTorso", v(-1.1, -0.5, -0.2)),
            pole("HatCrown", 0.35, 0.9, "Fabric", STRAW, "LowerTorso", v(-1.1, -0.35, -0.2)),
            block("Basket", v(1.1, 0.6, 0.8), "Wood", rgb(120, 86, 56), "LowerTorso", v(0.1, -0.5, -1.0)),
            ball("PearA", 0.45, "SmoothPlastic", rgb(214, 200, 90), "LowerTorso", v(-0.15, -0.1, -1.0)),
            ball("PearB", 0.45, "SmoothPlastic", rgb(200, 188, 80), "LowerTorso", v(0.35, -0.1, -0.95)),
            pole("Cup", 0.4, 0.4, "SmoothPlastic", rgb(240, 240, 244), "RightHand", v(0, -0.2, -0.3)),
        },
        Lines = { "I came up from the valley with a basket of pears. They gave me tea and a seat.", "Nobody asked me for anything." },
    },

    -- ================= Windrift Hold (Unorthodox): the Hearth Yard =================
    {
        Id = "DeokSu", Territory = "Windrift", Spot = "NpcHearth1", Name = "Deok Su", Role = "Cook",
        Lift = 0, Pose = "Stand",
        Scale = { Height = 1, Width = 1.1, Head = 1 },
        Colours = { Head = SKIN.Red, Torso = U_JADE, Arms = SKIN.Red, Legs = U_TROUSER },
        Hair = rgb(80, 56, 44), Face = { Owner = "Forgemaster", Moustache = rgb(80, 56, 44) },
        Parts = {
            coat(U_JADE, 1.5),
            block("Apron", v(1.9, 2.2, 0.2), "Fabric", U_LINEN, "LowerTorso", v(0, -0.8, -0.62)),
            block("PatchA", v(0.6, 0.6, 0.08), "Fabric", U_PATCH, "LowerTorso", v(0.4, -0.5, -0.74)),
            block("PatchB", v(0.5, 0.5, 0.08), "Fabric", U_COPPER, "LowerTorso", v(-0.4, -1.2, -0.74)),
            block("Scarf", v(1.1, 0.5, 1.1), "Fabric", U_PATCH, "Head", v(0, 0.46, 0.03)),
            ball("ScarfKnot", 0.34, "Fabric", U_PATCH, "Head", v(0, 0.35, 0.62)),
            block("RollL", v(1.1, 0.7, 1.1), "Fabric", U_JADE, "LeftUpperArm", v(0, 0.1, 0)),
            block("RollR", v(1.1, 0.7, 1.1), "Fabric", U_JADE, "RightUpperArm", v(0, 0.1, 0)),
            lay("Ladle", 2.4, 0.14, "Wood", WOOD, "RightHand", v(0, -0.1, -1.2)),
            ball("LadleBowl", 0.55, "Metal", U_COPPER, "RightHand", v(0, -0.1, -2.4)),
        },
        Lines = { "Stew is for everyone. Bring your own spoon.", "Nobody runs this kitchen. I just stand nearest the pot." },
    },
    {
        Id = "Aoi", Territory = "Windrift", Spot = "NpcHearth2", Name = "Aoi", Role = "Rope Climber",
        Lift = 0.5, Pose = "Sit", Seat = { Lower = 1.2, Back = 2.2 },
        Scale = { Height = 1, Width = 0.9, Head = 1 },
        Colours = { Head = SKIN.Tan, Torso = U_JADE, Arms = SKIN.Tan, Legs = U_TROUSER },
        Hair = rgb(28, 26, 30), Face = { Owner = "Appraiser" },
        Parts = {
            coat(U_JADE, 1.2),
            hairCap(rgb(28, 26, 30)),
            ball("Knot", 0.4, "SmoothPlastic", rgb(28, 26, 30), "Head", v(0, 0.86, 0.03)),
            disc("Ring", 0.12, 0.44, "Metal", U_COPPER, "Head", v(0, 0.7, 0.03)),
            block("WrapL", v(1.08, 0.9, 1.08), "Fabric", U_LINEN, "LeftLowerArm", v(0, 0, 0)),
            block("WrapR", v(1.08, 0.9, 1.08), "Fabric", U_LINEN, "RightLowerArm", v(0, 0, 0)),
            block("BandL", v(1.1, 0.12, 1.1), "Metal", U_COPPER, "LeftLowerArm", v(0, -0.45, 0)),
            block("BandR", v(1.1, 0.12, 1.1), "Metal", U_COPPER, "RightLowerArm", v(0, -0.45, 0)),
            disc("RopeA", 0.22, 1.1, "Fabric", ROPE, "UpperTorso", v(-0.5, 0.5, 0.65), v(0, 90, 0)),
            disc("RopeB", 0.22, 1.1, "Fabric", ROPE, "UpperTorso", v(-0.5, 0.5, 0.88), v(0, 90, 0)),
            disc("RopeC", 0.22, 1.1, "Fabric", ROPE, "UpperTorso", v(-0.5, 0.5, 1.11), v(0, 90, 0)),
        },
        Lines = { "Every rope here is older than I am. I still check each one twice.", "They have not failed me yet. Do not tell them I said so." },
    },
    {
        Id = "Kiyo", Territory = "Windrift", Spot = "NpcHearth3", Name = "Kiyo", Role = "Lantern Mender",
        Lift = 0, Pose = "Stand",
        Scale = { Height = 0.88, Width = 0.9, Head = 1 },
        Colours = { Head = SKIN.Warm, Torso = U_PATCH, Arms = U_PATCH, Legs = U_TROUSER },
        Hair = rgb(190, 192, 198), Face = { Owner = "Appraiser" },
        Parts = { -- stand-in for the patchwork cloak (kit K2 later)
            coat(U_PATCH, 2.8),
            block("SkirtHem", v(2.35, 0.4, 1.35), "Fabric", U_JADE, "LowerTorso", v(0, -2.45, 0)),
            block("PatchCuA", v(0.5, 0.5, 0.08), "Fabric", U_COPPER, "LowerTorso", v(0.5, -0.9, -0.69)),
            block("PatchCuB", v(0.45, 0.45, 0.08), "Fabric", U_COPPER, "LowerTorso", v(-0.5, -1.7, -0.69)),
            hairCap(rgb(190, 192, 198)),
            ball("Knot", 0.5, "SmoothPlastic", rgb(190, 192, 198), "Head", v(0, 0.86, 0.03)),
            block("Specs", v(0.95, 0.05, 0.05), "Metal", rgb(120, 90, 56), "Head", v(0, 0.08, -0.62)),
            pole("LanternPole", 3.0, 0.14, "Wood", WOOD, "RightHand", v(0, 0.6, -0.2)),
            block("Lantern", v(0.7, 0.9, 0.7), "SmoothPlastic", rgb(236, 224, 190), "RightHand", v(0, 2.5, -0.2)),
            block("LanternCap", v(0.8, 0.14, 0.8), "Metal", U_COPPER, "RightHand", v(0, 3.02, -0.2)),
        },
        Lines = { "Paper tears. The wind makes sure of it. I mend them anyway.", "The wind never gets bored." },
    },
    {
        Id = "GunWoo", Territory = "Windrift", Spot = "NpcHearth4", Name = "Gun Woo", Role = "Brawler",
        Lift = 0, Pose = "Stand",
        Scale = { Height = 1.1, Width = 1.15, Head = 1 },
        Colours = { Head = SKIN.Tan, Torso = U_LINEN, Arms = SKIN.Tan, Legs = rgb(40, 72, 56) },
        Hair = rgb(30, 28, 34), Face = { Owner = "Appraiser" },
        Parts = {
            block("RopeBelt", v(2.1, 0.25, 1.1), "Fabric", ROPE, "LowerTorso", v(0, 0.0, 0)),
            ball("Bead", 0.22, "Metal", U_COPPER, "UpperTorso", v(0, 0.5, -0.55)),
            block("BeadCord", v(0.05, 0.8, 0.05), "Fabric", rgb(60, 48, 36), "UpperTorso", v(0, 0.9, -0.55)),
            hairCap(rgb(30, 28, 34)),
            topknot(rgb(30, 28, 34)),
            block("WrapL", v(1.08, 1.1, 1.08), "Fabric", U_LINEN, "LeftLowerArm", v(0, 0, 0)),
            block("WrapR", v(1.08, 1.1, 1.08), "Fabric", U_LINEN, "RightLowerArm", v(0, 0, 0)),
            block("FistWrapL", v(1.06, 0.4, 1.1), "Fabric", U_LINEN, "LeftHand", v(0, 0, 0)),
            block("FistWrapR", v(1.06, 0.4, 1.1), "Fabric", U_LINEN, "RightHand", v(0, 0, 0)),
        },
        Lines = { "I lost four bouts today. The stew tastes better after a loss.", "Nobody is my boss. Tomorrow I will lose to somebody else." },
    },
    {
        Id = "JongSu", Territory = "Windrift", Spot = "NpcHearth5", Name = "Jong Su", Role = "Storyteller",
        Lift = 0.5, Pose = "Sit", Seat = { Lower = 1.2, Back = 2.2 },
        Scale = { Height = 1, Width = 0.88, Head = 1 },
        Colours = { Head = SKIN.Warm, Torso = rgb(60, 104, 92), Arms = rgb(60, 104, 92), Legs = rgb(70, 74, 66) },
        Hair = rgb(180, 180, 186), Face = { Owner = "Forgemaster", Beard = rgb(180, 180, 186) },
        Parts = {
            coat(rgb(60, 104, 92), 1.4),
            ball("Clasp", 0.22, "Metal", BRONZE, "UpperTorso", v(0, 0.7, -0.54)),
            block("Fan", v(1.1, 0.06, 0.9), "Wood", rgb(190, 170, 110), "LowerTorso", v(0, -0.4, -1.0)),
            block("FanRim", v(1.12, 0.08, 0.1), "Metal", U_COPPER, "LowerTorso", v(0, -0.4, -1.45)),
            disc("HatBrim", 0.1, 2.0, "Fabric", STRAW, "Head", v(0, 0.5, 0.45), v(-30, 0, 90)),
            pole("HatCrown", 0.45, 1.1, "Fabric", STRAW, "Head", v(0, 0.72, 0.56), v(-30, 0, 0)),
            hairCap(rgb(180, 180, 186)),
        },
        Lines = { "Every road into this hold was made up by someone who did not ask first.", "That is the whole story. The rest is stew." },
    },
    {
        Id = "Tomo", Territory = "Windrift", Spot = "NpcHearth6", Name = "Tomo", Role = "Bell Boy",
        Lift = 0, Pose = "Stand",
        Scale = { Height = 0.8, Width = 0.8, Head = 1.1 },
        Colours = { Head = SKIN.Light, Torso = U_JADE, Arms = U_JADE, Legs = U_TROUSER },
        Hair = rgb(70, 50, 40), Face = { Owner = "Appraiser" },
        Parts = {
            block("Tunic", v(2.4, 2.2, 1.4), "Fabric", U_JADE, "LowerTorso", v(0, -1.0, 0)),
            block("RollL", v(1.15, 0.35, 1.15), "Fabric", U_PATCH, "LeftLowerArm", v(0, 0.3, 0)),
            block("RollR", v(1.15, 0.35, 1.15), "Fabric", U_PATCH, "RightLowerArm", v(0, 0.3, 0)),
            headband(rgb(214, 170, 70)),
            hairCap(rgb(70, 50, 40)),
            ball("BellBody", 0.55, "Metal", BRONZE, "RightHand", v(0, 0.5, -0.15)),
            pole("BellHandle", 0.4, 0.12, "Metal", BRONZE, "RightHand", v(0, 0.1, -0.15)),
        },
        Lines = { "I rang every bell in the hold today. This one is the loudest.", "Do not tell the others which one." },
    },
    {
        Id = "HyeJin", Territory = "Windrift", Spot = "NpcHearth7", Name = "Hye Jin", Role = "Cloth Mender",
        Lift = 0.5, Pose = "Sit", Seat = { Lower = 1.2, Back = 3.2 },
        Colours = { Head = SKIN.Warm, Torso = U_LINEN, Arms = U_LINEN, Legs = U_TROUSER },
        Hair = rgb(62, 46, 40), Face = { Owner = "Curator", Blush = false },
        Parts = {
            coat(U_LINEN, 1.4),
            block("PatchA", v(0.55, 0.55, 0.08), "Fabric", U_PATCH, "UpperTorso", v(-0.5, 0.2, -0.54)),
            block("PatchB", v(0.45, 0.45, 0.08), "Fabric", rgb(96, 150, 110), "UpperTorso", v(0.5, -0.4, -0.54)),
            block("PatchC", v(0.5, 0.5, 0.08), "Fabric", rgb(40, 100, 80), "LeftUpperArm", v(0, 0.1, -0.54)),
            hairCap(rgb(62, 46, 40)),
            block("Braid", v(0.3, 2.2, 0.3), "SmoothPlastic", rgb(62, 46, 40), "UpperTorso", v(0.7, 0.0, -0.6)),
            block("BraidTie", v(0.36, 0.14, 0.36), "Fabric", U_COPPER, "UpperTorso", v(0.7, -1.05, -0.6)),
            lay("Needle", 1.0, 0.05, "Metal", BRONZE, "RightHand", v(0, -0.1, -0.6)),
            block("ClothSquare", v(0.9, 0.06, 0.9), "Fabric", U_PATCH, "LowerTorso", v(0, -0.4, -0.9)),
        },
        Lines = { "Everything here is patched. That is how you know it was loved.", "Hold still, your sleeve is next." },
    },
    {
        Id = "SeokHun", Territory = "Windrift", Spot = "NpcHearth8", Name = "Seok Hun", Role = "Old Fighter",
        Lift = 0.5, Pose = "Sit", Seat = { Lower = 1.2, Back = 2.4 },
        Scale = { Height = 1, Width = 1.12, Head = 1 },
        Colours = { Head = SKIN.Brown, Torso = rgb(40, 72, 60), Arms = rgb(40, 72, 60), Legs = rgb(70, 74, 66) },
        Hair = rgb(120, 120, 124), Face = { Owner = "Appraiser", Moustache = rgb(140, 140, 144) },
        Parts = { -- stand-in for the ragged moss cloak (kit K2 later)
            block("Cloak", v(2.3, 2.8, 0.15), "Fabric", rgb(70, 82, 56), "UpperTorso", v(0, -0.5, 0.6)),
            block("CloakCollar", v(2.3, 0.5, 1.25), "Fabric", rgb(70, 82, 56), "UpperTorso", v(0, 0.75, 0.05)),
            block("HemA", v(0.9, 0.5, 0.2), "Fabric", rgb(60, 72, 48), "UpperTorso", v(-0.7, -2.1, 0.62), v(0, 0, 12)),
            block("HemB", v(0.9, 0.6, 0.2), "Fabric", rgb(78, 90, 62), "UpperTorso", v(0.1, -2.15, 0.64), v(0, 0, -8)),
            block("HemC", v(0.8, 0.5, 0.2), "Fabric", rgb(64, 76, 52), "UpperTorso", v(0.85, -2.1, 0.62), v(0, 0, 15)),
            block("ShinWrap", v(1.1, 0.8, 1.1), "Fabric", rgb(214, 204, 184), "LeftLowerLeg", v(0, -0.1, 0)),
            lay("Staff", 4.0, 0.2, "Wood", WOOD, "LowerTorso", v(0, -0.5, -1.0)),
            block("Stubble", v(0.86, 0.5, 0.14), "SmoothPlastic", rgb(110, 110, 112), "Head", v(0, -0.38, -0.5)),
        },
        Lines = { "I fought everywhere and followed no one. Now I follow the fire.", "It is easier on the knees." },
    },
    {
        Id = "Haru", Territory = "Windrift", Spot = "NpcHearth9", Name = "Haru", Role = "Forager",
        Lift = 0, Pose = "Stand",
        Scale = { Height = 0.92, Width = 0.9, Head = 1 },
        Colours = { Head = SKIN.Warm, Torso = rgb(40, 80, 60), Arms = rgb(40, 80, 60), Legs = rgb(80, 64, 48) },
        Hair = rgb(90, 66, 48), Face = { Owner = "Appraiser" },
        Parts = { -- stand-in for the hooded mantle (kit K2 later)
            block("Hood", v(1.28, 0.8, 1.28), "Fabric", rgb(30, 80, 60), "Head", v(0, 0.4, 0.05)),
            block("Mantle", v(2.4, 1.0, 1.3), "Fabric", rgb(30, 80, 60), "UpperTorso", v(0, 0.55, 0.08)),
            block("MantleBack", v(2.0, 2.0, 0.15), "Fabric", rgb(30, 80, 60), "UpperTorso", v(0, -0.1, 0.62)),
            ball("Pin", 0.22, "Metal", U_COPPER, "UpperTorso", v(0, 0.85, -0.64)),
            block("BasketFrame", v(1.5, 1.9, 0.9), "Fabric", rgb(160, 126, 80), "UpperTorso", v(0, -0.2, 1.1)),
            block("Leaves", v(1.2, 0.3, 0.7), "Fabric", rgb(80, 130, 70), "UpperTorso", v(0, 0.85, 1.1)),
            ball("Mushroom", 0.35, "SmoothPlastic", rgb(170, 120, 90), "UpperTorso", v(0.35, 1.1, 1.1)),
            block("StrapL", v(0.2, 1.8, 0.1), "Fabric", rgb(112, 80, 54), "UpperTorso", v(-0.6, 0.1, -0.54)),
            block("StrapR", v(0.2, 1.8, 0.1), "Fabric", rgb(112, 80, 54), "UpperTorso", v(0.6, 0.1, -0.54)),
            block("MudBootL", v(1.05, 0.9, 1.1), "Fabric", rgb(84, 64, 46), "LeftLowerLeg", v(0, -0.35, 0)),
            block("MudBootR", v(1.05, 0.9, 1.1), "Fabric", rgb(84, 64, 46), "RightLowerLeg", v(0, -0.35, 0)),
        },
        Lines = { "The forest feeds anyone who looks. Most people just walk past.", "Look down once in a while." },
    },
    {
        Id = "Sora", Territory = "Windrift", Spot = "NpcHearth10", Name = "Sora", Role = "Kite Maker",
        Lift = 0, Pose = "Stand",
        Colours = { Head = SKIN.Fair, Torso = rgb(232, 224, 200), Arms = rgb(232, 224, 200), Legs = rgb(30, 80, 66) },
        Hair = rgb(40, 34, 36), Face = { Owner = "Curator" },
        Parts = {
            block("Apron", v(1.9, 1.8, 0.2), "Fabric", U_JADE, "LowerTorso", v(0, -0.7, -0.62)),
            block("NeckCord", v(1.3, 0.07, 1.1), "Fabric", rgb(60, 48, 36), "UpperTorso", v(0, 0.78, 0)),
            disc("Rings", 0.1, 0.3, "Metal", U_COPPER, "UpperTorso", v(0, 0.45, -0.55), v(0, 90, 0)),
            hairCap(rgb(40, 34, 36)),
            block("Tuft", v(0.3, 0.3, 0.3), "SmoothPlastic", rgb(40, 34, 36), "Head", v(0.3, 0.8, 0.1), v(0, 0, 35)),
            block("Kite", v(1.7, 1.7, 0.06), "SmoothPlastic", U_JADE, "UpperTorso", v(0.3, 0.3, 0.9), v(0, 0, 45)),
            block("KiteCopper", v(1.0, 1.0, 0.08), "SmoothPlastic", U_COPPER, "UpperTorso", v(0.3, -0.2, 0.93), v(0, 0, 45)),
            block("TailA", v(0.1, 0.5, 0.1), "Fabric", ROPE, "UpperTorso", v(0.3, -1.4, 0.9)),
            block("TailB", v(0.1, 0.5, 0.1), "Fabric", ROPE, "UpperTorso", v(0.38, -1.95, 0.9)),
            block("TailC", v(0.1, 0.5, 0.1), "Fabric", ROPE, "UpperTorso", v(0.3, -2.5, 0.9)),
        },
        Lines = { "The wind here only goes one way. So I build kites that try the other.", "They all end up in the same tree." },
    },

    -- ================= Nightfall Citadel (Demonic): the Ember Court =================
    {
        Id = "Daichi", Territory = "Nightfall", Spot = "Npc1", Name = "Daichi", Role = "Banner Bearer",
        Lift = 0, Pose = "Stand",
        Scale = { Height = 1.18, Width = 1.2, Head = 1 },
        Colours = { Head = SKIN.Tan, Torso = D_BLACK, Arms = D_BLACK, Legs = D_BLACK },
        Hair = D_BLACK, Face = { Owner = "Appraiser" },
        Parts = { -- stand-in for the plate cuirass (kit K3 later); shaved head
            coat(D_BLACK),
            block("Hem", v(2.35, 0.3, 1.35), "Fabric", D_CRIMSON, "LowerTorso", v(0, -2.5, 0)),
            block("Chestplate", v(2.15, 1.6, 1.15), "Metal", IRON_LIGHT, "UpperTorso", v(0, 0, 0)),
            block("PauldronL", v(1.3, 0.5, 1.3), "Metal", IRON_LIGHT, "UpperTorso", v(-1.45, 0.75, 0)),
            block("PauldronR", v(1.3, 0.5, 1.3), "Metal", IRON_LIGHT, "UpperTorso", v(1.45, 0.75, 0)),
            pole("BannerPole", 9.0, 0.22, "Wood", WOOD, "RightHand", v(0, 2.5, -0.1)),
            block("Spike", v(0.35, 0.8, 0.35), "Metal", IRON_LIGHT, "RightHand", v(0, 7.4, -0.1)),
            block("BannerCloth", v(1.8, 3.0, 0.08), "Fabric", D_CRIMSON, "RightHand", v(0.95, 5.3, -0.1)),
            beard(D_BLACK),
        },
        Lines = { "The banner does not bend. Neither do I.", "Stand near it. It is quieter than it looks." },
    },
    {
        Id = "Hotaru", Territory = "Nightfall", Spot = "Npc2", Name = "Hotaru", Role = "Armour Polisher",
        Lift = 0.5, Pose = "Sit", Seat = { Lower = 1.2, Back = 2.8 },
        Scale = { Height = 0.95, Width = 0.88, Head = 1 },
        Colours = { Head = SKIN.Pale, Torso = D_BLACK, Arms = D_BLACK, Legs = rgb(22, 20, 26) },
        Hair = rgb(24, 22, 28), Face = { Owner = "Curator", Blush = false },
        Parts = {
            coat(D_BLACK, 1.4),
            sash(D_CRIMSON),
            block("Apron", v(1.7, 1.3, 0.2), "Fabric", rgb(110, 80, 56), "LowerTorso", v(0, -0.5, -0.62)),
            block("Breastplate", v(1.9, 0.25, 1.2), "Metal", IRON_LIGHT, "LowerTorso", v(0, -0.4, -1.0)),
            block("PolishCloth", v(0.5, 0.1, 0.5), "Fabric", rgb(200, 198, 190), "RightHand", v(0, -0.2, -0.3)),
            hairCap(rgb(24, 22, 28)),
            block("Tail", v(0.3, 0.9, 0.3), "SmoothPlastic", rgb(24, 22, 28), "Head", v(0, 0.1, 0.62), v(15, 0, 0)),
        },
        Lines = { "Polish it enough and the iron shows you your own face.", "Most people look away." },
    },
    {
        Id = "Kaito", Territory = "Nightfall", Spot = "Npc3", Name = "Kaito", Role = "Drummer",
        Lift = 0, Pose = "Stand",
        Scale = { Height = 1.05, Width = 0.92, Head = 1 },
        Colours = { Head = SKIN.Tan, Torso = D_BLACK, Arms = SKIN.Tan, Legs = D_BLACK },
        Hair = rgb(24, 22, 28), Face = { Owner = "Appraiser" },
        Parts = { -- the drum makes no sound (owner's decision)
            headband(D_CRIMSON),
            hairCap(rgb(24, 22, 28)),
            block("TrimL", v(0.15, 1.6, 0.08), "Fabric", D_CRIMSON, "UpperTorso", v(-0.3, 0, -0.52)),
            block("TrimR", v(0.15, 1.6, 0.08), "Fabric", D_CRIMSON, "UpperTorso", v(0.3, 0, -0.52)),
            lay("StickL", 1.7, 0.18, "Wood", WOOD, "LeftHand", v(0, -0.1, -0.5)),
            lay("StickR", 1.7, 0.18, "Wood", WOOD, "RightHand", v(0, -0.1, -0.5)),
            pole("DrumBody", 1.4, 2.2, "Metal", rgb(70, 68, 78), "LowerTorso", v(0, -1.0, -2.1)),
            disc("DrumHead", 0.12, 2.3, "SmoothPlastic", D_CRIMSON, "LowerTorso", v(0, -0.28, -2.1)),
            disc("DrumBandA", 0.14, 2.25, "Metal", D_IRON, "LowerTorso", v(0, -0.6, -2.1)),
            disc("DrumBandB", 0.14, 2.25, "Metal", D_IRON, "LowerTorso", v(0, -1.4, -2.1)),
            pole("DrumStand", 1.3, 1.2, "Wood", U_WOOD, "LowerTorso", v(0, -2.35, -2.1)),
        },
        Lines = { "The drum is the only voice the keep ever needs.", "I only play it when asked." },
    },
    {
        Id = "SeungHo", Territory = "Nightfall", Spot = "Npc4", Name = "Seung Ho", Role = "Blade Sharpener",
        Lift = 0.5, Pose = "Sit", Seat = { Lower = 1.2, Back = 2.8 },
        Scale = { Height = 1, Width = 1.08, Head = 1 },
        Colours = { Head = SKIN.Tan, Torso = D_BLACK, Arms = D_BLACK, Legs = rgb(22, 20, 26) },
        Hair = rgb(24, 22, 28), Face = { Owner = "Appraiser" },
        Parts = {
            coat(D_BLACK, 1.4),
            sash(D_CRIMSON),
            hairCap(rgb(24, 22, 28)),
            block("Ponytail", v(0.35, 1.8, 0.3), "SmoothPlastic", rgb(24, 22, 28), "Head", v(0, -0.2, 0.66), v(10, 0, 0)),
            block("SleeveCordL", v(1.05, 0.2, 1.05), "Fabric", D_CRIMSON, "LeftUpperArm", v(0, 0, 0)),
            block("SleeveCordR", v(1.05, 0.2, 1.05), "Fabric", D_CRIMSON, "RightUpperArm", v(0, 0, 0)),
            block("Whetstone", v(0.9, 0.35, 0.5), "SmoothPlastic", rgb(150, 152, 160), "LeftHand", v(0, -0.2, -0.4)),
            block("Blade", v(0.08, 0.25, 1.8), "Metal", rgb(190, 194, 204), "RightHand", v(0, -0.1, -0.6)),
        },
        Lines = { "A dull blade is a lie you tell yourself.", "I do not lie to myself." },
    },
    {
        Id = "Shin", Territory = "Nightfall", Spot = "Npc5", Name = "Shin", Role = "Chain Maker",
        Lift = 0, Pose = "Stand",
        Scale = { Height = 1.02, Width = 1.2, Head = 1 },
        Colours = { Head = SKIN.Brown, Torso = D_BLACK, Arms = D_BLACK, Legs = D_BLACK },
        Hair = rgb(70, 68, 72), Face = { Owner = "Appraiser" },
        Parts = { -- bald; the Appraiser's face, not the Forgemaster's, so he does not read as Brann
            coat(D_BLACK, 2.0),
            block("Apron", v(1.9, 2.6, 0.2), "Fabric", rgb(40, 38, 44), "UpperTorso", v(0, -0.6, -0.6)),
            block("BracerL", v(1.12, 0.9, 1.12), "Metal", D_IRON, "LeftLowerArm", v(0, -0.05, 0)),
            block("BracerR", v(1.12, 0.9, 1.12), "Metal", D_IRON, "RightLowerArm", v(0, -0.05, 0)),
            pole("HammerHaft", 1.6, 0.15, "Wood", WOOD, "LowerTorso", v(1.2, -0.7, -0.2)),
            block("HammerHead", v(0.7, 0.5, 0.5), "Metal", IRON_LIGHT, "LowerTorso", v(1.2, 0.2, -0.2)),
            lay("LinkA", 0.4, 0.28, "Metal", IRON_LIGHT, "UpperTorso", v(-0.8, 0.85, -0.55)),
            part("LinkB", "Cylinder", v(0.4, 0.28, 0.28), "Metal", IRON_LIGHT, "UpperTorso", v(0, 0.15, -0.6), v(0, 0, 0)),
            lay("LinkC", 0.4, 0.28, "Metal", IRON_LIGHT, "UpperTorso", v(0.8, -0.55, -0.55)),
        },
        Lines = { "Every chain on these walls passed through my hands.", "None has ever slipped." },
    },
    {
        Id = "Nao", Territory = "Nightfall", Spot = "Npc6", Name = "Nao", Role = "Fire Keeper",
        Lift = 0, Pose = "Stand",
        Colours = { Head = SKIN.Light, Torso = D_BLACK, Arms = D_BLACK, Legs = rgb(22, 20, 26) },
        Hair = rgb(24, 22, 28), Face = { Owner = "Curator", Lashes = false, Blush = false },
        Parts = {
            coat(D_BLACK, 2.4),
            block("Collar", v(1.35, 0.22, 1.15), "Fabric", D_CRIMSON, "UpperTorso", v(0, 0.78, 0)),
            hairCap(rgb(24, 22, 28)),
            ball("Bun", 0.5, "SmoothPlastic", rgb(24, 22, 28), "Head", v(0, 0.86, 0.03)),
            block("BunPin", v(0.6, 0.08, 0.08), "Metal", D_IRON, "Head", v(0, 0.86, 0.03)),
            block("GloveL", v(1.08, 0.5, 1.1), "Fabric", rgb(40, 36, 40), "LeftHand", v(0, 0, 0)),
            block("GloveR", v(1.08, 0.5, 1.1), "Fabric", rgb(40, 36, 40), "RightHand", v(0, 0, 0)),
            part("Poker", "Cylinder", v(5.0, 0.12, 0.12), "Metal", D_IRON, "RightHand", v(-0.2, 0.9, -0.1), v(0, 0, 80)),
            block("PokerHook", v(0.4, 0.12, 0.12), "Metal", D_IRON, "RightHand", v(-0.6, 3.3, -0.1)),
            part("Bucket", "Cylinder", v(0.8, 0.8, 0.8), "Metal", D_BLACK, "LeftHand", v(0, -0.9, 0), v(0, 0, 90)),
        },
        Lines = { "The fire has not gone out since before I came here.", "Nobody gets cold on my watch." },
    },
    {
        Id = "Isamu", Territory = "Nightfall", Spot = "Npc7", Name = "Isamu", Role = "Old Veteran",
        Lift = 0.5, Pose = "Sit", Seat = { Lower = 1.2, Back = 2.8 },
        Scale = { Height = 1.1, Width = 0.9, Head = 1 },
        Colours = { Head = SKIN.Warm, Torso = D_BLACK, Arms = D_BLACK, Legs = rgb(22, 20, 26) },
        Hair = WHITE, Face = { Owner = "Appraiser", Moustache = rgb(150, 150, 154) },
        Parts = {
            coat(D_BLACK, 1.4),
            hairCap(WHITE),
            block("SlingStrap", v(0.2, 2.0, 0.12), "Fabric", D_BLACK, "UpperTorso", v(0, 0.2, -0.54), v(0, 0, 40)),
            block("SlingPouch", v(1.1, 0.8, 0.5), "Fabric", D_BLACK, "LeftLowerArm", v(0, 0, -0.3)),
            block("Scarf", v(1.5, 0.5, 1.2), "Fabric", D_CRIMSON, "UpperTorso", v(0, 0.85, 0)),
            block("ScarfTail", v(0.4, 1.2, 0.12), "Fabric", D_CRIMSON, "UpperTorso", v(0.4, 0.2, -0.58)),
            part("Cane", "Cylinder", v(3.0, 0.16, 0.16), "Wood", WOOD, "LowerTorso", v(-0.7, -0.8, -1.3), v(0, 0, 90)),
            block("CaneHook", v(0.4, 0.15, 0.15), "Wood", WOOD, "LowerTorso", v(-0.5, 0.7, -1.3)),
        },
        Lines = { "Strength is the only law, they say.", "Nobody says what the law does about a sore shoulder." },
    },
    {
        Id = "Ren", Territory = "Nightfall", Spot = "Npc8", Name = "Ren", Role = "Recruit",
        Lift = 0, Pose = "Stand",
        Scale = { Height = 0.9, Width = 0.88, Head = 1 },
        Colours = { Head = SKIN.Light, Torso = D_BLACK, Arms = D_BLACK, Legs = D_BLACK },
        Hair = rgb(24, 22, 28), Face = { Owner = "Appraiser" },
        Parts = { -- the helmet is too big for him; stand-in for the oversized helmet (kit K3 later)
            coat(D_BLACK, 1.5),
            sash(D_CRIMSON, "Belt"),
            ball("HelmetDome", 1.6, "Metal", IRON_LIGHT, "Head", v(0, 0.9, 0.05)),
            disc("HelmetRim", 0.3, 1.5, "Metal", IRON_LIGHT, "Head", v(0, 0.5, 0.05)),
            block("Plume", v(0.15, 0.7, 0.8), "Fabric", D_CRIMSON, "Head", v(0, 1.85, 0.05)),
            pole("PracticeSpear", 6.5, 0.16, "Wood", WOOD, "RightHand", v(0, 1.2, -0.1)),
            block("PracticeTip", v(0.2, 0.6, 0.2), "Wood", rgb(160, 126, 80), "RightHand", v(0, 4.7, -0.1)),
        },
        Lines = { "Do not talk to me. I am on watch.", "...Hello. Please do not tell the captain I said hello." },
    },
    {
        Id = "HyunJoo", Territory = "Nightfall", Spot = "Npc9", Name = "Hyun Joo", Role = "Court Cook",
        Lift = 0.5, Pose = "Sit", Seat = { Lower = 1.2, Back = 2.8 },
        Scale = { Height = 0.95, Width = 1.15, Head = 1 },
        Colours = { Head = SKIN.Fair, Torso = rgb(120, 30, 40), Arms = rgb(120, 30, 40), Legs = D_BLACK },
        Hair = rgb(24, 22, 28), Face = { Owner = "Curator" },
        Parts = {
            coat(rgb(130, 32, 40), 1.4),
            block("Apron", v(1.9, 1.6, 0.2), "Fabric", D_BLACK, "LowerTorso", v(0, -0.2, -0.62)),
            hairCap(rgb(24, 22, 28)),
            headband(D_BLACK),
            block("BandKnot", v(0.3, 0.2, 0.1), "Fabric", D_BLACK, "Head", v(0, 0.28, -0.64)),
            part("Bowl", "Cylinder", v(0.4, 0.7, 0.7), "SmoothPlastic", rgb(230, 226, 214), "LeftHand", v(0, 0.2, -0.4), v(0, 0, 90)),
            part("Soup", "Cylinder", v(0.05, 0.62, 0.62), "SmoothPlastic", rgb(170, 60, 30), "LeftHand", v(0, 0.42, -0.4), v(0, 0, 90)),
            lay("Chopsticks", 1.0, 0.05, "Wood", WOOD, "RightHand", v(0, -0.1, -0.5)),
        },
        Lines = { "Black pot, red pepper, no complaints.", "Eat. Then complain." },
    },
    {
        Id = "DongHyun", Territory = "Nightfall", Spot = "Npc10", Name = "Dong Hyun", Role = "Gate Guard",
        Lift = 0, Pose = "Stand",
        Scale = { Height = 1.05, Width = 1.1, Head = 1 },
        Colours = { Head = SKIN.Tan, Torso = D_BLACK, Arms = D_BLACK, Legs = D_BLACK },
        Hair = rgb(24, 22, 28), Face = { Owner = "Appraiser" },
        Parts = { -- stand-in for the plate (kit K3 later)
            coat(D_BLACK),
            block("Breastplate", v(2.15, 1.6, 1.15), "Metal", IRON_LIGHT, "UpperTorso", v(0, 0, 0)),
            block("PlateEdge", v(2.2, 0.12, 1.2), "Metal", D_CRIMSON, "UpperTorso", v(0, -0.8, 0)),
            block("PauldronL", v(1.3, 0.5, 1.3), "Metal", IRON_LIGHT, "UpperTorso", v(-1.45, 0.75, 0)),
            block("PauldronR", v(1.3, 0.5, 1.3), "Metal", IRON_LIGHT, "UpperTorso", v(1.45, 0.75, 0)),
            ball("HelmetUnderArm", 0.9, "Metal", IRON_LIGHT, "LeftLowerArm", v(0.2, 0.2, -0.45)),
            pole("SpearShaft", 7.5, 0.18, "Wood", WOOD, "RightHand", v(0, 1.5, -0.1)),
            block("SpearHead", v(0.2, 0.9, 0.34), "Metal", rgb(190, 194, 204), "RightHand", v(0, 5.7, -0.1)),
            hairCap(rgb(24, 22, 28)),
        },
        Lines = { "The gate is open to anyone.", "It is also watched by me." },
    },
}

return {
    People = People,
    -- the R15 body parts a dress part may ride (the spec checks every part against these)
    BodyParts = {
        "Head", "UpperTorso", "LowerTorso",
        "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm", "RightHand",
        "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot",
    },
}
