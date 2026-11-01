-- One guardian encounter (design doc section 7, GameConfig.Guardians): the guardian, its health,
-- states and attacks, and the egg it guards up to a thief's egg inventory. GuardianService makes one
-- per configured guardian and steps it every frame.
--
-- States (the model's "State" attribute; clients animate it and show it on the health bar):
--   Dormant    a statue over its egg; a player within EngageRadius, or a strike, wakes it.
--   Guardian   awake at its lair over its egg; it sweeps players in front and sends waves round it.
--   Weakened   below WeakenedAt of its health: the egg can be taken (set down at Egg.Offered if it
--              is held out of reach). Attacks come slower. Health never falls below 1.
--   Enraged    the egg is taken: it chases the thief, pouncing and striking, and takes no damage.
--   Returning  walking back to its lair: the egg came back to it, or was secured.
--   Resting    the egg was secured: it sleeps without one for RespawnTime.
-- With nobody near for CalmAfter seconds, a Guardian or Weakened one heals and sleeps.
--
-- The egg (the model's "Egg" attribute, for inspecting in Studio): Guarded -> Available ->
-- Carried <-> Dropped, then None once secured (until the guardian respawns with a new one). Every
-- step is checked here; repeated requests are ignored. Only its thief can recover a dropped egg,
-- within DropTime; after that it returns to the lair. It also returns if the thief leaves the
-- server or the guardian's island, or carries it longer than MAX_CARRY without securing it.
--
-- Guardians never kill: every attack knocks players back (GuardianEvent "Knock" to that player's
-- client, which owns its character), and a knocked-back thief drops the egg.
--
-- Clients get every action as GuardianEvent:FireAllClients(model, action, ...):
--   "Awaken" | "Weaken" | <a Sweep's name> windUp | <a Wave's name> windUp radius waveSpeed arc |
--   <a Pounce's name> windUp air from to | "Land" position | "Steal" position | "Drop" position |
--   "Recover" | "Secure" position | "Return"
-- and the thief alone "Secured" eggId | "BagFull".
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local EggInventory = require(script.Parent.Parent:WaitForChild("Pets"):WaitForChild("EggInventory"))
local EggModel = require(script.Parent:WaitForChild("EggModel"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))
local WorldConfig = require(script.Parent.Parent:WaitForChild("World"):WaitForChild("WorldConfig"))

local FLAT = Vector3.new(1, 0, 1)
local DECIDE_EVERY = 0.1        -- seconds between decisions; movement runs every frame
local CHASE_STOP = 13           -- it stops this far from its prey (its face is ~20 studs ahead of the chest)
local KNOCK_IMMUNITY = 0.6      -- seconds
local TELEPORT_JUMP = 40        -- a thief moving this far in one frame was returned by the world
local SANCTUARY_MARGIN = 12     -- studs it keeps outside its safe zone's edge
local TAKE_GRACE = 1.5          -- seconds a fresh thief can't be knocked: a blow already on its way would feel random
local EGG_PROMPT_DISTANCE = 12
local POUNCE_HEIGHT = 9
local POUNCE_LEAD = 0.85        -- how far ahead it aims: a straight runner is caught, one who turns or dashes is not
local MAX_CARRY = 120           -- seconds a thief may carry the egg; a thief hiding out of reach can't hold the guardian forever

local Guardian = {}
Guardian.__index = Guardian

local eggsFolder = workspace:FindFirstChild("GuardianEggs") or Instance.new("Folder")
eggsFolder.Name = "GuardianEggs"
eggsFolder.Parent = workspace

local groundParams = RaycastParams.new()
groundParams.FilterType = Enum.RaycastFilterType.Include
groundParams.FilterDescendantsInstances = { workspace.Terrain, workspace:WaitForChild(WorldConfig.FolderName) }

local function flat(v)
    return v * FLAT
end

-- The ground under a point, casting down from `fromY`. Callers start just above the step they
-- allow, so canopies overhead aren't taken for ground (nor rocks it walks through: a ray starting
-- inside them misses them). nil over a drop.
local function groundAt(position, fromY)
    local result = workspace:Raycast(Vector3.new(position.X, fromY, position.Z), Vector3.new(0, -60, 0), groundParams)
    return result and result.Position
end

local function rootOf(player)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if humanoid and root and humanoid.Health > 0 then
        return root, humanoid
    end
    return nil
end

-- Whether the player's feet are on something (the server's own check: a ray from the root).
local function isGrounded(root, humanoid)
    local reach = humanoid.HipHeight + root.Size.Y / 2 + 1.5
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = { root.Parent, eggsFolder }
    return workspace:Raycast(root.Position, Vector3.new(0, -reach, 0), params) ~= nil
