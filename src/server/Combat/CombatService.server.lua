-- Resolves strikes (GameConfig.Combat, WeaponKinds). The client fires CombatEvent with no arguments;
-- the server decides the weapon (the one equipped, or the Qi Palm), the cooldown, the target and
-- the damage.
--
-- A target is a Model tagged GameConfig.Combat.TargetTag with a PrimaryPart and a HitRadius
-- attribute (studs round the PrimaryPart's centre). A strike lands on the nearest target within the
-- weapon's Arc of facing and Range, unless its "Invulnerable" attribute is set. A landing strike
-- fires Combat.Hit; every strike is relayed to all clients (CombatEvent: striker, kind ("Palm",
-- "Sword" or "Spear"), hit position or nil).
--
-- The flying sword is copied to ReplicatedStorage.Weapons so clients can show it striking.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Combat = require(script.Parent:WaitForChild("Combat"))

local COOLDOWN_SLACK = 0.85 -- requests a little early are latency, not cheating
local lastStrike = {}

do
    local source = ServerStorage:FindFirstChild("Weapons") and ServerStorage.Weapons:FindFirstChild("FlyingSword")
    if source then
        local folder = ReplicatedStorage:FindFirstChild("Weapons") or Instance.new("Folder")
        folder.Name = "Weapons"
        folder.Parent = ReplicatedStorage
        local old = folder:FindFirstChild("FlyingSword")
        if old then
            old:Destroy()
        end
        source:Clone().Parent = folder
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
                bestPoint = body.Position - (if flat.Magnitude > 0 then flat.Unit else facing) * math.min(radius, flat.Magnitude) * 0.9
            end
        end
    end
    return best, bestPoint
end

RemoteEvents.CombatEvent.OnServerEvent:Connect(function(player)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    if not (humanoid and rootPart) or humanoid.Health <= 0 or player:GetAttribute("IsCultivating") == true then
        return
    end
    local strike = Combat.strikeOf(player)
    local now = os.clock()
    if lastStrike[player] and now - lastStrike[player] < strike.Cooldown * COOLDOWN_SLACK then
        return
    end
    lastStrike[player] = now
    local target, point = findTarget(rootPart, strike)
    if target then
        Combat.Hit:Fire(player, target, strike.Damage * Combat.powerOf(player), point)
    end
    RemoteEvents.CombatEvent:FireAllClients(player, strike.Kind, point)
end)

Players.PlayerRemoving:Connect(function(player)
    lastStrike[player] = nil
end)
