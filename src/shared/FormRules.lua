-- Combat forms (the owner, 2026-11-24: "add the combo system ... combat forms ... each with unique attacks, effects and combos", "start a new and
-- fresh battle attacks"; then: "a combo and combat forms based on the WEAPONS, not for elements: all types of swords have the same combos and
-- forms, and all types of spears have the same combos and forms").
--
-- A weapon's FAMILY is its kind: Sword, Spear, or Palm (bare hands: no weapon equipped). Every weapon of a family shares that family's forms and
-- combos, whatever its tier, element or name: the realm weapons, the forged ones and the faction weapons alike. The weapon still sets the damage
-- tier, the look and the aura; the form sets the chain of strikes: how many, how hard, how fast, how wide, which one finishes, how the target
-- reacts. A player has a chosen form for each family (the server keeps it: the "CombatForm" attribute); if the chosen one doesn't belong to the
-- weapon in hand, or isn't unlocked, the family's first form is used. A form unlocks at a realm (UnlockRealm: 1 = from the start). The server owns
-- the choice, the chain and every number here; a client only shows.
--
-- THE COMBO ACCELERATES (the owner, 2026-11-24: "the fourth attack becomes faster and more powerful"): in the quick forms (Gale, Swallow, Flurry) the four lights come
-- quicker and harder one after another (Cd 0.66, 0.62, 0.58, 0.54 and Dmg 0.50, 0.52, 0.58, 0.60: the same sums as four steps of 0.6 and 0.55, so the form's damage per second
-- is exactly what it was), and each clip is played at its own step's pace.
--
-- THE BALANCE RULE (so guardian fights and the egg heist keep their pace): a step has Dmg and Cd, multiples of the weapon's own strike damage and
-- cooldown. A form's damage per second over its whole chain is sum(Dmg) / sum(Cd) of the weapon's own, and must stay within DPS_BAND of 1:
-- forms differ in HOW they deal damage (many light strikes, a few heavy ones, a huge finisher), never in how much. tests/specs/forms.spec.luau
-- enforces it. The combo counter below is for show: it gives no damage, so a long chain can't be farmed for power.
--
--   FormRules.Families[family]            the family's form ids in order, the first the default (every weapon kind has one, and "Palm")
--   FormRules.Forms[id]                   { Id, Family, Name, Identity, UnlockRealm, Chain = { { Name, Dmg, Cd, Range, Arc, Reaction } ... } }
--   FormRules.familyOf(id)                the family a form belongs to, or nil
--   FormRules.unlocked(id, realm)         whether a player in realm number `realm` (Shop.playerRealmIndex) can use it
--   FormRules.resolve(family, chosen, realm)  the form to fight with: the chosen one if it is this family's and unlocked (nothing chooses one now), else the highest the realm has unlocked
--   FormRules.sanitizeChoices(raw)        a saved table of chosen forms ({ Sword = id, Spear = id }) reduced to the valid ones: a form of that very family (unlocking is
--                                         checked where it is used: a form not yet unlocked is simply not fought with)
--   FormRules.stepOf(id, last, now, cd)   the strike's place in the chain: last = { Form, Step, At } or nil; cd = the weapon's cooldown
--   FormRules.strike(id, step, base)      the numbers of one strike: base = { Damage, Range, Arc, Cooldown } of the weapon
--   FormRules.flow(family, realm, last, now, cooldown)   the form of the next strike: the combo runs on from one unlocked form's finisher into the next (FormRules.Cycle)
--   FormRules.plan(family, chosen, realm, base, last, now)   the strike a player makes now (server and client both use it); chosen is nil: the flow decides the form
--   FormRules.dps(id)                     the form's damage per second as a multiple of the weapon's own
--   FormRules.countHit(counter, now)      the combo counter after a landed hit: { Hits, At }
--   FormRules.tierOf(hits)                the name of the counter's tier, or nil
local FormRules = {}

FormRules.GRACE = 0.6 -- seconds past a strike's own cooldown in which the next strike still continues the chain
FormRules.SWITCH_GAP = 1.5 -- seconds between two changes of form
FormRules.DPS_BAND = 0.02 -- how far a form's damage per second may stray from the weapon's own (a share)
FormRules.MAX_ARC = 170 -- degrees: no strike reaches behind the striker

-- Reaction: how the target answers a landed strike (GuardianReact): Light flinch, Heavy stagger, Launch a knock back (the finisher only).
FormRules.Forms = {
    -- ---------- swords ----------
    Crescent = {
        Family = "Sword", Name = "Crescent Form", UnlockRealm = 1,
        Identity = "Balanced. Two clean cuts, then a hard overhead finisher.",
        Chain = {
            { Name = "Rising Cut", Dmg = 0.85, Cd = 0.9, Range = 1, Arc = 1, Reaction = "Light" },
            { Name = "Falling Cut", Dmg = 0.85, Cd = 0.9, Range = 1, Arc = 1, Reaction = "Light" },
            { Name = "Heaven Splitter", Dmg = 1.5, Cd = 1.4, Range = 1.05, Arc = 1.1, Reaction = "Launch" },
        },
    },
    Gale = {
        Family = "Sword", Name = "Gale Form", UnlockRealm = 3,
        Identity = "Fast and flowing. Four quick cuts close in, then a spin that cuts all round.",
        Chain = {
            { Name = "Swift Cut", Dmg = 0.50, Cd = 0.66, Range = 0.85, Arc = 1.15, Reaction = "Light" },
            { Name = "Cross Cut", Dmg = 0.52, Cd = 0.62, Range = 0.85, Arc = 1.15, Reaction = "Light" },
            { Name = "Spin Cut", Dmg = 0.58, Cd = 0.58, Range = 0.85, Arc = 1.3, Reaction = "Light" },
            { Name = "Rush Cut", Dmg = 0.60, Cd = 0.54, Range = 0.9, Arc = 1.15, Reaction = "Heavy" },
            { Name = "Storm Ring", Dmg = 1.6, Cd = 1.4, Range = 0.95, Arc = 1.9, Reaction = "Launch" },
        },
    },
    Mountain = {
        Family = "Sword", Name = "Mountain Form", UnlockRealm = 6,
        Identity = "Slow and heavy. Two crushing blows, then a huge finisher that is worth the wait.",
        Chain = {
            { Name = "Heavy Cut", Dmg = 0.9, Cd = 1.0, Range = 1, Arc = 0.9, Reaction = "Heavy" },
            { Name = "Heavy Chop", Dmg = 0.9, Cd = 1.0, Range = 1, Arc = 0.9, Reaction = "Heavy" },
            { Name = "Mountain Fall", Dmg = 2.8, Cd = 2.6, Range = 1.1, Arc = 1.2, Reaction = "Launch" },
        },
    },
    -- ---------- spears ----------
    Lancer = {
        Family = "Spear", Name = "Lancer Form", UnlockRealm = 1,
        Identity = "Balanced. Two long thrusts, then a wide sweep.",
        Chain = {
            { Name = "Straight Thrust", Dmg = 0.85, Cd = 0.9, Range = 1, Arc = 1, Reaction = "Light" },
            { Name = "Twin Thrust", Dmg = 0.85, Cd = 0.9, Range = 1, Arc = 1, Reaction = "Light" },
            { Name = "Wide Sweep", Dmg = 1.5, Cd = 1.4, Range = 0.72, Arc = 2.4, Reaction = "Launch" },
        },
    },
    Swallow = {
        Family = "Spear", Name = "Swallow Form", UnlockRealm = 3,
        Identity = "Quick and darting. Four fast jabs, then a whirl all round.",
        Chain = {
            { Name = "Quick Jab", Dmg = 0.50, Cd = 0.66, Range = 0.8, Arc = 1.2, Reaction = "Light" },
            { Name = "Double Jab", Dmg = 0.52, Cd = 0.62, Range = 0.8, Arc = 1.2, Reaction = "Light" },
            { Name = "Low Jab", Dmg = 0.58, Cd = 0.58, Range = 0.8, Arc = 1.2, Reaction = "Light" },
            { Name = "Rising Jab", Dmg = 0.60, Cd = 0.54, Range = 0.85, Arc = 1.2, Reaction = "Heavy" },
            { Name = "Whirl Sweep", Dmg = 1.6, Cd = 1.4, Range = 0.7, Arc = 2.6, Reaction = "Launch" },
        },
    },
    Tiger = {
        Family = "Spear", Name = "Tiger Form", UnlockRealm = 6,
        Identity = "Slow and fierce. Two hard thrusts, then a slam that drives the target back.",
        Chain = {
            { Name = "Fang Thrust", Dmg = 0.9, Cd = 1.0, Range = 0.9, Arc = 1, Reaction = "Heavy" },
            { Name = "Claw Thrust", Dmg = 0.9, Cd = 1.0, Range = 0.9, Arc = 1, Reaction = "Heavy" },
            { Name = "Tiger Slam", Dmg = 2.8, Cd = 2.6, Range = 0.8, Arc = 2, Reaction = "Launch" },
        },
    },
    -- ---------- bare hands (no weapon equipped) ----------
    Fist = {
        Family = "Palm", Name = "Fist Form", UnlockRealm = 1,
        Identity = "Plain and quick. Two punches, then a palm strike that sends the target back.",
        Chain = {
            { Name = "Straight Punch", Dmg = 0.85, Cd = 0.9, Range = 1, Arc = 1, Reaction = "Light" },
            { Name = "Hook Punch", Dmg = 0.85, Cd = 0.9, Range = 1, Arc = 1, Reaction = "Light" },
            { Name = "Palm Strike", Dmg = 1.5, Cd = 1.4, Range = 1.05, Arc = 1.1, Reaction = "Launch" },
        },
    },
    -- (2026-11-24: bare hands get two more forms, as swords and spears have, so fighting without a weapon is not the poorer choice; the same damage per second as
    -- every other form, the same unlocks as Gale and Mountain)
    Flurry = {
        Family = "Palm", Name = "Flurry Form", UnlockRealm = 3,
        Identity = "Fast and relentless. Four quick punches from every angle, then a double palm that blasts the target back.",
        Chain = {
            { Name = "Jab", Dmg = 0.50, Cd = 0.66, Range = 0.85, Arc = 1.15, Reaction = "Light" },
            { Name = "Cross", Dmg = 0.52, Cd = 0.62, Range = 0.85, Arc = 1.15, Reaction = "Light" },
            { Name = "Body Hook", Dmg = 0.58, Cd = 0.58, Range = 0.85, Arc = 1.3, Reaction = "Light" },
            { Name = "Uppercut", Dmg = 0.60, Cd = 0.54, Range = 0.85, Arc = 1.15, Reaction = "Heavy" },
            { Name = "Double Palm", Dmg = 1.6, Cd = 1.4, Range = 0.95, Arc = 1.5, Reaction = "Launch" },
        },
    },
    Stone = {
        Family = "Palm", Name = "Stone Form", UnlockRealm = 6,
        Identity = "Slow and crushing. Two hammer fists, then a two-handed crush worth the wait.",
        Chain = {
            { Name = "Hammer Fist", Dmg = 0.9, Cd = 1.0, Range = 1, Arc = 0.9, Reaction = "Heavy" },
            { Name = "Backhand Hammer", Dmg = 0.9, Cd = 1.0, Range = 1, Arc = 0.9, Reaction = "Heavy" },
            { Name = "Mountain Crush", Dmg = 2.8, Cd = 2.6, Range = 1.0, Arc = 1.3, Reaction = "Launch" },
        },
    },
}
FormRules.Families = {
    Sword = { "Crescent", "Gale", "Mountain" },
    Spear = { "Lancer", "Swallow", "Tiger" },
    Palm = { "Fist", "Flurry", "Stone" },
}

for family, ids in FormRules.Families do
    for _, id in ids do
        assert(FormRules.Forms[id] and FormRules.Forms[id].Family == family, "FormRules: " .. id .. " is not a " .. family .. " form")
        FormRules.Forms[id].Id = id
    end
end

function FormRules.familyOf(id)
    local form = typeof(id) == "string" and FormRules.Forms[id]
    return if form then form.Family else nil
end

-- The player's chosen forms as saved with them (PlayerData "Forms"): { [family] = form id }, only a form that belongs to the family it is saved under.
-- Anything else (a table, a number, a form of another family, an id this version doesn't know, a family that doesn't exist) is dropped.
function FormRules.sanitizeChoices(raw)
    local choices = {}
    if typeof(raw) == "table" then
        for family, ids in FormRules.Families do
            local id = raw[family]
            if typeof(id) == "string" and table.find(ids, id) then
                choices[family] = id
            end
        end
    end
    return choices
end

function FormRules.unlocked(id, realm)
    local form = typeof(id) == "string" and FormRules.Forms[id]
    return form ~= false and form ~= nil and typeof(realm) == "number" and realm >= form.UnlockRealm
end

function FormRules.resolve(family, chosen, realm)
    local ids = FormRules.Families[family]
    if not ids then
        return nil
    end
    if FormRules.familyOf(chosen) == family and FormRules.unlocked(chosen, realm) then
        return chosen
    end
    -- no (valid) choice: the highest form of the family that the realm has unlocked, the first for anyone below them all. There is no form button
    -- (the owner, 2026-11-24): a player fights with the best form they have, and a new form arrives with the realm that opens it.
    local best = ids[1]
    for _, id in ids do
        if FormRules.unlocked(id, realm) then
            best = id
        end
    end
    return best
end

-- The strike's place in the chain, 1 to #Chain. A strike continues the chain when it comes before the last one's cooldown and the grace are up
-- (and is the same form); otherwise it is the first strike again. The strike after the last is the first.
function FormRules.stepOf(id, last, now, cooldown)
    local form = FormRules.Forms[id]
    if not form then
        return 1
    end
    local chain = form.Chain
    if last and last.Form == id and typeof(last.At) == "number" and typeof(last.Step) == "number" and chain[last.Step] then
        local since = now - last.At
        if since >= 0 and since < cooldown * chain[last.Step].Cd + FormRules.GRACE then
            return last.Step % #chain + 1
        end
    end
    return 1
end

-- One strike's numbers from the weapon's own: Damage and Cooldown scale by the step's Dmg and Cd, Range and Arc by its Range and Arc (the arc
-- never past MAX_ARC, the range never under 3 studs). Name, Finisher (the last strike), Reaction and Escalation (0 to 1 along the chain) come along.
function FormRules.strike(id, step, base)
    local form = FormRules.Forms[id]
    local entry = form and form.Chain[step]
    if not entry then
        return nil
    end
    return {
        Form = id, Family = form.Family, Step = step, Name = entry.Name, Finisher = step == #form.Chain, Reaction = entry.Reaction,
        Escalation = if #form.Chain > 1 then (step - 1) / (#form.Chain - 1) else 0, -- how deep in the chain: 0 at the first strike, 1 at the finisher (the effects build with it)
        Damage = base.Damage * entry.Dmg, Cooldown = base.Cooldown * entry.Cd,
        Range = math.max(3, base.Range * entry.Range), Arc = math.min(FormRules.MAX_ARC, base.Arc * entry.Arc),
    }
