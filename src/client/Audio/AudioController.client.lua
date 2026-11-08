-- The background: each island's ambient bed and music, following the player's "Island" attribute
-- (WorldService). Near an awake guardian the music turns to the battle theme, and a thief carrying
-- an egg hears the chase drums over it. Every button in the HUD clicks.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))

local player = Players.LocalPlayer

local AMBIENCE = { Yggdrasil = "AmbYggdrasil", BeginnerIsle = "AmbYggdrasil", JadeGrove = "AmbJade", EmberPeak = "AmbEmber", MoonlitIsle = "AmbMoon", OriginAbyss = "AmbAbyss" }
local MUSIC = { Yggdrasil = "MusicHub", BeginnerIsle = "MusicHub", JadeGrove = "MusicJade", EmberPeak = "MusicEmber", MoonlitIsle = "MusicMoon", OriginAbyss = "MusicAbyss" }
local AWAKE = { Guardian = true, Weakened = true, Enraged = true }
local BATTLE_DISTANCE = 150    -- studs from an awake guardian at which the battle theme takes over
local CROSSFADE = 2.5          -- seconds
local CALM_AFTER = 4           -- seconds out of battle before the island's music comes back (no flicker at the edge)
local CHECK_EVERY = 0.5

-- one slot per layer: what it plays now, its Sound and how to stop it
local layers = { ambience = {}, music = {}, chase = {} }
local resumeAt = {} -- [name] = where a track was left: the island's music picks up there after a fight

local function set(layer, name)
    local slot = layers[layer]
    if slot.name == name then
        return
    end
    if slot.stop then
        if slot.sound then
            resumeAt[slot.name] = slot.sound.TimePosition
        end
        slot.stop(CROSSFADE)
    end
    slot.name = name
    slot.stop, slot.sound = nil, nil
    if name then
        slot.stop, slot.sound = Sfx.loop(name)
        if slot.sound and resumeAt[name] then
            slot.sound.TimePosition = resumeAt[name]
        end
    end
end

local function nearAwakeGuardian()
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if not root then
        return false
    end
    for _, model in CollectionService:GetTagged(GameConfig.GuardianTag) do
        if AWAKE[model:GetAttribute("State")] and model.PrimaryPart
            and (model.PrimaryPart.Position - root.Position).Magnitude <= BATTLE_DISTANCE then
            return true
        end
    end
    return false
end

local battleAt = -math.huge

local function update()
    local island = player:GetAttribute("Island")
    set("ambience", AMBIENCE[island])
    local carrying = player:GetAttribute("CarryingEgg") ~= nil
    if carrying or nearAwakeGuardian() then
        battleAt = os.clock()
    end
    set("music", if os.clock() - battleAt < CALM_AFTER then "MusicBattle" else MUSIC[island])
    set("chase", if carrying then "ChaseLoop" else nil)
end

player:GetAttributeChangedSignal("Island"):Connect(update)
player:GetAttributeChangedSignal("CarryingEgg"):Connect(update)
task.spawn(function()
    while true do
        update()
        task.wait(CHECK_EVERY)
    end
end)

-- this player's cultivation: a low hum while they sit in meditation
local stopHum = nil
local function cultivating()
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if stopHum then
        stopHum()
        stopHum = nil
    end
    if player:GetAttribute("IsCultivating") == true and root then
        stopHum = Sfx.loop("CultivateLoop", root)
    end
end
player:GetAttributeChangedSignal("IsCultivating"):Connect(cultivating)
cultivating()

-- sword flight, for every player: the blade rings as it takes them up, and the wind rushes while
-- they fly (on their body, so it fades with distance and goes with a respawn)
local stopFlight = {}
local function watchFlight(other)
    local function changed(joined)
        local root = other.Character and other.Character:FindFirstChild("HumanoidRootPart")
        local flying = other:GetAttribute("IsFlying") == true
        if stopFlight[other] then
            stopFlight[other]()
            stopFlight[other] = nil
        end
        if flying and root then
            if not joined then
                Sfx.play("SwordTakeoff", root)
            end
            stopFlight[other] = Sfx.loop("FlightLoop", root)
        end
    end
    other:GetAttributeChangedSignal("IsFlying"):Connect(function()
        changed(false)
    end)
    if other:GetAttribute("IsFlying") == true then
        changed(true) -- already up when we arrived: only the wind
    end
end
Players.PlayerAdded:Connect(watchFlight)
Players.PlayerRemoving:Connect(function(other)
    stopFlight[other] = nil
end)
for _, other in Players:GetPlayers() do
    watchFlight(other)
end

-- every button the HUD makes, now or later, clicks when pressed; the touch controls (Strike, Dash,
-- Sword: TouchActions' ScreenGui) are actions with sounds of their own
local playerGui = player:WaitForChild("PlayerGui")
local function hook(button)
    local gui = button:FindFirstAncestorOfClass("ScreenGui")
    if button:IsA("GuiButton") and not (gui and gui.Name == "TouchActions") then
        button.Activated:Connect(function()
            Sfx.play("Click")
        end)
    end
end
playerGui.DescendantAdded:Connect(hook)
for _, item in playerGui:GetDescendants() do
    hook(item)
end
