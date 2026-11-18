-- Every player's realm aura (RealmAura) while they meditate, and the breakthrough when anyone ranks up near the camera: the
-- player's own is the whole sequence (BreakthroughShow: camera, screen, sound, title card, with BreakthroughFx drawing the world),
-- anyone else's the world part only, shorter and lighter (BreakthroughFx). Reduced Effects and the phone tier (Quality) thin other
-- players' effects.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local AuraConfig = require(ReplicatedStorage:WaitForChild("AuraConfig"))
local RealmAura = require(script.Parent:WaitForChild("RealmAura"))
local BreakthroughFx = require(script.Parent:WaitForChild("BreakthroughFx"))
local BreakthroughShow = require(script.Parent:WaitForChild("BreakthroughShow"))
local BreakthroughStyles = require(script.Parent:WaitForChild("BreakthroughStyles"))
local Quality = require(script.Parent.Parent:WaitForChild("Quality"))

-- another player's breakthrough plays only within this many studs of the camera (release audit, 2026-11-12: every rank-up anywhere
-- on the map played)
local BREAKTHROUGH_REACH = if Quality.Low then 120 else 250
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local PRINT_BUILD_SUMMARY = RunService:IsStudio()
local MAX_SWELL_RATE = if Quality.Low then 30 else 60 -- the most an emitter of the old aura is thickened to (the phone cap)

-- breakthrough effects are built in here (the pet aura layer that also lived here was removed,
-- 2026-11-11: no pet had a design of its own, so it never ran)
local container = Instance.new("Folder")
container.Name = "CultivationAuras"
container.Parent = workspace

local connections = {}
local activeBreakthroughs = {} -- [player] = { fx = BreakthroughFx's effect, show = the player's own BreakthroughShow, info }
local heldAura = {}             -- [player] = true from a breakthrough's start to its break: the old aura stays, the new one waits
local pendingOwn = nil          -- the local player's next breakthrough, when it came while one was playing: { rankId, from }
local showcases = {}            -- [player] = the new realm's aura worn for the reveal by one who is not meditating

local function isAlive(character)
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    return humanoid ~= nil and humanoid.Health > 0
end

local function getRankId(player)
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    return rank and rank.Id
end

-- every player's realm aura (RealmAura), only while they meditate (the owner, 2026-11-04: "there
-- should be no aura if the player is not meditating"): built round the character for their realm and
-- sub-rank, rebuilt when either changes, removed when they stop or die
local realmAuras = {} -- [player] = { fx = the aura's folder, key = what it was built for }

local function getRealm(rank)
    for index, tier in AuraConfig.Tiers do
        if tier.Name == rank.Realm then
            return index
        end
    end
    return nil
end

local function removeRealmAura(player)
    local current = realmAuras[player]
    if current then
        realmAuras[player] = nil
        -- at once: a rebuild in the same frame dresses the same body parts
        RealmAura.destroy(current.fx)
    end
end

-- the Reduced Effects setting hides other players' auras on this client
local function hiddenByReducedEffects(player)
    return player ~= Players.LocalPlayer and Players.LocalPlayer:GetAttribute("SettingReducedEffects") == true
end

local function refreshAura(player)
    local character = player.Character
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    local realm = rank and getRealm(rank)
    if not (rootPart and realm and isAlive(character)) or hiddenByReducedEffects(player)
        or player:GetAttribute("IsCultivating") ~= true then
        removeRealmAura(player)
        return
    end

    local current = realmAuras[player]
    if heldAura[player] and current and current.fx.Parent then
        return -- a breakthrough is gathering: the old aura stays until the break shows the new one
    end
    if current and current.fx.Parent and current.root == rootPart and current.realm == realm and current.sub == rank.Level then
        return
    end
    removeRealmAura(player)
    if heldAura[player] then
        return
    end
    local fx = RealmAura.build(rootPart, realm, rank.Level, { isLocal = player == Players.LocalPlayer })
    if fx then
        realmAuras[player] = { fx = fx, root = rootPart, realm = realm, sub = rank.Level }
    end
end

-- ---------- breakthroughs ----------
-- The new realm's aura, worn for the reveal by a cultivator who is standing (the aura is only for meditating, and a new realm ends
-- meditation): it blooms in at the break, stands through the title card, and fades out as the sequence settles.
local function retireShowcase(player)
    local fx = showcases[player]
    if not fx then
        return
    end
    showcases[player] = nil
    for _, item in fx:GetDescendants() do
        if item:IsA("ParticleEmitter") or item:IsA("Trail") then
            item.Enabled = false
        elseif item:IsA("Beam") then
            TweenService:Create(item, TweenInfo.new(0.9), { Width0 = 0, Width1 = 0 }):Play()
        elseif item:IsA("Light") then
            TweenService:Create(item, TweenInfo.new(0.9), { Brightness = 0 }):Play()
        elseif item:IsA("Highlight") then
            TweenService:Create(item, TweenInfo.new(0.9), { FillTransparency = 1, OutlineTransparency = 1 }):Play()
        end
    end
    task.delay(1.2, function()
        if fx.Parent then
            RealmAura.destroy(fx)
        end
    end)
