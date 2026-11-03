-- OwnerAura: the owner's own aura, designed on the Studio AuraWorkbench (2026-11-03) and worn by the
-- user ids in GameConfig.OwnerAura in place of their realm aura. Its pieces are kept as a template in
-- ReplicatedStorage.AuraMeshes.OwnerAura:
--   Ground  the energy circle and swirl ripple, the rising light streaks, the drifting mist, the
--           embers: each held at its height above the floor under the character
--   Body    the two vortex portals, the chain glitter rods and the storm cloud: held round the root
--   Hands   on each hand, a chain into its portal and three silver smoke beams along it
-- and, built here: the body aura (RealmAura.bodyAura, gold), four tapered ribbons spiralling from
-- the shins to above the head, the storm cloud's cubic in-out bob, lightning and pulsing light, and
-- the glitter bursting along the chains.
-- The portals, chains and their smoke and glitter show only while the owner meditates, when the
-- floating pose spreads the arms toward them (Character/PoseController).
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RealmAura = require(script.Parent:WaitForChild("RealmAura"))

local OwnerAura = {}

local RIBBON_RADIUS = 3.2
local RIBBON_LOW, RIBBON_HIGH = -2.1, 2.3   -- from the shins to just above the head
local RIBBON_PERIOD = 4.4
local RIBBON_SPIN = 2.6
local RIBBON_WIDTH = 1.8
local CLOUD_PERIOD = 3
local FLOOR_CHECK = 0.1                     -- seconds between floor checks
local MEDITATION_ONLY = { PortalLeft = true, PortalRight = true, ChainSmokeLeft = true, ChainSmokeRight = true }

local records = {}
local stepping = nil

function OwnerAura.isOwner(player)
    return player ~= nil and table.find(GameConfig.OwnerAura.UserIds, player.UserId) ~= nil
end

local function template()
    local meshes = ReplicatedStorage:FindFirstChild("AuraMeshes")
    return meshes and meshes:FindFirstChild("OwnerAura")
end

local function ease(x)
    return TweenService:GetValue(x, Enum.EasingStyle.Cubic, Enum.EasingDirection.InOut)
end

-- switch the meditation pieces on or off (their emitters, beams and lights)
local function setMeditating(record, on)
    if record.meditating == on then
        return
    end
    record.meditating = on
    for _, inst in record.meditationItems do
        if inst.Parent then
            inst.Enabled = on
            if not on and inst:IsA("ParticleEmitter") then
                inst:Clear()
            end
        end
    end
end

