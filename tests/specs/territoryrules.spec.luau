-- Which territory a player stands in, and what each one sounds like (shared/TerritoryRules).
local t = require("@env/t")
local TerritoryRules = require("@shared/TerritoryRules")

local T = {
    Orthodox = { X = 0, Z = 0, Radius = 150 },
    Unorthodox = { X = -230, Z = 40, Radius = 100 },
    Demonic = { X = -310, Z = -90, Radius = 100 },
}

t.test("a position is in the territory it is within the radius of, and in none far from all", function()
    t.eq(TerritoryRules.which(10, 10, T), "Orthodox")
    t.eq(TerritoryRules.which(-230, 40, T), "Unorthodox")
    t.eq(TerritoryRules.which(-300, -80, T), "Demonic")
    t.eq(TerritoryRules.which(500, 500, T), nil, "the open plaza belongs to no territory")
    t.eq(TerritoryRules.which(0, 0, {}), nil, "nothing built yet")
end)

t.test("the border does not flicker: the one you are in is kept a little past its radius", function()
    t.eq(TerritoryRules.which(160, 0, T), nil, "just outside, coming from nowhere: not in it yet")
    t.eq(TerritoryRules.which(160, 0, T, "Orthodox"), "Orthodox", "just outside, but you were in it: still in it")
    t.eq(TerritoryRules.which(190, 0, T, "Orthodox"), nil, "well outside: left it")
    t.eq(TerritoryRules.which(140, 0, T), "Orthodox", "inside again: in it")
end)

t.test("where two overlap you stay in yours until the other is clearly nearer", function()
    local close = {
        A = { X = 0, Z = 0, Radius = 100 },
        B = { X = 150, Z = 0, Radius = 100 },
    }
    t.eq(TerritoryRules.which(60, 0, close), "A")
    t.eq(TerritoryRules.which(80, 0, close), "B", "nearer to B and inside both: B, with no current one")
    t.eq(TerritoryRules.which(76, 0, close, "A"), "A", "a hair nearer to B is not enough to switch")
    t.eq(TerritoryRules.which(110, 0, close, "A"), "B", "clearly nearer to B: switched")
end)

t.test("every territory has a bed and a music of its own", function()
    local beds, musics = {}, {}
    for name, sound in TerritoryRules.SOUND do
        t.ok(type(sound.Ambience) == "string" and type(sound.Music) == "string", name .. " names its sounds")
        t.ok(not beds[sound.Ambience], name .. " shares a bed")
        t.ok(not musics[sound.Music], name .. " shares a music")
        beds[sound.Ambience], musics[sound.Music] = true, true
        if sound.Accent then
            t.ok(sound.Accent.Min > 0 and sound.Accent.Max >= sound.Accent.Min, name .. "'s accent timing")
        end
    end
    t.ok(TerritoryRules.SOUND.Orthodox and TerritoryRules.SOUND.Unorthodox and TerritoryRules.SOUND.Demonic, "all three")
end)

t.finish("territoryrules")
