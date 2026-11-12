local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local AuraConfig = require(ReplicatedStorage:WaitForChild("AuraConfig"))
local RealmAura = require(script.Parent:WaitForChild("RealmAura"))
local AuraStyles = require(script.Parent:WaitForChild("AuraStyles"))
local BreakthroughEffect = require(script.Parent:WaitForChild("BreakthroughEffect"))
local Quality = require(script.Parent.Parent:WaitForChild("Quality"))

-- another player's breakthrough plays only within this many studs of the camera (release audit, 2026-11-12: each is up to 40
-- beams, 10 trails and a light, and every rank-up anywhere on the map played)
local BREAKTHROUGH_REACH = if Quality.Low then 120 else 250
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local PRINT_BUILD_SUMMARY = RunService:IsStudio()

-- breakthrough effects are built in here (the pet aura layer that also lived here was removed,
-- 2026-11-11: no pet had a design of its own, so it never ran)
local container = Instance.new("Folder")
container.Name = "CultivationAuras"
container.Parent = workspace

local connections = {}
local activeBreakthroughs = {}

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
    if current and current.fx.Parent and current.root == rootPart and current.realm == realm and current.sub == rank.Level then
        return
    end
    removeRealmAura(player)
    local fx = RealmAura.build(rootPart, realm, rank.Level, { isLocal = player == Players.LocalPlayer })
    if fx then
        realmAuras[player] = { fx = fx, root = rootPart, realm = realm, sub = rank.Level }
    end
end

local function stopBreakthrough(player)
    local effect = activeBreakthroughs[player]
    if effect then
        activeBreakthroughs[player] = nil
        BreakthroughEffect.stop(effect)
    end
end

local function printBreakthroughSummary(player, effect, rankId)
    print(string.format("[Breakthrough] %s: %s", player.Name, tostring(rankId)))

    task.delay(1.2, function()
        if effect.stopped then
            return
        end
        local used = {}
        for _, descendant in effect.folder:GetDescendants() do
            used[descendant.ClassName] = (used[descendant.ClassName] or 0) + 1
        end
        local totals = {
            Beams = used.Beam or 0,
            ParticleEmitters = used.ParticleEmitter or 0,
            Trails = used.Trail or 0,
            Lights = used.PointLight or 0,
            SurfaceGuis = used.SurfaceGui or 0,
        }
        for name, limit in AuraStyles.BreakthroughBudget do
            if totals[name] > limit then
                warn(string.format("[Breakthrough] %s uses %d %s, over the budget of %d", rankId, totals[name], name, limit))
            end
        end
    end)
end

local function playBreakthrough(player)
    local character = player.Character
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    if not rootPart or not isAlive(character) then
        return
    end
    if player ~= Players.LocalPlayer then
        local camera = workspace.CurrentCamera
        if hiddenByReducedEffects(player)
            or (camera and (camera.CFrame.Position - rootPart.Position).Magnitude > BREAKTHROUGH_REACH) then
            return
        end
    end

    stopBreakthrough(player)
    local rankId = getRankId(player)
    local effect
    effect = BreakthroughEffect.play(container, character, rootPart, rankId, function()
        if activeBreakthroughs[player] == effect then
            activeBreakthroughs[player] = nil
        end
    end)
    activeBreakthroughs[player] = effect
    Sfx.play("Breakthrough", rootPart)

    if PRINT_BUILD_SUMMARY then
        printBreakthroughSummary(player, effect, rankId)
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
        table.insert(playerConnections, rankValue.Changed:Connect(function()
            local newRankIndex = Ranks.getIndex(rankValue.Value)
            local rose = newRankIndex ~= nil and lastRankIndex ~= nil and newRankIndex > lastRankIndex
            lastRankIndex = newRankIndex or lastRankIndex

            refresh()
            if rose then
                playBreakthrough(player)
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
