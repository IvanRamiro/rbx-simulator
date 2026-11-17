-- Notices movement no honest player could make. Roblox lets each client report its own character's
-- position, so a hacked client can teleport or speed about; rewards that depend on where a player
-- stands (prompts, shops, stands, strikes) ask here first.
--
-- Two checks, both from the player's rank (GameConfig.Qinggong; the slack below):
-- * one burst (every frame): from any place the server saw them at in the last TRAIL_SECONDS, they can't
--   have got farther across than their top speed (a dash, a run, a leap's push or sword flight) for the time
--   since, nor higher than their top climb (a leap, a jump or a climbing flight); falling is free. The time
--   is counted from when each place first showed, so a hitch that holds them still and then lets the
--   backlog arrive at once is fair, while a teleport the server spreads over a dozen frames is still a
--   teleport. The carried egg (Guardian) drops on the same rule: `movedSince`.
-- * the long run (every SAMPLE_TIME): a travel allowance, a bucket filled at the fastest they can honestly
--   keep up (RunSpeed, dashing as often as stamina allows, or sword flight), up to a burst for the dashes
--   and air leaps in hand. Each sample spends what they moved, not counting falls.
-- Caught by either, they're "suspect" for SUSPECT_TIME: rewards are refused and it's logged. It never
-- kicks or drags anyone back: a wrong guess costs an honest player a few seconds, nothing more.
--
--   MovementGuard.isSuspect(player)          true while rewards should be refused
--   MovementGuard.movedSince(player, t)      true if, since os.clock() `t`, they outran the burst rule or the server moved them
--   MovementGuard.maxTravel(player, seconds) the farthest they could honestly get in that time
--   MovementGuard.reset(player, to)          the server moved them itself (checkpoint, a gate's return) to `to` (a Vector3)
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
local BURST_SLACK = 60  -- studs of allowance for lag and small errors (the long run)
local SPEED_SLACK = 1.15
-- the burst rule's slack: LAG_SECONDS more of their top speed (packets reaching the server bunched, the server's own
-- smoothing) and LAG_STUDS (steps, physics pushing them out of a wall). A client teleport of 55 studs spread over 14
-- frames (largest step 22.5) passed the old 40-studs-a-frame check 2 times in 3 (2-player test, 2026-11-16).
local LAG_SECONDS = 0.2
local LAG_STUDS = 8
local TRAIL_SECONDS = 1 -- how far back the burst rule looks
local SPAWN_GRACE = 1   -- seconds after a new character in which Roblox may still be putting it at its spawn
local RESET_GRACE = 1   -- MovementGuard.reset: seconds the client may still report where it was before the server moved it
local RESET_NEAR = 25   -- studs from where the server put them that count as there
local THROW_TIME = 1.5  -- MovementGuard.allow: seconds a throw's studs widen the burst rule (the long run keeps them until spent)

local states = {} -- [player] = { position, budget, suspectUntil, extra, trail, movedAt, ... }

-- their Qinggong level, and how fast their rank lets them fly (0 below SwordFlight.UnlockRank, whatever the level holds)
local function levelOf(player)
    local rankName = Ranks.getPlayerRankName(player)
    return (Ranks.getQinggong(rankName)), Ranks.getFlightSpeed(rankName)
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

-- The fastest they ever move, studs a second, across and up, whatever they're doing now (a flight just ended keeps its
-- speed for a moment): a dash, a glide, a leap's push or sword flight; a leap, a jump or a flight climbing as it goes.
local function topSpeeds(level, humanoid, flightSpeed)
    local q = GameConfig.Qinggong
    local across = math.max(level.DashSpeed, level.RunSpeed * q.GlideSpeedFactor, q.LeapForwardSpeed, flightSpeed)
    local jump = if humanoid and humanoid.UseJumpPower then humanoid.JumpPower
        elseif humanoid then math.sqrt(2 * workspace.Gravity * humanoid.JumpHeight) else 0
    local up = math.max(q.LeapUpSpeed, jump, if flightSpeed > 0 then flightSpeed + GameConfig.SwordFlight.ClimbSpeed else 0)
    return across * SPEED_SLACK, up * SPEED_SLACK
end

function MovementGuard.maxTravel(player, seconds)
    local level = levelOf(player)
    return sustainedSpeed(player, level) * seconds + burst(level)
end

function MovementGuard.isSuspect(player)
    local state = states[player]
    return state ~= nil and os.clock() < state.suspectUntil
end

local function flag(player, state, level, moved, seconds)
    local clock = os.clock()
    if clock >= state.suspectUntil then
        warn("MovementGuard:", player.Name, "moved", math.floor(moved), "studs in", string.format("%.2f", seconds), "s")
        Analytics.event(player, "MovementSuspect", 1, level.RankId)
    end
    state.suspectUntil = clock + SUSPECT_TIME
end