end

-- The best of the guardian's eggs the player's rank opens (its Eggs are in rising rank order).
local function rewardFor(config, player)
    local rankName = Ranks.getPlayerRankName(player)
    local best = config.Eggs[1]
    for _, eggId in config.Eggs do
        if Ranks.isAtLeast(rankName, GameConfig.Eggs[eggId].RequiredRank) then
            best = eggId
        end
    end
    return best
end

function Guardian.new(id, config, source, folder)
    local self = setmetatable({}, Guardian)
    self.id = id
    self.config = config
    local island = WorldConfig.Islands[config.Island]
    self.islandCentre = island.Centre
    self.islandRadius = island.Radius

    local frame = WorldConfig.frame(config.Island)
    local at = frame:PointToWorldSpace(config.Lair)
    local ground = groundAt(at, at.Y + 10)
    at = Vector3.new(at.X, if ground then ground.Y else at.Y, at.Z)
    self.lair = CFrame.lookAt(at, at + flat(frame:PointToWorldSpace(config.Facing) - at))
    self.facing = self.lair.Rotation -- TurnsToFace guardians change this
    local zone = config.SafeZone
    self.safeCentre = frame:PointToWorldSpace(zone.Centre)

    local model = source:Clone()
    model.Name = id
    model.ModelStreamingMode = Enum.ModelStreamingMode.Persistent
    model:SetAttribute("GuardianId", id)
    model:SetAttribute("MaxHealth", config.MaxHealth)
    model:SetAttribute("Health", config.MaxHealth)
    model:SetAttribute("HitRadius", config.HitRadius)
    model:SetAttribute("TargetId", 0)
    model:SetAttribute("SafeZone", self.safeCentre) -- clients show the thief the way
    model:PivotTo(self.lair)
    CollectionService:AddTag(model, GameConfig.GuardianTag)
    CollectionService:AddTag(model, GameConfig.Combat.TargetTag)
    self.model = model

    -- server-owned physics movers, so every client sees it move smoothly
    local root = model.PrimaryPart
    root.Anchored = false
    root.RootPriority = 127
    local mover = Instance.new("Attachment")
    mover.Name = "Mover"
    mover.CFrame = root.CFrame:ToObjectSpace(self.lair) -- the model's origin, on the ground
    mover.Parent = root
    local align = Instance.new("AlignPosition")
    align.Mode = Enum.PositionAlignmentMode.OneAttachment
    align.Attachment0 = mover
    align.MaxForce = math.huge
    align.MaxVelocity = config.WalkSpeed
    align.Responsiveness = 40
    align.Position = self.lair.Position
    align.Parent = root
    local turn = Instance.new("AlignOrientation")
    turn.Mode = Enum.OrientationAlignmentMode.OneAttachment
    turn.Attachment0 = mover
    turn.MaxTorque = math.huge
    turn.MaxAngularVelocity = math.rad(config.TurnSpeed)
    turn.Responsiveness = 30
    turn.CFrame = self.lair.Rotation
    turn.Parent = root
    self.root, self.align, self.turn = root, align, turn

    model.Parent = folder
    root:SetNetworkOwner(nil)

    -- its longest sweep or wave: an enraged guardian attacks whoever is within it
    self.reach = 0
    for _, spec in config.Attacks do
        if spec.Kind ~= "Pounce" then
            self.reach = math.max(self.reach, spec.Range or spec.Radius or 0)
        end
    end
    self.health = config.MaxHealth
    self.cooldowns = {}
    self.busyUntil = 0
    self.nextDecision = 0
    self.lastEngaged = 0
    self.knocked = {}
    self.egg = { state = "None" }
    self:setState("Dormant")
    self:guardEgg()
    return self
end

-- State, health, and what clients see -------------------------------------------------------------

