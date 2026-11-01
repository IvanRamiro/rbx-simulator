local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local CharacterAura = require(script.Parent:WaitForChild("CharacterAura"))
local AuraStyles = require(script.Parent:WaitForChild("AuraStyles"))
local BreakthroughEffect = require(script.Parent:WaitForChild("BreakthroughEffect"))

local PRINT_BUILD_SUMMARY = RunService:IsStudio()

local container = Instance.new("Folder")
container.Name = "CultivationAuras"
container.Parent = workspace

local activeAuras = {}
local liveAuras = {}
local connections = {}
local activeBreakthroughs = {}

local updateConnection = nil
local refreshAura

local function destroyAura(aura)
    if aura.destroyed then
        return
    end

    liveAuras[aura] = nil
    if activeAuras[aura.player] == aura then
        activeAuras[aura.player] = nil
    end
    CharacterAura.destroy(aura)

    if next(liveAuras) == nil and updateConnection then
        updateConnection:Disconnect()
        updateConnection = nil
    end
end

local function removeAura(aura)
    if activeAuras[aura.player] == aura then
        activeAuras[aura.player] = nil
    end

    if not aura.rootPart:IsDescendantOf(workspace) then
        destroyAura(aura)
        return
    end

    CharacterAura.hide(aura)
    task.delay(CharacterAura.REMOVE_DELAY, destroyAura, aura)
end

local function updateAuras()
    local now = os.clock()
    local parts, cframes = {}, {}

    for aura in liveAuras do
        if aura.rootPart:IsDescendantOf(workspace) and aura.model.Parent then
            CharacterAura.update(aura, now, parts, cframes)
        elseif activeAuras[aura.player] == aura then
            destroyAura(aura)
            task.defer(refreshAura, aura.player)
        else
            destroyAura(aura)
        end
    end

    if #parts > 0 then
        workspace:BulkMoveTo(parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)
    end
end

local function printSummary(aura, petId, rankId)
    local counts = {}
    for _, descendant in aura.model:GetDescendants() do
        counts[descendant.ClassName] = (counts[descendant.ClassName] or 0) + 1
    end
    print(string.format(
        "[Aura] %s: %s / %s - %d moving parts, %d trails, %d particle emitters, %d lights",
        aura.player.Name,
        petId or "Neutral",
        tostring(rankId),
        (counts.Part or 0) + (counts.MeshPart or 0),
        counts.Trail or 0,
        counts.ParticleEmitter or 0,
        counts.PointLight or 0
    ))
end

local function isAlive(character)
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    return humanoid ~= nil and humanoid.Health > 0
end

local function getRankId(player)
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    return rank and rank.Id
end

local function getAuraPetId(player)
    local petId = player:GetAttribute("AuraPetId")
    return if typeof(petId) == "string" then petId else nil
end

function refreshAura(player)
    local character = player.Character
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    local rankId = getRankId(player)
    local petId = getAuraPetId(player)
    local shouldShow = player:GetAttribute("IsCultivating") == true
        and rootPart ~= nil
        and rankId ~= nil
        and isAlive(character)

    local rank = rankId and Ranks.getRankById(rankId)
    local lookKey = tostring(rank and rank.AuraTier) .. "/" .. tostring(petId)
    local current = activeAuras[player]
    if current and shouldShow and current.rootPart == rootPart and current.lookKey == lookKey then
        return
    end

    if current then
        removeAura(current)
    end

    local aura = shouldShow and CharacterAura.build(player, character, rootPart, petId, rankId)
    if aura then
        aura.lookKey = lookKey
        aura.model.Parent = container
        activeAuras[player] = aura
        liveAuras[aura] = true
        CharacterAura.show(aura)

        if not updateConnection then
            updateConnection = RunService.RenderStepped:Connect(updateAuras)
        end

        if PRINT_BUILD_SUMMARY then
            printSummary(aura, petId, rankId)
        end
    end
end

local function stopBreakthrough(player)
    local effect = activeBreakthroughs[player]
    if effect then
        activeBreakthroughs[player] = nil
        BreakthroughEffect.stop(effect)
    end
end

local function printBreakthroughSummary(player, effect, petId, rankId)
    print(string.format("[Breakthrough] %s: %s / %s", player.Name, petId or "Neutral", rankId))

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

    stopBreakthrough(player)
    local petId, rankId = getAuraPetId(player), getRankId(player)
    local effect
    effect = BreakthroughEffect.play(container, character, rootPart, petId, rankId, function()
        if activeBreakthroughs[player] == effect then
            activeBreakthroughs[player] = nil
        end
    end)
    activeBreakthroughs[player] = effect

    local aura = activeAuras[player]
    if aura then
        CharacterAura.pulse(aura)
    end

    if PRINT_BUILD_SUMMARY then
        printBreakthroughSummary(player, effect, petId, rankId)
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
            local aura = activeAuras[player]
            if aura and aura.character == character then
                destroyAura(aura)
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
    table.insert(playerConnections, player:GetAttributeChangedSignal("AuraPetId"):Connect(refresh))
    table.insert(playerConnections, player.CharacterAdded:Connect(function(character)
        watchCharacter(player, character)
    end))

    if player.Character then
        watchCharacter(player, player.Character)
    end

    task.spawn(function()
        local rankValue = player:WaitForChild("leaderstats"):WaitForChild("Rank")
        if connections[player] ~= playerConnections then
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

    for aura in liveAuras do
        if aura.player == player then
            destroyAura(aura)
        end
    end
    stopBreakthrough(player)
end

Players.PlayerAdded:Connect(watchPlayer)
Players.PlayerRemoving:Connect(unwatchPlayer)

for _, player in Players:GetPlayers() do
    watchPlayer(player)
end