end

function FormRules.dps(id)
    local damage, time = 0, 0
    for _, entry in FormRules.Forms[id].Chain do
        damage += entry.Dmg
        time += entry.Cd
    end
    return damage / time
end

-- THE FLOW: with no form button the forms are one combo (the owner, 2026-11-24: "five connected attack animations that transition naturally into one another"; "no other button
-- to press"). A family's unlocked forms run in the order of FormRules.Cycle: a combo begins with the first, and when its finisher has landed the same press-by-press chain goes on
-- into the next form without a pause (the chain window is the finisher's own cooldown and the grace), and after the last begins again with the first. A sword's player of
-- realm 3 strikes five quick cuts and a spin finisher (Gale), then three balanced ones (Crescent), and so on; at realm 6 a third, heavy form (Mountain) joins. The window lapsing
-- (a pause) begins the cycle again at its first form.
FormRules.Cycle = {
    Sword = { "Gale", "Crescent", "Mountain" },
    Spear = { "Swallow", "Lancer", "Tiger" },
    Palm = { "Flurry", "Fist", "Stone" },
}

-- the form of the next strike in the flow, from the last strike ({ Form, Step, At } or nil), the time and the weapon's cooldown; nil for an unknown family
function FormRules.flow(family, realm, last, now, cooldown)
    local order = FormRules.Cycle[family]
    local list = {}
    for _, id in order or {} do
        if FormRules.unlocked(id, realm) then
            table.insert(list, id)
        end
    end
    if #list == 0 then
        local ids = FormRules.Families[family]
        return ids and ids[1] or nil -- (a realm below every form's: the family's first)
    end
    local form = last and typeof(last.Form) == "string" and FormRules.Forms[last.Form]
    local at = form and table.find(list, last.Form)
    if at and typeof(last.Step) == "number" and form.Chain[last.Step] and typeof(last.At) == "number" then
        local since = now - last.At
        if since >= 0 and since < cooldown * form.Chain[last.Step].Cd + FormRules.GRACE then
            if last.Step < #form.Chain then
                return last.Form -- (the chain goes on)
            end
            return list[at % #list + 1] -- (the finisher is done: on into the next form)
        end
    end
    return list[1]
end

-- The strike a player makes now, from their weapon's family, the form they chose for it, their realm number, the weapon's own numbers
-- (base = { Damage, Range, Arc, Cooldown }), their last strike ({ Form, Step, At } or nil) and the time. The server decides every strike with
-- this, and the client calls it for the strike it shows at once, so the two can't disagree about the chain. nil for an unknown family.
function FormRules.plan(family, chosen, realm, base, last, now)
    local id
    if FormRules.familyOf(chosen) == family and FormRules.unlocked(chosen, realm) then
        id = chosen
    else
        id = FormRules.flow(family, realm, last, now, base.Cooldown)
    end
    if not id then
        return nil
    end
    return FormRules.strike(id, FormRules.stepOf(id, last, now, base.Cooldown), base)
end

-- ---------- the combo counter ----------
-- Consecutive landed hits, for show (no damage comes of it). A hit within WINDOW seconds of the last landed one adds to the count; a longer
-- gap starts it again at one. A miss does not add (and the client lets the count lapse after WINDOW). Tiers are named in plain words.
FormRules.Counter = {
    WINDOW = 3.0, -- (longer than the slowest finisher's recovery, 2.2 s for the Tiger and Mountain forms: with 2.2 the count restarted after every heavy finisher)
    Tiers = { { Hits = 5, Name = "Nice" }, { Hits = 10, Name = "Great" }, { Hits = 20, Name = "Amazing" }, { Hits = 40, Name = "Legendary" } },
}

function FormRules.countHit(counter, now)
    if counter and typeof(counter.At) == "number" and now - counter.At >= 0 and now - counter.At <= FormRules.Counter.WINDOW then
        return { Hits = counter.Hits + 1, At = now }
    end
    return { Hits = 1, At = now }
end

function FormRules.tierOf(hits)
    local name = nil
    for _, tier in FormRules.Counter.Tiers do
        if hits >= tier.Hits then
            name = tier.Name
        end
    end
    return name
end

return FormRules
