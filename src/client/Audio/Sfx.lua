-- The game's sounds, client side. Every sound is named in SoundCatalog (its Creator Store ids, from
-- Roblox's licensed libraries, and how it plays); this module plays them.
--
--   Sfx.play(name, at, pitch)  a one-shot, its pitch optionally scaled. `at` is a Vector3 or a BasePart / Attachment to sound from
--                            (it fades with distance, and is skipped beyond its reach), or nil for a
--                            flat sound (the interface, the local player's own feedback). Its layers (the entry's `With`)
--                            play with it, each at its own delay.
--   Sfx.after(delay, name, at, pitch)  the same, `delay` seconds later (an attack's impact after its wind-up).
--   Sfx.loop(name, parent)   a loop on a part (or flat with no parent), faded in; returns a function
--                            that fades it out and removes it, and the Sound.
--   Sfx.fadeOut(sound, time)  fades a playing one-shot out and removes it (a riser cut off by what it built up to).
--   Sfx.duck(level, seconds)  lowers the music (and a little of the island's bed) under a big moment, then lets it back.
--   Sfx.interfaceSince(seconds)  true if an interface sound began that recently (a button's own sound replaces its click).
--   Sfx.hold(seconds)        holds the stage for a big moment: notices wait it out (see below).
--
-- Sounds go through four SoundGroups in SoundService (Music, Ambience, Effects, Interface).
--   Sfx.setVolume(kind, share)  the player's setting, 0 to 1: "Music", or "Sound" for all the rest.
--
-- Against clutter: the same sound asked for again within its `Gap` is dropped (many players hitting at once), no more than its
-- `Max` copies play together, and past ALIVE_LIMIT sounds in all only the entries marked `Key` still start. A big moment
-- (an entry's `Moment`, in seconds) has the stage to itself: a notice (an entry marked `Defer`: a quest step, a title, the
-- breakthrough being ready) asked for meanwhile waits until it is over, then the waiting ones play one after another.
local ContentProvider = game:GetService("ContentProvider")
local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local SoundCatalog = require(script.Parent:WaitForChild("SoundCatalog"))

local Sfx = {}

local GROUP_VOLUME = { Music = 0.45, Ambience = 0.6, Effects = 1, Interface = 0.6 }
local REPEAT_GAP = 0.04     -- seconds: the same sound asked for again sooner is dropped (many players at once)
local MAX_COPIES = 6        -- copies of one sound playing at once, unless its entry says otherwise
local ALIVE_LIMIT = 40      -- one-shots playing at once, in all: past it only `Key` entries start
local FADE = 0.6            -- seconds a loop fades in and out
local LIFETIME = 12         -- seconds a one-shot is kept at most, if it never reports its end
local AMBIENCE_DUCK = 0.5   -- how much of a duck the island's bed takes (the music takes all of it)
local DEFER_SPACING = 1.1   -- seconds between notices that waited out a big moment (a quest step's chime runs 1.5 s)
local DEFER_LIMIT = 6       -- seconds a notice may wait before it's no longer worth playing

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

-- each group's volume: its base, times the player's setting, times the duck (Music and Ambience only)
local shares = { Music = 1, Sound = 1 }
local duckLevel = 1
local function groupVolume(name)
    local share = if name == "Music" then shares.Music else shares.Sound
    local duck = if name == "Music" then duckLevel elseif name == "Ambience" then 1 - (1 - duckLevel) * AMBIENCE_DUCK else 1
    return GROUP_VOLUME[name] * share * duck
end
local function applyVolumes(time)
    for name, group in groups do
        local volume = groupVolume(name)
        if time and time > 0 then
            TweenService:Create(group, TweenInfo.new(time, Enum.EasingStyle.Sine), { Volume = volume }):Play()
        else
            group.Volume = volume
        end
    end
end

function Sfx.setVolume(kind, share)
    shares[if kind == "Music" then "Music" else "Sound"] = share
    applyVolumes()
end

-- the music dips to `level` (0 to 1) over a quarter second, holds `seconds`, and comes back over a second and a half; a
-- deeper or longer duck asked for meanwhile wins
local duckUntil, duckId = 0, 0
function Sfx.duck(level, seconds)
    local now = os.clock()
    if level >= duckLevel and now < duckUntil and now + seconds <= duckUntil then
        return
    end
    duckLevel = math.min(level, if now < duckUntil then duckLevel else 1)
    duckUntil = math.max(duckUntil, now + seconds)
    duckId += 1
    local mine = duckId
    applyVolumes(0.25)
    task.delay(duckUntil - now, function()
        if duckId == mine then
            duckLevel = 1
            applyVolumes(1.5)
        end
    end)
end

local lastPlayed = {}  -- [name] = os.clock() it last started
local copies = {}      -- [name] = how many are playing
local alive = 0
local lastInterface = -math.huge

function Sfx.interfaceSince(seconds)
    return os.clock() - lastInterface <= seconds
end

local function pick(ids)
    return if type(ids) == "table" then ids[math.random(#ids)] else ids
end

local function spread(spec)
    local notes = spec.Notes
    if notes then
        return notes[math.random(#notes)]
    end
    local range = spec.Pitch
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
    sound.PlaybackSpeed = spread(spec)
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

-- a layer of `With`: a name, or { name, delay }
local function layers(with)
    if not with then
        return {}
    elseif type(with) == "string" then
        return { { with, 0 } }
    elseif type(with[1]) == "string" and type(with[2]) == "number" then
        return { with }
    end
    local out = {}
    for _, layer in with do
        table.insert(out, if type(layer) == "string" then { layer, 0 } else layer)
    end
    return out
end

-- the big moment holding the stage, and the notices waiting for it
local momentUntil = 0
local waiting = {} -- { name, at, pitch, asked }
local draining = false
local playLayer
local function drain()
    if draining then
        return
    end
    draining = true
    task.spawn(function()
        while #waiting > 0 do
            local wait = momentUntil - os.clock()
            if wait > 0 then
                task.wait(wait)
            else
                local entry = table.remove(waiting, 1)
                if os.clock() - entry[4] <= DEFER_LIMIT then
                    playLayer(entry[1], entry[2], entry[3])
                    task.wait(DEFER_SPACING)
                end
            end
        end
        draining = false
    end)
end

function playLayer(name, at, pitch)
    local spec = SoundCatalog[name]
    if not spec then
        warn("Sfx: no sound named " .. tostring(name))
        return nil
    end
    local now = os.clock()
    if spec.Defer and now < momentUntil then
        for _, entry in waiting do
            if entry[1] == name then
                return nil -- (already waiting)
            end
        end
        table.insert(waiting, { name, at, pitch, now })
        drain()
        return nil
    end
    if now - (lastPlayed[name] or -math.huge) < (spec.Gap or REPEAT_GAP) then
        return nil
    end
    if (copies[name] or 0) >= (spec.Max or MAX_COPIES) or (alive >= ALIVE_LIMIT and not spec.Key) then
        return nil
    end
    local position = positionOf(at)
    local camera = Workspace.CurrentCamera
    if position and camera and (camera.CFrame.Position - position).Magnitude > (spec.Reach or 120) then
        return nil
    end
    lastPlayed[name] = now
    local group = spec.Group or "Effects"
    if group == "Interface" then
        lastInterface = now
    end
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
        sound.Parent = groups[group]
    end
    copies[name] = (copies[name] or 0) + 1
    alive += 1
    local gone = false
    local trash = holder or sound
    local function remove()
        if gone then
            return
        end
        gone = true
        copies[name] -= 1
        alive -= 1
        trash:Destroy()
    end
    sound.Destroying:Once(function()
        -- (a sound on a part that went away)
        if not gone then
            gone = true
            copies[name] -= 1
            alive -= 1
        end
    end)
    local length = spec.Length
    if length then
        -- cut a longer file short, with a quick fade so it doesn't click
        local fade = spec.Fade or 0.15
        task.delay(length / sound.PlaybackSpeed, function()
            if sound.Parent then
                TweenService:Create(sound, TweenInfo.new(fade), { Volume = 0 }):Play()
            end
        end)
        task.delay(length / sound.PlaybackSpeed + fade + 0.05, remove)
    else
        sound.Ended:Once(remove)
        task.delay(LIFETIME, remove)
    end
    sound:Play()
    if spec.Moment then
        momentUntil = math.max(momentUntil, now + spec.Moment)
    end
    if spec.Duck then
        Sfx.duck(spec.Duck[1], spec.Duck[2])
    end
    for _, layer in layers(spec.With) do
        if layer[2] > 0 then
            task.delay(layer[2], playLayer, layer[1], at)
        else
            playLayer(layer[1], at)
        end
    end
    return sound
end

-- a big moment that isn't one entry (the player's own breakthrough, whose sound is the same one others hear): notices wait
-- `seconds`
function Sfx.hold(seconds)
    momentUntil = math.max(momentUntil, os.clock() + seconds)
end

function Sfx.play(name, at, pitch)
    return playLayer(name, at, pitch)
end

function Sfx.after(delay, name, at, pitch)
    task.delay(delay, playLayer, name, at, pitch)
end

function Sfx.fadeOut(sound, time)
    if not (sound and sound.Parent) then
        return
    end
    time = time or 0.25
    TweenService:Create(sound, TweenInfo.new(time), { Volume = 0 }):Play()
    task.delay(time + 0.05, function()
        if sound.Parent then
            sound:Stop()
            local holder = sound.Parent
            sound:Destroy()
            if holder:IsA("Attachment") and holder.Name:sub(1, 4) == "Sfx_" then
                holder:Destroy()
            end
        end
    end)
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

-- the number of one-shots playing now (for testing the limits above)
function Sfx.alive()
    return alive
end

-- load the effects once in the background, so the first of each doesn't arrive late (music and
-- beds stream when they start: they're long, and only one plays at a time)
task.spawn(function()
    local list = {}
    local seen = {}
    for _, spec in SoundCatalog do
        local ids = if type(spec.Id) == "table" then spec.Id else { spec.Id }
        for _, id in if spec.Group == "Music" or spec.Group == "Ambience" then {} else ids do
            if not seen[id] then
                seen[id] = true
                local sound = Instance.new("Sound")
                sound.SoundId = "rbxassetid://" .. id
                table.insert(list, sound)
            end
        end
    end
    ContentProvider:PreloadAsync(list)
    for _, sound in list do
        sound:Destroy()
    end
end)

return Sfx
