-- Every player's beast pen, shown and moved by this client alone (PenService replicates only each pasture's holder, pen level and the
-- beasts in it: ReplicatedStorage.BeastPastures.<n>; the server does nothing per frame). For each pasture held:
--   the fence and its wooden deck at its level (PenFence), which grow when the level rises, with a ring of gold light;
--   each beast, its own rig (PetModels, at its hatch size; shown smaller only if it couldn't turn in the pen at this level:
--   PenLayout.displayScale), roaming on its own: it idles a while, picks a spot inside the fence clear of the others (kept off the
--   fence by its own footprint), turns to face it with a few steps on the spot, walks there with its own gait (PetRig's walk, from the
--   speed it moves at), and idles again, on the deck; a name over it gives its name, rarity and size.
-- Cost: a pasture's fence and beasts are built only while the camera is within BUILD_REACH (freed past FREE_REACH); a beast moves and
-- poses only within ANIMATE_REACH (every 2nd frame past HALF_REACH), and rests otherwise; shorter reaches on a phone (Quality.Low).
-- It also shows the pasture's prompts to its holder alone, and tells the player where their pasture is when they are given one.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PenLayout = require(ReplicatedStorage:WaitForChild("PenLayout"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local PetModels = require(script.Parent:WaitForChild("PetModels"))
local PetRig = require(script.Parent:WaitForChild("PetRig"))
local PetPreload = require(script.Parent:WaitForChild("PetPreload"))
local PenFence = require(script.Parent:WaitForChild("PenFence"))
local PenPicker = require(script.Parent:WaitForChild("PenPicker"))
local Quality = require(script.Parent.Parent:WaitForChild("Quality"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Toast = require(UI:WaitForChild("Toast"))
local UiTheme = require(UI:WaitForChild("UiTheme"))

local player = Players.LocalPlayer

local BUILD_REACH = if Quality.Low then 160 else 240
local FREE_REACH = BUILD_REACH + 40
local ANIMATE_REACH = if Quality.Low then 80 else 120
local HALF_REACH = if Quality.Low then 40 else 60
local VOICE_REACH = 40   -- a beast's calls only this near (a meadow of pens mustn't be a din)
local LABEL_REACH = 60   -- its name shows this near
local TURN_RATE = 1.7    -- radians a second
local IDLE = { 2.5, 6.5 } -- seconds it idles between walks
local GROW = 1.2         -- seconds the fence takes to grow at an upgrade
local TEXTURES = { Glow = "rbxassetid://135169457468310", Ring = "rbxassetid://81927825399672" } -- (HatchCeremony's)

local folder = ReplicatedStorage:WaitForChild("BeastPastures", 60)
local container = Instance.new("Folder")
container.Name = "BeastPens"
container.Parent = workspace

local ray = RaycastParams.new()
ray.FilterType = Enum.RaycastFilterType.Include
ray.FilterDescendantsInstances = { workspace.Terrain }
local function groundAt(position, fallback)
    local hit = workspace:Raycast(position + Vector3.new(0, 20, 0), Vector3.new(0, -40, 0), ray)
    return if hit then hit.Position.Y else fallback
end

-- ---------- one beast ----------
local acrossOf = {} -- ["PetId:Size"] = its footprint's diagonal at its size, unscaled (studs): what it needs to turn on the spot

-- its name, rarity and size over it, sized in studs (a sign over it, not a screen label): far ones shrink, so a full pen seen down
-- its length doesn't pile its names on top of each other
local function nameTag(model, root, pet, height)
    local definition = GameConfig.Pets[pet.PetId]
    local gui = Instance.new("BillboardGui")
    gui.Name = "PenTag"
    gui.Size = UDim2.fromScale(8, 1.7)
    gui.StudsOffsetWorldSpace = Vector3.new(0, height + 0.9, 0)
    gui.MaxDistance = LABEL_REACH
    gui.LightInfluence = 0
    gui.Adornee = root
    local name = Instance.new("TextLabel")
    name.Name = "PetName"
    name.BackgroundTransparency = 1
    name.Size = UDim2.fromScale(1, 0.58)
    name.FontFace = UiTheme.Fonts.Heavy
    name.TextScaled = true
    name.TextColor3 = Color3.new(1, 1, 1)
    name.TextStrokeColor3 = UiTheme.Colors.Outline
    name.TextStrokeTransparency = 0.2
    name.Text = definition.DisplayName
    name.Parent = gui
    local size = PetRules.size(pet.Size)
    local info = Instance.new("TextLabel")
    info.Name = "Info"
    info.BackgroundTransparency = 1
    info.Position = UDim2.fromScale(0, 0.6)
    info.Size = UDim2.fromScale(1, 0.4)
    info.FontFace = UiTheme.Fonts.Heavy
    info.TextScaled = true
    info.RichText = true
    info.TextStrokeColor3 = UiTheme.Colors.Outline
    info.TextStrokeTransparency = 0.3
    local words = { string.format('<font color="#%s">%s</font>', (GameConfig.PetRarityColors[definition.Rarity] or Color3.new(1, 1, 1)):ToHex(),
        string.upper(definition.Rarity)) }
    if size ~= "Normal" then
        table.insert(words, string.format('<font color="#%s">%s</font>', PetRules.sizeInfo(size).Color:ToHex(), string.upper(size)))
    end
    if (pet.Level or 1) > 1 then
        table.insert(words, '<font color="#FFEEC4">LV ' .. pet.Level .. "</font>")
    end
    info.Text = table.concat(words, "  ·  ")
    info.Parent = gui
    gui.Parent = model
end

-- builds a beast at its size for a pen of `level` (smaller only if it couldn't turn there), standing on the pen's deck (`floor`, its
-- top's world Y: PenFence) or else on the ground; nil while its meshes load
local function buildBeast(pet, level, penFrame, owner, others, floor)
    if not PetPreload.isReady(pet.PetId) then
        PetPreload.want(pet.PetId)
        return nil
    end
    local key = pet.PetId .. ":" .. pet.Size
    local model, root
    if not acrossOf[key] then
        model, root = PetModels.build(pet.PetId, pet.Size)
        if not model then
            return nil
        end
        local _, size = model:GetBoundingBox()
        acrossOf[key] = math.sqrt(size.X * size.X + size.Z * size.Z)
    end
    local display = PenLayout.displayScale(level, acrossOf[key])
    if not model or display < 1 then
        if model then
            model:Destroy()
        end
        model, root = PetModels.build(pet.PetId, pet.Size, display)
        if not model then
            return nil
        end
    end
    local scale = model:GetAttribute("SizeScale") or 1
    local radius = acrossOf[key] * display / 2
    local half = PenLayout.roamHalf(level, radius)
    -- where it starts: the clearest of a few spots, away from the beasts already shown (so they don't start in a heap)
    local spot, bestGap = nil, -math.huge
    for _ = 1, 8 do
        local try = Vector3.new((math.random() * 2 - 1) * half.X, 0, (math.random() * 2 - 1) * half.Y)
        local gap = math.huge
        for _, other in others do
            local mark = penFrame:PointToObjectSpace(other.cframe.Position)
            gap = math.min(gap, (Vector3.new(mark.X, 0, mark.Z) - try).Magnitude - (radius + other.radius))
        end
        if gap > bestGap then
            spot, bestGap = try, gap
        end
    end
    local at = penFrame * spot
    local y = (floor or groundAt(at, penFrame.Y)) + PenLayout.Hip * scale
    local start = CFrame.new(at.X, y, at.Z) * CFrame.Angles(0, math.random() * math.pi * 2, 0)
    model:PivotTo(start)
    model.Parent = container
    local rig = PetModels.getRig(model)
    if rig then
        rig.owner = owner -- (a phone drops another player's pets' lights: PetRig)
    end
    local _, box = model:GetBoundingBox()
    nameTag(model, root, pet, box.Y / 2)
    return {
        model = model, root = root, rig = rig, penFrame = penFrame, half = half, radius = radius, scale = scale,
        unit = if rig then rig.unit else PetModels.SIZE * scale,
        cframe = start, height = y, targetHeight = y, floor = floor,
        state = "idle", stateUntil = os.clock() + math.random() * IDLE[2],
        target = nil, speed = 0, beat = math.random(0, 1), poseTime = 0,
    }
end

-- one step of its wander: idle, turn toward its next spot (stepping on the spot), walk there
local function wander(beast, others, dt, now)
    local position = beast.cframe.Position
    local look = beast.cframe.LookVector
    local yaw = math.atan2(-look.X, -look.Z)
    local moved = 0
    if beast.state == "idle" then
        if now >= beast.stateUntil then
            -- a spot inside the fence a few studs off, and as clear of the others as the pen allows (the best of a few tries)
            local half = beast.half
            local here = beast.penFrame:PointToObjectSpace(position)
            local best, bestScore = nil, -math.huge
            for _ = 1, 6 do
                local spot = Vector3.new((math.random() * 2 - 1) * half.X, 0, (math.random() * 2 - 1) * half.Y)
                local score = math.min((spot - Vector3.new(here.X, 0, here.Z)).Magnitude, 6)
                for _, other in others do
                    if other ~= beast then
                        local mark = beast.penFrame:PointToObjectSpace(other.target or other.cframe.Position)
                        local gap = (Vector3.new(mark.X, 0, mark.Z) - spot).Magnitude - (beast.radius + other.radius)
                        score += math.min(gap, 0) * 2
                    end
                end
                if score > bestScore then
                    best, bestScore = spot, score
                end
            end
            local world = beast.penFrame * best
            beast.target = Vector3.new(world.X, position.Y, world.Z)
            beast.targetHeight = (beast.floor or groundAt(world, beast.penFrame.Y)) + PenLayout.Hip * beast.scale
            beast.state = "turn"
        end
    else
        local to = beast.target - position
        local flat = Vector3.new(to.X, 0, to.Z)
        local want = math.atan2(-flat.X, -flat.Z)
        local diff = (want - yaw + math.pi) % (2 * math.pi) - math.pi
        local turn = math.clamp(diff, -TURN_RATE * dt, TURN_RATE * dt)
        yaw += turn
        if beast.state == "turn" then
            moved = math.abs(turn) * beast.unit * 1.1 -- (a few steps on the spot while it turns)
            if math.abs(diff) < 0.12 then
                beast.state = "walk"
            end
        else
            local pace = math.clamp(2.6 * beast.unit, 2.5, 7) -- studs a second: an amble (PetRig reads a full walk at 4 units a second)
            local distance = flat.Magnitude
            local step = math.min(distance, pace * dt * math.clamp(1 - math.abs(diff) / 1.2, 0.2, 1))
            if distance > 0.05 then
                position += flat.Unit * step
                moved = step
            end
            if distance < 0.3 then
                beast.state = "idle"
                beast.target = nil
                beast.stateUntil = now + IDLE[1] + math.random() * (IDLE[2] - IDLE[1])
            end
        end
    end
    -- held inside the fence whatever happens; its height eases to the ground under its next spot
    local here = beast.penFrame:PointToObjectSpace(position)
    here = Vector3.new(math.clamp(here.X, -beast.half.X, beast.half.X), 0, math.clamp(here.Z, -beast.half.Y, beast.half.Y))
    local world = beast.penFrame * here
    beast.height += (beast.targetHeight - beast.height) * math.min(1, dt * 2)
    beast.cframe = CFrame.new(world.X, beast.height, world.Z) * CFrame.Angles(0, yaw, 0)
    local speed = moved / math.max(dt, 1e-3)
    beast.speed += (speed - beast.speed) * math.min(1, dt * 8)
end

-- ---------- pastures ----------
local pastures = {} -- [Configuration] = { frame, level, owner, fence, beasts = { { key, pet, beast } }, built }

local function parsePets(text)
    local out = {}
    for _, entry in string.split(if typeof(text) == "string" then text else "", ",") do
        local petId, size, level = string.match(entry, "^([^:]+):([^:]*):?(%d*)$")
        if petId and GameConfig.Pets[petId] and #out < PenLayout.MostSlots then
            table.insert(out, { PetId = petId, Size = PetRules.size(size), Level = tonumber(level) or 1, key = entry })
        end
    end
    return out
end

local function clearBeasts(entry)
    for _, slot in entry.beasts do
        if slot.beast then
            slot.beast.model:Destroy()
            slot.beast = nil
        end
    end
end

local function unbuild(entry)
    entry.built = false
    clearBeasts(entry)
    if entry.fence then
        entry.fence:Destroy()
        entry.fence = nil
    end
end

-- a ring of gold light running out across the pen, and a soft flash, when it grows (seen by anyone near)
local function celebrate(entry)
    local level = entry.level
    local penFrame = entry.frame * PenLayout.penFrame(level)
    local deck = entry.fence and entry.fence:GetAttribute("DeckTop")
    local at = Vector3.new(penFrame.X, (deck or groundAt(penFrame.Position, entry.frame.Y)) + 0.3, penFrame.Z)
    local holder = Instance.new("Part")
    holder.Anchored, holder.CanCollide, holder.CanQuery, holder.CanTouch, holder.CastShadow = true, false, false, false, false
    holder.Transparency = 1
    holder.Size = Vector3.new(0.4, 0.4, 0.4)
    holder.CFrame = CFrame.new(at)
    holder.Parent = container
    task.delay(3, function()
        holder:Destroy()
    end)
    local gold = Color3.fromRGB(255, 196, 70)
    local core = Color3.fromRGB(255, 240, 200)
    local size = PenLayout.level(level)
    local function emit(props, count)
        local e = Instance.new("ParticleEmitter")
        e.Rate = 0
        e.LightEmission = 1
        e.LightInfluence = 0
        for k, v in props do
            e[k] = v
        end
        e.Parent = holder
        e:Emit(count)
    end
    emit({ Texture = TEXTURES.Ring, Speed = NumberRange.new(0.01), EmissionDirection = Enum.NormalId.Top,
        Orientation = Enum.ParticleOrientation.VelocityPerpendicular, Lifetime = NumberRange.new(1),
        Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 2), NumberSequenceKeypoint.new(1, math.max(size.Width, size.Depth) * 1.1) }),
        Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.6, 0.4), NumberSequenceKeypoint.new(1, 1) }),
        Color = ColorSequence.new(core, gold), Brightness = 2.4 }, 1)
    if player:GetAttribute("SettingReducedEffects") ~= true then
        emit({ Texture = TEXTURES.Glow, Speed = NumberRange.new(0), Lifetime = NumberRange.new(0.7),
            Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 4), NumberSequenceKeypoint.new(1, 16) }),
            Transparency = NumberSequence.new(0.3, 1), Color = ColorSequence.new(core, gold), Brightness = 2 }, 1)
    end
    Sfx.play("PenUpgrade", holder)