end

local function showcaseAura(player)
    local character = player.Character
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    local realm = rank and getRealm(rank)
    if not (rootPart and realm) or realmAuras[player] or showcases[player] then
        return
    end
    showcases[player] = RealmAura.build(rootPart, realm, rank.Level, { isLocal = player == Players.LocalPlayer })
end

local function endBreakthrough(player, record)
    if activeBreakthroughs[player] == record then
        activeBreakthroughs[player] = nil
    end
    heldAura[player] = nil
    retireShowcase(player)
    refreshAura(player)
end

local function stopBreakthrough(player)
    local record = activeBreakthroughs[player]
    if record then
        activeBreakthroughs[player] = nil
        if record.show then
            BreakthroughShow.stop(record.show)
        elseif record.fx then
            BreakthroughFx.stop(record.fx)
        end
    end
    if player == Players.LocalPlayer then
        pendingOwn = nil
    end
    heldAura[player] = nil
    local fx = showcases[player]
    if fx then
        showcases[player] = nil
        RealmAura.destroy(fx)
    end
end

-- the old aura grows through the gather (its emitters thicken), until the break replaces it
local swelling = {} -- [player] = { record = , rates = { [emitter] = its rate when the gather began } }
RunService.Heartbeat:Connect(function()
    for player, swell in swelling do
        local record, current = activeBreakthroughs[player], realmAuras[player]
        local fx = record and (record.show and record.show.fx or record.fx)
        if not (fx and current and current.fx.Parent) or fx.broke then
            swelling[player] = nil
            continue
        end
        local B, H = fx.B, fx.H
        local charge = math.clamp((fx.t - 0.12 * B) / (B - H - 0.12 * B), 0, 1)
        local factor = 1 + 1.6 * charge * charge
        for emitter, rate in swell.rates do
            if emitter.Parent then
                emitter.Rate = math.min(rate * factor, MAX_SWELL_RATE)
            end
        end
    end
end)

local function beginSwelling(player)
    local current = realmAuras[player]
    if not (current and current.fx.Parent) then
        return
    end
    local rates = {}
    for _, item in current.fx:GetDescendants() do
        if item:IsA("ParticleEmitter") and item.Rate > 0 then
            rates[item] = item.Rate
        end
    end
    swelling[player] = { rates = rates }
end

-- in Studio only (PRINT_BUILD_SUMMARY): warns when a breakthrough's effect goes over its budget (BreakthroughStyles.Budget)
local function checkBreakthroughBudget(record, rankId, own)
    task.delay(if own then 4 else 1.4, function()
        local fx = record.show and record.show.fx or record.fx
        if not fx or fx.finished then
            return
        end
        local used = {}
        for _, descendant in fx.folder:GetDescendants() do
            used[descendant.ClassName] = (used[descendant.ClassName] or 0) + 1
        end
        local totals = {
            Beams = used.Beam or 0, ParticleEmitters = used.ParticleEmitter or 0, Trails = used.Trail or 0,
            Lights = used.PointLight or 0, Billboards = used.BillboardGui or 0, Parts = used.Part or 0,
        }
        local budget = if own then BreakthroughStyles.Budget.Own else BreakthroughStyles.Budget.Near
        for name, limit in budget do
            if totals[name] > limit then
                warn(string.format("[Breakthrough] %s uses %d %s, over the budget of %d", rankId, totals[name], name, limit))
            end
        end
        print(string.format("[Breakthrough] %s %s: %d emitters, %d beams, %d trails, %d parts, %d billboards", rankId,
            if own then "own" else "near", totals.ParticleEmitters, totals.Beams, totals.Trails, totals.Parts, totals.Billboards))
    end)
end

local SOUND = { Step = "BreakthroughStep", Milestone = "BreakthroughMilestone", Realm = "BreakthroughRealm", Apex = "BreakthroughRealm" }

