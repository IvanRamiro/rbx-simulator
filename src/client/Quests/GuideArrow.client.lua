-- The guide arrow (the owner, beta 2026-11-17: "The tutorial arrow must always be positioned above the player's chest, clearly
-- visible and properly aligned with the character"): a small gold 3D arrow that floats just above the player's chest, on the side
-- of what they should go to, and points at it (turning, and tilting up or down a little). It is for the beginner's path only:
--   * the quest's place (its Way in GameConfig.Quests, then its Then once the player has been there, as the quest's marker does:
--     QuestController);
--   * while the guardian is weak and they can take an egg (their CanTakeEgg), the nearest stand holding an egg their rank can carry;
--   * while they carry an egg, the way home (the guardian's SafeZone).
-- It hides at the place, while a window is open (Hud steps the dock aside), during the hatch cinematic, in first person, and when
-- the player hid the quest; it fades out for good once the beginner's quests are done (through "JadeBridge"). One model, drawn in
-- front of everything by its Highlight (the character never hides it), one RenderStepped. Reduced Effects: no bob, no pulse.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local UiTheme = require(UI:WaitForChild("UiTheme"))

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

local GOLD = UiTheme.Colors.Highlight
local CORE = Color3.fromRGB(255, 184, 52) -- the neon's own colour: deeper than the HUD's gold, which neon washed to white
local RIM = Color3.fromRGB(255, 246, 214)
local HEIGHT_OVER_CHEST = 0.45 -- studs over the chest's top
local OUT = 2.3               -- studs out from the chest's middle, toward the place
local MAX_TILT = math.rad(30) -- it tilts toward a place above or below, at most this
local WAY_NEAR = 25           -- studs: at a quest's place it hides (the quest's own marker goes there too)
local THEN_REACHED = 60       -- studs from a Way that count as having been there (QuestController's WAY_MARKER_NEAR)
local STAND_NEAR = 7          -- studs from a stand: its prompt has taken over
local FADE = 5                -- alpha per second

-- ---------- the arrow ----------
-- It points along its -Z: a square shaft and a head of four wedges in a cross, so it reads as an arrow from any side.
local model = Instance.new("Model")
model.Name = "GuideArrow"
local function piece(class, size, cframe)
    local part = Instance.new(class)
    part.Size = size
    part.CFrame = cframe
    part.Material = Enum.Material.Neon
    part.Color = CORE
    part.CanCollide, part.CanQuery, part.CanTouch = false, false, false
    part.CastShadow = false
    part.Massless = true
    part.Anchored = false
    part.Parent = model
    return part
end
local SHAFT, HEAD, WING, THICK = 1.0, 1.0, 0.62, 0.2
local SHAFT_FROM_MIDDLE = 0.5 -- the arrow runs from -0.95 (its tip) to 1.05: the shaft's middle is this far behind the arrow's
local shaft = piece("Part", Vector3.new(0.3, 0.3, SHAFT), CFrame.new(0, 0, SHAFT / 2 + 0.05))
shaft.Name = "Shaft"
shaft.Anchored = true
model.PrimaryPart = shaft
-- a wedge's slope runs from its back (+Z, full height) down to its front: laid on its side, its low edge on the arrow's middle
-- line and its tall end out to one side, two make the head flat and two more stand across it
local headZ = -HEAD / 2 + 0.05
for _, side in {
    { Vector3.new(0, -1, 0), Vector3.new(1, 0, 0) },  -- right
    { Vector3.new(0, 1, 0), Vector3.new(-1, 0, 0) },  -- left
    { Vector3.new(1, 0, 0), Vector3.new(0, 1, 0) },   -- up
    { Vector3.new(-1, 0, 0), Vector3.new(0, -1, 0) }, -- down
} do
    local across, out = side[1], side[2]
    local wedge = piece("WedgePart", Vector3.new(THICK, WING, HEAD), CFrame.fromMatrix(out * WING / 2 + Vector3.new(0, 0, headZ), across, out))
    wedge.Name = "Head"
    local weld = Instance.new("Weld")
    weld.Part0, weld.Part1 = shaft, wedge
    weld.C0 = shaft.CFrame:Inverse() * wedge.CFrame
    weld.Parent = wedge
end
local glow = Instance.new("Highlight") -- drawn over everything, so the character never hides it
glow.FillColor = GOLD
glow.OutlineColor = RIM
glow.DepthMode = Enum.HighlightDepthMode.AlwaysOnTop
glow.Adornee = model
glow.Parent = model
local parts = {}
for _, part in model:GetChildren() do
    if part:IsA("BasePart") then
        table.insert(parts, part)
    end
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

-- The place to point at and how near counts as there; nil when there is none right now.
local function target(step, from)
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
local facing = nil -- the rotation shown, eased toward the goal
local connection

local shownAlpha = -1
local function setAlpha(value)
    if value == shownAlpha then
        return
    end
    shownAlpha = value
    for _, part in parts do
        part.Transparency = 1 - value * 0.95
    end
    glow.FillTransparency = 1 - value * 0.35
    glow.OutlineTransparency = 1 - value * 0.9
    glow.Enabled = value > 0.01
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
    return player:GetAttribute("SettingShowQuest") == false
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
    local toward = if goal then goal - chest.Position else nil
    local across = toward and flat(toward)
    if not (across and across.Magnitude > 0.05) then
        return
    end
    local still = player:GetAttribute("SettingReducedEffects") == true
    local now = os.clock()
    local bob = if still then 0 else 0.16 * math.sin(now * 2.6)
    local centre = chest.Position + Vector3.new(0, chest.Size.Y / 2 + HEIGHT_OVER_CHEST + bob, 0) + across.Unit * OUT
    local tilt = math.clamp(math.atan2(toward.Y, across.Magnitude), -MAX_TILT, MAX_TILT)
    local aim = CFrame.lookAt(Vector3.zero, across.Unit) * CFrame.Angles(tilt, 0, 0)
    facing = if facing then facing:Lerp(aim, 1 - math.exp(-12 * dt)) else aim
    -- a small push toward the place, so it reads as "this way"
    local push = if still then 0 else 0.12 * math.sin(now * 4)
    shaft.CFrame = CFrame.new(centre) * facing * CFrame.new(0, 0, SHAFT_FROM_MIDDLE - push)
    if not still then
        glow.FillTransparency = 1 - alpha * (0.3 + 0.1 * math.sin(now * 3))
    end
end)