local function step(dt)
    for record in records do
        local root = record.root
        if not root:IsDescendantOf(workspace) then
            OwnerAura.destroy(record.fx)
            continue
        end
        record.clock += dt
        local clock = record.clock
        setMeditating(record, record.player:GetAttribute("IsCultivating") == true)

        -- the ribbons: up and down on a smooth cosine, a quarter period apart, alternate ways round
        for _, r in record.ribbons do
            r.angle += dt * RIBBON_SPIN * r.dir
            local k = 0.5 - 0.5 * math.cos((clock / RIBBON_PERIOD + r.phase) * math.pi * 2)
            local y = RIBBON_LOW + (RIBBON_HIGH - RIBBON_LOW) * k
            local pos = Vector3.new(math.cos(r.angle) * RIBBON_RADIUS, y, math.sin(r.angle) * RIBBON_RADIUS)
            r.a0.Position = pos + Vector3.new(0, RIBBON_WIDTH / 2, 0)
            r.a1.Position = pos - Vector3.new(0, RIBBON_WIDTH / 2, 0)
        end

        -- the floor under the character, ten times a second
        record.floorClock -= dt
        if record.floorClock <= 0 then
            record.floorClock = FLOOR_CHECK
            local hit = workspace:Raycast(root.Position, Vector3.new(0, -14, 0), record.rayParams)
            record.floorY = if hit then hit.Position.Y else root.Position.Y - 3
        end
        local _, yaw = root.CFrame:ToOrientation()
        local flat = CFrame.fromOrientation(0, yaw, 0)
        for _, g in record.ground do
            g.part.CFrame = CFrame.new(root.Position.X, record.floorY + g.height, root.Position.Z) * flat * g.turn
        end
        for _, b in record.body do
            b.part.CFrame = root.CFrame * b.offset
        end

        -- the storm cloud: a cubic in-out bob, a slow turn, intermittent lightning, the light in step
        local cloud = record.cloud
        if cloud then
            record.cloudAngle += dt * 0.12
            local phase = (clock % CLOUD_PERIOD) / CLOUD_PERIOD
            local half = if phase < 0.5 then ease(phase * 2) else 1 - ease((phase - 0.5) * 2)
            cloud.part.CFrame = root.CFrame * cloud.offset * CFrame.new(0, (half - 0.5) * 0.6, 0) * CFrame.Angles(0, record.cloudAngle, 0)
            record.nextStrike -= dt
            if record.nextStrike <= 0 then
                record.nextStrike = 0.15 + math.random() * 0.4
                if cloud.bolt then
                    cloud.bolt:Emit(1)
                end
                record.flash = 1
            end
            record.flash = math.max(0, record.flash - dt * 6)
            if cloud.light then
                cloud.light.Brightness = 0.7 + 0.25 * math.sin(clock * 2.1) + 3.5 * record.flash
            end
        end

        -- glitter bursting at random points along the chains, while meditating
        if record.meditating and #record.rods > 0 then
            record.nextBurst -= dt
            if record.nextBurst <= 0 then
                record.nextBurst = 0.25 + math.random() * 0.35
                local rod = record.rods[math.random(1, #record.rods)]
                local at = rod:FindFirstChild("BurstPoint")
                if at then
                    at.Position = Vector3.new(0, 0, (math.random() - 0.5) * rod.Size.Z * 0.9)
                    local glitter, flashFx = at:FindFirstChild("GlitterBurst"), at:FindFirstChild("BurstFlash")
                    if glitter then
                        glitter:Emit(math.random(40, 60))
                    end
                    if flashFx then
                        flashFx:Emit(1)
                    end
                end
            end
        end
    end
end

-- builds the owner's aura round a character; returns its folder (OwnerAuraFX, under the root), or
-- nil when the template is missing
function OwnerAura.build(player, character, root)
    local source = template()
    if not source then
        warn("[OwnerAura] ReplicatedStorage.AuraMeshes.OwnerAura is missing")
        return nil
    end
    local old = root:FindFirstChild("OwnerAuraFX")
    if old then
        OwnerAura.destroy(old)
    end
    local fx = Instance.new("Folder")
    fx.Name = "OwnerAuraFX"
    fx.Parent = root

    local record = { player = player, character = character, root = root, fx = fx, clock = 0, floorClock = 0,
        floorY = root.Position.Y - 3, ground = {}, body = {}, ribbons = {}, rods = {}, meditationItems = {},
        made = {}, meditating = nil, cloudAngle = 0, nextStrike = 0.3, flash = 0, nextBurst = 0 }
    local rayParams = RaycastParams.new()
    rayParams.FilterType = Enum.RaycastFilterType.Exclude
    rayParams.FilterDescendantsInstances = { character }
    record.rayParams = rayParams

    local function collect(inst)
        for _, d in inst:GetDescendants() do
            if d:IsA("ParticleEmitter") or d:IsA("Beam") or d:IsA("Light") then
                table.insert(record.meditationItems, d)
            end
        end
    end

    for _, src in source.Ground:GetChildren() do
        local part = src:Clone()
        part.Parent = fx
        table.insert(record.ground, { part = part, height = src:GetAttribute("Height") or 0, turn = src:GetAttribute("Turn") or CFrame.identity })
    end
    local portals = {}
    for _, src in source.Body:GetChildren() do
        local part = src:Clone()
        part.Parent = fx
        local offset = src:GetAttribute("Offset") or CFrame.identity
        if part.Name == "StormCloud" then
            record.cloud = { part = part, offset = offset - offset.Position + Vector3.new(0, offset.Y, 0),
                bolt = part:FindFirstChild("CloudLightning"), light = part:FindFirstChild("CloudLight") }
        else
            table.insert(record.body, { part = part, offset = offset })
        end
        if MEDITATION_ONLY[part.Name] then
            collect(part)
        end
        if part.Name:sub(1, 6) == "Portal" then
            portals[part.Name:sub(7)] = part
        elseif part.Name:sub(1, 10) == "ChainSmoke" then
            table.insert(record.rods, part)
        end
    end

    -- the chains and their smoke, from each hand into its portal
    for _, side in { "Left", "Right" } do
        local hand = character:FindFirstChild(side .. "Hand")
        local folder = source.Hands:FindFirstChild(side .. "Hand")
        local portal = portals[side]
        if hand and folder and portal then
            local grip = folder.ChainGrip:Clone()
            grip.Name = "OwnerChainGrip"
            grip.Parent = hand
            table.insert(record.made, grip)
            for _, src in folder:GetChildren() do
                if src:IsA("Beam") then
                    local beam = src:Clone()
                    beam.Name = "Owner" .. src.Name
                    beam.Attachment0 = grip
                    beam.Attachment1 = portal:FindFirstChild("ChainEnd")
                    beam.Parent = hand
                    table.insert(record.made, beam)
                    table.insert(record.meditationItems, beam)
                end
            end
        end
    end

    -- the ribbons: tapered trails behind points on a helix round the body
    local texture = source:GetAttribute("RibbonTexture") or "rbxassetid://124753331461910"
    for i, phase in { 0, 0.5, 0.25, 0.75 } do
        local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
        a0.Name, a1.Name = "OwnerRibbon" .. i .. "A", "OwnerRibbon" .. i .. "B"
        a0.Parent, a1.Parent = root, root
        local trail = Instance.new("Trail")
        trail.Name = "OwnerRibbon" .. i
        trail.Attachment0, trail.Attachment1 = a0, a1
        trail.Texture = texture
        trail.TextureMode = Enum.TextureMode.Stretch
        trail.Color = ColorSequence.new(Color3.fromRGB(255, 220, 140))
        trail.LightEmission = 1
        trail.Brightness = 4
        trail.LightInfluence = 0
        trail.FaceCamera = false
        trail.Lifetime = 1.25
        trail.MinLength = 0.05
        trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.14, 0.02),
            NumberSequenceKeypoint.new(0.65, 0.18), NumberSequenceKeypoint.new(1, 1) })
        trail.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05), NumberSequenceKeypoint.new(0.2, 1),
            NumberSequenceKeypoint.new(0.45, 0.9), NumberSequenceKeypoint.new(1, 0.04) })
        trail.Parent = root
        table.insert(record.made, a0)
        table.insert(record.made, a1)
        table.insert(record.made, trail)
        table.insert(record.ribbons, { a0 = a0, a1 = a1, phase = phase, dir = if i % 2 == 1 then 1 else -1, angle = i * math.pi / 2 })
    end

    -- the gold body aura over the whole body
    record.undressBody = RealmAura.bodyAura(root, fx, source:GetAttribute("BodyColor") or Color3.fromRGB(255, 170, 40),
        source:GetAttribute("BodyLevel") or 0.4)

    setMeditating(record, player:GetAttribute("IsCultivating") == true)
    records[record] = true
    record.fxConnection = fx.Destroying:Connect(function()
        OwnerAura.destroy(fx)
    end)
    if not stepping then
        stepping = RunService.RenderStepped:Connect(step)
    end
    return fx
end

-- removes everything the aura made, at once (a rebuild in the same frame dresses the same parts)
function OwnerAura.destroy(fx)
    for record in records do
        if record.fx == fx then
            records[record] = nil
            if record.fxConnection then
                record.fxConnection:Disconnect()
            end
            if record.undressBody then
                record.undressBody()
            end
            for _, inst in record.made do
                inst:Destroy()
            end
        end
    end
    if fx.Parent then
        fx:Destroy()
    end
    if next(records) == nil and stepping then
        stepping:Disconnect()
        stepping = nil
    end
end

return OwnerAura
