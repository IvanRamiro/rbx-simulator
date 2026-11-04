-- The game's sounds, client side. Every sound is named in SoundCatalog (its Creator Store ids, from
-- Roblox's licensed libraries, and how it plays); this module plays them.
--
--   Sfx.play(name, at, pitch)  a one-shot, its pitch optionally scaled. `at` is a Vector3 or a BasePart / Attachment to sound from
--                            (it fades with distance, and is skipped beyond its reach), or nil for a
--                            flat sound (the interface, the local player's own feedback).
--   Sfx.after(delay, name, at)  the same, `delay` seconds later (an attack's impact after its wind-up).
--   Sfx.loop(name, parent)   a loop on a part (or flat with no parent), faded in; returns a function
--                            that fades it out and removes it, and the Sound.
--
-- Sounds go through four SoundGroups in SoundService (Music, Ambience, Effects, Interface).
--   Sfx.setVolume(kind, share)  the player's setting, 0 to 1: "Music", or "Sound" for all the rest.
local ContentProvider = game:GetService("ContentProvider")
local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local SoundCatalog = require(script.Parent:WaitForChild("SoundCatalog"))

local Sfx = {}

local GROUP_VOLUME = { Music = 0.45, Ambience = 0.6, Effects = 1, Interface = 0.6 }
local REPEAT_GAP = 0.04     -- seconds: the same sound asked for again sooner is dropped (many players at once)
local FADE = 0.6            -- seconds a loop fades in and out
local LIFETIME = 12         -- seconds a one-shot is kept at most, if it never reports its end

local groups = {}
for name, volume in GROUP_VOLUME do
    local group = SoundService:FindFirstChild(name)
    if not (group and group:IsA("SoundGroup")) then
        group = Instance.new("SoundGroup")
        group.Name = name
        group.Volume = volume
        group.Parent = SoundService
    end
    groups[name] = group
end

function Sfx.setVolume(kind, share)
    for name, group in groups do
        if (name == "Music") == (kind == "Music") then
            group.Volume = GROUP_VOLUME[name] * share
        end
    end
end

local lastPlayed = {}

local function pick(ids)
    return if type(ids) == "table" then ids[math.random(#ids)] else ids
end

local function spread(range)
    if type(range) == "table" then
        return range[1] + (range[2] - range[1]) * math.random()
    end
    return range or 1
end

local function make(spec, name)
    local sound = Instance.new("Sound")
    sound.Name = name
    sound.SoundId = "rbxassetid://" .. pick(spec.Id)
    sound.Volume = spec.Volume or 0.5
    sound.PlaybackSpeed = spread(spec.Pitch)
    sound.TimePosition = spec.Start or 0
    sound.SoundGroup = groups[spec.Group or "Effects"]
    sound.RollOffMode = Enum.RollOffMode.InverseTapered
    sound.RollOffMinDistance = spec.Near or 10
    sound.RollOffMaxDistance = spec.Reach or 120
    return sound
end

-- where `at` is in the world, or nil for a flat sound
local function positionOf(at)
    if typeof(at) == "Vector3" then
        return at
    elseif typeof(at) == "Instance" then
        if at:IsA("BasePart") then
            return at.Position
        elseif at:IsA("Attachment") then
            return at.WorldPosition
        end
    end
    return nil
end

function Sfx.play(name, at, pitch)
    local spec = SoundCatalog[name]
    if not spec then
        warn("Sfx: no sound named " .. tostring(name))
        return nil
    end
    local now = os.clock()
    if now - (lastPlayed[name] or 0) < REPEAT_GAP then
        return nil
    end
    local position = positionOf(at)
    local camera = Workspace.CurrentCamera
    if position and camera and (camera.CFrame.Position - position).Magnitude > (spec.Reach or 120) then
        return nil
    end
    lastPlayed[name] = now
    local sound = make(spec, name)
    sound.PlaybackSpeed *= pitch or 1
    local holder
    if typeof(at) == "Instance" and position then
        sound.Parent = at
    elseif position then
        holder = Instance.new("Attachment")
        holder.Name = "Sfx_" .. name
        holder.Parent = Workspace.Terrain
        holder.WorldPosition = position
        sound.Parent = holder
    else
        sound.Parent = groups[spec.Group or "Effects"]
    end
    local trash = holder or sound
    local length = spec.Length
    if length then
        -- cut a longer file short, with a quick fade so it doesn't click
        task.delay(length / sound.PlaybackSpeed, function()
            if sound.Parent then
                TweenService:Create(sound, TweenInfo.new(0.15), { Volume = 0 }):Play()
            end
        end)
        task.delay(length / sound.PlaybackSpeed + 0.2, function()
            trash:Destroy()
        end)
    else
        sound.Ended:Once(function()
            trash:Destroy()
        end)
        task.delay(LIFETIME, function()
            if trash.Parent then
                trash:Destroy()
            end
        end)
    end
    sound:Play()
    -- a layered sound: its other layers, from the same place
    local with = spec.With
    for _, layer in if type(with) == "table" then with elseif with then { with } else {} do
        Sfx.play(layer, at)
    end
    return sound
end

function Sfx.after(delay, name, at)
    task.delay(delay, Sfx.play, name, at)
end

function Sfx.loop(name, parent)
    local spec = SoundCatalog[name]
    if not spec then
        warn("Sfx: no sound named " .. tostring(name))
        return function() end, nil
    end
    local sound = make(spec, name)
    local volume = sound.Volume
    sound.Looped = true
    sound.Volume = 0
    sound.Parent = parent or groups[spec.Group or "Effects"]
    sound:Play()
    TweenService:Create(sound, TweenInfo.new(spec.FadeIn or FADE), { Volume = volume }):Play()
    local stopped = false
    local function stop(fade)
        if stopped then
            return
        end
        stopped = true
        fade = fade or spec.FadeOut or FADE
        if not sound.Parent then
            return
        end
        TweenService:Create(sound, TweenInfo.new(fade), { Volume = 0 }):Play()
        task.delay(fade + 0.05, function()
            sound:Destroy()
        end)
    end
    return stop, sound
end

-- load the effects once in the background, so the first of each doesn't arrive late (music and
-- beds stream when they start: they're long, and only one plays at a time)
task.spawn(function()
    local list = {}
    for _, spec in SoundCatalog do
        local ids = if type(spec.Id) == "table" then spec.Id else { spec.Id }
        for _, id in if spec.Group == "Music" or spec.Group == "Ambience" then {} else ids do
            local sound = Instance.new("Sound")
            sound.SoundId = "rbxassetid://" .. id
            table.insert(list, sound)
        end
    end
    ContentProvider:PreloadAsync(list)
    for _, sound in list do
        sound:Destroy()
    end
end)

return Sfx
