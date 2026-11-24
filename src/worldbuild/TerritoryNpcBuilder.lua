-- Build-time only: run from Studio (Edit mode), after a territory's builder has made its Spots folder, to put the territory's ten people at their
-- marked places (the owner approved all 30, 2026-11-24; the data is Placements/TerritoryNpcs.lua, the proposal "Territory NPC Proposals 2026-11-24").
-- Nothing calls this yet: the Studio session wires it in and looks at the result. Require a clone so Studio's module cache never serves an old copy:
--
--   local TNB = require(game.ServerStorage.WorldBuild.TerritoryNpcBuilder:Clone())
--   local spots = workspace.FloatingIslands.MurimCrossing.Dawnspire.Territory.Spots   -- (wherever the territory builder put it)
--   local made = TNB.build("Dawnspire", spots, spots.Parent:FindFirstChild("Npcs") or Instance.new("Folder", spots.Parent))
--
-- Modelled on CrossingBuilder.buildRep: the stock R15 rig from a HumanoidDescription (four colours, and the scales where a row has them), the stock Animate
-- script deleted, the root anchored, the stock face cleared and a hub face borrowed (brows, eyes, mouth, nose, and a beard or moustache where the row
-- asks), plain welded Parts for the clothes and props (light, unable to collide), a name tag "Name, Role" that shows within 20 studs, the tags HubNpc
-- (NpcService plays the standard idle) and TerritoryNpc, and the attributes NpcId, Territory, Role, Spot, Line1, Line2, Pose (+ SeatLower, SeatBack for a
-- seated person). A person's front is -Z. The seated pose itself is NOT made here: only the placement (lowered and moved toward the seat, per the row).
-- build() can be run again: a person already in `parent` under the same name is replaced.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")

local WorldBuild = ServerStorage:WaitForChild("WorldBuild")
local WorldBuilder = require(WorldBuild:WaitForChild("WorldBuilder"):Clone())
local Data = require(WorldBuild:WaitForChild("Placements"):WaitForChild("TerritoryNpcs"):Clone())

local TerritoryNpcBuilder = {}

local NAME_DISTANCE = 20 -- the hub's people show their tag within 45; ten tags in one small court would pile up
local TAG_PEOPLE = "TerritoryNpc"

local SHAPES = {
    Block = Enum.PartType.Block,
    Cylinder = Enum.PartType.Cylinder,
    Ball = Enum.PartType.Ball,
}
local MATERIALS = {
    Fabric = Enum.Material.Fabric,
    SmoothPlastic = Enum.Material.SmoothPlastic,
    Metal = Enum.Material.Metal,
    Wood = Enum.Material.Wood,
}

-- Which pieces of the hub's kit make up each borrowed face (the same lists as CrossingBuilder.FACES).
local FACE_PIECES = {
    Curator = { "Brows", "EyeWhites", "EyeShine", "Pupils", "Mouth" },
    Forgemaster = { "Brows", "EyeWhites", "EyeShine", "Pupils", "Nose" },
    Appraiser = { "Brows", "EyeWhites", "EyeShine", "Pupils", "Mouth", "Nose" },
}

local function newDescription(colours, scale)
    local description = Instance.new("HumanoidDescription")
    description.HeadColor = colours.Head
    description.TorsoColor = colours.Torso
    description.LeftArmColor, description.RightArmColor = colours.Arms, colours.Arms
    description.LeftLegColor, description.RightLegColor = colours.Legs, colours.Legs
    if scale then
        description.HeightScale = scale.Height or 1
        description.WidthScale = scale.Width or 1
        description.DepthScale = scale.Width or 1
        description.HeadScale = scale.Head or 1
    end
    return description
end

local function newRig(colours, scale)
    local rig = Players:CreateHumanoidModelFromDescription(newDescription(colours, scale), Enum.HumanoidRigType.R15)
    local stockAnimate = rig:FindFirstChild("Animate")
    if stockAnimate then
        stockAnimate:Destroy() -- (a LocalScript in the Workspace never runs; NpcService plays the idle on the server)
    end
    return rig
end

