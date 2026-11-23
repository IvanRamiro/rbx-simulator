-- WeatherRules (the day/night clock and the weather schedule, the same on every server and client), CodexRules and FactionRules.
local t = require("@env/t")
local GameConfig = require("@shared/GameConfig")
local WeatherConfig = require("@shared/WeatherConfig")
local WeatherRules = require("@shared/WeatherRules")
local CodexRules = require("@shared/CodexRules")
local FactionRules = require("@shared/FactionRules")
local Ranks = require("@shared/Ranks")

local WEATHER = WeatherConfig.Weather

-- ---------- weather ----------
t.test("the clock stays in 0 to 24 over a whole cycle, and every point of it has a segment name", function()
    local steps = 4000
    for i = 0, steps do
        local clock, segment = WeatherRules.clockAt(WeatherRules.CycleLength * i / steps)
        t.ok(clock >= 0 and clock < 24, "clock " .. tostring(clock))
        t.ok(type(segment) == "string" and #segment > 0)
    end
    t.eq(WeatherRules.clockAt(0), WeatherRules.clockAt(WeatherRules.CycleLength), "the cycle repeats")
    t.near(WeatherRules.clockAt(WeatherRules.CycleLength * 7.3), WeatherRules.clockAt(WeatherRules.CycleLength * 0.3), 1e-6)
end)

t.test("the clock never jumps (no more than a few minutes of game time per real second)", function()
    local lastClock = WeatherRules.clockAt(0)
    local worst = 0
    for second = 1, WeatherRules.CycleLength do
        local clock = WeatherRules.clockAt(second)
        local delta = math.abs(clock - lastClock)
        delta = math.min(delta, 24 - delta) -- across midnight
        worst = math.max(worst, delta)
        lastClock = clock
    end
    t.ok(worst < 0.5, "the clock jumped " .. worst .. " hours in one second")
end)

t.test("night: none at noon, full at midnight, always between 0 and 1, and rising through the evening", function()
    t.eq(WeatherRules.nightAt(12), 0)
    t.eq(WeatherRules.nightAt(8), 0)
    t.eq(WeatherRules.nightAt(0), 1)
    t.eq(WeatherRules.nightAt(23), 1)
    t.eq(WeatherRules.nightAt(3), 1)
    local last = 0
    for tenth = 0, 80 do
        local clock = 17 + tenth / 10 -- 17.0 to 25.0 would wrap: stop at 24
        if clock >= 24 then
            break
        end
        local night = WeatherRules.nightAt(clock)
        t.ok(night >= 0 and night <= 1)
        t.ok(night >= last - 1e-12, "evening gets darker, not lighter")
        last = night
    end
end)

t.test("the schedule is deterministic, and every spell is one of the known weathers", function()
    for index = 0, 3000 do
        local a, nameA = WeatherRules.spellAt(index * WEATHER.Spell)
        local b, nameB = WeatherRules.spellAt(index * WEATHER.Spell + 17)
        t.eq(a, index)
        t.eq(b, index, "inside a spell the index does not change")
        t.eq(nameA, nameB)
        t.ok(WeatherConfig.States[nameA] ~= nil, "unknown weather " .. tostring(nameA))
    end
end)

t.test("rain, fog and the Qi Bloom never last two spells running; fog never comes into the night", function()
    local last = nil
    for index = 1, 5000 do
        local _, name = WeatherRules.spellAt(index * WEATHER.Spell)
        local state = WeatherConfig.States[name]
        if last and state.Repeat == false then
            t.falsy(last == name, name .. " came twice running at spell " .. index)
        end
        if state.NotAtNight then
            for step = 0, 4 do
                local clock = WeatherRules.clockAt(index * WEATHER.Spell + WEATHER.Spell * step / 4)
                t.ok(WeatherRules.nightAt(clock) <= WEATHER.NightFor, name .. " ran into the night at spell " .. index)
            end
        end
        last = name
    end
end)

t.test("the weather odds follow the weights over a long run (fog and the Qi Bloom are rare)", function()
    local counts, total = {}, 0
    for index = 1, 20000 do
        local _, name = WeatherRules.spellAt(index * WEATHER.Spell)
        counts[name] = (counts[name] or 0) + 1
        total += 1
    end
    t.ok((counts.Clear or 0) > (counts.Rain or 0), "clear skies are more common than rain")
    t.ok((counts.QiBloom or 0) > 0, "the Qi Bloom does come")
    t.ok((counts.QiBloom or 0) / total < 0.12, "the Qi Bloom is rare")
end)

t.test("a change blends from one weather to the next over the transition and then holds", function()
    for index = 2, 400 do
        local start = index * WEATHER.Spell
        local from, to, k = WeatherRules.weatherAt(start)
        t.ok(WeatherConfig.States[from] ~= nil and WeatherConfig.States[to] ~= nil)
        t.ok(k >= 0 and k <= 1)
        local _, name = WeatherRules.spellAt(start)
        t.eq(to, name)
        local f2, t2, k2 = WeatherRules.weatherAt(start + WEATHER.Transition + 1)
        t.eq(f2, t2)
        t.eq(k2, 1, "after the transition the weather is settled")
    end
end)

t.test("a forced clock or weather only counts in Studio (the stub is a live server)", function()
    t.eq(WeatherRules.forced(), nil)
end)

-- ---------- the Codex ----------
t.test("codex rewards: numbered milestones rise, the last is 'Found:All', and each egg has one page", function()
    local last = 0
    local milestones, pages = 0, 0
    for _, reward in CodexRules.Rewards do
        if reward.Kind == "Found" then
            milestones += 1
            t.ok(reward.Count > last, "milestones must rise: " .. reward.Id)
            last = reward.Count
            t.ok(reward.QiPercent >= 0)
        else
            pages += 1
            t.eq(reward.Id, "Set:" .. reward.EggId)
            t.ok(reward.WeaponShare > 0, "a page pays something")
        end
        t.eq(CodexRules.reward(reward.Id), reward)
    end
    t.eq(CodexRules.Rewards[milestones].Id, "Found:All")
    t.eq(CodexRules.Rewards[milestones].Count, CodexRules.Total, "the last milestone is every beast")
    t.eq(pages, #CodexRules.Eggs)
    t.eq(CodexRules.reward("Nope"), nil)
    t.eq(CodexRules.reward(42), nil)
end)

t.test("old saved claims are migrated: an old 'Found:<total>' is 'Found:All'; known and odd ids pass through", function()
    t.eq(CodexRules.savedId("Found:All"), "Found:All")
    t.eq(CodexRules.savedId("Found:" .. CodexRules.Total), "Found:All", "the total at the time of the old id")
    t.eq(CodexRules.savedId("Found:999"), "Found:All")
    t.eq(CodexRules.savedId("Set:BeginnerQiEgg"), "Set:BeginnerQiEgg")
    t.eq(CodexRules.savedId("Found:1"), "Found:1", "a small numbered milestone is itself")
    t.eq(CodexRules.savedId("Found:12abc"), "Found:12abc")
    t.eq(CodexRules.savedId(7), 7)
    t.eq(CodexRules.savedId(nil), nil)
end)

t.test("progress and earning: found beasts count only if the Codex counts them", function()
    local found = {}
    t.eq(CodexRules.count(found), 0)
    t.eq(CodexRules.count({ NotABeast = true }), 0, "an unknown pet does not count")
    for i = 1, 5 do
        found[CodexRules.Pets[i]] = true
    end
    t.eq(CodexRules.count(found), 5)
    local first = CodexRules.Rewards[1]
    local have, goal = CodexRules.progress(first, found)
    t.eq(have, 5)
    t.eq(goal, first.Count)
    t.eq(CodexRules.isEarned(first, found), 5 >= first.Count)
    -- a page is earned by finding everything its egg hatches
    local egg = CodexRules.Eggs[1]
    local page = CodexRules.reward("Set:" .. egg.Id)
    local mine = {}
    t.falsy(CodexRules.isEarned(page, mine))
    for _, entry in egg.Pool do
        mine[entry.PetId] = true
    end
    t.ok(CodexRules.isEarned(page, mine))
    -- everything found earns everything
    local all = {}
    for _, petId in CodexRules.Pets do
        all[petId] = true
    end
    for _, reward in CodexRules.Rewards do
        t.ok(CodexRules.isEarned(reward, all), reward.Id .. " should be earned with every beast found")
    end
end)

t.test("the lasting Qi bonus adds only claimed rewards", function()
    t.eq(CodexRules.qiPercent({}), 0)
    local claimed, expected = {}, 0
    for _, reward in CodexRules.Rewards do
        claimed[reward.Id] = true
        expected += reward.QiPercent
    end
    t.near(CodexRules.qiPercent(claimed), expected, 1e-9)
    t.ok(expected > 0, "the Codex gives some Qi")
    t.eq(CodexRules.qiPercent({ ["Found:Nothing"] = true }), 0, "an unknown claim adds nothing")
end)

t.test("stones for a reward scale with the realm and round nicely", function()
    local reward = CodexRules.Rewards[1]
    local last = 0
    for realm = 1, 12 do
        local stones = CodexRules.stones(reward, realm)
        t.ok(stones >= last, "stones must not fall with the realm")
        last = stones
    end
    t.eq(CodexRules.stones(reward, 0), CodexRules.stones(reward, 1), "below the first realm counts as the first")
    t.eq(CodexRules.stones(reward, 99), CodexRules.stones(reward, 12), "above the last realm counts as the last")
    t.eq(CodexRules.stones(reward, nil), CodexRules.stones(reward, 1))
end)

t.test("eggsOf lists the eggs that hatch a pet, best chance first", function()
    for _, petId in CodexRules.Pets do
        local eggs = CodexRules.eggsOf(petId)
        t.ok(#eggs >= 1, petId .. " is hatched by no egg")
        for i = 2, #eggs do
            t.ok(eggs[i - 1].Percent >= eggs[i].Percent)
        end
    end
    t.eq(#CodexRules.eggsOf("NotABeast"), 0)
end)

-- ---------- factions ----------
t.test("joining and the trial are gated by realm, not by sub-rank", function()
    local joinRealm, trialRealm = GameConfig.Faction.JoinRealm, GameConfig.Faction.TrialRealm
    local firstOf, lastBefore = {}, {}
    for index, rank in GameConfig.Ranks do
        if not firstOf[rank.Realm] then
            firstOf[rank.Realm] = rank
            lastBefore[rank.Realm] = GameConfig.Ranks[index - 1]
        end
    end
    t.ok(FactionRules.canJoin(firstOf[joinRealm].Name), "the first rank of the join realm can join")
    t.falsy(FactionRules.canJoin(lastBefore[joinRealm].Name), "the rank before it cannot")
    t.ok(FactionRules.canJoin(GameConfig.Ranks[#GameConfig.Ranks].Name))
    t.ok(FactionRules.canTrial(firstOf[trialRealm].Name))
    t.falsy(FactionRules.canTrial(lastBefore[trialRealm].Name))
    t.falsy(FactionRules.canJoin(GameConfig.Ranks[1].Name), "a brand-new cultivator cannot join")
    t.falsy(FactionRules.canJoin("Nobody"), "an unknown rank counts as the first realm")
end)

t.test("faction keys and look-ups", function()
    t.eq(FactionRules.key(1234), GameConfig.Faction.KeyPrefix .. "1234")
    t.eq(FactionRules.key("5"), GameConfig.Faction.KeyPrefix .. "5")
    t.eq(FactionRules.get(5), nil)
    t.eq(FactionRules.get("Nobody"), nil)
    t.falsy(FactionRules.isFaction("Nobody"))
    t.eq(FactionRules.weaponFaction("Sword1"), nil, "an ordinary weapon belongs to no faction")
    t.eq(FactionRules.weaponFaction(nil), nil)
end)

t.finish("world")
