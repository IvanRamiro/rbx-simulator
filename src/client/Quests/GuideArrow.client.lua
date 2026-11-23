-- The guide arrow (the owner, beta 2026-11-17: "The tutorial arrow must always be positioned above the player's chest, clearly
-- visible and properly aligned with the character"; 2026-11-23: "choose a better guiding arrow ... something like a multiple arrow showing the directions", then "the arrow
-- line that continue moving towards your destination"): a line of gold chevrons (">>>") laid on the ground from just ahead of the player toward what they should go to,
-- up to 64 studs of it (and no further than the place), each one sliding along the line toward the place, fading in as it leaves the player and out at the line's far
-- end, so the whole line flows toward the destination. Each chevron stands on the ground under it (a ray down, so a slope or a stair carries the line up with it; over a
-- gap it runs level to the place) and always lies flat and level, pointing along the line (it never rolls or pitches). It is for the beginner's path only:
--   * before anything else, for a player who has not yet talked to Seren the Guide (their GuideMet setting is false: World/GuideService; the owner, 2026-11-23: "you can guide
--     them to talk with the NPC"): Seren herself, on the spawn plaza, until they stand by her;
--   * the quest's place (its Way in GameConfig.Quests, then its Then once the player has been there, as the quest's marker does:
--     QuestController);
--   * while the guardian is weak and they can take an egg (their CanTakeEgg), the nearest stand holding an egg their rank can carry;
--   * while they carry an egg, the way home (the guardian's SafeZone).
-- It hides at the place, while a window is open (Hud steps the dock aside), during the hatch cinematic, in first person, and when
-- the player hid the quest; it fades out for good once the beginner's quests are done (through "JadeBridge"). One model of 21 chevrons (neon parts, no script of its own),
-- one RenderStepped. Reduced Effects: the line stands still.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))

local player = Players.LocalPlayer
local QUESTS = GameConfig.Quests

-- the beginner's path: every quest up to and including the walk to the second island
local LAST_STEP = #QUESTS
for index, quest in QUESTS do
    if quest.Id == "JadeBridge" then
        LAST_STEP = index
        break
    end
end