-- The unscaled R15 body, built once per build() call: its part sizes and where its head sits (in the root's frame) are what a scaled person's dress and
-- borrowed face are measured against, so they follow whatever Roblox really did with the scales (clamped or not).
local function reference()
    local rig = newRig({ Head = Color3.new(1, 1, 1), Torso = Color3.new(1, 1, 1), Arms = Color3.new(1, 1, 1), Legs = Color3.new(1, 1, 1) }, nil)
    local ref = { Sizes = {}, HeadOffset = rig.HumanoidRootPart.CFrame:ToObjectSpace(rig.Head.CFrame).Position }
    for _, bodyPart in rig:GetChildren() do
        if bodyPart:IsA("BasePart") then
            ref.Sizes[bodyPart.Name] = bodyPart.Size
        end
    end
    rig:Destroy()
    return ref
end

-- how much a body part was scaled, per axis, against the unscaled body
local function factorOf(rig, ref, bodyName)
    local body = rig:FindFirstChild(bodyName)
    local base = ref.Sizes[bodyName]
    assert(body and base, "R15 body part " .. bodyName .. " is missing")
    return Vector3.new(body.Size.X / base.X, body.Size.Y / base.Y, body.Size.Z / base.Z)
end

-- Something worn or held: a plain Part welded to a body part, light and unable to collide (CrossingBuilder.wear).
local function wear(rig, ref, spec)
    local body = rig:FindFirstChild(spec.On)
    assert(body, "R15 body part " .. tostring(spec.On) .. " is missing")
    local factor = factorOf(rig, ref, spec.On)
    local size = Vector3.new(spec.Size.X * factor.X, spec.Size.Y * factor.Y, spec.Size.Z * factor.Z)
    local offset = Vector3.new(spec.Offset.X * factor.X, spec.Offset.Y * factor.Y, spec.Offset.Z * factor.Z)
    local turn = spec.Turn or Vector3.zero
    local p = Instance.new(if spec.Shape == "Wedge" then "WedgePart" else "Part")
    p.Name = spec.Name
    p.Size = size
    p.TopSurface = Enum.SurfaceType.Smooth
    p.BottomSurface = Enum.SurfaceType.Smooth
    p.Material = assert(MATERIALS[spec.Material], "unknown material " .. tostring(spec.Material))
    p.Color = spec.Colour
    if p:IsA("Part") then
        p.Shape = assert(SHAPES[spec.Shape], "unknown shape " .. tostring(spec.Shape))
    end
    p.CFrame = body.CFrame * CFrame.new(offset) * CFrame.Angles(math.rad(turn.X), math.rad(turn.Y), math.rad(turn.Z))
    p.Anchored = false
    p.Massless = true
    p.CanCollide, p.CanQuery, p.CanTouch = false, false, false
    p.CastShadow = spec.Material ~= "Fabric" -- (cloth casts none, as CrossingBuilder's does)
    local weld = Instance.new("WeldConstraint")
    weld.Part0 = body
    weld.Part1 = p
    weld.Parent = p
    p.Parent = rig
    return p
end

-- The borrowed face (CrossingBuilder.wearFace, with the options a row can ask for). Returns how many kit pieces were put on; 0 leaves the stock face alone
-- (the kit is not stored in this place).
local function wearFace(rig, ref, face, hair)
    local kit = WorldBuilder.kitFolder("HubNpcs")
    if not kit then
        return 0
    end
    local data = WorldBuilder.npcData()
    -- piece base name -> { Owner, Colour (nil: the kit's own) }
    local wanted = {}
    for _, piece in FACE_PIECES[face.Owner] do
        wanted[face.Owner .. "_" .. piece] = { Owner = face.Owner, Colour = if piece == "Brows" then hair else nil }
    end
    if face.Owner == "Curator" then
        if face.Lashes ~= false then
            wanted.Curator_Lashes = { Owner = "Curator" }
        end
        if face.Blush ~= false then
            wanted.Curator_Blush = { Owner = "Curator" }
        end
    end
    if face.Beard then
        wanted.Forgemaster_Beard = { Owner = "Forgemaster", Colour = face.Beard }
    end
    if face.Moustache then
        assert(face.Owner ~= "Curator", "the Curator has no moustache")
        wanted[face.Owner .. "_Moustache"] = { Owner = face.Owner, Colour = face.Moustache }
    end
    local head = rig.Head
    local factor = factorOf(rig, ref, "Head")
    local rootFrame = rig.HumanoidRootPart.CFrame
    local count = 0
    for _, template in kit:GetChildren() do
        local base = WorldBuilder.splitName(template.Name)
        local want = wanted[base]
        if template:IsA("MeshPart") and want then
            local bodyPart = rig:FindFirstChild(data.Pieces[base] or "")
            if bodyPart == head then
                -- (dressed unwelded first: a piece is moved and sized to this head before it is welded to it)
                local piece = WorldBuilder.dressPiece(template, data, want.Owner, rootFrame, rig, nil)
                if want.Colour then
                    piece.Color = want.Colour
                end
                if factor ~= Vector3.one then
                    -- (the kit is authored for the unscaled body: carry each piece with the head it sits on)
                    local fromHead = template.CFrame.Position - ref.HeadOffset
                    local scaled = Vector3.new(fromHead.X * factor.X, fromHead.Y * factor.Y, fromHead.Z * factor.Z)
                    local turned = rootFrame.Rotation * (template.CFrame - template.CFrame.Position)
                    piece.CFrame = CFrame.new(head.Position + rootFrame:VectorToWorldSpace(scaled)) * turned
                    piece.Size = Vector3.new(piece.Size.X * factor.X, piece.Size.Y * factor.Y, piece.Size.Z * factor.Z)
                end
                piece.Anchored = false
                piece.Massless = true
                piece.CanCollide, piece.CanQuery = false, false
                local weld = Instance.new("WeldConstraint")
                weld.Part0 = head
                weld.Part1 = piece
                weld.Parent = piece
                count += 1
            end
        end
    end
    if count > 0 then
        head.TextureID = "" -- the stock face: this one wears the modelled face
        for _, decal in head:GetChildren() do
            if decal:IsA("Decal") then
                decal:Destroy()
            end
        end
    end
    return count
end

-- The "Talk" prompt (F, as every other prompt; E is cultivation). Off by default: the client's talk controller may make its own.
function TerritoryNpcBuilder.addPrompt(rig, person)
    local prompt = Instance.new("ProximityPrompt")
    prompt.ActionText = "Talk"
    prompt.ObjectText = person.Name
    prompt.KeyboardKeyCode = Enum.KeyCode.F
    prompt.HoldDuration = 0
    prompt.MaxActivationDistance = 10
    prompt.RequiresLineOfSight = false
    prompt:SetAttribute("TerritoryTalk", true)
    prompt.Parent = rig.HumanoidRootPart
    return prompt
end

-- How high the root sits over the feet (the rest pose, as built, scaled): 3 studs for the unscaled body.
local function rootHeight(rig)
    local root = rig.HumanoidRootPart
    local lowest = math.huge
    for _, footName in { "LeftFoot", "RightFoot" } do
        local foot = rig:FindFirstChild(footName)
        if foot then
            lowest = math.min(lowest, foot.Position.Y - foot.Size.Y / 2)
        end
    end
    if lowest == math.huge then
        return 3
    end
    return root.Position.Y - lowest
end

local function buildPerson(person, spot, parent, ref, withPrompt)
    local old = parent:FindFirstChild(person.Id)
    if old then
        old:Destroy()
    end
    local rig = newRig(person.Colours, person.Scale)
    rig.Name = person.Id
    rig.Parent = parent

    -- placement: the spot's own rotation (Windrift's and Nightfall's already face the fire; Dawnspire's has yaw 0 and the row's Yaw is the facing), up by the root's
    -- height over the feet and the floor or seat (Lift), lowered and moved toward the seat for a seated person (a first guess, to be tuned in Studio)
    local up = rootHeight(rig) + (person.Lift or 0)
    local back = 0
    if person.Seat then
        up -= person.Seat.Lower
        back = person.Seat.Back
    end
    rig:PivotTo(spot.CFrame * CFrame.Angles(0, person.Yaw or 0, 0) * CFrame.new(0, up, back))
    rig.HumanoidRootPart.Anchored = true

    wearFace(rig, ref, person.Face, person.Hair)
    for _, spec in person.Parts do
        wear(rig, ref, spec)
    end
    for _, descendant in rig:GetDescendants() do
        if descendant:IsA("BasePart") then
            descendant.CanTouch = false
        end
    end

    local humanoid = rig:FindFirstChildOfClass("Humanoid")
    humanoid.DisplayName = person.Name .. ", " .. person.Role
    humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.Viewer
    humanoid.NameDisplayDistance = NAME_DISTANCE
    humanoid.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
    rig.PrimaryPart = rig.HumanoidRootPart
    rig.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
    rig:SetAttribute("NpcId", person.Id)
    rig:SetAttribute("Territory", person.Territory)
    rig:SetAttribute("Role", person.Role)
    rig:SetAttribute("Spot", person.Spot)
    rig:SetAttribute("Line1", person.Lines[1])
    rig:SetAttribute("Line2", person.Lines[2])
    rig:SetAttribute("Pose", person.Pose)
    if person.Seat then
        rig:SetAttribute("SeatLower", person.Seat.Lower)
        rig:SetAttribute("SeatBack", person.Seat.Back)
    end
    CollectionService:AddTag(rig, "HubNpc") -- (NpcService plays the standard idle)
    CollectionService:AddTag(rig, TAG_PEOPLE)
    if withPrompt then
        TerritoryNpcBuilder.addPrompt(rig, person)
    end
    return rig
end

-- Builds the territory's people at their spots. territoryName: "Dawnspire" | "Windrift" | "Nightfall". spotsFolder: that territory's Spots folder (the markers
-- named in the data). parent: where the models go. withPrompt: also make each person's "Talk" prompt (default off). Returns the built models.
function TerritoryNpcBuilder.build(territoryName, spotsFolder, parent, withPrompt)
    local ref = reference()
    local made = {}
    for _, person in Data.People do
        if person.Territory == territoryName then
            local spot = spotsFolder:FindFirstChild(person.Spot)
            if spot and spot:IsA("BasePart") then
                table.insert(made, buildPerson(person, spot, parent, ref, withPrompt == true))
            else
                warn("TerritoryNpcBuilder: no spot " .. person.Spot .. " in " .. spotsFolder:GetFullName() .. " for " .. person.Name .. ", left out")
            end
        end
    end
    return made
end

return TerritoryNpcBuilder
