-- The pets that follow each player: builds every equipped pet (their EquippedPets attribute) beside its owner, walks and
-- poses them (PetRig), and thins other players' pets with distance and Reduced Effects.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local PetModels = require(script.Parent:WaitForChild("PetModels"))
local PetRig = require(script.Parent:WaitForChild("PetRig"))
local PetPreload = require(script.Parent:WaitForChild("PetPreload"))
local PetHeft = require(script.Parent:WaitForChild("PetHeft"))

-- where each pet walks, in studs from its owner (x to the right, z behind): beside them, never in the line between them and
-- the camera, which sits straight behind them. Pets are about 6 studs long.
-- where each equipped beast walks (studs: X to the owner's right, Y behind them); the last three are the slots pass's (PassRules).
-- These are where a Normal one's middle walks; a bigger one walks farther out, by its own footprint (followOffsets).
local FOLLOW_SLOTS = { Vector2.new(6.4, 2.4), Vector2.new(-6.4, 2.4), Vector2.new(12.5, 1.2), Vector2.new(-12.5, 1.2), Vector2.new(4.2, 9.5), Vector2.new(-4.2, 9.5) }
local BACK_ROW = { [5] = true, [6] = true }    -- the slots behind the owner: only a pet this small walks there (else beside them)
local BACK_ROW_HALF = Vector2.new(3.5, 4.5)    -- (half its box: across, nose to tail)
local SIDE_GAP = 1.5      -- studs between a pet's flank and its owner's path, and 1.5 more for each size over Normal (a Giant 5)
local NEIGHBOUR_GAP = 0.8 -- studs between two pets on the same side
local CAMERA_BACK = 4     -- studs behind its owner a big pet's back end may reach (the camera follows about 12 behind): a long Giant walks
                          -- forward, so its tail doesn't fill the corner of the screen
local FOLLOW_HEIGHT = 0.9
local FOLLOW_SHARPNESS = 6 -- a Normal pet's; a bigger one follows more slowly, heavier (divided by the root of its size)
local FLIGHT_LIFT = 1.5   -- studs higher in flight for each size over Normal (a flying Giant rides over its owner's line of sight)
local LANDING_AIRTIME = 1 -- seconds in the air before a Giant walker lands with a thud and dust (not every hop)
local STRIDE = 0.4        -- a Giant walker's footfall every this share of its length travelled (about 1.5 a second at a run)
local SHADOW_EVERY = 3    -- frames between a big pet's ground checks for its shadow
local SNAP_DISTANCE = 40
local BOB_HEIGHT = 0.25
local BOB_SPEED = 2
local ORBIT_RADIUS = 6.5
local ORBIT_HEIGHT = 1.6
local ORBIT_SPEED = 0.6
local updateWarned = {} -- [petId] = true once its update has failed and been reported
local NOVA_INTERVAL = 25
local Quality = require(script.Parent.Parent:WaitForChild("Quality"))
local CULL_DISTANCE = if Quality.Low then 80 else 250 -- studs from the camera: other players' pets farther away are hidden and not animated
local RANK_CHECK_INTERVAL = 0.5
-- Another player's pets farther from the camera pose less often: every 2nd frame past LOD_HALF, every 3rd past LOD_THIRD
-- (they still move every frame). A rig's pose costs 20-40 microseconds a frame (measured in Play, 2026-11-12), and a busy hub
-- holds dozens. The player's own pets always pose every frame.
local LOD_HALF = if Quality.Low then 30 else 60
local LOD_THIRD = if Quality.Low then 55 else 140
-- another player's pets play their specials only this near the camera, and never with Reduced Effects on (release audit,
-- 2026-11-12: each makes parts, emitters and a light, every 25 s per pet of everyone cultivating)
local NOVA_REACH = if Quality.Low then 40 else 60

local function novaAllowed(player, pet)
    if player == Players.LocalPlayer then
        return true
    end
    if Players.LocalPlayer:GetAttribute("SettingReducedEffects") == true then
        return false
    end
    local camera = workspace.CurrentCamera
    return camera ~= nil and pet.rootPart ~= nil and (camera.CFrame.Position - pet.rootPart.Position).Magnitude <= NOVA_REACH
end

local container = Instance.new("Folder")
container.Name = "PetCompanions"
container.Parent = workspace

local companions = {}

local function destroyPet(pet)
    pet.model:Destroy()
end

local function clearPets(entry)
    for _, pet in entry.pets do
        destroyPet(pet)
    end
    entry.pets = {}
end

local function getRankNumber(player)
    return Ranks.getIndex(Ranks.getPlayerRankName(player))
end

-- `hidden`: its owner is culled (far away), so it waits out of the world like their other pets. `key` is "PetId:Size". `own`: the
-- local player's (another player's big pet on a phone gives up its shadow and dust).
local function buildPet(key, rootPart, hidden, own)
    local petId, size = string.match(key, "^([^:]+):?(.*)$")
    local model, petRoot = PetModels.build(petId, size)
    if not model then
        return nil
    end
    -- every piece moved, before parenting: a hidden pet waits out of the world, where pieces welded to its root
    -- wouldn't follow the root alone (they'd show offset once its owner came near)
    model:PivotTo(rootPart.CFrame)
    local foot = PetHeft.measure(model) -- its footprint, as built (before its shadow joins the model)
    local heft = own or not Quality.Low
    local pet = {
        model = model,
        rootPart = petRoot,
        cframe = rootPart.CFrame,
        petId = petId,
        key = key,
        scale = model:GetAttribute("SizeScale") or 1, -- its hatch size: where it walks and how high it rides scale with it
        rig = PetModels.getRig(model),
        speed = 0,
        foot = foot,
        shadow = if heft then PetHeft.shadow(model, foot.half) else nil,
        dust = if heft and PetModels.Walkers[petId] then PetHeft.dust(model, petRoot, foot.half) else nil,
        stepLeft = 0,
        stepSide = 1,
    }
    model.Parent = if hidden then nil else container
    return pet