local CORE = Color3.fromRGB(255, 184, 52) -- the neon's own colour: deeper than the HUD's gold, which neon washed to white
local START = 4.0            -- studs from the player to where the line begins
local GAP = 4.2              -- studs between one chevron and the next
local REACH = 64             -- the longest the line runs
local SPEED = 6              -- studs a second the chevrons slide toward the place
local LIFT = 0.6             -- studs a chevron lies over the ground under it
local CHEVRONS = math.ceil(REACH / GAP) + 2
local WAY_NEAR = 25           -- studs: at a quest's place it hides (the quest's own marker goes there too)
local THEN_REACHED = 60       -- studs from a Way that count as having been there (QuestController's WAY_MARKER_NEAR)
local STAND_NEAR = 7          -- studs from a stand: its prompt has taken over
local FADE = 5                -- alpha per second

-- ---------- the arrow ----------
-- A chevron points along its -Z: two flat bars meeting at the tip and opening backward (a ">" seen from above), so it reads from behind and above as a clear arrowhead.
local model = Instance.new("Model")
model.Name = "GuideArrow"
local BAR_LEN, BAR_W, BAR_THICK, BAR_ANGLE = 3.4, 0.8, 0.16, math.rad(30)
local chevrons = {} -- [index] = { parts = { left, right }, local_ = their frames in the chevron's own, shown = the light last set }
local function bar(parent, side)
    local direction = Vector3.new(side * math.sin(BAR_ANGLE), 0, math.cos(BAR_ANGLE))
    local centre = direction * (BAR_LEN / 2 - 0.12) + Vector3.new(0, 0, -0.12) -- (a touch forward, so the bars cross at the tip and leave no notch)
    local part = Instance.new("Part")
    part.Name = "Bar"
    part.Size = Vector3.new(BAR_W, BAR_THICK, BAR_LEN)
    part.Material = Enum.Material.Neon
    part.Color = CORE
    part.CanCollide, part.CanQuery, part.CanTouch = false, false, false
    part.CastShadow = false
    part.Massless = true
    part.Anchored = true
    part.Transparency = 1
    part.CFrame = CFrame.lookAt(centre, centre + direction) -- (local until the chevron is placed: the placement multiplies this in)
    part.Parent = parent
    return part
end
for index = 1, CHEVRONS do
    local left, right = bar(model, -1), bar(model, 1)
    chevrons[index] = { parts = { left, right }, local_ = { left.CFrame, right.CFrame }, shown = 1 }
end

-- ---------- where it points ----------
local wayGround = {} -- [quest step] = the ground's height at its Way (false: none found)
local reachedWay = {} -- [quest step] = true once the player has been at its Way
local function groundAt(step, x, z)
    if wayGround[step] == nil then
        local params = RaycastParams.new()
        params.FilterType = Enum.RaycastFilterType.Exclude
        params.FilterDescendantsInstances = { player.Character, model }
        local hit = Workspace:Raycast(Vector3.new(x, 1500, z), Vector3.new(0, -3000, 0), params)
        wayGround[step] = if hit then hit.Position.Y else false
    end
    return wayGround[step] or nil
end

local function flat(v)
    return Vector3.new(v.X, 0, v.Z)
end

-- the nearest stand of that guardian's island holding an egg this player's rank can carry
local function standToTake(guardianId, from)
    local config = GameConfig.Guardians[guardianId]
    local islands = config and Workspace:FindFirstChild("FloatingIslands")
    local island = islands and islands:FindFirstChild(config.Island)
    local folder = island and island:FindFirstChild("EggStands")
    local rankName = Ranks.getPlayerRankName(player)
    local best, bestDistance = nil, math.huge
    for _, stand in if folder then folder:GetChildren() else {} do
        local egg = GameConfig.Eggs[stand:GetAttribute("EggId") or ""]
        local pedestal = stand:FindFirstChild("Pedestal")
        if egg and pedestal and rankName ~= "" and Ranks.isAtLeast(rankName, egg.RequiredRank) then
            local distance = (pedestal.Position - from).Magnitude
            if distance < bestDistance then
                best, bestDistance = pedestal.Position, distance
            end
        end
    end
    return best
end

-- Seren the Guide's place (her model is tagged HubNpc and named Guide: WorldBuilder.buildHubNpcs), or nil while she is not loaded
local seren = nil
local function serenPosition()
    if seren and seren.Parent then
        return seren.Position
    end
    for _, model in CollectionService:GetTagged("HubNpc") do
        if model.Name == "Guide" then
            local root = model:FindFirstChild("HumanoidRootPart")
            if root and root:IsA("BasePart") then
                seren = root
                return root.Position
            end
        end
    end
    return nil
end

-- The place to point at and how near counts as there; nil when there is none right now.
local function target(step, from)
    if player:GetAttribute("SettingGuideMet") == false then
        local at = serenPosition()
        return if at then at + Vector3.new(0, 1, 0) else nil, 9
    end
    local carrying = player:GetAttribute("CarryingGuardian")
    if carrying then
        local guardians = Workspace:FindFirstChild("Guardians")
        for _, guardian in if guardians then guardians:GetChildren() else {} do
            if guardian:GetAttribute("GuardianId") == carrying then
                local home = guardian:GetAttribute("SafeZone")
                return if typeof(home) == "Vector3" then home else nil, WAY_NEAR
            end
        end
        return nil
    end
    local canTake = player:GetAttribute("CanTakeEgg")
    if canTake then
        local stand = standToTake(canTake, from)
        if stand then
            return stand, STAND_NEAR
        end
    end
    local way = QUESTS[step] and QUESTS[step].Way
    if not way then
        return nil
    end
    if way.Then and flat(Vector3.new(way[2], 0, way[3]) - from).Magnitude < THEN_REACHED then
        reachedWay[step] = true
    end
    if way.Then and reachedWay[step] then
        return Vector3.new(way.Then[2], way.Then[3], way.Then[4]), 10
    end
    local ground = groundAt(step, way[2], way[3])
    return if ground then Vector3.new(way[2], ground + 3, way[3]) else nil, WAY_NEAR
end

-- ---------- each frame ----------
local alpha = 0
local lastGoal = nil -- where it was last pointed (it stays so while it fades out)
local connection

-- one chevron's light (0 to 1, with the line's fade and the chevron's own fade in and out already in it)
local function lightChevron(chevron, value)
    value = math.clamp(value, 0, 1)
    if math.abs(value - chevron.shown) < 0.01 then
        return
    end
    chevron.shown = value
    for _, part in chevron.parts do
        part.Transparency = 1 - value * 0.92
    end
end
local function setAlpha(value)
    if value <= 0 then
        for _, chevron in chevrons do
            lightChevron(chevron, 0)
        end
    end
end
setAlpha(0)
model.Parent = Workspace

local function hiddenByScreen()
    if not Hud.Dock.Visible then -- a window is open (Hud steps the dock aside)
        return true
    end
    local cinema = player.PlayerGui:FindFirstChild("HatchCinema")
    if cinema and cinema.Enabled then
        return true
    end
    -- (a player who hid the quest still gets led to Seren: that is no quest)
    return player:GetAttribute("SettingShowQuest") == false and player:GetAttribute("SettingGuideMet") ~= false
end

connection = RunService.RenderStepped:Connect(function(dt)
    local step = player:GetAttribute("QuestStep")
    local finished = typeof(step) == "number" and step > LAST_STEP
    local character = player.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    local chest = character and (character:FindFirstChild("UpperTorso") or character:FindFirstChild("Torso")) or root
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local camera = Workspace.CurrentCamera
    local head = character and character:FindFirstChild("Head")

    local goal, near = nil, 0
    if not finished and typeof(step) == "number" and root and chest and camera and humanoid and humanoid.Health > 0 then
        goal, near = target(step, root.Position)
    end
    local show = goal ~= nil and flat(goal - root.Position).Magnitude > near and not hiddenByScreen()
        and not (head and (camera.CFrame.Position - head.Position).Magnitude < 1.5) -- first person: it would sit in the eyes
    alpha = math.clamp(alpha + (if show then dt else -dt) * FADE, 0, 1)
    if finished and alpha <= 0 then -- the beginner's path is done: gone for good
        connection:Disconnect()
        model:Destroy()
        return
    end
    setAlpha(alpha)
    if alpha <= 0 or not (root and chest) then
        return
    end
    -- (while it fades out it stays where it was last pointed)
    local aim = goal or lastGoal
    lastGoal = aim
    local across = aim and flat(aim - chest.Position)
    if not (aim and across and across.Magnitude > 0.05) then
        return
    end
    local still = player:GetAttribute("SettingReducedEffects") == true
    local now = os.clock()
    local reach = across.Magnitude
    local flatDirection = across.Unit
    local feet = Vector3.new(root.Position.X, root.Position.Y - 2.6, root.Position.Z) -- (their feet's height: where a stretch with no ground runs level from)
    local last = math.min(REACH, reach - 1) -- the line's far end
    local slide = if still then 0 else (now * SPEED) % GAP
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = { character, model }
    params.RespectCanCollide = true -- (only what a body can stand on: terrain, floors, bridges; not a leaf or a banner)
    for index, chevron in chevrons do
        local distance = START + slide + (index - 1) * GAP
        local light = alpha * math.clamp((distance - START) / GAP, 0, 1) * math.clamp((last - distance) / (GAP * 2), 0, 1)
        if light <= 0 or distance > last then
            lightChevron(chevron, 0)
            continue
        end
        lightChevron(chevron, light)
        local x, z = root.Position.X + flatDirection.X * distance, root.Position.Z + flatDirection.Z * distance
        local hit = Workspace:Raycast(Vector3.new(x, root.Position.Y + 14, z), Vector3.new(0, -34, 0), params)
        local y = if hit then hit.Position.Y else feet.Y + (aim.Y - feet.Y) * math.clamp(distance / math.max(reach, 1), 0, 1)
        local at = Vector3.new(x, y + LIFT, z)
        -- level and flat on the ground, pointing along the line (the owner, 2026-11-23: "it was actually tilting", then "just the one in the flat ground": the version that
        -- banked each chevron toward the camera read as slanted; a chevron never rolls or pitches)
        local frame = CFrame.fromMatrix(at, flatDirection:Cross(Vector3.yAxis).Unit, Vector3.yAxis, -flatDirection)
        chevron.parts[1].CFrame = frame * chevron.local_[1]
        chevron.parts[2].CFrame = frame * chevron.local_[2]
    end
end)
