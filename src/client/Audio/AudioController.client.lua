-- The background: each island's ambient bed and music, following the player's "Island" attribute
-- (WorldService). Near an awake guardian the music turns to the battle theme, and a thief carrying
-- an egg hears the chase drums over it. The weather (WeatherRules) adds its own bed: rain while it rains; and the hub's
-- morning birds give way to night insects after dark, and to the rain alone while it rains. Every button in the HUD clicks.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local WeatherConfig = require(ReplicatedStorage:WaitForChild("WeatherConfig"))
local WeatherRules = require(ReplicatedStorage:WaitForChild("WeatherRules"))
local TerritoryRules = require(ReplicatedStorage:WaitForChild("TerritoryRules"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))

local player = Players.LocalPlayer

local AMBIENCE = { Yggdrasil = "AmbYggdrasil", BeginnerIsle = "AmbYggdrasil", JadeGrove = "AmbJade", EmberPeak = "AmbEmber", MoonlitIsle = "AmbMoon", OriginAbyss = "AmbAbyss",
    BlossomSanctuary = "AmbSanctuary", -- (the sanctuary's pond and koi splashes: SanctuaryLife)
    MurimCrossing = "AmbSanctuary" } -- (wind over the plaza and the open island; each territory has its own: shared/TerritoryRules.SOUND)
local BIRDS = { AmbYggdrasil = true } -- a daytime bed: night insects after dark, nothing under the rain
local NIGHT_BED = "AmbMoon"
local MUSIC = { Yggdrasil = "MusicHub", BeginnerIsle = "MusicHub", JadeGrove = "MusicJade", EmberPeak = "MusicEmber", MoonlitIsle = "MusicMoon", OriginAbyss = "MusicAbyss",
    BlossomSanctuary = "MusicOrient", MurimCrossing = "MusicOrient" }
local AWAKE = { Guardian = true, Weakened = true, Enraged = true }
local BATTLE_DISTANCE = 150    -- studs from an awake guardian at which the battle theme takes over
local CROSSFADE = 2.5          -- seconds
local CALM_AFTER = 4           -- seconds out of battle before the island's music comes back (no flicker at the edge)
local CHECK_EVERY = 0.5

-- one slot per layer: what it plays now, its Sound and how to stop it
local layers = { ambience = {}, music = {}, chase = {}, weather = {} }
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

-- Murim Crossing's three territories each have their own bed and music (TerritoryRules.SOUND); the plaza and the open island keep the island's.
-- The territory is found from where the player stands against each Territory folder's Centre and Radius (the builders write both), and kept a little
-- past its edge so walking along a border doesn't flicker; the 2.5 s crossfade does the rest.
local PADS = { Orthodox = "OrthodoxPad", Unorthodox = "UnorthodoxPad", Demonic = "DemonicPad" }
local territoryNow = nil     -- the name of the territory the player is in, or nil
local ACCENT_REACH = 90     -- studs: a territory's accent comes from a building this close
local nextAccent = 0         -- when the territory's little sound plays next (os.clock)

local function territoryFolders()
    local islands = workspace:FindFirstChild("FloatingIslands")
    local crossing = islands and islands:FindFirstChild("MurimCrossing")
    local found = {}
    if crossing then
        for name, padName in PADS do
            local pad = crossing:FindFirstChild(padName)
            local folder = pad and pad:FindFirstChild("Territory")
            local centre, radius = folder and folder:GetAttribute("Centre"), folder and folder:GetAttribute("Radius")
            if typeof(centre) == "Vector3" and typeof(radius) == "number" then
                found[name] = { X = centre.X, Z = centre.Z, Radius = radius, Folder = folder }
            end
        end
    end
    return found
end

local function findTerritory()
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if not root or player:GetAttribute("Island") ~= "MurimCrossing" then
        territoryNow = nil
        return nil
    end
    local found = territoryFolders()
    territoryNow = TerritoryRules.which(root.Position.X, root.Position.Z, found, territoryNow)
    return territoryNow, found
end

-- the territory's accent (Orthodox: now and then a wind chime from the nearest building), after a random wait between its Min and Max
local function accent(name, found)
    local spec = TerritoryRules.SOUND[name].Accent
    if not spec or os.clock() < nextAccent then
        return
    end
    nextAccent = os.clock() + spec.Min + math.random() * (spec.Max - spec.Min)
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    local buildings = found[name] and found[name].Folder:FindFirstChild("Buildings")
    if not root or not buildings then
        return
    end
    local near = {}
    for _, model in buildings:GetChildren() do
        local part = if model:IsA("BasePart") then model else model:FindFirstChildWhichIsA("BasePart", true)
        if part and (part.Position - root.Position).Magnitude < ACCENT_REACH then
            table.insert(near, part)
        end
    end
    if #near > 0 then
        Sfx.play(spec.Name, near[math.random(#near)]) -- (a different place each time, not always the same wall)
    end
end

local function update()
    local island = player:GetAttribute("Island")
    -- the weather: rain once a change to it is half done (WeatherRules' blend), the hub's birds by day only
    local clock, _, from, to, k = WeatherRules.current()
    local raining = (if k >= 0.5 then to else from) == "Rain"
    local territory, found = findTerritory()
    local own = territory and TerritoryRules.SOUND[territory]
    local bed = if own then own.Ambience else AMBIENCE[island]
    if bed and BIRDS[bed] then
        bed = if raining then nil elseif WeatherRules.nightAt(clock) > 0.6 then NIGHT_BED else bed
    end
    set("ambience", bed)
    set("weather", if raining then WeatherConfig.Rain.Sound else nil)
    local carrying = player:GetAttribute("CarryingEgg") ~= nil
    if carrying or nearAwakeGuardian() then
        battleAt = os.clock()
    end
    local fighting = os.clock() - battleAt < CALM_AFTER
    set("music", if fighting then "MusicBattle" elseif own then own.Music else MUSIC[island])
    set("chase", if carrying then "ChaseLoop" else nil)
    if territory and found and not fighting then
        accent(territory, found)
    end
end

player:GetAttributeChangedSignal("Island"):Connect(update)
player:GetAttributeChangedSignal("CarryingEgg"):Connect(update)
task.spawn(function()
    while true do
        update()
        task.wait(CHECK_EVERY)
    end
end)

-- this player's cultivation: a soft swell as they sit, a low hum while they meditate, the shimmer falling away as they rise
local stopHum = nil
local function cultivating(changed)
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    local now = player:GetAttribute("IsCultivating") == true
    if stopHum then
        stopHum()
        stopHum = nil
        if changed and not now and root then
            Sfx.play("CultivateStop", root)
        end
    end
    if now and root then
        stopHum = Sfx.loop("CultivateLoop", root)
        if changed then
            Sfx.play("CultivateStart", root)
        end
    end
end
player:GetAttributeChangedSignal("IsCultivating"):Connect(function()
    cultivating(true)
end)
cultivating(false)

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
-- Sword: TouchActions' ScreenGui) are actions with sounds of their own. The click waits for the button's own handlers:
-- a button that sounds for itself (a window opening, a tab, a refusal) isn't clicked over.
local playerGui = player:WaitForChild("PlayerGui")
local function click()
    if not Sfx.interfaceSince(0.05) then
        Sfx.play("Click")
    end
end
local function hook(button)
    local gui = button:FindFirstAncestorOfClass("ScreenGui")
    if button:IsA("GuiButton") and not (gui and gui.Name == "TouchActions") then
        button.Activated:Connect(function()
            task.defer(click)
        end)
    end
end
playerGui.DescendantAdded:Connect(hook)
for _, item in playerGui:GetDescendants() do
    hook(item)
end