end

local function refresh(config)
    local entry = pastures[config]
    local level = config:GetAttribute("Level") or 0
    local owner = Players:GetPlayerByUserId(config:GetAttribute("OwnerUserId") or 0)
    local grew = entry.level ~= nil and level > entry.level and entry.owner == owner and entry.owner ~= nil
    if level ~= entry.level or owner ~= entry.owner then
        -- a new level (or holder): the fence is rebuilt and every beast fitted to the new room
        entry.level, entry.owner = level, owner
        local old = entry.fence
        entry.fence = nil
        clearBeasts(entry)
        if old then
            if grew then
                PenFence.sink(old, 0.35)
            else
                old:Destroy()
            end
        end
        entry.grow = grew
    end
    local wanted = parsePets(config:GetAttribute("Pets"))
    local keep = {}
    for _, slot in entry.beasts do
        keep[slot.key] = keep[slot.key] or {}
        table.insert(keep[slot.key], slot)
    end
    local beasts = {}
    for _, pet in wanted do
        local reuse = keep[pet.key] and table.remove(keep[pet.key])
        table.insert(beasts, reuse or { key = pet.key, pet = pet, beast = nil })
    end
    for _, list in keep do
        for _, slot in list do
            if slot.beast then
                slot.beast.model:Destroy()
            end
        end
    end
    entry.beasts = beasts