function Guardian:setState(state)
    self.state = state
    self.stateSince = os.clock()
    self.model:SetAttribute("State", state)
    -- only an awake guardian at its lair (or a sleeping one, which a strike wakes) can be struck
    self.model:SetAttribute("Invulnerable", not (state == "Dormant" or state == "Guardian" or state == "Weakened"))
end

function Guardian:broadcast(action, ...)
    RemoteEvents.GuardianEvent:FireAllClients(self.model, action, ...)
end

function Guardian:setHealth(health)
    self.health = math.clamp(health, 1, self.config.MaxHealth)
    self.model:SetAttribute("Health", math.ceil(self.health))
end

function Guardian:heal()
    self:setHealth(self.config.MaxHealth)
end

function Guardian:awaken()
    self:setState("Guardian")
    self.busyUntil = os.clock() + 1.6 -- its waking roar
    self.lastEngaged = os.clock()
    self:broadcast("Awaken")
end

function Guardian:weaken()
    self:setState("Weakened")
    self.busyUntil = os.clock() + 1.8 -- it falters
    self:broadcast("Weaken")
    if self.egg.state == "Guarded" then
        self:setEggState("Available")
    end
end

function Guardian:sleep()
    self:heal()
    self:setState("Dormant")
    self.model:SetAttribute("TargetId", 0)
    if self.egg.state == "Available" then
        self:setEggState("Guarded")
    end
end

-- A strike from a player (CombatService, through Combat.Hit).
function Guardian:onHit(player, damage)
    if self.model:GetAttribute("Invulnerable") then
        return
    end
    self.lastEngaged = os.clock()
    if self.state == "Dormant" then
        self:awaken()
    end
    self:setHealth(self.health - damage)
    if self.state == "Guardian" and self.health < self.config.MaxHealth * self.config.WeakenedAt then
        self:weaken()
    end
end

-- The egg ---------------------------------------------------------------------------------------

function Guardian:setEggState(state)
    local egg = self.egg
    if state ~= "Guarded" then
        self:releaseEgg()
    end
    egg.state = state
    self.model:SetAttribute("Egg", state)
    if egg.model then
        egg.model:SetAttribute("State", state) -- clients find a dropped egg by this
    end
    -- a guardian that holds its egg out of reach sets it down when it falters (Egg.Offered)
    local spot = self.config.Egg
    if egg.model and spot.Offered and (state == "Available" or state == "Guarded") then
        egg.model:PivotTo(self:home() * CFrame.new(if state == "Available" then spot.Offered else spot.Under))
    end
    if egg.prompt then
        egg.prompt.Enabled = state == "Available" or state == "Dropped"
        egg.prompt.ActionText = if state == "Dropped" then "Recover" else "Steal"
    end
end

local function anchorEgg(model, anchored)
    for _, part in model:GetDescendants() do
        if part:IsA("BasePart") then
            part.Anchored = anchored and part == model.PrimaryPart
        end
    end
end

function Guardian:makeEgg(eggId, height)
    local egg = self.egg
    if egg.model then
        egg.model:Destroy()
    end
    egg.held = nil
    local model = EggModel.build(eggId, height)
    model.Name = self.id .. "_Egg"
    model.ModelStreamingMode = Enum.ModelStreamingMode.Persistent
    model:SetAttribute("GuardianId", self.id)
    local prompt = Instance.new("ProximityPrompt")
    prompt.KeyboardKeyCode = Enum.KeyCode.F -- as on the egg stands (E is cultivation)
    prompt.HoldDuration = 0.5
    prompt.MaxActivationDistance = EGG_PROMPT_DISTANCE
    prompt.RequiresLineOfSight = false
    prompt.ObjectText = GameConfig.Eggs[eggId].DisplayName
    prompt.Enabled = false
    prompt.Parent = model.PrimaryPart
    prompt.Triggered:Connect(function(player)
        self:onEggPrompt(player)
    end)
    egg.model, egg.prompt, egg.eggId = model, prompt, eggId
    return model
end

-- A fresh guarded egg, always the island's first (a thief is given the best their rank opens).
function Guardian:guardEgg()
    local config = self.config
    local model = self:makeEgg(config.Eggs[1], config.Egg.Height)
    anchorEgg(model, true)
    model:PivotTo(self:home() * CFrame.new(config.Egg.Under))
    model.Parent = eggsFolder
    self.egg.owner = nil
    self:setEggState(if self.state == "Weakened" then "Available" else "Guarded")