local function restartTrail(state, at, clock)
    table.clear(state.trail)
    if at then
        table.insert(state.trail, { position = at, at = clock })
    end
end

-- The burst rule (see the top), for one player, now. Records where they are if they've moved, and flags a move past the rule.
local function observe(player, state)
    local character = player.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if not root then
        restartTrail(state, nil, 0)
        return
    end
    local clock = os.clock()
    local now = root.Position
    local trail = state.trail
    local last = trail[#trail]
    if last and (now - last.position).Magnitude < 0.01 then
        return -- not moved: the place keeps the time it first showed
    end
    if clock < state.spawnUntil then
        restartTrail(state, now, clock)
        return
    end
    if state.resetTo then
        if (now - state.resetTo).Magnitude <= RESET_NEAR then
            state.resetTo = nil -- there: measure on from here
        elseif clock < state.graceUntil then
            return -- still reporting where they were before the server moved them
        else
            state.resetTo = nil -- never got there: what they moved is measured from where they were put
        end
    end
    local level, flightSpeed = levelOf(player)
    local across, up = topSpeeds(level, character:FindFirstChildOfClass("Humanoid"), flightSpeed)
    -- the oldest places first, keeping the newest one even when it's old (they stood still)
    while #trail > 1 and clock - trail[1].at > TRAIL_SECONDS do
        table.remove(trail, 1)
    end
    for _, seen in trail do
        local move = now - seen.position
        local seconds = clock - seen.at + LAG_SECONDS
        local slack = LAG_STUDS + (if clock < state.thrownUntil then state.thrown else 0)
        if (move * Vector3.new(1, 0, 1)).Magnitude > across * seconds + slack or move.Y > up * seconds + slack then
            flag(player, state, level, move.Magnitude, clock - seen.at)
            state.movedAt, state.movedFrom = clock, seen.position
            restartTrail(state, now, clock)
            return
        end
    end
    table.insert(trail, { position = now, at = clock })
end

-- True if, since `since` (os.clock()), they moved faster than the burst rule allows or the server moved them (MovementGuard.reset);
-- then also where they were before an outrun move (nil after a server move). Checks them first, so a move this frame counts
-- whichever Heartbeat runs first.
function MovementGuard.movedSince(player, since)
    local state = states[player]
    if not state then
        return false, nil
    end
    observe(player, state)
    if state.movedAt >= since then
        return true, state.movedFrom
    end
    return false, nil
end

-- Their next move is measured from where the server put them, not from wherever they report next: forgetting the position here
-- let a cheat teleport anywhere for free right after a checkpoint return (release audit, 2026-11-12). For RESET_GRACE seconds a
-- report far from `to` (RESET_NEAR, declared at the top) is taken for the client still showing where they were before, and skipped.
function MovementGuard.reset(player, to)
    local state = states[player]
    if state then
        local clock = os.clock()
        state.position = to
        state.landing = to
        state.graceUntil = if to then clock + RESET_GRACE else 0
        state.resetTo = to
        state.movedAt, state.movedFrom = clock, nil
        restartTrail(state, to, clock)
    end
end

function MovementGuard.allow(player, studs)
    local state = states[player]
    if state then
        state.budget += studs
        state.extra = studs -- over the usual cap until it's spent
        state.thrown, state.thrownUntil = studs, os.clock() + THROW_TIME
    end
end

-- the long run (see the top), every SAMPLE_TIME
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
        if state.landing then
            if (now - state.landing).Magnitude <= RESET_NEAR then
                state.landing = nil -- there: measure on from here
            elseif os.clock() < (state.graceUntil or 0) then
                continue -- still reporting where they were before the server moved them
            else
                state.landing = nil -- never got there: what they moved since is charged from where they were put
            end
        end
        local from = state.position
        state.position = now
        if from and os.clock() >= state.spawnUntil then
            local move = now - from
            -- falling is free; everything else is spent
            state.budget -= (move * Vector3.new(1, 0, 1)).Magnitude + math.max(move.Y, 0)
            if state.budget < 0 then
                state.budget = cap / 2
                flag(player, state, level, move.Magnitude, dt)
            end
        end
    end
end

local function watch(player)
    local state = {
        position = nil, budget = burst(levelOf(player)), suspectUntil = 0, extra = 0,
        trail = {}, movedAt = -math.huge, spawnUntil = 0, graceUntil = 0, thrown = 0, thrownUntil = 0,
    }
    states[player] = state
    player.CharacterAdded:Connect(function()
        state.position = nil
        state.landing = nil
        state.resetTo = nil
        state.budget = burst(levelOf(player))
        state.spawnUntil = os.clock() + SPAWN_GRACE
        restartTrail(state, nil, 0)
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
    for player, state in states do
        observe(player, state)
    end
    waited += dt
    if waited >= SAMPLE_TIME then
        sample(waited)
        waited = 0
    end
end)

return MovementGuard
