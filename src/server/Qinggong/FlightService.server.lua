-- Sword flight (GameConfig.SwordFlight): the server decides who may fly and mounts the sword; the
-- client flies the character (it owns its physics) and spends the stamina.
--
-- Remote: FlightEvent (client -> server) true to take off, false to land. Take-off needs
-- SwordFlight.UnlockRank, a living character, no cultivation and no carried egg, at most once per
-- TOGGLE_COOLDOWN; it sets the "IsFlying" attribute. WorldService barriers still apply while flying.
--
-- The server keeps its own count of each rider's stamina, generous to them: a flight drains it at
-- the hover cost (the cheapest), the ground refill is the fastest, and dashes aren't counted, so it
-- never sits below an honest client's. It lands a flight once that count runs out, and refuses a
-- take-off it can't pay for, whatever the client says (before 2026-11-13 each flight got a full bar,
-- so landing and taking off again gave endless flight).
--
-- The sword (ServerStorage.Weapons.FlyingSword, stored by WorldBuild.OutfitBuilder.storeSword) is
-- welded under the rider's feet in Workspace.FlyingSwords, outside the character. Its glow parts
-- take the rider's realm colour.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))

local config = GameConfig.SwordFlight
local regen = GameConfig.Qinggong.Stamina
local TOGGLE_COOLDOWN = 0.5
local DURATION_MARGIN = 2 -- seconds of grace for latency
local TAKEOFF_SLACK = 10 -- stamina a take-off may be short by: the server hears of a landing late, so its refill starts late

local swordsFolder = workspace:FindFirstChild("FlyingSwords") or Instance.new("Folder")
swordsFolder.Name = "FlyingSwords"
swordsFolder.Parent = workspace

local flights = {}
local lastToggle = {}
local staminas = {} -- [player] = { stamina, at, flying, refillFrom }: made full at the first take-off and after each respawn

-- the server's count of a player's stamina, brought up to `now`
local function staminaAt(player, now)
    local maxStamina = player:GetAttribute("QinggongMaxStamina") or 0
    local state = staminas[player]
    if not state then
        state = { stamina = maxStamina, at = now, flying = false, refillFrom = now }
        staminas[player] = state
    end
    if state.flying then
        state.stamina -= config.HoverCost * (now - state.at)
    else
        state.stamina += regen.RegenGround * math.max(0, now - math.max(state.at, state.refillFrom))
    end
    state.stamina = math.min(state.stamina, maxStamina)
    state.at = now
    return state
end

local function glowFor(player)
    local rank = Ranks.getRank(Ranks.getPlayerRankName(player))
    return rank and config.RealmGlow[rank.Realm] or config.DefaultGlow
end

local function mountSword(player, character)
    local source = ServerStorage:FindFirstChild("Weapons") and ServerStorage.Weapons:FindFirstChild("FlyingSword")
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    local rootPart = character:FindFirstChild("HumanoidRootPart")
    if not (source and humanoid and rootPart) then
        return nil
    end
    -- the sword's origin is at the feet: below the root by the hip height plus half the root
    local feet = CFrame.new(0, -(humanoid.HipHeight + rootPart.Size.Y / 2) - source:GetAttribute("Top"), 0)
    local sword = Instance.new("Model")
    sword.Name = player.Name .. "_Sword"
    local glow = glowFor(player)
    for _, piece in source:GetChildren() do
        local part = piece:Clone()
        local offset = feet * piece:GetAttribute("Offset")
        part.Anchored = false
        part.CFrame = rootPart.CFrame * offset
        if piece:GetAttribute("Glow") then
            part.Color = glow
            part.Transparency = if part.Name == "Edge" then 0.3 else 0
        end
        local weld = Instance.new("Weld")
        weld.Part0, weld.Part1, weld.C0 = rootPart, part, offset
        weld.Parent = part
        part.Parent = sword
    end
    -- a wake across the blade near the guard; a Trail shows only while it moves
    local body = sword:FindFirstChild("Body")
    if body then
        -- points in the sword's own space (origin at the feet, tip toward -Z), in the body's frame
        local bodyOffset = source.Body:GetAttribute("Offset")
        local left, right = Instance.new("Attachment"), Instance.new("Attachment")
        left.Position = bodyOffset:PointToObjectSpace(Vector3.new(-0.3, 0, 1.6))
        right.Position = bodyOffset:PointToObjectSpace(Vector3.new(0.3, 0, 1.6))
        left.Parent, right.Parent = body, body
        local trail = Instance.new("Trail")
        trail.Attachment0, trail.Attachment1 = left, right
        trail.Lifetime = 0.45
        trail.MinLength = 0.2
        trail.FaceCamera = false
        trail.LightEmission = 0.5
        trail.LightInfluence = 0
        trail.Texture = "rbxassetid://187823474" -- a soft glow: no hard edges
        trail.TextureMode = Enum.TextureMode.Stretch
        trail.Color = ColorSequence.new(glow:Lerp(Color3.new(1, 1, 1), 0.35), glow)
        trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 1) })
        trail.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0.3) })
        trail.Parent = body
        -- a silk ribbon from the pommel
        local top, bottom = Instance.new("Attachment"), Instance.new("Attachment")
        top.Position = bodyOffset:PointToObjectSpace(Vector3.new(0, 0.12, 3.75))
        bottom.Position = bodyOffset:PointToObjectSpace(Vector3.new(0, -0.12, 3.75))
        top.Parent, bottom.Parent = body, body
        local ribbon = Instance.new("Trail")
        ribbon.Attachment0, ribbon.Attachment1 = top, bottom
        ribbon.Lifetime = 0.6
        ribbon.MinLength = 0.1
        ribbon.FaceCamera = true
        ribbon.LightEmission = 0.2
        ribbon.LightInfluence = 0.3
        ribbon.Color = ColorSequence.new(Color3.fromRGB(250, 246, 235), glow)
        ribbon.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05), NumberSequenceKeypoint.new(0.7, 0.4), NumberSequenceKeypoint.new(1, 1) })
        ribbon.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0.4) })
        ribbon.Parent = body
    end
    sword.Parent = swordsFolder
    return sword
