-- Resolves strikes (GameConfig.Combat, WeaponKinds). The client fires CombatEvent with no arguments;
-- the server decides the weapon (the one equipped, or the Qi Palm), the cooldown, the target and
-- the damage.
--
-- A target is a Model tagged GameConfig.Combat.TargetTag with a PrimaryPart and a HitRadius
-- attribute (studs round the PrimaryPart's centre). A strike lands on the nearest target within the
-- weapon's Arc of facing and Range, unless its "Invulnerable" attribute is set. A spear alternates a
-- thrust and a sweeping slash with its own reach (WeaponKinds.Spear.Slash); the server keeps the count,
-- so a client can't choose the wider reach. A landing strike
-- fires Combat.Hit; every strike is relayed to all clients (CombatEvent: striker, kind ("Palm",
-- "Sword" or "Spear"), hit position or nil, a spear's step in its combo or nil, and for a strike that
-- landed: its damage (a whole number), true if it was critical, and the target it struck).
--
-- A landing strike may be critical (GameConfig.Combat.Crit): rolled here, never by a client.
--
-- Every stored weapon (ServerStorage.Weapons: the flying sword and the realm weapons, OutfitBuilder)
-- is copied to ReplicatedStorage.Weapons so clients can show it striking.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Combat = require(script.Parent:WaitForChild("Combat"))
local MovementGuard = require(script.Parent.Parent:WaitForChild("Security"):WaitForChild("MovementGuard"))

local COOLDOWN_SLACK = 0.15 -- the share of a cooldown a request may come early: latency, not cheating
local lastStrike = {}
-- [player] = when their next strike is due. It moves on by a whole cooldown from when the last was
-- due, not from when it arrived, so coming early can't add up: a client firing as early as the slack
-- allows gets the same strikes a second as anyone else.
local nextStrike = {}
local spearSlashNext = {} -- [player] = true: their last strike was a thrust, inside the combo window
local roll = Random.new() -- critical strikes

do
    local stored = ServerStorage:FindFirstChild("Weapons")
    if stored then
        local folder = ReplicatedStorage:FindFirstChild("Weapons") or Instance.new("Folder")
        folder.Name = "Weapons"
        for _, source in stored:GetChildren() do
            local old = folder:FindFirstChild(source.Name)
            if old then
                old:Destroy()
            end
            source:Clone().Parent = folder
        end
        folder.Parent = ReplicatedStorage
    end
end

-- the nearest target in front within reach, and where the strike meets it
local function findTarget(rootPart, spec)
    local facing = rootPart.CFrame.LookVector * Vector3.new(1, 0, 1)
    facing = if facing.Magnitude > 0 then facing.Unit else Vector3.new(0, 0, -1)
    local cosArc = math.cos(math.rad(spec.Arc))
    local best, bestDistance, bestPoint = nil, math.huge, nil
    for _, target in CollectionService:GetTagged(GameConfig.Combat.TargetTag) do
        local body = target:IsA("Model") and target.PrimaryPart
        if body and target:IsDescendantOf(workspace) and target:GetAttribute("Invulnerable") ~= true then
            local radius = target:GetAttribute("HitRadius") or 2
            local offset = body.Position - rootPart.Position
            local flat = offset * Vector3.new(1, 0, 1)
            local distance = math.max(0, flat.Magnitude - radius)
            local inFront = flat.Magnitude <= radius or (flat.Unit:Dot(facing) >= cosArc)
            local vertical = math.abs(offset.Y) <= radius + 4
            if distance <= spec.Range and inFront and vertical and distance < bestDistance then
                best, bestDistance = target, distance
                -- on its near side, at the height of the striker's chest (where the weapon is), never at the height of its
                -- own centre: a big guardian's is at its base, and the blow showed at the striker's feet
                local near = body.Position - (if flat.Magnitude > 0 then flat.Unit else facing) * math.min(radius, flat.Magnitude) * 0.9
                bestPoint = Vector3.new(near.X, rootPart.Position.Y + 0.5, near.Z)
            end
        end
    end
    return best, bestPoint
end

RemoteEvents.CombatEvent.OnServerEvent:Connect(function(player)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    if not (humanoid and rootPart) or humanoid.Health <= 0 or player:GetAttribute("IsCultivating") == true
        or player:GetAttribute("CarryingEgg") ~= nil then -- both hands are round the egg
        return
    end
    local strike = Combat.strikeOf(player)
    local now = os.clock()
    local due = nextStrike[player]
    if due and now < due - strike.Cooldown * COOLDOWN_SLACK then
        return
    end
    nextStrike[player] = math.max(now, due or 0) + strike.Cooldown
    local continuing = strike.ComboWindow and lastStrike[player] and now - lastStrike[player] < strike.ComboWindow
    lastStrike[player] = now
    -- a spear's combo: a thrust, then a slash
    local slashing = strike.Slash ~= nil and continuing and spearSlashNext[player] == true
    spearSlashNext[player] = strike.Slash ~= nil and not slashing or nil
    -- from sword flight a strike swings but can't land: guardians can't reach a flyer, so a flyer
    -- can't reach them
    local target, point = nil, nil
    if player:GetAttribute("IsFlying") ~= true and not MovementGuard.isSuspect(player) then
        target, point = findTarget(rootPart, if slashing then strike.Slash else strike)
    end
    local damage, critical = nil, nil
    if target then
        local crit = GameConfig.Combat.Crit
        critical = roll:NextNumber() < crit.Chance
        damage = strike.Damage * Combat.powerOf(player) * (if critical then crit.Multiplier else 1)
        Combat.Hit:Fire(player, target, damage, point)
    end
    RemoteEvents.CombatEvent:FireAllClients(player, strike.Kind, point, if strike.Slash then (if slashing then 2 else 1) else nil,
        if damage then math.round(damage) else nil, critical or nil, target)
end)

Players.PlayerRemoving:Connect(function(player)
    lastStrike[player] = nil
    nextStrike[player] = nil
    spearSlashNext[player] = nil
end)
