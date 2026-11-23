-- TrialRules: how the three faction trials count a run (gates in order, any three of six tokens, three waves of dummies), and that the trials in
-- GameConfig are ones the server can run. The server's clocks, the prompts and the world are Studio's to test; the counting is here.
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local TrialRules = require("@shared/TrialRules")

local function fresh(faction)
    return TrialRules.new(faction, 1000)
end

t.test("every faction has a trial of a known kind with a time and a hint", function()
    for id, info in GameConfig.Faction.Factions do
        t.ok(TrialRules.of(id) == info.Trial, id .. " trial is the config's")
        t.ok(table.find(GameConfig.Faction.TrialKinds, info.Trial.Kind) ~= nil, id .. " has an unknown kind")
        t.ok(TrialRules.total(id) >= 1, id .. " needs nothing done")
    end
    t.eq(TrialRules.of("Nobody"), nil)
    t.eq(TrialRules.of(nil), nil)
    t.eq(TrialRules.total("Nobody"), 0)
end)

t.test("the three trials are the ones the owner asked for", function()
    t.eq(TrialRules.of("Orthodox").Kind, "Gates")
    t.eq(TrialRules.of("Orthodox").Count, 5, "five gates")
    t.eq(TrialRules.of("Orthodox").Seconds, 90)
    t.eq(TrialRules.of("Unorthodox").Kind, "Tokens")
    t.eq(TrialRules.of("Unorthodox").Need, 3, "three tokens")
    t.eq(TrialRules.of("Unorthodox").Seconds, 300, "five minutes")
    t.eq(TrialRules.of("Demonic").Kind, "Dummies")
    t.eq(#TrialRules.of("Demonic").Waves, 3, "three waves")
    t.eq(TrialRules.of("Demonic").Seconds, 90)
end)

t.test("a new run knows when it ends and starts with nothing done", function()
    local run = fresh("Orthodox")
    t.eq(run.Ends, 1090)
    t.eq(run.Done, 0)
    t.falsy(run.Passed)
    t.falsy(TrialRules.expired(run, 1089.9))
    t.ok(TrialRules.expired(run, 1090))
    t.ok(TrialRules.expired(run, 5000))
end)

-- ---------- the gates ----------
t.test("gates passed in order pass the trial on the last one", function()
    local run = fresh("Orthodox")
    for index = 1, 4 do
        t.eq(TrialRules.gate(run, index), "Next")
        t.falsy(run.Passed, "not passed after gate " .. index)
    end
    t.eq(TrialRules.gate(run, 5), "Next")
    t.ok(run.Passed)
    t.eq(run.Done, 5)
end)

t.test("a gate passed out of order sends the run back to the first", function()
    local run = fresh("Orthodox")
    t.eq(TrialRules.gate(run, 1), "Next")
    t.eq(TrialRules.gate(run, 2), "Next")
    t.eq(TrialRules.gate(run, 4), "Reset", "gate 3 skipped")
    t.eq(run.Done, 0)
    t.eq(run.Next, 1)
    t.eq(TrialRules.gate(run, 1), "Next", "and it can be run again")
    t.falsy(run.Passed)
end)

t.test("flying straight to the last gate is a skip, not a pass", function()
    local run = fresh("Orthodox")
    t.eq(TrialRules.gate(run, 5), "Reset")
    t.falsy(run.Passed)
end)

t.test("a gate already passed, or one that does not exist, changes nothing", function()
    local run = fresh("Orthodox")
    TrialRules.gate(run, 1)
    TrialRules.gate(run, 2)
    t.eq(TrialRules.gate(run, 1), "Ignore", "walking back through gate 1")
    t.eq(TrialRules.gate(run, 2), "Ignore", "or standing in gate 2")
    t.eq(TrialRules.gate(run, 0), "Ignore")
    t.eq(TrialRules.gate(run, 6), "Ignore")
    t.eq(TrialRules.gate(run, 2.5), "Ignore")
    t.eq(TrialRules.gate(run, "3"), "Ignore")
    t.eq(TrialRules.gate(run, nil), "Ignore")
    t.eq(run.Done, 2)
    t.eq(TrialRules.gate(fresh("Demonic"), 1), "Ignore", "a gate means nothing to another trial")
end)

-- ---------- the tokens ----------
t.test("any three of the six tokens pass, in any order", function()
    local run = fresh("Unorthodox")
    t.eq(TrialRules.token(run, 6), "Taken")
    t.eq(TrialRules.token(run, 2), "Taken")
    t.falsy(run.Passed)
    t.eq(TrialRules.token(run, 5), "Taken")
    t.ok(run.Passed)
    t.eq(run.Done, 3)
end)

t.test("a token counts once", function()
    local run = fresh("Unorthodox")
    t.eq(TrialRules.token(run, 3), "Taken")
    t.eq(TrialRules.token(run, 3), "Again")
    t.eq(TrialRules.token(run, 3), "Again")
    t.eq(run.Done, 1)
    t.falsy(run.Passed)
end)

t.test("a token that does not exist counts for nothing", function()
    local run = fresh("Unorthodox")
    t.eq(TrialRules.token(run, 0), "Ignore")
    t.eq(TrialRules.token(run, 7), "Ignore")
    t.eq(TrialRules.token(run, -1), "Ignore")
    t.eq(TrialRules.token(run, 1.5), "Ignore")
    t.eq(TrialRules.token(run, nil), "Ignore")
    t.eq(TrialRules.token(run, {}), "Ignore")
    t.eq(run.Done, 0)
    t.eq(TrialRules.token(fresh("Orthodox"), 1), "Ignore", "a token means nothing to another trial")
end)

t.test("a passed run takes no more", function()
    local run = fresh("Unorthodox")
    for index = 1, 3 do
        TrialRules.token(run, index)
    end
    t.ok(run.Passed)
    t.eq(TrialRules.token(run, 4), "Ignore")
    t.eq(run.Done, 3)
end)

-- ---------- the dummies ----------
t.test("three waves: each is cleared before the next, the last passes the run", function()
    local run = fresh("Demonic")
    local waves = TrialRules.of("Demonic").Waves
    t.eq(TrialRules.wave(run), waves[1])
    t.eq(TrialRules.dummyDown(run), "Down")
    t.eq(TrialRules.dummyDown(run), "Down")
    t.eq(TrialRules.dummyDown(run), "Wave", "wave 1 cleared")
    t.eq(TrialRules.wave(run), waves[2])
    t.eq(run.WaveDown, 0)
    t.eq(TrialRules.dummyDown(run), "Down")
    t.eq(TrialRules.dummyDown(run), "Down")
    t.eq(TrialRules.dummyDown(run), "Wave")
    t.eq(TrialRules.wave(run), waves[3])
    t.eq(TrialRules.dummyDown(run), "Down")
    t.falsy(run.Passed)
    t.eq(TrialRules.dummyDown(run), "Cleared")
    t.ok(run.Passed)
    t.eq(run.Done, 8, "all eight dummies")
    t.eq(TrialRules.wave(run), nil)
    t.eq(TrialRules.dummyDown(run), "Ignore", "nothing is left to fall")
    t.eq(run.Done, 8)
end)

t.test("the arena's eight places are each used once across the waves", function()
    local seen, count = {}, 0
    for _, wave in TrialRules.of("Demonic").Waves do
        for _, place in wave.Places do
            t.falsy(seen[place], "place " .. place .. " is used twice")
            seen[place] = true
            count += 1
        end
    end
    t.eq(count, TrialRules.ArenaPlaces)
    t.eq(TrialRules.total("Demonic"), 8)
end)

t.test("a dummy means nothing to another trial", function()
    t.eq(TrialRules.dummyDown(fresh("Orthodox")), "Ignore")
    t.eq(TrialRules.wave(fresh("Unorthodox")), nil)
end)

-- ---------- the words ----------
t.test("the progress reads in plain words", function()
    local gates = fresh("Orthodox")
    t.eq(TrialRules.text(gates), "Gate 1 of 5")
    TrialRules.gate(gates, 1)
    t.eq(TrialRules.text(gates), "Gate 2 of 5")
    for index = 2, 5 do
        TrialRules.gate(gates, index)
    end
    t.eq(TrialRules.text(gates), "All gates passed")
    local tokens = fresh("Unorthodox")
    TrialRules.token(tokens, 4)
    t.eq(TrialRules.text(tokens), "Tokens 1 of 3")
    local dummies = fresh("Demonic")
    t.eq(TrialRules.text(dummies), "Wave 1 of 3  -  0 of 8 down")
    TrialRules.dummyDown(dummies)
    t.eq(TrialRules.text(dummies), "Wave 1 of 3  -  1 of 8 down")
    for _ = 1, 2 do
        TrialRules.dummyDown(dummies)
    end
    t.eq(TrialRules.text(dummies), "Wave 2 of 3  -  3 of 8 down")
end)

t.test("every token has a clue and every clue is a plain sentence", function()
    local trial = TrialRules.of("Unorthodox")
    t.eq(#trial.Clues, trial.Count)
    for index, clue in trial.Clues do
        t.ok(#clue >= 20 and #clue <= 90, "clue " .. index .. " is the wrong length")
        t.ok(string.sub(clue, -1) == ".", "clue " .. index .. " should end with a full stop")
    end
end)

t.finish("trials")