end

local function watch(config)
    if not config:IsA("Configuration") or pastures[config] then
        return
    end
    pastures[config] = { frame = config:GetAttribute("Frame"), level = nil, owner = nil, fence = nil, beasts = {}, built = false }
    refresh(config)
    for _, name in { "Pets", "Level", "OwnerUserId" } do
        config:GetAttributeChangedSignal(name):Connect(function()
            refresh(config)
        end)
    end
end

if folder then
    for _, config in folder:GetChildren() do
        watch(config)
    end
    folder.ChildAdded:Connect(watch)
end

-- ---------- each frame ----------
RunService.Heartbeat:Connect(function(dt)
    local camera = workspace.CurrentCamera
    if not camera then
        return
    end
    local eye = camera.CFrame.Position
    local now = os.clock()
    local parts, cframes = {}, {}
    for _, entry in pastures do
        local frame = entry.frame
        if typeof(frame) ~= "CFrame" then
            continue
        end
        local away = (frame.Position - eye).Magnitude
        if away > FREE_REACH or not entry.owner or (entry.level or 0) < 1 then
            if entry.built or entry.fence then
                unbuild(entry)
            end
            continue
        end
        if away > BUILD_REACH and not entry.built then
            continue
        end
        entry.built = true
        local level = entry.level
        if not entry.fence then
            entry.fence = PenFence.build(frame, level)
            entry.fence.Parent = container
            if entry.grow then
                entry.grow = false
                PenFence.grow(entry.fence, GROW)
                celebrate(entry)
            end
        end
        local penFrame = frame * PenLayout.penFrame(level)
        local floor = entry.fence:GetAttribute("DeckTop")
        local live = {}
        for _, slot in entry.beasts do
            if not slot.beast then
                local ok, beast = pcall(buildBeast, slot.pet, level, penFrame, entry.owner, live, floor)
                if ok then
                    slot.beast = beast
                elseif not slot.warned then
                    slot.warned = true
                    warn("PenController: couldn't show " .. tostring(slot.pet.PetId) .. ": " .. tostring(beast))
                end
            end
            if slot.beast then
                table.insert(live, slot.beast)
            end
        end
        for _, beast in live do
            local distance = (beast.cframe.Position - eye).Magnitude
            if distance > ANIMATE_REACH then
                continue -- (it rests where it is: nothing moves or poses out here)
            end
            wander(beast, live, dt, now)
            table.insert(parts, beast.root)
            table.insert(cframes, beast.cframe)
            if beast.rig then
                beast.poseTime += dt
                beast.beat = (beast.beat + 1) % 2
                if distance > HALF_REACH and beast.beat ~= 0 then
                    continue
                end
                beast.rig.quiet = distance > VOICE_REACH
                local ok, err = pcall(PetRig.update, beast.rig, beast.poseTime, { speed = beast.speed, flying = false })
                beast.poseTime = 0
                if not ok and not beast.warned then
                    beast.warned = true
                    warn("PenController: " .. tostring(beast.rig.petId) .. " failed to update: " .. tostring(err))
                end
            end
        end
    end
    if #parts > 0 then
        workspace:BulkMoveTo(parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)
    end
end)

