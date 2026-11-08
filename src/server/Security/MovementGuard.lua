-- Notices movement no honest player could make. Roblox lets each client report its own character's
-- position, so a hacked client can teleport or speed about; rewards that depend on where a player
-- stands (prompts, shops, stands, strikes) ask here first.
--
-- It keeps a travel allowance per player, a bucket filled at the fastest they can honestly keep up for
-- their rank (RunSpeed, dashing as often as stamina allows, or sword flight), up to a burst for the dashes
-- and air leaps in hand. Each sample spends what they moved, not counting falls. Overdrawn, or moving
-- far too far in one sample, they're "suspect" for SUSPECT_TIME: rewards are refused and it's logged. It never kicks or drags anyone back:
-- a wrong guess costs an honest player a few seconds, nothing more.
--
--   MovementGuard.isSuspect(player)          true while rewards should be refused
--   MovementGuard.maxTravel(player, seconds) the farthest they could honestly get in that time
--   MovementGuard.reset(player)              the server moved them itself (checkpoint, a gate's return)
--   MovementGuard.allow(player, studs)       the server threw them that far (a guardian's knockback)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local Analytics = require(script.Parent.Parent:WaitForChild("Analytics"):WaitForChild("Analytics"))

local MovementGuard = {}

local SAMPLE_TIME = 0.25
local SUSPECT_TIME = 5
local BURST_SLACK = 60  -- studs of allowance for lag and small errors
local SPEED_SLACK = 1.15
local JUMP_SECONDS = 1

local states = {} -- [player] = { position, budget, suspectUntil }

local function levelOf(player)
    return (Ranks.getQinggong(Ranks.getPlayerRankName(player)))
end

-- the studs a second they can keep up
local function sustainedSpeed(player, level)
    local q = GameConfig.Qinggong
    if player:GetAttribute("IsFlying") == true then
        -- a flier goes along the camera at FlightSpeed and climbs on top of it; a sample is charged its
        -- level distance plus its rise, which along a slope comes to at most FlightSpeed * sqrt(2)
        return (level.FlightSpeed * math.sqrt(2) + GameConfig.SwordFlight.ClimbSpeed) * SPEED_SLACK
    end
    local run = level.RunSpeed * q.GlideSpeedFactor
    local dashShare = q.Dash.Duration / q.Dash.Cooldown -- dashing as often as its cooldown lets them
    return math.max(run, q.LeapForwardSpeed, level.DashSpeed * dashShare + run * (1 - dashShare)) * SPEED_SLACK
end

-- the studs they can cover at once: every dash stamina allows, every air leap, and some slack
local function burst(level)
    local q = GameConfig.Qinggong
    local dashes = level.Stamina / q.Dash.Cost * q.Dash.Duration * level.DashSpeed
    local leaps = level.AirLeaps * q.LeapUpSpeed * 0.6
    return dashes + leaps + BURST_SLACK
end

function MovementGuard.maxTravel(player, seconds)
    local level = levelOf(player)
    return sustainedSpeed(player, level) * seconds + burst(level)
end

function MovementGuard.isSuspect(player)
    local state = states[player]
    return state ~= nil and os.clock() < state.suspectUntil
end

function MovementGuard.reset(player)
    local state = states[player]
    if state then
        state.position = nil
    end
end

function MovementGuard.allow(player, studs)
    local state = states[player]
    if state then
        state.budget += studs
        state.extra = studs -- over the usual cap until it's spent
    end
end

local function sample(dt)
    for player, state in states do
        local character = player.Character
        local root = character and character:FindFirstChild("HumanoidRootPart")
        if not root then
            state.position = nil
            continue
        end
        local level = levelOf(player)
        local cap = burst(level)
        state.budget = math.min(cap + state.extra, state.budget + sustainedSpeed(player, level) * dt)
        if state.budget <= cap then
            state.extra = 0
        end
        local now = root.Position
        local from = state.position
        state.position = now
        if from then
            local move = now - from
            -- falling is free; everything else is spent
            local spent = (move * Vector3.new(1, 0, 1)).Magnitude + math.max(move.Y, 0)
            state.budget -= spent
            -- the allowance is for several dashes in a row, not all at once: no sample may hold more than a
            -- second's movement at their top speed (a network hitch), whatever is saved up
            local fastest = math.max(level.DashSpeed, level.FlightSpeed) * SPEED_SLACK
            if state.budget < 0 or spent > fastest * JUMP_SECONDS + BURST_SLACK + state.extra then
                state.budget = cap / 2
                local clock = os.clock()
                if clock >= state.suspectUntil then
                    warn("MovementGuard:", player.Name, "moved", math.floor(move.Magnitude), "studs in", SAMPLE_TIME, "s")
                    Analytics.event(player, "MovementSuspect", 1, level.RankId)
                end
                state.suspectUntil = clock + SUSPECT_TIME
            end
        end
    end
end

local function watch(player)
    local state = { position = nil, budget = burst(levelOf(player)), suspectUntil = 0, extra = 0 }
    states[player] = state
    player.CharacterAdded:Connect(function()
        state.position = nil
        state.budget = burst(levelOf(player))
    end)
end

Players.PlayerAdded:Connect(watch)
for _, player in Players:GetPlayers() do
    watch(player)
end
Players.PlayerRemoving:Connect(function(player)
    states[player] = nil
end)

local waited = 0
RunService.Heartbeat:Connect(function(dt)
    waited += dt
    if waited >= SAMPLE_TIME then
        sample(waited)
        waited = 0
    end
end)

return MovementGuard
