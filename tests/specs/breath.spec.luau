-- The aura's breath (shared/BreathRules): a surge on each breath out, each realm its own character, never too bright, never silent.
local t = require("@env/t")
local BreathRules = require("@shared/BreathRules")

-- runs a breath for `seconds` at 60 fps and returns the surge at each frame
local function run(tier, seconds, seed)
    local state = BreathRules.new(seed or 1)
    local surges, flickers = {}, {}
    local now = 0
    for _ = 1, math.floor(seconds * 60) do
        local surge, wave, flicker = BreathRules.step(state, 1 / 60, now, tier)
        t.ok(wave >= 0 and wave <= 1, "the chest stays in 0..1")
        table.insert(surges, surge)
        table.insert(flickers, flicker)
        now += 1 / 60
    end
    return surges, flickers
end

t.test("every realm has a personality, and nothing is missing from it", function()
    for tier = 1, 12 do
        local p = BreathRules.Personality[tier]
        t.ok(p ~= nil, "realm " .. tier)
        t.ok(p.Attack > 0 and p.Release > 0 and p.Hold > 0, "realm " .. tier .. " has timings")
        t.ok(p.Depth > 0 and p.Depth <= 0.7, "realm " .. tier .. " depth stays modest")
        t.ok(p.Flicker >= 0 and p.Flicker <= 0.3, "realm " .. tier .. " flicker stays small")
    end
end)

t.test("each breath out swells the aura, and it settles again before the next", function()
    for tier = 1, 12 do
        local surges = run(tier, 20)
        local peak, low = 0, 1
        for i = 600, #surges do -- after the first cycles
            peak = math.max(peak, surges[i])
            low = math.min(low, surges[i])
        end
        t.ok(peak > 0.5, "realm " .. tier .. " swells (peak " .. string.format("%.2f", peak) .. ")")
        t.ok(peak <= 1.0001, "realm " .. tier .. " never over 1")
        t.ok(low < 0.45, "realm " .. tier .. " settles between breaths (low " .. string.format("%.2f", low) .. ")")
    end
end)

t.test("the swell comes once a breath: about every 5 seconds", function()
    local surges = run(1, 30)
    local crossings = 0
    for i = 2, #surges do
        if surges[i - 1] < 0.5 and surges[i] >= 0.5 then
            crossings += 1
        end
    end
    t.ok(crossings >= 5 and crossings <= 7, "6 breaths in 30 seconds, got " .. crossings)
end)

t.test("a heartbeat realm beats twice a breath", function()
    local surges = run(7, 10)
    local rises = 0
    for i = 2, #surges do
        if surges[i] > surges[i - 1] + 1e-6 and surges[i - 1] <= surges[math.max(1, i - 2)] + 1e-6 then
            rises += 1 -- a new rise begins
        end
    end
    local single = run(1, 10)
    local singleRises = 0
    for i = 2, #single do
        if single[i] > single[i - 1] + 1e-6 and single[i - 1] <= single[math.max(1, i - 2)] + 1e-6 then
            singleRises += 1
        end
    end
    t.ok(rises > singleRises, "Divine rises more often than Qi Awakening (" .. rises .. " against " .. singleRises .. ")")
end)

t.test("brightness and rate stay in safe bounds for every realm at every surge", function()
    for tier = 1, 12 do
        for s = 0, 10 do
            local surge = s / 10
            for _, flicker in { -0.3, 0, 0.3 } do
                local b = BreathRules.brightness(tier, surge, flicker)
                t.ok(b >= 0.6 and b <= 1.4, "realm " .. tier .. " brightness " .. b)
            end
            local r = BreathRules.rate(tier, surge)
            t.ok(r >= 1 and r <= 1.8, "realm " .. tier .. " rate " .. r)
        end
    end
    t.near(BreathRules.brightness(1, 0, 0), 0.86, 1e-9, "between breaths a little under the set level")
end)

t.test("the flicker is its own for each aura and small", function()
    local a = select(2, run(5, 5, 11))
    local b = select(2, run(5, 5, 523))
    local same, big = true, 0
    for i = 1, #a do
        if math.abs(a[i] - b[i]) > 1e-9 then
            same = false
        end
        big = math.max(big, math.abs(a[i]))
    end
    t.ok(not same, "two auras do not flicker in step")
    t.ok(big <= BreathRules.Personality[5].Flicker + 1e-9, "never over its personality's share")
end)

t.test("only the prismatic realm's colours drift", function()
    for tier = 1, 11 do
        t.eq(BreathRules.hue(tier, 3), nil, "realm " .. tier)
    end
    local lo, hi = 1, 0
    for i = 0, 440 do
        local h = BreathRules.hue(12, i * 0.1)
        t.ok(h >= 0 and h <= 1)
        lo, hi = math.min(lo, h), math.max(hi, h)
    end
    t.ok(lo < 0.05 and hi > 0.95, "the whole palette is travelled")
end)

t.finish("breath")