-- ---------- the prompts: only the pasture's holder sees them ----------
local function pastureIndexOf(prompt)
    local node = prompt.Parent
    while node and not (node:IsA("Model") and node:GetAttribute("Index")) do
        node = node.Parent
    end
    return node and node:GetAttribute("Index")
end

local function setPrompt(prompt)
    if prompt:IsA("ProximityPrompt") and (prompt.Name == "PenPrompt" or prompt.Name == "UpgradePrompt") then
        local index = pastureIndexOf(prompt)
        prompt.Enabled = typeof(index) == "number" and player:GetAttribute("PastureIndex") == index
    end
end

local built = nil
task.spawn(function()
    local islands = workspace:WaitForChild("FloatingIslands", 60)
    local hub = islands and islands:WaitForChild("Yggdrasil", 60)
    built = hub and hub:WaitForChild("BeastPastures", 60)
    if not built then
        return
    end
    for _, d in built:GetDescendants() do
        setPrompt(d)
    end
    built.DescendantAdded:Connect(setPrompt) -- (a pasture streams in as the player nears it)
end)

player:GetAttributeChangedSignal("PastureIndex"):Connect(function()
    if built then
        for _, d in built:GetDescendants() do
            setPrompt(d)
        end
    end
end)

game:GetService("ProximityPromptService").PromptTriggered:Connect(function(prompt)
    if prompt.Name == "PenPrompt" then
        PenPicker.open()
    elseif prompt.Name == "UpgradePrompt" then
        PenPicker.open(true)
    end
end)

-- ---------- where the player's pasture is ----------
local told = false
local notice = Toast.new("PastureNotice", Color3.new(1, 1, 1), 5)
local function tell()
    local area = player:GetAttribute("PastureArea")
    local index = player:GetAttribute("PastureIndex")
    if told or typeof(area) ~= "string" or typeof(index) ~= "number" or index <= 0 then
        return
    end
    told = true
    task.delay(4, function() -- (after the join's own greetings)
        notice:show("Your Beast Pasture: the " .. area .. ". Put pets in your pen from PETS, then PEN.", "Info")
    end)
end
player:GetAttributeChangedSignal("PastureArea"):Connect(tell)
tell()

