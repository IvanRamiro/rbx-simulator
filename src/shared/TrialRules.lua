-- The three faction trials, as rules (the owner's brief, 2026-11-22: a trial in each headquarters, passed once, then the faction's vault opens and gives its
-- secret weapon). The numbers are GameConfig.Faction.Factions.<Id>.Trial; the server (server/Factions/TrialService) runs the clocks and decides every result,
-- the client (client/Factions/TrialController) only shows the run. This module is the plain part: how a run counts its progress, so it can be tested without Studio.
--
--   Orthodox, Trial of Discipline   Kind "Gates":   five gates up the stair, in order; one passed out of order sends the run back to the first
--   Unorthodox, Trial of Three Tokens   Kind "Tokens":  six tokens are hidden, any three pass, each token counts once
--   Demonic, Trial of Strength      Kind "Dummies": three waves of dummies in the arena; a wave is cleared before the next stands up
--
--   local run = TrialRules.new("Orthodox", now)    a new run: { Faction, Kind, Started, Ends, Done, Total, Passed, ... }
--   TrialRules.gate(run, index)       "Next" (the next gate, in order) | "Reset" (a later gate first: back to the first) | "Ignore"
--   TrialRules.token(run, index)      "Taken" | "Again" (this one already counted) | "Ignore"
--   TrialRules.dummyDown(run)         "Down" (one of the wave) | "Wave" (the wave is cleared, the next one is due) | "Cleared" (the last wave: the run is passed)
--   TrialRules.wave(run)              the wave now standing: { Places = {...}, Blows } (a Dummies run), or nil
--   TrialRules.expired(run, now)      whether the clock has run out
--   TrialRules.text(run)              what the HUD says of the progress, in plain words
-- run.Done counts what is done, run.Total what is needed (a token run needs Need of Count), run.Passed is set when Done reaches Total.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))

local TrialRules = {}

local config = GameConfig.Faction
local KINDS = {}
for _, kind in config.TrialKinds do
    KINDS[kind] = true
end

function TrialRules.of(factionId)
    local info = if typeof(factionId) == "string" then config.Factions[factionId] else nil
    return info and info.Trial
end

-- the dummies' places a Dummies trial uses are the arena's eight marked places
TrialRules.ArenaPlaces = 8

-- every faction's trial must be one the server can run; a wrong number here fails at load, not in a player's run
for id, info in config.Factions do
    local trial = info.Trial
    assert(trial and KINDS[trial.Kind], "faction " .. id .. " has no trial of a known kind")
    assert(typeof(trial.Seconds) == "number" and trial.Seconds >= 30 and trial.Seconds <= 900, "faction " .. id .. "'s trial has no sensible time")
    assert(typeof(trial.Hint) == "string" and trial.Hint ~= "", "faction " .. id .. "'s trial has no hint")
    if trial.Kind == "Gates" then
        assert(typeof(trial.Count) == "number" and trial.Count >= 2, "faction " .. id .. "'s gate trial needs at least two gates")
    elseif trial.Kind == "Tokens" then
        assert(typeof(trial.Count) == "number" and typeof(trial.Need) == "number" and trial.Need >= 1 and trial.Need <= trial.Count,
            "faction " .. id .. "'s token trial: Need must be between 1 and Count")
        assert(typeof(trial.Clues) == "table" and #trial.Clues == trial.Count, "faction " .. id .. "'s token trial needs one clue for each token")
    else
        assert(typeof(trial.Waves) == "table" and #trial.Waves >= 1, "faction " .. id .. "'s dummy trial has no waves")
        local used = {}
        for index, wave in trial.Waves do
            assert(typeof(wave.Blows) == "number" and wave.Blows >= 1, "faction " .. id .. "'s wave " .. index .. " needs a blow count")
            assert(typeof(wave.Places) == "table" and #wave.Places >= 1, "faction " .. id .. "'s wave " .. index .. " has no places")
            for _, place in wave.Places do
                assert(typeof(place) == "number" and place >= 1 and place <= TrialRules.ArenaPlaces and place == math.floor(place), "a dummy place is outside the arena's eight")
                assert(not used[place], "faction " .. id .. " uses dummy place " .. place .. " twice")
                used[place] = true
            end
        end
    end
end

local function dummyTotal(trial)
    local total = 0
    for _, wave in trial.Waves do
        total += #wave.Places
    end
    return total
end

-- how many things the run needs done: the gates, the tokens needed, or every dummy
function TrialRules.total(factionId)
    local trial = TrialRules.of(factionId)
    if not trial then
        return 0
    end
    if trial.Kind == "Gates" then
        return trial.Count
    elseif trial.Kind == "Tokens" then
        return trial.Need
    end
    return dummyTotal(trial)
end

function TrialRules.new(factionId, now)
    local trial = assert(TrialRules.of(factionId), "no such faction")
    local run = {
        Faction = factionId, Kind = trial.Kind, Started = now, Ends = now + trial.Seconds,
        Done = 0, Total = TrialRules.total(factionId), Passed = false,
        Next = 1,      -- Gates: the gate due
        Taken = {},    -- Tokens: [index] = true
        WaveIndex = 1, -- Dummies: the wave standing
        WaveDown = 0,  -- Dummies: how many of it have fallen
    }
    return run
end

function TrialRules.expired(run, now)
    return now >= run.Ends
end

local function finish(run)
    if run.Done >= run.Total then
        run.Passed = true
    end
end

function TrialRules.gate(run, index)
    local trial = TrialRules.of(run.Faction)
    if run.Kind ~= "Gates" or run.Passed or typeof(index) ~= "number" or index ~= math.floor(index) or index < 1 or index > trial.Count then
        return "Ignore"
    end
    if index == run.Next then
        run.Next += 1
        run.Done += 1
        finish(run)
        return "Next"
    elseif index > run.Next then
        run.Next = 1
        run.Done = 0
        return "Reset"
    end
    return "Ignore" -- a gate already passed
end

function TrialRules.token(run, index)
    local trial = TrialRules.of(run.Faction)
    if run.Kind ~= "Tokens" or run.Passed or typeof(index) ~= "number" or index ~= math.floor(index) or index < 1 or index > trial.Count then
        return "Ignore"
    end
    if run.Taken[index] then
        return "Again"
    end
    run.Taken[index] = true
    run.Done += 1
    finish(run)
    return "Taken"
end

function TrialRules.wave(run)
    if run.Kind ~= "Dummies" or run.Passed then
        return nil
    end
    return TrialRules.of(run.Faction).Waves[run.WaveIndex]
end

function TrialRules.dummyDown(run)
    local wave = TrialRules.wave(run)
    if not wave then
        return "Ignore"
    end
    run.Done += 1
    run.WaveDown += 1
    if run.WaveDown >= #wave.Places then
        run.WaveIndex += 1
        run.WaveDown = 0
        finish(run)
        return if run.Passed then "Cleared" else "Wave"
    end
    return "Down"
end

-- the progress in plain words (the run's Done and Total, with the place in it)
function TrialRules.text(run)
    if run.Kind == "Gates" then
        return if run.Passed then "All gates passed" else string.format("Gate %d of %d", math.min(run.Next, run.Total), run.Total)
    elseif run.Kind == "Tokens" then
        return string.format("Tokens %d of %d", run.Done, run.Total)
    end
    local waves = #TrialRules.of(run.Faction).Waves
    return string.format("Wave %d of %d  -  %d of %d down", math.min(run.WaveIndex, waves), waves, run.Done, run.Total)
end

return TrialRules