local function playBreakthrough(player, fromName)
    local character = player.Character
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    if not rootPart or not isAlive(character) then
        return
    end
    local rankId = getRankId(player)
    local info = rankId and BreakthroughStyles.describe(rankId, fromName)
    if not info then
        return
    end
    local own = player == Players.LocalPlayer
    if not own then
        local camera = workspace.CurrentCamera
        if hiddenByReducedEffects(player)
            or (camera and (camera.CFrame.Position - rootPart.Position).Magnitude > BREAKTHROUGH_REACH) then
            return
        end
    end

    -- a second breakthrough while one is playing: the first jumps to its settle, then the next plays (for others, it is cut)
    local running = activeBreakthroughs[player]
    if running then
        if own and running.show then
            pendingOwn = { rankId = rankId, from = if pendingOwn then pendingOwn.from else fromName }
            BreakthroughShow.skip(running.show)
            return
        end
        stopBreakthrough(player)
    end

    local reduced = Players.LocalPlayer:GetAttribute("SettingReducedEffects") == true
    local record = { info = info }
    activeBreakthroughs[player] = record
    heldAura[player] = true
    local grade = info.Grade
    local function onBreak()
        heldAura[player] = nil
        swelling[player] = nil
        refreshAura(player)
        if own and grade.Name ~= "Step" and player:GetAttribute("IsCultivating") ~= true then
            showcaseAura(player)
        end
    end

    -- the player's own stands aside for the hatch cinematic (its camera and screen are taken): the world part only
    local theirOwnShow = own and player:GetAttribute("InHatchCinematic") ~= true
    if theirOwnShow then
        record.show = BreakthroughShow.play({
            Player = player, Character = character, Root = rootPart, Info = info, Container = container, Calm = reduced, Low = Quality.Low,
            OnBreak = onBreak,
            OnSettle = function()
                retireShowcase(player)
            end,
            OnDone = function(instant)
                endBreakthrough(player, record)
                if own and pendingOwn and not instant then
                    local pending = pendingOwn
                    pendingOwn = nil
                    task.defer(function()
                        -- (the latest rank, with the first one's "from": the card says what the run of them gained)
                        playBreakthrough(player, pending.from)
                    end)
                end
            end,
        })
        Sfx.hold(grade.Own.End)
    else
        record.fx = BreakthroughFx.start({
            Parent = container, Character = character, Root = rootPart, Info = info, Own = false, Calm = reduced, Low = Quality.Low,
            OnBreak = onBreak,
            OnDone = function()
                endBreakthrough(player, record)
            end,
        })
        -- its sound grows with the kind of breakthrough, like the effect; the breaker's own music steps back under it
        Sfx.after(math.max(0, grade.Near.Break - 0.05), SOUND[grade.Name], rootPart)
    end
    beginSwelling(player)
    if PRINT_BUILD_SUMMARY then
        checkBreakthroughBudget(record, rankId, theirOwnShow)
    end
end

local characterConnections = {}

local function disconnectCharacter(player)
    for _, connection in characterConnections[player] or {} do
        connection:Disconnect()
    end
    characterConnections[player] = nil
end

local function watchCharacter(player, character)
    stopBreakthrough(player)
    disconnectCharacter(player) -- the previous character may not be destroyed on respawn
    local watching = {}
    characterConnections[player] = watching

    table.insert(watching, character.ChildAdded:Connect(function(child)
        if child.Name == "HumanoidRootPart" then
            refreshAura(player)
        end
    end))

    task.spawn(function()
        local humanoid = character:WaitForChild("Humanoid", 10)
        if not humanoid or characterConnections[player] ~= watching then
            return
        end

        table.insert(watching, humanoid.Died:Connect(function()
            local realmAura = realmAuras[player]
            if realmAura and realmAura.root.Parent == character then
                removeRealmAura(player)
            end
            stopBreakthrough(player)
        end))
    end)

    refreshAura(player)
end

local function watchPlayer(player)
    local playerConnections = {}
    connections[player] = playerConnections

    local function refresh()
        refreshAura(player)
    end

    table.insert(playerConnections, player:GetAttributeChangedSignal("IsCultivating"):Connect(refresh))
    table.insert(playerConnections, player.CharacterAdded:Connect(function(character)
        watchCharacter(player, character)
    end))

    if player.Character then
        watchCharacter(player, player.Character)
    end

    task.spawn(function()
        local leaderstats = player:WaitForChild("leaderstats", 60)
        local rankValue = leaderstats and leaderstats:WaitForChild("Rank", 60)
        if not rankValue or connections[player] ~= playerConnections then
            return
        end

        local lastRankIndex = Ranks.getIndex(rankValue.Value)
        local lastRankName = rankValue.Value
        table.insert(playerConnections, rankValue.Changed:Connect(function()
            local newRankIndex = Ranks.getIndex(rankValue.Value)
            local rose = newRankIndex ~= nil and lastRankIndex ~= nil and newRankIndex > lastRankIndex
            local fromName = lastRankName
            lastRankIndex = newRankIndex or lastRankIndex
            lastRankName = rankValue.Value

            if rose then
                -- the old aura stays through the gather: the new one is shown at the break (playBreakthrough holds it)
                heldAura[player] = true
            end
            refresh()
            if rose then
                heldAura[player] = nil
                playBreakthrough(player, fromName)
                if not activeBreakthroughs[player] then
                    refresh() -- (nothing played: out of reach, or no body to show it on)
                end
            end
        end))
        refresh()
    end)
end

local function unwatchPlayer(player)
    local playerConnections = connections[player]
    if playerConnections then
        for _, connection in playerConnections do
            connection:Disconnect()
        end
        connections[player] = nil
    end
    disconnectCharacter(player)
    removeRealmAura(player)
    stopBreakthrough(player)
end

Players.PlayerAdded:Connect(watchPlayer)
Players.PlayerRemoving:Connect(unwatchPlayer)

for _, player in Players:GetPlayers() do
    watchPlayer(player)
end

Players.LocalPlayer:GetAttributeChangedSignal("SettingReducedEffects"):Connect(function()
    for _, player in Players:GetPlayers() do
        refreshAura(player)
    end
end)
