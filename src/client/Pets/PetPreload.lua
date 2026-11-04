-- Downloads a pet's meshes and maps before it's shown. A pet is many mesh pieces, fetched only when first
-- used, so without this it appears a piece at a time, or late, on a phone's connection. One pet loads at
-- a time, those being shown first; a pet that takes too long is shown anyway, so it can never go missing.
local ContentProvider = game:GetService("ContentProvider")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PetPreload = {}

local TIMEOUT = 8 -- seconds before a waiting pet is shown as it is

local meshFolder = ReplicatedStorage:WaitForChild("PetMeshes", 10)
local loaded = {}    -- [petId] = true
local queue = {}     -- petIds, first in line first
local waiting = {}   -- [petId] = callbacks
local working = false

local function finish(petId)
    loaded[petId] = true
    local callbacks = waiting[petId]
    waiting[petId] = nil
    for _, callback in callbacks or {} do
        task.spawn(callback)
    end
end

local function work()
    if working then
        return
    end
    working = true
    task.spawn(function()
        while #queue > 0 do
            local petId = table.remove(queue, 1)
            if not loaded[petId] then
                local imported = meshFolder and meshFolder:FindFirstChild(petId, true)
                if imported then
                    pcall(function()
                        ContentProvider:PreloadAsync({ imported })
                    end)
                end
                finish(petId)
            end
        end
        working = false
    end)
end

-- Fetches a pet in the background (the ones a player owns, ready for when they're wanted).
function PetPreload.soon(petId)
    if not loaded[petId] and not table.find(queue, petId) then
        table.insert(queue, petId)
        work()
    end
end

-- Calls back once the pet is fetched, or after TIMEOUT; at once if it already is.
function PetPreload.whenReady(petId, callback)
    if loaded[petId] then
        callback()
        return
    end
    local done = false
    local function once()
        if not done then
            done = true
            callback()
        end
    end
    waiting[petId] = waiting[petId] or {}
    table.insert(waiting[petId], once)
    task.delay(TIMEOUT, once)
    local index = table.find(queue, petId)
    if index then
        table.remove(queue, index)
    end
    table.insert(queue, 1, petId) -- ahead of anything only fetched for later
    work()
end

return PetPreload