end

function Guardian:clearThief()
    local owner = self.egg.owner
    if owner and owner.Parent then
        owner:SetAttribute("CarryingEgg", nil)
        owner:SetAttribute("CarryingGuardian", nil)
    end
    self.egg.owner = nil
end

-- Welds the egg above the thief's head.
function Guardian:carry(player)
    local root = rootOf(player)
    local head = player.Character:FindFirstChild("Head") or root
    local egg = self.egg
    anchorEgg(egg.model, false)
    local height = self.config.Egg.CarriedHeight
    local body = egg.model.PrimaryPart
    local offset = CFrame.new(0, head.Size.Y / 2 + height / 2 + 0.6, 0)
    body.CFrame = head.CFrame * offset * body.PivotOffset:Inverse()
    local weld = Instance.new("Weld")
    weld.Name = "CarryWeld"
    weld.Part0, weld.Part1 = head, body
    weld.C0 = offset * body.PivotOffset:Inverse()
    weld.Parent = body
    egg.owner = player
    egg.takenAt = os.clock()
    egg.lastGrounded = nil
    egg.lastPosition = root.Position
    self.knocked[player] = os.clock() + TAKE_GRACE
    player:SetAttribute("CarryingEgg", egg.eggId)
    player:SetAttribute("CarryingGuardian", self.id)
    self:setEggState("Carried")
end

function Guardian:onEggPrompt(player)
    local egg = self.egg
    local root = rootOf(player)
    if not root or player:GetAttribute("IsFlying") == true or player:GetAttribute("CarryingEgg") then
        return
    end
    if (root.Position - egg.model:GetPivot().Position).Magnitude > EGG_PROMPT_DISTANCE + 4 then
        return
    end
    if egg.state == "Available" and self.state == "Weakened" then
        -- the egg becomes the one this thief earns
        local position = egg.model:GetPivot().Position
        self:makeEgg(rewardFor(self.config, player), self.config.Egg.CarriedHeight)
        self:carry(player)
        self.egg.model.Parent = eggsFolder
        self:setState("Enraged")
        -- it roars, then its first move is a leap at the thief
        self.busyUntil = os.clock() + 1.2
        for name in self:attacksOf("Pounce") do
            self.cooldowns[name] = self.busyUntil
        end
        self.lastEngaged = os.clock()
        self:broadcast("Steal", position)
    elseif egg.state == "Dropped" and egg.owner == player then
        self:carry(player)
        self:broadcast("Recover")
    end
end

-- A clear, reachable spot near `near` for a dropped egg: on the ground, on the island, out of the
-- guardian's body; the front of the lair if there is none.
function Guardian:dropSpot(near)
    local offset = flat(near - self.islandCentre)
    local limit = self.islandRadius - 12
    if offset.Magnitude > limit then
        offset = offset.Unit * limit
    end
    local point = self.islandCentre + offset + Vector3.new(0, near.Y - self.islandCentre.Y, 0)
    local fromGuardian = flat(point - self.root.Position)
    if fromGuardian.Magnitude < 18 then
        point = self.root.Position + (if fromGuardian.Magnitude > 0.1 then fromGuardian.Unit else self.root.CFrame.LookVector * FLAT) * 18
            + Vector3.new(0, point.Y - self.root.Position.Y, 0)
    end
    local ground = groundAt(point, point.Y)
    if not ground then
        ground = groundAt((self.lair * CFrame.new(0, 0, -34)).Position, self.lair.Y + 10)
    end
    return ground or self.lair.Position
end

function Guardian:dropEgg(near)
    local egg = self.egg
    if egg.state ~= "Carried" then
        return
    end
    local spot = self:dropSpot(near)
    local weld = egg.model.PrimaryPart:FindFirstChild("CarryWeld")
    if weld then
        weld:Destroy()
    end
    anchorEgg(egg.model, true)
    egg.model:PivotTo(CFrame.new(spot + Vector3.new(0, self.config.Egg.CarriedHeight / 2, 0)))
    egg.model:SetAttribute("OwnerUserId", egg.owner.UserId)
    egg.dropUntil = os.clock() + self.config.DropTime
    egg.model:SetAttribute("DropUntil", workspace:GetServerTimeNow() + self.config.DropTime)
    local owner = egg.owner
    self:clearThief()
    egg.owner = owner -- still theirs to recover
    self:setEggState("Dropped")
    self:broadcast("Drop", spot)
