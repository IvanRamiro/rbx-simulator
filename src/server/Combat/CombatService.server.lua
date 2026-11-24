-- Resolves strikes (GameConfig.Combat, WeaponKinds). The client fires CombatEvent with no arguments;
-- the server decides the weapon (the one equipped, or the Qi Palm), the cooldown, the target and
-- the damage.
--
-- A target is a Model tagged GameConfig.Combat.TargetTag with a PrimaryPart and a HitRadius
-- attribute (studs round the PrimaryPart's centre). A strike lands on the nearest target within the
-- strike's Arc of facing and Range, unless its "Invulnerable" attribute is set.
--
-- COMBAT FORMS (shared/FormRules; the owner, 2026-11-24): every weapon of a family (Sword, Spear, bare-hands Palm) shares that family's forms. The
-- strike's damage, range, arc and cooldown are the weapon's own scaled by the step of the player's form (FormRules.plan, which the client runs too
-- for the strike it shows at once); the server keeps the chain per player, so a client can't choose a step, a form it hasn't unlocked or a faster
-- cooldown. FormEvent(formId) chooses a form: it is checked here and kept in the player's "Form<Family>" attribute. A landing strike fires
-- Combat.Hit; every strike is relayed to all clients (CombatEvent: striker, kind ("Palm", "Sword" or "Spear"), hit position or nil, the strike's
-- step in its form's chain, and for a strike that landed: its damage (a whole number), true if it was critical, and the target it struck; then
-- the form's id and the combo counter: consecutive landed hits, for show).
--
-- A landing strike may be critical (GameConfig.Combat.Crit): rolled here, never by a client.
--
-- Drawing and sheathing (the owner, 2026-11-11: "add equip and unequip for weapons"): WeaponDrawEvent(wanted) sets the
-- player's "WeaponDrawn" attribute, which keeps their weapon in the hand (CombatFx) until they sheathe it. Only a player
-- with a weapon, alive, not cultivating and not carrying an egg can draw; starting to cultivate, picking up an egg,
-- changing weapon and respawning sheathe it. A strike with a weapon draws it.
--
-- Every stored weapon (ServerStorage.Weapons: the flying sword and the realm weapons, OutfitBuilder)
-- is copied to ReplicatedStorage.Weapons so clients can show it striking.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local FormRules = require(ReplicatedStorage:WaitForChild("FormRules"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Combat = require(script.Parent:WaitForChild("Combat"))
local MovementGuard = require(script.Parent.Parent:WaitForChild("Security"):WaitForChild("MovementGuard"))
local PlayerData = require(script.Parent.Parent:WaitForChild("Data"):WaitForChild("PlayerData"))
local GoalBook = require(script.Parent.Parent:WaitForChild("Rewards"):WaitForChild("GoalBook"))

local COOLDOWN_SLACK = 0.15 -- the share of a cooldown a request may come early: latency, not cheating
local lastStrike = {} -- [player] = { Form, Step, At } (FormRules.plan): the chain's last strike
local comboCount = {} -- [player] = { Hits, At } (FormRules.countHit): consecutive landed hits, for show
local lastFormChange = {} -- [player] = when they last chose a form
-- [player] = when their next strike is due. It moves on by a whole cooldown from when the last was
-- due, not from when it arrived, so coming early can't add up: a client firing as early as the slack
-- allows gets the same strikes a second as anyone else.
local nextStrike = {}
local roll = Random.new() -- critical strikes

do
    local stored = ServerStorage:FindFirstChild("Weapons")
    if stored then
        local folder = ReplicatedStorage:FindFirstChild("Weapons") or Instance.new("Folder")
        folder.Name = "Weapons"
        for _, source in stored:GetChildren() do
            local old = folder:FindFirstChild(source.Name)
            if old then
                old:Destroy()
            end
            source:Clone().Parent = folder
        end
        folder.Parent = ReplicatedStorage
    end
end

-- ---------- drawing and sheathing ----------
local function canDraw(player)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    return humanoid ~= nil and humanoid.Health > 0 and player:GetAttribute("WeaponId") ~= nil
        and player:GetAttribute("IsCultivating") ~= true and player:GetAttribute("CarryingEgg") == nil
end

local function setDrawn(player, drawn)
    drawn = drawn and canDraw(player)
    if (player:GetAttribute("WeaponDrawn") == true) ~= drawn then
        player:SetAttribute("WeaponDrawn", drawn)
    end
end

-- At most one change every DRAW_GAP seconds: a cheat flipping it as fast as it can sent every client's weapon effects a flood
-- (release audit, 2026-11-12). Requests in between aren't dropped: the last one is applied when the gap is up.
local DRAW_GAP = 0.2
local lastDraw, pendingDraw = {}, {}

RemoteEvents.WeaponDrawEvent.OnServerEvent:Connect(function(player, wanted)
    if typeof(wanted) ~= "boolean" then
        return
    end
    local wait = DRAW_GAP - (os.clock() - (lastDraw[player] or 0))
    if wait <= 0 then
        lastDraw[player] = os.clock()
        setDrawn(player, wanted)
        return
    end
    local scheduled = pendingDraw[player] ~= nil
    pendingDraw[player] = wanted
    if not scheduled then
        task.delay(wait, function()
            local latest = pendingDraw[player]
            pendingDraw[player] = nil
            if latest ~= nil and player.Parent then
                lastDraw[player] = os.clock()
                setDrawn(player, latest)
            end
        end)
    end
end)

local function watch(player)
    player:SetAttribute("WeaponDrawn", false)
    local function sheatheIf(condition)
        return function()
            if condition() then
                setDrawn(player, false)
            end
        end
    end
    player:GetAttributeChangedSignal("IsCultivating"):Connect(sheatheIf(function()
        return player:GetAttribute("IsCultivating") == true
    end))
    player:GetAttributeChangedSignal("CarryingEgg"):Connect(sheatheIf(function()
        return player:GetAttribute("CarryingEgg") ~= nil
    end))
    player:GetAttributeChangedSignal("WeaponId"):Connect(sheatheIf(function()
        return true
    end))
    player.CharacterAdded:Connect(function()
        setDrawn(player, false)
    end)
end
Players.PlayerAdded:Connect(watch)
for _, player in Players:GetPlayers() do
    watch(player)
end

-- the nearest target in front within reach, and where the strike meets it
local function findTarget(rootPart, spec)
    local facing = rootPart.CFrame.LookVector * Vector3.new(1, 0, 1)
    facing = if facing.Magnitude > 0 then facing.Unit else Vector3.new(0, 0, -1)
    local cosArc = math.cos(math.rad(spec.Arc))
    local best, bestDistance, bestPoint = nil, math.huge, nil
    for _, target in CollectionService:GetTagged(GameConfig.Combat.TargetTag) do
        local body = target:IsA("Model") and target.PrimaryPart
        if body and target:IsDescendantOf(workspace) and target:GetAttribute("Invulnerable") ~= true then
            local radius = target:GetAttribute("HitRadius") or 2
            local offset = body.Position - rootPart.Position
            local flat = offset * Vector3.new(1, 0, 1)
            local distance = math.max(0, flat.Magnitude - radius)
            local inFront = flat.Magnitude <= radius or (flat.Unit:Dot(facing) >= cosArc)
            local vertical = math.abs(offset.Y) <= radius + 4
            if distance <= spec.Range and inFront and vertical and distance < bestDistance then
                best, bestDistance = target, distance
                -- on its near side, at the height of the striker's chest (where the weapon is), never at the height of its
                -- own centre: a big guardian's is at its base, and the blow showed at the striker's feet
                local near = body.Position - (if flat.Magnitude > 0 then flat.Unit else facing) * math.min(radius, flat.Magnitude) * 0.9
                bestPoint = Vector3.new(near.X, rootPart.Position.Y + 0.5, near.Z)
            end
        end
    end
    return best, bestPoint
end

-- ---------- choosing a form ----------
RemoteEvents.FormEvent.OnServerEvent:Connect(function(player, id)
    local family = FormRules.familyOf(id) -- (nil for anything that isn't a form's id, a table or a number included)
    if not family or not FormRules.unlocked(id, Shop.playerRealmIndex(player)) then
        return
    end
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    if not humanoid or humanoid.Health <= 0 or player:GetAttribute("IsCultivating") == true or player:GetAttribute("CarryingEgg") ~= nil then
        return
    end
    local now = os.clock()
    if now - (lastFormChange[player] or 0) < FormRules.SWITCH_GAP then
        return
    end
    lastFormChange[player] = now
    player:SetAttribute("Form" .. family, id)
    PlayerData.saveSoon(player) -- (the choice is saved with the player: PlayerData "Forms", read from these attributes)
end)

-- The saved choice is put back as soon as the player's data is in (the attribute stays unset until then: the family's first form is fought with). A choice
-- made meanwhile is theirs and is kept. It is the saved id of a form of that very family (FormRules.sanitizeChoices); unlocking is checked where it is used.
local function restoreForms(player)
    local progress = PlayerData.waitForData(player)
    if not progress or player.Parent ~= Players then
        return
    end
    for family, id in FormRules.sanitizeChoices(progress.Forms) do
        if player:GetAttribute("Form" .. family) == nil then
            player:SetAttribute("Form" .. family, id)
        end
    end
end
Players.PlayerAdded:Connect(function(player)
    task.spawn(restoreForms, player)
end)
for _, player in Players:GetPlayers() do
    task.spawn(restoreForms, player)
end

RemoteEvents.CombatEvent.OnServerEvent:Connect(function(player)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    if not (humanoid and rootPart) or humanoid.Health <= 0 or player:GetAttribute("IsCultivating") == true
        or player:GetAttribute("CarryingEgg") ~= nil then -- both hands are round the egg
        return
    end
    local weapon = Combat.strikeOf(player) -- the weapon's own numbers
    if weapon.Kind ~= "Palm" then
        setDrawn(player, true) -- striking with a weapon draws it
    end
    local now = os.clock()
    local due = nextStrike[player]
    if due and now < due - weapon.Cooldown * COOLDOWN_SLACK then
        return
    end
    -- the strike: its family's form the player chose (and has unlocked), the step of its chain, the numbers of that step (FormRules.plan)
    local strike = FormRules.plan(weapon.Kind, player:GetAttribute("Form" .. weapon.Kind), Shop.playerRealmIndex(player),
        { Damage = weapon.Damage, Range = weapon.Range, Arc = weapon.Arc, Cooldown = weapon.Cooldown }, lastStrike[player], now)
    if not strike then
        return
    end
    nextStrike[player] = math.max(now, due or 0) + strike.Cooldown
    lastStrike[player] = { Form = strike.Form, Step = strike.Step, At = now }
    -- from sword flight a strike swings but can't land: guardians can't reach a flyer, so a flyer
    -- can't reach them
    local target, point = nil, nil
    if player:GetAttribute("IsFlying") ~= true and not MovementGuard.isSuspect(player) then
        target, point = findTarget(rootPart, strike)
    end
    local damage, critical = nil, nil
    local counter = comboCount[player]
    if target then
        local crit = GameConfig.Combat.Crit
        critical = roll:NextNumber() < crit.Chance
        damage = strike.Damage * Combat.powerOf(player) * (if critical then crit.Multiplier else 1)
        counter = FormRules.countHit(counter, now)
        comboCount[player] = counter
        Combat.Hit:Fire(player, target, damage, point)
    end
    -- the counter as it stands: a miss leaves it, and it lapses after the window
    local hits = if counter and now - counter.At <= FormRules.Counter.WINDOW then counter.Hits else 0
    if hits > 1 then
        GoalBook.count(player, "Combo", hits) -- (a daily or weekly goal: the best combo; the goal's own mode keeps the best)
    end
    RemoteEvents.CombatEvent:FireAllClients(player, weapon.Kind, point, strike.Step, if damage then math.round(damage) else nil, critical or nil, target,
        strike.Form, hits)
end)

Players.PlayerRemoving:Connect(function(player)
    lastDraw[player], pendingDraw[player] = nil, nil
    lastStrike[player] = nil
    nextStrike[player] = nil
    comboCount[player] = nil
    lastFormChange[player] = nil
end)
