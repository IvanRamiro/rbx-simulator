-- The Heavenly Tribulation (GameConfig.Tribulation, November 9, 2026): breaking through into a new realm, the heavens test
-- the cultivator. A storm gathers over them; rings mark the ground where lightning will fall, a moment later it falls, and
-- they must be out of the ring. The server places every ring and judges every strike, from where the cultivator really
-- is; every client is told, to draw the storm (TribulationController). Survive every bolt and the breakthrough is theirs
-- (RankService's onPass); Lives hits and it is over, and they may try again RetryAfter seconds later (their
-- "TribulationRetryAt" attribute, in server time). Their "InTribulation" attribute holds while it lasts: meditation and
-- sword flight stop and can't start (QiService, FlightService). Dying or leaving ends it with no wait.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Analytics = require(script.Parent.Parent:WaitForChild("Analytics"):WaitForChild("Analytics"))

local CONFIG = GameConfig.Tribulation
local HITBOX = 1.2 -- studs added to a bolt's reach for the cultivator's own width
local HIT_GAP = 0.35 -- seconds: bolts falling together cost one life between them, not one each

local Tribulation = {}

local active = {} -- [player] = the run's token

local realmNumbers = {} -- [realm name] = its number (1 = Qi Awakening)
for _, rank in GameConfig.Ranks do
    if not realmNumbers[rank.Realm] then
        local count = 0
        for _ in realmNumbers do
            count += 1
        end
        realmNumbers[rank.Realm] = count + 1
    end
end

function Tribulation.realmNumber(realmName)
    return realmNumbers[realmName]
end

local function liveRoot(player, character)
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    if player.Parent ~= Players or player.Character ~= character or not humanoid or humanoid.Health <= 0 then
        return nil
    end
    return character:FindFirstChild("HumanoidRootPart")
end

-- the ground under a point (characters ignored), or a little under the point itself
local function groundBelow(position)
    local params = RaycastParams.new()
    local characters = {}
    for _, other in Players:GetPlayers() do
        if other.Character then
            table.insert(characters, other.Character)
        end
    end
    params.FilterDescendantsInstances = characters
    params.FilterType = Enum.RaycastFilterType.Exclude
    local hit = Workspace:Raycast(position + Vector3.new(0, 4, 0), Vector3.new(0, -220, 0), params)
    return if hit then hit.Position else position - Vector3.new(0, 3, 0)
end

local function finish(player, token, passed, cancelled, realm, onPass)
    if active[player] ~= token then
        return
    end
    active[player] = nil
    local retryAt = nil
    if player.Parent == Players then
        player:SetAttribute("InTribulation", nil)
        if not passed and not cancelled then
            retryAt = Workspace:GetServerTimeNow() + CONFIG.RetryAfter
            player:SetAttribute("TribulationRetryAt", retryAt)
        end
    end
    RemoteEvents.TribulationEvent:FireAllClients("End", player, { Passed = passed, Cancelled = cancelled, RetryAt = retryAt })
    if not cancelled then
        Analytics.event(player, if passed then "TribulationPassed" else "TribulationFailed", realm)
    end
    if passed then
        onPass()
    end
end

local function run(player, character, token, realm, onPass)
    local step = math.clamp(realm - 1, 1, #CONFIG.Bolts)
    local bolts, warnTime, gap = CONFIG.Bolts[step], CONFIG.Warn[step], CONFIG.Gap[step]
    local together, lead = CONFIG.Together[step], CONFIG.Lead[step]
    local lives = CONFIG.Lives
    local lastHit = -math.huge
    local nextId = 0

    local function strike(id, position)
        if active[player] ~= token then
            return
        end
        local root = liveRoot(player, character)
        local hit = false
        if root then
            local offset = root.Position - position
            hit = Vector3.new(offset.X, 0, offset.Z).Magnitude <= CONFIG.Radius + HITBOX and offset.Y > -4 -- the bolt is a column: any height
        end
        if hit and os.clock() - lastHit > HIT_GAP then
            lastHit = os.clock()
            lives -= 1
        end
        RemoteEvents.TribulationEvent:FireAllClients("Strike", player, { Id = id, Position = position, Hit = hit, Lives = lives })
        if lives <= 0 then
            finish(player, token, false, false, realm, onPass)
        end
    end

    task.wait(CONFIG.Gather)
    for k = 1, bolts do
        if active[player] ~= token then
            return
        end
        local root = liveRoot(player, character)
        if not root then
            finish(player, token, false, true, realm, onPass)
            return
        end
        -- one aimed where they are heading; the others ringing round where they are, to close the easy ways out
        local heading = root.AssemblyLinearVelocity * Vector3.new(1, 0, 1)
        local targets = { groundBelow(root.Position + heading * warnTime * lead) }
        local turn = math.random() * 2 * math.pi
        for j = 2, together do
            local a = turn + (j - 2) / math.max(1, together - 1) * 2 * math.pi + (math.random() - 0.5) * 0.8
            local reach = CONFIG.Radius * (1.3 + 0.5 * math.random())
            table.insert(targets, groundBelow(root.Position + Vector3.new(math.cos(a), 0, math.sin(a)) * reach))
        end
        for _, position in targets do
            nextId += 1
            local id = nextId
            RemoteEvents.TribulationEvent:FireAllClients("Warn", player, { Id = id, Position = position, Radius = CONFIG.Radius, Delay = warnTime, Left = bolts - k })
            task.delay(warnTime, strike, id, position)
        end
        task.wait(gap)
    end
    task.wait(warnTime + 0.15)
    if active[player] == token then
        finish(player, token, lives > 0, false, realm, onPass)
    end
end

-- Starts their tribulation for entering realm number `realm`; onPass() is called if they survive it. False if they can't
-- face it now (already in one, still recovering from the last, carrying a guardian's egg, no living character).
function Tribulation.start(player, realm, onPass)
    if active[player] or player:GetAttribute("CarryingEgg") ~= nil then
        return false
    end
    if (player:GetAttribute("TribulationRetryAt") or 0) > Workspace:GetServerTimeNow() then
        return false
    end
    local character = player.Character
    if not liveRoot(player, character) then
        return false
    end
    local token = {}
    active[player] = token
    player:SetAttribute("InTribulation", true)
    local step = math.clamp(realm - 1, 1, #CONFIG.Bolts)
    RemoteEvents.TribulationEvent:FireAllClients("Start", player, {
        Realm = realm, Bolts = CONFIG.Bolts[step], Lives = CONFIG.Lives, Gather = CONFIG.Gather, CloudHeight = CONFIG.CloudHeight,
    })
    Analytics.event(player, "TribulationStarted", realm)
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    humanoid.Died:Once(function()
        finish(player, token, false, true, realm, onPass)
    end)
    task.spawn(run, player, character, token, realm, onPass)
    return true
end

Players.PlayerRemoving:Connect(function(player)
    active[player] = nil
end)

return Tribulation
