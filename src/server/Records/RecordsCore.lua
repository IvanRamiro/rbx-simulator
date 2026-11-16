-- The Hall of Records' rules on stored data, with no services in them (RecordsService runs them inside UpdateAsync, so every
-- server agrees): reading a stored Firsts or Rarest record safely, and merging new claims into it.
--   Firsts  { [first id] = { u = userId, n = name then, t = unix time } }: a first is set once; a claim never replaces one.
--   Rarest  { { id, u, n, p = petId, s = size, e = eggId, o = odds (0-1), t }, ... }: the rarest hatches, rarest first, capped.
local RecordsCore = {}

local function isEntry(e)
    return typeof(e) == "table" and typeof(e.u) == "number" and e.u == e.u and typeof(e.t) == "number"
end

local function cleanName(n)
    return if typeof(n) == "string" then string.sub(n, 1, 40) else ""
end

-- validIds: { [first id] = anything } (RecordsConfig.FirstById): an unknown id is dropped from what this server shows (it is
-- left in the store untouched).
function RecordsCore.sanitizeFirsts(raw, validIds)
    local out = {}
    if typeof(raw) ~= "table" then
        return out
    end
    for id, e in raw do
        if typeof(id) == "string" and isEntry(e) and (validIds == nil or validIds[id]) then
            out[id] = { u = math.floor(e.u), n = cleanName(e.n), t = math.floor(e.t) }
        end
    end
    return out
end

-- The stored record with every pending claim that is still free added (ones already taken are left as they are).
-- Returns the record to store, or nil when nothing was added (UpdateAsync then cancels the write), and the record as it now is.
function RecordsCore.mergeFirsts(stored, pending)
    local record = if typeof(stored) == "table" then stored else {}
    local added = false
    for id, claim in pending do
        if record[id] == nil and isEntry(claim) then
            record[id] = { u = claim.u, n = cleanName(claim.n), t = claim.t }
            added = true
        end
    end
    return if added then record else nil, record
end

local function isHatch(e)
    return isEntry(e) and typeof(e.id) == "string" and typeof(e.p) == "string" and typeof(e.o) == "number"
        and e.o == e.o and e.o > 0 and e.o <= 1
end

local function rarer(a, b)
    if a.o ~= b.o then
        return a.o < b.o
    end
    if a.t ~= b.t then
        return a.t < b.t -- (the same odds: the earlier hatch first)
    end
    return a.id < b.id
end

function RecordsCore.sanitizeRarest(raw, keep)
    local out = {}
    if typeof(raw) ~= "table" then
        return out
    end
    local seen = {}
    for _, e in raw do
        if isHatch(e) and not seen[e.id] then
            seen[e.id] = true
            table.insert(out, { id = string.sub(e.id, 1, 40), u = math.floor(e.u), n = cleanName(e.n), p = e.p,
                s = if typeof(e.s) == "string" then e.s else "Normal", e = if typeof(e.e) == "string" then e.e else "", o = e.o,
                t = math.floor(e.t) })
        end
    end
    table.sort(out, rarer)
    while #out > keep do
        table.remove(out)
    end
    return out
end

-- Whether a hatch of these odds belongs in `list` (the rarest `keep`, rarest first): rare enough at all, and the list not full
-- or the hatch rarer than its last.
function RecordsCore.qualifies(list, odds, keep, mostLikely)
    if typeof(odds) ~= "number" or odds <= 0 or odds > mostLikely then
        return false
    end
    return #list < keep or odds < list[#list].o
end

-- The stored list with the pending hatches added, kept to the rarest `keep`. Returns the list to store, or nil when none of the
-- pending ones made it (the write is cancelled), and the list as it now is.
function RecordsCore.mergeRarest(stored, pending, keep)
    local list = RecordsCore.sanitizeRarest(stored, keep)
    local known = {}
    for _, e in list do
        known[e.id] = true
    end
    local merged = table.clone(list)
    for _, e in pending do
        if isHatch(e) and not known[e.id] then
            table.insert(merged, e)
        end
    end
    merged = RecordsCore.sanitizeRarest(merged, keep)
    local madeIt = false
    for _, e in merged do
        if not known[e.id] then
            madeIt = true
        end
    end
    return if madeIt then merged else nil, merged
end

-- A feed key that sorts by time (MemoryStore SortedMap keys sort as strings): the time to the millisecond, then a tie-breaker.
function RecordsCore.feedKey(serverTime, tie)
    return string.format("%013d_%04d", math.floor(serverTime * 1000), tie % 10000)
end

return RecordsCore
