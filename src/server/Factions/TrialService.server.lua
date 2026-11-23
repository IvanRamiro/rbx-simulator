-- The faction trials (the owner's brief, 2026-11-22: "a trial in the HQ ... passing it opens the vault and gives the weapon once"). The rules and numbers are
-- shared/TrialRules and GameConfig.Faction.<Id>.Trial; the world's places (Trial Stones, gates, tokens, dummies' places, vaults) are world/TrialBuilder's. This decides:
-- the client only draws the run (client/Factions/TrialController) and never reports a result.
--
-- A member of the faction, at the Immortal realm or higher, who has not passed yet, presses the prompt on their faction's Trial Stone (a part tagged FactionTrialPost).
-- Then ONE run exists for them (never two at once), with a server clock (FactionBook.setRunning, the "FactionTrial*" attributes the HUD reads):
--   Orthodox   Trial of Discipline: the player's position is tested every frame against five gate zones (tagged TrialGateZone, each with an Index). They must pass them
--              1 to 5 in order (flying is allowed: a zone is a tall box); passing a later one first sends the run back to gate 1. 90 seconds.
--   Unorthodox Trial of Three Tokens: six tokens (models tagged TrialToken, each with an Index and a prompt) are hidden round Windrift Hold; the server counts each the player
--              takes once, and any three pass. 300 seconds.
--   Demonic    Trial of Strength: the arena sends three waves of dummies (a model stored in ServerStorage.TrialDummy, stood on the arena's eight marked places, tagged
--              CombatTarget so the player's ordinary strikes land on them). Each dummy falls after its wave's number of LANDING blows (Combat.Hit), whatever the weapon, so the
--              trial tests doing it, not gear. A wave is cleared before the next stands up. One challenger in the arena at a time. 90 seconds.
-- A run ends when: the last thing is done (PASSED: FactionBook.markTrial writes it on the pledge for good, the player's state becomes "Passed" and the vault opens), the
-- clock runs out, the player dies or leaves, or (the arena) walks away from it (FAILED: nothing is lost, they may begin again after a few seconds).
--
-- FactionEvent (server -> client), besides FactionService's: "TrialStart" (faction id), "TrialNote" (plain words: a token taken, a wave up, a gate skipped),
-- "TrialResult" ("Passed" | "Failed", plain words).
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")
local TweenService = game:GetService("TweenService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local FactionRules = require(ReplicatedStorage:WaitForChild("FactionRules"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local TrialRules = require(ReplicatedStorage:WaitForChild("TrialRules"))

local serverRoot = script.Parent.Parent
local FactionBook = require(script.Parent:WaitForChild("FactionBook"))
local Combat = require(serverRoot:WaitForChild("Combat"):WaitForChild("Combat"))
local PromptRules = require(serverRoot:WaitForChild("World"):WaitForChild("PromptRules"))
local MovementGuard = require(serverRoot:WaitForChild("Security"):WaitForChild("MovementGuard"))
local WeaponInventory = require(serverRoot:WaitForChild("Shop"):WaitForChild("WeaponInventory"))

local Event = RemoteEvents.FactionEvent
local config = GameConfig.Faction

local WAVE_PAUSE = 1.4          -- seconds between a wave's last dummy falling and the next wave standing
local ARENA_LEAVE = 70          -- studs from the arena's centre past which a challenger has walked out of it
local RECORD_TRIES = 3          -- tries to write a pass on the pledge before telling the player
local FALL_TIME = 0.5           -- a fallen dummy's fade
local RISE_TIME = 0.35          -- a new dummy's fade-in

local runs = {}       -- [player] = the running trial: TrialRules' run, plus Dummies (a Dummies run)
local recording = {}  -- [player] = true while a pass is being written (no new run until it is)
local lastEnd = {}    -- [player] = os.clock() when their last run ended
local arenaUser = nil -- the player in the Demonic arena
local throttle = {}   -- [player] = os.clock() of their last prompt

local function now()
    return workspace:GetServerTimeNow()
end

local function tell(player, text)
    if player.Parent == Players then
        Event:FireClient(player, "Refused", text)
    end
end

local function note(player, text)
    if player.Parent == Players then
        Event:FireClient(player, "TrialNote", text)
    end
end

local function rootOf(player)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if humanoid and root and humanoid.Health > 0 then
        return root, humanoid
    end
    return nil
end

local function partOf(instance)
    if instance:IsA("BasePart") then
        return instance
    end
    return if instance:IsA("Model") then (instance.PrimaryPart or instance:FindFirstChildWhichIsA("BasePart", true)) else nil
end

-- ---------- what the world holds ----------
-- the tagged parts or models of a faction, by their "Index" attribute (a list in order)
local function indexed(tag, factionId)
    local list = {}
    for _, instance in CollectionService:GetTagged(tag) do
        local index = instance:GetAttribute("Index")
        if instance:GetAttribute("Faction") == factionId and typeof(index) == "number" and instance:IsDescendantOf(workspace) then
            list[index] = instance
        end
    end
    return list
end

local function arenaPlaces()
    local places = {}
    for _, spot in CollectionService:GetTagged("NightfallArenaDummy") do
        local index = tonumber(string.match(spot.Name, "^ArenaDummy(%d+)$"))
        if index and spot:IsA("BasePart") and spot:IsDescendantOf(workspace) then
            places[index] = spot
        end
    end
    return places
end

local function arenaCentre()
    for _, spot in CollectionService:GetTagged("NightfallArenaDummy") do
        local centre = spot.Parent and spot.Parent:FindFirstChild("ArenaCentre")
        if centre and centre:IsA("BasePart") then
            return centre.Position
        end
    end
    return nil
end

-- ---------- the dummies ----------
local function setFade(model, from, to, seconds)
    for _, part in model:GetDescendants() do
        if part:IsA("BasePart") and part:GetAttribute("KeepInvisible") ~= true then
            part.Transparency = from
            TweenService:Create(part, TweenInfo.new(seconds), { Transparency = to }):Play()
        end
    end
end

local function removeDummies(run)
    for _, dummy in run.Dummies or {} do
        if dummy.Parent then
            dummy:Destroy()
        end
    end
    run.Dummies = {}
end

local function spawnWave(player, run)
    local wave = TrialRules.wave(run)
    local template = ServerStorage:FindFirstChild("TrialDummy")
    if not wave or not template then
        return
    end
    local places, centre = arenaPlaces(), arenaCentre()
    run.Dummies = {}
    run.WaveBlows = wave.Blows
    for _, place in wave.Places do
        local spot = places[place]
        if spot then
            local dummy = template:Clone()
            local at = spot.Position
            dummy:PivotTo(if centre then CFrame.lookAt(at, Vector3.new(centre.X, at.Y, centre.Z)) else CFrame.new(at))
            dummy:SetAttribute("TrialOwner", player.UserId)
            dummy:SetAttribute("MaxHealth", wave.Blows)
            dummy:SetAttribute("Health", wave.Blows)
            dummy:SetAttribute("HitRadius", 3)
            CollectionService:AddTag(dummy, GameConfig.Combat.TargetTag)
            CollectionService:AddTag(dummy, FactionRules.DummyTag)
            dummy.Parent = workspace
            setFade(dummy, 1, 0, RISE_TIME)
            table.insert(run.Dummies, dummy)
        end
    end
end

-- ---------- the end of a run ----------
local function publishProgress(player, run)
    local taken
    if run.Kind == "Tokens" then
        local places = {}
        for index in run.Taken do
            table.insert(places, index)
        end
        table.sort(places)
        taken = table.concat(places, ",")
    end
    FactionBook.setProgress(player, run.Done, run.Total, TrialRules.text(run), taken)
end

local function clearRun(player)
    local run = runs[player]
    if not run then
        return nil
    end
    runs[player] = nil
    FactionBook.setRunning(player, nil)
    if run.Kind == "Dummies" then
        removeDummies(run)
        if arenaUser == player then
            arenaUser = nil
        end
    end
    lastEnd[player] = os.clock()
    return run
end

local function writePass(player)
    for try = 1, RECORD_TRIES do
        if player.Parent ~= Players then
            return false
        end
        if FactionBook.markTrial(player) then
            return true
        end
        task.wait(2 * try)
    end
    return false
end

-- passed: true | false; reason: plain words for a failure
local function finish(player, passed, reason)
    local run = clearRun(player)
    if not run or player.Parent ~= Players then
        return
    end
    FactionBook.setProgress(player, nil, nil, nil, nil)
    if not passed then
        FactionBook.setTrial(player, "Open", nil)
        Event:FireClient(player, "TrialResult", "Failed", reason or "The trial is over.")
        return
    end
    recording[player] = true
    FactionBook.setPassing(player, true)
    FactionBook.setTrial(player, "Passed", nil) -- (at once: the banner must not stay on "Running", nor the faction window say "begin" while the pass is written)
    task.spawn(function()
        local ok = writePass(player)
        recording[player] = nil
        FactionBook.setPassing(player, nil)
        if player.Parent ~= Players then
            return
        end
        if ok then
            FactionBook.setTrial(player, "Passed", nil)
            local info = FactionRules.get(run.Faction)
            Event:FireClient(player, "TrialResult", "Passed", "You passed the " .. info.Trial.Name .. ". Go to " .. info.Hq .. "'s vault and take the " .. info.Weapon.Name .. ".")
        else
            FactionBook.setTrial(player, "Open", nil)
            Event:FireClient(player, "TrialResult", "Failed", "You passed, but it couldn't be written down just now. Please try the trial again in a moment.")
        end
    end)
end

-- ---------- beginning a trial ----------
local function begin(player, post)
    local factionId = post:GetAttribute("Faction")
    if not FactionRules.isFaction(factionId) or runs[player] then
        return
    end
    if recording[player] then
        tell(player, "Your pass is being written down. One moment.")
        return
    end
    local info = FactionRules.get(factionId)
    if not FactionBook.ready(player) then
        tell(player, "Your faction record is still loading. Try again in a moment.")
        return
    end
    local own = FactionBook.factionOf(player)
    if own ~= factionId then
        tell(player, if own then "This is the " .. info.Trial.Name .. ", the " .. info.DisplayName .. "'s. You belong to the " .. FactionRules.get(own).DisplayName .. "."
            else "Only a member of the " .. info.DisplayName .. " may take its trial. Join it at the plaza first.")
        return
    end
    if not FactionRules.canTrial(Ranks.getPlayerRankName(player)) then
        tell(player, "Reach the " .. config.TrialRealm .. " to take " .. info.Master .. "'s trial.")
        return
    end
    local pledge = FactionBook.record(player)
    if WeaponInventory.owns(player, info.Weapon.Id) then
        tell(player, "You already hold the " .. info.Weapon.Name .. ". Your trial is done.")
        return
    end
    if pledge and pledge.Trial then
        tell(player, "You have passed the trial. Go to the vault and take the " .. info.Weapon.Name .. ".")
        return
    end
    if os.clock() - (lastEnd[player] or -100) < config.TrialCooldown then
        tell(player, "Catch your breath. You can begin again in a moment.")
        return
    end
    if not rootOf(player) then
        return
    end
    local trial = info.Trial
    if trial.Kind == "Dummies" then
        if arenaUser and arenaUser ~= player and runs[arenaUser] then
            tell(player, "Another challenger is in the arena. Wait for them to finish.")
            return
        end
        if not ServerStorage:FindFirstChild("TrialDummy") or next(arenaPlaces()) == nil then
            tell(player, "The arena is not ready yet.")
            return
        end
    elseif trial.Kind == "Gates" and next(indexed(FactionRules.GateTag, factionId)) == nil then
        tell(player, "The gates are not ready yet.")
        return
    elseif trial.Kind == "Tokens" and next(indexed(FactionRules.TokenTag, factionId)) == nil then
        tell(player, "The tokens are not hidden yet.")
        return
    end
    local run = TrialRules.new(factionId, now())
    runs[player] = run
    FactionBook.setRunning(player, run.Ends)
    FactionBook.setTrial(player, "Running", run.Ends)
    publishProgress(player, run)
    Event:FireClient(player, "TrialStart", factionId)
    if trial.Kind == "Dummies" then
        arenaUser = player
        run.Dummies = {}
        spawnWave(player, run)
    end
end

-- ---------- the prompts ----------
local function canPrompt(player)
    local at = os.clock()
    if at - (throttle[player] or 0) < 0.4 then
        return false
    end
    throttle[player] = at
    return true
end

local watched = {}
local function watchPost(post)
    local prompt = post:FindFirstChildWhichIsA("ProximityPrompt", true)
    if not prompt or watched[prompt] then
        return
    end
    watched[prompt] = true
    prompt.Triggered:Connect(function(player)
        local part = partOf(post)
        if part and canPrompt(player) and PromptRules.isAliveAndNear(player, part, PromptRules.maxDistance(prompt)) then
            begin(player, post)
        end
    end)
end

local function watchToken(token)
    local prompt = token:FindFirstChildWhichIsA("ProximityPrompt", true)
    if not prompt or watched[prompt] then
        return
    end
    watched[prompt] = true
    prompt.Triggered:Connect(function(player)
        local part = partOf(token)
        if not part or not canPrompt(player) or not PromptRules.isAliveAndNear(player, part, PromptRules.maxDistance(prompt)) then
            return
        end
        local factionId = token:GetAttribute("Faction")
        local run = runs[player]
        if not run or run.Kind ~= "Tokens" or run.Faction ~= factionId then
            tell(player, "A token of the Windrift trial. Begin the trial at the Trial Stone to gather them.")
            return
        end
        local outcome = TrialRules.token(run, token:GetAttribute("Index"))
        if outcome == "Taken" then
            publishProgress(player, run)
            if run.Passed then
                finish(player, true)
            else
                note(player, string.format("Token %d of %d. Keep looking.", run.Done, run.Total))
            end
        elseif outcome == "Again" then
            note(player, "You already took this one.")
        end
    end)
end

for _, post in CollectionService:GetTagged(FactionRules.PostTag) do
    watchPost(post)
end
CollectionService:GetInstanceAddedSignal(FactionRules.PostTag):Connect(watchPost)
for _, token in CollectionService:GetTagged(FactionRules.TokenTag) do
    watchToken(token)
end
CollectionService:GetInstanceAddedSignal(FactionRules.TokenTag):Connect(watchToken)

-- ---------- the dummies are struck ----------
Combat.Hit.Event:Connect(function(player, target)
    if typeof(target) ~= "Instance" or target:GetAttribute("TrialOwner") ~= player.UserId then
        return
    end
    local run = runs[player]
    if not run or run.Kind ~= "Dummies" or not table.find(run.Dummies, target) or target:GetAttribute("Down") then
        return
    end
    local left = (target:GetAttribute("Health") or 1) - 1
    target:SetAttribute("Health", math.max(0, left))
    if left > 0 then
        return
    end
    target:SetAttribute("Down", true)
    CollectionService:RemoveTag(target, GameConfig.Combat.TargetTag) -- (no more blows land on it)
    setFade(target, 0, 1, FALL_TIME)
    task.delay(FALL_TIME + 0.1, function()
        if target.Parent then
            target:Destroy()
        end
    end)
    local outcome = TrialRules.dummyDown(run)
    publishProgress(player, run)
    if outcome == "Cleared" then
        finish(player, true)
    elseif outcome == "Wave" then
        note(player, "Wave cleared. The next one is coming.")
        task.delay(WAVE_PAUSE, function()
            if runs[player] == run and not run.Passed then
                spawnWave(player, run)
            end
        end)
    end
end)

-- ---------- the clock, the gates, the arena ----------
local function insideZone(zone, position)
    local point = zone.CFrame:PointToObjectSpace(position)
    local half = zone.Size / 2
    return math.abs(point.X) <= half.X and math.abs(point.Y) <= half.Y and math.abs(point.Z) <= half.Z
end

RunService.Heartbeat:Connect(function()
    if next(runs) == nil then
        return
    end
    local clock = now()
    for player, run in runs do
        if player.Parent ~= Players then
            clearRun(player)
            continue
        end
        local root = rootOf(player)
        if not root then
            finish(player, false, "You fell. The trial is over.")
        elseif TrialRules.expired(run, clock) then
            finish(player, false, "Time is up. Begin again when you are ready.")
        elseif run.Kind == "Gates" and not MovementGuard.isSuspect(player) then
            -- the gates in order, and only the first that changes anything: two zones that meet at an edge can't both count in one frame
            local zones = indexed(FactionRules.GateTag, run.Faction)
            for index = 1, TrialRules.of(run.Faction).Count do
                local zone = zones[index]
                if zone and insideZone(zone, root.Position) then
                    local hadProgress = run.Done > 0
                    local outcome = TrialRules.gate(run, index)
                    if outcome == "Next" then
                        publishProgress(player, run)
                        if run.Passed then
                            finish(player, true)
                        end
                        break
                    elseif outcome == "Reset" then
                        -- (standing in a later gate's zone with nothing to lose: said once in a while, not every frame)
                        if hadProgress then
                            publishProgress(player, run)
                        end
                        if hadProgress or os.clock() - (run.WarnedAt or -10) > 4 then
                            run.WarnedAt = os.clock()
                            note(player, "You skipped a gate. Go back to gate 1 and pass them in order.")
                        end
                        break
                    end
                end
            end
        elseif run.Kind == "Dummies" then
            local centre = arenaCentre()
            if centre and (root.Position - centre).Magnitude > ARENA_LEAVE then
                finish(player, false, "You left the arena. The trial is over.")
            end
        end
    end
end)

-- ---------- the player's side ----------
Players.PlayerRemoving:Connect(function(player)
    clearRun(player)
    recording[player] = nil
    lastEnd[player] = nil
    throttle[player] = nil
end)
