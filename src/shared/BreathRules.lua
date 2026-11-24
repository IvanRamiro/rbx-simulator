-- The aura's breath (the owner, 2026-11-24: "make auras feel alive; some of it looks static"). Every realm's aura now breathes with the body: the lotus seat
-- breathes on a 5 second loop (MeditationPoses LOTUS.Loop, on os.clock), and as the chest tops out and the breath goes out the aura SURGES (more
-- particles, brighter, the outline and light flare) and settles again, the way Realm 1's vortex always did. Each realm has its own character in how it
-- does that (a heartbeat for Divine, a flame's flicker for the solar and lava realms, a slow tide for the water and silver ones, a slow gathering and a
-- snap for the Void). Pure numbers, so the spec runs it; RealmAura applies the result.
--
--   BreathRules.new(seed)                    a breath's state (seed: each aura flickers on its own)
--   BreathRules.step(state, dt, now, tier)   -> surge (0..1, the exhale's swell), wave (0..1, the chest: 1 at the top), flicker (about -1..1)
--   BreathRules.brightness(tier, surge, flicker)   the multiplier for an emitter's Brightness
--   BreathRules.rate(tier, surge)                  the multiplier for an emitter's Rate
--   BreathRules.hue(tier, now)               0..1 along the realm's palette for a realm whose colours drift (Eternal), else nil
local BreathRules = {}

BreathRules.LOOP = 5   -- seconds: the lotus seat's breath
BreathRules.LAG = 0.3  -- the chest lags the loop by this (radians, as RealmAura always had it)

-- Attack: seconds to rise to a surge; Release: seconds to settle; Hold: how long the swell is held once risen before it lets go (seconds);
-- Depth: how big the swell is (a share); Flicker: the size of the random shimmer (a share of brightness); Beats: extra beats after the first
-- ({ afterSeconds, strength }); Hue: the colours drift along the palette (seconds for a whole turn)
BreathRules.Personality = {
    [1] = { Attack = 0.15, Release = 1.2, Hold = 1.1, Depth = 0.45, Flicker = 0.03 },                                  -- jade: the breath out, as it always was
    [2] = { Attack = 0.6, Release = 2.0, Hold = 1.0, Depth = 0.35, Flicker = 0.03 },                                   -- teal: a tide
    [3] = { Attack = 0.25, Release = 1.6, Hold = 1.1, Depth = 0.35, Flicker = 0.05 },                                  -- gold: a steady radiance
    [4] = { Attack = 0.2, Release = 1.4, Hold = 1.1, Depth = 0.45, Flicker = 0.06 },                                   -- blue
    [5] = { Attack = 0.1, Release = 0.9, Hold = 0.9, Depth = 0.55, Flicker = 0.22 },                                   -- solar: a flame's flicker
    [6] = { Attack = 0.7, Release = 2.4, Hold = 1.2, Depth = 0.3, Flicker = 0.02 },                                    -- silver: calm, slow
    [7] = { Attack = 0.08, Release = 0.45, Hold = 0.1, Depth = 0.6, Flicker = 0.1, Beats = { { 0.34, 0.75 } } },        -- crimson: a heartbeat, two beats
    [8] = { Attack = 0.9, Release = 2.2, Hold = 1.3, Depth = 0.4, Flicker = 0.12 },                                    -- violet: a slow swell, stars twinkling
    [9] = { Attack = 1.1, Release = 0.25, Hold = 0.2, Depth = 0.5, Flicker = 0.04 },                                   -- void: draws in slowly, then lets go at once
    [10] = { Attack = 0.35, Release = 1.8, Hold = 0.05, Depth = 0.45, Flicker = 0.06, Beats = { { 0.5, 0.5 } } },       -- rose: a wave and its echo
    [11] = { Attack = 0.12, Release = 1.0, Hold = 0.9, Depth = 0.6, Flicker = 0.25 },                                  -- lava: irregular, hot
    [12] = { Attack = 0.8, Release = 2.6, Hold = 1.4, Depth = 0.5, Flicker = 0.05, Hue = 22 },                         -- prismatic: a great slow tide, colours drifting
}

local TAU = math.pi * 2

function BreathRules.new(seed)
    return { surge = 0, hold = 0, timer = 0, wasRising = false, beats = {}, seed = (seed or 0) % 1000 }
end

local function personality(tier)
    return BreathRules.Personality[tier] or BreathRules.Personality[1]
end

function BreathRules.step(state, dt, now, tier)
    local p = personality(tier)
    local rising = math.cos(TAU * now / BreathRules.LOOP - BreathRules.LAG)
    if state.wasRising and rising <= 0 then
        state.hold, state.timer = 1, p.Attack + p.Hold -- a breath out begins as the chest tops out: held until it has risen, and a while
        for _, beat in p.Beats or {} do
            table.insert(state.beats, { after = beat[1], strength = beat[2] })
        end
    end
    state.wasRising = rising > 0
    for i = #state.beats, 1, -1 do
        local beat = state.beats[i]
        beat.after -= dt
        if beat.after <= 0 then
            state.hold, state.timer = math.max(state.hold, beat.strength), p.Attack + p.Hold
            table.remove(state.beats, i)
        end
    end
    state.surge += (state.hold - state.surge) * math.min(1, dt / (if state.hold > state.surge then p.Attack else p.Release)) -- in fast, out slow (or the other way for the Void)
    state.timer -= dt
    if state.timer <= 0 then
        state.hold = 0 -- let go
    end
    local wave = 0.5 + 0.5 * rising
    local s = state.seed
    local flicker = (math.sin(now * 7.3 + s) + 0.6 * math.sin(now * 11.9 + s * 2.1) + 0.4 * math.sin(now * 3.1 + s * 0.7)) / 2
    return state.surge, wave, flicker * p.Flicker
end

-- an emitter's Brightness: a little under its set level between swells, over it at the top of one
function BreathRules.brightness(tier, surge, flicker)
    local p = personality(tier)
    return math.clamp(0.86 + p.Depth * 0.7 * surge + flicker, 0.6, 1.4)
end

-- an emitter's Rate: more particles on the exhale
function BreathRules.rate(tier, surge)
    return 1 + personality(tier).Depth * 1.1 * surge
end

function BreathRules.hue(tier, now)
    local p = personality(tier)
    if not p.Hue then
        return nil
    end
    return 0.5 + 0.5 * math.sin(TAU * now / p.Hue)
end

return BreathRules