end

-- Keeps a player's pets matching their EquippedPets ("PetId:Size", ...): pets still equipped stay where they are,
-- new ones appear at the player's side, unequipped ones go. A new character starts them all again.
local function syncPets(player, entry)
    local character = player.Character
    local rootPart = character and character:FindFirstChild("HumanoidRootPart")
    local equipped = player:GetAttribute("EquippedPets")
    equipped = if typeof(equipped) == "string" and rootPart then equipped else ""
    if equipped == entry.equipped and entry.settled and rootPart == entry.rootPart then
        return
    end
    entry.equipped = equipped

    -- a pet joins once its meshes have arrived, so it appears whole (PetPreload)
    local shown = {}
    entry.settled = true
    for _, key in string.split(equipped, ",") do
        local petId = string.match(key, "^[^:]+")
        if petId then
            if PetPreload.isReady(petId) then
                table.insert(shown, key)
            else
                PetPreload.want(petId)
                entry.settled = false
            end
        end
    end
    local key = table.concat(shown, ",")

    if key == entry.key and rootPart == entry.rootPart then
        return
    end
    -- a pet equipped or put away is heard at its owner's side; a whole set built at once (joining, a new character) is not
    local audible = rootPart ~= nil and rootPart == entry.rootPart and not entry.culled
        and not (player == Players.LocalPlayer and player:GetAttribute("InHatchCinematic") == true)
    if rootPart ~= entry.rootPart then
        clearPets(entry)
    end
    entry.key = key
    entry.rootPart = rootPart

    local spare = {}
    for _, pet in entry.pets do
        spare[pet.key] = spare[pet.key] or {}
        table.insert(spare[pet.key], pet)
    end
    entry.pets = {}
    if key ~= "" then
        for _, petKey in string.split(key, ",") do
            local kept = spare[petKey] and table.remove(spare[petKey])
            local pet = kept or buildPet(petKey, rootPart, entry.culled, player == Players.LocalPlayer)
            if pet and not kept and audible then
                PetRig.Sfx.play("PetSummon", rootPart)
            end
            if pet then
                if pet.rig then
                    pet.rig.owner = player -- (a special can show its owner: the Obsidian Guardian's)
                elseif Quality.Low and player ~= Players.LocalPlayer then
                    -- an unrigged pet's light (PetRig's sweep covers rigged ones): another player's pet on a phone gives it up
                    for _, d in pet.model:GetDescendants() do
                        if d:IsA("PointLight") then
                            d.Enabled = false
                        end
                    end
                end
                table.insert(entry.pets, pet)
            end
        end
    end
    for _, pets in spare do
        for _, pet in pets do
            if audible and pet.rootPart and pet.rootPart:IsDescendantOf(workspace) then
                PetRig.Sfx.play("PetDismiss", pet.rootPart.Position)
            end
            destroyPet(pet)
        end
    end
end

-- Hides or shows a player's pets.
local function setCulled(entry, culled)
    entry.culled = culled
    local parent = if culled then nil else container
    for _, pet in entry.pets do
        pet.model.Parent = parent
    end
end