end

-- The egg goes back to the guardian and it walks home.
function Guardian:returnEgg()
    self:clearThief()
    self:guardEgg()
    self:setState("Returning")
    self:broadcast("Return")
end

function Guardian:secure()
    local egg = self.egg
    local player = egg.owner
    local position = egg.model:GetPivot().Position
    if not EggInventory.grant(player, egg.eggId) then
        RemoteEvents.GuardianEvent:FireClient(player, self.model, "BagFull")
        self:returnEgg()
        return
    end
    PlayerData.saveSoon(player)
    RemoteEvents.GuardianEvent:FireClient(player, self.model, "Secured", egg.eggId)
    self:clearThief()
    egg.model:Destroy()
    egg.model, egg.prompt, egg.eggId = nil, nil, nil
    self:setEggState("None")
    self:setState("Returning")
    self:broadcast("Secure", position)
end

-- Every frame while the egg is carried: secured in the safe zone; dropped if the thief is gone,
-- dead or returned by the world (falling off the island); back to the guardian if they leave its
-- island or keep it past MAX_CARRY.
function Guardian:watchThief()
    local egg = self.egg
    local player = egg.owner
    local root, humanoid = rootOf(player)
    if not root then
        if egg.lastGrounded then
            self:dropEgg(egg.lastGrounded)
        else
            self:returnEgg()
        end
        return
    end
    local position = root.Position
    if egg.lastPosition and (position - egg.lastPosition).Magnitude > TELEPORT_JUMP then
        self:dropEgg(egg.lastGrounded or egg.lastPosition)
        return
    end
    egg.lastPosition = position
    if self:inSafeZone(position) then
        self:secure()
        return
    end
    local now = os.clock()
    if flat(position - self.islandCentre).Magnitude > self.islandRadius + 10 or now - egg.takenAt > MAX_CARRY then
        self:returnEgg()
        return
    end
    if not egg.nextGroundCheck or now >= egg.nextGroundCheck then
        egg.nextGroundCheck = now + 0.2
        if isGrounded(root, humanoid) then
            egg.lastGrounded = position
        end
    end
end

function Guardian:onPlayerRemoving(player)
    if self.egg.owner == player then
        self:returnEgg()
    end
    self.knocked[player] = nil
end

-- Attacks ---------------------------------------------------------------------------------------

function Guardian:inSafeZone(position, margin)
    return flat(position - self.safeCentre).Magnitude <= self.config.SafeZone.Radius + (margin or 0)
        and math.abs(position.Y - self.safeCentre.Y) < 14
end