end

local function land(player)
    local flight = flights[player]
    flights[player] = nil
    if flight and flight.sword then
        flight.sword:Destroy()
    end
    if flight and staminas[player] then
        local now = os.clock()
        local state = staminaAt(player, now)
        state.flying = false
        state.stamina = math.max(state.stamina, 0)
        state.refillFrom = now + regen.RegenDelay
    end
    if player.Parent then
        player:SetAttribute("IsFlying", nil)
    end
end

local function canFly(player)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    return humanoid ~= nil and humanoid.Health > 0
        and player:GetAttribute("IsCultivating") ~= true
        and player:GetAttribute("CarryingEgg") == nil -- a guardian's egg is carried on foot
        and player:GetAttribute("InTribulation") ~= true -- a tribulation is faced on foot
        and Ranks.isAtLeast(Ranks.getPlayerRankName(player), config.UnlockRank)
        and (player:GetAttribute("QinggongFlightSpeed") or 0) > 0
end

local function takeOff(player)
    if flights[player] or not canFly(player) then
        return
    end
    local state = staminaAt(player, os.clock())
    if state.stamina < config.MinStamina - TAKEOFF_SLACK then
        return
    end
    local character = player.Character
    local sword = mountSword(player, character)
    state.flying = true
    flights[player] = { sword = sword }
    player:SetAttribute("IsFlying", true)
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    humanoid.Died:Once(function()
        if flights[player] and player.Character == character then
            land(player)
        end
    end)
end

RemoteEvents.FlightEvent.OnServerEvent:Connect(function(player, wantsFlight)
    if typeof(wantsFlight) ~= "boolean" then
        return
    end
    local now = os.clock()
    if lastToggle[player] and now - lastToggle[player] < TOGGLE_COOLDOWN then
        return
    end
    lastToggle[player] = now
    if wantsFlight then
        takeOff(player)
    else
        land(player)
    end
end)

local function onPlayerAdded(player)
    player.CharacterAdded:Connect(function()
        land(player)
        staminas[player] = nil -- a new body starts with a full bar, as the client's does
    end)
    -- cultivating lands you (QiService also stops cultivation when a flight starts)
    player:GetAttributeChangedSignal("IsCultivating"):Connect(function()
        if player:GetAttribute("IsCultivating") == true and flights[player] then
            land(player)
        end
    end)
    player:GetAttributeChangedSignal("InTribulation"):Connect(function() -- and so does a tribulation
        if player:GetAttribute("InTribulation") == true and flights[player] then
            land(player)
        end
    end)
end

Players.PlayerAdded:Connect(onPlayerAdded)
for _, player in Players:GetPlayers() do
    onPlayerAdded(player)
end
Players.PlayerRemoving:Connect(function(player)
    land(player)
    lastToggle[player] = nil
    staminas[player] = nil
end)

-- lands flights whose stamina has run out (after DURATION_MARGIN seconds' grace at the hover cost), after a rank
-- loss, or once an egg is picked up
while true do
    task.wait(1)
    local now = os.clock()
    for player in flights do
        if staminaAt(player, now).stamina < -config.HoverCost * DURATION_MARGIN or not canFly(player) then
            land(player)
        end
    end
end