local function levelFacing(rootPart)
    local look = rootPart.CFrame.LookVector
    local flatLook = Vector3.new(look.X, 0, look.Z)
    if flatLook.Magnitude < 0.01 then
        flatLook = Vector3.new(0, 0, -1)
    end
    local position = rootPart.Position
    return CFrame.lookAt(position, position + flatLook.Unit)
end

-- the height of the owner's root above their feet (a pet's place above the ground scales with its size from there)
local function hipOf(player)
    local humanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
    local rootPart = humanoid and humanoid.RootPart
    return if rootPart then humanoid.HipHeight + rootPart.Size.Y / 2 else 3
end

-- Each pet's place beside its owner, with its size (pets[i].scale) and its footprint (pets[i].foot, as built): a pet rides at its size
-- times the height a Normal one rides above the ground (so a Giant's feet still reach it and a Small's do too). A Normal one walks at
-- its slot; a bigger one walks out past its owner by its own half-width (never nearer than its slot), and a long one walks forward so
-- its back end stays clear of the camera behind its owner. A pet farther out on the same side keeps clear of the one nearer in, by
-- footprints; a back-row slot (5, 6) takes only a small pet, a bigger one walks beside the emptier side instead. In flight a big pet
-- rides higher. While its owner cultivates they all circle at one radius: past the largest's reach, and wide enough for them all.
local function followOffsets(pets, hip, flying)
    local offsets = {}
    local edge, count = { [1] = 0, [-1] = 0 }, { [1] = 0, [-1] = 0 }
    local lastX = { [1] = 0, [-1] = 0 }
    local reachMost, reaches = 0, {}
    for index, pet in pets do
        local slot = FOLLOW_SLOTS[index] or FOLLOW_SLOTS[#FOLLOW_SLOTS]
        local f = pet.scale or 1
        local half = if pet.foot then pet.foot.half else Vector3.new(2, 2, 3) * f
        local off = if pet.foot then pet.foot.offset else Vector3.zero
        local cx, cz
        if BACK_ROW[index] and half.X <= BACK_ROW_HALF.X and half.Z <= BACK_ROW_HALF.Y then
            cx, cz = slot.X, slot.Y
        else
            local side = if slot.X >= 0 then 1 else -1
            if BACK_ROW[index] and edge[-side] < edge[side] then
                side = -side
            end
            local out
            if count[side] == 0 then
                out = math.max(math.abs(FOLLOW_SLOTS[1].X), half.X + SIDE_GAP * math.max(f, 1))
            else
                out = math.max(lastX[side] + (math.abs(FOLLOW_SLOTS[3].X) - math.abs(FOLLOW_SLOTS[1].X)), edge[side] + NEIGHBOUR_GAP + half.X)
            end
            local back = if count[side] == 0 then FOLLOW_SLOTS[1].Y else FOLLOW_SLOTS[3].Y
            cx, cz = side * out, if f > 1 then math.min(back, CAMERA_BACK - half.Z) else back
            edge[side], lastX[side], count[side] = out + half.X, out, count[side] + 1
        end
        local reach = math.max(half.X, half.Z)
        reachMost, reaches[index] = math.max(reachMost, reach), reach
        offsets[index] = {
            x = cx - off.X,
            z = cz - off.Z,
            y = (hip + FOLLOW_HEIGHT) * f - hip + (if flying then FLIGHT_LIFT * math.max(f - 1, 0) else 0),
            rest = (hip + FOLLOW_HEIGHT) * f, -- its root's height over the ground when it stands on it
            scale = f,
        }
    end
    -- (evenly spaced round the circle: each pair of neighbours needs the chord between them longer than their reaches together)
    local orbit = math.max(ORBIT_RADIUS, reachMost + 3)
    local count = #reaches
    if count >= 2 then
        local chord = 2 * math.sin(math.pi / count)
        for index, reach in reaches do
            orbit = math.max(orbit, (reach + reaches[index % count + 1] + 1.5) / chord)
        end
    end
    for _, offset in offsets do
        offset.orbit = orbit
    end
    return offsets
end

local function getTargetCFrame(player, rootPart, index, count, now, offset, hip)
    local f = offset.scale
    local big = math.sqrt(math.max(f, 1)) -- (a big pet bobs and circles more slowly: it reads as heavy)
    local bob = math.sin(now * BOB_SPEED / big + index * 1.7) * BOB_HEIGHT * f

    if player:GetAttribute("IsCultivating") == true then
        local angle = now * ORBIT_SPEED * 6.5 / offset.orbit + (index - 1) / count * 2 * math.pi
        local center = rootPart.Position + Vector3.new(0, (hip + ORBIT_HEIGHT) * f - hip + bob, 0)
        local position = center + Vector3.new(math.cos(angle), 0, math.sin(angle)) * offset.orbit
        local heading = Vector3.new(-math.sin(angle), 0, math.cos(angle))
        return CFrame.lookAt(position, position + heading)
    end

    return levelFacing(rootPart) * CFrame.new(offset.x, offset.y + bob, offset.z)
end

-- the ground under a point (the world only: no pets, no players), or nil
local groundRay = RaycastParams.new()
groundRay.FilterType = Enum.RaycastFilterType.Exclude
groundRay.RespectCanCollide = true
local groundFilterAt = 0
local function groundUnder(position)
    local now = os.clock()
    if now >= groundFilterAt then
        groundFilterAt = now + 1
        local skip = { container }
        for _, other in Players:GetPlayers() do
            if other.Character then
                table.insert(skip, other.Character)
            end
        end
        groundRay.FilterDescendantsInstances = skip
    end
    local hit = workspace:Raycast(position + Vector3.new(0, 4, 0), Vector3.new(0, -140, 0), groundRay)
    return hit and hit.Position
end

-- A big pet's shadow, footfalls and fade, after it has moved this frame (`moved`: studs of ground travel). Its shadow follows it in
-- the same BulkMoveTo (parts, cframes).
local function heft(pet, offset, moved, grounded, eye, deltaTime, parts, cframes)
    PetHeft.fade(pet, eye, deltaTime)
    if not (pet.shadow or pet.dust) then
        return
    end
    pet.shadowBeat = ((pet.shadowBeat or math.random(0, SHADOW_EVERY - 1)) + 1) % SHADOW_EVERY
    local middle = pet.cframe * CFrame.new(pet.foot.offset)
    if pet.shadowBeat == 0 or pet.ground == nil then
        pet.ground = groundUnder(middle.Position) or false
    end
    local ground = pet.ground or nil
    if ground then
        ground = Vector3.new(middle.X, ground.Y, middle.Z)
    end
    if pet.shadow then
        local lift = if ground then pet.cframe.Y - ground.Y - offset.rest else 0
        local at = PetHeft.placeShadow(pet.shadow, ground, lift, pet.cframe.Rotation)
        if at then
            table.insert(parts, pet.shadow)
            table.insert(cframes, at)
        end
    end
    if pet.dust and grounded and ground then
        pet.stepLeft -= moved
        if pet.stepLeft <= 0 then
            pet.stepLeft = STRIDE * 2 * math.max(pet.foot.half.X, pet.foot.half.Z)
            pet.stepSide = -pet.stepSide
            local foot = middle * CFrame.new(pet.stepSide * pet.foot.half.X * 0.45, 0, -pet.foot.half.Z * 0.25)
            PetHeft.step(pet.dust, Vector3.new(foot.X, ground.Y, foot.Z), false)
        end
    end
end

local function updateCompanions(deltaTime)
    local now = os.clock()
    local parts, cframes = {}, {}
    local camera = workspace.CurrentCamera
    local eye = camera and camera.CFrame.Position

    for player, entry in companions do
        syncPets(player, entry)
        local rootPart = entry.rootPart
        local far = rootPart ~= nil and eye ~= nil and player ~= Players.LocalPlayer
            and (rootPart.Position - eye).Magnitude > CULL_DISTANCE
        -- the player's own pets step out of the hatch cinematic's shot (a Giant beside them filled it: HatchCeremony sets this)
        far = far or (player == Players.LocalPlayer and player:GetAttribute("InHatchCinematic") == true)
        if far ~= (entry.culled == true) then
            setCulled(entry, far)
        end
        local every = 1
        if player ~= Players.LocalPlayer and rootPart and eye then
            local distance = (rootPart.Position - eye).Magnitude
            every = if distance > LOD_THIRD then 3 elseif distance > LOD_HALF then 2 else 1
        end
        entry.every = every
        if far then
            continue
        end

        local hip = hipOf(player)
        local flying = entry.flying == true -- (last frame's: worked out below with the poses)
        local offsets = followOffsets(entry.pets, hip, flying)
        local grounded = not flying and player:GetAttribute("IsCultivating") ~= true
        for index, pet in entry.pets do
            local target = getTargetCFrame(player, rootPart, index, #entry.pets, now, offsets[index], hip)
            local previous = pet.cframe.Position
            if (pet.cframe.Position - target.Position).Magnitude > SNAP_DISTANCE * math.max(pet.scale, 1) then
                pet.cframe = target
            else
                -- a big one follows more slowly: it reads as heavy (a Giant's lag at a run is about 5 studs)
                local blend = 1 - math.exp(-FOLLOW_SHARPNESS / math.sqrt(math.max(pet.scale, 1)) * deltaTime)
                pet.cframe = pet.cframe:Lerp(target, blend)
            end
            -- ground travel only: the idle bob is up and down, and counting it kept a still pet from ever settling (its naps never came)
            local step = pet.cframe.Position - previous
            local travelled = Vector2.new(step.X, step.Z).Magnitude
            local moved = travelled / math.max(deltaTime, 1e-3)
            pet.speed += (math.min(moved, 60) - pet.speed) * math.min(1, deltaTime * 8)

            table.insert(parts, pet.rootPart)
            table.insert(cframes, pet.cframe)
            heft(pet, offsets[index], travelled, grounded, eye, deltaTime, parts, cframes)
        end
    end

    if #parts > 0 then
        workspace:BulkMoveTo(parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)
    end

    for player, entry in companions do
        if entry.culled then
            continue
        end
        local rankedUp = false
        if now >= (entry.rankCheck or 0) then
            entry.rankCheck = now + RANK_CHECK_INTERVAL
            local rank = getRankNumber(player)
            rankedUp = entry.rank ~= nil and rank ~= nil and rank > entry.rank
            entry.rank = rank
        end
        -- Pets fly with their owner: during sword flight, and whenever the owner has been off the
        -- ground for a moment (a Qinggong leap, a glide or a long fall).
        local ownerHumanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
        local airborne = ownerHumanoid ~= nil and ownerHumanoid.FloorMaterial == Enum.Material.Air
        entry.airborneTime = if airborne then (entry.airborneTime or 0) + deltaTime else 0
        local flying = player:GetAttribute("IsFlying") == true or entry.airborneTime > 0.35
        -- a Giant walker lands with its owner after a real time in the air (a flight, a long leap): a thud and a wide ring of dust
        entry.airPeak = math.max(entry.airPeak or 0, entry.airborneTime)
        if entry.flying and not flying then
            if entry.airPeak >= LANDING_AIRTIME then
                for _, pet in entry.pets do
                    if pet.dust and pet.ground then
                        local middle = pet.cframe * CFrame.new(pet.foot.offset)
                        PetHeft.step(pet.dust, Vector3.new(middle.X, pet.ground.Y, middle.Z), true)
                    end
                end
            end
            entry.airPeak = 0
        elseif not flying then
            entry.airPeak = 0
        end
        entry.flying = flying
        local cultivating = player:GetAttribute("IsCultivating") == true
        for _, pet in entry.pets do
            local rig = pet.rig
            if not rig then
                continue
            end
            if cultivating and PetRig.SPECIALS_ENABLED then -- (pets' specials are switched off for now: PetRig.SPECIALS_ENABLED)
                pet.nextNova = pet.nextNova or now + 6
                if now >= pet.nextNova then
                    pet.nextNova = now + NOVA_INTERVAL
                    if novaAllowed(player, pet) then
                        PetRig.nova(rig)
                    end
                end
            else
                pet.nextNova = nil
            end
            if rankedUp and PetRig.SPECIALS_ENABLED and novaAllowed(player, pet) then
                PetRig.nova(rig)
            end
            -- posed every entry.every frames, with the time since its last pose (each pet on its own beat, so a crowd's
            -- poses spread over the frames)
            pet.poseTime = (pet.poseTime or 0) + deltaTime
            pet.beat = ((pet.beat or math.random(0, 5)) + 1) % 6
            if pet.beat % (entry.every or 1) ~= 0 then
                continue
            end
            local poseTime = pet.poseTime
            pet.poseTime = 0
            -- (guarded: one rig that throws must not stop every pet after it this frame, release audit 2026-11-12)
            local ok, err = pcall(PetRig.update, rig, poseTime, { speed = pet.speed, flying = flying })
            if not ok and not updateWarned[rig.petId] then
                updateWarned[rig.petId] = true
                warn("PetCompanionController: " .. tostring(rig.petId) .. " failed to update: " .. tostring(err))
            end
        end
    end
end

local function watchPlayer(player)
    companions[player] = { key = "", rootPart = nil, pets = {} }
end

local function unwatchPlayer(player)
    local entry = companions[player]
    if entry then
        clearPets(entry)
        companions[player] = nil
    end
end

Players.PlayerAdded:Connect(watchPlayer)
Players.PlayerRemoving:Connect(unwatchPlayer)

for _, player in Players:GetPlayers() do
    watchPlayer(player)
end

RunService.RenderStepped:Connect(updateCompanions)