-- Knocks a player back from `origin` (no damage: guardians never kill); a thief drops the egg.
-- Nobody in the safe zone is touched, nor anyone on a flying sword (the knock's stagger would hand
-- their character back to the Humanoid mid-flight; a thief can't fly, so no egg is at stake).
function Guardian:knock(player, origin, power)
    local root = rootOf(player)
    local now = os.clock()
    if not root or (self.knocked[player] and now < self.knocked[player]) or self:inSafeZone(root.Position)
        or player:GetAttribute("IsFlying") == true then
        return
    end
    self.knocked[player] = now + KNOCK_IMMUNITY
    local away = flat(root.Position - origin)
    away = if away.Magnitude > 0.1 then away.Unit else flat(self.root.CFrame.LookVector).Unit
    RemoteEvents.GuardianEvent:FireClient(player, self.model, "Knock", away * power + Vector3.new(0, power * 0.5, 0), self.config.Stagger)
    if self.egg.state == "Carried" and self.egg.owner == player then
        self:dropEgg(root.Position)
    end
end

function Guardian:ready(name)
    return os.clock() >= (self.cooldowns[name] or 0)
end

function Guardian:startCooldown(name)
    local spec = self.config.Attacks[name]
    local slowdown = if self.state == "Weakened" then self.config.WeakenedSlowdown else 1
    self.cooldowns[name] = os.clock() + spec.Cooldown * slowdown
end

-- The players near, nearest first: { player, root, distance (flat, from the chest) }.
function Guardian:playersNear(radius)
    local list = {}
    local centre = self.root.Position
    for _, player in Players:GetPlayers() do
        local root = rootOf(player)
        if root and math.abs(root.Position.Y - centre.Y) < 30 then
            local distance = flat(root.Position - centre).Magnitude
            if distance <= radius then
                table.insert(list, { player = player, root = root, distance = distance })
            end
        end
    end
    table.sort(list, function(a, b)
        return a.distance < b.distance
    end)
    return list
end

function Guardian:inFront(position, arc)
    local to = flat(position - self.root.Position)
    return to.Magnitude < 1 or to.Unit:Dot(flat(self.root.CFrame.LookVector).Unit) >= math.cos(math.rad(arc))
end

-- Attack kinds. Each guardian names its own attacks in GameConfig; clients get the attack's name
-- and the kind's arguments.

-- A Sweep knocks back whoever is within Range and Arc of its facing.
function Guardian:sweep(name)
    local spec = self.config.Attacks[name]
    self:startCooldown(name)
    self.busyUntil = os.clock() + spec.WindUp + 0.6
    self:broadcast(name, spec.WindUp)
    task.delay(spec.WindUp, function()
        if not self.model.Parent then
            return
        end
        for _, near in self:playersNear(spec.Range) do
            if self:inFront(near.root.Position, spec.Arc) then
                self:knock(near.player, self.root.Position, spec.Knockback)
            end
        end
    end)
end

-- A Wave rolls out along the ground to Radius, all round (Arc 180 or more) or within Arc of its
-- facing. Whoever is grounded when it passes is knocked back; a jump clears it.
function Guardian:wave(name)
    local spec = self.config.Attacks[name]
    local arc = spec.Arc or 180
    self:startCooldown(name)
    self.busyUntil = os.clock() + spec.WindUp + 0.5
    self:broadcast(name, spec.WindUp, spec.Radius, spec.WaveSpeed, arc)
    task.delay(spec.WindUp, function()
        if not self.model.Parent then
            return
        end
        local origin = self.root.Position
        local facing = flat(self.root.CFrame.LookVector).Unit
        local cosArc = math.cos(math.rad(arc))
        local start = os.clock()
        local passed = {}
        while self.model.Parent do
            local radius = (os.clock() - start) * spec.WaveSpeed
            for _, player in Players:GetPlayers() do
                local root, humanoid = rootOf(player)
                if root and not passed[player] then
                    local offset = flat(root.Position - origin)
                    local distance = offset.Magnitude
                    if distance <= radius then
                        passed[player] = true
                        local within = arc >= 180 or distance < 1 or offset.Unit:Dot(facing) >= cosArc
                        if within and distance <= spec.Radius and math.abs(root.Position.Y - origin.Y) < 10 and isGrounded(root, humanoid) then
                            self:knock(player, origin, spec.Knockback)
                        end
                    end
                end
            end
            if radius > spec.Radius then
                break
            end
            task.wait()
        end
    end)
end

-- A Pounce leaps onto where the thief is heading, committed at the wind-up, and lands with a shockwave.
function Guardian:pounce(name, targetRoot)
    local spec = self.config.Attacks[name]
    self:startCooldown(name)
    local from = self.root.Position
    local lead = targetRoot.Position + flat(targetRoot.AssemblyLinearVelocity) * (spec.WindUp + spec.Air) * POUNCE_LEAD
    local reach = flat(lead - from)
    if reach.Magnitude > spec.MaxRange then
        reach = reach.Unit * spec.MaxRange
    end
    local offset = flat(from + reach - self.islandCentre)
    if offset.Magnitude > self.islandRadius - 12 then
        offset = offset.Unit * (self.islandRadius - 12)
    end
    local landing = self.islandCentre + offset
    local keepOut = self.config.SafeZone.Radius + SANCTUARY_MARGIN
    local fromZone = flat(landing - self.safeCentre)
    if fromZone.Magnitude < keepOut then
        landing = self.safeCentre + (if fromZone.Magnitude > 0.1 then fromZone.Unit else flat(from - self.safeCentre).Unit) * keepOut
    end
    local ground = groundAt(landing, from.Y + 4) or groundAt(landing, from.Y + 25)
    if not ground then
        return
    end
    local launch = self:origin().Position
    self.busyUntil = os.clock() + spec.WindUp + spec.Air + 0.5
    self.leap = { name = name, from = launch, to = ground, start = os.clock() + spec.WindUp, air = spec.Air, height = spec.Height or POUNCE_HEIGHT }
    if flat(ground - launch).Magnitude > 0.5 then
        self.turn.CFrame = CFrame.lookAt(Vector3.zero, flat(ground - launch)).Rotation
    end
    self:broadcast(name, spec.WindUp, spec.Air, launch, ground)
end

function Guardian:land()
    local spec = self.config.Attacks[self.leap.name]
    local at = self.leap.to
    self.leap = nil
    self.align.Position = at
    self:broadcast("Land", at)
    for _, near in self:playersNear(spec.Radius) do
        self:knock(near.player, at, spec.Knockback)
    end
end

-- Its attacks of one kind, by name.
function Guardian:attacksOf(kind)
    local out = {}
    for name, spec in self.config.Attacks do
        if spec.Kind == kind then
            out[name] = spec
        end
    end
    return out
end

-- Movement --------------------------------------------------------------------------------------

-- Heads for `target` (a world point) at `speed`, stopping `stop` short of it, along the ground.
function Guardian:moveToward(target, speed, stop, dt)
    local here = self:origin().Position
    local to = flat(target - here)
    if to.Magnitude > 0.5 then
        self.turn.CFrame = CFrame.lookAt(Vector3.zero, to).Rotation
    end
    -- slack: it heads for a point `stop` short of the target, so it only nears that distance
    if to.Magnitude <= stop + 0.25 then
        self.align.Position = here
        return true
    end
    local step = math.min(to.Magnitude - stop, math.max(speed * dt * 4, 2))
    local point = here + to.Unit * step
    local offset = flat(point - self.islandCentre)
    if offset.Magnitude > self.islandRadius - 10 then
        point = self.islandCentre + offset.Unit * (self.islandRadius - 10) + Vector3.new(0, point.Y - self.islandCentre.Y, 0)
    end
    -- it walks round the sanctuary's rim, never into it
    local keepOut = self.config.SafeZone.Radius + SANCTUARY_MARGIN
    local fromZone = flat(point - self.safeCentre)
    if fromZone.Magnitude < keepOut then
        local away = if fromZone.Magnitude > 0.1 then fromZone.Unit else flat(here - self.safeCentre).Unit
        point = self.safeCentre + away * keepOut + Vector3.new(0, point.Y - self.safeCentre.Y, 0)
    end
    local ground = groundAt(point, here.Y + 3.5)
    self.align.MaxVelocity = speed
    self.align.Responsiveness = 40
    self.align.Position = if ground then ground else Vector3.new(point.X, here.Y, point.Z)
    return false
end

-- Where its origin (the ground under it) is now, and where it stands at its lair.
function Guardian:origin()
    return self.root.CFrame * self.align.Attachment0.CFrame
end

function Guardian:home()
    return CFrame.new(self.lair.Position) * self.facing
end

function Guardian:holdAtLair()
    self.align.MaxVelocity = self.config.WalkSpeed
    self.align.Position = self.lair.Position
    self.turn.CFrame = self.facing
end

-- A guardian that TurnsToFace (the mantis) turns at its lair toward the player it watches, the egg
-- in its arms turning with it.
function Guardian:faceTarget()
    local id = self.model:GetAttribute("TargetId")
    local target = id and id ~= 0 and Players:GetPlayerByUserId(id)
    local root = target and rootOf(target)
    local to = root and flat(root.Position - self.lair.Position)
    if to and to.Magnitude > 1 then
        self.facing = CFrame.lookAt(Vector3.zero, to).Rotation
    end
    self:holdEgg()
end

-- At its lair the egg in its arms is welded to its root, so it rides the same smooth physics; it is
-- let go when the egg is set down, taken or replaced.
function Guardian:holdEgg()
    local egg = self.egg
    if egg.held or egg.state ~= "Guarded" or not egg.model then
        return
    end
    anchorEgg(egg.model, false)
    egg.model:PivotTo(self:origin() * CFrame.new(self.config.Egg.Under))
    local weld = Instance.new("Weld")
    weld.Name = "HeldWeld"
    weld.Part0, weld.Part1 = self.root, egg.model.PrimaryPart
    weld.C0 = self.root.CFrame:ToObjectSpace(egg.model.PrimaryPart.CFrame)
    weld.Parent = egg.model.PrimaryPart
    egg.held = weld
end

function Guardian:releaseEgg()
    local egg = self.egg
    if egg.held then
        egg.held:Destroy()
        egg.held = nil
        if egg.model then
            anchorEgg(egg.model, true)
        end
    end
end

-- Each frame ------------------------------------------------------------------------------------

function Guardian:step(dt)
    local now = os.clock()
    local config = self.config
    local egg = self.egg

    if egg.state == "Carried" then
        self:watchThief()
    elseif egg.state == "Dropped" then
        if not (egg.owner and egg.owner.Parent) or now >= egg.dropUntil then
            self:returnEgg()
        end
    end

    if self.leap then
        local leap = self.leap
        local t = (now - leap.start) / leap.air
        if t >= 1 then
            self:land()
        elseif t >= 0 then
            self.align.MaxVelocity = 400
            self.align.Responsiveness = 200
            self.align.Position = leap.from:Lerp(leap.to, t) + Vector3.new(0, leap.height * 4 * t * (1 - t), 0)
        end
        return
    end

    if self.state == "Enraged" then
        local thief = egg.owner
        local root = thief and rootOf(thief)
        if root and flat(root.Position - self.islandCentre).Magnitude < self.islandRadius + 10 then
            self.model:SetAttribute("TargetId", thief.UserId)
            if now >= self.busyUntil then
                self:moveToward(root.Position, config.ChaseSpeed, CHASE_STOP, dt)
            else
                self.align.Position = self:origin().Position
            end
        else
            self.align.Position = self:origin().Position
        end
    elseif self.state == "Returning" then
        if self:moveToward(self.lair.Position, config.WalkSpeed, 1.5, dt) then
            self:holdAtLair()
            if egg.state == "None" then
                self:setState("Resting")
                self.restUntil = now + config.RespawnTime
                self:heal()
            else
                self.lastEngaged = now
                if self.health < config.MaxHealth * config.WeakenedAt then
                    self:setState("Weakened")
                    self:setEggState("Available")
                else
                    self:setState("Guardian")
                end
            end
        end
    else
        if self.state == "Guardian" and config.TurnsToFace then
            self:faceTarget()
        end
        self:holdAtLair()
    end

    if now < self.nextDecision then
        return
    end
    self.nextDecision = now + DECIDE_EVERY
    self:decide(now)
end

function Guardian:decide(now)
    local config = self.config
    local state = self.state

    if state == "Resting" then
        if now >= self.restUntil then
            self:guardEgg()
            self:setState("Dormant")
        end
        return
    end

    -- who holds its attention: players near its lair (or, enraged, near itself)
    local near = self:playersNear(if state == "Enraged" then self.reach else config.LeashRadius)
    if state == "Dormant" then
        if near[1] and near[1].distance <= config.EngageRadius then
            self:awaken()
        end
        return
    end
    if state == "Returning" then
        return
    end

    if state == "Guardian" or state == "Weakened" then
        if near[1] then
            self.lastEngaged = now
            self.model:SetAttribute("TargetId", near[1].player.UserId)
        elseif now - self.lastEngaged > config.CalmAfter then
            self:sleep()
            return
        end
    end
    if now < self.busyUntil or not near[1] then
        return
    end

    if state == "Enraged" then
        local thief = self.egg.owner
        local root = thief and rootOf(thief)
        if root and self.egg.state == "Carried" then
            local distance = flat(root.Position - self.root.Position).Magnitude
            for name, spec in self:attacksOf("Pounce") do
                if self:ready(name) and distance >= spec.MinRange and distance <= spec.MaxRange then
                    self:pounce(name, root)
                    return
                end
            end
        end
    end
    for name, spec in self:attacksOf("Sweep") do
        for _, entry in near do
            if entry.distance <= spec.Range and self:ready(name) and self:inFront(entry.root.Position, spec.Arc) then
                self:sweep(name)
                return
            end
        end
    end
    for name, spec in self:attacksOf("Wave") do
        local reach = if (spec.Arc or 180) >= 180 then spec.Radius * 0.6 else spec.Radius * 0.8
        for _, entry in near do
            local inArc = (spec.Arc or 180) >= 180 or self:inFront(entry.root.Position, spec.Arc)
            if self:ready(name) and entry.distance <= reach and inArc then
                self:wave(name)
                return
            end
        end
    end
end

return Guardian
